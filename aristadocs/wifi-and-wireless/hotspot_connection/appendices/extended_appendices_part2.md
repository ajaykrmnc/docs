│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  Inner Authentication Methods:                                               │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  ┌────────────────────────────────────────────────────────────┐     │    │
│  │  │ Inner Method  Windows  macOS  iOS  Android  Linux  ChromeOS│     │    │
│  │  │ ────────────  ───────  ─────  ───  ───────  ─────  ────────│     │    │
│  │  │ MSCHAPv2      Yes      Yes    Yes  Yes      Yes    Yes     │     │    │
│  │  │ GTC           Yes      Yes    Yes  Yes      Yes    Yes     │     │    │
│  │  │ PAP           Yes      Yes    No   Yes      Yes    Yes     │     │    │
│  │  │ CHAP          Yes      No     No   Yes      Yes    No      │     │    │
│  │  │ MD5           Yes      No     No   Yes      Yes    No      │     │    │
│  │  │ TLS           Yes      Yes    Yes  Yes      Yes    Yes     │     │    │
│  │  └────────────────────────────────────────────────────────────┘     │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### AP.3 WiFi Chipset Capabilities

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    WIFI CHIPSET CAPABILITIES                                 │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  Intel WiFi Chipsets:                                                        │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  ┌────────────────────────────────────────────────────────────┐     │    │
│  │  │ Chipset           Standard   Bands      Streams   Features │     │    │
│  │  │ ───────           ────────   ─────      ───────   ──────── │     │    │
│  │  │ AX210             WiFi 6E    2.4/5/6    2x2       WPA3,FT  │     │    │
│  │  │ AX211             WiFi 6E    2.4/5/6    2x2       WPA3,FT  │     │    │
│  │  │ AX411             WiFi 6E    2.4/5/6    2x2       WPA3,FT  │     │    │
│  │  │ BE200             WiFi 7     2.4/5/6    2x2       MLO,WPA3 │     │    │
│  │  │ AX201             WiFi 6     2.4/5      2x2       WPA3,FT  │     │    │
│  │  │ AX200             WiFi 6     2.4/5      2x2       WPA3,FT  │     │    │
│  │  │ AC9560            WiFi 5     2.4/5      2x2       WPA2,FT  │     │    │
│  │  │ AC9260            WiFi 5     2.4/5      2x2       WPA2,FT  │     │    │
│  │  │ AC8265            WiFi 5     2.4/5      2x2       WPA2,FT  │     │    │
│  │  └────────────────────────────────────────────────────────────┘     │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  Qualcomm WiFi Chipsets:                                                     │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  ┌────────────────────────────────────────────────────────────┐     │    │
│  │  │ Chipset           Standard   Bands      Streams   Features │     │    │
│  │  │ ───────           ────────   ─────      ───────   ──────── │     │    │
│  │  │ FastConnect 7800  WiFi 7     2.4/5/6    2x2       MLO,WPA3 │     │    │
│  │  │ FastConnect 6900  WiFi 6E    2.4/5/6    2x2       WPA3,FT  │     │    │
│  │  │ FastConnect 6800  WiFi 6     2.4/5      2x2       WPA3,FT  │     │    │
│  │  │ FastConnect 6700  WiFi 6     2.4/5      2x2       WPA3,FT  │     │    │
│  │  │ QCA6390           WiFi 6     2.4/5      2x2       WPA3,FT  │     │    │
│  │  │ QCA6391           WiFi 6     2.4/5      2x2       WPA3,FT  │     │    │
│  │  │ WCN6855           WiFi 6E    2.4/5/6    2x2       WPA3,FT  │     │    │
│  │  └────────────────────────────────────────────────────────────┘     │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  Broadcom WiFi Chipsets:                                                     │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  ┌────────────────────────────────────────────────────────────┐     │    │
│  │  │ Chipset           Standard   Bands      Streams   Features │     │    │
│  │  │ ───────           ────────   ─────      ───────   ──────── │     │    │
│  │  │ BCM4389           WiFi 6E    2.4/5/6    2x2       WPA3,FT  │     │    │
│  │  │ BCM4398           WiFi 7     2.4/5/6    2x2       MLO,WPA3 │     │    │
│  │  │ BCM43752          WiFi 6E    2.4/5/6    2x2       WPA3,FT  │     │    │
│  │  │ BCM4375           WiFi 6     2.4/5      2x2       WPA3,FT  │     │    │
│  │  │ BCM4359           WiFi 5     2.4/5      2x2       WPA2,FT  │     │    │
│  │  │ BCM4356           WiFi 5     2.4/5      2x2       WPA2,FT  │     │    │
│  │  └────────────────────────────────────────────────────────────┘     │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  MediaTek WiFi Chipsets:                                                     │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  ┌────────────────────────────────────────────────────────────┐     │    │
│  │  │ Chipset           Standard   Bands      Streams   Features │     │    │
│  │  │ ───────           ────────   ─────      ───────   ──────── │     │    │
│  │  │ MT7925            WiFi 7     2.4/5/6    2x2       MLO,WPA3 │     │    │
│  │  │ MT7922            WiFi 6E    2.4/5/6    2x2       WPA3,FT  │     │    │
│  │  │ MT7921            WiFi 6     2.4/5      2x2       WPA3,FT  │     │    │
│  │  │ MT7915            WiFi 6     2.4/5      4x4       WPA3,FT  │     │    │
│  │  │ MT7612            WiFi 5     2.4/5      2x2       WPA2,FT  │     │    │
│  │  └────────────────────────────────────────────────────────────┘     │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Appendix AQ: WiFi Alliance Certification Programs

### AQ.1 WiFi CERTIFIED Programs

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    WIFI ALLIANCE CERTIFICATION PROGRAMS                      │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  Core Certification Programs:                                                │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  ┌────────────────────────────────────────────────────────────┐     │    │
│  │  │ Program                   Standard    Description          │     │    │
│  │  │ ───────                   ────────    ───────────          │     │    │
│  │  │ WiFi CERTIFIED n          802.11n     High throughput      │     │    │
│  │  │ WiFi CERTIFIED ac         802.11ac    Very high throughput │     │    │
│  │  │ WiFi CERTIFIED 6          802.11ax    High efficiency      │     │    │
│  │  │ WiFi CERTIFIED 6E         802.11ax    6 GHz band           │     │    │
│  │  │ WiFi CERTIFIED 7          802.11be    Extremely high       │     │    │
│  │  │                                       throughput           │     │    │
│  │  └────────────────────────────────────────────────────────────┘     │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  Security Certification Programs:                                            │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  ┌────────────────────────────────────────────────────────────┐     │    │
│  │  │ Program                   Features                         │     │    │
│  │  │ ───────                   ────────                         │     │    │
│  │  │ WPA2-Personal             AES-CCMP, PSK                    │     │    │
│  │  │ WPA2-Enterprise           AES-CCMP, 802.1X                 │     │    │
│  │  │ WPA3-Personal             SAE, AES-CCMP/GCMP               │     │    │
│  │  │ WPA3-Enterprise           802.1X, GCMP-256                 │     │    │
│  │  │ WPA3-Enterprise 192-bit   Suite B, GCMP-256                │     │    │
│  │  │ Enhanced Open             OWE, opportunistic encryption    │     │    │
│  │  │ Protected Management      802.11w, MFP                     │     │    │
│  │  │ Frames                                                     │     │    │
│  │  └────────────────────────────────────────────────────────────┘     │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  Roaming and Connectivity Programs:                                          │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  ┌────────────────────────────────────────────────────────────┐     │    │
│  │  │ Program                   Standard    Description          │     │    │
│  │  │ ───────                   ────────    ───────────          │     │    │
│  │  │ Voice-Enterprise          802.11k/r/v Voice over WiFi      │     │    │
│  │  │ Optimized Connectivity    802.11k/v   Fast roaming         │     │    │
│  │  │ Agile Multiband           802.11k/v   Band steering        │     │    │
│  │  │ Passpoint                 802.11u     Hotspot 2.0          │     │    │
│  │  │ Passpoint Release 2       HS2.0 R2    OSU, remediation     │     │    │
│  │  │ Passpoint Release 3       HS2.0 R3    Venue URL, T&C       │     │    │
│  │  │ FILS                      802.11ai    Fast initial link    │     │    │
│  │  └────────────────────────────────────────────────────────────┘     │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  IoT and Specialty Programs:                                                 │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  ┌────────────────────────────────────────────────────────────┐     │    │
│  │  │ Program                   Description                      │     │    │
│  │  │ ───────                   ───────────                      │     │    │
│  │  │ WiFi HaLow                802.11ah, sub-1 GHz IoT          │     │    │
│  │  │ WiFi Aware                Neighbor Awareness Networking    │     │    │
│  │  │ WiFi Direct               Peer-to-peer connections         │     │    │
│  │  │ Miracast                  Display mirroring                │     │    │
│  │  │ WiFi Location             Fine timing measurement          │     │    │
│  │  │ WiFi TimeSync             Time synchronization             │     │    │
│  │  │ WiFi Easy Connect         DPP, QR code provisioning        │     │    │
│  │  │ WiFi CERTIFIED QoS        WMM, traffic prioritization      │     │    │
│  │  │ WiFi Vantage              Enterprise optimization          │     │    │
│  │  └────────────────────────────────────────────────────────────┘     │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### AQ.2 Certification Test Categories

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    CERTIFICATION TEST CATEGORIES                             │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  WiFi 6 (802.11ax) Test Categories:                                          │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  ┌────────────────────────────────────────────────────────────┐     │    │
│  │  │ Category                  Tests                            │     │    │
│  │  │ ────────                  ─────                            │     │    │
│  │  │ OFDMA                     DL-OFDMA, UL-OFDMA, RU allocation│     │    │
│  │  │ MU-MIMO                   DL-MU-MIMO, UL-MU-MIMO           │     │    │
│  │  │ BSS Coloring              Color assignment, collision avoid│     │    │
│  │  │ TWT                       Individual TWT, Broadcast TWT    │     │    │
│  │  │ 1024-QAM                  High-order modulation            │     │    │
│  │  │ Beamforming               SU-BF, MU-BF                     │     │    │
│  │  │ Spatial Reuse             SR operation, OBSS PD            │     │    │
│  │  │ Extended Range            ER SU PPDU                       │     │    │
│  │  └────────────────────────────────────────────────────────────┘     │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  WPA3 Test Categories:                                                       │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  ┌────────────────────────────────────────────────────────────┐     │    │
│  │  │ Category                  Tests                            │     │    │
│  │  │ ────────                  ─────                            │     │    │
│  │  │ SAE                       Commit, Confirm, anti-clogging   │     │    │
│  │  │ SAE-PK                    Public key authentication        │     │    │
│  │  │ SAE H2E                   Hash-to-element                  │     │    │
│  │  │ Transition Mode           WPA2/WPA3 mixed mode             │     │    │
│  │  │ PMF                       Required, optional               │     │    │
│  │  │ Suite B                   192-bit security                 │     │    │
│  │  │ OWE                       Opportunistic encryption         │     │    │
│  │  │ OWE Transition            Open/OWE mixed mode              │     │    │
│  │  └────────────────────────────────────────────────────────────┘     │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  Voice-Enterprise Test Categories:                                           │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  ┌────────────────────────────────────────────────────────────┐     │    │
│  │  │ Category                  Tests                            │     │    │
│  │  │ ────────                  ─────                            │     │    │
│  │  │ 802.11r                   FT over-the-air, FT over-the-DS  │     │    │
│  │  │ 802.11k                   Neighbor report, beacon report   │     │    │
│  │  │ 802.11v                   BSS transition, WNM sleep        │     │    │
│  │  │ WMM                       AC_VO, AC_VI, AC_BE, AC_BK       │     │    │
│  │  │ WMM-AC                    Admission control                │     │    │
│  │  │ U-APSD                    Unscheduled power save           │     │    │
│  │  │ Roaming Time              <50 ms requirement               │     │    │
│  │  └────────────────────────────────────────────────────────────┘     │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Appendix AR: Security Best Practices Checklist

### AR.1 Network Security Checklist

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    NETWORK SECURITY CHECKLIST                                │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  Authentication Security:                                                    │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  [ ] Use WPA3-Personal or WPA3-Enterprise                            │    │
│  │  [ ] If WPA2, use AES-CCMP only (disable TKIP)                       │    │
│  │  [ ] Enable Protected Management Frames (802.11w)                    │    │
│  │  [ ] Use strong passphrases (12+ characters, mixed case, numbers)    │    │
│  │  [ ] Implement 802.1X for enterprise networks                        │    │
│  │  [ ] Use EAP-TLS with client certificates for highest security       │    │
│  │  [ ] Validate server certificates in supplicant configuration        │    │
│  │  [ ] Implement certificate revocation checking (OCSP/CRL)            │    │
│  │  [ ] Use unique PSK per device (UPSK) where possible                 │    │
│  │  [ ] Rotate PSK/passwords regularly                                  │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  RADIUS Security:                                                            │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  [ ] Use strong RADIUS shared secrets (32+ characters)               │    │
│  │  [ ] Implement RadSec (RADIUS over TLS) for secure transport         │    │
│  │  [ ] Configure RADIUS server redundancy                              │    │
│  │  [ ] Enable RADIUS accounting for audit trail                        │    │
│  │  [ ] Implement CoA/DM for dynamic session control                    │    │
│  │  [ ] Use Message-Authenticator attribute                             │    │
│  │  [ ] Restrict RADIUS client IP addresses                             │    │
│  │  [ ] Monitor RADIUS logs for authentication failures                 │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  Network Segmentation:                                                       │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  [ ] Separate guest and corporate networks                           │    │
│  │  [ ] Use VLANs for network segmentation                              │    │
│  │  [ ] Implement dynamic VLAN assignment via RADIUS                    │    │
│  │  [ ] Isolate IoT devices on separate network                         │    │
│  │  [ ] Enable client isolation on guest networks                       │    │
│  │  [ ] Implement firewall rules between segments                       │    │
│  │  [ ] Use private VLANs where appropriate                             │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  Rogue AP Detection:                                                         │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  [ ] Enable rogue AP detection on all APs                            │    │
│  │  [ ] Configure alerts for rogue AP detection                         │    │
│  │  [ ] Implement wireless intrusion prevention (WIPS)                  │    │
│  │  [ ] Regularly scan for unauthorized APs                             │    │
│  │  [ ] Maintain authorized AP whitelist                                │    │
│  │  [ ] Monitor for evil twin attacks                                   │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  Management Security:                                                        │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  [ ] Use HTTPS for web management interface                          │    │
│  │  [ ] Use SSH instead of Telnet for CLI access                        │    │
│  │  [ ] Implement strong admin passwords                                │    │
│  │  [ ] Enable multi-factor authentication for admin access             │    │
│  │  [ ] Restrict management access to specific VLANs/IPs                │    │
│  │  [ ] Disable unused management interfaces                            │    │
│  │  [ ] Keep firmware up to date                                        │    │
│  │  [ ] Implement configuration backup and change control               │    │
│  │  [ ] Enable logging and send to central syslog server                │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### AR.2 Client Security Checklist

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    CLIENT SECURITY CHECKLIST                                 │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  Supplicant Configuration:                                                   │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  [ ] Validate server certificate in EAP configuration                │    │
│  │  [ ] Specify expected server certificate CN/SAN                      │    │
│  │  [ ] Install trusted CA certificates                                 │    │
│  │  [ ] Disable auto-connect to open networks                           │    │
│  │  [ ] Remove saved networks that are no longer needed                 │    │
│  │  [ ] Use randomized MAC addresses for privacy                        │    │
│  │  [ ] Enable WPA3 where supported                                     │    │
│  │  [ ] Disable legacy protocols (WEP, TKIP)                            │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  Mobile Device Management (MDM):                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  [ ] Deploy WiFi profiles via MDM                                    │    │
│  │  [ ] Push certificates via MDM                                       │    │
│  │  [ ] Enforce security policies on managed devices                    │    │
│  │  [ ] Implement device compliance checks                              │    │
│  │  [ ] Enable remote wipe capability                                   │    │
│  │  [ ] Monitor device security posture                                 │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Appendix AS: Capacity Planning Guide

### AS.1 Client Density Planning

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    CLIENT DENSITY PLANNING                                   │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  Recommended Client Density per AP:                                          │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  ┌────────────────────────────────────────────────────────────┐     │    │
│  │  │ Environment           Low Density   Medium    High Density │     │    │
│  │  │ ───────────           ───────────   ──────    ──────────── │     │    │
│  │  │ Office                25-50         50-75     75-100       │     │    │
│  │  │ Conference Room       15-25         25-40     40-60        │     │    │
│  │  │ Auditorium            50-100        100-150   150-200      │     │    │
│  │  │ Classroom             20-30         30-40     40-50        │     │    │
│  │  │ Hospital              15-25         25-35     35-50        │     │    │
│  │  │ Retail                30-50         50-75     75-100       │     │    │
│  │  │ Warehouse             50-100        100-150   150-200      │     │    │
│  │  │ Stadium               100-200       200-300   300-500      │     │    │
│  │  └────────────────────────────────────────────────────────────┘     │    │
│  │                                                                      │    │
│  │  Note: High-density deployments require WiFi 6/6E/7 APs             │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  Bandwidth per Client Estimates:                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  ┌────────────────────────────────────────────────────────────┐     │    │
│  │  │ Application           Minimum       Recommended   Peak     │     │    │
│  │  │ ───────────           ───────       ───────────   ────     │     │    │
│  │  │ Web Browsing          1 Mbps        5 Mbps        10 Mbps  │     │    │
│  │  │ Email                 0.5 Mbps      2 Mbps        5 Mbps   │     │    │
│  │  │ VoIP                  0.1 Mbps      0.3 Mbps      0.5 Mbps │     │    │
│  │  │ Video Conferencing    1 Mbps        3 Mbps        8 Mbps   │     │    │
│  │  │ HD Video Streaming    5 Mbps        10 Mbps       25 Mbps  │     │    │
│  │  │ 4K Video Streaming    15 Mbps       25 Mbps       50 Mbps  │     │    │
│  │  │ File Transfer         5 Mbps        20 Mbps       100 Mbps │     │    │
│  │  │ Cloud Applications    2 Mbps        10 Mbps       25 Mbps  │     │    │
│  │  │ VDI/Remote Desktop    2 Mbps        5 Mbps        15 Mbps  │     │    │
│  │  └────────────────────────────────────────────────────────────┘     │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  AP Capacity Calculation:                                                    │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  Formula:                                                            │    │
│  │  ┌────────────────────────────────────────────────────────────┐     │    │
│  │  │                                                            │     │    │
│  │  │  Max Clients = (AP Throughput × Efficiency) / BW per Client│     │    │
│  │  │                                                            │     │    │
│  │  │  Example (WiFi 6, 80 MHz, 2x2):                            │     │    │
│  │  │  - AP Throughput: 1.2 Gbps                                 │     │    │
│  │  │  - Efficiency: 50% (typical)                               │     │    │
│  │  │  - BW per Client: 10 Mbps                                  │     │    │
│  │  │  - Max Clients: (1200 × 0.5) / 10 = 60 clients             │     │    │
│  │  │                                                            │     │    │
│  │  └────────────────────────────────────────────────────────────┘     │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### AS.2 Coverage Planning

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    COVERAGE PLANNING                                         │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  Signal Strength Requirements:                                               │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  ┌────────────────────────────────────────────────────────────┐     │    │
│  │  │ Application           Min RSSI      Recommended   SNR      │     │    │
│  │  │ ───────────           ────────      ───────────   ───      │     │    │
│  │  │ VoIP                  -67 dBm       -65 dBm       25 dB    │     │    │
│  │  │ Video Conferencing    -67 dBm       -65 dBm       25 dB    │     │    │
│  │  │ Real-time Location    -70 dBm       -67 dBm       20 dB    │     │    │
│  │  │ General Data          -70 dBm       -67 dBm       20 dB    │     │    │
│  │  │ Email/Web             -75 dBm       -70 dBm       15 dB    │     │    │
│  │  │ IoT/Sensors           -80 dBm       -75 dBm       10 dB    │     │    │
│  │  └────────────────────────────────────────────────────────────┘     │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  Typical Coverage Ranges:                                                    │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  ┌────────────────────────────────────────────────────────────┐     │    │
│  │  │ Environment           2.4 GHz       5 GHz         6 GHz    │     │    │
│  │  │ ───────────           ───────       ─────         ─────    │     │    │
│  │  │ Open Office           30-50 m       20-35 m       15-25 m  │     │    │
│  │  │ Cubicle Office        25-40 m       15-25 m       10-20 m  │     │    │
│  │  │ Walled Office         15-25 m       10-20 m       8-15 m   │     │    │
│  │  │ Warehouse             50-100 m      35-60 m       25-45 m  │     │    │
│  │  │ Outdoor               100-150 m     60-100 m      40-70 m  │     │    │
│  │  │ Hospital              15-25 m       10-20 m       8-15 m   │     │    │
│  │  │ Hotel Room            1 room        1 room        1 room   │     │    │
│  │  └────────────────────────────────────────────────────────────┘     │    │
│  │                                                                      │    │
│  │  Note: Ranges depend on TX power, antenna gain, and obstacles       │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  Wall Attenuation Factors:                                                   │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  ┌────────────────────────────────────────────────────────────┐     │    │
│  │  │ Material              2.4 GHz       5 GHz         6 GHz    │     │    │
│  │  │ ────────              ───────       ─────         ─────    │     │    │
│  │  │ Drywall               3 dB          4 dB          5 dB     │     │    │
│  │  │ Plywood               4 dB          5 dB          6 dB     │     │    │
│  │  │ Glass (clear)         3 dB          4 dB          5 dB     │     │    │
│  │  │ Glass (tinted)        6 dB          8 dB          10 dB    │     │    │
│  │  │ Brick                 6 dB          8 dB          10 dB    │     │    │
│  │  │ Concrete              10 dB         15 dB         18 dB    │     │    │
│  │  │ Concrete (reinforced) 15 dB         20 dB         25 dB    │     │    │
│  │  │ Metal                 20+ dB        25+ dB        30+ dB   │     │    │
│  │  │ Elevator Shaft        25+ dB        30+ dB        35+ dB   │     │    │
│  │  └────────────────────────────────────────────────────────────┘     │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### AS.3 Channel Planning

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    CHANNEL PLANNING                                          │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  2.4 GHz Channel Plan:                                                       │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  Non-overlapping Channels: 1, 6, 11 (US/Canada)                      │    │
│  │                            1, 5, 9, 13 (Europe/Japan)                │    │
│  │                                                                      │    │
│  │  ┌────────────────────────────────────────────────────────────┐     │    │
│  │  │                                                            │     │    │
│  │  │  Channel 1    Channel 6    Channel 11                      │     │    │
│  │  │  ─────────    ─────────    ──────────                      │     │    │
│  │  │  2401-2423    2426-2448    2451-2473 MHz                   │     │    │
│  │  │                                                            │     │    │
│  │  │  Recommended: Use only channels 1, 6, 11                   │     │    │
│  │  │  Avoid: Channels 2-5, 7-10 (overlap)                       │     │    │
│  │  │                                                            │     │    │
│  │  └────────────────────────────────────────────────────────────┘     │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  5 GHz Channel Plan (US):                                                    │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  UNII-1 (Indoor): 36, 40, 44, 48                                     │    │
│  │  UNII-2A (DFS):   52, 56, 60, 64                                     │    │
│  │  UNII-2C (DFS):   100, 104, 108, 112, 116, 120, 124, 128, 132, 136,  │    │
│  │                   140, 144                                           │    │
│  │  UNII-3 (Indoor): 149, 153, 157, 161, 165                            │    │
│  │                                                                      │    │
│  │  80 MHz Channels:                                                    │    │
│  │  ┌────────────────────────────────────────────────────────────┐     │    │
│  │  │ Primary   Secondary   Center Freq   Channels               │     │    │
│  │  │ ───────   ─────────   ───────────   ────────               │     │    │
│  │  │ 36        40,44,48    42            36+40+44+48            │     │    │
│  │  │ 52        56,60,64    58            52+56+60+64 (DFS)      │     │    │
│  │  │ 100       104,108,112 106           100+104+108+112 (DFS)  │     │    │
│  │  │ 116       120,124,128 122           116+120+124+128 (DFS)  │     │    │
│  │  │ 132       136,140,144 138           132+136+140+144 (DFS)  │     │    │
│  │  │ 149       153,157,161 155           149+153+157+161        │     │    │
│  │  └────────────────────────────────────────────────────────────┘     │    │
│  │                                                                      │    │
│  │  160 MHz Channels:                                                   │    │
│  │  ┌────────────────────────────────────────────────────────────┐     │    │
│  │  │ Primary   Center Freq   Channels                           │     │    │
│  │  │ ───────   ───────────   ────────                           │     │    │
│  │  │ 36        50            36-64                              │     │    │
│  │  │ 100       114           100-128 (DFS)                      │     │    │
│  │  └────────────────────────────────────────────────────────────┘     │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  6 GHz Channel Plan (US):                                                    │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  UNII-5: 1-93 (5925-6425 MHz)                                        │    │
│  │  UNII-6: 97-113 (6425-6525 MHz)                                      │    │
│  │  UNII-7: 117-185 (6525-6875 MHz)                                     │    │
│  │  UNII-8: 189-233 (6875-7125 MHz)                                     │    │
│  │                                                                      │    │
│  │  Total: 59 × 20 MHz channels                                         │    │
│  │         29 × 40 MHz channels                                         │    │
│  │         14 × 80 MHz channels                                         │    │
│  │          7 × 160 MHz channels                                        │    │
│  │          3 × 320 MHz channels                                        │    │
│  │                                                                      │    │
│  │  320 MHz Channels (WiFi 7):                                          │    │
│  │  ┌────────────────────────────────────────────────────────────┐     │    │
│  │  │ Center Freq   Frequency Range                              │     │    │
│  │  │ ───────────   ───────────────                              │     │    │
│  │  │ 31            5945-6265 MHz                                │     │    │
│  │  │ 95            6265-6585 MHz                                │     │    │
│  │  │ 159           6585-6905 MHz                                │     │    │
│  │  └────────────────────────────────────────────────────────────┘     │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Appendix AT: Antenna and RF Considerations

### AT.1 Antenna Types and Patterns

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    ANTENNA TYPES AND PATTERNS                                │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  Omnidirectional Antenna:                                                    │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  Horizontal Pattern:           Vertical Pattern:                     │    │
│  │                                                                      │    │
│  │        ┌───────┐                      ┌─┐                            │    │
│  │       /         \                    / │ \                           │    │
│  │      │     ●     │                  │  ●  │                          │    │
│  │       \         /                    \ │ /                           │    │
│  │        └───────┘                      └─┘                            │    │
│  │                                                                      │    │
│  │  Characteristics:                                                    │    │
│  │  - 360° horizontal coverage                                          │    │
│  │  - Typical gain: 2-8 dBi                                             │    │
│  │  - Best for: General indoor coverage                                 │    │
│  │  - Beamwidth: 360° H-plane, 30-80° E-plane                           │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  Directional Antenna (Patch/Panel):                                          │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  Horizontal Pattern:           Vertical Pattern:                     │    │
│  │                                                                      │    │
│  │           ┌───┐                       ┌───┐                          │    │
│  │          /     \                     /     \                         │    │
│  │         │   ●───────────            │   ●───────────                 │    │
│  │          \     /                     \     /                         │    │
│  │           └───┘                       └───┘                          │    │
│  │                                                                      │    │
│  │  Characteristics:                                                    │    │
│  │  - Focused coverage in one direction                                 │    │
│  │  - Typical gain: 6-14 dBi                                            │    │
│  │  - Best for: Hallways, outdoor point-to-point                        │    │
│  │  - Beamwidth: 60-120° H-plane, 60-120° E-plane                       │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  Sector Antenna:                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  Horizontal Pattern:           Vertical Pattern:                     │    │
│  │                                                                      │    │
│  │         ┌─────┐                      ┌─┐                             │    │
│  │        /       \                    / │ \                            │    │
│  │       │    ●────────────           │  ●────────────                  │    │
│  │        \       /                    \ │ /                            │    │
│  │         └─────┘                      └─┘                             │    │
│  │                                                                      │    │
│  │  Characteristics:                                                    │    │
│  │  - Wide horizontal, narrow vertical                                  │    │
│  │  - Typical gain: 10-18 dBi                                           │    │
│  │  - Best for: Stadium, outdoor coverage                               │    │
│  │  - Beamwidth: 60-120° H-plane, 10-30° E-plane                        │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  Yagi Antenna:                                                               │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  Pattern:                                                            │    │
│  │                                                                      │    │
│  │         ┌─┐                                                          │    │
│  │        / │ \                                                         │    │
│  │       │  ●──────────────────────────────────────                     │    │
│  │        \ │ /                                                         │    │
│  │         └─┘                                                          │    │
│  │                                                                      │    │
│  │  Characteristics:                                                    │    │
│  │  - Highly directional                                                │    │
│  │  - Typical gain: 12-18 dBi                                           │    │
│  │  - Best for: Long-range point-to-point                               │    │
│  │  - Beamwidth: 30-60° H-plane, 30-60° E-plane                         │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  Parabolic Dish Antenna:                                                     │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  Pattern:                                                            │    │
│  │                                                                      │    │
│  │        ┌┐                                                            │    │
│  │       /││\                                                           │    │
│  │      │ ●│────────────────────────────────────────────────            │    │
│  │       \││/                                                           │    │
│  │        └┘                                                            │    │
│  │                                                                      │    │
│  │  Characteristics:                                                    │    │
│  │  - Extremely directional                                             │    │
│  │  - Typical gain: 20-30 dBi                                           │    │
│  │  - Best for: Very long-range point-to-point                          │    │
│  │  - Beamwidth: 5-15° H-plane, 5-15° E-plane                           │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### AT.2 MIMO Configurations

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    MIMO CONFIGURATIONS                                       │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  MIMO Notation: TxR:S (Transmit × Receive : Spatial Streams)                 │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  ┌────────────────────────────────────────────────────────────┐     │    │
│  │  │ Config    TX Chains   RX Chains   Streams   Typical Use    │     │    │
│  │  │ ──────    ─────────   ─────────   ───────   ───────────    │     │    │
│  │  │ 1x1:1     1           1           1         IoT, basic     │     │    │
│  │  │ 2x2:2     2           2           2         Laptop, phone  │     │    │
│  │  │ 3x3:3     3           3           3         High-end laptop│     │    │
│  │  │ 4x4:4     4           4           4         Enterprise AP  │     │    │
│  │  │ 8x8:8     8           8           8         High-density AP│     │    │
│  │  │ 16x16:16  16          16          16        WiFi 7 AP      │     │    │
│  │  └────────────────────────────────────────────────────────────┘     │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  MIMO Techniques:                                                            │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  Spatial Multiplexing:                                               │    │
│  │  ┌────────────────────────────────────────────────────────────┐     │    │
│  │  │                                                            │     │    │
│  │  │  TX Antenna 1 ────────────────────────────> RX Antenna 1   │     │    │
│  │  │       │                                          │         │     │    │
│  │  │       │         ╲                    ╱           │         │     │    │
│  │  │       │          ╲                  ╱            │         │     │    │
│  │  │       │           ╲                ╱             │         │     │    │
│  │  │       │            ╲              ╱              │         │     │    │
│  │  │       │             ╲            ╱               │         │     │    │
│  │  │       │              ╲          ╱                │         │     │    │
│  │  │       │               ╲        ╱                 │         │     │    │
│  │  │       │                ╲      ╱                  │         │     │    │
│  │  │       │                 ╲    ╱                   │         │     │    │
│  │  │       │                  ╲  ╱                    │         │     │    │
│  │  │       │                   ╲╱                     │         │     │    │
│  │  │       │                   ╱╲                     │         │     │    │
│  │  │       │                  ╱  ╲                    │         │     │    │
│  │  │       │                 ╱    ╲                   │         │     │    │
│  │  │       │                ╱      ╲                  │         │     │    │
│  │  │       │               ╱        ╲                 │         │     │    │
│  │  │       │              ╱          ╲                │         │     │    │
│  │  │       │             ╱            ╲               │         │     │    │
│  │  │       │            ╱              ╲              │         │     │    │
│  │  │       │           ╱                ╲             │         │     │    │
│  │  │       │          ╱                  ╲            │         │     │    │
│  │  │       │         ╱                    ╲           │         │     │    │
│  │  │  TX Antenna 2 ────────────────────────────> RX Antenna 2   │     │    │
│  │  │                                                            │     │    │
│  │  │  - Sends different data on each stream                     │     │    │
│  │  │  - Multiplies throughput by number of streams              │     │    │
│  │  │  - Requires good SNR and multipath                         │     │    │
│  │  │                                                            │     │    │
│  │  └────────────────────────────────────────────────────────────┘     │    │
│  │                                                                      │    │
│  │  Beamforming:                                                        │    │
│  │  ┌────────────────────────────────────────────────────────────┐     │    │
│  │  │                                                            │     │    │
│  │  │  Without Beamforming:        With Beamforming:             │     │    │
│  │  │                                                            │     │    │
│  │  │       ┌───────┐                    ┌───┐                   │     │    │
│  │  │      /         \                  /     \                  │     │    │
│  │  │     │     ●     │                │   ●───────> Client      │     │    │
│  │  │      \         /                  \     /                  │     │    │
│  │  │       └───────┘                    └───┘                   │     │    │
│  │  │                                                            │     │    │
│  │  │  - Focuses energy toward client                            │     │    │
│  │  │  - Increases range and throughput                          │     │    │
│  │  │  - Reduces interference to other clients                   │     │    │
│  │  │                                                            │     │    │
│  │  └────────────────────────────────────────────────────────────┘     │    │
│  │                                                                      │    │
│  │  MU-MIMO:                                                            │    │
│  │  ┌────────────────────────────────────────────────────────────┐     │    │
│  │  │                                                            │     │    │
│  │  │  SU-MIMO:                    MU-MIMO:                      │     │    │
│  │  │                                                            │     │    │
│  │  │       ┌───┐                       ┌───┐                    │     │    │
│  │  │      /     \                     /     \                   │     │    │
│  │  │     │   ●───────> Client 1      │   ●───────> Client 1    │     │    │
│  │  │      \     /                     │   │                     │     │    │
│  │  │       └───┘                      │   └───────> Client 2    │     │    │
│  │  │                                   \     /                   │     │    │
│  │  │  (One client at a time)           └───┘                    │     │    │
│  │  │                                                            │     │    │
│  │  │                              (Multiple clients             │     │    │
│  │  │                               simultaneously)              │     │    │
│  │  │                                                            │     │    │
│  │  │  - Serves multiple clients simultaneously                  │     │    │
│  │  │  - Increases network capacity                              │     │    │
│  │  │  - Requires client support                                 │     │    │
│  │  │                                                            │     │    │
│  │  └────────────────────────────────────────────────────────────┘     │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### AT.3 Link Budget Calculation

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    LINK BUDGET CALCULATION                                   │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  Link Budget Formula:                                                        │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  Received Power (dBm) = TX Power (dBm)                               │    │
│  │                       + TX Antenna Gain (dBi)                        │    │
│  │                       - TX Cable Loss (dB)                           │    │
│  │                       - Free Space Path Loss (dB)                    │    │
│  │                       - Obstacle Loss (dB)                           │    │
│  │                       + RX Antenna Gain (dBi)                        │    │
│  │                       - RX Cable Loss (dB)                           │    │
│  │                                                                      │    │
│  │  Free Space Path Loss (dB) = 20 × log10(d) + 20 × log10(f) + 32.44   │    │
│  │                              where d = distance in km                │    │
│  │                                    f = frequency in MHz              │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  Example Link Budget:                                                        │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  Scenario: Indoor AP to Client, 30 meters, 5 GHz                     │    │
│  │                                                                      │    │
│  │  ┌────────────────────────────────────────────────────────────┐     │    │
│  │  │ Parameter                 Value        Cumulative          │     │    │
│  │  │ ─────────                 ─────        ──────────          │     │    │
│  │  │ AP TX Power               20 dBm       20 dBm              │     │    │
│  │  │ AP Antenna Gain           +4 dBi       24 dBm              │     │    │
│  │  │ AP Cable Loss             -1 dB        23 dBm              │     │    │
│  │  │ Free Space Path Loss      -68 dB       -45 dBm             │     │    │
│  │  │ Wall Loss (2 walls)       -8 dB        -53 dBm             │     │    │
│  │  │ Client Antenna Gain       +2 dBi       -51 dBm             │     │    │
│  │  │ ─────────────────────────────────────────────────────────  │     │    │
│  │  │ Received Signal           -51 dBm                          │     │    │
│  │  │ Client Sensitivity        -75 dBm                          │     │    │
│  │  │ Link Margin               24 dB                            │     │    │
│  │  └────────────────────────────────────────────────────────────┘     │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  Receiver Sensitivity by Data Rate:                                          │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  ┌────────────────────────────────────────────────────────────┐     │    │
│  │  │ Standard    Data Rate     Typical Sensitivity              │     │    │
│  │  │ ────────    ─────────     ────────────────────              │     │    │
│  │  │ 802.11b     1 Mbps        -94 dBm                          │     │    │
│  │  │ 802.11b     11 Mbps       -85 dBm                          │     │    │
│  │  │ 802.11a/g   6 Mbps        -90 dBm                          │     │    │
│  │  │ 802.11a/g   54 Mbps       -75 dBm                          │     │    │
│  │  │ 802.11n     MCS 0         -90 dBm                          │     │    │
│  │  │ 802.11n     MCS 7         -72 dBm                          │     │    │
│  │  │ 802.11ac    MCS 0         -88 dBm                          │     │    │
│  │  │ 802.11ac    MCS 9         -65 dBm                          │     │    │
│  │  │ 802.11ax    MCS 0         -88 dBm                          │     │    │
│  │  │ 802.11ax    MCS 11        -60 dBm                          │     │    │
│  │  └────────────────────────────────────────────────────────────┘     │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Appendix AU: Troubleshooting Decision Trees

### AU.1 Connection Failure Decision Tree

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    CONNECTION FAILURE DECISION TREE                          │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │                    Client Cannot Connect                             │    │
│  │                           │                                          │    │
│  │                           ▼                                          │    │
│  │              ┌────────────────────────┐                              │    │
│  │              │ Can client see SSID?   │                              │    │
│  │              └────────────────────────┘                              │    │
│  │                    │           │                                     │    │
│  │                   Yes          No                                    │    │
│  │                    │           │                                     │    │
│  │                    ▼           ▼                                     │    │
│  │              ┌─────────┐  ┌─────────────────────────┐                │    │
│  │              │ Step 2  │  │ Check:                  │                │    │
│  │              └─────────┘  │ - AP powered on?        │                │    │
│  │                    │      │ - SSID broadcast on?    │                │    │
│  │                    │      │ - Client in range?      │                │    │
│  │                    │      │ - Correct band enabled? │                │    │
│  │                    │      │ - Regulatory domain?    │                │    │
│  │                    │      └─────────────────────────┘                │    │
│  │                    ▼                                                 │    │
│  │              ┌────────────────────────┐                              │    │
│  │              │ Authentication fails?  │                              │    │
│  │              └────────────────────────┘                              │    │
│  │                    │           │                                     │    │
│  │                   Yes          No                                    │    │
│  │                    │           │                                     │    │
│  │                    ▼           ▼                                     │    │
│  │              ┌─────────────────────────┐  ┌─────────┐                │    │
│  │              │ Check:                  │  │ Step 3  │                │    │
│  │              │ - Correct password?     │  └─────────┘                │    │
│  │              │ - Security mode match?  │       │                     │    │
│  │              │ - PMF compatibility?    │       │                     │    │
│  │              │ - SAE/WPA3 support?     │       │                     │    │
│  │              │ - RADIUS reachable?     │       │                     │    │
│  │              │ - Certificate valid?    │       │                     │    │
│  │              └─────────────────────────┘       │                     │    │
│  │                                                ▼                     │    │
│  │                                  ┌────────────────────────┐          │    │
│  │                                  │ Association fails?     │          │    │
│  │                                  └────────────────────────┘          │    │
│  │                                        │           │                 │    │
│  │                                       Yes          No                │    │
│  │                                        │           │                 │    │
│  │                                        ▼           ▼                 │    │
│  │                                  ┌─────────────────────────┐         │    │
│  │                                  │ Check:                  │         │    │
│  │                                  │ - Max clients reached?  │         │    │
│  │                                  │ - MAC filter blocking?  │         │    │
│  │                                  │ - Capability mismatch?  │         │    │
│  │                                  │ - HT/VHT/HE required?   │         │    │
│  │                                  └─────────────────────────┘         │    │
│  │                                                │                     │    │
│  │                                                ▼                     │    │
│  │                                  ┌────────────────────────┐          │    │
│  │                                  │ 4-Way Handshake fails? │          │    │
│  │                                  └────────────────────────┘          │    │
│  │                                        │           │                 │    │
│  │                                       Yes          No                │    │
│  │                                        │           │                 │    │
│  │                                        ▼           ▼                 │    │
│  │                                  ┌─────────────────────────┐         │    │
│  │                                  │ Check:                  │         │    │
│  │                                  │ - PMK mismatch?         │         │    │
│  │                                  │ - Timeout too short?    │         │    │
│  │                                  │ - MIC failure?          │         │    │
│  │                                  │ - Replay counter?       │         │    │
│  │                                  └─────────────────────────┘         │    │
│  │                                                │                     │    │
│  │                                                ▼                     │    │
│  │                                  ┌────────────────────────┐          │    │
│  │                                  │ DHCP fails?            │          │    │
│  │                                  └────────────────────────┘          │    │
│  │                                        │           │                 │    │
│  │                                       Yes          No                │    │
│  │                                        │           │                 │    │
│  │                                        ▼           ▼                 │    │
│  │                                  ┌─────────────────────────┐         │    │
│  │                                  │ Check:                  │         │    │
│  │                                  │ - DHCP server running?  │         │    │
│  │                                  │ - IP pool exhausted?    │         │    │
│  │                                  │ - VLAN configured?      │         │    │
│  │                                  │ - DHCP relay working?   │         │    │
│  │                                  └─────────────────────────┘         │    │
│  │                                                │                     │    │
│  │                                                ▼                     │    │
│  │                                  ┌────────────────────────┐          │    │
│  │                                  │ Connected Successfully │          │    │
│  │                                  └────────────────────────┘          │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### AU.2 Slow Performance Decision Tree

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    SLOW PERFORMANCE DECISION TREE                            │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │                    Slow WiFi Performance                             │    │
│  │                           │                                          │    │
│  │                           ▼                                          │    │
│  │              ┌────────────────────────┐                              │    │
│  │              │ Check signal strength  │                              │    │
│  │              └────────────────────────┘                              │    │
│  │                    │           │                                     │    │
│  │              RSSI < -70 dBm   RSSI > -70 dBm                         │    │
│  │                    │           │                                     │    │
│  │                    ▼           ▼                                     │    │
│  │              ┌─────────────────────────┐  ┌─────────┐                │    │
│  │              │ Actions:                │  │ Step 2  │                │    │
│  │              │ - Move closer to AP     │  └─────────┘                │    │
│  │              │ - Add more APs          │       │                     │    │
│  │              │ - Increase TX power     │       │                     │    │
│  │              │ - Use directional ant.  │       │                     │    │
│  │              │ - Remove obstacles      │       │                     │    │
│  │              └─────────────────────────┘       │                     │    │
│  │                                                ▼                     │    │
│  │                                  ┌────────────────────────┐          │    │
│  │                                  │ Check channel util.    │          │    │
│  │                                  └────────────────────────┘          │    │
│  │                                        │           │                 │    │
│  │                                    > 70%        < 70%                │    │
│  │                                        │           │                 │    │
│  │                                        ▼           ▼                 │    │
│  │                                  ┌─────────────────────────┐         │    │
│  │                                  │ Actions:                │         │    │
│  │                                  │ - Change channel        │         │    │
│  │                                  │ - Use 5/6 GHz band      │         │    │
│  │                                  │ - Enable band steering  │         │    │
│  │                                  │ - Add more APs          │         │    │
│  │                                  │ - Enable load balancing │         │    │
│  │                                  └─────────────────────────┘         │    │
│  │                                                │                     │    │
│  │                                                ▼                     │    │
│  │                                  ┌────────────────────────┐          │    │
│  │                                  │ Check client count     │          │    │
│  │                                  └────────────────────────┘          │    │
│  │                                        │           │                 │    │
│  │                                    > 50         < 50                 │    │
│  │                                        │           │                 │    │
│  │                                        ▼           ▼                 │    │
│  │                                  ┌─────────────────────────┐         │    │
│  │                                  │ Actions:                │         │    │
│  │                                  │ - Add more APs          │         │    │
│  │                                  │ - Enable OFDMA          │         │    │
│  │                                  │ - Enable MU-MIMO        │         │    │
│  │                                  │ - Limit max clients     │         │    │
│  │                                  └─────────────────────────┘         │    │
│  │                                                │                     │    │
│  │                                                ▼                     │    │
│  │                                  ┌────────────────────────┐          │    │
│  │                                  │ Check for interference │          │    │
│  │                                  └────────────────────────┘          │    │
│  │                                        │           │                 │    │
│  │                                  Interference   No interference      │    │
│  │                                        │           │                 │    │
│  │                                        ▼           ▼                 │    │
│  │                                  ┌─────────────────────────┐         │    │
│  │                                  │ Actions:                │         │    │
│  │                                  │ - Identify source       │         │    │
│  │                                  │ - Change channel        │         │    │
│  │                                  │ - Use 5/6 GHz           │         │    │
│  │                                  │ - Enable DFS            │         │    │
│  │                                  │ - Relocate AP           │         │    │
│  │                                  └─────────────────────────┘         │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Appendix AV: Protocol Timing Diagrams

### AV.1 Complete Connection Timing

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    COMPLETE CONNECTION TIMING                                │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  Time (ms)  Client                    AP                    RADIUS          │
│  ─────────  ──────                    ──                    ──────          │
│                                                                              │
│     0       │                         │                         │           │
│             │ ──── Probe Request ───> │                         │           │
│     5       │ <─── Probe Response ─── │                         │           │
│             │                         │                         │           │
│    10       │ ──── Auth Request ────> │                         │           │
│    15       │ <─── Auth Response ──── │                         │           │
│             │                         │                         │           │
│    20       │ ──── Assoc Request ───> │                         │           │
│    25       │ <─── Assoc Response ─── │                         │           │
│             │                         │                         │           │
│    30       │ <─── EAP-Request/ID ─── │                         │           │
│    35       │ ──── EAP-Response/ID ─> │                         │           │
│    40       │                         │ ── Access-Request ────> │           │
│    50       │                         │ <── Access-Challenge ── │           │
│    55       │ <─── EAP-Request/TLS ── │                         │           │
│             │                         │                         │           │
│   ...       │     (TLS Handshake)     │                         │           │
│             │                         │                         │           │
│   300       │ ──── EAP-Response ────> │                         │           │
│   310       │                         │ ── Access-Request ────> │           │
│   320       │                         │ <── Access-Accept ───── │           │
│   325       │ <─── EAP-Success ────── │                         │           │
│             │                         │                         │           │
│   330       │ <─── EAPOL-Key M1 ───── │                         │           │
│   335       │ ──── EAPOL-Key M2 ────> │                         │           │
│   340       │ <─── EAPOL-Key M3 ───── │                         │           │
│   345       │ ──── EAPOL-Key M4 ────> │                         │           │
│             │                         │                         │           │
│   350       │ ──── DHCP Discover ───> │                         │           │
│   360       │ <─── DHCP Offer ─────── │                         │           │
│   370       │ ──── DHCP Request ────> │                         │           │
│   380       │ <─── DHCP ACK ───────── │                         │           │
│             │                         │                         │           │
│   400       │ ════ Connected ═════════│                         │           │
│             │                         │                         │           │
│                                                                              │
│  Total Connection Time: ~400 ms (WPA2-Enterprise with EAP-TLS)               │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### AV.2 Fast Transition Timing

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    FAST TRANSITION TIMING                                    │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  Time (ms)  Client                    Target AP              Current AP     │
│  ─────────  ──────                    ─────────              ──────────     │
│                                                                              │
│     0       │                         │                         │           │
│             │ ──── FT Auth Request ─> │                         │           │
│     5       │                         │ ─── PMK-R1 Request ───> │           │
│    10       │                         │ <── PMK-R1 Response ─── │           │
│    15       │ <─── FT Auth Response ─ │                         │           │
│             │                         │                         │           │
│    20       │ ──── Reassoc Request ─> │                         │           │
│    25       │ <─── Reassoc Response ─ │                         │           │
│             │                         │                         │           │
│    30       │ ════ Connected ═════════│                         │           │
│             │                         │                         │           │
│                                                                              │
│  Total Roaming Time: ~30 ms (802.11r Over-the-Air)                           │
│                                                                              │
│  ───────────────────────────────────────────────────────────────────────    │
│                                                                              │
│  Over-the-DS Variant:                                                        │
│                                                                              │
│  Time (ms)  Client                    Target AP              Current AP     │
│  ─────────  ──────                    ─────────              ──────────     │
│                                                                              │
│     0       │                         │                         │           │
│             │ ──── FT Request ──────────────────────────────> │           │
│     5       │                         │ <── FT Request ─────── │           │
│    10       │                         │ ─── FT Response ─────> │           │
│    15       │ <─── FT Response ─────────────────────────────── │           │
│             │                         │                         │           │
│    20       │ (Channel Switch)        │                         │           │
│             │                         │                         │           │
│    25       │ ──── Reassoc Request ─> │                         │           │
│    30       │ <─── Reassoc Response ─ │                         │           │
│             │                         │                         │           │
│    35       │ ════ Connected ═════════│                         │           │
│             │                         │                         │           │
│                                                                              │
│  Total Roaming Time: ~35 ms (802.11r Over-the-DS)                            │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Appendix AW: QoS and WMM Configuration

### AW.1 WMM Access Categories

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    WMM ACCESS CATEGORIES                                     │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  Access Category Mapping:                                                    │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  ┌────────────────────────────────────────────────────────────┐     │    │
│  │  │ AC      Priority   DSCP Values        Applications         │     │    │
│  │  │ ──      ────────   ───────────        ────────────         │     │    │
│  │  │ AC_VO   Highest    46 (EF), 48        VoIP, Video Call     │     │    │
│  │  │ AC_VI   High       34 (AF41), 36      Video Streaming      │     │    │
│  │  │ AC_BE   Normal     0 (BE), 24         Web, Email           │     │    │
│  │  │ AC_BK   Low        8, 10              Background Downloads │     │    │
│  │  └────────────────────────────────────────────────────────────┘     │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  802.1p to WMM Mapping:                                                      │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  ┌────────────────────────────────────────────────────────────┐     │    │
│  │  │ 802.1p   UP    Access Category   Description               │     │    │
│  │  │ ──────   ──    ───────────────   ───────────               │     │    │
│  │  │ 0        0     AC_BE             Best Effort               │     │    │
│  │  │ 1        1     AC_BK             Background                │     │    │
│  │  │ 2        2     AC_BK             Background                │     │    │
│  │  │ 3        3     AC_BE             Best Effort               │     │    │
│  │  │ 4        4     AC_VI             Video                     │     │    │
│  │  │ 5        5     AC_VI             Video                     │     │    │
│  │  │ 6        6     AC_VO             Voice                     │     │    │
│  │  │ 7        7     AC_VO             Voice                     │     │    │
│  │  └────────────────────────────────────────────────────────────┘     │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  EDCA Parameters:                                                            │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  ┌────────────────────────────────────────────────────────────┐     │    │
│  │  │ AC      CWmin   CWmax   AIFSN   TXOP Limit                 │     │    │
│  │  │ ──      ─────   ─────   ─────   ──────────                 │     │    │
│  │  │ AC_BK   15      1023    7       0                          │     │    │
│  │  │ AC_BE   15      1023    3       0                          │     │    │
│  │  │ AC_VI   7       15      2       3.008 ms                   │     │    │
│  │  │ AC_VO   3       7       2       1.504 ms                   │     │    │
│  │  └────────────────────────────────────────────────────────────┘     │    │
│  │                                                                      │    │
│  │  CWmin/CWmax: Contention Window (slots)                              │    │
│  │  AIFSN: Arbitration Inter-Frame Space Number                         │    │
│  │  TXOP: Transmission Opportunity                                      │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### AW.2 WMM Power Save (U-APSD)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    WMM POWER SAVE (U-APSD)                                   │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  U-APSD Operation:                                                           │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  Client                                AP                            │    │
│  │     │                                   │                            │    │
│  │     │ ──── Association (U-APSD) ──────> │                            │    │
│  │     │                                   │                            │    │
│  │     │ (Client enters power save)        │                            │    │
│  │     │                                   │                            │    │
│  │     │                                   │ (AP buffers frames)        │    │
│  │     │                                   │                            │    │
│  │     │ ──── Trigger Frame (QoS Null) ──> │                            │    │
│  │     │                                   │                            │    │
│  │     │ <─── Buffered Data (EOSP=0) ───── │                            │    │
│  │     │ <─── Buffered Data (EOSP=0) ───── │                            │    │
│  │     │ <─── Buffered Data (EOSP=1) ───── │                            │    │
│  │     │                                   │                            │    │
│  │     │ (Client returns to power save)    │                            │    │
│  │     │                                   │                            │    │
│  │                                                                      │    │
│  │  EOSP = End of Service Period                                        │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  U-APSD Configuration:                                                       │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  # hostapd.conf                                                      │    │
│  │  wmm_enabled=1                                                       │    │
│  │  uapsd_advertisement_enabled=1                                       │    │
│  │                                                                      │    │
│  │  # Per-AC U-APSD settings                                            │    │
│  │  wmm_ac_bk_aifs=7                                                    │    │
│  │  wmm_ac_bk_cwmin=4                                                   │    │
│  │  wmm_ac_bk_cwmax=10                                                  │    │
│  │  wmm_ac_bk_txop_limit=0                                              │    │
│  │  wmm_ac_bk_acm=0                                                     │    │
│  │                                                                      │    │
│  │  wmm_ac_be_aifs=3                                                    │    │
│  │  wmm_ac_be_cwmin=4                                                   │    │
│  │  wmm_ac_be_cwmax=10                                                  │    │
│  │  wmm_ac_be_txop_limit=0                                              │    │
│  │  wmm_ac_be_acm=0                                                     │    │
│  │                                                                      │    │
│  │  wmm_ac_vi_aifs=2                                                    │    │
│  │  wmm_ac_vi_cwmin=3                                                   │    │
│  │  wmm_ac_vi_cwmax=4                                                   │    │
│  │  wmm_ac_vi_txop_limit=94                                             │    │
│  │  wmm_ac_vi_acm=0                                                     │    │
│  │                                                                      │    │
│  │  wmm_ac_vo_aifs=2                                                    │    │
│  │  wmm_ac_vo_cwmin=2                                                   │    │
│  │  wmm_ac_vo_cwmax=3                                                   │    │
│  │  wmm_ac_vo_txop_limit=47                                             │    │
│  │  wmm_ac_vo_acm=0                                                     │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Appendix AX: Network Deployment Topologies

### AX.1 Standalone AP Deployment

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    STANDALONE AP DEPLOYMENT                                  │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │                         ┌─────────────┐                              │    │
│  │                         │   Internet  │                              │    │
│  │                         └──────┬──────┘                              │    │
│  │                                │                                     │    │
│  │                         ┌──────┴──────┐                              │    │
│  │                         │   Router    │                              │    │
│  │                         │  (Gateway)  │                              │    │
│  │                         └──────┬──────┘                              │    │
│  │                                │                                     │    │
│  │                         ┌──────┴──────┐                              │    │
│  │                         │   Switch    │                              │    │
│  │                         └──────┬──────┘                              │    │
│  │                                │                                     │    │
│  │              ┌─────────────────┼─────────────────┐                   │    │
│  │              │                 │                 │                   │    │
│  │       ┌──────┴──────┐   ┌──────┴──────┐   ┌──────┴──────┐            │    │
│  │       │    AP 1     │   │    AP 2     │   │    AP 3     │            │    │
│  │       │ (Standalone)│   │ (Standalone)│   │ (Standalone)│            │    │
│  │       └──────┬──────┘   └──────┬──────┘   └──────┬──────┘            │    │
│  │              │                 │                 │                   │    │
│  │         ┌────┴────┐       ┌────┴────┐       ┌────┴────┐              │    │
│  │         │ Clients │       │ Clients │       │ Clients │              │    │
│  │         └─────────┘       └─────────┘       └─────────┘              │    │
│  │                                                                      │    │
│  │  Characteristics:                                                    │    │
│  │  - Each AP configured independently                                  │    │
│  │  - No centralized management                                         │    │
│  │  - Limited roaming support                                           │    │
│  │  - Best for: Small deployments, home networks                        │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### AX.2 Controller-Based Deployment

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    CONTROLLER-BASED DEPLOYMENT                               │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │                         ┌─────────────┐                              │    │
│  │                         │   Internet  │                              │    │
│  │                         └──────┬──────┘                              │    │
│  │                                │                                     │    │
│  │                         ┌──────┴──────┐                              │    │
│  │                         │   Router    │                              │    │
│  │                         └──────┬──────┘                              │    │
│  │                                │                                     │    │
│  │              ┌─────────────────┼─────────────────┐                   │    │
│  │              │                 │                 │                   │    │
│  │       ┌──────┴──────┐   ┌──────┴──────┐   ┌──────┴──────┐            │    │
│  │       │  Wireless   │   │   Switch    │   │   RADIUS    │            │    │
│  │       │ Controller  │   │             │   │   Server    │            │    │
│  │       └──────┬──────┘   └──────┬──────┘   └─────────────┘            │    │
│  │              │                 │                                     │    │
│  │              │    ┌────────────┼────────────┐                        │    │
│  │              │    │            │            │                        │    │
│  │              │ ┌──┴───┐    ┌───┴──┐    ┌───┴──┐                      │    │
│  │              └─│ AP 1 │    │ AP 2 │    │ AP 3 │                      │    │
│  │                │(Thin)│    │(Thin)│    │(Thin)│                      │    │
│  │                └──┬───┘    └──┬───┘    └──┬───┘                      │    │
│  │                   │           │           │                          │    │
│  │              ┌────┴────┐ ┌────┴────┐ ┌────┴────┐                     │    │
│  │              │ Clients │ │ Clients │ │ Clients │                     │    │
│  │              └─────────┘ └─────────┘ └─────────┘                     │    │
│  │                                                                      │    │
│  │  Characteristics:                                                    │    │
│  │  - Centralized configuration and management                          │    │
│  │  - Controller handles authentication, roaming                        │    │
│  │  - CAPWAP/LWAPP tunnel between AP and controller                     │    │
│  │  - Best for: Enterprise, large deployments                           │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### AX.3 Cloud-Managed Deployment

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    CLOUD-MANAGED DEPLOYMENT                                  │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │                    ┌─────────────────────────┐                       │    │
│  │                    │     Cloud Dashboard     │                       │    │
│  │                    │   (Management Portal)   │                       │    │
│  │                    └───────────┬─────────────┘                       │    │
│  │                                │                                     │    │
│  │                         ┌──────┴──────┐                              │    │
│  │                         │   Internet  │                              │    │
│  │                         └──────┬──────┘                              │    │
│  │                                │                                     │    │
│  │         ┌──────────────────────┼──────────────────────┐              │    │
│  │         │                      │                      │              │    │
│  │  ┌──────┴──────┐        ┌──────┴──────┐        ┌──────┴──────┐       │    │
│  │  │   Site A    │        │   Site B    │        │   Site C    │       │    │
│  │  │   Router    │        │   Router    │        │   Router    │       │    │
│  │  └──────┬──────┘        └──────┬──────┘        └──────┬──────┘       │    │
│  │         │                      │                      │              │    │
│  │    ┌────┴────┐            ┌────┴────┐            ┌────┴────┐         │    │
│  │    │   APs   │            │   APs   │            │   APs   │         │    │
│  │    │ (Cloud) │            │ (Cloud) │            │ (Cloud) │         │    │
│  │    └────┬────┘            └────┬────┘            └────┬────┘         │    │
│  │         │                      │                      │              │    │
│  │    ┌────┴────┐            ┌────┴────┐            ┌────┴────┐         │    │
│  │    │ Clients │            │ Clients │            │ Clients │         │    │
│  │    └─────────┘            └─────────┘            └─────────┘         │    │
│  │                                                                      │    │
│  │  Characteristics:                                                    │    │
│  │  - Management via cloud portal                                       │    │
│  │  - APs are "thick" (local processing)                                │    │
│  │  - Configuration pushed from cloud                                   │    │
│  │  - Multi-site management                                             │    │
│  │  - Best for: Distributed enterprises, MSPs                           │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Appendix AY: Compliance and Regulatory Reference

### AY.1 Regulatory Compliance Requirements

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    REGULATORY COMPLIANCE REQUIREMENTS                        │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  FCC (United States):                                                        │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  ┌────────────────────────────────────────────────────────────┐     │    │
│  │  │ Requirement              Description                       │     │    │
│  │  │ ───────────              ───────────                       │     │    │
│  │  │ Part 15.247              2.4 GHz ISM band rules            │     │    │
│  │  │ Part 15.407              5 GHz U-NII band rules            │     │    │
│  │  │ Part 15.407(h)           6 GHz U-NII band rules            │     │    │
│  │  │ DFS                      Required for U-NII-2 bands        │     │    │
│  │  │ TPC                      Required for U-NII-2/3 bands      │     │    │
│  │  │ Max EIRP (2.4 GHz)       36 dBm (4W)                       │     │    │
│  │  │ Max EIRP (5 GHz Indoor)  30 dBm (1W)                       │     │    │
│  │  │ Max EIRP (5 GHz Outdoor) 36 dBm (4W)                       │     │    │
│  │  │ Max EIRP (6 GHz LPI)     30 dBm (1W)                       │     │    │
│  │  │ Max EIRP (6 GHz SP)      36 dBm (4W)                       │     │    │
│  │  └────────────────────────────────────────────────────────────┘     │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  ETSI (Europe):                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  ┌────────────────────────────────────────────────────────────┐     │    │
│  │  │ Requirement              Description                       │     │    │
│  │  │ ───────────              ───────────                       │     │    │
│  │  │ EN 300 328               2.4 GHz band rules                │     │    │
│  │  │ EN 301 893               5 GHz band rules                  │     │    │
│  │  │ EN 303 687               6 GHz band rules                  │     │    │
│  │  │ DFS                      Required for 5150-5350 MHz        │     │    │
│  │  │ TPC                      Required for 5 GHz                │     │    │
│  │  │ Max EIRP (2.4 GHz)       20 dBm (100 mW)                   │     │    │
│  │  │ Max EIRP (5 GHz Indoor)  23 dBm (200 mW)                   │     │    │
│  │  │ Max EIRP (5 GHz Outdoor) 30 dBm (1W) with TPC/DFS          │     │    │
│  │  │ Max EIRP (6 GHz LPI)     23 dBm (200 mW)                   │     │    │
│  │  │ Max EIRP (6 GHz VLP)     14 dBm (25 mW)                    │     │    │
│  │  └────────────────────────────────────────────────────────────┘     │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  Industry Compliance:                                                        │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  ┌────────────────────────────────────────────────────────────┐     │    │
│  │  │ Standard                 Description                       │     │    │
│  │  │ ────────                 ───────────                       │     │    │
│  │  │ PCI-DSS                  Payment card industry security    │     │    │
│  │  │ HIPAA                    Healthcare data protection        │     │    │
│  │  │ SOX                      Financial reporting security      │     │    │
│  │  │ GDPR                     EU data protection                │     │    │
│  │  │ FERPA                    Education records privacy         │     │    │
│  │  │ CJIS                     Criminal justice information      │     │    │
│  │  │ NIST 800-53              Federal security controls         │     │    │
│  │  │ ISO 27001                Information security management   │     │    │
│  │  └────────────────────────────────────────────────────────────┘     │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### AY.2 Security Compliance Mapping

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    SECURITY COMPLIANCE MAPPING                               │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  PCI-DSS WiFi Requirements:                                                  │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  ┌────────────────────────────────────────────────────────────┐     │    │
│  │  │ Requirement              WiFi Implementation               │     │    │
│  │  │ ───────────              ────────────────────               │     │    │
│  │  │ 1.2.3                    Segment wireless from CDE         │     │    │
│  │  │ 2.1.1                    Change default passwords          │     │    │
│  │  │ 4.1.1                    Use WPA2/WPA3-Enterprise          │     │    │
│  │  │ 9.1.3                    Restrict physical access to APs   │     │    │
│  │  │ 11.1                     Quarterly wireless scans          │     │    │
│  │  │ 11.1.1                   Rogue AP detection                │     │    │
│  │  │ 11.1.2                   Authorized AP inventory           │     │    │
│  │  └────────────────────────────────────────────────────────────┘     │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  HIPAA WiFi Requirements:                                                    │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  ┌────────────────────────────────────────────────────────────┐     │    │
│  │  │ Requirement              WiFi Implementation               │     │    │
│  │  │ ───────────              ────────────────────               │     │    │
│  │  │ 164.312(a)(1)            Access control (802.1X)           │     │    │
│  │  │ 164.312(a)(2)(i)         Unique user identification        │     │    │
│  │  │ 164.312(b)               Audit controls (RADIUS acct)      │     │    │
│  │  │ 164.312(c)(1)            Integrity (MIC, encryption)       │     │    │
│  │  │ 164.312(d)               Person authentication (EAP)       │     │    │
│  │  │ 164.312(e)(1)            Transmission security (WPA2/3)    │     │    │
│  │  │ 164.312(e)(2)(ii)        Encryption (AES-CCMP/GCMP)        │     │    │
│  │  └────────────────────────────────────────────────────────────┘     │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Appendix AZ: Advanced Debugging Techniques

### AZ.1 Kernel-Level Debugging

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    KERNEL-LEVEL DEBUGGING                                    │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  Enable mac80211 Debug Messages:                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  # Enable all mac80211 debug messages                                │    │
│  │  echo 0xffffffff > /sys/kernel/debug/ieee80211/phy0/mac80211/debug   │    │
│  │                                                                      │    │
│  │  # Enable specific debug categories                                  │    │
│  │  # Bit 0: HT                                                         │    │
│  │  # Bit 1: IBSS                                                       │    │
│  │  # Bit 2: PS                                                         │    │
│  │  # Bit 3: RX                                                         │    │
│  │  # Bit 4: TX                                                         │    │
│  │  # Bit 5: MLME                                                       │    │
│  │  # Bit 6: SCAN                                                       │    │
│  │  # Bit 7: TDLS                                                       │    │
│  │  # Bit 8: MESH                                                       │    │
│  │  # Bit 9: WME                                                        │    │
│  │  # Bit 10: CHAN                                                      │    │
│  │                                                                      │    │
│  │  # Example: Enable MLME and SCAN debug                               │    │
│  │  echo 0x60 > /sys/kernel/debug/ieee80211/phy0/mac80211/debug         │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  Driver-Specific Debug:                                                      │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  # ath10k debug                                                      │    │
│  │  echo 0xffffffff > /sys/kernel/debug/ieee80211/phy0/ath10k/debug_mask│    │
│  │                                                                      │    │
│  │  # ath11k debug                                                      │    │
│  │  echo 0xffffffff > /sys/kernel/debug/ath11k/debug_mask               │    │
│  │                                                                      │    │
│  │  # iwlwifi debug                                                     │    │
│  │  echo 0xffffffff > /sys/module/iwlwifi/parameters/debug              │    │
│  │                                                                      │    │
│  │  # mt76 debug                                                        │    │
│  │  echo 0xffffffff > /sys/kernel/debug/ieee80211/phy0/mt76/debug       │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  View Debug Output:                                                          │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  # View kernel messages in real-time                                 │    │
│  │  dmesg -w | grep -E "(ieee80211|wlan|ath|iwl)"                       │    │
│  │                                                                      │    │
│  │  # View with timestamps                                              │    │
│  │  dmesg -wT | grep -E "(ieee80211|wlan|ath|iwl)"                      │    │
│  │                                                                      │    │
│  │  # Save to file                                                      │    │
│  │  dmesg -wT | grep -E "(ieee80211|wlan)" > /tmp/wifi_debug.log        │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### AZ.2 hostapd Debug Levels

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    HOSTAPD DEBUG LEVELS                                      │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  Debug Level Configuration:                                                  │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  # hostapd.conf                                                      │    │
│  │  logger_syslog=-1                                                    │    │
│  │  logger_syslog_level=0                                               │    │
│  │  logger_stdout=-1                                                    │    │
│  │  logger_stdout_level=0                                               │    │
│  │                                                                      │    │
│  │  # Debug levels:                                                     │    │
│  │  # 0 = verbose (all messages)                                        │    │
│  │  # 1 = debug                                                         │    │
│  │  # 2 = info                                                          │    │
│  │  # 3 = warning                                                       │    │
│  │  # 4 = error                                                         │    │
│  │                                                                      │    │
│  │  # Logger modules (bitmask):                                         │    │
│  │  # -1 = all modules                                                  │    │
│  │  # 0x1 = IEEE 802.11                                                 │    │
│  │  # 0x2 = IEEE 802.1X                                                 │    │
│  │  # 0x4 = RADIUS                                                      │    │
│  │  # 0x8 = WPA                                                         │    │
│  │  # 0x10 = driver interface                                           │    │
│  │  # 0x20 = IAPP                                                       │    │
│  │  # 0x40 = MLME                                                       │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  Run hostapd with Debug Output:                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  # Maximum debug output                                              │    │
│  │  hostapd -dd /etc/hostapd/hostapd.conf                               │    │
│  │                                                                      │    │
│  │  # Debug with timestamps                                             │    │
│  │  hostapd -ddt /etc/hostapd/hostapd.conf                              │    │
│  │                                                                      │    │
│  │  # Debug to file                                                     │    │
│  │  hostapd -dd /etc/hostapd/hostapd.conf > /tmp/hostapd.log 2>&1       │    │
│  │                                                                      │    │
│  │  # Debug specific interface                                          │    │
│  │  hostapd -dd -i wlan0 /etc/hostapd/hostapd.conf                      │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Appendix BA: Client Supplicant Configuration

### BA.1 wpa_supplicant Configuration Examples

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    WPA_SUPPLICANT CONFIGURATION                              │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  WPA2-Personal Configuration:                                                │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  # /etc/wpa_supplicant/wpa_supplicant.conf                           │    │
│  │  ctrl_interface=/var/run/wpa_supplicant                              │    │
│  │  ctrl_interface_group=wheel                                          │    │
│  │  update_config=1                                                     │    │
│  │  country=US                                                          │    │
│  │                                                                      │    │
│  │  network={                                                           │    │
│  │      ssid="MyNetwork"                                                │    │
│  │      psk="MySecurePassword123"                                       │    │
│  │      key_mgmt=WPA-PSK                                                │    │
│  │      proto=RSN                                                       │    │
│  │      pairwise=CCMP                                                   │    │
│  │      group=CCMP                                                      │    │
│  │      priority=1                                                      │    │
│  │  }                                                                   │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  WPA3-Personal (SAE) Configuration:                                          │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  network={                                                           │    │
│  │      ssid="WPA3Network"                                              │    │
│  │      sae_password="MySecurePassword123"                              │    │
│  │      key_mgmt=SAE                                                    │    │
│  │      ieee80211w=2                                                    │    │
│  │      proto=RSN                                                       │    │
│  │      pairwise=CCMP GCMP-256                                          │    │
│  │      group=CCMP GCMP-256                                             │    │
│  │  }                                                                   │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  WPA2-Enterprise (EAP-TLS) Configuration:                                    │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  network={                                                           │    │
│  │      ssid="EnterpriseNetwork"                                        │    │
│  │      key_mgmt=WPA-EAP                                                │    │
│  │      eap=TLS                                                         │    │
│  │      identity="user@example.com"                                     │    │
│  │      ca_cert="/etc/certs/ca.pem"                                     │    │
│  │      client_cert="/etc/certs/client.pem"                             │    │
│  │      private_key="/etc/certs/client.key"                             │    │
│  │      private_key_passwd="keypassword"                                │    │
│  │      domain_suffix_match="example.com"                               │    │
│  │      proto=RSN                                                       │    │
│  │      pairwise=CCMP                                                   │    │
│  │      group=CCMP                                                      │    │
│  │  }                                                                   │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  WPA2-Enterprise (EAP-PEAP) Configuration:                                   │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  network={                                                           │    │
│  │      ssid="EnterpriseNetwork"                                        │    │
│  │      key_mgmt=WPA-EAP                                                │    │
│  │      eap=PEAP                                                        │    │
│  │      identity="user@example.com"                                     │    │
│  │      password="userpassword"                                         │    │
│  │      ca_cert="/etc/certs/ca.pem"                                     │    │
│  │      phase2="auth=MSCHAPV2"                                          │    │
│  │      domain_suffix_match="example.com"                               │    │
│  │      anonymous_identity="anonymous@example.com"                      │    │
│  │      proto=RSN                                                       │    │
│  │      pairwise=CCMP                                                   │    │
│  │      group=CCMP                                                      │    │
│  │  }                                                                   │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  Fast Transition (802.11r) Configuration:                                    │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  network={                                                           │    │
│  │      ssid="FTNetwork"                                                │    │
│  │      psk="MySecurePassword123"                                       │    │
│  │      key_mgmt=FT-PSK WPA-PSK                                         │    │
│  │      proto=RSN                                                       │    │
│  │      pairwise=CCMP                                                   │    │
│  │      group=CCMP                                                      │    │
│  │  }                                                                   │    │
│  │                                                                      │    │
│  │  # For Enterprise with FT                                            │    │
│  │  network={                                                           │    │
│  │      ssid="FTEnterpriseNetwork"                                      │    │
│  │      key_mgmt=FT-EAP WPA-EAP                                         │    │
│  │      eap=TLS                                                         │    │
│  │      identity="user@example.com"                                     │    │
│  │      ca_cert="/etc/certs/ca.pem"                                     │    │
│  │      client_cert="/etc/certs/client.pem"                             │    │
│  │      private_key="/etc/certs/client.key"                             │    │
│  │      proto=RSN                                                       │    │
│  │      pairwise=CCMP                                                   │    │
│  │      group=CCMP                                                      │    │
│  │  }                                                                   │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  Hotspot 2.0 (Passpoint) Configuration:                                     │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  cred={                                                              │    │
│  │      realm="example.com"                                             │    │
│  │      username="user@example.com"                                     │    │
│  │      password="userpassword"                                         │    │
│  │      ca_cert="/etc/certs/ca.pem"                                     │    │
│  │      domain="example.com"                                            │    │
│  │      roaming_consortium=001122334455                                 │    │
│  │      eap=TTLS                                                        │    │
│  │      phase2="auth=MSCHAPV2"                                          │    │
│  │  }                                                                   │    │
│  │                                                                      │    │
│  │  # Enable Hotspot 2.0                                                │    │
│  │  interworking=1                                                      │    │
│  │  hs20=1                                                              │    │
│  │  auto_interworking=1                                                 │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### BA.2 wpa_supplicant Commands

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    WPA_SUPPLICANT COMMANDS                                   │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  Starting wpa_supplicant:                                                    │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  # Start with config file                                            │    │
│  │  wpa_supplicant -B -i wlan0 -c /etc/wpa_supplicant/wpa_supplicant.conf│   │
│  │                                                                      │    │
│  │  # Start with debug output                                           │    │
│  │  wpa_supplicant -dd -i wlan0 -c /etc/wpa_supplicant/wpa_supplicant.conf│  │
│  │                                                                      │    │
│  │  # Start with nl80211 driver                                         │    │
│  │  wpa_supplicant -B -D nl80211 -i wlan0 -c /etc/wpa_supplicant/wpa.conf│   │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  wpa_cli Commands:                                                           │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  # Interactive mode                                                  │    │
│  │  wpa_cli -i wlan0                                                    │    │
│  │                                                                      │    │
│  │  # Status commands                                                   │    │
│  │  wpa_cli -i wlan0 status                                             │    │
│  │  wpa_cli -i wlan0 status verbose                                     │    │
│  │                                                                      │    │
│  │  # Scan commands                                                     │    │
│  │  wpa_cli -i wlan0 scan                                               │    │
│  │  wpa_cli -i wlan0 scan_results                                       │    │
│  │                                                                      │    │
│  │  # Network management                                                │    │
│  │  wpa_cli -i wlan0 list_networks                                      │    │
│  │  wpa_cli -i wlan0 select_network 0                                   │    │
│  │  wpa_cli -i wlan0 enable_network 0                                   │    │
│  │  wpa_cli -i wlan0 disable_network 0                                  │    │
│  │  wpa_cli -i wlan0 remove_network 0                                   │    │
│  │                                                                      │    │
│  │  # Add new network                                                   │    │
│  │  wpa_cli -i wlan0 add_network                                        │    │
│  │  wpa_cli -i wlan0 set_network 0 ssid '"MyNetwork"'                   │    │
│  │  wpa_cli -i wlan0 set_network 0 psk '"MyPassword"'                   │    │
│  │  wpa_cli -i wlan0 enable_network 0                                   │    │
│  │  wpa_cli -i wlan0 save_config                                        │    │
│  │                                                                      │    │
│  │  # Connection commands                                               │    │
│  │  wpa_cli -i wlan0 reassociate                                        │    │
│  │  wpa_cli -i wlan0 disconnect                                         │    │
│  │  wpa_cli -i wlan0 reconnect                                          │    │
│  │                                                                      │    │
│  │  # Roaming commands                                                  │    │
│  │  wpa_cli -i wlan0 bss_expire_age 180                                 │    │
│  │  wpa_cli -i wlan0 roam &lt;BSSID&gt;                                       │    │
│  │  wpa_cli -i wlan0 ft_ds &lt;BSSID&gt;                                      │    │
│  │                                                                      │    │
│  │  # Signal quality                                                    │    │
│  │  wpa_cli -i wlan0 signal_poll                                        │    │
│  │                                                                      │    │
│  │  # Debug                                                             │    │
│  │  wpa_cli -i wlan0 log_level DEBUG                                    │    │
│  │  wpa_cli -i wlan0 log_level INFO                                     │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Appendix BB: VLAN and Network Segmentation

### BB.1 Dynamic VLAN Assignment

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    DYNAMIC VLAN ASSIGNMENT                                   │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  RADIUS-Based VLAN Assignment:                                               │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  Client                AP                 RADIUS                     │    │
│  │     │                   │                    │                       │    │
│  │     │ ── Auth Request ─>│                    │                       │    │
│  │     │                   │ ── Access-Req ───> │                       │    │
│  │     │                   │                    │                       │    │
│  │     │                   │ <── Access-Accept ─│                       │    │
│  │     │                   │     Tunnel-Type=VLAN                       │    │
│  │     │                   │     Tunnel-Medium-Type=802                 │    │
│  │     │                   │     Tunnel-Private-Group-Id=100            │    │
│  │     │                   │                    │                       │    │
│  │     │ <── Auth Success ─│                    │                       │    │
│  │     │                   │                    │                       │    │
│  │     │ (Client placed on VLAN 100)            │                       │    │
│  │     │                   │                    │                       │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  RADIUS Attributes for VLAN:                                                 │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  # FreeRADIUS users file                                             │    │
│  │  user1  Cleartext-Password := "password1"                            │    │
│  │         Tunnel-Type = VLAN,                                          │    │
│  │         Tunnel-Medium-Type = IEEE-802,                               │    │
│  │         Tunnel-Private-Group-Id = 100                                │    │
│  │                                                                      │    │
│  │  user2  Cleartext-Password := "password2"                            │    │
│  │         Tunnel-Type = VLAN,                                          │    │
│  │         Tunnel-Medium-Type = IEEE-802,                               │    │
│  │         Tunnel-Private-Group-Id = 200                                │    │
│  │                                                                      │    │
│  │  # Group-based VLAN assignment                                       │    │
│  │  DEFAULT  Ldap-Group == "employees"                                  │    │
│  │           Tunnel-Type = VLAN,                                        │    │
│  │           Tunnel-Medium-Type = IEEE-802,                             │    │
│  │           Tunnel-Private-Group-Id = 100                              │    │
│  │                                                                      │    │
│  │  DEFAULT  Ldap-Group == "guests"                                     │    │
│  │           Tunnel-Type = VLAN,                                        │    │
│  │           Tunnel-Medium-Type = IEEE-802,                             │    │
│  │           Tunnel-Private-Group-Id = 999                              │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  hostapd VLAN Configuration:                                                 │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  # hostapd.conf                                                      │    │
│  │  dynamic_vlan=1                                                      │    │
│  │  vlan_file=/etc/hostapd/hostapd.vlan                                 │    │
│  │  vlan_bridge=br                                                      │    │
│  │  vlan_naming=1                                                       │    │
│  │                                                                      │    │
│  │  # /etc/hostapd/hostapd.vlan                                         │    │
│  │  # Format: vlan_id interface_name                                    │    │
│  │  100 vlan100                                                         │    │
│  │  200 vlan200                                                         │    │
│  │  999 vlan999                                                         │    │
│  │  *  vlan#                                                            │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### BB.2 Network Segmentation Strategies

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    NETWORK SEGMENTATION STRATEGIES                           │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  Role-Based Segmentation:                                                    │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  ┌────────────────────────────────────────────────────────────┐     │    │
│  │  │ Role          VLAN    SSID              Access Level       │     │    │
│  │  │ ────          ────    ────              ────────────       │     │    │
│  │  │ Employees     100     Corporate         Full network       │     │    │
│  │  │ Contractors   200     Contractor        Limited servers    │     │    │
│  │  │ Guests        999     Guest             Internet only      │     │    │
│  │  │ IoT Devices   300     IoT               Isolated           │     │    │
│  │  │ VoIP          400     Voice             Voice servers      │     │    │
│  │  │ Management    10      Management        Network devices    │     │    │
│  │  └────────────────────────────────────────────────────────────┘     │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  Segmentation Architecture:                                                  │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │                         ┌─────────────┐                              │    │
│  │                         │   Firewall  │                              │    │
│  │                         └──────┬──────┘                              │    │
│  │                                │                                     │    │
│  │              ┌─────────────────┼─────────────────┐                   │    │
│  │              │                 │                 │                   │    │
│  │       ┌──────┴──────┐   ┌──────┴──────┐   ┌──────┴──────┐            │    │
│  │       │  VLAN 100   │   │  VLAN 200   │   │  VLAN 999   │            │    │
│  │       │  Corporate  │   │ Contractor  │   │   Guest     │            │    │
│  │       └──────┬──────┘   └──────┬──────┘   └──────┬──────┘            │    │
│  │              │                 │                 │                   │    │
│  │       ┌──────┴──────┐   ┌──────┴──────┐   ┌──────┴──────┐            │    │
│  │       │    APs      │   │    APs      │   │    APs      │            │    │
│  │       │ (Tagged)    │   │ (Tagged)    │   │ (Tagged)    │            │    │
│  │       └──────┬──────┘   └──────┬──────┘   └──────┬──────┘            │    │
│  │              │                 │                 │                   │    │
│  │       ┌──────┴──────┐   ┌──────┴──────┐   ┌──────┴──────┐            │    │
│  │       │  Employees  │   │ Contractors │   │   Guests    │            │    │
│  │       └─────────────┘   └─────────────┘   └─────────────┘            │    │
│  │                                                                      │    │
│  │  Firewall Rules:                                                     │    │
│  │  - VLAN 100 → All internal resources                                 │    │
│  │  - VLAN 200 → Specific servers only                                  │    │
│  │  - VLAN 999 → Internet only (no internal access)                     │    │
│  │  - Inter-VLAN routing controlled by firewall                         │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Appendix BC: Rate Limiting and Traffic Shaping

### BC.1 Per-Client Rate Limiting

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    PER-CLIENT RATE LIMITING                                  │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  RADIUS-Based Rate Limiting:                                                 │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  # FreeRADIUS users file                                             │    │
│  │  user1  Cleartext-Password := "password1"                            │    │
│  │         WISPr-Bandwidth-Max-Down = 10000000,                         │    │
│  │         WISPr-Bandwidth-Max-Up = 5000000                             │    │
│  │                                                                      │    │
│  │  # Arista-specific attributes                                        │    │
│  │  user2  Cleartext-Password := "password2"                            │    │
│  │         Arista-BW-Limit-Down = 20000,                                │    │
│  │         Arista-BW-Limit-Up = 10000                                   │    │
│  │                                                                      │    │
│  │  # Cisco-specific attributes                                         │    │
│  │  user3  Cleartext-Password := "password3"                            │    │
│  │         Cisco-AVPair = "subscriber:sub-qos-policy-in=10Mbps",        │    │
│  │         Cisco-AVPair = "subscriber:sub-qos-policy-out=5Mbps"         │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  CoA-Based Rate Limiting:                                                    │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  # Send CoA to change bandwidth                                      │    │
│  │  echo "User-Name=user1,                                              │    │
│  │        WISPr-Bandwidth-Max-Down=5000000,                             │    │
│  │        WISPr-Bandwidth-Max-Up=2500000" | \                           │    │
│  │  radclient -x 192.168.1.1:3799 coa secret                            │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  Linux tc-based Rate Limiting:                                               │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  # Create HTB qdisc                                                  │    │
│  │  tc qdisc add dev wlan0 root handle 1: htb default 30                │    │
│  │                                                                      │    │
│  │  # Create root class                                                 │    │
│  │  tc class add dev wlan0 parent 1: classid 1:1 htb rate 100mbit       │    │
│  │                                                                      │    │
│  │  # Create per-client class (10 Mbps limit)                           │    │
│  │  tc class add dev wlan0 parent 1:1 classid 1:10 htb rate 10mbit      │    │
│  │                                                                      │    │
│  │  # Filter traffic by MAC address                                     │    │
│  │  tc filter add dev wlan0 parent 1: protocol ip prio 1 \              │    │
│  │     u32 match ether src 00:11:22:33:44:55 flowid 1:10                │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### BC.2 Airtime Fairness

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    AIRTIME FAIRNESS                                          │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  Problem Without Airtime Fairness:                                           │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  Client A (54 Mbps)     Client B (6 Mbps)                            │    │
│  │       │                      │                                       │    │
│  │       │ ─── 1 packet ──────> │                                       │    │
│  │       │                      │ ─── 1 packet (9x longer) ───>         │    │
│  │       │ ─── 1 packet ──────> │                                       │    │
│  │       │                      │ ─── 1 packet (9x longer) ───>         │    │
│  │       │                      │                                       │    │
│  │  Result: Client B uses 90% of airtime, Client A gets 10%             │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  With Airtime Fairness:                                                      │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  Client A (54 Mbps)     Client B (6 Mbps)                            │    │
│  │       │                      │                                       │    │
│  │       │ ─── 9 packets ─────> │                                       │    │
│  │       │                      │ ─── 1 packet ───>                     │    │
│  │       │ ─── 9 packets ─────> │                                       │    │
│  │       │                      │ ─── 1 packet ───>                     │    │
│  │       │                      │                                       │    │
│  │  Result: Each client gets 50% of airtime                             │    │
│  │  Client A throughput: ~27 Mbps                                       │    │
│  │  Client B throughput: ~3 Mbps                                        │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  Configuration:                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  # hostapd.conf                                                      │    │
│  │  # Enable airtime fairness (driver-dependent)                        │    │
│  │  airtime_mode=2                                                      │    │
│  │                                                                      │    │
│  │  # Airtime modes:                                                    │    │
│  │  # 0 = disabled                                                      │    │
│  │  # 1 = static configuration                                          │    │
│  │  # 2 = dynamic (per-station)                                         │    │
│  │  # 3 = limit (enforce maximum airtime)                               │    │
│  │                                                                      │    │
│  │  # Per-BSS airtime weight                                            │    │
│  │  airtime_bss_weight=256                                              │    │
│  │                                                                      │    │
│  │  # Per-station airtime limit (microseconds per second)               │    │
│  │  airtime_bss_limit=500000                                            │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Appendix BD: High Availability and Redundancy

### BD.1 AP Failover Mechanisms

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    AP FAILOVER MECHANISMS                                    │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  Controller Failover:                                                        │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │                    ┌─────────────────────────┐                       │    │
│  │                    │   Primary Controller    │                       │    │
│  │                    │      (Active)           │                       │    │
│  │                    └───────────┬─────────────┘                       │    │
│  │                                │                                     │    │
│  │                         ┌──────┴──────┐                              │    │
│  │                         │  Heartbeat  │                              │    │
│  │                         └──────┬──────┘                              │    │
│  │                                │                                     │    │
│  │                    ┌───────────┴─────────────┐                       │    │
│  │                    │  Secondary Controller   │                       │    │
│  │                    │      (Standby)          │                       │    │
│  │                    └─────────────────────────┘                       │    │
│  │                                                                      │    │
│  │  Failover Process:                                                   │    │
│  │  1. Primary controller fails                                         │    │
│  │  2. APs detect loss of CAPWAP tunnel                                 │    │
│  │  3. APs attempt connection to secondary                              │    │
│  │  4. Secondary takes over (configuration synced)                      │    │
│  │  5. Clients remain connected (local switching)                       │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  RADIUS Server Failover:                                                     │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  # hostapd.conf                                                      │    │
│  │  # Primary RADIUS server                                             │    │
│  │  auth_server_addr=192.168.1.10                                       │    │
│  │  auth_server_port=1812                                               │    │
│  │  auth_server_shared_secret=secret1                                   │    │
│  │                                                                      │    │
│  │  # Secondary RADIUS server                                           │    │
│  │  auth_server_addr=192.168.1.11                                       │    │
│  │  auth_server_port=1812                                               │    │
│  │  auth_server_shared_secret=secret2                                   │    │
│  │                                                                      │    │
│  │  # Failover settings                                                 │    │
│  │  radius_retry_primary_interval=600                                   │    │
│  │  radius_server_retries=3                                             │    │
│  │  radius_server_timeout=5                                             │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  Auth Survivability Mode:                                                    │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  When RADIUS is unreachable:                                         │    │
│  │                                                                      │    │
│  │  1. AP caches successful authentications                             │    │
│  │  2. When RADIUS fails, AP uses cached credentials                    │    │
│  │  3. New clients can authenticate using cached data                   │    │
│  │  4. When RADIUS recovers, normal operation resumes                   │    │
│  │                                                                      │    │
│  │  # Configuration                                                     │    │
│  │  auth_survivability=1                                                │    │
│  │  auth_survivability_cache_timeout=86400                              │    │
│  │  auth_survivability_max_entries=1000                                 │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Appendix BE: IoT and Device Profiling

### BE.1 Device Fingerprinting

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    DEVICE FINGERPRINTING                                     │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  DHCP Fingerprinting:                                                        │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  DHCP Option 55 (Parameter Request List):                            │    │
│  │  ┌────────────────────────────────────────────────────────────┐     │    │
│  │  │ Fingerprint                    Device Type                 │     │    │
│  │  │ ───────────                    ───────────                 │     │    │
│  │  │ 1,3,6,15,31,33,43,44,46,47,   Windows 10                   │     │    │
│  │  │ 119,121,249,252                                            │     │    │
│  │  │                                                            │     │    │
│  │  │ 1,121,3,6,15,119,252          macOS                        │     │    │
│  │  │                                                            │     │    │
│  │  │ 1,3,6,15,26,28,51,58,59,43    iOS/iPadOS                   │     │    │
│  │  │                                                            │     │    │
│  │  │ 1,3,6,15,26,28,51,58,59       Android                      │     │    │
│  │  │                                                            │     │    │
│  │  │ 1,3,6,12,15,28,42             Linux                        │     │    │
│  │  └────────────────────────────────────────────────────────────┘     │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  HTTP User-Agent Fingerprinting:                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  ┌────────────────────────────────────────────────────────────┐     │    │
│  │  │ User-Agent Pattern            Device Type                  │     │    │
│  │  │ ──────────────────            ───────────                  │     │    │
│  │  │ Mozilla/5.0 (Windows NT 10.0) Windows 10                   │     │    │
│  │  │ Mozilla/5.0 (Macintosh)       macOS                        │     │    │
│  │  │ Mozilla/5.0 (iPhone)          iPhone                       │     │    │
│  │  │ Mozilla/5.0 (iPad)            iPad                         │     │    │
│  │  │ Mozilla/5.0 (Linux; Android)  Android                      │     │    │
│  │  │ Roku/DVP                      Roku                         │     │    │
│  │  │ AppleTV                       Apple TV                     │     │    │
│  │  │ Chromecast                    Chromecast                   │     │    │
│  │  └────────────────────────────────────────────────────────────┘     │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  MAC OUI Lookup:                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  ┌────────────────────────────────────────────────────────────┐     │    │
│  │  │ OUI Prefix     Manufacturer                                │     │    │
│  │  │ ──────────     ────────────                                │     │    │
│  │  │ 00:03:93       Apple                                       │     │    │
│  │  │ 00:1A:11       Google                                      │     │    │
│  │  │ 00:50:F2       Microsoft                                   │     │    │
│  │  │ 00:17:88       Philips Lighting                            │     │    │
│  │  │ 00:1E:C0       Microchip Technology                        │     │    │
│  │  │ B8:27:EB       Raspberry Pi                                │     │    │
│  │  │ 00:04:4B       Nvidia                                      │     │    │
│  │  │ 00:0C:29       VMware                                      │     │    │
│  │  └────────────────────────────────────────────────────────────┘     │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### BE.2 IoT Security Considerations

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    IOT SECURITY CONSIDERATIONS                               │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  IoT Device Challenges:                                                      │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  ┌────────────────────────────────────────────────────────────┐     │    │
│  │  │ Challenge                  Mitigation                      │     │    │
│  │  │ ─────────                  ──────────                      │     │    │
│  │  │ No WPA3 support            Use WPA2-PSK with strong key    │     │    │
│  │  │ No 802.1X support          Use MAC auth + VLAN isolation   │     │    │
│  │  │ Weak encryption            Isolate on separate VLAN        │     │    │
│  │  │ No firmware updates        Monitor for vulnerabilities     │     │    │
│  │  │ Default credentials        Change before deployment        │     │    │
│  │  │ Unencrypted protocols      Use network segmentation        │     │    │
│  │  └────────────────────────────────────────────────────────────┘     │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  IoT Network Architecture:                                                   │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │                         ┌─────────────┐                              │    │
│  │                         │   Firewall  │                              │    │
│  │                         └──────┬──────┘                              │    │
│  │                                │                                     │    │
│  │         ┌──────────────────────┼──────────────────────┐              │    │
│  │         │                      │                      │              │    │
│  │  ┌──────┴──────┐        ┌──────┴──────┐        ┌──────┴──────┐       │    │
│  │  │  VLAN 100   │        │  VLAN 300   │        │  VLAN 400   │       │    │
│  │  │  Corporate  │        │    IoT      │        │   Cameras   │       │    │
│  │  └──────┬──────┘        └──────┬──────┘        └──────┬──────┘       │    │
│  │         │                      │                      │              │    │
│  │    ┌────┴────┐            ┌────┴────┐            ┌────┴────┐         │    │
│  │    │ Laptops │            │ Sensors │            │ IP Cams │         │    │
│  │    │ Phones  │            │ Lights  │            │   NVR   │         │    │
│  │    └─────────┘            │ Locks   │            └─────────┘         │    │
│  │                           └─────────┘                                │    │
│  │                                                                      │    │
│  │  Firewall Rules:                                                     │    │
│  │  - IoT VLAN → Internet: Limited (cloud services only)                │    │
│  │  - IoT VLAN → Corporate: Blocked                                     │    │
│  │  - Corporate → IoT: Limited (management only)                        │    │
│  │  - Camera VLAN → NVR only                                            │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Appendix BF: Captive Portal Implementation

### BF.1 Captive Portal Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    CAPTIVE PORTAL ARCHITECTURE                               │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  Captive Portal Flow:                                                        │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  Client              AP/Controller         Portal Server            │    │
│  │     │                     │                      │                  │    │
│  │     │ ── Associate ─────> │                      │                  │    │
│  │     │                     │                      │                  │    │
│  │     │ ── DHCP Request ──> │                      │                  │    │
│  │     │ <── DHCP Response ─ │                      │                  │    │
│  │     │                     │                      │                  │    │
│  │     │ ── HTTP Request ──> │                      │                  │    │
│  │     │ <── HTTP 302 ────── │ (Redirect to portal) │                  │    │
│  │     │                     │                      │                  │    │
│  │     │ ── HTTPS ──────────────────────────────────>│                  │    │
│  │     │ <── Login Page ─────────────────────────────│                  │    │
│  │     │                     │                      │                  │    │
│  │     │ ── Credentials ─────────────────────────────>│                  │    │
│  │     │                     │                      │                  │    │
│  │     │                     │ <── Auth Success ─── │                  │    │
│  │     │                     │    (RADIUS CoA)      │                  │    │
│  │     │                     │                      │                  │    │
│  │     │ <── Access Granted ─│                      │                  │    │
│  │     │                     │                      │                  │    │
│  │     │ ── Normal Traffic ─>│ ── Forward ────────> │ Internet         │    │
│  │     │                     │                      │                  │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  Captive Portal Detection (CPD):                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  ┌────────────────────────────────────────────────────────────┐     │    │
│  │  │ OS              Detection URL                              │     │    │
│  │  │ ──              ─────────────                              │     │    │
│  │  │ Apple           captive.apple.com/hotspot-detect.html      │     │    │
│  │  │ Android         connectivitycheck.gstatic.com/generate_204 │     │    │
│  │  │ Windows         www.msftconnecttest.com/connecttest.txt    │     │    │
│  │  │ Firefox         detectportal.firefox.com/success.txt       │     │    │
│  │  │ Chrome          clients3.google.com/generate_204           │     │    │
│  │  └────────────────────────────────────────────────────────────┘     │    │
│  │                                                                      │    │
│  │  Detection Process:                                                  │    │
│  │  1. Client connects to WiFi                                          │    │
│  │  2. Client sends HTTP request to detection URL                       │    │
│  │  3. If response is not expected, captive portal detected             │    │
│  │  4. Client opens captive portal browser/webview                      │    │
│  │  5. User completes authentication                                    │    │
│  │  6. Client re-tests detection URL                                    │    │
│  │  7. If response is expected, internet access confirmed               │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### BF.2 Captive Portal Configuration

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    CAPTIVE PORTAL CONFIGURATION                              │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  iptables-based Captive Portal:                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  # Create captive portal chain                                       │    │
│  │  iptables -N CAPTIVE_PORTAL                                          │    │
│  │                                                                      │    │
│  │  # Allow DHCP                                                        │    │
│  │  iptables -A CAPTIVE_PORTAL -p udp --dport 67:68 -j ACCEPT           │    │
│  │                                                                      │    │
│  │  # Allow DNS                                                         │    │
│  │  iptables -A CAPTIVE_PORTAL -p udp --dport 53 -j ACCEPT              │    │
│  │  iptables -A CAPTIVE_PORTAL -p tcp --dport 53 -j ACCEPT              │    │
│  │                                                                      │    │
│  │  # Allow portal server                                               │    │
│  │  iptables -A CAPTIVE_PORTAL -d 192.168.1.100 -j ACCEPT               │    │
│  │                                                                      │    │
│  │  # Redirect HTTP to portal                                           │    │
│  │  iptables -t nat -A PREROUTING -i wlan0 -p tcp --dport 80 \          │    │
│  │      -j DNAT --to-destination 192.168.1.100:80                       │    │
│  │                                                                      │    │
│  │  # Redirect HTTPS to portal                                          │    │
│  │  iptables -t nat -A PREROUTING -i wlan0 -p tcp --dport 443 \         │    │
│  │      -j DNAT --to-destination 192.168.1.100:443                      │    │
│  │                                                                      │    │
│  │  # Drop all other traffic                                            │    │
│  │  iptables -A CAPTIVE_PORTAL -j DROP                                  │    │
│  │                                                                      │    │
│  │  # Apply to wireless interface                                       │    │
│  │  iptables -A FORWARD -i wlan0 -j CAPTIVE_PORTAL                      │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  Authenticated Client Bypass:                                                │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  # Add authenticated client to bypass list                           │    │
│  │  iptables -I CAPTIVE_PORTAL -m mac --mac-source 00:11:22:33:44:55 \  │    │
│  │      -j ACCEPT                                                       │    │
│  │                                                                      │    │
│  │  # Remove client on logout/timeout                                   │    │
│  │  iptables -D CAPTIVE_PORTAL -m mac --mac-source 00:11:22:33:44:55 \  │    │
│  │      -j ACCEPT                                                       │    │
│  │                                                                      │    │
│  │  # Using ipset for better performance                                │    │
│  │  ipset create authenticated_clients hash:mac                         │    │
│  │  iptables -I CAPTIVE_PORTAL -m set --match-set authenticated_clients \│   │
│  │      src -j ACCEPT                                                   │    │
│  │                                                                      │    │
│  │  # Add/remove clients                                                │    │
│  │  ipset add authenticated_clients 00:11:22:33:44:55                   │    │
│  │  ipset del authenticated_clients 00:11:22:33:44:55                   │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Appendix BG: Location Services and Analytics

### BG.1 WiFi-Based Location

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    WIFI-BASED LOCATION                                       │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  Location Methods:                                                           │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  ┌────────────────────────────────────────────────────────────┐     │    │
│  │  │ Method              Accuracy    Requirements               │     │    │
│  │  │ ──────              ────────    ────────────               │     │    │
│  │  │ RSSI Triangulation  5-15m       3+ APs, RSSI data          │     │    │
│  │  │ Time of Arrival     1-3m        Precise timing, sync       │     │    │
│  │  │ Angle of Arrival    1-3m        Antenna arrays             │     │    │
│  │  │ Fingerprinting      2-5m        Pre-surveyed RF map        │     │    │
│  │  │ RTT (802.11mc)      1-2m        FTM-capable devices        │     │    │
│  │  └────────────────────────────────────────────────────────────┘     │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  RSSI Triangulation:                                                         │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │              AP1 (-45 dBm)                                           │    │
│  │                 *                                                    │    │
│  │                /|\                                                   │    │
│  │               / | \                                                  │    │
│  │              /  |  \                                                 │    │
│  │             /   |   \                                                │    │
│  │            /    |    \                                               │    │
│  │           /     |     \                                              │    │
│  │          /      |      \                                             │    │
│  │         /       |       \                                            │    │
│  │        /        |        \                                           │    │
│  │       /         |         \                                          │    │
│  │      /          |          \                                         │    │
│  │     *───────────X───────────*                                        │    │
│  │  AP2 (-55 dBm)  │        AP3 (-60 dBm)                               │    │
│  │                 │                                                    │    │
│  │            Client Location                                           │    │
│  │                                                                      │    │
│  │  Distance estimation: d = 10^((TxPower - RSSI) / (10 * n))           │    │
│  │  Where n = path loss exponent (typically 2-4)                        │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  Fine Timing Measurement (802.11mc):                                         │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  Client                                AP                            │    │
│  │     │                                   │                            │    │
│  │     │ ──── FTM Request ───────────────> │                            │    │
│  │     │                                   │                            │    │
│  │     │ <─── FTM Response (t1, t4) ────── │                            │    │
│  │     │                                   │                            │    │
│  │     │ ──── FTM Request ───────────────> │                            │    │
│  │     │                                   │                            │    │
│  │     │ <─── FTM Response (t1, t4) ────── │                            │    │
│  │     │                                   │                            │    │
│  │                                                                      │    │
│  │  RTT = (t4 - t1) - (t3 - t2)                                         │    │
│  │  Distance = RTT * c / 2                                              │    │
│  │  Where c = speed of light (3 × 10^8 m/s)                             │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### BG.2 WiFi Analytics

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    WIFI ANALYTICS                                            │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  Metrics Collection:                                                         │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  ┌────────────────────────────────────────────────────────────┐     │    │
│  │  │ Metric                  Description                        │     │    │
│  │  │ ──────                  ───────────                        │     │    │
│  │  │ Client Count            Number of associated clients       │     │    │
│  │  │ Unique Visitors         Distinct MAC addresses seen        │     │    │
│  │  │ Dwell Time              Time spent in coverage area        │     │    │
│  │  │ Visit Frequency         Return visits per client           │     │    │
│  │  │ Traffic Volume          Bytes transmitted/received         │     │    │
│  │  │ Channel Utilization     Percentage of airtime used         │     │    │
│  │  │ Retry Rate              Percentage of retransmissions      │     │    │
│  │  │ SNR Distribution        Signal quality distribution        │     │    │
│  │  │ Roaming Events          Inter-AP handoffs                  │     │    │
│  │  │ Auth Failures           Failed authentication attempts     │     │    │
│  │  └────────────────────────────────────────────────────────────┘     │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  Privacy Considerations:                                                     │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  MAC Address Randomization:                                          │    │
│  │  - iOS 14+: Random MAC per network                                   │    │
│  │  - Android 10+: Random MAC per network                               │    │
│  │  - Windows 10+: Optional random MAC                                  │    │
│  │                                                                      │    │
│  │  Impact on Analytics:                                                │    │
│  │  - Unique visitor counts inflated                                    │    │
│  │  - Return visit tracking unreliable                                  │    │
│  │  - Dwell time tracking affected                                      │    │
│  │                                                                      │    │
│  │  Mitigations:                                                        │    │
│  │  - Use authenticated sessions for tracking                           │    │
│  │  - Aggregate analytics (not individual tracking)                     │    │
│  │  - Use probe request patterns (not MAC alone)                        │    │
│  │  - Implement opt-in tracking via app                                 │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Appendix BH: Spectrum Analysis

### BH.1 Interference Detection

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    INTERFERENCE DETECTION                                    │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  Common Interference Sources:                                                │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  2.4 GHz Band:                                                       │    │
│  │  ┌────────────────────────────────────────────────────────────┐     │    │
│  │  │ Source                  Frequency       Impact             │     │    │
│  │  │ ──────                  ─────────       ──────             │     │    │
│  │  │ Microwave Oven          2.45 GHz        Severe (pulsed)    │     │    │
│  │  │ Bluetooth               2.4-2.4835 GHz  Moderate (FHSS)    │     │    │
│  │  │ Cordless Phone          2.4 GHz         Moderate           │     │    │
│  │  │ Baby Monitor            2.4 GHz         Moderate           │     │    │
│  │  │ Wireless Camera         2.4 GHz         Moderate           │     │    │
│  │  │ ZigBee/Z-Wave           2.4 GHz         Low                │     │    │
│  │  │ Fluorescent Lights      Broadband       Low                │     │    │
│  │  └────────────────────────────────────────────────────────────┘     │    │
│  │                                                                      │    │
│  │  5 GHz Band:                                                         │    │
│  │  ┌────────────────────────────────────────────────────────────┐     │    │
│  │  │ Source                  Frequency       Impact             │     │    │
│  │  │ ──────                  ─────────       ──────             │     │    │
│  │  │ Weather Radar           5.25-5.35 GHz   Severe (DFS)       │     │    │
│  │  │ Military Radar          5.25-5.725 GHz  Severe (DFS)       │     │    │
│  │  │ Cordless Phone          5.8 GHz         Moderate           │     │    │
│  │  │ Perimeter Sensors       5.8 GHz         Low                │     │    │
│  │  └────────────────────────────────────────────────────────────┘     │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  Spectrum Analysis Display:                                                  │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  Power                                                               │    │
│  │  (dBm)                                                               │    │
│  │    │                                                                 │    │
│  │ -30│                    ┌──┐                                         │    │
│  │    │                    │  │                                         │    │
│  │ -40│         ┌──┐       │  │       ┌──┐                              │    │
│  │    │         │  │       │  │       │  │                              │    │
│  │ -50│    ┌──┐ │  │  ┌──┐ │  │  ┌──┐ │  │  ┌──┐                        │    │
│  │    │    │  │ │  │  │  │ │  │  │  │ │  │  │  │                        │    │
│  │ -60│ ┌──┤  ├─┤  ├──┤  ├─┤  ├──┤  ├─┤  ├──┤  ├──┐                     │    │
│  │    │ │  │  │ │  │  │  │ │  │  │  │ │  │  │  │  │                     │    │
│  │ -70│─┴──┴──┴─┴──┴──┴──┴─┴──┴──┴──┴─┴──┴──┴──┴──┴─                    │    │
│  │    │                                                                 │    │
│  │ -80│─────────────────────────────────────────────                    │    │
│  │    └────────────────────────────────────────────> Frequency          │    │
│  │       Ch1  Ch2  Ch3  Ch4  Ch5  Ch6  Ch7  Ch8  Ch9                    │    │
│  │                                                                      │    │
│  │  Legend:                                                             │    │
│  │  ┌──┐ = WiFi signal                                                  │    │
│  │  ─── = Noise floor                                                   │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### BH.2 Channel Planning

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    CHANNEL PLANNING                                          │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  2.4 GHz Non-Overlapping Channels:                                           │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  Frequency (MHz)                                                     │    │
│  │  2412  2417  2422  2427  2432  2437  2442  2447  2452  2457  2462    │    │
│  │    │     │     │     │     │     │     │     │     │     │     │     │    │
│  │    1     2     3     4     5     6     7     8     9    10    11     │    │
│  │                                                                      │    │
│  │  ┌─────────────────────┐                                             │    │
│  │  │     Channel 1       │                                             │    │
│  │  └─────────────────────┘                                             │    │
│  │                          ┌─────────────────────┐                     │    │
│  │                          │     Channel 6       │                     │    │
│  │                          └─────────────────────┘                     │    │
│  │                                                  ┌─────────────────────┐ │
│  │                                                  │     Channel 11      │ │
│  │                                                  └─────────────────────┘ │
│  │                                                                      │    │
│  │  Non-overlapping: 1, 6, 11 (US) or 1, 5, 9, 13 (EU)                  │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  5 GHz Channel Plan (US):                                                    │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  U-NII-1 (Indoor):                                                   │    │
│  │  36, 40, 44, 48 (5180-5240 MHz)                                      │    │
│  │                                                                      │    │
│  │  U-NII-2A (DFS):                                                     │    │
│  │  52, 56, 60, 64 (5260-5320 MHz)                                      │    │
│  │                                                                      │    │
│  │  U-NII-2C (DFS):                                                     │    │
│  │  100, 104, 108, 112, 116, 120, 124, 128, 132, 136, 140, 144          │    │
│  │  (5500-5720 MHz)                                                     │    │
│  │                                                                      │    │
│  │  U-NII-3 (Outdoor):                                                  │    │
│  │  149, 153, 157, 161, 165 (5745-5825 MHz)                             │    │
│  │                                                                      │    │
│  │  80 MHz Channels:                                                    │    │
│  │  36-48, 52-64, 100-112, 116-128, 132-144, 149-161                    │    │
│  │                                                                      │    │
│  │  160 MHz Channels:                                                   │    │
│  │  36-64, 100-128                                                      │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  6 GHz Channel Plan (US):                                                    │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  U-NII-5: 1-93 (5925-6425 MHz)                                       │    │
│  │  U-NII-6: 97-113 (6425-6525 MHz)                                     │    │
│  │  U-NII-7: 117-185 (6525-6875 MHz)                                    │    │
│  │  U-NII-8: 189-233 (6875-7125 MHz)                                    │    │
│  │                                                                      │    │
│  │  Total: 59 × 20 MHz, 29 × 40 MHz, 14 × 80 MHz, 7 × 160 MHz,          │    │
│  │         3 × 320 MHz channels                                         │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Appendix BI: Migration and Upgrade Strategies

### BI.1 WPA2 to WPA3 Migration

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    WPA2 TO WPA3 MIGRATION                                    │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  Migration Phases:                                                           │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  Phase 1: Assessment                                                 │    │
│  │  ┌────────────────────────────────────────────────────────────┐     │    │
│  │  │ - Inventory all client devices                             │     │    │
│  │  │ - Identify WPA3-capable devices                            │     │    │
│  │  │ - Identify legacy devices requiring WPA2                   │     │    │
│  │  │ - Check AP firmware for WPA3 support                       │     │    │
│  │  │ - Plan transition timeline                                 │     │    │
│  │  └────────────────────────────────────────────────────────────┘     │    │
│  │                                                                      │    │
│  │  Phase 2: Transition Mode                                            │    │
│  │  ┌────────────────────────────────────────────────────────────┐     │    │
│  │  │ - Enable WPA3-Transition mode (WPA2/WPA3 mixed)            │     │    │
│  │  │ - WPA3 clients use SAE                                     │     │    │
│  │  │ - WPA2 clients use PSK                                     │     │    │
│  │  │ - Monitor client distribution                              │     │    │
│  │  │ - Upgrade legacy devices where possible                    │     │    │
│  │  └────────────────────────────────────────────────────────────┘     │    │
│  │                                                                      │    │
│  │  Phase 3: WPA3-Only                                                  │    │
│  │  ┌────────────────────────────────────────────────────────────┐     │    │
│  │  │ - Disable WPA2 on primary SSID                             │     │    │
│  │  │ - Create separate legacy SSID for WPA2 devices             │     │    │
│  │  │ - Isolate legacy SSID on separate VLAN                     │     │    │
│  │  │ - Plan retirement of legacy SSID                           │     │    │
│  │  └────────────────────────────────────────────────────────────┘     │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  Transition Mode Configuration:                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  # hostapd.conf - WPA3 Transition Mode                               │    │
│  │  wpa=2                                                               │    │
│  │  wpa_key_mgmt=WPA-PSK SAE                                            │    │
│  │  wpa_pairwise=CCMP                                                   │    │
│  │  rsn_pairwise=CCMP                                                   │    │
│  │  sae_password=MySecurePassword123                                    │    │
│  │  wpa_passphrase=MySecurePassword123                                  │    │
│  │  ieee80211w=1                                                        │    │
│  │  sae_require_mfp=1                                                   │    │
│  │                                                                      │    │
│  │  # ieee80211w values:                                                │    │
│  │  # 0 = disabled                                                      │    │
│  │  # 1 = optional (required for transition)                            │    │
│  │  # 2 = required (WPA3-only)                                          │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### BI.2 WiFi 6/6E/7 Upgrade Path

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    WIFI 6/6E/7 UPGRADE PATH                                  │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  Feature Comparison:                                                         │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  ┌────────────────────────────────────────────────────────────┐     │    │
│  │  │ Feature           WiFi 5    WiFi 6    WiFi 6E   WiFi 7     │     │    │
│  │  │ ───────           ──────    ──────    ───────   ──────     │     │    │
│  │  │ Standard          802.11ac  802.11ax  802.11ax  802.11be   │     │    │
│  │  │ Max Speed         3.5 Gbps  9.6 Gbps  9.6 Gbps  46 Gbps    │     │    │
│  │  │ Bands             2.4/5     2.4/5     2.4/5/6   2.4/5/6    │     │    │
│  │  │ Channel Width     160 MHz   160 MHz   160 MHz   320 MHz    │     │    │
│  │  │ Modulation        256-QAM   1024-QAM  1024-QAM  4096-QAM   │     │    │
│  │  │ OFDMA             No        Yes       Yes       Yes        │     │    │
│  │  │ MU-MIMO           DL only   UL+DL     UL+DL     UL+DL      │     │    │
│  │  │ BSS Coloring      No        Yes       Yes       Yes        │     │    │
│  │  │ TWT               No        Yes       Yes       Yes        │     │    │
│  │  │ MLO               No        No        No        Yes        │     │    │
│  │  └────────────────────────────────────────────────────────────┘     │     │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  Upgrade Considerations:                                                     │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  Infrastructure:                                                     │    │
│  │  - Ethernet: 2.5GbE or 5GbE for WiFi 6, 10GbE for WiFi 7             │    │
│  │  - PoE: 802.3at (PoE+) or 802.3bt (PoE++) for high-power APs         │    │
│  │  - Cabling: Cat6a minimum for 10GbE                                  │    │
│  │                                                                      │    │
│  │  Client Compatibility:                                               │    │
│  │  - WiFi 6 APs backward compatible with WiFi 5/4 clients              │    │
│  │  - WiFi 6E requires 6 GHz capable clients                            │    │
│  │  - WiFi 7 backward compatible with all previous standards            │    │
│  │                                                                      │    │
│  │  Deployment Strategy:                                                │    │
│  │  - Start with high-density areas                                     │    │
│  │  - Prioritize conference rooms, auditoriums                          │    │
│  │  - Phase out legacy APs gradually                                    │    │
│  │  - Consider 6 GHz for new deployments                                │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Appendix BJ: API and Automation

### BJ.1 hostapd Control Interface

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    HOSTAPD CONTROL INTERFACE                                 │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  Control Interface Commands:                                                 │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  # Connect to control interface                                      │    │
│  │  hostapd_cli -i wlan0                                                │    │
│  │                                                                      │    │
│  │  # Status commands                                                   │    │
│  │  > status                                                            │    │
│  │  > sta                                                               │    │
│  │  > all_sta                                                           │    │
│  │  > sta &lt;MAC&gt;                                                         │    │
│  │                                                                      │    │
│  │  # Client management                                                 │    │
│  │  > disassociate &lt;MAC&gt;                                                │    │
│  │  > deauthenticate &lt;MAC&gt;                                              │    │
│  │  > poll_sta &lt;MAC&gt;                                                    │    │
│  │                                                                      │    │
│  │  # Configuration                                                     │    │
│  │  > set &lt;param&gt; &lt;value&gt;                                               │    │
│  │  > get &lt;param&gt;                                                       │    │
│  │  > reload                                                            │    │
│  │  > disable                                                           │    │
│  │  > enable                                                            │    │
│  │                                                                      │    │
│  │  # WPS                                                               │    │
│  │  > wps_pbc                                                           │    │
│  │  > wps_pin any &lt;PIN&gt;                                                 │    │
│  │  > wps_cancel                                                        │    │
│  │                                                                      │    │
│  │  # Neighbor reports                                                  │    │
│  │  > show_neighbor                                                     │    │
│  │  > set_neighbor &lt;BSSID&gt; &lt;SSID&gt; &lt;NR&gt;                                  │    │
│  │  > remove_neighbor &lt;BSSID&gt; &lt;SSID&gt;                                    │    │
│  │                                                                      │    │
│  │  # BSS Transition                                                    │    │
│  │  > bss_tm_req &lt;MAC&gt; [options]                                        │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  Python API Example:                                                         │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  import socket                                                       │    │
│  │                                                                      │    │
│  │  class HostapdCtrl:                                                  │    │
│  │      def __init__(self, ctrl_path):                                  │    │
│  │          self.sock = socket.socket(socket.AF_UNIX, socket.SOCK_DGRAM)│    │
│  │          self.sock.bind('/tmp/hostapd_ctrl_' + str(os.getpid()))     │    │
│  │          self.sock.connect(ctrl_path)                                │    │
│  │                                                                      │    │
│  │      def request(self, cmd):                                         │    │
│  │          self.sock.send(cmd.encode())                                │    │
│  │          return self.sock.recv(4096).decode()                        │    │
│  │                                                                      │    │
│  │      def get_status(self):                                           │    │
│  │          return self.request('STATUS')                               │    │
│  │                                                                      │    │
│  │      def get_stations(self):                                         │    │
│  │          return self.request('STA')                                  │    │
│  │                                                                      │    │
│  │      def deauth_station(self, mac):                                  │    │
│  │          return self.request(f'DEAUTHENTICATE {mac}')                │    │
│  │                                                                      │    │
│  │  # Usage                                                             │    │
│  │  ctrl = HostapdCtrl('/var/run/hostapd/wlan0')                        │    │
│  │  print(ctrl.get_status())                                            │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Appendix BK: Multicast and Broadcast Optimization

### BK.1 Multicast to Unicast Conversion

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    MULTICAST TO UNICAST CONVERSION                           │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  Problem with Multicast over WiFi:                                           │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  - Multicast frames sent at lowest basic rate (1-6 Mbps)             │    │
│  │  - No acknowledgment (no retransmission on loss)                     │    │
│  │  - Consumes significant airtime                                      │    │
│  │  - Unreliable delivery                                               │    │
│  │                                                                      │    │
│  │  Example: 1 Mbps multicast video stream                              │    │
│  │  - At 6 Mbps: Uses 16.7% of airtime                                  │    │
│  │  - At 54 Mbps unicast: Uses 1.9% of airtime                          │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  Multicast to Unicast Conversion:                                            │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  Without Conversion:                                                 │    │
│  │  ┌─────────────────────────────────────────────────────────────┐    │    │
│  │  │                                                              │    │    │
│  │  │  Source ──> AP ──> Multicast Frame (6 Mbps) ──> All Clients  │    │    │
│  │  │                    (No ACK, unreliable)                      │    │    │
│  │  │                                                              │    │    │
│  │  └─────────────────────────────────────────────────────────────┘    │    │
│  │                                                                      │    │
│  │  With Conversion:                                                    │    │
│  │  ┌─────────────────────────────────────────────────────────────┐    │    │
│  │  │                                                              │    │    │
│  │  │  Source ──> AP ──> Unicast Frame 1 (54 Mbps) ──> Client 1    │    │    │
│  │  │                    (ACK, reliable)                           │    │    │
│  │  │            AP ──> Unicast Frame 2 (54 Mbps) ──> Client 2     │    │    │
│  │  │                    (ACK, reliable)                           │    │    │
│  │  │            AP ──> Unicast Frame 3 (54 Mbps) ──> Client 3     │    │    │
│  │  │                    (ACK, reliable)                           │    │    │
│  │  │                                                              │    │    │
│  │  └─────────────────────────────────────────────────────────────┘    │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  Configuration:                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  # hostapd.conf                                                      │    │
│  │  multicast_to_unicast=1                                              │    │
│  │                                                                      │    │
│  │  # Linux bridge configuration                                        │    │
│  │  echo 1 > /sys/class/net/br0/bridge/multicast_snooping               │    │
│  │  echo 1 > /sys/class/net/br0/bridge/multicast_querier                │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### BK.2 IGMP Snooping

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    IGMP SNOOPING                                             │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  IGMP Snooping Operation:                                                    │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  Client 1              AP/Switch              Multicast Source       │    │
│  │     │                      │                        │                │    │
│  │     │ ── IGMP Join ──────> │                        │                │    │
│  │     │    (224.1.1.1)       │                        │                │    │
│  │     │                      │ (Records membership)   │                │    │
│  │     │                      │                        │                │    │
│  │     │                      │ <── Multicast Data ─── │                │    │
│  │     │                      │     (224.1.1.1)        │                │    │
│  │     │                      │                        │                │    │
│  │     │ <── Forward ──────── │                        │                │    │
│  │     │    (Only to members) │                        │                │    │
│  │     │                      │                        │                │    │
│  │  Client 2 (not member)     │                        │                │    │
│  │     │                      │                        │                │    │
│  │     │ (No traffic)         │                        │                │    │
│  │     │                      │                        │                │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  IGMP Message Types:                                                         │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  ┌────────────────────────────────────────────────────────────┐     │    │
│  │  │ Type                    Description                        │     │    │
│  │  │ ────                    ───────────                        │     │    │
│  │  │ Membership Query        Router queries for group members   │     │    │
│  │  │ Membership Report v1    Client joins group (IGMPv1)        │     │    │
│  │  │ Membership Report v2    Client joins group (IGMPv2)        │     │    │
│  │  │ Membership Report v3    Client joins/leaves (IGMPv3)       │     │    │
│  │  │ Leave Group             Client leaves group (IGMPv2)       │     │    │
│  │  └────────────────────────────────────────────────────────────┘     │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Appendix BL: Voice over WiFi (VoWiFi)

### BL.1 VoWiFi Requirements

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    VOWIFI REQUIREMENTS                                       │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  Quality Requirements:                                                       │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  ┌────────────────────────────────────────────────────────────┐     │    │
│  │  │ Parameter           Requirement      Impact                │     │    │
│  │  │ ─────────           ───────────      ──────                │     │    │
│  │  │ Latency             < 150 ms         Voice delay           │     │    │
│  │  │ Jitter              < 30 ms          Voice quality         │     │    │
│  │  │ Packet Loss         < 1%             Voice dropouts        │     │    │
│  │  │ Bandwidth           64-128 kbps      Per call              │     │    │
│  │  │ MOS Score           > 3.5            User satisfaction     │     │    │
│  │  └────────────────────────────────────────────────────────────┘     │    │
│  │                                                                      │    │
│  │  MOS (Mean Opinion Score):                                           │    │
│  │  5 = Excellent                                                       │    │
│  │  4 = Good                                                            │    │
│  │  3 = Fair                                                            │    │
│  │  2 = Poor                                                            │    │
│  │  1 = Bad                                                             │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  VoWiFi Architecture:                                                        │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  ┌─────────┐    ┌─────────┐    ┌─────────┐    ┌─────────────────┐   │    │
│  │  │  Phone  │────│   AP    │────│ Router  │────│  ePDG/SBC       │   │    │
│  │  │ (VoWiFi)│    │         │    │         │    │ (Carrier Core)  │   │    │
│  │  └─────────┘    └─────────┘    └─────────┘    └────────┬────────┘   │    │
│  │                                                        │            │    │
│  │                                                        │            │    │
│  │                                               ┌────────┴────────┐   │    │
│  │                                               │   IMS Core      │   │    │
│  │                                               │ (VoLTE/VoWiFi)  │   │    │
│  │                                               └────────┬────────┘   │    │
│  │                                                        │            │    │
│  │                                               ┌────────┴────────┐   │    │
│  │                                               │   PSTN/Mobile   │   │    │
│  │                                               │    Network      │   │    │
│  │                                               └─────────────────┘   │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  QoS Configuration for Voice:                                                │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  # hostapd.conf                                                      │    │
│  │  wmm_enabled=1                                                       │    │
│  │                                                                      │    │
│  │  # Voice (AC_VO) parameters                                          │    │
│  │  wmm_ac_vo_cwmin=2                                                   │    │
│  │  wmm_ac_vo_cwmax=3                                                   │    │
│  │  wmm_ac_vo_aifs=2                                                    │    │
│  │  wmm_ac_vo_txop_limit=47                                             │    │
│  │  wmm_ac_vo_acm=0                                                     │    │
│  │                                                                      │    │
│  │  # Enable U-APSD for power save                                      │    │
│  │  uapsd_advertisement_enabled=1                                       │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### BL.2 WiFi Calling Handoff

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    WIFI CALLING HANDOFF                                      │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  VoWiFi to VoLTE Handoff:                                                    │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  Phone                WiFi                LTE                 IMS    │    │
│  │    │                   │                   │                   │     │    │
│  │    │ ── VoWiFi Call ─> │                   │                   │     │    │
│  │    │                   │ ─────────────────────────────────────>│     │    │
│  │    │                   │                   │                   │     │    │
│  │    │ (WiFi signal weak)│                   │                   │     │    │
│  │    │                   │                   │                   │     │    │
│  │    │ ── Attach ────────────────────────────>│                   │     │    │
│  │    │                   │                   │                   │     │    │
│  │    │ ── Handoff Req ───────────────────────────────────────────>│     │    │
│  │    │                   │                   │                   │     │    │
│  │    │ <── Handoff Ack ──────────────────────────────────────────│     │    │
│  │    │                   │                   │                   │     │    │
│  │    │ ── VoLTE Call ────────────────────────>│ ────────────────>│     │    │
│  │    │                   │                   │                   │     │    │
│  │    │ ── Disconnect ───>│                   │                   │     │    │
│  │    │                   │                   │                   │     │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  Handoff Triggers:                                                           │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  ┌────────────────────────────────────────────────────────────┐     │    │
│  │  │ Trigger                 Threshold        Action            │     │    │
│  │  │ ───────                 ─────────        ──────            │     │    │
│  │  │ WiFi RSSI               < -75 dBm        Consider handoff  │     │    │
│  │  │ WiFi RSSI               < -80 dBm        Initiate handoff  │     │    │
│  │  │ Packet Loss             > 2%             Consider handoff  │     │    │
│  │  │ Latency                 > 200 ms         Consider handoff  │     │    │
│  │  │ LTE RSRP                > -100 dBm       LTE available     │     │    │
│  │  │ WiFi Disconnect         Immediate        Force handoff     │     │    │
│  │  └────────────────────────────────────────────────────────────┘     │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Appendix BM: Enterprise Integration

### BM.1 Active Directory Integration

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    ACTIVE DIRECTORY INTEGRATION                              │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  Authentication Flow:                                                        │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  Client        AP          RADIUS         AD/LDAP                    │    │
│  │    │           │             │               │                       │    │
│  │    │ ── EAP ─> │             │               │                       │    │
│  │    │           │ ── RADIUS ─>│               │                       │    │
│  │    │           │             │ ── LDAP ─────>│                       │    │
│  │    │           │             │   (Bind)      │                       │    │
│  │    │           │             │               │                       │    │
│  │    │           │             │ <── Success ──│                       │    │
│  │    │           │             │               │                       │    │
│  │    │           │             │ ── LDAP ─────>│                       │    │
│  │    │           │             │   (Search)    │                       │    │
│  │    │           │             │               │                       │    │
│  │    │           │             │ <── Groups ───│                       │    │
│  │    │           │             │               │                       │    │
│  │    │           │ <── Accept ─│               │                       │    │
│  │    │           │    (VLAN)   │               │                       │    │
│  │    │ <── OK ── │             │               │                       │    │
│  │    │           │             │               │                       │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  FreeRADIUS LDAP Configuration:                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  # /etc/freeradius/mods-available/ldap                               │    │
│  │  ldap {                                                              │    │
│  │      server = "ldap://dc.example.com"                                │    │
│  │      port = 389                                                      │    │
│  │      identity = "CN=radius,OU=Service,DC=example,DC=com"             │    │
│  │      password = "RadiusServicePassword"                              │    │
│  │      base_dn = "DC=example,DC=com"                                   │    │
│  │                                                                      │    │
│  │      user {                                                          │    │
│  │          base_dn = "OU=Users,${..base_dn}"                           │    │
│  │          filter = "(sAMAccountName=%{%{Stripped-User-Name}:-%{User-Name&#125;&#125;)"│
│  │      }                                                               │    │
│  │                                                                      │    │
│  │      group {                                                         │    │
│  │          base_dn = "OU=Groups,${..base_dn}"                          │    │
│  │          filter = "(objectClass=group)"                              │    │
│  │          membership_attribute = "memberOf"                           │    │
│  │      }                                                               │    │
│  │                                                                      │    │
│  │      options {                                                       │    │
│  │          chase_referrals = yes                                       │    │
│  │          rebind = yes                                                │    │
│  │      }                                                               │    │
│  │  }                                                                   │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  Group-Based VLAN Assignment:                                                │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  # /etc/freeradius/policy.d/vlan                                     │    │
│  │  vlan_assignment {                                                   │    │
│  │      if (LDAP-Group == "CN=Employees,OU=Groups,DC=example,DC=com") { │    │
│  │          update reply {                                              │    │
│  │              Tunnel-Type := VLAN                                     │    │
│  │              Tunnel-Medium-Type := IEEE-802                          │    │
│  │              Tunnel-Private-Group-Id := 100                          │    │
│  │          }                                                           │    │
│  │      }                                                               │    │
│  │      elsif (LDAP-Group == "CN=Guests,OU=Groups,DC=example,DC=com") { │    │
│  │          update reply {                                              │    │
│  │              Tunnel-Type := VLAN                                     │    │
│  │              Tunnel-Medium-Type := IEEE-802                          │    │
│  │              Tunnel-Private-Group-Id := 999                          │    │
│  │          }                                                           │    │
│  │      }                                                               │    │
│  │  }                                                                   │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### BM.2 Certificate-Based Authentication

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    CERTIFICATE-BASED AUTHENTICATION                         │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  PKI Infrastructure:                                                         │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │                    ┌─────────────────────┐                           │    │
│  │                    │     Root CA         │                           │    │
│  │                    │  (Offline, Secure)  │                           │    │
│  │                    └──────────┬──────────┘                           │    │
│  │                               │                                      │    │
│  │              ┌────────────────┼────────────────┐                     │    │
│  │              │                │                │                     │    │
│  │     ┌────────┴────────┐ ┌─────┴─────┐ ┌───────┴───────┐              │    │
│  │     │  Issuing CA     │ │ RADIUS CA │ │   User CA     │              │    │
│  │     │  (Servers)      │ │ (RADIUS)  │ │  (Clients)    │              │    │
│  │     └────────┬────────┘ └─────┬─────┘ └───────┬───────┘              │    │
│  │              │                │               │                      │    │
│  │     ┌────────┴────────┐ ┌─────┴─────┐ ┌───────┴───────┐              │    │
│  │     │ Server Certs    │ │ RADIUS    │ │ User Certs    │              │    │
│  │     │ (Web, LDAP)     │ │ Server    │ │ (EAP-TLS)     │              │    │
│  │     └─────────────────┘ └───────────┘ └───────────────┘              │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  EAP-TLS Configuration:                                                      │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  # /etc/freeradius/mods-available/eap                                │    │
│  │  eap {                                                               │    │
│  │      default_eap_type = tls                                          │    │
│  │                                                                      │    │
│  │      tls-config tls-common {                                         │    │
│  │          private_key_password = "keypassword"                        │    │
│  │          private_key_file = /etc/freeradius/certs/server.key         │    │
│  │          certificate_file = /etc/freeradius/certs/server.pem         │    │
│  │          ca_file = /etc/freeradius/certs/ca.pem                      │    │
│  │          ca_path = /etc/freeradius/certs                             │    │
│  │          check_crl = yes                                             │    │
│  │          check_all_crl = yes                                         │    │
│  │          cipher_list = "HIGH:!aNULL:!MD5"                            │    │
│  │          tls_min_version = "1.2"                                     │    │
│  │          tls_max_version = "1.3"                                     │    │
│  │      }                                                               │    │
│  │                                                                      │    │
│  │      tls {                                                           │    │
│  │          tls = tls-common                                            │    │
│  │      }                                                               │    │
│  │  }                                                                   │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  Certificate Revocation:                                                     │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  Methods:                                                            │    │
│  │  - CRL (Certificate Revocation List)                                 │    │
│  │    - Periodic download of revoked certificates                       │    │
│  │    - Can be stale between updates                                    │    │
│  │                                                                      │    │
│  │  - OCSP (Online Certificate Status Protocol)                         │    │
│  │    - Real-time certificate status check                              │    │
│  │    - Requires OCSP responder availability                            │    │
│  │                                                                      │    │
│  │  # FreeRADIUS OCSP configuration                                     │    │
│  │  ocsp {                                                              │    │
│  │      enable = yes                                                    │    │
│  │      override_cert_url = yes                                         │    │
│  │      url = "http://ocsp.example.com"                                 │    │
│  │      use_nonce = yes                                                 │    │
│  │      timeout = 5                                                     │    │
│  │      softfail = no                                                   │    │
│  │  }                                                                   │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Appendix BN: Monitoring and Alerting

### BN.1 SNMP Monitoring

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    SNMP MONITORING                                           │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  Common WiFi MIBs:                                                           │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  ┌────────────────────────────────────────────────────────────┐     │    │
│  │  │ MIB                     Description                        │     │    │
│  │  │ ───                     ───────────                        │     │    │
│  │  │ IEEE802dot11-MIB        Standard 802.11 MIB                │     │    │
│  │  │ IF-MIB                  Interface statistics               │     │    │
│  │  │ ENTITY-MIB              Physical entity information        │     │    │
│  │  │ HOST-RESOURCES-MIB      CPU, memory, disk                  │     │    │
│  │  │ Vendor-specific MIBs    Proprietary extensions             │     │    │
│  │  └────────────────────────────────────────────────────────────┘     │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  Key OIDs:                                                                   │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  ┌────────────────────────────────────────────────────────────┐     │    │
│  │  │ OID                              Description               │     │    │
│  │  │ ───                              ───────────               │     │    │
│  │  │ .1.3.6.1.2.1.2.2.1.10            ifInOctets                │     │    │
│  │  │ .1.3.6.1.2.1.2.2.1.16            ifOutOctets               │     │    │
│  │  │ .1.3.6.1.2.1.2.2.1.14            ifInErrors                │     │    │
│  │  │ .1.3.6.1.2.1.2.2.1.20            ifOutErrors               │     │    │
│  │  │ .1.3.6.1.4.1.14179.2.1.1.1.38    bsnAPNumOfSlots           │     │    │
│  │  │ .1.3.6.1.4.1.14179.2.2.1.1.3     bsnAPIfPhyChannelNumber   │     │    │
│  │  │ .1.3.6.1.4.1.14179.2.2.2.1.2     bsnAPIfLoadChannelUtil    │     │    │
│  │  └────────────────────────────────────────────────────────────┘     │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  SNMP Traps:                                                                 │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  ┌────────────────────────────────────────────────────────────┐     │    │
│  │  │ Trap                         Trigger                       │     │    │
│  │  │ ────                         ───────                       │     │    │
│  │  │ coldStart                    AP reboot                     │     │    │
│  │  │ linkDown                     Interface down                │     │    │
│  │  │ linkUp                       Interface up                  │     │    │
│  │  │ authenticationFailure        SNMP auth failure             │     │    │
│  │  │ dot11Deauthenticate          Client deauth                 │     │    │
│  │  │ dot11Disassociate            Client disassoc               │     │    │
│  │  │ bsnAPDisassociated           AP disconnected               │     │    │
│  │  │ bsnRadarChannelDetected      DFS radar detected            │     │    │
│  │  │ bsnRogueAPDetected           Rogue AP detected             │     │    │
│  │  └────────────────────────────────────────────────────────────┘     │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### BN.2 Syslog and Log Analysis

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    SYSLOG AND LOG ANALYSIS                                   │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  Log Categories:                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  ┌────────────────────────────────────────────────────────────┐     │    │
│  │  │ Category              Examples                             │     │    │
│  │  │ ────────              ────────                             │     │    │
│  │  │ Authentication        EAP success/failure, PSK mismatch    │     │    │
│  │  │ Association           Client connect/disconnect            │     │    │
│  │  │ Roaming               FT events, OKC events                │     │    │
│  │  │ Security              MIC failures, replay attacks         │     │    │
│  │  │ Radio                 Channel changes, DFS events          │     │    │
│  │  │ System                AP boot, config changes              │     │    │
│  │  │ RADIUS                Auth requests, accounting            │     │    │
│  │  └────────────────────────────────────────────────────────────┘     │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  Sample Log Messages:                                                        │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  # Successful authentication                                         │    │
│  │  Jan  8 10:15:23 ap1 hostapd: wlan0: STA 00:11:22:33:44:55           │    │
│  │      IEEE 802.11: authenticated                                      │    │
│  │                                                                      │    │
│  │  # Association                                                       │    │
│  │  Jan  8 10:15:23 ap1 hostapd: wlan0: STA 00:11:22:33:44:55           │    │
│  │      IEEE 802.11: associated (aid 1)                                 │    │
│  │                                                                      │    │
│  │  # WPA key exchange                                                  │    │
│  │  Jan  8 10:15:24 ap1 hostapd: wlan0: STA 00:11:22:33:44:55           │    │
│  │      WPA: pairwise key handshake completed (RSN)                     │    │
│  │                                                                      │    │
│  │  # Authentication failure                                            │    │
│  │  Jan  8 10:20:15 ap1 hostapd: wlan0: STA 00:11:22:33:44:66           │    │
│  │      IEEE 802.11: authentication failed (status 15)                  │    │
│  │                                                                      │    │
│  │  # RADIUS timeout                                                    │    │
│  │  Jan  8 10:25:30 ap1 hostapd: wlan0: STA 00:11:22:33:44:77           │    │
│  │      RADIUS: No response from authentication server                  │    │
│  │                                                                      │    │
│  │  # DFS radar detection                                               │    │
│  │  Jan  8 11:00:00 ap1 hostapd: wlan1: DFS radar detected on          │    │
│  │      frequency 5260 MHz                                              │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  Log Analysis Queries:                                                       │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  # Count authentication failures                                     │    │
│  │  grep "authentication failed" /var/log/hostapd.log | wc -l          │    │
│  │                                                                      │    │
│  │  # Find clients with repeated failures                               │    │
│  │  grep "authentication failed" /var/log/hostapd.log | \              │    │
│  │      awk '{print $7}' | sort | uniq -c | sort -rn | head            │    │
│  │                                                                      │    │
│  │  # Track client roaming                                              │    │
│  │  grep "00:11:22:33:44:55" /var/log/hostapd.log | \                  │    │
│  │      grep -E "(associated|disassociated)"                           │    │
│  │                                                                      │    │
│  │  # Find DFS events                                                   │    │
│  │  grep "DFS" /var/log/hostapd.log                                    │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Appendix BO: Disaster Recovery

### BO.1 Backup and Restore

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    BACKUP AND RESTORE                                        │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  Configuration Backup:                                                       │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  Files to Backup:                                                    │    │
│  │  ┌────────────────────────────────────────────────────────────┐     │    │
│  │  │ File/Directory              Purpose                        │     │    │
│  │  │ ──────────────              ───────                        │     │    │
│  │  │ /etc/hostapd/               hostapd configuration          │     │    │
│  │  │ /etc/wpa_supplicant/        Supplicant configuration       │     │    │
│  │  │ /etc/freeradius/            RADIUS configuration           │     │    │
│  │  │ /etc/network/               Network configuration          │     │    │
│  │  │ /etc/ssl/certs/             SSL certificates               │     │    │
│  │  │ /etc/ssl/private/           Private keys                   │     │    │
│  │  │ /var/lib/hostapd/           Runtime state                  │     │    │
│  │  └────────────────────────────────────────────────────────────┘     │    │
│  │                                                                      │    │
│  │  Backup Script:                                                      │    │
│  │  ┌────────────────────────────────────────────────────────────┐     │    │
│  │  │                                                            │     │    │
│  │  │  #!/bin/bash                                               │     │    │
│  │  │  BACKUP_DIR="/backup/$(date +%Y%m%d)"                      │     │    │
│  │  │  mkdir -p $BACKUP_DIR                                      │     │    │
│  │  │                                                            │     │    │
│  │  │  # Backup configurations                                   │     │    │
│  │  │  tar -czf $BACKUP_DIR/hostapd.tar.gz /etc/hostapd/         │     │    │
│  │  │  tar -czf $BACKUP_DIR/freeradius.tar.gz /etc/freeradius/   │     │    │
│  │  │  tar -czf $BACKUP_DIR/network.tar.gz /etc/network/         │     │    │
│  │  │                                                            │     │    │
│  │  │  # Backup certificates (encrypted)                         │     │    │
│  │  │  tar -czf - /etc/ssl/ | \                                  │     │    │
│  │  │      openssl enc -aes-256-cbc -salt -out $BACKUP_DIR/ssl.enc│    │    │
│  │  │                                                            │     │    │
│  │  │  # Create checksum                                         │     │    │
│  │  │  sha256sum $BACKUP_DIR/* > $BACKUP_DIR/checksums.txt       │     │    │
│  │  │                                                            │     │    │
│  │  └────────────────────────────────────────────────────────────┘     │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  Restore Procedure:                                                          │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  1. Stop services                                                    │    │
│  │     systemctl stop hostapd freeradius                                │    │
│  │                                                                      │    │
│  │  2. Verify backup integrity                                          │    │
│  │     sha256sum -c checksums.txt                                       │    │
│  │                                                                      │    │
│  │  3. Restore configurations                                           │    │
│  │     tar -xzf hostapd.tar.gz -C /                                     │    │
│  │     tar -xzf freeradius.tar.gz -C /                                  │    │
│  │                                                                      │    │
│  │  4. Restore certificates                                             │    │
│  │     openssl enc -d -aes-256-cbc -in ssl.enc | tar -xzf - -C /        │    │
│  │                                                                      │    │
│  │  5. Verify permissions                                               │    │
│  │     chown -R freerad:freerad /etc/freeradius                         │    │
│  │     chmod 600 /etc/ssl/private/*                                     │    │
│  │                                                                      │    │
│  │  6. Start services                                                   │    │
│  │     systemctl start hostapd freeradius                               │    │
│  │                                                                      │    │
│  │  7. Verify operation                                                 │    │
│  │     hostapd_cli status                                               │    │
│  │     radtest user password localhost 0 testing123                     │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Appendix BP: Wireless Intrusion Detection

### BP.1 Rogue AP Detection

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    ROGUE AP DETECTION                                        │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  Rogue AP Types:                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  ┌────────────────────────────────────────────────────────────┐     │    │
│  │  │ Type                    Description                        │     │    │
│  │  │ ────                    ───────────                        │     │    │
│  │  │ Evil Twin               Same SSID as legitimate network    │     │    │
│  │  │ Honeypot                Open network to attract clients    │     │    │
│  │  │ Unauthorized AP         Employee-installed AP              │     │    │
│  │  │ Misconfigured AP        Legitimate AP with wrong settings  │     │    │
│  │  │ Ad-hoc Network          Peer-to-peer wireless network      │     │    │
│  │  │ Soft AP                 Client acting as AP (tethering)    │     │    │
│  │  └────────────────────────────────────────────────────────────┘     │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  Detection Methods:                                                          │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  1. BSSID Whitelist                                                  │    │
│  │     - Maintain list of authorized AP MAC addresses                   │    │
│  │     - Alert on unknown BSSIDs with corporate SSID                    │    │
│  │                                                                      │    │
│  │  2. RF Fingerprinting                                                │    │
│  │     - Analyze signal characteristics                                 │    │
│  │     - Detect anomalies in expected RF patterns                       │    │
│  │                                                                      │    │
│  │  3. Wired-Side Detection                                             │    │
│  │     - Monitor switch ports for unauthorized APs                      │    │
│  │     - Use 802.1X on all switch ports                                 │    │
│  │                                                                      │    │
│  │  4. Client Behavior Analysis                                         │    │
│  │     - Track client associations                                      │    │
│  │     - Detect clients connecting to unknown APs                       │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  Rogue Containment:                                                          │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  Methods:                                                            │    │
│  │  - Deauthentication (legal concerns in some jurisdictions)          │    │
│  │  - Client blacklisting                                               │    │
│  │  - Switch port shutdown                                              │    │
│  │  - Physical location and removal                                     │    │
│  │                                                                      │    │
│  │  Note: Wireless deauthentication attacks may be illegal              │    │
│  │  in some jurisdictions. Consult legal counsel before                 │    │
│  │  implementing active containment measures.                           │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### BP.2 Attack Detection

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    ATTACK DETECTION                                          │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  Detectable Attacks:                                                         │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  ┌────────────────────────────────────────────────────────────┐     │    │
│  │  │ Attack                  Detection Method                   │     │    │
│  │  │ ──────                  ────────────────                   │     │    │
│  │  │ Deauth Flood            High rate of deauth frames         │     │    │
│  │  │ Disassoc Flood          High rate of disassoc frames       │     │    │
│  │  │ Auth Flood              High rate of auth requests         │     │    │
│  │  │ Probe Flood             High rate of probe requests        │     │    │
│  │  │ EAPOL Flood             High rate of EAPOL frames          │     │    │
│  │  │ Beacon Flood            Excessive beacons on channel       │     │    │
│  │  │ CTS/RTS Flood           NAV manipulation attack            │     │    │
│  │  │ Dictionary Attack       Repeated auth failures             │     │    │
│  │  │ PMKID Attack            Unusual PMKID requests             │     │    │
│  │  │ KRACK                   Nonce reuse detection              │     │    │
│  │  │ Karma Attack            Probe response to all probes       │     │    │
│  │  └────────────────────────────────────────────────────────────┘     │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  Detection Thresholds:                                                       │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  ┌────────────────────────────────────────────────────────────┐     │    │
│  │  │ Event                   Threshold        Window            │     │    │
│  │  │ ─────                   ─────────        ──────            │     │    │
│  │  │ Deauth frames           > 10             per second        │     │    │
│  │  │ Auth failures           > 5              per minute        │     │    │
│  │  │ Probe requests          > 100            per second        │     │    │
│  │  │ Association failures    > 10             per minute        │     │    │
│  │  │ MIC failures            > 2              per minute        │     │    │
│  │  │ Replay attacks          > 1              per minute        │     │    │
│  │  └────────────────────────────────────────────────────────────┘     │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  Alert Actions:                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  - SNMP trap to management system                                    │    │
│  │  - Syslog message to SIEM                                            │    │
│  │  - Email notification to security team                               │    │
│  │  - Automatic client blacklisting                                     │    │
│  │  - Packet capture for forensics                                      │    │
│  │  - Ticket creation in incident management                            │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Appendix BQ: Cloud-Managed WiFi

### BQ.1 Cloud Management Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    CLOUD MANAGEMENT ARCHITECTURE                             │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  Architecture Overview:                                                      │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │                         ┌─────────────────────┐                      │    │
│  │                         │   Cloud Dashboard   │                      │    │
│  │                         │   (Web Console)     │                      │    │
│  │                         └──────────┬──────────┘                      │    │
│  │                                    │                                 │    │
│  │                         ┌──────────┴──────────┐                      │    │
│  │                         │   Cloud Controller  │                      │    │
│  │                         │   (Multi-tenant)    │                      │    │
│  │                         └──────────┬──────────┘                      │    │
│  │                                    │                                 │    │
│  │                    ┌───────────────┼───────────────┐                 │    │
│  │                    │               │               │                 │    │
│  │            ┌───────┴───────┐ ┌─────┴─────┐ ┌───────┴───────┐         │    │
│  │            │   Site A      │ │  Site B   │ │   Site C      │         │    │
│  │            │   Gateway     │ │  Gateway  │ │   Gateway     │         │    │
│  │            └───────┬───────┘ └─────┬─────┘ └───────┬───────┘         │    │
│  │                    │               │               │                 │    │
│  │            ┌───────┴───────┐ ┌─────┴─────┐ ┌───────┴───────┐         │    │
│  │            │  AP  AP  AP   │ │  AP  AP   │ │  AP  AP  AP   │         │    │
│  │            └───────────────┘ └───────────┘ └───────────────┘         │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  Communication Protocols:                                                    │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  ┌────────────────────────────────────────────────────────────┐     │    │
│  │  │ Protocol            Purpose                                │     │    │
│  │  │ ────────            ───────                                │     │    │
│  │  │ HTTPS               Configuration push/pull                │     │    │
│  │  │ WebSocket           Real-time status updates               │     │    │
│  │  │ MQTT                Telemetry and events                   │     │    │
│  │  │ gRPC                High-performance RPC                   │     │    │
│  │  │ CAPWAP              Legacy controller protocol             │     │    │
│  │  └────────────────────────────────────────────────────────────┘     │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### BQ.2 Zero-Touch Provisioning

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    ZERO-TOUCH PROVISIONING                                   │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  Provisioning Flow:                                                          │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  New AP              DHCP              Cloud                         │    │
│  │    │                  │                  │                           │    │
│  │    │ ── DHCP Req ───> │                  │                           │    │
│  │    │ <── DHCP Resp ── │                  │                           │    │
│  │    │    (IP, DNS)     │                  │                           │    │
│  │    │                  │                  │                           │    │
│  │    │ ── DNS Query ────────────────────────> (cloud.vendor.com)       │    │
│  │    │ <── DNS Response ──────────────────── (IP address)              │    │
│  │    │                  │                  │                           │    │
│  │    │ ── HTTPS ────────────────────────────>│                         │    │
│  │    │    (Serial, MAC) │                  │                           │    │
│  │    │                  │                  │                           │    │
│  │    │ <── Config ──────────────────────────│                          │    │
│  │    │    (SSID, Security, etc.)           │                           │    │
│  │    │                  │                  │                           │    │
│  │    │ ── Status ───────────────────────────>│                         │    │
│  │    │    (Online, Clients)                │                           │    │
│  │    │                  │                  │                           │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  Pre-Provisioning Steps:                                                     │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  1. Register AP serial numbers in cloud dashboard                    │    │
│  │  2. Assign APs to sites/networks                                     │    │
│  │  3. Configure network settings (SSID, security, VLAN)                │    │
│  │  4. Ship APs to site                                                 │    │
│  │  5. Connect APs to network (power and Ethernet)                      │    │
│  │  6. APs automatically provision and come online                      │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  Fallback Mechanisms:                                                        │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  - Local configuration cache for cloud outages                       │    │
│  │  - Standalone mode with last-known-good config                       │    │
│  │  - Local management interface for emergency access                   │    │
│  │  - Automatic reconnection with exponential backoff                   │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Appendix BR: Performance Testing

### BR.1 Throughput Testing

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    THROUGHPUT TESTING                                        │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  Test Tools:                                                                 │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  ┌────────────────────────────────────────────────────────────┐     │    │
│  │  │ Tool                Purpose                                │     │    │
│  │  │ ────                ───────                                │     │    │
│  │  │ iperf3              TCP/UDP throughput testing             │     │    │
│  │  │ netperf             Network performance benchmark          │     │    │
│  │  │ speedtest-cli       Internet speed testing                 │     │    │
│  │  │ Chariot             Commercial WiFi testing                │     │    │
│  │  │ Veriwave            Enterprise WiFi testing                │     │    │
│  │  └────────────────────────────────────────────────────────────┘     │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  iperf3 Examples:                                                            │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  # Server side                                                       │    │
│  │  iperf3 -s                                                           │    │
│  │                                                                      │    │
│  │  # Client - TCP throughput                                           │    │
│  │  iperf3 -c 192.168.1.100 -t 60                                       │    │
│  │                                                                      │    │
│  │  # Client - UDP throughput with target bandwidth                     │    │
│  │  iperf3 -c 192.168.1.100 -u -b 500M -t 60                            │    │
│  │                                                                      │    │
│  │  # Client - Bidirectional test                                       │    │
│  │  iperf3 -c 192.168.1.100 --bidir -t 60                               │    │
│  │                                                                      │    │
│  │  # Client - Multiple parallel streams                                │    │
│  │  iperf3 -c 192.168.1.100 -P 4 -t 60                                  │    │
│  │                                                                      │    │
│  │  # Client - Reverse mode (server sends)                              │    │
│  │  iperf3 -c 192.168.1.100 -R -t 60                                    │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  Expected Throughput (Theoretical Max):                                      │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  ┌────────────────────────────────────────────────────────────┐     │    │
│  │  │ Standard      Channel     Streams    Max Rate   Typical    │     │    │
│  │  │ ────────      ───────     ───────    ────────   ───────    │     │    │
│  │  │ 802.11n       40 MHz      2x2        300 Mbps   150 Mbps   │     │    │
│  │  │ 802.11ac      80 MHz      2x2        867 Mbps   400 Mbps   │     │    │
│  │  │ 802.11ac      160 MHz     2x2        1.7 Gbps   800 Mbps   │     │    │
│  │  │ 802.11ax      80 MHz      2x2        1.2 Gbps   600 Mbps   │     │    │
│  │  │ 802.11ax      160 MHz     2x2        2.4 Gbps   1.2 Gbps   │     │    │
│  │  │ 802.11be      320 MHz     2x2        5.8 Gbps   2.5 Gbps   │     │    │
│  │  └────────────────────────────────────────────────────────────┘     │    │
│  │                                                                      │    │
│  │  Note: Typical throughput is ~50% of theoretical maximum             │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### BR.2 Latency and Jitter Testing

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    LATENCY AND JITTER TESTING                                │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  Latency Measurement:                                                        │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  # Basic ping test                                                   │    │
│  │  ping -c 100 192.168.1.1                                             │    │
│  │                                                                      │    │
│  │  # Flood ping (requires root)                                        │    │
│  │  ping -f -c 1000 192.168.1.1                                         │    │
│  │                                                                      │    │
│  │  # Ping with timestamp                                               │    │
│  │  ping -D -c 100 192.168.1.1                                          │    │
│  │                                                                      │    │
│  │  # mtr for path analysis                                             │    │
│  │  mtr -r -c 100 192.168.1.1                                           │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  Jitter Measurement:                                                         │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  # iperf3 UDP with jitter reporting                                  │    │
│  │  iperf3 -c 192.168.1.100 -u -b 10M -t 60                             │    │
│  │                                                                      │    │
│  │  Sample output:                                                      │    │
│  │  [ ID] Interval           Transfer     Bitrate         Jitter        │    │
│  │  [  5]   0.00-60.00  sec  71.5 MBytes  10.0 Mbits/sec  0.123 ms      │    │
│  │                                                                      │    │
│  │  Acceptable jitter values:                                           │    │
│  │  - VoIP: < 30 ms                                                     │    │
│  │  - Video: < 50 ms                                                    │    │
│  │  - Data: < 100 ms                                                    │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  Latency Targets:                                                            │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  ┌────────────────────────────────────────────────────────────┐     │    │
│  │  │ Application         Target Latency    Acceptable          │     │    │
│  │  │ ───────────         ──────────────    ──────────          │     │    │
│  │  │ VoIP                < 50 ms           < 150 ms            │     │    │
│  │  │ Video Conference    < 100 ms          < 200 ms            │     │    │
│  │  │ Online Gaming       < 30 ms           < 100 ms            │     │    │
│  │  │ Web Browsing        < 100 ms          < 500 ms            │     │    │
│  │  │ File Transfer       < 200 ms          < 1000 ms           │     │    │
│  │  └────────────────────────────────────────────────────────────┘     │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Appendix BS: Regulatory Compliance Testing

### BS.1 RF Emissions Testing

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    RF EMISSIONS TESTING                                      │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  FCC Part 15 Requirements:                                                   │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  ┌────────────────────────────────────────────────────────────┐     │    │
│  │  │ Band              Max EIRP        Max Power Spectral Density│    │    │
│  │  │ ────              ────────        ─────────────────────────│     │    │
│  │  │ 2.4 GHz           36 dBm          17 dBm/MHz               │     │    │
│  │  │ U-NII-1           36 dBm          17 dBm/MHz               │     │    │
│  │  │ U-NII-2A          30 dBm          11 dBm/MHz               │     │    │
│  │  │ U-NII-2C          30 dBm          11 dBm/MHz               │     │    │
│  │  │ U-NII-3           36 dBm          17 dBm/MHz               │     │    │
│  │  │ 6 GHz (LPI)       30 dBm          5 dBm/MHz                │     │    │
│  │  │ 6 GHz (SP)        36 dBm          23 dBm/MHz               │     │    │
│  │  └────────────────────────────────────────────────────────────┘     │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  Test Equipment:                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  ┌────────────────────────────────────────────────────────────┐     │    │
│  │  │ Equipment               Purpose                            │     │    │
│  │  │ ─────────               ───────                            │     │    │
│  │  │ Spectrum Analyzer       Measure RF emissions               │     │    │
│  │  │ Power Meter             Measure transmit power             │     │    │
│  │  │ Anechoic Chamber        Controlled RF environment          │     │    │
│  │  │ Reference Antenna       Calibrated measurement antenna     │     │    │
│  │  │ Signal Generator        Generate test signals              │     │    │
│  │  │ Vector Network Analyzer Antenna characterization           │     │    │
│  │  └────────────────────────────────────────────────────────────┘     │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  DFS Testing:                                                                │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  Test Cases:                                                         │    │
│  │  - Channel Availability Check (CAC): 60 seconds minimum             │    │
│  │  - Non-Occupancy Period (NOP): 30 minutes minimum                   │    │
│  │  - Radar Detection: Must detect within 200 ms                       │    │
│  │  - Channel Move Time: Must vacate within 10 seconds                 │    │
│  │                                                                      │    │
│  │  Radar Patterns (FCC):                                               │    │
│  │  - Type 0: Short pulse (1 μs)                                        │    │
│  │  - Type 1: Short pulse (1-5 μs)                                      │    │
│  │  - Type 2: Long pulse (1-5 μs)                                       │    │
│  │  - Type 3: Short pulse (6-10 μs)                                     │    │
│  │  - Type 4: Long pulse (11-20 μs)                                     │    │
│  │  - Type 5: Variable pulse                                            │    │
│  │  - Type 6: Long pulse (> 100 μs)                                     │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Appendix BT: Troubleshooting Checklists

### BT.1 Connection Issues Checklist

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    CONNECTION ISSUES CHECKLIST                               │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  Client Cannot See SSID:                                                     │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  [ ] AP is powered on and operational                                │    │
│  │  [ ] SSID broadcast is enabled                                       │    │
│  │  [ ] Client supports the band (2.4/5/6 GHz)                          │    │
│  │  [ ] Client is within range                                          │    │
│  │  [ ] No MAC filtering blocking client                                │    │
│  │  [ ] SSID is not hidden (or client has profile)                      │    │
│  │  [ ] Regulatory domain allows channel                                │    │
│  │  [ ] DFS channel not in CAC or NOP                                   │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  Authentication Failure:                                                     │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  [ ] Correct password/credentials                                    │    │
│  │  [ ] Security type matches (WPA2/WPA3)                               │    │
│  │  [ ] RADIUS server reachable                                         │    │
│  │  [ ] RADIUS shared secret correct                                    │    │
│  │  [ ] Certificate valid and trusted                                   │    │
│  │  [ ] User account not locked/expired                                 │    │
│  │  [ ] EAP method supported by client                                  │    │
│  │  [ ] Time synchronized (for certificates)                            │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  Association Failure:                                                        │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  [ ] AP not at maximum client capacity                               │    │
│  │  [ ] Client supports required features (MFP, etc.)                   │    │
│  │  [ ] No rate limiting blocking association                           │    │
│  │  [ ] VLAN configured correctly                                       │    │
│  │  [ ] No ACL blocking client                                          │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  No IP Address:                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  [ ] DHCP server running                                             │    │
│  │  [ ] DHCP pool not exhausted                                         │    │
│  │  [ ] VLAN trunking correct                                           │    │
│  │  [ ] DHCP relay configured (if needed)                               │    │
│  │  [ ] Client DHCP enabled                                             │    │
│  │  [ ] No firewall blocking DHCP                                       │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  Slow Performance:                                                           │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  [ ] Check signal strength (RSSI > -70 dBm)                          │    │
│  │  [ ] Check channel utilization (< 70%)                               │    │
│  │  [ ] Check for interference                                          │    │
│  │  [ ] Check client capabilities (802.11n/ac/ax)                       │    │
│  │  [ ] Check for legacy clients slowing network                        │    │
│  │  [ ] Check backhaul bandwidth                                        │    │
│  │  [ ] Check for rate limiting                                         │    │
│  │  [ ] Check QoS configuration                                         │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Document Revision History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2026-01-08 | Auto-generated | Initial document creation |
| 1.1 | 2026-01-08 | Auto-generated | Added packet capture analysis, regulatory domains, client compatibility |
| 1.2 | 2026-01-08 | Auto-generated | Added EAP methods, band steering, load balancing, mesh networking, power save |
| 1.3 | 2026-01-08 | Auto-generated | Added RADIUS attributes, debug commands, troubleshooting flowchart, quick reference |
| 1.4 | 2026-01-08 | Auto-generated | Added WiFi 7 features, Hotspot 2.0 deep dive, glossary, standards reference |
| 1.5 | 2026-01-08 | Auto-generated | Added security attacks, performance optimization, complete hostapd config |
| 1.6 | 2026-01-08 | Auto-generated | Added frame formats, information elements, status/reason codes |
| 1.7 | 2026-01-08 | Auto-generated | Added vendor extensions, debugging/logging, packet capture commands |
| 1.8 | 2026-01-08 | Auto-generated | Added test case reference, regulatory domain deep dive |
| 1.9 | 2026-01-08 | Auto-generated | Added action frame reference, error scenarios and troubleshooting |
| 2.0 | 2026-01-08 | Auto-generated | Added Wireshark filter reference, complete configuration examples |
| 2.1 | 2026-01-08 | Auto-generated | Added performance benchmarks, client device compatibility matrix |
| 2.2 | 2026-01-08 | Auto-generated | Added WiFi Alliance certification, security checklist, capacity planning |
| 2.3 | 2026-01-08 | Auto-generated | Added antenna/RF considerations, troubleshooting trees, timing diagrams |
| 2.4 | 2026-01-08 | Auto-generated | Added QoS/WMM, deployment topologies, compliance, advanced debugging |
| 2.5 | 2026-01-08 | Auto-generated | Added supplicant config, VLAN, rate limiting, HA, IoT profiling |
| 2.6 | 2026-01-08 | Auto-generated | Added captive portal, location services, spectrum analysis, migration, API |
| 2.7 | 2026-01-08 | Auto-generated | Added multicast, VoWiFi, enterprise integration, monitoring, disaster recovery |
| 2.8 | 2026-01-08 | Auto-generated | Added WIDS, cloud management, performance testing, compliance, checklists |
| 2.9 | 2026-01-08 | Auto-generated | Added outdoor WiFi, stadium/venue, healthcare, education deployments |

---

## Appendix BU: Outdoor WiFi Deployments

### BU.1 Outdoor AP Considerations

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    OUTDOOR AP CONSIDERATIONS                                 │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  Environmental Factors:                                                      │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  ┌────────────────────────────────────────────────────────────┐     │    │
│  │  │ Factor              Consideration                          │     │    │
│  │  │ ──────              ─────────────                          │     │    │
│  │  │ Temperature         -40°C to +65°C operating range         │     │    │
│  │  │ Humidity            0-100% condensing                      │     │    │
│  │  │ Rain/Snow           IP67 or higher enclosure               │     │    │
│  │  │ Wind                Mounting rated for wind load           │     │    │
│  │  │ Lightning           Surge protection required              │     │    │
│  │  │ UV Exposure         UV-resistant housing                   │     │    │
│  │  │ Salt Spray          Marine-grade for coastal               │     │    │
│  │  └────────────────────────────────────────────────────────────┘     │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  IP Rating Reference:                                                        │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  ┌────────────────────────────────────────────────────────────┐     │    │
│  │  │ Rating    Solid Protection         Liquid Protection      │     │    │
│  │  │ ──────    ────────────────         ─────────────────      │     │    │
│  │  │ IP65      Dust tight               Water jets             │     │    │
│  │  │ IP66      Dust tight               Powerful water jets    │     │    │
│  │  │ IP67      Dust tight               Immersion (1m, 30min)  │     │    │
│  │  │ IP68      Dust tight               Continuous immersion   │     │    │
│  │  └────────────────────────────────────────────────────────────┘     │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  Power Options:                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  ┌────────────────────────────────────────────────────────────┐     │    │
│  │  │ Option              Max Power       Distance               │     │    │
│  │  │ ──────              ─────────       ────────               │     │    │
│  │  │ PoE (802.3af)       15.4W           100m                   │     │    │
│  │  │ PoE+ (802.3at)      30W             100m                   │     │    │
│  │  │ PoE++ (802.3bt)     60-90W          100m                   │     │    │
│  │  │ Fiber + PoE         30W             Unlimited              │     │    │
│  │  │ Solar               Varies          N/A                    │     │    │
│  │  │ DC Power            Varies          Varies                 │     │    │
│  │  └────────────────────────────────────────────────────────────┘     │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  Antenna Types for Outdoor:                                                  │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  ┌────────────────────────────────────────────────────────────┐     │    │
│  │  │ Type                Gain        Beamwidth    Use Case      │     │    │
│  │  │ ────                ────        ─────────    ────────      │     │    │
│  │  │ Omni-directional    6-9 dBi     360°         General       │     │    │
│  │  │ Sector              12-17 dBi   60-120°      Directional   │     │    │
│  │  │ Panel               14-19 dBi   30-60°       Point-to-area │     │    │
│  │  │ Parabolic           24-30 dBi   5-15°        Point-to-point│     │    │
│  │  │ Yagi                12-18 dBi   30-45°       Long range    │     │    │
│  │  └────────────────────────────────────────────────────────────┘     │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### BU.2 Point-to-Point Links

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    POINT-TO-POINT LINKS                                      │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  Link Budget Calculation:                                                    │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  Link Budget = Tx Power + Tx Antenna Gain + Rx Antenna Gain          │    │
│  │                - Free Space Path Loss - Cable Loss - Fade Margin     │    │
│  │                                                                      │    │
│  │  Free Space Path Loss (dB) = 20*log10(d) + 20*log10(f) + 32.44       │    │
│  │  Where: d = distance in km, f = frequency in MHz                     │    │
│  │                                                                      │    │
│  │  Example: 5 GHz, 5 km link                                           │    │
│  │  ┌────────────────────────────────────────────────────────────┐     │    │
│  │  │ Component                Value                             │     │    │
│  │  │ ─────────                ─────                             │     │    │
│  │  │ Tx Power                 +23 dBm                           │     │    │
│  │  │ Tx Antenna Gain          +24 dBi                           │     │    │
│  │  │ Rx Antenna Gain          +24 dBi                           │     │    │
│  │  │ Free Space Path Loss     -126 dB                           │     │    │
│  │  │ Cable Loss               -2 dB                             │     │    │
│  │  │ Fade Margin              -10 dB                            │     │    │
│  │  │ ─────────────────────────────────                          │     │    │
│  │  │ Received Signal          -67 dBm                           │     │    │
│  │  │ Rx Sensitivity           -90 dBm                           │     │    │
│  │  │ Link Margin              +23 dB (Good)                     │     │    │
│  │  └────────────────────────────────────────────────────────────┘     │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  Fresnel Zone Clearance:                                                     │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  First Fresnel Zone Radius (m) = 17.3 * sqrt(d / (4 * f))            │    │
│  │  Where: d = distance in km, f = frequency in GHz                     │    │
│  │                                                                      │    │
│  │  Minimum clearance: 60% of first Fresnel zone                        │    │
│  │                                                                      │    │
│  │  Example: 5 GHz, 5 km link                                           │    │
│  │  First Fresnel Zone = 17.3 * sqrt(5 / (4 * 5)) = 8.65 m              │    │
│  │  Minimum clearance = 0.6 * 8.65 = 5.2 m                              │    │
│  │                                                                      │    │
│  │  ┌─────────────────────────────────────────────────────────────┐    │    │
│  │  │                                                              │    │    │
│  │  │  AP1 ─────────────────────────────────────────────────── AP2 │    │    │
│  │  │       \                                                 /    │    │    │
│  │  │        \              Fresnel Zone                     /     │    │    │
│  │  │         \─────────────────────────────────────────────/      │    │    │
│  │  │                                                              │    │    │
│  │  │  ═══════════════════════════════════════════════════════════ │    │    │
│  │  │                        Ground                                │    │    │
│  │  │                                                              │    │    │
│  │  └─────────────────────────────────────────────────────────────┘    │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Appendix BV: Stadium and Venue WiFi

### BV.1 High-Density Deployment

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    HIGH-DENSITY DEPLOYMENT                                   │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  Capacity Planning:                                                          │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  ┌────────────────────────────────────────────────────────────┐     │    │
│  │  │ Venue Type          Clients/AP    AP Density               │     │    │
│  │  │ ──────────          ──────────    ──────────               │     │    │
│  │  │ Stadium             25-50         1 AP per 50-100 seats    │     │    │
│  │  │ Convention Center   30-50         1 AP per 1000 sq ft      │     │    │
│  │  │ Auditorium          25-40         1 AP per 50 seats        │     │    │
│  │  │ Lecture Hall        30-50         1 AP per 75 seats        │     │    │
│  │  │ Trade Show          20-30         1 AP per 500 sq ft       │     │    │
│  │  └────────────────────────────────────────────────────────────┘     │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  Antenna Strategies:                                                         │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  Under-Seat Deployment:                                              │    │
│  │  ┌─────────────────────────────────────────────────────────────┐    │    │
│  │  │                                                              │    │    │
│  │  │  ┌─────┐ ┌─────┐ ┌─────┐ ┌─────┐ ┌─────┐ ┌─────┐ ┌─────┐    │    │    │
│  │  │  │Seat │ │Seat │ │Seat │ │Seat │ │Seat │ │Seat │ │Seat │    │    │    │
│  │  │  └──┬──┘ └─────┘ └─────┘ └──┬──┘ └─────┘ └─────┘ └──┬──┘    │    │    │
│  │  │     │                       │                       │       │    │    │
│  │  │    [AP]                    [AP]                    [AP]     │    │    │
│  │  │                                                              │    │    │
│  │  │  Benefits:                                                   │    │    │
│  │  │  - Low power, small cells                                    │    │    │
│  │  │  - Reduced interference                                      │    │    │
│  │  │  - Better frequency reuse                                    │    │    │
│  │  │                                                              │    │    │
│  │  └─────────────────────────────────────────────────────────────┘    │    │
│  │                                                                      │    │
│  │  Overhead Deployment:                                                │    │
│  │  ┌─────────────────────────────────────────────────────────────┐    │    │
│  │  │                                                              │    │    │
│  │  │           [AP]              [AP]              [AP]           │    │    │
│  │  │            │                 │                 │             │    │    │
│  │  │            ▼                 ▼                 ▼             │    │    │
│  │  │  ┌─────┐ ┌─────┐ ┌─────┐ ┌─────┐ ┌─────┐ ┌─────┐ ┌─────┐    │    │    │
│  │  │  │Seat │ │Seat │ │Seat │ │Seat │ │Seat │ │Seat │ │Seat │    │    │    │
│  │  │  └─────┘ └─────┘ └─────┘ └─────┘ └─────┘ └─────┘ └─────┘    │    │    │
│  │  │                                                              │    │    │
│  │  │  Benefits:                                                   │    │    │
│  │  │  - Easier installation                                       │    │    │
│  │  │  - Better coverage per AP                                    │    │    │
│  │  │  - Directional antennas possible                             │    │    │
│  │  │                                                              │    │    │
│  │  └─────────────────────────────────────────────────────────────┘    │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  Channel Planning for High Density:                                          │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  5 GHz with 20 MHz channels (more channels, less interference):     │    │
│  │                                                                      │    │
│  │  ┌────────────────────────────────────────────────────────────┐     │    │
│  │  │ Channel    36   40   44   48   52   56   60   64           │     │    │
│  │  │ Channel   100  104  108  112  116  120  124  128           │     │    │
│  │  │ Channel   132  136  140  144  149  153  157  161  165      │     │    │
│  │  └────────────────────────────────────────────────────────────┘     │    │
│  │                                                                      │    │
│  │  Total: 25 non-overlapping 20 MHz channels in 5 GHz                  │    │
│  │                                                                      │    │
│  │  6 GHz adds 59 additional 20 MHz channels                            │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Appendix BW: Healthcare WiFi

### BW.1 Medical Device Considerations

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    MEDICAL DEVICE CONSIDERATIONS                             │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  Medical Device Categories:                                                  │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  ┌────────────────────────────────────────────────────────────┐     │    │
│  │  │ Category            Examples                   Priority   │     │    │
│  │  │ ────────            ────────                   ────────   │     │    │
│  │  │ Life-Critical       Telemetry, infusion pumps  Highest    │     │    │
│  │  │ Clinical            Vital signs monitors       High       │     │    │
│  │  │ Diagnostic          Portable X-ray, ultrasound Medium     │     │    │
│  │  │ Administrative      Tablets, workstations      Normal     │     │    │
│  │  │ Guest               Patient entertainment      Low        │     │    │
│  │  └────────────────────────────────────────────────────────────┘     │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  Network Segmentation:                                                       │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  ┌────────────────────────────────────────────────────────────┐     │    │
│  │  │ SSID                VLAN    Security        Purpose        │     │    │
│  │  │ ────                ────    ────────        ───────        │     │    │
│  │  │ Medical-Critical    10      WPA3-Enterprise Telemetry      │     │    │
│  │  │ Medical-Clinical    20      WPA3-Enterprise Clinical       │     │    │
│  │  │ Staff               30      WPA3-Enterprise Staff devices  │     │    │
│  │  │ Guest               999     WPA3-Personal   Patient/visitor│     │    │
│  │  └────────────────────────────────────────────────────────────┘     │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  QoS for Medical Devices:                                                    │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  # hostapd.conf for medical network                                  │    │
│  │  wmm_enabled=1                                                       │    │
│  │                                                                      │    │
│  │  # Prioritize medical device traffic                                 │    │
│  │  # Mark telemetry as Voice (AC_VO)                                   │    │
│  │  # Mark clinical as Video (AC_VI)                                    │    │
│  │                                                                      │    │
│  │  # iptables DSCP marking                                             │    │
│  │  iptables -t mangle -A PREROUTING -s 10.10.0.0/24 \                  │    │
│  │      -j DSCP --set-dscp-class EF                                     │    │
│  │  iptables -t mangle -A PREROUTING -s 10.20.0.0/24 \                  │    │
│  │      -j DSCP --set-dscp-class AF41                                   │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  Compliance Requirements:                                                    │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  ┌────────────────────────────────────────────────────────────┐     │    │
│  │  │ Regulation          Requirement                            │     │    │
│  │  │ ──────────          ───────────                            │     │    │
│  │  │ HIPAA               Encryption, access control, audit logs │     │    │
│  │  │ FDA 21 CFR Part 11  Electronic records, signatures         │     │    │
│  │  │ IEC 80001-1         Medical IT network risk management     │     │    │
│  │  │ Joint Commission    Environment of care standards          │     │    │
│  │  └────────────────────────────────────────────────────────────┘     │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Appendix BX: Education WiFi

### BX.1 K-12 and Higher Education

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    K-12 AND HIGHER EDUCATION                                 │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  Typical Deployment Scenarios:                                               │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  ┌────────────────────────────────────────────────────────────┐     │    │
│  │  │ Area                Clients/AP    AP Placement             │     │    │
│  │  │ ────                ──────────    ────────────             │     │    │
│  │  │ Classroom           30-40         1 per classroom          │     │    │
│  │  │ Library             50-75         1 per 1500 sq ft         │     │    │
│  │  │ Cafeteria           100-150       1 per 1000 sq ft         │     │    │
│  │  │ Auditorium          200-300       1 per 50 seats           │     │    │
│  │  │ Gymnasium           100-200       High-mount directional   │     │    │
│  │  │ Dormitory           2-4           1 per 2-4 rooms          │     │    │
│  │  │ Outdoor             50-100        Weatherproof, directional│     │    │
│  │  └────────────────────────────────────────────────────────────┘     │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  Network Segmentation:                                                       │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  ┌────────────────────────────────────────────────────────────┐     │    │
│  │  │ SSID                VLAN    Users                          │     │    │
│  │  │ ────                ────    ─────                          │     │    │
│  │  │ Staff               10      Faculty and staff              │     │    │
│  │  │ Student             20      Student devices                │     │    │
│  │  │ 1:1-Devices         30      School-issued devices          │     │    │
│  │  │ IoT                 40      Printers, displays, sensors    │     │    │
│  │  │ Guest               999     Visitors                       │     │    │
│  │  └────────────────────────────────────────────────────────────┘     │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  Content Filtering (CIPA Compliance):                                        │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  Children's Internet Protection Act (CIPA) Requirements:            │    │
│  │  - Block access to obscene content                                   │    │
│  │  - Block access to harmful content                                   │    │
│  │  - Monitor online activities                                         │    │
│  │                                                                      │    │
│  │  Implementation Options:                                             │    │
│  │  - DNS-based filtering (OpenDNS, Cloudflare Gateway)                 │    │
│  │  - Proxy-based filtering (Squid, Blue Coat)                          │    │
│  │  - Firewall-based filtering (Palo Alto, Fortinet)                    │    │
│  │  - Cloud-based filtering (Lightspeed, GoGuardian)                    │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  1:1 Device Programs:                                                        │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  Authentication Options:                                             │    │
│  │  - Device certificates (EAP-TLS)                                     │    │
│  │  - MDM-provisioned credentials                                       │    │
│  │  - MAC authentication with device inventory                          │    │
│  │                                                                      │    │
│  │  MDM Integration:                                                    │    │
│  │  - Jamf (Apple devices)                                              │    │
│  │  - Intune (Windows/iOS/Android)                                      │    │
│  │  - Google Workspace (Chromebooks)                                    │    │
│  │  - Mosyle (Apple devices)                                            │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Appendix BY: Retail and Hospitality WiFi

### BY.1 Guest WiFi Best Practices

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    GUEST WIFI BEST PRACTICES                                 │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  Authentication Methods:                                                     │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  ┌────────────────────────────────────────────────────────────┐     │    │
│  │  │ Method              Pros                    Cons           │     │    │
│  │  │ ──────              ────                    ────           │     │    │
│  │  │ Open + Captive      Easy for guests         No encryption  │     │    │
│  │  │ Social Login        Marketing data          Privacy issues │     │    │
│  │  │ SMS Verification    Identity verification   Cost per SMS   │     │    │
│  │  │ Email Registration  Contact collection      Fake emails    │     │    │
│  │  │ Room/Ticket Code    Ties to purchase        Code sharing   │     │    │
│  │  │ Passpoint           Seamless, encrypted     Setup required │     │    │
│  │  └────────────────────────────────────────────────────────────┘     │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  Captive Portal Design:                                                      │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  Best Practices:                                                     │    │
│  │  - Mobile-responsive design                                          │    │
│  │  - Minimal required fields                                           │    │
│  │  - Clear terms of service                                            │    │
│  │  - Brand-consistent styling                                          │    │
│  │  - Fast loading (< 3 seconds)                                        │    │
│  │  - Support for multiple languages                                    │    │
│  │  - Accessibility compliance (WCAG 2.1)                               │    │
│  │                                                                      │    │
│  │  Required Legal Elements:                                            │    │
│  │  - Terms of Service acceptance                                       │    │
│  │  - Privacy Policy link                                               │    │
│  │  - Acceptable Use Policy                                             │    │
│  │  - GDPR consent (if applicable)                                      │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  Bandwidth Management:                                                       │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  ┌────────────────────────────────────────────────────────────┐     │    │
│  │  │ Tier                Download    Upload      Use Case       │     │    │
│  │  │ ────                ────────    ──────      ────────       │     │    │
│  │  │ Basic (Free)        2 Mbps      1 Mbps      Email, browse  │     │    │
│  │  │ Standard            10 Mbps     5 Mbps      Video stream   │     │    │
│  │  │ Premium (Paid)      50 Mbps     25 Mbps     Business use   │     │    │
│  │  │ VIP                 100 Mbps    50 Mbps     Unlimited      │     │    │
│  │  └────────────────────────────────────────────────────────────┘     │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  Analytics and Marketing:                                                    │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  Data Collection (with consent):                                     │    │
│  │  - Visit frequency and duration                                      │    │
│  │  - Device types and capabilities                                     │    │
│  │  - Traffic patterns and peak times                                   │    │
│  │  - Popular content/applications                                      │    │
│  │  - Return visitor identification                                     │    │
│  │                                                                      │    │
│  │  Marketing Integration:                                              │    │
│  │  - Email marketing opt-in                                            │    │
│  │  - Social media follows                                              │    │
│  │  - Loyalty program enrollment                                        │    │
│  │  - Survey and feedback collection                                    │    │
│  │  - Location-based promotions                                         │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Appendix BZ: Industrial WiFi

### BZ.1 Manufacturing and Warehouse

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    MANUFACTURING AND WAREHOUSE                               │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  Industrial Environment Challenges:                                          │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  ┌────────────────────────────────────────────────────────────┐     │    │
│  │  │ Challenge           Impact              Mitigation         │     │    │
│  │  │ ─────────           ──────              ──────────         │     │    │
│  │  │ Metal structures    RF reflection       Directional antennas│    │    │
│  │  │ Moving equipment    Variable coverage   Overlapping cells  │     │    │
│  │  │ RF interference     Packet loss         Spectrum analysis  │     │    │
│  │  │ Dust/debris         AP damage           Industrial enclosures│   │    │
│  │  │ Temperature         Component failure   Extended temp APs  │     │    │
│  │  │ Vibration           Connection drops    Ruggedized mounting│     │    │
│  │  └────────────────────────────────────────────────────────────┘     │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  Industrial IoT Devices:                                                     │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  ┌────────────────────────────────────────────────────────────┐     │    │
│  │  │ Device Type         Protocol        Latency Requirement   │     │    │
│  │  │ ───────────         ────────        ───────────────────   │     │    │
│  │  │ Barcode scanners    802.11n/ac      < 100 ms              │     │    │
│  │  │ AGVs/AMRs           802.11ac/ax     < 50 ms               │     │    │
│  │  │ Voice picking       802.11n/ac      < 150 ms              │     │    │
│  │  │ RFID readers        802.11n         < 200 ms              │     │    │
│  │  │ Tablets/handhelds   802.11ac/ax     < 100 ms              │     │    │
│  │  │ Sensors             802.11ah        < 1000 ms             │     │    │
│  │  │ Cameras             802.11ac/ax     < 50 ms               │     │    │
│  │  └────────────────────────────────────────────────────────────┘     │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  Roaming for Mobile Devices:                                                 │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  Requirements for AGVs and Mobile Workers:                           │    │
│  │  - Fast roaming (< 50 ms handoff)                                    │    │
│  │  - 802.11r Fast Transition                                           │    │
│  │  - 802.11k Neighbor Reports                                          │    │
│  │  - 802.11v BSS Transition Management                                 │    │
│  │  - Overlapping coverage (20-30%)                                     │    │
│  │  - Consistent RSSI (-67 dBm minimum)                                 │    │
│  │                                                                      │    │
│  │  # hostapd.conf for industrial roaming                               │    │
│  │  ieee80211r=1                                                        │    │
│  │  ft_over_ds=1                                                        │    │
│  │  ft_psk_generate_local=1                                             │    │
│  │  rrm_neighbor_report=1                                               │    │
│  │  bss_transition=1                                                    │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Document Revision History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2026-01-08 | Auto-generated | Initial document creation |
| 1.1 | 2026-01-08 | Auto-generated | Added packet capture analysis, regulatory domains, client compatibility |
| 1.2 | 2026-01-08 | Auto-generated | Added EAP methods, band steering, load balancing, mesh networking, power save |
| 1.3 | 2026-01-08 | Auto-generated | Added RADIUS attributes, debug commands, troubleshooting flowchart, quick reference |
| 1.4 | 2026-01-08 | Auto-generated | Added WiFi 7 features, Hotspot 2.0 deep dive, glossary, standards reference |
| 1.5 | 2026-01-08 | Auto-generated | Added security attacks, performance optimization, complete hostapd config |
| 1.6 | 2026-01-08 | Auto-generated | Added frame formats, information elements, status/reason codes |
| 1.7 | 2026-01-08 | Auto-generated | Added vendor extensions, debugging/logging, packet capture commands |
| 1.8 | 2026-01-08 | Auto-generated | Added test case reference, regulatory domain deep dive |
| 1.9 | 2026-01-08 | Auto-generated | Added action frame reference, error scenarios and troubleshooting |
| 2.0 | 2026-01-08 | Auto-generated | Added Wireshark filter reference, complete configuration examples |
| 2.1 | 2026-01-08 | Auto-generated | Added performance benchmarks, client device compatibility matrix |
| 2.2 | 2026-01-08 | Auto-generated | Added WiFi Alliance certification, security checklist, capacity planning |
| 2.3 | 2026-01-08 | Auto-generated | Added antenna/RF considerations, troubleshooting trees, timing diagrams |
| 2.4 | 2026-01-08 | Auto-generated | Added QoS/WMM, deployment topologies, compliance, advanced debugging |
| 2.5 | 2026-01-08 | Auto-generated | Added supplicant config, VLAN, rate limiting, HA, IoT profiling |
| 2.6 | 2026-01-08 | Auto-generated | Added captive portal, location services, spectrum analysis, migration, API |
| 2.7 | 2026-01-08 | Auto-generated | Added multicast, VoWiFi, enterprise integration, monitoring, disaster recovery |
| 2.8 | 2026-01-08 | Auto-generated | Added WIDS, cloud management, performance testing, compliance, checklists |
| 2.9 | 2026-01-08 | Auto-generated | Added outdoor WiFi, stadium/venue, healthcare, education, retail, industrial |
| 3.0 | 2026-01-08 | Auto-generated | Added WiFi 6E/7 deep dive, OFDMA, MU-MIMO, BSS coloring, TWT |

---

## Appendix CA: WiFi 6E Deep Dive

### CA.1 6 GHz Band Overview

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    6 GHz BAND OVERVIEW                                       │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  6 GHz Spectrum Allocation:                                                  │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  5925 MHz                                              7125 MHz      │    │
│  │    │                                                      │          │    │
│  │    ▼                                                      ▼          │    │
│  │  ┌────────────────────────────────────────────────────────┐          │    │
│  │  │                    1200 MHz                            │          │    │
│  │  │                                                        │          │    │
│  │  │  U-NII-5    U-NII-6    U-NII-7    U-NII-8              │          │    │
│  │  │  5925-6425  6425-6525  6525-6875  6875-7125            │          │    │
│  │  │  500 MHz    100 MHz    350 MHz    250 MHz              │          │    │
│  │  │                                                        │          │    │
│  │  └────────────────────────────────────────────────────────┘          │    │
│  │                                                                      │    │
│  │  Channel Availability:                                               │    │
│  │  ┌────────────────────────────────────────────────────────────┐     │    │
│  │  │ Width       Channels    Total                              │     │    │
│  │  │ ─────       ────────    ─────                              │     │    │
│  │  │ 20 MHz      59          59 non-overlapping                 │     │    │
│  │  │ 40 MHz      29          29 non-overlapping                 │     │    │
│  │  │ 80 MHz      14          14 non-overlapping                 │     │    │
│  │  │ 160 MHz     7           7 non-overlapping                  │     │    │
│  │  │ 320 MHz     3           3 non-overlapping (WiFi 7)         │     │    │
│  │  └────────────────────────────────────────────────────────────┘     │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  Power Classes:                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  ┌────────────────────────────────────────────────────────────┐     │    │
│  │  │ Class               Max EIRP    PSD           Use Case     │     │    │
│  │  │ ─────               ────────    ───           ────────     │     │    │
│  │  │ Low Power Indoor    30 dBm      5 dBm/MHz     Indoor only  │     │    │
│  │  │ Standard Power      36 dBm      23 dBm/MHz    AFC required │     │    │
│  │  │ Very Low Power      14 dBm      -8 dBm/MHz    Wearables    │     │    │
│  │  └────────────────────────────────────────────────────────────┘     │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  AFC (Automated Frequency Coordination):                                     │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  Purpose: Protect incumbent users (fixed satellite, microwave)       │    │
│  │                                                                      │    │
│  │  Flow:                                                               │    │
│  │  1. AP sends location (GPS or manual) to AFC server                  │    │
│  │  2. AFC server checks incumbent database                             │    │
│  │  3. AFC returns allowed channels and power levels                    │    │
│  │  4. AP operates within allowed parameters                            │    │
│  │  5. Periodic re-query (every 24 hours)                               │    │
│  │                                                                      │    │
│  │  AFC Providers (FCC approved):                                       │    │
│  │  - Broadcom                                                          │    │
│  │  - Google                                                            │    │
│  │  - Sony                                                              │    │
│  │  - Federated Wireless                                                │    │
│  │  - Qualcomm                                                          │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### CA.2 6 GHz Discovery Mechanisms

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    6 GHz DISCOVERY MECHANISMS                                │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  Discovery Challenge:                                                        │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  Problem: 59 channels × scanning time = very slow discovery          │    │
│  │                                                                      │    │
│  │  Solutions:                                                          │    │
│  │  1. Reduced Neighbor Report (RNR) in 2.4/5 GHz beacons               │    │
│  │  2. FILS Discovery frames                                            │    │
│  │  3. Unsolicited Probe Response (UPR)                                 │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  Reduced Neighbor Report (RNR):                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  ┌─────────────────────────────────────────────────────────────┐    │    │
│  │  │                                                              │    │    │
│  │  │  2.4/5 GHz AP                        6 GHz AP                │    │    │
│  │  │      │                                   │                   │    │    │
│  │  │      │ ── Beacon with RNR ──────────────>│                   │    │    │
│  │  │      │    (6 GHz channel info)           │                   │    │    │
│  │  │      │                                   │                   │    │    │
│  │  │  Client                                  │                   │    │    │
│  │  │      │                                   │                   │    │    │
│  │  │      │ ── Receives RNR ──────────────────│                   │    │    │
│  │  │      │                                   │                   │    │    │
│  │  │      │ ── Direct probe to 6 GHz ─────────>│                  │    │    │
│  │  │      │                                   │                   │    │    │
│  │  │      │ <── Probe Response ───────────────│                   │    │    │
│  │  │      │                                   │                   │    │    │
│  │  └─────────────────────────────────────────────────────────────┘    │    │
│  │                                                                      │    │
│  │  RNR Element Format:                                                 │    │
│  │  ┌────────────────────────────────────────────────────────────┐     │    │
│  │  │ Field                   Size        Description            │     │    │
│  │  │ ─────                   ────        ───────────            │     │    │
│  │  │ Element ID              1 byte      201                    │     │    │
│  │  │ Length                  1 byte      Variable               │     │    │
│  │  │ Neighbor AP Info        Variable    TBTT info, channel     │     │    │
│  │  └────────────────────────────────────────────────────────────┘     │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  FILS Discovery Frame:                                                       │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  Purpose: Lightweight beacon alternative for 6 GHz                   │    │
│  │                                                                      │    │
│  │  Characteristics:                                                    │    │
│  │  - Shorter than full beacon                                          │    │
│  │  - Contains essential discovery info                                 │    │
│  │  - Transmitted at 20 TUs (vs 100 TUs for beacon)                     │    │
│  │                                                                      │    │
│  │  Contents:                                                           │    │
│  │  - SSID (short or full)                                              │    │
│  │  - Capability information                                            │    │
│  │  - Operating class and channel                                       │    │
│  │  - Primary channel                                                   │    │
│  │  - AP configuration sequence number                                  │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  Unsolicited Probe Response (UPR):                                           │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  Purpose: Broadcast probe response without request                   │    │
│  │                                                                      │    │
│  │  Interval: Configurable (typically 20 TUs)                           │    │
│  │                                                                      │    │
│  │  # hostapd.conf                                                      │    │
│  │  unsol_bcast_probe_resp_interval=20                                  │    │
│  │  fils_discovery_max_interval=20                                      │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Appendix CB: OFDMA Deep Dive

### CB.1 OFDMA Fundamentals

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    OFDMA FUNDAMENTALS                                        │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  OFDM vs OFDMA:                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  OFDM (802.11a/g/n/ac):                                              │    │
│  │  ┌────────────────────────────────────────────────────────────┐     │    │
│  │  │                                                             │     │    │
│  │  │  Time ──────────────────────────────────────────────────>   │     │    │
│  │  │                                                             │     │    │
│  │  │  ┌─────────────────────────────────────────────────────┐   │     │    │
│  │  │  │              Client A (all subcarriers)             │   │     │    │
│  │  │  └─────────────────────────────────────────────────────┘   │     │    │
│  │  │  ┌─────────────────────────────────────────────────────┐   │     │    │
│  │  │  │              Client B (all subcarriers)             │   │     │    │
│  │  │  └─────────────────────────────────────────────────────┘   │     │    │
│  │  │  ┌─────────────────────────────────────────────────────┐   │     │    │
│  │  │  │              Client C (all subcarriers)             │   │     │    │
│  │  │  └─────────────────────────────────────────────────────┘   │     │    │
│  │  │                                                             │     │    │
│  │  │  One client at a time uses entire channel                  │     │    │
│  │  │                                                             │     │    │
│  │  └────────────────────────────────────────────────────────────┘     │    │
│  │                                                                      │    │
│  │  OFDMA (802.11ax/be):                                                │    │
│  │  ┌────────────────────────────────────────────────────────────┐     │    │
│  │  │                                                             │     │    │
│  │  │  Time ──────────────────────────────────────────────────>   │     │    │
│  │  │                                                             │     │    │
│  │  │  ┌─────────────────────────────────────────────────────┐   │     │    │
│  │  │  │ Client A │ Client B │ Client C │ Client D │ Client E│   │     │    │
│  │  │  │  (RU1)   │  (RU2)   │  (RU3)   │  (RU4)   │  (RU5)  │   │     │    │
│  │  │  └─────────────────────────────────────────────────────┘   │     │    │
│  │  │  ┌─────────────────────────────────────────────────────┐   │     │    │
│  │  │  │ Client A │ Client F │ Client G │ Client H │ Client B│   │     │    │
│  │  │  │  (RU1)   │  (RU2)   │  (RU3)   │  (RU4)   │  (RU5)  │   │     │    │
│  │  │  └─────────────────────────────────────────────────────┘   │     │    │
│  │  │                                                             │     │    │
│  │  │  Multiple clients simultaneously on different RUs           │     │    │
│  │  │                                                             │     │    │
│  │  └────────────────────────────────────────────────────────────┘     │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  Resource Unit (RU) Sizes:                                                   │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  ┌────────────────────────────────────────────────────────────┐     │    │
│  │  │ RU Size     Subcarriers    Bandwidth    Max in 20 MHz     │     │    │
│  │  │ ───────     ───────────    ─────────    ─────────────     │     │    │
│  │  │ 26-tone     26             2 MHz        9                 │     │    │
│  │  │ 52-tone     52             4 MHz        4                 │     │    │
│  │  │ 106-tone    106            8 MHz        2                 │     │    │
│  │  │ 242-tone    242            20 MHz       1                 │     │    │
│  │  │ 484-tone    484            40 MHz       1 (in 40 MHz)     │     │    │
│  │  │ 996-tone    996            80 MHz       1 (in 80 MHz)     │     │    │
│  │  │ 2x996-tone  1992           160 MHz      1 (in 160 MHz)    │     │    │
│  │  └────────────────────────────────────────────────────────────┘     │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### CB.2 Trigger Frames

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    TRIGGER FRAMES                                            │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  Trigger Frame Purpose:                                                      │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  - Coordinates uplink OFDMA transmissions                            │    │
│  │  - Assigns RUs to specific clients                                   │    │
│  │  - Specifies MCS, coding, and power                                  │    │
│  │  - Enables simultaneous uplink from multiple clients                 │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  Trigger Frame Types:                                                        │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  ┌────────────────────────────────────────────────────────────┐     │    │
│  │  │ Type                    Purpose                            │     │    │
│  │  │ ────                    ───────                            │     │    │
│  │  │ Basic                   Standard UL OFDMA                  │     │    │
│  │  │ BFRP                    Beamforming Report Poll            │     │    │
│  │  │ MU-BAR                  Multi-User Block Ack Request       │     │    │
│  │  │ MU-RTS                  Multi-User RTS                     │     │    │
│  │  │ BSRP                    Buffer Status Report Poll          │     │    │
│  │  │ GCR MU-BAR              Groupcast with Retries MU-BAR      │     │    │
│  │  │ BQRP                    Bandwidth Query Report Poll        │     │    │
│  │  │ NFRP                    NDP Feedback Report Poll           │     │    │
│  │  └────────────────────────────────────────────────────────────┘     │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  UL OFDMA Sequence:                                                          │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  AP                Client A        Client B        Client C          │    │
│  │   │                   │               │               │              │    │
│  │   │ ── Trigger ───────────────────────────────────────>│             │    │
│  │   │    (RU1=A, RU2=B, RU3=C)                           │             │    │
│  │   │                   │               │               │              │    │
│  │   │ <── Data (RU1) ───│               │               │              │    │
│  │   │ <── Data (RU2) ───────────────────│               │              │    │
│  │   │ <── Data (RU3) ───────────────────────────────────│              │    │
│  │   │    (Simultaneous)                                 │              │    │
│  │   │                   │               │               │              │    │
│  │   │ ── Multi-STA BA ──────────────────────────────────>│             │    │
│  │   │                   │               │               │              │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Appendix CC: MU-MIMO Deep Dive

### CC.1 MU-MIMO Fundamentals

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    MU-MIMO FUNDAMENTALS                                      │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  SU-MIMO vs MU-MIMO:                                                         │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  SU-MIMO (Single User):                                              │    │
│  │  ┌────────────────────────────────────────────────────────────┐     │    │
│  │  │                                                             │     │    │
│  │  │       AP (4x4)                                              │     │    │
│  │  │         │                                                   │     │    │
│  │  │         │ ═══════════════════════════> Client A (2x2)       │     │    │
│  │  │         │    4 spatial streams                              │     │    │
│  │  │         │    to one client                                  │     │    │
│  │  │                                                             │     │    │
│  │  └────────────────────────────────────────────────────────────┘     │    │
│  │                                                                      │    │
│  │  MU-MIMO (Multi User):                                               │    │
│  │  ┌────────────────────────────────────────────────────────────┐     │    │
│  │  │                                                             │     │    │
│  │  │       AP (4x4)                                              │     │    │
│  │  │         │                                                   │     │    │
│  │  │         ├──────────────────────────> Client A (1x1)         │     │    │
│  │  │         ├──────────────────────────> Client B (1x1)         │     │    │
│  │  │         ├──────────────────────────> Client C (1x1)         │     │    │
│  │  │         └──────────────────────────> Client D (1x1)         │     │    │
│  │  │            4 clients simultaneously                         │     │    │
│  │  │                                                             │     │    │
│  │  └────────────────────────────────────────────────────────────┘     │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  MU-MIMO Evolution:                                                          │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  ┌────────────────────────────────────────────────────────────┐     │    │
│  │  │ Standard      Direction    Max Users    Max Streams        │     │    │
│  │  │ ────────      ─────────    ─────────    ───────────        │     │    │
│  │  │ 802.11ac      DL only      4            8                  │     │    │
