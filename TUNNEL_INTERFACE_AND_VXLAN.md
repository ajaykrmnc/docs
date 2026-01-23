# Tunnel Interfaces, VXLAN, and UTUN - Complete Technical Reference

This document provides a comprehensive guide to tunnel interface technologies used in Access Point (AP) networking, focusing on VXLAN, EoGRE, IPSec tunnels, and user-space tunnel (utun) interfaces.

---

## Table of Contents

1. [Introduction to Tunnel Interfaces](#introduction-to-tunnel-interfaces)
2. [Tunnel Types Overview](#tunnel-types-overview)
3. [VXLAN (Virtual Extensible LAN)](#vxlan-virtual-extensible-lan)
4. [EoGRE (Ethernet over GRE)](#eogre-ethernet-over-gre)
5. [IPSec Tunnels](#ipsec-tunnels)
6. [UTUN (User-Space Tunnels)](#utun-user-space-tunnels)
7. [Tunnel Interface Naming Conventions](#tunnel-interface-naming-conventions)
8. [Tunnel Configuration Parameters](#tunnel-configuration-parameters)
9. [Tunnel Failover and High Availability](#tunnel-failover-and-high-availability)
10. [MTU and Fragmentation](#mtu-and-fragmentation)
11. [Troubleshooting](#troubleshooting)

---

## Introduction to Tunnel Interfaces

Tunnel interfaces create virtual point-to-point links that encapsulate traffic inside another protocol. In the AP codebase, tunnels enable:

- **Remote Bridging**: Extending Layer 2 networks across Layer 3 boundaries
- **Secure Communication**: Encrypting traffic between APs and controllers/gateways
- **Network Segmentation**: VLAN mapping across tunnel endpoints
- **High Availability**: Primary/secondary tunnel failover

### Network Type Enumeration

The codebase defines the following network tunnel types:

```c
typedef enum network_tunnel_type {
  NW_TUNNEL_TYPE_EOGRE = 1,       // Ethernet over GRE
  NW_TUNNEL_TYPE_EOGRE_IPSEC,     // EoGRE with IPSec encryption
  NW_TUNNEL_TYPE_VXLAN,           // Virtual Extensible LAN
  NW_TUNNEL_TYPE_VPN_IPSEC,       // VPN with IPSec (AP-RAP)
  NW_TUNNEL_TYPE_VXLAN_IPSEC      // VXLAN with IPSec encryption
} nw_tunnel_type;
```

In Go:
```go
const (
    Eogre          NetworkType = 0x1  // EoGRE
    EogreOverIPsec NetworkType = 0x2  // EoGRE + IPSec
    VxLAN          NetworkType = 0x3  // VXLAN
    VpnWithIPSec   NetworkType = 0x4  // VPN/AP-RAP IPSec
    VxlanOverIPsec NetworkType = 0x5  // VXLAN + IPSec
)
```

---

## Tunnel Types Overview

| Type | Network Type ID | Encapsulation | Encryption | Use Case |
|------|-----------------|---------------|------------|----------|
| EoGRE | 1 | GRE (Layer 2) | None | Basic L2 extension |
| EoGRE+IPSec | 2 | GRE over IPSec | IPSec ESP | Secure L2 extension |
| VXLAN | 3 | UDP (Port 4789) | None | Scalable L2 extension |
| VPN IPSec | 4 | IPSec | IPSec ESP | AP-to-RAP VPN |
| VXLAN+IPSec | 5 | VXLAN over IPSec | IPSec ESP | Secure VXLAN |

### Tunnel Interface Types

```go
const (
    VtIf Interface = 0x1  // VXLAN tunnel interface (vt*)
    GtIf Interface = 0x2  // GRE tunnel interface (gt*)
)
```

---

## VXLAN (Virtual Extensible LAN)

### Overview

VXLAN is a network virtualization technology that encapsulates Layer 2 Ethernet frames within Layer 3 UDP packets. It's designed to address the scalability limitations of traditional VLANs (4,096 limit) by using a 24-bit VXLAN Network Identifier (VNI), allowing up to 16 million logical networks.

### VXLAN Header Format

```
 0                   1                   2                   3
 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|R|R|R|R|I|R|R|R|            Reserved                           |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|                VXLAN Network Identifier (VNI) |   Reserved    |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
```

- **I Flag**: VNI valid flag (must be set to 1)
- **VNI**: 24-bit network identifier
- **Default UDP Port**: 4789

### VXLAN Interface Creation

The system creates VXLAN interfaces using the `ip link` command:

```bash
# IPv4 VXLAN interface
ip link add vt<PROFILE_ID> type vxlan \
    id <VNI> \
    local <LOCAL_IP> \
    df set|unset \
    remote <REMOTE_IP> \
    dstport 4789 \
    nolearning

# IPv6 VXLAN interface  
ip -6 link add 6vt<PROFILE_ID> type vxlan \
    id <VNI> \
    local <LOCAL_IPV6> \
    df set|unset \
    remote <REMOTE_IPV6> \
    dstport 4789 \
    nolearning \
    udp6zerocsumrx
```

### VNI Calculation

VNI is calculated from VLAN ID and an offset:

```bash
# Function: vlan_to_vni
VNI = VLAN_ID + VXLAN_VNI_OFFSET
```

### VXLAN Configuration Parameters

| Parameter | Description | Example |
|-----------|-------------|---------|
| `VXLAN_DST_PORT` | Destination UDP port | 4789 |
| `VXLAN_VNI_PRIMARY_OFFSET` | VNI offset for primary tunnel | 100000 |
| `VXLAN_VNI_SECONDARY_OFFSET` | VNI offset for secondary tunnel | 200000 |
| `VXLAN_DONT_FRAGMENT` | Set DF bit in outer IP header | 0 or 1 |
| `VXLAN_L2_PROXY` | Enable L2 proxy for ARP/ND | 0 or 1 |
| `PRIMARY_FORCE_FRAGMENT` | Force fragmentation | 0 or 1 |

### VXLAN Interface Naming

```
vt<NETWORK_PROFILE_ID>          - Primary IPv4 VXLAN
6vt<NETWORK_PROFILE_ID>         - Primary IPv6 VXLAN
vt<NETWORK_PROFILE_ID>_1        - Secondary IPv4 VXLAN
6vt<NETWORK_PROFILE_ID>_1       - Secondary IPv6 VXLAN
vt<NETWORK_PROFILE_ID>-<VLAN>   - VLAN-tagged VXLAN
```

### VXLAN Encapsulation Overhead

```
Outer Ethernet Header:    14 bytes
Outer IP Header:          20 bytes (IPv4) / 40 bytes (IPv6)
UDP Header:                8 bytes
VXLAN Header:              8 bytes
-----------------------------------
Total IPv4 Overhead:      50 bytes
Total IPv6 Overhead:      70 bytes
```

---

## EoGRE (Ethernet over GRE)

### Overview

EoGRE (Ethernet over Generic Routing Encapsulation) encapsulates Layer 2 Ethernet frames inside GRE packets for transport over Layer 3 networks. Unlike standard GRE which carries Layer 3 packets, EoGRE uses `gretap` to preserve full Ethernet frames including MAC addresses.

### EoGRE Header Format

```
Outer IP Header (20/40 bytes)
+------------------------+
| GRE Header (4-8 bytes) |
+------------------------+
| Inner Ethernet Frame   |
+------------------------+
```

GRE Header:
```
 0                   1                   2                   3
 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|C|R|K|S|  Reserved0  | Ver |         Protocol Type            |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|                      Key (optional)                           |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
```

### EoGRE Interface Creation

```bash
# IPv4 GRE TAP interface
ip link add gt<PROFILE_ID> type gretap \
    local <LOCAL_IP> \
    remote <REMOTE_IP> \
    nopmtudisc \
    key <KEY> \
    tos inherit

# IPv6 GRE TAP interface
ip link add 6gt<PROFILE_ID> type ip6gretap \
    local <LOCAL_IPV6> \
    remote <REMOTE_IPV6> \
    tos inherit
```

### EoGRE Interface Naming

```
gt<NETWORK_PROFILE_ID>          - Primary IPv4 GRE TAP
6gt<NETWORK_PROFILE_ID>         - Primary IPv6 GRE TAP
gt<NETWORK_PROFILE_ID>_1        - Secondary IPv4 GRE TAP
6gt<NETWORK_PROFILE_ID>_1       - Secondary IPv6 GRE TAP
gt<NETWORK_PROFILE_ID>.<VLAN>   - VLAN-tagged GRE TAP
```

### EoGRE Configuration

| Parameter | Description |
|-----------|-------------|
| `EOGRE_PRIMARY_KEY` | GRE key for primary tunnel |
| `EOGRE_SECONDARY_KEY` | GRE key for secondary tunnel |
| `PRIMARY_REMOTE_IP` | Remote endpoint IP (primary) |
| `SECONDARY_REMOTE_IP` | Remote endpoint IP (secondary) |

### EoGRE Encapsulation Overhead

```
Outer IP Header:      20 bytes (IPv4) / 40 bytes (IPv6)
GRE Header:            4 bytes (without key)
GRE Key:               4 bytes (optional)
-----------------------------------
Total IPv4 Overhead:  24-28 bytes
Total IPv6 Overhead:  44-48 bytes
```

---

## IPSec Tunnels

### Overview

IPSec provides encryption and authentication for tunnel traffic. It can be used standalone (VPN/AP-RAP) or combined with VXLAN or EoGRE for secure Layer 2 extension.

### IPSec Modes

1. **Transport Mode**: Encrypts only the payload
2. **Tunnel Mode**: Encrypts the entire original IP packet

### IPSec Configuration

The system uses strongSwan for IPSec implementation:

```
/etc/strongswan/ipsec.d/
├── primary_ipsec.conf
├── primary_ipsec.secrets
├── primary6_ipsec.conf
├── primary6_ipsec.secrets
├── secondary_ipsec.conf
├── secondary_ipsec.secrets
├── secondary6_ipsec.conf
└── secondary6_ipsec.secrets
```

### IPSec Subnet Configuration

For VXLAN over IPSec:
```bash
# IPv4: Protocol 17 (UDP) for VXLAN, Protocol 1 (ICMP)
leftsubnet=${LOCAL_IP}[17],${LOCAL_IP}[1]
rightsubnet=${REMOTE_IP}[17],${REMOTE_IP}[1]

# IPv6: Protocol 17 (UDP), Protocol 58 (ICMPv6)
leftsubnet=${LOCAL_IP}[17],${LOCAL_IP}[58]
rightsubnet=${REMOTE_IP}[17],${REMOTE_IP}[58]
```

For EoGRE over IPSec:
```bash
# Protocol 47 (GRE)
leftsubnet=${LOCAL_IP}[47]
rightsubnet=${REMOTE_IP}[47]
```

### IPSec with Virtual IP

When `IPSEC_VIRTUAL_IP_ENABLED=1`, the tunnel uses dynamically assigned virtual IPs:
```bash
IPSEC_PRIMARY_VIRTUALIP=<assigned_vip>
IPSEC_SECONDARY_VIRTUALIP=<assigned_vip>
```

### IPSec Overhead

```
ESP Header:           8 bytes
ESP Trailer:          2 bytes
ESP Auth:            12 bytes (varies)
IV (AES):            16 bytes
Padding:              0-15 bytes
-----------------------------------
Total Overhead:      ~38-53 bytes (approximate)
```

---

## UTUN (User-Space Tunnels)

### Overview

UTUN (User-space Tunnel) interfaces are virtual network interfaces that allow user-space applications to send and receive network packets. They are commonly used for VPN implementations and are the modern replacement for TUN/TAP interfaces on macOS.

### Interface Naming Convention

```
utun*    - User-space tunnel (macOS VPN)
tun*     - Generic TUN device (Layer 3, point-to-point)
tap*     - Generic TAP device (Layer 2, Ethernet)
```

### TUN vs TAP

| Feature | TUN | TAP |
|---------|-----|-----|
| OSI Layer | Layer 3 (IP) | Layer 2 (Ethernet) |
| Frame Type | IP packets | Ethernet frames |
| MAC Address | No | Yes |
| Broadcast | No | Yes |
| Use Case | Routing/VPN | Bridging/L2 VPN |

### Creating TAP Interfaces

```bash
# Create TAP interface
ip tuntap add <interface_name> mode tap

# Bring interface up
ip link set <interface_name> up

# Assign IP address
ip address add <ip>/<prefix> dev <interface_name>
```

### TAP Interface in Bridging

TAP interfaces can be added to bridges for Layer 2 connectivity:

```bash
# Add TAP to bridge
brctl addif <bridge_name> <tap_interface>

# Set interface up
ifconfig <bridge_name> up
ifconfig <tap_interface> up
```

### UTUN Characteristics (macOS)

- Created by the kernel on demand
- Named sequentially: `utun0`, `utun1`, etc.
- Used by VPN clients (e.g., OpenVPN, WireGuard)
- Point-to-point interfaces
- No broadcast support
- Automatically removed when owning process exits

---

## Tunnel Interface Naming Conventions

### Complete Interface Naming Reference

| Interface Pattern | Type | Description |
|-------------------|------|-------------|
| `vt<N>` | VXLAN | Primary IPv4 VXLAN tunnel for network profile N |
| `6vt<N>` | VXLAN | Primary IPv6 VXLAN tunnel for network profile N |
| `vt<N>_1` | VXLAN | Secondary IPv4 VXLAN tunnel |
| `6vt<N>_1` | VXLAN | Secondary IPv6 VXLAN tunnel |
| `vt<N>-<V>` | VXLAN | VXLAN tunnel with VLAN V |
| `gt<N>` | GRE | Primary IPv4 GRE TAP for network profile N |
| `6gt<N>` | GRE | Primary IPv6 GRE TAP for network profile N |
| `gt<N>_1` | GRE | Secondary IPv4 GRE TAP |
| `6gt<N>_1` | GRE | Secondary IPv6 GRE TAP |
| `gt<N>.<V>` | GRE | GRE TAP with VLAN V |
| `tunbr<N>` | Bridge | Tunnel bridge for network profile N |
| `tunbr<N>.<V>` | Bridge | Tunnel bridge with VLAN V |
| `br0` | Bridge | Default bridge interface |
| `eth0`, `eth1` | Ethernet | Physical Ethernet interfaces |
| `bond0` | Bond | Bonded interface (LAG) |
| `utun*` | UTUN | User-space tunnel (macOS) |

### Network Profile ID

The `<N>` in interface names represents the `NETWORK_PROFILE_ID`, which:
- Is a unique identifier for each network profile
- Can range from 1 to 16 (`NetworkProfileMaxLimit`)
- Determines tunnel isolation and VLAN mapping

---

## Tunnel Configuration Parameters

### Network Configuration File Structure

```
/tmp/network<NETWORK_PROFILE_ID>/
├── network.conf          # Network profile configuration
├── running               # Runtime state and status
├── gretap/
│   └── gretap.conf       # EoGRE-specific configuration
└── ipsec/
    ├── primary_ipsec.conf
    ├── primary_ipsec.secrets
    ├── secondary_ipsec.conf
    └── secondary_ipsec.secrets
```

### Key Configuration Parameters

| Parameter | Description |
|-----------|-------------|
| `NETWORK_PROFILE_ID` | Unique network profile identifier |
| `NETWORK_PROFILE_NAME` | Human-readable profile name |
| `NETWORK_TYPE` | Tunnel type (1-5) |
| `PRIMARY_REMOTE_IP` | Primary endpoint remote IP |
| `SECONDARY_REMOTE_IP` | Secondary endpoint remote IP |
| `PRIMARY_NETWORK_VLAN` | Local VLAN for primary tunnel |
| `SECONDARY_NETWORK_VLAN` | Local VLAN for secondary tunnel |
| `PRIMARY_NETWORK_PMTU` | Path MTU for primary tunnel |
| `SECONDARY_NETWORK_PMTU` | Path MTU for secondary tunnel |
| `ExternalInterface` | Source interface for primary tunnel |
| `SecExternalInterface` | Source interface for secondary tunnel |
| `NetworkExternalInterface` | Bridge interface for tunnel traffic |
| `NETWORK_PROBE_INTERVAL` | Tunnel health check interval (seconds) |
| `NETWORK_PING_RETRY_COUNT` | Retry count before failover |
| `NETWORK_PING_TIMEOUT` | Ping timeout (seconds) |
| `DISCONNECT_CLIENTS_ON_SWITCHING` | Deauth clients on tunnel switch |

### Running File State Variables

| Variable | Description |
|----------|-------------|
| `TYPE` | Current active tunnel (PRIMARY/SECONDARY) |
| `IFACE_NAME` | Current active interface name |
| `PRIMARY_IPADDR_FAMILY` | Address family (AF_INET/AF_INET6) |
| `SECONDARY_IPADDR_FAMILY` | Secondary address family |
| `PRIMARY_STATUS_IPV4` | IPv4 primary tunnel status |
| `PRIMARY_STATUS_IPV6` | IPv6 primary tunnel status |
| `SECONDARY_STATUS_IPV4` | IPv4 secondary tunnel status |
| `SECONDARY_STATUS_IPV6` | IPv6 secondary tunnel status |
| `PRIMARY_UPDOWN` | Primary tunnel up/down state |
| `SECONDARY_UPDOWN` | Secondary tunnel up/down state |
| `PRIMARY_NETWORK_MSS` | Calculated MSS for primary |
| `SECONDARY_NETWORK_MSS` | Calculated MSS for secondary |

---

## Tunnel Failover and High Availability

### Primary/Secondary Tunnel Architecture

```
                    ┌──────────────────┐
                    │   Access Point   │
                    └────────┬─────────┘
                             │
              ┌──────────────┴──────────────┐
              │                             │
    ┌─────────▼─────────┐       ┌───────────▼─────────┐
    │  Primary Tunnel   │       │  Secondary Tunnel   │
    │   (Active/Hot)    │       │  (Standby/Monitor)  │
    └─────────┬─────────┘       └───────────┬─────────┘
              │                             │
              ▼                             ▼
    ┌─────────────────────┐     ┌─────────────────────┐
    │  Primary Endpoint   │     │  Secondary Endpoint │
    │  (Remote Gateway)   │     │  (Remote Gateway)   │
    └─────────────────────┘     └─────────────────────┘
```

### Tunnel Types

```go
const (
    PrimaryTunnel   TunnelType = 0x1
    SecondaryTunnel TunnelType = 0x2
    NotSet          TunnelType = 0xFFFF
)
```

### Tunnel Health Monitoring

The `katunnel` Go package continuously monitors tunnel health:

1. **ICMP Ping Probes**: Periodic pings to remote endpoint
2. **RX Packet Counting**: Monitors received packet count increase
3. **IPSec SA Status**: Checks IPSec security association state

### Failover Logic

```
################################
Curr    |   Backup  |   Action
################################
UP      |   DOWN    |   SSID UP (stay on current)
UP      |   UP      |   SSID UP (stay on current)
UP      |   NIL     |   SSID UP (no backup configured)
################################
DOWN    |   UP      |   Switch to backup, SSID UP
################################
DOWN    |   DOWN    |   SSID DOWN
DOWN    |   NIL     |   SSID DOWN
################################
```

### Tunnel Switch Process

When failover occurs:

1. **Delete old interface** from bridge
2. **Create new interface** with new remote endpoint
3. **Add to bridge** (tunbr<N>)
4. **Update running file** with new state
5. **Optionally disconnect clients** if configured
6. **Restart tunnel DHCP** for IP acquisition
7. **Send tunnel switch event** (ATN_TUNNEL_SWITCH)

### Fallback Behavior

The system also supports fallback to primary when:
- Primary becomes reachable again
- Configurable fallback timer expires
- `PREFER_PRIMARY` mode is enabled

---

## MTU and Fragmentation

### Understanding Tunnel MTU

Tunnel encapsulation adds overhead that reduces the effective MTU for user traffic:

```
Standard Ethernet MTU:     1500 bytes
- Tunnel Overhead:         50-100+ bytes
= Effective Payload MTU:   1400-1450 bytes (typical)
```

### Tunnel Header Length Constants

```bash
# IPv4 tunnel header (IP + GRE/VXLAN)
IPV4_TUN_HDR_LEN=20    # Base IPv4 header

# IPv6 tunnel header
IPV6_TUN_HDR_LEN=40    # Base IPv6 header

# Additional overhead per tunnel type:
# GRE:    4 bytes (+ 4 for key)
# VXLAN:  8 bytes (header) + 8 bytes (UDP)
# IPSec:  ~38-53 bytes (ESP + auth)
```

### PMTU Discovery

The system supports Path MTU Discovery to automatically determine optimal MTU:

```go
func (network *NetworkProfile) discoverPMTU(endPoint *EndPoint) uint16 {
    // Uses script: discover_path_mtu
    // Parameters: externalIface, remoteIP, addrFamily, networkType
    // Returns: discovered PMTU value
}
```

### MSS Clamping

To prevent fragmentation, the system clamps TCP Maximum Segment Size (MSS):

```bash
# Calculate effective MSS
MTU=$(expr $PMTU - $tun_hdr)

# Write to interface sysfs
echo $MTU >/sys/devices/virtual/net/$VXLAN_IFACE/pmtu

# Update running configuration
sed -i "s/${tunnel_type}_NETWORK_MSS=.*/${tunnel_type}_NETWORK_MSS=${MTU}/g" $RUNNING_FILE
```

### VXLAN Fragmentation Options

| Option | Description |
|--------|-------------|
| `VXLAN_DONT_FRAGMENT` | Set DF bit (`df set`/`df unset`) |
| `PRIMARY_FORCE_FRAGMENT` | Force fragmentation on primary |
| `SECONDARY_FORCE_FRAGMENT` | Force fragmentation on secondary |

### DF Bit Behavior

```bash
if [ "$VXLAN_DONT_FRAGMENT" = "1" ]; then
    df_bit="set"    # Set DF bit, packets too large will be dropped
else
    df_bit="unset"  # Allow fragmentation
fi

ip link add $VXLAN_IFACE type vxlan ... df $df_bit ...
```

### MTU on Bridges

When creating tunnel interfaces, MTU is also set on the bridge:

```bash
check_and_set_mtu_on_bridge $LocalInterface
```

---

## Troubleshooting

### Common Issues and Solutions

#### 1. Tunnel Interface Not Created

**Symptoms**: Interface doesn't appear in `ip link show`

**Checks**:
```bash
# Check for VNI conflicts
check_and_report_vni_conflicts $VNI $VLAN $VXLAN_VNI_OFFSET $NETWORK_PROFILE_ID

# Verify remote IP is set
if [ "$REMOTE" = "" ]; then
    echo "Empty remote IP"
fi

# Check running file exists
ls -la /tmp/network<PROFILE_ID>/running
```

#### 2. Tunnel Shows UP But No Traffic

**Symptoms**: Interface up, ping fails

**Checks**:
```bash
# Verify bridge membership
brctl show tunbr<PROFILE_ID>

# Check RX/TX counters
cat /sys/class/net/vt<PROFILE_ID>/statistics/rx_packets
cat /sys/class/net/vt<PROFILE_ID>/statistics/tx_packets

# Verify remote endpoint reachability
ping -c 3 <REMOTE_IP>
```

#### 3. IPSec Tunnel Not Establishing

**Symptoms**: IPSec SA not installed

**Checks**:
```bash
# Check IPSec status
ipsec status
ipsec statusall

# Reload configuration
ipsec rereadall
ipsec update

# Check logs
journalctl -u strongswan
```

#### 4. Fragmentation Issues

**Symptoms**: Large packets dropped, TCP connections hang

**Checks**:
```bash
# Check PMTU
cat /sys/devices/virtual/net/$IFACE/pmtu

# Check DF bit setting
ip link show $IFACE

# Test with different packet sizes
ping -c 3 -s 1400 <REMOTE_IP>
ping -c 3 -s 1200 <REMOTE_IP>
```

#### 5. Tunnel Flapping

**Symptoms**: Frequent up/down state changes

**Checks**:
- Review probe interval: `NETWORK_PROBE_INTERVAL`
- Check retry count: `NETWORK_PING_RETRY_COUNT`
- Verify network stability to remote endpoint
- Check logs for pattern of failures

### Debugging Commands

```bash
# View tunnel interfaces
ip link show type vxlan
ip link show type gretap

# View bridge configuration
brctl show

# Check tunnel statistics
ip -s link show vt<PROFILE_ID>

# View VXLAN details
ip -d link show vt<PROFILE_ID>

# Monitor tunnel events
tail -f /var/log/messages | grep -i tunnel

# Check network profile configuration
cat /tmp/network<PROFILE_ID>/network.conf
cat /tmp/network<PROFILE_ID>/running
```

### Tunnel Status Events

| Event Code | Description |
|------------|-------------|
| `ATN_EOGRE_VAPS_UP` | EoGRE VAPs enabled |
| `ATN_EOGRE_VAPS_DOWN` | EoGRE VAPs disabled |
| `ATN_NET_TUNNEL_DOWN_EVT_WITH_REASON` | Tunnel down with reason |
| `ATN_TUNNEL_SWITCH` | Tunnel switched (failover/fallback) |

### Log Locations

- Network tunnel logs: `/var/log/messages`
- IPSec logs: `journalctl -u strongswan`
- Profile-specific logs: Unified logging with `NETWORK $NETWORK_PROFILE_ID` prefix

---

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              ACCESS POINT                                    │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                        WIRELESS CLIENTS                              │   │
│  │                    (SSIDs with Remote Bridging)                      │   │
│  └────────────────────────────────┬────────────────────────────────────┘   │
│                                   │                                         │
│                         ┌─────────▼─────────┐                              │
│                         │  VAP Interfaces   │                              │
│                         │  (wlan0, wlan1)   │                              │
│                         └─────────┬─────────┘                              │
│                                   │                                         │
│                         ┌─────────▼─────────┐                              │
│                         │  Tunnel Bridge    │                              │
│                         │  tunbr<N>         │                              │
│                         └─────────┬─────────┘                              │
│                                   │                                         │
│              ┌────────────────────┼────────────────────┐                   │
│              │                    │                    │                   │
│    ┌─────────▼─────────┐ ┌────────▼────────┐ ┌────────▼────────┐          │
│    │  VXLAN Interface  │ │ GRE Interface   │ │ IPSec Tunnel    │          │
│    │  vt<N> / 6vt<N>   │ │ gt<N> / 6gt<N>  │ │ (strongSwan)    │          │
│    └─────────┬─────────┘ └────────┬────────┘ └────────┬────────┘          │
│              │                    │                    │                   │
│              └────────────────────┼────────────────────┘                   │
│                                   │                                         │
│                         ┌─────────▼─────────┐                              │
│                         │  Physical/Bond    │                              │
│                         │  eth0/bond0       │                              │
│                         └─────────┬─────────┘                              │
│                                   │                                         │
└───────────────────────────────────┼─────────────────────────────────────────┘
                                    │
                          ┌─────────▼─────────┐
                          │   IP NETWORK      │
                          │  (Underlay)       │
                          └─────────┬─────────┘
                                    │
                          ┌─────────▼─────────┐
                          │  REMOTE GATEWAY   │
                          │  (Tunnel Server)  │
                          └───────────────────┘
```

---

## References

### Internal Code References

- **VXLAN Script**: `ap/rootfs/scripts/handle_vxlan_tunnel.sh`
- **EoGRE Script**: `ap/rootfs/scripts/handle_eogre_tunnel.sh`
- **IPSec Script**: `ap/rootfs/scripts/handle_ipsec_tunnel.sh`
- **Tunnel Handler**: `ap/rootfs/scripts/handle_tunnel.sh`
- **Go Tunnel Manager**: `ap/src/go/arista-ap/katunnel/`
- **Network Utilities**: `ap/src/go/arista-ap/nwutils/nwutils.go`
- **Tunnel Configuration**: `ap/src/go/arista-ap/ocagent/tunnel-config.go`

### External References

- [RFC 7348 - VXLAN](https://tools.ietf.org/html/rfc7348)
- [RFC 2784 - GRE](https://tools.ietf.org/html/rfc2784)
- [RFC 4301 - IPSec Architecture](https://tools.ietf.org/html/rfc4301)
- [Linux VXLAN Documentation](https://www.kernel.org/doc/Documentation/networking/vxlan.txt)
- [strongSwan Documentation](https://wiki.strongswan.org/)

---

*Document Version: 1.0*
*Last Updated: 2026-01-09*
