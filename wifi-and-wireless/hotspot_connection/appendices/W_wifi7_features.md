## Appendix W: WiFi 7 (802.11be) Features

### W.1 Multi-Link Operation (MLO)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    MULTI-LINK OPERATION (MLO)                                │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  MLO Architecture:                                                           │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │                    ┌─────────────────────┐                          │    │
│  │                    │   Multi-Link Device │                          │    │
│  │                    │       (MLD)         │                          │    │
│  │                    └──────────┬──────────┘                          │    │
│  │                               │                                      │    │
│  │              ┌────────────────┼────────────────┐                    │    │
│  │              │                │                │                     │    │
│  │         ┌────┴────┐      ┌────┴────┐     ┌────┴────┐               │    │
│  │         │ Link 1  │      │ Link 2  │     │ Link 3  │               │    │
│  │         │ 2.4 GHz │      │  5 GHz  │     │  6 GHz  │               │    │
│  │         │ 20 MHz  │      │ 160 MHz │     │ 320 MHz │               │    │
│  │         └─────────┘      └─────────┘     └─────────┘               │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  MLO Benefits:                                                               │
│  • Aggregate throughput across multiple bands                                │
│  • Seamless link switching (no roaming needed)                               │
│  • Lower latency (use least congested link)                                  │
│  • Improved reliability (redundant paths)                                    │
│                                                                              │
│  MLO Modes:                                                                  │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │ 1. Simultaneous Transmit and Receive (STR)                          │    │
│  │    • Transmit on one link while receiving on another                │    │
│  │    • Requires sufficient isolation between radios                   │    │
│  │                                                                      │    │
│  │ 2. Non-Simultaneous Transmit and Receive (NSTR)                     │    │
│  │    • Only one link active at a time                                 │    │
│  │    • For devices with shared radio components                       │    │
│  │                                                                      │    │
│  │ 3. Enhanced Multi-Link Single Radio (eMLSR)                         │    │
│  │    • Listen on multiple links, transmit on one                      │    │
│  │    • Dynamic link selection                                         │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  MLO Association:                                                            │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  Client MLD                              AP MLD                      │    │
│  │       │                                    │                         │    │
│  │       │ ML Probe Request ─────────────────►│                         │    │
│  │       │ (Multi-Link Element)               │                         │    │
│  │       │                                    │                         │    │
│  │       │◄───────────────── ML Probe Response│                         │    │
│  │       │ (Multi-Link Element with all links)│                         │    │
│  │       │                                    │                         │    │
│  │       │ ML Association Request ───────────►│                         │    │
│  │       │ (Per-STA Profile for each link)   │                         │    │
│  │       │                                    │                         │    │
│  │       │◄─────────────── ML Association Resp│                         │    │
│  │       │ (Link setup for all requested)    │                         │    │
│  │       │                                    │                         │    │
│  │       │ 4-Way Handshake (on primary link) │                         │    │
│  │       │ ◄─────────────────────────────────►│                         │    │
│  │       │                                    │                         │    │
│  │       │═══════════════════════════════════│                         │    │
│  │       │    ALL LINKS ESTABLISHED          │                         │    │
│  │       │═══════════════════════════════════│                         │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### W.2 320 MHz Channels

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    320 MHz CHANNEL OPERATION                                 │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  6 GHz Band 320 MHz Channels:                                                │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  Channel   Center Freq   Frequency Range                            │    │
│  │  ───────   ───────────   ───────────────                            │    │
│  │    31      6105 MHz      5945 - 6265 MHz                            │    │
│  │    63      6265 MHz      6105 - 6425 MHz                            │    │
│  │    95      6425 MHz      6265 - 6585 MHz                            │    │
│  │   127      6585 MHz      6425 - 6745 MHz                            │    │
│  │   159      6745 MHz      6585 - 6905 MHz                            │    │
│  │   191      6905 MHz      6745 - 7065 MHz                            │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  Throughput Comparison:                                                      │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  Bandwidth   Subcarriers   Max PHY Rate (4096-QAM, 4SS)             │    │
│  │  ─────────   ───────────   ────────────────────────────             │    │
│  │   20 MHz        234        ~1.0 Gbps                                │    │
│  │   40 MHz        468        ~2.0 Gbps                                │    │
│  │   80 MHz        980        ~4.3 Gbps                                │    │
│  │  160 MHz       1960        ~8.6 Gbps                                │    │
│  │  320 MHz       3920        ~17.3 Gbps (theoretical)                 │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  Preamble Puncturing:                                                        │
│  • Allows use of 320 MHz even with interferers                               │
│  • Puncture (disable) 20/40/80 MHz portions                                  │
│  • Maintain high throughput despite interference                             │
│                                                                              │
│  Example: 320 MHz with 80 MHz punctured                                      │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │  ████████████████████████░░░░░░░░████████████████████████████████   │    │
│  │  ◄──── 80 MHz ────►◄──── 80 MHz ────►◄──── 80 MHz ────►◄── 80 ──►  │    │
│  │       Active           Punctured          Active          Active    │    │
│  │                                                                      │    │
│  │  Effective bandwidth: 240 MHz                                       │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### W.3 4096-QAM (4K-QAM)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    4096-QAM MODULATION                                       │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  QAM Evolution:                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  Standard    Max QAM    Bits/Symbol   Improvement                   │    │
│  │  ────────    ───────    ───────────   ───────────                   │    │
│  │  802.11n     64-QAM     6 bits        Baseline                      │    │
│  │  802.11ac    256-QAM    8 bits        +33%                          │    │
│  │  802.11ax    1024-QAM   10 bits       +25%                          │    │
│  │  802.11be    4096-QAM   12 bits       +20%                          │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  4096-QAM Constellation:                                                     │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  • 64 x 64 = 4096 constellation points                              │    │
│  │  • Each symbol carries 12 bits                                       │    │
│  │  • Requires very high SNR (~40 dB)                                  │    │
│  │  • Only usable at close range with good conditions                  │    │
│  │                                                                      │    │
│  │  SNR Requirements:                                                   │    │
│  │  ┌─────────────────────────────────────────────────────────────┐    │    │
│  │  │  MCS    Modulation    Coding    Required SNR                │    │    │
│  │  │  ───    ──────────    ──────    ────────────                │    │    │
│  │  │  12     4096-QAM      3/4       ~38 dB                      │    │    │
│  │  │  13     4096-QAM      5/6       ~40 dB                      │    │    │
│  │  └─────────────────────────────────────────────────────────────┘    │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

