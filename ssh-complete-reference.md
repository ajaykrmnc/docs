# Complete SSH Configuration Reference Guide

## Table of Contents

1. [Introduction to SSH](#introduction-to-ssh)
2. [SSH Architecture and Protocol](#ssh-architecture-and-protocol)
3. [SSH Configuration Files](#ssh-configuration-files)
4. [Host Configuration Block](#host-configuration-block)
5. [Connection Settings](#connection-settings)
6. [Authentication Settings](#authentication-settings)
7. [Identity and Key Management](#identity-and-key-management)
8. [Connection Multiplexing](#connection-multiplexing)
9. [Keep-Alive and Timeout Settings](#keep-alive-and-timeout-settings)
10. [Compression Settings](#compression-settings)
11. [Agent Forwarding](#agent-forwarding)
12. [Security Considerations](#security-considerations)
13. [Network and Firewall Considerations](#network-and-firewall-considerations)
14. [Troubleshooting Guide](#troubleshooting-guide)
15. [Best Practices](#best-practices)
16. [Complete Configuration Examples](#complete-configuration-examples)

---

# Chapter 1: Introduction to SSH

## What is SSH?

SSH (Secure Shell) is a cryptographic network protocol designed for secure communication
between two networked computers. It was developed in 1995 by Tatu Ylönen as a replacement
for insecure protocols like Telnet, rlogin, and FTP.

### The Problem SSH Solves

Before SSH, system administrators used protocols that transmitted data in plaintext:

```
┌─────────────┐                              ┌─────────────┐
│   Client    │ ──── Telnet (Plaintext) ───> │   Server    │
│             │                              │             │
│ Password:   │ ──── "mypassword123" ──────> │             │
│ secret123   │                              │             │
└─────────────┘                              └─────────────┘
                         │
                         │ Attacker can intercept!
                         ▼
                  ┌─────────────┐
                  │  Eavesdrop  │
                  │  Captured:  │
                  │ "password123"│
                  └─────────────┘
```

With SSH, all communication is encrypted:

```
┌─────────────┐                              ┌─────────────┐
│   Client    │ ──── SSH (Encrypted) ──────> │   Server    │
│             │                              │             │
│ Password:   │ ──── "aX9#kL2$mN..." ──────> │             │
│ secret123   │      (encrypted blob)        │             │
└─────────────┘                              └─────────────┘
                         │
                         │ Attacker sees gibberish!
                         ▼
                  ┌─────────────┐
                  │  Eavesdrop  │
                  │  Captured:  │
                  │ "aX9#kL2$mN"│
                  │  (useless)  │
                  └─────────────┘
```

### Core Capabilities of SSH

1. **Secure Remote Login**: Access command-line interface of remote machines
2. **Secure File Transfer**: SCP (Secure Copy) and SFTP (SSH File Transfer Protocol)
3. **Port Forwarding**: Tunnel other protocols through SSH (local, remote, dynamic)
4. **X11 Forwarding**: Run graphical applications remotely
5. **Agent Forwarding**: Use local SSH keys on remote machines
6. **SOCKS Proxy**: Create encrypted proxy tunnels

### SSH Versions

| Version | Year | Status | Notes |
|---------|------|--------|-------|
| SSH-1   | 1995 | Deprecated | Security vulnerabilities, do not use |
| SSH-2   | 2006 | Current | Complete redesign, secure |

SSH-2 is the only version you should use. SSH-1 has known cryptographic weaknesses.

---

# Chapter 2: SSH Architecture and Protocol

## The Three Layers of SSH

SSH protocol consists of three layers, each with specific responsibilities:

```
┌─────────────────────────────────────────────────────────────┐
│                    APPLICATION LAYER                        │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐         │
│  │   Remote    │  │    File     │  │    Port     │         │
│  │   Shell     │  │  Transfer   │  │  Forwarding │         │
│  └─────────────┘  └─────────────┘  └─────────────┘         │
├─────────────────────────────────────────────────────────────┤
│              SSH CONNECTION PROTOCOL (RFC 4254)             │
│  - Multiplexes encrypted tunnel into logical channels       │
│  - Handles channel requests, flow control                   │
├─────────────────────────────────────────────────────────────┤
│           SSH USER AUTHENTICATION PROTOCOL (RFC 4252)       │
│  - Authenticates client to server                           │
│  - Methods: publickey, password, keyboard-interactive       │
├─────────────────────────────────────────────────────────────┤
│              SSH TRANSPORT LAYER PROTOCOL (RFC 4253)        │
│  - Server authentication (host key verification)            │
│  - Key exchange (Diffie-Hellman, ECDH)                      │
│  - Encryption (AES, ChaCha20)                               │
│  - Integrity (HMAC-SHA2, Poly1305)                          │
│  - Compression (optional, zlib)                             │
├─────────────────────────────────────────────────────────────┤
│                     TCP/IP (Port 22)                        │
└─────────────────────────────────────────────────────────────┘
```

## SSH Connection Lifecycle

Understanding the connection lifecycle helps you identify bottlenecks:

### Phase 1: TCP Connection (0.5-2 seconds typically)

```
Client                                          Server
   │                                               │
   │ ────────── SYN ─────────────────────────────> │
   │                                               │
   │ <───────── SYN-ACK ────────────────────────── │
   │                                               │
   │ ────────── ACK ─────────────────────────────> │
   │                                               │
   │            TCP Connection Established         │
   │                                               │
```

### Phase 2: Protocol Version Exchange (instant)

```
Client                                          Server

### Phase 4: User Authentication (1-10+ seconds)

This phase can be the SLOWEST if misconfigured:

```
Client                                          Server
   │                                               │
   │ ─────── SSH_MSG_SERVICE_REQUEST ───────────> │
   │         "ssh-userauth"                        │
   │                                               │
   │ <────── SSH_MSG_SERVICE_ACCEPT ──────────────│
   │                                               │
   │ ─────── SSH_MSG_USERAUTH_REQUEST ──────────> │
   │         method: "publickey"                   │
   │         key: ed25519 public key               │
   │                                               │
   │ <────── SSH_MSG_USERAUTH_SUCCESS ────────────│
   │         (or FAILURE, try next method)         │
   │                                               │
```

**Why authentication can be slow:**

1. **Multiple key attempts**: SSH tries each identity file
2. **GSSAPI/Kerberos**: DNS lookups for KDC
3. **Server-side delays**: PAM, LDAP, 2FA verification

### Phase 5: Channel Setup (instant)

```
Client                                          Server
   │                                               │
   │ ─────── SSH_MSG_CHANNEL_OPEN ──────────────> │
   │         "session"                             │
   │                                               │
   │ <────── SSH_MSG_CHANNEL_OPEN_CONFIRMATION ───│
   │                                               │
   │ ─────── SSH_MSG_CHANNEL_REQUEST ───────────> │
   │         "shell" or "exec"                     │
   │                                               │
   │         Interactive Session Ready             │
   │                                               │
```

## Total Connection Time Breakdown

| Phase | Typical Time | With Optimization |
|-------|--------------|-------------------|
| TCP Handshake | 50-500ms | Same |
| Version Exchange | 10ms | Same |
| Key Exchange | 100-500ms | Same |
| User Auth | 500ms-30s | 100-500ms |
| Channel Setup | 50ms | Same |
| **Total** | **1-30+ seconds** | **300ms-1.5s** |

With **Connection Multiplexing**, phases 1-4 are SKIPPED for subsequent connections!

---

# Chapter 3: SSH Configuration Files

## Configuration File Hierarchy

SSH reads configuration from multiple sources in this order:

```
Priority (highest to lowest):
┌─────────────────────────────────────────────────────────────┐
│ 1. Command-line options (-o Option=value)                   │
├─────────────────────────────────────────────────────────────┤
│ 2. User configuration (~/.ssh/config)                       │
├─────────────────────────────────────────────────────────────┤
│ 3. System configuration (/etc/ssh/ssh_config)               │
├─────────────────────────────────────────────────────────────┤
│ 4. System configuration includes (/etc/ssh/ssh_config.d/*)  │
├─────────────────────────────────────────────────────────────┤
│ 5. Compiled-in defaults                                     │
└─────────────────────────────────────────────────────────────┘
```

**Important**: First match wins! If an option is set at a higher priority level,
lower priority settings for that same option are ignored.

## User Configuration File: ~/.ssh/config

This is YOUR personal SSH configuration. Create it if it doesn't exist:

```bash
touch ~/.ssh/config
chmod 600 ~/.ssh/config
```

### File Permissions (Critical for Security)

SSH enforces strict permissions on configuration files:

```
File/Directory          Required Permissions    Why
─────────────────────────────────────────────────────────────
~/.ssh/                 700 (drwx------)        Only owner can access
~/.ssh/config           600 (-rw-------)        Only owner can read/write
~/.ssh/id_*             600 (-rw-------)        Private keys must be protected
~/.ssh/id_*.pub         644 (-rw-r--r--)        Public keys can be shared
~/.ssh/known_hosts      644 (-rw-r--r--)        Host keys
~/.ssh/authorized_keys  600 (-rw-------)        Server-side (who can login)
```

If permissions are wrong, SSH will refuse to use the file:

```
@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
@         WARNING: UNPROTECTED PRIVATE KEY FILE!          @
@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
Permissions 0644 for '/Users/user/.ssh/id_rsa' are too open.
It is required that your private key files are NOT accessible by others.
```

### Configuration File Syntax

```ssh-config
# Comments start with hash
# Blank lines are ignored

# Host block - applies to matching hosts
Host hostname-pattern
    Option1 value1
    Option2 value2

# Multiple patterns
Host server1 server2 *.example.com
    User admin

# Wildcard pattern (matches everything)
Host *
    Option value
```

### Pattern Matching Rules

| Pattern | Matches | Example |
|---------|---------|---------|
| `*` | Any string | `Host *` matches all hosts |
| `?` | Single character | `Host server?` matches server1, server2 |
| `!` | Negation | `Host * !github.com` matches all except github |
| `192.168.*.*` | IP wildcards | Matches 192.168.0.0/16 |

### Order of Host Blocks Matters!

```ssh-config
# CORRECT ORDER: Specific first, general last

Host myserver
    User admin
    Port 2222

Host *.example.com
    User deploy
    IdentityFile ~/.ssh/deploy_key

Host *
    ServerAliveInterval 60
    AddKeysToAgent yes
```

```ssh-config
# WRONG ORDER: General first (overrides everything)

Host *
    User default_user    # This User will be used for ALL hosts!

Host myserver
    User admin           # IGNORED! Already set above.
```

---

# Chapter 4: Host Configuration Block

## The Host Directive

The `Host` directive begins a configuration block that applies to matching hostnames.

### Syntax

```ssh-config
Host pattern1 [pattern2] [pattern3] ...
    Option1 value1
    Option2 value2
```

### How Host Matching Works

When you run `ssh myserver`, SSH:

1. Reads the config file from top to bottom
2. For each `Host` block, checks if "myserver" matches the pattern
3. If it matches, applies ALL options in that block
4. Continues to next block (doesn't stop at first match!)
5. First value wins for each option

```
Example: ssh production-web-01

Config file:
┌─────────────────────────────────────────┐
│ Host production-*                       │  ← Matches! Apply options
│     User deploy                         │
│     IdentityFile ~/.ssh/prod_key        │
├─────────────────────────────────────────┤
│ Host *-web-*                            │  ← Matches! Apply options
│     Port 2222                           │
├─────────────────────────────────────────┤
│ Host *                                  │  ← Matches! Apply options
│     ServerAliveInterval 60              │
│     User default                        │  ← IGNORED (User already set)
└─────────────────────────────────────────┘

Final effective configuration:
  User = deploy (from production-*)
  IdentityFile = ~/.ssh/prod_key (from production-*)
  Port = 2222 (from *-web-*)
  ServerAliveInterval = 60 (from *)
```

## HostName Directive

**Purpose**: Specifies the actual hostname or IP address to connect to.

### Syntax

```ssh-config
Host alias
    HostName actual.hostname.or.ip.address
```

### Why Use HostName?

1. **Create short aliases**:
   ```ssh-config
   Host prod
       HostName production-server-us-east-1.company.internal.example.com
   ```
   Now `ssh prod` connects to the long hostname.

2. **Connect by IP when DNS is unreliable**:
   ```ssh-config
   Host myserver
       HostName 10.247.213.3
   ```

3. **Use different names for same server**:
   ```ssh-config
   Host work-server
       HostName 192.168.1.100
       User work_account

   Host personal-server
       HostName 192.168.1.100
       User personal_account
   ```

### Token Substitution

You can use tokens in HostName:

| Token | Expands To |
|-------|------------|
| `%h` | Original hostname from command line |
| `%n` | Original hostname (same as %h for HostName) |
| `%%` | Literal % character |

```ssh-config
# Jump through bastion
Host *.internal
    HostName %h
    ProxyJump bastion.example.com
```

## User Directive

**Purpose**: Specifies the username for the remote connection.

### Syntax

```ssh-config
Host server
    User username
```

### Without User Directive

If not specified, SSH uses your local username:

```bash
# If logged in as "ajay.kumar" locally
ssh myserver
# Equivalent to: ssh ajay.kumar@myserver
```

### Examples

```ssh-config
# Different users for different servers
Host github.com
    User git                    # GitHub always uses "git" user

Host production-*
    User deploy                 # Production servers use deploy account

Host raspberry-pi
    User pi                     # Default Raspberry Pi user

Host *
    User ajay.kumar             # Default for everything else
```

---

# Chapter 5: Connection Settings

## ConnectTimeout

**Purpose**: Maximum time to wait for TCP connection to establish.

### Syntax

```ssh-config
ConnectTimeout seconds
```

### Default Value

The default is system TCP timeout, typically 75-120 seconds.

### How It Works

```
┌──────────┐                              ┌──────────┐
│  Client  │ ────── SYN ────────────────> │  Server  │
│          │                              │  (down)  │
│          │         ... waiting ...      │          │
│          │                              │          │
│          │  ConnectTimeout expires!     │          │
│          │  "Connection timed out"      │          │
└──────────┘                              └──────────┘
```

### Recommended Values

| Scenario | Value | Rationale |
|----------|-------|-----------|
| Local network | 5-10 | Fast failure for debugging |
| Internet servers | 15-30 | Allow for latency |
| Unreliable networks | 30-60 | More tolerance |
| Scripts/automation | 10-15 | Fail fast, retry logic |

### Example

```ssh-config
Host critical-server
    ConnectTimeout 5            # Fail fast, I have retry logic

Host overseas-server
    ConnectTimeout 30           # High latency expected

Host *
    ConnectTimeout 10           # Reasonable default
```

## TCPKeepAlive

**Purpose**: Enable TCP-level keepalive packets to detect dead connections.

### Syntax

```ssh-config
TCPKeepAlive yes|no
```

### Default Value

`yes`

### How It Works

TCP keepalives are handled by the operating system kernel:

```
┌──────────┐                              ┌──────────┐
│  Client  │                              │  Server  │
│          │ ──── TCP Keepalive Probe ──> │          │
│          │ <─── TCP Keepalive ACK ───── │          │
│          │                              │          │
│          │       (every ~2 hours        │          │
│          │        by default)           │          │
└──────────┘                              └──────────┘
```

### TCPKeepAlive vs ServerAliveInterval

| Feature | TCPKeepAlive | ServerAliveInterval |
|---------|--------------|---------------------|
| Layer | TCP (kernel) | SSH (application) |
| Interval | System default (~2 hours) | Configurable |
| Encrypted | No | Yes |
| Spoofable | Yes | No |
| Through NAT | May fail | Works reliably |

### Recommendation

Use BOTH for maximum reliability:

```ssh-config
Host *
    TCPKeepAlive yes            # Kernel-level backup
    ServerAliveInterval 60      # Application-level primary
```

## Port

**Purpose**: Specifies the port number to connect to on the remote host.

### Syntax

```ssh-config
Port port_number
```

### Default Value

`22` (standard SSH port)

### When to Change

1. **Server runs SSH on non-standard port** (security through obscurity):
   ```ssh-config
   Host secure-server
       Port 2222
   ```

2. **Port forwarding scenarios**:
   ```ssh-config
   Host tunneled-server
       HostName localhost
       Port 10022              # Local port forwarded to remote SSH
   ```

3. **Different services on same host**:
   ```ssh-config
   Host git-server
       HostName myserver.com
       Port 22

   Host sftp-server
       HostName myserver.com
       Port 2222
   ```

---

# Chapter 6: Authentication Settings

## Understanding SSH Authentication Methods

SSH supports multiple authentication methods, tried in order:

```
┌─────────────────────────────────────────────────────────────┐
│                 Authentication Methods                       │
├─────────────────────────────────────────────────────────────┤
│  1. publickey        - Cryptographic key pair               │
│  2. gssapi-with-mic  - Kerberos/GSSAPI                      │
│  3. keyboard-interactive - Challenge-response (2FA, OTP)   │
│  4. password         - Simple password                      │
│  5. hostbased        - Trust based on client hostname       │
└─────────────────────────────────────────────────────────────┘
```

## GSSAPIAuthentication

**Purpose**: Enable/disable GSSAPI (Kerberos) authentication.

### Syntax

```ssh-config
GSSAPIAuthentication yes|no
```

### Default Value

`yes` on most systems (unfortunately, this causes delays!)

### What is GSSAPI/Kerberos?

GSSAPI (Generic Security Services Application Program Interface) is a framework
for providing security services. Kerberos is the most common GSSAPI mechanism.

```
Kerberos Authentication Flow:

┌──────────┐     ┌─────────────┐     ┌──────────┐
│  Client  │     │     KDC     │     │  Server  │
│          │     │ (Key Dist   │     │          │
│          │     │   Center)   │     │          │
└────┬─────┘     └──────┬──────┘     └────┬─────┘
     │                  │                 │
     │  1. Request TGT  │                 │
     │ ───────────────> │                 │
     │                  │                 │
     │  2. TGT          │                 │
     │ <─────────────── │                 │
     │                  │                 │
     │  3. Request Service Ticket         │
     │ ───────────────> │                 │
     │                  │                 │
     │  4. Service Ticket                 │
     │ <─────────────── │                 │
     │                  │                 │
     │  5. Authenticate with ticket       │
     │ ─────────────────────────────────> │
     │                  │                 │
```

### Why GSSAPI Causes Slowness

When GSSAPI is enabled, SSH performs these steps BEFORE trying other auth methods:

1. **DNS Lookup**: Resolve hostname to find Kerberos realm
2. **SRV Record Query**: Look for `_kerberos._tcp.DOMAIN`
3. **KDC Connection**: Try to contact Key Distribution Center
4. **Timeout**: Wait for KDC response (5-30 seconds if unreachable!)

```
Timeline with GSSAPI enabled (no Kerberos infrastructure):

0s ─────────────────────────────────────────────────────────>
   │
   │ DNS lookup for kerberos realm...
   │ Trying to contact KDC...
   │ ... waiting ...
   │ ... waiting ...
   │ Timeout! (5-30 seconds wasted)
   │
   │ Now trying publickey authentication...
   │ Success! (would have been instant)
   │
30s ────────────────────────────────────────────────────────>
```

### Recommendation

**Disable GSSAPI unless you actually use Kerberos:**

```ssh-config
Host *
    GSSAPIAuthentication no
```

**Time saved**: 5-30 seconds per connection!

## PreferredAuthentications

**Purpose**: Specify the order and selection of authentication methods.

### Syntax

```ssh-config
PreferredAuthentications method1,method2,method3
```

### Available Methods

| Method | Description | Speed |
|--------|-------------|-------|
| `publickey` | SSH key pair | Fast |
| `gssapi-with-mic` | Kerberos | Slow if no KDC |
| `keyboard-interactive` | Challenge-response | Medium |
| `password` | Password prompt | Medium |
| `hostbased` | Host-to-host trust | Fast |

### Default Order

```
gssapi-with-mic,publickey,keyboard-interactive,password
```

Notice GSSAPI is FIRST! This is why connections are slow by default.

### Optimized Order

```ssh-config
Host *
    PreferredAuthentications publickey,keyboard-interactive,password
```

Benefits:
- GSSAPI is removed entirely
- Tries fast `publickey` first
- Falls back to interactive/password if needed

### Examples

```ssh-config
# Key-only servers (most secure)
Host production-*
    PreferredAuthentications publickey

# Servers requiring 2FA
Host secure-*
    PreferredAuthentications publickey,keyboard-interactive

# Legacy servers with password auth
Host legacy-*
    PreferredAuthentications password

# General purpose
Host *
    PreferredAuthentications publickey,keyboard-interactive,password
```

## PasswordAuthentication

**Purpose**: Enable or disable password authentication.

### Syntax

```ssh-config
PasswordAuthentication yes|no
```

### Default Value

`yes`

### Security Implications

```
Password Auth:                     Key Auth:
┌────────────┐                    ┌────────────┐
│  Guessable │                    │ 256+ bits  │
│  "password │                    │ of entropy │
│   123"     │                    │            │
└────────────┘                    └────────────┘
     │                                  │
     ▼                                  ▼
 Brute-force                      Computationally
   attacks                          infeasible
   possible                         to crack
```

### Recommendation

Disable password auth when using keys:

```ssh-config
Host secure-servers
    PasswordAuthentication no
    PreferredAuthentications publickey
```

---

# Chapter 7: Identity and Key Management

## Understanding SSH Key Types

```
┌─────────────────────────────────────────────────────────────────┐
│                    SSH Key Types Comparison                      │
├──────────┬──────────┬──────────┬────────────────────────────────┤
│ Type     │ Key Size │ Security │ Notes                          │
├──────────┼──────────┼──────────┼────────────────────────────────┤
│ RSA      │ 2048-4096│ Good     │ Widely compatible, larger keys │
│ ECDSA    │ 256-521  │ Good     │ Smaller, faster                │
│ Ed25519  │ 256      │ Excellent│ Best choice, fast, secure      │
│ DSA      │ 1024     │ Weak     │ DEPRECATED, do not use!        │
└──────────┴──────────┴──────────┴────────────────────────────────┘
```

### Ed25519 (Recommended)

```bash
# Generate Ed25519 key
ssh-keygen -t ed25519 -C "your_email@example.com"
```

**Advantages:**
- Fixed 256-bit key size (simpler)
- Faster signing and verification
- Resistant to timing attacks
- Smaller key/signature size
- Modern, secure algorithm

### RSA (Legacy Compatibility)

```bash
# Generate RSA key (4096-bit for security)
ssh-keygen -t rsa -b 4096 -C "your_email@example.com"
```

**When to use:**
- Old servers that don't support Ed25519
- Compliance requirements mandating RSA

## IdentityFile

**Purpose**: Specify which private key file to use for authentication.

### Syntax

```ssh-config
IdentityFile path/to/private_key
```

### Default Identity Files

SSH tries these files by default (in order):

```
~/.ssh/id_dsa        (deprecated)
~/.ssh/id_ecdsa
~/.ssh/id_ecdsa_sk   (security key)
~/.ssh/id_ed25519
~/.ssh/id_ed25519_sk (security key)
~/.ssh/id_rsa
~/.ssh/id_xmss
```

### Why Specify IdentityFile?

1. **Speed**: Skip checking other keys
2. **Clarity**: Know which key is used
3. **Multiple keys**: Different keys for different servers

```ssh-config
# Work servers use work key
Host *.company.com
    IdentityFile ~/.ssh/work_ed25519

# Personal projects use personal key
Host github.com-personal
    IdentityFile ~/.ssh/personal_ed25519

# Specific server uses specific key
Host legacy-server
    IdentityFile ~/.ssh/legacy_rsa
```

### Using Multiple Identity Files

You can specify multiple identity files for fallback:

```ssh-config
Host someserver
    IdentityFile ~/.ssh/primary_key
    IdentityFile ~/.ssh/backup_key
```

SSH will try each key in order until one succeeds.

## IdentitiesOnly

**Purpose**: Use ONLY the explicitly specified identity files.

### Syntax

```ssh-config
IdentitiesOnly yes|no
```

### Default Value

`no`

### How It Works

```
IdentitiesOnly no (default):
┌─────────────────────────────────────────────────────────────┐
│ SSH tries:                                                  │
│  1. Keys from ssh-agent                                     │
│  2. Keys specified by IdentityFile                          │
│  3. Default identity files (~/.ssh/id_*)                    │
└─────────────────────────────────────────────────────────────┘

IdentitiesOnly yes:
┌─────────────────────────────────────────────────────────────┐
│ SSH tries ONLY:                                             │
│  1. Keys specified by IdentityFile                          │
│  (ssh-agent keys only if they match IdentityFile)           │
└─────────────────────────────────────────────────────────────┘
```

### Why Use IdentitiesOnly?

1. **Prevent "too many authentication failures"**

   Some servers limit authentication attempts:
   ```
   Received disconnect: Too many authentication failures
   ```

   If you have 10 keys in ssh-agent, SSH tries all 10!
   With `IdentitiesOnly yes`, it only tries the specified key.

2. **Security**: Prevent accidentally sending wrong key
3. **Speed**: Faster authentication

### Recommended Configuration

```ssh-config
Host github.com
    IdentityFile ~/.ssh/github_key
    IdentitiesOnly yes           # Only use github_key, nothing else

Host work-*
    IdentityFile ~/.ssh/work_key
    IdentitiesOnly yes
```

## AddKeysToAgent

**Purpose**: Automatically add keys to ssh-agent after first use.

### Syntax

```ssh-config
AddKeysToAgent yes|no|confirm|ask|time
```

### Values

| Value | Behavior |
|-------|----------|
| `no` | Don't add keys |
| `yes` | Add keys automatically |
| `confirm` | Add, but require confirmation for each use |
| `ask` | Ask before adding |
| `30m` | Add with 30-minute lifetime |

### How It Works

```
First SSH connection:
┌──────────┐                              ┌──────────┐
│  Client  │                              │  Agent   │
│          │                              │(ssh-agent)│
│ 1. Read key from disk                   │          │
│ 2. Decrypt key (enter passphrase)       │          │
│ 3. Use key for authentication           │          │
│ 4. AddKeysToAgent=yes:                  │          │
│    ─────── "Store this key" ──────────> │          │
│                                          │ [stored] │
└──────────┘                              └──────────┘

Subsequent connections:
┌──────────┐                              ┌──────────┐
│  Client  │                              │  Agent   │
│          │ <───── "Here's the key" ─────│          │
│          │   (no passphrase needed!)    │          │
└──────────┘                              └──────────┘
```

### Recommended Configuration

```ssh-config
Host *
    AddKeysToAgent yes           # Convenience: type passphrase once
```

With time limit (more secure):

```ssh-config
Host *
    AddKeysToAgent 4h            # Key expires after 4 hours
```
   │                                               │
```

### Phase 3: Key Exchange (1-3 seconds)

This is where cryptographic parameters are negotiated:

```
Client                                          Server
   │                                               │
   │ ─────── SSH_MSG_KEXINIT ────────────────────> │
   │  (supported algorithms list)                  │
   │                                               │
   │ <────── SSH_MSG_KEXINIT ─────────────────────│
   │  (supported algorithms list)                  │
   │                                               │
   │         Algorithm Negotiation:                │
   │         - Key Exchange: ecdh-sha2-nistp256    │
   │         - Host Key: ssh-ed25519               │
   │         - Cipher: aes256-gcm                  │
   │         - MAC: implicit (GCM mode)            │
   │                                               │
   │ ─────── ECDH Public Key ───────────────────> │
   │                                               │
   │ <────── ECDH Public Key + Host Key ──────────│
   │         + Signature                           │
   │                                               │
   │        Both derive shared secret              │
   │        Encryption keys established            │
   │                                               │
```

