# Socket and Buffer Structures Documentation

This document describes the socket (`sk_sock`) and buffer (`sk_buff`) structures used in the AP codebase.

## General Information

### Purpose

In Linux kernel networking, two fundamental concepts govern how network data flows through the system:

1. **Sockets (`sk_sock`)** - Endpoints for network communication that provide the interface between user-space applications and the kernel networking stack. They manage connection state, buffering, and protocol handling.

2. **Socket Buffers (`sk_buff`)** - The primary data structure for representing network packets as they traverse the kernel. Every packet received or transmitted goes through an `sk_buff`.

### Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                     User Space                               │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐  │
│  │  sensord    │  │  hostapd    │  │  wlan-drivers       │  │
│  └──────┬──────┘  └──────┬──────┘  └──────────┬──────────┘  │
└─────────┼────────────────┼────────────────────┼─────────────┘
          │                │                    │
┌─────────┼────────────────┼────────────────────┼─────────────┐
│         ▼                ▼                    ▼              │
│  ┌─────────────────────────────────────────────────────┐    │
│  │              Socket Layer (sk_sock)                  │    │
│  │   - ial_raw_sock_t    - ial_sniff_sock_t            │    │
│  │   - socket_context    - SOCKET descriptors           │    │
│  └───────────────────────────┬─────────────────────────┘    │
│                              │                               │
│  ┌───────────────────────────▼─────────────────────────┐    │
│  │           Buffer Layer (sk_buff / qdf_nbuf)          │    │
│  │   - Packet data & metadata                           │    │
│  │   - QDF wrappers for portability                     │    │
│  │   - Arista extensions (ar_meta, pkt_trace)           │    │
│  └───────────────────────────┬─────────────────────────┘    │
│                              │                               │
│  ┌───────────────────────────▼─────────────────────────┐    │
│  │              Network Device Drivers                  │    │
│  │   - QCA WLAN drivers                                 │    │
│  │   - Ethernet drivers                                 │    │
│  └─────────────────────────────────────────────────────┘    │
│                        Kernel Space                          │
└─────────────────────────────────────────────────────────────┘
```

### Relationship Between sk_sock and sk_buff

| Aspect | sk_sock (Socket) | sk_buff (Buffer) |
|--------|------------------|------------------|
| **Role** | Communication endpoint | Packet container |
| **Lifetime** | Persists across multiple packets | Per-packet (created/destroyed) |
| **Contains** | Connection state, options, queues | Packet data, headers, metadata |
| **Created by** | `socket()` system call | `alloc_skb()` / `dev_alloc_skb()` |
| **Used for** | Managing connections | Carrying packet data |

### Data Flow Example

1. **Packet Reception:**
   - NIC receives frame → Driver allocates `sk_buff` → Fills with packet data
   - `sk_buff` travels up the stack → Protocol processing → Queued to socket
   - Application reads from socket → Data copied from `sk_buff` → `sk_buff` freed

2. **Packet Transmission:**
   - Application writes to socket → `sk_buff` allocated → Data copied in
   - `sk_buff` travels down the stack → Headers added → Sent to driver
   - Driver transmits → Completion callback → `sk_buff` freed

### Memory Layout of sk_buff

```
      ┌──────────────────────────────────────────┐
      │           sk_buff structure              │
      │  (metadata: len, protocol, dev, etc.)    │
      └──────────────────────────────────────────┘
                         │
                         ▼
      ┌──────────────────────────────────────────┐
 head │              Headroom                    │ ← Space for adding headers
      ├──────────────────────────────────────────┤
 data │                                          │
      │           Actual Packet Data             │ ← len bytes
      │    (Ethernet + IP + TCP/UDP + Payload)   │
      │                                          │
 tail ├──────────────────────────────────────────┤
      │              Tailroom                    │ ← Space for adding trailers
 end  └──────────────────────────────────────────┘
```

### Why Abstractions?

The codebase uses abstraction layers (QDF, ar_os_if) because:

1. **Portability** - Same code works across different kernel versions
2. **Debugging** - Wrappers can add memory tracking and logging
3. **Customization** - Arista-specific fields can be added without modifying core kernel
4. **Vendor Independence** - Abstracts QCA-specific implementations

---

## sk_buff (Socket Buffer)

`struct sk_buff` is the fundamental Linux kernel data structure for network packet handling. It represents a network packet as it flows through the networking stack.

### Overview

The socket buffer is used throughout the WLAN drivers and kernel networking code to:
- Hold packet data (headers and payload)
- Track packet metadata (protocol, device, timestamps)
- Manage memory for efficient packet manipulation

### Key Fields

| Field | Type | Description |
|-------|------|-------------|
| `head` | `unsigned char*` | Start of the allocated buffer |
| `data` | `unsigned char*` | Start of actual packet data |
| `tail` | `unsigned char*` | End of actual packet data |
| `end` | `unsigned char*` | End of allocated buffer |
| `len` | `unsigned int` | Length of actual data |
| `truesize` | `unsigned int` | Total size of buffer including sk_buff struct |
| `users` | `refcount_t` | Reference count |
| `priority` | `__u32` | Packet priority for QoS |
| `protocol` | `__be16` | Packet protocol (ETH_P_*) |

### Custom Extensions (Arista)

The codebase adds custom fields via kernel patches:

| Field | Description | Patch |
|-------|-------------|-------|
| `sum_data` | Additional checksum data | `skb_data_*.patch` |
| `pkt_trace` | Packet tracing pointer | `ar_pkt_trace_*.patch` |
| `ar_meta` | 16-bit metadata cache (TID, EAPOL, DHCP flags) | `ar_skb_meta_cache_*.patch` |

### Wrapper APIs

The QDF (Qualcomm Driver Framework) provides platform-independent wrappers:

```c
// Allocation
qdf_nbuf_t qdf_nbuf_alloc(qdf_device_t osdev, qdf_size_t size,
                          int reserve, int align, int prio);

// Freeing
void qdf_nbuf_free(qdf_nbuf_t buf);

// Data access
void* qdf_nbuf_data(qdf_nbuf_t buf);
uint32_t qdf_nbuf_len(qdf_nbuf_t buf);

// Buffer manipulation
void qdf_nbuf_push_head(qdf_nbuf_t buf, qdf_size_t size);
void qdf_nbuf_pull_head(qdf_nbuf_t buf, qdf_size_t size);
void qdf_nbuf_put_tail(qdf_nbuf_t buf, qdf_size_t size);
void qdf_nbuf_trim_tail(qdf_nbuf_t buf, qdf_size_t size);
```

### OS Interface Helpers (`ar_os_if.h`)

```c
// Expand headroom/tailroom
struct sk_buff* ar_os_skb_expand(struct sk_buff* skb, uint32_t headroom, uint32_t tailroom);

// Put data at tail with automatic expansion
uint8_t* ar_os_skb_put_tail(struct sk_buff* skb, size_t size);

// Priority management
uint32_t ar_os_skb_get_priority(struct sk_buff* skb);
void ar_os_skb_set_priority(struct sk_buff* skb, uint32_t p);

// VLAN handling
int ar_os_skb_vlan_tag_present(struct sk_buff* skb);
int ar_os_skb_vlan_tag_get(struct sk_buff* skb);
void ar_os_skb_put_vlan_tag(struct sk_buff* skb, uint16_t vlan_tag);
```

---

## sk_sock (Socket Abstractions)

The codebase uses several socket abstraction types rather than a single `sk_sock` structure.

### SOCKET Type

Basic socket descriptor type (cross-platform compatible):

```c
#define SOCKET int  // In rpcap_definitions.h
```

### ial_raw_sock_t (Raw Socket)

Used for sending raw packets on interfaces:

```c
typedef struct ial_raw_sock {
    int sock_desc;              // Socket descriptor
    struct ial_iface_info* iface;  // Interface for socket
} ial_raw_sock_t;
```

### ial_sniff_sock_t (Sniffer Socket)

Used for packet sniffing/capture:

```c
typedef struct ial_sniff_sock {
    int sock_desc;              // Socket descriptor
    struct ial_iface_info* iface;  // Interface being sniffed
    MMFrame* frame_q;           // Memory-mapped socket buffer
    int frame_i;                // Index of next frame in buffer
} ial_sniff_sock_t;
```

### socket_context (cfg80211/WEXT)

Used for driver configuration:

```c
struct socket_context {
    u_int8_t cfg80211;              // cfg80211 enable flag
    wifi_cfg80211_context cfg80211_ctxt;  // cfg80211 context
    int sock_fd;                    // WEXT socket file descriptor
};
```

### Socket Utility Functions (`rpcap_sockutils.h`)

```c
int sock_open(struct addrinfo* addrinfo, int server, int nconn, char* errbuf);
int sock_close(SOCKET sock, char* errbuf);
int sock_send(SOCKET socket, const char* buffer, int size, char* errbuf);
int sock_recv(SOCKET socket, char* buffer, int size, char* errbuf);
int sock_bufferize(const char* buffer, int size, char* tempbuf,
                   int* offset, int totsize, int checkonly, char* errbuf);
int sock_discard(SOCKET socket, int size, char* errbuf);
void sock_geterror(const char* caller, char* string, int size);
```

---

## Key Source Files

| File | Description |
|------|-------------|
| `src/wlan-drivers/ar/os_if/ar_os_if.h` | OS interface wrappers for sk_buff |
| `src/sensord/include/ial/ial.h` | IAL socket structures |
| `src/sensord/include/packet_capture/rpcap_*.h` | Socket utilities |
| `src/wlan-drivers/QCA/.../qdf/inc/qdf_nbuf.h` | QDF nbuf abstraction |
| `platform/patches/kernel/5.4/*/ar_*.patch` | Kernel sk_buff patches |

