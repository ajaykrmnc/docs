## Appendix AA: Security Attack Vectors and Mitigations

### AA.1 Common WiFi Attacks

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    WIFI SECURITY ATTACK VECTORS                              │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  1. DEAUTHENTICATION ATTACK                                                  │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  Attack Flow:                                                        │    │
│  │  ┌─────────┐                                                        │    │
│  │  │ Attacker│                                                        │    │
│  │  └────┬────┘                                                        │    │
│  │       │ Spoofed Deauth (AP MAC → Client)                            │    │
│  │       ▼                                                              │    │
│  │  ┌─────────┐         ┌─────────┐                                    │    │
│  │  │ Client  │ ◄─────► │   AP    │                                    │    │
│  │  └─────────┘         └─────────┘                                    │    │
│  │       │                                                              │    │
│  │       ▼                                                              │    │
│  │  Client disconnects, must reconnect                                 │    │
│  │                                                                      │    │
│  │  Impact:                                                             │    │
│  │  • Denial of Service                                                 │    │
│  │  • Force reconnection (capture handshake)                           │    │
│  │  • Disrupt VoIP/video calls                                         │    │
│  │                                                                      │    │
│  │  Mitigation:                                                         │    │
│  │  • 802.11w (MFP) - Protected Management Frames                      │    │
│  │  • WPA3 requires MFP                                                 │    │
│  │  • Detect anomalous deauth rates                                    │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  2. EVIL TWIN ATTACK                                                         │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  Attack Flow:                                                        │    │
│  │  ┌─────────────┐                                                    │    │
│  │  │ Evil Twin AP│ (Same SSID, stronger signal)                       │    │
│  │  └──────┬──────┘                                                    │    │
│  │         │                                                            │    │
│  │         ▼                                                            │    │
│  │  ┌─────────┐         ┌─────────┐                                    │    │
│  │  │ Client  │ ──X──── │ Real AP │                                    │    │
│  │  └─────────┘         └─────────┘                                    │    │
│  │         │                                                            │    │
│  │         ▼                                                            │    │
│  │  Client connects to attacker                                        │    │
│  │                                                                      │    │
│  │  Impact:                                                             │    │
│  │  • Man-in-the-middle                                                 │    │
│  │  • Credential theft                                                  │    │
│  │  • Traffic interception                                              │    │
│  │                                                                      │    │
│  │  Mitigation:                                                         │    │
│  │  • WPA2/WPA3-Enterprise with server certificate validation          │    │
│  │  • Hotspot 2.0 with proper realm configuration                      │    │
│  │  • WIDS/WIPS detection                                               │    │
│  │  • Client certificate authentication (EAP-TLS)                      │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  3. KRACK (Key Reinstallation Attack)                                        │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  Attack Flow:                                                        │    │
│  │  ┌─────────┐         ┌─────────┐         ┌─────────┐               │    │
│  │  │ Client  │ ◄─────► │ Attacker│ ◄─────► │   AP    │               │    │
│  │  └─────────┘         └─────────┘         └─────────┘               │    │
│  │       │                   │                   │                      │    │
│  │       │ M1 ◄──────────────┼───────────────────│                      │    │
│  │       │ M2 ───────────────┼──────────────────►│                      │    │
│  │       │ M3 ◄──────────────┼───────────────────│                      │    │
│  │       │ M3 ◄──────────────┼───────────────────│ (Replayed)          │    │
│  │       │ M4 ───────────────┼──────────────────►│                      │    │
│  │       │                   │                   │                      │    │
│  │       ▼                   │                   │                      │    │
│  │  Key reinstalled, nonce reused                                      │    │
│  │                                                                      │    │
│  │  Impact:                                                             │    │
│  │  • Decrypt traffic                                                   │    │
│  │  • Inject packets                                                    │    │
│  │  • Forge packets                                                     │    │
│  │                                                                      │    │
│  │  Mitigation:                                                         │    │
│  │  • Patched hostapd/wpa_supplicant                                   │    │
│  │  • Don't reinstall already-in-use keys                              │    │
│  │  • WPA3 with updated handshake                                      │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  4. PMKID ATTACK                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  Attack Flow:                                                        │    │
│  │  ┌─────────┐                                                        │    │
│  │  │ Attacker│                                                        │    │
│  │  └────┬────┘                                                        │    │
│  │       │ Association Request                                          │    │
│  │       ▼                                                              │    │
│  │  ┌─────────┐                                                        │    │
│  │  │   AP    │ ──► EAPOL M1 with PMKID                                │    │
│  │  └─────────┘                                                        │    │
│  │       │                                                              │    │
│  │       ▼                                                              │    │
│  │  PMKID = HMAC-SHA1-128(PMK, "PMK Name" || AA || SPA)                │    │
│  │  Offline dictionary attack on PMKID                                 │    │
│  │                                                                      │    │
│  │  Impact:                                                             │    │
│  │  • Offline password cracking                                         │    │
│  │  • No client needed                                                  │    │
│  │  • Single packet capture sufficient                                  │    │
│  │                                                                      │    │
│  │  Mitigation:                                                         │    │
│  │  • Strong passwords (>12 chars, mixed)                              │    │
│  │  • WPA3-SAE (no PMKID in first message)                             │    │
│  │  • Disable PMKID in hostapd (disable_pmksa_caching=1)               │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  5. DICTIONARY/BRUTE FORCE ATTACK                                            │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  Attack Flow:                                                        │    │
│  │  1. Capture 4-way handshake                                         │    │
│  │  2. Extract ANonce, SNonce, MACs, MIC                               │    │
│  │  3. For each password guess:                                        │    │
│  │     a. PMK = PBKDF2(password, SSID, 4096, 256)                      │    │
│  │     b. PTK = PRF(PMK, ANonce, SNonce, AA, SPA)                      │    │
│  │     c. MIC' = HMAC-SHA1(KCK, M2)                                    │    │
│  │     d. If MIC' == MIC: password found                               │    │
│  │                                                                      │    │
│  │  Tools:                                                              │    │
│  │  • Hashcat (GPU-accelerated)                                        │    │
│  │  • Aircrack-ng                                                       │    │
│  │  • John the Ripper                                                   │    │
│  │                                                                      │    │
│  │  Mitigation:                                                         │    │
│  │  • Strong passwords (entropy > 80 bits)                             │    │
│  │  • WPA3-SAE (resistant to offline attacks)                          │    │
│  │  • Rate limiting on authentication                                   │    │
│  │  • Account lockout                                                   │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  6. DRAGONBLOOD (WPA3-SAE Attacks)                                           │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  Timing Side-Channel:                                                │    │
│  │  • Measure time for SAE Commit processing                           │    │
│  │  • Leak information about password                                  │    │
│  │                                                                      │    │
│  │  Cache Side-Channel:                                                 │    │
│  │  • Monitor CPU cache during SAE                                     │    │
│  │  • Extract password bits                                            │    │
│  │                                                                      │    │
│  │  Downgrade Attack:                                                   │    │
│  │  • Force WPA2 instead of WPA3                                       │    │
│  │  • Attack weaker protocol                                           │    │
│  │                                                                      │    │
│  │  Mitigation:                                                         │    │
│  │  • Patched implementations                                          │    │
│  │  • Constant-time operations                                         │    │
│  │  • Disable WPA2 fallback (WPA3-only mode)                           │    │
│  │  • Anti-clogging tokens                                             │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### AA.2 Security Best Practices

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    SECURITY BEST PRACTICES                                   │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  Network Configuration:                                                      │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │  ✓ Use WPA3-SAE for personal networks                               │    │
│  │  ✓ Use WPA3-Enterprise with EAP-TLS for corporate                   │    │
│  │  ✓ Enable 802.11w (MFP) - required for WPA3                         │    │
│  │  ✓ Disable legacy protocols (WEP, WPA-TKIP)                         │    │
│  │  ✓ Use strong, unique passwords (>16 characters)                    │    │
│  │  ✓ Change default SSID (avoid common names)                         │    │
│  │  ✓ Disable WPS (vulnerable to brute force)                          │    │
│  │  ✓ Enable client isolation on guest networks                        │    │
│  │  ✓ Use separate VLANs for different user groups                     │    │
│  │  ✓ Implement proper firewall rules                                  │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  RADIUS/Enterprise:                                                          │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │  ✓ Use RadSec (RADIUS over TLS) for server communication           │    │
│  │  ✓ Validate server certificates on clients                         │    │
│  │  ✓ Use client certificates (EAP-TLS) when possible                  │    │
│  │  ✓ Implement certificate revocation (CRL/OCSP)                      │    │
│  │  ✓ Use strong RADIUS shared secrets                                 │    │
│  │  ✓ Enable accounting for audit trail                                │    │
│  │  ✓ Implement CoA for dynamic policy changes                         │    │
│  │  ✓ Configure proper session timeouts                                │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  Monitoring:                                                                 │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │  ✓ Deploy WIDS/WIPS for rogue AP detection                         │    │
│  │  ✓ Monitor for deauthentication floods                              │    │
│  │  ✓ Alert on authentication failures                                 │    │
│  │  ✓ Log all client connections/disconnections                        │    │
│  │  ✓ Monitor for evil twin APs                                        │    │
│  │  ✓ Track client roaming patterns                                    │    │
│  │  ✓ Analyze RF spectrum for interference                             │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  Client Configuration:                                                       │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │  ✓ Disable auto-connect to open networks                            │    │
│  │  ✓ Validate server certificates for Enterprise                      │    │
│  │  ✓ Use VPN on untrusted networks                                    │    │
│  │  ✓ Keep client software updated                                     │    │
│  │  ✓ Disable WiFi when not in use                                     │    │
│  │  ✓ Forget networks no longer used                                   │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Appendix AB: Performance Optimization

### AB.1 Throughput Optimization

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    THROUGHPUT OPTIMIZATION                                   │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  Channel Width Selection:                                                    │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  Environment          Recommended Width    Reason                   │    │
│  │  ───────────          ─────────────────    ──────                   │    │
│  │  Dense urban          20 MHz               Less interference        │    │
│  │  Office               40 MHz               Balance                  │    │
│  │  Suburban home        80 MHz               Good throughput          │    │
│  │  Rural/isolated       160/320 MHz          Maximum throughput       │    │
│  │                                                                      │    │
│  │  Note: Wider channels = more throughput but more interference       │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  MCS Rate Selection:                                                         │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  • Enable all MCS rates for auto-selection                          │    │
│  │  • Disable low rates (1, 2, 5.5, 6 Mbps) to reduce airtime          │    │
│  │  • Set minimum rate based on coverage requirements                  │    │
│  │                                                                      │    │
│  │  hostapd configuration:                                              │    │
│  │  supported_rates=12 18 24 36 48 54                                  │    │
│  │  basic_rates=12 24                                                   │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  Aggregation Settings:                                                       │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  A-MPDU (Aggregate MAC Protocol Data Unit):                         │    │
│  │  • Combine multiple frames into single transmission                 │    │
│  │  • Reduces overhead significantly                                   │    │
│  │  • Max A-MPDU length: 65535 bytes (HT), 1048575 bytes (VHT/HE)     │    │
│  │                                                                      │    │
│  │  A-MSDU (Aggregate MAC Service Data Unit):                          │    │
│  │  • Combine multiple MSDUs into single MPDU                          │    │
│  │  • Max A-MSDU length: 3839, 7935, or 11454 bytes                   │    │
│  │                                                                      │    │
│  │  Recommendation:                                                     │    │
│  │  • Enable A-MPDU for all traffic                                    │    │
│  │  • Enable A-MSDU for bulk transfers                                 │    │
│  │  • Disable A-MSDU for latency-sensitive traffic                     │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  MIMO Configuration:                                                         │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  Spatial Streams:                                                    │    │
│  │  • 1SS: Basic, single antenna                                       │    │
│  │  • 2SS: 2x throughput, requires 2 antennas                          │    │
│  │  • 3SS: 3x throughput, requires 3 antennas                          │    │
│  │  • 4SS: 4x throughput, requires 4 antennas                          │    │
│  │  • 8SS: 8x throughput (802.11ax/be)                                 │    │
│  │                                                                      │    │
│  │  MU-MIMO:                                                            │    │
│  │  • Downlink MU-MIMO: Transmit to multiple clients simultaneously    │    │
│  │  • Uplink MU-MIMO: Receive from multiple clients (802.11ax)         │    │
│  │  • Requires capable clients                                         │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### AB.2 Latency Optimization

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    LATENCY OPTIMIZATION                                      │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  QoS Configuration (WMM):                                                    │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  Access Category   Priority   Typical Traffic                       │    │
│  │  ───────────────   ────────   ───────────────                       │    │
│  │  AC_VO (Voice)     Highest    VoIP, video calls                     │    │
│  │  AC_VI (Video)     High       Video streaming                       │    │
│  │  AC_BE (Best Eff)  Medium     Web, email                            │    │
│  │  AC_BK (Background) Low       Backups, updates                      │    │
│  │                                                                      │    │
│  │  EDCA Parameters (example for low latency):                         │    │
│  │  wmm_ac_vo_cwmin=2                                                   │    │
│  │  wmm_ac_vo_cwmax=3                                                   │    │
│  │  wmm_ac_vo_aifs=2                                                    │    │
│  │  wmm_ac_vo_txop_limit=47                                             │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  OFDMA (802.11ax):                                                           │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  • Divide channel into Resource Units (RUs)                         │    │
│  │  • Serve multiple clients simultaneously                            │    │
│  │  • Reduces wait time for small packets                              │    │
│  │  • Especially beneficial for IoT devices                            │    │
│  │                                                                      │    │
│  │  RU Sizes (20 MHz channel):                                         │    │
│  │  ┌─────────────────────────────────────────────────────────────┐    │    │
│  │  │  26-tone RU  │  52-tone RU  │  106-tone RU │  242-tone RU  │    │    │
│  │  │  (2 MHz)     │  (4 MHz)     │  (8 MHz)     │  (20 MHz)     │    │    │
│  │  │  9 per 20MHz │  4 per 20MHz │  2 per 20MHz │  1 per 20MHz  │    │    │
│  │  └─────────────────────────────────────────────────────────────┘    │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  Target Wake Time (TWT):                                                     │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  • Schedule specific wake times for clients                         │    │
│  │  • Reduces contention during wake periods                           │    │
│  │  • Predictable latency for scheduled traffic                        │    │
│  │  • Ideal for IoT sensors with periodic data                         │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  BSS Coloring (802.11ax):                                                    │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  • Assign color (1-63) to each BSS                                  │    │
│  │  • Ignore frames from different-colored BSSs                        │    │
│  │  • Reduces unnecessary deferrals                                    │    │
│  │  • Improves spatial reuse                                           │    │
│  │                                                                      │    │
│  │  hostapd configuration:                                              │    │
│  │  he_bss_color=42                                                     │    │
│  │  he_bss_color_partial=0                                              │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### AB.3 Roaming Optimization

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    ROAMING OPTIMIZATION                                      │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  Fast Transition (802.11r):                                                  │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  Without FT:                                                         │    │
│  │  ┌─────────────────────────────────────────────────────────────┐    │    │
│  │  │ Scan → Auth → Assoc → 802.1X → 4-Way HS → Connected         │    │    │
│  │  │                       ~2-5 seconds                           │    │    │
│  │  └─────────────────────────────────────────────────────────────┘    │    │
│  │                                                                      │    │
│  │  With FT Over-the-Air:                                               │    │
│  │  ┌─────────────────────────────────────────────────────────────┐    │    │
│  │  │ FT Auth → FT Reassoc → Connected                            │    │    │
│  │  │           ~50-100 ms                                         │    │    │
│  │  └─────────────────────────────────────────────────────────────┘    │    │
│  │                                                                      │    │
│  │  With FT Over-the-DS:                                                │    │
│  │  ┌─────────────────────────────────────────────────────────────┐    │    │
│  │  │ FT Action (via current AP) → Reassoc → Connected            │    │    │
│  │  │           ~30-50 ms                                          │    │    │
│  │  └─────────────────────────────────────────────────────────────┘    │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  OKC (Opportunistic Key Caching):                                            │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  • Cache PMK across APs in same mobility domain                     │    │
│  │  • Skip 802.1X on roam                                              │    │
│  │  • Still requires 4-way handshake                                   │    │
│  │  • Roam time: ~200-500 ms                                           │    │
│  │                                                                      │    │
│  │  hostapd configuration:                                              │    │
│  │  okc=1                                                               │    │
│  │  pmk_r1_push=1                                                       │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  802.11k (Radio Resource Measurement):                                       │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  • AP provides neighbor report to client                            │    │
│  │  • Client knows where to roam without full scan                     │    │
│  │  • Reduces roam decision time                                       │    │
│  │                                                                      │    │
│  │  hostapd configuration:                                              │    │
│  │  rrm_neighbor_report=1                                               │    │
│  │  rrm_beacon_report=1                                                 │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  802.11v (BSS Transition Management):                                        │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  • AP can suggest/request client to roam                            │    │
│  │  • Load balancing across APs                                        │    │
│  │  • Proactive roaming before signal degrades                         │    │
│  │                                                                      │    │
│  │  hostapd configuration:                                              │    │
│  │  bss_transition=1                                                    │    │
│  │  wnm_sleep_mode=1                                                    │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

