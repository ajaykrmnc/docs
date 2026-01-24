# Complete Guide to dynv6 Dynamic DNS Setup

## A Comprehensive Guide for Raspberry Pi Home Server

**Author:** Auto-generated Guide  
**Last Updated:** January 2026  
**Version:** 1.0

---

## Table of Contents

1. [Introduction](#1-introduction)
2. [Understanding Dynamic DNS](#2-understanding-dynamic-dns)
3. [Why dynv6?](#3-why-dynv6)
4. [Prerequisites](#4-prerequisites)
5. [Creating a dynv6 Account](#5-creating-a-dynv6-account)
6. [Creating Your First Zone](#6-creating-your-first-zone)
7. [Understanding dynv6 Tokens and Authentication](#7-understanding-dynv6-tokens-and-authentication)
8. [Raspberry Pi Setup](#8-raspberry-pi-setup)
9. [Update Methods](#9-update-methods)
10. [Automation with Cron](#10-automation-with-cron)
11. [Advanced Configuration](#11-advanced-configuration)
12. [Security Best Practices](#12-security-best-practices)
13. [Troubleshooting](#13-troubleshooting)
14. [Monitoring and Logging](#14-monitoring-and-logging)
15. [Using Your Own Domain](#15-using-your-own-domain)
16. [Integration with Services](#16-integration-with-services)
17. [Backup and Recovery](#17-backup-and-recovery)
18. [FAQ](#18-faq)
19. [Appendix](#19-appendix)

---

# 1. Introduction

## 1.1 What This Guide Covers

This comprehensive guide will walk you through setting up dynv6 Dynamic DNS 
service on your Raspberry Pi. By the end of this guide, you will have:

- A permanent hostname that always points to your Raspberry Pi
- Automatic IP address updates when your IP changes
- Secure access to your home server from anywhere in the world
- Knowledge of best practices for maintaining your setup

## 1.2 Who Is This Guide For?

This guide is designed for:

- Home server enthusiasts
- Raspberry Pi hobbyists
- Self-hosting advocates
- Anyone behind CGNAT wanting remote access
- Developers needing remote access to home labs

## 1.3 Time Required

| Task | Estimated Time |
|------|----------------|
| Account creation | 5 minutes |
| Zone setup | 5 minutes |
| Raspberry Pi configuration | 15-30 minutes |
| Testing and verification | 10 minutes |
| **Total** | **35-50 minutes** |

## 1.4 Difficulty Level

**Beginner to Intermediate**

Basic familiarity with:
- Linux command line
- SSH access to Raspberry Pi
- Text editing (nano, vim, etc.)

---

# 2. Understanding Dynamic DNS

## 2.1 What is DNS?

DNS (Domain Name System) is the internet's phone book. It translates 
human-readable domain names into IP addresses that computers use.

```
Example:
google.com  →  142.250.190.14
github.com  →  140.82.121.4
```

## 2.2 The Problem with Dynamic IPs

Most home internet connections have **dynamic IP addresses**. This means:

```
Monday:    Your IP = 2401:4900:8f56:85f8:ba27:ebff:fed2:832d
Tuesday:   Your IP = 2401:4900:8f56:85f8:1234:5678:abcd:ef01  (changed!)
Wednesday: Your IP = 2401:4900:8f56:85f8:9999:8888:7777:6666  (changed again!)
```

This creates a problem: **How do you connect to your home server if the 
address keeps changing?**

## 2.3 How Dynamic DNS Solves This

Dynamic DNS (DDNS) provides a **permanent hostname** that automatically 
updates to point to your current IP address.

```
Your hostname: myhomeserver.dynv6.net

Monday:    myhomeserver.dynv6.net → 2401:4900:...:832d
Tuesday:   myhomeserver.dynv6.net → 2401:4900:...:ef01  (auto-updated!)
Wednesday: myhomeserver.dynv6.net → 2401:4900:...:6666  (auto-updated!)
```

## 2.4 How It Works (Technical Overview)

```
┌─────────────────────────────────────────────────────────────────────┐
│                        DYNAMIC DNS FLOW                              │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  1. Your Raspberry Pi detects its current IPv6 address              │
│                           │                                          │
│                           ▼                                          │
│  2. Pi sends update request to dynv6:                               │
│     "Hey dynv6, my hostname is 'mypi.dynv6.net'                     │
│      and my current IP is 2401:4900:...:832d"                       │
│                           │                                          │
│                           ▼                                          │
│  3. dynv6 updates its DNS records:                                  │
│     mypi.dynv6.net  AAAA  2401:4900:...:832d                        │
│                           │                                          │
│                           ▼                                          │
│  4. When someone queries mypi.dynv6.net:                            │
│     DNS returns: 2401:4900:...:832d                                 │
│                           │                                          │
│                           ▼                                          │
│  5. Connection established to your Pi!                              │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

## 2.5 IPv4 vs IPv6 Dynamic DNS

### IPv4 Challenges

```
┌─────────────────────────────────────────────────────────────────────┐
│                         IPv4 SITUATION                               │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  Internet ──→ ISP's CGNAT ──→ Your Router ──→ Your Pi               │
│                   │                                                  │
│                   └── Multiple customers share ONE public IP         │
│                       (You can't receive incoming connections!)      │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

### IPv6 Advantage

```
┌─────────────────────────────────────────────────────────────────────┐
│                         IPv6 SITUATION                               │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  Internet ──→ Your Router ──→ Your Pi                               │
│                                  │                                   │
│                                  └── Your Pi has a GLOBAL IPv6!      │
│                                      (Direct connection possible!)   │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

This is why dynv6 focuses on IPv6 - it solves the CGNAT problem!

---

# 3. Why dynv6?

## 3.1 Comparison with Other DDNS Providers

| Feature | dynv6 | No-IP | DuckDNS | Dynu | Cloudflare |
|---------|-------|-------|---------|------|------------|
| **Free tier** | ✅ Unlimited | ⚠️ 3 hosts | ✅ 5 hosts | ✅ 4 hosts | ✅ Unlimited |
| **IPv6 support** | ✅ Excellent | ⚠️ Limited | ✅ Yes | ✅ Yes | ✅ Yes |
| **Custom domain** | ✅ Free | ❌ Paid | ❌ No | ✅ Free | ✅ Yes |
| **API options** | ✅ Many | ⚠️ Basic | ✅ Simple | ✅ Good | ✅ Extensive |
| **No renewal needed** | ✅ Yes | ❌ 30 days | ✅ Yes | ❌ 30 days | ✅ Yes |
| **GDPR compliant** | ✅ German | ⚠️ USA | ⚠️ USA | ⚠️ USA | ⚠️ USA |

## 3.2 dynv6 Advantages

### 3.2.1 Multiple Update Methods

dynv6 offers various ways to update your IP:

1. **REST API** - Simple HTTP requests
2. **Update API** - Legacy compatible
3. **DynDNS API** - Works with existing clients
4. **SSH** - Secure updates with public key
5. **DNS (TSIG)** - Standard DNS update protocol

### 3.2.2 Free Custom Domain Support

Unlike many providers, dynv6 allows you to use your own domain for free:

```
Free subdomain:     mypi.dynv6.net
Your own domain:    home.yourdomain.com  (also free!)
```

### 3.2.3 No Annoying Renewals

Many free DDNS providers require you to "confirm" your hostname every 30 days.
dynv6 does NOT require this - set it and forget it!

### 3.2.4 Privacy-Focused

- Based in Germany (strict GDPR laws)
- Minimal data collection
- No tracking or advertising

## 3.3 dynv6 Limitations

Be aware of these limitations:

| Limitation | Details |
|------------|---------|
| No SLA | Free service, no uptime guarantees |
| No DDoS protection | Not suitable for high-traffic sites |
| Community support | No paid support options |
| IPv6 focused | IPv4 support is secondary |

## 3.4 When to Use dynv6

✅ **Good for:**
- Home servers
- Personal projects
- Development/testing
- IoT devices
- Remote access to home network

❌ **Not recommended for:**
- Production business services
- High-availability requirements
- Services requiring DDoS protection

---

# 4. Prerequisites

## 4.1 Hardware Requirements

### Raspberry Pi

| Component | Minimum | Recommended |
|-----------|---------|-------------|
| Model | Any Pi with networking | Pi 3B+ or newer |
| Storage | 8GB SD card | 32GB+ SD card |
| Network | WiFi or Ethernet | Ethernet preferred |
| Power | Official power supply | Official power supply |

### Network

| Requirement | Details |
|-------------|---------|
| Internet connection | Active broadband |
| IPv6 support | Must be enabled by ISP |
| Router access | For firewall configuration |

## 4.2 Software Requirements

### On Raspberry Pi

```bash
# Required packages
curl        # For HTTP requests
bash        # Shell scripting
cron        # Task scheduling (usually pre-installed)

# Optional but recommended
jq          # JSON parsing
dig         # DNS testing
ssh         # Remote access
ufw         # Firewall management
```

### Installation Commands

```bash
# Update package list
sudo apt update

# Install required packages
sudo apt install -y curl

# Install optional packages
sudo apt install -y jq dnsutils ufw
```

## 4.3 Network Requirements

### Verify IPv6 Support

Run these commands on your Raspberry Pi:

```bash
# Check if you have a global IPv6 address
ip -6 addr show scope global

# Expected output should include something like:
# inet6 2401:4900:xxxx:xxxx:xxxx:xxxx:xxxx:xxxx/64 scope global
```

### Test IPv6 Connectivity

```bash
# Ping Google's IPv6 DNS
ping6 -c 4 2001:4860:4860::8888

# Or ping Google by hostname
ping6 -c 4 google.com

# Get your public IPv6
curl -s -6 https://ipv6.icanhazip.com
```

### Expected Output

```
PING 2001:4860:4860::8888(2001:4860:4860::8888) 56 data bytes
64 bytes from 2001:4860:4860::8888: icmp_seq=1 ttl=118 time=12.3 ms
64 bytes from 2001:4860:4860::8888: icmp_seq=2 ttl=118 time=11.8 ms
64 bytes from 2001:4860:4860::8888: icmp_seq=3 ttl=118 time=12.1 ms
64 bytes from 2001:4860:4860::8888: icmp_seq=4 ttl=118 time=11.9 ms

--- 2001:4860:4860::8888 ping statistics ---
4 packets transmitted, 4 received, 0% packet loss, time 3004ms
```

## 4.4 Account Requirements

| Item | Details |
|------|---------|
| Email address | Valid email for account creation |
| Password | Strong password (12+ characters recommended) |

---

# 5. Creating a dynv6 Account

## 5.1 Step-by-Step Account Creation

### Step 1: Visit dynv6.com

Open your web browser and navigate to:

```
https://dynv6.com
```

### Step 2: Click "Sign up"

Look for the "Sign up" link in the top navigation bar.

### Step 3: Fill in Registration Form

```
┌─────────────────────────────────────────────────────────────────────┐
│                      CREATE YOUR ACCOUNT                             │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  Email:     [your.email@example.com                    ]            │
│                                                                      │
│  Password:  [••••••••••••••••                          ]            │
│                                                                      │
│  Confirm:   [••••••••••••••••                          ]            │
│                                                                      │
│             [  Create Account  ]                                     │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

### Step 4: Verify Your Email

1. Check your inbox for verification email
2. Click the verification link
3. Your account is now active!

## 5.2 Account Security Recommendations

### Strong Password Guidelines

```
Good password:  Tr0ub4dor&3#Horse!Battery
Bad password:   password123

Requirements:
✅ At least 12 characters
✅ Mix of uppercase and lowercase
✅ Include numbers
✅ Include special characters
✅ Not a dictionary word
```

### Enable Two-Factor Authentication (if available)

Check your account settings for 2FA options.

## 5.3 Account Dashboard Overview

After logging in, you'll see:

```
┌─────────────────────────────────────────────────────────────────────┐
│  dynv6 Dashboard                                    [Account] [Logout]│
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐                  │
│  │  My Zones   │  │ My Domains  │  │    Keys     │                  │
│  │             │  │             │  │             │                  │
│  │  Manage     │  │  Custom     │  │  API tokens │                  │
│  │  hostnames  │  │  domains    │  │  SSH keys   │                  │
│  └─────────────┘  └─────────────┘  └─────────────┘                  │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

---

# 6. Creating Your First Zone

## 6.1 What is a Zone?

A "zone" in dynv6 is your hostname configuration. It includes:

- Your chosen hostname (e.g., `mypi.dynv6.net`)
- Associated IP addresses (IPv4 and/or IPv6)
- Additional DNS records (optional)

## 6.2 Creating a Zone

### Step 1: Navigate to "My Zones"

Click on "My Zones" in the dashboard.

### Step 2: Click "Create Zone"

### Step 3: Choose Your Hostname

```
┌─────────────────────────────────────────────────────────────────────┐
│                        CREATE NEW ZONE                               │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  Hostname: [mypi                    ] . [dynv6.net        ▼]        │
│                                                                      │
│  Available domains:                                                  │
│    • dynv6.net                                                       │
│    • v6.rocks                                                        │
│    • dns.army                                                        │
│    • dns.navy                                                        │
│    • (and more...)                                                   │
│                                                                      │
│                        [  Create Zone  ]                             │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

### Hostname Naming Tips

```
Good hostnames:
✅ mypi
✅ homeserver
✅ ajay-home
✅ rpi4-lab

Avoid:
❌ my pi (no spaces)
❌ my.pi (no dots in hostname part)
❌ test (too generic, might be taken)
```

## 6.3 Zone Configuration Options

After creating your zone, you can configure:

### IPv6 Address (AAAA Record)

```
Record Type: AAAA
Value:       2401:4900:8f56:85f8:ba27:ebff:fed2:832d
TTL:         300 (5 minutes)
```

### IPv4 Address (A Record) - Optional

```
Record Type: A
Value:       192.168.1.100 (or your public IPv4 if available)
TTL:         300
```

### Additional Records

You can also add:
- **MX records** - For email
- **TXT records** - For verification
- **CNAME records** - For aliases
- **SRV records** - For services

## 6.4 Understanding TTL (Time To Live)

TTL determines how long DNS resolvers cache your record:

| TTL Value | Meaning | Use Case |
|-----------|---------|----------|
| 60 | 1 minute | Frequently changing IP |
| 300 | 5 minutes | Default, good balance |
| 3600 | 1 hour | Stable IP |
| 86400 | 1 day | Very stable IP |

**Recommendation:** Start with 300 (5 minutes) for dynamic DNS.

---

# 7. Understanding dynv6 Tokens and Authentication

## 7.1 Authentication Methods Overview

dynv6 supports multiple authentication methods:

| Method | Security | Ease of Use | Best For |
|--------|----------|-------------|----------|
| HTTP Token | Medium | Easy | Simple scripts |
| Zone Token | Medium | Easy | Per-zone access |
| SSH Key | High | Medium | Secure updates |
| TSIG Key | High | Complex | DNS protocol updates |

## 7.2 Creating an HTTP Token

### Step 1: Navigate to Keys

In your dynv6 dashboard, click on "Keys" or navigate to:
```
https://dynv6.com/keys
```

### Step 2: Create New Token

```
┌─────────────────────────────────────────────────────────────────────┐
│                        CREATE HTTP TOKEN                             │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  Token Name: [Raspberry Pi Update Token              ]              │
│                                                                      │
│  Permissions:                                                        │
│    [✓] Update zones                                                  │
│    [ ] Create zones                                                  │
│    [ ] Delete zones                                                  │
│                                                                      │
│                        [  Create Token  ]                            │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

### Step 3: Save Your Token

**IMPORTANT:** The token is only shown once! Save it securely.

```
Your new token: aBcDeFgHiJkLmNoPqRsTuVwXyZ123456

⚠️  Copy this token now! It won't be shown again.
```

## 7.3 Zone-Specific Tokens

Each zone can have its own token for more granular control:

### Finding Zone Token

1. Go to "My Zones"
2. Click on your zone
3. Look for "Zone Token" or "Update Token"

### Zone Token vs HTTP Token

| Feature | Zone Token | HTTP Token |
|---------|------------|------------|
| Scope | Single zone | All zones |
| Security | More secure | Less secure |
| Management | Per-zone | Global |
| Recommended | ✅ Yes | For multiple zones |

## 7.4 SSH Key Authentication

For maximum security, use SSH keys:

### Generate SSH Key on Raspberry Pi

```bash
# Generate a new SSH key pair
ssh-keygen -t ed25519 -f ~/.ssh/dynv6_key -N ""

# View your public key
cat ~/.ssh/dynv6_key.pub
```

### Output Example

```
ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIBxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx pi@raspberrypi
```

### Add Key to dynv6

1. Go to "Keys" in dynv6 dashboard
2. Click "Add SSH Key"
3. Paste your public key
4. Save

### Update via SSH

```bash
# Update your zone via SSH
ssh -i ~/.ssh/dynv6_key api@dynv6.com update mypi.dynv6.net
```

## 7.5 Token Security Best Practices

### DO:

```
✅ Store tokens in environment variables
✅ Use zone-specific tokens when possible
✅ Rotate tokens periodically
✅ Use SSH keys for highest security
✅ Set restrictive file permissions
```

### DON'T:

```
❌ Commit tokens to Git repositories
❌ Share tokens publicly
❌ Use the same token for multiple purposes
❌ Store tokens in plain text files with open permissions
```

### Secure Token Storage

```bash
# Create a secure directory
mkdir -p ~/.config/dynv6
chmod 700 ~/.config/dynv6

# Store token securely
echo "YOUR_TOKEN_HERE" > ~/.config/dynv6/token
chmod 600 ~/.config/dynv6/token

# Read token in scripts
TOKEN=$(cat ~/.config/dynv6/token)
```

---

# 8. Raspberry Pi Setup

## 8.1 Initial Pi Configuration

### Connect to Your Pi

```bash
# SSH into your Raspberry Pi
ssh pi@raspberrypi.local
# or
ssh pi@192.168.1.x
```

### Update System

```bash
# Update package lists
sudo apt update

# Upgrade installed packages
sudo apt upgrade -y

# Install required packages
sudo apt install -y curl jq dnsutils
```

## 8.2 Verify Network Configuration

### Check IPv6 Address

```bash
# Show all IPv6 addresses
ip -6 addr show

# Show only global (public) IPv6
ip -6 addr show scope global
```

### Expected Output

```
3: wlan0: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 1500 state UP qlen 1000
    inet6 2401:4900:8f56:85f8:ba27:ebff:fed2:832d/64 scope global dynamic
       valid_lft 86134sec preferred_lft 86134sec
```

### Get Current Public IPv6

```bash
# Method 1: Using icanhazip
curl -s -6 https://ipv6.icanhazip.com

# Method 2: Using ifconfig.co
curl -s -6 https://ifconfig.co

# Method 3: Using ipify
curl -s -6 https://api6.ipify.org
```

## 8.3 Create Update Script Directory

```bash
# Create directory for dynv6 scripts
mkdir -p ~/dynv6
cd ~/dynv6

# Create logs directory
mkdir -p ~/dynv6/logs
```

## 8.4 Store Your Token Securely

```bash
# Create config directory
mkdir -p ~/.config/dynv6
chmod 700 ~/.config/dynv6

# Store your token (replace with your actual token)
echo "YOUR_DYNV6_TOKEN_HERE" > ~/.config/dynv6/token
chmod 600 ~/.config/dynv6/token

# Store your hostname
echo "mypi.dynv6.net" > ~/.config/dynv6/hostname
chmod 600 ~/.config/dynv6/hostname

# Verify permissions
ls -la ~/.config/dynv6/
```

### Expected Output

```
total 16
drwx------ 2 pi pi 4096 Jan 29 10:00 .
drwxr-xr-x 3 pi pi 4096 Jan 29 10:00 ..
-rw------- 1 pi pi   33 Jan 29 10:00 token
-rw------- 1 pi pi   16 Jan 29 10:00 hostname
```

## 8.5 Create the Update Script

### Basic Update Script

```bash
# Create the update script
nano ~/dynv6/update.sh
```

### Script Content

```bash
#!/bin/bash
#
# dynv6 Update Script for Raspberry Pi
# Updates your dynv6 hostname with current IPv6 address
#
# Author: Your Name
# Version: 1.0
# Last Updated: January 2026

# ============================================================
# CONFIGURATION
# ============================================================

# Read configuration from secure files
CONFIG_DIR="$HOME/.config/dynv6"
TOKEN=$(cat "$CONFIG_DIR/token" 2>/dev/null)
HOSTNAME=$(cat "$CONFIG_DIR/hostname" 2>/dev/null)

# Log file location
LOG_DIR="$HOME/dynv6/logs"
LOG_FILE="$LOG_DIR/update.log"

# Maximum log file size (in bytes) - 1MB
MAX_LOG_SIZE=1048576

# ============================================================
# FUNCTIONS
# ============================================================

# Logging function
log() {
    local level="$1"
    local message="$2"
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    echo "[$timestamp] [$level] $message" >> "$LOG_FILE"

    # Also print to stdout if running interactively
    if [ -t 1 ]; then
        echo "[$timestamp] [$level] $message"
    fi
}

# Rotate log if too large
rotate_log() {
    if [ -f "$LOG_FILE" ]; then
        local size=$(stat -f%z "$LOG_FILE" 2>/dev/null || stat -c%s "$LOG_FILE" 2>/dev/null)
        if [ "$size" -gt "$MAX_LOG_SIZE" ]; then
            mv "$LOG_FILE" "$LOG_FILE.old"
            log "INFO" "Log rotated"
        fi
    fi
}

# Get current IPv6 address
get_ipv6() {
    # Try multiple services for reliability
    local ipv6=""

    # Method 1: icanhazip
    ipv6=$(curl -s -6 --max-time 10 https://ipv6.icanhazip.com 2>/dev/null)

    # Method 2: ifconfig.co (fallback)
    if [ -z "$ipv6" ]; then
        ipv6=$(curl -s -6 --max-time 10 https://ifconfig.co 2>/dev/null)
    fi

    # Method 3: ipify (fallback)
    if [ -z "$ipv6" ]; then
        ipv6=$(curl -s -6 --max-time 10 https://api6.ipify.org 2>/dev/null)
    fi

    echo "$ipv6"
}

# Get current IPv4 address (optional)
get_ipv4() {
    curl -s -4 --max-time 10 https://ipv4.icanhazip.com 2>/dev/null
}

# Update dynv6
update_dynv6() {
    local ipv6="$1"
    local ipv4="$2"

    local url="https://dynv6.com/api/update?hostname=${HOSTNAME}&token=${TOKEN}"

    # Add IPv6 if available
    if [ -n "$ipv6" ]; then
        url="${url}&ipv6=${ipv6}"
    fi

    # Add IPv4 if available
    if [ -n "$ipv4" ]; then
        url="${url}&ipv4=${ipv4}"
    fi

    # Make the update request
    local response=$(curl -s --max-time 30 "$url")
    echo "$response"
}

# ============================================================
# MAIN SCRIPT
# ============================================================

# Ensure log directory exists
mkdir -p "$LOG_DIR"

# Rotate log if needed
rotate_log

log "INFO" "========== Starting dynv6 update =========="

# Validate configuration
if [ -z "$TOKEN" ]; then
    log "ERROR" "Token not found in $CONFIG_DIR/token"
    exit 1
fi

if [ -z "$HOSTNAME" ]; then
    log "ERROR" "Hostname not found in $CONFIG_DIR/hostname"
    exit 1
fi

log "INFO" "Hostname: $HOSTNAME"

# Get current IP addresses
log "INFO" "Fetching current IP addresses..."

IPV6=$(get_ipv6)
IPV4=$(get_ipv4)

if [ -z "$IPV6" ] && [ -z "$IPV4" ]; then
    log "ERROR" "Could not determine any IP address"
    exit 1
fi

log "INFO" "IPv6: ${IPV6:-none}"
log "INFO" "IPv4: ${IPV4:-none}"

# Check if IP has changed (optional optimization)
CACHE_FILE="$CONFIG_DIR/last_ip"
LAST_IP=$(cat "$CACHE_FILE" 2>/dev/null)
CURRENT_IP="${IPV6}|${IPV4}"

if [ "$LAST_IP" = "$CURRENT_IP" ]; then
    log "INFO" "IP unchanged, skipping update"
    exit 0
fi

# Update dynv6
log "INFO" "Updating dynv6..."
RESPONSE=$(update_dynv6 "$IPV6" "$IPV4")

# Check response
if echo "$RESPONSE" | grep -qi "updated\|unchanged"; then
    log "INFO" "Update successful: $RESPONSE"
    # Cache current IP
    echo "$CURRENT_IP" > "$CACHE_FILE"
else
    log "ERROR" "Update failed: $RESPONSE"
    exit 1
fi

log "INFO" "========== Update complete =========="
```

### Make Script Executable

```bash
chmod +x ~/dynv6/update.sh
```

## 8.6 Test the Update Script

### Run Manually

```bash
# Run the script
~/dynv6/update.sh
```

### Expected Output

```
[2026-01-29 10:30:00] [INFO] ========== Starting dynv6 update ==========
[2026-01-29 10:30:00] [INFO] Hostname: mypi.dynv6.net
[2026-01-29 10:30:00] [INFO] Fetching current IP addresses...
[2026-01-29 10:30:01] [INFO] IPv6: 2401:4900:8f56:85f8:ba27:ebff:fed2:832d
[2026-01-29 10:30:01] [INFO] IPv4: none
[2026-01-29 10:30:01] [INFO] Updating dynv6...
[2026-01-29 10:30:02] [INFO] Update successful: addresses updated
[2026-01-29 10:30:02] [INFO] ========== Update complete ==========
```

### Verify Update

```bash
# Check DNS resolution
dig AAAA mypi.dynv6.net +short

# Should return your IPv6 address
# 2401:4900:8f56:85f8:ba27:ebff:fed2:832d
```

---

# 9. Update Methods

## 9.1 REST API Method

The simplest method using HTTP GET requests.

### Basic URL Format

```
https://dynv6.com/api/update?hostname=HOSTNAME&token=TOKEN&ipv6=IPV6
```

### Parameters

| Parameter | Required | Description |
|-----------|----------|-------------|
| hostname | Yes | Your dynv6 hostname |
| token | Yes | Your API token |
| ipv6 | No* | IPv6 address to set |
| ipv4 | No* | IPv4 address to set |
| auto | No | Auto-detect IP from request |

*At least one of ipv6, ipv4, or auto is required.

### Examples

```bash
# Update with specific IPv6
curl "https://dynv6.com/api/update?hostname=mypi.dynv6.net&token=YOUR_TOKEN&ipv6=2401:4900:..."

# Update with auto-detection
curl "https://dynv6.com/api/update?hostname=mypi.dynv6.net&token=YOUR_TOKEN&auto"

# Update both IPv4 and IPv6
curl "https://dynv6.com/api/update?hostname=mypi.dynv6.net&token=YOUR_TOKEN&ipv6=2401:...&ipv4=1.2.3.4"
```

### Response Codes

| Response | Meaning |
|----------|---------|
| `addresses updated` | Success, IP was changed |
| `addresses unchanged` | Success, IP was same |
| `invalid authentication` | Bad token |
| `zone not found` | Hostname doesn't exist |

## 9.2 DynDNS2 Protocol

Compatible with standard DynDNS clients.

### URL Format

```
https://dynv6.com/nic/update?hostname=HOSTNAME&myip=IP
```

### Authentication

Use HTTP Basic Auth with:
- Username: `none` (or your email)
- Password: Your token

### Example with curl

```bash
curl -u "none:YOUR_TOKEN" \
  "https://dynv6.com/nic/update?hostname=mypi.dynv6.net&myip=2401:4900:..."
```

## 9.3 SSH Method

Most secure method using SSH keys.

### Setup

1. Generate SSH key (if not done):
```bash
ssh-keygen -t ed25519 -f ~/.ssh/dynv6_key -N ""
```

2. Add public key to dynv6 dashboard

3. Update via SSH:
```bash
ssh -i ~/.ssh/dynv6_key api@dynv6.com update mypi.dynv6.net --ipv6 2401:4900:...
```

### SSH Update Script

```bash
#!/bin/bash
# SSH-based dynv6 update

HOSTNAME="mypi.dynv6.net"
KEY="$HOME/.ssh/dynv6_key"
IPV6=$(curl -s -6 https://ipv6.icanhazip.com)

ssh -i "$KEY" -o StrictHostKeyChecking=accept-new \
    api@dynv6.com update "$HOSTNAME" --ipv6 "$IPV6"
```

## 9.4 DNS Update (TSIG)

For advanced users using standard DNS update protocol.

### Generate TSIG Key

In dynv6 dashboard, create a TSIG key for your zone.

### Update with nsupdate

```bash
# Create update file
cat > /tmp/nsupdate.txt << EOF
server dynv6.com
zone mypi.dynv6.net
update delete mypi.dynv6.net AAAA
update add mypi.dynv6.net 300 AAAA 2401:4900:8f56:85f8:ba27:ebff:fed2:832d
send
EOF

# Execute update
nsupdate -k /path/to/tsig.key /tmp/nsupdate.txt
```

## 9.5 Comparison of Methods

| Method | Security | Complexity | Best For |
|--------|----------|------------|----------|
| REST API | Medium | Low | Simple setups |
| DynDNS2 | Medium | Low | Router integration |
| SSH | High | Medium | Security-focused |
| TSIG | High | High | DNS professionals |

---

# 10. Automation with Cron

## 10.1 Understanding Cron

Cron is a time-based job scheduler in Unix-like systems.

### Cron Syntax

```
┌───────────── minute (0 - 59)
│ ┌───────────── hour (0 - 23)
│ │ ┌───────────── day of month (1 - 31)
│ │ │ ┌───────────── month (1 - 12)
│ │ │ │ ┌───────────── day of week (0 - 6) (Sunday = 0)
│ │ │ │ │
* * * * * command to execute
```

### Common Patterns

| Pattern | Meaning |
|---------|---------|
| `* * * * *` | Every minute |
| `*/5 * * * *` | Every 5 minutes |
| `*/15 * * * *` | Every 15 minutes |
| `0 * * * *` | Every hour |
| `0 0 * * *` | Daily at midnight |
| `@reboot` | On system startup |

## 10.2 Setting Up Cron Job

### Edit Crontab

```bash
# Open crontab editor
crontab -e
```

### Add Update Job

```bash
# dynv6 update - runs every 5 minutes
*/5 * * * * /home/pi/dynv6/update.sh >> /home/pi/dynv6/logs/cron.log 2>&1

# Also run on boot (after 60 second delay for network)
@reboot sleep 60 && /home/pi/dynv6/update.sh >> /home/pi/dynv6/logs/cron.log 2>&1
```

### Save and Exit

- In nano: `Ctrl+X`, then `Y`, then `Enter`
- In vim: `:wq`

### Verify Cron Job

```bash
# List current cron jobs
crontab -l
```

## 10.3 Recommended Update Frequency

| Scenario | Frequency | Cron Pattern |
|----------|-----------|--------------|
| Stable connection | Every 15 min | `*/15 * * * *` |
| Normal use | Every 5 min | `*/5 * * * *` |
| Frequent changes | Every 1 min | `* * * * *` |
| After reboot | On boot | `@reboot sleep 60 && ...` |

## 10.4 Systemd Timer Alternative

For more control, use systemd timers instead of cron.

### Create Service File

```bash
sudo nano /etc/systemd/system/dynv6-update.service
```

```ini
[Unit]
Description=Update dynv6 Dynamic DNS
After=network-online.target
Wants=network-online.target

[Service]
Type=oneshot
User=pi
ExecStart=/home/pi/dynv6/update.sh
StandardOutput=append:/home/pi/dynv6/logs/systemd.log
StandardError=append:/home/pi/dynv6/logs/systemd.log

[Install]
WantedBy=multi-user.target
```

### Create Timer File

```bash
sudo nano /etc/systemd/system/dynv6-update.timer
```

```ini
[Unit]
Description=Run dynv6 update every 5 minutes

[Timer]
OnBootSec=1min
OnUnitActiveSec=5min
AccuracySec=1min

[Install]
WantedBy=timers.target
```

### Enable Timer

```bash
# Reload systemd
sudo systemctl daemon-reload

# Enable and start timer
sudo systemctl enable dynv6-update.timer
sudo systemctl start dynv6-update.timer

# Check status
sudo systemctl status dynv6-update.timer
sudo systemctl list-timers
```

## 10.5 Network-Triggered Updates

Update immediately when network changes.

### Using NetworkManager Dispatcher

```bash
sudo nano /etc/NetworkManager/dispatcher.d/99-dynv6
```

```bash
#!/bin/bash
# Update dynv6 when network comes up

INTERFACE="$1"
ACTION="$2"

if [ "$ACTION" = "up" ]; then
    # Wait for network to stabilize
    sleep 5
    # Run update as pi user
    sudo -u pi /home/pi/dynv6/update.sh
fi
```

```bash
sudo chmod +x /etc/NetworkManager/dispatcher.d/99-dynv6
```

### Using dhcpcd Hook (for Raspberry Pi OS)

```bash
sudo nano /etc/dhcpcd.exit-hook
```

```bash
#!/bin/bash
# Update dynv6 when DHCP lease changes

if [ "$reason" = "BOUND" ] || [ "$reason" = "RENEW" ] || [ "$reason" = "REBIND" ]; then
    sudo -u pi /home/pi/dynv6/update.sh &
fi
```

```bash
sudo chmod +x /etc/dhcpcd.exit-hook
```

---

# 11. Advanced Configuration

## 11.1 Multiple Zones

Managing multiple hostnames from one Pi.

### Configuration File

```bash
nano ~/.config/dynv6/zones.conf
```

```ini
# Zone configuration file
# Format: hostname:token

mypi.dynv6.net:token1234567890
homelab.dynv6.net:token0987654321
nas.v6.rocks:tokenabcdefghij
```

### Multi-Zone Update Script

```bash
#!/bin/bash
# Multi-zone dynv6 update script

CONFIG_FILE="$HOME/.config/dynv6/zones.conf"
LOG_FILE="$HOME/dynv6/logs/multi-update.log"

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" >> "$LOG_FILE"
}

# Get current IPv6
IPV6=$(curl -s -6 --max-time 10 https://ipv6.icanhazip.com)

if [ -z "$IPV6" ]; then
    log "ERROR: Could not get IPv6 address"
    exit 1
fi

log "Current IPv6: $IPV6"

# Update each zone
while IFS=: read -r hostname token; do
    # Skip comments and empty lines
    [[ "$hostname" =~ ^#.*$ ]] && continue
    [ -z "$hostname" ] && continue

    log "Updating $hostname..."

    response=$(curl -s --max-time 30 \
        "https://dynv6.com/api/update?hostname=${hostname}&token=${token}&ipv6=${IPV6}")

    log "  Response: $response"
done < "$CONFIG_FILE"

log "All zones updated"
```

## 11.2 Dual-Stack (IPv4 + IPv6)

Update both IPv4 and IPv6 addresses.

### Dual-Stack Script

```bash
#!/bin/bash
# Dual-stack dynv6 update

HOSTNAME=$(cat ~/.config/dynv6/hostname)
TOKEN=$(cat ~/.config/dynv6/token)

# Get both IP versions
IPV6=$(curl -s -6 --max-time 10 https://ipv6.icanhazip.com 2>/dev/null)
IPV4=$(curl -s -4 --max-time 10 https://ipv4.icanhazip.com 2>/dev/null)

# Build update URL
URL="https://dynv6.com/api/update?hostname=${HOSTNAME}&token=${TOKEN}"

[ -n "$IPV6" ] && URL="${URL}&ipv6=${IPV6}"
[ -n "$IPV4" ] && URL="${URL}&ipv4=${IPV4}"

# Update
curl -s "$URL"
```

## 11.3 Subdomain Records

Create additional subdomains under your zone.

### Example: Multiple Services

```
Main zone:     mypi.dynv6.net      → 2401:4900:...:832d
Web server:    www.mypi.dynv6.net  → 2401:4900:...:832d
SSH:           ssh.mypi.dynv6.net  → 2401:4900:...:832d
API:           api.mypi.dynv6.net  → 2401:4900:...:832d
```

### Adding Subdomains via API

```bash
# Note: Subdomains typically point to the same IP
# Configure in dynv6 dashboard or use DNS update API

# Using REST API for main zone
curl "https://dynv6.com/api/update?hostname=mypi.dynv6.net&token=TOKEN&ipv6=IP"

# Subdomains are usually CNAME records pointing to main zone
# Configure these in the dynv6 dashboard
```

## 11.4 Webhook Notifications

Get notified when your IP changes.

### dynv6 Webhook Setup

1. Go to your zone settings in dynv6
2. Find "Webhooks" section
3. Add webhook URL (e.g., Discord, Slack, custom endpoint)

### Custom Notification Script

```bash
#!/bin/bash
# Update with notification

HOSTNAME=$(cat ~/.config/dynv6/hostname)
TOKEN=$(cat ~/.config/dynv6/token)
WEBHOOK_URL="https://discord.com/api/webhooks/YOUR_WEBHOOK"

# Get IPs
IPV6=$(curl -s -6 https://ipv6.icanhazip.com)
OLD_IP=$(cat ~/.config/dynv6/last_ip 2>/dev/null)

# Check if changed
if [ "$IPV6" != "$OLD_IP" ]; then
    # Update dynv6
    curl -s "https://dynv6.com/api/update?hostname=${HOSTNAME}&token=${TOKEN}&ipv6=${IPV6}"

    # Send notification
    curl -H "Content-Type: application/json" \
         -d "{\"content\": \"🔄 IP Changed!\\nOld: ${OLD_IP}\\nNew: ${IPV6}\"}" \
         "$WEBHOOK_URL"

    # Save new IP
    echo "$IPV6" > ~/.config/dynv6/last_ip
fi
```

## 11.5 Health Checks

Monitor your dynv6 setup.

### Health Check Script

```bash
#!/bin/bash
# dynv6 health check

HOSTNAME=$(cat ~/.config/dynv6/hostname)
LOG_FILE="$HOME/dynv6/logs/health.log"

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

# Check 1: Can we resolve the hostname?
log "Checking DNS resolution..."
RESOLVED_IP=$(dig AAAA "$HOSTNAME" +short)

if [ -z "$RESOLVED_IP" ]; then
    log "❌ FAIL: Cannot resolve $HOSTNAME"
    exit 1
fi
log "✅ Resolved to: $RESOLVED_IP"

# Check 2: Does it match our current IP?
log "Checking IP match..."
CURRENT_IP=$(curl -s -6 https://ipv6.icanhazip.com)

if [ "$RESOLVED_IP" != "$CURRENT_IP" ]; then
    log "⚠️  WARNING: IP mismatch!"
    log "   DNS shows: $RESOLVED_IP"
    log "   Current:   $CURRENT_IP"
    exit 1
fi
log "✅ IPs match"

# Check 3: Can we reach the Pi via the hostname?
log "Checking connectivity..."
if ping6 -c 1 -W 5 "$HOSTNAME" > /dev/null 2>&1; then
    log "✅ Hostname is reachable"
else
    log "⚠️  WARNING: Hostname not reachable (might be firewall)"
fi

log "Health check complete"
```

### Cron for Health Check

```bash
# Run health check every hour
0 * * * * /home/pi/dynv6/health-check.sh
```

---

# 12. Security Best Practices

## 12.1 Firewall Configuration

### Using UFW (Uncomplicated Firewall)

```bash
# Install UFW
sudo apt install -y ufw

# Default policies
sudo ufw default deny incoming
sudo ufw default allow outgoing

# Allow SSH (important! don't lock yourself out)
sudo ufw allow ssh

# Allow specific services
sudo ufw allow 80/tcp    # HTTP
sudo ufw allow 443/tcp   # HTTPS

# Enable firewall
sudo ufw enable

# Check status
sudo ufw status verbose
```

### IPv6-Specific Rules

```bash
# Allow SSH over IPv6
sudo ufw allow from any to any port 22 proto tcp

# Allow specific IPv6 range (your network)
sudo ufw allow from 2401:4900:8f56:85f8::/64

# View IPv6 rules
sudo ufw status verbose
```

## 12.2 SSH Hardening

### Disable Password Authentication

```bash
sudo nano /etc/ssh/sshd_config
```

```
# Disable password authentication
PasswordAuthentication no
PubkeyAuthentication yes

# Disable root login
PermitRootLogin no

# Use only SSH protocol 2
Protocol 2

# Limit authentication attempts
MaxAuthTries 3
```

```bash
# Restart SSH
sudo systemctl restart sshd
```

### Use SSH Keys

```bash
# On your client machine, generate key
ssh-keygen -t ed25519 -C "your_email@example.com"

# Copy to Pi
ssh-copy-id pi@your-pi-ip

# Test key-based login
ssh pi@your-pi-ip
```

## 12.3 Fail2Ban Setup

Protect against brute-force attacks.

```bash
# Install fail2ban
sudo apt install -y fail2ban

# Create local config
sudo cp /etc/fail2ban/jail.conf /etc/fail2ban/jail.local
sudo nano /etc/fail2ban/jail.local
```

```ini
[DEFAULT]
bantime = 1h
findtime = 10m
maxretry = 5

[sshd]
enabled = true
port = ssh
filter = sshd
logpath = /var/log/auth.log
maxretry = 3
bantime = 24h
```

```bash
# Restart fail2ban
sudo systemctl restart fail2ban

# Check status
sudo fail2ban-client status sshd
```

## 12.4 Token Security

### Environment Variables

```bash
# Add to ~/.bashrc
export DYNV6_TOKEN="your_token_here"
export DYNV6_HOSTNAME="mypi.dynv6.net"

# Use in scripts
curl "https://dynv6.com/api/update?hostname=${DYNV6_HOSTNAME}&token=${DYNV6_TOKEN}&auto"
```

### Secure File Permissions

```bash
# Secure the config directory
chmod 700 ~/.config/dynv6
chmod 600 ~/.config/dynv6/*

# Secure scripts
chmod 700 ~/dynv6/*.sh
```

## 12.5 Regular Updates

```bash
# Create update script
sudo nano /etc/cron.weekly/system-update
```

```bash
#!/bin/bash
apt update && apt upgrade -y
```

```bash
sudo chmod +x /etc/cron.weekly/system-update
```

---

# 13. Troubleshooting

## 13.1 Common Issues

### Issue: "invalid authentication"

**Cause:** Wrong token or hostname

**Solution:**
```bash
# Verify token
cat ~/.config/dynv6/token

# Verify hostname
cat ~/.config/dynv6/hostname

# Test manually
curl "https://dynv6.com/api/update?hostname=YOUR_HOSTNAME&token=YOUR_TOKEN&auto"
```

### Issue: "zone not found"

**Cause:** Hostname doesn't exist or typo

**Solution:**
1. Log into dynv6.com
2. Verify zone exists
3. Check spelling exactly

### Issue: No IPv6 Address

**Cause:** ISP doesn't provide IPv6 or router misconfigured

**Solution:**
```bash
# Check for IPv6
ip -6 addr show scope global

# Test IPv6 connectivity
ping6 google.com

# Check router settings for IPv6
```

### Issue: DNS Not Updating

**Cause:** Caching or propagation delay

**Solution:**
```bash
# Force DNS refresh
dig AAAA mypi.dynv6.net @dynv6.com +short

# Wait for TTL to expire (usually 5 minutes)

# Check multiple DNS servers
dig AAAA mypi.dynv6.net @8.8.8.8 +short
dig AAAA mypi.dynv6.net @1.1.1.1 +short
```

## 13.2 Debugging Commands

### Check Current IP

```bash
# IPv6
curl -s -6 https://ipv6.icanhazip.com
ip -6 addr show scope global

# IPv4
curl -s -4 https://ipv4.icanhazip.com
```

### Check DNS Resolution

```bash
# Query dynv6 directly
dig AAAA mypi.dynv6.net @dynv6.com +short

# Query public DNS
dig AAAA mypi.dynv6.net @8.8.8.8 +short

# Full DNS trace
dig AAAA mypi.dynv6.net +trace
```

### Check Script Logs

```bash
# View update logs
tail -50 ~/dynv6/logs/update.log

# Watch logs in real-time
tail -f ~/dynv6/logs/update.log

# Check cron logs
grep dynv6 /var/log/syslog
```

### Test API Manually

```bash
# Test with verbose output
curl -v "https://dynv6.com/api/update?hostname=mypi.dynv6.net&token=TOKEN&auto"
```

## 13.3 Network Diagnostics

### Check Connectivity

```bash
# Ping dynv6
ping -c 4 dynv6.com

# Trace route
traceroute dynv6.com

# Check if port 443 is open
nc -zv dynv6.com 443
```

### Check Firewall

```bash
# UFW status
sudo ufw status

# iptables (IPv4)
sudo iptables -L -n

# ip6tables (IPv6)
sudo ip6tables -L -n
```

## 13.4 Log Analysis

### Create Log Analyzer Script

```bash
#!/bin/bash
# Analyze dynv6 logs

LOG_FILE="$HOME/dynv6/logs/update.log"

echo "=== dynv6 Log Analysis ==="
echo ""

echo "Total updates:"
grep -c "Starting dynv6 update" "$LOG_FILE"

echo ""
echo "Successful updates:"
grep -c "Update successful" "$LOG_FILE"

echo ""
echo "Failed updates:"
grep -c "ERROR" "$LOG_FILE"

echo ""
echo "Last 5 updates:"
grep "Update successful\|ERROR" "$LOG_FILE" | tail -5

echo ""
echo "IP changes in last 24 hours:"
grep "IPv6:" "$LOG_FILE" | tail -24 | sort -u
```

---

# 14. Monitoring and Logging

## 14.1 Comprehensive Logging

### Enhanced Update Script with Logging

```bash
#!/bin/bash
# Enhanced dynv6 update with comprehensive logging

# Configuration
CONFIG_DIR="$HOME/.config/dynv6"
LOG_DIR="$HOME/dynv6/logs"
LOG_FILE="$LOG_DIR/update.log"
STATS_FILE="$LOG_DIR/stats.json"

# Ensure directories exist
mkdir -p "$LOG_DIR"

# Initialize stats file if not exists
if [ ! -f "$STATS_FILE" ]; then
    echo '{"total_updates":0,"successful":0,"failed":0,"ip_changes":0}' > "$STATS_FILE"
fi

# Logging with levels
log() {
    local level="$1"
    local message="$2"
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    local log_entry="[$timestamp] [$level] $message"

    echo "$log_entry" >> "$LOG_FILE"

    # Color output for terminal
    case "$level" in
        "ERROR") echo -e "\033[31m$log_entry\033[0m" ;;
        "WARN")  echo -e "\033[33m$log_entry\033[0m" ;;
        "INFO")  echo -e "\033[32m$log_entry\033[0m" ;;
        *)       echo "$log_entry" ;;
    esac
}

# Update statistics
update_stats() {
    local field="$1"
    if command -v jq &> /dev/null; then
        local current=$(jq ".$field" "$STATS_FILE")
        jq ".$field = $((current + 1))" "$STATS_FILE" > "$STATS_FILE.tmp"
        mv "$STATS_FILE.tmp" "$STATS_FILE"
    fi
}

# Main update logic
main() {
    log "INFO" "========== Update Started =========="
    update_stats "total_updates"

    # Get configuration
    local token=$(cat "$CONFIG_DIR/token" 2>/dev/null)
    local hostname=$(cat "$CONFIG_DIR/hostname" 2>/dev/null)

    if [ -z "$token" ] || [ -z "$hostname" ]; then
        log "ERROR" "Missing configuration"
        update_stats "failed"
        exit 1
    fi

    # Get current IP
    local ipv6=$(curl -s -6 --max-time 10 https://ipv6.icanhazip.com)
    local last_ip=$(cat "$CONFIG_DIR/last_ip" 2>/dev/null)

    log "INFO" "Current IPv6: $ipv6"
    log "INFO" "Last IPv6: ${last_ip:-none}"

    # Check for change
    if [ "$ipv6" = "$last_ip" ]; then
        log "INFO" "IP unchanged, skipping update"
        exit 0
    fi

    # Update dynv6
    local response=$(curl -s --max-time 30 \
        "https://dynv6.com/api/update?hostname=${hostname}&token=${token}&ipv6=${ipv6}")

    if echo "$response" | grep -qi "updated\|unchanged"; then
        log "INFO" "Update successful: $response"
        echo "$ipv6" > "$CONFIG_DIR/last_ip"
        update_stats "successful"

        if [ "$ipv6" != "$last_ip" ] && [ -n "$last_ip" ]; then
            update_stats "ip_changes"
            log "INFO" "IP changed from $last_ip to $ipv6"
        fi
    else
        log "ERROR" "Update failed: $response"
        update_stats "failed"
        exit 1
    fi

    log "INFO" "========== Update Complete =========="
}

main "$@"
```

## 14.2 Log Rotation

### Using logrotate

```bash
sudo nano /etc/logrotate.d/dynv6
```

```
/home/pi/dynv6/logs/*.log {
    daily
    rotate 7
    compress
    delaycompress
    missingok
    notifempty
    create 644 pi pi
}
```

### Manual Rotation Script

```bash
#!/bin/bash
# Manual log rotation

LOG_DIR="$HOME/dynv6/logs"
MAX_SIZE=1048576  # 1MB
MAX_FILES=5

for log_file in "$LOG_DIR"/*.log; do
    if [ -f "$log_file" ]; then
        size=$(stat -c%s "$log_file" 2>/dev/null || stat -f%z "$log_file")

        if [ "$size" -gt "$MAX_SIZE" ]; then
            # Rotate existing backups
            for i in $(seq $((MAX_FILES-1)) -1 1); do
                [ -f "${log_file}.$i" ] && mv "${log_file}.$i" "${log_file}.$((i+1))"
            done

            # Rotate current log
            mv "$log_file" "${log_file}.1"
            touch "$log_file"

            # Remove old backups
            [ -f "${log_file}.$((MAX_FILES+1))" ] && rm "${log_file}.$((MAX_FILES+1))"
        fi
    fi
done
```

## 14.3 Monitoring Dashboard

### Simple Status Script

```bash
#!/bin/bash
# dynv6 Status Dashboard

clear
echo "╔══════════════════════════════════════════════════════════════╗"
echo "║                    dynv6 Status Dashboard                     ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo ""

# Configuration
HOSTNAME=$(cat ~/.config/dynv6/hostname 2>/dev/null)
echo "Hostname: $HOSTNAME"
echo ""

# Current IPs
echo "┌─ Current IP Addresses ─────────────────────────────────────────┐"
IPV6=$(curl -s -6 --max-time 5 https://ipv6.icanhazip.com)
IPV4=$(curl -s -4 --max-time 5 https://ipv4.icanhazip.com 2>/dev/null)
echo "│ IPv6: ${IPV6:-Not available}"
echo "│ IPv4: ${IPV4:-Not available}"
echo "└───────────────────────────────────────────────────────────────┘"
echo ""

# DNS Resolution
echo "┌─ DNS Resolution ──────────────────────────────────────────────┐"
DNS_IP=$(dig AAAA "$HOSTNAME" +short 2>/dev/null)
echo "│ DNS returns: ${DNS_IP:-Resolution failed}"
if [ "$DNS_IP" = "$IPV6" ]; then
    echo "│ Status: ✅ MATCH"
else
    echo "│ Status: ⚠️  MISMATCH"
fi
echo "└───────────────────────────────────────────────────────────────┘"
echo ""

# Last Update
echo "┌─ Last Update ─────────────────────────────────────────────────┐"
if [ -f ~/dynv6/logs/update.log ]; then
    LAST_UPDATE=$(grep "Update complete" ~/dynv6/logs/update.log | tail -1)
    echo "│ $LAST_UPDATE"
else
    echo "│ No update log found"
fi
echo "└───────────────────────────────────────────────────────────────┘"
echo ""

# Statistics
echo "┌─ Statistics ──────────────────────────────────────────────────┐"
if [ -f ~/dynv6/logs/stats.json ] && command -v jq &> /dev/null; then
    STATS=$(cat ~/dynv6/logs/stats.json)
    echo "│ Total updates: $(echo $STATS | jq .total_updates)"
    echo "│ Successful: $(echo $STATS | jq .successful)"
    echo "│ Failed: $(echo $STATS | jq .failed)"
    echo "│ IP changes: $(echo $STATS | jq .ip_changes)"
else
    echo "│ Statistics not available"
fi
echo "└───────────────────────────────────────────────────────────────┘"
```

---

# 15. Using Your Own Domain

## 15.1 Why Use Your Own Domain?

| Free Subdomain | Your Own Domain |
|----------------|-----------------|
| mypi.dynv6.net | home.yourdomain.com |
| Depends on dynv6 | You control it |
| Free | Domain costs ~$10-15/year |
| Less professional | More professional |

## 15.2 Domain Delegation Setup

### Step 1: Get a Domain

Purchase from registrars like:
- Namecheap
- Cloudflare
- Google Domains
- Porkbun

### Step 2: Create Zone in dynv6

1. Go to "My Domains" in dynv6
2. Click "Add Domain"
3. Enter your domain: `yourdomain.com`

### Step 3: Get NS Records

dynv6 will provide nameserver records:
```
ns1.dynv6.com
ns2.dynv6.com
ns3.dynv6.com
```

### Step 4: Update Domain Registrar

At your registrar, set nameservers to:
```
ns1.dynv6.com
ns2.dynv6.com
ns3.dynv6.com
```

### Step 5: Wait for Propagation

DNS changes can take 24-48 hours to propagate globally.

### Step 6: Verify

```bash
# Check nameservers
dig NS yourdomain.com +short

# Should return:
# ns1.dynv6.com.
# ns2.dynv6.com.
# ns3.dynv6.com.
```

## 15.3 Subdomain Delegation (Alternative)

Keep your main domain elsewhere, only delegate a subdomain.

### At Your Registrar/DNS Provider

Add NS records for the subdomain:
```
home.yourdomain.com  NS  ns1.dynv6.com
home.yourdomain.com  NS  ns2.dynv6.com
home.yourdomain.com  NS  ns3.dynv6.com
```

### In dynv6

Create zone for `home.yourdomain.com`

## 15.4 Update Script for Custom Domain

```bash
#!/bin/bash
# Update custom domain

HOSTNAME="home.yourdomain.com"
TOKEN=$(cat ~/.config/dynv6/token)
IPV6=$(curl -s -6 https://ipv6.icanhazip.com)

curl -s "https://dynv6.com/api/update?hostname=${HOSTNAME}&token=${TOKEN}&ipv6=${IPV6}"
```

---

# 16. Integration with Services

## 16.1 Web Server (Nginx)

### Install Nginx

```bash
sudo apt install -y nginx
```

### Configure Virtual Host

```bash
sudo nano /etc/nginx/sites-available/mypi
```

```nginx
server {
    listen 80;
    listen [::]:80;

    server_name mypi.dynv6.net;

    root /var/www/mypi;
    index index.html;

    location / {
        try_files $uri $uri/ =404;
    }
}
```

### Enable Site

```bash
sudo ln -s /etc/nginx/sites-available/mypi /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

## 16.2 SSL with Let's Encrypt

### Install Certbot

```bash
sudo apt install -y certbot python3-certbot-nginx
```

### Get Certificate

```bash
sudo certbot --nginx -d mypi.dynv6.net
```

### Auto-Renewal

```bash
# Test renewal
sudo certbot renew --dry-run

# Certbot automatically adds cron job
```

## 16.3 SSH Access

### SSH Config on Client

```bash
# ~/.ssh/config
Host mypi
    HostName mypi.dynv6.net
    User pi
    IdentityFile ~/.ssh/id_ed25519
    Port 22
```

### Connect

```bash
ssh mypi
```

## 16.4 Home Assistant

### Configuration

```yaml
# configuration.yaml
homeassistant:
  external_url: "https://mypi.dynv6.net:8123"
  internal_url: "http://192.168.1.x:8123"
```

## 16.5 Nextcloud

### Trusted Domains

```php
// config/config.php
'trusted_domains' =>
array (
  0 => '192.168.1.x',
  1 => 'mypi.dynv6.net',
),
```

## 16.6 Plex Media Server

### Remote Access

1. Open Plex settings
2. Go to Remote Access
3. Manually specify public port
4. Use mypi.dynv6.net for access

---

# 17. Backup and Recovery

## 17.1 What to Backup

| Item | Location | Priority |
|------|----------|----------|
| Token | ~/.config/dynv6/token | Critical |
| Hostname | ~/.config/dynv6/hostname | Critical |
| Update script | ~/dynv6/update.sh | High |
| Logs | ~/dynv6/logs/ | Low |
| Crontab | crontab -l | High |

## 17.2 Backup Script

```bash
#!/bin/bash
# Backup dynv6 configuration

BACKUP_DIR="$HOME/backups/dynv6"
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="$BACKUP_DIR/dynv6_backup_$DATE.tar.gz"

mkdir -p "$BACKUP_DIR"

# Create backup
tar -czf "$BACKUP_FILE" \
    -C "$HOME" \
    .config/dynv6 \
    dynv6

# Backup crontab
crontab -l > "$BACKUP_DIR/crontab_$DATE.txt"

echo "Backup created: $BACKUP_FILE"

# Keep only last 5 backups
ls -t "$BACKUP_DIR"/dynv6_backup_*.tar.gz | tail -n +6 | xargs -r rm
```

## 17.3 Recovery Procedure

### Step 1: Restore Files

```bash
# Extract backup
tar -xzf dynv6_backup_YYYYMMDD_HHMMSS.tar.gz -C $HOME

# Restore crontab
crontab crontab_YYYYMMDD_HHMMSS.txt
```

### Step 2: Verify Permissions

```bash
chmod 700 ~/.config/dynv6
chmod 600 ~/.config/dynv6/*
chmod 700 ~/dynv6/*.sh
```

### Step 3: Test

```bash
~/dynv6/update.sh
```

## 17.4 Disaster Recovery

If you lose access to your Pi:

1. **Log into dynv6.com**
2. **Manually update IP** in the dashboard
3. **Regain SSH access**
4. **Restore from backup**

---

# 18. FAQ

## 18.1 General Questions

### Q: Is dynv6 really free?

**A:** Yes, dynv6 is completely free for personal use. There are no hidden fees or premium tiers required for basic functionality.

### Q: How reliable is dynv6?

**A:** dynv6 has been running for years and is generally reliable. However, they explicitly state they don't offer enterprise-grade SLAs, so don't use it for critical business services.

### Q: Can I use dynv6 for commercial purposes?

**A:** Check dynv6's terms of service. For commercial use, you might want to consider paid alternatives with SLAs.

## 18.2 Technical Questions

### Q: How often should I update my IP?

**A:** Every 5 minutes is a good balance. More frequent updates (1 minute) are fine but usually unnecessary.

### Q: Why isn't my hostname resolving?

**A:** Common causes:
1. DNS propagation delay (wait 5-10 minutes)
2. Wrong token or hostname
3. Update script not running
4. Network issues

### Q: Can I use dynv6 with IPv4 only?

**A:** Yes, but dynv6 is optimized for IPv6. For IPv4-only, consider other providers like DuckDNS or No-IP.

### Q: How do I update multiple hostnames?

**A:** Create multiple zones in dynv6 and use a multi-zone update script (see Section 11.1).

## 18.3 Security Questions

### Q: Is it safe to expose my home server?

**A:** With proper security measures (firewall, SSH keys, fail2ban), it's reasonably safe. Always keep software updated.

### Q: Can someone find my home IP through dynv6?

**A:** Yes, anyone can query your hostname to find your IP. This is how DNS works. Use a VPN or Cloudflare Tunnel if you need to hide your IP.

### Q: What if my token is compromised?

**A:** Immediately:
1. Log into dynv6.com
2. Delete the compromised token
3. Create a new token
4. Update your scripts

---

# 19. Appendix

## 19.1 Complete Update Script

```bash
#!/bin/bash
#
# dynv6 Complete Update Script
# Version: 2.0
#
# Features:
# - IPv4 and IPv6 support
# - Multiple fallback IP detection services
# - Comprehensive logging
# - IP change detection
# - Error handling
# - Statistics tracking

set -euo pipefail

# ============================================================
# CONFIGURATION
# ============================================================

readonly CONFIG_DIR="${HOME}/.config/dynv6"
readonly LOG_DIR="${HOME}/dynv6/logs"
readonly LOG_FILE="${LOG_DIR}/update.log"
readonly CACHE_FILE="${CONFIG_DIR}/last_ip"
readonly STATS_FILE="${LOG_DIR}/stats.json"
readonly MAX_LOG_SIZE=1048576  # 1MB

# Read configuration
TOKEN=""
HOSTNAME=""

# ============================================================
# FUNCTIONS
# ============================================================

init() {
    mkdir -p "$LOG_DIR"
    mkdir -p "$CONFIG_DIR"

    if [ -f "${CONFIG_DIR}/token" ]; then
        TOKEN=$(cat "${CONFIG_DIR}/token")
    fi

    if [ -f "${CONFIG_DIR}/hostname" ]; then
        HOSTNAME=$(cat "${CONFIG_DIR}/hostname")
    fi

    # Initialize stats
    if [ ! -f "$STATS_FILE" ]; then
        echo '{"updates":0,"success":0,"failed":0,"changes":0}' > "$STATS_FILE"
    fi
}

log() {
    local level="$1"
    local message="$2"
    local timestamp
    timestamp=$(date '+%Y-%m-%d %H:%M:%S')

    echo "[$timestamp] [$level] $message" >> "$LOG_FILE"

    if [ -t 1 ]; then
        case "$level" in
            ERROR) echo -e "\033[31m[$timestamp] [$level] $message\033[0m" ;;
            WARN)  echo -e "\033[33m[$timestamp] [$level] $message\033[0m" ;;
            INFO)  echo -e "\033[32m[$timestamp] [$level] $message\033[0m" ;;
            *)     echo "[$timestamp] [$level] $message" ;;
        esac
    fi
}

rotate_log() {
    if [ -f "$LOG_FILE" ]; then
        local size
        size=$(stat -c%s "$LOG_FILE" 2>/dev/null || stat -f%z "$LOG_FILE" 2>/dev/null || echo 0)
        if [ "$size" -gt "$MAX_LOG_SIZE" ]; then
            mv "$LOG_FILE" "${LOG_FILE}.old"
            log "INFO" "Log rotated"
        fi
    fi
}

update_stats() {
    local field="$1"
    if command -v jq &> /dev/null && [ -f "$STATS_FILE" ]; then
        local tmp
        tmp=$(mktemp)
        jq ".$field += 1" "$STATS_FILE" > "$tmp" && mv "$tmp" "$STATS_FILE"
    fi
}

get_ipv6() {
    local ip=""
    local services=(
        "https://ipv6.icanhazip.com"
        "https://api6.ipify.org"
        "https://v6.ident.me"
    )

    for service in "${services[@]}"; do
        ip=$(curl -s -6 --max-time 10 "$service" 2>/dev/null) && break
    done

    echo "$ip"
}

get_ipv4() {
    local ip=""
    local services=(
        "https://ipv4.icanhazip.com"
        "https://api.ipify.org"
        "https://v4.ident.me"
    )

    for service in "${services[@]}"; do
        ip=$(curl -s -4 --max-time 10 "$service" 2>/dev/null) && break
    done

    echo "$ip"
}

update_dynv6() {
    local ipv6="$1"
    local ipv4="$2"

    local url="https://dynv6.com/api/update?hostname=${HOSTNAME}&token=${TOKEN}"

    [ -n "$ipv6" ] && url="${url}&ipv6=${ipv6}"
    [ -n "$ipv4" ] && url="${url}&ipv4=${ipv4}"

    curl -s --max-time 30 "$url"
}

main() {
    init
    rotate_log

    log "INFO" "=========================================="
    log "INFO" "Starting dynv6 update"
    update_stats "updates"

    # Validate configuration
    if [ -z "$TOKEN" ]; then
        log "ERROR" "Token not configured"
        update_stats "failed"
        exit 1
    fi

    if [ -z "$HOSTNAME" ]; then
        log "ERROR" "Hostname not configured"
        update_stats "failed"
        exit 1
    fi

    log "INFO" "Hostname: $HOSTNAME"

    # Get current IPs
    local ipv6 ipv4
    ipv6=$(get_ipv6)
    ipv4=$(get_ipv4)

    log "INFO" "IPv6: ${ipv6:-none}"
    log "INFO" "IPv4: ${ipv4:-none}"

    if [ -z "$ipv6" ] && [ -z "$ipv4" ]; then
        log "ERROR" "Could not determine any IP address"
        update_stats "failed"
        exit 1
    fi

    # Check for changes
    local current_ip="${ipv6}|${ipv4}"
    local last_ip=""
    [ -f "$CACHE_FILE" ] && last_ip=$(cat "$CACHE_FILE")

    if [ "$current_ip" = "$last_ip" ]; then
        log "INFO" "IP unchanged, skipping update"
        exit 0
    fi

    # Update dynv6
    log "INFO" "Updating dynv6..."
    local response
    response=$(update_dynv6 "$ipv6" "$ipv4")

    if echo "$response" | grep -qi "updated\|unchanged"; then
        log "INFO" "Success: $response"
        echo "$current_ip" > "$CACHE_FILE"
        update_stats "success"

        if [ -n "$last_ip" ] && [ "$current_ip" != "$last_ip" ]; then
            update_stats "changes"
            log "INFO" "IP changed!"
        fi
    else
        log "ERROR" "Failed: $response"
        update_stats "failed"
        exit 1
    fi

    log "INFO" "Update complete"
    log "INFO" "=========================================="
}

main "$@"
```

## 19.2 Quick Reference Card

```
╔══════════════════════════════════════════════════════════════════════╗
║                     dynv6 QUICK REFERENCE                             ║
╠══════════════════════════════════════════════════════════════════════╣
║                                                                       ║
║  CONFIGURATION FILES                                                  ║
║  ─────────────────                                                    ║
║  Token:      ~/.config/dynv6/token                                    ║
║  Hostname:   ~/.config/dynv6/hostname                                 ║
║  Script:     ~/dynv6/update.sh                                        ║
║  Logs:       ~/dynv6/logs/update.log                                  ║
║                                                                       ║
║  USEFUL COMMANDS                                                      ║
║  ───────────────                                                      ║
║  Get IPv6:   curl -s -6 https://ipv6.icanhazip.com                   ║
║  Get IPv4:   curl -s -4 https://ipv4.icanhazip.com                   ║
║  Check DNS:  dig AAAA mypi.dynv6.net +short                          ║
║  Test ping:  ping6 mypi.dynv6.net                                    ║
║                                                                       ║
║  UPDATE API                                                           ║
║  ──────────                                                           ║
║  URL: https://dynv6.com/api/update                                   ║
║  Params: hostname, token, ipv6, ipv4, auto                           ║
║                                                                       ║
║  CRON EXAMPLES                                                        ║
║  ─────────────                                                        ║
║  Every 5 min:  */5 * * * * ~/dynv6/update.sh                         ║
║  On boot:      @reboot sleep 60 && ~/dynv6/update.sh                 ║
║                                                                       ║
║  TROUBLESHOOTING                                                      ║
║  ───────────────                                                      ║
║  View logs:    tail -50 ~/dynv6/logs/update.log                      ║
║  Test script:  ~/dynv6/update.sh                                     ║
║  Check cron:   crontab -l                                            ║
║                                                                       ║
╚══════════════════════════════════════════════════════════════════════╝
```

## 19.3 Glossary

| Term | Definition |
|------|------------|
| **AAAA Record** | DNS record type for IPv6 addresses |
| **A Record** | DNS record type for IPv4 addresses |
| **CGNAT** | Carrier-Grade NAT - ISP-level NAT that shares public IPs |
| **DDNS** | Dynamic DNS - automatically updates DNS when IP changes |
| **DNS** | Domain Name System - translates hostnames to IP addresses |
| **IPv4** | Internet Protocol version 4 (e.g., 192.168.1.1) |
| **IPv6** | Internet Protocol version 6 (e.g., 2001:db8::1) |
| **NAT** | Network Address Translation |
| **TTL** | Time To Live - how long DNS records are cached |
| **Zone** | A DNS zone containing records for a domain |

## 19.4 Resources

### Official Links

- dynv6 Website: https://dynv6.com
- dynv6 Documentation: https://dynv6.com/docs
- dynv6 API Reference: https://dynv6.com/docs/apis

### Community Resources

- Reddit r/selfhosted: https://reddit.com/r/selfhosted
- Reddit r/homelab: https://reddit.com/r/homelab

### Related Tools

- dig (DNS lookup): Part of dnsutils package
- curl: HTTP client for API requests
- jq: JSON processor for scripts

---

# Document Information

| Property | Value |
|----------|-------|
| **Title** | Complete Guide to dynv6 Dynamic DNS Setup |
| **Version** | 1.0 |
| **Created** | January 2026 |
| **Author** | Auto-generated |
| **Target Audience** | Raspberry Pi users, home server enthusiasts |
| **Estimated Reading Time** | 45-60 minutes |
| **Difficulty** | Beginner to Intermediate |

---

# Changelog

## Version 1.0 (January 2026)
- Initial release
- Complete setup guide for Raspberry Pi
- Multiple update methods documented
- Security best practices included
- Troubleshooting section added
- Integration examples provided

---

**End of Document**

*Thank you for reading this guide. If you found it helpful, consider
supporting the dynv6 service and the open-source community.*


