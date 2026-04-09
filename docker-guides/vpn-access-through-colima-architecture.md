# VPN Access Through Colima VM to Docker Containers - Complete Architecture Guide

**Last Updated:** March 24, 2026

---

## Table of Contents

1. [Overview](#overview)
2. [Network Architecture Layers](#network-architecture-layers)
3. [How VPN Access Works Through the Stack](#how-vpn-access-works-through-the-stack)
4. [Detailed Layer-by-Layer Explanation](#detailed-layer-by-layer-explanation)
5. [Network Modes in Docker](#network-modes-in-docker)
6. [Troubleshooting VPN Connectivity](#troubleshooting-vpn-connectivity)
7. [Practical Examples](#practical-examples)

---

## Overview

When you connect to Arista VPN on your Mac via WiFi and run Docker containers inside Colima VM, the network traffic flows through multiple layers. This guide explains exactly how containers can access VPN-protected resources.

### The Question

> "When I'm using Colima as a virtual machine, how can Docker containers access Arista VPN running on my Mac when I'm connected via WiFi? How does docker-compose replicate this?"

### The Short Answer

**Your containers CAN access VPN resources because:**
1. Your Mac's VPN connection modifies the host routing table
2. Colima VM uses your Mac as its network gateway (via NAT or bridging)
3. Docker containers inherit network access from the Colima VM
4. With `--network host` mode, containers use the VM's network stack directly
5. Traffic flows: Container → Colima VM → Mac → VPN → Arista Network

---

## Network Architecture Layers

```
┌─────────────────────────────────────────────────────────────────┐
│                    ARISTA INTERNAL NETWORK                      │
│              (10.14.0.0/16, sjc.aristanetworks.com)            │
└─────────────────────────────────────────────────────────────────┘
                              ▲
                              │ VPN Tunnel (encrypted)
                              │
┌─────────────────────────────────────────────────────────────────┐
│  LAYER 1: Mac Host (macOS)                                      │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │ WiFi Interface (en0): 192.168.1.100                       │  │
│  │ VPN Interface (utun3): 10.14.x.x                          │  │
│  │ Routing Table:                                            │  │
│  │   - 10.14.0.0/16 → utun3 (VPN)                           │  │
│  │   - 10.128.0.0/16 → utun3 (VPN)                          │  │
│  │   - 0.0.0.0/0 → en0 (default via WiFi)                   │  │
│  └───────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                              ▲
                              │ NAT / Bridge
                              │
┌─────────────────────────────────────────────────────────────────┐
│  LAYER 2: Colima VM (Linux VM on Mac)                          │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │ VM Network Interface: 192.168.106.2                       │  │
│  │ Gateway: 192.168.106.1 (Mac host)                         │  │
│  │ DNS: 10.14.0.1, 10.128.1.1 (Arista DNS servers)          │  │
│  │ Routing: Default route → Mac host                        │  │
│  └───────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                              ▲
                              │ Docker networking
                              │
┌─────────────────────────────────────────────────────────────────┐
│  LAYER 3: Docker Containers                                     │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │ Container 1 (wifiap) - Network Mode: host                 │  │
│  │   - Uses VM's network stack directly                      │  │
│  │   - IP: Same as VM (192.168.106.2)                        │  │
│  │   - DNS: 10.14.0.1, 10.128.1.1                           │  │
│  │                                                            │  │
│  │ Container 2 (artools-base) - Network Mode: host           │  │
│  │   - Uses VM's network stack directly                      │  │
│  │   - IP: Same as VM (192.168.106.2)                        │  │
│  │   - DNS: 10.14.0.1, 10.128.1.1                           │  │
│  └───────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

---

## How VPN Access Works Through the Stack

### Step-by-Step Traffic Flow

Let's trace what happens when a container tries to access `git.sjc.aristanetworks.com` (internal Arista resource):

#### Step 1: Container Makes Request
```bash
# Inside wifiap container
$ curl https://git.sjc.aristanetworks.com
```

#### Step 2: DNS Resolution
```
Container → Colima VM DNS resolver → Mac DNS resolver → VPN DNS (10.14.0.1)
```

The container's `/etc/resolv.conf` contains:
```
nameserver 10.14.0.1
nameserver 10.128.1.1
search sjc.aristanetworks.com aristanetworks.com
```

#### Step 3: Routing Decision in Container
Since container uses `--network host`, it shares the VM's network namespace:
```bash
# Container sees VM's routing table
$ ip route
default via 192.168.106.1 dev eth0
192.168.106.0/24 dev eth0 scope link
```

#### Step 4: Packet Leaves Container → VM
Packet destination: `10.14.50.100` (git.sjc.aristanetworks.com)
- Container sends packet to VM's network stack
- VM routing table: "10.14.0.0/16 → send to gateway (Mac)"

#### Step 5: VM → Mac Host
- Packet arrives at Mac via Colima's virtual network interface
- Mac's routing table is consulted

#### Step 6: Mac Routing Decision
```bash
# Mac's routing table (when VPN is connected)
$ netstat -nr
Destination        Gateway            Flags    Netif
10.14.0.0/16       10.14.1.1          UGSc     utun3   # VPN route
10.128.0.0/16      10.14.1.1          UGSc     utun3   # VPN route
default            192.168.1.1        UGSc     en0     # WiFi default
```

Mac sees destination `10.14.50.100` matches `10.14.0.0/16` → route via `utun3` (VPN interface)

#### Step 7: VPN Tunnel
- Packet is encrypted by VPN client
- Sent through WiFi (en0) to VPN gateway
- VPN gateway decrypts and forwards to Arista internal network

#### Step 8: Response Path
```
Arista Server → VPN Gateway → Mac (utun3) → Colima VM → Container
```

---

## Detailed Layer-by-Layer Explanation

### Layer 1: Mac Host Network

#### WiFi Connection
```bash
# Your Mac's WiFi interface
$ ifconfig en0
en0: flags=8863<UP,BROADCAST,SMART,RUNNING,SIMPLEX,MULTICAST> mtu 1500
    inet 192.168.1.100 netmask 0xffffff00 broadcast 192.168.1.255
```

**What this provides:**
- Physical network connectivity to the internet
- IP address from your home/office router (192.168.1.100)
- Default gateway to reach the internet (192.168.1.1)

#### VPN Connection (Arista VPN)
```bash
# VPN tunnel interface (created when VPN connects)
$ ifconfig utun3
utun3: flags=8051<UP,POINTOPOINT,RUNNING,MULTICAST> mtu 1400
    inet 10.14.25.50 --> 10.14.1.1 netmask 0xffffffff
```

**What this provides:**
- Virtual tunnel interface (utun3, utun4, etc.)
- IP address on Arista's internal network (10.14.25.50)
- Point-to-point connection to VPN gateway (10.14.1.1)
- Encrypted tunnel for all traffic to Arista networks

#### Mac Routing Table (With VPN Connected)
```bash
$ netstat -nr
Routing tables

Internet:
Destination        Gateway            Flags    Netif Expire
default            192.168.1.1        UGSc     en0         # Default via WiFi
10.14.0.0/16       10.14.1.1          UGSc     utun3       # Arista SJC network
10.128.0.0/16      10.14.1.1          UGSc     utun3       # Arista other sites
172.16.0.0/12      10.14.1.1          UGSc     utun3       # Arista private ranges
192.168.1.0/24     link#4             UCS      en0         # Local WiFi network
192.168.106.0/24   link#20            UCS      bridge100   # Colima VM network
```

**Key Points:**
- Specific routes for Arista networks (10.14.0.0/16, 10.128.0.0/16) go through VPN
- Default route still goes through WiFi (for internet access)
- Colima VM network (192.168.106.0/24) is on a virtual bridge
- This is **split-tunnel VPN** - only Arista traffic goes through VPN

#### Mac DNS Configuration
```bash
$ scutil --dns
DNS configuration

resolver #1
  nameserver[0] : 192.168.1.1        # Home router DNS

resolver #2
  domain   : sjc.aristanetworks.com
  nameserver[0] : 10.14.0.1          # Arista DNS (via VPN)
  nameserver[1] : 10.128.1.1         # Arista DNS backup

resolver #3
  domain   : aristanetworks.com
  nameserver[0] : 10.14.0.1
```

**Key Points:**
- Multiple DNS resolvers based on domain
- Arista domains (*.aristanetworks.com) use Arista DNS servers
- General internet queries use home router DNS
- DNS servers 10.14.0.1 and 10.128.1.1 are only reachable via VPN

---

### Layer 2: Colima VM Network

#### How Colima VM Connects to Mac

Colima creates a Linux VM using one of these hypervisors:
- **QEMU** (default on Apple Silicon)
- **VZ** (Apple's Virtualization framework)

The VM networking can use different modes:

##### Mode 1: NAT (Network Address Translation) - Default
```bash
# Inside Colima VM
$ ip addr show col0
col0: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 1500
    inet 192.168.106.2/24 brd 192.168.106.255 scope global col0

$ ip route
default via 192.168.106.1 dev col0
192.168.106.0/24 dev col0 proto kernel scope link src 192.168.106.2
```

**How NAT Works:**
```
Container (192.168.106.2) → Mac translates to (192.168.1.100) → Internet/VPN
```

- VM has private IP (192.168.106.2)
- Mac acts as NAT gateway (192.168.106.1)
- All VM traffic appears to come from Mac's IP
- **VPN routes on Mac apply to VM traffic!**

##### Mode 2: Bridge Mode
```bash
# VM gets IP on same network as Mac
VM IP: 192.168.1.150 (from same DHCP as Mac)
```

**How Bridge Works:**
- VM appears as separate device on your WiFi network
- Gets its own IP from router
- Still routes through Mac for VPN access (Mac is the VPN client)

#### Colima VM DNS Configuration
```bash
# Inside Colima VM
$ cat /etc/resolv.conf
nameserver 192.168.106.1    # Points to Mac (which forwards to correct DNS)

# Or with custom DNS (your setup):
nameserver 10.14.0.1        # Arista DNS directly
nameserver 10.128.1.1       # Arista DNS backup
nameserver 8.8.8.8          # Google DNS fallback
search sjc.aristanetworks.com aristanetworks.com arista.io
```

**How DNS Resolution Works:**
1. VM queries `git.sjc.aristanetworks.com`
2. Query goes to 10.14.0.1 (Arista DNS)
3. Packet routed through Mac's VPN tunnel (because 10.14.0.1 is in VPN network)
4. DNS server responds with internal IP (e.g., 10.14.50.100)
5. Response comes back through VPN → Mac → VM

#### Verifying VM Can Reach VPN Resources
```bash
# SSH into Colima VM
$ colima ssh

# Test DNS resolution
$ nslookup git.sjc.aristanetworks.com
Server:         10.14.0.1
Address:        10.14.0.1#53

Name:   git.sjc.aristanetworks.com
Address: 10.14.50.100

# Test connectivity to VPN resource
$ ping -c 3 10.14.50.100
PING 10.14.50.100 (10.14.50.100) 56(84) bytes of data.
64 bytes from 10.14.50.100: icmp_seq=1 ttl=64 time=15.2 ms

# Trace route to see path
$ traceroute 10.14.50.100
 1  192.168.106.1 (192.168.106.1)  0.5 ms    # Mac host
 2  10.14.1.1 (10.14.1.1)  10.2 ms           # VPN gateway
 3  10.14.50.100 (10.14.50.100)  15.1 ms     # Arista server
```

---

### Layer 3: Docker Container Network

#### Network Mode: `host`

Your containers use `--network host` mode:

```bash
docker run -dit \
  --name wifiap \
  --network host \      # <-- This is the key!
  --dns 10.14.0.1 \
  --dns 10.128.1.1 \
  ...
```

**What `--network host` means:**
- Container shares the **VM's network namespace**
- Container sees the same network interfaces as the VM
- Container has the same IP as the VM (192.168.106.2)
- Container uses the same routing table as the VM
- **No network isolation** between container and VM

**Inside the container:**
```bash
$ docker exec -it wifiap bash

# Container sees VM's network interfaces
root@wifiap:/# ip addr
1: lo: <LOOPBACK,UP,LOWER_UP> mtu 65536
    inet 127.0.0.1/8 scope host lo
2: col0: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 1500
    inet 192.168.106.2/24 brd 192.168.106.255 scope global col0

# Container sees VM's routing table
root@wifiap:/# ip route
default via 192.168.106.1 dev col0
192.168.106.0/24 dev col0 proto kernel scope link

# Container's DNS configuration
root@wifiap:/# cat /etc/resolv.conf
nameserver 10.14.0.1
nameserver 10.128.1.1
nameserver 10.128.1.2
nameserver 8.8.8.8
search sjc.aristanetworks.com aristanetworks.com arista.io
```

#### Testing VPN Access from Container
```bash
# Inside wifiap container
$ docker exec -it wifiap bash

# Test DNS resolution
root@wifiap:/# nslookup git.sjc.aristanetworks.com
Server:         10.14.0.1
Address:        10.14.0.1#53

Name:   git.sjc.aristanetworks.com
Address: 10.14.50.100

# Test HTTP access to internal resource
root@wifiap:/# curl -I https://git.sjc.aristanetworks.com
HTTP/2 200
server: nginx
...

# Test SSH to internal server
root@wifiap:/# ssh user@10.14.100.50
# Should work if VPN is connected!
```

---

## Network Modes in Docker

### Comparison of Docker Network Modes



| Network Mode | Container IP | VPN Access | Use Case | Isolation |
|--------------|-------------|------------|----------|-----------|
| **host** | Same as VM (192.168.106.2) | ✅ Yes (via VM) | Your setup - needs VPN access | None - shares VM network |
| **bridge** | Private (172.17.0.x) | ✅ Yes (via NAT) | Default mode, isolated containers | Network isolated, NAT'd |
| **none** | No network | ❌ No | Testing, security | Complete isolation |
| **container:X** | Same as container X | Depends on X | Sidecar patterns | Shares with another container |

#### Mode 1: Host Network (Your Setup)

**Configuration:**
```bash
docker run --network host myimage
```

**Network Stack:**
```
Container process → VM network namespace → VM routing → Mac → VPN
```

**Advantages for VPN access:**
- ✅ Direct access to all VM network interfaces
- ✅ No NAT overhead
- ✅ Same routing table as VM (inherits VPN routes)
- ✅ Can bind to any port on VM
- ✅ DNS configuration from VM

**Disadvantages:**
- ❌ No network isolation between containers
- ❌ Port conflicts between containers
- ❌ Less secure (container can see all VM network traffic)

#### Mode 2: Bridge Network (Default Docker)

**Configuration:**
```bash
docker run myimage  # Uses bridge by default
# Or explicitly:
docker run --network bridge myimage
```

**Network Stack:**
```
Container (172.17.0.2) → Docker bridge (docker0) → VM → Mac → VPN
```

**How VPN access works:**
```bash
# Inside Colima VM
$ ip addr show docker0
docker0: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 1500
    inet 172.17.0.1/16 brd 172.17.255.255 scope global docker0

# Container routing
$ docker exec mycontainer ip route
default via 172.17.0.1 dev eth0          # Docker bridge
172.17.0.0/16 dev eth0 scope link        # Container network
```

**Traffic flow to VPN resource:**
1. Container (172.17.0.2) sends packet to 10.14.50.100
2. Packet goes to default gateway (172.17.0.1 - docker0 bridge)
3. VM NATs packet: source becomes 192.168.106.2
4. VM routes to Mac (192.168.106.1)
5. Mac routes via VPN (utun3)

**Advantages:**
- ✅ Network isolation between containers
- ✅ Still has VPN access (via NAT)
- ✅ No port conflicts
- ✅ More secure

**Disadvantages:**
- ❌ Extra NAT layer (slight performance overhead)
- ❌ Need to publish ports (-p) for external access

#### Mode 3: Custom Bridge Network

**Configuration:**
```bash
docker network create mynetwork
docker run --network mynetwork myimage
```

**Advantages over default bridge:**
- ✅ Automatic DNS resolution between containers
- ✅ Better isolation
- ✅ Custom subnet configuration
- ✅ Still has VPN access

---

## Docker Compose and VPN Access

### How Docker Compose Handles Networking

When you use `docker-compose`, it automatically creates a custom bridge network for your services.

#### Example docker-compose.yml

```yaml
version: '3.8'

services:
  web:
    image: nginx
    ports:
      - "8080:80"
    # Uses default bridge network created by compose

  app:
    image: myapp
    environment:
      - API_URL=https://api.sjc.aristanetworks.com  # VPN resource
    # Can access VPN resources!

  database:
    image: postgres
    # All services can communicate by service name
```

**Network created by compose:**
```bash
$ docker network ls
NETWORK ID     NAME                    DRIVER    SCOPE
abc123def456   myproject_default       bridge    local
```

**How VPN access works in compose:**
```
Service container → Compose network → Docker bridge → VM → Mac → VPN
```

#### Using Host Network in Docker Compose

```yaml
version: '3.8'

services:
  vpn-client:
    image: myimage
    network_mode: "host"  # Uses host network (VM's network)
    dns:
      - 10.14.0.1
      - 10.128.1.1
    dns_search:
      - sjc.aristanetworks.com
      - aristanetworks.com
```

**This is equivalent to your `docker run --network host` setup!**

---

## Troubleshooting VPN Connectivity

### Problem 1: Container Cannot Resolve Internal Hostnames

**Symptom:**
```bash
$ docker exec mycontainer nslookup git.sjc.aristanetworks.com
;; connection timed out; no servers could be reached
```

**Diagnosis:**
```bash
# Check container's DNS configuration
$ docker exec mycontainer cat /etc/resolv.conf
nameserver 192.168.106.1  # Wrong! Should be Arista DNS

# Check if DNS server is reachable
$ docker exec mycontainer ping 10.14.0.1
ping: connect: Network is unreachable  # VPN not accessible
```

**Solution:**
```bash
# Option 1: Specify DNS servers when creating container
docker run --dns 10.14.0.1 --dns 10.128.1.1 \
  --dns-search sjc.aristanetworks.com \
  myimage

# Option 2: Configure in docker-compose.yml
services:
  myapp:
    dns:
      - 10.14.0.1
      - 10.128.1.1
    dns_search:
      - sjc.aristanetworks.com

# Option 3: Configure Colima's DNS (affects all containers)
# Edit ~/.colima/default/colima.yaml
dns:
  - 10.14.0.1
  - 10.128.1.1
```

### Problem 2: VPN Connected on Mac, But Container Can't Access

**Symptom:**
```bash
# On Mac - VPN works
$ ping 10.14.50.100
PING 10.14.50.100: 56 data bytes
64 bytes from 10.14.50.100: icmp_seq=0 ttl=64 time=12.3 ms

# In container - doesn't work
$ docker exec mycontainer ping 10.14.50.100
ping: connect: Network is unreachable
```

**Diagnosis Steps:**

**Step 1: Check Colima VM can reach VPN**
```bash
$ colima ssh

# Inside VM
$ ping 10.14.50.100
# If this fails, VM doesn't have VPN access
```

**Step 2: Check VM routing**
```bash
$ colima ssh
$ ip route
default via 192.168.106.1 dev col0  # Should route to Mac
```

**Step 3: Check Mac is forwarding traffic**
```bash
# On Mac
$ sysctl net.inet.ip.forwarding
net.inet.ip.forwarding: 1  # Should be 1 (enabled)

# If not enabled:
$ sudo sysctl -w net.inet.ip.forwarding=1
```

**Step 4: Check firewall on Mac**
```bash
# Check if Mac firewall is blocking
$ sudo pfctl -sr | grep -i block

# Temporarily disable to test
$ sudo pfctl -d  # Disable
$ sudo pfctl -e  # Enable
```

**Solution:**
Usually Colima handles this automatically, but if not:
```bash
# Restart Colima with proper network configuration
colima stop
colima start --network-address  # Enables reachable IP
```

### Problem 3: DNS Works, But Connection Times Out

**Symptom:**
```bash
$ docker exec mycontainer nslookup git.sjc.aristanetworks.com
Name:   git.sjc.aristanetworks.com
Address: 10.14.50.100  # DNS works!

$ docker exec mycontainer curl https://git.sjc.aristanetworks.com
curl: (28) Failed to connect to git.sjc.aristanetworks.com port 443: Connection timed out
```

**Diagnosis:**
```bash
# Check routing from container
$ docker exec mycontainer ip route
default via 172.17.0.1 dev eth0  # Goes to Docker bridge

# Check if packets are leaving container
$ docker exec mycontainer traceroute 10.14.50.100
 1  172.17.0.1 (172.17.0.1)  0.3 ms
 2  * * *  # Stops here - routing issue
```

**Possible causes:**
1. **VPN split-tunnel not including the subnet**
   - Check Mac's routing table for VPN routes
   - VPN might not route 10.14.0.0/16

2. **Firewall blocking container traffic**
   - Arista VPN might have firewall rules
   - Try from Mac directly to confirm

3. **MTU issues with VPN tunnel**
   ```bash
   # Check MTU
   $ docker exec mycontainer ip link show eth0
   eth0: mtu 1500

   # VPN tunnel usually has lower MTU (1400)
   # Try reducing container MTU
   $ docker network create --opt com.docker.network.driver.mtu=1400 lowmtu
   $ docker run --network lowmtu myimage
   ```

### Problem 4: Works Sometimes, Fails Other Times

**Symptom:**
Intermittent connectivity to VPN resources from containers.

**Common causes:**

1. **VPN disconnects/reconnects**
   ```bash
   # Check VPN status on Mac
   $ ifconfig | grep utun
   utun3: flags=8051<UP,POINTOPOINT,RUNNING,MULTICAST>  # VPN up

   # If no utun interface, VPN is down
   ```

2. **DNS caching in container**
   ```bash
   # Container might cache old DNS results
   # Restart container to clear
   $ docker restart mycontainer
   ```

3. **Colima VM network reset**
   ```bash
   # Colima VM might lose routes after sleep/wake
   $ colima restart
   ```

**Solution: Health check script**
```bash
#!/bin/bash
# Add to container or run periodically

# Test VPN connectivity
if ! ping -c 1 -W 2 10.14.0.1 &>/dev/null; then
    echo "VPN DNS unreachable - check VPN connection"
    exit 1
fi

if ! curl -s --max-time 5 https://git.sjc.aristanetworks.com &>/dev/null; then
    echo "Cannot reach internal resources"
    exit 1
fi

echo "VPN connectivity OK"
```

---

## Practical Examples

### Example 1: Accessing Arista Git from Container

```bash
# Your wifiap container with host networking
$ docker exec -it wifiap bash

# Clone from internal Git
root@wifiap:/# git clone https://git.sjc.aristanetworks.com/repo.git
Cloning into 'repo'...
# Works because:
# 1. DNS resolves git.sjc.aristanetworks.com via 10.14.0.1 (Arista DNS)
# 2. Connection to 10.14.50.100:443 routes through VM → Mac → VPN
# 3. SSH keys mounted from Mac (/root/.ssh) work for authentication
```

### Example 2: Accessing Internal API

```bash
# Inside container
root@wifiap:/# curl https://api.sjc.aristanetworks.com/v1/status
{"status": "ok", "region": "sjc"}

# Traffic flow:
# Container → VM (192.168.106.2) → Mac (192.168.1.100) →
# VPN (utun3) → Arista Network → API Server
```

### Example 3: Docker Compose with VPN Access

```yaml
# docker-compose.yml
version: '3.8'

services:
  dev-environment:
    image: barney-docker:latest
    network_mode: "host"  # Use host network for VPN access
    dns:
      - 10.14.0.1
      - 10.128.1.1
    dns_search:
      - sjc.aristanetworks.com
      - aristanetworks.com
    volumes:
      - ~/.ssh:/root/.ssh:ro
      - ./workspace:/workspace
    environment:
      - ARISTA_API=https://api.sjc.aristanetworks.com
    command: /bin/bash
    stdin_open: true
    tty: true
```

**Start and use:**
```bash
$ docker-compose up -d
$ docker-compose exec dev-environment bash

# Inside container - full VPN access
root@dev:/# ping 10.14.0.1
root@dev:/# curl https://git.sjc.aristanetworks.com
root@dev:/# ssh user@10.14.100.50
```

---

## Summary

### Key Takeaways

1. **VPN runs on Mac, not in VM or containers**
   - Mac's VPN client creates tunnel interface (utun3)
   - Mac's routing table directs Arista traffic through VPN

2. **Colima VM inherits Mac's network access**
   - VM uses Mac as gateway (NAT mode)
   - All VM traffic goes through Mac
   - Mac's VPN routes apply to VM traffic

3. **Containers inherit VM's network access**
   - With `--network host`: direct access to VM network
   - With `bridge` mode: NAT'd through VM, then Mac
   - Both modes can access VPN resources!

4. **DNS is critical**
   - Containers need Arista DNS servers (10.14.0.1, 10.128.1.1)
   - DNS servers are only reachable via VPN
   - Use `--dns` flag or configure in Colima

5. **The complete path:**
   ```
   Container → Colima VM → Mac Host → VPN Tunnel → Arista Network
   ```

### Why It Works

- **Routing**: Mac's routing table has VPN routes that apply to all traffic from VM
- **NAT**: Colima VM's traffic is NAT'd to appear from Mac's IP
- **DNS**: Containers use Arista DNS servers accessible via VPN
- **No special configuration needed**: Standard Docker networking works!

### When It Doesn't Work

- VPN disconnected on Mac
- DNS not configured in container
- Firewall blocking traffic
- MTU mismatch
- Split-tunnel VPN not including required subnets

---

## Additional Resources

- **Colima Documentation**: https://github.com/abiosoft/colima
- **Docker Networking**: https://docs.docker.com/network/
- **Your Migration Guide**: `~/docs/docker-guides/docker-desktop-to-colima-migration.md`
- **Container Commands**: `~/docs/docker-guides/container-recreation-commands.sh`

---

**Last Updated:** March 24, 2026
**Author:** Generated for Ajay Kumar's development environment

