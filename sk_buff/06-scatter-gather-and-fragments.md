# Chapter 6: Scatter-Gather and Fragments

The network stack frequently handles packets whose data does not reside in a
single contiguous memory region. Scatter-gather I/O, paged fragments, and
segmentation offloads are the mechanisms the kernel uses to avoid expensive
memory copies while still presenting a coherent packet abstraction. This chapter
examines every layer of that abstraction.

---

## 1. Linear vs Non-Linear sk_buffs

### 1.1 The Linear Region

The simplest form of an `sk_buff` stores all packet data in the contiguous
buffer between the `head` and `end` pointers. The actual payload occupies the
region between `data` and `tail`:

```
┌─────────────────────────────────────────────────┐
│                sk_buff linear buffer             │
├─────────┬──────────────────────────┬────────────┤
│ headroom│      data ◄──► tail      │  tailroom  │
│         │     (packet payload)     │            │
├─────────┼──────────────────────────┼────────────┤
│  head   │                          │    end     │
└─────────┴──────────────────────────┴────────────┘
```

A linear `sk_buff` satisfies two conditions:

1. `skb->data_len == 0`
2. `skb->len == (skb->tail - skb->data)`

All packet bytes are accessible through a simple pointer dereference starting
at `skb->data`.

### 1.2 The Non-Linear Region

When packet data extends beyond the linear buffer, additional bytes are stored
in **paged fragments** or **fragment lists** attached via `skb_shared_info`.
The kernel calls such a buffer *non-linear*.

```c
/* Check whether sk_buff contains non-linear (paged) data */
static inline bool skb_is_nonlinear(const struct sk_buff *skb)
{
    return skb->data_len != 0;  /* non-zero means paged data exists */
}
```

### 1.3 Length Accounting

Two fields cooperate to describe total packet length:

| Field           | Meaning                                              |
|-----------------|------------------------------------------------------|
| `skb->len`      | Total number of data bytes (linear + non-linear)     |
| `skb->data_len` | Number of bytes in the non-linear (paged) region     |

The linear portion is therefore:

```c
unsigned int linear_len = skb->len - skb->data_len;
```

The helper `skb_headlen()` returns exactly this value:

```c
static inline unsigned int skb_headlen(const struct sk_buff *skb)
{
    return skb->len - skb->data_len;
}
```

### 1.4 Why Non-Linear Buffers Exist

Contiguous allocations via `kmalloc()` become expensive and fragile as packet
sizes grow. A 64 KiB TCP segment assembled from GRO would require an
order-4 page allocation, which is prone to failure under memory pressure. Paged
fragments allow the kernel to store payload across many individual pages,
avoiding high-order allocations entirely.

Non-linear buffers also enable **zero-copy** techniques. Userspace pages
pinned by `sendmsg(MSG_ZEROCOPY)` can be attached directly as fragments,
eliminating the copy from user to kernel space.

### 1.5 Diagram: Linear vs Non-Linear

```
┌───────────────────────────────────────────────────────────────┐
│                  LINEAR sk_buff                               │
│                                                               │
│  sk_buff                                                      │
│  ├── data ──────────────────────────────────────► tail        │
│  │        [ Ethernet | IP | TCP | Payload ... ]               │
│  │                                                            │
│  ├── len      = 1500                                          │
│  └── data_len = 0      (no paged data)                        │
└───────────────────────────────────────────────────────────────┘

┌───────────────────────────────────────────────────────────────┐
│                NON-LINEAR sk_buff                              │
│                                                               │
│  sk_buff                                                      │
│  ├── data ────────────────────► tail                          │
│  │        [ Ethernet | IP | TCP ]   (headers only, 66 bytes)  │
│  │                                                            │
│  ├── len      = 65536                                         │
│  ├── data_len = 65470  (payload in paged fragments)           │
│  │                                                            │
│  └── skb_shared_info                                          │
│       ├── nr_frags = 3                                        │
│       ├── frags[0] ──► page X, off=0,   len=16384            │
│       ├── frags[1] ──► page Y, off=0,   len=16384            │
│       ├── frags[2] ──► page Z, off=0,   len=16384            │
│       └── frags[3] ──► page W, off=0,   len=16318            │
└───────────────────────────────────────────────────────────────┘
```

---

## 2. skb_shared_info Fragment Array

### 2.1 Location of skb_shared_info

`skb_shared_info` lives at the *end* of the linear data buffer, immediately
after `skb->end`. The macro `skb_shinfo()` computes its address:

```c
#define skb_shinfo(SKB)  ((struct skb_shared_info *)(skb_end_pointer(SKB)))
```

This placement avoids a separate allocation; the shared info structure is
carved out of the same `kmalloc` block that holds the linear data.

```
┌──────────────────────────────────────────────────────────────┐
│            Allocated buffer (kmalloc)                         │
├──────────┬───────────────────────┬───────────┬───────────────┤
│ headroom │   linear data area    │ tailroom  │skb_shared_info│
│          │  (data ◄──► tail)     │           │               │
├──────────┼───────────────────────┼───────────┼───────────────┤
│  head    │                       │           │     end       │
└──────────┴───────────────────────┴───────────┴───────────────┘
```

### 2.2 The skb_frag_t Structure

Each paged fragment is described by `skb_frag_t`, which is a typedef for
`struct bio_vec` (shared with the block layer):

```c
typedef struct bio_vec skb_frag_t;

struct bio_vec {
    struct page *bv_page;      /* the physical page                */
    unsigned int bv_len;       /* number of bytes in this fragment  */
    unsigned int bv_offset;    /* offset within the page            */
};
```

Accessor macros provide a stable interface regardless of internal layout
changes:

```c
/* Get the page backing fragment i */
static inline struct page *skb_frag_page(const skb_frag_t *frag)
{
    return frag->bv_page;
}

/* Get byte count of fragment i */
static inline unsigned int skb_frag_size(const skb_frag_t *frag)
{
    return frag->bv_len;
}

/* Get offset within the page for fragment i */
static inline unsigned int skb_frag_off(const skb_frag_t *frag)
{
    return frag->bv_offset;
}
```

### 2.3 The Fragment Array

`skb_shared_info` contains a fixed-size array of fragments:

```c
struct skb_shared_info {
    __u8        nr_frags;                    /* number of active frags  */
    /* ... other fields ... */
    skb_frag_t  frags[MAX_SKB_FRAGS];        /* fragment descriptors    */
    /* ... */
};
```

`MAX_SKB_FRAGS` is defined as:

```c
#define MAX_SKB_FRAGS  ((65536 / PAGE_SIZE) + 1)   /* typically 17 on 4K pages */
```

On a system with 4 KiB pages this yields 17 fragments, enough to describe
a full 64 KiB IP datagram in non-linear form. `nr_frags` records how many
entries in the array are actually populated.

### 2.4 Fragment-to-Page Mapping

Each fragment references a `struct page` obtained from the page allocator.
Multiple fragments may reference the same compound page at different offsets,
or each may reference a distinct page.

```
┌────────────────────────────────────────────────────────────────┐
│              Fragment Array ──► Physical Pages                  │
│                                                                │
│  skb_shared_info                                               │
│  ├── nr_frags = 3                                              │
│  │                                                             │
│  ├── frags[0]                                                  │
│  │   ├── bv_page   ──────────────────────► ┌──────────────┐   │
│  │   ├── bv_offset = 0                     │  Page A       │   │
│  │   └── bv_len    = 4096                  │  (4096 bytes) │   │
│  │                                         └──────────────┘   │
│  ├── frags[1]                                                  │
│  │   ├── bv_page   ──────────────────────► ┌──────────────┐   │
│  │   ├── bv_offset = 512                   │  Page B       │   │
│  │   └── bv_len    = 2048                  │  (4096 bytes) │   │
│  │                                         └──────────────┘   │
│  ├── frags[2]                                                  │
│  │   ├── bv_page   ──────────────────────► ┌──────────────┐   │
│  │   ├── bv_offset = 0                     │  Page C       │   │
│  │   └── bv_len    = 1500                  │  (4096 bytes) │   │
│  │                                         └──────────────┘   │
│  └── frags[3..16] — unused (nr_frags = 3)                      │
└────────────────────────────────────────────────────────────────┘
```

### 2.5 Adding a Fragment

The kernel provides `skb_fill_page_desc()` to append a fragment:

```c
/**
 * skb_fill_page_desc - populate fragment i
 * @skb:    sk_buff to modify
 * @i:      fragment index to fill
 * @page:   page backing the fragment
 * @off:    byte offset within page
 * @size:   number of data bytes in this fragment
 */
static inline void skb_fill_page_desc(struct sk_buff *skb, int i,
                                      struct page *page,
                                      int off, int size)
{
    skb_frag_t *frag = &skb_shinfo(skb)->frags[i];

    frag->bv_page   = page;
    frag->bv_offset = off;
    frag->bv_len    = size;

    skb_shinfo(skb)->nr_frags = i + 1;   /* update active count */
}
```

A higher-level helper, `skb_add_rx_frag()`, additionally updates `skb->len`
and `skb->data_len`:

```c
void skb_add_rx_frag(struct sk_buff *skb, int i,
                     struct page *page, int off,
                     int size, unsigned int truesize)
{
    skb_fill_page_desc(skb, i, page, off, size);
    skb->len      += size;       /* total length grows         */
    skb->data_len += size;       /* non-linear portion grows   */
    skb->truesize += truesize;   /* memory accounting          */
}
```

### 2.6 Reference Counting on Fragment Pages

Fragment pages are reference-counted. When an `sk_buff` is cloned, the clone
shares the same fragment pages with elevated reference counts. `skb_frag_ref()`
and `skb_frag_unref()` manage these references:

```c
static inline void skb_frag_ref(struct sk_buff *skb, int f)
{
    get_page(skb_frag_page(&skb_shinfo(skb)->frags[f]));
}

static inline void skb_frag_unref(struct sk_buff *skb, int f)
{
    put_page(skb_frag_page(&skb_shinfo(skb)->frags[f]));
}
```

When `kfree_skb()` or `consume_skb()` is called and the `skb_shared_info`
reference count (`dataref`) reaches zero, each fragment page is released via
`skb_frag_unref()`.

### 2.7 Complete Data Layout Diagram

```
┌────────────────────────────────────────────────────────────────────────┐
│                    Complete sk_buff Data Layout                        │
│                                                                        │
│  sk_buff (metadata)                                                    │
│  ├── head ─────────────────────────────────────────────────┐           │
│  ├── data ──────────────────────┐                          │           │
│  ├── tail ──────────┐           │                          │           │
│  ├── end ───────┐   │           │                          │           │
│  ├── len = 5066 │   │           │                          │           │
│  └── data_len   │   │           │                          │           │
│       = 4000    │   │           │                          │           │
│                 │   │           │                          │           │
│                 ▼   ▼           ▼                          ▼           │
│  Buffer:  ┌─────┬───────────────┬──────┬──────────────────┐           │
│           │head │ linear data   │tail  │ skb_shared_info  │           │
│           │room │  (1066 bytes) │room  │                  │           │
│           └─────┴───────────────┴──────┴──────────────────┘           │
│                                         │                              │
│                                         ├── nr_frags = 2               │
│                                         ├── frags[0] ──► page (2048B)  │
│                                         └── frags[1] ──► page (1952B)  │
│                                                                        │
│  Total: 1066 (linear) + 2048 + 1952 = 5066 bytes                      │
└────────────────────────────────────────────────────────────────────────┘
```

---

## 3. Fragment Lists (frag_list)

### 3.1 Purpose

While the fragment array (`frags[]`) holds references to individual pages,
the **fragment list** (`frag_list`) chains together complete `sk_buff`
structures. It is used primarily during:

1. **IP fragmentation reassembly** — each received IP fragment becomes its own
   `sk_buff`; the reassembled datagram links them via `frag_list`.
2. **Segmentation** — GSO may produce a chain of `sk_buff` structures.
3. **Encapsulation** — some tunneling code attaches inner packets.

### 3.2 Structure

The `frag_list` field resides in `skb_shared_info`:

```c
struct skb_shared_info {
    /* ... */
    struct sk_buff *frag_list;   /* linked list of sk_buffs */
    /* ... */
};
```

Each `sk_buff` in the list is linked through its `next` pointer:

```c
/* Walking the frag_list */
struct sk_buff *frag;
for (frag = skb_shinfo(skb)->frag_list; frag; frag = frag->next) {
    /* process each fragment sk_buff */
    pr_info("frag len=%u\n", frag->len);
}
```

### 3.3 frag_list in IP Reassembly

When the IP layer receives fragments of the same datagram, it collects them
using `inet_frag_queue`. Upon reassembly, the first fragment's `skb_shared_info`
points to the remaining fragments via `frag_list`. The total `skb->len` of the
head `sk_buff` accounts for all data in the chain, and `skb->data_len` includes
the combined length of the chained buffers.

```
┌────────────────────────────────────────────────────────────────────┐
│                   IP Reassembly via frag_list                      │
│                                                                    │
│  Head sk_buff (first fragment)                                     │
│  ├── data ──► [ IP hdr | payload part 1 ]                         │
│  ├── len = 4000  (total reassembled)                               │
│  ├── data_len = 3000  (data in frag_list)                          │
│  └── skb_shared_info                                               │
│       └── frag_list ─┐                                             │
│                      ▼                                             │
│               ┌──────────────┐     ┌──────────────┐               │
│               │  sk_buff #2  │     │  sk_buff #3  │               │
│               │  (frag 2)    │────►│  (frag 3)    │────► NULL     │
│               │  len = 1500  │     │  len = 1500  │               │
│               │  data ──►    │     │  data ──►    │               │
│               │  [payload 2] │     │  [payload 3] │               │
│               └──────────────┘     └──────────────┘               │
└────────────────────────────────────────────────────────────────────┘
```

### 3.4 Length Accounting with frag_list

When `frag_list` is populated, `skb->len` on the head buffer includes the
total data across all chained sk_buffs. `skb->data_len` is increased by the
sum of each chained sk_buff's `len`:

```c
/* Simplified: how the reassembly code updates lengths */
head->len      += frag->len;       /* total grows           */
head->data_len += frag->len;       /* non-linear data grows */
head->truesize += frag->truesize;  /* memory accounting     */
```

### 3.5 Difference: frags[] vs frag_list

| Aspect            | frags[] (paged fragments)           | frag_list                           |
|-------------------|-------------------------------------|-------------------------------------|
| Element type      | `skb_frag_t` (page + offset + len)  | Complete `sk_buff`                  |
| Maximum count     | `MAX_SKB_FRAGS` (17)                | Unbounded (linked list)             |
| Overhead per elem | 16-20 bytes                         | Full `sk_buff` (~256 bytes)         |
| Primary use       | Payload pages, zero-copy TX         | IP reassembly, GSO output           |
| Data access       | `kmap` / `page_address`             | `skb->data` directly                |
| Nesting           | Cannot nest                         | Each sk_buff may itself have frags  |

### 3.6 Walking All Data

To process every byte in an `sk_buff` that may have both `frags[]` and
`frag_list`, the kernel must:

1. Read the linear region (`data` to `tail`).
2. Iterate over `frags[0..nr_frags-1]`, mapping each page.
3. Walk `frag_list`, recursively handling each chained sk_buff's linear +
   paged regions.

This complexity is abstracted by `skb_seq_read()` and `skb_copy_bits()`.

---

## 4. Accessing Non-Linear Data

Direct pointer arithmetic (`skb->data + offset`) only works within the linear
region. The kernel provides several functions to safely access data that may
reside in paged fragments or the fragment list.

### 4.1 skb_header_pointer()

This function returns a pointer to `len` bytes starting at `offset` within
the packet. If the data lies entirely in the linear region, it returns a
direct pointer. Otherwise, it copies the data into a caller-supplied buffer
and returns a pointer to that buffer.

```c
/**
 * skb_header_pointer - safely access packet data at an offset
 * @skb:    the sk_buff
 * @offset: byte offset into the packet
 * @len:    number of bytes needed
 * @buffer: fallback buffer (must be >= len bytes)
 *
 * Returns pointer to data, or NULL on error.
 */
static inline void *skb_header_pointer(const struct sk_buff *skb,
                                       int offset, int len,
                                       void *buffer)
{
    int hlen = skb_headlen(skb);   /* linear data length */

    if (offset + len <= hlen)
        return skb->data + offset;  /* fast path: in linear area */

    /* slow path: copy from non-linear area into buffer */
    if (skb_copy_bits(skb, offset, buffer, len) < 0)
        return NULL;

    return buffer;
}
```

**Usage example** (reading a TCP header that might span the linear boundary):

```c
struct tcphdr _tcph;
struct tcphdr *th;

th = skb_header_pointer(skb, ip_hdrlen(skb),
                        sizeof(_tcph), &_tcph);
if (!th)
    return -EINVAL;   /* not enough data */

/* th now points to the TCP header, safe to use */
__be16 dst_port = th->dest;
```

### 4.2 skb_copy_bits()

Copies `len` bytes from `skb` at `offset` into a kernel buffer `to`. Handles
linear data, paged fragments, and frag_list transparently.

```c
/**
 * skb_copy_bits - copy data from a possibly non-linear sk_buff
 * @skb:    source sk_buff
 * @offset: byte offset to start copying from
 * @to:     destination kernel buffer
 * @len:    number of bytes to copy
 *
 * Returns 0 on success, -EFAULT on error.
 */
int skb_copy_bits(const struct sk_buff *skb, int offset,
                  void *to, int len);
```

Internally, it follows this algorithm:

```
┌───────────────────────────────────────────────────────┐
│              skb_copy_bits() Algorithm                  │
│                                                        │
│  1. Copy from linear region (data..tail)               │
│     └── if offset < headlen, copy min(headlen-off,len) │
│                                                        │
│  2. Copy from frags[0..nr_frags-1]                     │
│     └── for each frag:                                 │
│         ├── kmap_local_page(frag->bv_page)             │
│         ├── memcpy(to, page_addr + off, chunk)         │
│         └── kunmap_local()                             │
│                                                        │
│  3. Copy from frag_list sk_buffs                       │
│     └── recursively call skb_copy_bits() on each       │
│                                                        │
│  4. Return 0 (success) or -EFAULT (not enough data)    │
└───────────────────────────────────────────────────────┘
```

### 4.3 skb_store_bits()

The write counterpart of `skb_copy_bits()`. Writes `len` bytes from a
kernel buffer into the sk_buff at `offset`, traversing fragments as needed:

```c
int skb_store_bits(struct sk_buff *skb, int offset,
                   const void *from, int len);
```

This is used, for example, when computing and inserting checksums into
non-linear packets.

### 4.4 skb_seq_read() — Sequential Iterator

For code that needs to process every byte in order (e.g., pattern matching
in netfilter), `skb_seq_read()` provides a block-at-a-time iterator:

```c
struct skb_seq_state st;
const u8 *data;
unsigned int consumed = 0;
unsigned int block_len;

skb_prepare_seq_read(skb, 0, skb->len, &st);

while ((block_len = skb_seq_read(consumed, &data, &st)) != 0) {
    /* 'data' points to 'block_len' contiguous bytes   */
    /* Process the block...                             */
    process_data(data, block_len);
    consumed += block_len;
}

skb_abort_seq_read(&st);   /* clean up (unmap pages, etc.) */
```

Each call returns the next contiguous block: first the linear region, then
each paged fragment's mapped data, then the linear region of each frag_list
entry, and so on.

```
┌──────────────────────────────────────────────────────┐
│           skb_seq_read() Iteration Order              │
│                                                       │
│  Call 1: linear data      (data..tail)                │
│  Call 2: frags[0] mapped  (page A data)               │
│  Call 3: frags[1] mapped  (page B data)               │
│  Call 4: frag_list[0] linear                          │
│  Call 5: frag_list[0] frags[0]                        │
│  Call 6: frag_list[1] linear                          │
│  ...                                                  │
│  Call N: returns 0        (end of data)                │
└──────────────────────────────────────────────────────┘
```

### 4.5 pskb_may_pull()

This function ensures that at least `len` bytes are available in the linear
region. If less than `len` bytes are linear, it pulls data from the paged
fragments into the linear area (reallocating the buffer if necessary).

```c
/**
 * pskb_may_pull - ensure N bytes are in the linear part
 * @skb:  the sk_buff
 * @len:  number of bytes required in linear area
 *
 * Returns true on success, false if not enough data exists.
 */
static inline bool pskb_may_pull(struct sk_buff *skb, unsigned int len)
{
    if (likely(len <= skb_headlen(skb)))
        return true;              /* already have enough linear data */
    if (unlikely(len > skb->len))
        return false;             /* not enough data at all          */
    return __pskb_pull_tail(skb, len - skb_headlen(skb)) != NULL;
}
```

`__pskb_pull_tail()` performs the actual work:

1. Allocates a new, larger linear buffer if needed.
2. Copies data from the first N paged fragments into the linear area.
3. Releases the consumed fragment pages.
4. Updates `skb->data_len` and `nr_frags`.

**Critical usage pattern** (protocol handlers must pull headers into linear
area before accessing them):

```c
/* Ensure the full TCP header is in the linear part */
if (!pskb_may_pull(skb, sizeof(struct tcphdr)))
    goto drop;

struct tcphdr *th = tcp_hdr(skb);   /* safe dereference now */
```

### 4.6 skb_linearize()

The nuclear option: convert a non-linear sk_buff into a fully linear one.
All paged data is copied into a single contiguous buffer. Expensive but
sometimes necessary.

```c
static inline int skb_linearize(struct sk_buff *skb)
{
    return skb_is_nonlinear(skb) ? __skb_linearize(skb) : 0;
}
```

After `skb_linearize()`, `skb->data_len == 0` and all data is between `data`
and `tail`. The function may fail with `-ENOMEM` if it cannot allocate a
buffer large enough.

### 4.7 Summary of Access Functions

```
┌──────────────────────┬────────────────────────────────────────────┐
│ Function             │ Purpose                                    │
├──────────────────────┼────────────────────────────────────────────┤
│ skb_header_pointer() │ Get pointer to N bytes at offset;          │
│                      │ copies to temp buffer if in paged area     │
├──────────────────────┼────────────────────────────────────────────┤
│ skb_copy_bits()      │ Copy N bytes from skb at offset to buffer  │
├──────────────────────┼────────────────────────────────────────────┤
│ skb_store_bits()     │ Write N bytes into skb at offset           │
├──────────────────────┼────────────────────────────────────────────┤
│ skb_seq_read()       │ Iterate through all data block by block    │
├──────────────────────┼────────────────────────────────────────────┤
│ pskb_may_pull()      │ Ensure N bytes are linear (pull if needed) │
├──────────────────────┼────────────────────────────────────────────┤
│ skb_linearize()      │ Make entire buffer linear (expensive)      │
└──────────────────────┴────────────────────────────────────────────┘
```

---

## 5. GSO (Generic Segmentation Offload)

### 5.1 Concept

Generic Segmentation Offload allows the kernel to construct packets larger
than the network MTU and defer segmentation to a later point. If the NIC
supports hardware segmentation (TSO/USO), the large packet is handed directly
to hardware. If not, GSO performs segmentation in software just before the
packet reaches the driver.

This approach reduces per-packet overhead in the upper layers of the stack
(socket, transport, IP) because a single large `sk_buff` flows through the
entire path rather than many small ones.

### 5.2 GSO Fields in skb_shared_info

```c
struct skb_shared_info {
    /* ... */
    unsigned short gso_size;   /* MSS: max segment payload      */
    unsigned short gso_segs;   /* number of segments expected    */
    unsigned int   gso_type;   /* protocol-specific GSO type     */
    /* ... */
};
```

| Field       | Description                                                |
|-------------|------------------------------------------------------------|
| `gso_size`  | Maximum Segment Size for splitting (typically TCP MSS)     |
| `gso_segs`  | Number of segments the large packet represents             |
| `gso_type`  | Bitmask of `SKB_GSO_*` flags identifying the protocol      |

### 5.3 GSO Types

Common GSO type flags:

```c
enum {
    SKB_GSO_TCPV4      = 1 << 0,   /* TCP over IPv4          */
    SKB_GSO_UDPV4       = 1 << 1,   /* UDP fragmentation IPv4 */
    SKB_GSO_TCPV6      = 1 << 2,   /* TCP over IPv6          */
    SKB_GSO_UDP_L4     = 1 << 5,   /* UDP GSO (USO)          */
    SKB_GSO_GRE        = 1 << 6,   /* GRE tunnel             */
    SKB_GSO_GRE_CSUM   = 1 << 7,   /* GRE with checksum      */
    SKB_GSO_IPXIP4     = 1 << 8,   /* IP-in-IP over IPv4     */
    SKB_GSO_IPXIP6     = 1 << 9,   /* IP-in-IP over IPv6     */
    SKB_GSO_UDP_TUNNEL = 1 << 10,  /* UDP tunnel (VXLAN)     */
    /* ... additional types ... */
};
```

### 5.4 The GSO Path

```
┌────────────────────────────────────────────────────────────────────┐
│                     GSO Segmentation Flow                          │
│                                                                    │
│  Application                                                       │
│  └── write(fd, data, 64000)                                        │
│                                                                    │
│  TCP Layer                                                         │
│  └── Builds ONE sk_buff with 64000 bytes of payload                │
│      ├── gso_size = 1460  (MSS)                                    │
│      ├── gso_segs = 44                                             │
│      └── gso_type = SKB_GSO_TCPV4                                  │
│                                                                    │
│  IP Layer                                                          │
│  └── Passes the single large sk_buff down                          │
│                                                                    │
│  dev_queue_xmit()                                                  │
│  └── Checks: does NIC support TSO?                                 │
│      ├── YES ──► Pass large sk_buff to driver ──► NIC segments     │
│      └── NO  ──► Call skb_gso_segment()                            │
│                  └── Produces 44 individual sk_buffs                │
│                      ├── sk_buff 1: seq=0,    len=1460             │
│                      ├── sk_buff 2: seq=1460, len=1460             │
│                      ├── ...                                       │
│                      └── sk_buff 44: seq=62780, len=1220           │
│                                                                    │
│  Driver / NIC                                                      │
│  └── Transmits individual frames                                   │
└────────────────────────────────────────────────────────────────────┘
```

### 5.5 skb_gso_segment()

This is the entry point for software GSO. It returns a linked list of
`sk_buff` structures, each sized according to `gso_size`:

```c
/**
 * skb_gso_segment - perform GSO segmentation
 * @skb:      the large sk_buff to segment
 * @features: netdev features to honor (e.g., checksum offload)
 *
 * Returns head of sk_buff list, or ERR_PTR on failure.
 */
struct sk_buff *skb_gso_segment(struct sk_buff *skb,
                                netdev_features_t features);
```

The function dispatches to protocol-specific segmentation callbacks
(`tcp_gso_segment`, `udp4_ufo_fragment`, etc.) registered via
`net_offload` structures.

### 5.6 Checking for GSO

```c
/* Does this sk_buff need GSO processing? */
static inline bool skb_is_gso(const struct sk_buff *skb)
{
    return skb_shinfo(skb)->gso_size != 0;
}

/* Validate GSO against device capabilities */
static inline bool skb_gso_ok(struct sk_buff *skb,
                               netdev_features_t features)
{
    return net_gso_ok(features, skb_shinfo(skb)->gso_type);
}
```

### 5.7 GSO Segmentation Diagram

```
┌──────────────────────────────────────────────────────────────────┐
│                 Before GSO (one large sk_buff)                    │
│                                                                   │
│  sk_buff                                                          │
│  ├── len = 64054  (Eth+IP+TCP headers + 64000 payload)           │
│  ├── gso_size = 1460                                              │
│  ├── gso_segs = 44                                                │
│  └── data ──► [ETH][IP][TCP][ 64000 bytes payload ............]  │
│                                                                   │
├═══════════════════ skb_gso_segment() ════════════════════════════┤
│                                                                   │
│                 After GSO (linked list of sk_buffs)               │
│                                                                   │
│  sk_buff #1          sk_buff #2              sk_buff #44          │
│  ├── len=1514        ├── len=1514            ├── len=1274         │
│  ├── next ──────────►├── next ──────────► ...├── next ──► NULL    │
│  └── data ──►        └── data ──►            └── data ──►        │
│   [ETH][IP][TCP]      [ETH][IP][TCP]          [ETH][IP][TCP]     │
│   [1460B payload]     [1460B payload]         [1220B payload]    │
│   seq=0               seq=1460                seq=62780          │
└──────────────────────────────────────────────────────────────────┘
```

---

## 6. GRO (Generic Receive Offload)

### 6.1 Concept

Generic Receive Offload is the receive-path counterpart of GSO. Instead of
delivering every small incoming packet individually up the stack, GRO merges
consecutive packets of the same flow into a single large `sk_buff`. The upper
layers then process one large packet instead of many small ones, reducing
per-packet CPU overhead dramatically.

### 6.2 GRO Criteria for Merging

For two packets to be merged, they must:

1. Belong to the same flow (same 5-tuple for TCP/UDP).
2. Have consecutive sequence numbers (TCP) or be contiguous (UDP GRO).
3. Share compatible header fields (same IP ID progression, same TCP flags
   except PSH, no ECN CE changes).
4. Not exceed a maximum merged size (typically 64 KiB).

### 6.3 The GRO Receive Path

```
┌────────────────────────────────────────────────────────────────┐
│                     GRO Receive Flow                           │
│                                                                │
│  NIC receives packets                                          │
│  └── NAPI poll() calls napi_gro_receive() for each packet     │
│                                                                │
│  napi_gro_receive(napi, skb)                                   │
│  ├── 1. Walk napi->gro_hash[] looking for matching flow        │
│  ├── 2. If match found:                                        │
│  │      ├── Merge skb payload into existing large sk_buff      │
│  │      ├── Update gso_segs count                              │
│  │      └── Free the small incoming skb                        │
│  ├── 3. If no match:                                           │
│  │      └── Add skb to gro_hash[] as new flow head             │
│  └── 4. On flush (timer, napi_complete, max count):            │
│         └── Deliver merged sk_buff up the stack                │
│                                                                │
│  Result: TCP layer sees one sk_buff with 64K of payload        │
│          instead of ~44 individual 1460-byte packets           │
└────────────────────────────────────────────────────────────────┘
```

### 6.4 GRO Hash Table

Since Linux 4.10, GRO uses a hash table (`napi->gro_hash[]`) indexed by
flow hash to find candidate packets for merging. Each bucket is a short
list of `sk_buff` structures representing active flows being aggregated.

```c
struct napi_struct {
    /* ... */
    struct gro_list  gro_hash[GRO_HASH_BUCKETS]; /* flow buckets */
    /* ... */
};

struct gro_list {
    struct list_head list;   /* list of sk_buffs in this bucket */
    int              count;  /* number of flows                 */
};
```

### 6.5 GRO Flush Triggers

A merged sk_buff is flushed (delivered up the stack) when:

1. **Maximum segment count reached** — `gso_segs` hits the configured limit.
2. **Timer expiry** — GRO holds packets for a bounded time.
3. **NAPI poll completion** — `napi_complete_done()` flushes all pending.
4. **Mismatch** — a packet arrives that cannot merge (e.g., different flags).
5. **Explicit flush** — `napi_gro_flush()` called by driver.

### 6.6 GRO API Functions

```c
/* Primary entry point: attempt to merge, deliver if flush needed */
gro_result_t napi_gro_receive(struct napi_struct *napi,
                              struct sk_buff *skb);

/* For drivers that already computed the flow hash */
gro_result_t napi_gro_frags(struct napi_struct *napi);

/* Flush all held GRO packets */
void napi_gro_flush(struct napi_struct *napi, bool flush_old);

/* Complete NAPI poll and flush GRO */
bool napi_complete_done(struct napi_struct *napi, int work_done);
```

### 6.7 GRO Result Codes

```c
typedef enum {
    GRO_MERGED,         /* packet merged into existing flow     */
    GRO_MERGED_FREE,    /* merged; caller should free skb       */
    GRO_HELD,           /* new flow head; skb held for merging  */
    GRO_NORMAL,         /* cannot merge; deliver normally       */
    GRO_CONSUMED,       /* packet consumed by GRO processing    */
} gro_result_t;
```

### 6.8 Relationship Between GRO and GSO

GRO and GSO form a symmetric pair:

```
┌─────────────────────────────────────────────────────────────┐
│                  GRO ←──── Symmetry ────► GSO               │
│                                                              │
│  Receive side:                  Transmit side:               │
│  ┌─────────────┐               ┌─────────────┐              │
│  │ Small pkts  │               │ Large pkt   │              │
│  │ from NIC    │               │ from socket │              │
│  │ 1460B each  │               │ 64000B      │              │
│  └──────┬──────┘               └──────┬──────┘              │
│         │ GRO merge                   │ GSO segment          │
│         ▼                             ▼                      │
│  ┌─────────────┐               ┌─────────────┐              │
│  │ One large   │               │ Small pkts  │              │
│  │ sk_buff     │               │ to NIC      │              │
│  │ 64000B      │               │ 1460B each  │              │
│  └─────────────┘               └─────────────┘              │
│                                                              │
│  Both use gso_size, gso_segs, gso_type in skb_shared_info   │
└─────────────────────────────────────────────────────────────┘
```

A GRO-merged packet is indistinguishable from a GSO packet; if the stack
later needs to forward it, GSO can segment it again without any special
handling.

---

## 7. TSO (TCP Segmentation Offload) and Hardware Offloads

### 7.1 TCP Segmentation Offload (TSO)

TSO moves the work of splitting large TCP segments into MTU-sized frames from
the CPU to the NIC. The kernel sends a single large `sk_buff` (up to 64 KiB)
to the driver, and the NIC's hardware or firmware creates individual Ethernet
frames on the wire.

### 7.2 Feature Flags

NICs advertise offload capabilities through `netdev_features_t`:

```c
#define NETIF_F_TSO      __NETIF_F(TSO)       /* TCP segmentation IPv4   */
#define NETIF_F_TSO6     __NETIF_F(TSO6)      /* TCP segmentation IPv6   */
#define NETIF_F_TSO_ECN  __NETIF_F(TSO_ECN)   /* TSO with ECN support    */
#define NETIF_F_UFO      __NETIF_F(UFO)       /* UDP fragmentation       */
#define NETIF_F_GSO      __NETIF_F(GSO)       /* Generic segmentation    */
#define NETIF_F_SG       __NETIF_F(SG)        /* Scatter-gather DMA      */
```

A NIC that supports TSO typically also requires `NETIF_F_SG` (scatter-gather)
since the large packet's data is usually spread across multiple pages.

### 7.3 TSO Flow

```
┌──────────────────────────────────────────────────────────────────┐
│                       TSO Transmit Flow                          │
│                                                                  │
│  TCP Layer                                                       │
│  └── Creates sk_buff with 64000 bytes payload                    │
│      ├── gso_size = 1460                                         │
│      └── gso_type = SKB_GSO_TCPV4                                │
│                                                                  │
│  IP Layer                                                        │
│  └── Sets IP header (total_len = full size, id = N)              │
│                                                                  │
│  dev_queue_xmit()                                                │
│  └── NIC has NETIF_F_TSO? ──► YES ──► send directly to driver   │
│                                                                  │
│  NIC Driver                                                      │
│  └── Programs TX descriptors:                                    │
│      ├── Context descriptor: MSS=1460, header lengths            │
│      └── Data descriptors: point to header + payload pages       │
│                                                                  │
│  NIC Hardware                                                    │
│  └── For each MSS-sized chunk:                                   │
│      ├── Duplicates Ethernet + IP + TCP headers                  │
│      ├── Adjusts: IP total_len, IP id, TCP seq, TCP checksum     │
│      └── Transmits frame on wire                                 │
│                                                                  │
│  Wire: 44 individual 1514-byte Ethernet frames                   │
└──────────────────────────────────────────────────────────────────┘
```

### 7.4 What the NIC Must Adjust Per Segment

For each segment the NIC creates from the large packet, it must update:

| Header Field     | Adjustment                                          |
|------------------|-----------------------------------------------------|
| IP total length  | Set to header_len + segment_payload_len             |
| IP identification| Increment by 1 for each segment                    |
| IP checksum      | Recompute (or offloaded)                            |
| TCP sequence     | Advance by MSS for each segment                    |
| TCP FIN/PSH      | Only set on the final segment                       |
| TCP checksum     | Recompute for each segment's data                   |
| Ethernet FCS     | Recompute                                           |

### 7.5 GSO as Software Fallback

When a NIC does not support TSO (or the feature is disabled), the kernel's
GSO code performs the same segmentation in software. The `validate_xmit_skb()`
function checks whether the device can handle the GSO packet:

```c
/* Simplified logic in validate_xmit_skb() */
if (skb_is_gso(skb) && !skb_gso_ok(skb, dev->features)) {
    /* NIC cannot handle this GSO type; segment in software */
    struct sk_buff *segs = skb_gso_segment(skb, dev->features);
    /* ... transmit each segment individually ... */
}
```

### 7.6 UFO (UDP Fragmentation Offload)

UFO is the UDP equivalent of TSO. The kernel builds one large UDP datagram
and lets the NIC (or GSO software fallback) split it into IP fragments:

```c
/* Check for UFO capability */
if (dev->features & NETIF_F_UFO) {
    /* Send large UDP datagram; NIC will fragment */
}
```

UFO support in hardware is less common than TSO. The kernel has largely
moved to `SKB_GSO_UDP_L4` (UDP GSO / USO) which segments at the UDP layer
rather than relying on IP fragmentation.

### 7.7 LRO (Large Receive Offload) — Hardware GRO

LRO is the hardware counterpart of GRO. The NIC merges incoming TCP segments
in hardware before delivering them to the host. However, LRO has significant
limitations:

1. Cannot be used on forwarding/routing paths (modifies headers irreversibly).
2. Some implementations lose information (e.g., per-packet timestamps).
3. GRO has largely supplanted LRO as the preferred receive offload.

```c
#define NETIF_F_LRO  __NETIF_F(LRO)   /* Large Receive Offload */
```

Modern best practice: use GRO (`NETIF_F_GRO`) and disable LRO.

---

## 8. Scatter-Gather I/O (SG)

### 8.1 The Problem: Contiguous DMA

Without scatter-gather, the NIC can only DMA from a single contiguous memory
region. If the packet data is spread across multiple pages (non-linear
sk_buff), the kernel must first `skb_linearize()` it — copying all fragments
into one buffer. This is expensive for large packets.

### 8.2 The Solution: NETIF_F_SG

When a NIC advertises `NETIF_F_SG`, it can DMA from multiple non-contiguous
memory regions. Each paged fragment is DMA-mapped individually, and the
driver programs one TX descriptor per fragment.

```c
/* Check for scatter-gather support */
if (dev->features & NETIF_F_SG) {
    /* Can transmit non-linear sk_buffs directly */
} else {
    /* Must linearize before transmit */
    if (skb_linearize(skb))
        goto drop;
}
```

### 8.3 DMA Mapping of Fragments

Each fragment must be mapped for DMA before the NIC can read it. The kernel
provides `skb_frag_dma_map()`:

```c
/**
 * skb_frag_dma_map - DMA-map a paged fragment
 * @dev:       device for DMA mapping
 * @frag:      the fragment to map
 * @offset:    additional offset within fragment
 * @size:      number of bytes to map
 * @dir:       DMA direction (DMA_TO_DEVICE for TX)
 *
 * Returns DMA address, or DMA_MAPPING_ERROR on failure.
 */
dma_addr_t skb_frag_dma_map(struct device *dev,
                             const skb_frag_t *frag,
                             size_t offset, size_t size,
                             enum dma_data_direction dir);
```

### 8.4 TX Descriptor Ring with Scatter-Gather

A typical transmit path for a non-linear sk_buff:

```c
/* Simplified scatter-gather transmit (pseudo-code) */
int my_driver_xmit(struct sk_buff *skb, struct net_device *dev)
{
    struct my_tx_ring *ring = &priv->tx_ring;
    dma_addr_t dma;
    int i;

    /* 1. Map the linear (header) portion */
    dma = dma_map_single(dev->dev.parent,
                         skb->data,
                         skb_headlen(skb),   /* linear length */
                         DMA_TO_DEVICE);
    ring->desc[ring->next].addr = dma;
    ring->desc[ring->next].len  = skb_headlen(skb);
    ring->desc[ring->next].flags = DESC_FIRST;
    ring->next++;

    /* 2. Map each paged fragment */
    for (i = 0; i < skb_shinfo(skb)->nr_frags; i++) {
        skb_frag_t *frag = &skb_shinfo(skb)->frags[i];

        dma = skb_frag_dma_map(dev->dev.parent,
                                frag, 0,
                                skb_frag_size(frag),
                                DMA_TO_DEVICE);
        ring->desc[ring->next].addr = dma;
        ring->desc[ring->next].len  = skb_frag_size(frag);

        /* Mark the last fragment */
        if (i == skb_shinfo(skb)->nr_frags - 1)
            ring->desc[ring->next].flags = DESC_LAST;

        ring->next++;
    }

    /* 3. Ring the doorbell */
    writel(ring->next, priv->doorbell_reg);

    return NETDEV_TX_OK;
}
```

### 8.5 Scatter-Gather DMA Diagram

```
┌──────────────────────────────────────────────────────────────────────┐
│              Scatter-Gather DMA: Non-Linear TX                       │
│                                                                      │
│  sk_buff                                                             │
│  ├── data ──► [ETH|IP|TCP]  (66 bytes, linear)                      │
│  └── skb_shared_info                                                 │
│       ├── frags[0] ──► Page A (1460 bytes)                           │
│       ├── frags[1] ──► Page B (1460 bytes)                           │
│       └── frags[2] ──► Page C (1014 bytes)                           │
│                                                                      │
│  TX Descriptor Ring                                                  │
│  ┌────────┬──────────────────────────────┬───────┬───────┐          │
│  │ Index  │ DMA Address                  │ Length│ Flags │          │
│  ├────────┼──────────────────────────────┼───────┼───────┤          │
│  │   0    │ dma_map(skb->data)           │   66  │ FIRST │          │
│  ├────────┼──────────────────────────────┼───────┼───────┤          │
│  │   1    │ skb_frag_dma_map(frags[0])   │ 1460  │       │          │
│  ├────────┼──────────────────────────────┼───────┼───────┤          │
│  │   2    │ skb_frag_dma_map(frags[1])   │ 1460  │       │          │
│  ├────────┼──────────────────────────────┼───────┼───────┤          │
│  │   3    │ skb_frag_dma_map(frags[2])   │ 1014  │ LAST  │          │
│  └────────┴──────────────────────────────┴───────┴───────┘          │
│                                                                      │
│  NIC Hardware                                                        │
│  └── DMA engine reads from 4 separate memory locations               │
│      └── Assembles one contiguous frame on the wire                  │
│          [ETH|IP|TCP|1460B|1460B|1014B] = 4000 byte frame            │
└──────────────────────────────────────────────────────────────────────┘
```

### 8.6 DMA Unmapping on Completion

After the NIC signals transmission completion (usually via an interrupt and
completion queue), the driver must unmap each DMA region:

```c
/* TX completion handler (simplified) */
void my_driver_tx_complete(struct my_tx_ring *ring)
{
    while (ring->clean != ring->next) {
        struct tx_desc *desc = &ring->desc[ring->clean];

        if (desc->flags & DESC_FIRST) {
            /* Unmap linear data */
            dma_unmap_single(dev, desc->addr,
                             desc->len, DMA_TO_DEVICE);
        } else {
            /* Unmap fragment */
            dma_unmap_page(dev, desc->addr,
                           desc->len, DMA_TO_DEVICE);
        }

        ring->clean++;
    }

    /* Now safe to free the sk_buff */
    dev_consume_skb_any(skb);
}
```

### 8.7 Without Scatter-Gather: Linearization Cost

When `NETIF_F_SG` is absent, `validate_xmit_skb()` calls `skb_linearize()`
to collapse all fragments into a single buffer. The cost:

1. **Memory allocation** — must allocate a contiguous buffer large enough for
   the entire packet. For a 64 KiB GSO packet this is an order-4 allocation.
2. **Memory copy** — every fragment page must be mapped and copied.
3. **Cache pollution** — the copy touches cache lines that may evict useful
   data.

For high-throughput paths, the absence of SG support is a severe performance
penalty. Virtually all modern NICs support scatter-gather.

### 8.8 Scatter-Gather and Checksum Offload

SG and checksum offload are closely related. When the kernel uses paged
fragments, computing a software checksum requires mapping each page — an
expensive operation. If the NIC supports `NETIF_F_HW_CSUM` or
`NETIF_F_IP_CSUM`, the checksum is computed in hardware over the DMA'd data,
avoiding this cost entirely.

```c
/* Common feature combination for high-performance NICs */
dev->features |= NETIF_F_SG        /* scatter-gather DMA        */
              |  NETIF_F_TSO       /* TCP segmentation offload   */
              |  NETIF_F_TSO6      /* TSO for IPv6               */
              |  NETIF_F_HW_CSUM   /* hardware checksum          */
              |  NETIF_F_GRO;      /* generic receive offload    */
```

### 8.9 End-to-End Example: sendfile() with SG

The `sendfile()` system call demonstrates the full zero-copy scatter-gather
path:

```
┌──────────────────────────────────────────────────────────────────┐
│              sendfile() Zero-Copy SG Path                        │
│                                                                  │
│  1. Application calls sendfile(sock_fd, file_fd, ...)            │
│                                                                  │
│  2. Kernel pins file pages in page cache                         │
│     └── No copy from page cache to socket buffer                 │
│                                                                  │
│  3. TCP builds sk_buff:                                          │
│     ├── Linear area: TCP/IP headers only (66 bytes)              │
│     └── frags[]: references to page cache pages                  │
│         ├── frags[0] ──► page cache page 1                       │
│         ├── frags[1] ──► page cache page 2                       │
│         └── ...                                                  │
│                                                                  │
│  4. Driver DMA-maps each fragment                                │
│     └── NIC reads headers + payload from separate locations      │
│                                                                  │
│  5. NIC assembles and transmits frame                            │
│     └── ZERO copies of payload data                              │
└──────────────────────────────────────────────────────────────────┘
```

### 8.10 Summary of Offload Features

```
┌──────────────────┬────────────┬────────────────────────────────────┐
│ Feature          │ Direction  │ Description                        │
├──────────────────┼────────────┼────────────────────────────────────┤
│ NETIF_F_SG       │ TX         │ Scatter-gather DMA from fragments  │
├──────────────────┼────────────┼────────────────────────────────────┤
│ NETIF_F_TSO      │ TX         │ TCP segmentation in hardware (v4)  │
├──────────────────┼────────────┼────────────────────────────────────┤
│ NETIF_F_TSO6     │ TX         │ TCP segmentation in hardware (v6)  │
├──────────────────┼────────────┼────────────────────────────────────┤
│ NETIF_F_UFO      │ TX         │ UDP fragmentation offload          │
├──────────────────┼────────────┼────────────────────────────────────┤
│ NETIF_F_GSO      │ TX         │ Generic segmentation (software)    │
├──────────────────┼────────────┼────────────────────────────────────┤
│ NETIF_F_GRO      │ RX         │ Generic receive offload (software) │
├──────────────────┼────────────┼────────────────────────────────────┤
│ NETIF_F_LRO      │ RX         │ Large receive offload (hardware)   │
├──────────────────┼────────────┼────────────────────────────────────┤
│ NETIF_F_HW_CSUM  │ TX         │ Hardware checksum computation      │
├──────────────────┼────────────┼────────────────────────────────────┤
│ NETIF_F_RXCSUM   │ RX         │ Hardware RX checksum verification  │
└──────────────────┴────────────┴────────────────────────────────────┘
```

---

## Appendix A: Key Data Structure Reference

### A.1 skb_shared_info (Fragment-Related Fields)

```c
struct skb_shared_info {
    __u8            flags;
    __u8            meta_len;
    __u8            nr_frags;          /* paged fragment count          */
    __u8            tx_flags;
    unsigned short  gso_size;          /* MSS for segmentation          */
    unsigned short  gso_segs;          /* segment count                 */
    struct sk_buff  *frag_list;        /* chain of sk_buffs             */
    skb_frag_t      frags[MAX_SKB_FRAGS]; /* paged fragment array      */
    unsigned int    gso_type;          /* GSO protocol type             */
    /* ... refcount, destructor, etc. ... */
};
```

### A.2 skb_frag_t (bio_vec)

```c
struct bio_vec {
    struct page    *bv_page;    /* physical page          */
    unsigned int    bv_len;     /* data length in bytes   */
    unsigned int    bv_offset;  /* offset within page     */
};
```

### A.3 Frequently Used Helper Functions

| Function                  | Purpose                                      |
|---------------------------|----------------------------------------------|
| `skb_is_nonlinear(skb)`  | Check if skb has paged data                  |
| `skb_headlen(skb)`       | Linear data length                           |
| `skb_shinfo(skb)`        | Get skb_shared_info pointer                  |
| `skb_frag_page(frag)`    | Get page from fragment                       |
| `skb_frag_size(frag)`    | Get fragment data size                       |
| `skb_frag_off(frag)`     | Get fragment page offset                     |
| `skb_fill_page_desc()`   | Populate a fragment entry                    |
| `skb_add_rx_frag()`      | Add fragment and update lengths              |
| `pskb_may_pull()`        | Ensure N bytes linear                        |
| `skb_linearize()`        | Make entire skb linear                       |
| `skb_copy_bits()`        | Copy from non-linear skb                     |
| `skb_store_bits()`       | Write to non-linear skb                      |
| `skb_header_pointer()`   | Safe access to header data                   |
| `skb_seq_read()`         | Sequential data iterator                     |
| `skb_is_gso(skb)`        | Check if GSO is active                       |
| `skb_gso_segment()`      | Perform software segmentation                |
| `skb_frag_dma_map()`     | DMA-map a fragment                           |

---

## Appendix B: Debugging Non-Linear sk_buffs

### B.1 Printing Fragment Information

```c
/* Debug: dump all fragments of an sk_buff */
static void skb_dump_frags(const struct sk_buff *skb)
{
    int i;

    pr_info("skb %p: len=%u data_len=%u headlen=%u nr_frags=%u\n",
            skb, skb->len, skb->data_len,
            skb_headlen(skb), skb_shinfo(skb)->nr_frags);

    for (i = 0; i < skb_shinfo(skb)->nr_frags; i++) {
        const skb_frag_t *f = &skb_shinfo(skb)->frags[i];
        pr_info("  frag[%d]: page=%p offset=%u size=%u\n",
                i, skb_frag_page(f),
                skb_frag_off(f), skb_frag_size(f));
    }

    if (skb_shinfo(skb)->frag_list) {
        struct sk_buff *frag;
        pr_info("  frag_list:\n");
        for (frag = skb_shinfo(skb)->frag_list;
             frag; frag = frag->next) {
            pr_info("    skb=%p len=%u\n", frag, frag->len);
        }
    }

    if (skb_is_gso(skb)) {
        pr_info("  GSO: size=%u segs=%u type=0x%x\n",
                skb_shinfo(skb)->gso_size,
                skb_shinfo(skb)->gso_segs,
                skb_shinfo(skb)->gso_type);
    }
}
```

### B.2 Common Pitfalls

1. **Accessing paged data via skb->data** — only works for the linear part.
   Always use `skb_header_pointer()` or `pskb_may_pull()` first.

2. **Forgetting to update data_len** — when adding fragments manually,
   `skb->data_len` and `skb->len` must both be updated.

3. **Linearizing unnecessarily** — `skb_linearize()` is expensive. Use
   `pskb_may_pull()` to pull only what is needed.

4. **DMA mapping lifetime** — fragment pages must remain mapped for the
   entire duration the NIC might access them. Unmap only after TX completion.

5. **GRO vs LRO confusion** — GRO preserves packet boundaries and works
   with forwarding; LRO does not. Always prefer GRO.

---

*Next: [Chapter 7: Queues and Lists](07-queues-and-lists.md)*
