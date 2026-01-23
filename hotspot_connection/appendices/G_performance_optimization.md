## Appendix G: Performance Optimization

### G.1 Connection Time Optimization

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    CONNECTION TIME OPTIMIZATION                              │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  Phase 1: Scanning Optimization                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │ Problem: Scanning all channels takes 2-5 seconds                    │    │
│  │                                                                      │    │
│  │ Solutions:                                                           │    │
│  │   • Use active scanning (probe requests)                            │    │
│  │   • Reduce dwell time per channel                                   │    │
│  │   • Use preferred channel list                                      │    │
│  │   • Enable 802.11k neighbor reports                                 │    │
│  │   • Use background scanning                                         │    │
│  │                                                                      │    │
│  │ Configuration:                                                       │    │
│  │   # Enable RRM (802.11k)                                            │    │
│  │   rrm_neighbor_report=1                                             │    │
│  │   rrm_beacon_report=1                                               │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  Phase 3: Authentication Optimization                                        │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │ Problem: SAE takes 10-50ms for crypto operations                    │    │
│  │                                                                      │    │
│  │ Solutions:                                                           │    │
│  │   • Use SAE-H2E (faster than H2C)                                   │    │
│  │   • Enable SAE-PT (Password Token) caching                         │    │
│  │   • Use hardware crypto acceleration                                │    │
│  │   • Tune anti-clogging threshold                                    │    │
│  │                                                                      │    │
│  │ Configuration:                                                       │    │
│  │   sae_pwe=2  # H2E only                                             │    │
│  │   sae_anti_clogging_threshold=5                                     │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  Phase 5: 4-Way Handshake Optimization                                       │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │ Problem: EAPOL frame loss causes retransmissions                    │    │
│  │                                                                      │    │
│  │ Solutions:                                                           │    │
│  │   • Reduce EAPOL timeout                                            │    │
│  │   • Increase EAPOL retry count                                      │    │
│  │   • Use QoS for EAPOL frames                                        │    │
│  │   • Enable PMKSA caching                                            │    │
│  │                                                                      │    │
│  │ Configuration:                                                       │    │
│  │   wpa_pairwise_update_count=3                                       │    │
│  │   wpa_group_update_count=3                                          │    │
│  │   wpa_ptk_rekey=0  # Disable PTK rekeying                           │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  Phase 6: DHCP Optimization                                                  │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │ Problem: DHCP can take 100-500ms                                    │    │
│  │                                                                      │    │
│  │ Solutions:                                                           │    │
│  │   • Use local DHCP server on AP                                     │    │
│  │   • Enable DHCP relay optimization                                  │    │
│  │   • Use DHCP rapid commit (2-message exchange)                      │    │
│  │   • Increase DHCP pool size                                         │    │
│  │   • Reduce lease time for guest networks                            │    │
│  │                                                                      │    │
│  │ Configuration:                                                       │    │
│  │   # dnsmasq.conf                                                    │    │
│  │   dhcp-rapid-commit                                                 │    │
│  │   dhcp-lease-max=1000                                               │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  Roaming Optimization:                                                       │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │ Problem: Full re-authentication takes 500-2000ms                    │    │
│  │                                                                      │    │
│  │ Solutions:                                                           │    │
│  │   • Enable OKC (Opportunistic Key Caching)                          │    │
│  │   • Enable 802.11r Fast Transition                                  │    │
│  │   • Use FT-over-DS for faster roaming                               │    │
│  │   • Enable PMK caching                                              │    │
│  │   • Use 802.11v BSS Transition Management                           │    │
│  │                                                                      │    │
│  │ Configuration:                                                       │    │
│  │   okc=1                                                             │    │
│  │   mobility_domain=a1b2                                              │    │
│  │   ft_over_ds=1                                                      │    │
│  │   pmk_r1_push=1                                                     │    │
│  │   bss_transition=1                                                  │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### G.2 Throughput Optimization

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                      THROUGHPUT OPTIMIZATION                                 │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  Channel Configuration:                                                      │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │ • Use 5 GHz band for higher throughput                              │    │
│  │ • Use 80 MHz or 160 MHz channel width                               │    │
│  │ • Avoid DFS channels if possible (radar detection delays)          │    │
│  │ • Use non-overlapping channels                                      │    │
│  │                                                                      │    │
│  │ Configuration:                                                       │    │
│  │   hw_mode=a                                                         │    │
│  │   channel=36                                                        │    │
│  │   vht_oper_chwidth=1  # 80 MHz                                      │    │
│  │   vht_oper_centr_freq_seg0_idx=42                                   │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  802.11n/ac/ax Features:                                                     │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │ • Enable A-MPDU aggregation                                         │    │
│  │ • Enable A-MSDU aggregation                                         │    │
│  │ • Enable short guard interval                                       │    │
│  │ • Enable LDPC coding                                                │    │
│  │ • Enable beamforming                                                │    │
│  │                                                                      │    │
│  │ Configuration:                                                       │    │
│  │   ieee80211n=1                                                      │    │
│  │   ieee80211ac=1                                                     │    │
│  │   ieee80211ax=1                                                     │    │
│  │   ht_capab=[HT40+][SHORT-GI-40][LDPC][TX-STBC][RX-STBC1]           │    │
│  │   vht_capab=[SHORT-GI-80][SU-BEAMFORMER][SU-BEAMFORMEE]            │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  QoS Configuration:                                                          │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │ • Enable WMM for QoS                                                │    │
│  │ • Configure EDCA parameters                                         │    │
│  │ • Enable U-APSD for power save                                      │    │
│  │                                                                      │    │
│  │ Configuration:                                                       │    │
│  │   wmm_enabled=1                                                     │    │
│  │   uapsd_advertisement_enabled=1                                     │    │
│  │   wmm_ac_bk_cwmin=4                                                 │    │
│  │   wmm_ac_bk_cwmax=10                                                │    │
│  │   wmm_ac_bk_aifs=7                                                  │    │
│  │   wmm_ac_bk_txop_limit=0                                            │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  Airtime Fairness:                                                           │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │ • Enable airtime fairness to prevent slow clients from             │    │
│  │   monopolizing the channel                                          │    │
│  │ • Configure per-client rate limiting                                │    │
│  │ • Use band steering to move capable clients to 5 GHz               │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

