## Appendix P: Band Steering and Load Balancing

### P.1 Band Steering

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    BAND STEERING MECHANISM                                   │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  Purpose: Move dual-band capable clients from 2.4 GHz to 5 GHz              │
│                                                                              │
│  Detection Methods:                                                          │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │ 1. Probe Request Analysis                                           │    │
│  │    • Client sends probe on both bands                               │    │
│  │    • AP detects client is dual-band capable                         │    │
│  │                                                                      │    │
│  │ 2. Association History                                               │    │
│  │    • Track which bands client has connected to before               │    │
│  │    • Use historical data for steering decisions                     │    │
│  │                                                                      │    │
│  │ 3. Capability Detection                                              │    │
│  │    • Check HT/VHT/HE capabilities in probe/assoc                    │    │
│  │    • Determine maximum supported band                               │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  Steering Techniques:                                                        │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │ 1. Probe Response Suppression                                        │    │
│  │    • Don't respond to 2.4 GHz probes from dual-band clients         │    │
│  │    • Client will connect to 5 GHz                                   │    │
│  │                                                                      │    │
│  │ 2. Authentication Rejection                                          │    │
│  │    • Reject auth on 2.4 GHz with status code                        │    │
│  │    • Client retries on 5 GHz                                        │    │
│  │                                                                      │    │
│  │ 3. BSS Transition Management (802.11v)                               │    │
│  │    • Send BTM Request to move client to 5 GHz BSS                   │    │
│  │    • More graceful, client-cooperative approach                     │    │
│  │                                                                      │    │
│  │ 4. Disassociation                                                    │    │
│  │    • Force disconnect from 2.4 GHz                                  │    │
│  │    • Client reconnects to 5 GHz                                     │    │
│  │    • Last resort, may cause brief disconnection                     │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  Steering Decision Factors:                                                  │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │ • Client RSSI on each band                                          │    │
│  │ • Channel utilization on each band                                  │    │
│  │ • Number of clients on each band                                    │    │
│  │ • Client capabilities (11n vs 11ac vs 11ax)                         │    │
│  │ • Application requirements (voice, video, data)                     │    │
│  │ • Historical connection success rate                                │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  Configuration Example:                                                      │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │ # Band steering configuration                                       │    │
│  │ band_steering_mode=prefer_5ghz                                      │    │
│  │ band_steering_rssi_threshold=-70                                    │    │
│  │ band_steering_probe_suppress_count=3                                │    │
│  │ band_steering_auth_reject_count=2                                   │    │
│  │ band_steering_btm_enabled=1                                         │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### P.2 Load Balancing

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    LOAD BALANCING MECHANISM                                  │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  Purpose: Distribute clients across multiple APs for optimal performance    │
│                                                                              │
│  Load Metrics:                                                               │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │ • Client count per AP                                               │    │
│  │ • Channel utilization percentage                                    │    │
│  │ • Airtime utilization                                               │    │
│  │ • Throughput per client                                             │    │
│  │ • Retry rate                                                        │    │
│  │ • RSSI distribution                                                 │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  Balancing Techniques:                                                       │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │ 1. Association Limiting                                              │    │
│  │    • Set maximum clients per AP                                     │    │
│  │    • Reject new associations when limit reached                     │    │
│  │                                                                      │    │
│  │ 2. Probe Response Delay                                              │    │
│  │    • Delay probe response on overloaded AP                          │    │
│  │    • Client connects to faster-responding AP                        │    │
│  │                                                                      │    │
│  │ 3. BSS Transition Management (802.11v)                               │    │
│  │    • Send BTM Request to move client to less loaded AP              │    │
│  │    • Include candidate AP list with load information                │    │
│  │                                                                      │    │
│  │ 4. Neighbor Report (802.11k)                                         │    │
│  │    • Provide client with neighbor AP information                    │    │
│  │    • Client can make informed roaming decisions                     │    │
│  │                                                                      │    │
│  │ 5. RSSI-Based Steering                                               │    │
│  │    • Steer clients to AP with better signal                         │    │
│  │    • Improves overall network efficiency                            │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  Load Balancing Flow:                                                        │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  Client ──► Probe Request ──► AP1 (overloaded)                      │    │
│  │                              │                                       │    │
│  │                              ▼                                       │    │
│  │                         Check Load                                   │    │
│  │                              │                                       │    │
│  │                    ┌─────────┴─────────┐                            │    │
│  │                    │                   │                             │    │
│  │               Load OK            Load High                           │    │
│  │                    │                   │                             │    │
│  │                    ▼                   ▼                             │    │
│  │            Send Probe Resp      Delay/Suppress                       │    │
│  │                                 Probe Response                       │    │
│  │                                       │                              │    │
│  │                                       ▼                              │    │
│  │                              Client connects                         │    │
│  │                              to AP2 instead                          │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

