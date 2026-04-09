# Arista SSH Agent - Complete Explanation

**Last Updated:** March 24, 2026

---

## What You're Seeing

```bash
~/.ssh/arista-ssh ❯ ls
agent.sock  cli.sock
```

These are **Unix domain sockets** created by the `arista-ssh-agent` daemon to enable SSH access to Arista's Kubernetes pods and internal infrastructure.

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                         YOUR MAC                                 │
│                                                                  │
│  ┌────────────────────────────────────────────────────────┐    │
│  │  arista-ssh-agent (daemon)                              │    │
│  │  PID: 1350                                              │    │
│  │  Running since: Feb 9, 2026                             │    │
│  │                                                          │    │
│  │  Creates two Unix sockets:                              │    │
│  │  • agent.sock  - SSH authentication socket              │    │
│  │  • cli.sock    - CLI communication socket               │    │
│  └────────────────────────────────────────────────────────┘    │
│                           │                                      │
│                           │                                      │
│  ┌────────────────────────▼──────────────────────────────┐     │
│  │  SSH Client (when you run: ssh ap-remote)             │     │
│  │                                                         │     │
│  │  Reads: /etc/ssh/ssh_config.d/09-arista-ssh-agent.conf│     │
│  │                                                         │     │
│  │  Match exec "arista-ssh check-auth --check-host %h"   │     │
│  │     IdentityAgent ~/.ssh/arista-ssh/agent.sock         │     │
│  └────────────────────────────────────────────────────────┘     │
│                           │                                      │
└───────────────────────────┼──────────────────────────────────────┘
                            │
                            │ SSH Connection
                            │ (using certificate from agent.sock)
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│              ARISTA KUBERNETES INFRASTRUCTURE                    │
│                                                                  │
│  Pod: ajaykumar-ajaykrarista-2zfg4                              │
│  (Your remote development environment)                           │
└─────────────────────────────────────────────────────────────────┘
```

---

## How It Works

### 1. **The Daemon Process**

```bash
$ ps aux | grep arista-ssh-agent
ajay.kumar  1350  /usr/local/libexec/arista-ssh-agent \
  --socket path=/Users/ajay.kumar/.ssh/arista-ssh/agent.sock \
  --cli-socket path=/Users/ajay.kumar/.ssh/arista-ssh/cli.sock
```

This daemon:
- Runs continuously in the background
- Manages authentication with Arista's identity provider (OneLogin)
- Provides SSH certificates for accessing Kubernetes pods
- Listens on two Unix sockets for communication

### 2. **The Two Sockets**

#### **agent.sock** - SSH Authentication Socket
- **Type:** Unix domain socket (like a local IPC pipe)
- **Purpose:** Acts as an SSH agent (similar to `ssh-agent`)
- **Used by:** SSH client when connecting to Arista infrastructure
- **Protocol:** SSH agent protocol (RFC 4253)

#### **cli.sock** - CLI Communication Socket
- **Type:** Unix domain socket
- **Purpose:** Communication between `arista-ssh` CLI tool and the agent daemon
- **Used by:** Commands like `arista-ssh login`, `arista-ssh check-auth`

### 3. **System-Wide SSH Configuration**

File: `/etc/ssh/ssh_config.d/09-arista-ssh-agent.conf`

```ssh-config
# Match hosts that are Arista infrastructure
Match exec "/usr/local/bin/arista-ssh check-auth --check-host %h"
   # Only accept SSH certificates (not regular keys)
   PubkeyAcceptedKeyTypes ^ssh-ed25519-cert-v01@openssh.com
   # Use the arista-ssh-agent socket for authentication
   IdentityAgent %d/.ssh/arista-ssh/agent.sock
```

**What this does:**
1. For every SSH connection, runs: `arista-ssh check-auth --check-host <hostname>`
2. If the hostname is an Arista host (e.g., `ajaykumar-ajaykrarista-2zfg4`), the Match succeeds
3. SSH client then uses `~/.ssh/arista-ssh/agent.sock` as the identity agent
4. The agent provides an SSH certificate (not a regular SSH key) for authentication

---

## SSH Certificates vs SSH Keys

### Traditional SSH Keys
```
Your Mac                    Remote Server
┌──────────┐               ┌──────────┐
│ Private  │               │ Public   │
│ Key      │  ─────────>   │ Key in   │
│ id_ed25519│              │authorized│
│          │               │_keys     │
└──────────┘               └──────────┘
```

### SSH Certificates (Arista's Approach)
```
Your Mac                    Certificate Authority        Kubernetes Pod
┌──────────┐               ┌──────────────────┐         ┌──────────┐
│ arista-  │  Login via    │ Arista Identity  │         │ Trusts   │
│ ssh-agent│  ────────>    │ Provider         │         │ CA       │
│          │  OneLogin     │ (OneLogin)       │         │ Public   │
│          │               │                  │         │ Key      │
│          │  <────────    │ Issues short-    │         │          │
│ Receives │  Certificate  │ lived cert       │  SSH    │          │
│ cert     │               │                  │  ─────> │ Accepts  │
│          │               │                  │  cert   │ cert     │
└──────────┘               └──────────────────┘         └──────────┘
```

**Benefits:**
- ✅ Centralized authentication (OneLogin SSO)
- ✅ Short-lived credentials (expire after hours/days)
- ✅ No need to manage individual SSH keys on each pod
- ✅ Automatic revocation when you leave the company
- ✅ Audit trail of who accessed what

---

## Your SSH Config for ap-remote

```ssh-config
Host ap-remote
  HostName ajaykumar-ajaykrarista-2zfg4
  ForwardAgent yes
  User ajay.kumar
  # ... other settings ...
```

When you run `ssh ap-remote`:

1. SSH reads your `~/.ssh/config`
2. SSH reads `/etc/ssh/ssh_config.d/09-arista-ssh-agent.conf`
3. Runs: `arista-ssh check-auth --check-host ajaykumar-ajaykrarista-2zfg4`
4. Check succeeds → uses `agent.sock` for authentication
5. `arista-ssh-agent` provides the SSH certificate
6. SSH connects to the Kubernetes pod using the certificate

---

## Common Commands

### Check if agent is running
```bash
ps aux | grep arista-ssh-agent
```

### Check authentication status
```bash
arista-ssh check-auth
```

### Login (refresh authentication)
```bash
arista-ssh login
```

This will:
- Open your browser
- Authenticate via OneLogin
- Receive a new SSH certificate
- Store it in the agent

### View socket files
```bash
ls -la ~/.ssh/arista-ssh/
# Output:
# srwxr-xr-x  agent.sock  (s = socket)
# srwxr-xr-x  cli.sock
```

---

## Comparison: Docker Containers vs Kubernetes Pods

### Docker Containers on Colima
```bash
# Direct access via docker exec
docker exec -it wifiap /bin/bash

# No special SSH agent needed
# Containers run locally on your Mac's VM
```

### Kubernetes Pods (Arista Infrastructure)
```bash
# SSH access via arista-ssh-agent
ssh ap-remote

# Requires:
# ✓ arista-ssh-agent running
# ✓ Valid authentication session
# ✓ SSH certificate from OneLogin
# ✓ Network access to Kubernetes cluster
```

---

## Can You Use This for Docker Containers?

**Short answer:** No, this is specific to Arista's Kubernetes infrastructure.

**Why not:**
- `arista-ssh-agent` only issues certificates for Arista hosts
- Docker containers on Colima don't have SSH servers by default
- Docker containers are local, don't need certificate-based auth

**For Docker containers, you have simpler options:**
1. `docker exec -it container bash` (what you're already doing)
2. Install SSH server in container + use regular SSH keys
3. Use `colima ssh` then `docker exec` (two-hop)

---

## Troubleshooting

### "Auth session has expired"
```bash
arista-ssh login
```

### Agent not running
```bash
# Check if running
ps aux | grep arista-ssh-agent

# If not, it should auto-start on next SSH attempt
# Or manually start (check with IT for exact command)
```

### Socket files missing
```bash
ls -la ~/.ssh/arista-ssh/
# If missing, restart the agent
```

---

## Summary

The `~/.ssh/arista-ssh/` sockets are part of Arista's **enterprise SSH certificate infrastructure**:

- **agent.sock**: Provides SSH certificates for accessing Kubernetes pods
- **cli.sock**: Communication channel for the `arista-ssh` CLI tool
- **Purpose**: Centralized, secure, auditable access to Arista's development infrastructure
- **Authentication**: OneLogin SSO → SSH certificate → Kubernetes pod access
- **Scope**: Only for Arista infrastructure, not applicable to local Docker containers

This is a sophisticated enterprise solution that's much more secure than traditional SSH key management!

