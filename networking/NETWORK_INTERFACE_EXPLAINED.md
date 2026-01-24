# Network Interface Configuration Explained

This document explains the output of `ifconfig en0` command, breaking down each field and flag.

## Sample Output

```
en0: flags=8863<UP,BROADCAST,SMART,RUNNING,SIMPLEX,MULTICAST> mtu 1500
options=6460<TSO4,TSO6,CHANNEL_IO,PARTIAL_CSUM,ZEROINVERT_CSUM>
ether 84:2f:57:45:99:44
inet6 fe80::17:6f14:80b8:54c0%en0 prefixlen 64 secured scopeid 0xe 
inet 10.86.8.94 netmask 0xfffffc00 broadcast 10.86.11.255
nd6 options=201<PERFORMNUD,DAD>
media: autoselect
status: active
```

---

## Interface Name: `en0`

| Field | Value | Description |
|-------|-------|-------------|
| `en0` | Ethernet 0 | Primary network interface (typically Wi-Fi on macOS, or first Ethernet port) |

The naming convention:
- `en*` = Ethernet/Network interfaces
- `lo0` = Loopback interface
- `bridge*` = Bridge interfaces
- `utun*` = User-space tunnels (VPN)

---

## Flags: `flags=8863<UP,BROADCAST,SMART,RUNNING,SIMPLEX,MULTICAST>`

The hex value `8863` is a bitmask. The flags in angle brackets show which bits are set:

| Flag | Hex Bit | Description |
|------|---------|-------------|
| **UP** | 0x0001 | Interface is administratively enabled and can send/receive traffic |
| **BROADCAST** | 0x0002 | Interface supports broadcasting (sending to all hosts on the network) |
| **SMART** | 0x0020 | Interface manages its own route table (macOS specific) |
| **RUNNING** | 0x0040 | Interface has resources allocated and is operational |
| **SIMPLEX** | 0x0800 | Interface cannot hear its own transmissions (normal for Ethernet) |
| **MULTICAST** | 0x8000 | Interface supports multicast (sending to a group of hosts) |

### Flag Breakdown
```
8863 hex = 1000 1000 0110 0011 binary

Bit 0  (0x0001) = UP          ✓
Bit 1  (0x0002) = BROADCAST   ✓
Bit 5  (0x0020) = SMART       ✓
Bit 6  (0x0040) = RUNNING     ✓
Bit 11 (0x0800) = SIMPLEX     ✓
Bit 15 (0x8000) = MULTICAST   ✓
```

---

## MTU: `mtu 1500`

| Field | Value | Description |
|-------|-------|-------------|
| **MTU** | 1500 bytes | Maximum Transmission Unit - largest packet size the interface can send |

- **1500** is the standard Ethernet MTU
- Larger packets are fragmented or dropped
- Jumbo frames use MTU of 9000 bytes
- VPN/tunnel overhead may require lower MTU (e.g., 1400)

---

## Options: `options=6460<TSO4,TSO6,CHANNEL_IO,PARTIAL_CSUM,ZEROINVERT_CSUM>`

Hardware offload capabilities supported by the NIC:

| Option | Description |
|--------|-------------|
| **TSO4** | TCP Segmentation Offload for IPv4 - NIC handles large TCP segment splitting |
| **TSO6** | TCP Segmentation Offload for IPv6 - Same as TSO4 but for IPv6 |
| **CHANNEL_IO** | Channel-based I/O (macOS network stack optimization) |
| **PARTIAL_CSUM** | Partial checksum offload - NIC computes part of the checksum |
| **ZEROINVERT_CSUM** | Zero-invert checksum handling for UDP |

These options reduce CPU load by offloading network processing to the hardware.

---

## MAC Address: `ether 84:2f:57:45:99:44`

| Field | Value | Description |
|-------|-------|-------------|
| **ether** | 84:2f:57:45:99:44 | Layer 2 hardware (MAC) address |

### MAC Address Breakdown
```
84:2f:57:45:99:44
│       │
└───────┴── OUI (Organizationally Unique Identifier) = 84:2f:57
            Identifies the manufacturer (Apple Inc.)
            
            Last 3 octets (45:99:44) = Device unique identifier
```

- 48 bits total (6 octets)
- Globally unique identifier for the NIC
- Used for Layer 2 (Ethernet) addressing

---

## IPv6 Address: `inet6 fe80::17:6f14:80b8:54c0%en0 prefixlen 64 secured scopeid 0xe`

| Field | Value | Description |
|-------|-------|-------------|
| **inet6** | fe80::17:6f14:80b8:54c0 | IPv6 link-local address |
| **%en0** | Interface scope | Specifies which interface this address is bound to |
| **prefixlen** | 64 | Network prefix length (equivalent to subnet mask) |
| **secured** | - | Address is secured (privacy extensions enabled) |
| **scopeid** | 0xe (14) | Numeric scope identifier for the interface |

### IPv6 Address Type
```
fe80::/10 = Link-Local Address Range
            - Auto-configured on every IPv6 interface
            - Not routable beyond the local network segment
            - Used for neighbor discovery, router discovery
```

---

## IPv4 Address: `inet 10.86.8.94 netmask 0xfffffc00 broadcast 10.86.11.255`

| Field | Value | Description |
|-------|-------|-------------|
| **inet** | 10.86.8.94 | IPv4 address assigned to the interface |
| **netmask** | 0xfffffc00 | Subnet mask in hexadecimal |
| **broadcast** | 10.86.11.255 | Broadcast address for the subnet |

### Subnet Mask Breakdown
```
0xfffffc00 = 255.255.252.0 = /22 CIDR

Binary: 11111111.11111111.11111100.00000000
        └────────────────────────┘└────────┘
              22 network bits      10 host bits

Hosts per subnet: 2^10 - 2 = 1022 usable addresses
Network range: 10.86.8.0 - 10.86.11.255
```

### Address Classification
```
10.x.x.x = Private IP (RFC 1918)
           Class A private range: 10.0.0.0/8
```

---

## ND6 Options: `nd6 options=201<PERFORMNUD,DAD>`

IPv6 Neighbor Discovery options:

| Option | Description |
|--------|-------------|
| **PERFORMNUD** | Perform Neighbor Unreachability Detection - monitors if neighbors are still reachable |
| **DAD** | Duplicate Address Detection - checks for IP conflicts before using an address |

---

## Media: `media: autoselect`

| Field | Value | Description |
|-------|-------|-------------|
| **media** | autoselect | Speed/duplex auto-negotiation enabled |

Possible values:
- `autoselect` - Auto-negotiate speed and duplex
- `100baseTX <full-duplex>` - 100 Mbps full duplex
- `1000baseT <full-duplex>` - 1 Gbps full duplex

---

## Status: `status: active`

| Field | Value | Description |
|-------|-------|-------------|
| **status** | active | Physical link is up and connected |

Possible values:
- `active` - Link detected, cable connected (or Wi-Fi associated)
- `inactive` - No link detected, cable unplugged (or Wi-Fi disconnected)

---

## Summary Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                    Network Interface: en0                    │
├─────────────────────────────────────────────────────────────┤
│  Layer 2 (Data Link)                                        │
│  ├─ MAC: 84:2f:57:45:99:44                                  │
│  ├─ MTU: 1500 bytes                                         │
│  └─ Media: autoselect, Status: active                       │
├─────────────────────────────────────────────────────────────┤
│  Layer 3 (Network)                                          │
│  ├─ IPv4: 10.86.8.94/22                                     │
│  │   └─ Broadcast: 10.86.11.255                             │
│  └─ IPv6: fe80::17:6f14:80b8:54c0/64 (link-local)          │
├─────────────────────────────────────────────────────────────┤
│  Capabilities                                               │
│  ├─ Flags: UP, BROADCAST, RUNNING, MULTICAST               │
│  └─ Offload: TSO4, TSO6, Partial Checksum                  │
└─────────────────────────────────────────────────────────────┘
```

