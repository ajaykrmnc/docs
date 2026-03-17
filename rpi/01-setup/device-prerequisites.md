# Device Prerequisites

> Complete software and configuration requirements for all devices in the distributed network.

**Previous:** [README](../README.md) | **Next:** [Network Configuration](./network-configuration.md)

---

## Device Inventory

| Device | Role | OS | Primary Function |
|--------|------|----|--------------------|
| Office Laptop | Node A (Worker) | macOS/Linux | Development, testing |
| Personal Laptop | Node B (Worker) | macOS/Linux | Development, testing |
| Raspberry Pi | Node C (Leader) | Raspberry Pi OS | Data storage, coordination |

---

## Common Requirements (All Devices)

### Programming Languages

```bash
# Python 3.9+ (for prototyping)
python3 --version

# Go 1.21+ (recommended for distributed systems)
go version

# Node.js 18+ (optional, for web interfaces)
node --version
```

### Essential Tools

```bash
# Git for version control
git --version

# SSH for secure communication
ssh -V

# rsync for file synchronization
rsync --version

# curl/wget for HTTP testing
curl --version
```

### Network Utilities

```bash
# netcat for TCP/UDP testing
nc -h

# nmap for network discovery (optional)
nmap --version

# iperf3 for bandwidth testing
iperf3 --version
```

---

## macOS Specific (Office & Personal Laptop)

### Install Homebrew (if not present)

```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```

### Required Packages

```bash
# Core tools
brew install go python@3.11 node
brew install rsync fswatch
brew install protobuf grpc

# Distributed systems tools
brew install etcd redis
brew install syncthing

# Development tools
brew install tmux htop jq
```

### File System Watching

```bash
# fswatch for file change detection
brew install fswatch

# Test it works
fswatch -o ~/test-folder | head -5
```

---

## Linux Specific (if using Linux laptops)

```bash
# Ubuntu/Debian
sudo apt update
sudo apt install -y golang python3 python3-pip nodejs npm
sudo apt install -y rsync inotify-tools
sudo apt install -y protobuf-compiler
sudo apt install -y etcd redis-server
sudo apt install -y syncthing
sudo apt install -y tmux htop jq netcat-openbsd

# Fedora/RHEL
sudo dnf install golang python3 nodejs
sudo dnf install rsync inotify-tools
```

---

## Raspberry Pi Specific

See detailed setup: [Raspberry Pi Setup](./rpi-setup.md)

### Quick Prerequisites

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install core tools
sudo apt install -y golang python3 python3-pip
sudo apt install -y rsync nginx
sudo apt install -y protobuf-compiler
sudo apt install -y redis-server
sudo apt install -y syncthing
sudo apt install -y tmux htop jq

# Enable SSD (see rpi-setup.md for details)
```

---

## Verification Script

Create this script on each device to verify setup:

```bash
#!/bin/bash
# save as: verify-setup.sh

echo "=== Distributed Lab Setup Verification ==="
echo ""

check_cmd() {
    if command -v $1 &> /dev/null; then
        echo "✅ $1: $(command -v $1)"
    else
        echo "❌ $1: NOT FOUND"
    fi
}

echo "Languages:"
check_cmd python3
check_cmd go
check_cmd node

echo ""
echo "Tools:"
check_cmd git
check_cmd ssh
check_cmd rsync
check_cmd curl

echo ""
echo "Network:"
check_cmd nc
check_cmd iperf3

echo ""
echo "Distributed Systems:"
check_cmd etcd
check_cmd redis-cli
check_cmd syncthing

echo ""
echo "=== Verification Complete ==="
```

Run with: `chmod +x verify-setup.sh && ./verify-setup.sh`

---

## SSH Key Setup

Generate and distribute SSH keys for passwordless access:

```bash
# Generate key (on each device)
ssh-keygen -t ed25519 -C "distributed-lab"

# Copy to RPi (from laptops)
ssh-copy-id pi@rpi.local

# Copy between laptops as needed
ssh-copy-id user@office-laptop.local
ssh-copy-id user@personal-laptop.local
```

---

## Directory Structure

Create consistent directory structure on all devices:

```bash
mkdir -p ~/distributed-lab/{data,logs,config,src}
mkdir -p ~/distributed-lab/src/{raft,crdt,sync}
```

---

**Next:** [Network Configuration →](./network-configuration.md)

