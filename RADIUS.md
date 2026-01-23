# RADIUS (Remote Authentication Dial-In User Service)

This document provides a comprehensive overview of RADIUS implementation and testing in this repository.

## Overview

RADIUS is a networking protocol that provides centralized Authentication, Authorization, and Accounting (AAA) for users connecting to wireless networks. It enables:

- **Authentication**: Verify user credentials (username/password, certificates)
- **Authorization**: Determine user access rights (VLAN, bandwidth, session limits)
- **Accounting**: Track user sessions (start/stop times, data usage)

## Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         RADIUS Communication Flow                            │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌──────────────┐     ┌──────────────┐     ┌──────────────────────────────┐ │
│  │   Wireless   │     │     AP       │     │       RADIUS Server          │ │
│  │    Client    │     │  (NAS/NAS)   │     │    (Authentication Server)   │ │
│  └──────┬───────┘     └──────┬───────┘     └──────────────┬───────────────┘ │
│         │                    │                            │                  │
│         │  802.1X/EAPOL      │      RADIUS (UDP/TLS)      │                  │
│         │ ─────────────────► │ ─────────────────────────► │                  │
│         │                    │                            │                  │
│         │  EAP-Request       │    Access-Request          │                  │
│         │ ◄───────────────── │    (User-Name, NAS-ID,     │                  │
│         │                    │     EAP-Message)           │                  │
│         │  EAP-Response      │                            │                  │
│         │ ─────────────────► │                            │                  │
│         │                    │    Access-Challenge        │                  │
│         │                    │ ◄───────────────────────── │                  │
│         │      ...           │           ...              │                  │
│         │                    │                            │                  │
│         │  EAP-Success       │    Access-Accept           │                  │
│         │ ◄───────────────── │    (VLAN, PMK, Attributes) │                  │
│         │                    │ ◄───────────────────────── │                  │
│         │                    │                            │                  │
│         │  ═══ Connected ═══ │                            │                  │
│         │                    │                            │                  │
│         │                    │    Accounting-Request      │                  │
│         │                    │    (Start/Interim/Stop)    │                  │
│         │                    │ ─────────────────────────► │                  │
│         │                    │                            │                  │
│         │                    │    Accounting-Response     │                  │
│         │                    │ ◄───────────────────────── │                  │
│                                                                              │
└──────────────────────────────────────────────────────────────────────────────┘
```

## RADIUS Packet Types

### Authentication

| Code | Name | Direction | Description |
|------|------|-----------|-------------|
| 1 | Access-Request | AP → RADIUS | Request user authentication |
| 2 | Access-Accept | RADIUS → AP | Authentication successful |
| 3 | Access-Reject | RADIUS → AP | Authentication failed |
| 11 | Access-Challenge | RADIUS → AP | Request additional info (EAP) |

### Accounting

| Code | Name | Direction | Description |
|------|------|-----------|-------------|
| 4 | Accounting-Request | AP → RADIUS | Start/Interim/Stop session |
| 5 | Accounting-Response | RADIUS → AP | Acknowledge accounting |

### Dynamic Authorization (DAS/CoA)

| Code | Name | Direction | Description |
|------|------|-----------|-------------|
| 40 | Disconnect-Request | RADIUS → AP | Disconnect a client |
| 41 | Disconnect-ACK | AP → RADIUS | Disconnect successful |
| 42 | Disconnect-NAK | AP → RADIUS | Disconnect failed |
| 43 | CoA-Request | RADIUS → AP | Change of Authorization |
| 44 | CoA-ACK | AP → RADIUS | CoA successful |
| 45 | CoA-NAK | AP → RADIUS | CoA failed |

## Common RADIUS Attributes

| Attribute | ID | Description |
|-----------|-----|-------------|
| User-Name | 1 | Client username/identity |
| User-Password | 2 | Client password (encrypted) |
| NAS-IP-Address | 4 | AP IP address |
| NAS-Port | 5 | Physical port number |
| Service-Type | 6 | Type of service requested |
| Framed-IP-Address | 8 | Client IP address |
| Called-Station-Id | 30 | AP MAC + SSID |
| Calling-Station-Id | 31 | Client MAC address |
| NAS-Identifier | 32 | Unique AP identifier |
| Acct-Status-Type | 40 | Start(1)/Stop(2)/Interim(3) |
| Acct-Session-Id | 44 | Unique session identifier |
| Acct-Session-Time | 46 | Session duration (seconds) |
| Acct-Input-Octets | 42 | Bytes received from client |
| Acct-Output-Octets | 43 | Bytes sent to client |
| Event-Timestamp | 55 | Time of event |
| Tunnel-Type | 64 | VLAN tunneling type |
| Tunnel-Medium-Type | 65 | IEEE-802 for VLANs |
| Tunnel-Private-Group-Id | 81 | VLAN ID assignment |
| EAP-Message | 79 | EAP message encapsulation |
| Message-Authenticator | 80 | Message integrity check |

## Vendor-Specific Attributes (VSA)

### Arista/Airtight VSA (Vendor ID: Custom)

| Attribute | Description |
|-----------|-------------|
| Wibhu-User-BW-UL | Upload bandwidth limit (kbps) |
| Wibhu-User-BW-DL | Download bandwidth limit (kbps) |
| Airtight-Download-Limit | Download bandwidth limit |
| Airtight-Upload-Limit | Upload bandwidth limit |

### Microsoft VSA (Vendor ID: 311)

| Attribute | ID | Description |
|-----------|-----|-------------|
| MS-MPPE-Send-Key | 16 | MSK for encryption (send) |
| MS-MPPE-Recv-Key | 17 | MSK for encryption (receive) |

### Cisco VSA (Vendor ID: 9)

| Attribute | Description |
|-----------|-------------|
| Cisco-AV-Pair | Generic attribute-value pair |

## Authentication Modes

### 802.1X (WPA-Enterprise)

Uses EAP (Extensible Authentication Protocol):
- **EAP-TLS**: Certificate-based mutual authentication
- **EAP-TTLS**: Tunneled TLS with inner authentication
- **EAP-PEAP**: Protected EAP with MSCHAPv2/GTC
- **EAP-SIM/AKA/AKA'**: SIM card-based authentication

### MAC Authentication (MAC-Auth)

Authenticates using client MAC address:
- MAC sent as username and password
- Formats: no delimiter, colon, hyphen
- Used for non-802.1X capable devices

## Server Configuration

### Authentication Server

```
# hostapd configuration
auth_server_addr=192.168.1.100
auth_server_port=1812
auth_server_shared_secret=RadiusSecret
```

### Accounting Server

```
# hostapd configuration
acct_server_addr=192.168.1.100
acct_server_port=1813
acct_server_shared_secret=RadiusSecret
```

### Multiple Server Support (Failover)

Up to 4 RADIUS servers can be configured for redundancy:

```
# Primary Authentication Server
RADIUS_SERVER_1_HOST=radius1.example.com
RADIUS_SERVER_1_PORT=1812
RADIUS_SERVER_1_SECRET=secret1

# Secondary Authentication Server (failover)
RADIUS_SERVER_2_HOST=radius2.example.com
RADIUS_SERVER_2_PORT=1812
RADIUS_SERVER_2_SECRET=secret2
```

## RADIUS Accounting

### Accounting Status Types

| Type | Value | Description |
|------|-------|-------------|
| Start | 1 | Session started |
| Stop | 2 | Session ended |
| Interim-Update | 3 | Periodic update during session |
| Accounting-On | 7 | AP started (all sessions) |
| Accounting-Off | 8 | AP stopped (all sessions) |

### Accounting Flow

```
Client Connects
      │
      ▼
┌─────────────────┐
│ Accounting-Start│ ──► Session-Id, User-Name, NAS-ID, Called/Calling-Station-Id
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Interim-Update  │ ──► Session-Time, Input/Output-Octets (periodic)
└────────┬────────┘
         │ (repeat at configured interval)
         ▼
┌─────────────────┐
│ Accounting-Stop │ ──► Final Session-Time, Total Input/Output-Octets, Terminate-Cause
└─────────────────┘
```

### Interim Interval

Configurable periodic updates during active sessions:
- Default: 600 seconds (10 minutes)
- Can be updated dynamically via CoA

## Dynamic Authorization (CoA/DM)

### Change of Authorization (CoA)

Allows RADIUS server to dynamically modify active sessions:

**Supported CoA Actions:**
- Update bandwidth limits (upload/download)
- Change VLAN assignment
- Update session timeout
- Modify interim accounting interval

### Disconnect Messages (DM)

Allows RADIUS server to terminate active sessions:

```
RADIUS Server                           AP
     │                                   │
     │  Disconnect-Request               │
     │  (Session-Id, User-Name)          │
     │ ─────────────────────────────────►│
     │                                   │
     │  Disconnect-ACK                   │
     │ ◄─────────────────────────────────│
     │                                   │
     │                          Client Disconnected
```

### CoA Cluster

Multiple CoA server IPs can be configured for redundancy:

```
coa_cluster_ips=192.168.1.100,192.168.1.101,192.168.1.102
```

## RadSec (RADIUS over TLS)

RadSec provides secure RADIUS communication using TLS encryption.

### Architecture

```
┌──────────────┐     ┌──────────────────┐     ┌──────────────────┐
│      AP      │     │   radsecproxy    │     │  RADIUS Server   │
│   (hostapd)  │────►│   (TLS Client)   │────►│   (TLS Server)   │
└──────────────┘     └──────────────────┘     └──────────────────┘
     localhost:1812        TCP/2083              TCP/2083
```

### Features

- **TLS Encryption**: All RADIUS traffic encrypted
- **Certificate-Based Auth**: Mutual TLS authentication
- **CRL Revocation**: Certificate revocation list support
- **Multiple Servers**: Up to 4 RadSec servers per SSID
- **Failover**: Automatic failover to backup servers

### Configuration

```
# RadSec server configuration
radsec_server_addr=radsec.example.com
radsec_server_port=2083
radsec_ca_cert=/etc/certs/ca.pem
radsec_client_cert=/etc/certs/client.pem
radsec_client_key=/etc/certs/client.key
```

## RADIUS Pooling

Load balancing across multiple RADIUS servers:

### Features

- **Randomized Order**: Servers selected randomly for load distribution
- **FQDN Support**: DNS-based server resolution
- **Persistent Order**: Server order maintained across reboots
- **Automatic Failover**: Failed servers skipped

### Configuration

```
# RADIUS server pool (1-4 servers)
radius_pool_servers=radius1.example.com,radius2.example.com,radius3.example.com
radius_pool_port=1812
radius_pool_secret=SharedSecret
```

## Auth Survivability Mode

Allows local authentication when RADIUS server is unreachable:

### Features

- **Cached Credentials**: Previously authenticated users can reconnect
- **Fallback Mode**: Automatic switch when RADIUS unreachable
- **Configurable Timeout**: Time before entering survivability mode

## Client Profiling

RADIUS accounting includes client profiling attributes:

| Attribute | Source | Description |
|-----------|--------|-------------|
| DHCP Fingerprint | DHCP Options | Device type identification |
| HTTP User-Agent | HTTP Headers | Browser/OS identification |
| Hostname | DHCP Option 12 | Client hostname |

## Source Code Files

| File | Description |
|------|-------------|
| `src/hostapd/src/radius/ar_radius_client.c` | Arista RADIUS client extensions |
| `src/hostapd/src/radius/ar_radius_das.c` | Dynamic Authorization Server (CoA/DM) |
| `src/hostapd/src/ap/ar_accounting.c` | RADIUS accounting implementation |
| `src/portal/src/synchradius.c` | Captive portal RADIUS integration |
| `src/portal/src/coahandler.c` | CoA handler for captive portal |
| `src/radius_auth/radius_client.c` | RADIUS client using freeradius-client |

## RADIUS Tests

### Test Files

| Test | Description |
|------|-------------|
| `RadiusAcctServerTest.py` | Accounting Start/Interim/Stop validation |
| `RadiusBwCoaTest.py` | Bandwidth limits via CoA and Accept-Reply |
| `RadiusPoolingTest.py` | Multi-server pooling with FQDN |
| `RadiusFqdnTest.py` | FQDN resolution, CoA cluster, Auth Survivability |
| `RadsecproxyTest.py` | RadSec (RADIUS over TLS) connections |
| `AgniRadsecproxyTest.py` | RadSec with Agni platform |
| `AuthSurvivabilityModeTest.py` | Local auth when RADIUS unreachable |

### Test Categories

#### Accounting Tests (`RadiusAcctServerTest`)

- Validate Accounting-Start packet attributes
- Validate Accounting-Interim-Update packets
- Validate Accounting-Stop packet attributes
- Client profiling attributes (DHCP, HTTP UA)
- Server failover testing
- CoA Interim Interval updates
- Tagged VLAN accounting

#### Bandwidth CoA Tests (`RadiusBwCoaTest`)

- Bandwidth limits via Access-Accept
- Dynamic bandwidth update via CoA
- Traffic class (`tc`) validation
- Dynamic VLAN assignment (static/auto)
- Default rates: UL=2332 kbps, DL=3223 kbps

#### Server Pooling Tests (`RadiusPoolingTest`)

- 1-4 server configurations
- Randomized server selection
- FQDN resolution with DNS
- Order persistence across reboots

#### FQDN Tests (`RadiusFqdnTest`)

- FQDN resolution for RADIUS servers
- CoA ACK/NAK testing
- CoA cluster configuration
- IPv4/IPv6/Dual-stack support
- DNS retry mechanism

#### RadSec Tests (`RadsecproxyTest`)

- Multiple SSIDs with different RadSec servers
- TLS connection validation
- CRL revocation (PEM/DER format)
- Certificate validation (CN/SAN)
- Failover testing
- Process crash recovery

### Running Tests

```bash
# Run RADIUS accounting test
python3 autotest/WifiClusterTest/ctest/RadiusAcctServerTest.py

# Run RadSec test with 4 TLS connections
python3 autotest/WifiClusterTest/ctest/RadsecproxyTest.py --tlsconns 4

# Run RADIUS pooling test
python3 autotest/WifiClusterTest/ctest/RadiusPoolingTest.py

# Run CoA bandwidth test
python3 autotest/WifiClusterTest/ctest/RadiusBwCoaTest.py
```

## RFCs and Standards

| RFC | Title |
|-----|-------|
| RFC 2865 | Remote Authentication Dial In User Service (RADIUS) |
| RFC 2866 | RADIUS Accounting |
| RFC 3579 | RADIUS Support for EAP |
| RFC 3580 | IEEE 802.1X RADIUS Usage Guidelines |
| RFC 5176 | Dynamic Authorization Extensions (CoA/DM) |
| RFC 6614 | Transport Layer Security (TLS) Encryption for RADIUS |
| RFC 6929 | Remote Authentication Dial-In User Service (RADIUS) Protocol Extensions |

## See Also

- [WPA/WPA2 Security](WPA_WPA2_SECURITY.md) - Key management and 802.1X
- [hostapd](HOSTAPD.md) - RADIUS configuration in hostapd
- [Inter-AP Communication](INTER_AP_COMMUNICATION.md) - CoA routing via Synch Agent

