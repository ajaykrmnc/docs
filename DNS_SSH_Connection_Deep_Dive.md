# DNS Resolution for SSH Connections: A Comprehensive Deep Dive

## Table of Contents

1. [Introduction](#introduction)
2. [DNS Fundamentals](#dns-fundamentals)
3. [The DNS Resolution Process](#the-dns-resolution-process)
4. [SSH Protocol Overview](#ssh-protocol-overview)
5. [DNS Resolution in SSH Connections](#dns-resolution-in-ssh-connections)
6. [SSH-Specific DNS Behaviors](#ssh-specific-dns-behaviors)
7. [Comparison with Other Protocols](#comparison-with-other-protocols)
8. [SSHFP Records and DNS-Based Host Verification](#sshfp-records)
9. [SSH Configuration and DNS](#ssh-configuration-and-dns)
10. [Security Considerations](#security-considerations)
11. [Troubleshooting DNS for SSH](#troubleshooting)
12. [Advanced Topics](#advanced-topics)
13. [Best Practices](#best-practices)

---

## Chapter 1: Introduction

### 1.1 Purpose of This Document

This document provides an exhaustive exploration of how Domain Name System (DNS)
resolution works specifically in the context of Secure Shell (SSH) connections.
While DNS resolution might seem like a simple hostname-to-IP translation, the
reality is far more nuanced, especially when combined with SSH's security
requirements and various configuration options.

### 1.2 Why DNS Matters for SSH

When you type `ssh user@example.com`, a complex series of operations begins
before any encrypted tunnel is established. The very first step—often overlooked
—is resolving "example.com" to an IP address. This resolution process:

- Determines which server you'll actually connect to
- Can be a vector for security attacks if not properly secured
- Affects connection latency and reliability
- Interacts with SSH's host key verification system
- Can be customized through SSH configuration

### 1.3 Scope

This document covers:
- Complete DNS resolution mechanics
- SSH-specific DNS behaviors and configurations
- Security implications and mitigations
- Comparison with HTTP/HTTPS, FTP, and other protocols
- Practical troubleshooting techniques
- Advanced topics including DNSSEC, SSHFP, and proxy configurations

---

## Chapter 2: DNS Fundamentals

### 2.1 What is DNS?

The Domain Name System (DNS) is a hierarchical, distributed database that
translates human-readable domain names into machine-readable IP addresses.
Created in 1983 by Paul Mockapetris (RFCs 882 and 883, later updated by
RFC 1034 and 1035), DNS solved the scalability problems of the earlier
HOSTS.TXT file distributed by the Stanford Research Institute.

### 2.2 The DNS Hierarchy

```
                    . (Root)
                    |
        +-----------+-----------+
        |           |           |
       com         org         net
        |           |           |
    +---+---+   +---+---+   +---+---+
    |       |   |       |   |       |
 google  amazon apache  gnu  example cloudflare
    |       |   |       |   |       |
   www    aws  www    ftp  mail   dns
```

#### 2.2.1 Root Zone

The root zone sits at the apex of the DNS hierarchy. It is represented by
a single dot (.) and is managed by ICANN. There are 13 root server clusters
(A through M) operated by various organizations:

| Letter | Operator | Location(s) |
|--------|----------|-------------|
| A | Verisign | Multiple |
| B | USC-ISI | Marina del Rey, CA |
| C | Cogent Communications | Multiple |
| D | University of Maryland | College Park, MD |
| E | NASA Ames Research Center | Mountain View, CA |
| F | Internet Systems Consortium | Multiple |
| G | US DoD NIC | Multiple |
| H | US Army Research Lab | Multiple |
| I | Netnod | Multiple |
| J | Verisign | Multiple |
| K | RIPE NCC | Multiple |
| L | ICANN | Multiple |
| M | WIDE Project | Multiple |

While there are 13 root server "identities," anycast routing means there are
actually over 1,500 physical root server instances worldwide.

#### 2.2.2 Top-Level Domains (TLDs)

TLDs are divided into several categories:

**Generic TLDs (gTLDs):**
- Original: .com, .org, .net, .edu, .gov, .mil, .int
- New gTLDs (post-2012): .app, .dev, .cloud, .io, etc.

**Country Code TLDs (ccTLDs):**
- Two-letter codes: .us, .uk, .de, .jp, .cn, etc.
- Some have become generic: .io, .tv, .co

**Infrastructure TLD:**
- .arpa (Address and Routing Parameter Area)

#### 2.2.3 Second-Level Domains and Subdomains

Below TLDs are second-level domains (example in example.com) and then
subdomains (www in www.example.com). Organizations can create unlimited
subdomain levels.

### 2.3 DNS Record Types

Understanding DNS record types is crucial for SSH connections, as different
record types serve different purposes in the resolution process.

#### 2.3.1 A Record (Address Record)

The A record maps a hostname to an IPv4 address.

```
example.com.    IN    A    93.184.216.34
```

- TTL (Time To Live): Specifies how long the record can be cached
- Multiple A records can exist for load balancing (round-robin DNS)
- Most commonly used for SSH hostname resolution

#### 2.3.2 AAAA Record (IPv6 Address Record)

The AAAA record maps a hostname to an IPv6 address.

```
example.com.    IN    AAAA    2606:2800:220:1:248:1893:25c8:1946
```

- Essential for IPv6-enabled SSH connections
- Coexists with A records for dual-stack hosts
- SSH clients can prefer IPv4 or IPv6 based on configuration

#### 2.3.3 CNAME Record (Canonical Name)

CNAME creates an alias pointing to another domain name.

```
ssh.example.com.    IN    CNAME    server1.example.com.
server1.example.com.    IN    A    192.0.2.1
```

Important considerations for SSH:
- CNAME resolution adds an extra DNS lookup
- The canonical name becomes important for host key verification
- SSH can use either the alias or canonical name for known_hosts

#### 2.3.4 PTR Record (Pointer Record)

PTR records provide reverse DNS lookup (IP to hostname).

```
34.216.184.93.in-addr.arpa.    IN    PTR    example.com.
```

For IPv6:
```
6.4.9.1.8.c.5.2.3.9.8.1.8.4.2.0.1.0.0.0.0.2.2.0.0.0.8.2.6.0.6.2.ip6.arpa.    IN    PTR    example.com.
```

PTR records are crucial for SSH because:
- SSH servers can use reverse DNS for logging
- Some servers use `UseDNS` option for hostname verification
- Lack of PTR records can cause connection delays

#### 2.3.5 SSHFP Record (SSH Fingerprint)

SSHFP is specifically designed for SSH host key verification.

```
server.example.com.    IN    SSHFP    2 1 123456789abcdef...
```

Structure:
- Algorithm: 1=RSA, 2=DSA, 3=ECDSA, 4=Ed25519
- Fingerprint type: 1=SHA-1, 2=SHA-256
- Fingerprint: Hexadecimal hash of the host key

We'll explore SSHFP in detail in Chapter 8.

#### 2.3.6 SRV Record (Service Record)

While not commonly used for SSH, SRV records can specify service locations.

```
_ssh._tcp.example.com.    IN    SRV    10 5 22 server.example.com.
```

Structure: priority weight port target

#### 2.3.7 TXT Record

TXT records store arbitrary text and are used for:
- SPF, DKIM, DMARC (email security)
- Domain verification
- DANE TLSA (certificate pinning)

#### 2.3.8 NS Record (Name Server)

NS records delegate a zone to authoritative name servers.

```
example.com.    IN    NS    ns1.example.com.
example.com.    IN    NS    ns2.example.com.
```

#### 2.3.9 SOA Record (Start of Authority)

SOA contains administrative information about a zone.

```
example.com.    IN    SOA    ns1.example.com. admin.example.com. (
                            2024010101 ; Serial
                            3600       ; Refresh
                            900        ; Retry
                            604800     ; Expire
                            86400      ; Minimum TTL
                            )
```

### 2.4 DNS Resolution Components

#### 2.4.1 Stub Resolver

The stub resolver is the DNS client built into the operating system. It:
- Receives queries from applications
- Forwards queries to recursive resolvers
- Caches responses locally (usually)
- Is configured via /etc/resolv.conf (Unix) or network settings (Windows)

On Linux/Unix systems, the stub resolver is part of the C library (glibc, musl).

#### 2.4.2 Recursive Resolver

The recursive resolver (also called a caching nameserver):
- Receives queries from stub resolvers
- Performs full DNS resolution by querying the hierarchy
- Caches results to improve performance
- Often provided by ISPs or third parties (Google: 8.8.8.8, Cloudflare: 1.1.1.1)

#### 2.4.3 Authoritative Nameserver

Authoritative nameservers:
- Hold the actual DNS records for a zone
- Respond definitively to queries about their zones
- Do not recurse or cache other zones' data
- Are identified by NS records

### 2.5 The DNS Query Process

When an application needs to resolve a hostname, the following occurs:

```
[Application] -> [Stub Resolver] -> [Recursive Resolver] -> [DNS Hierarchy]
                      |                    |
                      v                    v
                 [Local Cache]      [Resolver Cache]
```

1. **Application Query**: Application calls getaddrinfo() or gethostbyname()
2. **Local Cache Check**: Stub resolver checks OS DNS cache
3. **Resolver Query**: If not cached, query sent to configured recursive resolver
4. **Recursive Resolution**: Resolver queries root -> TLD -> authoritative servers
5. **Response Caching**: Results cached at multiple levels
6. **Application Response**: IP address(es) returned to application

### 2.6 DNS Caching Layers

DNS uses aggressive caching to reduce load and improve performance:

| Cache Layer | Location | Typical Duration |
|-------------|----------|------------------|
| Browser Cache | Web browser | 1 min - 1 hour |
| OS Cache | Operating system | Until TTL expires |
| Resolver Cache | ISP/Third-party resolver | Until TTL expires |
| CDN/Proxy Cache | Edge servers | Varies |

SSH clients typically bypass browser caching and use the OS resolver directly.

### 2.7 DNS Transport Protocols

#### 2.7.1 Traditional DNS (UDP/53, TCP/53)

- UDP port 53: Primary transport for most queries
- TCP port 53: Used for zone transfers and large responses (>512 bytes)
- No encryption: Queries and responses are plaintext

#### 2.7.2 DNS over TLS (DoT)

- Uses TCP port 853
- Encrypts DNS traffic using TLS
- Supported by modern resolvers (Cloudflare, Google, Quad9)
- Configured at the OS/resolver level

#### 2.7.3 DNS over HTTPS (DoH)

- Uses TCP port 443 (standard HTTPS)
- Encapsulates DNS queries in HTTP requests
- Harder to block than DoT
- Often used by browsers, less commonly for SSH

#### 2.7.4 DNS over QUIC (DoQ)

- Uses UDP port 853
- Based on QUIC protocol
- Lower latency than DoT
- Emerging standard (RFC 9250)

---

## Chapter 3: The DNS Resolution Process

### 3.1 Iterative vs Recursive Resolution

#### 3.1.1 Recursive Resolution

In recursive resolution, the client sends one query to its resolver, which
then does all the work:

```
Client                Resolver              Root         TLD          Auth
  |                      |                    |           |             |
  |---Query: www.ex.com->|                    |           |             |
  |                      |---Query: www.ex.com->          |             |
  |                      |<--Referral: .com NS-|          |             |
  |                      |                    |           |             |
  |                      |---Query: www.ex.com----------->|             |
  |                      |<--Referral: example.com NS-----|             |
  |                      |                    |           |             |
  |                      |---Query: www.ex.com------------------------>|
  |                      |<--Answer: 93.184.216.34-----------------------|
  |                      |                    |           |             |
  |<--Answer: 93.184.216.34                   |           |             |
```

#### 3.1.2 Iterative Resolution

In iterative resolution, each server returns a referral, and the client
follows the chain:

```
Client              Root              TLD              Auth
  |                   |                |                 |
  |---Query--------->|                |                 |
  |<--Referral-------|                |                 |
  |                   |                |                 |
  |---Query------------------------->|                 |
  |<--Referral-----------------------|                 |
  |                   |                |                 |
  |---Query------------------------------------------->|
  |<--Answer-------------------------------------------|
```

Most clients use recursive resolution for simplicity.

### 3.2 The Complete Resolution Flow

Let's trace a complete DNS resolution for `ssh.example.com`:

**Step 1: Application Request**
```c
struct addrinfo hints = {0};
hints.ai_family = AF_UNSPEC;     // Allow IPv4 or IPv6
hints.ai_socktype = SOCK_STREAM; // TCP
getaddrinfo("ssh.example.com", "22", &hints, &result);
```

**Step 2: Check /etc/hosts**
```
# /etc/hosts
127.0.0.1       localhost
192.168.1.100   ssh.example.com    # If present, used directly
```

**Step 3: Check NSS Configuration**
```
# /etc/nsswitch.conf
hosts: files dns myhostname
```

This means: check files (/etc/hosts) first, then DNS.

**Step 4: Local DNS Cache Check**
On modern Linux systems, systemd-resolved maintains a local cache:
```bash
$ resolvectl query ssh.example.com
ssh.example.com: 93.184.216.34
```

**Step 5: Query Recursive Resolver**
```
# /etc/resolv.conf
nameserver 8.8.8.8
nameserver 8.8.4.4
options timeout:2 attempts:3
```

**Step 6: Recursive Resolution**

The resolver (8.8.8.8) performs:

a) **Root Server Query**
```
Query: ssh.example.com A?
Response: Referral to .com TLD servers
          com. NS a.gtld-servers.net.
          a.gtld-servers.net. A 192.5.6.30
```

b) **TLD Server Query**
```
Query: ssh.example.com A?
Response: Referral to example.com authoritative servers
          example.com. NS ns1.example.com.
          ns1.example.com. A 192.0.2.1
```

c) **Authoritative Server Query**
```
Query: ssh.example.com A?
Response: Answer
          ssh.example.com. 3600 IN A 93.184.216.34
```

**Step 7: Response to Client**
```
93.184.216.34 returned with TTL=3600 (1 hour)
```

### 3.3 DNS Message Format

DNS messages follow a specific binary format (RFC 1035):

```
+---------------------+
|        Header       |  12 bytes
+---------------------+
|       Question      |  Variable
+---------------------+
|        Answer       |  Variable
+---------------------+
|      Authority      |  Variable
+---------------------+
|      Additional     |  Variable
+---------------------+
```

#### 3.3.1 Header Format (12 bytes)

```
                                1  1  1  1  1  1
  0  1  2  3  4  5  6  7  8  9  0  1  2  3  4  5
+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+
|                      ID                       |
+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+
|QR|   Opcode  |AA|TC|RD|RA|   Z    |   RCODE   |
+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+
|                    QDCOUNT                    |
+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+
|                    ANCOUNT                    |
+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+
|                    NSCOUNT                    |
+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+
|                    ARCOUNT                    |
+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+
```

Flag meanings:
- QR: Query (0) or Response (1)
- Opcode: 0=Standard, 1=Inverse, 2=Status
- AA: Authoritative Answer
- TC: Truncation (response too large for UDP)
- RD: Recursion Desired
- RA: Recursion Available
- RCODE: 0=No error, 1=Format error, 2=Server failure, 3=NXDOMAIN

### 3.4 DNS Response Codes

| RCODE | Name | Meaning |
|-------|------|---------|
| 0 | NOERROR | Successful query |
| 1 | FORMERR | Format error in query |
| 2 | SERVFAIL | Server unable to process |
| 3 | NXDOMAIN | Domain does not exist |
| 4 | NOTIMP | Query type not implemented |
| 5 | REFUSED | Query refused by policy |
| 6 | YXDOMAIN | Name exists when it shouldn't |
| 7 | YXRRSET | RRset exists when it shouldn't |
| 8 | NXRRSET | RRset doesn't exist |
| 9 | NOTAUTH | Server not authoritative |
| 10 | NOTZONE | Name not in zone |

### 3.5 EDNS (Extension Mechanisms for DNS)

EDNS0 (RFC 6891) extends DNS capabilities:

- Larger UDP payload sizes (up to 4096 bytes)
- Additional flags and options
- Required for DNSSEC
- Client Subnet support for CDN optimization

```
; EDNS: version: 0, flags:; udp: 4096
; OPT PSEUDOSECTION:
; EDNS: version: 0, flags: do; udp: 512
; COOKIE: 1234567890abcdef
```

---

## Chapter 4: SSH Protocol Overview

### 4.1 What is SSH?

Secure Shell (SSH) is a cryptographic network protocol for:
- Secure remote command-line login
- Secure file transfer (SCP, SFTP)
- Port forwarding and tunneling
- VPN-like functionality

SSH was designed in 1995 by Tatu Ylönen as a replacement for insecure
protocols like Telnet, rlogin, and rsh.

### 4.2 SSH Protocol Versions

#### 4.2.1 SSH-1 (Deprecated)

- Released 1995
- Known security vulnerabilities
- Should not be used
- Some legacy systems still support it

#### 4.2.2 SSH-2

- Current standard (RFC 4251-4256)
- Completely redesigned protocol
- Multiple authentication methods
- Strong encryption and integrity

### 4.3 SSH Protocol Layers

```
+----------------------------------+
|     SSH Connection Protocol      |  Channels, Sessions, Forwarding
+----------------------------------+
|   SSH User Authentication        |  Password, Public Key, etc.
+----------------------------------+
|     SSH Transport Layer          |  Encryption, Integrity, Key Exchange
+----------------------------------+
|            TCP/IP                |  Reliable Transport
+----------------------------------+
```

#### 4.3.1 Transport Layer (RFC 4253)

- Initial key exchange
- Server authentication
- Encryption algorithm negotiation
- Data integrity
- Compression (optional)

#### 4.3.2 User Authentication Layer (RFC 4252)

Authentication methods:
- Public key (most secure)
- Password (common but less secure)
- Keyboard-interactive (two-factor)
- Host-based (trusted hosts)
- GSSAPI/Kerberos

#### 4.3.3 Connection Layer (RFC 4254)

- Multiplexed channels
- Interactive sessions
- X11 forwarding
- TCP/IP port forwarding
- Agent forwarding

### 4.4 SSH Connection Establishment

The SSH connection process involves multiple phases:

```
Client                                           Server
   |                                                |
   |  1. TCP Handshake (SYN, SYN-ACK, ACK)         |
   |<---------------------------------------------->|
   |                                                |
   |  2. Protocol Version Exchange                  |
   |  SSH-2.0-OpenSSH_8.9\r\n                      |
   |<---------------------------------------------->|
   |                                                |
   |  3. Key Exchange (KEX)                        |
   |  SSH_MSG_KEXINIT                              |
   |<---------------------------------------------->|
   |                                                |
   |  4. Diffie-Hellman Key Exchange               |
   |<---------------------------------------------->|
   |                                                |
   |  5. New Keys                                   |
   |  (Session encryption begins)                   |
   |<---------------------------------------------->|
   |                                                |
   |  6. User Authentication                        |
   |<---------------------------------------------->|
   |                                                |
   |  7. Session/Channel Establishment              |
   |<---------------------------------------------->|
```

### 4.5 SSH Key Exchange

Modern SSH supports several key exchange algorithms:

| Algorithm | Security Level | Performance |
|-----------|----------------|-------------|
| curve25519-sha256 | High | Fast |
| ecdh-sha2-nistp256 | High | Fast |
| ecdh-sha2-nistp384 | High | Medium |
| ecdh-sha2-nistp521 | Very High | Slower |
| diffie-hellman-group16-sha512 | High | Slow |
| diffie-hellman-group18-sha512 | Very High | Very Slow |

### 4.6 SSH Host Keys

Host keys are the server's identity:

```bash
$ ls -la /etc/ssh/ssh_host_*
-rw------- 1 root root  513 Jan  1 00:00 /etc/ssh/ssh_host_ecdsa_key
-rw-r--r-- 1 root root  179 Jan  1 00:00 /etc/ssh/ssh_host_ecdsa_key.pub
-rw------- 1 root root  411 Jan  1 00:00 /etc/ssh/ssh_host_ed25519_key
-rw-r--r-- 1 root root   99 Jan  1 00:00 /etc/ssh/ssh_host_ed25519_key.pub
-rw------- 1 root root 2602 Jan  1 00:00 /etc/ssh/ssh_host_rsa_key
-rw-r--r-- 1 root root  571 Jan  1 00:00 /etc/ssh/ssh_host_rsa_key.pub
```

Host key verification prevents man-in-the-middle attacks:

```
$ ssh server.example.com
The authenticity of host 'server.example.com (192.0.2.1)' can't be established.
ED25519 key fingerprint is SHA256:xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx.
Are you sure you want to continue connecting (yes/no/[fingerprint])?
```

### 4.7 Known Hosts

SSH stores verified host keys in `~/.ssh/known_hosts`:

```
server.example.com,192.0.2.1 ssh-ed25519 AAAA...
|hostname|,|IP address| |key type| |public key|
```

Options for known_hosts:
- Plain text hostnames (default)
- Hashed hostnames (`HashKnownHosts yes`)
- Wildcards supported
- Multiple entries per host allowed

---

## Chapter 5: DNS Resolution in SSH Connections

### 5.1 How SSH Resolves Hostnames

When you execute `ssh user@hostname`, the SSH client performs DNS resolution
using the system's standard resolver. This section details the complete process.

### 5.2 The getaddrinfo() System Call

SSH uses the POSIX `getaddrinfo()` function for name resolution:

```c
#include <sys/types.h>
#include <sys/socket.h>
#include <netdb.h>

int getaddrinfo(const char *node,
                const char *service,
                const struct addrinfo *hints,
                struct addrinfo **res);
```

Key parameters for SSH:
- `node`: The hostname to resolve (e.g., "server.example.com")
- `service`: The port/service (e.g., "22" or "ssh")
- `hints`: Configuration structure
- `res`: Returned linked list of addresses

### 5.3 SSH's Resolution Preferences

OpenSSH sets specific preferences when calling getaddrinfo():

```c
// From OpenSSH source code (simplified)
memset(&hints, 0, sizeof(hints));
hints.ai_family = options.address_family;  // AF_UNSPEC, AF_INET, or AF_INET6
hints.ai_socktype = SOCK_STREAM;           // TCP
hints.ai_flags = AI_CANONNAME;             // Request canonical name

getaddrinfo(host, strport, &hints, &res);
```

The `AI_CANONNAME` flag is important—it requests the canonical name of the
host, which SSH may use for host key verification.

### 5.4 Address Family Selection

SSH can be configured to prefer IPv4 or IPv6:

```
# ~/.ssh/config or /etc/ssh/ssh_config

# Default: try both IPv4 and IPv6
AddressFamily any

# Force IPv4 only
AddressFamily inet

# Force IPv6 only
AddressFamily inet6
```

Command-line equivalents:
```bash
ssh -4 server.example.com  # Force IPv4
ssh -6 server.example.com  # Force IPv6
```

### 5.5 The Complete SSH DNS Resolution Flow

```
                    ssh user@server.example.com
                              |
                              v
                    +-------------------+
                    | Parse Command     |
                    | Extract hostname  |
                    +-------------------+
                              |
                              v
                    +-------------------+
                    | Check SSH Config  |
                    | - Hostname alias? |
                    | - CanonicalDomains|
                    +-------------------+
                              |
                              v
                    +-------------------+
                    | getaddrinfo()     |
                    +-------------------+
                              |
                              v
                    +-------------------+
                    | System Resolver   |
                    | (nsswitch.conf)   |
                    +-------------------+
                              |
               +--------------+--------------+
               |              |              |
               v              v              v
        +----------+   +----------+   +----------+
        |  /etc/   |   |   DNS    |   |   mDNS   |
        |  hosts   |   | Resolver |   | (Avahi)  |
        +----------+   +----------+   +----------+
               |              |              |
               +--------------+--------------+
                              |
                              v
                    +-------------------+
                    | Return IP Address |
                    | (possibly multiple)|
                    +-------------------+
                              |
                              v
                    +-------------------+
                    | TCP Connect to IP |
                    | on Port 22        |
                    +-------------------+
```

### 5.6 DNS Caching for SSH

Unlike web browsers, SSH clients typically don't maintain their own DNS cache.
They rely on:

1. **OS-level caching**: systemd-resolved, nscd, or similar
2. **Resolver caching**: ISP or third-party resolver cache
3. **No session caching**: Each ssh command triggers fresh resolution

This behavior has important security implications—it prevents cache poisoning
at the SSH client level but makes SSH connections more dependent on DNS
infrastructure reliability.

### 5.7 Multiple Address Handling

When DNS returns multiple addresses (A and/or AAAA records), SSH:

1. Receives all addresses from getaddrinfo()
2. Attempts connection to first address
3. If connection fails, tries next address
4. Continues until success or all addresses exhausted

```bash
# Example: host with multiple A records
$ dig +short server.example.com
192.0.2.1
192.0.2.2
192.0.2.3

$ ssh -v server.example.com
# SSH will try each IP in order if needed
```

### 5.8 Connection Timeout and DNS

SSH has separate timeouts for DNS and connection:

```
# ~/.ssh/config

# Connection timeout (applies after DNS resolution)
ConnectTimeout 30

# TCP keepalive settings (after connection established)
TCPKeepAlive yes
ServerAliveInterval 60
ServerAliveCountMax 3
```

DNS timeout is controlled by the system resolver:
```
# /etc/resolv.conf
options timeout:5 attempts:2
```

### 5.9 Canonical Hostname Resolution

SSH can perform canonical hostname resolution to:
- Normalize hostnames for known_hosts
- Expand short hostnames to FQDNs
- Handle DNS aliases properly

```
# ~/.ssh/config

# Canonicalize hostnames
CanonicalizeHostname yes

# Search these domains
CanonicalDomains example.com internal.example.com

# Maximum CNAME chain depth
CanonicalizeMaxDots 1

# Behavior if canonicalization fails
CanonicalizeFallbackLocal yes
CanonicalizePermittedCNAMEs *.internal.example.com:*.server.example.com
```

Example workflow:
```bash
$ ssh server
# 1. Check if "server" has dots (no)
# 2. Try server.example.com (first CanonicalDomains entry)
# 3. If exists, use canonical name for connection
```


---

## Chapter 6: SSH-Specific DNS Behaviors

### 6.1 UseDNS Option (Server-Side)

The SSH server has a `UseDNS` option that affects authentication:

```
# /etc/ssh/sshd_config

# Enable reverse DNS lookup for connecting clients
UseDNS yes   # Default was 'yes' in older versions

# Disable reverse DNS lookup
UseDNS no    # Recommended for performance
```

When `UseDNS yes`:
1. Server receives client connection from IP address
2. Server performs PTR lookup (IP → hostname)
3. Server performs A lookup on returned hostname
4. Server verifies forward and reverse match
5. Hostname can be used in authorized_keys "from=" restrictions

```
# ~/.ssh/authorized_keys
from="*.trusted.example.com" ssh-ed25519 AAAA...
```

Implications:
- Adds latency to connection establishment
- Requires proper reverse DNS configuration
- Can cause long delays if DNS is slow/unavailable
- Modern recommendation: `UseDNS no`

### 6.2 Host Key Verification and DNS

SSH uses the hostname for host key lookup in known_hosts:

```
# When connecting to server.example.com at 192.0.2.1
# SSH checks known_hosts for:
# 1. server.example.com
# 2. 192.0.2.1
# 3. [server.example.com]:port (if non-standard port)
# 4. [192.0.2.1]:port (if non-standard port)
```

This creates an interesting DNS dependency:
- Same server with different DNS names = different known_hosts entries
- CNAME aliases may require multiple entries
- IP address changes don't affect hostname-based verification

### 6.3 CheckHostIP Option

```
# ~/.ssh/config
CheckHostIP yes  # Default

# Behavior when enabled:
# - Verifies host key against both hostname AND IP
# - Warns if IP changes but hostname key matches
# - Provides additional MITM protection
```

Warning example:
```
@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
@       WARNING: POSSIBLE DNS SPOOFING DETECTED!          @
@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
The ECDSA host key for server.example.com has changed,
and the key for the corresponding IP address 192.0.2.1
is unknown. This could either mean that
DNS SPOOFING is happening or the IP address for the host
and its host key have changed at the same time.
```

### 6.4 UpdateHostKeys Option

```
# ~/.ssh/config
UpdateHostKeys yes

# Automatically learn new host keys when server presents them
# Helps with key rotation and algorithm upgrades
```

### 6.5 ProxyJump and DNS Resolution

When using ProxyJump (jump hosts), DNS resolution occurs at different points:

```
# ~/.ssh/config
Host target
    HostName internal.example.com
    ProxyJump bastion.example.com
```

Resolution flow:
```
Local Client                Bastion Host              Target Server
     |                           |                          |
     | 1. Resolve bastion.example.com                       |
     |    (LOCAL DNS)            |                          |
     |                           |                          |
     |---TCP Connect to Bastion->|                          |
     |                           |                          |
     | 2. Request proxy to internal.example.com             |
     |-------------------------->|                          |
     |                           |                          |
     |                           | 3. Resolve internal.example.com
     |                           |    (BASTION DNS)         |
     |                           |                          |
     |                           |---TCP Connect to Target->|
     |                           |                          |
     |<--------Proxied SSH Connection-----------------------|
```

Important: The target hostname is resolved by the jump host, not the client.

### 6.6 ProxyCommand and DNS

With ProxyCommand, you have full control over DNS resolution:

```
# ~/.ssh/config
Host *.internal
    ProxyCommand ssh -W %h:%p bastion.example.com
```

The `%h` token expands to the target hostname, resolved by the bastion.

Alternative with local resolution:
```
Host *.internal
    ProxyCommand ssh -W $(dig +short %h):%p bastion.example.com
```

### 6.7 DynamicForward and SOCKS

When using SSH as a SOCKS proxy:

```bash
ssh -D 1080 server.example.com
```

DNS resolution for SOCKS traffic:
- SOCKS4: DNS resolved locally (client-side)
- SOCKS4a: DNS can be resolved by proxy
- SOCKS5: DNS resolved by proxy (default for most clients)

Browser configuration matters:
```
# Firefox: network.proxy.socks_remote_dns = true
# Ensures DNS queries go through the tunnel
```

### 6.8 Local and Remote Port Forwarding

#### Local Forwarding
```bash
ssh -L 8080:internal.example.com:80 bastion.example.com
```

DNS resolution: `internal.example.com` is resolved by `bastion.example.com`

#### Remote Forwarding
```bash
ssh -R 8080:localhost:80 server.example.com
```

DNS resolution: `localhost` is resolved by the local client

### 6.9 X11 Forwarding and DNS

X11 forwarding can involve DNS for the DISPLAY variable:

```bash
$ echo $DISPLAY
localhost:10.0
```

SSH uses `localhost` to avoid DNS issues with X11 forwarding.

---

## Chapter 7: Comparison with Other Protocols

### 7.1 SSH vs HTTP/HTTPS DNS Resolution

| Aspect | SSH | HTTP/HTTPS |
|--------|-----|------------|
| Client Caching | No client DNS cache | Browser DNS cache |
| DoH/DoT | System resolver only | Browser may use DoH |
| Happy Eyeballs | Not implemented | RFC 8305 compliance |
| Connection Reuse | Yes (multiplexing) | HTTP/2, HTTP/3 |
| DNS Pre-resolution | No | DNS prefetching |
| Alt-Svc/HTTPS records | Not applicable | Supported |

### 7.2 Web Browser DNS Resolution

Modern web browsers have sophisticated DNS handling:

#### 7.2.1 DNS Prefetching
```html
<link rel="dns-prefetch" href="//example.com">
```

Browsers proactively resolve domains before they're needed.

#### 7.2.2 Browser DNS Cache

```
Chrome: chrome://net-internals/#dns
Firefox: about:networking#dns
```

Typical cache duration: 1-60 minutes (ignoring TTL in some cases)

#### 7.2.3 Happy Eyeballs (RFC 8305)

Browsers implement Happy Eyeballs for IPv4/IPv6 racing:

```
1. Start IPv6 resolution
2. After 50ms, also start IPv4 resolution
3. Start IPv6 connection attempt
4. After 250ms, also start IPv4 connection attempt
5. Use whichever connects first
6. Cancel the other
```

SSH does NOT implement Happy Eyeballs—it tries addresses sequentially.

#### 7.2.4 DNS over HTTPS in Browsers

```
Chrome: Settings > Security > Use secure DNS
Firefox: Settings > Network Settings > Enable DNS over HTTPS
```

Browsers can bypass system DNS entirely, which SSH cannot do natively.

### 7.3 SSH vs FTP DNS Resolution

| Aspect | SSH/SFTP | FTP |
|--------|----------|-----|
| Active Mode | N/A | Requires reverse DNS for data connections |
| Passive Mode | N/A | Client resolves server-provided IP |
| Security | All encrypted | Commands in cleartext (unless FTPS) |
| DNS Hijacking Risk | Host key verification | High risk |

### 7.4 SSH vs Database Connections

Database clients (MySQL, PostgreSQL, etc.) typically:
- Use system resolver (like SSH)
- May cache DNS within connection pools
- Often use IP addresses directly in production
- May support Unix sockets (no DNS needed)

Example PostgreSQL connection string:
```
postgresql://user:pass@db.example.com:5432/database
```

Resolution is similar to SSH—system resolver, no client caching.

### 7.5 Email (SMTP/IMAP/POP3) vs SSH

Email protocols have unique DNS requirements:

```
# MX record lookup for email
$ dig +short MX example.com
10 mail.example.com.
20 mail2.example.com.
```

| Aspect | SSH | Email |
|--------|-----|-------|
| Primary Record | A/AAAA | MX (then A/AAAA) |
| Port | Usually 22 | 25, 587, 993, 995 |
| TLS Discovery | Always SSH | STARTTLS or implicit |
| Authentication DNS | SSHFP (optional) | SPF, DKIM, DMARC |

### 7.6 VPN Protocols vs SSH

#### IPsec/IKEv2
- May use DNS for gateway discovery
- Can push DNS servers to clients
- Split tunneling affects DNS routing

#### WireGuard
- Endpoints typically use IP addresses
- No built-in DNS handling
- DNS leaks are a concern

#### OpenVPN
- `--redirect-gateway` affects DNS
- Can push DNS servers
- `--block-outside-dns` option (Windows)

SSH tunnels:
- No automatic DNS pushing
- Requires manual configuration (SOCKS proxy)
- DNS leaks possible without proper setup

### 7.7 Comparison Table: DNS Behaviors

| Protocol | Resolver | Caching | DoH/DoT | Prefetch | Happy Eyeballs |
|----------|----------|---------|---------|----------|----------------|
| SSH | System | No | Via system | No | No |
| HTTPS | Browser or system | Yes | Yes | Yes | Yes |
| FTP | System | No | Via system | No | No |
| SMTP | System | No | Via system | No | No |
| Database | System/Pool | Pool-level | Via system | No | No |
| VPN | System/Pushed | Varies | Via system | No | No |

---

## Chapter 8: SSHFP Records and DNS-Based Host Verification

### 8.1 Introduction to SSHFP

SSH Fingerprint (SSHFP) records (RFC 4255, updated by RFC 6594 and 7479)
allow SSH host key verification via DNS. This provides an alternative to
the traditional "trust on first use" (TOFU) model.

### 8.2 SSHFP Record Format

```
hostname.  IN  SSHFP  <algorithm> <type> <fingerprint>
```

Algorithm numbers:
- 1 = RSA
- 2 = DSA (deprecated)
- 3 = ECDSA
- 4 = Ed25519
- 6 = Ed448

Fingerprint type:
- 1 = SHA-1 (deprecated)
- 2 = SHA-256

### 8.3 Generating SSHFP Records

```bash
# Generate SSHFP records for all host keys
$ ssh-keygen -r server.example.com

server.example.com IN SSHFP 1 1 8b83...  # RSA SHA-1
server.example.com IN SSHFP 1 2 2a4f...  # RSA SHA-256
server.example.com IN SSHFP 3 1 6e7a...  # ECDSA SHA-1
server.example.com IN SSHFP 3 2 9c2d...  # ECDSA SHA-256
server.example.com IN SSHFP 4 1 a1b2...  # Ed25519 SHA-1
server.example.com IN SSHFP 4 2 f8e9...  # Ed25519 SHA-256
```

### 8.4 Publishing SSHFP Records

Add to your DNS zone file:

```
; Zone file for example.com
$TTL 3600
@       IN      SOA     ns1.example.com. admin.example.com. (
                        2024010101 ; Serial
                        3600       ; Refresh
                        900        ; Retry
                        604800     ; Expire
                        86400 )    ; Minimum

        IN      NS      ns1.example.com.
        IN      NS      ns2.example.com.

server  IN      A       192.0.2.1
server  IN      AAAA    2001:db8::1

; SSHFP records
server  IN      SSHFP   1 2 2a4f...
server  IN      SSHFP   3 2 9c2d...
server  IN      SSHFP   4 2 f8e9...
```

### 8.5 Configuring SSH to Use SSHFP

```
# ~/.ssh/config

# Enable SSHFP verification
VerifyHostKeyDNS yes

# Or, verify only if DNSSEC validated
VerifyHostKeyDNS ask
```

Client behavior:
- `yes`: Trust SSHFP if present (even without DNSSEC)
- `ask`: Prompt user if SSHFP found but not DNSSEC-validated
- `no`: Ignore SSHFP records (default)

### 8.6 SSHFP with DNSSEC

SSHFP without DNSSEC is vulnerable to DNS spoofing—an attacker who can
forge DNS responses can also forge SSHFP records. DNSSEC provides
cryptographic authentication of DNS records.

```bash
# Check if SSHFP is DNSSEC validated
$ dig +dnssec SSHFP server.example.com

;; flags: qr rd ra ad; QUERY: 1, ANSWER: 2, AUTHORITY: 0, ADDITIONAL: 1
#                   ^^-- 'ad' flag indicates authenticated data (DNSSEC valid)

server.example.com. 3600 IN SSHFP 4 2 f8e9...
server.example.com. 3600 IN RRSIG SSHFP ...
```

### 8.7 SSHFP Verification Flow

```
Client                           DNS                           Server
  |                               |                               |
  | 1. Query SSHFP records        |                               |
  |------------------------------>|                               |
  |                               |                               |
  | 2. Receive SSHFP + DNSSEC sig |                               |
  |<------------------------------|                               |
  |                               |                               |
  | 3. Validate DNSSEC chain      |                               |
  |                               |                               |
  | 4. Start SSH connection       |                               |
  |------------------------------------------------------>|
  |                               |                               |
  | 5. Receive server host key    |                               |
  |<------------------------------------------------------|
  |                               |                               |
  | 6. Hash host key              |                               |
  | 7. Compare to SSHFP           |                               |
  | 8. If match, verify host key  |                               |
  |                               |                               |
```

### 8.8 SSHFP Troubleshooting

```bash
# Query SSHFP records
$ dig SSHFP server.example.com

# Verify SSH can see SSHFP
$ ssh -v -o VerifyHostKeyDNS=yes server.example.com 2>&1 | grep -i sshfp

# Check DNSSEC validation
$ delv @8.8.8.8 SSHFP server.example.com
```

Common issues:
- SSHFP records not published
- Algorithm/type mismatch
- DNSSEC not validated
- Resolver doesn't support SSHFP queries
- TTL too long after key rotation

### 8.9 SSHFP Limitations

1. **DNSSEC Dependency**: Without DNSSEC, SSHFP adds little security
2. **Adoption**: DNSSEC deployment is still incomplete
3. **Key Rotation**: DNS propagation delays during key rotation
4. **Resolver Trust**: Requires trusting the DNS resolver
5. **Client Support**: Not all SSH clients support VerifyHostKeyDNS

### 8.10 Alternatives to SSHFP

1. **Certificate-based host keys**: SSH certificates signed by a CA
2. **Manual fingerprint verification**: Out-of-band verification
3. **Ansible/Puppet provisioning**: Push known_hosts to clients
4. **TOFU with caution**: Accept on first connection, verify on changes

---

## Chapter 9: SSH Configuration and DNS

### 9.1 SSH Client Configuration Files

SSH configuration hierarchy:
1. Command-line options
2. ~/.ssh/config
3. /etc/ssh/ssh_config

```
# ~/.ssh/config syntax
Host <pattern>
    Option Value
    Option Value
```

### 9.2 DNS-Related Client Options

#### 9.2.1 HostName

Override the target hostname:

```
Host myserver
    HostName actual-server.example.com
    User admin
```

```bash
$ ssh myserver
# Connects to actual-server.example.com
```

#### 9.2.2 AddressFamily

Control IP version preference:

```
Host *
    AddressFamily inet    # IPv4 only

Host ipv6-host
    AddressFamily inet6   # IPv6 only
```

#### 9.2.3 CanonicalizeHostname

Enable hostname canonicalization:

```
Host *
    CanonicalizeHostname yes
    CanonicalDomains example.com corp.example.com
    CanonicalizeMaxDots 1
    CanonicalizeFallbackLocal yes
```

How it works:
1. If hostname has 0-1 dots, try appending CanonicalDomains
2. Query DNS for each candidate
3. Use first successful resolution
4. Reload config with canonical name

#### 9.2.4 CanonicalizePermittedCNAMEs

Control CNAME following:

```
Host *
    CanonicalizePermittedCNAMEs *.example.com:*.example.com *.dev:*.prod
```

Format: source_pattern:target_pattern

#### 9.2.5 CheckHostIP

Verify IP address in known_hosts:

```
Host *
    CheckHostIP yes    # Default: verify IP matches
```

#### 9.2.6 GlobalKnownHostsFile

System-wide known hosts:

```
Host *
    GlobalKnownHostsFile /etc/ssh/ssh_known_hosts
```

#### 9.2.7 UserKnownHostsFile

Per-user known hosts:

```
Host *
    UserKnownHostsFile ~/.ssh/known_hosts
```

#### 9.2.8 StrictHostKeyChecking

Host key verification policy:

```
Host *
    StrictHostKeyChecking ask      # Default: prompt for new hosts

Host trusted.example.com
    StrictHostKeyChecking no       # Dangerous: auto-accept new keys

Host secure.example.com
    StrictHostKeyChecking yes      # Reject unknown hosts
```

#### 9.2.9 VerifyHostKeyDNS

SSHFP verification:

```
Host *
    VerifyHostKeyDNS yes           # Trust SSHFP records
    VerifyHostKeyDNS ask           # Prompt if SSHFP present
```

#### 9.2.10 UpdateHostKeys

Automatic host key updates:

```
Host *
    UpdateHostKeys yes             # Learn new keys from server
```

### 9.3 SSH Server Configuration

#### 9.3.1 UseDNS

Reverse DNS for client authentication:

```
# /etc/ssh/sshd_config
UseDNS no    # Recommended: disable for faster connections
UseDNS yes   # Enable for hostname-based access control
```

#### 9.3.2 ListenAddress

Specify listening addresses:

```
# Listen on specific IP
ListenAddress 192.0.2.1

# Listen on all IPv4
ListenAddress 0.0.0.0

# Listen on all IPv6
ListenAddress ::
```

#### 9.3.3 AddressFamily (Server)

```
# Accept IPv4 only
AddressFamily inet

# Accept IPv6 only
AddressFamily inet6

# Accept both
AddressFamily any
```

### 9.4 SSH Config Pattern Matching

SSH config supports powerful pattern matching:

```
# Exact match
Host server.example.com

# Wildcard match
Host *.example.com

# Negation
Host * !*.evil.com

# Multiple patterns
Host server1 server2 server3

# All hosts
Host *
```

Match blocks (SSH 7.3+):
```
Match host *.internal.example.com exec "test -f /etc/on-corporate-network"
    ProxyJump bastion.example.com
```

### 9.5 DNS and Jump Hosts

#### 9.5.1 ProxyJump Configuration

```
Host internal-*
    ProxyJump bastion.example.com
```

DNS resolution:
- `bastion.example.com`: Resolved locally
- `internal-*`: Resolved by bastion

#### 9.5.2 Complex Jump Chains

```
Host deep-internal
    ProxyJump bastion1,bastion2,bastion3
```

Each hop resolves the next hostname.

#### 9.5.3 ProxyCommand with DNS Control

```
Host internal
    ProxyCommand ssh -W %h:%p bastion

# %h = target hostname (resolved by bastion)
# %n = original hostname from command line
```

### 9.6 Example: Complete SSH Config

```
# ~/.ssh/config

# Global defaults
Host *
    AddressFamily any
    CheckHostIP yes
    HashKnownHosts no
    StrictHostKeyChecking ask
    VerifyHostKeyDNS ask
    UpdateHostKeys yes
    ServerAliveInterval 60
    ServerAliveCountMax 3

# Canonical hostnames for internal network
Match host * exec "test -f ~/.on-corporate-network"
    CanonicalizeHostname yes
    CanonicalDomains corp.example.com
    CanonicalizeMaxDots 1

# Development servers
Host dev-*
    User developer
    IdentityFile ~/.ssh/dev_ed25519

# Production servers (extra security)
Host prod-*
    User admin
    IdentityFile ~/.ssh/prod_ed25519
    StrictHostKeyChecking yes
    VerifyHostKeyDNS yes

# Jump host configuration
Host bastion
    HostName bastion.example.com
    User jumpuser
    IdentityFile ~/.ssh/bastion_ed25519

Host internal-*
    ProxyJump bastion
    User internal_admin

# AWS instances (direct IP, no DNS)
Host aws-*
    IdentityFile ~/.ssh/aws.pem
    User ec2-user
    StrictHostKeyChecking no
    UserKnownHostsFile /dev/null
```



---

## Chapter 10: Security Considerations

### 10.1 DNS-Based Attacks on SSH

#### 10.1.1 DNS Spoofing/Cache Poisoning

An attacker who can control DNS responses can redirect SSH connections:

```
Normal Resolution:
client -> DNS -> server.example.com -> 192.0.2.1 (legitimate)

Poisoned Resolution:
client -> DNS (poisoned) -> server.example.com -> 192.0.2.100 (attacker)
```

SSH's host key verification is the primary defense:
- Client has cached host key for server.example.com
- Attacker's server presents different host key
- SSH warns user of changed key

```
@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
@    WARNING: REMOTE HOST IDENTIFICATION HAS CHANGED!     @
@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
IT IS POSSIBLE THAT SOMEONE IS DOING SOMETHING NASTY!
Someone could be eavesdropping on you right now (man-in-the-middle attack)!
It is also possible that a host key has just been changed.
The fingerprint for the ECDSA key sent by the remote host is
SHA256:xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx.
Please contact your system administrator.
Add correct host key in /home/user/.ssh/known_hosts to get rid of this message.
Offending ECDSA key in /home/user/.ssh/known_hosts:15
ECDSA host key for server.example.com has changed and you have requested
strict checking.
Host key verification failed.
```

#### 10.1.2 First Connection Vulnerability

The "trust on first use" (TOFU) model is vulnerable during the first connection:

```
First connection (vulnerable):
client -> DNS (poisoned) -> server.example.com -> 192.0.2.100 (attacker)
                                                  |
                                                  v
                                          Client accepts attacker's key
```

Mitigations:
- Use SSHFP records with DNSSEC
- Distribute known_hosts via configuration management
- Use SSH certificates
- Verify fingerprints out-of-band

#### 10.1.3 Homograph Attacks

Unicode domain names can be visually similar to legitimate domains:

```
Legitimate: server.example.com
Homograph:  ѕerver.example.com (Cyrillic 'ѕ')
```

SSH doesn't perform punycode conversion—it passes the hostname directly
to the resolver. Defense: Use IP addresses or internal DNS.

### 10.2 DNSSEC for SSH Security

DNSSEC provides cryptographic authentication of DNS records:

```
+------------------+      +------------------+      +------------------+
|   Root Zone      |  ->  |    TLD Zone      |  ->  |   Domain Zone    |
| (Trust Anchor)   |      |    (DS record)   |      |   (DNSKEY)       |
+------------------+      +------------------+      +------------------+
        |                         |                         |
        v                         v                         v
   Root DNSKEY              TLD DNSKEY               Zone DNSKEY
        |                         |                         |
        v                         v                         v
   Signs DS for TLD         Signs DS for domain      Signs records
```

Benefits for SSH:
- Authenticated SSHFP records
- Protection against cache poisoning
- Confidence in A/AAAA record authenticity

### 10.3 DNS Rebinding Attacks

DNS rebinding can bypass security controls:

```
1. Client connects to attacker.com, gets IP 203.0.113.1 (attacker)
2. Attacker serves malicious content
3. DNS TTL expires
4. Same hostname now resolves to 192.168.1.100 (internal network)
5. Attacker's code can now access internal resources
```

SSH is generally less vulnerable because:
- SSH doesn't run arbitrary code like browsers
- Connection is to a specific port (22)
- Host key verification would detect changed server

### 10.4 Reverse DNS Security

#### 10.4.1 PTR Record Spoofing

If `UseDNS yes` on server:

```
1. Attacker connects from 203.0.113.50
2. Server queries PTR for 203.0.113.50
3. Attacker controls reverse zone, returns "admin.internal.com"
4. If "from=" restriction trusts *.internal.com, attacker bypasses
```

Proper implementation:
```
1. PTR lookup: 203.0.113.50 -> admin.internal.com
2. Forward lookup: admin.internal.com -> 203.0.113.50 (must match!)
3. Only if forward/reverse match, hostname is trusted
```

#### 10.4.2 Best Practice

```
# /etc/ssh/sshd_config
UseDNS no
```

Use IP-based restrictions or firewall rules instead.

### 10.5 DNS Tunneling and SSH

SSH connections can be tunneled over DNS:

```bash
# Using iodine for DNS tunneling
$ iodine -f tunnel.example.com
# Then SSH through the tunnel
$ ssh -p 22 user@192.168.99.1
```

This bypasses firewalls that only allow DNS traffic but has security
implications for both detection and performance.

### 10.6 Split-Horizon DNS Risks

Split-horizon DNS serves different records for internal vs external clients:

```
External DNS:
server.example.com -> 93.184.216.34 (public IP)

Internal DNS:
server.example.com -> 10.0.1.50 (private IP)
```

Risks for SSH:
- Users on wrong network connect to wrong server
- Host key mismatch confuses users
- Potential for MITM if attacker controls either IP

Mitigation: Use distinct hostnames for internal/external access.

### 10.7 DNS Leaks with SSH Tunnels

When using SSH as a SOCKS proxy, DNS leaks can expose browsing activity:

```
Correct: Browser -> SOCKS5 -> SSH tunnel -> DNS query -> target
Leak:    Browser -> Local DNS -> ISP sees query
```

Prevention:
- Configure browser for remote DNS resolution
- Use transparent proxy mode
- Verify with DNS leak test sites

### 10.8 Certificate Authority Compromise

If using SSH certificates, CA compromise affects all hosts:

```bash
# SSH certificate-based host authentication
$ ssh-keygen -s /path/to/ca -I host_id -h /etc/ssh/ssh_host_ed25519_key.pub
```

No DNS dependency, but related security consideration for enterprise SSH.

### 10.9 Security Recommendations

#### 10.9.1 Client-Side

1. Enable StrictHostKeyChecking for sensitive hosts
2. Use VerifyHostKeyDNS with DNSSEC when possible
3. Maintain up-to-date known_hosts
4. Use SSH certificates for enterprise environments
5. Verify fingerprints for first connections

#### 10.9.2 Server-Side

1. Disable UseDNS (`UseDNS no`)
2. Use IP-based restrictions instead of hostname-based
3. Implement firewall rules
4. Consider SSH certificates
5. Monitor for brute force attempts

#### 10.9.3 Infrastructure

1. Deploy DNSSEC
2. Use DNS-over-TLS or DNS-over-HTTPS
3. Monitor DNS for suspicious queries
4. Implement split-horizon carefully
5. Use configuration management for known_hosts

---

## Chapter 11: Troubleshooting DNS for SSH

### 11.1 Common DNS Issues

#### 11.1.1 "Could not resolve hostname"

```bash
$ ssh server.example.com
ssh: Could not resolve hostname server.example.com: Name or service not known
```

Debugging steps:
```bash
# 1. Check basic resolution
$ nslookup server.example.com
$ dig server.example.com

# 2. Check /etc/hosts
$ grep server.example.com /etc/hosts

# 3. Check /etc/resolv.conf
$ cat /etc/resolv.conf

# 4. Check search domain
$ dig +search server  # Uses search domains

# 5. Test with explicit resolver
$ dig @8.8.8.8 server.example.com
```

#### 11.1.2 Connection Timeout (DNS Delay)

```bash
$ ssh server.example.com
# Hangs for a long time before connecting
```

Possible causes:
- Reverse DNS lookup failing (`UseDNS yes` on server)
- IPv6 tried first but failing
- DNS server slow or unreachable

Debugging:
```bash
# Test with verbose mode
$ ssh -v server.example.com 2>&1 | grep -i dns

# Force IPv4
$ ssh -4 server.example.com

# Check reverse DNS
$ dig -x $(dig +short server.example.com)
```

#### 11.1.3 Host Key Changed After IP Change

```
@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
@    WARNING: REMOTE HOST IDENTIFICATION HAS CHANGED!     @
@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
```

If this is expected (e.g., DNS pointed to new server):
```bash
# Remove old entry
$ ssh-keygen -R server.example.com

# Or edit known_hosts manually
$ vim ~/.ssh/known_hosts
```

### 11.2 Diagnostic Tools

#### 11.2.1 dig (DNS lookup utility)

```bash
# Basic query
$ dig server.example.com

# Specific record type
$ dig A server.example.com
$ dig AAAA server.example.com
$ dig SSHFP server.example.com

# Short output
$ dig +short server.example.com

# Trace resolution
$ dig +trace server.example.com

# Check specific resolver
$ dig @8.8.8.8 server.example.com

# Show DNSSEC info
$ dig +dnssec server.example.com
```

#### 11.2.2 nslookup

```bash
# Simple lookup
$ nslookup server.example.com

# Specific server
$ nslookup server.example.com 8.8.8.8

# Reverse lookup
$ nslookup 192.0.2.1
```

#### 11.2.3 host

```bash
# Simple lookup
$ host server.example.com

# Verbose output
$ host -v server.example.com

# Specific type
$ host -t SSHFP server.example.com
```

#### 11.2.4 getent

```bash
# Query NSS (respects /etc/hosts and nsswitch.conf)
$ getent hosts server.example.com
$ getent ahosts server.example.com  # All addresses
```

#### 11.2.5 resolvectl (systemd-resolved)

```bash
# Query through systemd-resolved
$ resolvectl query server.example.com

# Check resolver status
$ resolvectl status

# Flush cache
$ resolvectl flush-caches

# View statistics
$ resolvectl statistics
```

### 11.3 SSH Verbose Mode

```bash
# Single verbose level
$ ssh -v user@server.example.com

# Maximum verbosity
$ ssh -vvv user@server.example.com
```

Relevant output for DNS issues:
```
debug1: Connecting to server.example.com [192.0.2.1] port 22.
debug1: Connection established.
```

### 11.4 Network Tracing

#### 11.4.1 tcpdump

```bash
# Capture DNS traffic
$ sudo tcpdump -i any port 53

# Capture SSH and DNS
$ sudo tcpdump -i any 'port 53 or port 22'

# Write to file for analysis
$ sudo tcpdump -i any -w ssh_dns.pcap 'port 53 or port 22'
```

#### 11.4.2 Wireshark Filters

```
# DNS queries only
dns

# SSH traffic
tcp.port == 22

# Specific hostname
dns.qry.name == "server.example.com"

# DNS and SSH
dns or ssh
```

### 11.5 Common Fixes

#### 11.5.1 Add to /etc/hosts

```
# /etc/hosts
192.0.2.1    server.example.com server
```

#### 11.5.2 Fix /etc/resolv.conf

```
# /etc/resolv.conf
nameserver 8.8.8.8
nameserver 8.8.4.4
options timeout:5 attempts:2
search example.com
```

#### 11.5.3 Force IP Version

```
# ~/.ssh/config
Host slow-server
    AddressFamily inet  # Force IPv4
```

#### 11.5.4 Disable CheckHostIP

If IP changes frequently:
```
Host dynamic-ip-host
    CheckHostIP no
```

#### 11.5.5 Clear DNS Cache

```bash
# macOS
$ sudo dscacheutil -flushcache
$ sudo killall -HUP mDNSResponder

# Linux (systemd)
$ sudo systemctl restart systemd-resolved
# or
$ resolvectl flush-caches

# Linux (nscd)
$ sudo nscd -i hosts
```

### 11.6 Platform-Specific Issues

#### 11.6.1 macOS

- Uses `mDNSResponder` for DNS
- `.local` domain uses multicast DNS (mDNS)
- Check with `scutil --dns`

```bash
$ scutil --dns
DNS configuration
resolver #1
  nameserver[0] : 192.168.1.1
  flags    : Request A records
  reach    : 0x00020002 (Reachable,Directly Reachable Address)
```

#### 11.6.2 Linux

- `/etc/nsswitch.conf` controls resolution order
- systemd-resolved may intercept queries
- Check with `resolvectl status`

```bash
$ cat /etc/nsswitch.conf
hosts: files mdns4_minimal [NOTFOUND=return] dns myhostname

$ resolvectl status
Global
       LLMNR setting: yes
MulticastDNS setting: yes
  DNSOverTLS setting: opportunistic
      DNSSEC setting: allow-downgrade
```

#### 11.6.3 Windows (WSL)

```bash
# Check WSL DNS settings
$ cat /etc/resolv.conf
# This file was automatically generated by WSL.
nameserver 172.30.96.1

# May need manual configuration for corporate networks
```

### 11.7 Logging and Monitoring

#### Server-Side Logging

```
# /etc/ssh/sshd_config
LogLevel DEBUG3

# View logs
$ sudo journalctl -u sshd -f
$ sudo tail -f /var/log/auth.log
```

#### Client-Side Debug

```bash
# Log SSH debug output
$ ssh -vvv user@host 2>&1 | tee ssh_debug.log
```

---

## Chapter 12: Advanced Topics

### 12.1 DNS-SD (DNS Service Discovery)

DNS-SD (RFC 6763) allows services to advertise via DNS:

```
_ssh._tcp.example.com.  IN  PTR  server._ssh._tcp.example.com.
server._ssh._tcp.example.com.  IN  SRV  0 0 22 server.example.com.
server._ssh._tcp.example.com.  IN  TXT  "txtvers=1" "user=admin"
```

Usage:
```bash
# Discover SSH services (using avahi)
$ avahi-browse -t _ssh._tcp
```

### 12.2 Multicast DNS (mDNS)

mDNS (RFC 6762) enables local network name resolution without a DNS server:

```bash
# .local domain uses mDNS
$ ssh raspberry.local

# Avahi on Linux
$ avahi-resolve -n server.local
```

How it works:
- Query sent to 224.0.0.251:5353 (IPv4) or ff02::fb:5353 (IPv6)
- All devices on local network receive query
- Device with matching name responds

### 12.3 LLMNR (Link-Local Multicast Name Resolution)

Windows equivalent to mDNS:
- Uses 224.0.0.252:5355 (IPv4) or ff02::1:3:5355 (IPv6)
- Falls back when DNS fails
- Can be a security risk (responder attacks)

### 12.4 Split DNS and VPN

#### 12.4.1 Corporate VPN Split DNS

```
VPN Connected:
  *.corp.example.com -> Corporate DNS
  *.                 -> Public DNS

VPN Disconnected:
  *.                 -> Public DNS
```

Impact on SSH:
- Internal servers only reachable when VPN connected
- Different SSH configs may be needed
- known_hosts may have different entries

#### 12.4.2 Conditional DNS Configuration

```
# Using systemd-resolved
$ resolvectl dns tun0 10.0.0.53
$ resolvectl domain tun0 ~corp.example.com
```

### 12.5 DNS Load Balancing

#### Round-Robin DNS

```
server.example.com.  IN  A  192.0.2.1
server.example.com.  IN  A  192.0.2.2
server.example.com.  IN  A  192.0.2.3
```

SSH behavior:
- Receives all addresses from getaddrinfo()
- Connects to first address
- If fails, tries next
- May hit different server each connection

Implications:
- Different host keys per server
- known_hosts may have multiple entries
- Consider using individual hostnames

#### GeoDNS

Different IPs returned based on client location:

```
# Client in US
server.example.com -> 192.0.2.1 (US datacenter)

# Client in EU
server.example.com -> 198.51.100.1 (EU datacenter)
```

### 12.6 DANE for SSH

DANE (DNS-Based Authentication of Named Entities) can complement SSHFP:

```
_22._tcp.server.example.com.  IN  TLSA  3 1 1 abc123...
```

While primarily for TLS, the concept extends to any certificate-based
authentication.

### 12.7 SSH Certificates

SSH certificates reduce DNS dependency for host verification:

```bash
# Create CA
$ ssh-keygen -t ed25519 -f ca_key

# Sign host key
$ ssh-keygen -s ca_key -I host_id -h -n server.example.com \
    /etc/ssh/ssh_host_ed25519_key.pub

# Client trusts CA, not individual host keys
# ~/.ssh/known_hosts
@cert-authority *.example.com ssh-ed25519 AAAA...
```

Benefits:
- No need for SSHFP records
- No TOFU vulnerability
- Centralized trust management

### 12.8 Dynamic DNS (DDNS)

For hosts with dynamic IPs:

```bash
# Update script example
$ nsupdate -v << EOF
server ns1.example.com
zone example.com
update delete home.example.com A
update add home.example.com 300 A $CURRENT_IP
send
EOF
```

SSH considerations:
- Short TTL for quick updates
- CheckHostIP no may be needed
- Consider hostname-only known_hosts

### 12.9 Kubernetes and Container DNS

#### CoreDNS in Kubernetes

```
# Pod DNS resolution
<service>.<namespace>.svc.cluster.local

# SSH to pod (if exposed)
$ ssh user@myapp.default.svc.cluster.local
```

#### Docker DNS

```
# Docker internal DNS
$ docker run --name myserver ...
$ docker exec another_container ssh user@myserver
# Docker resolves container names
```

### 12.10 Cloud Provider DNS

#### AWS Route 53

- Private hosted zones
- Alias records (AWS-specific)
- Health checks for failover

```
# Private zone in VPC
server.internal.example.com -> 10.0.1.50
```

#### GCP Cloud DNS

- Private zones
- Cross-project resolution
- DNS peering

#### Azure DNS

- Private DNS zones
- VNet integration
- Automatic VM registration

### 12.11 IPv6 and SSH

#### IPv6 Resolution

```bash
# Force IPv6
$ ssh -6 user@server.example.com

# Connect to specific IPv6 address
$ ssh user@2001:db8::1

# Connect to link-local (requires interface)
$ ssh user@fe80::1%eth0
```

#### IPv6 in SSH Config

```
Host ipv6server
    HostName 2001:db8::1
    AddressFamily inet6
```

### 12.12 Tor Hidden Services

SSH over Tor uses .onion addresses (no DNS):

```bash
# Tor hidden service
$ ssh user@abcdefghij234567.onion -o ProxyCommand='nc -X 5 -x 127.0.0.1:9050 %h %p'
```

The .onion address is resolved within the Tor network, bypassing DNS entirely.


---

## Chapter 13: Best Practices

### 13.1 Enterprise SSH DNS Architecture

#### 13.1.1 Recommended Architecture

```
                    +-------------------+
                    |   External DNS    |
                    |   (Public zones)  |
                    +-------------------+
                            |
                            | Split-horizon
                            |
+---------------------------+---------------------------+
|                           |                           |
v                           v                           v
+---------------+   +---------------+   +---------------+
| DMZ DNS       |   | Corp DNS      |   | Dev DNS       |
| bastion.*     |   | internal.*    |   | dev.*         |
+---------------+   +---------------+   +---------------+
       |                    |                   |
       v                    v                   v
+---------------+   +---------------+   +---------------+
| Bastion Hosts |   | Prod Servers  |   | Dev Servers   |
+---------------+   +---------------+   +---------------+
```

#### 13.1.2 DNS Best Practices

1. **Separate zones for environments**
   - dev.example.com for development
   - staging.example.com for staging
   - prod.example.com for production

2. **DNSSEC everywhere**
   - Sign all zones
   - Validate on all resolvers
   - Use SSHFP records

3. **Consistent naming**
   - Hostname patterns: role-env-number.zone
   - Example: web-prod-001.prod.example.com

4. **Appropriate TTLs**
   - Stable servers: 3600 seconds (1 hour)
   - Dynamic environments: 300 seconds (5 minutes)
   - SSHFP records: 3600 seconds

### 13.2 SSH Client Best Practices

#### 13.2.1 ~/.ssh/config Template

```
# ~/.ssh/config - Recommended configuration

# Global defaults
Host *
    # Security settings
    HashKnownHosts yes
    StrictHostKeyChecking ask
    VerifyHostKeyDNS ask
    UpdateHostKeys yes

    # Performance settings
    AddressFamily inet
    ServerAliveInterval 60
    ServerAliveCountMax 3

    # Key settings
    IdentitiesOnly yes
    PreferredAuthentications publickey,keyboard-interactive,password

# Development environment
Host dev-*
    HostName %h.dev.example.com
    User developer
    IdentityFile ~/.ssh/dev_key

# Staging environment
Host staging-*
    HostName %h.staging.example.com
    User deployer
    IdentityFile ~/.ssh/staging_key
    StrictHostKeyChecking yes

# Production environment (most secure)
Host prod-*
    HostName %h.prod.example.com
    User admin
    IdentityFile ~/.ssh/prod_key
    StrictHostKeyChecking yes
    VerifyHostKeyDNS yes
    LogLevel VERBOSE

# Bastion hosts
Host bastion
    HostName bastion.example.com
    User jump
    IdentityFile ~/.ssh/bastion_key
    ControlMaster auto
    ControlPath ~/.ssh/sockets/%r@%h-%p
    ControlPersist 600

# Internal hosts via bastion
Host internal-*
    ProxyJump bastion
    User internal_admin
```

#### 13.2.2 Known Hosts Management

Options for managing known_hosts:

1. **Manual management**
   ```bash
   # Add host key manually
   $ ssh-keyscan server.example.com >> ~/.ssh/known_hosts
   ```

2. **Configuration management**
   ```yaml
   # Ansible example
   - name: Deploy known_hosts
     copy:
       src: files/known_hosts
       dest: /home/{{ user }}/.ssh/known_hosts
       mode: '0600'
   ```

3. **SSH Certificates (recommended for enterprise)**
   ```
   @cert-authority *.example.com ssh-ed25519 AAAA...
   ```

### 13.3 SSH Server Best Practices

#### 13.3.1 /etc/ssh/sshd_config Template

```
# /etc/ssh/sshd_config - Recommended configuration

# Network
Port 22
AddressFamily any
ListenAddress 0.0.0.0
ListenAddress ::

# DNS (disable for performance)
UseDNS no

# Authentication
PermitRootLogin no
PubkeyAuthentication yes
PasswordAuthentication no
PermitEmptyPasswords no
ChallengeResponseAuthentication no

# Security
Protocol 2
HostKey /etc/ssh/ssh_host_ed25519_key
HostKey /etc/ssh/ssh_host_rsa_key

# Key exchange
KexAlgorithms curve25519-sha256,curve25519-sha256@libssh.org

# Ciphers
Ciphers chacha20-poly1305@openssh.com,aes256-gcm@openssh.com

# MACs
MACs hmac-sha2-512-etm@openssh.com,hmac-sha2-256-etm@openssh.com

# Logging
SyslogFacility AUTH
LogLevel INFO

# Session
X11Forwarding no
AllowAgentForwarding no
AllowTcpForwarding no
PrintMotd no
PrintLastLog yes
TCPKeepAlive yes
ClientAliveInterval 300
ClientAliveCountMax 2

# Access control (use IPs, not hostnames)
AllowUsers admin@192.168.1.0/24
DenyUsers *@*
```

### 13.4 DNS Security Best Practices

#### 13.4.1 DNSSEC Deployment Checklist

1. **Zone signing**
   ```bash
   # Generate zone signing key (ZSK)
   $ dnssec-keygen -a ECDSAP256SHA256 example.com

   # Generate key signing key (KSK)
   $ dnssec-keygen -a ECDSAP256SHA256 -f KSK example.com

   # Sign zone
   $ dnssec-signzone -o example.com db.example.com
   ```

2. **DS record publication**
   - Submit DS record to registrar
   - Verify DNSSEC chain with tools

3. **Validation on resolvers**
   ```
   # BIND configuration
   dnssec-validation auto;
   ```

#### 13.4.2 SSHFP Deployment

```bash
# 1. Generate SSHFP records
$ ssh-keygen -r $(hostname -f)

# 2. Add to DNS zone
# 3. Sign zone with DNSSEC
# 4. Configure clients
# VerifyHostKeyDNS yes
```

### 13.5 Monitoring and Alerting

#### 13.5.1 DNS Monitoring

```bash
# Monitor DNS resolution time
$ time dig server.example.com

# Monitor DNSSEC validation
$ dig +dnssec server.example.com | grep -c 'ad'

# Monitor SSHFP presence
$ dig SSHFP server.example.com +short | wc -l
```

#### 13.5.2 SSH Monitoring

```bash
# Monitor SSH connection success
$ ssh -o BatchMode=yes -o ConnectTimeout=5 server.example.com exit
$ echo $?  # 0 = success

# Monitor host key changes
$ ssh-keyscan server.example.com 2>/dev/null | diff - known_hosts_backup
```

### 13.6 Disaster Recovery

#### 13.6.1 DNS Failure Scenarios

| Scenario | Impact | Mitigation |
|----------|--------|------------|
| DNS server down | Can't resolve hostnames | Use /etc/hosts backup |
| DNSSEC validation failure | Resolution fails | Have non-validating fallback |
| DNS cache poisoning | Wrong server connected | Host key verification |
| Zone file corruption | Missing/wrong records | Regular zone backups |

#### 13.6.2 Recovery Procedures

```bash
# Emergency: DNS completely down
# 1. Add critical hosts to /etc/hosts
$ echo "192.0.2.1 critical-server.example.com" >> /etc/hosts

# 2. Connect using IP directly
$ ssh user@192.0.2.1

# 3. Use backup DNS
$ echo "nameserver 8.8.8.8" > /etc/resolv.conf.backup
$ sudo mv /etc/resolv.conf.backup /etc/resolv.conf
```

### 13.7 Performance Optimization

#### 13.7.1 Reduce DNS Latency

1. **Use local caching resolver**
   ```bash
   # Install and use dnsmasq
   $ sudo apt install dnsmasq
   ```

2. **Disable reverse DNS on server**
   ```
   UseDNS no
   ```

3. **Force IPv4 if IPv6 is slow**
   ```
   AddressFamily inet
   ```

4. **Use connection multiplexing**
   ```
   ControlMaster auto
   ControlPath ~/.ssh/sockets/%r@%h-%p
   ControlPersist 600
   ```

#### 13.7.2 Optimize SSH Connections

```
# ~/.ssh/config optimizations

Host *
    # Reuse connections
    ControlMaster auto
    ControlPath ~/.ssh/sockets/%r@%h-%p
    ControlPersist 600

    # Compression for slow links
    Compression yes

    # Faster key exchange
    KexAlgorithms curve25519-sha256@libssh.org

    # Faster ciphers
    Ciphers chacha20-poly1305@openssh.com
```

### 13.8 Audit and Compliance

#### 13.8.1 SSH Audit Checklist

- [ ] All servers use key-based authentication
- [ ] Password authentication disabled
- [ ] Root login disabled
- [ ] UseDNS disabled on servers
- [ ] Host keys rotated periodically
- [ ] SSHFP records published and DNSSEC-signed
- [ ] known_hosts distributed via configuration management
- [ ] SSH logs monitored and retained
- [ ] Failed login attempts alerted

#### 13.8.2 DNS Audit Checklist

- [ ] All zones DNSSEC-signed
- [ ] DS records published at registrar
- [ ] DNSSEC validation enabled on resolvers
- [ ] DNS query logging enabled
- [ ] Zone transfer restrictions in place
- [ ] TTLs appropriate for each record type
- [ ] Reverse DNS properly configured
- [ ] DNS servers monitored and redundant

---

## Chapter 14: Reference Tables

### 14.1 DNS Record Types for SSH

| Record Type | Purpose | Example |
|-------------|---------|---------|
| A | IPv4 address | server.example.com. IN A 192.0.2.1 |
| AAAA | IPv6 address | server.example.com. IN AAAA 2001:db8::1 |
| CNAME | Alias | ssh.example.com. IN CNAME server.example.com. |
| PTR | Reverse lookup | 1.2.0.192.in-addr.arpa. IN PTR server.example.com. |
| SSHFP | Host key fingerprint | server.example.com. IN SSHFP 4 2 abc123... |
| SRV | Service location | _ssh._tcp.example.com. IN SRV 0 0 22 server.example.com. |

### 14.2 SSH Client Options Reference

| Option | Values | Description |
|--------|--------|-------------|
| AddressFamily | any/inet/inet6 | IP version preference |
| CanonicalizeHostname | yes/no/always | Enable hostname canonicalization |
| CanonicalDomains | domain list | Domains to try for canonicalization |
| CheckHostIP | yes/no | Verify IP in known_hosts |
| StrictHostKeyChecking | yes/no/ask | Host key verification policy |
| VerifyHostKeyDNS | yes/no/ask | Use SSHFP for verification |
| UpdateHostKeys | yes/no | Auto-update known host keys |
| ConnectTimeout | seconds | Connection timeout |
| ProxyJump | host list | Jump host chain |
| ProxyCommand | command | Custom proxy command |

### 14.3 SSH Server Options Reference

| Option | Values | Description |
|--------|--------|-------------|
| UseDNS | yes/no | Reverse DNS for clients |
| AddressFamily | any/inet/inet6 | Accepted IP versions |
| ListenAddress | IP address | Binding address |
| LogLevel | QUIET to DEBUG3 | Logging verbosity |

### 14.4 SSHFP Algorithm Numbers

| Number | Algorithm | Status |
|--------|-----------|--------|
| 1 | RSA | Supported |
| 2 | DSA | Deprecated |
| 3 | ECDSA | Supported |
| 4 | Ed25519 | Recommended |
| 6 | Ed448 | Supported |

### 14.5 SSHFP Fingerprint Types

| Number | Hash Algorithm | Status |
|--------|----------------|--------|
| 1 | SHA-1 | Deprecated |
| 2 | SHA-256 | Recommended |

### 14.6 Common Ports

| Port | Protocol | Description |
|------|----------|-------------|
| 22 | SSH | Standard SSH |
| 53 | DNS | Standard DNS |
| 853 | DoT | DNS over TLS |
| 443 | DoH | DNS over HTTPS |
| 5353 | mDNS | Multicast DNS |

### 14.7 DNS Response Codes

| Code | Name | Description |
|------|------|-------------|
| 0 | NOERROR | Successful |
| 1 | FORMERR | Format error |
| 2 | SERVFAIL | Server failure |
| 3 | NXDOMAIN | Domain not found |
| 4 | NOTIMP | Not implemented |
| 5 | REFUSED | Query refused |

---

## Chapter 15: Glossary

### A

**A Record**: DNS record mapping hostname to IPv4 address.

**AAAA Record**: DNS record mapping hostname to IPv6 address.

**AddressFamily**: SSH option controlling IPv4/IPv6 preference.

**Anycast**: Network addressing where multiple servers share an IP address.

**Authoritative Nameserver**: DNS server with definitive records for a zone.

### C

**Cache Poisoning**: Attack inserting false DNS records into cache.

**Canonicalization**: Converting hostname to its canonical (standard) form.

**CNAME**: Canonical Name DNS record creating an alias.

**Connection Multiplexing**: Reusing SSH connections for multiple sessions.

### D

**DANE**: DNS-Based Authentication of Named Entities.

**DDNS**: Dynamic DNS - automatic DNS updates for changing IPs.

**DNSSEC**: DNS Security Extensions - cryptographic DNS authentication.

**DoH**: DNS over HTTPS - encrypted DNS using HTTPS.

**DoT**: DNS over TLS - encrypted DNS using TLS.

### E

**EDNS**: Extension mechanisms for DNS.

### F

**FQDN**: Fully Qualified Domain Name (e.g., server.example.com.).

### G

**getaddrinfo()**: POSIX function for DNS resolution.

**gTLD**: Generic Top-Level Domain (e.g., .com, .org).

### H

**Happy Eyeballs**: Algorithm for racing IPv4/IPv6 connections.

**Host Key**: SSH server's public key for authentication.

### I

**Iterative Resolution**: DNS resolution where client follows referrals.

### J

**Jump Host**: Intermediate SSH server (bastion) for accessing internal hosts.

### K

**Known Hosts**: File containing verified SSH host keys.

### L

**LLMNR**: Link-Local Multicast Name Resolution (Windows).

### M

**mDNS**: Multicast DNS for local network resolution.

**MITM**: Man-in-the-Middle attack.

### N

**NSS**: Name Service Switch - OS name resolution configuration.

**NXDOMAIN**: DNS response indicating domain doesn't exist.

### P

**ProxyJump**: SSH option for jump host connections.

**PTR Record**: DNS record for reverse lookup (IP to hostname).

### R

**Recursive Resolution**: DNS resolution where resolver does all work.

**Resolver**: DNS client or caching nameserver.

**Reverse DNS**: Mapping IP address to hostname.

### S

**Split-Horizon DNS**: Different DNS responses based on query source.

**SSHFP**: SSH Fingerprint DNS record.

**Stub Resolver**: Basic DNS client in operating system.

### T

**TLD**: Top-Level Domain (e.g., .com, .org, .uk).

**TOFU**: Trust On First Use - accepting unknown host keys.

**TTL**: Time To Live - how long DNS records can be cached.

### U

**UseDNS**: SSH server option for reverse DNS lookup.

### V

**VerifyHostKeyDNS**: SSH option to use SSHFP records.

### Z

**Zone**: DNS administrative division (e.g., example.com).

---

## Chapter 16: Appendices

### Appendix A: Quick Reference Commands

#### DNS Troubleshooting
```bash
# Basic resolution
dig server.example.com
nslookup server.example.com
host server.example.com

# Detailed resolution
dig +trace server.example.com
dig +dnssec server.example.com

# Reverse DNS
dig -x 192.0.2.1

# SSHFP records
dig SSHFP server.example.com

# Cache management
resolvectl flush-caches     # Linux
sudo killall -HUP mDNSResponder  # macOS
```

#### SSH Troubleshooting
```bash
# Verbose connection
ssh -vvv user@server

# Test host key
ssh-keyscan server.example.com

# Generate SSHFP records
ssh-keygen -r server.example.com

# Remove known host
ssh-keygen -R server.example.com

# Force IPv4/IPv6
ssh -4 user@server
ssh -6 user@server
```

### Appendix B: Example Zone File

```
; Zone file for example.com with SSH support
$TTL 3600
@       IN      SOA     ns1.example.com. admin.example.com. (
                        2024010101      ; Serial (YYYYMMDDNN)
                        3600            ; Refresh (1 hour)
                        900             ; Retry (15 minutes)
                        604800          ; Expire (1 week)
                        86400           ; Minimum TTL (1 day)
                        )

; Name servers
        IN      NS      ns1.example.com.
        IN      NS      ns2.example.com.

; Name server addresses
ns1     IN      A       192.0.2.10
ns1     IN      AAAA    2001:db8::10
ns2     IN      A       192.0.2.11
ns2     IN      AAAA    2001:db8::11

; SSH servers
bastion IN      A       192.0.2.100
bastion IN      AAAA    2001:db8::100
bastion IN      SSHFP   4 2 abc123def456...

server1 IN      A       192.0.2.101
server1 IN      AAAA    2001:db8::101
server1 IN      SSHFP   4 2 def789ghi012...

server2 IN      A       192.0.2.102
server2 IN      AAAA    2001:db8::102
server2 IN      SSHFP   4 2 ghi345jkl678...

; Aliases
ssh     IN      CNAME   bastion
```

### Appendix C: Complete SSH Config Example

```
# ~/.ssh/config - Complete example with DNS considerations

# ============================================================
# Global Defaults
# ============================================================
Host *
    # Security
    HashKnownHosts yes
    StrictHostKeyChecking ask
    VerifyHostKeyDNS ask
    UpdateHostKeys yes
    IdentitiesOnly yes

    # Performance
    AddressFamily inet
    ServerAliveInterval 60
    ServerAliveCountMax 3
    Compression yes

    # Connection reuse
    ControlMaster auto
    ControlPath ~/.ssh/sockets/%r@%h-%p
    ControlPersist 600

# ============================================================
# Hostname Canonicalization
# ============================================================
Match host * exec "test -f ~/.on-corporate-network"
    CanonicalizeHostname yes
    CanonicalDomains corp.example.com example.com
    CanonicalizeMaxDots 1
    CanonicalizeFallbackLocal yes

# ============================================================
# Bastion/Jump Hosts
# ============================================================
Host bastion jump
    HostName bastion.example.com
    User jump
    IdentityFile ~/.ssh/id_bastion
    ForwardAgent no

# ============================================================
# Development Environment
# ============================================================
Host dev-*
    HostName %h.dev.example.com
    User developer
    IdentityFile ~/.ssh/id_dev
    StrictHostKeyChecking no
    UserKnownHostsFile /dev/null

# ============================================================
# Staging Environment
# ============================================================
Host staging-*
    HostName %h.staging.example.com
    User deployer
    IdentityFile ~/.ssh/id_staging
    ProxyJump bastion

# ============================================================
# Production Environment (Maximum Security)
# ============================================================
Host prod-*
    HostName %h.prod.example.com
    User admin
    IdentityFile ~/.ssh/id_prod
    StrictHostKeyChecking yes
    VerifyHostKeyDNS yes
    ProxyJump bastion
    LogLevel VERBOSE

# ============================================================
# Cloud Providers
# ============================================================
Host aws-*
    IdentityFile ~/.ssh/aws-key.pem
    User ec2-user
    StrictHostKeyChecking accept-new

Host gcp-*
    IdentityFile ~/.ssh/google_compute_engine
    User $(whoami)

Host azure-*
    IdentityFile ~/.ssh/azure-key
    User azureuser

# ============================================================
# Special Cases
# ============================================================
Host github.com
    HostName github.com
    User git
    IdentityFile ~/.ssh/id_github

Host gitlab.com
    HostName gitlab.com
    User git
    IdentityFile ~/.ssh/id_gitlab

# IPv6 only host
Host ipv6server
    HostName 2001:db8::1
    AddressFamily inet6

# Tor hidden service
Host *.onion
    ProxyCommand nc -X 5 -x 127.0.0.1:9050 %h %p
```

### Appendix D: Troubleshooting Decision Tree

```
SSH Connection Problem
         |
         v
    Can you ping the server?
         |
    +----+----+
    |         |
   Yes        No
    |          |
    v          v
  DNS OK?    Network issue
    |         - Check routing
   Yes        - Check firewall
    |         - Check VPN
    v
  SSH connects?
    |
    +----+----+
    |         |
   Yes        No
    |          |
    v          v
  Auth OK?   Connection refused?
    |          |
   Yes         +----+----+
    |          |         |
   Done       Yes        No
               |          |
               v          v
           Port 22    Timeout?
           blocked?      |
               |         v
               v      Check DNS
           Check     Check firewall
           firewall  Check routing
```

---

## Chapter 17: Further Reading

### RFCs

- **RFC 1034/1035**: Domain Names - Concepts and Implementation
- **RFC 4033-4035**: DNS Security (DNSSEC)
- **RFC 4251-4254**: SSH Protocol Architecture
- **RFC 4255**: SSHFP Records
- **RFC 6594**: SSHFP with SHA-256
- **RFC 7479**: SSHFP with Ed25519
- **RFC 6762**: Multicast DNS
- **RFC 6763**: DNS-Based Service Discovery
- **RFC 8305**: Happy Eyeballs Version 2
- **RFC 8484**: DNS over HTTPS
- **RFC 7858**: DNS over TLS
- **RFC 9250**: DNS over QUIC

### Books

- "SSH, The Secure Shell: The Definitive Guide" by Barrett, Silverman, Byrnes
- "DNS and BIND" by Cricket Liu and Paul Albitz
- "Pro DNS and BIND 10" by Ron Aitchison

### Online Resources

- OpenSSH Manual Pages: https://www.openssh.com/manual.html
- IANA DNS Parameters: https://www.iana.org/assignments/dns-parameters
- DNSSEC Deployment Guide: https://www.icann.org/resources/pages/dnssec-what-is-it-why-important
- SSH.com Knowledge Base: https://www.ssh.com/academy

---

## Document Information

**Title**: DNS Resolution for SSH Connections: A Comprehensive Deep Dive

**Version**: 1.0

**Date**: January 2026

**Author**: Technical Documentation Team

**Scope**: This document provides comprehensive coverage of DNS resolution
mechanisms in the context of SSH connections, including comparisons with
other protocols, security considerations, and best practices.

**Audience**: System administrators, network engineers, security professionals,
and developers working with SSH and DNS infrastructure.

---

*End of Document*