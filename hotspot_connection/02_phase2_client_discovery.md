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

| Criteria | Priority | Description |
|----------|----------|-------------|
| SSID Match | Highest | Matches preferred/configured network |
| Signal Strength (RSSI) | High | Stronger signal preferred |
| Security Level | High | WPA3 > WPA2 > WPA > Open |
| Band Preference | Medium | 5 GHz/6 GHz preferred for speed |
| Load | Low | Less congested AP preferred |

---

