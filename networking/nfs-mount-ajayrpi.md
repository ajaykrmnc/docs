# NFS Mount Guide: ajayrpi.dynv6.net

## Overview

This document provides a comprehensive guide for mounting NFS shares from `ajayrpi.dynv6.net`
(a Raspberry Pi running Raspberry Pi OS/Debian Trixie) on macOS. It covers the complete setup
process including SSH key configuration, NFS server installation, export configuration, and
client-side mounting.

**Date Configured**: 2026-01-31

---

## Table of Contents

1. [Host Information](#host-information)
2. [Current Status](#current-status)
3. [Quick Reference](#quick-reference)
4. [Network Connectivity](#network-connectivity)
5. [SSH Configuration](#ssh-configuration)
6. [NFS Server Setup (Raspberry Pi)](#nfs-server-setup-raspberry-pi)
7. [NFS Client Setup (macOS)](#nfs-client-setup-macos)
8. [Symlink Limitation and USB Drive Access](#symlink-limitation-and-usb-drive-access)
9. [Auto-Mount Configuration](#auto-mount-configuration)
10. [Troubleshooting](#troubleshooting)
11. [Complete Setup Log](#complete-setup-log)

---

## Host Information

### Raspberry Pi (Server)

| Property | Value |
|----------|-------|
| **Hostname** | ajayrpi.dynv6.net |
| **Dynamic DNS Provider** | dynv6.net |
| **IPv4 Address** | 198.168.1.12 (local network only, not routable) |
| **IPv6 Address** | 2401:4900:8f56:cbfa:ba27:ebff:fed2:832d |
| **Operating System** | Raspberry Pi OS (Debian Trixie) |
| **SSH Username** | ajayrpi |
| **SSH Password** | indu218009 |
| **Home Directory** | /home/ajayrpi |
| **USB Mount Point** | /mnt/usb |

### macOS Client

| Property | Value |
|----------|-------|
| **Username** | ajay.kumar |
| **UID** | 501 |
| **GID** | 20 (staff) |
| **SSH Key** | ~/.ssh/id_ed25519 |

---

## Current Status

| Component | Status | Details |
|-----------|--------|---------|
| **IPv6 Connectivity** | ✅ Working | Ping successful via IPv6 |
| **IPv4 Connectivity** | ❌ Not routable | 198.168.1.12 is not reachable externally |
| **Passwordless SSH** | ✅ Configured | Using ~/.ssh/id_ed25519 key |
| **SSH Config Entry** | ✅ Added | `Host ajayrpi` in ~/.ssh/config |
| **NFS Server** | ✅ Installed | nfs-kernel-server package |
| **NFS Exports** | ✅ Configured | /home/ajayrpi and /mnt/usb |
| **Home Directory Mount** | ✅ Working | /Volumes/ajayrpi |
| **USB Drive Mount** | ✅ Working | /Volumes/ajayrpi-usb |

---

## Quick Reference

### Mount Commands (Copy-Paste Ready)

```bash
# Create mount points (one-time setup)
sudo mkdir -p /Volumes/ajayrpi /Volumes/ajayrpi-usb

# Mount Pi home directory
sudo mount -t nfs -o nfsvers=3,resvport ajayrpi.dynv6.net:/home/ajayrpi /Volumes/ajayrpi

# Mount USB drive
sudo mount -t nfs -o nfsvers=3,resvport ajayrpi.dynv6.net:/mnt/usb /Volumes/ajayrpi-usb

# Unmount both
sudo umount /Volumes/ajayrpi /Volumes/ajayrpi-usb
```

### SSH Access

```bash
# Using SSH config alias (recommended)
ssh ajayrpi

# Full command
ssh ajayrpi@ajayrpi.dynv6.net
```

### Mount Points Summary

| Local Mount Point | Remote Export Path | Description |
|-------------------|-------------------|-------------|
| `/Volumes/ajayrpi` | `/home/ajayrpi` | Pi user home directory |
| `/Volumes/ajayrpi-usb` | `/mnt/usb` | External USB drive |

---

## Network Connectivity

### IPv6 vs IPv4

The Raspberry Pi uses **dynv6.net** for dynamic DNS. The DNS record contains both IPv4 and IPv6 addresses:

```bash
$ host ajayrpi.dynv6.net
ajayrpi.dynv6.net has address 198.168.1.12
ajayrpi.dynv6.net has IPv6 address 2401:4900:8f56:cbfa:ba27:ebff:fed2:832d
```

**Important**: The IPv4 address `198.168.1.12` is a private/local address that is NOT routable
over the internet. Only IPv6 connectivity works for remote access.

### Testing Connectivity

```bash
# Test IPv6 (should work)
ping6 -c 2 ajayrpi.dynv6.net

# Test IPv4 (will fail if not on same local network)
ping -c 2 ajayrpi.dynv6.net
```

### Why IPv6 Works

The Pi has a globally routable IPv6 address assigned by the ISP. The dynv6 dynamic DNS
service keeps this address updated automatically via a script running on the Pi
(`/home/ajayrpi/ipv6-dynv6-updater.sh`).

---

## SSH Configuration

### Passwordless SSH Setup Process

The following steps were performed to enable passwordless SSH access:

#### Step 1: Identify Available SSH Keys on macOS

```bash
$ ls -la ~/.ssh/*.pub
-rw-r--r--  1 ajay.kumar  staff  574 Jul 24  2025 /Users/ajay.kumar/.ssh/github_personal.pub
-rw-r--r--@ 1 ajay.kumar  staff   92 Jul  7  2025 /Users/ajay.kumar/.ssh/id_ed25519.pub
-rw-r--r--  1 ajay.kumar  staff  105 Aug 20 11:29 /Users/ajay.kumar/.ssh/id_mwm.pub
```

#### Step 2: Copy Public Key to Pi

Initially, `ssh-copy-id` was used with password authentication:

```bash
sshpass -p 'indu218009' ssh-copy-id -o StrictHostKeyChecking=no ajayrpi@ajayrpi.dynv6.net
```

This copied `id_mwm.pub` to the Pi. Then the `id_ed25519.pub` key was also added:

```bash
cat ~/.ssh/id_ed25519.pub | ssh -i ~/.ssh/id_mwm ajayrpi@ajayrpi.dynv6.net \
  "mkdir -p ~/.ssh && cat >> ~/.ssh/authorized_keys"
```

#### Step 3: Verify Passwordless Access

```bash
$ ssh ajayrpi@ajayrpi.dynv6.net "whoami"
ajayrpi
```

#### Step 4: Add SSH Config Entry

Added to `~/.ssh/config` for convenience:

```
Host ajayrpi
    HostName ajayrpi.dynv6.net
    User ajayrpi
    IdentityFile ~/.ssh/id_ed25519
```

Now you can simply use:

```bash
ssh ajayrpi
```

### Authorized Keys on Pi

The Pi's `~/.ssh/authorized_keys` file now contains:
- `id_mwm.pub` (from ssh-copy-id)
- `id_ed25519.pub` (manually added)

---

## NFS Server Setup (Raspberry Pi)

### Package Installation

NFS server was not installed by default. The following command installed it:

```bash
sudo apt update
sudo apt install -y nfs-kernel-server
```

**Installed packages**:
- `nfs-kernel-server` - Main NFS server
- `nfs-common` - Common NFS utilities
- `rpcbind` - RPC portmapper service
- `keyutils` - Key management utilities
- `libnfsidmap1` - NFS ID mapping library
- `libevent-core-2.1-7t64` - Event notification library

### Export Configuration

The NFS exports are defined in `/etc/exports` on the Pi:

```
/home/ajayrpi *(rw,sync,no_subtree_check,insecure,no_root_squash)
/mnt/usb *(rw,sync,no_subtree_check,insecure,no_root_squash)
```

### Export Options Explained

| Option | Description |
|--------|-------------|
| `*` | Allow connections from any client IP |
| `rw` | Read and write access |
| `sync` | Write changes to disk before replying (safer, slightly slower) |
| `no_subtree_check` | Disables subtree checking for better reliability |
| `insecure` | Allow connections from ports > 1024 (required for macOS) |
| `no_root_squash` | Root user on client maps to root on server (use with caution) |

### Applying Export Changes

After modifying `/etc/exports`, apply changes with:

```bash
sudo exportfs -ra
```

### Service Management

```bash
# Start NFS server
sudo systemctl start nfs-kernel-server

# Enable on boot
sudo systemctl enable nfs-kernel-server

# Restart after config changes
sudo systemctl restart nfs-kernel-server

# Check status
sudo systemctl status nfs-kernel-server
```

### Verify Exports

```bash
# Show active exports
sudo exportfs -v

# Show exports (from client)
showmount -e localhost
```

---

## NFS Client Setup (macOS)

### Create Mount Points

```bash
sudo mkdir -p /Volumes/ajayrpi
sudo mkdir -p /Volumes/ajayrpi-usb
```

### Mount Command Syntax

```bash
sudo mount -t nfs -o <options> <server>:<export_path> <local_mount_point>
```

### Mount Options for macOS

| Option | Description |
|--------|-------------|
| `-t nfs` | Specify NFS filesystem type |
| `nfsvers=3` | Use NFS version 3 (better macOS compatibility than v4) |
| `resvport` | Use a reserved port (<1024) for the connection |
| `soft` | Return error on timeout instead of hanging (optional) |
| `intr` | Allow keyboard interrupts (optional) |
| `tcp` | Use TCP instead of UDP (default on most systems) |

### Mount Home Directory

```bash
sudo mount -t nfs -o nfsvers=3,resvport ajayrpi.dynv6.net:/home/ajayrpi /Volumes/ajayrpi
```

### Mount USB Drive

```bash
sudo mount -t nfs -o nfsvers=3,resvport ajayrpi.dynv6.net:/mnt/usb /Volumes/ajayrpi-usb
```

### Verify Mounts

```bash
$ mount | grep ajayrpi
ajayrpi.dynv6.net:/home/ajayrpi on /Volumes/ajayrpi (nfs)
ajayrpi.dynv6.net:/mnt/usb on /Volumes/ajayrpi-usb (nfs)
```

### Unmount

```bash
# Normal unmount
sudo umount /Volumes/ajayrpi
sudo umount /Volumes/ajayrpi-usb

# Force unmount if stuck
sudo umount -f /Volumes/ajayrpi
```

---

## Symlink Limitation and USB Drive Access

### The Problem

The Pi's home directory contains a symlink to the USB drive:

```bash
$ ls -la /home/ajayrpi/usb
lrwxrwxrwx 1 ajayrpi ajayrpi 8 Jan 29 22:28 /home/ajayrpi/usb -> /mnt/usb
```

When accessing via NFS, this symlink is visible:

```bash
$ ls -la /Volumes/ajayrpi/usb
lrwxrwxrwx  1 1000  1000  8 Jan 29 22:28 /Volumes/ajayrpi/usb -> /mnt/usb
```

However, trying to follow the symlink fails:

```bash
$ ls /Volumes/ajayrpi/usb/
ls: /Volumes/ajayrpi/usb/: No such file or directory
```

### Why This Happens

NFS exports are **bounded** to the exported directory tree. The symlink points to `/mnt/usb`,
which is **outside** the exported path `/home/ajayrpi`. NFS does not follow symlinks that
point outside the export boundary for security reasons.

### The Solution

Export `/mnt/usb` as a separate NFS share and mount it independently:

1. **Add to /etc/exports on Pi**:
   ```
   /mnt/usb *(rw,sync,no_subtree_check,insecure,no_root_squash)
   ```

2. **Apply changes**:
   ```bash
   sudo exportfs -ra
   ```

3. **Mount on macOS**:
   ```bash
   sudo mount -t nfs -o nfsvers=3,resvport ajayrpi.dynv6.net:/mnt/usb /Volumes/ajayrpi-usb
   ```

### USB Drive Contents

```bash
$ ls -la /Volumes/ajayrpi-usb/
total 16
drwxr-xr-x  3 root  wheel  4096 Jan 31 23:42 .
drwxr-xr-x  6 root  wheel   192 Jan 31 23:59 ..
drwxr-xr-x  2 1000  1000   4096 Jan 31 23:50 doc

$ ls -la /Volumes/ajayrpi-usb/doc/
total 183
drwxr-xr-x  2 1000  1000    4096 Jan 31 23:50 .
drwxr-xr-x  3 root  wheel   4096 Jan 31 23:42 ..
-rw-rw-r--  1 1000  1000   20171 Jan 31 23:50 dailynews-kindle-delivery-guide.md
-rw-rw-r--  1 1000  1000   65022 Jan 31 23:27 ipv6-dynv6-updater-guide.md
```

---

## Auto-Mount Configuration

### Option 1: Using /etc/fstab

Add entries to `/etc/fstab` for automatic mounting at boot:

```bash
# Edit fstab
sudo nano /etc/fstab

# Add these lines:
ajayrpi.dynv6.net:/home/ajayrpi /Volumes/ajayrpi nfs rw,resvport,nfsvers=3,soft,intr,bg 0 0
ajayrpi.dynv6.net:/mnt/usb /Volumes/ajayrpi-usb nfs rw,resvport,nfsvers=3,soft,intr,bg 0 0
```

**Options explained**:
- `bg` - Mount in background if server is unavailable (prevents boot hang)
- `soft` - Return error on timeout
- `intr` - Allow interrupts

### Option 2: Using autofs (On-Demand Mounting)

Autofs mounts the share only when accessed and unmounts after idle timeout.

1. **Edit `/etc/auto_master`**:
   ```
   /Volumes/nfs auto_nfs
   ```

2. **Create `/etc/auto_nfs`**:
   ```
   ajayrpi -fstype=nfs,resvport,nfsvers=3 ajayrpi.dynv6.net:/home/ajayrpi
   ajayrpi-usb -fstype=nfs,resvport,nfsvers=3 ajayrpi.dynv6.net:/mnt/usb
   ```

3. **Restart autofs**:
   ```bash
   sudo automount -vc
   ```

4. **Access**:
   ```bash
   ls /Volumes/nfs/ajayrpi      # Auto-mounts on access
   ls /Volumes/nfs/ajayrpi-usb  # Auto-mounts on access
   ```

### Option 3: Shell Script

Create a mount script for manual use:

```bash
#!/bin/bash
# ~/bin/mount-ajayrpi.sh

MOUNTS=(
    "ajayrpi.dynv6.net:/home/ajayrpi:/Volumes/ajayrpi"
    "ajayrpi.dynv6.net:/mnt/usb:/Volumes/ajayrpi-usb"
)

for mount_spec in "${MOUNTS[@]}"; do
    IFS=':' read -r server export mountpoint <<< "$mount_spec"

    if mount | grep -q "$mountpoint"; then
        echo "Already mounted: $mountpoint"
    else
        sudo mkdir -p "$mountpoint"
        sudo mount -t nfs -o nfsvers=3,resvport "$server:$export" "$mountpoint"
        echo "Mounted: $mountpoint"
    fi
done
```

---

## Troubleshooting

### Permission Denied When Listing Mount

**Symptom**:
```bash
$ ls /Volumes/ajayrpi/
ls: /Volumes/ajayrpi/: Permission denied
```

**Cause**: The Pi home directory has restrictive permissions (700 = `drwx------`).

**Solution**: Change permissions on the Pi:
```bash
ssh ajayrpi "chmod 755 /home/ajayrpi"
```

### UID Mismatch - Files Show Wrong Owner

**Symptom**: Files appear owned by numeric UID instead of username:
```bash
$ ls -la /Volumes/ajayrpi/
drwxr-xr-x  12 1000  1000    4096 Jan 31 23:42 .
```

**Cause**:
- macOS UID: 501 (ajay.kumar)
- Pi UID: 1000 (ajayrpi)

NFS uses numeric UIDs. Since the UIDs don't match, macOS shows the raw number.

**Solutions**:

1. **Make files world-writable on Pi** (simple but less secure):
   ```bash
   chmod -R o+rw /home/ajayrpi/shared_folder
   ```

2. **Use all_squash in exports** (map all users to one UID):
   ```
   /home/ajayrpi *(rw,sync,all_squash,anonuid=1000,anongid=1000)
   ```

3. **Change UID on Pi to match macOS** (complex, not recommended).

### Connection Refused (Error 61)

**Symptom**:
```bash
mount_nfs: can't mount /home/ajayrpi from ajayrpi.dynv6.net onto /Volumes/ajayrpi: Connection refused
```

**Causes and Solutions**:

| Cause | Solution |
|-------|----------|
| NFS server not running | `ssh ajayrpi "sudo systemctl start nfs-kernel-server"` |
| NFS server not installed | `ssh ajayrpi "sudo apt install nfs-kernel-server"` |
| Export not configured | Add export to `/etc/exports` and run `sudo exportfs -ra` |
| Firewall blocking | Open ports 111 and 2049 |

### Mount Hangs or Times Out

**Symptom**: Mount command hangs indefinitely.

**Causes and Solutions**:

1. **Network unreachable**: Test with `ping6 ajayrpi.dynv6.net`
2. **Use soft mount**: Add `soft,timeo=10` to mount options
3. **Background mount**: Add `bg` option to retry in background

### Stale File Handle

**Symptom**:
```bash
ls: /Volumes/ajayrpi: Stale file handle
```

**Cause**: Server was restarted or export was changed.

**Solution**:
```bash
sudo umount -f /Volumes/ajayrpi
sudo mount -t nfs -o nfsvers=3,resvport ajayrpi.dynv6.net:/home/ajayrpi /Volumes/ajayrpi
```

### Check NFS Server Status

```bash
# On Pi - check if NFS is running
ssh ajayrpi "sudo systemctl status nfs-kernel-server"

# On Pi - check RPC services
ssh ajayrpi "rpcinfo -p localhost"

# On Pi - list active exports
ssh ajayrpi "sudo exportfs -v"

# From macOS - query exports
showmount -e ajayrpi.dynv6.net
```

### Required Ports

| Port | Protocol | Service |
|------|----------|---------|
| 111 | TCP/UDP | portmapper (rpcbind) |
| 2049 | TCP/UDP | nfs |

### Open Firewall on Pi (if using ufw)

```bash
ssh ajayrpi "sudo ufw allow 111 && sudo ufw allow 2049"
```

---

## Complete Setup Log

This section documents the exact commands executed during the initial setup on 2026-01-31.

### 1. Network Connectivity Test

```bash
# IPv4 failed (not routable)
$ ping -c 2 ajayrpi.dynv6.net
PING ajayrpi.dynv6.net (198.168.1.12): 56 data bytes
Request timeout for icmp_seq 0
--- ajayrpi.dynv6.net ping statistics ---
2 packets transmitted, 0 packets received, 100.0% packet loss

# IPv6 succeeded
$ ping6 -c 2 ajayrpi.dynv6.net
PING6(56=40+8+8 bytes) 2401:4900:8f56:cbfa:20e4:fd5d:2a83:c5f5 --> 2401:4900:8f56:cbfa:ba27:ebff:fed2:832d
16 bytes from 2401:4900:8f56:cbfa:ba27:ebff:fed2:832d, icmp_seq=0 hlim=64 time=6.714 ms
16 bytes from 2401:4900:8f56:cbfa:ba27:ebff:fed2:832d, icmp_seq=1 hlim=64 time=9.693 ms
--- ajayrpi.dynv6.net ping6 statistics ---
2 packets transmitted, 2 packets received, 0.0% packet loss
```

### 2. SSH Key Setup

```bash
# Copy SSH key using password
$ sshpass -p 'indu218009' ssh-copy-id -o StrictHostKeyChecking=no ajayrpi@ajayrpi.dynv6.net
/usr/bin/ssh-copy-id: INFO: 1 key(s) remain to be installed

# Add ed25519 key
$ cat ~/.ssh/id_ed25519.pub | ssh -i ~/.ssh/id_mwm ajayrpi@ajayrpi.dynv6.net \
    "mkdir -p ~/.ssh && cat >> ~/.ssh/authorized_keys"

# Verify passwordless access
$ ssh ajayrpi@ajayrpi.dynv6.net "whoami"
ajayrpi
```

### 3. SSH Config Entry

```bash
$ cat >> ~/.ssh/config << 'EOF'

Host ajayrpi
    HostName ajayrpi.dynv6.net
    User ajayrpi
    IdentityFile ~/.ssh/id_ed25519
EOF
```

### 4. NFS Server Installation

```bash
$ ssh ajayrpi@ajayrpi.dynv6.net "sudo apt update && sudo apt install -y nfs-kernel-server"
# ... installation output ...
Setting up nfs-kernel-server (1:2.8.3-1) ...
Created symlink '/etc/systemd/system/multi-user.target.wants/nfs-server.service'
```

### 5. Configure NFS Exports

```bash
# Add home directory export
$ ssh ajayrpi "echo '/home/ajayrpi *(rw,sync,no_subtree_check,insecure,no_root_squash)' | sudo tee /etc/exports"

# Add USB drive export
$ ssh ajayrpi "echo '/mnt/usb *(rw,sync,no_subtree_check,insecure,no_root_squash)' | sudo tee -a /etc/exports"

# Apply and restart
$ ssh ajayrpi "sudo exportfs -ra && sudo systemctl restart nfs-kernel-server"
```

### 6. Fix Home Directory Permissions

```bash
# Original permissions were 700 (drwx------)
$ ssh ajayrpi "chmod 755 /home/ajayrpi"
```

### 7. Create Mount Points on macOS

```bash
$ sudo mkdir -p /Volumes/ajayrpi /Volumes/ajayrpi-usb
```

### 8. Mount NFS Shares

```bash
# Mount home directory
$ sudo mount -t nfs -o nfsvers=3,resvport ajayrpi.dynv6.net:/home/ajayrpi /Volumes/ajayrpi

# Mount USB drive
$ sudo mount -t nfs -o nfsvers=3,resvport ajayrpi.dynv6.net:/mnt/usb /Volumes/ajayrpi-usb
```

### 9. Verify Mounts

```bash
$ mount | grep ajayrpi
ajayrpi.dynv6.net:/home/ajayrpi on /Volumes/ajayrpi (nfs)
ajayrpi.dynv6.net:/mnt/usb on /Volumes/ajayrpi-usb (nfs)

$ ls /Volumes/ajayrpi/
.augment  .bashrc  .cargo  .config  DailyNews  neovim  usb  ...

$ ls /Volumes/ajayrpi-usb/doc/
dailynews-kindle-delivery-guide.md  ipv6-dynv6-updater-guide.md
```

---

## Useful Commands Reference

### macOS Client Commands

```bash
# Show all NFS mounts
mount | grep nfs

# Show mount details
nfsstat -m

# Force unmount
sudo umount -f /Volumes/ajayrpi

# Check what's exported from server
showmount -e ajayrpi.dynv6.net
```

### Raspberry Pi Server Commands

```bash
# Check NFS server status
sudo systemctl status nfs-kernel-server

# List active exports
sudo exportfs -v

# Show connected clients
sudo showmount

# Check RPC services
rpcinfo -p localhost

# View NFS server logs
journalctl -u nfs-kernel-server -f
```

---

## Security Considerations

1. **`no_root_squash`**: Currently enabled, meaning root on macOS has root access on Pi.
   Consider using `root_squash` for better security.

2. **`*` in exports**: Allows any client to connect. Consider restricting to specific IPs:
   ```
   /home/ajayrpi 192.168.1.0/24(rw,sync,no_subtree_check,insecure)
   ```

3. **Password in documentation**: The SSH password is documented here. Consider:
   - Disabling password authentication on Pi (`PasswordAuthentication no` in sshd_config)
   - Using only key-based authentication

4. **Firewall**: Consider enabling ufw on Pi and only allowing necessary ports.

---

## Related Documentation

- [dynv6 Complete Guide](../dynv6-complete-guide.md) - Dynamic DNS setup
- [Remote Dev NFS Solution](../remove-dev/remote-dev-nfs-solution.md) - NFS for development
- [SSH Connectivity Issue IPv6](../remove-dev/ssh-connectivity-issue-ipv6.md) - IPv6 SSH troubleshooting
