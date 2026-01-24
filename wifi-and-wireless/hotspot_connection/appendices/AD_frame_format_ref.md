## Appendix AD: Frame Format Reference

### AD.1 802.11 MAC Header

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    802.11 MAC HEADER FORMAT                                  │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  General MAC Header (24-30 bytes):                                           │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │ Bytes:  2      2       6        6        6       2       6     0-2  │    │
│  │       ┌────┬──────┬────────┬────────┬────────┬──────┬────────┬────┐│    │
│  │       │Frm │Dur/  │Address │Address │Address │Seq   │Address │QoS ││    │
│  │       │Ctrl│ID    │   1    │   2    │   3    │Ctrl  │   4    │Ctrl││    │
│  │       └────┴──────┴────────┴────────┴────────┴──────┴────────┴────┘│    │
│  │                                                                      │    │
│  │  Address fields depend on To DS and From DS bits:                   │    │
│  │  ┌──────────────────────────────────────────────────────────────┐   │    │
│  │  │ To DS │ From DS │ Addr1  │ Addr2  │ Addr3  │ Addr4           │   │    │
│  │  │───────│─────────│────────│────────│────────│─────────────────│   │    │
│  │  │   0   │    0    │   DA   │   SA   │  BSSID │   N/A           │   │    │
│  │  │   0   │    1    │   DA   │  BSSID │   SA   │   N/A           │   │    │
│  │  │   1   │    0    │  BSSID │   SA   │   DA   │   N/A           │   │    │
│  │  │   1   │    1    │   RA   │   TA   │   DA   │   SA (WDS)      │   │    │
│  │  └──────────────────────────────────────────────────────────────┘   │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  Frame Control Field (2 bytes):                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │ Bits: 2      2      4       1    1    1    1    1    1    1    1   │    │
│  │      ┌────┬──────┬──────┬────┬────┬────┬────┬────┬────┬────┬────┐  │    │
│  │      │Prot│ Type │Subtyp│ToDS│FrDS│More│Rtry│Pwr │More│Prot│Ordr│  │    │
│  │      │Ver │      │      │    │    │Frag│    │Mgmt│Data│Frm │    │  │    │
│  │      └────┴──────┴──────┴────┴────┴────┴────┴────┴────┴────┴────┘  │    │
│  │                                                                      │    │
│  │  Protocol Version: 0 (current)                                      │    │
│  │  Type: 00=Management, 01=Control, 10=Data                           │    │
│  │  Subtype: Specific frame type                                       │    │
│  │  To DS: Frame going to Distribution System                          │    │
│  │  From DS: Frame coming from Distribution System                     │    │
│  │  More Fragments: More fragments follow                              │    │
│  │  Retry: Frame is a retransmission                                   │    │
│  │  Power Management: STA in power save mode                           │    │
│  │  More Data: More frames buffered for STA                            │    │
│  │  Protected Frame: Frame body is encrypted                           │    │
│  │  Order: Strict ordering required                                    │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### AD.2 Frame Types and Subtypes

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    FRAME TYPES AND SUBTYPES                                  │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  Management Frames (Type = 00):                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │  Subtype   Name                    Description                      │    │
│  │  ───────   ────                    ───────────                      │    │
│  │  0000      Association Request     Client requests association      │    │
│  │  0001      Association Response    AP responds to association       │    │
│  │  0010      Reassociation Request   Client requests reassociation    │    │
│  │  0011      Reassociation Response  AP responds to reassociation     │    │
│  │  0100      Probe Request           Client scans for networks        │    │
│  │  0101      Probe Response          AP responds to probe             │    │
│  │  0110      Timing Advertisement    Time synchronization             │    │
│  │  0111      Reserved                                                 │    │
│  │  1000      Beacon                  AP announces presence            │    │
│  │  1001      ATIM                    Ad-hoc traffic indication        │    │
│  │  1010      Disassociation          End association                  │    │
│  │  1011      Authentication          Authentication exchange          │    │
│  │  1100      Deauthentication        End authentication               │    │
│  │  1101      Action                  Various actions (11k/v/r)        │    │
│  │  1110      Action No Ack           Action without acknowledgment    │    │
│  │  1111      Reserved                                                 │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  Control Frames (Type = 01):                                                 │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │  Subtype   Name                    Description                      │    │
│  │  ───────   ────                    ───────────                      │    │
│  │  0000-0110 Reserved                                                 │    │
│  │  0111      Control Wrapper         Carries control frame            │    │
│  │  1000      Block Ack Request       Request block acknowledgment     │    │
│  │  1001      Block Ack               Block acknowledgment             │    │
│  │  1010      PS-Poll                 Power save poll                  │    │
│  │  1011      RTS                     Request to Send                  │    │
│  │  1100      CTS                     Clear to Send                    │    │
│  │  1101      ACK                     Acknowledgment                   │    │
│  │  1110      CF-End                  Contention-free period end       │    │
│  │  1111      CF-End + CF-Ack         CF end with acknowledgment       │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  Data Frames (Type = 10):                                                    │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │  Subtype   Name                    Description                      │    │
│  │  ───────   ────                    ───────────                      │    │
│  │  0000      Data                    Simple data frame                │    │
│  │  0001      Data + CF-Ack           Data with CF acknowledgment      │    │
│  │  0010      Data + CF-Poll          Data with CF poll                │    │
│  │  0011      Data + CF-Ack + CF-Poll Data with both                   │    │
│  │  0100      Null (no data)          No data, just header             │    │
│  │  0101      CF-Ack (no data)        CF ack, no data                  │    │
│  │  0110      CF-Poll (no data)       CF poll, no data                 │    │
│  │  0111      CF-Ack + CF-Poll        Both, no data                    │    │
│  │  1000      QoS Data                QoS data frame                   │    │
│  │  1001      QoS Data + CF-Ack       QoS data with CF ack             │    │
│  │  1010      QoS Data + CF-Poll      QoS data with CF poll            │    │
│  │  1011      QoS Data + CF-Ack+Poll  QoS data with both               │    │
│  │  1100      QoS Null                QoS null frame                   │    │
│  │  1101      Reserved                                                 │    │
│  │  1110      QoS CF-Poll (no data)   QoS CF poll                      │    │
│  │  1111      QoS CF-Ack+Poll         QoS CF ack and poll              │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### AD.3 EAPOL Frame Format

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    EAPOL FRAME FORMAT                                        │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  EAPOL Header:                                                               │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │ Bytes:    1          1           2            Variable              │    │
│  │         ┌────────┬──────────┬──────────┬─────────────────────────┐  │    │
│  │         │Protocol│  Packet  │  Packet  │      Packet Body        │  │    │
│  │         │Version │   Type   │  Length  │                         │  │    │
│  │         └────────┴──────────┴──────────┴─────────────────────────┘  │    │
│  │                                                                      │    │
│  │  Protocol Version: 1 (802.1X-2001), 2 (802.1X-2004), 3 (802.1X-2010)│    │
│  │                                                                      │    │
│  │  Packet Types:                                                       │    │
│  │  ┌─────────────────────────────────────────────────────────────┐    │    │
│  │  │  Type   Name                Description                     │    │    │
│  │  │  ────   ────                ───────────                     │    │    │
│  │  │   0     EAP-Packet          EAP frame                       │    │    │
│  │  │   1     EAPOL-Start         Client initiates authentication │    │    │
│  │  │   2     EAPOL-Logoff        Client ends session             │    │    │
│  │  │   3     EAPOL-Key           Key exchange (4-way handshake)  │    │    │
│  │  │   4     EAPOL-Encapsulated  Encapsulated ASF alert          │    │    │
│  │  │   5     EAPOL-MKA           MACsec Key Agreement            │    │    │
│  │  │   6     EAPOL-Announcement  Generic announcement            │    │    │
│  │  │   7     EAPOL-Announcement-Req  Announcement request        │    │    │
│  │  └─────────────────────────────────────────────────────────────┘    │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  EAPOL-Key Frame (for 4-Way Handshake):                                      │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  ┌──────────────────────────────────────────────────────────────┐   │    │
│  │  │ Field              Size      Description                     │   │    │
│  │  │ ─────              ────      ───────────                     │   │    │
│  │  │ Descriptor Type    1 byte    2=RSN, 254=WPA                  │   │    │
│  │  │ Key Information    2 bytes   Key type, install, ack, etc.   │   │    │
│  │  │ Key Length         2 bytes   Length of PTK (16 or 32)       │   │    │
│  │  │ Key Replay Counter 8 bytes   Replay protection              │   │    │
│  │  │ Key Nonce          32 bytes  ANonce or SNonce               │   │    │
│  │  │ Key IV             16 bytes  Initialization vector          │   │    │
│  │  │ Key RSC            8 bytes   Receive sequence counter       │   │    │
│  │  │ Reserved           8 bytes   Reserved                       │   │    │
│  │  │ Key MIC            16 bytes  Message integrity code         │   │    │
│  │  │ Key Data Length    2 bytes   Length of key data             │   │    │
│  │  │ Key Data           Variable  RSN IE, GTK, etc.              │   │    │
│  │  └──────────────────────────────────────────────────────────────┘   │    │
│  │                                                                      │    │
│  │  Key Information Bits:                                               │    │
│  │  ┌──────────────────────────────────────────────────────────────┐   │    │
│  │  │ Bit    Name              Description                         │   │    │
│  │  │ ───    ────              ───────────                         │   │    │
│  │  │ 0-2    Key Descriptor    Version (1=HMAC-MD5, 2=HMAC-SHA1)  │   │    │
│  │  │ 3      Key Type          0=Group, 1=Pairwise                │   │    │
│  │  │ 4-5    Reserved                                              │   │    │
│  │  │ 6      Install           Install PTK after verifying MIC    │   │    │
│  │  │ 7      Key Ack           Sender expects response            │   │    │
│  │  │ 8      Key MIC           MIC is present                     │   │    │
│  │  │ 9      Secure            Pairwise keys installed            │   │    │
│  │  │ 10     Error             Error occurred                     │   │    │
│  │  │ 11     Request           STA requests new key               │   │    │
│  │  │ 12     Encrypted Key     Key Data is encrypted              │   │    │
│  │  │ 13     SMK Message       SMK handshake message              │   │    │
│  │  │ 14-15  Reserved                                              │   │    │
│  │  └──────────────────────────────────────────────────────────────┘   │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

