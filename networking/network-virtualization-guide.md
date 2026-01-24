# Network Virtualization Technologies: VLAN, VXLAN, and VAP
## A Comprehensive Technical Guide

---

## Table of Contents

1. [Introduction to Network Virtualization](#introduction-to-network-virtualization)
2. [VLAN (Virtual Local Area Network)](#vlan-virtual-local-area-network)
   - [VLAN Fundamentals](#vlan-fundamentals)
   - [VLAN Architecture and Components](#vlan-architecture-and-components)
   - [VLAN Tagging and Frame Format](#vlan-tagging-and-frame-format)
   - [VLAN Trunking Protocols](#vlan-trunking-protocols)
   - [VLAN Configuration Examples](#vlan-configuration-examples)
   - [Inter-VLAN Routing](#inter-vlan-routing)
   - [VLAN Best Practices](#vlan-best-practices)
   - [VLAN Security Considerations](#vlan-security-considerations)
   - [VLAN Troubleshooting](#vlan-troubleshooting)
3. [VXLAN (Virtual Extensible LAN)](#vxlan-virtual-extensible-lan)
   - [VXLAN Fundamentals](#vxlan-fundamentals)
   - [VXLAN Architecture](#vxlan-architecture)
   - [VXLAN Packet Format](#vxlan-packet-format)
   - [VXLAN Control Plane Options](#vxlan-control-plane-options)
   - [VXLAN with EVPN](#vxlan-with-evpn)
   - [VXLAN Configuration Examples](#vxlan-configuration-examples)
   - [VXLAN in Data Center Fabrics](#vxlan-in-data-center-fabrics)
   - [VXLAN Best Practices](#vxlan-best-practices)
   - [VXLAN Security](#vxlan-security)
   - [VXLAN Troubleshooting](#vxlan-troubleshooting)
4. [VAP (Virtual Access Point)](#vap-virtual-access-point)
   - [VAP Fundamentals](#vap-fundamentals)
   - [VAP Architecture](#vap-architecture)
   - [VAP Implementation](#vap-implementation)
   - [VAP Configuration](#vap-configuration)
   - [VAP Security](#vap-security)
   - [VAP Best Practices](#vap-best-practices)
5. [Comparison and Use Cases](#comparison-and-use-cases)
6. [Integration Strategies](#integration-strategies)
7. [Performance Considerations](#performance-considerations)
8. [Future Trends](#future-trends)
9. [Glossary](#glossary)
10. [References](#references)

---

## Introduction to Network Virtualization

### What is Network Virtualization?

Network virtualization is a method of combining hardware and software network resources and network functionality into a single, software-based administrative entity. This abstraction layer decouples the network services from the underlying hardware, enabling greater flexibility, scalability, and efficiency in network management.

### The Evolution of Network Virtualization

Network virtualization has evolved significantly over the past few decades:

**1980s-1990s: Early Virtualization Concepts**
- Introduction of VLANs (IEEE 802.1Q standard ratified in 1998)
- Basic network segmentation capabilities
- Hardware-dependent implementations

**2000s: Expansion and Maturation**
- Widespread VLAN adoption in enterprise networks
- Development of more sophisticated trunking protocols
- Introduction of virtual switching concepts

**2010s: Cloud and Data Center Revolution**
- VXLAN introduction (RFC 7348, 2014)
- Software-defined networking (SDN) emergence
- Overlay network technologies proliferation

**2020s: Modern Network Virtualization**
- Advanced EVPN-VXLAN fabrics
- Multi-cloud networking
- Intent-based networking
- AI/ML-driven network automation

### Key Benefits of Network Virtualization

1. **Improved Resource Utilization**
   - Better use of physical network infrastructure
   - Reduced hardware requirements
   - Dynamic resource allocation

2. **Enhanced Flexibility**
   - Rapid network provisioning
   - Easy network reconfiguration
   - Support for diverse workloads

3. **Better Security**
   - Network segmentation and isolation
   - Micro-segmentation capabilities
   - Enhanced access control

4. **Cost Reduction**
   - Lower capital expenditure (CapEx)
   - Reduced operational expenditure (OpEx)
   - Simplified network management

5. **Scalability**
   - Support for large-scale deployments
   - Horizontal scaling capabilities
   - Multi-tenancy support

### Core Technologies Overview

This document covers three fundamental network virtualization technologies:

| Technology | Layer | Primary Use Case | Scale |
|------------|-------|------------------|-------|
| VLAN | Layer 2 | LAN Segmentation | 4,094 VLANs |
| VXLAN | Layer 2 over Layer 3 | Data Center/Cloud | 16 million VNIs |
| VAP | Layer 2 (Wireless) | Wireless Segmentation | Vendor-dependent |

---

## VLAN (Virtual Local Area Network)

### VLAN Fundamentals

#### Definition and Core Concepts

A Virtual Local Area Network (VLAN) is a logical grouping of network devices that appear to be on the same LAN regardless of their physical location. VLANs enable network administrators to partition a single physical network into multiple isolated broadcast domains, improving network efficiency, security, and management.

#### How VLANs Work

VLANs operate at Layer 2 (Data Link Layer) of the OSI model. They work by adding a tag to Ethernet frames that identifies which VLAN the frame belongs to. This tagging mechanism allows switches to:

1. **Segregate Traffic**: Keep traffic from different VLANs separate
2. **Control Broadcasts**: Limit broadcast domains to specific VLANs
3. **Enforce Policies**: Apply different policies to different VLANs
4. **Enable Mobility**: Allow devices to maintain VLAN membership regardless of physical location

#### Types of VLANs

**1. Data VLAN (User VLAN)**
- Carries user-generated traffic
- Typically assigned to end-user devices
- Also known as user VLANs

**2. Default VLAN**
- VLAN 1 on most switches
- All ports belong to this VLAN by default
- Cannot be deleted or renamed on most platforms

**3. Native VLAN**
- Carries untagged traffic on trunk links
- Default is VLAN 1 (should be changed for security)
- Only one native VLAN per trunk link

**4. Management VLAN**
- Used for switch management traffic
- SSH, Telnet, SNMP, and web management
- Should be isolated from user traffic

**5. Voice VLAN**
- Dedicated VLAN for VoIP traffic
- Enables QoS prioritization
- Separates voice from data traffic

**6. Private VLAN (PVLAN)**
- Provides Layer 2 isolation within a VLAN
- Contains primary and secondary VLANs
- Types: Isolated, Community, Promiscuous

#### VLAN ID Ranges

| Range | VLAN IDs | Description |
|-------|----------|-------------|
| Normal Range | 1-1005 | Available on all switches, stored in vlan.dat |
| Extended Range | 1006-4094 | Available on switches in VTP transparent mode |
| Reserved | 0, 4095 | Reserved for system use |
| Default | 1 | Default VLAN, cannot be deleted |
| Reserved (Cisco) | 1002-1005 | Reserved for FDDI and Token Ring |

### VLAN Architecture and Components

#### Physical Components

**1. VLAN-Capable Switches**
- Layer 2 switches with VLAN support
- Layer 3 switches for inter-VLAN routing
- Support for IEEE 802.1Q tagging

**2. Network Interface Cards (NICs)**
- VLAN-aware NICs for tagged traffic
- Virtual NICs in virtualized environments
- Support for 802.1Q VLAN tagging

**3. Routers**
- Router-on-a-stick configurations
- Subinterface support for VLANs
- Layer 3 inter-VLAN routing

#### Logical Components

**1. VLAN Database**
```
VLAN ID: 1-4094
VLAN Name: Up to 32 characters
VLAN State: Active/Suspended
VLAN Type: Ethernet/FDDI/Token Ring
```

**2. Port Membership**
- Static VLAN assignment
- Dynamic VLAN assignment (802.1X, VMPS)
- Voice VLAN assignment

**3. VLAN Trunks**
- Carry multiple VLANs between switches
- Use 802.1Q tagging
- Native VLAN for untagged traffic

### VLAN Tagging and Frame Format

#### IEEE 802.1Q Standard

The IEEE 802.1Q standard defines VLAN tagging for Ethernet frames. It inserts a 4-byte tag into the Ethernet frame header.

#### 802.1Q Frame Format

```
+------------------+------------------+------+------------------+
| Destination MAC  |   Source MAC     | 802.1Q Tag         | Type/Length |
|   (6 bytes)      |   (6 bytes)      | (4 bytes)          | (2 bytes)   |
+------------------+------------------+------+------------------+

802.1Q Tag Structure (4 bytes):
+----------------+-----+----------------+
| TPID (16 bits) | TCI (16 bits)       |
+----------------+-----+----------------+
| 0x8100         | PCP | DEI | VID     |
|                |(3b) |(1b) | (12b)   |
+----------------+-----+----------------+

Where:
- TPID: Tag Protocol Identifier (0x8100 for 802.1Q)
- TCI: Tag Control Information
- PCP: Priority Code Point (0-7, for QoS)
- DEI: Drop Eligible Indicator
- VID: VLAN Identifier (0-4095)
```

#### Frame Size Considerations

| Frame Type | Standard Size | With 802.1Q Tag |
|------------|---------------|-----------------|
| Ethernet II | 1518 bytes | 1522 bytes |
| Jumbo Frame | 9000 bytes | 9004 bytes |
| Baby Giant | 1600 bytes | 1604 bytes |

#### Double Tagging (Q-in-Q / 802.1ad)

Q-in-Q allows service providers to add an additional VLAN tag:

```
+------------------+------------------+-------------+-------------+-------------+
| Destination MAC  |   Source MAC     | S-Tag       | C-Tag       | Type/Length |
|   (6 bytes)      |   (6 bytes)      | (4 bytes)   | (4 bytes)   | (2 bytes)   |
+------------------+------------------+-------------+-------------+-------------+

S-Tag: Service Provider VLAN tag (TPID: 0x88A8)
C-Tag: Customer VLAN tag (TPID: 0x8100)
```

### VLAN Trunking Protocols

#### VTP (VLAN Trunking Protocol) - Cisco Proprietary

VTP is a Cisco proprietary protocol that manages VLAN additions, deletions, and name changes across a network.

**VTP Modes:**

| Mode | Create/Modify VLANs | Forward VTP | Sync VLANs | Save to NVRAM |
|------|---------------------|-------------|------------|---------------|
| Server | Yes | Yes | Yes | Yes |
| Client | No | Yes | Yes | No |
| Transparent | Yes (local only) | Yes | No | Yes |
| Off | Yes (local only) | No | No | Yes |

**VTP Versions:**

| Feature | VTPv1 | VTPv2 | VTPv3 |
|---------|-------|-------|-------|
| Token Ring Support | No | Yes | Yes |
| Unrecognized TLVs | Drop | Forward | Forward |
| Extended VLANs | No | No | Yes |
| Private VLANs | No | No | Yes |
| Password Encryption | MD5 | MD5 | Hidden |
| Primary Server | No | No | Yes |

#### GVRP (GARP VLAN Registration Protocol)

GVRP is an IEEE standard protocol for VLAN registration:

- Defined in IEEE 802.1Q
- Automatically propagates VLAN information
- Uses GARP (Generic Attribute Registration Protocol)
- Vendor-neutral alternative to VTP

#### MVRP (Multiple VLAN Registration Protocol)

MVRP is the successor to GVRP:

- Defined in IEEE 802.1Q-2011
- Uses MRP (Multiple Registration Protocol)
- Better scalability than GVRP
- Faster convergence

### VLAN Configuration Examples

#### Cisco IOS Configuration

**Creating VLANs:**
```cisco
! Enter global configuration mode
Switch# configure terminal

! Create VLAN 10 for Engineering
Switch(config)# vlan 10
Switch(config-vlan)# name Engineering
Switch(config-vlan)# exit

! Create VLAN 20 for Sales
Switch(config)# vlan 20
Switch(config-vlan)# name Sales
Switch(config-vlan)# exit

! Create VLAN 30 for Management
Switch(config)# vlan 30
Switch(config-vlan)# name Management
Switch(config-vlan)# exit

! Create VLAN 100 for Voice
Switch(config)# vlan 100
Switch(config-vlan)# name Voice
Switch(config-vlan)# exit
```

**Assigning Ports to VLANs:**
```cisco
! Configure access port for VLAN 10
Switch(config)# interface GigabitEthernet0/1
Switch(config-if)# switchport mode access
Switch(config-if)# switchport access vlan 10
Switch(config-if)# spanning-tree portfast
Switch(config-if)# exit

! Configure access port with voice VLAN
Switch(config)# interface GigabitEthernet0/2
Switch(config-if)# switchport mode access
Switch(config-if)# switchport access vlan 20
Switch(config-if)# switchport voice vlan 100
Switch(config-if)# spanning-tree portfast
Switch(config-if)# exit
```

**Configuring Trunk Ports:**
```cisco
! Configure trunk port
Switch(config)# interface GigabitEthernet0/24
Switch(config-if)# switchport mode trunk
Switch(config-if)# switchport trunk encapsulation dot1q
Switch(config-if)# switchport trunk native vlan 999
Switch(config-if)# switchport trunk allowed vlan 10,20,30,100
Switch(config-if)# exit
```

**VTP Configuration:**
```cisco
! Configure VTP domain
Switch(config)# vtp domain MyCompany
Switch(config)# vtp version 3
Switch(config)# vtp mode server
Switch(config)# vtp password SecurePass123 hidden

! Verify VTP status
Switch# show vtp status
```

#### Juniper JunOS Configuration

**Creating VLANs:**
```junos
# Configure VLANs
set vlans Engineering vlan-id 10
set vlans Engineering description "Engineering Department"

set vlans Sales vlan-id 20
set vlans Sales description "Sales Department"

set vlans Management vlan-id 30
set vlans Management description "Network Management"

set vlans Voice vlan-id 100
set vlans Voice description "VoIP Traffic"
```

**Assigning Ports to VLANs:**
```junos
# Configure access port
set interfaces ge-0/0/1 unit 0 family ethernet-switching interface-mode access
set interfaces ge-0/0/1 unit 0 family ethernet-switching vlan members Engineering

# Configure trunk port
set interfaces ge-0/0/24 unit 0 family ethernet-switching interface-mode trunk
set interfaces ge-0/0/24 unit 0 family ethernet-switching vlan members [Engineering Sales Management Voice]
set interfaces ge-0/0/24 native-vlan-id 999
```

#### Linux VLAN Configuration

**Using ip command:**
```bash
# Load 8021q kernel module
sudo modprobe 8021q

# Create VLAN interface
sudo ip link add link eth0 name eth0.10 type vlan id 10

# Bring up the VLAN interface
sudo ip link set eth0.10 up

# Assign IP address
sudo ip addr add 192.168.10.1/24 dev eth0.10

# Verify VLAN configuration
cat /proc/net/vlan/eth0.10
```

**Using netplan (Ubuntu 18.04+):**
```yaml
# /etc/netplan/01-network.yaml
network:
  version: 2
  renderer: networkd
  ethernets:
    eth0:
      dhcp4: no
  vlans:
    vlan10:
      id: 10
      link: eth0
      addresses:
        - 192.168.10.1/24
    vlan20:
      id: 20
      link: eth0
      addresses:
        - 192.168.20.1/24
```

**Using NetworkManager:**
```bash
# Create VLAN connection
nmcli connection add type vlan con-name vlan10 dev eth0 id 10

# Configure IP address
nmcli connection modify vlan10 ipv4.addresses 192.168.10.1/24
nmcli connection modify vlan10 ipv4.method manual

# Activate the connection
nmcli connection up vlan10
```

### Inter-VLAN Routing

#### Router-on-a-Stick Configuration

**Concept:**
Router-on-a-stick uses a single physical router interface with multiple subinterfaces to route between VLANs.

```
                    ┌─────────────────┐
                    │     Router      │
                    │                 │
                    │ Gi0/0.10 (VLAN10)
                    │ Gi0/0.20 (VLAN20)
                    │ Gi0/0.30 (VLAN30)
                    └────────┬────────┘
                             │ Trunk
                    ┌────────┴────────┐
                    │     Switch      │
                    │                 │
                    ├─────┬─────┬─────┤
                    │     │     │     │
                  VLAN10 VLAN20 VLAN30
```

**Router Configuration:**
```cisco
! Configure physical interface
Router(config)# interface GigabitEthernet0/0
Router(config-if)# no shutdown
Router(config-if)# exit

! Configure subinterface for VLAN 10
Router(config)# interface GigabitEthernet0/0.10
Router(config-subif)# encapsulation dot1Q 10
Router(config-subif)# ip address 192.168.10.1 255.255.255.0
Router(config-subif)# exit

! Configure subinterface for VLAN 20
Router(config)# interface GigabitEthernet0/0.20
Router(config-subif)# encapsulation dot1Q 20
Router(config-subif)# ip address 192.168.20.1 255.255.255.0
Router(config-subif)# exit

! Configure subinterface for VLAN 30
Router(config)# interface GigabitEthernet0/0.30
Router(config-subif)# encapsulation dot1Q 30
Router(config-subif)# ip address 192.168.30.1 255.255.255.0
Router(config-subif)# exit
```

#### Layer 3 Switch Inter-VLAN Routing

**Using SVIs (Switched Virtual Interfaces):**
```cisco
! Enable IP routing
Switch(config)# ip routing

! Create SVI for VLAN 10
Switch(config)# interface Vlan10
Switch(config-if)# ip address 192.168.10.1 255.255.255.0
Switch(config-if)# no shutdown
Switch(config-if)# exit

! Create SVI for VLAN 20
Switch(config)# interface Vlan20
Switch(config-if)# ip address 192.168.20.1 255.255.255.0
Switch(config-if)# no shutdown
Switch(config-if)# exit

! Create SVI for VLAN 30
Switch(config)# interface Vlan30
Switch(config-if)# ip address 192.168.30.1 255.255.255.0
Switch(config-if)# no shutdown
Switch(config-if)# exit

! Configure DHCP relay if needed
Switch(config)# interface Vlan10
Switch(config-if)# ip helper-address 192.168.100.10
```

#### Routed Ports on Layer 3 Switches

```cisco
! Convert switch port to routed port
Switch(config)# interface GigabitEthernet1/0/1
Switch(config-if)# no switchport
Switch(config-if)# ip address 10.0.0.1 255.255.255.252
Switch(config-if)# exit
```

### VLAN Best Practices

#### Design Best Practices

**1. VLAN Naming Conventions**
```
Format: <Location>_<Function>_<VLAN_ID>
Examples:
- NYC_Engineering_010
- LAX_Sales_020
- CHI_Management_030
```

**2. VLAN ID Allocation Strategy**

| Range | Purpose | Example |
|-------|---------|---------|
| 1-99 | Reserved/System | Native VLAN (99) |
| 100-199 | User VLANs | Engineering (100), Sales (110) |
| 200-299 | Server VLANs | Web Servers (200), DB (210) |
| 300-399 | Management | Switch Mgmt (300), AP Mgmt (310) |
| 400-499 | Voice | VoIP (400) |
| 500-599 | Guest/DMZ | Guest WiFi (500), DMZ (510) |
| 900-999 | Infrastructure | Native (999), Black Hole (998) |

**3. Trunk Configuration Standards**
- Always use explicit trunk allowed lists
- Change native VLAN from default (VLAN 1)
- Use a dedicated native VLAN (e.g., 999)
- Prune unused VLANs from trunks

**4. VLAN Distribution**
```
                    ┌─────────────────┐
                    │   Core Switch   │
                    │   (All VLANs)   │
                    └────────┬────────┘
                             │
              ┌──────────────┼──────────────┐
              │              │              │
     ┌────────┴─────┐ ┌──────┴──────┐ ┌─────┴────────┐
     │ Distribution │ │ Distribution│ │ Distribution │
     │   Switch 1   │ │   Switch 2  │ │   Switch 3   │
     │ (VLANs 10-19)│ │(VLANs 20-29)│ │(VLANs 30-39) │
     └──────────────┘ └─────────────┘ └──────────────┘
```

#### Operational Best Practices

**1. Documentation Requirements**
- VLAN database with ID, name, purpose, and subnet
- Port-to-VLAN mapping documentation
- Trunk link documentation
- Network diagrams showing VLAN topology

**2. Change Management**
- Test VLAN changes in lab environment
- Schedule changes during maintenance windows
- Have rollback procedures ready
- Verify connectivity after changes

**3. Monitoring and Alerting**
- Monitor VLAN interface status
- Track VLAN utilization
- Alert on unauthorized VLAN creation
- Monitor STP topology changes

### VLAN Security Considerations

#### Common VLAN Attacks

**1. VLAN Hopping Attack**

*Switch Spoofing:*
```
Attacker configures their NIC to act as a trunk port,
potentially gaining access to all VLANs.

Mitigation:
- Disable DTP on access ports
- Explicitly configure ports as access mode
- Set unused ports to a black hole VLAN
```

```cisco
! Mitigation configuration
Switch(config)# interface range GigabitEthernet0/1-24
Switch(config-if-range)# switchport mode access
Switch(config-if-range)# switchport nonegotiate
Switch(config-if-range)# switchport access vlan 998  ! Black hole VLAN
Switch(config-if-range)# shutdown  ! Disable unused ports
```

*Double Tagging Attack:*
```
Attacker sends double-tagged frames to hop VLANs.
Only works if:
1. Attacker is on native VLAN
2. Target VLAN traffic passes through another switch

Mitigation:
- Change native VLAN to unused VLAN
- Tag native VLAN traffic on trunks
- Use VLAN access lists
```

```cisco
! Mitigation - tag native VLAN on trunk
Switch(config)# vlan dot1q tag native

! Or change native VLAN
Switch(config)# interface GigabitEthernet0/24
Switch(config-if)# switchport trunk native vlan 999
```

**2. MAC Address Table Overflow (CAM Table Attack)**
```cisco
! Mitigation - Port Security
Switch(config)# interface GigabitEthernet0/1
Switch(config-if)# switchport port-security
Switch(config-if)# switchport port-security maximum 3
Switch(config-if)# switchport port-security violation shutdown
Switch(config-if)# switchport port-security mac-address sticky
```

**3. DHCP Spoofing Attack**
```cisco
! Mitigation - DHCP Snooping
Switch(config)# ip dhcp snooping
Switch(config)# ip dhcp snooping vlan 10,20,30

! Trust uplink to legitimate DHCP server
Switch(config)# interface GigabitEthernet0/24
Switch(config-if)# ip dhcp snooping trust

! Limit DHCP rate on access ports
Switch(config)# interface GigabitEthernet0/1
Switch(config-if)# ip dhcp snooping limit rate 15
```

#### VLAN Access Control Lists (VACLs)

```cisco
! Create access list
Switch(config)# ip access-list extended BLOCK_TELNET
Switch(config-ext-nacl)# deny tcp any any eq telnet
Switch(config-ext-nacl)# permit ip any any

! Create VLAN access map
Switch(config)# vlan access-map BLOCK_TELNET_MAP 10
Switch(config-access-map)# match ip address BLOCK_TELNET
Switch(config-access-map)# action drop
Switch(config)# vlan access-map BLOCK_TELNET_MAP 20
Switch(config-access-map)# action forward

! Apply to VLAN
Switch(config)# vlan filter BLOCK_TELNET_MAP vlan-list 10
```

#### Private VLANs (PVLANs)

Private VLANs provide Layer 2 isolation within a VLAN:

```
                    ┌─────────────────────────────────┐
                    │       Primary VLAN 100          │
                    │                                 │
                    │  ┌──────────┐  ┌──────────┐    │
                    │  │Isolated  │  │Community │    │
                    │  │VLAN 101  │  │VLAN 102  │    │
                    │  │          │  │          │    │
                    │  │ No comm. │  │ Can talk │    │
                    │  │ between  │  │ within   │    │
                    │  │ ports    │  │ community│    │
                    │  └──────────┘  └──────────┘    │
                    │                                 │
                    │     Promiscuous Port            │
                    │     (Gateway/Router)            │
                    │     Can reach all ports         │
                    └─────────────────────────────────┘
```

```cisco
! Configure Private VLANs
Switch(config)# vtp mode transparent  ! Required for PVLANs

! Create primary VLAN
Switch(config)# vlan 100
Switch(config-vlan)# private-vlan primary
Switch(config-vlan)# private-vlan association 101,102

! Create isolated secondary VLAN
Switch(config)# vlan 101
Switch(config-vlan)# private-vlan isolated

! Create community secondary VLAN
Switch(config)# vlan 102
Switch(config-vlan)# private-vlan community

! Configure promiscuous port (to router)
Switch(config)# interface GigabitEthernet0/1
Switch(config-if)# switchport mode private-vlan promiscuous
Switch(config-if)# switchport private-vlan mapping 100 101,102

! Configure isolated host port
Switch(config)# interface GigabitEthernet0/2
Switch(config-if)# switchport mode private-vlan host
Switch(config-if)# switchport private-vlan host-association 100 101

! Configure community host port
Switch(config)# interface GigabitEthernet0/3
Switch(config-if)# switchport mode private-vlan host
Switch(config-if)# switchport private-vlan host-association 100 102
```

### VLAN Troubleshooting

#### Common VLAN Issues

**1. VLAN Mismatch**
- Access port assigned to wrong VLAN
- Native VLAN mismatch on trunk
- Trunk allowing wrong VLANs

**2. Trunk Issues**
- DTP negotiation failure
- Encapsulation mismatch
- Speed/duplex mismatch

**3. STP Issues**
- VLAN not active due to STP
- Root bridge placement issues
- Spanning tree loops

#### Troubleshooting Commands (Cisco)

```cisco
! Show VLAN information
Switch# show vlan brief
Switch# show vlan id 10
Switch# show vlan summary

! Show interface VLAN status
Switch# show interfaces trunk
Switch# show interfaces GigabitEthernet0/1 switchport
Switch# show interfaces status

! Show MAC address table
Switch# show mac address-table
Switch# show mac address-table vlan 10
Switch# show mac address-table interface GigabitEthernet0/1

! Show VTP status
Switch# show vtp status
Switch# show vtp password

! Show spanning tree per VLAN
Switch# show spanning-tree vlan 10
Switch# show spanning-tree summary

! Debug commands
Switch# debug sw-vlan vtp events
Switch# debug sw-vlan packets
```

#### Troubleshooting Flowchart

```
Device can't communicate?
           │
           ▼
    ┌──────────────┐
    │Check physical│
    │ connectivity │
    └──────┬───────┘
           │ OK
           ▼
    ┌──────────────┐     No
    │Port in same  │─────────► Move to correct VLAN
    │   VLAN?      │
    └──────┬───────┘
           │ Yes
           ▼
    ┌──────────────┐     No
    │ Port status  │─────────► Check port security,
    │    up/up?    │           STP, admin shutdown
    └──────┬───────┘
           │ Yes
           ▼
    ┌──────────────┐     No
    │MAC learned on│─────────► Check cable, NIC,
    │   switch?    │           speed/duplex
    └──────┬───────┘
           │ Yes
           ▼
    ┌──────────────┐     No
    │Trunk passing │─────────► Check allowed VLANs
    │  this VLAN?  │           on trunk
    └──────┬───────┘
           │ Yes
           ▼
    ┌──────────────┐
    │ Check Layer 3│
    │   routing    │
    └──────────────┘
```

#### VLAN Troubleshooting Script (Python)

```python
#!/usr/bin/env python3
"""
VLAN Troubleshooting Script
Connects to switches and verifies VLAN configuration
"""

from netmiko import ConnectHandler
import re

def check_vlan_config(device_info, vlan_id):
    """Check VLAN configuration on a switch."""

    results = {
        'vlan_exists': False,
        'ports_in_vlan': [],
        'trunk_ports': [],
        'stp_status': None
    }

    try:
        connection = ConnectHandler(**device_info)

        # Check if VLAN exists
        output = connection.send_command(f'show vlan id {vlan_id}')
        if 'not found' not in output.lower():
            results['vlan_exists'] = True

            # Parse ports in VLAN
            lines = output.split('\n')
            for line in lines:
                if 'Gi' in line or 'Fa' in line:
                    ports = re.findall(r'[GF][ai]\d+/\d+(?:/\d+)?', line)
                    results['ports_in_vlan'].extend(ports)

        # Check trunk ports
        trunk_output = connection.send_command('show interfaces trunk')
        trunk_lines = trunk_output.split('\n')
        for line in trunk_lines:
            if str(vlan_id) in line:
                port = re.match(r'^(\S+)', line)
                if port:
                    results['trunk_ports'].append(port.group(1))

        # Check STP status
        stp_output = connection.send_command(f'show spanning-tree vlan {vlan_id}')
        if 'does not exist' in stp_output.lower():
            results['stp_status'] = 'VLAN not in STP'
        elif 'forwarding' in stp_output.lower():
            results['stp_status'] = 'Active'
        else:
            results['stp_status'] = 'Check Required'

        connection.disconnect()

    except Exception as e:
        results['error'] = str(e)

    return results

def main():
    device = {
        'device_type': 'cisco_ios',
        'host': '192.168.1.1',
        'username': 'admin',
        'password': 'password',
    }

    vlan_to_check = 10
    results = check_vlan_config(device, vlan_to_check)

    print(f"VLAN {vlan_to_check} Configuration Check:")
    print(f"  VLAN Exists: {results['vlan_exists']}")
    print(f"  Access Ports: {', '.join(results['ports_in_vlan'])}")
    print(f"  Trunk Ports: {', '.join(results['trunk_ports'])}")
    print(f"  STP Status: {results['stp_status']}")

if __name__ == '__main__':
    main()
```

---

## VXLAN (Virtual Extensible LAN)

### VXLAN Fundamentals

#### What is VXLAN?

VXLAN (Virtual Extensible LAN) is a network virtualization technology that addresses the scalability limitations of traditional VLANs. Defined in RFC 7348, VXLAN encapsulates Layer 2 Ethernet frames within Layer 3 UDP packets, creating an overlay network that can span Layer 3 boundaries.

#### Why VXLAN?

**VLAN Limitations:**
| Limitation | VLAN | VXLAN Solution |
|------------|------|----------------|
| Scale | 4,094 VLANs max | 16 million VNIs |
| Spanning Tree | Required in L2 | L3 underlay, no STP |
| L2 Adjacency | Required | Not required |
| Multi-tenancy | Limited | Massive scale |
| Mobility | Same L2 domain | Across L3 boundaries |

**VXLAN Key Benefits:**
1. **Massive Scale**: 24-bit VNI provides 16+ million segments
2. **L3 Underlay**: Leverages existing IP routing infrastructure
3. **Workload Mobility**: VMs can move across L3 boundaries
4. **Multi-tenancy**: Supports cloud and data center multi-tenant architectures
5. **Efficient Routing**: Uses ECMP in the underlay

#### VXLAN Terminology

| Term | Definition |
|------|------------|
| VNI | VXLAN Network Identifier (24-bit) |
| VTEP | VXLAN Tunnel Endpoint |
| NVE | Network Virtual Edge |
| Underlay | Physical IP network infrastructure |
| Overlay | Virtual L2 network over the underlay |
| BUM | Broadcast, Unknown unicast, Multicast |

### VXLAN Architecture

#### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        VXLAN Overlay                            │
│                     (Virtual L2 Network)                        │
│   ┌─────────┐         ┌─────────┐         ┌─────────┐          │
│   │  VM1    │         │  VM2    │         │  VM3    │          │
│   │VNI:5000 │         │VNI:5000 │         │VNI:6000 │          │
│   └────┬────┘         └────┬────┘         └────┬────┘          │
│        │                   │                   │                │
└────────┼───────────────────┼───────────────────┼────────────────┘
         │                   │                   │
    ┌────┴────┐         ┌────┴────┐         ┌────┴────┐
    │  VTEP1  │         │  VTEP2  │         │  VTEP3  │
    │10.1.1.1 │         │10.1.1.2 │         │10.1.1.3 │
    └────┬────┘         └────┬────┘         └────┬────┘
         │                   │                   │
┌────────┴───────────────────┴───────────────────┴────────────────┐
│                        IP Underlay                              │
│              (Physical L3 Network - OSPF/BGP)                   │
└─────────────────────────────────────────────────────────────────┘
```

#### VTEP (VXLAN Tunnel Endpoint)

VTEPs are the devices that perform VXLAN encapsulation and decapsulation:

**VTEP Types:**
1. **Hardware VTEP**: Physical switches with VXLAN support
2. **Software VTEP**: Virtual switches (vSphere vDS, OVS, Linux bridge)
3. **Hybrid VTEP**: Combination of hardware and software

**VTEP Functions:**
- Encapsulate original L2 frames in VXLAN headers
- Decapsulate VXLAN packets and forward original frames
- Maintain mapping of VNI to VLAN
- Learn and maintain MAC-to-VTEP mappings
- Handle BUM traffic (flood or head-end replication)

### VXLAN Packet Format

#### VXLAN Header Structure

```
Outer Ethernet Header:
┌──────────────────┬──────────────────┬─────────────┐
│ Outer Dest MAC   │ Outer Source MAC │ Ether Type  │
│    (6 bytes)     │    (6 bytes)     │  (0x0800)   │
└──────────────────┴──────────────────┴─────────────┘

Outer IP Header:
┌─────────┬─────────┬──────────┬──────────┬──────────────┐
│ Version │   IHL   │   TOS    │  Length  │    ID        │
│  (4b)   │  (4b)   │ (8bits)  │ (16bits) │  (16bits)    │
├─────────┴─────────┼──────────┼──────────┼──────────────┤
│     Flags/Frag    │   TTL    │ Protocol │   Checksum   │
│      (16bits)     │  (8b)    │ (17=UDP) │   (16bits)   │
├───────────────────┴──────────┴──────────┴──────────────┤
│                  Source IP Address                      │
│                     (32 bits)                           │
├─────────────────────────────────────────────────────────┤
│               Destination IP Address                    │
│                     (32 bits)                           │
└─────────────────────────────────────────────────────────┘

Outer UDP Header:
┌────────────────┬────────────────┬─────────────┬─────────────┐
│  Source Port   │   Dest Port    │   Length    │  Checksum   │
│ (hash-based)   │    (4789)      │  (16bits)   │  (16bits)   │
└────────────────┴────────────────┴─────────────┴─────────────┘

VXLAN Header (8 bytes):
┌─────────────────────────────────────────────────────────────┐
│ Flags    │          Reserved                                │
│ (8bits)  │          (24 bits)                               │
├─────────────────────────────────────────────────────────────┤
│        VNI (VXLAN Network Identifier)     │    Reserved     │
│              (24 bits)                    │    (8 bits)     │
└─────────────────────────────────────────────────────────────┘

Original Inner Ethernet Frame:
┌──────────────────┬──────────────────┬─────────────┬─────────┐
│ Inner Dest MAC   │ Inner Source MAC │ Ether Type  │ Payload │
│    (6 bytes)     │    (6 bytes)     │  (2 bytes)  │         │
└──────────────────┴──────────────────┴─────────────┴─────────┘
```

#### VXLAN Flags Field

```
VXLAN Flags (8 bits):
┌───┬───┬───┬───┬───┬───┬───┬───┐
│ R │ R │ R │ R │ I │ R │ R │ R │
└───┴───┴───┴───┴───┴───┴───┴───┘
                  │
                  └─ I flag: VNI valid (must be 1)

R = Reserved (must be 0)
```

#### MTU Considerations

VXLAN adds 50 bytes of overhead:
- Outer Ethernet: 14 bytes
- Outer IP: 20 bytes
- Outer UDP: 8 bytes
- VXLAN Header: 8 bytes

| Original Frame | VXLAN Encapsulated | Required MTU |
|---------------|-------------------|--------------|
| 1500 bytes | 1550 bytes | 1550+ bytes |
| 9000 bytes | 9050 bytes | 9050+ bytes |

**MTU Configuration Recommendations:**
```
# Set underlay MTU to accommodate VXLAN overhead
# If inner MTU is 1500, underlay should be at least 1550
# Recommended: 9216 bytes for jumbo frame support

# Cisco NX-OS
switch(config)# system jumbomtu 9216
switch(config)# interface Ethernet1/1
switch(config-if)# mtu 9216

# Linux
ip link set dev eth0 mtu 9000
```

### VXLAN Control Plane Options

#### 1. Multicast-based Control Plane

Uses IP multicast for BUM traffic distribution:

```
┌─────────────────────────────────────────────────────────────┐
│                    Multicast Group                          │
│                    (239.1.1.1)                              │
│                         │                                   │
│         ┌───────────────┼───────────────┐                  │
│         │               │               │                   │
│    ┌────┴────┐    ┌────┴────┐    ┌────┴────┐              │
│    │  VTEP1  │    │  VTEP2  │    │  VTEP3  │              │
│    │  Join   │    │  Join   │    │  Join   │              │
│    │Multicast│    │Multicast│    │Multicast│              │
│    └─────────┘    └─────────┘    └─────────┘              │
└─────────────────────────────────────────────────────────────┘
```

**Pros:**
- Simple configuration
- Efficient BUM handling
- No external controller

**Cons:**
- Requires multicast in underlay
- Multicast configuration complexity
- Limited scalability

#### 2. Ingress Replication (Head-End Replication)

VTEPs replicate BUM traffic to all remote VTEPs:

```
BUM Frame from VTEP1:
                    ┌─────────┐
                    │  VTEP1  │
                    │ (Source)│
                    └────┬────┘
                         │
          ┌──────────────┼──────────────┐
          │              │              │
          ▼              ▼              ▼
     ┌─────────┐   ┌─────────┐   ┌─────────┐
     │  VTEP2  │   │  VTEP3  │   │  VTEP4  │
     │ (Copy1) │   │ (Copy2) │   │ (Copy3) │
     └─────────┘   └─────────┘   └─────────┘
```

**Configuration (Cisco NX-OS):**
```cisco
switch(config)# interface nve1
switch(config-if-nve)# member vni 5000
switch(config-if-nve-vni)# ingress-replication protocol static
switch(config-if-nve-vni)# peer-ip 10.1.1.2
switch(config-if-nve-vni)# peer-ip 10.1.1.3
switch(config-if-nve-vni)# peer-ip 10.1.1.4
```

#### 3. BGP EVPN Control Plane

Most scalable option using BGP to distribute MAC/IP information:

```
┌─────────────────────────────────────────────────────────────┐
│                    BGP Route Reflectors                     │
│                                                             │
│              ┌──────────┐     ┌──────────┐                 │
│              │   RR1    │     │   RR2    │                 │
│              └─────┬────┘     └────┬─────┘                 │
│                    │ iBGP EVPN     │                        │
│         ┌──────────┼───────────────┼──────────┐            │
│         │          │               │          │             │
│    ┌────┴────┐┌────┴────┐    ┌────┴────┐┌────┴────┐       │
│    │  VTEP1  ││  VTEP2  │    │  VTEP3  ││  VTEP4  │       │
│    │  Leaf1  ││  Leaf2  │    │  Leaf3  ││  Leaf4  │       │
│    └─────────┘└─────────┘    └─────────┘└─────────┘       │
└─────────────────────────────────────────────────────────────┘
```

**Benefits of BGP EVPN:**
- Scalable MAC/IP learning
- Efficient ARP suppression
- Multi-tenancy support
- Integrated routing and bridging
- Standards-based (RFC 7432, RFC 8365)

### VXLAN with EVPN

#### EVPN Route Types

| Type | Name | Purpose |
|------|------|---------|
| 1 | Ethernet Auto-Discovery | Multi-homing, fast convergence |
| 2 | MAC/IP Advertisement | MAC and IP learning |
| 3 | Inclusive Multicast | BUM traffic optimization |
| 4 | Ethernet Segment | Multi-homing DF election |
| 5 | IP Prefix | L3 VPN prefix advertisement |

#### EVPN Type-2 Route

```
Type-2 MAC/IP Advertisement Route:
┌────────────────────────────────────────────────────────────┐
│ Route Distinguisher (RD)          │ 8 bytes               │
├────────────────────────────────────────────────────────────┤
│ Ethernet Segment Identifier (ESI) │ 10 bytes              │
├────────────────────────────────────────────────────────────┤
│ Ethernet Tag ID                   │ 4 bytes               │
├────────────────────────────────────────────────────────────┤
│ MAC Address Length                │ 1 byte (48 = 6 bytes) │
├────────────────────────────────────────────────────────────┤
│ MAC Address                       │ 6 bytes               │
├────────────────────────────────────────────────────────────┤
│ IP Address Length                 │ 1 byte (32 or 128)    │
├────────────────────────────────────────────────────────────┤
│ IP Address                        │ 4 or 16 bytes         │
├────────────────────────────────────────────────────────────┤
│ MPLS Label (VNI)                  │ 3 bytes               │
└────────────────────────────────────────────────────────────┘
```

#### Symmetric vs Asymmetric IRB

**Asymmetric IRB (Integrated Routing and Bridging):**
```
Host A (VLAN 10) → Host B (VLAN 20)

Ingress VTEP:
1. Receives frame on VLAN 10
2. Routes to VLAN 20 (local routing)
3. Encapsulates with VNI 20
4. Sends to egress VTEP

Egress VTEP:
1. Decapsulates VNI 20
2. Bridges to Host B on VLAN 20
3. No routing required

Return path uses same asymmetric pattern
```

**Symmetric IRB:**
```
Host A (VLAN 10) → Host B (VLAN 20)

Ingress VTEP:
1. Receives frame on VLAN 10
2. Routes frame
3. Encapsulates with L3 VNI (transit VNI)
4. Sends to egress VTEP

Egress VTEP:
1. Decapsulates L3 VNI
2. Routes to VLAN 20
3. Bridges to Host B

Both ingress and egress perform routing - symmetric
```

| Feature | Asymmetric IRB | Symmetric IRB |
|---------|----------------|---------------|
| VNI requirement | All L2 VNIs on all VTEPs | Only local L2 VNIs + L3 VNI |
| Routing location | Ingress only | Ingress and egress |
| Scalability | Lower | Higher |
| Configuration | Simpler | More complex |
| Preferred for | Small deployments | Large-scale deployments |

### VXLAN Configuration Examples

#### Cisco NX-OS VXLAN EVPN Configuration

**Underlay Configuration:**
```cisco
! Enable required features
switch(config)# feature ospf
switch(config)# feature bgp
switch(config)# feature pim
switch(config)# feature nv overlay
switch(config)# feature vn-segment-vlan-based
switch(config)# nv overlay evpn

! Configure loopback for VTEP
switch(config)# interface loopback0
switch(config-if)# ip address 10.1.1.1/32
switch(config-if)# ip router ospf 1 area 0
switch(config-if)# ip pim sparse-mode

! Configure loopback for NVE source
switch(config)# interface loopback1
switch(config-if)# ip address 10.2.1.1/32
switch(config-if)# ip router ospf 1 area 0
switch(config-if)# ip pim sparse-mode

! Configure underlay interface
switch(config)# interface Ethernet1/1
switch(config-if)# no switchport
switch(config-if)# mtu 9216
switch(config-if)# ip address 10.0.0.1/30
switch(config-if)# ip router ospf 1 area 0
switch(config-if)# ip pim sparse-mode
switch(config-if)# no shutdown
```

**BGP EVPN Configuration:**
```cisco
! Configure BGP for EVPN
switch(config)# router bgp 65001
switch(config-router)# router-id 10.1.1.1
switch(config-router)# address-family l2vpn evpn
switch(config-router-af)# advertise-pip

! Configure BGP neighbor (to spine/RR)
switch(config-router)# neighbor 10.1.1.100
switch(config-router-neighbor)# remote-as 65001
switch(config-router-neighbor)# update-source loopback0
switch(config-router-neighbor)# address-family l2vpn evpn
switch(config-router-neighbor-af)# send-community extended
switch(config-router-neighbor-af)# route-reflector-client
```

**VXLAN Overlay Configuration:**
```cisco
! Create VLANs and map to VNI
switch(config)# vlan 10
switch(config-vlan)# name Web_Servers
switch(config-vlan)# vn-segment 10010

switch(config)# vlan 20
switch(config-vlan)# name App_Servers
switch(config-vlan)# vn-segment 10020

switch(config)# vlan 100
switch(config-vlan)# name L3_VNI_Tenant1
switch(config-vlan)# vn-segment 10100

! Create VRF for tenant
switch(config)# vrf context Tenant1
switch(config-vrf)# vni 10100
switch(config-vrf)# rd auto
switch(config-vrf)# address-family ipv4 unicast
switch(config-vrf-af-ipv4)# route-target import 65001:10100
switch(config-vrf-af-ipv4)# route-target import 65001:10100 evpn
switch(config-vrf-af-ipv4)# route-target export 65001:10100
switch(config-vrf-af-ipv4)# route-target export 65001:10100 evpn

! Configure SVIs
switch(config)# interface Vlan10
switch(config-if)# vrf member Tenant1
switch(config-if)# ip address 192.168.10.1/24
switch(config-if)# fabric forwarding mode anycast-gateway

switch(config)# interface Vlan20
switch(config-if)# vrf member Tenant1
switch(config-if)# ip address 192.168.20.1/24
switch(config-if)# fabric forwarding mode anycast-gateway

switch(config)# interface Vlan100
switch(config-if)# vrf member Tenant1
switch(config-if)# ip forward

! Configure anycast gateway MAC
switch(config)# fabric forwarding anycast-gateway-mac 0000.2222.3333

! Configure NVE interface
switch(config)# interface nve1
switch(config-if-nve)# no shutdown
switch(config-if-nve)# source-interface loopback1
switch(config-if-nve)# host-reachability protocol bgp
switch(config-if-nve)# member vni 10010
switch(config-if-nve-vni)# suppress-arp
switch(config-if-nve-vni)# ingress-replication protocol bgp
switch(config-if-nve)# member vni 10020
switch(config-if-nve-vni)# suppress-arp
switch(config-if-nve-vni)# ingress-replication protocol bgp
switch(config-if-nve)# member vni 10100 associate-vrf

! Configure EVPN
switch(config)# evpn
switch(config-evpn)# vni 10010 l2
switch(config-evpn-evi)# rd auto
switch(config-evpn-evi)# route-target import auto
switch(config-evpn-evi)# route-target export auto
switch(config-evpn)# vni 10020 l2
switch(config-evpn-evi)# rd auto
switch(config-evpn-evi)# route-target import auto
switch(config-evpn-evi)# route-target export auto
```

#### Arista EOS VXLAN Configuration

```eos
! Enable required services
switch(config)# service routing protocols model multi-agent

! Configure loopback for VTEP
switch(config)# interface Loopback0
switch(config-if-Lo0)# ip address 10.1.1.1/32

switch(config)# interface Loopback1
switch(config-if-Lo1)# ip address 10.2.1.1/32

! Configure VLANs
switch(config)# vlan 10
switch(config-vlan-10)# name Web_Servers

switch(config)# vlan 20
switch(config-vlan-20)# name App_Servers

! Configure VXLAN interface
switch(config)# interface Vxlan1
switch(config-if-Vx1)# vxlan source-interface Loopback1
switch(config-if-Vx1)# vxlan udp-port 4789
switch(config-if-Vx1)# vxlan vlan 10 vni 10010
switch(config-if-Vx1)# vxlan vlan 20 vni 10020
switch(config-if-Vx1)# vxlan vrf Tenant1 vni 10100

! Configure VRF
switch(config)# vrf instance Tenant1
switch(config-vrf-Tenant1)# rd 10.1.1.1:10100

! Configure SVIs
switch(config)# interface Vlan10
switch(config-if-Vl10)# vrf Tenant1
switch(config-if-Vl10)# ip address virtual 192.168.10.1/24

switch(config)# interface Vlan20
switch(config-if-Vl20)# vrf Tenant1
switch(config-if-Vl20)# ip address virtual 192.168.20.1/24

! Configure BGP
switch(config)# router bgp 65001
switch(config-router-bgp)# router-id 10.1.1.1
switch(config-router-bgp)# neighbor SPINE peer group
switch(config-router-bgp)# neighbor SPINE remote-as 65001
switch(config-router-bgp)# neighbor SPINE update-source Loopback0
switch(config-router-bgp)# neighbor SPINE send-community extended
switch(config-router-bgp)# neighbor 10.1.1.100 peer group SPINE
switch(config-router-bgp)# neighbor 10.1.1.101 peer group SPINE

switch(config-router-bgp)# address-family evpn
switch(config-router-bgp-af)# neighbor SPINE activate

switch(config-router-bgp)# vlan 10
switch(config-macvrf-10)# rd auto
switch(config-macvrf-10)# route-target both 65001:10010
switch(config-macvrf-10)# redistribute learned

switch(config-router-bgp)# vlan 20
switch(config-macvrf-20)# rd auto
switch(config-macvrf-20)# route-target both 65001:10020
switch(config-macvrf-20)# redistribute learned
```

#### Linux VXLAN Configuration

**Using iproute2:**
```bash
# Create VXLAN interface with multicast
ip link add vxlan10 type vxlan \
    id 10010 \
    group 239.1.1.10 \
    dev eth0 \
    dstport 4789

# Create VXLAN interface with unicast (static)
ip link add vxlan20 type vxlan \
    id 10020 \
    local 10.1.1.1 \
    remote 10.1.1.2 \
    dev eth0 \
    dstport 4789

# Bring up interface
ip link set vxlan10 up
ip link set vxlan20 up

# Add to bridge
ip link add br10 type bridge
ip link set br10 up
ip link set vxlan10 master br10

# Add static FDB entry for remote VTEP
bridge fdb append 00:00:00:00:00:00 dev vxlan10 dst 10.1.1.2
bridge fdb append 00:00:00:00:00:00 dev vxlan10 dst 10.1.1.3

# Verify configuration
ip -d link show vxlan10
bridge fdb show dev vxlan10
```

**Using Open vSwitch:**
```bash
# Create OVS bridge
ovs-vsctl add-br br0

# Add VXLAN port
ovs-vsctl add-port br0 vxlan1 -- set interface vxlan1 \
    type=vxlan \
    options:remote_ip=10.1.1.2 \
    options:key=10010 \
    options:dst_port=4789

# Add VXLAN port with flow-based key
ovs-vsctl add-port br0 vxlan2 -- set interface vxlan2 \
    type=vxlan \
    options:remote_ip=flow \
    options:key=flow \
    options:dst_port=4789

# Verify configuration
ovs-vsctl show
ovs-ofctl dump-ports br0
```

### VXLAN in Data Center Fabrics

#### Spine-Leaf Architecture with VXLAN

```
                    ┌─────────────────────────────────────────┐
                    │            Border/Edge                  │
                    │           ┌─────────┐                   │
                    │           │ Border  │                   │
                    │           │  Leaf   │                   │
                    │           └────┬────┘                   │
                    └────────────────┼────────────────────────┘
                                     │
    ┌────────────────────────────────┼────────────────────────────┐
    │                           Spine Layer                       │
    │     ┌─────────┐         ┌─────┴─────┐         ┌─────────┐  │
    │     │ Spine 1 │─────────│  Spine 2  │─────────│ Spine 3 │  │
    │     └────┬────┘         └─────┬─────┘         └────┬────┘  │
    │          │                    │                    │        │
    │          │    ┌───────────────┼───────────────┐    │        │
    │          │    │               │               │    │        │
    └──────────┼────┼───────────────┼───────────────┼────┼────────┘
               │    │               │               │    │
    ┌──────────┼────┼───────────────┼───────────────┼────┼────────┐
    │          │    │               │               │    │         │
    │     ┌────┴────┴───┐     ┌─────┴─────┐   ┌────┴────┴────┐   │
    │     │   Leaf 1    │     │  Leaf 2   │   │   Leaf 3     │   │
    │     │   (VTEP)    │     │  (VTEP)   │   │   (VTEP)     │   │
    │     └──────┬──────┘     └─────┬─────┘   └──────┬───────┘   │
    │            │                  │                │            │
    │       ┌────┴────┐        ┌────┴────┐      ┌────┴────┐      │
    │       │ Servers │        │ Servers │      │ Servers │      │
    │       │  VMs    │        │  VMs    │      │  VMs    │      │
    │       └─────────┘        └─────────┘      └─────────┘      │
    │                        Leaf Layer                          │
    └────────────────────────────────────────────────────────────┘
```

#### Multi-Site VXLAN EVPN

```
┌─────────────────────────────┐     ┌─────────────────────────────┐
│         Site A              │     │         Site B              │
│                             │     │                             │
│   ┌───────┐   ┌───────┐    │     │    ┌───────┐   ┌───────┐   │
│   │Spine 1│   │Spine 2│    │     │    │Spine 1│   │Spine 2│   │
│   └───┬───┘   └───┬───┘    │     │    └───┬───┘   └───┬───┘   │
│       │           │        │     │        │           │        │
│   ┌───┴───────────┴───┐    │     │    ┌───┴───────────┴───┐   │
│   │                   │    │     │    │                   │   │
│   │                   │    │     │    │                   │   │
│   │  Border Gateway   │    │     │    │  Border Gateway   │   │
│   │     (BGW)         │◄───┼─────┼───►│     (BGW)         │   │
│   │                   │    │     │    │                   │   │
│   └───────────────────┘    │     │    └───────────────────┘   │
│                             │     │                             │
│   ┌─────┐ ┌─────┐ ┌─────┐  │     │  ┌─────┐ ┌─────┐ ┌─────┐  │
│   │Leaf1│ │Leaf2│ │Leaf3│  │     │  │Leaf1│ │Leaf2│ │Leaf3│  │
│   └─────┘ └─────┘ └─────┘  │     │  └─────┘ └─────┘ └─────┘  │
│                             │     │                             │
└─────────────────────────────┘     └─────────────────────────────┘
        DCI (Data Center Interconnect)
        - VXLAN over WAN
        - EVPN Type-5 routes
        - Multi-site anycast gateway
```

### VXLAN Best Practices

#### Design Recommendations

**1. Underlay Design**
- Use a simple, scalable underlay (OSPF or eBGP)
- Enable ECMP for load balancing
- Configure appropriate MTU (9216 recommended)
- Use PIM if multicast is required

**2. VTEP Placement**
- Deploy VTEPs on leaf switches
- Use anycast VTEP IP for active-active multi-homing
- Consider vPC/MLAG for server multi-homing

**3. VNI Planning**
```
VNI Allocation Strategy:
┌─────────────┬─────────────────────┬──────────────────────┐
│ VNI Range   │ Purpose             │ Example              │
├─────────────┼─────────────────────┼──────────────────────┤
│ 10000-19999 │ L2 VNIs Tenant 1    │ 10010 = VLAN 10      │
│ 20000-29999 │ L2 VNIs Tenant 2    │ 20010 = VLAN 10      │
│ 30000-39999 │ L3 VNIs             │ 30001 = Tenant1 VRF  │
│ 50000-59999 │ Infrastructure      │ 50001 = Management   │
└─────────────┴─────────────────────┴──────────────────────┘
```

**4. ARP Suppression**
- Enable ARP suppression on all L2 VNIs
- Reduces BUM traffic significantly
- Improves scalability

```cisco
! Enable ARP suppression
switch(config)# interface nve1
switch(config-if-nve)# member vni 10010
switch(config-if-nve-vni)# suppress-arp
```

**5. Anycast Gateway**
- Use the same gateway IP on all VTEPs
- Use the same virtual MAC across fabric
- Enables seamless VM mobility

#### Operational Best Practices

**1. Monitoring**
```cisco
! Key monitoring commands
show nve peers
show nve vni
show bgp l2vpn evpn summary
show l2route evpn mac all
show l2route evpn mac-ip all
show fabric forwarding ip local-host-db vrf all
```

**2. Documentation Requirements**
- VNI-to-VLAN mapping table
- VTEP inventory with IP addresses
- Tenant-to-VRF mapping
- Network diagrams with VNI overlays

**3. Change Management**
- Test VNI additions in lab first
- Use consistent naming conventions
- Maintain version control for configurations
- Document rollback procedures

### VXLAN Security

#### Security Considerations

**1. Underlay Security**
```cisco
! Secure underlay with ACLs
ip access-list UNDERLAY_PROTECTION
  permit ospf any any
  permit udp any any eq 4789  ! VXLAN
  permit tcp any any eq 179   ! BGP
  permit icmp any any
  deny ip any any log

! Apply to underlay interfaces
interface Ethernet1/1
  ip access-group UNDERLAY_PROTECTION in
```

**2. Control Plane Security**
```cisco
! BGP authentication
router bgp 65001
  neighbor 10.1.1.100 password 3 SecureBGPPass123

! OSPF authentication
interface Ethernet1/1
  ip ospf authentication message-digest
  ip ospf message-digest-key 1 md5 SecureOSPFPass123
```

**3. Data Plane Security**
- VNI isolation provides tenant separation
- Use VRFs for inter-tenant isolation
- Implement microsegmentation where needed

**4. VXLAN-Specific Attacks**

| Attack | Description | Mitigation |
|--------|-------------|------------|
| VNI Injection | Attacker injects packets with spoofed VNI | ACLs on underlay, VTEP authentication |
| VTEP Spoofing | Attacker impersonates a VTEP | BGP EVPN with authentication |
| BUM Flooding | Amplification attack via broadcast | ARP suppression, rate limiting |
| Underlay Attack | Attack on IP underlay affects overlay | Underlay ACLs, authentication |

### VXLAN Troubleshooting

#### Common Issues and Solutions

**1. VTEP Reachability**
```cisco
! Verify NVE interface status
show nve interface nve1

! Verify NVE peers
show nve peers

! Test underlay connectivity
ping 10.2.1.2 source-interface loopback1

! Verify BGP EVPN neighbors
show bgp l2vpn evpn summary
```

**2. VNI Issues**
```cisco
! Verify VNI status
show nve vni

! Verify VLAN to VNI mapping
show vxlan

! Check for VNI in EVPN
show bgp l2vpn evpn vni-id 10010
```

**3. MAC Learning Issues**
```cisco
! Show local MAC addresses
show mac address-table vlan 10

! Show remote MAC addresses (EVPN)
show l2route evpn mac all

! Show MAC-IP bindings
show l2route evpn mac-ip all
```

#### Troubleshooting Flowchart

```
VXLAN Communication Issue?
           │
           ▼
    ┌──────────────┐     No
    │  NVE up/up?  │─────────► Check loopback, feature
    └──────┬───────┘           enablement
           │ Yes
           ▼
    ┌──────────────┐     No
    │ VTEP peers   │─────────► Check underlay routing,
    │  visible?    │           BGP EVPN
    └──────┬───────┘
           │ Yes
           ▼
    ┌──────────────┐     No
    │  VNI active  │─────────► Check VLAN-VNI mapping,
    │   on NVE?    │           VLAN state
    └──────┬───────┘
           │ Yes
           ▼
    ┌──────────────┐     No
    │ MAC learned  │─────────► Check port, server NIC,
    │ locally?     │           VLAN assignment
    └──────┬───────┘
           │ Yes
           ▼
    ┌──────────────┐     No
    │ MAC in EVPN  │─────────► Check BGP EVPN config,
    │   routes?    │           RT import/export
    └──────┬───────┘
           │ Yes
           ▼
    ┌──────────────┐
    │ Check MTU,   │
    │ routing, ACLs│
    └──────────────┘
```

#### VXLAN Packet Capture Analysis

```bash
# Capture VXLAN packets on Linux
tcpdump -i eth0 'udp port 4789' -w vxlan_capture.pcap

# Capture with verbose output
tcpdump -i eth0 'udp port 4789' -nn -vvv

# Analyze with tshark
tshark -r vxlan_capture.pcap -V -Y 'vxlan'

# Filter for specific VNI
tshark -r vxlan_capture.pcap -Y 'vxlan.vni == 10010'
```

---

## VAP (Virtual Access Point)

### VAP Fundamentals

#### What is a Virtual Access Point?

A Virtual Access Point (VAP) is a logical wireless network created on a physical access point (AP) that allows a single radio to broadcast multiple SSIDs (Service Set Identifiers). Each VAP operates as an independent wireless network with its own security settings, VLAN assignment, and policies.

#### Key Concepts

**Physical AP vs Virtual AP:**
```
┌─────────────────────────────────────────────────────────────┐
│                    Physical Access Point                    │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │                     Radio 1 (2.4GHz)                │   │
│  │  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐   │   │
│  │  │  VAP1   │ │  VAP2   │ │  VAP3   │ │  VAP4   │   │   │
│  │  │Corporate│ │  Guest  │ │   IoT   │ │  Voice  │   │   │
│  │  │VLAN 10  │ │VLAN 100 │ │VLAN 200 │ │VLAN 50  │   │   │
│  │  └─────────┘ └─────────┘ └─────────┘ └─────────┘   │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │                     Radio 2 (5GHz)                  │   │
│  │  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐   │   │
│  │  │  VAP1   │ │  VAP2   │ │  VAP3   │ │  VAP4   │   │   │
│  │  │Corporate│ │  Guest  │ │   IoT   │ │  Voice  │   │   │
│  │  │VLAN 10  │ │VLAN 100 │ │VLAN 200 │ │VLAN 50  │   │   │
│  │  └─────────┘ └─────────┘ └─────────┘ └─────────┘   │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

#### VAP Terminology

| Term | Definition |
|------|------------|
| SSID | Service Set Identifier - Network name |
| BSSID | Basic Service Set Identifier - MAC address of VAP |
| WLAN | Wireless LAN - Logical wireless network |
| BSS | Basic Service Set - Single AP coverage area |
| ESS | Extended Service Set - Multiple APs, same network |

### VAP Architecture

#### Component Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                   Wireless Controller                        │
│                                                              │
│  ┌────────────────────────────────────────────────────────┐ │
│  │              WLAN Configuration Database               │ │
│  │  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐      │ │
│  │  │ WLAN 1  │ │ WLAN 2  │ │ WLAN 3  │ │ WLAN 4  │      │ │
│  │  │Corporate│ │  Guest  │ │   IoT   │ │  Voice  │      │ │
│  │  └─────────┘ └─────────┘ └─────────┘ └─────────┘      │ │
│  └────────────────────────────────────────────────────────┘ │
│                           │                                  │
│                    CAPWAP/LWAPP                             │
│                           │                                  │
└───────────────────────────┼──────────────────────────────────┘
                            │
         ┌──────────────────┼──────────────────┐
         │                  │                  │
    ┌────┴────┐        ┌────┴────┐        ┌────┴────┐
    │   AP1   │        │   AP2   │        │   AP3   │
    │  VAPs   │        │  VAPs   │        │  VAPs   │
    └─────────┘        └─────────┘        └─────────┘
```

#### BSSID Allocation

Each VAP requires a unique BSSID (MAC address):

```
Physical AP MAC: 00:11:22:33:44:50

Radio 1 BSSIDs:
- VAP1: 00:11:22:33:44:50
- VAP2: 00:11:22:33:44:51
- VAP3: 00:11:22:33:44:52
- VAP4: 00:11:22:33:44:53

Radio 2 BSSIDs:
- VAP1: 00:11:22:33:44:60
- VAP2: 00:11:22:33:44:61
- VAP3: 00:11:22:33:44:62
- VAP4: 00:11:22:33:44:63
```

#### Beacon and Probe Response

Each VAP transmits its own beacons:

```
Timeline of Beacon Transmissions (100ms Target Beacon Transmission Time):
─────────────────────────────────────────────────────────────────────────►
│     │     │     │     │     │     │     │     │
VAP1  VAP2  VAP3  VAP4  VAP1  VAP2  VAP3  VAP4
0ms   25ms  50ms  75ms  100ms 125ms 150ms 175ms

With 4 VAPs, each gets ~25ms beacon interval within 100ms TBTT
```

### VAP Implementation

#### Controller-Based Architecture (Cisco WLC)

**WLAN Configuration:**
```cisco
! Create WLAN for Corporate users
(Cisco Controller) > config wlan create 1 Corporate Corporate-Network
(Cisco Controller) > config wlan interface 1 vlan10
(Cisco Controller) > config wlan security wpa2 enable 1
(Cisco Controller) > config wlan security wpa2 ciphers aes enable 1
(Cisco Controller) > config wlan security wpa akm 802.1x enable 1
(Cisco Controller) > config wlan radius_server auth add 1 1
(Cisco Controller) > config wlan enable 1

! Create WLAN for Guest users
(Cisco Controller) > config wlan create 2 Guest Guest-Network
(Cisco Controller) > config wlan interface 2 vlan100
(Cisco Controller) > config wlan security wpa2 enable 2
(Cisco Controller) > config wlan security wpa2 ciphers aes enable 2
(Cisco Controller) > config wlan security wpa akm psk enable 2
(Cisco Controller) > config wlan security wpa akm psk set-key ascii GuestPass123 2
(Cisco Controller) > config wlan webauth enable 2
(Cisco Controller) > config wlan enable 2

! Create WLAN for IoT devices
(Cisco Controller) > config wlan create 3 IoT IoT-Devices
(Cisco Controller) > config wlan interface 3 vlan200
(Cisco Controller) > config wlan security wpa2 enable 3
(Cisco Controller) > config wlan security wpa2 ciphers aes enable 3
(Cisco Controller) > config wlan security wpa akm psk enable 3
(Cisco Controller) > config wlan security wpa akm psk set-key ascii IoTSecure456 3
(Cisco Controller) > config wlan enable 3

! Verify WLAN configuration
(Cisco Controller) > show wlan summary
(Cisco Controller) > show wlan 1
```

**AP Group Configuration:**
```cisco
! Create AP group for specific location
(Cisco Controller) > config wlan apgroup add Building-A

! Add WLANs to AP group
(Cisco Controller) > config wlan apgroup interface-mapping add Building-A 1 vlan10
(Cisco Controller) > config wlan apgroup interface-mapping add Building-A 2 vlan100
(Cisco Controller) > config wlan apgroup interface-mapping add Building-A 3 vlan200

! Add APs to group
(Cisco Controller) > config ap group-name Building-A AP-1st-Floor
(Cisco Controller) > config ap group-name Building-A AP-2nd-Floor
```

#### Controller-Based Architecture (Aruba)

```aruba
! Create SSID profile
(Aruba) (config)# wlan ssid-profile Corporate
(Aruba) (SSID Profile "Corporate")# essid Corporate-Network
(Aruba) (SSID Profile "Corporate")# opmode wpa2-aes
(Aruba) (SSID Profile "Corporate")# exit

! Create AAA profile
(Aruba) (config)# aaa profile Corporate-AAA
(Aruba) (AAA Profile "Corporate-AAA")# authentication-dot1x
(Aruba) (AAA Profile "Corporate-AAA")# dot1x-default-role authenticated
(Aruba) (AAA Profile "Corporate-AAA")# radius-server RADIUS-Server
(Aruba) (AAA Profile "Corporate-AAA")# exit

! Create Virtual AP profile
(Aruba) (config)# wlan virtual-ap Corporate-VAP
(Aruba) (Virtual AP profile "Corporate-VAP")# aaa-profile Corporate-AAA
(Aruba) (Virtual AP profile "Corporate-VAP")# ssid-profile Corporate
(Aruba) (Virtual AP profile "Corporate-VAP")# vlan 10
(Aruba) (Virtual AP profile "Corporate-VAP")# exit

! Create Guest SSID
(Aruba) (config)# wlan ssid-profile Guest
(Aruba) (SSID Profile "Guest")# essid Guest-Network
(Aruba) (SSID Profile "Guest")# opmode wpa2-psk-aes
(Aruba) (SSID Profile "Guest")# wpa-passphrase GuestPass123
(Aruba) (SSID Profile "Guest")# exit

! Create Guest VAP
(Aruba) (config)# wlan virtual-ap Guest-VAP
(Aruba) (Virtual AP profile "Guest-VAP")# ssid-profile Guest
(Aruba) (Virtual AP profile "Guest-VAP")# vlan 100
(Aruba) (Virtual AP profile "Guest-VAP")# captive-portal enable
(Aruba) (Virtual AP profile "Guest-VAP")# exit

! Apply to AP group
(Aruba) (config)# ap-group Building-A
(Aruba) (AP group "Building-A")# virtual-ap Corporate-VAP
(Aruba) (AP group "Building-A")# virtual-ap Guest-VAP
(Aruba) (AP group "Building-A")# exit
```

#### Autonomous AP Configuration

```cisco
! Configure SSID on autonomous AP
AP(config)# dot11 ssid Corporate
AP(config-ssid)# vlan 10
AP(config-ssid)# authentication open eap eap_methods
AP(config-ssid)# authentication network-eap eap_methods
AP(config-ssid)# authentication key-management wpa version 2
AP(config-ssid)# mbssid guest-mode
AP(config-ssid)# exit

! Configure Guest SSID
AP(config)# dot11 ssid Guest
AP(config-ssid)# vlan 100
AP(config-ssid)# authentication open
AP(config-ssid)# wpa-psk ascii GuestPass123
AP(config-ssid)# authentication key-management wpa version 2
AP(config-ssid)# mbssid guest-mode
AP(config-ssid)# exit

! Apply SSIDs to radio
AP(config)# interface Dot11Radio0
AP(config-if)# mbssid
AP(config-if)# ssid Corporate
AP(config-if)# ssid Guest
AP(config-if)# no shutdown
AP(config-if)# exit

! Configure VLAN interfaces
AP(config)# interface Dot11Radio0.10
AP(config-subif)# encapsulation dot1q 10
AP(config-subif)# bridge-group 10
AP(config-subif)# exit

AP(config)# interface Dot11Radio0.100
AP(config-subif)# encapsulation dot1q 100
AP(config-subif)# bridge-group 100
AP(config-subif)# exit

! Configure ethernet trunk
AP(config)# interface GigabitEthernet0.10
AP(config-subif)# encapsulation dot1q 10
AP(config-subif)# bridge-group 10
AP(config-subif)# exit

AP(config)# interface GigabitEthernet0.100
AP(config-subif)# encapsulation dot1q 100
AP(config-subif)# bridge-group 100
AP(config-subif)# exit
```

### VAP Configuration

#### VAP Design Considerations

**1. Number of VAPs per Radio**
```
Recommended Maximum: 4-8 VAPs per radio

Factors affecting performance:
- Beacon overhead (each VAP sends beacons)
- Management frame overhead
- Airtime efficiency
- Client capacity per VAP

Calculation:
Target Beacon Transmission Time (TBTT): 100ms (102.4ms actual)
Beacon size: ~300 bytes @ 6Mbps = ~0.4ms per beacon
8 VAPs = ~3.2ms beacon transmission time per TBTT
Overhead: ~3.2% of airtime for beacons
```

**2. VLAN-to-VAP Mapping**

| VAP | SSID | VLAN | Purpose | Security |
|-----|------|------|---------|----------|
| 1 | Corporate | 10 | Employee access | 802.1X/EAP |
| 2 | Guest | 100 | Guest access | PSK + Captive Portal |
| 3 | IoT | 200 | IoT devices | PSK |
| 4 | Voice | 50 | VoIP phones | 802.1X + QoS |
| 5 | BYOD | 150 | Personal devices | 802.1X + Onboarding |

**3. Radio Frequency Planning**

```
              VAP Distribution Across Radios

2.4GHz Radio:                          5GHz Radio:
┌─────────────────────────┐            ┌─────────────────────────┐
│ Channels: 1, 6, 11      │            │ Channels: 36-165        │
│ Max VAPs: 4 recommended │            │ Max VAPs: 8 recommended │
│                         │            │                         │
│ Use for:                │            │ Use for:                │
│ - Legacy devices        │            │ - High-bandwidth apps   │
│ - IoT with 2.4GHz only  │            │ - Enterprise devices    │
│ - Extended range needed │            │ - Video/Voice           │
└─────────────────────────┘            └─────────────────────────┘
```

#### QoS Configuration for VAPs

**WMM (Wi-Fi Multimedia) Settings:**
```cisco
! Cisco WLC - Configure WLAN QoS
(Cisco Controller) > config wlan qos 1 platinum
(Cisco Controller) > config wlan wmm allow 1
(Cisco Controller) > config wlan call-snoop enable 1

! QoS Profiles:
! Platinum - Voice (highest priority)
! Gold - Video
! Silver - Best Effort (default)
! Bronze - Background (lowest priority)

! Configure Voice WLAN
(Cisco Controller) > config wlan qos 4 platinum
(Cisco Controller) > config wlan wmm require 4
(Cisco Controller) > config wlan call-snoop enable 4
(Cisco Controller) > config wlan avc 4 profile Voice-Profile
```

### VAP Security

#### Authentication Methods

**1. WPA2/WPA3 Enterprise (802.1X)**
```
Client ◄──────────────────► AP ◄──────────────────► RADIUS
       EAP over 802.11            RADIUS (UDP 1812)

Authentication Flow:
1. Client associates with VAP
2. AP sends EAP-Request/Identity
3. Client responds with identity
4. EAP method exchange (PEAP, EAP-TLS, etc.)
5. RADIUS Access-Accept/Reject
6. 4-way handshake for key derivation
7. Client connected
```

**2. WPA2/WPA3 Personal (PSK/SAE)**
```
Pre-Shared Key Authentication:
1. Client associates with VAP
2. 4-way handshake begins
   - AP sends ANonce
   - Client sends SNonce + MIC
   - AP sends GTK + MIC
   - Client sends ACK
3. Client connected with PTK/GTK

SAE (Simultaneous Authentication of Equals) for WPA3:
1. Commit exchange (Diffie-Hellman)
2. Confirm exchange (verification)
3. 4-way handshake
4. Client connected
```

**3. Captive Portal (Guest Authentication)**
```cisco
! Cisco WLC Captive Portal Configuration
(Cisco Controller) > config wlan security web-auth enable 2
(Cisco Controller) > config wlan security web-auth server-precedence 2 local radius ldap

! External web authentication
(Cisco Controller) > config wlan security web-auth 2 external
(Cisco Controller) > config custom-web redirectUrl https://portal.company.com/guest
```

#### Per-VAP Security Policies

**Role-Based Access Control:**
```aruba
! Aruba - Define user roles
(Aruba) (config)# user-role employee
(Aruba) (config-role)# access-list session global-sacl
(Aruba) (config-role)# access-list session apprf-employee-sacl
(Aruba) (config-role)# vlan 10
(Aruba) (config-role)# exit

(Aruba) (config)# user-role guest
(Aruba) (config-role)# access-list session guest-sacl
(Aruba) (config-role)# captive-portal guest-cp
(Aruba) (config-role)# vlan 100
(Aruba) (config-role)# bandwidth-limit downstream 10000
(Aruba) (config-role)# bandwidth-limit upstream 5000
(Aruba) (config-role)# exit

! Access control list for guests
(Aruba) (config)# ip access-list session guest-sacl
(Aruba) (config-sess-guest-sacl)# any any svc-http permit
(Aruba) (config-sess-guest-sacl)# any any svc-https permit
(Aruba) (config-sess-guest-sacl)# any any svc-dns permit
(Aruba) (config-sess-guest-sacl)# any network 10.0.0.0 255.0.0.0 any deny
(Aruba) (config-sess-guest-sacl)# any network 172.16.0.0 255.240.0.0 any deny
(Aruba) (config-sess-guest-sacl)# any network 192.168.0.0 255.255.0.0 any deny
(Aruba) (config-sess-guest-sacl)# any any any permit
(Aruba) (config-sess-guest-sacl)# exit
```

**Client Isolation:**
```cisco
! Cisco WLC - Enable peer-to-peer blocking
(Cisco Controller) > config wlan peer-blocking drop 2

! Options:
! disable - No blocking
! drop - Drop packets between clients
! forward-upstream - Forward to switch for filtering
```

### VAP Best Practices

#### Design Best Practices

**1. Limit VAP Count**
- Maximum 4-8 VAPs per radio
- Each VAP adds beacon overhead
- Consider band-specific VAP deployment

**2. SSID Naming Standards**
```
Format: <Organization>-<Purpose>[-<Security>]

Examples:
- ACME-Corporate
- ACME-Guest
- ACME-IoT
- ACME-Voice

Avoid:
- Generic names (Free WiFi, Public)
- Personally identifiable information
- Location-specific names (hard to maintain)
```

**3. VLAN Design**
```
VLAN Strategy per VAP:

┌───────────────────────────────────────────────────────────────┐
│ VAP Type      │ VLAN Range │ Notes                           │
├───────────────┼────────────┼─────────────────────────────────┤
│ Corporate     │ 10-49      │ Full network access             │
│ Voice         │ 50-99      │ QoS priority, dedicated         │
│ Guest         │ 100-149    │ Internet only, isolated         │
│ BYOD          │ 150-199    │ Limited internal access         │
│ IoT           │ 200-249    │ Segmented, device-specific      │
│ Management    │ 250-254    │ AP management traffic           │
└───────────────────────────────────────────────────────────────┘
```

**4. Security Best Practices**
- Use WPA3 where possible (WPA2 minimum)
- Enable PMF (Protected Management Frames)
- Use 802.1X for corporate networks
- Implement RADIUS with certificate-based auth (EAP-TLS)
- Enable rogue AP detection
- Configure client isolation for guest networks

#### Operational Best Practices

**1. Monitoring**
```cisco
! Cisco WLC - Monitor VAP/WLAN status
(Cisco Controller) > show wlan summary
(Cisco Controller) > show wlan 1
(Cisco Controller) > show client summary
(Cisco Controller) > show ap summary

! Per-WLAN statistics
(Cisco Controller) > show wlan 1 stats
```

**2. Capacity Planning**
```
Client Density Guidelines:

High-Density (Conference rooms, auditoriums):
- 25-30 clients per radio per AP
- Deploy more APs with lower power
- Minimize VAPs (2-3 per radio)

Medium-Density (Office space):
- 40-50 clients per radio per AP
- Standard power settings
- Up to 4 VAPs per radio

Low-Density (Warehouse, outdoor):
- 50+ clients per radio per AP
- Higher power for coverage
- Up to 8 VAPs per radio
```

**3. Troubleshooting Commands**
```cisco
! Cisco WLC Troubleshooting
(Cisco Controller) > debug client <mac-address>
(Cisco Controller) > debug dot11 mobile enable
(Cisco Controller) > debug dot11 state enable
(Cisco Controller) > show client detail <mac-address>
(Cisco Controller) > show ap config 802.11a <ap-name>

! Clear client
(Cisco Controller) > config client deauthenticate <mac-address>
```

---

## Comparison and Use Cases

### Technology Comparison

| Feature | VLAN | VXLAN | VAP |
|---------|------|-------|-----|
| **Layer** | 2 | 2 over 3 | 2 (Wireless) |
| **Scale** | 4,094 | 16 million | 8-16 per AP |
| **Scope** | Single L2 domain | Across L3 | Per Access Point |
| **Transport** | Ethernet | UDP/IP | 802.11 |
| **Use Case** | Campus LAN | Data Center/Cloud | Wireless Networks |
| **Complexity** | Low | Medium-High | Medium |
| **Standards** | IEEE 802.1Q | RFC 7348 | IEEE 802.11 |

### Use Case Matrix

| Scenario | VLAN | VXLAN | VAP |
|----------|------|-------|-----|
| Campus network segmentation | ✓✓✓ | ✓ | ✓✓✓ |
| Data center multi-tenancy | ✓ | ✓✓✓ | N/A |
| Cloud provider infrastructure | ✗ | ✓✓✓ | N/A |
| VM mobility across L3 | ✗ | ✓✓✓ | N/A |
| Wireless guest network | ✓✓ | ✓ | ✓✓✓ |
| IoT segmentation | ✓✓ | ✓ | ✓✓✓ |
| Branch office | ✓✓✓ | ✓ | ✓✓ |

### Detailed Use Cases

#### Use Case 1: Enterprise Campus Network

```
Requirement: Segment corporate network by department

Solution: VLAN + VAP combination

              ┌──────────────────────────────────────────────┐
              │            Core Switch                       │
              │                                              │
              │   VLAN 10: Engineering                       │
              │   VLAN 20: Sales                             │
              │   VLAN 30: HR                                │
              │   VLAN 40: Finance                           │
              │   VLAN 100: Guest                            │
              │   VLAN 200: IoT                              │
              └─────────────────┬────────────────────────────┘
                                │
              ┌─────────────────┼─────────────────┐
              │                 │                 │
         ┌────┴────┐       ┌────┴────┐       ┌────┴────┐
         │ Access  │       │ Access  │       │   AP    │
         │ Switch  │       │ Switch  │       │  VAPs:  │
         │         │       │         │       │ -Corp   │
         │         │       │         │       │ -Guest  │
         │         │       │         │       │ -IoT    │
         └─────────┘       └─────────┘       └─────────┘
              │                 │
         ┌────┴────┐       ┌────┴────┐
         │Endpoints│       │Endpoints│
         │VLAN 10  │       │VLAN 20  │
         └─────────┘       └─────────┘
```

#### Use Case 2: Multi-Tenant Data Center

```
Requirement: Isolate multiple tenants with massive scale

Solution: VXLAN with EVPN

┌────────────────────────────────────────────────────────────────┐
│                    Data Center Fabric                          │
│                                                                │
│     Tenant A          Tenant B          Tenant C               │
│     VNI: 10000        VNI: 20000        VNI: 30000            │
│                                                                │
│  ┌──────────┐     ┌──────────┐     ┌──────────┐              │
│  │ VMs      │     │ VMs      │     │ VMs      │              │
│  │ (Tenant A│     │ (Tenant B│     │ (Tenant C│              │
│  └────┬─────┘     └────┬─────┘     └────┬─────┘              │
│       │                │                │                      │
│  ┌────┴────────────────┴────────────────┴────┐                │
│  │               VXLAN Overlay               │                │
│  │            (Isolated per VNI)             │                │
│  └────┬────────────────┬────────────────┬────┘                │
│       │                │                │                      │
│  ┌────┴────┐      ┌────┴────┐      ┌────┴────┐               │
│  │  Leaf1  │      │  Leaf2  │      │  Leaf3  │               │
│  │  VTEP   │      │  VTEP   │      │  VTEP   │               │
│  └────┬────┘      └────┬────┘      └────┬────┘               │
│       │                │                │                      │
│  ┌────┴────────────────┴────────────────┴────┐                │
│  │              IP Underlay                  │                │
│  └───────────────────────────────────────────┘                │
│                                                                │
└────────────────────────────────────────────────────────────────┘
```

#### Use Case 3: Hybrid Cloud Connectivity

```
Requirement: Extend L2 segments across multiple clouds

Solution: VXLAN over DCI/WAN

┌──────────────────────┐         ┌──────────────────────┐
│    On-Premises DC    │         │     Public Cloud     │
│                      │         │                      │
│    VNI: 50000        │         │    VNI: 50000        │
│    (Workload A)      │         │    (Workload A)      │
│                      │         │                      │
│    ┌─────────┐       │         │       ┌─────────┐   │
│    │   VMs   │       │         │       │   VMs   │   │
│    └────┬────┘       │         │       └────┬────┘   │
│         │            │         │            │        │
│    ┌────┴────┐       │         │       ┌────┴────┐   │
│    │  VTEP   │◄──────┼─────────┼──────►│  VTEP   │   │
│    │ (BGW)   │       │  VXLAN  │       │ (Cloud) │   │
│    └─────────┘       │   DCI   │       └─────────┘   │
│                      │         │                      │
└──────────────────────┘         └──────────────────────┘
```

---

## Integration Strategies

### VLAN and VXLAN Integration

#### VLAN-to-VNI Mapping

```
┌─────────────────────────────────────────────────────────────┐
│                     Leaf Switch (VTEP)                      │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │              VLAN-to-VNI Translation                │   │
│  │                                                     │   │
│  │   VLAN 10  ◄─────────────────►  VNI 10010          │   │
│  │   VLAN 20  ◄─────────────────►  VNI 10020          │   │
│  │   VLAN 30  ◄─────────────────►  VNI 10030          │   │
│  │                                                     │   │
│  │   Access Port ────► VLAN ────► VNI ────► Overlay   │   │
│  │                                                     │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
│  Access Ports (VLAN tagged)      NVE Interface (VXLAN)     │
│       │                                    │                │
│       ▼                                    ▼                │
│  ┌─────────┐                         ┌─────────┐           │
│  │ Servers │                         │ IP      │           │
│  │   VMs   │                         │ Fabric  │           │
│  └─────────┘                         └─────────┘           │
└─────────────────────────────────────────────────────────────┘
```

#### Gateway Integration

**Hardware VTEP Gateway:**
```cisco
! Cisco Nexus - Hardware VTEP with VLAN access
switch(config)# interface Ethernet1/10
switch(config-if)# switchport mode access
switch(config-if)# switchport access vlan 10

switch(config)# vlan 10
switch(config-vlan)# vn-segment 10010

! Traffic from VLAN 10 is encapsulated in VNI 10010
```

**Software Gateway (Linux):**
```bash
# Create bridge for local VLAN traffic
ip link add br10 type bridge
ip link set br10 up

# Create VXLAN interface
ip link add vxlan10 type vxlan id 10010 \
    local 10.1.1.1 \
    dstport 4789 \
    nolearning

# Create VLAN interface
ip link add link eth0 name eth0.10 type vlan id 10

# Add both to bridge
ip link set vxlan10 master br10
ip link set eth0.10 master br10

ip link set vxlan10 up
ip link set eth0.10 up
```

### VAP and VLAN Integration

#### Wireless to Wired VLAN Mapping

```
┌─────────────────────────────────────────────────────────────┐
│                    Access Point                              │
│                                                              │
│   Radio 1 (2.4GHz)              Radio 2 (5GHz)              │
│   ┌───────────┐                 ┌───────────┐               │
│   │ Corporate │ VLAN 10         │ Corporate │ VLAN 10       │
│   │   Guest   │ VLAN 100        │   Guest   │ VLAN 100      │
│   │   IoT     │ VLAN 200        │   Voice   │ VLAN 50       │
│   └─────┬─────┘                 └─────┬─────┘               │
│         │                             │                      │
│         └──────────────┬──────────────┘                      │
│                        │                                     │
│              ┌─────────┴─────────┐                          │
│              │   Trunk Port      │                          │
│              │ VLANs: 10,50,     │                          │
│              │        100,200    │                          │
│              └─────────┬─────────┘                          │
└────────────────────────┼────────────────────────────────────┘
                         │
                         │ 802.1Q Trunk
                         │
              ┌──────────┴──────────┐
              │   Access Switch     │
              │                     │
              │  VLAN 10: Corp LAN  │
              │  VLAN 50: Voice     │
              │  VLAN 100: Guest    │
              │  VLAN 200: IoT      │
              └─────────────────────┘
```

### Three-Tier Integration Example

**Full Stack Integration: VAP → VLAN → VXLAN**

```
                    Wireless Client
                         │
                    ┌────┴────┐
                    │   AP    │ VAP: Corporate
                    │ BSSID:  │ SSID: ACME-Corp
                    │xx:xx:xx │
                    └────┬────┘
                         │ VLAN 10 (802.1Q)
                    ┌────┴────┐
                    │ Access  │
                    │ Switch  │
                    └────┬────┘
                         │ VLAN 10
                    ┌────┴────┐
                    │  Leaf   │ VNI 10010 Mapping
                    │  VTEP   │
                    └────┬────┘
                         │ VXLAN (UDP 4789)
                    ┌────┴────┐
                    │  Spine  │
                    │ Router  │
                    └────┬────┘
                         │ VXLAN
                    ┌────┴────┐
                    │  Leaf   │ VNI 10010 Mapping
                    │  VTEP   │
                    └────┬────┘
                         │ VLAN 10
                    ┌────┴────┐
                    │ Server  │
                    │ on      │
                    │ VLAN 10 │
                    └─────────┘
```

---

## Performance Considerations

### VLAN Performance

#### Factors Affecting VLAN Performance

**1. Broadcast Domain Size**
```
Impact of Broadcast Domain Size:

Devices    Broadcast/sec    Impact
10         10-50           Minimal
100        100-500         Noticeable
500        500-2500        Significant CPU usage
1000+      1000+           Performance degradation

Recommendation: Keep broadcast domains < 250 devices
```

**2. Spanning Tree Convergence**
```
STP Convergence Times:

Protocol     Convergence Time
STP          30-50 seconds
RSTP         1-2 seconds
MST          1-2 seconds
PVST+        30-50 seconds (per VLAN)
Rapid PVST+  1-2 seconds (per VLAN)
```

**3. Inter-VLAN Routing**
```
Routing Method         Throughput      Latency
Router-on-a-Stick     Limited by link  Higher
L3 Switch SVI         Line rate        Lower
Distributed L3        Line rate        Lowest
```

### VXLAN Performance

#### Encapsulation Overhead

```
VXLAN Overhead Breakdown:
- Outer Ethernet: 14 bytes
- Outer IP: 20 bytes
- Outer UDP: 8 bytes
- VXLAN Header: 8 bytes
- Total: 50 bytes

Effective MTU Calculation:
- Underlay MTU: 9216 bytes
- VXLAN Overhead: 50 bytes
- Maximum Inner Frame: 9166 bytes
- Usable Payload: ~9150 bytes (with inner headers)
```

#### Hardware Offload

```
VXLAN Hardware Offload Capabilities:

Feature                  Benefit
VTEP in ASIC            Line-rate encap/decap
TSO (TCP Segmentation)  Reduced CPU for large flows
RSS (Receive Side)      Multi-core distribution
Checksum Offload        CPU bypass for checksums

Verify offload support:
$ ethtool -k eth0 | grep vxlan
tx-udp_tnl-segmentation: on
tx-udp_tnl-csum-segmentation: on
```

#### ECMP and Load Balancing

```cisco
! Cisco NX-OS - Configure ECMP for VXLAN
switch(config)# port-channel load-balance src-dst l4port
switch(config)# hardware access-list tcam region racl 512
switch(config)# hardware access-list tcam region arp-ether 256 double-wide

! Verify ECMP paths
switch# show ip route 10.2.1.2
    *via 10.0.0.2, Eth1/1, [110/80], 1d02h, ospf-1, intra
    *via 10.0.0.6, Eth1/2, [110/80], 1d02h, ospf-1, intra
    *via 10.0.0.10, Eth1/3, [110/80], 1d02h, ospf-1, intra
```

### VAP Performance

#### Airtime Efficiency

```
VAP Impact on Airtime:

Each VAP adds:
- Beacon frames (every 100ms)
- Probe responses
- Association/Authentication overhead

Airtime Calculation for Beacons:
- Beacon size: ~300 bytes
- At 6 Mbps (mandatory rate): ~0.4ms per beacon
- 8 VAPs = 3.2ms per 100ms interval
- Beacon overhead: 3.2%

Recommendation: Limit to 4-8 VAPs per radio
```

#### Client Capacity

```
Per-VAP Client Capacity Considerations:

Factor              Impact
Max associations    Platform dependent (50-200)
Airtime per client  1-5% depending on traffic
Memory per client   ~8KB on controller
Processing          Higher with encryption
```

---

## Future Trends

### Emerging Technologies

#### 1. EVPN Multihoming Enhancements

```
Active-Active Multihoming Evolution:
- Single-Active (legacy)
- Active-Active with ESI (current)
- Anycast VTEP with vPC (current)
- Distributed anycast gateway (emerging)
```

#### 2. SRv6 as VXLAN Alternative

```
Segment Routing v6 (SRv6):
- Native IPv6 encapsulation
- No additional header overhead
- Programming in IPv6 extension headers
- Better integration with SD-WAN

Comparison:
Feature          VXLAN        SRv6
Encapsulation    50 bytes     Variable (IPv6)
Scalability      16M VNIs     Massive (SID space)
Ecosystem        Mature       Emerging
Complexity       Medium       Higher
```

#### 3. Wi-Fi 6E and Wi-Fi 7

```
Impact on VAP Design:

Wi-Fi 6E (6GHz):
- New spectrum = more capacity
- Additional radio for more VAPs
- Dedicated high-performance VAPs

Wi-Fi 7:
- Multi-Link Operation (MLO)
- Simultaneous multi-band connectivity
- Dynamic VAP assignment across bands
```

### Software-Defined Networking Evolution

```
SDN Impact on Network Virtualization:

┌────────────────────────────────────────────────────────────┐
│                    SDN Controller                          │
│           (Centralized Policy Engine)                      │
│                                                            │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐         │
│  │ VLAN Policy │ │VXLAN Policy │ │ VAP Policy  │         │
│  │   Engine    │ │   Engine    │ │   Engine    │         │
│  └──────┬──────┘ └──────┬──────┘ └──────┬──────┘         │
│         │               │               │                  │
│         └───────────────┼───────────────┘                  │
│                         │                                  │
│                  ┌──────┴──────┐                          │
│                  │  Unified    │                          │
│                  │   API       │                          │
│                  └──────┬──────┘                          │
└─────────────────────────┼──────────────────────────────────┘
                          │
         ┌────────────────┼────────────────┐
         │                │                │
    ┌────┴────┐      ┌────┴────┐      ┌────┴────┐
    │ Switches│      │ VTEPs   │      │  WLCs   │
    │ (VLAN)  │      │(VXLAN)  │      │ (VAP)   │
    └─────────┘      └─────────┘      └─────────┘
```

---

## Glossary

| Term | Definition |
|------|------------|
| **802.1Q** | IEEE standard for VLAN tagging |
| **ARP Suppression** | Reduces broadcast by answering ARP locally |
| **BGP EVPN** | BGP-based control plane for EVPN |
| **BUM Traffic** | Broadcast, Unknown unicast, Multicast |
| **BSSID** | Basic Service Set Identifier (MAC of VAP) |
| **CAPWAP** | Control and Provisioning of Wireless Access Points |
| **DEI** | Drop Eligible Indicator in 802.1Q |
| **DTP** | Dynamic Trunking Protocol |
| **ECMP** | Equal-Cost Multi-Path routing |
| **ESI** | Ethernet Segment Identifier |
| **EVPN** | Ethernet VPN (RFC 7432) |
| **GVRP** | GARP VLAN Registration Protocol |
| **IRB** | Integrated Routing and Bridging |
| **MVRP** | Multiple VLAN Registration Protocol |
| **NVE** | Network Virtual Edge |
| **PCP** | Priority Code Point in 802.1Q |
| **PMF** | Protected Management Frames |
| **PVLAN** | Private VLAN |
| **RD** | Route Distinguisher |
| **RT** | Route Target |
| **SAE** | Simultaneous Authentication of Equals (WPA3) |
| **SDN** | Software-Defined Networking |
| **SSID** | Service Set Identifier |
| **STP** | Spanning Tree Protocol |
| **SVI** | Switched Virtual Interface |
| **TBTT** | Target Beacon Transmission Time |
| **TPID** | Tag Protocol Identifier |
| **VACL** | VLAN Access Control List |
| **VAP** | Virtual Access Point |
| **VID** | VLAN Identifier |
| **VLAN** | Virtual Local Area Network |
| **VNI** | VXLAN Network Identifier |
| **VTEP** | VXLAN Tunnel Endpoint |
| **VTP** | VLAN Trunking Protocol |
| **VXLAN** | Virtual Extensible LAN (RFC 7348) |
| **WLC** | Wireless LAN Controller |
| **WMM** | Wi-Fi Multimedia (QoS) |

---

## References

### Standards and RFCs

1. **IEEE 802.1Q-2018** - Bridges and Bridged Networks
2. **IEEE 802.1ad** - Provider Bridges (Q-in-Q)
3. **RFC 7348** - Virtual eXtensible Local Area Network (VXLAN)
4. **RFC 7432** - BGP MPLS-Based Ethernet VPN
5. **RFC 8365** - A Network Virtualization Overlay Solution Using EVPN
6. **IEEE 802.11-2020** - Wireless LAN Medium Access Control and Physical Layer
7. **IEEE 802.11ax** - High Efficiency WLAN (Wi-Fi 6)

### Vendor Documentation

**Cisco:**
- VXLAN EVPN Configuration Guide
- Wireless LAN Controller Configuration Guide
- VLAN Configuration Guide for Catalyst Switches

**Arista:**
- VXLAN Configuration Guide
- EVPN Deployment Guide

**Juniper:**
- EVPN-VXLAN Technical Documentation
- Virtual Chassis Configuration Guide

**Aruba/HPE:**
- ArubaOS User Guide
- Virtual AP Configuration Guide

### Books and Resources

1. "VXLAN Network Engineering" - Lukas Krattiger, et al.
2. "Data Center Virtualization Fundamentals" - Gustavo A.A. Santana
3. "Building Data Centers with VXLAN BGP EVPN" - David Jansen, et al.
4. "Certified Wireless Network Administrator (CWNA) Study Guide"
5. "CCNP and CCIE Enterprise Core ENCOR 350-401 Official Cert Guide"

---

## Appendix A: Quick Reference Cards

### VLAN Quick Reference

```
VLAN ID Range:     1-4094 (1-1005 normal, 1006-4094 extended)
Frame Size:        1522 bytes (with 802.1Q tag)
Tag Format:        TPID (0x8100) + TCI (PCP + DEI + VID)
Native VLAN:       Untagged traffic on trunk (default: 1)
```

### VXLAN Quick Reference

```
VNI Range:         1-16,777,215 (24-bit)
UDP Port:          4789 (default)
Overhead:          50 bytes (Outer Eth + IP + UDP + VXLAN)
Minimum MTU:       1550 bytes (for 1500 inner MTU)
```

### VAP Quick Reference

```
Max VAPs/Radio:    8-16 (vendor dependent, 4-8 recommended)
Beacon Interval:   100ms (102.4ms actual)
BSSID Allocation:  One per VAP per radio
Security:          WPA2/WPA3 Enterprise or Personal
```

---

## Appendix B: Configuration Cheat Sheets

### Cisco VLAN Cheat Sheet

```cisco
! Create VLAN
vlan <id>
  name <name>

! Access Port
interface <int>
  switchport mode access
  switchport access vlan <id>

! Trunk Port
interface <int>
  switchport mode trunk
  switchport trunk allowed vlan <list>
  switchport trunk native vlan <id>

! SVI
interface Vlan<id>
  ip address <ip> <mask>
  no shutdown

! Verify
show vlan brief
show interfaces trunk
show interfaces switchport
```

### Cisco VXLAN EVPN Cheat Sheet

```cisco
! Enable Features
feature nv overlay
feature vn-segment-vlan-based
nv overlay evpn

! NVE Interface
interface nve1
  no shutdown
  source-interface loopback1
  host-reachability protocol bgp
  member vni <vni>
    suppress-arp
    ingress-replication protocol bgp

! EVPN Configuration
evpn
  vni <vni> l2
    rd auto
    route-target import auto
    route-target export auto

! Verify
show nve peers
show nve vni
show bgp l2vpn evpn summary
```

### Wireless VAP Cheat Sheet (Cisco WLC)

```cisco
! Create WLAN
config wlan create <id> <profile> <ssid>
config wlan interface <id> <interface>
config wlan security wpa2 enable <id>
config wlan security wpa2 ciphers aes enable <id>
config wlan enable <id>

! 802.1X Authentication
config wlan security wpa akm 802.1x enable <id>
config wlan radius_server auth add <id> <radius-idx>

! PSK Authentication
config wlan security wpa akm psk enable <id>
config wlan security wpa akm psk set-key ascii <key> <id>

! Verify
show wlan summary
show wlan <id>
show client summary
```

---

*Document Version: 1.0*
*Last Updated: January 2026*
*Author: Network Engineering Team*

