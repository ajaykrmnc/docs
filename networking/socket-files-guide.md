# Comprehensive Guide to .sock Files (Unix Domain Sockets)

## Table of Contents
1. [What are .sock Files?](#what-are-sock-files)
2. [How Unix Domain Sockets Work](#how-unix-domain-sockets-work)
3. [Types of Unix Domain Sockets](#types-of-unix-domain-sockets)
4. [Your Specific Socket Files](#your-specific-socket-files)
5. [Common Use Cases](#common-use-cases)
6. [Technical Details](#technical-details)
7. [Working with Socket Files](#working-with-socket-files)
8. [Security Considerations](#security-considerations)
9. [Troubleshooting](#troubleshooting)
10. [Comparison with Other IPC Methods](#comparison-with-other-ipc-methods)

---

## What are .sock Files?

`.sock` files are **Unix Domain Sockets** (UDS) - special files that enable **Inter-Process Communication (IPC)** between processes running on the same machine. Despite appearing as files in the filesystem, they don't contain data like regular files. Instead, they act as communication endpoints.

### Key Characteristics:
- **Not regular files**: They don't store data on disk
- **Communication channels**: Bidirectional data exchange between processes
- **Filesystem presence**: Visible in directory listings but have 0 bytes
- **Special file type**: Identified by 's' in `ls -l` output (e.g., `srwxr-xr-x`)
- **Local only**: Only work for processes on the same machine

---

## How Unix Domain Sockets Work

### Basic Concept:
```
Process A (Server)          Socket File          Process B (Client)
     |                      agent.sock                  |
     |--- Creates socket -----> |                       |
     |--- Listens ------------> |                       |
     |                          | <---- Connects -------|
     |<======= Data Exchange =========================>|
```

### Workflow:
1. **Server Process**: Creates the socket file and listens for connections
2. **Client Process**: Connects to the socket file
3. **Communication**: Both processes exchange data through the socket
4. **Cleanup**: Socket file is typically deleted when the server stops

---

## Types of Unix Domain Sockets

### 1. **SOCK_STREAM** (Stream Sockets)
- **Protocol**: Connection-oriented, like TCP
- **Reliability**: Guaranteed delivery, ordered packets
- **Use case**: When data integrity is critical
- **Example**: SSH agent sockets, database connections

### 2. **SOCK_DGRAM** (Datagram Sockets)
- **Protocol**: Connectionless, like UDP
- **Reliability**: No delivery guarantee, may arrive out of order
- **Use case**: When speed matters more than reliability
- **Example**: Logging services, system notifications

### 3. **SOCK_SEQPACKET** (Sequential Packet Sockets)
- **Protocol**: Connection-oriented with message boundaries
- **Reliability**: Guaranteed delivery with preserved message boundaries
- **Use case**: When you need both reliability and message framing

---

## Your Specific Socket Files

### In `~/.ssh/arista-ssh/`:

#### 1. **agent.sock**
- **Purpose**: SSH authentication agent socket
- **Function**: Stores and manages SSH private keys in memory
- **Benefits**:
  - Single sign-on for multiple SSH connections
  - Keys remain encrypted and never touch disk
  - Avoids repeated passphrase entry
- **How it works**:
  ```
  ssh-agent → Creates agent.sock → SSH clients connect → Agent provides keys
  ```

#### 2. **cli.sock**
- **Purpose**: Command-line interface socket (Arista-specific)
- **Function**: Likely used for CLI commands to communicate with a background service
- **Typical use**: Network device management, configuration commands

### Checking Your Sockets:
```bash
# View socket details
ls -la ~/.ssh/arista-ssh/

# Check which process owns them
lsof ~/.ssh/arista-ssh/agent.sock
lsof ~/.ssh/arista-ssh/cli.sock

# See socket type and state
file ~/.ssh/arista-ssh/agent.sock
```

---

## Common Use Cases

### 1. **SSH Agent Forwarding**
```bash
# Start SSH agent
eval $(ssh-agent -s)
# Agent creates socket at $SSH_AUTH_SOCK

# Add keys
ssh-add ~/.ssh/id_rsa

# SSH clients use the socket to authenticate
ssh user@server
```

### 2. **Docker Daemon**
```bash
# Docker daemon socket
/var/run/docker.sock

# Docker CLI communicates via socket
docker ps  # Connects to docker.sock
```

### 3. **Database Connections**
```bash
# MySQL socket
/var/run/mysqld/mysqld.sock

# PostgreSQL socket
/var/run/postgresql/.s.PGSQL.5432

# Faster than TCP/IP for local connections
mysql -S /var/run/mysqld/mysqld.sock
```

### 4. **Web Servers**
```bash
# Nginx/PHP-FPM communication
/var/run/php-fpm.sock

# Gunicorn/uWSGI for Python apps
/tmp/gunicorn.sock
```

### 5. **System Services**
```bash
# systemd
/run/systemd/private

# D-Bus
/var/run/dbus/system_bus_socket

# X11 display server
/tmp/.X11-unix/X0
```

---

## Technical Details

### File Permissions
```bash
srwxr-xr-x  1 user  group  0 Mar 24 10:30 agent.sock
│││││││││
│││││││││
│└┴┴┴┴┴┴┴─ Permission bits (rwx for owner, r-x for group, r-x for others)
└────────── 's' indicates socket file
```

### Socket Address Families
- **AF_UNIX / AF_LOCAL**: Unix domain sockets (local machine only)
- **AF_INET**: IPv4 network sockets
- **AF_INET6**: IPv6 network sockets

### Performance Characteristics
- **Speed**: 2-3x faster than TCP/IP loopback (127.0.0.1)
- **Overhead**: No network stack processing
- **Latency**: Microseconds vs milliseconds for network sockets
- **Throughput**: Can exceed 10 GB/s on modern systems

### Kernel Behavior
- Socket files are **not** stored on disk
- They're entries in the filesystem namespace
- Data passes through kernel buffers
- No filesystem I/O operations involved

---

## Working with Socket Files

### Creating a Socket (Python Example)
```python
import socket
import os

# Remove old socket if exists
socket_path = '/tmp/my_app.sock'
try:
    os.unlink(socket_path)
except OSError:
    if os.path.exists(socket_path):
        raise

# Create socket
sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
sock.bind(socket_path)
sock.listen(1)

print(f"Listening on {socket_path}")

# Accept connections
while True:
    connection, client_address = sock.accept()
    try:
        data = connection.recv(1024)
        connection.sendall(b"Response: " + data)
    finally:
        connection.close()
```

### Connecting to a Socket (Python Example)
```python
import socket

socket_path = '/tmp/my_app.sock'

# Create client socket
client = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
client.connect(socket_path)

# Send data
client.sendall(b"Hello, server!")

# Receive response
response = client.recv(1024)
print(f"Received: {response.decode()}")

client.close()
```

### Using netcat/socat
```bash
# Send data to socket using socat
echo "Hello" | socat - UNIX-CONNECT:/tmp/my_app.sock

# Listen on a socket
socat UNIX-LISTEN:/tmp/test.sock,fork EXEC:/bin/cat

# Bidirectional communication
socat - UNIX-CONNECT:/var/run/docker.sock
```

### Inspecting Socket Connections
```bash
# List all Unix sockets
netstat -a -p --unix

# Or using ss (modern alternative)
ss -x

# Show processes using sockets
lsof -U

# Find specific socket
lsof | grep "\.sock"

# Check socket statistics
ss -x -a | grep agent.sock
```

---

## Security Considerations

### 1. **File Permissions**
```bash
# Restrict access to owner only
chmod 600 agent.sock  # rw-------

# Allow group access
chmod 660 agent.sock  # rw-rw----

# Public read (rarely needed)
chmod 644 agent.sock  # rw-r--r--
```

**Best Practice**: Use most restrictive permissions necessary

### 2. **Directory Permissions**
```bash
# Secure the parent directory
chmod 700 ~/.ssh/arista-ssh/
```
Even if socket has open permissions, directory restrictions apply.

### 3. **Socket Ownership**
```bash
# Check ownership
ls -l ~/.ssh/arista-ssh/agent.sock

# Change ownership (if needed)
chown user:group agent.sock
```

### 4. **Namespace Isolation**
- Sockets respect filesystem permissions
- Use separate directories for different security contexts
- Consider using abstract namespace sockets (Linux-specific)

### 5. **Common Vulnerabilities**
- **World-writable sockets**: Anyone can connect
- **Predictable paths**: `/tmp` race conditions
- **Stale sockets**: Old socket files can be hijacked
- **Privilege escalation**: Connecting to privileged sockets

### 6. **Security Best Practices**
```bash
# Use secure temporary directories
mktemp -d  # Creates random directory

# Clean up on exit
trap "rm -f /tmp/my_app.sock" EXIT

# Verify socket ownership before connecting
stat -c "%U %G" /path/to/socket.sock

# Use abstract sockets (Linux) - no filesystem presence
# Prefix with @ in socket path
```

---

## Troubleshooting

### Problem 1: "Address already in use"
```bash
# Socket file exists from previous run
ls -l /tmp/my_app.sock

# Solution: Remove stale socket
rm /tmp/my_app.sock

# Or in code: unlink before binding
```

### Problem 2: "Permission denied"
```bash
# Check permissions
ls -l /path/to/socket.sock

# Check directory permissions
ls -ld /path/to/

# Solution: Fix permissions
chmod 666 socket.sock  # Or appropriate permissions
```

### Problem 3: "No such file or directory"
```bash
# Server process not running
ps aux | grep server-name

# Solution: Start the server process
./start-server.sh
```

### Problem 4: "Connection refused"
```bash
# Socket exists but nothing listening
lsof /path/to/socket.sock

# Solution: Restart the listening process
```

### Problem 5: Stale Socket Files
```bash
# Socket file exists but process is dead
lsof /path/to/socket.sock  # Returns nothing

# Solution: Safe cleanup
if ! lsof /path/to/socket.sock > /dev/null 2>&1; then
    rm /path/to/socket.sock
fi
```

### Problem 6: Socket Path Too Long
```bash
# Unix socket paths limited to ~100 characters
# Error: "Socket path too long"

# Solution: Use shorter paths or symlinks
ln -s /very/long/path/to/socket.sock /tmp/short.sock
```

### Debugging Commands
```bash
# Trace socket operations
strace -e socket,connect,bind,listen program

# Monitor socket activity
watch -n 1 'lsof -U | grep my_app'

# Test socket connectivity
timeout 5 socat - UNIX-CONNECT:/path/to/socket.sock

# Check socket buffer sizes
cat /proc/sys/net/core/rmem_default  # Receive buffer
cat /proc/sys/net/core/wmem_default  # Send buffer
```

---

## Comparison with Other IPC Methods

### Unix Domain Sockets vs TCP/IP Sockets

| Feature | Unix Domain Sockets | TCP/IP Sockets |
|---------|-------------------|----------------|
| **Scope** | Same machine only | Network-capable |
| **Speed** | Very fast (2-3x) | Slower (network stack) |
| **Security** | Filesystem permissions | Firewall, encryption needed |
| **Overhead** | Minimal | Protocol overhead |
| **Use case** | Local IPC | Network communication |
| **Address** | Filesystem path | IP:Port |

### Unix Domain Sockets vs Named Pipes (FIFOs)

| Feature | Unix Domain Sockets | Named Pipes |
|---------|-------------------|-------------|
| **Bidirectional** | Yes | No (unidirectional) |
| **Connection-oriented** | Yes (SOCK_STREAM) | No |
| **Multiple clients** | Yes | Limited |
| **Message boundaries** | Optional (SOCK_DGRAM) | No |
| **Use case** | Complex IPC | Simple data streaming |

### Unix Domain Sockets vs Shared Memory

| Feature | Unix Domain Sockets | Shared Memory |
|---------|-------------------|---------------|
| **Speed** | Fast | Fastest |
| **Synchronization** | Built-in | Manual (semaphores) |
| **Complexity** | Simple API | Complex |
| **Data copying** | Yes (kernel) | No (direct access) |
| **Use case** | General IPC | High-performance data sharing |

### Unix Domain Sockets vs Message Queues

| Feature | Unix Domain Sockets | Message Queues |
|---------|-------------------|----------------|
| **Message boundaries** | Optional | Always preserved |
| **Priority** | No | Yes |
| **Persistence** | No | Can persist |
| **Blocking** | Yes | Yes |
| **Use case** | Stream/datagram IPC | Message-based IPC |

---

## Advanced Topics

### 1. **Abstract Namespace Sockets (Linux)**
```python
# No filesystem presence - starts with null byte
socket_path = '\0my_abstract_socket'

sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
sock.bind(socket_path)
```

**Benefits**:
- No filesystem cleanup needed
- No permission issues
- Automatic cleanup on process exit
- Namespace isolation

### 2. **Socket Credentials (SCM_CREDENTIALS)**
```python
import socket
import struct

# Receive peer credentials
sock.setsockopt(socket.SOL_SOCKET, socket.SO_PASSCRED, 1)

# Get peer PID, UID, GID
creds = sock.getsockopt(socket.SOL_SOCKET, socket.SO_PEERCRED,
                        struct.calcsize('3i'))
pid, uid, gid = struct.unpack('3i', creds)
```

**Use case**: Authentication without passwords

### 3. **File Descriptor Passing**
```python
import socket
import array

# Send file descriptor over socket
def send_fd(sock, fd):
    sock.sendmsg([b'x'],
                 [(socket.SOL_SOCKET, socket.SCM_RIGHTS,
                   array.array("i", [fd]))])

# Receive file descriptor
def recv_fd(sock):
    msg, ancdata, flags, addr = sock.recvmsg(1,
                                             socket.CMSG_LEN(4))
    cmsg_level, cmsg_type, cmsg_data = ancdata[0]
    return array.array("i", cmsg_data)[0]
```

**Use case**: Privilege separation, systemd socket activation

### 4. **Socket Activation (systemd)**
```ini
# /etc/systemd/system/myapp.socket
[Unit]
Description=My Application Socket

[Socket]
ListenStream=/run/myapp.sock
SocketMode=0660
SocketUser=myapp
SocketGroup=myapp

[Install]
WantedBy=sockets.target
```

**Benefits**:
- On-demand service activation
- Zero-downtime restarts
- Simplified service management

### 5. **Socket Buffers and Performance Tuning**
```python
# Increase buffer sizes
sock.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, 1024*1024)
sock.setsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF, 1024*1024)

# Set socket timeout
sock.settimeout(5.0)

# Enable keepalive
sock.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)

# Non-blocking mode
sock.setblocking(False)
```

---

## Real-World Examples

### Example 1: Docker Communication
```bash
# Docker daemon listens on socket
ls -l /var/run/docker.sock
# srw-rw---- 1 root docker 0 Mar 24 10:00 /var/run/docker.sock

# Docker CLI connects to socket
docker ps
# Internally: connects to /var/run/docker.sock
# Sends HTTP request over Unix socket
# Receives JSON response

# Manual HTTP request over socket
echo -e "GET /containers/json HTTP/1.1\r\nHost: localhost\r\n\r\n" | \
  socat - UNIX-CONNECT:/var/run/docker.sock
```

### Example 2: SSH Agent
```bash
# Start SSH agent
eval $(ssh-agent -s)
# Output: SSH_AUTH_SOCK=/tmp/ssh-XXX/agent.1234; export SSH_AUTH_SOCK;

# Add key
ssh-add ~/.ssh/id_rsa

# SSH client uses agent
ssh user@server
# Internally:
# 1. SSH client connects to $SSH_AUTH_SOCK
# 2. Requests signature from agent
# 3. Agent signs challenge with private key
# 4. SSH client sends signature to server
```

### Example 3: Nginx + PHP-FPM
```nginx
# nginx.conf
location ~ \.php$ {
    fastcgi_pass unix:/var/run/php-fpm.sock;
    fastcgi_index index.php;
    include fastcgi_params;
}
```

```ini
; php-fpm.conf
[www]
listen = /var/run/php-fpm.sock
listen.owner = www-data
listen.group = www-data
listen.mode = 0660
```

**Flow**:
1. Nginx receives HTTP request for PHP file
2. Nginx connects to `/var/run/php-fpm.sock`
3. Sends FastCGI request over socket
4. PHP-FPM processes PHP script
5. Returns response over socket
6. Nginx sends HTTP response to client

---

## Monitoring and Management

### System-wide Socket Monitoring
```bash
# All Unix sockets with details
ss -xlp

# Count active Unix sockets
ss -x | wc -l

# Watch socket creation/deletion
watch -n 1 'ls -l /var/run/*.sock'

# Socket statistics
cat /proc/net/unix
```

### Application-specific Monitoring
```bash
# Find sockets for specific process
lsof -p <PID> | grep unix

# Find process using specific socket
fuser /path/to/socket.sock

# Continuous monitoring
inotifywait -m /path/to/socket/directory/
```

### Logging Socket Activity
```bash
# Audit socket access (Linux)
auditctl -w /var/run/docker.sock -p rwa -k docker_socket

# View audit logs
ausearch -k docker_socket

# System logs
journalctl -f | grep socket
```

---

## Best Practices Summary

### ✅ DO:
- Use most restrictive permissions possible
- Clean up socket files on exit
- Check for stale sockets before binding
- Use secure directories (not world-writable `/tmp`)
- Validate peer credentials when security matters
- Handle SIGPIPE signal (broken pipe)
- Set appropriate timeouts
- Use abstract sockets on Linux when appropriate
- Document socket paths and protocols
- Monitor socket health in production

### ❌ DON'T:
- Leave world-writable sockets
- Use predictable paths in `/tmp`
- Forget to unlink socket files
- Ignore permission errors
- Assume socket exists without checking
- Mix up socket types (STREAM vs DGRAM)
- Exceed path length limits (~100 chars)
- Share sockets across security boundaries
- Hardcode socket paths (use configuration)
- Ignore error handling

---

## Quick Reference Commands

```bash
# Create socket directory
mkdir -p ~/.ssh/arista-ssh && chmod 700 ~/.ssh/arista-ssh

# List all sockets
find / -type s 2>/dev/null

# Check socket type
file /path/to/socket.sock

# Test socket connectivity
timeout 2 bash -c "</dev/tcp/localhost/port" 2>/dev/null  # TCP
echo "test" | socat - UNIX-CONNECT:/path/to/socket.sock   # Unix socket

# Remove all sockets in directory
find /path/to/dir -type s -delete

# Monitor socket I/O
iotop -o  # If socket causes disk I/O (shouldn't normally)

# Check socket limits
ulimit -n  # Max open file descriptors (includes sockets)
cat /proc/sys/fs/file-max  # System-wide limit
```

---

## Conclusion

Unix domain sockets (`.sock` files) are powerful IPC mechanisms that provide:
- **High performance** for local communication
- **Security** through filesystem permissions
- **Simplicity** with familiar socket API
- **Flexibility** for various communication patterns

Your `agent.sock` and `cli.sock` files in `~/.ssh/arista-ssh/` are examples of this technology in action, enabling secure and efficient communication between SSH/Arista components on your system.

Understanding socket files helps you:
- Debug connection issues
- Secure your system properly
- Optimize application performance
- Design better IPC architectures

---

## Additional Resources

- **Man pages**: `man 7 unix`, `man 2 socket`, `man 2 bind`
- **Books**: "Unix Network Programming" by W. Richard Stevens
- **RFCs**: Not applicable (Unix-specific, not standardized)
- **Tools**: `socat`, `netcat`, `ss`, `lsof`, `strace`
- **Linux kernel docs**: Documentation/networking/af_unix.txt

---

*Document created: 2026-03-24*
*For questions about your specific socket files, check the process that created them using `lsof` or `fuser`.*

