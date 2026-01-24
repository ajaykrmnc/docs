## Appendix K: Packet Capture Analysis

### K.1 Capturing WiFi Traffic

```bash
# Enable monitor mode
sudo ip link set wlan0 down
sudo iw dev wlan0 set type monitor
sudo ip link set wlan0 up

# Set channel
sudo iw dev wlan0 set channel 36

# Capture with tcpdump
sudo tcpdump -i wlan0 -w capture.pcap

# Capture with tshark (Wireshark CLI)
sudo tshark -i wlan0 -w capture.pcap

# Capture specific frame types
sudo tcpdump -i wlan0 'type mgt' -w mgmt_frames.pcap
sudo tcpdump -i wlan0 'type mgt subtype beacon' -w beacons.pcap
sudo tcpdump -i wlan0 'type mgt subtype probe-req' -w probes.pcap
sudo tcpdump -i wlan0 'ether proto 0x888e' -w eapol.pcap
```

### K.2 Wireshark Display Filters

```
# Beacon frames
wlan.fc.type_subtype == 0x08

# Probe Request
wlan.fc.type_subtype == 0x04

# Probe Response
wlan.fc.type_subtype == 0x05

# Authentication
wlan.fc.type_subtype == 0x0b

# Association Request
wlan.fc.type_subtype == 0x00

# Association Response
wlan.fc.type_subtype == 0x01

# Reassociation Request
wlan.fc.type_subtype == 0x02

# Reassociation Response
wlan.fc.type_subtype == 0x03

# Deauthentication
wlan.fc.type_subtype == 0x0c

# Disassociation
wlan.fc.type_subtype == 0x0a

# Action frames
wlan.fc.type_subtype == 0x0d

# EAPOL frames
eapol

# 4-Way Handshake Message 1
eapol.keydes.key_info == 0x008a

# 4-Way Handshake Message 2
eapol.keydes.key_info == 0x010a

# 4-Way Handshake Message 3
eapol.keydes.key_info == 0x13ca

# 4-Way Handshake Message 4
eapol.keydes.key_info == 0x030a

# DHCP
bootp

# Specific SSID
wlan.ssid == "MyNetwork"

# Specific MAC address
wlan.addr == 00:11:22:33:44:55

# RSN Information Element
wlan.rsn.version

# Hotspot 2.0
wlan.hs20.indication

# GAS frames
wlan.fixed.action_code == 10 || wlan.fixed.action_code == 11
```

### K.3 Sample Packet Decode

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    SAMPLE BEACON FRAME DECODE                                │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  Frame 1: 256 bytes on wire                                                  │
│  IEEE 802.11 Beacon frame                                                    │
│      Type/Subtype: Beacon frame (0x0008)                                     │
│      Frame Control Field: 0x8000                                             │
│          .... ..00 = Protocol Version: 0                                     │
│          .... 00.. = Type: Management frame (0)                              │
│          1000 .... = Subtype: 8                                              │
│      Duration: 0                                                             │
│      Receiver address: ff:ff:ff:ff:ff:ff (Broadcast)                         │
│      Transmitter address: 00:11:22:33:44:55                                  │
│      BSS Id: 00:11:22:33:44:55                                               │
│      Fragment number: 0                                                      │
│      Sequence number: 1234                                                   │
│                                                                              │
│  IEEE 802.11 Wireless Management                                             │
│      Fixed parameters (12 bytes)                                             │
│          Timestamp: 0x0000000012345678                                       │
│          Beacon Interval: 0.102400 [Seconds]                                 │
│          Capabilities Information: 0x0431                                    │
│              .... .... .... ...1 = ESS capabilities: Transmitter is AP      │
│              .... .... .... ..0. = IBSS status: Not IBSS                     │
│              .... .... ...1 .... = Privacy: AP requires encryption          │
│              .... .... ..1. .... = Short Preamble: Allowed                   │
│              .... .1.. .... .... = Short Slot Time: In use                   │
│                                                                              │
│      Tagged parameters (244 bytes)                                           │
│          Tag: SSID parameter set                                             │
│              Tag Number: SSID parameter set (0)                              │
│              Tag length: 10                                                  │
│              SSID: MyHotspot                                                 │
│                                                                              │
│          Tag: Supported Rates                                                │
│              Tag Number: Supported Rates (1)                                 │
│              Tag length: 8                                                   │
│              Supported Rates: 6(B), 9, 12(B), 18, 24(B), 36, 48, 54          │
│                                                                              │
│          Tag: DS Parameter set                                               │
│              Tag Number: DS Parameter set (3)                                │
│              Tag length: 1                                                   │
│              Current Channel: 36                                             │
│                                                                              │
│          Tag: RSN Information                                                │
│              Tag Number: RSN Information (48)                                │
│              Tag length: 20                                                  │
│              RSN Version: 1                                                  │
│              Group Cipher Suite: 00-0f-ac (Ieee 802.11) CCMP-128             │
│              Pairwise Cipher Suite Count: 1                                  │
│              Pairwise Cipher Suite: 00-0f-ac (Ieee 802.11) CCMP-128          │
│              Auth Key Management Suite Count: 1                              │
│              Auth Key Management Suite: 00-0f-ac (Ieee 802.11) SAE           │
│              RSN Capabilities: 0x00cc                                        │
│                  .... .... .... ..00 = RSN Pre-Auth: Not supported           │
│                  .... .... ..11 .... = PTKSA Replay Counter: 16              │
│                  .... .... 11.. .... = GTKSA Replay Counter: 16              │
│                  .... ...1 .... .... = Management Frame Protection Req: Yes │
│                  .... ..1. .... .... = Management Frame Protection Cap: Yes │
│                                                                              │
│          Tag: HT Capabilities                                                │
│          Tag: HT Information                                                 │
│          Tag: VHT Capabilities                                               │
│          Tag: VHT Operation                                                  │
│          Tag: HE Capabilities                                                │
│          Tag: HE Operation                                                   │
│          Tag: Vendor Specific: Microsoft Corp.: WMM/WME                      │
│          Tag: Vendor Specific: WiFi Alliance: Hotspot 2.0 Indication         │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### K.4 Sample EAPOL Decode

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    SAMPLE EAPOL-KEY MESSAGE 1 DECODE                         │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  Frame 100: 121 bytes on wire                                                │
│  IEEE 802.11 QoS Data                                                        │
│      Type/Subtype: QoS Data (0x0028)                                         │
│      Receiver address: aa:bb:cc:dd:ee:ff (Client)                            │
│      Transmitter address: 00:11:22:33:44:55 (AP)                             │
│                                                                              │
│  Logical-Link Control                                                        │
│      DSAP: SNAP (0xaa)                                                       │
│      SSAP: SNAP (0xaa)                                                       │
│      Control field: U, func=UI (0x03)                                        │
│      Type: 802.1X Authentication (0x888e)                                    │
│                                                                              │
│  802.1X Authentication                                                       │
│      Version: 802.1X-2004 (2)                                                │
│      Type: Key (3)                                                           │
│      Length: 95                                                              │
│                                                                              │
│  802.1X Key                                                                  │
│      Key Descriptor Type: EAPOL RSN Key (2)                                  │
│      Key Information: 0x008a                                                 │
│          .... .... .... .010 = Key Descriptor Version: AES-128-CMAC (2)      │
│          .... .... .... 1... = Key Type: Pairwise key                        │
│          .... .... ..00 .... = Key Index: 0                                  │
│          .... .... .0.. .... = Install: Not set                              │
│          .... .... 1... .... = Key ACK: Set                                  │
│          .... ...0 .... .... = Key MIC: Not set                              │
│          .... ..0. .... .... = Secure: Not set                               │
│          .... .0.. .... .... = Error: Not set                                │
│          .... 0... .... .... = Request: Not set                              │
│          ...0 .... .... .... = Encrypted Key Data: Not set                   │
│      Key Length: 16                                                          │
│      Replay Counter: 1                                                       │
│      WPA Key Nonce: 1234567890abcdef... (ANonce)                             │
│      Key IV: 00000000000000000000000000000000                                │
│      WPA Key RSC: 0000000000000000                                           │
│      WPA Key ID: 0000000000000000                                            │
│      WPA Key MIC: 00000000000000000000000000000000                           │
│      WPA Key Data Length: 22                                                 │
│      WPA Key Data: PMKID KDE                                                 │
│          Type: Vendor Specific (221)                                         │
│          Length: 20                                                          │
│          OUI: 00-0f-ac (IEEE 802.11)                                         │
│          Type: PMKID (4)                                                     │
│          PMKID: abcdef1234567890...                                          │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

