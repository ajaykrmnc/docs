## Appendix AI: Test Case Reference

### AI.1 Authentication Tests

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    AUTHENTICATION TEST CASES                                 │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  WPA/WPA2 Personal Tests:                                                    │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  Test File: WpaPersonalTest.py                                      │    │
│  │  ┌────────────────────────────────────────────────────────────┐     │    │
│  │  │ Test Case                    Description                   │     │    │
│  │  │ ─────────                    ───────────                   │     │    │
│  │  │ test_wpa2_psk_ccmp           WPA2-PSK with CCMP            │     │    │
│  │  │ test_wpa2_psk_tkip           WPA2-PSK with TKIP            │     │    │
│  │  │ test_wpa_psk_tkip            WPA-PSK with TKIP             │     │    │
│  │  │ test_wpa_wpa2_mixed          Mixed mode WPA/WPA2           │     │    │
│  │  │ test_wrong_passphrase        Incorrect passphrase          │     │    │
│  │  │ test_passphrase_change       Change passphrase             │     │    │
│  │  │ test_gtk_rekey               GTK rekeying                  │     │    │
│  │  │ test_ptk_rekey               PTK rekeying                  │     │    │
│  │  │ test_pmf_required            MFP required                  │     │    │
│  │  │ test_pmf_optional            MFP optional                  │     │    │
│  │  └────────────────────────────────────────────────────────────┘     │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  WPA3 Tests:                                                                 │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  Test File: Wpa3Test.py                                             │    │
│  │  ┌────────────────────────────────────────────────────────────┐     │    │
│  │  │ Test Case                    Description                   │     │    │
│  │  │ ─────────                    ───────────                   │     │    │
│  │  │ test_wpa3_sae                WPA3-SAE authentication       │     │    │
│  │  │ test_wpa3_sae_transition     SAE transition mode           │     │    │
│  │  │ test_wpa3_sae_h2e            SAE Hash-to-Element           │     │    │
│  │  │ test_wpa3_sae_pk             SAE-PK (public key)           │     │    │
│  │  │ test_wpa3_owe                OWE (Enhanced Open)           │     │    │
│  │  │ test_wpa3_owe_transition     OWE transition mode           │     │    │
│  │  │ test_wpa3_enterprise         WPA3-Enterprise               │     │    │
│  │  │ test_wpa3_suite_b_192        Suite B 192-bit               │     │    │
│  │  │ test_sae_anti_clogging       SAE anti-clogging             │     │    │
│  │  │ test_sae_password_id         SAE password identifier       │     │    │
│  │  └────────────────────────────────────────────────────────────┘     │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  802.1X Enterprise Tests:                                                    │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  Test File: EnterpriseAuthTest.py                                   │    │
│  │  ┌────────────────────────────────────────────────────────────┐     │    │
│  │  │ Test Case                    Description                   │     │    │
│  │  │ ─────────                    ───────────                   │     │    │
│  │  │ test_eap_tls                 EAP-TLS authentication        │     │    │
│  │  │ test_eap_ttls_mschapv2       EAP-TTLS/MSCHAPv2             │     │    │
│  │  │ test_eap_ttls_pap            EAP-TTLS/PAP                  │     │    │
│  │  │ test_eap_peap_mschapv2       EAP-PEAP/MSCHAPv2             │     │    │
│  │  │ test_eap_peap_gtc            EAP-PEAP/GTC                  │     │    │
│  │  │ test_eap_fast                EAP-FAST                      │     │    │
│  │  │ test_eap_sim                 EAP-SIM                       │     │    │
│  │  │ test_eap_aka                 EAP-AKA                       │     │    │
│  │  │ test_eap_aka_prime           EAP-AKA'                      │     │    │
│  │  │ test_cert_expiry             Certificate expiration        │     │    │
│  │  │ test_cert_revocation         Certificate revocation        │     │    │
│  │  │ test_radius_failover         RADIUS server failover        │     │    │
│  │  │ test_radius_timeout          RADIUS timeout handling       │     │    │
│  │  └────────────────────────────────────────────────────────────┘     │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  MAC Authentication Tests:                                                   │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  Test File: MacAuthTest.py                                          │    │
│  │  ┌────────────────────────────────────────────────────────────┐     │    │
│  │  │ Test Case                    Description                   │     │    │
│  │  │ ─────────                    ───────────                   │     │    │
│  │  │ test_mac_auth_radius         MAC auth via RADIUS           │     │    │
│  │  │ test_mac_auth_local          MAC auth via local list       │     │    │
│  │  │ test_mac_auth_format         MAC address format options    │     │    │
│  │  │ test_mac_auth_fallback       Fallback to 802.1X            │     │    │
│  │  │ test_mac_auth_vlan           VLAN assignment               │     │    │
│  │  │ test_mac_auth_deny           MAC auth denial               │     │    │
│  │  └────────────────────────────────────────────────────────────┘     │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### AI.2 Roaming Tests

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    ROAMING TEST CASES                                        │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  802.11r Fast Transition Tests:                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  Test File: FastTransitionTest.py                                   │    │
│  │  ┌────────────────────────────────────────────────────────────┐     │    │
│  │  │ Test Case                    Description                   │     │    │
│  │  │ ─────────                    ───────────                   │     │    │
│  │  │ test_ft_over_air             FT over-the-air               │     │    │
│  │  │ test_ft_over_ds              FT over-the-DS                │     │    │
│  │  │ test_ft_psk                  FT with PSK                   │     │    │
│  │  │ test_ft_eap                  FT with 802.1X                │     │    │
│  │  │ test_ft_sae                  FT with SAE                   │     │    │
│  │  │ test_ft_reassoc_deadline     Reassociation deadline        │     │    │
│  │  │ test_ft_key_lifetime         Key lifetime                  │     │    │
│  │  │ test_ft_r0kh_r1kh            R0KH/R1KH communication       │     │    │
│  │  │ test_ft_pmk_r0_push          PMK-R0 push                   │     │    │
│  │  │ test_ft_pmk_r1_pull          PMK-R1 pull                   │     │    │
│  │  │ test_ft_roam_time            Roam time measurement         │     │    │
│  │  └────────────────────────────────────────────────────────────┘     │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  OKC Tests:                                                                  │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  Test File: OkcTest.py                                              │    │
│  │  ┌────────────────────────────────────────────────────────────┐     │    │
│  │  │ Test Case                    Description                   │     │    │
│  │  │ ─────────                    ───────────                   │     │    │
│  │  │ test_okc_roam                OKC roaming                   │     │    │
│  │  │ test_okc_pmk_sync            PMK synchronization           │     │    │
│  │  │ test_okc_cache_timeout       Cache timeout                 │     │    │
│  │  │ test_okc_multi_ap            Multi-AP OKC                  │     │    │
│  │  │ test_okc_with_ft             OKC with FT fallback          │     │    │
│  │  └────────────────────────────────────────────────────────────┘     │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  PMK Cache Sync Tests:                                                       │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  Test File: PMKCacheSyncTest.py                                     │    │
│  │  ┌────────────────────────────────────────────────────────────┐     │    │
│  │  │ Test Case                    Description                   │     │    │
│  │  │ ─────────                    ───────────                   │     │    │
│  │  │ test_pmk_sync_l2             PMK sync via L2 broadcast     │     │    │
│  │  │ test_pmk_sync_rf_domain      PMK sync via RF domain        │     │    │
│  │  │ test_pmk_sync_zmq            PMK sync via ZeroMQ           │     │    │
│  │  │ test_pmk_cache_size          Cache size limits             │     │    │
│  │  │ test_pmk_cache_eviction      Cache eviction policy         │     │    │
│  │  └────────────────────────────────────────────────────────────┘     │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  802.11k/v Tests:                                                            │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  Test File: RrmBtmTest.py                                           │    │
│  │  ┌────────────────────────────────────────────────────────────┐     │    │
│  │  │ Test Case                    Description                   │     │    │
│  │  │ ─────────                    ───────────                   │     │    │
│  │  │ test_neighbor_report         Neighbor report request       │     │    │
│  │  │ test_beacon_report           Beacon measurement report     │     │    │
│  │  │ test_btm_request             BSS transition request        │     │    │
│  │  │ test_btm_response            BSS transition response       │     │    │
│  │  │ test_btm_disassoc_imminent   Disassociation imminent       │     │    │
│  │  │ test_btm_abridged            Abridged neighbor list        │     │    │
│  │  │ test_btm_candidate_list      Candidate list preference     │     │    │
│  │  └────────────────────────────────────────────────────────────┘     │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### AI.3 RADIUS Tests

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    RADIUS TEST CASES                                         │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  RADIUS Authentication Tests:                                                │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  Test File: RadiusAuthTest.py                                       │    │
│  │  ┌────────────────────────────────────────────────────────────┐     │    │
│  │  │ Test Case                    Description                   │     │    │
│  │  │ ─────────                    ───────────                   │     │    │
│  │  │ test_radius_auth_accept      Access-Accept handling        │     │    │
│  │  │ test_radius_auth_reject      Access-Reject handling        │     │    │
│  │  │ test_radius_auth_challenge   Access-Challenge handling     │     │    │
│  │  │ test_radius_retransmit       Retransmission                │     │    │
│  │  │ test_radius_timeout          Timeout handling              │     │    │
│  │  │ test_radius_failover         Server failover               │     │    │
│  │  │ test_radius_dead_time        Dead time recovery            │     │    │
│  │  │ test_radius_shared_secret    Shared secret validation      │     │    │
│  │  └────────────────────────────────────────────────────────────┘     │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  RADIUS Accounting Tests:                                                    │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  Test File: RadiusAcctServerTest.py                                 │    │
│  │  ┌────────────────────────────────────────────────────────────┐     │    │
│  │  │ Test Case                    Description                   │     │    │
│  │  │ ─────────                    ───────────                   │     │    │
│  │  │ test_acct_start              Accounting-Start              │     │    │
│  │  │ test_acct_stop               Accounting-Stop               │     │    │
│  │  │ test_acct_interim            Interim-Update                │     │    │
│  │  │ test_acct_on_off             Accounting-On/Off             │     │    │
│  │  │ test_acct_session_id         Session ID generation         │     │    │
│  │  │ test_acct_input_output       Input/Output octets           │     │    │
│  │  │ test_acct_session_time       Session time tracking         │     │    │
│  │  │ test_acct_terminate_cause    Terminate cause codes         │     │    │
│  │  └────────────────────────────────────────────────────────────┘     │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  RADIUS CoA/DM Tests:                                                        │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  Test File: RadiusBwCoaTest.py                                      │    │
│  │  ┌────────────────────────────────────────────────────────────┐     │    │
│  │  │ Test Case                    Description                   │     │    │
│  │  │ ─────────                    ───────────                   │     │    │
│  │  │ test_coa_bandwidth           Bandwidth modification        │     │    │
│  │  │ test_coa_vlan                VLAN change                   │     │    │
│  │  │ test_coa_session_timeout     Session timeout change        │     │    │
│  │  │ test_coa_acl                 ACL modification              │     │    │
│  │  │ test_dm_disconnect           Disconnect-Request            │     │    │
│  │  │ test_dm_session_id           Session ID matching           │     │    │
│  │  │ test_dm_user_name            User-Name matching            │     │    │
│  │  │ test_coa_nak                 CoA-NAK handling              │     │    │
│  │  └────────────────────────────────────────────────────────────┘     │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  RadSec Tests:                                                               │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  Test File: RadsecproxyTest.py                                      │    │
│  │  ┌────────────────────────────────────────────────────────────┐     │    │
│  │  │ Test Case                    Description                   │     │    │
│  │  │ ─────────                    ───────────                   │     │    │
│  │  │ test_radsec_tls              RadSec TLS connection         │     │    │
│  │  │ test_radsec_cert_verify      Certificate verification      │     │    │
│  │  │ test_radsec_crl              CRL checking                  │     │    │
│  │  │ test_radsec_ocsp             OCSP checking                 │     │    │
│  │  │ test_radsec_reconnect        Connection reconnection       │     │    │
│  │  │ test_radsec_failover         Server failover               │     │    │
│  │  └────────────────────────────────────────────────────────────┘     │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  RADIUS Pooling Tests:                                                       │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  Test File: RadiusPoolingTest.py                                    │    │
│  │  ┌────────────────────────────────────────────────────────────┐     │    │
│  │  │ Test Case                    Description                   │     │    │
│  │  │ ─────────                    ───────────                   │     │    │
│  │  │ test_pool_round_robin        Round-robin load balancing    │     │    │
│  │  │ test_pool_failover           Pool failover                 │     │    │
│  │  │ test_pool_priority           Priority-based selection      │     │    │
│  │  │ test_pool_health_check       Server health checking        │     │    │
│  │  └────────────────────────────────────────────────────────────┘     │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### AI.4 DFS Tests

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    DFS TEST CASES                                            │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  DFS Operation Tests:                                                        │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  Test File: DfsTest.py                                              │    │
│  │  ┌────────────────────────────────────────────────────────────┐     │    │
│  │  │ Test Case                    Description                   │     │    │
│  │  │ ─────────                    ───────────                   │     │    │
│  │  │ test_cac_start               CAC initiation                │     │    │
│  │  │ test_cac_complete            CAC completion                │     │    │
│  │  │ test_radar_detection         Radar detection               │     │    │
│  │  │ test_channel_switch          Channel switch announcement   │     │    │
│  │  │ test_nol_management          NOL list management           │     │    │
│  │  │ test_nol_timeout             NOL timeout (30 min)          │     │    │
│  │  │ test_cac_timeout             CAC timeout (60s/600s)        │     │    │
│  │  │ test_off_channel_cac         Off-channel CAC               │     │    │
│  │  │ test_background_cac          Background CAC                │     │    │
│  │  └────────────────────────────────────────────────────────────┘     │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  DFS Information Sharing Tests:                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  Test File: ApDfsInfoSharingTest.py                                 │    │
│  │  ┌────────────────────────────────────────────────────────────┐     │    │
│  │  │ Test Case                    Description                   │     │    │
│  │  │ ─────────                    ───────────                   │     │    │
│  │  │ test_dfs_sync_l2             DFS sync via L2 broadcast     │     │    │
│  │  │ test_dfs_sync_rf_domain      DFS sync via RF domain        │     │    │
│  │  │ test_dfs_nol_sync            NOL synchronization           │     │    │
│  │  │ test_dfs_radar_notify        Radar detection notification  │     │    │
│  │  │ test_dfs_channel_avoidance   Channel avoidance             │     │    │
│  │  └────────────────────────────────────────────────────────────┘     │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### AI.5 Hotspot 2.0 Tests

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    HOTSPOT 2.0 TEST CASES                                    │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  Hotspot 2.0 Tests:                                                          │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  Test File: Hotspot2Test.py                                         │    │
│  │  ┌────────────────────────────────────────────────────────────┐     │    │
│  │  │ Test Case                    Description                   │     │    │
│  │  │ ─────────                    ───────────                   │     │    │
│  │  │ test_hs20_indication         HS2.0 indication element      │     │    │
│  │  │ test_interworking_ie         Interworking IE               │     │    │
│  │  │ test_roaming_consortium      Roaming consortium IE         │     │    │
│  │  │ test_gas_request             GAS initial request           │     │    │
│  │  │ test_gas_response            GAS initial response          │     │    │
│  │  │ test_gas_comeback            GAS comeback request          │     │    │
│  │  │ test_anqp_capability         ANQP capability list          │     │    │
│  │  │ test_anqp_venue_name         ANQP venue name               │     │    │
│  │  │ test_anqp_network_auth       ANQP network auth type        │     │    │
│  │  │ test_anqp_roaming_consortium ANQP roaming consortium       │     │    │
│  │  │ test_anqp_nai_realm          ANQP NAI realm                │     │    │
│  │  │ test_anqp_3gpp_cellular      ANQP 3GPP cellular            │     │    │
│  │  │ test_anqp_domain_name        ANQP domain name              │     │    │
│  │  │ test_hs20_operator_name      HS2.0 operator name           │     │    │
│  │  │ test_hs20_wan_metrics        HS2.0 WAN metrics             │     │    │
│  │  │ test_hs20_connection_cap     HS2.0 connection capability   │     │    │
│  │  │ test_hs20_osu_providers      HS2.0 OSU providers           │     │    │
│  │  │ test_hs20_icon               HS2.0 icon request            │     │    │
│  │  └────────────────────────────────────────────────────────────┘     │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

