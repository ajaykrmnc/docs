## Phase 8: Connected State

After all authentication phases complete, the client is fully connected.

### 8.1 Data Frame Flow

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           DATA FRAME FLOW                                    │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  Client                        AP                        Internet           │
│    │                           │                              │             │
│    │  802.11 Data Frame        │                              │             │
│    │  ┌────────────────────────┤                              │             │
│    │  │ Frame Control          │                              │             │
│    │  │ Duration               │                              │             │
│    │  │ Address 1: BSSID (AP)  │                              │             │
│    │  │ Address 2: SA (Client) │                              │             │
│    │  │ Address 3: DA (Dest)   │                              │             │
│    │  │ Sequence Control       │                              │             │
│    │  │ QoS Control (if WMM)   │                              │             │
│    │  │ CCMP Header (8 bytes)  │                              │             │
│    │  │ Encrypted Payload      │                              │             │
│    │  │ MIC (8 bytes)          │                              │             │
│    │  │ FCS                    │                              │             │
│    │  └────────────────────────┤                              │             │
│    │ ─────────────────────────►│                              │             │
│    │                           │                              │             │
│    │                           │  ┌────────────────────────────┤             │
│    │                           │  │ Decrypt with TK            │             │
│    │                           │  │ Verify MIC                 │             │
│    │                           │  │ Convert to Ethernet frame  │             │
│    │                           │  │ Apply QoS/VLAN tagging     │             │
│    │                           │  │ Forward to network         │             │
│    │                           │  └────────────────────────────┤             │
│    │                           │                              │             │
│    │                           │  Ethernet Frame              │             │
│    │                           │ ─────────────────────────────►│             │
│    │                           │                              │             │
│    │                           │  Ethernet Frame (Response)   │             │
│    │                           │ ◄─────────────────────────────│             │
│    │                           │                              │             │
│    │                           │  ┌────────────────────────────┤             │
│    │                           │  │ Convert to 802.11 frame   │             │
│    │                           │  │ Encrypt with TK            │             │
│    │                           │  │ Add CCMP header and MIC    │             │
│    │                           │  └────────────────────────────┤             │
│    │                           │                              │             │
│    │  802.11 Data Frame        │                              │             │
│    │ ◄─────────────────────────│                              │             │
│    │                           │                              │             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 8.2 QoS (Quality of Service) - WMM

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    WMM (WiFi Multimedia) ACCESS CATEGORIES                   │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  Priority   AC        Description           Example Traffic                 │
│  ────────   ──        ───────────           ───────────────                 │
│  Highest    AC_VO     Voice                 VoIP, video calls               │
│             AC_VI     Video                 Streaming video, IPTV           │
│             AC_BE     Best Effort           Web browsing, email             │
│  Lowest     AC_BK     Background            File downloads, backups         │
│                                                                              │
│  EDCA Parameters (per AC):                                                  │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │ AC    CWmin   CWmax   AIFSN   TXOP Limit                            │    │
│  │ ──    ─────   ─────   ─────   ──────────                            │    │
│  │ VO    3       7       2       1.504 ms                              │    │
│  │ VI    7       15      2       3.008 ms                              │    │
│  │ BE    15      1023    3       0                                     │    │
│  │ BK    15      1023    7       0                                     │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 8.3 Power Save Modes

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         POWER SAVE MODES                                     │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  Legacy Power Save (PS-Poll):                                               │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │ 1. Client enters sleep mode                                         │    │
│  │ 2. AP buffers frames for sleeping client                            │    │
│  │ 3. AP sets TIM bit in beacon                                        │    │
│  │ 4. Client wakes up, receives beacon                                 │    │
│  │ 5. Client sends PS-Poll to retrieve buffered frames                 │    │
│  │ 6. AP sends buffered frames                                         │    │
│  │ 7. Client returns to sleep                                          │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  U-APSD (Unscheduled Automatic Power Save Delivery):                        │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │ 1. Client sends trigger frame (QoS Data or QoS Null)                │    │
│  │ 2. AP sends all buffered frames in a burst                          │    │
│  │ 3. More efficient for VoIP and real-time applications               │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  TWT (Target Wake Time) - WiFi 6:                                           │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │ 1. Client negotiates wake schedule with AP                          │    │
│  │ 2. Client sleeps for extended periods                               │    │
│  │ 3. Wakes at predetermined times                                     │    │
│  │ 4. Significantly improves battery life for IoT devices              │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 8.4 Client Statistics and Monitoring

```c
// sta_info.c - Client statistics
struct sta_info {
    // Connection info
    struct os_reltime connected_time;
    int last_rssi;
    int last_snr;

    // Traffic statistics
    unsigned long rx_packets;
    unsigned long tx_packets;
    unsigned long rx_bytes;
    unsigned long tx_bytes;
    unsigned long rx_errors;
    unsigned long tx_errors;
    unsigned long tx_retry_count;
    unsigned long tx_retry_failed;

    // Rate info
    u16 last_rx_rate;
    u16 last_tx_rate;
    u8 last_rx_mcs;
    u8 last_tx_mcs;

    // Capabilities
    u8 ht_supported;
    u8 vht_supported;
    u8 he_supported;
    u8 eht_supported;
};
```

---

