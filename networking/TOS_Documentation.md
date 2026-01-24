# Comprehensive TOS (Type of Service) Documentation

## Arista WiFi Access Point Implementation

**Version:** 1.0
**Date:** 2024
**Classification:** Technical Reference Documentation
**Copyright:** © 2024 Arista Networks, Inc. All rights reserved.

---

# Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [Introduction to TOS](#2-introduction-to-tos)
3. [TOS Field Structure](#3-tos-field-structure)
4. [TOS vs DSCP: Key Differences](#4-tos-vs-dscp-key-differences)
5. [IP Precedence (Legacy TOS)](#5-ip-precedence-legacy-tos)
6. [TOS Byte Layout](#6-tos-byte-layout)
7. [TOS in IPv4 Header](#7-tos-in-ipv4-header)
8. [TOS in IPv6 (Traffic Class)](#8-tos-in-ipv6-traffic-class)
9. [TOS to TID Mapping](#9-tos-to-tid-mapping)
10. [TOS Downstream Mapping](#10-tos-downstream-mapping)
11. [TOS Upstream Marking](#11-tos-upstream-marking)
12. [TOS Configuration in Arista AP](#12-tos-configuration-in-arista-ap)
13. [Driver-Level TOS Implementation](#13-driver-level-tos-implementation)
14. [TOS Processing Flow](#14-tos-processing-flow)
15. [ECN (Explicit Congestion Notification)](#15-ecn-explicit-congestion-notification)
16. [Testing TOS Functionality](#16-testing-tos-functionality)
17. [TOS Reference Tables](#17-tos-reference-tables)
18. [RFC Standards Reference](#18-rfc-standards-reference)
19. [Troubleshooting Guide](#19-troubleshooting-guide)
20. [Appendix](#20-appendix)

---

# 1. Executive Summary

## 1.1 Document Purpose

This document provides comprehensive documentation of the Type of Service (TOS) field implementation in Arista WiFi Access Points. It covers the TOS byte structure, its relationship with DSCP, and how TOS values are used for traffic prioritization in WiFi networks.

## 1.2 Key Concepts

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         TOS (Type of Service) Overview                       │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  The TOS field is an 8-bit field in the IPv4 header that was originally    │
│  defined in RFC 791 for specifying quality of service parameters.           │
│                                                                              │
│  Modern Usage:                                                               │
│  • The TOS byte has been redefined by RFC 2474 as the DS (DiffServ) field  │
│  • Upper 6 bits: DSCP (Differentiated Services Code Point)                 │
│  • Lower 2 bits: ECN (Explicit Congestion Notification)                    │
│                                                                              │
│  Legacy TOS Interpretation:                                                  │
│  • Bits 7-5: IP Precedence (0-7)                                           │
│  • Bits 4-1: TOS subfield (D, T, R, C flags)                               │
│  • Bit 0: Reserved (MBZ - Must Be Zero)                                    │
│                                                                              │
│  In Arista APs:                                                              │
│  • TOS downstream mapping uses IP Precedence (bits 7-5)                     │
│  • DSCP downstream mapping uses bits 7-2 (6-bit DSCP value)                │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

## 1.3 TOS vs DSCP Quick Reference

| Aspect | TOS (Legacy) | DSCP (Modern) |
|--------|--------------|---------------|
| Bits Used | Bits 7-5 (3 bits) | Bits 7-2 (6 bits) |
| Values | 8 (0-7) | 64 (0-63) |
| Name | IP Precedence | DSCP Codepoint |
| Shift Operation | `>> 5` | `>> 2` |
| Priority Levels | 8 levels | 64 codepoints |
| RFC | RFC 791 | RFC 2474 |

---

# 2. Introduction to TOS

## 2.1 Historical Background

The Type of Service (TOS) field was introduced in RFC 791 (1981) as part of the original IPv4 specification. It was designed to allow applications to specify the desired quality of service characteristics for IP datagrams.

## 2.2 Evolution of TOS

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           TOS Field Evolution                                │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  1981 (RFC 791) - Original TOS Definition:                                  │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │ Precedence │ D │ T │ R │ C │ MBZ │                                    │  │
│  │   (3 bits) │   │   │   │   │     │                                    │  │
│  │    7-5     │ 4 │ 3 │ 2 │ 1 │  0  │                                    │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                                                                              │
│  1998 (RFC 2474) - DiffServ Redefinition:                                   │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │           DSCP (6 bits)           │      ECN (2 bits)                 │  │
│  │           Bits 7-2                │      Bits 1-0                     │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                                                                              │
│  Key Changes:                                                                │
│  • D, T, R, C flags were deprecated                                         │
│  • 6-bit DSCP replaced the precedence + flags                               │
│  • ECN added for congestion notification                                    │
│  • Class Selectors maintain backward compatibility with IP Precedence      │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

## 2.3 TOS in Modern Networks

While DSCP has largely replaced TOS for traffic classification, the TOS-based mapping remains relevant for:

1. **Legacy Compatibility**: Supporting older network equipment
2. **Simplified Classification**: Using only 8 priority levels instead of 64
3. **Backward Compatibility**: Class Selectors (CS0-CS7) map directly to IP Precedence
4. **WiFi Integration**: Mapping IP precedence to 802.11 TID values

---

# 3. TOS Field Structure

## 3.1 Original TOS Byte Layout (RFC 791)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    Original TOS Byte Structure (RFC 791)                     │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  Bit Position:                                                               │
│  ┌─────┬─────┬─────┬─────┬─────┬─────┬─────┬─────┐                          │
│  │  7  │  6  │  5  │  4  │  3  │  2  │  1  │  0  │                          │
│  ├─────┴─────┴─────┼─────┼─────┼─────┼─────┼─────┤                          │
│  │   Precedence    │  D  │  T  │  R  │  C  │ MBZ │                          │
│  │    (3 bits)     │     │     │     │     │     │                          │
│  └─────────────────┴─────┴─────┴─────┴─────┴─────┘                          │
│                                                                              │
│  Field Definitions:                                                          │
│  ─────────────────────────────────────────────────────────────────────────  │
│  Precedence (Bits 7-5): IP Precedence value (0-7)                           │
│      - 7 = Network Control (highest)                                        │


## 3.2 Modern DS Field Layout (RFC 2474)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    Modern DS Field Structure (RFC 2474)                      │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  Bit Position:                                                               │
│  ┌─────┬─────┬─────┬─────┬─────┬─────┬─────┬─────┐                          │
│  │  7  │  6  │  5  │  4  │  3  │  2  │  1  │  0  │                          │
│  ├─────┴─────┴─────┴─────┴─────┴─────┼─────┴─────┤                          │
│  │          DSCP (6 bits)            │ECN(2 bits)│                          │
│  │          Bits 7-2                 │ Bits 1-0  │                          │
│  └───────────────────────────────────┴───────────┘                          │
│                                                                              │
│  DSCP Values:                                                                │
│  • Range: 0-63 (64 possible values)                                         │
│  • Extraction: dscp = (tos >> 2) & 0x3F                                     │
│                                                                              │
│  ECN Values:                                                                 │
│  • 00 = Not-ECT (Not ECN-Capable Transport)                                 │
│  • 01 = ECT(1) - ECN-Capable Transport                                      │
│  • 10 = ECT(0) - ECN-Capable Transport                                      │
│  • 11 = CE (Congestion Experienced)                                         │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

## 3.3 TOS Byte Representation

```c
// TOS byte structure
struct tos_byte {
    uint8_t ecn       : 2;    // Bits 0-1: ECN (Explicit Congestion Notification)
    uint8_t dscp      : 6;    // Bits 2-7: DSCP (Differentiated Services Code Point)
};

// Alternative view - Legacy TOS
struct legacy_tos_byte {
    uint8_t mbz       : 1;    // Bit 0: Must Be Zero
    uint8_t cost      : 1;    // Bit 1: Minimize Cost
    uint8_t reliable  : 1;    // Bit 2: High Reliability
    uint8_t throughput: 1;    // Bit 3: High Throughput
    uint8_t delay     : 1;    // Bit 4: Low Delay
    uint8_t precedence: 3;    // Bits 5-7: IP Precedence
};

// Extraction macros
#define GET_IP_PRECEDENCE(tos)  ((tos) >> 5)           // Extract bits 7-5
#define GET_DSCP(tos)           (((tos) >> 2) & 0x3F)  // Extract bits 7-2
#define GET_ECN(tos)            ((tos) & 0x03)          // Extract bits 1-0
```

---

# 4. TOS vs DSCP: Key Differences

## 4.1 Comparison Table

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        TOS vs DSCP Comparison                                │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  Feature          │ TOS (IP Precedence)     │ DSCP                          │
│  ─────────────────┼─────────────────────────┼──────────────────────────────  │
│  RFC              │ RFC 791 (1981)          │ RFC 2474 (1998)                │
│  Bits Used        │ Bits 7-5 (3 bits)       │ Bits 7-2 (6 bits)              │
│  Values           │ 8 (0-7)                 │ 64 (0-63)                      │
│  Extraction       │ tos >> 5                │ (tos >> 2) & 0x3F              │
│  Priority Levels  │ 8 levels                │ 64 codepoints                  │
│  WiFi TID Mapping │ Direct (0-7 → TID 0-7)  │ Table lookup (64 → 8)          │
│  Granularity      │ Coarse (8 levels)       │ Fine (64 codepoints)           │
│  Use Case         │ Legacy equipment        │ Modern QoS policies            │
│                                                                              │
│  Shift Operations:                                                           │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │  TOS:  pri = (ip->tos >> IP_PRI_SHIFT)   where IP_PRI_SHIFT = 5      │  │
│  │  DSCP: dscp = (ip->tos >> 2) & 0x3F                                   │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                                                                              │
│  Example - TOS Byte Value 0xB8 (DSCP EF = 46):                             │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │  Binary: 1011 1000                                                    │  │
│  │  TOS (>> 5): 101 = 5 (IP Precedence 5)                               │  │
│  │  DSCP (>> 2): 101110 = 46 (Expedited Forwarding)                     │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

## 4.2 Mapping Granularity

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    TOS vs DSCP Granularity Comparison                        │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  IP Precedence (TOS bits 7-5):                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │  0 │ 1 │ 2 │ 3 │ 4 │ 5 │ 6 │ 7 │                                   │    │
│  │ BE │BK │   │   │ VI│ VI│ VO│ VO│                                   │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  DSCP Values (64 codepoints):                                                │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │  0-7   │ 8-15  │ 16-23 │ 24-31 │ 32-39 │ 40-47 │ 48-55 │ 56-63    │    │
│  │  BE    │  BK   │  BK   │  BE   │  VI   │  VI   │  VO   │  VO      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  Key Insight:                                                                │
│  • TOS provides coarse 8-level classification                               │
│  • DSCP provides fine-grained 64-level classification                       │
│  • Both ultimately map to 4 WMM Access Categories (or 8 TIDs)              │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

# 5. IP Precedence (Legacy TOS)

## 5.1 IP Precedence Values

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        IP Precedence Values (RFC 791)                        │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  Value │ Binary │ Name                    │ Description                     │
│  ──────┼────────┼─────────────────────────┼──────────────────────────────── │
│    7   │  111   │ Network Control         │ Reserved for network control    │
│    6   │  110   │ Internetwork Control    │ Inter-network control traffic   │
│    5   │  101   │ CRITIC/ECP              │ Critical traffic                │
│    4   │  100   │ Flash Override          │ Flash override priority         │
│    3   │  011   │ Flash                   │ Flash priority                  │
│    2   │  010   │ Immediate               │ Immediate priority              │
│    1   │  001   │ Priority                │ Priority traffic                │
│    0   │  000   │ Routine                 │ Normal/Default traffic          │
│                                                                              │
│  Memory Aid:                                                                 │
│  "Network Never Stops; Flash Folks Find Fast Internet, Routine Really      │
│   Runs Slow"                                                                 │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

## 5.2 IP Precedence to TOS Byte Mapping

| IP Precedence | Binary | TOS Byte (Hex) | TOS Byte (Binary) |
|---------------|--------|----------------|-------------------|
| 0 (Routine) | 000 | 0x00 | 0000 0000 |
| 1 (Priority) | 001 | 0x20 | 0010 0000 |
| 2 (Immediate) | 010 | 0x40 | 0100 0000 |
| 3 (Flash) | 011 | 0x60 | 0110 0000 |
| 4 (Flash Override) | 100 | 0x80 | 1000 0000 |
| 5 (CRITIC/ECP) | 101 | 0xA0 | 1010 0000 |
| 6 (Internetwork) | 110 | 0xC0 | 1100 0000 |
| 7 (Network Control) | 111 | 0xE0 | 1110 0000 |

---

# 6. TOS Byte Layout

## 6.1 Complete TOS Byte Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         Complete TOS Byte Layout                             │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  TOS Byte: 8 bits total                                                      │
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────────┐│
│  │  Bit 7 │ Bit 6 │ Bit 5 │ Bit 4 │ Bit 3 │ Bit 2 │ Bit 1 │ Bit 0        ││
│  ├────────┴───────┴───────┴───────┴───────┴───────┼───────┴───────────────┤│
│  │               DSCP (6 bits)                    │    ECN (2 bits)       ││
│  └────────────────────────────────────────────────┴───────────────────────┘│
│                                                                              │
│  Alternative Views:                                                          │
│                                                                              │
│  Legacy TOS View (RFC 791):                                                  │
│  ┌────────┬───────┬───────┬───────┬───────┬───────┬───────┬───────────────┐│
│  │ Prec-2 │Prec-1 │Prec-0 │   D   │   T   │   R   │   C   │     MBZ       ││
│  │  (MSB) │       │(LSB)  │ Delay │Throgh │ Rely  │ Cost  │   Reserved    ││
│  └────────┴───────┴───────┴───────┴───────┴───────┴───────┴───────────────┘│
│                                                                              │
│  IP Precedence View (Bits 7-5):                                             │
│  ┌────────────────────────┬───────────────────────────────────────────────┐│
│  │   IP Precedence (3)    │                Ignored (5)                    ││
│  └────────────────────────┴───────────────────────────────────────────────┘│
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

## 6.2 TOS Byte Examples

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         TOS Byte Value Examples                              │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  Example 1: Best Effort Traffic (TOS = 0x00)                                │
│  ┌────────────────────────────────────────────────────────────────────────┐ │
│  │  Binary:    0 0 0 0 0 0 0 0                                            │ │
│  │  IP Prec:   0 0 0 = 0 (Routine)                                        │ │
│  │  DSCP:      0 0 0 0 0 0 = 0 (CS0/BE)                                   │ │
│  │  ECN:       0 0 = Not-ECT                                              │ │
│  └────────────────────────────────────────────────────────────────────────┘ │
│                                                                              │
│  Example 2: Voice Traffic (TOS = 0xB8, DSCP EF)                             │
│  ┌────────────────────────────────────────────────────────────────────────┐ │
│  │  Binary:    1 0 1 1 1 0 0 0                                            │ │
│  │  IP Prec:   1 0 1 = 5 (CRITIC/ECP)                                     │ │
│  │  DSCP:      1 0 1 1 1 0 = 46 (EF - Expedited Forwarding)               │ │
│  │  ECN:       0 0 = Not-ECT                                              │ │
│  └────────────────────────────────────────────────────────────────────────┘ │
│                                                                              │
│  Example 3: Network Control (TOS = 0xC0, CS6)                               │
│  ┌────────────────────────────────────────────────────────────────────────┐ │
│  │  Binary:    1 1 0 0 0 0 0 0                                            │ │
│  │  IP Prec:   1 1 0 = 6 (Internetwork Control)                           │ │
│  │  DSCP:      1 1 0 0 0 0 = 48 (CS6)                                     │ │
│  │  ECN:       0 0 = Not-ECT                                              │ │
│  └────────────────────────────────────────────────────────────────────────┘ │
│                                                                              │
│  Example 4: Video Traffic (TOS = 0x88, DSCP AF41)                           │
│  ┌────────────────────────────────────────────────────────────────────────┐ │
│  │  Binary:    1 0 0 0 1 0 0 0                                            │ │
│  │  IP Prec:   1 0 0 = 4 (Flash Override)                                 │ │
│  │  DSCP:      1 0 0 0 1 0 = 34 (AF41)                                    │ │
│  │  ECN:       0 0 = Not-ECT                                              │ │
│  └────────────────────────────────────────────────────────────────────────┘ │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

# 7. TOS in IPv4 Header

## 7.1 IPv4 Header Structure

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         IPv4 Header Structure                                │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  Offset  0       4       8      12      16      20      24      28      31  │
│  ┌───────┬───────┬───────────────┬───────────────────────────────────────┐  │
│  │Version│  IHL  │   TOS Byte    │          Total Length                 │  │
│  │  (4)  │  (4)  │     (8)       │            (16)                       │  │
│  ├───────┴───────┼───────────────┼───────┬───────────────────────────────┤  │
│  │ Identification│     Flags     │        Fragment Offset                │  │
│  │     (16)      │      (3)      │            (13)                       │  │
│  ├───────────────┼───────────────┼───────────────────────────────────────┤  │
│  │     TTL       │   Protocol    │        Header Checksum                │  │
│  │      (8)      │      (8)      │            (16)                       │  │
│  ├───────────────┴───────────────┼───────────────────────────────────────┤  │
│  │            Source IP Address (32 bits)                                │  │
│  ├───────────────────────────────────────────────────────────────────────┤  │
│  │         Destination IP Address (32 bits)                              │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                                                                              │
│  TOS Byte Location: Byte 1 (offset 1) of the IPv4 header                    │
│                                                                              │
│  C Code Access:                                                              │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │  struct iphdr *ip = (struct iphdr*)skb_network_header(skb);           │  │
│  │  uint8_t tos = ip->tos;  // Get TOS byte directly                     │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

## 7.2 TOS Extraction from IPv4

From `ar_upperproto.h`:

```c
/*
 * Structure of the IP frame
 */
struct ip_header {
  uint8_t version_ihl;
  uint8_t tos;           // TOS byte at offset 1
  uint16_t tot_len;
  uint16_t id;
  uint16_t frag_off;
  uint8_t ttl;
  uint8_t protocol;
  uint16_t check;
  uint32_t saddr;
  uint32_t daddr;
};

#define IP_PRI_SHIFT 5   // Shift to extract IP Precedence from TOS
```

## 7.3 TOS Processing Code

From `ar_qos.c`:

```c
// TOS-based downstream mapping
AR_STATUS ar_qos_dp_set_map_dstream_tos(struct sk_buff* skb,
                                         struct ar_dp_vdev_s* vdev,
                                         int* v_wme_ac, int* v_pri)
{
  struct ether_header* eh = (struct ether_header*)skb_mac_header(skb);
  int pri = *v_pri;

  if (eh->ether_type == __constant_htons(ETHERTYPE_IP)) {
    const struct iphdr* ip = (struct iphdr*)skb_network_header(skb);

    // IP frame: exclude ECN bits 0-1 and map IP Precedence bits 7-5
    pri = (ip->tos & (~INET_ECN_MASK)) >> IP_PRI_SHIFT;
  }

  *v_wme_ac = AR_TID_TO_WME_AC(pri);
  AR_CEIL_QOS_PRIO(vdev, *v_wme_ac, pri);
  vdrv_dp_if_wbuf_set_tid(skb, pri);
  skb->priority = *v_wme_ac;
  *v_pri = pri;
  return AR_STATUS_SUCCESS;
}
```

---

# 8. TOS in IPv6 (Traffic Class)

## 8.1 IPv6 Header Structure

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         IPv6 Header Structure                                │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  IPv6 uses "Traffic Class" instead of "TOS" but with identical structure   │
│                                                                              │
│  Offset  0       4       8      12      16      20      24      28      31  │
│  ┌───────┬───────────────┬───────────────────────────────────────────────┐  │
│  │Version│ Traffic Class │              Flow Label                       │  │
│  │  (4)  │     (8)       │                (20)                           │  │
│  ├───────┴───────────────┼───────────────┬───────────────────────────────┤  │
│  │    Payload Length     │  Next Header  │        Hop Limit              │  │
│  │        (16)           │      (8)      │           (8)                 │  │
│  ├───────────────────────┴───────────────┴───────────────────────────────┤  │
│  │                    Source Address (128 bits)                          │  │
│  ├───────────────────────────────────────────────────────────────────────┤  │
│  │                  Destination Address (128 bits)                       │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                                                                              │
│  Traffic Class Byte (same structure as IPv4 TOS):                           │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │  DSCP (6 bits)                        │ ECN (2 bits)                  │  │
│  │  Bits 7-2                              │ Bits 1-0                      │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

## 8.2 IPv6 Traffic Class Extraction

From `ar_qos.c`:

```c
// IPv6 Traffic Class extraction for TOS mapping
} else if (eh->ether_type == __constant_htons(ETHERTYPE_IPV6)) {
    const struct ipv6hdr* ip = (struct ipv6hdr*)skb_network_header(skb);

    // Extract Traffic Class from IPv6 header
    // Traffic Class is split across priority (4 bits) and flow_lbl[0] (4 bits)
    pri = ip->priority;
    pri = (pri << 4);  // setting first 4 bits of pri = ip->priority value
    pri = pri | (((ip->flow_lbl[0]) >> 4) & 0x0f);  // setting last 4 bits
    pri = (pri >> IP_PRI_SHIFT);  // convert TOS to TID, by right shifting by 5
}
```

## 8.3 IPv6 Priority Field Layout

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    IPv6 Traffic Class Bit Layout                             │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  IPv6 Header First 32 bits:                                                  │
│  ┌──────────┬──────────────────┬────────────────────────────────────────┐   │
│  │ Version  │  Traffic Class   │           Flow Label                   │   │
│  │  4 bits  │     8 bits       │           20 bits                      │   │
│  └──────────┴──────────────────┴────────────────────────────────────────┘   │
│                                                                              │
│  Traffic Class stored in IPv6 header:                                        │
│  • ip->priority: Upper 4 bits (bits 7-4 of Traffic Class)                   │
│  • ip->flow_lbl[0] >> 4: Lower 4 bits (bits 3-0 of Traffic Class)           │
│                                                                              │
│  Reconstruction:                                                             │
│  tc = (ip->priority << 4) | ((ip->flow_lbl[0] >> 4) & 0x0f)                 │
│                                                                              │
│  IP Precedence extraction:                                                   │
│  ip_prec = tc >> 5                                                          │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

# 9. TOS to TID Mapping

## 9.1 Overview

In 802.11 WiFi networks, the TOS value from IP packets must be mapped to a Traffic Identifier (TID) for proper QoS handling. The TID is a 4-bit value (0-15), but typically only TID 0-7 are used for data traffic.

## 9.2 TOS to TID Mapping Table

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         TOS to TID Mapping                                   │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  IP Precedence (TOS >> 5)  →  TID  →  WMM Access Category                   │
│                                                                              │
│  ┌─────────────┬─────────┬────────┬─────────────────────────────────────┐   │
│  │ IP Prec     │   TID   │  WMM   │  Description                        │   │
│  ├─────────────┼─────────┼────────┼─────────────────────────────────────┤   │
│  │    0        │    0    │ AC_BE  │  Best Effort (default)              │   │
│  │    1        │    1    │ AC_BK  │  Background                         │   │
│  │    2        │    2    │ AC_BK  │  Background (Spare)                 │   │
│  │    3        │    3    │ AC_BE  │  Best Effort (Excellent Effort)     │   │
│  │    4        │    4    │ AC_VI  │  Video                              │   │
│  │    5        │    5    │ AC_VI  │  Video (Interactive)                │   │
│  │    6        │    6    │ AC_VO  │  Voice                              │   │
│  │    7        │    7    │ AC_VO  │  Network Control                    │   │
│  └─────────────┴─────────┴────────┴─────────────────────────────────────┘   │
│                                                                              │
│  Key Insight:                                                                │
│  • TOS-based mapping: TID = IP Precedence = (TOS >> 5) & 0x07              │
│  • Direct 1:1 mapping from IP Precedence to TID                             │
│  • Simpler than DSCP mapping (which requires lookup table)                  │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

## 9.3 TID to Access Category Mapping

```c
// From ar_qos.c - TID to WMM AC mapping
#define AR_TID_TO_WME_AC(tid)  \
    (((tid) == 0) ? WME_AC_BE : \
     ((tid) == 1) ? WME_AC_BK : \
     ((tid) == 2) ? WME_AC_BK : \
     ((tid) == 3) ? WME_AC_BE : \
     ((tid) == 4) ? WME_AC_VI : \
     ((tid) == 5) ? WME_AC_VI : \
     ((tid) == 6) ? WME_AC_VO : \
     ((tid) == 7) ? WME_AC_VO : WME_AC_BE)

// WMM Access Category definitions
#define WME_AC_BE   0    // Best Effort
#define WME_AC_BK   1    // Background
#define WME_AC_VI   2    // Video
#define WME_AC_VO   3    // Voice
```

## 9.4 Visual Mapping Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    TOS → TID → WMM Access Category Flow                     │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  TOS Byte: 0xB8 (Voice Traffic - DSCP EF)                                   │
│  ┌────────────────────────────────────────────────────────────────────────┐ │
│  │  Binary: 1 0 1 1 1 0 0 0                                               │ │
│  │          ├─┴─┴─┤                                                       │ │
│  │          IP Precedence = 5 (bits 7-5)                                  │ │
│  └────────────────────────────────────────────────────────────────────────┘ │
│                            │                                                 │
│                            ▼                                                 │
│  ┌────────────────────────────────────────────────────────────────────────┐ │
│  │  TID = 5 (TOS-based mapping uses IP Precedence directly)              │ │
│  └────────────────────────────────────────────────────────────────────────┘ │
│                            │                                                 │
│                            ▼                                                 │
│  ┌────────────────────────────────────────────────────────────────────────┐ │
│  │  WMM Access Category = AC_VI (Video)                                  │ │
│  │  Queue: Video queue with enhanced QoS parameters                      │ │
│  └────────────────────────────────────────────────────────────────────────┘ │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```



---

# 10. TOS Downstream Mapping

## 10.1 Overview

TOS downstream mapping is the process of classifying incoming traffic from the wired network to the wireless network based on the TOS field. This determines which WiFi queue (Access Category) the packet will use.

## 10.2 Configuration Value

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                      Downstream Mapping Values                               │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  Value │ Constant              │ Description                                │
│  ──────┼───────────────────────┼─────────────────────────────────────────── │
│    0   │ AR_QOS_DSTREAM_OFF    │ No downstream mapping (use default)        │
│    1   │ AR_QOS_DSTREAM_DSCP   │ Use DSCP (6 bits) for mapping              │
│    2   │ AR_QOS_DSTREAM_TOS    │ Use TOS/IP Precedence (3 bits)             │
│    3   │ AR_QOS_DSTREAM_8021P  │ Use 802.1p VLAN priority                   │
│                                                                              │
│  Configuration in ApQoSTest.py:                                              │
│  • qosDownStrMap=2 selects TOS-based downstream mapping                     │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

## 10.3 Driver Implementation

From `ar_qos.c`:

```c
/**
 * ar_qos_dp_set_map_dstream_tos - Map TOS to TID for downstream traffic
 * @skb: Socket buffer containing the packet
 * @vdev: Virtual device structure
 * @v_wme_ac: Output - WMM Access Category
 * @v_pri: Output - Priority (TID)
 *
 * This function extracts the IP Precedence from the TOS byte and maps it
 * directly to a TID value for downstream (AP to client) traffic.
 */
AR_STATUS ar_qos_dp_set_map_dstream_tos(struct sk_buff* skb,
                                         struct ar_dp_vdev_s* vdev,
                                         int* v_wme_ac, int* v_pri)
{
  struct ether_header* eh = (struct ether_header*)skb_mac_header(skb);
  int pri = *v_pri;

  if (eh->ether_type == __constant_htons(ETHERTYPE_IP)) {
    const struct iphdr* ip = (struct iphdr*)skb_network_header(skb);

    // IP frame: exclude ECN bits 0-1 and extract IP Precedence from bits 7-5
    // INET_ECN_MASK = 0x03, so ~INET_ECN_MASK = 0xFC
    // IP_PRI_SHIFT = 5
    pri = (ip->tos & (~INET_ECN_MASK)) >> IP_PRI_SHIFT;

  } else if (eh->ether_type == __constant_htons(ETHERTYPE_IPV6)) {
    const struct ipv6hdr* ip = (struct ipv6hdr*)skb_network_header(skb);

    // IPv6: Extract Traffic Class and convert to IP Precedence
    pri = ip->priority;
    pri = (pri << 4);
    pri = pri | (((ip->flow_lbl[0]) >> 4) & 0x0f);
    pri = (pri >> IP_PRI_SHIFT);
  }

  // Map TID to WMM Access Category
  *v_wme_ac = AR_TID_TO_WME_AC(pri);

  // Apply ceiling if configured
  AR_CEIL_QOS_PRIO(vdev, *v_wme_ac, pri);

  // Set TID in packet buffer
  vdrv_dp_if_wbuf_set_tid(skb, pri);
  skb->priority = *v_wme_ac;
  *v_pri = pri;

  return AR_STATUS_SUCCESS;
}
```

## 10.4 TOS Downstream Flow Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                      TOS Downstream Mapping Flow                             │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌─────────────┐    ┌─────────────────┐    ┌─────────────────┐              │
│  │   Wired     │───▶│  Access Point   │───▶│   Wireless      │              │
│  │   Network   │    │  (TOS Mapping)  │    │   Client        │              │
│  └─────────────┘    └─────────────────┘    └─────────────────┘              │
│         │                   │                       │                        │
│         │                   ▼                       │                        │
│         │    ┌─────────────────────────────┐       │                        │
│         │    │  1. Extract TOS from IP     │       │                        │
│         │    │  2. Mask ECN bits           │       │                        │
│         │    │  3. Shift >> 5 for IP Prec  │       │                        │
│         │    │  4. TID = IP Precedence     │       │                        │
│         │    │  5. Map TID to WMM AC       │       │                        │
│         │    │  6. Queue to appropriate AC │       │                        │
│         │    └─────────────────────────────┘       │                        │
│         │                   │                       │                        │
│         │                   ▼                       │                        │
│         │    ┌─────────────────────────────┐       │                        │
│         │    │  WiFi Frame Transmission    │       │                        │
│         │    │  with appropriate TID       │───────┘                        │
│         │    └─────────────────────────────┘                                │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```


---

# 11. TOS Upstream Marking

## 11.1 Overview

TOS upstream marking is the process of modifying (marking) the TOS field of packets traveling from wireless clients to the wired network. This allows the AP to set or preserve QoS markings for traffic leaving the WiFi network.

## 11.2 Configuration Flags

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        Upstream TOS Marking Flags                            │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  From ar_qos.h:                                                              │
│                                                                              │
│  #define AR_QOS_USTREAM_TOS_MASK   0x80  /* Bit 7: TOS upstream marking */  │
│                                                                              │
│  QoS Upstream Flags (8-bit byte):                                           │
│  ┌─────┬─────┬─────┬─────┬─────┬─────┬─────┬─────┐                          │
│  │  7  │  6  │  5  │  4  │  3  │  2  │  1  │  0  │                          │
│  ├─────┼─────┴─────┴─────┴─────┴─────┴─────┴─────┤                          │
│  │ TOS │              Reserved                   │                          │
│  └─────┴─────────────────────────────────────────┘                          │
│                                                                              │
│  Bit 7 (0x80): TOS upstream marking enable                                  │
│  • 1 = Mark upstream traffic with TOS based on TID                          │
│  • 0 = Preserve original TOS value                                          │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

## 11.3 Macro Definitions

From `ar_qos.h`:

```c
// TOS upstream marking macros
#define AR_QOS_USTREAM_TOS_MASK 0x80  /* # - - - - - - - */

// Check if TOS upstream marking is enabled for a VAP
#define AR_IS_QOS_USTREAM_TOS(_vap) (((_vap)->qos).ustream_tos)

// Set TOS upstream marking value for a VAP
#define AR_SET_QOS_USTREAM_TOS(_vap, _val) ((((_vap)->qos).ustream_tos) = (_val))
```

## 11.4 TOS Upstream Marking Flow

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                       TOS Upstream Marking Flow                              │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌─────────────────┐    ┌─────────────────┐    ┌─────────────┐              │
│  │   Wireless      │───▶│  Access Point   │───▶│   Wired     │              │
│  │   Client        │    │  (TOS Marking)  │    │   Network   │              │
│  └─────────────────┘    └─────────────────┘    └─────────────┘              │
│         │                       │                     │                      │
│         │                       ▼                     │                      │
│         │        ┌─────────────────────────────┐      │                      │
│         │        │  If TOS marking enabled:    │      │                      │
│         │        │  1. Get TID from WiFi frame │      │                      │
│         │        │  2. Map TID to TOS value    │      │                      │
│         │        │  3. Set TOS in IP header    │      │                      │
│         │        └─────────────────────────────┘      │                      │
│         │                       │                     │                      │
│         │                       ▼                     │                      │
│         │        ┌─────────────────────────────┐      │                      │
│         │        │  Packet with marked TOS    │───────┘                      │
│         │        │  forwarded to wired network │                             │
│         │        └─────────────────────────────┘                             │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

## 11.5 TID to TOS Conversion

When marking upstream traffic, the TID value from the WiFi frame is converted back to a TOS value:

```c
// TID to IP Precedence (TOS bits 7-5)
// TOS = TID << IP_PRI_SHIFT = TID << 5

uint8_t tid_to_tos(uint8_t tid) {
    return (tid & 0x07) << IP_PRI_SHIFT;  // IP_PRI_SHIFT = 5
}

// Example conversions:
// TID 0 → TOS 0x00 (Best Effort)
// TID 5 → TOS 0xA0 (CRITIC/ECP, IP Precedence 5)
// TID 6 → TOS 0xC0 (Internetwork Control)
// TID 7 → TOS 0xE0 (Network Control)
```


---

# 12. TOS Configuration in Arista AP

## 12.1 QoS Flag Encoding

In Arista APs, TOS configuration is part of the QoS flags byte that combines multiple settings:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         QoS Flags Encoding                                   │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  QoS Flags Byte (encoded in ApQoSTest.py):                                  │
│                                                                              │
│  flags = (qosPrio << 5) | (qosUpStrMarkDscpTos << 4) | qosDownStrMap        │
│                                                                              │
│  Bit Layout:                                                                 │
│  ┌─────┬─────┬─────┬─────┬─────┬─────┬─────┬─────┐                          │
│  │  7  │  6  │  5  │  4  │  3  │  2  │  1  │  0  │                          │
│  ├─────┴─────┴─────┼─────┼─────┴─────┴─────┴─────┤                          │
│  │   qosPrio (3)   │Uprm │  qosDownStrMap (4)    │                          │
│  └─────────────────┴─────┴───────────────────────┘                          │
│                                                                              │
│  Fields:                                                                     │
│  • Bits 7-5: qosPrio (0-7) - Priority ceiling                               │
│  • Bit 4:    qosUpStrMarkDscpTos - Upstream marking (0=off, 1=on)           │
│  • Bits 3-0: qosDownStrMap (0-3) - Downstream mapping type                  │
│                                                                              │
│  Example - TOS downstream with marking (qosPrio=4, marking=1, dstream=2):   │
│  flags = (4 << 5) | (1 << 4) | 2 = 0x80 | 0x10 | 0x02 = 0x92               │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

## 12.2 ApQoSTest.py Configuration Examples

```python
# From ApQoSTest.py - Test variants

class ApQoSTest(WifiClusterTest):
    # Test variant parameters
    qosPrio = 4              # Priority ceiling (0-7)
    qosUpStrMarkDscpTos = 1  # Enable upstream marking
    qosDownStrMap = 2        # TOS-based downstream mapping (2 = TOS)

    def configureSsid(self):
        # Configure SSID with QoS settings
        self.configureSsid(
            'TestSSID',
            qosDownStrMap=self.qosDownStrMap,
            qosUpStrMarkDscpTos=self.qosUpStrMarkDscpTos,
            qosPrio=self.qosPrio
        )

# Test Variants for TOS Testing:
# ApQoSTest__qosPrio_4_qosUpStrMarkDscpTos_1_qosDownStrMap_2
# - Uses TOS downstream mapping (qosDownStrMap=2)
# - Enables upstream DSCP/TOS marking
# - Sets priority ceiling to 4 (AC_VI)
```

## 12.3 Configuration Verification

The test verifies QoS flags are correctly applied:

```python
def verifyQoSConfig(self, ap):
    # Calculate expected QoS flags
    expectedFlags = (self.qosPrio << 5) | \
                    (self.qosUpStrMarkDscpTos << 4) | \
                    self.qosDownStrMap

    # Get actual flags from AP driver
    actualFlags = ap.getQoSFlags(vapIndex=0)

    # Verify flags match
    self.assertEqual(expectedFlags, actualFlags,
        f"QoS flags mismatch: expected {hex(expectedFlags)}, "
        f"got {hex(actualFlags)}")
```

## 12.4 Configuration Parameters Table

| Parameter | Values | Description |
|-----------|--------|-------------|
| `qosPrio` | 0-7 | Priority ceiling (highest allowed TID) |
| `qosUpStrMarkDscpTos` | 0, 1 | Enable/disable upstream TOS marking |
| `qosDownStrMap` | 0-3 | Downstream mapping type (2=TOS) |


---

# 13. Driver-Level TOS Implementation

## 13.1 Key Source Files

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                     Driver Source Files for TOS                              │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  File                                │ Purpose                               │
│  ────────────────────────────────────┼─────────────────────────────────────  │
│  ar_qos.c                            │ Core QoS/TOS processing functions    │
│  ar_qos.h                            │ QoS macros and flag definitions      │
│  ar_upperproto.h                     │ IP header structures, IP_PRI_SHIFT   │
│  wlan_son_ald.h                      │ IPTOS class selector definitions     │
│  firewall_marking.c                  │ Content analytics TOS marking        │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

## 13.2 Key Constants

From `ar_upperproto.h`:

```c
// IP Priority Shift - converts TOS byte to IP Precedence
#define IP_PRI_SHIFT 5

// ECN mask - used to exclude ECN bits from TOS processing
// INET_ECN_MASK = 0x03 (bits 0-1)
```

From `wlan_son_ald.h` - IPTOS Class Selector Values:

```c
// IP TOS Class Selector values (equivalent to DSCP CS values)
#define IPTOS_CLASS_CS0  0x00   // TOS 0x00, IP Prec 0, Best Effort
#define IPTOS_CLASS_CS1  0x20   // TOS 0x20, IP Prec 1, Priority
#define IPTOS_CLASS_CS2  0x40   // TOS 0x40, IP Prec 2, Immediate
#define IPTOS_CLASS_CS3  0x60   // TOS 0x60, IP Prec 3, Flash
#define IPTOS_CLASS_CS4  0x80   // TOS 0x80, IP Prec 4, Flash Override
#define IPTOS_CLASS_CS5  0xA0   // TOS 0xA0, IP Prec 5, CRITIC/ECP
#define IPTOS_CLASS_CS6  0xC0   // TOS 0xC0, IP Prec 6, Internetwork
#define IPTOS_CLASS_CS7  0xE0   // TOS 0xE0, IP Prec 7, Network Control
```

## 13.3 QoS Structure Definition

```c
// QoS configuration structure per VAP
struct ar_qos_config {
    uint8_t dstream;         // Downstream mapping type (0-3)
    uint8_t ustream_tos;     // Upstream TOS marking flag
    uint8_t prio_ceiling;    // Priority ceiling (0-7)
    uint8_t reserved;        // Reserved for future use
};

// Accessor macros
#define AR_IS_QOS_DSTREAM_TOS(_vap)  \
    ((((_vap)->qos).dstream) == AR_QOS_DSTREAM_TOS)

#define AR_IS_QOS_USTREAM_TOS(_vap)  \
    (((_vap)->qos).ustream_tos)
```

## 13.4 TOS Processing Decision Tree

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    Driver TOS Processing Decision Tree                       │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  Incoming Packet                                                             │
│       │                                                                      │
│       ▼                                                                      │
│  ┌─────────────────────┐                                                     │
│  │ Check ether_type    │                                                     │
│  └─────────────────────┘                                                     │
│       │                                                                      │
│       ├──── ETHERTYPE_IP (0x0800) ────▶ Extract IPv4 TOS: ip->tos          │
│       │                                                                      │
│       ├──── ETHERTYPE_IPV6 (0x86DD) ──▶ Extract IPv6 Traffic Class         │
│       │                                  tc = (priority << 4) |              │
│       │                                       (flow_lbl[0] >> 4)            │
│       │                                                                      │
│       └──── Other ────────────────────▶ Use default priority (0)            │
│                                                                              │
│  After TOS/TC extraction:                                                    │
│       │                                                                      │
│       ▼                                                                      │
│  ┌─────────────────────────────────────┐                                     │
│  │ Apply ECN mask:                     │                                     │
│  │ tos_masked = tos & (~INET_ECN_MASK) │                                     │
│  │ IP Prec = tos_masked >> 5           │                                     │
│  └─────────────────────────────────────┘                                     │
│       │                                                                      │
│       ▼                                                                      │
│  TID = IP Precedence (0-7)                                                  │
│       │                                                                      │
│       ▼                                                                      │
│  WMM AC = AR_TID_TO_WME_AC(TID)                                             │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```


---

# 14. TOS Processing Flow

## 14.1 Complete Downstream Processing Flow

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    Complete TOS Downstream Processing Flow                   │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  Step 1: Packet Reception                                                    │
│  ┌─────────────────────────────────────────────────────────────────────────┐│
│  │ Ethernet Frame from Wired Network                                       ││
│  │ ┌─────────────┬─────────────┬───────────────┬──────────────────────────┐││
│  │ │  Dst MAC    │  Src MAC    │  EtherType    │  Payload (IP Packet)     │││
│  │ └─────────────┴─────────────┴───────────────┴──────────────────────────┘││
│  └─────────────────────────────────────────────────────────────────────────┘│
│                                   │                                          │
│                                   ▼                                          │
│  Step 2: EtherType Check                                                     │
│  ┌─────────────────────────────────────────────────────────────────────────┐│
│  │ if (eh->ether_type == 0x0800)  // IPv4                                 ││
│  │ else if (eh->ether_type == 0x86DD)  // IPv6                            ││
│  └─────────────────────────────────────────────────────────────────────────┘│
│                                   │                                          │
│                                   ▼                                          │
│  Step 3: TOS/TC Extraction                                                   │
│  ┌─────────────────────────────────────────────────────────────────────────┐│
│  │ IPv4: tos = ip->tos                                                     ││
│  │ IPv6: tc = (ip->priority << 4) | ((ip->flow_lbl[0] >> 4) & 0x0f)       ││
│  └─────────────────────────────────────────────────────────────────────────┘│
│                                   │                                          │
│                                   ▼                                          │
│  Step 4: ECN Masking and IP Precedence Extraction                            │
│  ┌─────────────────────────────────────────────────────────────────────────┐│
│  │ pri = (tos & 0xFC) >> 5;   // Mask ECN, shift to get IP Precedence     ││
│  └─────────────────────────────────────────────────────────────────────────┘│
│                                   │                                          │
│                                   ▼                                          │
│  Step 5: TID Assignment                                                      │
│  ┌─────────────────────────────────────────────────────────────────────────┐│
│  │ tid = pri;  // TOS mapping: TID = IP Precedence directly               ││
│  └─────────────────────────────────────────────────────────────────────────┘│
│                                   │                                          │
│                                   ▼                                          │
│  Step 6: WMM AC Mapping                                                      │
│  ┌─────────────────────────────────────────────────────────────────────────┐│
│  │ wme_ac = AR_TID_TO_WME_AC(tid);                                        ││
│  │ // TID 0,3 → AC_BE, TID 1,2 → AC_BK, TID 4,5 → AC_VI, TID 6,7 → AC_VO ││
│  └─────────────────────────────────────────────────────────────────────────┘│
│                                   │                                          │
│                                   ▼                                          │
│  Step 7: Priority Ceiling                                                    │
│  ┌─────────────────────────────────────────────────────────────────────────┐│
│  │ AR_CEIL_QOS_PRIO(vdev, wme_ac, tid);                                   ││
│  │ // Cap priority to configured ceiling if exceeded                      ││
│  └─────────────────────────────────────────────────────────────────────────┘│
│                                   │                                          │
│                                   ▼                                          │
│  Step 8: Queue Selection                                                     │
│  ┌─────────────────────────────────────────────────────────────────────────┐│
│  │ skb->priority = wme_ac;                                                 ││
│  │ vdrv_dp_if_wbuf_set_tid(skb, tid);                                     ││
│  │ // Packet queued to appropriate WMM queue                              ││
│  └─────────────────────────────────────────────────────────────────────────┘│
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

## 14.2 Timing and Performance

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    TOS Processing Performance                                │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  TOS-based mapping is faster than DSCP mapping because:                      │
│                                                                              │
│  TOS Mapping:                                                                │
│  ┌─────────────────────────────────────────────────────────────────────────┐│
│  │  1. Mask ECN bits:     tos & 0xFC                    ~1 CPU cycle       ││
│  │  2. Shift right by 5:  >> 5                          ~1 CPU cycle       ││
│  │  3. Direct TID use:    tid = result                  ~1 CPU cycle       ││
│  │  Total: ~3 CPU cycles                                                   ││
│  └─────────────────────────────────────────────────────────────────────────┘│
│                                                                              │
│  DSCP Mapping:                                                               │
│  ┌─────────────────────────────────────────────────────────────────────────┐│
│  │  1. Shift right by 2:  >> 2                          ~1 CPU cycle       ││
│  │  2. Table lookup:      dscp_to_tid[dscp]             ~3-5 CPU cycles   ││
│  │  Total: ~4-6 CPU cycles                                                 ││
│  └─────────────────────────────────────────────────────────────────────────┘│
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

# 15. ECN (Explicit Congestion Notification)

## 15.1 Overview

ECN (Explicit Congestion Notification) occupies bits 0-1 of the TOS byte. These bits are intentionally excluded when processing TOS for QoS classification.

## 15.2 ECN Field Values

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         ECN Field Values (RFC 3168)                          │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ECN Bits (0-1)  │ Name      │ Description                                  │
│  ────────────────┼───────────┼───────────────────────────────────────────── │
│       00         │ Not-ECT   │ Not ECN-Capable Transport                    │
│       01         │ ECT(1)    │ ECN-Capable Transport (codepoint 1)          │
│       10         │ ECT(0)    │ ECN-Capable Transport (codepoint 0)          │
│       11         │ CE        │ Congestion Experienced                       │
│                                                                              │
│  ECN is used for:                                                            │
│  • Signaling network congestion without dropping packets                    │
│  • TCP endpoints can respond to congestion marks                            │
│  • Routers set CE when experiencing congestion                              │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

## 15.3 ECN Masking in Code

```c
// From Linux kernel include/net/inet_ecn.h
#define INET_ECN_MASK 0x03  // ECN bits mask (bits 0-1)

// TOS processing with ECN masking
pri = (ip->tos & (~INET_ECN_MASK)) >> IP_PRI_SHIFT;
// Equivalent to:
// pri = (ip->tos & 0xFC) >> 5;
//
// ~INET_ECN_MASK = ~0x03 = 0xFC = 11111100 binary
// This zeros out bits 0-1 (ECN) before extracting IP Precedence
```

## 15.4 ECN Preservation

When marking upstream traffic, ECN bits should be preserved:

```c
// Preserve ECN when setting TOS
uint8_t set_tos_preserve_ecn(uint8_t original_tos, uint8_t new_pri) {
    uint8_t ecn = original_tos & INET_ECN_MASK;  // Save ECN bits
    uint8_t new_tos = (new_pri << IP_PRI_SHIFT) | ecn;  // Combine
    return new_tos;
}
```


---

# 16. Testing TOS Functionality

## 16.1 ApQoSTest.py Overview

The `ApQoSTest.py` file tests TOS functionality when `qosDownStrMap=2` is configured:

```python
# From ApQoSTest.py
class ApQoSTest(WifiClusterTest):
    """
    Test QoS configuration including TOS downstream mapping.

    When qosDownStrMap=2, the test verifies that:
    1. QoS flags are correctly encoded and applied
    2. TOS-based traffic classification is working
    3. QoS counters increment for mapped traffic
    """

    # Test parameters
    qosPrio = 4              # Priority ceiling
    qosUpStrMarkDscpTos = 1  # Upstream marking enabled
    qosDownStrMap = 2        # TOS downstream mapping
```

## 16.2 Scapy TOS Testing Examples

Using Scapy to generate packets with specific TOS values:

```python
from scapy.all import *

# Create packets with different TOS/IP Precedence values

# Best Effort (IP Precedence 0, TOS 0x00)
pkt_be = IP(dst="10.0.0.1", tos=0x00)/ICMP()

# Priority (IP Precedence 1, TOS 0x20)
pkt_pri = IP(dst="10.0.0.1", tos=0x20)/ICMP()

# Immediate (IP Precedence 2, TOS 0x40)
pkt_imm = IP(dst="10.0.0.1", tos=0x40)/ICMP()

# Flash (IP Precedence 3, TOS 0x60)
pkt_flash = IP(dst="10.0.0.1", tos=0x60)/ICMP()

# Flash Override (IP Precedence 4, TOS 0x80)
pkt_fo = IP(dst="10.0.0.1", tos=0x80)/ICMP()

# CRITIC/ECP (IP Precedence 5, TOS 0xA0)
pkt_critic = IP(dst="10.0.0.1", tos=0xA0)/ICMP()

# Internetwork Control (IP Precedence 6, TOS 0xC0)
pkt_inter = IP(dst="10.0.0.1", tos=0xC0)/ICMP()

# Network Control (IP Precedence 7, TOS 0xE0)
pkt_net = IP(dst="10.0.0.1", tos=0xE0)/ICMP()

# Send packets
send(pkt_be)
send(pkt_critic)
```

## 16.3 DSCP to TOS Conversion for Testing

```python
# DSCP to TOS byte conversion
def dscp_to_tos(dscp):
    """Convert DSCP value to TOS byte."""
    return dscp << 2

# TOS byte to IP Precedence
def tos_to_ip_prec(tos):
    """Extract IP Precedence from TOS byte."""
    return (tos >> 5) & 0x07

# Common DSCP values and their TOS bytes
dscp_tos_mapping = {
    'CS0': (0, 0x00),    # Best Effort
    'CS1': (8, 0x20),    # Priority
    'CS2': (16, 0x40),   # Immediate
    'CS3': (24, 0x60),   # Flash
    'CS4': (32, 0x80),   # Flash Override
    'CS5': (40, 0xA0),   # CRITIC/ECP
    'CS6': (48, 0xC0),   # Internetwork
    'CS7': (56, 0xE0),   # Network Control
    'EF':  (46, 0xB8),   # Expedited Forwarding
    'AF41': (34, 0x88),  # Assured Forwarding 41
}

# Test all class selector values
for name, (dscp, tos) in dscp_tos_mapping.items():
    print(f"{name}: DSCP={dscp}, TOS=0x{tos:02X}, IP_Prec={tos_to_ip_prec(tos)}")
```

## 16.4 Verifying QoS Counters

```python
def verifyQoSCounters(self, ap, client):
    """
    Verify QoS counters after sending traffic with TOS values.
    """
    # Get initial counters
    initial_counters = ap.getQoSCounters()

    # Send traffic with specific TOS (e.g., 0xA0 = IP Prec 5)
    client.sendTraffic(tos=0xA0, count=100)

    # Wait for traffic to be processed
    time.sleep(2)

    # Get final counters
    final_counters = ap.getQoSCounters()

    # Verify AC_VI counter increased (IP Prec 5 → TID 5 → AC_VI)
    vi_increase = final_counters['AC_VI'] - initial_counters['AC_VI']
    self.assertGreater(vi_increase, 0,
        "AC_VI counter should increase for TOS 0xA0 traffic")
```

## 16.5 Debug Commands

```bash
# Show QoS configuration on AP
iwpriv ath0 get_qos_flags

# Show QoS counters per Access Category
cat /sys/kernel/debug/ieee80211/phy0/netdev:wlan0/stations/*/qos_counters

# Monitor TOS values in real-time (requires tcpdump)
tcpdump -i eth0 -n -v | grep "tos"

# Verify TID assignment in WiFi frames
iw dev wlan0 station dump | grep -A5 "Station"
```


---

# 17. TOS Reference Tables

## 17.1 Complete IP Precedence Table

| IP Prec | Name | TOS Byte | Binary | DSCP Equiv | TID | WMM AC |
|---------|------|----------|--------|------------|-----|--------|
| 0 | Routine | 0x00 | 000 00000 | CS0 (0) | 0 | AC_BE |
| 1 | Priority | 0x20 | 001 00000 | CS1 (8) | 1 | AC_BK |
| 2 | Immediate | 0x40 | 010 00000 | CS2 (16) | 2 | AC_BK |
| 3 | Flash | 0x60 | 011 00000 | CS3 (24) | 3 | AC_BE |
| 4 | Flash Override | 0x80 | 100 00000 | CS4 (32) | 4 | AC_VI |
| 5 | CRITIC/ECP | 0xA0 | 101 00000 | CS5 (40) | 5 | AC_VI |
| 6 | Internetwork | 0xC0 | 110 00000 | CS6 (48) | 6 | AC_VO |
| 7 | Network Control | 0xE0 | 111 00000 | CS7 (56) | 7 | AC_VO |

## 17.2 Common TOS Byte Values

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         Common TOS Byte Values                               │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  TOS   │ DSCP │ PHB Name    │ IP Prec │ Application          │ WMM AC      │
│  ──────┼──────┼─────────────┼─────────┼──────────────────────┼───────────  │
│  0x00  │  0   │ CS0/BE      │   0     │ Best Effort          │ AC_BE       │
│  0x20  │  8   │ CS1         │   1     │ Scavenger            │ AC_BK       │
│  0x28  │ 10   │ AF11        │   1     │ Bulk Data Low        │ AC_BK       │
│  0x40  │ 16   │ CS2         │   2     │ OAM                  │ AC_BK       │
│  0x48  │ 18   │ AF21        │   2     │ Transactional Data   │ AC_BK       │
│  0x60  │ 24   │ CS3         │   3     │ Signaling            │ AC_BE       │
│  0x68  │ 26   │ AF31        │   3     │ Multimedia Streaming │ AC_BE       │
│  0x80  │ 32   │ CS4         │   4     │ Real-Time Interactive│ AC_VI       │
│  0x88  │ 34   │ AF41        │   4     │ Video Conferencing   │ AC_VI       │
│  0xA0  │ 40   │ CS5         │   5     │ Broadcast Video      │ AC_VI       │
│  0xB8  │ 46   │ EF          │   5     │ Voice/VoIP           │ AC_VI       │
│  0xC0  │ 48   │ CS6         │   6     │ Network Control      │ AC_VO       │
│  0xE0  │ 56   │ CS7         │   7     │ Network Control      │ AC_VO       │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

## 17.3 TOS to TID Quick Reference

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        TOS to TID Quick Reference                            │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  Formula: TID = (TOS >> 5) & 0x07                                           │
│                                                                              │
│  TOS Range        │  IP Prec  │  TID  │  WMM AC  │  Queue Priority          │
│  ─────────────────┼───────────┼───────┼──────────┼────────────────────────  │
│  0x00 - 0x1F      │     0     │   0   │  AC_BE   │  Best Effort             │
│  0x20 - 0x3F      │     1     │   1   │  AC_BK   │  Background              │
│  0x40 - 0x5F      │     2     │   2   │  AC_BK   │  Background              │
│  0x60 - 0x7F      │     3     │   3   │  AC_BE   │  Best Effort             │
│  0x80 - 0x9F      │     4     │   4   │  AC_VI   │  Video                   │
│  0xA0 - 0xBF      │     5     │   5   │  AC_VI   │  Video                   │
│  0xC0 - 0xDF      │     6     │   6   │  AC_VO   │  Voice                   │
│  0xE0 - 0xFF      │     7     │   7   │  AC_VO   │  Voice                   │
│                                                                              │
│  Note: ECN bits (0-1) are masked out, so the actual range includes all     │
│  combinations of ECN within each TOS range.                                  │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

## 17.4 WMM Access Category Parameters

| AC | CWmin | CWmax | AIFSN | TXOP Limit | Traffic Type |
|----|-------|-------|-------|------------|--------------|
| AC_BK | 31 | 1023 | 7 | 0 | Background |
| AC_BE | 31 | 1023 | 3 | 0 | Best Effort |
| AC_VI | 15 | 31 | 2 | 3.008ms | Video |
| AC_VO | 7 | 15 | 2 | 1.504ms | Voice |

## 17.5 Bit Manipulation Reference

```c
// Common bit operations for TOS processing

// Extract IP Precedence (bits 7-5)
#define GET_IP_PREC(tos)     ((tos) >> 5)

// Extract DSCP (bits 7-2)
#define GET_DSCP(tos)        (((tos) >> 2) & 0x3F)

// Extract ECN (bits 1-0)
#define GET_ECN(tos)         ((tos) & 0x03)

// Set IP Precedence (preserving other bits)
#define SET_IP_PREC(tos, p)  (((tos) & 0x1F) | ((p) << 5))

// Set DSCP (preserving ECN)
#define SET_DSCP(tos, d)     (((tos) & 0x03) | ((d) << 2))

// TOS to TID conversion
#define TOS_TO_TID(tos)      (((tos) & 0xFC) >> 5)

// TID to TOS conversion
#define TID_TO_TOS(tid)      ((tid) << 5)
```



---

# 18. RFC Standards Reference

## 18.1 Primary RFCs for TOS

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           RFC Standards for TOS                              │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  RFC      │ Title                                    │ Status               │
│  ─────────┼──────────────────────────────────────────┼─────────────────────  │
│  RFC 791  │ Internet Protocol (IP)                   │ Standard (1981)      │
│           │ - Defines original TOS byte structure                          │
│           │ - 3-bit IP Precedence + 4-bit TOS flags                        │
│                                                                              │
│  RFC 1349 │ Type of Service in the Internet          │ Historic (1992)      │
│           │ - Extended TOS definitions                                      │
│           │ - Delay, Throughput, Reliability, Cost                          │
│                                                                              │
│  RFC 2474 │ Definition of the DS Field               │ Standard (1998)      │
│           │ - Redefined TOS byte as DS field                                │
│           │ - 6-bit DSCP + 2-bit ECN                                        │
│                                                                              │
│  RFC 2475 │ Architecture for Differentiated Services │ Informational        │
│           │ - DiffServ architecture overview                                │
│           │ - PHB (Per-Hop Behavior) concepts                               │
│                                                                              │
│  RFC 3168 │ Explicit Congestion Notification (ECN)   │ Standard (2001)      │
│           │ - Defines ECN bits (bits 0-1)                                   │
│           │ - ECT(0), ECT(1), CE codepoints                                 │
│                                                                              │
│  RFC 4594 │ Configuration Guidelines for DiffServ    │ Informational        │
│           │ - Service class recommendations                                  │
│           │ - DSCP to PHB mapping guidance                                  │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

## 18.2 RFC 791 - Original TOS Definition

From RFC 791 (September 1981):

```
Type of Service:  8 bits

    The Type of Service provides an indication of the abstract
    parameters of the quality of service desired.  These parameters
    are to be used to guide the selection of the actual service
    parameters when transmitting a datagram through a particular
    network.

      Bits 0-2:  Precedence.
      Bit    3:  0 = Normal Delay,      1 = Low Delay.
      Bits   4:  0 = Normal Throughput, 1 = High Throughput.
      Bits   5:  0 = Normal Relibility, 1 = High Relibility.
      Bits 6-7:  Reserved for Future Use.

         0     1     2     3     4     5     6     7
      +-----+-----+-----+-----+-----+-----+-----+-----+
      |                 |     |     |     |     |     |
      |   PRECEDENCE    |  D  |  T  |  R  |  0  |  0  |
      |                 |     |     |     |     |     |
      +-----+-----+-----+-----+-----+-----+-----+-----+

      Precedence

        111 - Network Control
        110 - Internetwork Control
        101 - CRITIC/ECP
        100 - Flash Override
        011 - Flash
        010 - Immediate
        001 - Priority
        000 - Routine
```

## 18.3 RFC 2474 - DSCP Redefinition

RFC 2474 (December 1998) redefined the TOS byte:

```
      0   1   2   3   4   5   6   7
    +---+---+---+---+---+---+---+---+
    |         DSCP          |  CU   |
    +---+---+---+---+---+---+---+---+

    DSCP: Differentiated Services Code Point (6 bits)
    CU: Currently Unused (later used for ECN, 2 bits)
```

## 18.4 Backward Compatibility

The relationship between legacy IP Precedence and modern DSCP:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    IP Precedence to DSCP Compatibility                       │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  IP Precedence values map to Class Selector (CS) DSCP values:               │
│                                                                              │
│  IP Prec 0 (000) = CS0 = DSCP 0  (000 000)                                  │
│  IP Prec 1 (001) = CS1 = DSCP 8  (001 000)                                  │
│  IP Prec 2 (010) = CS2 = DSCP 16 (010 000)                                  │
│  IP Prec 3 (011) = CS3 = DSCP 24 (011 000)                                  │
│  IP Prec 4 (100) = CS4 = DSCP 32 (100 000)                                  │
│  IP Prec 5 (101) = CS5 = DSCP 40 (101 000)                                  │
│  IP Prec 6 (110) = CS6 = DSCP 48 (110 000)                                  │
│  IP Prec 7 (111) = CS7 = DSCP 56 (111 000)                                  │
│                                                                              │
│  Relationship: DSCP = IP_Precedence × 8                                     │
│               TOS_Byte = IP_Precedence << 5                                  │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```


---

# 19. Troubleshooting Guide

## 19.1 Common TOS Issues

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         Common TOS Issues                                    │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  Issue                         │ Possible Cause             │ Solution      │
│  ─────────────────────────────┼────────────────────────────┼─────────────── │
│  Traffic not prioritized       │ qosDownStrMap != 2         │ Set to 2      │
│  Wrong queue assignment        │ ECN bits not masked        │ Check driver  │
│  VoIP in wrong AC              │ IP Prec mapping issue      │ Verify TOS    │
│  All traffic in BE             │ QoS disabled               │ Enable QoS    │
│  Priority ceiling ignored      │ qosPrio not set            │ Configure     │
│  IPv6 not classified           │ TC extraction issue        │ Check driver  │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

## 19.2 Debug Commands

### 19.2.1 Checking QoS Configuration

```bash
# Check QoS flags on VAP
iwpriv ath0 get_qos_flags

# Expected output for TOS mapping enabled:
# ath0    get_qos_flags:0x8200
#   Bit 9 (0x200) = TOS downstream mapping
#   Bit 15 (0x8000) = TOS upstream marking

# Check QoS configuration via config agent
arista-ap-cli show ssid qos

# Check driver QoS state
cat /sys/kernel/debug/ar_qos/vap0/config
```

### 19.2.2 Monitoring Traffic

```bash
# Watch TOS values on incoming traffic
tcpdump -i eth0 -n -v 'ip' 2>/dev/null | grep -E "tos 0x[0-9a-f]+"

# Count packets by TOS value
tcpdump -i eth0 -n -c 1000 'ip' 2>&1 | \
    grep -oE "tos 0x[0-9a-f]+" | sort | uniq -c | sort -rn

# Monitor WMM queue statistics
watch -n 1 'cat /sys/kernel/debug/ieee80211/phy0/statistics'
```

### 19.2.3 Verifying TID Assignment

```bash
# Check TID statistics per station
iw dev wlan0 station dump | grep -A 20 "Station"

# Check per-AC packet counts
cat /sys/kernel/debug/ieee80211/phy0/netdev:wlan0/queues/*/count
```

## 19.3 Troubleshooting Decision Tree

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                      TOS Troubleshooting Decision Tree                       │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  START: Traffic not being prioritized correctly                              │
│       │                                                                      │
│       ▼                                                                      │
│  ┌─────────────────────────────────────┐                                     │
│  │ Is qosDownStrMap set to 2 (TOS)?    │                                     │
│  └─────────────────────────────────────┘                                     │
│       │                                                                      │
│   No ─┼─▶ Set qosDownStrMap=2 in SSID config                                │
│       │                                                                      │
│  Yes  │                                                                      │
│       ▼                                                                      │
│  ┌─────────────────────────────────────┐                                     │
│  │ Is traffic IP (not ARP/DHCP)?       │                                     │
│  └─────────────────────────────────────┘                                     │
│       │                                                                      │
│   No ─┼─▶ Non-IP traffic uses default priority (AC_BE)                      │
│       │                                                                      │
│  Yes  │                                                                      │
│       ▼                                                                      │
│  ┌─────────────────────────────────────┐                                     │
│  │ Is TOS byte set correctly?          │                                     │
│  └─────────────────────────────────────┘                                     │
│       │                                                                      │
│   No ─┼─▶ Verify source is marking TOS (tcpdump)                            │
│       │                                                                      │
│  Yes  │                                                                      │
│       ▼                                                                      │
│  ┌─────────────────────────────────────┐                                     │
│  │ Is priority ceiling blocking?       │                                     │
│  └─────────────────────────────────────┘                                     │
│       │                                                                      │
│  Yes ─┼─▶ Increase qosPrio to allow higher priorities                       │
│       │                                                                      │
│   No  │                                                                      │
│       ▼                                                                      │
│  Check driver logs: dmesg | grep -i qos                                      │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

## 19.4 Common Mistakes

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          Common TOS Mistakes                                 │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  1. Confusing DSCP and TOS values                                           │
│     ❌ Wrong: Setting TOS=46 for VoIP                                       │
│     ✓ Right: Setting TOS=0xB8 (DSCP 46 = 46<<2 = 0xB8)                      │
│                                                                              │
│  2. Forgetting ECN bits affect TOS byte but not priority                    │
│     ❌ Wrong: Expecting TOS 0xB9 to be different from 0xB8                  │
│     ✓ Right: Both map to same IP Precedence (5)                             │
│                                                                              │
│  3. Using TOS mapping when DSCP mapping is needed                           │
│     ❌ Wrong: Using qosDownStrMap=2 when fine-grained DSCP control needed   │
│     ✓ Right: Use qosDownStrMap=1 for full 64-value DSCP mapping             │
│                                                                              │
│  4. Setting priority ceiling too low                                        │
│     ❌ Wrong: qosPrio=3 blocks all video/voice traffic                      │
│     ✓ Right: qosPrio=7 or appropriate ceiling for use case                  │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

## 19.5 Log Messages

```bash
# Common QoS-related log messages

# TOS mapping applied
[ar_qos] TOS downstream mapping enabled for vap0

# QoS configuration applied
[ar_qos] QoS flags set: dstream=2 ustream_tos=1 prio=4

# Priority ceiling applied
[ar_qos] Priority capped from 6 to 4 for vap0

# ECN processing
[ar_qos] ECN bits preserved: original=0xB9 marked=0xB8
```


---

# 20. Appendix

## 20.1 Glossary

| Term | Definition |
|------|------------|
| **TOS** | Type of Service - 8-bit field in IPv4 header for QoS |
| **DSCP** | Differentiated Services Code Point - 6-bit QoS marking |
| **ECN** | Explicit Congestion Notification - 2-bit congestion signaling |
| **IP Precedence** | Legacy 3-bit priority field (bits 7-5 of TOS) |
| **TID** | Traffic Identifier - 802.11 queue selector (0-7) |
| **WMM** | Wi-Fi Multimedia - QoS extension for 802.11 |
| **AC** | Access Category - WMM traffic class (VO, VI, BE, BK) |
| **PHB** | Per-Hop Behavior - DiffServ forwarding treatment |
| **CS** | Class Selector - DSCP values compatible with IP Precedence |
| **EF** | Expedited Forwarding - Low-latency PHB for voice |
| **AF** | Assured Forwarding - Multi-class PHB with drop precedence |
| **VAP** | Virtual Access Point - Logical WiFi interface |
| **CWmin/CWmax** | Contention Window min/max - EDCA backoff parameters |
| **AIFSN** | Arbitration Inter-Frame Space Number |
| **TXOP** | Transmission Opportunity - Time to transmit |

## 20.2 Code File References

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         TOS-Related Source Files                             │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  File Path                                    │ Purpose                      │
│  ─────────────────────────────────────────────┼───────────────────────────── │
│  ap/src/wlan-drivers/ar/core/src/ar_qos.c    │ Core QoS processing          │
│  ap/src/wlan-drivers/ar/core/src/ar_qos.h    │ QoS macros and flags         │
│  ap/src/wlan-drivers/ar/core/src/ar_upper    │ IP header structures         │
│    proto.h                                    │                              │
│  ap/src/wlan-drivers/QCA/.../wlan_son_ald.h  │ IPTOS class definitions      │
│  ap/src/go/.../ssid_qos_qca.go               │ Go config agent QoS          │
│  autotest/.../ApQoSTest.py                   │ QoS test automation          │
│  ap/src/content_analytics/src/firewall_      │ Content analytics marking    │
│    marking.c                                  │                              │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

## 20.3 Quick Reference Card

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           TOS Quick Reference Card                           │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │  TOS BYTE STRUCTURE                                                  │    │
│  │  ┌───────────────────────────┬───────────────────────┬─────────────┐│    │
│  │  │ Bits 7-5 (IP Precedence) │ Bits 4-2 (DSCP low)  │ Bits 1-0    ││    │
│  │  │       (3 bits)           │     (3 bits)         │   (ECN)     ││    │
│  │  └───────────────────────────┴───────────────────────┴─────────────┘│    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │  CONVERSIONS                                                         │    │
│  │  • TOS → IP Prec:  (tos >> 5) & 0x07                                │    │
│  │  • TOS → DSCP:     (tos >> 2) & 0x3F                                │    │
│  │  • DSCP → TOS:     dscp << 2                                        │    │
│  │  • IP Prec → TID:  ip_prec (direct)                                 │    │
│  │  • TID → WMM AC:   AR_TID_TO_WME_AC(tid)                            │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │  COMMON TOS VALUES                                                   │    │
│  │  0x00 = Best Effort    (IP Prec 0, AC_BE)                           │    │
│  │  0x20 = Priority       (IP Prec 1, AC_BK)                           │    │
│  │  0x80 = Flash Override (IP Prec 4, AC_VI)                           │    │
│  │  0xB8 = VoIP/EF        (IP Prec 5, AC_VI, DSCP 46)                  │    │
│  │  0xE0 = Network Ctrl   (IP Prec 7, AC_VO)                           │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │  CONFIGURATION                                                       │    │
│  │  • qosDownStrMap=2  → Enable TOS downstream mapping                 │    │
│  │  • qosUpStrMarkDscpTos=1 → Enable upstream TOS marking              │    │
│  │  • qosPrio=0-7      → Set priority ceiling                          │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │  DEBUG COMMANDS                                                      │    │
│  │  • iwpriv ath0 get_qos_flags                                        │    │
│  │  • tcpdump -i eth0 -n -v | grep tos                                 │    │
│  │  • iw dev wlan0 station dump                                        │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

## 20.4 Python TOS Utilities

```python
#!/usr/bin/env python3
"""TOS Utility Functions for Testing and Debugging."""

# TOS byte manipulation
def tos_to_ip_precedence(tos: int) -> int:
    """Extract IP Precedence from TOS byte."""
    return (tos >> 5) & 0x07

def tos_to_dscp(tos: int) -> int:
    """Extract DSCP from TOS byte."""
    return (tos >> 2) & 0x3F

def tos_to_ecn(tos: int) -> int:
    """Extract ECN from TOS byte."""
    return tos & 0x03

def dscp_to_tos(dscp: int, ecn: int = 0) -> int:
    """Create TOS byte from DSCP and ECN."""
    return (dscp << 2) | (ecn & 0x03)

def ip_prec_to_tos(ip_prec: int) -> int:
    """Create TOS byte from IP Precedence."""
    return ip_prec << 5

# TID mapping
TID_TO_AC = {0: 'AC_BE', 1: 'AC_BK', 2: 'AC_BK', 3: 'AC_BE',
             4: 'AC_VI', 5: 'AC_VI', 6: 'AC_VO', 7: 'AC_VO'}

def tos_to_tid(tos: int) -> int:
    """Convert TOS to TID (for TOS mapping mode)."""
    return (tos >> 5) & 0x07

def tos_to_ac(tos: int) -> str:
    """Convert TOS to WMM Access Category."""
    return TID_TO_AC[tos_to_tid(tos)]

# Display function
def analyze_tos(tos: int) -> None:
    """Analyze and display TOS byte components."""
    print(f"TOS Byte: 0x{tos:02X} ({tos:08b})")
    print(f"  IP Precedence: {tos_to_ip_precedence(tos)}")
    print(f"  DSCP: {tos_to_dscp(tos)}")
    print(f"  ECN: {tos_to_ecn(tos)}")
    print(f"  TID: {tos_to_tid(tos)}")
    print(f"  WMM AC: {tos_to_ac(tos)}")
```

---

# Document Information

| Field | Value |
|-------|-------|
| **Document Title** | TOS (Type of Service) Technical Reference |
| **Version** | 1.0 |
| **Created** | 2026-02-03 |
| **Author** | Augment Agent |
| **Target Audience** | Network Engineers, QoS Developers, Test Engineers |
| **Related Documents** | DSCP_Documentation.md, ApQoSTest_Documentation.md |

---

*End of Document*
