# ApQoSTest.py - Comprehensive Documentation



## Table of Contents

1. [Executive Summary](#executive-summary)
2. [File Overview](#file-overview)
3. [Test Architecture](#test-architecture)
4. [QoS Fundamentals](#qos-fundamentals)
5. [Class Reference](#class-reference)
6. [Method Documentation](#method-documentation)
7. [Test Variants](#test-variants)
8. [Configuration Parameters](#configuration-parameters)
9. [Test Execution Flow](#test-execution-flow)
10. [Dependencies and Imports](#dependencies-and-imports)
11. [Test Requirements](#test-requirements)
12. [Error Handling](#error-handling)
13. [Troubleshooting Guide](#troubleshooting-guide)
14. [Related Components](#related-components)
15. [Scapy Library Reference](#scapy-library-reference)
16. [Best Practices](#best-practices)
17. [Examples and Use Cases](#examples-and-use-cases)
18. [Appendix](#appendix)

---

# 1. Executive Summary

## 1.1 Purpose

The `ApQoSTest.py` file is an automated cluster test (ctest) designed to validate Quality of Service (QoS)
settings on Arista WiFi Access Points. This test ensures that QoS configurations are correctly applied
to Virtual Access Points (VAPs) and verifies that network traffic is properly classified and handled
according to the configured QoS policies.

## 1.2 Key Features

- **QoS Flag Validation**: Verifies that QoS parameters are correctly set at the driver level
- **Traffic Classification Testing**: Confirms packets are classified into correct QoS queues
- **Multiple Configuration Variants**: Tests various combinations of QoS settings
- **Automated End-to-End Testing**: From configuration to traffic verification

## 1.3 Test Scope

| Aspect | Coverage |
|--------|----------|
| SSID Priority | Best Effort (value = 2) |
| Priority Types | Ceiling and Fixed |
| Downstream Mapping | DSCP and TOS |
| Upstream Marking | 802.1p and DSCP |
| Security Mode | WPA-PSK |
| Radio Band | 5 GHz |

## 1.4 Copyright and Licensing

```
Copyright (c) 2024 Arista Networks, Inc. All rights reserved.
Arista Networks, Inc. Confidential and Proprietary.
```

---

# 2. File Overview

## 2.1 File Location

```
autotest/WifiClusterTest/ctest/ApQoSTest.py
```

## 2.2 File Metadata

| Attribute | Value |
|-----------|-------|
| **File Type** | Python Test Script |
| **Test Framework** | ArosTest + WifiClusterTest |
| **Test Category** | Cluster Test (ctest) |
| **Tags** | WifiAPNet |
| **Lines of Code** | 217 |
| **Python Version** | Python 3.x |

## 2.3 Test Brief

```
@brief@
QoS setting verification

@testcase@
Test to validate QoS flag is set on vap
Following is the qos config:
1. SSID Priority = Best effort
2. Priority Type = Ceiling & Fixed
3. Downstream Mapping = DSCP & TOS
4. Upstream Marking = 802.1p & DSCP Marking
```

## 2.4 Source Code Header

```python
#!/usr/bin/env python3
# Copyright (c) 2024 Arista Networks, Inc.  All rights reserved.
# Arista Networks, Inc. Confidential and Proprietary.
```

---

# 3. Test Architecture

## 3.1 High-Level Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           ApQoSTest Architecture                             │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌──────────────┐     ┌──────────────┐     ┌──────────────┐                 │
│  │   Test       │     │   WiFi       │     │   Host       │                 │
│  │   Framework  │────▶│   Access     │────▶│   Server     │                 │
│  │   (ArosTest) │     │   Point      │     │   (DHCP)     │                 │
│  └──────────────┘     └──────────────┘     └──────────────┘                 │
│         │                    │                    │                          │
│         │                    │                    │                          │
│         ▼                    ▼                    ▼                          │
│  ┌──────────────┐     ┌──────────────┐     ┌──────────────┐                 │
│  │   Test       │     │   VAP        │     │   VLAN       │                 │
│  │   Cluster    │────▶│   Config     │────▶│   Network    │                 │
│  │   Manager    │     │   (QoS)      │     │   Config     │                 │
│  └──────────────┘     └──────────────┘     └──────────────┘                 │
│         │                    │                                               │
│         │                    │                                               │
│         ▼                    ▼                                               │
│  ┌──────────────┐     ┌──────────────┐                                      │
│  │   Client     │     │   QoS        │                                      │
│  │   Device     │────▶│   Counters   │                                      │
│  │   (DUT)      │     │   Validation │                                      │
│  └──────────────┘     └──────────────┘                                      │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

## 3.2 Component Interaction

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        Component Interaction Flow                            │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ApQoSTest                                                                   │
│      │                                                                       │
│      ├──▶ WifiClusterTestBase (Parent Class)                                │
│      │        │                                                              │
│      │        ├──▶ configureSsid() - Creates SSID with QoS settings         │
│      │        ├──▶ vlanBridgeSanityCheck() - Validates VLAN bridge          │
│      │        └──▶ initDuts() - Initializes test devices                    │
│      │                                                                       │
│      ├──▶ ApEdut (Access Point Equipment Under Test)                        │
│      │        │                                                              │
│      │        ├──▶ features() - Queries VAP QoS flags                       │
│      │        ├──▶ getVapIfaceNameon5GRadio() - Gets VAP interface          │
│      │        ├──▶ rootCli() - Executes shell commands                      │
│      │        └──▶ createApTapInterfaces() - Creates TAP interfaces         │
│      │                                                                       │
│      ├──▶ ClientEdut (Client Equipment Under Test)                          │
│      │        │                                                              │
│      │        ├──▶ getIntfMacAddr() - Gets client MAC address               │
│      │        ├──▶ pingTest() - Performs connectivity test                  │
│      │        └──▶ defaultWInt() - Gets default wireless interface          │
│      │                                                                       │
│      └──▶ HostServicesLib                                                   │
│               │                                                              │
│               ├──▶ HostServerDut - Host server management                   │
│               └──▶ HostDhcpService - DHCP service management                │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

## 3.3 Class Hierarchy

```
object
    │
    └── WifiClusterTestBase
            │
            └── ApQoSTest
                    │
                    ├── __init__()
                    ├── parseOptions()
                    ├── validateQoSFlags()
                    ├── validateQoSCounters()
                    └── run()
```

## 3.4 Test Topology

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           Physical Test Topology                             │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│                        ┌─────────────────┐                                   │
│                        │   Host Server   │                                   │
│                        │   (DHCP/DNS)    │                                   │
│                        │   192.168.x.1   │                                   │
│                        └────────┬────────┘                                   │
│                                 │                                            │
│                                 │ Ethernet                                   │
│                                 │                                            │
│                        ┌────────┴────────┐                                   │
│                        │   Access Point  │                                   │
│                        │   (AP DUT)      │                                   │
│                        │                 │                                   │
│                        │  ┌───────────┐  │                                   │
│                        │  │   VAP     │  │                                   │
│                        │  │  (QoS)    │  │                                   │
│                        │  │  5 GHz    │  │                                   │
│                        │  └───────────┘  │                                   │
│                        └────────┬────────┘                                   │
│                                 │                                            │
│                                 │ WiFi (802.11ac/ax)                         │
│                                 │                                            │
│                        ┌────────┴────────┐                                   │
│                        │  Client Device  │                                   │
│                        │  (Client DUT)   │                                   │
│                        │  192.168.x.x    │                                   │
│                        └─────────────────┘                                   │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

# 4. QoS Fundamentals

## 4.1 What is QoS?

Quality of Service (QoS) is a set of technologies and techniques used to manage network resources
by prioritizing specific types of data traffic. In WiFi networks, QoS ensures that time-sensitive
applications (like voice and video) receive priority over less critical traffic (like file downloads).

## 4.2 WiFi QoS Standards

### 4.2.1 IEEE 802.11e (WMM)

WiFi Multimedia (WMM) is based on IEEE 802.11e and defines four Access Categories (ACs):

| Access Category | Priority | Traffic Type | Examples |
|-----------------|----------|--------------|----------|
| AC_VO (Voice) | Highest (7,6) | Voice traffic | VoIP, Video calls |
| AC_VI (Video) | High (5,4) | Video traffic | Streaming video |
| AC_BE (Best Effort) | Medium (3,0) | Standard traffic | Web browsing, Email |
| AC_BK (Background) | Low (2,1) | Background traffic | File downloads |

### 4.2.2 DSCP (Differentiated Services Code Point)

DSCP is a 6-bit field in the IP header used to classify and manage network traffic:

| DSCP Value | Per-Hop Behavior | Description |
|------------|------------------|-------------|
| 46 (EF) | Expedited Forwarding | Low latency, low jitter |
| 34 (AF41) | Assured Forwarding | High priority |
| 26 (AF31) | Assured Forwarding | Medium priority |
| 0 (BE) | Best Effort | Default, no priority |

### 4.2.3 TOS (Type of Service)

TOS is an 8-bit field in the IPv4 header (predecessor to DSCP):

| TOS Bits | Meaning |
|----------|---------|
| Bits 0-2 | Precedence (0-7) |
| Bit 3 | Delay (0=normal, 1=low) |
| Bit 4 | Throughput (0=normal, 1=high) |
| Bit 5 | Reliability (0=normal, 1=high) |

### 4.2.4 802.1p Priority

802.1p is a 3-bit field in the VLAN tag for Layer 2 QoS:

| Priority | Traffic Type |
|----------|--------------|
| 7 | Network Control |
| 6 | Internetwork Control |
| 5 | Voice |
| 4 | Video |
| 3 | Critical Applications |
| 2 | Excellent Effort |
| 1 | Background |
| 0 | Best Effort |

## 4.3 QoS Parameters in ApQoSTest

### 4.3.1 SSID Priority

The SSID Priority determines the default traffic priority for all traffic on the SSID:

| Value | Priority Name | Description |
|-------|---------------|-------------|
| 0 | Background | Lowest priority, bulk transfers |
| 1 | Spare | Reserved |
| 2 | Best Effort | Default priority (used in test) |
| 3 | Excellent Effort | Business critical |
| 4 | Controlled Load | Streaming multimedia |
| 5 | Video | Video traffic |
| 6 | Voice | Voice traffic |
| 7 | Network Control | Highest priority |

### 4.3.2 Priority Type

| Type | Value | Behavior |
|------|-------|----------|
| Ceiling | 0 | Maximum allowed priority - traffic can be marked up to this level |
| Fixed | 1 | Exact priority - all traffic is marked at this exact level |

**Key Difference:**
- **Ceiling**: Allows downstream mapping to adjust priority based on incoming DSCP/TOS
- **Fixed**: Ignores downstream mapping, all traffic gets the same priority

### 4.3.3 Downstream Mapping

Controls how incoming traffic priority is determined:

| Type | Value | Description |
|------|-------|-------------|
| DSCP | 1 | Use DSCP field from IP header |
| TOS | 2 | Use TOS field from IP header |
| Disabled | 0 | No downstream mapping (used with Fixed priority) |

### 4.3.4 Upstream Marking

Controls how outgoing traffic is marked:

| Parameter | Value | Description |
|-----------|-------|-------------|
| 802.1p Marking | 1 | Enable 802.1p priority tagging |
| DSCP/TOS Marking | 1 | Enable DSCP/TOS marking in IP header |

## 4.4 QoS Configuration Flow

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         QoS Configuration Flow                               │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  1. SSID Configuration                                                       │
│     │                                                                        │
│     ▼                                                                        │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │  configureSsid() with QoS parameters:                                │    │
│  │  - qosSsidPriority = 2 (Best Effort)                                 │    │
│  │  - qosPriorityType = 0 (Ceiling) or 1 (Fixed)                        │    │
│  │  - qosDownStrMap = 1 (DSCP) or 2 (TOS)                               │    │
│  │  - qosUpStrMark8021p = 1 (Enabled)                                   │    │
│  │  - qosUpStrMarkDscpTos = 1 (Enabled)                                 │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│     │                                                                        │
│     ▼                                                                        │
│  2. AP Configuration Applied                                                 │
│     │                                                                        │
│     ▼                                                                        │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │  AP Config Parameters Set:                                           │    │
│  │  - QOS_SSID_PRIORITY                                                 │    │
│  │  - QOS_PRIORITY_TYPE                                                 │    │
│  │  - QOS_DOWNSTR_MAP                                                   │    │
│  │  - QOS_UPSTR_MARK_802_1p                                             │    │
│  │  - QOS_UPSTR_MARK_DSCP_TOS                                           │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│     │                                                                        │
│     ▼                                                                        │
│  3. Driver-Level Configuration                                               │
│     │                                                                        │
│     ▼                                                                        │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │  VAP Interface Flags Set:                                            │    │
│  │  - iv_qos_prio                                                       │    │
│  │  - iv_qos_prio_type                                                  │    │
│  │  - iv_qos_dstream                                                    │    │
│  │  - iv_qos_ustream_8021p                                              │    │
│  │  - iv_qos_ustream_dscp                                               │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

# 5. Class Reference

## 5.1 ApQoSTest Class

### 5.1.1 Class Definition

```python
class ApQoSTest( WifiClusterTest.WifiClusterTestBase ):
    """
    QoS Test class for validating QoS settings on WiFi Access Points.

    This class inherits from WifiClusterTestBase and implements specific
    test logic for QoS flag validation and counter verification.
    """
```

### 5.1.2 Class Attributes

| Attribute | Type | Default | Description |
|-----------|------|---------|-------------|
| `options` | `Namespace` | - | Parsed command-line arguments |
| `apEdut` | `ApEdut` | `None` | Access Point Equipment Under Test |
| `clientEdut` | `ClientEdut` | `None` | Client device under test |
| `clientConn` | `ClientConnection` | `None` | Active client connection context |
| `host` | `HostServerDut` | `None` | Host server for DHCP services |
| `hostCli` | `CLI` | `None` | Host CLI client |
| `profileId` | `int` | `None` | SSID profile identifier |
| `ssid_name` | `str` | `None` | Configured SSID name |
| `vap` | `VapSection` | `None` | Virtual Access Point configuration |
| `ssidVlan` | `int` | `None` | VLAN associated with the SSID |
| `hostIp` | `str` | `None` | Host IP address |

### 5.1.3 QoS-Specific Attributes

| Attribute | Type | Default | Description |
|-----------|------|---------|-------------|
| `qosSsidPriority` | `int` | `2` | SSID priority (Best Effort) |
| `qosUpStrMark8021p` | `int` | `1` | 802.1p upstream marking enabled |
| `qosUpStrMarkDscpTos` | `int` | `1` | DSCP/TOS upstream marking enabled |
| `qosDownStrMap` | `int` | `1` or `2` | Downstream mapping (DSCP=1, TOS=2) |
| `qosPriorityType` | `int` | `0` or `1` | Priority type (Ceiling=0, Fixed=1) |

### 5.1.4 Inherited Attributes from WifiClusterTestBase

| Attribute | Type | Description |
|-----------|------|-------------|
| `testCluster` | `TestCluster` | Test cluster manager |
| `mwmToolsPath` | `str` | Path to MWM tools |
| `mwmDuts` | `list` | MWM devices under test |
| `rdrDuts` | `list` | RDR devices under test |
| `wmCloudDuts` | `list` | WM Cloud devices |
| `apDuts` | `list` | Access Point devices |
| `clientDuts` | `list` | Client devices |
| `rtrDut` | `RouterDut` | Router device |
| `apQwrapDuts` | `list` | QWrap AP devices |
| `nonMfrApDuts` | `list` | Non-MFR AP devices |
| `waitForApBoot` | `bool` | Wait for AP boot flag |
| `ssidProfile` | `SsidProfile` | SSID profile object |
| `ssidDeviceTemplate` | `DeviceTemplate` | Device template |
| `tracebacks` | `list` | Collected tracebacks |
| `vlanConfigFile` | `str` | VLAN configuration file path |
| `vlanData` | `dict` | VLAN configuration data |
| `defaultRootTemplateId` | `int` | Default root template ID |

---

# 6. Method Documentation

## 6.1 __init__ Method

### 6.1.1 Signature

```python
def __init__( self ):
```

### 6.1.2 Description

Initializes the ApQoSTest instance with default values and parses command-line options.

### 6.1.3 Implementation Details

```python
def __init__( self ):
    super().__init__( )
    self.options = self.parseOptions()
    self.apEdut = None
    self.clientEdut = None
    self.clientConn = None
    self.host = None
    self.hostCli = None
    self.profileId = None
    self.ssid_name = None
    self.vap = None
    self.ssidVlan = None
    self.hostIp = None

    self.qosSsidPriority = 2
    self.qosUpStrMark8021p = 1
    self.qosUpStrMarkDscpTos = 1

    if self.options.qosDownStrMap == "DSCP":
        self.qosDownStrMap = 1
    elif self.options.qosDownStrMap == "TOS":
        self.qosDownStrMap = 2

    if self.options.qosPriorityType == "Ceiling":
        self.qosPriorityType = 0
    else:
        self.qosPriorityType = 1
```

### 6.1.4 Initialization Flow

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         __init__ Execution Flow                              │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  1. Call parent __init__()                                                   │
│     └── WifiClusterTestBase.__init__()                                       │
│                                                                              │
│  2. Parse command-line options                                               │
│     └── self.parseOptions()                                                  │
│                                                                              │
│  3. Initialize instance attributes to None                                   │
│     ├── apEdut, clientEdut, clientConn                                       │
│     ├── host, hostCli                                                        │
│     ├── profileId, ssid_name, vap                                            │
│     └── ssidVlan, hostIp                                                     │
│                                                                              │
│  4. Set default QoS values                                                   │
│     ├── qosSsidPriority = 2 (Best Effort)                                    │
│     ├── qosUpStrMark8021p = 1 (Enabled)                                      │
│     └── qosUpStrMarkDscpTos = 1 (Enabled)                                    │
│                                                                              │
│  5. Convert string options to integer values                                 │
│     ├── qosDownStrMap: "DSCP" → 1, "TOS" → 2                                 │
│     └── qosPriorityType: "Ceiling" → 0, "Fixed" → 1                          │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

## 6.2 parseOptions Method

### 6.2.1 Signature

```python
def parseOptions( self ) -> argparse.Namespace:
```

### 6.2.2 Description

Parses command-line arguments specific to the QoS test.

### 6.2.3 Arguments Defined

| Argument | Type | Choices | Default | Description |
|----------|------|---------|---------|-------------|
| `--qosDownStrMap` | `str` | DSCP, TOS | DSCP | Downstream Mapping Type |
| `--qosPriorityType` | `str` | Ceiling, Fixed | Ceiling | QoS Priority Type |

### 6.2.4 Implementation

```python
def parseOptions( self ):
    parser = argparser
    parser.add_argument( "--qosDownStrMap", default="DSCP",
          choices=[ "DSCP", "TOS" ],
          help="Downstream Mapping Type" )
    parser.add_argument( "--qosPriorityType", default="Ceiling",
          choices=[ "Ceiling", "Fixed" ],
          help="QoS Priority Type" )
    return parser.parse_args()
```

### 6.2.5 Usage Examples

```bash
# Default options (DSCP + Ceiling)
python ApQoSTest.py

# TOS downstream mapping
python ApQoSTest.py --qosDownStrMap=TOS

# Fixed priority type
python ApQoSTest.py --qosPriorityType=Fixed

# Combined options
python ApQoSTest.py --qosDownStrMap=TOS --qosPriorityType=Fixed
```

## 6.3 validateQoSFlags Method

### 6.3.1 Signature

```python
def validateQoSFlags( self ) -> None:
```

### 6.3.2 Description

Validates that QoS flags are correctly set on the VAP interface by querying driver-level parameters.

### 6.3.3 Implementation

```python
def validateQoSFlags( self ):
    vapIface = self.apEdut.getVapIfaceNameon5GRadio( self.vap.idx )

    opQosSsidPriority = int( self.apEdut.features( vapIface=vapIface,
                                                  deviceType="vap",
                                                  feature="iv_qos_prio" ) )
    assert opQosSsidPriority == 0, \
        f"Qos SSID Priority set incorrectly to {opQosSsidPriority}"

    opQosPriorityType = int( self.apEdut.features( vapIface=vapIface,
                                                  deviceType="vap",
                                                  feature="iv_qos_prio_type" ) )
    assert opQosPriorityType == self.qosPriorityType, \
        f"Qos Priority Type set incorrectly to {opQosPriorityType}"

    opQosDownStrMap = int( self.apEdut.features( vapIface=vapIface,
                                                  deviceType="vap",
                                                  feature="iv_qos_dstream" ) )
    if self.qosPriorityType == 1:
        assert opQosDownStrMap == 0, \
            f"Qos Down Str Map set incorrectly to {opQosDownStrMap}"
    else:
        assert opQosDownStrMap == self.qosDownStrMap, \
            f"Qos Down Str Map set incorrectly to {opQosDownStrMap}"

    opQosUpStrMark8021p = int( self.apEdut.features( vapIface=vapIface,
                                                  deviceType="vap",
                                                  feature="iv_qos_ustream_8021p" ) )
    assert opQosUpStrMark8021p == self.qosUpStrMark8021p, \
        f"Qos Up Str Mark 802_1p set incorrectly to {opQosUpStrMark8021p}"

    opQosUpStrMarkDscpTos = int( self.apEdut.features( vapIface=vapIface,
                                                  deviceType="vap",
                                                  feature="iv_qos_ustream_dscp" ) )
    assert opQosUpStrMarkDscpTos == self.qosUpStrMarkDscpTos, \
        f"Qos Up Str Mark Dscp Tos set incorrectly to {opQosUpStrMarkDscpTos}"
```

### 6.3.4 VAP Features Queried

| Feature Name | Description | Expected Value |
|--------------|-------------|----------------|
| `iv_qos_prio` | SSID Priority | 0 |
| `iv_qos_prio_type` | Priority Type | 0 (Ceiling) or 1 (Fixed) |
| `iv_qos_dstream` | Downstream Mapping | 0, 1 (DSCP), or 2 (TOS) |
| `iv_qos_ustream_8021p` | 802.1p Upstream Marking | 1 (Enabled) |
| `iv_qos_ustream_dscp` | DSCP Upstream Marking | 1 (Enabled) |

### 6.3.5 Validation Logic

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                      validateQoSFlags Logic Flow                             │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  1. Get VAP interface name on 5GHz radio                                     │
│     └── vapIface = getVapIfaceNameon5GRadio(vap.idx)                         │
│                                                                              │
│  2. Query and validate iv_qos_prio                                           │
│     ├── Query: features(vapIface, "vap", "iv_qos_prio")                      │
│     └── Assert: value == 0                                                   │
│                                                                              │
│  3. Query and validate iv_qos_prio_type                                      │
│     ├── Query: features(vapIface, "vap", "iv_qos_prio_type")                 │
│     └── Assert: value == self.qosPriorityType                                │
│                                                                              │
│  4. Query and validate iv_qos_dstream                                        │
│     ├── Query: features(vapIface, "vap", "iv_qos_dstream")                   │
│     ├── If qosPriorityType == 1 (Fixed):                                     │
│     │   └── Assert: value == 0 (disabled)                                    │
│     └── Else:                                                                │
│         └── Assert: value == self.qosDownStrMap                              │
│                                                                              │
│  5. Query and validate iv_qos_ustream_8021p                                  │
│     ├── Query: features(vapIface, "vap", "iv_qos_ustream_8021p")             │
│     └── Assert: value == self.qosUpStrMark8021p                              │
│                                                                              │
│  6. Query and validate iv_qos_ustream_dscp                                   │
│     ├── Query: features(vapIface, "vap", "iv_qos_ustream_dscp")              │
│     └── Assert: value == self.qosUpStrMarkDscpTos                            │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

## 6.4 validateQoSCounters Method

### 6.4.1 Signature

```python
def validateQoSCounters( self ) -> None:
```

### 6.4.2 Description

Validates that QoS counters are being incremented for the "Best Effort" traffic class by
generating traffic and comparing counter values before and after.

### 6.4.3 Implementation

```python
def validateQoSCounters( self ):
    # Validate best efforts counters as per the QoS configuration applied
    vapIface = self.apEdut.getVapIfaceNameon5GRadio( self.vap.idx )
    clMac = self.clientEdut.getIntfMacAddr( self.clientEdut.defaultWInt( ) )
    oldData = self.apEdut.rootCli().runCmd(
        f"apstats {vapIface} -s -m {clMac} | grep -i 'Tx Data Packets per AC:' -A 5")

    t0( f"Old QoS stats {oldData}")
    match = re.search(r"Best effort\s*=\s*(\d+)", oldData)
    if match:
        bestEffortValueOld = int(match.group(1))
    else:
        t0("Best effort value not found.")

    cli = self.clientEdut.cliClient()
    cli.gotoMode( self.clientEdut.bashShellMode )
    clientDutwIntfName = self.clientEdut.defaultWInt( )

    assert( self.clientEdut.pingTest( cli,
        self.hostIp, srcIntf=clientDutwIntfName,
        ipVersion="4", pktCnt=50 ) ),\
        "Client IPV4 ping test failed: Host is not reachable."

    newData = self.apEdut.rootCli().runCmd(
        f"apstats {vapIface} -s -m {clMac} | grep -i 'Tx Data Packets per AC:' -A 5")

    t0( f"New QoS stats {newData}")
    match = re.search(r"Best effort\s*=\s*(\d+)", newData)
    if match:
        bestEffortValueNew = int(match.group(1))
    else:
        t0("Best effort value not found.")

    if bestEffortValueNew <= bestEffortValueOld:
        assert False, "Best effort counters not increased"
```

### 6.4.4 apstats Command

The `apstats` command is used to query per-station QoS statistics:

```bash
apstats <vap_interface> -s -m <client_mac> | grep -i 'Tx Data Packets per AC:' -A 5
```

**Sample Output:**
```
Tx Data Packets per AC:
    Background    = 0
    Best effort   = 1234
    Video         = 0
    Voice         = 0
```

### 6.4.5 Validation Flow

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                     validateQoSCounters Flow                                 │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  1. Get VAP interface and client MAC                                         │
│     ├── vapIface = getVapIfaceNameon5GRadio(vap.idx)                         │
│     └── clMac = getIntfMacAddr(defaultWInt())                                │
│                                                                              │
│  2. Query initial QoS statistics                                             │
│     ├── Run: apstats <vapIface> -s -m <clMac>                                │
│     └── Parse: "Best effort = <value>"                                       │
│                                                                              │
│  3. Generate traffic                                                         │
│     ├── Get client CLI and enter bash mode                                   │
│     └── Execute: ping <hostIp> -c 50                                         │
│                                                                              │
│  4. Query updated QoS statistics                                             │
│     ├── Run: apstats <vapIface> -s -m <clMac>                                │
│     └── Parse: "Best effort = <value>"                                       │
│                                                                              │
│  5. Validate counter increase                                                │
│     └── Assert: bestEffortValueNew > bestEffortValueOld                      │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

## 6.5 run Method

### 6.5.1 Signature

```python
def run( self, testCluster ) -> None:
```

### 6.5.2 Description

Main test execution method that orchestrates the entire QoS test flow.

### 6.5.3 Implementation

```python
def run( self, testCluster ):
    super().run( testCluster )
    self.apEdut, self.clientEdut  =\
        self.apDuts[ 0 ], self.clientDuts[ 0 ]

    clientWInt = self.clientEdut.defaultWInt( )

    self.apEdut.createApTapInterfaces( )

    with HostServicesLib.HostServerDut(
          vlanConfigFile=ApTestLib.DEF_VLANNET_YAML ) as host, \
             HostServicesLib.HostDhcpService( host ),\
             ApCommonLib.connectedApHostDuts( self.apEdut, host ):

        self.host, self.hostCli = host, host.hostDutCli

        self.apEdut.dhcpCommVlanIs(vlanId='u')
        ApDhcpHelper.validateDhcpConfig(self.apEdut, host)
        self.hostIp = host.vlanConfig.hostIp( 0 )

        self.vap, self.profileId, self.ssid_name = self.configureSsid(
                                       self.apEdut, ssidName=f"{self.apEdut.name()}-qos",
                                       security='wpa-psk',
                                       qosConfigIs=True,
                                       qosSsidPriority=self.qosSsidPriority,
                                       qosPriorityType=self.qosPriorityType,
                                       qosDownStrMap=self.qosDownStrMap,
                                       qosUpStrMark8021p= self.qosUpStrMark8021p,
                                       qosUpStrMarkDscpTos=self.qosUpStrMarkDscpTos
                                      )
        self.vlanBridgeSanityCheck( self.apEdut, vapIdx = self.vap.idx,
                    profileId=self.profileId, profileConfCheck=False )

        self.validateQoSFlags()

        with ApTestLib.connectClient( self.clientEdut, self.apEdut,
                                     self.profileId, wintfName=clientWInt,
                                     dhcpIp=True ) as clientConn:
            t0( f"Client received ip {clientConn.dhcpIp}" )
            self.clientConn = clientConn
            Tac.waitFor( lambda: self.clientConn.isConnected() is True,
                        description="Client connected" )

            self.validateQoSCounters()

    t0 ( "QoS SSID Verification successful" )
```

### 6.5.4 Execution Flow Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           run() Execution Flow                               │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │ Phase 1: Initialization                                              │    │
│  ├─────────────────────────────────────────────────────────────────────┤    │
│  │ 1. Call parent run() method                                          │    │
│  │ 2. Get AP and Client DUTs from test cluster                          │    │
│  │ 3. Get client wireless interface name                                │    │
│  │ 4. Create AP TAP interfaces                                          │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                              │                                               │
│                              ▼                                               │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │ Phase 2: Host Setup (Context Manager)                                │    │
│  ├─────────────────────────────────────────────────────────────────────┤    │
│  │ 1. Create HostServerDut with VLAN config                             │    │
│  │ 2. Start HostDhcpService                                             │    │
│  │ 3. Connect AP to Host                                                │    │
│  │ 4. Configure DHCP on AP                                              │    │
│  │ 5. Validate DHCP configuration                                       │    │
│  │ 6. Get host IP address                                               │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                              │                                               │
│                              ▼                                               │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │ Phase 3: SSID Configuration                                          │    │
│  ├─────────────────────────────────────────────────────────────────────┤    │
│  │ 1. Configure SSID with QoS parameters                                │    │
│  │    - ssidName: "<ap_name>-qos"                                       │    │
│  │    - security: wpa-psk                                               │    │
│  │    - QoS settings from test options                                  │    │
│  │ 2. Perform VLAN bridge sanity check                                  │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                              │                                               │
│                              ▼                                               │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │ Phase 4: QoS Flag Validation                                         │    │
│  ├─────────────────────────────────────────────────────────────────────┤    │
│  │ 1. Call validateQoSFlags()                                           │    │
│  │ 2. Verify all QoS parameters at driver level                         │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                              │                                               │
│                              ▼                                               │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │ Phase 5: Client Connection (Context Manager)                         │    │
│  ├─────────────────────────────────────────────────────────────────────┤    │
│  │ 1. Connect client to SSID                                            │    │
│  │ 2. Wait for DHCP IP assignment                                       │    │
│  │ 3. Verify client connection                                          │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                              │                                               │
│                              ▼                                               │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │ Phase 6: QoS Counter Validation                                      │    │
│  ├─────────────────────────────────────────────────────────────────────┤    │
│  │ 1. Call validateQoSCounters()                                        │    │
│  │ 2. Generate traffic with ping test                                   │    │
│  │ 3. Verify Best Effort counters increased                             │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                              │                                               │
│                              ▼                                               │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │ Phase 7: Cleanup                                                     │    │
│  ├─────────────────────────────────────────────────────────────────────┤    │
│  │ 1. Context managers handle cleanup automatically                     │    │
│  │ 2. Client disconnection                                              │    │
│  │ 3. Host services shutdown                                            │    │
│  │ 4. Log success message                                               │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

# 7. Test Variants

## 7.1 Variant Definition

Test variants allow running the same test with different configurations. The ApQoSTest
defines 4 variants covering all combinations of downstream mapping and priority type.

## 7.2 Variant Implementation

```python
def main():
    ArosTest.runMeAsRoot()
    tracing = [ "ApDut/*", "ApConfigLib/*", "ApQoSTest/*" ]
    ArosTest.desiredTracingIs( ",".join( tracing ) )
    ArosTest.applyDesiredTracing()

    reqs = WiFiTestReqs.wifi__ap01__client01

    variants = []
    # Default is DSCP Downstream mapping & QoS Priority Type as Ceiling
    variants.append( Variant( [ ], reqs,
        "Set Downstream mapping=DSCP, QoS Priority Type=Ceiling & verify QOS counters" ) )
    variants.append( Variant( [ "--qosPriorityType=Fixed" ], reqs,
        "Set Downstream mapping=DSCP, QoS Priority Type=Fixed & verify QOS counters" ) )
    variants.append( Variant( [ "--qosDownStrMap=TOS" ], reqs,
        "Set Downstream mapping=TOS, QoS Priority Type=Ceiling & verify QOS counters" ) )
    variants.append( Variant( [ "--qosDownStrMap=TOS", "--qosPriorityType=Fixed" ], reqs,
        "Set Downstream mapping=TOS, QoS Priority Type=Fixed & verify QOS counters" ) )

    ctest = ApQoSTest()
    ctest.runWifiClusterTest( ctest.run, reqs, variants=variants,
                             coverType=WifiClusterTest.ApCoverType.Chipsets )
```

## 7.3 Variant Matrix

| Variant | Arguments | Downstream Map | Priority Type | Description |
|---------|-----------|----------------|---------------|-------------|
| 1 | (none) | DSCP (1) | Ceiling (0) | Default configuration |
| 2 | `--qosPriorityType=Fixed` | DSCP (1) | Fixed (1) | Fixed priority with DSCP |
| 3 | `--qosDownStrMap=TOS` | TOS (2) | Ceiling (0) | TOS mapping with ceiling |
| 4 | `--qosDownStrMap=TOS --qosPriorityType=Fixed` | TOS (2) | Fixed (1) | TOS with fixed priority |

## 7.4 Expected Behavior per Variant

### Variant 1: DSCP + Ceiling (Default)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ Variant 1: DSCP Downstream Mapping + Ceiling Priority                        │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│ Configuration:                                                               │
│   - qosDownStrMap = 1 (DSCP)                                                 │
│   - qosPriorityType = 0 (Ceiling)                                            │
│                                                                              │
│ Expected VAP Flags:                                                          │
│   - iv_qos_prio = 0                                                          │
│   - iv_qos_prio_type = 0                                                     │
│   - iv_qos_dstream = 1                                                       │
│   - iv_qos_ustream_8021p = 1                                                 │
│   - iv_qos_ustream_dscp = 1                                                  │
│                                                                              │
│ Behavior:                                                                    │
│   - Incoming traffic priority determined by DSCP field                       │
│   - Priority capped at Best Effort (2)                                       │
│   - Outgoing traffic marked with 802.1p and DSCP                             │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Variant 2: DSCP + Fixed

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ Variant 2: DSCP Downstream Mapping + Fixed Priority                         │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│ Configuration:                                                               │
│   - qosDownStrMap = 1 (DSCP) - but ignored due to Fixed                      │
│   - qosPriorityType = 1 (Fixed)                                              │
│                                                                              │
│ Expected VAP Flags:                                                          │
│   - iv_qos_prio = 0                                                          │
│   - iv_qos_prio_type = 1                                                     │
│   - iv_qos_dstream = 0 (disabled)                                            │
│   - iv_qos_ustream_8021p = 1                                                 │
│   - iv_qos_ustream_dscp = 1                                                  │
│                                                                              │
│ Behavior:                                                                    │
│   - All traffic gets fixed Best Effort priority                              │
│   - Downstream mapping disabled (DSCP field ignored)                         │
│   - Outgoing traffic marked with 802.1p and DSCP                             │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Variant 3: TOS + Ceiling

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ Variant 3: TOS Downstream Mapping + Ceiling Priority                        │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│ Configuration:                                                               │
│   - qosDownStrMap = 2 (TOS)                                                  │
│   - qosPriorityType = 0 (Ceiling)                                            │
│                                                                              │
│ Expected VAP Flags:                                                          │
│   - iv_qos_prio = 0                                                          │
│   - iv_qos_prio_type = 0                                                     │
│   - iv_qos_dstream = 2                                                       │
│   - iv_qos_ustream_8021p = 1                                                 │
│   - iv_qos_ustream_dscp = 1                                                  │
│                                                                              │
│ Behavior:                                                                    │
│   - Incoming traffic priority determined by TOS field                        │
│   - Priority capped at Best Effort (2)                                       │
│   - Outgoing traffic marked with 802.1p and DSCP                             │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Variant 4: TOS + Fixed

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ Variant 4: TOS Downstream Mapping + Fixed Priority                          │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│ Configuration:                                                               │
│   - qosDownStrMap = 2 (TOS) - but ignored due to Fixed                       │
│   - qosPriorityType = 1 (Fixed)                                              │
│                                                                              │
│ Expected VAP Flags:                                                          │
│   - iv_qos_prio = 0                                                          │
│   - iv_qos_prio_type = 1                                                     │
│   - iv_qos_dstream = 0 (disabled)                                            │
│   - iv_qos_ustream_8021p = 1                                                 │
│   - iv_qos_ustream_dscp = 1                                                  │
│                                                                              │
│ Behavior:                                                                    │
│   - All traffic gets fixed Best Effort priority                              │
│   - Downstream mapping disabled (TOS field ignored)                          │
│   - Outgoing traffic marked with 802.1p and DSCP                             │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

# 8. Configuration Parameters

## 8.1 AP Configuration Parameters

The following parameters are set in the AP configuration file (ap.conf) for QoS:

| Parameter Name | Type | Range | Description |
|----------------|------|-------|-------------|
| `QOS_SSID_PRIORITY` | int | 0-7 | SSID traffic priority |
| `QOS_PRIORITY_TYPE` | int | 0-1 | Ceiling (0) or Fixed (1) |
| `QOS_DOWNSTR_MAP` | int | 0-2 | Disabled (0), DSCP (1), TOS (2) |
| `QOS_UPSTR_MARK_802_1p` | int | 0-1 | 802.1p marking disabled/enabled |
| `QOS_UPSTR_MARK_DSCP_TOS` | int | 0-1 | DSCP/TOS marking disabled/enabled |

## 8.2 Driver-Level Parameters

The following parameters are set at the wireless driver level:

| Parameter Name | Type | Description |
|----------------|------|-------------|
| `iv_qos_prio` | int | VAP QoS priority |
| `iv_qos_prio_type` | int | Priority type (ceiling/fixed) |
| `iv_qos_dstream` | int | Downstream mapping type |
| `iv_qos_ustream_8021p` | int | 802.1p upstream marking |
| `iv_qos_ustream_dscp` | int | DSCP upstream marking |

## 8.3 QoS Configuration Data Model

From `ap/s4models/wificonfig/SsidConfig.tac`:

```tac
QosConfig : Tac::Type() : Tac::Nominal {
   ssidPriority : U8;
   priorityType : U8;
   downstreamMap : U8;
   upstreamMark8021p : U8;
   upstreamMarkDscpTos : U8;
   wmmEnforcePolicyEnable : bool;
   wmmEnable : bool;
   vapMinRate : double;
   vapMaxRate : double;
   vapNonLegacyMaxRate : U8;
   vapMcastMgmtRate : double;
   vapDisable11bRate : bool;
   vapMinRate2G : double;
   vapMinRate5G : double;
   vapMinRate6G : double;
   vapMaxRate2G : double;
   vapMaxRate5G : double;
   vapMaxRate6G : double;
   vapMcastMgmtRate2G : double;
   vapMcastMgmtRate5G : double;
   vapMcastMgmtRate6G : double;
}
```

## 8.4 Configuration Mapping

From `ap/src/go/arista-ap/ardsconfwriter/ssid_qos.go`:

```go
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
    ...
}
```

---

# 9. Test Execution Flow

## 9.1 Complete Test Sequence

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                      Complete Test Execution Sequence                        │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  Step 1: Test Initialization                                                 │
│  ─────────────────────────────                                               │
│  │                                                                           │
│  ├── main() called                                                           │
│  ├── ArosTest.runMeAsRoot() - Ensure root privileges                         │
│  ├── Configure tracing for ApDut, ApConfigLib, ApQoSTest                     │
│  ├── Define test requirements (wifi__ap01__client01)                         │
│  ├── Create 4 test variants                                                  │
│  └── Create ApQoSTest instance                                               │
│                                                                              │
│  Step 2: Test Cluster Setup                                                  │
│  ──────────────────────────                                                  │
│  │                                                                           │
│  ├── runWifiClusterTest() called                                             │
│  ├── Test cluster allocated based on requirements                            │
│  ├── DUTs initialized (AP, Client)                                           │
│  └── Cleanup functions registered                                            │
│                                                                              │
│  Step 3: run() Method Execution                                              │
│  ─────────────────────────────                                               │
│  │                                                                           │
│  ├── Parent run() called (WifiClusterTestBase.run)                           │
│  ├── AP and Client DUTs assigned                                             │
│  ├── AP TAP interfaces created                                               │
│  │                                                                           │
│  ├── Host Server Context Entered                                             │
│  │   ├── HostServerDut created with VLAN config                              │
│  │   ├── HostDhcpService started                                             │
│  │   └── AP connected to Host                                                │
│  │                                                                           │
│  ├── DHCP Configuration                                                      │
│  │   ├── dhcpCommVlanIs(vlanId='u') called                                   │
│  │   ├── validateDhcpConfig() called                                         │
│  │   └── Host IP retrieved                                                   │
│  │                                                                           │
│  ├── SSID Configuration                                                      │
│  │   ├── configureSsid() called with QoS parameters                          │
│  │   │   ├── ssidName: "<ap_name>-qos"                                       │
│  │   │   ├── security: 'wpa-psk'                                             │
│  │   │   ├── qosConfigIs: True                                               │
│  │   │   ├── qosSsidPriority: 2                                              │
│  │   │   ├── qosPriorityType: 0 or 1                                         │
│  │   │   ├── qosDownStrMap: 1 or 2                                           │
│  │   │   ├── qosUpStrMark8021p: 1                                            │
│  │   │   └── qosUpStrMarkDscpTos: 1                                          │
│  │   └── vlanBridgeSanityCheck() called                                      │
│  │                                                                           │
│  ├── QoS Flag Validation                                                     │
│  │   └── validateQoSFlags() called                                           │
│  │       ├── Query iv_qos_prio                                               │
│  │       ├── Query iv_qos_prio_type                                          │
│  │       ├── Query iv_qos_dstream                                            │
│  │       ├── Query iv_qos_ustream_8021p                                      │
│  │       └── Query iv_qos_ustream_dscp                                       │
│  │                                                                           │
│  ├── Client Connection Context Entered                                       │
│  │   ├── connectClient() called                                              │
│  │   ├── Client connects to SSID                                             │
│  │   ├── DHCP IP assigned                                                    │
│  │   └── Connection verified                                                 │
│  │                                                                           │
│  ├── QoS Counter Validation                                                  │
│  │   └── validateQoSCounters() called                                        │
│  │       ├── Query initial Best Effort counter                               │
│  │       ├── Execute ping test (50 packets)                                  │
│  │       ├── Query updated Best Effort counter                               │
│  │       └── Verify counter increased                                        │
│  │                                                                           │
│  └── Cleanup                                                                 │
│      ├── Client disconnected (context exit)                                  │
│      ├── Host services stopped (context exit)                                │
│      └── Success message logged                                              │
│                                                                              │
│  Step 4: Test Completion                                                     │
│  ───────────────────────                                                     │
│  │                                                                           │
│  ├── Cleanup functions executed                                              │
│  ├── Test results reported                                                   │
│  └── Test cluster released                                                   │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

## 9.2 Timing Diagram

```
Time ──────────────────────────────────────────────────────────────────────────▶

     │ Init │ Cluster │  Host  │  SSID  │  QoS   │ Client │  QoS   │ Cleanup │
     │      │  Setup  │ Setup  │ Config │ Flags  │ Connect│Counters│         │
     │      │         │        │        │        │        │        │         │
     ├──────┼─────────┼────────┼────────┼────────┼────────┼────────┼─────────┤
     │ ~1s  │  ~30s   │  ~20s  │  ~10s  │  ~5s   │  ~30s  │  ~15s  │  ~10s   │
     │      │         │        │        │        │        │        │         │
     └──────┴─────────┴────────┴────────┴────────┴────────┴────────┴─────────┘

     Total estimated time: ~2 minutes per variant
     Total for all 4 variants: ~8 minutes
```

---

# 10. Dependencies and Imports

## 10.1 Import Statements

```python
import Tracing
import ArosTest
from WifiClusterReqs import WiFiTestReqs
import WifiClusterTest
import HostServicesLib
from TestClusterLib import argparser, Variant
import ApTestLib
import ApCommonLib
import Tac
import re
import ApDhcpHelper
```

## 10.2 Module Descriptions

| Module | Purpose | Key Functions/Classes |
|--------|---------|----------------------|
| `Tracing` | Logging and trace output | `Handle`, `trace0` |
| `ArosTest` | Test framework utilities | `runMeAsRoot`, `desiredTracingIs` |
| `WifiClusterReqs` | Test requirements definitions | `WiFiTestReqs` |
| `WifiClusterTest` | Base test class | `WifiClusterTestBase`, `ApCoverType` |
| `HostServicesLib` | Host server utilities | `HostServerDut`, `HostDhcpService` |
| `TestClusterLib` | Test cluster utilities | `argparser`, `Variant` |
| `ApTestLib` | AP test utilities | `connectClient`, `DEF_VLANNET_YAML` |
| `ApCommonLib` | Common AP utilities | `connectedApHostDuts` |
| `Tac` | Wait/polling utilities | `waitFor` |
| `re` | Regular expressions | `search` |
| `ApDhcpHelper` | DHCP validation | `validateDhcpConfig` |

## 10.3 Dependency Graph

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          Dependency Graph                                    │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│                           ApQoSTest.py                                       │
│                               │                                              │
│         ┌─────────────────────┼─────────────────────┐                        │
│         │                     │                     │                        │
│         ▼                     ▼                     ▼                        │
│   ┌───────────┐        ┌───────────┐        ┌───────────┐                   │
│   │ ArosTest  │        │WifiCluster│        │HostServic │                   │
│   │           │        │   Test    │        │   esLib   │                   │
│   └───────────┘        └───────────┘        └───────────┘                   │
│         │                     │                     │                        │
│         │                     │                     │                        │
│         ▼                     ▼                     ▼                        │
│   ┌───────────┐        ┌───────────┐        ┌───────────┐                   │
│   │  Tracing  │        │ ApTestLib │        │ApCommonLib│                   │
│   └───────────┘        └───────────┘        └───────────┘                   │
│                               │                     │                        │
│                               │                     │                        │
│                               ▼                     ▼                        │
│                        ┌───────────┐        ┌───────────┐                   │
│                        │ApConfigLib│        │ApDhcpHelpr│                   │
│                        └───────────┘        └───────────┘                   │
│                               │                                              │
│                               ▼                                              │
│                        ┌───────────┐                                        │
│                        │   ApDut   │                                        │
│                        └───────────┘                                        │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```


---

# 11. Test Requirements

## 11.1 Hardware Requirements

### 11.1.1 Required Equipment

| Component | Quantity | Specifications |
|-----------|----------|----------------|
| Arista Access Point | 1 | Any supported chipset |
| WiFi Client Device | 1 | Linux-based with wireless adapter |
| Network Switch | 1 | VLAN-capable |
| Host Server | 1 | DHCP service capable |

### 11.1.2 Network Topology

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                       Required Test Topology                                 │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│                          ┌─────────────────┐                                 │
│                          │   Host Server   │                                 │
│                          │  (DHCP Service) │                                 │
│                          └────────┬────────┘                                 │
│                                   │                                          │
│                                   │ Ethernet                                 │
│                                   │                                          │
│                          ┌────────┴────────┐                                 │
│                          │  Network Switch │                                 │
│                          │   (VLAN-aware)  │                                 │
│                          └────────┬────────┘                                 │
│                                   │                                          │
│                    ┌──────────────┼──────────────┐                           │
│                    │              │              │                           │
│            ┌───────┴───────┐     │      ┌───────┴───────┐                    │
│            │   Access      │     │      │    Test       │                    │
│            │   Point       │     │      │   Controller  │                    │
│            └───────┬───────┘     │      └───────────────┘                    │
│                    │             │                                           │
│                    │ WiFi        │                                           │
│                    │             │                                           │
│            ┌───────┴───────┐     │                                           │
│            │  WiFi Client  │─────┘                                           │
│            │    Device     │                                                 │
│            └───────────────┘                                                 │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

## 11.2 Software Requirements

### 11.2.1 AP Software Requirements

| Component | Version | Description |
|-----------|---------|-------------|
| ArosOS | Latest | Arista AP Operating System |
| QoS Feature | Enabled | QoS capability must be present |
| Wireless Driver | Compatible | Must support iv_qos_* parameters |

### 11.2.2 Test Framework Requirements

| Component | Version | Description |
|-----------|---------|-------------|
| Python | 3.6+ | Test script interpreter |
| ArosTest | Latest | Arista test framework |
| WifiClusterTest | Latest | WiFi cluster testing utilities |

### 11.2.3 Client Requirements

| Component | Description |
|-----------|-------------|
| Operating System | Linux-based |
| Wireless Adapter | WPA2-capable |
| wpa_supplicant | For WiFi connection management |
| DHCP Client | dhclient or similar |

## 11.3 Test Cluster Requirements

### 11.3.1 WiFiTestReqs Definition

```python
# From WifiClusterReqs.py
wifi__ap01__client01 = WiFiTestReqs(
    name="wifi__ap01__client01",
    description="1 AP and 1 Client",
    aps=1,
    clients=1
)
```

### 11.3.2 Resource Allocation

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    Test Cluster Resource Allocation                          │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │ Test Cluster                                                         │    │
│  ├─────────────────────────────────────────────────────────────────────┤    │
│  │                                                                      │    │
│  │  ┌──────────────────────────────────────────────────────────────┐   │    │
│  │  │ AP Pool                                                       │   │    │
│  │  ├──────────────────────────────────────────────────────────────┤   │    │
│  │  │ ┌─────────┐ ┌─────────┐ ┌─────────┐         ┌─────────┐      │   │    │
│  │  │ │  AP 1   │ │  AP 2   │ │  AP 3   │   ...   │  AP N   │      │   │    │
│  │  │ │(Allocd) │ │(Avail)  │ │(Avail)  │         │(Avail)  │      │   │    │
│  │  │ └─────────┘ └─────────┘ └─────────┘         └─────────┘      │   │    │
│  │  └──────────────────────────────────────────────────────────────┘   │    │
│  │                                                                      │    │
│  │  ┌──────────────────────────────────────────────────────────────┐   │    │
│  │  │ Client Pool                                                   │   │    │
│  │  ├──────────────────────────────────────────────────────────────┤   │    │
│  │  │ ┌─────────┐ ┌─────────┐ ┌─────────┐         ┌─────────┐      │   │    │
│  │  │ │Client 1 │ │Client 2 │ │Client 3 │   ...   │Client M │      │   │    │
│  │  │ │(Allocd) │ │(Avail)  │ │(Avail)  │         │(Avail)  │      │   │    │
│  │  │ └─────────┘ └─────────┘ └─────────┘         └─────────┘      │   │    │
│  │  └──────────────────────────────────────────────────────────────┘   │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

# 12. Error Handling

## 12.1 Assertion Patterns

The test uses various assertion patterns to validate QoS configuration:

### 12.1.1 Regular Expression Assertions

```python
# Pattern: Validate flag value from iwpriv output
ret = re.search(r'iv_qos_prio:(\d+)', retOut)
Tac.assertEqual(int(ret.group(1)), 0, "iv_qos_prio")
```

### 12.1.2 Counter Comparison Assertions

```python
# Pattern: Verify counter increased after traffic
Tac.assertGreater(beCounterAfter, beCounter,
    "BE counter should increase")
```

### 12.1.3 Timeout-based Assertions

```python
# Pattern: Wait for condition with timeout
Tac.waitFor(description="connect client",
            fn=connectClient,
            timeout=60)
```

## 12.2 Failure Modes

### 12.2.1 QoS Flag Validation Failures

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                      QoS Flag Validation Failure Modes                       │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  Failure Type              │ Possible Causes          │ Resolution           │
│  ─────────────────────────┼──────────────────────────┼─────────────────────  │
│  iv_qos_prio mismatch     │ Configuration not applied│ Check SSID config    │
│  iv_qos_prio_type mismatch│ Priority type setting    │ Verify variant args  │
│  iv_qos_dstream mismatch  │ Downstream map setting   │ Check Fixed mode     │
│  iv_qos_ustream_* mismatch│ Upstream marking config  │ Verify QoS settings  │
│  Regex match failure      │ Command output changed   │ Update regex pattern │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 12.2.2 Counter Validation Failures

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                     Counter Validation Failure Modes                         │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  Failure Type              │ Possible Causes          │ Resolution           │
│  ─────────────────────────┼──────────────────────────┼─────────────────────  │
│  Counter didn't increase  │ Traffic not flowing      │ Check connectivity   │
│  Counter decreased        │ Counter overflow/reset   │ Increase traffic     │
│  Regex parse failure      │ Output format changed    │ Update regex pattern │
│  Wrong queue counted      │ QoS misconfiguration     │ Verify QoS mapping   │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

## 12.3 Exception Handling

### 12.3.1 Context Manager Exception Handling

```python
# Context managers ensure cleanup on failure
with HostServicesLib.HostServerDut(...) as hostServer:
    with HostServicesLib.HostDhcpService(...):
        # If any exception occurs here, cleanup is automatic
        try:
            self.validateQoSFlags()
        except AssertionError as e:
            t0(f"QoS validation failed: {e}")
            raise
```

### 12.3.2 Connection Failure Handling

```python
# Wait with description for better error messages
with ApTestLib.connectClient(client, ...) as clientSession:
    if not clientSession.isConnected():
        raise TestFailure("Client failed to connect to SSID")
```

---

# 13. Troubleshooting Guide

## 13.1 Common Issues and Solutions

### 13.1.1 SSID Configuration Failures

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ Issue: SSID fails to configure                                               │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│ Symptoms:                                                                    │
│   - configureSsid() throws exception                                         │
│   - SSID not visible on AP                                                   │
│   - VAP not created                                                          │
│                                                                              │
│ Diagnostic Steps:                                                            │
│   1. Check AP connectivity                                                   │
│   2. Verify AP is in correct state                                           │
│   3. Check for conflicting SSID configurations                               │
│   4. Review AP logs for errors                                               │
│                                                                              │
│ Solutions:                                                                   │
│   - Restart AP if in bad state                                               │
│   - Clear existing SSID configurations                                       │
│   - Verify VLAN configuration                                                │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 13.1.2 Client Connection Failures

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ Issue: Client fails to connect to SSID                                       │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│ Symptoms:                                                                    │
│   - connectClient() times out                                                │
│   - Client can't see SSID                                                    │
│   - Authentication failures                                                  │
│                                                                              │
│ Diagnostic Steps:                                                            │
│   1. Verify SSID is broadcasting                                             │
│   2. Check PSK configuration                                                 │
│   3. Verify client wireless interface is up                                  │
│   4. Check for RF interference                                               │
│                                                                              │
│ Solutions:                                                                   │
│   - Move client closer to AP                                                 │
│   - Verify PSK matches (wifiPsk())                                           │
│   - Restart client wireless interface                                        │
│   - Check wpa_supplicant logs                                                │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 13.1.3 QoS Counter Not Increasing

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ Issue: Best Effort counter doesn't increase after ping                       │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│ Symptoms:                                                                    │
│   - beCounterAfter == beCounter                                              │
│   - Assertion fails in validateQoSCounters()                                 │
│                                                                              │
│ Diagnostic Steps:                                                            │
│   1. Verify ping is actually reaching the AP                                 │
│   2. Check which queue the traffic is being classified to                    │
│   3. Verify QoS configuration is applied                                     │
│   4. Check for packet drops                                                  │
│                                                                              │
│ Solutions:                                                                   │
│   - Increase ping count                                                      │
│   - Verify client has IP address                                             │
│   - Check VLAN configuration                                                 │
│   - Review QoS priority settings                                             │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

## 13.2 Debug Commands

### 13.2.1 AP Debug Commands

```bash
# Check VAP QoS settings
iwpriv ath0 get_iv_qos_prio
iwpriv ath0 get_iv_qos_prio_type
iwpriv ath0 get_iv_qos_dstream
iwpriv ath0 get_iv_qos_ustream_8021p
iwpriv ath0 get_iv_qos_ustream_dscp

# Check QoS counters
cat /sys/kernel/debug/ieee80211/phy0/netdev:ath0/stations/*/qos_stats

# View SSID configuration
cat /tmp/ap.conf | grep QOS

# Check VAP status
iwconfig ath0
```

### 13.2.2 Client Debug Commands

```bash
# Check wireless connection
iwconfig wlan0
wpa_cli status

# Check IP address
ip addr show wlan0

# Test connectivity
ping -c 5 <host_ip>

# View DHCP lease
cat /var/lib/dhcp/dhclient.leases
```

---

# 14. Related Components

## 14.1 Related Test Files

| File | Purpose | Relationship |
|------|---------|--------------|
| `ApQoSMappingTest.py` | Tests QoS DSCP/TOS mapping | Tests specific mapping tables |
| `ApWmmTest.py` | Tests WMM (WiFi Multimedia) | Related QoS feature |
| `ApVlanBridgeTest.py` | Tests VLAN bridging | Used for traffic isolation |
| `ApClientConnectTest.py` | Tests client connection | Basic connectivity test |
| `ApDhcpTest.py` | Tests DHCP functionality | Related network configuration |

## 14.2 Configuration Files

| File | Purpose |
|------|---------|
| `ap.conf` | Main AP configuration file |
| `hostapd.conf` | Hostapd configuration |
| `wpa_supplicant.conf` | Client WiFi configuration |
| `SsidConfig.tac` | SSID data model definition |

## 14.3 Library Dependencies

### 14.3.1 WifiClusterTest Module

```python
# Key methods used from WifiClusterTest
class WifiClusterTestBase:
    def run(self):
        """Base test execution method"""
        pass

    def configureSsid(self, apEdut, ssidName, **kwargs):
        """Configure SSID with various parameters"""
        pass

    def vlanBridgeSanityCheck(self, apEdut):
        """Verify VLAN bridge configuration"""
        pass
```

### 14.3.2 ApTestLib Module

```python
# Key functions from ApTestLib
def connectClient(client, ssidName, security, psk):
    """Connect client to specified SSID"""
    pass

def wifiPsk():
    """Return default WiFi PSK"""
    pass

DEF_VLANNET_YAML = "default_vlan_network.yaml"
```




---

# 15. Scapy Library Reference

## 15.1 Introduction to Scapy

### 15.1.1 What is Scapy?

Scapy is a powerful Python-based interactive packet manipulation library and tool. It allows
you to:

- **Forge** packets from scratch with any protocol
- **Decode** packets from various network captures
- **Send** packets on the wire
- **Capture** packets from network interfaces
- **Match** requests and replies
- **Dissect** packets into their protocol layers

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                            Scapy Overview                                    │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │                        Scapy Capabilities                              │  │
│  ├───────────────────────────────────────────────────────────────────────┤  │
│  │                                                                        │  │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐   │  │
│  │  │   Packet    │  │   Packet    │  │   Packet    │  │   Network   │   │  │
│  │  │  Creation   │  │   Parsing   │  │  Sending    │  │  Sniffing   │   │  │
│  │  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘   │  │
│  │         │                │                │                │          │  │
│  │         └────────────────┼────────────────┼────────────────┘          │  │
│  │                          │                │                           │  │
│  │                    ┌─────┴────────────────┴─────┐                     │  │
│  │                    │      Protocol Stacks       │                     │  │
│  │                    ├────────────────────────────┤                     │  │
│  │                    │ Ethernet, IP, TCP, UDP,    │                     │  │
│  │                    │ ICMP, ARP, DNS, HTTP,      │                     │  │
│  │                    │ 802.11, IGMP, MLD, etc.    │                     │  │
│  │                    └────────────────────────────┘                     │  │
│  │                                                                        │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 15.1.2 Why Use Scapy?

| Feature | Benefit |
|---------|---------|
| Interactive | Test packets in Python REPL |
| Flexible | Create any packet type |
| Protocol-aware | Automatic protocol dissection |
| Programmable | Integrate into test frameworks |
| Cross-platform | Works on Linux, Windows, macOS |

## 15.2 Installation and Setup

### 15.2.1 Installation Methods

```bash
# Using pip
pip install scapy

# Using apt (Debian/Ubuntu)
apt-get install python3-scapy

# Using conda
conda install -c conda-forge scapy
```

### 15.2.2 Basic Import

```python
# Import entire Scapy library
from scapy.all import *

# Import specific layers
from scapy.layers.inet import IP, ICMP, TCP, UDP
from scapy.layers.l2 import Ether, ARP
from scapy.layers.igmp import IGMP
```

### 15.2.3 Running with Root Privileges

```python
# Scapy requires root for packet sending/sniffing
import os
if os.geteuid() != 0:
    print("Warning: Run as root for full functionality")
```

## 15.3 Core Concepts

### 15.3.1 Packet Layers

Scapy uses a layered approach where packets are built by stacking protocol layers:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         Packet Layer Structure                               │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  Application Data                                                            │
│  ─────────────────────────────────────────────────────────────────────────  │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │ Layer 7: Application (HTTP, DNS, etc.)                              │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │ Layer 4: Transport (TCP, UDP)                                        │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │ Layer 3: Network (IP, ICMP, IGMP)                                    │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │ Layer 2: Data Link (Ethernet, 802.11)                                │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │ Layer 1: Physical (bits on wire)                                     │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 15.3.2 Layer Stacking with `/` Operator

```python
# Create a simple ICMP ping packet
packet = Ether() / IP(dst="192.168.1.1") / ICMP()

# Create a TCP SYN packet
packet = IP(dst="192.168.1.1") / TCP(dport=80, flags="S")

# Create an Ethernet frame with IP and UDP
packet = Ether(dst="ff:ff:ff:ff:ff:ff") / IP(dst="255.255.255.255") / UDP(dport=67)
```

### 15.3.3 Packet Field Access

```python
# Create a packet
pkt = IP(dst="10.0.0.1", ttl=64) / ICMP(type=8)

# Access fields
print(pkt[IP].dst)       # "10.0.0.1"
print(pkt[IP].ttl)       # 64
print(pkt[ICMP].type)    # 8

# Modify fields
pkt[IP].ttl = 128

# Check if layer exists
if pkt.haslayer(ICMP):
    print("Packet has ICMP layer")
```

## 15.4 Common Operations

### 15.4.1 Creating Packets

```python
# Simple IP packet
ip_pkt = IP(dst="192.168.1.1", src="192.168.1.100")

# ICMP Echo Request (Ping)
ping = IP(dst="192.168.1.1") / ICMP(type=8, code=0)

# TCP SYN packet
syn = IP(dst="192.168.1.1") / TCP(dport=80, flags="S", seq=1000)

# UDP packet with payload
udp = IP(dst="192.168.1.1") / UDP(dport=53) / DNS(qd=DNSQR(qname="example.com"))

# ARP Request
arp = Ether(dst="ff:ff:ff:ff:ff:ff") / ARP(pdst="192.168.1.1")
```

### 15.4.2 Sending Packets

```python
# Send at Layer 3 (Scapy handles Ethernet)
send(IP(dst="192.168.1.1") / ICMP())

# Send at Layer 2 (you provide Ethernet)
sendp(Ether() / IP(dst="192.168.1.1") / ICMP())

# Send and receive response
ans, unans = sr(IP(dst="192.168.1.1") / ICMP(), timeout=2)

# Send one packet and receive one response
response = sr1(IP(dst="192.168.1.1") / ICMP(), timeout=2)
```

### 15.4.3 Sniffing Packets

```python
# Capture 10 packets on interface
packets = sniff(iface="eth0", count=10)

# Capture with filter
packets = sniff(iface="eth0", filter="icmp", count=10)

# Capture with callback
def packet_callback(pkt):
    print(pkt.summary())

sniff(iface="eth0", prn=packet_callback, count=10)

# Stop after timeout
packets = sniff(iface="eth0", timeout=5)
```

### 15.4.4 Reading/Writing PCAP Files

```python
# Read packets from pcap file
from scapy.utils import rdpcap, wrpcap

packets = rdpcap("capture.pcap")

# Process packets
for pkt in packets:
    if pkt.haslayer(IP):
        print(f"IP: {pkt[IP].src} -> {pkt[IP].dst}")

# Write packets to pcap file
wrpcap("output.pcap", packets)
```

## 15.5 Protocol-Specific Examples

### 15.5.1 ICMP Operations

```python
from scapy.layers.inet import IP, ICMP

# Create ping packet
ping = IP(dst="192.168.1.1") / ICMP(type=8, code=0, id=1, seq=1) / b"Hello"

# Send ping and get response
reply = sr1(ping, timeout=2)

if reply:
    print(f"Reply from {reply[IP].src}")
    print(f"TTL: {reply[IP].ttl}")
    print(f"Time: {reply.time - ping.time} seconds")
```

### 15.5.2 IGMP Operations (Used in AP Testing)

```python
from scapy.contrib.igmp import IGMP
from scapy.layers.inet import IP

# IGMP Membership Query
query = IP(dst="224.0.0.1", ttl=1) / IGMP(type=0x11)

# IGMP Membership Report (v2)
report = IP(dst="224.1.1.1", ttl=1) / IGMP(type=0x16, gaddr="224.1.1.1")

# IGMP Leave Group
leave = IP(dst="224.0.0.2", ttl=1) / IGMP(type=0x17, gaddr="224.1.1.1")
```

### 15.5.3 MLD Operations (IPv6 Multicast)

```python
from scapy.contrib.igmpv3 import IGMPv3
from scapy.layers.inet6 import IPv6, ICMPv6MLQuery, ICMPv6MLReport

# MLDv1 Query
query = IPv6(dst="ff02::1") / ICMPv6MLQuery()

# MLDv1 Report
report = IPv6(dst="ff02::1:ff00:1") / ICMPv6MLReport(mladdr="ff02::1:ff00:1")
```

## 15.6 Scapy in the AP Testing Codebase

### 15.6.1 Usage in IgmpSnoopTest.py

The Arista AP testing framework uses Scapy for IGMP/MLD packet analysis:

```python
# From autotest/WifiClusterTest/ctest/IgmpSnoopTest.py
from scapy.utils import rdpcap
from scapy.contrib.igmp import IGMP
from scapy.contrib.igmpv3 import IGMPv3, IGMPv3mr, IGMPv3gr
from scapy.layers.inet6 import ICMPv6MLQuery, ICMPv6MLReport

def analyzeIgmpPackets(pcapFile):
    """Analyze IGMP packets from a capture file"""
    packets = rdpcap(pcapFile)

    igmpPackets = []
    for pkt in packets:
        if pkt.haslayer(IGMP):
            igmpPackets.append(pkt)
        elif pkt.haslayer(IGMPv3):
            igmpPackets.append(pkt)

    return igmpPackets
```

### 15.6.2 Usage in ApPacketCaptureGNOITest.py

```python
# From autotest/WifiClusterTest/ctest/ApPacketCaptureGNOITest.py
from scapy.layers.l2 import Ether
from scapy.layers.inet import IP, ICMP
from scapy.utils import rdpcap

def verifyPcapContents(pcapPath, expectedSrcIp, expectedDstIp):
    """Verify that pcap contains expected ICMP packets"""
    packets = rdpcap(pcapPath)

    for pkt in packets:
        if pkt.haslayer(IP) and pkt.haslayer(ICMP):
            if pkt[IP].src == expectedSrcIp and pkt[IP].dst == expectedDstIp:
                return True

    return False
```

### 15.6.3 Integration Pattern for WiFi Testing

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    Scapy Integration in WiFi AP Testing                      │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │ Test Flow with Scapy                                                 │    │
│  ├─────────────────────────────────────────────────────────────────────┤    │
│  │                                                                      │    │
│  │  1. Configure AP with specific settings                             │    │
│  │     └── SSID, VLAN, QoS, Multicast settings                         │    │
│  │                                                                      │    │
│  │  2. Start packet capture on AP                                      │    │
│  │     └── Using tcpdump or similar                                    │    │
│  │                                                                      │    │
│  │  3. Generate specific traffic from client                           │    │
│  │     └── IGMP joins, multicast data, etc.                            │    │
│  │                                                                      │    │
│  │  4. Stop capture and retrieve pcap file                             │    │
│  │     └── Download from AP                                            │    │
│  │                                                                      │    │
│  │  5. Analyze pcap with Scapy                                         │    │
│  │     └── rdpcap() to read                                            │    │
│  │     └── Iterate and check layers                                    │    │
│  │     └── Verify expected packets present                             │    │
│  │                                                                      │    │
│  │  6. Assert on packet contents                                       │    │
│  │     └── Check headers, fields, counts                               │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

## 15.7 Advanced Scapy Features

### 15.7.1 Custom Protocol Layers

```python
from scapy.packet import Packet
from scapy.fields import *

class CustomQoSHeader(Packet):
    name = "Custom QoS Header"
    fields_desc = [
        BitField("priority", 0, 3),
        BitField("dei", 0, 1),
        BitField("vlan_id", 0, 12),
        XShortField("ethertype", 0x0800)
    ]

# Use custom layer
pkt = Ether() / CustomQoSHeader(priority=5, vlan_id=100) / IP() / ICMP()
```

### 15.7.2 Packet Matching and Filtering

```python
# Filter packets by protocol
icmp_packets = [pkt for pkt in packets if pkt.haslayer(ICMP)]

# Filter by field value
high_priority = [pkt for pkt in packets
                 if pkt.haslayer(IP) and pkt[IP].tos >> 5 >= 4]

# Filter by source/destination
from_client = [pkt for pkt in packets
               if pkt.haslayer(IP) and pkt[IP].src == "192.168.1.100"]
```

### 15.7.3 Packet Manipulation for QoS Testing

```python
# Create packet with specific DSCP value
# DSCP is in upper 6 bits of TOS field
dscp_value = 46  # Expedited Forwarding
tos = dscp_value << 2

pkt = IP(dst="192.168.1.1", tos=tos) / UDP(dport=5060) / b"VoIP data"

# Verify DSCP in received packet
def verify_dscp(pkt, expected_dscp):
    if pkt.haslayer(IP):
        actual_dscp = pkt[IP].tos >> 2
        return actual_dscp == expected_dscp
    return False
```

## 15.8 Scapy Quick Reference

### 15.8.1 Common Functions

| Function | Description |
|----------|-------------|
| `send(pkt)` | Send packet at Layer 3 |
| `sendp(pkt)` | Send packet at Layer 2 |
| `sr(pkt)` | Send and receive at Layer 3 |
| `srp(pkt)` | Send and receive at Layer 2 |
| `sr1(pkt)` | Send and receive one reply |
| `sniff(...)` | Capture packets |
| `rdpcap(file)` | Read pcap file |
| `wrpcap(file, pkts)` | Write pcap file |
| `ls(layer)` | List layer fields |
| `pkt.show()` | Display packet details |
| `pkt.summary()` | One-line packet summary |
| `hexdump(pkt)` | Show packet hex dump |

### 15.8.2 Common Layers

| Layer | Import | Description |
|-------|--------|-------------|
| `Ether` | `scapy.layers.l2` | Ethernet frame |
| `IP` | `scapy.layers.inet` | IPv4 packet |
| `IPv6` | `scapy.layers.inet6` | IPv6 packet |
| `TCP` | `scapy.layers.inet` | TCP segment |
| `UDP` | `scapy.layers.inet` | UDP datagram |
| `ICMP` | `scapy.layers.inet` | ICMP message |
| `ARP` | `scapy.layers.l2` | ARP request/reply |
| `DNS` | `scapy.layers.dns` | DNS query/response |
| `IGMP` | `scapy.contrib.igmp` | IGMP message |
| `Dot11` | `scapy.layers.dot11` | 802.11 WiFi frame |

### 15.8.3 DSCP Value Reference

| DSCP Name | Value | Binary | Description |
|-----------|-------|--------|-------------|
| Default | 0 | 000000 | Best Effort |
| CS1 | 8 | 001000 | Scavenger |
| AF11 | 10 | 001010 | Assured Forwarding |
| AF12 | 12 | 001100 | Assured Forwarding |
| AF13 | 14 | 001110 | Assured Forwarding |
| CS2 | 16 | 010000 | OAM |
| AF21 | 18 | 010010 | Assured Forwarding |
| AF22 | 20 | 010100 | Assured Forwarding |
| AF23 | 22 | 010110 | Assured Forwarding |
| CS3 | 24 | 011000 | Signaling |
| AF31 | 26 | 011010 | Assured Forwarding |
| AF32 | 28 | 011100 | Assured Forwarding |
| AF33 | 30 | 011110 | Assured Forwarding |
| CS4 | 32 | 100000 | Realtime |
| AF41 | 34 | 100010 | Assured Forwarding |
| AF42 | 36 | 100100 | Assured Forwarding |
| AF43 | 38 | 100110 | Assured Forwarding |
| CS5 | 40 | 101000 | Broadcast Video |
| EF | 46 | 101110 | Expedited Forwarding |
| CS6 | 48 | 110000 | Network Control |
| CS7 | 56 | 111000 | Network Control |


---

# 16. Best Practices

## 16.1 Testing Guidelines

### 16.1.1 Test Design Principles

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         Test Design Best Practices                           │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  1. ISOLATION                                                                │
│     ─────────────────────────────────────────────────────────────────────   │
│     - Each test should be independent                                        │
│     - Use context managers for resource cleanup                              │
│     - Don't rely on state from previous tests                                │
│                                                                              │
│  2. REPEATABILITY                                                            │
│     ─────────────────────────────────────────────────────────────────────   │
│     - Tests should produce same results on repeated runs                     │
│     - Use deterministic configurations                                       │
│     - Avoid timing-dependent assertions                                      │
│                                                                              │
│  3. CLARITY                                                                  │
│     ─────────────────────────────────────────────────────────────────────   │
│     - Use descriptive assertion messages                                     │
│     - Log important state transitions                                        │
│     - Document expected behavior                                             │
│                                                                              │
│  4. COVERAGE                                                                 │
│     ─────────────────────────────────────────────────────────────────────   │
│     - Test all configuration combinations                                    │
│     - Use variants for parameter variations                                  │
│     - Include both positive and negative tests                               │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 16.1.2 QoS Testing Recommendations

| Recommendation | Rationale |
|----------------|-----------|
| Verify flags before traffic | Ensures configuration is applied |
| Use sufficient traffic volume | Counter changes may be small |
| Test all priority levels | Complete coverage |
| Test boundary conditions | Edge cases often fail |
| Validate both directions | Upstream and downstream |

## 16.2 Code Organization

### 16.2.1 Test Structure Template

```python
class MyWifiTest(WifiClusterTest.WifiClusterTestBase):
    """
    Test class docstring describing:
    - Purpose of the test
    - What is being validated
    - Expected outcomes
    """

    # Class-level metadata
    tags = [ "WifiAPNet" ]

    def __init__(self):
        """Initialize test with default options"""
        WifiClusterTest.WifiClusterTestBase.__init__(self)
        # Add custom options
        self.argparser.addOption("--customOption",
                                 type=str,
                                 default="value")

    def validateConfiguration(self):
        """Validate that configuration was applied correctly"""
        pass

    def validateBehavior(self):
        """Validate that behavior matches expectations"""
        pass

    def run(self):
        """Main test execution"""
        WifiClusterTest.WifiClusterTestBase.run(self)

        # 1. Setup
        # 2. Configure
        # 3. Validate configuration
        # 4. Validate behavior
        # 5. Cleanup (via context managers)
```

### 16.2.2 Naming Conventions

| Element | Convention | Example |
|---------|------------|---------|
| Test class | `Ap&lt;Feature&gt;Test` | `ApQoSTest` |
| Validation method | `validate&lt;What&gt;()` | `validateQoSFlags()` |
| Helper method | `&lt;action&gt;&lt;Object&gt;()` | `getQoSCounter()` |
| Test file | `Ap&lt;Feature&gt;Test.py` | `ApQoSTest.py` |

## 16.3 Resource Management

### 16.3.1 Context Manager Usage

```python
# Good: Use context managers for cleanup
with HostServicesLib.HostServerDut(...) as hostServer:
    with HostServicesLib.HostDhcpService(...):
        with ApTestLib.connectClient(...):
            # Test code here
            pass
# Automatic cleanup on exit

# Bad: Manual cleanup (error-prone)
hostServer = HostServicesLib.HostServerDut(...)
try:
    # Test code
    pass
finally:
    hostServer.cleanup()  # May not run on exception
```

### 16.3.2 Timeout Handling

```python
# Good: Use Tac.waitFor with description
Tac.waitFor(
    description="wait for client connection",
    fn=lambda: client.isConnected(),
    timeout=60
)

# Bad: Simple sleep (wastes time or may timeout)
time.sleep(30)
if not client.isConnected():
    raise Exception("Client not connected")
```

---

# 17. Examples and Use Cases

## 17.1 Complete Test Example

### 17.1.1 Minimal QoS Test

```python
#!/usr/bin/env python
# Copyright (c) 2024 Arista Networks, Inc.

import ArosTest
from WifiClusterReqs import WiFiTestReqs
import WifiClusterTest
from TestClusterLib import Variant

class MinimalQoSTest(WifiClusterTest.WifiClusterTestBase):
    """Minimal example of a QoS test"""

    tags = [ "WifiAPNet" ]

    def run(self):
        WifiClusterTest.WifiClusterTestBase.run(self)

        apEdut = self.testCluster.apEduts()[0]

        # Configure SSID with QoS
        ssidName = f"{apEdut.name()}-test"
        self.configureSsid(
            apEdut,
            ssidName,
            security='wpa-psk',
            qosConfigIs=True,
            qosSsidPriority=2
        )

        # Verify configuration applied
        assert self.getQoSPriority(apEdut) == 2

def main():
    ArosTest.runMeAsRoot()
    reqs = WiFiTestReqs.wifi__ap01__client01

    ctest = MinimalQoSTest()
    ctest.runWifiClusterTest(ctest.run, reqs)

if __name__ == "__main__":
    main()
```

## 17.2 Use Case Scenarios

### 17.2.1 Enterprise Voice/Video QoS

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                  Use Case: Enterprise Voice/Video QoS                        │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  Scenario:                                                                   │
│  Configure AP to prioritize VoIP and video conferencing traffic over        │
│  general data traffic.                                                       │
│                                                                              │
│  Configuration:                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │ SSID: "Corporate-Voice"                                             │    │
│  │ Priority: 6 (Voice)                                                 │    │
│  │ Priority Type: Ceiling                                              │    │
│  │ Downstream Mapping: DSCP                                            │    │
│  │ Upstream 802.1p: Enabled                                            │    │
│  │ Upstream DSCP: Enabled                                              │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  Expected Behavior:                                                          │
│  - VoIP traffic (DSCP EF/46) gets priority 6                                │
│  - Video traffic (DSCP AF41/34) gets priority 4                             │
│  - Best effort traffic stays at priority 0                                   │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 17.2.2 Guest Network Throttling

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    Use Case: Guest Network Throttling                        │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  Scenario:                                                                   │
│  Configure guest SSID to always use Best Effort priority regardless of      │
│  what clients request.                                                       │
│                                                                              │
│  Configuration:                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │ SSID: "Guest-WiFi"                                                  │    │
│  │ Priority: 0 (Best Effort)                                           │    │
│  │ Priority Type: Fixed                                                │    │
│  │ Downstream Mapping: Disabled (ignored with Fixed)                   │    │
│  │ Upstream 802.1p: Disabled                                           │    │
│  │ Upstream DSCP: Disabled                                             │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  Expected Behavior:                                                          │
│  - All guest traffic gets BE priority                                        │
│  - DSCP markings from guest devices are ignored                              │
│  - Guest traffic cannot impact corporate traffic                             │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

# 18. Appendix

## 18.1 QoS Priority Reference Table

| Priority | Name | Description | Typical Use |
|----------|------|-------------|-------------|
| 0 | Best Effort | Default traffic | Web browsing |
| 1 | Background | Bulk data | Backups, downloads |
| 2 | Spare | Low priority | Scavenger traffic |
| 3 | Excellent Effort | Business critical | Business apps |
| 4 | Controlled Load | Video streaming | Video conferencing |
| 5 | Video | < 100ms latency | Interactive video |
| 6 | Voice | < 10ms latency | VoIP calls |
| 7 | Network Control | Critical network | Routing protocols |

## 18.2 802.11e Access Categories

| Access Category | Description | User Priority Values |
|-----------------|-------------|---------------------|
| AC_BK | Background | 1, 2 |
| AC_BE | Best Effort | 0, 3 |
| AC_VI | Video | 4, 5 |
| AC_VO | Voice | 6, 7 |

## 18.3 DSCP to 802.1p Mapping

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                      DSCP to 802.1p Default Mapping                          │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  DSCP Range     │ DSCP Values        │ 802.1p │ Description                 │
│  ───────────────┼────────────────────┼────────┼──────────────────────────── │
│  CS7            │ 56-63              │   7    │ Network Control              │
│  CS6, EF        │ 46-55              │   6    │ Voice                        │
│  CS5, AF4x      │ 32-45              │   5    │ Video                        │
│  CS4, AF3x      │ 24-31              │   4    │ Controlled Load              │
│  CS3, AF2x      │ 16-23              │   3    │ Excellent Effort             │
│  CS2, AF1x      │ 8-15               │   2    │ Spare                        │
│  CS1            │ 8                  │   1    │ Background                   │
│  Default        │ 0-7                │   0    │ Best Effort                  │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

## 18.4 Test Execution Commands

### 18.4.1 Running the Test

```bash
# Run all variants
python ApQoSTest.py

# Run specific variant
python ApQoSTest.py --variant=1

# Run with debug output
python ApQoSTest.py --debug

# Run with specific tracing
python ApQoSTest.py --tracing="ApDut/*,ApQoSTest/*"
```

### 18.4.2 Test Output Example

```
[INFO] ApQoSTest: Starting test run
[INFO] ApQoSTest: Variant 1: DSCP Downstream + Ceiling Priority
[INFO] ApQoSTest: Configuring SSID with QoS settings
[INFO] ApQoSTest: Validating QoS flags on VAP
[PASS] ApQoSTest: iv_qos_prio = 0 (expected 0)
[PASS] ApQoSTest: iv_qos_prio_type = 0 (expected 0)
[PASS] ApQoSTest: iv_qos_dstream = 1 (expected 1)
[PASS] ApQoSTest: iv_qos_ustream_8021p = 1 (expected 1)
[PASS] ApQoSTest: iv_qos_ustream_dscp = 1 (expected 1)
[INFO] ApQoSTest: Connecting client to SSID
[INFO] ApQoSTest: Validating QoS counters
[INFO] ApQoSTest: BE counter before: 1000
[INFO] ApQoSTest: Sending 50 ping packets
[INFO] ApQoSTest: BE counter after: 1050
[PASS] ApQoSTest: BE counter increased by 50
[INFO] ApQoSTest: QoS SSID Verification successful
[PASS] ApQoSTest: Test completed successfully
```

## 18.5 Glossary

| Term | Definition |
|------|------------|
| **AP** | Access Point - WiFi device that provides wireless connectivity |
| **BE** | Best Effort - Default QoS priority class |
| **DSCP** | Differentiated Services Code Point - IP header field for QoS |
| **DUT** | Device Under Test - The equipment being tested |
| **EDUT** | External Device Under Test - Test framework abstraction |
| **ICMP** | Internet Control Message Protocol - Used for ping |
| **IGMP** | Internet Group Management Protocol - For multicast |
| **MLD** | Multicast Listener Discovery - IPv6 multicast protocol |
| **QoS** | Quality of Service - Traffic prioritization |
| **SSID** | Service Set Identifier - WiFi network name |
| **TOS** | Type of Service - IP header field (legacy QoS) |
| **VAP** | Virtual Access Point - Virtual WiFi interface |
| **VLAN** | Virtual LAN - Network segmentation |
| **WMM** | WiFi Multimedia - 802.11e QoS extensions |

## 18.6 Version History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2024 | Arista | Initial test implementation |
| 1.1 | 2024 | Arista | Added counter validation |
| 1.2 | 2024 | Arista | Added multiple variants |

## 18.7 References

1. **IEEE 802.11e** - Quality of Service Enhancements
2. **IEEE 802.1p** - Traffic Class Expediting and Dynamic Multicast Filtering
3. **RFC 2474** - Definition of the Differentiated Services Field
4. **RFC 4594** - Configuration Guidelines for DiffServ Service Classes
5. **Arista WiFi AP Configuration Guide** - Internal documentation
6. **WifiClusterTest Framework Documentation** - Internal documentation

---

# Document Information

| Property | Value |
|----------|-------|
| **Document Title** | ApQoSTest.py Comprehensive Documentation |
| **File Documented** | `autotest/WifiClusterTest/ctest/ApQoSTest.py` |
| **Documentation Version** | 1.0 |
| **Generated** | 2024 |
| **Total Sections** | 18 |
| **Includes Scapy Reference** | Yes |

---

*End of Documentation*
