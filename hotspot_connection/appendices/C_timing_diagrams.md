## Appendix C: Timing Diagrams

### C.1 Complete Connection Timeline

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    COMPLETE CONNECTION TIMELINE                              │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  Time (ms)   Event                                                          │
│  ─────────   ─────                                                          │
│                                                                              │
│  0           Client starts scanning                                          │
│  │                                                                           │
│  │  ┌─────────────────────────────────────────────────────────────────┐     │
│  │  │ Passive scan: Wait for beacons (100ms per channel)              │     │
│  │  │ Active scan: Send probe, wait for response (10-20ms per channel)│     │
│  │  └─────────────────────────────────────────────────────────────────┘     │
│  │                                                                           │
│  100-2000    Scanning complete (depends on channels and method)              │
│  │                                                                           │
│  │  ┌─────────────────────────────────────────────────────────────────┐     │
│  │  │ Client selects best AP based on:                                │     │
│  │  │ - Signal strength (RSSI)                                        │     │
│  │  │ - Security match                                                 │     │
│  │  │ - Preferred network list                                         │     │
│  │  └─────────────────────────────────────────────────────────────────┘     │
│  │                                                                           │
│  2001        Authentication Request sent                                     │
│  2002        Authentication Response received                                │
│  │                                                                           │
│  │  ┌─────────────────────────────────────────────────────────────────┐     │
│  │  │ Open System: 2 frames, ~1-2ms                                   │     │
│  │  │ SAE: 4 frames, ~10-50ms (crypto operations)                     │     │
│  │  └─────────────────────────────────────────────────────────────────┘     │
│  │                                                                           │
│  2003        Association Request sent                                        │
│  2004        Association Response received                                   │
│  │                                                                           │
│  │  ┌─────────────────────────────────────────────────────────────────┐     │
│  │  │ Association: 2 frames, ~1-2ms                                   │     │
│  │  └─────────────────────────────────────────────────────────────────┘     │
│  │                                                                           │
│  2005        EAPOL-Key Message 1 (ANonce)                                    │
│  2006        EAPOL-Key Message 2 (SNonce, MIC)                               │
│  2007        EAPOL-Key Message 3 (GTK, MIC)                                  │
│  2008        EAPOL-Key Message 4 (MIC)                                       │
│  │                                                                           │
│  │  ┌─────────────────────────────────────────────────────────────────┐     │
│  │  │ 4-Way Handshake: 4 frames, ~5-20ms                              │     │
│  │  └─────────────────────────────────────────────────────────────────┘     │
│  │                                                                           │
│  2009        Keys installed, encryption active                               │
│  │                                                                           │
│  2010        DHCP Discover                                                   │
│  2050        DHCP Offer                                                      │
│  2051        DHCP Request                                                    │
│  2100        DHCP ACK                                                        │
│  │                                                                           │
│  │  ┌─────────────────────────────────────────────────────────────────┐     │
│  │  │ DHCP: 4 frames, ~50-500ms (depends on server)                   │     │
│  │  └─────────────────────────────────────────────────────────────────┘     │
│  │                                                                           │
│  2101        IP address configured                                           │
│  │                                                                           │
│  2102        ARP for gateway                                                 │
│  2103        ARP response                                                    │
│  │                                                                           │
│  2104        ════════════════════════════════════════════════════════       │
│              CLIENT FULLY CONNECTED                                          │
│              ════════════════════════════════════════════════════════       │
│                                                                              │
│  Total time: ~2-3 seconds (typical)                                          │
│                                                                              │
│  With 802.1X: Add 500-2000ms for EAP exchange                               │
│  With Captive Portal: Add 5-30 seconds for user interaction                 │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

