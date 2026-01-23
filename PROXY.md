# Proxy in the AP Network Stack

This document describes the various proxy mechanisms implemented in the Access Point (AP) codebase, their
application at different network layers, and their usage.

## Overview

The AP implements several proxy mechanisms across different network layers:

| Proxy Type    | Network Layer                    | Primary Purpose                            |
| ------------- | -------------------------------- | ------------------------------------------ |
| L2 Proxy      | Layer 2 (Data Link)              | MAC address translation for VXLAN tunnels  |
| Proxy ARP     | Layer 2/3                        | ARP response on behalf of wireless clients |
| Proxy Server  | Layer 4+ (Transport/Application) | Cloud connectivity via HTTP proxy          |
| Netlink Proxy | OS/Kernel                        | Kernel event forwarding to userspace       |
| Radsecproxy   | Layer 7 (Application)            | RADIUS over TLS proxy                      |

---

## 1. L2 Proxy (Layer 2)

### Location

- **Kernel Module**: `ap/src/l2proxy/`
- **Configuration**: `ap/src/go/arista-ap/config/network_conf.go`

### Purpose

L2 Proxy handles MAC address translation for VXLAN tunnels, enabling proper packet forwarding when wireless
clients communicate over Layer 2 tunnels.

### How It Works

1. **TX Path (Client → Network)**: Rewrites client MAC addresses to the AP's MAC in outbound packets,
   maintaining an IP-to-MAC mapping database.

2. **RX Path (Network → Client)**: Looks up destination IP in the client database and rewrites the destination
   MAC to the correct client MAC.

3. **Client Database**: Maintains hash tables for:
   - Client MAC → IP mapping (`client_info_hash`)
   - Client IPv4 → MAC mapping (`client_v4_hash`)
   - Client IPv6 → MAC mapping (`client_v6_hash`)

### Kernel Integration

L2 Proxy hooks into the VXLAN kernel module via function pointers:

```c
int (*l2proxy_vxlan_rx_p)(struct sk_buff* skb, struct vxlan_dev* vxlan);
int (*l2proxy_vxlan_tx_p)(struct sk_buff** pskb, struct vxlan_dev* vxlan);
```

### Configuration

Enable via network configuration:

```go
type NetworkConfig struct {
  VxlanL2Proxy bool  // Enable L2 proxy for VXLAN tunnels
  // ...
}
```

### Key Files

- `l2proxy_main.c` - Module initialization and packet classification
- `l2proxy_clientdb.c` - Client database management
- `l2proxy_proto_handler.c` - Protocol-specific handlers (ARP, IPv4, IPv6)
- `l2proxy_dhcp.c` - DHCP snooping for IP discovery

---

## 2. Proxy ARP (Layer 2/3)

### Location

- **Driver Layer**: `ap/src/wlan-drivers/ar/core/src/ar_proxyarp.c`
- **Vendor Interface**: `ap/src/wlan-drivers/ar/vdrv_if/qca/common/vdrv_cp_if_proxy_arp.c`
- **Configuration**: `ap/src/go/arista-ap/configagent/ssid_mcast_bcast.go`

### Purpose

Proxy ARP allows the AP to respond to ARP requests on behalf of wireless clients, reducing broadcast traffic
on the wireless medium.

### How It Works

1. **Cache Update**: When the AP receives an ARP packet from a client, it updates its local ARP cache with the
   client's IP-MAC binding.

2. **ARP Response**: When an ARP request is received for a known client IP, the AP responds with the cached
   MAC address instead of flooding the request.

3. **Conflict Detection**: Detects IP address conflicts by monitoring ARP packets.

### Configuration

Per-SSID configuration:

```go
type ProxyArpConfig struct {
  ProxyArpEnable      bool  // Enable Proxy ARP
  ProxyArpDgafDisable bool  // Disable downstream group-addressed forwarding
}
```

### Key Functions

```c
void ar_proxyarp_update_cache(struct ar_dp_vdev_s* ar_dp_vdev, wbuf_t wbuf);
void ar_proxyarp_check_ip_conflict(struct ar_dp_vdev_s* dp_vdev, struct sk_buff* skb);
void vdrv_cp_if_proxy_arp_find_update_node(vdrv_if_soc_t soc, uint8_t vdev_id, uint8_t* mac, uint32_t sip);
```

---

## 3. Proxy Server (Cloud Connectivity)

### Location

- **Configuration**: `ap/src/go/arista-ap/aputils/proxy_server_config.go`
- **Sensor Daemon**: `ap/src/libpmac/inc/pmac.h`

### Purpose

Enables the AP to connect to cloud services (e.g., CloudVision) through an HTTP proxy when direct internet
access is not available.

### Configuration Sources

1. **CLI Configuration** (`/opt/ap/sensor/proxycli.conf`)
2. **DHCP Option 43** (`/tmp/dhcp_opt43.conf`)

### Selection Method

```go
proxyServerSelectionMethod:
0 = Don't use proxy
1 = Use CLI-configured proxy
2 = Use DHCP Option 43 proxy (default)
```

### Data Structure

```go
type ProxyServerConfig struct {
  UseProxy        bool
  SelectionMethod int32
  IP              string
  Port            int64
}
```

---

## 4. Netlink Proxy

### Location

- `ap/src/netlink_proxy/nl_evt_proxy.c`

### Purpose

Forwards kernel netlink events to userspace applications via POSIX message queues.

### How It Works

1. Listens on a NETLINK_ROUTE socket for kernel events
2. Receives interface up/down, address changes, and routing events
3. Forwards events to interested userspace daemons via message queues

### Event Flow

```
Kernel → Netlink Socket → nl_evt_proxy → POSIX MQ → Userspace Daemons
```

---

## 5. Radsecproxy (RADIUS Proxy)

### Location

- `ap/src/go/arista-ap/config/rspconf/radsecproxy_conf.go`

### Purpose

Proxies RADIUS authentication/accounting traffic over TLS, providing secure transport for AAA communications.

### Configuration

```go
type Radsecproxy struct {
  ListenAuthPort uint16
  ListenAcctPort uint16
  TLS            *TLS
  Cl             Client
  Ser            *Server
  Rlm            Realm
}
```

---

## Summary

| Proxy         | Layer       | Direction     | Key Benefit                               |
| ------------- | ----------- | ------------- | ----------------------------------------- |
| L2 Proxy      | L2          | Bidirectional | Enables MAC translation for VXLAN tunnels |
| Proxy ARP     | L2/L3       | AP responds   | Reduces wireless broadcast traffic        |
| Proxy Server  | L4+         | Outbound      | Cloud connectivity through firewalls      |
| Netlink Proxy | Kernel/User | Kernel → User | Decouples kernel events from userspace    |
| Radsecproxy   | L7          | Bidirectional | Secure RADIUS transport                   |
