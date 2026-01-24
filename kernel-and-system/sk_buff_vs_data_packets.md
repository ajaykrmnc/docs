# sk_buff vs Data Packets: A Comprehensive Guide

## Executive Summary

This document explores the fundamental distinction between **`sk_buff`** (socket buffer) — the Linux kernel's
internal data structure for managing network packets — and **data packets** — the actual network data that
travels across the wire. Understanding this difference is crucial for kernel developers, network programmers,
and anyone working with Linux networking.

---

## 1. What is a Data Packet?

A **data packet** is the actual unit of data transmitted over a network. It follows the OSI model or TCP/IP
model layering and consists of:

### 1.1 Packet Structure at Each Layer

```
┌─────────────────────────────────────────────────────────────────┐
│                    PHYSICAL LAYER (Layer 1)                     │
│  Raw bits/signals on the wire                                   │
├─────────────────────────────────────────────────────────────────┤
│                    DATA LINK LAYER (Layer 2)                    │
│  ┌──────────────┬─────────────────────────┬──────────────────┐  │
│  │ Ethernet Hdr │        Payload          │      FCS         │  │
│  │   (14 bytes) │                         │   (4 bytes)      │  │
│  └──────────────┴─────────────────────────┴──────────────────┘  │
├─────────────────────────────────────────────────────────────────┤
│                    NETWORK LAYER (Layer 3)                      │
│  ┌──────────────┬─────────────────────────────────────────────┐ │
│  │   IP Header  │              Payload                        │ │
│  │ (20-60 bytes)│                                             │ │
│  └──────────────┴─────────────────────────────────────────────┘ │
├─────────────────────────────────────────────────────────────────┤
│                   TRANSPORT LAYER (Layer 4)                     │
│  ┌──────────────┬─────────────────────────────────────────────┐ │
│  │  TCP/UDP Hdr │           Application Data                  │ │
│  │(8-60 bytes)  │                                             │ │
│  └──────────────┴─────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
```

### 1.2 Key Characteristics of Data Packets

| Characteristic              | Description                                               |
| --------------------------- | --------------------------------------------------------- |
| **Physical representation** | Actual bytes transmitted on network medium                |
| **Protocol-defined**        | Structure defined by RFC standards (e.g., RFC 791 for IP) |
| **Self-contained**          | Contains all info needed for routing/delivery             |
| **Stateless**               | Each packet is independent                                |
| **Fixed format**            | Headers have defined positions and sizes                  |

---

## 2. What is sk_buff?

**`sk_buff`** (socket buffer) is the Linux kernel's **metadata structure** that manages and tracks network
packets as they traverse the kernel's networking stack. It is NOT the packet itself—it's a control structure
that points to and describes the packet data.

### 2.1 The Critical Distinction

```
┌─────────────────────────────────────────────────────────────────┐
│                       sk_buff Structure                         │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │  *next, *prev      → Linked list pointers                 │  │
│  │  *sk               → Associated socket                    │  │
│  │  *dev              → Network device                       │  │
│  │  *dst              → Routing information                  │  │
│  │  tstamp            → Timestamp                            │  │
│  │  protocol          → Protocol identifier                  │  │
│  │  pkt_type          → Packet type (PACKET_HOST, etc.)      │  │
│  │  ip_summed         → Checksum status                      │  │
│  │  len               → Total data length                    │  │
│  │  data_len          → Length of paged data                 │  │
│  │  mac_len           → MAC header length                    │  │
│  │  *head             → Start of buffer                      │  │
│  │  *data             → Start of actual data                 │  │
│  │  *tail             → End of actual data                   │  │
│  │  *end              → End of buffer                        │  │
│  │  cb[48]            → Control buffer (protocol private)    │  │
│  │  transport_header  → L4 header offset                     │  │
│  │  network_header    → L3 header offset                     │  │
│  │  mac_header        → L2 header offset                     │  │
│  └───────────────────────────────────────────────────────────┘  │
│                              │                                  │
│                              │ Points to                        │
│                              ▼                                  │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │                  Actual Packet Data Buffer                │  │
│  │  ┌─────────┬──────────────────────┬─────────┬──────────┐  │  │
│  │  │headroom │   packet data        │tailroom │shinfo    │  │  │
│  │  └─────────┴──────────────────────┴─────────┴──────────┘  │  │
│  └───────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

### 2.2 sk_buff Buffer Layout

```
---------------
| sk_buff       |  ← Metadata structure (~200 bytes)
---------------
,---------------------------  + head
/          ,-----------------  + data
/          /      ,-----------  + tail
|          |      |            , + end
|          |      |           |
v          v      v           v
-----------------------------------------------
| headroom | data |  tailroom | skb_shared_info |
-----------------------------------------------
+ [page frag]
+ [page frag]
+ [page frag]
+ [page frag]       ---------
+ frag_list    --> | sk_buff |
---------
```

---

## 3. Key Differences: sk_buff vs Data Packet

| Aspect                | sk_buff                            | Data Packet                         |
| --------------------- | ---------------------------------- | ----------------------------------- |
| **Nature**            | Kernel metadata structure          | Actual network data                 |
| **Location**          | Kernel memory only                 | Network wire, NIC buffers, memory   |
| **Lifetime**          | Created/destroyed in kernel        | Exists from creation to delivery    |
| **Size**              | ~200+ bytes (struct) + data buffer | Varies (64 - 65535 bytes typically) |
| **Content**           | Pointers, flags, metadata          | Headers + payload                   |
| **Purpose**           | Efficient packet management        | Data transmission                   |
| **Visibility**        | Kernel internal only               | Visible on network                  |
| **Protocol Agnostic** | Yes (handles all protocols)        | Protocol-specific format            |
| **Mutable**           | Yes (pointers move)                | Headers can be modified             |
| **Cloning**           | Fast (share data buffer)           | Requires full copy                  |

---

## 4. The Four Critical Pointers

The sk_buff structure uses four pointers to manage the data buffer efficiently:

```c
unsigned char *head;   // Absolute start of allocated buffer
unsigned char *data;   // Start of actual packet data
unsigned char *tail;   // End of actual packet data
unsigned char *end;    // Absolute end of allocated buffer (start of skb_shared_info)
```

### 4.1 Pointer Relationships

```
head                    data              tail                 end
│                       │                 │                    │
▼                       ▼                 ▼                    ▼
┌───────────────────────┬─────────────────┬────────────────────┬──────────────┐
│      HEADROOM         │   PACKET DATA   │     TAILROOM       │ skb_shared_  │
│   (for adding hdrs)   │  (actual data)  │  (for adding data) │    info      │
└───────────────────────┴─────────────────┴────────────────────┴──────────────┘

│◄────────────────────── skb_headroom ──►│
│◄─── skb_len ──►│
│◄── skb_tailroom ───►│
│◄──────────────────────────────── total buffer ─────────────────────────────►│
```

### 4.2 Length Calculations

```c
skb->len        = tail - data;           // Total data length
skb_headroom()  = data - head;           // Space before data
skb_tailroom()  = end - tail;            // Space after data
skb_headlen()   = skb->len - skb->data_len;  // Linear data length
```

---

## 5. sk_buff Operations: Manipulating the Packet

### 5.1 skb_reserve() - Reserve Headroom

Called **before** adding any data to reserve space for protocol headers.

```c
// Reserve space for maximum expected headers
skb_reserve(skb, MAX_TCP_HEADER);
```

```
BEFORE skb_reserve():
head,data,tail                                            end
│                                                       │
▼                                                       ▼
┌───────────────────────────────────────────────────────┐
│                   ALL TAILROOM                        │
└───────────────────────────────────────────────────────┘

AFTER skb_reserve(skb, header_len):
head              data,tail                                end
│                 │                                      │
▼                 ▼                                      ▼
┌─────────────────┬─────────────────────────────────────┐
│    HEADROOM     │            TAILROOM                 │
│  (reserved)     │                                     │
└─────────────────┴─────────────────────────────────────┘
```

### 5.2 skb_put() - Add Data to Tail

Adds data at the end of the packet (extends tail).

```c
unsigned char *ptr = skb_put(skb, len);
memcpy(ptr, user_data, len);
```

```
BEFORE skb_put():
head              data            tail                     end
│               │               │                        │
▼               ▼               ▼                        ▼
┌───────────────┬───────────────┬────────────────────────┐
│   HEADROOM    │  PACKET DATA  │       TAILROOM         │
└───────────────┴───────────────┴────────────────────────┘

AFTER skb_put(skb, len):
head              data                      tail           end
│               │                         │              │
▼               ▼                         ▼              ▼
┌───────────────┬─────────────────────────┬──────────────┐
│   HEADROOM    │     PACKET DATA         │  TAILROOM    │
│               │     (extended)          │  (reduced)   │
└───────────────┴─────────────────────────┴──────────────┘
```

### 5.3 skb_push() - Add Header to Head

Prepends a header by moving data pointer backward (into headroom).

```c
// Add TCP header
struct tcphdr *th = skb_push(skb, sizeof(struct tcphdr));
th->source = htons(src_port);
th->dest = htons(dst_port);
```

```
BEFORE skb_push():
head              data                      tail           end
│               │                         │              │
▼               ▼                         ▼              ▼
┌───────────────┬─────────────────────────┬──────────────┐
│   HEADROOM    │     PAYLOAD DATA        │  TAILROOM    │
└───────────────┴─────────────────────────┴──────────────┘

AFTER skb_push(skb, sizeof(struct tcphdr)):
head        data                            tail           end
│         │                               │              │
▼         ▼                               ▼              ▼
┌─────────┬───────┬───────────────────────┬──────────────┐
│HEADROOM │TCP HDR│     PAYLOAD DATA      │  TAILROOM    │
│(reduced)│       │                       │              │
└─────────┴───────┴───────────────────────┴──────────────┘
```

### 5.4 skb_pull() - Remove Header from Head

Removes/skips a header by advancing the data pointer (used during receive).

```c
// Skip over Ethernet header during receive processing
skb_pull(skb, ETH_HLEN);
```

```
BEFORE skb_pull() (receiving packet):
head,data                                   tail           end
│                                         │              │
▼                                         ▼              ▼
┌───────┬───────┬─────────────────────────┬──────────────┐
│ETH HDR│IP HDR │     PAYLOAD DATA        │  TAILROOM    │
└───────┴───────┴─────────────────────────┴──────────────┘

AFTER skb_pull(skb, ETH_HLEN):
head        data                            tail           end
│         │                               │              │
▼         ▼                               ▼              ▼
┌─────────┬───────┬───────────────────────┬──────────────┐
│(skipped)│IP HDR │     PAYLOAD DATA      │  TAILROOM    │
└─────────┴───────┴───────────────────────┴──────────────┘
```

---

## 6. Packet Lifecycle: Transmit Path (TX)

When an application sends data, here's how sk_buff and packet data interact:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         APPLICATION LAYER                                   │
│   Application calls write()/sendto()/sendmsg()                              │
└─────────────────────────────────────────────────────────────────────────────┘
│
▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                          SOCKET LAYER                                       │
│   1. sk_buff allocated with alloc_skb()                                     │
│   2. skb_reserve() called to reserve header space                           │
│   3. User data copied via skb_put() + copy_from_user()                      │
│                                                                             │
│   sk_buff state: [headroom][         user_data        ][tailroom]           │
└─────────────────────────────────────────────────────────────────────────────┘
│
▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                       TRANSPORT LAYER (TCP/UDP)                             │
│   1. skb_push() to add TCP/UDP header                                       │
│   2. Fill in ports, sequence numbers, checksum                              │
│   3. tcp_sendmsg() / udp_sendmsg()                                          │
│                                                                             │
│   sk_buff state: [headroom][TCP_HDR][    user_data    ][tailroom]           │
└─────────────────────────────────────────────────────────────────────────────┘
│
▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                        NETWORK LAYER (IP)                                   │
│   1. skb_push() to add IP header                                            │
│   2. ip_queue_xmit() fills src/dst IP, TTL, protocol                        │
│   3. Routing decision (skb->dst populated)                                  │
│                                                                             │
│   sk_buff state: [headroom][IP_HDR][TCP_HDR][ user_data ][tailroom]         │
└─────────────────────────────────────────────────────────────────────────────┘
│
▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                       DATA LINK LAYER (Ethernet)                            │
│   1. eth_header() → skb_push() to add Ethernet header                       │
│   2. Fill destination MAC (from ARP cache), source MAC, EtherType           │
│   3. dev_queue_xmit() called                                                │
│                                                                             │
│   sk_buff state: [ETH_HDR][IP_HDR][TCP_HDR][ user_data ][tailroom]          │
│                    └─────────── Complete packet ──────────┘                 │
└─────────────────────────────────────────────────────────────────────────────┘
│
▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                         DEVICE DRIVER                                       │
│   1. ndo_start_xmit() receives complete sk_buff                             │
│   2. DMA mapping: maps sk_buff data to hardware                             │
│   3. Packet transmitted on wire                                             │
│   4. sk_buff freed after transmission complete                              │
│                                                                             │
│   ⚡ ACTUAL PACKET leaves as bytes on the wire!                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 6.1 Code Flow (Simplified)

```c
// Application
write(sockfd, data, len);

// Socket Layer (net/socket.c)
sock_sendmsg() → inet_sendmsg()

// Transport Layer (net/ipv4/tcp_output.c or udp.c)
tcp_sendmsg() {
  skb = sk_stream_alloc_skb();
  skb_reserve(skb, MAX_TCP_HEADER);
  skb_put(skb, copy);
  copy_from_user(skb->data, from, copy);
  __tcp_push_pending_frames(sk, mss);
}

// IP Layer (net/ipv4/ip_output.c)
ip_queue_xmit() {
  skb_push(skb, sizeof(struct iphdr));
  // Fill IP header
  ip_local_out();
}

// Ethernet Layer (net/ethernet/eth.c)
eth_header() {
  eth = skb_push(skb, ETH_HLEN);
  memcpy(eth->h_dest, daddr, ETH_ALEN);
  memcpy(eth->h_source, saddr, ETH_ALEN);
  eth->h_proto = htons(type);
}

// Device (dev_queue_xmit → driver)
driver_xmit(skb) {
  dma_map_single(skb->data, skb->len);
  // Configure TX descriptor, trigger transmission
}
```

---

## 7. Packet Lifecycle: Receive Path (RX)

When a packet arrives from the network:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         NETWORK INTERFACE CARD                              │
│   1. Packet arrives as electrical signals                                   │
│   2. NIC DMA copies bytes into pre-allocated buffer (ring buffer)           │
│   3. Interrupt raised → NAPI polling starts                                 │
└─────────────────────────────────────────────────────────────────────────────┘
│
▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                         DEVICE DRIVER                                       │
│   1. sk_buff created pointing to received data                              │
│   2. skb->protocol set via eth_type_trans()                                 │
│   3. netif_receive_skb() called                                             │
│                                                                             │
│   sk_buff state: data→[ETH_HDR][IP_HDR][TCP_HDR][payload]                   │
└─────────────────────────────────────────────────────────────────────────────┘
│
▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                       DATA LINK LAYER                                       │
│   1. eth_type_trans() processes Ethernet header                             │
│   2. skb_pull() to skip Ethernet header                                     │
│   3. Dispatch based on EtherType (0x0800 = IPv4)                            │
│                                                                             │
│   sk_buff state: [skipped]data→[IP_HDR][TCP_HDR][payload]                   │
└─────────────────────────────────────────────────────────────────────────────┘
│
▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                        NETWORK LAYER (IP)                                   │
│   1. ip_rcv() validates IP header                                           │
│   2. Routing decision (local delivery vs forward)                           │
│   3. skb_pull() to skip IP header                                           │
│   4. ip_local_deliver() for local packets                                   │
│                                                                             │
│   sk_buff state: [skipped][skipped]data→[TCP_HDR][payload]                  │
└─────────────────────────────────────────────────────────────────────────────┘
│
▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                       TRANSPORT LAYER (TCP/UDP)                             │
│   1. tcp_v4_rcv() / udp_rcv() processes header                              │
│   2. Find associated socket                                                 │
│   3. skb_pull() to skip TCP/UDP header                                      │
│   4. Queue data to socket receive buffer                                    │
│                                                                             │
│   sk_buff state: [skipped][skipped][skipped]data→[payload]                  │
└─────────────────────────────────────────────────────────────────────────────┘
│
▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                          SOCKET LAYER                                       │
│   1. Data queued in sk->sk_receive_queue                                    │
│   2. Wake up any waiting processes                                          │
│   3. read()/recvfrom()/recvmsg() copies to user space                       │
│   4. sk_buff freed after data copied                                        │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 8. sk_buff Cloning and Sharing

### 8.1 Why Clone?

Multiple entities may need access to the same packet data:

- Packet sniffers (tcpdump)
- TCP retransmission (keep original, send clone)
- Multicast/broadcast forwarding

### 8.2 Clone vs Copy

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           SKB CLONING (Fast)                                │
│                                                                             │
│   Original sk_buff                     Cloned sk_buff                       │
│   ┌─────────────┐                     ┌─────────────┐                       │
│   │ next, prev  │                     │ next, prev  │  ← Private copy       │
│   │ sk, dev     │                     │ sk, dev     │                       │
│   │ head, data  │──────┐       ┌──────│ head, data  │                       │
│   │ tail, end   │      │       │      │ tail, end   │                       │
│   │ len, etc.   │      │       │      │ len, etc.   │                       │
│   │ cloned=1    │      │       │      │ cloned=1    │                       │
│   └─────────────┘      │       │      └─────────────┘                       │
│                        │       │                                            │
│                        ▼       ▼                                            │
│                ┌───────────────────────────┐                                │
│                │   SHARED DATA BUFFER      │  ← refcount incremented        │
│                │ ┌───────────────────────┐ │                                │
│                │ │ skb_shared_info       │ │                                │
│                │ │   dataref = 2         │ │                                │
│                │ └───────────────────────┘ │                                │
│                └───────────────────────────┘                                │
│                                                                             │
│   skb_clone() → New sk_buff struct, SAME data buffer                        │
│   Cost: ~200 bytes (struct only)                                            │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│                           SKB COPY (Slow)                                   │
│                                                                             │
│   Original sk_buff                     Copied sk_buff                       │
│   ┌─────────────┐                     ┌─────────────┐                       │
│   │ metadata    │                     │ metadata    │                       │
│   │ head, data  │──┐               ┌──│ head, data  │                       │
│   └─────────────┘  │               │  └─────────────┘                       │
│                    ▼               ▼                                        │
│           ┌────────────────┐  ┌────────────────┐                            │
│           │ DATA BUFFER 1  │  │ DATA BUFFER 2  │                            │
│           │ [packet data]  │  │ [packet data]  │  ← Full copy!              │
│           └────────────────┘  └────────────────┘                            │
│                                                                             │
│   skb_copy() → New sk_buff struct AND new data buffer                       │
│   Cost: ~200 bytes + packet_size bytes                                      │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 9. Non-Linear (Paged) Data

For large packets or zero-copy operations, sk_buff supports fragmented data:

### 9.1 Linear vs Non-Linear Data

```
LINEAR DATA (Simple Case):
┌─────────────────────────────────────────────────────────────────────────────┐
│  sk_buff                                                                    │
│  ┌──────────────┐         ┌──────────────────────────────────────────────┐  │
│  │ head ────────│────────►│ [headroom][     all packet data      ]       │  │
│  │ data ────────│─────┐   │           ▲                          ▲       │  │
│  │ tail ────────│──┐  │   │           │                          │       │  │
│  │ len = 1500   │  │  └───│───────────┘                          │       │  │
│  │ data_len = 0 │  └──────│──────────────────────────────────────┘       │  │
│  └──────────────┘         └──────────────────────────────────────────────┘  │
│                                                                             │
│  skb_headlen(skb) = len - data_len = 1500 (all data in linear buffer)       │
└─────────────────────────────────────────────────────────────────────────────┘

NON-LINEAR DATA (Paged/Fragmented):
┌─────────────────────────────────────────────────────────────────────────────┐
│  sk_buff                                                                    │
│  ┌──────────────┐         ┌────────────────────────┐                        │
│  │ head ────────│────────►│ [headroom][headers]    │ ← Linear portion       │
│  │ data ────────│─────┐   │           ▲            │                        │
│  │ tail ────────│──┐  │   │           │            │                        │
│  │ len = 65000  │  │  └───│───────────┘            │                        │
│  │ data_len=64K │  └──────│────────────────────────│                        │
│  └──────────────┘         │ skb_shared_info:       │                        │
│                           │   nr_frags = 3         │                        │
│                           │   frags[0] ─────────►[PAGE 1: 16KB]             │
│                           │   frags[1] ─────────►[PAGE 2: 16KB]             │
│                           │   frags[2] ─────────►[PAGE 3: 32KB]             │
│                           └────────────────────────┘                        │
│                                                                             │
│  skb_headlen(skb) = len - data_len = 1000 (headers in linear buffer)        │
│  skb_is_nonlinear(skb) = true                                               │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 9.2 Page Fragment Structure

```c
struct skb_frag_struct {
  struct page *page;      // Pointer to memory page
  __u16 page_offset;      // Offset within the page
  __u16 size;             // Size of data in this fragment
};

struct skb_shared_info {
  atomic_t dataref;           // Reference count for data
  unsigned int nr_frags;      // Number of page fragments
  unsigned short gso_size;    // GSO segment size
  unsigned short gso_segs;    // Number of GSO segments
  struct sk_buff *frag_list;  // List of sk_buffs for IP fragments
  skb_frag_t frags[MAX_SKB_FRAGS];  // Page fragments array
};
```

---

## 10. Header Location Tracking

sk_buff tracks where each protocol header is located:

```c
// Modern kernel uses offsets (not pointers) for cache efficiency
struct sk_buff {
  ...
  __u16 transport_header;   // Offset to L4 (TCP/UDP) header
  __u16 network_header;     // Offset to L3 (IP) header
  __u16 mac_header;         // Offset to L2 (Ethernet) header
  ...
};

// Helper functions to get actual pointers
static inline unsigned char *skb_mac_header(const struct sk_buff *skb)
{
  return skb->head + skb->mac_header;
}

static inline unsigned char *skb_network_header(const struct sk_buff *skb)
{
  return skb->head + skb->network_header;
}

static inline unsigned char *skb_transport_header(const struct sk_buff *skb)
{
  return skb->head + skb->transport_header;
}
```

### 10.1 Header Offset Visualization

```
head                                                 end
│                                                   │
▼                                                   ▼
┌───────┬────────┬────────┬───────────┬─────────────┐
│ETH HDR│ IP HDR │TCP HDR │  PAYLOAD  │ skb_shared_ │
└───────┴────────┴────────┴───────────┴─────────────┘
▲       ▲        ▲        ▲
│       │        │        │
mac_header    │        │        │
│ network_header │        │
│       │ transport_header│
│       │        │        │
│       │        │        └── data (after headers processed)
│       │        │
└───────┴────────┴── Offsets from head (stored as __u16)
```

---

## 11. sk_buff Memory Management

### 11.1 Allocation

```c
// General allocation (can sleep)
struct sk_buff *skb = alloc_skb(size, GFP_KERNEL);

// Driver allocation (atomic context, for interrupt handlers)
struct sk_buff *skb = netdev_alloc_skb(dev, size);
struct sk_buff *skb = dev_alloc_skb(size);  // Deprecated

// With IP alignment (NET_IP_ALIGN = 2 on most platforms)
struct sk_buff *skb = netdev_alloc_skb_ip_align(dev, size);
```

### 11.2 Reference Counting

```c
// sk_buff has users field for refcounting
atomic_t users;

// Increment reference
skb_get(skb);      // users++

// Decrement reference (free if users == 0)
kfree_skb(skb);    // users--, free if 0
consume_skb(skb);  // Same but for "consumed" packets (different trace)

// Driver cleanup
dev_kfree_skb(skb);
dev_kfree_skb_any(skb);  // Safe in any context
```

### 11.3 Socket Buffer Accounting

sk_buff tracks memory for socket buffer accounting:

```c
struct sk_buff {
  ...
  struct sock *sk;           // Associated socket
  unsigned int truesize;     // Total memory consumed
  void (*destructor)(struct sk_buff *skb);  // Cleanup callback
  ...
};

// truesize includes:
// - sizeof(struct sk_buff)
// - Actual data buffer size
// - Any associated page fragments
```

---

## 12. Performance Optimizations

### 12.1 Zero-Copy Transmission

sk_buff enables zero-copy by pointing directly to user memory pages:

```
Traditional Copy:
┌──────────────┐     memcpy      ┌──────────────┐     DMA      ┌─────────┐
│  User Buffer │ ───────────────► │  Kernel skb  │ ───────────► │   NIC   │
└──────────────┘                 └──────────────┘              └─────────┘

Zero-Copy (sendfile, MSG_ZEROCOPY):
┌──────────────┐                  ┌──────────────┐     DMA      ┌─────────┐
│  User Pages  │ ◄───page ref──── │  skb frags   │ ───────────► │   NIC   │
└──────────────┘                  └──────────────┘              └─────────┘
(no data copy!)
```

### 12.2 GSO/TSO (Segmentation Offload)

Large packets can be passed to hardware for segmentation:

```c
struct sk_buff {
  ...
  // In skb_shared_info:
  unsigned short gso_size;    // Size of each segment
  unsigned short gso_segs;    // Number of segments
  unsigned short gso_type;    // SKB_GSO_TCPV4, SKB_GSO_TCPV6, etc.
  ...
};
```

### 12.3 Checksum Offload

```c
struct sk_buff {
  ...
  __u8 ip_summed:2;          // Checksum status
  // CHECKSUM_NONE      - No checksum computed
  // CHECKSUM_PARTIAL   - Partial checksum, HW to complete
  // CHECKSUM_COMPLETE  - Full checksum in skb->csum
  // CHECKSUM_UNNECESSARY - Checksum verified by HW

  __u16 csum_start;          // Offset where checksum starts
  __u16 csum_offset;         // Offset to store checksum result
  __u32 csum;                // Checksum value
  ...
};
```

---

## 13. Control Buffer (cb)

Each sk_buff has a private storage area for protocol-specific data:

```c
struct sk_buff {
  ...
  char cb[48];  // Control buffer - opaque to other layers
  ...
};

// TCP uses it to store per-packet state:
struct tcp_skb_cb {
  __u32 seq;           // Starting sequence number
  __u32 end_seq;       // Ending sequence number
  __u32 tcp_tw_isn;    // ISN for TIME_WAIT
  __u8  tcp_flags;     // TCP flags
  __u8  sacked;        // SACK state
  // ... more TCP-specific fields
};

#define TCP_SKB_CB(__skb) ((struct tcp_skb_cb *)&((__skb)->cb[0]))
```

---

## 14. Summary: The Complete Picture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    DATA PACKET (What's on the Wire)                         │
│  ┌─────────┬─────────┬─────────┬─────────────────────────────────┬────────┐ │
│  │Preamble │ ETH HDR │ IP HDR  │       TCP HDR + PAYLOAD         │  FCS   │ │
│  │ (8B)    │ (14B)   │ (20B)   │                                 │  (4B)  │ │
│  └─────────┴─────────┴─────────┴─────────────────────────────────┴────────┘ │
│                    ▲                                                        │
│                    │                                                        │
│         This is the ACTUAL data transmitted                                 │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│                    sk_buff (Kernel's View/Management)                       │
│                                                                             │
│  struct sk_buff {                    Data Buffer:                           │
│    *next, *prev;   ─────┐           ┌─────────────────────────────────────┐ │
│    *sk;                 │           │ head                                │ │
│    tstamp;              │           │  ↓                                  │ │
│    *dev;                │           │ [hdrm][ETH][IP][TCP][PAYLOAD][tail] │ │
│    *dst;            ────┼───────────│                    ↑                │ │
│    transport_header;    │           │                  data               │ │
│    network_header;      │           │                                     │ │
│    mac_header;          │           │ skb_shared_info:                    │ │
│    *head; ──────────────┼───────────│   dataref, frags[], frag_list       │ │
│    *data; ──────────────┼───────────│                   ↑                 │ │
│    *tail; ──────────────┼───────────│                  end                │ │
│    *end; ───────────────┘           └─────────────────────────────────────┘ │
│    len;                                                                     │
│    data_len;                                                                │
│    cb[48];                                                                  │
│    ip_summed;                                                               │
│    protocol;                                                                │
│    ...                                                                      │
│  };                                                                         │
│                                                                             │
│  This is the METADATA + pointers to data                                    │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Key Takeaways

1. **sk_buff is NOT the packet** — it's a metadata structure that manages packet data
2. **Packet data lives in a separate buffer** — sk_buff points to it
3. **Four pointers (head/data/tail/end)** enable efficient header manipulation
4. **skb_push/skb_pull** move data pointer without copying data
5. **Cloning shares data buffer** — only metadata is duplicated
6. **Non-linear data** enables zero-copy and large packet handling
7. **Header offsets** allow quick access to any protocol layer
8. **The packet on the wire** is just the bytes between headers and tail

---

## 15. Quick Reference

### Common sk_buff Functions

| Function                | Purpose                           |
| ----------------------- | --------------------------------- |
| `alloc_skb(len, gfp)`   | Allocate new sk_buff              |
| `kfree_skb(skb)`        | Free sk_buff                      |
| `skb_reserve(skb, len)` | Reserve headroom                  |
| `skb_put(skb, len)`     | Add data to tail                  |
| `skb_push(skb, len)`    | Add header (move data backward)   |
| `skb_pull(skb, len)`    | Remove header (move data forward) |
| `skb_clone(skb, gfp)`   | Clone (share data buffer)         |
| `skb_copy(skb, gfp)`    | Full copy (new data buffer)       |
| `skb_headroom(skb)`     | Available headroom                |
| `skb_tailroom(skb)`     | Available tailroom                |
| `skb_headlen(skb)`      | Linear data length                |
| `skb_is_nonlinear(skb)` | Check for paged data              |

### Header Access Functions

| Function                    | Returns                   |
| --------------------------- | ------------------------- |
| `skb_mac_header(skb)`       | Pointer to L2 header      |
| `skb_network_header(skb)`   | Pointer to L3 header      |
| `skb_transport_header(skb)` | Pointer to L4 header      |
| `eth_hdr(skb)`              | Cast to `struct ethhdr *` |
| `ip_hdr(skb)`               | Cast to `struct iphdr *`  |
| `tcp_hdr(skb)`              | Cast to `struct tcphdr *` |
| `udp_hdr(skb)`              | Cast to `struct udphdr *` |

---

## References

- Linux Kernel Documentation: https://docs.kernel.org/networking/skbuff.html
- How SKBs Work (Dave Miller): [Link 2](http://oldvger.kernel.org/~davem/skb.html)
- Linux Foundation Wiki: [Link 3](https://wiki.linuxfoundation.org/networking/sk_buff)
- Linux Kernel Source: `include/linux/skbuff.h`, `net/core/skbuff.c`
