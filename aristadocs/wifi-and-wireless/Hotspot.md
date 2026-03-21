# Hotspot Connection Pathway

This document provides a comprehensive, step-by-step guide explaining the complete pathway when a wireless
hotspot is enabled on an Access Point (AP) and how clients connect to it. It covers every layer of the
connection process from RF discovery to application-level connectivity.

## Overview

[When](2026-01-08_when.md) you enable a WiFi hotspot on an Access Point, a complex series of events occurs at
multiple layers of the network stack. The connection process involves:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    HOTSPOT CONNECTION PATHWAY OVERVIEW                       │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌──────────────────┐                          ┌──────────────────────────┐ │
│  │  Wireless Client │                          │    Access Point (AP)     │ │
│  │    (STA/Device)  │                          │       (Hotspot)          │ │
│  └────────┬─────────┘                          └────────────┬─────────────┘ │
│           │                                                 │               │
│           │  ══════════════════════════════════════════════ │               │
│           │           PHASE 1: AP INITIALIZATION            │               │
│           │  ══════════════════════════════════════════════ │               │
│           │                                                 │               │
│           │                                    ┌────────────┴────────────┐  │
│           │                                    │ • hostapd starts        │  │
│           │                                    │ • VAP created           │  │
│           │                                    │ • Beacon transmission   │  │
│           │                                    │ • Security configured   │  │
│           │                                    └────────────┬────────────┘  │
│           │                                                 │               │
│           │  ══════════════════════════════════════════════ │               │
│           │           PHASE 2: DISCOVERY (SCANNING)          │               │
│           │  ══════════════════════════════════════════════ │               │
│           │                                                 │               │
│  ┌────────┴─────────┐      Probe Request      ┌────────────┴────────────┐  │
│  │ Passive/Active   │ ─────────────────────► │ Probe Response          │  │
│  │ Scanning         │ ◄───────────────────── │ (SSID, Capabilities)    │  │
│  └────────┬─────────┘                        └────────────┬────────────┘  │
│           │                   Beacon                       │               │
│           │ ◄─────────────────────────────────────────────│               │
│           │                                                 │               │
│           │  ══════════════════════════════════════════════ │               │
│           │           PHASE 3: AUTHENTICATION               │               │
│           │  ══════════════════════════════════════════════ │               │
│           │                                                 │               │
│           │      Authentication Request                     │               │
│           │ ────────────────────────────────────────────── ►│               │
│           │      Authentication Response                    │               │
│           │ ◄────────────────────────────────────────────── │               │
│           │                                                 │               │
│           │  ══════════════════════════════════════════════ │               │
│           │           PHASE 4: ASSOCIATION                  │               │
│           │  ══════════════════════════════════════════════ │               │
│           │                                                 │               │
│           │      Association Request                        │               │
│           │ ────────────────────────────────────────────── ►│               │
│           │      Association Response (AID)                 │               │
│           │ ◄────────────────────────────────────────────── │               │
│           │                                                 │               │
│           │  ══════════════════════════════════════════════ │               │
│           │     PHASE 5: 4-WAY HANDSHAKE (WPA/WPA2/WPA3)    │               │
│           │  ══════════════════════════════════════════════ │               │
│           │                                                 │               │
│           │      EAPOL Message 1 (ANonce)                   │               │
│           │ ◄────────────────────────────────────────────── │               │
│           │      EAPOL Message 2 (SNonce, MIC)              │               │
│           │ ────────────────────────────────────────────── ►│               │
│           │      EAPOL Message 3 (GTK, MIC)                 │               │
│           │ ◄────────────────────────────────────────────── │               │
│           │      EAPOL Message 4 (ACK)                      │               │
│           │ ────────────────────────────────────────────── ►│               │
│           │                                                 │               │
│           │  ══════════════════════════════════════════════ │               │
│           │           PHASE 6: DHCP (IP ASSIGNMENT)         │               │
│           │  ══════════════════════════════════════════════ │               │
│           │                                                 │               │
│           │      DHCP Discover                              │               │
│           │ ────────────────────────────────────────────── ►│               │
│           │      DHCP Offer                                 │               │
│           │ ◄────────────────────────────────────────────── │               │
│           │      DHCP Request                               │               │
│           │ ────────────────────────────────────────────── ►│               │
│           │      DHCP ACK (IP Address)                      │               │
│           │ ◄────────────────────────────────────────────── │               │
│           │                                                 │               │
│           │  ══════════════════════════════════════════════ │               │
│           │     PHASE 7: CAPTIVE PORTAL (OPTIONAL)          │               │
│           │  ══════════════════════════════════════════════ │               │
│           │                                                 │               │
│           │      HTTP Request                               │               │
│           │ ────────────────────────────────────────────── ►│               │
│           │      HTTP Redirect (302)                        │               │
│           │ ◄────────────────────────────────────────────── │               │
│           │      Portal Authentication                      │               │
│           │ ◄──────────────────────────────────────────────►│               │
│           │                                                 │               │
│           │  ══════════════════════════════════════════════ │               │
│           │           PHASE 8: CONNECTED                    │               │
│           │  ══════════════════════════════════════════════ │               │
│           │                                                 │               │
│           │      ════ Full Internet Access ════             │               │
│           │ ◄──────────────────────────────────────────────►│               │
│           │                                                 │               │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Phase 1: AP Initialization and Hotspot Enabling

When the hotspot is enabled on an Access Point, the following initialization sequence occurs:

### 1.1 System Initialization

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         AP INITIALIZATION SEQUENCE                           │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌───────────────┐     ┌───────────────┐     ┌───────────────────────────┐  │
│  │ Configuration │     │    Radio      │     │       hostapd             │  │
│  │    Agent      │────►│   Manager     │────►│   (AP Daemon)             │  │
│  └───────────────┘     └───────────────┘     └───────────────────────────┘  │
│         │                     │                         │                    │
│         ▼                     ▼                         ▼                    │
│  ┌───────────────┐     ┌───────────────┐     ┌───────────────────────────┐  │
│  │ Read Config   │     │ Initialize    │     │ Create VAP (Virtual AP)  │  │
│  │ (ap.conf)     │     │ WiFi Driver   │     │ Start Beacon Tx          │  │
│  └───────────────┘     └───────────────┘     └───────────────────────────┘  │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 1.2 Configuration Loading

The AP loads configuration from multiple sources:

| Configuration Item | Description          | Example                        |
| ------------------ | -------------------- | ------------------------------ |
| SSID               | Network name         | `MyHotspot`                    |
| Security Mode      | Authentication type  | `WPA2-PSK`, `WPA3-SAE`, `Open` |
| Channel            | Operating frequency  | `36` (5 GHz), `6` (2.4 GHz)    |
| Bandwidth          | Channel width        | `20`, `40`, `80`, `160` MHz    |
| VLAN               | Network isolation    | `100`                          |
| Captive Portal     | Guest authentication | `Enabled/Disabled`             |

### 1.3 VAP (Virtual Access Point) Creation

```bash
# VAP creation script (configVAP)
# Creates virtual interface for each SSID

# Enable Hotspot 2.0 if configured
if [ "$HS20_VAP_ENABLE" != "" ]; then
  iwpriv ${APNAME} hs20_vap $HS20_VAP_ENABLE
fi

# Enable OSEN (OSU Server-Only Authenticated L2 Encryption Network)
if [ "$HS20_OSEN_ENABLED" != "" ]; then
  iwpriv ${APNAME} hs20_osen $HS20_OSEN_ENABLED
fi
```

### 1.4 hostapd Initialization

hostapd is the core daemon that manages the access point functionality:

```c
/* hostapd initialization sequence */
1. Parse configuration file (hostapd.conf)
2. Initialize wireless driver interface
3. Set up security parameters (WPA/WPA2/WPA3)
4. Initialize RADIUS client (if 802.1X)
5. Start beacon transmission
6. Register for management frame callbacks
7. Initialize GAS/ANQP server (if Hotspot 2.0)
```

### 1.5 Beacon Frame Generation

The AP starts transmitting beacon frames at regular intervals (typically 100ms):

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           BEACON FRAME STRUCTURE                             │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌──────────────────────────────────────────────────────────────────────┐   │
│  │                         MAC Header (24 bytes)                         │   │
│  ├───────────────┬───────────────┬───────────────┬──────────────────────┤   │
│  │ Frame Control │   Duration    │    DA (FF:FF) │   SA (AP MAC)        │   │
│  └───────────────┴───────────────┴───────────────┴──────────────────────┘   │
│                                                                              │
│  ┌──────────────────────────────────────────────────────────────────────┐   │
│  │                       Fixed Parameters (12 bytes)                     │   │
│  ├───────────────────────┬───────────────────┬──────────────────────────┤   │
│  │      Timestamp        │  Beacon Interval  │    Capability Info       │   │
│  │      (8 bytes)        │    (2 bytes)      │      (2 bytes)           │   │
│  └───────────────────────┴───────────────────┴──────────────────────────┘   │
│                                                                              │
│  ┌──────────────────────────────────────────────────────────────────────┐   │
│  │                    Information Elements (Variable)                    │   │
│  ├──────────────────────────────────────────────────────────────────────┤   │
│  │  • SSID (ID=0)                 - Network name                         │   │
│  │  • Supported Rates (ID=1)      - 1, 2, 5.5, 11 Mbps, etc.            │   │
│  │  • DS Parameter Set (ID=3)     - Channel number                       │   │
│  │  • TIM (ID=5)                  - Traffic Indication Map               │   │
│  │  • Country (ID=7)              - Regulatory domain                    │   │
│  │  • RSN (ID=48)                 - WPA2/WPA3 security info             │   │
│  │  • HT Capabilities (ID=45)     - 802.11n support                     │   │
│  │  • VHT Capabilities (ID=191)   - 802.11ac support                    │   │
│  │  • HE Capabilities (ID=255)    - 802.11ax (WiFi 6) support           │   │
│  │  • Vendor Specific (ID=221)    - WPA, WMM, WPS, Hotspot 2.0          │   │
│  └──────────────────────────────────────────────────────────────────────┘   │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

**Source Code Reference:**

```c
// beacon.c - Beacon frame generation
static u8 * hostapd_eid_bss_load(struct hostapd_data *hapd, u8 *eid, size_t len)
{
  if (hapd->conf->bss_load_update_period) {
    *eid++ = WLAN_EID_BSS_LOAD;
    *eid++ = 5;
    WPA_PUT_LE16(eid, hapd->num_sta);  // Number of associated stations
    eid += 2;
    *eid++ = hapd->iface->channel_utilization;  // Channel utilization
    WPA_PUT_LE16(eid, 0);  // Available admission capacity
    eid += 2;
  }
  return eid;
}
```

---

## Phase 2: Client Discovery (Scanning)

When a client device wants to connect to a WiFi network, it first needs to discover available networks.

### 2.1 Passive Scanning

The client listens for beacon frames on each channel:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           PASSIVE SCANNING                                   │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  Channel 1        Channel 6        Channel 11       Channel 36              │
│  ┌────────┐      ┌────────┐       ┌────────┐       ┌────────┐              │
│  │ Listen │      │ Listen │       │ Listen │       │ Listen │              │
│  │ 100ms  │─────►│ 100ms  │──────►│ 100ms  │──────►│ 100ms  │ ───► ...     │
│  └────────┘      └────────┘       └────────┘       └────────┘              │
│      │               │                │                │                    │
│      ▼               ▼                ▼                ▼                    │
│  ┌────────┐      ┌────────┐       ┌────────┐       ┌────────┐              │
│  │Receive │      │Receive │       │Receive │       │Receive │              │
│  │Beacons │      │Beacons │       │Beacons │       │Beacons │              │
│  └────────┘      └────────┘       └────────┘       └────────┘              │
│                                                                              │
│  Advantage: Lower power consumption                                          │
│  Disadvantage: Slower discovery, may miss hidden SSIDs                      │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 2.2 Active Scanning

The client sends probe requests and waits for probe responses:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                            ACTIVE SCANNING                                   │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  Client                                                          AP         │
│    │                                                              │         │
│    │  Probe Request (Broadcast or Directed)                      │         │
│    │  ┌─────────────────────────────────────────────────────┐    │         │
│    │  │ SSID: "MyHotspot" or Wildcard (empty)               │    │         │
│    │  │ Supported Rates: 6, 9, 12, 18, 24, 36, 48, 54 Mbps  │    │         │
│    │  │ HT Capabilities: 802.11n support                     │    │         │
│    │  │ VHT Capabilities: 802.11ac support                   │    │         │
│    │  └─────────────────────────────────────────────────────┘    │         │
│    │ ────────────────────────────────────────────────────────────►│         │
│    │                                                              │         │
│    │  Probe Response                                              │         │
│    │  ┌─────────────────────────────────────────────────────┐    │         │
│    │  │ SSID: "MyHotspot"                                    │    │         │
│    │  │ BSSID: AA:BB:CC:DD:EE:FF                            │    │         │
│    │  │ Channel: 36                                          │    │         │
│    │  │ Security: WPA2-PSK (RSN IE)                         │    │         │
│    │  │ Capabilities: ESS, Short Preamble, Short Slot       │    │         │
│    │  └─────────────────────────────────────────────────────┘    │         │
│    │ ◄────────────────────────────────────────────────────────────│         │
│    │                                                              │         │
│                                                                              │
│  Advantage: Faster discovery, finds hidden SSIDs                            │
│  Disadvantage: Higher power consumption, reveals client presence            │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 2.3 Probe Request Handling (hostapd)

```c
// ieee802_11.c - Probe request handling
void handle_probe_req(struct hostapd_data *hapd,
                      const struct ieee80211_mgmt *mgmt, size_t len,
                      int ssi_signal)
{
  // 1. Check if SSID matches (or is wildcard)
  // 2. Check if client supports required rates
  // 3. Check MAC ACL (allow/deny lists)
  // 4. Build and send probe response with:
  //    - SSID, Supported Rates, Channel
  //    - RSN IE (security capabilities)
  //    - HT/VHT/HE capabilities
  //    - Vendor extensions (WMM, WPS, HS2.0)
}
```

### 2.4 Network Selection Criteria

The client selects a network based on:

| Criteria               | Priority | Description                          |
| ---------------------- | -------- | ------------------------------------ |
| SSID Match             | Highest  | Matches preferred/configured network |
| Signal Strength (RSSI) | High     | Stronger signal preferred            |
| Security Level         | High     | WPA3 > WPA2 > WPA > Open             |
| Band Preference        | Medium   | 5 GHz/6 GHz preferred for speed      |
| Load                   | Low      | Less congested AP preferred          |

---

## Phase 3: Authentication

After selecting a network, the client initiates the authentication process.

### 3.1 Open System Authentication

For Open networks and WPA/WPA2/WPA3-Personal, Open System Authentication is used:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                       OPEN SYSTEM AUTHENTICATION                             │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  Client                                                          AP         │
│    │                                                              │         │
│    │  Authentication Request                                      │         │
│    │  ┌─────────────────────────────────────────────────────┐    │         │
│    │  │ Algorithm: Open System (0)                           │    │         │
│    │  │ Sequence Number: 1                                   │    │         │
│    │  │ Status Code: 0 (Reserved)                            │    │         │
│    │  └─────────────────────────────────────────────────────┘    │         │
│    │ ────────────────────────────────────────────────────────────►│         │
│    │                                                              │         │
│    │  Authentication Response                                     │         │
│    │  ┌─────────────────────────────────────────────────────┐    │         │
│    │  │ Algorithm: Open System (0)                           │    │         │
│    │  │ Sequence Number: 2                                   │    │         │
│    │  │ Status Code: 0 (Success)                             │    │         │
│    │  └─────────────────────────────────────────────────────┘    │         │
│    │ ◄────────────────────────────────────────────────────────────│         │
│    │                                                              │         │
│    │         ══════ Authentication Complete ══════                │         │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 3.2 SAE (Simultaneous Authentication of Equals) - WPA3

For WPA3-Personal, SAE provides stronger authentication:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    SAE AUTHENTICATION (WPA3-Personal)                        │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  Client                                                          AP         │
│    │                                                              │         │
│    │  SAE Commit                                                  │         │
│    │  ┌─────────────────────────────────────────────────────┐    │         │
│    │  │ Algorithm: SAE (3)                                   │    │         │
│    │  │ Sequence: 1 (Commit)                                 │    │         │
│    │  │ Finite Cyclic Group: 19 (256-bit ECC)               │    │         │
│    │  │ Scalar: Random value derived from password          │    │         │
│    │  │ Element: ECC point                                   │    │         │
│    │  └─────────────────────────────────────────────────────┘    │         │
│    │ ────────────────────────────────────────────────────────────►│         │
│    │                                                              │         │
│    │  SAE Commit                                                  │         │
│    │  ┌─────────────────────────────────────────────────────┐    │         │
│    │  │ Algorithm: SAE (3)                                   │    │         │
│    │  │ Sequence: 1 (Commit)                                 │    │         │
│    │  │ Scalar: AP's random value                           │    │         │
│    │  │ Element: AP's ECC point                             │    │         │
│    │  └─────────────────────────────────────────────────────┘    │         │
│    │ ◄────────────────────────────────────────────────────────────│         │
│    │                                                              │         │
│    │  SAE Confirm                                                 │         │
│    │  ┌─────────────────────────────────────────────────────┐    │         │
│    │  │ Algorithm: SAE (3)                                   │    │         │
│    │  │ Sequence: 2 (Confirm)                                │    │         │
│    │  │ Send-Confirm: Counter                                │    │         │
│    │  │ Confirm: HMAC of shared secret                       │    │         │
│    │  └─────────────────────────────────────────────────────┘    │         │
│    │ ────────────────────────────────────────────────────────────►│         │
│    │                                                              │         │
│    │  SAE Confirm                                                 │         │
│    │ ◄────────────────────────────────────────────────────────────│         │
│    │                                                              │         │
│    │    ══════ PMK Derived, Authentication Complete ══════       │         │
│                                                                              │
│  Benefits:                                                                   │
│  • Resistant to offline dictionary attacks                                  │
│  • Forward secrecy (past sessions protected even if password compromised)  │
│  • Mutual authentication (both parties prove password knowledge)           │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 3.3 Authentication State Machine (hostapd)

```c
// ieee802_11.c - Authentication handling
static void handle_auth(struct hostapd_data *hapd,
                        const struct ieee80211_mgmt *mgmt, size_t len,
                        int rssi, int from_queue)
{
  u16 auth_alg = le_to_host16(mgmt->u.auth.auth_alg);
  u16 auth_transaction = le_to_host16(mgmt->u.auth.auth_transaction);

  switch (auth_alg) {
    case WLAN_AUTH_OPEN:
      // Simple open system authentication
      // Send success response
      break;
    case WLAN_AUTH_SHARED_KEY:
      // WEP shared key (deprecated)
      break;
    case WLAN_AUTH_FT:
      // 802.11r Fast Transition
      handle_auth_ft_finish(ctx, dst, bssid, auth_transaction, status, ies, ies_len);
      break;
    case WLAN_AUTH_SAE:
      // WPA3 SAE authentication
      handle_auth_sae(hapd, sta, mgmt, len, auth_transaction, status_code);
      break;
    case WLAN_AUTH_FILS_SK:
    case WLAN_AUTH_FILS_SK_PFS:
      // Fast Initial Link Setup
      handle_auth_fils(hapd, sta, ...);
      break;
  }
}
```

---

## Phase 4: Association

After successful authentication, the client associates with the AP.

### 4.1 Association Request/Response

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           ASSOCIATION PROCESS                                │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  Client                                                          AP         │
│    │                                                              │         │
│    │  Association Request                                         │         │
│    │  ┌─────────────────────────────────────────────────────┐    │         │
│    │  │ Capability Information:                              │    │         │
│    │  │   • ESS (Infrastructure mode)                        │    │         │
│    │  │   • Short Preamble                                   │    │         │
│    │  │   • Short Slot Time                                  │    │         │
│    │  │ Listen Interval: 10 beacons                          │    │         │
│    │  │ SSID: "MyHotspot"                                    │    │         │
│    │  │ Supported Rates: 6-54 Mbps                           │    │         │
│    │  │ RSN IE: Security capabilities                        │    │         │
│    │  │   • Pairwise Cipher: CCMP-128                        │    │         │
│    │  │   • AKM Suite: PSK or SAE                           │    │         │
│    │  │ HT Capabilities: 802.11n parameters                  │    │         │
│    │  │ VHT Capabilities: 802.11ac parameters                │    │         │
│    │  │ HE Capabilities: 802.11ax parameters                 │    │         │
│    │  └─────────────────────────────────────────────────────┘    │         │
│    │ ────────────────────────────────────────────────────────────►│         │
│    │                                                              │         │
│    │                                         ┌────────────────────┤         │
│    │                                         │ • Validate request │         │
│    │                                         │ • Check capacity   │         │
│    │                                         │ • Assign AID       │         │
│    │                                         │ • Create STA entry │         │
│    │                                         └────────────────────┤         │
│    │                                                              │         │
│    │  Association Response                                        │         │
│    │  ┌─────────────────────────────────────────────────────┐    │         │
│    │  │ Capability Information: ESS, Short Preamble, etc.   │    │         │
│    │  │ Status Code: 0 (Success)                             │    │         │
│    │  │ Association ID (AID): 1-2007                         │    │         │
│    │  │ Supported Rates                                      │    │         │
│    │  │ HT/VHT/HE Operation Parameters                       │    │         │
│    │  │ EDCA Parameters (QoS)                                │    │         │
│    │  └─────────────────────────────────────────────────────┘    │         │
│    │ ◄────────────────────────────────────────────────────────────│         │
│    │                                                              │         │
│    │         ══════ Association Complete ══════                   │         │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 4.2 Association Handling (hostapd)

```c
// ieee802_11.c - Association handling
static void handle_assoc(struct hostapd_data *hapd,
                         const struct ieee80211_mgmt *mgmt, size_t len,
                         int reassoc, int rssi)
{
  struct sta_info *sta;
  u16 capab_info, listen_interval;

  // 1. Parse association request
  capab_info = le_to_host16(mgmt->u.assoc_req.capab_info);
  listen_interval = le_to_host16(mgmt->u.assoc_req.listen_interval);

  // 2. Look up or create station entry
  sta = ap_get_sta(hapd, mgmt->sa);
  if (!sta) {
    sta = ap_sta_add(hapd, mgmt->sa);
  }

  // 3. Validate security parameters (RSN IE)
  // 4. Check MAC ACL
  // 5. Check association limits
  // 6. Assign AID (Association ID)
  // 7. Add station to driver
  hostapd_sta_add(hapd, addr, sta->aid, sta->capability, ...);

  // 8. Send association response
  send_assoc_resp(hapd, sta, mgmt->sa, WLAN_STATUS_SUCCESS, reassoc, ...);
}
```

### 4.3 Station (STA) Data Structure

```c
// sta_info.c - Station information
struct sta_info {
  u8 addr[ETH_ALEN];           // Client MAC address
  u16 aid;                      // Association ID
  u32 flags;                    // WLAN_STA_* flags

  // Security
  struct wpa_state_machine *wpa_sm;  // WPA state machine
  int vlan_id;                  // Assigned VLAN

  // Capabilities
  u16 capability;               // Capability info
  u8 supported_rates[WLAN_SUPP_RATES_MAX];
  struct ieee80211_ht_capabilities *ht_capabilities;
  struct ieee80211_vht_capabilities *vht_capabilities;
  struct ieee80211_he_capabilities *he_capabilities;

  // Statistics
  struct os_reltime connected_time;
  unsigned long rx_packets, tx_packets;
  unsigned long rx_bytes, tx_bytes;
};
```

---

## Phase 5: Security Key Exchange (4-Way Handshake)

After association, the 4-Way Handshake establishes encryption keys.

### 5.1 Key Hierarchy

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           WPA/WPA2/WPA3 KEY HIERARCHY                        │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                    Master Key Sources                                │    │
│  ├─────────────────────────────────────────────────────────────────────┤    │
│  │                                                                      │    │
│  │  WPA-Personal:                    WPA-Enterprise:                    │    │
│  │  ┌──────────────────┐            ┌──────────────────┐               │    │
│  │  │   Passphrase     │            │   EAP Method     │               │    │
│  │  │  (8-63 chars)    │            │ (TLS/TTLS/PEAP)  │               │    │
│  │  └────────┬─────────┘            └────────┬─────────┘               │    │
│  │           │                               │                          │    │
│  │           ▼                               ▼                          │    │
│  │  ┌──────────────────┐            ┌──────────────────┐               │    │
│  │  │ PBKDF2(pass,SSID)│            │       MSK        │               │    │
│  │  │   4096 rounds    │            │ (Master Session  │               │    │
│  │  └────────┬─────────┘            │      Key)        │               │    │
│  │           │                      └────────┬─────────┘               │    │
│  │           │                               │                          │    │
│  │           └───────────────┬───────────────┘                          │    │
│  │                           ▼                                          │    │
│  │                  ┌──────────────────┐                                │    │
│  │                  │       PMK        │                                │    │
│  │                  │ (Pairwise Master │                                │    │
│  │                  │      Key)        │                                │    │
│  │                  │   256 bits       │                                │    │
│  │                  └────────┬─────────┘                                │    │
│  │                           │                                          │    │
│  └───────────────────────────┼──────────────────────────────────────────┘    │
│                              │                                               │
│                              ▼                                               │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                    4-Way Handshake                                   │    │
│  │                                                                      │    │
│  │  PTK = PRF(PMK + ANonce + SNonce + AA + SPA)                        │    │
│  │                                                                      │    │
│  │  Where:                                                              │    │
│  │    PMK    = Pairwise Master Key                                     │    │
│  │    ANonce = Authenticator Nonce (random from AP)                    │    │
│  │    SNonce = Supplicant Nonce (random from client)                   │    │
│  │    AA     = Authenticator Address (AP MAC)                          │    │
│  │    SPA    = Supplicant Address (Client MAC)                         │    │
│  │                                                                      │    │
│  └────────────────────────────┬────────────────────────────────────────┘    │
│                               │                                              │
│                               ▼                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                    PTK (Pairwise Transient Key)                      │    │
│  ├─────────────────────────────────────────────────────────────────────┤    │
│  │                                                                      │    │
│  │  ┌─────────────┬─────────────┬─────────────────────────────────┐    │    │
│  │  │     KCK     │     KEK     │              TK                 │    │    │
│  │  │  (128 bits) │  (128 bits) │          (128/256 bits)         │    │    │
│  │  ├─────────────┼─────────────┼─────────────────────────────────┤    │    │
│  │  │ Key         │ Key         │ Temporal Key                    │    │    │
│  │  │ Confirmation│ Encryption  │ (Data encryption)               │    │    │
│  │  │ Key         │ Key         │                                 │    │    │
│  │  │ (MIC calc)  │ (Key wrap)  │                                 │    │    │
│  │  └─────────────┴─────────────┴─────────────────────────────────┘    │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                    GTK (Group Temporal Key)                          │    │
│  ├─────────────────────────────────────────────────────────────────────┤    │
│  │                                                                      │    │
│  │  GMK (Group Master Key) ──► GTK (128/256 bits)                      │    │
│  │                                                                      │    │
│  │  Used for broadcast/multicast traffic encryption                    │    │
│  │  Shared among all clients on the same BSS                           │    │
│  │  Delivered encrypted with KEK during 4-Way Handshake                │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 5.2 4-Way Handshake Sequence

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           4-WAY HANDSHAKE                                    │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  Client (Supplicant)                                    AP (Authenticator)  │
│    │                                                              │         │
│    │                                                              │         │
│    │  ┌─────────────────────────────────────────────────────────┐│         │
│    │  │ Both parties have PMK (from password or RADIUS)         ││         │
│    │  └─────────────────────────────────────────────────────────┘│         │
│    │                                                              │         │
│    │  ════════════════════════════════════════════════════════   │         │
│    │                    MESSAGE 1 (M1)                            │         │
│    │  ════════════════════════════════════════════════════════   │         │
│    │                                                              │         │
│    │  EAPOL-Key (ANonce, Replay Counter)                         │         │
│    │  ┌─────────────────────────────────────────────────────┐    │         │
│    │  │ Key Info: Pairwise, ACK                              │    │         │
│    │  │ Key Length: 16 (CCMP) or 32 (GCMP-256)              │    │         │
│    │  │ Replay Counter: 1                                    │    │         │
│    │  │ Key Nonce: ANonce (32 bytes random)                  │    │         │
│    │  │ Key MIC: 0 (not yet computed)                        │    │         │
│    │  │ Key Data: Empty                                      │    │         │
│    │  └─────────────────────────────────────────────────────┘    │         │
│    │ ◄────────────────────────────────────────────────────────────│         │
│    │                                                              │         │
│    │  ┌─────────────────────────────────────────────────────┐    │         │
│    │  │ Client generates SNonce                              │    │         │
│    │  │ Client computes PTK = PRF(PMK, ANonce, SNonce, ...)  │    │         │
│    │  │ Client derives KCK, KEK, TK from PTK                 │    │         │
│    │  └─────────────────────────────────────────────────────┘    │         │
│    │                                                              │         │
│    │  ════════════════════════════════════════════════════════   │         │
│    │                    MESSAGE 2 (M2)                            │         │
│    │  ════════════════════════════════════════════════════════   │         │
│    │                                                              │         │
│    │  EAPOL-Key (SNonce, MIC, RSN IE)                            │         │
│    │  ┌─────────────────────────────────────────────────────┐    │         │
│    │  │ Key Info: Pairwise, MIC                              │    │         │
│    │  │ Replay Counter: 1 (same as M1)                       │    │         │
│    │  │ Key Nonce: SNonce (32 bytes random)                  │    │         │
│    │  │ Key MIC: HMAC-SHA1(KCK, EAPOL-Key frame)            │    │         │
│    │  │ Key Data: RSN IE (client's security capabilities)   │    │         │
│    │  └─────────────────────────────────────────────────────┘    │         │
│    │ ────────────────────────────────────────────────────────────►│         │
│    │                                                              │         │
│    │                         ┌────────────────────────────────────┤         │
│    │                         │ AP computes PTK using SNonce       │         │
│    │                         │ AP verifies MIC using KCK          │         │
│    │                         │ AP validates RSN IE                │         │
│    │                         └────────────────────────────────────┤         │
│    │                                                              │         │
│    │  ════════════════════════════════════════════════════════   │         │
│    │                    MESSAGE 3 (M3)                            │         │
│    │  ════════════════════════════════════════════════════════   │         │
│    │                                                              │         │
│    │  EAPOL-Key (ANonce, MIC, Install, Encrypted GTK)            │         │
│    │  ┌─────────────────────────────────────────────────────┐    │         │
│    │  │ Key Info: Pairwise, Install, ACK, MIC, Secure       │    │         │
│    │  │ Replay Counter: 2                                    │    │         │
│    │  │ Key Nonce: ANonce (same as M1)                       │    │         │
│    │  │ Key MIC: HMAC-SHA1(KCK, EAPOL-Key frame)            │    │         │
│    │  │ Key Data (encrypted with KEK):                       │    │         │
│    │  │   • RSN IE (AP's security capabilities)             │    │         │
│    │  │   • GTK KDE (Group Temporal Key)                    │    │         │
│    │  │   • IGTK KDE (Integrity GTK, if MFP enabled)        │    │         │
│    │  └─────────────────────────────────────────────────────┘    │         │
│    │ ◄────────────────────────────────────────────────────────────│         │
│    │                                                              │         │
│    │  ┌─────────────────────────────────────────────────────┐    │         │
│    │  │ Client verifies MIC                                  │    │         │
│    │  │ Client decrypts GTK using KEK                        │    │         │
│    │  │ Client installs PTK and GTK                          │    │         │
│    │  └─────────────────────────────────────────────────────┘    │         │
│    │                                                              │         │
│    │  ════════════════════════════════════════════════════════   │         │
│    │                    MESSAGE 4 (M4)                            │         │
│    │  ════════════════════════════════════════════════════════   │         │
│    │                                                              │         │
│    │  EAPOL-Key (MIC, Acknowledgment)                            │         │
│    │  ┌─────────────────────────────────────────────────────┐    │         │
│    │  │ Key Info: Pairwise, MIC, Secure                      │    │         │
│    │  │ Replay Counter: 2 (same as M3)                       │    │         │
│    │  │ Key Nonce: 0                                         │    │         │
│    │  │ Key MIC: HMAC-SHA1(KCK, EAPOL-Key frame)            │    │         │
│    │  │ Key Data: Empty                                      │    │         │
│    │  └─────────────────────────────────────────────────────┘    │         │
│    │ ────────────────────────────────────────────────────────────►│         │
│    │                                                              │         │
│    │                         ┌────────────────────────────────────┤         │
│    │                         │ AP verifies MIC                    │         │
│    │                         │ AP installs PTK                    │         │
│    │                         │ AP opens controlled port           │         │
│    │                         └────────────────────────────────────┤         │
│    │                                                              │         │
│    │  ════════════════════════════════════════════════════════   │         │
│    │           ENCRYPTED DATA COMMUNICATION BEGINS                │         │
│    │  ════════════════════════════════════════════════════════   │         │
│    │                                                              │         │
│    │  ◄═══════════════ Encrypted with TK ═══════════════════════►│         │
│    │                                                              │         │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 5.3 WPA State Machine (hostapd)

```c
// wpa_auth.c - WPA PTK state machine
SM_STATE(WPA_PTK, INITIALIZE)
{
  SM_ENTRY_MA(WPA_PTK, INITIALIZE, wpa_ptk);
  sm->keycount = 0;
  sm->PTKRequest = FALSE;
  sm->TimeoutEvt = FALSE;
  sm->TimeoutCtr = 0;
  sm->PInitAKeys = FALSE;
  sm->Pair = TRUE;
}

SM_STATE(WPA_PTK, PTKSTART)
{
  SM_ENTRY_MA(WPA_PTK, PTKSTART, wpa_ptk);
  sm->PTKRequest = FALSE;
  sm->TimeoutEvt = FALSE;
  sm->TimeoutCtr++;

  // Generate ANonce
  if (random_get_bytes(sm->ANonce, WPA_NONCE_LEN)) {
    wpa_printf(MSG_ERROR, "WPA: Failed to get random data for ANonce");
    sm->Disconnect = TRUE;
    return;
  }

  // Send Message 1
  wpa_send_eapol(sm->wpa_auth, sm, WPA_KEY_INFO_ACK | WPA_KEY_INFO_KEY_TYPE,
                 NULL, sm->ANonce, NULL, 0, 0, 0);
}

SM_STATE(WPA_PTK, PTKCALCNEGOTIATING)
{
  SM_ENTRY_MA(WPA_PTK, PTKCALCNEGOTIATING, wpa_ptk);

  // Derive PTK from PMK, ANonce, SNonce, AA, SPA
  wpa_derive_ptk(sm, sm->SNonce, sm->PMK, sm->pmk_len, &PTK);

  // Verify MIC in Message 2
  if (wpa_verify_key_mic(sm->wpa_key_mgmt, sm->pmk_len, &PTK.kck,
                         sm->last_rx_eapol_key, sm->last_rx_eapol_key_len)) {
    wpa_printf(MSG_DEBUG, "WPA: Invalid MIC in msg 2/4");
    return;
  }
}

SM_STATE(WPA_PTK, PTKINITNEGOTIATING)
{
  SM_ENTRY_MA(WPA_PTK, PTKINITNEGOTIATING, wpa_ptk);

  // Send Message 3 with GTK
  wpa_send_eapol(sm->wpa_auth, sm,
                 WPA_KEY_INFO_ACK | WPA_KEY_INFO_INSTALL |
                 WPA_KEY_INFO_KEY_TYPE | WPA_KEY_INFO_MIC |
                 WPA_KEY_INFO_SECURE | WPA_KEY_INFO_ENCR_KEY_DATA,
                 kde, kde_len, sm->ANonce, keyidx, encr);
}

SM_STATE(WPA_PTK, PTKINITDONE)
{
  SM_ENTRY_MA(WPA_PTK, PTKINITDONE, wpa_ptk);

  // Install PTK to driver
  wpa_auth_set_key(sm->wpa_auth, 0, alg, sm->addr, 0, sm->PTK.tk, tk_len);

  // Mark port as authorized
  sm->pairwise_set = TRUE;
  wpa_auth_set_eapol(sm->wpa_auth, sm->addr, WPA_EAPOL_authorized, 1);
}
```

### 5.4 EAPOL-Key Frame Format

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         EAPOL-KEY FRAME FORMAT                               │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  Offset  Size   Field                Description                            │
│  ──────  ────   ─────                ───────────                            │
│  0       1      Protocol Version     0x02 (802.1X-2004)                     │
│  1       1      Packet Type          0x03 (EAPOL-Key)                       │
│  2       2      Packet Body Length   Length of key descriptor               │
│  4       1      Descriptor Type      0x02 (RSN Key)                         │
│  5       2      Key Information      Flags (see below)                      │
│  7       2      Key Length           16 (CCMP) or 32 (GCMP-256)            │
│  9       8      Replay Counter       Monotonically increasing               │
│  17      32     Key Nonce            ANonce or SNonce                       │
│  49      16     EAPOL-Key IV         Initialization vector (legacy)         │
│  65      8      Key RSC              Receive Sequence Counter               │
│  73      8      Reserved             Must be zero                           │
│  81      16     Key MIC              Message Integrity Code                 │
│  97      2      Key Data Length      Length of Key Data field               │
│  99      var    Key Data             RSN IE, GTK, etc. (may be encrypted)  │
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                    Key Information Bits                              │    │
│  ├─────────────────────────────────────────────────────────────────────┤    │
│  │  Bit 0-2:   Key Descriptor Version (1=HMAC-MD5/RC4, 2=HMAC-SHA1/AES)│    │
│  │  Bit 3:     Key Type (0=Group, 1=Pairwise)                          │    │
│  │  Bit 4-5:   Reserved                                                 │    │
│  │  Bit 6:     Install (set in M3)                                     │    │
│  │  Bit 7:     Key ACK (set by AP in M1, M3)                           │    │
│  │  Bit 8:     Key MIC (set when MIC is present)                       │    │
│  │  Bit 9:     Secure (set after PTK installed)                        │    │
│  │  Bit 10:    Error (set on MIC failure)                              │    │
│  │  Bit 11:    Request (set by STA to request new key)                 │    │
│  │  Bit 12:    Encrypted Key Data (set when Key Data is encrypted)     │    │
│  │  Bit 13:    SMK Message (for PeerKey)                               │    │
│  │  Bit 14-15: Reserved                                                 │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

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

| Device Type | DHCP Fingerprint (Option 55)               |
| ----------- | ------------------------------------------ |
| Windows 10  | 1,3,6,15,31,33,43,44,46,47,119,121,249,252 |
| macOS       | 1,121,3,6,15,119,252,95,44,46              |
| iOS         | 1,121,3,6,15,119,252,95,44,46              |
| Android     | 1,3,6,15,26,28,51,58,59,43                 |
| Linux       | 1,28,2,3,15,6,119,12,44,47,26,121,42       |

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
```
