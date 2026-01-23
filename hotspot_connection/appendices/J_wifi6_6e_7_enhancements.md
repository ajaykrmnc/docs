## Appendix J: WiFi 6/6E/7 Enhancements

### J.1 WiFi 6 (802.11ax) Features

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                      WIFI 6 (802.11ax) FEATURES                              │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  OFDMA (Orthogonal Frequency Division Multiple Access):                      │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │ • Divides channel into Resource Units (RUs)                         │    │
│  │ • Multiple clients can transmit/receive simultaneously              │    │
│  │ • Reduces latency for small packets                                 │    │
│  │ • RU sizes: 26, 52, 106, 242, 484, 996, 2x996 tones                │    │
│  │                                                                      │    │
│  │ Configuration:                                                       │    │
│  │   he_su_beamformer=1                                                │    │
│  │   he_su_beamformee=1                                                │    │
│  │   he_mu_beamformer=1                                                │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  MU-MIMO (Multi-User MIMO):                                                  │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │ • Uplink and downlink MU-MIMO                                       │    │
│  │ • Up to 8 spatial streams                                           │    │
│  │ • Beamforming for improved range                                    │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  TWT (Target Wake Time):                                                     │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │ • Scheduled wake times for clients                                  │    │
│  │ • Reduces contention and power consumption                          │    │
│  │ • Individual and broadcast TWT                                      │    │
│  │                                                                      │    │
│  │ Configuration:                                                       │    │
│  │   he_twt_required=0                                                 │    │
│  │   he_twt_responder=1                                                │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  BSS Coloring:                                                               │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │ • 6-bit BSS color in HE SIG-A                                       │    │
│  │ • Allows spatial reuse in dense environments                        │    │
│  │ • Reduces CCA sensitivity for different colors                      │    │
│  │                                                                      │    │
│  │ Configuration:                                                       │    │
│  │   he_bss_color=1                                                    │    │
│  │   he_bss_color_partial=0                                            │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  1024-QAM:                                                                   │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │ • Higher modulation for 25% throughput increase                     │    │
│  │ • Requires good SNR (>35 dB)                                        │    │
│  │ • MCS 10 and MCS 11                                                 │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### J.2 WiFi 6E (6 GHz Band)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                      WIFI 6E (6 GHz BAND)                                    │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  Spectrum:                                                                   │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │ • 5925 - 7125 MHz (1200 MHz of spectrum)                            │    │
│  │ • Up to 59 new 20 MHz channels                                      │    │
│  │ • Up to 7 new 160 MHz channels                                      │    │
│  │ • No legacy devices (clean spectrum)                                │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  Discovery:                                                                  │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │ • Reduced Neighbor Report (RNR) in 2.4/5 GHz beacons               │    │
│  │ • FILS Discovery frames                                             │    │
│  │ • Unsolicited Probe Response                                        │    │
│  │ • Out-of-band discovery required                                    │    │
│  │                                                                      │    │
│  │ Configuration:                                                       │    │
│  │   rnr=1                                                             │    │
│  │   fils_discovery_min_interval=20                                    │    │
│  │   fils_discovery_max_interval=20                                    │    │
│  │   unsol_bcast_probe_resp_interval=20                                │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  Security:                                                                   │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │ • WPA3 required (no WPA2)                                           │    │
│  │ • PMF required                                                      │    │
│  │ • SAE-H2E required                                                  │    │
│  │                                                                      │    │
│  │ Configuration:                                                       │    │
│  │   wpa=2                                                             │    │
│  │   wpa_key_mgmt=SAE                                                  │    │
│  │   ieee80211w=2                                                      │    │
│  │   sae_pwe=1  # H2E only for 6 GHz                                   │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  Power Modes:                                                                │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │ • LPI (Low Power Indoor): Indoor only, lower power                  │    │
│  │ • SP (Standard Power): Higher power with AFC                        │    │
│  │ • VLP (Very Low Power): Portable devices                            │    │
│  │                                                                      │    │
│  │ AFC (Automated Frequency Coordination):                             │    │
│  │   • Database lookup for incumbent protection                        │    │
│  │   • Required for Standard Power operation                           │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### J.3 WiFi 7 (802.11be) Features

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                      WIFI 7 (802.11be) FEATURES                              │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  Multi-Link Operation (MLO):                                                 │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │ • Single connection across multiple bands/channels                  │    │
│  │ • Aggregation: Combine throughput from multiple links              │    │
│  │ • Redundancy: Failover between links                               │    │
│  │ • Low latency: Use least congested link                            │    │
│  │                                                                      │    │
│  │ Configuration:                                                       │    │
│  │   mld_ap=1                                                          │    │
│  │   mld_addr=00:11:22:33:44:55                                        │    │
│  │   mld_id=0                                                          │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  320 MHz Channels:                                                           │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │ • Double the bandwidth of WiFi 6                                    │    │
│  │ • Available in 6 GHz band only                                      │    │
│  │ • Up to 46 Gbps theoretical throughput                              │    │
│  │                                                                      │    │
│  │ Configuration:                                                       │    │
│  │   eht_oper_chwidth=9  # 320 MHz                                     │    │
│  │   eht_oper_centr_freq_seg0_idx=...                                  │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  4096-QAM:                                                                   │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │ • 20% throughput increase over 1024-QAM                             │    │
│  │ • MCS 12 and MCS 13                                                 │    │
│  │ • Requires excellent SNR (>40 dB)                                   │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  Preamble Puncturing:                                                        │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │ • Allows use of wide channels with interference                     │    │
│  │ • Puncture (skip) 20 MHz sub-channels with interference            │    │
│  │ • Maintains wide channel benefits                                   │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  16 Spatial Streams:                                                         │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │ • Double the spatial streams of WiFi 6                              │    │
│  │ • Enhanced MU-MIMO                                                  │    │
│  │ • Coordinated Multi-AP operation                                    │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Document Revision History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2026-01-08 | Auto-generated | Initial document creation |

---

