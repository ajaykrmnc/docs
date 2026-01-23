## Appendix I: Vendor-Specific Information Elements

### I.1 Common Vendor OUIs

| OUI | Vendor | Description |
|-----|--------|-------------|
| 00:50:F2 | Microsoft | WMM, WPS, WPA |
| 00:0B:86 | Arista | Arista-specific extensions |
| 00:40:96 | Cisco | CCX, Aironet |
| 00:17:F2 | Apple | Apple-specific |
| 00:10:18 | Broadcom | Broadcom-specific |
| 50:6F:9A | WiFi Alliance | Hotspot 2.0, P2P, NAN |

### I.2 WMM Information Element

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                      WMM INFORMATION ELEMENT                                 │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  Element ID: 221 (Vendor Specific)                                           │
│  OUI: 00:50:F2                                                               │
│  OUI Type: 2 (WMM/WME)                                                       │
│  OUI Subtype: 0 (Information) or 1 (Parameter)                               │
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │ WMM Parameter Element                                               │    │
│  ├─────────────────────────────────────────────────────────────────────┤    │
│  │ QoS Info (1 byte)                                                   │    │
│  │   • EDCA Parameter Set Update Count (4 bits)                        │    │
│  │   • Q-Ack (1 bit)                                                   │    │
│  │   • Queue Request (1 bit)                                           │    │
│  │   • TXOP Request (1 bit)                                            │    │
│  │   • More Data Ack (1 bit)                                           │    │
│  │                                                                      │    │
│  │ Reserved (1 byte)                                                   │    │
│  │                                                                      │    │
│  │ AC_BE Parameters (4 bytes)                                          │    │
│  │   • AIFSN, ACM, ACI (1 byte)                                        │    │
│  │   • ECWmin, ECWmax (1 byte)                                         │    │
│  │   • TXOP Limit (2 bytes)                                            │    │
│  │                                                                      │    │
│  │ AC_BK Parameters (4 bytes)                                          │    │
│  │ AC_VI Parameters (4 bytes)                                          │    │
│  │ AC_VO Parameters (4 bytes)                                          │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  Default EDCA Parameters:                                                    │
│  ┌──────────┬───────┬────────┬────────┬──────────┐                          │
│  │ AC       │ AIFSN │ CWmin  │ CWmax  │ TXOP     │                          │
│  ├──────────┼───────┼────────┼────────┼──────────┤                          │
│  │ AC_BK    │ 7     │ 15     │ 1023   │ 0        │                          │
│  │ AC_BE    │ 3     │ 15     │ 1023   │ 0        │                          │
│  │ AC_VI    │ 2     │ 7      │ 15     │ 3.008ms  │                          │
│  │ AC_VO    │ 2     │ 3      │ 7      │ 1.504ms  │                          │
│  └──────────┴───────┴────────┴────────┴──────────┘                          │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### I.3 Hotspot 2.0 Indication Element

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                   HOTSPOT 2.0 INDICATION ELEMENT                             │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  Element ID: 221 (Vendor Specific)                                           │
│  OUI: 50:6F:9A                                                               │
│  OUI Type: 16 (HS2.0 Indication)                                             │
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │ HS2.0 Indication                                                    │    │
│  ├─────────────────────────────────────────────────────────────────────┤    │
│  │ HS2.0 Indication (4 bytes)                                          │    │
│  │   • DGAF Disabled (1 bit)                                           │    │
│  │   • PPS MO ID Present (1 bit)                                       │    │
│  │   • ANQP Domain ID Present (1 bit)                                  │    │
│  │   • Reserved (1 bit)                                                │    │
│  │   • Release Number (4 bits)                                         │    │
│  │     - 0: Release 1                                                  │    │
│  │     - 1: Release 2                                                  │    │
│  │     - 2: Release 3                                                  │    │
│  │                                                                      │    │
│  │ PPS MO ID (2 bytes) - if present                                    │    │
│  │ ANQP Domain ID (2 bytes) - if present                               │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

