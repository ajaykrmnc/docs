# DHCP and WiFi Beacon Documentation


## Overview

This document covers two fundamental aspects of WiFi networking:

1. **DHCP (Dynamic Host Configuration Protocol)** - Automatically assigns IP addresses and network configuration to clients after they associate with an AP.

2. **WiFi Beacon Frames** - Periodic management frames broadcast by APs to announce their presence and capabilities.

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    DHCP AND BEACON IN WIFI CONNECTION                        │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  Client                           Access Point              DHCP Server      │
│    │                                   │                         │           │
│    │◄──────── Beacon Frames ──────────│                         │           │
│    │         (Periodic broadcast)      │                         │           │
│    │                                   │                         │           │
│    │─── Probe Request ────────────────►│                         │           │
│    │◄── Probe Response ────────────────│                         │           │
│    │                                   │                         │           │
│    │─── Authentication ───────────────►│                         │           │
│    │◄── Authentication ────────────────│                         │           │
│    │                                   │                         │           │
│    │─── Association Request ──────────►│                         │           │
│    │◄── Association Response ──────────│                         │           │
│    │                                   │                         │           │
│    │◄─── 4-Way Handshake ─────────────►│                         │           │
│    │                                   │                         │           │
│    │══════════════════════════════════════════════════════════════           │
│    │              NOW DHCP CAN BEGIN                                         │
│    │══════════════════════════════════════════════════════════════           │
│    │                                   │                         │           │
│    │─── DHCP Discover ────────────────►│──── DHCP Discover ────►│           │
│    │◄── DHCP Offer ────────────────────│◄─── DHCP Offer ────────│           │
│    │─── DHCP Request ─────────────────►│──── DHCP Request ─────►│           │
│    │◄── DHCP Ack ──────────────────────│◄─── DHCP Ack ──────────│           │
│    │                                   │                         │           │
│    │   [Client now has IP address]     │                         │           │
│    │                                   │                         │           │
└─────────────────────────────────────────────────────────────────────────────┘
```

---
[](2026-01-08_.md)
## DHCP Protocol

### DHCP Basics

DHCP (Dynamic Host Configuration Protocol) is defined in RFC 2131 and operates on UDP ports 67 (server) and 68 (client).

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    DHCP PROTOCOL OVERVIEW                                    │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  Purpose:                                                                    │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  • Automatic IP address assignment                                   │    │
│  │  • Subnet mask configuration                                         │    │
│  │  • Default gateway assignment                                        │    │
│  │  • DNS server configuration                                          │    │
│  │  • Lease time management                                             │    │
│  │  • Domain name assignment                                            │    │
│  │  • NTP server configuration                                          │    │
│  │  • TFTP server for network boot                                      │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  Transport:                                                                  │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  Protocol: UDP                                                       │    │
│  │  Server Port: 67                                                     │    │
│  │  Client Port: 68                                                     │    │
│  │  Broadcast Address: 255.255.255.255                                  │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### DHCP Message Types

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    DHCP MESSAGE TYPES                                        │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  Type │ Name           │ Direction      │ Description                       │
│  ──── │ ────           │ ─────────      │ ───────────                       │
│  1    │ DHCPDISCOVER   │ Client→Server  │ Client broadcasts to find servers │
│  2    │ DHCPOFFER      │ Server→Client  │ Server offers IP address          │
│  3    │ DHCPREQUEST    │ Client→Server  │ Client requests offered address   │
│  4    │ DHCPDECLINE    │ Client→Server  │ Client declines (address in use)  │
│  5    │ DHCPACK        │ Server→Client  │ Server confirms assignment        │
│  6    │ DHCPNAK        │ Server→Client  │ Server denies request             │
│  7    │ DHCPRELEASE    │ Client→Server  │ Client releases IP address        │
│  8    │ DHCPINFORM     │ Client→Server  │ Client requests parameters only   │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### DHCP Four-Message Exchange (DORA)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    DHCP DORA PROCESS                                         │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  Client                                                      Server          │
│    │                                                            │            │
│    │  1. DHCPDISCOVER (Broadcast)                               │            │
│    │────────────────────────────────────────────────────────────►            │
│    │    • Source IP: 0.0.0.0                                    │            │
│    │    • Dest IP: 255.255.255.255                              │            │
│    │    • Client MAC                                            │            │
│    │    • Transaction ID (xid)                                  │            │
│    │    • Option 55 (Parameter Request List)                    │            │
│    │                                                            │            │
│    │  2. DHCPOFFER (Unicast or Broadcast)                       │            │
│    │◄────────────────────────────────────────────────────────────           │
│    │    • Offered IP address (yiaddr)                           │            │
│    │    • Server IP (siaddr)                                    │            │
│    │    • Lease time                                            │            │
│    │    • Subnet mask, gateway, DNS                             │            │
│    │                                                            │            │
│    │  3. DHCPREQUEST (Broadcast)                                │            │
│    │────────────────────────────────────────────────────────────►            │
│    │    • Requested IP (Option 50)                              │            │
│    │    • Server Identifier (Option 54)                         │            │
│    │    • Client ID (Option 61)                                 │            │
│    │                                                            │            │
│    │  4. DHCPACK (Unicast or Broadcast)                         │            │
│    │◄────────────────────────────────────────────────────────────           │
│    │    • Confirms IP assignment                                │            │
│    │    • All configuration parameters                          │            │
│    │    • Lease time                                            │            │
│    │                                                            │            │
│    │  [Client configures network interface]                     │            │
│    │                                                            │            │
└─────────────────────────────────────────────────────────────────────────────┘
```

### DHCP Packet Structure

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    DHCP PACKET FORMAT                                        │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  0                   1                   2                   3               │
│  0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1             │
│  +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+           │
│  |     op (1)    |   htype (1)   |   hlen (1)    |    hops (1)   |           │
│  +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+           │
│  |                            xid (4)                            |           │
│  +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+           │
│  |           secs (2)            |           flags (2)           |           │
│  +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+           │
│  |                          ciaddr (4)                           |           │
│  +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+           │
│  |                          yiaddr (4)                           |           │
│  +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+           │
│  |                          siaddr (4)                           |           │
│  +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+           │
│  |                          giaddr (4)                           |           │
│  +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+           │
│  |                          chaddr (16)                          |           │
│  +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+           │
│  |                          sname (64)                           |           │
│  +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+           │
│  |                          file (128)                           |           │
│  +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+           │
│  |                          options (variable)                   |           │
│  +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+           │
│                                                                              │
│  Field Descriptions:                                                         │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │  Field   │ Size  │ Description                                      │    │
│  │  ─────   │ ────  │ ───────────                                      │    │
│  │  op      │ 1     │ Message type (1=BOOTREQUEST, 2=BOOTREPLY)        │    │
│  │  htype   │ 1     │ Hardware address type (1=Ethernet)              │    │
│  │  hlen    │ 1     │ Hardware address length (6 for Ethernet)        │    │
│  │  hops    │ 1     │ Relay agent hop count                           │    │
│  │  xid     │ 4     │ Transaction ID                                  │    │
│  │  secs    │ 2     │ Seconds elapsed since client began              │    │
│  │  flags   │ 2     │ Flags (bit 0 = broadcast flag)                  │    │
│  │  ciaddr  │ 4     │ Client IP address (if known)                    │    │
│  │  yiaddr  │ 4     │ 'Your' IP address (offered to client)           │    │
│  │  siaddr  │ 4     │ Server IP address                               │    │
│  │  giaddr  │ 4     │ Gateway/relay agent IP address                  │    │
│  │  chaddr  │ 16    │ Client hardware address                         │    │
│  │  sname   │ 64    │ Server host name                                │    │
│  │  file    │ 128   │ Boot file name                                  │    │
│  │  options │ var   │ DHCP options (magic cookie + options)           │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### DHCP Options

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    COMMON DHCP OPTIONS                                       │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  Option │ Name                    │ Description                             │
│  ────── │ ────                    │ ───────────                             │
│  1      │ Subnet Mask             │ Subnet mask for the client              │
│  3      │ Router                  │ Default gateway IP address(es)          │
│  6      │ DNS Servers             │ List of DNS server IP addresses         │
│  12     │ Host Name               │ Client's host name                      │
│  15     │ Domain Name             │ DNS domain name for client              │
│  42     │ NTP Servers             │ Network Time Protocol servers           │
│  50     │ Requested IP            │ Client's requested IP address           │
│  51     │ Lease Time              │ IP address lease time in seconds        │
│  53     │ Message Type            │ DHCP message type (1-8)                 │
│  54     │ Server Identifier       │ DHCP server IP address                  │
│  55     │ Parameter Request List  │ List of requested DHCP options          │
│  58     │ Renewal Time (T1)       │ Time to start renewal (50% of lease)    │
│  59     │ Rebinding Time (T2)     │ Time to start rebinding (87.5% lease)   │
│  60     │ Vendor Class ID         │ Vendor-specific identifier              │
│  61     │ Client Identifier       │ Client's unique identifier              │
│  66     │ TFTP Server Name        │ TFTP server for boot file               │
│  67     │ Bootfile Name           │ Boot file name                          │
│  82     │ Relay Agent Info        │ Circuit ID, Remote ID (Option 82)       │
│  119    │ Domain Search List      │ DNS search suffixes                     │
│  121    │ Classless Static Routes │ Static routes (CIDR format)             │
│  255    │ End                     │ End of options marker                   │
│                                                                              │
│  Magic Cookie: 99.130.83.99 (0x63825363)                                     │
│  - Must appear at the beginning of DHCP options field                        │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### DHCP Relay

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    DHCP RELAY OPERATION                                      │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  DHCP Relay allows DHCP to work across different network segments:          │
│                                                                              │
│  ┌─────────┐      ┌─────────────┐      ┌─────────────┐      ┌────────────┐  │
│  │ Client  │──────│  AP/Relay   │──────│   Router    │──────│DHCP Server │  │
│  │Subnet A │      │   Agent     │      │             │      │  Subnet B  │  │
│  └─────────┘      └─────────────┘      └─────────────┘      └────────────┘  │
│                                                                              │
│  Without Relay:                                                              │
│  - DHCP broadcast (255.255.255.255) stays within subnet                     │
│  - Client cannot reach DHCP server on different subnet                      │
│                                                                              │
│  With Relay Agent:                                                           │
│  1. Client broadcasts DHCPDISCOVER                                          │
│  2. Relay agent receives broadcast                                          │
│  3. Relay agent sets giaddr to its own IP                                   │
│  4. Relay agent unicasts to DHCP server                                     │
│  5. Server responds based on giaddr (knows client's subnet)                 │
│  6. Relay agent forwards response to client                                 │
│                                                                              │
│  Configuration in Arista AP:                                                 │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  # DHCP Relay Configuration                                          │    │
│  │  DHCP_RELAY=1                                                        │    │
│  │  DHCP_RELAY_DESTINATIONS=192.168.1.100,192.168.1.101                 │    │
│  │  DHCP_RELAY_VIA_TUNNEL=0                                             │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### DHCP Fingerprinting

DHCP Fingerprinting is a technique to identify device types based on the DHCP options they request.

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    DHCP FINGERPRINTING                                       │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  How It Works:                                                               │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  1. Client sends DHCPDISCOVER with Option 55 (Parameter Request)    │    │
│  │  2. Option 55 contains list of requested DHCP options               │    │
│  │  3. Different OS/devices request different option combinations      │    │
│  │  4. AP matches fingerprint against known signatures                 │    │
│  │  5. Device type is identified (Windows, iOS, Android, etc.)         │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  Example Fingerprints (Option 55 values):                                    │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  Device Type      │ Option 55 Fingerprint                           │    │
│  │  ───────────      │ ─────────────────────                           │    │
│  │  Windows 10       │ 1,3,6,15,31,33,43,44,46,47,119,121,249,252      │    │
│  │  macOS            │ 1,121,3,6,15,119,252,95,44,46                   │    │
│  │  iOS/iPadOS       │ 1,121,3,6,15,119,252,95,44,46                   │    │
│  │  Android          │ 1,3,6,15,26,28,51,58,59,43                      │    │
│  │  Linux            │ 1,28,2,3,15,6,119,12,44,47,26,121,42            │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  Additional Fingerprinting Sources:                                          │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  • Option 60 (Vendor Class ID) - e.g., "MSFT 5.0" for Windows       │    │
│  │  • Option 12 (Host Name) - Naming patterns                          │    │
│  │  • Option 61 (Client ID) - Client identifier format                 │    │
│  │  • MAC OUI - First 3 bytes of MAC address (manufacturer)            │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  Arista AP DHCP Fingerprinting Configuration:                                │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  DHCP_FP_ENABLED=1                                                   │    │
│  │  DHCP_FP_UNIDENTIFIED_ACTION=allow|deny                              │    │
│  │  DHCP_FP_DEVICE_TYPE=laptop,phone,tablet                             │    │
│  │  DHCP_FP_VENDOR=Apple,Microsoft,Samsung                              │    │
│  │  DHCP_FP_OS_TYPE=iOS,Android,Windows                                 │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  Use Cases:                                                                  │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  • Device-based access control (allow only corporate devices)       │    │
│  │  • BYOD policy enforcement                                          │    │
│  │  • Network segmentation by device type                              │    │
│  │  • Analytics and reporting                                          │    │
│  │  • Security monitoring (detect rogue devices)                       │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### DHCP Option 82

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    DHCP OPTION 82 (RELAY AGENT INFORMATION)                  │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  Option 82 allows relay agents to insert additional information:             │
│                                                                              │
│  Sub-options:                                                                │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  Sub-option │ Name              │ Description                       │    │
│  │  ────────── │ ────              │ ───────────                       │    │
│  │  1          │ Circuit ID        │ Identifies the circuit/port       │    │
│  │  2          │ Remote ID         │ Identifies the relay agent        │    │
│  │  5          │ Link Selection    │ Subnet selection for DHCP server  │    │
│  │  6          │ Subscriber ID     │ Subscriber identification         │    │
│  │  9          │ Vendor-Specific   │ Vendor-specific information       │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  Option 82 Format:                                                           │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  +--------+--------+--------+--------+--------+--------+             │    │
│  │  |   82   | Length |Sub-opt1| Len1   | Data1  |Sub-opt2| ...         │    │
│  │  +--------+--------+--------+--------+--------+--------+             │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  Circuit ID Contents (typical):                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  • VLAN ID                                                           │    │
│  │  • Port number                                                       │    │
│  │  • SSID name                                                         │    │
│  │  • AP name/MAC                                                       │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  Remote ID Contents (typical):                                               │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  • AP MAC address                                                    │    │
│  │  • AP hostname                                                       │    │
│  │  • AP serial number                                                  │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  Use Cases:                                                                  │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  • IP address assignment based on location (AP/SSID)                 │    │
│  │  • Tracking which AP a client connected through                      │    │
│  │  • Per-SSID DHCP pools                                               │    │
│  │  • Audit and compliance logging                                      │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### DHCPv6

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    DHCPv6 OVERVIEW                                           │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  DHCPv6 is the IPv6 version of DHCP, defined in RFC 8415.                   │
│                                                                              │
│  Key Differences from DHCPv4:                                                │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  Feature          │ DHCPv4              │ DHCPv6                    │    │
│  │  ───────          │ ──────              │ ──────                    │    │
│  │  Transport        │ UDP 67/68           │ UDP 546/547               │    │
│  │  Broadcast        │ 255.255.255.255     │ ff02::1:2 (multicast)     │    │
│  │  Client ID        │ MAC or Option 61    │ DUID (unique identifier)  │    │
│  │  Server ID        │ IP address          │ DUID                      │    │
│  │  Relay            │ giaddr field        │ Relay-forward message     │    │
│  │  Prefix Delegation│ Not supported       │ Supported (IA_PD)         │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  DHCPv6 Message Types:                                                       │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  Type │ Name           │ Description                                │    │
│  │  ──── │ ────           │ ───────────                                │    │
│  │  1    │ SOLICIT        │ Client looking for servers                 │    │
│  │  2    │ ADVERTISE      │ Server response to SOLICIT                 │    │
│  │  3    │ REQUEST        │ Client requests configuration              │    │
│  │  4    │ CONFIRM        │ Client confirms address still valid        │    │
│  │  5    │ RENEW          │ Client renews lease                        │    │
│  │  6    │ REBIND         │ Client rebinds to any server               │    │
│  │  7    │ REPLY          │ Server response with configuration         │    │
│  │  8    │ RELEASE        │ Client releases address                    │    │
│  │  9    │ DECLINE        │ Client declines address                    │    │
│  │  11   │ INFORMATION-REQ│ Client requests info only (no address)     │    │
│  │  12   │ RELAY-FORW     │ Relay agent forwards message               │    │
│  │  13   │ RELAY-REPL     │ Relay agent forwards reply                 │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  DHCPv6 Modes:                                                               │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  1. Stateful DHCPv6 (Managed)                                        │    │
│  │     - Server assigns IPv6 addresses                                  │    │
│  │     - Full DHCP functionality                                        │    │
│  │     - Router Advertisement M flag = 1                                │    │
│  │                                                                      │    │
│  │  2. Stateless DHCPv6 (Other)                                         │    │
│  │     - Client uses SLAAC for address                                  │    │
│  │     - DHCP provides DNS, NTP, etc.                                   │    │
│  │     - Router Advertisement O flag = 1                                │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### DHCP Server Configuration (udhcpd)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    UDHCPD CONFIGURATION                                      │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  Arista APs use udhcpd (BusyBox DHCP server) for local DHCP:                │
│                                                                              │
│  Configuration File: /etc/udhcpd.conf                                        │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  # Interface to serve DHCP on                                        │    │
│  │  interface       br0                                                 │    │
│  │                                                                      │    │
│  │  # IP address range                                                  │    │
│  │  start           192.168.1.100                                       │    │
│  │  end             192.168.1.200                                       │    │
│  │                                                                      │    │
│  │  # Lease time in seconds (default 12 hours)                          │    │
│  │  lease_file      /var/lib/misc/udhcpd.leases                         │    │
│  │  max_leases      100                                                 │    │
│  │  auto_time       7200                                                │    │
│  │                                                                      │    │
│  │  # DHCP Options                                                      │    │
│  │  opt     dns     8.8.8.8 8.8.4.4                                     │    │
│  │  opt     subnet  255.255.255.0                                       │    │
│  │  opt     router  192.168.1.1                                         │    │
│  │  opt     domain  local                                               │    │
│  │  opt     lease   86400                                               │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  Starting udhcpd:                                                            │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  # Start DHCP server                                                 │    │
│  │  udhcpd /etc/udhcpd.conf                                             │    │
│  │                                                                      │    │
│  │  # Start in foreground (debug)                                       │    │
│  │  udhcpd -f /etc/udhcpd.conf                                          │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## WiFi Beacon Frames

### Beacon Basics

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    WIFI BEACON OVERVIEW                                      │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  What is a Beacon?                                                           │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  A beacon is a management frame broadcast by an Access Point to:    │    │
│  │                                                                      │    │
│  │  • Announce the presence of a WiFi network                          │    │
│  │  • Advertise network capabilities and parameters                    │    │
│  │  • Synchronize client timing                                        │    │
│  │  • Indicate buffered frames for power-save clients                  │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  Beacon Transmission:                                                        │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  Access Point                                                        │    │
│  │       │                                                              │    │
│  │       │──── Beacon ────────────────────────────────────►            │    │
│  │       │                                    (Broadcast)               │    │
│  │       │                                                              │    │
│  │       │──── Beacon ────────────────────────────────────►            │    │
│  │       │                                    (100 TU later)            │    │
│  │       │                                                              │    │
│  │       │──── Beacon ────────────────────────────────────►            │    │
│  │       │                                    (200 TU later)            │    │
│  │       │                                                              │    │
│  │  TU = Time Unit = 1024 microseconds ≈ 1.024 ms                       │    │
│  │  Default Beacon Interval = 100 TU ≈ 102.4 ms                         │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  Beacon vs Probe Response:                                                   │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  Feature        │ Beacon              │ Probe Response              │    │
│  │  ───────        │ ──────              │ ──────────────              │    │
│  │  Trigger        │ Periodic timer      │ Probe Request from client   │    │
│  │  Destination    │ Broadcast           │ Unicast to requester        │    │
│  │  Contains TIM   │ Yes                 │ No                          │    │
│  │  Content        │ Nearly identical    │ Nearly identical            │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Beacon Frame Structure

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    BEACON FRAME FORMAT                                       │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  MAC Header (24 bytes):                                                      │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  +──────────+──────────+──────────+──────────+──────────+──────────+ │    │
│  │  │Frame Ctrl│ Duration │  DA      │  SA      │  BSSID   │ Seq Ctrl │ │    │
│  │  │ (2)      │ (2)      │  (6)     │  (6)     │  (6)     │ (2)      │ │    │
│  │  +──────────+──────────+──────────+──────────+──────────+──────────+ │    │
│  │                                                                      │    │
│  │  Frame Control: 0x8000 (Beacon)                                      │    │
│  │  DA: FF:FF:FF:FF:FF:FF (Broadcast)                                   │    │
│  │  SA: AP MAC address                                                  │    │
│  │  BSSID: AP MAC address (same as SA for infrastructure mode)          │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  Beacon Frame Body:                                                          │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  +──────────+──────────+──────────+──────────────────────────────+  │    │
│  │  │Timestamp │ Beacon   │Capability│ Information Elements         │  │    │
│  │  │ (8)      │ Interval │ Info (2) │ (variable)                   │  │    │
│  │  │          │ (2)      │          │                              │  │    │
│  │  +──────────+──────────+──────────+──────────────────────────────+  │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  Fixed Fields:                                                               │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  Field           │ Size  │ Description                              │    │
│  │  ─────           │ ────  │ ───────────                              │    │
│  │  Timestamp       │ 8     │ TSF timer value (microseconds)           │    │
│  │  Beacon Interval │ 2     │ Time between beacons (TUs)               │    │
│  │  Capability Info │ 2     │ Network capabilities bitmap              │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  Capability Information Bits:                                                │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  Bit │ Name              │ Description                              │    │
│  │  ─── │ ────              │ ───────────                              │    │
│  │  0   │ ESS               │ Infrastructure mode (AP)                 │    │
│  │  1   │ IBSS              │ Ad-hoc mode                              │    │
│  │  2   │ CF-Pollable       │ Point coordination function              │    │
│  │  3   │ CF-Poll Request   │ PCF poll request                         │    │
│  │  4   │ Privacy           │ WEP/WPA/WPA2 encryption required         │    │
│  │  5   │ Short Preamble    │ Short preamble supported                 │    │
│  │  6   │ Reserved          │                                          │    │
│  │  7   │ Reserved          │                                          │    │
│  │  8   │ Spectrum Mgmt     │ 802.11h spectrum management              │    │
│  │  9   │ QoS               │ 802.11e QoS supported                    │    │
│  │  10  │ Short Slot Time   │ Short slot time (9μs vs 20μs)            │    │
│  │  11  │ APSD              │ Automatic power save delivery            │    │
│  │  12  │ Radio Measurement │ 802.11k radio measurement                │    │
│  │  13  │ Reserved          │                                          │    │
│  │  14  │ Delayed Block Ack │ Delayed block acknowledgment             │    │
│  │  15  │ Immediate Block Ack│ Immediate block acknowledgment          │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Information Elements

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    BEACON INFORMATION ELEMENTS                               │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  Information Element Format:                                                 │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  +──────────+──────────+──────────────────────────────────────────+ │    │
│  │  │ Element  │ Length   │ Element Data                             │ │    │
│  │  │ ID (1)   │ (1)      │ (variable, 0-255 bytes)                  │ │    │
│  │  +──────────+──────────+──────────────────────────────────────────+ │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  Common Information Elements:                                                │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  ID  │ Name                    │ Description                        │    │
│  │  ──  │ ────                    │ ───────────                        │    │
│  │  0   │ SSID                    │ Network name (0-32 bytes)          │    │
│  │  1   │ Supported Rates         │ Basic and supported data rates     │    │
│  │  3   │ DS Parameter Set        │ Current channel number             │    │
│  │  5   │ TIM                     │ Traffic Indication Map             │    │
│  │  7   │ Country                 │ Country code and channels          │    │
│  │  32  │ Power Constraint        │ Local power constraint             │    │
│  │  42  │ ERP Information         │ 802.11g protection modes           │    │
│  │  45  │ HT Capabilities         │ 802.11n capabilities               │    │
│  │  48  │ RSN                     │ WPA2/WPA3 security parameters      │    │
│  │  50  │ Extended Supported Rates│ Additional data rates              │    │
│  │  61  │ HT Operation            │ 802.11n operation parameters       │    │
│  │  127 │ Extended Capabilities   │ Additional capability flags        │    │
│  │  191 │ VHT Capabilities        │ 802.11ac capabilities              │    │
│  │  192 │ VHT Operation           │ 802.11ac operation parameters      │    │
│  │  221 │ Vendor Specific         │ Vendor-specific data (WPA, WMM)    │    │
│  │  255 │ Extension               │ Extended element (HE, EHT)         │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  Extended Element IDs (Element ID 255):                                      │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  Ext ID │ Name                  │ Description                       │    │
│  │  ────── │ ────                  │ ───────────                       │    │
│  │  35     │ HE Capabilities       │ 802.11ax (WiFi 6) capabilities    │    │
│  │  36     │ HE Operation          │ 802.11ax operation parameters     │    │
│  │  37     │ UORA Parameter Set    │ Uplink OFDMA random access        │    │
│  │  38     │ MU EDCA Parameter Set │ Multi-user EDCA parameters        │    │
│  │  39     │ Spatial Reuse         │ BSS coloring parameters           │    │
│  │  106    │ EHT Capabilities      │ 802.11be (WiFi 7) capabilities    │    │
│  │  107    │ EHT Operation         │ 802.11be operation parameters     │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### SSID Information Element

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    SSID INFORMATION ELEMENT                                  │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  Format:                                                                     │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  +──────────+──────────+──────────────────────────────────────────+ │    │
│  │  │ ID = 0   │ Length   │ SSID String                              │ │    │
│  │  │ (1 byte) │ (0-32)   │ (UTF-8 encoded)                          │ │    │
│  │  +──────────+──────────+──────────────────────────────────────────+ │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  Examples:                                                                   │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  Normal SSID:                                                        │    │
│  │  00 0B 4D 79 4E 65 74 77 6F 72 6B 31 32                              │    │
│  │  │  │  └─────────────────────────────┘                               │    │
│  │  │  │  "MyNetwork12" (11 bytes)                                      │    │
│  │  │  └─ Length = 11                                                   │    │
│  │  └─ Element ID = 0 (SSID)                                            │    │
│  │                                                                      │    │
│  │  Hidden SSID (Broadcast SSID disabled):                              │    │
│  │  00 00                                                               │    │
│  │  │  └─ Length = 0 (empty SSID)                                       │    │
│  │  └─ Element ID = 0                                                   │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### TIM (Traffic Indication Map)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    TRAFFIC INDICATION MAP (TIM)                              │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  Purpose:                                                                    │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  The TIM indicates which power-save clients have buffered frames    │    │
│  │  waiting at the AP. Clients wake up to receive beacons and check    │    │
│  │  the TIM to see if they need to retrieve buffered data.             │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  TIM Format:                                                                 │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  +──────────+──────────+──────────+──────────+──────────+──────────+ │    │
│  │  │ ID = 5   │ Length   │ DTIM     │ DTIM     │ Bitmap   │ Partial  │ │    │
│  │  │ (1)      │ (1)      │ Count(1) │ Period(1)│ Ctrl (1) │ Bitmap   │ │    │
│  │  +──────────+──────────+──────────+──────────+──────────+──────────+ │    │
│  │                                                                      │    │
│  │  DTIM Count: Beacons until next DTIM (0 = this is DTIM)              │    │
│  │  DTIM Period: Number of beacons between DTIMs                        │    │
│  │  Bitmap Control: Offset and multicast indication                     │    │
│  │  Partial Virtual Bitmap: Bit map of AIDs with buffered frames        │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  Virtual Bitmap:                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  • Each bit represents one Association ID (AID)                      │    │
│  │  • Bit 0 of first byte = multicast/broadcast buffered                │    │
│  │  • Bit N = 1 means client with AID N has buffered frames             │    │
│  │  • Maximum 2007 AIDs (251 bytes × 8 bits - 1)                        │    │
│  │                                                                      │    │
│  │  Example:                                                            │    │
│  │  Bitmap = 0x06 (binary: 00000110)                                    │    │
│  │  - AID 1 has buffered frames                                         │    │
│  │  - AID 2 has buffered frames                                         │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  Power Save Operation:                                                       │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  Client (Power Save)                              AP                 │    │
│  │       │                                            │                 │    │
│  │       │  [Sleeping]                                │                 │    │
│  │       │                                            │                 │    │
│  │       │◄──────── Beacon (TIM bit=1) ───────────────│                 │    │
│  │       │                                            │                 │    │
│  │       │  [Wakes up, sees TIM bit set]              │                 │    │
│  │       │                                            │                 │    │
│  │       │─────── PS-Poll ───────────────────────────►│                 │    │
│  │       │                                            │                 │    │
│  │       │◄────── Buffered Data ──────────────────────│                 │    │
│  │       │                                            │                 │    │
│  │       │  [Goes back to sleep]                      │                 │    │
│  │       │                                            │                 │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Beacon Interval

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    BEACON INTERVAL                                           │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  Definition:                                                                 │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  Beacon Interval = Time between consecutive beacon transmissions    │    │
│  │                                                                      │    │
│  │  Unit: TU (Time Unit) = 1024 microseconds ≈ 1.024 milliseconds      │    │
│  │                                                                      │    │
│  │  Default: 100 TU = 102.4 ms ≈ ~10 beacons per second                │    │
│  │                                                                      │    │
│  │  Range: 10 - 65535 TU                                                │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  Trade-offs:                                                                 │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  Shorter Interval (e.g., 50 TU):                                     │    │
│  │  ✓ Faster network discovery                                          │    │
│  │  ✓ Better power save timing                                          │    │
│  │  ✗ More airtime consumed by beacons                                  │    │
│  │  ✗ Higher AP CPU usage                                               │    │
│  │                                                                      │    │
│  │  Longer Interval (e.g., 200 TU):                                     │    │
│  │  ✓ Less beacon overhead                                              │    │
│  │  ✓ More airtime for data                                             │    │
│  │  ✗ Slower network discovery                                          │    │
│  │  ✗ Longer power save latency                                         │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  Configuration in hostapd:                                                   │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  # hostapd.conf                                                      │    │
│  │  beacon_int=100                                                      │    │
│  │                                                                      │    │
│  │  # Range: 10-65535 TU                                                │    │
│  │  # Default: 100 TU                                                   │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  Beacon Timing:                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  Time ──────────────────────────────────────────────────────────►   │    │
│  │                                                                      │    │
│  │  │◄── 100 TU ──►│◄── 100 TU ──►│◄── 100 TU ──►│◄── 100 TU ──►│     │    │
│  │  │              │              │              │              │      │    │
│  │  B              B              B              B              B      │    │
│  │  │              │              │              │              │      │    │
│  │  TBTT           TBTT           TBTT           TBTT           TBTT   │    │
│  │                                                                      │    │
│  │  B = Beacon frame                                                    │    │
│  │  TBTT = Target Beacon Transmission Time                              │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### DTIM (Delivery Traffic Indication Message)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    DTIM PERIOD                                               │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  Definition:                                                                 │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  DTIM = Delivery Traffic Indication Message                          │    │
│  │                                                                      │    │
│  │  DTIM Period = Number of beacon intervals between DTIMs              │    │
│  │                                                                      │    │
│  │  Default: 1-3 (typically 2)                                          │    │
│  │                                                                      │    │
│  │  Purpose: Indicates when multicast/broadcast frames will be sent     │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  DTIM Timing:                                                                │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  DTIM Period = 3                                                     │    │
│  │                                                                      │    │
│  │  Beacon:  B1    B2    B3    B4    B5    B6    B7    B8    B9         │    │
│  │           │     │     │     │     │     │     │     │     │          │    │
│  │  DTIM:    D           D           D           D           D          │    │
│  │  Count:   0     2     1     0     2     1     0     2     1          │    │
│  │                                                                      │    │
│  │  D = DTIM beacon (multicast/broadcast sent after this)               │    │
│  │  Count = Beacons until next DTIM (0 = this is DTIM)                  │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  Power Save Impact:                                                          │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  • Clients in power save mode must wake up for DTIM beacons          │    │
│  │  • Higher DTIM period = longer sleep time = better battery life      │    │
│  │  • Higher DTIM period = longer multicast latency                     │    │
│  │                                                                      │    │
│  │  Typical Values:                                                     │    │
│  │  - VoIP/Real-time: DTIM = 1 (low latency)                            │    │
│  │  - General use: DTIM = 2-3                                           │    │
│  │  - IoT/Battery: DTIM = 5-10 (power saving)                           │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  Configuration in hostapd:                                                   │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  # hostapd.conf                                                      │    │
│  │  dtim_period=2                                                       │    │
│  │                                                                      │    │
│  │  # Range: 1-255                                                      │    │
│  │  # Default: 2                                                        │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Hidden SSID

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    HIDDEN SSID (BROADCAST SSID DISABLED)                     │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  What is Hidden SSID?                                                        │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  When "Broadcast SSID" is disabled:                                  │    │
│  │  • Beacon frames contain empty SSID (length = 0)                     │    │
│  │  • Network doesn't appear in normal WiFi scans                       │    │
│  │  • Clients must know SSID to connect                                 │    │
│  │                                                                      │    │
│  │  Note: This is NOT a security feature!                               │    │
│  │  • SSID is still visible in probe requests/responses                 │    │
│  │  • SSID is visible in association frames                             │    │
│  │  • Easy to discover with WiFi sniffing tools                         │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  Beacon Comparison:                                                          │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  Normal Beacon:                                                      │    │
│  │  SSID IE: 00 0B 4D 79 4E 65 74 77 6F 72 6B                           │    │
│  │           │  │  └─────────────────────┘                              │    │
│  │           │  │  "MyNetwork"                                          │    │
│  │           │  └─ Length = 11                                          │    │
│  │           └─ Element ID = 0                                          │    │
│  │                                                                      │    │
│  │  Hidden SSID Beacon:                                                 │    │
│  │  SSID IE: 00 00                                                      │    │
│  │           │  └─ Length = 0 (empty)                                   │    │
│  │           └─ Element ID = 0                                          │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  Client Connection to Hidden SSID:                                           │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  Client                                              AP              │    │
│  │    │                                                  │              │    │
│  │    │◄──────── Beacon (SSID empty) ────────────────────│              │    │
│  │    │                                                  │              │    │
│  │    │  [Client doesn't see network in scan]            │              │    │
│  │    │                                                  │              │    │
│  │    │  [User manually enters SSID "MyNetwork"]         │              │    │
│  │    │                                                  │              │    │
│  │    │─── Probe Request (SSID="MyNetwork") ────────────►│              │    │
│  │    │                                                  │              │    │
│  │    │◄── Probe Response (SSID="MyNetwork") ────────────│              │    │
│  │    │                                                  │              │    │
│  │    │─── Authentication ──────────────────────────────►│              │    │
│  │    │◄── Authentication ───────────────────────────────│              │    │
│  │    │                                                  │              │    │
│  │    │─── Association Request (SSID="MyNetwork") ──────►│              │    │
│  │    │◄── Association Response ─────────────────────────│              │    │
│  │    │                                                  │              │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  Configuration in hostapd:                                                   │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  # hostapd.conf                                                      │    │
│  │  ignore_broadcast_ssid=0   # Normal (SSID visible)                   │    │
│  │  ignore_broadcast_ssid=1   # Hidden (empty SSID)                     │    │
│  │  ignore_broadcast_ssid=2   # Hidden (SSID filled with zeros)         │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### RSN Information Element

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    RSN INFORMATION ELEMENT (WPA2/WPA3)                       │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  The RSN (Robust Security Network) IE advertises security capabilities:     │
│                                                                              │
│  RSN IE Format:                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  +──────────+──────────+──────────+──────────+──────────+──────────+ │    │
│  │  │ ID = 48  │ Length   │ Version  │ Group    │ Pairwise │ Pairwise │ │    │
│  │  │ (1)      │ (1)      │ (2)      │ Cipher(4)│ Count(2) │ Cipher(4)│ │    │
│  │  +──────────+──────────+──────────+──────────+──────────+──────────+ │    │
│  │                                                                      │    │
│  │  +──────────+──────────+──────────+──────────+──────────+           │    │
│  │  │ AKM      │ AKM      │ RSN      │ PMKID    │ PMKID    │ ...       │    │
│  │  │ Count(2) │ Suite(4) │ Caps(2)  │ Count(2) │ List     │           │    │
│  │  +──────────+──────────+──────────+──────────+──────────+           │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  Cipher Suite Selectors:                                                     │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  OUI + Type        │ Cipher                                         │    │
│  │  ────────────      │ ──────                                         │    │
│  │  00-0F-AC-01       │ WEP-40                                         │    │
│  │  00-0F-AC-02       │ TKIP                                           │    │
│  │  00-0F-AC-04       │ CCMP-128 (AES)                                 │    │
│  │  00-0F-AC-05       │ WEP-104                                        │    │
│  │  00-0F-AC-06       │ BIP-CMAC-128 (management frame protection)     │    │
│  │  00-0F-AC-08       │ GCMP-128                                       │    │
│  │  00-0F-AC-09       │ GCMP-256                                       │    │
│  │  00-0F-AC-0A       │ CCMP-256                                       │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  AKM (Authentication and Key Management) Suites:                             │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  OUI + Type        │ AKM Type                                       │    │
│  │  ────────────      │ ────────                                       │    │
│  │  00-0F-AC-01       │ 802.1X (EAP)                                   │    │
│  │  00-0F-AC-02       │ PSK                                            │    │
│  │  00-0F-AC-03       │ FT over 802.1X                                 │    │
│  │  00-0F-AC-04       │ FT over PSK                                    │    │
│  │  00-0F-AC-05       │ 802.1X with SHA-256                            │    │
│  │  00-0F-AC-06       │ PSK with SHA-256                               │    │
│  │  00-0F-AC-08       │ SAE (WPA3-Personal)                            │    │
│  │  00-0F-AC-09       │ FT over SAE                                    │    │
│  │  00-0F-AC-12       │ OWE (Enhanced Open)                            │    │
│  │  00-0F-AC-13       │ 802.1X Suite B 192-bit                         │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  RSN Capabilities:                                                           │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  Bit │ Name                    │ Description                        │    │
│  │  ─── │ ────                    │ ───────────                        │    │
│  │  0   │ Pre-Auth                │ Pre-authentication supported       │    │
│  │  1   │ No Pairwise             │ No pairwise cipher required        │    │
│  │  2-3 │ PTKSA Replay Counter    │ PTK replay counter capability      │    │
│  │  4-5 │ GTKSA Replay Counter    │ GTK replay counter capability      │    │
│  │  6   │ MFP Required            │ Management Frame Protection req    │    │
│  │  7   │ MFP Capable             │ MFP supported                      │    │
│  │  8   │ Joint Multi-band RSNA   │ Multi-band RSNA                    │    │
│  │  9   │ PeerKey Enabled         │ PeerKey handshake supported        │    │
│  │  10  │ SPP A-MSDU Capable      │ SPP A-MSDU supported               │    │
│  │  11  │ SPP A-MSDU Required     │ SPP A-MSDU required                │    │
│  │  12  │ PBAC                    │ Protected Block Ack Agreement      │    │
│  │  13  │ Extended Key ID         │ Extended Key ID for PTK            │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### HT/VHT/HE/EHT Capability Elements

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    WIFI GENERATION CAPABILITY ELEMENTS                       │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  WiFi 4 (802.11n) - HT Capabilities (Element ID 45):                         │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  Field                    │ Size │ Description                      │    │
│  │  ─────                    │ ──── │ ───────────                      │    │
│  │  HT Capabilities Info     │ 2    │ LDPC, channel width, SM PS, etc  │    │
│  │  A-MPDU Parameters        │ 1    │ Max A-MPDU length, spacing       │    │
│  │  Supported MCS Set        │ 16   │ Supported modulation/coding      │    │
│  │  HT Extended Capabilities │ 2    │ PCO, MCS feedback                │    │
│  │  Transmit Beamforming     │ 4    │ Beamforming capabilities         │    │
│  │  ASEL Capabilities        │ 1    │ Antenna selection                │    │
│  │                                                                      │    │
│  │  Key Features:                                                       │    │
│  │  • 20/40 MHz channel width                                           │    │
│  │  • Up to 4 spatial streams                                           │    │
│  │  • Max 600 Mbps (40 MHz, 4SS, SGI)                                   │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  WiFi 5 (802.11ac) - VHT Capabilities (Element ID 191):                      │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  Field                    │ Size │ Description                      │    │
│  │  ─────                    │ ──── │ ───────────                      │    │
│  │  VHT Capabilities Info    │ 4    │ Max MPDU, channel width, etc     │    │
│  │  VHT Supported MCS Set    │ 8    │ Rx/Tx MCS maps                   │    │
│  │                                                                      │    │
│  │  Key Features:                                                       │    │
│  │  • 80/160 MHz channel width                                          │    │
│  │  • Up to 8 spatial streams                                           │    │
│  │  • 256-QAM modulation                                                │    │
│  │  • MU-MIMO (downlink)                                                │    │
│  │  • Max 6.9 Gbps (160 MHz, 8SS)                                       │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  WiFi 6 (802.11ax) - HE Capabilities (Extended Element ID 35):               │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  Field                    │ Size │ Description                      │    │
│  │  ─────                    │ ──── │ ───────────                      │    │
│  │  HE MAC Capabilities      │ 6    │ TWT, OM control, BSR, etc        │    │
│  │  HE PHY Capabilities      │ 11   │ Channel width, LDPC, STBC, etc   │    │
│  │  Tx/Rx HE-MCS NSS Support │ 4-12 │ MCS support per spatial stream   │    │
│  │  PPE Thresholds           │ var  │ Packet extension thresholds      │    │
│  │                                                                      │    │
│  │  Key Features:                                                       │    │
│  │  • OFDMA (multi-user access)                                         │    │
│  │  • MU-MIMO (uplink and downlink)                                     │    │
│  │  • 1024-QAM modulation                                               │    │
│  │  • Target Wake Time (TWT)                                            │    │
│  │  • BSS Coloring                                                      │    │
│  │  • Max 9.6 Gbps                                                      │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  WiFi 7 (802.11be) - EHT Capabilities (Extended Element ID 106):             │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  Field                    │ Size │ Description                      │    │
│  │  ─────                    │ ──── │ ───────────                      │    │
│  │  EHT MAC Capabilities     │ 2    │ EPCS, OM control, etc            │    │
│  │  EHT PHY Capabilities     │ 9    │ 320 MHz, 4K-QAM, etc             │    │
│  │  Supported EHT-MCS NSS    │ var  │ MCS support per bandwidth        │    │
│  │  PPE Thresholds           │ var  │ Packet extension thresholds      │    │
│  │                                                                      │    │
│  │  Key Features:                                                       │    │
│  │  • 320 MHz channel width                                             │    │
│  │  • 4096-QAM modulation                                               │    │
│  │  • Multi-Link Operation (MLO)                                        │    │
│  │  • 16 spatial streams                                                │    │
│  │  • Preamble puncturing                                               │    │
│  │  • Max 46 Gbps                                                       │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Vendor Specific Information Elements

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    VENDOR SPECIFIC ELEMENTS (ID 221)                         │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  Format:                                                                     │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  +──────────+──────────+──────────+──────────+──────────────────+   │    │
│  │  │ ID = 221 │ Length   │ OUI      │ Type     │ Vendor Data      │   │    │
│  │  │ (1)      │ (1)      │ (3)      │ (1)      │ (variable)       │   │    │
│  │  +──────────+──────────+──────────+──────────+──────────────────+   │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  Common Vendor IEs:                                                          │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  OUI          │ Type │ Name                                         │    │
│  │  ───          │ ──── │ ────                                         │    │
│  │  00-50-F2     │ 1    │ WPA (legacy WPA1)                            │    │
│  │  00-50-F2     │ 2    │ WMM/WME (QoS)                                │    │
│  │  00-50-F2     │ 4    │ WPS (WiFi Protected Setup)                   │    │
│  │  00-50-F2     │ 8    │ OWE Transition Mode                          │    │
│  │  50-6F-9A     │ 9    │ P2P (WiFi Direct)                            │    │
│  │  50-6F-9A     │ 16   │ MBO (Multi-Band Operation)                   │    │
│  │  50-6F-9A     │ 28   │ OCV (Operating Channel Validation)           │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  WMM Information Element:                                                    │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  OUI: 00-50-F2, Type: 2, Subtype: 0 (Information) or 1 (Parameter)  │    │
│  │                                                                      │    │
│  │  Access Categories:                                                  │    │
│  │  • AC_BK (Background) - Lowest priority                             │    │
│  │  • AC_BE (Best Effort) - Default                                    │    │
│  │  • AC_VI (Video) - High priority                                    │    │
│  │  • AC_VO (Voice) - Highest priority                                 │    │
│  │                                                                      │    │
│  │  Parameters per AC:                                                  │    │
│  │  • AIFSN (Arbitration Inter-Frame Spacing Number)                   │    │
│  │  • ECWmin/ECWmax (Contention Window)                                │    │
│  │  • TXOP Limit (Transmission Opportunity)                            │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Multiple BSSID (MBSSID)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    MULTIPLE BSSID (MBSSID)                                   │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  Overview:                                                                   │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  MBSSID allows a single beacon to advertise multiple BSSIDs         │    │
│  │  (virtual APs/SSIDs), reducing beacon overhead significantly.       │    │
│  │                                                                      │    │
│  │  Without MBSSID:                                                     │    │
│  │  • Each SSID requires its own beacon                                 │    │
│  │  • 8 SSIDs = 8 beacons per beacon interval                           │    │
│  │  • Significant airtime overhead                                      │    │
│  │                                                                      │    │
│  │  With MBSSID:                                                        │    │
│  │  • Single beacon contains all BSSID information                      │    │
│  │  • 8 SSIDs = 1 beacon per beacon interval                            │    │
│  │  • Much more efficient                                               │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  MBSSID Element (Element ID 71):                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  +──────────+──────────+──────────+──────────────────────────────+  │    │
│  │  │ ID = 71  │ Length   │ Max BSSID│ Nontransmitted BSSID         │  │    │
│  │  │ (1)      │ (1)      │ Indicator│ Profile Subelements          │  │    │
│  │  │          │          │ (1)      │ (variable)                   │  │    │
│  │  +──────────+──────────+──────────+──────────────────────────────+  │    │
│  │                                                                      │    │
│  │  Max BSSID Indicator:                                                │    │
│  │  • Value N means up to 2^N BSSIDs                                    │    │
│  │  • N=3 → up to 8 BSSIDs                                              │    │
│  │  • N=4 → up to 16 BSSIDs                                             │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  Transmitted vs Nontransmitted BSSID:                                        │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  Transmitted BSSID (Reference):                                      │    │
│  │  • The BSSID in the beacon's Address 3 field                         │    │
│  │  • Full information in main beacon body                              │    │
│  │                                                                      │    │
│  │  Nontransmitted BSSIDs:                                              │    │
│  │  • Included in MBSSID element as profiles                            │    │
│  │  • Each profile contains:                                            │    │
│  │    - BSSID Index (offset from transmitted BSSID)                     │    │
│  │    - SSID                                                            │    │
│  │    - Capability Information                                          │    │
│  │    - Security parameters (RSN IE)                                    │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  Configuration in hostapd:                                                   │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  # hostapd.conf (transmitted BSSID)                                  │    │
│  │  interface=wlan0                                                     │    │
│  │  ssid=MainNetwork                                                    │    │
│  │  mbssid=1                                                            │    │
│  │                                                                      │    │
│  │  # Additional BSS (nontransmitted)                                   │    │
│  │  bss=wlan0_1                                                         │    │
│  │  ssid=GuestNetwork                                                   │    │
│  │                                                                      │    │
│  │  bss=wlan0_2                                                         │    │
│  │  ssid=IoTNetwork                                                     │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### FILS Discovery Frame

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    FILS DISCOVERY FRAME                                      │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  Overview:                                                                   │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  FILS (Fast Initial Link Setup) Discovery is a compact frame        │    │
│  │  that can be sent between beacons to speed up network discovery.    │    │
│  │                                                                      │    │
│  │  Benefits:                                                           │    │
│  │  • Smaller than full beacon (faster transmission)                    │    │
│  │  • Sent more frequently than beacons                                 │    │
│  │  • Reduces discovery time for clients                                │    │
│  │  • Particularly useful for 6 GHz band                                │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  FILS Discovery Frame Format:                                                │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  +──────────+──────────+──────────+──────────+──────────+──────────+ │    │
│  │  │ Frame    │ Duration │ DA       │ SA       │ BSSID    │ Seq Ctrl │ │    │
│  │  │ Control  │          │ (Bcast)  │          │          │          │ │    │
│  │  +──────────+──────────+──────────+──────────+──────────+──────────+ │    │
│  │                                                                      │    │
│  │  +──────────+──────────+──────────+──────────+──────────+           │    │
│  │  │ Category │ Action   │ FILS Disc│ Timestamp│ Beacon   │ ...       │    │
│  │  │ (Public) │ (FILS)   │ Info     │          │ Interval │           │    │
│  │  +──────────+──────────+──────────+──────────+──────────+           │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  FILS Discovery Information:                                                 │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  Field                    │ Description                             │    │
│  │  ─────                    │ ───────────                             │    │
│  │  FILS Discovery Info      │ Capability and SSID length              │    │
│  │  Timestamp                │ TSF timer value                         │    │
│  │  Beacon Interval          │ Time between beacons                    │    │
│  │  Short SSID               │ 4-byte hash of SSID (optional)          │    │
│  │  Full SSID                │ Complete SSID (optional)                │    │
│  │  Access Network Options   │ Network type, internet access           │    │
│  │  Primary Channel          │ Operating channel                       │    │
│  │  RSN Info                 │ Security parameters                     │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  6 GHz Discovery:                                                            │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  In 6 GHz band, FILS Discovery is essential because:                 │    │
│  │  • Passive scanning is not allowed on all channels                   │    │
│  │  • Active probing requires knowing the SSID                          │    │
│  │  • FILS Discovery provides fast network discovery                    │    │
│  │                                                                      │    │
│  │  Unsolicited Probe Response (UPR):                                   │    │
│  │  • Alternative to FILS Discovery                                     │    │
│  │  • Full probe response sent periodically                             │    │
│  │  • Larger but contains complete information                          │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  Configuration in hostapd:                                                   │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  # hostapd.conf                                                      │    │
│  │  fils_discovery_min_interval=20   # Minimum interval (TUs)           │    │
│  │  fils_discovery_max_interval=20   # Maximum interval (TUs)           │    │
│  │                                                                      │    │
│  │  # Or use Unsolicited Probe Response                                 │    │
│  │  unsol_bcast_probe_resp_interval=20                                  │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Beacon Implementation

### Source Code Files

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    BEACON IMPLEMENTATION FILES                               │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  Core Beacon Files:                                                          │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  File                              │ Purpose                        │    │
│  │  ────                              │ ───────                        │    │
│  │  src/ap/beacon.c                   │ Beacon frame construction      │    │
│  │  src/ap/beacon.h                   │ Beacon function declarations   │    │
│  │  src/ap/ieee802_11.c               │ 802.11 frame handling          │    │
│  │  src/ap/ieee802_11.h               │ 802.11 definitions             │    │
│  │  src/ap/hostapd.c                  │ Main AP daemon                 │    │
│  │  src/ap/hostapd.h                  │ AP data structures             │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  Key Functions in beacon.c:                                                  │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  Function                          │ Purpose                        │    │
│  │  ────────                          │ ───────                        │    │
│  │  ieee802_11_build_ap_params()      │ Build AP parameters            │    │
│  │  ieee802_11_set_beacon()           │ Set beacon in driver           │    │
│  │  ieee802_11_set_beacons()          │ Update all interface beacons   │    │
│  │  hostapd_build_beacon_data()       │ Construct beacon frame data    │    │
│  │  hostapd_gen_probe_resp()          │ Generate probe response        │    │
│  │  hostapd_eid_*()                   │ Add information elements       │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  Information Element Functions:                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  Function                          │ Element                        │    │
│  │  ────────                          │ ───────                        │    │
│  │  hostapd_eid_ssid()                │ SSID (ID 0)                    │    │
│  │  hostapd_eid_supp_rates()          │ Supported Rates (ID 1)         │    │
│  │  hostapd_eid_ds_params()           │ DS Parameter Set (ID 3)        │    │
│  │  hostapd_eid_country()             │ Country (ID 7)                 │    │
│  │  hostapd_eid_erp_info()            │ ERP Information (ID 42)        │    │
│  │  hostapd_eid_ht_capabilities()     │ HT Capabilities (ID 45)        │    │
│  │  hostapd_eid_ht_operation()        │ HT Operation (ID 61)           │    │
│  │  hostapd_eid_vht_capabilities()    │ VHT Capabilities (ID 191)      │    │
│  │  hostapd_eid_vht_operation()       │ VHT Operation (ID 192)         │    │
│  │  hostapd_eid_he_capab()            │ HE Capabilities (Ext ID 35)    │    │
│  │  hostapd_eid_he_operation()        │ HE Operation (Ext ID 36)       │    │
│  │  hostapd_eid_eht_capab()           │ EHT Capabilities (Ext ID 106)  │    │
│  │  hostapd_eid_eht_operation()       │ EHT Operation (Ext ID 107)     │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Beacon Update Triggers

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    BEACON UPDATE TRIGGERS                                    │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  Events that trigger beacon updates:                                         │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  Event                             │ Beacon Change                  │    │
│  │  ─────                             │ ─────────────                  │    │
│  │  Client associates                 │ TIM bitmap updated             │    │
│  │  Client disassociates              │ TIM bitmap updated             │    │
│  │  Buffered frame for PS client      │ TIM bit set                    │    │
│  │  PS client retrieves frames        │ TIM bit cleared                │    │
│  │  Channel switch                    │ CSA element added              │    │
│  │  Security mode change              │ RSN IE updated                 │    │
│  │  SSID change                       │ SSID IE updated                │    │
│  │  HT/VHT/HE mode change             │ Capability IEs updated         │    │
│  │  WMM parameter change              │ WMM IE updated                 │    │
│  │  Quiet period                      │ Quiet element added            │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  Beacon Update Flow:                                                         │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  Configuration Change                                                │    │
│  │         │                                                            │    │
│  │         ▼                                                            │    │
│  │  hostapd_reload_config()                                             │    │
│  │         │                                                            │    │
│  │         ▼                                                            │    │
│  │  ieee802_11_set_beacons()                                            │    │
│  │         │                                                            │    │
│  │         ▼                                                            │    │
│  │  hostapd_build_beacon_data()                                         │    │
│  │         │                                                            │    │
│  │         ▼                                                            │    │
│  │  hostapd_drv_set_ap()                                                │    │
│  │         │                                                            │    │
│  │         ▼                                                            │    │
│  │  Driver updates beacon template                                      │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Configuration Examples

### Complete hostapd Beacon Configuration

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    HOSTAPD BEACON CONFIGURATION                              │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  Basic Beacon Settings:                                                      │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  # /etc/hostapd/hostapd.conf                                         │    │
│  │                                                                      │    │
│  │  # Interface and driver                                              │    │
│  │  interface=wlan0                                                     │    │
│  │  driver=nl80211                                                      │    │
│  │                                                                      │    │
│  │  # SSID (appears in beacon)                                          │    │
│  │  ssid=MyNetwork                                                      │    │
│  │                                                                      │    │
│  │  # Beacon interval (TUs, default 100)                                │    │
│  │  beacon_int=100                                                      │    │
│  │                                                                      │    │
│  │  # DTIM period (beacons between DTIMs, default 2)                    │    │
│  │  dtim_period=2                                                       │    │
│  │                                                                      │    │
│  │  # Hidden SSID (0=visible, 1=empty, 2=zeros)                         │    │
│  │  ignore_broadcast_ssid=0                                             │    │
│  │                                                                      │    │
│  │  # Country code (required for 5 GHz)                                 │    │
│  │  country_code=US                                                     │    │
│  │  ieee80211d=1                                                        │    │
│  │                                                                      │    │
│  │  # Channel                                                           │    │
│  │  channel=36                                                          │    │
│  │  hw_mode=a                                                           │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  WiFi 6 (802.11ax) Beacon Settings:                                          │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  # Enable 802.11ax (WiFi 6)                                          │    │
│  │  ieee80211ax=1                                                       │    │
│  │                                                                      │    │
│  │  # HE capabilities in beacon                                         │    │
│  │  he_su_beamformer=1                                                  │    │
│  │  he_su_beamformee=1                                                  │    │
│  │  he_mu_beamformer=1                                                  │    │
│  │                                                                      │    │
│  │  # BSS Coloring (advertised in beacon)                               │    │
│  │  he_bss_color=42                                                     │    │
│  │                                                                      │    │
│  │  # OFDMA                                                             │    │
│  │  he_default_pe_duration=4                                            │    │
│  │  he_rts_threshold=1023                                               │    │
│  │                                                                      │    │
│  │  # 6 GHz specific (FILS Discovery)                                   │    │
│  │  fils_discovery_min_interval=20                                      │    │
│  │  fils_discovery_max_interval=20                                      │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Testing

### Beacon Tests

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    BEACON RELATED TESTS                                      │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  Test Files:                                                                 │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  File                              │ Description                    │    │
│  │  ────                              │ ───────────                    │    │
│  │  ValidateBeaconTest.py             │ Beacon frame validation        │    │
│  │  BeaconReportTest.py               │ 802.11k beacon reports         │    │
│  │  BeaconRateTest.py                 │ Beacon rate configuration      │    │
│  │  HiddenSsidTest.py                 │ Hidden SSID functionality      │    │
│  │  MbssidTest.py                     │ Multiple BSSID testing         │    │
│  │  FilsDiscoveryTest.py              │ FILS discovery frames          │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  BeaconReportTest.py:                                                        │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  Tests 802.11k Radio Resource Management beacon reports:             │    │
│  │                                                                      │    │
│  │  • test_beacon_report_passive - Passive beacon scanning              │    │
│  │  • test_beacon_report_active - Active beacon scanning                │    │
│  │  • test_beacon_report_table - Beacon table mode                      │    │
│  │  • test_beacon_report_ssid - SSID-specific reports                   │    │
│  │  • test_beacon_report_bssid - BSSID-specific reports                 │    │
│  │                                                                      │    │
│  │  Validates:                                                          │    │
│  │  • Beacon report request frames                                      │    │
│  │  • Beacon report response frames                                     │    │
│  │  • Report contents (BSSID, SSID, channel, RCPI, RSNI)                │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### DHCP Tests

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    DHCP RELATED TESTS                                        │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  Test Files:                                                                 │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  File                              │ Description                    │    │
│  │  ────                              │ ───────────                    │    │
│  │  DhcpFPACLTest.py                  │ DHCP fingerprint ACL           │    │
│  │  ApDhcpInfoTestMwm.py              │ DHCP info in MWM mode          │    │
│  │  ApDhcpParametersValidationTest.py │ DHCP parameter validation      │    │
│  │  DhcpRelayTest.py                  │ DHCP relay functionality       │    │
│  │  DhcpOption82Test.py               │ Option 82 insertion            │    │
│  │  DhcpServerTest.py                 │ Local DHCP server              │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  DhcpFPACLTest.py:                                                           │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  Tests DHCP Fingerprinting Based ACL:                                │    │
│  │                                                                      │    │
│  │  • test_dhcp_fp_allow - Allow identified devices                     │    │
│  │  • test_dhcp_fp_deny - Deny identified devices                       │    │
│  │  • test_dhcp_fp_unidentified_allow - Allow unknown devices           │    │
│  │  • test_dhcp_fp_unidentified_deny - Deny unknown devices             │    │
│  │                                                                      │    │
│  │  Validates:                                                          │    │
│  │  • Device identification via DHCP Option 55                          │    │
│  │  • ACL enforcement based on device type                              │    │
│  │  • Unidentified client handling                                      │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  Running Tests:                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  # Run beacon tests                                                  │    │
│  │  python -m pytest BeaconReportTest.py -v                             │    │
│  │                                                                      │    │
│  │  # Run DHCP tests                                                    │    │
│  │  python -m pytest DhcpFPACLTest.py -v                                │    │
│  │                                                                      │    │
│  │  # Run all related tests                                             │    │
│  │  python -m pytest *Beacon*.py *Dhcp*.py -v                           │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Troubleshooting

### DHCP Troubleshooting

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    DHCP TROUBLESHOOTING                                      │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  Common Issues:                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  Issue                             │ Possible Cause                 │    │
│  │  ─────                             │ ──────────────                 │    │
│  │  No IP address                     │ DHCP server unreachable        │    │
│  │  169.254.x.x address               │ DHCP timeout (APIPA)           │    │
│  │  Wrong subnet                      │ DHCP relay misconfigured       │    │
│  │  Duplicate IP                      │ DHCP pool exhausted            │    │
│  │  Slow DHCP                         │ Server overloaded              │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  Diagnostic Commands:                                                        │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  # Check DHCP server status                                          │    │
│  │  systemctl status udhcpd                                             │    │
│  │                                                                      │    │
│  │  # View DHCP leases                                                  │    │
│  │  cat /var/lib/misc/udhcpd.leases                                     │    │
│  │                                                                      │    │
│  │  # Capture DHCP traffic                                              │    │
│  │  tcpdump -i eth0 port 67 or port 68 -vvv                             │    │
│  │                                                                      │    │
│  │  # Test DHCP client                                                  │    │
│  │  dhclient -v wlan0                                                   │    │
│  │                                                                      │    │
│  │  # Check relay configuration                                         │    │
│  │  cat /etc/dhcp/dhcrelay.conf                                         │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  DHCP Packet Analysis:                                                       │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  # Wireshark filter for DHCP                                         │    │
│  │  bootp                                                               │    │
│  │                                                                      │    │
│  │  # Filter by message type                                            │    │
│  │  bootp.option.dhcp == 1    # DISCOVER                                │    │
│  │  bootp.option.dhcp == 2    # OFFER                                   │    │
│  │  bootp.option.dhcp == 3    # REQUEST                                 │    │
│  │  bootp.option.dhcp == 5    # ACK                                     │    │
│  │                                                                      │    │
│  │  # Filter by client MAC                                              │    │
│  │  bootp.hw.mac_addr == aa:bb:cc:dd:ee:ff                              │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Beacon Troubleshooting

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    BEACON TROUBLESHOOTING                                    │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  Common Issues:                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  Issue                             │ Possible Cause                 │    │
│  │  ─────                             │ ──────────────                 │    │
│  │  Network not visible               │ Hidden SSID enabled            │    │
│  │  Slow network discovery            │ Long beacon interval           │    │
│  │  Client can't connect              │ Capability mismatch            │    │
│  │  Security mismatch                 │ RSN IE incorrect               │    │
│  │  Power save issues                 │ DTIM period too long           │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  Diagnostic Commands:                                                        │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  # Check hostapd status                                              │    │
│  │  hostapd_cli status                                                  │    │
│  │                                                                      │    │
│  │  # View beacon configuration                                         │    │
│  │  hostapd_cli get_config                                              │    │
│  │                                                                      │    │
│  │  # Scan for beacons                                                  │    │
│  │  iw dev wlan0 scan                                                   │    │
│  │                                                                      │    │
│  │  # Capture beacon frames                                             │    │
│  │  tcpdump -i wlan0 -e type mgt subtype beacon                         │    │
│  │                                                                      │    │
│  │  # Check beacon interval                                             │    │
│  │  iw dev wlan0 info | grep beacon                                     │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  Beacon Frame Analysis:                                                      │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  # Wireshark filter for beacons                                      │    │
│  │  wlan.fc.type_subtype == 0x08                                        │    │
│  │                                                                      │    │
│  │  # Filter by SSID                                                    │    │
│  │  wlan.ssid == "MyNetwork"                                            │    │
│  │                                                                      │    │
│  │  # Filter by BSSID                                                   │    │
│  │  wlan.bssid == aa:bb:cc:dd:ee:ff                                     │    │
│  │                                                                      │    │
│  │  # Show beacon interval                                              │    │
│  │  wlan.fixed.beacon                                                   │    │
│  │                                                                      │    │
│  │  # Show capability info                                              │    │
│  │  wlan.fixed.capabilities                                             │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## DHCP and Beacon Relationship

### Connection Flow

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    DHCP AND BEACON IN CONNECTION FLOW                        │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  Complete Connection Sequence:                                               │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  ┌─────────┐                                    ┌─────────┐          │    │
│  │  │ Client  │                                    │   AP    │          │    │
│  │  └────┬────┘                                    └────┬────┘          │    │
│  │       │                                              │               │    │
│  │       │  ◄──────────── Beacon ───────────────────────│               │    │
│  │       │  (SSID, Capabilities, Security)              │               │    │
│  │       │                                              │               │    │
│  │       │  ─────────── Probe Request ─────────────────►│               │    │
│  │       │                                              │               │    │
│  │       │  ◄────────── Probe Response ─────────────────│               │    │
│  │       │                                              │               │    │
│  │       │  ─────────── Authentication ────────────────►│               │    │
│  │       │  ◄────────── Authentication ─────────────────│               │    │
│  │       │                                              │               │    │
│  │       │  ─────────── Association Req ───────────────►│               │    │
│  │       │  ◄────────── Association Resp ───────────────│               │    │
│  │       │                                              │               │    │
│  │       │  ◄──────────── 4-Way Handshake ─────────────►│               │    │
│  │       │  (EAPOL Key Exchange)                        │               │    │
│  │       │                                              │               │    │
│  │       │  ════════════ CONNECTED ═════════════════════│               │    │
│  │       │                                              │               │    │
│  │       │  ─────────── DHCP DISCOVER ─────────────────►│               │    │
│  │       │  (Broadcast, looking for DHCP server)        │               │    │
│  │       │                                              │               │    │
│  │       │  ◄────────── DHCP OFFER ─────────────────────│               │    │
│  │       │  (IP address offer)                          │               │    │
│  │       │                                              │               │    │
│  │       │  ─────────── DHCP REQUEST ──────────────────►│               │    │
│  │       │  (Accept offered IP)                         │               │    │
│  │       │                                              │               │    │
│  │       │  ◄────────── DHCP ACK ───────────────────────│               │    │
│  │       │  (IP address confirmed)                      │               │    │
│  │       │                                              │               │    │
│  │       │  ════════════ FULLY OPERATIONAL ═════════════│               │    │
│  │       │                                              │               │    │
│  │  └────┴────┘                                    └────┴────┘          │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  Timeline:                                                                   │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  Phase              │ Duration      │ Protocol                      │    │
│  │  ─────              │ ────────      │ ────────                      │    │
│  │  Discovery          │ 0-200ms       │ Beacon/Probe                  │    │
│  │  Authentication     │ 10-50ms       │ 802.11 Auth                   │    │
│  │  Association        │ 10-50ms       │ 802.11 Assoc                  │    │
│  │  Key Exchange       │ 50-200ms      │ EAPOL (4-Way)                 │    │
│  │  IP Assignment      │ 100-500ms     │ DHCP (DORA)                   │    │
│  │  ─────────────────────────────────────────────────────────────────  │    │
│  │  Total              │ 170-1000ms    │ Complete connection           │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Beacon Information Used by DHCP

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    BEACON INFORMATION AFFECTING DHCP                         │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  VLAN Assignment:                                                            │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  Beacon advertises SSID → SSID maps to VLAN → VLAN determines        │    │
│  │  which DHCP scope the client receives IP from                        │    │
│  │                                                                      │    │
│  │  Example:                                                            │    │
│  │  • SSID "Corporate" → VLAN 10 → DHCP scope 10.10.0.0/24              │    │
│  │  • SSID "Guest" → VLAN 20 → DHCP scope 10.20.0.0/24                  │    │
│  │  • SSID "IoT" → VLAN 30 → DHCP scope 10.30.0.0/24                    │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  DHCP Option 82 (Relay Agent Information):                                   │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  AP inserts information from beacon/association into DHCP:           │    │
│  │                                                                      │    │
│  │  • Circuit ID: AP MAC + SSID name                                    │    │
│  │  • Remote ID: Client MAC                                             │    │
│  │                                                                      │    │
│  │  DHCP server can use this to:                                        │    │
│  │  • Assign IP based on SSID                                           │    │
│  │  • Track which AP client connected through                           │    │
│  │  • Apply different policies per SSID                                 │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## References

### DHCP Standards

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    DHCP STANDARDS AND RFCS                                   │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  Core DHCP RFCs:                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  RFC         │ Title                                                │    │
│  │  ───         │ ─────                                                │    │
│  │  RFC 2131    │ Dynamic Host Configuration Protocol                  │    │
│  │  RFC 2132    │ DHCP Options and BOOTP Vendor Extensions             │    │
│  │  RFC 3046    │ DHCP Relay Agent Information Option (Option 82)      │    │
│  │  RFC 3118    │ Authentication for DHCP Messages                     │    │
│  │  RFC 3203    │ DHCP Reconfigure Extension                           │    │
│  │  RFC 3315    │ DHCPv6 (obsoleted by RFC 8415)                       │    │
│  │  RFC 4361    │ Node-specific Client Identifiers for DHCPv4          │    │
│  │  RFC 4702    │ The DHCP Client FQDN Option                          │    │
│  │  RFC 8415    │ DHCPv6 (current)                                     │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  DHCP Option RFCs:                                                           │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  RFC         │ Option                                               │    │
│  │  ───         │ ──────                                               │    │
│  │  RFC 2241    │ DHCP Options for Novell Directory Services           │    │
│  │  RFC 2242    │ NetWare/IP Domain Name and Information               │    │
│  │  RFC 3004    │ User Class Option                                    │    │
│  │  RFC 3011    │ IPv4 Subnet Selection Option                         │    │
│  │  RFC 3442    │ Classless Static Route Option                        │    │
│  │  RFC 3925    │ Vendor-Identifying Vendor Options                    │    │
│  │  RFC 4578    │ DHCP Options for PXE                                 │    │
│  │  RFC 5859    │ TFTP Server Address Option                           │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Beacon/802.11 Standards

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    802.11 STANDARDS                                          │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  Core 802.11 Standards:                                                      │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  Standard        │ Description                                      │    │
│  │  ────────        │ ───────────                                      │    │
│  │  IEEE 802.11     │ Base standard (1997)                             │    │
│  │  IEEE 802.11a    │ 5 GHz OFDM (1999)                                │    │
│  │  IEEE 802.11b    │ 2.4 GHz DSSS (1999)                              │    │
│  │  IEEE 802.11g    │ 2.4 GHz OFDM (2003)                              │    │
│  │  IEEE 802.11n    │ HT - WiFi 4 (2009)                               │    │
│  │  IEEE 802.11ac   │ VHT - WiFi 5 (2013)                              │    │
│  │  IEEE 802.11ax   │ HE - WiFi 6/6E (2021)                            │    │
│  │  IEEE 802.11be   │ EHT - WiFi 7 (2024)                              │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  Security Standards:                                                         │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  Standard        │ Description                                      │    │
│  │  ────────        │ ───────────                                      │    │
│  │  IEEE 802.11i    │ RSN (WPA2) security                              │    │
│  │  IEEE 802.11w    │ Protected Management Frames (PMF)                │    │
│  │  WPA3            │ SAE, OWE, Suite B (Wi-Fi Alliance)               │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  Management Frame Standards:                                                 │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  Standard        │ Description                                      │    │
│  │  ────────        │ ───────────                                      │    │
│  │  IEEE 802.11k    │ Radio Resource Management (beacon reports)       │    │
│  │  IEEE 802.11r    │ Fast BSS Transition                              │    │
│  │  IEEE 802.11v    │ Wireless Network Management                      │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Glossary

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    GLOSSARY                                                  │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  DHCP Terms:                                                                 │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  Term            │ Definition                                       │    │
│  │  ────            │ ──────────                                       │    │
│  │  DHCP            │ Dynamic Host Configuration Protocol              │    │
│  │  DORA            │ Discover, Offer, Request, Acknowledge            │    │
│  │  Lease           │ Time period IP address is valid                  │    │
│  │  Scope           │ Range of IP addresses for assignment             │    │
│  │  Relay           │ Agent forwarding DHCP between subnets            │    │
│  │  Option 82       │ Relay Agent Information Option                   │    │
│  │  APIPA           │ Automatic Private IP Addressing (169.254.x.x)    │    │
│  │  DUID            │ DHCP Unique Identifier (DHCPv6)                  │    │
│  │  Fingerprint     │ Device identification via Option 55              │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  Beacon Terms:                                                               │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  Term            │ Definition                                       │    │
│  │  ────            │ ──────────                                       │    │
│  │  Beacon          │ Periodic broadcast frame from AP                 │    │
│  │  TU              │ Time Unit (1024 microseconds)                    │    │
│  │  Beacon Interval │ Time between beacons (default 100 TU)            │    │
│  │  DTIM            │ Delivery Traffic Indication Message              │    │
│  │  TIM             │ Traffic Indication Map                           │    │
│  │  SSID            │ Service Set Identifier (network name)            │    │
│  │  BSSID           │ Basic Service Set Identifier (AP MAC)            │    │
│  │  RSN IE          │ Robust Security Network Information Element      │    │
│  │  Capability      │ 16-bit field indicating AP features              │    │
│  │  IE              │ Information Element                              │    │
│  │  MBSSID          │ Multiple BSSID (multiple SSIDs in one beacon)    │    │
│  │  FILS            │ Fast Initial Link Setup                          │    │
│  │  HT              │ High Throughput (802.11n/WiFi 4)                  │    │
│  │  VHT             │ Very High Throughput (802.11ac/WiFi 5)           │    │
│  │  HE              │ High Efficiency (802.11ax/WiFi 6)                │    │
│  │  EHT             │ Extremely High Throughput (802.11be/WiFi 7)      │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Document Summary

This document provides comprehensive coverage of two essential WiFi networking components:

**DHCP (Dynamic Host Configuration Protocol)**:
- Protocol overview and DORA process
- Message types and packet structure
- DHCP options including fingerprinting (Option 55) and relay (Option 82)
- DHCPv6 for IPv6 networks
- Server configuration with udhcpd

**Beacon Frames**:
- Frame structure and timing
- Information Elements (SSID, TIM, RSN, HT/VHT/HE/EHT capabilities)
- Power save operation with DTIM
- Hidden SSID configuration
- MBSSID for multiple virtual APs
- FILS Discovery for 6 GHz
- Vendor-specific elements (WPA, WMM, WPS)

**Relationship**:
- Complete connection flow from beacon discovery to IP assignment
- VLAN-based DHCP scope selection
- Option 82 integration with SSID information

---

*Document generated for Arista Access Point WiFi firmware documentation.*
*Last updated: 2026-01-08*

