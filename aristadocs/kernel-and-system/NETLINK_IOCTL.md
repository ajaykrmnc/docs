# Netlink and ioctl Communication Architecture

This document describes the Netlink and ioctl interfaces used for communication between user space and kernel space in the Arista AP software stack.

## Overview

The AP software uses two primary IPC mechanisms for kernel-userspace communication:

| Mechanism | Direction | Use Case | Latency |
|-----------|-----------|----------|---------|
| **ioctl** | User → Kernel | Configuration, commands, synchronous queries | Low (sync) |
| **Netlink** | Kernel → User | Events, async notifications, bulk data | Variable (async) |

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              USER SPACE                                      │
│                                                                              │
│  ┌──────────────────────────────────────────────────────────────────────┐   │
│  │                         GO AGENTS                                     │   │
│  │  ┌─────────────────────────────────────────────────────────────────┐ │   │
│  │  │ wlanioctl package         │ netlink package                     │ │   │
│  │  │ ap/src/go/arista-ap/      │ ap/src/go/arista-ap/netlink/        │ │   │
│  │  │   wlanioctl/              │   messenger.go                      │ │   │
│  │  │   wlan_ioctl.go           │   generic_netlink.go                │ │   │
│  │  └─────────────────────────────────────────────────────────────────┘ │   │
│  └──────────────────────────────────────────────────────────────────────┘   │
│  ┌──────────────────────────────────────────────────────────────────────┐   │
│  │                         C DAEMONS                                     │   │
│  │  ┌─────────────────────┐     ┌─────────────────────────────────────┐ │   │
│  │  │ libioctl            │     │ nl_agent                            │ │   │
│  │  │ wl_priv_ioctl.c     │     │ nl_agent.c, nl_handlers.c           │ │   │
│  │  │ cfg80211_nlwrapper  │     │ nl_msg.c, nl_producer.c             │ │   │
│  │  └─────────────────────┘     └─────────────────────────────────────┘ │   │
│  │  ┌─────────────────────┐     ┌─────────────────────────────────────┐ │   │
│  │  │ hostapd             │     │ wl_evt_handler                      │ │   │
│  │  │ driver_nl80211.c    │     │ (event processing)                  │ │   │
│  │  └─────────────────────┘     └─────────────────────────────────────┘ │   │
│  └──────────────────────────────────────────────────────────────────────┘   │
├─────────────────────────────────────────────────────────────────────────────┤
│                     ↕ ioctl (sync)      ↕ Netlink (async)                   │
├─────────────────────────────────────────────────────────────────────────────┤
│                             KERNEL SPACE                                     │
│  ┌──────────────────────────────────────────────────────────────────────┐   │
│  │                    ARISTA WLAN DRIVER (arwlandrv.ko)                  │   │
│  │  ┌─────────────────────────────────────────────────────────────────┐ │   │
│  │  │ ar_cfg.c (ioctl handler)  │ ar_evt.c (event dispatcher)        │ │   │
│  │  │ ar_cp.c (control path)    │ wireless_send_event()              │ │   │
│  │  │ priv_ioctl_cmds.h         │                                     │ │   │
│  │  └─────────────────────────────────────────────────────────────────┘ │   │
│  │  ┌─────────────────────────────────────────────────────────────────┐ │   │
│  │  │ vdrv_cp_if.c (vendor driver interface)                          │ │   │
│  │  │ cfg80211 / nl80211 handler callbacks                            │ │   │
│  │  └─────────────────────────────────────────────────────────────────┘ │   │
│  └──────────────────────────────────────────────────────────────────────┘   │
│  ┌──────────────────────────────────────────────────────────────────────┐   │
│  │                      QCA DRIVER (umac, qca_ol)                        │   │
│  │  ┌─────────────────────────────────────────────────────────────────┐ │   │
│  │  │ ioctl_vendor_generic.c    │ wlan_nlink_srv.c                    │ │   │
│  │  │ ieee80211_ioctl.h         │ ath_netlink.c                       │ │   │
│  │  │ cfg80211_ven_cmd.h        │                                     │ │   │
│  │  └─────────────────────────────────────────────────────────────────┘ │   │
│  └──────────────────────────────────────────────────────────────────────┘   │
│  ┌──────────────────────────────────────────────────────────────────────┐   │
│  │                    OTHER KERNEL MODULES                               │   │
│  │  content_analytics.ko        role.ko             appfw.ko             │   │
│  │  (chardev_ioctl.c)           (role_cdev.c)       (appfw_cdev.c)       │   │
│  └──────────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────────┘
```

## ioctl Interface

### Overview

ioctl (input/output control) is the primary mechanism for **synchronous** configuration commands from user space to kernel space. It uses socket file descriptors and the `SIOCDEVPRIVATE` family of commands.

### ioctl Types

| Type | Base Constant | Range | Purpose |
|------|---------------|-------|---------|
| **Wireless Extensions** | `SIOCIWFIRSTPRIV` | +0 to +31 | Standard wireless private ioctls |
| **Device Private** | `SIOCDEVPRIVATE` | +0 to +15 | Device-specific ioctls |
| **Vendor Commands** | `SIOCDEVPRIVATE+15` | N/A | QCA vendor-specific commands |

### Arista Private ioctl Commands

Defined in `ap/src/priv_ioctl/priv_ioctl_cmds.h`:

```c
enum PRIV_IOCTLS {
  SET_ACS_CHANS,       // Set ACS channels
  SET_SS_PARAMS,       // Smart steering parameters
  SET_ACS_PARAMS,      // ACS parameters
  GET_ACS_PARAMS,      // Get ACS parameters
  SET_ASSOC_PARAMS,    // Association parameters
  GET_DOT11_STATS,     // 802.11 statistics
  SET_NBR_TBL,         // Neighbor table
  SET_MAC_ACL,         // MAC ACL
  SET_RF_PARAMS,       // RF parameters
  SET_AUTO_TPC,        // Auto TPC
  PACKET_CAPTURE,      // Packet capture control
  GET_PEER_INFO,       // Peer information
  // ... many more
};
```

### User Space ioctl Libraries

#### Go: wlanioctl Package (`ap/src/go/arista-ap/wlanioctl/`)

```go
// wlan_ioctl.go - Primary Go interface for iwpriv-style ioctls

const (
    siocgIWPrivs   = 0x8B0D  // Get private ioctl list
    siocDevPrivate = 0x89F0  // Device private ioctl base
)

// Execute ioctl via socket
func ioctl(fd, op, arg uintptr) error {
    _, _, err := syscall.Syscall(syscall.SYS_IOCTL, fd, op, arg)
    if err != 0 {
        return err
    }
    return nil
}
```

#### C: libioctl (`ap/src/libioctl/`)

```c
// wl_priv_ioctl.c - C wrapper for wireless ioctls

int wl_priv_ioctl(const char* cmd, intptr_t arg0, void* arg1,
                  const char* ifname, int8_t set)
{
    struct cfg80211_data arg;
    int cmd_id = ar_get_cmdid(cmd);
    
    // Fill cfg80211 command data
    prepare_cfg80211_command_data(cmd_id, arg0, arg1, set, &ar_data);
    arg.data = &ar_data;
    arg.length = sizeof(ar_data);
    
    // Execute via cfg80211
    return cfg80211_send_command(...);
}
```

### Kernel ioctl Handlers

#### Arista Driver (`ar_cfg.c`)

The Arista driver registers ioctl handlers through the vendor driver interface:

```c
// ar_cp_if.h - Main ioctl interface
int ar_cp_if_vdev_config(vdrv_if_vdev_t vdev, int arg, int value, char* extra);
```

#### QCA Driver (`ioctl_vendor_generic.c`)

```c
// Vendor-specific ioctl handler
static int ath_ioctl_vendor_generic(struct net_device *dev, ioctl_ifreq_req_t *iiReq)
{
    athcfg_wcmd_t *iiCmd = IFREQ_TO_VENDOR_CMD(iiReq);

    if (iiCmd->iic_vendor != ATHCFG_WCMD_VENDORID)
        return -EOPNOTSUPP;

    if (cmd & IOCTL_SET_MASK) {
        retv = ath_vendor_ioctl_setparam(dev, iiCmd);
    } else {
        retv = ath_vendor_ioctl_getparam(dev, iiCmd);
    }
    return retv;
}
```

#### IEEE 802.11 ioctl Definitions (`ieee80211_ioctl.h`)

```c
#define IEEE80211_IOCTL_SETPARAM      (SIOCIWFIRSTPRIV+0)
#define IEEE80211_IOCTL_GETPARAM      (SIOCIWFIRSTPRIV+1)
#define IEEE80211_IOCTL_SETKEY        (SIOCIWFIRSTPRIV+2)
#define IEEE80211_IOCTL_SETWMMPARAMS  (SIOCIWFIRSTPRIV+3)
#define IEEE80211_IOCTL_SETMLME       (SIOCIWFIRSTPRIV+6)
#define IEEE80211_IOCTL_GETCHANINFO   (SIOCIWFIRSTPRIV+7)
#define IEEE80211_IOCTL_DBGREQ        (SIOCIWFIRSTPRIV+24)
// ... up to +31

// Device private ioctls
#define IEEE80211_IOCTL_CONFIG_GENERIC  (SIOCDEVPRIVATE+12)
#define SIOCDEVVENDOR                   (SIOCDEVPRIVATE+15)
```

### Character Device ioctl Interfaces

For non-network modules, character devices provide ioctl interfaces:

| Module | Device | Source | Commands |
|--------|--------|--------|----------|
| Content Analytics | `/dev/ca_chardev_ioctl` | `chardev_ioctl.c` | `IOCTL_CLIENT_APP_QOE_*` |
| Role Filtering | `/dev/role_cdev` | `role_cdev.c` | `IOCTL_CLIENT_ROLE_EVENT` |
| App Firewall | `/dev/appfw_cdev` | `appfw_cdev.c` | `IOCTL_XWF_EVENT` |

## Netlink Interface

### Overview

Netlink is the primary mechanism for **asynchronous** event delivery from kernel to user space. It supports multicast groups for efficient event distribution to multiple listeners.

### Netlink Families

| Family | Protocol | Purpose |
|--------|----------|---------|
| `NETLINK_ROUTE` | `AF_NETLINK` | Network interface events (link up/down) |
| `NETLINK_GENERIC` | `GENL_ID_*` | Generic netlink for driver events |
| `NETLINK_ATH_EVENT` | Custom | QCA Atheros-specific events |
| `WLAN_NLINK_PROTO_FAMILY` | Custom | QCA WLAN netlink events |

### Netlink Event Flow

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        KERNEL EVENT SOURCES                              │
│                                                                          │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐ │
│  │ Client Assoc │  │ Client Dis-  │  │ Channel      │  │ DFS Radar   │ │
│  │              │  │ association  │  │ Change       │  │ Detection   │ │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘ │
│         │                 │                 │                 │         │
│         └────────────────┬┴─────────────────┴─────────────────┘         │
│                          ▼                                               │
│                  ┌───────────────┐                                       │
│                  │ ar_evt.c      │  ar_evt_vdev_deliver_event()          │
│                  │ ar_evt_net_   │  wireless_send_event()                │
│                  │ deliver_event │                                       │
│                  └───────┬───────┘                                       │
│                          ▼                                               │
│                  ┌───────────────┐                                       │
│                  │ QCA Netlink   │  nl_srv_bcast() / netlink_unicast()   │
│                  │ wlan_nlink_   │                                       │
│                  │ srv.c         │                                       │
│                  └───────┬───────┘                                       │
├──────────────────────────┼──────────────────────────────────────────────┤
│                          │ AF_NETLINK socket                             │
├──────────────────────────┼──────────────────────────────────────────────┤
│                          ▼                  USER SPACE                   │
│                  ┌───────────────┐                                       │
│                  │ nl_agent      │  handle_nl_events()                   │
│                  │ nl_agent.c    │  NETLINK_ROUTE (RTMGRP_LINK)          │
│                  └───────┬───────┘                                       │
│                          ▼                                               │
│                  ┌───────────────┐                                       │
│                  │ wl_evt_handler│  Event parsing & ARDS updates         │
│                  └───────┬───────┘                                       │
│                          ▼                                               │
│                  ┌───────────────┐                                       │
│                  │ ARDS State    │  WldrvState updates                   │
│                  │ Store         │  Trigger file creation                │
│                  └───────┬───────┘                                       │
│                          ▼                                               │
│                  ┌───────────────┐                                       │
│                  │ Go Agents     │  configagent, gobin respond           │
│                  │               │  to triggers                          │
│                  └───────────────┘                                       │
└─────────────────────────────────────────────────────────────────────────┘
```

### User Space Netlink Implementation

#### Go: netlink Package (`ap/src/go/arista-ap/netlink/`)

```go
// messenger.go - Netlink socket management

func init() {
    SetEndianess()
    if err := createSocket(); err != nil {
        glog.Errorf("NETLINK_GENERIC socket creation failed: %v", err)
    }
    msgSendMutex = &sync.RWMutex{}
}

// ResolveFamilyName returns familyID of a given familyName
func ResolveFamilyName(familyName string) (uint16, error) {
    // Create CTRL_CMD_GETFAMILY message
    reqGennl, _ := createGenlmsgWithAttribute(
        unix.CTRL_ATTR_FAMILY_NAME,
        Bytes(familyName),
        unix.CTRL_CMD_GETFAMILY)

    // Send and receive
    nlmsgBytes, _ := reqGennl.generateNlBytesFrmGenlmsg(
        unix.GENL_ID_CTRL, uint16(Request))
    rcvdBytes, _ := sendNetlinkMsg(nlmsgBytes, &rbuf)

    // Parse response
    return parseFamilyID(rbuf[:rcvdBytes])
}
```

```go
// generic_netlink.go - Generic netlink message handling

type GenlMessage struct {
    Header unix.Genlmsghdr
    Data   []byte
}

// CreateNlMsgwithGenlMsg packs a generic netlink Message
func (msg *GenlMessage) CreateNlMsgwithGenlMsg(family uint16,
    headerFlags uint16) (NetlinkMessage, error) {
    nm := NetlinkMessage{
        Header: syscall.NlMsghdr{
            Type:  family,
            Flags: headerFlags,
        },
    }
    nm.Data, _ = msg.toByte()
    return nm, nil
}
```

#### C: nl_agent (`ap/src/nl_agent/`)

```c
// nl_agent.c - Netlink event listener

static void init_netlink_socket(MarcoCTimerId id, void* userArg) {
    // Create NETLINK_ROUTE socket for link events
    int sock = socket(PF_NETLINK, SOCK_RAW, NETLINK_ROUTE);

    // Bind to RTMGRP_LINK multicast group
    struct sockaddr_nl local = {
        .nl_family = AF_NETLINK,
        .nl_groups = RTMGRP_LINK
    };
    bind(sock, (struct sockaddr*)&local, sizeof(local));

    // Add to event loop
    MarcoCAddFdCallback(sock, MarcoCReadableEvent, handle_nl_events, NULL);
}
```

### Kernel Netlink Implementation

#### QCA Netlink Service (`wlan_nlink_srv.c`)

```c
// Initialize the netlink service
int nl_srv_init(void *wiphy, int proto) {
    struct netlink_kernel_cfg cfg = {
        .groups = WLAN_NLINK_MCAST_GRP_ID,
        .input = nl_srv_rcv   // Message receive callback
    };

    nl_srv_sock = netlink_kernel_create(&init_net, proto, &cfg);
    return nl_srv_sock ? 0 : -ECONNREFUSED;
}

// Broadcast message to all listeners
int nl_srv_bcast(struct sk_buff *skb) {
    return netlink_broadcast(nl_srv_sock, skb, 0,
                            WLAN_NLINK_MCAST_GRP_ID, GFP_KERNEL);
}
```

#### Arista Event Dispatcher (`ar_evt.c`)

```c
// Deliver event to user space via wireless extensions
void ar_evt_vdev_deliver_event(struct ar_vdev_s* vdev, atn_iw_cmd_t cmd,
                               char* data, unsigned int size, bool is_ml_peer) {
    struct net_device* netdev = vdrv_cp_if_vdev_get_netdev(vdev->vdrv_vdev);
    ar_evt_net_deliver_event(netdev, cmd, data, size);
}

static void ar_evt_net_deliver_event(struct net_device* netdev,
                                     atn_iw_cmd_t cmd, char* data, uint size) {
    union iwreq_data wreq = {0};
    // ... prepare event data
    ar_os_send_wireless_event(netdev, &wreq, (void*)&buf[0]);
}
```

## cfg80211 / nl80211 Interface

Modern Linux wireless subsystem uses cfg80211/nl80211 for configuration:

### hostapd nl80211 Driver (`driver_nl80211.c`)

```c
// Send command via nl80211
void * nl80211_cmd(struct wpa_driver_nl80211_data *drv,
                   struct nl_msg *msg, int flags, uint8_t cmd) {
    return genlmsg_put(msg, 0, 0, drv->global->nl80211_id,
                       0, flags, cmd, 0);
}

// Send/receive nl80211 message
int wpa_driver_nl80211_mlme(struct wpa_driver_nl80211_data* drv,
                            const u8* addr, int cmd, u16 reason_code) {
    struct nl_msg* msg = nl80211_drv_msg(drv, 0, cmd);
    nla_put_u16(msg, NL80211_ATTR_REASON_CODE, reason_code);
    nla_put(msg, NL80211_ATTR_MAC, ETH_ALEN, addr);
    return send_and_recv_msgs(drv, msg, NULL, NULL, NULL, NULL);
}
```

### cfg80211 Wrapper (`cfg80211_nlwrapper_api.c`)

```c
// Initialize nl80211 socket
int wifi_init_nl80211_largebuf(wifi_cfg80211_context *ctx, uint8_t largebuf) {
    // Command socket for configuration
    ctx->cmd_sock = wifi_create_nl_socket(NCT_CMD_SOCK_PORT, NETLINK_GENERIC);

    // Event socket for async notifications
    ctx->event_sock = wifi_create_nl_socket(NCT_EVENT_SOCK_PORT, NETLINK_GENERIC);

    // Resolve nl80211 family
    ctx->nl80211_family_id = genl_ctrl_resolve(ctx->cmd_sock, "nl80211");
}
```

## Common Event Types

| Event | Source | Handler | Description |
|-------|--------|---------|-------------|
| `ATN_NEWSTA` | Client association | wl_evt_handler | New client connected |
| `ATN_DELSTA` | Client disassoc | wl_evt_handler | Client disconnected |
| `ATN_CHANNELCHANGE` | Channel switch | nl_agent | Radio changed channel |
| `ATN_DFS_RADAR` | DFS detection | rrmd | Radar detected |
| `ATN_11V_RESPONSE` | 11v BTM | configagent | BSS transition response |
| `ATN_AUTH_FAIL` | Auth failure | wl_evt_handler | Authentication failed |

## Debugging

### ioctl Debugging

```bash
# List available private ioctls for an interface
iwpriv wifi0
iwpriv ath0

# Use priv_ioctl CLI tool
priv_ioctl ath0 get_peer_info <mac>
priv_ioctl wifi0 get_acs_params
```

### Netlink Debugging

```bash
# Monitor netlink events
nl-monitor

# Check netlink socket statistics
cat /proc/net/netlink

# Debug nl_agent logs
journalctl -u nl_agent -f
```

## Key Source Files

| File | Layer | Purpose |
|------|-------|---------|
| `ap/src/go/arista-ap/wlanioctl/wlan_ioctl.go` | User (Go) | Go ioctl wrapper |
| `ap/src/go/arista-ap/netlink/messenger.go` | User (Go) | Go netlink client |
| `ap/src/go/arista-ap/netlink/generic_netlink.go` | User (Go) | Generic netlink msgs |
| `ap/src/libioctl/wl_priv_ioctl.c` | User (C) | C ioctl library |
| `ap/src/nl_agent/nl_agent.c` | User (C) | Netlink event listener |
| `ap/src/nl_agent/nl_handlers.c` | User (C) | Event handlers |
| `ap/src/hostapd-2.10/src/drivers/driver_nl80211.c` | User (C) | hostapd nl80211 |
| `ap/src/qca-apps/*/cfg80211_nlwrapper_api.c` | User (C) | cfg80211 wrapper |
| `ap/src/wlan-drivers/ar/core/src/ar_cfg.c` | Kernel | Arista ioctl handler |
| `ap/src/wlan-drivers/ar/core/src/ar_evt.c` | Kernel | Arista event dispatcher |
| `ap/src/priv_ioctl/priv_ioctl_cmds.h` | Header | Private ioctl definitions |
| `ap/src/wlan-drivers/QCA/*/ieee80211_ioctl.h` | Header | IEEE 802.11 ioctl defs |
| `ap/src/wlan-drivers/QCA/*/wlan_nlink_srv.c` | Kernel | QCA netlink service |
| `ap/src/wlan-drivers/QCA/*/ioctl_vendor_generic.c` | Kernel | QCA vendor ioctl |

## Related Documentation

- [KERNEL_USERSPACE.md](KERNEL_USERSPACE.md) - Overall kernel/user architecture
- [DATAPATH_CONTROLPATH.md](DATAPATH_CONTROLPATH.md) - DP/CP architecture
- [GO_CODEBASE.md](GO_CODEBASE.md) - Go agent details

