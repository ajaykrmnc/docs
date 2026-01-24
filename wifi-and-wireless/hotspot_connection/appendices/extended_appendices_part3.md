│  │  │ 802.11ax      DL + UL      8            8                  │     │    │
│  │  │ 802.11be      DL + UL      16           16                 │     │    │
│  │  └────────────────────────────────────────────────────────────┘     │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  Beamforming for MU-MIMO:                                                    │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  Sounding Procedure:                                                 │    │
│  │  1. AP sends NDP Announcement                                        │    │
│  │  2. AP sends NDP (Null Data Packet)                                  │    │
│  │  3. Clients measure channel and compute feedback                     │    │
│  │  4. AP polls each client for feedback                                │    │
│  │  5. Clients send Compressed Beamforming Report                       │    │
│  │  6. AP computes steering matrix                                      │    │
│  │  7. AP transmits with beamforming                                    │    │
│  │                                                                      │    │
│  │  ┌─────────────────────────────────────────────────────────────┐    │    │
│  │  │                                                              │    │    │
│  │  │  AP              Client A        Client B        Client C    │    │    │
│  │  │   │                 │               │               │        │    │    │
│  │  │   │ ── NDPA ────────────────────────────────────────>│       │    │    │
│  │  │   │ ── NDP ─────────────────────────────────────────>│       │    │    │
│  │  │   │                 │               │               │        │    │    │
│  │  │   │ ── Poll A ──────>│              │               │        │    │    │
│  │  │   │ <── Report A ───│               │               │        │    │    │
│  │  │   │                 │               │               │        │    │    │
│  │  │   │ ── Poll B ──────────────────────>│              │        │    │    │
│  │  │   │ <── Report B ───────────────────│               │        │    │    │
│  │  │   │                 │               │               │        │    │    │
│  │  │   │ ── Poll C ──────────────────────────────────────>│       │    │    │
│  │  │   │ <── Report C ───────────────────────────────────│        │    │    │
│  │  │   │                 │               │               │        │    │    │
│  │  │   │ ══ MU Data ═════════════════════════════════════>│       │    │    │
│  │  │   │    (Beamformed)                                  │       │    │    │
│  │  │                                                              │    │    │
│  │  └─────────────────────────────────────────────────────────────┘    │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Appendix CD: BSS Coloring

### CD.1 BSS Coloring Overview

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    BSS COLORING OVERVIEW                                     │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  Problem: Co-Channel Interference                                            │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  Without BSS Coloring:                                               │    │
│  │  ┌────────────────────────────────────────────────────────────┐     │    │
│  │  │                                                             │     │    │
│  │  │     AP1 (Ch 36)              AP2 (Ch 36)                    │     │    │
│  │  │         │                        │                          │     │    │
│  │  │         │ ── Tx ──>              │                          │     │    │
│  │  │         │                        │ (Defers - same channel)  │     │    │
│  │  │         │                        │                          │     │    │
│  │  │     Even weak signals from AP1 cause AP2 to defer           │     │    │
│  │  │                                                             │     │    │
│  │  └────────────────────────────────────────────────────────────┘     │    │
│  │                                                                      │    │
│  │  With BSS Coloring:                                                  │    │
│  │  ┌────────────────────────────────────────────────────────────┐     │    │
│  │  │                                                             │     │    │
│  │  │     AP1 (Ch 36, Color 1)     AP2 (Ch 36, Color 2)           │     │    │
│  │  │         │                        │                          │     │    │
│  │  │         │ ── Tx ──>              │ ── Tx ──>                │     │    │
│  │  │         │                        │                          │     │    │
│  │  │     Different colors = can transmit simultaneously          │     │    │
│  │  │     (if signal is below OBSS-PD threshold)                  │     │    │
│  │  │                                                             │     │    │
│  │  └────────────────────────────────────────────────────────────┘     │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  BSS Color Field:                                                            │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  Location: HE-SIG-A field in PHY header                              │    │
│  │  Size: 6 bits                                                        │    │
│  │  Values: 1-63 (0 = disabled)                                         │    │
│  │                                                                      │    │
│  │  # hostapd.conf                                                      │    │
│  │  he_bss_color=15                                                     │    │
│  │  he_bss_color_partial=0                                              │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  OBSS-PD (Overlapping BSS Packet Detect):                                    │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  Thresholds:                                                         │    │
│  │  - Intra-BSS (same color): -82 dBm (standard CCA)                    │    │
│  │  - Inter-BSS (different color): -62 to -82 dBm (adjustable)          │    │
│  │                                                                      │    │
│  │  Higher OBSS-PD threshold = more aggressive spatial reuse            │    │
│  │  Lower OBSS-PD threshold = more conservative, less interference      │    │
│  │                                                                      │    │
│  │  # hostapd.conf                                                      │    │
│  │  he_obss_pd_min_offset=20                                            │    │
│  │  he_obss_pd_max_offset=20                                            │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  BSS Color Collision:                                                        │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  Detection: AP detects frames with same color from different BSSID   │    │
│  │                                                                      │    │
│  │  Resolution:                                                         │    │
│  │  1. AP announces color change in beacon                              │    │
│  │  2. Countdown (similar to channel switch)                            │    │
│  │  3. AP switches to new color                                         │    │
│  │  4. Clients update color association                                 │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Appendix CE: Target Wake Time (TWT)

### CE.1 TWT Overview

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    TARGET WAKE TIME OVERVIEW                                 │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  Purpose:                                                                    │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  - Reduce power consumption for battery-powered devices              │    │
│  │  - Schedule wake times to reduce contention                          │    │
│  │  - Improve efficiency for IoT devices                                │    │
│  │  - Enable deterministic latency for time-sensitive applications      │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  TWT Types:                                                                  │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  ┌────────────────────────────────────────────────────────────┐     │    │
│  │  │ Type                Description                            │     │    │
│  │  │ ────                ───────────                            │     │    │
│  │  │ Individual TWT      Negotiated between AP and single STA   │     │    │
│  │  │ Broadcast TWT       AP announces schedule for all STAs     │     │    │
│  │  │ Triggered TWT       AP triggers transmission at TWT        │     │    │
│  │  │ Untriggered TWT     STA can transmit during TWT window     │     │    │
│  │  └────────────────────────────────────────────────────────────┘     │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  TWT Parameters:                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  ┌────────────────────────────────────────────────────────────┐     │    │
│  │  │ Parameter           Description                            │     │    │
│  │  │ ─────────           ───────────                            │     │    │
│  │  │ TWT Wake Interval   Time between wake periods              │     │    │
│  │  │ TWT Wake Duration   Length of wake period                  │     │    │
│  │  │ TWT Channel         Channel for TWT session                │     │    │
│  │  │ TWT Protection      Whether TWT is protected               │     │    │
│  │  │ TWT Flow ID         Identifier for TWT agreement           │     │    │
│  │  └────────────────────────────────────────────────────────────┘     │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  TWT Timeline:                                                               │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  Time ──────────────────────────────────────────────────────────>    │    │
│  │                                                                      │    │
│  │  ┌───┐     ┌───┐     ┌───┐     ┌───┐     ┌───┐     ┌───┐            │    │
│  │  │TWT│     │TWT│     │TWT│     │TWT│     │TWT│     │TWT│            │    │
│  │  │ 1 │     │ 1 │     │ 1 │     │ 1 │     │ 1 │     │ 1 │            │    │
│  │  └───┘     └───┘     └───┘     └───┘     └───┘     └───┘            │    │
│  │    │         │         │         │         │         │              │    │
│  │    │<──────>│         │<──────>│         │<──────>│                 │    │
│  │    Wake      Sleep     Wake      Sleep     Wake                     │    │
│  │    Interval            Interval            Interval                 │    │
│  │                                                                      │    │
│  │  ┌─────────────────────────────────────────────────────────────┐    │    │
│  │  │ Example: IoT sensor with 1 second wake interval             │    │    │
│  │  │                                                              │    │    │
│  │  │ Wake Duration: 5 ms                                          │    │    │
│  │  │ Wake Interval: 1000 ms                                       │    │    │
│  │  │ Duty Cycle: 0.5%                                             │    │    │
│  │  │ Power Savings: ~99.5%                                        │    │    │
│  │  └─────────────────────────────────────────────────────────────┘    │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  TWT Negotiation:                                                            │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  STA                                AP                               │    │
│  │   │                                  │                               │    │
│  │   │ ── TWT Setup Request ──────────>│                               │    │
│  │   │    (Requested parameters)        │                               │    │
│  │   │                                  │                               │    │
│  │   │ <── TWT Setup Response ─────────│                               │    │
│  │   │    (Accepted/Modified/Rejected)  │                               │    │
│  │   │                                  │                               │    │
│  │   │    ... TWT sessions ...          │                               │    │
│  │   │                                  │                               │    │
│  │   │ ── TWT Teardown ───────────────>│                               │    │
│  │   │    (End TWT agreement)           │                               │    │
│  │   │                                  │                               │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  Configuration:                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  # hostapd.conf                                                      │    │
│  │  ieee80211ax=1                                                       │    │
│  │  he_twt_required=0                                                   │    │
│  │  he_twt_responder=1                                                  │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Document Revision History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2026-01-08 | Auto-generated | Initial document creation |
| 1.1 | 2026-01-08 | Auto-generated | Added packet capture analysis, regulatory domains, client compatibility |
| 1.2 | 2026-01-08 | Auto-generated | Added EAP methods, band steering, load balancing, mesh networking, power save |
| 1.3 | 2026-01-08 | Auto-generated | Added RADIUS attributes, debug commands, troubleshooting flowchart, quick reference |
| 1.4 | 2026-01-08 | Auto-generated | Added WiFi 7 features, Hotspot 2.0 deep dive, glossary, standards reference |
| 1.5 | 2026-01-08 | Auto-generated | Added security attacks, performance optimization, complete hostapd config |
| 1.6 | 2026-01-08 | Auto-generated | Added frame formats, information elements, status/reason codes |
| 1.7 | 2026-01-08 | Auto-generated | Added vendor extensions, debugging/logging, packet capture commands |
| 1.8 | 2026-01-08 | Auto-generated | Added test case reference, regulatory domain deep dive |
| 1.9 | 2026-01-08 | Auto-generated | Added action frame reference, error scenarios and troubleshooting |
| 2.0 | 2026-01-08 | Auto-generated | Added Wireshark filter reference, complete configuration examples |
| 2.1 | 2026-01-08 | Auto-generated | Added performance benchmarks, client device compatibility matrix |
| 2.2 | 2026-01-08 | Auto-generated | Added WiFi Alliance certification, security checklist, capacity planning |
| 2.3 | 2026-01-08 | Auto-generated | Added antenna/RF considerations, troubleshooting trees, timing diagrams |
| 2.4 | 2026-01-08 | Auto-generated | Added QoS/WMM, deployment topologies, compliance, advanced debugging |
| 2.5 | 2026-01-08 | Auto-generated | Added supplicant config, VLAN, rate limiting, HA, IoT profiling |
| 2.6 | 2026-01-08 | Auto-generated | Added captive portal, location services, spectrum analysis, migration, API |
| 2.7 | 2026-01-08 | Auto-generated | Added multicast, VoWiFi, enterprise integration, monitoring, disaster recovery |
| 2.8 | 2026-01-08 | Auto-generated | Added WIDS, cloud management, performance testing, compliance, checklists |
| 2.9 | 2026-01-08 | Auto-generated | Added outdoor WiFi, stadium/venue, healthcare, education, retail, industrial |
| 3.0 | 2026-01-08 | Auto-generated | Added WiFi 6E/7 deep dive, OFDMA, MU-MIMO, BSS coloring, TWT |
| 3.1 | 2026-01-08 | Auto-generated | Added WiFi 7 MLO, puncturing, 4K-QAM, multi-RU, enhanced security |

---

## Appendix CF: WiFi 7 (802.11be) Deep Dive

### CF.1 Multi-Link Operation (MLO)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    MULTI-LINK OPERATION (MLO)                                │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  MLO Concept:                                                                │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  Traditional (Single Link):                                          │    │
│  │  ┌────────────────────────────────────────────────────────────┐     │    │
│  │  │                                                             │     │    │
│  │  │     AP                              Client                  │     │    │
│  │  │      │                                 │                    │     │    │
│  │  │      │ ═══════ 5 GHz Link ═══════════>│                    │     │    │
│  │  │      │                                 │                    │     │    │
│  │  │     One link at a time                                      │     │    │
│  │  │                                                             │     │    │
│  │  └────────────────────────────────────────────────────────────┘     │    │
│  │                                                                      │    │
│  │  MLO (Multi-Link):                                                   │    │
│  │  ┌────────────────────────────────────────────────────────────┐     │    │
│  │  │                                                             │     │    │
│  │  │     MLD-AP                          MLD-Client              │     │    │
│  │  │      │                                 │                    │     │    │
│  │  │      │ ═══════ 2.4 GHz Link ══════════>│                   │     │    │
│  │  │      │ ═══════ 5 GHz Link ════════════>│                   │     │    │
│  │  │      │ ═══════ 6 GHz Link ════════════>│                   │     │    │
│  │  │      │                                 │                    │     │    │
│  │  │     Multiple links simultaneously                           │     │    │
│  │  │                                                             │     │    │
│  │  └────────────────────────────────────────────────────────────┘     │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  MLO Benefits:                                                               │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  ┌────────────────────────────────────────────────────────────┐     │    │
│  │  │ Benefit             Description                            │     │    │
│  │  │ ───────             ───────────                            │     │    │
│  │  │ Aggregation         Combine bandwidth of multiple links    │     │    │
│  │  │ Low Latency         Use least congested link               │     │    │
│  │  │ Reliability         Failover between links                 │     │    │
│  │  │ Load Balancing      Distribute traffic across links        │     │    │
│  │  │ Seamless Roaming    No handoff between bands               │     │    │
│  │  └────────────────────────────────────────────────────────────┘     │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  MLO Modes:                                                                  │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  ┌────────────────────────────────────────────────────────────┐     │    │
│  │  │ Mode                Description                            │     │    │
│  │  │ ────                ───────────                            │     │    │
│  │  │ STR (Simultaneous   Both links transmit/receive at same    │     │    │
│  │  │ Transmit/Receive)   time (requires sufficient isolation)   │     │    │
│  │  │                                                             │     │    │
│  │  │ NSTR (Non-STR)      Only one link active at a time         │     │    │
│  │  │                     (for devices with limited isolation)   │     │    │
│  │  │                                                             │     │    │
│  │  │ eMLSR (Enhanced     Dynamic switching between links        │     │    │
│  │  │ Multi-Link Single   for low-latency applications           │     │    │
│  │  │ Radio)                                                      │     │    │
│  │  └────────────────────────────────────────────────────────────┘     │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  MLD Architecture:                                                           │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  ┌─────────────────────────────────────────────────────────────┐    │    │
│  │  │                                                              │    │    │
│  │  │  ┌─────────────────────────────────────────────────────┐    │    │    │
│  │  │  │                    MLD (Multi-Link Device)          │    │    │    │
│  │  │  │                                                      │    │    │    │
│  │  │  │  MLD MAC Address: aa:bb:cc:dd:ee:ff                  │    │    │    │
│  │  │  │                                                      │    │    │    │
│  │  │  │  ┌──────────┐  ┌──────────┐  ┌──────────┐           │    │    │    │
│  │  │  │  │ Link 1   │  │ Link 2   │  │ Link 3   │           │    │    │    │
│  │  │  │  │ 2.4 GHz  │  │ 5 GHz    │  │ 6 GHz    │           │    │    │    │
│  │  │  │  │ MAC: 11  │  │ MAC: 22  │  │ MAC: 33  │           │    │    │    │
│  │  │  │  └──────────┘  └──────────┘  └──────────┘           │    │    │    │
│  │  │  │                                                      │    │    │    │
│  │  │  └─────────────────────────────────────────────────────┘    │    │    │
│  │  │                                                              │    │    │
│  │  │  Each link has its own MAC address                          │    │    │
│  │  │  MLD MAC is used for upper layer identification              │    │    │
│  │  │                                                              │    │    │
│  │  └─────────────────────────────────────────────────────────────┘    │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  MLO Association:                                                            │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  MLD-STA                              MLD-AP                         │    │
│  │     │                                    │                           │    │
│  │     │ ── ML Probe Request ──────────────>│                          │    │
│  │     │    (Request info on all links)     │                           │    │
│  │     │                                    │                           │    │
│  │     │ <── ML Probe Response ─────────────│                          │    │
│  │     │    (Info on all available links)   │                           │    │
│  │     │                                    │                           │    │
│  │     │ ── Authentication ────────────────>│ (on one link)            │    │
│  │     │ <── Authentication ────────────────│                          │    │
│  │     │                                    │                           │    │
│  │     │ ── ML Association Request ────────>│                          │    │
│  │     │    (Request multiple links)        │                           │    │
│  │     │                                    │                           │    │
│  │     │ <── ML Association Response ───────│                          │    │
│  │     │    (Confirm links, assign AIDs)    │                           │    │
│  │     │                                    │                           │    │
│  │     │ ══ 4-Way Handshake ════════════════│ (on one link)            │    │
│  │     │                                    │                           │    │
│  │     │ ══ Data on Link 1 ═════════════════│                          │    │
│  │     │ ══ Data on Link 2 ═════════════════│                          │    │
│  │     │ ══ Data on Link 3 ═════════════════│                          │    │
│  │     │                                    │                           │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### CF.2 Preamble Puncturing

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    PREAMBLE PUNCTURING                                       │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  Problem: Wideband Channel Availability                                      │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  Without Puncturing:                                                 │    │
│  │  ┌────────────────────────────────────────────────────────────┐     │    │
│  │  │                                                             │     │    │
│  │  │  320 MHz Channel                                            │     │    │
│  │  │  ┌────────────────────────────────────────────────────────┐│     │    │
│  │  │  │ 20 │ 20 │ 20 │ 20 │ 20 │ 20 │ 20 │ 20 │ 20 │ 20 │ 20 │ ││     │    │
│  │  │  │ OK │ OK │ OK │ OK │BUSY│ OK │ OK │ OK │ OK │ OK │ OK │ ││     │    │
│  │  │  └────────────────────────────────────────────────────────┘│     │    │
│  │  │                        ▲                                    │     │    │
│  │  │                        │                                    │     │    │
│  │  │              Incumbent/Radar detected                       │     │    │
│  │  │              Cannot use 320 MHz channel                     │     │    │
│  │  │                                                             │     │    │
│  │  └────────────────────────────────────────────────────────────┘     │    │
│  │                                                                      │    │
│  │  With Puncturing:                                                    │    │
│  │  ┌────────────────────────────────────────────────────────────┐     │    │
│  │  │                                                             │     │    │
│  │  │  320 MHz Channel (with punctured 20 MHz)                    │     │    │
│  │  │  ┌────────────────────────────────────────────────────────┐│     │    │
│  │  │  │ 20 │ 20 │ 20 │ 20 │ XX │ 20 │ 20 │ 20 │ 20 │ 20 │ 20 │ ││     │    │
│  │  │  │ OK │ OK │ OK │ OK │PUNC│ OK │ OK │ OK │ OK │ OK │ OK │ ││     │    │
│  │  │  └────────────────────────────────────────────────────────┘│     │    │
│  │  │                        ▲                                    │     │    │
│  │  │                        │                                    │     │    │
│  │  │              Punctured subchannel                           │     │    │
│  │  │              Still use 300 MHz effective bandwidth          │     │    │
│  │  │                                                             │     │    │
│  │  └────────────────────────────────────────────────────────────┘     │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  Puncturing Patterns:                                                        │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  ┌────────────────────────────────────────────────────────────┐     │    │
│  │  │ Channel Width    Puncturable Units    Max Punctured        │     │    │
│  │  │ ─────────────    ─────────────────    ────────────         │     │    │
│  │  │ 80 MHz           20 MHz               1 x 20 MHz           │     │    │
│  │  │ 160 MHz          20 MHz               2 x 20 MHz           │     │    │
│  │  │ 320 MHz          40 MHz               2 x 40 MHz           │     │    │
│  │  └────────────────────────────────────────────────────────────┘     │    │
│  │                                                                      │    │
│  │  Note: Primary 20 MHz cannot be punctured                            │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### CF.3 4096-QAM (4K-QAM)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    4096-QAM (4K-QAM)                                         │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  QAM Evolution:                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  ┌────────────────────────────────────────────────────────────┐     │    │
│  │  │ Standard      Max QAM       Bits/Symbol    Improvement     │     │    │
│  │  │ ────────      ───────       ───────────    ───────────     │     │    │
│  │  │ 802.11a/g     64-QAM        6 bits         Baseline        │     │    │
│  │  │ 802.11n       64-QAM        6 bits         -               │     │    │
│  │  │ 802.11ac      256-QAM       8 bits         +33%            │     │    │
│  │  │ 802.11ax      1024-QAM      10 bits        +25%            │     │    │
│  │  │ 802.11be      4096-QAM      12 bits        +20%            │     │    │
│  │  └────────────────────────────────────────────────────────────┘     │     │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  Constellation Diagram:                                                      │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  64-QAM (8x8 = 64 points):                                           │    │
│  │  ┌────────────────────────────────────────────────────────────┐     │    │
│  │  │  ●  ●  ●  ●  ●  ●  ●  ●                                    │     │    │
│  │  │  ●  ●  ●  ●  ●  ●  ●  ●                                    │     │    │
│  │  │  ●  ●  ●  ●  ●  ●  ●  ●                                    │     │    │
│  │  │  ●  ●  ●  ●  ●  ●  ●  ●                                    │     │    │
│  │  │  ●  ●  ●  ●  ●  ●  ●  ●                                    │     │    │
│  │  │  ●  ●  ●  ●  ●  ●  ●  ●                                    │     │    │
│  │  │  ●  ●  ●  ●  ●  ●  ●  ●                                    │     │    │
│  │  │  ●  ●  ●  ●  ●  ●  ●  ●                                    │     │    │
│  │  └────────────────────────────────────────────────────────────┘     │    │
│  │                                                                      │    │
│  │  4096-QAM (64x64 = 4096 points):                                     │    │
│  │  ┌────────────────────────────────────────────────────────────┐     │    │
│  │  │  ████████████████████████████████████████████████████████  │     │    │
│  │  │  ████████████████████████████████████████████████████████  │     │    │
│  │  │  ████████████████████████████████████████████████████████  │     │    │
│  │  │  ████████████████████████████████████████████████████████  │     │    │
│  │  │  ████████████████████████████████████████████████████████  │     │    │
│  │  │  ████████████████████████████████████████████████████████  │     │    │
│  │  │  ████████████████████████████████████████████████████████  │     │    │
│  │  │  ████████████████████████████████████████████████████████  │     │    │
│  │  │  (Points are so dense they appear as solid block)          │     │    │
│  │  └────────────────────────────────────────────────────────────┘     │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  SNR Requirements:                                                           │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  ┌────────────────────────────────────────────────────────────┐     │    │
│  │  │ Modulation        Min SNR (approx)    Typical Range        │     │    │
│  │  │ ──────────        ────────────────    ─────────────        │     │    │
│  │  │ BPSK              6 dB                Very far             │     │    │
│  │  │ QPSK              9 dB                Far                  │     │    │
│  │  │ 16-QAM            15 dB               Medium               │     │    │
│  │  │ 64-QAM            21 dB               Medium-close         │     │    │
│  │  │ 256-QAM           27 dB               Close                │     │    │
│  │  │ 1024-QAM          33 dB               Very close           │     │    │
│  │  │ 4096-QAM          39 dB               Extremely close      │     │    │
│  │  └────────────────────────────────────────────────────────────┘     │    │
│  │                                                                      │    │
│  │  4K-QAM requires excellent signal quality (close range, low noise)  │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Appendix CG: Enhanced Security Features

### CG.1 SAE (Simultaneous Authentication of Equals)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    SAE (WPA3-PERSONAL)                                       │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  SAE vs PSK:                                                                 │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  ┌────────────────────────────────────────────────────────────┐     │    │
│  │  │ Feature             WPA2-PSK           WPA3-SAE            │     │    │
│  │  │ ───────             ────────           ────────            │     │    │
│  │  │ Key Derivation      PBKDF2             Dragonfly           │     │    │
│  │  │ Offline Attack      Vulnerable         Resistant           │     │    │
│  │  │ Forward Secrecy     No                 Yes                 │     │    │
│  │  │ Dictionary Attack   Vulnerable         Resistant           │     │    │
│  │  │ PMKID Attack        Vulnerable         Not applicable      │     │    │
│  │  └────────────────────────────────────────────────────────────┘     │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  SAE Handshake (Dragonfly):                                                  │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  STA                                AP                               │    │
│  │   │                                  │                               │    │
│  │   │ ── Commit (scalar, element) ────>│                              │    │
│  │   │                                  │                               │    │
│  │   │ <── Commit (scalar, element) ────│                              │    │
│  │   │                                  │                               │    │
│  │   │    Both compute shared secret    │                               │    │
│  │   │    (without revealing password)  │                               │    │
│  │   │                                  │                               │    │
│  │   │ ── Confirm (confirm value) ─────>│                              │    │
│  │   │                                  │                               │    │
│  │   │ <── Confirm (confirm value) ─────│                              │    │
│  │   │                                  │                               │    │
│  │   │    PMK established               │                               │    │
│  │   │                                  │                               │    │
│  │   │ ══ 4-Way Handshake ══════════════│                              │    │
│  │   │                                  │                               │    │
│  │                                                                      │    │
│  │  Key Properties:                                                     │    │
│  │  - Password never transmitted                                        │    │
│  │  - Each session has unique PMK                                       │    │
│  │  - Resistant to offline dictionary attacks                           │    │
│  │  - Forward secrecy (past sessions protected)                         │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  SAE Configuration:                                                          │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  # hostapd.conf for WPA3-SAE only                                    │    │
│  │  wpa=2                                                               │    │
│  │  wpa_key_mgmt=SAE                                                    │    │
│  │  wpa_passphrase=MySecurePassword123                                  │    │
│  │  ieee80211w=2                                                        │    │
│  │  sae_require_mfp=1                                                   │    │
│  │  sae_pwe=2                                                           │    │
│  │                                                                      │    │
│  │  # hostapd.conf for WPA3-SAE Transition (WPA2+WPA3)                  │    │
│  │  wpa=2                                                               │    │
│  │  wpa_key_mgmt=WPA-PSK SAE                                            │    │
│  │  wpa_passphrase=MySecurePassword123                                  │    │
│  │  ieee80211w=1                                                        │    │
│  │  sae_require_mfp=1                                                   │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  SAE Groups:                                                                 │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  ┌────────────────────────────────────────────────────────────┐     │    │
│  │  │ Group    Curve/Algorithm         Security Level            │     │    │
│  │  │ ─────    ───────────────         ──────────────            │     │    │
│  │  │ 19       ECC P-256               128-bit (default)         │     │    │
│  │  │ 20       ECC P-384               192-bit                   │     │    │
│  │  │ 21       ECC P-521               256-bit                   │     │    │
│  │  │ 15       MODP 3072-bit           128-bit                   │     │    │
│  │  │ 16       MODP 4096-bit           152-bit                   │     │    │
│  │  └────────────────────────────────────────────────────────────┘     │    │
│  │                                                                      │    │
│  │  # hostapd.conf                                                      │    │
│  │  sae_groups=19 20 21                                                 │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### CG.2 OWE (Opportunistic Wireless Encryption)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    OWE (ENHANCED OPEN)                                       │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  OWE Purpose:                                                                │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  Problem: Open networks have no encryption                           │    │
│  │  Solution: OWE provides encryption without authentication            │    │
│  │                                                                      │    │
│  │  ┌────────────────────────────────────────────────────────────┐     │    │
│  │  │ Feature             Open Network       OWE                 │     │    │
│  │  │ ───────             ────────────       ───                 │     │    │
│  │  │ Password Required   No                 No                  │     │    │
│  │  │ Encryption          None               Yes (AES)           │     │    │
│  │  │ Eavesdropping       Possible           Protected           │     │    │
│  │  │ User Experience     Same               Same                │     │    │
│  │  └────────────────────────────────────────────────────────────┘     │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  OWE Handshake:                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  STA                                AP                               │    │
│  │   │                                  │                               │    │
│  │   │ ── Association Request ─────────>│                              │    │
│  │   │    (STA's DH public key)         │                               │    │
│  │   │                                  │                               │    │
│  │   │ <── Association Response ────────│                              │    │
│  │   │    (AP's DH public key)          │                               │    │
│  │   │                                  │                               │    │
│  │   │    Both compute PMK from DH      │                               │    │
│  │   │                                  │                               │    │
│  │   │ ══ 4-Way Handshake ══════════════│                              │    │
│  │   │                                  │                               │    │
│  │   │ ══ Encrypted Data ═══════════════│                              │    │
│  │   │                                  │                               │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  OWE Configuration:                                                          │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  # hostapd.conf for OWE only                                         │    │
│  │  wpa=2                                                               │    │
│  │  wpa_key_mgmt=OWE                                                    │    │
│  │  rsn_pairwise=CCMP                                                   │    │
│  │  ieee80211w=2                                                        │    │
│  │                                                                      │    │
│  │  # hostapd.conf for OWE Transition (Open + OWE)                      │    │
│  │  # Requires two BSSes                                                │    │
│  │                                                                      │    │
│  │  # BSS 1: Open network (visible)                                     │    │
│  │  ssid=GuestNetwork                                                   │    │
│  │  owe_transition_bssid=02:00:00:00:00:01                              │    │
│  │  owe_transition_ssid="GuestNetwork-OWE"                              │    │
│  │                                                                      │    │
│  │  # BSS 2: OWE network (hidden)                                       │    │
│  │  bss=wlan0_1                                                         │    │
│  │  ssid=GuestNetwork-OWE                                               │    │
│  │  ignore_broadcast_ssid=1                                             │    │
│  │  wpa=2                                                               │    │
│  │  wpa_key_mgmt=OWE                                                    │    │
│  │  owe_transition_bssid=02:00:00:00:00:00                              │    │
│  │  owe_transition_ssid="GuestNetwork"                                  │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### CG.3 Management Frame Protection (802.11w)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    MANAGEMENT FRAME PROTECTION (MFP)                         │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  Protected Frame Types:                                                      │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  ┌────────────────────────────────────────────────────────────┐     │    │
│  │  │ Frame Type              Protected    Attack Prevented      │     │    │
│  │  │ ──────────              ─────────    ────────────────      │     │    │
│  │  │ Deauthentication        Yes          Deauth flood          │     │    │
│  │  │ Disassociation          Yes          Disassoc flood        │     │    │
│  │  │ Action frames           Yes          Various               │     │    │
│  │  │ Robust Action frames    Yes          Various               │     │    │
│  │  │ Beacon                  No*          -                     │     │    │
│  │  │ Probe Request           No           -                     │     │    │
│  │  │ Probe Response          No           -                     │     │    │
│  │  │ Authentication          No           -                     │     │    │
│  │  │ Association             No           -                     │     │    │
│  │  └────────────────────────────────────────────────────────────┘     │    │
│  │                                                                      │    │
│  │  * Beacon Protection added in 802.11ax                               │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  MFP Keys:                                                                   │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  IGTK (Integrity Group Temporal Key):                                │    │
│  │  - Used for broadcast/multicast management frames                    │    │
│  │  - Distributed during 4-way handshake (Message 3)                    │    │
│  │  - Uses BIP (Broadcast Integrity Protocol)                           │    │
│  │                                                                      │    │
│  │  BIGTK (Beacon Integrity Group Temporal Key):                        │    │
│  │  - Used for beacon protection (802.11ax+)                            │    │
│  │  - Separate from IGTK                                                │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  MFP Configuration:                                                          │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  # hostapd.conf                                                      │    │
│  │  ieee80211w=0    # Disabled                                          │    │
│  │  ieee80211w=1    # Optional (capable but not required)               │    │
│  │  ieee80211w=2    # Required (mandatory for WPA3)                     │    │
│  │                                                                      │    │
│  │  # Group management cipher                                           │    │
│  │  group_mgmt_cipher=AES-128-CMAC    # Default                         │    │
│  │  group_mgmt_cipher=BIP-GMAC-128    # Alternative                     │    │
│  │  group_mgmt_cipher=BIP-GMAC-256    # Higher security                 │    │
│  │  group_mgmt_cipher=BIP-CMAC-256    # Higher security                 │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  SA Query (Security Association Query):                                      │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  Purpose: Verify if deauth/disassoc is legitimate                    │    │
│  │                                                                      │    │
│  │  Flow:                                                               │    │
│  │  1. STA receives unprotected deauth                                  │    │
│  │  2. STA sends SA Query Request to AP                                 │    │
│  │  3. If AP responds with SA Query Response, deauth was fake           │    │
│  │  4. If no response, deauth may be legitimate                         │    │
│  │                                                                      │    │
│  │  # hostapd.conf                                                      │    │
│  │  assoc_sa_query_max_timeout=1000                                     │    │
│  │  assoc_sa_query_retry_timeout=201                                    │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Document Revision History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2026-01-08 | Auto-generated | Initial document creation |
| 1.1 | 2026-01-08 | Auto-generated | Added packet capture analysis, regulatory domains, client compatibility |
| 1.2 | 2026-01-08 | Auto-generated | Added EAP methods, band steering, load balancing, mesh networking, power save |
| 1.3 | 2026-01-08 | Auto-generated | Added RADIUS attributes, debug commands, troubleshooting flowchart, quick reference |
| 1.4 | 2026-01-08 | Auto-generated | Added WiFi 7 features, Hotspot 2.0 deep dive, glossary, standards reference |
| 1.5 | 2026-01-08 | Auto-generated | Added security attacks, performance optimization, complete hostapd config |
| 1.6 | 2026-01-08 | Auto-generated | Added frame formats, information elements, status/reason codes |
| 1.7 | 2026-01-08 | Auto-generated | Added vendor extensions, debugging/logging, packet capture commands |
| 1.8 | 2026-01-08 | Auto-generated | Added test case reference, regulatory domain deep dive |
| 1.9 | 2026-01-08 | Auto-generated | Added action frame reference, error scenarios and troubleshooting |
| 2.0 | 2026-01-08 | Auto-generated | Added Wireshark filter reference, complete configuration examples |
| 2.1 | 2026-01-08 | Auto-generated | Added performance benchmarks, client device compatibility matrix |
| 2.2 | 2026-01-08 | Auto-generated | Added WiFi Alliance certification, security checklist, capacity planning |
| 2.3 | 2026-01-08 | Auto-generated | Added antenna/RF considerations, troubleshooting trees, timing diagrams |
| 2.4 | 2026-01-08 | Auto-generated | Added QoS/WMM, deployment topologies, compliance, advanced debugging |
| 2.5 | 2026-01-08 | Auto-generated | Added supplicant config, VLAN, rate limiting, HA, IoT profiling |
| 2.6 | 2026-01-08 | Auto-generated | Added captive portal, location services, spectrum analysis, migration, API |
| 2.7 | 2026-01-08 | Auto-generated | Added multicast, VoWiFi, enterprise integration, monitoring, disaster recovery |
| 2.8 | 2026-01-08 | Auto-generated | Added WIDS, cloud management, performance testing, compliance, checklists |
| 2.9 | 2026-01-08 | Auto-generated | Added outdoor WiFi, stadium/venue, healthcare, education, retail, industrial |
| 3.0 | 2026-01-08 | Auto-generated | Added WiFi 6E/7 deep dive, OFDMA, MU-MIMO, BSS coloring, TWT |
| 3.1 | 2026-01-08 | Auto-generated | Added WiFi 7 MLO, puncturing, 4K-QAM, multi-RU, enhanced security |
| 3.2 | 2026-01-08 | Auto-generated | Added FILS, DPP, enterprise security, certificate management |

---

## Appendix CH: FILS (Fast Initial Link Setup)

### CH.1 FILS Overview

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    FILS OVERVIEW                                             │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  Purpose:                                                                    │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  - Reduce initial connection time for 802.1X networks                │    │
│  │  - Target: < 100ms total connection time                             │    │
│  │  - Combines authentication and association                           │    │
│  │  - Useful for IoT, VoWiFi, and high-mobility scenarios               │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  Connection Time Comparison:                                                 │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  ┌────────────────────────────────────────────────────────────┐     │    │
│  │  │ Method              Typical Time    Frames                 │     │    │
│  │  │ ──────              ────────────    ──────                 │     │    │
│  │  │ Full 802.1X         1-3 seconds     20+ frames             │     │    │
│  │  │ PMKSA Caching       200-500 ms      8 frames               │     │    │
│  │  │ 802.11r FT          50-100 ms       4 frames               │     │    │
│  │  │ FILS                < 100 ms        4 frames               │     │    │
│  │  └────────────────────────────────────────────────────────────┘     │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  FILS Variants:                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  ┌────────────────────────────────────────────────────────────┐     │    │
│  │  │ Variant             Description                            │     │    │
│  │  │ ───────             ───────────                            │     │    │
│  │  │ FILS-SHA256         Basic FILS with SHA-256                │     │    │
│  │  │ FILS-SHA384         FILS with SHA-384 (higher security)    │     │    │
│  │  │ FILS-SK-PFS         FILS with Perfect Forward Secrecy      │     │    │
│  │  └────────────────────────────────────────────────────────────┘     │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  FILS Authentication Flow:                                                   │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  STA                    AP                    RADIUS                 │    │
│  │   │                      │                       │                   │    │
│  │   │ ── Auth Request ────>│                       │                   │    │
│  │   │    (EAP-Initiate)    │                       │                   │    │
│  │   │                      │ ── Access-Request ───>│                   │    │
│  │   │                      │    (ERP)              │                   │    │
│  │   │                      │                       │                   │    │
│  │   │                      │ <── Access-Accept ────│                   │    │
│  │   │                      │    (rMSK)             │                   │    │
│  │   │                      │                       │                   │    │
│  │   │ <── Auth Response ───│                       │                   │    │
│  │   │    (EAP-Finish)      │                       │                   │    │
│  │   │                      │                       │                   │    │
│  │   │ ── Assoc Request ───>│                       │                   │    │
│  │   │    (FILS Session,    │                       │                   │    │
│  │   │     Key Confirm,     │                       │                   │    │
│  │   │     encrypted data)  │                       │                   │    │
│  │   │                      │                       │                   │    │
│  │   │ <── Assoc Response ──│                       │                   │    │
│  │   │    (Key Confirm,     │                       │                   │    │
│  │   │     GTK, encrypted)  │                       │                   │    │
│  │   │                      │                       │                   │    │
│  │   │ ══ Data ═════════════│                       │                   │    │
│  │   │                      │                       │                   │    │
│  │                                                                      │    │
│  │  Note: No separate 4-way handshake needed!                           │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  ERP (EAP Re-authentication Protocol):                                       │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  - Prerequisite for FILS                                             │    │
│  │  - Derives rRK (re-authentication Root Key) from MSK                 │    │
│  │  - rRK used to derive rMSK for fast re-authentication                │    │
│  │  - Stored on RADIUS server for domain-wide roaming                   │    │
│  │                                                                      │    │
│  │  Key Hierarchy:                                                      │    │
│  │  MSK ──> rRK (re-auth Root Key)                                      │    │
│  │           │                                                          │    │
│  │           └──> rIK (re-auth Integrity Key)                           │    │
│  │           └──> rMSK (re-auth MSK) ──> PMK                            │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  FILS Configuration:                                                         │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  # hostapd.conf                                                      │    │
│  │  wpa=2                                                               │    │
│  │  wpa_key_mgmt=FILS-SHA256 FILS-SHA384                                │    │
│  │  ieee8021x=1                                                         │    │
│  │  auth_server_addr=192.168.1.10                                       │    │
│  │  auth_server_port=1812                                               │    │
│  │  auth_server_shared_secret=secret                                    │    │
│  │  erp_domain=example.com                                              │    │
│  │  fils_realm=example.com                                              │    │
│  │  fils_cache_id=1234                                                  │    │
│  │  fils_hlp_wait_time=30                                               │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Appendix CI: DPP (Device Provisioning Protocol)

### CI.1 DPP Overview

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    DPP (EASY CONNECT) OVERVIEW                               │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  Purpose:                                                                    │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  - Simplify WiFi provisioning for IoT devices                        │    │
│  │  - Replace WPS (WiFi Protected Setup)                                │    │
│  │  - Use QR codes, NFC, or Bluetooth for bootstrapping                 │    │
│  │  - Secure provisioning without typing passwords                      │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  DPP Roles:                                                                  │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  ┌────────────────────────────────────────────────────────────┐     │    │
│  │  │ Role                Description                            │     │    │
│  │  │ ────                ───────────                            │     │    │
│  │  │ Configurator        Device that provisions others          │     │    │
│  │  │                     (typically smartphone or AP)           │     │    │
│  │  │                                                             │     │    │
│  │  │ Enrollee            Device being provisioned               │     │    │
│  │  │                     (IoT device, new client)               │     │    │
│  │  │                                                             │     │    │
│  │  │ Responder           Device responding to DPP auth          │     │    │
│  │  │                     (can be Configurator or Enrollee)      │     │    │
│  │  │                                                             │     │    │
│  │  │ Initiator           Device starting DPP auth               │     │    │
│  │  │                     (can be Configurator or Enrollee)      │     │    │
│  │  └────────────────────────────────────────────────────────────┘     │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  DPP Bootstrapping Methods:                                                  │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  ┌────────────────────────────────────────────────────────────┐     │    │
│  │  │ Method              Description                            │     │    │
│  │  │ ──────              ───────────                            │     │    │
│  │  │ QR Code             Scan QR code on device                 │     │    │
│  │  │ NFC                 Tap devices together                   │     │    │
│  │  │ BLE                 Bluetooth Low Energy exchange          │     │    │
│  │  │ PKEX                Public Key Exchange (password-based)   │     │    │
│  │  │ Cloud               Cloud-based bootstrapping              │     │    │
│  │  └────────────────────────────────────────────────────────────┘     │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  DPP QR Code Format:                                                         │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  DPP:C:81/1;M:aabbccddeeff;K:MDkwEwYHKoZIzj0CAQYIKoZIzj0DAQcD       │    │
│  │  IgADIgACJQO8gLsRgMLJyQO5daPFzWF8052bwYwFYS8Ej2MmQQ==;;              │    │
│  │                                                                      │    │
│  │  Components:                                                         │    │
│  │  - C: Channel/Operating Class (81/1 = 2.4 GHz channel 1)             │    │
│  │  - M: MAC address                                                    │    │
│  │  - K: Public key (base64 encoded)                                    │    │
│  │  - I: Information (optional, device info)                            │    │
│  │  - V: Version (optional)                                             │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  DPP Protocol Flow:                                                          │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  Configurator              Enrollee                AP                │    │
│  │       │                       │                     │                │    │
│  │       │ ── Scan QR Code ─────>│                     │                │    │
│  │       │    (Get public key)   │                     │                │    │
│  │       │                       │                     │                │    │
│  │       │ ══ DPP Auth Request ══>│                    │                │    │
│  │       │                       │                     │                │    │
│  │       │ <══ DPP Auth Response ═│                    │                │    │
│  │       │                       │                     │                │    │
│  │       │ ══ DPP Auth Confirm ══>│                    │                │    │
│  │       │                       │                     │                │    │
│  │       │ ══ DPP Config Request ═│                    │                │    │
│  │       │    (Request network)  │                     │                │    │
│  │       │                       │                     │                │    │
│  │       │ <══ DPP Config Response│                    │                │    │
│  │       │    (Network config)   │                     │                │    │
│  │       │                       │                     │                │    │
│  │       │                       │ ── Connect ────────>│                │    │
│  │       │                       │    (Using config)   │                │    │
│  │       │                       │                     │                │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  DPP Configuration Object:                                                   │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  {                                                                   │    │
│  │    "wi-fi_tech": "infra",                                            │    │
│  │    "discovery": {                                                    │    │
│  │      "ssid": "MyNetwork"                                             │    │
│  │    },                                                                │    │
│  │    "cred": {                                                         │    │
│  │      "akm": "dpp",                                                   │    │
│  │      "signedConnector": "...",                                       │    │
│  │      "csign": {                                                      │    │
│  │        "kid": "...",                                                 │    │
│  │        "crv": "P-256",                                               │    │
│  │        "x": "...",                                                   │    │
│  │        "y": "..."                                                    │    │
│  │      },                                                              │    │
│  │      "netAccessKey": {                                               │    │
│  │        "crv": "P-256",                                               │    │
│  │        "x": "...",                                                   │    │
│  │        "y": "..."                                                    │    │
│  │      }                                                               │    │
│  │    }                                                                 │    │
│  │  }                                                                   │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  DPP Configuration:                                                          │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  # hostapd.conf                                                      │    │
│  │  wpa=2                                                               │    │
│  │  wpa_key_mgmt=DPP                                                    │    │
│  │  rsn_pairwise=CCMP                                                   │    │
│  │  ieee80211w=2                                                        │    │
│  │  dpp_connector=...                                                   │    │
│  │  dpp_csign=...                                                       │    │
│  │  dpp_netaccesskey=...                                                │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Appendix CJ: Certificate Management

### CJ.1 Certificate Types

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    CERTIFICATE TYPES                                         │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  Certificate Hierarchy:                                                      │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  ┌─────────────────────────────────────────────────────────────┐    │    │
│  │  │                                                              │    │    │
│  │  │  ┌─────────────────────────────────────────────────────┐    │    │    │
│  │  │  │              Root CA Certificate                    │    │    │    │
│  │  │  │              (Self-signed, offline)                 │    │    │    │
│  │  │  └─────────────────────────────────────────────────────┘    │    │    │
│  │  │                          │                                   │    │    │
│  │  │                          ▼                                   │    │    │
│  │  │  ┌─────────────────────────────────────────────────────┐    │    │    │
│  │  │  │           Intermediate CA Certificate               │    │    │    │
│  │  │  │           (Signs end-entity certs)                  │    │    │    │
│  │  │  └─────────────────────────────────────────────────────┘    │    │    │
│  │  │                          │                                   │    │    │
│  │  │          ┌───────────────┼───────────────┐                   │    │    │
│  │  │          ▼               ▼               ▼                   │    │    │
│  │  │  ┌───────────┐   ┌───────────┐   ┌───────────┐              │    │    │
│  │  │  │  RADIUS   │   │    AP     │   │  Client   │              │    │    │
│  │  │  │   Cert    │   │   Cert    │   │   Cert    │              │    │    │
│  │  │  └───────────┘   └───────────┘   └───────────┘              │    │    │
│  │  │                                                              │    │    │
│  │  └─────────────────────────────────────────────────────────────┘    │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  Certificate Uses in WiFi:                                                   │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  ┌────────────────────────────────────────────────────────────┐     │    │
│  │  │ Certificate         Use Case                               │     │    │
│  │  │ ───────────         ────────                               │     │    │
│  │  │ RADIUS Server       EAP-TLS server authentication          │     │    │
│  │  │ Client              EAP-TLS client authentication          │     │    │
│  │  │ AP (RadSec)         RADIUS over TLS                        │     │    │
│  │  │ Hotspot 2.0 OSU     Online Sign-Up server                  │     │    │
│  │  │ Passpoint           Credential provisioning                │     │    │
│  │  │ DPP Configurator    Device provisioning                    │     │    │
│  │  └────────────────────────────────────────────────────────────┘     │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### CJ.2 Certificate Validation

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    CERTIFICATE VALIDATION                                    │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  Validation Steps:                                                           │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  1. Signature Verification                                           │    │
│  │     - Verify certificate signed by trusted CA                        │    │
│  │     - Check entire chain to root CA                                  │    │
│  │                                                                      │    │
│  │  2. Validity Period                                                  │    │
│  │     - Check notBefore and notAfter dates                             │    │
│  │     - Reject expired certificates                                    │    │
│  │                                                                      │    │
│  │  3. Revocation Check                                                 │    │
│  │     - CRL (Certificate Revocation List)                              │    │
│  │     - OCSP (Online Certificate Status Protocol)                      │    │
│  │                                                                      │    │
│  │  4. Name Matching                                                    │    │
│  │     - Subject CN or SAN matches expected name                        │    │
│  │     - For RADIUS: match server name in supplicant config             │    │
│  │                                                                      │    │
│  │  5. Key Usage                                                        │    │
│  │     - Server cert: serverAuth                                        │    │
│  │     - Client cert: clientAuth                                        │    │
│  │                                                                      │    │
│  │  6. Extended Key Usage                                               │    │
│  │     - id-kp-serverAuth (1.3.6.1.5.5.7.3.1)                           │    │
│  │     - id-kp-clientAuth (1.3.6.1.5.5.7.3.2)                           │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  CRL vs OCSP:                                                                │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  ┌────────────────────────────────────────────────────────────┐     │    │
│  │  │ Feature             CRL                 OCSP               │     │    │
│  │  │ ───────             ───                 ────               │     │    │
│  │  │ Update Frequency    Periodic            Real-time          │     │    │
│  │  │ Bandwidth           High (full list)    Low (per-cert)     │     │    │
│  │  │ Latency             Low (cached)        Higher (query)     │     │    │
│  │  │ Offline Support     Yes (cached)        No                 │     │    │
│  │  │ Privacy             Better              Server sees certs  │     │    │
│  │  └────────────────────────────────────────────────────────────┘     │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  OCSP Stapling:                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  - Server fetches OCSP response and includes in TLS handshake        │    │
│  │  - Client doesn't need to contact OCSP server                        │    │
│  │  - Improves privacy and performance                                  │    │
│  │                                                                      │    │
│  │  # FreeRADIUS configuration                                          │    │
│  │  tls {                                                               │    │
│  │      ocsp {                                                          │    │
│  │          enable = yes                                                │    │
│  │          override_cert_url = yes                                     │    │
│  │          url = "http://ocsp.example.com"                             │    │
│  │      }                                                               │    │
│  │  }                                                                   │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Appendix CK: Roaming Protocols Comparison

### CK.1 Roaming Methods

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    ROAMING METHODS COMPARISON                                │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  Roaming Method Comparison:                                                  │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  ┌────────────────────────────────────────────────────────────┐     │    │
│  │  │ Method          Time      Frames    Requirements           │     │    │
│  │  │ ──────          ────      ──────    ────────────           │     │    │
│  │  │ Full 802.1X     1-3s      20+       RADIUS                 │     │    │
│  │  │ PMKSA Cache     200-500ms 8         Same AP or OKC         │     │    │
│  │  │ OKC             200-500ms 8         PMK distribution       │     │    │
│  │  │ 802.11r OTA     50-100ms  4         FT enabled             │     │    │
│  │  │ 802.11r ODS     30-50ms   2         FT + DS                │     │    │
│  │  │ FILS            <100ms    4         ERP, FILS              │     │    │
│  │  │ 802.11k/v       Varies    +2-4      Neighbor reports       │     │    │
│  │  └────────────────────────────────────────────────────────────┘     │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  802.11r Over-the-Air (OTA):                                                 │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  STA                    Current AP              Target AP            │    │
│  │   │                         │                       │                │    │
│  │   │ ── FT Auth Request ─────────────────────────────>│               │    │
│  │   │    (via air)            │                       │                │    │
│  │   │                         │                       │                │    │
│  │   │ <── FT Auth Response ───────────────────────────│               │    │
│  │   │                         │                       │                │    │
│  │   │ ── Reassoc Request ─────────────────────────────>│               │    │
│  │   │                         │                       │                │    │
│  │   │ <── Reassoc Response ───────────────────────────│               │    │
│  │   │                         │                       │                │    │
│  │   │ ══ Data ════════════════════════════════════════│               │    │
│  │   │                         │                       │                │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  802.11r Over-the-DS (ODS):                                                  │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  STA                    Current AP              Target AP            │    │
│  │   │                         │                       │                │    │
│  │   │ ── FT Action Request ──>│                       │                │    │
│  │   │    (via current AP)     │ ── Forward ──────────>│                │    │
│  │   │                         │                       │                │    │
│  │   │                         │ <── Response ─────────│                │    │
│  │   │ <── FT Action Response ─│                       │                │    │
│  │   │                         │                       │                │    │
│  │   │ ── Reassoc Request ─────────────────────────────>│               │    │
│  │   │                         │                       │                │    │
│  │   │ <── Reassoc Response ───────────────────────────│               │    │
│  │   │                         │                       │                │    │
│  │                                                                      │    │
│  │  Note: Pre-authentication happens while still connected              │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  802.11k Neighbor Report:                                                    │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  Purpose: Help client find best AP to roam to                        │    │
│  │                                                                      │    │
│  │  STA                                AP                               │    │
│  │   │                                  │                               │    │
│  │   │ ── Neighbor Report Request ─────>│                              │    │
│  │   │                                  │                               │    │
│  │   │ <── Neighbor Report Response ────│                              │    │
│  │   │    (List of neighbor APs with    │                               │    │
│  │   │     channel, BSSID, capabilities)│                               │    │
│  │   │                                  │                               │    │
│  │                                                                      │    │
│  │  Neighbor Report Element:                                            │    │
│  │  - BSSID                                                             │    │
│  │  - BSSID Information (capabilities)                                  │    │
│  │  - Operating Class                                                   │    │
│  │  - Channel Number                                                    │    │
│  │  - PHY Type                                                          │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  802.11v BSS Transition Management:                                          │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  Purpose: AP-initiated roaming suggestion                            │    │
│  │                                                                      │    │
│  │  AP                                 STA                              │    │
│  │   │                                  │                               │    │
│  │   │ ── BTM Request ─────────────────>│                              │    │
│  │   │    (Suggested APs, deadline)     │                               │    │
│  │   │                                  │                               │    │
│  │   │ <── BTM Response ────────────────│                              │    │
│  │   │    (Accept/Reject, target BSSID) │                               │    │
│  │   │                                  │                               │    │
│  │                                                                      │    │
│  │  BTM Request Fields:                                                 │    │
│  │  - Disassociation Imminent (force roam)                              │    │
│  │  - BSS Termination Included                                          │    │
│  │  - ESS Disassociation Imminent                                       │    │
│  │  - Disassociation Timer                                              │    │
│  │  - Validity Interval                                                 │    │
│  │  - Candidate List (preferred APs)                                    │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Document Revision History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2026-01-08 | Auto-generated | Initial document creation |
| 1.1 | 2026-01-08 | Auto-generated | Added packet capture analysis, regulatory domains, client compatibility |
| 1.2 | 2026-01-08 | Auto-generated | Added EAP methods, band steering, load balancing, mesh networking, power save |
| 1.3 | 2026-01-08 | Auto-generated | Added RADIUS attributes, debug commands, troubleshooting flowchart, quick reference |
| 1.4 | 2026-01-08 | Auto-generated | Added WiFi 7 features, Hotspot 2.0 deep dive, glossary, standards reference |
| 1.5 | 2026-01-08 | Auto-generated | Added security attacks, performance optimization, complete hostapd config |
| 1.6 | 2026-01-08 | Auto-generated | Added frame formats, information elements, status/reason codes |
| 1.7 | 2026-01-08 | Auto-generated | Added vendor extensions, debugging/logging, packet capture commands |
| 1.8 | 2026-01-08 | Auto-generated | Added test case reference, regulatory domain deep dive |
| 1.9 | 2026-01-08 | Auto-generated | Added action frame reference, error scenarios and troubleshooting |
| 2.0 | 2026-01-08 | Auto-generated | Added Wireshark filter reference, complete configuration examples |
| 2.1 | 2026-01-08 | Auto-generated | Added performance benchmarks, client device compatibility matrix |
| 2.2 | 2026-01-08 | Auto-generated | Added WiFi Alliance certification, security checklist, capacity planning |
| 2.3 | 2026-01-08 | Auto-generated | Added antenna/RF considerations, troubleshooting trees, timing diagrams |
| 2.4 | 2026-01-08 | Auto-generated | Added QoS/WMM, deployment topologies, compliance, advanced debugging |
| 2.5 | 2026-01-08 | Auto-generated | Added supplicant config, VLAN, rate limiting, HA, IoT profiling |
| 2.6 | 2026-01-08 | Auto-generated | Added captive portal, location services, spectrum analysis, migration, API |
| 2.7 | 2026-01-08 | Auto-generated | Added multicast, VoWiFi, enterprise integration, monitoring, disaster recovery |
| 2.8 | 2026-01-08 | Auto-generated | Added WIDS, cloud management, performance testing, compliance, checklists |
| 2.9 | 2026-01-08 | Auto-generated | Added outdoor WiFi, stadium/venue, healthcare, education, retail, industrial |
| 3.0 | 2026-01-08 | Auto-generated | Added WiFi 6E/7 deep dive, OFDMA, MU-MIMO, BSS coloring, TWT |
| 3.1 | 2026-01-08 | Auto-generated | Added WiFi 7 MLO, puncturing, 4K-QAM, multi-RU, enhanced security |
| 3.2 | 2026-01-08 | Auto-generated | Added FILS, DPP, enterprise security, certificate management |
| 3.3 | 2026-01-08 | Auto-generated | Added power management, airtime fairness, channel utilization |

---

## Appendix CL: Power Management Deep Dive

### CL.1 Legacy Power Save (PS-Poll)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    LEGACY POWER SAVE (PS-POLL)                               │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  Power Save Mode States:                                                     │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  ┌────────────────────────────────────────────────────────────┐     │    │
│  │  │ State               Description                            │     │    │
│  │  │ ─────               ───────────                            │     │    │
│  │  │ Active Mode (AM)    Radio always on, immediate response    │     │    │
│  │  │ Power Save (PS)     Radio mostly off, periodic wake        │     │    │
│  │  │ Doze                Radio off, waiting for beacon          │     │    │
│  │  │ Awake               Radio on, processing frames            │     │    │
│  │  └────────────────────────────────────────────────────────────┘     │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  PS-Poll Mechanism:                                                          │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  STA (Doze)                         AP                               │    │
│  │   │                                  │                               │    │
│  │   │    ┌─────────────────────────────│                               │    │
│  │   │    │ AP buffers frames for STA  │                               │    │
│  │   │    └─────────────────────────────│                               │    │
│  │   │                                  │                               │    │
│  │   │ ── Wake for Beacon ─────────────>│                              │    │
│  │   │                                  │                               │    │
│  │   │ <── Beacon (TIM: AID=5 set) ─────│                              │    │
│  │   │    (Traffic Indication Map)      │                               │    │
│  │   │                                  │                               │    │
│  │   │ ── PS-Poll ─────────────────────>│                              │    │
│  │   │    (Request buffered frame)      │                               │    │
│  │   │                                  │                               │    │
│  │   │ <── Data (More Data=1) ──────────│                              │    │
│  │   │                                  │                               │    │
│  │   │ ── PS-Poll ─────────────────────>│                              │    │
│  │   │                                  │                               │    │
│  │   │ <── Data (More Data=0) ──────────│                              │    │
│  │   │                                  │                               │    │
│  │   │ ── Return to Doze ───────────────│                              │    │
│  │   │                                  │                               │    │
│  │                                                                      │    │
│  │  TIM (Traffic Indication Map):                                       │    │
│  │  - Bitmap in beacon indicating which STAs have buffered data         │    │
│  │  - Each bit corresponds to an AID (Association ID)                   │    │
│  │  - STA checks its AID bit to know if data is waiting                 │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  DTIM (Delivery TIM):                                                        │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  - Special beacon for multicast/broadcast delivery                   │    │
│  │  - DTIM Period: Number of beacons between DTIMs                      │    │
│  │  - All PS STAs must wake for DTIM beacons                            │    │
│  │                                                                      │    │
│  │  # hostapd.conf                                                      │    │
│  │  dtim_period=2    # DTIM every 2 beacons (200ms at 100ms beacon)     │    │
│  │                                                                      │    │
│  │  Trade-off:                                                          │    │
│  │  - Lower DTIM = More responsive, higher power consumption            │    │
│  │  - Higher DTIM = Better battery life, delayed multicast              │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### CL.2 U-APSD (Unscheduled Automatic Power Save Delivery)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    U-APSD (WMM POWER SAVE)                                   │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  U-APSD vs PS-Poll:                                                          │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  ┌────────────────────────────────────────────────────────────┐     │    │
│  │  │ Feature             PS-Poll             U-APSD             │     │    │
│  │  │ ───────             ───────             ──────             │     │    │
│  │  │ Trigger             Beacon TIM          Uplink data        │     │    │
│  │  │ Latency             High (wait beacon)  Low (immediate)    │     │    │
│  │  │ Efficiency          Low (1 frame/poll)  High (burst)       │     │    │
│  │  │ VoIP Suitable       No                  Yes                │     │    │
│  │  │ Per-AC Control      No                  Yes                │     │    │
│  │  └────────────────────────────────────────────────────────────┘     │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  U-APSD Mechanism:                                                           │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  STA (Doze)                         AP                               │    │
│  │   │                                  │                               │    │
│  │   │    ┌─────────────────────────────│                               │    │
│  │   │    │ AP buffers frames for STA  │                               │    │
│  │   │    └─────────────────────────────│                               │    │
│  │   │                                  │                               │    │
│  │   │ ── Trigger Frame (QoS Data) ────>│                              │    │
│  │   │    (Uplink voice packet)         │                               │    │
│  │   │                                  │                               │    │
│  │   │ <── Service Period Start ────────│                              │    │
│  │   │                                  │                               │    │
│  │   │ <── QoS Data (EOSP=0) ───────────│                              │    │
│  │   │ <── QoS Data (EOSP=0) ───────────│                              │    │
│  │   │ <── QoS Data (EOSP=1) ───────────│                              │    │
│  │   │    (End of Service Period)       │                               │    │
│  │   │                                  │                               │    │
│  │   │ ── Return to Doze ───────────────│                              │    │
│  │   │                                  │                               │    │
│  │                                                                      │    │
│  │  Key Concepts:                                                       │    │
│  │  - Trigger Frame: Uplink QoS data that triggers downlink delivery    │    │
│  │  - Service Period: Time when AP delivers buffered frames            │    │
│  │  - EOSP: End of Service Period bit                                   │    │
│  │  - Max SP Length: Maximum frames per service period (2, 4, 6, all)   │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  U-APSD Configuration:                                                       │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  # hostapd.conf                                                      │    │
│  │  wmm_enabled=1                                                       │    │
│  │  uapsd_advertisement_enabled=1                                       │    │
│  │                                                                      │    │
│  │  # Per-AC U-APSD (in WMM IE)                                         │    │
│  │  # AC_VO: Voice (trigger + delivery enabled)                         │    │
│  │  # AC_VI: Video (trigger + delivery enabled)                         │    │
│  │  # AC_BE: Best Effort (legacy PS)                                    │    │
│  │  # AC_BK: Background (legacy PS)                                     │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### CL.3 TWT (Target Wake Time) - Detailed

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    TWT DETAILED OPERATION                                    │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  TWT Agreement Negotiation:                                                  │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  STA                                AP                               │    │
│  │   │                                  │                               │    │
│  │   │ ── TWT Setup Request ───────────>│                              │    │
│  │   │    Request Type: Individual      │                               │    │
│  │   │    Wake Interval: 1000 TUs       │                               │    │
│  │   │    Wake Duration: 10 TUs         │                               │    │
│  │   │    Flow ID: 0                    │                               │    │
│  │   │                                  │                               │    │
│  │   │ <── TWT Setup Response ──────────│                              │    │
│  │   │    Accept/Alternate/Reject       │                               │    │
│  │   │    Confirmed parameters          │                               │    │
│  │   │                                  │                               │    │
│  │   │ ══ TWT Agreement Active ═════════│                              │    │
│  │   │                                  │                               │    │
│  │                                                                      │    │
│  │  TWT Element Fields:                                                 │    │
│  │  - TWT Request (1 bit): Request or response                          │    │
│  │  - TWT Setup Command (3 bits): Request/Suggest/Demand/Accept/etc.    │    │
│  │  - Trigger (1 bit): Trigger-enabled TWT                              │    │
│  │  - Implicit (1 bit): Implicit or explicit TWT                        │    │
│  │  - Flow Type (1 bit): Announced or unannounced                       │    │
│  │  - TWT Wake Interval Mantissa (16 bits)                              │    │
│  │  - TWT Wake Interval Exponent (5 bits)                               │    │
│  │  - Nominal Minimum TWT Wake Duration (8 bits)                        │    │
│  │  - TWT Channel (8 bits)                                              │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  TWT Timeline:                                                               │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  Time ──────────────────────────────────────────────────────────>    │    │
│  │                                                                      │    │
│  │  ┌────┐          ┌────┐          ┌────┐          ┌────┐             │    │
│  │  │Wake│          │Wake│          │Wake│          │Wake│             │    │
│  │  │    │          │    │          │    │          │    │             │    │
│  │  └────┘          └────┘          └────┘          └────┘             │    │
│  │  ◄───────────────►                                                   │    │
│  │   Wake Interval                                                      │    │
│  │                                                                      │    │
│  │  ◄──►                                                                │    │
│  │  Wake Duration                                                       │    │
│  │                                                                      │    │
│  │  During Wake:                                                        │    │
│  │  - STA can transmit/receive                                          │    │
│  │  - AP delivers buffered frames                                       │    │
│  │  - Trigger frames for UL OFDMA                                       │    │
│  │                                                                      │    │
│  │  During Doze:                                                        │    │
│  │  - Radio off, minimal power                                          │    │
│  │  - AP buffers frames                                                 │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  Broadcast TWT:                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  - AP announces TWT schedule in beacon                               │    │
│  │  - Multiple STAs share same TWT schedule                             │    │
│  │  - Efficient for IoT deployments                                     │    │
│  │                                                                      │    │
│  │  Beacon                                                              │    │
│  │  ┌─────────────────────────────────────────────────────────────┐    │    │
│  │  │ Broadcast TWT Element                                        │    │    │
│  │  │ - TWT ID: 1                                                  │    │    │
│  │  │ - Wake Interval: 500 TUs                                     │    │    │
│  │  │ - Wake Duration: 5 TUs                                       │    │    │
│  │  │ - Next TWT: 12345678 TUs                                     │    │    │
│  │  └─────────────────────────────────────────────────────────────┘    │    │
│  │                                                                      │    │
│  │  STAs join broadcast TWT by sending TWT Setup with matching ID       │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Appendix CM: Airtime Fairness

### CM.1 Airtime Fairness Concepts

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    AIRTIME FAIRNESS                                          │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  Problem: Slow Clients Affect Everyone                                       │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  Without Airtime Fairness:                                           │    │
│  │  ┌────────────────────────────────────────────────────────────┐     │    │
│  │  │                                                             │     │    │
│  │  │  Client A (Fast, 1 Gbps)                                    │     │    │
│  │  │  ┌──┐                                                       │     │    │
│  │  │  │  │ 1 MB takes 8 ms                                       │     │    │
│  │  │  └──┘                                                       │     │    │
│  │  │                                                             │     │    │
│  │  │  Client B (Slow, 10 Mbps)                                   │     │    │
│  │  │  ┌────────────────────────────────────────────────────────┐│     │    │
│  │  │  │                                                         ││     │    │
│  │  │  │ 1 MB takes 800 ms                                       ││     │    │
│  │  │  │                                                         ││     │    │
│  │  │  └────────────────────────────────────────────────────────┘│     │    │
│  │  │                                                             │     │    │
│  │  │  Equal bytes = Unequal airtime                              │     │    │
│  │  │  Slow client monopolizes the channel                        │     │    │
│  │  │                                                             │     │    │
│  │  └────────────────────────────────────────────────────────────┘     │    │
│  │                                                                      │    │
│  │  With Airtime Fairness:                                              │    │
│  │  ┌────────────────────────────────────────────────────────────┐     │    │
│  │  │                                                             │     │    │
│  │  │  Client A (Fast, 1 Gbps)                                    │     │    │
│  │  │  ┌──────────────────────────────────────────────────────┐  │     │    │
│  │  │  │ Gets 50% airtime = 62.5 MB                            │  │     │    │
│  │  │  └──────────────────────────────────────────────────────┘  │     │    │
│  │  │                                                             │     │    │
│  │  │  Client B (Slow, 10 Mbps)                                   │     │    │
│  │  │  ┌──────────────────────────────────────────────────────┐  │     │    │
│  │  │  │ Gets 50% airtime = 0.625 MB                           │  │     │    │
│  │  │  └──────────────────────────────────────────────────────┘  │     │    │
│  │  │                                                             │     │    │
│  │  │  Equal airtime = Fair channel access                        │     │    │
│  │  │                                                             │     │    │
│  │  └────────────────────────────────────────────────────────────┘     │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  Airtime Calculation:                                                        │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  Airtime = (Frame Size / Data Rate) + Overhead                       │    │
│  │                                                                      │    │
│  │  Overhead includes:                                                  │    │
│  │  - Preamble and headers                                              │    │
│  │  - SIFS, DIFS, backoff                                               │    │
│  │  - ACK frame                                                         │    │
│  │  - Retransmissions                                                   │    │
│  │                                                                      │    │
│  │  Example:                                                            │    │
│  │  1500 byte frame at 54 Mbps:                                         │    │
│  │  - Data time: 1500 * 8 / 54,000,000 = 222 µs                         │    │
│  │  - Overhead: ~100 µs                                                 │    │
│  │  - Total: ~322 µs                                                    │    │
│  │                                                                      │    │
│  │  1500 byte frame at 6 Mbps:                                          │    │
│  │  - Data time: 1500 * 8 / 6,000,000 = 2000 µs                         │    │
│  │  - Overhead: ~100 µs                                                 │    │
│  │  - Total: ~2100 µs (6.5x more airtime!)                              │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  Airtime Fairness Policies:                                                  │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  ┌────────────────────────────────────────────────────────────┐     │    │
│  │  │ Policy              Description                            │     │    │
│  │  │ ──────              ───────────                            │     │    │
│  │  │ Per-Client          Equal airtime per client               │     │    │
│  │  │ Per-SSID            Equal airtime per SSID                 │     │    │
│  │  │ Per-User            Equal airtime per user (across devices)│     │    │
│  │  │ Weighted            Proportional to configured weight      │     │    │
│  │  │ Dynamic             Adjust based on traffic type           │     │    │
│  │  └────────────────────────────────────────────────────────────┘     │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Appendix CN: Channel Utilization Analysis

### CN.1 Channel Utilization Metrics

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    CHANNEL UTILIZATION METRICS                               │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  Channel Time Breakdown:                                                     │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  Total Channel Time (100%)                                           │    │
│  │  ┌─────────────────────────────────────────────────────────────┐    │    │
│  │  │                                                              │    │    │
│  │  │  ┌──────────────────────────────────────────────────────┐   │    │    │
│  │  │  │ Busy Time                                             │   │    │    │
│  │  │  │ ┌────────────────────────────────────────────────────┐│   │    │    │
│  │  │  │ │ TX Time    │ RX Time    │ Interference │ Overhead  ││   │    │    │
│  │  │  │ │ (Our TX)   │ (Our RX)   │ (Other BSS)  │ (Mgmt)    ││   │    │    │
│  │  │  │ └────────────────────────────────────────────────────┘│   │    │    │
│  │  │  └──────────────────────────────────────────────────────┘   │    │    │
│  │  │                                                              │    │    │
│  │  │  ┌──────────────────────────────────────────────────────┐   │    │    │
│  │  │  │ Idle Time (Available for new transmissions)          │   │    │    │
│  │  │  └──────────────────────────────────────────────────────┘   │    │    │
│  │  │                                                              │    │    │
│  │  └─────────────────────────────────────────────────────────────┘    │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  Key Metrics:                                                                │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  ┌────────────────────────────────────────────────────────────┐     │    │
│  │  │ Metric              Description                 Target     │     │    │
│  │  │ ──────              ───────────                 ──────     │     │    │
│  │  │ Channel Busy %      Total busy / total time     < 70%      │     │    │
│  │  │ TX Utilization      Our TX / total time         Varies     │     │    │
│  │  │ RX Utilization      Our RX / total time         Varies     │     │    │
│  │  │ Interference %      Other BSS / total time      < 30%      │     │    │
│  │  │ Retry Rate          Retries / total frames      < 10%      │     │    │
│  │  │ Noise Floor         Background noise (dBm)      < -90 dBm  │     │    │
│  │  └────────────────────────────────────────────────────────────┘     │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  Channel Utilization Thresholds:                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  ┌────────────────────────────────────────────────────────────┐     │    │
│  │  │ Utilization         Status              Action             │     │    │
│  │  │ ───────────         ──────              ──────             │     │    │
│  │  │ 0-30%               Excellent           None needed        │     │    │
│  │  │ 30-50%              Good                Monitor            │     │    │
│  │  │ 50-70%              Moderate            Consider changes   │     │    │
│  │  │ 70-85%              High                Add capacity       │     │    │
│  │  │ 85-100%             Critical            Immediate action   │     │    │
│  │  └────────────────────────────────────────────────────────────┘     │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  Monitoring Commands:                                                        │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  # Get channel survey data                                           │    │
│  │  iw dev wlan0 survey dump                                            │    │
│  │                                                                      │    │
│  │  # Output:                                                           │    │
│  │  Survey data from wlan0                                              │    │
│  │    frequency:                  5180 MHz [in use]                     │    │
│  │    noise:                      -95 dBm                               │    │
│  │    channel active time:        1000000 ms                            │    │
│  │    channel busy time:          350000 ms                             │    │
│  │    channel receive time:       200000 ms                             │    │
│  │    channel transmit time:      100000 ms                             │    │
│  │                                                                      │    │
│  │  # Calculate utilization                                             │    │
│  │  Busy % = 350000 / 1000000 = 35%                                     │    │
│  │  TX % = 100000 / 1000000 = 10%                                       │    │
│  │  RX % = 200000 / 1000000 = 20%                                       │    │
│  │  Interference % = (350000 - 200000 - 100000) / 1000000 = 5%          │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Document Revision History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2026-01-08 | Auto-generated | Initial document creation |
| 1.1 | 2026-01-08 | Auto-generated | Added packet capture analysis, regulatory domains, client compatibility |
| 1.2 | 2026-01-08 | Auto-generated | Added EAP methods, band steering, load balancing, mesh networking, power save |
| 1.3 | 2026-01-08 | Auto-generated | Added RADIUS attributes, debug commands, troubleshooting flowchart, quick reference |
| 1.4 | 2026-01-08 | Auto-generated | Added WiFi 7 features, Hotspot 2.0 deep dive, glossary, standards reference |
| 1.5 | 2026-01-08 | Auto-generated | Added security attacks, performance optimization, complete hostapd config |
| 1.6 | 2026-01-08 | Auto-generated | Added frame formats, information elements, status/reason codes |
| 1.7 | 2026-01-08 | Auto-generated | Added vendor extensions, debugging/logging, packet capture commands |
| 1.8 | 2026-01-08 | Auto-generated | Added test case reference, regulatory domain deep dive |
| 1.9 | 2026-01-08 | Auto-generated | Added action frame reference, error scenarios and troubleshooting |
| 2.0 | 2026-01-08 | Auto-generated | Added Wireshark filter reference, complete configuration examples |
| 2.1 | 2026-01-08 | Auto-generated | Added performance benchmarks, client device compatibility matrix |
| 2.2 | 2026-01-08 | Auto-generated | Added WiFi Alliance certification, security checklist, capacity planning |
| 2.3 | 2026-01-08 | Auto-generated | Added antenna/RF considerations, troubleshooting trees, timing diagrams |
| 2.4 | 2026-01-08 | Auto-generated | Added QoS/WMM, deployment topologies, compliance, advanced debugging |
| 2.5 | 2026-01-08 | Auto-generated | Added supplicant config, VLAN, rate limiting, HA, IoT profiling |
| 2.6 | 2026-01-08 | Auto-generated | Added captive portal, location services, spectrum analysis, migration, API |
| 2.7 | 2026-01-08 | Auto-generated | Added multicast, VoWiFi, enterprise integration, monitoring, disaster recovery |
| 2.8 | 2026-01-08 | Auto-generated | Added WIDS, cloud management, performance testing, compliance, checklists |
| 2.9 | 2026-01-08 | Auto-generated | Added outdoor WiFi, stadium/venue, healthcare, education, retail, industrial |
| 3.0 | 2026-01-08 | Auto-generated | Added WiFi 6E/7 deep dive, OFDMA, MU-MIMO, BSS coloring, TWT |
| 3.1 | 2026-01-08 | Auto-generated | Added WiFi 7 MLO, puncturing, 4K-QAM, multi-RU, enhanced security |
| 3.2 | 2026-01-08 | Auto-generated | Added FILS, DPP, enterprise security, certificate management |
| 3.3 | 2026-01-08 | Auto-generated | Added power management, airtime fairness, channel utilization |
| 3.4 | 2026-01-08 | Auto-generated | Added client steering, band selection, load balancing algorithms |

---

## Appendix CO: Client Steering Mechanisms

### CO.1 Band Steering

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    BAND STEERING                                             │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  Purpose:                                                                    │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  - Move dual-band clients from 2.4 GHz to 5 GHz or 6 GHz             │    │
│  │  - Reduce congestion on 2.4 GHz band                                 │    │
│  │  - Improve overall network performance                               │    │
│  │  - Better utilize available spectrum                                 │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  Band Steering Methods:                                                      │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  1. Probe Response Suppression                                       │    │
│  │  ┌────────────────────────────────────────────────────────────┐     │    │
│  │  │                                                             │     │    │
│  │  │  Client                    AP (2.4 GHz)    AP (5 GHz)       │     │    │
│  │  │    │                           │               │            │     │    │
│  │  │    │ ── Probe Request (2.4) ──>│               │            │     │    │
│  │  │    │                           │               │            │     │    │
│  │  │    │    (No response - suppressed)             │            │     │    │
│  │  │    │                           │               │            │     │    │
│  │  │    │ ── Probe Request (5 GHz) ─────────────────>│           │     │    │
│  │  │    │                           │               │            │     │    │
│  │  │    │ <── Probe Response ───────────────────────│           │     │    │
│  │  │    │                           │               │            │     │    │
│  │  │    │ ── Connect to 5 GHz ──────────────────────>│           │     │    │
│  │  │    │                           │               │            │     │    │
│  │  └────────────────────────────────────────────────────────────┘     │    │
│  │                                                                      │    │
│  │  2. Authentication Rejection                                         │    │
│  │  ┌────────────────────────────────────────────────────────────┐     │    │
│  │  │                                                             │     │    │
│  │  │  Client                    AP (2.4 GHz)    AP (5 GHz)       │     │    │
│  │  │    │                           │               │            │     │    │
│  │  │    │ ── Auth Request (2.4) ───>│               │            │     │    │
│  │  │    │                           │               │            │     │    │
│  │  │    │ <── Auth Reject ──────────│               │            │     │    │
│  │  │    │    (Status: 17)           │               │            │     │    │
│  │  │    │                           │               │            │     │    │
│  │  │    │ ── Auth Request (5 GHz) ──────────────────>│           │     │    │
│  │  │    │                           │               │            │     │    │
│  │  │    │ <── Auth Success ─────────────────────────│           │     │    │
│  │  │    │                           │               │            │     │    │
│  │  └────────────────────────────────────────────────────────────┘     │    │
│  │                                                                      │    │
│  │  3. 802.11v BTM (BSS Transition Management)                          │    │
│  │  ┌────────────────────────────────────────────────────────────┐     │    │
│  │  │                                                             │     │    │
│  │  │  Client                    AP (2.4 GHz)    AP (5 GHz)       │     │    │
│  │  │    │                           │               │            │     │    │
│  │  │    │ ══ Connected (2.4 GHz) ═══│               │            │     │    │
│  │  │    │                           │               │            │     │    │
│  │  │    │ <── BTM Request ──────────│               │            │     │    │
│  │  │    │    (Suggest 5 GHz BSSID)  │               │            │     │    │
│  │  │    │                           │               │            │     │    │
│  │  │    │ ── BTM Response ─────────>│               │            │     │    │
│  │  │    │    (Accept)               │               │            │     │    │
│  │  │    │                           │               │            │     │    │
│  │  │    │ ── Roam to 5 GHz ─────────────────────────>│           │     │    │
│  │  │    │                           │               │            │     │    │
│  │  └────────────────────────────────────────────────────────────┘     │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  Band Steering Configuration:                                                │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  # Probe suppression parameters                                      │    │
│  │  band_steering_mode=prefer_5ghz                                      │    │
│  │  probe_suppress_count=3        # Suppress first 3 probes             │    │
│  │  probe_suppress_age=30         # Reset after 30 seconds              │    │
│  │                                                                      │    │
│  │  # RSSI thresholds                                                   │    │
│  │  min_rssi_5ghz=-75             # Minimum 5 GHz RSSI to steer         │    │
│  │  max_rssi_2ghz=-65             # Maximum 2.4 GHz RSSI to steer       │    │
│  │                                                                      │    │
│  │  # Client capability check                                           │    │
│  │  require_dual_band=true        # Only steer dual-band clients        │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### CO.2 Load Balancing

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    LOAD BALANCING                                            │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  Load Balancing Metrics:                                                     │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  ┌────────────────────────────────────────────────────────────┐     │    │
│  │  │ Metric              Description                 Weight     │     │    │
│  │  │ ──────              ───────────                 ──────     │     │    │
│  │  │ Client Count        Number of associated clients  30%      │     │    │
│  │  │ Channel Utilization Busy time percentage          25%      │     │    │
│  │  │ Airtime Usage       TX + RX time percentage       25%      │     │    │
│  │  │ Throughput          Current data rate             10%      │     │    │
│  │  │ Retry Rate          Retransmission percentage     10%      │     │    │
│  │  └────────────────────────────────────────────────────────────┘     │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  Load Balancing Algorithms:                                                  │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  1. Client Count Balancing                                           │    │
│  │  ┌────────────────────────────────────────────────────────────┐     │    │
│  │  │                                                             │     │    │
│  │  │  Before:                                                    │     │    │
│  │  │  AP1: ████████████████████ (20 clients)                     │     │    │
│  │  │  AP2: ████ (4 clients)                                      │     │    │
│  │  │  AP3: ██████ (6 clients)                                    │     │    │
│  │  │                                                             │     │    │
│  │  │  After:                                                     │     │    │
│  │  │  AP1: ██████████ (10 clients)                               │     │    │
│  │  │  AP2: ██████████ (10 clients)                               │     │    │
│  │  │  AP3: ██████████ (10 clients)                               │     │    │
│  │  │                                                             │     │    │
│  │  └────────────────────────────────────────────────────────────┘     │    │
│  │                                                                      │    │
│  │  2. Airtime Balancing                                                │    │
│  │  ┌────────────────────────────────────────────────────────────┐     │    │
│  │  │                                                             │     │    │
│  │  │  Before:                                                    │     │    │
│  │  │  AP1: ████████████████████ (80% airtime)                    │     │    │
│  │  │  AP2: ████████ (30% airtime)                                │     │    │
│  │  │  AP3: ██████████ (40% airtime)                              │     │    │
│  │  │                                                             │     │    │
│  │  │  After:                                                     │     │    │
│  │  │  AP1: ████████████ (50% airtime)                            │     │    │
│  │  │  AP2: ████████████ (50% airtime)                            │     │    │
│  │  │  AP3: ████████████ (50% airtime)                            │     │    │
│  │  │                                                             │     │    │
│  │  └────────────────────────────────────────────────────────────┘     │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  Load Balancing Flow:                                                        │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  New Client                 AP1 (Overloaded)    AP2 (Available)      │    │
│  │      │                           │                   │               │    │
│  │      │ ── Probe Request ────────>│                   │               │    │
│  │      │                           │                   │               │    │
│  │      │    (Check load: 80%)      │                   │               │    │
│  │      │    (Threshold: 70%)       │                   │               │    │
│  │      │    (Suppress response)    │                   │               │    │
│  │      │                           │                   │               │    │
│  │      │ ── Probe Request ─────────────────────────────>│              │    │
│  │      │                           │                   │               │    │
│  │      │ <── Probe Response ───────────────────────────│              │    │
│  │      │                           │                   │               │    │
│  │      │ ── Connect ───────────────────────────────────>│              │    │
│  │      │                           │                   │               │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  Load Balancing Configuration:                                               │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  # Enable load balancing                                             │    │
│  │  load_balancing_enabled=true                                         │    │
│  │                                                                      │    │
│  │  # Thresholds                                                        │    │
│  │  max_clients_per_radio=50                                            │    │
│  │  max_channel_utilization=70                                          │    │
│  │  load_balance_threshold=20     # Difference to trigger balancing     │    │
│  │                                                                      │    │
│  │  # Balancing method                                                  │    │
│  │  load_balance_method=airtime   # client_count, airtime, hybrid       │    │
│  │                                                                      │    │
│  │  # Sticky client handling                                            │    │
│  │  sticky_client_rssi=-80        # Force roam below this RSSI          │    │
│  │  sticky_client_timeout=300     # Seconds before forcing roam         │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Appendix CP: Wireless Intrusion Detection

### CP.1 WIDS/WIPS Overview

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    WIDS/WIPS OVERVIEW                                        │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  WIDS vs WIPS:                                                               │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  ┌────────────────────────────────────────────────────────────┐     │    │
│  │  │ System              Function                               │     │    │
│  │  │ ──────              ────────                               │     │    │
│  │  │ WIDS                Wireless Intrusion Detection System    │     │    │
│  │  │                     - Monitors and alerts                  │     │    │
│  │  │                     - Passive detection                    │     │    │
│  │  │                                                             │     │    │
│  │  │ WIPS                Wireless Intrusion Prevention System   │     │    │
│  │  │                     - Monitors, alerts, and responds       │     │    │
│  │  │                     - Active countermeasures               │     │    │
│  │  └────────────────────────────────────────────────────────────┘     │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  Threat Categories:                                                          │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  ┌────────────────────────────────────────────────────────────┐     │    │
│  │  │ Category            Examples                               │     │    │
│  │  │ ────────            ────────                               │     │    │
│  │  │ Rogue APs           Unauthorized APs on network            │     │    │
│  │  │ Evil Twin           AP impersonating legitimate SSID       │     │    │
│  │  │ Deauth Attack       Flood of deauthentication frames       │     │    │
│  │  │ Disassoc Attack     Flood of disassociation frames         │     │    │
│  │  │ Auth Flood          Authentication request flood           │     │    │
│  │  │ Probe Flood         Excessive probe requests               │     │    │
│  │  │ EAPOL Flood         EAP frame flood                        │     │    │
│  │  │ Null Probe          Probe with null SSID (reconnaissance)  │     │    │
│  │  │ Karma Attack        Responding to all probe requests       │     │    │
│  │  │ KRACK               Key reinstallation attack              │     │    │
│  │  │ PMKID Attack        Offline PSK cracking                   │     │    │
│  │  └────────────────────────────────────────────────────────────┘     │     │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  Detection Methods:                                                          │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  1. Signature-Based Detection                                        │    │
│  │     - Known attack patterns                                          │    │
│  │     - Frame sequence analysis                                        │    │
│  │     - Specific field values                                          │    │
│  │                                                                      │    │
│  │  2. Anomaly-Based Detection                                          │    │
│  │     - Baseline behavior modeling                                     │    │
│  │     - Statistical analysis                                           │    │
│  │     - Machine learning                                               │    │
│  │                                                                      │    │
│  │  3. Policy-Based Detection                                           │    │
│  │     - Authorized AP list                                             │    │
│  │     - Allowed channels                                               │    │
│  │     - Security requirements                                          │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  Rogue AP Detection:                                                         │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  Classification:                                                     │    │
│  │  ┌────────────────────────────────────────────────────────────┐     │    │
│  │  │ Type                Description                 Action     │     │    │
│  │  │ ────                ───────────                 ──────     │     │    │
│  │  │ Authorized          Known, managed AP           Allow      │     │    │
│  │  │ Friendly            Known, not managed          Monitor    │     │    │
│  │  │ Interfering         Neighbor AP, different SSID Monitor    │     │    │
│  │  │ Rogue               Unknown, same SSID          Alert      │     │    │
│  │  │ Evil Twin           Impersonating our SSID      Block      │     │    │
│  │  └────────────────────────────────────────────────────────────┘     │    │
│  │                                                                      │    │
│  │  Detection Criteria:                                                 │    │
│  │  - BSSID not in authorized list                                      │    │
│  │  - SSID matches our network                                          │    │
│  │  - Connected to wired network (detected via ARP/DHCP)                │    │
│  │  - Unusual location (RSSI triangulation)                             │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  Countermeasures:                                                            │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  ┌────────────────────────────────────────────────────────────┐     │    │
│  │  │ Countermeasure      Description                 Caution    │     │    │
│  │  │ ──────────────      ───────────                 ───────    │     │    │
│  │  │ Deauth Flood        Send deauth to rogue clients Legal     │     │    │
│  │  │ Channel Jamming     Interfere with rogue channel Illegal   │     │    │
│  │  │ Port Blocking       Block switch port of rogue   Safe      │     │    │
│  │  │ Alert Only          Notify administrator         Safe      │     │    │
│  │  │ Client Blacklist    Block clients on rogue       Safe      │     │    │
│  │  └────────────────────────────────────────────────────────────┘     │    │
│  │                                                                      │    │
│  │  Note: Active countermeasures may have legal implications            │    │
│  │  depending on jurisdiction. Consult legal counsel.                   │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Appendix CQ: Antenna and RF Fundamentals

### CQ.1 Antenna Types

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    ANTENNA TYPES                                             │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  Common Antenna Types:                                                       │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  ┌────────────────────────────────────────────────────────────┐     │    │
│  │  │ Type                Pattern         Gain      Use Case     │     │    │
│  │  │ ────                ───────         ────      ────────     │     │    │
│  │  │ Omnidirectional     360° horizontal 2-5 dBi   Indoor       │     │    │
│  │  │ Dipole              Donut shape     2-3 dBi   General      │     │    │
│  │  │ Patch/Panel         Directional     6-12 dBi  Wall mount   │     │    │
│  │  │ Sector              60-120° beam    10-18 dBi Outdoor      │     │    │
│  │  │ Yagi                Narrow beam     12-18 dBi Point-to-pt  │     │    │
│  │  │ Parabolic           Very narrow     20-30 dBi Long range   │     │    │
│  │  └────────────────────────────────────────────────────────────┘     │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  Antenna Patterns:                                                           │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  Omnidirectional (Top View):        Directional (Top View):         │    │
│  │                                                                      │    │
│  │         ┌───────┐                          ┌───────┐                │    │
│  │       ╱           ╲                      ╱           ╲              │    │
│  │      │             │                    │             │             │    │
│  │     │      ●       │                   │      ●───────────>         │    │
│  │      │             │                    │             │             │    │
│  │       ╲           ╱                      ╲           ╱              │    │
│  │         └───────┘                          └───────┘                │    │
│  │                                                                      │    │
│  │  Omnidirectional (Side View):       Directional (Side View):        │    │
│  │                                                                      │    │
│  │           │                                   ╱╲                    │    │
│  │      ─────●─────                         ────●────>                 │    │
│  │           │                                   ╲╱                    │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  MIMO Antenna Configurations:                                                │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  ┌────────────────────────────────────────────────────────────┐     │    │
│  │  │ Config              Streams    Typical Use                 │     │    │
│  │  │ ──────              ───────    ───────────                 │     │    │
│  │  │ 1x1 SISO            1          IoT, basic clients          │     │    │
│  │  │ 2x2 MIMO            2          Smartphones, tablets        │     │    │
│  │  │ 3x3 MIMO            3          Laptops                     │     │    │
│  │  │ 4x4 MIMO            4          High-end laptops, APs       │     │    │
│  │  │ 8x8 MIMO            8          Enterprise APs              │     │    │
│  │  │ 16x16 MIMO          16         WiFi 7 APs                  │     │    │
│  │  └────────────────────────────────────────────────────────────┘     │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### CQ.2 RF Propagation

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    RF PROPAGATION                                            │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  Free Space Path Loss (FSPL):                                                │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  FSPL (dB) = 20 × log₁₀(d) + 20 × log₁₀(f) + 20 × log₁₀(4π/c)       │    │
│  │                                                                      │    │
│  │  Simplified:                                                         │    │
│  │  FSPL (dB) = 20 × log₁₀(d) + 20 × log₁₀(f) - 147.55                  │    │
│  │                                                                      │    │
│  │  Where:                                                              │    │
│  │  - d = distance in meters                                            │    │
│  │  - f = frequency in Hz                                               │    │
│  │                                                                      │    │
│  │  Example at 10 meters:                                               │    │
│  │  - 2.4 GHz: 60.0 dB                                                  │    │
│  │  - 5 GHz:   66.4 dB                                                  │    │
│  │  - 6 GHz:   68.0 dB                                                  │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  Material Attenuation:                                                       │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  ┌────────────────────────────────────────────────────────────┐     │    │
│  │  │ Material            2.4 GHz     5 GHz       6 GHz          │     │    │
│  │  │ ────────            ───────     ─────       ─────          │     │    │
│  │  │ Drywall             3 dB        4 dB        5 dB           │     │    │
│  │  │ Glass (clear)       3 dB        4 dB        5 dB           │     │    │
│  │  │ Glass (tinted)      6 dB        8 dB        10 dB          │     │    │
│  │  │ Wood door           4 dB        5 dB        6 dB           │     │    │
│  │  │ Brick wall          6 dB        10 dB       12 dB          │     │    │
│  │  │ Concrete wall       10 dB       15 dB       18 dB          │     │    │
│  │  │ Metal door          15 dB       20 dB       25 dB          │     │    │
│  │  │ Elevator shaft      25 dB       30 dB       35 dB          │     │    │
│  │  │ Floor (wood)        10 dB       15 dB       18 dB          │     │    │
│  │  │ Floor (concrete)    15 dB       20 dB       25 dB          │     │    │
│  │  └────────────────────────────────────────────────────────────┘     │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  Link Budget Calculation:                                                    │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  Received Power = TX Power + TX Antenna Gain - Path Loss             │    │
│  │                   - Cable Loss + RX Antenna Gain                     │    │
│  │                                                                      │    │
│  │  Example:                                                            │    │
│  │  ┌────────────────────────────────────────────────────────────┐     │    │
│  │  │ Component           Value                                  │     │    │
│  │  │ ─────────           ─────                                  │     │    │
│  │  │ TX Power            +20 dBm                                │     │    │
│  │  │ TX Antenna Gain     +5 dBi                                 │     │    │
│  │  │ Cable Loss          -2 dB                                  │     │    │
│  │  │ FSPL (50m, 5 GHz)   -80 dB                                 │     │    │
│  │  │ Wall Loss           -10 dB                                 │     │    │
│  │  │ RX Antenna Gain     +3 dBi                                 │     │    │
│  │  │ ─────────────────────────────────────────────────────────  │     │    │
│  │  │ Received Power      -64 dBm                                │     │    │
│  │  └────────────────────────────────────────────────────────────┘     │    │
│  │                                                                      │    │
│  │  Fade Margin:                                                        │    │
│  │  - Add 10-20 dB margin for multipath fading                          │    │
│  │  - Required RSSI for reliable connection: -67 dBm                    │    │
│  │  - Margin = -64 - (-67) = 3 dB (insufficient!)                       │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Document Revision History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2026-01-08 | Auto-generated | Initial document creation |
| 1.1 | 2026-01-08 | Auto-generated | Added packet capture analysis, regulatory domains, client compatibility |
| 1.2 | 2026-01-08 | Auto-generated | Added EAP methods, band steering, load balancing, mesh networking, power save |
| 1.3 | 2026-01-08 | Auto-generated | Added RADIUS attributes, debug commands, troubleshooting flowchart, quick reference |
| 1.4 | 2026-01-08 | Auto-generated | Added WiFi 7 features, Hotspot 2.0 deep dive, glossary, standards reference |
| 1.5 | 2026-01-08 | Auto-generated | Added security attacks, performance optimization, complete hostapd config |
| 1.6 | 2026-01-08 | Auto-generated | Added frame formats, information elements, status/reason codes |
| 1.7 | 2026-01-08 | Auto-generated | Added vendor extensions, debugging/logging, packet capture commands |
| 1.8 | 2026-01-08 | Auto-generated | Added test case reference, regulatory domain deep dive |
| 1.9 | 2026-01-08 | Auto-generated | Added action frame reference, error scenarios and troubleshooting |
| 2.0 | 2026-01-08 | Auto-generated | Added Wireshark filter reference, complete configuration examples |
| 2.1 | 2026-01-08 | Auto-generated | Added performance benchmarks, client device compatibility matrix |
| 2.2 | 2026-01-08 | Auto-generated | Added WiFi Alliance certification, security checklist, capacity planning |
| 2.3 | 2026-01-08 | Auto-generated | Added antenna/RF considerations, troubleshooting trees, timing diagrams |
| 2.4 | 2026-01-08 | Auto-generated | Added QoS/WMM, deployment topologies, compliance, advanced debugging |
| 2.5 | 2026-01-08 | Auto-generated | Added supplicant config, VLAN, rate limiting, HA, IoT profiling |
| 2.6 | 2026-01-08 | Auto-generated | Added captive portal, location services, spectrum analysis, migration, API |
| 2.7 | 2026-01-08 | Auto-generated | Added multicast, VoWiFi, enterprise integration, monitoring, disaster recovery |
| 2.8 | 2026-01-08 | Auto-generated | Added WIDS, cloud management, performance testing, compliance, checklists |
| 2.9 | 2026-01-08 | Auto-generated | Added outdoor WiFi, stadium/venue, healthcare, education, retail, industrial |
| 3.0 | 2026-01-08 | Auto-generated | Added WiFi 6E/7 deep dive, OFDMA, MU-MIMO, BSS coloring, TWT |
| 3.1 | 2026-01-08 | Auto-generated | Added WiFi 7 MLO, puncturing, 4K-QAM, multi-RU, enhanced security |
| 3.2 | 2026-01-08 | Auto-generated | Added FILS, DPP, enterprise security, certificate management |
| 3.3 | 2026-01-08 | Auto-generated | Added power management, airtime fairness, channel utilization |
| 3.4 | 2026-01-08 | Auto-generated | Added client steering, band selection, load balancing algorithms |
| 3.5 | 2026-01-08 | Auto-generated | Added mesh networking, WDS, repeater modes, backhaul optimization |

---

## Appendix CR: Mesh Networking Deep Dive

### CR.1 Mesh Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    MESH ARCHITECTURE                                         │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  Mesh Network Topology:                                                      │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │                    ┌─────────────────────────────────────┐          │    │
│  │                    │           Internet                   │          │    │
│  │                    └─────────────┬───────────────────────┘          │    │
│  │                                  │                                   │    │
│  │                           ┌──────┴──────┐                           │    │
│  │                           │   Gateway   │                           │    │
│  │                           │   (Root)    │                           │    │
│  │                           └──────┬──────┘                           │    │
│  │                                  │                                   │    │
│  │              ┌───────────────────┼───────────────────┐              │    │
│  │              │                   │                   │              │    │
│  │       ┌──────┴──────┐     ┌──────┴──────┐     ┌──────┴──────┐      │    │
│  │       │   Mesh AP   │─────│   Mesh AP   │─────│   Mesh AP   │      │    │
│  │       │   (Node 1)  │     │   (Node 2)  │     │   (Node 3)  │      │    │
│  │       └──────┬──────┘     └──────┬──────┘     └──────┬──────┘      │    │
│  │              │                   │                   │              │    │
│  │       ┌──────┴──────┐     ┌──────┴──────┐     ┌──────┴──────┐      │    │
│  │       │   Mesh AP   │─────│   Mesh AP   │─────│   Mesh AP   │      │    │
│  │       │   (Node 4)  │     │   (Node 5)  │     │   (Node 6)  │      │    │
│  │       └─────────────┘     └─────────────┘     └─────────────┘      │    │
│  │                                                                      │    │
│  │  Key Concepts:                                                       │    │
│  │  - Root/Gateway: Wired connection to network                         │    │
│  │  - Mesh Node: Wireless-only connection                               │    │
│  │  - Backhaul: Inter-node wireless links                               │    │
│  │  - Fronthaul: Client-facing wireless                                 │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  Mesh Roles:                                                                 │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  ┌────────────────────────────────────────────────────────────┐     │    │
│  │  │ Role                Description                            │     │    │
│  │  │ ────                ───────────                            │     │    │
│  │  │ Mesh Portal (MPP)   Gateway to external network            │     │    │
│  │  │ Mesh Point (MP)     Mesh node, forwards traffic            │     │    │
│  │  │ Mesh AP (MAP)       MP + AP functionality for clients      │     │    │
│  │  │ Mesh STA (MSTA)     Client connected to mesh               │     │    │
│  │  └────────────────────────────────────────────────────────────┘     │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  802.11s Mesh:                                                               │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  - Standard mesh protocol (IEEE 802.11s)                             │    │
│  │  - HWMP (Hybrid Wireless Mesh Protocol) for routing                  │    │
│  │  - SAE for mesh peer authentication                                  │    │
│  │  - AMPE (Authenticated Mesh Peering Exchange)                        │    │
│  │                                                                      │    │
│  │  Configuration:                                                      │    │
│  │  # hostapd.conf for mesh                                             │    │
│  │  mode=mesh                                                           │    │
│  │  mesh_id=MyMeshNetwork                                               │    │
│  │  mesh_fwding=1                                                       │    │
│  │  mesh_rssi_threshold=-70                                             │    │
│  │  mesh_hwmp_active_path_timeout=5000                                  │    │
│  │  mesh_hwmp_preq_min_interval=10                                      │    │
│  │  mesh_hwmp_net_diameter_traversal_time=50                            │    │
│  │  mesh_hwmp_rootmode=4                                                │    │
│  │  mesh_gate_announcements=1                                           │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### CR.2 Mesh Routing (HWMP)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    HWMP (HYBRID WIRELESS MESH PROTOCOL)                      │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  HWMP Overview:                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  - Combines reactive and proactive routing                           │    │
│  │  - Reactive: On-demand path discovery (like AODV)                    │    │
│  │  - Proactive: Tree-based routing to root mesh portal                 │    │
│  │                                                                      │    │
│  │  Frame Types:                                                        │    │
│  │  ┌────────────────────────────────────────────────────────────┐     │    │
│  │  │ Frame               Purpose                                │     │    │
│  │  │ ─────               ───────                                │     │    │
│  │  │ PREQ                Path Request (discover route)          │     │    │
│  │  │ PREP                Path Reply (return route info)         │     │    │
│  │  │ PERR                Path Error (route broken)              │     │    │
│  │  │ RANN                Root Announcement (proactive)          │     │    │
│  │  │ GANN                Gate Announcement (portal)             │     │    │
│  │  └────────────────────────────────────────────────────────────┘     │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  Reactive Path Discovery:                                                    │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  Source                Node A          Node B          Destination   │    │
│  │    │                     │               │                 │         │    │
│  │    │ ── PREQ (broadcast) ─────────────────────────────────>│         │    │
│  │    │                     │               │                 │         │    │
│  │    │                     │ ── PREQ ─────>│                 │         │    │
│  │    │                     │               │                 │         │    │
│  │    │                     │               │ ── PREQ ───────>│         │    │
│  │    │                     │               │                 │         │    │
│  │    │                     │               │ <── PREP ───────│         │    │
│  │    │                     │               │                 │         │    │
│  │    │                     │ <── PREP ─────│                 │         │    │
│  │    │                     │               │                 │         │    │
│  │    │ <── PREP ───────────│               │                 │         │    │
│  │    │                     │               │                 │         │    │
│  │    │ ══ Data Path Established ═══════════════════════════>│         │    │
│  │    │                     │               │                 │         │    │
│  │                                                                      │    │
│  │  Path Metric:                                                        │    │
│  │  - Airtime Link Metric (ALM)                                         │    │
│  │  - ALM = (O + Bt/r) / (1 - ef)                                       │    │
│  │  - O = overhead (channel access, headers)                            │    │
│  │  - Bt = test frame length                                            │    │
│  │  - r = data rate                                                     │    │
│  │  - ef = frame error rate                                             │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  Proactive Tree Building:                                                    │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  Root Portal                                                         │    │
│  │      │                                                               │    │
│  │      │ ── RANN (broadcast) ──────────────────────────────────>       │    │
│  │      │                                                               │    │
│  │      │    All nodes receive RANN and build path to root              │    │
│  │      │                                                               │    │
│  │      │ <── PREQ (unicast to root) ────────────────────────────       │    │
│  │      │                                                               │    │
│  │      │ ── PREP (unicast to node) ────────────────────────────>       │    │
│  │      │                                                               │    │
│  │      │    Tree structure established                                 │    │
│  │      │                                                               │    │
│  │                                                                      │    │
│  │  Root Modes:                                                         │    │
│  │  - Mode 0: No root                                                   │    │
│  │  - Mode 1: Root without RANN                                         │    │
│  │  - Mode 2: Root with RANN                                            │    │
│  │  - Mode 3: Root with proactive PREQ                                  │    │
│  │  - Mode 4: Root with RANN and proactive PREQ                         │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### CR.3 Backhaul Optimization

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    BACKHAUL OPTIMIZATION                                     │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  Backhaul Types:                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  ┌────────────────────────────────────────────────────────────┐     │    │
│  │  │ Type                Description                 Speed      │     │    │
│  │  │ ────                ───────────                 ─────      │     │    │
│  │  │ Wired               Ethernet backhaul           1-10 Gbps  │     │    │
│  │  │ Dedicated Radio     Separate radio for backhaul 1-4 Gbps   │     │    │
│  │  │ Shared Radio        Same radio for front/back   500 Mbps   │     │    │
│  │  │ Multi-Band          Use multiple bands          2-6 Gbps   │     │    │
│  │  └────────────────────────────────────────────────────────────┘     │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  Dedicated Backhaul Radio:                                                   │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  ┌─────────────────────────────────────────────────────────────┐    │    │
│  │  │                                                              │    │    │
│  │  │  Mesh AP (Tri-Band)                                          │    │    │
│  │  │  ┌─────────────────────────────────────────────────────┐    │    │    │
│  │  │  │                                                      │    │    │    │
│  │  │  │  Radio 1 (2.4 GHz)  ──────> Client Access            │    │    │    │
│  │  │  │                                                      │    │    │    │
│  │  │  │  Radio 2 (5 GHz-1)  ──────> Client Access            │    │    │    │
│  │  │  │                                                      │    │    │    │
│  │  │  │  Radio 3 (5 GHz-2)  ──────> Dedicated Backhaul       │    │    │    │
│  │  │  │                                                      │    │    │    │
│  │  │  └─────────────────────────────────────────────────────┘    │    │    │
│  │  │                                                              │    │    │
│  │  └─────────────────────────────────────────────────────────────┘    │    │
│  │                                                                      │    │
│  │  Benefits:                                                           │    │
│  │  - No contention between client and backhaul traffic                 │    │
│  │  - Full bandwidth for backhaul                                       │    │
│  │  - Lower latency                                                     │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  Multi-Link Backhaul (WiFi 7):                                               │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  ┌─────────────────────────────────────────────────────────────┐    │    │
│  │  │                                                              │    │    │
│  │  │  Mesh AP 1                      Mesh AP 2                    │    │    │
│  │  │  ┌─────────┐                    ┌─────────┐                  │    │    │
│  │  │  │ 2.4 GHz │ ═══════════════════│ 2.4 GHz │  Link 1          │    │    │
│  │  │  │ 5 GHz   │ ═══════════════════│ 5 GHz   │  Link 2          │    │    │
│  │  │  │ 6 GHz   │ ═══════════════════│ 6 GHz   │  Link 3          │    │    │
│  │  │  └─────────┘                    └─────────┘                  │    │    │
│  │  │                                                              │    │    │
│  │  │  MLO aggregates all links for maximum throughput             │    │    │
│  │  │  Automatic failover if one link degrades                     │    │    │
│  │  │                                                              │    │    │
│  │  └─────────────────────────────────────────────────────────────┘    │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  Backhaul Channel Selection:                                                 │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  Considerations:                                                     │    │
│  │  - Avoid DFS channels for stability                                  │    │
│  │  - Use widest channel width possible                                 │    │
│  │  - Minimize interference with client channels                        │    │
│  │  - Consider regulatory limits                                        │    │
│  │                                                                      │    │
│  │  Recommended Channels:                                               │    │
│  │  ┌────────────────────────────────────────────────────────────┐     │    │
│  │  │ Band                Backhaul Channels                      │     │    │
│  │  │ ────                ─────────────────                      │     │    │
│  │  │ 5 GHz (non-DFS)     36, 40, 44, 48, 149, 153, 157, 161     │     │    │
│  │  │ 5 GHz (DFS)         52-144 (if radar unlikely)             │     │    │
│  │  │ 6 GHz               Any (no DFS, no legacy)                │     │    │
│  │  └────────────────────────────────────────────────────────────┘     │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Appendix CS: WDS (Wireless Distribution System)

### CS.1 WDS Overview

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    WDS OVERVIEW                                              │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  WDS vs Mesh:                                                                │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  ┌────────────────────────────────────────────────────────────┐     │    │
│  │  │ Feature             WDS                 Mesh (802.11s)     │     │    │
│  │  │ ───────             ───                 ──────────────     │     │    │
│  │  │ Topology            Static              Dynamic            │     │    │
│  │  │ Configuration       Manual              Automatic          │     │    │
│  │  │ Routing             Layer 2 bridge      Layer 2/3 routing  │     │    │
│  │  │ Self-healing        No                  Yes                │     │    │
│  │  │ Scalability         Limited             Good               │     │    │
│  │  │ Interoperability    Vendor-specific     Standard           │     │    │
│  │  │ Complexity          Low                 Higher             │     │    │
│  │  └────────────────────────────────────────────────────────────┘     │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  WDS Topology:                                                               │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │                    ┌─────────────────────────────────────┐          │    │
│  │                    │           Wired Network              │          │    │
│  │                    └─────────────┬───────────────────────┘          │    │
│  │                                  │                                   │    │
│  │                           ┌──────┴──────┐                           │    │
│  │                           │   Root AP   │                           │    │
│  │                           │   (WDS)     │                           │    │
│  │                           └──────┬──────┘                           │    │
│  │                                  │                                   │    │
│  │                    ┌─────────────┼─────────────┐                    │    │
│  │                    │             │             │                    │    │
│  │             ┌──────┴──────┐ ┌────┴────┐ ┌──────┴──────┐            │    │
│  │             │  WDS AP 1   │ │ WDS AP 2│ │  WDS AP 3   │            │    │
│  │             │  (Leaf)     │ │ (Leaf)  │ │  (Leaf)     │            │    │
│  │             └─────────────┘ └─────────┘ └─────────────┘            │    │
│  │                                                                      │    │
│  │  Note: WDS links are statically configured                           │    │
│  │  Each AP knows its WDS peer MAC addresses                            │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  WDS 4-Address Frame:                                                        │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  Standard 3-Address Frame:                                           │    │
│  │  ┌────────────────────────────────────────────────────────────┐     │    │
│  │  │ Address 1    │ Address 2    │ Address 3    │ Data          │     │    │
│  │  │ (Receiver)   │ (Transmitter)│ (BSSID)      │               │     │    │
│  │  └────────────────────────────────────────────────────────────┘     │    │
│  │                                                                      │    │
│  │  WDS 4-Address Frame:                                                │    │
│  │  ┌────────────────────────────────────────────────────────────┐     │    │
│  │  │ Address 1    │ Address 2    │ Address 3    │ Address 4    │     │    │
│  │  │ (Receiver)   │ (Transmitter)│ (Dest MAC)   │ (Source MAC) │     │    │
│  │  └────────────────────────────────────────────────────────────┘     │    │
│  │                                                                      │    │
│  │  - ToDS=1, FromDS=1 indicates WDS frame                              │    │
│  │  - Allows bridging of Ethernet frames over wireless                  │    │
│  │  - Preserves original source and destination MAC                     │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  WDS Configuration:                                                          │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  # Root AP (hostapd.conf)                                            │    │
│  │  interface=wlan0                                                     │    │
│  │  ssid=MyNetwork                                                      │    │
│  │  wds_sta=1                                                           │    │
│  │  wds_bridge=br0                                                      │    │
│  │                                                                      │    │
│  │  # Leaf AP (wpa_supplicant.conf)                                     │    │
│  │  network={                                                           │    │
│  │      ssid="MyNetwork"                                                │    │
│  │      psk="password"                                                  │    │
│  │      mode=0                                                          │    │
│  │      wds=1                                                           │    │
│  │  }                                                                   │    │
│  │                                                                      │    │
│  │  # Bridge configuration                                              │    │
│  │  brctl addbr br0                                                     │    │
│  │  brctl addif br0 eth0                                                │    │
│  │  brctl addif br0 wlan0                                               │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Appendix CT: Repeater Mode

### CT.1 Repeater Overview

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    REPEATER MODE                                             │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  Repeater Concept:                                                           │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  ┌─────────────────────────────────────────────────────────────┐    │    │
│  │  │                                                              │    │    │
│  │  │  Main AP                 Repeater                 Client     │    │    │
│  │  │  ┌─────┐                 ┌─────┐                 ┌─────┐    │    │    │
│  │  │  │     │ ═══════════════ │     │ ═══════════════ │     │    │    │    │
│  │  │  │     │   Uplink        │     │   Downlink      │     │    │    │    │
│  │  │  └─────┘                 └─────┘                 └─────┘    │    │    │
│  │  │                                                              │    │    │
│  │  │  Repeater acts as:                                           │    │    │
│  │  │  - Client to main AP (uplink)                                │    │    │
│  │  │  - AP to clients (downlink)                                  │    │    │
│  │  │                                                              │    │    │
│  │  └─────────────────────────────────────────────────────────────┘    │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  Repeater Types:                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  ┌────────────────────────────────────────────────────────────┐     │    │
│  │  │ Type                Description                 Efficiency │     │    │
│  │  │ ────                ───────────                 ────────── │     │    │
│  │  │ Single-Radio        Same radio for up/down      ~50%       │     │    │
│  │  │ Dual-Radio          Separate radios             ~90%       │     │    │
│  │  │ Same-Channel        Same channel up/down        ~40%       │     │    │
│  │  │ Cross-Band          Different bands             ~85%       │     │    │
│  │  └────────────────────────────────────────────────────────────┘     │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  Single-Radio Repeater Timing:                                               │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  Time ──────────────────────────────────────────────────────────>    │    │
│  │                                                                      │    │
│  │  ┌────────┐          ┌────────┐          ┌────────┐                 │    │
│  │  │ Uplink │          │Downlink│          │ Uplink │                 │    │
│  │  │  TX/RX │          │  TX/RX │          │  TX/RX │                 │    │
│  │  └────────┘          └────────┘          └────────┘                 │    │
│  │                                                                      │    │
│  │  - Radio switches between uplink and downlink                        │    │
│  │  - Each frame transmitted twice (received then retransmitted)        │    │
│  │  - Effective throughput: ~50% of single link                         │    │
│  │  - Latency increased                                                 │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  Dual-Radio Repeater:                                                        │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  ┌─────────────────────────────────────────────────────────────┐    │    │
│  │  │                                                              │    │    │
│  │  │  Main AP                 Repeater                 Client     │    │    │
│  │  │  ┌─────┐                 ┌─────┐                 ┌─────┐    │    │    │
│  │  │  │     │ ═══ 5 GHz ═════ │Radio│                 │     │    │    │    │
│  │  │  │     │                 │  1  │                 │     │    │    │    │
│  │  │  │     │                 ├─────┤                 │     │    │    │    │
│  │  │  │     │                 │Radio│ ═══ 2.4 GHz ═══ │     │    │    │    │
│  │  │  │     │                 │  2  │                 │     │    │    │    │
│  │  │  └─────┘                 └─────┘                 └─────┘    │    │    │
│  │  │                                                              │    │    │
│  │  │  - Simultaneous uplink and downlink                          │    │    │
│  │  │  - No throughput penalty                                     │    │    │
│  │  │  - Different bands avoid interference                        │    │    │
│  │  │                                                              │    │    │
│  │  └─────────────────────────────────────────────────────────────┘    │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Document Revision History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2026-01-08 | Auto-generated | Initial document creation |
| 1.1 | 2026-01-08 | Auto-generated | Added packet capture analysis, regulatory domains, client compatibility |
| 1.2 | 2026-01-08 | Auto-generated | Added EAP methods, band steering, load balancing, mesh networking, power save |
| 1.3 | 2026-01-08 | Auto-generated | Added RADIUS attributes, debug commands, troubleshooting flowchart, quick reference |
| 1.4 | 2026-01-08 | Auto-generated | Added WiFi 7 features, Hotspot 2.0 deep dive, glossary, standards reference |
| 1.5 | 2026-01-08 | Auto-generated | Added security attacks, performance optimization, complete hostapd config |
| 1.6 | 2026-01-08 | Auto-generated | Added frame formats, information elements, status/reason codes |
| 1.7 | 2026-01-08 | Auto-generated | Added vendor extensions, debugging/logging, packet capture commands |
| 1.8 | 2026-01-08 | Auto-generated | Added test case reference, regulatory domain deep dive |
| 1.9 | 2026-01-08 | Auto-generated | Added action frame reference, error scenarios and troubleshooting |
| 2.0 | 2026-01-08 | Auto-generated | Added Wireshark filter reference, complete configuration examples |
| 2.1 | 2026-01-08 | Auto-generated | Added performance benchmarks, client device compatibility matrix |
| 2.2 | 2026-01-08 | Auto-generated | Added WiFi Alliance certification, security checklist, capacity planning |
| 2.3 | 2026-01-08 | Auto-generated | Added antenna/RF considerations, troubleshooting trees, timing diagrams |
| 2.4 | 2026-01-08 | Auto-generated | Added QoS/WMM, deployment topologies, compliance, advanced debugging |
| 2.5 | 2026-01-08 | Auto-generated | Added supplicant config, VLAN, rate limiting, HA, IoT profiling |
| 2.6 | 2026-01-08 | Auto-generated | Added captive portal, location services, spectrum analysis, migration, API |
| 2.7 | 2026-01-08 | Auto-generated | Added multicast, VoWiFi, enterprise integration, monitoring, disaster recovery |
| 2.8 | 2026-01-08 | Auto-generated | Added WIDS, cloud management, performance testing, compliance, checklists |
| 2.9 | 2026-01-08 | Auto-generated | Added outdoor WiFi, stadium/venue, healthcare, education, retail, industrial |
| 3.0 | 2026-01-08 | Auto-generated | Added WiFi 6E/7 deep dive, OFDMA, MU-MIMO, BSS coloring, TWT |
| 3.1 | 2026-01-08 | Auto-generated | Added WiFi 7 MLO, puncturing, 4K-QAM, multi-RU, enhanced security |
| 3.2 | 2026-01-08 | Auto-generated | Added FILS, DPP, enterprise security, certificate management |
| 3.3 | 2026-01-08 | Auto-generated | Added power management, airtime fairness, channel utilization |
| 3.4 | 2026-01-08 | Auto-generated | Added client steering, band selection, load balancing algorithms |
| 3.5 | 2026-01-08 | Auto-generated | Added mesh networking, WDS, repeater modes, backhaul optimization |
| 3.6 | 2026-01-08 | Auto-generated | Added roaming protocols, 802.11k/v/r deep dive, seamless handoff |

---

## Appendix CU: Roaming Protocols Deep Dive

### CU.1 802.11k (Radio Resource Management)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    802.11k RADIO RESOURCE MANAGEMENT                         │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  Purpose:                                                                    │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  - Provide clients with information about neighboring APs            │    │
│  │  - Enable faster roaming decisions                                   │    │
│  │  - Reduce scanning time during roaming                               │    │
│  │  - Improve overall network efficiency                                │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  Neighbor Report:                                                            │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  Client                              AP                              │    │
│  │    │                                  │                              │    │
│  │    │ ── Neighbor Report Request ─────>│                              │    │
│  │    │    (Action Frame)                │                              │    │
│  │    │                                  │                              │    │
│  │    │ <── Neighbor Report Response ────│                              │    │
│  │    │    (List of neighbor APs)        │                              │    │
│  │    │                                  │                              │    │
│  │                                                                      │    │
│  │  Neighbor Report Element:                                            │    │
│  │  ┌────────────────────────────────────────────────────────────┐     │    │
│  │  │ Field               Size      Description                  │     │    │
│  │  │ ─────               ────      ───────────                  │     │    │
│  │  │ BSSID               6 bytes   Neighbor AP MAC address      │     │    │
│  │  │ BSSID Info          4 bytes   Capabilities, security       │     │    │
│  │  │ Operating Class     1 byte    Regulatory class             │     │    │
│  │  │ Channel Number      1 byte    Channel of neighbor          │     │    │
│  │  │ PHY Type            1 byte    802.11a/b/g/n/ac/ax          │     │    │
│  │  │ TSF Info (opt)      Variable  Timing synchronization       │     │    │
│  │  │ Country (opt)       Variable  Country string               │     │    │
│  │  └────────────────────────────────────────────────────────────┘     │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  BSSID Information Field:                                                    │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  Bits 0-1:   AP Reachability                                         │    │
│  │              00 = Reserved                                           │    │
│  │              01 = Not reachable                                      │    │
│  │              10 = Unknown                                            │    │
│  │              11 = Reachable                                          │    │
│  │                                                                      │    │
│  │  Bit 2:      Security (same as current)                              │    │
│  │  Bit 3:      Key Scope (same PMK)                                    │    │
│  │  Bit 4:      Spectrum Management                                     │    │
│  │  Bit 5:      QoS                                                     │    │
│  │  Bit 6:      APSD                                                    │    │
│  │  Bit 7:      Radio Measurement                                       │    │
│  │  Bit 8:      Delayed Block Ack                                       │    │
│  │  Bit 9:      Immediate Block Ack                                     │    │
│  │  Bit 10:     Mobility Domain                                         │    │
│  │  Bit 11:     High Throughput                                         │    │
│  │  Bit 12:     Very High Throughput                                    │    │
│  │  Bit 13:     FTM Responder                                           │    │
│  │  Bit 14:     HE (WiFi 6)                                             │    │
│  │  Bit 15:     EHT (WiFi 7)                                            │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  Configuration:                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  # hostapd.conf                                                      │    │
│  │  rrm_neighbor_report=1                                               │    │
│  │  rrm_beacon_report=1                                                 │    │
│  │                                                                      │    │
│  │  # Static neighbor list                                              │    │
│  │  neighbor=aa:bb:cc:dd:ee:ff,MySSID,115,36,7,0301ff                   │    │
│  │  neighbor=11:22:33:44:55:66,MySSID,115,44,7,0301ff                   │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### CU.2 802.11v (BSS Transition Management)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    802.11v BSS TRANSITION MANAGEMENT                         │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  Purpose:                                                                    │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  - Network-assisted roaming                                          │    │
│  │  - AP can suggest or require client to roam                          │    │
│  │  - Load balancing across APs                                         │    │
│  │  - Band steering (2.4 GHz to 5 GHz)                                  │    │
│  │  - Graceful AP shutdown                                              │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  BTM Request/Response:                                                       │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  Client                              AP                              │    │
│  │    │                                  │                              │    │
│  │    │ <── BTM Request ─────────────────│                              │    │
│  │    │    (Candidate list, reason)      │                              │    │
│  │    │                                  │                              │    │
│  │    │ ── BTM Response ────────────────>│                              │    │
│  │    │    (Accept/Reject, target BSSID) │                              │    │
│  │    │                                  │                              │    │
│  │    │ ── Reassociation ───────────────────────────> Target AP         │    │
│  │    │                                  │                              │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  BTM Request Fields:                                                         │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  ┌────────────────────────────────────────────────────────────┐     │    │
│  │  │ Field                   Description                        │     │    │
│  │  │ ─────                   ───────────                        │     │    │
│  │  │ Request Mode            Flags for request behavior         │     │    │
│  │  │   Bit 0: Preferred      Candidate list is preferred        │     │    │
│  │  │   Bit 1: Abridged       Use abridged candidate list        │     │    │
│  │  │   Bit 2: Disassoc Imm   Disassociate immediately           │     │    │
│  │  │   Bit 3: BSS Term       BSS termination included           │     │    │
│  │  │   Bit 4: ESS Disassoc   ESS disassociation imminent        │     │    │
│  │  │ Disassoc Timer          Time until disassociation (TUs)    │     │    │
│  │  │ Validity Interval       How long candidates are valid      │     │    │
│  │  │ BSS Termination         When BSS will terminate            │     │    │
│  │  │ Session Info URL        Captive portal URL                 │     │    │
│  │  │ Candidate List          List of target BSSIDs              │     │    │
│  │  └────────────────────────────────────────────────────────────┘     │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  BTM Response Status Codes:                                                  │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  ┌────────────────────────────────────────────────────────────┐     │    │
│  │  │ Code    Status                                             │     │    │
│  │  │ ────    ──────                                             │     │    │
│  │  │ 0       Accept                                             │     │    │
│  │  │ 1       Reject - Unspecified                               │     │    │
│  │  │ 2       Reject - Insufficient beacon/probe response        │     │    │
│  │  │ 3       Reject - Insufficient capacity                     │     │    │
│  │  │ 4       Reject - BSS termination undesired                 │     │    │
│  │  │ 5       Reject - BSS termination delay requested           │     │    │
│  │  │ 6       Reject - STA BSS candidate list provided           │     │    │
│  │  │ 7       Reject - No suitable BSS transition candidates     │     │    │
│  │  │ 8       Reject - Leaving ESS                               │     │    │
│  │  └────────────────────────────────────────────────────────────┘     │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  Configuration:                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  # hostapd.conf                                                      │    │
│  │  bss_transition=1                                                    │    │
│  │  wnm_sleep_mode=1                                                    │    │
│  │                                                                      │    │
│  │  # CLI command to send BTM request                                   │    │
│  │  hostapd_cli bss_tm_req <sta_mac> neighbor=<bssid>,<info>,<op>,<ch>  │    │
│  │                                                                      │    │
│  │  # Example                                                           │    │
│  │  hostapd_cli bss_tm_req 00:11:22:33:44:55 \                          │    │
│  │      neighbor=aa:bb:cc:dd:ee:ff,0x0000,115,36,7 \                    │    │
│  │      pref=1 disassoc_timer=100                                       │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### CU.3 802.11r (Fast BSS Transition)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    802.11r FAST BSS TRANSITION                               │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  Purpose:                                                                    │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  - Reduce roaming time to < 50ms                                     │    │
│  │  - Pre-establish security with target AP                             │    │
│  │  - Eliminate full 4-way handshake during roam                        │    │
│  │  - Critical for voice/video applications                             │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  FT Key Hierarchy:                                                           │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │                    ┌─────────────────┐                               │    │
│  │                    │       MSK       │                               │    │
│  │                    │ (Master Session │                               │    │
│  │                    │     Key)        │                               │    │
│  │                    └────────┬────────┘                               │    │
│  │                             │                                        │    │
│  │                    ┌────────┴────────┐                               │    │
│  │                    │      PMK-R0     │                               │    │
│  │                    │ (Held by R0KH)  │                               │    │
│  │                    └────────┬────────┘                               │    │
│  │                             │                                        │    │
│  │         ┌───────────────────┼───────────────────┐                    │    │
│  │         │                   │                   │                    │    │
│  │  ┌──────┴──────┐     ┌──────┴──────┐     ┌──────┴──────┐            │    │
│  │  │   PMK-R1    │     │   PMK-R1    │     │   PMK-R1    │            │    │
│  │  │   (AP 1)    │     │   (AP 2)    │     │   (AP 3)    │            │    │
│  │  └──────┬──────┘     └──────┬──────┘     └──────┬──────┘            │    │
│  │         │                   │                   │                    │    │
│  │  ┌──────┴──────┐     ┌──────┴──────┐     ┌──────┴──────┐            │    │
│  │  │     PTK     │     │     PTK     │     │     PTK     │            │    │
│  │  │   (AP 1)    │     │   (AP 2)    │     │   (AP 3)    │            │    │
│  │  └─────────────┘     └─────────────┘     └─────────────┘            │    │
│  │                                                                      │    │
│  │  R0KH = R0 Key Holder (usually first AP or controller)               │    │
│  │  R1KH = R1 Key Holder (each AP in mobility domain)                   │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  FT Over-the-Air (OTA):                                                      │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  Client                Current AP              Target AP             │    │
│  │    │                       │                       │                 │    │
│  │    │ ══ Connected ═════════│                       │                 │    │
│  │    │                       │                       │                 │    │
│  │    │ ── FT Auth Request ───────────────────────────>│                │    │
│  │    │    (SNonce, PMKR0Name)│                       │                 │    │
│  │    │                       │                       │                 │    │
│  │    │                       │ <── PMK-R1 Request ───│                 │    │
│  │    │                       │                       │                 │    │
│  │    │                       │ ── PMK-R1 Response ──>│                 │    │
│  │    │                       │                       │                 │    │
│  │    │ <── FT Auth Response ─────────────────────────│                 │    │
│  │    │    (ANonce, PMKR1Name)│                       │                 │    │
│  │    │                       │                       │                 │    │
│  │    │ ── Reassoc Request ───────────────────────────>│                │    │
│  │    │    (MIC, GTK request) │                       │                 │    │
│  │    │                       │                       │                 │    │
│  │    │ <── Reassoc Response ─────────────────────────│                 │    │
│  │    │    (GTK)              │                       │                 │    │
│  │    │                       │                       │                 │    │
│  │    │ ══ Connected ═════════════════════════════════│                 │    │
│  │    │                       │                       │                 │    │
│  │                                                                      │    │
│  │  Total roam time: ~50ms (vs 200-500ms without FT)                    │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  FT Over-the-DS (ODS):                                                       │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  Client                Current AP              Target AP             │    │
│  │    │                       │                       │                 │    │
│  │    │ ══ Connected ═════════│                       │                 │    │
│  │    │                       │                       │                 │    │
│  │    │ ── FT Action (Req) ──>│                       │                 │    │
│  │    │                       │                       │                 │    │
│  │    │                       │ ── FT Request ───────>│                 │    │
│  │    │                       │    (via DS)           │                 │    │
│  │    │                       │                       │                 │    │
│  │    │                       │ <── FT Response ──────│                 │    │
│  │    │                       │    (via DS)           │                 │    │
│  │    │                       │                       │                 │    │
│  │    │ <── FT Action (Resp) ─│                       │                 │    │
│  │    │                       │                       │                 │    │
│  │    │ ── Reassoc Request ───────────────────────────>│                │    │
│  │    │                       │                       │                 │    │
│  │    │ <── Reassoc Response ─────────────────────────│                 │    │
│  │    │                       │                       │                 │    │
│  │    │ ══ Connected ═════════════════════════════════│                 │    │
│  │    │                       │                       │                 │    │
│  │                                                                      │    │
│  │  Benefits:                                                           │    │
│  │  - Pre-authentication before leaving current AP                      │    │
│  │  - Even faster roam (authentication already done)                    │    │
│  │  - Requires DS (distribution system) connectivity                    │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  Configuration:                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  # hostapd.conf                                                      │    │
│  │  mobility_domain=a1b2                                                │    │
│  │  ft_over_ds=1                                                        │    │
│  │  ft_psk_generate_local=1                                             │    │
│  │                                                                      │    │
│  │  # R0 Key Holder                                                     │    │
│  │  nas_identifier=ap1.example.com                                      │    │
│  │  r0_key_lifetime=10000                                               │    │
│  │  r1_key_holder=000102030405                                          │    │
│  │  pmk_r1_push=1                                                       │    │
│  │                                                                      │    │
│  │  # R0KH list (other APs in mobility domain)                          │    │
│  │  r0kh=02:00:00:00:03:00 nas1.example.com 000102030405060708090a...   │    │
│  │  r0kh=02:00:00:00:04:00 nas2.example.com 000102030405060708090a...   │    │
│  │                                                                      │    │
│  │  # R1KH list                                                         │    │
│  │  r1kh=02:00:00:00:03:00 02:00:00:00:03:00 000102030405060708090a...  │    │
│  │  r1kh=02:00:00:00:04:00 02:00:00:00:04:00 000102030405060708090a...  │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Appendix CV: Roaming Decision Algorithms

### CV.1 Client Roaming Triggers

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    CLIENT ROAMING TRIGGERS                                   │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  RSSI-Based Roaming:                                                         │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  Signal Strength                                                     │    │
│  │  ▲                                                                   │    │
│  │  │                                                                   │    │
│  │  │ -50 dBm ┌────────────────────────────────────────────────────    │    │
│  │  │         │ Excellent - No roaming needed                          │    │
│  │  │ -60 dBm ├────────────────────────────────────────────────────    │    │
│  │  │         │ Good - Monitor for better AP                           │    │
│  │  │ -67 dBm ├────────────────────────────────────────────────────    │    │
│  │  │         │ Fair - Start scanning for alternatives                 │    │
│  │  │ -70 dBm ├────────────────────────────────────────────────────    │    │
│  │  │         │ Poor - Actively seek better AP                         │    │
│  │  │ -75 dBm ├────────────────────────────────────────────────────    │    │
│  │  │         │ Critical - Roam immediately                            │    │
│  │  │ -80 dBm └────────────────────────────────────────────────────    │    │
│  │  │         │ Disconnection likely                                   │    │
│  │  └──────────────────────────────────────────────────────────────>    │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  Roaming Hysteresis:                                                         │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  Purpose: Prevent ping-pong roaming between APs                      │    │
│  │                                                                      │    │
│  │  ┌────────────────────────────────────────────────────────────┐     │    │
│  │  │                                                             │     │    │
│  │  │  Current AP: -70 dBm                                        │     │    │
│  │  │  Target AP:  -65 dBm                                        │     │    │
│  │  │  Difference: 5 dB                                           │     │    │
│  │  │  Hysteresis: 8 dB                                           │     │    │
│  │  │                                                             │     │    │
│  │  │  Decision: Stay (5 dB < 8 dB threshold)                     │     │    │
│  │  │                                                             │     │    │
│  │  │  ─────────────────────────────────────────────────────────  │     │    │
│  │  │                                                             │     │    │
│  │  │  Current AP: -75 dBm                                        │     │    │
│  │  │  Target AP:  -60 dBm                                        │     │    │
│  │  │  Difference: 15 dB                                          │     │    │
│  │  │  Hysteresis: 8 dB                                           │     │    │
│  │  │                                                             │     │    │
│  │  │  Decision: Roam (15 dB > 8 dB threshold)                    │     │    │
│  │  │                                                             │     │    │
│  │  └────────────────────────────────────────────────────────────┘     │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  Other Roaming Triggers:                                                     │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  ┌────────────────────────────────────────────────────────────┐     │    │
│  │  │ Trigger              Description                           │     │    │
│  │  │ ───────              ───────────                           │     │    │
│  │  │ Beacon Loss          No beacons received for threshold     │     │    │
│  │  │ High Retry Rate      Too many retransmissions              │     │    │
│  │  │ Low Data Rate        MCS dropped below threshold           │     │    │
│  │  │ BTM Request          AP requested transition               │     │    │
│  │  │ Deauthentication     Forced disconnect                     │     │    │
│  │  │ Channel Change       AP changed channel (DFS)              │     │    │
│  │  │ Load Balancing       AP overloaded                         │     │    │
│  │  └────────────────────────────────────────────────────────────┘     │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### CV.2 AP Selection Algorithm

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    AP SELECTION ALGORITHM                                    │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  Selection Criteria:                                                         │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  ┌────────────────────────────────────────────────────────────┐     │    │
│  │  │ Criterion           Weight    Description                  │     │    │
│  │  │ ─────────           ──────    ───────────                  │     │    │
│  │  │ RSSI                40%       Signal strength              │     │    │
│  │  │ Band                20%       Prefer 5/6 GHz over 2.4 GHz  │     │    │
│  │  │ Channel Width       15%       Wider = better               │     │    │
│  │  │ Load                10%       Lower utilization preferred  │     │    │
│  │  │ Security Match      10%       Same security as current     │     │    │
│  │  │ FT Support          5%        Fast transition capable      │     │    │
│  │  └────────────────────────────────────────────────────────────┘     │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  Selection Flow:                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  ┌─────────────────────────────────────────────────────────────┐    │    │
│  │  │                                                              │    │    │
│  │  │  1. Scan for APs                                             │    │    │
│  │  │     │                                                        │    │    │
│  │  │     ▼                                                        │    │    │
│  │  │  2. Filter by SSID                                           │    │    │
│  │  │     │                                                        │    │    │
│  │  │     ▼                                                        │    │    │
│  │  │  3. Filter by security                                       │    │    │
│  │  │     │                                                        │    │    │
│  │  │     ▼                                                        │    │    │
│  │  │  4. Filter by minimum RSSI                                   │    │    │
│  │  │     │                                                        │    │    │
│  │  │     ▼                                                        │    │    │
│  │  │  5. Calculate score for each AP                              │    │    │
│  │  │     │                                                        │    │    │
│  │  │     ▼                                                        │    │    │
│  │  │  6. Apply hysteresis vs current AP                           │    │    │
│  │  │     │                                                        │    │    │
│  │  │     ▼                                                        │    │    │
│  │  │  7. Select highest scoring AP                                │    │    │
│  │  │                                                              │    │    │
│  │  └─────────────────────────────────────────────────────────────┘    │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  Score Calculation Example:                                                  │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  AP 1 (5 GHz, 80 MHz, -65 dBm, 30% load, FT):                        │    │
│  │  - RSSI:    ((-65 - (-90)) / 40) × 40 = 25                           │    │
│  │  - Band:    20 (5 GHz bonus)                                         │    │
│  │  - Width:   12 (80 MHz)                                              │    │
│  │  - Load:    7 (70% free)                                             │    │
│  │  - Security: 10 (match)                                              │    │
│  │  - FT:      5 (supported)                                            │    │
│  │  - Total:   79                                                       │    │
│  │                                                                      │    │
│  │  AP 2 (2.4 GHz, 20 MHz, -55 dBm, 60% load, no FT):                   │    │
│  │  - RSSI:    ((-55 - (-90)) / 40) × 40 = 35                           │    │
│  │  - Band:    0 (2.4 GHz)                                              │    │
│  │  - Width:   5 (20 MHz)                                               │    │
│  │  - Load:    4 (40% free)                                             │    │
│  │  - Security: 10 (match)                                              │    │
│  │  - FT:      0 (not supported)                                        │    │
│  │  - Total:   54                                                       │    │
│  │                                                                      │    │
│  │  Winner: AP 1 (score 79 > 54)                                        │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Document Revision History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2026-01-08 | Auto-generated | Initial document creation |
| 1.1 | 2026-01-08 | Auto-generated | Added packet capture analysis, regulatory domains, client compatibility |
| 1.2 | 2026-01-08 | Auto-generated | Added EAP methods, band steering, load balancing, mesh networking, power save |
| 1.3 | 2026-01-08 | Auto-generated | Added RADIUS attributes, debug commands, troubleshooting flowchart, quick reference |
| 1.4 | 2026-01-08 | Auto-generated | Added WiFi 7 features, Hotspot 2.0 deep dive, glossary, standards reference |
| 1.5 | 2026-01-08 | Auto-generated | Added security attacks, performance optimization, complete hostapd config |
| 1.6 | 2026-01-08 | Auto-generated | Added frame formats, information elements, status/reason codes |
| 1.7 | 2026-01-08 | Auto-generated | Added vendor extensions, debugging/logging, packet capture commands |
| 1.8 | 2026-01-08 | Auto-generated | Added test case reference, regulatory domain deep dive |
| 1.9 | 2026-01-08 | Auto-generated | Added action frame reference, error scenarios and troubleshooting |
| 2.0 | 2026-01-08 | Auto-generated | Added Wireshark filter reference, complete configuration examples |
| 2.1 | 2026-01-08 | Auto-generated | Added performance benchmarks, client device compatibility matrix |
| 2.2 | 2026-01-08 | Auto-generated | Added WiFi Alliance certification, security checklist, capacity planning |
| 2.3 | 2026-01-08 | Auto-generated | Added antenna/RF considerations, troubleshooting trees, timing diagrams |
| 2.4 | 2026-01-08 | Auto-generated | Added QoS/WMM, deployment topologies, compliance, advanced debugging |
| 2.5 | 2026-01-08 | Auto-generated | Added supplicant config, VLAN, rate limiting, HA, IoT profiling |
| 2.6 | 2026-01-08 | Auto-generated | Added captive portal, location services, spectrum analysis, migration, API |
| 2.7 | 2026-01-08 | Auto-generated | Added multicast, VoWiFi, enterprise integration, monitoring, disaster recovery |
| 2.8 | 2026-01-08 | Auto-generated | Added WIDS, cloud management, performance testing, compliance, checklists |
| 2.9 | 2026-01-08 | Auto-generated | Added outdoor WiFi, stadium/venue, healthcare, education, retail, industrial |
| 3.0 | 2026-01-08 | Auto-generated | Added WiFi 6E/7 deep dive, OFDMA, MU-MIMO, BSS coloring, TWT |
| 3.1 | 2026-01-08 | Auto-generated | Added WiFi 7 MLO, puncturing, 4K-QAM, multi-RU, enhanced security |
| 3.2 | 2026-01-08 | Auto-generated | Added FILS, DPP, enterprise security, certificate management |
| 3.3 | 2026-01-08 | Auto-generated | Added power management, airtime fairness, channel utilization |
| 3.4 | 2026-01-08 | Auto-generated | Added client steering, band selection, load balancing algorithms |
| 3.5 | 2026-01-08 | Auto-generated | Added mesh networking, WDS, repeater modes, backhaul optimization |
| 3.6 | 2026-01-08 | Auto-generated | Added roaming protocols, 802.11k/v/r deep dive, seamless handoff |
| 3.7 | 2026-01-08 | Auto-generated | Added DHCP deep dive, DNS, mDNS, service discovery |

---

## Appendix CW: DHCP Deep Dive

### CW.1 DHCP Process

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    DHCP PROCESS (DORA)                                       │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  DHCP Message Exchange:                                                      │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  Client                              DHCP Server                     │    │
│  │    │                                      │                          │    │
│  │    │ ── DHCP DISCOVER (broadcast) ───────>│                          │    │
│  │    │    src: 0.0.0.0                      │                          │    │
│  │    │    dst: 255.255.255.255              │                          │    │
│  │    │                                      │                          │    │
│  │    │ <── DHCP OFFER ──────────────────────│                          │    │
│  │    │    Offered IP: 192.168.1.100         │                          │    │
│  │    │    Lease time: 86400 seconds         │                          │    │
│  │    │                                      │                          │    │
│  │    │ ── DHCP REQUEST (broadcast) ────────>│                          │    │
│  │    │    Requested IP: 192.168.1.100       │                          │    │
│  │    │    Server ID: 192.168.1.1            │                          │    │
│  │    │                                      │                          │    │
│  │    │ <── DHCP ACK ────────────────────────│                          │    │
│  │    │    Assigned IP: 192.168.1.100        │                          │    │
│  │    │    Subnet: 255.255.255.0             │                          │    │
│  │    │    Gateway: 192.168.1.1              │                          │    │
│  │    │    DNS: 8.8.8.8, 8.8.4.4             │                          │    │
│  │    │                                      │                          │    │
│  │    │ ══ IP Address Configured ════════════│                          │    │
│  │    │                                      │                          │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  DHCP Message Types:                                                         │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  ┌────────────────────────────────────────────────────────────┐     │    │
│  │  │ Type        Code    Description                            │     │    │
│  │  │ ────        ────    ───────────                            │     │    │
│  │  │ DISCOVER    1       Client looking for DHCP servers        │     │    │
│  │  │ OFFER       2       Server offers IP address               │     │    │
│  │  │ REQUEST     3       Client requests offered IP             │     │    │
│  │  │ DECLINE     4       Client rejects offered IP              │     │    │
│  │  │ ACK         5       Server confirms assignment             │     │    │
│  │  │ NAK         6       Server rejects request                 │     │    │
│  │  │ RELEASE     7       Client releases IP address             │     │    │
│  │  │ INFORM      8       Client requests config only            │     │    │
│  │  └────────────────────────────────────────────────────────────┘     │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  DHCP Lease Lifecycle:                                                       │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  Time ──────────────────────────────────────────────────────────>    │    │
│  │                                                                      │    │
│  │  ├─────────────────────────────────────────────────────────────┤    │    │
│  │  │                    Lease Time (T)                            │    │    │
│  │  ├─────────────────────────────────────────────────────────────┤    │    │
│  │                                                                      │    │
│  │  ├───────────────────────────┤                                       │    │
│  │  │      T1 (50% of T)        │ ← Renewal timer                       │    │
│  │  ├───────────────────────────┤                                       │    │
│  │                                                                      │    │
│  │  ├─────────────────────────────────────┤                             │    │
│  │  │          T2 (87.5% of T)            │ ← Rebinding timer           │    │
│  │  ├─────────────────────────────────────┤                             │    │
│  │                                                                      │    │
│  │  At T1: Client sends REQUEST to original server (unicast)           │    │
│  │  At T2: Client sends REQUEST to any server (broadcast)              │    │
│  │  At T:  Lease expires, client must stop using IP                    │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### CW.2 DHCP Options

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    DHCP OPTIONS                                              │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  Common DHCP Options:                                                        │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  ┌────────────────────────────────────────────────────────────┐     │    │
│  │  │ Option    Name                    Description              │     │    │
│  │  │ ──────    ────                    ───────────              │     │    │
│  │  │ 1         Subnet Mask             Network mask             │     │    │
│  │  │ 3         Router                  Default gateway          │     │    │
│  │  │ 6         DNS Servers             Domain name servers      │     │    │
│  │  │ 12        Hostname                Client hostname          │     │    │
│  │  │ 15        Domain Name             DNS domain suffix        │     │    │
│  │  │ 28        Broadcast Address       Network broadcast        │     │    │
│  │  │ 42        NTP Servers             Time servers             │     │    │
│  │  │ 43        Vendor Specific         Vendor-defined options   │     │    │
│  │  │ 50        Requested IP            Client's preferred IP    │     │    │
│  │  │ 51        Lease Time              IP lease duration        │     │    │
│  │  │ 53        Message Type            DHCP message type        │     │    │
│  │  │ 54        Server Identifier       DHCP server IP           │     │    │
│  │  │ 55        Parameter Request       Options client wants     │     │    │
│  │  │ 60        Vendor Class ID         Client vendor/type       │     │    │
│  │  │ 61        Client Identifier       Unique client ID         │     │    │
│  │  │ 66        TFTP Server             Boot server name         │     │    │
│  │  │ 67        Bootfile Name           Boot file path           │     │    │
│  │  │ 82        Relay Agent Info        DHCP relay information   │     │    │
│  │  │ 119       Domain Search           DNS search list          │     │    │
│  │  │ 121       Classless Static Route  Static routes            │     │    │
│  │  │ 150       TFTP Server Address     Cisco TFTP server        │     │    │
│  │  │ 252       WPAD                    Web proxy auto-discovery │     │    │
│  │  └────────────────────────────────────────────────────────────┘     │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  Option 82 (Relay Agent Information):                                        │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  Used by DHCP relay agents to add information about the client      │    │
│  │                                                                      │    │
│  │  Sub-options:                                                        │    │
│  │  ┌────────────────────────────────────────────────────────────┐     │    │
│  │  │ Sub-option    Name                Description              │     │    │
│  │  │ ──────────    ────                ───────────              │     │    │
│  │  │ 1             Circuit ID          Port/VLAN identifier     │     │    │
│  │  │ 2             Remote ID           Device identifier        │     │    │
│  │  │ 5             Link Selection      Subnet selection         │     │    │
│  │  │ 6             Subscriber ID       User identifier          │     │    │
│  │  │ 9             Vendor Specific     Vendor-defined           │     │    │
│  │  │ 11            Server ID Override  Force server selection   │     │    │
│  │  └────────────────────────────────────────────────────────────┘     │    │
│  │                                                                      │    │
│  │  Example Circuit ID format:                                          │    │
│  │  - VLAN ID + Port number                                             │    │
│  │  - AP MAC + SSID                                                     │    │
│  │  - Location information                                              │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  DHCP Fingerprinting:                                                        │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  Option 55 (Parameter Request List) can identify device type        │    │
│  │                                                                      │    │
│  │  ┌────────────────────────────────────────────────────────────┐     │    │
│  │  │ Device              Option 55 Signature                    │     │    │
│  │  │ ──────              ───────────────────                    │     │    │
│  │  │ Windows 10          1,3,6,15,31,33,43,44,46,47,119,121,249 │     │    │
│  │  │ macOS               1,121,3,6,15,119,252,95,44,46          │     │    │
│  │  │ iOS                 1,121,3,6,15,119,252                   │     │    │
│  │  │ Android             1,3,6,15,26,28,51,58,59,43             │     │    │
│  │  │ Linux               1,28,2,3,15,6,119,12,44,47,26,121      │     │    │
│  │  └────────────────────────────────────────────────────────────┘     │    │
│  │                                                                      │    │
│  │  Option 60 (Vendor Class ID) examples:                               │    │
│  │  - "MSFT 5.0" = Windows                                              │    │
│  │  - "android-dhcp-10" = Android 10                                    │    │
│  │  - "dhcpcd-6.11.5" = Linux dhcpcd                                    │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### CW.3 DHCP Relay

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    DHCP RELAY                                                │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  DHCP Relay Operation:                                                       │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  Client          AP/Relay          DHCP Server                       │    │
│  │    │                │                    │                           │    │
│  │    │ ── DISCOVER ──>│                    │                           │    │
│  │    │   (broadcast)  │                    │                           │    │
│  │    │                │                    │                           │    │
│  │    │                │ ── DISCOVER ──────>│                           │    │
│  │    │                │   (unicast)        │                           │    │
│  │    │                │   giaddr=10.0.0.1  │                           │    │
│  │    │                │   Option 82 added  │                           │    │
│  │    │                │                    │                           │    │
│  │    │                │ <── OFFER ─────────│                           │    │
│  │    │                │   (unicast)        │                           │    │
│  │    │                │                    │                           │    │
│  │    │ <── OFFER ─────│                    │                           │    │
│  │    │   (broadcast)  │                    │                           │    │
│  │    │                │                    │                           │    │
│  │    │ ── REQUEST ───>│                    │                           │    │
│  │    │                │ ── REQUEST ───────>│                           │    │
│  │    │                │ <── ACK ───────────│                           │    │
│  │    │ <── ACK ───────│                    │                           │    │
│  │    │                │                    │                           │    │
│  │                                                                      │    │
│  │  giaddr (Gateway IP Address):                                        │    │
│  │  - Set by relay agent to its own IP                                  │    │
│  │  - Server uses this to determine client's subnet                     │    │
│  │  - Server sends response to this address                             │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  AP as DHCP Relay:                                                           │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  Configuration:                                                      │    │
│  │  # Enable DHCP relay on AP                                           │    │
│  │  dhcp-relay enable                                                   │    │
│  │  dhcp-relay server 10.1.1.100                                        │    │
│  │  dhcp-relay server 10.1.1.101                                        │    │
│  │  dhcp-relay option-82 enable                                         │    │
│  │  dhcp-relay option-82 circuit-id format ap-mac-ssid                  │    │
│  │  dhcp-relay option-82 remote-id format ap-name                       │    │
│  │                                                                      │    │
│  │  Benefits:                                                           │    │
│  │  - Centralized DHCP server                                           │    │
│  │  - Per-SSID IP pools                                                 │    │
│  │  - Client tracking via Option 82                                     │    │
│  │  - Policy enforcement based on location                              │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Appendix CX: DNS and Service Discovery

### CX.1 DNS Resolution

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    DNS RESOLUTION                                            │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  DNS Query Flow:                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  Client          Local DNS         Root DNS        TLD DNS    Auth DNS│   │
│  │    │                │                  │              │           │   │   │
│  │    │ ── Query ─────>│                  │              │           │   │   │
│  │    │  www.example.com                  │              │           │   │   │
│  │    │                │                  │              │           │   │   │
│  │    │                │ ── Query ───────>│              │           │   │   │
│  │    │                │  (if not cached) │              │           │   │   │
│  │    │                │                  │              │           │   │   │
│  │    │                │ <── Referral ────│              │           │   │   │
│  │    │                │  (.com NS)       │              │           │   │   │
│  │    │                │                  │              │           │   │   │
│  │    │                │ ── Query ────────────────────>│            │   │   │
│  │    │                │                  │              │           │   │   │
│  │    │                │ <── Referral ───────────────────│           │   │   │
│  │    │                │  (example.com NS)│              │           │   │   │
│  │    │                │                  │              │           │   │   │
│  │    │                │ ── Query ───────────────────────────────>│  │   │   │
│  │    │                │                  │              │           │   │   │
│  │    │                │ <── Answer ─────────────────────────────────│   │   │
│  │    │                │  (93.184.216.34) │              │           │   │   │
│  │    │                │                  │              │           │   │   │
│  │    │ <── Answer ────│                  │              │           │   │   │
│  │    │  93.184.216.34 │                  │              │           │   │   │
│  │    │                │                  │              │           │   │   │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  DNS Record Types:                                                           │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  ┌────────────────────────────────────────────────────────────┐     │    │
│  │  │ Type    Name                Description                    │     │    │
│  │  │ ────    ────                ───────────                    │     │    │
│  │  │ A       Address             IPv4 address                   │     │    │
│  │  │ AAAA    IPv6 Address        IPv6 address                   │     │    │
│  │  │ CNAME   Canonical Name      Alias to another name          │     │    │
│  │  │ MX      Mail Exchange       Mail server                    │     │    │
│  │  │ NS      Name Server         Authoritative DNS server       │     │    │
│  │  │ PTR     Pointer             Reverse DNS lookup             │     │    │
│  │  │ SOA     Start of Authority  Zone information               │     │    │
│  │  │ SRV     Service             Service location               │     │    │
│  │  │ TXT     Text                Arbitrary text data            │     │    │
│  │  │ CAA     Cert Authority      Allowed certificate issuers    │     │    │
│  │  └────────────────────────────────────────────────────────────┘     │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  DNS over HTTPS (DoH) / DNS over TLS (DoT):                                  │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  ┌────────────────────────────────────────────────────────────┐     │    │
│  │  │ Protocol    Port    Encryption    Privacy                  │     │    │
│  │  │ ────────    ────    ──────────    ───────                  │     │    │
│  │  │ DNS         53      None          Queries visible          │     │    │
│  │  │ DoT         853     TLS           Encrypted queries        │     │    │
│  │  │ DoH         443     HTTPS         Encrypted, looks like web│     │    │
│  │  └────────────────────────────────────────────────────────────┘     │    │
│  │                                                                      │    │
│  │  Enterprise considerations:                                          │    │
│  │  - DoH/DoT may bypass corporate DNS policies                         │    │
│  │  - May need to block or redirect encrypted DNS                       │    │
│  │  - Consider deploying internal DoH/DoT servers                       │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### CX.2 mDNS (Multicast DNS)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    mDNS (MULTICAST DNS)                                      │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  mDNS Overview:                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  - Zero-configuration DNS for local networks                         │    │
│  │  - Uses .local domain suffix                                         │    │
│  │  - Multicast address: 224.0.0.251 (IPv4), ff02::fb (IPv6)            │    │
│  │  - Port: 5353 (UDP)                                                  │    │
│  │  - Also known as Bonjour (Apple), Avahi (Linux)                      │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  mDNS Query:                                                                 │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  Client                              All Devices                     │    │
│  │    │                                      │                          │    │
│  │    │ ── mDNS Query (multicast) ──────────>│                          │    │
│  │    │    "printer.local"                   │                          │    │
│  │    │                                      │                          │    │
│  │    │ <── mDNS Response (multicast) ───────│ (from printer)           │    │
│  │    │    "printer.local = 192.168.1.50"    │                          │    │
│  │    │                                      │                          │    │
│  │                                                                      │    │
│  │  Features:                                                           │    │
│  │  - No DNS server required                                            │    │
│  │  - Devices announce their own names                                  │    │
│  │  - Conflict resolution built-in                                      │    │
│  │  - TTL typically 120 seconds                                         │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  mDNS Gateway (Bonjour Gateway):                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  Problem: mDNS is link-local, doesn't cross VLANs                    │    │
│  │                                                                      │    │
│  │  ┌─────────────────────────────────────────────────────────────┐    │    │
│  │  │                                                              │    │    │
│  │  │  VLAN 10                    VLAN 20                          │    │    │
│  │  │  ┌─────────┐               ┌─────────┐                       │    │    │
│  │  │  │ Client  │               │ Printer │                       │    │    │
│  │  │  └────┬────┘               └────┬────┘                       │    │    │
│  │  │       │                         │                            │    │    │
│  │  │       │    ┌─────────────────┐  │                            │    │    │
│  │  │       └────│  mDNS Gateway   │──┘                            │    │    │
│  │  │            │  (on AP/Switch) │                               │    │    │
│  │  │            └─────────────────┘                               │    │    │
│  │  │                                                              │    │    │
│  │  │  Gateway forwards mDNS between VLANs                         │    │    │
│  │  │                                                              │    │    │
│  │  └─────────────────────────────────────────────────────────────┘    │    │
│  │                                                                      │    │
│  │  Configuration:                                                      │    │
│  │  # Enable mDNS gateway                                               │    │
│  │  mdns-gateway enable                                                 │    │
│  │  mdns-gateway vlan 10,20,30                                          │    │
│  │  mdns-gateway service-filter _ipp._tcp                               │    │
│  │  mdns-gateway service-filter _airplay._tcp                           │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### CX.3 DNS-SD (DNS Service Discovery)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    DNS-SD (DNS SERVICE DISCOVERY)                            │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  DNS-SD Overview:                                                            │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  - Uses DNS (or mDNS) to discover services                           │    │
│  │  - RFC 6763                                                          │    │
│  │  - Service types: _service._protocol.domain                          │    │
│  │  - Examples: _http._tcp.local, _ipp._tcp.local                       │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  Service Discovery Flow:                                                     │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  1. Browse for service type (PTR query)                              │    │
│  │     Query: _ipp._tcp.local                                           │    │
│  │     Response: "HP Printer._ipp._tcp.local"                           │    │
│  │                                                                      │    │
│  │  2. Get service details (SRV query)                                  │    │
│  │     Query: HP Printer._ipp._tcp.local SRV                            │    │
│  │     Response: 0 0 631 printer.local                                  │    │
│  │               (priority, weight, port, target)                       │    │
│  │                                                                      │    │
│  │  3. Get additional info (TXT query)                                  │    │
│  │     Query: HP Printer._ipp._tcp.local TXT                            │    │
│  │     Response: "ty=HP LaserJet" "pdl=application/pdf"                 │    │
│  │                                                                      │    │
│  │  4. Resolve hostname (A/AAAA query)                                  │    │
│  │     Query: printer.local A                                           │    │
│  │     Response: 192.168.1.50                                           │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  Common Service Types:                                                       │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  ┌────────────────────────────────────────────────────────────┐     │    │
│  │  │ Service Type          Description                          │     │    │
│  │  │ ────────────          ───────────                          │     │    │
│  │  │ _http._tcp            Web server                           │     │    │
│  │  │ _https._tcp           Secure web server                    │     │    │
│  │  │ _ipp._tcp             Internet Printing Protocol           │     │    │
│  │  │ _printer._tcp         LPR/LPD printing                     │     │    │
│  │  │ _airplay._tcp         Apple AirPlay                        │     │    │
│  │  │ _raop._tcp            Remote Audio Output Protocol         │     │    │
│  │  │ _googlecast._tcp      Google Chromecast                    │     │    │
│  │  │ _spotify-connect._tcp Spotify Connect                      │     │    │
│  │  │ _smb._tcp             Windows file sharing                 │     │    │
│  │  │ _afpovertcp._tcp      Apple file sharing                   │     │    │
│  │  │ _ssh._tcp             SSH server                           │     │    │
│  │  │ _sftp-ssh._tcp        SFTP over SSH                        │     │    │
│  │  │ _homekit._tcp         Apple HomeKit                        │     │    │
│  │  │ _hap._tcp             HomeKit Accessory Protocol           │     │    │
│  │  └────────────────────────────────────────────────────────────┘     │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Appendix CY: Network Segmentation

### CY.1 VLAN Assignment

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    VLAN ASSIGNMENT                                           │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  VLAN Assignment Methods:                                                    │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  ┌────────────────────────────────────────────────────────────┐     │    │
│  │  │ Method              Description                 Priority   │     │    │
│  │  │ ──────              ───────────                 ────────   │     │    │
│  │  │ RADIUS              Server assigns VLAN         Highest    │     │    │
│  │  │ MAC-based           Based on client MAC         High       │     │    │
│  │  │ User Role           Based on user group         Medium     │     │    │
│  │  │ SSID                Per-SSID default VLAN       Low        │     │    │
│  │  │ Default             Fallback VLAN               Lowest     │     │    │
│  │  └────────────────────────────────────────────────────────────┘     │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  RADIUS VLAN Assignment:                                                     │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  RADIUS Attributes for VLAN:                                         │    │
│  │  - Tunnel-Type (64) = VLAN (13)                                      │    │
│  │  - Tunnel-Medium-Type (65) = IEEE-802 (6)                            │    │
│  │  - Tunnel-Private-Group-ID (81) = VLAN ID or name                    │    │
│  │                                                                      │    │
│  │  Example FreeRADIUS configuration:                                   │    │
│  │  # users file                                                        │    │
│  │  employee1  Cleartext-Password := "password"                         │    │
│  │      Tunnel-Type = VLAN,                                             │    │
│  │      Tunnel-Medium-Type = IEEE-802,                                  │    │
│  │      Tunnel-Private-Group-ID = 100                                   │    │
│  │                                                                      │    │
│  │  guest1  Cleartext-Password := "guestpass"                           │    │
│  │      Tunnel-Type = VLAN,                                             │    │
│  │      Tunnel-Medium-Type = IEEE-802,                                  │    │
│  │      Tunnel-Private-Group-ID = 200                                   │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  Dynamic VLAN Flow:                                                          │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  Client          AP              RADIUS                              │    │
│  │    │              │                 │                                │    │
│  │    │ ── 802.1X ──>│                 │                                │    │
│  │    │              │                 │                                │    │
│  │    │              │ ── Access-Req ─>│                                │    │
│  │    │              │                 │                                │    │
│  │    │              │ <── Access-Acc ─│                                │    │
│  │    │              │    VLAN=100     │                                │    │
│  │    │              │                 │                                │    │
│  │    │ <── 4-Way ───│                 │                                │    │
│  │    │              │                 │                                │    │
│  │    │ ══ Traffic on VLAN 100 ════════│                                │    │
│  │    │              │                 │                                │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  VLAN Pooling:                                                               │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  Purpose: Distribute clients across multiple VLANs                   │    │
│  │                                                                      │    │
│  │  ┌─────────────────────────────────────────────────────────────┐    │    │
│  │  │                                                              │    │    │
│  │  │  SSID: Guest                                                 │    │    │
│  │  │  VLAN Pool: 200, 201, 202, 203                               │    │    │
│  │  │                                                              │    │    │
│  │  │  Client 1 ──> VLAN 200                                       │    │    │
│  │  │  Client 2 ──> VLAN 201                                       │    │    │
│  │  │  Client 3 ──> VLAN 202                                       │    │    │
│  │  │  Client 4 ──> VLAN 203                                       │    │    │
│  │  │  Client 5 ──> VLAN 200 (round-robin)                         │    │    │
│  │  │                                                              │    │    │
│  │  └─────────────────────────────────────────────────────────────┘    │    │
│  │                                                                      │    │
│  │  Benefits:                                                           │    │
│  │  - Larger broadcast domains split                                    │    │
│  │  - Better scalability                                                │    │
│  │  - Client isolation                                                  │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Document Revision History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2026-01-08 | Auto-generated | Initial document creation |
| 1.1 | 2026-01-08 | Auto-generated | Added packet capture analysis, regulatory domains, client compatibility |
| 1.2 | 2026-01-08 | Auto-generated | Added EAP methods, band steering, load balancing, mesh networking, power save |
| 1.3 | 2026-01-08 | Auto-generated | Added RADIUS attributes, debug commands, troubleshooting flowchart, quick reference |
| 1.4 | 2026-01-08 | Auto-generated | Added WiFi 7 features, Hotspot 2.0 deep dive, glossary, standards reference |
| 1.5 | 2026-01-08 | Auto-generated | Added security attacks, performance optimization, complete hostapd config |
| 1.6 | 2026-01-08 | Auto-generated | Added frame formats, information elements, status/reason codes |
| 1.7 | 2026-01-08 | Auto-generated | Added vendor extensions, debugging/logging, packet capture commands |
| 1.8 | 2026-01-08 | Auto-generated | Added test case reference, regulatory domain deep dive |
| 1.9 | 2026-01-08 | Auto-generated | Added action frame reference, error scenarios and troubleshooting |
| 2.0 | 2026-01-08 | Auto-generated | Added Wireshark filter reference, complete configuration examples |
| 2.1 | 2026-01-08 | Auto-generated | Added performance benchmarks, client device compatibility matrix |
| 2.2 | 2026-01-08 | Auto-generated | Added WiFi Alliance certification, security checklist, capacity planning |
| 2.3 | 2026-01-08 | Auto-generated | Added antenna/RF considerations, troubleshooting trees, timing diagrams |
| 2.4 | 2026-01-08 | Auto-generated | Added QoS/WMM, deployment topologies, compliance, advanced debugging |
| 2.5 | 2026-01-08 | Auto-generated | Added supplicant config, VLAN, rate limiting, HA, IoT profiling |
| 2.6 | 2026-01-08 | Auto-generated | Added captive portal, location services, spectrum analysis, migration, API |
| 2.7 | 2026-01-08 | Auto-generated | Added multicast, VoWiFi, enterprise integration, monitoring, disaster recovery |
| 2.8 | 2026-01-08 | Auto-generated | Added WIDS, cloud management, performance testing, compliance, checklists |
| 2.9 | 2026-01-08 | Auto-generated | Added outdoor WiFi, stadium/venue, healthcare, education, retail, industrial |
| 3.0 | 2026-01-08 | Auto-generated | Added WiFi 6E/7 deep dive, OFDMA, MU-MIMO, BSS coloring, TWT |
| 3.1 | 2026-01-08 | Auto-generated | Added WiFi 7 MLO, puncturing, 4K-QAM, multi-RU, enhanced security |
| 3.2 | 2026-01-08 | Auto-generated | Added FILS, DPP, enterprise security, certificate management |
| 3.3 | 2026-01-08 | Auto-generated | Added power management, airtime fairness, channel utilization |
| 3.4 | 2026-01-08 | Auto-generated | Added client steering, band selection, load balancing algorithms |
| 3.5 | 2026-01-08 | Auto-generated | Added mesh networking, WDS, repeater modes, backhaul optimization |
| 3.6 | 2026-01-08 | Auto-generated | Added roaming protocols, 802.11k/v/r deep dive, seamless handoff |
| 3.7 | 2026-01-08 | Auto-generated | Added DHCP deep dive, DNS, mDNS, service discovery |
| 3.8 | 2026-01-08 | Auto-generated | Added firewall policies, ACLs, traffic filtering, NAT |

---

## Appendix CZ: Firewall and Access Control

### CZ.1 Wireless Firewall Policies

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    WIRELESS FIREWALL POLICIES                                │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  Firewall Policy Hierarchy:                                                  │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  ┌─────────────────────────────────────────────────────────────┐    │    │
│  │  │                                                              │    │    │
│  │  │  1. User Role Policy (highest priority)                      │    │    │
│  │  │     │                                                        │    │    │
│  │  │     ▼                                                        │    │    │
│  │  │  2. SSID Policy                                              │    │    │
│  │  │     │                                                        │    │    │
│  │  │     ▼                                                        │    │    │
│  │  │  3. VLAN Policy                                              │    │    │
│  │  │     │                                                        │    │    │
│  │  │     ▼                                                        │    │    │
│  │  │  4. Global Policy (lowest priority)                          │    │    │
│  │  │                                                              │    │    │
│  │  └─────────────────────────────────────────────────────────────┘    │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  Policy Actions:                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  ┌────────────────────────────────────────────────────────────┐     │    │
│  │  │ Action          Description                                │     │    │
│  │  │ ──────          ───────────                                │     │    │
│  │  │ PERMIT          Allow traffic                              │     │    │
│  │  │ DENY            Block traffic                              │     │    │
│  │  │ REDIRECT        Redirect to captive portal                 │     │    │
│  │  │ RATE-LIMIT      Apply bandwidth limit                      │     │    │
│  │  │ QOS-MARK        Set DSCP/802.1p priority                   │     │    │
│  │  │ LOG             Log matching traffic                       │     │    │
│  │  │ MIRROR          Copy traffic for analysis                  │     │    │
│  │  └────────────────────────────────────────────────────────────┘     │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  Match Criteria:                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  ┌────────────────────────────────────────────────────────────┐     │    │
│  │  │ Criterion           Examples                               │     │    │
│  │  │ ─────────           ────────                               │     │    │
│  │  │ Source IP           192.168.1.0/24, any                    │     │    │
│  │  │ Destination IP      10.0.0.0/8, host 8.8.8.8               │     │    │
│  │  │ Protocol            TCP, UDP, ICMP, any                    │     │    │
│  │  │ Source Port         1024-65535, any                        │     │    │
│  │  │ Destination Port    80, 443, 22, range 1-1024              │     │    │
│  │  │ Application         http, https, ssh, dns                  │     │    │
│  │  │ User                user@domain, group:employees           │     │    │
│  │  │ Device Type         windows, ios, android                  │     │    │
│  │  │ Time                weekdays 9am-5pm                       │     │    │
│  │  │ Location            building-a, floor-2                    │     │    │
│  │  └────────────────────────────────────────────────────────────┘     │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  Example Firewall Rules:                                                     │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  # Guest SSID policy                                                 │    │
│  │  firewall-policy guest-policy                                        │    │
│  │    # Allow DNS                                                       │    │
│  │    rule 10 permit udp any any eq 53                                  │    │
│  │    # Allow DHCP                                                      │    │
│  │    rule 20 permit udp any eq 68 any eq 67                            │    │
│  │    # Allow HTTP/HTTPS                                                │    │
│  │    rule 30 permit tcp any any eq 80                                  │    │
│  │    rule 40 permit tcp any any eq 443                                 │    │
│  │    # Block internal networks                                         │    │
│  │    rule 50 deny ip any 10.0.0.0/8                                    │    │
│  │    rule 60 deny ip any 172.16.0.0/12                                 │    │
│  │    rule 70 deny ip any 192.168.0.0/16                                │    │
│  │    # Allow all other internet                                        │    │
│  │    rule 100 permit ip any any                                        │    │
│  │                                                                      │    │
│  │  # Apply to SSID                                                     │    │
│  │  ssid Guest                                                          │    │
│  │    firewall-policy guest-policy                                      │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### CZ.2 Client Isolation

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    CLIENT ISOLATION                                          │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  Isolation Levels:                                                           │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  ┌────────────────────────────────────────────────────────────┐     │    │
│  │  │ Level               Description                            │     │    │
│  │  │ ─────               ───────────                            │     │    │
│  │  │ None                Clients can communicate freely         │     │    │
│  │  │ Layer 2             Block L2 between clients (same AP)     │     │    │
│  │  │ Layer 3             Block L3 between clients (same subnet) │     │    │
│  │  │ Full                Block all client-to-client traffic     │     │    │
│  │  └────────────────────────────────────────────────────────────┘     │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  Layer 2 Isolation:                                                          │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  Without Isolation:                                                  │    │
│  │  ┌─────────────────────────────────────────────────────────────┐    │    │
│  │  │                                                              │    │    │
│  │  │  Client A ◄──────────────────────────────────────► Client B  │    │    │
│  │  │      │                    AP                           │     │    │    │
│  │  │      └────────────────────┴────────────────────────────┘     │    │    │
│  │  │                                                              │    │    │
│  │  │  Direct L2 communication allowed                             │    │    │
│  │  │                                                              │    │    │
│  │  └─────────────────────────────────────────────────────────────┘    │    │
│  │                                                                      │    │
│  │  With Isolation:                                                     │    │
│  │  ┌─────────────────────────────────────────────────────────────┐    │    │
│  │  │                                                              │    │    │
│  │  │  Client A ────────► AP ────────► Gateway ────────► Client B  │    │    │
│  │  │                      │              │                        │    │    │
│  │  │                      │              │                        │    │    │
│  │  │                      └──────────────┘                        │    │    │
│  │  │                      (traffic forced                         │    │    │
│  │  │                       through gateway)                       │    │    │
│  │  │                                                              │    │    │
│  │  └─────────────────────────────────────────────────────────────┘    │    │
│  │                                                                      │    │
│  │  Configuration:                                                      │    │
│  │  # Enable client isolation                                           │    │
│  │  ssid Guest                                                          │    │
│  │    client-isolation enable                                           │    │
│  │    client-isolation mode layer2                                      │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  Proxy ARP:                                                                  │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  Purpose: AP responds to ARP requests on behalf of clients          │    │
│  │                                                                      │    │
│  │  Without Proxy ARP:                                                  │    │
│  │  Client A ── ARP Request (broadcast) ──> All Clients                 │    │
│  │  Client B ── ARP Reply ──> Client A                                  │    │
│  │                                                                      │    │
│  │  With Proxy ARP:                                                     │    │
│  │  Client A ── ARP Request ──> AP                                      │    │
│  │  AP ── ARP Reply (on behalf of B) ──> Client A                       │    │
│  │                                                                      │    │
│  │  Benefits:                                                           │    │
│  │  - Reduces broadcast traffic                                         │    │
│  │  - Works with client isolation                                       │    │
│  │  - Improves airtime efficiency                                       │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### CZ.3 NAT and Port Forwarding

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    NAT AND PORT FORWARDING                                   │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  NAT Types:                                                                  │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  ┌────────────────────────────────────────────────────────────┐     │    │
│  │  │ Type            Description                                │     │    │
│  │  │ ────            ───────────                                │     │    │
│  │  │ SNAT            Source NAT - change source IP              │     │    │
│  │  │ DNAT            Destination NAT - change dest IP           │     │    │
│  │  │ PAT             Port Address Translation - many-to-one     │     │    │
│  │  │ 1:1 NAT         One-to-one IP mapping                      │     │    │
│  │  │ Hairpin NAT     Internal to internal via external IP       │     │    │
│  │  └────────────────────────────────────────────────────────────┘     │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  NAT on AP (Local Breakout):                                                 │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  ┌─────────────────────────────────────────────────────────────┐    │    │
│  │  │                                                              │    │    │
│  │  │  Client                AP                    Internet        │    │    │
│  │  │  192.168.1.100         │                         │           │    │    │
│  │  │       │                │                         │           │    │    │
│  │  │       │ ── Packet ────>│                         │           │    │    │
│  │  │       │  src: 192.168.1.100                      │           │    │    │
│  │  │       │  dst: 8.8.8.8  │                         │           │    │    │
│  │  │       │                │                         │           │    │    │
│  │  │       │                │ ── NAT'd Packet ───────>│           │    │    │
│  │  │       │                │  src: 10.0.0.1 (AP WAN) │           │    │    │
│  │  │       │                │  dst: 8.8.8.8           │           │    │    │
│  │  │       │                │                         │           │    │    │
│  │  │       │                │ <── Response ───────────│           │    │    │
│  │  │       │                │  src: 8.8.8.8           │           │    │    │
│  │  │       │                │  dst: 10.0.0.1          │           │    │    │
│  │  │       │                │                         │           │    │    │
│  │  │       │ <── De-NAT ────│                         │           │    │    │
│  │  │       │  src: 8.8.8.8  │                         │           │    │    │
│  │  │       │  dst: 192.168.1.100                      │           │    │    │
│  │  │                                                              │    │    │
│  │  └─────────────────────────────────────────────────────────────┘    │    │
│  │                                                                      │    │
│  │  Configuration:                                                      │    │
│  │  # Enable NAT on guest SSID                                          │    │
│  │  ssid Guest                                                          │    │
│  │    nat enable                                                        │    │
│  │    nat interface wan                                                 │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  NAT Session Table:                                                          │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  ┌────────────────────────────────────────────────────────────┐     │    │
│  │  │ Internal IP:Port    External IP:Port    Dest IP:Port       │     │    │
│  │  │ ─────────────────   ────────────────    ─────────────      │     │    │
│  │  │ 192.168.1.100:45678 10.0.0.1:10001      8.8.8.8:53         │     │    │
│  │  │ 192.168.1.101:52341 10.0.0.1:10002      93.184.216.34:443  │     │    │
│  │  │ 192.168.1.102:38291 10.0.0.1:10003      142.250.80.46:443  │     │    │
│  │  └────────────────────────────────────────────────────────────┘     │    │
│  │                                                                      │    │
│  │  Session limits:                                                     │    │
│  │  - Per-client: 1000 sessions                                         │    │
│  │  - Total: 65535 sessions                                             │    │
│  │  - Timeout: TCP 3600s, UDP 300s                                      │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Appendix DA: Rate Limiting and Traffic Shaping

### DA.1 Bandwidth Control

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    BANDWIDTH CONTROL                                         │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  Rate Limiting Levels:                                                       │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  ┌────────────────────────────────────────────────────────────┐     │    │
│  │  │ Level           Description                                │     │    │
│  │  │ ─────           ───────────                                │     │    │
│  │  │ Per-Client      Limit each client individually             │     │    │
│  │  │ Per-SSID        Aggregate limit for all clients on SSID    │     │    │
│  │  │ Per-AP          Total bandwidth for AP                     │     │    │
│  │  │ Per-User        Limit based on authenticated user          │     │    │
│  │  │ Per-Role        Limit based on user role                   │     │    │
│  │  │ Per-Application Limit specific applications                │     │    │
│  │  └────────────────────────────────────────────────────────────┘     │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  Token Bucket Algorithm:                                                     │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  ┌─────────────────────────────────────────────────────────────┐    │    │
│  │  │                                                              │    │    │
│  │  │  Tokens added at rate R                                      │    │    │
│  │  │         │                                                    │    │    │
│  │  │         ▼                                                    │    │    │
│  │  │  ┌─────────────┐                                             │    │    │
│  │  │  │             │ ← Bucket size B (burst)                     │    │    │
│  │  │  │  ○ ○ ○ ○ ○  │                                             │    │    │
│  │  │  │  ○ ○ ○ ○ ○  │                                             │    │    │
│  │  │  │  ○ ○ ○ ○ ○  │                                             │    │    │
│  │  │  └──────┬──────┘                                             │    │    │
│  │  │         │                                                    │    │    │
│  │  │         ▼                                                    │    │    │
│  │  │  Packet consumes tokens                                      │    │    │
│  │  │  (1 token per byte)                                          │    │    │
│  │  │                                                              │    │    │
│  │  │  If tokens available: packet sent                            │    │    │
│  │  │  If no tokens: packet queued or dropped                      │    │    │
│  │  │                                                              │    │    │
│  │  └─────────────────────────────────────────────────────────────┘    │    │
│  │                                                                      │    │
│  │  Parameters:                                                         │    │
│  │  - Rate (R): Sustained bandwidth (e.g., 10 Mbps)                     │    │
│  │  - Burst (B): Maximum burst size (e.g., 1 MB)                        │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  Configuration Examples:                                                     │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  # Per-client rate limit                                             │    │
│  │  ssid Guest                                                          │    │
│  │    rate-limit client downstream 10mbps                               │    │
│  │    rate-limit client upstream 5mbps                                  │    │
│  │    rate-limit client burst 1mb                                       │    │
│  │                                                                      │    │
│  │  # Per-SSID aggregate limit                                          │    │
│  │  ssid Guest                                                          │    │
│  │    rate-limit ssid downstream 100mbps                                │    │
│  │    rate-limit ssid upstream 50mbps                                   │    │
│  │                                                                      │    │
│  │  # RADIUS-assigned rate limit                                        │    │
│  │  # Access-Accept attributes:                                         │    │
│  │  # Arista-Bandwidth-Max-Down = 20000000  (20 Mbps)                   │    │
│  │  # Arista-Bandwidth-Max-Up = 10000000    (10 Mbps)                   │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### DA.2 Traffic Shaping

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    TRAFFIC SHAPING                                           │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  Shaping vs Policing:                                                        │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  ┌────────────────────────────────────────────────────────────┐     │    │
│  │  │ Feature         Policing            Shaping                │     │    │
│  │  │ ───────         ────────            ───────                │     │    │
│  │  │ Excess traffic  Dropped             Queued/delayed         │     │    │
│  │  │ Latency         Low                 Higher (buffering)     │     │    │
│  │  │ Burst handling  Limited             Better                 │     │    │
│  │  │ CPU usage       Lower               Higher                 │     │    │
│  │  │ Use case        Ingress traffic     Egress traffic         │     │    │
│  │  └────────────────────────────────────────────────────────────┘     │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  Hierarchical Token Bucket (HTB):                                            │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  ┌─────────────────────────────────────────────────────────────┐    │    │
│  │  │                                                              │    │    │
│  │  │                    Root (100 Mbps)                           │    │    │
│  │  │                         │                                    │    │    │
│  │  │         ┌───────────────┼───────────────┐                    │    │    │
│  │  │         │               │               │                    │    │    │
│  │  │    Corporate       Guest           IoT                       │    │    │
│  │  │    (60 Mbps)      (30 Mbps)      (10 Mbps)                   │    │    │
│  │  │         │               │               │                    │    │    │
│  │  │    ┌────┴────┐     ┌────┴────┐     ┌────┴────┐               │    │    │
│  │  │    │         │     │         │     │         │               │    │    │
│  │  │  Voice    Data   Web      Video  Sensors  Cameras            │    │    │
│  │  │  (20M)   (40M)  (20M)    (10M)   (5M)     (5M)               │    │    │
│  │  │                                                              │    │    │
│  │  │  - Guaranteed rate (rate)                                    │    │    │
│  │  │  - Maximum rate (ceil)                                       │    │    │
│  │  │  - Borrowing from parent                                     │    │    │
│  │  │                                                              │    │    │
│  │  └─────────────────────────────────────────────────────────────┘    │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  Queue Disciplines:                                                          │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  ┌────────────────────────────────────────────────────────────┐     │    │
│  │  │ Qdisc           Description                                │     │    │
│  │  │ ─────           ───────────                                │     │    │
│  │  │ FIFO            First In First Out (default)               │     │    │
│  │  │ PRIO            Priority queuing                           │     │    │
│  │  │ SFQ             Stochastic Fair Queuing                    │     │    │
│  │  │ FQ_CODEL        Fair Queue Controlled Delay                │     │    │
│  │  │ HTB             Hierarchical Token Bucket                  │     │    │
│  │  │ CAKE            Common Applications Kept Enhanced          │     │    │
│  │  └────────────────────────────────────────────────────────────┘     │    │
│  │                                                                      │    │
│  │  FQ_CODEL (recommended for WiFi):                                    │    │
│  │  - Reduces bufferbloat                                               │    │
│  │  - Fair queuing per flow                                             │    │
│  │  - Active queue management                                           │    │
│  │  - Low latency for interactive traffic                               │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Appendix DB: High Availability

### DB.1 AP Redundancy

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    AP REDUNDANCY                                             │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  Redundancy Strategies:                                                      │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  ┌────────────────────────────────────────────────────────────┐     │    │
│  │  │ Strategy            Description                            │     │    │
│  │  │ ────────            ───────────                            │     │    │
│  │  │ Overlapping         Multiple APs cover same area           │     │    │
│  │  │ N+1                 Spare AP for every N active APs        │     │    │
│  │  │ Active-Standby      Backup AP takes over on failure        │     │    │
│  │  │ Load Sharing        All APs active, redistribute on fail   │     │    │
│  │  └────────────────────────────────────────────────────────────┘     │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  Overlapping Coverage:                                                       │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  ┌─────────────────────────────────────────────────────────────┐    │    │
│  │  │                                                              │    │    │
│  │  │      ┌───────────────┐     ┌───────────────┐                 │    │    │
│  │  │     /                 \   /                 \                │    │    │
│  │  │    /                   \ /                   \               │    │    │
│  │  │   │        AP1         │         AP2         │               │    │    │
│  │  │   │                    │                     │               │    │    │
│  │  │    \                   / \                   /               │    │    │
│  │  │     \                 /   \                 /                │    │    │
│  │  │      └───────────────┘     └───────────────┘                 │    │    │
│  │  │                                                              │    │    │
│  │  │              ▲                                               │    │    │
│  │  │              │                                               │    │    │
│  │  │         Overlap zone                                         │    │    │
│  │  │         (20-30% recommended)                                 │    │    │
│  │  │                                                              │    │    │
│  │  │  If AP1 fails:                                               │    │    │
│  │  │  - Clients in overlap zone roam to AP2                       │    │    │
│  │  │  - AP2 may increase power to extend coverage                 │    │    │
│  │  │                                                              │    │    │
│  │  └─────────────────────────────────────────────────────────────┘    │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  AP Failure Detection:                                                       │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  ┌────────────────────────────────────────────────────────────┐     │    │
│  │  │ Method              Detection Time    Description          │     │    │
│  │  │ ──────              ──────────────    ───────────          │     │    │
│  │  │ Heartbeat           1-5 seconds       Controller polling   │     │    │
│  │  │ RF Neighbor         10-30 seconds     Neighbor AP detects  │     │    │
│  │  │ Client Report       Variable          Clients report issue │     │    │
│  │  │ SNMP Trap           1-5 seconds       Network monitoring   │     │    │
│  │  │ Syslog              1-5 seconds       Log-based detection  │     │    │
│  │  └────────────────────────────────────────────────────────────┘     │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  Automatic Power Adjustment:                                                 │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  When neighbor AP fails:                                             │    │
│  │  1. Detect failure (RF neighbor missing)                             │    │
│  │  2. Calculate coverage gap                                           │    │
│  │  3. Increase TX power on adjacent APs                                │    │
│  │  4. Optionally change channel to reduce interference                 │    │
│  │                                                                      │    │
│  │  Configuration:                                                      │    │
│  │  # Enable automatic coverage hole recovery                           │    │
│  │  rf-management coverage-hole-recovery enable                         │    │
│  │  rf-management coverage-hole-recovery power-increase 6dB             │    │
│  │  rf-management coverage-hole-recovery detection-time 30              │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### DB.2 Controller Redundancy

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    CONTROLLER REDUNDANCY                                     │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  Controller HA Modes:                                                        │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  ┌────────────────────────────────────────────────────────────┐     │    │
│  │  │ Mode              Description                              │     │    │
│  │  │ ────              ───────────                              │     │    │
│  │  │ Active-Standby    One active, one standby                  │     │    │
│  │  │ Active-Active     Both active, load shared                 │     │    │
│  │  │ N+1               N active, 1 standby                      │     │    │
│  │  │ Cluster           Multiple controllers, distributed        │     │    │
│  │  └────────────────────────────────────────────────────────────┘     │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  Active-Standby:                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  ┌─────────────────────────────────────────────────────────────┐    │    │
│  │  │                                                              │    │    │
│  │  │  ┌─────────────┐         ┌─────────────┐                     │    │    │
│  │  │  │   Primary   │◄───────►│  Secondary  │                     │    │    │
│  │  │  │ Controller  │  Sync   │ Controller  │                     │    │    │
│  │  │  │  (Active)   │         │  (Standby)  │                     │    │    │
│  │  │  └──────┬──────┘         └──────┬──────┘                     │    │    │
│  │  │         │                       │                            │    │    │
│  │  │         │ Primary               │ (Ready to                  │    │    │
│  │  │         │ connection            │  take over)                │    │    │
│  │  │         │                       │                            │    │    │
│  │  │  ┌──────┴───────────────────────┴──────┐                     │    │    │
│  │  │  │                                      │                     │    │    │
│  │  │  │              APs                     │                     │    │    │
│  │  │  │                                      │                     │    │    │
│  │  │  └──────────────────────────────────────┘                     │    │    │
│  │  │                                                              │    │    │
│  │  │  Failover:                                                   │    │    │
│  │  │  1. Primary fails                                            │    │    │
│  │  │  2. Secondary detects (heartbeat timeout)                    │    │    │
│  │  │  3. Secondary becomes active                                 │    │    │
│  │  │  4. APs reconnect to secondary                               │    │    │
│  │  │  5. Failover time: 30-60 seconds                             │    │    │
│  │  │                                                              │    │    │
│  │  └─────────────────────────────────────────────────────────────┘    │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  AP Survivability:                                                           │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  When controller is unreachable:                                     │    │
│  │                                                                      │    │
│  │  ┌────────────────────────────────────────────────────────────┐     │    │
│  │  │ Feature             Behavior                               │     │    │
│  │  │ ───────             ────────                               │     │    │
│  │  │ Existing clients    Remain connected                       │     │    │
│  │  │ New clients         Can associate (cached config)          │     │    │
│  │  │ Authentication      Local cache or survivability mode      │     │    │
│  │  │ Roaming             Works between local APs                │     │    │
│  │  │ Configuration       Read-only (no changes)                 │     │    │
│  │  │ Statistics          Buffered locally                       │     │    │
│  │  └────────────────────────────────────────────────────────────┘     │    │
│  │                                                                      │    │
│  │  Configuration:                                                      │    │
│  │  # Enable AP survivability                                           │    │
│  │  ap-survivability enable                                             │    │
│  │  ap-survivability auth-cache-timeout 86400                           │    │
│  │  ap-survivability local-radius enable                                │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Document Revision History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2026-01-08 | Auto-generated | Initial document creation |
| 1.1 | 2026-01-08 | Auto-generated | Added packet capture analysis, regulatory domains, client compatibility |
| 1.2 | 2026-01-08 | Auto-generated | Added EAP methods, band steering, load balancing, mesh networking, power save |
| 1.3 | 2026-01-08 | Auto-generated | Added RADIUS attributes, debug commands, troubleshooting flowchart, quick reference |
| 1.4 | 2026-01-08 | Auto-generated | Added WiFi 7 features, Hotspot 2.0 deep dive, glossary, standards reference |
| 1.5 | 2026-01-08 | Auto-generated | Added security attacks, performance optimization, complete hostapd config |
| 1.6 | 2026-01-08 | Auto-generated | Added frame formats, information elements, status/reason codes |
| 1.7 | 2026-01-08 | Auto-generated | Added vendor extensions, debugging/logging, packet capture commands |
| 1.8 | 2026-01-08 | Auto-generated | Added test case reference, regulatory domain deep dive |
| 1.9 | 2026-01-08 | Auto-generated | Added action frame reference, error scenarios and troubleshooting |
| 2.0 | 2026-01-08 | Auto-generated | Added Wireshark filter reference, complete configuration examples |
| 2.1 | 2026-01-08 | Auto-generated | Added performance benchmarks, client device compatibility matrix |
| 2.2 | 2026-01-08 | Auto-generated | Added WiFi Alliance certification, security checklist, capacity planning |
| 2.3 | 2026-01-08 | Auto-generated | Added antenna/RF considerations, troubleshooting trees, timing diagrams |
| 2.4 | 2026-01-08 | Auto-generated | Added QoS/WMM, deployment topologies, compliance, advanced debugging |
| 2.5 | 2026-01-08 | Auto-generated | Added supplicant config, VLAN, rate limiting, HA, IoT profiling |
| 2.6 | 2026-01-08 | Auto-generated | Added captive portal, location services, spectrum analysis, migration, API |
| 2.7 | 2026-01-08 | Auto-generated | Added multicast, VoWiFi, enterprise integration, monitoring, disaster recovery |
| 2.8 | 2026-01-08 | Auto-generated | Added WIDS, cloud management, performance testing, compliance, checklists |
| 2.9 | 2026-01-08 | Auto-generated | Added outdoor WiFi, stadium/venue, healthcare, education, retail, industrial |
| 3.0 | 2026-01-08 | Auto-generated | Added WiFi 6E/7 deep dive, OFDMA, MU-MIMO, BSS coloring, TWT |
| 3.1 | 2026-01-08 | Auto-generated | Added WiFi 7 MLO, puncturing, 4K-QAM, multi-RU, enhanced security |
| 3.2 | 2026-01-08 | Auto-generated | Added FILS, DPP, enterprise security, certificate management |
| 3.3 | 2026-01-08 | Auto-generated | Added power management, airtime fairness, channel utilization |
| 3.4 | 2026-01-08 | Auto-generated | Added client steering, band selection, load balancing algorithms |
| 3.5 | 2026-01-08 | Auto-generated | Added mesh networking, WDS, repeater modes, backhaul optimization |
| 3.6 | 2026-01-08 | Auto-generated | Added roaming protocols, 802.11k/v/r deep dive, seamless handoff |
| 3.7 | 2026-01-08 | Auto-generated | Added DHCP deep dive, DNS, mDNS, service discovery |
| 3.8 | 2026-01-08 | Auto-generated | Added firewall policies, ACLs, traffic filtering, NAT |
| 3.9 | 2026-01-08 | Auto-generated | Added IoT device profiling, device fingerprinting, MAC randomization |

---

## Appendix DC: IoT Device Profiling

### DC.1 Device Fingerprinting

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    DEVICE FINGERPRINTING                                     │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  Fingerprinting Methods:                                                     │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  ┌────────────────────────────────────────────────────────────┐     │    │
│  │  │ Method              Data Source         Accuracy           │     │    │
│  │  │ ──────              ───────────         ────────           │     │    │
│  │  │ DHCP Fingerprint    Option 55, 60       High               │     │    │
│  │  │ HTTP User-Agent     HTTP headers        High               │     │    │
│  │  │ MAC OUI             First 3 bytes       Medium             │     │    │
│  │  │ mDNS/Bonjour        Service types       High               │     │    │
│  │  │ SSDP/UPnP           Device description  High               │     │    │
│  │  │ TCP/IP Stack        TTL, window size    Medium             │     │    │
│  │  │ 802.11 Probe        Capabilities IE     Medium             │     │    │
│  │  │ TLS Fingerprint     JA3/JA3S hash       High               │     │    │
│  │  └────────────────────────────────────────────────────────────┘     │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  DHCP Fingerprinting:                                                        │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  Option 55 (Parameter Request List):                                 │    │
│  │  ┌────────────────────────────────────────────────────────────┐     │    │
│  │  │ Device              Option 55 Signature                    │     │    │
│  │  │ ──────              ───────────────────                    │     │    │
│  │  │ iPhone              1,121,3,6,15,119,252                   │     │    │
│  │  │ iPad                1,121,3,6,15,119,252                   │     │    │
│  │  │ MacBook             1,121,3,6,15,119,252,95,44,46          │     │    │
│  │  │ Windows 10          1,3,6,15,31,33,43,44,46,47,119,121,249 │     │    │
│  │  │ Android             1,3,6,15,26,28,51,58,59,43             │     │    │
│  │  │ Chromecast          1,3,6,12,15,28,42                      │     │    │
│  │  │ Amazon Echo         1,3,6,12,15,28,42,119                  │     │    │
│  │  │ Nest Thermostat     1,3,6,12,15,28,42                      │     │    │
│  │  │ Ring Doorbell       1,3,6,12,15,28,42,119                  │     │    │
│  │  │ Philips Hue         1,3,6,12,15,28,42                      │     │    │
│  │  └────────────────────────────────────────────────────────────┘     │    │
│  │                                                                      │    │
│  │  Option 60 (Vendor Class Identifier):                                │    │
│  │  ┌────────────────────────────────────────────────────────────┐     │    │
│  │  │ Device              Option 60 Value                        │     │    │
│  │  │ ──────              ───────────────                        │     │    │
│  │  │ Windows             MSFT 5.0                               │     │    │
│  │  │ Android 10          android-dhcp-10                        │     │    │
│  │  │ Linux               dhcpcd-6.11.5                          │     │    │
│  │  │ Cisco IP Phone      Cisco Systems, Inc. IP Phone           │     │    │
│  │  │ HP Printer          Hewlett-Packard JetDirect               │     │    │
│  │  └────────────────────────────────────────────────────────────┘     │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  MAC OUI Database:                                                           │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  ┌────────────────────────────────────────────────────────────┐     │    │
│  │  │ OUI (First 3 bytes)    Manufacturer                        │     │    │
│  │  │ ───────────────────    ────────────                        │     │    │
│  │  │ 00:17:88               Philips Lighting                    │     │    │
│  │  │ 18:B4:30               Nest Labs                           │     │    │
│  │  │ 44:65:0D               Amazon Technologies                 │     │    │
│  │  │ 68:37:E9               Amazon Technologies                 │     │    │
│  │  │ B0:FC:36               Google                              │     │    │
│  │  │ F4:F5:D8               Google                              │     │    │
│  │  │ 7C:2F:80               Apple                               │     │    │
│  │  │ 3C:22:FB               Apple                               │     │    │
│  │  │ 00:1A:11               Google                              │     │    │
│  │  │ 94:94:26               Ring                                │     │    │
│  │  └────────────────────────────────────────────────────────────┘     │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### DC.2 MAC Address Randomization

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    MAC ADDRESS RANDOMIZATION                                 │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  MAC Randomization Types:                                                    │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  ┌────────────────────────────────────────────────────────────┐     │    │
│  │  │ Type                Description                            │     │    │
│  │  │ ────                ───────────                            │     │    │
│  │  │ Probe Randomization Random MAC in probe requests           │     │    │
│  │  │ Per-Network         Different MAC per saved network        │     │    │
│  │  │ Per-Connection      New MAC each connection                │     │    │
│  │  │ Daily Rotation      MAC changes daily                      │     │    │
│  │  └────────────────────────────────────────────────────────────┘     │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  Identifying Randomized MACs:                                                │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  MAC Address Format: XX:XX:XX:XX:XX:XX                               │    │
│  │                                                                      │    │
│  │  Second character of first byte:                                     │    │
│  │  - 2, 6, A, E = Locally Administered (randomized)                    │    │
│  │  - 0, 4, 8, C = Universally Administered (real)                      │    │
│  │                                                                      │    │
│  │  Examples:                                                           │    │
│  │  - 02:XX:XX:XX:XX:XX = Randomized                                    │    │
│  │  - 06:XX:XX:XX:XX:XX = Randomized                                    │    │
│  │  - 00:17:88:XX:XX:XX = Real (Philips)                                │    │
│  │  - 44:65:0D:XX:XX:XX = Real (Amazon)                                 │    │
│  │                                                                      │    │
│  │  Bit 1 of first byte (U/L bit):                                      │    │
│  │  - 0 = Universally Administered                                      │    │
│  │  - 1 = Locally Administered                                          │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  Platform Behavior:                                                          │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  ┌────────────────────────────────────────────────────────────┐     │    │
│  │  │ Platform        Probe Random    Connected Random           │     │    │
│  │  │ ────────        ────────────    ────────────────           │     │    │
│  │  │ iOS 14+         Yes             Per-network (default)      │     │    │
│  │  │ Android 10+     Yes             Per-network (default)      │     │    │
│  │  │ Windows 10+     Yes             Per-network (optional)     │     │    │
│  │  │ macOS 14+       Yes             Per-network (optional)     │     │    │
│  │  │ Linux           Varies          Varies                     │     │    │
│  │  └────────────────────────────────────────────────────────────┘     │    │
│  │                                                                      │    │
│  │  Impact on WiFi Operations:                                          │    │
│  │  - MAC-based authentication may fail                                 │    │
│  │  - Device tracking becomes difficult                                 │    │
│  │  - Analytics less accurate                                           │    │
│  │  - Roaming may be affected                                           │    │
│  │                                                                      │    │
│  │  Workarounds:                                                        │    │
│  │  - Use 802.1X authentication                                         │    │
│  │  - Use device certificates                                           │    │
│  │  - Rely on DHCP fingerprinting                                       │    │
│  │  - Use application-layer identification                              │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### DC.3 IoT Device Categories

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    IoT DEVICE CATEGORIES                                     │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  Device Categories:                                                          │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  ┌────────────────────────────────────────────────────────────┐     │    │
│  │  │ Category            Examples                               │     │    │
│  │  │ ────────            ────────                               │     │    │
│  │  │ Smart Speakers      Amazon Echo, Google Home, Apple HomePod│     │    │
│  │  │ Smart Displays      Echo Show, Nest Hub, Portal            │     │    │
│  │  │ Streaming           Chromecast, Fire TV, Roku, Apple TV    │     │    │
│  │  │ Thermostats         Nest, Ecobee, Honeywell                │     │    │
│  │  │ Cameras             Ring, Nest Cam, Wyze, Arlo             │     │    │
│  │  │ Doorbells           Ring, Nest Hello, Eufy                 │     │    │
│  │  │ Lighting            Philips Hue, LIFX, Sengled             │     │    │
│  │  │ Locks               August, Yale, Schlage                  │     │    │
│  │  │ Appliances          Smart refrigerators, washers           │     │    │
│  │  │ Wearables           Smartwatches, fitness trackers         │     │    │
│  │  │ Medical             Blood pressure, glucose monitors       │     │    │
│  │  │ Industrial          Sensors, actuators, PLCs               │     │    │
│  │  └────────────────────────────────────────────────────────────┘     │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  IoT Security Concerns:                                                      │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  ┌────────────────────────────────────────────────────────────┐     │    │
│  │  │ Concern             Description                            │     │    │
│  │  │ ───────             ───────────                            │     │    │
│  │  │ Default Credentials Factory passwords unchanged            │     │    │
│  │  │ No Updates          Firmware never updated                 │     │    │
│  │  │ Weak Encryption     WEP, weak TLS, or none                 │     │    │
│  │  │ Open Ports          Unnecessary services exposed           │     │    │
│  │  │ Cloud Dependency    Requires internet for local control    │     │    │
│  │  │ Data Privacy        Sends data to manufacturer             │     │    │
│  │  │ Botnet Risk         Can be recruited into botnets          │     │    │
│  │  └────────────────────────────────────────────────────────────┘     │    │
│  │                                                                      │    │
│  │  Recommended Policies:                                               │    │
│  │  - Separate VLAN for IoT devices                                     │    │
│  │  - Block IoT-to-IoT communication                                    │    │
│  │  - Allow only required cloud endpoints                               │    │
│  │  - Monitor for anomalous behavior                                    │    │
│  │  - Regular firmware updates                                          │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  IoT VLAN Configuration:                                                     │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  # Create IoT SSID                                                   │    │
│  │  ssid IoT-Devices                                                    │    │
│  │    vlan 50                                                           │    │
│  │    security wpa2-psk                                                 │    │
│  │    psk "IoTSecurePassword123"                                        │    │
│  │    client-isolation enable                                           │    │
│  │                                                                      │    │
│  │  # Firewall policy for IoT                                           │    │
│  │  firewall-policy iot-policy                                          │    │
│  │    # Allow DNS                                                       │    │
│  │    rule 10 permit udp any any eq 53                                  │    │
│  │    # Allow NTP                                                       │    │
│  │    rule 20 permit udp any any eq 123                                 │    │
│  │    # Allow HTTPS to cloud                                            │    │
│  │    rule 30 permit tcp any any eq 443                                 │    │
│  │    # Block internal networks                                         │    │
│  │    rule 40 deny ip any 10.0.0.0/8                                    │    │
│  │    rule 50 deny ip any 172.16.0.0/12                                 │    │
│  │    rule 60 deny ip any 192.168.0.0/16                                │    │
│  │    # Allow internet                                                  │    │
│  │    rule 100 permit ip any any                                        │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Appendix DD: Logging and Monitoring

### DD.1 Syslog Configuration

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    SYSLOG CONFIGURATION                                      │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  Syslog Severity Levels:                                                     │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  ┌────────────────────────────────────────────────────────────┐     │    │
│  │  │ Level    Name          Description                         │     │    │
│  │  │ ─────    ────          ───────────                         │     │    │
│  │  │ 0        Emergency     System unusable                     │     │    │
│  │  │ 1        Alert         Immediate action required           │     │    │
│  │  │ 2        Critical      Critical conditions                 │     │    │
│  │  │ 3        Error         Error conditions                    │     │    │
│  │  │ 4        Warning       Warning conditions                  │     │    │
│  │  │ 5        Notice        Normal but significant              │     │    │
│  │  │ 6        Info          Informational                       │     │    │
│  │  │ 7        Debug         Debug-level messages                │     │    │
│  │  └────────────────────────────────────────────────────────────┘     │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  Syslog Facilities:                                                          │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  ┌────────────────────────────────────────────────────────────┐     │    │
│  │  │ Facility    Code    Description                            │     │    │
│  │  │ ────────    ────    ───────────                            │     │    │
│  │  │ kern        0       Kernel messages                        │     │    │
│  │  │ user        1       User-level messages                    │     │    │
│  │  │ daemon      3       System daemons                         │     │    │
│  │  │ auth        4       Security/authorization                 │     │    │
│  │  │ syslog      5       Syslog internal                        │     │    │
│  │  │ local0-7    16-23   Local use                              │     │    │
│  │  └────────────────────────────────────────────────────────────┘     │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  AP Syslog Configuration:                                                    │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  # Configure syslog server                                           │    │
│  │  logging host 10.1.1.100                                             │    │
│  │  logging host 10.1.1.101 port 1514                                   │    │
│  │  logging facility local0                                             │    │
│  │  logging level info                                                  │    │
│  │                                                                      │    │
│  │  # Enable specific log categories                                    │    │
│  │  logging category client-events level info                           │    │
│  │  logging category security level warning                             │    │
│  │  logging category radio level error                                  │    │
│  │  logging category system level notice                                │    │
│  │                                                                      │    │
│  │  # TLS syslog (RFC 5425)                                             │    │
│  │  logging host 10.1.1.100 protocol tls                                │    │
│  │  logging tls-certificate /etc/ssl/syslog-client.pem                  │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  Important Log Messages:                                                     │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  Client Events:                                                      │    │
│  │  - Client associated: MAC, SSID, RSSI, channel                       │    │
│  │  - Client disassociated: MAC, reason code                            │    │
│  │  - Client authenticated: MAC, auth type, user                        │    │
│  │  - Client roamed: MAC, from AP, to AP                                │    │
│  │                                                                      │    │
│  │  Security Events:                                                    │    │
│  │  - Authentication failure: MAC, reason                               │    │
│  │  - Deauth attack detected: MAC, count                                │    │
│  │  - Rogue AP detected: BSSID, SSID, channel                           │    │
│  │  - MIC failure: MAC, count                                           │    │
│  │                                                                      │    │
│  │  Radio Events:                                                       │    │
│  │  - Channel change: radio, old channel, new channel                   │    │
│  │  - Power change: radio, old power, new power                         │    │
│  │  - Radar detected: channel, timestamp                                │    │
│  │  - Interference detected: channel, type                              │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### DD.2 SNMP Monitoring

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    SNMP MONITORING                                           │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  SNMP Versions:                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  ┌────────────────────────────────────────────────────────────┐     │    │
│  │  │ Version    Security            Recommendation             │     │    │
│  │  │ ───────    ────────            ──────────────             │     │    │
│  │  │ v1         Community string    Not recommended            │     │    │
│  │  │ v2c        Community string    Legacy only                │     │    │
│  │  │ v3         Auth + Encryption   Recommended                │     │    │
│  │  └────────────────────────────────────────────────────────────┘     │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  WiFi MIBs:                                                                  │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  ┌────────────────────────────────────────────────────────────┐     │    │
│  │  │ MIB                     Description                        │     │    │
│  │  │ ───                     ───────────                        │     │    │
│  │  │ IEEE802dot11-MIB        Standard 802.11 MIB                │     │    │
│  │  │ IF-MIB                  Interface statistics               │     │    │
│  │  │ ENTITY-MIB              Physical entity info               │     │    │
│  │  │ HOST-RESOURCES-MIB      CPU, memory, storage               │     │    │
│  │  │ Vendor-specific         Custom AP statistics               │     │    │
│  │  └────────────────────────────────────────────────────────────┘     │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  Key OIDs:                                                                   │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  ┌────────────────────────────────────────────────────────────┐     │    │
│  │  │ OID                           Description                  │     │    │
│  │  │ ───                           ───────────                  │     │    │
│  │  │ 1.3.6.1.2.1.1.1               sysDescr                     │     │    │
│  │  │ 1.3.6.1.2.1.1.3               sysUpTime                    │     │    │
│  │  │ 1.3.6.1.2.1.2.2.1.10          ifInOctets                   │     │    │
│  │  │ 1.3.6.1.2.1.2.2.1.16          ifOutOctets                  │     │    │
│  │  │ 1.3.6.1.4.1.14179.2.1.1       bsnDot11EssTable             │     │    │
│  │  │ 1.3.6.1.4.1.14179.2.2.1       bsnAPTable                   │     │    │
│  │  │ 1.3.6.1.4.1.14179.2.2.2       bsnAPIfTable                 │     │    │
│  │  └────────────────────────────────────────────────────────────┘     │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  SNMP Configuration:                                                         │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  # SNMPv3 configuration                                              │    │
│  │  snmp-server enable                                                  │    │
│  │  snmp-server user admin auth sha AuthPass123 priv aes PrivPass123    │    │
│  │  snmp-server host 10.1.1.100 version 3 user admin                    │    │
│  │                                                                      │    │
│  │  # SNMP traps                                                        │    │
│  │  snmp-server trap-source interface management                        │    │
│  │  snmp-server trap client-association                                 │    │
│  │  snmp-server trap client-disassociation                              │    │
│  │  snmp-server trap rogue-ap                                           │    │
│  │  snmp-server trap radio-failure                                      │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### DD.3 Streaming Telemetry

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    STREAMING TELEMETRY                                       │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  Telemetry Protocols:                                                        │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  ┌────────────────────────────────────────────────────────────┐     │    │
│  │  │ Protocol        Transport       Encoding                   │     │    │
│  │  │ ────────        ─────────       ────────                   │     │    │
│  │  │ gRPC            HTTP/2          Protobuf                   │     │    │
│  │  │ gNMI            gRPC            Protobuf                   │     │    │
│  │  │ Kafka           TCP             JSON/Avro                  │     │    │
│  │  │ MQTT            TCP             JSON                       │     │    │
│  │  │ WebSocket       HTTP            JSON                       │     │    │
│  │  └────────────────────────────────────────────────────────────┘     │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  Telemetry Data Types:                                                       │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  ┌────────────────────────────────────────────────────────────┐     │    │
│  │  │ Category            Metrics                                │     │    │
│  │  │ ────────            ───────                                │     │    │
│  │  │ Client Stats        RSSI, SNR, data rate, retries          │     │    │
│  │  │ Radio Stats         Channel util, noise, interference      │     │    │
│  │  │ AP Stats            CPU, memory, uptime, temperature       │     │    │
│  │  │ Traffic Stats       Bytes, packets, errors, drops          │     │    │
│  │  │ Security Stats      Auth failures, attacks, rogues         │     │    │
│  │  │ Roaming Stats       Roam count, latency, failures          │     │    │
│  │  └────────────────────────────────────────────────────────────┘     │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  Sample Telemetry Data (JSON):                                               │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  {                                                                   │    │
│  │    "timestamp": "2026-01-08T12:00:00Z",                              │    │
│  │    "ap_name": "AP-Floor2-East",                                      │    │
│  │    "ap_mac": "00:11:22:33:44:55",                                    │    │
│  │    "radio": {                                                        │    │
│  │      "band": "5GHz",                                                 │    │
│  │      "channel": 36,                                                  │    │
│  │      "channel_width": 80,                                            │    │
│  │      "tx_power": 17,                                                 │    │
│  │      "channel_utilization": 45,                                      │    │
│  │      "noise_floor": -95,                                             │    │
│  │      "client_count": 25                                              │    │
│  │    },                                                                │    │
│  │    "clients": [                                                      │    │
│  │      {                                                               │    │
│  │        "mac": "AA:BB:CC:DD:EE:FF",                                   │    │
│  │        "rssi": -65,                                                  │    │
│  │        "snr": 30,                                                    │    │
│  │        "tx_rate": 866,                                               │    │
│  │        "rx_rate": 866,                                               │    │
│  │        "tx_bytes": 1234567,                                          │    │
│  │        "rx_bytes": 9876543                                           │    │
│  │      }                                                               │    │
│  │    ]                                                                 │    │
│  │  }                                                                   │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Appendix DE: Troubleshooting Guide

### DE.1 Connection Issues

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    CONNECTION TROUBLESHOOTING                                │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  Cannot See SSID:                                                            │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  ┌────────────────────────────────────────────────────────────┐     │    │
│  │  │ Symptom                 Possible Cause          Solution   │     │    │
│  │  │ ───────                 ──────────────          ────────   │     │    │
│  │  │ SSID not visible        Hidden SSID             Manual add │     │    │
│  │  │ SSID not visible        Wrong band              Check 5GHz │     │    │
│  │  │ SSID not visible        AP down                 Check AP   │     │    │
│  │  │ SSID not visible        Regulatory domain       Check DFS  │     │    │
│  │  │ SSID not visible        Client too far          Move closer│     │    │
│  │  └────────────────────────────────────────────────────────────┘     │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  Authentication Failures:                                                    │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  ┌────────────────────────────────────────────────────────────┐     │    │
│  │  │ Error                   Cause                   Solution   │     │    │
│  │  │ ─────                   ─────                   ────────   │     │    │
│  │  │ Wrong password          Incorrect PSK           Re-enter   │     │    │
│  │  │ Auth timeout            RADIUS unreachable      Check srv  │     │    │
│  │  │ EAP failure             Certificate issue       Check cert │     │    │
│  │  │ User not found          Wrong username          Verify user│     │    │
│  │  │ Account disabled        AD/LDAP issue           Check AD   │     │    │
│  │  │ MIC failure             Key mismatch            Re-auth    │     │    │
│  │  └────────────────────────────────────────────────────────────┘     │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  Association Failures:                                                       │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  ┌────────────────────────────────────────────────────────────┐     │    │
│  │  │ Status Code    Meaning                     Solution        │     │    │
│  │  │ ───────────    ───────                     ────────        │     │    │
│  │  │ 12             Assoc denied, reason        Check policy    │     │    │
│  │  │ 17             AP unable to handle         Reduce clients  │     │    │
│  │  │ 18             Timeout                     Check signal    │     │    │
│  │  │ 34             Requested SSID not avail    Check SSID      │     │    │
│  │  │ 37             Requested caps not support  Check security  │     │    │
│  │  └────────────────────────────────────────────────────────────┘     │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  DHCP Issues:                                                                │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  ┌────────────────────────────────────────────────────────────┐     │    │
│  │  │ Symptom                 Cause                   Solution   │     │    │
│  │  │ ───────                 ─────                   ────────   │     │    │
│  │  │ No IP address           DHCP server down        Check srv  │     │    │
│  │  │ 169.254.x.x             DHCP timeout            Check VLAN │     │    │
│  │  │ Wrong subnet            Wrong VLAN              Check VLAN │     │    │
