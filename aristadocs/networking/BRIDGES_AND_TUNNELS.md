# Bridges and Tunnels - Complete Technical Reference

This document provides a comprehensive guide to bridge and tunnel architecture on the Access Point (AP), covering how they work together to enable local bridging and remote bridging (tunneling) for wireless traffic.

---

## Table of Contents

1. [Overview](#overview)
2. [Bridge Architecture](#bridge-architecture)
3. [Bridge Types](#bridge-types)
4. [Bridge Management](#bridge-management)
5. [Tunnel Types](#tunnel-types)
6. [Tunnel Bridge Integration](#tunnel-bridge-integration)
7. [Traffic Flow](#traffic-flow)
8. [VLAN Handling](#vlan-handling)
9. [Interface Naming](#interface-naming)
10. [Bridge Configuration](#bridge-configuration)
11. [Tunnel Configuration](#tunnel-configuration)
12. [Failover and High Availability](#failover-and-high-availability)
13. [Troubleshooting](#troubleshooting)

---

## Overview

The AP uses Linux bridge interfaces to forward Layer 2 traffic between wireless clients and wired networks. Bridges can operate in two modes:

1. **Local Bridging**: Traffic exits through physical Ethernet ports
2. **Remote Bridging (Tunneling)**: Traffic is encapsulated and sent to remote endpoints

### Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              ACCESS POINT                                    │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                     WIRELESS CLIENTS (SSIDs)                         │   │
│  └────────────────────────────────┬────────────────────────────────────┘   │
│                                   │                                         │
│                         ┌─────────▼─────────┐                              │
│                         │   VAP Interfaces  │                              │
│                         │ (ath0, ath1, ...) │                              │
│                         └─────────┬─────────┘                              │
│                                   │                                         │
│              ┌────────────────────┴────────────────────┐                   │
│              │                                         │                   │
│    ┌─────────▼─────────┐                   ┌───────────▼───────────┐       │
│    │   Local Bridge    │                   │    Tunnel Bridge      │       │
│    │       br0         │                   │      tunbr&lt;N&gt;         │       │
│    └─────────┬─────────┘                   └───────────┬───────────┘       │
│              │                                         │                   │
│    ┌─────────▼─────────┐             ┌─────────────────┼─────────────────┐ │
│    │  Physical Port    │             │                 │                 │ │
│    │  eth0 / bond0     │      ┌──────▼──────┐   ┌──────▼──────┐         │ │
│    └─────────┬─────────┘      │  VXLAN      │   │  GRE TAP    │         │ │
│              │                │  vt&lt;N&gt;      │   │  gt&lt;N&gt;      │         │ │
│              │                └──────┬──────┘   └──────┬──────┘         │ │
│              │                       │                 │                 │ │
│              │                       └────────┬────────┘                 │ │
│              │                                │                          │ │
│              │                      ┌─────────▼─────────┐               │ │
│              │                      │  IPSec (optional) │               │ │
│              │                      │    strongSwan     │               │ │
│              │                      └─────────┬─────────┘               │ │
│              │                                │                          │ │
│              └────────────────────────────────┤                          │ │
│                                               │                          │ │
└───────────────────────────────────────────────┼──────────────────────────┘ │
                                                │                            │
                                      ┌─────────▼─────────┐                  │
                                      │   IP NETWORK      │                  │
                                      │   (Underlay)      │                  │
                                      └───────────────────┘                  │
```

---

## Bridge Architecture

### Linux Bridge Fundamentals

A Linux bridge is a software-based Layer 2 switch that:

- Learns MAC addresses from incoming frames
- Forwards frames based on destination MAC
- Floods unknown unicast, broadcast, and multicast
- Maintains a MAC address table (FDB)

### Bridge Creation

```bash
# Create a new bridge
brctl addbr br0

# Set bridge forwarding delay
brctl setfd br0 0

# Disable spanning tree (optional)
brctl stp br0 off
```

### Bridge Properties

| Property | Description |
|----------|-------------|
| `drop_noneth` | Drop non-Ethernet frames |
| `drop_vlanid0` | Drop VLAN ID 0 frames |
| `arp_ignore` | ARP ignore setting |
| `multicast_snooping` | Multicast snooping enable/disable |

### Bridge Initialization Script

```bash
add_bridge_iface() {
    local iface_name="$1"
    brctl addbr $iface_name
    
    # Configure bridge properties
    echo 1 >/sys/class/net/$iface_name/bridge/drop_noneth
    echo 1 >/sys/class/net/$iface_name/bridge/drop_vlanid0
}
```

---

## Bridge Types

### Default Bridge (br0)

The primary bridge for local traffic:

```bash
# Create default bridge
brctl addbr br0
brctl setfd br0 0

# Add physical interface
brctl addif br0 eth0
# or for link aggregation
brctl addif br0 bond0

ifconfig br0 up
```

### VLAN Bridge (br0.VLAN)

Per-VLAN bridges for network segmentation:

```bash
# Create VLAN subinterface
ip link add link eth0 name eth0.100 type vlan id 100

# Add to bridge
brctl addif br0.100 eth0.100
```

### Tunnel Bridge (tunbr&lt;N&gt;)

Dedicated bridges for tunneled traffic:

```go
func (confProfile *SecProfile) SetBridgeName(remoteBridgingEnabled bool, nwProfileID int64) {
    if remoteBridgingEnabled {
        confProfile.BridgeName = fmt.Sprintf("tunbr%v", nwProfileID)
    } else {
        confProfile.BridgeName = "br0"
    }
}
```

---

## Bridge Management

### Adding Interfaces to Bridges

```go
// AddIntfToBridge adds interfaces to the bridge.
func AddIntfToBridge(bridgeName, ifName string) error {
    if CheckBridgeInterface(bridgeName, ifName) {
        log.Printf("ifName %s is already added under bridge %s", ifName, bridgeName)
        return nil
    }
    cmd := []string{"brctl", "addif", bridgeName, ifName}
    err := aputils.ExecTimeout(cmd, aputils.MediumExecTimeout)
    return err
}
```

### Creating New Bridges

```go
// AddNewBridge adds a new bridge with default settings
func AddNewBridge(vbrName string) error {
    // Adding the new bridge interface
    cmd := []string{"brctl", "addbr", vbrName}
    if err := aputils.ExecTimeout(cmd, aputils.MediumExecTimeout); err != nil {
        return err
    }

    // Configure arp_ignore
    arpIgnoreFile := aputils.Ipv4ConfPath + vbrName + "/arp_ignore"
    os.WriteFile(arpIgnoreFile, []byte("1"), 0644)

    return nil
}
```

### Bridge Operations (C API)

```c
typedef enum {
    BRIDGE_OP_CREATE,    // brctl addbr
    BRIDGE_OP_DELETE,    // brctl delbr
    BRIDGE_OP_ADD_INTF,  // brctl addif
    BRIDGE_OP_DEL_INTF,  // brctl delif
} bridge_op_t;

int bridge_operation(bridge_op_t bridge_op,
                     const char* bridge_intf,
                     const char* port_name);
```

### Shell Bridge Management

```bash
check_and_add_bridge_iface() {
    VBRNAME=$1
    NETWORK_VLAN=$2
    IFACE_TO_ADD=$3

    interface_exists $VBRNAME
    if [ $? -eq 0 ]; then
        bridge_exist=1
    fi

    if [ "$bridge_exist" = "0" ]; then
        check_and_add_bridge $VBRNAME 1

        if [ "$NETWORK_VLAN" = "0" ]; then
            brctl addif $VBRNAME $ETH_INTERFACE
        else
            ip link add link $ETH_INTERFACE name $ETH_INTERFACE.$NETWORK_VLAN type vlan id $NETWORK_VLAN
            brctl addif $VBRNAME $ETH_INTERFACE.$NETWORK_VLAN
        fi
    fi

    brctl addif $VBRNAME $IFACE_TO_ADD
}
```

---

## Tunnel Types

### Network Type Enumeration

```go
const (
    Eogre          NetworkType = 0x1  // Ethernet over GRE
    EogreOverIPsec NetworkType = 0x2  // EoGRE with IPSec
    VxLAN          NetworkType = 0x3  // VXLAN
    VpnWithIPSec   NetworkType = 0x4  // VPN with IPSec
    VxlanOverIPsec NetworkType = 0x5  // VXLAN with IPSec
)
```

### Tunnel Interface Types

```go
const (
    VtIf Interface = 0x1  // VXLAN tunnel interface (vt*)
    GtIf Interface = 0x2  // GRE tunnel interface (gt*)
)
```

### VXLAN Tunnel

```bash
# Create VXLAN interface
ip link add vt1 type vxlan id $VNI \
    local $LocalIP \
    remote $REMOTE \
    dstport 4789 \
    df set \
    nolearning

# Configure MTU and MAC
ifconfig vt1 mtu 1500
ifconfig vt1 hw ether $tunnel_fake_mac

# Add to tunnel bridge
brctl addif tunbr1 vt1
```

### GRE TAP Tunnel

```bash
# Create GRE TAP interface (IPv4)
ip link add gt1 type gretap \
    local $LocalIP \
    remote $REMOTE \
    nopmtudisc

# Create GRE TAP interface (IPv6)
ip link add 6gt1 type ip6gretap \
    local $LocalIP \
    remote $REMOTE

# Add to tunnel bridge
brctl addif tunbr1 gt1
```

---

## Tunnel Bridge Integration

### Bridge with VXLAN Support

```go
// AddNewBridgeWithVxVlan creates a new bridge with VxVlan support
func AddNewBridgeWithVxVlan(vbrName string, nwType NetworkType, netID uint32, vlanID uint16, profileID int) error {

    if err := AddNewBridge(vbrName); err != nil {
        return err
    }

    if nwType == VxLAN || nwType == VxlanOverIPsec {
        if err := HandleVxlanWired(vlanID, netID, profileID); err != nil {
            return err
        }
    }
    return nil
}
```

### Tunnel Bridge Naming

| Bridge Pattern | Description |
|----------------|-------------|
| `tunbr&lt;N&gt;` | Tunnel bridge for network profile N |
| `tunbr&lt;N&gt;.&lt;V&gt;` | Tunnel bridge with VLAN V |

### Bridge Name Resolution

```go
func getSanitizedNetworkConf(netConf *WiredNetwork) (*WiredNetworkProfile, error) {
    nwProfile.BridgeName = "br0"

    if netConf.RemoteBridgingEnabled {
        nwProfile.NetworkProfileID = uint32(netConf.NetworkProfileID)
        nwProfile.BridgeName = fmt.Sprintf("tunbr%v", nwProfile.NetworkProfileID)
    }

    nwProfile.ExtInterface = nwProfile.BridgeName
    if nwProfile.VlanID != 0 {
        nwProfile.ExtInterface = fmt.Sprintf("%s.%v", nwProfile.BridgeName, nwProfile.VlanID)
    }

    return &nwProfile, nil
}
```

### Adding Tunnel Interface to Bridge

```bash
# VXLAN interface to bridge
brctl addif $VXLAN_BRIDGE_IFACE $VXLAN_IFACE
ifconfig $VXLAN_BRIDGE_IFACE up
ifconfig $VXLAN_IFACE up

# GRE interface to bridge
brctl addif $GRETAP_BRIDGE_IFACE $GRETAP_IFACE
ifconfig $GRETAP_BRIDGE_IFACE up
ifconfig $GRETAP_IFACE up
```

---

## Traffic Flow

### Local Bridging Flow

```
┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐
│  Client  │───▶│   VAP    │───▶│   br0    │───▶│   eth0   │───▶ Network
│          │    │  (ath0)  │    │          │    │          │
└──────────┘    └──────────┘    └──────────┘    └──────────┘
```

### Remote Bridging (Tunnel) Flow

```
┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐
│  Client  │───▶│   VAP    │───▶│  tunbr1  │───▶│   vt1    │───▶│   eth0   │
│          │    │  (ath0)  │    │          │    │ (VXLAN)  │    │          │
└──────────┘    └──────────┘    └──────────┘    └──────────┘    └──────────┘
                                                      │
                                               ┌──────▼──────┐
                                               │  VXLAN      │
                                               │ Encapsulate │
                                               └──────┬──────┘
                                                      │
                                               ┌──────▼──────┐
                                               │   Remote    │
                                               │  Gateway    │
                                               └─────────────┘
```

### Bridge Selection Logic

```bash
get_all_bridges_for_profile() {
    if [ "$remote_bridging_enabled" = "1" ]; then
        network_id=$(cfg_get NETWORK_PROFILE_ID $profile_dir/profile.conf)
        if [ "$vlan" = "0" ]; then
            br_name="tunbr$network_id"
        else
            br_name="tunbr$network_id.$vlan"
        fi
    else
        if [ "$vlan" = "0" ]; then
            br_name="br0"
        else
            br_name="br0.$vlan"
        fi
    fi
}
```

---

## VLAN Handling

### VLAN Interface Creation

```bash
# Create VLAN subinterface with MVRP
ip link add link $ETH_INTERFACE name $ETH_INTERFACE.$NETWORK_VLAN \
    type vlan id $NETWORK_VLAN mvrp $mvrp_status

# Configure VLAN QoS mapping
vconfig set_ingress_map $ETH_INTERFACE.$NETWORK_VLAN 0 0
vconfig set_ingress_map $ETH_INTERFACE.$NETWORK_VLAN 1 1
# ... up to priority 7
```

### Dynamic VLAN Support

```bash
DYNAMIC_VLAN_ENABLED=$(cfg_get DYNAMIC_VLAN_ENABLED $profile_conf)
ROLE_PROFILE_ENABLED=$(cfg_get ROLE_PROFILE_ENABLED $profile_conf)

if [ "$DYNAMIC_VLAN_ENABLED" = "1" -o "$ROLE_PROFILE_ENABLED" = "1" ]; then
    DYNAMIC_VLAN=$(cfg_get ALL_EXTRA_SSID_VLAN_LIST $profile_conf)
    VLAN_IDS_LIST="$VLAN_IDS_LIST $DYNAMIC_VLAN"
fi
```

### Per-VLAN Tunnel Interfaces

```bash
# Create VXLAN VLAN subinterface
create_vxlan_vlan_interface() {
    local VLAN_IDS_LIST=$4

    for VLAN_ID in $VLAN_IDS_LIST; do
        create_tunnel_interface "$VLAN_ID" "$profile_conf" "$tunnel_type" \
            "$PARENT_VXLAN_IFACE" "$PROFILE_TYPE" &
    done
    sys_waitfor_bg_procs
}
```

### Fake MAC for VLANs

```bash
# Generate unique MAC per VLAN
iface_mac=$(ap_mac_get eth0)
iface_fake_mac=$(fakemac "$iface_mac" "$NETWORK_VLAN" 2>/dev/null)
ifconfig $ETH_INTERFACE."$NETWORK_VLAN" hw ether "$iface_fake_mac"
```

---

## Interface Naming

### Complete Naming Reference

| Interface Pattern | Type | Description |
|-------------------|------|-------------|
| `br0` | Bridge | Default local bridge |
| `br0.&lt;V&gt;` | Bridge | VLAN V local bridge |
| `tunbr&lt;N&gt;` | Bridge | Tunnel bridge for profile N |
| `tunbr&lt;N&gt;.&lt;V&gt;` | Bridge | Tunnel bridge with VLAN V |
| `eth0` | Ethernet | Primary physical port |
| `eth1` | Ethernet | Secondary physical port |
| `bond0` | Bond | Link aggregation interface |
| `eth0.&lt;V&gt;` | VLAN | VLAN V on eth0 |
| `vt&lt;N&gt;` | VXLAN | Primary IPv4 VXLAN tunnel |
| `6vt&lt;N&gt;` | VXLAN | Primary IPv6 VXLAN tunnel |
| `vt&lt;N&gt;_1` | VXLAN | Secondary VXLAN tunnel |
| `gt&lt;N&gt;` | GRE | Primary IPv4 GRE TAP |
| `6gt&lt;N&gt;` | GRE | Primary IPv6 GRE TAP |
| `gt&lt;N&gt;_1` | GRE | Secondary GRE TAP |
| `ath&lt;R&gt;.&lt;S&gt;` | Wireless | VAP on radio R, SSID S |
| `vle0` | Virtual | Mesh virtual link |

### External Interface Selection

```bash
if [ -e "$AP_TMPDIR/mesh_enabled" ]; then
    ETH_INTERFACE="vle0"
else
    if [ -e "$AP_TMPDIR/link_aggr_enabled" ]; then
        ETH_INTERFACE="bond0"
    else
        ETH_INTERFACE="eth0"
    fi
fi
```

---

## Bridge Configuration

### IPv6 Handling

```bash
check_and_add_bridge() {
    local bridge_name=$1
    local enable_ipv6=$2

    add_bridge_iface $bridge_name
    remove_default_mcast_snooping $bridge_name

    if [[ "$bridge_name" == tunbr* ]]; then
        if [[ -z "$enable_ipv6" || $enable_ipv6 -eq 0 ]]; then
            handle_disable_ipv6 "$bridge_name" 1
        fi
    fi
}
```

### Multicast Snooping

```bash
remove_default_mcast_snooping() {
    local bridge_name=$1
    echo 0 > /sys/devices/virtual/net/$bridge_name/bridge/multicast_snooping
}
```

### Bridge Port Settings

```bash
# Set hairpin mode for bridge port
echo 1 > /sys/class/net/$BRIDGE/brif/$PORT/hairpin_mode

# Set L2TIF (Layer 2 Tunnel Interface Flag)
echo $profile_id > /sys/devices/virtual/net/$PORT/brport/hotspot_l2tif
```

---

## Tunnel Configuration

### VXLAN Parameters

| Parameter | Description |
|-----------|-------------|
| `VNI` | VXLAN Network Identifier |
| `dstport` | Destination UDP port (default 4789) |
| `df` | Don't Fragment bit (set/unset) |
| `nolearning` | Disable MAC learning |
| `local` | Local IP address |
| `remote` | Remote endpoint IP |

### VNI Calculation

```bash
VNI = VLAN_ID + VXLAN_VNI_OFFSET
```

### GRE Parameters

| Parameter | Description |
|-----------|-------------|
| `local` | Local IP address |
| `remote` | Remote endpoint IP |
| `nopmtudisc` | Disable PMTU discovery |
| `key` | Optional GRE key |

### MTU Configuration

```bash
# Set MTU on tunnel interface
ifconfig $TUNNEL_IFACE mtu $MTU

# Configure MSS clamping
configure_mss $MTU "$TUNNEL_TYPE"

# Write PMTU to sysfs
echo $MTU > /sys/devices/virtual/net/$TUNNEL_IFACE/pmtu
```

---

## Failover and High Availability

### Primary/Secondary Tunnels

```
################################
Curr    |   Backup  |   Action
################################
UP      |   DOWN    |   Stay on current
UP      |   UP      |   Stay on current
DOWN    |   UP      |   Switch to backup
DOWN    |   DOWN    |   SSIDs DOWN
################################
```

### Tunnel Switch Process

```bash
# When failover occurs:

# 1. Remove old interface from bridge
brctl delif $BRIDGE $old_iface_name

# 2. Create new tunnel interface
ip link add $new_iface type vxlan ...

# 3. Add new interface to bridge
brctl addif $BRIDGE $new_iface

# 4. Bring up interfaces
ifconfig $BRIDGE up
ifconfig $new_iface up
```

### Protocol Switch (IPv4 ↔ IPv6)

```bash
if [ "$PROTOCOL_SWITCH" = "IPV6_TO_IPV4" ]; then
    # Remove IPv6 interface from bridge
    brctl delif $VXLAN_BRIDGE_IFACE $old_iface_name

    # Create IPv4 interface
    ip link add $VXLAN_IFACE type vxlan ...

    # Add to bridge
    brctl addif $VXLAN_BRIDGE_IFACE $VXLAN_IFACE
fi
```

---

## Troubleshooting

### View Bridge Configuration

```bash
# List all bridges
brctl show

# Show specific bridge details
brctl showmacs br0
brctl showstp br0

# Show bridge interfaces
ls /sys/class/net/br0/brif/
```

### View Tunnel Interfaces

```bash
# List VXLAN interfaces
ip link show type vxlan
ip -d link show vt1

# List GRE interfaces
ip link show type gretap
ip -d link show gt1
```

### Check Interface State

```bash
# Interface status
ifconfig tunbr1
cat /sys/class/net/vt1/operstate

# Statistics
ip -s link show vt1
cat /sys/class/net/vt1/statistics/rx_packets
cat /sys/class/net/vt1/statistics/tx_packets
```

### Common Issues

| Issue | Cause | Solution |
|-------|-------|----------|
| Interface not in bridge | Failed brctl addif | Check interface exists, bridge exists |
| Tunnel UP, no traffic | Wrong VNI/Remote IP | Verify tunnel parameters |
| Bridge not forwarding | STP blocking | Check `brctl showstp` |
| VLAN traffic dropped | Missing VLAN interface | Create eth0.$VLAN |
| IPv6 not working | IPv6 disabled | Check `disable_ipv6` sysctl |

### Debugging Commands

```bash
# Check bridge FDB entries
bridge fdb show br br0

# Monitor bridge events
ip monitor link

# Check tunnel connectivity
ping -c 3 $REMOTE_ENDPOINT

# View iptables/ebtables rules
iptables -L -v -n
ebtables -L
```

---

## References

### Internal Code References

- **Bridge Management Script**: `ap/rootfs/scripts/bridge_mgmt.sh`
- **Bridge Initialization**: `ap/rootfs/scripts/rc.bridge`
- **Network Utilities (Shell)**: `ap/rootfs/scripts/utils/network`
- **Network Utilities (Go)**: `ap/src/go/arista-ap/nwutils/nwutils.go`
- **VXLAN Handler**: `ap/rootfs/scripts/handle_vxlan_tunnel.sh`
- **EoGRE Handler**: `ap/rootfs/scripts/handle_eogre_tunnel.sh`
- **VLAN API**: `ap/src/common/src/utils/vlan_api.c`
- **Wired Features**: `ap/src/go/arista-ap/wiredfeatures/network_feature.go`
- **Security Profile**: `ap/src/go/arista-ap/config/sec_profile.go`
- **Misc Functions**: `ap/rootfs/scripts/ap_misc_functions`

### External References

- [Linux Bridge Documentation](https://wiki.linuxfoundation.org/networking/bridge)
- [brctl man page](https://linux.die.net/man/8/brctl)
- [VXLAN RFC 7348](https://tools.ietf.org/html/rfc7348)
- [GRE RFC 2784](https://tools.ietf.org/html/rfc2784)

---

*Document Version: 1.0*
*Last Updated: 2026-01-10*

