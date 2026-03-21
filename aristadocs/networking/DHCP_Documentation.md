# DHCP (Dynamic Host Configuration Protocol) - Comprehensive Documentation

## Table of Contents

1. [Introduction](#introduction)
2. [DHCP Protocol Overview](#dhcp-protocol-overview)
3. [DHCPv4 vs DHCPv6](#dhcpv4-vs-dhcpv6)
4. [DHCP Message Types](#dhcp-message-types)
5. [DHCP Options](#dhcp-options)
6. [DHCP Packet Structure](#dhcp-packet-structure)
7. [DHCP Client Implementation](#dhcp-client-implementation)
8. [DHCP Server Implementation](#dhcp-server-implementation)
9. [DHCP Relay Agent](#dhcp-relay-agent)
10. [Lease Management](#lease-management)
11. [Codebase Implementation](#codebase-implementation)
12. [Configuration Files](#configuration-files)
13. [Troubleshooting](#troubleshooting)
14. [Security Considerations](#security-considerations)
15. [Best Practices](#best-practices)

---

## 1. Introduction

### What is DHCP?

Dynamic Host Configuration Protocol (DHCP) is a network management protocol used to automatically assign IP addresses and other network configuration parameters to devices on a network. This eliminates the need for manual IP address configuration, reducing administrative overhead and minimizing configuration errors.

### Purpose and Benefits

- **Automatic IP Assignment**: Devices receive IP addresses automatically upon connecting to the network
- **Centralized Management**: Network administrators can manage IP allocation from a central server
- **Efficient IP Utilization**: Dynamic allocation ensures efficient use of available IP addresses
- **Reduced Configuration Errors**: Automation eliminates manual configuration mistakes
- **Lease-Based Allocation**: Addresses are temporarily assigned and can be reused

### DHCP in Access Point Context

In the context of Access Points (APs), DHCP plays a crucial role in:
- Obtaining network configuration for the AP itself from upstream infrastructure
- Providing IP addresses to wireless clients connected to the AP
- Managing multiple VLANs with different DHCP pools
- Supporting captive portal networks with NAT and local DHCP

---

## 2. DHCP Protocol Overview

### The DORA Process (DHCPv4)

The DHCPv4 protocol follows a four-step process known as DORA:

```
Client                                          Server
   |                                               |
   |  1. DHCPDISCOVER (broadcast)                  |
   |---------------------------------------------->|
   |                                               |
   |  2. DHCPOFFER (unicast/broadcast)             |
   |<----------------------------------------------|
   |                                               |
   |  3. DHCPREQUEST (broadcast)                   |
   |---------------------------------------------->|
   |                                               |
   |  4. DHCPACK (unicast/broadcast)               |
   |<----------------------------------------------|
   |                                               |
```

#### Step 1: DHCP Discover
- Client broadcasts a DHCPDISCOVER message on the local network
- Source IP: 0.0.0.0, Destination IP: 255.255.255.255
- Uses UDP port 67 (server) and 68 (client)
- Contains client MAC address and optional requested parameters

#### Step 2: DHCP Offer
- Server responds with a DHCPOFFER message
- Offers an available IP address from the pool
- Includes lease duration, subnet mask, gateway, and other options

#### Step 3: DHCP Request
- Client broadcasts DHCPREQUEST to accept the offered address
- Broadcast allows other DHCP servers to know the offer was declined

#### Step 4: DHCP Acknowledgment
- Server sends DHCPACK confirming the lease
- Client can now use the assigned IP address

### Transport Layer Details

| Parameter | Value |
|-----------|-------|
| Protocol | UDP |
| Server Port | 67 |
| Client Port | 68 |
| DHCPv6 Server Port | 547 |
| DHCPv6 Client Port | 546 |

---

## 3. DHCPv4 vs DHCPv6

### Key Differences

| Feature | DHCPv4 | DHCPv6 |
|---------|--------|--------|
| IP Version | IPv4 | IPv6 |
| Address Format | 32-bit | 128-bit |
| Broadcast | Uses broadcast | Uses multicast |
| Ports | 67/68 | 547/546 |
| DUID | Not used | Uses DUID for identification |
| Stateless Mode | Not supported | Supports SLAAC |

### DHCPv6 Message Types

| Code | Message | Description |
|------|---------|-------------|
| 1 | SOLICIT | Client looking for servers |
| 2 | ADVERTISE | Server response to SOLICIT |
| 3 | REQUEST | Client requesting configuration |
| 4 | CONFIRM | Client confirming address |
| 5 | RENEW | Client renewing lease |
| 6 | REBIND | Client rebinding lease |
| 7 | REPLY | Server response with configuration |
| 8 | RELEASE | Client releasing address |
| 9 | DECLINE | Client declining address |
| 11 | INFORMATION-REQUEST | Stateless configuration request |

### Stateful vs Stateless DHCPv6

**Stateful DHCPv6**: Server manages and tracks address assignments
**Stateless DHCPv6 (SLAAC)**: Client generates its own address; server provides other configuration

---

## 4. DHCP Message Types

### DHCPv4 Message Types

| Type | Value | Description |
|------|-------|-------------|
| DHCPDISCOVER | 1 | Client broadcast to locate servers |
| DHCPOFFER | 2 | Server response to DISCOVER |
| DHCPREQUEST | 3 | Client requests parameters |
| DHCPDECLINE | 4 | Client declines offered address |
| DHCPACK | 5 | Server acknowledges request |
| DHCPNAK | 6 | Server denies request |
| DHCPRELEASE | 7 | Client releases IP address |
| DHCPINFORM | 8 | Client requests only config info |

### Operation Codes

```c
#define DHCP_BOOTREQUEST 1  // Client to Server
#define DHCP_BOOTREPLY   2  // Server to Client
```

---

## 5. DHCP Options

### Common DHCP Options

| Option | Code | Description |
|--------|------|-------------|
| Subnet Mask | 1 | Subnet mask for the network |
| Router | 3 | Default gateway address(es) |
| DNS Servers | 6 | Domain Name Server addresses |
| Domain Name | 15 | Domain name for client |
| Broadcast Address | 28 | Broadcast address |
| NTP Servers | 42 | Network Time Protocol servers |
| Vendor Specific | 43 | Vendor-specific information |
| Requested IP | 50 | Client's requested IP address |
| Lease Time | 51 | IP address lease time |
| Message Type | 53 | DHCP message type |
| Server Identifier | 54 | DHCP server identifier |
| Parameter List | 55 | Requested parameters |
| Vendor Class ID | 60 | Client's vendor class identifier |
| Client Identifier | 61 | Client identifier |

### Option 43 - Vendor Specific Information

Option 43 is particularly important in AP deployments as it can contain:
- Controller discovery information
- Configuration server addresses
- Vendor-specific provisioning data

```
DHCP Option 43 Format:
+--------+--------+--------+--------+
| Type   | Length | Data...         |
+--------+--------+--------+--------+
```

### Magic Cookie

The DHCP magic cookie is a special 4-byte sequence that identifies DHCP messages:

```c
#define DHCP_MAGIC_COOKIE 0x63825363  // "99.130.83.99" in hex
```

---

## 6. DHCP Packet Structure

### DHCPv4 Packet Format

```
 0                   1                   2                   3
 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|     op (1)    |   htype (1)   |   hlen (1)    |   hops (1)    |
+---------------+---------------+---------------+---------------+
|                            xid (4)                            |
+-------------------------------+-------------------------------+
|           secs (2)            |           flags (2)           |
+-------------------------------+-------------------------------+
|                          ciaddr (4)                           |
+---------------------------------------------------------------+
|                          yiaddr (4)                           |
+---------------------------------------------------------------+
|                          siaddr (4)                           |
+---------------------------------------------------------------+
|                          giaddr (4)                           |
+---------------------------------------------------------------+
|                                                               |
|                          chaddr (16)                          |
|                                                               |
|                                                               |
+---------------------------------------------------------------+
|                                                               |
|                          sname (64)                           |
+---------------------------------------------------------------+
|                                                               |
|                          file (128)                           |
+---------------------------------------------------------------+
|                                                               |
|                          options (variable)                   |
+---------------------------------------------------------------+
```

### Field Descriptions

| Field | Size | Description |
|-------|------|-------------|
| op | 1 byte | Operation code (1=request, 2=reply) |
| htype | 1 byte | Hardware address type (1=Ethernet) |
| hlen | 1 byte | Hardware address length (6 for MAC) |
| hops | 1 byte | Hop count (used by relay agents) |
| xid | 4 bytes | Transaction ID |
| secs | 2 bytes | Seconds elapsed since client started |
| flags | 2 bytes | Flags (bit 0 = broadcast flag) |
| ciaddr | 4 bytes | Client IP address |
| yiaddr | 4 bytes | 'Your' (client) IP address |
| siaddr | 4 bytes | Next server IP address |
| giaddr | 4 bytes | Relay agent IP address |
| chaddr | 16 bytes | Client hardware address |
| sname | 64 bytes | Server host name |
| file | 128 bytes | Boot file name |
| options | Variable | DHCP options |

### C Structure Definition

```c
struct dhcp_packet {
  uint8_t op;           // Message op code
  uint8_t htype;        // Hardware address type
  uint8_t hlen;         // Hardware address length
  uint8_t hops;         // Hop count
  uint32_t xid;         // Transaction ID
  uint16_t secs;        // Seconds since start
  uint16_t flags;       // Flags
  uint32_t ciaddr;      // Client IP address
  uint32_t yiaddr;      // Your (client) IP address
  uint32_t siaddr;      // Server IP address
  uint32_t giaddr;      // Gateway IP address
  uint8_t chaddr[16];   // Client hardware address
  uint8_t sname[64];    // Server host name
  uint8_t file[128];    // Boot filename
  uint32_t magic_cookie; // Magic cookie
  uint8_t options[0];   // Variable length options
} __attribute__((__packed__));
```

### DHCP Option Structure

```c
struct dhcp_option {
  uint8_t type;     // Option type
  uint8_t len;      // Option length
  uint8_t value[0]; // Option value (variable)
} __attribute__((__packed__));
```

---

## 7. DHCP Client Implementation

### udhcpc - BusyBox DHCP Client

The AP uses `udhcpc` (micro DHCP client) from BusyBox for DHCPv4 client functionality.

#### Starting the DHCP Client

```bash
# Basic udhcpc invocation
udhcpc -i <interface> -s <script> [options]

# Example from codebase
UDHCP_START_CMD="$UDHCPC_CMD start "${net_dev}" -S -v --tryagain 40 -V ${VCI_STR} \
    -s /usr/share/udhcpc/default.script"
```

#### Key udhcpc Options

| Option | Description |
|--------|-------------|
| -i | Interface to use |
| -s | Script to run on lease events |
| -S | Log to syslog |
| -v | Verbose output |
| -V | Vendor class string |
| -x | Add extra DHCP option |
| -f | Run in foreground |
| -b | Background after lease obtained |
| --tryagain | Retry interval on failure |

#### DHCP Client Script Events

The script specified with `-s` is called with these events:

| Event | Description |
|-------|-------------|
| deconfig | Interface should be deconfigured |
| bound | Lease obtained, configure interface |
| renew | Lease renewed |
| leasefail | Failed to obtain lease |
| nak | Server sent NAK |

### DHCPv6 Client (dhclient)

For DHCPv6, the AP uses ISC dhclient:

```bash
# DHCPv6 client startup
dhclient -6 -d <interface>
```

### Client State Machine

```
    START
      |
      v
  +--------+
  |  INIT  |<-----------------+
  +--------+                  |
      |                       |
      | Send DISCOVER         |
      v                       |
  +----------+                |
  | SELECTING|                |
  +----------+                |
      |                       |
      | Receive OFFER         |
      v                       |
  +----------+                |
  | REQUESTING|               |
  +----------+                |
      |                       |
      | Receive ACK           | Receive NAK
      v                       |
  +--------+                  |
  |  BOUND |------------------+
  +--------+
      |
      | T1 Timer expires
      v
  +----------+
  | RENEWING |
  +----------+
      |
      | T2 Timer expires (no ACK)
      v
  +----------+
  | REBINDING|
  +----------+
      |
      | Lease expires
      v
  +--------+
  |  INIT  |
  +--------+
```


---

## 8. DHCP Server Implementation

### udhcpd - BusyBox DHCP Server

The AP can function as a DHCP server using `udhcpd` for NAT/captive portal networks.

#### Server Configuration File Structure

```ini
# /etc/udhcpd.conf

# IP Address Pool
start       192.168.1.20    # First IP to assign
end         192.168.1.254   # Last IP to assign

# Interface to listen on
interface   br0             # Bridge interface

# Lease Settings
lease       86400           # Lease time in seconds (24 hours)
max_leases  254             # Maximum concurrent leases

# Network Options
option subnet   255.255.255.0
option router   192.168.1.1
option dns      192.168.1.1 8.8.8.8
option domain   local

# Lease File
lease_file  /var/lib/misc/udhcpd.leases
pidfile     /var/run/udhcpd.pid

# Static Leases (optional)
static_lease 00:11:22:33:44:55 192.168.1.100
```

#### Starting the DHCP Server

```bash
# Start udhcpd with config file
udhcpd -S -f /path/to/udhcpd.conf

# Using procd (OpenWrt style)
procd_set_param command "$PROG" -S -f "$UDHCPD_CONF_FILE"
procd_set_param respawn 3600 5 0
```

#### Server Validation

Before starting the server, configuration validation is performed:

```bash
validate_udhcpd() {
    # Validate configuration file exists and is readable
    # Check IP pool configuration
    # Verify interface exists
    # Ensure no conflicting DHCP servers
}
```

### NAT Portal DHCP

For captive portal networks, the DHCP server provides:
- Private IP addresses to captive clients
- Gateway pointing to the AP
- DNS redirected through the AP for portal functionality

```bash
launch_udhcpd() {
    if [ -f "$UDHCPD_CONF_FILE" ]; then
        validate_udhcpd
        # Delay start to allow bridge initialization
        (sleep 17 && udhcpd.init start "$UDHCPD_CONF_FILE") &
    fi
}
```

---

## 9. DHCP Relay Agent

### Purpose of DHCP Relay

DHCP relay agents forward DHCP messages between clients and servers across different network segments. This is essential when:
- DHCP server is on a different subnet
- Multiple VLANs need centralized DHCP service

### Relay Operation

```
Client          Relay Agent          DHCP Server
   |                 |                    |
   | DISCOVER        |                    |
   |---------------->|                    |
   |                 | DISCOVER (unicast) |
   |                 |------------------->|
   |                 |                    |
   |                 | OFFER              |
   |                 |<-------------------|
   | OFFER           |                    |
   |<----------------|                    |
   |                 |                    |
   | REQUEST         |                    |
   |---------------->|                    |
   |                 | REQUEST (unicast)  |
   |                 |------------------->|
   |                 |                    |
   |                 | ACK                |
   |                 |<-------------------|
   | ACK             |                    |
   |<----------------|                    |
```

### giaddr Field

The relay agent populates the `giaddr` (Gateway IP Address) field with its own IP address on the client's subnet. This allows the DHCP server to:
- Identify which subnet the request originated from
- Select the appropriate address pool
- Route the response back through the relay

### L2 Proxy DHCP Handling

The codebase includes L2 proxy DHCP handling for advanced scenarios:

```c
// Verify DHCP magic cookie
bool l2proxy_dhcp_verify_magic_cookie(const uint8_t* opt_buf) {
    if (!opt_buf) return false;
    return (memcmp(opt_buf, ic_bootp_cookie, 4) ? false : true);
}

// Get DHCP option from packet
uint8_t* l2proxy_dhcp_get_option(uint8_t* opt_buf, size_t buf_len, int option);

// Get DHCP message type
uint8_t l2proxy_dhcp_get_type(uint8_t* opt_buf, size_t buf_len);
```

---

## 10. Lease Management

### Lease Lifecycle

```
  +----------------+
  | IP Available   |
  +----------------+
         |
         | DHCPOFFER sent
         v
  +----------------+
  | Offered        |----+ Offer timeout
  +----------------+    | (no REQUEST)
         |              |
         | DHCPREQUEST  |
         v              v
  +----------------+   +----------------+
  | Bound          |   | IP Available   |
  +----------------+   +----------------+
         |
         | Time passes
         v
  +----------------+
  | T1 (50% lease) |
  +----------------+
         |
         | Renew attempt
         v
  +----------------+
  | T2 (87.5%)     |
  +----------------+
         |
         | Rebind attempt
         v
  +----------------+
  | Lease Expires  |
  +----------------+
         |
         v
  +----------------+
  | IP Available   |
  +----------------+
```

### Lease Timers

| Timer | Default | Description |
|-------|---------|-------------|
| T1 | 50% of lease | Start unicast renewal |
| T2 | 87.5% of lease | Start broadcast rebinding |
| Lease Time | Server configured | Total lease duration |

### Lease Information Structure

```c
struct dhcp_info {
    uint32_t dhcpv4_lease_time;
    uint32_t dhcpv6_lease_time;

    in_addr_t dhcpv4_server_ip;
    in_addr_t default_gw_v4;

    struct in6_addr dhcpv6_server_ip;
    struct in6_addr default_gw_v6;

    char pri_dns_server_v4[SERVERLEN];
    uint16_t pri_dns_server_v4_len;
    char sec_dns_server_v4[SERVERLEN];
    uint16_t sec_dns_server_v4_len;
    char ter_dns_server_v4[SERVERLEN];
    uint16_t ter_dns_server_v4_len;

    // IPv6 DNS servers
    char pri_dns_server_v6[SERVERLEN];
    char sec_dns_server_v6[SERVERLEN];
    char ter_dns_server_v6[SERVERLEN];
};
```

### Lease File Management

```bash
# Lease success indicator
DHCP_LEASE=/tmp/DHCP_Success.$interface

# Wait for DHCP lease
ctr=0
while [ $ctr -lt 8 ]; do
    if [ -f "$DHCP_LEASE" ]; then
        break
    fi
    sleep 1
    ctr=$((ctr + 1))
done
```

### Lease Failure Handling

```bash
case "leasefail")
    # Remove IP address from config
    sed -i '/^IPADDR/d' $NET_CONF_DIR/ifcfg-$interface

    # Apply fallback IP
    ifconfig $interface $FIXED_IP $FIXED_NMASK

    # Remove default route
    route del default dev $interface

    # Trigger lease failure event
    echo "ATN_LEASEFAIL_EVT NETWORK ALERT $vlan,IPv4,expired" >> $EVT_LOGGING_FILE

    touch $LEASEFAIL
    rm -f $DHCP_LEASE
    ;;
```



---

## 11. Codebase Implementation

### Key DHCP Source Files

| File | Purpose |
|------|---------|
| `ap/src/gwmac/src/gwmac_dhcp.c` | Gateway MAC DHCP packet handling |
| `ap/src/gwmac/include/gwmac_dhcp.h` | DHCP packet structures and constants |
| `ap/src/l2proxy/src/l2proxy_dhcp.c` | L2 proxy DHCP handling |
| `ap/src/l2proxy/src/l2proxy_dhcp.h` | L2 proxy DHCP interface |
| `ap/src/common/include/dhcp_info/dhcp_info.h` | DHCP information structures |
| `ap/src/common/src/dhcp_info/dhcp_info.c` | DHCP info parsing |
| `ap/src/wl_evt_handler/src/modules/wl_sta.c` | Station DHCP event handling |

### Gateway MAC DHCP Handler

The gateway MAC module processes DHCP replies to extract gateway information:

```c
int gwmac_dhcp_pkt_handle(struct net_bridge* br,
                          dhcp_packet_t* dhcp_pkt,
                          int pkt_len) {
    dhcp_option_t *dhcp_option = NULL;
    dhcp_option_t *dhcp_router_option = NULL;
    dhcp_option_t *dhcp_subnet_mask_option = NULL;
    dhcp_option_t *dhcp_si_addr_option = NULL;
    uint32_t subnet_mask = 0, dhcp_server_ip = 0;

    // Validate packet
    if ((pkt_len < (sizeof(dhcp_packet_t) + sizeof(dhcp_option_t) +
                    DHCP_OPTION_MESSAGE_TYPE_LEN)) ||
        (dhcp_pkt->op != DHCP_BOOTREPLY) ||
        (dhcp_pkt->magic_cookie != htonl(DHCP_MAGIC_COOKIE)))
        return -1;

    // Parse options and extract gateway information
    // ...
}
```

### DHCP Information Parsing

```c
int get_dhcp_info(const char* comm_ifcfg_conf_file,
                  struct dhcp_info* info) {
    FILE* dhcp_fp = NULL;
    char* line = NULL;

    line = (char*)calloc(1, MAX_FILE_ENTRY_LEN);
    if (line == NULL) {
        LOG(LOG_ERR, "Unable to allocate memory.");
        return -1;
    }

    dhcp_fp = fopen(comm_ifcfg_conf_file, "r");
    if (dhcp_fp == NULL) {
        LOG(LOG_ERR, "Unable to open file %s", comm_ifcfg_conf_file);
        free(line);
        return -1;
    }

    while (fscanf(dhcp_fp, "%s", line) != EOF) {
        parse_dhcp_info(line, info);
    }

    fclose(dhcp_fp);
    free(line);
    return 0;
}
```

### Station DHCP Events

```c
void wl_sta_start_dhcp(struct wl_sta* sta) {
    if (!sta) return;

    LOG(LOG_CRIT, "start the udhcpc");
    system("/opt/client/udhcpc_client >> /tmp/udhcpc_client_log 2>&1 &");
    sta->sta_state = STA_DHCP_STARTED;
}
```

### DHCPv6 Handling

```c
// Extract IPv6 address from DHCPv6 response
struct in6_addr l2proxy_dhcpv6_extract_ip(uint8_t* payload,
                                           size_t payload_len);

// Extract transaction ID from DHCPv6 packet
bool l2proxy_dhcpv6_extract_xid(uint8_t* payload,
                                 size_t payload_len,
                                 uint32_t* xid);

// Check DHCPv6 status code
bool l2proxy_dhcpv6_status_code(uint8_t* payload,
                                 size_t payload_len);
```

---

## 12. Configuration Files

### Interface Configuration (ifcfg)

```bash
# /tmp/net_conf/ifcfg-<interface>
IPADDR=192.168.1.100
NETMASK=255.255.255.0
GATEWAY=192.168.1.1
LeaseTime=86400
DHCP_ServerIP=192.168.1.1
PrimaryDNS=8.8.8.8
SecondaryDNS=8.8.4.4
DNSPrefix=example.com
```

### DHCP Client Configuration

```bash
# Vendor Class Identifier (VCI)
get_vci_string VCI_STR

# Hostname option
if [ "$allow_hostname" = "1" ] && [ "$devicename" != "" ]; then
    UDHCP_START_CMD="$UDHCP_START_CMD -x hostname:${devicename}"
fi
```

### Resolv.conf Generation

```bash
# Clear and rebuild resolv.conf
echo -n > $RESOLV_CONF_V4

if [ -n "$domain" ]; then
    echo "search $domain" >> $RESOLV_CONF_V4
fi

for i in $dns; do
    echo "nameserver $i" >> $RESOLV_CONF_V4
done

# Merge IPv4 and IPv6 DNS entries
merge_dns_entries_sensor $RESOLV_CONF $RESOLV_CONF_V4 $RESOLV_CONF_V6
```

---

## 13. Troubleshooting

### Common DHCP Issues

#### Issue 1: No DHCP Response
**Symptoms**: Client stuck in DISCOVER phase
**Possible Causes**:
- DHCP server not running
- Network connectivity issues
- VLAN misconfiguration
- Firewall blocking UDP 67/68

**Diagnostics**:
```bash
# Check DHCP client status
ps | grep udhcpc

# Monitor DHCP traffic
tcpdump -i eth0 port 67 or port 68

# Check interface status
ifconfig eth0
```

#### Issue 2: Lease Failure
**Symptoms**: leasefail event triggered
**Possible Causes**:
- DHCP pool exhausted
- Server unreachable after initial lease
- IP conflict detected

**Diagnostics**:
```bash
# Check lease failure flag
ls -la /tmp/LEASEFAIL*

# Review DHCP logs
cat /var/log/unified_logs/*.logs | grep -i dhcp
```

#### Issue 3: Wrong Gateway/DNS
**Symptoms**: Connectivity issues after obtaining lease
**Possible Causes**:
- Incorrect DHCP server configuration
- Option 43 conflicts
- Multiple DHCP servers

**Diagnostics**:
```bash
# Check current configuration
cat /tmp/net_conf/ifcfg-eth0

# Verify routes
route -n

# Check DNS resolution
cat /etc/resolv.conf
```

### Debug Logging

Enable verbose DHCP client logging:
```bash
# Start udhcpc with verbose output
udhcpc -v -i eth0 -s /usr/share/udhcpc/default.script
```

### DHCP Packet Analysis

Key fields to examine in DHCP packets:
1. **xid**: Verify transaction ID matches
2. **ciaddr/yiaddr**: Client/Your IP addresses
3. **options**: Parse and validate all options
4. **magic_cookie**: Must be 0x63825363

---

## 14. Security Considerations

### DHCP Threats

#### DHCP Starvation Attack
**Description**: Attacker exhausts DHCP pool with fake requests
**Mitigation**:
- MAC-based rate limiting
- Port security on switches
- DHCP snooping

#### Rogue DHCP Server
**Description**: Unauthorized server provides malicious configuration
**Mitigation**:
- DHCP snooping on switches
- Only trust specific DHCP servers
- Monitor for unexpected DHCP OFFERs

#### DHCP Spoofing
**Description**: Attacker impersonates legitimate DHCP server
**Mitigation**:
- Enable DHCP snooping
- Use 802.1X authentication
- Implement dynamic ARP inspection

### Secure DHCP Configuration

```bash
# Limit maximum leases to prevent exhaustion
max_leases 254

# Use static leases for critical devices
static_lease 00:11:22:33:44:55 192.168.1.10

# Short lease times for guest networks
lease 3600

# Validate client identifiers
```

### Option 43 Security

The Vendor Specific Option (43) can be used maliciously:
- Always validate Option 43 content
- Use CLI override to ignore DHCP-provided discovery info when needed
- Log Option 43 changes for audit purposes

```bash
# CLI override prevents sensord restart from opt43 changes
if [ -f $CLI_DISCOVERY_OVERRIDE ]; then
    DHCP_OPT43_CHANGED="0"
fi
```

---

## 15. Best Practices

### DHCP Server Configuration

1. **Appropriate Pool Size**: Size pools based on expected client count plus margin
2. **Lease Duration**: Balance between address efficiency and client stability
3. **Redundancy**: Consider failover DHCP servers for high availability
4. **Documentation**: Maintain records of static allocations

### DHCP Client Configuration

1. **Retry Strategy**: Configure appropriate retry intervals
2. **Fallback Configuration**: Define behavior when DHCP fails
3. **Hostname Configuration**: Use consistent naming conventions
4. **VCI String**: Include appropriate vendor class identifier

### Network Design

1. **Subnet Planning**: Plan address ranges to avoid conflicts
2. **VLAN Isolation**: Separate DHCP domains per VLAN
3. **Relay Configuration**: Properly configure relay agents for cross-subnet DHCP
4. **Monitoring**: Implement DHCP monitoring and alerting

### Operational Practices

1. **Regular Audits**: Review lease tables periodically
2. **Log Analysis**: Monitor DHCP logs for anomalies
3. **Backup Configuration**: Maintain configuration backups
4. **Testing**: Test DHCP failover scenarios

---

## Appendix A: DHCP Option Reference

### Commonly Used Options

| Code | Name | Length | Description |
|------|------|--------|-------------|
| 1 | Subnet Mask | 4 | Network subnet mask |
| 3 | Router | 4n | Default gateway(s) |
| 6 | DNS | 4n | DNS server(s) |
| 12 | Hostname | Variable | Client hostname |
| 15 | Domain Name | Variable | Domain name |
| 28 | Broadcast | 4 | Broadcast address |
| 42 | NTP Servers | 4n | Time server(s) |
| 43 | Vendor Specific | Variable | Vendor data |
| 50 | Requested IP | 4 | Preferred IP |
| 51 | Lease Time | 4 | Lease duration |
| 53 | Message Type | 1 | DHCP message type |
| 54 | Server ID | 4 | Server identifier |
| 55 | Parameter List | Variable | Requested params |
| 60 | Vendor Class | Variable | Client class |
| 61 | Client ID | Variable | Client identifier |
| 255 | End | 0 | End of options |

---

## Appendix B: Related RFCs

| RFC | Title |
|-----|-------|
| RFC 2131 | Dynamic Host Configuration Protocol |
| RFC 2132 | DHCP Options and BOOTP Vendor Extensions |
| RFC 3315 | DHCPv6 |
| RFC 3646 | DNS Configuration options for DHCPv6 |
| RFC 4361 | Node-specific Client Identifiers |
| RFC 8415 | DHCPv6 (Updated) |

---

*Document Version: 1.0*
*Last Updated: February 2026*