# QoS Downstream Traffic Management - AP Configuration Guide

## Overview

This document describes how Quality of Service (QoS) values are managed for downstream traffic (traffic from the wired network to wireless clients) and the role of Access Point (AP) configuration in traffic prioritization.

## QoS Flags Bit Structure

The QoS configuration is encoded in an 8-bit flag parameter that is applied to each Virtual Access Point (VAP):

```
Bit 7 -------------------- Bit 0
  7     6     5     4-3     2     1-0
  |     |     |      |      |      |
  TOS   DSCP  8021p  Dstrm  Type  Priority
  Mark  Mark  Mark   Map    
```

| Bits  | Field                  | Description                                      |
|-------|------------------------|--------------------------------------------------|
| 0-1   | QoS Priority           | SSID Priority level (Voice=0, Video=1, BE=2, BG=3) |
| 2     | QoS Priority Type      | 0=Ceiling, 1=Fixed                              |
| 3-4   | Downstream Mapping     | 0=802.1p, 1=DSCP, 2=TOS                         |
| 5     | Upstream 802.1p Mark   | Enable 802.1p marking on upstream traffic       |
| 6     | Upstream DSCP Mark     | Enable DSCP marking on upstream traffic         |
| 7     | Upstream TOS Mark      | Enable TOS marking on upstream traffic          |

## Downstream Mapping Types

### 1. DSCP Mapping (QOS_DOWNSTR_MAP=1)

DSCP (Differentiated Services Code Point) is extracted from the IP header TOS field. The 6-bit DSCP value determines the traffic priority:

| DSCP Value | Per-Hop Behavior | WMM Access Category |
|------------|------------------|---------------------|
| 46 (EF)    | Expedited Forwarding | Voice (AC_VO)  |
| 34 (AF41)  | Assured Forwarding   | Video (AC_VI)  |
| 0 (BE)     | Best Effort          | Best Effort (AC_BE) |

**Processing Logic** (`ar_qos_dp_set_map_dstream_dscp()`):
- Extract DSCP from IPv4/IPv6 header
- Special case: DSCP=46 maps directly to Voice queue (TID=6)
- Other values: Right-shift by 5 to get TID, then map to WMM AC

### 2. TOS Mapping (QOS_DOWNSTR_MAP=2)

TOS (Type of Service) uses the full 8-bit TOS field priority for traffic classification:

**Processing Logic** (`ar_qos_dp_set_map_dstream_tos()`):
- Extract priority from IPv4/IPv6 header
- Right-shift by 5 (IP_PRI_SHIFT) to convert to TID
- Map TID to WMM Access Category

### 3. 802.1p Mapping (QOS_DOWNSTR_MAP=0)

Uses VLAN priority from the 802.1Q tag for classification:

| 802.1p Priority | WMM TID | WMM Access Category |
|-----------------|---------|---------------------|
| 0 (Background)  | 1       | Background (AC_BK)  |
| 1 (Best Effort) | 0       | Best Effort (AC_BE) |
| 2 (Excellent)   | 3       | Best Effort (AC_BE) |
| 3 (Critical)    | 4       | Video (AC_VI)       |
| 4 (Video)       | 5       | Video (AC_VI)       |
| 5 (Voice)       | 6       | Voice (AC_VO)       |
| 6-7 (Control)   | 7       | Voice (AC_VO)       |

## Priority Type Behavior

### Ceiling Mode (QOS_PRIORITY_TYPE=0)

When Priority Type is set to Ceiling:
- Downstream mapping (DSCP/TOS/802.1p) is **active**
- Traffic priority is determined by the packet's marking
- Priority is **capped** at the configured SSID Priority level
- Higher priority traffic is downgraded to the ceiling value

```c
#define AR_CEIL_QOS_PRIO(_vap, _ac, _prio)
  if (CONVERT_AC(_ac) > CONVERT_AC(AR_GET_QOS_PRIO(_vap))) {
    (_ac) = AR_GET_QOS_PRIO(_vap);
    (_prio) = WME_AC_TO_TID(_ac);
  }
```

### Fixed Mode (QOS_PRIORITY_TYPE=1)

When Priority Type is set to Fixed:
- Downstream mapping is **disabled** (ignored)
- All traffic receives the same fixed priority
- All packets use the configured SSID Priority regardless of DSCP/TOS values

```c
if (AR_IS_QOS_PRIO_FIXED(vdev)) {
  effective_tid = WME_AC_TO_TID(AR_GET_QOS_PRIO(vdev));
  ar_os_skb_set_priority(skb, effective_tid);
}
```

## WMM Access Categories

| Access Category | Value | Traffic Type | TID Range |
|-----------------|-------|--------------|-----------|
| AC_VO (Voice)   | 3     | Real-time voice | 6, 7    |
| AC_VI (Video)   | 2     | Streaming video | 4, 5    |
| AC_BE (Best Effort) | 0 | Normal traffic | 0, 3    |
| AC_BK (Background)  | 1 | Bulk transfers | 1, 2    |

## AP Configuration Parameters

These parameters are configured per-SSID in the AP configuration:

| Parameter             | Config Key              | Values               |
|-----------------------|-------------------------|----------------------|
| SSID Priority         | `QOS_SSID_PRIORITY`    | 0=Voice, 1=Video, 2=BE, 3=BG |
| Priority Type         | `QOS_PRIORITY_TYPE`    | 0=Ceiling, 1=Fixed   |
| Downstream Mapping    | `QOS_DOWNSTR_MAP`      | 0=802.1p, 1=DSCP, 2=TOS |
| Upstream 802.1p Mark  | `QOS_UPSTR_MARK_802_1p`| 0=Disabled, 1=Enabled |
| Upstream DSCP/TOS Mark| `QOS_UPSTR_MARK_DSCP_TOS`| 0=Disabled, 1=Enabled |

## Traffic Flow Decision Tree

```
Incoming Downstream Packet
         |
         v
   Is Priority Fixed?
        / \
      Yes  No
       |    |
       v    v
  Use SSID   Check Downstream
  Priority   Mapping Type
       |         |
       v    +----+----+----+
  Fixed     |    |    |
  Queue   802.1p DSCP TOS
            |    |    |
            v    v    v
      Extract priority from header
            |
            v
      Map to WMM TID
            |
            v
      Is TID > Ceiling?
           / \
         Yes  No
          |    |
          v    v
     Cap at   Use
     Ceiling  TID
          \   /
           \ /
            v
    Assign to WMM Queue
```

## Driver Implementation

The QoS downstream traffic handling is implemented in `ap/src/wlan-drivers/ar/core/src/ar_qos.c`:

- `ar_qos_dp_set_map_dstream_dscp()` - DSCP-based classification
- `ar_qos_dp_set_map_dstream_tos()` - TOS-based classification  
- `ar_qos_dp_set_map_dstream_8021p()` - 802.1p VLAN priority classification
- `ar_qos_dp_set_map_pri_fixed()` - Fixed priority assignment

## Configuration Application

QoS configuration is applied via:

1. **Config Agent** (`ssid_qos_qca.go`): Calculates QoS flag parameter and calls `iwpriv set_qos`
2. **Shell Script** (`configVAP`): Sets QoS params using `iwpriv $APNAME set_qos $QOS_PARAMS`
3. **Driver**: Parses flags and configures VAP QoS behavior

