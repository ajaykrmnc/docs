## Appendix AH: Debugging and Logging

### AH.1 hostapd Debug Levels

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    HOSTAPD DEBUG LEVELS                                      │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  Debug Level Configuration:                                                  │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  # In hostapd.conf:                                                  │    │
│  │  logger_syslog=-1          # Log all modules to syslog              │    │
│  │  logger_syslog_level=2     # Log level for syslog                   │    │
│  │  logger_stdout=-1          # Log all modules to stdout              │    │
│  │  logger_stdout_level=2     # Log level for stdout                   │    │
│  │                                                                      │    │
│  │  Log Levels:                                                         │    │
│  │  ┌────────────────────────────────────────────────────────────┐     │    │
│  │  │ Level   Name        Description                            │     │    │
│  │  │ ─────   ────        ───────────                            │     │    │
│  │  │   0     EXCESSIVE   Extremely verbose (all messages)       │     │    │
│  │  │   1     MSGDUMP     Message dumps (frame contents)         │     │    │
│  │  │   2     DEBUG       Debug messages                         │     │    │
│  │  │   3     INFO        Informational messages                 │     │    │
│  │  │   4     WARNING     Warning messages                       │     │    │
│  │  │   5     ERROR       Error messages only                    │     │    │
│  │  └────────────────────────────────────────────────────────────┘     │     │
│  │                                                                      │    │
│  │  Log Modules (bitmask for logger_syslog/logger_stdout):             │    │
│  │  ┌────────────────────────────────────────────────────────────┐     │    │
│  │  │ Bit   Module                                               │     │    │
│  │  │ ───   ──────                                               │     │    │
│  │  │  0    IEEE 802.11                                          │     │    │
│  │  │  1    IEEE 802.1X                                          │     │    │
│  │  │  2    RADIUS                                               │     │    │
│  │  │  3    WPA                                                  │     │    │
│  │  │  4    Driver interface                                     │     │    │
│  │  │  5    IAPP                                                 │     │    │
│  │  │  6    MLME                                                 │     │    │
│  │  │ -1    All modules                                          │     │    │
│  │  └────────────────────────────────────────────────────────────┘     │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  Command Line Debug Options:                                                 │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  hostapd -d              # Debug level 1                            │    │
│  │  hostapd -dd             # Debug level 2 (more verbose)             │    │
│  │  hostapd -ddd            # Debug level 3 (very verbose)             │    │
│  │  hostapd -dddd           # Debug level 4 (extremely verbose)        │    │
│  │  hostapd -t              # Include timestamps                       │    │
│  │  hostapd -K              # Include key data in debug                │    │
│  │  hostapd -f /var/log/hostapd.log  # Log to file                     │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### AH.2 Common Log Messages

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    COMMON HOSTAPD LOG MESSAGES                               │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  Successful Connection:                                                      │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  wlan0: STA aa:bb:cc:dd:ee:ff IEEE 802.11: authenticated            │    │
│  │  wlan0: STA aa:bb:cc:dd:ee:ff IEEE 802.11: associated (aid 1)       │    │
│  │  wlan0: STA aa:bb:cc:dd:ee:ff RADIUS: starting accounting session   │    │
│  │  wlan0: STA aa:bb:cc:dd:ee:ff IEEE 802.1X: authorizing port         │    │
│  │  wlan0: STA aa:bb:cc:dd:ee:ff WPA: pairwise key handshake completed │    │
│  │  wlan0: STA aa:bb:cc:dd:ee:ff WPA: group key handshake completed    │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  Authentication Failure:                                                     │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  wlan0: STA aa:bb:cc:dd:ee:ff IEEE 802.1X: authentication failed    │    │
│  │  wlan0: STA aa:bb:cc:dd:ee:ff RADIUS: Access-Reject received        │    │
│  │  wlan0: STA aa:bb:cc:dd:ee:ff IEEE 802.11: deauthenticated (reason=23)│   │
│  │                                                                      │    │
│  │  Reason 23 = IEEE_802_1X_AUTH_FAILED                                │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  4-Way Handshake Failure:                                                    │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  wlan0: STA aa:bb:cc:dd:ee:ff WPA: received EAPOL-Key msg 2/4       │    │
│  │  wlan0: STA aa:bb:cc:dd:ee:ff WPA: invalid MIC in msg 2/4           │    │
│  │  wlan0: STA aa:bb:cc:dd:ee:ff WPA: 4-Way Handshake failed           │    │
│  │  wlan0: STA aa:bb:cc:dd:ee:ff IEEE 802.11: deauthenticated (reason=15)│   │
│  │                                                                      │    │
│  │  Reason 15 = 4WAY_HANDSHAKE_TIMEOUT                                 │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  RADIUS Timeout:                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  wlan0: STA aa:bb:cc:dd:ee:ff RADIUS: No response from server       │    │
│  │  wlan0: STA aa:bb:cc:dd:ee:ff RADIUS: Retransmitting message        │    │
│  │  wlan0: STA aa:bb:cc:dd:ee:ff RADIUS: Authentication timed out      │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  DFS Events:                                                                 │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  wlan0: DFS-CAC-START freq=5260 chan=52 sec_chan=1                  │    │
│  │  wlan0: DFS-CAC-COMPLETED success=1 freq=5260                       │    │
│  │  wlan0: DFS-RADAR-DETECTED freq=5260                                │    │
│  │  wlan0: DFS-NEW-CHANNEL freq=5180 chan=36                           │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  Channel Switch:                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  wlan0: CTRL-EVENT-STARTED-CHANNEL-SWITCH freq=5180 ht_enabled=1    │    │
│  │  wlan0: CTRL-EVENT-CHANNEL-SWITCH freq=5180 ht_enabled=1            │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### AH.3 Packet Capture Commands

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    PACKET CAPTURE COMMANDS                                   │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  tcpdump Commands:                                                           │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  # Capture all WiFi frames on monitor interface                     │    │
│  │  tcpdump -i wlan0mon -w capture.pcap                                │    │
│  │                                                                      │    │
│  │  # Capture EAPOL frames only                                        │    │
│  │  tcpdump -i wlan0 'ether proto 0x888e' -w eapol.pcap                │    │
│  │                                                                      │    │
│  │  # Capture RADIUS traffic                                           │    │
│  │  tcpdump -i eth0 'port 1812 or port 1813' -w radius.pcap            │    │
│  │                                                                      │    │
│  │  # Capture DHCP traffic                                             │    │
│  │  tcpdump -i br0 'port 67 or port 68' -w dhcp.pcap                   │    │
│  │                                                                      │    │
│  │  # Capture specific client traffic                                  │    │
│  │  tcpdump -i wlan0 'ether host aa:bb:cc:dd:ee:ff' -w client.pcap     │    │
│  │                                                                      │    │
│  │  # Capture management frames only                                   │    │
│  │  tcpdump -i wlan0mon 'type mgt' -w mgmt.pcap                        │    │
│  │                                                                      │    │
│  │  # Capture beacon frames                                            │    │
│  │  tcpdump -i wlan0mon 'type mgt subtype beacon' -w beacons.pcap      │    │
│  │                                                                      │    │
│  │  # Capture probe requests/responses                                 │    │
│  │  tcpdump -i wlan0mon 'type mgt subtype probe-req or                 │    │
│  │                       type mgt subtype probe-resp' -w probes.pcap   │    │
│  │                                                                      │    │
│  │  # Capture authentication frames                                    │    │
│  │  tcpdump -i wlan0mon 'type mgt subtype auth' -w auth.pcap           │    │
│  │                                                                      │    │
│  │  # Capture association frames                                       │    │
│  │  tcpdump -i wlan0mon 'type mgt subtype assoc-req or                 │    │
│  │                       type mgt subtype assoc-resp' -w assoc.pcap    │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  tshark Commands:                                                            │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  # Decode EAPOL frames                                              │    │
│  │  tshark -r capture.pcap -Y 'eapol' -V                               │    │
│  │                                                                      │    │
│  │  # Show 4-way handshake                                             │    │
│  │  tshark -r capture.pcap -Y 'eapol.keydes.type == 2'                 │    │
│  │                                                                      │    │
│  │  # Decode RADIUS packets                                            │    │
│  │  tshark -r radius.pcap -Y 'radius' -V                               │    │
│  │                                                                      │    │
│  │  # Show EAP exchanges                                               │    │
│  │  tshark -r capture.pcap -Y 'eap' -V                                 │    │
│  │                                                                      │    │
│  │  # Extract RSN IE from beacons                                      │    │
│  │  tshark -r capture.pcap -Y 'wlan.fc.type_subtype == 8' \            │    │
│  │         -T fields -e wlan.rsn.akms.type                             │    │
│  │                                                                      │    │
│  │  # Show association request/response                                │    │
│  │  tshark -r capture.pcap -Y 'wlan.fc.type_subtype == 0 or            │    │
│  │                             wlan.fc.type_subtype == 1' -V           │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  Monitor Mode Setup:                                                         │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  # Create monitor interface                                         │    │
│  │  iw phy phy0 interface add wlan0mon type monitor                    │    │
│  │  ip link set wlan0mon up                                            │    │
│  │                                                                      │    │
│  │  # Set channel for capture                                          │    │
│  │  iw dev wlan0mon set channel 36 HT40+                               │    │
│  │                                                                      │    │
│  │  # Or use airmon-ng                                                 │    │
│  │  airmon-ng start wlan0                                              │    │
│  │  airmon-ng start wlan0 36                                           │    │
│  │                                                                      │    │
│  │  # Remove monitor interface                                         │    │
│  │  iw dev wlan0mon del                                                │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

