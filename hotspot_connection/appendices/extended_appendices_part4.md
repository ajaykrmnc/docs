│  │  │ Duplicate IP            Pool exhausted          Expand pool│     │    │
│  │  │ Slow DHCP               Relay issue             Check relay│     │    │
│  │  └────────────────────────────────────────────────────────────┘     │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### DE.2 Performance Issues

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    PERFORMANCE TROUBLESHOOTING                               │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  Slow Throughput:                                                            │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  ┌────────────────────────────────────────────────────────────┐     │    │
│  │  │ Cause                   Diagnosis               Solution   │     │    │
│  │  │ ─────                   ─────────               ────────   │     │    │
│  │  │ Weak signal             Check RSSI              Move closer│     │    │
│  │  │ Interference            Check channel util      Change ch  │     │    │
│  │  │ Too many clients        Check client count      Add APs    │     │    │
│  │  │ Legacy clients          Check data rates        Disable 11b│     │    │
│  │  │ Rate limiting           Check policy            Adjust     │     │    │
│  │  │ Backhaul congestion     Check uplink            Upgrade    │     │    │
│  │  └────────────────────────────────────────────────────────────┘     │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  High Latency:                                                               │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  ┌────────────────────────────────────────────────────────────┐     │    │
│  │  │ Cause                   Diagnosis               Solution   │     │    │
│  │  │ ─────                   ─────────               ────────   │     │    │
│  │  │ Retransmissions         Check retry rate        Improve RF │     │    │
│  │  │ Bufferbloat             Check queue depth       Enable AQM │     │    │
│  │  │ Power save              Check PS mode           Disable PS │     │    │
│  │  │ Roaming                 Check roam time         Enable FT  │     │    │
│  │  │ DNS issues              Check DNS latency       Local DNS  │     │    │
│  │  └────────────────────────────────────────────────────────────┘     │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  Frequent Disconnections:                                                    │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  ┌────────────────────────────────────────────────────────────┐     │    │
│  │  │ Cause                   Diagnosis               Solution   │     │    │
│  │  │ ─────                   ─────────               ────────   │     │    │
│  │  │ Roaming issues          Check roam logs         Tune roam  │     │    │
│  │  │ Deauth attacks          Check security logs     Enable PMF │     │    │
│  │  │ AP overload             Check client count      Load bal   │     │    │
│  │  │ Driver bugs             Check client driver     Update     │     │    │
│  │  │ Inactivity timeout      Check idle timeout      Increase   │     │    │
│  │  │ Key rotation            Check GTK rekey         Adjust     │     │    │
│  │  └────────────────────────────────────────────────────────────┘     │    │
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
| 3.1 | 2026-01-08 | Auto-generated | Added WiFi 7 MLO, puncturing, 4K-QAM, multi-RU, enhanced security |
| 3.2 | 2026-01-08 | Auto-generated | Added FILS, DPP, enterprise security, certificate management |
| 3.3 | 2026-01-08 | Auto-generated | Added power management, airtime fairness, channel utilization |
| 3.4 | 2026-01-08 | Auto-generated | Added client steering, band selection, load balancing algorithms |
| 3.5 | 2026-01-08 | Auto-generated | Added mesh networking, WDS, repeater modes, backhaul optimization |
| 3.6 | 2026-01-08 | Auto-generated | Added roaming protocols, 802.11k/v/r deep dive, seamless handoff |
| 3.7 | 2026-01-08 | Auto-generated | Added DHCP deep dive, DNS, mDNS, service discovery |
| 3.8 | 2026-01-08 | Auto-generated | Added firewall policies, ACLs, traffic filtering, NAT |
| 3.9 | 2026-01-08 | Auto-generated | Added IoT device profiling, device fingerprinting, MAC randomization |
| 4.0 | 2026-01-08 | Auto-generated | Added CLI command reference, API reference, automation |

---

## Appendix DF: CLI Command Reference

### DF.1 Show Commands

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    SHOW COMMANDS                                             │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  Client Commands:                                                            │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  # Show all connected clients                                        │    │
│  │  show clients                                                        │    │
│  │                                                                      │    │
│  │  # Show client details                                               │    │
│  │  show client mac AA:BB:CC:DD:EE:FF                                   │    │
│  │                                                                      │    │
│  │  # Show client statistics                                            │    │
│  │  show client statistics                                              │    │
│  │                                                                      │    │
│  │  # Show clients by SSID                                              │    │
│  │  show clients ssid Corporate                                         │    │
│  │                                                                      │    │
│  │  # Show client roaming history                                       │    │
│  │  show client mac AA:BB:CC:DD:EE:FF roaming-history                   │    │
│  │                                                                      │    │
│  │  Sample Output:                                                      │    │
│  │  ┌────────────────────────────────────────────────────────────┐     │    │
│  │  │ MAC Address        SSID        RSSI   Rate    IP Address   │     │    │
│  │  │ ───────────        ────        ────   ────    ──────────   │     │    │
│  │  │ AA:BB:CC:DD:EE:FF  Corporate   -65    866M    10.1.1.100   │     │    │
│  │  │ 11:22:33:44:55:66  Guest       -72    433M    192.168.1.50 │     │    │
│  │  │ 77:88:99:AA:BB:CC  IoT         -58    144M    10.50.1.25   │     │    │
│  │  └────────────────────────────────────────────────────────────┘     │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  Radio Commands:                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  # Show radio status                                                 │    │
│  │  show radio                                                          │    │
│  │                                                                      │    │
│  │  # Show radio statistics                                             │    │
│  │  show radio statistics                                               │    │
│  │                                                                      │    │
│  │  # Show channel utilization                                          │    │
│  │  show radio channel-utilization                                      │    │
│  │                                                                      │    │
│  │  # Show neighbor APs                                                 │    │
│  │  show radio neighbors                                                │    │
│  │                                                                      │    │
│  │  # Show DFS status                                                   │    │
│  │  show radio dfs                                                      │    │
│  │                                                                      │    │
│  │  Sample Output:                                                      │    │
│  │  ┌────────────────────────────────────────────────────────────┐     │    │
│  │  │ Radio   Band    Channel   Width   Power   Clients   Util   │     │    │
│  │  │ ─────   ────    ───────   ─────   ─────   ───────   ────   │     │    │
│  │  │ 0       2.4GHz  6         20MHz   17dBm   15        45%    │     │    │
│  │  │ 1       5GHz    36        80MHz   20dBm   42        62%    │     │    │
│  │  │ 2       6GHz    5         160MHz  24dBm   8         25%    │     │    │
│  │  └────────────────────────────────────────────────────────────┘     │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  SSID Commands:                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  # Show SSID configuration                                           │    │
│  │  show ssid                                                           │    │
│  │                                                                      │    │
│  │  # Show SSID details                                                 │    │
│  │  show ssid Corporate                                                 │    │
│  │                                                                      │    │
│  │  # Show SSID statistics                                              │    │
│  │  show ssid statistics                                                │    │
│  │                                                                      │    │
│  │  Sample Output:                                                      │    │
│  │  ┌────────────────────────────────────────────────────────────┐     │    │
│  │  │ SSID        Security      VLAN   Clients   TX Bytes       │     │    │
│  │  │ ────        ────────      ────   ───────   ────────       │     │    │
│  │  │ Corporate   WPA3-Ent      10     45        1.2 GB         │     │    │
│  │  │ Guest       WPA2-PSK      20     23        456 MB         │     │    │
│  │  │ IoT         WPA2-PSK      50     12        89 MB          │     │    │
│  │  └────────────────────────────────────────────────────────────┘     │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  System Commands:                                                            │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  # Show system information                                           │    │
│  │  show system                                                         │    │
│  │                                                                      │    │
│  │  # Show CPU and memory                                               │    │
│  │  show system resources                                               │    │
│  │                                                                      │    │
│  │  # Show uptime                                                       │    │
│  │  show uptime                                                         │    │
│  │                                                                      │    │
│  │  # Show version                                                      │    │
│  │  show version                                                        │    │
│  │                                                                      │    │
│  │  # Show running configuration                                        │    │
│  │  show running-config                                                 │    │
│  │                                                                      │    │
│  │  # Show interfaces                                                   │    │
│  │  show interfaces                                                     │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### DF.2 Debug Commands

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    DEBUG COMMANDS                                            │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  Client Debugging:                                                           │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  # Enable client debug                                               │    │
│  │  debug client mac AA:BB:CC:DD:EE:FF                                  │    │
│  │                                                                      │    │
│  │  # Debug all clients on SSID                                         │    │
│  │  debug client ssid Corporate                                         │    │
│  │                                                                      │    │
│  │  # Debug authentication                                              │    │
│  │  debug dot1x                                                         │    │
│  │  debug radius                                                        │    │
│  │                                                                      │    │
│  │  # Debug 4-way handshake                                             │    │
│  │  debug wpa                                                           │    │
│  │                                                                      │    │
│  │  # Debug roaming                                                     │    │
│  │  debug roaming                                                       │    │
│  │  debug dot11r                                                        │    │
│  │  debug dot11k                                                        │    │
│  │  debug dot11v                                                        │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  Radio Debugging:                                                            │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  # Debug radio events                                                │    │
│  │  debug radio                                                         │    │
│  │                                                                      │    │
│  │  # Debug DFS                                                         │    │
│  │  debug dfs                                                           │    │
│  │                                                                      │    │
│  │  # Debug channel selection                                           │    │
│  │  debug arm                                                           │    │
│  │                                                                      │    │
│  │  # Debug interference                                                │    │
│  │  debug spectrum                                                      │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  Packet Capture:                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  # Capture on radio interface                                        │    │
│  │  packet-capture interface wlan0 file /tmp/capture.pcap               │    │
│  │                                                                      │    │
│  │  # Capture with filter                                               │    │
│  │  packet-capture interface wlan0 filter "host 10.1.1.100"             │    │
│  │                                                                      │    │
│  │  # Capture specific client                                           │    │
│  │  packet-capture client AA:BB:CC:DD:EE:FF                             │    │
│  │                                                                      │    │
│  │  # Remote capture (stream to Wireshark)                              │    │
│  │  packet-capture interface wlan0 remote 10.1.1.200:5555               │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### DF.3 Configuration Commands

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    CONFIGURATION COMMANDS                                    │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  SSID Configuration:                                                         │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  # Create SSID                                                       │    │
│  │  ssid Corporate                                                      │    │
│  │    enable                                                            │    │
│  │    vlan 10                                                           │    │
│  │    security wpa3-enterprise                                          │    │
│  │    radius-server primary 10.1.1.100                                  │    │
│  │    radius-server secondary 10.1.1.101                                │    │
│  │    pmf required                                                      │    │
│  │    fast-transition enable                                            │    │
│  │    okc enable                                                        │    │
│  │                                                                      │    │
│  │  # Modify SSID                                                       │    │
│  │  ssid Corporate                                                      │    │
│  │    rate-limit client downstream 100mbps                              │    │
│  │    rate-limit client upstream 50mbps                                 │    │
│  │                                                                      │    │
│  │  # Delete SSID                                                       │    │
│  │  no ssid Corporate                                                   │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  Radio Configuration:                                                        │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  # Configure radio                                                   │    │
│  │  radio 1                                                             │    │
│  │    channel 36                                                        │    │
│  │    channel-width 80                                                  │    │
│  │    tx-power 17                                                       │    │
│  │    mode 802.11ax                                                     │    │
│  │                                                                      │    │
│  │  # Enable automatic channel selection                                │    │
│  │  radio 1                                                             │    │
│  │    channel auto                                                      │    │
│  │    arm enable                                                        │    │
│  │                                                                      │    │
│  │  # Configure DFS                                                     │    │
│  │  radio 1                                                             │    │
│  │    dfs enable                                                        │    │
│  │    dfs-channel-list 52 56 60 64 100 104 108 112 116 120 124 128      │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  Security Configuration:                                                     │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  # Configure RADIUS                                                  │    │
│  │  radius-server auth primary                                          │    │
│  │    host 10.1.1.100                                                   │    │
│  │    port 1812                                                         │    │
│  │    secret RadiusSecret123                                            │    │
│  │    timeout 5                                                         │    │
│  │    retries 3                                                         │    │
│  │                                                                      │    │
│  │  # Configure certificates                                            │    │
│  │  crypto pki import ca-cert /tmp/ca.pem                               │    │
│  │  crypto pki import server-cert /tmp/server.pem                       │    │
│  │  crypto pki import server-key /tmp/server.key                        │    │
│  │                                                                      │    │
│  │  # Configure firewall                                                │    │
│  │  firewall-policy guest-policy                                        │    │
│  │    rule 10 permit tcp any any eq 80                                  │    │
│  │    rule 20 permit tcp any any eq 443                                 │    │
│  │    rule 30 deny ip any 10.0.0.0/8                                    │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Appendix DG: REST API Reference

### DG.1 API Authentication

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    API AUTHENTICATION                                        │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  Authentication Methods:                                                     │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  ┌────────────────────────────────────────────────────────────┐     │    │
│  │  │ Method              Description                            │     │    │
│  │  │ ──────              ───────────                            │     │    │
│  │  │ API Key             Static key in header                   │     │    │
│  │  │ Bearer Token        JWT token from login                   │     │    │
│  │  │ OAuth 2.0           OAuth flow with refresh tokens         │     │    │
│  │  │ Basic Auth          Username:password (deprecated)         │     │    │
│  │  └────────────────────────────────────────────────────────────┘     │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  Login Request:                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  POST /api/v1/login                                                  │    │
│  │  Content-Type: application/json                                      │    │
│  │                                                                      │    │
│  │  {                                                                   │    │
│  │    "username": "admin",                                              │    │
│  │    "password": "SecurePassword123"                                   │    │
│  │  }                                                                   │    │
│  │                                                                      │    │
│  │  Response:                                                           │    │
│  │  {                                                                   │    │
│  │    "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",               │    │
│  │    "expires_in": 3600,                                               │    │
│  │    "refresh_token": "dGhpcyBpcyBhIHJlZnJlc2ggdG9rZW4..."            │    │
│  │  }                                                                   │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  Using Bearer Token:                                                         │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  GET /api/v1/clients                                                 │    │
│  │  Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...       │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### DG.2 Client API

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    CLIENT API                                                │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  List Clients:                                                               │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  GET /api/v1/clients                                                 │    │
│  │                                                                      │    │
│  │  Query Parameters:                                                   │    │
│  │  - ssid: Filter by SSID                                              │    │
│  │  - ap: Filter by AP name                                             │    │
│  │  - limit: Max results (default 100)                                  │    │
│  │  - offset: Pagination offset                                         │    │
│  │                                                                      │    │
│  │  Response:                                                           │    │
│  │  {                                                                   │    │
│  │    "clients": [                                                      │    │
│  │      {                                                               │    │
│  │        "mac": "AA:BB:CC:DD:EE:FF",                                   │    │
│  │        "ip": "10.1.1.100",                                           │    │
│  │        "ssid": "Corporate",                                          │    │
│  │        "ap_name": "AP-Floor2-East",                                  │    │
│  │        "rssi": -65,                                                  │    │
│  │        "snr": 30,                                                    │    │
│  │        "tx_rate": 866,                                               │    │
│  │        "rx_rate": 866,                                               │    │
│  │        "connected_time": 3600,                                       │    │
│  │        "tx_bytes": 1234567890,                                       │    │
│  │        "rx_bytes": 9876543210,                                       │    │
│  │        "device_type": "iPhone",                                      │    │
│  │        "os": "iOS 17.2",                                             │    │
│  │        "username": "john.doe@company.com"                            │    │
│  │      }                                                               │    │
│  │    ],                                                                │    │
│  │    "total": 150,                                                     │    │
│  │    "limit": 100,                                                     │    │
│  │    "offset": 0                                                       │    │
│  │  }                                                                   │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  Get Client Details:                                                         │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  GET /api/v1/clients/AA:BB:CC:DD:EE:FF                               │    │
│  │                                                                      │    │
│  │  Response:                                                           │    │
│  │  {                                                                   │    │
│  │    "mac": "AA:BB:CC:DD:EE:FF",                                       │    │
│  │    "ip": "10.1.1.100",                                               │    │
│  │    "ssid": "Corporate",                                              │    │
│  │    "ap_name": "AP-Floor2-East",                                      │    │
│  │    "radio": "5GHz",                                                  │    │
│  │    "channel": 36,                                                    │    │
│  │    "rssi": -65,                                                      │    │
│  │    "snr": 30,                                                        │    │
│  │    "capabilities": {                                                 │    │
│  │      "ht": true,                                                     │    │
│  │      "vht": true,                                                    │    │
│  │      "he": true,                                                     │    │
│  │      "eht": false,                                                   │    │
│  │      "mlo": false                                                    │    │
│  │    },                                                                │    │
│  │    "roaming_history": [                                              │    │
│  │      {                                                               │    │
│  │        "timestamp": "2026-01-08T10:30:00Z",                          │    │
│  │        "from_ap": "AP-Floor1-West",                                  │    │
│  │        "to_ap": "AP-Floor2-East",                                    │    │
│  │        "roam_type": "802.11r",                                       │    │
│  │        "roam_time_ms": 15                                            │    │
│  │      }                                                               │    │
│  │    ]                                                                 │    │
│  │  }                                                                   │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  Disconnect Client:                                                          │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  POST /api/v1/clients/AA:BB:CC:DD:EE:FF/disconnect                   │    │
│  │  Content-Type: application/json                                      │    │
│  │                                                                      │    │
│  │  {                                                                   │    │
│  │    "reason": "admin_disconnect",                                     │    │
│  │    "ban_duration": 0                                                 │    │
│  │  }                                                                   │    │
│  │                                                                      │    │
│  │  Response:                                                           │    │
│  │  {                                                                   │    │
│  │    "status": "success",                                              │    │
│  │    "message": "Client disconnected"                                  │    │
│  │  }                                                                   │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### DG.3 SSID API

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    SSID API                                                  │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  List SSIDs:                                                                 │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  GET /api/v1/ssids                                                   │    │
│  │                                                                      │    │
│  │  Response:                                                           │    │
│  │  {                                                                   │    │
│  │    "ssids": [                                                        │    │
│  │      {                                                               │    │
│  │        "name": "Corporate",                                          │    │
│  │        "enabled": true,                                              │    │
│  │        "security": "wpa3-enterprise",                                │    │
│  │        "vlan": 10,                                                   │    │
│  │        "client_count": 45,                                           │    │
│  │        "bands": ["2.4GHz", "5GHz", "6GHz"]                           │    │
│  │      },                                                              │    │
│  │      {                                                               │    │
│  │        "name": "Guest",                                              │    │
│  │        "enabled": true,                                              │    │
│  │        "security": "wpa2-psk",                                       │    │
│  │        "vlan": 20,                                                   │    │
│  │        "client_count": 23,                                           │    │
│  │        "bands": ["2.4GHz", "5GHz"]                                   │    │
│  │      }                                                               │    │
│  │    ]                                                                 │    │
│  │  }                                                                   │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  Create SSID:                                                                │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  POST /api/v1/ssids                                                  │    │
│  │  Content-Type: application/json                                      │    │
│  │                                                                      │    │
│  │  {                                                                   │    │
│  │    "name": "NewSSID",                                                │    │
│  │    "enabled": true,                                                  │    │
│  │    "security": {                                                     │    │
│  │      "type": "wpa2-psk",                                             │    │
│  │      "psk": "SecurePassword123"                                      │    │
│  │    },                                                                │    │
│  │    "vlan": 30,                                                       │    │
│  │    "bands": ["5GHz"],                                                │    │
│  │    "rate_limit": {                                                   │    │
│  │      "downstream": 50000000,                                         │    │
│  │      "upstream": 25000000                                            │    │
│  │    },                                                                │    │
│  │    "client_isolation": true                                          │    │
│  │  }                                                                   │    │
│  │                                                                      │    │
│  │  Response:                                                           │    │
│  │  {                                                                   │    │
│  │    "status": "success",                                              │    │
│  │    "ssid": {                                                         │    │
│  │      "name": "NewSSID",                                              │    │
│  │      "id": "ssid-12345"                                              │    │
│  │    }                                                                 │    │
│  │  }                                                                   │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  Update SSID:                                                                │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  PUT /api/v1/ssids/Corporate                                         │    │
│  │  Content-Type: application/json                                      │    │
│  │                                                                      │    │
│  │  {                                                                   │    │
│  │    "rate_limit": {                                                   │    │
│  │      "downstream": 100000000,                                        │    │
│  │      "upstream": 50000000                                            │    │
│  │    }                                                                 │    │
│  │  }                                                                   │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  Delete SSID:                                                                │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  DELETE /api/v1/ssids/OldSSID                                        │    │
│  │                                                                      │    │
│  │  Response:                                                           │    │
│  │  {                                                                   │    │
│  │    "status": "success",                                              │    │
│  │    "message": "SSID deleted"                                         │    │
│  │  }                                                                   │    │
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
| 3.1 | 2026-01-08 | Auto-generated | Added WiFi 7 MLO, puncturing, 4K-QAM, multi-RU, enhanced security |
| 3.2 | 2026-01-08 | Auto-generated | Added FILS, DPP, enterprise security, certificate management |
| 3.3 | 2026-01-08 | Auto-generated | Added power management, airtime fairness, channel utilization |
| 3.4 | 2026-01-08 | Auto-generated | Added client steering, band selection, load balancing algorithms |
| 3.5 | 2026-01-08 | Auto-generated | Added mesh networking, WDS, repeater modes, backhaul optimization |
| 3.6 | 2026-01-08 | Auto-generated | Added roaming protocols, 802.11k/v/r deep dive, seamless handoff |
| 3.7 | 2026-01-08 | Auto-generated | Added DHCP deep dive, DNS, mDNS, service discovery |
| 3.8 | 2026-01-08 | Auto-generated | Added firewall policies, ACLs, traffic filtering, NAT |
| 3.9 | 2026-01-08 | Auto-generated | Added IoT device profiling, device fingerprinting, MAC randomization |
| 4.0 | 2026-01-08 | Auto-generated | Added CLI command reference, API reference, automation |
| 4.1 | 2026-01-08 | Auto-generated | Added network automation, scripting, integration examples |

---

## Appendix DH: Network Automation

### DH.1 Ansible Integration

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    ANSIBLE INTEGRATION                                       │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  Ansible Inventory:                                                          │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  # inventory.yml                                                     │    │
│  │  all:                                                                │    │
│  │    children:                                                         │    │
│  │      access_points:                                                  │    │
│  │        hosts:                                                        │    │
│  │          ap-floor1-east:                                             │    │
│  │            ansible_host: 10.1.1.10                                   │    │
│  │          ap-floor1-west:                                             │    │
│  │            ansible_host: 10.1.1.11                                   │    │
│  │          ap-floor2-east:                                             │    │
│  │            ansible_host: 10.1.1.20                                   │    │
│  │          ap-floor2-west:                                             │    │
│  │            ansible_host: 10.1.1.21                                   │    │
│  │        vars:                                                         │    │
│  │          ansible_network_os: arista_ap                               │    │
│  │          ansible_connection: network_cli                             │    │
│  │          ansible_user: admin                                         │    │
│  │          ansible_password: "{{ vault_ap_password }}"                 │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  Ansible Playbook - Configure SSID:                                         │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  # configure_ssid.yml                                                │    │
│  │  ---                                                                 │    │
│  │  - name: Configure Corporate SSID                                    │    │
│  │    hosts: access_points                                              │    │
│  │    gather_facts: no                                                  │    │
│  │    tasks:                                                            │    │
│  │      - name: Configure SSID                                          │    │
│  │        arista_ap_ssid:                                               │    │
│  │          name: Corporate                                             │    │
│  │          enabled: yes                                                │    │
│  │          security: wpa3-enterprise                                   │    │
│  │          vlan: 10                                                    │    │
│  │          radius_server: 10.1.1.100                                   │    │
│  │          radius_secret: "{{ vault_radius_secret }}"                  │    │
│  │          pmf: required                                               │    │
│  │          fast_transition: yes                                        │    │
│  │          okc: yes                                                    │    │
│  │                                                                      │    │
│  │      - name: Configure rate limiting                                 │    │
│  │        arista_ap_rate_limit:                                         │    │
│  │          ssid: Corporate                                             │    │
│  │          downstream: 100mbps                                         │    │
│  │          upstream: 50mbps                                            │    │
│  │                                                                      │    │
│  │      - name: Save configuration                                      │    │
│  │        arista_ap_command:                                            │    │
│  │          commands:                                                   │    │
│  │            - write memory                                            │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  Ansible Playbook - Firmware Upgrade:                                       │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  # upgrade_firmware.yml                                              │    │
│  │  ---                                                                 │    │
│  │  - name: Upgrade AP Firmware                                         │    │
│  │    hosts: access_points                                              │    │
│  │    serial: 1                                                         │    │
│  │    gather_facts: no                                                  │    │
│  │    tasks:                                                            │    │
│  │      - name: Check current version                                   │    │
│  │        arista_ap_command:                                            │    │
│  │          commands:                                                   │    │
│  │            - show version                                            │    │
│  │        register: version_output                                      │    │
│  │                                                                      │    │
│  │      - name: Download firmware                                       │    │
│  │        arista_ap_command:                                            │    │
│  │          commands:                                                   │    │
│  │            - copy tftp://10.1.1.50/firmware.bin flash:               │    │
│  │        when: "'17.0.0' not in version_output.stdout[0]"              │    │
│  │                                                                      │    │
│  │      - name: Install firmware                                        │    │
│  │        arista_ap_command:                                            │    │
│  │          commands:                                                   │    │
│  │            - boot system flash:firmware.bin                          │    │
│  │        when: "'17.0.0' not in version_output.stdout[0]"              │    │
│  │                                                                      │    │
│  │      - name: Reboot AP                                               │    │
│  │        arista_ap_command:                                            │    │
│  │          commands:                                                   │    │
│  │            - reload                                                  │    │
│  │        when: "'17.0.0' not in version_output.stdout[0]"              │    │
│  │                                                                      │    │
│  │      - name: Wait for AP to come back                                │    │
│  │        wait_for:                                                     │    │
│  │          host: "{{ ansible_host }}"                                  │    │
│  │          port: 22                                                    │    │
│  │          delay: 60                                                   │    │
│  │          timeout: 300                                                │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### DH.2 Python Scripting

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    PYTHON SCRIPTING                                          │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  API Client Library:                                                         │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  # ap_client.py                                                      │    │
│  │  import requests                                                     │    │
│  │  import json                                                         │    │
│  │                                                                      │    │
│  │  class APClient:                                                     │    │
│  │      def __init__(self, host, username, password):                   │    │
│  │          self.host = host                                            │    │
│  │          self.base_url = f"https://{host}/api/v1"                    │    │
│  │          self.session = requests.Session()                           │    │
│  │          self.session.verify = False                                 │    │
│  │          self._login(username, password)                             │    │
│  │                                                                      │    │
│  │      def _login(self, username, password):                           │    │
│  │          response = self.session.post(                               │    │
│  │              f"{self.base_url}/login",                               │    │
│  │              json={"username": username, "password": password}       │    │
│  │          )                                                           │    │
│  │          token = response.json()["token"]                            │    │
│  │          self.session.headers["Authorization"] = f"Bearer {token}"   │    │
│  │                                                                      │    │
│  │      def get_clients(self, ssid=None):                               │    │
│  │          params = {"ssid": ssid} if ssid else {}                     │    │
│  │          response = self.session.get(                                │    │
│  │              f"{self.base_url}/clients",                             │    │
│  │              params=params                                           │    │
│  │          )                                                           │    │
│  │          return response.json()["clients"]                           │    │
│  │                                                                      │    │
│  │      def disconnect_client(self, mac):                               │    │
│  │          response = self.session.post(                               │    │
│  │              f"{self.base_url}/clients/{mac}/disconnect"             │    │
│  │          )                                                           │    │
│  │          return response.json()                                      │    │
│  │                                                                      │    │
│  │      def get_ssids(self):                                            │    │
│  │          response = self.session.get(f"{self.base_url}/ssids")       │    │
│  │          return response.json()["ssids"]                             │    │
│  │                                                                      │    │
│  │      def create_ssid(self, config):                                  │    │
│  │          response = self.session.post(                               │    │
│  │              f"{self.base_url}/ssids",                               │    │
│  │              json=config                                             │    │
│  │          )                                                           │    │
│  │          return response.json()                                      │    │
│  │                                                                      │    │
│  │      def get_radio_stats(self):                                      │    │
│  │          response = self.session.get(                                │    │
│  │              f"{self.base_url}/radios/statistics"                    │    │
│  │          )                                                           │    │
│  │          return response.json()                                      │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  Usage Example:                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  # example_usage.py                                                  │    │
│  │  from ap_client import APClient                                      │    │
│  │                                                                      │    │
│  │  # Connect to AP                                                     │    │
│  │  ap = APClient("10.1.1.10", "admin", "password")                     │    │
│  │                                                                      │    │
│  │  # Get all clients                                                   │    │
│  │  clients = ap.get_clients()                                          │    │
│  │  print(f"Total clients: {len(clients)}")                             │    │
│  │                                                                      │    │
│  │  # Find clients with weak signal                                     │    │
│  │  weak_clients = [c for c in clients if c["rssi"] < -75]              │    │
│  │  for client in weak_clients:                                         │    │
│  │      print(f"Weak client: {client['mac']} RSSI: {client['rssi']}")   │    │
│  │                                                                      │    │
│  │  # Get radio statistics                                              │    │
│  │  stats = ap.get_radio_stats()                                        │    │
│  │  for radio in stats["radios"]:                                       │    │
│  │      print(f"Radio {radio['band']}: {radio['channel_utilization']}%")│    │
│  │                                                                      │    │
│  │  # Create new SSID                                                   │    │
│  │  new_ssid = ap.create_ssid({                                         │    │
│  │      "name": "TestSSID",                                             │    │
│  │      "enabled": True,                                                │    │
│  │      "security": {"type": "wpa2-psk", "psk": "TestPassword123"},     │    │
│  │      "vlan": 100                                                     │    │
│  │  })                                                                  │    │
│  │  print(f"Created SSID: {new_ssid}")                                  │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  Monitoring Script:                                                          │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  # monitor_clients.py                                                │    │
│  │  import time                                                         │    │
│  │  import logging                                                      │    │
│  │  from ap_client import APClient                                      │    │
│  │                                                                      │    │
│  │  logging.basicConfig(level=logging.INFO)                             │    │
│  │  logger = logging.getLogger(__name__)                                │    │
│  │                                                                      │    │
│  │  def monitor_clients(ap, interval=60):                               │    │
│  │      """Monitor client connections and alert on issues."""           │    │
│  │      previous_clients = set()                                        │    │
│  │                                                                      │    │
│  │      while True:                                                     │    │
│  │          clients = ap.get_clients()                                  │    │
│  │          current_clients = {c["mac"] for c in clients}               │    │
│  │                                                                      │    │
│  │          # New connections                                           │    │
│  │          new = current_clients - previous_clients                    │    │
│  │          for mac in new:                                             │    │
│  │              logger.info(f"New client connected: {mac}")             │    │
│  │                                                                      │    │
│  │          # Disconnections                                            │    │
│  │          disconnected = previous_clients - current_clients           │    │
│  │          for mac in disconnected:                                    │    │
│  │              logger.info(f"Client disconnected: {mac}")              │    │
│  │                                                                      │    │
│  │          # Check for weak signals                                    │    │
│  │          for client in clients:                                      │    │
│  │              if client["rssi"] < -80:                                │    │
│  │                  logger.warning(                                     │    │
│  │                      f"Weak signal: {client['mac']} "                │    │
│  │                      f"RSSI: {client['rssi']}"                       │    │
│  │                  )                                                   │    │
│  │                                                                      │    │
│  │          previous_clients = current_clients                          │    │
│  │          time.sleep(interval)                                        │    │
│  │                                                                      │    │
│  │  if __name__ == "__main__":                                          │    │
│  │      ap = APClient("10.1.1.10", "admin", "password")                 │    │
│  │      monitor_clients(ap)                                             │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### DH.3 Terraform Integration

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    TERRAFORM INTEGRATION                                     │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  Provider Configuration:                                                     │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  # main.tf                                                           │    │
│  │  terraform {                                                         │    │
│  │    required_providers {                                              │    │
│  │      arista_ap = {                                                   │    │
│  │        source  = "arista/arista-ap"                                  │    │
│  │        version = "~> 1.0"                                            │    │
│  │      }                                                               │    │
│  │    }                                                                 │    │
│  │  }                                                                   │    │
│  │                                                                      │    │
│  │  provider "arista_ap" {                                              │    │
│  │    host     = var.controller_host                                    │    │
│  │    username = var.controller_username                                │    │
│  │    password = var.controller_password                                │    │
│  │  }                                                                   │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  SSID Resource:                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  # ssid.tf                                                           │    │
│  │  resource "arista_ap_ssid" "corporate" {                             │    │
│  │    name     = "Corporate"                                            │    │
│  │    enabled  = true                                                   │    │
│  │    vlan     = 10                                                     │    │
│  │                                                                      │    │
│  │    security {                                                        │    │
│  │      type = "wpa3-enterprise"                                        │    │
│  │      pmf  = "required"                                               │    │
│  │    }                                                                 │    │
│  │                                                                      │    │
│  │    radius {                                                          │    │
│  │      primary_server   = "10.1.1.100"                                 │    │
│  │      primary_secret   = var.radius_secret                            │    │
│  │      secondary_server = "10.1.1.101"                                 │    │
│  │      secondary_secret = var.radius_secret                            │    │
│  │    }                                                                 │    │
│  │                                                                      │    │
│  │    roaming {                                                         │    │
│  │      fast_transition = true                                          │    │
│  │      okc             = true                                          │    │
│  │    }                                                                 │    │
│  │                                                                      │    │
│  │    rate_limit {                                                      │    │
│  │      downstream_mbps = 100                                           │    │
│  │      upstream_mbps   = 50                                            │    │
│  │    }                                                                 │    │
│  │  }                                                                   │    │
│  │                                                                      │    │
│  │  resource "arista_ap_ssid" "guest" {                                 │    │
│  │    name     = "Guest"                                                │    │
│  │    enabled  = true                                                   │    │
│  │    vlan     = 20                                                     │    │
│  │                                                                      │    │
│  │    security {                                                        │    │
│  │      type = "wpa2-psk"                                               │    │
│  │      psk  = var.guest_psk                                            │    │
│  │    }                                                                 │    │
│  │                                                                      │    │
│  │    captive_portal {                                                  │    │
│  │      enabled      = true                                             │    │
│  │      redirect_url = "https://portal.company.com"                     │    │
│  │    }                                                                 │    │
│  │                                                                      │    │
│  │    client_isolation = true                                           │    │
│  │  }                                                                   │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  Radio Configuration:                                                        │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  # radio.tf                                                          │    │
│  │  resource "arista_ap_radio_profile" "default_5ghz" {                 │    │
│  │    name = "default-5ghz"                                             │    │
│  │    band = "5GHz"                                                     │    │
│  │                                                                      │    │
│  │    channel {                                                         │    │
│  │      mode  = "auto"                                                  │    │
│  │      width = 80                                                      │    │
│  │    }                                                                 │    │
│  │                                                                      │    │
│  │    power {                                                           │    │
│  │      mode = "auto"                                                   │    │
│  │      max  = 20                                                       │    │
│  │      min  = 8                                                        │    │
│  │    }                                                                 │    │
│  │                                                                      │    │
│  │    dfs {                                                             │    │
│  │      enabled = true                                                  │    │
│  │    }                                                                 │    │
│  │  }                                                                   │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Appendix DI: Time Synchronization

### DI.1 NTP Configuration

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    NTP CONFIGURATION                                         │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  NTP Importance for WiFi:                                                    │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  ┌────────────────────────────────────────────────────────────┐     │    │
│  │  │ Feature                 Time Sensitivity                   │     │    │
│  │  │ ───────                 ────────────────                   │     │    │
│  │  │ Certificate validation  Seconds                            │     │    │
│  │  │ RADIUS accounting       Seconds                            │     │    │
│  │  │ Log correlation         Seconds                            │     │    │
│  │  │ Roaming (802.11r)       Milliseconds                       │     │    │
│  │  │ TWT scheduling          Microseconds                       │     │    │
│  │  │ Location services       Nanoseconds (for ToA)              │     │    │
│  │  └────────────────────────────────────────────────────────────┘     │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  NTP Configuration:                                                          │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  # Configure NTP servers                                             │    │
│  │  ntp server 10.1.1.50 prefer                                         │    │
│  │  ntp server 10.1.1.51                                                │    │
│  │  ntp server pool.ntp.org                                             │    │
│  │                                                                      │    │
│  │  # Configure timezone                                                │    │
│  │  clock timezone PST -8                                               │    │
│  │  clock summer-time PDT recurring                                     │    │
│  │                                                                      │    │
│  │  # Enable NTP authentication                                         │    │
│  │  ntp authentication enable                                           │    │
│  │  ntp authentication-key 1 md5 NtpSecret123                           │    │
│  │  ntp trusted-key 1                                                   │    │
│  │  ntp server 10.1.1.50 key 1                                          │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  NTP Status:                                                                 │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  # Show NTP status                                                   │    │
│  │  show ntp status                                                     │    │
│  │                                                                      │    │
│  │  Sample Output:                                                      │    │
│  │  ┌────────────────────────────────────────────────────────────┐     │    │
│  │  │ Clock is synchronized                                      │     │    │
│  │  │ Stratum: 3                                                 │     │    │
│  │  │ Reference: 10.1.1.50                                       │     │    │
│  │  │ Offset: +0.003 seconds                                     │     │    │
│  │  │ Last update: 2026-01-08 12:00:00                           │     │    │
│  │  └────────────────────────────────────────────────────────────┘     │    │
│  │                                                                      │    │
│  │  # Show NTP associations                                             │    │
│  │  show ntp associations                                               │    │
│  │                                                                      │    │
│  │  Sample Output:                                                      │    │
│  │  ┌────────────────────────────────────────────────────────────┐     │    │
│  │  │ Server          Stratum   Offset    Delay     Status      │     │    │
│  │  │ ──────          ───────   ──────    ─────     ──────      │     │    │
│  │  │ *10.1.1.50      2         +0.003    0.5ms     sys.peer    │     │    │
│  │  │ +10.1.1.51      2         +0.005    0.8ms     candidate   │     │    │
│  │  │ -pool.ntp.org   2         +0.050    25ms      outlier     │     │    │
│  │  └────────────────────────────────────────────────────────────┘     │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### DI.2 PTP (Precision Time Protocol)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    PTP CONFIGURATION                                         │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  PTP Overview:                                                               │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  PTP (IEEE 1588) provides sub-microsecond time synchronization       │    │
│  │  Required for:                                                       │    │
│  │  - WiFi 7 Multi-Link Operation (MLO)                                 │    │
│  │  - Fine Timing Measurement (FTM)                                     │    │
│  │  - Location services                                                 │    │
│  │  - Coordinated scheduling                                            │    │
│  │                                                                      │    │
│  │  PTP Profiles:                                                       │    │
│  │  ┌────────────────────────────────────────────────────────────┐     │    │
│  │  │ Profile             Accuracy        Use Case               │     │    │
│  │  │ ───────             ────────        ────────               │     │    │
│  │  │ Default             < 1 μs          General purpose        │     │    │
│  │  │ Telecom             < 100 ns        Carrier networks       │     │    │
│  │  │ Power               < 1 μs          Power grid             │     │    │
│  │  │ Enterprise          < 1 μs          Enterprise WiFi        │     │    │
│  │  └────────────────────────────────────────────────────────────┘     │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  PTP Configuration:                                                          │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  # Enable PTP                                                        │    │
│  │  ptp enable                                                          │    │
│  │  ptp mode boundary-clock                                             │    │
│  │  ptp domain 0                                                        │    │
│  │  ptp priority1 128                                                   │    │
│  │  ptp priority2 128                                                   │    │
│  │                                                                      │    │
│  │  # Configure PTP interface                                           │    │
│  │  interface ethernet0                                                 │    │
│  │    ptp enable                                                        │    │
│  │    ptp transport ipv4                                                │    │
│  │    ptp announce-interval 1                                           │    │
│  │    ptp sync-interval -3                                              │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Appendix DJ: Cable and Infrastructure

### DJ.1 Ethernet Cabling

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    ETHERNET CABLING                                          │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  Cable Categories:                                                           │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  ┌────────────────────────────────────────────────────────────┐     │    │
│  │  │ Category    Speed       Distance    PoE Support            │     │    │
│  │  │ ────────    ─────       ────────    ───────────            │     │    │
│  │  │ Cat5e       1 Gbps      100m        PoE, PoE+              │     │    │
│  │  │ Cat6        1 Gbps      100m        PoE, PoE+, PoE++       │     │    │
│  │  │ Cat6        10 Gbps     55m         PoE, PoE+, PoE++       │     │    │
│  │  │ Cat6a       10 Gbps     100m        PoE, PoE+, PoE++       │     │    │
│  │  │ Cat7        10 Gbps     100m        PoE, PoE+, PoE++       │     │    │
│  │  │ Cat8        25/40 Gbps  30m         PoE, PoE+, PoE++       │     │    │
│  │  └────────────────────────────────────────────────────────────┘     │    │
│  │                                                                      │    │
│  │  Recommendation for WiFi 6/6E/7:                                     │    │
│  │  - Minimum: Cat6 for WiFi 6                                          │    │
│  │  - Recommended: Cat6a for WiFi 6E/7                                  │    │
│  │  - Future-proof: Cat6a or Cat7                                       │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  PoE Standards:                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  ┌────────────────────────────────────────────────────────────┐     │    │
│  │  │ Standard        IEEE        Power       Voltage            │     │    │
│  │  │ ────────        ────        ─────       ───────            │     │    │
│  │  │ PoE             802.3af     15.4W       48V                │     │    │
│  │  │ PoE+            802.3at     30W         48V                │     │    │
│  │  │ PoE++/4PPoE     802.3bt     60W         48V                │     │    │
│  │  │ PoE++ Type 4    802.3bt     90W         48V                │     │    │
│  │  └────────────────────────────────────────────────────────────┘     │    │
│  │                                                                      │    │
│  │  AP Power Requirements:                                              │    │
│  │  ┌────────────────────────────────────────────────────────────┐     │    │
│  │  │ AP Type             Typical Power    Recommended PoE       │     │    │
│  │  │ ───────             ─────────────    ───────────────       │     │    │
│  │  │ WiFi 5 (2x2)        12W              PoE (802.3af)         │     │    │
│  │  │ WiFi 6 (4x4)        20W              PoE+ (802.3at)        │     │    │
│  │  │ WiFi 6E (4x4x4)     30W              PoE+ (802.3at)        │     │    │
│  │  │ WiFi 7 (4x4x4)      40W              PoE++ (802.3bt)       │     │    │
│  │  │ Outdoor AP          50W              PoE++ (802.3bt)       │     │    │
│  │  └────────────────────────────────────────────────────────────┘     │    │
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
| 3.1 | 2026-01-08 | Auto-generated | Added WiFi 7 MLO, puncturing, 4K-QAM, multi-RU, enhanced security |
| 3.2 | 2026-01-08 | Auto-generated | Added FILS, DPP, enterprise security, certificate management |
| 3.3 | 2026-01-08 | Auto-generated | Added power management, airtime fairness, channel utilization |
| 3.4 | 2026-01-08 | Auto-generated | Added client steering, band selection, load balancing algorithms |
| 3.5 | 2026-01-08 | Auto-generated | Added mesh networking, WDS, repeater modes, backhaul optimization |
| 3.6 | 2026-01-08 | Auto-generated | Added roaming protocols, 802.11k/v/r deep dive, seamless handoff |
| 3.7 | 2026-01-08 | Auto-generated | Added DHCP deep dive, DNS, mDNS, service discovery |
| 3.8 | 2026-01-08 | Auto-generated | Added firewall policies, ACLs, traffic filtering, NAT |
| 3.9 | 2026-01-08 | Auto-generated | Added IoT device profiling, device fingerprinting, MAC randomization |
| 4.0 | 2026-01-08 | Auto-generated | Added CLI command reference, API reference, automation |
| 4.1 | 2026-01-08 | Auto-generated | Added network automation, scripting, integration examples |
| 4.2 | 2026-01-08 | Auto-generated | Added site survey, capacity planning, deployment best practices |

---

## Appendix DK: Site Survey Methodology

### DK.1 Pre-Deployment Survey

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    PRE-DEPLOYMENT SURVEY                                     │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  Survey Types:                                                               │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  ┌────────────────────────────────────────────────────────────┐     │    │
│  │  │ Type              Description                              │     │    │
│  │  │ ────              ───────────                              │     │    │
│  │  │ Passive           Listen-only, no transmission             │     │    │
│  │  │ Active            Connect to AP, measure throughput        │     │    │
│  │  │ Predictive        Software-based modeling                  │     │    │
│  │  │ Hybrid            Combination of above                     │     │    │
│  │  └────────────────────────────────────────────────────────────┘     │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  Survey Equipment:                                                           │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  Required Equipment:                                                 │    │
│  │  - WiFi adapter with monitor mode support                            │    │
│  │  - Survey software (Ekahau, AirMagnet, NetSpot)                      │    │
│  │  - Floor plans (CAD or PDF)                                          │    │
│  │  - Laptop or tablet                                                  │    │
│  │  - Spectrum analyzer (optional)                                      │    │
│  │  - Measuring wheel or laser distance meter                           │    │
│  │                                                                      │    │
│  │  Survey Checklist:                                                   │    │
│  │  ┌────────────────────────────────────────────────────────────┐     │    │
│  │  │ □ Obtain accurate floor plans                              │     │    │
│  │  │ □ Identify coverage requirements                           │     │    │
│  │  │ □ Document wall materials and attenuation                  │     │    │
│  │  │ □ Identify interference sources                            │     │    │
│  │  │ □ Note ceiling heights and obstructions                    │     │    │
│  │  │ □ Document power and network drops                         │     │    │
│  │  │ □ Identify high-density areas                              │     │    │
│  │  │ □ Note security requirements                               │     │    │
│  │  └────────────────────────────────────────────────────────────┘     │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  Wall Attenuation Values:                                                    │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  ┌────────────────────────────────────────────────────────────┐     │    │
│  │  │ Material              2.4 GHz    5 GHz      6 GHz          │     │    │
│  │  │ ────────              ───────    ─────      ─────          │     │    │
│  │  │ Drywall               3 dB       4 dB       5 dB           │     │    │
│  │  │ Plywood               4 dB       5 dB       6 dB           │     │    │
│  │  │ Glass (clear)         3 dB       4 dB       5 dB           │     │    │
│  │  │ Glass (tinted)        6 dB       8 dB       10 dB          │     │    │
│  │  │ Glass (Low-E)         10 dB      12 dB      15 dB          │     │    │
│  │  │ Brick                 6 dB       8 dB       10 dB          │     │    │
│  │  │ Concrete              10 dB      15 dB      20 dB          │     │    │
│  │  │ Concrete (reinforced) 15 dB      20 dB      25 dB          │     │    │
│  │  │ Metal                 20 dB      25 dB      30 dB          │     │    │
│  │  │ Elevator shaft        30 dB      35 dB      40 dB          │     │    │
│  │  └────────────────────────────────────────────────────────────┘     │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### DK.2 AP Placement Guidelines

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    AP PLACEMENT GUIDELINES                                   │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  Coverage vs Capacity Design:                                                │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  Coverage Design:                                                    │    │
│  │  - Focus on signal strength (-67 dBm minimum)                        │    │
│  │  - Fewer APs, larger coverage areas                                  │    │
│  │  - Suitable for low-density environments                             │    │
│  │  - Typical: 1 AP per 2,500-5,000 sq ft                               │    │
│  │                                                                      │    │
│  │  Capacity Design:                                                    │    │
│  │  - Focus on client density and throughput                            │    │
│  │  - More APs, smaller cells                                           │    │
│  │  - Suitable for high-density environments                            │    │
│  │  - Typical: 1 AP per 25-50 clients                                   │    │
│  │                                                                      │    │
│  │  ┌────────────────────────────────────────────────────────────┐     │    │
│  │  │ Environment           Clients/AP    Coverage Area          │     │    │
│  │  │ ───────────           ──────────    ─────────────          │     │    │
│  │  │ Office (standard)     25-30         2,500 sq ft            │     │    │
│  │  │ Office (high-density) 15-20         1,500 sq ft            │     │    │
│  │  │ Conference room       10-15         500 sq ft              │     │    │
│  │  │ Auditorium            50-75         Per section            │     │    │
│  │  │ Warehouse             50-100        10,000 sq ft           │     │    │
│  │  │ Retail                20-30         2,000 sq ft            │     │    │
│  │  │ Healthcare            15-20         1,500 sq ft            │     │    │
│  │  │ Education             25-35         Classroom              │     │    │
│  │  └────────────────────────────────────────────────────────────┘     │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  Mounting Options:                                                           │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  ┌────────────────────────────────────────────────────────────┐     │    │
│  │  │ Mount Type        Best For                                 │     │    │
│  │  │ ──────────        ────────                                 │     │    │
│  │  │ Ceiling (flush)   Standard office, drop ceiling            │     │    │
│  │  │ Ceiling (pendant) High ceilings, open areas                │     │    │
│  │  │ Wall mount        Corridors, narrow spaces                 │     │    │
│  │  │ Above ceiling     Aesthetic requirements                   │     │    │
│  │  │ Pole mount        Outdoor, parking lots                    │     │    │
│  │  │ Desk mount        Temporary deployments                    │     │    │
│  │  └────────────────────────────────────────────────────────────┘     │    │
│  │                                                                      │    │
│  │  Height Recommendations:                                             │    │
│  │  - Standard ceiling: 8-12 feet                                       │    │
│  │  - High ceiling: Use pendant mount to lower AP                       │    │
│  │  - Warehouse: 15-20 feet maximum                                     │    │
│  │  - Outdoor: 10-15 feet                                               │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  Channel Planning:                                                           │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  2.4 GHz (3 non-overlapping channels):                               │    │
│  │  ┌────────────────────────────────────────────────────────────┐     │    │
│  │  │                                                            │     │    │
│  │  │     [1]         [6]         [11]                           │     │    │
│  │  │      │           │           │                             │     │    │
│  │  │  ────┴───────────┴───────────┴────                         │     │    │
│  │  │  2412 MHz    2437 MHz    2462 MHz                          │     │    │
│  │  │                                                            │     │    │
│  │  │  Honeycomb Pattern:                                        │     │    │
│  │  │       [1]     [6]                                          │     │    │
│  │  │          [11]                                              │     │    │
│  │  │       [6]     [1]                                          │     │    │
│  │  │                                                            │     │    │
│  │  └────────────────────────────────────────────────────────────┘     │    │
│  │                                                                      │    │
│  │  5 GHz (UNII bands):                                                 │    │
│  │  ┌────────────────────────────────────────────────────────────┐     │    │
│  │  │ Band        Channels (20 MHz)    DFS Required              │     │    │
│  │  │ ────        ─────────────────    ────────────              │     │    │
│  │  │ UNII-1      36, 40, 44, 48       No                        │     │    │
│  │  │ UNII-2A     52, 56, 60, 64       Yes                       │     │    │
│  │  │ UNII-2C     100-144              Yes                       │     │    │
│  │  │ UNII-3      149, 153, 157, 161   No                        │     │    │
│  │  │ UNII-4      165, 169, 173, 177   No (some regions)         │     │    │
│  │  └────────────────────────────────────────────────────────────┘     │    │
│  │                                                                      │    │
│  │  6 GHz (WiFi 6E/7):                                                  │    │
│  │  ┌────────────────────────────────────────────────────────────┐     │    │
│  │  │ Band        Channels             Notes                     │     │    │
│  │  │ ────        ────────             ─────                     │     │    │
│  │  │ UNII-5      1-93 (20 MHz)        Indoor only (LPI)         │     │    │
│  │  │ UNII-6      97-113               Indoor only (LPI)         │     │    │
│  │  │ UNII-7      117-185              Standard power (SP)       │     │    │
│  │  │ UNII-8      189-233              Standard power (SP)       │     │    │
│  │  └────────────────────────────────────────────────────────────┘     │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### DK.3 Heatmap Analysis

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    HEATMAP ANALYSIS                                          │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  Signal Strength Thresholds:                                                 │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  ┌────────────────────────────────────────────────────────────┐     │    │
│  │  │ RSSI Range      Quality     Color       Use Case           │     │    │
│  │  │ ──────────      ───────     ─────       ────────           │     │    │
│  │  │ > -50 dBm       Excellent   Green       VoIP, Video        │     │    │
│  │  │ -50 to -60      Very Good   Light Green All applications   │     │    │
│  │  │ -60 to -67      Good        Yellow      Data, Web          │     │    │
│  │  │ -67 to -70      Fair        Orange      Basic connectivity │     │    │
│  │  │ -70 to -80      Poor        Red         Marginal           │     │    │
│  │  │ < -80 dBm       No coverage Gray        Dead zone          │     │    │
│  │  └────────────────────────────────────────────────────────────┘     │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  SNR Thresholds:                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  ┌────────────────────────────────────────────────────────────┐     │    │
│  │  │ SNR Range       Quality     Supported Rates                │     │    │
│  │  │ ─────────       ───────     ───────────────                │     │    │
│  │  │ > 40 dB         Excellent   All MCS rates                  │     │    │
│  │  │ 25-40 dB        Good        Most MCS rates                 │     │    │
│  │  │ 15-25 dB        Fair        Lower MCS rates                │     │    │
│  │  │ 10-15 dB        Poor        Basic rates only               │     │    │
│  │  │ < 10 dB         Unusable    Connection issues              │     │    │
│  │  └────────────────────────────────────────────────────────────┘     │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  Heatmap Types:                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  1. Signal Strength (RSSI)                                           │    │
│  │     - Primary coverage indicator                                     │    │
│  │     - Target: -67 dBm or better                                      │    │
│  │                                                                      │    │
│  │  2. Signal-to-Noise Ratio (SNR)                                      │    │
│  │     - Quality indicator                                              │    │
│  │     - Target: 25 dB or better                                        │    │
│  │                                                                      │    │
│  │  3. Channel Overlap                                                  │    │
│  │     - Co-channel interference                                        │    │
│  │     - Target: Minimal overlap                                        │    │
│  │                                                                      │    │
│  │  4. Data Rate                                                        │    │
│  │     - Throughput potential                                           │    │
│  │     - Target: Application-dependent                                  │    │
│  │                                                                      │    │
│  │  5. Retry Rate                                                       │    │
│  │     - Transmission quality                                           │    │
│  │     - Target: < 10%                                                  │    │
│  │                                                                      │    │
│  │  6. Channel Utilization                                              │    │
│  │     - Airtime usage                                                  │    │
│  │     - Target: < 50%                                                  │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Appendix DL: Performance Testing

### DL.1 Throughput Testing

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    THROUGHPUT TESTING                                        │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  iPerf3 Testing:                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  Server Setup:                                                       │    │
│  │  # Start iPerf3 server                                               │    │
│  │  iperf3 -s -p 5201                                                   │    │
│  │                                                                      │    │
│  │  Client Tests:                                                       │    │
│  │  # Basic TCP test                                                    │    │
│  │  iperf3 -c 10.1.1.100 -p 5201 -t 30                                  │    │
│  │                                                                      │    │
│  │  # UDP test with bandwidth limit                                     │    │
│  │  iperf3 -c 10.1.1.100 -u -b 500M -t 30                               │    │
│  │                                                                      │    │
│  │  # Bidirectional test                                                │    │
│  │  iperf3 -c 10.1.1.100 --bidir -t 30                                  │    │
│  │                                                                      │    │
│  │  # Multiple parallel streams                                         │    │
│  │  iperf3 -c 10.1.1.100 -P 4 -t 30                                     │    │
│  │                                                                      │    │
│  │  # Reverse mode (server to client)                                   │    │
│  │  iperf3 -c 10.1.1.100 -R -t 30                                       │    │
│  │                                                                      │    │
│  │  Sample Output:                                                      │    │
│  │  ┌────────────────────────────────────────────────────────────┐     │    │
│  │  │ [ ID] Interval       Transfer    Bitrate        Retr       │     │    │
│  │  │ [  5] 0.00-30.00 sec 2.45 GBytes 702 Mbits/sec  12         │     │    │
│  │  │                                                            │     │    │
│  │  │ - - - - - - - - - - - - - - - - - - - - - - - - - - - - -  │     │    │
│  │  │ [ ID] Interval       Transfer    Bitrate        Retr       │     │    │
│  │  │ [  5] 0.00-30.00 sec 2.45 GBytes 702 Mbits/sec  12  sender │     │    │
│  │  │ [  5] 0.00-30.00 sec 2.45 GBytes 701 Mbits/sec      receiver│     │    │
│  │  └────────────────────────────────────────────────────────────┘     │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  Expected Throughput by Standard:                                            │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  ┌────────────────────────────────────────────────────────────┐     │    │
│  │  │ Standard    PHY Rate    Real Throughput    Test Conditions │     │    │
│  │  │ ────────    ────────    ───────────────    ─────────────── │     │    │
│  │  │ 802.11n     300 Mbps    150-180 Mbps       2x2, 40 MHz     │     │    │
│  │  │ 802.11ac    867 Mbps    400-500 Mbps       2x2, 80 MHz     │     │    │
│  │  │ 802.11ac    1733 Mbps   700-900 Mbps       4x4, 80 MHz     │     │    │
│  │  │ 802.11ax    1201 Mbps   600-800 Mbps       2x2, 80 MHz     │     │    │
│  │  │ 802.11ax    2402 Mbps   1000-1400 Mbps     4x4, 80 MHz     │     │    │
│  │  │ 802.11ax    4804 Mbps   1800-2400 Mbps     4x4, 160 MHz    │     │    │
│  │  │ 802.11be    5764 Mbps   2500-3500 Mbps     4x4, 160 MHz    │     │    │
│  │  │ 802.11be    11529 Mbps  4000-6000 Mbps     4x4, 320 MHz    │     │    │
│  │  └────────────────────────────────────────────────────────────┘     │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### DL.2 Latency Testing

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    LATENCY TESTING                                           │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  Ping Testing:                                                               │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  # Basic ping test                                                   │    │
│  │  ping -c 100 10.1.1.1                                                │    │
│  │                                                                      │    │
│  │  # Flood ping (requires root)                                        │    │
│  │  ping -f -c 1000 10.1.1.1                                            │    │
│  │                                                                      │    │
│  │  # Ping with timestamp                                               │    │
│  │  ping -D -c 100 10.1.1.1                                             │    │
│  │                                                                      │    │
│  │  Sample Output:                                                      │    │
│  │  ┌────────────────────────────────────────────────────────────┐     │    │
│  │  │ --- 10.1.1.1 ping statistics ---                           │     │    │
│  │  │ 100 packets transmitted, 100 received, 0% packet loss      │     │    │
│  │  │ rtt min/avg/max/mdev = 1.234/2.567/5.890/0.876 ms          │     │    │
│  │  └────────────────────────────────────────────────────────────┘     │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  Latency Thresholds:                                                         │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  ┌────────────────────────────────────────────────────────────┐     │    │
│  │  │ Application         Max Latency    Max Jitter              │     │    │
│  │  │ ───────────         ───────────    ──────────              │     │    │
│  │  │ VoIP                150 ms         30 ms                   │     │    │
│  │  │ Video conferencing  200 ms         50 ms                   │     │    │
│  │  │ Real-time gaming    50 ms          10 ms                   │     │    │
│  │  │ Web browsing        500 ms         N/A                     │     │    │
│  │  │ File transfer       N/A            N/A                     │     │    │
│  │  │ IoT sensors         1000 ms        N/A                     │     │    │
│  │  └────────────────────────────────────────────────────────────┘     │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  Jitter Testing:                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  # iPerf3 UDP jitter test                                            │    │
│  │  iperf3 -c 10.1.1.100 -u -b 10M -t 60                                │    │
│  │                                                                      │    │
│  │  Sample Output:                                                      │    │
│  │  ┌────────────────────────────────────────────────────────────┐     │    │
│  │  │ [ ID] Interval       Transfer    Bitrate    Jitter  Lost  │     │    │
│  │  │ [  5] 0.00-60.00 sec 71.5 MBytes 10.0 Mbits/sec 0.234 ms  │     │    │
│  │  │                                              0/5089 (0%)   │     │    │
│  │  └────────────────────────────────────────────────────────────┘     │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### DL.3 Roaming Testing

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    ROAMING TESTING                                           │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  Roaming Time Measurement:                                                   │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  Test Setup:                                                         │    │
│  │  1. Configure two APs with same SSID                                 │    │
│  │  2. Enable 802.11r, 802.11k, 802.11v                                 │    │
│  │  3. Start continuous ping from client                                │    │
│  │  4. Walk between AP coverage areas                                   │    │
│  │  5. Measure packet loss during roam                                  │    │
│  │                                                                      │    │
│  │  Expected Roaming Times:                                             │    │
│  │  ┌────────────────────────────────────────────────────────────┐     │    │
│  │  │ Roaming Type        Time            Packet Loss            │     │    │
│  │  │ ────────────        ────            ───────────            │     │    │
│  │  │ Full re-auth        500-2000 ms     5-20 packets           │     │    │
│  │  │ OKC                 50-100 ms       1-2 packets            │     │    │
│  │  │ 802.11r (Over-Air)  20-50 ms        0-1 packets            │     │    │
│  │  │ 802.11r (Over-DS)   10-30 ms        0 packets              │     │    │
│  │  │ WiFi 7 MLO          0 ms            0 packets              │     │    │
│  │  └────────────────────────────────────────────────────────────┘     │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  Roaming Test Script:                                                        │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  #!/bin/bash                                                         │    │
│  │  # roaming_test.sh                                                   │    │
│  │                                                                      │    │
│  │  TARGET="10.1.1.1"                                                   │    │
│  │  DURATION=300                                                        │    │
│  │  OUTPUT="roaming_test_$(date +%Y%m%d_%H%M%S).log"                    │    │
│  │                                                                      │    │
│  │  echo "Starting roaming test for $DURATION seconds"                  │    │
│  │  echo "Target: $TARGET"                                              │    │
│  │  echo "Output: $OUTPUT"                                              │    │
│  │                                                                      │    │
│  │  # Start ping with timestamps                                        │    │
│  │  ping -D -i 0.1 -c $((DURATION * 10)) $TARGET | while read line; do  │    │
│  │    # Get current BSSID                                               │    │
│  │    BSSID=$(iwconfig wlan0 2>/dev/null | grep "Access Point" | \      │    │
│  │            awk '{print $6}')                                         │    │
│  │    echo "$(date +%H:%M:%S.%3N) BSSID=$BSSID $line"                   │    │
│  │  done | tee $OUTPUT                                                  │    │
│  │                                                                      │    │
│  │  # Analyze results                                                   │    │
│  │  echo ""                                                             │    │
│  │  echo "=== Results ==="                                              │    │
│  │  grep -c "time=" $OUTPUT | xargs echo "Successful pings:"           │    │
│  │  grep -c "Request timeout" $OUTPUT | xargs echo "Timeouts:"         │    │
│  │  grep "BSSID=" $OUTPUT | awk '{print $2}' | sort | uniq -c          │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Appendix DM: Regulatory Compliance

### DM.1 Regional Regulations

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    REGIONAL REGULATIONS                                      │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  Regulatory Bodies:                                                          │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  ┌────────────────────────────────────────────────────────────┐     │    │
│  │  │ Region          Body        Key Regulations                │     │    │
│  │  │ ──────          ────        ───────────────                │     │    │
│  │  │ United States   FCC         Part 15, Part 18               │     │    │
│  │  │ Europe          ETSI        EN 300 328, EN 301 893         │     │    │
│  │  │ Canada          ISED        RSS-247, RSS-102               │     │    │
│  │  │ Japan           MIC         ARIB STD-T66, T71              │     │    │
│  │  │ Australia       ACMA        AS/NZS 4268                    │     │    │
│  │  │ China           MIIT        SRRC certification             │     │    │
│  │  │ India           WPC         ETA certification              │     │    │
│  │  │ Brazil          ANATEL      Resolution 680                 │     │    │
│  │  └────────────────────────────────────────────────────────────┘     │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  Power Limits by Region:                                                     │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  2.4 GHz Band:                                                       │    │
│  │  ┌────────────────────────────────────────────────────────────┐     │    │
│  │  │ Region          Max EIRP    Notes                          │     │    │
│  │  │ ──────          ────────    ─────                          │     │    │
│  │  │ US (FCC)        36 dBm      Point-to-point higher          │     │    │
│  │  │ Europe (ETSI)   20 dBm      100 mW                         │     │    │
│  │  │ Japan           10 mW/MHz   Varies by channel              │     │    │
│  │  │ Australia       36 dBm      Similar to FCC                 │     │    │
│  │  └────────────────────────────────────────────────────────────┘     │    │
│  │                                                                      │    │
│  │  5 GHz Band:                                                         │    │
│  │  ┌────────────────────────────────────────────────────────────┐     │    │
│  │  │ Region          UNII-1      UNII-2      UNII-3             │     │    │
│  │  │ ──────          ──────      ──────      ──────             │     │    │
│  │  │ US (FCC)        23 dBm      24 dBm      30 dBm             │     │    │
│  │  │ Europe (ETSI)   23 dBm      23 dBm      30 dBm             │     │    │
│  │  │ Japan           23 dBm      23 dBm      N/A                │     │    │
│  │  └────────────────────────────────────────────────────────────┘     │    │
│  │                                                                      │    │
│  │  6 GHz Band:                                                         │    │
│  │  ┌────────────────────────────────────────────────────────────┐     │    │
│  │  │ Region          LPI (Indoor)    SP (Standard Power)        │     │    │
│  │  │ ──────          ────────────    ───────────────────        │     │    │
│  │  │ US (FCC)        21 dBm          36 dBm (AFC required)      │     │    │
│  │  │ Europe (ETSI)   23 dBm          In development             │     │    │
│  │  │ Canada          21 dBm          36 dBm (AFC required)      │     │    │
│  │  └────────────────────────────────────────────────────────────┘     │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### DM.2 DFS Requirements

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    DFS REQUIREMENTS                                          │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  DFS Overview:                                                               │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  Dynamic Frequency Selection (DFS) is required to:                   │    │
│  │  - Detect radar signals                                              │    │
│  │  - Vacate channel when radar detected                                │    │
│  │  - Avoid interference with weather/military radar                    │    │
│  │                                                                      │    │
│  │  DFS Channels (5 GHz):                                               │    │
│  │  ┌────────────────────────────────────────────────────────────┐     │    │
│  │  │ Band        Channels                                       │     │    │
│  │  │ ────        ────────                                       │     │    │
│  │  │ UNII-2A     52, 56, 60, 64                                 │     │    │
│  │  │ UNII-2C     100, 104, 108, 112, 116, 120, 124, 128,        │     │    │
│  │  │             132, 136, 140, 144                             │     │    │
│  │  └────────────────────────────────────────────────────────────┘     │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  DFS Timing Requirements:                                                    │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  ┌────────────────────────────────────────────────────────────┐     │    │
│  │  │ Parameter               Value                              │     │    │
│  │  │ ─────────               ─────                              │     │    │
│  │  │ CAC (Channel Avail.)    60 seconds (10 min for weather)    │     │    │
│  │  │ Channel Move Time       10 seconds                         │     │    │
│  │  │ Non-Occupancy Period    30 minutes                         │     │    │
│  │  │ In-Service Monitoring   Continuous                         │     │    │
│  │  └────────────────────────────────────────────────────────────┘     │    │
│  │                                                                      │    │
│  │  DFS State Machine:                                                  │    │
│  │  ┌────────────────────────────────────────────────────────────┐     │    │
│  │  │                                                            │     │    │
│  │  │  [IDLE] ──(select DFS channel)──> [CAC]                    │     │    │
│  │  │                                      │                     │     │    │
│  │  │                          (60 sec, no radar)                │     │    │
│  │  │                                      ▼                     │     │    │
│  │  │  [NOL] <──(radar detected)── [OPERATIONAL]                 │     │    │
│  │  │    │                                                       │     │    │
│  │  │    └──(30 min)──> [AVAILABLE]                              │     │    │
│  │  │                                                            │     │    │
│  │  └────────────────────────────────────────────────────────────┘     │    │
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
| 3.1 | 2026-01-08 | Auto-generated | Added WiFi 7 MLO, puncturing, 4K-QAM, multi-RU, enhanced security |
| 3.2 | 2026-01-08 | Auto-generated | Added FILS, DPP, enterprise security, certificate management |
| 3.3 | 2026-01-08 | Auto-generated | Added power management, airtime fairness, channel utilization |
| 3.4 | 2026-01-08 | Auto-generated | Added client steering, band selection, load balancing algorithms |
| 3.5 | 2026-01-08 | Auto-generated | Added mesh networking, WDS, repeater modes, backhaul optimization |
| 3.6 | 2026-01-08 | Auto-generated | Added roaming protocols, 802.11k/v/r deep dive, seamless handoff |
| 3.7 | 2026-01-08 | Auto-generated | Added DHCP deep dive, DNS, mDNS, service discovery |
| 3.8 | 2026-01-08 | Auto-generated | Added firewall policies, ACLs, traffic filtering, NAT |
| 3.9 | 2026-01-08 | Auto-generated | Added IoT device profiling, device fingerprinting, MAC randomization |
| 4.0 | 2026-01-08 | Auto-generated | Added CLI command reference, API reference, automation |
| 4.1 | 2026-01-08 | Auto-generated | Added network automation, scripting, integration examples |
| 4.2 | 2026-01-08 | Auto-generated | Added site survey, capacity planning, deployment best practices |
| 4.3 | 2026-01-08 | Auto-generated | Added troubleshooting runbook, migration guide, vendor interoperability |

---

## Appendix DN: Troubleshooting Runbook

### DN.1 Connection Failures

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    CONNECTION FAILURE TROUBLESHOOTING                        │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  Symptom: Client Cannot See SSID                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  Step 1: Verify SSID is enabled                                      │    │
│  │  # show ssid Corporate                                               │    │
│  │  Expected: Status = Enabled                                          │    │
│  │                                                                      │    │
│  │  Step 2: Check radio status                                          │    │
│  │  # show radio all                                                    │    │
│  │  Expected: Radio = Up, Channel = Valid                               │    │
│  │                                                                      │    │
│  │  Step 3: Verify beacon transmission                                  │    │
│  │  # debug wireless beacon                                             │    │
│  │  Expected: Beacons being transmitted                                 │    │
│  │                                                                      │    │
│  │  Step 4: Check client band support                                   │    │
│  │  - 5 GHz only SSID with 2.4 GHz only client                          │    │
│  │  - 6 GHz SSID with non-WiFi 6E client                                │    │
│  │                                                                      │    │
│  │  Step 5: Check hidden SSID setting                                   │    │
│  │  # show ssid Corporate | include broadcast                          │    │
│  │  If hidden, client must manually enter SSID                          │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  Symptom: Authentication Failure                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  For PSK Authentication:                                             │    │
│  │  Step 1: Verify password is correct                                  │    │
│  │  Step 2: Check security mode match                                   │    │
│  │          (WPA2 vs WPA3, TKIP vs CCMP)                                │    │
│  │  Step 3: Check PMF settings                                          │    │
│  │          (Required vs Optional vs Disabled)                          │    │
│  │                                                                      │    │
│  │  For 802.1X Authentication:                                          │    │
│  │  Step 1: Check RADIUS server reachability                            │    │
│  │  # ping 10.1.1.100                                                   │    │
│  │                                                                      │    │
│  │  Step 2: Verify RADIUS shared secret                                 │    │
│  │  # debug radius authentication                                       │    │
│  │  Look for: "Invalid authenticator" = wrong secret                    │    │
│  │                                                                      │    │
│  │  Step 3: Check certificate validity                                  │    │
│  │  # show certificate all                                              │    │
│  │  Verify: Not expired, correct CA chain                               │    │
│  │                                                                      │    │
│  │  Step 4: Check EAP method support                                    │    │
│  │  # show ssid Corporate | include eap                                 │    │
│  │  Verify client supports configured EAP method                        │    │
│  │                                                                      │    │
│  │  Step 5: Check RADIUS logs                                           │    │
│  │  # show log | include RADIUS                                         │    │
│  │  Look for: Access-Reject, timeout, error messages                    │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  Symptom: Association Failure                                                │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  Step 1: Check client limit                                          │    │
│  │  # show client count                                                 │    │
│  │  Compare to: max-clients setting                                     │    │
│  │                                                                      │    │
│  │  Step 2: Check MAC filtering                                         │    │
│  │  # show mac-filter                                                   │    │
│  │  Verify client MAC is allowed                                        │    │
│  │                                                                      │    │
│  │  Step 3: Check capability mismatch                                   │    │
│  │  # debug wireless association                                        │    │
│  │  Look for: Unsupported rates, HT/VHT/HE capability issues            │    │
│  │                                                                      │    │
│  │  Step 4: Check for blacklist                                         │    │
│  │  # show client blacklist                                             │    │
│  │  Remove if necessary: clear client blacklist <mac>                   │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### DN.2 Performance Issues

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    PERFORMANCE TROUBLESHOOTING                               │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  Symptom: Slow Throughput                                                    │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  Step 1: Check signal strength                                       │    │
│  │  # show client detail <mac>                                          │    │
│  │  Target: RSSI > -67 dBm                                              │    │
│  │                                                                      │    │
│  │  Step 2: Check channel utilization                                   │    │
│  │  # show radio statistics                                             │    │
│  │  Target: < 50% utilization                                           │    │
│  │                                                                      │    │
│  │  Step 3: Check for interference                                      │    │
│  │  # show spectrum analysis                                            │    │
│  │  Look for: Non-WiFi interference, radar                              │    │
│  │                                                                      │    │
│  │  Step 4: Check client capabilities                                   │    │
│  │  # show client detail <mac> | include capability                     │    │
│  │  Verify: Spatial streams, channel width support                      │    │
│  │                                                                      │    │
│  │  Step 5: Check rate limiting                                         │    │
│  │  # show rate-limit                                                   │    │
│  │  Verify: Not artificially limited                                    │    │
│  │                                                                      │    │
│  │  Step 6: Check retry rate                                            │    │
│  │  # show client statistics <mac>                                      │    │
│  │  Target: < 10% retry rate                                            │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  Symptom: High Latency                                                       │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  Step 1: Check channel utilization                                   │    │
│  │  High utilization = contention delays                                │    │
│  │                                                                      │    │
│  │  Step 2: Check QoS settings                                          │    │
│  │  # show qos                                                          │    │
│  │  Verify WMM is enabled                                               │    │
│  │                                                                      │    │
│  │  Step 3: Check power save mode                                       │    │
│  │  # show client detail <mac> | include power                          │    │
│  │  Power save can add latency                                          │    │
│  │                                                                      │    │
│  │  Step 4: Check backhaul                                              │    │
│  │  # ping -c 100 <gateway>                                             │    │
│  │  Verify wired network is not the bottleneck                          │    │
│  │                                                                      │    │
│  │  Step 5: Check for bufferbloat                                       │    │
│  │  Run: DSLReports speed test                                          │    │
│  │  Look for: High latency under load                                   │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  Symptom: Intermittent Disconnections                                        │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  Step 1: Check for roaming issues                                    │    │
│  │  # show client history <mac>                                         │    │
│  │  Look for: Frequent AP changes                                       │    │
│  │                                                                      │    │
│  │  Step 2: Check for DFS events                                        │    │
│  │  # show log | include DFS                                            │    │
│  │  Radar detection causes channel change                               │    │
│  │                                                                      │    │
│  │  Step 3: Check for deauth attacks                                    │    │
│  │  # show wids events                                                  │    │
│  │  Look for: Deauth flood, disassoc flood                              │    │
│  │                                                                      │    │
│  │  Step 4: Check client driver issues                                  │    │
│  │  Update client WiFi drivers                                          │    │
│  │  Check for known issues with client device                           │    │
│  │                                                                      │    │
│  │  Step 5: Check for interference                                      │    │
│  │  # show spectrum analysis                                            │    │
│  │  Microwave ovens, Bluetooth, etc.                                    │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### DN.3 DHCP Issues

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    DHCP TROUBLESHOOTING                                      │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  Symptom: Client Not Getting IP Address                                      │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  Step 1: Verify DHCP server is reachable                             │    │
│  │  # ping 10.1.1.1                                                     │    │
│  │                                                                      │    │
│  │  Step 2: Check VLAN configuration                                    │    │
│  │  # show vlan                                                         │    │
│  │  Verify client VLAN has DHCP relay or local server                   │    │
│  │                                                                      │    │
│  │  Step 3: Check DHCP relay configuration                              │    │
│  │  # show dhcp-relay                                                   │    │
│  │  Verify helper address is correct                                    │    │
│  │                                                                      │    │
│  │  Step 4: Check DHCP pool exhaustion                                  │    │
│  │  # show dhcp pool                                                    │    │
│  │  Verify available addresses                                          │    │
│  │                                                                      │    │
│  │  Step 5: Capture DHCP traffic                                        │    │
│  │  # debug dhcp                                                        │    │
│  │  Look for: DISCOVER, OFFER, REQUEST, ACK                             │    │
│  │                                                                      │    │
│  │  Step 6: Check for duplicate IP                                      │    │
│  │  # show arp                                                          │    │
│  │  Look for: Multiple MACs with same IP                                │    │
│  │                                                                      │    │
│  │  Common Issues:                                                      │    │
│  │  ┌────────────────────────────────────────────────────────────┐     │    │
│  │  │ Issue                   Solution                           │     │    │
│  │  │ ─────                   ────────                           │     │    │
│  │  │ No DISCOVER seen        Client issue, check WiFi driver    │     │    │
│  │  │ DISCOVER but no OFFER   DHCP server issue, check server    │     │    │
│  │  │ OFFER but no REQUEST    Client rejecting offer             │     │    │
│  │  │ REQUEST but no ACK      Server rejecting request           │     │    │
│  │  │ ACK but no IP           Client not applying IP             │     │    │
│  │  └────────────────────────────────────────────────────────────┘     │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Appendix DO: Migration Guide

### DO.1 Controller Migration

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    CONTROLLER MIGRATION                                      │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  Pre-Migration Checklist:                                                    │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  □ Document current configuration                                    │    │
│  │    - SSID settings                                                   │    │
│  │    - Security policies                                               │    │
│  │    - RADIUS servers                                                  │    │
│  │    - VLAN mappings                                                   │    │
│  │    - RF profiles                                                     │    │
│  │                                                                      │    │
│  │  □ Export configuration backup                                       │    │
│  │    # copy running-config tftp://backup-server/config.txt             │    │
│  │                                                                      │    │
│  │  □ Document AP inventory                                             │    │
│  │    - AP names and locations                                          │    │
│  │    - MAC addresses                                                   │    │
│  │    - IP addresses                                                    │    │
│  │    - Firmware versions                                               │    │
│  │                                                                      │    │
│  │  □ Plan maintenance window                                           │    │
│  │    - Notify users                                                    │    │
│  │    - Schedule off-hours                                              │    │
│  │    - Prepare rollback plan                                           │    │
│  │                                                                      │    │
│  │  □ Test new controller                                               │    │
│  │    - Verify connectivity                                             │    │
│  │    - Test RADIUS integration                                         │    │
│  │    - Validate VLAN configuration                                     │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  Migration Steps:                                                            │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  Phase 1: Preparation                                                │    │
│  │  1. Deploy new controller in parallel                                │    │
│  │  2. Configure identical SSIDs and policies                           │    │
│  │  3. Test with pilot APs                                              │    │
│  │                                                                      │    │
│  │  Phase 2: Staged Migration                                           │    │
│  │  1. Migrate APs in groups (by floor, building)                       │    │
│  │  2. Verify client connectivity after each group                      │    │
│  │  3. Monitor for issues                                               │    │
│  │                                                                      │    │
│  │  Phase 3: Cutover                                                    │    │
│  │  1. Migrate remaining APs                                            │    │
│  │  2. Update DNS/DHCP if needed                                        │    │
│  │  3. Decommission old controller                                      │    │
│  │                                                                      │    │
│  │  Phase 4: Validation                                                 │    │
│  │  1. Verify all APs connected                                         │    │
│  │  2. Test client connectivity                                         │    │
│  │  3. Verify roaming                                                   │    │
│  │  4. Check monitoring/alerting                                        │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### DO.2 Security Mode Migration

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    SECURITY MODE MIGRATION                                   │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  WPA2 to WPA3 Migration:                                                     │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  Phase 1: Assessment                                                 │    │
│  │  1. Inventory client devices                                         │    │
│  │  2. Identify WPA3-capable devices                                    │    │
│  │  3. Plan for legacy device support                                   │    │
│  │                                                                      │    │
│  │  Phase 2: Transition Mode                                            │    │
│  │  Configure WPA3-Transition (WPA2/WPA3 mixed mode):                   │    │
│  │  ┌────────────────────────────────────────────────────────────┐     │    │
│  │  │ ssid Corporate                                             │     │    │
│  │  │   security wpa3-transition                                 │     │    │
│  │  │   wpa2-psk passphrase "SecurePassword123"                  │     │    │
│  │  │   sae passphrase "SecurePassword123"                       │     │    │
│  │  │   pmf optional                                             │     │    │
│  │  └────────────────────────────────────────────────────────────┘     │    │
│  │                                                                      │    │
│  │  Phase 3: Monitor                                                    │    │
│  │  1. Track WPA2 vs WPA3 connections                                   │    │
│  │  2. Identify remaining WPA2 clients                                  │    │
│  │  3. Plan device upgrades                                             │    │
│  │                                                                      │    │
│  │  Phase 4: WPA3-Only                                                  │    │
│  │  When all clients support WPA3:                                      │    │
│  │  ┌────────────────────────────────────────────────────────────┐     │    │
│  │  │ ssid Corporate                                             │     │    │
│  │  │   security wpa3-personal                                   │     │    │
│  │  │   sae passphrase "SecurePassword123"                       │     │    │
│  │  │   pmf required                                             │     │    │
│  │  └────────────────────────────────────────────────────────────┘     │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  PSK to 802.1X Migration:                                                    │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  Phase 1: Deploy RADIUS Infrastructure                               │    │
│  │  1. Deploy RADIUS servers                                            │    │
│  │  2. Configure user database (AD, LDAP)                               │    │
│  │  3. Deploy certificates                                              │    │
│  │                                                                      │    │
│  │  Phase 2: Create New SSID                                            │    │
│  │  1. Create 802.1X SSID alongside PSK SSID                            │    │
│  │  2. Configure same VLAN                                              │    │
│  │  3. Test with pilot users                                            │    │
│  │                                                                      │    │
│  │  Phase 3: User Migration                                             │    │
│  │  1. Deploy certificates to devices                                   │    │
│  │  2. Configure supplicant settings                                    │    │
│  │  3. Migrate users in groups                                          │    │
│  │                                                                      │    │
│  │  Phase 4: Decommission PSK                                           │    │
│  │  1. Verify all users on 802.1X                                       │    │
│  │  2. Disable PSK SSID                                                 │    │
│  │  3. Remove PSK SSID                                                  │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Appendix DP: Vendor Interoperability

### DP.1 Multi-Vendor Environments

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    MULTI-VENDOR INTEROPERABILITY                             │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  Common Interoperability Issues:                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  ┌────────────────────────────────────────────────────────────┐     │    │
│  │  │ Issue                   Cause                   Solution   │     │    │
│  │  │ ─────                   ─────                   ────────   │     │    │
│  │  │ Roaming failures        Different FT impl.      Use OKC    │     │    │
│  │  │ PMK sync issues         Proprietary sync        Standard   │     │    │
│  │  │ RADIUS attributes       Vendor-specific         Map attrs  │     │    │
│  │  │ QoS marking             Different defaults      Standardize│     │    │
│  │  │ VLAN assignment         Different methods       Use RADIUS │     │    │
│  │  └────────────────────────────────────────────────────────────┘     │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  802.11r Interoperability:                                                   │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  Requirements for cross-vendor 802.11r:                              │    │
│  │  1. Same Mobility Domain ID                                          │    │
│  │  2. Same R0KH-ID format                                              │    │
│  │  3. Compatible R1KH configuration                                    │    │
│  │  4. Same PMK-R0 key derivation                                       │    │
│  │                                                                      │    │
│  │  Configuration Example:                                              │    │
│  │  ┌────────────────────────────────────────────────────────────┐     │    │
│  │  │ # Vendor A AP                                              │     │    │
│  │  │ mobility-domain 0x1234                                     │     │    │
│  │  │ r0kh-id ap1.company.com                                    │     │    │
│  │  │ r1kh 00:11:22:33:44:55 ap2.company.com <key>               │     │    │
│  │  │                                                            │     │    │
│  │  │ # Vendor B AP                                              │     │    │
│  │  │ mobility-domain 0x1234                                     │     │    │
│  │  │ r0kh-id ap2.company.com                                    │     │    │
│  │  │ r1kh 00:11:22:33:44:66 ap1.company.com <key>               │     │    │
│  │  └────────────────────────────────────────────────────────────┘     │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  RADIUS Attribute Mapping:                                                   │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  ┌────────────────────────────────────────────────────────────┐     │    │
│  │  │ Function          Standard Attr    Vendor A    Vendor B    │     │    │
│  │  │ ────────          ─────────────    ────────    ────────    │     │    │
│  │  │ VLAN              Tunnel-Pvt-Grp   Same        Same        │     │    │
│  │  │ Bandwidth         N/A              VSA 1       VSA 100     │     │    │
│  │  │ ACL               Filter-Id        Same        VSA 101     │     │    │
│  │  │ Session timeout   Session-Timeout  Same        Same        │     │    │
│  │  │ Role              Class            VSA 2       VSA 102     │     │    │
│  │  └────────────────────────────────────────────────────────────┘     │    │
│  │                                                                      │    │
│  │  Solution: Use RADIUS proxy to translate attributes                  │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### DP.2 Client Compatibility

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    CLIENT COMPATIBILITY                                      │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  Operating System Support:                                                   │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  ┌────────────────────────────────────────────────────────────┐     │    │
│  │  │ Feature         Windows   macOS    iOS      Android        │     │    │
│  │  │ ───────         ───────   ─────    ───      ───────        │     │    │
│  │  │ WPA3-Personal   10+       10.15+   13+      10+            │     │    │
│  │  │ WPA3-Enterprise 10+       10.15+   13+      10+            │     │    │
│  │  │ OWE             10+       10.15+   13+      10+            │     │    │
│  │  │ 802.11r         7+        10.13+   6+       4.1+           │     │    │
│  │  │ 802.11k         10+       10.13+   6+       4.1+           │     │    │
│  │  │ 802.11v         10+       10.13+   6+       4.1+           │     │    │
│  │  │ WiFi 6          10+       11+      14+      10+            │     │    │
│  │  │ WiFi 6E         11+       12+      15+      12+            │     │    │
│  │  │ WiFi 7          11+       14+      17+      14+            │     │    │
│  │  └────────────────────────────────────────────────────────────┘     │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  Known Client Issues:                                                        │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  Windows:                                                            │    │
│  │  - Some Intel drivers have 802.11r issues                            │    │
│  │  - WPA3 requires specific driver versions                            │    │
│  │  - Group Policy can override WiFi settings                           │    │
│  │                                                                      │    │
│  │  macOS:                                                              │    │
│  │  - Aggressive roaming can cause issues                               │    │
│  │  - Certificate trust requires user interaction                       │    │
│  │  - Power save can affect VoIP                                        │    │
│  │                                                                      │    │
│  │  iOS:                                                                │    │
│  │  - MAC randomization affects tracking                                │    │
│  │  - Captive portal detection can be aggressive                        │    │
│  │  - Background app restrictions affect connectivity                   │    │
│  │                                                                      │    │
│  │  Android:                                                            │    │
│  │  - Fragmented driver support                                         │    │
│  │  - Vendor-specific WiFi implementations                              │    │
│  │  - Battery optimization can disconnect WiFi                          │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Appendix DQ: Security Hardening

### DQ.1 AP Security Hardening

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    AP SECURITY HARDENING                                     │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  Management Access:                                                          │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  # Disable HTTP, use HTTPS only                                      │    │
│  │  no ip http server                                                   │    │
│  │  ip http secure-server                                               │    │
│  │                                                                      │    │
│  │  # Use strong TLS                                                    │    │
│  │  ip http tls-version 1.2                                             │    │
│  │  ip http cipher-suite strong                                         │    │
│  │                                                                      │    │
│  │  # Disable Telnet, use SSH only                                      │    │
│  │  no telnet server                                                    │    │
│  │  ssh server enable                                                   │    │
│  │  ssh server version 2                                                │    │
│  │                                                                      │    │
│  │  # Configure management ACL                                          │    │
│  │  ip access-list management                                           │    │
│  │    permit 10.1.1.0/24                                                │    │
│  │    deny any                                                          │    │
│  │                                                                      │    │
│  │  # Apply to management interface                                     │    │
│  │  interface management                                                │    │
│  │    ip access-group management in                                     │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  Authentication:                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  # Use RADIUS for admin authentication                               │    │
│  │  aaa authentication login default group radius local                 │    │
│  │  aaa authorization exec default group radius local                   │    │
│  │                                                                      │    │
│  │  # Configure local fallback with strong password                     │    │
│  │  username admin privilege 15 secret 0 <strong-password>              │    │
│  │                                                                      │    │
│  │  # Enable login delay                                                │    │
│  │  login delay 3                                                       │    │
│  │  login block-for 300 attempts 5 within 60                            │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  Logging and Monitoring:                                                     │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  # Enable syslog                                                     │    │
│  │  logging host 10.1.1.200                                             │    │
│  │  logging trap informational                                          │    │
│  │  logging source-interface management                                 │    │
│  │                                                                      │    │
│  │  # Enable SNMP v3 only                                               │    │
│  │  no snmp-server community                                            │    │
│  │  snmp-server group admin v3 priv                                     │    │
│  │  snmp-server user snmpuser admin v3 auth sha <auth-pass> \           │    │
│  │    priv aes 256 <priv-pass>                                          │    │
│  │                                                                      │    │
│  │  # Enable NTP authentication                                         │    │
│  │  ntp authentication enable                                           │    │
│  │  ntp authentication-key 1 md5 <ntp-key>                              │    │
│  │  ntp trusted-key 1                                                   │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### DQ.2 Wireless Security Hardening

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    WIRELESS SECURITY HARDENING                               │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  SSID Security:                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  # Use WPA3 with PMF required                                        │    │
│  │  ssid Corporate                                                      │    │
│  │    security wpa3-enterprise                                          │    │
│  │    pmf required                                                      │    │
│  │    fast-transition enable                                            │    │
│  │    okc enable                                                        │    │
│  │                                                                      │    │
│  │  # Disable legacy protocols                                          │    │
│  │  no security wpa                                                     │    │
│  │  no security wep                                                     │    │
│  │  no security open                                                    │    │
│  │                                                                      │    │
│  │  # Enable client isolation for guest                                 │    │
│  │  ssid Guest                                                          │    │
│  │    client-isolation enable                                           │    │
│  │    local-switching disable                                           │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  WIDS/WIPS:                                                                  │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  # Enable wireless intrusion detection                               │    │
│  │  wids enable                                                         │    │
│  │                                                                      │    │
│  │  # Configure detection policies                                      │    │
│  │  wids policy                                                         │    │
│  │    detect rogue-ap enable                                            │    │
│  │    detect deauth-flood enable threshold 100                          │    │
│  │    detect disassoc-flood enable threshold 100                        │    │
│  │    detect auth-flood enable threshold 100                            │    │
│  │    detect probe-flood enable threshold 1000                          │    │
│  │    detect evil-twin enable                                           │    │
│  │    detect honeypot enable                                            │    │
│  │                                                                      │    │
│  │  # Configure containment (use with caution)                          │    │
│  │  wids containment                                                    │    │
│  │    contain rogue-ap enable                                           │    │
│  │    contain evil-twin enable                                          │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  Rogue AP Detection:                                                         │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  # Configure rogue AP classification                                 │    │
│  │  rogue-ap classification                                             │    │
│  │    friendly ssid-match "Corporate*"                                  │    │
│  │    friendly mac-oui 00:11:22                                         │    │
│  │    malicious ssid-match "Corporate"                                  │    │
│  │    malicious signal-strength > -50                                   │    │
│  │                                                                      │    │
│  │  # Configure alerting                                                │    │
│  │  rogue-ap alert                                                      │    │
│  │    email admin@company.com                                           │    │
│  │    syslog enable                                                     │    │
│  │    snmp-trap enable                                                  │    │
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
| 3.1 | 2026-01-08 | Auto-generated | Added WiFi 7 MLO, puncturing, 4K-QAM, multi-RU, enhanced security |
| 3.2 | 2026-01-08 | Auto-generated | Added FILS, DPP, enterprise security, certificate management |
| 3.3 | 2026-01-08 | Auto-generated | Added power management, airtime fairness, channel utilization |
| 3.4 | 2026-01-08 | Auto-generated | Added client steering, band selection, load balancing algorithms |
| 3.5 | 2026-01-08 | Auto-generated | Added mesh networking, WDS, repeater modes, backhaul optimization |
| 3.6 | 2026-01-08 | Auto-generated | Added roaming protocols, 802.11k/v/r deep dive, seamless handoff |
| 3.7 | 2026-01-08 | Auto-generated | Added DHCP deep dive, DNS, mDNS, service discovery |
| 3.8 | 2026-01-08 | Auto-generated | Added firewall policies, ACLs, traffic filtering, NAT |
| 3.9 | 2026-01-08 | Auto-generated | Added IoT device profiling, device fingerprinting, MAC randomization |
| 4.0 | 2026-01-08 | Auto-generated | Added CLI command reference, API reference, automation |
| 4.1 | 2026-01-08 | Auto-generated | Added network automation, scripting, integration examples |
| 4.2 | 2026-01-08 | Auto-generated | Added site survey, capacity planning, deployment best practices |
| 4.3 | 2026-01-08 | Auto-generated | Added troubleshooting runbook, migration guide, vendor interoperability |
| 4.4 | 2026-01-08 | Auto-generated | Added high availability, disaster recovery, backup strategies |

---

## Appendix DR: High Availability

### DR.1 Controller High Availability

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    CONTROLLER HIGH AVAILABILITY                              │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  HA Architectures:                                                           │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  Active-Standby:                                                     │    │
│  │  ┌────────────────────────────────────────────────────────────┐     │    │
│  │  │                                                            │     │    │
│  │  │  ┌─────────────┐         ┌─────────────┐                   │     │    │
│  │  │  │  Primary    │◄───────►│  Secondary  │                   │     │    │
│  │  │  │ Controller  │  Sync   │ Controller  │                   │     │    │
│  │  │  │  (Active)   │         │  (Standby)  │                   │     │    │
│  │  │  └──────┬──────┘         └──────┬──────┘                   │     │    │
│  │  │         │                       │                          │     │    │
│  │  │         └───────────┬───────────┘                          │     │    │
│  │  │                     │                                      │     │    │
│  │  │              ┌──────┴──────┐                               │     │    │
│  │  │              │    APs      │                               │     │    │
│  │  │              └─────────────┘                               │     │    │
│  │  │                                                            │     │    │
│  │  └────────────────────────────────────────────────────────────┘     │    │
│  │                                                                      │    │
│  │  Active-Active:                                                      │    │
│  │  ┌────────────────────────────────────────────────────────────┐     │    │
│  │  │                                                            │     │    │
│  │  │  ┌─────────────┐         ┌─────────────┐                   │     │    │
│  │  │  │ Controller  │◄───────►│ Controller  │                   │     │    │
│  │  │  │     A       │  Sync   │     B       │                   │     │    │
│  │  │  │  (Active)   │         │  (Active)   │                   │     │    │
│  │  │  └──────┬──────┘         └──────┬──────┘                   │     │    │
│  │  │         │                       │                          │     │    │
│  │  │    ┌────┴────┐             ┌────┴────┐                     │     │    │
│  │  │    │  APs    │             │  APs    │                     │     │    │
│  │  │    │ Group A │             │ Group B │                     │     │    │
│  │  │    └─────────┘             └─────────┘                     │     │    │
│  │  │                                                            │     │    │
│  │  └────────────────────────────────────────────────────────────┘     │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  Configuration:                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  # Primary Controller                                                │    │
│  │  high-availability                                                   │    │
│  │    mode active-standby                                               │    │
│  │    role primary                                                      │    │
│  │    peer-ip 10.1.1.2                                                  │    │
│  │    virtual-ip 10.1.1.100                                             │    │
│  │    heartbeat-interval 1                                              │    │
│  │    failover-threshold 3                                              │    │
│  │    preempt enable                                                    │    │
│  │    sync-interval 60                                                  │    │
│  │                                                                      │    │
│  │  # Secondary Controller                                              │    │
│  │  high-availability                                                   │    │
│  │    mode active-standby                                               │    │
│  │    role secondary                                                    │    │
│  │    peer-ip 10.1.1.1                                                  │    │
│  │    virtual-ip 10.1.1.100                                             │    │
│  │    heartbeat-interval 1                                              │    │
│  │    failover-threshold 3                                              │    │
│  │    preempt enable                                                    │    │
│  │    sync-interval 60                                                  │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  Failover Behavior:                                                          │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  ┌────────────────────────────────────────────────────────────┐     │    │
│  │  │ Event                   Action                             │     │    │
│  │  │ ─────                   ──────                             │     │    │
│  │  │ Primary failure         Secondary becomes active           │     │    │
│  │  │ Primary recovery        Preempt (if enabled)               │     │    │
│  │  │ Split-brain             Use tiebreaker (priority)          │     │    │
│  │  │ Network partition       APs stay with reachable controller │     │    │
│  │  └────────────────────────────────────────────────────────────┘     │    │
│  │                                                                      │    │
│  │  Failover Timeline:                                                  │    │
│  │  ┌────────────────────────────────────────────────────────────┐     │    │
│  │  │                                                            │     │    │
│  │  │  T=0s     Primary fails                                    │     │    │
│  │  │  T=1s     Heartbeat missed (1)                             │     │    │
│  │  │  T=2s     Heartbeat missed (2)                             │     │    │
│  │  │  T=3s     Heartbeat missed (3) - threshold reached         │     │    │
│  │  │  T=3.5s   Secondary declares primary dead                  │     │    │
│  │  │  T=4s     Secondary becomes active                         │     │    │
│  │  │  T=5s     APs reconnect to secondary                       │     │    │
│  │  │  T=10s    Full service restored                            │     │    │
│  │  │                                                            │     │    │
│  │  └────────────────────────────────────────────────────────────┘     │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### DR.2 AP Survivability

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    AP SURVIVABILITY                                          │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  Controller-Less Operation:                                                  │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  When controller is unreachable, APs can:                            │    │
│  │  - Continue serving existing clients                                 │    │
│  │  - Accept new client connections (with cached config)                │    │
│  │  - Perform local authentication (if configured)                      │    │
│  │  - Maintain roaming within local cluster                             │    │
│  │                                                                      │    │
│  │  Configuration:                                                      │    │
│  │  ┌────────────────────────────────────────────────────────────┐     │    │
│  │  │ ap-survivability                                           │     │    │
│  │  │   enable                                                   │     │    │
│  │  │   cache-timeout 86400                                      │     │    │
│  │  │   local-auth enable                                        │     │    │
│  │  │   local-auth-cache 1000                                    │     │    │
│  │  │   local-switching enable                                   │     │    │
│  │  └────────────────────────────────────────────────────────────┘     │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  Local Authentication Cache:                                                 │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  Cached Information:                                                 │    │
│  │  - User credentials (hashed)                                         │    │
│  │  - VLAN assignments                                                  │    │
│  │  - Role/policy assignments                                           │    │
│  │  - Session parameters                                                │    │
│  │                                                                      │    │
│  │  Cache Behavior:                                                     │    │
│  │  ┌────────────────────────────────────────────────────────────┐     │    │
│  │  │ Scenario                Action                             │     │    │
│  │  │ ────────                ──────                             │     │    │
│  │  │ User in cache           Authenticate locally               │     │    │
│  │  │ User not in cache       Deny (or allow with default role)  │     │    │
│  │  │ Cache expired           Deny (or allow with default role)  │     │    │
│  │  │ Controller restored     Sync cache, re-authenticate        │     │    │
│  │  └────────────────────────────────────────────────────────────┘     │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### DR.3 Disaster Recovery

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    DISASTER RECOVERY                                         │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  Backup Strategy:                                                            │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  ┌────────────────────────────────────────────────────────────┐     │    │
│  │  │ Backup Type         Frequency    Retention    Location     │     │    │
│  │  │ ───────────         ─────────    ─────────    ────────     │     │    │
│  │  │ Full config         Daily        30 days      Off-site     │     │    │
│  │  │ Incremental         Hourly       7 days       Local        │     │    │
│  │  │ AP firmware         Per version  Indefinite   Repository   │     │    │
│  │  │ Certificates        Monthly      1 year       Secure vault │     │    │
│  │  │ RADIUS config       Daily        30 days      Off-site     │     │    │
│  │  └────────────────────────────────────────────────────────────┘     │    │
│  │                                                                      │    │
│  │  Automated Backup Script:                                            │    │
│  │  ┌────────────────────────────────────────────────────────────┐     │    │
│  │  │ #!/bin/bash                                                │     │    │
│  │  │ # backup_wifi.sh                                           │     │    │
│  │  │                                                            │     │    │
│  │  │ DATE=$(date +%Y%m%d_%H%M%S)                                 │     │    │
│  │  │ BACKUP_DIR="/backup/wifi"                                  │     │    │
│  │  │ CONTROLLER="10.1.1.100"                                    │     │    │
│  │  │                                                            │     │    │
│  │  │ # Backup running config                                    │     │    │
│  │  │ ssh admin@$CONTROLLER "show running-config" > \            │     │    │
│  │  │   $BACKUP_DIR/config_$DATE.txt                             │     │    │
│  │  │                                                            │     │    │
│  │  │ # Backup AP database                                       │     │    │
│  │  │ ssh admin@$CONTROLLER "show ap database" > \               │     │    │
│  │  │   $BACKUP_DIR/ap_db_$DATE.txt                              │     │    │
│  │  │                                                            │     │    │
│  │  │ # Compress and encrypt                                     │     │    │
│  │  │ tar czf - $BACKUP_DIR/*_$DATE.txt | \                      │     │    │
│  │  │   gpg --encrypt -r backup@company.com > \                  │     │    │
│  │  │   $BACKUP_DIR/backup_$DATE.tar.gz.gpg                      │     │    │
│  │  │                                                            │     │    │
│  │  │ # Upload to off-site storage                               │     │    │
│  │  │ aws s3 cp $BACKUP_DIR/backup_$DATE.tar.gz.gpg \            │     │    │
│  │  │   s3://company-backups/wifi/                               │     │    │
│  │  │                                                            │     │    │
│  │  │ # Cleanup old backups                                      │     │    │
│  │  │ find $BACKUP_DIR -name "*.txt" -mtime +7 -delete           │     │    │
│  │  └────────────────────────────────────────────────────────────┘     │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  Recovery Procedures:                                                        │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  Controller Recovery:                                                │    │
│  │  1. Deploy new controller hardware/VM                                │    │
│  │  2. Install base firmware                                            │    │
│  │  3. Restore configuration from backup                                │    │
│  │  4. Restore certificates                                             │    │
│  │  5. Verify RADIUS connectivity                                       │    │
│  │  6. Re-adopt APs                                                     │    │
│  │  7. Verify client connectivity                                       │    │
│  │                                                                      │    │
│  │  AP Recovery:                                                        │    │
│  │  1. Factory reset AP                                                 │    │
│  │  2. Configure controller IP                                          │    │
│  │  3. AP downloads config from controller                              │    │
│  │  4. Verify radio operation                                           │    │
│  │  5. Verify client connectivity                                       │    │
│  │                                                                      │    │
│  │  Site Recovery:                                                      │    │
│  │  1. Assess damage                                                    │    │
│  │  2. Deploy replacement hardware                                      │    │
│  │  3. Restore from backup                                              │    │
│  │  4. Verify network connectivity                                      │    │
│  │  5. Test all SSIDs                                                   │    │
│  │  6. Verify roaming                                                   │    │
│  │  7. Document lessons learned                                         │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  RTO/RPO Targets:                                                            │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  ┌────────────────────────────────────────────────────────────┐     │    │
│  │  │ Scenario              RTO          RPO                     │     │    │
│  │  │ ────────              ───          ───                     │     │    │
│  │  │ Controller failure    5 minutes    0 (HA sync)             │     │    │
│  │  │ AP failure            15 minutes   0 (config on controller)│     │    │
│  │  │ Site failure          4 hours      1 hour                  │     │    │
│  │  │ Complete DR           24 hours     1 day                   │     │    │
│  │  └────────────────────────────────────────────────────────────┘     │    │
│  │                                                                      │    │
│  │  RTO = Recovery Time Objective                                       │    │
│  │  RPO = Recovery Point Objective                                      │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Appendix DS: Network Segmentation

### DS.1 VLAN Strategies

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    VLAN STRATEGIES                                           │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  VLAN Design:                                                                │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  ┌────────────────────────────────────────────────────────────┐     │    │
│  │  │ VLAN ID    Name           Purpose                          │     │    │
│  │  │ ───────    ────           ───────                          │     │    │
│  │  │ 10         Management     AP management, controller        │     │    │
│  │  │ 20         Corporate      Employee devices                 │     │    │
│  │  │ 30         Guest          Guest WiFi                       │     │    │
│  │  │ 40         IoT            IoT devices                      │     │    │
│  │  │ 50         Voice          VoIP phones                      │     │    │
│  │  │ 60         Video          Video conferencing               │     │    │
│  │  │ 100        Quarantine     Non-compliant devices            │     │    │
│  │  └────────────────────────────────────────────────────────────┘     │    │
│  │                                                                      │    │
│  │  VLAN Configuration:                                                 │    │
│  │  ┌────────────────────────────────────────────────────────────┐     │    │
│  │  │ # SSID to VLAN mapping                                     │     │    │
│  │  │ ssid Corporate                                             │     │    │
│  │  │   vlan 20                                                  │     │    │
│  │  │                                                            │     │    │
│  │  │ ssid Guest                                                 │     │    │
│  │  │   vlan 30                                                  │     │    │
│  │  │                                                            │     │    │
│  │  │ ssid IoT                                                   │     │    │
│  │  │   vlan 40                                                  │     │    │
│  │  │                                                            │     │    │
│  │  │ # Dynamic VLAN from RADIUS                                 │     │    │
│  │  │ ssid Corporate                                             │     │    │
│  │  │   vlan dynamic                                             │     │    │
│  │  │   vlan-pool 20,50,60                                       │     │    │
│  │  └────────────────────────────────────────────────────────────┘     │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  Inter-VLAN Routing:                                                         │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  ┌────────────────────────────────────────────────────────────┐     │    │
│  │  │                                                            │     │    │
│  │  │  VLAN 20 ◄──────────────────────────────────► VLAN 50      │     │    │
│  │  │  (Corp)        Allowed (VoIP)                 (Voice)      │     │    │
│  │  │                                                            │     │    │
│  │  │  VLAN 20 ◄──────────────────────────────────► VLAN 60      │     │    │
│  │  │  (Corp)        Allowed (Video)                (Video)      │     │    │
│  │  │                                                            │     │    │
│  │  │  VLAN 30 ◄─────────────X────────────────────► VLAN 20      │     │    │
│  │  │  (Guest)       Blocked                        (Corp)       │     │    │
│  │  │                                                            │     │    │
│  │  │  VLAN 40 ◄─────────────X────────────────────► VLAN 20      │     │    │
│  │  │  (IoT)         Blocked                        (Corp)       │     │    │
│  │  │                                                            │     │    │
│  │  └────────────────────────────────────────────────────────────┘     │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### DS.2 Microsegmentation

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    MICROSEGMENTATION                                         │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  Role-Based Access:                                                          │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  ┌────────────────────────────────────────────────────────────┐     │    │
│  │  │ Role          Access                                       │     │    │
│  │  │ ────          ──────                                       │     │    │
│  │  │ Employee      Full corporate network                       │     │    │
│  │  │ Contractor    Limited corporate, no finance                │     │    │
│  │  │ Guest         Internet only                                │     │    │
│  │  │ IoT-Camera    Video server only                            │     │    │
│  │  │ IoT-Sensor    IoT gateway only                             │     │    │
│  │  │ BYOD          Internet + limited corporate                 │     │    │
│  │  └────────────────────────────────────────────────────────────┘     │    │
│  │                                                                      │    │
│  │  Role Configuration:                                                 │    │
│  │  ┌────────────────────────────────────────────────────────────┐     │    │
│  │  │ role Employee                                              │     │    │
│  │  │   permit any to 10.0.0.0/8                                 │     │    │
│  │  │   permit any to 0.0.0.0/0                                  │     │    │
│  │  │                                                            │     │    │
│  │  │ role Contractor                                            │     │    │
│  │  │   deny any to 10.1.50.0/24  # Finance                      │     │    │
│  │  │   deny any to 10.1.60.0/24  # HR                           │     │    │
│  │  │   permit any to 10.0.0.0/8                                 │     │    │
│  │  │   permit any to 0.0.0.0/0                                  │     │    │
│  │  │                                                            │     │    │
│  │  │ role Guest                                                 │     │    │
│  │  │   deny any to 10.0.0.0/8                                   │     │    │
│  │  │   deny any to 172.16.0.0/12                                │     │    │
│  │  │   deny any to 192.168.0.0/16                               │     │    │
│  │  │   permit any to 0.0.0.0/0                                  │     │    │
│  │  │                                                            │     │    │
│  │  │ role IoT-Camera                                            │     │    │
│  │  │   permit any to 10.1.100.10/32  # Video server             │     │    │
│  │  │   deny any to any                                          │     │    │
│  │  └────────────────────────────────────────────────────────────┘     │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  Client Isolation:                                                           │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  # Prevent client-to-client communication                           │    │
│  │  ssid Guest                                                          │    │
│  │    client-isolation enable                                           │    │
│  │                                                                      │    │
│  │  # Allow specific client-to-client (e.g., printers)                  │    │
│  │  ssid Corporate                                                      │    │
│  │    client-isolation enable                                           │    │
│  │    client-isolation-whitelist 10.1.20.100  # Printer                 │    │
│  │    client-isolation-whitelist 10.1.20.101  # Printer                 │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Appendix DT: Logging and SIEM Integration

### DT.1 Log Configuration

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    LOG CONFIGURATION                                         │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  Syslog Configuration:                                                       │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  # Configure syslog servers                                          │    │
│  │  logging host 10.1.1.200 port 514 protocol udp                       │    │
│  │  logging host 10.1.1.201 port 6514 protocol tcp-tls                  │    │
│  │                                                                      │    │
│  │  # Configure log levels                                              │    │
│  │  logging trap informational                                          │    │
│  │  logging console warnings                                            │    │
│  │  logging buffer 10000                                                │    │
│  │                                                                      │    │
│  │  # Configure log categories                                          │    │
│  │  logging category wireless level debug                               │    │
│  │  logging category security level informational                       │    │
│  │  logging category radius level informational                         │    │
│  │  logging category dhcp level informational                           │    │
│  │                                                                      │    │
│  │  # Configure log format                                              │    │
│  │  logging format rfc5424                                              │    │
│  │  logging origin-id hostname                                          │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  Log Levels:                                                                 │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  ┌────────────────────────────────────────────────────────────┐     │    │
│  │  │ Level           Severity    Use Case                       │     │    │
│  │  │ ─────           ────────    ────────                       │     │    │
│  │  │ Emergency       0           System unusable                │     │    │
│  │  │ Alert           1           Immediate action required      │     │    │
│  │  │ Critical        2           Critical conditions            │     │    │
│  │  │ Error           3           Error conditions               │     │    │
│  │  │ Warning         4           Warning conditions             │     │    │
│  │  │ Notice          5           Normal but significant         │     │    │
│  │  │ Informational   6           Informational messages         │     │    │
│  │  │ Debug           7           Debug-level messages           │     │    │
│  │  └────────────────────────────────────────────────────────────┘     │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### DT.2 SIEM Integration

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    SIEM INTEGRATION                                          │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  Common SIEM Platforms:                                                      │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  ┌────────────────────────────────────────────────────────────┐     │    │
│  │  │ SIEM              Integration Method                       │     │    │
│  │  │ ────              ──────────────────                       │     │    │
│  │  │ Splunk            Syslog, HEC, Universal Forwarder         │     │    │
│  │  │ Elastic/ELK       Syslog, Beats, Logstash                  │     │    │
│  │  │ IBM QRadar        Syslog, DSM                              │     │    │
│  │  │ Microsoft Sentinel Syslog, CEF, API                        │     │    │
│  │  │ Sumo Logic        Syslog, Collector                        │     │    │
│  │  │ Datadog           Syslog, Agent                            │     │    │
│  │  └────────────────────────────────────────────────────────────┘     │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  Splunk Integration:                                                         │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  # inputs.conf                                                       │    │
│  │  [udp://514]                                                         │    │
│  │  connection_host = ip                                                │    │
│  │  sourcetype = syslog                                                 │    │
│  │  index = wifi                                                        │    │
│  │                                                                      │    │
│  │  # props.conf                                                        │    │
│  │  [wifi:syslog]                                                       │    │
│  │  TIME_FORMAT = %b %d %H:%M:%S                                        │    │
│  │  MAX_TIMESTAMP_LOOKAHEAD = 32                                        │    │
│  │  SHOULD_LINEMERGE = false                                            │    │
│  │                                                                      │    │
│  │  # transforms.conf                                                   │    │
│  │  [wifi_client_connect]                                               │    │
│  │  REGEX = client (\S+) connected to SSID (\S+)                        │    │
│  │  FORMAT = client_mac::$1 ssid::$2                                    │    │
│  │                                                                      │    │
│  │  Sample Splunk Queries:                                              │    │
│  │  ┌────────────────────────────────────────────────────────────┐     │    │
│  │  │ # Client connections per hour                              │     │    │
│  │  │ index=wifi "client connected"                              │     │    │
│  │  │ | timechart span=1h count                                  │     │    │
│  │  │                                                            │     │    │
│  │  │ # Authentication failures                                  │     │    │
│  │  │ index=wifi "authentication failed"                         │     │    │
│  │  │ | stats count by client_mac, ssid                          │     │    │
│  │  │                                                            │     │    │
│  │  │ # Rogue AP detection                                       │     │    │
│  │  │ index=wifi "rogue AP detected"                             │     │    │
│  │  │ | table _time, ap_name, rogue_mac, rogue_ssid              │     │    │
│  │  └────────────────────────────────────────────────────────────┘     │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  Security Alerts:                                                            │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  ┌────────────────────────────────────────────────────────────┐     │    │
│  │  │ Alert                    Condition                         │     │    │
│  │  │ ─────                    ─────────                         │     │    │
│  │  │ Brute force              > 10 auth failures in 1 min       │     │    │
│  │  │ Rogue AP                 Unknown AP with corporate SSID    │     │    │
│  │  │ Deauth flood             > 100 deauth frames in 1 min      │     │    │
│  │  │ Unusual roaming          > 20 roams in 5 min               │     │    │
│  │  │ After-hours access       Connection outside business hours │     │    │
│  │  │ New device               First-time device on network      │     │    │
│  │  └────────────────────────────────────────────────────────────┘     │    │
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
| 3.1 | 2026-01-08 | Auto-generated | Added WiFi 7 MLO, puncturing, 4K-QAM, multi-RU, enhanced security |
| 3.2 | 2026-01-08 | Auto-generated | Added FILS, DPP, enterprise security, certificate management |
| 3.3 | 2026-01-08 | Auto-generated | Added power management, airtime fairness, channel utilization |
| 3.4 | 2026-01-08 | Auto-generated | Added client steering, band selection, load balancing algorithms |
| 3.5 | 2026-01-08 | Auto-generated | Added mesh networking, WDS, repeater modes, backhaul optimization |
| 3.6 | 2026-01-08 | Auto-generated | Added roaming protocols, 802.11k/v/r deep dive, seamless handoff |
| 3.7 | 2026-01-08 | Auto-generated | Added DHCP deep dive, DNS, mDNS, service discovery |
| 3.8 | 2026-01-08 | Auto-generated | Added firewall policies, ACLs, traffic filtering, NAT |
| 3.9 | 2026-01-08 | Auto-generated | Added IoT device profiling, device fingerprinting, MAC randomization |
| 4.0 | 2026-01-08 | Auto-generated | Added CLI command reference, API reference, automation |
| 4.1 | 2026-01-08 | Auto-generated | Added network automation, scripting, integration examples |
| 4.2 | 2026-01-08 | Auto-generated | Added site survey, capacity planning, deployment best practices |
| 4.3 | 2026-01-08 | Auto-generated | Added troubleshooting runbook, migration guide, vendor interoperability |
| 4.4 | 2026-01-08 | Auto-generated | Added high availability, disaster recovery, backup strategies |
| 4.5 | 2026-01-08 | Auto-generated | Added spectrum analysis, interference mitigation, RF optimization |

---

## Appendix DU: Spectrum Analysis

### DU.1 RF Spectrum Fundamentals

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    RF SPECTRUM FUNDAMENTALS                                  │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  WiFi Frequency Bands:                                                       │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  2.4 GHz Band (2400-2483.5 MHz):                                     │    │
│  │  ┌────────────────────────────────────────────────────────────┐     │    │
│  │  │                                                            │     │    │
│  │  │  Ch1    Ch2    Ch3    Ch4    Ch5    Ch6    Ch7    Ch8      │     │    │
│  │  │  ├──────┼──────┼──────┼──────┼──────┼──────┼──────┼──────┤ │     │    │
│  │  │  2412   2417   2422   2427   2432   2437   2442   2447     │     │    │
│  │  │                                                            │     │    │
│  │  │  Ch9    Ch10   Ch11   Ch12   Ch13   Ch14                   │     │    │
│  │  │  ├──────┼──────┼──────┼──────┼──────┼──────┤               │     │    │
│  │  │  2452   2457   2462   2467   2472   2484                   │     │    │
│  │  │                                                            │     │    │
│  │  │  Non-overlapping: 1, 6, 11 (20 MHz channels)               │     │    │
│  │  │  Channel width: 20 MHz (40 MHz possible but not recommended)│     │    │
│  │  │                                                            │     │    │
│  │  └────────────────────────────────────────────────────────────┘     │    │
│  │                                                                      │    │
│  │  5 GHz Band (5150-5850 MHz):                                         │    │
│  │  ┌────────────────────────────────────────────────────────────┐     │    │
│  │  │                                                            │     │    │
│  │  │  UNII-1 (5150-5250 MHz): 36, 40, 44, 48                    │     │    │
│  │  │  UNII-2A (5250-5350 MHz): 52, 56, 60, 64 (DFS)             │     │    │
│  │  │  UNII-2C (5470-5725 MHz): 100-144 (DFS)                    │     │    │
│  │  │  UNII-3 (5725-5850 MHz): 149, 153, 157, 161, 165           │     │    │
│  │  │                                                            │     │    │
│  │  │  Channel widths: 20, 40, 80, 160 MHz                       │     │    │
│  │  │                                                            │     │    │
│  │  │  80 MHz channels:                                          │     │    │
│  │  │  36-48, 52-64, 100-112, 116-128, 132-144, 149-161          │     │    │
│  │  │                                                            │     │    │
│  │  │  160 MHz channels:                                         │     │    │
│  │  │  36-64, 100-128                                            │     │    │
│  │  │                                                            │     │    │
│  │  └────────────────────────────────────────────────────────────┘     │    │
│  │                                                                      │    │
│  │  6 GHz Band (5925-7125 MHz):                                         │    │
│  │  ┌────────────────────────────────────────────────────────────┐     │    │
│  │  │                                                            │     │    │
│  │  │  UNII-5 (5925-6425 MHz): Channels 1-93                     │     │    │
│  │  │  UNII-6 (6425-6525 MHz): Channels 97-109                   │     │    │
│  │  │  UNII-7 (6525-6875 MHz): Channels 113-177                  │     │    │
│  │  │  UNII-8 (6875-7125 MHz): Channels 181-233                  │     │    │
│  │  │                                                            │     │    │
│  │  │  Channel widths: 20, 40, 80, 160, 320 MHz                  │     │    │
│  │  │                                                            │     │    │
│  │  │  59 x 20 MHz channels                                      │     │    │
│  │  │  29 x 40 MHz channels                                      │     │    │
│  │  │  14 x 80 MHz channels                                      │     │    │
│  │  │  7 x 160 MHz channels                                      │     │    │
│  │  │  3 x 320 MHz channels                                      │     │    │
│  │  │                                                            │     │    │
│  │  └────────────────────────────────────────────────────────────┘     │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### DU.2 Interference Sources

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    INTERFERENCE SOURCES                                      │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  2.4 GHz Interference:                                                       │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  ┌────────────────────────────────────────────────────────────┐     │    │
│  │  │ Source              Frequency       Impact                 │     │    │
│  │  │ ──────              ─────────       ──────                 │     │    │
│  │  │ Microwave oven      2.45 GHz        Severe (when active)   │     │    │
│  │  │ Bluetooth           2.4-2.4835 GHz  Moderate               │     │    │
│  │  │ Cordless phones     2.4 GHz         Moderate               │     │    │
│  │  │ Baby monitors       2.4 GHz         Moderate               │     │    │
│  │  │ Wireless cameras    2.4 GHz         Moderate               │     │    │
│  │  │ ZigBee/Z-Wave       2.4 GHz         Low-Moderate           │     │    │
│  │  │ Fluorescent lights  Broadband       Low                    │     │    │
│  │  │ USB 3.0             2.4-2.5 GHz     Low-Moderate           │     │    │
│  │  └────────────────────────────────────────────────────────────┘     │    │
│  │                                                                      │    │
│  │  Microwave Oven Interference Pattern:                               │    │
│  │  ┌────────────────────────────────────────────────────────────┐     │    │
│  │  │                                                            │     │    │
│  │  │  Signal │                                                  │     │    │
│  │  │  Level  │    ████                                          │     │    │
│  │  │    ▲    │   ██████                                         │     │    │
│  │  │    │    │  ████████                                        │     │    │
│  │  │    │    │ ██████████                                       │     │    │
│  │  │    │    │████████████                                      │     │    │
│  │  │    └────┼────────────────────────────────────────► Freq    │     │    │
│  │  │         2.40  2.45  2.50 GHz                               │     │    │
│  │  │                                                            │     │    │
│  │  │  Mitigation: Use 5 GHz or 6 GHz, avoid channels 7-11       │     │    │
│  │  │                                                            │     │    │
│  │  └────────────────────────────────────────────────────────────┘     │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  5 GHz Interference:                                                         │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  ┌────────────────────────────────────────────────────────────┐     │    │
│  │  │ Source              Frequency       Impact                 │     │    │
│  │  │ ──────              ─────────       ──────                 │     │    │
│  │  │ Weather radar       5.25-5.35 GHz   Severe (DFS required)  │     │    │
│  │  │ Military radar      5.25-5.85 GHz   Severe (DFS required)  │     │    │
│  │  │ Satellite downlink  5.725-5.875 GHz Moderate               │     │    │
│  │  │ Cordless phones     5.8 GHz         Low                    │     │    │
│  │  │ Wireless bridges    5 GHz           Moderate               │     │    │
│  │  └────────────────────────────────────────────────────────────┘     │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  Co-Channel Interference (CCI):                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  Definition: Multiple APs on same channel                           │    │
│  │                                                                      │    │
│  │  ┌────────────────────────────────────────────────────────────┐     │    │
│  │  │                                                            │     │    │
│  │  │     AP1 (Ch 36)              AP2 (Ch 36)                   │     │    │
│  │  │        ◉ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ◉                           │     │    │
│  │  │       /│\         CCI        /│\                           │     │    │
│  │  │      / │ \                  / │ \                          │     │    │
│  │  │     /  │  \                /  │  \                         │     │    │
│  │  │    ○   ○   ○              ○   ○   ○                        │     │    │
│  │  │  Clients                Clients                            │     │    │
│  │  │                                                            │     │    │
│  │  │  Impact: Reduced throughput, increased latency             │     │    │
│  │  │  Mitigation: Proper channel planning, reduce power         │     │    │
│  │  │                                                            │     │    │
│  │  └────────────────────────────────────────────────────────────┘     │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  Adjacent Channel Interference (ACI):                                        │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  Definition: APs on overlapping channels                            │    │
│  │                                                                      │    │
│  │  ┌────────────────────────────────────────────────────────────┐     │    │
│  │  │                                                            │     │    │
│  │  │  2.4 GHz Example:                                          │     │    │
│  │  │                                                            │     │    │
│  │  │  Ch 1 ████████████████████                                 │     │    │
│  │  │  Ch 3     ████████████████████                             │     │    │
│  │  │  Ch 6             ████████████████████                     │     │    │
│  │  │       ─────────────────────────────────────► Frequency     │     │    │
│  │  │                                                            │     │    │
│  │  │  Ch 1 and Ch 3 overlap = ACI                               │     │    │
│  │  │  Ch 1 and Ch 6 do not overlap = No ACI                     │     │    │
│  │  │                                                            │     │    │
│  │  │  Mitigation: Use non-overlapping channels (1, 6, 11)       │     │    │
│  │  │                                                            │     │    │
│  │  └────────────────────────────────────────────────────────────┘     │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### DU.3 Spectrum Analysis Tools

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    SPECTRUM ANALYSIS TOOLS                                   │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  Built-in Spectrum Analysis:                                                 │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  # Enable spectrum analysis on AP                                    │    │
│  │  ap-name AP-Floor1                                                   │    │
│  │    spectrum-analysis enable                                          │    │
│  │    spectrum-analysis mode dedicated                                  │    │
│  │                                                                      │    │
│  │  # View spectrum data                                                │    │
│  │  show spectrum-analysis summary                                      │    │
│  │  show spectrum-analysis interference                                 │    │
│  │  show spectrum-analysis channel-quality                              │    │
│  │                                                                      │    │
│  │  Modes:                                                              │    │
│  │  - Dedicated: Radio dedicated to spectrum analysis                   │    │
│  │  - Hybrid: Time-shared between serving clients and analysis          │    │
│  │  - Background: Analysis during idle periods                          │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  Spectrum Analysis Display:                                                  │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  Real-Time FFT (Fast Fourier Transform):                             │    │
│  │  ┌────────────────────────────────────────────────────────────┐     │    │
│  │  │                                                            │     │    │
│  │  │  dBm │                                                     │     │    │
│  │  │  -30 │                                                     │     │    │
│  │  │  -40 │      ▄▄                                             │     │    │
│  │  │  -50 │     ████    ▄▄                                      │     │    │
│  │  │  -60 │    ██████  ████   ▄▄                                │     │    │
│  │  │  -70 │   ████████████████████                              │     │    │
│  │  │  -80 │  ██████████████████████                             │     │    │
│  │  │  -90 │ ████████████████████████                            │     │    │
│  │  │      └────────────────────────────────────────► MHz        │     │    │
│  │  │        2412  2437  2462                                    │     │    │
│  │  │        Ch1   Ch6   Ch11                                    │     │    │
│  │  │                                                            │     │    │
│  │  └────────────────────────────────────────────────────────────┘     │    │
│  │                                                                      │    │
│  │  Waterfall Display (Time vs Frequency):                              │    │
│  │  ┌────────────────────────────────────────────────────────────┐     │    │
│  │  │                                                            │     │    │
│  │  │  Time │ ░░░░████░░░░░░░░████░░░░░░░░████░░░░               │     │    │
│  │  │   ▲   │ ░░░░████░░░░░░░░████░░░░░░░░████░░░░               │     │    │
│  │  │   │   │ ░░░░████░░░░░░░░████░░░░░░░░████░░░░               │     │    │
│  │  │   │   │ ░░░░████░░░░████████░░░░░░░░████░░░░  ← Interference│     │    │
│  │  │   │   │ ░░░░████░░░░████████░░░░░░░░████░░░░               │     │    │
│  │  │   │   │ ░░░░████░░░░░░░░████░░░░░░░░████░░░░               │     │    │
│  │  │       └────────────────────────────────────────► Frequency │     │    │
│  │  │         Ch1        Ch6        Ch11                         │     │    │
│  │  │                                                            │     │    │
│  │  │  ░ = Low signal    █ = High signal                         │     │    │
│  │  │                                                            │     │    │
│  │  └────────────────────────────────────────────────────────────┘     │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  Interference Classification:                                                │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  ┌────────────────────────────────────────────────────────────┐     │    │
│  │  │ Interferer Type     Signature                              │     │    │
│  │  │ ───────────────     ─────────                              │     │    │
│  │  │ Microwave oven      Wideband, periodic, 2.45 GHz center    │     │    │
│  │  │ Bluetooth           Frequency hopping, narrowband          │     │    │
│  │  │ Cordless phone      Narrowband, fixed frequency            │     │    │
│  │  │ Video bridge        Wideband, continuous                   │     │    │
│  │  │ ZigBee              Narrowband, 2 MHz wide                 │     │    │
│  │  │ Radar               Pulsed, high power, DFS channels       │     │    │
│  │  │ Jammer              Wideband, continuous, high power       │     │    │
│  │  └────────────────────────────────────────────────────────────┘     │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Appendix DV: Advanced RF Optimization

### DV.1 Transmit Power Control

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    TRANSMIT POWER CONTROL                                    │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  Power Level Guidelines:                                                     │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  ┌────────────────────────────────────────────────────────────┐     │    │
│  │  │ Environment         2.4 GHz Power    5 GHz Power           │     │    │
│  │  │ ───────────         ─────────────    ───────────           │     │    │
│  │  │ High density        6-9 dBm          9-12 dBm              │     │    │
│  │  │ Medium density      12-15 dBm        15-18 dBm             │     │    │
│  │  │ Low density         15-18 dBm        18-21 dBm             │     │    │
│  │  │ Outdoor             18-23 dBm        21-30 dBm             │     │    │
│  │  └────────────────────────────────────────────────────────────┘     │    │
│  │                                                                      │    │
│  │  Configuration:                                                      │    │
│  │  ┌────────────────────────────────────────────────────────────┐     │    │
│  │  │ # Manual power configuration                               │     │    │
│  │  │ radio 2.4ghz                                               │     │    │
│  │  │   tx-power 12                                              │     │    │
│  │  │                                                            │     │    │
│  │  │ radio 5ghz                                                 │     │    │
│  │  │   tx-power 15                                              │     │    │
│  │  │                                                            │     │    │
│  │  │ # Automatic power control                                  │     │    │
│  │  │ rf-management                                              │     │    │
│  │  │   power-control enable                                     │     │    │
│  │  │   power-control min 6                                      │     │    │
│  │  │   power-control max 18                                     │     │    │
│  │  │   power-control target-rssi -65                            │     │    │
│  │  └────────────────────────────────────────────────────────────┘     │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  Power Control Algorithm:                                                    │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  ┌────────────────────────────────────────────────────────────┐     │    │
│  │  │                                                            │     │    │
│  │  │  Start                                                     │     │    │
│  │  │    │                                                       │     │    │
│  │  │    ▼                                                       │     │    │
│  │  │  ┌─────────────────────────────────────┐                   │     │    │
│  │  │  │ Measure neighbor AP signal strength │                   │     │    │
│  │  │  └─────────────────┬───────────────────┘                   │     │    │
│  │  │                    │                                       │     │    │
│  │  │                    ▼                                       │     │    │
│  │  │  ┌─────────────────────────────────────┐                   │     │    │
│  │  │  │ Neighbor RSSI > -65 dBm?            │                   │     │    │
│  │  │  └─────────────────┬───────────────────┘                   │     │    │
│  │  │           Yes │           │ No                             │     │    │
│  │  │               ▼           ▼                                │     │    │
│  │  │  ┌─────────────────┐  ┌─────────────────┐                  │     │    │
│  │  │  │ Decrease power  │  │ Increase power  │                  │     │    │
│  │  │  │ (if > min)      │  │ (if < max)      │                  │     │    │
│  │  │  └─────────────────┘  └─────────────────┘                  │     │    │
│  │  │                                                            │     │    │
│  │  └────────────────────────────────────────────────────────────┘     │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### DV.2 Channel Selection

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    CHANNEL SELECTION                                         │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  Automatic Channel Selection (ACS):                                          │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  Configuration:                                                      │    │
│  │  ┌────────────────────────────────────────────────────────────┐     │    │
│  │  │ rf-management                                              │     │    │
│  │  │   channel-selection enable                                 │     │    │
│  │  │   channel-selection mode least-congested                   │     │    │
│  │  │   channel-selection interval 3600                          │     │    │
│  │  │   channel-selection time 02:00                             │     │    │
│  │  │                                                            │     │    │
│  │  │ # Exclude specific channels                                │     │    │
│  │  │ radio 5ghz                                                 │     │    │
│  │  │   channel-exclude 52,56,60,64  # DFS channels              │     │    │
│  │  └────────────────────────────────────────────────────────────┘     │    │
│  │                                                                      │    │
│  │  Channel Selection Criteria:                                         │    │
│  │  ┌────────────────────────────────────────────────────────────┐     │    │
│  │  │ Factor              Weight    Description                  │     │    │
│  │  │ ──────              ──────    ───────────                  │     │    │
│  │  │ Channel utilization High      % of time channel is busy    │     │    │
│  │  │ Noise floor         Medium    Background noise level       │     │    │
│  │  │ Neighbor count      Medium    Number of APs on channel     │     │    │
│  │  │ Interference        High      Non-WiFi interference        │     │    │
│  │  │ Client count        Low       Clients on channel           │     │    │
│  │  │ DFS availability    Medium    Radar detection history      │     │    │
│  │  └────────────────────────────────────────────────────────────┘     │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  Channel Width Selection:                                                    │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  ┌────────────────────────────────────────────────────────────┐     │    │
│  │  │ Width    Throughput    Coverage    Interference Risk       │     │    │
│  │  │ ─────    ──────────    ────────    ────────────────        │     │    │
│  │  │ 20 MHz   Low           Best        Lowest                  │     │    │
│  │  │ 40 MHz   Medium        Good        Low                     │     │    │
│  │  │ 80 MHz   High          Moderate    Medium                  │     │    │
│  │  │ 160 MHz  Very High     Limited     High                    │     │    │
│  │  │ 320 MHz  Highest       Limited     Highest                 │     │    │
│  │  └────────────────────────────────────────────────────────────┘     │    │
│  │                                                                      │    │
│  │  Recommendations:                                                    │    │
│  │  - High density: 20-40 MHz                                           │    │
│  │  - Medium density: 40-80 MHz                                         │    │
│  │  - Low density: 80-160 MHz                                           │    │
│  │  - 6 GHz: 80-320 MHz (more spectrum available)                       │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### DV.3 Antenna Optimization

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    ANTENNA OPTIMIZATION                                      │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  Antenna Types:                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  ┌────────────────────────────────────────────────────────────┐     │    │
│  │  │ Type            Pattern         Gain      Use Case         │     │    │
│  │  │ ────            ───────         ────      ────────         │     │    │
│  │  │ Omnidirectional 360° horizontal 2-5 dBi   General coverage │     │    │
│  │  │ Directional     60-120° beam    8-15 dBi  Point-to-point   │     │    │
│  │  │ Sector          90-120° beam    6-12 dBi  Outdoor coverage │     │    │
│  │  │ Patch           60-90° beam     6-9 dBi   Wall mount       │     │    │
│  │  │ Yagi            30-60° beam     10-18 dBi Long range       │     │    │
│  │  └────────────────────────────────────────────────────────────┘     │    │
│  │                                                                      │    │
│  │  Antenna Patterns:                                                   │    │
│  │  ┌────────────────────────────────────────────────────────────┐     │    │
│  │  │                                                            │     │    │
│  │  │  Omnidirectional (Top View):    Directional (Top View):    │     │    │
│  │  │                                                            │     │    │
│  │  │        ╭───────╮                      ╭──╮                 │     │    │
│  │  │       ╱         ╲                    ╱    ╲                │     │    │
│  │  │      │     ◉     │                  │  ◉   ╲               │     │    │
│  │  │       ╲         ╱                    ╲    ╱                │     │    │
│  │  │        ╰───────╯                      ╰──╯                 │     │    │
│  │  │                                                            │     │    │
│  │  │  Coverage: 360°                 Coverage: 60-90°           │     │    │
│  │  │                                                            │     │    │
│  │  └────────────────────────────────────────────────────────────┘     │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  MIMO Antenna Configuration:                                                 │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  ┌────────────────────────────────────────────────────────────┐     │    │
│  │  │ Configuration    Streams    Max Throughput (WiFi 6)        │     │    │
│  │  │ ─────────────    ───────    ───────────────────────        │     │    │
│  │  │ 2x2 MIMO         2          1.2 Gbps (80 MHz)              │     │    │
│  │  │ 4x4 MIMO         4          2.4 Gbps (80 MHz)              │     │    │
│  │  │ 8x8 MIMO         8          4.8 Gbps (80 MHz)              │     │    │
│  │  │ 4x4 MIMO         4          4.8 Gbps (160 MHz)             │     │    │
│  │  │ 8x8 MIMO         8          9.6 Gbps (160 MHz)             │     │    │
│  │  └────────────────────────────────────────────────────────────┘     │    │
│  │                                                                      │    │
│  │  Note: Actual throughput depends on client capabilities             │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  Antenna Placement:                                                          │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  Indoor:                                                             │    │
│  │  - Mount on ceiling for best coverage                                │    │
│  │  - Avoid metal obstructions                                          │    │
│  │  - Keep away from fluorescent lights                                 │    │
│  │  - Maintain line of sight where possible                             │    │
│  │                                                                      │    │
│  │  Outdoor:                                                            │    │
│  │  - Use weatherproof enclosures                                       │    │
│  │  - Consider wind loading                                             │    │
│  │  - Ground for lightning protection                                   │    │
│  │  - Aim antenna for desired coverage area                             │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Appendix DW: Future Technologies

### DW.1 WiFi 8 (802.11bn)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    WIFI 8 (802.11bn) PREVIEW                                 │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  Expected Features:                                                          │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  ┌────────────────────────────────────────────────────────────┐     │    │
│  │  │ Feature                 Description                        │     │    │
│  │  │ ───────                 ───────────                        │     │    │
│  │  │ Ultra High Reliability  99.9999% reliability target        │     │    │
│  │  │ Coordinated AP          Multiple APs serve single client   │     │    │
│  │  │ Enhanced MLO            Improved multi-link operation      │     │    │
│  │  │ 16x16 MIMO              More spatial streams               │     │    │
│  │  │ 8K-QAM                  Higher modulation (if feasible)    │     │    │
│  │  │ AI/ML Integration       Intelligent network optimization   │     │    │
│  │  │ Sub-1ms Latency         Ultra-low latency for XR/gaming    │     │    │
│  │  │ 100 Gbps+               Aggregate throughput target        │     │    │
│  │  └────────────────────────────────────────────────────────────┘     │    │
│  │                                                                      │    │
│  │  Timeline:                                                           │    │
│  │  - 2024-2025: Study group and requirements                           │    │
│  │  - 2025-2027: Draft specification development                        │    │
│  │  - 2028: Expected ratification                                       │    │
│  │  - 2029+: Commercial products                                        │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  Coordinated Multi-AP:                                                       │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  ┌────────────────────────────────────────────────────────────┐     │    │
│  │  │                                                            │     │    │
│  │  │     AP1 ◉ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ◉ AP2                      │     │    │
│  │  │          ╲                     ╱                           │     │    │
│  │  │           ╲   Coordinated    ╱                             │     │    │
│  │  │            ╲  Transmission  ╱                              │     │    │
│  │  │             ╲             ╱                                │     │    │
│  │  │              ╲           ╱                                 │     │    │
│  │  │               ╲         ╱                                  │     │    │
│  │  │                ╲       ╱                                   │     │    │
│  │  │                 ○ Client                                   │     │    │
│  │  │                                                            │     │    │
│  │  │  Benefits:                                                 │     │    │
│  │  │  - Improved coverage at cell edges                         │     │    │
│  │  │  - Higher throughput through spatial diversity             │     │    │
│  │  │  - Reduced interference                                    │     │    │
│  │  │                                                            │     │    │
│  │  └────────────────────────────────────────────────────────────┘     │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### DW.2 Emerging Technologies

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    EMERGING TECHNOLOGIES                                     │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  WiFi Sensing (802.11bf):                                                    │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  Uses WiFi signals for sensing applications:                         │    │
│  │  - Presence detection                                                │    │
│  │  - Motion detection                                                  │    │
│  │  - Gesture recognition                                               │    │
│  │  - Health monitoring (breathing, heart rate)                         │    │
│  │  - Object detection                                                  │    │
│  │                                                                      │    │
│  │  How it works:                                                       │    │
│  │  ┌────────────────────────────────────────────────────────────┐     │    │
│  │  │                                                            │     │    │
│  │  │  AP ◉ ─────────────────────────────────────────► Client    │     │    │
│  │  │       ╲                                       ╱            │     │    │
│  │  │        ╲                                     ╱             │     │    │
│  │  │         ╲         ┌─────────┐              ╱              │     │    │
│  │  │          ╲        │ Person  │             ╱               │     │    │
│  │  │           ╲       │ Moving  │            ╱                │     │    │
│  │  │            ╲      └─────────┘           ╱                 │     │    │
│  │  │             ╲                          ╱                  │     │    │
│  │  │              ╲                        ╱                   │     │    │
│  │  │               ╲──────────────────────╱                    │     │    │
│  │  │                  Reflected signal                         │     │    │
│  │  │                                                            │     │    │
│  │  │  CSI (Channel State Information) analysis detects changes │     │    │
│  │  │                                                            │     │    │
│  │  └────────────────────────────────────────────────────────────┘     │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  Private 5G/WiFi Convergence:                                                │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  ┌────────────────────────────────────────────────────────────┐     │    │
│  │  │ Technology      Spectrum        Use Case                   │     │    │
│  │  │ ──────────      ────────        ────────                   │     │    │
│  │  │ WiFi 6E/7       6 GHz           High throughput, indoor    │     │    │
│  │  │ Private 5G      CBRS (3.5 GHz)  Wide area, outdoor         │     │    │
│  │  │ Hybrid          Both            Seamless indoor/outdoor    │     │    │
│  │  └────────────────────────────────────────────────────────────┘     │    │
│  │                                                                      │    │
│  │  Convergence Benefits:                                               │    │
│  │  - Single management platform                                        │    │
│  │  - Seamless handoff between WiFi and 5G                              │    │
│  │  - Unified security policies                                         │    │
│  │  - Optimized spectrum utilization                                    │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  AI/ML in WiFi:                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  Applications:                                                       │    │
│  │  ┌────────────────────────────────────────────────────────────┐     │    │
│  │  │ Application              Benefit                           │     │    │
│  │  │ ───────────              ───────                           │     │    │
│  │  │ Predictive roaming       Anticipate client movement        │     │    │
│  │  │ Anomaly detection        Identify security threats         │     │    │
│  │  │ Capacity planning        Predict future needs              │     │    │
│  │  │ Interference mitigation  Proactive channel changes         │     │    │
│  │  │ Client profiling         Automatic device classification   │     │    │
│  │  │ Troubleshooting          Root cause analysis               │     │    │
│  │  └────────────────────────────────────────────────────────────┘     │    │
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
| 3.1 | 2026-01-08 | Auto-generated | Added WiFi 7 MLO, puncturing, 4K-QAM, multi-RU, enhanced security |
| 3.2 | 2026-01-08 | Auto-generated | Added FILS, DPP, enterprise security, certificate management |
| 3.3 | 2026-01-08 | Auto-generated | Added power management, airtime fairness, channel utilization |
| 3.4 | 2026-01-08 | Auto-generated | Added client steering, band selection, load balancing algorithms |
| 3.5 | 2026-01-08 | Auto-generated | Added mesh networking, WDS, repeater modes, backhaul optimization |
| 3.6 | 2026-01-08 | Auto-generated | Added roaming protocols, 802.11k/v/r deep dive, seamless handoff |
| 3.7 | 2026-01-08 | Auto-generated | Added DHCP deep dive, DNS, mDNS, service discovery |
| 3.8 | 2026-01-08 | Auto-generated | Added firewall policies, ACLs, traffic filtering, NAT |
| 3.9 | 2026-01-08 | Auto-generated | Added IoT device profiling, device fingerprinting, MAC randomization |
| 4.0 | 2026-01-08 | Auto-generated | Added CLI command reference, API reference, automation |
| 4.1 | 2026-01-08 | Auto-generated | Added network automation, scripting, integration examples |
| 4.2 | 2026-01-08 | Auto-generated | Added site survey, capacity planning, deployment best practices |
| 4.3 | 2026-01-08 | Auto-generated | Added troubleshooting runbook, migration guide, vendor interoperability |
| 4.4 | 2026-01-08 | Auto-generated | Added high availability, disaster recovery, backup strategies |
| 4.5 | 2026-01-08 | Auto-generated | Added spectrum analysis, interference mitigation, RF optimization |
| 4.6 | 2026-01-08 | Auto-generated | Added API integration, webhooks, automation scripts |

---

## Appendix DX: API Integration

### DX.1 REST API Overview

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    REST API OVERVIEW                                         │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  API Authentication:                                                         │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  # API Token Authentication                                          │    │
│  │  curl -X POST https://controller.example.com/api/v1/auth/login \     │    │
│  │    -H "Content-Type: application/json" \                             │    │
│  │    -d '{"username": "admin", "password": "secret"}'                  │    │
│  │                                                                      │    │
│  │  Response:                                                           │    │
│  │  {                                                                   │    │
│  │    "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",               │    │
│  │    "expires_in": 3600,                                               │    │
│  │    "token_type": "Bearer"                                            │    │
│  │  }                                                                   │    │
│  │                                                                      │    │
│  │  # Using the token                                                   │    │
│  │  curl -X GET https://controller.example.com/api/v1/aps \             │    │
│  │    -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."│    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  API Endpoints:                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  ┌────────────────────────────────────────────────────────────┐     │    │
│  │  │ Endpoint                    Method    Description          │     │    │
│  │  │ ────────                    ──────    ───────────          │     │    │
│  │  │ /api/v1/aps                 GET       List all APs         │     │    │
│  │  │ /api/v1/aps/{id}            GET       Get AP details       │     │    │
│  │  │ /api/v1/aps/{id}            PUT       Update AP config     │     │    │
│  │  │ /api/v1/aps/{id}/reboot     POST      Reboot AP            │     │    │
│  │  │ /api/v1/clients             GET       List all clients     │     │    │
│  │  │ /api/v1/clients/{mac}       GET       Get client details   │     │    │
│  │  │ /api/v1/clients/{mac}       DELETE    Disconnect client    │     │    │
│  │  │ /api/v1/ssids               GET       List all SSIDs       │     │    │
│  │  │ /api/v1/ssids               POST      Create SSID          │     │    │
│  │  │ /api/v1/ssids/{id}          PUT       Update SSID          │     │    │
│  │  │ /api/v1/ssids/{id}          DELETE    Delete SSID          │     │    │
│  │  │ /api/v1/rf-profiles         GET       List RF profiles     │     │    │
│  │  │ /api/v1/rf-profiles         POST      Create RF profile    │     │    │
│  │  │ /api/v1/stats/throughput    GET       Get throughput stats │     │    │
│  │  │ /api/v1/stats/clients       GET       Get client stats     │     │    │
│  │  │ /api/v1/events              GET       Get events           │     │    │
│  │  │ /api/v1/alerts              GET       Get alerts           │     │    │
│  │  └────────────────────────────────────────────────────────────┘     │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  Example API Calls:                                                          │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  # Get all APs                                                       │    │
│  │  curl -X GET https://controller.example.com/api/v1/aps \             │    │
│  │    -H "Authorization: Bearer $TOKEN"                                 │    │
│  │                                                                      │    │
│  │  Response:                                                           │    │
│  │  {                                                                   │    │
│  │    "aps": [                                                          │    │
│  │      {                                                               │    │
│  │        "id": "ap-001",                                               │    │
│  │        "name": "AP-Floor1-Lobby",                                    │    │
│  │        "mac": "00:11:22:33:44:55",                                   │    │
│  │        "ip": "10.1.1.10",                                            │    │
│  │        "model": "AP-550",                                            │    │
│  │        "status": "online",                                           │    │
│  │        "clients": 25,                                                │    │
│  │        "uptime": 864000                                              │    │
│  │      },                                                              │    │
│  │      ...                                                             │    │
│  │    ],                                                                │    │
│  │    "total": 50,                                                      │    │
│  │    "page": 1,                                                        │    │
│  │    "per_page": 20                                                    │    │
│  │  }                                                                   │    │
│  │                                                                      │    │
│  │  # Create new SSID                                                   │    │
│  │  curl -X POST https://controller.example.com/api/v1/ssids \          │    │
│  │    -H "Authorization: Bearer $TOKEN" \                               │    │
│  │    -H "Content-Type: application/json" \                             │    │
│  │    -d '{                                                             │    │
│  │      "name": "Guest-WiFi",                                           │    │
│  │      "security": "wpa2-psk",                                         │    │
│  │      "passphrase": "GuestPassword123",                               │    │
│  │      "vlan": 30,                                                     │    │
│  │      "enabled": true                                                 │    │
│  │    }'                                                                │    │
│  │                                                                      │    │
│  │  # Disconnect a client                                               │    │
│  │  curl -X DELETE \                                                    │    │
│  │    https://controller.example.com/api/v1/clients/aa:bb:cc:dd:ee:ff \ │    │
│  │    -H "Authorization: Bearer $TOKEN"                                 │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### DX.2 Webhooks

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    WEBHOOKS                                                  │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  Webhook Configuration:                                                      │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  # Configure webhook endpoint                                        │    │
│  │  curl -X POST https://controller.example.com/api/v1/webhooks \       │    │
│  │    -H "Authorization: Bearer $TOKEN" \                               │    │
│  │    -H "Content-Type: application/json" \                             │    │
│  │    -d '{                                                             │    │
│  │      "url": "https://myserver.example.com/wifi-events",              │    │
│  │      "events": ["client.connect", "client.disconnect", "ap.offline"],│    │
│  │      "secret": "webhook-secret-key",                                 │    │
│  │      "enabled": true                                                 │    │
│  │    }'                                                                │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  Webhook Events:                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  ┌────────────────────────────────────────────────────────────┐     │    │
│  │  │ Event                   Description                        │     │    │
│  │  │ ─────                   ───────────                        │     │    │
│  │  │ client.connect          Client connected to network        │     │    │
│  │  │ client.disconnect       Client disconnected                │     │    │
│  │  │ client.roam             Client roamed to new AP            │     │    │
│  │  │ client.auth_failure     Authentication failed              │     │    │
│  │  │ ap.online               AP came online                     │     │    │
│  │  │ ap.offline              AP went offline                    │     │    │
│  │  │ ap.config_change        AP configuration changed           │     │    │
│  │  │ rogue.detected          Rogue AP detected                  │     │    │
│  │  │ dfs.radar_detected      Radar detected on DFS channel      │     │    │
│  │  │ alert.threshold         Threshold alert triggered          │     │    │
│  │  └────────────────────────────────────────────────────────────┘     │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  Webhook Payload Examples:                                                   │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  # client.connect event                                              │    │
│  │  {                                                                   │    │
│  │    "event": "client.connect",                                        │    │
│  │    "timestamp": "2026-01-08T10:30:00Z",                              │    │
│  │    "data": {                                                         │    │
│  │      "client_mac": "aa:bb:cc:dd:ee:ff",                              │    │
│  │      "client_ip": "10.1.20.50",                                      │    │
│  │      "ssid": "Corporate",                                            │    │
│  │      "ap_name": "AP-Floor1-Lobby",                                   │    │
│  │      "ap_mac": "00:11:22:33:44:55",                                  │    │
│  │      "channel": 36,                                                  │    │
│  │      "rssi": -55,                                                    │    │
│  │      "username": "john.doe@company.com",                             │    │
│  │      "auth_method": "802.1X"                                         │    │
│  │    }                                                                 │    │
│  │  }                                                                   │    │
│  │                                                                      │    │
│  │  # ap.offline event                                                  │    │
│  │  {                                                                   │    │
│  │    "event": "ap.offline",                                            │    │
│  │    "timestamp": "2026-01-08T10:35:00Z",                              │    │
│  │    "data": {                                                         │    │
│  │      "ap_name": "AP-Floor2-Conference",                              │    │
│  │      "ap_mac": "00:11:22:33:44:66",                                  │    │
│  │      "ap_ip": "10.1.1.11",                                           │    │
│  │      "last_seen": "2026-01-08T10:34:30Z",                            │    │
│  │      "clients_affected": 15                                          │    │
│  │    }                                                                 │    │
│  │  }                                                                   │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  Webhook Receiver Example (Python):                                          │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  from flask import Flask, request, jsonify                           │    │
│  │  import hmac                                                         │    │
│  │  import hashlib                                                      │    │
│  │                                                                      │    │
│  │  app = Flask(__name__)                                               │    │
│  │  WEBHOOK_SECRET = "webhook-secret-key"                               │    │
│  │                                                                      │    │
│  │  def verify_signature(payload, signature):                           │    │
│  │      expected = hmac.new(                                            │    │
│  │          WEBHOOK_SECRET.encode(),                                    │    │
│  │          payload,                                                    │    │
│  │          hashlib.sha256                                              │    │
│  │      ).hexdigest()                                                   │    │
│  │      return hmac.compare_digest(expected, signature)                 │    │
│  │                                                                      │    │
│  │  @app.route('/wifi-events', methods=['POST'])                        │    │
│  │  def handle_webhook():                                               │    │
│  │      signature = request.headers.get('X-Webhook-Signature')          │    │
│  │      if not verify_signature(request.data, signature):               │    │
│  │          return jsonify({"error": "Invalid signature"}), 401         │    │
│  │                                                                      │    │
│  │      event = request.json                                            │    │
│  │      event_type = event.get('event')                                 │    │
│  │                                                                      │    │
│  │      if event_type == 'client.connect':                              │    │
│  │          handle_client_connect(event['data'])                        │    │
│  │      elif event_type == 'ap.offline':                                │    │
│  │          handle_ap_offline(event['data'])                            │    │
│  │                                                                      │    │
│  │      return jsonify({"status": "ok"}), 200                           │    │
│  │                                                                      │    │
│  │  def handle_client_connect(data):                                    │    │
│  │      print(f"Client {data['client_mac']} connected to {data['ssid']}")│   │
│  │      # Add to database, send notification, etc.                      │    │
│  │                                                                      │    │
│  │  def handle_ap_offline(data):                                        │    │
│  │      print(f"AP {data['ap_name']} went offline!")                    │    │
│  │      # Send alert, create ticket, etc.                               │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### DX.3 Automation Scripts

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    AUTOMATION SCRIPTS                                        │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  Python SDK Example:                                                         │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  import requests                                                     │    │
│  │  import json                                                         │    │
│  │                                                                      │    │
│  │  class WifiController:                                               │    │
│  │      def __init__(self, host, username, password):                   │    │
│  │          self.host = host                                            │    │
│  │          self.base_url = f"https://{host}/api/v1"                    │    │
│  │          self.token = self._authenticate(username, password)         │    │
│  │                                                                      │    │
│  │      def _authenticate(self, username, password):                    │    │
│  │          response = requests.post(                                   │    │
│  │              f"{self.base_url}/auth/login",                          │    │
│  │              json={"username": username, "password": password}       │    │
│  │          )                                                           │    │
│  │          return response.json()['token']                             │    │
│  │                                                                      │    │
│  │      def _headers(self):                                             │    │
│  │          return {"Authorization": f"Bearer {self.token}"}            │    │
│  │                                                                      │    │
│  │      def get_aps(self):                                              │    │
│  │          response = requests.get(                                    │    │
│  │              f"{self.base_url}/aps",                                 │    │
│  │              headers=self._headers()                                 │    │
│  │          )                                                           │    │
│  │          return response.json()['aps']                               │    │
│  │                                                                      │    │
│  │      def get_clients(self, ssid=None):                               │    │
│  │          params = {"ssid": ssid} if ssid else {}                     │    │
│  │          response = requests.get(                                    │    │
│  │              f"{self.base_url}/clients",                             │    │
│  │              headers=self._headers(),                                │    │
│  │              params=params                                           │    │
│  │          )                                                           │    │
│  │          return response.json()['clients']                           │    │
│  │                                                                      │    │
│  │      def disconnect_client(self, mac):                               │    │
│  │          response = requests.delete(                                 │    │
│  │              f"{self.base_url}/clients/{mac}",                       │    │
│  │              headers=self._headers()                                 │    │
│  │          )                                                           │    │
│  │          return response.status_code == 200                          │    │
│  │                                                                      │    │
│  │      def create_ssid(self, name, security, passphrase, vlan):        │    │
│  │          response = requests.post(                                   │    │
│  │              f"{self.base_url}/ssids",                               │    │
│  │              headers=self._headers(),                                │    │
│  │              json={                                                  │    │
│  │                  "name": name,                                       │    │
│  │                  "security": security,                               │    │
│  │                  "passphrase": passphrase,                           │    │
│  │                  "vlan": vlan,                                       │    │
│  │                  "enabled": True                                     │    │
│  │              }                                                       │    │
│  │          )                                                           │    │
│  │          return response.json()                                      │    │
│  │                                                                      │    │
│  │  # Usage                                                             │    │
│  │  controller = WifiController("10.1.1.100", "admin", "password")      │    │
│  │                                                                      │    │
│  │  # Get all APs                                                       │    │
│  │  aps = controller.get_aps()                                          │    │
│  │  for ap in aps:                                                      │    │
│  │      print(f"{ap['name']}: {ap['status']} ({ap['clients']} clients)")│    │
│  │                                                                      │    │
│  │  # Get clients on Guest SSID                                         │    │
│  │  guests = controller.get_clients(ssid="Guest")                       │    │
│  │  print(f"Guest clients: {len(guests)}")                              │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  Ansible Playbook Example:                                                   │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  ---                                                                 │    │
│  │  # wifi_config.yml                                                   │    │
│  │  - name: Configure WiFi Network                                      │    │
│  │    hosts: wifi_controllers                                           │    │
│  │    vars:                                                             │    │
│  │      controller_host: "{{ inventory_hostname }}"                     │    │
│  │      api_token: "{{ lookup('env', 'WIFI_API_TOKEN') }}"              │    │
│  │                                                                      │    │
│  │    tasks:                                                            │    │
│  │      - name: Create Corporate SSID                                   │    │
│  │        uri:                                                          │    │
│  │          url: "https://{{ controller_host }}/api/v1/ssids"           │    │
│  │          method: POST                                                │    │
│  │          headers:                                                    │    │
│  │            Authorization: "Bearer {{ api_token }}"                   │    │
│  │          body_format: json                                           │    │
│  │          body:                                                       │    │
│  │            name: "Corporate"                                         │    │
│  │            security: "wpa3-enterprise"                               │    │
│  │            radius_server: "10.1.1.50"                                │    │
│  │            vlan: 20                                                  │    │
│  │            enabled: true                                             │    │
│  │          status_code: [200, 201]                                     │    │
│  │                                                                      │    │
│  │      - name: Create Guest SSID                                       │    │
│  │        uri:                                                          │    │
│  │          url: "https://{{ controller_host }}/api/v1/ssids"           │    │
│  │          method: POST                                                │    │
│  │          headers:                                                    │    │
│  │            Authorization: "Bearer {{ api_token }}"                   │    │
│  │          body_format: json                                           │    │
│  │          body:                                                       │    │
│  │            name: "Guest"                                             │    │
│  │            security: "wpa2-psk"                                      │    │
│  │            passphrase: "{{ guest_password }}"                        │    │
│  │            vlan: 30                                                  │    │
│  │            client_isolation: true                                    │    │
│  │            enabled: true                                             │    │
│  │          status_code: [200, 201]                                     │    │
│  │                                                                      │    │
│  │      - name: Configure RF Profile                                    │    │
│  │        uri:                                                          │    │
│  │          url: "https://{{ controller_host }}/api/v1/rf-profiles"     │    │
│  │          method: POST                                                │    │
│  │          headers:                                                    │    │
│  │            Authorization: "Bearer {{ api_token }}"                   │    │
│  │          body_format: json                                           │    │
│  │          body:                                                       │    │
│  │            name: "High-Density"                                      │    │
│  │            band_2_4ghz:                                              │    │
│  │              tx_power: 9                                             │    │
│  │              channel_width: 20                                       │    │
│  │            band_5ghz:                                                │    │
│  │              tx_power: 12                                            │    │
│  │              channel_width: 40                                       │    │
│  │          status_code: [200, 201]                                     │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  Terraform Provider Example:                                                 │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  # main.tf                                                           │    │
│  │  terraform {                                                         │    │
│  │    required_providers {                                              │    │
│  │      wifi = {                                                        │    │
│  │        source  = "example/wifi"                                      │    │
│  │        version = "~> 1.0"                                            │    │
│  │      }                                                               │    │
│  │    }                                                                 │    │
│  │  }                                                                   │    │
│  │                                                                      │    │
│  │  provider "wifi" {                                                   │    │
│  │    host     = "10.1.1.100"                                           │    │
│  │    username = var.wifi_username                                      │    │
│  │    password = var.wifi_password                                      │    │
│  │  }                                                                   │    │
│  │                                                                      │    │
│  │  resource "wifi_ssid" "corporate" {                                  │    │
│  │    name     = "Corporate"                                            │    │
│  │    security = "wpa3-enterprise"                                      │    │
│  │    vlan     = 20                                                     │    │
│  │                                                                      │    │
│  │    radius {                                                          │    │
│  │      server = "10.1.1.50"                                            │    │
│  │      port   = 1812                                                   │    │
│  │      secret = var.radius_secret                                      │    │
│  │    }                                                                 │    │
│  │  }                                                                   │    │
│  │                                                                      │    │
│  │  resource "wifi_ssid" "guest" {                                      │    │
│  │    name             = "Guest"                                        │    │
│  │    security         = "wpa2-psk"                                     │    │
│  │    passphrase       = var.guest_password                             │    │
│  │    vlan             = 30                                             │    │
│  │    client_isolation = true                                           │    │
│  │  }                                                                   │    │
│  │                                                                      │    │
│  │  resource "wifi_rf_profile" "high_density" {                         │    │
│  │    name = "High-Density"                                             │    │
│  │                                                                      │    │
│  │    band_2_4ghz {                                                     │    │
│  │      tx_power      = 9                                               │    │
│  │      channel_width = 20                                              │    │
│  │    }                                                                 │    │
│  │                                                                      │    │
│  │    band_5ghz {                                                       │    │
│  │      tx_power      = 12                                              │    │
│  │      channel_width = 40                                              │    │
│  │    }                                                                 │    │
│  │  }                                                                   │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Appendix DY: Complete Glossary

### DY.1 Acronyms and Terms (A-M)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    GLOSSARY (A-M)                                            │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  A:                                                                          │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │ AAA        Authentication, Authorization, Accounting                │    │
│  │ AC         Access Category (QoS)                                    │    │
│  │ ACK        Acknowledgment                                           │    │
│  │ ACL        Access Control List                                      │    │
│  │ ACS        Automatic Channel Selection                              │    │
│  │ AES        Advanced Encryption Standard                             │    │
│  │ AFC        Automated Frequency Coordination (6 GHz)                 │    │
│  │ AIFSN      Arbitration Inter-Frame Space Number                     │    │
│  │ AKM        Authentication and Key Management                        │    │
│  │ AMPDU      Aggregated MAC Protocol Data Unit                        │    │
│  │ AMSDU      Aggregated MAC Service Data Unit                         │    │
│  │ ANI        Adaptive Noise Immunity                                  │    │
│  │ ANQP       Access Network Query Protocol                            │    │
│  │ AP         Access Point                                             │    │
│  │ ARP        Address Resolution Protocol                              │    │
│  │ ASRA       Additional Step Required for Access                      │    │
│  │ ATF        Airtime Fairness                                         │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  B:                                                                          │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │ BA         Block Acknowledgment                                     │    │
│  │ BAR        Block Acknowledgment Request                             │    │
│  │ BE         Best Effort (QoS)                                        │    │
│  │ BK         Background (QoS)                                         │    │
│  │ BPSK       Binary Phase Shift Keying                                │    │
│  │ BSS        Basic Service Set                                        │    │
│  │ BSSID      Basic Service Set Identifier                             │    │
│  │ BTM        BSS Transition Management                                │    │
│  │ BW         Bandwidth                                                │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  C:                                                                          │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │ CAC        Channel Availability Check (DFS)                         │    │
│  │ CAPWAP     Control and Provisioning of Wireless Access Points       │    │
│  │ CCA        Clear Channel Assessment                                 │    │
│  │ CCMP       Counter Mode with CBC-MAC Protocol                       │    │
│  │ CCI        Co-Channel Interference                                  │    │
│  │ CEF        Common Event Format                                      │    │
│  │ CFP        Contention-Free Period                                   │    │
│  │ CoA        Change of Authorization (RADIUS)                         │    │
│  │ CP         Contention Period                                        │    │
│  │ CRC        Cyclic Redundancy Check                                  │    │
│  │ CSA        Channel Switch Announcement                              │    │
│  │ CSI        Channel State Information                                │    │
│  │ CSMA/CA    Carrier Sense Multiple Access with Collision Avoidance   │    │
│  │ CTS        Clear to Send                                            │    │
│  │ CW         Contention Window                                        │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  D:                                                                          │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │ DA         Destination Address                                      │    │
│  │ DAS        Dynamic Authorization Server (RADIUS)                    │    │
│  │ dB         Decibel                                                  │    │
│  │ dBi        Decibel Isotropic                                        │    │
│  │ dBm        Decibel Milliwatt                                        │    │
│  │ DCF        Distributed Coordination Function                        │    │
│  │ DFS        Dynamic Frequency Selection                              │    │
│  │ DHCP       Dynamic Host Configuration Protocol                      │    │
│  │ DIFS       Distributed Inter-Frame Space                            │    │
│  │ DL         Downlink                                                 │    │
│  │ DM         Disconnect Message (RADIUS)                              │    │
│  │ DNS        Domain Name System                                       │    │
│  │ DPP        Device Provisioning Protocol                             │    │
│  │ DSCP       Differentiated Services Code Point                       │    │
│  │ DSS        Direct Sequence Spread Spectrum                          │    │
│  │ DTIM       Delivery Traffic Indication Map                          │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  E:                                                                          │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │ EAP        Extensible Authentication Protocol                       │    │
│  │ EAPOL      EAP over LAN                                             │    │
│  │ EDCA       Enhanced Distributed Channel Access                      │    │
│  │ EIRP       Effective Isotropic Radiated Power                       │    │
│  │ ESS        Extended Service Set                                     │    │
│  │ ESSID      Extended Service Set Identifier                          │    │
│  │ ETSI       European Telecommunications Standards Institute          │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  F:                                                                          │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │ FCC        Federal Communications Commission                        │    │
│  │ FCS        Frame Check Sequence                                     │    │
│  │ FFT        Fast Fourier Transform                                   │    │
│  │ FILS       Fast Initial Link Setup                                  │    │
│  │ FQDN       Fully Qualified Domain Name                              │    │
│  │ FT         Fast Transition (802.11r)                                │    │
│  │ FTM        Fine Timing Measurement                                  │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  G:                                                                          │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │ GAS        Generic Advertisement Service                            │    │
│  │ GCMP       Galois/Counter Mode Protocol                             │    │
│  │ GI         Guard Interval                                           │    │
│  │ GMK        Group Master Key                                         │    │
│  │ GPSK       Group Pre-Shared Key                                     │    │
│  │ GTK        Group Temporal Key                                       │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  H:                                                                          │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │ HA         High Availability                                        │    │
│  │ HE         High Efficiency (802.11ax)                               │    │
│  │ HESSID     Homogeneous Extended Service Set Identifier              │    │
│  │ HT         High Throughput (802.11n)                                │    │
│  │ HTTP       Hypertext Transfer Protocol                              │    │
│  │ HTTPS      HTTP Secure                                              │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  I:                                                                          │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │ IBSS       Independent Basic Service Set (Ad-hoc)                   │    │
│  │ IE         Information Element                                      │    │
│  │ IEEE       Institute of Electrical and Electronics Engineers        │    │
│  │ IGTK       Integrity Group Temporal Key                             │    │
│  │ IoT        Internet of Things                                       │    │
│  │ IP         Internet Protocol                                        │    │
│  │ ISM        Industrial, Scientific, Medical (band)                   │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  K:                                                                          │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │ KCK        Key Confirmation Key                                     │    │
│  │ KDK        Key Derivation Key                                       │    │
│  │ KEK        Key Encryption Key                                       │    │
│  │ KRACK      Key Reinstallation Attack                                │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  L:                                                                          │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │ LDPC       Low-Density Parity-Check                                 │    │
│  │ LLC        Logical Link Control                                     │    │
│  │ LPI        Low Power Indoor (6 GHz)                                 │    │
│  │ LTE        Long-Term Evolution                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  M:                                                                          │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │ MAC        Media Access Control                                     │    │
│  │ MBO        Multi-Band Operation                                     │    │
│  │ MBSS       Mesh Basic Service Set                                   │    │
│  │ MCS        Modulation and Coding Scheme                             │    │
│  │ mDNS       Multicast DNS                                            │    │
│  │ MFP        Management Frame Protection                              │    │
│  │ MIC        Message Integrity Code                                   │    │
│  │ MIMO       Multiple Input Multiple Output                           │    │
│  │ MLO        Multi-Link Operation (802.11be)                          │    │
│  │ MPDU       MAC Protocol Data Unit                                   │    │
│  │ MSDU       MAC Service Data Unit                                    │    │
│  │ MSK        Master Session Key                                       │    │
│  │ MU-MIMO    Multi-User MIMO                                          │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### DY.2 Acronyms and Terms (N-Z)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    GLOSSARY (N-Z)                                            │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  N:                                                                          │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │ NAC        Network Access Control                                   │    │
│  │ NAS        Network Access Server                                    │    │
│  │ NAT        Network Address Translation                              │    │
│  │ NDP        Null Data Packet                                         │    │
│  │ NIC        Network Interface Card                                   │    │
│  │ NTP        Network Time Protocol                                    │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  O:                                                                          │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │ OBSS       Overlapping Basic Service Set                            │    │
│  │ OCE        Optimized Connectivity Experience                        │    │
│  │ OFDM       Orthogonal Frequency Division Multiplexing               │    │
│  │ OFDMA      Orthogonal Frequency Division Multiple Access            │    │
│  │ OKC        Opportunistic Key Caching                                │    │
│  │ OUI        Organizationally Unique Identifier                       │    │
│  │ OWE        Opportunistic Wireless Encryption                        │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  P:                                                                          │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │ PBSS       Personal Basic Service Set                               │    │
│  │ PCF        Point Coordination Function                              │    │
│  │ PEAP       Protected EAP                                            │    │
│  │ PHY        Physical Layer                                           │    │
│  │ PLCP       Physical Layer Convergence Procedure                     │    │
│  │ PMF        Protected Management Frames                              │    │
│  │ PMK        Pairwise Master Key                                      │    │
│  │ PMKID      PMK Identifier                                           │    │
│  │ PMKSA      PMK Security Association                                 │    │
│  │ PN         Packet Number                                            │    │
│  │ PoE        Power over Ethernet                                      │    │
│  │ PPDU       PLCP Protocol Data Unit                                  │    │
│  │ PRF        Pseudo-Random Function                                   │    │
│  │ PSK        Pre-Shared Key                                           │    │
│  │ PTK        Pairwise Transient Key                                   │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  Q:                                                                          │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │ QAM        Quadrature Amplitude Modulation                          │    │
│  │ QoS        Quality of Service                                       │    │
│  │ QPSK       Quadrature Phase Shift Keying                            │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  R:                                                                          │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │ RA         Receiver Address                                         │    │
│  │ RADIUS     Remote Authentication Dial-In User Service               │    │
│  │ RF         Radio Frequency                                          │    │
│  │ RRM        Radio Resource Management                                │    │
│  │ RSN        Robust Security Network                                  │    │
│  │ RSNA       RSN Association                                          │    │
│  │ RSSI       Received Signal Strength Indicator                       │    │
│  │ RTS        Request to Send                                          │    │
│  │ RU         Resource Unit (OFDMA)                                    │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  S:                                                                          │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │ SA         Source Address                                           │    │
│  │ SAE        Simultaneous Authentication of Equals                    │    │
│  │ SC         Sequence Control                                         │    │
│  │ SIFS       Short Inter-Frame Space                                  │    │
│  │ SIM        Subscriber Identity Module                               │    │
│  │ SISO       Single Input Single Output                               │    │
│  │ SNAP       Subnetwork Access Protocol                               │    │
│  │ SNR        Signal-to-Noise Ratio                                    │    │
│  │ SP         Service Period                                           │    │
│  │ SPI        Standard Power Indoor (6 GHz)                            │    │
│  │ SSID       Service Set Identifier                                   │    │
│  │ STA        Station (client)                                         │    │
│  │ STBC       Space-Time Block Coding                                  │    │
│  │ SU-MIMO    Single-User MIMO                                         │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  T:                                                                          │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │ TA         Transmitter Address                                      │    │
│  │ TBTT       Target Beacon Transmission Time                          │    │
│  │ TCP        Transmission Control Protocol                            │    │
│  │ TIM        Traffic Indication Map                                   │    │
│  │ TK         Temporal Key                                             │    │
│  │ TKIP       Temporal Key Integrity Protocol                          │    │
│  │ TLS        Transport Layer Security                                 │    │
│  │ TPC        Transmit Power Control                                   │    │
│  │ TSF        Timing Synchronization Function                          │    │
│  │ TTLS       Tunneled TLS                                             │    │
│  │ TWT        Target Wake Time                                         │    │
│  │ TXOP       Transmission Opportunity                                 │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  U:                                                                          │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │ UDP        User Datagram Protocol                                   │    │
│  │ UL         Uplink                                                   │    │
│  │ UNII       Unlicensed National Information Infrastructure          │    │
│  │ UPSK       Unique Pre-Shared Key                                    │    │
│  │ URL        Uniform Resource Locator                                 │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  V:                                                                          │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │ VHT        Very High Throughput (802.11ac)                          │    │
│  │ VI         Video (QoS)                                              │    │
│  │ VLAN       Virtual Local Area Network                               │    │
│  │ VO         Voice (QoS)                                              │    │
│  │ VoIP       Voice over IP                                            │    │
│  │ VoWiFi     Voice over WiFi                                          │    │
│  │ VSA        Vendor-Specific Attribute                                │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  W:                                                                          │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │ WDS        Wireless Distribution System                             │    │
│  │ WEP        Wired Equivalent Privacy                                 │    │
│  │ WIDS       Wireless Intrusion Detection System                      │    │
│  │ WIPS       Wireless Intrusion Prevention System                     │    │
│  │ WLAN       Wireless Local Area Network                              │    │
│  │ WMM        WiFi Multimedia                                          │    │
│  │ WNM        Wireless Network Management                              │    │
│  │ WPA        WiFi Protected Access                                    │    │
│  │ WPA2       WiFi Protected Access 2                                  │    │
│  │ WPA3       WiFi Protected Access 3                                  │    │
│  │ WPS        WiFi Protected Setup                                     │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  X-Z:                                                                        │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │ XR         Extended Reality (VR/AR/MR)                              │    │
│  │ ZMQ        ZeroMQ (messaging library)                               │    │
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
| 3.1 | 2026-01-08 | Auto-generated | Added WiFi 7 MLO, puncturing, 4K-QAM, multi-RU, enhanced security |
| 3.2 | 2026-01-08 | Auto-generated | Added FILS, DPP, enterprise security, certificate management |
| 3.3 | 2026-01-08 | Auto-generated | Added power management, airtime fairness, channel utilization |
| 3.4 | 2026-01-08 | Auto-generated | Added client steering, band selection, load balancing algorithms |
| 3.5 | 2026-01-08 | Auto-generated | Added mesh networking, WDS, repeater modes, backhaul optimization |
| 3.6 | 2026-01-08 | Auto-generated | Added roaming protocols, 802.11k/v/r deep dive, seamless handoff |
| 3.7 | 2026-01-08 | Auto-generated | Added DHCP deep dive, DNS, mDNS, service discovery |
| 3.8 | 2026-01-08 | Auto-generated | Added firewall policies, ACLs, traffic filtering, NAT |
| 3.9 | 2026-01-08 | Auto-generated | Added IoT device profiling, device fingerprinting, MAC randomization |
| 4.0 | 2026-01-08 | Auto-generated | Added CLI command reference, API reference, automation |
| 4.1 | 2026-01-08 | Auto-generated | Added network automation, scripting, integration examples |
| 4.2 | 2026-01-08 | Auto-generated | Added site survey, capacity planning, deployment best practices |
| 4.3 | 2026-01-08 | Auto-generated | Added troubleshooting runbook, migration guide, vendor interoperability |
| 4.4 | 2026-01-08 | Auto-generated | Added high availability, disaster recovery, backup strategies |
| 4.5 | 2026-01-08 | Auto-generated | Added spectrum analysis, interference mitigation, RF optimization |
| 4.6 | 2026-01-08 | Auto-generated | Added API integration, webhooks, automation scripts |
| 4.7 | 2026-01-08 | Auto-generated | Added reference architecture, deployment patterns, design templates |

---

## Appendix DZ: Reference Architecture

### DZ.1 Enterprise Campus Deployment

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    ENTERPRISE CAMPUS DEPLOYMENT                              │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  Campus Network Topology:                                                    │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │                        ┌─────────────────┐                           │    │
│  │                        │   Internet      │                           │    │
│  │                        └────────┬────────┘                           │    │
│  │                                 │                                    │    │
│  │                        ┌────────┴────────┐                           │    │
│  │                        │    Firewall     │                           │    │
│  │                        └────────┬────────┘                           │    │
│  │                                 │                                    │    │
│  │                        ┌────────┴────────┐                           │    │
│  │                        │  Core Switch    │                           │    │
│  │                        │  (Layer 3)      │                           │    │
│  │                        └────────┬────────┘                           │    │
│  │                                 │                                    │    │
│  │         ┌───────────────────────┼───────────────────────┐            │    │
│  │         │                       │                       │            │    │
│  │  ┌──────┴──────┐         ┌──────┴──────┐         ┌──────┴──────┐     │    │
│  │  │ Distribution│         │ Distribution│         │ Distribution│     │    │
│  │  │ Switch Bldg1│         │ Switch Bldg2│         │ Switch Bldg3│     │    │
│  │  └──────┬──────┘         └──────┬──────┘         └──────┬──────┘     │    │
│  │         │                       │                       │            │    │
│  │    ┌────┴────┐             ┌────┴────┐             ┌────┴────┐       │    │
│  │    │         │             │         │             │         │       │    │
│  │  ┌─┴─┐     ┌─┴─┐         ┌─┴─┐     ┌─┴─┐         ┌─┴─┐     ┌─┴─┐     │    │
│  │  │IDF│     │IDF│         │IDF│     │IDF│         │IDF│     │IDF│     │    │
│  │  │ 1 │     │ 2 │         │ 1 │     │ 2 │         │ 1 │     │ 2 │     │    │
│  │  └─┬─┘     └─┬─┘         └─┬─┘     └─┬─┘         └─┬─┘     └─┬─┘     │    │
│  │    │         │             │         │             │         │       │    │
│  │  ◉◉◉◉      ◉◉◉◉          ◉◉◉◉      ◉◉◉◉          ◉◉◉◉      ◉◉◉◉     │    │
│  │  APs       APs           APs       APs           APs       APs      │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  Controller Placement:                                                       │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  ┌────────────────────────────────────────────────────────────┐     │    │
│  │  │ Deployment Size    Controller Location    Redundancy       │     │    │
│  │  │ ───────────────    ───────────────────    ──────────       │     │    │
│  │  │ Small (<50 APs)    Single building        N+1              │     │    │
│  │  │ Medium (50-200)    Data center            Active-Standby   │     │    │
│  │  │ Large (200-1000)   Data center            Active-Active    │     │    │
│  │  │ Enterprise (1000+) Multiple DC            Geo-redundant    │     │    │
│  │  └────────────────────────────────────────────────────────────┘     │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  VLAN Design:                                                                │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  ┌────────────────────────────────────────────────────────────┐     │    │
│  │  │ VLAN ID    Name              Purpose                       │     │    │
│  │  │ ───────    ────              ───────                       │     │    │
│  │  │ 10         Management        AP management traffic         │     │    │
│  │  │ 20         Corporate         Employee devices              │     │    │
│  │  │ 30         Guest             Guest/visitor access          │     │    │
│  │  │ 40         IoT               IoT devices                   │     │    │
│  │  │ 50         Voice             VoIP phones                   │     │    │
│  │  │ 60         Video             Video conferencing            │     │    │
│  │  │ 100        RADIUS            RADIUS server                 │     │    │
│  │  │ 200        DMZ               Guest internet access         │     │    │
│  │  └────────────────────────────────────────────────────────────┘     │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### DZ.2 Branch Office Deployment

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    BRANCH OFFICE DEPLOYMENT                                  │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  Branch Architecture:                                                        │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  ┌─────────────────────────────────────────────────────────────┐    │    │
│  │  │                     Headquarters                             │    │    │
│  │  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐          │    │    │
│  │  │  │ Controller  │  │   RADIUS    │  │    DHCP     │          │    │    │
│  │  │  │  (Primary)  │  │   Server    │  │   Server    │          │    │    │
│  │  │  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘          │    │    │
│  │  │         └────────────────┼────────────────┘                  │    │    │
│  │  │                          │                                   │    │    │
│  │  │                   ┌──────┴──────┐                            │    │    │
│  │  │                   │  WAN Router │                            │    │    │
│  │  │                   └──────┬──────┘                            │    │    │
│  │  └──────────────────────────┼───────────────────────────────────┘    │    │
│  │                             │                                        │    │
│  │                        ┌────┴────┐                                   │    │
│  │                        │   WAN   │                                   │    │
│  │                        │ (MPLS/  │                                   │    │
│  │                        │ VPN)    │                                   │    │
│  │                        └────┬────┘                                   │    │
│  │                             │                                        │    │
│  │  ┌──────────────────────────┼───────────────────────────────────┐    │    │
│  │  │                     Branch Office                            │    │    │
│  │  │                   ┌──────┴──────┐                            │    │    │
│  │  │                   │ Branch      │                            │    │    │
│  │  │                   │ Router      │                            │    │    │
│  │  │                   └──────┬──────┘                            │    │    │
│  │  │                          │                                   │    │    │
│  │  │                   ┌──────┴──────┐                            │    │    │
│  │  │                   │   Switch    │                            │    │    │
│  │  │                   └──────┬──────┘                            │    │    │
│  │  │                          │                                   │    │    │
│  │  │              ┌───────────┼───────────┐                       │    │    │
│  │  │              │           │           │                       │    │    │
│  │  │            ◉ AP1      ◉ AP2      ◉ AP3                       │    │    │
│  │  │                                                              │    │    │
│  │  └──────────────────────────────────────────────────────────────┘    │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  Branch Survivability:                                                       │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  When WAN is down:                                                   │    │
│  │  - APs continue serving existing clients                             │    │
│  │  - Local DHCP server provides IP addresses                           │    │
│  │  - Cached authentication allows reconnection                         │    │
│  │  - Local DNS resolution for cached entries                           │    │
│  │                                                                      │    │
│  │  Configuration:                                                      │    │
│  │  ┌────────────────────────────────────────────────────────────┐     │    │
│  │  │ # Enable survivability mode                                │     │    │
│  │  │ ap-group Branch-APs                                        │     │    │
│  │  │   survivability enable                                     │     │    │
│  │  │   survivability auth-cache-timeout 86400                   │     │    │
│  │  │   survivability local-dhcp enable                          │     │    │
│  │  │   survivability local-dhcp pool 10.100.0.0/24              │     │    │
│  │  └────────────────────────────────────────────────────────────┘     │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### DZ.3 Multi-Site Deployment

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    MULTI-SITE DEPLOYMENT                                     │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  Global Architecture:                                                        │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  ┌─────────────────────────────────────────────────────────────┐    │    │
│  │  │                    Cloud Management                          │    │    │
│  │  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐          │    │    │
│  │  │  │   Central   │  │   Global    │  │   License   │          │    │    │
│  │  │  │  Dashboard  │  │  Analytics  │  │   Server    │          │    │    │
│  │  │  └─────────────┘  └─────────────┘  └─────────────┘          │    │    │
│  │  └─────────────────────────────────────────────────────────────┘    │    │
│  │                             │                                        │    │
│  │         ┌───────────────────┼───────────────────┐                    │    │
│  │         │                   │                   │                    │    │
│  │  ┌──────┴──────┐     ┌──────┴──────┐     ┌──────┴──────┐            │    │
│  │  │   Region    │     │   Region    │     │   Region    │            │    │
│  │  │   Americas  │     │    EMEA     │     │    APAC     │            │    │
│  │  └──────┬──────┘     └──────┬──────┘     └──────┬──────┘            │    │
│  │         │                   │                   │                    │    │
│  │    ┌────┴────┐         ┌────┴────┐         ┌────┴────┐              │    │
│  │    │         │         │         │         │         │              │    │
│  │  ┌─┴─┐     ┌─┴─┐     ┌─┴─┐     ┌─┴─┐     ┌─┴─┐     ┌─┴─┐            │    │
│  │  │NYC│     │LAX│     │LON│     │FRA│     │SIN│     │TKY│            │    │
│  │  │DC │     │DC │     │DC │     │DC │     │DC │     │DC │            │    │
│  │  └─┬─┘     └─┬─┘     └─┬─┘     └─┬─┘     └─┬─┘     └─┬─┘            │    │
│  │    │         │         │         │         │         │              │    │
│  │  Sites     Sites     Sites     Sites     Sites     Sites            │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  Regional Controller Design:                                                 │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  ┌────────────────────────────────────────────────────────────┐     │    │
│  │  │ Region      Primary DC    Secondary DC    Sites Managed    │     │    │
│  │  │ ──────      ──────────    ────────────    ─────────────    │     │    │
│  │  │ Americas    New York      Los Angeles     150              │     │    │
│  │  │ EMEA        London        Frankfurt       120              │     │    │
│  │  │ APAC        Singapore     Tokyo           100              │     │    │
│  │  └────────────────────────────────────────────────────────────┘     │    │
│  │                                                                      │    │
│  │  Failover Strategy:                                                  │    │
│  │  - Primary DC handles all sites in region                            │    │
│  │  - Secondary DC takes over if primary fails                          │    │
│  │  - Cross-region failover for disaster recovery                       │    │
│  │  - Cloud management provides global visibility                       │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Appendix EA: Complete Configuration Templates

### EA.1 Enterprise SSID Configuration

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    ENTERPRISE SSID CONFIGURATION                             │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  Corporate SSID (802.1X):                                                    │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  ssid Corporate                                                      │    │
│  │    enable                                                            │    │
│  │    broadcast                                                         │    │
│  │    security wpa3-enterprise                                          │    │
│  │    pmf required                                                      │    │
│  │    vlan 20                                                           │    │
│  │                                                                      │    │
│  │    # RADIUS configuration                                            │    │
│  │    radius-server primary 10.1.1.50 1812 secret RadiusSecret123       │    │
│  │    radius-server secondary 10.1.1.51 1812 secret RadiusSecret123     │    │
│  │    radius-accounting enable                                          │    │
│  │    radius-accounting server 10.1.1.50 1813 secret RadiusSecret123    │    │
│  │    radius-accounting interim-interval 300                            │    │
│  │                                                                      │    │
│  │    # Fast roaming                                                    │    │
│  │    fast-transition enable                                            │    │
│  │    fast-transition over-ds enable                                    │    │
│  │    okc enable                                                        │    │
│  │                                                                      │    │
│  │    # Client management                                               │    │
│  │    band-steering enable                                              │    │
│  │    band-steering mode prefer-5ghz                                    │    │
│  │    load-balancing enable                                             │    │
│  │    load-balancing threshold 50                                       │    │
│  │                                                                      │    │
│  │    # QoS                                                             │    │
│  │    wmm enable                                                        │    │
│  │    wmm-uapsd enable                                                  │    │
│  │                                                                      │    │
│  │    # Timeouts                                                        │    │
│  │    session-timeout 28800                                             │    │
│  │    idle-timeout 1800                                                 │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  Guest SSID (Captive Portal):                                                │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  ssid Guest                                                          │    │
│  │    enable                                                            │    │
│  │    broadcast                                                         │    │
│  │    security owe-transition                                           │    │
│  │    vlan 30                                                           │    │
│  │                                                                      │    │
│  │    # Captive portal                                                  │    │
│  │    captive-portal enable                                             │    │
│  │    captive-portal type external                                      │    │
│  │    captive-portal url https://guest.company.com/portal               │    │
│  │    captive-portal redirect-url https://www.company.com               │    │
│  │    captive-portal session-timeout 14400                              │    │
│  │                                                                      │    │
│  │    # Client isolation                                                │    │
│  │    client-isolation enable                                           │    │
│  │    client-isolation mode full                                        │    │
│  │                                                                      │    │
│  │    # Rate limiting                                                   │    │
│  │    rate-limit downstream 10000                                       │    │
│  │    rate-limit upstream 5000                                          │    │
│  │                                                                      │    │
│  │    # Firewall                                                        │    │
│  │    firewall deny-inter-user-traffic                                  │    │
│  │    firewall allow-dhcp                                               │    │
│  │    firewall allow-dns                                                │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  IoT SSID (WPA2-PSK):                                                        │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  ssid IoT-Devices                                                    │    │
│  │    enable                                                            │    │
│  │    no broadcast                                                      │    │
│  │    security wpa2-psk                                                 │    │
│  │    passphrase IoTSecurePass2024!                                     │    │
│  │    vlan 40                                                           │    │
│  │                                                                      │    │
│  │    # MAC filtering                                                   │    │
│  │    mac-filter enable                                                 │    │
│  │    mac-filter mode whitelist                                         │    │
│  │    mac-filter list IoT-Devices-List                                  │    │
│  │                                                                      │    │
│  │    # Client isolation                                                │    │
│  │    client-isolation enable                                           │    │
│  │                                                                      │    │
│  │    # Rate limiting                                                   │    │
│  │    rate-limit downstream 1000                                        │    │
│  │    rate-limit upstream 500                                           │    │
│  │                                                                      │    │
│  │    # Restrict to 2.4 GHz only                                        │    │
│  │    radio 2.4ghz enable                                               │    │
│  │    radio 5ghz disable                                                │    │
│  │    radio 6ghz disable                                                │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### EA.2 RF Profile Configuration

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    RF PROFILE CONFIGURATION                                  │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  High-Density Profile:                                                       │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  rf-profile High-Density                                             │    │
│  │    description "Conference rooms, auditoriums, cafeterias"           │    │
│  │                                                                      │    │
│  │    # 2.4 GHz settings                                                │    │
│  │    radio 2.4ghz                                                      │    │
│  │      tx-power 6                                                      │    │
│  │      channel-width 20                                                │    │
│  │      channels 1,6,11                                                 │    │
│  │      min-data-rate 12                                                │    │
│  │      max-clients 50                                                  │    │
│  │                                                                      │    │
│  │    # 5 GHz settings                                                  │    │
│  │    radio 5ghz                                                        │    │
│  │      tx-power 9                                                      │    │
│  │      channel-width 40                                                │    │
│  │      channels 36,40,44,48,149,153,157,161                            │    │
│  │      min-data-rate 24                                                │    │
│  │      max-clients 100                                                 │    │
│  │                                                                      │    │
│  │    # 6 GHz settings                                                  │    │
│  │    radio 6ghz                                                        │    │
│  │      tx-power 12                                                     │    │
│  │      channel-width 80                                                │    │
│  │      min-data-rate 24                                                │    │
│  │      max-clients 150                                                 │    │
│  │                                                                      │    │
│  │    # Client management                                               │    │
│  │    band-steering enable                                              │    │
│  │    band-steering mode prefer-6ghz                                    │    │
│  │    load-balancing enable                                             │    │
│  │    load-balancing threshold 40                                       │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  Standard Office Profile:                                                    │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  rf-profile Standard-Office                                          │    │
│  │    description "Open office areas, cubicles"                         │    │
│  │                                                                      │    │
│  │    # 2.4 GHz settings                                                │    │
│  │    radio 2.4ghz                                                      │    │
│  │      tx-power 12                                                     │    │
│  │      channel-width 20                                                │    │
│  │      channels 1,6,11                                                 │    │
│  │      min-data-rate 6                                                 │    │
│  │      max-clients 75                                                  │    │
│  │                                                                      │    │
│  │    # 5 GHz settings                                                  │    │
│  │    radio 5ghz                                                        │    │
│  │      tx-power 15                                                     │    │
│  │      channel-width 80                                                │    │
│  │      min-data-rate 12                                                │    │
│  │      max-clients 150                                                 │    │
│  │      dfs enable                                                      │    │
│  │                                                                      │    │
│  │    # 6 GHz settings                                                  │    │
│  │    radio 6ghz                                                        │    │
│  │      tx-power 18                                                     │    │
│  │      channel-width 160                                               │    │
│  │      min-data-rate 24                                                │    │
│  │      max-clients 200                                                 │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  Warehouse Profile:                                                          │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  rf-profile Warehouse                                                │    │
│  │    description "Large open spaces, warehouses, manufacturing"        │    │
│  │                                                                      │    │
│  │    # 2.4 GHz settings                                                │    │
│  │    radio 2.4ghz                                                      │    │
│  │      tx-power 18                                                     │    │
│  │      channel-width 20                                                │    │
│  │      channels 1,6,11                                                 │    │
│  │      min-data-rate 6                                                 │    │
│  │                                                                      │    │
│  │    # 5 GHz settings                                                  │    │
│  │    radio 5ghz                                                        │    │
│  │      tx-power 21                                                     │    │
│  │      channel-width 40                                                │    │
│  │      min-data-rate 12                                                │    │
│  │                                                                      │    │
│  │    # Antenna settings                                                │    │
│  │    antenna-type directional                                          │    │
│  │    antenna-gain 6                                                    │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

