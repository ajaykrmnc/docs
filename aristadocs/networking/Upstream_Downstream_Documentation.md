# Upstream and Downstream Network Concepts - Comprehensive Documentation

## Table of Contents

1. [Introduction](#introduction)
2. [Terminology and Definitions](#terminology-and-definitions)
3. [Upstream Network Architecture](#upstream-network-architecture)
4. [Downstream Network Architecture](#downstream-network-architecture)
5. [Data Flow Patterns](#data-flow-patterns)
6. [Network Topology](#network-topology)
7. [Uplink Management](#uplink-management)
8. [VLAN Architecture](#vlan-architecture)
9. [Tunneling and Encapsulation](#tunneling-and-encapsulation)
10. [Load Balancing and Failover](#load-balancing-and-failover)
11. [Quality of Service (QoS)](#quality-of-service-qos)
12. [Codebase Implementation](#codebase-implementation)
13. [Configuration and Management](#configuration-and-management)
14. [Monitoring and Diagnostics](#monitoring-and-diagnostics)
15. [Best Practices](#best-practices)

---

## 1. Introduction

### Overview

In networking, particularly in the context of Access Points (APs) and wireless infrastructure, the terms "upstream" and "downstream" describe the direction of data flow relative to the network hierarchy. Understanding these concepts is essential for proper network design, troubleshooting, and optimization.

### Purpose of This Document

This document provides comprehensive coverage of:

- Upstream and downstream concepts in AP networking
- Network architecture patterns
- Implementation details within the codebase
- Operational guidance and best practices

### Document Scope

This documentation covers:

- Physical and logical network topology
- Data flow direction and patterns
- Uplink port management
- VLAN tagging and routing
- Tunnel implementations
- Failover and redundancy mechanisms

---

## 2. Terminology and Definitions

### Core Definitions

| Term           | Definition                                                            |
| -------------- | --------------------------------------------------------------------- |
| **Upstream**   | Direction toward the network core/internet; from AP to infrastructure |
| **Downstream** | Direction toward end clients; from infrastructure to AP to clients    |
| **Uplink**     | Physical or logical connection from AP to upstream network            |
| **Downlink**   | Connection from AP to wireless clients                                |
| **Backhaul**   | Network connection carrying aggregated traffic to core network        |
| **Fronthaul**  | Connection between radio units and baseband processing                |

### AP-Specific Terminology

| Term                   | Definition                                         |
| ---------------------- | -------------------------------------------------- |
| **Primary Uplink**     | Main Ethernet connection to network infrastructure |
| **Secondary Uplink**   | Backup Ethernet connection for redundancy          |
| **Communication VLAN** | VLAN used for AP management and control traffic    |
| **Data VLAN**          | VLAN carrying client data traffic                  |
| **Gateway**            | Router providing path to upstream network          |
| **Controller**         | Central management server for AP fleet             |

### Traffic Direction Examples

```
UPSTREAM TRAFFIC (Client → AP → Network → Internet)
┌─────────────────────────────────────────────────────────────┐
│                                                             │
│  Client    ──────>    AP    ──────>   Switch   ──────>  Router/Internet
│  Device              Uplink           Core              Gateway
│                                                             │
└─────────────────────────────────────────────────────────────┘

DOWNSTREAM TRAFFIC (Internet → Network → AP → Client)
┌─────────────────────────────────────────────────────────────┐
│                                                             │
│  Internet   ──────>   Router  ──────>  Switch  ──────>  AP  ──────>  Client
│  Server              Gateway           Core         Downlink       Device
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## 3. Upstream Network Architecture

### Physical Connectivity

#### Ethernet Uplink Ports

APs typically have one or two Ethernet ports for upstream connectivity:

```
┌──────────────────────────────────────────────────────────┐
│                    Access Point                          │
│                                                          │
│  ┌──────────┐         ┌──────────┐                      │
│  │  eth0    │         │  eth1    │     (Radio Interfaces)│
│  │ Primary  │         │Secondary │                      │
│  │ Uplink   │         │ Uplink   │                      │
│  └────┬─────┘         └────┬─────┘                      │
│       │                    │                             │
└───────┼────────────────────┼─────────────────────────────┘
        │                    │
        │                    │
        ▼                    ▼
┌──────────────────────────────────────────────────────────┐
│              Network Switch Infrastructure               │
│                                                          │
│   Port 1              Port 2                             │
│   (Active)            (Standby/LAG)                      │
└──────────────────────────────────────────────────────────┘
```

#### Link Aggregation (LAG)

When both Ethernet ports are available, they can be configured for:

- **Active-Standby**: One active port, one standby for failover
- **LAG/Bonding**: Both ports aggregated for increased bandwidth

```c
// Bonding mode configuration
#define BONDING_MODE_ACTIVE_BACKUP  1  // Active-standby
#define BONDING_MODE_LACP           4  // 802.3ad LACP

// Check if LAG is enabled
func IsLinkAggregationEnabled() bool {
    return nwutils.BondingMode() != 1
}


### Upstream Services

The AP communicates with several upstream services:

| Service | Purpose | Protocol |
|---------|---------|----------|
| DHCP Server | IP address allocation | UDP 67/68 |
| DNS Server | Name resolution | UDP/TCP 53 |
| NTP Server | Time synchronization | UDP 123 |
| Controller | Management and configuration | HTTPS/gRPC |
| RADIUS | Authentication | UDP 1812/1813 |
| Syslog Server | Log collection | UDP 514 |

```

## 4. Downstream Network Architecture

### Wireless Client Connectivity

#### Radio Interfaces

```
┌────────────────────────────────────────────────────────────┐
│                      Access Point                          │
│                                                            │
│  ┌──────────────────┐    ┌──────────────────┐            │
│  │   Radio 0        │    │   Radio 1        │            │
│  │   (2.4 GHz)      │    │   (5 GHz)        │            │
│  │                  │    │                  │            │
│  │  - SSID: Corp    │    │  - SSID: Corp    │            │
│  │  - SSID: Guest   │    │  - SSID: Guest   │            │
│  │  - SSID: IoT     │    │  - SSID: IoT     │            │
│  └────────┬─────────┘    └────────┬─────────┘            │
│           │                       │                       │
└───────────┼───────────────────────┼───────────────────────┘
            │                       │
            ▼                       ▼
     ┌──────────────────────────────────────┐
     │        Wireless Clients              │
     │                                       │
     │  📱 Phones    💻 Laptops    📺 IoT   │
     └──────────────────────────────────────┘
```

#### Virtual Access Points (VAPs)

Each SSID creates a Virtual Access Point:

```
Radio Interface
     │
     ├── VAP 0 (ath0) ── SSID: Corporate ── VLAN 100
     │
     ├── VAP 1 (ath1) ── SSID: Guest ────── VLAN 200
     │
     └── VAP 2 (ath2) ── SSID: IoT ──────── VLAN 300
```

### Bridge Architecture

Downstream traffic is bridged between wireless and wired interfaces:

```
┌────────────────────────────────────────────────────────────────┐
│                        Bridge (br-vlan100)                     │
│                                                                │
│   ┌─────────────┐   ┌─────────────┐   ┌───────────────────┐  │
│   │  ath0       │   │  ath1       │   │ eth0.100 (tagged) │  │
│   │  (Corp WiFi)│   │  (Corp WiFi)│   │  (Uplink VLAN)    │  │
│   └──────┬──────┘   └──────┬──────┘   └─────────┬─────────┘  │
│          │                 │                    │             │
│          └─────────────────┴────────────────────┘             │
│                           │                                   │
│                    Bridge Learning                            │
│                    MAC Table                                  │
│                    Forwarding                                 │
└────────────────────────────────────────────────────────────────┘
```

### Client Traffic Flow

#### Association and Authentication

```
┌─────────────────────────────────────────────────────────────────────┐
│                    Client Connection Flow                           │
│                                                                     │
│  1. Probe Request/Response                                          │
│     Client ────────────────────────────────────> AP                 │
│     Client <──────────────────────────────────── AP                 │
│                                                                     │
│  2. Authentication                                                  │
│     Client ────────────────────────────────────> AP                 │
│     Client <──────────────────────────────────── AP                 │
│                                                                     │
│  3. Association                                                     │
│     Client ────────────────────────────────────> AP                 │
│     Client <──────────────────────────────────── AP                 │
│                                                                     │
│  4. 802.1X/EAP (if WPA-Enterprise)                                 │
│     Client <────────────────────────────────────> AP <───> RADIUS  │
│                                                                     │
│  5. 4-Way Handshake                                                 │
│     Client <────────────────────────────────────> AP                │
│                                                                     │
│  6. DHCP                                                            │
│     Client ──> AP ──> Switch ──> DHCP Server                       │
│     Client <── AP <── Switch <── DHCP Server                       │
│                                                                     │
│  7. Data Transfer                                                   │
│     Client <────────────────────────────────────> AP <───> Network │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 5. Data Flow Patterns

### Upstream Data Flow

Data flowing from clients toward the network core:

```
┌─────────────────────────────────────────────────────────────────────┐
│                    UPSTREAM DATA FLOW                               │
│                                                                     │
│  ┌──────────┐    ┌──────────────────────────────────────────────┐  │
│  │  Client  │───>│                    AP                        │  │
│  │  Packet  │    │                                              │  │
│  └──────────┘    │  1. Receive on WiFi interface (athX)         │  │
│                  │  2. Decrypt (WPA2/WPA3)                      │  │
│                  │  3. Bridge lookup (MAC table)                │  │
│                  │  4. Apply QoS policies                       │  │
│                  │  5. VLAN tagging (if applicable)             │  │
│                  │  6. Forward to uplink (eth0/bond0)           │  │
│                  └──────────────────────────────────────────────┘  │
│                                    │                                │
│                                    ▼                                │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │                     Network Switch                           │   │
│  │  - Receive tagged/untagged frame                             │   │
│  │  - VLAN processing                                           │   │
│  │  - Forward to uplink/router                                  │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                                    │                                │
│                                    ▼                                │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │                     Gateway/Router                           │   │
│  │  - Route to destination                                      │   │
│  │  - NAT (if applicable)                                       │   │
│  │  - Send to Internet                                          │   │
│  └─────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────┘
```

### Downstream Data Flow

Data flowing from network core to clients:

```
┌─────────────────────────────────────────────────────────────────────┐
│                    DOWNSTREAM DATA FLOW                             │
│                                                                     │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │                     Internet/Server                          │   │
│  │  - Response packet generated                                 │   │
│  │  - Route to destination network                              │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                                    │                                │
│                                    ▼                                │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │                     Gateway/Router                           │   │
│  │  - NAT translation (if applicable)                           │   │
│  │  - Route to local subnet                                     │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                                    │                                │
│                                    ▼                                │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │                     Network Switch                           │   │
│  │  - MAC lookup                                                │   │
│  │  - Forward to AP port                                        │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                                    │                                │
│                                    ▼                                │
│  ┌──────────────────────────────────────────────────────────┐      │
│  │                         AP                                │      │
│  │  1. Receive on uplink (eth0/bond0)                       │      │
│  │  2. VLAN processing                                      │      │
│  │  3. Bridge lookup (destination MAC)                      │      │
│  │  4. Queue for transmission (QoS)                         │      │
│  │  5. Encrypt (WPA2/WPA3)                                  │      │
│  │  6. Transmit on WiFi interface (athX)                    │      │
│  └──────────────────────────────────────────────────────────┘      │
│                                    │                                │
│                                    ▼                                │
│                             ┌──────────┐                            │
│                             │  Client  │                            │
│                             └──────────┘                            │
└─────────────────────────────────────────────────────────────────────┘
```

### Multicast and Broadcast Traffic

Special handling for multicast/broadcast downstream traffic:

```
┌─────────────────────────────────────────────────────────────────────┐
│                  MULTICAST/BROADCAST HANDLING                       │
│                                                                     │
│  Upstream Multicast Source                                          │
│            │                                                        │
│            ▼                                                        │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │                          AP                                  │   │
│  │                                                              │   │
│  │  - Receive multicast on uplink                               │   │
│  │  - IGMP snooping check                                       │   │
│  │  - Convert to unicast (if supported)                         │   │
│  │  - OR broadcast to all associated clients                    │   │
│  │  - Rate limiting to prevent airtime exhaustion               │   │
│  └─────────────────────────────────────────────────────────────┘   │
│            │                                                        │
│            ▼                                                        │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │        All Subscribed Wireless Clients                       │   │
│  └─────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 6. Network Topology

### Star Topology

Most common deployment pattern:

```
                    ┌──────────────────┐
                    │   Core Network   │
                    │    / Router      │
                    └────────┬─────────┘
                             │
              ┌──────────────┼──────────────┐
              │              │              │
              ▼              ▼              ▼
        ┌─────────┐    ┌─────────┐    ┌─────────┐
        │ Switch  │    │ Switch  │    │ Switch  │
        │  IDF 1  │    │  IDF 2  │    │  IDF 3  │
        └────┬────┘    └────┬────┘    └────┬────┘
             │              │              │
     ┌───────┼───────┐      │      ┌───────┼───────┐
     │       │       │      │      │       │       │
     ▼       ▼       ▼      ▼      ▼       ▼       ▼
   ┌───┐   ┌───┐   ┌───┐  ┌───┐  ┌───┐   ┌───┐   ┌───┐
   │AP1│   │AP2│   │AP3│  │AP4│  │AP5│   │AP6│   │AP7│
   └───┘   └───┘   └───┘  └───┘  └───┘   └───┘   └───┘
```

### Mesh Topology

For extended coverage without wired backhaul:

```
┌─────────────────────────────────────────────────────────────────────┐
│                        MESH TOPOLOGY                                │
│                                                                     │
│              ┌─────────┐                                            │
│              │  Root   │  ◄── Wired Uplink to Network               │
│              │   AP    │                                            │
│              └────┬────┘                                            │
│                   │                                                 │
│         ┌─────────┴─────────┐         Wireless Backhaul             │
│         │                   │         (Upstream Direction)          │
│         ▼                   ▼                                       │
│    ┌─────────┐         ┌─────────┐                                  │
│    │ Mesh AP │         │ Mesh AP │                                  │
│    │   #1    │         │   #2    │                                  │
│    └────┬────┘         └────┬────┘                                  │
│         │                   │                                       │
│         ▼                   ▼                                       │
│    ┌─────────┐         ┌─────────┐                                  │
│    │ Mesh AP │         │ Mesh AP │                                  │
│    │   #3    │         │   #4    │                                  │
│    └─────────┘         └─────────┘                                  │
│                                                                     │
│    ▲                                            ▼                   │
│    │                                            │                   │
│  Client traffic                          Client traffic             │
│  (Downstream direction                   (Downstream direction      │
│   to wireless clients)                    to wireless clients)      │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 7. Uplink Management

### Dual Uplink Configuration

The AP supports dual uplink ports for redundancy:

```go
// DualUplink state variables
var (
    DisableDualUplink      = "disable_dual_uplink"
    DualUplinkDir          = apOpt + "/dual_uplink/"
    DualUplinkEnabledFile  = DualUplinkDir + "dual_uplink_enabled"
    DualUplinkMaxCounter   = 12 // 60 seconds (Minimum delay 5 seconds * 12)
)

// Uplink configuration
type DualUplinkMonStruct struct {
    DualUplinkTimeoutEnabled bool
    DualUplinkCounter        int
    Enable                   bool
    Eth0Status               string
    Eth1Status               string
    LagStatus                bool
    EthShiftCounter          int
    PriUplinkLAN             string
    SecUplinkLAN             string
}
```

### Uplink Monitoring

```go
// GetLANUplinkConfig returns current uplink configuration
func GetLANUplinkConfig() (string, string) {
    if !ap.Env.DualUplinkSupport {
        return cst.LANIntf1, cst.LANIntf1
    } else if IsFileExist(DualUplinkEnabledFile) {
        return cst.LANIntf2, cst.LANIntf1
    }
    return cst.LANIntf1, cst.LANIntf2
}

// SwitchToBackupUplink activates the backup uplink
func SwitchToBackupUplink() error {
    return utils.WriteToFile(path.ActiveSlaveFile, BackupUplink(), true)
}

// BackupUplink returns the backup interface name
func BackupUplink() string {
    if EthernetConfigMap[ActiveUplinkInterface] == cst.EthIntf0 {
        return cst.EthIntf1
    }
    return cst.EthIntf0
}
```

### Uplink Failover Logic

```
┌─────────────────────────────────────────────────────────────────────┐
│                    UPLINK FAILOVER STATE MACHINE                    │
│                                                                     │
│  ┌─────────────────┐                                               │
│  │  Both Links Up  │  (Normal Operation)                           │
│  │  Primary Active │                                               │
│  └────────┬────────┘                                               │
│           │                                                         │
│           │  Primary link fails                                     │
│           ▼                                                         │
│  ┌─────────────────┐                                               │
│  │  Start Failover │                                               │
│  │     Timer       │  (DualUplinkMaxCounter = 60 sec)              │
│  └────────┬────────┘                                               │
│           │                                                         │
│           │  Timer expires & secondary up                           │
│           ▼                                                         │
│  ┌─────────────────┐                                               │
│  │ Switch to       │                                               │
│  │ Secondary       │                                               │
│  └────────┬────────┘                                               │
│           │                                                         │
│           │  Primary recovers                                       │
│           ▼                                                         │
│  ┌─────────────────┐                                               │
│  │  Failback       │  (If configured)                              │
│  │  to Primary     │                                               │
│  └─────────────────┘                                               │
└─────────────────────────────────────────────────────────────────────┘
```

### Bonding Modes

| Mode | Name          | Description                              |
| ---- | ------------- | ---------------------------------------- |
| 0    | balance-rr    | Round-robin load balancing               |
| 1    | active-backup | Active-standby failover                  |
| 2    | balance-xor   | XOR hash-based distribution              |
| 3    | broadcast     | Transmit on all slaves                   |
| 4    | 802.3ad       | LACP (Link Aggregation Control Protocol) |
| 5    | balance-tlb   | Adaptive transmit load balancing         |
| 6    | balance-alb   | Adaptive load balancing                  |

---

## 8. VLAN Architecture

### VLAN Tagging

```
┌────────────────────────────────────────────────────────────┐
│                      Access Point                          │
│                                                            │
│  ┌────────────────────────────────────────────────────┐   │
│  │                  Bond Interface                     │   │
│  │                     (bond0)                         │   │
│  └────────────────────────┬───────────────────────────┘   │
│                           │                                │
│            ┌──────────────┼──────────────┐                │
│            │              │              │                 │
│  ┌─────────▼───┐  ┌──────▼──────┐  ┌───▼─────────┐      │
│  │  VLAN 100   │  │  VLAN 200   │  │  VLAN 300   │      │
│  │ Management  │  │ Client Data │  │ Guest Data  │      │
│  └─────────────┘  └─────────────┘  └─────────────┘      │
│                                                            │
└────────────────────────────────────────────────────────────┘
```

### VLAN Types

| VLAN Type                | Purpose                | Direction |
| ------------------------ | ---------------------- | --------- |
| Management/Communication | AP management traffic  | Upstream  |
| Data VLANs               | Client data traffic    | Both      |
| Guest VLANs              | Isolated guest traffic | Both      |
| Voice VLANs              | VoIP traffic with QoS  | Both      |

### VLAN Gateway Monitoring

```c
// VLAN monitoring sysfs path
VLAN_MONITORING_SYSFS=""
if toggleUnifiedVlanGatewayP1Enabled &&
   [ -f "/sys/class/net/$interface/gwmac/vlan_monitoring" ]; then
    VLAN_MONITORING_SYSFS="/sys/class/net/$interface/gwmac/vlan_monitoring"
fi

// Enable VLAN monitoring
start_service() {
    [ -n "${VLAN_MONITORING_SYSFS}" ] && echo 1 >"${VLAN_MONITORING_SYSFS}"
}

// Disable VLAN monitoring
stop_service() {
    [ -n "${VLAN_MONITORING_SYSFS}" ] && echo 0 >"${VLAN_MONITORING_SYSFS}"
}
```

---

## 9. Tunneling and Encapsulation

### Tunnel Types

The AP supports multiple tunnel types for upstream connectivity:

| Tunnel Type | Use Case                  | Protocol |
| ----------- | ------------------------- | -------- |
| EoGRE       | Layer 2 extension over IP | GRE      |
| IPsec       | Secure connectivity       | ESP/AH   |
| VXLAN       | Data center overlay       | UDP 4789 |
| L2TP        | VPN tunneling             | UDP 1701 |

### Tunnel Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                      TUNNEL ARCHITECTURE                            │
│                                                                     │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │                    Original Packet                           │   │
│  │  +----------+----------+----------+------------------------+ │   │
│  │  | Eth Hdr  | IP Hdr   | TCP/UDP  |        Payload        | │   │
│  │  +----------+----------+----------+------------------------+ │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                              │                                      │
│                              │  Tunnel Encapsulation                │
│                              ▼                                      │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │                   Encapsulated Packet                        │   │
│  │  +--------+--------+--------+---------+--------------------+ │   │
│  │  |Outer   |Outer IP|Tunnel  | Inner   |    Original       | │   │
│  │  |Eth Hdr |Header  |Header  | Packet  |    Payload        | │   │
│  │  +--------+--------+--------+---------+--------------------+ │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                                                                     │
│                              │                                      │
│                              ▼                                      │
│                    Upstream to Tunnel Endpoint                      │
└─────────────────────────────────────────────────────────────────────┘
```

### Tunnel Configuration

```bash
# Handle tunnel types
case $NETWORK_TYPE in
    1)  # EoGRE
        "$AP_OPTDIR/ap/handle_eogre_tunnel.sh" "$NETWORK_DIR" "$PROTOCOL" \
            "$is_primary_network" "$is_secondary_network" \
            "$primary_remote_ip" "$sec_remote_ip"
        ;;
    2|5)  # IPsec
        "$AP_OPTDIR/ap/handle_ipsec_tunnel.sh" "$NETWORK_DIR" "$PROTOCOL" \
            "$is_primary_network" "$is_secondary_network" \
            "$primary_remote_ip" "$sec_remote_ip"
        ;;
    3)  # VXLAN
        "$AP_OPTDIR/ap/handle_vxlan_tunnel.sh" "INIT" "$NETWORK_DIR" "$PROTOCOL" \
            "$is_primary_network" "$is_secondary_network" \
            "$primary_remote_ip" "$sec_remote_ip"
        ;;
esac
```

### Tunnel Endpoint Resolution

```bash
resolve_tunnel_endpoint() {
    remote_host=$(cfg_get "$tunnel_ip_type" "$iter_network_conf")

    # If remote endpoint not configured, use NTP server from DHCP option 42
    if [ "$remote_host" = "" ]; then
        tunnel_remote_ip=$ntp_remote_server_ip
        echo "$tunnel_remote_ip"
        return
    fi

    # Resolve hostname to IP
    # ...
}
```

---

## 10. Load Balancing and Failover

### Uplink Load Balancing

```
┌─────────────────────────────────────────────────────────────────────┐
│                    LOAD BALANCING MODES                             │
│                                                                     │
│  Mode 1: Active-Standby (Failover Only)                            │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │     eth0 (Active) ────────> Switch                           │   │
│  │     eth1 (Standby) - - - -> Switch  (Takes over on failure)  │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                                                                     │
│  Mode 4: LACP (802.3ad)                                            │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │     eth0 ─────┬──────> Switch Port 1                         │   │
│  │               │        (LAG Group)                           │   │
│  │     eth1 ─────┴──────> Switch Port 2                         │   │
│  │                                                              │   │
│  │  Traffic distributed based on hash algorithm                 │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

### Failover Scenarios

| Scenario            | Detection         | Action           | Recovery       |
| ------------------- | ----------------- | ---------------- | -------------- |
| Link Down           | MII monitoring    | Switch to backup | Auto failback  |
| No DHCP             | Lease failure     | Fallback IP      | Retry DHCP     |
| Gateway Unreachable | ARP/ping failure  | Report event     | Await recovery |
| Tunnel Down         | Keepalive timeout | Switch tunnel    | Re-establish   |

### Reselect Policies

```go
// Bonding reselect policies
AlwaysReselectPolicy  = "always 0"      // Always use primary when up
FailureReselectPolicy = "failure 2"     // Only switch on failure
```

---

## 11. Quality of Service (QoS)

### Upstream QoS

Traffic classification for upstream direction:

```
┌─────────────────────────────────────────────────────────────────────┐
│                    UPSTREAM QoS PROCESSING                          │
│                                                                     │
│  Client Packet                                                      │
│       │                                                             │
│       ▼                                                             │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │  1. Receive from wireless interface                          │   │
│  │  2. Extract WMM Access Category (AC)                         │   │
│  │  3. Map to DSCP/CoS value                                    │   │
│  │  4. Apply traffic shaping (if configured)                    │   │
│  │  5. Forward with QoS marking                                 │   │
│  └─────────────────────────────────────────────────────────────┘   │
│       │                                                             │
│       ▼                                                             │
│  To Upstream Network (with QoS marking preserved)                   │
└─────────────────────────────────────────────────────────────────────┘
```

### Downstream QoS

```
┌─────────────────────────────────────────────────────────────────────┐
│                    DOWNSTREAM QoS PROCESSING                        │
│                                                                     │
│  From Upstream Network                                              │
│       │                                                             │
│       ▼                                                             │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │  1. Receive from uplink interface                            │   │
│  │  2. Extract DSCP/CoS value                                   │   │
│  │  3. Map to WMM Access Category                               │   │
│  │  4. Queue in appropriate WMM queue                           │   │
│  │  5. Transmit based on WMM scheduling                         │   │
│  └─────────────────────────────────────────────────────────────┘   │
│       │                                                             │
│       ▼                                                             │
│  To Wireless Client (with WMM priority)                             │
└─────────────────────────────────────────────────────────────────────┘
```

### WMM Access Categories

| AC    | Name        | Traffic Type    | Priority |
| ----- | ----------- | --------------- | -------- |
| AC_VO | Voice       | VoIP, real-time | Highest  |
| AC_VI | Video       | Streaming video | High     |
| AC_BE | Best Effort | Default traffic | Normal   |
| AC_BK | Background  | Bulk transfers  | Low      |

---

## 12. Codebase Implementation

### Key Source Files

| File                                          | Purpose                        |
| --------------------------------------------- | ------------------------------ |
| `ap/src/go/arista-ap/gobin/uplink_monitor.go` | Uplink monitoring and failover |
| `ap/rootfs/scripts/network_start.sh`          | Network initialization         |
| `ap/rootfs/scripts/handle_tunnel.sh`          | Tunnel management              |
| `ap/rootfs/scripts/comm_vlan_init.sh`         | Communication VLAN setup       |
| `ap/rootfs/init.d/functions`                  | Common network functions       |

### Uplink Monitor Implementation

```go
// Monitor uplink status
func dualUplinkMonitor(t *TimeSpec) error {
    logPrefix := "[dualUplinkMonitor] "

    // Check if dual uplink supported
    if !ap.Env.DualUplinkSupport {
        return nil
    }

    // Get interface status
    iseth0Up := DualUplinkConfig.Eth0Status == cst.EthUp
    iseth1Up := DualUplinkConfig.Eth1Status == cst.EthUp

    // Handle failover condition
    if !iseth0Up && iseth1Up {
        glog.Infof(logPrefix + "Initiate Uplink Switch timer")
        DualUplinkConfig.DualUplinkTimeoutEnabled = true
        DualUplinkConfig.EthShiftCounter++
    }

    return nil
}
```

### Network Initialization

```bash
# Communication VLAN initialization
if [ "$IPV6_SUPPORT" = "1" ]; then
    "$AP_ETCDIR/init.d/autoconf6.init" start ${NET_DEV}
fi

# Wait for DHCP or IP assignment
DHCP_LEASE=$AP_TMPDIR/DHCP_Success.${NET_DEV}
ctr=0
while [ $ctr -lt 8 ]; do
    if [ -f "$DHCP_LEASE" ]; then
        break
    fi
    sleep 1
    ctr=$((ctr + 1))
done
```

### Ethernet Link Monitoring

```go
// Check backup uplink availability
func CheckBackupUplinkAvailability() bool {
    if nwutils.BondingMode() != 1 || ap.SenConf.PreferPrimaryUplink {
        return false
    }

    // Verify MII status for bonding slave
    filepath := fmt.Sprint(aputils.GetSysFsNetBase() + "/" +
                          BackupUplink() + "/bonding_slave/mii_status")
    return utils.IsStringExistInFile("up", filepath)
}
```

---

## 13. Configuration and Management

### Uplink Configuration

#### Static Configuration

```bash
# Configure primary uplink
PRI_UPLINK_LAN=eth0
SEC_UPLINK_LAN=eth1

# Bonding configuration
BONDING_MODE=1  # active-backup
BONDING_MIIMON=100  # Link monitoring interval (ms)
```

#### Dynamic Configuration

```bash
# Check dual uplink status
if [ -f "$AP_OPTDIR/dual_uplink/dual_uplink_enabled" ]; then
    # Secondary uplink is primary
    ACTIVE_UPLINK=eth1
else
    # Primary uplink is active
    ACTIVE_UPLINK=eth0
fi
```

### VLAN Configuration

```bash
# Communication VLAN setup
NET_DEV="eth0.100"  # VLAN 100 on eth0

# Create VLAN interface
ip link add link eth0 name eth0.100 type vlan id 100
ip link set eth0.100 up

# Assign IP via DHCP
start_udhcp_process "${NET_DEV}"
```

### Tunnel Configuration

```bash
# IPsec tunnel configuration
NETWORK_TYPE=2  # IPsec
PROTOCOL="AF_INET"  # IPv4
PRIMARY_REMOTE_IP="203.0.113.1"
SECONDARY_REMOTE_IP="203.0.113.2"

# EoGRE tunnel configuration
NETWORK_TYPE=1  # EoGRE
TUNNEL_INTERFACE="gre1"
```

### Feature Toggles

```bash
# Check dual uplink feature toggle
if toggleDualUplinkEnabled && [ "$DUAL_UPLINK_SUPPORT" = "TRUE" ]; then
    # Enable dual uplink monitoring
    enable_dual_uplink_monitoring
fi

# Check ethernet parity toggle
if toggleEthernetParityEnabled; then
    # Use single uplink mode
    rm -rf "$AP_OPTDIR/dual_uplink/dual_uplink_enabled"
fi
```

---

## 14. Monitoring and Diagnostics

### Interface Status

```bash
# Check interface status
ip link show eth0
ip link show bond0

# Check bonding status
cat /proc/net/bonding/bond0

# Check VLAN interfaces
cat /proc/net/vlan/config
```

### Traffic Statistics

```bash
# Interface statistics
cat /sys/class/net/eth0/statistics/rx_packets
cat /sys/class/net/eth0/statistics/tx_packets
cat /sys/class/net/eth0/statistics/rx_bytes
cat /sys/class/net/eth0/statistics/tx_bytes
```

### Connectivity Tests

```bash
# Test upstream connectivity
ping -c 3 $GATEWAY_IP

# Test DNS resolution
nslookup controller.example.com

# Test tunnel endpoint
ping -c 3 $TUNNEL_ENDPOINT
```

### Log Analysis

```bash
# Check network-related logs
grep -i "uplink\|dhcp\|vlan\|tunnel" /var/log/unified_logs/*.logs

# Check for link events
dmesg | grep -i "link\|eth\|bond"

# Check DHCP events
grep -i "leasefail\|bound\|renew" /var/log/unified_logs/*.logs
```

### Diagnostic Commands

| Command      | Purpose                         |
| ------------ | ------------------------------- |
| `ip addr`    | Show IP addresses               |
| `ip route`   | Show routing table              |
| `ip link`    | Show link status                |
| `bridge fdb` | Show bridge forwarding database |
| `arp -n`     | Show ARP cache                  |
| `ss -tunp`   | Show network connections        |

### Event Logging

```bash
# Network events format
# ATN_<EVENT_TYPE> NETWORK <SEVERITY> <details>

# Examples:
echo "ATN_LEASEFAIL_EVT NETWORK ALERT $vlan,IPv4,expired" >> $EVT_LOGGING_FILE
echo "ATN_LINK_DOWN NETWORK ALERT eth0,down" >> $EVT_LOGGING_FILE
echo "ATN_UPLINK_SWITCH NETWORK INFO primary_to_secondary" >> $EVT_LOGGING_FILE
```

---

## 15. Best Practices

### Network Design

1. **Redundancy**: Always configure dual uplinks when available
2. **VLAN Segmentation**: Separate management, data, and guest traffic
3. **QoS Planning**: Configure QoS for voice and video traffic
4. **Tunnel Selection**: Choose appropriate tunnel type for use case

### Uplink Configuration

1. **Active-Backup**: Use for simple failover scenarios
2. **LACP**: Use for increased bandwidth and redundancy
3. **Monitoring**: Configure appropriate MII monitoring intervals
4. **Failback**: Configure failback behavior based on requirements

### VLAN Best Practices

1. **Native VLAN**: Avoid using VLAN 1 for production traffic
2. **Pruning**: Only trunk necessary VLANs to APs
3. **Monitoring**: Enable VLAN gateway monitoring
4. **Documentation**: Maintain VLAN assignment documentation

### Tunnel Best Practices

1. **Security**: Use IPsec for sensitive traffic
2. **MTU**: Account for tunnel overhead in MTU settings
3. **Redundancy**: Configure primary and secondary tunnel endpoints
4. **Keep-alives**: Enable keep-alives for tunnel health monitoring

### Monitoring and Alerting

1. **Link Monitoring**: Configure timely link failure detection
2. **DHCP Monitoring**: Alert on persistent lease failures
3. **Throughput Monitoring**: Track upstream/downstream utilization
4. **Event Correlation**: Correlate network events with client issues

### Troubleshooting Approach

1. **Layer by Layer**: Start from physical layer (cables, ports)
2. **Upstream First**: Verify uplink connectivity before downstream
3. **Logs Review**: Check unified logs for network events
4. **Packet Capture**: Use tcpdump for detailed analysis

---

## Appendix A: Network Interface Reference

### Physical Interfaces

| Interface | Description                       |
| --------- | --------------------------------- |
| eth0      | Primary Ethernet uplink           |
| eth1      | Secondary Ethernet uplink         |
| bond0     | Bonded interface (if LAG enabled) |

### Wireless Interfaces

| Interface | Description             |
| --------- | ----------------------- |
| wifi0     | 2.4 GHz radio interface |
| wifi1     | 5 GHz radio interface   |
| ath0-athN | Virtual AP interfaces   |

### Bridge Interfaces

| Interface | Description          |
| --------- | -------------------- |
| br-lanN   | Bridge for VLAN N    |
| br-guest  | Guest network bridge |
| br-mgmt   | Management bridge    |

---

## Appendix B: Upstream/Downstream Traffic Summary

### Upstream Traffic Types

| Traffic Type   | Source           | Destination   | Protocol |
| -------------- | ---------------- | ------------- | -------- |
| Client Data    | Wireless clients | Internet      | Various  |
| Management     | AP               | Controller    | HTTPS    |
| Authentication | AP               | RADIUS        | UDP 1812 |
| Logs           | AP               | Syslog server | UDP 514  |
| Telemetry      | AP               | Collector     | gRPC     |

### Downstream Traffic Types

| Traffic Type  | Source           | Destination      | Protocol  |
| ------------- | ---------------- | ---------------- | --------- |
| Client Data   | Internet         | Wireless clients | Various   |
| Configuration | Controller       | AP               | HTTPS     |
| Firmware      | Update server    | AP               | HTTPS     |
| DHCP          | DHCP server      | Clients          | UDP 67/68 |
| Multicast     | Multicast source | Clients          | UDP       |

---

_Document Version: 1.0_
_Last Updated: February 2026_
