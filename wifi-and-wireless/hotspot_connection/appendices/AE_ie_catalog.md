## Appendix AE: Information Element Catalog

### AE.1 Common Information Elements

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    INFORMATION ELEMENTS CATALOG                              │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  Standard Information Elements:                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │  ID    Name                        Max Len   Description            │    │
│  │  ──    ────                        ───────   ───────────            │    │
│  │   0    SSID                        32        Network name           │    │
│  │   1    Supported Rates             8         Basic/supported rates  │    │
│  │   2    FH Parameter Set            5         Frequency hopping      │    │
│  │   3    DS Parameter Set            1         Channel number         │    │
│  │   4    CF Parameter Set            6         Contention-free params │    │
│  │   5    TIM                         254       Traffic indication map │    │
│  │   6    IBSS Parameter Set          2         Ad-hoc parameters      │    │
│  │   7    Country                     254       Regulatory domain      │    │
│  │  10    Request                     255       Request IEs            │    │
│  │  11    BSS Load                    5         Channel utilization    │    │
│  │  12    EDCA Parameter Set          18        QoS parameters         │    │
│  │  13    TSPEC                       55        Traffic specification  │    │
│  │  14    TCLAS                       255       Traffic classification │    │
│  │  16    Challenge Text              253       Auth challenge         │    │
│  │  32    Power Constraint            1         Local power limit      │    │
│  │  33    Power Capability            2         Min/max TX power       │    │
│  │  34    TPC Request                 0         Request TPC report     │    │
│  │  35    TPC Report                  2         TX power and margin    │    │
│  │  36    Supported Channels          254       Supported channels     │    │
│  │  37    Channel Switch Announce     3         CSA parameters         │    │
│  │  38    Measurement Request         255       RRM request            │    │
│  │  39    Measurement Report          255       RRM report             │    │
│  │  40    Quiet                       6         Quiet period           │    │
│  │  41    IBSS DFS                    255       Ad-hoc DFS             │    │
│  │  42    ERP Information             1         802.11g protection     │    │
│  │  45    HT Capabilities             26        802.11n capabilities   │    │
│  │  46    QoS Capability              1         QoS support            │    │
│  │  48    RSN                         255       Security parameters    │    │
│  │  50    Extended Supported Rates    255       Additional rates       │    │
│  │  54    Mobility Domain             3         802.11r domain         │    │
│  │  55    Fast BSS Transition         255       802.11r FT info        │    │
│  │  56    Timeout Interval            5         Reassoc deadline       │    │
│  │  57    RIC Data                    255       Resource request       │    │
│  │  59    Supported Operating Classes 255       Regulatory classes     │    │
│  │  61    HT Operation                22        802.11n operation      │    │
│  │  62    Secondary Channel Offset    1         40 MHz offset          │    │
│  │  70    RM Enabled Capabilities     5         802.11k capabilities   │    │
│  │  72    20/40 BSS Coexistence       1         Coexistence info       │    │
│  │  74    Overlapping BSS Scan Params 14        OBSS scan params       │    │
│  │ 107    Interworking                7-9       Hotspot 2.0            │    │
│  │ 108    Advertisement Protocol      255       GAS advertisement      │    │
│  │ 111    Roaming Consortium          255       Roaming partners       │    │
│  │ 127    Extended Capabilities       15        Extended caps          │    │
│  │ 191    VHT Capabilities            12        802.11ac capabilities  │    │
│  │ 192    VHT Operation               5         802.11ac operation     │    │
│  │ 195    VHT TX Power Envelope       2-5       TX power limits        │    │
│  │ 199    Operating Mode Notification 1         Op mode change         │    │
│  │ 221    Vendor Specific             255       Vendor extensions      │    │
│  │ 255    Extension                   255       Extended IEs           │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  Extension IEs (ID=255):                                                     │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │  Ext ID  Name                      Description                      │    │
│  │  ──────  ────                      ───────────                      │    │
│  │    1     Association Delay Info    Association delay                │    │
│  │    2     FILS Request Parameters   FILS parameters                  │    │
│  │    3     FILS Key Confirmation     FILS key confirm                 │    │
│  │    4     FILS Session              FILS session                     │    │
│  │    5     FILS HLP Container        FILS HLP                         │    │
│  │    6     FILS IP Address Assign    FILS IP assignment               │    │
│  │    7     Key Delivery              Key delivery                     │    │
│  │    8     FILS Wrapped Data         FILS wrapped data                │    │
│  │    9     FILS Public Key           FILS public key                  │    │
│  │   10     FILS Nonce                FILS nonce                       │    │
│  │   11     Future Channel Guidance   Future channel                   │    │
│  │   32     OWE DH Parameter          OWE Diffie-Hellman               │    │
│  │   35     HE Capabilities           802.11ax capabilities            │    │
│  │   36     HE Operation              802.11ax operation               │    │
│  │   37     UORA Parameter Set        Uplink OFDMA                     │    │
│  │   38     MU EDCA Parameter Set     MU EDCA                          │    │
│  │   39     Spatial Reuse Parameter   Spatial reuse                    │    │
│  │   40     NDP Feedback Report       NDP feedback                     │    │
│  │   41     BSS Color Change Announce BSS color change                 │    │
│  │   42     Quiet Time Period         Quiet time                       │    │
│  │   43     ESS Report                ESS report                       │    │
│  │  106     Multi-Link                802.11be MLO                     │    │
│  │  107     EHT Capabilities          802.11be capabilities            │    │
│  │  108     EHT Operation             802.11be operation               │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### AE.2 RSN Information Element

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    RSN INFORMATION ELEMENT STRUCTURE                         │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  RSN IE Format:                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  ┌──────────────────────────────────────────────────────────────┐   │    │
│  │  │ Field                    Size        Description             │   │    │
│  │  │ ─────                    ────        ───────────             │   │    │
│  │  │ Element ID               1 byte      48 (0x30)               │   │    │
│  │  │ Length                   1 byte      Variable                │   │    │
│  │  │ Version                  2 bytes     1                       │   │    │
│  │  │ Group Cipher Suite       4 bytes     Multicast cipher        │   │    │
│  │  │ Pairwise Cipher Count    2 bytes     Number of ciphers       │   │    │
│  │  │ Pairwise Cipher Suites   4*n bytes   Unicast ciphers         │   │    │
│  │  │ AKM Suite Count          2 bytes     Number of AKMs          │   │    │
│  │  │ AKM Suites               4*m bytes   Auth methods            │   │    │
│  │  │ RSN Capabilities         2 bytes     Capability flags        │   │    │
│  │  │ PMKID Count              2 bytes     Number of PMKIDs        │   │    │
│  │  │ PMKID List               16*p bytes  PMKID values            │   │    │
│  │  │ Group Mgmt Cipher Suite  4 bytes     MFP cipher (optional)   │   │    │
│  │  └──────────────────────────────────────────────────────────────┘   │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  Cipher Suite Selectors (OUI + Suite Type):                                  │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │  OUI          Suite   Name                                          │    │
│  │  ───          ─────   ────                                          │    │
│  │  00-0F-AC     0       Use group cipher                              │    │
│  │  00-0F-AC     1       WEP-40                                        │    │
│  │  00-0F-AC     2       TKIP                                          │    │
│  │  00-0F-AC     3       Reserved                                      │    │
│  │  00-0F-AC     4       CCMP-128                                      │    │
│  │  00-0F-AC     5       WEP-104                                       │    │
│  │  00-0F-AC     6       BIP-CMAC-128                                  │    │
│  │  00-0F-AC     7       Group addressed traffic not allowed           │    │
│  │  00-0F-AC     8       GCMP-128                                      │    │
│  │  00-0F-AC     9       GCMP-256                                      │    │
│  │  00-0F-AC     10      CCMP-256                                      │    │
│  │  00-0F-AC     11      BIP-GMAC-128                                  │    │
│  │  00-0F-AC     12      BIP-GMAC-256                                  │    │
│  │  00-0F-AC     13      BIP-CMAC-256                                  │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  AKM Suite Selectors:                                                        │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │  OUI          Suite   Name                                          │    │
│  │  ───          ─────   ────                                          │    │
│  │  00-0F-AC     1       802.1X (EAP)                                  │    │
│  │  00-0F-AC     2       PSK                                           │    │
│  │  00-0F-AC     3       FT over 802.1X                                │    │
│  │  00-0F-AC     4       FT over PSK                                   │    │
│  │  00-0F-AC     5       802.1X with SHA-256                           │    │
│  │  00-0F-AC     6       PSK with SHA-256                              │    │
│  │  00-0F-AC     7       TDLS                                          │    │
│  │  00-0F-AC     8       SAE                                           │    │
│  │  00-0F-AC     9       FT over SAE                                   │    │
│  │  00-0F-AC     10      AP Peer Key                                   │    │
│  │  00-0F-AC     11      802.1X Suite B                                │    │
│  │  00-0F-AC     12      802.1X Suite B 192-bit                        │    │
│  │  00-0F-AC     13      FT over 802.1X SHA-384                        │    │
│  │  00-0F-AC     14      FILS SHA-256                                  │    │
│  │  00-0F-AC     15      FILS SHA-384                                  │    │
│  │  00-0F-AC     16      FT over FILS SHA-256                          │    │
│  │  00-0F-AC     17      FT over FILS SHA-384                          │    │
│  │  00-0F-AC     18      OWE                                           │    │
│  │  00-0F-AC     19      FT over PSK SHA-384                           │    │
│  │  00-0F-AC     20      PSK SHA-384                                   │    │
│  │  00-0F-AC     21      PASN                                          │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  RSN Capabilities:                                                           │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │  Bit    Name                    Description                         │    │
│  │  ───    ────                    ───────────                         │    │
│  │  0      Pre-Auth                Pre-authentication supported        │    │
│  │  1      No Pairwise             No pairwise key needed              │    │
│  │  2-3    PTKSA Replay Counter    PTK replay counter size             │    │
│  │  4-5    GTKSA Replay Counter    GTK replay counter size             │    │
│  │  6      MFP Required            802.11w required                    │    │
│  │  7      MFP Capable             802.11w capable                     │    │
│  │  8      Joint Multi-band RSNA   Multi-band support                  │    │
│  │  9      PeerKey Enabled         PeerKey supported                   │    │
│  │  10     SPP A-MSDU Capable      SPP A-MSDU support                  │    │
│  │  11     SPP A-MSDU Required     SPP A-MSDU required                 │    │
│  │  12     PBAC                    Protected Block Ack                 │    │
│  │  13     Extended Key ID         Extended Key ID support             │    │
│  │  14     OCVC                    Operating Channel Validation        │    │
│  │  15     Reserved                                                    │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

