# macOS Network Debugging Guide

## Quick Network Overview

```bash
# Show all network interfaces and their status
networksetup -listallhardwareports

# Get current network service order
networksetup -listnetworkserviceorder

# Show active network interface
route get default | grep interface
```

## IP & Interface Information

```bash
# Show all IP addresses assigned to interfaces
ifconfig | grep "inet "

# Detailed interface info (replace en0 with your interface)
ifconfig en0

# Get your public IP address
curl -s ifconfig.me

# Get local IP on primary interface
ipconfig getifaddr en0
```

## Wi-Fi Specific Commands

```bash
# Current Wi-Fi network details (SSID, BSSID, channel, signal, etc.)
/System/Library/PrivateFrameworks/[Apple80211](2026-01-09_apple80211.md).framework/Versions/Current/Resources/airport 
-I

# Scan available Wi-Fi networks
/System/Library/PrivateFrameworks/Apple80211.framework/Versions/Current/Resources/airport -s

# Wi-Fi signal strength and noise
/System/Library/PrivateFrameworks/Apple80211.framework/Versions/Current/Resources/airport -I | grep -E 
"agrCtlRSSI|agrCtlNoise"

# Show saved Wi-Fi networks
networksetup -listpreferredwirelessnetworks en0
```

## DNS Information

```bash
# Show current DNS servers
scutil --dns | grep "nameserver"

# Full DNS configuration
scutil --dns

# Test DNS resolution
nslookup google.com

# Detailed DNS query
dig google.com

# Flush DNS cache
sudo dscacheutil -flushcache; sudo killall -HUP mDNSResponder
```

## Routing & Gateway

```bash
# Show default gateway
netstat -nr | grep default

# Full routing table
netstat -nr

# Trace route to a host
traceroute google.com

# Show route to specific host
route get google.com
```

## Connection Testing

```bash
# Basic connectivity test
ping -c 5 8.8.8.8

# Ping with timestamp
ping -c 5 -D google.com

# Test specific port connectivity
nc -zv google.com 443

# Test TCP connection with timeout
nc -w 3 -zv google.com 80
```

## Active Connections & Ports

```bash
# Show all active connections
netstat -an | grep ESTABLISHED

# Show listening ports
lsof -i -P | grep LISTEN

# Show connections by process
lsof -i -P -n

# Show network statistics
netstat -s
```

## Network Performance

```bash
# Bandwidth test (requires speedtest-cli: brew install speedtest-cli)
speedtest-cli

# Network throughput to a host
# Install iperf3: brew install iperf3
# Then run: iperf3 -c <server-ip>

# Check packet loss
ping -c 100 google.com | grep "packet loss"
```

## DHCP Information

```bash
# Show DHCP info for interface
ipconfig getpacket en0

# Renew DHCP lease
sudo ipconfig set en0 DHCP
```

## Firewall & Security

```bash
# Check firewall status
sudo /usr/libexec/ApplicationFirewall/socketfilterfw --getglobalstate

# List firewall rules
sudo pfctl -sr

# Check if specific port is blocked
sudo lsof -i :80
```

## Network Diagnostics (Built-in)

```bash
# Run Apple's network diagnostics (generates report)
sudo sysdiagnose -f ~/Desktop

# Wireless diagnostics (GUI)
# Hold Option key and click Wi-Fi icon, select "Open Wireless Diagnostics"
```

## Quick Troubleshooting Script

```bash
#!/bin/bash
echo "=== Network Debug Summary ==="
echo "\n--- Active Interface ---"
route get default | grep interface
echo "\n--- IP Address ---"
ifconfig en0 | grep "inet "
echo "\n--- Gateway ---"
netstat -nr | grep "default" | head -1
echo "\n--- DNS Servers ---"
scutil --dns | grep "nameserver" | head -3
echo "\n--- Public IP ---"
curl -s ifconfig.me
echo "\n--- Connectivity Test ---"
ping -c 3 8.8.8.8 | tail -2
```

## Useful Aliases (add to ~/.zshrc or ~/.bashrc)

```bash
alias myip='curl -s ifconfig.me && echo'
alias localip='ipconfig getifaddr en0'
alias wifi='/System/Library/PrivateFrameworks/Apple80211.framework/Versions/Current/Resources/airport -I'
alias wifiscan='/System/Library/PrivateFrameworks/Apple80211.framework/Versions/Current/Resources/airport -s'
alias flushdns='sudo dscacheutil -flushcache; sudo killall -HUP mDNSResponder'
alias ports='lsof -i -P | grep LISTEN'
alias connections='netstat -an | grep ESTABLISHED'
```

