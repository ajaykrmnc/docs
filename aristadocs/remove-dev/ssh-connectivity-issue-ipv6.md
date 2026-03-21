# SSH Connectivity Issue to IPv6 Home Lab Server

**Target:** `2401:4900:8f56:85f8:ba27:ebff:fed2:832d` (Home Lab Server)
**Date:** 2026-01-29
**Status:** ❌ NOT POSSIBLE FROM CORPORATE NETWORK

---

## Summary

SSH connection to the home lab server at IPv6 address `2401:4900:8f56:85f8:ba27:ebff:fed2:832d` is **impossible** because:

> **The Arista corporate network does NOT provide IPv6 connectivity to the public internet.**

This is a **network infrastructure limitation**, not a machine configuration issue.

---

## Root Cause: Corporate Network Has No IPv6

### Evidence

1. **No IPv6 address assigned by network:**
   ```
   networksetup -getinfo "Wi-Fi"
   IPv6: Automatic
   IPv6 IP address: none      <-- No IPv6 address!
   IPv6 Router: none          <-- No IPv6 gateway!
   ```

2. **No IPv6 router advertisements from corporate network:**
   - The Wi-Fi network (en0) only provides IPv4 via DHCP
   - No Router Advertisements (RA) for IPv6 are being sent by the network

3. **Cannot reach ANY public IPv6 address:**
   ```bash
   $ ping6 2001:4860:4860::8888   # Google DNS
   ping6: UDP connect: No route to host

   $ curl -6 https://ipv6.icanhazip.com
   # Times out - no IPv6 connectivity
   ```

4. **DNS configured for IPv4 only:**
   ```
   nameserver: 10.14.0.1 (IPv4 only)
   flags: Request A records    <-- Only A records, no AAAA!
   ```

---

## Why IPv6 is Disabled (Corporate Network Reasons)

Arista Networks corporate infrastructure likely disabled IPv6 for these reasons:

1. **Security Policy** - Many enterprises disable IPv6 to reduce attack surface
2. **Network Simplicity** - IPv4-only networks are easier to monitor/firewall
3. **Legacy Infrastructure** - Some internal systems may not support IPv6
4. **VPN Compatibility** - Corporate VPNs often only tunnel IPv4 traffic

---

## Can You Enable IPv6 From Your Machine?

### ❌ NO - Here's Why:

| What You Control | What You DON'T Control |
|------------------|------------------------|
| Your Mac's IPv6 setting (already set to "Automatic") | Network router sending IPv6 Router Advertisements |
| | DHCP server providing IPv6 addresses |
| | Corporate firewall allowing IPv6 traffic |
| | ISP providing IPv6 to the office |

Your Mac is **already configured correctly** for IPv6:
```
IPv6: Automatic
net.inet6.ip6.accept_rtadv: 1  (accepting router advertisements)
```

The problem is the **corporate network infrastructure** doesn't provide IPv6.

---

## Possible Workarounds (Require Home Server Setup)

Since you can't get IPv6 on the corporate network, your home server needs to be reachable via IPv4:

### Option 1: Cloudflare Tunnel (Free, Recommended)
On your home server:
```bash
# Install cloudflared
curl -L https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64 -o cloudflared
chmod +x cloudflared
./cloudflared tunnel login
./cloudflared tunnel create homelab
./cloudflared tunnel route dns homelab ssh.yourdomain.com
./cloudflared tunnel run homelab
```
From work: `ssh user@ssh.yourdomain.com`

### Option 2: Reverse SSH Tunnel (Requires a VPS)
On home server:
```bash
ssh -R 2222:localhost:22 user@your-vps-ip -N -f
```
From work: `ssh -p 2222 user@your-vps-ip`

### Option 3: ngrok (Quick setup)
On home server:
```bash
ngrok tcp 22
```

---

## Network Details

| Parameter | Value |
|-----------|-------|
| Wi-Fi IP | 10.86.8.94 |
| Subnet | 255.255.252.0 |
| Gateway | 10.86.8.1 |
| DNS | 10.14.0.1 |
| IPv6 Status | **DISABLED BY NETWORK** |
| Public IPv4 | 136.233.250.250 |

---

## Conclusion

**You cannot SSH to your home lab's IPv6 address from the Arista corporate network.**

The corporate network does not provide IPv6 connectivity, and this cannot be changed from your machine. You would need to either:
1. Request IT to enable IPv6 (unlikely to be approved)
2. Set up a tunnel/relay on your home server to make it reachable via IPv4

