# Comprehensive Networking Debugging Guide

> A complete reference for diagnosing, troubleshooting, and resolving network issues across all layers of the OSI model.

---

## Table of Contents

1. [Introduction](#introduction)
2. [Network Fundamentals](#network-fundamentals)
3. [OSI Model and Debugging](#osi-model-and-debugging)
4. [Essential Networking Tools](#essential-networking-tools)
5. [DNS Debugging](#dns-debugging)
6. [TCP/IP Troubleshooting](#tcpip-troubleshooting)
7. [HTTP/HTTPS Debugging](#httphttps-debugging)
8. [SSL/TLS Issues](#ssltls-issues)
9. [Firewall and Security](#firewall-and-security)
10. [Load Balancer Debugging](#load-balancer-debugging)
11. [Proxy and VPN Issues](#proxy-and-vpn-issues)
12. [Container Networking](#container-networking)
13. [Kubernetes Networking](#kubernetes-networking)
14. [Cloud Networking](#cloud-networking)
15. [Performance Optimization](#performance-optimization)
16. [Common Issues and Solutions](#common-issues-and-solutions)
17. [Scripts and Automation](#scripts-and-automation)
18. [Best Practices](#best-practices)
19. [Troubleshooting Flowcharts](#troubleshooting-flowcharts)
20. [Reference Tables](#reference-tables)

---

## Introduction

### Purpose of This Guide

This guide serves as a comprehensive reference for network debugging across various environments, from simple local networks to complex distributed cloud systems. Whether you're debugging a simple connectivity issue or investigating complex latency problems in a microservices architecture, this guide provides the tools, techniques, and methodologies needed.

### Prerequisites

- Basic understanding of networking concepts
- Access to command-line tools
- Administrative privileges on the systems being debugged

### How to Use This Guide

1. **Quick Reference**: Jump to specific sections using the table of contents
2. **Systematic Debugging**: Follow the OSI model approach for methodical troubleshooting
3. **Tool Reference**: Use the tools section for command syntax and examples
4. **Scripts**: Utilize provided automation scripts for common tasks

---

## Network Fundamentals

### IP Addressing

#### IPv4 Addressing

IPv4 addresses are 32-bit numbers typically represented in dotted decimal notation.

```
Format: xxx.xxx.xxx.xxx
Example: 192.168.1.100
```

**Address Classes:**

| Class | Range | Default Subnet Mask | Networks | Hosts per Network |
|-------|-------|---------------------|----------|-------------------|
| A | 1.0.0.0 - 126.255.255.255 | 255.0.0.0 | 126 | 16,777,214 |
| B | 128.0.0.0 - 191.255.255.255 | 255.255.0.0 | 16,384 | 65,534 |
| C | 192.0.0.0 - 223.255.255.255 | 255.255.255.0 | 2,097,152 | 254 |
| D | 224.0.0.0 - 239.255.255.255 | N/A (Multicast) | N/A | N/A |
| E | 240.0.0.0 - 255.255.255.255 | N/A (Reserved) | N/A | N/A |

**Private IP Ranges (RFC 1918):**

```
10.0.0.0 - 10.255.255.255     (10.0.0.0/8)
172.16.0.0 - 172.31.255.255   (172.16.0.0/12)
192.168.0.0 - 192.168.255.255 (192.168.0.0/16)
```

#### IPv6 Addressing

IPv6 addresses are 128-bit numbers represented in hexadecimal.

```
Format: xxxx:xxxx:xxxx:xxxx:xxxx:xxxx:xxxx:xxxx
Example: 2001:0db8:85a3:0000:0000:8a2e:0370:7334
Compressed: 2001:db8:85a3::8a2e:370:7334
```

**Special IPv6 Addresses:**

| Address | Description |
|---------|-------------|
| ::1 | Loopback |
| :: | Unspecified |
| fe80::/10 | Link-local |
| fc00::/7 | Unique local |
| 2000::/3 | Global unicast |
| ff00::/8 | Multicast |

### Subnetting

#### CIDR Notation

CIDR (Classless Inter-Domain Routing) notation represents network prefixes.

```
Format: IP_address/prefix_length
Example: 192.168.1.0/24
```

**Common CIDR Blocks:**

| CIDR | Subnet Mask | Hosts | Wildcard |
|------|-------------|-------|----------|
| /32 | 255.255.255.255 | 1 | 0.0.0.0 |
| /31 | 255.255.255.254 | 2 | 0.0.0.1 |
| /30 | 255.255.255.252 | 4 | 0.0.0.3 |
| /29 | 255.255.255.248 | 8 | 0.0.0.7 |
| /28 | 255.255.255.240 | 16 | 0.0.0.15 |
| /27 | 255.255.255.224 | 32 | 0.0.0.31 |
| /26 | 255.255.255.192 | 64 | 0.0.0.63 |
| /25 | 255.255.255.128 | 128 | 0.0.0.127 |
| /24 | 255.255.255.0 | 256 | 0.0.0.255 |
| /23 | 255.255.254.0 | 512 | 0.0.1.255 |
| /22 | 255.255.252.0 | 1024 | 0.0.3.255 |
| /21 | 255.255.248.0 | 2048 | 0.0.7.255 |
| /20 | 255.255.240.0 | 4096 | 0.0.15.255 |
| /19 | 255.255.224.0 | 8192 | 0.0.31.255 |
| /18 | 255.255.192.0 | 16384 | 0.0.63.255 |
| /17 | 255.255.128.0 | 32768 | 0.0.127.255 |
| /16 | 255.255.0.0 | 65536 | 0.0.255.255 |

#### Subnet Calculation Example

```bash
# Calculate subnet details
Network: 192.168.10.0/26

Subnet Mask: 255.255.255.192
Network Address: 192.168.10.0
First Host: 192.168.10.1
Last Host: 192.168.10.62
Broadcast: 192.168.10.63
Usable Hosts: 62
```

### Ports and Protocols

#### Well-Known Ports (0-1023)

| Port | Protocol | Service |
|------|----------|---------|
| 20 | TCP | FTP Data |
| 21 | TCP | FTP Control |
| 22 | TCP | SSH |
| 23 | TCP | Telnet |
| 25 | TCP | SMTP |
| 53 | TCP/UDP | DNS |
| 67 | UDP | DHCP Server |
| 68 | UDP | DHCP Client |
| 69 | UDP | TFTP |
| 80 | TCP | HTTP |
| 110 | TCP | POP3 |
| 123 | UDP | NTP |
| 143 | TCP | IMAP |
| 161 | UDP | SNMP |
| 162 | UDP | SNMP Trap |
| 389 | TCP | LDAP |
| 443 | TCP | HTTPS |
| 445 | TCP | SMB |
| 465 | TCP | SMTPS |
| 514 | UDP | Syslog |
| 587 | TCP | SMTP Submission |
| 636 | TCP | LDAPS |
| 993 | TCP | IMAPS |
| 995 | TCP | POP3S |

#### Registered Ports (1024-49151)

| Port | Protocol | Service |
|------|----------|---------|
| 1433 | TCP | MS SQL |
| 1521 | TCP | Oracle DB |
| 2049 | TCP/UDP | NFS |
| 3306 | TCP | MySQL |
| 3389 | TCP | RDP |
| 5432 | TCP | PostgreSQL |
| 5672 | TCP | AMQP (RabbitMQ) |
| 5900 | TCP | VNC |
| 6379 | TCP | Redis |
| 8080 | TCP | HTTP Proxy |
| 8443 | TCP | HTTPS Alt |
| 9000 | TCP | PHP-FPM |
| 9090 | TCP | Prometheus |
| 9200 | TCP | Elasticsearch |
| 9300 | TCP | Elasticsearch Cluster |
| 11211 | TCP | Memcached |
| 27017 | TCP | MongoDB |

---

## OSI Model and Debugging

Understanding the OSI model is crucial for systematic network debugging. Each layer has specific tools and techniques.

### Layer 1: Physical Layer

**What it handles:**
- Physical transmission of raw bits
- Cables, connectors, hubs
- Signal encoding and transmission

**Common Issues:**
- Cable damage or disconnection
- Incorrect cable types
- Signal interference
- Hardware failures

**Debugging Commands:**

```bash
# Check interface status (Linux)
ip link show
ethtool eth0

# Check interface status (macOS)
ifconfig -a
networksetup -listallhardwareports

# Check interface status (Windows)
netsh interface show interface
ipconfig /all

# Check for link status
ethtool eth0 | grep "Link detected"

# Check cable diagnostics (if supported)
ethtool --test eth0

# View interface statistics
ip -s link show eth0
cat /proc/net/dev
```

**Physical Layer Checklist:**

- [ ] Is the cable properly connected?
- [ ] Is the cable damaged?
- [ ] Is the correct cable type being used?
- [ ] Are the NICs functioning?
- [ ] Is there a link light on the switch/router?
- [ ] Is the port on the switch enabled?

### Layer 2: Data Link Layer

**What it handles:**
- MAC addressing
- Frame encapsulation
- Error detection (CRC)
- VLANs
- Switches and bridges

**Common Issues:**
- MAC address conflicts
- VLAN misconfiguration
- Spanning tree issues
- Switch port security violations
- Broadcast storms

**Debugging Commands:**

```bash
# View MAC address
ip link show eth0
ifconfig eth0 | grep ether

# View ARP cache
arp -a
ip neigh show

# Clear ARP cache
sudo ip neigh flush all
sudo arp -d <ip_address>

# Check for duplicate MAC addresses
arping -D -I eth0 192.168.1.1

# Monitor ARP traffic
tcpdump -i eth0 arp

# View bridge/switch information (Linux bridge)
brctl show
bridge link show

# Check VLAN configuration
cat /proc/net/vlan/config
ip -d link show eth0.100
```

**Layer 2 Troubleshooting Script:**

```bash
#!/bin/bash
# layer2_check.sh - Layer 2 Diagnostics

INTERFACE=${1:-eth0}

echo "=== Layer 2 Diagnostics for $INTERFACE ==="
echo ""

echo "1. Interface MAC Address:"
ip link show $INTERFACE | grep ether

echo ""
echo "2. ARP Cache:"
ip neigh show

echo ""
echo "3. Checking for link status:"
ethtool $INTERFACE 2>/dev/null | grep -E "Link|Speed|Duplex"

echo ""
echo "4. Interface Statistics:"
ip -s link show $INTERFACE

echo ""
echo "5. VLAN Configuration:"
cat /proc/net/vlan/config 2>/dev/null || echo "No VLAN configuration found"
```

### Layer 3: Network Layer

**What it handles:**
- IP addressing
- Routing
- Packet fragmentation
- ICMP

**Common Issues:**
- IP address conflicts
- Incorrect subnet configuration
- Routing problems
- MTU issues
- ICMP blocked

**Debugging Commands:**

```bash
# View IP configuration
ip addr show
ifconfig -a

# View routing table
ip route show
route -n
netstat -rn

# Test connectivity
ping -c 4 8.8.8.8
ping6 -c 4 2001:4860:4860::8888

# Trace route
traceroute 8.8.8.8
traceroute -I 8.8.8.8  # Use ICMP
traceroute -T 8.8.8.8  # Use TCP
mtr 8.8.8.8

# Check for IP conflicts
arping -D -I eth0 192.168.1.100

# Test MTU
ping -c 4 -M do -s 1472 8.8.8.8

# View ICMP statistics
netstat -s | grep -i icmp
cat /proc/net/snmp | grep Icmp
```

**MTU Discovery Script:**

```bash
#!/bin/bash
# mtu_discovery.sh - Find optimal MTU

TARGET=${1:-8.8.8.8}
INTERFACE=${2:-eth0}

echo "Finding optimal MTU to $TARGET"

# Start with 1500 and work down
for size in $(seq 1500 -10 1200); do
    if ping -c 1 -M do -s $((size - 28)) $TARGET > /dev/null 2>&1; then
        echo "MTU $size works"
        WORKING_MTU=$size
        break
    fi
done

# Fine tune
if [ -n "$WORKING_MTU" ]; then
    for size in $(seq $WORKING_MTU 1 $((WORKING_MTU + 10))); do
        if ping -c 1 -M do -s $((size - 28)) $TARGET > /dev/null 2>&1; then
            OPTIMAL_MTU=$size
        else
            break
        fi
    done
    echo "Optimal MTU: $OPTIMAL_MTU"
fi
```


### Layer 4: Transport Layer

**What it handles:**
- TCP/UDP protocols
- Port numbers
- Connection management
- Flow control
- Error recovery

**Common Issues:**
- Port exhaustion
- Connection timeouts
- TCP retransmissions
- UDP packet loss
- Firewall blocking ports

**Debugging Commands:**

```bash
# View active connections
netstat -tuln
ss -tuln

# View all connections with process info
netstat -tulnp
ss -tulnp

# View TCP connection states
netstat -ant | awk '{print $6}' | sort | uniq -c | sort -rn
ss -s

# Check for port exhaustion
cat /proc/sys/net/ipv4/ip_local_port_range
netstat -an | wc -l

# View socket statistics
ss -m
cat /proc/net/sockstat

# Test specific port connectivity
nc -zv host.example.com 443
telnet host.example.com 443

# Monitor TCP connections
tcpdump -i eth0 tcp port 443

# Check for TIME_WAIT connections
netstat -an | grep TIME_WAIT | wc -l

# View TCP retransmissions
netstat -s | grep -i retrans
cat /proc/net/netstat | grep -i retrans
```

**TCP Connection State Reference:**

| State | Description |
|-------|-------------|
| LISTEN | Waiting for connection |
| SYN_SENT | Sent SYN, waiting for SYN-ACK |
| SYN_RECEIVED | Received SYN, sent SYN-ACK |
| ESTABLISHED | Connection established |
| FIN_WAIT_1 | Sent FIN, waiting for ACK |
| FIN_WAIT_2 | Received ACK for FIN |
| CLOSE_WAIT | Received FIN, waiting to close |
| CLOSING | Both sides sent FIN |
| LAST_ACK | Sent FIN, waiting for final ACK |
| TIME_WAIT | Waiting for packets to expire |
| CLOSED | Connection closed |

**TCP Tuning Parameters:**

```bash
# View current TCP parameters
sysctl net.ipv4.tcp_max_syn_backlog
sysctl net.ipv4.tcp_synack_retries
sysctl net.ipv4.tcp_syn_retries
sysctl net.core.somaxconn
sysctl net.ipv4.tcp_keepalive_time
sysctl net.ipv4.tcp_keepalive_probes
sysctl net.ipv4.tcp_keepalive_intvl

# Common tuning for high-load servers
sysctl -w net.core.somaxconn=65535
sysctl -w net.ipv4.tcp_max_syn_backlog=65535
sysctl -w net.ipv4.tcp_tw_reuse=1
sysctl -w net.ipv4.tcp_fin_timeout=30
```

### Layer 5-6: Session and Presentation Layers

**What they handle:**
- Session establishment/termination
- Data encryption/decryption
- Data compression
- Character encoding

**Common Issues:**
- Session timeouts
- SSL/TLS handshake failures
- Certificate problems
- Encoding issues

**Debugging Commands:**

```bash
# Test SSL/TLS connection
openssl s_client -connect host.example.com:443

# Check certificate details
openssl s_client -connect host.example.com:443 -servername host.example.com 2>/dev/null | openssl x509 -noout -text

# Test specific TLS version
openssl s_client -connect host.example.com:443 -tls1_2
openssl s_client -connect host.example.com:443 -tls1_3

# Check certificate expiration
echo | openssl s_client -connect host.example.com:443 2>/dev/null | openssl x509 -noout -dates

# Verify certificate chain
openssl verify -CAfile ca-bundle.crt certificate.crt

# Test cipher suites
nmap --script ssl-enum-ciphers -p 443 host.example.com
```

### Layer 7: Application Layer

**What it handles:**
- Application protocols (HTTP, DNS, SMTP, etc.)
- User interface
- Application services

**Common Issues:**
- Application misconfiguration
- Protocol errors
- Authentication failures
- API errors

**Debugging Commands:**

```bash
# HTTP debugging
curl -v https://example.com
curl -I https://example.com  # Headers only
curl -w "@curl-format.txt" -o /dev/null -s https://example.com

# DNS debugging
dig example.com
nslookup example.com
host example.com

# Email debugging
telnet mail.example.com 25
openssl s_client -connect mail.example.com:587 -starttls smtp

# Database connectivity
mysql -h host -u user -p -e "SELECT 1"
psql -h host -U user -c "SELECT 1"
```

---

## Essential Networking Tools

### ping

The most basic network diagnostic tool for testing connectivity.

**Basic Usage:**

```bash
# Simple ping
ping google.com

# Specify count
ping -c 5 google.com

# Specify interval
ping -i 0.5 google.com

# Specify packet size
ping -s 1000 google.com

# Flood ping (requires root)
sudo ping -f google.com

# Set TTL
ping -t 64 google.com

# Quiet mode (only summary)
ping -q -c 10 google.com

# Timestamp each packet
ping -D google.com
```

**Advanced ping Options:**

```bash
# Don't fragment (test MTU)
ping -M do -s 1472 google.com

# Use specific source interface
ping -I eth0 google.com

# Record route
ping -R google.com

# IPv6 ping
ping6 ipv6.google.com

# Audible ping
ping -a google.com

# Adaptive ping
ping -A google.com
```

**Interpreting ping Output:**

```
PING google.com (142.250.185.206): 56 data bytes
64 bytes from 142.250.185.206: icmp_seq=0 ttl=117 time=12.4 ms
64 bytes from 142.250.185.206: icmp_seq=1 ttl=117 time=11.8 ms
64 bytes from 142.250.185.206: icmp_seq=2 ttl=117 time=12.1 ms

--- google.com ping statistics ---
3 packets transmitted, 3 packets received, 0.0% packet loss
round-trip min/avg/max/stddev = 11.8/12.1/12.4/0.245 ms
```

- **icmp_seq**: Sequence number (missing numbers indicate packet loss)
- **ttl**: Time To Live (hops remaining)
- **time**: Round-trip time in milliseconds

### traceroute / tracert

Shows the path packets take to reach a destination.

**Basic Usage:**

```bash
# Standard traceroute
traceroute google.com

# Use ICMP instead of UDP
traceroute -I google.com

# Use TCP
traceroute -T google.com

# Specify port
traceroute -p 443 google.com

# Set max hops
traceroute -m 30 google.com

# Don't resolve hostnames
traceroute -n google.com

# Set timeout
traceroute -w 3 google.com
```

**MTR (My Traceroute):**

MTR combines ping and traceroute for continuous monitoring.

```bash
# Basic MTR
mtr google.com

# Report mode (non-interactive)
mtr -r -c 100 google.com

# Wide report
mtr -rw -c 100 google.com

# TCP mode
mtr --tcp google.com

# UDP mode
mtr --udp google.com

# Specify port
mtr --tcp --port 443 google.com
```

**Interpreting MTR Output:**

```
HOST: server                      Loss%   Snt   Last   Avg  Best  Wrst StDev
  1.|-- gateway                    0.0%    10    0.5   0.6   0.4   0.9   0.1
  2.|-- isp-router                 0.0%    10    5.2   5.4   4.8   6.1   0.4
  3.|-- ???                       100.0    10    0.0   0.0   0.0   0.0   0.0
  4.|-- core-router                0.0%    10   15.3  15.8  14.9  17.2   0.7
  5.|-- google.com                 0.0%    10   12.1  12.4  11.8  13.2   0.5
```

- **Loss%**: Packet loss percentage
- **Snt**: Packets sent
- **Last/Avg/Best/Wrst**: Latency statistics
- **StDev**: Standard deviation (jitter indicator)


### netstat and ss

View network connections, routing tables, and interface statistics.

**netstat Commands:**

```bash
# All listening ports
netstat -l

# All TCP connections
netstat -t

# All UDP connections
netstat -u

# Show process information
netstat -p

# Numeric output (no DNS resolution)
netstat -n

# Combined: all listening TCP/UDP with process info
netstat -tulnp

# Show routing table
netstat -r

# Show interface statistics
netstat -i

# Show network statistics
netstat -s

# Continuous monitoring
netstat -c
```

**ss Commands (modern replacement):**

```bash
# All sockets
ss -a

# All listening sockets
ss -l

# TCP sockets
ss -t

# UDP sockets
ss -u

# Show process info
ss -p

# Numeric output
ss -n

# Combined
ss -tulnp

# Show socket memory usage
ss -m

# Show timer information
ss -o

# Show detailed socket info
ss -e

# Filter by state
ss state established
ss state time-wait
ss state listening

# Filter by port
ss sport = :443
ss dport = :80

# Filter by address
ss dst 192.168.1.0/24
ss src 10.0.0.0/8

# Complex filter
ss -t state established '( sport = :ssh or dport = :ssh )'
```

### tcpdump

Powerful packet capture and analysis tool.

**Basic Usage:**

```bash
# Capture on interface
tcpdump -i eth0

# Capture specific number of packets
tcpdump -c 100 -i eth0

# Don't resolve hostnames
tcpdump -n -i eth0

# Verbose output
tcpdump -v -i eth0
tcpdump -vv -i eth0
tcpdump -vvv -i eth0

# Write to file
tcpdump -w capture.pcap -i eth0

# Read from file
tcpdump -r capture.pcap

# Show packet contents in ASCII
tcpdump -A -i eth0

# Show packet contents in hex
tcpdump -X -i eth0
```

**Filtering:**

```bash
# By host
tcpdump host 192.168.1.1
tcpdump src host 192.168.1.1
tcpdump dst host 192.168.1.1

# By network
tcpdump net 192.168.1.0/24

# By port
tcpdump port 80
tcpdump portrange 8000-9000
tcpdump src port 443

# By protocol
tcpdump tcp
tcpdump udp
tcpdump icmp
tcpdump arp

# Combined filters
tcpdump 'host 192.168.1.1 and port 80'
tcpdump 'src host 192.168.1.1 and dst port 443'
tcpdump 'tcp and (port 80 or port 443)'
tcpdump 'not port 22'

# By packet size
tcpdump 'len > 1000'
tcpdump 'less 100'

# By TCP flags
tcpdump 'tcp[tcpflags] & (tcp-syn) != 0'
tcpdump 'tcp[tcpflags] & (tcp-rst) != 0'
tcpdump 'tcp[tcpflags] & (tcp-fin) != 0'
tcpdump 'tcp[tcpflags] & (tcp-syn|tcp-ack) == tcp-syn'
```

**Practical Examples:**

```bash
# Capture HTTP requests
tcpdump -i eth0 -A -s 0 'tcp port 80 and (((ip[2:2] - ((ip[0]&0xf)<<2)) - ((tcp[12]&0xf0)>>2)) != 0)'

# Capture DNS queries
tcpdump -i eth0 port 53

# Capture SYN packets (new connections)
tcpdump -i eth0 'tcp[tcpflags] & (tcp-syn) != 0 and tcp[tcpflags] & (tcp-ack) == 0'

# Capture packets with specific content
tcpdump -i eth0 -A 'tcp port 80' | grep -i 'user-agent'

# Capture HTTPS handshakes
tcpdump -i eth0 'tcp port 443 and (tcp[((tcp[12:1] & 0xf0) >> 2)] = 0x16)'

# Monitor for connection resets
tcpdump -i eth0 'tcp[tcpflags] & (tcp-rst) != 0'

# Capture with timestamps
tcpdump -tttt -i eth0

# Rotate capture files
tcpdump -w capture-%Y%m%d%H%M%S.pcap -G 3600 -i eth0
```

### Wireshark / tshark

GUI and CLI packet analyzer for deep packet inspection.

**tshark Basic Usage:**

```bash
# Capture packets
tshark -i eth0

# Capture to file
tshark -i eth0 -w capture.pcap

# Read from file
tshark -r capture.pcap

# Display specific fields
tshark -r capture.pcap -T fields -e ip.src -e ip.dst -e tcp.port

# Filter capture
tshark -i eth0 -f "port 443"

# Display filter
tshark -r capture.pcap -Y "http.request"

# Statistics
tshark -r capture.pcap -z io,stat,1
tshark -r capture.pcap -z conv,tcp
tshark -r capture.pcap -z http,stat
```

**Useful Display Filters:**

```
# HTTP filters
http.request
http.response
http.response.code == 500
http.request.method == "POST"
http.host contains "example.com"

# TLS filters
tls
tls.handshake
tls.alert
ssl.handshake.type == 1

# TCP filters
tcp.analysis.retransmission
tcp.analysis.duplicate_ack
tcp.analysis.zero_window
tcp.analysis.lost_segment
tcp.flags.reset == 1

# DNS filters
dns
dns.flags.response == 1
dns.qry.name contains "example.com"
dns.resp.type == 1

# IP filters
ip.addr == 192.168.1.1
ip.src == 192.168.1.1
ip.dst == 192.168.1.1
```


### curl

Versatile tool for transferring data with URLs.

**Basic Usage:**

```bash
# Simple GET request
curl https://example.com

# Verbose output
curl -v https://example.com

# Very verbose (includes SSL debug)
curl -vv https://example.com

# Show headers only
curl -I https://example.com

# Include headers in output
curl -i https://example.com

# Follow redirects
curl -L https://example.com

# Save output to file
curl -o file.html https://example.com
curl -O https://example.com/file.pdf

# Silent mode
curl -s https://example.com

# Show errors in silent mode
curl -sS https://example.com
```

**HTTP Methods:**

```bash
# POST request
curl -X POST https://api.example.com/data

# POST with data
curl -X POST -d "key=value" https://api.example.com/data

# POST JSON
curl -X POST -H "Content-Type: application/json" \
  -d '{"key":"value"}' https://api.example.com/data

# PUT request
curl -X PUT -d "data" https://api.example.com/resource/1

# DELETE request
curl -X DELETE https://api.example.com/resource/1

# PATCH request
curl -X PATCH -d '{"key":"newvalue"}' https://api.example.com/resource/1
```

**Headers and Authentication:**

```bash
# Custom headers
curl -H "Authorization: Bearer token123" https://api.example.com
curl -H "X-Custom-Header: value" https://api.example.com

# Multiple headers
curl -H "Accept: application/json" \
     -H "Content-Type: application/json" \
     https://api.example.com

# Basic authentication
curl -u username:password https://api.example.com

# Bearer token
curl -H "Authorization: Bearer eyJhbGc..." https://api.example.com

# Cookie handling
curl -c cookies.txt https://example.com  # Save cookies
curl -b cookies.txt https://example.com  # Send cookies
curl -b "session=abc123" https://example.com  # Inline cookie
```

**Timing and Performance:**

```bash
# Create timing format file
cat << 'EOF' > curl-format.txt
    time_namelookup:  %{time_namelookup}s\n
       time_connect:  %{time_connect}s\n
    time_appconnect:  %{time_appconnect}s\n
   time_pretransfer:  %{time_pretransfer}s\n
      time_redirect:  %{time_redirect}s\n
 time_starttransfer:  %{time_starttransfer}s\n
                    ----------\n
         time_total:  %{time_total}s\n
EOF

# Use timing format
curl -w "@curl-format.txt" -o /dev/null -s https://example.com

# Inline timing
curl -w "Total: %{time_total}s\n" -o /dev/null -s https://example.com

# More metrics
curl -w "DNS: %{time_namelookup}s, Connect: %{time_connect}s, \
TLS: %{time_appconnect}s, TTFB: %{time_starttransfer}s, \
Total: %{time_total}s\n" -o /dev/null -s https://example.com
```

**SSL/TLS Options:**

```bash
# Skip certificate verification (insecure)
curl -k https://self-signed.example.com

# Specify CA certificate
curl --cacert /path/to/ca.crt https://example.com

# Client certificate
curl --cert client.crt --key client.key https://example.com

# Force TLS version
curl --tlsv1.2 https://example.com
curl --tlsv1.3 https://example.com

# Show certificate info
curl -v https://example.com 2>&1 | grep -A6 "Server certificate"
```

**Advanced Options:**

```bash
# Set timeout
curl --connect-timeout 5 --max-time 30 https://example.com

# Retry on failure
curl --retry 3 --retry-delay 2 https://example.com

# Limit bandwidth
curl --limit-rate 100K https://example.com/largefile

# Use specific interface
curl --interface eth0 https://example.com

# Resolve hostname to specific IP
curl --resolve example.com:443:1.2.3.4 https://example.com

# Use specific DNS server
curl --dns-servers 8.8.8.8 https://example.com

# Proxy
curl -x http://proxy:8080 https://example.com
curl -x socks5://proxy:1080 https://example.com

# Compressed response
curl --compressed https://example.com
```

### nmap

Network exploration and security auditing tool.

**Basic Scanning:**

```bash
# Ping scan
nmap -sn 192.168.1.0/24

# TCP SYN scan (default, requires root)
nmap -sS 192.168.1.1

# TCP connect scan (no root required)
nmap -sT 192.168.1.1

# UDP scan
nmap -sU 192.168.1.1

# Combined TCP and UDP
nmap -sS -sU 192.168.1.1

# Scan specific ports
nmap -p 22,80,443 192.168.1.1
nmap -p 1-1000 192.168.1.1
nmap -p- 192.168.1.1  # All ports

# Fast scan (top 100 ports)
nmap -F 192.168.1.1

# Service version detection
nmap -sV 192.168.1.1

# OS detection
nmap -O 192.168.1.1

# Aggressive scan
nmap -A 192.168.1.1
```

**Advanced Scanning:**

```bash
# Timing templates (0=slowest, 5=fastest)
nmap -T4 192.168.1.1

# Skip host discovery
nmap -Pn 192.168.1.1

# No DNS resolution
nmap -n 192.168.1.1

# Save output
nmap -oN output.txt 192.168.1.1    # Normal
nmap -oX output.xml 192.168.1.1    # XML
nmap -oG output.gnmap 192.168.1.1  # Grepable
nmap -oA output 192.168.1.1        # All formats

# Script scanning
nmap --script=default 192.168.1.1
nmap --script=vuln 192.168.1.1
nmap --script=ssl-enum-ciphers -p 443 192.168.1.1
nmap --script=http-headers -p 80 192.168.1.1

# Firewall evasion
nmap -f 192.168.1.1  # Fragment packets
nmap -D RND:5 192.168.1.1  # Decoy scan
nmap --source-port 53 192.168.1.1  # Source port
```

---

## DNS Debugging

### Understanding DNS

DNS (Domain Name System) translates domain names to IP addresses.

**DNS Record Types:**

| Type | Description | Example |
|------|-------------|---------|
| A | IPv4 address | example.com → 93.184.216.34 |
| AAAA | IPv6 address | example.com → 2606:2800:220:1:248:1893:25c8:1946 |
| CNAME | Canonical name (alias) | www.example.com → example.com |
| MX | Mail exchange | example.com → mail.example.com |
| NS | Name server | example.com → ns1.example.com |
| TXT | Text record | example.com → "v=spf1 include:_spf.example.com ~all" |
| PTR | Pointer (reverse DNS) | 34.216.184.93.in-addr.arpa → example.com |
| SOA | Start of authority | Zone information |
| SRV | Service | _http._tcp.example.com → 0 5 80 www.example.com |
| CAA | Certificate Authority Authorization | example.com → 0 issue "letsencrypt.org" |

### DNS Debugging Tools

#### dig (Domain Information Groper)

```bash
# Basic query
dig example.com

# Query specific record type
dig example.com A
dig example.com AAAA
dig example.com MX
dig example.com TXT
dig example.com NS
dig example.com SOA

# Query specific DNS server
dig @8.8.8.8 example.com
dig @1.1.1.1 example.com

# Short answer only
dig +short example.com

# Trace DNS resolution
dig +trace example.com

# Reverse DNS lookup
dig -x 93.184.216.34

# Query all records
dig example.com ANY

# TCP instead of UDP
dig +tcp example.com

# Disable recursion
dig +norecurse example.com

# Show query time
dig +stats example.com

# Verbose output
dig +all example.com

# DNSSEC validation
dig +dnssec example.com

# Check DNSSEC chain
dig +sigchase example.com
```

#### nslookup

```bash
# Basic query
nslookup example.com

# Query specific DNS server
nslookup example.com 8.8.8.8

# Interactive mode
nslookup
> set type=mx
> example.com
> set type=ns
> example.com
> exit

# Query specific record type
nslookup -type=mx example.com
nslookup -type=txt example.com
nslookup -type=ns example.com

# Reverse lookup
nslookup 93.184.216.34

# Debug mode
nslookup -debug example.com
```

#### host

```bash
# Basic query
host example.com

# Verbose output
host -v example.com

# Query specific record type
host -t mx example.com
host -t txt example.com
host -t ns example.com

# Use specific DNS server
host example.com 8.8.8.8

# Reverse lookup
host 93.184.216.34

# Query all records
host -a example.com
```

### Common DNS Issues

#### 1. DNS Resolution Failure

**Symptoms:**
- "Could not resolve hostname"
- "Temporary failure in name resolution"
- Applications timing out

**Debugging Steps:**

```bash
# 1. Check if DNS service is running
systemctl status systemd-resolved
systemctl status named

# 2. Check DNS configuration
cat /etc/resolv.conf
resolvectl status

# 3. Test with different DNS servers
dig @8.8.8.8 example.com
dig @1.1.1.1 example.com

# 4. Check if it's specific to one domain
dig google.com
dig example.com

# 5. Check DNS connectivity
nc -zvu 8.8.8.8 53

# 6. Clear DNS cache
systemd-resolve --flush-caches
sudo dscacheutil -flushcache  # macOS
ipconfig /flushdns  # Windows
```

#### 2. DNS Propagation Delays

**Symptoms:**
- Old DNS records still being returned
- Different results from different locations
- Recently changed records not visible

**Debugging Steps:**

```bash
# 1. Check TTL of records
dig +ttl example.com

# 2. Query authoritative nameservers directly
dig NS example.com +short
dig @ns1.example.com example.com

# 3. Compare multiple DNS servers
for dns in 8.8.8.8 1.1.1.1 9.9.9.9; do
    echo "DNS: $dns"
    dig @$dns +short example.com
done

# 4. Check from multiple locations (online tools)
# Use https://www.whatsmydns.net/ or similar

# 5. Monitor propagation over time
watch -n 30 'dig +short example.com'
```

#### 3. DNSSEC Validation Failures

**Symptoms:**
- "SERVFAIL" responses
- Works with some DNS servers but not others

**Debugging Steps:**

```bash
# 1. Check if DNSSEC is the issue
dig example.com          # Normal query
dig +cd example.com      # Disable DNSSEC checking

# 2. Verify DNSSEC records
dig +dnssec example.com
dig DNSKEY example.com
dig DS example.com

# 3. Validate DNSSEC chain
delv example.com

# 4. Check for DNSSEC issues
dig +sigchase +trusted-key=/path/to/key example.com
```

### DNS Configuration Files

#### /etc/resolv.conf

```bash
# Example resolv.conf
nameserver 8.8.8.8
nameserver 8.8.4.4
nameserver 1.1.1.1
search example.com internal.example.com
options timeout:2 attempts:3
```

#### /etc/hosts

```bash
# Static hostname resolution
127.0.0.1   localhost
::1         localhost
192.168.1.10  server.example.com server
10.0.0.5   database.internal db
```

#### systemd-resolved Configuration

```bash
# /etc/systemd/resolved.conf
[Resolve]
DNS=8.8.8.8 8.8.4.4
FallbackDNS=1.1.1.1 9.9.9.9
Domains=~.
DNSSEC=yes
DNSOverTLS=opportunistic
Cache=yes

# Check status
resolvectl status

# Flush cache
resolvectl flush-caches

# Show cache statistics
resolvectl statistics
```

---

## TCP/IP Troubleshooting

### Connection Issues

#### 1. Connection Refused

**Symptoms:**
- "Connection refused" error
- Port scan shows port as closed

**Causes:**
- Service not running
- Service bound to wrong interface
- Firewall blocking

**Debugging Steps:**

```bash
# 1. Check if service is listening
ss -tlnp | grep :PORT
netstat -tlnp | grep :PORT

# 2. Check service status
systemctl status servicename

# 3. Check what address service is bound to
ss -tlnp  # Look for 0.0.0.0 vs 127.0.0.1

# 4. Test locally
curl http://localhost:PORT
nc -zv localhost PORT

# 5. Check firewall
iptables -L -n
firewall-cmd --list-all
ufw status

# 6. Check from remote
nc -zv server PORT
telnet server PORT
```

#### 2. Connection Timeout

**Symptoms:**
- "Connection timed out"
- Long delays before failure

**Causes:**
- Firewall silently dropping packets
- Network routing issues
- Host unreachable
- Service overloaded

**Debugging Steps:**

```bash
# 1. Test basic connectivity
ping target-host

# 2. Check routing
traceroute target-host
mtr target-host

# 3. Test specific port
nc -zv -w5 target-host PORT

# 4. Check firewall rules
iptables -L -n -v | grep DROP
iptables -L -n -v | grep REJECT

# 5. Monitor for SYN packets
tcpdump -i eth0 'tcp[tcpflags] & (tcp-syn) != 0' and host target-host

# 6. Check for SYN floods
netstat -ant | grep SYN_RECV | wc -l

# 7. Check server load
uptime
top -bn1 | head -20
```

#### 3. Connection Reset

**Symptoms:**
- "Connection reset by peer"
- Sudden disconnection

**Causes:**
- Server closed connection abruptly
- Firewall RST injection
- Application crash
- Protocol mismatch

**Debugging Steps:**

```bash
# 1. Capture traffic for analysis
tcpdump -i eth0 -w reset.pcap host target-host and port PORT

# 2. Look for RST packets
tcpdump -i eth0 'tcp[tcpflags] & (tcp-rst) != 0' and host target-host

# 3. Check server logs
journalctl -u servicename -f
tail -f /var/log/application.log

# 4. Check for connection limits
ss -s
cat /proc/sys/net/core/somaxconn
ulimit -n

# 5. Check for kernel drops
netstat -s | grep -i reset
netstat -s | grep -i overflow
```


### Latency and Performance Issues

#### High Latency Diagnosis

```bash
# 1. Measure round-trip time
ping -c 100 target-host | tail -1

# 2. Identify latency location
mtr -rw -c 50 target-host

# 3. Check for packet loss
ping -c 1000 -i 0.1 target-host | grep loss

# 4. Measure TCP connection time
curl -w "TCP Connect: %{time_connect}s\n" -o /dev/null -s http://target-host

# 5. Check for network congestion
ss -ti | grep -E "rtt|cwnd|retrans"

# 6. Monitor latency over time
#!/bin/bash
while true; do
    echo "$(date): $(ping -c 1 target-host | grep time=)"
    sleep 5
done
```

#### Packet Loss Investigation

```bash
# 1. Basic packet loss test
ping -c 1000 -i 0.01 target-host

# 2. MTR for hop-by-hop analysis
mtr -r -c 200 target-host

# 3. Check interface errors
ip -s link show eth0
cat /proc/net/dev

# 4. Check for buffer overruns
netstat -s | grep -E "pruned|collapsed|overflow"

# 5. Check ring buffer sizes
ethtool -g eth0

# 6. Monitor drops in real-time
watch -n 1 "cat /proc/net/dev | grep eth0"
```

#### Network Interface Statistics

```bash
# Full interface statistics
ip -s link show eth0

# Detailed interface info
ethtool eth0

# Driver information
ethtool -i eth0

# Ring buffer sizes
ethtool -g eth0

# Interrupt coalescing
ethtool -c eth0

# Offload settings
ethtool -k eth0

# NIC statistics
ethtool -S eth0 | head -50
```

### TCP Tuning

#### View Current Settings

```bash
# TCP memory settings
sysctl net.ipv4.tcp_mem
sysctl net.ipv4.tcp_rmem
sysctl net.ipv4.tcp_wmem
sysctl net.core.rmem_max
sysctl net.core.wmem_max

# Connection settings
sysctl net.core.somaxconn
sysctl net.ipv4.tcp_max_syn_backlog
sysctl net.ipv4.tcp_max_tw_buckets

# Keepalive settings
sysctl net.ipv4.tcp_keepalive_time
sysctl net.ipv4.tcp_keepalive_probes
sysctl net.ipv4.tcp_keepalive_intvl

# Timeout settings
sysctl net.ipv4.tcp_fin_timeout
sysctl net.ipv4.tcp_syn_retries
sysctl net.ipv4.tcp_synack_retries
```

#### Recommended Tuning for High-Traffic Servers

```bash
# /etc/sysctl.d/99-network-tuning.conf

# Increase socket buffer sizes
net.core.rmem_max = 134217728
net.core.wmem_max = 134217728
net.core.rmem_default = 1048576
net.core.wmem_default = 1048576

# TCP buffer sizes (min, default, max)
net.ipv4.tcp_rmem = 4096 1048576 134217728
net.ipv4.tcp_wmem = 4096 1048576 134217728

# Connection queue sizes
net.core.somaxconn = 65535
net.ipv4.tcp_max_syn_backlog = 65535
net.core.netdev_max_backlog = 65535

# Enable TCP window scaling
net.ipv4.tcp_window_scaling = 1

# Enable TCP timestamps
net.ipv4.tcp_timestamps = 1

# Enable TCP SACK
net.ipv4.tcp_sack = 1

# Reduce TIME_WAIT
net.ipv4.tcp_tw_reuse = 1
net.ipv4.tcp_fin_timeout = 30

# Faster keepalive
net.ipv4.tcp_keepalive_time = 600
net.ipv4.tcp_keepalive_probes = 5
net.ipv4.tcp_keepalive_intvl = 15

# Apply settings
sysctl -p /etc/sysctl.d/99-network-tuning.conf
```

---

## HTTP/HTTPS Debugging

### HTTP Status Codes

| Code | Category | Common Codes |
|------|----------|--------------|
| 1xx | Informational | 100 Continue, 101 Switching Protocols |
| 2xx | Success | 200 OK, 201 Created, 204 No Content |
| 3xx | Redirection | 301 Moved Permanently, 302 Found, 304 Not Modified |
| 4xx | Client Error | 400 Bad Request, 401 Unauthorized, 403 Forbidden, 404 Not Found |
| 5xx | Server Error | 500 Internal Server Error, 502 Bad Gateway, 503 Service Unavailable |

### Debugging HTTP Requests

#### Using curl

```bash
# Verbose request
curl -v https://api.example.com/endpoint

# Show timing breakdown
curl -w "DNS: %{time_namelookup}s\nConnect: %{time_connect}s\nTLS: %{time_appconnect}s\nStart: %{time_starttransfer}s\nTotal: %{time_total}s\n" \
  -o /dev/null -s https://api.example.com

# Test with specific headers
curl -H "Host: example.com" http://192.168.1.1/

# Test POST with JSON
curl -v -X POST \
  -H "Content-Type: application/json" \
  -d '{"key": "value"}' \
  https://api.example.com/data

# Follow redirects with verbose
curl -vL https://example.com

# Show response headers only
curl -sI https://example.com

# Test with custom resolver
curl --resolve api.example.com:443:1.2.3.4 https://api.example.com
```

#### Using httpie (Modern Alternative)

```bash
# Simple GET
http https://api.example.com/users

# POST with JSON
http POST https://api.example.com/users name=John email=john@example.com

# Custom headers
http https://api.example.com Authorization:"Bearer token"

# Verbose output
http -v https://api.example.com

# Download file
http --download https://example.com/file.zip

# Form submission
http -f POST https://example.com/form username=user password=pass
```

### Common HTTP Issues

#### 502 Bad Gateway

**Causes:**
- Upstream server not responding
- Upstream server timeout
- Proxy/load balancer misconfiguration

**Debugging:**

```bash
# 1. Check upstream server directly
curl -v http://upstream-server:port/path

# 2. Check proxy/LB logs
tail -f /var/log/nginx/error.log
journalctl -u nginx -f

# 3. Check if upstream is listening
ss -tlnp | grep :upstream_port

# 4. Check connection to upstream
nc -zv upstream-server port

# 5. Check for timeout issues
curl --connect-timeout 5 --max-time 30 http://upstream-server:port
```

#### 503 Service Unavailable

**Causes:**
- Server overloaded
- Service down for maintenance
- Rate limiting
- Circuit breaker open

**Debugging:**

```bash
# 1. Check server load
uptime
top -bn1

# 2. Check service status
systemctl status application

# 3. Check connection pool
ss -s
ss state established | wc -l

# 4. Check application logs
tail -f /var/log/application/error.log

# 5. Check rate limits
curl -I https://example.com | grep -i rate
```

#### 504 Gateway Timeout

**Causes:**
- Slow upstream response
- Database queries taking too long
- Network latency
- Timeout configuration too low

**Debugging:**

```bash
# 1. Measure upstream response time
time curl -o /dev/null -s upstream-server:port/slow-endpoint

# 2. Check timeout configurations
grep -r timeout /etc/nginx/
grep -r timeout /etc/haproxy/

# 3. Profile slow requests
tcpdump -i any -w slow-request.pcap host upstream-server

# 4. Check database query times
# (Application-specific)

# 5. Increase timeout temporarily for testing
curl --max-time 120 http://example.com/slow-endpoint
```


---

## SSL/TLS Issues

### Certificate Debugging

#### Check Certificate Details

```bash
# View certificate from server
openssl s_client -connect example.com:443 -servername example.com 2>/dev/null | openssl x509 -noout -text

# Check expiration date
echo | openssl s_client -connect example.com:443 -servername example.com 2>/dev/null | openssl x509 -noout -dates

# Check subject and issuer
echo | openssl s_client -connect example.com:443 2>/dev/null | openssl x509 -noout -subject -issuer

# Check SANs (Subject Alternative Names)
echo | openssl s_client -connect example.com:443 2>/dev/null | openssl x509 -noout -ext subjectAltName

# Verify certificate chain
openssl s_client -connect example.com:443 -showcerts 2>/dev/null | awk '/BEGIN/,/END/{print}' > chain.pem
openssl verify -CAfile /etc/ssl/certs/ca-certificates.crt chain.pem

# Check certificate file
openssl x509 -in certificate.crt -noout -text
```

#### Certificate Chain Issues

```bash
# Download full certificate chain
openssl s_client -connect example.com:443 -showcerts 2>/dev/null

# Verify chain
openssl verify -CAfile ca-bundle.crt -untrusted intermediate.crt server.crt

# Check certificate chain order
openssl crl2pkcs7 -nocrl -certfile chain.pem | openssl pkcs7 -print_certs -noout

# Identify missing intermediate
curl -I https://example.com  # Will show SSL error if chain incomplete

# Test with SSL Labs (online)
# https://www.ssllabs.com/ssltest/
```

### TLS Version and Cipher Issues

```bash
# Test TLS versions
openssl s_client -connect example.com:443 -tls1    # TLS 1.0 (deprecated)
openssl s_client -connect example.com:443 -tls1_1  # TLS 1.1 (deprecated)
openssl s_client -connect example.com:443 -tls1_2  # TLS 1.2
openssl s_client -connect example.com:443 -tls1_3  # TLS 1.3

# List supported ciphers
nmap --script ssl-enum-ciphers -p 443 example.com

# Test specific cipher
openssl s_client -connect example.com:443 -cipher 'AES256-GCM-SHA384'

# Check for weak ciphers
testssl.sh example.com:443

# Show negotiated cipher
openssl s_client -connect example.com:443 2>/dev/null | grep "Cipher is"
```

### Common SSL/TLS Errors

#### "certificate verify failed"

**Causes:**
- Self-signed certificate
- Expired certificate
- Untrusted CA
- Missing intermediate certificate

**Solutions:**

```bash
# Check if it's a CA trust issue
curl -v https://example.com 2>&1 | grep -i "ssl\|certificate"

# Bypass verification (for testing only!)
curl -k https://example.com

# Add CA to trust store
cp custom-ca.crt /usr/local/share/ca-certificates/
update-ca-certificates

# Verify with specific CA
curl --cacert /path/to/ca.crt https://example.com
```

#### "SSL handshake failed"

**Causes:**
- TLS version mismatch
- Cipher suite mismatch
- SNI not supported
- Certificate key mismatch

**Debugging:**

```bash
# Verbose SSL debug
openssl s_client -connect example.com:443 -debug

# Test with SNI
openssl s_client -connect example.com:443 -servername example.com

# Check protocol support
for proto in tls1 tls1_1 tls1_2 tls1_3; do
    echo -n "Testing $proto: "
    timeout 3 openssl s_client -connect example.com:443 -$proto 2>/dev/null | grep "Protocol"
done

# Verify certificate matches key
openssl x509 -noout -modulus -in cert.crt | md5sum
openssl rsa -noout -modulus -in private.key | md5sum
```

#### Certificate Expiration Monitoring

```bash
#!/bin/bash
# check_cert_expiry.sh

DOMAINS="example.com api.example.com"
WARN_DAYS=30

for domain in $DOMAINS; do
    expiry=$(echo | openssl s_client -connect $domain:443 -servername $domain 2>/dev/null | \
             openssl x509 -noout -enddate 2>/dev/null | cut -d= -f2)

    if [ -n "$expiry" ]; then
        expiry_epoch=$(date -d "$expiry" +%s)
        now_epoch=$(date +%s)
        days_left=$(( (expiry_epoch - now_epoch) / 86400 ))

        if [ $days_left -lt $WARN_DAYS ]; then
            echo "WARNING: $domain expires in $days_left days ($expiry)"
        else
            echo "OK: $domain expires in $days_left days"
        fi
    else
        echo "ERROR: Could not check $domain"
    fi
done
```

---

## Firewall and Security

### Linux Firewall (iptables)

#### Viewing Rules

```bash
# List all rules
iptables -L -n -v

# List rules with line numbers
iptables -L -n -v --line-numbers

# List NAT rules
iptables -t nat -L -n -v

# List mangle rules
iptables -t mangle -L -n -v

# List specific chain
iptables -L INPUT -n -v
iptables -L OUTPUT -n -v
iptables -L FORWARD -n -v

# Show raw output (for scripting)
iptables-save
```

#### Common Debugging Commands

```bash
# Watch packet counts
watch -n 1 'iptables -L -n -v | head -20'

# Log dropped packets (add logging rule)
iptables -A INPUT -j LOG --log-prefix "IPTables-Dropped: " --log-level 4
tail -f /var/log/messages | grep "IPTables-Dropped"

# Test if port is blocked
iptables -L INPUT -n -v | grep ":80"

# Check for REJECT vs DROP
iptables -L -n -v | grep -E "REJECT|DROP"

# Count dropped packets
iptables -L -n -v | awk '/DROP/ {sum += $1} END {print sum}'
```

#### Temporarily Allow Traffic for Testing

```bash
# Insert allow rule at top (temporary)
iptables -I INPUT 1 -p tcp --dport 80 -j ACCEPT

# Remove test rule
iptables -D INPUT 1

# Flush all rules (CAUTION!)
iptables -F

# Save rules
iptables-save > /etc/iptables/rules.v4

# Restore rules
iptables-restore < /etc/iptables/rules.v4
```

### nftables (Modern Replacement)

```bash
# List all rules
nft list ruleset

# List specific table
nft list table inet filter

# List specific chain
nft list chain inet filter input

# Watch counters
watch -n 1 'nft list ruleset | head -50'

# Add rule
nft add rule inet filter input tcp dport 80 accept

# Delete rule (by handle)
nft -a list ruleset  # Get handle numbers
nft delete rule inet filter input handle 5
```

### UFW (Ubuntu Firewall)

```bash
# Check status
ufw status
ufw status verbose
ufw status numbered

# Allow port
ufw allow 80/tcp
ufw allow 443/tcp

# Deny port
ufw deny 22/tcp

# Allow from specific IP
ufw allow from 192.168.1.0/24 to any port 22

# Delete rule
ufw delete allow 80/tcp

# Logging
ufw logging on
tail -f /var/log/ufw.log
```

### Firewalld (CentOS/RHEL)

```bash
# Check status
firewall-cmd --state
firewall-cmd --list-all

# List zones
firewall-cmd --get-zones
firewall-cmd --get-active-zones

# List services in zone
firewall-cmd --zone=public --list-services
firewall-cmd --zone=public --list-ports

# Add port
firewall-cmd --zone=public --add-port=80/tcp --permanent
firewall-cmd --reload

# Add service
firewall-cmd --zone=public --add-service=http --permanent
firewall-cmd --reload

# Debug mode
firewall-cmd --set-log-denied=all
journalctl -f -u firewalld
```


---

## Load Balancer Debugging

### HAProxy

#### Status and Statistics

```bash
# Check configuration syntax
haproxy -c -f /etc/haproxy/haproxy.cfg

# View runtime info via socket
echo "show info" | socat stdio /var/run/haproxy.sock
echo "show stat" | socat stdio /var/run/haproxy.sock
echo "show servers state" | socat stdio /var/run/haproxy.sock
echo "show backend" | socat stdio /var/run/haproxy.sock

# Enable stats page (add to config)
# listen stats
#     bind *:8404
#     stats enable
#     stats uri /stats
#     stats refresh 10s

# Check logs
journalctl -u haproxy -f
tail -f /var/log/haproxy.log
```

#### Common Debugging Commands

```bash
# Check backend health
echo "show servers state" | socat stdio /var/run/haproxy.sock

# Disable/enable server
echo "disable server backend/server1" | socat stdio /var/run/haproxy.sock
echo "enable server backend/server1" | socat stdio /var/run/haproxy.sock

# Set server weight
echo "set server backend/server1 weight 50" | socat stdio /var/run/haproxy.sock

# Show current sessions
echo "show sess" | socat stdio /var/run/haproxy.sock

# Show errors
echo "show errors" | socat stdio /var/run/haproxy.sock

# Show table entries (stick tables)
echo "show table" | socat stdio /var/run/haproxy.sock
```

### Nginx (as Load Balancer)

#### Status and Debugging

```bash
# Test configuration
nginx -t

# Show compiled modules
nginx -V

# Reload configuration
nginx -s reload

# Check worker processes
ps aux | grep nginx

# View access logs
tail -f /var/log/nginx/access.log

# View error logs
tail -f /var/log/nginx/error.log

# Enable stub_status (add to config)
# location /nginx_status {
#     stub_status;
#     allow 127.0.0.1;
#     deny all;
# }
curl http://localhost/nginx_status
```

#### Upstream Debugging

```bash
# Check upstream status (with nginx plus or ngx_http_upstream_check_module)
curl http://localhost/upstream_status

# Debug upstream connections
# Add to nginx.conf:
# upstream backend {
#     server 10.0.0.1:8080;
#     server 10.0.0.2:8080;
#     keepalive 32;
# }

# Test upstream directly
curl -v http://10.0.0.1:8080/health
curl -v http://10.0.0.2:8080/health

# Check for upstream errors in logs
grep "upstream" /var/log/nginx/error.log
grep "502\|504" /var/log/nginx/access.log
```

### AWS Elastic Load Balancer

```bash
# Check target health (ALB/NLB)
aws elbv2 describe-target-health \
    --target-group-arn arn:aws:elasticloadbalancing:region:account:targetgroup/name/id

# Check load balancer attributes
aws elbv2 describe-load-balancer-attributes \
    --load-balancer-arn arn:aws:elasticloadbalancing:region:account:loadbalancer/app/name/id

# Enable access logs
aws elbv2 modify-load-balancer-attributes \
    --load-balancer-arn arn:aws:... \
    --attributes Key=access_logs.s3.enabled,Value=true \
                 Key=access_logs.s3.bucket,Value=my-bucket

# Check security groups
aws elbv2 describe-load-balancers --names my-lb | jq '.LoadBalancers[0].SecurityGroups'

# Check listeners
aws elbv2 describe-listeners \
    --load-balancer-arn arn:aws:...
```

---

## Proxy and VPN Issues

### HTTP Proxy Debugging

```bash
# Test through proxy
curl -v -x http://proxy:8080 https://example.com

# Test SOCKS proxy
curl -v -x socks5://proxy:1080 https://example.com

# Check proxy environment variables
env | grep -i proxy

# Set proxy environment
export http_proxy=http://proxy:8080
export https_proxy=http://proxy:8080
export no_proxy=localhost,127.0.0.1,.internal.com

# Test proxy authentication
curl -v -x http://user:pass@proxy:8080 https://example.com

# Debug proxy with verbose output
curl -v --proxy-verbose -x http://proxy:8080 https://example.com
```

### VPN Debugging

#### OpenVPN

```bash
# Check VPN status
systemctl status openvpn
systemctl status openvpn@client

# View logs
journalctl -u openvpn -f
tail -f /var/log/openvpn.log

# Test connection manually
openvpn --config /path/to/config.ovpn --verb 4

# Check routing table after VPN connect
ip route show
route -n

# Check if tunnel interface exists
ip addr show tun0

# Test connectivity through VPN
ping 10.8.0.1  # VPN gateway
traceroute 10.8.0.1

# Check DNS through VPN
cat /etc/resolv.conf
dig @10.8.0.1 internal.example.com
```

#### WireGuard

```bash
# Check interface status
wg show

# Show detailed info
wg show wg0

# Check interface exists
ip addr show wg0

# Check routing
ip route show | grep wg0

# Bring up/down interface
wg-quick up wg0
wg-quick down wg0

# Debug with verbose
WG_DEBUG=1 wg-quick up wg0

# Check handshake timing
wg show wg0 latest-handshakes

# Test connectivity
ping 10.0.0.1  # Peer IP

# Monitor traffic
watch -n 1 'wg show wg0'
```

#### IPSec VPN

```bash
# StrongSwan status
strongswan statusall
ipsec statusall

# Check connections
ipsec status

# View logs
journalctl -u strongswan -f

# Restart connection
ipsec down connection-name
ipsec up connection-name

# Debug mode
ipsec start --debug

# Check SA (Security Associations)
ipsec statusall | grep "ESTABLISHED\|INSTALLED"

# Verify routing
ip route show table 220
ip xfrm state
ip xfrm policy
```

---

## Container Networking

### Docker Networking

#### View Networks

```bash
# List networks
docker network ls

# Inspect network
docker network inspect bridge
docker network inspect host

# Show container IP
docker inspect -f '{{range.NetworkSettings.Networks}}{{.IPAddress}}{{end}}' container_name

# Show all container IPs
docker ps -q | xargs -I {} docker inspect -f '{{.Name}} - {{range.NetworkSettings.Networks}}{{.IPAddress}}{{end}}' {}

# Show network mode
docker inspect -f '{{.HostConfig.NetworkMode}}' container_name

# Show port mappings
docker port container_name
```

#### Debugging Container Networking

```bash
# Enter container network namespace
docker exec -it container_name sh

# Inside container:
ip addr
ip route
cat /etc/resolv.conf
ping other_container
curl http://service:port

# From host - run networking tools in container's network namespace
docker run --rm --net container:target_container nicolaka/netshoot ping -c 4 google.com
docker run --rm --net container:target_container nicolaka/netshoot tcpdump -i eth0

# Check iptables NAT rules (for port mapping)
iptables -t nat -L -n -v | grep DOCKER

# Check bridge network
brctl show
ip link show docker0

# Trace network issue
docker run --rm --net container:target_container nicolaka/netshoot mtr -r google.com
```

#### Docker Network Troubleshooting

```bash
# Test DNS resolution
docker run --rm alpine nslookup google.com
docker run --rm --dns 8.8.8.8 alpine nslookup google.com

# Test connectivity between containers
docker network create test-net
docker run -d --name server --network test-net nginx
docker run --rm --network test-net curlimages/curl curl -s http://server

# Check if container can reach host
docker run --rm alpine ping -c 4 host.docker.internal

# Debug network with netshoot
docker run -it --rm --network host nicolaka/netshoot
docker run -it --rm --network container:myapp nicolaka/netshoot

# Check for port conflicts
ss -tlnp | grep :PORT
docker ps -a --format "table {{.Names}}\t{{.Ports}}"
```

### Docker Compose Networking

```bash
# Show compose networks
docker-compose ps
docker network ls | grep compose

# Check service connectivity
docker-compose exec service1 ping service2
docker-compose exec service1 curl http://service2:port

# View service logs for network issues
docker-compose logs -f service_name

# Restart networking
docker-compose down
docker-compose up -d

# Debug DNS
docker-compose exec service1 cat /etc/resolv.conf
docker-compose exec service1 nslookup service2
```


---

## Kubernetes Networking

### Cluster DNS (CoreDNS)

```bash
# Check CoreDNS pods
kubectl get pods -n kube-system -l k8s-app=kube-dns

# Check CoreDNS logs
kubectl logs -n kube-system -l k8s-app=kube-dns -f

# Test DNS resolution from a pod
kubectl run -it --rm debug --image=busybox -- nslookup kubernetes
kubectl run -it --rm debug --image=busybox -- nslookup my-service.my-namespace.svc.cluster.local

# Check CoreDNS ConfigMap
kubectl get configmap -n kube-system coredns -o yaml

# Check kube-dns service
kubectl get svc -n kube-system kube-dns

# Debug DNS from existing pod
kubectl exec -it my-pod -- cat /etc/resolv.conf
kubectl exec -it my-pod -- nslookup my-service
```

### Service Networking

```bash
# List services
kubectl get svc -A

# Describe service
kubectl describe svc my-service

# Check endpoints
kubectl get endpoints my-service
kubectl describe endpoints my-service

# Check service CIDR
kubectl cluster-info dump | grep -m 1 service-cluster-ip-range

# Test service connectivity
kubectl run -it --rm debug --image=curlimages/curl -- curl http://my-service:port

# Check kube-proxy logs
kubectl logs -n kube-system -l k8s-app=kube-proxy -f

# View iptables rules (on node)
iptables -t nat -L KUBE-SERVICES -n
```

### Pod Networking

```bash
# Check pod IP
kubectl get pod my-pod -o wide

# Check pod network config
kubectl exec my-pod -- ip addr
kubectl exec my-pod -- ip route
kubectl exec my-pod -- cat /etc/resolv.conf

# Test connectivity between pods
kubectl exec pod1 -- ping pod2-ip
kubectl exec pod1 -- curl http://pod2-ip:port

# Check network policies
kubectl get networkpolicy -A
kubectl describe networkpolicy my-policy

# Debug with ephemeral container
kubectl debug my-pod -it --image=nicolaka/netshoot

# Check CNI configuration (on node)
ls /etc/cni/net.d/
cat /etc/cni/net.d/*.conf
```

### Ingress Debugging

```bash
# List ingress resources
kubectl get ingress -A

# Describe ingress
kubectl describe ingress my-ingress

# Check ingress controller logs
kubectl logs -n ingress-nginx -l app.kubernetes.io/name=ingress-nginx -f

# Check ingress controller service
kubectl get svc -n ingress-nginx

# Test ingress
curl -v -H "Host: my-app.example.com" http://ingress-ip/path

# Check TLS secret
kubectl get secret my-tls-secret -o yaml

# Debug ingress annotations
kubectl get ingress my-ingress -o yaml | grep -A20 annotations
```

### Network Policies

```bash
# List all network policies
kubectl get networkpolicy -A

# Describe policy
kubectl describe networkpolicy my-policy

# Test if policy is blocking
# Deploy a test pod and try to connect
kubectl run test-pod --image=curlimages/curl -- sleep infinity
kubectl exec test-pod -- curl -v --connect-timeout 5 http://target-service

# Check if CNI supports network policies
# (Calico, Cilium, Weave support them; Flannel does not by default)

# Debug with Calico
calicoctl get networkpolicy -A
calicoctl get globalnetworkpolicy

# Debug with Cilium
cilium endpoint list
cilium policy get
```

### Debugging Tools for Kubernetes

```bash
# Deploy netshoot for debugging
kubectl run netshoot --image=nicolaka/netshoot -- sleep infinity
kubectl exec -it netshoot -- bash

# Inside netshoot:
# - ping, traceroute, mtr
# - dig, nslookup
# - curl, wget
# - tcpdump, tshark
# - iperf3
# - nmap

# Debug in same namespace as target
kubectl run netshoot -n target-namespace --image=nicolaka/netshoot -- sleep infinity

# Debug with host network
kubectl run netshoot --image=nicolaka/netshoot --overrides='{"spec":{"hostNetwork":true}}' -- sleep infinity

# Capture traffic on specific pod
kubectl exec my-pod -- tcpdump -i eth0 -w - | wireshark -k -i -
```

---

## Cloud Networking

### AWS VPC Debugging

```bash
# Check VPC configuration
aws ec2 describe-vpcs --vpc-ids vpc-xxx

# Check subnets
aws ec2 describe-subnets --filters "Name=vpc-id,Values=vpc-xxx"

# Check route tables
aws ec2 describe-route-tables --filters "Name=vpc-id,Values=vpc-xxx"

# Check security groups
aws ec2 describe-security-groups --group-ids sg-xxx

# Check NACLs
aws ec2 describe-network-acls --filters "Name=vpc-id,Values=vpc-xxx"

# Check VPC flow logs
aws ec2 describe-flow-logs --filter "Name=resource-id,Values=vpc-xxx"

# Query flow logs (if in CloudWatch)
aws logs filter-log-events \
    --log-group-name vpc-flow-logs \
    --filter-pattern "REJECT"

# Check NAT Gateway
aws ec2 describe-nat-gateways --filter "Name=vpc-id,Values=vpc-xxx"

# Check Internet Gateway
aws ec2 describe-internet-gateways --filters "Name=attachment.vpc-id,Values=vpc-xxx"

# VPC Reachability Analyzer
aws ec2 create-network-insights-path \
    --source eni-xxx \
    --destination eni-yyy \
    --protocol tcp \
    --destination-port 443
```

### AWS Security Groups

```bash
# List security group rules
aws ec2 describe-security-groups --group-ids sg-xxx --query 'SecurityGroups[0].IpPermissions'

# Check inbound rules
aws ec2 describe-security-groups --group-ids sg-xxx \
    --query 'SecurityGroups[0].IpPermissions[*].[IpProtocol,FromPort,ToPort,IpRanges[0].CidrIp]' \
    --output table

# Check outbound rules
aws ec2 describe-security-groups --group-ids sg-xxx \
    --query 'SecurityGroups[0].IpPermissionsEgress'

# Find security groups attached to instance
aws ec2 describe-instances --instance-ids i-xxx \
    --query 'Reservations[0].Instances[0].SecurityGroups'

# Add rule for debugging
aws ec2 authorize-security-group-ingress \
    --group-id sg-xxx \
    --protocol tcp \
    --port 22 \
    --cidr 1.2.3.4/32
```

### GCP Networking

```bash
# Check VPC networks
gcloud compute networks list
gcloud compute networks describe my-network

# Check subnets
gcloud compute networks subnets list --network=my-network

# Check firewall rules
gcloud compute firewall-rules list
gcloud compute firewall-rules describe my-rule

# Check routes
gcloud compute routes list

# Test connectivity
gcloud compute ssh my-instance --command="curl -v http://target:port"

# Connectivity tests
gcloud network-management connectivity-tests create my-test \
    --source-instance=projects/project/zones/zone/instances/source \
    --destination-instance=projects/project/zones/zone/instances/dest \
    --protocol=TCP \
    --destination-port=443

# Check load balancer health
gcloud compute backend-services get-health my-backend-service
```

### Azure Networking

```bash
# Check VNet
az network vnet show -g myResourceGroup -n myVNet

# Check subnets
az network vnet subnet list -g myResourceGroup --vnet-name myVNet

# Check NSG rules
az network nsg rule list -g myResourceGroup --nsg-name myNSG

# Check route tables
az network route-table list -g myResourceGroup

# Network Watcher - IP flow verify
az network watcher show-topology -g myResourceGroup

# Check connectivity
az network watcher test-ip-flow \
    --resource-group myResourceGroup \
    --vm myVM \
    --direction Inbound \
    --protocol TCP \
    --local "*:22" \
    --remote "1.2.3.4:*"

# Connection Monitor
az network watcher connection-monitor list
```

---

## Performance Optimization

### Bandwidth Testing

```bash
# iperf3 server
iperf3 -s

# iperf3 client
iperf3 -c server-ip
iperf3 -c server-ip -t 30 -P 4  # 30 seconds, 4 parallel streams
iperf3 -c server-ip -u -b 1G    # UDP test with 1Gbps target

# Reverse mode (server sends)
iperf3 -c server-ip -R

# JSON output
iperf3 -c server-ip -J

# Test with specific MSS
iperf3 -c server-ip -M 1400
```

### Latency Optimization

```bash
# Check current latency
ping -c 100 target | tail -1

# Check latency at each hop
mtr -r -c 100 target

# Check TCP latency
tcpping target 443

# Check application latency
curl -w "Total: %{time_total}s, DNS: %{time_namelookup}s, Connect: %{time_connect}s, TTFB: %{time_starttransfer}s\n" \
    -o /dev/null -s http://target

# Check for bufferbloat
# Run speed test while pinging
iperf3 -c server &
ping -c 60 8.8.8.8
```

### TCP Optimization Checklist

```bash
# 1. Check current settings
sysctl -a | grep -E "net\.core|net\.ipv4\.tcp"

# 2. Enable TCP BBR (if available)
sysctl net.ipv4.tcp_congestion_control=bbr
sysctl net.core.default_qdisc=fq

# 3. Increase buffer sizes for high bandwidth
sysctl -w net.core.rmem_max=134217728
sysctl -w net.core.wmem_max=134217728

# 4. Enable TCP timestamps and window scaling
sysctl -w net.ipv4.tcp_timestamps=1
sysctl -w net.ipv4.tcp_window_scaling=1

# 5. Reduce TIME_WAIT
sysctl -w net.ipv4.tcp_fin_timeout=30
sysctl -w net.ipv4.tcp_tw_reuse=1

# 6. Check current congestion control
cat /proc/sys/net/ipv4/tcp_congestion_control
cat /proc/sys/net/ipv4/tcp_available_congestion_control
```


---

## Common Issues and Solutions

### Quick Reference: Issue → Solution

| Issue | Common Causes | Quick Checks |
|-------|--------------|--------------|
| Connection refused | Service not running, wrong port | `ss -tlnp`, `systemctl status` |
| Connection timeout | Firewall, routing issue | `ping`, `traceroute`, `iptables -L` |
| DNS failure | Bad config, DNS server down | `cat /etc/resolv.conf`, `dig @8.8.8.8` |
| SSL handshake failed | Cert expired, TLS mismatch | `openssl s_client`, check dates |
| 502 Bad Gateway | Upstream down | Check upstream directly, logs |
| 504 Gateway Timeout | Slow upstream | Check latency, increase timeout |
| High latency | Congestion, distance | `mtr`, `ping`, check hops |
| Packet loss | Bad link, congestion | `mtr -r`, interface stats |

### Systematic Debugging Approach

#### Step 1: Define the Problem

```markdown
Questions to answer:
- What is the exact error message?
- When did the problem start?
- Is it affecting all users or just some?
- Is it intermittent or constant?
- What changed recently?
```

#### Step 2: Layer-by-Layer Check

```bash
# Layer 1-2: Physical and Data Link
ip link show
ethtool eth0

# Layer 3: Network
ping target
traceroute target
ip route show

# Layer 4: Transport
ss -tlnp
nc -zv target port

# Layer 5-7: Application
curl -v http://target
```

#### Step 3: Isolate the Problem

```bash
# Test from different locations
# Client → Local gateway → Internet → Target

# Step 1: Can you reach the local gateway?
ping $(ip route | grep default | awk '{print $3}')

# Step 2: Can you reach external DNS?
ping 8.8.8.8

# Step 3: Can you resolve DNS?
dig google.com

# Step 4: Can you reach the target?
ping target

# Step 5: Can you reach the specific port?
nc -zv target port
```

### Issue-Specific Troubleshooting

#### "Network is unreachable"

```bash
# Check if interface is up
ip link show

# Check IP address
ip addr show

# Check routing table
ip route show

# Check default gateway
ip route | grep default

# Try adding default route
sudo ip route add default via GATEWAY_IP

# Check if DHCP is working
sudo dhclient -v eth0
```

#### "No route to host"

```bash
# Check routing
ip route show
ip route get TARGET_IP

# Check if target is on same subnet
# If not, check gateway

# Check for firewall blocking ICMP
iptables -L -n | grep icmp

# Try with specific interface
ping -I eth0 target
```

#### "Host unreachable"

```bash
# Check ARP table
arp -n

# Try to ARP the target
arping -I eth0 TARGET_IP

# Check if on same VLAN
ip -d link show eth0

# Check switch/router logs if available
```

#### Slow DNS Resolution

```bash
# Time DNS resolution
time dig example.com

# Try different DNS servers
time dig @8.8.8.8 example.com
time dig @1.1.1.1 example.com

# Check if IPv6 DNS is slow
dig AAAA example.com

# Check /etc/nsswitch.conf
grep hosts /etc/nsswitch.conf

# Check if systemd-resolved is slow
systemd-resolve --status
```

#### Intermittent Connectivity

```bash
# Continuous ping
ping -D target | tee ping.log

# Watch for packet loss
mtr -r -c 1000 target

# Check for interface errors
watch -n 1 'ip -s link show eth0'

# Check dmesg for network errors
dmesg | grep -i eth0
dmesg | grep -i network
dmesg | grep -i link

# Check for duplicate IPs
arping -D -I eth0 YOUR_IP
```

---

## Scripts and Automation

### Comprehensive Network Diagnostics Script

```bash
#!/bin/bash
# network_diagnostics.sh
# Run comprehensive network diagnostics

TARGET=${1:-8.8.8.8}
OUTPUT_DIR="/tmp/network_diag_$(date +%Y%m%d_%H%M%S)"
mkdir -p "$OUTPUT_DIR"

echo "=== Network Diagnostics Report ===" | tee "$OUTPUT_DIR/report.txt"
echo "Date: $(date)" | tee -a "$OUTPUT_DIR/report.txt"
echo "Target: $TARGET" | tee -a "$OUTPUT_DIR/report.txt"
echo "" | tee -a "$OUTPUT_DIR/report.txt"

echo "=== Interface Configuration ===" | tee -a "$OUTPUT_DIR/report.txt"
ip addr show | tee -a "$OUTPUT_DIR/report.txt"
echo "" | tee -a "$OUTPUT_DIR/report.txt"

echo "=== Routing Table ===" | tee -a "$OUTPUT_DIR/report.txt"
ip route show | tee -a "$OUTPUT_DIR/report.txt"
echo "" | tee -a "$OUTPUT_DIR/report.txt"

echo "=== DNS Configuration ===" | tee -a "$OUTPUT_DIR/report.txt"
cat /etc/resolv.conf | tee -a "$OUTPUT_DIR/report.txt"
echo "" | tee -a "$OUTPUT_DIR/report.txt"

echo "=== DNS Resolution Test ===" | tee -a "$OUTPUT_DIR/report.txt"
dig +short google.com | tee -a "$OUTPUT_DIR/report.txt"
echo "" | tee -a "$OUTPUT_DIR/report.txt"

echo "=== Connectivity Test ===" | tee -a "$OUTPUT_DIR/report.txt"
ping -c 5 $TARGET | tee -a "$OUTPUT_DIR/report.txt"
echo "" | tee -a "$OUTPUT_DIR/report.txt"

echo "=== Route Trace ===" | tee -a "$OUTPUT_DIR/report.txt"
traceroute -n -m 15 $TARGET 2>&1 | tee -a "$OUTPUT_DIR/report.txt"
echo "" | tee -a "$OUTPUT_DIR/report.txt"

echo "=== Listening Ports ===" | tee -a "$OUTPUT_DIR/report.txt"
ss -tlnp | tee -a "$OUTPUT_DIR/report.txt"
echo "" | tee -a "$OUTPUT_DIR/report.txt"

echo "=== Active Connections ===" | tee -a "$OUTPUT_DIR/report.txt"
ss -s | tee -a "$OUTPUT_DIR/report.txt"
echo "" | tee -a "$OUTPUT_DIR/report.txt"

echo "=== Firewall Rules ===" | tee -a "$OUTPUT_DIR/report.txt"
iptables -L -n 2>/dev/null | tee -a "$OUTPUT_DIR/report.txt"
echo "" | tee -a "$OUTPUT_DIR/report.txt"

echo "Report saved to: $OUTPUT_DIR/report.txt"
```

### Connection Monitor Script

```bash
#!/bin/bash
# connection_monitor.sh
# Monitor connectivity to a target

TARGET=${1:-8.8.8.8}
INTERVAL=${2:-5}
LOG_FILE="/var/log/connection_monitor.log"

echo "Monitoring connectivity to $TARGET every ${INTERVAL}s"
echo "Logging to $LOG_FILE"
echo "Press Ctrl+C to stop"

while true; do
    TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')

    if ping -c 1 -W 2 $TARGET > /dev/null 2>&1; then
        LATENCY=$(ping -c 1 -W 2 $TARGET | grep time= | sed 's/.*time=\([0-9.]*\).*/\1/')
        echo "$TIMESTAMP OK latency=${LATENCY}ms" | tee -a $LOG_FILE
    else
        echo "$TIMESTAMP FAIL" | tee -a $LOG_FILE
    fi

    sleep $INTERVAL
done
```

### Port Scanner Script

```bash
#!/bin/bash
# port_scanner.sh
# Simple port scanner

TARGET=${1:-localhost}
START_PORT=${2:-1}
END_PORT=${3:-1024}

echo "Scanning $TARGET ports $START_PORT-$END_PORT"

for port in $(seq $START_PORT $END_PORT); do
    timeout 1 bash -c "echo >/dev/tcp/$TARGET/$port" 2>/dev/null && \
        echo "Port $port: OPEN"
done

echo "Scan complete"
```

### SSL Certificate Checker Script

```bash
#!/bin/bash
# ssl_checker.sh
# Check SSL certificates for multiple domains

DOMAINS="$@"
WARN_DAYS=30

if [ -z "$DOMAINS" ]; then
    echo "Usage: $0 domain1 domain2 ..."
    exit 1
fi

echo "SSL Certificate Status Report"
echo "=============================="
echo ""

for domain in $DOMAINS; do
    echo "Checking: $domain"

    # Get certificate info
    CERT_INFO=$(echo | openssl s_client -connect $domain:443 -servername $domain 2>/dev/null | openssl x509 -noout -dates -subject 2>/dev/null)

    if [ -z "$CERT_INFO" ]; then
        echo "  ERROR: Could not retrieve certificate"
        echo ""
        continue
    fi

    # Extract dates
    NOT_AFTER=$(echo "$CERT_INFO" | grep notAfter | cut -d= -f2)
    SUBJECT=$(echo "$CERT_INFO" | grep subject | cut -d= -f2-)

    # Calculate days until expiry
    EXPIRY_EPOCH=$(date -d "$NOT_AFTER" +%s 2>/dev/null || date -j -f "%b %d %T %Y %Z" "$NOT_AFTER" +%s 2>/dev/null)
    NOW_EPOCH=$(date +%s)
    DAYS_LEFT=$(( (EXPIRY_EPOCH - NOW_EPOCH) / 86400 ))

    echo "  Subject: $SUBJECT"
    echo "  Expires: $NOT_AFTER"
    echo "  Days Left: $DAYS_LEFT"

    if [ $DAYS_LEFT -lt 0 ]; then
        echo "  STATUS: EXPIRED!"
    elif [ $DAYS_LEFT -lt $WARN_DAYS ]; then
        echo "  STATUS: WARNING - Expires soon!"
    else
        echo "  STATUS: OK"
    fi
    echo ""
done
```

### HTTP Endpoint Monitor

```bash
#!/bin/bash
# http_monitor.sh
# Monitor HTTP endpoints

ENDPOINTS=(
    "https://api.example.com/health"
    "https://www.example.com"
    "https://app.example.com/status"
)

TIMEOUT=10
LOG_FILE="/var/log/http_monitor.log"

check_endpoint() {
    local url=$1
    local start_time=$(date +%s.%N)

    HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" \
        --connect-timeout $TIMEOUT \
        --max-time $TIMEOUT \
        "$url")

    local end_time=$(date +%s.%N)
    local duration=$(echo "$end_time - $start_time" | bc)

    TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')

    if [ "$HTTP_CODE" -eq 200 ]; then
        echo "$TIMESTAMP OK $url HTTP=$HTTP_CODE time=${duration}s"
    else
        echo "$TIMESTAMP FAIL $url HTTP=$HTTP_CODE"
    fi
}

echo "HTTP Endpoint Monitor"
echo "====================="

for endpoint in "${ENDPOINTS[@]}"; do
    check_endpoint "$endpoint" | tee -a $LOG_FILE
done
```


---

## Best Practices

### Documentation and Logging

#### What to Document

```markdown
1. Network Topology
   - IP addressing scheme
   - VLAN assignments
   - Routing tables
   - Firewall rules

2. Service Dependencies
   - Which services depend on which endpoints
   - Required ports and protocols
   - Expected response times

3. Baseline Metrics
   - Normal latency values
   - Expected bandwidth
   - Typical connection counts

4. Runbooks
   - Common issues and solutions
   - Escalation procedures
   - Contact information
```

#### Log Analysis Tips

```bash
# Common log locations
/var/log/syslog          # General system logs
/var/log/messages        # System messages (RHEL/CentOS)
/var/log/kern.log        # Kernel messages
/var/log/nginx/          # Nginx logs
/var/log/apache2/        # Apache logs
/var/log/haproxy.log     # HAProxy logs
/var/log/firewalld       # Firewalld logs

# Quick log analysis
grep -i "error\|fail\|denied" /var/log/syslog | tail -50

# Time-based filtering
journalctl --since "1 hour ago" -u nginx

# Follow logs in real-time
tail -f /var/log/syslog | grep -i network

# Log aggregation with journalctl
journalctl -u nginx -u haproxy --since today
```

### Monitoring Best Practices

#### Key Metrics to Monitor

```markdown
1. Availability
   - Service uptime
   - Port reachability
   - Health check status

2. Performance
   - Latency (avg, p95, p99)
   - Bandwidth utilization
   - Connection counts

3. Errors
   - Connection failures
   - Timeout rates
   - Error response codes

4. Capacity
   - Port utilization
   - Connection pool usage
   - Buffer utilization
```

#### Alerting Thresholds

```yaml
# Example alerting rules
alerts:
  - name: HighLatency
    condition: avg_latency > 500ms
    severity: warning

  - name: PacketLoss
    condition: packet_loss > 1%
    severity: critical

  - name: ServiceDown
    condition: health_check_failed
    duration: 2m
    severity: critical

  - name: HighConnectionCount
    condition: connections > 80% of max
    severity: warning

  - name: CertificateExpiry
    condition: days_to_expiry < 30
    severity: warning
```

### Security Best Practices

#### Network Hardening Checklist

```markdown
□ Disable unused services and ports
□ Use firewalls to restrict access
□ Implement network segmentation
□ Enable TLS 1.2+ for all services
□ Use strong cipher suites
□ Regularly update SSL certificates
□ Monitor for unusual traffic patterns
□ Log all access attempts
□ Implement rate limiting
□ Use VPNs for remote access
```

#### Firewall Rule Best Practices

```bash
# Default deny policy
iptables -P INPUT DROP
iptables -P FORWARD DROP
iptables -P OUTPUT ACCEPT

# Allow established connections
iptables -A INPUT -m conntrack --ctstate ESTABLISHED,RELATED -j ACCEPT

# Allow loopback
iptables -A INPUT -i lo -j ACCEPT

# Allow specific services
iptables -A INPUT -p tcp --dport 22 -s 10.0.0.0/8 -j ACCEPT
iptables -A INPUT -p tcp --dport 80 -j ACCEPT
iptables -A INPUT -p tcp --dport 443 -j ACCEPT

# Log dropped packets
iptables -A INPUT -j LOG --log-prefix "IPTables-Dropped: "
```

---

## Troubleshooting Flowcharts

### General Connectivity Troubleshooting

```
┌─────────────────────────────────────────────────────────┐
│                Can you ping localhost?                   │
└─────────────────────────────────────────────────────────┘
                          │
           ┌──────────────┴──────────────┐
           │ NO                          │ YES
           ▼                             ▼
┌──────────────────────┐    ┌─────────────────────────────┐
│ Check network stack  │    │ Can you ping your gateway?  │
│ - Is interface up?   │    └─────────────────────────────┘
│ - Is IP configured?  │                  │
└──────────────────────┘       ┌──────────┴──────────┐
                               │ NO                  │ YES
                               ▼                     ▼
                  ┌─────────────────────┐  ┌───────────────────┐
                  │ Check Layer 1-2     │  │ Can you ping      │
                  │ - Cable connected?  │  │ 8.8.8.8?          │
                  │ - Link light on?    │  └───────────────────┘
                  │ - Correct VLAN?     │            │
                  └─────────────────────┘   ┌────────┴────────┐
                                            │ NO              │ YES
                                            ▼                 ▼
                               ┌─────────────────┐  ┌─────────────────┐
                               │ Check routing   │  │ Can you resolve │
                               │ and firewall    │  │ DNS names?      │
                               └─────────────────┘  └─────────────────┘
                                                              │
                                                    ┌─────────┴─────────┐
                                                    │ NO                │ YES
                                                    ▼                   ▼
                                       ┌─────────────────┐  ┌─────────────────┐
                                       │ Check DNS       │  │ Can you connect │
                                       │ configuration   │  │ to target port? │
                                       └─────────────────┘  └─────────────────┘
                                                                      │
                                                            ┌─────────┴─────────┐
                                                            │ NO                │ YES
                                                            ▼                   ▼
                                               ┌─────────────────┐  ┌─────────────────┐
                                               │ Check firewall  │  │ Application     │
                                               │ and service     │  │ issue - check   │
                                               │ status          │  │ app logs        │
                                               └─────────────────┘  └─────────────────┘
```

### DNS Troubleshooting Flowchart

```
┌─────────────────────────────────────────────────────────┐
│           DNS Resolution Failing?                        │
└─────────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────┐
│     Can you resolve with dig @8.8.8.8?                  │
└─────────────────────────────────────────────────────────┘
                          │
           ┌──────────────┴──────────────┐
           │ NO                          │ YES
           ▼                             ▼
┌──────────────────────┐    ┌─────────────────────────────┐
│ Network issue -      │    │ Local DNS config issue      │
│ Check connectivity   │    │ Check /etc/resolv.conf      │
│ to 8.8.8.8:53        │    │ Check systemd-resolved      │
└──────────────────────┘    └─────────────────────────────┘
```

### TLS/SSL Troubleshooting Flowchart

```
┌─────────────────────────────────────────────────────────┐
│              SSL/TLS Connection Failing?                 │
└─────────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────┐
│   Run: openssl s_client -connect host:443               │
└─────────────────────────────────────────────────────────┘
                          │
           ┌──────────────┼──────────────┐
           │              │              │
           ▼              ▼              ▼
    ┌────────────┐ ┌────────────┐ ┌────────────┐
    │ Connection │ │ Handshake  │ │ Certificate│
    │ refused    │ │ failure    │ │ error      │
    └────────────┘ └────────────┘ └────────────┘
           │              │              │
           ▼              ▼              ▼
    ┌────────────┐ ┌────────────┐ ┌────────────┐
    │ Port open? │ │ TLS version│ │ Check      │
    │ Service    │ │ Cipher     │ │ expiration │
    │ running?   │ │ mismatch?  │ │ chain,     │
    │            │ │ SNI issue? │ │ CA trust   │
    └────────────┘ └────────────┘ └────────────┘
```

---

## Reference Tables

### ICMP Types and Codes

| Type | Code | Description |
|------|------|-------------|
| 0 | 0 | Echo Reply |
| 3 | 0 | Network Unreachable |
| 3 | 1 | Host Unreachable |
| 3 | 2 | Protocol Unreachable |
| 3 | 3 | Port Unreachable |
| 3 | 4 | Fragmentation Needed |
| 3 | 9 | Network Administratively Prohibited |
| 3 | 10 | Host Administratively Prohibited |
| 3 | 13 | Communication Administratively Prohibited |
| 8 | 0 | Echo Request |
| 11 | 0 | TTL Exceeded |
| 11 | 1 | Fragment Reassembly Time Exceeded |

### Common Network Ports Quick Reference

| Port | Service | Description |
|------|---------|-------------|
| 22 | SSH | Secure Shell |
| 25 | SMTP | Email sending |
| 53 | DNS | Domain name resolution |
| 80 | HTTP | Web traffic |
| 443 | HTTPS | Secure web traffic |
| 3306 | MySQL | MySQL database |
| 5432 | PostgreSQL | PostgreSQL database |
| 6379 | Redis | Redis cache |
| 8080 | HTTP-ALT | Alternative HTTP |
| 9090 | Prometheus | Metrics |
| 27017 | MongoDB | MongoDB database |

### HTTP Status Codes Quick Reference

| Code Range | Category | Common Codes |
|------------|----------|--------------|
| 1xx | Informational | 100 Continue |
| 2xx | Success | 200 OK, 201 Created, 204 No Content |
| 3xx | Redirection | 301 Permanent, 302 Found, 304 Not Modified |
| 4xx | Client Error | 400 Bad Request, 401 Unauthorized, 403 Forbidden, 404 Not Found, 429 Too Many Requests |
| 5xx | Server Error | 500 Internal Error, 502 Bad Gateway, 503 Unavailable, 504 Gateway Timeout |

### TCP Flags Reference

| Flag | Description | Usage |
|------|-------------|-------|
| SYN | Synchronize | Initiate connection |
| ACK | Acknowledge | Acknowledge received data |
| FIN | Finish | Close connection |
| RST | Reset | Abort connection |
| PSH | Push | Send data immediately |
| URG | Urgent | Urgent data |

### curl Exit Codes

| Code | Description |
|------|-------------|
| 0 | Success |
| 6 | Could not resolve host |
| 7 | Failed to connect |
| 28 | Operation timeout |
| 35 | SSL connect error |
| 51 | SSL peer certificate invalid |
| 52 | Empty reply from server |
| 56 | Failure receiving data |
| 60 | SSL certificate problem |

### Useful One-Liners

```bash
# Find process using a port
lsof -i :PORT
ss -tlnp | grep :PORT

# Check public IP
curl -s ifconfig.me
curl -s ipinfo.io/ip

# Quick bandwidth test
curl -o /dev/null http://speedtest.tele2.net/10MB.zip

# Watch network connections
watch -n 1 'ss -s'

# Monitor new connections
conntrack -E

# Check SSL certificate expiry
echo | openssl s_client -connect host:443 2>/dev/null | openssl x509 -noout -dates

# Quick HTTP response time
curl -w "Total: %{time_total}s\n" -o /dev/null -s https://example.com

# Test TCP connection
timeout 2 bash -c "echo > /dev/tcp/host/port" && echo "Open" || echo "Closed"

# Show routing for specific IP
ip route get 8.8.8.8

# List all network namespaces
ip netns list

# Quick packet capture
tcpdump -c 100 -i any 'port 80 or port 443'
```

---

## Appendix: Tool Installation

### Linux (Debian/Ubuntu)

```bash
# Essential networking tools
apt-get update
apt-get install -y \
    iproute2 \
    iputils-ping \
    traceroute \
    mtr-tiny \
    dnsutils \
    net-tools \
    tcpdump \
    nmap \
    curl \
    wget \
    netcat-openbsd \
    iperf3 \
    ethtool \
    iftop \
    nethogs \
    conntrack

# Advanced tools
apt-get install -y \
    tshark \
    wireshark \
    ngrep \
    hping3 \
    arping \
    socat
```

### Linux (RHEL/CentOS)

```bash
# Essential networking tools
yum install -y \
    iproute \
    iputils \
    traceroute \
    mtr \
    bind-utils \
    net-tools \
    tcpdump \
    nmap \
    curl \
    wget \
    nc \
    iperf3 \
    ethtool \
    iftop \
    nethogs \
    conntrack-tools

# Advanced tools
yum install -y \
    wireshark-cli \
    ngrep \
    hping3 \
    socat
```

### macOS

```bash
# Using Homebrew
brew install \
    iproute2mac \
    mtr \
    nmap \
    tcpdump \
    iperf3 \
    wget \
    curl \
    netcat \
    socat \
    wireshark
```

### Docker (Debugging Container)

```bash
# Use netshoot - the Swiss Army knife for network debugging
docker run -it --rm nicolaka/netshoot

# Or build your own
cat << 'EOF' > Dockerfile
FROM alpine:latest
RUN apk add --no-cache \
    bash \
    curl \
    wget \
    bind-tools \
    iputils \
    tcpdump \
    nmap \
    mtr \
    iperf3 \
    netcat-openbsd \
    socat \
    openssl \
    jq
CMD ["/bin/bash"]
EOF
docker build -t network-debug .
docker run -it --rm network-debug
```

---

## Conclusion

This guide provides comprehensive coverage of network debugging techniques across all layers and environments. Key takeaways:

1. **Systematic Approach**: Always start from the bottom of the OSI model and work your way up
2. **Right Tool for the Job**: Use the appropriate tool for each layer and problem type
3. **Document Everything**: Keep records of your network configuration and baseline metrics
4. **Automation**: Use scripts to automate common debugging tasks
5. **Continuous Monitoring**: Implement monitoring to catch issues before they become critical

Remember: Network debugging is often a process of elimination. Start with the simplest checks and progressively move to more complex diagnostics.

---

*Last Updated: 2026-02-03*
*Version: 1.0*