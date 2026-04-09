# SSH from Docker Container to Kubernetes Pod (ap-remote)

**Last Updated:** March 24, 2026

---

## Question

**Can I do `ssh ap-remote` from inside a Docker container?**

**Short Answer:** Yes, but it requires additional setup to make the arista-ssh-agent socket accessible inside the container.

---

## Current Situation

### What's Working on Your Mac
```bash
# On Mac - this works
$ ssh ap-remote
# ✅ Connects to Kubernetes pod
```

### What's NOT Working in Container
```bash
# Inside container - this fails
$ docker exec -it dev-arm64 bash
root@dev-arm64:/# ssh ap-remote
# ❌ Fails - no arista-ssh-agent socket
```

---

## Why It Doesn't Work (Yet)

### The Problem

```
┌─────────────────────────────────────────────────────────────────┐
│                         YOUR MAC                                 │
│                                                                  │
│  ┌──────────────────────────────────────────────────────┐      │
│  │ arista-ssh-agent                                      │      │
│  │ Socket: ~/.ssh/arista-ssh/agent.sock                 │      │
│  └──────────────────────────────────────────────────────┘      │
│                           │                                      │
│                           │ ✅ Mac SSH can access                │
│                           │                                      │
│  ┌────────────────────────────────────────────────────────┐    │
│  │ Colima VM                                               │    │
│  │                                                         │    │
│  │  ┌────────────────────────────────────────────────┐    │    │
│  │  │ Docker Container (dev-arm64)                   │    │    │
│  │  │                                                 │    │    │
│  │  │ Mount: /Users/ajay.kumar/.ssh:/root/.ssh      │    │    │
│  │  │                                                 │    │    │
│  │  │ Problem: Socket files don't work across        │    │    │
│  │  │          VM boundaries!                         │    │    │
│  │  │                                                 │    │    │
│  │  │ /root/.ssh/arista-ssh/agent.sock               │    │    │
│  │  │ ❌ Exists as file, but NOT functional socket   │    │    │
│  │  └────────────────────────────────────────────────┘    │    │
│  └────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────┘
```

**Key Issue:** Unix domain sockets are **kernel-level IPC mechanisms**. When you mount `~/.ssh` into the container:
- Regular files (keys, config) ✅ Work fine
- Socket files (agent.sock) ❌ Don't work - they're just dead files

---

## Solution: SSH Agent Forwarding

There are **three approaches** to make this work:

---

## ✅ Solution 1: SSH Agent Forwarding (Recommended)

Forward the SSH agent socket into the container using Docker's built-in support.

### Step 1: Update Container Run Command

```bash
docker run -dit \
  --name dev-arm64 \
  --network host \
  -v /Users/ajay.kumar/.ssh:/root/.ssh:ro \
  -v /Users/ajay.kumar/.ssh/arista-ssh:/root/.ssh/arista-ssh:rw \
  -e SSH_AUTH_SOCK=/root/.ssh/arista-ssh/agent.sock \
  -v /Volumes/linux-dev/garage:/garage \
  -v /Volumes/linux-dev/linux:/linux \
  dev-arm64:latest
```

**Key additions:**
- `-v /Users/ajay.kumar/.ssh/arista-ssh:/root/.ssh/arista-ssh:rw` - Mount socket directory
- `-e SSH_AUTH_SOCK=/root/.ssh/arista-ssh/agent.sock` - Set environment variable

### Step 2: Copy SSH Config into Container

```bash
# Copy your SSH config
docker exec dev-arm64 bash -c "cat > /root/.ssh/config" < ~/.ssh/config

# Or mount it directly (add to docker run):
# -v /Users/ajay.kumar/.ssh/config:/root/.ssh/config:ro
```

### Step 3: Copy System SSH Config

```bash
# Copy the arista-ssh-agent config
docker exec dev-arm64 bash -c "mkdir -p /etc/ssh/ssh_config.d"
docker cp /etc/ssh/ssh_config.d/09-arista-ssh-agent.conf \
  dev-arm64:/etc/ssh/ssh_config.d/
```

### Step 4: Install arista-ssh CLI (Optional)

```bash
# If you need arista-ssh commands inside container
docker cp /usr/local/bin/arista-ssh dev-arm64:/usr/local/bin/
docker cp /usr/local/libexec/arista-ssh-agent dev-arm64:/usr/local/libexec/
```

### Step 5: Test

```bash
docker exec -it dev-arm64 bash

# Inside container
root@dev-arm64:/# ssh ap-remote
# Should work! 🎉
```

---

## ⚠️ Solution 2: SSH ProxyJump (Simpler, but Two-Hop)

Use your Mac as a jump host.

### Step 1: Update Container's SSH Config

```bash
docker exec dev-arm64 bash -c "cat > /root/.ssh/config << 'EOF'
Host ap-remote
  HostName ajaykumar-ajaykrarista-2zfg4
  User ajay.kumar
  ProxyJump mac-host
  ForwardAgent yes

Host mac-host
  HostName host.docker.internal
  User ajay.kumar
  IdentityFile /root/.ssh/id_ed25519
  ForwardAgent yes
EOF"
```

### Step 2: Enable SSH on Your Mac

```bash
# On Mac
sudo systemsetup -setremotelogin on
```

### Step 3: Test

```bash
docker exec -it dev-arm64 bash

# Inside container - goes through Mac as jump host
root@dev-arm64:/# ssh ap-remote
# Mac → Kubernetes pod
```

**Flow:**
```
Container → Mac (via host.docker.internal) → ap-remote (Kubernetes pod)
```

---

## 🔧 Solution 3: socat Socket Forwarding (Advanced)

Forward the socket using `socat` (socket relay).

### On Mac (Terminal 1)

```bash
# Forward agent socket to TCP port
socat TCP-LISTEN:9999,reuseaddr,fork \
  UNIX-CONNECT:/Users/ajay.kumar/.ssh/arista-ssh/agent.sock
```

### In Container

```bash
# Install socat
docker exec dev-arm64 apt-get update && apt-get install -y socat

# Create socket forwarder
docker exec -d dev-arm64 bash -c "
  mkdir -p /root/.ssh/arista-ssh
  socat UNIX-LISTEN:/root/.ssh/arista-ssh/agent.sock,fork \
    TCP:host.docker.internal:9999
"

# Set environment variable
docker exec dev-arm64 bash -c "
  echo 'export SSH_AUTH_SOCK=/root/.ssh/arista-ssh/agent.sock' >> /root/.bashrc
"
```

### Test

```bash
docker exec -it dev-arm64 bash
root@dev-arm64:/# ssh ap-remote
```

---

## Comparison of Solutions

| Solution | Complexity | Performance | Reliability | Use Case |
|----------|-----------|-------------|-------------|----------|
| **Agent Forwarding** | Medium | Fast | High | Best for production |
| **ProxyJump** | Low | Slower (2 hops) | High | Quick setup |
| **socat** | High | Fast | Medium | Advanced users |

---

## Recommended Approach

### For Quick Testing: ProxyJump
```bash
# Simplest - just update SSH config in container
# Two-hop: Container → Mac → Kubernetes
```

### For Production Use: Agent Forwarding
```bash
# Mount socket directory properly
# Configure SSH to use the socket
# Best performance and security
```

---

## Complete Example: Agent Forwarding Setup

### 1. Recreate Container with Proper Mounts

```bash
# Stop existing container
docker stop dev-arm64
docker rm dev-arm64

# Create with socket forwarding
docker run -dit \
  --name dev-arm64 \
  --network host \
  --hostname dev-arm64 \
  -v /Users/ajay.kumar/.ssh:/root/.ssh:ro \
  -v /Users/ajay.kumar/.ssh/arista-ssh:/ssh-agent:rw \
  -e SSH_AUTH_SOCK=/ssh-agent/agent.sock \
  -v /Volumes/linux-dev/garage:/garage \
  -v /Volumes/linux-dev/linux:/linux \
  -v /Users/ajay.kumar/.config:/root/.config:rw \
  dev-arm64:latest
```

### 2. Configure SSH in Container

```bash
# Copy SSH config
docker cp ~/.ssh/config dev-arm64:/root/.ssh/config

# Copy system SSH config
docker exec dev-arm64 mkdir -p /etc/ssh/ssh_config.d
docker cp /etc/ssh/ssh_config.d/09-arista-ssh-agent.conf \
  dev-arm64:/etc/ssh/ssh_config.d/

# Copy arista-ssh CLI
docker cp /usr/local/bin/arista-ssh dev-arm64:/usr/local/bin/
```

### 3. Test

```bash
docker exec -it dev-arm64 bash

# Check socket
root@dev-arm64:/# ls -la $SSH_AUTH_SOCK
srwxr-xr-x 1 root root 0 Feb  9 11:43 /ssh-agent/agent.sock

# Test SSH
root@dev-arm64:/# ssh ap-remote
# Should work! 🎉
```

---

## Troubleshooting

### Socket Not Working
```bash
# Check if socket is accessible
docker exec dev-arm64 test -S /ssh-agent/agent.sock && echo "OK" || echo "FAIL"

# Check environment variable
docker exec dev-arm64 env | grep SSH_AUTH_SOCK
```

### Permission Denied
```bash
# Check socket permissions
docker exec dev-arm64 ls -la /ssh-agent/agent.sock

# Should be: srwxr-xr-x (socket with read/execute)
```

### arista-ssh-agent Not Running on Mac
```bash
# On Mac - check if agent is running
ps aux | grep arista-ssh-agent

# If not running, it should auto-start on next SSH attempt
```

---

## Summary

**Yes, you can SSH to `ap-remote` from inside a Docker container!**

**Recommended approach:**
1. Mount the arista-ssh socket directory into container
2. Set `SSH_AUTH_SOCK` environment variable
3. Copy SSH configs into container
4. Test with `ssh ap-remote`

**The socket forwarding allows the container to use your Mac's arista-ssh-agent for authentication.** 🚀

