## Phase 6: IP Address Assignment (DHCP)

After the 4-Way Handshake completes, the client needs an IP address.

### 6.1 DHCP Process

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           DHCP PROCESS (DORA)                                │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  Client                        AP                        DHCP Server        │
│    │                           │                              │             │
│    │  DHCP Discover            │                              │             │
│    │  ┌────────────────────────┴──────────────────────────────┴───────┐    │
│    │  │ Source IP: 0.0.0.0                                            │    │
│    │  │ Dest IP: 255.255.255.255 (Broadcast)                          │    │
│    │  │ Source MAC: Client MAC                                        │    │
│    │  │ Options:                                                       │    │
│    │  │   • Message Type: DHCPDISCOVER (1)                            │    │
│    │  │   • Client Identifier: Client MAC                             │    │
│    │  │   • Requested IP: (optional, previous IP)                     │    │
│    │  │   • Parameter Request List: Subnet, Router, DNS, Domain       │    │
│    │  │   • Vendor Class: Device type (e.g., "MSFT 5.0")             │    │
│    │  └───────────────────────────────────────────────────────────────┘    │
│    │ ─────────────────────────────────────────────────────────────────────►│
│    │                                                                       │
│    │  DHCP Offer                                                           │
│    │  ┌───────────────────────────────────────────────────────────────┐   │
│    │  │ Source IP: DHCP Server IP                                     │   │
│    │  │ Dest IP: 255.255.255.255 or Client IP                         │   │
│    │  │ Options:                                                       │   │
│    │  │   • Message Type: DHCPOFFER (2)                               │   │
│    │  │   • Your IP Address: 192.168.1.100                            │   │
│    │  │   • Subnet Mask: 255.255.255.0                                │   │
│    │  │   • Router: 192.168.1.1                                       │   │
│    │  │   • DNS Servers: 8.8.8.8, 8.8.4.4                            │   │
│    │  │   • Lease Time: 86400 seconds (24 hours)                      │   │
│    │  │   • Server Identifier: DHCP Server IP                         │   │
│    │  └───────────────────────────────────────────────────────────────┘   │
│    │ ◄─────────────────────────────────────────────────────────────────────│
│    │                                                                       │
│    │  DHCP Request                                                         │
│    │  ┌───────────────────────────────────────────────────────────────┐   │
│    │  │ Source IP: 0.0.0.0                                            │   │
│    │  │ Dest IP: 255.255.255.255                                      │   │
│    │  │ Options:                                                       │   │
│    │  │   • Message Type: DHCPREQUEST (3)                             │   │
│    │  │   • Requested IP: 192.168.1.100                               │   │
│    │  │   • Server Identifier: DHCP Server IP                         │   │
│    │  │   • Client Identifier: Client MAC                             │   │
│    │  └───────────────────────────────────────────────────────────────┘   │
│    │ ─────────────────────────────────────────────────────────────────────►│
│    │                                                                       │
│    │  DHCP ACK                                                             │
│    │  ┌───────────────────────────────────────────────────────────────┐   │
│    │  │ Source IP: DHCP Server IP                                     │   │
│    │  │ Dest IP: 255.255.255.255 or Client IP                         │   │
│    │  │ Options:                                                       │   │
│    │  │   • Message Type: DHCPACK (5)                                 │   │
│    │  │   • Your IP Address: 192.168.1.100                            │   │
│    │  │   • All configuration parameters                              │   │
│    │  └───────────────────────────────────────────────────────────────┘   │
│    │ ◄─────────────────────────────────────────────────────────────────────│
│    │                                                                       │
│    │  ════════════════════════════════════════════════════════════════    │
│    │              CLIENT NOW HAS IP ADDRESS: 192.168.1.100                 │
│    │  ════════════════════════════════════════════════════════════════    │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 6.2 DHCP Fingerprinting

The AP can identify device types based on DHCP options:

| Device Type | DHCP Fingerprint (Option 55) |
|-------------|------------------------------|
| Windows 10 | 1,3,6,15,31,33,43,44,46,47,119,121,249,252 |
| macOS | 1,121,3,6,15,119,252,95,44,46 |
| iOS | 1,121,3,6,15,119,252,95,44,46 |
| Android | 1,3,6,15,26,28,51,58,59,43 |
| Linux | 1,28,2,3,15,6,119,12,44,47,26,121,42 |

### 6.3 IPv6 Address Assignment

For IPv6, clients can use SLAAC or DHCPv6:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    IPv6 ADDRESS ASSIGNMENT                                   │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  SLAAC (Stateless Address Autoconfiguration):                               │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │ 1. Client sends Router Solicitation (RS)                            │    │
│  │ 2. Router sends Router Advertisement (RA) with prefix               │    │
│  │ 3. Client generates address: Prefix + EUI-64 (from MAC)            │    │
│  │    Example: 2001:db8:1234::/64 + fe80::1234:5678:abcd:ef01          │    │
│  │ 4. Client performs DAD (Duplicate Address Detection)               │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  DHCPv6 (Stateful):                                                         │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │ 1. Client sends DHCPv6 Solicit                                      │    │
│  │ 2. Server sends DHCPv6 Advertise                                    │    │
│  │ 3. Client sends DHCPv6 Request                                      │    │
│  │ 4. Server sends DHCPv6 Reply with address and options              │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

