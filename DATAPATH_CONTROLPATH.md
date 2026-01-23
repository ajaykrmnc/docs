# Data Path (DP) and Control Path (CP) Architecture

This document describes the Data Path (DP) and Control Path (CP) architecture in the Arista AP WLAN driver stack.

## Overview

The WLAN driver architecture separates packet handling into two distinct paths:

- **Data Path (DP)**: High-performance TX/RX packet processing for user data traffic
- **Control Path (CP)**: Management frame handling, configuration, and control operations

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        WLAN Driver Architecture                             │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌────────────────────────────┐     ┌────────────────────────────┐         │
│  │      DATA PATH (DP)        │     │     CONTROL PATH (CP)      │         │
│  ├────────────────────────────┤     ├────────────────────────────┤         │
│  │ • TX/RX packet processing  │     │ • Management frames        │         │
│  │ • QoS/TID handling         │     │ • Configuration updates    │         │
│  │ • VLAN tagging             │     │ • Client steering          │         │
│  │ • Multicast enhancement    │     │ • Statistics collection    │         │
│  │ • ACL filtering            │     │ • Event handling           │         │
│  │ • ARP/DHCP inspection      │     │ • Peer management          │         │
│  └────────────────────────────┘     └────────────────────────────┘         │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Data Path (DP)

### Purpose

The Data Path handles high-throughput packet forwarding for user data traffic between wireless clients and the network.

### Key Components

| File | Purpose |
|------|---------|
| `ar/core/src/ar_dp.c` | Core data path TX/RX handling |
| `ar/core/src/ar_dp.h` | Data path declarations and inline accessors |
| `ar/core/src/ar_qos.c` | QoS and TID/AC mapping |
| `ar/vdrv_if/inc/vdrv_dp_if.h` | Vendor driver data path interface |
| `ar/vdrv_if/qca/common/vdrv_dp_if.c` | QCA-specific DP implementation |
| `ar/ar_if/qca/common/ar_dp_if.c` | Arista-QCA interface layer |

### Key Functions

| Function | Description |
|----------|-------------|
| `ar_dp_tx_handle()` | Main TX packet processing entry point |
| `ar_dp_rx_handle()` | Main RX packet processing entry point |
| `ar_dp_rx_process_pkt()` | Per-packet RX processing (DHCP, EAPOL, ACL) |
| `ar_dp_classify_skb()` | Classify packets for QoS (set TID, DHCP, EAPOL flags) |
| `vdrv_dp_if_tx_send()` | Send packet to vendor driver |

### TX Data Flow

```
Linux Kernel (netif_rx)
    │
    ▼
osif_vap_hardstart()        [QCA: os/linux/src/ieee80211_wireless.c]
    │
    ▼
ar_dp_if_tx_handle()        [Arista: ar/ar_if/qca/ar_dp_if.c]
    │
    ▼
ar_dp_tx_handle()           [Arista: ar/core/src/ar_dp.c]
    │
    ├─ ar_dp_classify_skb()  → Set TID, DHCP, EAPOL in ar_meta + CB
    │
    ▼
vdrv_dp_if_tx_send()        [Arista: ar/vdrv_if/qca/.../vdrv_dp_if.c]
    │
    ▼
dp_tx_send()                [QCA Binary: cmn_dev/dp/wifi3.0/dp_tx.c]
    │
    ▼
WiFi Hardware (Over-the-Air)
```

### RX Data Flow

```
WiFi Hardware (Received frame)
    │
    ▼
dp_rx_process()             [QCA Binary: cmn_dev/dp/wifi3.0/dp_rx.c]
    │
    ├─ Read TID from REO descriptor (hardware)
    ├─ Set QDF_NBUF_CB_RX_TID_VAL(skb)
    │
    ▼
ar_dp_if_rx_handle()        [Arista: ar/ar_if/qca/ar_dp_if.c]
    │
    ▼
ar_dp_rx_handle()           [Arista: ar/core/src/ar_dp.c]
    │
    ├─ Read TID from CB (set by QCA binary)
    ├─ Process, filter, stats
    │
    ▼
netif_rx() / netif_receive_skb()
    │
    ▼
Linux Kernel Network Stack
```

### Data Path Features

- **QoS Handling**: TID/AC mapping for traffic prioritization
- **VLAN Support**: Per-client and per-VAP VLAN tagging
- **ACL Filtering**: Client-level access control lists
- **Multicast Enhancement (ME)**: Convert multicast to unicast for performance
- **DHCP/EAPOL Detection**: Special handling for control-plane packets
- **ARP Inspection**: Proxy ARP and ARP filtering
- **IPv6 Processing**: RA/NA handling, IPv6 filtering

## Control Path (CP)

### Purpose

The Control Path handles management frames, configuration, and control operations that don't require high-throughput processing.

### Key Components

| File | Purpose |
|------|---------|
| `ar/core/src/ar_cp.c` | Core control path logic |
| `ar/core/src/ar_cp.h` | Control path declarations |
| `ar/vdrv_if/inc/vdrv_cp_if.h` | Vendor driver control path interface |
| `ar/vdrv_if/qca/common/vdrv_cp_if.c` | QCA-specific CP implementation |
| `ar/core/src/ar_evt.c` | Event handling |
| `ar/core/src/ar_cfg.c` | Configuration management |
| `ar/core/src/ar_mgmt_ap.c` | AP management operations |

### Key Functions

| Function | Description |
|----------|-------------|
| `ar_cp_global_init()` | Initialize global CP state |
| `ar_cp_pdev_init()` | Per-radio CP initialization |
| `ar_cp_set_flags()` | Set control flags (band steering, etc.) |
| `ar_cp_set_rf_clients_params()` | Configure RF client parameters |
| `ar_cp_update_clperfrec()` | Update client performance records |
| `vdrv_cp_if_get_peer_obj_from_dp_psoc()` | Get control path peer from data path |

### Control Path Features

- **Band Steering**: Move clients between 2.4/5/6 GHz bands
- **Smart Steering**: Load-based client steering
- **Client Statistics**: Performance metrics collection
- **11v BSS Transition**: Managed client roaming
- **Beacon Updates**: Dynamic beacon IE management
- **Channel Scanning**: Off-channel and background scanning
- **WNM (Wireless Network Management)**: 802.11v support
- **Hotspot 2.0**: Passpoint configuration

## Vendor Driver Interface Layers

Both DP and CP have corresponding vendor interface layers that abstract QCA-specific implementations:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                     Vendor Driver Interface Structure                       │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  vdrv_if/                                                                   │
│  ├── inc/                          # Vendor-agnostic headers                │
│  │   ├── vdrv_dp_if.h              # Data path interface                    │
│  │   ├── vdrv_cp_if.h              # Control path interface                 │
│  │   └── vdrv_cp_if_*.h            # Extended CP interfaces                 │
│  └── qca/                          # QCA-specific implementations           │
│      ├── common/                   # Common QCA implementation              │
│      │   ├── vdrv_dp_if.c          # DP wrapper (wbuf functions)            │
│      │   └── vdrv_cp_if.c          # CP wrappers                            │
│      ├── spf11_4/                  # SPF 11.4 specific                      │
│      ├── spf12_2_csu2/             # SPF 12.2 CSU2 specific                 │
│      └── spf12_5_cs/               # SPF 12.5 CS specific                   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Object Hierarchy

Both DP and CP maintain parallel object hierarchies attached to QCA objects:

```
QCA Object Manager              Arista Extensions
─────────────────               ─────────────────
wlan_objmgr_psoc    ◄──────►    ar_psoc / ar_dp_soc_s
        │
        ▼
wlan_objmgr_pdev    ◄──────►    ar_pdev / ar_dp_pdev_s
        │
        ▼
wlan_objmgr_vdev    ◄──────►    ar_vdev / ar_dp_vdev_s
        │
        ▼
wlan_objmgr_peer    ◄──────►    ar_peer / ar_dp_peer_s
```

## DP vs CP: When to Use Which

| Use Data Path (DP) | Use Control Path (CP) |
|--------------------|----------------------|
| User data packets | Management frames |
| Per-packet operations | Per-client configuration |
| High-frequency calls | Low-frequency operations |
| TX/RX handlers | IOCTLs and netlink |
| QoS classification | Statistics collection |
| ACL enforcement | Steering decisions |

## Key Header Files

### Data Path Headers

| Header | Purpose |
|--------|---------|
| `ar/core/src/ar_dp.h` | DP constants, macros, accessors |
| `ar/vdrv_if/inc/vdrv_dp_if.h` | ar_meta cache, SKB metadata |
| `ar/core/src/ar_qos.h` | TID/AC mapping declarations |

### Control Path Headers

| Header | Purpose |
|--------|---------|
| `ar/core/src/ar_cp.h` | CP flags, steering constants |
| `ar/vdrv_if/inc/vdrv_cp_if.h` | PHY modes, crypto params |
| `ar/core/src/ar_evt.h` | Event type definitions |

## Related Documentation

- [QCA_ARISTA_INTEGRATION.md](QCA_ARISTA_INTEGRATION.md) - QCA driver integration details
- [ar/docs/codebase_structure.md](../ap/src/wlan-drivers/ar/docs/codebase_structure.md) - Detailed codebase structure
- [ar/docs/skb_tid_metadata_flow.md](../ap/src/wlan-drivers/ar/docs/skb_tid_metadata_flow.md) - SKB metadata handling

