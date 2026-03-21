# Networking Interfaces Documentation

## Access Point (AP) Network Interface Architecture

This comprehensive document covers all networking interfaces used in the AP codebase, including their types, configuration, lifecycle management, and implementation details.

---

## Table of Contents

1. [Introduction](#1-introduction)
2. [Interface Overview](#2-interface-overview)
3. [Physical Ethernet Interfaces](#3-physical-ethernet-interfaces)
4. [Bonded/LAG Interfaces](#4-bondedlag-interfaces)
5. [VLAN Interfaces](#5-vlan-interfaces)
6. [Bridge Interfaces](#6-bridge-interfaces)
7. [Wireless Interfaces](#7-wireless-interfaces)
8. [Tunnel Interfaces](#8-tunnel-interfaces)
9. [Mesh Interfaces](#9-mesh-interfaces)
10. [Loopback and Special Interfaces](#10-loopback-and-special-interfaces)
11. [Interface Hierarchy and Relationships](#11-interface-hierarchy-and-relationships)
12. [Interface Configuration](#12-interface-configuration)
13. [Interface Lifecycle Management](#13-interface-lifecycle-management)
14. [Interface Statistics and Monitoring](#14-interface-statistics-and-monitoring)
15. [Codebase Implementation](#15-codebase-implementation)
16. [CLI Commands](#16-cli-commands)
17. [Troubleshooting](#17-troubleshooting)
18. [Best Practices](#18-best-practices)

---

## 1. Introduction

### Purpose

The Access Point uses multiple types of network interfaces to handle:
- Wired uplink connectivity to the network infrastructure
- Wireless connectivity for client devices
- Traffic segmentation using VLANs
- Layer 2 bridging between wired and wireless
- Tunnel encapsulation for overlay networks
- Mesh networking for extended coverage

### Interface Categories

```
┌─────────────────────────────────────────────────────────────────────┐
│                    AP NETWORK INTERFACE TYPES                       │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  Physical Layer                                                     │
│  ├── eth0          (Primary Ethernet)                              │
│  ├── eth1          (Secondary Ethernet)                            │
│  └── wifiN         (Radio Interfaces)                              │
│                                                                     │
│  Virtual Layer                                                      │
│  ├── bond0         (Bonded Interface)                              │
│  ├── eth0.VLAN     (VLAN Sub-interfaces)                           │
│  ├── brN           (Bridge Interfaces)                             │
│  ├── athN          (Virtual Access Points)                         │
│  ├── greN          (GRE Tunnel Interfaces)                         │
│  ├── vtN           (VXLAN Tunnel Interfaces)                       │
│  └── vle0/bre0     (Mesh Virtual Ethernet)                         │
│                                                                     │
│  Special Interfaces                                                 │
│  ├── lo            (Loopback)                                      │
│  ├── monN          (Monitor Interfaces)                            │
│  └── monitN        (Monitoring Interfaces)                         │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 2. Interface Overview

### Interface Naming Conventions

| Pattern | Type | Description | Example |
|---------|------|-------------|---------|
| `eth[0-1]` | Physical | Physical Ethernet ports | eth0, eth1 |
| `bond0` | Virtual | Bonded interface (LAG) | bond0 |
| `eth[0-1].&lt;vlan&gt;` | Virtual | VLAN sub-interface | eth0.100 |
| `bond0.&lt;vlan&gt;` | Virtual | VLAN on bond | bond0.100 |
| `br[0-N]` | Virtual | Bridge interface | br0 |
| `br-lan&lt;N&gt;` | Virtual | LAN bridge | br-lan100 |
| `wifi[0-3]` | Physical | Radio interface | wifi0, wifi1 |
| `ath[0-N]` | Virtual | Virtual AP (VAP) | ath0, ath1 |
| `gt[0-1]` | Virtual | GRE tunnel | gt0, gt1 |
| `vt[0-1]` | Virtual | VXLAN tunnel | vt0, vt1 |
| `vle0` | Virtual | Mesh virtual link egress | vle0 |
| `bre0` | Virtual | Mesh bridge end | bre0 |
| `mon[0-N]` | Virtual | Monitor interface | mon0 |

### Interface Hierarchy

```
                            ┌───────────┐
                            │    lo     │
                            │ (loopback)│
                            └───────────┘
                                  
       ┌──────────────────────────┼──────────────────────────┐
       │                          │                          │
  ┌────┴────┐                ┌────┴────┐               ┌────┴────┐
  │  eth0   │                │  eth1   │               │  wifiN  │
  │(primary)│                │(second) │               │ (radio) │
  └────┬────┘                └────┬────┘               └────┬────┘
       │                          │                          │
       └──────────┬───────────────┘                          │
                  │                                          │
             ┌────┴────┐                               ┌────┴────┐
             │  bond0  │                               │  athN   │
             │  (LAG)  │                               │  (VAP)  │
             └────┬────┘                               └────┬────┘
                  │                                          │
        ┌─────────┼─────────┐                               │
        │         │         │                               │
   ┌────┴───┐ ┌───┴────┐ ┌──┴───┐                          │
   │eth0.100│ │eth0.200│ │bond0 │                          │
   │(VLAN)  │ │(VLAN)  │ │.300  │                          │
   └────┬───┘ └───┬────┘ └──┬───┘                          │
        │         │         │                               │
        └─────────┼─────────┘                               │
                  │                                          │
             ┌────┴────┐                                     │
             │  br0    │─────────────────────────────────────┘
             │(bridge) │
             └─────────┘
```

---

## 3. Physical Ethernet Interfaces

### Overview

Physical Ethernet interfaces provide the wired uplink connectivity to the network infrastructure.

| Interface | Purpose | Default State |
|-----------|---------|---------------|
| eth0 | Primary uplink | Active |
| eth1 | Secondary uplink (if supported) | Standby/Active |

### Interface Properties

```bash
# Get interface MAC address
iface_mac=$(ap_mac_get eth0)

# Check interface state
ip link show eth0

# Interface statistics location
/sys/class/net/eth0/statistics/
```

### Ethernet Interface Configuration

```c
// Interface statistics structure (from networking.c)
bool get_interface_stats(const char* interface_name, interface_stats* stats)
{
  FILE* fh = fopen(PROCNET_DEV_PATH, "r");
  if (!fh) {
    LOG(LOG_ERR, "cannot open %s. Error %s", PROCNET_DEV_PATH, strerror(errno));
    return false;
  }
  // Parse /proc/net/dev for interface statistics
  // rx_packets, tx_packets, rx_bytes, tx_bytes, etc.
}
```

### Link Speed Configuration

```bash
# Check link speed
ethtool eth0

# Configure link speed (from setuplinkaggr)
setuplinkspeed() {
    # Match eth0 and eth1 link speeds for LAG
    if [ "$SEC_PORT_ETH_LINK_SPEED" = "1000" ]; then
        # Set eth0 speed same as eth1 default speed
    fi
}
```

### Dual Uplink Support

```go
// Dual uplink constants (from uplink_monitor.go)
var (
    DisableDualUplink      = "disable_dual_uplink"
    DualUplinkDir          = apOpt + "/dual_uplink/"
    DualUplinkEnabledFile  = DualUplinkDir + "dual_uplink_enabled"
    DualUplinkMaxCounter   = 12 // 60 seconds
)

// Get active uplink interface
func BackupUplink() string {
    if EthernetConfigMap[ActiveUplinkInterface] == cst.EthIntf0 {
        return cst.EthIntf1
    }
    return cst.EthIntf0
}
```

---

## 4. Bonded/LAG Interfaces

### Overview

Bonded interfaces (Link Aggregation) combine multiple physical Ethernet interfaces for redundancy and/or increased bandwidth.

```
┌─────────────────────────────────────────────────────────────────────┐
│                    BONDING ARCHITECTURE                             │
│                                                                     │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │                       bond0                                  │   │
│  │                  (Bonded Interface)                          │   │
│  └─────────────────────────┬───────────────────────────────────┘   │
│                            │                                        │
│              ┌─────────────┴─────────────┐                         │
│              │                           │                          │
│        ┌─────┴─────┐               ┌─────┴─────┐                   │
│        │   eth0    │               │   eth1    │                   │
│        │ (slave 1) │               │ (slave 2) │                   │
│        └───────────┘               └───────────┘                   │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

### Bonding Modes

| Mode | Name | Description |
|------|------|-------------|
| 0 | balance-rr | Round-robin transmit policy |
| 1 | active-backup | Active-standby failover (default for dual uplink) |
| 2 | balance-xor | XOR hash-based transmit policy |
| 3 | broadcast | Transmit on all slaves |
| 4 | 802.3ad | LACP (Link Aggregation Control Protocol) |
| 5 | balance-tlb | Adaptive transmit load balancing |
| 6 | balance-alb | Adaptive receive/transmit load balancing |

### Bonding Setup

```bash
# Setup link aggregation (from functions)
setuplinkaggr() {
    local BOND0="bond0"
    local mode

    # Load bonding kernel module
    insmod $MODULE_PATH/bonding.ko

    # Bring down physical interfaces
    ifconfig eth0 down
    ifconfig eth1 down

    # Get bonding mode (default: 4 for LACP)
    mode=$(cat $AP_TMPDIR/link_aggr_enabled)
    if [ -z "$mode" ]; then
        mode=4
    fi

    # Configure bonding mode
    echo $mode >/sys/devices/virtual/net/$BOND0/bonding/mode

    # Add slaves to bond
    echo "+eth0" >/sys/class/net/$BOND0/bonding/slaves
    echo "+eth1" >/sys/class/net/$BOND0/bonding/slaves

    # Bring up interfaces
    bring_up_iface "eth0"
    bring_up_iface "eth1"
    bring_up_iface $BOND0
}
```

### Active-Backup Configuration

```bash
# Configure active-backup mode
if [ "$mode" = "1" ]; then
    # Set primary interface
    pref_intf="eth0"
    echo "$pref_intf" >/sys/devices/virtual/net/$BOND0/bonding/primary

    # Wait 60 seconds before considering interface as up (avoid flapping)
    echo 60000 >/sys/devices/virtual/net/$BOND0/bonding/updelay

    # Wait 30 seconds before considering interface as down
    echo 30000 >/sys/devices/virtual/net/$BOND0/bonding/downdelay

    # Set active slave as eth0 at bootup
    echo "eth0" >/sys/devices/virtual/net/$BOND0/bonding/active_slave
fi
```

### Bonding Mode Detection

```go
// BondingMode returns the mode for the configured bond interface
func BondingMode() int {
    if utils.IsFileNotExist(path.LinkAggrEnabledFile) ||
       utils.IsFileNotExist(path.BondingModeFile) {
        return -1
    }

    output, err := os.ReadFile(path.BondingModeFile)
    if err != nil {
        return -1
    }

    parts := strings.Fields(string(output))
    if len(parts) < 2 {
        return -1
    }

    mode, _ := strconv.Atoi(parts[1])
    return mode
}
```

### Bonding sysfs Paths

| Path | Purpose |
|------|---------|
| `/sys/class/net/bond0/bonding/mode` | Bonding mode |
| `/sys/class/net/bond0/bonding/slaves` | Slave interfaces |
| `/sys/class/net/bond0/bonding/primary` | Primary interface |
| `/sys/class/net/bond0/bonding/active_slave` | Currently active slave |
| `/sys/class/net/bond0/bonding/miimon` | Link monitoring interval |
| `/sys/class/net/bond0/bonding/updelay` | Delay before marking up |
| `/sys/class/net/bond0/bonding/downdelay` | Delay before marking down |

---

## 5. VLAN Interfaces

### Overview

VLAN (Virtual LAN) interfaces provide traffic segmentation by creating sub-interfaces on physical or bonded interfaces.

```
┌─────────────────────────────────────────────────────────────────────┐
│                    VLAN INTERFACE HIERARCHY                         │
│                                                                     │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │              Parent Interface (eth0/bond0)                   │   │
│  └────────────────────────┬────────────────────────────────────┘   │
│                           │                                         │
│         ┌─────────────────┼─────────────────┐                      │
│         │                 │                 │                       │
│    ┌────┴────┐       ┌────┴────┐       ┌────┴────┐                 │
│    │eth0.100 │       │eth0.200 │       │eth0.300 │                 │
│    │VLAN 100 │       │VLAN 200 │       │VLAN 300 │                 │
│    │ (Mgmt)  │       │ (Data)  │       │ (Guest) │                 │
│    └─────────┘       └─────────┘       └─────────┘                 │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

### VLAN Interface Creation

```bash
# Create VLAN interface with MVRP support
ip link add link $ETH_INTERFACE name $ETH_INTERFACE.$NETWORK_VLAN \
    type vlan id $NETWORK_VLAN mvrp $mvrp_status

# Configure QoS mappings
vconfig set_egress_map $ETH_INTERFACE.$NETWORK_VLAN 0 0
vconfig set_egress_map $ETH_INTERFACE.$NETWORK_VLAN 1 1
# ... (0-7 priority mappings)
vconfig set_ingress_map $ETH_INTERFACE.$NETWORK_VLAN 0 0
vconfig set_ingress_map $ETH_INTERFACE.$NETWORK_VLAN 1 1
# ... (0-7 priority mappings)
```

### VLAN Types

```go
// VLAN type definitions (from vlan.go)
type Vlan struct {
    nwutils.InterfaceName
}

// IsSsidVlan checks if vlan is of type SSID
func (v Vlan) IsSsidVlan() bool

// IsNetworkVlan checks if vlan is of type network
func (v Vlan) IsNetworkVlan() bool

// IsCommunicationVlan checks if vlan is of type communication
func (v Vlan) IsCommunicationVlan() bool

// IsVapVlan checks if vlan is of type vap
func (v Vlan) IsVapVlan() bool

// IsServiceVlan checks if vlan is of type service
func (v Vlan) IsServiceVlan() bool
```

### VLAN Categories

| Type | Purpose | Example |
|------|---------|---------|
| Communication VLAN | AP management traffic | eth0.100 |
| Network VLAN | Tunnel network traffic | eth0.200 |
| SSID VLAN | Per-SSID traffic segregation | eth0.300 |
| VAP VLAN | Virtual AP traffic | ath0.400 |
| Service VLAN | Special service traffic | eth0.500 |
| Dynamic VLAN | RADIUS-assigned VLANs | eth0.NNN |

### Fake MAC Address

```bash
# Assign fake MAC address to VLAN interfaces (non-communication VLANs)
if [ "$COMMUNICATION_VLAN" != "$NETWORK_VLAN" ]; then
    iface_mac=$(ap_mac_get eth0)
    iface_fake_mac=$(fakemac "$iface_mac" "$NETWORK_VLAN" 2>/dev/null)
    /sbin/ifconfig $ETH_INTERFACE."$NETWORK_VLAN" hw ether "$iface_fake_mac"
fi
```

### VLAN Manager

```go
// HandleVlanAdd adds a VLAN interface (from vlan_manager.go)
func HandleVlanAdd(ifaceCfg *nwutils.Ifcfg) error {
    // Parse ifcfg files and handle VLAN add operations
}

// VLAN interface configuration parsing
for _, ifaceFile := range ifaceFiles {
    var ifaceCfg nwutils.Ifcfg
    err = ifaceCfg.Parse(path.SysNetIfCfgDir + "/" + ifaceFile.Name())
    if err != nil {
        continue
    }
    err = HandleVlanAdd(&ifaceCfg)
}
```

---

## 6. Bridge Interfaces

### Overview

Bridge interfaces provide Layer 2 connectivity between multiple network interfaces, enabling traffic forwarding between wired and wireless networks.

```
┌─────────────────────────────────────────────────────────────────────┐
│                    BRIDGE ARCHITECTURE                               │
│                                                                     │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │                        br0 (Bridge)                          │   │
│  └────────────────────────────┬────────────────────────────────┘   │
│                               │                                     │
│         ┌─────────────────────┼─────────────────────┐               │
│         │                     │                     │               │
│    ┌────┴────┐           ┌────┴────┐           ┌────┴────┐         │
│    │eth0.100 │           │  ath0   │           │  ath1   │         │
│    │ (VLAN)  │           │ (VAP 1) │           │ (VAP 2) │         │
│    └─────────┘           └─────────┘           └─────────┘         │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

### Bridge Types

| Bridge | Purpose | Member Interfaces |
|--------|---------|-------------------|
| br0 | Primary bridge | VLAN interfaces, VAPs |
| br-lanN | Per-network bridges | Network-specific VLANs, VAPs |
| tunbrN | Tunnel bridges | Tunnel interfaces, VAPs |

### Bridge Creation

```bash
# Create a new bridge (from nwutils.go)
AddNewBridge() {
    brctl addbr $BRIDGE_NAME
    brctl stp $BRIDGE_NAME off
    ifconfig $BRIDGE_NAME up
}

# From bridge_mgmt.sh - check_and_add_bridge_iface()
check_and_add_bridge_iface() {
    local bridge_name=$1
    local vlan_id=$2

    # Select parent interface based on mode
    if [ -e "$AP_TMPDIR/mesh_enabled" ]; then
        ETH_INTERFACE="vle0"
    else
        if [ -e "$AP_TMPDIR/link_aggr_enabled" ]; then
            ETH_INTERFACE="bond0"
        else
            ETH_INTERFACE="eth0"
        fi
    fi

    # Create bridge if it doesn't exist
    if ! brctl show | grep -q "^$bridge_name"; then
        brctl addbr $bridge_name
        brctl stp $bridge_name off
    fi

    # Create VLAN interface and add to bridge
    vconfig add $ETH_INTERFACE $vlan_id
    brctl addif $bridge_name $ETH_INTERFACE.$vlan_id
    ifconfig $ETH_INTERFACE.$vlan_id up
    ifconfig $bridge_name up
}
```

### Adding Interfaces to Bridge

```bash
# Add VLAN interface to bridge
brctl addif br0 eth0.100

# Add wireless VAP to bridge
brctl addif br0 ath0

# Show bridge members
brctl show br0

# Remove interface from bridge
brctl delif br0 eth0.100
```

### Bridge Configuration Options

```bash
# Disable Spanning Tree Protocol (typical for AP bridges)
brctl stp br0 off

# Set bridge forwarding delay
brctl setfd br0 0

# Set bridge aging time
brctl setageing br0 300

# Set bridge priority
brctl setbridgeprio br0 32768
```

### Bridge with Tunnel Interfaces

```bash
# Tunnel bridge creation (from handle_eogre_tunnel.sh)
create_tunnel_bridge() {
    BRIDGE_NAME="tunbr${NETWORK_PROFILE_ID}"

    if ! brctl show | grep -q "^$BRIDGE_NAME"; then
        brctl addbr $BRIDGE_NAME
        brctl stp $BRIDGE_NAME off
    fi

    # Add GRE tunnel interface
    brctl addif $BRIDGE_NAME $GRETAP_IFACE

    # Add VLAN interface for the tunnel
    brctl addif $BRIDGE_NAME $GRETAP_IFACE.$VLAN_ID
}
```

---

## 7. Wireless Interfaces

### Overview

Wireless interfaces provide WiFi connectivity and are organized into radio interfaces and Virtual Access Points (VAPs).

```
┌─────────────────────────────────────────────────────────────────────┐
│                    WIRELESS INTERFACE HIERARCHY                      │
│                                                                     │
│  Physical Radios                                                    │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │   wifi0 (2.4GHz)    │    wifi1 (5GHz)    │   wifi2 (6GHz)   │   │
│  └────────┬────────────┴─────────┬──────────┴────────┬─────────┘   │
│           │                      │                   │              │
│  Virtual Access Points (VAPs)    │                   │              │
│  ┌────────┴────────┐    ┌────────┴────────┐   ┌──────┴──────┐      │
│  │ ath0  │  ath1   │    │ ath2  │  ath3   │   │ ath4 │ ath5 │      │
│  │(SSID1)│ (SSID2) │    │(SSID1)│ (SSID2) │   │(SSID1)│(SSID2)│     │
│  └───────┴─────────┘    └───────┴─────────┘   └──────┴──────┘      │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

### Radio Interfaces

| Interface | Band | Typical Use |
|-----------|------|-------------|
| wifi0 | 2.4 GHz | Legacy clients, IoT devices |
| wifi1 | 5 GHz | High-performance clients |
| wifi2 | 6 GHz | WiFi 6E clients |
| wifi3 | 6 GHz (optional) | Additional 6 GHz capacity |

### Virtual Access Points (VAPs)

```bash
# Create VAP interface (from createVAP script)
create_vap_interface() {
    ATH_NAME=$1
    RADIO_WIFI=$2
    MODE=$3

    # Using iw command
    iw dev $RADIO_WIFI interface add $ATH_NAME type $MODE

    # Alternative using wlanconfig (older method)
    # wlanconfig $ATH_NAME create wlandev $RADIO_WIFI wlanmode $MODE
}

# Example VAP creation
iw dev wifi0 interface add ath0 type __ap
iw dev wifi1 interface add ath2 type __ap
```

### VAP Configuration

```bash
# From createVAP script
configure_vap() {
    ATH_NAME=$1

    # Set SSID
    iwconfig $ATH_NAME essid "$SSID_NAME"

    # Set channel
    iwconfig $ATH_NAME channel $CHANNEL

    # Configure encryption
    # (handled by hostapd/wpa_supplicant)

    # Bring up interface
    ifconfig $ATH_NAME up
}
```

### VAP VLAN Configuration

```bash
# Add VLAN to VAP (from configure_vap_vlan)
if [ "$VVLANID" != "0" ]; then
    UNI_ID_LOG PROFILE $PROFILE_ID "INFO: vconfig add $VAPNAME $VVLANID"
    vconfig add $VAPNAME $VVLANID

    if toggleMTUConfigEnabled; then
        set_mtu_on_iface $VAPNAME
        set_mtu_on_iface $VAPNAME.$VVLANID
    fi
fi
```

### Interface Abstraction Layer (IAL)

```c
// From ial_core.c - Interface management
typedef struct ial_iface {
    char name[IFNAMSIZ];
    int index;
    int type;
    int radio_index;
    struct ial_iface *next;
} ial_iface_t;

// Get interfaces matching criteria
int ial_get_ifaces(ial_iface_params_t *params, ial_iface_t **ifaces) {
    // Query interfaces based on type, radio, etc.
    // Returns list of matching interfaces
}

// Interface types
#define IAL_IFACE_TYPE_RADIO    1
#define IAL_IFACE_TYPE_VAP      2
#define IAL_IFACE_TYPE_MONITOR  3
```

### Monitor Interfaces

```bash
# Create monitor interface for packet capture
iw dev wifi0 interface add mon0 type monitor
ifconfig mon0 up

# Monitor interface naming
# mon0, mon1 - General monitoring
# monit0 - Specific monitoring tasks
```

### Maximum VAPs per Radio

```c
// From cfg_ol.h - VAP limits
#define CFG_TGT_VDEVS_MIN 1
#define CFG_TGT_VDEVS_MAX 16
#define CFG_TGT_VDEVS_DEFAULT CFG_TGT_VDEVS_MAX

// Mesh VAP limits
#define CFG_TGT_NUM_VDEV_MESH_MIN 1
#define CFG_TGT_NUM_VDEV_MESH_MAX 8
#define CFG_TGT_NUM_VDEV_MESH_DEFAULT CFG_TGT_NUM_VDEV_MESH_MAX
```

---

## 8. Tunnel Interfaces

### Overview

Tunnel interfaces encapsulate traffic for overlay networks, enabling connectivity across Layer 3 networks.

```
┌─────────────────────────────────────────────────────────────────────┐
│                    TUNNEL INTERFACE TYPES                            │
│                                                                     │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐      │
│  │   GRE/GRETap    │  │     VXLAN       │  │     IPsec       │      │
│  │   (gt0, gt1)    │  │   (vt0, vt1)    │  │   (ipsec0)      │      │
│  └────────┬────────┘  └────────┬────────┘  └────────┬────────┘      │
│           │                    │                    │               │
│           └────────────────────┼────────────────────┘               │
│                                │                                     │
│                    ┌───────────┴───────────┐                        │
│                    │   Tunnel Bridge       │                        │
│                    │   (tunbrN)            │                        │
│                    └───────────────────────┘                        │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

### GRE/GRETap Interfaces

```bash
# Create GRETap interface (from handle_eogre_tunnel.sh)
create_gretap_interface() {
    local GRETAP_IFACE=$1
    local LOCAL_IP=$2
    local REMOTE_IP=$3
    local KEY=$4

    # Delete existing interface
    ip link del $GRETAP_IFACE 2>/dev/null

    # Create new GRETap interface
    ip link add $GRETAP_IFACE type gretap \
        local $LOCAL_IP \
        remote $REMOTE_IP \
        key $KEY \
        ttl 64

    # Assign fake MAC address
    tunnel_fake_mac=$(tunnel_fakemac 0 $NETWORK_PROFILE_ID)
    ifconfig $GRETAP_IFACE hw ether $tunnel_fake_mac

    # Configure MTU
    ifconfig $GRETAP_IFACE mtu $MTU up
}
```

### GRETap VLAN Configuration

```bash
# Create VLAN on GRETap interface
create_vconfig_gretap() {
    IFACE=$1.$2
    VVLANID=$2

    vconfig add $1 $2 2>/dev/null
    if [ "$?" != "0" ]; then
        return
    fi

    # Assign fake MAC
    tunnel_fake_mac=$(tunnel_fakemac $VVLANID $NETWORK_PROFILE_ID)
    /sbin/ifconfig $IFACE hw ether $tunnel_fake_mac

    # Configure QoS egress/ingress mappings
    for i in 0 1 2 3 4 5 6 7; do
        vconfig set_egress_map $IFACE $i $i
        vconfig set_ingress_map $IFACE $i $i
    done
}
```

### VXLAN Interfaces

```bash
# Create VXLAN interface (from handle_vxlan_tunnel.sh)
create_vxlan_interface() {
    local VXLAN_IFACE=$1
    local VNI=$2
    local LOCAL_IP=$3
    local REMOTE_IP=$4
    local DST_PORT=$5

    # Calculate VNI from VLAN
    VNI=$(vlan_to_vni $VLAN $VXLAN_VNI_OFFSET)

    # Set DF bit for network type 3
    if [ "$NETWORK_TYPE" = "3" -a "$VXLAN_DONT_FRAGMENT" = "1" ]; then
        df_bit="set"
    else
        df_bit="unset"
    fi

    # Create VXLAN interface
    ip link add $VXLAN_IFACE type vxlan \
        id $VNI \
        local $LOCAL_IP \
        df $df_bit \
        remote $REMOTE_IP \
        dstport $DST_PORT \
        nolearning

    # Configure interface
    ifconfig $VXLAN_IFACE mtu $DEFAULT_MTU
    tunnel_fake_mac=$(tunnel_fakemac 0 $NETWORK_PROFILE_ID)
    ifconfig $VXLAN_IFACE hw ether $tunnel_fake_mac
}
```

### VXLAN L2 Proxy Configuration

```bash
# Configure L2 proxy for VXLAN (from handle_vxlan_tunnel.sh)
configure_vxlan_l2Proxy() {
    local l2_proxy=$1

    if [ "$l2_proxy" == "1" ]; then
        ap_raw_mac=$(/sbin/mfg_cli get_ether_mac | tr '[a-z]' '[A-Z]')
        ap_formatted_mac=$(echo "$ap_raw_mac" | sed 's/../&:/g; s/:$//')
        echo "$ap_formatted_mac" >/sys/kernel/l2proxy/l2proxy_ap_mac
    fi

    echo $l2_proxy >$AP_SYSDIR/devices/virtual/net/$VXLAN_IFACE/l2_proxy
}
```

### VXLAN MTU Configuration

```bash
# Configure VXLAN MTU (from handle_vxlan_tunnel.sh)
configure_vxlan_mtu() {
    local PMTU=$1
    local MTU=$2
    local tun_hdr=$3
    local tunnel_type=$4
    local force_fragment=$5

    if [ $PMTU -lt $(expr $DEFAULT_MTU + $tun_hdr) ]; then
        /sbin/ifconfig $VXLAN_IFACE mtu $MTU
        configure_mss $MTU "$tunnel_type"

        if [ "$force_fragment" = "1" ]; then
            echo 1 >/sys/devices/virtual/net/$VXLAN_IFACE/force_fragment
        fi
    else
        /sbin/ifconfig $VXLAN_IFACE mtu $DEFAULT_MTU
    fi
}
```

### IPsec Tunnel Interfaces

```bash
# IPsec tunnel configuration (from handle_ipsec_tunnel.sh)
# IPsec tunnels use xfrm framework rather than explicit tunnel interfaces
# Traffic is matched by security policies and encrypted/decrypted transparently

# Configure IPsec tunnel endpoint
configure_ipsec_tunnel() {
    local LOCAL_IP=$1
    local REMOTE_IP=$2
    local PSK=$3

    # IPsec configuration is typically handled by strongSwan/libreswan
    # Configuration files in /etc/ipsec.conf and /etc/ipsec.secrets
}
```

### Tunnel sysfs Paths

| Path | Purpose |
|------|---------|
| `/sys/devices/virtual/net/&lt;iface&gt;/l2_proxy` | L2 proxy mode |
| `/sys/devices/virtual/net/&lt;iface&gt;/pmtu` | Path MTU |
| `/sys/devices/virtual/net/&lt;iface&gt;/force_fragment` | Force fragmentation |

---

## 9. Mesh Interfaces

### Overview

Mesh interfaces enable wireless mesh networking, allowing APs to communicate with each other wirelessly to extend network coverage.

```
┌─────────────────────────────────────────────────────────────────────┐
│                    MESH INTERFACE ARCHITECTURE                       │
│                                                                     │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │                     Root AP (eth0 connected)                 │   │
│  │  ┌─────────┐                                                 │   │
│  │  │  eth0   │ <── Wired uplink                                │   │
│  │  └────┬────┘                                                 │   │
│  │       │                                                      │   │
│  │  ┌────┴────┐     ┌─────────┐                                 │   │
│  │  │  vle0   │<───>│  bre0   │ (Virtual Ethernet Pair)         │   │
│  │  └────┬────┘     └────┬────┘                                 │   │
│  │       │               │                                      │   │
│  │  ┌────┴────┐     ┌────┴────┐                                 │   │
│  │  │   br0   │     │ Mesh    │                                 │   │
│  │  │(bridge) │     │ Radio   │                                 │   │
│  │  └─────────┘     └────┬────┘                                 │   │
│  │                       │                                      │   │
│  │                  Wireless                                    │   │
│  │                    Mesh                                      │   │
│  │                    Link                                      │   │
│  └───────────────────────┼─────────────────────────────────────┘   │
│                          │                                          │
│  ┌───────────────────────┴─────────────────────────────────────┐   │
│  │                     Non-Root AP (mesh only)                  │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

### Mesh Virtual Ethernet Pair

```bash
# Create mesh veth pair (from rc.bridge)
if [ "$mesh_enabled" = "1" ]; then
    # Load veth kernel module
    insmod $MODULE_PATH/veth.ko

    if ! ip link show vle0 >/dev/null 2>&1; then
        # Create veth pair (vle0 <-> bre0)
        if ! ip link add vle0 type veth peer name bre0; then
            UNI_LOG PARSER "ERROR: Failed to create veth pair for mesh configuration"
            return 1
        fi
        UNI_LOG PARSER "INFO: Created veth pair (vle0/bre0) for mesh configuration"
    fi

    # vle0 becomes the ETH_INTERFACE for bridging
    ETH0="vle0"
fi
```

### Mesh MAC Address Configuration

```bash
# Configure mesh interface MAC addresses (from rc.bridge)
if [ "$mesh_enabled" = "1" ]; then
    basemac_t=$(echo "$iface_mac" | sed 's/[0-9a-fA-F]$//')
    chng_val=$(echo "$iface_mac" | cut -d ':' -f 6 | cut -c 2 | xargs)

    if [ "$ETH_MAC_OFFSET" != "" ]; then
        eth_mac_minus_2=${basemac_t}$(d2h4 $((0x$chng_val - $ETH_MAC_OFFSET)))
        eth_mac_minus_3=${basemac_t}$(d2h4 $((0x$chng_val - $ETH_MAC_OFFSET - 1)))
    else
        eth_mac_minus_2=${basemac_t}$(d2h4 $((0x$chng_val - 2)))
        eth_mac_minus_3=${basemac_t}$(d2h4 $((0x$chng_val - 3)))
    fi

    # Reconfigure eth0 with offset MAC
    ifconfig eth0 down
    ifconfig eth0 hw ether "$eth_mac_minus_2"
    bring_up_iface "eth0"

    # Configure veth pair MAC addresses
    ip link set dev $ETH0 address "$iface_mac"
    ip link set dev bre0 address "$eth_mac_minus_3"
    bring_up_iface "bre0"
fi
```

### Mesh Configuration Structure

```c
// From atn_structs.h - Mesh configuration
typedef struct mesh_conf_info_s {
    int16_t min_rssi;          // Minimum RSSI for mesh link
    uint16_t max_hop_count;    // Maximum hop count
    uint16_t max_downlinks;    // Maximum downlink nodes
    uint16_t mesh_id;          // Mesh network ID
    bool root_enabled;         // Is this a root AP
    uint8_t mesh_ap_mac[IEEE80211_ADDR_LEN];  // Mesh AP MAC
} mesh_conf_info_t;

typedef struct mesh_data_s {
    mesh_conf_info_t mesh_conf;
    mesh_path_info_t curr_mesh_path;
} mesh_data_t;
```

### Mesh Path Configuration

```go
// Mesh configuration map (from ssid_mesh.go)
var meshConfigMap = map[string]string{
    "Id":           "MESH_ID",
    "Enabled":      "MESH_ENABLED",
    "V2Enabled":    "MESH_v2_ENABLED",
    "MaxHopCount":  "MESH_MAX_HOP_COUNT",
    "MaxDownlinks": "MESH_MAX_DOWNLINKS",
    "MinRssi":      "MESH_MIN_RSSI",
}
```

### Mesh Protocol Parameters

```c
// From mesh.c (wpa_supplicant) - Mesh protocol defaults
conf->mesh_pp_id = MESH_PATH_PROTOCOL_HWMP;     // Path protocol: HWMP
conf->mesh_pm_id = MESH_PATH_METRIC_AIRTIME;    // Metric: Airtime
conf->mesh_cc_id = 0;                           // Congestion control
conf->mesh_sp_id = MESH_SYNC_METHOD_NEIGHBOR_OFFSET;  // Time sync
conf->mesh_auth_id = (conf->security & MESH_CONF_SEC_AUTH) ? 1 : 0;
```

### Mesh Role Detection

```bash
# Check mesh role (from rc.bridge)
MESH_CAPAB=$(senv_get MESH_SUPPORT)

if [ "$wifi_6ghz_capable" = "1" ]; then
    MESH_CONFIGURED=$(grep "MESH_v2_ENABLED=1" "$APCONF_PATH")
else
    MESH_CONFIGURED=$(grep "MESH_ENABLED=1" "$APCONF_PATH")
fi

if [ ! -z "$MESH_CONFIGURED" -a "$MESH_CAPAB" = "1" -a "$CIEP_ENABLED" != "1" ]; then
    mesh_enabled=1
    touch "$AP_TMPDIR/mesh_enabled"

    # Check if non-root mesh node
    if grep -q "MESH_ROLE=2" "$APCONF_PATH"; then
        touch "$AP_TMPDIR/mesh_nonroot"
    fi
fi
```

---

## 10. Loopback and Special Interfaces

### Loopback Interface (lo)

The loopback interface is a virtual interface used for local communication within the AP.

```bash
# Loopback interface properties
Interface: lo
IP Address: 127.0.0.1
Netmask: 255.0.0.0
Purpose: Local process communication, localhost services

# Configure loopback
ifconfig lo 127.0.0.1 netmask 255.0.0.0 up
```

### Monitor Interfaces

Monitor interfaces are used for packet capture and wireless monitoring.

```bash
# Create monitor interface
iw dev wifi0 interface add mon0 type monitor

# Configure monitor flags
iw dev mon0 set monitor fcsfail otherbss

# Bring up monitor interface
ifconfig mon0 up

# Monitor interface types
# mon0, mon1    - General radio monitoring
# monit0        - Specific monitoring tasks
# radiotap      - Radiotap header capture
```

### Special Interface Files

| File/Path | Purpose |
|-----------|---------|
| `/sys/class/net/&lt;iface&gt;/address` | Interface MAC address |
| `/sys/class/net/&lt;iface&gt;/mtu` | Interface MTU |
| `/sys/class/net/&lt;iface&gt;/operstate` | Operational state |
| `/sys/class/net/&lt;iface&gt;/carrier` | Link carrier state |
| `/sys/class/net/&lt;iface&gt;/flags` | Interface flags |
| `/sys/class/net/&lt;iface&gt;/statistics/` | Interface statistics |

### Interface State Machine

```
┌─────────────────────────────────────────────────────────────────────┐
│                    INTERFACE STATE TRANSITIONS                       │
│                                                                     │
│   ┌──────────┐     ┌──────────┐     ┌──────────┐     ┌──────────┐  │
│   │  DOWN    │────>│DORMANT   │────>│  LOWER   │────>│   UP     │  │
│   │          │     │          │     │  LAYER   │     │          │  │
│   │          │     │          │     │   UP     │     │          │  │
│   └──────────┘     └──────────┘     └──────────┘     └──────────┘  │
│        ^                                                    │       │
│        │                                                    │       │
│        └────────────────────────────────────────────────────┘       │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 11. Interface Hierarchy and Relationships

### Complete Interface Hierarchy

```
┌─────────────────────────────────────────────────────────────────────┐
│                    COMPLETE INTERFACE HIERARCHY                      │
│                                                                     │
│  Layer 1 (Physical)                                                 │
│  ├── eth0                     (Primary Ethernet)                    │
│  ├── eth1                     (Secondary Ethernet)                  │
│  ├── wifi0                    (Radio 2.4GHz)                        │
│  ├── wifi1                    (Radio 5GHz)                          │
│  └── wifi2                    (Radio 6GHz)                          │
│                                                                     │
│  Layer 2 (Link Aggregation)                                         │
│  └── bond0                    (Bonded eth0+eth1)                    │
│      ├── eth0 (slave)                                               │
│      └── eth1 (slave)                                               │
│                                                                     │
│  Layer 3 (Virtual Ethernet - Mesh)                                  │
│  └── vle0 <──> bre0           (Virtual Ethernet Pair)               │
│                                                                     │
│  Layer 4 (VLAN)                                                     │
│  ├── eth0.100                 (Management VLAN)                     │
│  ├── eth0.200                 (Data VLAN)                           │
│  ├── bond0.100                (VLAN on Bond)                        │
│  └── vle0.100                 (VLAN on Mesh)                        │
│                                                                     │
│  Layer 5 (Wireless VAPs)                                            │
│  ├── ath0                     (VAP on wifi0)                        │
│  ├── ath1                     (VAP on wifi0)                        │
│  ├── ath2                     (VAP on wifi1)                        │
│  └── ath3                     (VAP on wifi1)                        │
│                                                                     │
│  Layer 6 (Tunnels)                                                  │
│  ├── gt0                      (GRETap Tunnel)                       │
│  ├── vt0                      (VXLAN Tunnel)                        │
│  └── ipsec0                   (IPsec Tunnel)                        │
│                                                                     │
│  Layer 7 (Bridges)                                                  │
│  ├── br0                      (Main Bridge)                         │
│  │   ├── eth0.100 (member)                                          │
│  │   ├── ath0 (member)                                              │
│  │   └── ath2 (member)                                              │
│  └── tunbr1                   (Tunnel Bridge)                       │
│      ├── gt0 (member)                                               │
│      └── ath1 (member)                                              │
│                                                                     │
│  Special                                                            │
│  ├── lo                       (Loopback)                            │
│  └── mon0                     (Monitor)                             │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

### Interface Selection Logic

```bash
# Determine primary uplink interface (from bridge_mgmt.sh)
get_uplink_interface() {
    if [ -e "$AP_TMPDIR/mesh_enabled" ]; then
        # Mesh mode: use virtual ethernet
        ETH_INTERFACE="vle0"
    else
        if [ -e "$AP_TMPDIR/link_aggr_enabled" ]; then
            # LAG mode: use bonded interface
            ETH_INTERFACE="bond0"
        else
            # Standard mode: use primary ethernet
            ETH_INTERFACE="eth0"
        fi
    fi
    echo "$ETH_INTERFACE"
}
```

---

## 12. Interface Configuration

### Interface Configuration Files

```bash
# Configuration file locations
/tmp/net_conf/ifcfg-*           # Interface configuration files
/opt/ap/sensor/ethernet.conf    # Ethernet settings
/opt/ap/config/ap.conf          # AP configuration

# ifcfg file format
# ifcfg-eth0.100
DEVICE=eth0.100
BOOTPROTO=static
IPADDR=192.168.1.1
NETMASK=255.255.255.0
GATEWAY=192.168.1.254
ONBOOT=yes
```

### Interface Configuration Structure

```go
// From ifcfg.go - Interface configuration
type Ifcfg struct {
    Device     string    // Interface name
    BootProto  string    // dhcp, static, none
    IPv4       string    // IPv4 address
    IPv6       string    // IPv6 address
    Netmask    string    // Network mask
    Gateway    string    // Default gateway
    Gateway6   string    // IPv6 gateway
    OnBoot     bool      // Enable at boot
}

// Parse configuration file
func (cfg *Ifcfg) Parse(filepath string) error {
    // Read and parse ifcfg file
}
```

### IP Address Configuration

```bash
# Static IP configuration
ifconfig eth0 192.168.1.1 netmask 255.255.255.0 up
route add default gw 192.168.1.254

# DHCP configuration
udhcpc -i eth0 -s /opt/ap/scripts/udhcpc.script

# IPv6 configuration
ifconfig eth0 add 2001:db8::1/64
```

### MTU Configuration

```bash
# Set interface MTU
ifconfig eth0 mtu 1500

# MTU considerations for tunnels
# GRE overhead: ~24 bytes
# VXLAN overhead: ~50 bytes
# IPsec overhead: variable (typically 50-100 bytes)

# Example: VXLAN with 1500 byte payload
# Outer MTU = 1500 + 50 = 1550 (or fragment inner packet)
```

---

## 13. Interface Lifecycle Management

### Interface Lifecycle States

```
┌─────────────────────────────────────────────────────────────────────┐
│                    INTERFACE LIFECYCLE                               │
│                                                                     │
│  ┌──────────┐                                                       │
│  │  CREATE  │  ip link add / brctl addbr / iw interface add        │
│  └────┬─────┘                                                       │
│       │                                                             │
│       v                                                             │
│  ┌──────────┐                                                       │
│  │CONFIGURE │  ifconfig, ip addr, vconfig, brctl addif              │
│  └────┬─────┘                                                       │
│       │                                                             │
│       v                                                             │
│  ┌──────────┐                                                       │
│  │   UP     │  ifconfig <iface> up / ip link set up                 │
│  └────┬─────┘                                                       │
│       │                                                             │
│       v                                                             │
│  ┌──────────┐                                                       │
│  │ RUNNING  │  Normal operation                                     │
│  └────┬─────┘                                                       │
│       │                                                             │
│       v                                                             │
│  ┌──────────┐                                                       │
│  │  DOWN    │  ifconfig <iface> down                                │
│  └────┬─────┘                                                       │
│       │                                                             │
│       v                                                             │
│  ┌──────────┐                                                       │
│  │ DESTROY  │  ip link del / brctl delbr / iw interface del        │
│  └──────────┘                                                       │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

### Interface Creation Examples

```bash
# Physical interface (already exists)
ifconfig eth0 up

# VLAN interface
ip link add link eth0 name eth0.100 type vlan id 100
ifconfig eth0.100 up

# Bond interface
echo "+eth0" >/sys/class/net/bond0/bonding/slaves
echo "+eth1" >/sys/class/net/bond0/bonding/slaves
ifconfig bond0 up

# Bridge interface
brctl addbr br0
brctl addif br0 eth0.100
brctl addif br0 ath0
ifconfig br0 up

# VAP interface
iw dev wifi0 interface add ath0 type __ap
ifconfig ath0 up

# Tunnel interface
ip link add gt0 type gretap local 10.0.0.1 remote 10.0.0.2
ifconfig gt0 up
```

### Interface Destruction Examples

```bash
# Remove from bridge first
brctl delif br0 ath0
brctl delif br0 eth0.100

# Destroy bridge
ifconfig br0 down
brctl delbr br0

# Destroy VLAN
ifconfig eth0.100 down
ip link del eth0.100

# Destroy VAP
ifconfig ath0 down
iw dev ath0 del

# Destroy tunnel
ifconfig gt0 down
ip link del gt0
```

---

## 14. Interface Statistics and Monitoring

### Statistics Locations

```bash
# Kernel statistics
/proc/net/dev                           # All interface statistics
/sys/class/net/<iface>/statistics/      # Per-interface statistics

# Available statistics
rx_packets      # Received packets
tx_packets      # Transmitted packets
rx_bytes        # Received bytes
tx_bytes        # Transmitted bytes
rx_errors       # Receive errors
tx_errors       # Transmit errors
rx_dropped      # Received dropped
tx_dropped      # Transmitted dropped
multicast       # Multicast packets received
collisions      # Collisions
```

### Reading Interface Statistics

```c
// From networking.c - Get interface statistics
bool get_interface_stats(const char* interface_name, interface_stats* stats) {
    FILE* fh = fopen(PROCNET_DEV_PATH, "r");
    if (!fh) {
        LOG(LOG_ERR, "cannot open %s. Error %s", PROCNET_DEV_PATH, strerror(errno));
        return false;
    }

    // Parse /proc/net/dev for interface line
    // Format: iface: rx_bytes rx_packets rx_errs ... tx_bytes tx_packets tx_errs ...

    while (fgets(line, sizeof(line), fh)) {
        if (strstr(line, interface_name)) {
            sscanf(line, "%*s %llu %llu %llu %*u %*u %*u %*u %*u %llu %llu %llu",
                   &stats->rx_bytes, &stats->rx_packets, &stats->rx_errors,
                   &stats->tx_bytes, &stats->tx_packets, &stats->tx_errors);
            break;
        }
    }

    fclose(fh);
    return true;
}
```

### Link State Monitoring

```bash
# Check link state
cat /sys/class/net/eth0/carrier      # 1 = link up, 0 = link down
cat /sys/class/net/eth0/operstate    # up, down, unknown, etc.

# ethtool link status
ethtool eth0 | grep "Link detected"

# Monitor link changes
ip monitor link
```

### Wireless Statistics

```bash
# Wireless interface statistics
iwconfig ath0
iw dev ath0 station dump
iw dev ath0 survey dump

# Radio statistics
cat /sys/kernel/debug/ieee80211/phy0/statistics/
```

---

## 15. Codebase Implementation

### Key Source Files

| File | Purpose |
|------|---------|
| `ap/rootfs/init.d/functions` | Shell functions for interface management |
| `ap/rootfs/scripts/bridge_mgmt.sh` | Bridge management functions |
| `ap/rootfs/scripts/createVAP` | VAP creation script |
| `ap/rootfs/scripts/rc.bridge` | Bridge initialization |
| `ap/rootfs/scripts/handle_eogre_tunnel.sh` | GRE tunnel management |
| `ap/rootfs/scripts/handle_vxlan_tunnel.sh` | VXLAN tunnel management |
| `ap/rootfs/scripts/configure_vap_vlan` | VAP VLAN configuration |
| `ap/src/go/arista-ap/nwutils/nwutils.go` | Go network utilities |
| `ap/src/go/arista-ap/nwutils/ifcfg.go` | Interface configuration parsing |
| `ap/src/go/arista-ap/vlan/vlan.go` | VLAN type definitions |
| `ap/src/go/arista-ap/vlan/vlan_manager.go` | VLAN lifecycle management |
| `ap/src/sensord/src/ial/ial_core.c` | Interface Abstraction Layer |

### Interface Helper Functions

```bash
# From functions - bring_up_iface()
bring_up_iface() {
    local iface=$1
    local max_retries=10
    local retry=0

    while [ $retry -lt $max_retries ]; do
        ifconfig $iface up 2>/dev/null
        if [ $? -eq 0 ]; then
            return 0
        fi
        retry=$((retry + 1))
        sleep 1
    done

    return 1
}

# Get interface MAC address
ap_mac_get() {
    local iface=$1
    cat /sys/class/net/$iface/address
}
```

### Go Interface Utilities

```go
// From nwutils.go - Interface operations
package nwutils

// AddNewBridge creates a new bridge interface
func AddNewBridge(bridgeName string) error {
    cmd := exec.Command("brctl", "addbr", bridgeName)
    if err := cmd.Run(); err != nil {
        return err
    }

    cmd = exec.Command("brctl", "stp", bridgeName, "off")
    cmd.Run()

    cmd = exec.Command("ifconfig", bridgeName, "up")
    return cmd.Run()
}

// AddInterfaceToBridge adds an interface to a bridge
func AddInterfaceToBridge(bridgeName, ifaceName string) error {
    cmd := exec.Command("brctl", "addif", bridgeName, ifaceName)
    return cmd.Run()
}

// GetInterfaceMAC returns the MAC address of an interface
func GetInterfaceMAC(ifaceName string) (string, error) {
    iface, err := net.InterfaceByName(ifaceName)
    if err != nil {
        return "", err
    }
    return iface.HardwareAddr.String(), nil
}
```

### Interface Abstraction Layer (C)

```c
// From ial_core.c - Interface query functions

// Get list of interfaces matching criteria
int ial_get_ifaces(ial_iface_params_t *params, ial_iface_t **ifaces) {
    DIR *dir;
    struct dirent *entry;
    ial_iface_t *head = NULL, *tail = NULL;
    int count = 0;

    dir = opendir("/sys/class/net");
    if (!dir) return -1;

    while ((entry = readdir(dir)) != NULL) {
        if (entry->d_name[0] == '.') continue;

        // Check if interface matches criteria
        if (ial_match_iface(entry->d_name, params)) {
            ial_iface_t *iface = malloc(sizeof(ial_iface_t));
            strncpy(iface->name, entry->d_name, IFNAMSIZ);
            iface->next = NULL;

            if (!head) head = iface;
            if (tail) tail->next = iface;
            tail = iface;
            count++;
        }
    }

    closedir(dir);
    *ifaces = head;
    return count;
}
```

---

## 16. CLI Commands

### Interface Information Commands

```bash
# List all interfaces
ip link show
ifconfig -a

# Show specific interface
ip link show eth0
ifconfig eth0

# Show interface statistics
ip -s link show eth0
cat /proc/net/dev

# Show bridge information
brctl show
brctl showmacs br0

# Show VLAN information
cat /proc/net/vlan/config

# Show bonding information
cat /proc/net/bonding/bond0
cat /sys/class/net/bond0/bonding/slaves
cat /sys/class/net/bond0/bonding/mode

# Show wireless information
iwconfig
iw dev
iw phy
```

### Interface Configuration Commands

```bash
# Configure IP address
ifconfig eth0 192.168.1.1 netmask 255.255.255.0
ip addr add 192.168.1.1/24 dev eth0

# Bring interface up/down
ifconfig eth0 up
ifconfig eth0 down
ip link set eth0 up
ip link set eth0 down

# Set MAC address
ifconfig eth0 hw ether 00:11:22:33:44:55
ip link set eth0 address 00:11:22:33:44:55

# Set MTU
ifconfig eth0 mtu 9000
ip link set eth0 mtu 9000
```

### VLAN Commands

```bash
# Create VLAN
vconfig add eth0 100
ip link add link eth0 name eth0.100 type vlan id 100

# Delete VLAN
vconfig rem eth0.100
ip link del eth0.100

# Show VLAN configuration
cat /proc/net/vlan/eth0.100
ip -d link show eth0.100
```

### Bridge Commands

```bash
# Create bridge
brctl addbr br0

# Delete bridge
brctl delbr br0

# Add interface to bridge
brctl addif br0 eth0.100

# Remove interface from bridge
brctl delif br0 eth0.100

# Show bridge MAC table
brctl showmacs br0

# Configure STP
brctl stp br0 on
brctl stp br0 off
```

### Wireless Commands

```bash
# Create VAP
iw dev wifi0 interface add ath0 type __ap

# Delete VAP
iw dev ath0 del

# Show station list
iw dev ath0 station dump

# Show survey
iw dev ath0 survey dump

# Configure channel
iw dev ath0 set channel 36
```

### Tunnel Commands

```bash
# Create GRE tunnel
ip link add gt0 type gretap local 10.0.0.1 remote 10.0.0.2

# Create VXLAN tunnel
ip link add vt0 type vxlan id 100 local 10.0.0.1 remote 10.0.0.2 dstport 4789

# Delete tunnel
ip link del gt0
ip link del vt0

# Show tunnel info
ip -d link show gt0
ip -d link show vt0
```

---

## 17. Troubleshooting

### Common Interface Issues

#### Issue: Interface Not Coming Up

```bash
# Check interface exists
ip link show eth0

# Check for errors in dmesg
dmesg | grep eth0

# Check driver status
ethtool -i eth0

# Try bringing up manually
ifconfig eth0 up
ip link set eth0 up

# Check for conflicting processes
lsof -i | grep eth0
```

#### Issue: No Link Detected

```bash
# Check link status
ethtool eth0 | grep "Link detected"
cat /sys/class/net/eth0/carrier

# Check cable connection
ethtool eth0 | grep "Speed"

# Try forcing speed/duplex
ethtool -s eth0 speed 1000 duplex full autoneg off
```

#### Issue: VLAN Not Working

```bash
# Check 8021q module
lsmod | grep 8021q
modprobe 8021q

# Verify VLAN interface exists
cat /proc/net/vlan/config

# Check parent interface is up
ifconfig eth0

# Verify VLAN ID on switch
# (Check switch configuration)
```

#### Issue: Bridge Not Forwarding

```bash
# Check bridge state
brctl show br0
brctl showstp br0

# Verify member interfaces
brctl show | grep br0

# Check interface states
for iface in $(brctl show br0 | tail -n +2 | awk '{print $NF}'); do
    echo "$iface: $(cat /sys/class/net/$iface/operstate)"
done

# Check forwarding enabled
cat /proc/sys/net/ipv4/ip_forward
```

#### Issue: Bonding Not Working

```bash
# Check bonding module
lsmod | grep bonding

# Verify slaves
cat /sys/class/net/bond0/bonding/slaves

# Check mode
cat /sys/class/net/bond0/bonding/mode

# Check slave states
cat /proc/net/bonding/bond0

# Verify link on slave interfaces
ethtool eth0 | grep "Link detected"
ethtool eth1 | grep "Link detected"
```

#### Issue: VAP Not Creating

```bash
# Check radio interface
iw phy

# Verify radio is up
ifconfig wifi0

# Check max VAP limit
iw dev | grep -c Interface

# Check for errors
dmesg | tail -20
```

### Diagnostic Commands

```bash
# Interface diagnostics
ethtool eth0           # Link status, speed, duplex
ethtool -S eth0        # Statistics
ethtool -i eth0        # Driver info
ethtool -k eth0        # Offload features

# Bridge diagnostics
brctl showmacs br0     # MAC address table
brctl showstp br0      # STP status

# Wireless diagnostics
iw dev ath0 info       # VAP information
iw dev ath0 station dump  # Connected clients
iwconfig ath0          # Wireless parameters

# Tunnel diagnostics
ip tunnel show         # GRE tunnels
bridge fdb show        # VXLAN FDB entries
```

---

## 18. Best Practices

### Interface Naming

1. **Use consistent naming conventions**
   - eth0, eth1 for physical Ethernet
   - bond0 for bonded interfaces
   - eth0.VID for VLAN interfaces
   - br0, br-lanN for bridges
   - athN for wireless VAPs
   - gtN for GRE tunnels
   - vtN for VXLAN tunnels

2. **Document interface purposes**
   - Keep configuration files updated
   - Use comments in scripts

### Interface Configuration

1. **Always check interface state before operations**
   ```bash
   if ip link show $IFACE >/dev/null 2>&1; then
       # Interface exists
   fi
   ```

2. **Use proper error handling**
   ```bash
   if ! brctl addbr br0 2>/dev/null; then
       log_error "Failed to create bridge"
       return 1
   fi
   ```

3. **Clean up properly on shutdown**
   ```bash
   # Remove from bridge first
   brctl delif br0 ath0 2>/dev/null
   # Then delete interface
   iw dev ath0 del 2>/dev/null
   ```

### VLAN Configuration

1. **Use MVRP for dynamic VLAN propagation**
2. **Configure QoS mappings for proper priority handling**
3. **Use fake MACs for non-management VLANs**
4. **Validate VLAN IDs (1-4094)**

### Bridge Configuration

1. **Disable STP for simple topologies**
2. **Set forwarding delay to 0 for faster convergence**
3. **Use per-VLAN bridges for isolation**
4. **Monitor bridge MAC table for issues**

### Bonding Configuration

1. **Match physical link speeds**
2. **Use appropriate mode for network topology**
   - Mode 1 (active-backup) for redundancy
   - Mode 4 (LACP) for load balancing with switch support
3. **Configure appropriate up/down delays to prevent flapping**
4. **Set primary interface for active-backup**

### Wireless Configuration

1. **Limit VAPs per radio to avoid performance issues**
2. **Use appropriate channel widths**
3. **Configure band steering when applicable**
4. **Monitor client distribution across radios**

### Tunnel Configuration

1. **Consider MTU overhead when configuring tunnels**
2. **Use DF bit appropriately for fragmentation control**
3. **Configure L2 proxy when needed**
4. **Monitor tunnel statistics for issues**

### Monitoring

1. **Regularly check interface statistics**
2. **Monitor link states for failures**
3. **Track error counters**
4. **Use logging for state changes**

---

## Appendix A: Interface Quick Reference

| Interface | Type | Parent | Purpose |
|-----------|------|--------|---------|
| lo | Loopback | - | Local communication |
| eth0 | Physical | - | Primary uplink |
| eth1 | Physical | - | Secondary uplink |
| bond0 | Bond | eth0, eth1 | Link aggregation |
| eth0.VID | VLAN | eth0/bond0 | Traffic segmentation |
| br0 | Bridge | - | L2 forwarding |
| wifi0-3 | Radio | - | Wireless PHY |
| ath0-N | VAP | wifiN | Wireless AP |
| gt0-1 | GRETap | - | GRE tunnel |
| vt0-1 | VXLAN | - | VXLAN tunnel |
| vle0 | Veth | - | Mesh egress |
| bre0 | Veth | - | Mesh bridge |
| mon0 | Monitor | wifiN | Packet capture |

---

## Appendix B: Common sysfs Paths

```
/sys/class/net/<iface>/
├── address              # MAC address
├── mtu                  # Maximum transmission unit
├── operstate            # Operational state (up/down)
├── carrier              # Link carrier state
├── speed                # Link speed (Mbps)
├── duplex               # Duplex mode
├── flags                # Interface flags
├── type                 # Interface type
├── ifindex              # Interface index
└── statistics/
    ├── rx_packets
    ├── tx_packets
    ├── rx_bytes
    ├── tx_bytes
    ├── rx_errors
    ├── tx_errors
    ├── rx_dropped
    └── tx_dropped

/sys/class/net/bond0/bonding/
├── mode                 # Bonding mode
├── slaves               # Slave interfaces
├── primary              # Primary interface
├── active_slave         # Active slave
├── miimon               # MII monitoring interval
├── updelay              # Up delay
└── downdelay            # Down delay
```

---

## Appendix C: Interface Limits

| Resource | Limit | Notes |
|----------|-------|-------|
| Physical Ethernet | 2 | eth0, eth1 |
| Bond interfaces | 1 | bond0 |
| VLANs per interface | 128 | MAX_VLANS constant |
| Radios | 2-4 | Platform dependent |
| VAPs per radio | 8-16 | Platform dependent |
| Bridges | No hard limit | Memory constrained |
| Tunnels | Platform dependent | Per type |

---

*Document Version: 1.0*
*Last Updated: 2026-02-03*

