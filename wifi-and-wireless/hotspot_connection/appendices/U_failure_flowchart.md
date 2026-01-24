## Appendix U: Connection Failure Flowchart

### U.1 Troubleshooting Decision Tree

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    CONNECTION FAILURE TROUBLESHOOTING                        │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  START: Client cannot connect                                                │
│     │                                                                        │
│     ▼                                                                        │
│  ┌─────────────────────────────────────┐                                     │
│  │ Can client see SSID in scan?        │                                     │
│  └─────────────────────────────────────┘                                     │
│     │                                                                        │
│     ├── NO ──► Check:                                                        │
│     │          • AP is broadcasting (hidden SSID?)                           │
│     │          • Client supports band (2.4/5/6 GHz)                          │
│     │          • Regulatory domain matches                                   │
│     │          • Client is in range                                          │
│     │          • No RF interference                                          │
│     │                                                                        │
│     ▼ YES                                                                    │
│  ┌─────────────────────────────────────┐                                     │
│  │ Does authentication succeed?        │                                     │
│  └─────────────────────────────────────┘                                     │
│     │                                                                        │
│     ├── NO ──► Check:                                                        │
│     │          • Correct password/credentials                                │
│     │          • Security mode matches (WPA2/WPA3)                           │
│     │          • SAE anti-clogging (WPA3)                                    │
│     │          • RADIUS server reachable (Enterprise)                        │
│     │          • Certificate valid (EAP-TLS)                                 │
│     │          • MFP compatibility (802.11w)                                 │
│     │                                                                        │
│     ▼ YES                                                                    │
│  ┌─────────────────────────────────────┐                                     │
│  │ Does association succeed?           │                                     │
│  └─────────────────────────────────────┘                                     │
│     │                                                                        │
│     ├── NO ──► Check:                                                        │
│     │          • Max clients reached                                         │
│     │          • MAC filtering                                               │
│     │          • Capability mismatch                                         │
│     │          • Load balancing rejection                                    │
│     │                                                                        │
│     ▼ YES                                                                    │
│  ┌─────────────────────────────────────┐                                     │
│  │ Does 4-way handshake complete?      │                                     │
│  └─────────────────────────────────────┘                                     │
│     │                                                                        │
│     ├── NO ──► Check:                                                        │
│     │          • PMK mismatch (wrong password)                               │
│     │          • MIC failure                                                 │
│     │          • Timeout (increase wpa_ptk_rekey)                            │
│     │          • RADIUS key delivery (MS-MPPE-*)                             │
│     │          • Replay counter issues                                       │
│     │                                                                        │
│     ▼ YES                                                                    │
│  ┌─────────────────────────────────────┐                                     │
│  │ Does client get IP address?         │                                     │
│  └─────────────────────────────────────┘                                     │
│     │                                                                        │
│     ├── NO ──► Check:                                                        │
│     │          • DHCP server running                                         │
│     │          • DHCP pool not exhausted                                     │
│     │          • VLAN configuration                                          │
│     │          • Firewall rules                                              │
│     │          • Client DHCP enabled                                         │
│     │                                                                        │
│     ▼ YES                                                                    │
│  ┌─────────────────────────────────────┐                                     │
│  │ Can client reach gateway?           │                                     │
│  └─────────────────────────────────────┘                                     │
│     │                                                                        │
│     ├── NO ──► Check:                                                        │
│     │          • Gateway IP correct                                          │
│     │          • ARP resolution                                              │
│     │          • VLAN routing                                                │
│     │          • Firewall rules                                              │
│     │                                                                        │
│     ▼ YES                                                                    │
│  ┌─────────────────────────────────────┐                                     │
│  │ Can client reach internet?          │                                     │
│  └─────────────────────────────────────┘                                     │
│     │                                                                        │
│     ├── NO ──► Check:                                                        │
│     │          • Captive portal redirect                                     │
│     │          • DNS resolution                                              │
│     │          • NAT configuration                                           │
│     │          • Upstream connectivity                                       │
│     │          • Walled garden (if captive portal)                           │
│     │                                                                        │
│     ▼ YES                                                                    │
│  ┌─────────────────────────────────────┐                                     │
│  │ CONNECTION SUCCESSFUL               │                                     │
│  └─────────────────────────────────────┘                                     │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

