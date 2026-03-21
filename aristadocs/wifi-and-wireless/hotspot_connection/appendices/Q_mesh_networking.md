## Appendix Q: Mesh Networking (802.11s)

### Q.1 Mesh Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    802.11s MESH ARCHITECTURE                                 │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│                        ┌─────────────┐                                       │
│                        │   Gateway   │                                       │
│                        │    (MPP)    │                                       │
│                        └──────┬──────┘                                       │
│                               │ Ethernet                                     │
│                               │                                              │
│                        ┌──────┴──────┐                                       │
│                        │   Mesh AP   │                                       │
│                        │    (MAP)    │                                       │
│                        └──────┬──────┘                                       │
│                               │ Wireless Mesh                                │
│                    ┌──────────┼──────────┐                                   │
│                    │          │          │                                   │
│             ┌──────┴──────┐   │   ┌──────┴──────┐                            │
│             │   Mesh AP   │   │   │   Mesh AP   │                            │
│             │    (MAP)    │   │   │    (MAP)    │                            │
│             └──────┬──────┘   │   └──────┬──────┘                            │
│                    │          │          │                                   │
│                    │   ┌──────┴──────┐   │                                   │
│                    │   │   Mesh AP   │   │                                   │
│                    │   │    (MAP)    │   │                                   │
│                    │   └─────────────┘   │                                   │
│                    │                     │                                   │
│             ┌──────┴──────┐       ┌──────┴──────┐                            │
│             │   Client    │       │   Client    │                            │
│             └─────────────┘       └─────────────┘                            │
│                                                                              │
│  Terminology:                                                                │
│  • MP (Mesh Point): Any node in the mesh                                     │
│  • MAP (Mesh AP): Mesh point that also serves clients                        │
│  • MPP (Mesh Portal Point): Gateway to external network                      │
│  • MBSS (Mesh Basic Service Set): The mesh network                           │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Q.2 Mesh Peering

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    MESH PEERING ESTABLISHMENT                                │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  Mesh Point A                              Mesh Point B                      │
│       │                                          │                           │
│       │◄──────────── Beacon ────────────────────│                           │
│       │ (Mesh ID, Mesh Config, Mesh Peering)    │                           │
│       │                                          │                           │
│       │ Mesh Peering Open ──────────────────────►│                           │
│       │ (Mesh ID, Mesh Config, PMK-MA)          │                           │
│       │                                          │                           │
│       │◄────────────── Mesh Peering Open ────────│                           │
│       │ (Mesh ID, Mesh Config, PMK-MA)          │                           │
│       │                                          │                           │
│       │ Mesh Peering Confirm ───────────────────►│                           │
│       │ (Peer Link ID, MIC)                     │                           │
│       │                                          │                           │
│       │◄────────────── Mesh Peering Confirm ─────│                           │
│       │ (Peer Link ID, MIC)                     │                           │
│       │                                          │                           │
│       │═══════════════════════════════════════════│                           │
│       │         MESH PEERING ESTABLISHED         │                           │
│       │═══════════════════════════════════════════│                           │
│       │                                          │                           │
│                                                                              │
│  Security:                                                                   │
│  • SAE (Simultaneous Authentication of Equals) for mesh peering             │
│  • PMK-MA (Pairwise Master Key - Mesh Authenticator)                        │
│  • AMPE (Authenticated Mesh Peering Exchange)                               │
│                                                                              │
│  Configuration:                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │ # hostapd.conf for mesh                                             │    │
│  │ mode=mesh                                                           │    │
│  │ mesh_id=MyMesh                                                      │    │
│  │ mesh_hwmp_rootmode=4                                                │    │
│  │ mesh_gate_announcements=1                                           │    │
│  │ mesh_fwding=1                                                       │    │
│  │ wpa=2                                                               │    │
│  │ wpa_key_mgmt=SAE                                                    │    │
│  │ sae_password=meshpassword                                           │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Q.3 HWMP (Hybrid Wireless Mesh Protocol)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    HWMP PATH SELECTION                                       │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  HWMP combines reactive and proactive routing:                               │
│                                                                              │
│  Reactive Mode (On-Demand):                                                  │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  Source ──► PREQ (Path Request) ──► Broadcast to all peers          │    │
│  │                                                                      │    │
│  │  Destination receives PREQ                                           │    │
│  │                                                                      │    │
│  │  Destination ──► PREP (Path Reply) ──► Unicast back to source       │    │
│  │                                                                      │    │
│  │  Path established, data can flow                                     │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  Proactive Mode (Tree-Based):                                                │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  Root (MPP) ──► RANN (Root Announcement) ──► Broadcast              │    │
│  │                                                                      │    │
│  │  All MPs learn path to root                                          │    │
│  │                                                                      │    │
│  │  MPs ──► PREQ to root ──► Establish proactive path                  │    │
│  │                                                                      │    │
│  │  Traffic to external network uses proactive tree                     │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  Path Metric (Airtime Link Metric):                                          │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  Metric = (O + Bt/r) / (1 - ef)                                     │    │
│  │                                                                      │    │
│  │  Where:                                                              │    │
│  │  • O = Channel access overhead                                       │    │
│  │  • Bt = Test frame length (8192 bits)                               │    │
│  │  • r = Data rate in Mbps                                            │    │
│  │  • ef = Frame error rate                                            │    │
│  │                                                                      │    │
│  │  Lower metric = better path                                          │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

