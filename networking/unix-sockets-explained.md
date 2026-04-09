# Unix Domain Sockets - What Are Those .sock Files?

**Last Updated:** March 24, 2026

---

## What You're Seeing

```bash
~/.ssh/arista-ssh ❯ ls -la
srwxr-xr-x  agent.sock
srwxr-xr-x  cli.sock
```

Notice the `s` at the beginning: `srwxr-xr-x`
- `s` = **socket** (special file type)
- Not a regular file, not a directory
- It's an IPC (Inter-Process Communication) endpoint

---

## What is a Unix Domain Socket?

A Unix domain socket is like a **telephone line between two programs** on the same computer.

### Analogy: Phone System

```
Regular File (like a letter):
┌──────────┐                    ┌──────────┐
│ Program A│ writes to file     │ Program B│
│          │ ─────────────────> │          │
│          │                    │ reads file│
└──────────┘                    └──────────┘
• One-way communication
• Data stored on disk
• Slow (disk I/O)

Unix Socket (like a phone call):
┌──────────┐                    ┌──────────┐
│ Program A│ <───────────────> │ Program B│
│          │   bidirectional    │          │
│          │   real-time        │          │
└──────────┘                    └──────────┘
• Two-way communication
• Data in memory (no disk)
• Fast (direct IPC)
```

---

## Types of Sockets

### 1. Network Sockets (TCP/IP)
```
Your Mac                        Remote Server
┌──────────┐                   ┌──────────┐
│ Browser  │ ─── Internet ───> │ Web      │
│          │   TCP socket      │ Server   │
└──────────┘   (port 443)      └──────────┘

Address: IP:Port (e.g., 192.168.1.1:443)
```

### 2. Unix Domain Sockets (Local IPC)
```
Your Mac
┌──────────────────────────────────────┐
│                                      │
│  ┌──────────┐         ┌──────────┐  │
│  │ SSH      │ ◄─────► │ arista-  │  │
│  │ Client   │  socket │ ssh-agent│  │
│  └──────────┘         └──────────┘  │
│                                      │
└──────────────────────────────────────┘

Address: File path (e.g., ~/.ssh/arista-ssh/agent.sock)
```

---

## How Unix Sockets Work

### Step-by-Step Example: arista-ssh-agent

#### 1. Agent Creates Socket (Server Side)

```c
// Simplified C code (what arista-ssh-agent does)

// Create socket
int sock = socket(AF_UNIX, SOCK_STREAM, 0);

// Bind to file path
struct sockaddr_un addr;
addr.sun_family = AF_UNIX;
strcpy(addr.sun_path, "/Users/ajay.kumar/.ssh/arista-ssh/agent.sock");
bind(sock, (struct sockaddr*)&addr, sizeof(addr));

// Listen for connections
listen(sock, 5);

// Accept connections
while (1) {
    int client = accept(sock, NULL, NULL);
    // Handle client requests...
}
```

**Result:** File `agent.sock` appears in filesystem

#### 2. SSH Client Connects (Client Side)

```c
// Simplified C code (what SSH client does)

// Create socket
int sock = socket(AF_UNIX, SOCK_STREAM, 0);

// Connect to agent socket
struct sockaddr_un addr;
addr.sun_family = AF_UNIX;
strcpy(addr.sun_path, "/Users/ajay.kumar/.ssh/arista-ssh/agent.sock");
connect(sock, (struct sockaddr*)&addr, sizeof(addr));

// Send request
write(sock, "REQUEST_CERTIFICATE", 19);

// Receive response
char cert[4096];
read(sock, cert, sizeof(cert));
```

#### 3. Communication Flow

```
SSH Client                      arista-ssh-agent
    │                                  │
    │  1. connect(agent.sock)          │
    │ ──────────────────────────────>  │
    │                                  │
    │  2. "I need SSH cert for host X" │
    │ ──────────────────────────────>  │
    │                                  │
    │  3. Check if cert is valid       │
    │                                  │ (checks OneLogin session)
    │                                  │
    │  4. "Here's your certificate"    │
    │ <──────────────────────────────  │
    │                                  │
    │  5. close()                      │
    │ ──────────────────────────────>  │
    │                                  │
```

---

## Real-World Examples of Unix Sockets

### 1. Docker
```bash
$ ls -la /var/run/docker.sock
srwxr-xr-x  docker.sock

# Docker CLI talks to Docker daemon via this socket
docker ps  →  connects to docker.sock  →  Docker daemon responds
```

### 2. SSH Agent (Standard)
```bash
$ echo $SSH_AUTH_SOCK
/private/tmp/com.apple.launchd.xyz/Listeners

$ ls -la $SSH_AUTH_SOCK
srwxr-xr-x  Listeners

# SSH client talks to ssh-agent via this socket
ssh github.com  →  connects to SSH_AUTH_SOCK  →  ssh-agent provides key
```

### 3. MySQL
```bash
$ ls -la /tmp/mysql.sock
srwxrwxrwx  mysql.sock

# MySQL client talks to MySQL server via this socket
mysql -u root  →  connects to mysql.sock  →  MySQL server
```

### 4. Arista SSH Agent
```bash
$ ls -la ~/.ssh/arista-ssh/
srwxr-xr-x  agent.sock   # SSH client ↔ agent
srwxr-xr-x  cli.sock     # arista-ssh CLI ↔ agent
```

---

## Why Use Sockets Instead of Files?

### Regular File Approach (Slow, Insecure)
```
SSH Client                      arista-ssh-agent
    │                                  │
    │  1. Write request to file        │
    │     /tmp/request.txt             │
    │ ──────────────────────────────>  │
    │                                  │
    │  2. Poll for response file       │
    │     (check every 100ms)          │
    │     /tmp/response.txt exists?    │
    │                                  │
    │  3. Read response file           │
    │ <──────────────────────────────  │
    │                                  │

Problems:
❌ Slow (disk I/O)
❌ Polling wastes CPU
❌ Race conditions
❌ Security (files visible to other users)
❌ Cleanup (leftover files)
```

### Unix Socket Approach (Fast, Secure)
```
SSH Client                      arista-ssh-agent
    │                                  │
    │  1. connect() - instant          │
    │ ──────────────────────────────>  │
    │                                  │
    │  2. write() - instant            │
    │ ──────────────────────────────>  │
    │                                  │
    │  3. read() - blocks until ready  │
    │ <──────────────────────────────  │
    │                                  │

Benefits:
✅ Fast (memory, no disk)
✅ Blocking I/O (no polling)
✅ Atomic operations
✅ Permissions (only owner can connect)
✅ Auto-cleanup (disappears when process dies)
```

---

## Inspecting Sockets

### Check Socket Type
```bash
$ file ~/.ssh/arista-ssh/agent.sock
/Users/ajay.kumar/.ssh/arista-ssh/agent.sock: socket
```

### Check Permissions
```bash
$ ls -la ~/.ssh/arista-ssh/agent.sock
srwxr-xr-x  1 ajay.kumar  staff  0 Feb  9 11:43 agent.sock
#│││││││││
#│││││││││
#│└┴┴┴┴┴┴┴─ Permissions (rwxr-xr-x)
#└───────── Type: s = socket
```

### Find Process Using Socket
```bash
$ lsof ~/.ssh/arista-ssh/agent.sock
COMMAND    PID        USER   FD   TYPE     DEVICE SIZE/OFF NODE NAME
arista-ss 1350 ajay.kumar    3u  unix 0x1234567        0t0      ~/.ssh/arista-ssh/agent.sock
```

### Test Socket Connection
```bash
# Try to connect (will fail without proper protocol)
$ nc -U ~/.ssh/arista-ssh/agent.sock
# (hangs waiting for data - press Ctrl+C)

# This proves the socket is listening!
```

---

## The Two Arista SSH Sockets

### agent.sock - SSH Authentication

**Purpose:** Provide SSH certificates to SSH client

**Protocol:** SSH Agent Protocol (RFC 4253)

**Communication:**
```
SSH Client                      agent.sock
    │                                │
    │  SSH_AGENTC_REQUEST_IDENTITIES │
    │ ─────────────────────────────> │
    │                                │
    │  SSH_AGENT_IDENTITIES_ANSWER   │
    │ <───────────────────────────── │
    │  (list of certificates)        │
    │                                │
    │  SSH_AGENTC_SIGN_REQUEST       │
    │ ─────────────────────────────> │
    │                                │
    │  SSH_AGENT_SIGN_RESPONSE       │
    │ <───────────────────────────── │
    │  (signed challenge)            │
```

### cli.sock - CLI Communication

**Purpose:** Control the agent from command line

**Protocol:** Custom (Arista-specific)

**Communication:**
```
arista-ssh CLI                  cli.sock
    │                                │
    │  "check-auth"                  │
    │ ─────────────────────────────> │
    │                                │
    │  {"status": "valid",           │
    │   "expires": "2026-02-10"}     │
    │ <───────────────────────────── │
    │                                │
    │  "login"                       │
    │ ─────────────────────────────> │
    │                                │
    │  "Opening browser..."          │
    │ <───────────────────────────── │
```

---

## Summary

**Unix domain sockets** are:
- ✅ Fast IPC mechanism (faster than files, pipes)
- ✅ Bidirectional communication
- ✅ Secure (filesystem permissions)
- ✅ Automatic cleanup (disappear when process exits)
- ✅ Used by: Docker, MySQL, SSH agent, and many more

**Your arista-ssh sockets:**
- `agent.sock` - SSH client gets certificates here
- `cli.sock` - `arista-ssh` CLI controls agent here

**They're not magic** - just efficient phone lines between programs! 📞

