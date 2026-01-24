## Roaming Between APs

When a client moves between access points, fast roaming mechanisms minimize connection interruption.

### 11.1 Roaming Decision

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         ROAMING DECISION PROCESS                             │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  Client monitors signal quality:                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │ • RSSI (Received Signal Strength Indicator)                         │    │
│  │ • SNR (Signal-to-Noise Ratio)                                       │    │
│  │ • Packet error rate                                                  │    │
│  │ • Retry rate                                                         │    │
│  │ • Data rate degradation                                              │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  Roaming triggers:                                                           │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │ • RSSI below threshold (typically -70 to -75 dBm)                   │    │
│  │ • Better AP available (RSSI difference > hysteresis)                │    │
│  │ • AP sends BSS Transition Management Request (802.11v)              │    │
│  │ • Current AP deauthenticates client                                 │    │
│  │ • Channel change required (DFS radar detection)                     │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  Signal Strength Timeline:                                                   │
│                                                                              │
│  RSSI                                                                        │
│   │                                                                          │
│   │ ─────────────────────────────────────────────────────────────────────   │
│   │ -50 dBm  ████████████                                                   │
│   │          ████████████                                                   │
│   │ -60 dBm  ████████████████████                                           │
│   │          ████████████████████                                           │
│   │ -70 dBm  ████████████████████████████  ← Roaming threshold              │
│   │          ████████████████████████████                                   │
│   │ -80 dBm  ████████████████████████████████████                           │
│   │          ████████████████████████████████████                           │
│   │ -90 dBm  ████████████████████████████████████████████                   │
│   │          ████████████████████████████████████████████                   │
│   └──────────────────────────────────────────────────────────────────────►  │
│              Time →                                                          │
│                                                                              │
│              ▲                              ▲                                │
│              │                              │                                │
│         Start scanning              Initiate roam                            │
│         for new APs                 to new AP                                │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 11.2 OKC (Opportunistic Key Caching)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    OKC (OPPORTUNISTIC KEY CACHING)                           │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  OKC allows fast roaming by caching PMK across APs in the same network.     │
│                                                                              │
│  Initial Connection (AP1):                                                   │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │ 1. Full 802.1X/EAP authentication                                   │    │
│  │ 2. Derive PMK from MSK                                              │    │
│  │ 3. Calculate PMKID = HMAC-SHA1-128(PMK, "PMK Name" || AA || SPA)   │    │
│  │ 4. Cache PMK with PMKID                                             │    │
│  │ 5. Sync PMK to other APs via IAPC                                   │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  Roaming to AP2:                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │ 1. Client sends Reassociation Request with PMKID                    │    │
│  │ 2. AP2 looks up PMK using PMKID                                     │    │
│  │ 3. Skip 802.1X - go directly to 4-Way Handshake                     │    │
│  │ 4. Derive new PTK using cached PMK                                  │    │
│  │ 5. Complete 4-Way Handshake                                         │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  OKC Flow Diagram:                                                           │
│                                                                              │
│  Client              AP1                AP2              RADIUS              │
│    │                  │                  │                  │                │
│    │  802.1X/EAP      │                  │                  │                │
│    │ ◄───────────────►│◄────────────────────────────────────►│               │
│    │                  │                  │                  │                │
│    │  4-Way Handshake │                  │                  │                │
│    │ ◄───────────────►│                  │                  │                │
│    │                  │                  │                  │                │
│    │                  │  PMK Sync (IAPC) │                  │                │
│    │                  │ ────────────────►│                  │                │
│    │                  │                  │                  │                │
│    │  ═══════════════════════════════════════════════════   │                │
│    │           CLIENT MOVES TO AP2 COVERAGE                  │                │
│    │  ═══════════════════════════════════════════════════   │                │
│    │                  │                  │                  │                │
│    │  Reassoc Req     │                  │                  │                │
│    │  (with PMKID)    │                  │                  │                │
│    │ ────────────────────────────────────►│                  │                │
│    │                  │                  │                  │                │
│    │                  │  ┌───────────────┤                  │                │
│    │                  │  │ Lookup PMK    │                  │                │
│    │                  │  │ by PMKID      │                  │                │
│    │                  │  │ (Found!)      │                  │                │
│    │                  │  └───────────────┤                  │                │
│    │                  │                  │                  │                │
│    │  Reassoc Resp    │                  │                  │                │
│    │ ◄────────────────────────────────────│                  │                │
│    │                  │                  │                  │                │
│    │  4-Way Handshake │                  │                  │                │
│    │ ◄───────────────────────────────────►│                  │                │
│    │                  │                  │                  │                │
│    │  ═══════════════════════════════════════════════════   │                │
│    │           ROAMING COMPLETE (~50ms)                      │                │
│    │  ═══════════════════════════════════════════════════   │                │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 11.3 802.11r Fast BSS Transition (FT)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    802.11r FAST BSS TRANSITION (FT)                          │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  FT Key Hierarchy:                                                           │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │                          MSK (Master Session Key)                    │    │
│  │                                   │                                  │    │
│  │                                   ▼                                  │    │
│  │                    ┌──────────────────────────────┐                 │    │
│  │                    │ PMK-R0 = KDF(MSK, SSID,      │                 │    │
│  │                    │          MDID, R0KH-ID,      │                 │    │
│  │                    │          S0KH-ID)            │                 │    │
│  │                    └──────────────┬───────────────┘                 │    │
│  │                                   │                                  │    │
│  │                    Stored at R0KH (Key Holder)                      │    │
│  │                                   │                                  │    │
│  │                                   ▼                                  │    │
│  │                    ┌──────────────────────────────┐                 │    │
│  │                    │ PMK-R1 = KDF(PMK-R0,         │                 │    │
│  │                    │          R1KH-ID, S1KH-ID)   │                 │    │
│  │                    └──────────────┬───────────────┘                 │    │
│  │                                   │                                  │    │
│  │                    Distributed to R1KH (Target AP)                  │    │
│  │                                   │                                  │    │
│  │                                   ▼                                  │    │
│  │                    ┌──────────────────────────────┐                 │    │
│  │                    │ PTK = KDF(PMK-R1, ANonce,    │                 │    │
│  │                    │       SNonce, AA, SPA)       │                 │    │
│  │                    └──────────────────────────────┘                 │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  FT Over-the-Air (OTA) Protocol:                                            │
│                                                                              │
│  Client              Current AP           Target AP                         │
│    │                     │                    │                             │
│    │  FT Auth Request    │                    │                             │
│    │  ┌──────────────────┤                    │                             │
│    │  │ FTIE: SNonce     │                    │                             │
│    │  │ RSNIE            │                    │                             │
│    │  │ MDE: MDID        │                    │                             │
│    │  └──────────────────┤                    │                             │
│    │ ─────────────────────────────────────────►│                             │
│    │                     │                    │                             │
│    │                     │  ┌─────────────────┤                             │
│    │                     │  │ Request PMK-R1  │                             │
│    │                     │  │ from R0KH       │                             │
│    │                     │  │ (if not cached) │                             │
│    │                     │  └─────────────────┤                             │
│    │                     │                    │                             │
│    │  FT Auth Response   │                    │                             │
│    │  ┌──────────────────┤                    │                             │
│    │  │ FTIE: ANonce,    │                    │                             │
│    │  │       SNonce,    │                    │                             │
│    │  │       MIC        │                    │                             │
│    │  │ RSNIE            │                    │                             │
│    │  │ MDE              │                    │                             │
│    │  │ GTK (encrypted)  │                    │                             │
│    │  └──────────────────┤                    │                             │
│    │ ◄─────────────────────────────────────────│                             │
│    │                     │                    │                             │
│    │  ┌──────────────────┤                    │                             │
│    │  │ Derive PTK       │                    │                             │
│    │  │ Verify MIC       │                    │                             │
│    │  │ Install keys     │                    │                             │
│    │  └──────────────────┤                    │                             │
│    │                     │                    │                             │
│    │  FT Reassoc Request │                    │                             │
│    │  ┌──────────────────┤                    │                             │
│    │  │ FTIE: MIC        │                    │                             │
│    │  │ RSNIE            │                    │                             │
│    │  │ MDE              │                    │                             │
│    │  └──────────────────┤                    │                             │
│    │ ─────────────────────────────────────────►│                             │
│    │                     │                    │                             │
│    │  FT Reassoc Response│                    │                             │
│    │  ┌──────────────────┤                    │                             │
│    │  │ Status: Success  │                    │                             │
│    │  │ FTIE: MIC        │                    │                             │
│    │  └──────────────────┤                    │                             │
│    │ ◄─────────────────────────────────────────│                             │
│    │                     │                    │                             │
│    │  ═══════════════════════════════════════════════════                   │
│    │           ROAMING COMPLETE (~20ms)                                      │
│    │  ═══════════════════════════════════════════════════                   │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 11.4 FT Over-the-DS (Distribution System)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    FT OVER-THE-DS PROTOCOL                                   │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  Client              Current AP           Target AP                         │
│    │                     │                    │                             │
│    │  FT Action Request  │                    │                             │
│    │  (via Current AP)   │                    │                             │
│    │ ────────────────────►│                    │                             │
│    │                     │                    │                             │
│    │                     │  FT Request        │                             │
│    │                     │  (over DS)         │                             │
│    │                     │ ──────────────────►│                             │
│    │                     │                    │                             │
│    │                     │  FT Response       │                             │
│    │                     │  (over DS)         │                             │
│    │                     │ ◄──────────────────│                             │
│    │                     │                    │                             │
│    │  FT Action Response │                    │                             │
│    │  (via Current AP)   │                    │                             │
│    │ ◄────────────────────│                    │                             │
│    │                     │                    │                             │
│    │  ═══════════════════════════════════════════════════                   │
│    │           CLIENT MOVES TO TARGET AP                                     │
│    │  ═══════════════════════════════════════════════════                   │
│    │                     │                    │                             │
│    │  Reassociation Request                   │                             │
│    │ ─────────────────────────────────────────►│                             │
│    │                     │                    │                             │
│    │  Reassociation Response                  │                             │
│    │ ◄─────────────────────────────────────────│                             │
│    │                     │                    │                             │
│    │  ═══════════════════════════════════════════════════                   │
│    │           ROAMING COMPLETE (~10ms)                                      │
│    │  ═══════════════════════════════════════════════════                   │
│                                                                              │
│  Advantage: Pre-authentication before physical move                          │
│  Disadvantage: Requires wired connectivity between APs                       │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 11.5 802.11v BSS Transition Management

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    802.11v BSS TRANSITION MANAGEMENT                         │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  AP-initiated roaming (load balancing, band steering):                       │
│                                                                              │
│  Client                                                          AP         │
│    │                                                              │         │
│    │  BSS Transition Management Request                           │         │
│    │  ┌─────────────────────────────────────────────────────┐    │         │
│    │  │ Request Mode:                                        │    │         │
│    │  │   • Preferred Candidate List Included: 1             │    │         │
│    │  │   • Abridged: 0                                      │    │         │
│    │  │   • Disassociation Imminent: 0/1                     │    │         │
│    │  │   • BSS Termination Included: 0                      │    │         │
│    │  │   • ESS Disassociation Imminent: 0                   │    │         │
│    │  │ Validity Interval: 100 TUs                           │    │         │
│    │  │ Neighbor Report:                                     │    │         │
│    │  │   • BSSID: 00:11:22:33:44:66                        │    │         │
│    │  │   • Channel: 36                                      │    │         │
│    │  │   • PHY Type: VHT                                    │    │         │
│    │  │   • Preference: 255 (highest)                        │    │         │
│    │  └─────────────────────────────────────────────────────┘    │         │
│    │ ◄────────────────────────────────────────────────────────────│         │
│    │                                                              │         │
│    │  BSS Transition Management Response                          │         │
│    │  ┌─────────────────────────────────────────────────────┐    │         │
│    │  │ Status: Accept (0) / Reject (1-6)                    │    │         │
│    │  │ BSS Termination Delay: 0                             │    │         │
│    │  │ Target BSSID: 00:11:22:33:44:66                      │    │         │
│    │  └─────────────────────────────────────────────────────┘    │         │
│    │ ────────────────────────────────────────────────────────────►│         │
│    │                                                              │         │
│    │  (Client roams to suggested AP)                              │         │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 11.6 Roaming Comparison

| Feature | Full Reconnect | OKC | 802.11r FT-OTA | 802.11r FT-DS |
|---------|---------------|-----|----------------|---------------|
| Roam Time | 500-1000ms | 50-100ms | 20-50ms | 10-20ms |
| 802.1X Required | Yes | No | No | No |
| 4-Way Handshake | Yes | Yes | No (in auth) | No (pre-auth) |
| PMK Sync | N/A | Required | Required | Required |
| Client Support | All | Most | Some | Few |
| Voice/Video | Poor | Good | Excellent | Excellent |

---

