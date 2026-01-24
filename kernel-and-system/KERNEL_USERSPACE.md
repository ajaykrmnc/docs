# Kernel Space vs User Space Architecture

This document describes the separation between kernel space and user space components in the Arista AP software stack, including their responsibilities and communication mechanisms.

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              USER SPACE                                      │
│                                                                              │
│  ┌────────────────────────────────────────────────────────────────────────┐ │
│  │                         GO AGENTS                                       │ │
│  │  ┌──────────┐ ┌─────────────┐ ┌──────────┐ ┌───────────┐ ┌──────────┐  │ │
│  │  │ ocagent  │ │ configagent │ │ rrmagent │ │cloudagent │ │  gobin   │  │ │
│  │  │ (gNMI)   │ │  (config)   │ │  (RRM)   │ │ (cloud)   │ │(triggers)│  │ │
│  │  └──────────┘ └─────────────┘ └──────────┘ └───────────┘ └──────────┘  │ │
│  └────────────────────────────────────────────────────────────────────────┘ │
│  ┌────────────────────────────────────────────────────────────────────────┐ │
│  │                          C DAEMONS                                      │ │
│  │  ┌──────────┐ ┌─────────────┐ ┌──────────┐ ┌───────────┐ ┌──────────┐  │ │
│  │  │ sensord  │ │  wl_evt_d   │ │ hostapd  │ │  portald  │ │synch_agt │  │ │
│  │  │          │ │             │ │ (802.1X) │ │ (captive) │ │          │  │ │
│  │  └──────────┘ └─────────────┘ └──────────┘ └───────────┘ └──────────┘  │ │
│  │  ┌──────────┐ ┌─────────────┐ ┌──────────┐ ┌───────────┐ ┌──────────┐  │ │
│  │  │ nl_agent │ │ app_vis_cli │ │   rrmd   │ │ wired_agt │ │  led     │  │ │
│  │  └──────────┘ └─────────────┘ └──────────┘ └───────────┘ └──────────┘  │ │
│  └────────────────────────────────────────────────────────────────────────┘ │
│  ┌────────────────────────────────────────────────────────────────────────┐ │
│  │                        USER-SPACE LIBRARIES                             │ │
│  │    libioctl    │   libpmac    │  libl2pioctl  │  radius_utils           │ │
│  └────────────────────────────────────────────────────────────────────────┘ │
├─────────────────────────────────────────────────────────────────────────────┤
│                    ↕ ioctl / netlink / procfs / sysfs ↕                     │
├─────────────────────────────────────────────────────────────────────────────┤
│                             KERNEL SPACE                                     │
│                                                                              │
│  ┌────────────────────────────────────────────────────────────────────────┐ │
│  │                      ARISTA KERNEL MODULES                              │ │
│  │  ┌───────────┐ ┌──────────┐ ┌───────────┐ ┌───────────┐ ┌───────────┐  │ │
│  │  │ arwlandrv │ │  gwmac   │ │  l2proxy  │ │   role    │ │  appfw    │  │ │
│  │  │ (ar_dp.c) │ │          │ │           │ │(iptables) │ │(iptables) │  │ │
│  │  └───────────┘ └──────────┘ └───────────┘ └───────────┘ └───────────┘  │ │
│  │  ┌───────────┐ ┌──────────┐ ┌───────────┐ ┌───────────┐ ┌───────────┐  │ │
│  │  │ firewall  │ │ content_ │ │  ipwcmask │ │  bcmcopt  │ │  tcpmss   │  │ │
│  │  │           │ │analytics │ │           │ │           │ │           │  │ │
│  │  └───────────┘ └──────────┘ └───────────┘ └───────────┘ └───────────┘  │ │
│  │  ┌───────────┐ ┌──────────┐ ┌───────────┐ ┌───────────┐ ┌───────────┐  │ │
│  │  │ar_pkt_trc │ │  bpipe   │ │  arutils  │ │upsk_isol  │ │arkerneltgl│  │ │
│  │  └───────────┘ └──────────┘ └───────────┘ └───────────┘ └───────────┘  │ │
│  └────────────────────────────────────────────────────────────────────────┘ │
│  ┌────────────────────────────────────────────────────────────────────────┐ │
│  │                       QCA KERNEL MODULES                                │ │
│  │  ┌───────────┐ ┌──────────┐ ┌───────────┐ ┌───────────┐ ┌───────────┐  │ │
│  │  │   qdf    │ │   asf    │ │   umac    │ │  qca_ol   │ │ wifi_3_0  │  │ │
│  │  └───────────┘ └──────────┘ └───────────┘ └───────────┘ └───────────┘  │ │
│  │  ┌───────────┐ ┌──────────┐ ┌───────────┐ ┌───────────┐                │ │
│  │  │ spectral  │ │ pktlog   │ │smart_ant  │ │mem_manager│                │ │
│  │  └───────────┘ └──────────┘ └───────────┘ └───────────┘                │ │
│  └────────────────────────────────────────────────────────────────────────┘ │
│  ┌────────────────────────────────────────────────────────────────────────┐ │
│  │                      LINUX KERNEL MODULES                               │ │
│  │   iptables  │  ebtables  │  nf_conntrack  │  bridge  │  veth  │ ...    │ │
│  └────────────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
                              ┌───────────────┐
                              │   HARDWARE    │
                              │  (WiFi Radio) │
                              └───────────────┘
```

## Kernel Space Components

### Arista Kernel Modules

| Module | Source Location | Purpose |
|--------|-----------------|---------|
| `arwlandrv.ko` | `ap/src/wlan-drivers/ar/` | Main WLAN driver (DP/CP), packet processing |
| `gwmac.ko` | `ap/src/gwmac/` | Gateway MAC learning, ARP/DHCP snooping |
| `l2proxy.ko` | `ap/src/l2proxy/` | L2 proxy for client isolation |
| `role.ko` | `ap/src/ipth/role/` | iptables role-based filtering |
| `firewall.ko` | `ap/src/ipth/firewall/` | Firewall rules enforcement |
| `appfw.ko` | `ap/src/ipth/appfw/` | Application firewall |
| `content_analytics.ko` | `ap/src/content_analytics/` | Deep packet inspection, app visibility |
| `ipwcmask.ko` | `ap/src/ipwcmask/` | IP wildcard masking |
| `bcmcopt.ko` | `ap/src/broadcast_multicast_opt/` | Broadcast/multicast optimization |
| `tcpmss.ko` | `ap/src/tcpmss/` | TCP MSS clamping |
| `bpipe.ko` | `ap/src/bpipe/` | Bridge pipe |
| `arutils.ko` | `ap/src/arutils/` | Kernel utility functions |
| `upsk_isolation.ko` | `ap/src/upsk_isolation/` | UPSK client isolation |
| `ar_pkt_trace.ko` | `ap/src/ar_pkt_trace/` | Packet tracing |
| `arkerneltoggle.ko` | `ap/src/arkerneltoggle/` | Runtime kernel feature toggles |

### QCA Vendor Kernel Modules

| Module | Purpose |
|--------|---------|
| `qdf.ko` | QCA Driver Framework - OS abstraction |
| `asf.ko` | Atheros Service Framework |
| `umac.ko` | Upper MAC - 802.11 state machines |
| `qca_ol.ko` | QCA Offload - firmware interface |
| `wifi_3_0.ko` | WiFi 3.0 (11ax) support |
| `qca_spectral.ko` | Spectral analysis |
| `ath_pktlog.ko` | Packet logging |
| `smart_antenna.ko` | Smart antenna control |
| `mem_manager.ko` | Memory management |

### Linux Kernel Modules

Standard Linux modules loaded for networking:
- `iptables` / `ip_tables.ko` - IPv4 firewall
- `ebtables` / `ebtables.ko` - Ethernet bridge filtering
- `nf_conntrack.ko` - Connection tracking
- `bridge.ko` - Ethernet bridging
- `veth.ko` - Virtual ethernet pairs
- `xt_*.ko` - Netfilter extensions

### Kernel Space Responsibilities

1. **Packet Processing (Data Path)**
   - TX/RX packet handling in `arwlandrv` (`ar_dp.c`)
   - QoS classification and marking
   - VLAN tagging/untagging
   - ACL filtering
   - Multicast enhancement

2. **Protocol Handling**
   - ARP inspection and proxy ARP
   - DHCP snooping
   - IPv6 processing
   - 802.1X frame handling (to hostapd)

3. **Filtering & Security**
   - Firewall rule enforcement
   - Role-based access control
   - Application visibility (DPI)
   - Client isolation

4. **Hardware Interface**
   - Driver ↔ firmware communication
   - Register access
   - DMA management
   - Interrupt handling

## User Space Components

### Go Agents

| Agent | Source Location | Purpose |
|-------|-----------------|---------|
| `ocagent` | `ap/src/go/arista-ap/ocagent/` | OpenConfig gNMI/gNOI server |
| `configagent` | `ap/src/go/arista-ap/configagent/` | Configuration application |
| `rrmagent` | `ap/src/go/arista-ap/rrmagent/` | Radio Resource Management |
| `cloudagent` | `ap/src/go/arista-ap/cloudagent/` | Cloud connectivity |
| `gobin` | `ap/src/go/arista-ap/gobin/` | Trigger/timer manager, health monitor |
| `arqwrap` | `ap/src/go/arista-ap/arqwrap/` | QWRAP helper |

### C Daemons

| Daemon | Source Location | Purpose |
|--------|-----------------|---------|
| `sensord` | `ap/src/sensord/` | Main sensor daemon, cloud comm |
| `wl_evt_handler` | `ap/src/wl_evt_handler/` | WLAN event processing |
| `hostapd` | `ap/src/hostapd-2.10/` | 802.1X, WPA, RADIUS |
| `portald` | `ap/src/portal/` | Captive portal |
| `synch_agent` | `ap/src/synch_agent/` | Inter-AP synchronization |
| `nl_agent` | `ap/src/nl_agent/` | Netlink event agent |
| `rrmd` | `ap/src/rrmd/` | RRM daemon (DFS) |
| `wired_agent` | `ap/src/wired_agent/` | Wired client handling |
| `led` | `ap/src/led/` | LED control daemon |
| `app_visibility_cli` | `ap/src/cli_appvisibility/` | App visibility CLI |

### User-Space Libraries

| Library | Source Location | Purpose |
|---------|-----------------|---------|
| `libioctl` | `ap/src/libioctl/` | ioctl wrapper for driver communication |
| `libpmac` | `ap/src/libpmac/` | PseudoMAC library |
| `libl2pioctl` | `ap/src/libl2pioctl/` | L2 proxy ioctl interface |
| `radius_utils` | `ap/src/radius_utils/` | RADIUS protocol utilities |

### User Space Responsibilities

1. **Management & Configuration**
   - gNMI/gNOI interface (ocagent)
   - Configuration parsing and application
   - ARDS state management
   - Cloud registration

2. **Protocol Processing**
   - 802.1X authentication (hostapd)
   - RADIUS client
   - Captive portal
   - WPA key management

3. **Monitoring & Events**
   - WLAN event handling
   - Health monitoring
   - Statistics collection
   - Logging

4. **Radio Management**
   - Channel selection (RRM)
   - DFS handling
   - TPC (Transmit Power Control)
   - Background scanning

## Communication Mechanisms

### ioctl Interface

Primary mechanism for user-space to kernel-space configuration:

```
┌─────────────────┐                    ┌─────────────────┐
│   User Space    │                    │  Kernel Space   │
│                 │                    │                 │
│  ┌───────────┐  │    ioctl()         │  ┌───────────┐  │
│  │ libioctl  │──┼───────────────────►│  │ arwlandrv │  │
│  │           │  │   SIOCDEVPRIVATE   │  │           │  │
│  └───────────┘  │                    │  └───────────┘  │
│                 │                    │                 │
│  ┌───────────┐  │    ioctl()         │  ┌───────────┐  │
│  │libl2pioctl│──┼───────────────────►│  │  l2proxy  │  │
│  └───────────┘  │                    │  └───────────┘  │
└─────────────────┘                    └─────────────────┘
```

**Key Files:**
- `ap/src/libioctl/wl_priv_ioctl.c` - WLAN ioctl wrapper
- `ap/src/go/arista-ap/wlanioctl/` - Go ioctl bindings
- `ap/src/libl2pioctl/l2p_ioctl.c` - L2 proxy ioctl

### Netlink Interface

Asynchronous kernel-to-user notifications:

```
┌─────────────────┐                    ┌─────────────────┐
│   User Space    │                    │  Kernel Space   │
│                 │    Netlink         │                 │
│  ┌───────────┐  │   AF_NETLINK       │  ┌───────────┐  │
│  │ nl_agent  │◄─┼───────────────────►│  │ arwlandrv │  │
│  └───────────┘  │                    │  └───────────┘  │
│                 │                    │                 │
│  ┌───────────┐  │   Generic NL       │  ┌───────────┐  │
│  │ Go agents │◄─┼───────────────────►│  │ QCA umac  │  │
│  │ (netlink) │  │                    │  │           │  │
│  └───────────┘  │                    │  └───────────┘  │
└─────────────────┘                    └─────────────────┘
```

**Key Files:**
- `ap/src/go/arista-ap/netlink/netlink.go` - Go netlink wrapper
- `ap/src/nl_agent/nl_agent.c` - C netlink agent

### procfs / sysfs Interface

Kernel state exposure and configuration:

```
/proc/
├── net/
│   ├── ar_dp/          # arwlandrv data path stats
│   └── ar_cp/          # arwlandrv control path info
├── driver/
│   └── content_analytics/  # CA statistics
└── sys/
    └── kernel/
        └── debug/      # debugfs interface

/sys/
├── class/net/          # Network interfaces
├── kernel/
│   └── gwmac/          # gwmac sysfs interface
└── devices/            # Device tree
```

**Key Files:**
- `ap/src/wlan-drivers/ar/core/src/ar_proc.c` - Driver procfs
- `ap/src/gwmac/src/gwmac_sysfs.c` - gwmac sysfs
- `ap/src/l2proxy/src/l2proxy_sysfs.c` - l2proxy sysfs

### Character Device Interface

Direct kernel communication for specialized modules:

```
/dev/
├── ca_chardev_ioctl    # Content analytics
├── role_cdev           # Role-based filtering
└── appfw_cdev          # Application firewall
```

**Key Files:**
- `ap/src/content_analytics/src/app_visibility/chardev_ioctl.c`
- `ap/src/ipth/role/src/role_cdev.c`
- `ap/src/ipth/appfw/src/appfw_cdev.c`

## Module Loading Order

Kernel modules are loaded at boot by `/etc/init.d/load_kernel_modules.sh`:

```
1. gwmac.ko              # Gateway MAC (before WLAN driver)
2. QCA modules           # QCA driver stack (qdf, asf, umac, etc.)
3. iptables modules      # Netfilter (ip_tables, iptable_filter, etc.)
4. content_analytics.ko  # App visibility
5. role.ko               # Role-based filtering
6. firewall.ko           # Firewall rules
7. appfw.ko              # App firewall
8. ar_pkt_trace.ko       # Packet tracing
9. l2proxy.ko            # L2 proxy
10. arwlandrv.ko         # Arista WLAN driver (last)
```

## Data Flow Example

### TX Path (User Space → Kernel → Hardware)

```
┌─────────────────────────────────────────────────────────────────────────┐
│ 1. Application sends packet                                              │
│    └──► Linux TCP/IP stack                                               │
│         └──► Bridge (br0)                                                │
│              └──► arwlandrv.ko (ar_dp_tx_handle)                        │
│                   ├──► QoS classification                                │
│                   ├──► VLAN processing                                   │
│                   ├──► ACL check                                         │
│                   └──► QCA driver (umac → qca_ol → firmware)            │
│                        └──► WiFi Hardware                                │
└─────────────────────────────────────────────────────────────────────────┘
```

### RX Path (Hardware → Kernel → User Space)

```
┌─────────────────────────────────────────────────────────────────────────┐
│ 1. WiFi Hardware receives frame                                          │
│    └──► QCA driver (firmware → qca_ol → umac)                           │
│         └──► arwlandrv.ko (ar_dp_rx_handle)                              │
│              ├──► gwmac.ko (gateway MAC learning)                        │
│              ├──► content_analytics.ko (DPI)                             │
│              ├──► ACL/firewall filtering                                 │
│              └──► Bridge (br0)                                           │
│                   └──► Linux TCP/IP stack                                │
│                        └──► Application                                  │
└─────────────────────────────────────────────────────────────────────────┘
```

### Event Flow (Kernel → User Space)

```
┌─────────────────────────────────────────────────────────────────────────┐
│ 1. WiFi event occurs (client assoc/disassoc, channel change, etc.)       │
│    └──► QCA driver generates netlink event                               │
│         └──► wl_evt_handler receives event                               │
│              ├──► ARDS update (state change)                             │
│              └──► Trigger file creation                                  │
│                   └──► gobin/configagent handles trigger                 │
│                        └──► Apply configuration (ioctl to driver)        │
└─────────────────────────────────────────────────────────────────────────┘
```

## Debugging Interfaces

### Kernel Space

| Interface | Location | Purpose |
|-----------|----------|---------|
| procfs | `/proc/net/ar_*/` | Driver statistics |
| sysfs | `/sys/kernel/*/` | Module parameters |
| debugfs | `/sys/kernel/debug/` | Debug information |
| dmesg | kernel ring buffer | Kernel log messages |
| printk | `pr_debug()`, `pr_info()` | Kernel logging |

### User Space

| Interface | Purpose |
|-----------|---------|
| glog | Go agent logging |
| syslog | System logging |
| ARDS | State inspection via `ardstest` |
| CLI | `cli` binary for diagnostics |

## Key Source Directories Summary

| Path | Space | Description |
|------|-------|-------------|
| `ap/src/wlan-drivers/ar/` | Kernel | Arista WLAN driver |
| `ap/src/wlan-drivers/QCA/` | Kernel | QCA vendor driver |
| `ap/src/gwmac/` | Kernel | Gateway MAC module |
| `ap/src/content_analytics/` | Kernel | Content analytics/DPI |
| `ap/src/ipth/` | Kernel | iptables extensions |
| `ap/src/l2proxy/` | Kernel | L2 proxy module |
| `ap/src/go/arista-ap/` | User | Go agents |
| `ap/src/sensord/` | User | Sensor daemon |
| `ap/src/hostapd-2.10/` | User | 802.1X supplicant |
| `ap/src/wl_evt_handler/` | User | Event handler |
| `ap/src/libioctl/` | User | ioctl library |
| `ap/src/common/` | User | Common utilities |

## Related Documentation

- [GO_CODEBASE.md](GO_CODEBASE.md) - Go agent architecture
- [DATAPATH_CONTROLPATH.md](DATAPATH_CONTROLPATH.md) - DP/CP architecture
- [QCA_ARISTA_INTEGRATION.md](QCA_ARISTA_INTEGRATION.md) - QCA driver integration

