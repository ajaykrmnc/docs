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

e
