## Troubleshooting Connection Issues

### 12.1 Common Connection Failures

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    COMMON CONNECTION FAILURES                                │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  Phase 1: Discovery Failures                                                 │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │ Symptom: Network not visible                                        │    │
│  │ Causes:                                                              │    │
│  │   • SSID hidden and not in client's preferred list                 │    │
│  │   • Channel not supported by client (e.g., DFS channels)           │    │
│  │   • Regulatory domain mismatch                                      │    │
│  │   • AP not broadcasting (radio disabled)                            │    │
│  │   • Client too far from AP (weak signal)                            │    │
│  │ Debug:                                                               │    │
│  │   • Check beacon transmission: iw dev wlan0 scan                    │    │
│  │   • Verify channel: iw dev wlan0 info                               │    │
│  │   • Check regulatory: iw reg get                                    │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  Phase 3: Authentication Failures                                            │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │ Symptom: "Authentication failed" or timeout                         │    │
│  │ Causes:                                                              │    │
│  │   • Wrong password (PSK mismatch)                                   │    │
│  │   • SAE anti-clogging token required                                │    │
│  │   • MAC filtering enabled                                           │    │
│  │   • Maximum client limit reached                                    │    │
│  │   • Client blacklisted                                              │    │
│  │ Debug:                                                               │    │
│  │   • Check hostapd logs: journalctl -u hostapd                       │    │
│  │   • Verify PSK: hostapd_cli get_config                              │    │
│  │   • Check MAC filter: hostapd_cli accept_acl / deny_acl             │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  Phase 4: Association Failures                                               │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │ Symptom: "Association failed" with status code                      │    │
│  │ Common Status Codes:                                                 │    │
│  │   • 12: Association denied (not in same BSS)                        │    │
│  │   • 17: Association denied (AP unable to handle)                    │    │
│  │   • 18: Association denied (outside supported rates)                │    │
│  │   • 34: Association denied (RSNE mismatch)                          │    │
│  │   • 37: Association denied (MFP required)                           │    │
│  │ Debug:                                                               │    │
│  │   • Check capabilities: iw phy phy0 info                            │    │
│  │   • Verify RSN IE match                                             │    │
│  │   • Check MFP settings                                              │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  Phase 5: 4-Way Handshake Failures                                           │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │ Symptom: "4-way handshake timeout" or "MIC failure"                 │    │
│  │ Causes:                                                              │    │
│  │   • PSK mismatch (most common)                                      │    │
│  │   • EAPOL frame loss (poor signal)                                  │    │
│  │   • Replay counter mismatch                                         │    │
│  │   • Clock skew (for time-based protocols)                           │    │
│  │   • Driver/firmware bugs                                            │    │
│  │ Debug:                                                               │    │
│  │   • Enable WPA debug: hostapd -dd                                   │    │
│  │   • Check EAPOL frames: tcpdump -i wlan0 ether proto 0x888e         │    │
│  │   • Verify PSK derivation                                           │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  Phase 6: DHCP Failures                                                      │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │ Symptom: "Connected, no internet" or 169.254.x.x address            │    │
│  │ Causes:                                                              │    │
│  │   • DHCP server not running                                         │    │
│  │   • DHCP pool exhausted                                             │    │
│  │   • VLAN misconfiguration                                           │    │
│  │   • Firewall blocking DHCP                                          │    │
│  │   • Client isolation enabled                                        │    │
│  │ Debug:                                                               │    │
│  │   • Check DHCP server: systemctl status dnsmasq                     │    │
│  │   • Monitor DHCP: tcpdump -i br0 port 67 or port 68                 │    │
│  │   • Check leases: cat /var/lib/misc/dnsmasq.leases                  │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  Enterprise (802.1X) Failures                                                │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │ Symptom: "EAP authentication failed"                                │    │
│  │ Causes:                                                              │    │
│  │   • RADIUS server unreachable                                       │    │
│  │   • Wrong RADIUS shared secret                                      │    │
│  │   • Certificate issues (expired, untrusted CA)                      │    │
│  │   • EAP method mismatch                                             │    │
│  │   • User credentials incorrect                                      │    │
│  │ Debug:                                                               │    │
│  │   • Check RADIUS connectivity: radtest user pass server 0 secret   │    │
│  │   • Verify certificates: openssl verify -CAfile ca.pem server.pem  │    │
│  │   • Check RADIUS logs: tail -f /var/log/freeradius/radius.log      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 12.2 Debug Commands

```bash
# hostapd control interface commands
hostapd_cli -i wlan0 status           # AP status
hostapd_cli -i wlan0 all_sta          # List all connected stations
hostapd_cli -i wlan0 sta <MAC>        # Station details
hostapd_cli -i wlan0 get_config       # Current configuration
hostapd_cli -i wlan0 log_level DEBUG  # Enable debug logging

# Wireless interface commands
iw dev wlan0 info                     # Interface info
iw dev wlan0 station dump             # Connected stations
iw dev wlan0 survey dump              # Channel survey
iw phy phy0 info                      # PHY capabilities
iw reg get                            # Regulatory domain

# Packet capture
tcpdump -i wlan0 -w capture.pcap      # Capture all traffic
tcpdump -i wlan0 ether proto 0x888e   # EAPOL frames only
tcpdump -i wlan0 type mgt             # Management frames only

# RADIUS debugging
radtest user password localhost 0 testing123
eapol_test -c eap.conf -s testing123 -a 127.0.0.1

# System logs
journalctl -u hostapd -f              # hostapd logs
journalctl -u wpa_supplicant -f       # wpa_supplicant logs
dmesg | grep -i wifi                  # Kernel WiFi messages
```

### 12.3 Status Codes Reference

| Code | Name | Description |
|------|------|-------------|
| 0 | SUCCESS | Successful |
| 1 | UNSPECIFIED_FAILURE | Unspecified failure |
| 10 | CAPS_UNSUPPORTED | Cannot support all capabilities |
| 11 | REASSOC_NO_ASSOC | Reassociation denied (not associated) |
| 12 | ASSOC_DENIED_UNSPEC | Association denied for unspecified reason |
| 13 | NOT_SUPPORTED_AUTH_ALG | Auth algorithm not supported |
| 14 | UNKNOWN_AUTH_TRANSACTION | Unknown auth transaction sequence |
| 15 | CHALLENGE_FAIL | Challenge failure |
| 16 | AUTH_TIMEOUT | Auth timeout |
| 17 | AP_UNABLE_TO_HANDLE | AP unable to handle new STA |
| 18 | ASSOC_DENIED_RATES | Association denied (rates) |
| 19 | ASSOC_DENIED_NOSHORT | Association denied (no short preamble) |
| 34 | INVALID_RSN_IE_CAP | Invalid RSN IE capabilities |
| 37 | ROBUST_MGMT_FRAME_POLICY_VIOLATION | MFP policy violation |
| 38 | UNSPECIFIED_QOS_FAILURE | Unspecified QoS failure |
| 39 | DENIED_INSUFFICIENT_BANDWIDTH | Insufficient bandwidth |
| 40 | INVALID_PARAMETERS | Invalid parameters |
| 46 | INVALID_FT_ACTION_FRAME_COUNT | Invalid FT action frame count |
| 47 | INVALID_PMKID | Invalid PMKID |
| 48 | INVALID_MDE | Invalid MDE |
| 49 | INVALID_FTE | Invalid FTE |
| 53 | INVALID_RSNIE | Invalid RSNIE |
| 77 | DENIED_HE_NOT_SUPPORTED | HE not supported |

### 12.4 Reason Codes Reference

| Code | Name | Description |
|------|------|-------------|
| 1 | UNSPECIFIED | Unspecified reason |
| 2 | PREV_AUTH_NOT_VALID | Previous authentication no longer valid |
| 3 | DEAUTH_LEAVING | Deauthenticated because STA is leaving |
| 4 | DISASSOC_DUE_TO_INACTIVITY | Disassociated due to inactivity |
| 5 | DISASSOC_AP_BUSY | Disassociated (AP unable to handle) |
| 6 | CLASS2_FRAME_FROM_NONAUTH_STA | Class 2 frame from non-authenticated STA |
| 7 | CLASS3_FRAME_FROM_NONASSOC_STA | Class 3 frame from non-associated STA |
| 8 | DISASSOC_STA_HAS_LEFT | Disassociated (STA has left BSS) |
| 14 | MICHAEL_MIC_FAILURE | MIC failure |
| 15 | 4WAY_HANDSHAKE_TIMEOUT | 4-way handshake timeout |
| 16 | GROUP_KEY_UPDATE_TIMEOUT | Group key update timeout |
| 17 | IE_IN_4WAY_DIFFERS | IE in 4-way handshake different |
| 18 | GROUP_CIPHER_NOT_VALID | Group cipher not valid |
| 19 | PAIRWISE_CIPHER_NOT_VALID | Pairwise cipher not valid |
| 20 | AKMP_NOT_VALID | AKMP not valid |
| 21 | UNSUPPORTED_RSN_IE_VERSION | Unsupported RSN IE version |
| 22 | INVALID_RSN_IE_CAPAB | Invalid RSN IE capabilities |
| 23 | IEEE_802_1X_AUTH_FAILED | 802.1X authentication failed |
| 24 | CIPHER_SUITE_REJECTED | Cipher suite rejected |
| 34 | DISASSOC_LOW_ACK | Disassociated due to low ACK |

---

