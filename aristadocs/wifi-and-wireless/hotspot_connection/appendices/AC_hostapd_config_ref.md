## Appendix AC: Complete hostapd Configuration Reference

### AC.1 Full Configuration Example

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    COMPLETE HOSTAPD CONFIGURATION                            │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  # /etc/hostapd/hostapd.conf                                                 │
│  # Complete configuration for enterprise WiFi 6 AP                          │
│                                                                              │
│  ############################################################               │
│  # Interface Configuration                                                   │
│  ############################################################               │
│  interface=wlan0                                                             │
│  bridge=br0                                                                  │
│  driver=nl80211                                                              │
│  ctrl_interface=/var/run/hostapd                                             │
│  ctrl_interface_group=0                                                      │
│                                                                              │
│  ############################################################               │
│  # SSID Configuration                                                        │
│  ############################################################               │
│  ssid=Enterprise-WiFi                                                        │
│  utf8_ssid=1                                                                 │
│  ignore_broadcast_ssid=0                                                     │
│                                                                              │
│  ############################################################               │
│  # Country and Regulatory                                                    │
│  ############################################################               │
│  country_code=US                                                             │
│  ieee80211d=1                                                                │
│  ieee80211h=1                                                                │
│  local_pwr_constraint=3                                                      │
│  spectrum_mgmt_required=1                                                    │
│                                                                              │
│  ############################################################               │
│  # Radio Configuration (5 GHz, 80 MHz, WiFi 6)                               │
│  ############################################################               │
│  hw_mode=a                                                                   │
│  channel=36                                                                  │
│  op_class=128                                                                │
│                                                                              │
│  # 802.11n (HT)                                                              │
│  ieee80211n=1                                                                │
│  ht_capab=[HT40+][SHORT-GI-20][SHORT-GI-40][TX-STBC][RX-STBC1][MAX-AMSDU-7935]│
│                                                                              │
│  # 802.11ac (VHT)                                                            │
│  ieee80211ac=1                                                               │
│  vht_oper_chwidth=1                                                          │
│  vht_oper_centr_freq_seg0_idx=42                                             │
│  vht_capab=[MAX-MPDU-11454][RXLDPC][SHORT-GI-80][TX-STBC-2BY1][RX-STBC-1]    │
│  vht_capab=[SU-BEAMFORMER][SU-BEAMFORMEE][MU-BEAMFORMER][MU-BEAMFORMEE]      │
│                                                                              │
│  # 802.11ax (HE)                                                             │
│  ieee80211ax=1                                                               │
│  he_su_beamformer=1                                                          │
│  he_su_beamformee=1                                                          │
│  he_mu_beamformer=1                                                          │
│  he_bss_color=42                                                             │
│  he_default_pe_duration=4                                                    │
│  he_rts_threshold=1023                                                       │
│  he_oper_chwidth=1                                                           │
│  he_oper_centr_freq_seg0_idx=42                                              │
│                                                                              │
│  ############################################################               │
│  # Security Configuration (WPA3-Enterprise)                                  │
│  ############################################################               │
│  wpa=2                                                                       │
│  wpa_key_mgmt=WPA-EAP WPA-EAP-SHA256 WPA-EAP-SUITE-B-192                     │
│  wpa_pairwise=CCMP GCMP-256                                                  │
│  rsn_pairwise=CCMP GCMP-256                                                  │
│  group_cipher=CCMP                                                           │
│                                                                              │
│  # 802.11w (MFP)                                                             │
│  ieee80211w=2                                                                │
│  group_mgmt_cipher=AES-128-CMAC                                              │
│  beacon_prot=1                                                               │
│                                                                              │
│  ############################################################               │
│  # RADIUS Configuration                                                      │
│  ############################################################               │
│  ieee8021x=1                                                                 │
│  eapol_version=2                                                             │
│  eap_reauth_period=3600                                                      │
│                                                                              │
│  # Authentication Server                                                     │
│  auth_server_addr=10.0.0.100                                                 │
│  auth_server_port=1812                                                       │
│  auth_server_shared_secret=RadiusSecret123                                   │
│                                                                              │
│  # Accounting Server                                                         │
│  acct_server_addr=10.0.0.100                                                 │
│  acct_server_port=1813                                                       │
│  acct_server_shared_secret=RadiusSecret123                                   │
│                                                                              │
│  # RADIUS options                                                            │
│  radius_acct_interim_interval=300                                            │
│  radius_request_cui=1                                                        │
│  radius_das_port=3799                                                        │
│  radius_das_client=10.0.0.100 DasSecret123                                   │
│  radius_das_require_event_timestamp=1                                        │
│                                                                              │
│  ############################################################               │
│  # Fast Transition (802.11r)                                                 │
│  ############################################################               │
│  mobility_domain=a1b2                                                        │
│  ft_over_ds=1                                                                │
│  ft_psk_generate_local=0                                                     │
│  pmk_r1_push=1                                                               │
│  r0_key_lifetime=10000                                                       │
│  r1_key_holder=000102030405                                                  │
│  reassociation_deadline=1000                                                 │
│  r0kh=02:00:00:00:03:00 nas1.example.com 000102030405060708090a0b0c0d0e0f    │
│  r0kh=02:00:00:00:04:00 nas2.example.com 000102030405060708090a0b0c0d0e0f    │
│  r1kh=02:00:00:00:03:00 02:00:00:00:03:00 000102030405060708090a0b0c0d0e0f   │
│  r1kh=02:00:00:00:04:00 02:00:00:00:04:00 000102030405060708090a0b0c0d0e0f   │
│                                                                              │
│  ############################################################               │
│  # OKC (Opportunistic Key Caching)                                           │
│  ############################################################               │
│  okc=1                                                                       │
│                                                                              │
│  ############################################################               │
│  # 802.11k/v (RRM and WNM)                                                   │
│  ############################################################               │
│  rrm_neighbor_report=1                                                       │
│  rrm_beacon_report=1                                                         │
│  bss_transition=1                                                            │
│  wnm_sleep_mode=1                                                            │
│  time_advertisement=2                                                        │
│  time_zone=EST5EDT,M3.2.0,M11.1.0                                            │
│                                                                              │
│  ############################################################               │
│  # Hotspot 2.0                                                               │
│  ############################################################               │
│  hs20=1                                                                      │
│  hs20_release=3                                                              │
│  disable_dgaf=1                                                              │
│  osen=0                                                                      │
│  anqp_domain_id=1234                                                         │
│  hs20_deauth_req_timeout=60                                                  │
│                                                                              │
│  # Venue                                                                     │
│  venue_group=2                                                               │
│  venue_type=8                                                                │
│  venue_name=eng:Example Venue                                                │
│                                                                              │
│  # Network Type                                                              │
│  network_auth_type=00                                                        │
│  ipaddr_type_availability=0c                                                 │
│                                                                              │
│  # Domain and Realm                                                          │
│  domain_name=example.com                                                     │
│  nai_realm=0,example.com,13[5:6],21[2:4][5:7]                                │
│                                                                              │
│  # Roaming Consortium                                                        │
│  roaming_consortium=506F9A                                                   │
│  roaming_consortium=001BC504BD                                               │
│                                                                              │
│  # Operator Name                                                             │
│  hs20_oper_friendly_name=eng:Example Operator                                │
│                                                                              │
│  # WAN Metrics                                                               │
│  hs20_wan_metrics=01:8000:1000:80:240:3000                                   │
│                                                                              │
│  # Connection Capability                                                     │
│  hs20_conn_capab=6:22:1                                                      │
│  hs20_conn_capab=6:80:1                                                      │
│  hs20_conn_capab=6:443:1                                                     │
│  hs20_conn_capab=17:5060:1                                                   │
│                                                                              │
│  ############################################################               │
│  # QoS (WMM)                                                                 │
│  ############################################################               │
│  wmm_enabled=1                                                               │
│  uapsd_advertisement_enabled=1                                               │
│                                                                              │
│  # Voice (AC_VO)                                                             │
│  wmm_ac_vo_cwmin=2                                                           │
│  wmm_ac_vo_cwmax=3                                                           │
│  wmm_ac_vo_aifs=2                                                            │
│  wmm_ac_vo_txop_limit=47                                                     │
│  wmm_ac_vo_acm=0                                                             │
│                                                                              │
│  # Video (AC_VI)                                                             │
│  wmm_ac_vi_cwmin=3                                                           │
│  wmm_ac_vi_cwmax=4                                                           │
│  wmm_ac_vi_aifs=2                                                            │
│  wmm_ac_vi_txop_limit=94                                                     │
│  wmm_ac_vi_acm=0                                                             │
│                                                                              │
│  # Best Effort (AC_BE)                                                       │
│  wmm_ac_be_cwmin=4                                                           │
│  wmm_ac_be_cwmax=10                                                          │
│  wmm_ac_be_aifs=3                                                            │
│  wmm_ac_be_txop_limit=0                                                      │
│  wmm_ac_be_acm=0                                                             │
│                                                                              │
│  # Background (AC_BK)                                                        │
│  wmm_ac_bk_cwmin=4                                                           │
│  wmm_ac_bk_cwmax=10                                                          │
│  wmm_ac_bk_aifs=7                                                            │
│  wmm_ac_bk_txop_limit=0                                                      │
│  wmm_ac_bk_acm=0                                                             │
│                                                                              │
│  ############################################################               │
│  # Logging                                                                   │
│  ############################################################               │
│  logger_syslog=-1                                                            │
│  logger_syslog_level=2                                                       │
│  logger_stdout=-1                                                            │
│  logger_stdout_level=2                                                       │
│                                                                              │
│  ############################################################               │
│  # Miscellaneous                                                             │
│  ############################################################               │
│  max_num_sta=128                                                             │
│  ap_max_inactivity=300                                                       │
│  skip_inactivity_poll=0                                                      │
│  disassoc_low_ack=1                                                          │
│  preamble=1                                                                  │
│  wpa_group_rekey=600                                                         │
│  wpa_strict_rekey=1                                                          │
│  wpa_gmk_rekey=86400                                                         │
│  wpa_ptk_rekey=600                                                           │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

