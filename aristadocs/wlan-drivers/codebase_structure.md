# WLAN Drivers Codebase Structure

This document describes the folder structure, component relationships, and the 
division between Arista-controlled code and Qualcomm (QCA) vendor driver code.

## High-Level Directory Structure

```
ap/src/wlan-drivers/
├── ar/                     # Arista WLAN driver code (MODIFIABLE)
├── QCA/                    # Qualcomm vendor driver code
│   ├── licensed/           # Licensed QCA driver source (PARTIALLY MODIFIABLE)
│   └── channel_lists/      # Regulatory channel configuration
└── null_apdrv_mod/         # Null/stub driver module
```

## Component Ownership Summary

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        OWNERSHIP & MODIFIABILITY                            │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  ARISTA CODE (Full Control)                                         │   │
│  │  ar/                                                                 │   │
│  │  ✅ Can modify freely                                               │   │
│  │  ✅ Can add new features                                            │   │
│  │  ✅ Can optimize (e.g., ar_meta caching)                            │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                               │                                             │
│                               │ Uses APIs from                              │
│                               ▼                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  QCA HEADER FILES (Compiled into Arista binary)                     │   │
│  │  QCA/licensed/.../include/, os/linux/include/                       │   │
│  │  ⚠️ Inline functions compiled into our code                        │   │
│  │  ⚠️ Structure definitions (ieee80211_cb, etc.)                      │   │
│  │  ⚠️ Can use, should not modify                                      │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                               │                                             │
│                               │ Calls into                                  │
│                               ▼                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  QCA BINARY DRIVER (Pre-compiled, closed source)                    │   │
│  │  dp_tx.o, dp_rx.o, hal_srng.o, etc.                                 │   │
│  │  ❌ Cannot modify                                                   │   │
│  │  ❌ Must work with existing behavior                                │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                               │                                             │
│                               │ Programs                                    │
│                               ▼                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  WIFI HARDWARE (Qualcomm chipset)                                   │   │
│  │  IPQ8074, IPQ6018, QCA8074, etc.                                    │   │
│  │  ❌ Cannot modify                                                   │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Arista Code (`ar/`)

### Directory Structure

```
ar/
├── core/           # Core business logic (MAIN ARISTA CODE)
│   ├── src/        # Source files
│   └── inc/        # Internal headers
├── ar_if/          # Arista interface layer
│   ├── inc/        # Interface headers
│   └── qca/        # QCA-specific interface implementation
├── vdrv_if/        # Vendor driver interface (abstraction layer)
│   ├── inc/        # Vendor-agnostic interface headers
│   └── qca/        # QCA-specific implementation
├── os_if/          # Linux OS interface
├── user_if/        # User-space interface (ioctl, netlink)
├── utils/          # Utility functions
└── docs/           # Documentation
```

### Core Source Files (`ar/core/src/`)

| File | Purpose | Key Functions |
|------|---------|---------------|
| `ar_dp.c` | **Data path** - TX/RX packet handling | `ar_dp_tx_handle()`, `ar_dp_rx_handle()`, `ar_dp_classify_skb()` |
| `ar_qos.c` | **QoS handling** - TID/AC mapping | `ar_qos_get_tid()`, `ar_qos_tid_to_ac()` |
| `ar_apc.c` | **APC (Access Point Controller)** | `ar_apc_is_spl_data_pkt()` |
| `ar_acl.c` | Access Control Lists | Client filtering |
| `ar_arp.c` | ARP handling | Proxy ARP, ARP inspection |
| `ar_cfg.c` | Configuration management | Runtime configuration |
| `ar_cp.c` | Control path | Management frame handling |
| `ar_evt.c` | Event handling | Driver events, notifications |
| `ar_main.c` | Module initialization | `ar_init()`, `ar_exit()` |
| `ar_proc.c` | Procfs interface | Debug/stats via /proc |
| `ar_proxyarp.c` | Proxy ARP implementation | DHCP/ARP proxying |
| `ar_radiotap.c` | Radiotap header handling | Monitor mode |
| `ar_bgmon.c` | Background monitoring | Channel/radio monitoring |
| `ar_cs_scan.c` | Channel scanning | Off-channel scanning |
| `ar_mgmt_ap.c` | AP management | BSS management |
| `ar_rf_nbr.c` | RF neighbor handling | Neighbor AP detection |
| `ar_ie.c` | Information Element handling | 802.11 IE parsing/building |

### Vendor Driver Interface (`ar/vdrv_if/`)

This layer abstracts vendor-specific APIs, allowing Arista code to work with
different WiFi chipset vendors.

```
vdrv_if/
├── inc/                    # Vendor-agnostic headers
│   ├── vdrv_dp_if.h        # Data path interface (TX/RX, TID, DHCP, EAPOL)
│   ├── vdrv_cp_if.h        # Control path interface
│   └── vdrv_cp_if_*.h      # Other control path interfaces
└── qca/                    # QCA-specific implementations
    ├── common/             # Common QCA implementation
    │   └── vdrv_dp_if.c    # Wraps QCA wbuf functions
    ├── spf11_4/            # SPF 11.4 specific
    ├── spf12_2_csu2/       # SPF 12.2 CSU2 specific
    └── spf12_5_cs/         # SPF 12.5 CS specific
```

**Key Files:**

| File | Purpose |
|------|---------|
| `vdrv_dp_if.h` | Inline accessors for `ar_meta` (TID, DHCP, EAPOL) |
| `vdrv_dp_if.c` | Wrapper functions calling QCA `wbuf_*()` functions |
| `vdrv_cp_if.c` | Control path wrappers |

### Arista Interface (`ar/ar_if/`)

Interface between Arista core and the rest of the system.

```
ar_if/
├── inc/                    # Interface headers
└── qca/                    # QCA-specific glue code
    └── ar_dp_if.c          # Data path interface to QCA
```

---

## Qualcomm Driver Code (`QCA/`)

### Directory Structure

```
QCA/
├── licensed/                           # Licensed source code
│   ├── 11.0_sensor_spf10_cs/          # SPF 10 (Sensor platform)
│   ├── 11.0_sensor_spf11_csu2/        # SPF 11 CSU2
│   ├── 11.1_ap_spf11/                 # SPF 11 (AP platform)
│   ├── 11.1_sensor_spf11/             # SPF 11 Sensor
│   ├── 11.4_ap_spf11_csu1/            # SPF 11.4 CSU1
│   ├── spf12_2_csu2/                  # SPF 12.2 CSU2
│   └── spf12_5_cs/                    # SPF 12.5 CS (latest)
└── channel_lists/                      # Regulatory channel configs
    ├── ap/                             # AP channel lists
    └── sensor/                         # Sensor channel lists
```

### SPF Version Structure (Example: 11.0_sensor_spf10_cs)

```
11.0_sensor_spf10_cs/
├── cmn_dev/            # Common device code (CORE DRIVER)
│   ├── dp/             # Data Path (TX/RX, rings)
│   ├── hal/            # Hardware Abstraction Layer
│   ├── hif/            # Host Interface (PCIe/AHB)
│   ├── htc/            # Host-Target Communication
│   ├── qdf/            # Qualcomm Driver Framework
│   ├── wmi/            # Wireless Management Interface
│   └── ...
├── os/                 # OS-specific code
│   └── linux/          # Linux kernel integration
│       ├── src/        # Source files (osif_net.c, etc.)
│       └── include/    # Headers (wbuf.h, osdep_adf.h)
├── umac/               # Upper MAC
├── offload/            # Offload components
├── qca_ol/             # QCA offload module
├── include/            # Public headers
└── ...
```

### Key QCA Components

#### 1. Common Device (`cmn_dev/`)

| Folder | Purpose | Key Files |
|--------|---------|-----------|
| `dp/wifi3.0/` | **Data Path** - WiFi 3.0 (11ax) | `dp_tx.c`, `dp_rx.c`, `dp_main.c` |
| `hal/wifi3.0/` | **HAL** - Hardware Abstraction | `hal_srng.c`, `hal_tx.h`, `hal_rx.h` |
| `hif/` | Host Interface (PCIe/AHB bus) | Bus communication |
| `htc/` | Host-Target Communication | Message passing to firmware |
| `qdf/` | Qualcomm Driver Framework | OS abstraction (`qdf_nbuf`, etc.) |
| `wmi/` | Wireless Management Interface | Firmware commands/events |

#### 2. Data Path (`cmn_dev/dp/wifi3.0/`)

This is the **core TX/RX engine**:

| File | Purpose |
|------|---------|
| `dp_tx.c` | **TX path** - Submit packets to hardware |
| `dp_rx.c` | **RX path** - Process received packets |
| `dp_main.c` | DP initialization and setup |
| `dp_peer.c` | Peer (client) management |
| `dp_htt.c` | Host-Target TX/RX |
| `dp_types.h` | Data structures (`dp_srng`, `dp_soc`, etc.) |

#### 3. HAL (`cmn_dev/hal/wifi3.0/`)

Hardware Abstraction Layer - interfaces with silicon:

| File | Purpose |
|------|---------|
| `hal_srng.c` | **SRNG** - Ring buffer operations |
| `hal_tx.h` | TX descriptor programming |
| `hal_rx.h` | RX descriptor parsing |
| `hal_reo.c` | **REO** - Reorder Engine operations |
| `hal_wbm.h` | **WBM** - WiFi Buffer Manager |
| `hal_api.h` | Ring type definitions |

#### 4. OS Linux Layer (`os/linux/`)

Linux-specific integration:

| File | Purpose |
|------|---------|
| `src/osif_net.c` | **Creates wifiX/athX** net_devices |
| `src/ieee80211_wireless.c` | WEXT/cfg80211 integration |
| `include/osdep_adf.h` | `struct ieee80211_cb`, N_FLAG macros |
| `include/wbuf_adf_private.h` | `wbuf_*()` inline functions |
| `include/wbuf_private.h` | wbuf structure definitions |

#### 5. UMAC (`umac/`)

Upper MAC - 802.11 protocol implementation:

| Folder | Purpose |
|--------|---------|
| `base/` | Base 802.11 functionality |
| `mlme/` | MLME - Management Layer |
| `crypto/` | Encryption/Decryption |
| `scan/` | Scanning |
| `acl/` | Access Control Lists |
| `acs/` | Automatic Channel Selection |
| `txrx/` | TX/RX data path |

---

## Data Flow: Arista ↔ QCA Interaction

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           TX DATA FLOW                                      │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  Linux Kernel (netif_rx)                                                    │
│       │                                                                     │
│       ▼                                                                     │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ osif_vap_hardstart()        [QCA: os/linux/src/ieee80211_wireless.c]│   │
│  │    │                                                                 │   │
│  │    ▼                                                                 │   │
│  │ ar_dp_if_tx_handle()        [ARISTA: ar/ar_if/qca/ar_dp_if.c]       │   │
│  │    │                                                                 │   │
│  │    ▼                                                                 │   │
│  │ ar_dp_tx_handle()           [ARISTA: ar/core/src/ar_dp.c]           │   │
│  │    │                                                                 │   │
│  │    ├─ ar_dp_classify_skb()  → Set TID, DHCP, EAPOL in ar_meta + CB  │   │
│  │    │                                                                 │   │
│  │    ▼                                                                 │   │
│  │ vdrv_dp_if_tx_send()        [ARISTA: ar/vdrv_if/qca/.../vdrv_dp_if.c]│  │
│  │    │                                                                 │   │
│  │    ▼                                                                 │   │
│  │ dp_tx_send()                [QCA BINARY: cmn_dev/dp/wifi3.0/dp_tx.c]│   │
│  │    │                                                                 │   │
│  │    ├─ Read TID from skb->cb (ieee80211_cb)                          │   │
│  │    ├─ DMA map skb->data                                              │   │
│  │    ├─ Fill TCL descriptor                                            │   │
│  │    └─ Submit to TCL ring                                             │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│       │                                                                     │
│       ▼                                                                     │
│  WiFi Hardware (Over-the-Air)                                              │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│                           RX DATA FLOW                                      │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  WiFi Hardware (Received frame)                                            │
│       │                                                                     │
│       ▼                                                                     │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ dp_rx_process()             [QCA BINARY: cmn_dev/dp/wifi3.0/dp_rx.c]│   │
│  │    │                                                                 │   │
│  │    ├─ Read TID from REO descriptor (hardware)                       │   │
│  │    ├─ Set QDF_NBUF_CB_RX_TID_VAL(skb)                               │   │
│  │    ├─ DMA unmap                                                      │   │
│  │    │                                                                 │   │
│  │    ▼                                                                 │   │
│  │ ar_dp_if_rx_handle()        [ARISTA: ar/ar_if/qca/ar_dp_if.c]       │   │
│  │    │                                                                 │   │
│  │    ▼                                                                 │   │
│  │ ar_dp_rx_handle()           [ARISTA: ar/core/src/ar_dp.c]           │   │
│  │    │                                                                 │   │
│  │    ├─ Read TID from CB (set by QCA binary)                          │   │
│  │    ├─ Process, filter, stats                                         │   │
│  │    │                                                                 │   │
│  │    ▼                                                                 │   │
│  │ netif_rx() / netif_receive_skb()                                    │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│       │                                                                     │
│       ▼                                                                     │
│  Linux Kernel Network Stack                                                │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Key Header Files Reference

### Arista Headers

| Header | Location | Purpose |
|--------|----------|---------|
| `vdrv_dp_if.h` | `ar/vdrv_if/inc/` | ar_meta inline accessors |
| `ar_dp.h` | `ar/core/src/` | Data path declarations |
| `ar_qos.h` | `ar/core/src/` | QoS/TID declarations |
| `ar_types.h` | `ar/core/src/` | Common type definitions |

### QCA Headers (Used by Arista)

| Header | Location | Purpose |
|--------|----------|---------|
| `osdep_adf.h` | `os/linux/include/` | `struct ieee80211_cb`, N_FLAG macros |
| `wbuf_adf_private.h` | `os/linux/include/` | `wbuf_*()` inline functions |
| `wbuf.h` | `include/` | wbuf type definitions |
| `qdf_nbuf.h` | `cmn_dev/qdf/inc/` | `qdf_nbuf_t` (skb wrapper) |
| `cdp_txrx_cmn.h` | `cmn_dev/dp/inc/` | CDP (Common Data Path) APIs |
| `hal_api.h` | `cmn_dev/hal/wifi3.0/` | HAL ring types and APIs |
| `dp_types.h` | `cmn_dev/dp/wifi3.0/` | DP structures |

---

## SPF Version Differences

| Version | Platform | Key Features |
|---------|----------|--------------|
| `11.0_sensor_spf10_cs` | Sensor | WiFi 6 (11ax), IPQ8074 |
| `11.0_sensor_spf11_csu2` | Sensor | Bug fixes, security updates |
| `11.1_ap_spf11` | AP | Full AP features |
| `11.1_sensor_spf11` | Sensor | Sensor-optimized |
| `11.4_ap_spf11_csu1` | AP | CSU1 updates |
| `spf12_2_csu2` | AP | WiFi 6E support |
| `spf12_5_cs` | AP | Latest, WiFi 6E/7 |

**Note:** Different SPF versions may have different APIs. The `vdrv_if/qca/`
folder has version-specific implementations (spf11_4, spf12_2_csu2, spf12_5_cs).

---

## What Can/Cannot Be Modified

### ✅ Can Modify (Arista Code)

| Component | Files | Examples |
|-----------|-------|----------|
| Core logic | `ar/core/src/*.c` | Add ar_meta caching |
| Vendor interface | `ar/vdrv_if/qca/**/*.c` | Wrap QCA functions |
| Arista interface | `ar/ar_if/**/*.c` | Custom hooks |
| OS interface | `ar/os_if/*.c` | Linux-specific |
| Utilities | `ar/utils/**/*.c` | Helper functions |

### ⚠️ Use But Don't Modify (QCA Headers)

| Component | Files | Notes |
|-----------|-------|-------|
| wbuf inline functions | `wbuf_adf_private.h` | Compiled into our code |
| CB structure | `osdep_adf.h` | `struct ieee80211_cb` |
| QDF wrappers | `qdf_nbuf.h` | nbuf operations |
| Flag macros | `osdep_adf.h` | N_EAPOL, N_DHCP, etc. |

### ❌ Cannot Modify (QCA Binary)

| Component | Files | Reason |
|-----------|-------|--------|
| TX datapath | `dp_tx.c` → `dp_tx.o` | Pre-compiled binary |
| RX datapath | `dp_rx.c` → `dp_rx.o` | Pre-compiled binary |
| HAL | `hal_srng.c` → `.o` | Hardware-specific |
| Ring management | All HAL files | Closed source |

---

## Build Integration

```
Build Order:
1. QCA driver modules compile first (provides .o files and headers)
2. Arista ar/ code compiles using QCA headers
3. Final kernel module(s) link together

Makefile Files:
- ar/Makefile.sdk           # Arista build
- ar/arwlandrv.mk           # Arista driver make rules
- QCA/.../Makefile          # QCA build
- QCA/.../Makefile.sdk      # QCA SDK build
```

---

## Quick Reference: Where to Find Things

| Looking For | Location |
|-------------|----------|
| TX/RX handling | `ar/core/src/ar_dp.c` |
| TID/QoS logic | `ar/core/src/ar_qos.c` |
| ar_meta accessors | `ar/vdrv_if/inc/vdrv_dp_if.h` |
| Vendor wrapper | `ar/vdrv_if/qca/common/vdrv_dp_if.c` |
| wbuf functions | `QCA/.../os/linux/include/wbuf_adf_private.h` |
| CB flags | `QCA/.../os/linux/include/osdep_adf.h` |
| DP TX code (QCA) | `QCA/.../cmn_dev/dp/wifi3.0/dp_tx.c` |
| DP RX code (QCA) | `QCA/.../cmn_dev/dp/wifi3.0/dp_rx.c` |
| Ring structures | `QCA/.../cmn_dev/dp/wifi3.0/dp_types.h` |
| HAL ring ops | `QCA/.../cmn_dev/hal/wifi3.0/hal_srng.c` |
| Net device creation | `QCA/.../os/linux/src/osif_net.c` |
| wifiX/athX ops | `QCA/.../os/linux/src/ieee80211_wireless.c` |




