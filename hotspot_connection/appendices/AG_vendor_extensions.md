## Appendix AG: Vendor-Specific Extensions

### AG.1 Microsoft Vendor Extensions

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    MICROSOFT VENDOR EXTENSIONS                               │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  Microsoft OUI: 00-50-F2                                                     │
│                                                                              │
│  WPA Information Element (Legacy):                                           │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │  Element ID: 221 (Vendor Specific)                                  │    │
│  │  OUI: 00-50-F2                                                      │    │
│  │  OUI Type: 1 (WPA)                                                  │    │
│  │                                                                      │    │
│  │  Format:                                                             │    │
│  │  ┌────────────────────────────────────────────────────────────┐     │    │
│  │  │ ID │ Len │ OUI     │ Type │ Version │ Group │ Pairwise │ AKM │     │    │
│  │  │ 221│ var │00-50-F2 │  1   │    1    │ Suite │  Suites  │Suite│     │    │
│  │  └────────────────────────────────────────────────────────────┘     │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  WMM/WME Information Element:                                                │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │  Element ID: 221 (Vendor Specific)                                  │    │
│  │  OUI: 00-50-F2                                                      │    │
│  │  OUI Type: 2 (WMM/WME)                                              │    │
│  │  OUI Subtype: 0 (Information), 1 (Parameter)                        │    │
│  │                                                                      │    │
│  │  WMM Parameter Element:                                              │    │
│  │  ┌────────────────────────────────────────────────────────────┐     │    │
│  │  │ Field              Size    Description                     │     │    │
│  │  │ ─────              ────    ───────────                     │     │    │
│  │  │ QoS Info           1       U-APSD, parameter set count     │     │    │
│  │  │ Reserved           1       Reserved                        │     │    │
│  │  │ AC_BE Parameters   4       Best Effort parameters          │     │    │
│  │  │ AC_BK Parameters   4       Background parameters           │     │    │
│  │  │ AC_VI Parameters   4       Video parameters                │     │    │
│  │  │ AC_VO Parameters   4       Voice parameters                │     │    │
│  │  └────────────────────────────────────────────────────────────┘     │    │
│  │                                                                      │    │
│  │  AC Parameter Record:                                                │    │
│  │  ┌────────────────────────────────────────────────────────────┐     │    │
│  │  │ Bits   Field       Description                             │     │    │
│  │  │ ────   ─────       ───────────                             │     │    │
│  │  │ 0-3    AIFSN       Arbitration Interframe Space Number     │     │    │
│  │  │ 4      ACM         Admission Control Mandatory             │     │    │
│  │  │ 5-6    ACI         Access Category Index                   │     │    │
│  │  │ 7      Reserved                                            │     │    │
│  │  │ 8-11   ECWmin      Exponent for CWmin                      │     │    │
│  │  │ 12-15  ECWmax      Exponent for CWmax                      │     │    │
│  │  │ 16-31  TXOP Limit  Transmit Opportunity Limit              │     │    │
│  │  └────────────────────────────────────────────────────────────┘     │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  Microsoft RADIUS Attributes:                                                │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │  Vendor ID: 311 (Microsoft)                                         │    │
│  │                                                                      │    │
│  │  Attribute   Name                    Description                    │    │
│  │  ─────────   ────                    ───────────                    │    │
│  │     10       MS-CHAP-Response        MS-CHAP response               │    │
│  │     11       MS-CHAP-Error           MS-CHAP error message          │    │
│  │     16       MS-MPPE-Send-Key        MPPE send key                  │    │
│  │     17       MS-MPPE-Recv-Key        MPPE receive key               │    │
│  │     25       MS-CHAP2-Response       MS-CHAPv2 response             │    │
│  │     26       MS-CHAP2-Success        MS-CHAPv2 success              │    │
│  │     27       MS-CHAP2-CPW            MS-CHAPv2 change password      │    │
│  │                                                                      │    │
│  │  MPPE Key Format (for PMK derivation):                              │    │
│  │  ┌────────────────────────────────────────────────────────────┐     │    │
│  │  │ Byte 0: Salt (high byte)                                   │     │    │
│  │  │ Byte 1: Salt (low byte)                                    │     │    │
│  │  │ Byte 2: Key Length                                         │     │    │
│  │  │ Bytes 3-34: Encrypted Key (32 bytes for PMK)               │     │    │
│  │  │ Remaining: Padding                                         │     │    │
│  │  └────────────────────────────────────────────────────────────┘     │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### AG.2 Cisco Vendor Extensions

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    CISCO VENDOR EXTENSIONS                                   │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  Cisco OUI: 00-40-96                                                         │
│                                                                              │
│  Cisco Compatible Extensions (CCX):                                          │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  CCX Version History:                                                │    │
│  │  • CCXv1: Basic compatibility                                       │    │
│  │  • CCXv2: LEAP, CCKM, AP-assisted roaming                           │    │
│  │  • CCXv3: Voice metrics, location services                          │    │
│  │  • CCXv4: Management Frame Protection, diagnostics                  │    │
│  │  • CCXv5: Video metrics, enhanced location                          │    │
│  │                                                                      │    │
│  │  CCKM (Cisco Centralized Key Management):                           │    │
│  │  ┌────────────────────────────────────────────────────────────┐     │    │
│  │  │ • Fast roaming without full 802.1X                         │     │    │
│  │  │ • Key cached at WLC                                        │     │    │
│  │  │ • Roam time: ~50ms                                         │     │    │
│  │  │ • Predecessor to 802.11r                                   │     │    │
│  │  └────────────────────────────────────────────────────────────┘     │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  Cisco RADIUS Attributes:                                                    │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │  Vendor ID: 9 (Cisco)                                               │    │
│  │                                                                      │    │
│  │  Attribute   Name                    Description                    │    │
│  │  ─────────   ────                    ───────────                    │    │
│  │     1        Cisco-AV-Pair          Attribute-value pair           │    │
│  │     2        Cisco-NAS-Port         NAS port info                  │    │
│  │     5        Cisco-Command          Command authorization          │    │
│  │    23        Cisco-Account-Info     Accounting info                │    │
│  │    24        Cisco-Service-Info     Service info                   │    │
│  │    25        Cisco-Command-Code     Command code                   │    │
│  │    26        Cisco-Control-Protocols Control protocols             │    │
│  │   252        Cisco-Data-Rate        Data rate limit                │    │
│  │   253        Cisco-PreAuth-Context  Pre-auth context               │    │
│  │   254        Cisco-Audit-Session-Id Audit session ID               │    │
│  │   255        Cisco-Disconnect-Cause Disconnect cause               │    │
│  │                                                                      │    │
│  │  Common AV-Pairs:                                                   │    │
│  │  ┌────────────────────────────────────────────────────────────┐     │    │
│  │  │ url-redirect=http://...        Captive portal redirect     │     │    │
│  │  │ url-redirect-acl=ACL_NAME      ACL for redirect            │     │    │
│  │  │ subscriber:command=...         Subscriber command          │     │    │
│  │  │ audit-session-id=...           Session tracking            │     │    │
│  │  │ ip:inacl#1=...                 Downloadable ACL            │     │    │
│  │  │ ip:outacl#1=...                Outbound ACL                │     │    │
│  │  └────────────────────────────────────────────────────────────┘     │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### AG.3 Wi-Fi Alliance Vendor Extensions

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    WI-FI ALLIANCE VENDOR EXTENSIONS                          │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  Wi-Fi Alliance OUI: 50-6F-9A                                                │
│                                                                              │
│  P2P (Wi-Fi Direct):                                                         │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │  OUI Type: 9                                                        │    │
│  │                                                                      │    │
│  │  P2P Attributes:                                                     │    │
│  │  ┌────────────────────────────────────────────────────────────┐     │    │
│  │  │ ID    Name                    Description                  │     │    │
│  │  │ ──    ────                    ───────────                  │     │    │
│  │  │  0    Status                  Operation status             │     │    │
│  │  │  1    Minor Reason Code       Detailed reason              │     │    │
│  │  │  2    P2P Capability          Device/group capabilities    │     │    │
│  │  │  3    P2P Device ID           Device MAC address           │     │    │
│  │  │  4    Group Owner Intent      GO negotiation intent        │     │    │
│  │  │  5    Configuration Timeout   Config timeout values        │     │    │
│  │  │  6    Listen Channel          Listen channel               │     │    │
│  │  │  7    P2P Group BSSID         Group BSSID                  │     │    │
│  │  │  8    Extended Listen Timing  Extended listen timing       │     │    │
│  │  │  9    Intended P2P Interface  Intended interface address   │     │    │
│  │  │ 10    P2P Manageability       Manageability info           │     │    │
│  │  │ 11    Channel List            Supported channels           │     │    │
│  │  │ 12    Notice of Absence       NoA schedule                 │     │    │
│  │  │ 13    P2P Device Info         Device information           │     │    │
│  │  │ 14    P2P Group Info          Group member info            │     │    │
│  │  │ 15    P2P Group ID            Group identifier             │     │    │
│  │  │ 16    P2P Interface           Interface address list       │     │    │
│  │  │ 17    Operating Channel       Operating channel            │     │    │
│  │  │ 18    Invitation Flags        Invitation flags             │     │    │
│  │  └────────────────────────────────────────────────────────────┘     │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  Hotspot 2.0 (HS2.0):                                                        │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │  OUI Type: 16                                                       │    │
│  │                                                                      │    │
│  │  HS2.0 Indication Element:                                          │    │
│  │  ┌────────────────────────────────────────────────────────────┐     │    │
│  │  │ Field                Size    Description                   │     │    │
│  │  │ ─────                ────    ───────────                   │     │    │
│  │  │ HS2.0 Indication     1       Capability flags              │     │    │
│  │  │ PPS MO ID            2       Policy/subscription ID        │     │    │
│  │  │ ANQP Domain ID       2       ANQP domain identifier        │     │    │
│  │  └────────────────────────────────────────────────────────────┘     │    │
│  │                                                                      │    │
│  │  HS2.0 Indication Bits:                                              │    │
│  │  ┌────────────────────────────────────────────────────────────┐     │    │
│  │  │ Bit   Name                    Description                  │     │    │
│  │  │ ───   ────                    ───────────                  │     │    │
│  │  │ 0     DGAF Disabled           Downstream Group-Addressed   │     │    │
│  │  │ 1-4   HS2.0 Version           Version number (0-3)         │     │    │
│  │  │ 5     ANQP Domain ID Present  ANQP Domain ID included      │     │    │
│  │  │ 6     Reserved                                             │     │    │
│  │  │ 7     OSU Providers Present   OSU providers available      │     │    │
│  │  └────────────────────────────────────────────────────────────┘     │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  MBO (Multi-Band Operation):                                                 │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │  OUI Type: 22                                                       │    │
│  │                                                                      │    │
│  │  MBO Attributes:                                                     │    │
│  │  ┌────────────────────────────────────────────────────────────┐     │    │
│  │  │ ID    Name                    Description                  │     │    │
│  │  │ ──    ────                    ───────────                  │     │    │
│  │  │  1    MBO AP Capability       AP MBO capabilities          │     │    │
│  │  │  2    Non-preferred Channels  Client channel preferences   │     │    │
│  │  │  3    Cellular Data Cap       Cellular data capability     │     │    │
│  │  │  4    Association Disallowed  Association not allowed      │     │    │
│  │  │  5    Cellular Data Pref      Cellular data preference     │     │    │
│  │  │  6    Transition Reason       BSS transition reason        │     │    │
│  │  │  7    Transition Reject Reason Reject reason               │     │    │
│  │  │  8    Assoc Retry Delay       Retry delay                  │     │    │
│  │  └────────────────────────────────────────────────────────────┘     │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  DPP (Device Provisioning Protocol):                                         │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │  OUI Type: 26                                                       │    │
│  │                                                                      │    │
│  │  DPP is used for Easy Connect (QR code provisioning)                │    │
│  │                                                                      │    │
│  │  DPP Frame Types:                                                    │    │
│  │  ┌────────────────────────────────────────────────────────────┐     │    │
│  │  │ Type   Name                    Description                 │     │    │
│  │  │ ────   ────                    ───────────                 │     │    │
│  │  │  0     Authentication Request  Start DPP auth              │     │    │
│  │  │  1     Authentication Response Response to auth            │     │    │
│  │  │  2     Authentication Confirm  Confirm authentication      │     │    │
│  │  │  3     Peer Discovery Request  Discover peer               │     │    │
│  │  │  4     Peer Discovery Response Response to discovery       │     │    │
│  │  │  5     PKEX Exchange Request   PKEX key exchange           │     │    │
│  │  │  6     PKEX Exchange Response  PKEX response               │     │    │
│  │  │  7     PKEX Commit-Reveal Req  PKEX commit                 │     │    │
│  │  │  8     PKEX Commit-Reveal Resp PKEX reveal                 │     │    │
│  │  │  9     Configuration Request   Request configuration       │     │    │
│  │  │ 10     Configuration Response  Provide configuration       │     │    │
│  │  │ 11     Configuration Result    Configuration result        │     │    │
│  │  │ 12     Connection Status       Connection status           │     │    │
│  │  │ 13     Presence Announcement   Announce presence           │     │    │
│  │  │ 14     Reconfig Announcement   Reconfiguration announce    │     │    │
│  │  │ 15     Reconfig Auth Request   Reconfig auth request       │     │    │
│  │  │ 16     Reconfig Auth Response  Reconfig auth response      │     │    │
│  │  │ 17     Reconfig Auth Confirm   Reconfig auth confirm       │     │    │
│  │  └────────────────────────────────────────────────────────────┘     │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

