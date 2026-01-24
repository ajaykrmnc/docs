## Phase 1: AP Initialization and Hotspot Enabling

When the hotspot is enabled on an Access Point, the following initialization sequence occurs:

### 1.1 System Initialization

[```](2026-01-08_```.md)
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

| Configuration Item | Description | Example |
|-------------------|-------------|---------|
| SSID | Network name | `MyHotspot` |
| Security Mode | Authentication type | `WPA2-PSK`, `WPA3-SAE`, `Open` |
| Channel | Operating frequency | `36` (5 GHz), `6` (2.4 GHz) |
| Bandwidth | Channel width | `20`, `40`, `80`, `160` MHz |
| VLAN | Network isolation | `100` |
| Captive Portal | Guest authentication | `Enabled/Disabled` |

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
