## Appendix R: Power Save Mechanisms

### R.1 Legacy Power Save

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    LEGACY POWER SAVE (PS-POLL)                               │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  Client                                   AP                                 │
│     │                                      │                                 │
│     │ Association (Power Save bit = 1) ───►│                                 │
│     │                                      │                                 │
│     │ ═══════ CLIENT ENTERS SLEEP ═══════ │                                 │
│     │                                      │                                 │
│     │                                      │ ◄── Buffered frame arrives     │
│     │                                      │                                 │
│     │ ◄─────────────── Beacon ─────────────│                                 │
│     │ (TIM: AID bit set = data waiting)   │                                 │
│     │                                      │                                 │
│     │ ═══════ CLIENT WAKES UP ═══════════ │                                 │
│     │                                      │                                 │
│     │ PS-Poll ────────────────────────────►│                                 │
│     │                                      │                                 │
│     │ ◄─────────────── Data ───────────────│                                 │
│     │ (More Data bit = 0)                 │                                 │
│     │                                      │                                 │
│     │ ACK ────────────────────────────────►│                                 │
│     │                                      │                                 │
│     │ ═══════ CLIENT RETURNS TO SLEEP ════ │                                 │
│     │                                      │                                 │
│                                                                              │
│  TIM (Traffic Indication Map):                                               │
│  • Bitmap in beacon indicating which AIDs have buffered data                 │
│  • Client checks its AID bit each beacon                                     │
│  • DTIM (Delivery TIM) for broadcast/multicast                               │
│                                                                              │
│  Limitations:                                                                │
│  • Client must wake for every beacon (100ms default)                         │
│  • PS-Poll retrieves one frame at a time                                     │
│  • High latency for bursty traffic                                           │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### R.2 U-APSD (Unscheduled Automatic Power Save Delivery)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    U-APSD (WMM POWER SAVE)                                   │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  Client                                   AP                                 │
│     │                                      │                                 │
│     │ Association (U-APSD enabled) ───────►│                                 │
│     │ (AC_VO, AC_VI trigger/delivery)     │                                 │
│     │                                      │                                 │
│     │ ═══════ CLIENT IN POWER SAVE ═══════ │                                 │
│     │                                      │                                 │
│     │                                      │ ◄── Voice frame buffered       │
│     │                                      │                                 │
│     │ Trigger Frame (QoS Null, AC_VO) ────►│                                 │
│     │                                      │                                 │
│     │ ◄─────────────── Data ───────────────│                                 │
│     │ (EOSP = 0, more data)               │                                 │
│     │                                      │                                 │
│     │ ◄─────────────── Data ───────────────│                                 │
│     │ (EOSP = 1, end of service period)   │                                 │
│     │                                      │                                 │
│     │ ═══════ CLIENT RETURNS TO SLEEP ════ │                                 │
│     │                                      │                                 │
│                                                                              │
│  Access Categories:                                                          │
│  • AC_VO (Voice): Trigger-enabled, Delivery-enabled                         │
│  • AC_VI (Video): Trigger-enabled, Delivery-enabled                         │
│  • AC_BE (Best Effort): Legacy power save                                   │
│  • AC_BK (Background): Legacy power save                                    │
│                                                                              │
│  Advantages:                                                                 │
│  • Client controls when to receive data                                      │
│  • Multiple frames delivered per trigger                                     │
│  • Lower latency for voice/video                                            │
│  • More efficient than PS-Poll                                               │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### R.3 TWT (Target Wake Time) - WiFi 6

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    TWT (TARGET WAKE TIME)                                    │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  TWT Negotiation:                                                            │
│  Client                                   AP                                 │
│     │                                      │                                 │
│     │ TWT Setup Request ──────────────────►│                                 │
│     │ (Wake Interval: 1000ms,              │                                 │
│     │  Wake Duration: 5ms,                 │                                 │
│     │  Trigger: Yes)                       │                                 │
│     │                                      │                                 │
│     │ ◄────────────── TWT Setup Response ──│                                 │
│     │ (Accepted, TWT = 12345678)          │                                 │
│     │                                      │                                 │
│                                                                              │
│  TWT Operation:                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  Time ──────────────────────────────────────────────────────────►   │    │
│  │                                                                      │    │
│  │  Client: ████░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░████    │    │
│  │          Wake                                                 Wake   │    │
│  │          5ms                                                  5ms    │    │
│  │          ◄────────────── 1000ms ──────────────►                     │    │
│  │                                                                      │    │
│  │  ████ = Awake (can transmit/receive)                                │    │
│  │  ░░░░ = Asleep (power save)                                         │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  TWT Types:                                                                  │
│  • Individual TWT: Negotiated per client                                     │
│  • Broadcast TWT: AP announces common wake times                             │
│  • Trigger-enabled TWT: AP sends trigger at TWT                              │
│  • Non-trigger TWT: Client initiates transmission                            │
│                                                                              │
│  Benefits:                                                                   │
│  • Predictable wake times (no beacon monitoring needed)                      │
│  • Longer sleep periods possible                                             │
│  • Reduced contention (scheduled access)                                     │
│  • Significant battery savings for IoT devices                               │
│                                                                              │
│  Configuration:                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │ # hostapd.conf                                                      │    │
│  │ ieee80211ax=1                                                       │    │
│  │ twt_responder=1                                                     │    │
│  │                                                                      │    │
│  │ # wpa_supplicant.conf                                               │    │
│  │ twt=1                                                               │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

