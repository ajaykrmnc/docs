# Comprehensive DSCP (Differentiated Services Code Point) Documentation

## Arista WiFi AP Implementation Reference Guide

**Document Version:** 1.0
**Date:** 2024
**Author:** Arista Networks Documentation

---

# Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [Introduction to DSCP](#2-introduction-to-dscp)
3. [DSCP Field Structure](#3-dscp-field-structure)
4. [DSCP Values and Classes](#4-dscp-values-and-classes)
5. [DSCP to TID Mapping](#5-dscp-to-tid-mapping)
6. [DSCP in WiFi (802.11e/WMM)](#6-dscp-in-wifi-80211ewmm)
7. [DSCP vs TOS](#7-dscp-vs-tos)
8. [DSCP to 802.1p (PCP) Mapping](#8-dscp-to-8021p-pcp-mapping)
9. [DSCP Configuration in Arista AP](#9-dscp-configuration-in-arista-ap)
10. [Driver-Level DSCP Implementation](#10-driver-level-dscp-implementation)
11. [DSCP Exception Handling](#11-dscp-exception-handling)
12. [QoS Map Structure](#12-qos-map-structure)
13. [Upstream DSCP Marking](#13-upstream-dscp-marking)
14. [Downstream DSCP Mapping](#14-downstream-dscp-mapping)
15. [DSCP in IPv4 vs IPv6](#15-dscp-in-ipv4-vs-ipv6)
16. [Testing DSCP Functionality](#16-testing-dscp-functionality)
17. [DSCP Reference Tables](#17-dscp-reference-tables)
18. [RFC Standards Reference](#18-rfc-standards-reference)
19. [Troubleshooting Guide](#19-troubleshooting-guide)
20. [Appendix](#20-appendix)

---

# 1. Executive Summary

## 1.1 What is DSCP?

**DSCP (Differentiated Services Code Point)** is a 6-bit field in the IP header used to classify and manage network traffic, enabling Quality of Service (QoS) in IP networks. It is defined in **RFC 2474** and replaces the older Type of Service (ToS) precedence field.

## 1.2 Key Concepts

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           DSCP Key Concepts                                  │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐         │
│  │    DSCP         │    │    TID          │    │    WMM AC       │         │
│  │  (6 bits)       │───▶│  (3 bits)       │───▶│  (2 bits)       │         │
│  │  0-63 values    │    │  0-7 values     │    │  BE,BK,VI,VO    │         │
│  └─────────────────┘    └─────────────────┘    └─────────────────┘         │
│                                                                              │
│  • DSCP: Differentiated Services Code Point - IP layer marking              │
│  • TID:  Traffic Identifier - 802.11 layer priority                         │
│  • AC:   Access Category - WiFi Multimedia (WMM) queue                       │
│  • PCP:  Priority Code Point - 802.1p VLAN priority                          │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

## 1.3 Purpose in Arista WiFi AP

DSCP is used in Arista WiFi Access Points to:

1. **Classify incoming traffic** - Determine priority based on DSCP values
2. **Map to WiFi priorities** - Convert DSCP to 802.11 TID/AC
3. **Mark outgoing traffic** - Apply DSCP values for upstream QoS
4. **Enforce QoS policies** - Manage traffic based on service level
5. **Support Hotspot 2.0** - Implement DSCP exceptions and QoS Maps

## 1.4 Document Scope

This document covers:
- DSCP fundamentals and standards (RFC 2474, 2475, 2597, 2598, 4594)
- Implementation in Arista WiFi AP codebase
- DSCP-to-TID mapping tables in QCA drivers
- Configuration options and parameters
- Testing and validation procedures
- Troubleshooting common issues

---

# 2. Introduction to DSCP

## 2.1 Historical Background

### 2.1.1 Evolution from ToS to DSCP

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                     Evolution of IP QoS Fields                               │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │                    Original ToS (RFC 791 - 1981)                       │  │
│  ├───────────────────────────────────────────────────────────────────────┤  │
│  │ Bit: │  0  │  1  │  2  │  3  │  4  │  5  │  6  │  7  │               │  │
│  │      │<------ Precedence ------>│ D │ T │ R │ 0 │               │  │
│  │      │      (3 bits)            │   │   │   │   │               │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                               │                                              │
│                               ▼                                              │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │                 Differentiated Services (RFC 2474 - 1998)              │  │
│  ├───────────────────────────────────────────────────────────────────────┤  │
│  │ Bit: │  0  │  1  │  2  │  3  │  4  │  5  │  6  │  7  │               │  │
│  │      │<------------ DSCP ------------->│<-- ECN -->│               │  │
│  │      │          (6 bits)               │ (2 bits)  │               │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                                                                              │
│  Legend:                                                                     │
│  • Precedence: Original 3-bit priority field                                │
│  • D: Delay, T: Throughput, R: Reliability (unused in practice)            │
│  • DSCP: Differentiated Services Code Point (6 bits, 64 values)            │
│  • ECN: Explicit Congestion Notification (2 bits)                           │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 2.1.2 Why DSCP Was Introduced

| Limitation of ToS | Solution with DSCP |
|-------------------|-------------------|
| Only 8 priority levels (3 bits) | 64 code points (6 bits) |
| Ambiguous field definitions | Well-defined PHBs |
| Inconsistent implementations | Standardized behavior |
| Limited scalability | Supports complex QoS policies |

## 2.2 DSCP in the Network Stack

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    DSCP in the Network Protocol Stack                        │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │ Application Layer                                                    │    │
│  │ (VoIP, Video, Web, etc.)                                            │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                              │                                               │
│                              ▼ Marks traffic with DSCP                       │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │ Transport Layer (TCP/UDP)                                            │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                              │                                               │
│                              ▼                                               │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │ Network Layer (IP)                                                   │    │
│  │ ┌───────────────────────────────────────────────────────────────┐   │    │
│  │ │ IPv4 Header: ... | ToS Byte [DSCP|ECN] | ... | Src IP | Dst IP│   │    │
│  │ └───────────────────────────────────────────────────────────────┘   │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                              │                                               │
│                              ▼ AP reads DSCP, maps to TID                    │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │ Data Link Layer (802.11 MAC)                                         │    │
│  │ ┌───────────────────────────────────────────────────────────────┐   │    │
│  │ │ 802.11 Header: ... | QoS Control [TID|...] | ...              │   │    │
│  │ └───────────────────────────────────────────────────────────────┘   │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                              │                                               │
│                              ▼ Queued by Access Category                     │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │ Physical Layer (802.11 PHY)                                          │    │
│  │ ┌────────┐  ┌────────┐  ┌────────┐  ┌────────┐                      │    │
│  │ │ AC_VO  │  │ AC_VI  │  │ AC_BE  │  │ AC_BK  │                      │    │
│  │ │(Voice) │  │(Video) │  │(Best E)│  │(Backgnd)│                      │    │
│  │ └────────┘  └────────┘  └────────┘  └────────┘                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

## 2.3 Per-Hop Behaviors (PHB)

DSCP defines several standard Per-Hop Behaviors:

| PHB | Description | DSCP Values | Use Case |
|-----|-------------|-------------|----------|
| **Default (BE)** | Best Effort forwarding | 0 (CS0) | General traffic |
| **EF** | Expedited Forwarding | 46 | Real-time voice |
| **AF** | Assured Forwarding | 10-43 | Business applications |
| **CS** | Class Selector | 0,8,16,24,32,40,48,56 | Backward compatibility |

---

# 3. DSCP Field Structure

## 3.1 IP Header ToS/DSCP Byte

### 3.1.1 IPv4 ToS Byte Layout

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        IPv4 Type of Service (ToS) Byte                       │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  Byte Position in IPv4 Header: Offset 1 (second byte)                       │
│                                                                              │
│  ┌─────┬─────┬─────┬─────┬─────┬─────┬─────┬─────┐                         │
│  │ Bit │ Bit │ Bit │ Bit │ Bit │ Bit │ Bit │ Bit │                         │
│  │  7  │  6  │  5  │  4  │  3  │  2  │  1  │  0  │                         │
│  ├─────┴─────┴─────┴─────┴─────┴─────┼─────┴─────┤                         │
│  │            DSCP (6 bits)          │ ECN (2b)  │                         │
│  │         (Bits 7-2 of ToS)         │(Bits 1-0) │                         │
│  └───────────────────────────────────┴───────────┘                         │
│                                                                              │
│  To extract DSCP from ToS byte:                                             │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │  DSCP = (ToS & 0xFC) >> 2                                              │  │
│  │  ECN  = ToS & 0x03                                                     │  │
│  │  DSCP Mask: 0xFC = 11111100 (binary)                                   │  │
│  │  ECN Mask:  0x03 = 00000011 (binary)                                   │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                                                                              │
│  From ar_qos.c:                                                              │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │  dscp = (ip->tos & (~INET_ECN_MASK)) >> 2;                            │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 3.1.2 DSCP Value Encoding

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        DSCP Value Encoding Examples                          │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │ DSCP Value: 46 (EF - Expedited Forwarding)                          │    │
│  │                                                                      │    │
│  │ DSCP Binary: 101110                                                  │    │
│  │ ToS Byte:    10111000 = 0xB8 = 184                                  │    │
│  │              [DSCP  ][ECN]                                           │    │
│  │              101110   00                                             │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │ DSCP Value: 0 (CS0 - Best Effort)                                   │    │
│  │                                                                      │    │
│  │ DSCP Binary: 000000                                                  │    │
│  │ ToS Byte:    00000000 = 0x00 = 0                                    │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │ DSCP Value: 34 (AF41 - Assured Forwarding Class 4, Low Drop)        │    │
│  │                                                                      │    │
│  │ DSCP Binary: 100010                                                  │    │
│  │ ToS Byte:    10001000 = 0x88 = 136                                  │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

## 3.2 IPv6 Traffic Class

### 3.2.1 IPv6 Header Structure

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        IPv6 Header - DSCP Location                           │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  IPv6 Header (First 4 bytes):                                               │
│  ┌────────────────────────────────────────────────────────────────────┐     │
│  │ Version │ Traffic Class │           Flow Label                     │     │
│  │ (4 bits)│   (8 bits)    │           (20 bits)                      │     │
│  ├─────────┼───────────────┼──────────────────────────────────────────┤     │
│  │  0110   │ DDDDDD EE     │  LLLL LLLL LLLL LLLL LLLL               │     │
│  └─────────┴───────────────┴──────────────────────────────────────────┘     │
│                                                                              │
│  Where:                                                                      │
│  • DDDDDD = DSCP (6 bits) - same as IPv4                                    │
│  • EE = ECN (2 bits)                                                        │
│  • L = Flow Label bits                                                       │
│                                                                              │
│  From ar_qos.c (IPv6 extraction):                                           │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │  ver_pri_flowlabel = *(unsigned long*)(eh + 1);                       │  │
│  │  pri = (ntohl(ver_pri_flowlabel) & IPV6_PRIORITY_MASK) >>             │  │
│  │        IPV6_PRIORITY_SHIFT;                                           │  │
│  │  dscp = (pri & (~INET_ECN_MASK)) >> 2;                                │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

# 4. DSCP Values and Classes

## 4.1 Class Selector (CS) Code Points

Class Selector code points provide backward compatibility with IP Precedence.

### 4.1.1 CS Code Points Definition

From `wlan_son_ald.h`:

```c
/*
 * In RFC 2474, Section 4.2.2.1, the Class Selector Codepoints subsume
 * the old ToS Precedence values.
 */

#define IPTOS_CLASS_CS0                 0x00    /* DSCP 0  - Best Effort */
#define IPTOS_CLASS_CS1                 0x20    /* DSCP 8  - Scavenger */
#define IPTOS_CLASS_CS2                 0x40    /* DSCP 16 - OAM */
#define IPTOS_CLASS_CS3                 0x60    /* DSCP 24 - Signaling */
#define IPTOS_CLASS_CS4                 0x80    /* DSCP 32 - Real-Time Interactive */
#define IPTOS_CLASS_CS5                 0xa0    /* DSCP 40 - Broadcast Video */
#define IPTOS_CLASS_CS6                 0xc0    /* DSCP 48 - Network Control */
#define IPTOS_CLASS_CS7                 0xe0    /* DSCP 56 - Reserved */

#define IPTOS_CLASS_DEFAULT             IPTOS_CLASS_CS0
```

### 4.1.2 CS Reference Table

| Class Selector | ToS Value | Binary | DSCP Value | Description |
|----------------|-----------|--------|------------|-------------|
| CS0 | 0x00 | 000 000 | 0 | Best Effort (Default) |
| CS1 | 0x20 | 001 000 | 8 | Scavenger / Low Priority |
| CS2 | 0x40 | 010 000 | 16 | OAM (Operations, Admin, Maintenance) |
| CS3 | 0x60 | 011 000 | 24 | Signaling |
| CS4 | 0x80 | 100 000 | 32 | Real-Time Interactive |
| CS5 | 0xa0 | 101 000 | 40 | Broadcast Video |
| CS6 | 0xc0 | 110 000 | 48 | Network Control |
| CS7 | 0xe0 | 111 000 | 56 | Reserved for Network Control |

## 4.2 Assured Forwarding (AF) Classes

Defined in **RFC 2597**, AF provides differentiated levels of forwarding assurance.

### 4.2.1 AF Code Points Definition

From `wlan_son_ald.h`:

```c
/*
 * Definitions for IP differentiated services code points (DSCP)
 *
 * Taken from RFC-2597, Section 6 and RFC-2598, Section 2.3.
 */

#define IPTOS_DSCP_MASK         0xfc

#define IPTOS_DSCP_AF11         0x28    /* DSCP 10 - Class 1, Low Drop */
#define IPTOS_DSCP_AF12         0x30    /* DSCP 12 - Class 1, Medium Drop */
#define IPTOS_DSCP_AF13         0x38    /* DSCP 14 - Class 1, High Drop */
#define IPTOS_DSCP_AF21         0x48    /* DSCP 18 - Class 2, Low Drop */
#define IPTOS_DSCP_AF22         0x50    /* DSCP 20 - Class 2, Medium Drop */
#define IPTOS_DSCP_AF23         0x58    /* DSCP 22 - Class 2, High Drop */
#define IPTOS_DSCP_AF31         0x68    /* DSCP 26 - Class 3, Low Drop */
#define IPTOS_DSCP_AF32         0x70    /* DSCP 28 - Class 3, Medium Drop */
#define IPTOS_DSCP_AF33         0x78    /* DSCP 30 - Class 3, High Drop */
#define IPTOS_DSCP_AF41         0x88    /* DSCP 34 - Class 4, Low Drop */
#define IPTOS_DSCP_AF42         0x90    /* DSCP 36 - Class 4, Medium Drop */
#define IPTOS_DSCP_AF43         0x98    /* DSCP 38 - Class 4, High Drop */
```

### 4.2.2 AF Classes Matrix

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    Assured Forwarding (AF) PHB Classes                       │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│              │      Low Drop      │   Medium Drop     │    High Drop        │
│              │  Precedence (1)    │ Precedence (2)    │  Precedence (3)    │
│  ────────────┼────────────────────┼───────────────────┼────────────────────│
│  Class 1     │ AF11 (DSCP 10)     │ AF12 (DSCP 12)    │ AF13 (DSCP 14)     │
│  (Low Pri)   │ ToS: 0x28          │ ToS: 0x30         │ ToS: 0x38          │
│  ────────────┼────────────────────┼───────────────────┼────────────────────│
│  Class 2     │ AF21 (DSCP 18)     │ AF22 (DSCP 20)    │ AF23 (DSCP 22)     │
│  (Med-Low)   │ ToS: 0x48          │ ToS: 0x50         │ ToS: 0x58          │
│  ────────────┼────────────────────┼───────────────────┼────────────────────│
│  Class 3     │ AF31 (DSCP 26)     │ AF32 (DSCP 28)    │ AF33 (DSCP 30)     │
│  (Med-High)  │ ToS: 0x68          │ ToS: 0x70         │ ToS: 0x78          │
│  ────────────┼────────────────────┼───────────────────┼────────────────────│
│  Class 4     │ AF41 (DSCP 34)     │ AF42 (DSCP 36)    │ AF43 (DSCP 38)     │
│  (High Pri)  │ ToS: 0x88          │ ToS: 0x90         │ ToS: 0x98          │
│                                                                              │
│  Note: Higher class = higher forwarding priority                             │
│        Lower drop precedence = less likely to drop during congestion        │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

## 4.3 Expedited Forwarding (EF)

### 4.3.1 EF Code Point

From `wlan_son_ald.h`:

```c
#define IPTOS_DSCP_EF           0xb8    /* DSCP 46 - Expedited Forwarding */
```

### 4.3.2 EF Characteristics

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                       Expedited Forwarding (EF) PHB                          │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  DSCP Value:    46                                                           │
│  Binary:        101110                                                       │
│  ToS Byte:      0xB8 (184)                                                  │
│  RFC:           2598                                                         │
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                    EF Traffic Characteristics                        │    │
│  ├─────────────────────────────────────────────────────────────────────┤    │
│  │  • Low latency (< 10ms one-way delay)                               │    │
│  │  • Low jitter (< 1ms variation)                                     │    │
│  │  • Low packet loss (< 0.1%)                                         │    │
│  │  • Guaranteed bandwidth                                              │    │
│  │  • Policed at ingress to prevent abuse                              │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  Typical Use Cases:                                                          │
│  • VoIP (Voice over IP)                                                     │
│  • Real-time gaming                                                          │
│  • Industrial control systems                                                │
│  • Video conferencing (audio portion)                                        │
│                                                                              │
│  Special Handling in ar_qos.c:                                              │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │  if ((pri >> 2) == 46) {                                              │  │
│  │    /* In case of value 46 (00101110), when we right shift it by 3   */  │
│  │    /* places it become 5 (101) which is not desirable.              */  │
│  │    /* So, instead of going for 5 right shift, we assign it value 6 */  │
│  │    wme_ac = WME_AC_VO;                                                │  │
│  │    pri = AR_WME_AC_TO_TID(wme_ac);                                    │  │
│  │  }                                                                     │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```


---

# 5. DSCP to TID Mapping

## 5.1 Understanding the Mapping

DSCP values (64 total) must be mapped to TID values (8 total) for WiFi transmission.

### 5.1.1 Default DSCP-TID Mapping Table

From `dp_rings_main.c` and `dp_main.c`:

```c
/* default_dscp_tid_map - Default DSCP-TID mapping
 *
 * DSCP        TID
 * 000000      0
 * 001000      1
 * 010000      2
 * 011000      3
 * 100000      4
 * 101000      5
 * 110000      6
 * 111000      7
 */
static uint8_t default_dscp_tid_map[DSCP_TID_MAP_MAX] = {
    0, 0, 0, 0, 0, 0, 0, 0,    /* DSCP  0- 7 -> TID 0 */
    1, 1, 1, 1, 1, 1, 1, 1,    /* DSCP  8-15 -> TID 1 */
    2, 2, 2, 2, 2, 2, 2, 2,    /* DSCP 16-23 -> TID 2 */
    3, 3, 3, 3, 3, 3, 3, 3,    /* DSCP 24-31 -> TID 3 */
    4, 4, 4, 4, 4, 4, 4, 4,    /* DSCP 32-39 -> TID 4 */
    5, 5, 5, 5, 5, 5, 5, 5,    /* DSCP 40-47 -> TID 5 */
    6, 6, 6, 6, 6, 6, 6, 6,    /* DSCP 48-55 -> TID 6 */
    7, 7, 7, 7, 7, 7, 7, 7,    /* DSCP 56-63 -> TID 7 */
};
```

### 5.1.2 DSCP to TID Visual Mapping

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                      DSCP to TID Default Mapping                             │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  DSCP Range    │ TID │ Access Category │ Priority Description               │
│  ──────────────┼─────┼─────────────────┼──────────────────────────────────── │
│   0 -  7       │  0  │    AC_BE        │ Best Effort                         │
│   8 - 15       │  1  │    AC_BK        │ Background                          │
│  16 - 23       │  2  │    AC_BK        │ Background (Spare)                  │
│  24 - 31       │  3  │    AC_BE        │ Best Effort (Excellent Effort)     │
│  32 - 39       │  4  │    AC_VI        │ Video                               │
│  40 - 47       │  5  │    AC_VI        │ Video (Includes EF=46)             │
│  48 - 55       │  6  │    AC_VO        │ Voice                               │
│  56 - 63       │  7  │    AC_VO        │ Voice (Network Control)            │
│                                                                              │
│  Note: EF (DSCP 46) is specially handled to map to Voice (AC_VO)            │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

## 5.2 Alternative DSCP-TID Mappings

### 5.2.1 Variant Mapping (from dp_rings_main.c)

Some driver versions use slightly different mappings:

```c
static uint8_t default_dscp_tid_map[DSCP_TID_MAP_MAX] = {
    0, 0, 0, 0, 0, 0, 0, 0,    /* DSCP  0- 7 */
    1, 1, 0, 1, 0, 1, 0, 1,    /* DSCP  8-15 (variant) */
    0, 2, 3, 2, 3, 2, 3, 2,    /* DSCP 16-23 (variant) */
    4, 3, 4, 3, 4, 3, 4, 3,    /* DSCP 24-31 (variant) */
    4, 4, 4, 4, 4, 4, 4, 4,    /* DSCP 32-39 */
    5, 5, 5, 5, 6, 5, 6, 5,    /* DSCP 40-47 (EF=46 -> TID 6) */
    7, 6, 6, 6, 6, 6, 6, 6,    /* DSCP 48-55 (variant) */
    7, 7, 7, 7, 7, 7, 7, 7,    /* DSCP 56-63 */
};
```

### 5.2.2 SAWF (Service-Aware WiFi) Mapping

From `dp_sawf.c`:

```c
uint32_t dscp_tid_map[WMI_HOST_DSCP_MAP_MAX] = {
    0, 0, 0, 0, 0, 0, 0, 0,
    1, 1, 1, 1, 1, 1, 1, 1,
    2, 2, 2, 2, 2, 2, 2, 2,
    3, 3, 3, 3, 3, 3, 3, 3,
    4, 4, 4, 4, 4, 4, 4, 4,
    5, 5, 5, 5, 5, 5, 5, 5,
    6, 6, 6, 6, 6, 6, 6, 6,
    7, 7, 7, 7, 7, 7, 7, 7,
};
```

## 5.3 TID to Access Category Mapping

### 5.3.1 Standard TID to AC Mapping

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        TID to Access Category Mapping                        │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  TID │ User Priority │ Access Category │ AC Index │ Description             │
│  ────┼───────────────┼─────────────────┼──────────┼──────────────────────── │
│   0  │      0        │     AC_BE       │    0     │ Best Effort             │
│   1  │      1        │     AC_BK       │    1     │ Background              │
│   2  │      2        │     AC_BK       │    1     │ Background (Spare)      │
│   3  │      3        │     AC_BE       │    0     │ Excellent Effort        │
│   4  │      4        │     AC_VI       │    2     │ Controlled Load         │
│   5  │      5        │     AC_VI       │    2     │ Video                   │
│   6  │      6        │     AC_VO       │    3     │ Voice                   │
│   7  │      7        │     AC_VO       │    3     │ Network Control         │
│                                                                              │
│  AC Priority Order (lowest to highest):                                      │
│  AC_BK (1) < AC_BE (0) < AC_VI (2) < AC_VO (3)                              │
│                                                                              │
│  Macro from ar_qos.c:                                                        │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │  #define AR_TID_TO_WME_AC(tid)                                        │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

## 5.4 HAL-Level DSCP-TID Mapping

### 5.4.1 Hardware DSCP-TID Map Registers

From `hal_8074v2_tx.h`:

```c
#define DSCP_TID_TABLE_SIZE 24
#define NUM_WORDS_PER_DSCP_TID_TABLE (DSCP_TID_TABLE_SIZE / 4)
#define HAL_TX_NUM_DSCP_REGISTER_SIZE 32

/**
 * hal_tx_set_dscp_tid_map_8074v2() - Configure default DSCP to TID map table
 * @soc: HAL SoC context
 * @map: DSCP-TID mapping table
 * @id: mapping table ID - 0,1
 *
 * DSCP are mapped to 8 TID values using TID values programmed
 * in two set of mapping registers DSCP_TID1_MAP_<0 to 6> (id = 0)
 * and DSCP_TID2_MAP_<0 to 6> (id = 1)
 * Each mapping register has TID mapping for 10 DSCP values
 *
 * Return: none
 */
static void hal_tx_set_dscp_tid_map_8074v2(struct hal_soc *soc,
                                           uint8_t *map,
                                           uint8_t id);
```

### 5.4.2 Multiple DSCP-TID Map Support

From `hal_6750_tx.h`:

```c
/**
 * hal_tx_set_dscp_tid_map_6750() - Configure default DSCP to TID map table
 * @hal_soc: HAL SoC context
 * @map: DSCP-TID mapping table
 * @id: mapping table ID - 0-31
 *
 * DSCP are mapped to 8 TID values using TID values programmed
 * in any of the 32 DSCP_TID_MAPS (id = 0-31).
 *
 * Return: none
 */
static void hal_tx_set_dscp_tid_map_6750(struct hal_soc *hal_soc,
                                          uint8_t *map, uint8_t id);
```

---

# 6. DSCP in WiFi (802.11e/WMM)

## 6.1 WiFi Multimedia (WMM) Overview

### 6.1.1 WMM Access Categories

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    WiFi Multimedia (WMM) Access Categories                   │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                          WMM Queue Structure                         │    │
│  │                                                                      │    │
│  │   High Priority                                                      │    │
│  │        ▲                                                             │    │
│  │        │   ┌─────────────────────────────────────────────────────┐  │    │
│  │        │   │ AC_VO (Voice)          - TID 6, 7                   │  │    │
│  │        │   │ • Highest priority                                  │  │    │
│  │        │   │ • Shortest AIFS, smallest CWmin                     │  │    │
│  │        │   │ • DSCP: 46-55 (EF, CS6, CS7)                        │  │    │
│  │        │   └─────────────────────────────────────────────────────┘  │    │
│  │        │   ┌─────────────────────────────────────────────────────┐  │    │
│  │        │   │ AC_VI (Video)          - TID 4, 5                   │  │    │
│  │        │   │ • Second highest priority                           │  │    │
│  │        │   │ • Short AIFS, small CWmin                           │  │    │
│  │        │   │ • DSCP: 32-45 (AF4x, CS4, CS5)                      │  │    │
│  │        │   └─────────────────────────────────────────────────────┘  │    │
│  │        │   ┌─────────────────────────────────────────────────────┐  │    │
│  │        │   │ AC_BE (Best Effort)    - TID 0, 3                   │  │    │
│  │        │   │ • Default traffic class                             │  │    │
│  │        │   │ • Standard AIFS, standard CWmin                     │  │    │
│  │        │   │ • DSCP: 0-7, 24-31 (CS0, AF2x, AF3x, CS3)          │  │    │
│  │        │   └─────────────────────────────────────────────────────┘  │    │
│  │        │   ┌─────────────────────────────────────────────────────┐  │    │
│  │        ▼   │ AC_BK (Background)     - TID 1, 2                   │  │    │
│  │            │ • Lowest priority                                   │  │    │
│  │            │ • Longest AIFS, largest CWmin                       │  │    │
│  │            │ • DSCP: 8-23 (CS1, CS2, AF1x)                       │  │    │
│  │   Low Priority                                                    │  │    │
│  │            └─────────────────────────────────────────────────────┘  │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 6.1.2 802.11e EDCA Parameters

| Access Category | CWmin | CWmax | AIFSN | TXOP Limit (802.11b) | TXOP Limit (802.11a/g/n) |
|-----------------|-------|-------|-------|---------------------|-------------------------|
| AC_BK | aCWmin | aCWmax | 7 | 0 | 0 |
| AC_BE | aCWmin | aCWmax | 3 | 0 | 0 |
| AC_VI | (aCWmin+1)/2 - 1 | aCWmin | 2 | 6.016 ms | 3.008 ms |
| AC_VO | (aCWmin+1)/4 - 1 | (aCWmin+1)/2 - 1 | 2 | 3.264 ms | 1.504 ms |

## 6.2 DSCP to WMM Mapping Flow

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                      DSCP to WMM Mapping Data Flow                           │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│   ┌────────────────┐                                                        │
│   │ IP Packet      │                                                        │
│   │ with DSCP      │                                                        │
│   └───────┬────────┘                                                        │
│           │                                                                  │
│           ▼                                                                  │
│   ┌────────────────────────────────────────────────┐                        │
│   │ Step 1: Extract DSCP from IP Header            │                        │
│   │                                                 │                        │
│   │ dscp = (ip->tos & 0xFC) >> 2;                  │                        │
│   └───────────────────┬────────────────────────────┘                        │
│                       │                                                      │
│                       ▼                                                      │
│   ┌────────────────────────────────────────────────┐                        │
│   │ Step 2: Look up TID in DSCP-TID Map            │                        │
│   │                                                 │                        │
│   │ tid = dscp_tid_map[dscp];                      │                        │
│   │ (Or check DSCP exceptions first)               │                        │
│   └───────────────────┬────────────────────────────┘                        │
│                       │                                                      │
│                       ▼                                                      │
│   ┌────────────────────────────────────────────────┐                        │
│   │ Step 3: Map TID to Access Category             │                        │
│   │                                                 │                        │
│   │ ac = AR_TID_TO_WME_AC(tid);                    │                        │
│   │ TID 0,3 -> AC_BE; TID 1,2 -> AC_BK;            │                        │
│   │ TID 4,5 -> AC_VI; TID 6,7 -> AC_VO             │                        │
│   └───────────────────┬────────────────────────────┘                        │
│                       │                                                      │
│                       ▼                                                      │
│   ┌────────────────────────────────────────────────┐                        │
│   │ Step 4: Apply Priority Ceiling (if configured) │                        │
│   │                                                 │                        │
│   │ AR_CEIL_QOS_PRIO(vdev, wme_ac, tid);           │                        │
│   └───────────────────┬────────────────────────────┘                        │
│                       │                                                      │
│                       ▼                                                      │
│   ┌────────────────────────────────────────────────┐                        │
│   │ Step 5: Set Priority and Queue Packet          │                        │
│   │                                                 │                        │
│   │ vdrv_dp_if_wbuf_set_tid(skb, tid);             │                        │
│   │ skb->priority = ac;                            │                        │
│   └────────────────────────────────────────────────┘                        │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```


---

# 7. DSCP vs TOS

## 7.1 Key Differences

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          DSCP vs TOS Comparison                              │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  Feature          │       ToS (Legacy)       │       DSCP (Modern)          │
│  ─────────────────┼──────────────────────────┼──────────────────────────────│
│  RFC              │       RFC 791 (1981)     │       RFC 2474 (1998)        │
│  Bits Used        │       8 bits             │       6 bits + 2 ECN         │
│  Values           │       8 precedence       │       64 code points         │
│  Granularity      │       Coarse             │       Fine-grained           │
│  Standard PHBs    │       None               │       EF, AF, CS, BE         │
│  Extraction       │       (tos >> 5)         │       (tos >> 2) & 0x3F      │
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                    Byte Layout Comparison                            │    │
│  ├─────────────────────────────────────────────────────────────────────┤    │
│  │  ToS:   │ P │ P │ P │ D │ T │ R │ 0 │ 0 │  (P=Precedence, D/T/R=flags) │
│  │  DSCP:  │ D │ D │ D │ D │ D │ D │ E │ E │  (D=DSCP, E=ECN)             │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

## 7.2 TOS-Based Mapping in Arista AP

### 7.2.1 TOS Downstream Mapping Function

From `ar_qos.c`:

```c
AR_STATUS ar_qos_dp_set_map_dstream_tos(struct sk_buff* skb,
                                        struct ar_dp_vdev_s* vdev,
                                        int* v_wme_ac, int* v_pri)
{
    struct ether_header* eh = (struct ether_header*)skb_mac_header(skb);
    size_t ip_ether_hdr_len = sizeof(struct iphdr) + sizeof(struct ether_header);
    size_t ipv6_ether_hdr_len = sizeof(struct ipv6hdr) + sizeof(struct ether_header);
    int pri = *v_pri, linear_len;

    if (eh->ether_type == __constant_htons(ETHERTYPE_IP) &&
        skb->len >= ip_ether_hdr_len) {
        const struct iphdr* ip = (struct iphdr*)skb_network_header(skb);
        linear_len = sizeof(struct ether_header) + sizeof(struct iphdr);
        if (!pskb_may_pull(skb, linear_len)) return AR_STATUS_EARLY_RETURN;
        ip = (struct iphdr*)skb_network_header(skb);

        // IP frame: exclude ECN bits 0-1 and map DSCP bits 2-7 from TOS byte.
        // Then right shift by 5 to get TID (0-7)
        pri = (ip->tos & (~INET_ECN_MASK)) >> IP_PRI_SHIFT;  // IP_PRI_SHIFT = 5
    }

    *v_wme_ac = AR_TID_TO_WME_AC(pri);
    AR_CEIL_QOS_PRIO(vdev, *v_wme_ac, pri);
    vdrv_dp_if_wbuf_set_tid(skb, pri);
    skb->priority = *v_wme_ac;
    *v_pri = pri;
    return AR_STATUS_SUCCESS;
}
```

### 7.2.2 TOS to TID Calculation

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        TOS to TID Conversion                                 │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  TOS Byte:   ┌───┬───┬───┬───┬───┬───┬───┬───┐                             │
│              │ 7 │ 6 │ 5 │ 4 │ 3 │ 2 │ 1 │ 0 │                             │
│              └───┴───┴───┴───┴───┴───┴───┴───┘                             │
│               │       │                   │                                  │
│               └───────┘                   │                                  │
│               Precedence                 ECN                                 │
│               (3 bits)                   (2 bits)                            │
│                                                                              │
│  Calculation:                                                                │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │  1. Mask out ECN:  tos & 0xFC  (keep bits 2-7)                        │  │
│  │  2. Right shift:   >> 5        (get bits 5-7 as value 0-7)            │  │
│  │  Result: TID = (tos & 0xFC) >> 5                                       │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                                                                              │
│  Examples:                                                                   │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │  ToS = 0xE0 (11100000) -> TID = (0xE0 & 0xFC) >> 5 = 7              │    │
│  │  ToS = 0xC0 (11000000) -> TID = (0xC0 & 0xFC) >> 5 = 6              │    │
│  │  ToS = 0xA0 (10100000) -> TID = (0xA0 & 0xFC) >> 5 = 5              │    │
│  │  ToS = 0x80 (10000000) -> TID = (0x80 & 0xFC) >> 5 = 4              │    │
│  │  ToS = 0x60 (01100000) -> TID = (0x60 & 0xFC) >> 5 = 3              │    │
│  │  ToS = 0x40 (01000000) -> TID = (0x40 & 0xFC) >> 5 = 2              │    │
│  │  ToS = 0x20 (00100000) -> TID = (0x20 & 0xFC) >> 5 = 1              │    │
│  │  ToS = 0x00 (00000000) -> TID = (0x00 & 0xFC) >> 5 = 0              │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

# 8. DSCP to 802.1p (PCP) Mapping

## 8.1 802.1p Priority Code Point (PCP)

### 8.1.1 802.1p to WMM Mapping

From `ar_qos.c`:

```c
/* v_wme_ac and v_pri are from VLAN header, convert it to appropriate WMM value
**
** 802.1P            :    WMM
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
```

### 8.1.2 802.1p to WMM Mapping Table

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                      802.1p to WMM Priority Mapping                          │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  802.1p (PCP) │ Name                  │ TID │ Access Category │ WMM Name    │
│  ─────────────┼───────────────────────┼─────┼─────────────────┼─────────────│
│       0       │ Background            │  1  │     AC_BK       │ Background  │
│       1       │ Best Effort           │  0  │     AC_BE       │ Best Effort │
│       2       │ Excellent Effort      │  3  │     AC_BE       │ Best Effort │
│       3       │ Critical Applications │  4  │     AC_VI       │ Video       │
│       4       │ Video                 │  5  │     AC_VI       │ Video       │
│       5       │ Voice                 │  6  │     AC_VO       │ Voice       │
│       6       │ Internetwork Control  │  7  │     AC_VO       │ Voice       │
│       7       │ Network Control       │  7  │     AC_VO       │ Voice       │
│                                                                              │
│  Note: This mapping differs from direct DSCP-TID mapping!                   │
│        802.1p 0 maps to TID 1 (not 0), and 802.1p 1 maps to TID 0           │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 8.1.3 802.1p Downstream Mapping Code

From `ar_qos.c`:

```c
void ar_qos_dp_set_map_dstream_8021p(struct sk_buff* skb, struct ar_dp_vdev_s* vdev,
                                      int* v_wme_ac, int* v_pri)
{
    int tid;
    int pri = *v_pri;
    struct vlan_ethhdr* veth = (struct vlan_ethhdr*)skb->data;

    // Extract priority from VLAN tag
    if (unlikely(ar_os_skb_vlan_tag_present(skb))) {
        uint32_t tag = ar_os_skb_vlan_tag_get(skb);
        pri = (tag >> VLAN_PRI_SHIFT) & VLAN_PRI_MASK;
    } else {
        if (veth->h_vlan_proto == __constant_htons(ETH_P_8021Q)) {
            pri = (veth->h_vlan_TCI >> VLAN_PRI_SHIFT) & VLAN_PRI_MASK;
        }
    }

    // Map 802.1p to TID
    switch (pri) {
        case 0: tid = 1; break;  // Background -> BK
        case 1: tid = 0; break;  // Best effort -> BE
        case 2: tid = 3; break;  // Excellent effort -> BE
        case 3: tid = 4; break;  // Critical apps -> VI
        case 4: tid = 5; break;  // Video -> VI
        case 5: tid = 6; break;  // Voice -> VO
        case 6:
        case 7: tid = 7; break;  // Network control -> VO
        default: tid = 0; break;
    }

    *v_wme_ac = AR_TID_TO_WME_AC(tid);
    AR_CEIL_QOS_PRIO(vdev, *v_wme_ac, tid);
    vdrv_dp_if_wbuf_set_tid(skb, tid);
    skb->priority = *v_wme_ac;
    *v_pri = tid;
}
```

## 8.2 Default PCP-TID Mapping

From `dp_rings_main.c`:

```c
/* default_pcp_tid_map - Default PCP-TID mapping
 *
 * PCP     TID
 * 000      0
 * 001      1
 * 010      2
 * 011      3
 * 100      4
 * 101      5
 * 110      6
 * 111      7
 */
static uint8_t default_pcp_tid_map[PCP_TID_MAP_MAX] = {
    0, 1, 2, 3, 4, 5, 6, 7,
};
```

---

# 9. DSCP Configuration in Arista AP

## 9.1 QoS Configuration Parameters

### 9.1.1 Configuration Data Model

From `SsidConfig.tac`:

```tac
/* Qos */
QosConfig : Tac::Type() : Tac::Nominal {
   ssidPriority : U8;           // 0-3 (Best Effort, Background, Video, Voice)
   priorityType : U8;           // 0=Ceiling, 1=Fixed
   downstreamMap : U8;          // 0=None, 1=DSCP, 2=TOS
   upstreamMark8021p : U8;      // 0=Disabled, 1=Enabled
   upstreamMarkDscpTos : U8;    // 0=Disabled, 1=Enabled
   wmmEnforcePolicyEnable : bool;
   wmmEnable : bool;
   // ... additional rate parameters
}
```

### 9.1.2 QoS Configuration Map

From `ssid_qos.go`:

```go
var qosConfigMap = map[string]string{
    "SsidPriority":           "QOS_SSID_PRIORITY",
    "PriorityType":           "QOS_PRIORITY_TYPE",
    "DownstreamMap":          "QOS_DOWNSTR_MAP",
    "UpstreamMark8021p":      "QOS_UPSTR_MARK_802_1p",
    "UpstreamMarkDscpTos":    "QOS_UPSTR_MARK_DSCP_TOS",
    "WmmEnforcePolicyEnable": "WMM_ENFORCE_POLICY_ENABLE",
    "WmmEnable":              "WMM_ENABLE",
    // ... additional mappings
}
```

## 9.2 QoS Flag Encoding

### 9.2.1 QoS Flag Bit Layout

From `ssid_qos_qca.go`:

```go
/*##############
# QoS Flags
# 7 -------------------- 0
# 0-1   :       QoS Priority
# 2     :       QoS Priority Type (Fixed / Ceil)
# 3-4   :       Downstream Mapping
# 5     :       Enable 802.1p Upstream Marking
# 6     :       Enable DSCP Upstream Marking
# 7     :       Enable TOS Upstream Marking
##############*/
```

### 9.2.2 QoS Flag Calculation

From `ssid_qos_qca.go`:

```go
func updateQosParams(config wificonfig.QosConfig, profileConfMap *sync.Map) {
    profileConfMap.Swap("QOS_SSID_PRIORITY", strconv.Itoa(int(config.SsidPriority)))
    profileConfMap.Swap("QOS_PRIORITY_TYPE", strconv.Itoa(int(config.PriorityType)))
    profileConfMap.Swap("QOS_DOWNSTR_MAP", strconv.Itoa(int(config.DownstreamMap)))
    profileConfMap.Swap("QOS_UPSTR_MARK_802_1p", strconv.Itoa(int(config.UpstreamMark8021p)))
    profileConfMap.Swap("QOS_UPSTR_MARK_DSCP_TOS", strconv.Itoa(int(config.UpstreamMarkDscpTos)))
}
```

### 9.2.3 QoS Flag Parameter Encoding

```go
var qosFlagParam uint

// SSID Priority encoding (bits 0-1)
switch config.SsidPriority {
    case 0:  qosFlagParam = 3    // Best Effort
    case 1:  qosFlagParam = 2    // Background
    case 2:  qosFlagParam = 0    // Video
    default: qosFlagParam = 1    // Voice
}

// Add Priority Type (bit 2)
qosFlagParam += 4 * uint(config.PriorityType)

// Add Downstream Map (bits 3-4)
qosFlagParam += 8 * uint(config.DownstreamMap)

// Add Upstream 802.1p marking (bit 5)
qosFlagParam += 32 * uint(config.UpstreamMark8021p)

// Add Upstream DSCP marking (bit 6)
qosFlagParam += 64 * uint(config.UpstreamMarkDscpTos)
```

## 9.3 Configuration Options Table

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    QoS Configuration Options Reference                       │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  Parameter              │ Values │ Description                              │
│  ───────────────────────┼────────┼──────────────────────────────────────────│
│  ssidPriority           │ 0      │ Best Effort (default)                    │
│                         │ 1      │ Background                               │
│                         │ 2      │ Video                                    │
│                         │ 3      │ Voice                                    │
│  ───────────────────────┼────────┼──────────────────────────────────────────│
│  priorityType           │ 0      │ Ceiling (cap at configured priority)     │
│                         │ 1      │ Fixed (always use configured priority)   │
│  ───────────────────────┼────────┼──────────────────────────────────────────│
│  downstreamMap          │ 0      │ Disabled / None                          │
│                         │ 1      │ DSCP-based mapping                       │
│                         │ 2      │ TOS-based mapping                        │
│  ───────────────────────┼────────┼──────────────────────────────────────────│
│  upstreamMark8021p      │ 0      │ Disabled                                 │
│                         │ 1      │ Enable 802.1p upstream marking           │
│  ───────────────────────┼────────┼──────────────────────────────────────────│
│  upstreamMarkDscpTos    │ 0      │ Disabled                                 │
│                         │ 1      │ Enable DSCP/TOS upstream marking         │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```



---

# 10. Driver-Level DSCP Implementation

## 10.1 QCA WiFi Driver DSCP Handling

### 10.1.1 Data Path DSCP Processing

From `dp_main.c`:

```c
/**
 * dp_set_dscp_tid_map() - Set DSCP to TID map
 * @soc_hdl: CDP SOC handle
 * @pdev_id: PDEV ID
 * @map_id: Map ID
 * @tos: TOS value
 * @tid: TID value
 *
 * Configure the DSCP to TID mapping in the hardware
 *
 * Return: QDF_STATUS
 */
QDF_STATUS dp_set_dscp_tid_map(struct cdp_soc_t *soc_hdl,
                               uint8_t pdev_id,
                               uint8_t map_id,
                               uint8_t tos, uint8_t tid)
{
    struct dp_soc *soc = cdp_soc_t_to_dp_soc(soc_hdl);
    struct dp_pdev *pdev = dp_get_pdev_from_soc_pdev_id_wifi3(soc, pdev_id);

    if (!pdev)
        return QDF_STATUS_E_FAILURE;

    pdev->dscp_tid_map[map_id][tos] = tid;

    hal_tx_set_dscp_tid_map(soc->hal_soc,
                            pdev->dscp_tid_map[map_id],
                            map_id);

    return QDF_STATUS_SUCCESS;
}
```

### 10.1.2 DSCP-TID Map Initialization

```c
/**
 * dp_dscp_tid_map_setup() - Initialize DSCP-TID maps
 * @pdev: Data path PDEV handle
 *
 * Initialize all DSCP to TID maps with default values
 */
static inline void dp_dscp_tid_map_setup(struct dp_pdev *pdev)
{
    uint8_t map_id;
    struct dp_soc *soc = pdev->soc;

    if (!wlan_cfg_get_dp_soc_nss_cfg(soc->wlan_cfg_ctx)) {
        for (map_id = 0; map_id < DP_MAX_TID_MAPS; map_id++) {
            qdf_mem_copy(pdev->dscp_tid_map[map_id],
                        default_dscp_tid_map,
                        sizeof(default_dscp_tid_map));
            hal_tx_set_dscp_tid_map(soc->hal_soc,
                                    pdev->dscp_tid_map[map_id],
                                    map_id);
        }
    }
}
```

## 10.2 Arista Driver DSCP Functions

### 10.2.1 DSCP Downstream Mapping

From `ar_qos.c`:

```c
AR_STATUS ar_qos_dp_set_map_dstream_dscp(struct sk_buff* skb,
                                          struct ar_dp_vdev_s* vdev,
                                          int* v_wme_ac, int* v_pri)
{
    struct ether_header* eh = (struct ether_header*)skb_mac_header(skb);
    size_t ip_ether_hdr_len = sizeof(struct iphdr) + sizeof(struct ether_header);
    size_t ipv6_ether_hdr_len = sizeof(struct ipv6hdr) + sizeof(struct ether_header);
    int pri = *v_pri, linear_len;
    int wme_ac;

    if (eh->ether_type == __constant_htons(ETHERTYPE_IP) &&
        skb->len >= ip_ether_hdr_len) {
        const struct iphdr* ip = (struct iphdr*)skb_network_header(skb);
        linear_len = sizeof(struct ether_header) + sizeof(struct iphdr);
        if (!pskb_may_pull(skb, linear_len)) return AR_STATUS_EARLY_RETURN;
        ip = (struct iphdr*)skb_network_header(skb);

        // IP frame: exclude ECN bits 0-1 and map DSCP bits 2-7 from TOS byte.
        pri = ip->tos & (~INET_ECN_MASK);  // Keep bits 2-7

        // Special handling for EF (DSCP 46) - ensure Voice priority
        if ((pri >> 2) == 46) {
            wme_ac = WME_AC_VO;
            pri = AR_WME_AC_TO_TID(wme_ac);
        } else {
            pri = pri >> 2;  // Right shift to get DSCP value
            pri = ar_qos_dscp_tid_map[pri];  // Look up TID
            wme_ac = AR_TID_TO_WME_AC(pri);
        }
    }

    *v_wme_ac = wme_ac;
    AR_CEIL_QOS_PRIO(vdev, *v_wme_ac, pri);
    vdrv_dp_if_wbuf_set_tid(skb, pri);
    skb->priority = *v_wme_ac;
    *v_pri = pri;
    return AR_STATUS_SUCCESS;
}
```

## 10.3 Hardware Register Programming

### 10.3.1 HAL DSCP-TID Map Programming

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    HAL DSCP-TID Register Programming                         │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                   DSCP_TID_MAP Register Layout                       │    │
│  │                                                                      │    │
│  │  Register: DSCP_TID1_MAP_0 through DSCP_TID1_MAP_6                  │    │
│  │                                                                      │    │
│  │  Each register holds TID values for 10 DSCP values                  │    │
│  │  (3 bits per TID, 10 TIDs = 30 bits used per register)              │    │
│  │                                                                      │    │
│  │  ┌─────────────────────────────────────────────────────────────┐    │    │
│  │  │ Bit 29-27 │ Bit 26-24 │ ... │ Bit 5-3 │ Bit 2-0 │           │    │    │
│  │  │  DSCP 9   │  DSCP 8   │ ... │ DSCP 1  │ DSCP 0  │           │    │    │
│  │  └─────────────────────────────────────────────────────────────┘    │    │
│  │                                                                      │    │
│  │  Total: 7 registers × 10 DSCP values = 70 entries                   │    │
│  │         (Only 64 DSCP values used: 0-63)                            │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

# 11. DSCP Exception Handling

## 11.1 Hotspot 2.0 QoS Map

### 11.1.1 QoS Map Configuration

From `ar_qos.c`:

```c
void ar_qos_dp_set_hs20_qos_map(struct ar_dp_vdev_s* vdev,
                                 struct ar_hs20_qos_map* qos_map)
{
    int i, j;
    int up, start, end;

    // Initialize with default mapping
    for (i = 0; i < 64; i++) {
        vdev->dscp_tid_map[i] = i >> 3;  // Default: DSCP/8 = TID
    }

    // Apply DSCP range mappings (from QoS Map element)
    for (i = 0; i < 8; i++) {
        start = qos_map->up[i].low;
        end = qos_map->up[i].high;
        up = i;

        if (start <= 63 && end <= 63 && start <= end) {
            for (j = start; j <= end; j++) {
                vdev->dscp_tid_map[j] = up;
            }
        }
    }

    // Apply DSCP exceptions (override range mappings)
    for (i = 0; i < qos_map->num_dscp_except; i++) {
        int dscp = qos_map->dscp_exception[i].dscp;
        up = qos_map->dscp_exception[i].up;

        if (dscp <= 63 && up <= 7) {
            vdev->dscp_tid_map[dscp] = up;
        }
    }
}
```

### 11.1.2 DSCP Exception Structure

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                       DSCP Exception Processing Flow                         │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌─────────────────┐                                                        │
│  │ Incoming Packet │                                                        │
│  │ with DSCP Value │                                                        │
│  └────────┬────────┘                                                        │
│           │                                                                  │
│           ▼                                                                  │
│  ┌─────────────────────────────────────────────────────┐                    │
│  │ Step 1: Check DSCP Exception List                   │                    │
│  │                                                      │                    │
│  │ if (dscp in exception_list):                        │                    │
│  │     tid = exception_map[dscp]                       │                    │
│  │     goto apply_priority                              │                    │
│  └─────────────────────┬───────────────────────────────┘                    │
│                        │                                                     │
│                        ▼                                                     │
│  ┌─────────────────────────────────────────────────────┐                    │
│  │ Step 2: Check DSCP Range (UP 0-7)                   │                    │
│  │                                                      │                    │
│  │ for up in 0..7:                                     │                    │
│  │     if (qos_map.up[up].low <= dscp <= high):        │                    │
│  │         tid = up                                     │                    │
│  │         goto apply_priority                          │                    │
│  └─────────────────────┬───────────────────────────────┘                    │
│                        │                                                     │
│                        ▼                                                     │
│  ┌─────────────────────────────────────────────────────┐                    │
│  │ Step 3: Apply Default Mapping                       │                    │
│  │                                                      │                    │
│  │ tid = default_dscp_tid_map[dscp]                    │                    │
│  └─────────────────────┬───────────────────────────────┘                    │
│                        │                                                     │
│                        ▼                                                     │
│  ┌─────────────────────────────────────────────────────┐                    │
│  │ Step 4: Apply Priority Ceiling (if configured)      │                    │
│  │                                                      │                    │
│  │ AR_CEIL_QOS_PRIO(vdev, wme_ac, tid)                 │                    │
│  └─────────────────────────────────────────────────────┘                    │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

## 11.2 Special DSCP Values

### 11.2.1 EF (DSCP 46) Special Handling

```c
// From ar_qos.c - Special handling for Expedited Forwarding
if ((pri >> 2) == 46) {  // DSCP 46 = EF
    wme_ac = WME_AC_VO;  // Force Voice priority
    pri = AR_WME_AC_TO_TID(wme_ac);  // TID 6 or 7
}
```

### 11.2.2 Voice Signaling (DSCP 44) Handling

```c
// DSCP 44 (Voice Signaling) typically maps to Voice
// Used for SIP, H.323, and other VoIP signaling protocols
if (dscp == 44) {
    wme_ac = WME_AC_VO;
}
```

---

# 12. QoS Map Structure

## 12.1 IEEE 802.11 QoS Map Element

### 12.1.1 QoS Map Data Structure

From `ieee80211_defines.h`:

```c
#define IEEE80211_MAX_QOS_UP_RANGE      8
#define IEEE80211_MAX_QOS_DSCP_EXCEPT   21

struct ieee80211_dscp_range {
    u_int8_t low;    // Low DSCP value for this UP
    u_int8_t high;   // High DSCP value for this UP
};

struct ieee80211_dscp_exception {
    u_int8_t dscp;   // DSCP value
    u_int8_t up;     // User Priority (0-7)
};

struct ieee80211_qos_map {
    struct ieee80211_dscp_range up[IEEE80211_MAX_QOS_UP_RANGE];  // 8 UP ranges
    u_int16_t valid;                                               // Validity bitmap
    u_int16_t num_dscp_except;                                    // Number of exceptions
    struct ieee80211_dscp_exception dscp_exception[IEEE80211_MAX_QOS_DSCP_EXCEPT];
};
```

### 12.1.2 QoS Map Visual Layout

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        IEEE 802.11 QoS Map Element                           │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                         QoS Map Element Format                       │    │
│  ├─────────────────────────────────────────────────────────────────────┤    │
│  │                                                                      │    │
│  │  ┌──────────┬──────────┬──────────┬──────────────────────────────┐  │    │
│  │  │ Element  │  Length  │  DSCP    │      DSCP Range               │  │    │
│  │  │   ID     │          │ Except.  │      (8 UP × 2 bytes)         │  │    │
│  │  ├──────────┼──────────┼──────────┼──────────────────────────────┤  │    │
│  │  │   110    │ Variable │ 0-21 ×   │  UP0 Low/High ... UP7 Low/High│  │    │
│  │  │          │          │ 2 bytes  │                               │  │    │
│  │  └──────────┴──────────┴──────────┴──────────────────────────────┘  │    │
│  │                                                                      │    │
│  │  DSCP Exception (variable, 0-21 pairs):                             │    │
│  │  ┌──────────────────────────────────────────────────────────────┐   │    │
│  │  │ DSCP Value │ User Priority │ DSCP Value │ User Priority │ ...│   │    │
│  │  │  (1 byte)  │   (1 byte)    │  (1 byte)  │   (1 byte)    │    │   │    │
│  │  └──────────────────────────────────────────────────────────────┘   │    │
│  │                                                                      │    │
│  │  DSCP Range (fixed, 16 bytes for 8 UPs):                            │    │
│  │  ┌────────────────────────────────────────────────────────────────┐ │    │
│  │  │UP0 Low│UP0 High│UP1 Low│UP1 High│...│UP7 Low│UP7 High│        │ │    │
│  │  └────────────────────────────────────────────────────────────────┘ │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

## 12.2 QoS Map Configuration Examples

### 12.2.1 Standard Enterprise QoS Map

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                      Enterprise QoS Map Configuration                        │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  UP │ DSCP Range │ Traffic Type           │ Description                     │
│  ───┼────────────┼────────────────────────┼──────────────────────────────── │
│   0 │   0 - 7    │ Best Effort            │ Default traffic                 │
│   1 │   8 - 15   │ Background             │ Bulk data, backups              │
│   2 │  16 - 23   │ Spare                  │ Reserved                        │
│   3 │  24 - 31   │ Excellent Effort       │ Critical data                   │
│   4 │  32 - 39   │ Controlled Load        │ Streaming video                 │
│   5 │  40 - 47   │ Video                  │ Interactive video, conferencing │
│   6 │  48 - 55   │ Voice                  │ VoIP traffic                    │
│   7 │  56 - 63   │ Network Control        │ Network management              │
│                                                                              │
│  DSCP Exceptions:                                                            │
│  ───────────────────────────────────────────────────────────────────────────│
│  DSCP 46 (EF)  → UP 6 (Voice)     : VoIP media streams                      │
│  DSCP 44 (CS5) → UP 6 (Voice)     : Voice signaling (SIP)                   │
│  DSCP 34 (AF41)→ UP 5 (Video)     : Video conferencing                      │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

# 13. Upstream DSCP Marking

## 13.1 DSCP/TOS Upstream Marking

### 13.1.1 Upstream Marking Configuration

From `ssid_qos_qca.go`:

```go
// Enable DSCP upstream marking (bit 6 in QoS flags)
if config.UpstreamMarkDscpTos == 1 {
    qosFlagParam += 64  // Set bit 6
}

// Enable TOS upstream marking (bit 7 in QoS flags)
if config.UpstreamMarkTos == 1 {
    qosFlagParam += 128  // Set bit 7
}
```

### 13.1.2 Upstream Marking Flow

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        Upstream DSCP Marking Flow                            │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌────────────────┐                                                         │
│  │ Client Transmit│                                                         │
│  │ (802.11 Frame) │                                                         │
│  └───────┬────────┘                                                         │
│          │                                                                   │
│          ▼                                                                   │
│  ┌──────────────────────────────────────────────┐                           │
│  │ Step 1: Extract WMM Priority from 802.11     │                           │
│  │                                               │                           │
│  │ tid = QoS_Control.TID                        │                           │
│  │ ac = TID_TO_AC(tid)                          │                           │
│  └──────────────────┬───────────────────────────┘                           │
│                     │                                                        │
│                     ▼                                                        │
│  ┌──────────────────────────────────────────────┐                           │
│  │ Step 2: Check Upstream Marking Config        │                           │
│  │                                               │                           │
│  │ if (upstreamMarkDscpTos enabled):            │                           │
│  │     goto mark_dscp                            │                           │
│  │ else:                                         │                           │
│  │     preserve original DSCP                    │                           │
│  └──────────────────┬───────────────────────────┘                           │
│                     │                                                        │
│                     ▼                                                        │
│  ┌──────────────────────────────────────────────┐                           │
│  │ Step 3: Mark DSCP in IP Header               │                           │
│  │                                               │                           │
│  │ dscp = ac_to_dscp_map[ac]                    │                           │
│  │ ip->tos = (dscp << 2) | (ip->tos & 0x03)     │                           │
│  └──────────────────────────────────────────────┘                           │
│                                                                              │
│  AC to DSCP Mapping:                                                         │
│  ┌─────────────────────────────────────────────────┐                        │
│  │ AC_BE (0) → DSCP 0  (Best Effort)              │                        │
│  │ AC_BK (1) → DSCP 8  (CS1)                      │                        │
│  │ AC_VI (2) → DSCP 32 (CS4)                      │                        │
│  │ AC_VO (3) → DSCP 46 (EF)                       │                        │
│  └─────────────────────────────────────────────────┘                        │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

## 13.2 802.1p Upstream Marking

### 13.2.1 VLAN Priority Marking

```go
// Enable 802.1p upstream marking (bit 5 in QoS flags)
if config.UpstreamMark8021p == 1 {
    qosFlagParam += 32  // Set bit 5
}
```

### 13.2.2 802.1p Marking Process

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                       802.1p Upstream Marking                                │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  Original Frame:                                                             │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │ DA │ SA │ EtherType │ Payload                                        │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                                                                              │
│  After 802.1Q Tagging:                                                       │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │ DA │ SA │ 0x8100 │ TCI │ EtherType │ Payload                         │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                 │                                                            │
│                 ▼                                                            │
│  ┌─────────────────────────────────────────────┐                            │
│  │           TCI (Tag Control Information)      │                            │
│  │  ┌─────────────────────────────────────────┐│                            │
│  │  │ PCP (3 bits) │ DEI │ VID (12 bits)     ││                            │
│  │  │   Priority   │     │   VLAN ID         ││                            │
│  │  └─────────────────────────────────────────┘│                            │
│  │                                              │                            │
│  │  PCP Values (from WMM):                     │                            │
│  │  AC_VO → PCP 6 (Voice)                      │                            │
│  │  AC_VI → PCP 5 (Video)                      │                            │
│  │  AC_BE → PCP 0 (Best Effort)                │                            │
│  │  AC_BK → PCP 1 (Background)                 │                            │
│  └─────────────────────────────────────────────┘                            │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```


---

# 14. Downstream DSCP Mapping

## 14.1 Downstream Mapping Options

### 14.1.1 Mapping Types

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                      Downstream Mapping Configuration                        │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  downstreamMap │ Mode       │ Description                                   │
│  ──────────────┼────────────┼───────────────────────────────────────────────│
│       0        │ None       │ No downstream mapping; use default priority   │
│       1        │ DSCP       │ Use DSCP field (6 bits) for priority mapping  │
│       2        │ TOS        │ Use TOS precedence (3 bits) for priority      │
│       3        │ 802.1p     │ Use VLAN PCP for priority mapping             │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 14.1.2 Downstream Mapping Selection

From `ar_qos.c`:

```c
AR_STATUS ar_qos_dp_set_map_dstream(struct sk_buff* skb,
                                     struct ar_dp_vdev_s* vdev,
                                     int* v_wme_ac, int* v_pri)
{
    AR_STATUS status = AR_STATUS_SUCCESS;

    switch (vdev->qos_downstream_map) {
        case AR_QOS_DSTREAM_MAP_NONE:
            // Use default priority from SSID configuration
            *v_wme_ac = vdev->default_wme_ac;
            *v_pri = vdev->default_tid;
            break;

        case AR_QOS_DSTREAM_MAP_DSCP:
            status = ar_qos_dp_set_map_dstream_dscp(skb, vdev, v_wme_ac, v_pri);
            break;

        case AR_QOS_DSTREAM_MAP_TOS:
            status = ar_qos_dp_set_map_dstream_tos(skb, vdev, v_wme_ac, v_pri);
            break;

        case AR_QOS_DSTREAM_MAP_8021P:
            ar_qos_dp_set_map_dstream_8021p(skb, vdev, v_wme_ac, v_pri);
            break;

        default:
            status = AR_STATUS_EINVAL;
            break;
    }

    return status;
}
```

## 14.2 Priority Ceiling Mechanism

### 14.2.1 AR_CEIL_QOS_PRIO Macro

```c
/**
 * AR_CEIL_QOS_PRIO - Apply priority ceiling to traffic
 * @vdev: Virtual device handle
 * @wme_ac: WMM Access Category (input/output)
 * @tid: Traffic Identifier (input/output)
 *
 * If the configured priority type is "Ceiling", caps the traffic
 * priority to the SSID's configured maximum priority.
 */
#define AR_CEIL_QOS_PRIO(vdev, wme_ac, tid)                     \
    do {                                                         \
        if (vdev->priority_type == AR_QOS_PRIO_CEILING) {       \
            if (wme_ac > vdev->ssid_priority) {                  \
                wme_ac = vdev->ssid_priority;                    \
                tid = AR_WME_AC_TO_TID(wme_ac);                  \
            }                                                    \
        }                                                        \
    } while (0)
```

### 14.2.2 Priority Ceiling Flow

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         Priority Ceiling Operation                           │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  Configuration:                                                              │
│  • SSID Priority: Video (AC_VI, priority 2)                                 │
│  • Priority Type: Ceiling (0)                                               │
│                                                                              │
│  Example Traffic Processing:                                                 │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │  Packet DSCP │ Derived AC │ After Ceiling │ Final AC │ Explanation   │  │
│  │  ────────────┼────────────┼───────────────┼──────────┼─────────────── │  │
│  │  EF (46)     │   AC_VO    │     Capped    │  AC_VI   │ Voice→Video   │  │
│  │  CS6 (48)    │   AC_VO    │     Capped    │  AC_VI   │ Voice→Video   │  │
│  │  AF41 (34)   │   AC_VI    │   No change   │  AC_VI   │ At ceiling    │  │
│  │  CS3 (24)    │   AC_BE    │   No change   │  AC_BE   │ Below ceiling │  │
│  │  CS1 (8)     │   AC_BK    │   No change   │  AC_BK   │ Below ceiling │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                                                                              │
│  Fixed Priority Mode (priorityType = 1):                                    │
│  All traffic uses the configured SSID priority, ignoring packet DSCP.      │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

# 15. DSCP in IPv4 vs IPv6

## 15.1 IPv4 DSCP Extraction

### 15.1.1 IPv4 Header Structure

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           IPv4 Header (First 20 bytes)                       │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  Offset  0       4       8      12      16      20      24      28      31  │
│  ┌───────┬───────┬───────────────┬───────────────────────────────────────┐  │
│  │Version│  IHL  │    ToS/DSCP   │          Total Length                 │  │
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
│  ToS/DSCP Byte Detail:                                                       │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │  Bit 7   │ Bit 6 │ Bit 5 │ Bit 4 │ Bit 3 │ Bit 2 │ Bit 1 │ Bit 0    │  │
│  │  DSCP[5] │DSCP[4]│DSCP[3]│DSCP[2]│DSCP[1]│DSCP[0]│ ECN[1]│ ECN[0]   │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                                                                              │
│  Extraction:  dscp = (ip->tos >> 2) & 0x3F                                  │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 15.1.2 IPv4 DSCP Code

```c
// From ar_qos.c
if (eh->ether_type == __constant_htons(ETHERTYPE_IP)) {
    const struct iphdr* ip = (struct iphdr*)skb_network_header(skb);

    // Extract DSCP from TOS byte
    uint8_t tos = ip->tos;
    uint8_t dscp = (tos >> 2) & 0x3F;  // Get bits 2-7 as DSCP
    uint8_t ecn = tos & 0x03;           // Get bits 0-1 as ECN

    // Look up TID from DSCP
    int tid = dscp_tid_map[dscp];
}
```

## 15.2 IPv6 DSCP Extraction

### 15.2.1 IPv6 Header Structure

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           IPv6 Header (40 bytes)                             │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  Offset  0       4       8      12      16      20      24      28      31  │
│  ┌───────┬───────────────┬───────────────────────────────────────────────┐  │
│  │Version│ Traffic Class │              Flow Label                       │  │
│  │  (4)  │     (8)       │                (20)                           │  │
│  ├───────┴───────────────┼───────────────┬───────────────────────────────┤  │
│  │    Payload Length     │  Next Header  │        Hop Limit              │  │
│  │        (16)           │      (8)      │           (8)                 │  │
│  ├───────────────────────┴───────────────┴───────────────────────────────┤  │
│  │                                                                        │  │
│  │                    Source Address (128 bits)                          │  │
│  │                                                                        │  │
│  ├───────────────────────────────────────────────────────────────────────┤  │
│  │                                                                        │  │
│  │                  Destination Address (128 bits)                       │  │
│  │                                                                        │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                                                                              │
│  Traffic Class Byte (same as IPv4 ToS):                                     │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │  DSCP (6 bits)                        │ ECN (2 bits)                  │  │
│  │  Bits 7-2                              │ Bits 1-0                      │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                                                                              │
│  Extraction:  dscp = (ipv6->priority << 2) | ((ipv6->flow_lbl[0] >> 6)     │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 15.2.2 IPv6 DSCP Code

```c
// From ar_qos.c - IPv6 handling
if (eh->ether_type == __constant_htons(ETHERTYPE_IPV6)) {
    const struct ipv6hdr* ipv6 = (struct ipv6hdr*)skb_network_header(skb);

    // Extract Traffic Class from IPv6 header
    // Traffic Class is split across priority (4 bits) and flow_lbl[0] (4 bits)
    uint8_t tc = (ipv6->priority << 4) | (ipv6->flow_lbl[0] >> 4);
    uint8_t dscp = (tc >> 2) & 0x3F;
    uint8_t ecn = tc & 0x03;

    // Look up TID from DSCP
    int tid = dscp_tid_map[dscp];
}
```

---

# 16. Testing DSCP Functionality

## 16.1 ApQoSTest.py Test Cases

### 16.1.1 Test Variants

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          ApQoSTest Variants                                  │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  Variant │ SSID Priority │ Priority Type │ Downstream Map │ Expected Flag  │
│  ────────┼───────────────┼───────────────┼────────────────┼──────────────── │
│  test1   │ Voice (3)     │ Ceiling (0)   │ DSCP (1)       │ 0x09           │
│  test2   │ Video (2)     │ Fixed (1)     │ TOS (2)        │ 0x14           │
│  test3   │ Background(1) │ Ceiling (0)   │ DSCP (1)       │ 0x0A           │
│  test4   │ Best Eff.(0)  │ Fixed (1)     │ None (0)       │ 0x07           │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 16.1.2 Test Code Example

From `ApQoSTest.py`:

```python
class ApQoSTest(WifiClusterTest):
    """Test QoS flag configuration on VAPs"""

    def test1_dscp_voice_ceiling(self):
        """Test DSCP downstream mapping with Voice ceiling"""
        self.configureSsid(
            ssidPriority=3,           # Voice
            qosPrioType=0,            # Ceiling
            qosDownStrMap=1,          # DSCP
            qosUpStrMark8021p=0,
            qosUpStrMarkDscpTos=0
        )

        # Connect client and verify QoS flag
        self.connectClient()
        self.verifyQosFlag(expected=0x09)

        # Generate traffic and verify counters
        self.sendTraffic(dscp=46)  # EF traffic
        self.verifyQosCounters(ac_vo_expected=True)
```

## 16.2 DSCP Testing Commands

### 16.2.1 Debug Commands

```bash
# View current DSCP-TID mapping on AP
iwpriv ath0 getdscp

# Set DSCP-TID mapping
iwpriv ath0 setdscp <dscp> <tid>

# View QoS statistics
cat /sys/kernel/debug/ath11k/qos_stats

# View per-AC TX/RX counters
iw dev wlan0 station dump | grep -A 20 "Station"
```

### 16.2.2 Traffic Generation with Scapy

```python
from scapy.all import *

# Send packet with specific DSCP value
def send_dscp_packet(dst_ip, dscp):
    tos_byte = dscp << 2  # Shift DSCP to TOS position
    pkt = IP(dst=dst_ip, tos=tos_byte)/ICMP()
    send(pkt)

# Test various DSCP values
dscp_values = [0, 8, 16, 24, 32, 40, 46, 48, 56]
for dscp in dscp_values:
    send_dscp_packet("192.168.1.100", dscp)
    print(f"Sent packet with DSCP {dscp}")
```


---

# 17. DSCP Reference Tables

## 17.1 Complete DSCP Value Reference

### 17.1.1 All 64 DSCP Values

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    Complete DSCP Value Reference (0-63)                      │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│ DSCP│ Binary │ PHB Name  │ ToS Byte│ TID │ AC    │ Description             │
│ ────┼────────┼───────────┼─────────┼─────┼───────┼──────────────────────── │
│   0 │ 000000 │ CS0/BE    │  0x00   │  0  │ AC_BE │ Best Effort (Default)   │
│   1 │ 000001 │ -         │  0x04   │  0  │ AC_BE │ Undefined               │
│   2 │ 000010 │ -         │  0x08   │  0  │ AC_BE │ Undefined               │
│   3 │ 000011 │ -         │  0x0C   │  0  │ AC_BE │ Undefined               │
│   4 │ 000100 │ -         │  0x10   │  0  │ AC_BE │ Undefined               │
│   5 │ 000101 │ -         │  0x14   │  0  │ AC_BE │ Undefined               │
│   6 │ 000110 │ -         │  0x18   │  0  │ AC_BE │ Undefined               │
│   7 │ 000111 │ -         │  0x1C   │  0  │ AC_BE │ Undefined               │
│   8 │ 001000 │ CS1       │  0x20   │  1  │ AC_BK │ Class Selector 1        │
│   9 │ 001001 │ -         │  0x24   │  1  │ AC_BK │ Undefined               │
│  10 │ 001010 │ AF11      │  0x28   │  1  │ AC_BK │ Assured Forwarding 11   │
│  11 │ 001011 │ -         │  0x2C   │  1  │ AC_BK │ Undefined               │
│  12 │ 001100 │ AF12      │  0x30   │  1  │ AC_BK │ Assured Forwarding 12   │
│  13 │ 001101 │ -         │  0x34   │  1  │ AC_BK │ Undefined               │
│  14 │ 001110 │ AF13      │  0x38   │  1  │ AC_BK │ Assured Forwarding 13   │
│  15 │ 001111 │ -         │  0x3C   │  1  │ AC_BK │ Undefined               │
│  16 │ 010000 │ CS2       │  0x40   │  2  │ AC_BK │ Class Selector 2        │
│  17 │ 010001 │ -         │  0x44   │  2  │ AC_BK │ Undefined               │
│  18 │ 010010 │ AF21      │  0x48   │  2  │ AC_BK │ Assured Forwarding 21   │
│  19 │ 010011 │ -         │  0x4C   │  2  │ AC_BK │ Undefined               │
│  20 │ 010100 │ AF22      │  0x50   │  2  │ AC_BK │ Assured Forwarding 22   │
│  21 │ 010101 │ -         │  0x54   │  2  │ AC_BK │ Undefined               │
│  22 │ 010110 │ AF23      │  0x58   │  2  │ AC_BK │ Assured Forwarding 23   │
│  23 │ 010111 │ -         │  0x5C   │  2  │ AC_BK │ Undefined               │
│  24 │ 011000 │ CS3       │  0x60   │  3  │ AC_BE │ Class Selector 3        │
│  25 │ 011001 │ -         │  0x64   │  3  │ AC_BE │ Undefined               │
│  26 │ 011010 │ AF31      │  0x68   │  3  │ AC_BE │ Assured Forwarding 31   │
│  27 │ 011011 │ -         │  0x6C   │  3  │ AC_BE │ Undefined               │
│  28 │ 011100 │ AF32      │  0x70   │  3  │ AC_BE │ Assured Forwarding 32   │
│  29 │ 011101 │ -         │  0x74   │  3  │ AC_BE │ Undefined               │
│  30 │ 011110 │ AF33      │  0x78   │  3  │ AC_BE │ Assured Forwarding 33   │
│  31 │ 011111 │ -         │  0x7C   │  3  │ AC_BE │ Undefined               │
│  32 │ 100000 │ CS4       │  0x80   │  4  │ AC_VI │ Class Selector 4        │
│  33 │ 100001 │ -         │  0x84   │  4  │ AC_VI │ Undefined               │
│  34 │ 100010 │ AF41      │  0x88   │  4  │ AC_VI │ Assured Forwarding 41   │
│  35 │ 100011 │ -         │  0x8C   │  4  │ AC_VI │ Undefined               │
│  36 │ 100100 │ AF42      │  0x90   │  4  │ AC_VI │ Assured Forwarding 42   │
│  37 │ 100101 │ -         │  0x94   │  4  │ AC_VI │ Undefined               │
│  38 │ 100110 │ AF43      │  0x98   │  4  │ AC_VI │ Assured Forwarding 43   │
│  39 │ 100111 │ -         │  0x9C   │  4  │ AC_VI │ Undefined               │
│  40 │ 101000 │ CS5       │  0xA0   │  5  │ AC_VI │ Class Selector 5        │
│  41 │ 101001 │ -         │  0xA4   │  5  │ AC_VI │ Undefined               │
│  42 │ 101010 │ -         │  0xA8   │  5  │ AC_VI │ Undefined               │
│  43 │ 101011 │ -         │  0xAC   │  5  │ AC_VI │ Undefined               │
│  44 │ 101100 │ VA        │  0xB0   │  5  │ AC_VI │ Voice-Admit             │
│  45 │ 101101 │ -         │  0xB4   │  5  │ AC_VI │ Undefined               │
│  46 │ 101110 │ EF        │  0xB8   │  6  │ AC_VO │ Expedited Forwarding    │
│  47 │ 101111 │ -         │  0xBC   │  5  │ AC_VI │ Undefined               │
│  48 │ 110000 │ CS6       │  0xC0   │  6  │ AC_VO │ Class Selector 6        │
│  49 │ 110001 │ -         │  0xC4   │  6  │ AC_VO │ Undefined               │
│  50 │ 110010 │ -         │  0xC8   │  6  │ AC_VO │ Undefined               │
│  51 │ 110011 │ -         │  0xCC   │  6  │ AC_VO │ Undefined               │
│  52 │ 110100 │ -         │  0xD0   │  6  │ AC_VO │ Undefined               │
│  53 │ 110101 │ -         │  0xD4   │  6  │ AC_VO │ Undefined               │
│  54 │ 110110 │ -         │  0xD8   │  6  │ AC_VO │ Undefined               │
│  55 │ 110111 │ -         │  0xDC   │  6  │ AC_VO │ Undefined               │
│  56 │ 111000 │ CS7       │  0xE0   │  7  │ AC_VO │ Class Selector 7        │
│  57 │ 111001 │ -         │  0xE4   │  7  │ AC_VO │ Undefined               │
│  58 │ 111010 │ -         │  0xE8   │  7  │ AC_VO │ Undefined               │
│  59 │ 111011 │ -         │  0xEC   │  7  │ AC_VO │ Undefined               │
│  60 │ 111100 │ -         │  0xF0   │  7  │ AC_VO │ Undefined               │
│  61 │ 111101 │ -         │  0xF4   │  7  │ AC_VO │ Undefined               │
│  62 │ 111110 │ -         │  0xF8   │  7  │ AC_VO │ Undefined               │
│  63 │ 111111 │ -         │  0xFC   │  7  │ AC_VO │ Undefined               │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

## 17.2 Standard PHB Summary

### 17.2.1 Class Selectors (CS)

| DSCP | Name | Binary | ToS Byte | Typical Use |
|------|------|--------|----------|-------------|
| 0 | CS0 (BE) | 000000 | 0x00 | Best Effort (default) |
| 8 | CS1 | 001000 | 0x20 | Scavenger/Bulk Data |
| 16 | CS2 | 010000 | 0x40 | OAM |
| 24 | CS3 | 011000 | 0x60 | Broadcast Video |
| 32 | CS4 | 100000 | 0x80 | Real-Time Interactive |
| 40 | CS5 | 101000 | 0xA0 | Signaling |
| 48 | CS6 | 110000 | 0xC0 | Network Control |
| 56 | CS7 | 111000 | 0xE0 | Reserved |

### 17.2.2 Assured Forwarding (AF)

| Class | Low Drop | Med Drop | High Drop | Typical Use |
|-------|----------|----------|-----------|-------------|
| AF1 | AF11 (10) | AF12 (12) | AF13 (14) | High-Throughput Data |
| AF2 | AF21 (18) | AF22 (20) | AF23 (22) | Low-Latency Data |
| AF3 | AF31 (26) | AF32 (28) | AF33 (30) | Multimedia Streaming |
| AF4 | AF41 (34) | AF42 (36) | AF43 (38) | Multimedia Conferencing |

### 17.2.3 Expedited Forwarding (EF)

| DSCP | Name | Binary | ToS Byte | Use |
|------|------|--------|----------|-----|
| 46 | EF | 101110 | 0xB8 | VoIP Media |
| 44 | VA | 101100 | 0xB0 | Voice-Admit (CAC-enabled) |

---

# 18. RFC Standards Reference

## 18.1 Core DiffServ RFCs

### 18.1.1 RFC 2474 - Definition of the DS Field

**Title:** Definition of the Differentiated Services Field (DS Field) in the IPv4 and IPv6 Headers

**Key Points:**
- Defines the 6-bit DSCP field in the ToS/Traffic Class byte
- Replaces the original IP Precedence model
- Defines 64 codepoints (0-63)
- Reserves codepoints for standard PHBs

### 18.1.2 RFC 2475 - DiffServ Architecture

**Title:** An Architecture for Differentiated Services

**Key Points:**
- Defines the DiffServ architecture
- Introduces Per-Hop Behaviors (PHBs)
- Defines traffic classification and conditioning
- Describes DS domain and region concepts

### 18.1.3 RFC 2597 - Assured Forwarding PHB Group

**Title:** Assured Forwarding PHB Group

**Key Points:**
- Defines 4 AF classes with 3 drop precedences each
- 12 DSCP values: AF11-AF13, AF21-AF23, AF31-AF33, AF41-AF43
- Higher drop precedence = more likely to be dropped

### 18.1.4 RFC 2598/3246 - Expedited Forwarding PHB

**Title:** An Expedited Forwarding PHB (Superseded by RFC 3246)

**Key Points:**
- Defines EF PHB (DSCP 46)
- Low loss, low latency, low jitter
- Designed for VoIP and real-time applications

## 18.2 Related WiFi Standards

### 18.2.1 IEEE 802.11e

**Title:** QoS Enhancements

**Key Points:**
- Defines WMM (WiFi Multimedia)
- 4 Access Categories: AC_VO, AC_VI, AC_BE, AC_BK
- EDCA (Enhanced Distributed Channel Access)
- 8 Traffic Identifiers (TID 0-7)

### 18.2.2 IEEE 802.11-2020 Section 10.2.4.2

**Title:** QoS Map Element

**Key Points:**
- Defines QoS Map frame format
- DSCP to UP mapping configuration
- DSCP exception handling

---

# 19. Troubleshooting Guide

## 19.1 Common DSCP Issues

### 19.1.1 Traffic Not Prioritized Correctly

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                     DSCP Prioritization Troubleshooting                      │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  Symptom: Voice traffic not getting Voice (AC_VO) priority                  │
│                                                                              │
│  Checklist:                                                                  │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │ 1. Verify DSCP value in packets:                                      │  │
│  │    tcpdump -i eth0 -v | grep "tos"                                    │  │
│  │                                                                        │  │
│  │ 2. Check downstream mapping configuration:                            │  │
│  │    - Is downstreamMap set to DSCP (1)?                                │  │
│  │    - Is WMM enabled on the SSID?                                      │  │
│  │                                                                        │  │
│  │ 3. Verify DSCP-TID mapping table:                                     │  │
│  │    iwpriv ath0 getdscp                                                │  │
│  │                                                                        │  │
│  │ 4. Check priority ceiling:                                            │  │
│  │    - If priorityType=Ceiling, check ssidPriority                      │  │
│  │    - Voice traffic needs ssidPriority >= 3                            │  │
│  │                                                                        │  │
│  │ 5. Verify QoS flag on VAP:                                            │  │
│  │    cat /sys/class/net/ath0/qos_flags                                  │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 19.1.2 DSCP Being Remarked

**Problem:** DSCP values are being changed by the network

**Solutions:**
1. Check intermediate switches/routers for QoS policies
2. Verify trust settings on switch ports
3. Check for NAT devices that may reset DSCP
4. Verify upstream marking configuration isn't overwriting values

### 19.1.3 QoS Counters Not Incrementing

```bash
# Debug steps:
# 1. Check if traffic is reaching the AP
tcpdump -i ath0 -c 10

# 2. Verify QoS counters location
cat /sys/kernel/debug/ath11k/*/qos_stats

# 3. Check driver version and QoS support
dmesg | grep -i qos

# 4. Verify WMM is enabled
iwpriv ath0 get_wmm
```

## 19.2 Debug Commands Reference

### 19.2.1 Driver Debug Commands

```bash
# View all QoS-related settings
iwpriv ath0 get_qos

# View WMM parameters
iwpriv ath0 getwmmparams

# View per-AC statistics
cat /proc/net/wireless

# Enable QoS debug logging
echo 1 > /sys/module/ath11k/parameters/debug_mask
```

### 19.2.2 Packet Capture Analysis

```bash
# Capture with DSCP filtering
tcpdump -i eth0 -w capture.pcap 'ip[1] & 0xfc != 0'

# Analyze DSCP distribution
tshark -r capture.pcap -T fields -e ip.dsfield.dscp | sort | uniq -c
```

---

# 20. Appendix

## 20.1 Glossary

| Term | Definition |
|------|------------|
| **DSCP** | Differentiated Services Code Point - 6-bit field for traffic classification |
| **TOS** | Type of Service - Legacy 8-bit IP header field |
| **ECN** | Explicit Congestion Notification - 2-bit field for congestion signaling |
| **TID** | Traffic Identifier - 802.11 4-bit field (0-15, typically 0-7 used) |
| **AC** | Access Category - WMM queue (VO, VI, BE, BK) |
| **WMM** | WiFi Multimedia - QoS mechanism for 802.11 |
| **PHB** | Per-Hop Behavior - Forwarding treatment for packets |
| **EF** | Expedited Forwarding - Low latency PHB (DSCP 46) |
| **AF** | Assured Forwarding - PHB group with drop precedence |
| **CS** | Class Selector - Backward-compatible DSCP values |
| **PCP** | Priority Code Point - 802.1Q VLAN priority field |
| **EDCA** | Enhanced Distributed Channel Access - 802.11e MAC enhancement |

## 20.2 Code Reference Files

| File | Purpose |
|------|---------|
| `ar_qos.c` | Core DSCP/TOS/802.1p processing functions |
| `ar_qos.h` | QoS header definitions and macros |
| `dp_main.c` | Data path DSCP-TID map management |
| `dp_rings_main.c` | Default DSCP-TID and PCP-TID mapping tables |
| `ssid_qos_qca.go` | Go configuration for QoS parameters |
| `ssid_qos.go` | QoS configuration mapping |
| `SsidConfig.tac` | QoS configuration data model |
| `ieee80211_defines.h` | IEEE 802.11 QoS map structures |
| `wlan_son_ald.h` | DSCP value definitions |
| `ApQoSTest.py` | QoS test automation |

## 20.3 Quick Reference Card

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          DSCP Quick Reference Card                           │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  DSCP Extraction:                                                            │
│  ├─ IPv4: dscp = (ip->tos >> 2) & 0x3F                                      │
│  └─ IPv6: dscp = (traffic_class >> 2) & 0x3F                                │
│                                                                              │
│  ToS Byte to DSCP:  dscp = (tos >> 2)                                       │
│  DSCP to ToS Byte:  tos = (dscp << 2) | ecn                                 │
│                                                                              │
│  Common DSCP Values:                                                         │
│  ├─ EF (46)  = 0xB8 → Voice                                                 │
│  ├─ AF41(34) = 0x88 → Video Conferencing                                    │
│  ├─ CS3 (24) = 0x60 → Signaling                                             │
│  └─ CS0 (0)  = 0x00 → Best Effort                                           │
│                                                                              │
│  TID to AC Mapping:                                                          │
│  ├─ TID 0, 3 → AC_BE (Best Effort)                                          │
│  ├─ TID 1, 2 → AC_BK (Background)                                           │
│  ├─ TID 4, 5 → AC_VI (Video)                                                │
│  └─ TID 6, 7 → AC_VO (Voice)                                                │
│                                                                              │
│  QoS Flag Bits:                                                              │
│  ├─ Bits 0-1: SSID Priority (0-3)                                           │
│  ├─ Bit 2:    Priority Type (Ceiling/Fixed)                                 │
│  ├─ Bits 3-4: Downstream Map (None/DSCP/TOS)                                │
│  ├─ Bit 5:    802.1p Upstream Marking                                       │
│  ├─ Bit 6:    DSCP Upstream Marking                                         │
│  └─ Bit 7:    TOS Upstream Marking                                          │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

## 20.4 Revision History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2024 | Arista Networks | Initial documentation |

---

**End of DSCP Documentation**

*© 2024 Arista Networks, Inc. All rights reserved.*
