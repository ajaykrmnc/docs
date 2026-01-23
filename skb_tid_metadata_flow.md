# SKB TID and Metadata Flow Documentation

## Overview

This document describes the end-to-end flow of the `sk_buff` (skb) TID field and packet
metadata (DHCP, EAPOL) through the Arista WLAN driver datapath, from network stack to
wireless transmission and vice versa.

## Data Flow Direction

### TX Path (Downstream - To Client)
```
Application → Linux Kernel Network Stack → Arista Driver → QCA Driver → Hardware → Over-the-Air
```
- **Origin**: Linux kernel network stack (packets from applications, routing, bridging)
- **Destination**: WiFi client device

### RX Path (Upstream - From Client)
```
Over-the-Air → Hardware → QCA Driver → Arista Driver → Linux Kernel Network Stack → Application
```
- **Origin**: WiFi client device
- **Destination**: Linux kernel network stack (for routing, bridging, applications)

## Architecture Layers

```
+-------------------------+
|   Applications          |  (User Space)
+-------------------------+
            ↓ TX  ↑ RX
+-------------------------+
|   Linux Kernel          |  (Socket Layer, TCP/IP Stack, Bridging, Routing)
|   Network Stack         |
+-------------------------+
            ↓ TX  ↑ RX
+-------------------------+
|   net_device            |  (wifiX = Radio, athX = VAP interface)
|   ndo_start_xmit (TX)   |  See "wifiX vs athX Interfaces" section below
+-------------------------+
            ↓ TX  ↑ RX
+-------------------------+
|   OSIF Layer            |  (OS Interface - ieee80211_wireless.c)
|   osif_vap_hardstart()  |  QCA's OS abstraction layer
+-------------------------+
            ↓ TX  ↑ RX
+-------------------------+
|   ar_dp_if              |  (Arista DP Interface - ar_dp_if.c)
|   ar_dp_if_tx_handle()  |  Entry point to Arista datapath
|   ar_dp_if_rx_handle()  |
+-------------------------+
            ↓ TX  ↑ RX
+-------------------------+
|   ar_dp (Core)          |  (Arista Datapath Core)
|   ar_dp_tx_handle()     |  ar_dp.c - TX processing, classification
|   ar_dp_rx_handle()     |  ar_qos.c - QoS/TID mapping
+-------------------------+
            ↓ TX  ↑ RX
+-------------------------+
|   vdrv_dp_if            |  (Vendor Driver DP Interface - vdrv_dp_if.c)
|   Wrapper functions     |  Abstraction for vendor-specific APIs
+-------------------------+
            ↓ TX  ↑ RX
+-------------------------+
|   QCA Driver (DP)       |  (Qualcomm Datapath - dp_tx.c, dp_rx.c)
|   dp_tx_send()          |  Manages TX/RX rings, descriptors
|   dp_rx_process()       |  DMA to/from hardware
+-------------------------+
            ↓ TX  ↑ RX
+-------------------------+
|   QCA Driver (HAL)      |  (Hardware Abstraction Layer)
|   hal_tx_desc_set_*()   |  Programs hardware registers
+-------------------------+
            ↓ TX  ↑ RX
+-------------------------+
|   WiFi Hardware (MAC)   |  (Qualcomm WiFi Chipset - IPQ series)
|   TX/RX DMA Rings       |  802.11 MAC, PHY, RF
+-------------------------+
            ↓ TX  ↑ RX
+-------------------------+
|   Over-the-Air (OTA)    |  (802.11 Radio Transmission)
+-------------------------+
            ↓ TX  ↑ RX
+-------------------------+
|   WiFi Client Device    |  (Phone, Laptop, IoT device)
+-------------------------+
```

## Key Insight: Where Does TID Come From?

### TX Path (Packet going TO client)
1. **Linux Kernel** provides `skb->priority` based on socket options (SO_PRIORITY),
   DSCP marking, or traffic control (tc)
2. **Arista Driver** maps priority to 802.11 TID based on QoS configuration
3. **QCA Driver** reads TID from `skb->cb` and programs hardware TX descriptor
4. **Hardware** transmits with correct 802.11 QoS TID in MAC header

### RX Path (Packet coming FROM client)
1. **Hardware** receives 802.11 frame with QoS TID in MAC header
2. **QCA Driver** extracts TID from RX descriptor, stores in `skb->cb`
3. **Arista Driver** reads TID, sets `skb->priority` for Linux kernel
4. **Linux Kernel** uses priority for traffic control, QoS, routing decisions

## QCA Binary vs Arista Code Dependencies

### Component Breakdown

```
+------------------------------------------------------------------+
|                     ARISTA CONTROLLED                            |
|  (Source code - can modify)                                      |
|                                                                  |
|  ┌─────────────────────────────────────────────────────────────┐ |
|  │  ar_dp.c, ar_qos.c, ar_apc.c                                │ |
|  │  - ar_dp_classify_skb() - Packet classification             │ |
|  │  - ar_dp_set_qos_map() - QoS/TID mapping                    │ |
|  │  - ar_dp_tx_handle() / ar_dp_rx_handle()                    │ |
|  └─────────────────────────────────────────────────────────────┘ |
|                              ↓ calls                             |
|  ┌─────────────────────────────────────────────────────────────┐ |
|  │  vdrv_dp_if.c, vdrv_cp_if.c                                 │ |
|  │  - Wrapper functions for vendor driver APIs                 │ |
|  │  - vdrv_dp_if_wbuf_set_tid/dhcp/eapol()                     │ |
|  │  - Now also caches to ar_meta                               │ |
|  └─────────────────────────────────────────────────────────────┘ |
+------------------------------------------------------------------+
                               ↓ calls
+------------------------------------------------------------------+
|                  QCA HEADER FILES (Inline)                       |
|  (Compiled into Arista code - effectively Arista controlled)    |
|                                                                  |
|  ┌─────────────────────────────────────────────────────────────┐ |
|  │  wbuf.h, wbuf_adf_private.h, wbuf_private.h, osdep_adf.h    │ |
|  │                                                             │ |
|  │  wbuf_set_tid(skb, tid)     → stores in skb->cb             │ |
|  │  wbuf_set_dhcp(skb)         → N_FLAG_SET(skb, N_DHCP)       │ |
|  │  wbuf_set_eapol(skb)        → N_FLAG_SET(skb, N_EAPOL)      │ |
|  │  wbuf_is_dhcp(skb)          → N_FLAG_IS(skb, N_DHCP)        │ |
|  │  wbuf_is_eapol(skb)         → N_FLAG_IS(skb, N_EAPOL)       │ |
|  │  wbuf_classify(skb)         → Parses packet, sets flags     │ |
|  │                                                             │ |
|  │  These are INLINE functions - compiled into Arista binary   │ |
|  └─────────────────────────────────────────────────────────────┘ |
+------------------------------------------------------------------+
                               ↓ uses
+------------------------------------------------------------------+
|                     skb->cb (Control Block)                      |
|  (48-byte array in struct sk_buff)                              |
|                                                                  |
|  ┌─────────────────────────────────────────────────────────────┐ |
|  │  struct ieee80211_cb (accessed via qdf_nbuf_get_ext_cb())   │ |
|  │                                                             │ |
|  │  flags (u_int32_t):                                         │ |
|  │    N_EAPOL  = 0x10       (bit 4)                            │ |
|  │    N_DHCP   = 0x400000   (bit 22)                           │ |
|  │    N_ARP    = ...                                           │ |
|  │    N_AMSDU  = 0x20                                          │ |
|  │    ...                                                      │ |
|  │                                                             │ |
|  │  peer_desc.peer → struct wlan_objmgr_peer*                  │ |
|  │  (WARNING: May become stale/dangling in TX completion!)     │ |
|  └─────────────────────────────────────────────────────────────┘ |
+------------------------------------------------------------------+
                               ↓ read by
+------------------------------------------------------------------+
|                     QCA BINARY DRIVER                            |
|  (Pre-compiled - CANNOT modify)                                 |
|                                                                  |
|  ┌─────────────────────────────────────────────────────────────┐ |
|  │  dp_tx.c, dp_rx.c (compiled into .ko binary)                │ |
|  │                                                             │ |
|  │  TX Path:                                                   │ |
|  │    - Reads TID from QDF_NBUF_CB_TX_TID(skb)                 │ |
|  │    - Programs HAL TX descriptor with TID                    │ |
|  │    - Submits to hardware TX ring                            │ |
|  │                                                             │ |
|  │  RX Path:                                                   │ |
|  │    - Extracts TID from hardware RX descriptor               │ |
|  │    - Stores via QDF_NBUF_CB_RX_TID_VAL(skb) = tid           │ |
|  │    - Calls registered RX callback (ar_dp_if_rx_handle)      │ |
|  │                                                             │ |
|  │  TX Completion:                                             │ |
|  │    - Calls registered completion callback                   │ |
|  │    - skb->cb may have been reused/overwritten!              │ |
|  └─────────────────────────────────────────────────────────────┘ |
+------------------------------------------------------------------+
                               ↓
+------------------------------------------------------------------+
|                     HARDWARE (WiFi Chipset)                      |
|  (Qualcomm IPQ series - cannot modify)                          |
|                                                                  |
|  ┌─────────────────────────────────────────────────────────────┐ |
|  │  - TX: Reads TID from TX descriptor, sets QoS in 802.11 hdr │ |
|  │  - RX: Extracts TID from 802.11 QoS header, puts in RX desc │ |
|  └─────────────────────────────────────────────────────────────┘ |
+------------------------------------------------------------------+
```

### Who Controls What?

| Component | Controls | Modifiable? |
|-----------|----------|-------------|
| **Arista Code** | Classification logic, QoS mapping, ar_meta caching | ✅ Yes |
| **QCA Headers** | CB structure layout, flag definitions, inline accessors | ⚠️ Shared (compiled into Arista) |
| **QCA Binary** | HW programming, RX TID extraction, TX descriptor | ❌ No |
| **Hardware** | 802.11 QoS TID in MAC header | ❌ No |

### Why ar_meta Optimization Works

1. **TX Path Classification** (Arista controlled):
   ```
   ar_dp_classify_skb()
       ├── vdrv_dp_if_wbuf_set_dhcp(skb)
       │       ├── wbuf_set_dhcp(skb)      → Sets N_DHCP in skb->cb
       │       └── ar_skb_set_dhcp(skb)    → Caches in skb->ar_meta ✓
       │
       └── vdrv_dp_if_wbuf_set_tid(skb, tid)
               ├── wbuf_set_tid(skb, tid)  → Sets TID in skb->cb
               └── ar_skb_set_tid(skb, tid) → Caches in skb->ar_meta ✓
   ```
   - Arista code is the FIRST to classify and set these flags
   - We cache to ar_meta at the same time we set in CB
   - No dependency on QCA binary for TX classification

2. **Subsequent TX Path Reads** (Arista controlled):
   ```
   ar_dp_tx_process_dhcp()
       └── ar_skb_is_dhcp(skb)  → O(1) read from skb->ar_meta ✓
                                   (instead of wbuf_is_dhcp parsing)
   ```

3. **TX Completion** (Critical use case):
   ```
   QCA Binary calls → ar_dp_tx_complete(skb, ...)
       │
       │  At this point:
       │    - skb->cb may have stale pointers (peer, context)
       │    - skb->ar_meta is STILL VALID ✓
       │
       └── ar_skb_get_tid(skb)     → Safe O(1) read from ar_meta ✓
           ar_skb_is_dhcp(skb)     → Safe O(1) read from ar_meta ✓
           ar_skb_is_eapol(skb)    → Safe O(1) read from ar_meta ✓
   ```

4. **RX Path** (Mixed - QCA binary + Arista):
   ```
   QCA Binary:
       dp_rx_process() → QDF_NBUF_CB_RX_TID_VAL(skb) = tid_from_hw

   Arista:
       ar_dp_rx_handle()
           └── tid = vdrv_dp_rx_tid(skb)  → Reads from CB (set by QCA)
               └── QDF_NBUF_CB_RX_TID_VAL(skb)
   ```
   - RX TID MUST be read from CB (set by QCA binary from hardware)
   - DHCP/EAPOL detection on RX is done by Arista parsing the packet

### Dependency Summary

```
┌────────────────────────────────────────────────────────────────────────┐
│                           TX PATH                                      │
├────────────────────────────────────────────────────────────────────────┤
│  Classification: Arista → sets CB + ar_meta                           │
│  Reading flags:  Arista → reads ar_meta (optimized)                   │
│  HW programming: QCA Binary → reads CB → programs hardware            │
│  Completion:     Arista → reads ar_meta (CB may be stale)             │
│                                                                        │
│  ✅ ar_meta works because Arista controls classification              │
└────────────────────────────────────────────────────────────────────────┘

┌────────────────────────────────────────────────────────────────────────┐
│                           RX PATH                                      │
├────────────────────────────────────────────────────────────────────────┤
│  TID extraction: QCA Binary → extracts from HW → sets CB              │
│  TID reading:    Arista → reads from CB (must use CB, not ar_meta)    │
│  DHCP/EAPOL:     Arista → parses packet headers                       │
│                                                                        │
│  ⚠️ RX TID must come from CB (set by QCA binary from hardware)        │
│  ⚠️ ar_meta could be used to cache RX DHCP/EAPOL if needed            │
└────────────────────────────────────────────────────────────────────────┘
```

## SKB Metadata Storage

### 1. Control Block (skb->cb) - Legacy Method
- 48-byte array in `struct sk_buff`
- Used by QCA driver via `QDF_NBUF_CB_*` macros
- **Problem**: Can have dangling pointers in TX completion handler

### 2. ar_meta Field (skb->ar_meta) - Optimized Method
- 16-bit field added to `struct sk_buff` via kernel patch
- Direct field access, no pointer issues
- **Layout**:
```
Bits 0-7:   TID value (8 bits, values 0-15 for QoS)
Bit 8:      EAPOL flag (1 bit)
Bit 9:      DHCP flag (1 bit)
Bits 10-15: Reserved (6 bits)
```

## TX Path Flow

### 1. Network Stack → OSIF Layer
```
net_device->ndo_start_xmit()
    └── osif_vap_hardstart()  [ieee80211_wireless.c]
            └── ar_dp_if_tx_handle()  [ar_dp_if.c]
```

### 2. Arista TX Handler Entry Point
```c
// ar_dp_if.c
QDF_STATUS ar_dp_if_tx_handle(osif_dev* osdev, struct sk_buff* skb, bool unshare_req)
    └── ar_dp_tx_handle(soc, vdev_id, skb, unshare_req)  [ar_dp.c]
```

### 3. Packet Classification (ar_dp_classify_skb)
```c
// ar_dp.c - Line 2859
static inline int ar_dp_classify_skb(struct sk_buff* skb)
{
    // 1. Set default priority
    skb->priority = WME_AC_BE;
    vdrv_dp_if_wbuf_set_tid(skb, 0);  // Sets TID=0 in CB and ar_meta

    // 2. Initialize ar_meta to avoid stale data
    ar_skb_meta_init(skb);  // Clears ar_meta to 0

    // 3. Classify based on EtherType
    switch (ntohs(eh->ether_type)) {
        case ETHERTYPE_IP:
            // Check for DHCP (UDP port 67→68)
            vdrv_dp_if_wbuf_set_dhcp(skb);  // Sets CB + ar_meta
            break;

        case ETHERTYPE_PAE:  // 0x888E
            vdrv_dp_if_wbuf_set_eapol(skb);  // Sets CB + ar_meta
            vdrv_dp_if_wbuf_set_tid(skb, OSDEP_EAPOL_TID);  // TID=6 (VO)
            skb->priority = AR_TID_TO_WME_AC(OSDEP_EAPOL_TID);
            break;

        case ETHERTYPE_IPV6:
            // Check for DHCPv6
            vdrv_dp_if_wbuf_set_dhcp(skb);
            break;
    }
}
```

### 4. QoS Mapping (ar_dp_set_qos_map)
```c
// ar_dp.c - Determines TID based on QoS configuration
ar_dp_set_qos_map(skb, peer)
    ├── ar_qos_dp_set_hs20_qos_map()     // Hotspot 2.0 QoS Map
    ├── ar_qos_dp_set_map_pri_fixed()    // Fixed priority
    ├── ar_qos_dp_set_map_dstream_8021p() // 802.1p VLAN priority
    ├── ar_qos_dp_set_map_dstream_tos()  // IP TOS/DSCP
    └── ar_qos_dp_set_map_dstream_dscp() // DSCP-to-TID mapping

// Each function calls:
vdrv_dp_if_wbuf_set_tid(skb, tid);  // Stores TID in CB + ar_meta
skb->priority = ac;                  // Sets Access Category
```

### 5. TID Storage in Wrapper Functions
```c
// vdrv_dp_if.c - Line 47
void vdrv_dp_if_wbuf_set_tid(struct sk_buff* skb, int tid)
{
    wbuf_set_tid(skb, tid);           // Store in skb->cb (QDF CB)
    ar_skb_set_tid(skb, (uint8_t)tid); // Cache in skb->ar_meta
}
```

### 6. Vendor Driver TX Path
```
ar_dp_tx_handle() → ar_dp_tx_process_pkt() → return to vendor driver
    └── QCA dp_tx_send()
        └── HAL TX descriptor built with TID from skb->cb
            └── Hardware transmits with correct QoS TID
```

## RX Path Flow

### 1. Hardware → QCA Driver
```
WiFi Hardware (MAC)
    └── dp_rx_process()  [QCA driver]
        └── Extracts TID from RX descriptor
        └── Stores in QDF_NBUF_CB_RX_TID_VAL(skb)
```

### 2. QCA Driver → Arista RX Handler
```c
// ar_dp_if.c
QDF_STATUS ar_dp_if_rx_handle(struct sk_buff* skb, struct cdp_soc_t* soc, uint8_t vdev_id)
    └── ar_dp_rx_handle(skb, soc->ar_dp_soc, vdev_id)  [ar_dp.c]
```

### 3. Arista RX Handler (ar_dp_rx_handle)
```c
// ar_dp.c - Line 2657
AR_STATUS ar_dp_rx_handle(struct sk_buff* skb, struct ar_dp_soc_s* soc, uint8_t vdev_id)
{
    // 1. Get TID from vendor driver CB
    tid = vdrv_dp_rx_tid(skb);  // Reads QDF_NBUF_CB_RX_TID_VAL

    // 2. Get peer_id from vendor driver CB
    peer_id = vdrv_dp_rx_peer_id(skb);

    // 3. Set skb priority based on RX TID
    ar_qos_dp_rx_set_prio(skb, vdev, tid);

    // 4. Process DHCP/EAPOL events, statistics, etc.
    // ...
}
```

### 4. RX TID Reading
```c
// vdrv_dp_if.c - Line 30
uint8_t vdrv_dp_rx_tid(struct sk_buff* skb)
{
    return QDF_NBUF_CB_RX_TID_VAL(skb);  // Read from QCA CB
}
```

### 5. RX Priority Setting
```c
// ar_qos.c - Line 16
void ar_qos_dp_rx_set_prio(struct sk_buff* skb, struct ar_dp_vdev_s* vdev, uint8_t tid)
{
    if (AR_IS_QOS_PRIO_FIXED(vdev)) {
        ar_os_skb_set_priority(skb, WME_AC_TO_TID(AR_GET_QOS_PRIO(vdev)));
    } else {
        AR_CEIL_QOS_TID(vdev, tid);
        ar_os_skb_set_priority(skb, tid);
    }
}
```

## TX Completion Handler

### Purpose
Process TX completion status after hardware confirms transmission.

### Flow
```c
// ar_dp.c - Line 4065
AR_STATUS ar_dp_tx_complete(struct sk_buff* skb, struct ar_dp_soc_s* soc,
                            uint8_t vdev_id, struct ar_dp_msdu_desc_s* desc)
{
    // Note: At this point, skb->cb may have stale/dangling pointers
    // Use ar_skb_get_tid(skb) to safely read TID from ar_meta instead

    // Process completion for bgmon, statistics, etc.
    ar_bgmon_process_msdu(skb, peer, vdev->dp_pdev, desc);
}
```

### Why ar_meta is Important for TX Completion
- `skb->cb` is reused by multiple layers during TX
- By TX completion, CB pointers may be invalid
- `skb->ar_meta` is a dedicated field that persists throughout SKB lifetime
- Safe to read TID/DHCP/EAPOL flags in completion handler

## Inline Accessor Functions

### Location: `vdrv_dp_if.h`

```c
// Initialize ar_meta to zero
static inline void ar_skb_meta_init(struct sk_buff* skb)

// TID accessors
static inline void ar_skb_set_tid(struct sk_buff* skb, uint8_t tid)
static inline uint8_t ar_skb_get_tid(const struct sk_buff* skb)

// EAPOL accessors
static inline void ar_skb_set_eapol(struct sk_buff* skb)
static inline int ar_skb_is_eapol(const struct sk_buff* skb)

// DHCP accessors
static inline void ar_skb_set_dhcp(struct sk_buff* skb)
static inline int ar_skb_is_dhcp(const struct sk_buff* skb)
```

## TID to Access Category Mapping

```
TID  | AC (Access Category) | Description
-----|---------------------|-------------
0, 3 | AC_BE (0)           | Best Effort
1, 2 | AC_BK (1)           | Background
4, 5 | AC_VI (2)           | Video
6, 7 | AC_VO (3)           | Voice
```

### Macros
```c
#define AR_TID_TO_WME_AC(tid)  // TID → Access Category
#define WME_AC_TO_TID(ac)      // Access Category → TID
```

## Special Packet Handling

### EAPOL Packets (802.1X Authentication)
- EtherType: `0x888E`
- TID: `OSDEP_EAPOL_TID` (typically 6 - Voice)
- Priority: High (sent on VO queue for fast authentication)

### DHCP Packets
- IPv4: UDP port 67 (server) → 68 (client)
- IPv6: UDP port 547 (server) → 546 (client)
- Used for DHCP fingerprinting and client blocking features

## Performance Benefits of ar_meta

| Operation | Before (CB-based) | After (ar_meta) |
|-----------|-------------------|-----------------|
| is_dhcp() | Parse packet headers | O(1) bitwise AND |
| is_eapol()| Parse packet headers | O(1) bitwise AND |
| get_tid() | CB pointer dereference | O(1) bitwise shift |
| TX completion | Risk of stale pointers | Safe field access |

## wifiX vs athX Interfaces

### Overview

The Qualcomm WiFi driver creates two types of Linux network interfaces:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        PHYSICAL HARDWARE                                    │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐              │
│  │  WiFi Radio 0   │  │  WiFi Radio 1   │  │  WiFi Radio 2   │              │
│  │  (2.4 GHz)      │  │  (5 GHz)        │  │  (6 GHz)        │              │
│  └────────┬────────┘  └────────┬────────┘  └────────┬────────┘              │
└───────────┼─────────────────────┼─────────────────────┼─────────────────────┘
            │                     │                     │
            ▼                     ▼                     ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                     RADIO INTERFACES (wifiX)                                │
│                     One per physical radio                                  │
│                                                                             │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐              │
│  │     wifi0       │  │     wifi1       │  │     wifi2       │              │
│  │  (Radio 0)      │  │  (Radio 1)      │  │  (Radio 2)      │              │
│  │                 │  │                 │  │                 │              │
│  │  - PHY control  │  │  - PHY control  │  │  - PHY control  │              │
│  │  - Channel cfg  │  │  - Channel cfg  │  │  - Channel cfg  │              │
│  │  - TX power     │  │  - TX power     │  │  - TX power     │              │
│  │  - Scan         │  │  - Scan         │  │  - Scan         │              │
│  └────────┬────────┘  └────────┬────────┘  └────────┬────────┘              │
└───────────┼─────────────────────┼─────────────────────┼─────────────────────┘
            │                     │                     │
            │ Creates             │ Creates             │ Creates
            ▼                     ▼                     ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                      VAP INTERFACES (athX)                                  │
│                      Multiple per radio (virtual APs)                       │
│                                                                             │
│  ┌───────────┐ ┌───────────┐   ┌───────────┐ ┌───────────┐   ┌───────────┐ │
│  │   ath0    │ │   ath1    │   │   ath2    │ │   ath3    │   │   ath4    │ │
│  │  (SSID:   │ │  (SSID:   │   │  (SSID:   │ │  (SSID:   │   │  (SSID:   │ │
│  │  Corp)    │ │  Guest)   │   │  Corp)    │ │  IoT)     │   │  Corp)    │ │
│  │           │ │           │   │           │ │           │   │           │ │
│  │  BSSID:   │ │  BSSID:   │   │  BSSID:   │ │  BSSID:   │   │  BSSID:   │ │
│  │  aa:bb:.. │ │  aa:cc:.. │   │  dd:ee:.. │ │  dd:ff:.. │   │  gg:hh:.. │ │
│  └───────────┘ └───────────┘   └───────────┘ └───────────┘   └───────────┘ │
│       │             │               │             │               │         │
│       ▼             ▼               ▼             ▼               ▼         │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                    Linux Bridge (br0)                               │   │
│  │                    or Routing/NAT                                   │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────────┘
```

### wifiX - Radio Interface

| Property | Description |
|----------|-------------|
| **Naming** | `wifi0`, `wifi1`, `wifi2`, ... |
| **Represents** | Physical WiFi radio hardware |
| **One per** | Physical radio chipset |
| **Purpose** | Radio-level configuration and control |
| **Data path** | No direct data TX/RX (control plane only) |

**Functions:**
- PHY configuration (channel, bandwidth, TX power)
- Scanning
- Radio-level statistics
- DFS/CAC handling
- Spectral analysis

**Created by:**
```c
// osif_net.c
__qdf_net_create_wifidev()  → Creates wifi0, wifi1, etc.
    netdev->netdev_ops = &__qdf_net_wifidev_ops;
```

### athX - VAP Interface (Virtual Access Point)

| Property | Description |
|----------|-------------|
| **Naming** | `ath0`, `ath1`, `ath2`, ... |
| **Represents** | Virtual Access Point (VAP) / BSS |
| **Multiple per** | Radio (wifi0 can have ath0, ath1, ath2...) |
| **Purpose** | Data TX/RX, client association |
| **Data path** | Yes - handles all client traffic |

**Functions:**
- SSID configuration
- Client association/authentication
- Data frame TX/RX
- Per-BSS encryption (WPA2/WPA3)
- VLAN tagging

**Created by:**
```c
// osif_net.c
__qdf_net_create_vapdev()  → Creates ath0, ath1, etc.
    netdev->netdev_ops = &__qdf_net_vapdev_ops;
        .ndo_start_xmit = osif_vap_hardstart,  // TX entry point!
```

### Data Path Flow (TX)

```
Linux Kernel Network Stack
         │
         │ Sends packet to athX (VAP interface)
         ▼
┌─────────────────────────────────────────┐
│  athX (net_device)                      │
│  netdev_ops->ndo_start_xmit()           │
│         │                               │
│         ▼                               │
│  osif_vap_hardstart(skb, dev)           │  ← TX entry point for VAP
│         │                               │
│         ▼                               │
│  ar_dp_if_tx_handle(osdev, skb)         │  ← Arista datapath entry
│         │                               │
│         ▼                               │
│  ar_dp_tx_handle(soc, vdev_id, skb)     │  ← Classification, QoS mapping
│         │                               │
│         ▼                               │
│  QCA Driver dp_tx_send()                │  ← Vendor driver TX
│         │                               │
│         ▼                               │
│  Hardware TX Ring                       │  ← DMA to radio
└─────────────────────────────────────────┘
         │
         ▼
    WiFi Radio (wifiX)
         │
         ▼
    Over-the-Air to Client
```

### Data Path Flow (RX)

```
    Over-the-Air from Client
         │
         ▼
    WiFi Radio (wifiX)
         │
         ▼
┌─────────────────────────────────────────┐
│  Hardware RX Ring                       │  ← DMA from radio
│         │                               │
│         ▼                               │
│  QCA Driver dp_rx_process()             │  ← Vendor driver RX
│         │                               │
│         ▼                               │
│  ar_dp_if_rx_handle(skb, soc, vdev_id)  │  ← Arista datapath entry
│         │                               │
│         ▼                               │
│  ar_dp_rx_handle(skb, soc, vdev_id)     │  ← Processing, statistics
│         │                               │
│         ▼                               │
│  netif_rx(skb) / netif_receive_skb()    │  ← Deliver to kernel
│         │                               │
│         ▼                               │
│  athX (net_device)                      │  ← VAP interface
└─────────────────────────────────────────┘
         │
         ▼
Linux Kernel Network Stack
         │
         ▼
Application / Bridge / Routing
```

### Key Structures

```c
// osif_dev - OS Interface Device (VAP)
struct osif_dev {
    struct net_device *netdev;      // athX net_device
    struct wlan_objmgr_vdev *vdev;  // VDEV object
    void *legacy_osif_priv;         // Legacy private data
    bool is_delete_in_progress;
    // ...
};

// Radio level
struct ath_softc {
    struct net_device *netdev;      // wifiX net_device
    struct wlan_objmgr_pdev *pdev;  // PDEV object
    // ...
};
```

### Example: Typical AP Configuration

```
Hardware: Qualcomm IPQ8074 (Tri-band AP)

wifi0 (2.4 GHz Radio)
  ├── ath0  (SSID: "Corporate", VLAN 10)
  ├── ath1  (SSID: "Guest", VLAN 20)
  └── ath2  (SSID: "IoT", VLAN 30)

wifi1 (5 GHz Radio)
  ├── ath3  (SSID: "Corporate", VLAN 10)
  ├── ath4  (SSID: "Guest", VLAN 20)
  └── ath5  (SSID: "IoT", VLAN 30)

wifi2 (6 GHz Radio)
  └── ath6  (SSID: "Corporate-6G", VLAN 10)
```

### Summary

| Interface | Type | Data Path | Created By | Purpose |
|-----------|------|-----------|------------|---------|
| `wifiX` | Radio | Control only | `__qdf_net_create_wifidev()` | PHY config, scan, DFS |
| `athX` | VAP | TX/RX data | `__qdf_net_create_vapdev()` | Client traffic, BSS |

## DMA (Direct Memory Access) and Ring Buffers

### What is DMA?

DMA (Direct Memory Access) allows the WiFi hardware to read/write data directly
from/to system memory without CPU involvement. This is critical for high-throughput
WiFi (802.11ax can exceed 1 Gbps) where CPU-based packet copying would be a bottleneck.

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         WITHOUT DMA (CPU Copy)                              │
│                                                                             │
│   CPU                                                                       │
│    │                                                                        │
│    ├─── Read packet from RAM ───────────────────────────────────┐           │
│    │                                                            │           │
│    ├─── Copy to hardware buffer ────────────────────────────────┼──→ HW    │
│    │                                                            │           │
│    └─── CPU is BUSY during entire transfer                      │           │
│                                                                             │
│   Problem: CPU bottleneck at high data rates                               │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│                          WITH DMA (Zero Copy)                               │
│                                                                             │
│   CPU                           DMA Engine                                  │
│    │                                │                                       │
│    ├─── Setup descriptor ──────────→├─── Read from RAM ────────┐           │
│    │    (paddr, length)             │                          │           │
│    │                                ├─── Write to HW ──────────┼──→ HW    │
│    ├─── Do other work               │                          │           │
│    │    (CPU is FREE!)              ├─── Interrupt when done ──┘           │
│    │                                │                                       │
│    └─── Handle completion ←─────────┘                                       │
│                                                                             │
│   Benefit: CPU free during transfer, hardware does the work                │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Key DMA Concepts

| Term | Description |
|------|-------------|
| **Physical Address (paddr)** | Actual RAM address hardware can access |
| **Virtual Address (vaddr)** | CPU's view of memory (via MMU) |
| **DMA Mapping** | Convert vaddr → paddr for hardware |
| **Descriptor** | Small structure telling HW what to transfer |
| **Ring Buffer** | Circular array of descriptors |
| **SRNG** | Scatter-gather Ring (Qualcomm's ring implementation) |

### SRNG (Scatter-gather Ring) Architecture

Qualcomm WiFi chipsets use SRNG (Scatter-gather Ring) for all DMA operations:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           SRNG RING BUFFER                                  │
│                                                                             │
│   Ring Buffer in System RAM (DMA-able memory)                              │
│                                                                             │
│   ┌─────┬─────┬─────┬─────┬─────┬─────┬─────┬─────┬─────┬─────┐            │
│   │ D0  │ D1  │ D2  │ D3  │ D4  │ D5  │ D6  │ D7  │ ... │ Dn  │            │
│   └─────┴─────┴─────┴─────┴─────┴─────┴─────┴─────┴─────┴─────┘            │
│     ↑                       ↑                                               │
│     │                       │                                               │
│   Tail Pointer           Head Pointer                                       │
│   (Consumer)             (Producer)                                         │
│                                                                             │
│   Each Descriptor (D) contains:                                            │
│   ┌────────────────────────────────────────┐                               │
│   │  paddr_lo    : 32-bit low address      │                               │
│   │  paddr_hi    : 8-bit high address      │                               │
│   │  length      : Buffer size             │                               │
│   │  flags       : Control bits            │                               │
│   │  metadata    : TID, peer_id, etc.      │                               │
│   └────────────────────────────────────────┘                               │
└─────────────────────────────────────────────────────────────────────────────┘
```

### TX Ring Types

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           TX PATH RINGS                                     │
│                                                                             │
│  ┌──────────────────┐                                                      │
│  │    Software      │                                                      │
│  │  (dp_tx_send)    │                                                      │
│  └────────┬─────────┘                                                      │
│           │ 1. Create TX descriptor                                        │
│           │ 2. Map skb->data to paddr                                      │
│           │ 3. Fill TCL descriptor                                         │
│           ▼                                                                 │
│  ┌──────────────────┐                                                      │
│  │  TCL Data Ring   │  TCL = Transmit Classifier                          │
│  │  (tcl_data_ring) │  - SW produces descriptors                          │
│  │                  │  - HW consumes and transmits                         │
│  └────────┬─────────┘                                                      │
│           │                                                                 │
│           ▼                                                                 │
│  ┌──────────────────┐                                                      │
│  │   WiFi Hardware  │  - DMA reads packet from RAM                         │
│  │   (MAC + PHY)    │  - Encrypts, adds 802.11 header                     │
│  │                  │  - Transmits over-the-air                            │
│  └────────┬─────────┘                                                      │
│           │                                                                 │
│           ▼                                                                 │
│  ┌──────────────────┐                                                      │
│  │  WBM Release Ring│  WBM = WiFi Buffer Manager                          │
│  │  (tx_comp_ring)  │  - HW produces completion status                    │
│  │                  │  - SW consumes, frees buffers                        │
│  └────────┬─────────┘                                                      │
│           │                                                                 │
│           ▼                                                                 │
│  ┌──────────────────┐                                                      │
│  │    Software      │                                                      │
│  │(dp_tx_comp_handler)│                                                    │
│  │                  │  - Reads completion status                           │
│  │                  │  - Unmaps DMA                                        │
│  │                  │  - Frees skb                                         │
│  │                  │  - Calls ar_dp_tx_complete()                         │
│  └──────────────────┘                                                      │
└─────────────────────────────────────────────────────────────────────────────┘
```

### RX Ring Types

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           RX PATH RINGS                                     │
│                                                                             │
│  ┌──────────────────┐                                                      │
│  │    Software      │  1. Pre-allocate empty buffers                       │
│  │ (dp_rx_buffers_  │  2. Map to paddr                                     │
│  │  replenish)      │  3. Fill refill ring descriptors                     │
│  └────────┬─────────┘                                                      │
│           │                                                                 │
│           ▼                                                                 │
│  ┌──────────────────┐                                                      │
│  │ RX Refill Ring   │  - SW produces empty buffer descriptors              │
│  │(rx_refill_buf_ring)│ - HW consumes for received packets                │
│  └────────┬─────────┘                                                      │
│           │                                                                 │
│           ▼                                                                 │
│  ┌──────────────────┐                                                      │
│  │   WiFi Hardware  │  - Receives 802.11 frame over-the-air               │
│  │   (MAC + PHY)    │  - Decrypts, removes 802.11 header                  │
│  │                  │  - DMA writes packet to RAM buffer                   │
│  │                  │  - Extracts TID from QoS header                      │
│  └────────┬─────────┘                                                      │
│           │                                                                 │
│           ▼                                                                 │
│  ┌──────────────────┐                                                      │
│  │ REO Dest Ring    │  REO = Reorder Engine                               │
│  │ (reo_dest_ring)  │  - HW produces received packet descriptors          │
│  │                  │  - Handles A-MPDU reordering                         │
│  │                  │  - SW consumes completed packets                     │
│  └────────┬─────────┘                                                      │
│           │                                                                 │
│           ▼                                                                 │
│  ┌──────────────────┐                                                      │
│  │    Software      │  - Reads RX descriptor (includes TID!)              │
│  │ (dp_rx_process)  │  - Sets QDF_NBUF_CB_RX_TID_VAL(skb)                 │
│  │                  │  - Unmaps DMA                                        │
│  │                  │  - Calls ar_dp_rx_handle()                           │
│  └──────────────────┘                                                      │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Ring Types Summary

| Ring | Direction | Producer | Consumer | Purpose |
|------|-----------|----------|----------|---------|
| **TCL Data Ring** | TX | Software | Hardware | Submit packets for transmission |
| **TX Comp Ring** | TX | Hardware | Software | TX completion status |
| **RX Refill Ring** | RX | Software | Hardware | Provide empty buffers |
| **REO Dest Ring** | RX | Hardware | Software | Deliver received packets |
| **REO Exception** | RX | Hardware | Software | Exception handling |
| **WBM Idle Link** | Both | Both | Both | Buffer management |

### DMA Mapping in TX Path

```c
// dp_tx.c - Simplified TX DMA flow

QDF_STATUS dp_tx_send(struct dp_vdev *vdev, qdf_nbuf_t nbuf)
{
    // 1. Allocate TX descriptor
    tx_desc = dp_tx_desc_alloc(soc);
    tx_desc->nbuf = nbuf;

    // 2. Map skb data to physical address (DMA mapping)
    status = qdf_nbuf_map(vdev->osdev, nbuf, QDF_DMA_TO_DEVICE);

    // 3. Get physical address
    paddr = qdf_nbuf_mapped_paddr_get(nbuf);

    // 4. Fill TCL descriptor with paddr
    hal_tx_desc_set_buf_addr(hal_tx_desc, paddr, ...);
    hal_tx_desc_set_buf_length(hal_tx_desc, qdf_nbuf_len(nbuf));

    // 5. Set TID in descriptor (read from skb->cb)
    hal_tx_desc_set_tid(hal_tx_desc, tid);

    // 6. Submit to TCL ring
    hal_srng_src_get_next(hal_srng);  // Get next descriptor slot
    // Hardware will DMA the packet data directly from RAM
}
```

### DMA Mapping in RX Path

```c
// dp_rx.c - Simplified RX DMA flow

void dp_rx_buffers_replenish(struct dp_soc *soc)
{
    // 1. Allocate new skb
    nbuf = qdf_nbuf_alloc(soc->osdev, RX_BUFFER_SIZE, ...);

    // 2. Map to physical address (DMA mapping)
    status = qdf_nbuf_map(soc->osdev, nbuf, QDF_DMA_FROM_DEVICE);
    paddr = qdf_nbuf_get_frag_paddr(nbuf, 0);

    // 3. Fill refill ring descriptor
    hal_rxdma_buff_addr_set(rxdma_ring_entry, paddr, ...);

    // Hardware will DMA received packet directly into this buffer
}

uint32_t dp_rx_process(struct dp_soc *soc, void *hal_ring, uint32_t quota)
{
    // 1. Get completed RX descriptor from REO ring
    ring_desc = hal_srng_dst_get_next(hal_ring);

    // 2. Get TID from RX descriptor (hardware extracted from 802.11 QoS)
    tid = hal_rx_mpdu_start_tid_get(ring_desc);

    // 3. Store TID in skb->cb for upper layers
    QDF_NBUF_CB_RX_TID_VAL(nbuf) = tid;

    // 4. Unmap DMA (sync for CPU access)
    qdf_nbuf_unmap(soc->osdev, nbuf, QDF_DMA_FROM_DEVICE);

    // 5. Deliver to upper layer
    ar_dp_rx_handle(nbuf, soc, vdev_id);
}
```

### Why DMA Matters for TID/ar_meta

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    TID FLOW THROUGH DMA                                     │
│                                                                             │
│  TX Path:                                                                   │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐  │
│  │ Arista sets │ →  │ TID stored  │ →  │ HW reads    │ →  │ 802.11 QoS  │  │
│  │ TID in CB   │    │ in TCL desc │    │ from TCL    │    │ TID in air  │  │
│  │ + ar_meta   │    │ (paddr)     │    │ via DMA     │    │             │  │
│  └─────────────┘    └─────────────┘    └─────────────┘    └─────────────┘  │
│                                                                             │
│  TX Completion:                                                             │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐                     │
│  │ HW writes   │ →  │ SW reads    │ →  │ ar_meta     │                     │
│  │ completion  │    │ status from │    │ still valid │  ← skb->cb may     │
│  │ to WBM ring │    │ WBM ring    │    │ for TID!    │    be overwritten   │
│  └─────────────┘    └─────────────┘    └─────────────┘                     │
│                                                                             │
│  RX Path:                                                                   │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐  │
│  │ 802.11 QoS  │ →  │ HW extracts │ →  │ TID in REO  │ →  │ SW reads    │  │
│  │ TID in air  │    │ TID, writes │    │ descriptor  │    │ TID from    │  │
│  │             │    │ to REO desc │    │ (via DMA)   │    │ CB (QDF)    │  │
│  └─────────────┘    └─────────────┘    └─────────────┘    └─────────────┘  │
│                                                                             │
│  Key Point: RX TID comes from hardware via DMA descriptor, not packet      │
│             parsing. ar_meta is useful for TX path caching only.           │
└─────────────────────────────────────────────────────────────────────────────┘
```

### DMA Performance Impact

| Aspect | Without DMA | With DMA |
|--------|-------------|----------|
| **CPU Usage** | 100% during transfer | Near 0% during transfer |
| **Throughput** | ~500 Mbps max | 1+ Gbps possible |
| **Latency** | Higher (CPU copy) | Lower (direct HW access) |
| **Memory** | Double buffering needed | Zero-copy possible |

### Key Structures

```c
// dp_srng - Descriptor Ring
struct dp_srng {
    void *hal_srng;                    // HAL ring handle
    void *base_vaddr_unaligned;        // Virtual address (CPU view)
    qdf_dma_addr_t base_paddr_unaligned; // Physical address (HW view)
    uint32_t alloc_size;               // Total ring size
    int irq;                           // Interrupt for this ring
    uint32_t num_entries;              // Number of descriptors
};

// TX Descriptor (simplified)
struct dp_tx_desc_s {
    qdf_nbuf_t nbuf;                   // SKB pointer
    uint16_t flags;                    // TX flags
    uint8_t pool_id;                   // Descriptor pool
    struct hal_tx_desc_comp_s comp;    // Completion status from HW
    // ...
};
```

## File References

| File | Purpose |
|------|---------|
| `ar_dp.c` | Main TX/RX handlers, classification |
| `ar_qos.c` | QoS mapping, TID/AC conversion |
| `vdrv_dp_if.c` | Wrapper functions for vendor driver |
| `vdrv_dp_if.h` | Inline accessors for ar_meta |
| `ar_dp_if.c` | Interface between ar_core and ar_if |
| `osif_net.c` | Creates wifiX/athX net_devices |
| `ieee80211_wireless.c` | osif_vap_hardstart() TX entry |
| `dp_tx.c` | QCA TX path, TCL ring submission, DMA mapping |
| `dp_rx.c` | QCA RX path, REO ring processing, buffer replenish |
| `dp_types.h` | Ring structures (dp_srng), TX/RX descriptors |
| `hal_api.h` | HAL SRNG types and ring operations |

