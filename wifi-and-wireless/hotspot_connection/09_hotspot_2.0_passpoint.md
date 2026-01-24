## Hotspot 2.0 (Passpoint) Connection

Hotspot 2.0 (also known as Passpoint) provides a seamless, secure connection experience similar to cellular networks.

### 10.1 Hotspot 2.0 Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                       HOTSPOT 2.0 ARCHITECTURE                               │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌──────────────────────────────────────────────────────────────────────┐   │
│  │                         Hotspot 2.0 Ecosystem                         │   │
│  │                                                                       │   │
│  │  ┌─────────────┐    ┌─────────────┐    ┌─────────────────────────┐   │   │
│  │  │   Mobile    │    │   Access    │    │    Service Provider     │   │   │
│  │  │   Device    │◄──►│    Point    │◄──►│    Infrastructure       │   │   │
│  │  │             │    │             │    │                         │   │   │
│  │  │ • HS2.0     │    │ • HS2.0     │    │ • AAA Server (RADIUS)   │   │   │
│  │  │   Profile   │    │   Enabled   │    │ • OSU Server            │   │   │
│  │  │ • Credential│    │ • ANQP      │    │ • Policy Server         │   │   │
│  │  │   Store     │    │   Server    │    │ • Subscription Mgmt     │   │   │
│  │  └─────────────┘    └─────────────┘    └─────────────────────────┘   │   │
│  │                                                                       │   │
│  └──────────────────────────────────────────────────────────────────────┘   │
│                                                                              │
│  Key Components:                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │ • GAS (Generic Advertisement Service) - Query/response protocol     │    │
│  │ • ANQP (Access Network Query Protocol) - Network information        │    │
│  │ • OSU (Online Sign-Up) - Credential provisioning                    │    │
│  │ • OSEN (OSU Server-Only Authenticated L2 Encryption Network)        │    │
│  │ • NAI Realm - EAP method advertisement                              │    │
│  │ • Roaming Consortium - Provider identification                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 10.2 Hotspot 2.0 Connection Flow

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    HOTSPOT 2.0 CONNECTION FLOW                               │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  Client                                                          AP         │
│    │                                                              │         │
│    │  ════════════════════════════════════════════════════════   │         │
│    │              STEP 1: NETWORK DISCOVERY                       │         │
│    │  ════════════════════════════════════════════════════════   │         │
│    │                                                              │         │
│    │  Probe Request                                               │         │
│    │  ┌─────────────────────────────────────────────────────┐    │         │
│    │  │ Interworking IE: Query for HS2.0 networks           │    │         │
│    │  └─────────────────────────────────────────────────────┘    │         │
│    │ ────────────────────────────────────────────────────────────►│         │
│    │                                                              │         │
│    │  Probe Response / Beacon                                     │         │
│    │  ┌─────────────────────────────────────────────────────┐    │         │
│    │  │ Interworking IE:                                     │    │         │
│    │  │   • Access Network Type: Free public network         │    │         │
│    │  │   • Internet: Available                              │    │         │
│    │  │   • HESSID: Network identifier                       │    │         │
│    │  │ HS2.0 Indication IE:                                 │    │         │
│    │  │   • HS2.0 Version: 3.0                              │    │         │
│    │  │   • DGAF Disabled: 0                                 │    │         │
│    │  │ Roaming Consortium IE:                               │    │         │
│    │  │   • OI: 001122 (Provider 1)                         │    │         │
│    │  │   • OI: 334455 (Provider 2)                         │    │         │
│    │  └─────────────────────────────────────────────────────┘    │         │
│    │ ◄────────────────────────────────────────────────────────────│         │
│    │                                                              │         │
│    │  ════════════════════════════════════════════════════════   │         │
│    │              STEP 2: ANQP QUERY (GAS)                        │         │
│    │  ════════════════════════════════════════════════════════   │         │
│    │                                                              │         │
│    │  GAS Initial Request                                         │         │
│    │  ┌─────────────────────────────────────────────────────┐    │         │
│    │  │ Advertisement Protocol: ANQP                         │    │         │
│    │  │ Query List:                                          │    │         │
│    │  │   • NAI Realm (263)                                  │    │         │
│    │  │   • 3GPP Cellular Network (264)                      │    │         │
│    │  │   • Domain Name (268)                                │    │         │
│    │  │   • Roaming Consortium (261)                         │    │         │
│    │  │   • Venue Name (258)                                 │    │         │
│    │  │   • WAN Metrics (HS2.0)                              │    │         │
│    │  │   • Connection Capability (HS2.0)                    │    │         │
│    │  │   • Operating Class Indication (HS2.0)               │    │         │
│    │  └─────────────────────────────────────────────────────┘    │         │
│    │ ────────────────────────────────────────────────────────────►│         │
│    │                                                              │         │
│    │  GAS Initial Response                                        │         │
│    │  ┌─────────────────────────────────────────────────────┐    │         │
│    │  │ NAI Realm:                                           │    │         │
│    │  │   • Realm: example.com                               │    │         │
│    │  │   • EAP Method: EAP-TLS, EAP-TTLS                   │    │         │
│    │  │   • Inner Auth: MSCHAPv2                             │    │         │
│    │  │ 3GPP Cellular:                                       │    │         │
│    │  │   • MCC: 310, MNC: 260 (T-Mobile US)                │    │         │
│    │  │ Domain Name:                                         │    │         │
│    │  │   • example.com                                      │    │         │
│    │  │ WAN Metrics:                                         │    │         │
│    │  │   • Link Status: Up                                  │    │         │
│    │  │   • Downlink Speed: 100 Mbps                         │    │         │
│    │  │   • Uplink Speed: 50 Mbps                            │    │         │
│    │  │ Connection Capability:                               │    │         │
│    │  │   • TCP 80: Open                                     │    │         │
│    │  │   • TCP 443: Open                                    │    │         │
│    │  │   • UDP 500: Open (IPsec)                            │    │         │
│    │  └─────────────────────────────────────────────────────┘    │         │
│    │ ◄────────────────────────────────────────────────────────────│         │
│    │                                                              │         │
│    │  ┌─────────────────────────────────────────────────────┐    │         │
│    │  │ Client evaluates ANQP response:                      │    │         │
│    │  │ • Match NAI Realm with stored credentials           │    │         │
│    │  │ • Match Roaming Consortium with home provider       │    │         │
│    │  │ • Check EAP method compatibility                     │    │         │
│    │  │ • Evaluate WAN metrics for network quality          │    │         │
│    │  └─────────────────────────────────────────────────────┘    │         │
│    │                                                              │         │
│    │  ════════════════════════════════════════════════════════   │         │
│    │              STEP 3: ASSOCIATION                             │         │
│    │  ════════════════════════════════════════════════════════   │         │
│    │                                                              │         │
│    │  (Standard 802.11 Association - see Phase 4)                │         │
│    │                                                              │         │
│    │  ════════════════════════════════════════════════════════   │         │
│    │              STEP 4: 802.1X/EAP AUTHENTICATION               │         │
│    │  ════════════════════════════════════════════════════════   │         │
│    │                                                              │         │
│    │  EAP-TLS / EAP-TTLS / EAP-SIM / EAP-AKA                     │         │
│    │  (See Enterprise Authentication section)                     │         │
│    │                                                              │         │
│    │  ════════════════════════════════════════════════════════   │         │
│    │              STEP 5: 4-WAY HANDSHAKE                         │         │
│    │  ════════════════════════════════════════════════════════   │         │
│    │                                                              │         │
│    │  (Standard WPA2/WPA3 4-Way Handshake - see Phase 5)         │         │
│    │                                                              │         │
│    │  ════════════════════════════════════════════════════════   │         │
│    │              CONNECTED - SEAMLESS ROAMING                    │         │
│    │  ════════════════════════════════════════════════════════   │         │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 10.3 ANQP Elements

| Element ID | Name | Description |
|------------|------|-------------|
| 256 | ANQP Query List | List of requested elements |
| 257 | ANQP Capability List | Supported ANQP elements |
| 258 | Venue Name | Human-readable venue name |
| 259 | Emergency Call Number | Emergency services info |
| 260 | Network Authentication Type | Captive portal info |
| 261 | Roaming Consortium List | Provider identifiers |
| 262 | IP Address Type Availability | IPv4/IPv6 support |
| 263 | NAI Realm List | EAP methods per realm |
| 264 | 3GPP Cellular Network | MCC/MNC for SIM auth |
| 265 | AP Geospatial Location | GPS coordinates |
| 266 | AP Civic Location | Street address |
| 267 | AP Location Public Identifier URI | Location URI |
| 268 | Domain Name List | Operator domain names |
| 269 | Emergency Alert Identifier URI | Alert system URI |
| 270 | TDLS Capability | TDLS support |
| 271 | Emergency NAI | Emergency realm |
| 272 | Neighbor Report | Neighbor AP info |

### 10.4 Hotspot 2.0 Configuration (hostapd)

```conf
# hostapd.conf - Hotspot 2.0 configuration

# Enable Hotspot 2.0
hs20=1

# Interworking (802.11u)
interworking=1
access_network_type=2
internet=1
venue_group=2
venue_type=8
hessid=00:11:22:33:44:55

# Roaming Consortium
roaming_consortium=001122
roaming_consortium=334455667788

# NAI Realm
nai_realm=0,example.com,13[5:6],21[2:4][5:7]
# Format: <encoding>,<realm>,<eap_method>[<inner_auth>]
# 13 = EAP-TLS, 21 = EAP-TTLS
# [5:6] = Credential Type: Certificate
# [2:4] = Inner Auth: MSCHAPv2

# Domain Name
domain_name=example.com

# 3GPP Cellular Network
anqp_3gpp_cell_net=310,260;310,410

# WAN Metrics
hs20_wan_metrics=01:8000:1000:80:240:3000

# Connection Capability
hs20_conn_capab=6:22:1
hs20_conn_capab=6:80:1
hs20_conn_capab=6:443:1
hs20_conn_capab=17:500:1
hs20_conn_capab=17:4500:1

# Operating Class Indication
hs20_operating_class=51

# OSU Providers
osu_ssid="OSU-Network"
osu_server_uri=https://osu.example.com/
osu_friendly_name=eng:Example OSU
osu_nai=anonymous@example.com
osu_method_list=1
```

### 10.5 GAS/ANQP Implementation (hostapd)

```c
// gas_serv.c - GAS/ANQP server implementation
static void gas_serv_rx_gas_initial_req(struct hostapd_data *hapd,
                                        const u8 *sa,
                                        const u8 *data, size_t len,
                                        int prot, int std_addr3)
{
    // Parse GAS request
    // Extract ANQP query list
    // Build ANQP response with requested elements:
    //   - NAI Realm
    //   - Roaming Consortium
    //   - 3GPP Cellular Network
    //   - Domain Name
    //   - WAN Metrics
    //   - Connection Capability
    // Send GAS response
}

// hs20.c - Hotspot 2.0 IE generation
u8 * hostapd_eid_hs20_indication(struct hostapd_data *hapd, u8 *eid)
{
    u8 conf;

    if (!hapd->conf->hs20)
        return eid;

    *eid++ = WLAN_EID_VENDOR_SPECIFIC;
    *eid++ = 7;  // Length
    WPA_PUT_BE24(eid, OUI_WFA);
    eid += 3;
    *eid++ = HS20_INDICATION_OUI_TYPE;

    conf = HS20_VERSION << 4;  // Version in upper nibble
    if (hapd->conf->hs20_release >= 2)
        conf |= HS20_ANQP_DOMAIN_ID_PRESENT;
    *eid++ = conf;

    if (hapd->conf->hs20_release >= 2) {
        WPA_PUT_LE16(eid, hapd->conf->anqp_domain_id);
        eid += 2;
    }

    return eid;
}
```

---

