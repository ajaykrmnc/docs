## Appendix V: Quick Reference Card

### V.1 Connection Timeline Summary

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    QUICK REFERENCE: CONNECTION TIMELINE                      │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  Phase          Frames                    Duration    Key Points            │
│  ─────          ──────                    ────────    ──────────            │
│  Discovery      Probe Req/Resp            100-500ms   Passive or active     │
│                 or Beacon                             scan                   │
│                                                                              │
│  Authentication Auth Req/Resp             10-50ms     Open System or SAE    │
│                 (SAE: Commit/Confirm)     (SAE: 50-200ms)                   │
│                                                                              │
│  Association    Assoc Req/Resp            10-50ms     Capability exchange   │
│                                                                              │
│  802.1X/EAP     EAP-Request/Response      500-5000ms  Only for Enterprise   │
│                 (multiple rounds)                                            │
│                                                                              │
│  4-Way HS       EAPOL-Key M1-M4           50-200ms    PTK/GTK derivation    │
│                                                                              │
│  DHCP           Discover/Offer/           100-500ms   IP assignment         │
│                 Request/ACK                                                  │
│                                                                              │
│  Captive Portal HTTP Redirect             1-30s       User interaction      │
│                 (if enabled)                                                 │
│                                                                              │
│  ─────────────────────────────────────────────────────────────────────────  │
│  TOTAL (PSK)    ~500ms - 2s                                                  │
│  TOTAL (Enterprise) ~2s - 10s                                                │
│  TOTAL (with Captive Portal) ~10s - 60s (user dependent)                     │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### V.2 Key Sizes Reference

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    QUICK REFERENCE: KEY SIZES                                │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  Key             Size (bits)   Size (bytes)   Purpose                       │
│  ───             ───────────   ────────────   ───────                       │
│  MSK             512           64             Master Session Key            │
│  PMK             256           32             Pairwise Master Key           │
│  PTK (CCMP)      384           48             Pairwise Transient Key        │
│  PTK (GCMP-256)  512           64             PTK for GCMP-256              │
│  KCK             128           16             Key Confirmation Key          │
│  KEK             128           16             Key Encryption Key            │
│  TK (CCMP)       128           16             Temporal Key                  │
│  TK (GCMP-256)   256           32             TK for GCMP-256               │
│  GMK             256           32             Group Master Key              │
│  GTK             128/256       16/32          Group Temporal Key            │
│  IGTK            128/256       16/32          Integrity GTK (MFP)           │
│  ANonce          256           32             Authenticator Nonce           │
│  SNonce          256           32             Supplicant Nonce              │
│  PMK-R0          256           32             FT Root Key                   │
│  PMK-R1          256           32             FT Pairwise Key               │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### V.3 Port Numbers Reference

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    QUICK REFERENCE: PORT NUMBERS                             │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  Port      Protocol   Service                                               │
│  ────      ────────   ───────                                               │
│  67/UDP    DHCP       DHCP Server                                           │
│  68/UDP    DHCP       DHCP Client                                           │
│  53/UDP    DNS        Domain Name System                                    │
│  53/TCP    DNS        DNS over TCP (large responses)                        │
│  80/TCP    HTTP       Web (Captive Portal)                                  │
│  443/TCP   HTTPS      Secure Web                                            │
│  1812/UDP  RADIUS     Authentication                                        │
│  1813/UDP  RADIUS     Accounting                                            │
│  3799/UDP  RADIUS     CoA/DM (Dynamic Authorization)                        │
│  2083/TCP  RadSec     RADIUS over TLS                                       │
│  8080/TCP  HTTP       Alternate HTTP (Captive Portal)                       │
│  8443/TCP  HTTPS      Alternate HTTPS                                       │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### V.4 EtherType Reference

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    QUICK REFERENCE: ETHERTYPES                               │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  EtherType   Protocol                                                       │
│  ─────────   ────────                                                       │
│  0x0800      IPv4                                                           │
│  0x0806      ARP                                                            │
│  0x86DD      IPv6                                                           │
│  0x888E      EAPOL (802.1X)                                                 │
│  0x88C7      802.11 Pre-Authentication                                      │
│  0x890D      802.11 Fast Roaming Remote Request                             │
│  0x88B4      WAPI (Chinese WLAN security)                                   │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

