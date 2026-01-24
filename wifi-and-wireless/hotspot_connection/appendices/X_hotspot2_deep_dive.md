## Appendix X: Hotspot 2.0 (Passpoint) Deep Dive

### X.1 ANQP Elements

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    ANQP ELEMENTS REFERENCE                                   │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  Standard ANQP Elements:                                                     │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │  ID      Name                        Description                    │    │
│  │  ──      ────                        ───────────                    │    │
│  │  256     Query List                  List of requested elements     │    │
│  │  257     Capability List             Supported ANQP elements        │    │
│  │  258     Venue Name                  Venue name in multiple langs   │    │
│  │  259     Emergency Call Number       Emergency numbers              │    │
│  │  260     Network Auth Type           Auth type (terms, online, etc) │    │
│  │  261     Roaming Consortium          Roaming partner OIs            │    │
│  │  262     IP Address Type Avail       IPv4/IPv6 availability         │    │
│  │  263     NAI Realm                   Supported realms and EAP       │    │
│  │  264     3GPP Cellular Network       PLMN IDs for cellular          │    │
│  │  265     AP Geospatial Location      GPS coordinates                │    │
│  │  266     AP Civic Location           Street address                 │    │
│  │  267     AP Location Public ID       Location identifier            │    │
│  │  268     Domain Name                 Domain names                   │    │
│  │  269     Emergency Alert ID          Alert system identifier        │    │
│  │  270     TDLS Capability             TDLS support                   │    │
│  │  271     Emergency NAI               Emergency realm                │    │
│  │  272     Neighbor Report             Neighbor APs                   │    │
│  │  273     Venue URL                   Venue website                  │    │
│  │  274     Advice of Charge            Pricing information            │    │
│  │  275     Local Content               Local services                 │    │
│  │  276     Network Auth Type w/ TS     Auth type with timestamp       │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  Hotspot 2.0 ANQP Elements (Vendor-Specific):                                │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │  Subtype  Name                       Description                    │    │
│  │  ───────  ────                       ───────────                    │    │
│  │    1      HS Query List              HS2.0 query list               │    │
│  │    2      HS Capability List         HS2.0 capabilities             │    │
│  │    3      Operator Friendly Name     Operator name (multi-lang)     │    │
│  │    4      WAN Metrics                WAN link info                  │    │
│  │    5      Connection Capability      Port/protocol availability     │    │
│  │    6      NAI Home Realm Query       Home realm check               │    │
│  │    7      Operating Class Indication Supported op classes           │    │
│  │    8      OSU Providers List         Online signup providers        │    │
│  │    9      Icon Request               Icon binary data               │    │
│  │   10      Icon Binary File           Icon file                      │    │
│  │   11      Operator Icon Metadata     Icon metadata                  │    │
│  │   12      OSU Providers NAI List     OSU NAI list                   │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### X.2 NAI Realm Configuration

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    NAI REALM CONFIGURATION                                   │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  NAI Realm Element Structure:                                                │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  ┌─────────────────────────────────────────────────────────────┐    │    │
│  │  │ NAI Realm Count: 2                                          │    │    │
│  │  ├─────────────────────────────────────────────────────────────┤    │    │
│  │  │ Realm 1:                                                    │    │    │
│  │  │   Encoding: 0 (UTF-8)                                       │    │    │
│  │  │   Realm: "example.com"                                      │    │    │
│  │  │   EAP Method Count: 2                                       │    │    │
│  │  │   ├── EAP Method 1:                                         │    │    │
│  │  │   │     Type: 13 (EAP-TLS)                                  │    │    │
│  │  │   │     Auth Params:                                        │    │    │
│  │  │   │       - Credential Type: Certificate                    │    │    │
│  │  │   │                                                         │    │    │
│  │  │   └── EAP Method 2:                                         │    │    │
│  │  │         Type: 21 (EAP-TTLS)                                 │    │    │
│  │  │         Auth Params:                                        │    │    │
│  │  │           - Non-EAP Inner: MS-CHAPv2                        │    │    │
│  │  │           - Credential Type: Username/Password              │    │    │
│  │  ├─────────────────────────────────────────────────────────────┤    │    │
│  │  │ Realm 2:                                                    │    │    │
│  │  │   Encoding: 0 (UTF-8)                                       │    │    │
│  │  │   Realm: "partner.org"                                      │    │    │
│  │  │   EAP Method Count: 1                                       │    │    │
│  │  │   └── EAP Method 1:                                         │    │    │
│  │  │         Type: 25 (EAP-PEAP)                                 │    │    │
│  │  │         Auth Params:                                        │    │    │
│  │  │           - Inner EAP: EAP-MSCHAPv2                         │    │    │
│  │  │           - Credential Type: Username/Password              │    │    │
│  │  └─────────────────────────────────────────────────────────────┘    │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  hostapd Configuration:                                                      │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │ # NAI Realm configuration                                           │    │
│  │ nai_realm=0,example.com,13[5:6],21[2:4][5:7]                        │    │
│  │ nai_realm=0,partner.org,25[3:26][5:7]                               │    │
│  │                                                                      │    │
│  │ # Format: encoding,realm,eap_method[auth_param]...                  │    │
│  │ # Auth params: [auth_id:auth_val]                                   │    │
│  │ #   2 = Non-EAP Inner Auth (1=PAP, 2=CHAP, 3=MSCHAP, 4=MSCHAPv2)   │    │
│  │ #   3 = Inner EAP (values same as EAP method types)                 │    │
│  │ #   5 = Credential Type (1=SIM, 2=USIM, 3=NFC, 4=HW, 5=Soft,       │    │
│  │ #                        6=Cert, 7=User/Pass, 9=Anonymous, 10=VID) │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### X.3 WAN Metrics

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    WAN METRICS ELEMENT                                       │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  WAN Metrics Structure:                                                      │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  Field                    Size      Description                     │    │
│  │  ─────                    ────      ───────────                     │    │
│  │  WAN Info                 1 byte    Link status and type            │    │
│  │    ├── Link Status        2 bits    0=down, 1=up, 2=test            │    │
│  │    ├── Symmetric Link     1 bit     Same up/down speed              │    │
│  │    ├── At Capacity        1 bit     Network at capacity             │    │
│  │    └── Reserved           4 bits                                    │    │
│  │  Downlink Speed           4 bytes   Kbps (0 = unknown)              │    │
│  │  Uplink Speed             4 bytes   Kbps (0 = unknown)              │    │
│  │  Downlink Load            1 byte    0-255 (255 = 100%)              │    │
│  │  Uplink Load              1 byte    0-255 (255 = 100%)              │    │
│  │  LMD (Load Measurement)   2 bytes   Duration in 1/10 seconds        │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  Example Configuration:                                                      │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │ # WAN Metrics                                                       │    │
│  │ # Format: wan_info:dl_speed:ul_speed:dl_load:ul_load:lmd            │    │
│  │ hs20_wan_metrics=01:8000:1000:80:240:3000                           │    │
│  │                                                                      │    │
│  │ # Interpretation:                                                   │    │
│  │ # wan_info=01: Link up, symmetric                                   │    │
│  │ # dl_speed=8000: 8 Mbps downlink                                    │    │
│  │ # ul_speed=1000: 1 Mbps uplink                                      │    │
│  │ # dl_load=80: ~31% downlink utilization                             │    │
│  │ # ul_load=240: ~94% uplink utilization                              │    │
│  │ # lmd=3000: 5 minute measurement duration                           │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

