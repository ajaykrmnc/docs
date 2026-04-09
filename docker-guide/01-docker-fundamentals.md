# Docker Fundamentals: Complete Guide

## Table of Contents

1. [Introduction to Containers](#introduction-to-containers)
2. [Docker Architecture](#docker-architecture)
3. [Core Concepts](#core-concepts)
4. [Container vs Virtual Machines](#container-vs-virtual-machines)
5. [Docker Engine Components](#docker-engine-components)
6. [Container Lifecycle](#container-lifecycle)
7. [Namespaces and Cgroups](#namespaces-and-cgroups)
8. [Union File Systems](#union-file-systems)

---

## 1. Introduction to Containers

### 1.1 What are Containers?

Containers are lightweight, standalone, executable packages that include everything needed to run a piece of software:
- Application code
- Runtime environment
- System tools
- System libraries
- Settings and dependencies

**Key Characteristics:**
- **Isolated**: Each container runs in its own isolated environment
- **Portable**: Run consistently across different environments
- **Lightweight**: Share the host OS kernel, no hypervisor needed
- **Fast**: Start in seconds, not minutes
- **Efficient**: Use fewer resources than VMs

### 1.2 Why Use Containers?

**Benefits:**

1. **Consistency Across Environments**
   - "Works on my machine" problem solved
   - Same container runs identically everywhere
   - Development, testing, production parity

2. **Resource Efficiency**
   - Minimal overhead compared to VMs
   - Higher density on same hardware
   - Better resource utilization

3. **Rapid Deployment**
   - Fast startup times
   - Quick scaling up/down
   - Efficient CI/CD pipelines

4. **Microservices Architecture**
   - Each service in its own container
   - Independent scaling
   - Technology diversity

5. **DevOps Enablement**
   - Infrastructure as code
   - Version control for environments
   - Automated deployments

### 1.3 Container History

**Evolution:**

```
2000: FreeBSD Jails
  ↓
2001: Linux VServer
  ↓
2004: Solaris Containers
  ↓
2006: Process Containers (Google) → cgroups
  ↓
2008: LXC (Linux Containers)
  ↓
2013: Docker (built on LXC initially)
  ↓
2014: Kubernetes
  ↓
2015: Docker creates libcontainer (replaces LXC)
  ↓
2015: OCI (Open Container Initiative) formed
  ↓
2016+: Container ecosystem explosion
```

---

## 2. Docker Architecture

### 2.1 High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     Docker Client                           │
│                   (docker CLI / API)                        │
└─────────────────────────────────────────────────────────────┘
                          ↓ REST API
┌─────────────────────────────────────────────────────────────┐
│                    Docker Daemon (dockerd)                  │
│  ┌──────────────────────────────────────────────────────┐   │
│  │              Container Management                    │   │
│  │  - Create, start, stop, delete containers           │   │
│  │  - Image management                                  │   │
│  │  - Network management                                │   │
│  │  - Volume management                                 │   │
│  └──────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│                      containerd                             │
│  - Container lifecycle management                          │
│  - Image transfer and storage                              │
│  - Container execution supervision                         │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│                        runc                                 │
│  - Low-level container runtime                             │
│  - Creates and runs containers                             │
│  - OCI compliant                                            │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│                   Linux Kernel                              │
│  - Namespaces (isolation)                                   │
│  - Cgroups (resource limits)                                │
│  - Union File Systems                                       │
│  - Security (AppArmor, SELinux, Seccomp)                   │
└─────────────────────────────────────────────────────────────┘
```

### 2.2 Component Breakdown

#### Docker Client
- Command-line interface (CLI)
- Sends commands to Docker daemon
- Can connect to remote daemons
- Uses REST API over Unix socket or TCP

#### Docker Daemon (dockerd)
- Background service
- Manages Docker objects (images, containers, networks, volumes)
- Listens for API requests
- Communicates with other daemons

#### containerd
- Industry-standard container runtime
- Manages container lifecycle
- Image management
- Storage and network attachments

#### runc
- Low-level container runtime
- OCI (Open Container Initiative) compliant
- Creates and runs containers
- Spawns and runs containers according to OCI specification

---

## 3. Core Concepts

### 3.1 Images

**Definition**: A Docker image is a read-only template with instructions for creating a container.

**Characteristics:**
- Immutable (cannot be changed once created)
- Composed of layers
- Stored in registries (Docker Hub, private registries)
- Versioned using tags

**Image Layers:**

```
┌─────────────────────────────────────┐
│  Application Layer (your app)      │  ← Writable layer (container)
├─────────────────────────────────────┤
│  Dependencies Layer                 │  ← Read-only
├─────────────────────────────────────┤
│  Runtime Layer (Node.js, Python)    │  ← Read-only
├─────────────────────────────────────┤
│  OS Layer (Ubuntu, Alpine)          │  ← Read-only
└─────────────────────────────────────┘
```

**Example:**
```bash
# Pull an image
docker pull ubuntu:22.04

# List images
docker images

# Inspect image
docker inspect ubuntu:22.04

# Remove image
docker rmi ubuntu:22.04
```

### 3.2 Containers

**Definition**: A container is a runnable instance of an image.

**Characteristics:**
- Isolated process(es)
- Has its own filesystem (from image + writable layer)
- Own network interface
- Isolated process tree
- Resource constraints applied

**Container States:**

```
Created → Running → Paused → Stopped → Removed
   ↓         ↓         ↓         ↓
   └─────────┴─────────┴─────────┘
          (can restart)
```

**Example:**
```bash
# Create and start container
docker run -d --name myapp nginx

# List running containers
docker ps

# List all containers (including stopped)
docker ps -a

# Stop container
docker stop myapp

# Start stopped container
docker start myapp

# Remove container
docker rm myapp
```

### 3.3 Registries

**Definition**: A registry is a storage and distribution system for Docker images.

**Types:**

1. **Public Registries**
   - Docker Hub (default)
   - GitHub Container Registry
   - Google Container Registry
   - Amazon ECR Public

2. **Private Registries**
   - Self-hosted Docker Registry
   - Harbor
   - JFrog Artifactory
   - Cloud provider registries (ECR, GCR, ACR)

**Registry Operations:**

```bash
# Login to registry
docker login

# Tag image for registry
docker tag myapp:latest username/myapp:v1.0

# Push to registry
docker push username/myapp:v1.0

# Pull from registry
docker pull username/myapp:v1.0

# Search Docker Hub
docker search nginx
```

### 3.4 Volumes

**Definition**: Volumes are the preferred mechanism for persisting data generated by and used by Docker containers.

**Types:**

1. **Named Volumes**: Managed by Docker
2. **Bind Mounts**: Mount host directory into container
3. **tmpfs Mounts**: Stored in host memory only

**Example:**
```bash
# Create volume
docker volume create mydata

# Run container with volume
docker run -d -v mydata:/data nginx

# List volumes
docker volume ls

# Inspect volume
docker volume inspect mydata

# Remove volume
docker volume rm mydata
```

### 3.5 Networks

**Definition**: Docker networks enable containers to communicate with each other and the outside world.

**Network Drivers:**

1. **bridge**: Default network driver
2. **host**: Remove network isolation
3. **overlay**: Multi-host networking
4. **macvlan**: Assign MAC address to container
5. **none**: Disable networking

**Example:**
```bash
# Create network
docker network create mynetwork

# Run container on network
docker run -d --network mynetwork --name web nginx

# Connect running container to network
docker network connect mynetwork db

# List networks
docker network ls

# Inspect network
docker network inspect mynetwork

# Remove network
docker network rm mynetwork
```

---

## 4. Container vs Virtual Machines

### 4.1 Architecture Comparison

**Virtual Machines:**
```
┌──────────┬──────────┬──────────┐
│  App A   │  App B   │  App C   │
├──────────┼──────────┼──────────┤
│  Bins/   │  Bins/   │  Bins/   │
│  Libs    │  Libs    │  Libs    │
├──────────┼──────────┼──────────┤
│ Guest OS │ Guest OS │ Guest OS │
│ (Linux)  │ (Windows)│ (Linux)  │
└──────────┴──────────┴──────────┘
         Hypervisor (VMware, VirtualBox)
─────────────────────────────────────
         Host OS (Windows, Linux, macOS)
─────────────────────────────────────
         Physical Hardware
```

**Containers:**
```
┌──────────┬──────────┬──────────┐
│  App A   │  App B   │  App C   │
├──────────┼──────────┼──────────┤
│  Bins/   │  Bins/   │  Bins/   │
│  Libs    │  Libs    │  Libs    │
└──────────┴──────────┴──────────┘
    Docker Engine (Container Runtime)
─────────────────────────────────────
         Host OS (Linux)
─────────────────────────────────────
         Physical Hardware
```

### 4.2 Comparison Table

| Feature | Containers | Virtual Machines |
|---------|-----------|------------------|
| **Startup Time** | Seconds | Minutes |
| **Size** | MBs | GBs |
| **Performance** | Near-native | Overhead from hypervisor |
| **Isolation** | Process-level | Hardware-level |
| **OS** | Share host kernel | Full OS per VM |
| **Resource Usage** | Lightweight | Heavy |
| **Portability** | Highly portable | Less portable |
| **Security** | Process isolation | Strong isolation |
| **Use Case** | Microservices, apps | Full OS, legacy apps |

### 4.3 When to Use What?

**Use Containers When:**
- Running microservices
- Need rapid scaling
- CI/CD pipelines
- Development environments
- Cloud-native applications
- Resource efficiency is important

**Use VMs When:**
- Need complete OS isolation
- Running different OS kernels
- Legacy applications
- Strong security requirements
- Need full hardware emulation
- Running untrusted code

---

## 5. Docker Engine Components

### 5.1 Detailed Component Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Docker CLI                               │
│  Commands: run, build, pull, push, exec, logs, etc.        │
└─────────────────────────────────────────────────────────────┘
                          ↓ REST API (HTTP/Unix Socket)
┌─────────────────────────────────────────────────────────────┐
│                   Docker Daemon (dockerd)                   │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │              API Server                             │   │
│  │  - Handles REST API requests                        │   │
│  │  - Authentication and authorization                 │   │
│  └─────────────────────────────────────────────────────┘   │
│                          ↓                                  │
│  ┌─────────────────────────────────────────────────────┐   │
│  │           Image Management                          │   │
│  │  - Build images                                     │   │
│  │  - Pull/push from registries                        │   │
│  │  - Image storage and caching                        │   │
│  └─────────────────────────────────────────────────────┘   │
│                          ↓                                  │
│  ┌─────────────────────────────────────────────────────┐   │
│  │         Container Management                        │   │
│  │  - Create containers                                │   │
│  │  - Start/stop/restart                               │   │
│  │  - Monitor container state                          │   │
│  └─────────────────────────────────────────────────────┘   │
│                          ↓                                  │
│  ┌─────────────────────────────────────────────────────┐   │
│  │          Network Management                         │   │
│  │  - Create networks                                  │   │
│  │  - Connect containers                               │   │
│  │  - DNS resolution                                   │   │
│  └─────────────────────────────────────────────────────┘   │
│                          ↓                                  │
│  ┌─────────────────────────────────────────────────────┐   │
│  │          Volume Management                          │   │
│  │  - Create volumes                                   │   │
│  │  - Mount volumes to containers                      │   │
│  │  - Volume drivers                                   │   │
│  └─────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
                          ↓ gRPC
┌─────────────────────────────────────────────────────────────┐
│                      containerd                             │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │         Container Lifecycle                         │   │
│  │  - Start/stop containers                            │   │
│  │  - Supervise running containers                     │   │
│  └─────────────────────────────────────────────────────┘   │
│                          ↓                                  │
│  ┌─────────────────────────────────────────────────────┐   │
│  │         Image Management                            │   │
│  │  - Pull images                                      │   │
│  │  - Unpack images                                    │   │
│  │  - Content addressable storage                      │   │
│  └─────────────────────────────────────────────────────┘   │
│                          ↓                                  │
│  ┌─────────────────────────────────────────────────────┐   │
│  │         Snapshot Management                         │   │
│  │  - Manage filesystem snapshots                      │   │
│  │  - Layer management                                 │   │
│  └─────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│                        runc                                 │
│  - Creates container processes                             │
│  - Sets up namespaces                                       │
│  - Configures cgroups                                       │
│  - Applies security profiles                                │
│  - Executes container init process                          │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│                   Linux Kernel                              │
└─────────────────────────────────────────────────────────────┘
```

### 5.2 Communication Flow

**Example: Running a Container**

```
1. User executes: docker run nginx
   ↓
2. Docker CLI sends REST API request to Docker daemon
   ↓
3. Docker daemon checks if nginx image exists locally
   ↓
4. If not, daemon pulls image from Docker Hub
   ↓
5. Daemon sends request to containerd to create container
   ↓
6. containerd prepares container bundle (rootfs, config)
   ↓
7. containerd calls runc to create container
   ↓
8. runc sets up namespaces, cgroups, and starts container process
   ↓
9. Container is running, containerd monitors it
   ↓
10. Daemon reports success to CLI
```

### 5.3 Docker Daemon Configuration

**Configuration File**: `/etc/docker/daemon.json`

```json
{
  "data-root": "/var/lib/docker",
  "storage-driver": "overlay2",
  "log-driver": "json-file",
  "log-opts": {
    "max-size": "10m",
    "max-file": "3"
  },
  "default-address-pools": [
    {
      "base": "172.17.0.0/16",
      "size": 24
    }
  ],
  "dns": ["8.8.8.8", "8.8.4.4"],
  "insecure-registries": [],
  "registry-mirrors": [],
  "live-restore": true,
  "userland-proxy": false,
  "experimental": false,
  "metrics-addr": "127.0.0.1:9323",
  "max-concurrent-downloads": 3,
  "max-concurrent-uploads": 5
}
```

**Key Configuration Options:**

- **data-root**: Where Docker stores images and containers
- **storage-driver**: Filesystem driver (overlay2, aufs, devicemapper)
- **log-driver**: Logging mechanism
- **live-restore**: Keep containers running during daemon downtime
- **userland-proxy**: Use userland proxy for port forwarding
- **insecure-registries**: Registries without TLS
- **registry-mirrors**: Mirror registries for faster pulls

---

## 6. Container Lifecycle

### 6.1 Lifecycle States

```
┌──────────┐
│  Image   │
└──────────┘
     │
     │ docker create / docker run
     ↓
┌──────────┐
│ Created  │ ← Container exists but not started
└──────────┘
     │
     │ docker start
     ↓
┌──────────┐
│ Running  │ ← Container process is executing
└──────────┘
     │
     ├─→ docker pause → ┌────────┐
     │                  │ Paused │ ← Process frozen
     │                  └────────┘
     │                       │
     │                       │ docker unpause
     │                       ↓
     │ ←─────────────────────┘
     │
     │ docker stop / docker kill
     ↓
┌──────────┐
│ Stopped  │ ← Container stopped, can be restarted
└──────────┘
     │
     │ docker rm
     ↓
┌──────────┐
│ Removed  │ ← Container deleted
└──────────┘
```

### 6.2 Lifecycle Commands

**Creating Containers:**

```bash
# Create container without starting
docker create --name myapp nginx

# Create and start container
docker run --name myapp nginx

# Run in detached mode (background)
docker run -d --name myapp nginx

# Run with interactive terminal
docker run -it ubuntu /bin/bash

# Run with automatic removal after exit
docker run --rm nginx

# Run with restart policy
docker run --restart=always nginx
```

**Managing Running Containers:**

```bash
# Start stopped container
docker start myapp

# Stop running container (SIGTERM, then SIGKILL after grace period)
docker stop myapp

# Stop with custom timeout
docker stop -t 30 myapp

# Kill container immediately (SIGKILL)
docker kill myapp

# Restart container
docker restart myapp

# Pause container (freeze process)
docker pause myapp

# Unpause container
docker unpause myapp
```

**Inspecting Containers:**

```bash
# List running containers
docker ps

# List all containers
docker ps -a

# Show container details
docker inspect myapp

# Show container logs
docker logs myapp

# Follow logs in real-time
docker logs -f myapp

# Show last 100 lines
docker logs --tail 100 myapp

# Show resource usage statistics
docker stats myapp

# Show running processes in container
docker top myapp
```

**Interacting with Containers:**

```bash
# Execute command in running container
docker exec myapp ls /app

# Get interactive shell
docker exec -it myapp /bin/bash

# Attach to container's main process
docker attach myapp

# Copy files from container to host
docker cp myapp:/app/file.txt ./file.txt

# Copy files from host to container
docker cp ./file.txt myapp:/app/file.txt
```

**Removing Containers:**

```bash
# Remove stopped container
docker rm myapp

# Force remove running container
docker rm -f myapp

# Remove all stopped containers
docker container prune

# Remove container and its volumes
docker rm -v myapp
```

### 6.3 Container Exit Codes

Understanding exit codes helps debug container issues:

| Exit Code | Meaning |
|-----------|---------|
| 0 | Success - container exited normally |
| 1 | Application error - generic error |
| 2 | Misuse of shell command |
| 125 | Docker daemon error |
| 126 | Command cannot execute |
| 127 | Command not found |
| 128 | Invalid exit argument |
| 130 | Container terminated by Ctrl+C (SIGINT) |
| 137 | Container killed (SIGKILL) - often OOM |
| 139 | Segmentation fault |
| 143 | Container stopped gracefully (SIGTERM) |
| 255 | Exit code out of range |

**Checking Exit Code:**

```bash
# Run container and check exit code
docker run myapp
echo $?

# Inspect exit code of stopped container
docker inspect myapp --format='{{.State.ExitCode}}'
```

---

## 7. Namespaces and Cgroups

### 7.1 Linux Namespaces

Namespaces provide isolation for containers. Each container gets its own namespace for various resources.

**Types of Namespaces:**

1. **PID Namespace** (Process ID)
   - Isolates process IDs
   - Container sees its own process tree
   - PID 1 inside container is different from host

```bash
# Inside container
ps aux
# Shows only container processes

# On host
ps aux | grep container_process
# Shows actual PID on host
```

2. **Network Namespace** (NET)
   - Isolates network interfaces, routing tables, firewall rules
   - Each container has its own network stack
   - Virtual ethernet pairs connect container to host

```bash
# List network namespaces
ip netns list

# Execute command in namespace
ip netns exec <namespace> ip addr
```

3. **Mount Namespace** (MNT)
   - Isolates filesystem mount points
   - Container has its own root filesystem
   - Cannot see host mounts (unless explicitly shared)

4. **UTS Namespace** (Unix Timesharing System)
   - Isolates hostname and domain name
   - Each container can have its own hostname

```bash
# Set hostname in container
docker run --hostname mycontainer ubuntu hostname
```

5. **IPC Namespace** (Inter-Process Communication)
   - Isolates IPC resources (message queues, semaphores, shared memory)
   - Prevents containers from interfering with each other's IPC

6. **User Namespace** (USER)
   - Isolates user and group IDs
   - Root in container != root on host
   - Enhanced security through user remapping

```bash
# Run container with user namespace
docker run --userns-remap=default ubuntu
```

7. **Cgroup Namespace**
   - Isolates cgroup view
   - Container sees its own cgroup hierarchy

**Namespace Example:**

```bash
# Create container with specific namespaces
docker run -d \
  --name isolated \
  --pid=container:other_container \
  --network=container:other_container \
  nginx

# Share host network namespace
docker run --network=host nginx

# Share host PID namespace
docker run --pid=host ubuntu ps aux
```

### 7.2 Control Groups (cgroups)

Cgroups limit and account for resource usage of containers.

**Resource Types:**

1. **CPU**
   - CPU shares (relative weight)
   - CPU quota (hard limit)
   - CPU pinning (specific cores)

```bash
# Limit to 50% of one CPU
docker run --cpus=0.5 nginx

# Set CPU shares (relative priority)
docker run --cpu-shares=512 nginx

# Pin to specific CPUs
docker run --cpuset-cpus="0,1" nginx
```

2. **Memory**
   - Memory limit
   - Memory reservation (soft limit)
   - Swap limit
   - OOM killer behavior

```bash
# Limit memory to 512MB
docker run --memory=512m nginx

# Set memory reservation
docker run --memory=1g --memory-reservation=512m nginx

# Disable swap
docker run --memory=512m --memory-swap=512m nginx

# Disable OOM killer
docker run --oom-kill-disable nginx
```

3. **Block I/O**
   - Read/write bandwidth limits
   - IOPS limits
   - Device weights

```bash
# Limit read rate to 10 MB/s
docker run --device-read-bps=/dev/sda:10mb nginx

# Limit write rate
docker run --device-write-bps=/dev/sda:5mb nginx

# Limit IOPS
docker run --device-read-iops=/dev/sda:1000 nginx
```

4. **Network**
   - Bandwidth limits (requires tc - traffic control)

**Cgroup Hierarchy:**

```
/sys/fs/cgroup/
├── cpu/
│   └── docker/
│       └── <container-id>/
│           ├── cpu.shares
│           ├── cpu.cfs_quota_us
│           └── cpu.cfs_period_us
├── memory/
│   └── docker/
│       └── <container-id>/
│           ├── memory.limit_in_bytes
│           ├── memory.usage_in_bytes
│           └── memory.stat
├── blkio/
│   └── docker/
│       └── <container-id>/
│           ├── blkio.throttle.read_bps_device
│           └── blkio.throttle.write_bps_device
└── devices/
    └── docker/
        └── <container-id>/
            └── devices.list
```

**Viewing Cgroup Settings:**

```bash
# Find container ID
CONTAINER_ID=$(docker inspect --format='{{.Id}}' myapp)

# View CPU settings
cat /sys/fs/cgroup/cpu/docker/$CONTAINER_ID/cpu.shares

# View memory limit
cat /sys/fs/cgroup/memory/docker/$CONTAINER_ID/memory.limit_in_bytes

# View current memory usage
cat /sys/fs/cgroup/memory/docker/$CONTAINER_ID/memory.usage_in_bytes
```

### 7.3 Resource Limits in Practice

**Comprehensive Resource Configuration:**

```bash
docker run -d \
  --name resource-limited \
  --cpus=2 \
  --cpu-shares=1024 \
  --memory=2g \
  --memory-reservation=1g \
  --memory-swap=3g \
  --kernel-memory=512m \
  --device-read-bps=/dev/sda:10mb \
  --device-write-bps=/dev/sda:5mb \
  --pids-limit=100 \
  nginx
```

**Monitoring Resource Usage:**

```bash
# Real-time stats
docker stats resource-limited

# One-time stats
docker stats --no-stream resource-limited

# Stats for all containers
docker stats --all

# Custom format
docker stats --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}"
```

---

## 8. Union File Systems

### 8.1 How Union File Systems Work

Union file systems allow files and directories from separate file systems (layers) to be transparently overlaid, forming a single coherent file system.

**Layered Architecture:**

```
Container Layer (Read-Write)
─────────────────────────────
Image Layer 4 (Read-Only) - Application files
─────────────────────────────
Image Layer 3 (Read-Only) - Dependencies
─────────────────────────────
Image Layer 2 (Read-Only) - Runtime
─────────────────────────────
Image Layer 1 (Read-Only) - Base OS
─────────────────────────────
```

**Copy-on-Write (CoW) Strategy:**

When a container modifies a file from a read-only layer:

```
1. File exists in read-only layer
   ↓
2. Container tries to modify file
   ↓
3. Storage driver copies file to container layer
   ↓
4. Modification happens in container layer
   ↓
5. Original file in image layer unchanged
```

### 8.2 Storage Drivers

Docker supports multiple storage drivers, each with different characteristics.

**Common Storage Drivers:**

1. **overlay2** (Recommended)
   - Modern, efficient
   - Good performance
   - Requires Linux kernel 4.0+
   - Default on most systems

2. **aufs**
   - Older, stable
   - Good for many layers
   - Not in mainline kernel

3. **devicemapper**
   - Block-level storage
   - Can use direct-lvm for production
   - More complex setup

4. **btrfs**
   - Uses Btrfs filesystem features
   - Requires Btrfs filesystem
   - Good for snapshots

5. **zfs**
   - Uses ZFS filesystem
   - Excellent for large deployments
   - Requires ZFS

**Checking Storage Driver:**

```bash
# Show storage driver info
docker info | grep "Storage Driver"

# Detailed storage info
docker info --format '{{.Driver}}'
```

### 8.3 overlay2 Deep Dive

**Directory Structure:**

```
/var/lib/docker/overlay2/
├── <layer-id>/
│   ├── diff/          # Layer contents
│   ├── link           # Short identifier
│   ├── lower          # Parent layers
│   └── work/          # Internal use
├── <layer-id>/
│   └── ...
└── l/                 # Symbolic links
    ├── <short-id> -> ../<layer-id>/diff
    └── ...
```

**How overlay2 Works:**

```
Container View:
/
├── bin/
├── etc/
├── app/
│   └── myapp
└── ...

Actual Structure:
upperdir: /var/lib/docker/overlay2/<container-id>/diff
lowerdir: /var/lib/docker/overlay2/<layer1>/diff:
          /var/lib/docker/overlay2/<layer2>/diff:
          /var/lib/docker/overlay2/<layer3>/diff
merged:   /var/lib/docker/overlay2/<container-id>/merged
workdir:  /var/lib/docker/overlay2/<container-id>/work
```

**Layer Sharing:**

```
Image: nginx:latest
├── Layer 1: Base OS (shared)
├── Layer 2: Nginx (shared)
└── Layer 3: Config

Container 1 (from nginx)
└── Container Layer 1 (unique)

Container 2 (from nginx)
└── Container Layer 2 (unique)

Both containers share Layers 1-3!
```

### 8.4 Image Layer Optimization

**Best Practices:**

1. **Minimize Layers**
```dockerfile
# Bad: Multiple layers
RUN apt-get update
RUN apt-get install -y package1
RUN apt-get install -y package2

# Good: Single layer
RUN apt-get update && \
    apt-get install -y package1 package2 && \
    rm -rf /var/lib/apt/lists/*
```

2. **Order Layers by Change Frequency**
```dockerfile
# Least frequently changed first
FROM ubuntu:22.04
RUN apt-get update && apt-get install -y python3
COPY requirements.txt .
RUN pip install -r requirements.txt
# Most frequently changed last
COPY . /app
```

3. **Use .dockerignore**
```
# .dockerignore
.git
.gitignore
node_modules
*.log
.env
```

4. **Multi-stage Builds**
```dockerfile
# Build stage
FROM golang:1.20 AS builder
WORKDIR /app
COPY . .
RUN go build -o myapp

# Runtime stage
FROM alpine:latest
COPY --from=builder /app/myapp /usr/local/bin/
CMD ["myapp"]
```

### 8.5 Inspecting Layers

**View Image Layers:**

```bash
# Show image history
docker history nginx

# Detailed layer information
docker inspect nginx --format='{{json .RootFS.Layers}}' | jq

# Show layer sizes
docker history --no-trunc --format "{{.Size}}\t{{.CreatedBy}}" nginx
```

**Example Output:**

```
IMAGE          CREATED       CREATED BY                                      SIZE
nginx:latest   2 weeks ago   /bin/sh -c #(nop)  CMD ["nginx" "-g" "daemon…   0B
<missing>      2 weeks ago   /bin/sh -c #(nop)  STOPSIGNAL SIGQUIT           0B
<missing>      2 weeks ago   /bin/sh -c #(nop)  EXPOSE 80                    0B
<missing>      2 weeks ago   /bin/sh -c ln -sf /dev/stdout /var/log/ngin…   22B
<missing>      2 weeks ago   /bin/sh -c set -x     && addgroup --system -…   61.1MB
<missing>      2 weeks ago   /bin/sh -c #(nop)  ENV PKG_RELEASE=1~bullseye   0B
<missing>      2 weeks ago   /bin/sh -c #(nop)  ENV NV_VERSION=1.23.3        0B
<missing>      2 weeks ago   /bin/sh -c #(nop)  LABEL maintainer=NGINX Do…   0B
<missing>      2 weeks ago   /bin/sh -c #(nop)  CMD ["bash"]                 0B
<missing>      2 weeks ago   /bin/sh -c #(nop) ADD file:1f4eb46669b5b6275…   80.4MB
```

---

## 9. Container Networking Fundamentals

### 9.1 Network Namespace Isolation

Each container gets its own network namespace with:
- Network interfaces
- Routing tables
- Firewall rules
- Network statistics

**Default Container Network Setup:**

```
Host:
┌─────────────────────────────────────┐
│  Physical Interface (eth0)          │
│  IP: 192.168.1.100                  │
└─────────────────────────────────────┘
              ↓
┌─────────────────────────────────────┐
│  Docker Bridge (docker0)            │
│  IP: 172.17.0.1                     │
└─────────────────────────────────────┘
         ↓              ↓
    ┌────────┐    ┌────────┐
    │ veth0  │    │ veth1  │
    └────────┘    └────────┘
         ↓              ↓
Container 1        Container 2
┌────────┐        ┌────────┐
│  eth0  │        │  eth0  │
│172.17. │        │172.17. │
│  0.2   │        │  0.3   │
└────────┘        └────────┘
```

### 9.2 Virtual Ethernet Pairs (veth)

Containers connect to the host using virtual ethernet pairs:

```
Container Network Namespace    Host Network Namespace
┌─────────────────────┐        ┌─────────────────────┐
│                     │        │                     │
│  ┌──────────────┐   │        │   ┌──────────────┐  │
│  │ eth0@if123   │◄──┼────────┼──►│ veth123@if1  │  │
│  │ 172.17.0.2   │   │        │   │              │  │
│  └──────────────┘   │        │   └──────────────┘  │
│                     │        │          │          │
└─────────────────────┘        │          ↓          │
                               │   ┌──────────────┐  │
                               │   │   docker0    │  │
                               │   │  172.17.0.1  │  │
                               │   └──────────────┘  │
                               └─────────────────────┘
```

**Viewing veth Pairs:**

```bash
# On host
ip link show

# Find veth for specific container
docker inspect myapp --format='{{.NetworkSettings.SandboxKey}}'

# Inside container
ip addr show
```

### 9.3 Port Mapping

Port mapping allows external access to container services:

```
External Client
      ↓
Host:80 (iptables NAT rule)
      ↓
Container:80

iptables rule:
DNAT: 192.168.1.100:80 → 172.17.0.2:80
```

**Port Mapping Examples:**

```bash
# Map host port 8080 to container port 80
docker run -p 8080:80 nginx

# Map to specific host interface
docker run -p 127.0.0.1:8080:80 nginx

# Map random host port
docker run -P nginx

# Map multiple ports
docker run -p 80:80 -p 443:443 nginx

# Map UDP port
docker run -p 53:53/udp dns-server
```

**Viewing Port Mappings:**

```bash
# Show port mappings
docker port myapp

# Inspect network settings
docker inspect myapp --format='{{json .NetworkSettings.Ports}}' | jq
```

---

## 10. Container Security Basics

### 10.1 Security Layers

```
┌─────────────────────────────────────┐
│  Application Security               │
│  - Input validation                 │
│  - Secure coding practices          │
└─────────────────────────────────────┘
              ↓
┌─────────────────────────────────────┐
│  Container Security                 │
│  - Non-root user                    │
│  - Read-only filesystem             │
│  - Dropped capabilities             │
└─────────────────────────────────────┘
              ↓
┌─────────────────────────────────────┐
│  Image Security                     │
│  - Minimal base images              │
│  - No secrets in images             │
│  - Vulnerability scanning           │
└─────────────────────────────────────┘
              ↓
┌─────────────────────────────────────┐
│  Runtime Security                   │
│  - AppArmor/SELinux                 │
│  - Seccomp profiles                 │
│  - Resource limits                  │
└─────────────────────────────────────┘
              ↓
┌─────────────────────────────────────┐
│  Host Security                      │
│  - Kernel hardening                 │
│  - Regular updates                  │
│  - Access control                   │
└─────────────────────────────────────┘
```

### 10.2 Running as Non-Root

**Why it matters:**
- Root in container can potentially escape to host
- Principle of least privilege
- Limits damage from compromised container

**Implementation:**

```dockerfile
# Create non-root user
FROM ubuntu:22.04
RUN useradd -m -u 1000 appuser
USER appuser
WORKDIR /home/appuser
COPY --chown=appuser:appuser app /home/appuser/app
CMD ["./app"]
```

```bash
# Run as specific user
docker run --user 1000:1000 myapp

# Verify user
docker exec myapp whoami
```

### 10.3 Linux Capabilities

Instead of running as root, drop unnecessary capabilities:

```bash
# Drop all capabilities, add only needed ones
docker run --cap-drop=ALL --cap-add=NET_BIND_SERVICE nginx

# Common capabilities:
# NET_BIND_SERVICE - Bind to ports < 1024
# CHOWN - Change file ownership
# DAC_OVERRIDE - Bypass file permission checks
# SETUID/SETGID - Change user/group ID
```

### 10.4 Read-Only Filesystem

```bash
# Make root filesystem read-only
docker run --read-only nginx

# With tmpfs for writable directories
docker run --read-only --tmpfs /tmp --tmpfs /var/run nginx
```

---

## 11. Summary

### Key Takeaways

1. **Containers are isolated processes** using Linux namespaces and cgroups
2. **Docker architecture** consists of CLI, daemon, containerd, and runc
3. **Images are layered** using union file systems for efficiency
4. **Namespaces provide isolation** for PID, network, mount, UTS, IPC, user, and cgroup
5. **Cgroups limit resources** including CPU, memory, I/O, and network
6. **Container lifecycle** includes created, running, paused, stopped, and removed states
7. **Security is multi-layered** from application to host

### Next Steps

- Practice creating and managing containers
- Learn Dockerfile syntax and image building
- Understand Docker networking in depth
- Explore Docker volumes and data persistence
- Study Docker Compose for multi-container apps
- Implement security best practices

---

**Document Version**: 1.0
**Last Updated**: 2026-03-26

