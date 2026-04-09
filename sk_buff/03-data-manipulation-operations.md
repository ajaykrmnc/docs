# Chapter 3: Data Manipulation Operations

The Linux kernel networking stack processes millions of packets per second on modern
hardware. At that scale, every unnecessary `memcpy` is a measurable performance
regression. The `sk_buff` structure achieves its remarkable efficiency through a
disciplined pointer-manipulation model: rather than copying data between buffers as
headers are added or removed, the kernel simply moves pointers within a single,
pre-allocated linear buffer. This chapter provides a rigorous treatment of every
data-manipulation function in the `sk_buff` API, with annotated diagrams showing
the exact pointer movements for each operation.

---

## 1. Overview: The Zero-Copy Philosophy

### 1.1 Why Pointer Manipulation Instead of Data Copying

Traditional network stacks in textbook implementations copy packet data at every
layer boundary. When the TCP layer hands a segment to the IP layer, the IP layer
allocates a new buffer, copies the TCP segment into it, and prepends the IP header.
The Ethernet layer then allocates yet another buffer, copies the IP datagram, and
prepends the Ethernet header. For a single 1500-byte packet, this naive approach
performs three allocations and copies roughly 4500 bytes of data.

The Linux kernel rejects this model entirely. Instead, it allocates a single buffer
large enough to hold all headers and payload from the start. Protocol layers then
add or remove headers by adjusting pointers within that fixed buffer. No data moves;
only metadata changes.

The performance implications are significant:

- **Zero copies during encapsulation**: Adding an Ethernet, IP, or TCP header is an
  O(1) pointer adjustment, not an O(n) memcpy.
- **Cache friendliness**: The entire packet resides in one contiguous memory region,
  maximizing L1/L2 cache hit rates.
- **Reduced allocator pressure**: One `kmalloc` per packet instead of one per layer.

### 1.2 The head/data/tail/end Pointer Model

Every `sk_buff` maintains four fundamental pointers into its linear data buffer:

```
┌──────────────────────────────────────────────────────────┐
│                   sk_buff structure                      │
│                                                          │
│   head ──────► start of allocated buffer                 │
│   data ──────► start of current packet data              │
│   tail ──────► end of current packet data                │
│   end  ──────► end of allocated buffer                   │
│                                                          │
│   len  ──────► total data length (linear + paged)        │
│   data_len ──► length of paged (non-linear) data         │
│                                                          │
└──────────────────────────────────────────────────────────┘
```

These pointers divide the linear buffer into four logical regions:

```
┌─────────────┬──────────────────────┬─────────────┐
│  headroom   │     packet data      │  tailroom   │
│             │                      │             │
│ head ► data │   data ► tail        │ tail ► end  │
└─────────────┴──────────────────────┴─────────────┘
```

Detailed memory layout with all four pointers:

```
head                data                 tail                end
 │                   │                    │                   │
 ▼                   ▼                    ▼                   ▼
 ┌───────────────────┬────────────────────┬───────────────────┐
 │                   │                    │                   │
 │    headroom       │    packet data     │    tailroom       │
 │                   │                    │                   │
 │  (space for       │  (current packet   │  (space for       │
 │   prepending      │   content: hdrs    │   appending       │
 │   headers)        │   + payload)       │   data)           │
 │                   │                    │                   │
 └───────────────────┴────────────────────┴───────────────────┘
 │◄─── skb_headroom ─►│◄──── skb->len ───►│◄── skb_tailroom ►│
```

**Key invariants:**
- `head <= data <= tail <= end` (always, enforced by BUG_ON checks)
- `skb->len = (tail - data) + skb->data_len`
- Linear data length: `skb_headlen(skb) = tail - data`
- Headroom: `skb_headroom(skb) = data - head`
- Tailroom: `skb_tailroom(skb) = end - tail`

### 1.3 How Protocol Headers Are Added and Removed

During **packet transmission** (egress), protocol layers work from the inside out.
The transport layer writes the payload, then the transport header, then the network
header, and finally the link-layer header. Each header is prepended by moving the
`data` pointer backward (via `skb_push`).

During **packet reception** (ingress), protocol layers work from the outside in.
The link layer strips the Ethernet header, the network layer strips the IP header,
and the transport layer strips the TCP/UDP header. Each header is consumed by moving
the `data` pointer forward (via `skb_pull`).

```
Transmit path (building a packet):         Receive path (parsing a packet):

  Payload                                    ┌─ ETH ─┬─ IP ─┬─ TCP ─┬─ Payload ─┐
  ┌──────────┐                               │       │      │       │           │
  │  data    │                               └───────┴──────┴───────┴───────────┘
  └──────────┘                                 data
       │ skb_push(tcp_hdr)                          │ skb_pull(ETH_HLEN)
       ▼                                            ▼
  ┌────┬──────────┐                            ┌───────┬──────┬───────┬───────────┐
  │TCP │  data    │                            │  ETH  │  IP  │  TCP  │  Payload  │
  └────┴──────────┘                            └───────┴──────┴───────┴───────────┘
  data                                                  data
       │ skb_push(ip_hdr)                                  │ skb_pull(ip_hdrlen)
       ▼                                                   ▼
  ┌──┬────┬──────────┐                         ┌───────┬──────┬───────┬───────────┐
  │IP│TCP │  data    │                         │  ETH  │  IP  │  TCP  │  Payload  │
  └──┴────┴──────────┘                         └───────┴──────┴───────┴───────────┘
  data                                                         data
       │ skb_push(eth_hdr)                                        │ skb_pull(tcp_hdrlen)
       ▼                                                          ▼
  ┌───┬──┬────┬──────────┐                     ┌───────┬──────┬───────┬───────────┐
  │ETH│IP│TCP │  data    │                     │  ETH  │  IP  │  TCP  │  Payload  │
  └───┴──┴────┴──────────┘                     └───────┴──────┴───────┴───────────┘
  data                                                                 data
```

This elegant symmetry -- `skb_push` on transmit, `skb_pull` on receive -- means the
same buffer structure serves both paths without any data movement.

---

## 2. skb_reserve(skb, len)

### 2.1 Purpose and Semantics

`skb_reserve` increases the headroom of an **empty** `sk_buff` by advancing both
the `data` and `tail` pointers forward by `len` bytes. It does not add any data to
the buffer; it merely carves out space at the beginning that will later be consumed
by `skb_push` calls to prepend protocol headers.

**Critical constraint**: `skb_reserve` must be called on a freshly allocated, empty
`sk_buff` -- that is, before any data has been added via `skb_put`. Calling it after
data has been placed in the buffer would silently corrupt the packet by shifting the
data pointer past the beginning of the actual data.

### 2.2 Kernel Implementation

```c
/**
 * skb_reserve - adjust headroom
 * @skb: buffer to alter
 * @len: bytes to move
 *
 * Increase the headroom of an empty &sk_buff by reducing the tail
 * room. This is only allowed for an empty buffer.
 */
static inline void skb_reserve(struct sk_buff *skb, int len)
{
    skb->data += len;    /* advance data pointer forward  */
    skb->tail += len;    /* advance tail pointer forward  */
}
```

Note the absence of any bounds checking in the production kernel. The function
trusts that the caller has verified sufficient space exists. In debug builds
(`CONFIG_DEBUG_NET`), additional assertions may fire.

### 2.3 Before/After Diagram

**Before `skb_reserve(skb, len)`** (freshly allocated skb):

```
head                                                         end
 │                                                            │
 ▼                                                            ▼
 ┌────────────────────────────────────────────────────────────┐
 │                                                            │
 │              entire buffer is tailroom                     │
 │                                                            │
 └────────────────────────────────────────────────────────────┘
 ▲                                                            ▲
 │                                                            │
data                                                        tail
(= head)                                                   (= end)

 headroom = 0
 tailroom = end - head
 skb->len = 0
```

**After `skb_reserve(skb, len)`**:

```
head          data                                           end
 │              │                                             │
 ▼              ▼                                             ▼
 ┌──────────────┬─────────────────────────────────────────────┐
 │              │                                             │
 │   headroom   │              tailroom                       │
 │   (len bytes)│                                             │
 └──────────────┴─────────────────────────────────────────────┘
                ▲                                             ▲
                │                                             │
              tail                                           end
              (= data)

 headroom = len
 tailroom = (end - head) - len
 skb->len = 0   (still empty, no data added yet)
```

### 2.4 Common Usage Patterns

**Pattern 1: IP alignment padding**

Many network interface cards (NICs) deliver frames with the IP header at a 2-byte
offset. To ensure the IP header is 4-byte aligned after the 14-byte Ethernet
header, drivers reserve 2 bytes:

```c
skb = netdev_alloc_skb(dev, length + NET_IP_ALIGN);  /* NET_IP_ALIGN = 2 */
if (!skb)
    return -ENOMEM;

skb_reserve(skb, NET_IP_ALIGN);  /* align IP header on 4-byte boundary */
/* Now copy received data into skb via skb_put */
```

Memory layout after the reserve:

```
head    data                                                 end
 │        │                                                   │
 ▼        ▼                                                   ▼
 ┌────────┬───────────────────────────────────────────────────┐
 │ 2 bytes│                                                   │
 │ align  │             available for packet data             │
 │ pad    │                                                   │
 └────────┴───────────────────────────────────────────────────┘
          ▲
          │
        tail (= data, buffer still empty)
```

**Pattern 2: Reserve space for all protocol headers**

When the transport layer creates a packet, it must reserve space for every header
that will be prepended later:

```c
/* Calculate total header space needed */
int hdr_len = MAX_TCP_HEADER;  /* includes TCP + IP + link-layer headers */

skb = alloc_skb(hdr_len + payload_len, GFP_KERNEL);
if (!skb)
    return -ENOMEM;

skb_reserve(skb, hdr_len);  /* reserve space for all headers */
/* Now payload can be added with skb_put, and headers prepended with skb_push */
```

```
head                            data                         end
 │                                │                           │
 ▼                                ▼                           ▼
 ┌────────────────────────────────┬───────────────────────────┐
 │                                │                           │
 │   reserved for ETH+IP+TCP     │   available for payload   │
 │   headers (MAX_TCP_HEADER)    │   (payload_len bytes)     │
 │                                │                           │
 └────────────────────────────────┴───────────────────────────┘
                                  ▲
                                  │
                                tail (= data)
```

### 2.5 Why Not Just Set data Directly?

One might wonder why a function is needed at all when it simply adds `len` to two
pointers. The abstraction serves several purposes:

1. **Semantic clarity**: `skb_reserve` communicates intent ("I am making room for
   future headers") in a way that raw pointer arithmetic does not.
2. **Debug instrumentation**: Debug builds can insert assertions verifying the
   buffer is empty and the reserve does not exceed the buffer size.
3. **Maintainability**: If the internal representation of `tail` changes (e.g., from
   a pointer to an offset, as it has in some kernel versions), only the inline
   function needs updating.

---

## 3. skb_put(skb, len)

### 3.1 Purpose and Semantics

`skb_put` extends the data area at the **tail** of the buffer. It moves the `tail`
pointer forward by `len` bytes and increments `skb->len` by the same amount. The
function returns a pointer to the beginning of the newly available area, which the
caller can then write data into.

This is the primary function for adding payload data to a packet, as well as for
appending any data after the current content.

### 3.2 Kernel Implementation

```c
/**
 * skb_put - add data to a buffer
 * @skb: buffer to use
 * @len: amount of data to add
 *
 * This function extends the used data area of the buffer at the
 * tail end. A pointer to the first byte of the extra data is returned.
 * If this would exceed the total buffer size the kernel will panic.
 */
void *skb_put(struct sk_buff *skb, unsigned int len)
{
    void *tmp = skb_tail_pointer(skb);   /* save current tail position */
    SKB_LINEAR_ASSERT(skb);              /* must be linear (no frags) */
    skb->tail += len;                    /* advance tail forward      */
    skb->len  += len;                    /* increase total length     */
    if (unlikely(skb->tail > skb->end)) /* overflow check            */
        skb_over_panic(skb, len, __builtin_return_address(0));
    return tmp;                          /* return ptr to new area    */
}
```

The `skb_over_panic` call produces a kernel oops with diagnostic information. This
is a hard failure -- there is no recovery. The caller is expected to have verified
sufficient tailroom before calling `skb_put`.

### 3.3 Before/After Diagram

**Before `skb_put(skb, len)`**:

```
head          data              tail                         end
 │              │                │                            │
 ▼              ▼                ▼                            ▼
 ┌──────────────┬────────────────┬────────────────────────────┐
 │              │                │                            │
 │   headroom   │  existing data │         tailroom           │
 │              │                │                            │
 └──────────────┴────────────────┴────────────────────────────┘

 skb->len = (old tail - data)
 tailroom = end - tail
```

**After `skb_put(skb, len)`** -- tail moves forward, data area grows:

```
head          data              old tail    new tail         end
 │              │                │            │               │
 ▼              ▼                ▼            ▼               ▼
 ┌──────────────┬────────────────┬────────────┬───────────────┐
 │              │                │  new area  │               │
 │   headroom   │  existing data │  (len      │   tailroom    │
 │              │                │   bytes)   │  (reduced)    │
 └──────────────┴────────────────┴────────────┴───────────────┘
                │◄──────── skb->len ──────────►│
                                 ▲
                                 │
                          returned pointer
                        (start of new area)
```

**Panic condition** -- if `new tail > end`:

```
head          data              tail         end
 │              │                │             │
 ▼              ▼                ▼             ▼
 ┌──────────────┬────────────────┬─────────────┐
 │   headroom   │  existing data │  tailroom   │
 └──────────────┴────────────────┴─────────────┘
                                 │◄── only X ──►│
                                      bytes

 Requested len > X bytes  ──►  skb_over_panic() ──► KERNEL BUG
```

### 3.4 Convenience Variants

**`skb_put_data(skb, data, len)`** -- put + memcpy in one call:

```c
/**
 * skb_put_data - add data and copy
 * @skb: buffer to use
 * @data: source buffer
 * @len: amount of data to add
 *
 * Extend the buffer, then copy data into the new area.
 */
static inline void *skb_put_data(struct sk_buff *skb,
                                 const void *data, unsigned int len)
{
    void *tmp = skb_put(skb, len);    /* extend the buffer          */
    memcpy(tmp, data, len);           /* copy data into new area    */
    return tmp;                        /* return ptr to copied data  */
}
```

**`skb_put_zero(skb, len)`** -- put + memset(0) in one call:

```c
/**
 * skb_put_zero - extend buffer and zero-fill
 * @skb: buffer to use
 * @len: amount of data to add
 *
 * Extend the buffer, then zero the new area.
 */
static inline void *skb_put_zero(struct sk_buff *skb, unsigned int len)
{
    void *tmp = skb_put(skb, len);    /* extend the buffer          */
    memset(tmp, 0, len);              /* zero-fill the new area     */
    return tmp;                        /* return ptr to zeroed area  */
}
```

**`skb_put_u8(skb, val)`** -- put a single byte:

```c
static inline u8 *skb_put_u8(struct sk_buff *skb, u8 val)
{
    void *tmp = skb_put(skb, 1);      /* extend by one byte         */
    *(u8 *)tmp = val;                  /* write the byte             */
    return tmp;
}
```

### 3.5 Usage Example: Adding Payload Data

```c
struct sk_buff *skb;
unsigned char *ptr;

skb = alloc_skb(MAX_TCP_HEADER + payload_len, GFP_KERNEL);
if (!skb)
    return -ENOMEM;

skb_reserve(skb, MAX_TCP_HEADER);     /* reserve header space       */

/* Add payload data using skb_put */
ptr = skb_put(skb, payload_len);      /* extend data area           */
memcpy(ptr, user_data, payload_len);  /* copy payload into buffer   */
```

Step-by-step memory state:

```
After alloc_skb:
 head/data/tail                                              end
  │                                                           │
  ▼                                                           ▼
  ┌───────────────────────────────────────────────────────────┐
  │                   empty buffer                            │
  └───────────────────────────────────────────────────────────┘

After skb_reserve(skb, MAX_TCP_HEADER):
 head                         data/tail                      end
  │                              │                            │
  ▼                              ▼                            ▼
  ┌──────────────────────────────┬────────────────────────────┐
  │    headroom (header space)   │         tailroom           │
  └──────────────────────────────┴────────────────────────────┘

After skb_put(skb, payload_len):
 head                         data          tail             end
  │                              │            │               │
  ▼                              ▼            ▼               ▼
  ┌──────────────────────────────┬────────────┬───────────────┐
  │    headroom (header space)   │  payload   │   tailroom    │
  └──────────────────────────────┴────────────┴───────────────┘
                                 │◄──────────►│
                                   skb->len
```

---

## 4. skb_push(skb, len)

### 4.1 Purpose and Semantics

`skb_push` extends the data area at the **head** of the buffer. It moves the `data`
pointer backward by `len` bytes and increments `skb->len` by the same amount. The
function returns a pointer to the new start of the data area.

This is the primary function for prepending protocol headers. Each layer of the
network stack calls `skb_push` to add its header in front of the existing data.

### 4.2 Kernel Implementation

```c
/**
 * skb_push - add data to the start of a buffer
 * @skb: buffer to use
 * @len: amount of data to add
 *
 * This function extends the used data area of the buffer at the
 * front. A pointer to the first byte of the extra data is returned.
 * If this would exceed the total buffer headroom the kernel will panic.
 */
void *skb_push(struct sk_buff *skb, unsigned int len)
{
    skb->data -= len;                    /* move data pointer backward  */
    skb->len  += len;                    /* increase total length       */
    if (unlikely(skb->data < skb->head)) /* underflow check            */
        skb_under_panic(skb, len, __builtin_return_address(0));
    return skb->data;                    /* return new data start       */
}
```

Like `skb_put`, the underflow check triggers a hard panic. The caller must ensure
sufficient headroom exists, typically by having called `skb_reserve` during
allocation.

### 4.3 Before/After Diagram

**Before `skb_push(skb, len)`**:

```
head               data                    tail              end
 │                   │                      │                 │
 ▼                   ▼                      ▼                 ▼
 ┌───────────────────┬──────────────────────┬─────────────────┐
 │                   │                      │                 │
 │     headroom      │   existing data      │    tailroom     │
 │                   │   (payload + any     │                 │
 │                   │    inner headers)    │                 │
 └───────────────────┴──────────────────────┴─────────────────┘
                     │◄──── skb->len ──────►│
```

**After `skb_push(skb, len)`** -- data moves backward:

```
head       new data  old data               tail              end
 │            │        │                      │                 │
 ▼            ▼        ▼                      ▼                 ▼
 ┌────────────┬────────┬──────────────────────┬─────────────────┐
 │            │new hdr │                      │                 │
 │  headroom  │(len    │   existing data      │    tailroom     │
 │  (reduced) │bytes)  │                      │                 │
 └────────────┴────────┴──────────────────────┴─────────────────┘
              │◄──────────── skb->len ────────►│
              ▲
              │
       returned pointer
     (new start of data)
```

**Panic condition** -- if `new data < head`:

```
head    data                                tail              end
 │        │                                  │                 │
 ▼        ▼                                  ▼                 ▼
 ┌────────┬──────────────────────────────────┬─────────────────┐
 │only X  │        existing data             │    tailroom     │
 │bytes   │                                  │                 │
 └────────┴──────────────────────────────────┴─────────────────┘
 │◄─ X ──►│

 Requested len > X bytes  ──►  skb_under_panic() ──► KERNEL BUG
```

### 4.4 Real-World Example: Building a Packet Layer by Layer

The following example demonstrates how `skb_push` is called at each protocol layer
during transmission. Note how each layer receives the `sk_buff` with the inner
layers already in place and simply prepends its own header.

```c
/* === Transport Layer (TCP) === */
static int tcp_transmit_skb(struct sock *sk, struct sk_buff *skb)
{
    struct tcphdr *th;

    /* skb already contains payload from skb_put earlier */

    /* Prepend TCP header */
    th = (struct tcphdr *)skb_push(skb, sizeof(struct tcphdr));
    skb_reset_transport_header(skb);  /* mark transport header position */

    /* Fill in TCP header fields */
    th->source = inet->inet_sport;    /* source port                    */
    th->dest   = inet->inet_dport;    /* destination port               */
    th->seq    = htonl(tcp_sk(sk)->write_seq);
    th->doff   = sizeof(struct tcphdr) / 4;
    th->syn    = 1;
    /* ... more TCP header fields ... */

    /* Pass down to IP layer */
    return ip_queue_xmit(sk, skb);
}

/* === Network Layer (IP) === */
static int ip_queue_xmit(struct sock *sk, struct sk_buff *skb)
{
    struct iphdr *iph;

    /* Prepend IP header */
    iph = (struct iphdr *)skb_push(skb, sizeof(struct iphdr));
    skb_reset_network_header(skb);    /* mark network header position   */

    /* Fill in IP header fields */
    iph->version  = 4;
    iph->ihl      = 5;
    iph->tot_len  = htons(skb->len);  /* total length including payload */
    iph->ttl      = 64;
    iph->protocol = IPPROTO_TCP;
    iph->saddr    = inet->inet_saddr;
    iph->daddr    = inet->inet_daddr;
    /* ... checksum, etc. ... */

    /* Pass down to link layer */
    return dev_queue_xmit(skb);
}

/* === Link Layer (Ethernet, in the device driver) === */
static int eth_header_create(struct sk_buff *skb, struct net_device *dev)
{
    struct ethhdr *eth;

    /* Prepend Ethernet header */
    eth = (struct ethhdr *)skb_push(skb, ETH_HLEN);

    /* Fill in Ethernet header fields */
    ether_addr_copy(eth->h_dest, dest_mac);    /* destination MAC      */
    ether_addr_copy(eth->h_source, dev->dev_addr); /* source MAC       */
    eth->h_proto = htons(ETH_P_IP);            /* EtherType = IPv4     */

    return 0;
}
```

The buffer state at each stage:

```
Step 1 — After payload added (skb_put):

 head                              data         tail         end
  │                                  │            │           │
  ▼                                  ▼            ▼           ▼
  ┌──────────────────────────────────┬────────────┬───────────┐
  │        reserved headroom         │  payload   │ tailroom  │
  └──────────────────────────────────┴────────────┴───────────┘
                                     │◄──────────►│
                                       skb->len

Step 2 — After skb_push(TCP header):

 head                     data       │            tail        end
  │                         │        │             │           │
  ▼                         ▼        ▼             ▼           ▼
  ┌─────────────────────────┬────────┬─────────────┬──────────┐
  │     reduced headroom    │  TCP   │   payload   │ tailroom │
  │                         │  hdr   │             │          │
  └─────────────────────────┴────────┴─────────────┴──────────┘
                            │◄───────────────────►│
                                    skb->len

Step 3 — After skb_push(IP header):

 head               data    │        │             tail       end
  │                   │      │        │              │          │
  ▼                   ▼      ▼        ▼              ▼          ▼
  ┌───────────────────┬──────┬────────┬──────────────┬─────────┐
  │   reduced headroom│  IP  │  TCP   │   payload    │tailroom │
  │                   │  hdr │  hdr   │              │         │
  └───────────────────┴──────┴────────┴──────────────┴─────────┘
                      │◄─────────────────────────────►│
                                   skb->len

Step 4 — After skb_push(Ethernet header):

 head         data    │      │        │              tail      end
  │             │      │      │        │               │        │
  ▼             ▼      ▼      ▼        ▼               ▼        ▼
  ┌─────────────┬──────┬──────┬────────┬───────────────┬───────┐
  │  remaining  │ ETH  │  IP  │  TCP   │   payload     │tail-  │
  │  headroom   │ hdr  │  hdr │  hdr   │               │room   │
  └─────────────┴──────┴──────┴────────┴───────────────┴───────┘
                │◄─────────────────────────────────────►│
                                 skb->len
```

---

## 5. skb_pull(skb, len)

### 5.1 Purpose and Semantics

`skb_pull` is the inverse of `skb_push`. It shrinks the data area from the front by
advancing the `data` pointer forward by `len` bytes and decrementing `skb->len` by
the same amount. The function returns a pointer to the new data start, or `NULL` if
`len` exceeds `skb->len`.

This is the primary function for stripping protocol headers during packet reception.
As the packet ascends the protocol stack, each layer calls `skb_pull` to remove its
header, leaving `data` pointing at the next layer's header.

### 5.2 Kernel Implementation

```c
/**
 * skb_pull - remove data from the start of a buffer
 * @skb: buffer to use
 * @len: amount of data to remove
 *
 * This function removes data from the start of a buffer, returning
 * the new data pointer. A pointer to the next data in the buffer
 * is returned. Once the data has been pulled, future pushes will
 * overwrite the old data.
 */
void *skb_pull(struct sk_buff *skb, unsigned int len)
{
    return skb_pull_inline(skb, len);
}

static inline void *skb_pull_inline(struct sk_buff *skb, unsigned int len)
{
    return unlikely(len > skb->len) ? NULL : __skb_pull(skb, len);
}

static inline void *__skb_pull(struct sk_buff *skb, unsigned int len)
{
    skb->len -= len;                  /* decrease total length        */
    if (unlikely(skb->len < skb->data_len))
        BUG();                        /* would eat into paged data    */
    return skb->data += len;          /* advance data pointer forward */
}
```

Unlike `skb_push` and `skb_put`, `skb_pull` does not unconditionally panic on
invalid input. If the requested length exceeds the buffer's data length, it returns
`NULL`, allowing the caller to handle the error gracefully. However, the internal
`__skb_pull` will BUG if the pull would consume into paged (non-linear) data.

### 5.3 Before/After Diagram

**Before `skb_pull(skb, len)`**:

```
head          data                              tail         end
 │              │                                │            │
 ▼              ▼                                ▼            ▼
 ┌──────────────┬────────┬───────────────────────┬────────────┐
 │              │ header │    remaining data      │            │
 │   headroom   │(len    │    (payload + inner    │  tailroom  │
 │              │ bytes) │     headers)           │            │
 └──────────────┴────────┴───────────────────────┴────────────┘
                │◄──────────── skb->len ─────────►│
```

**After `skb_pull(skb, len)`** -- data moves forward:

```
head          old data  new data                 tail         end
 │              │         │                       │            │
 ▼              ▼         ▼                       ▼            ▼
 ┌──────────────┬─────────┬───────────────────────┬────────────┐
 │              │ consumed│    remaining data      │            │
 │   headroom   │ header  │    (now starts here)   │  tailroom  │
 │  (increased) │ (now    │                        │            │
 │              │headroom)│                        │            │
 └──────────────┴─────────┴───────────────────────┴────────────┘
                          │◄──── skb->len ────────►│
                          ▲
                          │
                   returned pointer
                  (new start of data)
```

**NULL return** -- if `len > skb->len`:

```
head          data                    tail                    end
 │              │                      │                       │
 ▼              ▼                      ▼                       ▼
 ┌──────────────┬──────────────────────┬───────────────────────┐
 │   headroom   │     data (X bytes)   │       tailroom        │
 └──────────────┴──────────────────────┴───────────────────────┘
                │◄──── skb->len = X ──►│

 Requested len > X bytes  ──►  returns NULL (no panic)
```

### 5.4 Variant: pskb_pull

The `pskb_pull` function handles the case where the `sk_buff` contains non-linear
(paged) data. If the pull operation would extend into the paged portion, `pskb_pull`
first linearizes enough of the paged data to satisfy the request:

```c
/**
 * pskb_pull - pull data from a possibly non-linear buffer
 * @skb: buffer to pull from
 * @len: amount of data to pull
 *
 * Like skb_pull, but handles paged data. If len extends beyond
 * the linear portion, data is copied from pages into the linear area.
 */
void *pskb_pull(struct sk_buff *skb, unsigned int len)
{
    if (len > skb->len)
        return NULL;
    if (len <= skb_headlen(skb))         /* entirely within linear data */
        return __skb_pull(skb, len);
    if (!__pskb_pull_tail(skb, len - skb_headlen(skb)))
        return NULL;                     /* linearization failed        */
    return __skb_pull(skb, len);
}
```

### 5.5 Usage Example: Stripping an IP Header

```c
static int ip_rcv(struct sk_buff *skb, struct net_device *dev)
{
    struct iphdr *iph;
    unsigned int hdr_len;

    iph = ip_hdr(skb);                   /* get IP header pointer       */
    hdr_len = iph->ihl * 4;             /* IP header length in bytes   */

    /* Validate header length */
    if (hdr_len < sizeof(struct iphdr))
        goto drop;

    /* Strip the IP header — data now points to transport header */
    if (!pskb_pull(skb, hdr_len))
        goto drop;

    skb_reset_transport_header(skb);     /* mark transport header pos   */

    /* Hand off to transport layer (TCP, UDP, etc.) */
    return ip_local_deliver(skb);

drop:
    kfree_skb(skb);
    return NET_RX_DROP;
}
```

---

## 6. skb_trim(skb, len)

### 6.1 Purpose and Semantics

`skb_trim` sets the total data length of the `sk_buff` to exactly `len` bytes. If
the current length exceeds `len`, the tail pointer is moved backward to truncate the
data. If the current length is already less than or equal to `len`, the function is
a no-op.

This function is used to truncate packets -- for example, when a received packet
contains padding that must be removed, or when ICMP needs to quote only the first N
bytes of the original packet.

### 6.2 Kernel Implementation

```c
/**
 * skb_trim - remove end from a buffer
 * @skb: buffer to alter
 * @len: new length
 *
 * Cut the length of a buffer down by removing data from the tail.
 * If the buffer is already under the length specified it is not modified.
 * The skb must be linear.
 */
void skb_trim(struct sk_buff *skb, unsigned int len)
{
    if (skb->len > len)
        __skb_trim(skb, len);
}

static inline void __skb_trim(struct sk_buff *skb, unsigned int len)
{
    if (unlikely(skb_is_nonlinear(skb)))    /* not safe for paged data */
        BUG();
    skb->len  = len;                         /* set new length          */
    skb_set_tail_pointer(skb, len);          /* move tail to data + len */
}
```

The unchecked `__skb_trim` variant will BUG if the buffer is non-linear. For
non-linear buffers, use `pskb_trim` instead.

### 6.3 Before/After Diagram

**Before `skb_trim(skb, len)`** where `len < skb->len`:

```
head          data                                    tail   end
 │              │                                       │     │
 ▼              ▼                                       ▼     ▼
 ┌──────────────┬───────────────────────────────────────┬─────┐
 │              │                                       │     │
 │   headroom   │            packet data                │tail-│
 │              │          (skb->len bytes)              │room │
 │              │                                       │     │
 └──────────────┴───────────────────────────────────────┴─────┘
                │◄────────── skb->len (original) ──────►│
```

**After `skb_trim(skb, len)`** -- tail moves backward:

```
head          data                    new tail              end
 │              │                       │                     │
 ▼              ▼                       ▼                     ▼
 ┌──────────────┬───────────────────────┬─────────────────────┐
 │              │                       │                     │
 │   headroom   │  trimmed packet data  │     tailroom        │
 │              │  (len bytes)          │     (increased)     │
 │              │                       │                     │
 └──────────────┴───────────────────────┴─────────────────────┘
                │◄──── skb->len = len ─►│
                                        │◄── now available ──►│
```

**No-op condition** -- if `len >= skb->len`:

```
head          data              tail                         end
 │              │                │                            │
 ▼              ▼                ▼                            ▼
 ┌──────────────┬────────────────┬────────────────────────────┐
 │   headroom   │  packet data   │         tailroom           │
 └──────────────┴────────────────┴────────────────────────────┘
                │◄─ skb->len ──►│

 Requested len >= skb->len  ──►  no change (function returns)
```

### 6.4 Variant: pskb_trim

For non-linear buffers (those with paged fragments), `pskb_trim` handles the
truncation correctly by also adjusting the fragment list:

```c
/**
 * pskb_trim - trim a possibly non-linear buffer
 * @skb: buffer to trim
 * @len: new length
 *
 * Like skb_trim but handles paged data properly. Fragments beyond
 * the new length are released, and the last fragment is truncated
 * if necessary.
 */
static inline int pskb_trim(struct sk_buff *skb, unsigned int len)
{
    if (len < skb->len)
        return __pskb_trim(skb, len);  /* may fail (returns -ENOMEM)   */
    return 0;
}
```

Unlike `skb_trim`, `pskb_trim` can fail (returning `-ENOMEM`) because linearizing
paged data may require memory allocation.

### 6.5 Usage Example: Removing Ethernet Padding

Ethernet frames have a minimum length of 64 bytes (including FCS). Short packets
are padded to meet this minimum. The IP layer must trim this padding based on the
total length field in the IP header:

```c
static int ip_rcv(struct sk_buff *skb, struct net_device *dev)
{
    struct iphdr *iph = ip_hdr(skb);
    unsigned int ip_len = ntohs(iph->tot_len);

    /* The IP total length may be less than skb->len due to
     * Ethernet padding. Trim the extra bytes. */
    if (pskb_trim(skb, ip_len))
        goto drop;

    /* Now skb->len == ip_len, padding removed */
    /* ... continue processing ... */
}
```

```
Before trim (with Ethernet padding):

 data                                                tail
  │                                                    │
  ▼                                                    ▼
  ┌──────┬──────┬──────┬────────────┬──────────────────┐
  │  IP  │ TCP  │      │            │  Ethernet        │
  │  hdr │ hdr  │ data │  payload   │  padding         │
  │      │      │      │            │  (garbage)       │
  └──────┴──────┴──────┴────────────┴──────────────────┘
  │◄────────── skb->len ──────────────────────────────►│
  │◄────────── ip_len ─────────────►│

After pskb_trim(skb, ip_len):

 data                               tail
  │                                   │
  ▼                                   ▼
  ┌──────┬──────┬──────┬──────────────┐
  │  IP  │ TCP  │      │             │
  │  hdr │ hdr  │ data │  payload    │
  │      │      │      │             │
  └──────┴──────┴──────┴──────────────┘
  │◄────────── skb->len = ip_len ───►│
```

---

## 7. skb_headroom(skb) and skb_tailroom(skb)

### 7.1 Purpose and Semantics

These two functions report the available space before and after the current data
area, respectively. They are essential for checking whether sufficient room exists
before calling `skb_push` or `skb_put`.

### 7.2 Kernel Implementation

```c
/**
 * skb_headroom - bytes at buffer head
 * @skb: buffer to check
 *
 * Return the number of bytes of free space at the head of an &sk_buff.
 */
static inline unsigned int skb_headroom(const struct sk_buff *skb)
{
    return skb->data - skb->head;   /* distance from head to data      */
}

/**
 * skb_tailroom - bytes at buffer end
 * @skb: buffer to check
 *
 * Return the number of bytes of free space at the tail of an &sk_buff.
 */
static inline int skb_tailroom(const struct sk_buff *skb)
{
    return skb_is_nonlinear(skb) ? 0 : skb->end - skb->tail;
}
```

Note that `skb_tailroom` returns 0 for non-linear buffers. This is because the
linear tail region is not contiguous with the paged fragments, so appending data
there would create a gap. Non-linear buffers must be linearized first or have data
added to their fragment list.

### 7.3 Diagram: Headroom and Tailroom

```
head          data                         tail              end
 │              │                           │                 │
 ▼              ▼                           ▼                 ▼
 ┌──────────────┬───────────────────────────┬─────────────────┐
 │              │                           │                 │
 │   headroom   │       packet data         │    tailroom     │
 │              │                           │                 │
 └──────────────┴───────────────────────────┴─────────────────┘
 │◄────────────►│                           │◄───────────────►│
  skb_headroom()                             skb_tailroom()
  = data - head                              = end - tail
```

### 7.4 Usage: Checking Space Before Operations

```c
/* Before prepending a header, verify headroom */
if (skb_headroom(skb) < sizeof(struct iphdr)) {
    /* Not enough headroom — must reallocate */
    struct sk_buff *skb2;
    skb2 = skb_realloc_headroom(skb, sizeof(struct iphdr));
    if (!skb2) {
        kfree_skb(skb);
        return -ENOMEM;
    }
    consume_skb(skb);
    skb = skb2;
}

/* Now safe to push */
iph = (struct iphdr *)skb_push(skb, sizeof(struct iphdr));
```

```c
/* Before appending data, verify tailroom */
if (skb_tailroom(skb) < extra_len) {
    /* Not enough tailroom — must expand or use fragments */
    if (pskb_expand_head(skb, 0, extra_len, GFP_ATOMIC))
        return -ENOMEM;
}

/* Now safe to put */
ptr = skb_put(skb, extra_len);
```

### 7.5 Related: skb_headlen and skb_availroom

```c
/**
 * skb_headlen - length of the linear head portion
 * @skb: buffer to check
 *
 * This is the portion of data in the linear buffer (not in pages).
 */
static inline unsigned int skb_headlen(const struct sk_buff *skb)
{
    return skb->len - skb->data_len;   /* linear data length           */
}
```

Visual relationship between all size functions:

```
head          data                         tail              end
 │              │                           │                 │
 ▼              ▼                           ▼                 ▼
 ┌──────────────┬───────────────────────────┬─────────────────┐
 │              │                           │                 │
 │              │    linear data area       │                 │
 │              │                           │                 │
 └──────────────┴───────────────────────────┴─────────────────┘
 │◄────────────►│◄─────────────────────────►│◄───────────────►│
  skb_headroom    skb_headlen(skb)           skb_tailroom
                  = skb->len - data_len

 Total buffer:  │◄────────────────────────────────────────────►│
                  end - head (allocated size)

 For non-linear skbs:
   skb->len      = linear data + paged data (total)
   skb->data_len = paged data only
   skb_headlen   = linear data only = skb->len - skb->data_len
```

---

## 8. Complete Packet Construction Example

This section walks through the complete construction of a TCP/IP packet over
Ethernet, showing the exact buffer state after each operation. This is the canonical
example of the zero-copy header-prepend model.

### 8.1 Step 0: Planning the Buffer Layout

Before allocating, we must calculate the total buffer size:

```c
/* Header sizes */
#define ETH_HLEN      14    /* Ethernet header: 6 dst + 6 src + 2 type       */
#define IP_HDR_LEN    20    /* Minimum IPv4 header (no options)               */
#define TCP_HDR_LEN   20    /* Minimum TCP header (no options)                */
#define TOTAL_HDR_LEN (ETH_HLEN + IP_HDR_LEN + TCP_HDR_LEN)  /* = 54 bytes  */

unsigned int payload_len = 1400;   /* application data                       */
unsigned int alloc_size  = TOTAL_HDR_LEN + payload_len;  /* = 1454 bytes     */
```

### 8.2 Step 1: alloc_skb -- Allocate the Buffer

```c
struct sk_buff *skb;

skb = alloc_skb(alloc_size, GFP_KERNEL);
if (!skb)
    return -ENOMEM;
```

Buffer state after allocation:

```
head/data/tail                                               end
 │                                                            │
 ▼                                                            ▼
 ┌────────────────────────────────────────────────────────────┐
 │                                                            │
 │        entire buffer is unused (all tailroom)              │
 │                alloc_size bytes available                   │
 │                                                            │
 └────────────────────────────────────────────────────────────┘

 head     = data = tail   (all three at the start)
 end      = head + alloc_size + SKB_DATA_ALIGN padding
 skb->len = 0
 headroom = 0
 tailroom = alloc_size (+ alignment padding)
```

### 8.3 Step 2: skb_reserve -- Reserve Headroom for All Headers

```c
skb_reserve(skb, TOTAL_HDR_LEN);    /* 54 bytes for ETH + IP + TCP */
```

Buffer state after reserve:

```
head                                                  data/tail  end
 │                                                       │        │
 ▼                                                       ▼        ▼
 ┌───────────────────────────────────────────────────────┬────────┐
 │                                                       │        │
 │          reserved headroom (54 bytes)                 │tailroom│
 │                                                       │        │
 │  ┌──────────┬──────────────┬──────────────┐           │        │
 │  │ ETH (14) │   IP (20)    │   TCP (20)   │           │        │
 │  │  future  │   future     │   future     │           │        │
 │  └──────────┴──────────────┴──────────────┘           │        │
 │                                                       │        │
 └───────────────────────────────────────────────────────┴────────┘

 headroom = 54 bytes (TOTAL_HDR_LEN)
 tailroom = alloc_size - 54 = 1400 bytes (payload_len)
 skb->len = 0 (still empty)
```

### 8.4 Step 3: skb_put + memcpy -- Add the Payload

```c
unsigned char *payload_ptr;

payload_ptr = skb_put(skb, payload_len);       /* extend tail by 1400  */
memcpy(payload_ptr, app_data, payload_len);    /* copy application data*/
```

Buffer state after adding payload:

```
head                                          data        tail    end
 │                                              │           │      │
 ▼                                              ▼           ▼      ▼
 ┌──────────────────────────────────────────────┬───────────┬──────┐
 │                                              │           │      │
 │          reserved headroom (54 bytes)        │  PAYLOAD  │tail- │
 │                                              │ (1400 B)  │room  │
 │  ┌──────────┬──────────────┬──────────────┐  │           │      │
 │  │ ETH (14) │   IP (20)    │   TCP (20)   │  │           │      │
 │  │  empty   │   empty      │   empty      │  │           │      │
 │  └──────────┴──────────────┴──────────────┘  │           │      │
 │                                              │           │      │
 └──────────────────────────────────────────────┴───────────┴──────┘

 headroom = 54 bytes
 skb->len = 1400 bytes (payload only)
 tailroom = small (alignment padding only)
```

### 8.5 Step 4: skb_push -- Prepend TCP Header

```c
struct tcphdr *th;

th = (struct tcphdr *)skb_push(skb, TCP_HDR_LEN);  /* data -= 20      */
skb_reset_transport_header(skb);                    /* mark TCP header */

/* Fill TCP header fields */
th->source = htons(12345);            /* source port                   */
th->dest   = htons(80);               /* destination port              */
th->seq    = htonl(1000);             /* sequence number               */
th->ack_seq = htonl(0);               /* acknowledgment number         */
th->doff   = TCP_HDR_LEN / 4;         /* data offset (5 = 20 bytes)   */
th->syn    = 1;                        /* SYN flag                     */
th->window = htons(65535);             /* window size                  */
th->check  = 0;                        /* checksum (computed later)    */
th->urg_ptr = 0;                       /* urgent pointer               */
```

Buffer state after prepending TCP header:

```
head                               data                 tail    end
 │                                   │                    │      │
 ▼                                   ▼                    ▼      ▼
 ┌───────────────────────────────────┬───────┬────────────┬──────┐
 │                                   │       │            │      │
 │    remaining headroom (34 bytes)  │  TCP  │  PAYLOAD   │tail- │
 │                                   │  hdr  │ (1400 B)   │room  │
 │  ┌──────────┬──────────────┐      │(20 B) │            │      │
 │  │ ETH (14) │   IP (20)    │      │       │            │      │
 │  │  empty   │   empty      │      │       │            │      │
 │  └──────────┴──────────────┘      │       │            │      │
 │                                   │       │            │      │
 └───────────────────────────────────┴───────┴────────────┴──────┘
                                     │◄─────────────────►│
                                       skb->len = 1420

 transport_header ─────────────────► points here (= data)
```

### 8.6 Step 5: skb_push -- Prepend IP Header

```c
struct iphdr *iph;

iph = (struct iphdr *)skb_push(skb, IP_HDR_LEN);   /* data -= 20      */
skb_reset_network_header(skb);                      /* mark IP header  */

/* Fill IP header fields */
iph->version  = 4;                    /* IPv4                          */
iph->ihl      = IP_HDR_LEN / 4;       /* header length = 5 (20 bytes) */
iph->tos      = 0;                     /* type of service              */
iph->tot_len  = htons(skb->len);      /* total length = 1440          */
iph->id       = htons(1234);           /* identification               */
iph->frag_off = htons(IP_DF);          /* don't fragment               */
iph->ttl      = 64;                    /* time to live                 */
iph->protocol = IPPROTO_TCP;           /* protocol = TCP               */
iph->check    = 0;                     /* checksum (computed later)    */
iph->saddr    = htonl(0xC0A80001);     /* 192.168.0.1                  */
iph->daddr    = htonl(0xC0A80002);     /* 192.168.0.2                  */
```

Buffer state after prepending IP header:

```
head                data                                 tail    end
 │                    │                                    │      │
 ▼                    ▼                                    ▼      ▼
 ┌────────────────────┬──────┬───────┬────────────────────┬──────┐
 │                    │      │       │                    │      │
 │  remaining headroom│  IP  │  TCP  │     PAYLOAD       │tail- │
 │    (14 bytes)      │  hdr │  hdr  │    (1400 B)       │room  │
 │                    │(20 B)│(20 B) │                    │      │
 │  ┌──────────┐      │      │       │                    │      │
 │  │ ETH (14) │      │      │       │                    │      │
 │  │  empty   │      │      │       │                    │      │
 │  └──────────┘      │      │       │                    │      │
 │                    │      │       │                    │      │
 └────────────────────┴──────┴───────┴────────────────────┴──────┘
                      │◄─────────────────────────────────►│
                                  skb->len = 1440

 network_header ──────► points here (= data)
 transport_header ────► points at TCP header (data + 20)
```

### 8.7 Step 6: skb_push -- Prepend Ethernet Header

```c
struct ethhdr *eth;

eth = (struct ethhdr *)skb_push(skb, ETH_HLEN);    /* data -= 14      */

/* Fill Ethernet header fields */
memcpy(eth->h_dest, dst_mac, ETH_ALEN);    /* destination MAC address  */
memcpy(eth->h_source, src_mac, ETH_ALEN);  /* source MAC address       */
eth->h_proto = htons(ETH_P_IP);            /* EtherType = 0x0800 (IP)  */
```

Buffer state after prepending Ethernet header (packet complete):

```
head/data                                                tail    end
 │                                                         │      │
 ▼                                                         ▼      ▼
 ┌────────┬──────┬───────┬─────────────────────────────────┬──────┐
 │        │      │       │                                 │      │
 │  ETH   │  IP  │  TCP  │          PAYLOAD                │tail- │
 │  hdr   │  hdr │  hdr  │         (1400 B)                │room  │
 │ (14 B) │(20 B)│(20 B) │                                 │      │
 │        │      │       │                                 │      │
 └────────┴──────┴───────┴─────────────────────────────────┴──────┘
 │◄────────────────────────────────────────────────────────►│
                        skb->len = 1454

 headroom = 0 (fully consumed)
 data ─────────────────────► ETH header start
 network_header ───────────► IP header start (data + 14)
 transport_header ─────────► TCP header start (data + 34)
```

### 8.8 Complete Code Summary

```c
#include <linux/skbuff.h>
#include <linux/ip.h>
#include <linux/tcp.h>
#include <linux/if_ether.h>

int build_tcp_packet(const unsigned char *app_data, unsigned int payload_len,
                     const unsigned char *src_mac, const unsigned char *dst_mac,
                     __be32 saddr, __be32 daddr,
                     __be16 sport, __be16 dport)
{
    struct sk_buff *skb;
    struct ethhdr  *eth;
    struct iphdr   *iph;
    struct tcphdr  *th;
    unsigned char  *payload_ptr;

    unsigned int total_hdr = ETH_HLEN + sizeof(struct iphdr)
                           + sizeof(struct tcphdr);

    /* Step 1: Allocate */
    skb = alloc_skb(total_hdr + payload_len, GFP_KERNEL);
    if (!skb)
        return -ENOMEM;

    /* Step 2: Reserve headroom for all headers */
    skb_reserve(skb, total_hdr);

    /* Step 3: Add payload */
    payload_ptr = skb_put(skb, payload_len);
    memcpy(payload_ptr, app_data, payload_len);

    /* Step 4: Prepend TCP header */
    th = (struct tcphdr *)skb_push(skb, sizeof(struct tcphdr));
    skb_reset_transport_header(skb);
    memset(th, 0, sizeof(struct tcphdr));
    th->source = sport;
    th->dest   = dport;
    th->seq    = htonl(1000);
    th->doff   = sizeof(struct tcphdr) / 4;
    th->syn    = 1;
    th->window = htons(65535);

    /* Step 5: Prepend IP header */
    iph = (struct iphdr *)skb_push(skb, sizeof(struct iphdr));
    skb_reset_network_header(skb);
    iph->version  = 4;
    iph->ihl      = 5;
    iph->tos      = 0;
    iph->tot_len  = htons(skb->len);
    iph->id       = 0;
    iph->frag_off = htons(IP_DF);
    iph->ttl      = 64;
    iph->protocol = IPPROTO_TCP;
    iph->saddr    = saddr;
    iph->daddr    = daddr;
    iph->check    = 0;
    iph->check    = ip_fast_csum((unsigned char *)iph, iph->ihl);

    /* Step 6: Prepend Ethernet header */
    eth = (struct ethhdr *)skb_push(skb, ETH_HLEN);
    memcpy(eth->h_dest, dst_mac, ETH_ALEN);
    memcpy(eth->h_source, src_mac, ETH_ALEN);
    eth->h_proto = htons(ETH_P_IP);

    /* Packet is now complete — ready to transmit */
    return dev_queue_xmit(skb);
}
```

---

## 9. Complete Packet Receive Processing Example

This section traces the receive path -- the mirror image of Section 8. A packet
arrives from the NIC, and each protocol layer strips its header by calling
`skb_pull`.

### 9.1 Step 0: Frame Arrives from NIC

The network driver receives a complete Ethernet frame from the hardware. The DMA
engine places the raw bytes into a pre-allocated `sk_buff`, with `data` pointing to
the very beginning of the frame (the Ethernet header).

```c
/* In the NIC driver's receive interrupt handler / NAPI poll */
struct sk_buff *skb;
unsigned int frame_len = 1454;   /* total bytes received from NIC */

skb = netdev_alloc_skb(dev, frame_len + NET_IP_ALIGN);
if (!skb)
    return;

skb_reserve(skb, NET_IP_ALIGN);                  /* 2-byte alignment  */

/* DMA or PIO copy from NIC into skb */
unsigned char *buf = skb_put(skb, frame_len);     /* extend data area  */
memcpy(buf, hw_rx_buffer, frame_len);             /* copy frame data   */

/* Set up the skb metadata */
skb->protocol = eth_type_trans(skb, dev);         /* determine protocol*/
```

Buffer state when frame is first received:

```
head  data                                               tail    end
 │      │                                                  │      │
 ▼      ▼                                                  ▼      ▼
 ┌──────┬────────┬──────┬───────┬──────────────────────────┬──────┐
 │align │        │      │       │                          │      │
 │(2 B) │  ETH   │  IP  │  TCP  │        PAYLOAD           │tail- │
 │      │  hdr   │  hdr │  hdr  │       (1400 B)           │room  │
 │      │ (14 B) │(20 B)│(20 B) │                          │      │
 │      │        │      │       │                          │      │
 └──────┴────────┴──────┴───────┴──────────────────────────┴──────┘
        │◄─────────────────────────────────────────────────►│
                           skb->len = 1454

 data ──► Ethernet header
```

### 9.2 Step 1: eth_type_trans -- Process and Strip Ethernet Header

`eth_type_trans` is notable because it both determines the protocol type and
implicitly strips the Ethernet header by calling `skb_pull`:

```c
/**
 * eth_type_trans - determine the packet's protocol ID
 * @skb: received socket data
 * @dev: receiving network device
 *
 * This pulls the Ethernet header and sets skb->pkt_type
 * and returns the protocol (EtherType).
 */
__be16 eth_type_trans(struct sk_buff *skb, struct net_device *dev)
{
    unsigned short _service_access_point;
    const struct ethhdr *eth;

    skb->dev = dev;
    skb_reset_mac_header(skb);        /* mac_header = current data     */

    /* Strip Ethernet header */
    skb_pull_inline(skb, ETH_HLEN);   /* data += 14, len -= 14        */

    eth = (const struct ethhdr *)skb_mac_header(skb);

    /* Determine packet type from destination MAC */
    if (unlikely(!ether_addr_equal_64bits(eth->h_dest, dev->dev_addr))) {
        if (ether_addr_equal_64bits(eth->h_dest, dev->broadcast))
            skb->pkt_type = PACKET_BROADCAST;
        else
            skb->pkt_type = PACKET_OTHERHOST;
    }

    return eth->h_proto;              /* return EtherType              */
}
```

Buffer state after stripping Ethernet header:

```
head       mac_hdr  data                                 tail    end
 │            │       │                                    │      │
 ▼            ▼       ▼                                    ▼      ▼
 ┌────────────┬───────┬──────┬───────┬─────────────────────┬──────┐
 │  alignment │       │      │       │                     │      │
 │  + now     │  ETH  │  IP  │  TCP  │      PAYLOAD        │tail- │
 │  headroom  │  hdr  │  hdr │  hdr  │     (1400 B)        │room  │
 │            │(14 B) │(20 B)│(20 B) │                     │      │
 │            │ (now  │      │       │                     │      │
 │            │ head- │      │       │                     │      │
 │            │ room) │      │       │                     │      │
 └────────────┴───────┴──────┴───────┴─────────────────────┴──────┘
              ▲       │◄─────────────────────────────────►│
           mac_header              skb->len = 1440

 data ──► IP header (Ethernet header consumed)
 mac_header ──► still points to Ethernet header for reference
```

### 9.3 Step 2: ip_rcv -- Process and Strip IP Header

```c
static int ip_rcv(struct sk_buff *skb, struct net_device *dev,
                  struct packet_type *pt, struct net_device *orig_dev)
{
    struct iphdr *iph;
    unsigned int hdr_len;
    unsigned int ip_len;

    /* Ensure we can read the IP header */
    if (!pskb_may_pull(skb, sizeof(struct iphdr)))
        goto drop;

    iph = ip_hdr(skb);                   /* get pointer to IP header    */
    hdr_len = iph->ihl * 4;             /* header length with options  */
    ip_len  = ntohs(iph->tot_len);      /* total IP datagram length    */

    /* Trim Ethernet padding if present */
    if (pskb_trim(skb, ip_len))
        goto drop;

    /* Set transport header offset */
    skb_set_transport_header(skb, hdr_len);

    /* Strip IP header */
    skb_pull(skb, hdr_len);              /* data += 20, len -= 20       */

    /* Route and deliver to transport layer */
    return ip_local_deliver(skb);
}
```

Buffer state after stripping IP header:

```
head       mac_hdr  net_hdr  data                        tail    end
 │            │       │        │                           │      │
 ▼            ▼       ▼        ▼                           ▼      ▼
 ┌────────────┬───────┬────────┬───────┬───────────────────┬──────┐
 │            │       │        │       │                   │      │
 │  headroom  │  ETH  │   IP   │  TCP  │     PAYLOAD       │tail- │
 │            │  hdr  │   hdr  │  hdr  │    (1400 B)       │room  │
 │            │(14 B) │ (20 B) │(20 B) │                   │      │
 │            │       │  (now  │       │                   │      │
 │            │       │  head- │       │                   │      │
 │            │       │  room) │       │                   │      │
 └────────────┴───────┴────────┴───────┴───────────────────┴──────┘
                               ▲       │◄─────────────────►│
                           net_header    skb->len = 1420

 data ──► TCP header (IP header consumed)
 mac_header ──► Ethernet header (for reference)
 network_header ──► IP header (for reference)
 transport_header ──► TCP header (= data, set before pull)
```

### 9.4 Step 3: tcp_v4_rcv -- Process and Strip TCP Header

```c
int tcp_v4_rcv(struct sk_buff *skb)
{
    struct tcphdr *th;
    unsigned int tcp_hdr_len;

    /* Ensure we can read the minimum TCP header */
    if (!pskb_may_pull(skb, sizeof(struct tcphdr)))
        goto drop;

    th = (struct tcphdr *)skb->data;     /* TCP header at current data  */
    tcp_hdr_len = th->doff * 4;          /* TCP header length           */

    /* Validate header length */
    if (tcp_hdr_len < sizeof(struct tcphdr))
        goto drop;

    /* Ensure full TCP header (with options) is in linear data */
    if (!pskb_may_pull(skb, tcp_hdr_len))
        goto drop;

    /* Mark transport header position */
    skb_reset_transport_header(skb);

    /* Strip TCP header — data now points to application payload */
    __skb_pull(skb, tcp_hdr_len);        /* data += 20, len -= 20       */

    /* Deliver payload to socket receive queue */
    return tcp_queue_rcv(sk, skb);
}
```

Buffer state after stripping TCP header (payload exposed):

```
head       mac_hdr  net_hdr  tp_hdr   data               tail    end
 │            │       │        │        │                   │      │
 ▼            ▼       ▼        ▼        ▼                   ▼      ▼
 ┌────────────┬───────┬────────┬────────┬───────────────────┬──────┐
 │            │       │        │        │                   │      │
 │  headroom  │  ETH  │   IP   │  TCP   │    PAYLOAD        │tail- │
 │            │  hdr  │   hdr  │  hdr   │   (1400 B)        │room  │
 │            │(14 B) │ (20 B) │ (20 B) │                   │      │
 │            │       │        │  (now  │                   │      │
 │            │       │        │  head- │                   │      │
 │            │       │        │  room) │                   │      │
 └────────────┴───────┴────────┴────────┴───────────────────┴──────┘
                                        │◄─────────────────►│
                                          skb->len = 1400

 data ──► APPLICATION PAYLOAD (all headers consumed)
 mac_header ──► Ethernet header
 network_header ──► IP header
 transport_header ──► TCP header
```

### 9.5 Summary: The Receive Path at a Glance

```
┌─────────────────────────────────────────────────────────────────────┐
│                      RECEIVE PATH SUMMARY                          │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  NIC driver:  data ──► ┌ ETH ┬ IP ┬ TCP ┬ PAYLOAD ┐  len = 1454   │
│                        └─────┴────┴─────┴─────────┘               │
│                                                                     │
│  After eth_type_trans (skb_pull ETH_HLEN = 14):                    │
│               data ──► ┌ IP ┬ TCP ┬ PAYLOAD ┐         len = 1440   │
│                        └────┴─────┴─────────┘                      │
│                                                                     │
│  After ip_rcv (skb_pull ip_hdr_len = 20):                          │
│               data ──► ┌ TCP ┬ PAYLOAD ┐              len = 1420   │
│                        └─────┴─────────┘                           │
│                                                                     │
│  After tcp_v4_rcv (skb_pull tcp_hdr_len = 20):                     │
│               data ──► ┌ PAYLOAD ┐                    len = 1400   │
│                        └─────────┘                                 │
│                                                                     │
│  All headers stripped — payload delivered to socket.                 │
│  Each header is still accessible via mac_header, network_header,   │
│  and transport_header offsets.                                      │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 10. Header Pointer Setting Functions

### 10.1 Overview

In addition to the four fundamental pointers (`head`, `data`, `tail`, `end`), each
`sk_buff` maintains three protocol header offsets:

```c
struct sk_buff {
    /* ... */
    __u16  mac_header;        /* offset from head to MAC header        */
    __u16  network_header;    /* offset from head to network header    */
    __u16  transport_header;  /* offset from head to transport header  */
    /* ... */
};
```

These are stored as offsets (not pointers) from `skb->head`. This design saves
memory on 64-bit systems (16-bit offset vs. 64-bit pointer) and simplifies buffer
cloning since offsets remain valid even when the `sk_buff` metadata is copied without
duplicating the underlying data buffer.

### 10.2 skb_reset_mac_header

```c
/**
 * skb_reset_mac_header - set mac_header to current data position
 * @skb: buffer to modify
 *
 * Sets the MAC header to point to the current data position.
 * Called when the data pointer is at the start of the link-layer header.
 */
static inline void skb_reset_mac_header(struct sk_buff *skb)
{
    skb->mac_header = skb->data - skb->head;   /* offset from head    */
}
```

Diagram showing `skb_reset_mac_header` usage:

```
Before (data points to Ethernet header):

head                 data                                    tail
 │                     │                                      │
 ▼                     ▼                                      ▼
 ┌─────────────────────┬──────┬──────┬───────┬────────────────┐
 │     headroom        │ ETH  │  IP  │  TCP  │   PAYLOAD      │
 └─────────────────────┴──────┴──────┴───────┴────────────────┘

After skb_reset_mac_header(skb):

head                 data                                    tail
 │                     │                                      │
 ▼                     ▼                                      ▼
 ┌─────────────────────┬──────┬──────┬───────┬────────────────┐
 │     headroom        │ ETH  │  IP  │  TCP  │   PAYLOAD      │
 └─────────────────────┴──────┴──────┴───────┴────────────────┘
                       ▲
                       │
                  mac_header = data - head
                  (offset stored in skb->mac_header)
```

### 10.3 skb_set_network_header

```c
/**
 * skb_set_network_header - set network_header offset
 * @skb: buffer to modify
 * @offset: offset from current data pointer
 *
 * Sets the network header to skb->data + offset.
 */
static inline void skb_set_network_header(struct sk_buff *skb, int offset)
{
    skb->network_header = (skb->data + offset) - skb->head;
}

/**
 * skb_reset_network_header - set network_header to current data position
 * @skb: buffer to modify
 */
static inline void skb_reset_network_header(struct sk_buff *skb)
{
    skb->network_header = skb->data - skb->head;
}
```

The `skb_set_network_header(skb, offset)` variant is used when `data` points to the
MAC header and the IP header is known to be at `offset` bytes from `data`:

```
data                                                         tail
 │                                                            │
 ▼                                                            ▼
 ┌──────────────┬───────────────┬──────────┬──────────────────┐
 │  ETH header  │   IP header   │ TCP hdr  │    PAYLOAD       │
 │   (14 B)     │   (20 B)      │  (20 B)  │                  │
 └──────────────┴───────────────┴──────────┴──────────────────┘
 │◄── offset ──►│
      = 14       ▲
                 │
   skb_set_network_header(skb, ETH_HLEN)
   network_header = (data + 14) - head
```

The `skb_reset_network_header(skb)` variant is used after `skb_pull` has already
advanced `data` past the MAC header, so `data` now points directly at the IP header:

```
                data                                         tail
                 │                                            │
                 ▼                                            ▼
 ┌──────────────┬───────────────┬──────────┬──────────────────┐
 │  ETH header  │   IP header   │ TCP hdr  │    PAYLOAD       │
 │  (headroom)  │   (20 B)      │  (20 B)  │                  │
 └──────────────┴───────────────┴──────────┴──────────────────┘
                 ▲
                 │
   skb_reset_network_header(skb)
   network_header = data - head
```

### 10.4 skb_set_transport_header

```c
/**
 * skb_set_transport_header - set transport_header offset
 * @skb: buffer to modify
 * @offset: offset from current data pointer
 */
static inline void skb_set_transport_header(struct sk_buff *skb, int offset)
{
    skb->transport_header = (skb->data + offset) - skb->head;
}

/**
 * skb_reset_transport_header - set transport_header to current data
 * @skb: buffer to modify
 */
static inline void skb_reset_transport_header(struct sk_buff *skb)
{
    skb->transport_header = skb->data - skb->head;
}
```

Usage during IP receive processing -- the transport header is at a known offset from
`data` (which currently points at the IP header):

```
data                                                         tail
 │                                                            │
 ▼                                                            ▼
 ┌────────────────────┬──────────────┬────────────────────────┐
 │    IP header       │  TCP header  │       PAYLOAD          │
 │    (ihl * 4 B)     │   (20+ B)    │                        │
 └────────────────────┴──────────────┴────────────────────────┘
 │◄── ihl * 4 ───────►│
                       ▲
                       │
   skb_set_transport_header(skb, iph->ihl * 4)
   transport_header = (data + ihl*4) - head
```

### 10.5 Accessor Functions

Once the header offsets are set, protocol handlers retrieve header pointers using
these accessors:

```c
/* Get pointer to MAC header */
static inline unsigned char *skb_mac_header(const struct sk_buff *skb)
{
    return skb->head + skb->mac_header;
}

/* Get pointer to network (IP) header */
static inline unsigned char *skb_network_header(const struct sk_buff *skb)
{
    return skb->head + skb->network_header;
}

/* Get pointer to transport (TCP/UDP) header */
static inline unsigned char *skb_transport_header(const struct sk_buff *skb)
{
    return skb->head + skb->transport_header;
}

/* Convenience: cast to specific header types */
static inline struct iphdr *ip_hdr(const struct sk_buff *skb)
{
    return (struct iphdr *)skb_network_header(skb);
}

static inline struct tcphdr *tcp_hdr(const struct sk_buff *skb)
{
    return (struct tcphdr *)skb_transport_header(skb);
}

static inline struct ethhdr *eth_hdr(const struct sk_buff *skb)
{
    return (struct ethhdr *)skb_mac_header(skb);
}
```

### 10.6 Complete Header Offset Diagram

After full receive processing, the header offsets allow any layer to reference any
header, even after `data` has been advanced past them:

```
head      mac_hdr     net_hdr     tp_hdr     data            tail
 │          │           │           │          │               │
 ▼          ▼           ▼           ▼          ▼               ▼
 ┌──────────┬───────────┬───────────┬──────────┬───────────────┐
 │          │           │           │          │               │
 │ headroom │   ETH     │    IP     │   TCP    │   PAYLOAD     │
 │ (align)  │   hdr     │    hdr    │   hdr    │               │
 │          │  (14 B)   │  (20 B)   │  (20 B)  │  (1400 B)     │
 │          │           │           │          │               │
 └──────────┴───────────┴───────────┴──────────┴───────────────┘
            │           │           │          │               │
            │           │           │          │               │
   skb->mac_header      │           │     skb->data            │
   = mac_hdr - head     │           │     (current data start) │
                        │           │                          │
          skb->network_header       │                   skb->tail
          = net_hdr - head          │
                                    │
                  skb->transport_header
                  = tp_hdr - head

 Any layer can still access any header:
   eth_hdr(skb)  ──► Ethernet header (via mac_header offset)
   ip_hdr(skb)   ──► IP header (via network_header offset)
   tcp_hdr(skb)  ──► TCP header (via transport_header offset)
```

This is a critical design feature: even after `skb_pull` has moved `data` past a
header, the header remains in the buffer and is accessible through its stored offset.
The data is never overwritten; only the `data` pointer moves forward.

---

## 11. Safety Checks and Error Handling

### 11.1 Overflow and Underflow Panics

The kernel takes a deliberately harsh stance on buffer overflows and underflows in
`sk_buff` operations. Rather than silently corrupting memory, the kernel panics with
diagnostic information:

```c
/**
 * skb_over_panic - called when skb_put would overflow
 * @skb: buffer
 * @sz: requested put size
 * @addr: caller address (for traceback)
 *
 * Called when skb_put(skb, len) would push tail past end.
 * This is a fatal error — the kernel will panic.
 */
static void skb_over_panic(struct sk_buff *skb, unsigned int sz, void *addr)
{
    pr_emerg("skb_over_panic: text:%px len:%d put:%d head:%px data:%px "
             "tail:%#lx end:%#lx dev:%s\n",
             addr, skb->len, sz,
             skb->head, skb->data,
             (unsigned long)skb->tail, (unsigned long)skb->end,
             skb->dev ? skb->dev->name : "<NULL>");
    BUG();
}

/**
 * skb_under_panic - called when skb_push would underflow
 * @skb: buffer
 * @sz: requested push size
 * @addr: caller address
 *
 * Called when skb_push(skb, len) would push data before head.
 * This is a fatal error — the kernel will panic.
 */
static void skb_under_panic(struct sk_buff *skb, unsigned int sz, void *addr)
{
    pr_emerg("skb_under_panic: text:%px len:%d put:%d head:%px data:%px "
             "tail:%#lx end:%#lx dev:%s\n",
             addr, skb->len, sz,
             skb->head, skb->data,
             (unsigned long)skb->tail, (unsigned long)skb->end,
             skb->dev ? skb->dev->name : "<NULL>");
    BUG();
}
```

These panic functions dump the full state of the `sk_buff` pointers, making it
possible to diagnose the root cause from crash logs:

```
┌─────────────────────────────────────────────────────────────────┐
│                    skb_over_panic output                        │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  text:  ffffffff812abcde   ◄── address of caller               │
│  len:   1400               ◄── current skb->len                 │
│  put:   200                ◄── requested put size               │
│  head:  ffff888012340000   ◄── head pointer                     │
│  data:  ffff888012340036   ◄── data pointer                     │
│  tail:  0x5b2              ◄── tail offset                      │
│  end:   0x600              ◄── end offset                       │
│  dev:   eth0               ◄── network device                   │
│                                                                 │
│  Problem: tail (0x5b2) + put (200=0xc8) = 0x67a > end (0x600) │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 11.2 Debug vs. Production Builds

The level of checking varies between debug and production kernel configurations:

```
┌─────────────────────────────────────────────────────────────────┐
│                 Build Configuration Comparison                  │
├────────────────────────┬────────────────────────────────────────┤
│ CONFIG_DEBUG_NET=n     │ CONFIG_DEBUG_NET=y                     │
│ (Production)           │ (Debug)                                │
├────────────────────────┼────────────────────────────────────────┤
│                        │                                        │
│ skb_put:               │ skb_put:                               │
│  - tail > end check    │  - tail > end check                    │
│    (BUG_ON)            │  - SKB_LINEAR_ASSERT                   │
│                        │  - warn if data_len != 0               │
│                        │  - stack trace on failure              │
│                        │                                        │
│ skb_push:              │ skb_push:                              │
│  - data < head check   │  - data < head check                   │
│    (BUG_ON)            │  - warn if push into cloned data       │
│                        │  - stack trace on failure              │
│                        │                                        │
│ skb_pull:              │ skb_pull:                              │
│  - len > skb->len      │  - len > skb->len check               │
│    returns NULL        │  - warn if pull past linear data       │
│                        │  - KASAN checks for buffer access      │
│                        │                                        │
│ skb_reserve:           │ skb_reserve:                           │
│  - no checks           │  - WARN_ON if skb has data             │
│                        │  - WARN_ON if reserve > buffer size    │
│                        │                                        │
└────────────────────────┴────────────────────────────────────────┘
```

### 11.3 skb_cow_head -- Ensure Writable Headroom

When an `sk_buff` is shared (its data buffer has a reference count > 1, as happens
after `skb_clone`), the headroom cannot be written directly because other `sk_buff`
structures reference the same data. The `skb_cow_head` function ensures the headroom
is both sufficient and writable:

```c
/**
 * skb_cow_head - ensure headroom is writable and sufficient
 * @skb: buffer to check
 * @headroom: needed headroom
 *
 * If the headroom is insufficient or the buffer is shared,
 * reallocate. Returns 0 on success, -ENOMEM on failure.
 */
static inline int skb_cow_head(struct sk_buff *skb, unsigned int headroom)
{
    return __skb_cow(skb, headroom, skb_header_cloned(skb));
}

static inline int __skb_cow(struct sk_buff *skb, unsigned int headroom,
                            int cloned)
{
    int delta = headroom - skb_headroom(skb);

    if (delta < 0)
        delta = 0;

    if (delta || cloned)
        return pskb_expand_head(skb, ALIGN(delta, NET_SKB_PAD),
                                0, GFP_ATOMIC);
    return 0;
}
```

**Before `skb_cow_head`** -- shared buffer with insufficient headroom:

```
sk_buff A ──┐
            │     ┌──────────┬────────────────────────┬──────┐
            ├───► │ headroom │      packet data        │tail- │
            │     │ (small)  │                         │room  │
sk_buff B ──┘     └──────────┴────────────────────────┴──────┘
                  refcount = 2 (shared)

 Problem: skb_push would modify shared data — not safe!
 Problem: headroom may be too small for the needed header.
```

**After `skb_cow_head(skb_A, needed_headroom)`** -- A gets its own copy:

```
sk_buff A ──────► ┌──────────────────┬────────────────────────┬──────┐
                  │    headroom      │      packet data        │tail- │
                  │  (>= needed)     │     (private copy)      │room  │
                  └──────────────────┴────────────────────────┴──────┘
                  refcount = 1 (private)

sk_buff B ──────► ┌──────────┬────────────────────────┬──────┐
                  │ headroom │      packet data        │tail- │
                  │ (orig)   │     (original)          │room  │
                  └──────────┴────────────────────────┴──────┘
                  refcount = 1 (private)

 Now safe: skb_push on A won't affect B.
```

### 11.4 pskb_may_pull -- Ensure Linear Data Availability

Before accessing data in the linear portion of the buffer, protocol handlers must
ensure enough bytes have been pulled into the linear area from paged fragments:

```c
/**
 * pskb_may_pull - ensure len bytes are in the linear buffer
 * @skb: buffer to check
 * @len: number of bytes needed
 *
 * Ensure that the first @len bytes of @skb are in the linear data area.
 * If not, attempt to pull data from pages into the linear area.
 * Returns true on success, false if unable to linearize.
 */
static inline int pskb_may_pull(struct sk_buff *skb, unsigned int len)
{
    if (likely(len <= skb_headlen(skb)))   /* already in linear area    */
        return 1;
    if (unlikely(len > skb->len))          /* not enough data at all    */
        return 0;
    return __pskb_pull_tail(skb, len - skb_headlen(skb)) != NULL;
}
```

```
Before pskb_may_pull (data partially in pages):

 ┌──────────────────────────────────────────────────┐
 │              LINEAR BUFFER                       │
 │  head    data          tail                 end  │
 │   │        │             │                   │   │
 │   ▼        ▼             ▼                   ▼   │
 │   ┌────────┬─────────────┬───────────────────┐   │
 │   │headroom│  partial    │     tailroom      │   │
 │   │        │  data (10B) │                   │   │
 │   └────────┴─────────────┴───────────────────┘   │
 └──────────────────────────────────────────────────┘
                │
                ├── need 40 bytes but only 10 in linear area
                │
 ┌──────────────────────────────────────────────────┐
 │              PAGED FRAGMENTS                     │
 │  frag[0]: page + offset, len = 30               │
 │  frag[1]: page + offset, len = 1370             │
 └──────────────────────────────────────────────────┘

After pskb_may_pull(skb, 40):

 ┌──────────────────────────────────────────────────┐
 │              LINEAR BUFFER                       │
 │  head    data                       tail    end  │
 │   │        │                          │      │   │
 │   ▼        ▼                          ▼      ▼   │
 │   ┌────────┬──────────────────────────┬──────┐   │
 │   │headroom│  linearized data (40B)   │tail- │   │
 │   │        │  (copied from pages)     │room  │   │
 │   └────────┴──────────────────────────┴──────┘   │
 └──────────────────────────────────────────────────┘
                │
                ├── now 40 bytes available in linear area
                │
 ┌──────────────────────────────────────────────────┐
 │              PAGED FRAGMENTS (adjusted)          │
 │  frag[0]: (consumed, removed)                    │
 │  frag[1]: page + offset, len = 1370             │
 └──────────────────────────────────────────────────┘
```

### 11.5 skb_realloc_headroom -- Allocate New Buffer with More Headroom

When headroom is insufficient and the buffer cannot be expanded in place,
`skb_realloc_headroom` creates a new `sk_buff` with the requested headroom:

```c
/**
 * skb_realloc_headroom - reallocate header of &sk_buff
 * @skb: buffer to reallocate
 * @headroom: needed headroom
 *
 * Allocate a new &sk_buff with @headroom bytes of headroom,
 * copy the data from @skb. The original @skb is NOT freed.
 * Returns NULL on failure.
 */
struct sk_buff *skb_realloc_headroom(struct sk_buff *skb,
                                     unsigned int headroom)
{
    struct sk_buff *skb2;

    skb2 = skb_clone(skb, GFP_ATOMIC);
    if (!skb2)
        return NULL;

    if (pskb_expand_head(skb2, headroom, 0, GFP_ATOMIC)) {
        kfree_skb(skb2);
        return NULL;
    }

    return skb2;
}
```

**Before** -- insufficient headroom:

```
head     data                                    tail        end
 │         │                                      │           │
 ▼         ▼                                      ▼           ▼
 ┌─────────┬──────────────────────────────────────┬───────────┐
 │ 10 bytes│          packet data                 │ tailroom  │
 │headroom │                                      │           │
 └─────────┴──────────────────────────────────────┴───────────┘

 Need 64 bytes of headroom, but only have 10.
```

**After `skb_realloc_headroom(skb, 64)`** -- new skb with expanded headroom:

```
Original skb (unchanged, caller must free separately):

 head     data                                    tail        end
  │         │                                      │           │
  ▼         ▼                                      ▼           ▼
  ┌─────────┬──────────────────────────────────────┬───────────┐
  │ 10 B    │          packet data                 │ tailroom  │
  └─────────┴──────────────────────────────────────┴───────────┘

New skb (returned):

 head                         data                            tail  end
  │                              │                              │    │
  ▼                              ▼                              ▼    ▼
  ┌──────────────────────────────┬──────────────────────────────┬────┐
  │         64 bytes             │      packet data             │tail│
  │         headroom             │      (copied)                │room│
  └──────────────────────────────┴──────────────────────────────┴────┘
```

### 11.6 Defensive Programming Patterns

Well-written kernel network code follows these defensive patterns:

```c
/* Pattern 1: Always check headroom before push */
static int prepend_header(struct sk_buff *skb, unsigned int hdr_len)
{
    /* Ensure sufficient writable headroom */
    if (skb_cow_head(skb, hdr_len) < 0) {
        kfree_skb(skb);
        return -ENOMEM;
    }

    /* Safe to push — headroom is guaranteed sufficient and writable */
    void *hdr = skb_push(skb, hdr_len);
    /* ... fill header ... */
    return 0;
}

/* Pattern 2: Always validate before pull */
static int strip_header(struct sk_buff *skb, unsigned int hdr_len)
{
    /* Ensure enough linear data to read the header */
    if (!pskb_may_pull(skb, hdr_len)) {
        kfree_skb(skb);
        return -EINVAL;
    }

    /* Safe to access header fields and pull */
    struct myhdr *hdr = (struct myhdr *)skb->data;
    /* ... read header fields ... */

    skb_pull(skb, hdr_len);
    return 0;
}

/* Pattern 3: Always check tailroom before put */
static int append_data(struct sk_buff *skb, const void *data,
                       unsigned int len)
{
    /* Ensure sufficient tailroom */
    if (skb_tailroom(skb) < len) {
        if (pskb_expand_head(skb, 0, len - skb_tailroom(skb),
                             GFP_ATOMIC)) {
            kfree_skb(skb);
            return -ENOMEM;
        }
    }

    /* Safe to put */
    skb_put_data(skb, data, len);
    return 0;
}
```

### 11.7 Summary of Safety Functions

```
┌────────────────────────────┬───────────────────────────────────────┐
│ Function                   │ Purpose                               │
├────────────────────────────┼───────────────────────────────────────┤
│ skb_headroom(skb)          │ Check available headroom (bytes)      │
│ skb_tailroom(skb)          │ Check available tailroom (bytes)      │
│ skb_headlen(skb)           │ Check linear data length (bytes)      │
│ pskb_may_pull(skb, len)    │ Ensure len bytes in linear area       │
│ skb_cow_head(skb, hr)      │ Ensure writable headroom >= hr        │
│ skb_realloc_headroom(s,hr) │ Allocate new skb with headroom >= hr  │
│ pskb_expand_head(s,h,t,g)  │ Expand head and/or tail room          │
│ skb_over_panic(skb,sz,a)   │ Fatal: skb_put overflow (BUG)         │
│ skb_under_panic(skb,sz,a)  │ Fatal: skb_push underflow (BUG)       │
│ skb_linearize(skb)         │ Pull all paged data into linear area  │
└────────────────────────────┴───────────────────────────────────────┘
```

---

## 12. Quick Reference: Operation Summary

The following table summarizes all data manipulation operations covered in this
chapter, their pointer effects, and their typical use cases:

```
┌───────────────────┬────────────┬────────────┬───────────────────────────────┐
│ Operation         │ data ptr   │ tail ptr   │ Typical Use                   │
├───────────────────┼────────────┼────────────┼───────────────────────────────┤
│ skb_reserve(len)  │ += len     │ += len     │ Reserve headroom at alloc     │
│ skb_put(len)      │ unchanged  │ += len     │ Append data / add payload     │
│ skb_push(len)     │ -= len     │ unchanged  │ Prepend header (TX path)      │
│ skb_pull(len)     │ += len     │ unchanged  │ Strip header (RX path)        │
│ skb_trim(len)     │ unchanged  │ = data+len │ Truncate data to len bytes    │
├───────────────────┼────────────┼────────────┼───────────────────────────────┤
│ skb_headroom()    │ returns data - head     │ Check space for push          │
│ skb_tailroom()    │ returns end - tail      │ Check space for put           │
│ skb_headlen()     │ returns tail - data     │ Linear data length            │
└───────────────────┴───────────────────────────────────────────────────────────┘
```

Visual summary of all five fundamental operations on a single buffer:

```
              skb_reserve(R)
              ════════════►
              (data & tail move right by R)

 head         data                              tail          end
  │             │                                │             │
  ▼             ▼                                ▼             ▼
  ┌─────────────┬────────────────────────────────┬─────────────┐
  │  headroom   │         packet data            │  tailroom   │
  └─────────────┴────────────────────────────────┴─────────────┘
       ◄════════                                  ════════►
       skb_push(P)                                skb_put(U)
       (data moves left by P)                    (tail moves right by U)

       ════════►                   ◄════════════
       skb_pull(L)                 skb_trim(T)
       (data moves right by L)    (tail moves to data+T)
```

---

## 13. Appendix: Function Signature Quick Reference

```c
/* === Core data manipulation === */
void          skb_reserve(struct sk_buff *skb, int len);
void         *skb_put(struct sk_buff *skb, unsigned int len);
void         *skb_put_data(struct sk_buff *skb, const void *data, unsigned int len);
void         *skb_put_zero(struct sk_buff *skb, unsigned int len);
void         *skb_push(struct sk_buff *skb, unsigned int len);
void         *skb_pull(struct sk_buff *skb, unsigned int len);
void          skb_trim(struct sk_buff *skb, unsigned int len);

/* === Unchecked variants (no safety checks) === */
void         *__skb_put(struct sk_buff *skb, unsigned int len);
void         *__skb_push(struct sk_buff *skb, unsigned int len);
void         *__skb_pull(struct sk_buff *skb, unsigned int len);
void          __skb_trim(struct sk_buff *skb, unsigned int len);

/* === Non-linear (paged) data variants === */
void         *pskb_pull(struct sk_buff *skb, unsigned int len);
int           pskb_trim(struct sk_buff *skb, unsigned int len);
int           pskb_may_pull(struct sk_buff *skb, unsigned int len);

/* === Space queries === */
unsigned int  skb_headroom(const struct sk_buff *skb);
int           skb_tailroom(const struct sk_buff *skb);
unsigned int  skb_headlen(const struct sk_buff *skb);

/* === Header offset management === */
void          skb_reset_mac_header(struct sk_buff *skb);
void          skb_reset_network_header(struct sk_buff *skb);
void          skb_reset_transport_header(struct sk_buff *skb);
void          skb_set_mac_header(struct sk_buff *skb, int offset);
void          skb_set_network_header(struct sk_buff *skb, int offset);
void          skb_set_transport_header(struct sk_buff *skb, int offset);

/* === Header accessors === */
unsigned char *skb_mac_header(const struct sk_buff *skb);
unsigned char *skb_network_header(const struct sk_buff *skb);
unsigned char *skb_transport_header(const struct sk_buff *skb);
struct iphdr  *ip_hdr(const struct sk_buff *skb);
struct tcphdr *tcp_hdr(const struct sk_buff *skb);
struct ethhdr *eth_hdr(const struct sk_buff *skb);

/* === Safety and reallocation === */
int           skb_cow_head(struct sk_buff *skb, unsigned int headroom);
struct sk_buff *skb_realloc_headroom(struct sk_buff *skb, unsigned int headroom);
int           pskb_expand_head(struct sk_buff *skb, int nhead, int ntail, gfp_t gfp);
int           skb_linearize(struct sk_buff *skb);
```

---

*Next: [Chapter 4: Cloning, Copying, and Reference Counting](04-cloning-copying-refcounting.md)*
