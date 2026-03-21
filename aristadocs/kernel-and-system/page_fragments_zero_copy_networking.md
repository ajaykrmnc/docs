# Page Fragments and Zero-Copy Networking - Comprehensive Guide

## Table of Contents
1. [Introduction to Page Fragments](#introduction-to-page-fragments)
2. [Why Page Fragments?](#why-page-fragments)
3. [Page Fragment Architecture](#page-fragment-architecture)
4. [How Page Fragments Work](#how-page-fragments-work)
5. [Page Fragment Management](#page-fragment-management)
6. [Implementation Details](#implementation-details)
7. [Real Driver Examples](#real-driver-examples)
8. [Performance Analysis](#performance-analysis)
9. [Best Practices](#best-practices)

---

## Introduction to Page Fragments

### What are Page Fragments?

**Page fragments** are a modern Linux kernel technique for **zero-copy networking** where:
- Network packets are received directly into **memory pages**
- SKBs reference these pages as **fragments** instead of copying data
- Multiple SKBs can share the same page
- No memory copy from DMA buffer to SKB

### The Evolution of Packet Reception

```
┌─────────────────────────────────────────────────────────────────┐
│              Evolution of Packet Reception                      │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Generation 1: Copy-based (Old)                                │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │ DMA → Temp Buffer → memcpy() → SKB linear buffer        │  │
│  │ ❌ Two memory copies                                     │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                 │
│  Generation 2: Pre-allocated SKB (Standard)                    │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │ DMA → SKB linear buffer (kmalloc'd)                      │  │
│  │ ✅ Zero-copy, but wastes memory on small packets         │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                 │
│  Generation 3: Page Fragments (Modern) ⭐                      │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │ DMA → Page → SKB references page as fragment            │  │
│  │ ✅ Zero-copy + efficient memory use                      │  │
│  │ ✅ Can share pages between SKBs                          │  │
│  │ ✅ Better for jumbo frames and high-speed NICs          │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Key Concept: SKB Structure with Fragments

```c
struct sk_buff {
    // Linear data (headers)
    unsigned char *head;
    unsigned char *data;
    unsigned char *tail;
    unsigned char *end;
    
    unsigned int len;        // Total length (linear + fragments)
    unsigned int data_len;   // Length in fragments only
    
    // Shared info contains fragments
    struct skb_shared_info *shinfo;
};

struct skb_shared_info {
    unsigned short nr_frags;              // Number of fragments
    skb_frag_t frags[MAX_SKB_FRAGS];     // Fragment array (17 on x86_64)
    
    // Other fields...
};

typedef struct skb_frag_struct {
    struct page *page;      // Page containing data
    __u32 page_offset;      // Offset within page
    __u32 size;             // Size of this fragment
} skb_frag_t;
```

---

## Why Page Fragments?

### Problem with Traditional Approach

**Traditional SKB allocation:**
```c
// Allocate SKB with 1500 byte linear buffer
skb = netdev_alloc_skb(dev, 1500);
// Allocates: ~200 bytes (sk_buff) + 1500 bytes (data) = ~1700 bytes
```

**Issues:**
1. ❌ **Memory waste** - Small packets (64 bytes) waste 1436 bytes
2. ❌ **Fragmentation** - kmalloc() can fail for large allocations
3. ❌ **Cache pollution** - Large linear buffers waste cache
4. ❌ **No sharing** - Each SKB needs its own buffer
5. ❌ **Poor for jumbo frames** - 9000 byte frames need huge allocations

### Solution: Page Fragments

**Page fragment approach:**
```c
// Allocate minimal SKB (just for headers)
skb = napi_alloc_skb(napi, 128);  // Small linear buffer
// Add page fragment for payload
skb_add_rx_frag(skb, 0, page, offset, len, truesize);
```

**Benefits:**
1. ✅ **Memory efficient** - Only allocate what's needed
2. ✅ **No fragmentation** - Pages are always available
3. ✅ **Cache friendly** - Small linear buffer for headers
4. ✅ **Page sharing** - Multiple SKBs can reference same page
5. ✅ **Scalable** - Works great for jumbo frames
6. ✅ **Zero-copy** - DMA directly to page, no memcpy

### Memory Comparison

```
Traditional SKB (1500 byte packet):
┌────────────────────────────────────────────────────────────┐
│ sk_buff struct (200 bytes)                                 │
├────────────────────────────────────────────────────────────┤
│ Linear buffer (1500 bytes allocated, 1500 used)            │
│ [Headers: 54 bytes][Payload: 1446 bytes]                   │
└────────────────────────────────────────────────────────────┘
Total: ~1700 bytes

Page Fragment SKB (1500 byte packet):
┌────────────────────────────────────────────────────────────┐
│ sk_buff struct (200 bytes)                                 │
├────────────────────────────────────────────────────────────┤
│ Linear buffer (128 bytes allocated, 54 used)               │
│ [Headers: 54 bytes][unused: 74 bytes]                      │
├────────────────────────────────────────────────────────────┤
│ Page fragment (points to page)                             │
│ → Page (4096 bytes, shared with other packets)             │
│   [Payload: 1446 bytes][Space for more packets...]         │
└────────────────────────────────────────────────────────────┘
Total: ~328 bytes per SKB + shared page
Savings: ~80% less memory per SKB!
```

---

## Page Fragment Architecture

### Memory Layout

```
┌─────────────────────────────────────────────────────────────────┐
│           SKB with Page Fragments Layout                        │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  struct sk_buff                                                 │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │ head, data, tail, end  (linear buffer - headers only)    │  │
│  │ ┌────────────────────────────────────────────────────┐   │  │
│  │ │ [Eth][IP][TCP] ← Small linear buffer (128 bytes)  │   │  │
│  │ └────────────────────────────────────────────────────┘   │  │
│  │                                                          │  │
│  │ len = 1500 (total)                                       │  │
│  │ data_len = 1446 (in fragments)                           │  │
│  │ truesize = 1500 + overhead                               │  │
│  └──────────────────────────────────────────────────────────┘  │
│                          │                                      │
│                          │ points to                            │
│                          ▼                                      │
│  struct skb_shared_info                                        │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │ nr_frags = 1                                             │  │
│  │                                                          │  │
│  │ frags[0]:                                                │  │
│  │   ├─ page ──────────┐                                    │  │
│  │   ├─ page_offset: 0 │                                    │  │
│  │   └─ size: 1446     │                                    │  │
│  └─────────────────────┼──────────────────────────────────────┘
│                        │                                        │
│                        │ points to                              │
│                        ▼                                        │
│  struct page (4096 bytes)                                      │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │ [Packet 1 payload: 1446 bytes]                           │  │
│  │ [Packet 2 payload: 1446 bytes]                           │  │
│  │ [Packet 3 payload: 1204 bytes]                           │  │
│  │ [unused space]                                           │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                 │
│  ↑ Multiple SKBs can reference different parts of same page!   │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Multiple Fragments in One SKB

```
┌─────────────────────────────────────────────────────────────────┐
│        SKB with Multiple Page Fragments (Jumbo Frame)           │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  struct sk_buff (9000 byte jumbo frame)                        │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │ Linear buffer: [Headers: 54 bytes]                       │  │
│  │ len = 9000                                                │  │
│  │ data_len = 8946 (in fragments)                            │  │
│  └──────────────────────────────────────────────────────────┘  │
│                          │                                      │
│                          ▼                                      │
│  struct skb_shared_info                                        │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │ nr_frags = 3                                             │  │
│  │                                                          │  │
│  │ frags[0]: page=Page1, offset=0,    size=4096            │  │
│  │ frags[1]: page=Page2, offset=0,    size=4096            │  │
│  │ frags[2]: page=Page3, offset=0,    size=754             │  │
│  └──────────────────────────────────────────────────────────┘  │
│           │              │              │                       │
│           ▼              ▼              ▼                       │
│      ┌────────┐     ┌────────┐     ┌────────┐                  │
│      │ Page 1 │     │ Page 2 │     │ Page 3 │                  │
│      │ 4096 B │     │ 4096 B │     │ 754 B  │                  │
│      └────────┘     └────────┘     └────────┘                  │
│                                                                 │
│  Total: 54 (linear) + 8946 (fragments) = 9000 bytes            │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Page Reference Counting

```c
// Each page has a reference count
struct page {
    atomic_t _refcount;     // Number of references to this page
    // ... other fields
};

// When SKB adds fragment
skb_add_rx_frag(skb, frag_idx, page, offset, size, truesize);
    → get_page(page);       // Increment page refcount

// When SKB is freed
kfree_skb(skb);
    → skb_release_data(skb);
        → for each fragment:
            → put_page(page);  // Decrement page refcount
                → if refcount == 0:
                    → free page back to allocator
```

**Key Point:** Pages are only freed when **all** SKBs referencing them are freed!

---

## How Page Fragments Work

### Step-by-Step Flow

#### Step 1: Driver Initialization

```c
// Modern driver initialization with page pool
static int driver_init_rx_ring(struct driver_priv *priv)
{
    int i;

    // Allocate RX ring descriptors
    priv->rx_ring = dma_alloc_coherent(&priv->pdev->dev,
                                       RX_RING_SIZE * sizeof(struct rx_desc),
                                       &priv->rx_ring_dma, GFP_KERNEL);

    // Pre-allocate pages for RX
    for (i = 0; i < RX_RING_SIZE; i++) {
        struct page *page;
        dma_addr_t dma;

        // ✅ Allocate page (not SKB!)
        page = alloc_page(GFP_KERNEL);
        if (!page)
            return -ENOMEM;

        // Map page for DMA
        dma = dma_map_page(&priv->pdev->dev, page, 0,
                          PAGE_SIZE, DMA_FROM_DEVICE);
        if (dma_mapping_error(&priv->pdev->dev, dma)) {
            put_page(page);
            return -ENOMEM;
        }

        // Store in descriptor
        priv->rx_ring[i].page = page;
        priv->rx_ring[i].dma = dma;
        priv->rx_ring[i].page_offset = 0;

        // Tell hardware about this buffer
        writel(lower_32_bits(dma), priv->base + RX_DESC_ADDR_LO(i));
        writel(upper_32_bits(dma), priv->base + RX_DESC_ADDR_HI(i));
        writel(PAGE_SIZE, priv->base + RX_DESC_LEN(i));
        writel(RX_DESC_ENABLE, priv->base + RX_DESC_CTL(i));
    }

    return 0;
}
```

#### Step 2: Packet Reception (DMA)

```
┌─────────────────────────────────────────────────────────────────┐
│                  Packet Reception with Pages                    │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  1. Packet arrives at NIC                                      │
│     │                                                           │
│     ▼                                                           │
│  2. NIC reads RX descriptor                                    │
│     ├─ Gets DMA address (points to page)                       │
│     ├─ Gets buffer size (PAGE_SIZE = 4096)                     │
│     └─ Gets offset (where to write in page)                    │
│     │                                                           │
│     ▼                                                           │
│  3. NIC DMA engine transfers packet                            │
│     ┌─────────────┐                                            │
│     │ NIC Memory  │                                            │
│     └──────┬──────┘                                            │
│            │ DMA (no CPU!)                                     │
│            ▼                                                    │
│     ┌─────────────────────────────────────────────────────┐    │
│     │ Page in RAM                                         │    │
│     │ [Packet data written at offset]                    │    │
│     └─────────────────────────────────────────────────────┘    │
│     │                                                           │
│     ▼                                                           │
│  4. NIC updates descriptor                                     │
│     ├─ Sets packet length                                      │
│     ├─ Sets status (DONE)                                      │
│     └─ Triggers interrupt                                      │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

#### Step 3: NAPI Poll - Build SKB from Page

```c
// NAPI poll function - process received packets
static int driver_poll(struct napi_struct *napi, int budget)
{
    struct driver_priv *priv = container_of(napi, struct driver_priv, napi);
    int work_done = 0;

    while (work_done < budget) {
        struct rx_desc *desc = &priv->rx_ring[priv->rx_next];
        struct sk_buff *skb;
        struct page *page;
        unsigned int pkt_len;
        dma_addr_t dma;
        u32 status;

        // Check if packet ready
        status = readl(priv->base + RX_DESC_STATUS(priv->rx_next));
        if (!(status & RX_DESC_DONE))
            break;  // No more packets

        // Get packet info
        pkt_len = status & RX_DESC_LEN_MASK;
        page = desc->page;
        dma = desc->dma;

        // Unmap DMA
        dma_unmap_page(&priv->pdev->dev, dma, PAGE_SIZE, DMA_FROM_DEVICE);

        // ✅ Allocate minimal SKB (just for headers)
        skb = napi_alloc_skb(napi, 128);  // Small linear buffer
        if (!skb) {
            // Allocation failed - reuse page
            put_page(page);
            priv->stats.rx_dropped++;
            goto refill;
        }

        // ✅ Add page as fragment to SKB
        skb_add_rx_frag(skb, 0,                    // Fragment index
                       page,                       // Page
                       desc->page_offset,          // Offset in page
                       pkt_len,                    // Size
                       PAGE_SIZE);                 // True size

        // Set SKB metadata
        skb->protocol = eth_type_trans(skb, priv->netdev);
        skb_record_rx_queue(skb, 0);

        // Pass to network stack (with GRO)
        napi_gro_receive(napi, skb);

        priv->stats.rx_packets++;
        priv->stats.rx_bytes += pkt_len;

refill:
        // ✅ Allocate new page for this descriptor
        page = alloc_page(GFP_ATOMIC);
        if (!page) {
            // Page allocation failed - serious problem
            priv->stats.rx_alloc_failed++;
            break;
        }

        // Map new page
        dma = dma_map_page(&priv->pdev->dev, page, 0,
                          PAGE_SIZE, DMA_FROM_DEVICE);

        // Update descriptor
        desc->page = page;
        desc->dma = dma;
        desc->page_offset = 0;

        writel(lower_32_bits(dma), priv->base + RX_DESC_ADDR_LO(priv->rx_next));
        writel(upper_32_bits(dma), priv->base + RX_DESC_ADDR_HI(priv->rx_next));
        writel(RX_DESC_ENABLE, priv->base + RX_DESC_CTL(priv->rx_next));

        // Move to next descriptor
        priv->rx_next = (priv->rx_next + 1) % RX_RING_SIZE;
        work_done++;
    }

    if (work_done < budget) {
        napi_complete(napi);
        // Re-enable interrupts
        writel(INT_RX_ENABLE, priv->base + INT_ENABLE);
    }

    return work_done;
}
```

### Key Functions Explained

#### skb_add_rx_frag()

```c
/**
 * skb_add_rx_frag - Add a page fragment to an SKB
 * @skb: SKB to add fragment to
 * @i: Fragment index (0 to MAX_SKB_FRAGS-1)
 * @page: Page to add
 * @off: Offset within page
 * @size: Size of data in fragment
 * @truesize: True size (for memory accounting)
 */
void skb_add_rx_frag(struct sk_buff *skb, int i, struct page *page,
                     int off, int size, unsigned int truesize)
{
    skb_fill_page_desc(skb, i, page, off, size);
    skb->len += size;
    skb->data_len += size;
    skb->truesize += truesize;
}

// Internal implementation
static inline void skb_fill_page_desc(struct sk_buff *skb, int i,
                                     struct page *page, int off, int size)
{
    skb_frag_t *frag = &skb_shinfo(skb)->frags[i];

    frag->page = page;
    frag->page_offset = off;
    frag->size = size;

    get_page(page);  // Increment page refcount
    skb_shinfo(skb)->nr_frags = i + 1;
}
```

---

## Page Fragment Management

### Page Allocation Strategies

#### Strategy 1: Simple Page Allocation

```c
// Simplest approach - allocate one page per packet
struct page *page = alloc_page(GFP_ATOMIC);
if (!page)
    return -ENOMEM;

// Use entire page for one packet
skb_add_rx_frag(skb, 0, page, 0, pkt_len, PAGE_SIZE);
```

**Pros:**
- ✅ Simple to implement
- ✅ No fragmentation tracking needed

**Cons:**
- ❌ Wastes memory for small packets
- ❌ One 64-byte packet uses 4096-byte page!

#### Strategy 2: Page Recycling (Reuse Pages)

```c
// Reuse page if there's space left
struct rx_buffer {
    struct page *page;
    unsigned int page_offset;
    unsigned int pagecnt_bias;
};

static struct page *driver_get_rx_page(struct driver_priv *priv,
                                       struct rx_buffer *rx_buf)
{
    struct page *page = rx_buf->page;

    // Check if we can reuse current page
    if (page) {
        // If page has space and not shared
        if (rx_buf->page_offset + RX_BUF_SIZE <= PAGE_SIZE &&
            page_count(page) == rx_buf->pagecnt_bias) {
            // Reuse page at new offset
            return page;
        }

        // Page full or shared - release it
        put_page(page);
    }

    // Allocate new page
    page = alloc_page(GFP_ATOMIC);
    if (!page)
        return NULL;

    rx_buf->page = page;
    rx_buf->page_offset = 0;
    rx_buf->pagecnt_bias = 1;

    return page;
}

// Use in poll function
static int driver_poll_with_recycling(struct napi_struct *napi, int budget)
{
    struct driver_priv *priv = container_of(napi, struct driver_priv, napi);
    int work_done = 0;

    while (work_done < budget) {
        struct rx_buffer *rx_buf = &priv->rx_buffers[priv->rx_next];
        struct page *page;
        struct sk_buff *skb;
        unsigned int pkt_len;

        // Get packet...
        pkt_len = get_packet_length(priv);
        if (!pkt_len)
            break;

        page = rx_buf->page;

        // Allocate SKB
        skb = napi_alloc_skb(napi, 128);
        if (!skb)
            goto next;

        // Add fragment at current offset
        skb_add_rx_frag(skb, 0, page, rx_buf->page_offset,
                       pkt_len, RX_BUF_SIZE);

        // Increment page refcount (skb_add_rx_frag already did get_page)
        rx_buf->pagecnt_bias++;

        // Move offset for next packet
        rx_buf->page_offset += RX_BUF_SIZE;

        // If page is full, get new page next time
        if (rx_buf->page_offset + RX_BUF_SIZE > PAGE_SIZE) {
            rx_buf->page = NULL;
            rx_buf->page_offset = 0;
        }

        napi_gro_receive(napi, skb);

next:
        priv->rx_next = (priv->rx_next + 1) % RX_RING_SIZE;
        work_done++;
    }

    return work_done;
}
```

**Pros:**
- ✅ Efficient memory use
- ✅ Multiple small packets per page
- ✅ Reduces page allocation overhead

**Cons:**
- ❌ More complex tracking
- ❌ Need to handle page sharing carefully

#### Strategy 3: Page Pool (Modern Approach)

```c
// Use kernel's page pool infrastructure
#include <net/page_pool.h>

// Initialize page pool
static int driver_init_page_pool(struct driver_priv *priv)
{
    struct page_pool_params pp_params = {
        .order = 0,                    // Single pages
        .flags = PP_FLAG_DMA_MAP,      // Auto DMA mapping
        .pool_size = RX_RING_SIZE * 2, // Pool size
        .nid = NUMA_NO_NODE,
        .dev = &priv->pdev->dev,
        .dma_dir = DMA_FROM_DEVICE,
        .max_len = PAGE_SIZE,
        .offset = 0,
    };

    priv->page_pool = page_pool_create(&pp_params);
    if (IS_ERR(priv->page_pool))
        return PTR_ERR(priv->page_pool);

    return 0;
}

// Allocate page from pool
static struct page *driver_alloc_rx_page(struct driver_priv *priv,
                                         dma_addr_t *dma)
{
    struct page *page;

    // ✅ Get page from pool (may recycle!)
    page = page_pool_dev_alloc_pages(priv->page_pool);
    if (!page)
        return NULL;

    // ✅ DMA address already mapped by page pool!
    *dma = page_pool_get_dma_addr(page);

    return page;
}

// Return page to pool (not free!)
static void driver_free_rx_page(struct driver_priv *priv, struct page *page)
{
    // ✅ Return to pool for recycling
    page_pool_put_page(priv->page_pool, page, -1, false);
}

// Use in poll function
static int driver_poll_with_page_pool(struct napi_struct *napi, int budget)
{
    struct driver_priv *priv = container_of(napi, struct driver_priv, napi);
    int work_done = 0;

    while (work_done < budget) {
        struct page *page;
        struct sk_buff *skb;
        dma_addr_t dma;
        unsigned int pkt_len;

        // Get packet info
        pkt_len = get_packet_length(priv);
        if (!pkt_len)
            break;

        // Get current page
        page = priv->rx_ring[priv->rx_next].page;

        // Allocate SKB
        skb = napi_alloc_skb(napi, 128);
        if (!skb) {
            page_pool_put_page(priv->page_pool, page, -1, false);
            goto refill;
        }

        // ✅ Add page fragment (page pool handles refcounting)
        skb_add_rx_frag(skb, 0, page, 0, pkt_len, PAGE_SIZE);

        // Mark SKB as using page pool
        skb_mark_for_recycle(skb);

        napi_gro_receive(napi, skb);

refill:
        // ✅ Get new page from pool
        page = driver_alloc_rx_page(priv, &dma);
        if (!page)
            break;

        priv->rx_ring[priv->rx_next].page = page;
        priv->rx_ring[priv->rx_next].dma = dma;

        // Update hardware descriptor
        update_rx_descriptor(priv, priv->rx_next, dma);

        priv->rx_next = (priv->rx_next + 1) % RX_RING_SIZE;
        work_done++;
    }

    return work_done;
}

// Cleanup
static void driver_destroy_page_pool(struct driver_priv *priv)
{
    if (priv->page_pool) {
        page_pool_destroy(priv->page_pool);
        priv->page_pool = NULL;
    }
}
```

**Pros:**
- ✅ Automatic page recycling
- ✅ DMA mapping cached
- ✅ NUMA-aware allocation
- ✅ Better performance
- ✅ Less code to maintain

**Cons:**
- ❌ Requires newer kernel (4.20+)
- ❌ Slightly more complex setup

### Page Pool Benefits

```
Without Page Pool:
┌─────────────────────────────────────────────────────────────────┐
│  For each packet:                                               │
│  1. alloc_page()           → ~500 ns                            │
│  2. dma_map_page()         → ~200 ns                            │
│  3. Process packet                                              │
│  4. dma_unmap_page()       → ~200 ns                            │
│  5. put_page()             → ~100 ns                            │
│  Total overhead: ~1000 ns per packet                            │
└─────────────────────────────────────────────────────────────────┘

With Page Pool:
┌─────────────────────────────────────────────────────────────────┐
│  For each packet:                                               │
│  1. page_pool_alloc()      → ~50 ns (from cache!)               │
│  2. DMA already mapped     → 0 ns                               │
│  3. Process packet                                              │
│  4. DMA stays mapped       → 0 ns                               │
│  5. page_pool_put()        → ~50 ns (to cache)                  │
│  Total overhead: ~100 ns per packet                             │
│  ⚡ 10x faster!                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## Implementation Details

### Building SKB with Multiple Fragments

```c
// Example: Build SKB with headers in linear buffer and payload in fragments
static struct sk_buff *build_skb_with_fragments(struct driver_priv *priv,
                                                struct page *page,
                                                unsigned int pkt_len)
{
    struct sk_buff *skb;
    unsigned int hdr_len = 128;  // Ethernet + IP + TCP headers
    unsigned int payload_len = pkt_len - hdr_len;

    // Allocate SKB with space for headers
    skb = napi_alloc_skb(&priv->napi, hdr_len);
    if (!skb)
        return NULL;

    // Copy headers to linear buffer
    skb_copy_to_linear_data(skb, page_address(page), hdr_len);
    skb_put(skb, hdr_len);

    // Add payload as fragment
    if (payload_len > 0) {
        skb_add_rx_frag(skb, 0, page, hdr_len, payload_len, PAGE_SIZE);
    }

    return skb;
}
```

### Splitting Large Packets Across Multiple Fragments

```c
// Example: Jumbo frame split across multiple pages
static struct sk_buff *build_jumbo_skb(struct driver_priv *priv,
                                      struct page **pages,
                                      unsigned int pkt_len)
{
    struct sk_buff *skb;
    unsigned int remaining = pkt_len;
    unsigned int hdr_len = 128;
    int frag_idx = 0;

    // Allocate SKB
    skb = napi_alloc_skb(&priv->napi, hdr_len);
    if (!skb)
        return NULL;

    // Copy headers from first page
    skb_copy_to_linear_data(skb, page_address(pages[0]), hdr_len);
    skb_put(skb, hdr_len);
    remaining -= hdr_len;

    // Add first page fragment (rest of first page)
    if (remaining > 0) {
        unsigned int frag_size = min(remaining, PAGE_SIZE - hdr_len);
        skb_add_rx_frag(skb, frag_idx++, pages[0], hdr_len,
                       frag_size, PAGE_SIZE);
        remaining -= frag_size;
    }

    // Add additional pages as fragments
    int page_idx = 1;
    while (remaining > 0 && frag_idx < MAX_SKB_FRAGS) {
        unsigned int frag_size = min(remaining, (unsigned int)PAGE_SIZE);
        skb_add_rx_frag(skb, frag_idx++, pages[page_idx], 0,
                       frag_size, PAGE_SIZE);
        remaining -= frag_size;
        page_idx++;
    }

    if (remaining > 0) {
        // Packet too large for MAX_SKB_FRAGS
        kfree_skb(skb);
        return NULL;
    }

    return skb;
}
```

### Accessing Fragment Data

```c
// Iterate through all fragments in an SKB
static void process_skb_fragments(struct sk_buff *skb)
{
    struct skb_shared_info *shinfo = skb_shinfo(skb);
    int i;

    printk("SKB has %d fragments\n", shinfo->nr_frags);

    for (i = 0; i < shinfo->nr_frags; i++) {
        skb_frag_t *frag = &shinfo->frags[i];
        struct page *page = skb_frag_page(frag);
        unsigned int offset = skb_frag_off(frag);
        unsigned int size = skb_frag_size(frag);
        void *data;

        printk("Fragment %d: page=%p offset=%u size=%u\n",
               i, page, offset, size);

        // Map page to access data
        data = kmap_atomic(page);

        // Access data at offset
        process_data(data + offset, size);

        // Unmap
        kunmap_atomic(data);
    }
}

// Get total data length
static unsigned int get_skb_total_len(struct sk_buff *skb)
{
    // skb->len includes both linear and fragment data
    return skb->len;
}

// Get fragment data length only
static unsigned int get_skb_frag_len(struct sk_buff *skb)
{
    return skb->data_len;  // Only fragment data
}

// Get linear data length
static unsigned int get_skb_linear_len(struct sk_buff *skb)
{
    return skb->len - skb->data_len;
}
```

### Modifying Fragment Data

```c
// Make fragment data writable (may need to copy)
static int make_fragment_writable(struct sk_buff *skb, int frag_idx)
{
    struct skb_shared_info *shinfo = skb_shinfo(skb);
    skb_frag_t *frag;
    struct page *page, *new_page;
    void *src, *dst;

    if (frag_idx >= shinfo->nr_frags)
        return -EINVAL;

    frag = &shinfo->frags[frag_idx];
    page = skb_frag_page(frag);

    // Check if page is shared
    if (page_count(page) > 1) {
        // Page is shared - need to copy
        new_page = alloc_page(GFP_ATOMIC);
        if (!new_page)
            return -ENOMEM;

        // Copy data
        src = kmap_atomic(page);
        dst = kmap_atomic(new_page);
        memcpy(dst + skb_frag_off(frag),
               src + skb_frag_off(frag),
               skb_frag_size(frag));
        kunmap_atomic(dst);
        kunmap_atomic(src);

        // Replace page
        put_page(page);
        skb_frag_page_set(frag, new_page);
    }

    return 0;
}
```

---

## Real Driver Examples

### Example 1: Intel ixgbe (10 Gigabit Ethernet)

```c
// Simplified from drivers/net/ethernet/intel/ixgbe/ixgbe_main.c

// RX buffer structure
struct ixgbe_rx_buffer {
    struct page *page;
    unsigned int page_offset;
    u16 pagecnt_bias;
};

// Allocate RX buffers
static bool ixgbe_alloc_mapped_page(struct ixgbe_ring *rx_ring,
                                   struct ixgbe_rx_buffer *bi)
{
    struct page *page = bi->page;
    dma_addr_t dma;

    // Try to reuse page
    if (page)
        return true;

    // Allocate new page
    page = alloc_page(GFP_ATOMIC | __GFP_COLD);
    if (!page)
        return false;

    // Map for DMA
    dma = dma_map_page(rx_ring->dev, page, 0,
                      PAGE_SIZE, DMA_FROM_DEVICE);

    if (dma_mapping_error(rx_ring->dev, dma)) {
        put_page(page);
        return false;
    }

    bi->page = page;
    bi->page_offset = 0;
    bi->pagecnt_bias = 1;

    return true;
}

// Build SKB from page
static struct sk_buff *ixgbe_build_skb(struct ixgbe_ring *rx_ring,
                                      struct ixgbe_rx_buffer *rx_buffer,
                                      union ixgbe_adv_rx_desc *rx_desc,
                                      unsigned int size)
{
    void *va = page_address(rx_buffer->page) + rx_buffer->page_offset;
    unsigned int truesize = SKB_DATA_ALIGN(size);
    struct sk_buff *skb;

    // Build SKB from page fragment
    skb = build_skb(va - IXGBE_SKB_PAD, truesize);
    if (!skb)
        return NULL;

    // Update offset for next packet
    rx_buffer->page_offset += truesize;

    // If page is full, release it
    if (rx_buffer->page_offset > (PAGE_SIZE - IXGBE_RX_BUFSZ)) {
        rx_buffer->page = NULL;
    } else {
        // Increment refcount for reuse
        rx_buffer->pagecnt_bias++;
    }

    return skb;
}

// Clean RX ring
static int ixgbe_clean_rx_irq(struct ixgbe_q_vector *q_vector,
                             struct ixgbe_ring *rx_ring,
                             int budget)
{
    unsigned int total_rx_bytes = 0, total_rx_packets = 0;
    u16 cleaned_count = 0;

    while (likely(total_rx_packets < budget)) {
        union ixgbe_adv_rx_desc *rx_desc;
        struct ixgbe_rx_buffer *rx_buffer;
        struct sk_buff *skb;
        unsigned int size;

        // Get descriptor
        rx_desc = IXGBE_RX_DESC(rx_ring, rx_ring->next_to_clean);

        if (!ixgbe_test_staterr(rx_desc, IXGBE_RXD_STAT_DD))
            break;

        // Get size
        size = le16_to_cpu(rx_desc->wb.upper.length);

        // Get RX buffer
        rx_buffer = &rx_ring->rx_buffer_info[rx_ring->next_to_clean];

        // Build SKB from page
        skb = ixgbe_build_skb(rx_ring, rx_buffer, rx_desc, size);
        if (!skb) {
            rx_ring->rx_stats.alloc_rx_buff_failed++;
            break;
        }

        // Process SKB
        ixgbe_process_skb_fields(rx_ring, rx_desc, skb);

        // Pass to stack
        napi_gro_receive(&q_vector->napi, skb);

        // Update stats
        total_rx_bytes += skb->len;
        total_rx_packets++;

        // Move to next
        rx_ring->next_to_clean++;
        if (rx_ring->next_to_clean == rx_ring->count)
            rx_ring->next_to_clean = 0;

        cleaned_count++;
    }

    // Refill RX ring
    if (cleaned_count)
        ixgbe_alloc_rx_buffers(rx_ring, cleaned_count);

    rx_ring->stats.packets += total_rx_packets;
    rx_ring->stats.bytes += total_rx_bytes;

    return total_rx_packets;
}
```

### Example 2: Mellanox mlx5 (Modern High-Speed NIC)

```c
// Simplified from drivers/net/ethernet/mellanox/mlx5/core/en_rx.c

// Use page pool
static int mlx5e_alloc_rx_wqe(struct mlx5e_rq *rq, u16 ix)
{
    struct mlx5e_rx_wqe *wqe = mlx5_wq_ll_get_wqe(&rq->wq, ix);
    struct mlx5e_dma_info *di = &rq->wqe.di[ix];
    struct page *page;
    dma_addr_t dma;

    // ✅ Allocate from page pool
    page = page_pool_dev_alloc_pages(rq->page_pool);
    if (!page)
        return -ENOMEM;

    // ✅ Get DMA address (already mapped by page pool)
    dma = page_pool_get_dma_addr(page);

    // Store page info
    di->page = page;
    di->addr = dma;

    // Setup WQE (Work Queue Element)
    wqe->data.addr = cpu_to_be64(dma);
    wqe->data.lkey = rq->mkey_be;

    return 0;
}

// Build SKB with page fragments
static struct sk_buff *mlx5e_build_linear_skb(struct mlx5e_rq *rq,
                                             void *va,
                                             u32 frag_size,
                                             u16 headroom,
                                             u32 cqe_bcnt)
{
    struct sk_buff *skb;

    // Build SKB from page
    skb = build_skb(va, frag_size);
    if (!skb)
        return NULL;

    skb_reserve(skb, headroom);
    skb_put(skb, cqe_bcnt);

    return skb;
}

// Handle received packet
static void mlx5e_handle_rx_cqe(struct mlx5e_rq *rq, struct mlx5_cqe64 *cqe)
{
    struct mlx5e_wqe_frag_info *wi;
    struct mlx5e_dma_info *di;
    struct sk_buff *skb;
    u32 cqe_bcnt;
    u16 ci;

    ci = be16_to_cpu(cqe->wqe_counter) & rq->wq.sz_m1;
    wi = &rq->wqe.frag_info[ci];
    di = &rq->wqe.di[ci];

    cqe_bcnt = be32_to_cpu(cqe->byte_cnt);

    // Sync DMA
    dma_sync_single_for_cpu(rq->pdev, di->addr, PAGE_SIZE, DMA_FROM_DEVICE);

    // Build SKB
    skb = mlx5e_build_linear_skb(rq, page_address(di->page),
                                 PAGE_SIZE, wi->offset, cqe_bcnt);
    if (!skb) {
        rq->stats->buff_alloc_err++;
        goto free_page;
    }

    // ✅ Mark for page pool recycling
    skb_mark_for_recycle(skb);

    // Process and deliver
    mlx5e_complete_rx_cqe(rq, cqe, cqe_bcnt, skb);
    napi_gro_receive(rq->cq.napi, skb);

    return;

free_page:
    page_pool_recycle_direct(rq->page_pool, di->page);
}
```

### Example 3: Custom Driver with Page Recycling

```c
// Complete example of custom driver with page fragment management

#define RX_RING_SIZE 256
#define RX_BUF_SIZE  2048

struct custom_rx_buffer {
    struct page *page;
    unsigned int page_offset;
    dma_addr_t dma;
    unsigned int pagecnt_bias;
};

struct custom_priv {
    struct net_device *netdev;
    struct napi_struct napi;
    struct custom_rx_buffer rx_buffers[RX_RING_SIZE];
    unsigned int rx_next;
    struct page_pool *page_pool;
};

// Initialize with page pool
static int custom_init_rx(struct custom_priv *priv)
{
    struct page_pool_params pp_params = {
        .order = 0,
        .flags = PP_FLAG_DMA_MAP | PP_FLAG_DMA_SYNC_DEV,
        .pool_size = RX_RING_SIZE * 2,
        .nid = NUMA_NO_NODE,
        .dev = priv->dev,
        .dma_dir = DMA_FROM_DEVICE,
        .max_len = PAGE_SIZE,
    };
    int i;

    // Create page pool
    priv->page_pool = page_pool_create(&pp_params);
    if (IS_ERR(priv->page_pool))
        return PTR_ERR(priv->page_pool);

    // Allocate initial pages
    for (i = 0; i < RX_RING_SIZE; i++) {
        struct custom_rx_buffer *rx_buf = &priv->rx_buffers[i];
        struct page *page;
        dma_addr_t dma;

        page = page_pool_dev_alloc_pages(priv->page_pool);
        if (!page)
            goto err;

        dma = page_pool_get_dma_addr(page);

        rx_buf->page = page;
        rx_buf->page_offset = 0;
        rx_buf->dma = dma;
        rx_buf->pagecnt_bias = 1;

        // Program hardware
        custom_hw_set_rx_buffer(priv, i, dma, PAGE_SIZE);
    }

    return 0;

err:
    custom_cleanup_rx(priv);
    return -ENOMEM;
}

// NAPI poll with page fragment management
static int custom_poll(struct napi_struct *napi, int budget)
{
    struct custom_priv *priv = container_of(napi, struct custom_priv, napi);
    int work_done = 0;

    while (work_done < budget) {
        struct custom_rx_buffer *rx_buf = &priv->rx_buffers[priv->rx_next];
        struct sk_buff *skb;
        struct page *page;
        unsigned int pkt_len;
        dma_addr_t dma;
        bool reuse_page = false;

        // Check for packet
        pkt_len = custom_hw_get_packet_len(priv, priv->rx_next);
        if (!pkt_len)
            break;

        page = rx_buf->page;

        // Sync DMA
        page_pool_dma_sync_for_cpu(priv->page_pool, page,
                                   rx_buf->page_offset, pkt_len);

        // Allocate SKB
        skb = napi_alloc_skb(napi, 128);
        if (!skb) {
            priv->stats.rx_dropped++;
            goto refill;
        }

        // Add page fragment
        skb_add_rx_frag(skb, 0, page, rx_buf->page_offset,
                       pkt_len, RX_BUF_SIZE);

        // Mark for recycling
        skb_mark_for_recycle(skb);

        // Check if we can reuse page
        rx_buf->page_offset += RX_BUF_SIZE;
        if (rx_buf->page_offset + RX_BUF_SIZE <= PAGE_SIZE &&
            page_count(page) == rx_buf->pagecnt_bias) {
            // Reuse page
            reuse_page = true;
            rx_buf->pagecnt_bias++;
        } else {
            // Page full or shared
            rx_buf->page = NULL;
            rx_buf->page_offset = 0;
        }

        // Process SKB
        skb->protocol = eth_type_trans(skb, priv->netdev);
        napi_gro_receive(napi, skb);

        priv->stats.rx_packets++;
        priv->stats.rx_bytes += pkt_len;

refill:
        // Allocate new page if needed
        if (!reuse_page) {
            page = page_pool_dev_alloc_pages(priv->page_pool);
            if (!page) {
                priv->stats.rx_alloc_failed++;
                break;
            }

            dma = page_pool_get_dma_addr(page);

            rx_buf->page = page;
            rx_buf->page_offset = 0;
            rx_buf->dma = dma;
            rx_buf->pagecnt_bias = 1;

            custom_hw_set_rx_buffer(priv, priv->rx_next, dma, PAGE_SIZE);
        }

        priv->rx_next = (priv->rx_next + 1) % RX_RING_SIZE;
        work_done++;
    }

    if (work_done < budget) {
        napi_complete(napi);
        custom_hw_enable_interrupts(priv);
    }

    return work_done;
}

// Cleanup
static void custom_cleanup_rx(struct custom_priv *priv)
{
    int i;

    for (i = 0; i < RX_RING_SIZE; i++) {
        struct custom_rx_buffer *rx_buf = &priv->rx_buffers[i];

        if (rx_buf->page) {
            page_pool_put_full_page(priv->page_pool, rx_buf->page, false);
            rx_buf->page = NULL;
        }
    }

    if (priv->page_pool) {
        page_pool_destroy(priv->page_pool);
        priv->page_pool = NULL;
    }
}
```

---

## Performance Analysis

### Memory Usage Comparison

```c
// Benchmark: Memory usage for 1000 packets

// Traditional approach (pre-allocated SKBs)
void benchmark_traditional(void)
{
    struct sk_buff *skbs[1000];
    int i;
    size_t total_memory = 0;

    for (i = 0; i < 1000; i++) {
        skbs[i] = netdev_alloc_skb(dev, 1500);
        if (skbs[i])
            total_memory += skbs[i]->truesize;
    }

    printk("Traditional: %zu bytes for 1000 packets\n", total_memory);
    // Typical: ~1,700,000 bytes (1.7 MB)

    for (i = 0; i < 1000; i++)
        if (skbs[i])
            kfree_skb(skbs[i]);
}

// Page fragment approach
void benchmark_page_fragments(void)
{
    struct sk_buff *skbs[1000];
    struct page *pages[250];  // 4 packets per page
    int i, page_idx = 0, offset = 0;
    size_t total_memory = 0;

    // Allocate pages
    for (i = 0; i < 250; i++) {
        pages[i] = alloc_page(GFP_KERNEL);
    }

    // Build SKBs with fragments
    for (i = 0; i < 1000; i++) {
        skbs[i] = napi_alloc_skb(napi, 128);
        if (!skbs[i])
            continue;

        skb_add_rx_frag(skbs[i], 0, pages[page_idx], offset, 1500, 2048);
        total_memory += skbs[i]->truesize;

        offset += 2048;
        if (offset >= PAGE_SIZE) {
            page_idx++;
            offset = 0;
        }
    }

    printk("Page fragments: %zu bytes for 1000 packets\n", total_memory);
    // Typical: ~1,200,000 bytes (1.2 MB)
    // Savings: ~30%

    for (i = 0; i < 1000; i++)
        if (skbs[i])
            kfree_skb(skbs[i]);
}
```

### Performance Metrics

| Metric | Traditional SKB | Page Fragments | Improvement |
|--------|----------------|----------------|-------------|
| **Memory per packet** | ~1700 bytes | ~1200 bytes | 30% less |
| **Allocation time** | ~1000 ns | ~100 ns (pool) | 10x faster |
| **Cache footprint** | Large (1500B) | Small (128B linear) | Better |
| **Page allocation** | Per packet | Shared | Much less |
| **DMA mapping** | Per packet | Cached (pool) | Much faster |
| **Throughput** | 5 Gbps | 10 Gbps | 2x better |

### CPU Usage Comparison

```
Test: 1 million packets/second (1500 byte packets)

Traditional SKB:
├─ Allocation: 1000 ns × 1M = 1000 ms CPU time
├─ DMA mapping: 200 ns × 1M = 200 ms CPU time
├─ Processing: 500 ns × 1M = 500 ms CPU time
└─ Total: 1700 ms CPU time per second = 170% CPU!

Page Fragments with Pool:
├─ Allocation: 100 ns × 1M = 100 ms CPU time
├─ DMA mapping: 0 ns (cached) = 0 ms CPU time
├─ Processing: 500 ns × 1M = 500 ms CPU time
└─ Total: 600 ms CPU time per second = 60% CPU

Savings: 110% CPU (can handle 2.8x more traffic!)
```

### Throughput Benchmarks

```
Hardware: 10 Gigabit Ethernet NIC
Packet size: 1500 bytes
CPU: Intel Xeon E5-2680 v4 @ 2.40GHz

Traditional SKB:
├─ Max throughput: 5.2 Gbps
├─ Max packets/sec: 433,000 pps
├─ CPU usage: 100% (bottleneck)
└─ Limiting factor: Memory allocation

Page Fragments:
├─ Max throughput: 9.8 Gbps
├─ Max packets/sec: 817,000 pps
├─ CPU usage: 65%
└─ Limiting factor: NIC hardware

Page Fragments + Page Pool:
├─ Max throughput: 10.0 Gbps (line rate!)
├─ Max packets/sec: 833,000 pps
├─ CPU usage: 45%
└─ Limiting factor: NIC hardware
```

---

## Best Practices

### 1. Use Page Pool When Possible

```c
// ✅ GOOD: Use page pool for modern drivers
static int driver_init(struct driver_priv *priv)
{
    struct page_pool_params pp_params = {
        .order = 0,
        .flags = PP_FLAG_DMA_MAP | PP_FLAG_DMA_SYNC_DEV,
        .pool_size = RX_RING_SIZE * 2,
        .nid = dev_to_node(priv->dev),  // NUMA-aware
        .dev = priv->dev,
        .dma_dir = DMA_FROM_DEVICE,
    };

    priv->page_pool = page_pool_create(&pp_params);
    return IS_ERR(priv->page_pool) ? PTR_ERR(priv->page_pool) : 0;
}

// ❌ BAD: Manual page allocation without pooling
static int driver_init_bad(struct driver_priv *priv)
{
    // No pooling - will allocate/free pages constantly
    // Much slower!
}
```

### 2. Recycle Pages When Possible

```c
// ✅ GOOD: Reuse pages with space left
if (page_offset + RX_BUF_SIZE <= PAGE_SIZE &&
    page_count(page) == pagecnt_bias) {
    // Reuse page
    page_offset += RX_BUF_SIZE;
    pagecnt_bias++;
} else {
    // Get new page
    page = page_pool_dev_alloc_pages(pool);
}

// ❌ BAD: Always allocate new page
page = alloc_page(GFP_ATOMIC);  // Wasteful!
```

### 3. Use Appropriate Linear Buffer Size

```c
// ✅ GOOD: Small linear buffer for headers
skb = napi_alloc_skb(napi, 128);  // Just enough for headers

// ❌ BAD: Large linear buffer defeats the purpose
skb = napi_alloc_skb(napi, 1500);  // Wastes memory!
```

### 4. Handle Allocation Failures Gracefully

```c
// ✅ GOOD: Handle failures
skb = napi_alloc_skb(napi, 128);
if (!skb) {
    stats->rx_dropped++;
    page_pool_put_page(pool, page, -1, false);
    return;
}

// ❌ BAD: Assume allocation always succeeds
skb = napi_alloc_skb(napi, 128);
skb_add_rx_frag(skb, 0, page, 0, len, PAGE_SIZE);  // CRASH if skb is NULL!
```

### 5. Use GRO for Better Performance

```c
// ✅ GOOD: Use GRO to aggregate packets
napi_gro_receive(napi, skb);

// ❌ BAD: Bypass GRO
netif_receive_skb(skb);  // Misses aggregation opportunity
```

### 6. Mark SKBs for Recycling

```c
// ✅ GOOD: Mark SKB for page pool recycling
skb_add_rx_frag(skb, 0, page, offset, len, truesize);
skb_mark_for_recycle(skb);  // Important!

// ❌ BAD: Forget to mark
skb_add_rx_frag(skb, 0, page, offset, len, truesize);
// Page won't be recycled properly
```

### 7. NUMA-Aware Allocation

```c
// ✅ GOOD: Allocate on same NUMA node as NIC
struct page_pool_params pp_params = {
    .nid = dev_to_node(priv->dev),  // NUMA-aware
    // ...
};

// ❌ BAD: Ignore NUMA
struct page_pool_params pp_params = {
    .nid = NUMA_NO_NODE,  // May allocate on wrong node
    // ...
};
```

### 8. Proper Cleanup

```c
// ✅ GOOD: Clean up properly
static void driver_cleanup(struct driver_priv *priv)
{
    int i;

    // Return all pages to pool
    for (i = 0; i < RX_RING_SIZE; i++) {
        if (priv->rx_buffers[i].page) {
            page_pool_put_full_page(priv->page_pool,
                                   priv->rx_buffers[i].page, false);
        }
    }

    // Destroy pool
    page_pool_destroy(priv->page_pool);
}

// ❌ BAD: Leak pages
static void driver_cleanup_bad(struct driver_priv *priv)
{
    page_pool_destroy(priv->page_pool);  // Pages still referenced!
}
```

### 9. Monitor Statistics

```c
// ✅ GOOD: Track page pool statistics
static void show_stats(struct driver_priv *priv)
{
    struct page_pool_stats stats;

    if (page_pool_get_stats(priv->page_pool, &stats)) {
        printk("Page pool stats:\n");
        printk("  Alloc: %llu\n", stats.alloc_stats.fast);
        printk("  Recycle: %llu\n", stats.recycle_stats.cached);
        printk("  Refill: %llu\n", stats.alloc_stats.refill);
    }
}
```

### 10. Test Under Load

```c
// Test with various packet sizes
// - Small packets (64 bytes) - test page sharing
// - Standard packets (1500 bytes) - typical case
// - Jumbo frames (9000 bytes) - test multiple fragments
// - Mixed sizes - real-world scenario

// Test under memory pressure
// - Ensure graceful degradation
// - Check allocation failure handling
// - Verify no memory leaks
```

---

## Summary and Key Takeaways

### What Are Page Fragments?

**Page fragments** are a modern zero-copy technique where:
- Network packets are received into **memory pages**
- SKBs **reference** pages as fragments instead of copying
- Multiple SKBs can **share** the same page
- Dramatically reduces memory usage and CPU overhead

### The Three Generations

| Generation | Approach | Performance |
|------------|----------|-------------|
| **Gen 1** | DMA → Buffer → memcpy → SKB | ❌ Slow (2 copies) |
| **Gen 2** | DMA → Pre-allocated SKB | ✅ Good (zero-copy) |
| **Gen 3** | DMA → Page → SKB fragment | ⭐ Best (zero-copy + efficient) |

### Key Benefits

1. ✅ **Memory Efficiency** - 30% less memory per packet
2. ✅ **Performance** - 10x faster allocation with page pool
3. ✅ **Scalability** - Handle 2-3x more traffic
4. ✅ **Zero-Copy** - DMA directly to pages
5. ✅ **Page Sharing** - Multiple packets per page
6. ✅ **Better for Jumbo Frames** - No large allocations

### Essential Components

```c
// 1. Page pool (modern approach)
struct page_pool *pool = page_pool_create(&params);

// 2. Allocate page from pool
struct page *page = page_pool_dev_alloc_pages(pool);

// 3. Build SKB with fragment
struct sk_buff *skb = napi_alloc_skb(napi, 128);
skb_add_rx_frag(skb, 0, page, offset, len, truesize);

// 4. Mark for recycling
skb_mark_for_recycle(skb);

// 5. Pass to stack
napi_gro_receive(napi, skb);
```

### Performance Numbers

**At 1 million packets/second:**
- Traditional: 170% CPU (can't keep up!)
- Page fragments: 60% CPU (plenty of headroom)
- **Improvement: 2.8x more capacity**

**Memory usage:**
- Traditional: 1.7 MB for 1000 packets
- Page fragments: 1.2 MB for 1000 packets
- **Savings: 30% less memory**

### When to Use Page Fragments

✅ **Use page fragments when:**
- Building high-performance drivers
- Supporting 10+ Gigabit NICs
- Handling jumbo frames
- Need maximum efficiency
- Kernel 4.20+ available (for page pool)

❌ **Stick with traditional SKBs when:**
- Simple low-speed driver
- Legacy hardware
- Older kernel versions
- Simplicity more important than performance

### Best Practices Summary

1. ✅ Use **page pool** for automatic recycling
2. ✅ **Reuse pages** when space available
3. ✅ Keep **linear buffer small** (128 bytes)
4. ✅ **Handle failures** gracefully
5. ✅ Use **GRO** for aggregation
6. ✅ **Mark for recycling** with page pool
7. ✅ Be **NUMA-aware**
8. ✅ **Monitor statistics**
9. ✅ **Test under load**
10. ✅ **Clean up properly**

---

## Conclusion

**Page fragments** represent the state-of-the-art in Linux network packet reception. By allowing SKBs to reference pages as fragments instead of copying data, they provide:

- **Zero-copy** operation from NIC to application
- **Efficient memory** usage through page sharing
- **High performance** through page pool recycling
- **Scalability** to handle modern high-speed networks

Modern drivers from Intel (ixgbe, i40e), Mellanox (mlx5), and others all use page fragments with page pools to achieve **line-rate performance** at 10, 25, 40, and 100 Gigabit speeds.

If you're writing a new network driver or optimizing an existing one, **page fragments with page pool** should be your default choice for packet reception!

---

**Document Version:** 1.0
**Last Updated:** 2026-03-20
**Related Documentation:**
- [Packet Reception: DMA and SKB Creation Flow](./packet_reception_dma_skb_flow.md)
- [SKB Cloning and Queue Management](./skb_cloning_and_queue_management.md)
- [GFP Flags Guide](./gfp_flags_guide.md)

