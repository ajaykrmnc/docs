# Ethernet vs WiFi

## Overview

Both Ethernet and WiFi are technologies for Local Area Networks (LANs), but they differ fundamentally in their physical medium and protocols.

```
ETHERNET (Wired)                    WIFI (Wireless)

┌────────┐  Cable  ┌────────┐      ┌────────┐ )))  ┌────────┐
│ Device │─────────│ Switch │      │ Device │      │   AP   │
└────────┘         └────────┘      └────────┘      └────────┘
                                        Radio Waves
IEEE 802.3                          IEEE 802.11
```

## Quick Comparison

| Feature | Ethernet | WiFi |
|---------|----------|------|
| Medium | Copper/Fiber cables | Radio waves (2.4/5/6 GHz) |
| Standard | IEEE 802.3 | IEEE 802.11 (a/b/g/n/ac/ax) |
| Max Speed | 400 Gbps (802.3bs) | 9.6 Gbps (WiFi 6) |
| Typical Speed | 1-10 Gbps | 100-1000 Mbps |
| Latency | 0.1-0.3 ms | 1-10 ms |
| Reliability | Very high | Variable (interference) |
| Security | Physical access required | Encryption essential |
| Mobility | None (tethered) | Full mobility |
| Installation | Cabling required | Minimal infrastructure |

## Physical Layer Differences

### Ethernet Cabling

```
┌────────────────────────────────────────────────────────────────┐
│                     ETHERNET CABLE TYPES                       │
├──────────────┬──────────────┬──────────────┬───────────────────┤
│ Category     │ Max Speed    │ Max Distance │ Use Case          │
├──────────────┼──────────────┼──────────────┼───────────────────┤
│ Cat5e        │ 1 Gbps       │ 100m         │ Home/Small office │
│ Cat6         │ 10 Gbps      │ 55m          │ Enterprise        │
│ Cat6a        │ 10 Gbps      │ 100m         │ Data centers      │
│ Cat7         │ 10 Gbps      │ 100m         │ Shielded environ. │
│ Cat8         │ 25-40 Gbps   │ 30m          │ Data centers      │
├──────────────┼──────────────┼──────────────┼───────────────────┤
│ Fiber (MM)   │ 100 Gbps     │ 100-500m     │ Building backbone │
│ Fiber (SM)   │ 400 Gbps     │ 10+ km       │ Long distance     │
└──────────────┴──────────────┴──────────────┴───────────────────┘
```

### WiFi Frequencies

```
┌────────────────────────────────────────────────────────────────┐
│                      WIFI FREQUENCY BANDS                      │
├──────────────┬──────────────┬──────────────┬───────────────────┤
│ Band         │ Range        │ Speed        │ Characteristics   │
├──────────────┼──────────────┼──────────────┼───────────────────┤
│ 2.4 GHz      │ Longer       │ Slower       │ More interference │
│              │ (walls OK)   │ (up to 600Mb)│ Crowded spectrum  │
├──────────────┼──────────────┼──────────────┼───────────────────┤
│ 5 GHz        │ Shorter      │ Faster       │ Less interference │
│              │ (walls weak) │ (up to 3.5Gb)│ More channels     │
├──────────────┼──────────────┼──────────────┼───────────────────┤
│ 6 GHz        │ Shortest     │ Fastest      │ WiFi 6E/7 only    │
│ (WiFi 6E)    │              │ (up to 9.6Gb)│ Least congestion  │
└──────────────┴──────────────┴──────────────┴───────────────────┘
```

## Collision Handling: CSMA/CD vs CSMA/CA

This is a **fundamental protocol difference**:

### Ethernet: CSMA/CD (Collision Detection)
```
┌─────────────────────────────────────────────────────────────────┐
│  1. Listen: Is the wire busy?                                   │
│      │                                                          │
│      ▼ No                                                       │
│  2. Transmit data                                               │
│      │                                                          │
│      ▼                                                          │
│  3. Collision detected? ──Yes──► Stop, send jam signal          │
│      │                              │                           │
│      ▼ No                           ▼                           │
│  4. Success!                    Wait random backoff, retry      │
└─────────────────────────────────────────────────────────────────┘
```
- Collisions **detected** during transmission
- Works because signals travel fast in cables
- Modern switched Ethernet: collisions rare (full-duplex)

### WiFi: CSMA/CA (Collision Avoidance)
```
┌─────────────────────────────────────────────────────────────────┐
│  1. Listen: Is the channel busy?                                │
│      │                                                          │
│      ▼ No                                                       │
│  2. Wait random backoff (DIFS)                                  │
│      │                                                          │
│      ▼                                                          │
│  3. Send RTS (Request to Send) ─────────────────►  AP           │
│                                                     │           │
│  4. Receive CTS (Clear to Send) ◄───────────────────┘           │
│      │                                                          │
│      ▼                                                          │
│  5. Transmit data                                               │
│      │                                                          │
│      ▼                                                          │
│  6. Receive ACK ◄─────────────────────────────────  AP          │
│      │                                                          │
│      ▼                                                          │
│  7. Success! (No ACK = assume collision, retry)                 │
└─────────────────────────────────────────────────────────────────┘
```
- Collisions **avoided** proactively (can't detect mid-transmission)
- "Hidden node problem" requires RTS/CTS handshake
- ACK required for every frame (adds overhead)

## Frame Structure Comparison

### Ethernet Frame (802.3)
```
┌──────────┬──────────┬──────────┬──────┬─────────────┬─────┐
│ Preamble │ Dest MAC │ Src MAC  │ Type │   Payload   │ FCS │
│  8 bytes │ 6 bytes  │ 6 bytes  │  2   │ 46-1500 B   │  4  │
└──────────┴──────────┴──────────┴──────┴─────────────┴─────┘
Total: 64 - 1518 bytes (excluding preamble)
```

### WiFi Frame (802.11)
```
┌───────┬──────┬─────┬────────┬────────┬────────┬────────┬──────┬─────────┬─────┐
│Frame  │Dura- │Addr │ Addr 2 │ Addr 3 │  Seq   │ Addr 4 │ QoS  │ Payload │ FCS │
│Control│tion  │  1  │        │        │Control │(opt)   │(opt) │         │     │
│ 2 B   │ 2 B  │ 6 B │  6 B   │  6 B   │  2 B   │  6 B   │ 2 B  │ 0-2304  │ 4 B │
└───────┴──────┴─────┴────────┴────────┴────────┴────────┴──────┴─────────┴─────┘
```
- WiFi has **4 address fields** (source, destination, transmitter, receiver)
- Extra overhead for wireless management

## Security Comparison

| Aspect | Ethernet | WiFi |
|--------|----------|------|
| Physical Access | Required (plug in) | Not required (radio range) |
| Eavesdropping | Requires physical tap | Anyone in range can listen |
| Default Security | None needed | WPA3 essential |
| Attack Surface | Physical intrusion | Deauth, evil twin, cracking |

### WiFi Security Evolution
```
WEP (broken) → WPA (weak) → WPA2 (AES) → WPA3 (SAE)
   1999           2003         2004         2018
```

## Latency Breakdown

```
ETHERNET                          WIFI
┌─────────────────────┐           ┌─────────────────────────────┐
│ Propagation: ~0.05ms│           │ Propagation: ~0.05ms        │
│ Processing:  ~0.1ms │           │ Processing:  ~0.1ms         │
│ Queuing:     ~0.1ms │           │ Queuing:     ~0.5ms         │
├─────────────────────┤           │ Contention:  ~1-5ms         │
│ TOTAL:     ~0.2-0.3ms           │ Retransmits: variable       │
└─────────────────────┘           ├─────────────────────────────┤
                                  │ TOTAL:       ~2-10ms        │
                                  └─────────────────────────────┘
```

## Use Case Recommendations

| Scenario | Recommendation | Reason |
|----------|----------------|--------|
| Gaming (competitive) | Ethernet | Lowest latency, no jitter |
| Video conferencing | Either | WiFi 6 adequate for most |
| File server access | Ethernet | Consistent high throughput |
| Mobile devices | WiFi | No alternative |
| IoT sensors | WiFi/Ethernet | Depends on power/location |
| Data centers | Ethernet | Reliability, speed, density |
| Office desktops | Ethernet | Reliability, security |
| Laptops | WiFi | Mobility required |

## Hybrid Networks

Most networks use **both** technologies:

```
                         ┌─────────────────┐
                         │    Internet     │
                         └────────┬────────┘
                                  │
                         ┌────────▼────────┐
                         │     Router      │
                         └────────┬────────┘
                                  │ (Ethernet backbone)
              ┌───────────────────┼───────────────────┐
              │                   │                   │
        ┌─────▼─────┐       ┌─────▼─────┐       ┌─────▼─────┐
        │  Switch   │       │  Switch   │       │ WiFi AP   │
        └─────┬─────┘       └─────┬─────┘       └─────┬─────┘
              │                   │                   │
     ┌────────┼────────┐    ┌─────┴─────┐       )))  │  )))
     │        │        │    │           │            │
  ┌──▼──┐  ┌──▼──┐  ┌──▼──┐ ▼           ▼        ┌───▼───┐
  │ PC  │  │ PC  │  │Server│            NAS      │Laptops│
  └─────┘  └─────┘  └─────┘                      │Phones │
                                                 └───────┘
   Wired devices: Ethernet              Mobile: WiFi
```

## Summary

| Choose Ethernet When | Choose WiFi When |
|---------------------|------------------|
| Speed is critical | Mobility is required |
| Latency matters (gaming, trading) | Cabling impractical |
| Maximum reliability needed | Temporary setup |
| Security is paramount | Many mobile devices |
| Devices are stationary | Convenience over performance |

