## Appendix AJ: Regulatory Domain Deep Dive

### AJ.1 Channel Regulations by Region

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    REGULATORY DOMAIN DETAILS                                 │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  United States (FCC):                                                        │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  2.4 GHz Band:                                                       │    │
│  │  ┌────────────────────────────────────────────────────────────┐     │    │
│  │  │ Channels: 1-11                                             │     │    │
│  │  │ Max EIRP: 36 dBm (4W) with antenna gain                    │     │    │
│  │  │ Max TX Power: 30 dBm (1W) at antenna connector             │     │    │
│  │  │ Bandwidth: 20/40 MHz                                       │     │    │
│  │  └────────────────────────────────────────────────────────────┘     │    │
│  │                                                                      │    │
│  │  5 GHz Band:                                                         │    │
│  │  ┌────────────────────────────────────────────────────────────┐     │    │
│  │  │ UNII-1 (5150-5250 MHz): Channels 36-48                     │     │    │
│  │  │   - Indoor only                                            │     │    │
│  │  │   - Max EIRP: 23 dBm (200 mW)                              │     │    │
│  │  │   - No DFS required                                        │     │    │
│  │  │                                                            │     │    │
│  │  │ UNII-2A (5250-5350 MHz): Channels 52-64                    │     │    │
│  │  │   - Indoor only                                            │     │    │
│  │  │   - Max EIRP: 23 dBm (200 mW)                              │     │    │
│  │  │   - DFS required                                           │     │    │
│  │  │                                                            │     │    │
│  │  │ UNII-2C (5470-5725 MHz): Channels 100-144                  │     │    │
│  │  │   - Indoor/Outdoor                                         │     │    │
│  │  │   - Max EIRP: 24 dBm (250 mW)                              │     │    │
│  │  │   - DFS required                                           │     │    │
│  │  │                                                            │     │    │
│  │  │ UNII-3 (5725-5850 MHz): Channels 149-165                   │     │    │
│  │  │   - Indoor/Outdoor                                         │     │    │
│  │  │   - Max EIRP: 36 dBm (4W)                                  │     │    │
│  │  │   - No DFS required                                        │     │    │
│  │  │                                                            │     │    │
│  │  │ UNII-5 (5925-6425 MHz): WiFi 6E                            │     │    │
│  │  │   - Low Power Indoor (LPI): 30 dBm EIRP                    │     │    │
│  │  │   - Standard Power (AFC): 36 dBm EIRP                      │     │    │
│  │  │   - Very Low Power (VLP): 14 dBm EIRP                      │     │    │
│  │  │                                                            │     │    │
│  │  │ UNII-6 (6425-6525 MHz): WiFi 6E                            │     │    │
│  │  │   - Same power limits as UNII-5                            │     │    │
│  │  │                                                            │     │    │
│  │  │ UNII-7 (6525-6875 MHz): WiFi 6E                            │     │    │
│  │  │   - Same power limits as UNII-5                            │     │    │
│  │  │                                                            │     │    │
│  │  │ UNII-8 (6875-7125 MHz): WiFi 6E                            │     │    │
│  │  │   - Same power limits as UNII-5                            │     │    │
│  │  └────────────────────────────────────────────────────────────┘     │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  European Union (ETSI):                                                      │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  2.4 GHz Band:                                                       │    │
│  │  ┌────────────────────────────────────────────────────────────┐     │    │
│  │  │ Channels: 1-13                                             │     │    │
│  │  │ Max EIRP: 20 dBm (100 mW)                                  │     │    │
│  │  │ Bandwidth: 20/40 MHz                                       │     │    │
│  │  └────────────────────────────────────────────────────────────┘     │    │
│  │                                                                      │    │
│  │  5 GHz Band:                                                         │    │
│  │  ┌────────────────────────────────────────────────────────────┐     │    │
│  │  │ 5150-5250 MHz: Channels 36-48                              │     │    │
│  │  │   - Indoor only                                            │     │    │
│  │  │   - Max EIRP: 23 dBm (200 mW)                              │     │    │
│  │  │   - No DFS required                                        │     │    │
│  │  │                                                            │     │    │
│  │  │ 5250-5350 MHz: Channels 52-64                              │     │    │
│  │  │   - Indoor only                                            │     │    │
│  │  │   - Max EIRP: 23 dBm (200 mW)                              │     │    │
│  │  │   - DFS required                                           │     │    │
│  │  │                                                            │     │    │
│  │  │ 5470-5725 MHz: Channels 100-140                            │     │    │
│  │  │   - Indoor/Outdoor                                         │     │    │
│  │  │   - Max EIRP: 30 dBm (1W)                                  │     │    │
│  │  │   - DFS required                                           │     │    │
│  │  │   - TPC required                                           │     │    │
│  │  │                                                            │     │    │
│  │  │ Note: Channels 149-165 NOT available in EU                 │     │    │
│  │  └────────────────────────────────────────────────────────────┘     │    │
│  │                                                                      │    │
│  │  6 GHz Band (WiFi 6E):                                               │    │
│  │  ┌────────────────────────────────────────────────────────────┐     │    │
│  │  │ 5925-6425 MHz: Lower 6 GHz                                 │     │    │
│  │  │   - LPI: 23 dBm EIRP                                       │     │    │
│  │  │   - VLP: 14 dBm EIRP                                       │     │    │
│  │  │   - No AFC (Standard Power) in EU                          │     │    │
│  │  └────────────────────────────────────────────────────────────┘     │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  Japan (MIC):                                                                │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  2.4 GHz Band:                                                       │    │
│  │  ┌────────────────────────────────────────────────────────────┐     │    │
│  │  │ Channels: 1-14 (Channel 14 for 802.11b only)               │     │    │
│  │  │ Max EIRP: 10 mW/MHz (20 dBm for 20 MHz)                    │     │    │
│  │  └────────────────────────────────────────────────────────────┘     │    │
│  │                                                                      │    │
│  │  5 GHz Band:                                                         │    │
│  │  ┌────────────────────────────────────────────────────────────┐     │    │
│  │  │ W52 (5150-5250 MHz): Channels 36-48                        │     │    │
│  │  │   - Indoor only                                            │     │    │
│  │  │   - Max EIRP: 23 dBm                                       │     │    │
│  │  │                                                            │     │    │
│  │  │ W53 (5250-5350 MHz): Channels 52-64                        │     │    │
│  │  │   - Indoor only                                            │     │    │
│  │  │   - Max EIRP: 23 dBm                                       │     │    │
│  │  │   - DFS required                                           │     │    │
│  │  │                                                            │     │    │
│  │  │ W56 (5470-5725 MHz): Channels 100-144                      │     │    │
│  │  │   - Indoor/Outdoor                                         │     │    │
│  │  │   - Max EIRP: 23 dBm                                       │     │    │
│  │  │   - DFS required                                           │     │    │
│  │  └────────────────────────────────────────────────────────────┘     │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  China (SRRC):                                                               │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  2.4 GHz Band:                                                       │    │
│  │  ┌────────────────────────────────────────────────────────────┐     │    │
│  │  │ Channels: 1-13                                             │     │    │
│  │  │ Max EIRP: 20 dBm (100 mW)                                  │     │    │
│  │  └────────────────────────────────────────────────────────────┘     │    │
│  │                                                                      │    │
│  │  5 GHz Band:                                                         │    │
│  │  ┌────────────────────────────────────────────────────────────┐     │    │
│  │  │ 5150-5350 MHz: Channels 36-64                              │     │    │
│  │  │   - Indoor only                                            │     │    │
│  │  │   - Max EIRP: 23 dBm                                       │     │    │
│  │  │                                                            │     │    │
│  │  │ 5725-5850 MHz: Channels 149-165                            │     │    │
│  │  │   - Indoor/Outdoor                                         │     │    │
│  │  │   - Max EIRP: 33 dBm                                       │     │    │
│  │  │                                                            │     │    │
│  │  │ Note: UNII-2C (5470-5725) NOT available in China           │     │    │
│  │  └────────────────────────────────────────────────────────────┘     │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Appendix AK: Action Frame Reference

### AK.1 Radio Resource Management (802.11k) Action Frames

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    802.11k ACTION FRAMES                                     │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  Radio Measurement Request:                                                  │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  Category: 5 (Radio Measurement)                                    │    │
│  │  Action: 0 (Radio Measurement Request)                              │    │
│  │                                                                      │    │
│  │  Frame Format:                                                       │    │
│  │  ┌────────────────────────────────────────────────────────────┐     │    │
│  │  │ Field                Size    Description                   │     │    │
│  │  │ ─────                ────    ───────────                   │     │    │
│  │  │ Category             1       5 (Radio Measurement)         │     │    │
│  │  │ Action               1       0 (Request)                   │     │    │
│  │  │ Dialog Token         1       Sequence number               │     │    │
│  │  │ Number of Reps       2       Number of repetitions         │     │    │
│  │  │ Measurement Request  var     Measurement request elements  │     │    │
│  │  └────────────────────────────────────────────────────────────┘     │    │
│  │                                                                      │    │
│  │  Measurement Types:                                                  │    │
│  │  ┌────────────────────────────────────────────────────────────┐     │    │
│  │  │ Type   Name                    Description                 │     │    │
│  │  │ ────   ────                    ───────────                 │     │    │
│  │  │  0     Basic                   Basic measurement           │     │    │
│  │  │  1     CCA                     Clear Channel Assessment    │     │    │
│  │  │  2     RPI Histogram           Receive Power Indicator     │     │    │
│  │  │  3     Channel Load            Channel load measurement    │     │    │
│  │  │  4     Noise Histogram         Noise histogram             │     │    │
│  │  │  5     Beacon                  Beacon measurement          │     │    │
│  │  │  6     Frame                   Frame measurement           │     │    │
│  │  │  7     STA Statistics          Station statistics          │     │    │
│  │  │  8     LCI                     Location Configuration      │     │    │
│  │  │  9     Transmit Stream         Transmit stream measurement │     │    │
│  │  │ 10     Multicast Diagnostics   Multicast diagnostics       │     │    │
│  │  │ 11     Location Civic          Location civic measurement  │     │    │
│  │  │ 12     Location Identifier     Location identifier         │     │    │
│  │  │ 13     Directional Channel     Directional channel quality │     │    │
│  │  │ 14     Directional Measurement Directional measurement     │     │    │
│  │  │ 15     Directional Statistics  Directional statistics      │     │    │
│  │  │ 16     Fine Timing Measurement FTM measurement             │     │    │
│  │  └────────────────────────────────────────────────────────────┘     │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  Beacon Measurement Request:                                                 │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  Measurement Mode:                                                   │    │
│  │  ┌────────────────────────────────────────────────────────────┐     │    │
│  │  │ Mode   Name                    Description                 │     │    │
│  │  │ ────   ────                    ───────────                 │     │    │
│  │  │  0     Passive                 Passive scanning            │     │    │
│  │  │  1     Active                  Active scanning             │     │    │
│  │  │  2     Beacon Table            Report from beacon table    │     │    │
│  │  └────────────────────────────────────────────────────────────┘     │    │
│  │                                                                      │    │
│  │  Beacon Request Fields:                                              │    │
│  │  ┌────────────────────────────────────────────────────────────┐     │    │
│  │  │ Field                Size    Description                   │     │    │
│  │  │ ─────                ────    ───────────                   │     │    │
│  │  │ Regulatory Class     1       Operating class               │     │    │
│  │  │ Channel Number       1       Channel to measure            │     │    │
│  │  │ Randomization Int    2       Random delay interval         │     │    │
│  │  │ Measurement Duration 2       Duration in TUs               │     │    │
│  │  │ Measurement Mode     1       Passive/Active/Table          │     │    │
│  │  │ BSSID                6       Target BSSID (or wildcard)    │     │    │
│  │  │ Optional Subelements var     SSID, Reporting Detail, etc.  │     │    │
│  │  └────────────────────────────────────────────────────────────┘     │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  Neighbor Report Request/Response:                                           │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  Category: 5 (Radio Measurement)                                    │    │
│  │  Action: 4 (Neighbor Report Request)                                │    │
│  │  Action: 5 (Neighbor Report Response)                               │    │
│  │                                                                      │    │
│  │  Neighbor Report Element:                                            │    │
│  │  ┌────────────────────────────────────────────────────────────┐     │    │
│  │  │ Field                Size    Description                   │     │    │
│  │  │ ─────                ────    ───────────                   │     │    │
│  │  │ BSSID                6       Neighbor BSSID                │     │    │
│  │  │ BSSID Information    4       Capability information        │     │    │
│  │  │ Operating Class      1       Regulatory class              │     │    │
│  │  │ Channel Number       1       Channel number                │     │    │
│  │  │ PHY Type             1       PHY type                      │     │    │
│  │  │ Optional Subelements var     TSF, Country, etc.            │     │    │
│  │  └────────────────────────────────────────────────────────────┘     │    │
│  │                                                                      │    │
│  │  BSSID Information Field:                                            │    │
│  │  ┌────────────────────────────────────────────────────────────┐     │    │
│  │  │ Bit    Name                    Description                 │     │    │
│  │  │ ───    ────                    ───────────                 │     │    │
│  │  │ 0      AP Reachability         Reachability status         │     │    │
│  │  │ 1      (continued)             (2 bits total)              │     │    │
│  │  │ 2      Security                Security enabled            │     │    │
│  │  │ 3      Key Scope               Key scope                   │     │    │
│  │  │ 4      Spectrum Mgmt           Spectrum management         │     │    │
│  │  │ 5      QoS                     QoS capability              │     │    │
│  │  │ 6      APSD                    APSD capability             │     │    │
│  │  │ 7      Radio Measurement       RRM capability              │     │    │
│  │  │ 8      Delayed Block Ack       Delayed BA capability       │     │    │
│  │  │ 9      Immediate Block Ack     Immediate BA capability     │     │    │
│  │  │ 10     Mobility Domain         Same mobility domain        │     │    │
│  │  │ 11     High Throughput         HT capability               │     │    │
│  │  │ 12     Very High Throughput    VHT capability              │     │    │
│  │  │ 13     FTM                     FTM responder               │     │    │
│  │  │ 14-31  Reserved                                            │     │    │
│  │  └────────────────────────────────────────────────────────────┘     │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  Link Measurement Request/Report:                                            │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  Category: 5 (Radio Measurement)                                    │    │
│  │  Action: 2 (Link Measurement Request)                               │    │
│  │  Action: 3 (Link Measurement Report)                                │    │
│  │                                                                      │    │
│  │  Link Measurement Report Fields:                                     │    │
│  │  ┌────────────────────────────────────────────────────────────┐     │    │
│  │  │ Field                Size    Description                   │     │    │
│  │  │ ─────                ────    ───────────                   │     │    │
│  │  │ Dialog Token         1       Sequence number               │     │    │
│  │  │ TPC Report           4       Transmit power and link margin│     │    │
│  │  │ Receive Antenna ID   1       Receive antenna ID            │     │    │
│  │  │ Transmit Antenna ID  1       Transmit antenna ID           │     │    │
│  │  │ RCPI                 1       Received Channel Power Ind    │     │    │
│  │  │ RSNI                 1       Received Signal to Noise Ind  │     │    │
│  │  │ Optional Subelements var     DMG Link Margin, etc.         │     │    │
│  │  └────────────────────────────────────────────────────────────┘     │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### AK.2 Wireless Network Management (802.11v) Action Frames

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    802.11v ACTION FRAMES                                     │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  BSS Transition Management Request:                                          │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  Category: 10 (WNM)                                                 │    │
│  │  Action: 7 (BSS Transition Management Request)                      │    │
│  │                                                                      │    │
│  │  Frame Format:                                                       │    │
│  │  ┌────────────────────────────────────────────────────────────┐     │    │
│  │  │ Field                Size    Description                   │     │    │
│  │  │ ─────                ────    ───────────                   │     │    │
│  │  │ Category             1       10 (WNM)                      │     │    │
│  │  │ Action               1       7 (BTM Request)               │     │    │
│  │  │ Dialog Token         1       Sequence number               │     │    │
│  │  │ Request Mode         1       Request mode flags            │     │    │
│  │  │ Disassoc Timer       2       Disassociation timer (TUs)    │     │    │
│  │  │ Validity Interval    1       Candidate list validity       │     │    │
│  │  │ BSS Termination Dur  12      BSS termination duration      │     │    │
│  │  │ Session Info URL     var     Session information URL       │     │    │
│  │  │ Neighbor Report      var     Candidate AP list             │     │    │
│  │  └────────────────────────────────────────────────────────────┘     │    │
│  │                                                                      │    │
│  │  Request Mode Bits:                                                  │    │
│  │  ┌────────────────────────────────────────────────────────────┐     │    │
│  │  │ Bit   Name                    Description                  │     │    │
│  │  │ ───   ────                    ───────────                  │     │    │
│  │  │ 0     Preferred Candidate     Preferred candidate included │     │    │
│  │  │ 1     Abridged                Abridged neighbor list       │     │    │
│  │  │ 2     Disassoc Imminent       Disassociation imminent      │     │    │
│  │  │ 3     BSS Termination         BSS termination included     │     │    │
│  │  │ 4     ESS Disassoc Imminent   ESS disassociation imminent  │     │    │
│  │  │ 5-7   Reserved                                             │     │    │
│  │  └────────────────────────────────────────────────────────────┘     │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  BSS Transition Management Response:                                         │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  Category: 10 (WNM)                                                 │    │
│  │  Action: 8 (BSS Transition Management Response)                     │    │
│  │                                                                      │    │
│  │  Frame Format:                                                       │    │
│  │  ┌────────────────────────────────────────────────────────────┐     │    │
│  │  │ Field                Size    Description                   │     │    │
│  │  │ ─────                ────    ───────────                   │     │    │
│  │  │ Category             1       10 (WNM)                      │     │    │
│  │  │ Action               1       8 (BTM Response)              │     │    │
│  │  │ Dialog Token         1       Sequence number               │     │    │
│  │  │ Status Code          1       Accept/Reject status          │     │    │
│  │  │ BSS Termination Delay 1      Termination delay             │     │    │
│  │  │ Target BSSID         6       Target BSSID (if accepted)    │     │    │
│  │  │ Candidate List       var     Candidate preference list     │     │    │
│  │  └────────────────────────────────────────────────────────────┘     │    │
│  │                                                                      │    │
│  │  Status Codes:                                                       │    │
│  │  ┌────────────────────────────────────────────────────────────┐     │    │
│  │  │ Code   Description                                         │     │    │
│  │  │ ────   ───────────                                         │     │    │
│  │  │  0     Accept                                              │     │    │
│  │  │  1     Reject - Unspecified                                │     │    │
│  │  │  2     Reject - Insufficient beacon/probe response         │     │    │
│  │  │  3     Reject - Insufficient capacity                      │     │    │
│  │  │  4     Reject - BSS termination undesired                  │     │    │
│  │  │  5     Reject - BSS termination delay requested            │     │    │
│  │  │  6     Reject - STA BSS candidate list provided            │     │    │
│  │  │  7     Reject - No suitable BSS transition candidates      │     │    │
│  │  │  8     Reject - Leaving ESS                                │     │    │
│  │  └────────────────────────────────────────────────────────────┘     │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  WNM Sleep Mode Request/Response:                                            │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  Category: 10 (WNM)                                                 │    │
│  │  Action: 16 (WNM Sleep Mode Request)                                │    │
│  │  Action: 17 (WNM Sleep Mode Response)                               │    │
│  │                                                                      │    │
│  │  WNM Sleep Mode Element:                                             │    │
│  │  ┌────────────────────────────────────────────────────────────┐     │    │
│  │  │ Field                Size    Description                   │     │    │
│  │  │ ─────                ────    ───────────                   │     │    │
│  │  │ Action Type          1       Enter/Exit/Confirm            │     │    │
│  │  │ Response Status      1       Response status               │     │    │
│  │  │ Interval             2       Sleep interval                │     │    │
│  │  └────────────────────────────────────────────────────────────┘     │    │
│  │                                                                      │    │
│  │  Action Types:                                                       │    │
│  │  ┌────────────────────────────────────────────────────────────┐     │    │
│  │  │ Type   Description                                         │     │    │
│  │  │ ────   ───────────                                         │     │    │
│  │  │  0     Enter WNM Sleep Mode                                │     │    │
│  │  │  1     Exit WNM Sleep Mode                                 │     │    │
│  │  └────────────────────────────────────────────────────────────┘     │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  TIM Broadcast Request/Response:                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  Category: 10 (WNM)                                                 │    │
│  │  Action: 18 (TIM Broadcast Request)                                 │    │
│  │  Action: 19 (TIM Broadcast Response)                                │    │
│  │                                                                      │    │
│  │  Used for TIM broadcast in high-efficiency networks                 │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  Collocated Interference Report:                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  Category: 10 (WNM)                                                 │    │
│  │  Action: 11 (Collocated Interference Report)                        │    │
│  │                                                                      │    │
│  │  Reports interference from collocated radios (e.g., LTE, Bluetooth) │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### AK.3 Fast BSS Transition (802.11r) Action Frames

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    802.11r ACTION FRAMES                                     │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  FT Request:                                                                 │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  Category: 6 (Fast BSS Transition)                                  │    │
│  │  Action: 1 (FT Request)                                             │    │
│  │                                                                      │    │
│  │  Frame Format:                                                       │    │
│  │  ┌────────────────────────────────────────────────────────────┐     │    │
│  │  │ Field                Size    Description                   │     │    │
│  │  │ ─────                ────    ───────────                   │     │    │
│  │  │ Category             1       6 (Fast BSS Transition)       │     │    │
│  │  │ Action               1       1 (FT Request)                │     │    │
│  │  │ STA Address          6       Requesting STA address        │     │    │
│  │  │ Target AP Address    6       Target AP BSSID               │     │    │
│  │  │ FT Information       var     FT IEs (MDE, FTE, RSN, RIC)   │     │    │
│  │  └────────────────────────────────────────────────────────────┘     │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  FT Response:                                                                │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  Category: 6 (Fast BSS Transition)                                  │    │
│  │  Action: 2 (FT Response)                                            │    │
│  │                                                                      │    │
│  │  Frame Format:                                                       │    │
│  │  ┌────────────────────────────────────────────────────────────┐     │    │
│  │  │ Field                Size    Description                   │     │    │
│  │  │ ─────                ────    ───────────                   │     │    │
│  │  │ Category             1       6 (Fast BSS Transition)       │     │    │
│  │  │ Action               1       2 (FT Response)               │     │    │
│  │  │ STA Address          6       Requesting STA address        │     │    │
│  │  │ Target AP Address    6       Target AP BSSID               │     │    │
│  │  │ Status Code          2       Status of FT request          │     │    │
│  │  │ FT Information       var     FT IEs (MDE, FTE, RSN, RIC)   │     │    │
│  │  └────────────────────────────────────────────────────────────┘     │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  FT Confirm:                                                                 │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  Category: 6 (Fast BSS Transition)                                  │    │
│  │  Action: 3 (FT Confirm)                                             │    │
│  │                                                                      │    │
│  │  Sent by STA to confirm FT after receiving FT Response              │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  FT Ack:                                                                     │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  Category: 6 (Fast BSS Transition)                                  │    │
│  │  Action: 4 (FT Ack)                                                 │    │
│  │                                                                      │    │
│  │  Sent by AP to acknowledge FT Confirm                               │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  Mobility Domain Element (MDE):                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  Element ID: 54                                                     │    │
│  │  Length: 3                                                          │    │
│  │                                                                      │    │
│  │  Format:                                                             │    │
│  │  ┌────────────────────────────────────────────────────────────┐     │    │
│  │  │ Field                Size    Description                   │     │    │
│  │  │ ─────                ────    ───────────                   │     │    │
│  │  │ MDID                 2       Mobility Domain Identifier    │     │    │
│  │  │ FT Capability        1       FT capability and policy      │     │    │
│  │  └────────────────────────────────────────────────────────────┘     │    │
│  │                                                                      │    │
│  │  FT Capability Bits:                                                 │    │
│  │  ┌────────────────────────────────────────────────────────────┐     │    │
│  │  │ Bit   Name                    Description                  │     │    │
│  │  │ ───   ────                    ───────────                  │     │    │
│  │  │ 0     Fast BSS Transition     FT over-the-air supported    │     │    │
│  │  │ 1     Resource Request        Resource request supported   │     │    │
│  │  │ 2-7   Reserved                                             │     │    │
│  │  └────────────────────────────────────────────────────────────┘     │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  Fast BSS Transition Element (FTE):                                          │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  Element ID: 55                                                     │    │
│  │  Length: Variable                                                   │    │
│  │                                                                      │    │
│  │  Format:                                                             │    │
│  │  ┌────────────────────────────────────────────────────────────┐     │    │
│  │  │ Field                Size    Description                   │     │    │
│  │  │ ─────                ────    ───────────                   │     │    │
│  │  │ MIC Control          2       MIC control field             │     │    │
│  │  │ MIC                  16      Message Integrity Code        │     │    │
│  │  │ ANonce               32      AP nonce                      │     │    │
│  │  │ SNonce               32      STA nonce                     │     │    │
│  │  │ Optional Subelements var     R1KH-ID, R0KH-ID, GTK, etc.   │     │    │
│  │  └────────────────────────────────────────────────────────────┘     │    │
│  │                                                                      │    │
│  │  FTE Subelements:                                                    │    │
│  │  ┌────────────────────────────────────────────────────────────┐     │    │
│  │  │ ID    Name                    Description                  │     │    │
│  │  │ ──    ────                    ───────────                  │     │    │
│  │  │  1    R1KH-ID                 R1 Key Holder ID             │     │    │
│  │  │  2    GTK                     Group Temporal Key           │     │    │
│  │  │  3    R0KH-ID                 R0 Key Holder ID             │     │    │
│  │  │  4    IGTK                    Integrity GTK                │     │    │
│  │  │  5    OCI                     Operating Channel Info       │     │    │
│  │  │  6    BIGTK                   Beacon Integrity GTK         │     │    │
│  │  └────────────────────────────────────────────────────────────┘     │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Appendix AL: Common Error Scenarios and Troubleshooting

### AL.1 Authentication Failures

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    AUTHENTICATION FAILURE SCENARIOS                          │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  Scenario 1: Wrong PSK/Passphrase                                            │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  Symptoms:                                                           │    │
│  │  • Client associates but 4-way handshake fails                      │    │
│  │  • MIC verification failure in Message 2                            │    │
│  │  • Client deauthenticated with reason 15                            │    │
│  │                                                                      │    │
│  │  Log Messages:                                                       │    │
│  │  ┌────────────────────────────────────────────────────────────┐     │    │
│  │  │ wlan0: STA aa:bb:cc:dd:ee:ff WPA: invalid MIC in msg 2/4   │     │    │
│  │  │ wlan0: STA aa:bb:cc:dd:ee:ff WPA: 4-Way Handshake failed   │     │    │
│  │  │ wlan0: STA aa:bb:cc:dd:ee:ff IEEE 802.11: deauthenticated  │     │    │
│  │  │        due to local deauth request                         │     │    │
│  │  └────────────────────────────────────────────────────────────┘     │    │
│  │                                                                      │    │
│  │  Resolution:                                                         │    │
│  │  • Verify passphrase on client matches AP configuration             │    │
│  │  • Check for special characters that may be escaped differently     │    │
│  │  • Verify SSID matches exactly (case-sensitive)                     │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  Scenario 2: RADIUS Server Unreachable                                       │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  Symptoms:                                                           │    │
│  │  • Client associates but EAP authentication times out               │    │
│  │  • Multiple RADIUS retransmissions                                  │    │
│  │  • Client eventually disconnected                                   │    │
│  │                                                                      │    │
│  │  Log Messages:                                                       │    │
│  │  ┌────────────────────────────────────────────────────────────┐     │    │
│  │  │ wlan0: STA aa:bb:cc:dd:ee:ff RADIUS: No response from      │     │    │
│  │  │        authentication server                               │     │    │
│  │  │ wlan0: STA aa:bb:cc:dd:ee:ff RADIUS: Retransmitting        │     │    │
│  │  │        Access-Request                                      │     │    │
│  │  │ wlan0: STA aa:bb:cc:dd:ee:ff RADIUS: Authentication        │     │    │
│  │  │        timed out                                           │     │    │
│  │  └────────────────────────────────────────────────────────────┘     │    │
│  │                                                                      │    │
│  │  Resolution:                                                         │    │
│  │  • Verify RADIUS server IP and port                                 │    │
│  │  • Check network connectivity to RADIUS server                      │    │
│  │  • Verify shared secret matches                                     │    │
│  │  • Check RADIUS server logs                                         │    │
│  │  • Verify firewall allows UDP 1812/1813                             │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  Scenario 3: Certificate Validation Failure                                  │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  Symptoms:                                                           │    │
│  │  • EAP-TLS/TTLS/PEAP fails during TLS handshake                     │    │
│  │  • Certificate chain validation error                               │    │
│  │  • Client receives EAP-Failure                                      │    │
│  │                                                                      │    │
│  │  Common Causes:                                                      │    │
│  │  ┌────────────────────────────────────────────────────────────┐     │    │
│  │  │ • Expired certificate                                      │     │    │
│  │  │ • Missing intermediate CA certificate                      │     │    │
│  │  │ • Certificate not trusted by client                        │     │    │
│  │  │ • Certificate hostname mismatch                            │     │    │
│  │  │ • Certificate revoked (CRL/OCSP check)                     │     │    │
│  │  │ • Clock skew (certificate appears not yet valid)           │     │    │
│  │  └────────────────────────────────────────────────────────────┘     │    │
│  │                                                                      │    │
│  │  Resolution:                                                         │    │
│  │  • Check certificate expiration dates                               │    │
│  │  • Verify complete certificate chain                                │    │
│  │  • Install CA certificate on client                                 │    │
│  │  • Verify system time is correct                                    │    │
│  │  • Check CRL/OCSP status                                            │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  Scenario 4: SAE Authentication Failure                                      │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  Symptoms:                                                           │    │
│  │  • SAE commit/confirm exchange fails                                │    │
│  │  • Client receives authentication failure                           │    │
│  │  • Anti-clogging token required                                     │    │
│  │                                                                      │    │
│  │  Log Messages:                                                       │    │
│  │  ┌────────────────────────────────────────────────────────────┐     │    │
│  │  │ wlan0: STA aa:bb:cc:dd:ee:ff SAE: Commit mismatch          │     │    │
│  │  │ wlan0: STA aa:bb:cc:dd:ee:ff SAE: Confirm mismatch         │     │    │
│  │  │ wlan0: STA aa:bb:cc:dd:ee:ff SAE: Anti-clogging token      │     │    │
│  │  │        required                                            │     │    │
│  │  └────────────────────────────────────────────────────────────┘     │    │
│  │                                                                      │    │
│  │  Resolution:                                                         │    │
│  │  • Verify password matches                                          │    │
│  │  • Check SAE group compatibility                                    │    │
│  │  • Verify client supports WPA3-SAE                                  │    │
│  │  • Check for anti-clogging threshold                                │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### AL.2 Association Failures

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    ASSOCIATION FAILURE SCENARIOS                             │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  Scenario 1: Maximum Clients Reached                                         │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  Symptoms:                                                           │    │
│  │  • Association rejected with status 17                              │    │
│  │  • New clients cannot connect                                       │    │
│  │                                                                      │    │
│  │  Log Messages:                                                       │    │
│  │  ┌────────────────────────────────────────────────────────────┐     │    │
│  │  │ wlan0: STA aa:bb:cc:dd:ee:ff IEEE 802.11: association      │     │    │
│  │  │        denied - too many STAs                              │     │    │
│  │  └────────────────────────────────────────────────────────────┘     │    │
│  │                                                                      │    │
│  │  Resolution:                                                         │    │
│  │  • Increase max_num_sta in hostapd.conf                             │    │
│  │  • Disconnect idle clients                                          │    │
│  │  • Add additional APs for capacity                                  │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  Scenario 2: Capability Mismatch                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  Symptoms:                                                           │    │
│  │  • Association rejected with status 12 or 13                        │    │
│  │  • Client capabilities don't match AP requirements                  │    │
│  │                                                                      │    │
│  │  Common Causes:                                                      │    │
│  │  ┌────────────────────────────────────────────────────────────┐     │    │
│  │  │ • Client doesn't support required cipher suite             │     │    │
│  │  │ • Client doesn't support required AKM                      │     │    │
│  │  │ • Client doesn't support required HT/VHT/HE capabilities   │     │    │
│  │  │ • MFP required but client doesn't support                  │     │    │
│  │  └────────────────────────────────────────────────────────────┘     │    │
│  │                                                                      │    │
│  │  Resolution:                                                         │    │
│  │  • Check client capabilities                                        │    │
│  │  • Adjust AP security settings                                      │    │
│  │  • Enable mixed mode if needed                                      │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  Scenario 3: RSN IE Mismatch                                                 │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  Symptoms:                                                           │    │
│  │  • Association rejected with status 40                              │    │
│  │  • RSN IE in association request doesn't match beacon               │    │
│  │                                                                      │    │
│  │  Log Messages:                                                       │    │
│  │  ┌────────────────────────────────────────────────────────────┐     │    │
│  │  │ wlan0: STA aa:bb:cc:dd:ee:ff WPA: Invalid RSN IE in        │     │    │
│  │  │        association request                                 │     │    │
│  │  └────────────────────────────────────────────────────────────┘     │    │
│  │                                                                      │    │
│  │  Resolution:                                                         │    │
│  │  • Client may have cached old network profile                       │    │
│  │  • Delete and recreate network profile on client                    │    │
│  │  • Verify AP configuration hasn't changed                           │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### AL.3 Connectivity Issues

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    CONNECTIVITY ISSUE SCENARIOS                              │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  Scenario 1: DHCP Failure                                                    │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  Symptoms:                                                           │    │
│  │  • Client connected but no IP address                               │    │
│  │  • Client shows "Limited connectivity"                              │    │
│  │  • DHCP Discover sent but no Offer received                         │    │
│  │                                                                      │    │
│  │  Common Causes:                                                      │    │
│  │  ┌────────────────────────────────────────────────────────────┐     │    │
│  │  │ • DHCP server not running                                  │     │    │
│  │  │ • DHCP pool exhausted                                      │     │    │
│  │  │ • VLAN misconfiguration                                    │     │    │
│  │  │ • Firewall blocking DHCP                                   │     │    │
│  │  │ • Bridge not forwarding broadcast                          │     │    │
│  │  └────────────────────────────────────────────────────────────┘     │    │
│  │                                                                      │    │
│  │  Resolution:                                                         │    │
│  │  • Verify DHCP server is running                                    │    │
│  │  • Check DHCP pool availability                                     │    │
│  │  • Verify VLAN configuration                                        │    │
│  │  • Check bridge configuration                                       │    │
│  │  • Capture DHCP traffic to diagnose                                 │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  Scenario 2: Captive Portal Not Redirecting                                  │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  Symptoms:                                                           │    │
│  │  • Client connected with IP but no portal redirect                  │    │
│  │  • HTTP requests not intercepted                                    │    │
│  │  • HTTPS sites show certificate error                               │    │
│  │                                                                      │    │
│  │  Common Causes:                                                      │    │
│  │  ┌────────────────────────────────────────────────────────────┐     │    │
│  │  │ • Portal daemon not running                                │     │    │
│  │  │ • Firewall rules not configured                            │     │    │
│  │  │ • DNS interception not working                             │     │    │
│  │  │ • Client using DNS-over-HTTPS                              │     │    │
│  │  │ • Client using HTTPS for initial request                   │     │    │
│  │  └────────────────────────────────────────────────────────────┘     │    │
│  │                                                                      │    │
│  │  Resolution:                                                         │    │
│  │  • Verify portal daemon is running                                  │    │
│  │  • Check iptables/nftables rules                                    │    │
│  │  • Verify DNS interception                                          │    │
│  │  • Check client captive portal detection                            │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  Scenario 3: Intermittent Disconnections                                     │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  Symptoms:                                                           │    │
│  │  • Client randomly disconnects                                      │    │
│  │  • Deauthentication frames observed                                 │    │
│  │  • Connection unstable                                              │    │
│  │                                                                      │    │
│  │  Common Causes:                                                      │    │
│  │  ┌────────────────────────────────────────────────────────────┐     │    │
│  │  │ • Weak signal / interference                               │     │    │
│  │  │ • Deauthentication attack                                  │     │    │
│  │  │ • Inactivity timeout                                       │     │    │
│  │  │ • Session timeout                                          │     │    │
│  │  │ • DFS channel switch                                       │     │    │
│  │  │ • Power save issues                                        │     │    │
│  │  └────────────────────────────────────────────────────────────┘     │    │
│  │                                                                      │    │
│  │  Resolution:                                                         │    │
│  │  • Check signal strength and SNR                                    │    │
│  │  • Enable MFP to prevent deauth attacks                             │    │
│  │  • Adjust timeout values                                            │    │
│  │  • Check for DFS events                                             │    │
│  │  • Analyze power save behavior                                      │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Appendix AM: Wireshark Filter Reference

### AM.1 802.11 Frame Filters

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    WIRESHARK 802.11 FILTERS                                  │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  Frame Type Filters:                                                         │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  Management Frames:                                                  │    │
│  │  ┌────────────────────────────────────────────────────────────┐     │    │
│  │  │ Filter                          Description                │     │    │
│  │  │ ──────                          ───────────                │     │    │
│  │  │ wlan.fc.type == 0               All management frames      │     │    │
│  │  │ wlan.fc.type_subtype == 0x00    Association Request        │     │    │
│  │  │ wlan.fc.type_subtype == 0x01    Association Response       │     │    │
│  │  │ wlan.fc.type_subtype == 0x02    Reassociation Request      │     │    │
│  │  │ wlan.fc.type_subtype == 0x03    Reassociation Response     │     │    │
│  │  │ wlan.fc.type_subtype == 0x04    Probe Request              │     │    │
│  │  │ wlan.fc.type_subtype == 0x05    Probe Response             │     │    │
│  │  │ wlan.fc.type_subtype == 0x08    Beacon                     │     │    │
│  │  │ wlan.fc.type_subtype == 0x0a    Disassociation             │     │    │
│  │  │ wlan.fc.type_subtype == 0x0b    Authentication             │     │    │
│  │  │ wlan.fc.type_subtype == 0x0c    Deauthentication           │     │    │
│  │  │ wlan.fc.type_subtype == 0x0d    Action                     │     │    │
│  │  │ wlan.fc.type_subtype == 0x0e    Action No Ack              │     │    │
│  │  └────────────────────────────────────────────────────────────┘     │    │
│  │                                                                      │    │
│  │  Control Frames:                                                     │    │
│  │  ┌────────────────────────────────────────────────────────────┐     │    │
│  │  │ Filter                          Description                │     │    │
│  │  │ ──────                          ───────────                │     │    │
│  │  │ wlan.fc.type == 1               All control frames         │     │    │
│  │  │ wlan.fc.type_subtype == 0x18    Block Ack Request          │     │    │
│  │  │ wlan.fc.type_subtype == 0x19    Block Ack                  │     │    │
│  │  │ wlan.fc.type_subtype == 0x1a    PS-Poll                    │     │    │
│  │  │ wlan.fc.type_subtype == 0x1b    RTS                        │     │    │
│  │  │ wlan.fc.type_subtype == 0x1c    CTS                        │     │    │
│  │  │ wlan.fc.type_subtype == 0x1d    ACK                        │     │    │
│  │  │ wlan.fc.type_subtype == 0x1e    CF-End                     │     │    │
│  │  └────────────────────────────────────────────────────────────┘     │    │
│  │                                                                      │    │
│  │  Data Frames:                                                        │    │
│  │  ┌────────────────────────────────────────────────────────────┐     │    │
│  │  │ Filter                          Description                │     │    │
│  │  │ ──────                          ───────────                │     │    │
│  │  │ wlan.fc.type == 2               All data frames            │     │    │
│  │  │ wlan.fc.type_subtype == 0x20    Data                       │     │    │
│  │  │ wlan.fc.type_subtype == 0x24    Null Data                  │     │    │
│  │  │ wlan.fc.type_subtype == 0x28    QoS Data                   │     │    │
│  │  │ wlan.fc.type_subtype == 0x2c    QoS Null                   │     │    │
│  │  └────────────────────────────────────────────────────────────┘     │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  Address Filters:                                                            │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  ┌────────────────────────────────────────────────────────────┐     │    │
│  │  │ Filter                          Description                │     │    │
│  │  │ ──────                          ───────────                │     │    │
│  │  │ wlan.addr == aa:bb:cc:dd:ee:ff  Any address field          │     │    │
│  │  │ wlan.sa == aa:bb:cc:dd:ee:ff    Source address             │     │    │
│  │  │ wlan.da == aa:bb:cc:dd:ee:ff    Destination address        │     │    │
│  │  │ wlan.ta == aa:bb:cc:dd:ee:ff    Transmitter address        │     │    │
│  │  │ wlan.ra == aa:bb:cc:dd:ee:ff    Receiver address           │     │    │
│  │  │ wlan.bssid == aa:bb:cc:dd:ee:ff BSSID                      │     │    │
│  │  └────────────────────────────────────────────────────────────┘     │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  SSID Filters:                                                               │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  ┌────────────────────────────────────────────────────────────┐     │    │
│  │  │ Filter                          Description                │     │    │
│  │  │ ──────                          ───────────                │     │    │
│  │  │ wlan.ssid == "MyNetwork"        Exact SSID match           │     │    │
│  │  │ wlan.ssid contains "Guest"      SSID contains string       │     │    │
│  │  │ wlan.ssid == ""                 Hidden SSID (empty)        │     │    │
│  │  └────────────────────────────────────────────────────────────┘     │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### AM.2 EAPOL and Authentication Filters

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    EAPOL AND AUTHENTICATION FILTERS                          │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  EAPOL Filters:                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  ┌────────────────────────────────────────────────────────────┐     │    │
│  │  │ Filter                          Description                │     │    │
│  │  │ ──────                          ───────────                │     │    │
│  │  │ eapol                           All EAPOL frames           │     │    │
│  │  │ eapol.type == 0                 EAP-Packet                 │     │    │
│  │  │ eapol.type == 1                 EAPOL-Start                │     │    │
│  │  │ eapol.type == 2                 EAPOL-Logoff               │     │    │
│  │  │ eapol.type == 3                 EAPOL-Key                  │     │    │
│  │  │ eapol.keydes.type == 2          RSN Key (WPA2)             │     │    │
│  │  │ eapol.keydes.type == 254        WPA Key                    │     │    │
│  │  └────────────────────────────────────────────────────────────┘     │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  4-Way Handshake Filters:                                                    │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  ┌────────────────────────────────────────────────────────────┐     │    │
│  │  │ Filter                          Description                │     │    │
│  │  │ ──────                          ───────────                │     │    │
│  │  │ eapol.keydes.key_info == 0x008a Message 1 (ANonce)         │     │    │
│  │  │ eapol.keydes.key_info == 0x010a Message 2 (SNonce+MIC)     │     │    │
│  │  │ eapol.keydes.key_info == 0x13ca Message 3 (GTK+MIC)        │     │    │
│  │  │ eapol.keydes.key_info == 0x030a Message 4 (ACK)            │     │    │
│  │  │                                                            │     │    │
│  │  │ # More reliable filters:                                   │     │    │
│  │  │ eapol && !eapol.keydes.key_info.ack                        │     │    │
│  │  │   && !eapol.keydes.key_info.mic                            │     │    │
│  │  │   && eapol.keydes.nonce                   # Message 1      │     │    │
│  │  │                                                            │     │    │
│  │  │ eapol && !eapol.keydes.key_info.ack                        │     │    │
│  │  │   && eapol.keydes.key_info.mic                             │     │    │
│  │  │   && !eapol.keydes.key_info.secure        # Message 2      │     │    │
│  │  │                                                            │     │    │
│  │  │ eapol && eapol.keydes.key_info.ack                         │     │    │
│  │  │   && eapol.keydes.key_info.mic                             │     │    │
│  │  │   && eapol.keydes.key_info.secure         # Message 3      │     │    │
│  │  │                                                            │     │    │
│  │  │ eapol && !eapol.keydes.key_info.ack                        │     │    │
│  │  │   && eapol.keydes.key_info.mic                             │     │    │
│  │  │   && eapol.keydes.key_info.secure         # Message 4      │     │    │
│  │  └────────────────────────────────────────────────────────────┘     │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  EAP Filters:                                                                │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  ┌────────────────────────────────────────────────────────────┐     │    │
│  │  │ Filter                          Description                │     │    │
│  │  │ ──────                          ───────────                │     │    │
│  │  │ eap                             All EAP frames             │     │    │
│  │  │ eap.code == 1                   EAP-Request                │     │    │
│  │  │ eap.code == 2                   EAP-Response               │     │    │
│  │  │ eap.code == 3                   EAP-Success                │     │    │
│  │  │ eap.code == 4                   EAP-Failure                │     │    │
│  │  │ eap.type == 1                   EAP-Identity               │     │    │
│  │  │ eap.type == 4                   EAP-MD5                    │     │    │
│  │  │ eap.type == 13                  EAP-TLS                    │     │    │
│  │  │ eap.type == 21                  EAP-TTLS                   │     │    │
│  │  │ eap.type == 25                  EAP-PEAP                   │     │    │
│  │  │ eap.type == 18                  EAP-SIM                    │     │    │
│  │  │ eap.type == 23                  EAP-AKA                    │     │    │
│  │  │ eap.type == 50                  EAP-AKA'                   │     │    │
│  │  │ eap.type == 43                  EAP-FAST                   │     │    │
│  │  └────────────────────────────────────────────────────────────┘     │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  SAE Filters:                                                                │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  ┌────────────────────────────────────────────────────────────┐     │    │
│  │  │ Filter                          Description                │     │    │
│  │  │ ──────                          ───────────                │     │    │
│  │  │ wlan.fixed.auth.alg == 3        SAE authentication         │     │    │
│  │  │ wlan.fixed.auth_seq == 1        SAE Commit                 │     │    │
│  │  │ wlan.fixed.auth_seq == 2        SAE Confirm                │     │    │
│  │  └────────────────────────────────────────────────────────────┘     │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### AM.3 RADIUS Filters

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    RADIUS FILTERS                                            │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  RADIUS Packet Type Filters:                                                 │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  ┌────────────────────────────────────────────────────────────┐     │    │
│  │  │ Filter                          Description                │     │    │
│  │  │ ──────                          ───────────                │     │    │
│  │  │ radius                          All RADIUS packets         │     │    │
│  │  │ radius.code == 1                Access-Request             │     │    │
│  │  │ radius.code == 2                Access-Accept              │     │    │
│  │  │ radius.code == 3                Access-Reject              │     │    │
│  │  │ radius.code == 4                Accounting-Request         │     │    │
│  │  │ radius.code == 5                Accounting-Response        │     │    │
│  │  │ radius.code == 11               Access-Challenge           │     │    │
│  │  │ radius.code == 40               Disconnect-Request         │     │    │
│  │  │ radius.code == 41               Disconnect-ACK             │     │    │
│  │  │ radius.code == 42               Disconnect-NAK             │     │    │
│  │  │ radius.code == 43               CoA-Request                │     │    │
│  │  │ radius.code == 44               CoA-ACK                    │     │    │
│  │  │ radius.code == 45               CoA-NAK                    │     │    │
│  │  └────────────────────────────────────────────────────────────┘     │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  RADIUS Attribute Filters:                                                   │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  ┌────────────────────────────────────────────────────────────┐     │    │
│  │  │ Filter                          Description                │     │    │
│  │  │ ──────                          ───────────                │     │    │
│  │  │ radius.User_Name                User-Name attribute        │     │    │
│  │  │ radius.User_Name == "user@realm" Specific user             │     │    │
│  │  │ radius.Calling_Station_Id       Calling-Station-Id         │     │    │
│  │  │ radius.Called_Station_Id        Called-Station-Id          │     │    │
│  │  │ radius.NAS_IP_Address           NAS-IP-Address             │     │    │
│  │  │ radius.NAS_Port                 NAS-Port                   │     │    │
│  │  │ radius.Framed_IP_Address        Framed-IP-Address          │     │    │
│  │  │ radius.Session_Timeout          Session-Timeout            │     │    │
│  │  │ radius.Tunnel_Type              Tunnel-Type                │     │    │
│  │  │ radius.Tunnel_Medium_Type       Tunnel-Medium-Type         │     │    │
│  │  │ radius.Tunnel_Private_Group_Id  Tunnel-Private-Group-Id    │     │    │
│  │  │ radius.Acct_Session_Id          Acct-Session-Id            │     │    │
│  │  │ radius.Acct_Status_Type         Acct-Status-Type           │     │    │
│  │  │ radius.Acct_Input_Octets        Acct-Input-Octets          │     │    │
│  │  │ radius.Acct_Output_Octets       Acct-Output-Octets         │     │    │
│  │  │ radius.Acct_Session_Time        Acct-Session-Time          │     │    │
│  │  │ radius.Acct_Terminate_Cause     Acct-Terminate-Cause       │     │    │
│  │  └────────────────────────────────────────────────────────────┘     │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  RADIUS EAP Filters:                                                         │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  ┌────────────────────────────────────────────────────────────┐     │    │
│  │  │ Filter                          Description                │     │    │
│  │  │ ──────                          ───────────                │     │    │
│  │  │ radius.EAP_Message              EAP-Message attribute      │     │    │
│  │  │ radius.Message_Authenticator    Message-Authenticator      │     │    │
│  │  │ radius.State                    State attribute            │     │    │
│  │  └────────────────────────────────────────────────────────────┘     │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### AM.4 DHCP Filters

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    DHCP FILTERS                                              │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  DHCP Message Type Filters:                                                  │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  ┌────────────────────────────────────────────────────────────┐     │    │
│  │  │ Filter                          Description                │     │    │
│  │  │ ──────                          ───────────                │     │    │
│  │  │ dhcp                            All DHCP packets           │     │    │
│  │  │ dhcp.option.dhcp == 1           DHCP Discover              │     │    │
│  │  │ dhcp.option.dhcp == 2           DHCP Offer                 │     │    │
│  │  │ dhcp.option.dhcp == 3           DHCP Request               │     │    │
│  │  │ dhcp.option.dhcp == 4           DHCP Decline               │     │    │
│  │  │ dhcp.option.dhcp == 5           DHCP ACK                   │     │    │
│  │  │ dhcp.option.dhcp == 6           DHCP NAK                   │     │    │
│  │  │ dhcp.option.dhcp == 7           DHCP Release               │     │    │
│  │  │ dhcp.option.dhcp == 8           DHCP Inform                │     │    │
│  │  └────────────────────────────────────────────────────────────┘     │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  DHCP Option Filters:                                                        │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  ┌────────────────────────────────────────────────────────────┐     │    │
│  │  │ Filter                          Description                │     │    │
│  │  │ ──────                          ───────────                │     │    │
│  │  │ dhcp.hw.mac_addr                Client MAC address         │     │    │
│  │  │ dhcp.ip.your                    Your (client) IP address   │     │    │
│  │  │ dhcp.ip.server                  Server IP address          │     │    │
│  │  │ dhcp.option.subnet_mask         Subnet mask                │     │    │
│  │  │ dhcp.option.router              Default gateway            │     │    │
│  │  │ dhcp.option.domain_name_server  DNS servers                │     │    │
│  │  │ dhcp.option.lease_time          Lease time                 │     │    │
│  │  │ dhcp.option.hostname            Client hostname            │     │    │
│  │  │ dhcp.option.vendor_class_id     Vendor class ID            │     │    │
│  │  │ dhcp.option.requested_ip_address Requested IP              │     │    │
│  │  └────────────────────────────────────────────────────────────┘     │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### AM.5 Hotspot 2.0 / GAS / ANQP Filters

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    HOTSPOT 2.0 / GAS / ANQP FILTERS                          │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  GAS Filters:                                                                │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  ┌────────────────────────────────────────────────────────────┐     │    │
│  │  │ Filter                          Description                │     │    │
│  │  │ ──────                          ───────────                │     │    │
│  │  │ wlan.fixed.publicact == 10      GAS Initial Request        │     │    │
│  │  │ wlan.fixed.publicact == 11      GAS Initial Response       │     │    │
│  │  │ wlan.fixed.publicact == 12      GAS Comeback Request       │     │    │
│  │  │ wlan.fixed.publicact == 13      GAS Comeback Response      │     │    │
│  │  └────────────────────────────────────────────────────────────┘     │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  ANQP Filters:                                                               │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  ┌────────────────────────────────────────────────────────────┐     │    │
│  │  │ Filter                          Description                │     │    │
│  │  │ ──────                          ───────────                │     │    │
│  │  │ wlan.anqp                       All ANQP elements          │     │    │
│  │  │ wlan.anqp.info_id == 256        ANQP Query List            │     │    │
│  │  │ wlan.anqp.info_id == 257        ANQP Capability List       │     │    │
│  │  │ wlan.anqp.info_id == 258        Venue Name                 │     │    │
│  │  │ wlan.anqp.info_id == 260        Network Auth Type          │     │    │
│  │  │ wlan.anqp.info_id == 261        Roaming Consortium         │     │    │
│  │  │ wlan.anqp.info_id == 262        IP Address Type            │     │    │
│  │  │ wlan.anqp.info_id == 263        NAI Realm                  │     │    │
│  │  │ wlan.anqp.info_id == 264        3GPP Cellular Network      │     │    │
│  │  │ wlan.anqp.info_id == 268        Domain Name                │     │    │
│  │  └────────────────────────────────────────────────────────────┘     │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  Hotspot 2.0 ANQP Filters:                                                   │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  ┌────────────────────────────────────────────────────────────┐     │    │
│  │  │ Filter                          Description                │     │    │
│  │  │ ──────                          ───────────                │     │    │
│  │  │ wlan.hs20.anqp                  HS2.0 ANQP elements        │     │    │
│  │  │ wlan.hs20.anqp.subtype == 1     HS2.0 Query List           │     │    │
│  │  │ wlan.hs20.anqp.subtype == 2     HS2.0 Capability List      │     │    │
│  │  │ wlan.hs20.anqp.subtype == 3     Operator Friendly Name     │     │    │
│  │  │ wlan.hs20.anqp.subtype == 4     WAN Metrics                │     │    │
│  │  │ wlan.hs20.anqp.subtype == 5     Connection Capability      │     │    │
│  │  │ wlan.hs20.anqp.subtype == 6     NAI Home Realm Query       │     │    │
│  │  │ wlan.hs20.anqp.subtype == 7     Operating Class Indication │     │    │
│  │  │ wlan.hs20.anqp.subtype == 8     OSU Providers List         │     │    │
│  │  │ wlan.hs20.anqp.subtype == 11    Icon Request               │     │    │
│  │  │ wlan.hs20.anqp.subtype == 12    Icon Binary File           │     │    │
│  │  └────────────────────────────────────────────────────────────┘     │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Appendix AN: Complete Configuration Examples

### AN.1 Enterprise WPA2/WPA3 with RADIUS

```
# /etc/hostapd/hostapd-enterprise.conf
# Complete Enterprise WiFi Configuration

# Interface Configuration
interface=wlan0
driver=nl80211
bridge=br0

# Basic Settings
ssid=Corporate-WiFi
country_code=US
ieee80211d=1
ieee80211h=1

# Radio Settings (5 GHz)
hw_mode=a
channel=36
ieee80211n=1
ieee80211ac=1
ieee80211ax=1

# HT Capabilities (802.11n)
ht_capab=[HT40+][SHORT-GI-20][SHORT-GI-40][TX-STBC][RX-STBC1][DSSS_CCK-40]

# VHT Capabilities (802.11ac)
vht_oper_chwidth=1
vht_oper_centr_freq_seg0_idx=42
vht_capab=[MAX-MPDU-11454][RXLDPC][SHORT-GI-80][TX-STBC-2BY1][RX-STBC-1][MAX-A-MPDU-LEN-EXP7][RX-ANTENNA-PATTERN][TX-ANTENNA-PATTERN]

# HE Capabilities (802.11ax)
he_su_beamformer=1
he_su_beamformee=1
he_mu_beamformer=1
he_bss_color=1
he_default_pe_duration=4
he_rts_threshold=1023
he_mu_edca_qos_info_param_count=0
he_mu_edca_qos_info_q_ack=0
he_mu_edca_qos_info_queue_request=0
he_mu_edca_qos_info_txop_request=0

# Security - WPA2/WPA3 Enterprise
wpa=2
wpa_key_mgmt=WPA-EAP WPA-EAP-SHA256 WPA-EAP-SUITE-B-192
rsn_pairwise=CCMP CCMP-256 GCMP GCMP-256
group_cipher=CCMP

# IEEE 802.1X
ieee8021x=1
eapol_version=2
eapol_key_index_workaround=0

# RADIUS Authentication Server
auth_server_addr=10.0.0.100
auth_server_port=1812
auth_server_shared_secret=RadiusSecret123!

# RADIUS Authentication Server (Backup)
auth_server_addr=10.0.0.101
auth_server_port=1812
auth_server_shared_secret=RadiusSecret123!

# RADIUS Accounting Server
acct_server_addr=10.0.0.100
acct_server_port=1813
acct_server_shared_secret=RadiusSecret123!

# RADIUS Accounting Server (Backup)
acct_server_addr=10.0.0.101
acct_server_port=1813
acct_server_shared_secret=RadiusSecret123!

# RADIUS Settings
radius_retry_primary_interval=600
radius_acct_interim_interval=300
radius_request_cui=1
radius_auth_req_attr=126:s:Corporate-WiFi
radius_das_port=3799
radius_das_client=10.0.0.100 RadiusSecret123!
radius_das_require_event_timestamp=1
radius_das_require_message_authenticator=1

# Management Frame Protection (802.11w)
ieee80211w=2
group_mgmt_cipher=BIP-CMAC-256

# Fast Transition (802.11r)
mobility_domain=a1b2
ft_over_ds=1
ft_psk_generate_local=0
pmk_r1_push=1
r0_key_lifetime=10000
r1_key_holder=000102030405
reassociation_deadline=1000
r0kh=02:00:00:00:03:00 nas1.example.com 000102030405060708090a0b0c0d0e0f
r0kh=02:00:00:00:04:00 nas2.example.com 000102030405060708090a0b0c0d0e0f
r1kh=02:00:00:00:03:00 02:00:00:00:03:00 000102030405060708090a0b0c0d0e0f
r1kh=02:00:00:00:04:00 02:00:00:00:04:00 000102030405060708090a0b0c0d0e0f

# OKC (Opportunistic Key Caching)
okc=1

# PMKSA Caching
disable_pmksa_caching=0
pmksa_cache_lifetime=43200

# Radio Resource Management (802.11k)
rrm_neighbor_report=1
rrm_beacon_report=1

# BSS Transition Management (802.11v)
bss_transition=1
wnm_sleep_mode=1
wnm_sleep_mode_no_keys=0

# MBO (Multi-Band Operation)
mbo=1
mbo_cell_data_conn_pref=1

# OCE (Optimized Connectivity Experience)
oce=1

# Logging
logger_syslog=-1
logger_syslog_level=2
logger_stdout=-1
logger_stdout_level=2

# Control Interface
ctrl_interface=/var/run/hostapd
ctrl_interface_group=0

# Misc
ap_max_inactivity=300
skip_inactivity_poll=0
disassoc_low_ack=1
max_num_sta=128
```

### AN.2 Hotspot 2.0 Configuration

```
# /etc/hostapd/hostapd-hs20.conf
# Complete Hotspot 2.0 Configuration

# Interface Configuration
interface=wlan0
driver=nl80211
bridge=br0

# Basic Settings
ssid=Passpoint-Network
utf8_ssid=1
country_code=US
ieee80211d=1
ieee80211h=1

# Radio Settings
hw_mode=a
channel=36
ieee80211n=1
ieee80211ac=1
ieee80211ax=1

# Security - WPA2 Enterprise
wpa=2
wpa_key_mgmt=WPA-EAP WPA-EAP-SHA256
rsn_pairwise=CCMP
group_cipher=CCMP

# IEEE 802.1X
ieee8021x=1
eapol_version=2

# RADIUS
auth_server_addr=10.0.0.100
auth_server_port=1812
auth_server_shared_secret=RadiusSecret123!
acct_server_addr=10.0.0.100
acct_server_port=1813
acct_server_shared_secret=RadiusSecret123!

# Management Frame Protection
ieee80211w=1

# Interworking (802.11u)
interworking=1
access_network_type=2
internet=1
asra=0
esr=0
uesa=0
venue_group=2
venue_type=8
venue_name=eng:Example Venue
venue_name=fra:Lieu Exemple
venue_url=1:http://www.example.com/info/

# HESSID (Homogeneous ESS Identifier)
hessid=02:03:04:05:06:07

# Roaming Consortium
roaming_consortium=506F9A
roaming_consortium=001BC504BD
roaming_consortium=001BC50460

# Network Authentication Type
network_auth_type=00

# IP Address Type Availability
ipaddr_type_availability=0c

# Domain Name
domain_name=example.com,another.example.com

# 3GPP Cellular Network Information
anqp_3gpp_cell_net=310,026;310,260

# NAI Realm
nai_realm=0,example.com,13[5:6],21[2:4][5:7]
nai_realm=0,another.example.com,13[5:6],21[2:4][5:7]

# Hotspot 2.0 Configuration
hs20=1
hs20_release=3
disable_dgaf=0
osen=0

# Operator Friendly Name
hs20_oper_friendly_name=eng:Example Operator
hs20_oper_friendly_name=fra:Opérateur Exemple

# WAN Metrics
# Format: WAN Info:DL Speed:UL Speed:DL Load:UL Load:LMD
hs20_wan_metrics=01:8000:1000:80:240:3000

# Connection Capability
# Format: IP Protocol:Port Number:Status
hs20_conn_capab=1:0:2
hs20_conn_capab=6:22:1
hs20_conn_capab=6:80:1
hs20_conn_capab=6:443:1
hs20_conn_capab=6:5060:0
hs20_conn_capab=17:500:1
hs20_conn_capab=17:5060:0
hs20_conn_capab=17:4500:1
hs20_conn_capab=50:0:1

# Operating Class Indication
hs20_operating_class=51
hs20_operating_class=73
hs20_operating_class=5173

# OSU (Online Sign-Up) Providers
osu_ssid="OSU-Network"
osu_server_uri=https://osu.example.com/
osu_friendly_name=eng:Example OSU
osu_friendly_name=fra:OSU Exemple
osu_nai=anonymous@example.com
osu_nai2=anonymous@example.com
osu_method_list=1 0
osu_icon=icon32eng.png
osu_icon=icon32fra.png
osu_service_desc=eng:Example services
osu_service_desc=fra:Services Exemple

# Icons
hs20_icon=32:32:eng:image/png:icon32eng.png:/etc/hostapd/icons/icon32eng.png
hs20_icon=32:32:fra:image/png:icon32fra.png:/etc/hostapd/icons/icon32fra.png
hs20_icon=64:64:eng:image/png:icon64eng.png:/etc/hostapd/icons/icon64eng.png

# Deauthentication Request Timeout
hs20_deauth_req_timeout=60

# T&C (Terms and Conditions)
hs20_t_c_filename=terms-and-conditions
hs20_t_c_timestamp=1234567890
hs20_t_c_server_url=https://example.com/t_and_c?addr=@1@&ap=123

# GAS/ANQP Settings
gas_address3=0
gas_frag_limit=1400
gas_comeback_delay=500

# Proxy ARP
proxy_arp=1

# DGAF (Downstream Group-Addressed Forwarding)
na_mcast_to_ucast=1

# QoS Map
qos_map_set=0,0,2,16,1,1,255,255,0,0,255,255,0,0,255,255,34,34,36,38,40,42,44,46

# Control Interface
ctrl_interface=/var/run/hostapd
ctrl_interface_group=0
```

---

## Appendix AO: Performance Benchmarks and Metrics

### AO.1 Throughput Benchmarks by WiFi Generation

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    WIFI THROUGHPUT BENCHMARKS                                │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  Theoretical Maximum Throughput:                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  ┌────────────────────────────────────────────────────────────┐     │    │
│  │  │ Standard    Bandwidth   Streams   Max PHY Rate   Typical  │     │    │
│  │  │ ────────    ─────────   ───────   ────────────   ───────  │     │    │
│  │  │ 802.11b     20 MHz      1         11 Mbps        5 Mbps   │     │    │
│  │  │ 802.11a     20 MHz      1         54 Mbps        25 Mbps  │     │    │
│  │  │ 802.11g     20 MHz      1         54 Mbps        25 Mbps  │     │    │
│  │  │ 802.11n     20 MHz      1         72 Mbps        35 Mbps  │     │    │
│  │  │ 802.11n     40 MHz      1         150 Mbps       70 Mbps  │     │    │
│  │  │ 802.11n     40 MHz      4         600 Mbps       280 Mbps │     │    │
│  │  │ 802.11ac    80 MHz      1         433 Mbps       200 Mbps │     │    │
│  │  │ 802.11ac    80 MHz      4         1.73 Gbps      800 Mbps │     │    │
│  │  │ 802.11ac    160 MHz     4         3.47 Gbps      1.5 Gbps │     │    │
│  │  │ 802.11ac    160 MHz     8         6.93 Gbps      3 Gbps   │     │    │
│  │  │ 802.11ax    80 MHz      1         600 Mbps       300 Mbps │     │    │
│  │  │ 802.11ax    80 MHz      4         2.4 Gbps       1.2 Gbps │     │    │
│  │  │ 802.11ax    160 MHz     4         4.8 Gbps       2.4 Gbps │     │    │
│  │  │ 802.11ax    160 MHz     8         9.6 Gbps       4.8 Gbps │     │    │
│  │  │ 802.11be    160 MHz     8         11.5 Gbps      5.5 Gbps │     │    │
│  │  │ 802.11be    320 MHz     8         23 Gbps        11 Gbps  │     │    │
│  │  │ 802.11be    320 MHz     16        46 Gbps        22 Gbps  │     │    │
│  │  └────────────────────────────────────────────────────────────┘     │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  MCS Rate Tables (802.11ax):                                                 │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  20 MHz, 1 Spatial Stream:                                           │    │
│  │  ┌────────────────────────────────────────────────────────────┐     │    │
│  │  │ MCS   Modulation   Coding   GI=0.8μs   GI=1.6μs   GI=3.2μs │     │    │
│  │  │ ───   ──────────   ──────   ────────   ────────   ──────── │     │    │
│  │  │  0    BPSK         1/2      8.6        8.1        7.3      │     │    │
│  │  │  1    QPSK         1/2      17.2       16.3       14.6     │     │    │
│  │  │  2    QPSK         3/4      25.8       24.4       21.9     │     │    │
│  │  │  3    16-QAM       1/2      34.4       32.5       29.3     │     │    │
│  │  │  4    16-QAM       3/4      51.6       48.8       43.9     │     │    │
│  │  │  5    64-QAM       2/3      68.8       65.0       58.5     │     │    │
│  │  │  6    64-QAM       3/4      77.4       73.1       65.8     │     │    │
│  │  │  7    64-QAM       5/6      86.0       81.3       73.1     │     │    │
│  │  │  8    256-QAM      3/4      103.2      97.5       87.8     │     │    │
│  │  │  9    256-QAM      5/6      114.7      108.3      97.5     │     │    │
│  │  │ 10    1024-QAM     3/4      129.0      121.9      109.7    │     │    │
│  │  │ 11    1024-QAM     5/6      143.4      135.4      121.9    │     │    │
│  │  └────────────────────────────────────────────────────────────┘     │    │
│  │                                                                      │    │
│  │  80 MHz, 1 Spatial Stream:                                           │    │
│  │  ┌────────────────────────────────────────────────────────────┐     │    │
│  │  │ MCS   Modulation   Coding   GI=0.8μs   GI=1.6μs   GI=3.2μs │     │    │
│  │  │ ───   ──────────   ──────   ────────   ────────   ──────── │     │    │
│  │  │  0    BPSK         1/2      36.0       34.0       30.6     │     │    │
│  │  │  1    QPSK         1/2      72.1       68.1       61.3     │     │    │
│  │  │  2    QPSK         3/4      108.1      102.1      91.9     │     │    │
│  │  │  3    16-QAM       1/2      144.1      136.1      122.5    │     │    │
│  │  │  4    16-QAM       3/4      216.2      204.2      183.8    │     │    │
│  │  │  5    64-QAM       2/3      288.2      272.2      245.0    │     │    │
│  │  │  6    64-QAM       3/4      324.3      306.3      275.6    │     │    │
│  │  │  7    64-QAM       5/6      360.3      340.3      306.3    │     │    │
│  │  │  8    256-QAM      3/4      432.4      408.3      367.5    │     │    │
│  │  │  9    256-QAM      5/6      480.4      453.7      408.3    │     │    │
│  │  │ 10    1024-QAM     3/4      540.4      510.4      459.4    │     │    │
│  │  │ 11    1024-QAM     5/6      600.5      567.1      510.4    │     │    │
│  │  └────────────────────────────────────────────────────────────┘     │    │
│  │                                                                      │    │
│  │  160 MHz, 1 Spatial Stream:                                          │    │
│  │  ┌────────────────────────────────────────────────────────────┐     │    │
│  │  │ MCS   Modulation   Coding   GI=0.8μs   GI=1.6μs   GI=3.2μs │     │    │
│  │  │ ───   ──────────   ──────   ────────   ────────   ──────── │     │    │
│  │  │  0    BPSK         1/2      72.1       68.1       61.3     │     │    │
│  │  │  1    QPSK         1/2      144.1      136.1      122.5    │     │    │
│  │  │  2    QPSK         3/4      216.2      204.2      183.8    │     │    │
│  │  │  3    16-QAM       1/2      288.2      272.2      245.0    │     │    │
│  │  │  4    16-QAM       3/4      432.4      408.3      367.5    │     │    │
│  │  │  5    64-QAM       2/3      576.5      544.4      490.0    │     │    │
│  │  │  6    64-QAM       3/4      648.5      612.5      551.3    │     │    │
│  │  │  7    64-QAM       5/6      720.6      680.6      612.5    │     │    │
│  │  │  8    256-QAM      3/4      864.7      816.7      735.0    │     │    │
│  │  │  9    256-QAM      5/6      960.8      907.4      816.7    │     │    │
│  │  │ 10    1024-QAM     3/4      1080.9     1020.8     918.8    │     │    │
│  │  │ 11    1024-QAM     5/6      1201.0     1134.3     1020.8   │     │    │
│  │  └────────────────────────────────────────────────────────────┘     │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### AO.2 Roaming Time Benchmarks

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    ROAMING TIME BENCHMARKS                                   │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  Roaming Methods Comparison:                                                 │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  ┌────────────────────────────────────────────────────────────┐     │    │
│  │  │ Method                    Typical Time   Best Case   Notes │     │    │
│  │  │ ──────                    ────────────   ─────────   ───── │     │    │
│  │  │ Full Reauthentication     500-2000 ms    300 ms      EAP   │     │    │
│  │  │ PMKSA Caching             100-300 ms     50 ms       PMK   │     │    │
│  │  │ OKC                       100-300 ms     50 ms       PMK   │     │    │
│  │  │ 802.11r Over-the-Air      30-100 ms      20 ms       FT    │     │    │
│  │  │ 802.11r Over-the-DS       20-80 ms       15 ms       FT    │     │    │
│  │  │ FILS                      20-50 ms       10 ms       Fast  │     │    │
│  │  │ 802.11be MLO              <10 ms         <5 ms       Zero  │     │    │
│  │  └────────────────────────────────────────────────────────────┘     │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  Roaming Time Breakdown:                                                     │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  Full Reauthentication (WPA2-Enterprise):                            │    │
│  │  ┌────────────────────────────────────────────────────────────┐     │    │
│  │  │ Phase                     Time          Cumulative         │     │    │
│  │  │ ─────                     ────          ──────────         │     │    │
│  │  │ Scanning                  100-500 ms    100-500 ms         │     │    │
│  │  │ Authentication            1-5 ms        101-505 ms         │     │    │
│  │  │ Association               1-5 ms        102-510 ms         │     │    │
│  │  │ EAP Identity              10-50 ms      112-560 ms         │     │    │
│  │  │ EAP Method (TLS/TTLS)     200-1000 ms   312-1560 ms        │     │    │
│  │  │ 4-Way Handshake           10-50 ms      322-1610 ms        │     │    │
│  │  │ DHCP (if needed)          100-500 ms    422-2110 ms        │     │    │
│  │  │ ─────────────────────────────────────────────────────────  │     │    │
│  │  │ Total                     422-2110 ms                      │     │    │
│  │  └────────────────────────────────────────────────────────────┘     │    │
│  │                                                                      │    │
│  │  802.11r Fast Transition (Over-the-Air):                             │    │
│  │  ┌────────────────────────────────────────────────────────────┐     │    │
│  │  │ Phase                     Time          Cumulative         │     │    │
│  │  │ ─────                     ────          ──────────         │     │    │
│  │  │ Scanning                  10-50 ms      10-50 ms           │     │    │
│  │  │ FT Authentication         5-20 ms       15-70 ms           │     │    │
│  │  │ FT Reassociation          5-20 ms       20-90 ms           │     │    │
│  │  │ ─────────────────────────────────────────────────────────  │     │    │
│  │  │ Total                     20-90 ms                         │     │    │
│  │  └────────────────────────────────────────────────────────────┘     │    │
│  │                                                                      │    │
│  │  802.11r Fast Transition (Over-the-DS):                              │    │
│  │  ┌────────────────────────────────────────────────────────────┐     │    │
│  │  │ Phase                     Time          Cumulative         │     │    │
│  │  │ ─────                     ────          ──────────         │     │    │
│  │  │ FT Request (via DS)       5-15 ms       5-15 ms            │     │    │
│  │  │ FT Response (via DS)      5-15 ms       10-30 ms           │     │    │
│  │  │ Channel Switch            5-20 ms       15-50 ms           │     │    │
│  │  │ FT Reassociation          5-20 ms       20-70 ms           │     │    │
│  │  │ ─────────────────────────────────────────────────────────  │     │    │
│  │  │ Total                     20-70 ms                         │     │    │
│  │  └────────────────────────────────────────────────────────────┘     │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  VoIP Quality Requirements:                                                  │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  ┌────────────────────────────────────────────────────────────┐     │    │
│  │  │ Metric                    Requirement   Impact              │     │    │
│  │  │ ──────                    ───────────   ──────              │     │    │
│  │  │ Roaming Time              <50 ms        No audible gap      │     │    │
│  │  │ Packet Loss               <1%           Clear audio         │     │    │
│  │  │ Jitter                    <30 ms        Smooth audio        │     │    │
│  │  │ Latency                   <150 ms       Natural conversation│     │    │
│  │  └────────────────────────────────────────────────────────────┘     │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### AO.3 Latency Benchmarks

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    LATENCY BENCHMARKS                                        │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  WiFi Latency by Generation:                                                 │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  ┌────────────────────────────────────────────────────────────┐     │    │
│  │  │ Standard    Typical RTT   Best Case   Worst Case   Notes  │     │    │
│  │  │ ────────    ───────────   ─────────   ──────────   ─────  │     │    │
│  │  │ 802.11b     10-50 ms      5 ms        100+ ms      Legacy │     │    │
│  │  │ 802.11a/g   5-30 ms       2 ms        50+ ms       OFDM   │     │    │
│  │  │ 802.11n     3-20 ms       1 ms        30+ ms       HT     │     │    │
│  │  │ 802.11ac    2-15 ms       <1 ms       20+ ms       VHT    │     │    │
│  │  │ 802.11ax    1-10 ms       <1 ms       15+ ms       HE     │     │    │
│  │  │ 802.11be    <5 ms         <0.5 ms     10+ ms       EHT    │     │    │
│  │  └────────────────────────────────────────────────────────────┘     │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  Latency Components:                                                         │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  ┌────────────────────────────────────────────────────────────┐     │    │
│  │  │ Component               Typical Time   Notes                │     │    │
│  │  │ ─────────               ────────────   ─────                │     │    │
│  │  │ Channel Access (CSMA)   0.1-5 ms       Contention-based     │     │    │
│  │  │ Frame Transmission      0.01-1 ms      Depends on rate      │     │    │
│  │  │ ACK Wait                0.01-0.1 ms    SIFS + ACK           │     │    │
│  │  │ Retransmission          5-50 ms        If needed            │     │    │
│  │  │ Power Save Wake         1-10 ms        DTIM interval        │     │    │
│  │  │ AP Processing           0.1-1 ms       Software overhead    │     │    │
│  │  │ Bridge/Switch           0.01-0.1 ms    L2 forwarding        │     │    │
│  │  └────────────────────────────────────────────────────────────┘     │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  Application Latency Requirements:                                           │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  ┌────────────────────────────────────────────────────────────┐     │    │
│  │  │ Application             Max Latency   Jitter   Loss        │     │    │
│  │  │ ───────────             ───────────   ──────   ────        │     │    │
│  │  │ VoIP                    150 ms        30 ms    1%          │     │    │
│  │  │ Video Conferencing      200 ms        50 ms    1%          │     │    │
│  │  │ Online Gaming           50 ms         10 ms    0.1%        │     │    │
│  │  │ VR/AR                   20 ms         5 ms     0.01%       │     │    │
│  │  │ Industrial IoT          10 ms         1 ms     0.001%      │     │    │
│  │  │ Web Browsing            500 ms        N/A      5%          │     │    │
│  │  │ Video Streaming         2000 ms       N/A      0.1%        │     │    │
│  │  │ File Transfer           N/A           N/A      0.01%       │     │    │
│  │  └────────────────────────────────────────────────────────────┘     │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Appendix AP: Client Device Compatibility Matrix

### AP.1 Operating System WiFi Capabilities

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    OS WIFI CAPABILITIES                                      │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  Windows:                                                                    │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  ┌────────────────────────────────────────────────────────────┐     │    │
│  │  │ Version     WPA3   802.11r  802.11k  802.11v  OWE   FILS   │     │    │
│  │  │ ───────     ────   ───────  ───────  ───────  ───   ────   │     │    │
│  │  │ Windows 7   No     No       No       No       No    No     │     │    │
│  │  │ Windows 8   No     Yes*     No       No       No    No     │     │    │
│  │  │ Windows 8.1 No     Yes*     No       No       No    No     │     │    │
│  │  │ Windows 10  Yes**  Yes      Yes      Yes      Yes** No     │     │    │
│  │  │ Windows 11  Yes    Yes      Yes      Yes      Yes   Yes*** │     │    │
│  │  └────────────────────────────────────────────────────────────┘     │    │
│  │                                                                      │    │
│  │  * Requires driver support                                           │    │
│  │  ** Requires version 1903 or later                                   │    │
│  │  *** Requires version 22H2 or later                                  │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  macOS:                                                                      │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  ┌────────────────────────────────────────────────────────────┐     │    │
│  │  │ Version       WPA3   802.11r  802.11k  802.11v  OWE   FILS │     │    │
│  │  │ ───────       ────   ───────  ───────  ───────  ───   ──── │     │    │
│  │  │ macOS 10.14   No     Yes      Yes      Yes      No    No   │     │    │
│  │  │ macOS 10.15   Yes    Yes      Yes      Yes      Yes   No   │     │    │
│  │  │ macOS 11      Yes    Yes      Yes      Yes      Yes   No   │     │    │
│  │  │ macOS 12      Yes    Yes      Yes      Yes      Yes   Yes  │     │    │
│  │  │ macOS 13      Yes    Yes      Yes      Yes      Yes   Yes  │     │    │
│  │  │ macOS 14      Yes    Yes      Yes      Yes      Yes   Yes  │     │    │
│  │  └────────────────────────────────────────────────────────────┘     │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  iOS/iPadOS:                                                                 │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  ┌────────────────────────────────────────────────────────────┐     │    │
│  │  │ Version   WPA3   802.11r  802.11k  802.11v  OWE   FILS     │     │    │
│  │  │ ───────   ────   ───────  ───────  ───────  ───   ────     │     │    │
│  │  │ iOS 12    No     Yes      Yes      Yes      No    No       │     │    │
│  │  │ iOS 13    Yes    Yes      Yes      Yes      Yes   No       │     │    │
│  │  │ iOS 14    Yes    Yes      Yes      Yes      Yes   Yes      │     │    │
│  │  │ iOS 15    Yes    Yes      Yes      Yes      Yes   Yes      │     │    │
│  │  │ iOS 16    Yes    Yes      Yes      Yes      Yes   Yes      │     │    │
│  │  │ iOS 17    Yes    Yes      Yes      Yes      Yes   Yes      │     │    │
│  │  └────────────────────────────────────────────────────────────┘     │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  Android:                                                                    │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  ┌────────────────────────────────────────────────────────────┐     │    │
│  │  │ Version     WPA3   802.11r  802.11k  802.11v  OWE   FILS   │     │    │
│  │  │ ───────     ────   ───────  ───────  ───────  ───   ────   │     │    │
│  │  │ Android 8   No     Yes*     Yes*     Yes*     No    No     │     │    │
│  │  │ Android 9   No     Yes*     Yes*     Yes*     No    No     │     │    │
│  │  │ Android 10  Yes    Yes      Yes      Yes      Yes   No     │     │    │
│  │  │ Android 11  Yes    Yes      Yes      Yes      Yes   Yes*   │     │    │
│  │  │ Android 12  Yes    Yes      Yes      Yes      Yes   Yes    │     │    │
│  │  │ Android 13  Yes    Yes      Yes      Yes      Yes   Yes    │     │    │
│  │  │ Android 14  Yes    Yes      Yes      Yes      Yes   Yes    │     │    │
│  │  └────────────────────────────────────────────────────────────┘     │    │
│  │                                                                      │    │
│  │  * Depends on device manufacturer and chipset                        │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  Linux:                                                                      │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  ┌────────────────────────────────────────────────────────────┐     │    │
│  │  │ Component         WPA3   802.11r  802.11k  802.11v  OWE    │     │    │
│  │  │ ─────────         ────   ───────  ───────  ───────  ───    │     │    │
│  │  │ wpa_supplicant    Yes*   Yes      Yes      Yes      Yes*   │     │    │
│  │  │ NetworkManager    Yes**  Yes      Yes      Yes      Yes**  │     │    │
│  │  │ iwd               Yes    Yes      Yes      Yes      Yes    │     │    │
│  │  └────────────────────────────────────────────────────────────┘     │    │
│  │                                                                      │    │
│  │  * Requires version 2.9 or later                                     │    │
│  │  ** Requires version 1.20 or later                                   │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### AP.2 EAP Method Support by Platform

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    EAP METHOD SUPPORT BY PLATFORM                            │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  ┌────────────────────────────────────────────────────────────┐     │    │
│  │  │ EAP Method    Windows  macOS  iOS  Android  Linux  ChromeOS│     │    │
│  │  │ ──────────    ───────  ─────  ───  ───────  ─────  ────────│     │    │
│  │  │ EAP-TLS       Yes      Yes    Yes  Yes      Yes    Yes     │     │    │
│  │  │ EAP-TTLS      Yes      Yes    Yes  Yes      Yes    Yes     │     │    │
│  │  │ EAP-PEAP      Yes      Yes    Yes  Yes      Yes    Yes     │     │    │
│  │  │ EAP-FAST      Yes*     No     No   Yes*     Yes    No      │     │    │
│  │  │ EAP-SIM       Yes**    Yes    Yes  Yes      Yes    Yes     │     │    │
│  │  │ EAP-AKA       Yes**    Yes    Yes  Yes      Yes    Yes     │     │    │
│  │  │ EAP-AKA'      Yes**    Yes    Yes  Yes      Yes    Yes     │     │    │
│  │  │ EAP-PWD       No       No     No   Yes***   Yes    No      │     │    │
│  │  │ EAP-TEAP      Yes****  No     No   No       Yes    No      │     │    │
│  │  └────────────────────────────────────────────────────────────┘     │    │
│  │                                                                      │    │
│  │  * Requires Cisco AnyConnect or compatible supplicant                │    │
│  │  ** Requires SIM card and carrier support                            │    │
e
│  │  *** Requires Android 10 or later                                    │    │
│  │  **** Requires Windows 10 version 2004 or later                      │    │
