# WLAN Drivers Terminology and Architecture

## Table of Contents
1. [Overview](#overview)
2. [Object Hierarchy](#object-hierarchy)
3. [Core Terminology](#core-terminology)
4. [Driver Architecture Layers](#driver-architecture-layers)
5. [802.11 Frame Types](#80211-frame-types)
6. [Data Path Architecture](#data-path-architecture)
7. [Packet Units and Aggregation](#packet-units-and-aggregation)
8. [Communication Interfaces](#communication-interfaces)
9. [Kernel Modules](#kernel-modules)
10. [Frequency Bands and Channels](#frequency-bands-and-channels)
11. [Channel Widths and PHY Modes](#channel-widths-and-phy-modes)
12. [Security and Authentication](#security-and-authentication)
13. [Roaming and Mobility](#roaming-and-mobility)
14. [APC (AP Capture) Subsystem](#apc-ap-capture-subsystem)
15. [Additional Terminology](#additional-terminology)
16. [Arista-Specific Components](#arista-specific-components)
17. [hostapd Integration](#hostapd-integration)

---

## Overview

This document provides comprehensive coverage of the terminology, architecture, and components used in the 
WLAN (Wireless Local Area Network) driver stack. It covers the QCA (Qualcomm/Atheros) driver architecture, 
802.11 protocols, the APC (AP Capture) subsystem, and Arista-specific extensions.

The WLAN driver stack is a complex layered architecture that bridges user-space applications (like hostapd) 
with the wireless hardware, handling everything from packet transmission/reception to security, roaming, and 
regulatory compliance.

---

## Object Hierarchy

The WLAN driver uses a hierarchical object model representing the physical and logical components:

```
PSOC (Physical SoC) ─────────────────────────────────────────────────┐
│                                                                     │
├── PDEV 0 (2.4GHz Radio) ────────────────────────────────────────┐  │
│   ├── VDEV 0 (AP Mode - SSID "Corporate")                       │  │
│   │   ├── PEER 0 (Client AA:BB:CC:DD:EE:01)                     │  │
│   │   ├── PEER 1 (Client AA:BB:CC:DD:EE:02)                     │  │
│   │   └── BSS PEER (Self - BSSID)                               │  │
│   ├── VDEV 1 (AP Mode - SSID "Guest")                           │  │
│   │   └── PEER 0 (Client AA:BB:CC:DD:EE:03)                     │  │
│   └── VDEV 2 (Monitor Mode)                                     │  │
│                                                                  │  │
├── PDEV 1 (5GHz Radio) ──────────────────────────────────────────┤  │
│   ├── VDEV 3 (AP Mode - SSID "Corporate")                       │  │
│   │   └── PEER 0 (Client AA:BB:CC:DD:EE:04)                     │  │
│   └── VDEV 4 (AP Mode - SSID "IoT")                             │  │
│                                                                  │  │
└── PDEV 2 (6GHz Radio) ──────────────────────────────────────────┤  │
└── VDEV 5 (AP Mode - SSID "WiFi7")                           │  │
└── PEER 0 (Client AA:BB:CC:DD:EE:05)                     │  │
│  │
───────────────────────────────────────────────────────────────────┘  │
│
──────────────────────────────────────────────────────────────────────┘
```

### Object Relationships

| Parent | Child | Relationship |
|--------|-------|--------------|
| PSOC | PDEV | 1:N (typically 1-3 radios) |
| PDEV | VDEV | 1:N (multiple VAPs per radio) |
| VDEV | PEER | 1:N (multiple clients per VAP) |

---

## Core Terminology

### PSOC (Physical System-on-Chip)
- **Definition**: Represents the entire wireless SoC (System-on-Chip)
- **Scope**: Top-level object containing all PDEVs
- **Responsibilities**:
  - Global driver state management
  - Resource allocation across radios
  - Firmware interface initialization
  - Component registration (MLME, scan, crypto, etc.)

### PDEV (Physical Device)
- **Definition**: Represents a **physical radio interface** (actual hardware)
- **Correspondence**: Maps to a radio chip or band (2.4GHz, 5GHz, 6GHz)
- **Key Attributes**:

| Attribute | Description |
|-----------|-------------|
| `pdev_id` | Unique identifier (typically 0-2) |
| `hw_macaddr` | Hardware MAC address of the radio |
| `current_chan_list` | Supported channel list |
| `max_vdev_count` | Maximum VDEVs allowed |
| `wlan_peer_count` | Total peers across all VDEVs |

- **Key Flags**:

| Flag | Purpose |
|------|---------|
| `WLAN_PDEV_F_SCAN` | Radio is scanning |
| `WLAN_PDEV_F_RADAR` | Radar detected |
| `WLAN_PDEV_F_DFS_CHANSWITCH_PENDING` | DFS channel switch pending |
| `WLAN_PDEV_F_AMPDU` | A-MPDU supported |
| `WLAN_PDEV_F_AMSDU` | A-MSDU supported |

### VDEV (Virtual Device) / VAP (Virtual Access Point)
- **Definition**: Represents a **virtual/logical network interface** on top of a PDEV
- **Key Feature**: Multiple VDEVs can share the same physical radio
- **Key Attributes**:

| Attribute | Description |
|-----------|-------------|
| `vdev_id` | Unique identifier within PSOC (0-255) |
| `opmode` | Operating mode (AP, STA, Monitor) |
| `bss_chan` | Currently operating channel |
| `des_chan` | Desired/target channel |
| `macaddr` | BSSID (MAC address) |
| `mldaddr` | MLD address (Wi-Fi 7) |

- **Operation Modes (QDF_OPMODE)**:

| Mode | Value | Description |
|------|-------|-------------|
| `QDF_STA_MODE` | 0 | Station/Client mode |
| `QDF_SAP_MODE` | 1 | SoftAP/Access Point mode |
| `QDF_P2P_CLIENT_MODE` | 2 | P2P Client |
| `QDF_P2P_GO_MODE` | 3 | P2P Group Owner |
| `QDF_IBSS_MODE` | 6 | Ad-hoc mode |
| `QDF_MONITOR_MODE` | 7 | Packet capture/sniffer mode |
| `QDF_WDS_MODE` | 8 | Wireless Distribution System |
| `QDF_NDI_MODE` | 12 | NAN Data Interface |

### PEER / NODE (ieee80211_node)
- **Definition**: Represents a connected station/client
- **Association**: Linked to a specific VDEV
- **Stored State**:
  - MAC address
  - Capabilities (HT, VHT, HE, EHT)
  - Power save state
  - Security context (PTK, GTK)
  - QoS/TID state
  - Rate adaptation state

---

## Driver Architecture Layers

```
┌─────────────────────────────────────────────────────────────────────┐
│                     User Space Applications                         │
│                  (hostapd, wpa_supplicant, wlanconfig)              │
└─────────────────────────────────────────────────────────────────────┘
│ IOCTL/Netlink
┌─────────────────────────────────────────────────────────────────────┐
│                         OS Interface (OSIF)                         │
│                    (Linux netdevice interface)                      │
└─────────────────────────────────────────────────────────────────────┘
│
┌─────────────────────────────────────────────────────────────────────┐
│                     UMAC (Upper MAC Layer)                          │
│  ┌──────────┬──────────┬──────────┬──────────┬──────────┐          │
│  │   MLME   │   Scan   │   ACL    │   Crypto │   QoS    │          │
│  └──────────┴──────────┴──────────┴──────────┴──────────┘          │
│  ┌──────────┬──────────┬──────────┬──────────┬──────────┐          │
│  │   RRM    │   WNM    │   SON    │   DFS    │ Spectral │          │
│  └──────────┴──────────┴──────────┴──────────┴──────────┘          │
└─────────────────────────────────────────────────────────────────────┘
│
┌─────────────────────────────────────────────────────────────────────┐
│                    QCA Offload Layer (QCA_OL)                       │
│              (Target Interface, WMI, Offload management)            │
└─────────────────────────────────────────────────────────────────────┘
│
┌─────────────────────────────────────────────────────────────────────┐
│                      Data Path (DP/TXRX)                            │
│           (High-performance TX/RX packet processing)                │
└─────────────────────────────────────────────────────────────────────┘
│ WMI/HTT
┌─────────────────────────────────────────────────────────────────────┐
│                         Firmware (Target)                           │
│                    (Running on WiFi chipset)                        │
└─────────────────────────────────────────────────────────────────────┘
│
┌─────────────────────────────────────────────────────────────────────┐
│                        Hardware (PHY/RF)                            │
└─────────────────────────────────────────────────────────────────────┘
```

### UMAC (Upper MAC)
Upper MAC layer handling 802.11 protocol:

| Component | Description |
|-----------|-------------|
| **MLME** | MAC Layer Management Entity - state machines for association, authentication |
| **Scan** | Channel scanning, BSS discovery |
| **ACL** | Access Control Lists - MAC filtering |
| **Crypto** | Encryption/decryption (WEP, TKIP, CCMP, GCMP) |
| **QoS** | Quality of Service, WMM, admission control |
| **RRM** | Radio Resource Management (802.11k) |
| **WNM** | Wireless Network Management (802.11v) |
| **SON** | Self-Organizing Networks (mesh) |
| **DFS** | Dynamic Frequency Selection |
| **Spectral** | RF spectrum analysis |

### LMAC (Lower MAC)
Lower MAC layer closer to hardware:

| Component | Description |
|-----------|-------------|
| Rate Control | Adaptive rate selection |
| TX Scheduling | Transmission scheduling and queuing |
| HAL | Hardware Abstraction Layer |
| DA Support | Direct Attach for legacy hardware |

### QDF (QCA Driver Framework)
OS abstraction layer providing platform-independent APIs:

| API Category | Examples |
|--------------|----------|
| Memory | `qdf_mem_malloc()`, `qdf_mem_free()` |
| Timers | `qdf_timer_init()`, `qdf_timer_start()` |
| Spinlocks | `qdf_spinlock_create()`, `qdf_spin_lock()` |
| Network Buffer | `qdf_nbuf_alloc()`, `qdf_nbuf_free()` |
| Debug/Trace | `qdf_print()`, `qdf_trace()` |
| Events | `qdf_event_create()`, `qdf_event_set()` |

### ASF (Atheros Service Framework)
Service framework for common utilities:
- Print/logging infrastructure
- Debug facilities
- Common data structures

### QCA_OL (QCA Offload)
Offload layer for modern chipsets:
- Target Interface (TGT_IF) management
- WMI command/event processing
- Firmware download and management

---

## 802.11 Frame Types

### Frame Type Overview

802.11 frames are categorized into three main types:

```
┌─────────────────────────────────────────────────────────────────────┐
│                        802.11 Frame Types                           │
├─────────────────────────────────────────────────────────────────────┤
│  Type 0: MANAGEMENT (0x00)                                          │
│    - Beacon, Probe Request/Response                                 │
│    - Authentication, Deauthentication                               │
│    - Association, Reassociation, Disassociation                     │
│    - Action frames                                                  │
├─────────────────────────────────────────────────────────────────────┤
│  Type 1: CONTROL (0x01)                                             │
│    - RTS, CTS, ACK                                                  │
│    - Block Ack, Block Ack Request                                   │
│    - PS-Poll, CF-End                                                │
├─────────────────────────────────────────────────────────────────────┤
│  Type 2: DATA (0x02)                                                │
│    - Data, QoS Data                                                 │
│    - Null Data, QoS Null                                            │
└─────────────────────────────────────────────────────────────────────┘
```

### Management Frame Subtypes

| Subtype | Value | Description |
|---------|-------|-------------|
| Association Request | 0x00 | Client requests association |
| Association Response | 0x01 | AP responds to association request |
| Reassociation Request | 0x02 | Client requests reassociation (roaming) |
| Reassociation Response | 0x03 | AP responds to reassociation |
| Probe Request | 0x04 | Client scans for networks |
| Probe Response | 0x05 | AP responds with network info |
| Timing Advertisement | 0x06 | Timing synchronization |
| Beacon | 0x08 | Periodic AP announcement |
| ATIM | 0x09 | Announcement Traffic Indication |
| Disassociation | 0x0A | Terminate association |
| Authentication | 0x0B | Authentication exchange |
| Deauthentication | 0x0C | Terminate authentication |
| Action | 0x0D | Various action frames (RRM, WNM, etc.) |
| Action No Ack | 0x0E | Action without acknowledgment |

### Control Frame Subtypes

| Subtype | Value | Description |
|---------|-------|-------------|
| Block Ack Request (BAR) | 0x08 | Request block acknowledgment |
| Block Ack (BA) | 0x09 | Block acknowledgment |
| PS-Poll | 0x0A | Power save poll |
| RTS | 0x0B | Request to Send |
| CTS | 0x0C | Clear to Send |
| ACK | 0x0D | Acknowledgment |
| CF-End | 0x0E | Contention-Free End |
| CF-End + CF-Ack | 0x0F | CF-End with Ack |

### Data Frame Subtypes

| Subtype | Value | Description |
|---------|-------|-------------|
| Data | 0x00 | Standard data frame |
| Data + CF-Ack | 0x01 | Data with CF acknowledgment |
| Data + CF-Poll | 0x02 | Data with CF poll |
| Null | 0x04 | No data (power management) |
| QoS Data | 0x08 | QoS data frame |
| QoS Null | 0x0C | QoS null (power management) |

### Frame Control Field

```
0                   1                   2
0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1 2 3
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|Protocol |Type |  Subtype  |To |From|More|Retry|
| Version |     |           |DS |DS  |Frag|     |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|Pwr |More|Protected|+HTC/  |
|Mgmt|Data|Frame    |Order  |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
```

| Field | Bits | Description |
|-------|------|-------------|
| Protocol Version | 2 | Always 0 for current 802.11 |
| Type | 2 | 0=Mgmt, 1=Ctrl, 2=Data |
| Subtype | 4 | Frame subtype |
| To DS | 1 | Frame going to Distribution System |
| From DS | 1 | Frame coming from Distribution System |
| More Fragments | 1 | More fragments follow |
| Retry | 1 | Retransmission |
| Power Management | 1 | Power save mode |
| More Data | 1 | More data buffered |
| Protected Frame | 1 | Frame is encrypted |
| +HTC/Order | 1 | HT Control present / Strictly ordered |

### Address Fields (To DS / From DS)

| To DS | From DS | Address 1 | Address 2 | Address 3 | Address 4 |
|-------|---------|-----------|-----------|-----------|-----------|
| 0 | 0 | DA | SA | BSSID | N/A |
| 0 | 1 | DA | BSSID | SA | N/A |
| 1 | 0 | BSSID | SA | DA | N/A |
| 1 | 1 | RA | TA | DA | SA |

- **DA**: Destination Address
- **SA**: Source Address
- **RA**: Receiver Address
- **TA**: Transmitter Address
- **BSSID**: Basic Service Set Identifier

---

## Data Path Architecture

### Control Path (CP) vs Data Path (DP)

```
┌─────────────────────────────────────────────────────────────────────┐
│                        Control Path (CP)                            │
│  - Configuration and management                                     │
│  - Association/Authentication                                       │
│  - Band steering, smart steering                                    │
│  - WNM, RRM operations                                              │
│  - Low frequency, high latency OK                                   │
│  Key structures: ar_pdev_s, ar_vdev_s, ar_peer_s                    │
└─────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────┐
│                         Data Path (DP)                              │
│  - High-performance packet forwarding                               │
│  - TX/RX packet processing                                          │
│  - Aggregation (A-MPDU, A-MSDU)                                     │
│  - High frequency, low latency required                             │
│  Key structures: ar_dp_soc_s, ar_dp_pdev_s, ar_dp_vdev_s            │
└─────────────────────────────────────────────────────────────────────┘
```

### TX Data Path

```
Application → Socket → Network Stack → netdev TX
│
▼
┌───────────────────┐
│   OSIF TX Entry   │
│  (os_if_tx_data)  │
└─────────┬─────────┘
│
▼
┌───────────────────┐
│   UMAC TX Path    │
│  - Encryption     │
│  - QoS mapping    │
│  - Fragmentation  │
└─────────┬─────────┘
│
▼
┌───────────────────┐
│   DP TX Path      │
│  - Aggregation    │
│  - Rate control   │
│  - Queuing        │
└─────────┬─────────┘
│
▼
┌───────────────────┐
│   HTT TX         │
│  (Host→Target)   │
└─────────┬─────────┘
│
▼
┌───────────────────┐
│   Firmware TX     │
│  - Final TX       │
│  - Retries        │
└───────────────────┘
```

### RX Data Path

```
┌───────────────────┐
│   Firmware RX     │
│  - Decryption     │
│  - Deaggregation  │
└─────────┬─────────┘
│
▼
┌───────────────────┐
│   HTT RX         │
│  (Target→Host)   │
└─────────┬─────────┘
│
▼
┌───────────────────┐
│   DP RX Path      │
│  - Reorder        │
│  - Defragment     │
│  - APC capture    │
└─────────┬─────────┘
│
▼
┌───────────────────┐
│   UMAC RX Path    │
│  - Frame classify │
│  - MLME handling  │
└─────────┬─────────┘
│
▼
┌───────────────────┐
│   OSIF RX Entry   │
│  (netif_rx)       │
└─────────┬─────────┘
│
▼
Network Stack → Socket → Application
```

---

## Packet Units and Aggregation

### Packet Unit Hierarchy

```
┌─────────────────────────────────────────────────────────────────────┐
│                    PPDU (Physical Protocol Data Unit)               │
│  - Transmitted over the air as a single PHY burst                   │
│  - Contains preamble, header, and one or more MPDUs                 │
├─────────────────────────────────────────────────────────────────────┤
│  ┌───────────────────────────────────────────────────────────────┐  │
│  │              MPDU (MAC Protocol Data Unit)                    │  │
│  │  - Single 802.11 frame with MAC header                        │  │
│  │  - May contain one or more MSDUs (via A-MSDU)                 │  │
│  ├───────────────────────────────────────────────────────────────┤  │
│  │  ┌─────────────────────────────────────────────────────────┐  │  │
│  │  │           MSDU (MAC Service Data Unit)                  │  │  │
│  │  │  - Payload from upper layers (Ethernet frame)           │  │  │
│  │  │  - Maximum size: 2304 bytes (without encryption)        │  │  │
│  │  └─────────────────────────────────────────────────────────┘  │  │
│  └───────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────┘
```

### Aggregation Types

#### A-MPDU (Aggregated MPDU)
- **Definition**: Multiple MPDUs aggregated into a single PPDU
- **Benefit**: Reduces PHY overhead (preamble, headers)
- **Max Size**: Up to 1MB (802.11be), 4MB (802.11ax), 1MB (802.11ac)
- **Block Ack**: Receiver sends single Block Ack for all MPDUs

```
┌─────────────────────────────────────────────────────────────────────┐
│                         A-MPDU Structure                            │
├─────────────────────────────────────────────────────────────────────┤
│ ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐        │
│ │ MPDU 1  │ │ MPDU 2  │ │ MPDU 3  │ │ MPDU 4  │ │ MPDU N  │        │
│ │(Delim)  │ │(Delim)  │ │(Delim)  │ │(Delim)  │ │(Delim)  │        │
│ └─────────┘ └─────────┘ └─────────┘ └─────────┘ └─────────┘        │
└─────────────────────────────────────────────────────────────────────┘
```

#### A-MSDU (Aggregated MSDU)
- **Definition**: Multiple MSDUs aggregated into a single MPDU
- **Benefit**: Reduces MAC header overhead
- **Max Size**: 3839 bytes (HT), 7935 bytes (VHT/HE)
- **Limitation**: All MSDUs must have same TID and destination

```
┌─────────────────────────────────────────────────────────────────────┐
│                         A-MSDU Structure                            │
├─────────────────────────────────────────────────────────────────────┤
│ ┌──────────────────────────────────────────────────────────────┐   │
│ │                    Single MPDU Header                        │   │
│ ├──────────────────────────────────────────────────────────────┤   │
│ │ ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐         │   │
│ │ │ Subframe │ │ Subframe │ │ Subframe │ │ Subframe │         │   │
│ │ │ (MSDU 1) │ │ (MSDU 2) │ │ (MSDU 3) │ │ (MSDU N) │         │   │
│ │ └──────────┘ └──────────┘ └──────────┘ └──────────┘         │   │
│ └──────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────┘
```

### TID (Traffic Identifier)

| TID | AC | Description | Priority |
|-----|-----|-------------|----------|
| 0 | BE | Best Effort | Low |
| 1 | BK | Background | Lowest |
| 2 | BK | Background | Lowest |
| 3 | BE | Best Effort | Low |
| 4 | VI | Video | High |
| 5 | VI | Video | High |
| 6 | VO | Voice | Highest |
| 7 | VO | Voice | Highest |

### qdf_nbuf (Network Buffer)
- QDF abstraction for network buffers (sk_buff on Linux)
- Key operations:

| Function | Description |
|----------|-------------|
| `qdf_nbuf_alloc()` | Allocate network buffer |
| `qdf_nbuf_free()` | Free network buffer |
| `qdf_nbuf_data()` | Get data pointer |
| `qdf_nbuf_len()` | Get data length |
| `qdf_nbuf_push_head()` | Add data at head |
| `qdf_nbuf_pull_head()` | Remove data from head |
| `qdf_nbuf_put_tail()` | Add data at tail |
| `qdf_nbuf_trim_tail()` | Remove data from tail |

---

## Communication Interfaces

### WMI (WLAN Module Interface)

```
┌─────────────────────────────────────────────────────────────────────┐
│                              Host                                   │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │                    WMI Command Layer                        │   │
│  │  - wmi_unified_cmd_send()                                   │   │
│  │  - Command serialization                                    │   │
│  └─────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────┘
│ Commands ↓  ↑ Events
┌─────────────────────────────────────────────────────────────────────┐
│                           Firmware                                  │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │                    WMI Event Layer                          │   │
│  │  - Event generation                                         │   │
│  │  - Status reporting                                         │   │
│  └─────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────┘
```

**Common WMI Commands:**

| Command | Description |
|---------|-------------|
| `WMI_VDEV_CREATE_CMDID` | Create virtual device |
| `WMI_VDEV_DELETE_CMDID` | Delete virtual device |
| `WMI_VDEV_START_CMDID` | Start VDEV on channel |
| `WMI_VDEV_STOP_CMDID` | Stop VDEV |
| `WMI_PEER_CREATE_CMDID` | Create peer entry |
| `WMI_PEER_DELETE_CMDID` | Delete peer entry |
| `WMI_SCAN_START_CMDID` | Start scanning |
| `WMI_SCAN_STOP_CMDID` | Stop scanning |
| `WMI_PDEV_SET_PARAM_CMDID` | Set PDEV parameter |
| `WMI_VDEV_SET_PARAM_CMDID` | Set VDEV parameter |

**Common WMI Events:**

| Event | Description |
|-------|-------------|
| `WMI_VDEV_START_RESP_EVENTID` | VDEV start response |
| `WMI_SCAN_EVENTID` | Scan results/status |
| `WMI_MGMT_RX_EVENTID` | Management frame received |
| `WMI_PEER_STA_KICKOUT_EVENTID` | Client kicked out |
| `WMI_ROAM_EVENTID` | Roaming event |
| `WMI_DFS_RADAR_EVENTID` | Radar detected |

### HTT (Host-to-Target Transport)

High-throughput data transport layer:

| Message Type | Direction | Description |
|--------------|-----------|-------------|
| HTT_H2T_MSG_TYPE_TX_FRM | Host→Target | TX data frame |
| HTT_H2T_MSG_TYPE_RX_RING_CFG | Host→Target | RX ring configuration |
| HTT_T2H_MSG_TYPE_RX_IND | Target→Host | RX indication |
| HTT_T2H_MSG_TYPE_TX_COMPL_IND | Target→Host | TX completion |
| HTT_T2H_MSG_TYPE_PEER_MAP | Target→Host | Peer ID mapping |
| HTT_T2H_MSG_TYPE_PEER_UNMAP | Target→Host | Peer ID unmapping |

---

## Kernel Modules

The WLAN driver stack consists of multiple kernel modules loaded in order:

| Module | Purpose | Dependencies |
|--------|---------|--------------|
| `qdf.ko` | QCA Driver Framework (OS abstraction) | None |
| `asf.ko` | Atheros Service Framework | qdf |
| `umac.ko` | Upper MAC layer | qdf, asf |
| `qca_spectral.ko` | Spectral analysis support | umac |
| `qca_ol.ko` | QCA Offload layer | umac |
| `wifi_3_0.ko` | WiFi 6/6E chipset support | qca_ol |
| `wifi_2_0.ko` | WiFi 5 chipset support | qca_ol |
| `ath_dfs.ko` | DFS (Dynamic Frequency Selection) | umac |
| `ath_pktlog.ko` | Packet logging | umac |
| `smart_antenna.ko` | Smart antenna support | umac |
| `ec.ko` | Encryption module | umac |

### Module Loading Order

```bash
# Typical loading sequence
insmod qdf.ko
insmod asf.ko
insmod umac.ko
insmod qca_spectral.ko
insmod qca_ol.ko
insmod wifi_3_0.ko  # or wifi_2_0.ko depending on hardware
insmod ath_dfs.ko
insmod ath_pktlog.ko
insmod smart_antenna.ko
insmod ec.ko
```

---

## Frequency Bands and Channels

### Frequency Bands

| Band | Frequency Range | Channels | Standards |
|------|-----------------|----------|-----------|
| 2.4 GHz | 2400-2484 MHz | 1-14 | 802.11b/g/n/ax |
| 5 GHz | 5150-5895 MHz | 36-177 | 802.11a/n/ac/ax |
| 6 GHz | 5925-7125 MHz | 1-233 | 802.11ax/be |

### 2.4 GHz Channels

| Channel | Center Freq (MHz) | Notes |
|---------|-------------------|-------|
| 1 | 2412 | Non-overlapping |
| 2 | 2417 | |
| 3 | 2422 | |
| 4 | 2427 | |
| 5 | 2432 | |
| 6 | 2437 | Non-overlapping |
| 7 | 2442 | |
| 8 | 2447 | |
| 9 | 2452 | |
| 10 | 2457 | |
| 11 | 2462 | Non-overlapping |
| 12 | 2467 | Not allowed in US |
| 13 | 2472 | Not allowed in US |
| 14 | 2484 | Japan only, 802.11b only |

### 5 GHz Channels (UNII Bands)

| Band | Channels | Frequency Range | DFS Required |
|------|----------|-----------------|--------------|
| UNII-1 | 36, 40, 44, 48 | 5150-5250 MHz | No |
| UNII-2A | 52, 56, 60, 64 | 5250-5350 MHz | Yes |
| UNII-2C | 100-144 | 5470-5725 MHz | Yes |
| UNII-3 | 149, 153, 157, 161, 165 | 5725-5850 MHz | No |
| UNII-4 | 169, 173, 177 | 5850-5895 MHz | No (varies) |

### 6 GHz Channels

| Power Mode | Description | Channels |
|------------|-------------|----------|
| LPI | Low Power Indoor | All 6 GHz |
| SP | Standard Power | Requires AFC |
| VLP | Very Low Power | Portable devices |

### Regulatory Domains

| Domain | Region | Key Differences |
|--------|--------|-----------------|
| FCC | North America | Channels 1-11 (2.4G), UNII-1/2/3 (5G) |
| ETSI | Europe | Channels 1-13 (2.4G), DFS required |
| MKK | Japan | Channel 14 allowed (2.4G) |
| APAC | Asia Pacific | Varies by country |

---

## Channel Widths and PHY Modes

### Channel Width Options

| Width | Designation | Standards | Subcarriers |
|-------|-------------|-----------|-------------|
| 20 MHz | HT20/VHT20/HE20 | All | 64 (52 data) |
| 40 MHz | HT40/VHT40/HE40 | 802.11n+ | 128 (108 data) |
| 80 MHz | VHT80/HE80 | 802.11ac+ | 256 (234 data) |
| 160 MHz | VHT160/HE160 | 802.11ac+ | 512 (468 data) |
| 80+80 MHz | VHT80+80 | 802.11ac+ | 2×256 |
| 320 MHz | EHT320 | 802.11be | 1024 (936 data) |

### PHY Mode Definitions

| Mode | Standard | Description |
|------|----------|-------------|
| 11B | 802.11b | 2.4 GHz, DSSS, 1-11 Mbps |
| 11A | 802.11a | 5 GHz, OFDM, 6-54 Mbps |
| 11G | 802.11g | 2.4 GHz, OFDM, 6-54 Mbps |
| 11NA | 802.11n | 5 GHz, HT, up to 600 Mbps |
| 11NG | 802.11n | 2.4 GHz, HT, up to 600 Mbps |
| 11AC | 802.11ac | 5 GHz, VHT, up to 6.9 Gbps |
| 11AXA | 802.11ax | 5/6 GHz, HE, up to 9.6 Gbps |
| 11AXG | 802.11ax | 2.4 GHz, HE, up to 1.1 Gbps |
| 11BEA | 802.11be | 5/6 GHz, EHT, up to 46 Gbps |
| 11BEG | 802.11be | 2.4 GHz, EHT |

### Channel Width Flags

```c
// From dfs_channel.h
#define WLAN_CHAN_2GHZ             0x0000000000000010  // 2 GHz band
#define WLAN_CHAN_5GHZ             0x0000000000000020  // 5 GHz band
#define WLAN_CHAN_6GHZ             0x0000000000000030  // 6 GHz band

#define WLAN_CHAN_HT20             // HT 20 MHz
#define WLAN_CHAN_HT40PLUS         // HT 40 MHz, extension above
#define WLAN_CHAN_HT40MINUS        // HT 40 MHz, extension below

#define WLAN_CHAN_VHT20            // VHT 20 MHz
#define WLAN_CHAN_VHT40PLUS        // VHT 40 MHz, extension above
#define WLAN_CHAN_VHT40MINUS       // VHT 40 MHz, extension below
#define WLAN_CHAN_VHT80            // VHT 80 MHz
#define WLAN_CHAN_VHT160           // VHT 160 MHz
#define WLAN_CHAN_VHT80_80         // VHT 80+80 MHz

#define WLAN_CHAN_HE20             // HE 20 MHz
#define WLAN_CHAN_HE40PLUS         // HE 40 MHz, extension above
#define WLAN_CHAN_HE40MINUS        // HE 40 MHz, extension below
#define WLAN_CHAN_HE80             // HE 80 MHz
#define WLAN_CHAN_HE160            // HE 160 MHz
#define WLAN_CHAN_HE80_80          // HE 80+80 MHz
```

### Preamble Puncturing (802.11be)

- **Definition**: Ability to "punch holes" in wide channels to avoid interference
- **Benefit**: Use wider channels even with partial interference
- **Patterns**: Defined legitimate puncture patterns per standard

```c
// Puncture bitmap examples
#define PUNCTURE_NONE              0x0000  // No puncturing
#define PUNCTURE_INVALID           0xFFFF  // Invalid pattern
// Bitmap: each bit represents a 20 MHz subchannel
// 1 = punctured, 0 = active
```

---

## Security and Authentication

### Security Modes

| Mode | Description | Encryption | Authentication |
|------|-------------|------------|----------------|
| Open | No security | None | None |
| WEP | Legacy (deprecated) | WEP (40/104-bit) | Shared Key |
| WPA | Wi-Fi Protected Access | TKIP | PSK or 802.1X |
| WPA2 | WPA version 2 | CCMP (AES) | PSK or 802.1X |
| WPA3 | WPA version 3 | CCMP/GCMP | SAE or 802.1X |
| OWE | Opportunistic Wireless Encryption | CCMP | DH key exchange |

### Authentication Algorithms

| Algorithm | Value | Description |
|-----------|-------|-------------|
| Open System | 0 | No authentication |
| Shared Key | 1 | WEP shared key (deprecated) |
| FT (Fast Transition) | 2 | 802.11r fast roaming |
| SAE | 3 | Simultaneous Authentication of Equals (WPA3) |
| FILS SK | 4 | Fast Initial Link Setup (Shared Key) |
| FILS SK PFS | 5 | FILS with Perfect Forward Secrecy |
| FILS PK | 6 | FILS (Public Key) |
| PASN | 7 | Pre-Association Security Negotiation |

### Key Management

| Key | Description | Scope |
|-----|-------------|-------|
| PMK | Pairwise Master Key | Per-client, derived from passphrase or 802.1X |
| PTK | Pairwise Transient Key | Per-client, derived from PMK |
| GTK | Group Temporal Key | Per-BSS, for broadcast/multicast |
| IGTK | Integrity GTK | For protected management frames |
| KCK | Key Confirmation Key | Part of PTK, for MIC |
| KEK | Key Encryption Key | Part of PTK, for key wrapping |
| TK | Temporal Key | Part of PTK, for data encryption |

### Key Hierarchy

```
┌─────────────────────────────────────┐
│           Master Key (MK)           │
│  (Passphrase or 802.1X derived)     │
└─────────────────┬───────────────────┘
│
▼
┌─────────────────────────────────────┐
│      Pairwise Master Key (PMK)      │
│  PMK = PBKDF2(passphrase, SSID)     │
└─────────────────┬───────────────────┘
│ 4-Way Handshake
▼
┌─────────────────────────────────────┐
│    Pairwise Transient Key (PTK)     │
│  PTK = PRF(PMK, ANonce, SNonce,     │
│           AA, SPA)                  │
├─────────────────────────────────────┤
│  ┌─────┐ ┌─────┐ ┌─────────────┐   │
│  │ KCK │ │ KEK │ │     TK      │   │
│  └─────┘ └─────┘ └─────────────┘   │
└─────────────────────────────────────┘
```

### Encryption Ciphers

| Cipher | Key Size | Block Size | Standard |
|--------|----------|------------|----------|
| WEP-40 | 40 bits | 64 bits | 802.11 (deprecated) |
| WEP-104 | 104 bits | 64 bits | 802.11 (deprecated) |
| TKIP | 128 bits | 64 bits | WPA (deprecated) |
| CCMP | 128 bits | 128 bits | WPA2/WPA3 |
| CCMP-256 | 256 bits | 128 bits | WPA3 |
| GCMP | 128 bits | 128 bits | WPA3 |
| GCMP-256 | 256 bits | 128 bits | WPA3 |

### Protected Management Frames (PMF/802.11w)

| Mode | Description |
|------|-------------|
| Disabled | No PMF |
| Optional | PMF if client supports |
| Required | PMF mandatory |

Protected frame types:
- Disassociation
- Deauthentication
- Action frames (some)

### PMKSA Caching

```c
struct rsn_pmksa_cache_entry {
  u8 pmk[PMK_LEN_MAX];           // Cached PMK
  size_t pmk_len;                 // PMK length
  u8 pmkid[PMKID_LEN];           // PMKID for identification
  u8 aa[ETH_ALEN];               // Authenticator address
  u8 spa[ETH_ALEN];              // Supplicant address
  int session_timeout;            // Session timeout
  int akmp;                       // AKM suite
};
```

---

## Roaming and Mobility

### Roaming Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│                        Roaming Process                              │
├─────────────────────────────────────────────────────────────────────┤
│  1. Trigger: Signal degradation, load balancing, etc.              │
│  2. Scan: Find candidate APs                                       │
│  3. Decision: Select best AP                                       │
│  4. Transition: Move to new AP                                     │
│     - Pre-authentication (optional)                                │
│     - Reassociation                                                │
│     - Key establishment                                            │
│  5. Completion: Resume data transfer                               │
└─────────────────────────────────────────────────────────────────────┘
```

### 802.11r (Fast BSS Transition / FT)

- **Purpose**: Reduce roaming latency by pre-establishing keys
- **Benefit**: Sub-50ms roaming (vs 100-500ms without)
- **Key Concepts**:

| Term | Description |
|------|-------------|
| Mobility Domain | Group of APs supporting fast roaming |
| R0KH | R0 Key Holder (initial AP) |
| R1KH | R1 Key Holder (target AP) |
| PMK-R0 | First-level PMK derived from MSK |
| PMK-R1 | Second-level PMK derived from PMK-R0 |

```
┌─────────────────────────────────────────────────────────────────────┐
│                    802.11r Key Hierarchy                            │
├─────────────────────────────────────────────────────────────────────┤
│                         MSK (from 802.1X)                           │
│                              │                                      │
│                              ▼                                      │
│                    ┌─────────────────┐                              │
│                    │     PMK-R0      │ (Held by R0KH)               │
│                    └────────┬────────┘                              │
│                             │                                       │
│              ┌──────────────┼──────────────┐                        │
│              ▼              ▼              ▼                        │
│        ┌──────────┐   ┌──────────┐   ┌──────────┐                  │
│        │ PMK-R1   │   │ PMK-R1   │   │ PMK-R1   │ (Per R1KH)       │
│        │ (AP1)    │   │ (AP2)    │   │ (AP3)    │                  │
│        └────┬─────┘   └────┬─────┘   └────┬─────┘                  │
│             │              │              │                         │
│             ▼              ▼              ▼                         │
│           PTK            PTK            PTK                         │
└─────────────────────────────────────────────────────────────────────┘
```

**FT Methods:**

| Method | Description |
|--------|-------------|
| FT over Air | Direct reassociation to target AP |
| FT over DS | Reassociation via current AP (Distribution System) |

### 802.11k (Radio Resource Management / RRM)

- **Purpose**: Provide information for better roaming decisions
- **Key Features**:

| Feature | Description |
|---------|-------------|
| Neighbor Report | AP provides list of neighboring APs |
| Beacon Report | Client reports received beacons |
| Link Measurement | Measure link quality |
| Channel Load | Report channel utilization |

### 802.11v (Wireless Network Management / WNM)

- **Purpose**: Network-assisted client management
- **Key Features**:

| Feature | Description |
|---------|-------------|
| BSS Transition Management | AP suggests client roam |
| Directed Multicast Service | Efficient multicast delivery |
| Flexible Multicast Service | Multicast scheduling |
| TIM Broadcast | Traffic indication optimization |
| Sleep Mode | Extended power save |

### OKC (Opportunistic Key Caching)

- **Purpose**: Fast roaming without 802.11r
- **Mechanism**: Cache PMK across APs with same PMKID
- **Limitation**: Requires same RADIUS server or PMK distribution

### Connection Manager State Machine

```c
// Roaming states
enum wlan_cm_sm_state {
  WLAN_CM_S_INIT,           // Initial state
  WLAN_CM_S_CONNECTING,     // Connecting
  WLAN_CM_S_CONNECTED,      // Connected
  WLAN_CM_S_DISCONNECTING,  // Disconnecting
  WLAN_CM_S_ROAMING,        // Roaming
};

// Roaming sub-states
enum wlan_cm_roam_sub_state {
  WLAN_CM_SS_PREAUTH,       // Pre-authentication
  WLAN_CM_SS_REASSOC,       // Reassociation
  WLAN_CM_SS_ROAM_STARTED,  // FW roam started
  WLAN_CM_SS_ROAM_SYNC,     // Roam sync
};
```

---

## APC (AP Capture) Subsystem

### What is APC?
APC (AP Capture) is a packet capture subsystem that stores recent packets on a per-client basis for debugging 
and analysis purposes. It provides visibility into wireless traffic without requiring external capture 
equipment.

### APC Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                        APC Global Structure                         │
│                          (ar_apc_g)                                 │
├─────────────────────────────────────────────────────────────────────┤
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │                    Client Hash Table                        │   │
│  │                      (apc_ht)                               │   │
│  ├─────────────────────────────────────────────────────────────┤   │
│  │  Bucket 0: Client A → Client B → NULL                       │   │
│  │  Bucket 1: Client C → NULL                                  │   │
│  │  Bucket 2: NULL                                             │   │
│  │  ...                                                        │   │
│  │  Bucket N: Client X → Client Y → Client Z → NULL            │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                                                                     │
│  ┌─────────────────┐  ┌─────────────────┐                          │
│  │   Cleanup Timer │  │   Client Count  │                          │
│  │  (60 sec check) │  │   (atomic)      │                          │
│  └─────────────────┘  └─────────────────┘                          │
└─────────────────────────────────────────────────────────────────────┘
```

### Key APC Structures

```c
// Global APC structure
struct ar_apc_g {
  hash_table_t apc_ht;         // Client hash-table
  spinlock_t ht_lock;          // Hash-table lock
  timer cleanup_timer;         // Cleanup timer
  atomic_t cl_count;           // Client count
};

// Per-client APC structure
struct ar_apc_cl_s {
  uint8_t macaddr[6];          // Client MAC address
  pkt_q;                       // Packet buffer queue
  uint16_t data_pkt_count;     // Data packet count
  uint16_t total_pkt_count;    // Total packet count
  time_t last_pkt_timestamp;   // Last activity timestamp
  uint8_t vdev_id;             // Associated VDEV
};

// Packet capture header
struct ar_apc_cardhdr {
  uint16_t slotlen;            // Slot length
  uint16_t reclen;             // Record length
  uint32_t hosttime;           // Host timestamp
  uint16_t channel;            // Channel number
  uint8_t signal;              // Signal strength (RSSI)
  int16_t noise;               // Noise level
  uint8_t rate;                // Data rate
  uint8_t istx;                // TX (1) or RX (0) indicator
  uint16_t frmlen;             // Frame length
  uint64_t tsft;               // TSF timestamp
  uint16_t chan_freq;          // Channel frequency
};
```

### APC Default Parameters

| Parameter | Default Value | Description |
|-----------|---------------|-------------|
| `AR_APC_FRAME_LEN` | 500 | Max frame length to capture |
| `AR_APC_NUM_PKTS` | 200 | Max packets per client |
| `AR_APC_CLIENT_INACTIVITY_TIME` | 300 sec | Client cleanup timeout |
| `AR_APC_MAX_CLIENT_COUNT` | 200 | Max client entries |
| `AR_APC_MAX_DATA_PKTS_TO_STORE` | 20 | Max data packets per client |
| `AR_APC_CHECK_CLIENT_TIME` | 60 sec | Cleanup check interval |

### APC Key Functions

| Function | Purpose |
|----------|---------|
| `ar_apc_global_init()` | Initialize global APC structures |
| `ar_apc_get_cl()` | Get APC client by MAC address |
| `ar_apc_create_and_get_client()` | Create new client entry |
| `ar_apc_bcn_buf_init()` | Initialize beacon buffer for VDEV |
| `ar_apc_bcn_buf_deinit()` | Deinitialize beacon buffer |
| `ar_apc_beacon_capture()` | Capture beacon frames |
| `ar_dp_rx_apc()` | Process RX packets for APC |
| `ar_apc_cleanup_timer_cb()` | Periodic cleanup callback |

### APC Packet Flow

```
┌─────────────────────────────────────────────────────────────────────┐
│                        RX Packet Path                               │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  Firmware RX → HTT RX → DP RX Path                                  │
│                              │                                      │
│                              ▼                                      │
│                    ┌─────────────────┐                              │
│                    │  ar_dp_rx_apc() │                              │
│                    └────────┬────────┘                              │
│                             │                                       │
│              ┌──────────────┴──────────────┐                        │
│              ▼                             ▼                        │
│     ┌────────────────┐           ┌────────────────┐                │
│     │ Management/Ctrl│           │   Data Frame   │                │
│     │    Frame       │           │                │                │
│     └───────┬────────┘           └───────┬────────┘                │
│             │                            │                          │
│             ▼                            ▼                          │
│     Store all frames            Store up to 20 per client           │
│                                                                     │
│                    ┌─────────────────┐                              │
│                    │  Client Queue   │                              │
│                    │  (ar_apc_cl_s)  │                              │
│                    └─────────────────┘                              │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Additional Terminology

### DFS (Dynamic Frequency Selection)
- **Purpose**: Radar detection and channel switching for 5GHz bands
- **Requirement**: Regulatory compliance in UNII-2 bands
- **Process**:
  1. CAC (Channel Availability Check) - 60 sec minimum
  2. In-service monitoring
  3. Radar detection → Channel switch
  4. NOP (Non-Occupancy Period) - 30 minutes

### Spectral Analysis
- **Purpose**: RF spectrum analysis feature
- **Use Cases**:
  - Interference detection
  - Non-WiFi device identification
  - Channel quality assessment

### MLME (MAC Layer Management Entity)
- **Purpose**: Manages 802.11 state machines
- **Handles**:
  - Association/Disassociation
  - Authentication/Deauthentication
  - Scanning
  - Power management

### ACL (Access Control List)
- **Purpose**: MAC-based client filtering
- **Modes**:
  - Allow list (whitelist)
  - Deny list (blacklist)

### WDS (Wireless Distribution System)
- **Purpose**: 4-address mode for bridging between APs
- **Use Case**: Wireless backhaul

### SON (Self-Organizing Networks)
- **Purpose**: Wi-Fi mesh/repeater functionality
- **Features**:
  - Automatic topology discovery
  - Path selection
  - Load balancing

### Band Steering
- **Purpose**: Directing capable clients to preferred bands
- **Typical**: 5GHz preferred over 2.4GHz
- **Methods**:
  - Probe response suppression
  - Association rejection
  - BTM (BSS Transition Management)

### Smart Steering
- **Purpose**: Advanced client steering
- **Factors**:
  - Signal quality (RSSI)
  - AP load
  - Client capabilities
  - Historical performance

### MBO (Multi-Band Operation)
- **Standard**: 802.11v-based
- **Purpose**: Improved client steering mechanisms
- **Features**:
  - Cellular data offloading
  - Non-preferred channel list
  - Transition rejection

### RRM (Radio Resource Management)
- **Standard**: 802.11k
- **Features**:
  - Neighbor reports
  - Link measurements
  - Beacon reports
  - Channel load reports
  - Noise histogram

### WNM (Wireless Network Management)
- **Standard**: 802.11v
- **Features**:
  - BSS transition management
  - Sleep mode (extended power save)
  - Directed multicast service
  - TIM broadcast

### MLO (Multi-Link Operation)
- **Standard**: Wi-Fi 7 (802.11be)
- **Purpose**: Simultaneous connections on multiple links/bands
- **Key Concepts**:

| Term | Description |
|------|-------------|
| MLD | Multi-Link Device |
| MLD Address | Common address for all links |
| Link ID | Identifier for each link |
| EMLSR | Enhanced Multi-Link Single Radio |
| EMLMR | Enhanced Multi-Link Multi Radio |

### AFC (Automated Frequency Coordination)
- **Purpose**: Enable standard power operation in 6 GHz
- **Mechanism**: Query AFC server for allowed channels/power
- **Requirement**: Outdoor/standard power 6 GHz operation

### ACS (Automatic Channel Selection)
- **Purpose**: Automatically select best operating channel
- **Factors**:
  - Channel utilization
  - Interference levels
  - Radar history (DFS)
  - Neighbor AP density

### TPC (Transmit Power Control)
- **Purpose**: Automatic transmit power adjustment
- **Goals**:
  - Minimize interference
  - Optimize coverage
  - Regulatory compliance

---

## Arista-Specific Components

### AR Driver Layer (`ar/`)

Arista's driver abstraction layer provides a clean interface between the vendor (QCA) driver and Arista's 
management plane.

```
┌─────────────────────────────────────────────────────────────────────┐
│                     Arista Driver Architecture                      │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │                    User Space (hostapd)                     │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                              │                                      │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │                    user_if/ (User Interface)                │   │
│  │              (Netlink, IOCTL handlers)                      │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                              │                                      │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │                    ar_if/ (Arista Interface)                │   │
│  │              (Arista-specific abstractions)                 │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                              │                                      │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │                    core/ (Core Logic)                       │   │
│  │  ┌──────────┬──────────┬──────────┬──────────┐             │   │
│  │  │    CP    │    DP    │   APC    │  Types   │             │   │
│  │  │(Control) │  (Data)  │(Capture) │          │             │   │
│  │  └──────────┴──────────┴──────────┴──────────┘             │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                              │                                      │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │                    vdrv_if/ (Vendor Interface)              │   │
│  │              (QCA driver interface)                         │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                              │                                      │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │                    os_if/ (OS Interface)                    │   │
│  │              (Linux kernel interface)                       │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                              │                                      │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │                    QCA Driver (Vendor)                      │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

### Directory Structure

| Directory | Purpose |
|-----------|---------|
| `ar/ar_if/` | Arista interface layer - high-level abstractions |
| `ar/core/` | Core driver logic (CP, DP, APC, types) |
| `ar/os_if/` | OS interface layer - Linux kernel integration |
| `ar/vdrv_if/` | Vendor driver interface - QCA driver hooks |
| `ar/user_if/` | User-space interface - netlink, ioctl |
| `ar/docs/` | Driver documentation |

### Key Arista Structures

| Structure | Purpose | Location |
|-----------|---------|----------|
| `ar_global_s` | Global driver state | ar_types.h |
| `ar_pdev_s` | Arista radio object (wraps QCA pdev) | ar_types.h |
| `ar_vdev_s` | Arista VAP object (wraps QCA vdev) | ar_types.h |
| `ar_peer_s` | Arista peer/client object | ar_types.h |
| `ar_dp_soc_s` | Datapath SoC object | ar_types.h |
| `ar_dp_pdev_s` | Datapath pdev object | ar_types.h |
| `ar_dp_vdev_s` | Datapath vdev object | ar_types.h |
| `ar_dp_peer_s` | Datapath peer object | ar_types.h |
| `ar_apc_g` | Global APC structure | ar_apc.h |
| `ar_apc_cl_s` | Per-client APC structure | ar_apc.h |

### Control Path Flags (ar_cp.h)

| Flag | Purpose |
|------|---------|
| `AR_CP_FLAG_BAND_STEERING` | Band steering enabled |
| `AR_CP_FLAG_SMART_STEERING` | Smart steering enabled |
| `AR_CP_FLAG_APC_DEBUG` | APC debug mode |
| `AR_CP_FLAG_WNM_ENABLED` | WNM enabled |
| `AR_CP_FLAG_RRM_ENABLED` | RRM enabled |

### Arista Extensions

| Feature | Description |
|---------|-------------|
| WIPS Support | Wireless Intrusion Prevention System |
| APC | AP Capture for debugging |
| Band Steering | Enhanced client steering |
| Smart Steering | Load-aware steering |
| Airtight Extensions | Security and monitoring |

---

## hostapd Integration

### Overview

hostapd is the user-space daemon that manages AP functionality. It interfaces with the kernel driver to 
provide:

```
┌─────────────────────────────────────────────────────────────────────┐
│                        hostapd Architecture                         │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │                    hostapd Main Process                     │   │
│  ├─────────────────────────────────────────────────────────────┤   │
│  │  ┌──────────┬──────────┬──────────┬──────────┬──────────┐  │   │
│  │  │   WPA    │  RADIUS  │  802.1X  │   MLME   │  Driver  │  │   │
│  │  │Authenticator│ Client │   EAP   │ Interface│ Interface│  │   │
│  │  └──────────┴──────────┴──────────┴──────────┴──────────┘  │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                              │                                      │
│                    Netlink / IOCTL / cfg80211                       │
│                              │                                      │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │                    Kernel Driver                            │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

### hostapd Components

| Component | Purpose |
|-----------|---------|
| WPA Authenticator | 4-way handshake, key management |
| RADIUS Client | AAA server communication |
| 802.1X/EAP | Enterprise authentication |
| MLME Interface | Management frame handling |
| Driver Interface | Kernel driver communication |
| ACL | Access control lists |
| VLAN | Dynamic VLAN assignment |

### Key Configuration Files

| File | Purpose |
|------|---------|
| `hostapd.conf` | Main configuration |
| `hostapd.accept` | MAC allow list |
| `hostapd.deny` | MAC deny list |
| `hostapd.eap_user` | EAP user database |
| `hostapd.radius_clients` | RADIUS client list |

### Arista hostapd Extensions

| Extension | Purpose |
|-----------|---------|
| `ar_wpa_auth.c` | Arista WPA authentication extensions |
| `ar_wpa_auth_ft.c` | Arista 802.11r FT extensions |
| `ar_hostapd.c` | Arista hostapd integration |
| `ar_radius.c` | Arista RADIUS extensions |

### Fast Roaming Configuration (802.11r)

```go
// From ssid_fast_roaming.go
var fastRoaming11rConfigMap = map[string]string{
  "FtEnabled":   "FT_ENABLE",      // Enable 802.11r
  "FtOverDS":    "FT_OVER_DS",     // FT over Distribution System
  "FtMixedMode": "FT_MIXED_MODE",  // Mixed mode (FT + non-FT)
}
```

---

## Glossary

| Term | Full Name | Description |
|------|-----------|-------------|
| A-MPDU | Aggregated MPDU | Multiple MPDUs in one PPDU |
| A-MSDU | Aggregated MSDU | Multiple MSDUs in one MPDU |
| ACL | Access Control List | MAC filtering |
| ACS | Automatic Channel Selection | Auto channel selection |
| AFC | Automated Frequency Coordination | 6 GHz power coordination |
| AKM | Authentication and Key Management | Security suite |
| AP | Access Point | Wireless base station |
| APC | AP Capture | Packet capture subsystem |
| BA | Block Ack | Block acknowledgment |
| BAR | Block Ack Request | Request for block ack |
| BSS | Basic Service Set | Single AP network |
| BSSID | BSS Identifier | AP MAC address |
| CAC | Channel Availability Check | DFS radar check |
| CCMP | Counter Mode CBC-MAC Protocol | AES encryption |
| CP | Control Path | Configuration path |
| CTS | Clear to Send | Medium access control |
| DA | Destination Address | Frame destination |
| DFS | Dynamic Frequency Selection | Radar avoidance |
| DP | Data Path | Packet forwarding path |
| DTIM | Delivery Traffic Indication Map | Multicast indication |
| EAP | Extensible Authentication Protocol | 802.1X authentication |
| EHT | Extremely High Throughput | 802.11be |
| ESS | Extended Service Set | Multiple AP network |
| FT | Fast Transition | 802.11r fast roaming |
| GCMP | Galois/Counter Mode Protocol | AES-GCM encryption |
| GTK | Group Temporal Key | Broadcast/multicast key |
| HE | High Efficiency | 802.11ax |
| HT | High Throughput | 802.11n |
| HTT | Host-to-Target Transport | Data transport |
| IGTK | Integrity GTK | PMF integrity key |
| LMAC | Lower MAC | Hardware-close MAC |
| MBO | Multi-Band Operation | Client steering |
| MCS | Modulation and Coding Scheme | Rate index |
| MIC | Message Integrity Code | Frame integrity |
| MLO | Multi-Link Operation | 802.11be multi-link |
| MLME | MAC Layer Management Entity | State machines |
| MPDU | MAC Protocol Data Unit | MAC frame |
| MSDU | MAC Service Data Unit | Payload |
| NOP | Non-Occupancy Period | DFS channel timeout |
| OKC | Opportunistic Key Caching | Fast roaming |
| OWE | Opportunistic Wireless Encryption | Open encryption |
| PDEV | Physical Device | Radio hardware |
| PEER | Peer | Connected client |
| PMF | Protected Management Frames | 802.11w |
| PMK | Pairwise Master Key | Master key |
| PMKSA | PMK Security Association | Cached PMK |
| PPDU | Physical Protocol Data Unit | PHY frame |
| PSOC | Physical SoC | System-on-chip |
| PTK | Pairwise Transient Key | Session key |
| QDF | QCA Driver Framework | OS abstraction |
| QoS | Quality of Service | Traffic prioritization |
| RA | Receiver Address | Frame receiver |
| RRM | Radio Resource Management | 802.11k |
| RSSI | Received Signal Strength Indicator | Signal level |
| RTS | Request to Send | Medium access control |
| SA | Source Address | Frame source |
| SAE | Simultaneous Authentication of Equals | WPA3 auth |
| SON | Self-Organizing Networks | Mesh |
| STA | Station | Client device |
| TA | Transmitter Address | Frame transmitter |
| TID | Traffic Identifier | QoS priority |
| TIM | Traffic Indication Map | Buffered frames |
| TKIP | Temporal Key Integrity Protocol | WPA encryption |
| TPC | Transmit Power Control | Power management |
| TSF | Timing Synchronization Function | Time sync |
| UMAC | Upper MAC | Protocol MAC |
| VAP | Virtual Access Point | Virtual interface |
| VDEV | Virtual Device | Logical interface |
| VHT | Very High Throughput | 802.11ac |
| WDS | Wireless Distribution System | AP bridging |
| WEP | Wired Equivalent Privacy | Legacy encryption |
| WMI | WLAN Module Interface | Host-FW interface |
| WMM | Wi-Fi Multimedia | QoS |
| WNM | Wireless Network Management | 802.11v |
| WPA | Wi-Fi Protected Access | Security standard |

---

## References

### Internal Documentation
- See `docs/pdev_vs_vdev_documentation.md` for detailed PDEV/VDEV comparison

### Source Code Locations
| Component | Path |
|-----------|------|
| Driver source | `ap/src/wlan-drivers/` |
| QCA modules | `ap/src/wlan-drivers/QCA/licensed/` |
| Arista layer | `ap/src/wlan-drivers/ar/` |
| hostapd | `ap/src/hostapd-2.10/` |
| Arista hostapd | `ap/src/hostapd/` |
| Config agent | `ap/src/go/arista-ap/configagent/` |

### IEEE Standards
| Standard | Description |
|----------|-------------|
| 802.11 | Base WLAN standard |
| 802.11a | 5 GHz OFDM |
| 802.11b | 2.4 GHz DSSS |
| 802.11g | 2.4 GHz OFDM |
| 802.11n | High Throughput (HT) |
| 802.11ac | Very High Throughput (VHT) |
| 802.11ax | High Efficiency (HE) / Wi-Fi 6 |
| 802.11be | Extremely High Throughput (EHT) / Wi-Fi 7 |
| 802.11i | Security (WPA2) |
| 802.11k | Radio Resource Management |
| 802.11r | Fast BSS Transition |
| 802.11v | Wireless Network Management |
| 802.11w | Protected Management Frames |
| 802.1X | Port-based Network Access Control |

