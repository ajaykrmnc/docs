# SSH Connection Optimization Guide

## Overview

This document explains the SSH optimizations applied to speed up connections to remote hosts.
The primary bottlenecks in SSH connections are:

1. **Key negotiation** - Checking multiple identity files
2. **Authentication delays** - GSSAPI/Kerberos DNS lookups
3. **Connection overhead** - Establishing new TCP connections each time
4. **Encryption negotiation** - Cipher and MAC algorithm selection

---

## Optimizations Applied

### 1. Identity File Specification

```ssh-config
IdentityFile ~/.ssh/id_ed25519
IdentitiesOnly yes
AddKeysToAgent yes
```

**Problem**: By default, SSH tries ALL identity files in `~/.ssh/`:
- `id_rsa`, `id_ecdsa`, `id_ecdsa_sk`, `id_ed25519`, `id_ed25519_sk`, `id_xmss`, `id_dsa`
- Each check adds latency (especially if files don't exist or are encrypted)

**Solution**:
- `IdentityFile` - Specifies exactly which key to use
- `IdentitiesOnly yes` - ONLY use the specified key, ignore others
- `AddKeysToAgent yes` - Cache the key in ssh-agent after first use

**Time saved**: ~0.5-2 seconds per connection

---

### 2. Disable GSSAPI Authentication

```ssh-config
GSSAPIAuthentication no
PreferredAuthentications publickey,keyboard-interactive,password
```

**Problem**: GSSAPI (Kerberos) authentication performs DNS lookups to find the KDC (Key Distribution Center). 
Even if you don't use Kerberos, SSH still attempts this by default.

**What happens**:
1. SSH tries to resolve the hostname to a Kerberos realm
2. DNS lookup for `_kerberos._tcp.<domain>` SRV records
3. Timeout waiting for KDC response (can be 5-30 seconds!)

**Solution**:
- `GSSAPIAuthentication no` - Skip Kerberos entirely
- `PreferredAuthentications` - Explicitly order auth methods

**Time saved**: 5-30 seconds (when KDC is unreachable)

---

### 3. Connection Multiplexing (ControlMaster)

```ssh-config
ControlMaster auto
ControlPath ~/.ssh/sockets/%r@%h-%p
ControlPersist 600
```

**This is the most impactful optimization!**

**Problem**: Each SSH connection requires:
1. TCP 3-way handshake
2. SSH version exchange
3. Key exchange (Diffie-Hellman)
4. User authentication
5. Channel setup

This takes 3-10 seconds even on fast networks.

**Solution**: Connection multiplexing reuses an existing SSH connection.

| Setting | Description |
|---------|-------------|
| `ControlMaster auto` | First connection becomes "master", subsequent ones multiplex through it |
| `ControlPath` | Unix socket location for IPC between SSH processes |
| `ControlPersist 600` | Master stays alive 600 seconds (10 min) after last session ends |

**How it works**:
```
First connection (slow):
  Client ──TCP──> Server ──SSH Handshake──> Authenticated Session
                                                    │
                                             Creates master socket
                                                    │
                                    ~/.ssh/sockets/user@host-22

Second connection (instant):
  Client ──Unix Socket──> Master Process ──Multiplexed Channel──> Server
```

**Time saved**: 5-10 seconds on all subsequent connections!

**Path format explained**:
- `%r` = remote username
- `%h` = hostname
- `%p` = port

---

### 4. Keep-Alive Settings

```ssh-config
ServerAliveInterval 60
ServerAliveCountMax 3
TCPKeepAlive yes
```

**Problem**: Idle connections get terminated by:
- NAT gateways (typically 5-15 min timeout)
- Firewalls (stateful inspection timeouts)
- Load balancers

**Solution**:
- `ServerAliveInterval 60` - Send keep-alive every 60 seconds
- `ServerAliveCountMax 3` - Disconnect after 3 missed responses (180 sec)
- `TCPKeepAlive yes` - Enable TCP-level keep-alives

**Benefit**: Connections stay alive through firewalls/NAT

---

### 5. Connection Timeout

```ssh-config
ConnectTimeout 10
```

**Problem**: Default timeout is very long (~2 minutes). If host is down, you wait forever.

**Solution**: Fail fast after 10 seconds if TCP connection cannot be established.

---

### 6. Compression Settings

```ssh-config
Compression no
```

**When to disable** (our case):
- Fast local networks (LAN, datacenter)
- Low-latency connections
- CPU is the bottleneck

**When to enable**:
- Slow WAN links
- High-latency satellite connections
- Transferring compressible data

---

## Performance Comparison

| Scenario | Before | After |
|----------|--------|-------|
| First connection | ~10-15 sec | ~6 sec |
| Subsequent connections | ~10-15 sec | **~1-2 sec** |
| Connection after idle | Timeout/reconnect | Stays alive |

---

## Socket Directory Setup

The control sockets need a directory:

```bash
mkdir -p ~/.ssh/sockets
chmod 700 ~/.ssh/sockets
```

---

## Troubleshooting

### Check if multiplexing is active
```bash
ssh -O check a4c
```

### Force new connection (bypass master)
```bash
ssh -o ControlMaster=no a4c
```

### Stop the master connection
```bash
ssh -O exit a4c
```

### View active sockets
```bash
ls -la ~/.ssh/sockets/
```

---

## Complete Optimized Config

```ssh-config
Host a4c
    HostName 10.247.213.3
    User ajay.kumar
    IdentityFile ~/.ssh/id_ed25519
    IdentitiesOnly yes
    AddKeysToAgent yes
    GSSAPIAuthentication no
    PreferredAuthentications publickey,keyboard-interactive,password
    ControlMaster auto
    ControlPath ~/.ssh/sockets/%r@%h-%p
    ControlPersist 600
    ServerAliveInterval 60
    ServerAliveCountMax 3
    ConnectTimeout 10
    TCPKeepAlive yes
    Compression no
```

---

## References

- `man ssh_config` - Full SSH client configuration options
- `man ssh` - SSH client manual
- OpenSSH Cookbook: https://en.wikibooks.org/wiki/OpenSSH

