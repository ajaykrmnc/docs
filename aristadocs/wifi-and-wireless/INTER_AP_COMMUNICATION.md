# Inter-AP Communication and Information Sharing

This document describes how Access Points (APs) in this repository share information and communicate with each other to provide seamless roaming, security synchronization, and coordinated wireless operation.

## Overview

APs communicate through the **Synch Agent** (`synch_agent`), a core daemon that handles Inter-AP Communication (IAPC). The synch agent manages the exchange of security credentials, client state, DFS information, and other operational data between neighboring APs.

## Communication Paths

### 1. L2 Broadcast (PACKET_PATH_BROADCAST)

- Uses Layer 2 Ethernet broadcast frames
- Works across APs on the same L2 domain (VLAN)
- Default fallback method when RF neighbors aren't available
- Destination MAC: `FF:FF:FF:FF:FF:FF`

### 2. RF-Domain / Neighbors (PACKET_PATH_RF_DOMAIN)

- Communication limited to RF-detected neighbor APs
- APs discover neighbors through radio scanning (beacon/probe monitoring)
- More targeted than broadcast - reduces network traffic
- RF neighbors stored in `/opt/ap/rf_neighbors`
- Neighbors pruned after 6 hours of inactivity

### 3. Unicast IAPC via ZeroMQ

- High-performance TCP-based unicast communication
- Uses ZeroMQ PUB/SUB sockets (port 5559)
- Enabled when `INTER_AP_COMM = RF_NBR_UNICAST`
- More efficient than L2 broadcast for larger deployments
- Supports up to 256 RF neighbor connections

## IAPC Packet Types

The following packet types are exchanged between APs:

| Packet Type | ID | Purpose |
|-------------|----|---------|
| `ATN_OKC_PACKET` | 101 | OKC (Opportunistic Key Caching) PMK sync |
| `ATN_ASSOC_BROADCAST_PACKET` | 102 | Client association notifications |
| `PORTAL_CL_AUTH_PACKET` | 103 | Portal client authentication state |
| `DHCP_SYNCH_PACKET` | 104 | DHCP lease information |
| `ATN_COA_LOGOFF_PACKET` | 107 | RADIUS CoA disconnect notifications |
| `ATN_FT_PACKET` | 108 | 802.11r Fast Transition key exchange |
| `ATN_COA_ATTRIB_PACKET` | 109 | RADIUS CoA attribute updates |
| `ATN_SEC_AUTH_PACKET` | 111 | Security/authentication cache sync |
| `ATN_RF_CLIENT_PACKET` | 112 | RF client information |
| `ATN_RF_NBR_INFO_PACKET` | 118 | RF neighbor information |
| `ATN_DFS_SYNCH_PACKET` | 124 | DFS radar hit information |
| `ATN_CL_DHCP_FP_INFO_PACKET` | 125 | DHCP fingerprint info |

## Key Synchronization Mechanisms

### OKC (Opportunistic Key Caching)

When a client authenticates with an AP, the PMK (Pairwise Master Key) is synchronized to neighbor APs:

```
Client → AP1 (Full 802.1X auth) → PMK generated
                                    ↓
                            OKC PUSH packet
                                    ↓
                    AP2, AP3, AP4... (cache PMK)
```

**OKC Operations:**
- **PUSH**: Send new PMK entry to neighbors after client authentication
- **PULL ALL**: Request all cached PMKs (on AP boot/hostapd restart)

### 802.11r Fast Transition (FT)

For fast roaming, PMK-R0/R1 keys are pre-shared between APs:

```
┌─────────────────────────────────────────────────────────────┐
│                    FT Key Hierarchy                         │
├─────────────────────────────────────────────────────────────┤
│  PMK (from 802.1X or PSK)                                   │
│    ↓                                                        │
│  PMK-R0 (stored at R0KH - original authenticator AP)        │
│    ↓                                                        │
│  PMK-R1 (derived for each R1KH - target AP)                 │
└─────────────────────────────────────────────────────────────┘
```

**FT Packet Subtypes:**
- `FT_PACKET_R0KH_R1KH_PULL`: Request PMK-R1 from R0KH
- `FT_PACKET_R0KH_R1KH_RESP`: Response with PMK-R1
- `FT_PACKET_R0KH_R1KH_PUSH`: Proactive PMK-R1 push to neighbor
- `FT_PACKET_R0KH_R1KH_PULL_ALL`: Request all FT keys

### Sec-Auth Cache Sync

For MAC authentication and RADIUS-based authorization:
- Client authorization status synced across APs
- Enables splashless portal roaming
- VLAN assignments synchronized

## DFS Information Sharing

When an AP detects radar, it shares the hit information with neighbors:

```
AP1 detects radar on Ch 100
        ↓
ATN_DFS_SYNCH_PACKET sent to neighbors
        ↓
AP2, AP3 update their radar hit rate tables
        ↓
Smarter channel selection avoiding high-radar channels
```

**Configuration:**
- Controlled by `Radarhit_IAPC_Enabled` toggle per radio
- Only shared when enabled on both transmitting and receiving APs

## RF Neighbor Discovery

APs discover neighbors through wireless scanning:

```c
struct rf_neighbor {
    uint8_t eth_mac[ETH_ALEN];      // Neighbor's MAC address
    uint8_t ipv4_addr[MAX_IPV4_LEN]; // IPv4 address
    uint8_t ipv6_addr[MAX_IPV6_LEN]; // IPv6 address
    int32_t rx_rssi_a;               // RSSI on 5GHz
    int32_t rx_rssi_g;               // RSSI on 2.4GHz
    time_t last_seen_time;           // Last beacon seen
};
```

**Update Interval:** Every 5 minutes (`RF_NBR_UPDATE_INTERVAL = 300`)
**Prune Timeout:** 6 hours (`RF_NBR_PRUNE_TIMEOUT = 6 * 60 * 60`)

## Client Roaming Flow

```
┌──────────────────────────────────────────────────────────────────┐
│                    Client Roaming Sequence                        │
├──────────────────────────────────────────────────────────────────┤
│                                                                   │
│  1. Client connected to AP1, authenticated (PMK cached)          │
│                          ↓                                        │
│  2. AP1 sends OKC/FT PUSH to neighbor APs                        │
│                          ↓                                        │
│  3. Client decides to roam (low RSSI, 802.11k/v triggered)       │
│                          ↓                                        │
│  4. Client sends reassociation to AP2                            │
│                          ↓                                        │
│  5. AP2 looks up cached PMK (OKC) or derives PMK-R1 (FT)         │
│                          ↓                                        │
│  6. Fast 4-way handshake (skips full 802.1X)                     │
│                          ↓                                        │
│  7. Client roamed - data flows through AP2                       │
│                                                                   │
└──────────────────────────────────────────────────────────────────┘
```

## Tests for Inter-AP Communication

| Test | Description |
|------|-------------|
| `ClientRoamingTest` | Client roaming with OKC/FT, L2 broadcast or RF-domain |
| `PMKCacheSyncTest` | OKC cache PUSH, PULL ALL operations |
| `ApDfsInfoSharingTest` | DFS hit rate information sharing |
| `ApNeighborhoodTest` | RF neighbor discovery |

## Configuration

### Enable RF-Domain Communication
```
INTER_AP_COMM=2  # RF_NBR_UNICAST (vs 1=RF_NBR_BROADCAST)
```

### OKC Configuration (per SSID)
```
okc_enable=1
```

### Fast Transition Configuration
```
ieee80211r=1
mobility_domain=<MDID>
r0_key_holder=<R0KH-ID>
r1_key_holder=<R1KH-ID>
```

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│                         AP Architecture                              │
│                                                                      │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐              │
│  │   hostapd   │    │   portal    │    │    rrmd     │              │
│  │  (802.1X,   │    │ (captive    │    │   (radio    │              │
│  │   FT, OKC)  │    │  portal)    │    │  resource)  │              │
│  └──────┬──────┘    └──────┬──────┘    └──────┬──────┘               │
│         │                  │                  │                      │
│         └──────────────────┼──────────────────┘                      │
│                            │                                         │
│                    ┌───────▼───────┐                                 │
│                    │  synch_agent  │                                 │
│                    │   (IAPC)      │                                 │
│                    └───────┬───────┘                                 │
│                            │                                         │
│         ┌──────────────────┼──────────────────┐                      │
│         │                  │                  │                      │
│  ┌──────▼──────┐   ┌───────▼───────┐  ┌───────▼───────┐             │
│  │ L2 Broadcast│   │  RF-Domain    │  │ ZeroMQ TCP    │             │
│  │  (Ethernet) │   │  (filtered)   │  │  (unicast)    │             │
│  └─────────────┘   └───────────────┘  └───────────────┘             │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

