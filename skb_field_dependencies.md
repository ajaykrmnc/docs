# sk_buff Field Dependencies and Offset Caching

## Overview

This document explains why certain `sk_buff` fields have dependencies declared for eBPF offset resolution, while others do not. It also covers the parameter fetching and caching mechanism for BTF (BPF Type Format) offsets from kernel binaries.

---

## General Information

### Document Purpose

This document serves as a comprehensive technical reference for understanding:
- How the QCA WiFi driver fetches packets from hardware into Linux `sk_buff` structures
- Why certain sk_buff fields require BTF offset dependencies for eBPF access
- The complete RX/TX data paths from hardware to network stack
- Parameter caching mechanisms for efficient eBPF program execution

### Target Audience

- WiFi driver developers working on QCA chipsets
- eBPF/XDP developers creating network monitoring or packet processing programs
- Kernel developers modifying sk_buff structures
- Engineers debugging packet flow issues in the WiFi stack

---

### Glossary of Terms

| Term | Full Form | Description |
|------|-----------|-------------|
| **sk_buff** | Socket Buffer | Linux kernel's fundamental network buffer structure for packet data |
| **qdf_nbuf** | QCA Driver Framework Network Buffer | QCA's wrapper around sk_buff for cross-platform compatibility |
| **BTF** | BPF Type Format | Type information embedded in kernel/modules for eBPF program access |
| **eBPF** | Extended Berkeley Packet Filter | In-kernel virtual machine for safe, efficient packet/event processing |
| **SRNG** | Scatter-Gather Ring | Hardware ring buffer for DMA operations between host and WiFi hardware |
| **REO** | Reorder Engine | WiFi hardware component for packet reordering and block-ack window management |
| **RXDMA** | Receive DMA | Hardware DMA engine that fetches buffers and writes received packet data |
| **TCL** | Transmit Command and Status | Hardware ring for TX packet submission |
| **WBM** | Wireless Buffer Manager | Hardware component managing buffer allocation/deallocation |
| **HAL** | Hardware Abstraction Layer | Software layer abstracting hardware ring details |
| **TLV** | Type-Length-Value | Metadata format used by hardware to describe packet attributes |
| **MSDU** | MAC Service Data Unit | Individual data frame (can be aggregated into A-MSDU) |
| **MPDU** | MAC Protocol Data Unit | 802.11 frame including MAC header (can be aggregated into A-MPDU) |
| **A-MPDU** | Aggregated MPDU | Multiple MPDUs aggregated for efficient transmission |
| **BA** | Block Acknowledgment | Mechanism for acknowledging multiple frames at once |
| **NAPI** | New API | Linux kernel interface for efficient network polling |
| **GRO** | Generic Receive Offload | Kernel feature to merge packets before stack processing |
| **DMA** | Direct Memory Access | Hardware-to-memory transfer without CPU involvement |
| **Cookie** | SW Buffer Cookie | 21-bit identifier for HW-to-SW descriptor lookup |
| **cb** | Control Block | 48-byte private data area in sk_buff for driver use |
| **ar_meta** | Arista Metadata | Custom 16-bit field added to sk_buff via kernel patches |
| **VDEV** | Virtual Device | Virtual AP or STA interface |
| **PDEV** | Physical Device | Physical radio interface |
| **SOC** | System on Chip | Top-level driver structure representing the WiFi chipset |
| **CO-RE** | Compile Once, Run Everywhere | eBPF feature for portable programs across kernel versions |

---

### QCA WiFi Driver Architecture

The QCA WiFi driver stack consists of multiple layers:

```
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                              QCA WiFi Driver Stack                                   │
├─────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                      │
│  ┌─────────────────────────────────────────────────────────────────────────────────┐│
│  │ User Space                                                                       ││
│  │ ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          ││
│  │ │ hostapd/wpa  │  │ cfg80211     │  │ iw/iwconfig  │  │ eBPF tools   │          ││
│  │ │ supplicant   │  │ netlink      │  │ commands     │  │ (bpftool)    │          ││
│  │ └──────────────┘  └──────────────┘  └──────────────┘  └──────────────┘          ││
│  └─────────────────────────────────────────────────────────────────────────────────┘│
│         │                    │                    │                    │             │
│         ▼                    ▼                    ▼                    ▼             │
│  ┌─────────────────────────────────────────────────────────────────────────────────┐│
│  │ Kernel Space                                                                     ││
│  │                                                                                  ││
│  │  ┌─────────────────────────────────────────────────────────────────────────────┐││
│  │  │ Linux Network Stack                                                         │││
│  │  │ ┌───────────────┐  ┌───────────────┐  ┌───────────────┐                     │││
│  │  │ │ netdev/NAPI   │  │ cfg80211      │  │ mac80211      │ (not used by QCA)   │││
│  │  │ └───────────────┘  └───────────────┘  └───────────────┘                     │││
│  │  └─────────────────────────────────────────────────────────────────────────────┘││
│  │         │                                                                        ││
│  │         ▼                                                                        ││
│  │  ┌─────────────────────────────────────────────────────────────────────────────┐││
│  │  │ OSIF Layer (OS Interface)                                                   │││
│  │  │ - Bridges Linux netdev to WLAN driver                                       │││
│  │  │ - Handles netdev_ops (ndo_start_xmit, etc.)                                 │││
│  │  │ - NAPI registration and polling                                             │││
│  │  └─────────────────────────────────────────────────────────────────────────────┘││
│  │         │                                                                        ││
│  │         ▼                                                                        ││
│  │  ┌─────────────────────────────────────────────────────────────────────────────┐││
│  │  │ Data Path (DP) Layer                                                        │││
│  │  │ ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐          │││
│  │  │ │ dp_rx.c     │  │ dp_tx.c     │  │ dp_peer.c   │  │ dp_main.c   │          │││
│  │  │ │ RX process  │  │ TX process  │  │ Peer mgmt   │  │ Init/deinit │          │││
│  │  │ └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘          │││
│  │  │                                                                              │││
│  │  │ Key structures: dp_soc, dp_pdev, dp_vdev, dp_peer, dp_rx_desc               │││
│  │  └─────────────────────────────────────────────────────────────────────────────┘││
│  │         │                                                                        ││
│  │         ▼                                                                        ││
│  │  ┌─────────────────────────────────────────────────────────────────────────────┐││
│  │  │ Hardware Abstraction Layer (HAL)                                            │││
│  │  │ ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐          │││
│  │  │ │ hal_srng.c  │  │ hal_rx.c    │  │ hal_tx.c    │  │ hal_reo.c   │          │││
│  │  │ │ Ring mgmt   │  │ RX TLVs     │  │ TX descs    │  │ REO config  │          │││
│  │  │ └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘          │││
│  │  │                                                                              │││
│  │  │ Key structures: hal_soc, hal_srng, rx_pkt_tlvs                              │││
│  │  └─────────────────────────────────────────────────────────────────────────────┘││
│  │         │                                                                        ││
│  │         ▼                                                                        ││
│  │  ┌─────────────────────────────────────────────────────────────────────────────┐││
│  │  │ Host Interface (HIF) Layer                                                  │││
│  │  │ ┌─────────────┐  ┌─────────────┐  ┌─────────────┐                           │││
│  │  │ │ hif_pci.c   │  │ hif_ahb.c   │  │ hif_usb.c   │                           │││
│  │  │ │ PCIe bus    │  │ AHB bus     │  │ USB bus     │                           │││
│  │  │ └─────────────┘  └─────────────┘  └─────────────┘                           │││
│  │  │                                                                              │││
│  │  │ Interrupt handling, DMA management, bus abstraction                          │││
│  │  └─────────────────────────────────────────────────────────────────────────────┘││
│  │         │                                                                        ││
│  └─────────────────────────────────────────────────────────────────────────────────┘│
│         │                                                                            │
│         ▼                                                                            │
│  ┌─────────────────────────────────────────────────────────────────────────────────┐│
│  │ Hardware                                                                         ││
│  │ ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐              ││
│  │ │ WiFi SoC    │  │ SRNG Rings  │  │ REO Engine  │  │ Crypto HW   │              ││
│  │ │ (IPQ/QCN)   │  │ (DMA)       │  │ (Reorder)   │  │ (Encrypt)   │              ││
│  │ └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘              ││
│  └─────────────────────────────────────────────────────────────────────────────────┘│
│                                                                                      │
└─────────────────────────────────────────────────────────────────────────────────────┘
```

---

### Linux sk_buff Overview

The `sk_buff` (socket buffer) is the fundamental data structure for network packets in Linux:

```
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                              sk_buff Overview                                        │
├─────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                      │
│  Purpose:                                                                            │
│  - Container for network packet data and metadata                                   │
│  - Used throughout the Linux network stack                                          │
│  - Supports scatter-gather, cloning, and reference counting                         │
│                                                                                      │
│  Key Properties:                                                                     │
│  ┌─────────────────────────────────────────────────────────────────────────────────┐│
│  │ 1. Pointer-based data management (head, data, tail, end)                        ││
│  │ 2. Variable headroom/tailroom for header push/pull                              ││
│  │ 3. 48-byte control block (cb) for layer-private data                            ││
│  │ 4. Reference counted for zero-copy operations                                   ││
│  │ 5. Supports fragmented data (skb_shinfo, frags)                                 ││
│  └─────────────────────────────────────────────────────────────────────────────────┘│
│                                                                                      │
│  Lifecycle:                                                                          │
│  ┌─────────────────────────────────────────────────────────────────────────────────┐│
│  │                                                                                  ││
│  │  Allocation ──► Fill Data ──► Process ──► Deliver/Transmit ──► Free            ││
│  │       │             │             │                │              │              ││
│  │  alloc_skb    skb_put      protocol       netif_receive_skb   kfree_skb        ││
│  │  dev_alloc_skb skb_push    handlers       dev_queue_xmit      consume_skb      ││
│  │               skb_pull                                                           ││
│  │                                                                                  ││
│  └─────────────────────────────────────────────────────────────────────────────────┘│
│                                                                                      │
│  WiFi Driver Usage:                                                                  │
│  ┌─────────────────────────────────────────────────────────────────────────────────┐│
│  │ - RX: Hardware writes to DMA buffer → driver wraps in sk_buff → deliver        ││
│  │ - TX: Stack provides sk_buff → driver maps to DMA → hardware transmits          ││
│  │ - cb[] used to store: peer_id, vdev_id, tid, encryption info, timestamps        ││
│  │ - ar_meta (custom field) caches critical metadata for TX completion             ││
│  └─────────────────────────────────────────────────────────────────────────────────┘│
│                                                                                      │
└─────────────────────────────────────────────────────────────────────────────────────┘
```

---

### eBPF/BTF Background

eBPF (Extended Berkeley Packet Filter) allows running sandboxed programs in the Linux kernel:

```
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                              eBPF/BTF Overview                                       │
├─────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                      │
│  What is eBPF?                                                                       │
│  ┌─────────────────────────────────────────────────────────────────────────────────┐│
│  │ - In-kernel virtual machine for safe, efficient program execution               ││
│  │ - Programs verified before loading (no crashes, no infinite loops)              ││
│  │ - Hook points: XDP, TC, kprobes, tracepoints, socket filters                    ││
│  │ - Use cases: packet filtering, tracing, security, load balancing                ││
│  └─────────────────────────────────────────────────────────────────────────────────┘│
│                                                                                      │
│  What is BTF?                                                                        │
│  ┌─────────────────────────────────────────────────────────────────────────────────┐│
│  │ - Type information format for eBPF programs                                     ││
│  │ - Embedded in vmlinux and kernel modules                                        ││
│  │ - Allows eBPF to access kernel structures by field name                         ││
│  │ - Enables CO-RE (Compile Once, Run Everywhere)                                  ││
│  └─────────────────────────────────────────────────────────────────────────────────┘│
│                                                                                      │
│  Why BTF Offsets Matter:                                                             │
│  ┌─────────────────────────────────────────────────────────────────────────────────┐│
│  │                                                                                  ││
│  │  Problem: sk_buff structure varies between kernel versions                       ││
│  │                                                                                  ││
│  │  Kernel 5.4:                          Kernel 5.15:                               ││
│  │  struct sk_buff {                     struct sk_buff {                           ││
│  │      ...                                  ...                                    ││
│  │      char cb[48];  // offset 0x50         char cb[48];  // offset 0x58           ││
│  │      ...                                  ...                                    ││
│  │  };                                   };                                         ││
│  │                                                                                  ││
│  │  Solution: BTF provides runtime offset resolution                                ││
│  │                                                                                  ││
│  │  eBPF program:                                                                   ││
│  │    peer_id = BPF_CORE_READ(skb, cb, peer_id);  // Works on any kernel           ││
│  │                                                                                  ││
│  │  BTF lookup: sk_buff.cb offset = ? → vmlinux BTF → offset = 0x58                ││
│  │                                                                                  ││
│  └─────────────────────────────────────────────────────────────────────────────────┘│
│                                                                                      │
│  Offset Caching:                                                                     │
│  ┌─────────────────────────────────────────────────────────────────────────────────┐│
│  │ - BTF lookup is expensive (parse vmlinux, search types)                         ││
│  │ - Offsets cached at driver init time                                            ││
│  │ - Cached values used for fast eBPF field access                                 ││
│  │ - Cache invalidated on kernel upgrade                                           ││
│  └─────────────────────────────────────────────────────────────────────────────────┘│
│                                                                                      │
└─────────────────────────────────────────────────────────────────────────────────────┘
```

---

### Custom sk_buff Fields (Kernel Patches)

The WiFi driver adds custom fields to `sk_buff` via kernel patches:

```
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                              Custom sk_buff Fields                                   │
├─────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                      │
│  Patched Fields:                                                                     │
│  ┌─────────────────────────────────────────────────────────────────────────────────┐│
│  │                                                                                  ││
│  │  1. ar_pkt_trace (void *)                                                        ││
│  │     ┌─────────────────────────────────────────────────────────────────────────┐ ││
│  │     │ Purpose: Pointer to packet tracing structure                            │ ││
│  │     │ Size: 8 bytes (64-bit pointer)                                          │ ││
│  │     │ Dependencies: None (simple pointer, no subfield access)                 │ ││
│  │     │ Used for: Packet lifecycle tracing, latency measurement                 │ ││
│  │     └─────────────────────────────────────────────────────────────────────────┘ ││
│  │                                                                                  ││
│  │  2. ar_meta (uint16_t)                                                           ││
│  │     ┌─────────────────────────────────────────────────────────────────────────┐ ││
│  │     │ Purpose: Cached metadata for TX completion                              │ ││
│  │     │ Size: 2 bytes (16 bits)                                                 │ ││
│  │     │ Dependencies: Required (bit-field access for DHCP, EAPOL, TID)          │ ││
│  │     │                                                                          │ ││
│  │     │ Bit Layout:                                                              │ ││
│  │     │ ┌────────────────────────────────────────────────────────────────────┐  │ ││
│  │     │ │ Bits 15-10 │ Bit 9  │ Bit 8  │ Bits 7-0 │                          │  │ ││
│  │     │ │ Reserved   │ DHCP   │ EAPOL  │ TID      │                          │  │ ││
│  │     │ │ (6 bits)   │ (1 bit)│ (1 bit)│ (8 bits) │                          │  │ ││
│  │     │ └────────────────────────────────────────────────────────────────────┘  │ ││
│  │     │                                                                          │ ││
│  │     │ Why needed: skb->cb may have dangling pointers in TX completion         │ ││
│  │     └─────────────────────────────────────────────────────────────────────────┘ ││
│  │                                                                                  ││
│  └─────────────────────────────────────────────────────────────────────────────────┘│
│                                                                                      │
│  Patch Files:                                                                        │
│  ┌─────────────────────────────────────────────────────────────────────────────────┐│
│  │ - ar_skb_meta_cache_12_5.patch: Adds ar_meta field to sk_buff                  ││
│  │ - ar_pkt_trace_12_5.patch: Adds ar_pkt_trace field to sk_buff                  ││
│  │ - Applied to Linux kernel source before build                                   ││
│  └─────────────────────────────────────────────────────────────────────────────────┘│
│                                                                                      │
└─────────────────────────────────────────────────────────────────────────────────────┘
```

---

### Document Organization

This document is organized into the following sections:

| Section | Description |
|---------|-------------|
| **General Information** | Background on driver architecture, eBPF/BTF, glossary |
| **1. Why skb->cb Dependencies** | Explains dangling pointer problem and ar_meta solution |
| **2. Why ar_pkt_trace Has No Dependencies** | Simple pointer field, no subfield access |
| **3. Parameters from Binaries and Caching** | BTF offset resolution and caching |
| **4. Summary Table** | Quick reference for field dependencies |
| **5. How sk_buff is Fetched from Hardware** | Complete RX path (5.1-5.16) |
| **6. TX Path** | How sk_buff is transmitted to hardware |
| **7. Error Handling** | REO errors, RXDMA errors, buffer sanity |
| **8. NAPI and Interrupt Handling** | Interrupt architecture, polling |
| **9. Performance Considerations** | Optimizations, alignment, ring management |
| **10. Complete Packet Lifecycle** | Combined RX/TX summary |

---

## 1. Why `skb->cb` Dependencies for DHCP Values

### The Problem: Dangling Pointers in TX Completion

The `skb->cb` (control block) is a 48-byte region in `struct sk_buff` that different layers of the network stack can use to pass private data. However, when accessing `skb->cb` during TX completion:

1. **Dangling Pointer Risk**: The control block may contain pointers that become invalid (dangling) after the packet is transmitted
2. **Layer Ownership**: Different network layers may have already overwritten `cb` contents
3. **Race Conditions**: In TX completion handlers, the original `cb` data may no longer be valid

### The Solution: Dedicated Metadata Cache (`ar_meta`)

A new 16-bit `ar_meta` field was added directly to `struct sk_buff` to cache packet metadata:

```c
/*
 * ar_meta: 16-bit metadata cache
 * Used to cache TID, EAPOL, DHCP flags without relying on skb->cb
 * which may have dangling pointers in TX completion handler.
 */
__u16 ar_meta;
```

**Layout (16 bits total):**
- **Bits 0-7**: TID value (8 bits)
- **Bit 8**: EAPOL flag (1 bit)
- **Bit 9**: DHCP flag (1 bit)
- **Bits 10-15**: Reserved (6 bits)

### Why Dependencies are Required

When eBPF programs need to access DHCP-related values that were previously stored in `skb->cb`, they must:

1. **Resolve the `ar_meta` offset**: Since `ar_meta` was added via kernel patches, its offset within `sk_buff` varies by kernel version
2. **Depend on parent struct**: To access `ar_meta`, eBPF must first know the base offset of `sk_buff`
3. **Handle nested structures**: The `qdf_nbuf_cb` structure (used for WLAN driver private data) has complex nested unions that require BTF dependency resolution

**Dependency Chain for DHCP values:**
```
sk_buff
  └── ar_meta (offset varies by kernel version)
        └── DHCP flag (bit 9)
```

The dependency ensures that:
- The BTF offset for `ar_meta` is correctly resolved before accessing DHCP flags
- eBPF programs can safely access the cached DHCP status without touching the potentially-invalid `skb->cb`

---

## 2. Why `ar_pkt_trace` Has No Dependencies

### Direct sk_buff Member

The `pkt_trace` field is a simple pointer added directly to `struct sk_buff`:

```c
#ifdef CONFIG_AR_PKT_TRACE_ENABLE
void *pkt_trace;
#endif
```

### No Dependencies Needed Because:

1. **Simple Type**: It's a void pointer, not a nested structure
2. **No Subfield Access**: eBPF programs access the entire pointer, not subfields within it
3. **Conditional Compilation**: The field exists only when `CONFIG_AR_PKT_TRACE_ENABLE` is defined; BTF handles this at compile time
4. **No Semantic Dependencies**: The value doesn't require interpreting other `sk_buff` fields first

### Access Pattern Difference

| Field | Access Pattern | Dependencies |
|-------|---------------|--------------|
| `ar_meta` (DHCP) | Bit-level access to cached flags | Requires offset of parent struct |
| `pkt_trace` | Direct pointer dereference | No dependencies needed |

---

## 3. Parameters Fetched from Binaries and Caching

### BTF Offset Resolution Process

When eBPF programs need kernel structure offsets, the following parameters are fetched from the kernel binary (vmlinux):

#### Fetched Parameters:

| Parameter | Source | Purpose |
|-----------|--------|---------|
| `sk_buff` base offset | vmlinux BTF | Base for all skb field accesses |
| `ar_meta` offset | Patched kernel BTF | Access TID/EAPOL/DHCP cache |
| `pkt_trace` offset | Patched kernel BTF | Packet tracing pointer |
| `cb` offset | vmlinux BTF | Control block access (legacy) |
| `data` offset | vmlinux BTF | Packet data pointer |
| `len` offset | vmlinux BTF | Packet length |

#### Offset Extraction Methods:

1. **Static BTF**: Compiled into vmlinux, available at `/sys/kernel/btf/vmlinux`
2. **Runtime BTF**: Loaded at module insertion time
3. **CO-RE (Compile Once, Run Everywhere)**: BPF programs relocate offsets at load time

### Caching Mechanism

Offsets are cached to avoid repeated BTF lookups:

```
┌─────────────────────────────────────────────────────────┐
│                    Offset Cache                         │
├─────────────────────────────────────────────────────────┤
│  Structure      │  Field       │  Cached Offset        │
├─────────────────┼──────────────┼───────────────────────┤
│  sk_buff        │  ar_meta     │  Resolved at load     │
│  sk_buff        │  pkt_trace   │  Resolved at load     │
│  sk_buff        │  cb          │  Resolved at load     │
│  sk_buff        │  data        │  Resolved at load     │
└─────────────────┴──────────────┴───────────────────────┘
```

**Benefits of Caching:**
- Avoids repeated BTF traversal
- Reduces eBPF program load time
- Enables kernel version portability

---

## 4. Summary

| Field Type | Has Dependencies | Reason |
|------------|-----------------|--------|
| `skb->cb` DHCP values | ✅ Yes | Nested in `qdf_nbuf_cb`, requires `ar_meta` for safe access |
| `ar_meta` cache | ✅ Yes | Patched field, offset varies by kernel |
| `pkt_trace` | ❌ No | Simple pointer, no subfield access |
| `data`, `len` | ❌ No | Standard kernel fields with stable BTF |

The dependency mechanism ensures eBPF programs correctly resolve offsets for patched kernel fields while avoiding unsafe access to potentially stale `skb->cb` data.

---

## 5. How sk_buff is Fetched from Hardware (Detailed Process)

This section explains the complete data path of how packets are received from WiFi hardware and converted into `sk_buff` structures.

### 5.1 Hardware Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                              WiFi Hardware (QCA)                                     │
│                                                                                      │
│  ┌─────────────┐    ┌─────────────────────────────────────────────────────────────┐ │
│  │   RF/PHY    │───▶│                    MAC Hardware                             │ │
│  │             │    │  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐  │ │
│  │ - Antenna   │    │  │ RX Decoder  │  │ Decryption  │  │ Frame Validation    │  │ │
│  │ - ADC/DAC   │    │  │ - OFDM/CCK  │  │ - WEP/TKIP  │  │ - FCS Check         │  │ │
│  │ - Filters   │    │  │ - MIMO      │  │ - CCMP/GCMP │  │ - Address Filter    │  │ │
│  └─────────────┘    │  └──────┬──────┘  └──────┬──────┘  └──────────┬──────────┘  │ │
│                     │         │                │                    │             │ │
│                     │         └────────────────┴────────────────────┘             │ │
│                     └───────────────────────────┬─────────────────────────────────┘ │
│                                                 │                                    │
│  ┌──────────────────────────────────────────────▼──────────────────────────────────┐│
│  │                           RXDMA (Receive DMA Engine)                            ││
│  │  ┌─────────────────────────────────────────────────────────────────────────┐    ││
│  │  │ Functions:                                                               │    ││
│  │  │ - Fetches pre-allocated buffers from SW2RXDMA ring (RXDMA_BUF)          │    ││
│  │  │ - Writes TLV metadata (rx_pkt_tlvs) at buffer start                     │    ││
│  │  │ - Writes packet data after TLVs                                         │    ││
│  │  │ - Posts completion to RXDMA_DST ring (for LMAC rings)                   │    ││
│  │  │ - Handles scatter-gather for large packets (>2KB)                       │    ││
│  │  └─────────────────────────────────────────────────────────────────────────┘    ││
│  └──────────────────────────────────────────────┬──────────────────────────────────┘│
│                                                 │                                    │
│  ┌──────────────────────────────────────────────▼──────────────────────────────────┐│
│  │                        REO (Reorder Engine) - UMAC                              ││
│  │  ┌─────────────────────────────────────────────────────────────────────────┐    ││
│  │  │ Functions:                                                               │    ││
│  │  │ - MPDU reordering based on sequence number                              │    ││
│  │  │ - Block-Ack window management                                           │    ││
│  │  │ - Duplicate detection                                                   │    ││
│  │  │ - PN (Packet Number) validation for replay protection                   │    ││
│  │  │ - Routes packets to appropriate REO destination ring (REO2SW1-8)        │    ││
│  │  │ - Exception handling (REO_EXCEPTION ring for errors)                    │    ││
│  │  └─────────────────────────────────────────────────────────────────────────┘    ││
│  │                                                                                  ││
│  │  REO Destination Ring Selection (based on hash/TID):                            ││
│  │  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐              ││
│  │  │ REO2SW1  │ │ REO2SW2  │ │ REO2SW3  │ │ REO2SW4  │ │ REO2SW5-8│              ││
│  │  │ (Ring 0) │ │ (Ring 1) │ │ (Ring 2) │ │ (Ring 3) │ │ (Ring 4+)│              ││
│  │  └────┬─────┘ └────┬─────┘ └────┬─────┘ └────┬─────┘ └────┬─────┘              ││
│  │       │            │            │            │            │                     ││
│  └───────┼────────────┼────────────┼────────────┼────────────┼─────────────────────┘│
└──────────┼────────────┼────────────┼────────────┼────────────┼──────────────────────┘
           │            │            │            │            │
           │            │            │            │            │  DMA Write to Host
           ▼            ▼            ▼            ▼            ▼
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                              Host Memory (DDR)                                       │
│  ┌─────────────────────────────────────────────────────────────────────────────────┐│
│  │                         SRNG Ring Buffers                                        ││
│  │  - REO Destination Rings (REO_DST): Completed RX packets                        ││
│  │  - RXDMA Buffer Ring (RXDMA_BUF): Pre-allocated empty buffers                   ││
│  │  - WBM Release Ring (WBM2SW_RELEASE): Buffer release notifications              ││
│  │  - REO Exception Ring (REO_EXCEPTION): Error packets                            ││
│  └─────────────────────────────────────────────────────────────────────────────────┘│
│  ┌─────────────────────────────────────────────────────────────────────────────────┐│
│  │                         Packet Data Buffers                                      ││
│  │  - Pre-allocated sk_buff/qdf_nbuf buffers                                       ││
│  │  - TLV metadata + actual packet data                                            ││
│  └─────────────────────────────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────────────────────────────┘
```

#### 5.1.1 Hardware Component Details

| Component | Description | Key Functions |
|-----------|-------------|---------------|
| **RF/PHY** | Radio Frequency and Physical Layer | Signal reception, modulation/demodulation, MIMO processing, channel estimation |
| **MAC HW** | Medium Access Control Hardware | 802.11 frame decoding, decryption, FCS validation, address filtering |
| **RXDMA** | Receive DMA Engine | Buffer management, TLV generation, DMA transfers to host memory |
| **REO** | Reorder Engine | Sequence reordering, BA window, duplicate detection, ring routing |
| **WBM** | Wireless Buffer Manager | Buffer allocation/deallocation, idle buffer management |

#### 5.1.2 Ring Types in RX Path

```c
// From hal_internal.h - Ring type enumeration
enum hal_ring_type {
    REO_DST = 0,           // REO destination rings (REO2SW1-8) - main RX path
    REO_EXCEPTION = 1,     // Exception packets (errors, fragments)
    REO_REINJECT = 2,      // Packets reinjected for reprocessing
    REO_CMD = 3,           // REO command ring (SW to HW commands)
    REO_STATUS = 4,        // REO status ring (HW to SW responses)
    // ... TX rings ...
    RXDMA_BUF = 14,        // SW2RXDMA buffer ring (empty buffers for HW)
    RXDMA_DST = 15,        // RXDMA destination ring (LMAC completions)
    // ... monitor rings ...
};
```

### 5.2 Ring Buffer Architecture (SRNG)

The driver uses **Scatter-Gather Ring (SRNG)** for DMA transfers. SRNG is a circular buffer mechanism that enables efficient zero-copy data transfer between hardware and software.

#### 5.2.1 SRNG Ring Types

There are two fundamental ring types:

| Ring Type | Direction | Producer | Consumer | Example |
|-----------|-----------|----------|----------|---------|
| **Source Ring (SRC)** | SW → HW | Software | Hardware | RXDMA_BUF (empty buffers), TCL_DATA (TX packets) |
| **Destination Ring (DST)** | HW → SW | Hardware | Software | REO_DST (RX completions), WBM2SW_RELEASE |

#### 5.2.2 Ring Structure and Pointers

```
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                         SRNG Ring Memory Layout                                      │
├─────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                      │
│   Head Pointer (HP)                              Tail Pointer (TP)                  │
│        │                                              │                              │
│        ▼                                              ▼                              │
│   ┌─────────┬─────────┬─────────┬─────────┬─────────┬─────────┬─────────┬─────────┐ │
│   │ Entry 0 │ Entry 1 │ Entry 2 │ Entry 3 │ Entry 4 │ Entry 5 │ Entry 6 │ Entry 7 │ │
│   │ (used)  │ (used)  │ (used)  │ (valid) │ (valid) │ (valid) │ (empty) │ (empty) │ │
│   └─────────┴─────────┴─────────┴─────────┴─────────┴─────────┴─────────┴─────────┘ │
│   ◄─────────────────────────────────────────────────────────────────────────────────►│
│                              ring_size (num_entries * entry_size)                    │
│                                                                                      │
│   For Destination Ring (HW → SW):                                                   │
│   - HP: Updated by HW when writing new entries (producer)                           │
│   - TP: Updated by SW after processing entries (consumer)                           │
│   - Valid entries: TP to HP (exclusive)                                             │
│                                                                                      │
│   For Source Ring (SW → HW):                                                        │
│   - HP: Updated by SW when posting new entries (producer)                           │
│   - TP: Updated by HW after consuming entries (consumer)                            │
│   - Valid entries: TP to HP (exclusive)                                             │
│                                                                                      │
└─────────────────────────────────────────────────────────────────────────────────────┘
```

#### 5.2.3 hal_srng Structure (from hal_internal.h)

```c
// Common SRNG ring structure for source and destination rings
struct hal_srng {
    uint8_t ring_id;                    // Unique SRNG ring ID
    uint8_t initialized;                // Ring initialization done
    int irq;                            // Interrupt/MSI value assigned

    qdf_dma_addr_t ring_base_paddr;     // Physical base address of the ring
    uint32_t *ring_base_vaddr;          // Virtual base address of the ring
    uint32_t *ring_vaddr_end;           // Virtual address end

    uint32_t num_entries;               // Number of entries in ring
    uint32_t ring_size;                 // Ring size in bytes
    uint32_t ring_size_mask;            // Ring size mask for wrap-around
    uint32_t entry_size;                // Size of each ring entry (DWORDs)

    uint32_t intr_timer_thres_us;       // Interrupt timer threshold (microseconds)
    uint32_t intr_batch_cntr_thres_entries; // Interrupt batch counter threshold

    uint32_t flags;                     // Ring flags (HAL_SRNG_LMAC_RING, etc.)
    enum hal_srng_dir ring_dir;         // HAL_SRNG_SRC_RING or HAL_SRNG_DST_RING

    union {
        struct {
            uint32_t hp;                // Head pointer (SW maintained)
            uint32_t reap_hp;           // Reap head pointer
            uint32_t *tp_addr;          // Tail pointer address (HW updated)
            uint32_t *hp_addr;          // Head pointer address (for LMAC rings)
            uint32_t low_threshold;     // Low threshold for near-empty IRQ
        } src_ring;                     // Source ring specific fields

        struct {
            uint32_t tp;                // Tail pointer (SW maintained)
            uint32_t *hp_addr;          // Head pointer address (HW updated)
            uint32_t *tp_addr;          // Tail pointer address (for LMAC rings)
            uint32_t cached_hp;         // Cached head pointer value
        } dst_ring;                     // Destination ring specific fields
    } u;

    qdf_spinlock_t lock;                // Ring access lock
};
```

#### 5.2.4 dp_srng Structure (from dp_types.h)

```c
// Data path ring wrapper structure
struct dp_srng {
    hal_ring_handle_t hal_srng;         // HAL SRNG handle
    void *base_vaddr_unaligned;         // Unaligned virtual base address
    void *base_vaddr_aligned;           // Aligned virtual base address
    qdf_dma_addr_t base_paddr_unaligned; // Unaligned physical base address
    qdf_dma_addr_t base_paddr_aligned;  // Aligned physical base address
    uint32_t alloc_size;                // Total allocated size
    uint8_t cached;                     // Whether ring is cached
    int irq;                            // Interrupt number
    uint32_t num_entries;               // Number of ring entries
    struct ring_util_stats stats;       // Ring utilization statistics

#ifdef WLAN_FEATURE_NEAR_FULL_IRQ
    uint16_t crit_thresh;               // Critical threshold for near-full
    uint16_t safe_thresh;               // Safe threshold for near-full
    qdf_atomic_t near_full;             // Near-full flag
#endif
};
```

#### 5.2.5 Ring Entry Structure (REO Destination Ring)

```
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                    REO Destination Ring Entry (reo_destination_ring)                 │
├─────────────────────────────────────────────────────────────────────────────────────┤
│  ┌─────────────────────────────────────────────────────────────────────────────────┐│
│  │ DWORD 0-1: Buffer Address Info                                                  ││
│  │   - buffer_addr_31_0 (32 bits): Lower 32 bits of buffer physical address       ││
│  │   - buffer_addr_39_32 (8 bits): Upper 8 bits of buffer physical address        ││
│  │   - return_buffer_manager (4 bits): Which buffer manager owns this buffer      ││
│  │   - sw_buffer_cookie (21 bits): Cookie for SW descriptor lookup                ││
│  └─────────────────────────────────────────────────────────────────────────────────┘│
│  ┌─────────────────────────────────────────────────────────────────────────────────┐│
│  │ DWORD 2-5: RX MPDU Descriptor Info                                              ││
│  │   - msdu_count: Number of MSDUs in this MPDU                                    ││
│  │   - peer_id: Peer identifier                                                    ││
│  │   - tid: Traffic Identifier                                                     ││
│  │   - fragment_flag: Whether this is a fragment                                   ││
│  │   - push_reason: Why packet was pushed to this ring                             ││
│  │   - error_code: Error code if push_reason indicates error                       ││
│  └─────────────────────────────────────────────────────────────────────────────────┘│
│  ┌─────────────────────────────────────────────────────────────────────────────────┐│
│  │ DWORD 6-7: REO Queue Descriptor Address                                         ││
│  │   - rx_reo_queue_desc_addr: Address of REO queue descriptor                     ││
│  └─────────────────────────────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────────────────────────────┘
```

#### 5.2.6 Ring Access APIs

```c
// Start ring access (acquire lock, sync cached pointers)
void hal_srng_access_start(void *hal_soc, hal_ring_handle_t hal_ring_hdl);

// End ring access (release lock, update HW pointers)
void hal_srng_access_end(void *hal_soc, hal_ring_handle_t hal_ring_hdl);

// Destination ring: Peek at next entry without consuming
void *hal_srng_dst_peek(void *hal_soc, hal_ring_handle_t hal_ring_hdl);

// Destination ring: Get next entry and advance tail pointer
void *hal_srng_dst_get_next(void *hal_soc, hal_ring_handle_t hal_ring_hdl);

// Source ring: Get next free entry for posting
void *hal_srng_src_get_next(void *hal_soc, hal_ring_handle_t hal_ring_hdl);

// Get number of available entries
uint32_t hal_srng_dst_num_valid(void *hal_soc, hal_ring_handle_t hal_ring_hdl);
```

#### 5.2.7 Visual Ring Operation Flow

```
┌────────────────────────────────────────────────────────────────────────────────────┐
│                    SRNG Ring Operation (Destination Ring - RX)                      │
├────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                     │
│  Initial State:                                                                     │
│  ┌─────┬─────┬─────┬─────┬─────┬─────┬─────┬─────┐                                 │
│  │  E  │  E  │  E  │  E  │  E  │  E  │  E  │  E  │  (E = Empty)                    │
│  └─────┴─────┴─────┴─────┴─────┴─────┴─────┴─────┘                                 │
│    ▲                                                                                │
│    HP=TP=0                                                                          │
│                                                                                     │
│  After HW writes 3 packets (HP advances):                                          │
│  ┌─────┬─────┬─────┬─────┬─────┬─────┬─────┬─────┐                                 │
│  │ PKT │ PKT │ PKT │  E  │  E  │  E  │  E  │  E  │  (PKT = Valid packet)           │
│  └─────┴─────┴─────┴─────┴─────┴─────┴─────┴─────┘                                 │
│    ▲               ▲                                                                │
│    TP=0            HP=3                                                             │
│                                                                                     │
│  After SW processes 2 packets (TP advances):                                       │
│  ┌─────┬─────┬─────┬─────┬─────┬─────┬─────┬─────┐                                 │
│  │  P  │  P  │ PKT │  E  │  E  │  E  │  E  │  E  │  (P = Processed/Free)           │
│  └─────┴─────┴─────┴─────┴─────┴─────┴─────┴─────┘                                 │
│            ▲       ▲                                                                │
│            TP=2    HP=3                                                             │
│                                                                                     │
│  Ring wrap-around (circular buffer):                                               │
│  ┌─────┬─────┬─────┬─────┬─────┬─────┬─────┬─────┐                                 │
│  │ PKT │ PKT │  P  │  P  │  P  │  P  │ PKT │ PKT │                                 │
│  └─────┴─────┴─────┴─────┴─────┴─────┴─────┴─────┘                                 │
│            ▲                           ▲                                            │
│            HP=2                        TP=6                                         │
│                                                                                     │
└────────────────────────────────────────────────────────────────────────────────────┘
```

### 5.3 Step-by-Step Process

#### Step 1: Buffer Pre-allocation and Ring Replenishment

This step occurs during initialization (`dp_rx_pdev_buffers_alloc()`) and after processing packets (`dp_rx_buffers_replenish()`).

##### 5.3.1.1 Buffer Allocation Flow

```
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                         Buffer Allocation and Replenishment Flow                     │
├─────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                      │
│  dp_rx_pdev_buffers_alloc() / dp_rx_buffers_replenish()                             │
│         │                                                                            │
│         ▼                                                                            │
│  ┌─────────────────────────────────────────────────────────────────────────────────┐│
│  │ 1. Allocate sk_buff from kernel                                                  ││
│  │    nbuf = qdf_nbuf_alloc(soc->osdev, rx_desc_pool->buf_size,                    ││
│  │                          RX_BUFFER_RESERVATION,                                  ││
│  │                          rx_desc_pool->buf_alignment, FALSE);                    ││
│  │                                                                                  ││
│  │    - buf_size: Typically 2048 bytes (RX_DATA_BUFFER_SIZE)                       ││
│  │    - RX_BUFFER_RESERVATION: Headroom for driver use                             ││
│  │    - buf_alignment: Cache line alignment (typically 128 bytes)                  ││
│  └─────────────────────────────────────────────────────────────────────────────────┘│
│         │                                                                            │
│         ▼                                                                            │
│  ┌─────────────────────────────────────────────────────────────────────────────────┐│
│  │ 2. Map buffer for DMA (get physical address)                                     ││
│  │    ret = qdf_nbuf_map_nbytes_single(soc->osdev, nbuf,                           ││
│  │                                     QDF_DMA_FROM_DEVICE,                         ││
│  │                                     rx_desc_pool->buf_size);                     ││
│  │                                                                                  ││
│  │    - QDF_DMA_FROM_DEVICE: HW will write to this buffer                          ││
│  │    - Creates IOMMU mapping if SMMU is enabled                                   ││
│  │    - Syncs cache (invalidate) for DMA coherency                                 ││
│  └─────────────────────────────────────────────────────────────────────────────────┘│
│         │                                                                            │
│         ▼                                                                            │
│  ┌─────────────────────────────────────────────────────────────────────────────────┐│
│  │ 3. Get physical address and store in nbuf control block                         ││
│  │    paddr = qdf_nbuf_get_frag_paddr(nbuf, 0);                                    ││
│  │    QDF_NBUF_CB_PADDR(nbuf) = paddr;                                             ││
│  └─────────────────────────────────────────────────────────────────────────────────┘│
│         │                                                                            │
│         ▼                                                                            │
│  ┌─────────────────────────────────────────────────────────────────────────────────┐│
│  │ 4. Allocate software descriptor from freelist                                   ││
│  │    rx_desc = dp_rx_desc_alloc(soc, rx_desc_pool);                               ││
│  │    rx_desc->nbuf = nbuf;                                                        ││
│  │    rx_desc->paddr_buf_start = paddr;                                            ││
│  │    rx_desc->in_use = 1;                                                         ││
│  │    rx_desc->unmapped = 0;                                                       ││
│  └─────────────────────────────────────────────────────────────────────────────────┘│
│         │                                                                            │
│         ▼                                                                            │
│  ┌─────────────────────────────────────────────────────────────────────────────────┐│
│  │ 5. Post buffer to RXDMA ring (SW2RXDMA)                                         ││
│  │    hal_srng_access_start(soc->hal_soc, rxdma_srng);                             ││
│  │    rxdma_ring_entry = hal_srng_src_get_next(soc->hal_soc, rxdma_srng);          ││
│  │    hal_rxdma_buff_addr_info_set(rxdma_ring_entry, paddr,                        ││
│  │                                 rx_desc->cookie,                                 ││
│  │                                 rx_desc_pool->owner);                            ││
│  │    hal_srng_access_end(soc->hal_soc, rxdma_srng);                               ││
│  └─────────────────────────────────────────────────────────────────────────────────┘│
│                                                                                      │
└─────────────────────────────────────────────────────────────────────────────────────┘
```

##### 5.3.1.2 Actual Code from dp_rx.c

```c
// From dp_rx.c - __dp_rx_buffers_replenish()
QDF_STATUS __dp_rx_buffers_replenish(struct dp_soc *dp_soc, uint32_t mac_id,
                                     struct dp_srng *dp_rxdma_srng,
                                     struct rx_desc_pool *rx_desc_pool,
                                     uint32_t num_req_buffers,
                                     union dp_rx_desc_list_elem_t **desc_list,
                                     union dp_rx_desc_list_elem_t **tail,
                                     bool req_only, bool force_replenish,
                                     const char *func_name)
{
    // ... initialization ...

    // Allocate required number of nbufs
    for (count = 0; count < num_req_buffers; count++) {
        nbuf = dp_rx_nbuf_alloc(soc, rx_desc_pool);
        if (qdf_unlikely(!nbuf)) {
            DP_STATS_INC(dp_pdev, replenish.nbuf_alloc_fail, 1);
            num_req_buffers = count;
            break;
        }

        // Map and get physical address
        paddr = dp_rx_nbuf_sync_no_dsb(soc, nbuf, rx_desc_pool->buf_size);
        QDF_NBUF_CB_PADDR(nbuf) = paddr;

        // Add to list for batch processing
        DP_RX_LIST_APPEND(nbuf_head, nbuf_tail, nbuf);
    }
    qdf_dsb();  // Data synchronization barrier

    // Post buffers to ring
    nbuf = nbuf_head;
    hal_srng_access_start(soc->hal_soc, rxdma_srng);

    while (nbuf) {
        // Get next ring entry
        rxdma_ring_entry = hal_srng_src_get_next(soc->hal_soc, rxdma_srng);
        if (!rxdma_ring_entry)
            break;

        // Get descriptor from freelist
        next = (*desc_list)->next;
        rx_desc = &(*desc_list)->rx_desc;
        rx_desc->nbuf = nbuf;
        rx_desc->in_use = 1;

        // Set buffer address in ring entry
        hal_rxdma_buff_addr_info_set(rxdma_ring_entry,
                                     QDF_NBUF_CB_PADDR(nbuf),
                                     rx_desc->cookie,
                                     rx_desc_pool->owner);

        nbuf = qdf_nbuf_next(nbuf);
        *desc_list = next;
    }

    hal_srng_access_end(soc->hal_soc, rxdma_srng);
}
```

##### 5.3.1.3 Key Constants and Structures

| Constant/Structure | Value/Description |
|-------------------|-------------------|
| `RX_DATA_BUFFER_SIZE` | 2048 bytes (typical) |
| `RX_BUFFER_RESERVATION` | Headroom bytes reserved |
| `rx_desc_pool->buf_alignment` | 128 bytes (cache line) |
| `rx_desc_pool->owner` | Buffer manager ID (WBM) |
| `rx_desc->cookie` | 21-bit identifier for HW→SW lookup |

#### Step 2: Hardware Receives Packet and Writes to Buffer

When WiFi hardware receives a packet, it goes through multiple processing stages:

##### 5.3.2.1 Detailed Hardware Processing Pipeline

```
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                         Hardware RX Processing Pipeline                              │
├─────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                      │
│  ┌─────────────────────────────────────────────────────────────────────────────────┐│
│  │ Stage 1: RF/PHY Processing                                                       ││
│  │   - Antenna receives RF signal                                                   ││
│  │   - ADC converts to digital samples                                              ││
│  │   - OFDM/CCK demodulation                                                        ││
│  │   - MIMO processing (spatial streams)                                            ││
│  │   - Channel estimation and equalization                                          ││
│  │   - Viterbi/LDPC decoding                                                        ││
│  │   - Output: Raw 802.11 PPDU (Physical Protocol Data Unit)                       ││
│  └─────────────────────────────────────────────────────────────────────────────────┘│
│         │                                                                            │
│         ▼                                                                            │
│  ┌─────────────────────────────────────────────────────────────────────────────────┐│
│  │ Stage 2: MAC Hardware Processing                                                 ││
│  │   - MPDU extraction from A-MPDU                                                  ││
│  │   - FCS (Frame Check Sequence) validation                                        ││
│  │   - Address filtering (BSSID, unicast, multicast)                               ││
│  │   - Decryption (WEP/TKIP/CCMP/GCMP)                                             ││
│  │   - MIC verification (for TKIP)                                                  ││
│  │   - PN (Packet Number) extraction for replay check                              ││
│  │   - Output: Decrypted MPDU with status                                          ││
│  └─────────────────────────────────────────────────────────────────────────────────┘│
│         │                                                                            │
│         ▼                                                                            │
│  ┌─────────────────────────────────────────────────────────────────────────────────┐│
│  │ Stage 3: RXDMA Processing                                                        ││
│  │   - Fetches empty buffer from SW2RXDMA ring (using paddr + cookie)              ││
│  │   - Writes TLV metadata at buffer start:                                         ││
│  │     * rx_attention_tlv: Error flags, encryption info                            ││
│  │     * rx_mpdu_start_tlv: Peer ID, sequence number, TID                          ││
│  │     * rx_msdu_start_tlv: MSDU info, L3/L4 offsets                               ││
│  │     * rx_msdu_end_tlv: MSDU length, checksum status                             ││
│  │     * rx_mpdu_end_tlv: MPDU status                                              ││
│  │     * rx_pkt_hdr_tlv: 802.11 header (optional)                                  ││
│  │   - Writes actual packet data after TLVs                                         ││
│  │   - Posts completion to RXDMA_DST ring (for LMAC) or directly to REO            ││
│  └─────────────────────────────────────────────────────────────────────────────────┘│
│         │                                                                            │
│         ▼                                                                            │
│  ┌─────────────────────────────────────────────────────────────────────────────────┐│
│  │ Stage 4: REO (Reorder Engine) Processing                                         ││
│  │   - Receives MPDU from RXDMA                                                     ││
│  │   - Looks up REO queue descriptor for this TID/peer                             ││
│  │   - Sequence number validation:                                                  ││
│  │     * In-order: Forward immediately                                              ││
│  │     * Out-of-order: Buffer in reorder array                                      ││
│  │     * Duplicate: Drop                                                            ││
│  │     * Old: Drop (outside BA window)                                              ││
│  │   - Block-Ack window management                                                  ││
│  │   - PN validation for replay protection                                          ││
│  │   - Routes to appropriate REO destination ring:                                  ││
│  │     * REO2SW1-8: Normal packets (hash-based distribution)                       ││
│  │     * REO_EXCEPTION: Errors, fragments, special handling                        ││
│  │   - Posts reo_destination_ring entry with buffer info                           ││
│  └─────────────────────────────────────────────────────────────────────────────────┘│
│                                                                                      │
└─────────────────────────────────────────────────────────────────────────────────────┘
```

##### 5.3.2.2 Buffer Layout After HW Write

```
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                    DMA Buffer Layout (pointed by sk_buff->data)                      │
├─────────────────────────────────────────────────────────────────────────────────────┤
│  Offset 0                                                                            │
│  ┌─────────────────────────────────────────────────────────────────────────────────┐│
│  │                    RX Packet TLVs (rx_pkt_tlvs structure)                        ││
│  │  Size: RX_PKT_TLVS_LEN (varies by chip: 256-384 bytes)                          ││
│  │                                                                                  ││
│  │  ┌─────────────────────────────────────────────────────────────────────────────┐││
│  │  │ rx_msdu_end_tlv (72-128 bytes)                                              │││
│  │  │   - msdu_length: Actual MSDU length                                         │││
│  │  │   - l3_header_padding: Padding for L3 alignment                             │││
│  │  │   - tcp_udp_chksum: Hardware checksum result                                │││
│  │  │   - sa_idx / da_idx: Source/Dest address index                              │││
│  │  │   - decap_format: Decapsulation format (Raw/Native WiFi/Ethernet)           │││
│  │  │   - msdu_done: Indicates MSDU processing complete                           │││
│  │  │   - flow_idx: Flow classification index                                     │││
│  │  └─────────────────────────────────────────────────────────────────────────────┘││
│  │  ┌─────────────────────────────────────────────────────────────────────────────┐││
│  │  │ rx_attention_tlv (16 bytes) - if RXDMA_OPTIMIZATION                         │││
│  │  │   - first_mpdu / last_mpdu: MPDU boundary flags                             │││
│  │  │   - fragment_flag: Fragmented MPDU                                          │││
│  │  │   - encrypt_required: Encryption expected                                   │││
│  │  │   - fcs_err: FCS error detected                                             │││
│  │  │   - decrypt_err: Decryption failed                                          │││
│  │  │   - tkip_mic_err: TKIP MIC check failed                                     │││
│  │  └─────────────────────────────────────────────────────────────────────────────┘││
│  │  ┌─────────────────────────────────────────────────────────────────────────────┐││
│  │  │ rx_mpdu_start_tlv (96-120 bytes)                                            │││
│  │  │   - peer_meta_data: Peer ID for lookup                                      │││
│  │  │   - seq_number: 802.11 sequence number                                      │││
│  │  │   - tid: Traffic Identifier (0-7)                                           │││
│  │  │   - encrypt_type: Encryption type (Open/WEP/TKIP/CCMP/GCMP)                 │││
│  │  │   - pn_31_0 / pn_63_32 / pn_95_64 / pn_127_96: Packet Number               │││
│  │  │   - bssid_hit: BSSID matched                                                │││
│  │  │   - ampdu_flag: Part of A-MPDU                                              │││
│  │  └─────────────────────────────────────────────────────────────────────────────┘││
│  │  ┌─────────────────────────────────────────────────────────────────────────────┐││
│  │  │ rx_pkt_hdr_tlv (128 bytes) - Optional, controlled by NO_RX_PKT_HDR_TLV      │││
│  │  │   - rx_pkt_hdr[]: Raw 802.11 header (up to 120 bytes)                       │││
│  │  │   - Used for monitor mode and special processing                            │││
│  │  └─────────────────────────────────────────────────────────────────────────────┘││
│  └─────────────────────────────────────────────────────────────────────────────────┘│
│  Offset RX_PKT_TLVS_LEN                                                              │
│  ┌─────────────────────────────────────────────────────────────────────────────────┐│
│  │                    L2 Header Padding (l3_header_padding bytes)                   ││
│  │  - Ensures L3 header is aligned for efficient CPU access                        ││
│  │  - Typically 0 or 2 bytes                                                       ││
│  └─────────────────────────────────────────────────────────────────────────────────┘│
│  Offset RX_PKT_TLVS_LEN + l3_header_padding                                          │
│  ┌─────────────────────────────────────────────────────────────────────────────────┐│
│  │                    Actual Packet Data                                            ││
│  │  - Ethernet frame (if decap_format = Ethernet II)                               ││
│  │  - 802.11 frame (if decap_format = Raw/Native WiFi)                             ││
│  │  - Length: msdu_length bytes                                                    ││
│  └─────────────────────────────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────────────────────────────┘
```

#### Step 3: Interrupt and Ring Reaping

This step is triggered by hardware interrupts and involves reading completed packets from the REO destination ring.

##### 5.3.3.1 Interrupt to Ring Reaping Flow

```
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                         Interrupt to Ring Reaping Flow                               │
├─────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                      │
│  Hardware Interrupt (MSI/Legacy)                                                     │
│         │                                                                            │
│         ▼                                                                            │
│  ┌─────────────────────────────────────────────────────────────────────────────────┐│
│  │ 1. Interrupt Handler (hif_ahb_interrupt_handler / hif_pci_interrupt_handler)    ││
│  │    - Disable further interrupts for this group                                   ││
│  │    - Schedule NAPI poll                                                          ││
│  │    napi_schedule(&hif_ext_group->napi);                                         ││
│  └─────────────────────────────────────────────────────────────────────────────────┘│
│         │                                                                            │
│         ▼                                                                            │
│  ┌─────────────────────────────────────────────────────────────────────────────────┐│
│  │ 2. NAPI Poll (hif_napi_poll)                                                     ││
│  │    - Called by kernel with budget (typically 64)                                 ││
│  │    - Calls registered callback: dp_service_srngs()                              ││
│  │    work_done = ext_group->napi_cb(ext_group->cb_ctx, budget);                   ││
│  └─────────────────────────────────────────────────────────────────────────────────┘│
│         │                                                                            │
│         ▼                                                                            │
│  ┌─────────────────────────────────────────────────────────────────────────────────┐│
│  │ 3. Ring Service (dp_service_srngs)                                               ││
│  │    - Iterates through all rings in this interrupt group                         ││
│  │    - For each REO destination ring:                                              ││
│  │      work_done += dp_rx_process(int_ctx, hal_ring_hdl, ring_num, remaining);    ││
│  │    - Returns total work done                                                     ││
│  └─────────────────────────────────────────────────────────────────────────────────┘│
│         │                                                                            │
│         ▼                                                                            │
│  ┌─────────────────────────────────────────────────────────────────────────────────┐│
│  │ 4. RX Processing (dp_rx_process)                                                 ││
│  │    - Main packet processing loop                                                 ││
│  │    - Reaps packets from REO ring                                                 ││
│  │    - Processes and delivers to network stack                                     ││
│  └─────────────────────────────────────────────────────────────────────────────────┘│
│                                                                                      │
└─────────────────────────────────────────────────────────────────────────────────────┘
```

##### 5.3.3.2 Ring Reaping Process Detail

```c
// dp_rx_process() - Main RX processing function
uint32_t dp_rx_process(struct dp_intr *int_ctx,
                       hal_ring_handle_t hal_ring_hdl,
                       uint8_t reo_ring_num, uint32_t quota)
{
    struct dp_soc *soc = int_ctx->soc;
    hal_soc_handle_t hal_soc = soc->hal_soc;
    void *ring_desc;
    uint32_t rx_bufs_reaped = 0;

    // Start ring access (acquire lock, sync cached pointers)
    if (qdf_unlikely(hal_srng_access_start(hal_soc, hal_ring_hdl))) {
        // Ring access failed
        return 0;
    }

    // Main reaping loop
    while (quota && (ring_desc = hal_srng_dst_peek(hal_soc, hal_ring_hdl))) {

        // ┌─────────────────────────────────────────────────────────────────┐
        // │ Step 3a: Extract buffer info from ring descriptor               │
        // └─────────────────────────────────────────────────────────────────┘

        // Get buffer physical address (for validation)
        buf_paddr = HAL_RX_REO_BUFFER_ADDR_31_0_GET(ring_desc) |
                    ((uint64_t)HAL_RX_REO_BUFFER_ADDR_39_32_GET(ring_desc) << 32);

        // Get cookie for SW descriptor lookup
        rx_buf_cookie = HAL_RX_REO_BUF_COOKIE_GET(ring_desc);

        // Get push reason (normal, error, etc.)
        push_reason = HAL_RX_REO_PUSH_REASON_GET(ring_desc);

        // ┌─────────────────────────────────────────────────────────────────┐
        // │ Step 3b: Cookie to Virtual Address lookup                       │
        // └─────────────────────────────────────────────────────────────────┘

        // Extract pool_id and index from cookie
        pool_id = DP_RX_DESC_COOKIE_POOL_ID_GET(rx_buf_cookie);

        // Get software descriptor
        rx_desc = dp_rx_cookie_2_va_rxdma_buf(soc, rx_buf_cookie);
        if (qdf_unlikely(!rx_desc)) {
            // Invalid cookie - skip this entry
            hal_srng_dst_get_next(hal_soc, hal_ring_hdl);
            continue;
        }

        // ┌─────────────────────────────────────────────────────────────────┐
        // │ Step 3c: Validate and get sk_buff                               │
        // └─────────────────────────────────────────────────────────────────┘

        // Sanity check: verify physical address matches
        if (qdf_unlikely(rx_desc->paddr_buf_start != buf_paddr)) {
            // Address mismatch - corruption detected
            DP_STATS_INC(soc, rx.err.paddr_mismatch, 1);
            hal_srng_dst_get_next(hal_soc, hal_ring_hdl);
            continue;
        }

        // Get the sk_buff (qdf_nbuf)
        nbuf = rx_desc->nbuf;

        // ┌─────────────────────────────────────────────────────────────────┐
        // │ Step 3d: Unmap DMA and sync cache                               │
        // └─────────────────────────────────────────────────────────────────┘

        // Unmap DMA - invalidates CPU cache, makes data visible to CPU
        qdf_nbuf_unmap_nbytes_single(soc->osdev, nbuf,
                                     QDF_DMA_FROM_DEVICE,
                                     rx_desc_pool->buf_size);
        rx_desc->unmapped = 1;

        // ┌─────────────────────────────────────────────────────────────────┐
        // │ Step 3e: Prefetch for performance                               │
        // └─────────────────────────────────────────────────────────────────┘

        // Prefetch TLV data for faster processing
        qdf_prefetch(qdf_nbuf_data(nbuf));

        // Prefetch next ring descriptor
        qdf_prefetch(hal_srng_dst_peek_next(hal_soc, hal_ring_hdl));

        // ┌─────────────────────────────────────────────────────────────────┐
        // │ Step 3f: Add to processing list and advance ring                │
        // └─────────────────────────────────────────────────────────────────┘

        // Chain nbuf to processing list
        DP_RX_LIST_APPEND(nbuf_head, nbuf_tail, nbuf);

        // Pop descriptor from ring (advance tail pointer)
        hal_srng_dst_get_next(hal_soc, hal_ring_hdl);

        rx_bufs_reaped++;
        quota--;
    }

    // End ring access (release lock, update HW tail pointer)
    hal_srng_access_end(hal_soc, hal_ring_hdl);

    // Return descriptors to freelist for replenishment
    dp_rx_add_to_free_desc_list(&head, &tail, rx_desc);

    return rx_bufs_reaped;
}
```

##### 5.3.3.3 HAL Ring Access Macros

| Macro | Description |
|-------|-------------|
| `HAL_RX_REO_BUF_COOKIE_GET(ring_desc)` | Extract 21-bit cookie from ring entry |
| `HAL_RX_REO_BUFFER_ADDR_31_0_GET(ring_desc)` | Get lower 32 bits of buffer paddr |
| `HAL_RX_REO_BUFFER_ADDR_39_32_GET(ring_desc)` | Get upper 8 bits of buffer paddr |
| `HAL_RX_REO_PUSH_REASON_GET(ring_desc)` | Get push reason (0=normal, 1=error) |
| `HAL_RX_REO_ERROR_CODE_GET(ring_desc)` | Get error code if push_reason=error |
| `hal_srng_dst_peek()` | Peek at next entry without consuming |
| `hal_srng_dst_get_next()` | Get next entry and advance tail |

#### Step 4: TLV Parsing and Metadata Extraction

After reaping the buffer from the ring, the driver parses the TLV metadata written by hardware.

##### 5.3.4.1 TLV Parsing Flow

```
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                         TLV Parsing and Metadata Extraction                          │
├─────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                      │
│  nbuf->data points to start of DMA buffer                                           │
│         │                                                                            │
│         ▼                                                                            │
│  ┌─────────────────────────────────────────────────────────────────────────────────┐│
│  │ rx_tlv_hdr = qdf_nbuf_data(nbuf);  // Points to rx_pkt_tlvs structure           ││
│  └─────────────────────────────────────────────────────────────────────────────────┘│
│         │                                                                            │
│         ▼                                                                            │
│  ┌─────────────────────────────────────────────────────────────────────────────────┐│
│  │ Parse rx_msdu_end_tlv:                                                           ││
│  │   msdu_len = HAL_RX_MSDU_END_MSDU_LEN_GET(rx_tlv_hdr);                           ││
│  │   l3_hdr_pad = HAL_RX_MSDU_END_L3_HDR_PADDING_GET(rx_tlv_hdr);                   ││
│  │   decap_format = HAL_RX_MSDU_END_DECAP_FORMAT_GET(rx_tlv_hdr);                   ││
│  │   msdu_done = HAL_RX_TLV_MSDU_DONE_GET(rx_tlv_hdr);                              ││
│  │   tcp_udp_chksum = HAL_RX_MSDU_END_TCP_UDP_CHKSUM_GET(rx_tlv_hdr);               ││
│  │   sa_idx = HAL_RX_MSDU_END_SA_IDX_GET(rx_tlv_hdr);                               ││
│  │   da_idx = HAL_RX_MSDU_END_DA_IDX_GET(rx_tlv_hdr);                               ││
│  │   flow_idx = HAL_RX_MSDU_END_FLOW_IDX_GET(rx_tlv_hdr);                           ││
│  └─────────────────────────────────────────────────────────────────────────────────┘│
│         │                                                                            │
│         ▼                                                                            │
│  ┌─────────────────────────────────────────────────────────────────────────────────┐│
│  │ Parse rx_mpdu_start_tlv:                                                         ││
│  │   peer_id = HAL_RX_MPDU_PEER_META_DATA_GET(rx_tlv_hdr);                          ││
│  │   seq_num = HAL_RX_MPDU_SEQUENCE_NUMBER_GET(rx_tlv_hdr);                         ││
│  │   tid = HAL_RX_MPDU_TID_GET(rx_tlv_hdr);                                         ││
│  │   encrypt_type = HAL_RX_MPDU_ENCRYPT_TYPE_GET(rx_tlv_hdr);                       ││
│  │   pn = HAL_RX_MPDU_PN_GET(rx_tlv_hdr);  // 48-bit or 128-bit                     ││
│  │   ampdu_flag = HAL_RX_MPDU_AMPDU_FLAG_GET(rx_tlv_hdr);                           ││
│  │   bssid_hit = HAL_RX_MPDU_BSSID_HIT_GET(rx_tlv_hdr);                             ││
│  └─────────────────────────────────────────────────────────────────────────────────┘│
│         │                                                                            │
│         ▼                                                                            │
│  ┌─────────────────────────────────────────────────────────────────────────────────┐│
│  │ Parse rx_attention_tlv (error/status flags):                                     ││
│  │   fcs_err = HAL_RX_ATTN_FCS_ERR_GET(rx_tlv_hdr);                                 ││
│  │   decrypt_err = HAL_RX_ATTN_DECRYPT_ERR_GET(rx_tlv_hdr);                         ││
│  │   tkip_mic_err = HAL_RX_ATTN_TKIP_MIC_ERR_GET(rx_tlv_hdr);                       ││
│  │   fragment_flag = HAL_RX_ATTN_FRAGMENT_FLAG_GET(rx_tlv_hdr);                     ││
│  │   first_mpdu = HAL_RX_ATTN_FIRST_MPDU_GET(rx_tlv_hdr);                           ││
│  │   last_mpdu = HAL_RX_ATTN_LAST_MPDU_GET(rx_tlv_hdr);                             ││
│  └─────────────────────────────────────────────────────────────────────────────────┘│
│         │                                                                            │
│         ▼                                                                            │
│  ┌─────────────────────────────────────────────────────────────────────────────────┐│
│  │ Store metadata in sk_buff control block (cb):                                    ││
│  │   QDF_NBUF_CB_RX_PEER_ID(nbuf) = peer_id;                                        ││
│  │   QDF_NBUF_CB_RX_VDEV_ID(nbuf) = vdev_id;                                        ││
│  │   QDF_NBUF_CB_RX_TID_VAL(nbuf) = tid;                                            ││
│  │   QDF_NBUF_CB_RX_PKT_LEN(nbuf) = msdu_len;                                       ││
│  │   QDF_NBUF_CB_RX_TCP_CHKSUM(nbuf) = tcp_udp_chksum;                              ││
│  │   QDF_NBUF_CB_RX_FLOW_ID(nbuf) = flow_idx;                                       ││
│  └─────────────────────────────────────────────────────────────────────────────────┘│
│                                                                                      │
└─────────────────────────────────────────────────────────────────────────────────────┘
```

##### 5.3.4.2 HAL_RX Macro Implementation

```c
// Example HAL_RX macros from hal_be_rx_tlv.h

// Get MSDU length from msdu_end TLV
#define HAL_RX_MSDU_END_MSDU_LEN_GET(rx_tlv) \
    (HAL_RX_MSDU_END(rx_tlv).msdu_length)

// Get peer ID from mpdu_start TLV
#define HAL_RX_MPDU_PEER_META_DATA_GET(rx_tlv) \
    (HAL_RX_MPDU_START(rx_tlv).peer_meta_data)

// Get L3 header padding
#define HAL_RX_MSDU_END_L3_HDR_PADDING_GET(rx_tlv) \
    (HAL_RX_MSDU_END(rx_tlv).l3_header_padding)

// Get decapsulation format
#define HAL_RX_MSDU_END_DECAP_FORMAT_GET(rx_tlv) \
    (HAL_RX_MSDU_END(rx_tlv).decap_format)

// Check if MSDU processing is done
#define HAL_RX_TLV_MSDU_DONE_GET(rx_tlv) \
    (HAL_RX_MSDU_END(rx_tlv).msdu_done)

// Helper macros to access TLV structures
#define HAL_RX_MSDU_END(rx_tlv) \
    (((struct rx_pkt_tlvs *)(rx_tlv))->msdu_end_tlv.rx_msdu_end)

#define HAL_RX_MPDU_START(rx_tlv) \
    (((struct rx_pkt_tlvs *)(rx_tlv))->mpdu_start_tlv.rx_mpdu_start)
```

##### 5.3.4.3 MSDU Done Check

```c
// Critical validation: Ensure hardware has finished writing
if (qdf_unlikely(!HAL_RX_TLV_MSDU_DONE_GET(rx_tlv_hdr))) {
    // Hardware hasn't finished writing - this is a serious error
    // Can happen due to:
    // 1. DMA not complete
    // 2. Ring corruption
    // 3. Hardware bug

    DP_STATS_INC(soc, rx.err.msdu_done_fail, 1);
    rx_desc->msdu_done_fail = 1;

    // Drop this packet
    qdf_nbuf_free(nbuf);
    continue;
}
```

#### Step 5: sk_buff Preparation for Network Stack

After parsing TLVs, the sk_buff must be prepared for delivery to the Linux network stack.

##### 5.3.5.1 Buffer Adjustment Flow

```
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                         sk_buff Preparation for Network Stack                        │
├─────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                      │
│  Before Adjustment:                                                                  │
│  ┌─────────────────────────────────────────────────────────────────────────────────┐│
│  │ nbuf->data ──►┌──────────────────────────────────────────────────────────────┐  ││
│  │               │ rx_pkt_tlvs (RX_PKT_TLVS_LEN bytes)                          │  ││
│  │               ├──────────────────────────────────────────────────────────────┤  ││
│  │               │ L3 padding (l3_header_padding bytes, typically 0-2)          │  ││
│  │               ├──────────────────────────────────────────────────────────────┤  ││
│  │               │ Ethernet Header (14 bytes)                                   │  ││
│  │               ├──────────────────────────────────────────────────────────────┤  ││
│  │               │ IP Header + Payload (msdu_len - 14 bytes)                    │  ││
│  │               └──────────────────────────────────────────────────────────────┘  ││
│  │ nbuf->len = buf_size (2048 bytes, includes unused space)                        ││
│  └─────────────────────────────────────────────────────────────────────────────────┘│
│         │                                                                            │
│         ▼                                                                            │
│  ┌─────────────────────────────────────────────────────────────────────────────────┐│
│  │ Step 5a: Set correct packet length                                              ││
│  │   pkt_len = msdu_len + l3_header_padding + RX_PKT_TLVS_LEN;                     ││
│  │   qdf_nbuf_set_pktlen(nbuf, pkt_len);                                           ││
│  │                                                                                  ││
│  │   // Now nbuf->len = actual packet length (not full buffer)                     ││
│  └─────────────────────────────────────────────────────────────────────────────────┘│
│         │                                                                            │
│         ▼                                                                            │
│  ┌─────────────────────────────────────────────────────────────────────────────────┐│
│  │ Step 5b: Remove TLV header (pull head)                                          ││
│  │   pull_len = RX_PKT_TLVS_LEN + l3_header_padding;                               ││
│  │   qdf_nbuf_pull_head(nbuf, pull_len);                                           ││
│  │                                                                                  ││
│  │   // Advances nbuf->data pointer, decreases nbuf->len                           ││
│  └─────────────────────────────────────────────────────────────────────────────────┘│
│         │                                                                            │
│         ▼                                                                            │
│  After Adjustment:                                                                   │
│  ┌─────────────────────────────────────────────────────────────────────────────────┐│
│  │               ┌──────────────────────────────────────────────────────────────┐  ││
│  │               │ rx_pkt_tlvs (skipped, headroom)                              │  ││
│  │               ├──────────────────────────────────────────────────────────────┤  ││
│  │               │ L3 padding (skipped, headroom)                               │  ││
│  │ nbuf->data ──►├──────────────────────────────────────────────────────────────┤  ││
│  │               │ Ethernet Header (14 bytes)                                   │  ││
│  │               ├──────────────────────────────────────────────────────────────┤  ││
│  │               │ IP Header + Payload                                          │  ││
│  │               └──────────────────────────────────────────────────────────────┘  ││
│  │ nbuf->len = msdu_len (actual Ethernet frame length)                             ││
│  └─────────────────────────────────────────────────────────────────────────────────┘│
│                                                                                      │
└─────────────────────────────────────────────────────────────────────────────────────┘
```

##### 5.3.5.2 Protocol and Device Setup

```c
// Set protocol type for network stack
nbuf->protocol = eth_type_trans(nbuf, netdev);

// Set device pointer
nbuf->dev = netdev;

// Set checksum offload status (if hardware verified checksum)
if (rx_tlv_hdr->tcp_udp_chksum_valid) {
    nbuf->ip_summed = CHECKSUM_UNNECESSARY;
} else {
    nbuf->ip_summed = CHECKSUM_NONE;
}

// Set priority from TID
nbuf->priority = tid_to_priority[tid];
```

##### 5.3.5.3 Delivery to Network Stack

```c
// Option 1: Direct delivery (single packet)
netif_receive_skb(nbuf);

// Option 2: NAPI GRO (Generic Receive Offload) - preferred for performance
napi_gro_receive(&napi, nbuf);

// Option 3: Batch delivery via OSIF callback
// This is the typical path in QCA drivers
vdev->osif_rx(vdev->osif_vdev, nbuf);

// Inside osif_rx callback (dp_rx_deliver_to_stack):
void dp_rx_deliver_to_stack(struct dp_soc *soc,
                            struct dp_vdev *vdev,
                            struct dp_peer *peer,
                            qdf_nbuf_t nbuf_head,
                            qdf_nbuf_t nbuf_tail)
{
    qdf_nbuf_t nbuf, next;

    nbuf = nbuf_head;
    while (nbuf) {
        next = qdf_nbuf_next(nbuf);
        qdf_nbuf_set_next(nbuf, NULL);

        // Set device and protocol
        qdf_nbuf_set_dev(nbuf, osif_vdev->netdev);
        nbuf->protocol = eth_type_trans(nbuf, osif_vdev->netdev);

        // Deliver to kernel
        napi_gro_receive(&osif_vdev->napi, nbuf);

        nbuf = next;
    }
}
```

### 5.4 Cookie-Based Buffer Lookup

The **cookie** mechanism enables fast O(1) lookup from hardware descriptor to software state. This is critical because hardware only knows physical addresses and cookies, while software needs to access the sk_buff and associated metadata.

#### 5.4.1 Cookie Structure and Encoding

```
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                         Cookie Structure (21 bits)                                   │
├─────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                      │
│  Bit Layout:                                                                         │
│  ┌─────────────────────────────────────────────────────────────────────────────────┐│
│  │ Bit 20                                                              Bit 0       ││
│  │ ┌────────────────────────────────────────────────────────┬──────────────────┐   ││
│  │ │              Index (18 bits)                           │  Pool ID (3 bits)│   ││
│  │ │              Bits 20:3                                 │  Bits 2:0        │   ││
│  │ │              Range: 0 - 262143                         │  Range: 0 - 7    │   ││
│  │ └────────────────────────────────────────────────────────┴──────────────────┘   ││
│  └─────────────────────────────────────────────────────────────────────────────────┘│
│                                                                                      │
│  Pool ID identifies which rx_desc_pool to use (supports multiple pools)             │
│  Index identifies which descriptor within that pool                                 │
│                                                                                      │
└─────────────────────────────────────────────────────────────────────────────────────┘
```

#### 5.4.2 Cookie Encoding/Decoding Macros

```c
// From dp_rx.h - Cookie manipulation macros

// Cookie bit field definitions
#define DP_RX_DESC_COOKIE_POOL_ID_SHIFT     0
#define DP_RX_DESC_COOKIE_POOL_ID_MASK      0x7     // 3 bits
#define DP_RX_DESC_COOKIE_INDEX_SHIFT       3
#define DP_RX_DESC_COOKIE_INDEX_MASK        0x3FFFF // 18 bits

// Extract pool_id from cookie
#define DP_RX_DESC_COOKIE_POOL_ID_GET(cookie) \
    (((cookie) >> DP_RX_DESC_COOKIE_POOL_ID_SHIFT) & DP_RX_DESC_COOKIE_POOL_ID_MASK)

// Extract index from cookie
#define DP_RX_DESC_COOKIE_INDEX_GET(cookie) \
    (((cookie) >> DP_RX_DESC_COOKIE_INDEX_SHIFT) & DP_RX_DESC_COOKIE_INDEX_MASK)

// Create cookie from pool_id and index
#define DP_RX_DESC_COOKIE_SET(pool_id, index) \
    (((pool_id) << DP_RX_DESC_COOKIE_POOL_ID_SHIFT) | \
     ((index) << DP_RX_DESC_COOKIE_INDEX_SHIFT))
```

#### 5.4.3 Cookie to Virtual Address Lookup

```c
// From dp_rx.h - dp_rx_cookie_2_va_rxdma_buf()
// This is the critical function that converts hardware cookie to software descriptor

static inline struct dp_rx_desc *
dp_rx_cookie_2_va_rxdma_buf(struct dp_soc *soc, uint32_t cookie)
{
    uint8_t pool_id;
    uint16_t index;
    struct rx_desc_pool *rx_desc_pool;

    // Extract pool_id and index from cookie
    pool_id = DP_RX_DESC_COOKIE_POOL_ID_GET(cookie);
    index = DP_RX_DESC_COOKIE_INDEX_GET(cookie);

    // Validate pool_id
    if (qdf_unlikely(pool_id >= MAX_RXDESC_POOLS)) {
        dp_rx_err("Invalid pool_id %d", pool_id);
        return NULL;
    }

    // Get the descriptor pool
    rx_desc_pool = &soc->rx_desc_buf[pool_id];

    // Validate index
    if (qdf_unlikely(index >= rx_desc_pool->pool_size)) {
        dp_rx_err("Invalid index %d, pool_size %d", index, rx_desc_pool->pool_size);
        return NULL;
    }

    // Direct array access - O(1) lookup
    return &rx_desc_pool->array[index].rx_desc;
}
```

#### 5.4.4 Lookup Flow Diagram

```
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                         Cookie to sk_buff Lookup Flow                                │
├─────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                      │
│  REO Ring Entry                                                                      │
│  ┌─────────────────────────────────────────────────────────────────────────────────┐│
│  │ buffer_addr_39_0 | return_buffer_manager | sw_buffer_cookie (21 bits)           ││
│  └─────────────────────────────────────────────────────────────────────────────────┘│
│         │                                                                            │
│         │ HAL_RX_REO_BUF_COOKIE_GET(ring_desc)                                      │
│         ▼                                                                            │
│  ┌─────────────────────────────────────────────────────────────────────────────────┐│
│  │ cookie = 0x1A3F5  (example: pool_id=5, index=0x347E)                            ││
│  └─────────────────────────────────────────────────────────────────────────────────┘│
│         │                                                                            │
│         │ DP_RX_DESC_COOKIE_POOL_ID_GET(cookie) → pool_id = 5                       │
│         │ DP_RX_DESC_COOKIE_INDEX_GET(cookie)   → index = 0x347E                    │
│         ▼                                                                            │
│  ┌─────────────────────────────────────────────────────────────────────────────────┐│
│  │ soc->rx_desc_buf[5]  (rx_desc_pool for pool_id 5)                               ││
│  │     │                                                                            ││
│  │     └──► array[0x347E]  (direct array access)                                   ││
│  │              │                                                                   ││
│  │              └──► rx_desc                                                        ││
│  │                      │                                                           ││
│  │                      ├── nbuf ──────────────► sk_buff (packet data)             ││
│  │                      ├── paddr_buf_start ──► physical address                   ││
│  │                      ├── cookie ───────────► 0x1A3F5 (for validation)           ││
│  │                      ├── pool_id ──────────► 5                                  ││
│  │                      ├── in_use ───────────► 1 (currently in use)               ││
│  │                      └── unmapped ─────────► 0 (still DMA mapped)               ││
│  └─────────────────────────────────────────────────────────────────────────────────┘│
│                                                                                      │
└─────────────────────────────────────────────────────────────────────────────────────┘
```

#### 5.4.5 Why Cookie-Based Lookup?

| Aspect | Explanation |
|--------|-------------|
| **O(1) Performance** | Direct array indexing, no searching or hashing |
| **Hardware Simplicity** | HW only needs to store 21-bit cookie, not full pointer |
| **Memory Efficiency** | Cookie fits in ring entry alongside buffer address |
| **Multi-Pool Support** | Pool ID allows multiple descriptor pools (per-MAC, per-ring) |
| **Validation** | Pool ID and index bounds checking prevents corruption |

### 5.5 Buffer Pool Management

Buffer pool management is critical for efficient RX processing. The driver pre-allocates a pool of descriptors and sk_buffs to avoid allocation overhead in the hot path.

#### 5.5.1 Pool Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                         RX Buffer Pool Architecture                                 │
├─────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                      │
│  soc->rx_desc_buf[MAX_RXDESC_POOLS]                                                 │
│  ┌─────────────────────────────────────────────────────────────────────────────────┐│
│  │ Pool 0 (MAC 0, RXDMA)                                                           ││
│  │ ┌─────────────────────────────────────────────────────────────────────────────┐ ││
│  │ │ array ──► [desc_0][desc_1][desc_2]...[desc_N-1]  (contiguous memory)        │ ││
│  │ │ freelist_head ──► desc_5 ──► desc_12 ──► desc_3 ──► NULL (free descriptors) │ ││
│  │ │ pool_size = N                                                                │ ││
│  │ │ buf_size = 2048                                                              │ ││
│  │ │ buf_alignment = 128                                                          │ ││
│  │ │ lock (spinlock for freelist)                                                 │ ││
│  │ └─────────────────────────────────────────────────────────────────────────────┘ ││
│  ├─────────────────────────────────────────────────────────────────────────────────┤│
│  │ Pool 1 (MAC 1, RXDMA)                                                           ││
│  │ ┌─────────────────────────────────────────────────────────────────────────────┐ ││
│  │ │ array ──► [desc_0][desc_1][desc_2]...[desc_M-1]                             │ ││
│  │ │ freelist_head ──► ...                                                        │ ││
│  │ └─────────────────────────────────────────────────────────────────────────────┘ ││
│  ├─────────────────────────────────────────────────────────────────────────────────┤│
│  │ Pool 2 (MAC 2, RXDMA)                                                           ││
│  │ └─────────────────────────────────────────────────────────────────────────────┘ ││
│  └─────────────────────────────────────────────────────────────────────────────────┘│
│                                                                                      │
└─────────────────────────────────────────────────────────────────────────────────────┘
```

#### 5.5.2 rx_desc_pool Structure

```c
// From dp_types.h - RX descriptor pool structure
struct rx_desc_pool {
    // Contiguous array of descriptors (for O(1) cookie lookup)
    union dp_rx_desc_list_elem_t *array;

    // Freelist head (linked list of available descriptors)
    union dp_rx_desc_list_elem_t *freelist;

    // Freelist tail (for efficient append)
    union dp_rx_desc_list_elem_t *freelist_tail;

    // Lock for freelist operations
    qdf_spinlock_t lock;

    // Pool configuration
    uint32_t pool_size;         // Total number of descriptors
    uint16_t buf_size;          // Size of each buffer (typically 2048)
    uint8_t  buf_alignment;     // Alignment requirement (typically 128)
    uint8_t  pool_id;           // Pool identifier (0-7)

    // Owner information
    uint8_t  owner;             // HAL_RX_BUF_RBM_SW0_BM, etc.

    // Statistics
    uint32_t num_allocated;     // Currently allocated descriptors
    uint32_t num_free;          // Currently free descriptors
};
```

#### 5.5.3 dp_rx_desc Structure

```c
// From dp_rx.h - Individual RX descriptor
struct dp_rx_desc {
    // sk_buff pointer - the actual network buffer
    qdf_nbuf_t nbuf;

    // Physical address of buffer start (for DMA)
    qdf_dma_addr_t paddr_buf_start;

    // Cookie for HW→SW lookup
    uint32_t cookie;

    // Pool this descriptor belongs to
    uint8_t pool_id;

    // Status flags
    uint8_t in_use:1;           // 1 = in use by HW, 0 = free
    uint8_t unmapped:1;         // 1 = DMA unmapped, 0 = still mapped
    uint8_t msdu_done_fail:1;   // 1 = MSDU done check failed
    uint8_t in_err_state:1;     // 1 = error state

    // For freelist linking
    struct dp_rx_desc *next;
};

// Union for array/freelist dual use
union dp_rx_desc_list_elem_t {
    struct dp_rx_desc rx_desc;
    union dp_rx_desc_list_elem_t *next;
};
```

#### 5.5.4 Pool Initialization

```c
// dp_rx_pdev_desc_pool_alloc() - Allocate descriptor pool
QDF_STATUS dp_rx_pdev_desc_pool_alloc(struct dp_pdev *pdev)
{
    struct dp_soc *soc = pdev->soc;
    uint32_t pool_id = pdev->lmac_id;
    struct rx_desc_pool *rx_desc_pool = &soc->rx_desc_buf[pool_id];
    uint32_t num_entries;

    // Calculate pool size based on ring size
    num_entries = wlan_cfg_get_dp_soc_rxdma_refill_ring_size(soc->wlan_cfg_ctx);

    // Allocate contiguous array of descriptors
    rx_desc_pool->array = qdf_mem_malloc(
        num_entries * sizeof(union dp_rx_desc_list_elem_t));

    if (!rx_desc_pool->array)
        return QDF_STATUS_E_NOMEM;

    // Initialize pool metadata
    rx_desc_pool->pool_size = num_entries;
    rx_desc_pool->pool_id = pool_id;
    rx_desc_pool->buf_size = RX_DATA_BUFFER_SIZE;  // 2048
    rx_desc_pool->buf_alignment = RX_DATA_BUFFER_ALIGNMENT;  // 128
    rx_desc_pool->owner = HAL_RX_BUF_RBM_SW0_BM + pool_id;

    // Initialize spinlock
    qdf_spinlock_create(&rx_desc_pool->lock);

    // Build freelist - link all descriptors
    dp_rx_desc_pool_init(soc, pool_id, num_entries, rx_desc_pool);

    return QDF_STATUS_SUCCESS;
}

// dp_rx_desc_pool_init() - Initialize freelist
void dp_rx_desc_pool_init(struct dp_soc *soc, uint32_t pool_id,
                          uint32_t num_entries, struct rx_desc_pool *rx_desc_pool)
{
    uint32_t i;
    union dp_rx_desc_list_elem_t *desc;

    // Initialize each descriptor and link to freelist
    for (i = 0; i < num_entries; i++) {
        desc = &rx_desc_pool->array[i];

        // Set cookie (pool_id + index)
        desc->rx_desc.cookie = DP_RX_DESC_COOKIE_SET(pool_id, i);
        desc->rx_desc.pool_id = pool_id;
        desc->rx_desc.in_use = 0;
        desc->rx_desc.nbuf = NULL;

        // Link to freelist
        if (i < num_entries - 1) {
            desc->next = &rx_desc_pool->array[i + 1];
        } else {
            desc->next = NULL;  // Last entry
        }
    }

    // Set freelist head and tail
    rx_desc_pool->freelist = &rx_desc_pool->array[0];
    rx_desc_pool->freelist_tail = &rx_desc_pool->array[num_entries - 1];
    rx_desc_pool->num_free = num_entries;
    rx_desc_pool->num_allocated = 0;
}
```

#### 5.5.5 Descriptor Allocation and Free

```c
// Allocate descriptor from freelist (called during buffer replenish)
static inline struct dp_rx_desc *
dp_rx_desc_alloc(struct dp_soc *soc, struct rx_desc_pool *rx_desc_pool)
{
    struct dp_rx_desc *rx_desc;

    qdf_spin_lock_bh(&rx_desc_pool->lock);

    if (qdf_unlikely(!rx_desc_pool->freelist)) {
        qdf_spin_unlock_bh(&rx_desc_pool->lock);
        return NULL;  // Pool exhausted
    }

    // Pop from freelist head
    rx_desc = &rx_desc_pool->freelist->rx_desc;
    rx_desc_pool->freelist = rx_desc_pool->freelist->next;

    rx_desc->in_use = 1;
    rx_desc_pool->num_free--;
    rx_desc_pool->num_allocated++;

    qdf_spin_unlock_bh(&rx_desc_pool->lock);

    return rx_desc;
}

// Return descriptor to freelist (called after packet delivery)
static inline void
dp_rx_desc_free(struct dp_soc *soc, struct dp_rx_desc *rx_desc)
{
    uint8_t pool_id = rx_desc->pool_id;
    struct rx_desc_pool *rx_desc_pool = &soc->rx_desc_buf[pool_id];
    union dp_rx_desc_list_elem_t *desc_elem;

    // Clear descriptor state
    rx_desc->in_use = 0;
    rx_desc->nbuf = NULL;
    rx_desc->unmapped = 0;

    desc_elem = (union dp_rx_desc_list_elem_t *)rx_desc;

    qdf_spin_lock_bh(&rx_desc_pool->lock);

    // Push to freelist head
    desc_elem->next = rx_desc_pool->freelist;
    rx_desc_pool->freelist = desc_elem;

    rx_desc_pool->num_free++;
    rx_desc_pool->num_allocated--;

    qdf_spin_unlock_bh(&rx_desc_pool->lock);
}
```

#### 5.5.6 Buffer Lifecycle State Machine

```
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                         Buffer Lifecycle State Machine                               │
├─────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                      │
│  ┌─────────────┐                                                                     │
│  │   FREE      │◄──────────────────────────────────────────────────────────────────┐│
│  │  (freelist) │                                                                   ││
│  └──────┬──────┘                                                                   ││
│         │ dp_rx_desc_alloc()                                                       ││
│         │ qdf_nbuf_alloc()                                                         ││
│         ▼                                                                          ││
│  ┌─────────────┐                                                                   ││
│  │  ALLOCATED  │                                                                   ││
│  │ (nbuf set)  │                                                                   ││
│  └──────┬──────┘                                                                   ││
│         │ qdf_nbuf_map_single()                                                    ││
│         │ hal_rxdma_buff_addr_info_set()                                           ││
│         ▼                                                                          ││
│  ┌─────────────┐                                                                   ││
│  │   POSTED    │                                                                   ││
│  │ (in HW ring)│                                                                   ││
│  └──────┬──────┘                                                                   ││
│         │ Hardware receives packet                                                 ││
│         │ DMA writes TLVs + data                                                   ││
│         ▼                                                                          ││
│  ┌─────────────┐                                                                   ││
│  │  COMPLETED  │                                                                   ││
│  │ (in REO dst)│                                                                   ││
│  └──────┬──────┘                                                                   ││
│         │ dp_rx_process() reaps                                                    ││
│         │ qdf_nbuf_unmap_single()                                                  ││
│         ▼                                                                          ││
│  ┌─────────────┐                                                                   ││
│  │  UNMAPPED   │                                                                   ││
│  │ (CPU access)│                                                                   ││
│  └──────┬──────┘                                                                   ││
│         │ Process packet, deliver to stack                                         ││
│         │ Stack takes ownership of nbuf                                            ││
│         ▼                                                                          ││
│  ┌─────────────┐                                                                   ││
│  │  DELIVERED  │                                                                   ││
│  │ (nbuf gone) │                                                                   ││
│  └──────┬──────┘                                                                   ││
│         │ dp_rx_desc_free()                                                        ││
│         │ dp_rx_buffers_replenish() allocates new nbuf                             ││
│         └──────────────────────────────────────────────────────────────────────────┘│
│                                                                                      │
└─────────────────────────────────────────────────────────────────────────────────────┘
```

### 5.6 Complete Data Flow Summary

This section provides a comprehensive view of the entire RX data flow with function names, timing, and key operations at each step.

#### 5.6.1 High-Level Flow Diagram

```
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                         COMPLETE RX DATA FLOW                                        │
├─────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                      │
│  ┌─────────────────────────────────────────────────────────────────────────────────┐│
│  │ PHASE 1: INITIALIZATION (Boot time, ~100ms)                                     ││
│  ├─────────────────────────────────────────────────────────────────────────────────┤│
│  │ 1. POOL ALLOC: Create descriptor pools                                         ││
│  │    dp_rx_pdev_desc_pool_alloc() → qdf_mem_malloc(pool_size * sizeof(rx_desc))  ││
│  │                                                                                  ││
│  │ 2. BUFFER ALLOC: Allocate sk_buffs for each descriptor                         ││
│  │    dp_rx_pdev_buffers_alloc() → qdf_nbuf_alloc(buf_size, alignment)            ││
│  │                                                                                  ││
│  │ 3. DMA MAP: Map buffers for hardware access                                     ││
│  │    qdf_nbuf_map_single() → dma_map_single(dev, vaddr, size, DMA_FROM_DEVICE)   ││
│  │                                                                                  ││
│  │ 4. RING FILL: Post buffer addresses to RXDMA ring                              ││
│  │    dp_rx_buffers_replenish() → hal_rxdma_buff_addr_info_set(paddr, cookie)     ││
│  └─────────────────────────────────────────────────────────────────────────────────┘│
│         │                                                                            │
│         ▼                                                                            │
│  ┌─────────────────────────────────────────────────────────────────────────────────┐│
│  │ PHASE 2: HARDWARE RECEIVE (Per-packet, ~10-50μs)                                ││
│  ├─────────────────────────────────────────────────────────────────────────────────┤│
│  │ 5. RF/PHY: Receive over-the-air signal                                          ││
│  │    Antenna → LNA → ADC → Demodulator → Decoder                                  ││
│  │                                                                                  ││
│  │ 6. MAC HW: Process 802.11 frame                                                 ││
│  │    FCS check → Decrypt → Defragment → Reorder (BA window)                       ││
│  │                                                                                  ││
│  │ 7. RXDMA: Fetch buffer, write TLVs + data                                       ││
│  │    Read buffer from RXDMA ring → DMA write TLVs → DMA write packet data        ││
│  │                                                                                  ││
│  │ 8. REO: Reorder and route to destination ring                                   ││
│  │    Sequence check → BA window update → Post to REO_DST ring                     ││
│  └─────────────────────────────────────────────────────────────────────────────────┘│
│         │                                                                            │
│         ▼                                                                            │
│  ┌─────────────────────────────────────────────────────────────────────────────────┐│
│  │ PHASE 3: SOFTWARE PROCESSING (Per-packet, ~5-20μs)                              ││
│  ├─────────────────────────────────────────────────────────────────────────────────┤│
│  │ 9. INTERRUPT: Hardware signals completion                                        ││
│  │    MSI/Legacy IRQ → hif_ahb_interrupt_handler() → napi_schedule()               ││
│  │                                                                                  ││
│  │ 10. NAPI POLL: Kernel calls NAPI poll handler                                   ││
│  │     hif_napi_poll() → dp_service_srngs() → dp_rx_process()                      ││
│  │                                                                                  ││
│  │ 11. RING REAP: Read completed entries from REO ring                             ││
│  │     hal_srng_access_start() → hal_srng_dst_peek() → hal_srng_dst_get_next()    ││
│  │                                                                                  ││
│  │ 12. COOKIE LOOKUP: Convert cookie to software descriptor                        ││
│  │     HAL_RX_REO_BUF_COOKIE_GET() → dp_rx_cookie_2_va_rxdma_buf() → rx_desc      ││
│  │                                                                                  ││
│  │ 13. DMA UNMAP: Sync cache, unmap buffer                                         ││
│  │     qdf_nbuf_unmap_nbytes_single() → dma_unmap_single()                         ││
│  │                                                                                  ││
│  │ 14. TLV PARSE: Extract metadata from hardware TLVs                              ││
│  │     HAL_RX_MSDU_END_*_GET() → HAL_RX_MPDU_*_GET() → HAL_RX_ATTN_*_GET()        ││
│  │                                                                                  ││
│  │ 15. CB POPULATE: Store metadata in sk_buff control block                        ││
│  │     QDF_NBUF_CB_RX_PEER_ID() = peer_id, QDF_NBUF_CB_RX_TID_VAL() = tid, ...    ││
│  │                                                                                  ││
│  │ 16. BUFFER ADJUST: Set data pointer and length                                  ││
│  │     qdf_nbuf_set_pktlen(msdu_len) → qdf_nbuf_pull_head(TLV_LEN + padding)      ││
│  └─────────────────────────────────────────────────────────────────────────────────┘│
│         │                                                                            │
│         ▼                                                                            │
│  ┌─────────────────────────────────────────────────────────────────────────────────┐│
│  │ PHASE 4: DELIVERY AND REPLENISH (Per-packet, ~2-10μs)                           ││
│  ├─────────────────────────────────────────────────────────────────────────────────┤│
│  │ 17. PROTOCOL SETUP: Set protocol and device                                     ││
│  │     eth_type_trans() → skb->protocol, skb->dev = netdev                         ││
│  │                                                                                  ││
│  │ 18. DELIVER: Hand off to network stack                                          ││
│  │     vdev->osif_rx() → napi_gro_receive() → netif_receive_skb()                  ││
│  │                                                                                  ││
│  │ 19. DESC FREE: Return descriptor to freelist                                    ││
│  │     dp_rx_add_to_free_desc_list() → dp_rx_desc_free()                           ││
│  │                                                                                  ││
│  │ 20. REPLENISH: Allocate new buffer, refill ring                                 ││
│  │     dp_rx_buffers_replenish() → qdf_nbuf_alloc() → qdf_nbuf_map() → ring post  ││
│  └─────────────────────────────────────────────────────────────────────────────────┘│
│                                                                                      │
└─────────────────────────────────────────────────────────────────────────────────────┘
```

#### 5.6.2 Timing Breakdown

| Phase | Step | Function | Typical Time |
|-------|------|----------|--------------|
| Init | Pool alloc | `dp_rx_pdev_desc_pool_alloc()` | 1-5ms |
| Init | Buffer alloc | `dp_rx_pdev_buffers_alloc()` | 50-100ms |
| HW | RF/PHY | Hardware | 5-20μs |
| HW | MAC processing | Hardware | 2-10μs |
| HW | RXDMA + REO | Hardware | 1-5μs |
| SW | Interrupt → NAPI | `hif_ahb_interrupt_handler()` | 1-3μs |
| SW | Ring reap | `dp_rx_process()` | 0.5-2μs/pkt |
| SW | TLV parse | `HAL_RX_*_GET()` | 0.1-0.5μs/pkt |
| SW | Deliver | `napi_gro_receive()` | 1-5μs/pkt |
| SW | Replenish | `dp_rx_buffers_replenish()` | 0.5-2μs/pkt |

#### 5.6.3 Function Call Graph

```
dp_rx_process()
├── hal_srng_access_start()
├── while (ring_desc = hal_srng_dst_peek())
│   ├── HAL_RX_REO_BUF_COOKIE_GET()
│   ├── dp_rx_cookie_2_va_rxdma_buf()
│   ├── qdf_nbuf_unmap_nbytes_single()
│   ├── qdf_prefetch()
│   ├── DP_RX_LIST_APPEND()
│   └── hal_srng_dst_get_next()
├── hal_srng_access_end()
├── for each nbuf in list:
│   ├── HAL_RX_TLV_MSDU_DONE_GET()
│   ├── HAL_RX_MSDU_END_MSDU_LEN_GET()
│   ├── HAL_RX_MPDU_PEER_META_DATA_GET()
│   ├── dp_rx_peer_metadata_peer_id_get()
│   ├── dp_peer_get_ref_by_id()
│   ├── QDF_NBUF_CB_RX_*() setters
│   ├── qdf_nbuf_set_pktlen()
│   ├── qdf_nbuf_pull_head()
│   ├── dp_rx_deliver_to_stack()
│   │   ├── eth_type_trans()
│   │   └── napi_gro_receive()
│   └── dp_rx_add_to_free_desc_list()
└── dp_rx_buffers_replenish()
    ├── qdf_nbuf_alloc()
    ├── qdf_nbuf_map_single()
    └── hal_rxdma_buff_addr_info_set()
```

### 5.7 Key Data Structures

This section provides detailed information about the key data structures involved in the RX path.

#### 5.7.1 sk_buff (Socket Buffer)

The Linux kernel's fundamental network buffer structure:

```c
// From linux/skbuff.h (simplified)
struct sk_buff {
    // ┌─────────────────────────────────────────────────────────────────┐
    // │ Buffer Pointers                                                  │
    // └─────────────────────────────────────────────────────────────────┘
    unsigned char *head;        // Start of allocated buffer
    unsigned char *data;        // Start of packet data
    unsigned char *tail;        // End of packet data
    unsigned char *end;         // End of allocated buffer

    // ┌─────────────────────────────────────────────────────────────────┐
    // │ Length Information                                               │
    // └─────────────────────────────────────────────────────────────────┘
    unsigned int len;           // Length of data (tail - data)
    unsigned int data_len;      // Length in fragments (for SG)
    unsigned int truesize;      // Total allocated size

    // ┌─────────────────────────────────────────────────────────────────┐
    // │ Device and Protocol                                              │
    // └─────────────────────────────────────────────────────────────────┘
    struct net_device *dev;     // Device we arrived on/are leaving by
    __be16 protocol;            // Packet protocol (ETH_P_IP, etc.)

    // ┌─────────────────────────────────────────────────────────────────┐
    // │ Control Block (48 bytes for driver private data)                 │
    // └─────────────────────────────────────────────────────────────────┘
    char cb[48] __aligned(8);   // Driver-specific metadata

    // ┌─────────────────────────────────────────────────────────────────┐
    // │ Checksum and Priority                                            │
    // └─────────────────────────────────────────────────────────────────┘
    __u8 ip_summed:2;           // Checksum status
    __u8 priority;              // Packet priority (from TID)

    // ┌─────────────────────────────────────────────────────────────────┐
    // │ Linked List                                                      │
    // └─────────────────────────────────────────────────────────────────┘
    struct sk_buff *next;       // Next buffer in list
    struct sk_buff *prev;       // Previous buffer in list

    // ┌─────────────────────────────────────────────────────────────────┐
    // │ Custom Fields (added via kernel patches)                         │
    // └─────────────────────────────────────────────────────────────────┘
    void *ar_pkt_trace;         // Packet tracing pointer
    uint16_t ar_meta;           // Cached metadata (TID, EAPOL, DHCP flags)
};
```

#### 5.7.2 sk_buff Memory Layout

```
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                         sk_buff Memory Layout                                        │
├─────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                      │
│  sk_buff structure (metadata)                                                        │
│  ┌─────────────────────────────────────────────────────────────────────────────────┐│
│  │ head, data, tail, end pointers                                                  ││
│  │ len, data_len, truesize                                                         ││
│  │ dev, protocol                                                                   ││
│  │ cb[48] (control block)                                                          ││
│  │ ar_pkt_trace, ar_meta (custom fields)                                           ││
│  └─────────────────────────────────────────────────────────────────────────────────┘│
│         │                                                                            │
│         │ head pointer                                                               │
│         ▼                                                                            │
│  ┌─────────────────────────────────────────────────────────────────────────────────┐│
│  │ Headroom (for pushing headers)                                                  ││
│  │ ┌─────────────────────────────────────────────────────────────────────────────┐ ││
│  │ │ Reserved space (typically 128-256 bytes)                                    │ ││
│  │ └─────────────────────────────────────────────────────────────────────────────┘ ││
│  ├─────────────────────────────────────────────────────────────────────────────────┤│
│  │ ◄── data pointer                                                                ││
│  │ Packet Data                                                                     ││
│  │ ┌─────────────────────────────────────────────────────────────────────────────┐ ││
│  │ │ Ethernet Header (14 bytes)                                                  │ ││
│  │ │ IP Header (20-60 bytes)                                                     │ ││
│  │ │ TCP/UDP Header (8-60 bytes)                                                 │ ││
│  │ │ Payload (variable)                                                          │ ││
│  │ └─────────────────────────────────────────────────────────────────────────────┘ ││
│  │ ◄── tail pointer                                                                ││
│  ├─────────────────────────────────────────────────────────────────────────────────┤│
│  │ Tailroom (for appending data)                                                   ││
│  │ ┌─────────────────────────────────────────────────────────────────────────────┐ ││
│  │ │ Reserved space                                                              │ ││
│  │ └─────────────────────────────────────────────────────────────────────────────┘ ││
│  │ ◄── end pointer                                                                 ││
│  └─────────────────────────────────────────────────────────────────────────────────┘│
│                                                                                      │
│  len = tail - data (actual packet length)                                           │
│  headroom = data - head (space for pushing headers)                                 │
│  tailroom = end - tail (space for appending data)                                   │
│                                                                                      │
└─────────────────────────────────────────────────────────────────────────────────────┘
```

#### 5.7.3 rx_pkt_tlvs Structure

Hardware-written TLVs at the start of each received buffer:

```c
// From hal_be_rx_tlv.h
struct rx_pkt_tlvs {
    // ┌─────────────────────────────────────────────────────────────────┐
    // │ MSDU End TLV - Per-MSDU information                              │
    // └─────────────────────────────────────────────────────────────────┘
    struct rx_msdu_end_tlv {
        uint32_t tlv_tag;           // TLV type identifier
        struct rx_msdu_end {
            uint32_t msdu_length;       // MSDU length in bytes
            uint32_t l3_header_padding; // Padding before L3 header
            uint32_t decap_format;      // Decapsulation format
            uint32_t msdu_done;         // Processing complete flag
            uint32_t tcp_udp_chksum;    // TCP/UDP checksum
            uint32_t sa_idx;            // Source address index
            uint32_t da_idx;            // Destination address index
            uint32_t flow_idx;          // Flow index for steering
            // ... more fields
        } rx_msdu_end;
    } msdu_end_tlv;

    // ┌─────────────────────────────────────────────────────────────────┐
    // │ MPDU Start TLV - Per-MPDU information                            │
    // └─────────────────────────────────────────────────────────────────┘
    struct rx_mpdu_start_tlv {
        uint32_t tlv_tag;
        struct rx_mpdu_start {
            uint32_t peer_meta_data;    // Peer ID from AST lookup
            uint32_t sequence_number;   // 802.11 sequence number
            uint32_t tid;               // Traffic Identifier
            uint32_t encrypt_type;      // Encryption type
            uint64_t pn;                // Packet Number (for replay)
            uint32_t ampdu_flag;        // Part of A-MPDU
            uint32_t bssid_hit;         // BSSID matched
            // ... more fields
        } rx_mpdu_start;
    } mpdu_start_tlv;

    // ┌─────────────────────────────────────────────────────────────────┐
    // │ Attention TLV - Error and status flags                           │
    // └─────────────────────────────────────────────────────────────────┘
    struct rx_attention_tlv {
        uint32_t tlv_tag;
        struct rx_attention {
            uint32_t fcs_err:1;         // FCS error
            uint32_t decrypt_err:1;     // Decryption error
            uint32_t tkip_mic_err:1;    // TKIP MIC error
            uint32_t fragment_flag:1;   // Fragmented MPDU
            uint32_t first_mpdu:1;      // First MPDU of A-MPDU
            uint32_t last_mpdu:1;       // Last MPDU of A-MPDU
            uint32_t msdu_limit_error:1;// Too many MSDUs
            // ... more flags
        } rx_attention;
    } attn_tlv;

    // ┌─────────────────────────────────────────────────────────────────┐
    // │ Packet Header TLV - 802.11 header copy                           │
    // └─────────────────────────────────────────────────────────────────┘
    struct rx_pkt_hdr_tlv {
        uint32_t tlv_tag;
        uint8_t rx_pkt_hdr[128];    // Copy of 802.11 header
    } pkt_hdr_tlv;
};

// Total size: RX_PKT_TLVS_LEN (typically 384-512 bytes depending on chip)
```

#### 5.7.4 Data Structure Relationships

```
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                         Data Structure Relationships                                │
├─────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                      │
│  dp_soc                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────────────────┐│
│  │ rx_desc_buf[MAX_RXDESC_POOLS]                                                   ││
│  │     │                                                                            ││
│  │     └──► rx_desc_pool                                                           ││
│  │              │                                                                   ││
│  │              ├── array ──► [dp_rx_desc][dp_rx_desc]...[dp_rx_desc]              ││
│  │              │                    │                                              ││
│  │              │                    └── nbuf ──► sk_buff                          ││
│  │              │                    └── paddr_buf_start                           ││
│  │              │                    └── cookie                                    ││
│  │              │                                                                   ││
│  │              └── freelist ──► dp_rx_desc ──► dp_rx_desc ──► NULL               ││
│  │                                                                                  ││
│  │ reo_dest_ring[MAX_REO_DEST_RINGS]                                               ││
│  │     │                                                                            ││
│  │     └──► dp_srng                                                                ││
│  │              │                                                                   ││
│  │              └── hal_srng_handle ──► hal_srng                                   ││
│  │                                          │                                       ││
│  │                                          ├── ring_base_vaddr ──► ring entries   ││
│  │                                          ├── ring_base_paddr                    ││
│  │                                          ├── num_entries                        ││
│  │                                          └── u.dst_ring (hp, tp, cached_hp)     ││
│  └─────────────────────────────────────────────────────────────────────────────────┘│
│                                                                                      │
│  Ring Entry (REO Destination)                                                        │
│  ┌─────────────────────────────────────────────────────────────────────────────────┐│
│  │ buffer_addr_info                                                                ││
│  │     ├── buffer_addr_31_0                                                        ││
│  │     ├── buffer_addr_39_32                                                       ││
│  │     ├── return_buffer_manager                                                   ││
│  │     └── sw_buffer_cookie ──────────────────────────────────────────────────────┐││
│  │ rx_mpdu_desc_info                                                              │││
│  │ rx_msdu_desc_info                                                              │││
│  └────────────────────────────────────────────────────────────────────────────────┘││
│                                                                                    ││
│  Cookie Lookup:                                                                    ││
│  ┌─────────────────────────────────────────────────────────────────────────────────┘│
│  │                                                                                  │
│  │  cookie ──► pool_id + index ──► rx_desc_buf[pool_id].array[index] ──► rx_desc  │
│  │                                                                                  │
│  │  rx_desc.nbuf ──► sk_buff ──► packet data                                       │
│  │                                                                                  │
│  └─────────────────────────────────────────────────────────────────────────────────┘│
│                                                                                      │
└─────────────────────────────────────────────────────────────────────────────────────┘
```

#### 5.7.5 Structure Size Summary

| Structure | Typical Size | Notes |
|-----------|--------------|-------|
| `sk_buff` | 232-256 bytes | Varies by kernel version |
| `sk_buff->cb` | 48 bytes | Fixed, for driver private data |
| `dp_rx_desc` | 32-48 bytes | Per-buffer descriptor |
| `rx_pkt_tlvs` | 384-512 bytes | Hardware TLVs, chip-dependent |
| `hal_srng` | 256-384 bytes | Ring management structure |
| `rx_desc_pool` | 64-96 bytes | Pool management structure |
| Ring entry | 32-64 bytes | Per-entry in hardware ring |

### 5.8 QDF_NBUF_CB Metadata Population

During RX processing, metadata from hardware TLVs is stored in `skb->cb` for efficient access:

```c
// Macros for accessing RX metadata in sk_buff->cb
// File: cmn_dev/qdf/linux/src/i_qdf_nbuf.h

#define QDF_NBUF_CB_RX_PEER_ID(skb)     // Peer identifier
#define QDF_NBUF_CB_RX_VDEV_ID(skb)     // Virtual device ID
#define QDF_NBUF_CB_RX_TID_VAL(skb)     // Traffic Identifier (QoS)
#define QDF_NBUF_CB_RX_PKT_LEN(skb)     // MSDU length
#define QDF_NBUF_CB_RX_CTX_ID(skb)      // REO ring context

// Fragment chain flags (for scatter-gather)
#define QDF_NBUF_CB_RX_CHFRAG_START(skb)  // First fragment
#define QDF_NBUF_CB_RX_CHFRAG_CONT(skb)   // Continuation fragment
#define QDF_NBUF_CB_RX_CHFRAG_END(skb)    // Last fragment

// Address validation flags
#define QDF_NBUF_CB_RX_DA_MCBC(skb)     // Destination is multicast/broadcast
#define QDF_NBUF_CB_RX_DA_VALID(skb)    // DA is valid
#define QDF_NBUF_CB_RX_SA_VALID(skb)    // SA is valid
#define QDF_NBUF_CB_RX_IS_FRAG(skb)     // Is fragmented MPDU
#define QDF_NBUF_CB_RX_FCS_ERR(skb)     // FCS error flag
#define QDF_NBUF_CB_RX_RAW_FRAME(skb)   // Raw 802.11 frame
```

**Metadata population in dp_rx_process():**
```c
// From REO ring descriptor
peer_mdata = mpdu_desc_info.peer_meta_data;
QDF_NBUF_CB_RX_PEER_ID(rx_desc->nbuf) = DP_PEER_METADATA_PEER_ID_GET(peer_mdata);
QDF_NBUF_CB_RX_VDEV_ID(rx_desc->nbuf) = DP_PEER_METADATA_VDEV_ID_GET(peer_mdata);

// From MSDU descriptor
if (msdu_desc_info.msdu_flags & HAL_MSDU_F_FIRST_MSDU_IN_MPDU)
    qdf_nbuf_set_rx_chfrag_start(rx_desc->nbuf, 1);

if (msdu_desc_info.msdu_flags & HAL_MSDU_F_DA_IS_VALID)
    qdf_nbuf_set_da_valid(rx_desc->nbuf, 1);

if (msdu_desc_info.msdu_flags & HAL_MSDU_F_SA_IS_VALID)
    qdf_nbuf_set_sa_valid(rx_desc->nbuf, 1);

// TID from REO queue number
qdf_nbuf_set_tid_val(rx_desc->nbuf, HAL_RX_REO_QUEUE_NUMBER_GET(ring_desc));

// Packet length
QDF_NBUF_CB_RX_PKT_LEN(rx_desc->nbuf) = msdu_desc_info.msdu_len;

// Context ID (ring number)
QDF_NBUF_CB_RX_CTX_ID(rx_desc->nbuf) = reo_ring_num;
```

### 5.9 Scatter-Gather (SG) Handling for Large Packets

Large MSDUs that span multiple buffers are handled via scatter-gather:

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    SCATTER-GATHER REASSEMBLY                            │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│   Large MSDU spanning multiple nbufs:                                   │
│                                                                         │
│   ┌─────────────┐    ┌─────────────┐    ┌─────────────┐                │
│   │   nbuf[0]   │    │   nbuf[1]   │    │   nbuf[2]   │                │
│   │ chfrag_start│───▶│ chfrag_cont │───▶│ chfrag_end  │                │
│   │   = 1       │    │   = 1       │    │   = 1       │                │
│   │  Part 1     │    │   Part 2    │    │   Part 3    │                │
│   └─────────────┘    └─────────────┘    └─────────────┘                │
│         │                  │                  │                         │
│         └──────────────────┼──────────────────┘                         │
│                            ▼                                            │
│                    dp_rx_sg_create()                                    │
│                            │                                            │
│                            ▼                                            │
│                    ┌─────────────────────────────────┐                  │
│                    │  Parent nbuf with frag_list     │                  │
│                    │  ┌─────────────────────────────┐│                  │
│                    │  │ Part 1 | frag_list ──┐     ││                  │
│                    │  └────────────────────│────────┘│                  │
│                    │                       ▼         │                  │
│                    │              [Part 2]──▶[Part 3]│                  │
│                    └─────────────────────────────────┘                  │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

**dp_rx_sg_create() implementation:**
```c
qdf_nbuf_t dp_rx_sg_create(struct dp_soc *soc, qdf_nbuf_t nbuf)
{
    qdf_nbuf_t parent, frag_list, frag_tail, next = NULL;
    uint16_t frag_list_len = 0;
    uint16_t mpdu_len;

    // Use MSDU length from REO descriptor (more reliable than TLV)
    mpdu_len = QDF_NBUF_CB_RX_PKT_LEN(nbuf);

    // Handle case where first fragment has zero length
    if (!mpdu_len) {
        frag_tail = nbuf;
        while (frag_tail && qdf_nbuf_is_rx_chfrag_cont(frag_tail))
            frag_tail = frag_tail->next;

        if (frag_tail)
            QDF_NBUF_CB_RX_PKT_LEN(nbuf) = QDF_NBUF_CB_RX_PKT_LEN(frag_tail);
    }

    // Build frag_list from continuation fragments
    parent = nbuf;
    frag_list = nbuf->next;
    parent->next = NULL;

    // Accumulate total length
    while (frag_list) {
        frag_list_len += qdf_nbuf_len(frag_list);
        frag_list = frag_list->next;
    }

    // Attach frag_list to parent
    skb_shinfo(parent)->frag_list = nbuf->next;
    parent->data_len = frag_list_len;
    parent->len += frag_list_len;

    return parent;
}
```

**Chain Fragment Flags (chfrag):**
| Flag | Meaning |
|------|---------|
| `chfrag_start` | First buffer in scattered MSDU chain |
| `chfrag_cont` | Continuation buffer (middle) |
| `chfrag_end` | Last buffer in chain |

### 5.10 Decapsulation Process (802.11 to Ethernet)

Hardware can deliver packets in different encapsulation formats:

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    DECAPSULATION FORMATS                                │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  1. RAW Mode (HAL_HW_RX_DECAP_FORMAT_RAW):                              │
│     └─ Full 802.11 frame with FCS                                       │
│                                                                         │
│  2. Native WiFi (HAL_HW_RX_DECAP_FORMAT_NATIVE_WIFI):                   │
│     └─ 802.11 header (non-QoS) + payload               a                │
│                                                                         │
│  3. Ethernet II (HAL_HW_RX_DECAP_FORMAT_8023):                          │
│     └─ Standard Ethernet frame (DA/SA/Type/Payload)                     │
│                                                                         │
│  4. 802.3 LLC/SNAP (HAL_HW_RX_DECAP_FORMAT_ETH2):                       │
│     └─ Ethernet with LLC/SNAP encapsulation                             │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

**Native WiFi to Ethernet conversion:**
```c
void ol_rx_defrag_nwifi_to_8023(qdf_nbuf_t msdu)
{
    struct ieee80211_frame_addr4 wh;
    struct llc_snap_hdr_t llchdr;
    struct ethernet_hdr_t *eth_hdr;
    uint32_t hdrsize;

    // Copy 802.11 header
    qdf_mem_copy(&wh, qdf_nbuf_data(msdu), sizeof(wh));

    // Calculate 802.11 header size (varies by frame type)
    hdrsize = sizeof(struct ieee80211_frame);  // 24 bytes
    if ((wh.i_fc[1] & IEEE80211_FC1_DIR_MASK) == IEEE80211_FC1_DIR_DSTODS)
        hdrsize += 6;  // Add 4th address for WDS

    // Extract LLC/SNAP header following 802.11 header
    qdf_mem_copy(&llchdr, qdf_nbuf_data(msdu) + hdrsize,
                 sizeof(struct llc_snap_hdr_t));

    // Remove 802.11 + LLC/SNAP headers
    qdf_nbuf_pull_head(msdu, hdrsize + sizeof(llchdr));

    // Prepend Ethernet II header
    eth_hdr = (struct ethernet_hdr_t *)qdf_nbuf_push_head(msdu,
               sizeof(struct ethernet_hdr_t));

    // Set DA/SA based on To DS / From DS bits
    switch (wh.i_fc[1] & IEEE80211_FC1_DIR_MASK) {
    case IEEE80211_FC1_DIR_FROMDS:  // AP to STA
        qdf_mem_copy(eth_hdr->dest_addr, wh.i_addr1, 6);  // DA
        qdf_mem_copy(eth_hdr->src_addr, wh.i_addr3, 6);   // SA
        break;
    case IEEE80211_FC1_DIR_TODS:    // STA to AP
        qdf_mem_copy(eth_hdr->dest_addr, wh.i_addr3, 6);  // DA
        qdf_mem_copy(eth_hdr->src_addr, wh.i_addr2, 6);   // SA
        break;
    // ... handle other cases
    }

    // Copy EtherType from LLC/SNAP
    eth_hdr->ethertype = llchdr.ethertype;
}
```

### 5.11 Defragmentation (802.11 MPDU Fragments)

WiFi MPDUs can be fragmented at the MAC layer. The driver reassembles them:

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    MPDU DEFRAGMENTATION                                 │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│   Fragmented MPDU (sequence number + fragment number):                  │
│                                                                         │
│   ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐        │
│   │  Frag 0 (seq=N) │  │  Frag 1 (seq=N) │  │  Frag 2 (seq=N) │        │
│   │  More Frag = 1  │  │  More Frag = 1  │  │  More Frag = 0  │        │
│   │  PN: 100        │  │  PN: 101        │  │  PN: 102        │        │
│   └─────────────────┘  └─────────────────┘  └─────────────────┘        │
│           │                    │                    │                   │
│           └────────────────────┼────────────────────┘                   │
│                                ▼                                        │
│                    dp_rx_defrag_store_fragment()                        │
│                                │                                        │
│                    (wait for all fragments)                             │
│                                │                                        │
│                                ▼                                        │
│                    dp_rx_defrag() - when complete                       │
│                    ┌─────────────────────────────────┐                  │
│                    │  1. PN Check (replay attack)    │                  │
│                    │  2. Security decap (TKIP/CCMP)  │                  │
│                    │  3. MIC verification            │                  │
│                    │  4. Reassemble into single nbuf │                  │
│                    │  5. Deliver to network stack    │                  │
│                    └─────────────────────────────────┘                  │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

**PN (Packet Number) validation for replay protection:**
```c
static int dp_rx_defrag_pn_check(struct dp_soc *soc, qdf_nbuf_t msdu,
                                  uint64_t *cur_pn128, uint64_t *prev_pn128)
{
    int out_of_order = 0;

    // Extract 128-bit PN from TLV
    hal_rx_tlv_get_pn_num(soc->hal_soc, qdf_nbuf_data(msdu), cur_pn128);

    // PN must increment by exactly 1 for each fragment
    if (cur_pn128[1] == prev_pn128[1])
        out_of_order = (cur_pn128[0] - prev_pn128[0] != 1);
    else
        out_of_order = (cur_pn128[1] - prev_pn128[1] != 1);

    return out_of_order;  // 0 = OK, non-zero = replay detected
}
```

**Security type handling in defragmentation:**
```c
QDF_STATUS dp_rx_defrag(struct dp_txrx_peer *txrx_peer, unsigned int tid,
                         qdf_nbuf_t frag_list_head, qdf_nbuf_t frag_list_tail)
{
    // Determine security type
    index = hal_rx_msdu_is_wlan_mcast(soc->hal_soc, cur) ?
            dp_sec_mcast : dp_sec_ucast;

    switch (txrx_peer->security[index].sec_type) {
    case cdp_sec_type_tkip:
        tkip_demic = 1;
        // fallthrough
    case cdp_sec_type_tkip_nomic:
        // Strip TKIP header (8 bytes) and MIC (8 bytes)
        while (cur) {
            if (dp_rx_defrag_tkip_decap(soc, cur, hdr_space))
                return QDF_STATUS_E_DEFRAG_ERROR;
            cur = qdf_nbuf_next(cur);
        }
        break;

    case cdp_sec_type_aes_ccmp:
    case cdp_sec_type_aes_ccmp_256:
        // Strip CCMP header (8 bytes) and MIC (8/16 bytes)
        while (cur) {
            if (dp_rx_defrag_ccmp_decap(soc, cur, hdr_space))
                return QDF_STATUS_E_DEFRAG_ERROR;
            cur = qdf_nbuf_next(cur);
        }
        break;

    case cdp_sec_type_aes_gcmp:
    case cdp_sec_type_aes_gcmp_256:
        // Handle GCMP decryption
        // ...
        break;
    }

    // Verify MIC if TKIP
    if (tkip_demic) {
        if (!dp_rx_defrag_tkip_demic(soc, frag_list_head, key))
            return QDF_STATUS_E_DEFRAG_ERROR;
    }

    return QDF_STATUS_SUCCESS;
}
```

### 5.12 Multicast/Broadcast Handling

Multicast and broadcast packets require special handling:

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    MULTICAST/BROADCAST RX PATH                          │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│   ┌─────────────────────────────────────────────────────────────────┐   │
│   │                    Multicast/Broadcast Check                    │   │
│   │                                                                 │   │
│   │  if (qdf_nbuf_is_da_mcbc(nbuf)) {                              │   │
│   │      // Destination is multicast or broadcast                  │   │
│   │  }                                                              │   │
│   └─────────────────────────────────────────────────────────────────┘   │
│                              │                                          │
│               ┌──────────────┴──────────────┐                          │
│               ▼                              ▼                          │
│   ┌─────────────────────┐        ┌─────────────────────┐               │
│   │ MEC (Echo Check)    │        │ Intra-BSS Forward   │               │
│   │                     │        │                     │               │
│   │ - Prevent loops     │        │ - Forward to other  │               │
│   │ - Check SA against  │        │   clients in BSS    │               │
│   │   local MAC table   │        │ - Clone packet for  │               │
│   │                     │        │   local delivery    │               │
│   └─────────────────────┘        └─────────────────────┘               │
│              │                              │                           │
│              ▼                              ▼                           │
│   ┌─────────────────────┐        ┌─────────────────────┐               │
│   │ dp_rx_mcast_echo_   │        │ dp_rx_intrabss_     │               │
│   │ check()             │        │ mcbc_fwd()          │               │
│   │                     │        │                     │               │
│   │ Return: true=drop   │        │ Clone & TX to peers │               │
│   └─────────────────────┘        └─────────────────────┘               │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

**Multicast Echo Check (MEC):**
```c
bool dp_rx_mcast_echo_check(struct dp_soc *soc,
                             struct dp_txrx_peer *txrx_peer,
                             uint8_t *rx_tlv_hdr,
                             qdf_nbuf_t nbuf)
{
    struct dp_vdev *vdev = txrx_peer->vdev;

    // Only check for STA mode with MC/BC packets
    if (vdev->opmode != wlan_op_mode_sta)
        return false;
    if (!hal_rx_msdu_end_da_is_mcbc_get(soc->hal_soc, rx_tlv_hdr))
        return false;

    // Get source address from packet
    data = qdf_nbuf_data(nbuf);

    // Check if SA is in our MEC table (packets we transmitted)
    qdf_spin_lock_bh(&soc->mec_lock);
    mecentry = dp_mec_hash_find(soc, data + QDF_MAC_ADDR_SIZE);
    qdf_spin_unlock_bh(&soc->mec_lock);

    if (mecentry) {
        // This is a looped-back packet - drop it
        return true;
    }

    return false;
}
```

**NAWDS (Native Wireless Distribution System) multicast handling:**
```c
if (qdf_unlikely(txrx_peer->nawds_enabled &&
                 hal_rx_msdu_end_da_is_mcbc_get(soc->hal_soc, rx_tlv_hdr) &&
                 (hal_rx_get_mpdu_mac_ad4_valid(soc->hal_soc, rx_tlv_hdr) == false))) {
    // Drop MC/BC packets without valid Address 4 in NAWDS mode
    DP_PEER_PER_PKT_STATS_INC(txrx_peer, rx.nawds_mcast_drop, 1);
    dp_rx_nbuf_free(nbuf);
    continue;
}
```

### 5.13 Per-Packet Processing Optimizations

The RX path includes several optimizations for throughput:

```c
// Batch processing - chain packets for same VDEV
nbuf = nbuf_head;
while (nbuf) {
    next = nbuf->next;
    vdev_id = QDF_NBUF_CB_RX_VDEV_ID(nbuf);

    // Deliver batch when VDEV changes
    if (deliver_list_head && vdev && (vdev->vdev_id != vdev_id)) {
        dp_rx_deliver_to_stack(soc, vdev, peer,
                               deliver_list_head, deliver_list_tail);
        deliver_list_head = NULL;
        deliver_list_tail = NULL;
    }

    // Add to current batch
    DP_RX_LIST_APPEND(deliver_list_head, deliver_list_tail, nbuf);
    nbuf = next;
}

// Checksum offload
dp_rx_cksum_offload(vdev->pdev, nbuf, rx_tlv_hdr);

// Protocol tag update (for CCE/FSE)
dp_rx_update_protocol_tag(soc, vdev, nbuf, rx_tlv_hdr, reo_ring_num, false, true);
dp_rx_update_flow_tag(soc, vdev, nbuf, rx_tlv_hdr, true);

// Statistics update
dp_rx_msdu_stats_update(soc, nbuf, rx_tlv_hdr, peer, ring_id, tid_stats);
```

### 5.14 Delivery to Network Stack

Final delivery uses the OSIF callback registered during VDEV creation:

```c
QDF_STATUS dp_rx_deliver_to_stack(struct dp_soc *soc,
                                   struct dp_vdev *vdev,
                                   struct dp_txrx_peer *txrx_peer,
                                   qdf_nbuf_t nbuf_head,
                                   qdf_nbuf_t nbuf_tail)
{
    // Validate callbacks exist
    if (dp_rx_validate_rx_callbacks(soc, vdev, txrx_peer, nbuf_head)
        != QDF_STATUS_SUCCESS)
        return QDF_STATUS_E_FAILURE;

    // Handle raw/native WiFi decapsulation if needed
    if (qdf_unlikely(vdev->rx_decap_type == htt_cmn_pkt_type_raw) ||
        (vdev->rx_decap_type == htt_cmn_pkt_type_native_wifi)) {
        dp_rx_raw_pkt_mld_addr_conv(soc, vdev, txrx_peer, nbuf_head);
        vdev->osif_rsim_rx_decap(vdev->osif_vdev, &nbuf_head, &nbuf_tail);
    }

    // Call OSIF callback (leads to netif_receive_skb / napi_gro_receive)
    dp_rx_check_delivery_to_stack(soc, vdev, txrx_peer, nbuf_head);

    return QDF_STATUS_SUCCESS;
}
```

**OSIF layer delivery to Linux:**
```c
// In osif_nss_vdev.c or osif_rawmode.c
skb->dev = netdev;
skb->protocol = eth_type_trans(skb, netdev);

// Remove nbuf tracking for debug builds
nbuf_debug_del_record(skb);

// Deliver to network stack with GRO (Generic Receive Offload)
napi_gro_receive(napi, skb);
```

### 5.15 Complete dp_rx_process() Flow Diagram

```
┌─────────────────────────────────────────────────────────────────────────┐
│                      dp_rx_process() COMPLETE FLOW                      │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  PHASE 1: RING REAPING                                                  │
│  ─────────────────────                                                  │
│  while (quota && (ring_desc = hal_srng_dst_peek())) {                  │
│      ├─ Extract cookie from ring_desc                                   │
│      ├─ Lookup rx_desc from cookie                                      │
│      ├─ Get nbuf from rx_desc                                           │
│      ├─ Unmap DMA                                                       │
│      ├─ Populate QDF_NBUF_CB metadata:                                  │
│      │   ├─ PEER_ID, VDEV_ID                                            │
│      │   ├─ TID, PKT_LEN                                                │
│      │   ├─ chfrag_start/cont/end                                       │
│      │   └─ da_valid, sa_valid                                          │
│      ├─ Add to nbuf_head/nbuf_tail chain                               │
│      └─ hal_srng_dst_get_next() - pop ring entry                       │
│  }                                                                      │
│                                                                         │
│  PHASE 2: PER-PACKET PROCESSING                                         │
│  ─────────────────────────────                                          │
│  while (nbuf) {                                                         │
│      ├─ Get rx_tlv_hdr from nbuf data                                   │
│      ├─ Lookup vdev and peer                                            │
│      │                                                                   │
│      ├─ CHECK: MSDU Done?                                               │
│      │   └─ NO: Drop and increment msdu_done_fail stat                 │
│      │                                                                   │
│      ├─ CHECK: Scatter-Gather MSDU?                                     │
│      │   ├─ YES (raw): dp_rx_sg_create() - build frag_list             │
│      │   └─ YES (non-raw): Wait for chfrag_end                         │
│      │                                                                   │
│      ├─ CHECK: Raw Frame?                                               │
│      │   └─ YES: Handle as-is, increment rx_raw_pkts                   │
│      │                                                                   │
│      ├─ ADJUST: Strip TLVs, apply L3 padding                           │
│      │   └─ qdf_nbuf_pull_head(nbuf, RX_PKT_TLVS_LEN + l2_hdr_offset)  │
│      │                                                                   │
│      ├─ CHECK: Multipass VLAN processing?                               │
│      │   └─ dp_rx_multipass_process()                                   │
│      │                                                                   │
│      ├─ CHECK: WDS policy check                                         │
│      │   └─ FAIL: Drop with POLICY_CHECK_DROP stat                     │
│      │                                                                   │
│      ├─ PROCESS: Checksum offload                                       │
│      │   └─ dp_rx_cksum_offload()                                       │
│      │                                                                   │
│      ├─ PROCESS: Protocol/Flow tagging                                  │
│      │   ├─ dp_rx_update_protocol_tag()                                 │
│      │   └─ dp_rx_update_flow_tag()                                     │
│      │                                                                   │
│      ├─ STATS: Update per-MSDU statistics                               │
│      │   └─ dp_rx_msdu_stats_update()                                   │
│      │                                                                   │
│      ├─ BATCH: Add to per-VDEV delivery list                           │
│      │   └─ DP_RX_LIST_APPEND(deliver_list_head, nbuf)                 │
│      │                                                                   │
│      └─ DELIVER: When VDEV changes                                      │
│          └─ dp_rx_deliver_to_stack(vdev, peer, deliver_list)           │
│  }                                                                      │
│                                                                         │
│  PHASE 3: CLEANUP                                                       │
│  ────────────────                                                       │
│  ├─ Deliver remaining packets in deliver_list                          │
│  ├─ dp_rx_buffers_replenish() - refill RX rings                        │
│  └─ Return count of processed packets                                   │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

### 5.16 Why This Matters for BTF/eBPF

When eBPF programs need to access `sk_buff` fields:

1. **At buffer creation**: sk_buff is allocated in host memory
2. **After DMA write**: Hardware has written TLV metadata
3. **After parsing**: Driver has populated `sk_buff->cb` from TLVs
4. **At network stack**: `ar_meta` field may be populated with cached DHCP/EAPOL flags

eBPF programs hook at various points and need correct BTF offsets for:
- `sk_buff->data` - Points to packet data
- `sk_buff->cb` - Control block with driver metadata
- `sk_buff->ar_meta` - Cached TID/DHCP/EAPOL flags (patched field)
- `sk_buff->pkt_trace` - Packet tracing pointer (patched field)

---

## 6. TX Path: How sk_buff is Sent to Hardware

This section explains the transmit path - how packets flow from the network stack to WiFi hardware.

### 6.1 TX Data Flow Overview

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         TX DATA FLOW                                    │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│   Network Stack                                                         │
│        │                                                                │
│        ▼                                                                │
│   ┌─────────────────┐                                                   │
│   │  hard_start_xmit │  (OSIF/HDD layer)                                │
│   └────────┬────────┘                                                   │
│            │                                                            │
│            ▼                                                            │
│   ┌─────────────────┐                                                   │
│   │   dp_tx_send()   │  Entry point to DP TX layer                      │
│   └────────┬────────┘                                                   │
│            │                                                            │
│            ▼                                                            │
│   ┌─────────────────────────────────┐                                   │
│   │  dp_tx_send_msdu_single()       │                                   │
│   │  - Allocate TX descriptor       │                                   │
│   │  - Map nbuf for DMA             │                                   │
│   │  - Setup HAL TX descriptor      │                                   │
│   └────────┬────────────────────────┘                                   │
│            │                                                            │
│            ▼                                                            │
│   ┌─────────────────────────────────┐                                   │
│   │  hal_srng_src_get_next()        │  Get next TCL ring entry          │
│   │  hal_tx_desc_sync()             │  Write descriptor to HW ring      │
│   └────────┬────────────────────────┘                                   │
│            │                                                            │
│            ▼                                                            │
│   ┌─────────────────────────────────┐                                   │
│   │         TCL Ring (HW)           │  Transmit Command/Data Ring       │
│   └────────┬────────────────────────┘                                   │
│            │                                                            │
│            ▼                                                            │
│   ┌─────────────────────────────────┐                                   │
│   │    WiFi Hardware (TXDMA)        │  DMA reads buffer, transmits      │
│   └────────┬────────────────────────┘                                   │
│            │                                                            │
│            ▼                                                            │
│   ┌─────────────────────────────────┐                                   │
│   │  TX Completion Ring (WBM)       │  Hardware posts completion        │
│   └────────┬────────────────────────┘                                   │
│            │                                                            │
│            ▼                                                            │
│   ┌─────────────────────────────────┐                                   │
│   │   dp_tx_comp_handler()          │  Free nbuf, update stats          │
│   └─────────────────────────────────┘                                   │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

### 6.2 TX Descriptor Allocation

```c
// dp_tx_prepare_desc_single() - Allocate and prepare TX descriptor
tx_desc = dp_tx_desc_alloc(soc, tx_q->desc_pool_id);

// Store nbuf in tx_desc for completion handling
tx_desc->nbuf = nbuf;
tx_desc->flags = DP_TX_DESC_FLAG_ALLOCATED;

// Map buffer for DMA
tx_desc->dma_addr = qdf_nbuf_mapped_paddr_get(nbuf);
tx_desc->length = qdf_nbuf_len(nbuf);
```

### 6.3 TCL Ring Posting

```c
// Get next available slot in TCL (Transmit Command/Data) ring
hal_tx_desc = hal_srng_src_get_next(soc->hal_soc, hal_ring_hdl);

if (!hal_tx_desc) {
    // Ring is full - return nbuf to caller
    DP_STATS_INC(soc, tx.tcl_ring_full[ring_id], 1);
    return QDF_STATUS_E_RESOURCES;
}

// Populate HAL TX descriptor
hal_tx_desc_set_buf_addr(hal_tx_desc, tx_desc->dma_addr, ...);
hal_tx_desc_set_buf_length(hal_tx_desc, tx_desc->length);
hal_tx_desc_set_encap_type(hal_tx_desc, tx_desc->tx_encap_type);

// Sync cached descriptor to hardware ring
hal_tx_desc_sync(hal_tx_desc_cached, hal_tx_desc);
tx_desc->flags |= DP_TX_DESC_FLAG_QUEUED_TX;
```

### 6.4 TX Completion Handler

When hardware completes transmission, it posts to the WBM (Wireless Buffer Manager) release ring:

```c
// dp_tx_comp_handler() - Process TX completions
uint32_t dp_tx_comp_handler(struct dp_intr *int_ctx, struct dp_soc *soc,
                            hal_ring_handle_t hal_ring_hdl, uint8_t ring_id,
                            uint32_t quota)
{
    while (quota-- && (tx_comp_hal_desc = hal_srng_dst_get_next(...))) {
        // Extract tx_desc_id from completion descriptor
        tx_desc_id = hal_tx_comp_get_desc_id(tx_comp_hal_desc);

        // Lookup software TX descriptor
        tx_desc = dp_tx_desc_find(soc, pool_id, tx_desc_id);

        // Unmap DMA buffer
        qdf_nbuf_unmap_single(soc->osdev, tx_desc->nbuf, QDF_DMA_TO_DEVICE);

        // Free the sk_buff
        // ⚠️ WARNING: skb->cb may contain dangling pointers at this point!
        qdf_nbuf_free(tx_desc->nbuf);

        // Return descriptor to free pool
        dp_tx_desc_free(soc, tx_desc, pool_id);
    }
}
```

### 6.5 Why skb->cb is Dangerous in TX Completion

```
┌─────────────────────────────────────────────────────────────────────────┐
│                   skb->cb LIFECYCLE IN TX PATH                          │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  1. Network Stack:  skb->cb contains upper layer data                   │
│                     (e.g., TCP control info)                            │
│                                                                         │
│  2. Driver Entry:   skb->cb may be overwritten with driver metadata     │
│                     QDF_NBUF_CB_TX_*() macros used                      │
│                                                                         │
│  3. Hardware Queue: skb->cb contains pointers to tx_desc, vdev, etc.    │
│                     ⚠️ These are VALID at this point                    │
│                                                                         │
│  4. TX Completion:  Original context may be GONE                        │
│                     - vdev may have been deleted                        │
│                     - peer may have disassociated                       │
│                     - tx_desc pool may have been reallocated            │
│                     ⚠️ skb->cb pointers become DANGLING                 │
│                                                                         │
│  Solution: Use ar_meta field for any data needed in completion handler  │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 7. Error Handling in RX Path

### 7.1 Error Categories

| Error Type | Source | Handler Function |
|------------|--------|------------------|
| REO Errors | Reorder Engine | `dp_rx_err_process()` |
| RXDMA Errors | DMA Engine | `dp_rx_err_handler_rh()` |
| WBM Release Errors | Buffer Manager | `dp_rx_wbm_err_process()` |
| MSDU Done Failure | DMA Incomplete | Inline in `dp_rx_process()` |

### 7.2 REO Error Codes and Handling

```c
// REO Error codes from hal_rx_get_reo_error_code()
switch (error_code) {
    case HAL_REO_ERR_REGULAR_FRAME_2K_JUMP:
    case HAL_REO_ERR_BAR_FRAME_2K_JUMP:
        // Sequence number jumped by more than 2K - indicates reorder issue
        dp_2k_jump_handle(soc, nbuf, rx_tlv_hdr, peer_id, tid);
        break;

    case HAL_REO_ERR_REGULAR_FRAME_OOR:
    case HAL_REO_ERR_BAR_FRAME_OOR:
        // Out of Order - packet arrived too late
        dp_rx_oor_handle(soc, nbuf, peer_id, rx_tlv_hdr);
        break;

    case HAL_REO_ERR_QUEUE_DESC_ADDR_0:
        // NULL queue descriptor - unknown peer
        dp_rx_null_q_desc_handle(soc, nbuf, rx_tlv_hdr, ...);
        break;

    default:
        dp_err_rl("Non-support error code %d", error_code);
        dp_rx_nbuf_free(nbuf);
}
```

### 7.3 RXDMA Error Handling

```c
// From dp_rx_err_handler_rh()
static QDF_STATUS dp_rx_err_handler_rh(struct dp_soc *soc,
                                       struct dp_rx_desc *rx_desc,
                                       uint32_t error_code)
{
    switch (error_code) {
        case HTT_RXDATA_ERR_MSDU_LIMIT:
        case HTT_RXDATA_ERR_FLUSH_REQUEST:
        case HTT_RXDATA_ERR_ZERO_LEN_MSDU:
            // Invalid MSDU - just free the buffer
            dp_rx_nbuf_free(rx_desc->nbuf);
            break;

        case HTT_RXDATA_ERR_TKIP_MIC:
            // TKIP MIC failure - security error
            dp_rx_mic_err_handler_rh(soc, rx_desc->nbuf);
            break;

        case HTT_RXDATA_ERR_DECRYPT:
        case HTT_RXDATA_ERR_UNENCRYPTED:
            // Decryption failure
            dp_rx_decrypt_unecrypt_err_handler_rh(soc, rx_desc->nbuf, ...);
            break;
    }
}
```

### 7.4 MSDU Done Check (DMA Completion Verification)

```c
// In dp_rx_process() - Critical check for DMA completion
if (qdf_unlikely(!hal_rx_attn_msdu_done_get(rx_tlv_hdr))) {
    // DMA did not complete writing this buffer!
    dp_err("MSDU DONE failure");
    DP_STATS_INC(soc, rx.err.msdu_done_fail, 1);

    // Dump TLVs for debugging
    hal_rx_dump_pkt_tlvs(hal_soc, rx_tlv_hdr, QDF_TRACE_LEVEL_INFO);

    // Mark descriptor as error state
    rx_desc->msdu_done_fail = 1;

    // Free buffer and continue to next
    qdf_nbuf_free(nbuf);
    qdf_assert(0);  // Trigger assert in debug builds
    continue;
}
```

### 7.5 Buffer Sanity Checks

```c
// dp_rx_desc_paddr_sanity_check() - Verify buffer paddr hasn't been corrupted
#ifdef RX_DESC_DEBUG_CHECK
static inline bool dp_rx_desc_paddr_sanity_check(struct dp_rx_desc *rx_desc,
                                                  qdf_dma_addr_t paddr)
{
    // Compare physical address from HW descriptor with stored value
    if (rx_desc->paddr_buf_start != paddr) {
        DP_STATS_INC(soc, rx.err.nbuf_sanity_fail, 1);
        rx_desc->in_err_state = 1;
        return false;
    }
    return true;
}
#endif
```

### 7.6 Error Statistics

```c
// Key error counters tracked
struct dp_soc_stats {
    struct {
        uint32_t msdu_done_fail;      // DMA completion failed
        uint32_t nbuf_sanity_fail;    // Buffer address mismatch
        uint32_t rx_invalid_peer_id;  // Unknown peer
        uint32_t hal_reo_dest_dup;    // Duplicate descriptor
        uint32_t reo_error[HAL_REO_ERR_MAX];  // Per-error-code counts
    } err;
};
```

---

## 8. NAPI and Interrupt Handling

### 8.1 Interrupt Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    INTERRUPT HANDLING ARCHITECTURE                      │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  Hardware Interrupt                                                     │
│        │                                                                │
│        ▼                                                                │
│  ┌─────────────────────┐                                                │
│  │   HIF IRQ Handler   │  (Minimal processing - just schedule NAPI)    │
│  └──────────┬──────────┘                                                │
│             │ napi_schedule()                                           │
│             ▼                                                           │
│  ┌─────────────────────┐                                                │
│  │   hif_napi_poll()   │  (NAPI context - softirq)                     │
│  └──────────┬──────────┘                                                │
│             │                                                           │
│             ▼                                                           │
│  ┌─────────────────────┐                                                │
│  │  dp_service_srngs() │  (Process all rings for this interrupt ctx)   │
│  └──────────┬──────────┘                                                │
│             │                                                           │
│   ┌─────────┴─────────┬────────────────┬────────────────┐              │
│   ▼                   ▼                ▼                ▼              │
│ ┌──────────┐   ┌──────────────┐  ┌───────────────┐  ┌────────────┐    │
│ │TX Comp   │   │RX Process    │  │RX Error       │  │REO Status  │    │
│ │Handler   │   │(REO rings)   │  │Handler        │  │Handler     │    │
│ └──────────┘   └──────────────┘  └───────────────┘  └────────────┘    │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

### 8.2 NAPI Polling

```c
// hif_napi_poll() - NAPI poll callback
int hif_napi_poll(struct hif_opaque_softc *hif_ctx,
                  struct napi_struct *napi,
                  int budget)
{
    int rc = 0;
    int cpu = smp_processor_id();

    // Call data path service routine
    rc = dp_service_srngs(dp_ctx, budget, cpu);

    if (rc < budget) {
        // All work done - exit NAPI polling
        napi_complete(napi);
        // Re-enable interrupts
        hif_napi_enable_irq(hif_ctx, napi_info->id);
    }

    return rc;  // Return work done
}
```

### 8.3 Ring Service Routine

```c
// dp_service_srngs() - Service all rings for an interrupt context
uint32_t dp_service_srngs(void *dp_ctx, uint32_t dp_budget, int cpu)
{
    struct dp_intr *int_ctx = (struct dp_intr *)dp_ctx;
    uint32_t remaining_quota = dp_budget;
    uint32_t work_done = 0;

    // Get ring masks for this interrupt context
    uint8_t tx_mask = int_ctx->tx_ring_mask;
    uint8_t rx_mask = int_ctx->rx_ring_mask;
    uint8_t rx_err_mask = int_ctx->rx_err_ring_mask;

    // Process TX completion rings
    if (tx_mask) {
        for (ring = 0; ring < MAX_TCL_DATA_RINGS; ring++) {
            if (!(tx_mask & (1 << ring)))
                continue;
            work_done = dp_tx_comp_handler(int_ctx, soc,
                                           soc->tx_comp_ring[ring].hal_srng,
                                           ring, remaining_quota);
            budget -= work_done;
            if (budget <= 0) goto budget_done;
        }
    }

    // Process RX rings (REO destination rings)
    if (rx_mask) {
        for (ring = 0; ring < soc->num_reo_dest_rings; ring++) {
            if (!(rx_mask & (1 << ring)))
                continue;
            work_done = dp_rx_process(int_ctx,
                                      soc->reo_dest_ring[ring].hal_srng,
                                      ring, remaining_quota);
            budget -= work_done;
            if (budget <= 0) goto budget_done;
        }
    }

    // Process RX error ring
    if (rx_err_mask) {
        work_done = dp_rx_err_process(int_ctx, soc,
                                      soc->reo_exception_ring.hal_srng,
                                      remaining_quota);
    }

budget_done:
    return dp_budget - budget;  // Return total work done
}
```

### 8.4 Quota/Budget Management

```c
// Quota controls how many packets are processed per NAPI poll
┌──────────────────────────────────────────────────────────────────┐
│                    QUOTA MANAGEMENT                              │
├──────────────────────────────────────────────────────────────────┤
│                                                                  │
│  NAPI Budget (e.g., 64)                                         │
│        │                                                        │
│        ├──▶ TX Comp Ring 0: Process up to remaining_quota       │
│        │         │                                              │
│        │         └── work_done = 20, remaining = 44             │
│        │                                                        │
│        ├──▶ RX Ring 0: Process up to remaining_quota            │
│        │         │                                              │
│        │         └── work_done = 30, remaining = 14             │
│        │                                                        │
│        ├──▶ RX Ring 1: Process up to remaining_quota            │
│        │         │                                              │
│        │         └── work_done = 14, remaining = 0              │
│        │                                                        │
│        └──▶ Budget exhausted - return to NAPI                   │
│             (will be re-scheduled for more processing)          │
│                                                                  │
└──────────────────────────────────────────────────────────────────┘
```

### 8.5 Intra-BSS Forwarding

For packets destined to another station on the same BSS, forwarding happens in the driver:

```c
// dp_rx_intrabss_fwd() - Forward packet within same BSS
static bool dp_rx_intrabss_fwd(struct dp_soc *soc,
                               struct dp_peer *ta_peer,
                               uint8_t *rx_tlv_hdr,
                               qdf_nbuf_t nbuf,
                               struct hal_rx_msdu_metadata msdu_metadata)
{
    // Lookup destination peer from AST table
    ast_entry = dp_peer_ast_hash_find_soc(soc, &eh->ether_dhost);

    if (ast_entry && ast_entry->peer == ta_peer->vdev) {
        // Same VAP - clone and transmit
        nbuf_copy = qdf_nbuf_copy(nbuf);

        // Send via TX path (dp_tx_send)
        if (dp_tx_send(soc, ta_peer->vdev->vdev_id, nbuf_copy)) {
            // TX failed - free the copy
            qdf_nbuf_free(nbuf_copy);
        }

        tid_stats->intrabss_cnt++;
        return true;  // Forwarded
    }
    return false;  // Not intra-BSS
}
```

---

## 9. Performance Considerations

### 9.1 Key Optimizations

| Optimization | Description |
|--------------|-------------|
| **Prefetching** | `qdf_prefetch()` used to prefetch next descriptor while processing current |
| **Batch Processing** | Multiple packets processed per ring access to reduce lock overhead |
| **NAPI** | Polling mode reduces interrupt overhead for high traffic |
| **Buffer Pooling** | Pre-allocated buffer pools avoid per-packet allocation |
| **Cookie Lookup** | O(1) descriptor lookup via cookie index |
| **TLV Parsing** | Inline functions and macros for fast metadata extraction |

### 9.2 Memory Alignment

```c
// Buffers aligned for optimal DMA performance
#define RX_BUFFER_ALIGNMENT     128  // Cache line aligned
#define RX_BUFFER_RESERVATION   0    // Headroom for driver use

// TLVs aligned to avoid straddling cache lines
#define RX_PADDING0_BYTES       4
#define RX_PADDING1_BYTES       16
```

### 9.3 Ring Near-Full Handling

```c
// Monitor ring fill level to prevent overflow
if (dp_srng_get_near_full_level(soc, rx_ring) < DP_SRNG_THRESH_NEAR_FULL)
    return 0;

// Set flag to indicate ring is getting full
qdf_atomic_set(&rx_ring->near_full, 1);

// Trigger faster replenishment or flow control
```

---

## 10. Summary: Complete Packet Lifecycle

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    COMPLETE PACKET LIFECYCLE                            │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │                        RX PATH                                   │   │
│  │                                                                  │   │
│  │  1. Pre-allocate sk_buff, DMA map, post to RXDMA ring           │   │
│  │  2. Hardware receives packet, writes TLVs + data via DMA        │   │
│  │  3. Hardware posts to REO ring, triggers interrupt              │   │
│  │  4. NAPI polls, driver reaps ring via cookie lookup             │   │
│  │  5. DMA unmap, parse TLVs, populate sk_buff metadata            │   │
│  │  6. Check for errors (MSDU done, sanity checks)                 │   │
│  │  7. Intra-BSS forwarding check                                  │   │
│  │  8. Deliver to network stack (netif_receive_skb)                │   │
│  │  9. Replenish buffer pool                                       │   │
│  │                                                                  │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│                                                                         │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │                        TX PATH                                   │   │
│  │                                                                  │   │
│  │  1. Network stack calls hard_start_xmit with sk_buff            │   │
│  │  2. Allocate TX descriptor, store nbuf reference                │   │
│  │  3. DMA map buffer, populate HAL TX descriptor                  │   │
│  │  4. Post to TCL ring, hardware reads via DMA                    │   │
│  │  5. Hardware transmits, posts completion to WBM ring            │   │
│  │  6. NAPI polls, driver reaps TX completion                      │   │
│  │  7. DMA unmap, free sk_buff                                     │   │
│  │     ⚠️ sk_buff->cb may have DANGLING POINTERS here!             │   │
│  │  8. Return TX descriptor to pool                                │   │
│  │                                                                  │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│                                                                         │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │                      eBPF HOOK POINTS                            │   │
│  │                                                                  │   │
│  │  • TC ingress/egress - After sk_buff prepared for stack         │   │
│  │  • XDP - Early in RX path (before sk_buff allocated)            │   │
│  │  • Socket filters - At socket layer                             │   │
│  │  • kprobes/tracepoints - Any kernel function                    │   │
│  │                                                                  │   │
│  │  ➡️ All require correct BTF offsets for sk_buff fields          │   │
│  │  ➡️ ar_meta provides safe metadata access at all points         │   │
│  │                                                                  │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

