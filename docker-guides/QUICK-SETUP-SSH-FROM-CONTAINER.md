# Quick Setup: SSH to ap-remote from Docker Container

**Goal:** Enable `ssh ap-remote` from inside your `dev-arm64` container

---

## Option 1: Quick Fix (ProxyJump - 2 minutes)

This uses your Mac as a jump host. Simplest approach.

### Step 1: Enable SSH on Mac (if not already enabled)
```bash
# On Mac
sudo systemsetup -setremotelogin on
```

### Step 2: Add SSH Config to Container
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
  StrictHostKeyChecking no
  UserKnownHostsFile /dev/null
EOF"
```

### Step 3: Test
```bash
docker exec -it dev-arm64 bash
root@dev-arm64:/# ssh ap-remote
# Should work! (goes through Mac as jump host)
```

**Pros:** ✅ Simple, ✅ Works immediately  
**Cons:** ⚠️ Two-hop (slower), ⚠️ Requires SSH on Mac

---

## Option 2: Proper Setup (Agent Forwarding - 10 minutes)

This forwards the arista-ssh-agent socket into the container. Best performance.

### Step 1: Stop and Remove Current Container
```bash
docker stop dev-arm64
docker rm dev-arm64
```

### Step 2: Recreate Container with Socket Mount
```bash
docker run -dit \
  --name dev-arm64 \
  --network host \
  --hostname dev-arm64 \
  --workdir /workspace \
  -v /Users/ajay.kumar/.ssh:/root/.ssh:ro \
  -v /Users/ajay.kumar/.ssh/arista-ssh:/ssh-agent:rw \
  -v /Volumes/linux-dev/garage:/garage \
  -v /Volumes/linux-dev/linux:/linux \
  -v /Users/ajay.kumar/.config:/root/.config:rw \
  -v /Users/ajay.kumar:/home/user \
  -e SSH_AUTH_SOCK=/ssh-agent/agent.sock \
  -e TERM=xterm-256color \
  -e LANG=en_US.UTF-8 \
  -e LC_ALL=en_US.UTF-8 \
  dev-arm64:latest
```

### Step 3: Copy SSH Configs
```bash
# Copy your SSH config
docker cp ~/.ssh/config dev-arm64:/root/.ssh/config

# Copy system SSH config for arista-ssh
docker exec dev-arm64 mkdir -p /etc/ssh/ssh_config.d
docker cp /etc/ssh/ssh_config.d/09-arista-ssh-agent.conf \
  dev-arm64:/etc/ssh/ssh_config.d/

# Copy arista-ssh CLI tool
docker cp /usr/local/bin/arista-ssh dev-arm64:/usr/local/bin/
```

### Step 4: Test
```bash
docker exec -it dev-arm64 bash

# Verify socket is accessible
root@dev-arm64:/# ls -la $SSH_AUTH_SOCK
srwxr-xr-x 1 root root 0 Feb  9 11:43 /ssh-agent/agent.sock

# Test SSH
root@dev-arm64:/# ssh ap-remote
# Should work! 🎉
```

**Pros:** ✅ Fast (direct), ✅ Proper setup, ✅ Uses arista-ssh-agent  
**Cons:** ⚠️ Requires container recreation

---

## Option 3: Fix Existing Container (No Restart - 5 minutes)

If you can't recreate the container, use socat to forward the socket.

### Step 1: Install socat on Mac
```bash
brew install socat
```

### Step 2: Start Socket Forwarder on Mac
```bash
# In a separate terminal, keep this running
socat TCP-LISTEN:9999,reuseaddr,fork \
  UNIX-CONNECT:/Users/ajay.kumar/.ssh/arista-ssh/agent.sock
```

### Step 3: Install socat in Container
```bash
docker exec dev-arm64 apt-get update
docker exec dev-arm64 apt-get install -y socat
```

### Step 4: Create Socket Forwarder in Container
```bash
# Create the socket directory
docker exec dev-arm64 mkdir -p /ssh-agent

# Start socat forwarder (background)
docker exec -d dev-arm64 socat \
  UNIX-LISTEN:/ssh-agent/agent.sock,fork \
  TCP:host.docker.internal:9999

# Set environment variable
docker exec dev-arm64 bash -c \
  "echo 'export SSH_AUTH_SOCK=/ssh-agent/agent.sock' >> /root/.bashrc"

# Copy SSH configs
docker cp ~/.ssh/config dev-arm64:/root/.ssh/config
docker exec dev-arm64 mkdir -p /etc/ssh/ssh_config.d
docker cp /etc/ssh/ssh_config.d/09-arista-ssh-agent.conf \
  dev-arm64:/etc/ssh/ssh_config.d/
```

### Step 5: Test
```bash
docker exec -it dev-arm64 bash
root@dev-arm64:/# ssh ap-remote
# Should work!
```

**Pros:** ✅ No container restart needed  
**Cons:** ⚠️ Requires socat running on Mac, ⚠️ More complex

---

## Verification Commands

### Check if Socket is Accessible
```bash
docker exec dev-arm64 bash -c 'test -S "$SSH_AUTH_SOCK" && echo "✅ Socket OK" || echo "❌ Socket FAIL"'
```

### Check SSH Config
```bash
docker exec dev-arm64 cat /root/.ssh/config | grep -A 5 ap-remote
```

### Check Environment Variable
```bash
docker exec dev-arm64 env | grep SSH_AUTH_SOCK
```

### Test SSH Connection
```bash
docker exec dev-arm64 ssh -v ap-remote 2>&1 | grep -i "identity\|agent"
```

---

## Troubleshooting

### "Auth session has expired"
```bash
# On Mac (not in container)
arista-ssh login
```

### "Permission denied (publickey)"
```bash
# Check if socket is accessible
docker exec dev-arm64 ls -la $SSH_AUTH_SOCK

# Check if arista-ssh config is present
docker exec dev-arm64 cat /etc/ssh/ssh_config.d/09-arista-ssh-agent.conf
```

### "Could not resolve hostname"
```bash
# Check DNS in container
docker exec dev-arm64 nslookup ajaykumar-ajaykrarista-2zfg4

# If fails, check VPN on Mac
ping ajaykumar-ajaykrarista-2zfg4
```

---

## My Recommendation

**For you:** Use **Option 2 (Agent Forwarding)** because:
1. ✅ You already recreate containers (I saw your container-recreation-commands.sh)
2. ✅ Best performance (direct socket access)
3. ✅ Proper setup (matches how it works on Mac)
4. ✅ No extra processes needed

**Just add these lines to your container creation script:**
```bash
-v /Users/ajay.kumar/.ssh/arista-ssh:/ssh-agent:rw \
-e SSH_AUTH_SOCK=/ssh-agent/agent.sock \
```

Then copy the configs once after container creation.

---

## One-Liner Test

After setup, verify everything works:
```bash
docker exec dev-arm64 bash -c 'echo "Testing SSH to ap-remote..." && ssh -o ConnectTimeout=5 ap-remote "hostname && echo Success!"'
```

If you see the hostname of your Kubernetes pod, you're all set! 🚀

