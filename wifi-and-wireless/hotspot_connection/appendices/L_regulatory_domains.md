## Appendix L: Regulatory Domains

### L.1 Channel Availability by Region

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    2.4 GHz CHANNEL AVAILABILITY                              │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  Channel  Frequency   US    EU    JP    CN    AU                            │
│  ───────  ─────────   ──    ──    ──    ──    ──                            │
│     1     2412 MHz    ✓     ✓     ✓     ✓     ✓                             │
│     2     2417 MHz    ✓     ✓     ✓     ✓     ✓                             │
│     3     2422 MHz    ✓     ✓     ✓     ✓     ✓                             │
│     4     2427 MHz    ✓     ✓     ✓     ✓     ✓                             │
│     5     2432 MHz    ✓     ✓     ✓     ✓     ✓                             │
│     6     2437 MHz    ✓     ✓     ✓     ✓     ✓                             │
│     7     2442 MHz    ✓     ✓     ✓     ✓     ✓                             │
│     8     2447 MHz    ✓     ✓     ✓     ✓     ✓                             │
│     9     2452 MHz    ✓     ✓     ✓     ✓     ✓                             │
│    10     2457 MHz    ✓     ✓     ✓     ✓     ✓                             │
│    11     2462 MHz    ✓     ✓     ✓     ✓     ✓                             │
│    12     2467 MHz    ✗     ✓     ✓     ✓     ✓                             │
│    13     2472 MHz    ✗     ✓     ✓     ✓     ✓                             │
│    14     2484 MHz    ✗     ✗     ✓*    ✗     ✗                             │
│                                                                              │
│  * Japan channel 14 is 802.11b only                                         │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│                    5 GHz CHANNEL AVAILABILITY                                │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  UNII-1 (Indoor):                                                            │
│  Channel  Frequency   US    EU    JP    CN    AU    DFS                     │
│  ───────  ─────────   ──    ──    ──    ──    ──    ───                     │
│    36     5180 MHz    ✓     ✓     ✓     ✓     ✓     No                      │
│    40     5200 MHz    ✓     ✓     ✓     ✓     ✓     No                      │
│    44     5220 MHz    ✓     ✓     ✓     ✓     ✓     No                      │
│    48     5240 MHz    ✓     ✓     ✓     ✓     ✓     No                      │
│                                                                              │
│  UNII-2A (DFS):                                                              │
│    52     5260 MHz    ✓     ✓     ✓     ✓     ✓     Yes                     │
│    56     5280 MHz    ✓     ✓     ✓     ✓     ✓     Yes                     │
│    60     5300 MHz    ✓     ✓     ✓     ✓     ✓     Yes                     │
│    64     5320 MHz    ✓     ✓     ✓     ✓     ✓     Yes                     │
│                                                                              │
│  UNII-2C (DFS):                                                              │
│   100     5500 MHz    ✓     ✓     ✓     ✓     ✓     Yes                     │
│   104     5520 MHz    ✓     ✓     ✓     ✓     ✓     Yes                     │
│   108     5540 MHz    ✓     ✓     ✓     ✓     ✓     Yes                     │
│   112     5560 MHz    ✓     ✓     ✓     ✓     ✓     Yes                     │
│   116     5580 MHz    ✓     ✓     ✓     ✗     ✓     Yes                     │
│   120     5600 MHz    ✓     ✓     ✗     ✗     ✓     Yes                     │
│   124     5620 MHz    ✓     ✓     ✗     ✗     ✓     Yes                     │
│   128     5640 MHz    ✓     ✓     ✗     ✗     ✓     Yes                     │
│   132     5660 MHz    ✓     ✓     ✓     ✗     ✓     Yes                     │
│   136     5680 MHz    ✓     ✓     ✓     ✗     ✓     Yes                     │
│   140     5700 MHz    ✓     ✓     ✓     ✗     ✓     Yes                     │
│   144     5720 MHz    ✓     ✗     ✗     ✗     ✓     Yes                     │
│                                                                              │
│  UNII-3 (Outdoor):                                                           │
│   149     5745 MHz    ✓     ✓*    ✓     ✓     ✓     No                      │
│   153     5765 MHz    ✓     ✓*    ✓     ✓     ✓     No                      │
│   157     5785 MHz    ✓     ✓*    ✓     ✓     ✓     No                      │
│   161     5805 MHz    ✓     ✓*    ✓     ✓     ✓     No                      │
│   165     5825 MHz    ✓     ✓*    ✓     ✓     ✓     No                      │
│                                                                              │
│  * EU UNII-3 requires LPI (Low Power Indoor) or VLP                          │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│                    6 GHz CHANNEL AVAILABILITY                                │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  Region    Spectrum         Channels    Power Mode                          │
│  ──────    ────────         ────────    ──────────                          │
│  US        5925-7125 MHz    1-233       LPI, SP (with AFC), VLP             │
│  EU        5925-6425 MHz    1-93        LPI, VLP                            │
│  UK        5925-6425 MHz    1-93        LPI, VLP                            │
│  JP        5925-6425 MHz    1-93        LPI (pending)                       │
│  KR        5925-7125 MHz    1-233       LPI, SP (with AFC)                  │
│  AU        5925-6425 MHz    1-93        LPI, VLP                            │
│  BR        5925-7125 MHz    1-233       LPI, SP (with AFC)                  │
│                                                                              │
│  Power Modes:                                                                │
│  • LPI (Low Power Indoor): Indoor only, ~5 dBm/MHz EIRP                     │
│  • SP (Standard Power): With AFC, ~23 dBm/MHz EIRP                          │
│  • VLP (Very Low Power): Portable, ~-8 dBm/MHz EIRP                         │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### L.2 DFS (Dynamic Frequency Selection)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    DFS OPERATION                                             │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  DFS is required on channels 52-144 to protect radar systems.               │
│                                                                              │
│  CAC (Channel Availability Check):                                           │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │ • AP must listen for radar before transmitting                      │    │
│  │ • Duration: 60 seconds (1 minute) for most channels                 │    │
│  │ • Duration: 600 seconds (10 minutes) for weather radar channels     │    │
│  │   (120, 124, 128 in some regions)                                   │    │
│  │ • No transmission allowed during CAC                                │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  Radar Detection:                                                            │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │ • Continuous monitoring during operation                            │    │
│  │ • Must detect radar pulses with specific patterns                   │    │
│  │ • Detection probability: >60% for most patterns                     │    │
│  │ • False detection rate: <10%                                        │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  Channel Switch:                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │ • Must vacate channel within 10 seconds of radar detection          │    │
│  │ • Send Channel Switch Announcement (CSA) to clients                 │    │
│  │ • Move to non-DFS channel or perform CAC on new DFS channel         │    │
│  │ • Non-Occupancy Period: 30 minutes before returning to channel      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  Configuration:                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │ # hostapd.conf                                                      │    │
│  │ ieee80211d=1                                                        │    │
│  │ ieee80211h=1                                                        │    │
│  │ country_code=US                                                     │    │
│  │ channel=52                                                          │    │
│  │                                                                      │    │
│  │ # DFS debug                                                         │    │
│  │ iw reg get                                                          │    │
│  │ iw dev wlan0 info                                                   │    │
│  │ dmesg | grep -i radar                                               │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

