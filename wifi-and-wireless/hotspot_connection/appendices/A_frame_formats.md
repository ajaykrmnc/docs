## Appendix A: Frame Formats

### A.1 Beacon Frame Format

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           BEACON FRAME FORMAT                                │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │ MAC Header (24 bytes)                                               │    │
│  ├─────────────────────────────────────────────────────────────────────┤    │
│  │ Frame Control (2)  │ Duration (2) │ DA (6) │ SA (6) │ BSSID (6)    │    │
│  │ Sequence Control (2)                                                │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │ Beacon Frame Body                                                   │    │
│  ├─────────────────────────────────────────────────────────────────────┤    │
│  │ Timestamp (8 bytes)                                                 │    │
│  │ Beacon Interval (2 bytes) - typically 100 TUs (102.4 ms)           │    │
│  │ Capability Info (2 bytes)                                           │    │
│  │   • ESS: 1 (Infrastructure mode)                                    │    │
│  │   • Privacy: 1 (Encryption enabled)                                 │    │
│  │   • Short Preamble: 1                                               │    │
│  │   • Short Slot Time: 1                                              │    │
│  │   • Spectrum Management: 1 (if 5 GHz)                               │    │
│  │   • QoS: 1 (WMM enabled)                                            │    │
│  │   • Radio Measurement: 1 (802.11k)                                  │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │ Information Elements                                                │    │
│  ├─────────────────────────────────────────────────────────────────────┤    │
│  │ SSID (ID=0)                                                         │    │
│  │ Supported Rates (ID=1)                                              │    │
│  │ DS Parameter Set (ID=3) - Channel                                   │    │
│  │ TIM (ID=5) - Traffic Indication Map                                 │    │
│  │ Country (ID=7)                                                      │    │
│  │ BSS Load (ID=11) - Station count, utilization                       │    │
│  │ Power Constraint (ID=32)                                            │    │
│  │ TPC Report (ID=35)                                                  │    │
│  │ Channel Switch Announcement (ID=37)                                 │    │
│  │ HT Capabilities (ID=45)                                             │    │
│  │ RSN (ID=48) - Security info                                         │    │
│  │ HT Operation (ID=61)                                                │    │
│  │ Extended Capabilities (ID=127)                                      │    │
│  │ VHT Capabilities (ID=191)                                           │    │
│  │ VHT Operation (ID=192)                                              │    │
│  │ HE Capabilities (ID=255, Ext=35)                                    │    │
│  │ HE Operation (ID=255, Ext=36)                                       │    │
│  │ Vendor Specific (ID=221)                                            │    │
│  │   • WMM/WME                                                         │    │
│  │   • WPS                                                             │    │
│  │   • Hotspot 2.0 Indication                                          │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │ FCS (4 bytes)                                                       │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### A.2 Authentication Frame Format

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                       AUTHENTICATION FRAME FORMAT                            │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │ MAC Header (24 bytes)                                               │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │ Authentication Frame Body                                           │    │
│  ├─────────────────────────────────────────────────────────────────────┤    │
│  │ Authentication Algorithm (2 bytes)                                  │    │
│  │   • 0: Open System                                                  │    │
│  │   • 1: Shared Key (deprecated)                                      │    │
│  │   • 2: Fast BSS Transition                                          │    │
│  │   • 3: SAE (WPA3)                                                   │    │
│  │   • 4: FILS SK                                                      │    │
│  │   • 5: FILS SK+PFS                                                  │    │
│  │   • 6: FILS PK                                                      │    │
│  │                                                                      │    │
│  │ Authentication Transaction Sequence (2 bytes)                       │    │
│  │   • Open System: 1 (request), 2 (response)                          │    │
│  │   • SAE: 1 (commit), 2 (confirm)                                    │    │
│  │   • FT: 1 (request), 2 (response)                                   │    │
│  │                                                                      │    │
│  │ Status Code (2 bytes)                                               │    │
│  │   • 0: Success                                                      │    │
│  │   • 76: SAE anti-clogging token required                            │    │
│  │   • 126: SAE hash-to-element required                               │    │
│  │                                                                      │    │
│  │ Challenge Text (variable) - for Shared Key only                     │    │
│  │                                                                      │    │
│  │ SAE Elements (for SAE):                                             │    │
│  │   • Finite Cyclic Group (2 bytes)                                   │    │
│  │   • Anti-Clogging Token (variable)                                  │    │
│  │   • Scalar (variable)                                               │    │
│  │   • Element (variable)                                              │    │
│  │   • Confirm (for confirm message)                                   │    │
│  │                                                                      │    │
│  │ FT Elements (for FT):                                               │    │
│  │   • MDE (Mobility Domain Element)                                   │    │
│  │   • FTIE (Fast Transition IE)                                       │    │
│  │   • RSNIE                                                           │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### A.3 Association Request Frame Format

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    ASSOCIATION REQUEST FRAME FORMAT                          │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │ MAC Header (24 bytes)                                               │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │ Association Request Frame Body                                      │    │
│  ├─────────────────────────────────────────────────────────────────────┤    │
│  │ Capability Info (2 bytes)                                           │    │
│  │ Listen Interval (2 bytes)                                           │    │
│  │                                                                      │    │
│  │ Information Elements:                                               │    │
│  │   • SSID (ID=0)                                                     │    │
│  │   • Supported Rates (ID=1)                                          │    │
│  │   • Extended Supported Rates (ID=50)                                │    │
│  │   • Power Capability (ID=33)                                        │    │
│  │   • Supported Channels (ID=36)                                      │    │
│  │   • RSN (ID=48)                                                     │    │
│  │   • QoS Capability (ID=46)                                          │    │
│  │   • HT Capabilities (ID=45)                                         │    │
│  │   • Extended Capabilities (ID=127)                                  │    │
│  │   • VHT Capabilities (ID=191)                                       │    │
│  │   • HE Capabilities (ID=255, Ext=35)                                │    │
│  │   • Vendor Specific (ID=221)                                        │    │
│  │     - WMM Info                                                      │    │
│  │     - WPS                                                           │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

