## Appendix F: Security Analysis

### F.1 Attack Vectors and Mitigations

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    ATTACK VECTORS AND MITIGATIONS                            │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │ ATTACK: Evil Twin / Rogue AP                                        │    │
│  ├─────────────────────────────────────────────────────────────────────┤    │
│  │ Description:                                                         │    │
│  │   Attacker creates fake AP with same SSID to intercept traffic      │    │
│  │                                                                      │    │
│  │ Detection:                                                           │    │
│  │   • BSSID mismatch detection                                        │    │
│  │   • Certificate validation (802.1X)                                 │    │
│  │   • Hotspot 2.0 NAI realm verification                              │    │
│  │                                                                      │    │
│  │ Mitigation:                                                          │    │
│  │   • Use WPA2/WPA3-Enterprise with certificate validation            │    │
│  │   • Enable Hotspot 2.0 with proper credentials                      │    │
│  │   • Implement WIDS/WIPS for rogue AP detection                      │    │
│  │   • Use 802.11w (MFP) to prevent deauth attacks                     │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │ ATTACK: Deauthentication Attack                                     │    │
│  ├─────────────────────────────────────────────────────────────────────┤    │
│  │ Description:                                                         │    │
│  │   Attacker sends spoofed deauth frames to disconnect clients        │    │
│  │                                                                      │    │
│  │ Detection:                                                           │    │
│  │   • High rate of deauth frames                                      │    │
│  │   • Deauth from unexpected sources                                  │    │
│  │                                                                      │    │
│  │ Mitigation:                                                          │    │
│  │   • Enable 802.11w (MFP) - required for WPA3                        │    │
│  │   • Configure ieee80211w=2 (required) in hostapd                    │    │
│  │   • Use WPA3-SAE which mandates MFP                                 │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │ ATTACK: KRACK (Key Reinstallation Attack)                           │    │
│  ├─────────────────────────────────────────────────────────────────────┤    │
│  │ Description:                                                         │    │
│  │   Attacker forces nonce reuse in 4-way handshake                    │    │
│  │                                                                      │    │
│  │ Detection:                                                           │    │
│  │   • Duplicate EAPOL message 3 detection                             │    │
│  │   • Replay counter monitoring                                       │    │
│  │                                                                      │    │
│  │ Mitigation:                                                          │    │
│  │   • Update hostapd to patched version (2.6+)                        │    │
│  │   • Enable wpa_disable_eapol_key_retries=1                          │    │
│  │   • Use WPA3 which is not vulnerable                                │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │ ATTACK: PMKID Attack                                                │    │
│  ├─────────────────────────────────────────────────────────────────────┤    │
│  │ Description:                                                         │    │
│  │   Attacker captures PMKID from first EAPOL message for offline      │    │
│  │   dictionary attack                                                  │    │
│  │                                                                      │    │
│  │ Detection:                                                           │    │
│  │   • Cannot be detected (passive attack)                             │    │
│  │                                                                      │    │
│  │ Mitigation:                                                          │    │
│  │   • Use strong passphrases (20+ characters)                         │    │
│  │   • Use WPA3-SAE (resistant to offline attacks)                     │    │
│  │   • Disable PMKID in EAPOL message 1 if possible                    │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │ ATTACK: Dictionary/Brute Force Attack                               │    │
│  ├─────────────────────────────────────────────────────────────────────┤    │
│  │ Description:                                                         │    │
│  │   Attacker captures 4-way handshake and performs offline attack     │    │
│  │                                                                      │    │
│  │ Detection:                                                           │    │
│  │   • Cannot be detected (offline attack)                             │    │
│  │                                                                      │    │
│  │ Mitigation:                                                          │    │
│  │   • Use strong passphrases (20+ random characters)                  │    │
│  │   • Use WPA3-SAE (provides forward secrecy)                         │    │
│  │   • Use WPA2-Enterprise (no PSK to crack)                           │    │
│  │   • Rotate PSK regularly                                            │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │ ATTACK: Dragonblood (SAE Vulnerabilities)                           │    │
│  ├─────────────────────────────────────────────────────────────────────┤    │
│  │ Description:                                                         │    │
│  │   Side-channel attacks against SAE implementation                   │    │
│  │                                                                      │    │
│  │ Detection:                                                           │    │
│  │   • Timing analysis of SAE exchanges                                │    │
│  │                                                                      │    │
│  │ Mitigation:                                                          │    │
│  │   • Update to patched hostapd (2.9+)                                │    │
│  │   • Use SAE-H2E (Hash-to-Element) instead of H2C                    │    │
│  │   • Configure sae_pwe=2 (H2E only)                                  │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │ ATTACK: Captive Portal Bypass                                       │    │
│  ├─────────────────────────────────────────────────────────────────────┤    │
│  │ Description:                                                         │    │
│  │   Attacker bypasses captive portal using various techniques         │    │
│  │                                                                      │    │
│  │ Techniques:                                                          │    │
│  │   • MAC spoofing (clone authenticated client MAC)                   │    │
│  │   • DNS tunneling                                                   │    │
│  │   • ICMP tunneling                                                  │    │
│  │   • Exploiting walled garden                                        │    │
│  │                                                                      │    │
│  │ Mitigation:                                                          │    │
│  │   • Use RADIUS accounting for session tracking                      │    │
│  │   • Implement per-client rate limiting                              │    │
│  │   • Block tunneling protocols                                       │    │
│  │   • Minimize walled garden                                          │    │
│  │   • Use HTTPS portal with certificate validation                    │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### F.2 Security Best Practices

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                       SECURITY BEST PRACTICES                                │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  Authentication:                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │ ✓ Use WPA3-SAE for personal networks                               │    │
│  │ ✓ Use WPA3-Enterprise for corporate networks                       │    │
│  │ ✓ Enable WPA3-SAE Transition mode for compatibility                │    │
│  │ ✓ Use EAP-TLS with client certificates for highest security        │    │
│  │ ✓ Implement certificate pinning where possible                     │    │
│  │ ✓ Use strong passphrases (20+ characters, random)                  │    │
│  │ ✓ Rotate PSK regularly (quarterly minimum)                         │    │
│  │ ✗ Avoid WPA2-PSK with weak passwords                               │    │
│  │ ✗ Avoid WEP (completely broken)                                    │    │
│  │ ✗ Avoid WPA-TKIP (deprecated)                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  Encryption:                                                                 │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │ ✓ Use CCMP (AES) or GCMP for encryption                            │    │
│  │ ✓ Use CCMP-256 or GCMP-256 for Suite B                             │    │
│  │ ✓ Enable group key rotation (wpa_group_rekey=3600)                 │    │
│  │ ✓ Enable PTK rekeying for long sessions                            │    │
│  │ ✗ Avoid TKIP (deprecated, vulnerable)                              │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  Management Frame Protection:                                                │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │ ✓ Enable 802.11w (ieee80211w=2 for required)                       │    │
│  │ ✓ Use WPA3 which mandates MFP                                      │    │
│  │ ✓ Configure group_mgmt_cipher=AES-128-CMAC                         │    │
│  │ ✓ Use BIP-GMAC-256 for Suite B                                     │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  RADIUS:                                                                     │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │ ✓ Use RadSec (RADIUS over TLS) for secure transport                │    │
│  │ ✓ Use strong shared secrets (32+ random characters)                │    │
│  │ ✓ Enable RADIUS accounting for audit trail                         │    │
│  │ ✓ Implement RADIUS server redundancy                               │    │
│  │ ✓ Use certificate-based authentication for RadSec                  │    │
│  │ ✓ Enable CRL checking for certificate revocation                   │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  Network Isolation:                                                          │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │ ✓ Enable client isolation (ap_isolate=1)                           │    │
│  │ ✓ Use VLANs to segment traffic                                     │    │
│  │ ✓ Implement dynamic VLAN assignment via RADIUS                     │    │
│  │ ✓ Use separate SSIDs for guest and corporate                       │    │
│  │ ✓ Implement firewall rules between segments                        │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  Monitoring:                                                                 │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │ ✓ Enable WIDS/WIPS for intrusion detection                         │    │
│  │ ✓ Monitor for rogue APs                                            │    │
│  │ ✓ Log all authentication events                                    │    │
│  │ ✓ Alert on authentication failures                                 │    │
│  │ ✓ Monitor for deauth floods                                        │    │
│  │ ✓ Track client roaming patterns                                    │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

