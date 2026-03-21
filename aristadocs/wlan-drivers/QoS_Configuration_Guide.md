# QoS (Quality of Service) Configuration Guide

## Table of Contents

1. [Overview](#overview)
2. [QoS Fundamentals](#qos-fundamentals)
3. [Architecture Overview](#architecture-overview)
4. [QoS Flag Bit Structure](#qos-flag-bit-structure)
5. [QoS Configuration Parameters](#qos-configuration-parameters)
6. [WMM Access Categories and TID Mapping](#wmm-access-categories-and-tid-mapping)
7. [Configuration Flow](#configuration-flow)
8. [Source Files Reference](#source-files-reference)
9. [QoS Parameter Calculation](#qos-parameter-calculation)
10. [Driver QoS Application](#driver-qos-application)
11. [Traffic Priority Processing](#traffic-priority-processing)
12. [Detailed Code Walkthrough](#detailed-code-walkthrough)
13. [Example Configurations](#example-configurations)
14. [802.1p to WMM TID Mapping](#8021p-to-wmm-tid-mapping)
15. [DSCP and TOS Mapping](#dscp-and-tos-mapping)
16. [Hotspot 2.0 QoS Map](#hotspot-20-qos-map)
17. [Rate Limiting and QoS](#rate-limiting-and-qos)
18. [VLAN QoS Integration](#vlan-qos-integration)
19. [Debugging QoS](#debugging-qos)
20. [Troubleshooting Guide](#troubleshooting-guide)
21. [QosConfig Data Model](#qosconfig-data-model)
22. [API Reference](#api-reference)
23. [Best Practices](#best-practices)
24. [Performance Considerations](#performance-considerations)
25. [Appendix](#appendix)

---

## Overview

QoS (Quality of Service) in this codebase manages traffic prioritization for wireless access points. It controls how packets are classified, prioritized, and marked for both upstream (client-to-AP) and downstream (AP-to-client) traffic.

The QoS subsystem is a critical component that ensures:
- Voice and video traffic receives appropriate priority
- Background traffic doesn't interfere with time-sensitive applications
- Network administrators can enforce traffic policies per SSID
- Compliance with IEEE 802.11e WMM (Wi-Fi Multimedia) standards

### Key Features

1. **Per-SSID Priority Configuration**: Each SSID can have its own QoS policy
2. **Flexible Priority Modes**: Support for both Fixed and Ceiling priority types
3. **Multiple Mapping Sources**: Priority can be derived from 802.1p, DSCP, or TOS
4. **Upstream Marking**: Ability to mark packets leaving the AP
5. **WMM Compliance**: Full support for Wi-Fi Multimedia standards
6. **Hotspot 2.0 Integration**: QoS map support for HS2.0 networks

### Use Cases

- **Enterprise Voice over WiFi**: Prioritize VoIP traffic for clear calls
- **Video Conferencing**: Ensure smooth video streams
- **Guest Networks**: Limit guest traffic to best-effort priority
- **IoT Networks**: Assign appropriate priority to sensor data
- **Healthcare**: Prioritize critical medical device communications

---

## QoS Fundamentals

### What is QoS?

Quality of Service (QoS) refers to the overall performance of a network, particularly the performance seen by users. QoS mechanisms allow network administrators to prioritize certain types of traffic over others, ensuring that critical applications receive the bandwidth and low latency they require.

### Why QoS Matters in Wireless Networks

Wireless networks face unique challenges:
- **Shared Medium**: All devices share the same radio spectrum
- **Variable Conditions**: Signal strength and interference vary
- **Limited Bandwidth**: Wireless bandwidth is more constrained than wired
- **Latency Sensitivity**: Voice and video are highly sensitive to delays

### IEEE 802.11e and WMM

The IEEE 802.11e amendment introduced QoS capabilities to WiFi networks. Wi-Fi Multimedia (WMM) is the Wi-Fi Alliance's interoperability certification based on 802.11e.

#### WMM Access Categories

WMM defines four Access Categories (ACs) that map to different traffic types:

| Access Category | Abbreviation | Priority | Typical Traffic |
|----------------|--------------|----------|-----------------|
| Voice | AC_VO | Highest | VoIP, video calls |
| Video | AC_VI | High | Streaming video |
| Best Effort | AC_BE | Medium | Web browsing, email |
| Background | AC_BK | Low | File downloads, backups |

#### Traffic Identifiers (TIDs)

Each Access Category contains two Traffic Identifiers (TIDs):

| TID | Access Category | User Priority |
|-----|-----------------|---------------|
| 0 | Best Effort | 0 |
| 1 | Background | 1 |
| 2 | Background | 2 |
| 3 | Best Effort | 3 |
| 4 | Video | 4 |
| 5 | Video | 5 |
| 6 | Voice | 6 |
| 7 | Voice | 7 |

### DSCP (Differentiated Services Code Point)

DSCP is a 6-bit field in the IP header that classifies packets for QoS purposes. Common DSCP values:

| DSCP Value | Name | Description |
|------------|------|-------------|
| 0 | BE | Best Effort (default) |
| 8 | CS1 | Class Selector 1 (scavenger) |
| 10 | AF11 | Assured Forwarding 11 |
| 12 | AF12 | Assured Forwarding 12 |
| 14 | AF13 | Assured Forwarding 13 |
| 18 | AF21 | Assured Forwarding 21 |
| 20 | AF22 | Assured Forwarding 22 |
| 22 | AF23 | Assured Forwarding 23 |
| 26 | AF31 | Assured Forwarding 31 |
| 28 | AF32 | Assured Forwarding 32 |
| 30 | AF33 | Assured Forwarding 33 |
| 34 | AF41 | Assured Forwarding 41 |
| 36 | AF42 | Assured Forwarding 42 |
| 38 | AF43 | Assured Forwarding 43 |
| 46 | EF | Expedited Forwarding (voice) |
| 48 | CS6 | Class Selector 6 (network control) |
| 56 | CS7 | Class Selector 7 (network control) |

### 802.1p Priority

802.1p is a 3-bit field in the VLAN tag that provides Layer 2 QoS:

| Priority | Traffic Type |
|----------|--------------|
| 0 | Best Effort |
| 1 | Background |
| 2 | Spare |
| 3 | Excellent Effort |
| 4 | Controlled Load |
| 5 | Video |
| 6 | Voice |
| 7 | Network Control |

### TOS (Type of Service)

The legacy TOS field in the IP header has been largely replaced by DSCP, but is still supported for backward compatibility. The TOS byte structure:

```
Bits:  7   6   5   4   3   2   1   0
       |___|___|___|___|___|   |___|
              DSCP              ECN
```

---

## Architecture Overview

### System Components

The QoS subsystem spans multiple layers of the access point software stack:

```
+------------------------------------------------------------------+
|                     CLOUD / CONTROLLER                            |
|                  (Wireless Manager - WM)                          |
+------------------------------------------------------------------+
                              |
                              | Configuration Push
                              v
+------------------------------------------------------------------+
|                      AP CONFIGURATION                             |
|                                                                   |
|  +------------------+    +------------------+                     |
|  |   flatconf       |    |   ap.conf        |                     |
|  |   (Parser)       |--->|   (Config File)  |                     |
|  +------------------+    +------------------+                     |
+------------------------------------------------------------------+
                              |
                              | Configuration Processing
                              v
+------------------------------------------------------------------+
|                    GO SERVICES LAYER                              |
|                                                                   |
|  +------------------+    +------------------+                     |
|  | ardsconfwriter   |    |  configagent     |                     |
|  | (ssid_qos.go)    |    | (ssid_qos_qca.go)|                     |
|  +------------------+    +------------------+                     |
|          |                       |                                |
|          v                       v                                |
|  +------------------+    +------------------+                     |
|  |   ArDS Tree      |    |   wlanioctl      |                     |
|  |   (State Store)  |    |   (IOCTL calls)  |                     |
|  +------------------+    +------------------+                     |
+------------------------------------------------------------------+
                              |
                              | IOCTL / iwpriv
                              v
+------------------------------------------------------------------+
|                    SHELL SCRIPTS                                  |
|                                                                   |
|  +------------------+                                             |
|  |   configVAP      |  iwpriv athX set_qos <params>               |
|  +------------------+                                             |
+------------------------------------------------------------------+
                              |
                              | Kernel Interface
                              v
+------------------------------------------------------------------+
|                    WLAN DRIVER                                    |
|                                                                   |
|  +------------------+    +------------------+                     |
|  |   ar_cfg.c       |    |   ar_qos.c       |                     |
|  |   (Config)       |    |   (QoS Logic)    |                     |
|  +------------------+    +------------------+                     |
|          |                       |                                |
|          v                       v                                |
|  +------------------+    +------------------+                     |
|  |   ar_qos.h       |    |   ar_types.h     |                     |
|  |   (Definitions)  |    |   (Structures)   |                     |
|  +------------------+    +------------------+                     |
+------------------------------------------------------------------+
                              |
                              | Packet Processing
                              v
+------------------------------------------------------------------+
|                    DATA PATH                                      |
|                                                                   |
|  +------------------+    +------------------+                     |
|  |   TX Path        |    |   RX Path        |                     |
|  |   (Downstream)   |    |   (Upstream)     |                     |
|  +------------------+    +------------------+                     |
+------------------------------------------------------------------+
```

### Data Flow

1. **Configuration Origin**: QoS settings originate from the Wireless Manager (cloud controller)
2. **Configuration Delivery**: Settings are pushed to the AP via flatconf/ap.conf
3. **Configuration Processing**: Go services parse and apply the configuration
4. **Driver Configuration**: Settings are passed to the WLAN driver via IOCTL
5. **Packet Processing**: Driver applies QoS rules to each packet

---

## QoS Flag Bit Structure

The QoS configuration is encoded as an 8-bit value passed to the driver:

```
Bit Position:  7    6    5    4    3    2    1    0
               |    |    |    |    |    |    |____|
               |    |    |    |____|    |       |
               |    |    |       |      |       +-- QoS Priority (bits 0-1)
               |    |    |       |      +---------- QoS Priority Type (bit 2)
               |    |    |       +----------------- Downstream Mapping (bits 3-4)
               |    |    +------------------------- Enable 802.1p Upstream Marking (bit 5)
               |    +------------------------------ Enable DSCP Upstream Marking (bit 6)
               +----------------------------------- Enable TOS Upstream Marking (bit 7)
```

### Bit Masks (from `ar_qos.h`):
| Mask Name               | Value  | Description                      |
|------------------------|--------|----------------------------------|
| `AR_QOS_PRIO_MASK`     | 0x03   | QoS Priority (2 bits)            |
| `AR_QOS_PRIO_TYPE_MASK`| 0x04   | Priority Type: Fixed or Ceiling  |
| `AR_QOS_DSTREAM_MASK`  | 0x18   | Downstream Mapping (2 bits)      |
| `AR_QOS_USTREAM_8021P_MASK` | 0x20 | 802.1p Upstream Marking       |
| `AR_QOS_USTREAM_DSCP_MASK`  | 0x40 | DSCP Upstream Marking         |
| `AR_QOS_USTREAM_TOS_MASK`   | 0x80 | TOS Upstream Marking          |

---

## QoS Configuration Parameters

### 1. SSID Priority (`QOS_SSID_PRIORITY`)

Defines the maximum WMM Access Category for the SSID:

| Value | WMM AC   | Description           | Internal Encoding |
|-------|----------|-----------------------|-------------------|
| 0     | Voice    | Highest priority      | 3                 |
| 1     | Video    | High priority         | 2                 |
| 2     | Best Effort | Normal priority    | 0                 |
| 3     | Background | Lowest priority     | 1                 |

### 2. Priority Type (`QOS_PRIORITY_TYPE`)

| Value | Type    | Description                                           |
|-------|---------|-------------------------------------------------------|
| 0     | Ceiling | Allows priorities up to the configured SSID Priority |
| 1     | Fixed   | Forces all traffic to the configured SSID Priority   |

---

## Priority Type Deep Dive: Ceiling vs Fixed Mode

Understanding the difference between **Ceiling** and **Fixed** priority modes is crucial for proper QoS configuration. These modes fundamentally change how traffic priority is handled on an SSID.

### Ceiling Mode (Priority Type = 0)

**Ceiling mode** allows traffic to use its natural priority (derived from DSCP, 802.1p, or TOS) but **caps** it at the configured SSID priority level.

#### How Ceiling Mode Works

```
                    Incoming Packet Priority
                            |
                            v
            +-------------------------------+
            |   Extract Priority from       |
            |   DSCP / 802.1p / TOS         |
            +-------------------------------+
                            |
                            v
            +-------------------------------+
            |   Compare with SSID Priority  |
            |   (Ceiling Check)             |
            +-------------------------------+
                            |
              +-------------+-------------+
              |                           |
              v                           v
    Packet Priority <=          Packet Priority >
    SSID Priority               SSID Priority
              |                           |
              v                           v
    +-------------------+       +-------------------+
    | Use Packet's      |       | Cap to SSID       |
    | Original Priority |       | Priority Level    |
    +-------------------+       +-------------------+
```

#### Ceiling Mode Example

**Configuration:**
- SSID Priority: Video (1) → Internal AC = VI (2)
- Priority Type: Ceiling (0)
- Downstream Map: DSCP

**Behavior:**

| Incoming DSCP | Natural AC | After Ceiling | Result |
|---------------|------------|---------------|--------|
| 46 (EF) | Voice (3) | Video (2) | Capped to Video |
| 34 (AF41) | Video (2) | Video (2) | Unchanged |
| 0 (BE) | Best Effort (0) | Best Effort (0) | Unchanged |
| 8 (CS1) | Background (1) | Background (1) | Unchanged |

#### Ceiling Mode Use Cases

1. **Guest Networks**: Set ceiling to Best Effort to prevent guests from claiming high priority
2. **IoT Networks**: Limit IoT devices to Background priority
3. **General Data SSIDs**: Allow normal priority differentiation but cap at Video
4. **Untrusted Networks**: Prevent priority abuse by untrusted clients

#### Ceiling Mode Implementation

The ceiling logic is implemented using the `AR_CEIL_QOS_PRIO` and `AR_CEIL_QOS_TID` macros:

```c
/*
 * Convert AC value for comparison in Ceil Macros
 * The conversion is required because WMM category BG has higher numerical value
 * than WMM category BE whereas BE has higher priority.
 * Conversion is as follows:
 * {11,10,01,00} --> {11,10,00,01}
 *
 * This ensures proper comparison:
 * - VO (3) -> 3 (highest)
 * - VI (2) -> 2
 * - BE (0) -> 1
 * - BK (1) -> 0 (lowest)
 */
#define CONVERT_AC(_ac) (((_ac)&0x2) ? (_ac) : ((_ac) ^ 0x1))

/* Ceiling macro for AC/priority */
#define AR_CEIL_QOS_PRIO(_vap, _ac, _prio)                   \
    if (CONVERT_AC(_ac) > CONVERT_AC(AR_GET_QOS_PRIO(_vap))) { \
        (_ac) = AR_GET_QOS_PRIO(_vap);                           \
        (_prio) = WME_AC_TO_TID(_ac);                            \
    }

/* Ceiling macro for TID */
#define AR_CEIL_QOS_TID(_vap, _tid)                                          \
    if (CONVERT_AC(TID_TO_WME_AC(_tid)) > CONVERT_AC(AR_GET_QOS_PRIO(_vap))) { \
        (_tid) = WME_AC_TO_TID(AR_GET_QOS_PRIO(_vap));                           \
    }
```

#### Why CONVERT_AC is Needed

The WMM Access Categories have a quirk in their numerical values:

| AC | Value | Priority |
|----|-------|----------|
| BE | 0 | Medium |
| BK | 1 | Lowest |
| VI | 2 | High |
| VO | 3 | Highest |

Notice that BK (1) has a higher numerical value than BE (0), but BE has higher priority. The `CONVERT_AC` macro fixes this for proper comparison:

| Original | Converted | Correct Order |
|----------|-----------|---------------|
| VO (3) | 3 | Highest |
| VI (2) | 2 | High |
| BE (0) | 1 | Medium |
| BK (1) | 0 | Lowest |

### Fixed Mode (Priority Type = 1)

**Fixed mode** ignores the packet's natural priority and **forces** all traffic to the configured SSID priority level.

#### How Fixed Mode Works

```
                    Incoming Packet Priority
                            |
                            v
            +-------------------------------+
            |   IGNORE Packet Priority      |
            |   (DSCP/802.1p/TOS ignored)   |
            +-------------------------------+
                            |
                            v
            +-------------------------------+
            |   Force to SSID Priority      |
            +-------------------------------+
                            |
                            v
            +-------------------------------+
            |   All packets get same        |
            |   priority level              |
            +-------------------------------+
```

#### Fixed Mode Example

**Configuration:**
- SSID Priority: Voice (0) → Internal AC = VO (3)
- Priority Type: Fixed (1)
- Downstream Map: DSCP (ignored in Fixed mode)

**Behavior:**

| Incoming DSCP | Natural AC | After Fixed | Result |
|---------------|------------|-------------|--------|
| 46 (EF) | Voice (3) | Voice (3) | Forced to Voice |
| 34 (AF41) | Video (2) | Voice (3) | Forced to Voice |
| 0 (BE) | Best Effort (0) | Voice (3) | Forced to Voice |
| 8 (CS1) | Background (1) | Voice (3) | Forced to Voice |

#### Fixed Mode Use Cases

1. **VoIP-Only SSIDs**: Force all traffic to Voice priority
2. **Video Conferencing SSIDs**: Force all traffic to Video priority
3. **Strict Priority Enforcement**: When you need guaranteed priority regardless of packet marking
4. **Legacy Device Support**: When devices don't properly mark their traffic

#### Fixed Mode Implementation

```c
void ar_qos_dp_rx_set_prio(struct sk_buff* skb,
                            struct ar_dp_vdev_s* vdev,
                            uint8_t tid)
{
    uint8_t effective_tid;

    if (AR_IS_QOS_PRIO_FIXED(vdev)) {
        // Fixed mode: force to configured priority
        effective_tid = WME_AC_TO_TID(AR_GET_QOS_PRIO(vdev));
        ar_os_skb_set_priority(skb, effective_tid);
    } else {
        // Ceiling mode: cap at configured priority
        AR_CEIL_QOS_TID(vdev, tid);
        effective_tid = tid;
        ar_os_skb_set_priority(skb, tid);
    }

    vdrv_dp_if_ar_meta_set_tid(skb, effective_tid);
}
```

### Ceiling vs Fixed: Comparison Table

| Aspect | Ceiling Mode | Fixed Mode |
|--------|--------------|------------|
| Packet Priority | Respected (up to limit) | Ignored |
| SSID Priority | Maximum allowed | Forced value |
| Downstream Map | Used for priority extraction | Ignored |
| Traffic Differentiation | Preserved within limits | None (all same priority) |
| Use Case | General networks | Dedicated service SSIDs |
| Flexibility | High | Low |
| Control | Moderate | Strict |

### Choosing Between Ceiling and Fixed

#### Use Ceiling Mode When:
- You want to allow priority differentiation within limits
- The SSID serves multiple traffic types
- You trust the client's priority markings (within limits)
- You want to prevent priority abuse without eliminating differentiation

#### Use Fixed Mode When:
- The SSID is dedicated to a single traffic type (e.g., VoIP)
- You don't trust client priority markings at all
- You need strict, predictable priority behavior
- Legacy devices don't properly mark their traffic

### Configuration Examples

#### Example: Guest Network with Ceiling
```
QOS_SSID_PRIORITY=2     # Best Effort (ceiling)
QOS_PRIORITY_TYPE=0     # Ceiling mode
QOS_DOWNSTR_MAP=1       # Use DSCP

Result: Guest traffic can use BE or BK priority, but never VI or VO
```

#### Example: VoIP SSID with Fixed
```
QOS_SSID_PRIORITY=0     # Voice
QOS_PRIORITY_TYPE=1     # Fixed mode
QOS_DOWNSTR_MAP=1       # DSCP (ignored)

Result: All traffic on this SSID gets Voice priority
```

#### Example: Video Conferencing with Ceiling
```
QOS_SSID_PRIORITY=1     # Video (ceiling)
QOS_PRIORITY_TYPE=0     # Ceiling mode
QOS_DOWNSTR_MAP=1       # Use DSCP

Result: Video traffic gets VI, voice traffic capped to VI, data gets BE/BK
```

### 3. Downstream Mapping (`QOS_DOWNSTR_MAP`)

Determines how incoming packet priority is determined:

| Value | Source  | Description                                    |
|-------|---------|------------------------------------------------|
| 0     | 802.1p  | Priority from VLAN tag                         |
| 1     | DSCP    | Priority from IP Differentiated Services field |
| 2     | TOS     | Priority from IP Type of Service field         |

### 4. Upstream Marking (`QOS_UPSTR_MARK_*`)

Controls whether the AP marks outgoing packets:

| Parameter              | Description                          |
|-----------------------|--------------------------------------|
| `QOS_UPSTR_MARK_802_1p` | Mark 802.1p priority in VLAN tag    |
| `QOS_UPSTR_MARK_DSCP_TOS` | Mark DSCP/TOS in IP header        |

---

## WMM Access Categories and TID Mapping

### WMM Access Categories:
| AC Code | Name       | Value | Description      |
|---------|------------|-------|------------------|
| WME_AC_BE | Best Effort | 0   | Default traffic  |
| WME_AC_BK | Background  | 1   | Low priority     |
| WME_AC_VI | Video       | 2   | High priority    |
| WME_AC_VO | Voice       | 3   | Highest priority |

### TID to WMM AC Mapping:
| TID | WMM AC      |
|-----|-------------|
| 0, 3| Best Effort |
| 1, 2| Background  |
| 4, 5| Video       |
| 6, 7| Voice       |

---

## Configuration Flow

```
                    +---------------------------+
                    |   Cloud/Controller        |
                    |   (WM Configuration)      |
                    +-------------+-------------+
                                  |
                                  v
                    +---------------------------+
                    |   flatconf (ap.conf)      |
                    |   Configuration File      |
                    +-------------+-------------+
                                  |
                                  v
            +---------------------+---------------------+
            |                                           |
            v                                           v
+---------------------------+             +---------------------------+
|  ardsconfwriter           |             |  configagent              |
|  (ssid_qos.go)            |             |  (ssid_qos_qca.go)        |
|  Writes to ArDS Tree      |             |  Applies via ioctl        |
+---------------------------+             +-------------+-------------+
                                                        |
                                                        v
                                          +---------------------------+
                                          |  configVAP Script         |
                                          |  (Shell script)           |
                                          +-------------+-------------+
                                                        |
                                                        | iwpriv set_qos
                                                        v
                                          +---------------------------+
                                          |  WLAN Driver              |
                                          |  (ar_cfg.c / ar_qos.c)    |
                                          +---------------------------+
```

---

## Source Files Reference

| File | Purpose |
|------|---------|
| `ap/s4models/wificonfig/SsidConfig.tac` | QosConfig data model definition |
| `ap/src/go/arista-ap/ardsconfwriter/ssid_qos.go` | Writes QoS config to ArDS tree |
| `ap/src/go/arista-ap/configagent/ssid_qos_qca.go` | Applies QoS config via ioctl |
| `ap/rootfs/scripts/configVAP` | Shell script that calls `iwpriv set_qos` |
| `ap/src/wlan-drivers/ar/core/src/ar_qos.h` | Driver QoS definitions and macros |
| `ap/src/wlan-drivers/ar/core/src/ar_qos.c` | Driver QoS implementation |
| `ap/src/wlan-drivers/ar/core/src/ar_cfg.c` | Driver config handler (`ar_cfg_vdev_qos`) |
| `ap/src/wlan-drivers/ar/core/src/ar_types.h` | `qos_params` struct definition |

---

## QoS Parameter Calculation

The `qosFlagParam` value sent to the driver is calculated as:

```go
// From ssid_qos_qca.go
qosFlagParam = priority_encoding      // bits 0-1 (from SSID Priority mapping)
qosFlagParam += 4 * PriorityType      // bit 2
qosFlagParam += 8 * DownstreamMap     // bits 3-4
qosFlagParam += 32 * UpstreamMark8021p // bit 5
qosFlagParam += 64 * UpstreamMarkDscpTos // bit 6
```

### Priority Encoding:
| SSID Priority | Internal Value |
|---------------|----------------|
| 0 (Voice)     | 3              |
| 1 (Video)     | 2              |
| 2 (BE)        | 0              |
| 3 (BK)        | 1              |

---

## Driver QoS Application

In `ar_cfg_vdev_qos()` (ar_cfg.c), the QoS parameters are extracted and applied:

```c
AR_SET_QOS_PRIO(vdev, qos_params & AR_QOS_PRIO_MASK);
if (qos_params & AR_QOS_PRIO_TYPE_MASK) {
    AR_SET_QOS_PRIO_TYPE_FIXED(vdev);  // Fixed priority
} else {
    AR_SET_QOS_PRIO_TYPE_CEIL(vdev);   // Ceiling priority
    AR_SET_QOS_DSTREAM(vdev, (qos_params & AR_QOS_DSTREAM_MASK) >> 3);
}
AR_SET_QOS_USTREAM_DSCP(vdev, ...);
AR_SET_QOS_USTREAM_TOS(vdev, ...);
AR_SET_QOS_USTREAM_8021P(vdev, ...);
```

---

## Traffic Priority Processing

### Downstream (Ceiling Mode):
When a packet arrives, its priority is determined by the configured mapping (802.1p/DSCP/TOS), then **ceiling** logic is applied to cap the priority at the SSID's configured maximum.

### Downstream (Fixed Mode):
All packets are forced to the SSID's configured priority, ignoring packet markings.

### Functions:
- `ar_qos_dp_rx_set_prio()` - Sets packet priority on receive path
- `ar_qos_dp_set_map_dstream_8021p()` - Maps 802.1p to WMM AC
- `ar_qos_dp_set_map_dstream_dscp()` - Maps DSCP to WMM AC
- `ar_qos_dp_set_map_dstream_tos()` - Maps TOS to WMM AC

---

## Detailed Code Walkthrough

This section provides an in-depth analysis of the QoS implementation across all layers.

### Layer 1: Data Model (SsidConfig.tac)

The QoS configuration is defined in the TAC (Type-Aware Configuration) model:

```tac
/* Qos */
QosConfig : Tac::Type() : Tac::Nominal {
   ssidPriority : U8;           // SSID priority level (0-3)
   priorityType : U8;           // Fixed (1) or Ceiling (0)
   downstreamMap : U8;          // Mapping source (0=802.1p, 1=DSCP, 2=TOS)
   upstreamMark8021p : U8;      // Enable 802.1p upstream marking
   upstreamMarkDscpTos : U8;    // Enable DSCP/TOS upstream marking
   wmmEnforcePolicyEnable : bool;  // WMM policy enforcement
   wmmEnable : bool;            // WMM enabled flag
   vapMinRate : double;         // Minimum data rate
   vapMaxRate : double;         // Maximum data rate
   vapNonLegacyMaxRate : U8;    // Non-legacy max rate flag
   vapMcastMgmtRate : double;   // Multicast/management rate
   vapDisable11bRate : bool;    // Disable 802.11b rates
   vapMinRate2G : double;       // 2.4GHz minimum rate
   vapMinRate5G : double;       // 5GHz minimum rate
   vapMinRate6G : double;       // 6GHz minimum rate
   vapMaxRate2G : double;       // 2.4GHz maximum rate
   vapMaxRate5G : double;       // 5GHz maximum rate
   vapMaxRate6G : double;       // 6GHz maximum rate
   vapMcastMgmtRate2G : double; // 2.4GHz multicast rate
   vapMcastMgmtRate5G : double; // 5GHz multicast rate
   vapMcastMgmtRate6G : double; // 6GHz multicast rate
}
```

#### Field Descriptions

| Field | Type | Range | Description |
|-------|------|-------|-------------|
| `ssidPriority` | U8 | 0-3 | Maximum WMM AC for this SSID |
| `priorityType` | U8 | 0-1 | 0=Ceiling (cap), 1=Fixed (force) |
| `downstreamMap` | U8 | 0-2 | Priority source: 0=802.1p, 1=DSCP, 2=TOS |
| `upstreamMark8021p` | U8 | 0-1 | Mark 802.1p in upstream packets |
| `upstreamMarkDscpTos` | U8 | 0-1 | Mark DSCP/TOS in upstream packets |
| `wmmEnforcePolicyEnable` | bool | - | Enforce WMM policy |
| `wmmEnable` | bool | - | Enable WMM for this SSID |
| `vapMinRate` | double | 0-54 | Minimum rate in Mbps |
| `vapMaxRate` | double | 0-54 | Maximum rate in Mbps |

### Layer 2: Configuration Writer (ssid_qos.go)

The `ardsconfwriter` package handles writing QoS configuration to the ArDS tree:

```go
// qosConfigMap maps struct fields to configuration keys
var qosConfigMap = map[string]string{
    "SsidPriority":           "QOS_SSID_PRIORITY",
    "PriorityType":           "QOS_PRIORITY_TYPE",
    "DownstreamMap":          "QOS_DOWNSTR_MAP",
    "UpstreamMark8021p":      "QOS_UPSTR_MARK_802_1p",
    "UpstreamMarkDscpTos":    "QOS_UPSTR_MARK_DSCP_TOS",
    "WmmEnforcePolicyEnable": "WMM_ENFORCE_POLICY_ENABLE",
    "WmmEnable":              "WMM_ENABLE",
    "VapMinRate":             "VAP_MIN_RATE",
    "VapMaxRate":             "VAP_MAX_RATE",
    "VapNonLegacyMaxRate":    "VAP_NONLEGACY_MAX_RATE",
    "VapMcastMgmtRate":       "VAP_MCAST_MGMT_RATE",
    "VapDisable11bRate":      "VAP_DISABLE_11B_RATES",
    "VapMinRate2G":           "VAP_MIN_RATE_2.4G",
    "VapMinRate5G":           "VAP_MIN_RATE_5G",
    "VapMinRate6G":           "VAP_MIN_RATE_6G",
    "VapMaxRate2G":           "VAP_MAX_RATE_2.4G",
    "VapMaxRate5G":           "VAP_MAX_RATE_5G",
    "VapMaxRate6G":           "VAP_MAX_RATE_6G",
    "VapMcastMgmtRate2G":     "VAP_MCAST_MGMT_RATE_2.4G",
    "VapMcastMgmtRate5G":     "VAP_MCAST_MGMT_RATE_5G",
    "VapMcastMgmtRate6G":     "VAP_MCAST_MGMT_RATE_6G",
}

// writeQosConfigToArDS writes QoS configuration to the ArDS tree
func writeQosConfigToArDS(ssid *wificonfig.Ssid, qosConfig *wificonfig.QosConfig) {
    logPrefix := "[writeQosConfigToArDS]"
    tree.Lock()
    ssid.QosConfigSet(*qosConfig)
    tree.Unlock()
    glog.Infof("%v Profile %v, qosConfig written to ArDS: %v",
               logPrefix, ssid.ProfileId, *qosConfig)
}

// getQosConfig retrieves QoS configuration from flatconf
func getQosConfig(ssid *wificonfig.Ssid, flatconf *flatapconf.APConf,
    vapSectionID int, isFlatConfPartial bool) (*wificonfig.QosConfig, error) {
    logPrefix := "[getQosConfig]"

    qosConfig := &wificonfig.QosConfig{}
    if isFlatConfPartial {
        glog.Infof("%v Copying current qosConfig to new qosConfig struct for partial ap.conf",
                   logPrefix)
        aputils.CopyStructFields(qosConfig, &ssid.QosConfig)
    }

    err := populateFeatureValues(qosConfig, flatconf, ssidSection,
        vapSectionID, qosConfigMap, isFlatConfPartial)
    if err != nil {
        glog.Errorf("%v Error getting qosConfig from populateFeatureValues, err: %v",
                    logPrefix, err)
        return nil, err
    }

    return qosConfig, nil
}
```

### Layer 3: Configuration Agent (ssid_qos_qca.go)

The `configagent` package applies QoS configuration to the wireless interface:

```go
// setQosFlagParam sets QoS flags via IOCTL
func setQosFlagParam(action string, vapName string, qosFlagParam uint,
    logPrefix string, errors map[string]radiomgrstate.ErrorDetails) {
    err := RadioIoctl(action, vapName, SET, uintptr(qosFlagParam))
    if err != nil {
        glog.Errorf(logPrefix+"Failed to set %s: %v for %v ",
                    action, qosFlagParam, vapName)
        addErrorDetails(errors, "set_qos", err)
    } else {
        glog.Infof(logPrefix+"Set %s: %v for %v", action, qosFlagParam, vapName)
    }
}

// applyQosConfig applies the complete QoS configuration
func applyQosConfig(profileID uint32, qosParams qosParamsQca, dual5GHzEnable bool,
    callback func(uint32, string, wificonfig.QosConfig,
                  map[string]radiomgrstate.ErrorDetails)) error {
    logPrefix := "[applyQosConfig]"

    isBoot := qosParams.boot
    notConfigured := qosParams.notConfigured
    vapName := qosParams.vapName
    config := qosParams.newQos
    state := qosParams.curQos

    var err error
    var errors = map[string]radiomgrstate.ErrorDetails{}

    // Check if QoS parameters need to be updated
    if isBoot || notConfigured || config.SsidPriority != state.SsidPriority ||
        config.PriorityType != state.PriorityType ||
        config.DownstreamMap != state.DownstreamMap ||
        config.UpstreamMark8021p != state.UpstreamMark8021p ||
        config.UpstreamMarkDscpTos != state.UpstreamMarkDscpTos {

        // Calculate qosFlagParam
        var qosFlagParam uint
        switch config.SsidPriority {
        case 0:
            qosFlagParam = 3  // Voice -> internal 3
        case 1:
            qosFlagParam = 2  // Video -> internal 2
        case 2:
            qosFlagParam = 0  // Best Effort -> internal 0
        default:
            qosFlagParam = 1  // Background -> internal 1
        }

        qosFlagParam += 4 * uint(config.PriorityType)      // bit 2
        qosFlagParam += 8 * uint(config.DownstreamMap)     // bits 3-4
        qosFlagParam += 32 * uint(config.UpstreamMark8021p)   // bit 5
        qosFlagParam += 64 * uint(config.UpstreamMarkDscpTos) // bit 6

        setQosFlagParam(wlanioctl.SetQos, vapName, qosFlagParam, logPrefix, errors)
    }

    // Handle rate configurations...
    // (rate handling code continues)

    callback(profileID, vapName, config, errors)
    return err
}
```

### Layer 4: Shell Script (configVAP)

The `configVAP` script handles QoS configuration via `iwpriv`:

```bash
qos_params_set() {
    if [ "$QOS_SSID_PRIORITY" != "" ]; then
        # Map SSID priority to internal encoding
        if [ $QOS_SSID_PRIORITY -eq 0 ]; then
            QOS_PARAMS=3    # Voice
        elif [ $QOS_SSID_PRIORITY -eq 1 ]; then
            QOS_PARAMS=2    # Video
        elif [ $QOS_SSID_PRIORITY -eq 2 ]; then
            QOS_PARAMS=0    # Best Effort
        else
            QOS_PARAMS=1    # Background
        fi

        # Add priority type (bit 2)
        TEMP=$(expr 4 \* $QOS_PRIORITY_TYPE)
        QOS_PARAMS=$(expr $QOS_PARAMS + $TEMP)

        # Add downstream mapping (bits 3-4)
        TEMP=$(expr 8 \* $QOS_DOWNSTR_MAP)
        QOS_PARAMS=$(expr $QOS_PARAMS + $TEMP)

        # Add 802.1p upstream marking (bit 5)
        TEMP=$(expr 32 \* $QOS_UPSTR_MARK_802_1p)
        QOS_PARAMS=$(expr $QOS_PARAMS + $TEMP)

        # Add DSCP/TOS upstream marking (bit 6)
        TEMP=$(expr 64 \* $QOS_UPSTR_MARK_DSCP_TOS)
        QOS_PARAMS=$(expr $QOS_PARAMS + $TEMP)

        ##############
        # QoS Flags
        # 7 -------------------- 0
        # 0-1   :       QoS Priority
        # 2     :       QoS Priority Type (Fixed / Ceil)
        # 3-4   :       Downstream Mapping
        # 5     :       Enable 802.1p Upstream Marking
        # 6     :       Enable DSCP Upstream Marking
        # 7     :       Enable TOS Upstream Marking
        ##############

        iwpriv $APNAME set_qos $QOS_PARAMS
        UNI_ID_LOG PROFILE $PROFILE_ID "INFO: Set QoS $QOS_PARAMS"
    fi
}
```

### Layer 5: Driver Configuration (ar_cfg.c)

The driver receives QoS configuration via IOCTL:

```c
/**
 * @brief QoS configuration handler
 *
 * @param vdev VAP handle
 * @param data pointer to QoS parameters from user
 *
 * @return AR_STATUS
 */
static AR_STATUS ar_cfg_vdev_qos(struct ar_dp_vdev_s* vdev, char* data)
{
    AR_STATUS status = AR_STATUS_SUCCESS;
    int* i = (int*)data;
    int qos_params = i[1];

    // Clear existing QoS configuration
    memset(&(vdev->qos), 0, sizeof(vdev->qos));

    // Extract and set priority (bits 0-1)
    AR_SET_QOS_PRIO(vdev, qos_params & AR_QOS_PRIO_MASK);

    // Check priority type (bit 2)
    if (qos_params & AR_QOS_PRIO_TYPE_MASK) {
        // Priority Type = Fixed
        AR_SET_QOS_PRIO_TYPE_FIXED(vdev);
    } else {
        // Priority Type = Ceiling
        AR_SET_QOS_PRIO_TYPE_CEIL(vdev);
        // Set downstream mapping (bits 3-4)
        AR_SET_QOS_DSTREAM(vdev, (qos_params & AR_QOS_DSTREAM_MASK) >> 3);
    }

    // Set upstream marking flags
    AR_SET_QOS_USTREAM_DSCP(vdev, qos_params & AR_QOS_USTREAM_DSCP_MASK ? 1 : 0);
    AR_SET_QOS_USTREAM_TOS(vdev, qos_params & AR_QOS_USTREAM_TOS_MASK ? 1 : 0);
    AR_SET_QOS_USTREAM_8021P(vdev, qos_params & AR_QOS_USTREAM_8021P_MASK ? 1 : 0);

    return status;
}
```

### Layer 6: QoS Data Path (ar_qos.c)

The QoS logic is applied to packets in the data path:

```c
/**
 * @brief Set skb priority according to Rx TID
 *
 * This function sets the skb priority based on the TID value. It also
 * caches the effective TID in ar_meta for efficient subsequent access
 * without requiring CB (control block) lookups.
 *
 * @param skb Network buffer pointer
 * @param vdev VAP handle
 * @param tid QoS TID to be set for the packet
 */
void ar_qos_dp_rx_set_prio(struct sk_buff* skb, struct ar_dp_vdev_s* vdev, uint8_t tid)
{
    uint8_t effective_tid;
    uint8_t original_tid = tid;

    if (AR_IS_QOS_PRIO_FIXED(vdev)) {
        // Fixed mode: force to configured priority
        effective_tid = WME_AC_TO_TID(AR_GET_QOS_PRIO(vdev));
        ar_os_skb_set_priority(skb, effective_tid);
    } else {
        // Ceiling mode: cap at configured priority
        AR_CEIL_QOS_TID(vdev, tid);
        effective_tid = tid;
        ar_os_skb_set_priority(skb, tid);
    }

    // Cache effective TID in ar_meta for subsequent access
    vdrv_dp_if_ar_meta_set_tid(skb, effective_tid);

#if AR_META_TID_DEBUG
    pr_info("ar_meta_tid: [AR_QOS] skb=%pK orig_tid=%u effective_tid=%u "
            "ar_meta.tid=%u fixed=%d\n",
            skb, original_tid, effective_tid, skb->ar_meta.tid,
            AR_IS_QOS_PRIO_FIXED(vdev) ? 1 : 0);
#endif
}
```

### Layer 7: QoS Structures (ar_types.h)

The QoS parameters are stored in the vdev structure:

```c
struct qos_params {
    unsigned prio : 2;        // QoS priority (0-3)
    unsigned prio_type : 1;   // Priority type (0=ceiling, 1=fixed)
    unsigned dstream : 2;     // Downstream mapping source
    unsigned ustream_dscp : 1; // DSCP upstream marking
    unsigned ustream_tos : 1;  // TOS upstream marking
    unsigned ustream_8021p : 1; // 802.1p upstream marking
} qos; /**< QoS configuration */
```

---

## Example Configurations

### Example 1: Voice-Priority SSID with Fixed Priority
```
QOS_SSID_PRIORITY=0     # Voice (highest)
QOS_PRIORITY_TYPE=1     # Fixed
QOS_DOWNSTR_MAP=1       # DSCP (not used in fixed mode)
QOS_UPSTR_MARK_802_1p=0
QOS_UPSTR_MARK_DSCP_TOS=0

Calculated: qosFlagParam = 3 + 4*1 + 8*1 = 15 (0x0F)
```
All traffic on this SSID is forced to Voice priority.

### Example 2: Best Effort SSID with Ceiling and DSCP Mapping
```
QOS_SSID_PRIORITY=2     # Best Effort
QOS_PRIORITY_TYPE=0     # Ceiling
QOS_DOWNSTR_MAP=1       # DSCP
QOS_UPSTR_MARK_802_1p=0
QOS_UPSTR_MARK_DSCP_TOS=1

Calculated: qosFlagParam = 0 + 0 + 8*1 + 64*1 = 72 (0x48)
```
Traffic priority is determined by DSCP, but capped at Best Effort.

### Example 3: Video SSID with 802.1p Mapping and Upstream Marking
```
QOS_SSID_PRIORITY=1     # Video
QOS_PRIORITY_TYPE=0     # Ceiling
QOS_DOWNSTR_MAP=0       # 802.1p
QOS_UPSTR_MARK_802_1p=1 # Enable 802.1p marking
QOS_UPSTR_MARK_DSCP_TOS=0

Calculation:
- Priority encoding for Video (1) = 2
- Priority type (0) = 0 * 4 = 0
- Downstream map (0) = 0 * 8 = 0
- 802.1p marking (1) = 1 * 32 = 32
- DSCP marking (0) = 0 * 64 = 0

qosFlagParam = 2 + 0 + 0 + 32 + 0 = 34 (0x22)
```
Traffic uses 802.1p for priority, capped at Video, with 802.1p marking on upstream.

### Example 4: Background SSID with TOS Mapping
```
QOS_SSID_PRIORITY=3     # Background
QOS_PRIORITY_TYPE=0     # Ceiling
QOS_DOWNSTR_MAP=2       # TOS
QOS_UPSTR_MARK_802_1p=0
QOS_UPSTR_MARK_DSCP_TOS=0

Calculation:
- Priority encoding for Background (3) = 1
- Priority type (0) = 0 * 4 = 0
- Downstream map (2) = 2 * 8 = 16
- 802.1p marking (0) = 0 * 32 = 0
- DSCP marking (0) = 0 * 64 = 0

qosFlagParam = 1 + 0 + 16 + 0 + 0 = 17 (0x11)
```
Low-priority SSID using TOS for priority determination.

### Example 5: Full QoS Configuration with All Markings
```
QOS_SSID_PRIORITY=0     # Voice
QOS_PRIORITY_TYPE=0     # Ceiling
QOS_DOWNSTR_MAP=1       # DSCP
QOS_UPSTR_MARK_802_1p=1 # Enable
QOS_UPSTR_MARK_DSCP_TOS=1 # Enable

Calculation:
- Priority encoding for Voice (0) = 3
- Priority type (0) = 0 * 4 = 0
- Downstream map (1) = 1 * 8 = 8
- 802.1p marking (1) = 1 * 32 = 32
- DSCP marking (1) = 1 * 64 = 64

qosFlagParam = 3 + 0 + 8 + 32 + 64 = 107 (0x6B)
```
Voice SSID with DSCP mapping and full upstream marking.

### Example 6: OpenConfig Default QoS Settings
```go
// From ocagent/setconfig.go
s.items["QOS_SSID_PRIORITY"] = 0     // Voice=>0, Video=>1, BE=>2, BG=>3
s.items["QOS_PRIORITY_TYPE"] = 0     // Ceiling=>0, Fixed=>1
s.items["QOS_DOWNSTR_MAP"] = 1       // 802.1p=>0, DSCP=>1, TOS=>2
s.items["QOS_UPSTR_MARK_802_1p"] = 0 // mark 802.1p upstream
s.items["QOS_UPSTR_MARK_DSCP_TOS"] = 0 // or 1 if TrustDscp is false
```

### Configuration Scenarios Table

| Scenario | Priority | Type | DStream | 802.1p Mark | DSCP Mark | qosFlagParam |
|----------|----------|------|---------|-------------|-----------|--------------|
| VoIP SSID | Voice (0) | Fixed (1) | DSCP (1) | No (0) | No (0) | 15 |
| Video Conf | Video (1) | Ceiling (0) | DSCP (1) | No (0) | Yes (1) | 74 |
| Guest WiFi | BE (2) | Ceiling (0) | 802.1p (0) | No (0) | No (0) | 0 |
| IoT Network | BK (3) | Fixed (1) | TOS (2) | No (0) | No (0) | 21 |
| Enterprise | Voice (0) | Ceiling (0) | DSCP (1) | Yes (1) | Yes (1) | 107 |

---

## 802.1p to WMM TID Mapping

| 802.1p Value | Description          | WMM TID |
|--------------|----------------------|---------|
| 0            | Background           | 1       |
| 1            | Best effort          | 0       |
| 2            | Excellent effort     | 3       |
| 3            | Critical apps        | 4       |
| 4            | Video                | 5       |
| 5            | Voice                | 6       |
| 6            | Internetwork control | 7       |
| 7            | Network control      | 7       |

### 802.1p Mapping Implementation

The mapping is implemented in `ar_qos_dp_set_map_dstream_8021p()`:

```c
void ar_qos_dp_set_map_dstream_8021p(struct sk_buff* skb,
                                      struct ar_dp_vdev_s* vdev,
                                      int* v_wme_ac, int* v_pri)
{
    int tid;
    int pri = *v_pri;
    struct vlan_ethhdr* veth = (struct vlan_ethhdr*)skb->data;

    // Check for VLAN tag in skb
    if (unlikely(ar_os_skb_vlan_tag_present(skb))) {
        uint32_t tag = ar_os_skb_vlan_tag_get(skb);
        pri = (tag >> VLAN_PRI_SHIFT) & VLAN_PRI_MASK;
    } else {
        // Check for VLAN type in packet header
        if (veth->h_vlan_proto == __constant_htons(ETH_P_8021Q)) {
            pri = (veth->h_vlan_TCI >> VLAN_PRI_SHIFT) & VLAN_PRI_MASK;
        }
    }

    /* 802.1P to WMM mapping:
    ** 802.1P            :    WMM TID
    ** ======================================
    ** 0 (Background)       : 1 (Background)
    ** 1 (Best effort)      : 0 (Best effort)
    ** 2 (Excellent effort) : 3 (Best effort)
    ** 3 (Critical apps)    : 4 (Video)
    ** 4 (Video)            : 5 (Video)
    ** 5 (Voice)            : 6 (Voice)
    ** 6 (Internetwork ctrl): 7 (Voice)
    ** 7 (Network ctrl)     : 7 (Voice)
    */
    switch (pri) {
        case 0: tid = 1; break;
        case 1: tid = 0; break;
        case 2: tid = 3; break;
        case 3: tid = 4; break;
        case 4: tid = 5; break;
        case 5: tid = 6; break;
        case 6:
        case 7: tid = 7; break;
        default: tid = 0; break;
    }

    *v_wme_ac = AR_TID_TO_WME_AC(tid);
    AR_CEIL_QOS_PRIO(vdev, *v_wme_ac, tid);
    vdrv_dp_if_wbuf_set_tid(skb, tid);
    skb->priority = *v_wme_ac;
    *v_pri = tid;
}
```

---

## DSCP and TOS Mapping

### DSCP to WMM Mapping

DSCP values are mapped to WMM access categories based on the traffic class:

| DSCP Range | Traffic Class | WMM AC |
|------------|---------------|--------|
| 0-7 | Best Effort | BE |
| 8-15 | Class Selector 1 | BK |
| 16-23 | Class Selector 2 | BE |
| 24-31 | Class Selector 3 | VI |
| 32-39 | Class Selector 4 | VI |
| 40-47 | Class Selector 5 | VI |
| 46 | Expedited Forwarding | VO |
| 48-55 | Class Selector 6 | VO |
| 56-63 | Class Selector 7 | VO |

### DSCP Mapping Implementation

```c
AR_STATUS ar_qos_dp_set_map_dstream_dscp(struct sk_buff* skb,
                                          struct ar_dp_vdev_s* vdev,
                                          int* v_wme_ac, int* v_pri)
{
    struct ether_header* eh = (struct ether_header*)skb_mac_header(skb);
    int pri = *v_pri, linear_len;
    int wme_ac = *v_wme_ac;

    if (eh->ether_type == __constant_htons(ETHERTYPE_IP)) {
        const struct iphdr* ip = (struct iphdr*)skb_network_header(skb);
        linear_len = sizeof(struct ether_header) + sizeof(struct iphdr);
        if (!pskb_may_pull(skb, linear_len))
            return AR_STATUS_EARLY_RETURN;
        ip = (struct iphdr*)skb_network_header(skb);

        // Extract DSCP: exclude ECN bits 0-1, map DSCP bits 2-7
        pri = (ip->tos & (~INET_ECN_MASK));
    } else if (eh->ether_type == __constant_htons(ETHERTYPE_IPV6)) {
        const struct ipv6hdr* ip = (struct ipv6hdr*)skb_network_header(skb);
        linear_len = sizeof(struct ether_header) + sizeof(struct ipv6hdr);
        if (!pskb_may_pull(skb, linear_len))
            return AR_STATUS_EARLY_RETURN;
        ip = (struct ipv6hdr*)skb_network_header(skb);

        pri = ip->priority;
        pri = pri << 4;
        pri = pri | (((ip->flow_lbl[0]) >> 4) & 0x0f);
    } else {
        return AR_STATUS_EARLY_RETURN;
    }

    // Special handling for DSCP 46 (Expedited Forwarding)
    if ((pri >> 2) == 46) {
        wme_ac = WME_AC_VO;
        pri = AR_WME_AC_TO_TID(wme_ac);
    } else {
        pri = pri >> IP_PRI_SHIFT;
        wme_ac = AR_TID_TO_WME_AC(pri);
    }

    AR_CEIL_QOS_PRIO(vdev, wme_ac, pri);
    vdrv_dp_if_wbuf_set_tid(skb, pri);
    skb->priority = wme_ac;
    *v_pri = pri;
    *v_wme_ac = wme_ac;
    return AR_STATUS_SUCCESS;
}
```

### TOS Mapping Implementation

```c
AR_STATUS ar_qos_dp_set_map_dstream_tos(struct sk_buff* skb,
                                         struct ar_dp_vdev_s* vdev,
                                         int* v_wme_ac, int* v_pri)
{
    struct ether_header* eh = (struct ether_header*)skb_mac_header(skb);
    int pri = *v_pri, linear_len;

    if (eh->ether_type == __constant_htons(ETHERTYPE_IP)) {
        const struct iphdr* ip = (struct iphdr*)skb_network_header(skb);
        linear_len = sizeof(struct ether_header) + sizeof(struct iphdr);
        if (!pskb_may_pull(skb, linear_len))
            return AR_STATUS_EARLY_RETURN;
        ip = (struct iphdr*)skb_network_header(skb);

        // Exclude ECN bits and map DSCP bits from TOS byte
        pri = (ip->tos & (~INET_ECN_MASK)) >> IP_PRI_SHIFT;
    } else if (eh->ether_type == __constant_htons(ETHERTYPE_IPV6)) {
        const struct ipv6hdr* ip = (struct ipv6hdr*)skb_network_header(skb);
        linear_len = sizeof(struct ether_header) + sizeof(struct ipv6hdr);
        if (!pskb_may_pull(skb, linear_len))
            return AR_STATUS_EARLY_RETURN;
        ip = (struct ipv6hdr*)skb_network_header(skb);

        pri = ip->priority;
        pri = (pri << 4);
        pri = pri | (((ip->flow_lbl[0]) >> 4) & 0x0f);
        pri = (pri >> IP_PRI_SHIFT);
    } else {
        return AR_STATUS_EARLY_RETURN;
    }

    *v_wme_ac = AR_TID_TO_WME_AC(pri);
    AR_CEIL_QOS_PRIO(vdev, *v_wme_ac, pri);
    vdrv_dp_if_wbuf_set_tid(skb, pri);
    skb->priority = *v_wme_ac;
    *v_pri = pri;
    return AR_STATUS_SUCCESS;
}
```

### DSCP Value Reference Table

| DSCP | Binary | Name | Description | Recommended WMM |
|------|--------|------|-------------|-----------------|
| 0 | 000000 | BE | Best Effort | AC_BE |
| 8 | 001000 | CS1 | Scavenger | AC_BK |
| 10 | 001010 | AF11 | High-Throughput Data | AC_BE |
| 12 | 001100 | AF12 | High-Throughput Data | AC_BE |
| 14 | 001110 | AF13 | High-Throughput Data | AC_BE |
| 16 | 010000 | CS2 | OAM | AC_BE |
| 18 | 010010 | AF21 | Low-Latency Data | AC_BE |
| 20 | 010100 | AF22 | Low-Latency Data | AC_BE |
| 22 | 010110 | AF23 | Low-Latency Data | AC_BE |
| 24 | 011000 | CS3 | Broadcast Video | AC_VI |
| 26 | 011010 | AF31 | Multimedia Streaming | AC_VI |
| 28 | 011100 | AF32 | Multimedia Streaming | AC_VI |
| 30 | 011110 | AF33 | Multimedia Streaming | AC_VI |
| 32 | 100000 | CS4 | Real-Time Interactive | AC_VI |
| 34 | 100010 | AF41 | Multimedia Conferencing | AC_VI |
| 36 | 100100 | AF42 | Multimedia Conferencing | AC_VI |
| 38 | 100110 | AF43 | Multimedia Conferencing | AC_VI |
| 40 | 101000 | CS5 | Signaling | AC_VI |
| 46 | 101110 | EF | Telephony | AC_VO |
| 48 | 110000 | CS6 | Network Control | AC_VO |
| 56 | 111000 | CS7 | Network Control | AC_VO |

---

## Hotspot 2.0 QoS Map

Hotspot 2.0 (HS2.0) networks can define custom QoS mappings via the QoS Map element.

### QoS Map Structure

```c
struct ar_ieee80211_qos_map {
    struct ar_ieee80211_dscp_range up[AR_IEEE80211_MAX_QOS_UP_RANGE];
    uint16_t valid;
    uint16_t num_dscp_except;
    struct ar_ieee80211_dscp_exception dscp_exception[AR_IEEE80211_MAX_QOS_DSCP_EXCEPT];
};

struct ar_ieee80211_dscp_range {
    uint8_t low;
    uint8_t high;
};

struct ar_ieee80211_dscp_exception {
    uint8_t dscp;
    uint8_t up;
};
```

### HS2.0 QoS Map Processing

```c
void ar_qos_dp_set_hs20_qos_map(struct sk_buff* skb,
                                 struct ar_dp_peer_s* peer,
                                 struct ar_dp_vdev_s* vdev,
                                 int* v_wme_ac, int* v_pri)
{
    int ac = WME_AC_BE;
    int tid;
    struct ether_header* eh = (struct ether_header*)skb_mac_header(skb);

    if (unlikely(vdev->qos_map.valid)) {
        int i;
        u_int8_t dscp = 0;
        struct iphdr* ip;
        struct ar_ieee80211_qos_map* qos_map = &vdev->qos_map;

        // Extract DSCP from packet
        switch (ntohs(eh->ether_type)) {
            case ETHERTYPE_IP:
                ip = (struct iphdr*)skb_network_header(skb);
                dscp = (ip->tos & (~INET_ECN_MASK)) >> 2;
                break;
            case ETHERTYPE_IPV6:
                // IPv6 handling...
                break;
            case ETHERTYPE_PAE:
                // EAPOL frames get Voice priority
                tid = 6;
                goto found;
        }

        // Search DSCP exceptions first
        for (i = 0; i < qos_map->num_dscp_except; i++) {
            if (qos_map->dscp_exception[i].dscp == dscp) {
                tid = qos_map->dscp_exception[i].up;
                goto found;
            }
        }

        // Search UP range
        for (i = 0; i < AR_IEEE80211_MAX_QOS_UP_RANGE; i++) {
            if (qos_map->up[i].low <= dscp && qos_map->up[i].high >= dscp) {
                tid = i;
                goto found;
            }
        }

        // Fallback: no match means TID=0, AC=BE
        tid = 0;
    } else {
        tid = 0;
    }

found:
    ac = AR_TID_TO_WME_AC(tid);
    vdrv_dp_if_wbuf_set_tid(skb, tid);
    skb->priority = ac;
    *v_wme_ac = ac;
    *v_pri = tid;
}
```

### Configuring HS2.0 QoS Map

The QoS Map is configured via the `qosMapSet` and `qosMapSetExceptions` fields in the Hotspot configuration:

```tac
HotspotConfig : Tac::Type() : Tac::Nominal {
    // ... other fields ...
    qosMapSet : Tac::String;           // DSCP ranges for each UP
    qosMapSetExceptions : Tac::String; // DSCP exception mappings
    // ... other fields ...
}
```

---

## Rate Limiting and QoS

QoS configuration includes rate limiting parameters that work alongside priority settings.

### Rate Parameters

| Parameter | Description | Range |
|-----------|-------------|-------|
| `vapMinRate` | Minimum data rate (Mbps) | 0-54 |
| `vapMaxRate` | Maximum data rate (Mbps) | 0-54 |
| `vapMcastMgmtRate` | Multicast/management rate | 0-54 |
| `vapMinRate2G/5G/6G` | Band-specific minimum rates | 0-54 |
| `vapMaxRate2G/5G/6G` | Band-specific maximum rates | 0-54 |

### Rate Configuration Logic

```go
func applyQosConfig(...) error {
    // Determine final rates based on band
    minRateAllBand := -1.0
    minRateBandSpecific := -1.0

    switch wBand {
    case "2G":
        if config.VapMinRate2G != state.VapMinRate2G {
            minRateBandSpecific = config.VapMinRate2G
        }
    case "5G":
        if config.VapMinRate5G != state.VapMinRate5G {
            minRateBandSpecific = config.VapMinRate5G
        }
    case "6G":
        if config.VapMinRate6G != state.VapMinRate6G {
            minRateBandSpecific = config.VapMinRate6G
        }
    }

    // Band-specific takes precedence over all-band
    finalMinRate := maxValue(minRateAllBand, minRateBandSpecific)

    if finalMinRate != -1.0 {
        finalMinRate = finalMinRate * 2  // Convert to driver units
        if finalMinRate >= 0 && finalMinRate <= 108 {
            setRate(wlanioctl.SetMinRate, vapName, finalMinRate, ...)
        }
    }
}
```

### Rate Conversion

Rates are converted for the driver:
- User-facing rates are in Mbps (e.g., 6, 12, 24, 54)
- Driver rates are multiplied by 2 (e.g., 12, 24, 48, 108)
- Multicast rates are multiplied by 500 (e.g., 6 Mbps = 6000)

---

## VLAN QoS Integration

QoS settings integrate with VLAN configuration for proper priority handling.

### VLAN QoS Maps

```go
// setVlanQoSMaps configures VLAN egress and ingress QoS maps
func setVlanQoSMaps(wmmEnable bool, intfName string, vlanID uint16) {
    for i := uint8(0); i < 8; i++ {
        if wmmEnable {
            // WMM enabled: 1:1 mapping for egress and ingress
            nwutils.VconfigSetEgressMap(intfName, vlanID, i, i)
            nwutils.VconfigSetIngressMap(intfName, vlanID, i, i)
        } else {
            // WMM disabled: map all to priority 0
            nwutils.VconfigSetEgressMap(intfName, vlanID, i, 0)
            nwutils.VconfigSetIngressMap(intfName, vlanID, 0, i)
        }
    }
}
```

### WMM Enable Check

```go
func getWmmEnable(ssidConf *wificonfig.Ssid, ssidState *radiomgrstate.Ssid) bool {
    // MLD interface is not mapped to physical radio
    if ssidState.MloEnabled {
        return true
    }
    return ssidConf.QosConfig.WmmEnable
}
```

---

## Debugging QoS

### Check Current QoS Settings
```bash
# View QoS configuration in configVAP logs
grep -i qos /var/log/messages

# Check driver QoS via iwpriv
iwpriv athX get_qos
```

### Key Log Prefixes
- `[applyQosConfig]` - configagent QoS application
- `[writeQosConfigToArDS]` - ArDS tree writes
- `[qos]` - General QoS logging

### Driver Debug Logging

Enable QoS debug logging in the driver:

```c
// In ar_qos.c
#define AR_META_TID_DEBUG 1

// This enables logging like:
// ar_meta_tid: [AR_QOS] skb=0xffff... orig_tid=6 effective_tid=6 ar_meta.tid=6 fixed=0
```

### Checking QoS State via procfs

```bash
# View VAP QoS configuration
cat /proc/net/athX/qos_config

# View per-client QoS statistics
cat /proc/net/athX/client_qos_stats
```

### Using tcpdump for QoS Analysis

```bash
# Capture packets and show TOS/DSCP values
tcpdump -i athX -v -n 'ip'

# Filter for specific DSCP values (e.g., EF = 46)
tcpdump -i athX -n 'ip[1] & 0xfc == 184'

# Capture VLAN tagged traffic
tcpdump -i athX -e -n 'vlan'
```

### Common Debug Scenarios

#### Scenario 1: Verify QoS is Applied
```bash
# Check if QoS parameters were set
grep "Set QoS" /var/log/messages

# Expected output:
# configVAP: INFO: Set QoS 15
```

#### Scenario 2: Check Priority Mapping
```bash
# Monitor packet priorities
cat /sys/kernel/debug/ieee80211/phy0/netdev:athX/queues/*/tx_priority
```

#### Scenario 3: Verify WMM is Enabled
```bash
# Check WMM status
iwpriv athX get_wmm

# Check WMM parameters
iwpriv athX getwmmparams
```

---

## Troubleshooting Guide

### Common Issues and Solutions

#### Issue 1: Voice Traffic Not Getting Priority

**Symptoms:**
- VoIP calls have poor quality
- Voice packets are delayed

**Possible Causes:**
1. QoS not configured for Voice priority
2. Priority type set to Fixed with wrong priority
3. Downstream mapping not matching packet markings

**Solutions:**
```bash
# Check current QoS settings
iwpriv athX get_qos

# Verify SSID priority is set to Voice (0)
grep QOS_SSID_PRIORITY /tmp/ap.conf

# Ensure priority type is Ceiling (0) or Fixed with Voice
grep QOS_PRIORITY_TYPE /tmp/ap.conf
```

#### Issue 2: All Traffic Same Priority

**Symptoms:**
- No differentiation between traffic types
- Background traffic affects voice/video

**Possible Causes:**
1. Priority type set to Fixed
2. WMM disabled
3. Downstream mapping source doesn't match traffic

**Solutions:**
```bash
# Check if WMM is enabled
grep WMM_ENABLE /tmp/ap.conf

# Verify priority type is Ceiling
grep QOS_PRIORITY_TYPE /tmp/ap.conf

# Check downstream mapping matches traffic type
grep QOS_DOWNSTR_MAP /tmp/ap.conf
```

#### Issue 3: Upstream Marking Not Working

**Symptoms:**
- Packets leaving AP don't have expected markings
- Downstream network equipment doesn't see priority

**Possible Causes:**
1. Upstream marking not enabled
2. VLAN not configured properly
3. Bridge stripping markings

**Solutions:**
```bash
# Enable 802.1p upstream marking
grep QOS_UPSTR_MARK_802_1p /tmp/ap.conf

# Enable DSCP upstream marking
grep QOS_UPSTR_MARK_DSCP_TOS /tmp/ap.conf

# Verify VLAN QoS maps
cat /proc/net/vlan/athX.100
```

#### Issue 4: QoS Configuration Not Applied

**Symptoms:**
- Configuration changes don't take effect
- Driver shows old QoS values

**Possible Causes:**
1. Configuration not pushed to driver
2. VAP not restarted after change
3. Error in configuration parsing

**Solutions:**
```bash
# Check for configuration errors
grep -i "error\|fail" /var/log/messages | grep -i qos

# Force reconfiguration
iwpriv athX set_qos <value>

# Restart VAP
ifconfig athX down && ifconfig athX up
```

#### Issue 5: Ceiling Mode Not Capping Priority

**Symptoms:**
- High-priority traffic exceeds configured ceiling
- Background SSID has voice-priority traffic

**Possible Causes:**
1. Priority type incorrectly set to Fixed
2. Ceiling macro not working correctly
3. Priority encoding mismatch

**Solutions:**
```bash
# Verify priority type is 0 (Ceiling)
iwpriv athX get_qos

# Check driver logs for ceiling application
dmesg | grep -i "ceil\|qos"
```

### Diagnostic Commands Reference

| Command | Description |
|---------|-------------|
| `iwpriv athX get_qos` | Get current QoS flags |
| `iwpriv athX set_qos &lt;val&gt;` | Set QoS flags |
| `iwpriv athX get_wmm` | Get WMM status |
| `iwpriv athX getwmmparams` | Get WMM parameters |
| `cat /proc/net/athX/stats` | View interface statistics |
| `tcpdump -i athX -v` | Capture and analyze packets |

### Log Analysis

#### Key Log Messages

```
# Successful QoS configuration
[applyQosConfig] Set SetQos: 15 for ath0

# QoS written to ArDS
[writeQosConfigToArDS] Profile 1, qosConfig written to ArDS: {...}

# Error setting QoS
[applyQosConfig] Failed to set SetQos: 15 for ath0

# Driver QoS application
ar_cfg_vdev_qos: Setting QoS params 0x0F for vdev 0
```

#### Log Locations

| Log Type | Location |
|----------|----------|
| System logs | `/var/log/messages` |
| Kernel logs | `dmesg` |
| configVAP logs | `/var/log/configVAP.log` |
| configagent logs | `/var/log/configagent.log` |

---

## QosConfig Data Model

Defined in `SsidConfig.tac`:

```
QosConfig : Tac::Type() : Tac::Nominal {
   ssidPriority : U8;           // 0=Voice, 1=Video, 2=BE, 3=BK
   priorityType : U8;           // 0=Ceiling, 1=Fixed
   downstreamMap : U8;          // 0=802.1p, 1=DSCP, 2=TOS
   upstreamMark8021p : U8;      // Enable 802.1p marking
   upstreamMarkDscpTos : U8;    // Enable DSCP/TOS marking
   wmmEnforcePolicyEnable : bool;
   wmmEnable : bool;
   vapMinRate : double;
   vapMaxRate : double;
   vapNonLegacyMaxRate : U8;
   vapMcastMgmtRate : double;
   vapDisable11bRate : bool;
   vapMinRate2G/5G/6G : double; // Band-specific rates
   vapMaxRate2G/5G/6G : double;
   vapMcastMgmtRate2G/5G/6G : double;
}
```

### Field Validation Rules

| Field | Valid Range | Default | Notes |
|-------|-------------|---------|-------|
| `ssidPriority` | 0-3 | 0 | 0=Voice, 1=Video, 2=BE, 3=BK |
| `priorityType` | 0-1 | 0 | 0=Ceiling, 1=Fixed |
| `downstreamMap` | 0-2 | 1 | 0=802.1p, 1=DSCP, 2=TOS |
| `upstreamMark8021p` | 0-1 | 0 | Boolean |
| `upstreamMarkDscpTos` | 0-1 | 0 | Boolean |
| `wmmEnable` | bool | true | Should be true for QoS |
| `vapMinRate` | 0-54 | 0 | Mbps |
| `vapMaxRate` | 0-54 | 0 | Mbps, 0=unlimited |

---

## API Reference

### Go API (configagent)

#### applyQosConfig

```go
func applyQosConfig(
    profileID uint32,
    qosParams qosParamsQca,
    dual5GHzEnable bool,
    callback func(uint32, string, wificonfig.QosConfig,
                  map[string]radiomgrstate.ErrorDetails)
) error
```

**Parameters:**
- `profileID`: SSID profile identifier
- `qosParams`: QoS parameters structure
- `dual5GHzEnable`: Whether dual 5GHz mode is enabled
- `callback`: Callback function for completion notification

**Returns:**
- `error`: nil on success, error on failure

#### updateQosParams

```go
func updateQosParams(config wificonfig.QosConfig, profileConfMap *sync.Map)
```

**Parameters:**
- `config`: QoS configuration structure
- `profileConfMap`: Map to store configuration parameters

#### setQosFlagParam

```go
func setQosFlagParam(
    action string,
    vapName string,
    qosFlagParam uint,
    logPrefix string,
    errors map[string]radiomgrstate.ErrorDetails
)
```

**Parameters:**
- `action`: IOCTL action (e.g., `wlanioctl.SetQos`)
- `vapName`: VAP interface name (e.g., "ath0")
- `qosFlagParam`: Calculated QoS flag value
- `logPrefix`: Logging prefix
- `errors`: Error collection map

### Driver API (C)

#### ar_cfg_vdev_qos

```c
static AR_STATUS ar_cfg_vdev_qos(
    struct ar_dp_vdev_s* vdev,
    char* data
);
```

**Parameters:**
- `vdev`: Virtual device (VAP) handle
- `data`: Pointer to QoS parameters from userspace

**Returns:**
- `AR_STATUS_SUCCESS`: Configuration applied successfully
- `AR_STATUS_E_INVAL`: Invalid parameters

#### ar_qos_dp_rx_set_prio

```c
void ar_qos_dp_rx_set_prio(
    struct sk_buff* skb,
    struct ar_dp_vdev_s* vdev,
    uint8_t tid
);
```

**Parameters:**
- `skb`: Network buffer (socket buffer)
- `vdev`: Virtual device handle
- `tid`: Traffic Identifier (0-7)

#### ar_qos_dp_set_map_dstream_8021p

```c
void ar_qos_dp_set_map_dstream_8021p(
    struct sk_buff* skb,
    struct ar_dp_vdev_s* vdev,
    int* v_wme_ac,
    int* v_pri
);
```

**Parameters:**
- `skb`: Network buffer
- `vdev`: Virtual device handle
- `v_wme_ac`: Output WMM access category
- `v_pri`: Output priority/TID

#### ar_qos_dp_set_map_dstream_dscp

```c
AR_STATUS ar_qos_dp_set_map_dstream_dscp(
    struct sk_buff* skb,
    struct ar_dp_vdev_s* vdev,
    int* v_wme_ac,
    int* v_pri
);
```

**Parameters:**
- `skb`: Network buffer
- `vdev`: Virtual device handle
- `v_wme_ac`: Output WMM access category
- `v_pri`: Output priority/TID

**Returns:**
- `AR_STATUS_SUCCESS`: Mapping successful
- `AR_STATUS_EARLY_RETURN`: Non-IP packet or error

#### ar_qos_dp_set_map_dstream_tos

```c
AR_STATUS ar_qos_dp_set_map_dstream_tos(
    struct sk_buff* skb,
    struct ar_dp_vdev_s* vdev,
    int* v_wme_ac,
    int* v_pri
);
```

**Parameters:**
- `skb`: Network buffer
- `vdev`: Virtual device handle
- `v_wme_ac`: Output WMM access category
- `v_pri`: Output priority/TID

**Returns:**
- `AR_STATUS_SUCCESS`: Mapping successful
- `AR_STATUS_EARLY_RETURN`: Non-IP packet or error

### Macros Reference

#### Priority Macros

```c
// Get QoS priority from vdev
#define AR_GET_QOS_PRIO(_vap) (((_vap)->qos).prio)

// Check if priority type is Fixed
#define AR_IS_QOS_PRIO_FIXED(_vap) \
    ((((_vap)->qos).prio_type) == AR_QOS_PRIO_FIXED)

// Set priority type to Fixed
#define AR_SET_QOS_PRIO_TYPE_FIXED(_vap) \
    ((((_vap)->qos).prio_type) = AR_QOS_PRIO_FIXED)

// Set priority type to Ceiling
#define AR_SET_QOS_PRIO_TYPE_CEIL(_vap) \
    ((((_vap)->qos).prio_type) = AR_QOS_PRIO_CEIL)

// Set QoS priority
#define AR_SET_QOS_PRIO(_vap, _prio) \
    ((((_vap)->qos).prio) = (_prio))
```

#### Downstream Macros

```c
// Check downstream mapping type
#define AR_IS_QOS_DSTREAM_8021P(_vap) \
    ((((_vap)->qos).dstream) == AR_QOS_DSTREAM_8021P)
#define AR_IS_QOS_DSTREAM_DSCP(_vap) \
    ((((_vap)->qos).dstream) == AR_QOS_DSTREAM_DSCP)
#define AR_IS_QOS_DSTREAM_TOS(_vap) \
    ((((_vap)->qos).dstream) == AR_QOS_DSTREAM_TOS)

// Set downstream mapping
#define AR_SET_QOS_DSTREAM(_vap, _dstream) \
    ((((_vap)->qos).dstream) = (_dstream))
```

#### Upstream Macros

```c
// Check upstream marking
#define AR_IS_QOS_USTREAM_DSCP(_vap) (((_vap)->qos).ustream_dscp)
#define AR_IS_QOS_USTREAM_TOS(_vap) (((_vap)->qos).ustream_tos)
#define AR_IS_QOS_USTREAM_8021P(_vap) (((_vap)->qos).ustream_8021p)

// Set upstream marking
#define AR_SET_QOS_USTREAM_DSCP(_vap, _val) \
    ((((_vap)->qos).ustream_dscp) = (_val))
#define AR_SET_QOS_USTREAM_TOS(_vap, _val) \
    ((((_vap)->qos).ustream_tos) = (_val))
#define AR_SET_QOS_USTREAM_8021P(_vap, _val) \
    ((((_vap)->qos).ustream_8021p) = (_val))
```

#### Ceiling Macros

```c
// Convert AC for ceiling comparison
// Required because BG has higher value than BE but lower priority
#define CONVERT_AC(_ac) (((_ac)&0x2) ? (_ac) : ((_ac) ^ 0x1))

// Ceiling macro for AC/priority
#define AR_CEIL_QOS_PRIO(_vap, _ac, _prio)                   \
    if (CONVERT_AC(_ac) > CONVERT_AC(AR_GET_QOS_PRIO(_vap))) { \
        (_ac) = AR_GET_QOS_PRIO(_vap);                           \
        (_prio) = WME_AC_TO_TID(_ac);                            \
    }

// Ceiling macro for TID
#define AR_CEIL_QOS_TID(_vap, _tid)                                          \
    if (CONVERT_AC(TID_TO_WME_AC(_tid)) > CONVERT_AC(AR_GET_QOS_PRIO(_vap))) { \
        (_tid) = WME_AC_TO_TID(AR_GET_QOS_PRIO(_vap));                           \
    }
```

#### TID/AC Conversion Macros

```c
// WMM Access Categories
#define WME_AC_BE 0  // Best Effort
#define WME_AC_BK 1  // Background
#define WME_AC_VI 2  // Video
#define WME_AC_VO 3  // Voice

// Convert AC to TID
#define WME_AC_TO_TID(_ac) (       \
    ((_ac) == WME_AC_VO) ? 6 : \
    ((_ac) == WME_AC_VI) ? 5 : \
    ((_ac) == WME_AC_BK) ? 1 : \
    0)

// Convert TID to AC
#define TID_TO_WME_AC(_tid) (      \
    (((_tid) == 0) || ((_tid) == 3)) ? WME_AC_BE : \
    (((_tid) == 1) || ((_tid) == 2)) ? WME_AC_BK : \
    (((_tid) == 4) || ((_tid) == 5)) ? WME_AC_VI : \
    WME_AC_VO)
```

---

## Best Practices

### Configuration Best Practices

1. **Use Ceiling Mode for Most SSIDs**
   - Ceiling mode allows traffic to use its natural priority up to a limit
   - Fixed mode should only be used for strict priority enforcement

2. **Match Downstream Mapping to Traffic Type**
   - Use DSCP for enterprise networks with proper DSCP marking
   - Use 802.1p for networks with VLAN-based QoS
   - Use TOS only for legacy compatibility

3. **Enable WMM**
   - Always enable WMM for QoS to function properly
   - WMM is required for 802.11n/ac/ax operation

4. **Configure Appropriate SSID Priority**
   - Voice SSIDs: Priority 0 (Voice)
   - Video SSIDs: Priority 1 (Video)
   - Data SSIDs: Priority 2 (Best Effort)
   - Guest SSIDs: Priority 3 (Background)

5. **Use Band-Specific Rates When Needed**
   - 2.4GHz may need lower minimum rates for compatibility
   - 5GHz/6GHz can use higher minimum rates

### Deployment Best Practices

1. **Test QoS Configuration**
   - Verify with traffic generators before production
   - Use packet captures to confirm priority marking

2. **Monitor QoS Performance**
   - Track per-AC statistics
   - Monitor queue depths and drops

3. **Document Configuration**
   - Keep records of QoS settings per SSID
   - Document any custom mappings

4. **Coordinate with Network Infrastructure**
   - Ensure switches and routers honor QoS markings
   - Configure end-to-end QoS policy

### Security Considerations

1. **Prevent QoS Abuse**
   - Use Ceiling mode to prevent clients from claiming high priority
   - Consider Fixed mode for untrusted networks

2. **Guest Network Isolation**
   - Limit guest SSIDs to Background priority
   - Prevent guests from affecting enterprise traffic

---

## Performance Considerations

### Impact of QoS Processing

QoS processing adds minimal overhead to packet handling:

| Operation | Typical Latency |
|-----------|-----------------|
| Priority lookup | < 1 μs |
| DSCP extraction | < 1 μs |
| Ceiling check | < 1 μs |
| TID assignment | < 1 μs |

### Optimization Tips

1. **Use Fixed Mode for Simple Deployments**
   - Fixed mode skips downstream mapping lookup
   - Reduces per-packet processing

2. **Minimize DSCP Exceptions**
   - Each exception requires a linear search
   - Keep exception list short

3. **Disable Unused Upstream Marking**
   - Don't enable marking if not needed
   - Reduces packet modification overhead

### Queue Management

WMM uses four hardware queues with different parameters:

| Queue | AIFSN | CWmin | CWmax | TXOP |
|-------|-------|-------|-------|------|
| AC_BK | 7 | 15 | 1023 | 0 |
| AC_BE | 3 | 15 | 1023 | 0 |
| AC_VI | 2 | 7 | 15 | 3.008ms |
| AC_VO | 2 | 3 | 7 | 1.504ms |

---

## Appendix

### Appendix A: Complete QoS Flag Encoding Table

| Bits | Field | Value 0 | Value 1 | Value 2 | Value 3 |
|------|-------|---------|---------|---------|---------|
| 0-1 | Priority | BE | BK | VI | VO |
| 2 | Type | Ceiling | Fixed | - | - |
| 3-4 | DStream | 802.1p | DSCP | TOS | Reserved |
| 5 | 802.1p Mark | Disabled | Enabled | - | - |
| 6 | DSCP Mark | Disabled | Enabled | - | - |
| 7 | TOS Mark | Disabled | Enabled | - | - |

### Appendix B: SSID Priority to Internal Encoding

| SSID Priority | WMM AC | Internal Value | Binary |
|---------------|--------|----------------|--------|
| 0 (Voice) | VO (3) | 3 | 11 |
| 1 (Video) | VI (2) | 2 | 10 |
| 2 (Best Effort) | BE (0) | 0 | 00 |
| 3 (Background) | BK (1) | 1 | 01 |

### Appendix C: Complete qosFlagParam Calculation Examples

#### Example: Voice + Fixed + DSCP + All Marking
```
SSID Priority: 0 (Voice) -> Internal: 3
Priority Type: 1 (Fixed) -> 4 * 1 = 4
Downstream Map: 1 (DSCP) -> 8 * 1 = 8
802.1p Marking: 1 -> 32 * 1 = 32
DSCP Marking: 1 -> 64 * 1 = 64
TOS Marking: 1 -> 128 * 1 = 128

Total: 3 + 4 + 8 + 32 + 64 + 128 = 239 (0xEF)

Binary: 1110 1111
        |||| ||||
        |||| ||++-- Priority: 11 (VO)
        |||| |+---- Type: 1 (Fixed)
        |||+-+----- DStream: 01 (DSCP)
        ||+-------- 802.1p: 1 (Enabled)
        |+--------- DSCP: 1 (Enabled)
        +---------- TOS: 1 (Enabled)
```

#### Example: Background + Ceiling + 802.1p + No Marking
```
SSID Priority: 3 (Background) -> Internal: 1
Priority Type: 0 (Ceiling) -> 4 * 0 = 0
Downstream Map: 0 (802.1p) -> 8 * 0 = 0
802.1p Marking: 0 -> 32 * 0 = 0
DSCP Marking: 0 -> 64 * 0 = 0

Total: 1 + 0 + 0 + 0 + 0 = 1 (0x01)

Binary: 0000 0001
        |||| ||||
        |||| ||++-- Priority: 01 (BK)
        |||| |+---- Type: 0 (Ceiling)
        |||+-+----- DStream: 00 (802.1p)
        ||+-------- 802.1p: 0 (Disabled)
        |+--------- DSCP: 0 (Disabled)
        +---------- TOS: 0 (Disabled)
```

### Appendix D: File Locations Summary

| Component | File Path |
|-----------|-----------|
| Data Model | `ap/s4models/wificonfig/SsidConfig.tac` |
| ArDS Writer | `ap/src/go/arista-ap/ardsconfwriter/ssid_qos.go` |
| Config Agent | `ap/src/go/arista-ap/configagent/ssid_qos_qca.go` |
| Config Agent (Sim) | `ap/src/go/arista-ap/configagent/ssid_features_sim.go` |
| Shell Script | `ap/rootfs/scripts/configVAP` |
| Driver Header | `ap/src/wlan-drivers/ar/core/src/ar_qos.h` |
| Driver Implementation | `ap/src/wlan-drivers/ar/core/src/ar_qos.c` |
| Driver Config | `ap/src/wlan-drivers/ar/core/src/ar_cfg.c` |
| Driver Types | `ap/src/wlan-drivers/ar/core/src/ar_types.h` |
| IEEE80211 Defs | `ap/src/wlan-drivers/ar/core/src/ieee80211_extn.h` |
| VLAN Utils | `ap/src/go/arista-ap/configagent/vlan/vlan_utils.go` |
| OC Agent | `ap/src/go/arista-ap/ocagent/setconfig.go` |

### Appendix E: Related Configuration Parameters

| Parameter | Description | Related to QoS |
|-----------|-------------|----------------|
| `WMM_ENABLE` | Enable WMM | Required for QoS |
| `WMM_ENFORCE_POLICY_ENABLE` | Enforce WMM policy | Policy enforcement |
| `VAP_MIN_RATE` | Minimum data rate | Rate limiting |
| `VAP_MAX_RATE` | Maximum data rate | Rate limiting |
| `VAP_MCAST_MGMT_RATE` | Multicast rate | Multicast QoS |
| `VAP_DISABLE_11B_RATES` | Disable 11b rates | Legacy compatibility |
| `DTIM_PERIOD` | DTIM period | Power save |

### Appendix F: Error Codes

| Error | Description | Resolution |
|-------|-------------|------------|
| `set_qos failed` | IOCTL failed | Check driver state |
| `Invalid QoS params` | Bad parameter value | Verify configuration |
| `VAP not found` | Interface doesn't exist | Check interface name |
| `Permission denied` | Insufficient privileges | Run as root |

### Appendix G: Glossary

| Term | Definition |
|------|------------|
| **AC** | Access Category - WMM traffic classification |
| **AIFSN** | Arbitration Inter-Frame Space Number |
| **CW** | Contention Window |
| **DSCP** | Differentiated Services Code Point |
| **ECN** | Explicit Congestion Notification |
| **QoS** | Quality of Service |
| **TID** | Traffic Identifier |
| **TOS** | Type of Service |
| **TXOP** | Transmission Opportunity |
| **UP** | User Priority |
| **VAP** | Virtual Access Point |
| **VLAN** | Virtual Local Area Network |
| **WME** | Wireless Multimedia Extensions |
| **WMM** | Wi-Fi Multimedia |

### Appendix H: References

1. IEEE 802.11e-2005 - QoS Enhancements
2. IEEE 802.11-2016 - Wireless LAN Medium Access Control
3. RFC 2474 - Definition of the Differentiated Services Field
4. RFC 2597 - Assured Forwarding PHB Group
5. RFC 3246 - An Expedited Forwarding PHB
6. Wi-Fi Alliance WMM Specification

---

## Revision History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2026-01-27 | Auto-generated | Initial documentation |

---

## Contact

For questions or issues related to QoS configuration, contact the wireless team.

