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
### Phase 4: User Authentication (1-10+ seconds)
```
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

`
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


---

# Chapter 8: Connection Multiplexing (ControlMaster)

## The Most Impactful Optimization

Connection multiplexing is the single most effective way to speed up SSH.
It allows multiple SSH sessions to share a single TCP connection.

## How Normal SSH Works (Without Multiplexing)

```
Session 1: ssh server "command1"
┌─────────────────────────────────────────────────────────────┐
│ TCP Handshake → Key Exchange → Auth → Execute → Close      │
│                        ~5-10 seconds                        │
└─────────────────────────────────────────────────────────────┘

Session 2: ssh server "command2"
┌─────────────────────────────────────────────────────────────┐
│ TCP Handshake → Key Exchange → Auth → Execute → Close      │
│                        ~5-10 seconds                        │
└─────────────────────────────────────────────────────────────┘

Session 3: ssh server "command3"
┌─────────────────────────────────────────────────────────────┐
│ TCP Handshake → Key Exchange → Auth → Execute → Close      │
│                        ~5-10 seconds                        │
└─────────────────────────────────────────────────────────────┘

Total time: ~15-30 seconds
```

## How Multiplexing Works

```
Session 1 (Master): ssh server "command1"
┌─────────────────────────────────────────────────────────────┐
│ TCP Handshake → Key Exchange → Auth → Execute              │
│                        ~5-10 seconds                        │
│                                                             │
│                   Creates control socket:                   │
│               ~/.ssh/sockets/user@server-22                 │
│                                                             │
│                 ┌─────────────────────┐                     │
│                 │   Master Process    │                     │
│                 │  (stays running)    │                     │
│                 └─────────────────────┘                     │
└─────────────────────────────────────────────────────────────┘

Session 2 (Slave): ssh server "command2"
┌─────────────────────────────────────────────────────────────┐
│ Connect to control socket → Multiplex channel → Execute    │
│                        ~0.1-0.5 seconds!                    │
└─────────────────────────────────────────────────────────────┘

Session 3 (Slave): ssh server "command3"
┌─────────────────────────────────────────────────────────────┐
│ Connect to control socket → Multiplex channel → Execute    │
│                        ~0.1-0.5 seconds!                    │
└─────────────────────────────────────────────────────────────┘

Total time: ~5-11 seconds (vs 15-30 without multiplexing)
```

## ControlMaster

**Purpose**: Enable connection sharing.

### Syntax

```ssh-config
ControlMaster auto|yes|no|ask|autoask
```

### Values Explained

| Value | Behavior |
|-------|----------|
| `no` | Disable multiplexing |
| `yes` | Always be the master (fails if master exists) |
| `auto` | Become master if none exists, otherwise be slave |
| `ask` | Like `yes`, but ask before becoming master |
| `autoask` | Like `auto`, but ask before becoming master |

### Recommended Value

```ssh-config
ControlMaster auto
```

Why `auto`?
- First connection becomes master automatically
- Subsequent connections become slaves automatically
- No manual intervention needed

### How ControlMaster Works Internally

```
┌─────────────────────────────────────────────────────────────┐
│                      FIRST CONNECTION                        │
│                                                             │
│  $ ssh server                                               │
│      │                                                      │
│      ▼                                                      │
│  Check: Does control socket exist?                          │
│      │                                                      │
│      ▼ NO                                                   │
│  Create new TCP connection to server                        │
│      │                                                      │
│      ▼                                                      │
│  Perform full SSH handshake                                 │
│      │                                                      │
│      ▼                                                      │
│  Create Unix domain socket at ControlPath                   │
│      │                                                      │
│      ▼                                                      │
│  Fork: Parent becomes "master", child handles session       │
│      │                                                      │
│      ▼                                                      │
│  Master listens on control socket for new connections       │
│                                                             │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│                    SUBSEQUENT CONNECTION                     │
│                                                             │
│  $ ssh server                                               │
│      │                                                      │
│      ▼                                                      │
│  Check: Does control socket exist?                          │
│      │                                                      │
│      ▼ YES                                                  │
│  Connect to Unix socket (local IPC, instant)                │
│      │                                                      │
│      ▼                                                      │
│  Request new channel from master                            │
│      │                                                      │
│      ▼                                                      │
│  Master opens new channel on existing TCP connection        │
│      │                                                      │
│      ▼                                                      │
│  Session ready! (no TCP handshake, no auth)                 │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

## ControlPath

**Purpose**: Specify the location of the control socket file.

### Syntax

```ssh-config
ControlPath path_with_tokens
```

### Token Substitutions

| Token | Meaning | Example |
|-------|---------|---------|
| `%r` | Remote username | ajay.kumar |
| `%h` | Remote hostname | 10.247.213.3 |
| `%p` | Remote port | 22 |
| `%l` | Local hostname | macbook.local |
| `%L` | Local hostname (short) | macbook |
| `%n` | Original hostname | myalias |
| `%C` | Hash of %l%h%p%r | a1b2c3d4... |
| `%%` | Literal % | % |

### Recommended ControlPath

```ssh-config
ControlPath ~/.ssh/sockets/%r@%h-%p
```

This creates paths like:
```
~/.ssh/sockets/ajay.kumar@10.247.213.3-22
~/.ssh/sockets/root@192.168.1.1-22
~/.ssh/sockets/deploy@production.example.com-2222
```

### Why Include All Components?

```
%r (user)   - Different users = different sessions
%h (host)   - Different hosts = different sessions
%p (port)   - Different ports = different sessions (SSH on 22 vs 2222)
```

### Alternative: Using Hash

For very long hostnames, the path might exceed filesystem limits.
Use `%C` to create a fixed-length hash:

```ssh-config
ControlPath ~/.ssh/sockets/%C
```

Creates paths like:
```
~/.ssh/sockets/a1b2c3d4e5f6789012345678901234567890abcd
```

### Socket Directory Setup

**Important**: Create the sockets directory first!

```bash
mkdir -p ~/.ssh/sockets
chmod 700 ~/.ssh/sockets
```

Without this directory, you'll see:
```
muxserver_listen: mkdir /Users/user/.ssh/sockets failed: No such file or directory
```

## ControlPersist

**Purpose**: Keep the master connection alive after the initial session closes.

### Syntax

```ssh-config
ControlPersist yes|no|time
```

### Values

| Value | Behavior |
|-------|----------|
| `no` | Close master when last session closes |
| `yes` | Keep master alive indefinitely |
| `600` | Keep master alive for 600 seconds (10 minutes) |
| `30m` | Keep master alive for 30 minutes |
| `2h` | Keep master alive for 2 hours |

### How ControlPersist Works

```
Without ControlPersist (or ControlPersist no):
┌─────────────────────────────────────────────────────────────┐
│                                                             │
│  Session 1 starts (master created)                          │
│      │                                                      │
│      ▼                                                      │
│  Session 2 starts (slave)                                   │
│      │                                                      │
│      ▼                                                      │
│  Session 1 closes                                           │
│      │                                                      │
│      ▼                                                      │
│  Session 2 closes                                           │
│      │                                                      │
│      ▼                                                      │
│  Master closes immediately ← No persistence                 │
│      │                                                      │
│      ▼                                                      │
│  Session 3 starts: Full handshake required again!           │
│                                                             │
└─────────────────────────────────────────────────────────────┘

With ControlPersist 600:
┌─────────────────────────────────────────────────────────────┐
│                                                             │
│  Session 1 starts (master created)                          │
│      │                                                      │
│      ▼                                                      │
│  Session 1 closes                                           │
│      │                                                      │
│      ▼                                                      │
│  Master stays alive in background                           │
│  (timer starts: 600 seconds)                                │
│      │                                                      │
│     ... 5 minutes later ...                                 │
│      │                                                      │
│      ▼                                                      │
│  Session 2 starts: Instant! (uses existing master)          │
│      │                                                      │
│      ▼                                                      │
│  Session 2 closes                                           │
│      │                                                      │
│      ▼                                                      │
│  (timer resets: 600 seconds)                                │
│      │                                                      │
│     ... 10+ minutes of no activity ...                      │
│      │                                                      │
│      ▼                                                      │
│  Master closes (timeout expired)                            │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### Recommended Value

```ssh-config
ControlPersist 600    # 10 minutes
```

Why 600 seconds?
- Long enough for typical work sessions
- Short enough to not waste resources
- Good balance between convenience and security

### Complete Multiplexing Configuration

```ssh-config
Host *
    ControlMaster auto
    ControlPath ~/.ssh/sockets/%r@%h-%p
    ControlPersist 600
```

### Managing Master Connections

**Check if master is running:**
```bash
ssh -O check hostname
# Output: Master running (pid=12345)
# Or: Control socket not found
```

**Stop master connection:**
```bash
ssh -O exit hostname
# Output: Exit request sent.
```

**Force new connection (bypass master):**
```bash
ssh -o ControlMaster=no hostname
```

**List all active sockets:**
```bash
ls -la ~/.ssh/sockets/
```

**Stop all master connections:**
```bash
for socket in ~/.ssh/sockets/*; do
    ssh -O exit -o ControlPath="$socket" dummy 2>/dev/null
done
```

---

# Chapter 9: Keep-Alive and Timeout Settings

## Why Keep-Alive is Necessary

Network devices terminate idle connections:

```
┌─────────────────────────────────────────────────────────────┐
│                    WITHOUT KEEP-ALIVE                        │
│                                                             │
│  Client                NAT/Firewall              Server     │
│    │                      │                        │        │
│    │ ──────────────────── │ ─────────────────────> │        │
│    │      SSH Session     │     Established        │        │
│    │                      │                        │        │
│    │     (idle for 5 minutes...)                   │        │
│    │                      │                        │        │
│    │      NAT table entry │                        │        │
│    │      expires!        │                        │        │
│    │         ╳            │                        │        │
│    │                      │                        │        │
│    │ ──── Send data ────> │ ╳ (connection lost)    │        │
│    │                      │                        │        │
│    │  "Connection reset"  │                        │        │
│    │                      │                        │        │
└─────────────────────────────────────────────────────────────┘
```

## ServerAliveInterval

**Purpose**: Send keep-alive messages at specified intervals.

### Syntax

```ssh-config
ServerAliveInterval seconds
```

### Default Value

`0` (disabled)

### How It Works

```
┌─────────────────────────────────────────────────────────────┐
│                  WITH ServerAliveInterval 60                 │
│                                                             │
│  Client                                         Server      │
│    │                                               │        │
│    │  ────── SSH_MSG_GLOBAL_REQUEST ─────────────> │        │
│    │         "keepalive@openssh.com"               │        │
│    │                                               │        │
│    │  <───── SSH_MSG_REQUEST_SUCCESS ───────────── │        │
│    │                                               │        │
│    │         (60 seconds later)                    │        │
│    │                                               │        │
│    │  ────── SSH_MSG_GLOBAL_REQUEST ─────────────> │        │
│    │         "keepalive@openssh.com"               │        │
│    │                                               │        │
│    │  <───── SSH_MSG_REQUEST_SUCCESS ───────────── │        │
│    │                                               │        │
│    │         (continues every 60 seconds...)       │        │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### Recommended Value

```ssh-config
ServerAliveInterval 60
```

Why 60 seconds?
- Most NAT devices have 5-15 minute timeouts
- 60 seconds provides good margin
- Low overhead (small encrypted packets)

## ServerAliveCountMax

**Purpose**: Number of keep-alive messages without response before disconnect.

### Syntax

```ssh-config
ServerAliveCountMax count
```

### Default Value

`3`

### How It Works

```
ServerAliveInterval 60 + ServerAliveCountMax 3:

┌─────────────────────────────────────────────────────────────┐
│                                                             │
│  Time 0s:    Send keepalive #1                              │
│  Time 60s:   No response... Send keepalive #2               │
│  Time 120s:  No response... Send keepalive #3               │
│  Time 180s:  No response... Disconnect!                     │
│                                                             │
│  Total tolerance: 180 seconds (3 minutes) of unresponsive   │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### Recommended Configuration

```ssh-config
Host *
    ServerAliveInterval 60
    ServerAliveCountMax 3
```

This means:
- Send keepalive every 60 seconds
- Disconnect after 3 consecutive failures (180 seconds)

### Calculation

```
Disconnect after = ServerAliveInterval × ServerAliveCountMax seconds

Example:
  60 × 3 = 180 seconds = 3 minutes without response
```

### Different Scenarios

```ssh-config
# Stable connection, detect failures quickly
Host local-server
    ServerAliveInterval 15
    ServerAliveCountMax 2
    # Disconnect after 30 seconds

# Unstable connection, more tolerance
Host flaky-vpn
    ServerAliveInterval 60
    ServerAliveCountMax 6
    # Disconnect after 360 seconds (6 minutes)

# Long-running sessions
Host batch-server
    ServerAliveInterval 120
    ServerAliveCountMax 5
    # Disconnect after 600 seconds (10 minutes)
```

---

# Chapter 10: Compression Settings

## Compression Directive

**Purpose**: Enable or disable data compression.

### Syntax

```ssh-config
Compression yes|no
```

### Default Value

`no`

### How Compression Works

```
Without Compression:
┌──────────┐                              ┌──────────┐
│  Client  │                              │  Server  │
│          │ ────── 1000 bytes ─────────> │          │
│          │       (raw data)             │          │
└──────────┘                              └──────────┘

With Compression:
┌──────────┐                              ┌──────────┐
│  Client  │                              │  Server  │
│  ┌─────┐ │                              │ ┌─────┐  │
│  │Comp-│ │ ────── 300 bytes ──────────> │ │Decom│  │
│  │ress │ │     (compressed)             │ │press│  │
│  └─────┘ │                              │ └─────┘  │
│          │                              │          │
│  CPU     │                              │  CPU     │
│  cost    │                              │  cost    │
└──────────┘                              └──────────┘
```

### When to Enable Compression

| Scenario | Compression | Reason |
|----------|-------------|--------|
| Slow WAN link | Yes | Bandwidth limited |
| High latency (satellite) | Yes | Reduce round trips |
| Text-heavy data | Yes | Compresses well |
| Local network | No | Fast enough |
| Already compressed data | No | Won't compress further |
| CPU-limited device | No | CPU overhead |

### Compression Algorithm

SSH uses zlib compression:

```
Compression levels:
  Level 1-3: Fast compression, lower ratio
  Level 4-6: Balanced (default is ~6)
  Level 7-9: Best compression, CPU intensive
```

### Examples

```ssh-config
# Slow connection to remote server
Host remote-datacenter
    Compression yes

# Fast local network
Host local-*
    Compression no

# Default for everything
Host *
    Compression no
```

### Performance Comparison

```
Test: Transfer 100MB text file over different networks

1 Gbps LAN, Compression no:
  Time: 0.8 seconds
  CPU: 2%

1 Gbps LAN, Compression yes:
  Time: 3.2 seconds (SLOWER!)
  CPU: 45%

10 Mbps WAN, Compression no:
  Time: 80 seconds
  CPU: 2%

10 Mbps WAN, Compression yes:
  Time: 25 seconds (FASTER!)
  CPU: 35%
```

**Conclusion**: Only use compression on slow networks!

---

# Chapter 11: Agent Forwarding

## ForwardAgent

**Purpose**: Forward your local SSH agent to remote servers.

### Syntax

```ssh-config
ForwardAgent yes|no
```

### Default Value

`no`

### What is SSH Agent?

SSH agent is a program that holds your private keys in memory:

```
┌─────────────────────────────────────────────────────────────┐
│                       SSH Agent                              │
│                                                             │
│  ┌───────────────────────────────────────────────────────┐  │
│  │                     Memory                             │  │
│  │                                                        │  │
│  │   ┌──────────────┐   ┌──────────────┐                 │  │
│  │   │  id_ed25519  │   │  work_key    │                 │  │
│  │   │  (decrypted) │   │  (decrypted) │                 │  │
│  │   └──────────────┘   └──────────────┘                 │  │
│  │                                                        │  │
│  └───────────────────────────────────────────────────────┘  │
│                                                             │
│  Socket: /tmp/ssh-XXXXXX/agent.12345                        │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### How Agent Forwarding Works

```
Without Agent Forwarding:
┌──────────┐         ┌───────────┐         ┌───────────┐
│  Laptop  │  SSH    │  Jump     │  SSH    │  Target   │
│          │ ──────> │  Server   │ ──────> │  Server   │
│ [keys]   │         │ [no keys] │  FAIL!  │           │
└──────────┘         └───────────┘         └───────────┘

With Agent Forwarding:
┌──────────┐         ┌───────────┐         ┌───────────┐
│  Laptop  │  SSH    │  Jump     │  SSH    │  Target   │
│          │ ──────> │  Server   │ ──────> │  Server   │
│ [keys]   │         │ [forward] │ SUCCESS │           │
│  ▲       │         │     │     │         │           │
│  │       │◄────────│─────┘     │         │           │
│  │ Sign request forwarded back to laptop │           │
└──────────┘         └───────────┘         └───────────┘
```

### Detailed Flow

```
1. Laptop → JumpServer: SSH connection with ForwardAgent yes
2. JumpServer creates forwarded agent socket: /tmp/ssh-XXXXXX/agent.YYYY
3. JumpServer → TargetServer: SSH connection request
4. TargetServer: "I need authentication"
5. JumpServer: Receives sign request, forwards to Laptop via SSH channel
6. Laptop's ssh-agent: Signs the challenge
7. Signed response travels: Laptop → JumpServer → TargetServer
8. TargetServer: "Signature valid, access granted"
```

### Security Warning!

⚠️ **Agent forwarding is a security risk!**

```
RISK: Root on JumpServer can access your agent

┌──────────┐         ┌───────────┐         ┌───────────┐
│  Laptop  │  SSH    │  Jump     │         │ Attacker  │
│          │ ──────> │  Server   │         │  Server   │
│ [keys]   │         │           │         │           │
│          │         │ Malicious │ SSH     │           │
│          │ ◄────── │ root user │ ──────> │ Got in!   │
│          │  Uses   │ hijacks   │ using   │           │
│          │  your   │ agent     │ YOUR    │           │
│          │  key!   │ socket    │ keys!   │           │
└──────────┘         └───────────┘         └───────────┘
```

### When to Use Agent Forwarding

✅ **Safe scenarios:**
- Trusted jump servers you control
- Short sessions
- Internal infrastructure

❌ **Avoid:**
- Shared/public jump servers
- Long-running sessions
- Servers with multiple admins

### Safer Alternative: ProxyJump

Instead of agent forwarding, use ProxyJump:

```ssh-config
Host target-server
    HostName internal.target.com
    ProxyJump jump.example.com
    # No ForwardAgent needed!
```

ProxyJump tunnels through the jump server without exposing your agent.

---

# Chapter 12: Security Considerations

## Security Best Practices

### 1. Use Strong Key Types

```bash
# Generate Ed25519 (recommended)
ssh-keygen -t ed25519 -a 100 -C "email@example.com"

# If RSA required, use 4096 bits
ssh-keygen -t rsa -b 4096 -C "email@example.com"
```

### 2. Protect Private Keys

```bash
# Set correct permissions
chmod 600 ~/.ssh/id_ed25519
chmod 600 ~/.ssh/id_rsa

# Use passphrase!
# When generating key, ALWAYS set a passphrase
```

### 3. Use Different Keys for Different Purposes

```ssh-config
# Personal projects
Host github.com
    IdentityFile ~/.ssh/personal_ed25519
    IdentitiesOnly yes

# Work
Host *.company.com
    IdentityFile ~/.ssh/work_ed25519
    IdentitiesOnly yes

# Servers
Host production-*
    IdentityFile ~/.ssh/prod_ed25519
    IdentitiesOnly yes
```

### 4. Verify Host Keys

```
┌─────────────────────────────────────────────────────────────┐
│ First connection to new server:                             │
│                                                             │
│ The authenticity of host 'server.com' can't be established. │
│ ED25519 key fingerprint is SHA256:abcd1234...              │
│ Are you sure you want to continue connecting (yes/no)?      │
│                                                             │
│ ⚠️  VERIFY this fingerprint with server admin!              │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### 5. Limit Agent Forwarding

```ssh-config
# Disable by default
Host *
    ForwardAgent no

# Enable only for specific trusted hosts
Host trusted-jump
    ForwardAgent yes
```

---

# Chapter 13: Troubleshooting Guide

## Verbose Mode

SSH has multiple verbosity levels:

```bash
ssh server           # Normal (no debug)
ssh -v server        # Debug level 1
ssh -vv server       # Debug level 2
ssh -vvv server      # Debug level 3 (most verbose)
```

## Common Issues and Solutions

### Issue 1: "Connection timed out"

**Symptoms:**
```
ssh: connect to host server port 22: Connection timed out
```

**Causes and Solutions:**

```
┌─────────────────────────────────────────────────────────────┐
│ Cause                    │ Solution                         │
├─────────────────────────────────────────────────────────────┤
│ Server is down           │ Check server status              │
│ Wrong IP/hostname        │ Verify HostName setting          │
│ Firewall blocking        │ Check firewall rules             │
│ Wrong port               │ Verify Port setting              │
│ Network unreachable      │ Check routing                    │
└─────────────────────────────────────────────────────────────┘
```

### Issue 2: "Connection refused"

**Symptoms:**
```
ssh: connect to host server port 22: Connection refused
```

**Causes:**
- SSH server not running
- SSH listening on different port
- TCP wrapper denying connection

### Issue 3: "Permission denied (publickey)"

**Symptoms:**
```
Permission denied (publickey).
```

**Debug steps:**

```bash
# Check which keys are being offered
ssh -v server 2>&1 | grep "Offering"

# Verify your public key is on server
ssh server "cat ~/.ssh/authorized_keys"

# Check key permissions
ls -la ~/.ssh/

# Test specific key
ssh -i ~/.ssh/specific_key server
```

### Issue 4: "Too many authentication failures"

**Symptoms:**
```
Received disconnect from server: Too many authentication failures
```

**Solution:**

```ssh-config
Host server
    IdentityFile ~/.ssh/correct_key
    IdentitiesOnly yes      # Use ONLY this key
```

### Issue 5: Control socket issues

**Symptoms:**
```
Control socket connect(...): Connection refused
ControlPath ... already exists, disabling multiplexing
```

**Solutions:**

```bash
# Remove stale socket
rm ~/.ssh/sockets/user@server-22

# Or exit the master
ssh -O exit server

# Force new connection
ssh -o ControlMaster=no server
```

## Diagnostic Commands

```bash
# Test TCP connectivity
nc -zv server 22

# Check DNS resolution
nslookup server

# Trace route to server
traceroute server

# Check SSH configuration
ssh -G server | grep -E "^(hostname|user|port|identityfile)"

# Test authentication methods
ssh -o PreferredAuthentications=publickey server
ssh -o PreferredAuthentications=password server

# Check master connection status
ssh -O check server

# View loaded keys in agent
ssh-add -l
```

---

# Chapter 14: Best Practices

## Recommended Global Configuration

```ssh-config
# Place this at the END of ~/.ssh/config

Host *
    # Security
    AddKeysToAgent yes

    # Performance - Disable slow auth methods
    GSSAPIAuthentication no

    # Connection multiplexing (huge speed boost!)
    ControlMaster auto
    ControlPath ~/.ssh/sockets/%r@%h-%p
    ControlPersist 600

    # Keep connections alive
    ServerAliveInterval 60
    ServerAliveCountMax 3
    TCPKeepAlive yes

    # Reasonable timeout
    ConnectTimeout 10

    # Disable compression for fast networks
    Compression no
```

## Per-Host Configuration Template

```ssh-config
Host myserver
    # Connection
    HostName actual.hostname.or.ip
    Port 22
    User username

    # Authentication
    IdentityFile ~/.ssh/specific_key
    IdentitiesOnly yes

    # Forwarding (only if needed)
    ForwardAgent no
    LocalForward 8080 localhost:80    # Optional
```

## Security Checklist

```
[ ] Use Ed25519 or RSA-4096 keys
[ ] All keys have passphrases
[ ] Private keys have 600 permissions
[ ] ~/.ssh directory has 700 permissions
[ ] ForwardAgent disabled by default
[ ] IdentitiesOnly used with specific keys
[ ] Host keys verified before first connection
[ ] Unused keys removed from agent
```

## Performance Checklist

```
[ ] GSSAPIAuthentication disabled
[ ] ControlMaster enabled
[ ] ControlPath configured
[ ] ControlPersist set (600+ seconds)
[ ] ServerAliveInterval set (60 seconds)
[ ] ConnectTimeout set (10-30 seconds)
[ ] IdentityFile specified (avoid key scanning)
[ ] Sockets directory created (~/.ssh/sockets)
```

---

# Chapter 15: Complete Configuration Examples

## Example 1: Developer Workstation

```ssh-config
# GitHub
Host github.com
    HostName github.com
    User git
    IdentityFile ~/.ssh/github_ed25519
    IdentitiesOnly yes

# GitLab
Host gitlab.com
    HostName gitlab.com
    User git
    IdentityFile ~/.ssh/gitlab_ed25519
    IdentitiesOnly yes

# Production servers
Host prod-*
    User deploy
    IdentityFile ~/.ssh/production_ed25519
    IdentitiesOnly yes
    ForwardAgent no

# Development servers
Host dev-*
    User developer
    IdentityFile ~/.ssh/dev_ed25519
    ForwardAgent yes

# Jump server
Host bastion
    HostName bastion.company.com
    User admin
    IdentityFile ~/.ssh/bastion_ed25519
    IdentitiesOnly yes

# Internal servers via jump
Host internal-*
    ProxyJump bastion
    User admin

# Global defaults
Host *
    AddKeysToAgent yes
    GSSAPIAuthentication no
    ControlMaster auto
    ControlPath ~/.ssh/sockets/%r@%h-%p
    ControlPersist 600
    ServerAliveInterval 60
    ServerAliveCountMax 3
    ConnectTimeout 10
```

## Example 2: Your Optimized Configuration (a4c and ap-remote)

```ssh-config
Host ap-remote
    HostName ajaykumar-ajaykrarista-2zfg4
    ForwardAgent yes
    User ajay.kumar
    AddKeysToAgent yes
    GSSAPIAuthentication no
    ControlMaster auto
    ControlPath ~/.ssh/sockets/%r@%h-%p
    ControlPersist 600
    ServerAliveInterval 60
    ServerAliveCountMax 3
    ConnectTimeout 10
    TCPKeepAlive yes
    Compression no

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

# Chapter 16: Quick Reference Card

## Essential SSH Config Options

```
┌─────────────────────────────────────────────────────────────┐
│                    QUICK REFERENCE                           │
├──────────────────────┬──────────────────────────────────────┤
│ Host pattern         │ Start config block for matching hosts│
│ HostName ip/name     │ Actual host to connect to            │
│ User username        │ Remote username                      │
│ Port 22              │ SSH port number                      │
├──────────────────────┼──────────────────────────────────────┤
│ IdentityFile path    │ Private key file                     │
│ IdentitiesOnly yes   │ Use only specified key               │
│ AddKeysToAgent yes   │ Cache key in agent                   │
├──────────────────────┼──────────────────────────────────────┤
│ GSSAPIAuth no        │ Disable Kerberos (speeds up!)        │
│ PreferredAuth pubkey │ Auth method order                    │
├──────────────────────┼──────────────────────────────────────┤
│ ControlMaster auto   │ Enable connection multiplexing       │
│ ControlPath path     │ Socket location                      │
│ ControlPersist 600   │ Keep master alive (seconds)          │
├──────────────────────┼──────────────────────────────────────┤
│ ServerAliveInt 60    │ Keepalive interval (seconds)         │
│ ServerAliveMax 3     │ Max missed keepalives                │
│ TCPKeepAlive yes     │ TCP-level keepalive                  │
│ ConnectTimeout 10    │ Connection timeout (seconds)         │
├──────────────────────┼──────────────────────────────────────┤
│ Compression no       │ Disable compression (fast networks)  │
│ ForwardAgent no      │ Don't forward agent (security)       │
└──────────────────────┴──────────────────────────────────────┘
```

## Essential SSH Commands

```bash
# Basic connection
ssh user@host
ssh host              # Uses config file

# With options
ssh -p 2222 host      # Different port
ssh -i key host       # Specific key
ssh -v host           # Verbose (debug)

# Key management
ssh-keygen -t ed25519 # Generate key
ssh-add key           # Add to agent
ssh-add -l            # List keys in agent
ssh-add -D            # Remove all keys

# Multiplexing control
ssh -O check host     # Check master status
ssh -O exit host      # Stop master
ssh -O stop host      # Stop accepting new sessions

# File transfer
scp file host:path    # Copy file
sftp host             # Interactive transfer
rsync -avz dir host:  # Sync directory

# Port forwarding
ssh -L 8080:localhost:80 host   # Local forward
ssh -R 8080:localhost:80 host   # Remote forward
ssh -D 1080 host               # SOCKS proxy
```

---

# References and Further Reading

1. **Man Pages**
   - `man ssh` - SSH client
   - `man ssh_config` - Client configuration
   - `man sshd_config` - Server configuration
   - `man ssh-keygen` - Key generation
   - `man ssh-agent` - Key agent

2. **RFCs**
   - RFC 4251 - SSH Protocol Architecture
   - RFC 4252 - SSH Authentication Protocol
   - RFC 4253 - SSH Transport Layer Protocol
   - RFC 4254 - SSH Connection Protocol

3. **Online Resources**
   - OpenSSH: https://www.openssh.com/
   - SSH.com: https://www.ssh.com/academy/ssh
   - Wikibooks: https://en.wikibooks.org/wiki/OpenSSH

---

*Document created: March 2026*
*Last updated: March 2026*
*Author: System Documentation*
