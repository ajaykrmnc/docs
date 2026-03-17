# Network Configuration

> Setting up secure, reliable communication between all nodes in the distributed network.

**Previous:** [Device Prerequisites](./device-prerequisites.md) | **Next:** [RPi Setup](./rpi-setup.md)

---

## Network Topology

```
                    ┌─────────────────────────────────────┐
                    │           HOME NETWORK              │
                    │         (192.168.1.0/24)            │
                    └─────────────────────────────────────┘
                                     │
            ┌────────────────────────┼────────────────────────┐
            │                        │                        │
            ▼                        ▼                        ▼
    ┌───────────────┐       ┌───────────────┐       ┌───────────────┐
    │ Office Laptop │       │Personal Laptop│       │  Raspberry Pi │
    │ 192.168.1.101 │       │ 192.168.1.102 │       │ 192.168.1.100 │
    │   Port: 8001  │       │   Port: 8002  │       │   Port: 8000  │
    │   (Dynamic)   │       │   (Dynamic)   │       │   (Static)    │
    └───────────────┘       └───────────────┘       └───────────────┘
```

---

## Static IP for Raspberry Pi

The RPi should have a static IP as it's the primary data node.

### Method 1: dhcpcd.conf (Recommended)

```bash
# On RPi
sudo nano /etc/dhcpcd.conf

# Add at the end:
interface eth0
static ip_address=192.168.1.100/24
static routers=192.168.1.1
static domain_name_servers=192.168.1.1 8.8.8.8

# For WiFi, use wlan0 instead of eth0
```

### Method 2: Router DHCP Reservation

1. Access router admin (usually 192.168.1.1)
2. Find DHCP settings
3. Add reservation for RPi's MAC address → 192.168.1.100

---

## mDNS/Avahi Setup (Local DNS)

Enable `.local` hostname resolution for easier access.

### Raspberry Pi

```bash
# Install avahi
sudo apt install avahi-daemon

# Enable and start
sudo systemctl enable avahi-daemon
sudo systemctl start avahi-daemon

# Set hostname
sudo hostnamectl set-hostname rpi-sync

# Now accessible as: rpi-sync.local
```

### macOS

mDNS works out of the box. Test with:

```bash
ping rpi-sync.local
```

### Hosts File Backup

Add to `/etc/hosts` on all devices as fallback:

```
192.168.1.100   rpi-sync rpi-sync.local
192.168.1.101   office-laptop office-laptop.local
192.168.1.102   personal-laptop personal-laptop.local
```

---

## Firewall Configuration

### Raspberry Pi (ufw)

```bash
# Install ufw
sudo apt install ufw

# Default policies
sudo ufw default deny incoming
sudo ufw default allow outgoing

# Allow SSH
sudo ufw allow 22/tcp

# Allow nginx
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp

# Allow sync service ports (custom range)
sudo ufw allow 8000:8010/tcp

# Allow Syncthing
sudo ufw allow 22000/tcp
sudo ufw allow 21027/udp

# Enable firewall
sudo ufw enable
sudo ufw status verbose
```

### macOS Firewall

```bash
# Check status
sudo /usr/libexec/ApplicationFirewall/socketfilterfw --getglobalstate

# Allow specific apps through System Preferences > Security > Firewall
```

---

## Port Allocation

| Port | Service | Node | Description |
|------|---------|------|-------------|
| 22 | SSH | All | Secure shell access |
| 80 | nginx | RPi | HTTP server |
| 443 | nginx | RPi | HTTPS server |
| 8000 | Sync API | RPi | Main sync coordinator |
| 8001 | Sync API | Office | Worker node API |
| 8002 | Sync API | Personal | Worker node API |
| 6379 | Redis | RPi | Key-value store |
| 2379 | etcd | RPi | Distributed KV (if used) |
| 22000 | Syncthing | All | P2P sync (TCP) |
| 21027 | Syncthing | All | P2P discovery (UDP) |
| 9000 | Raft | All | Consensus protocol |

---

## Network Testing Script

```bash
#!/bin/bash
# save as: test-network.sh

NODES=("rpi-sync.local" "office-laptop.local" "personal-laptop.local")
PORTS=(8000 8001 8002)

echo "=== Network Connectivity Test ==="

for i in "${!NODES[@]}"; do
    node="${NODES[$i]}"
    port="${PORTS[$i]}"
    
    echo ""
    echo "Testing $node..."
    
    # Ping test
    if ping -c 1 -W 2 "$node" &> /dev/null; then
        echo "  ✅ Ping: OK"
    else
        echo "  ❌ Ping: FAILED"
    fi
    
    # SSH test
    if nc -z -w 2 "$node" 22 &> /dev/null; then
        echo "  ✅ SSH (22): OK"
    else
        echo "  ❌ SSH (22): FAILED"
    fi
    
    # Service port test
    if nc -z -w 2 "$node" "$port" &> /dev/null; then
        echo "  ✅ Service ($port): OK"
    else
        echo "  ⚠️  Service ($port): Not listening (expected before setup)"
    fi
done

echo ""
echo "=== Test Complete ==="
```

---

## Bandwidth Testing

Test network speed between nodes:

```bash
# On RPi (server)
iperf3 -s

# On laptops (clients)
iperf3 -c rpi-sync.local

# Expected: 100+ Mbps for gigabit ethernet, 50+ Mbps for good WiFi
```

---

**Next:** [Raspberry Pi Setup →](./rpi-setup.md)

