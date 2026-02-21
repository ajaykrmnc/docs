# Docker Comprehensive Guide

## Table of Contents
1. [Introduction to Docker](#introduction-to-docker)
2. [Docker Architecture](#docker-architecture)
   - [High-Level Architecture](#high-level-architecture)
   - [Component Breakdown](#component-breakdown)
   - [Detailed Component Interaction](#detailed-component-interaction)
   - [Container Creation Process](#container-creation-process)
   - [Image Build Architecture](#image-build-architecture)
   - [Storage Driver Architecture](#storage-driver-architecture)
   - [Network Architecture Internals](#network-architecture-internals)
   - [OCI Specifications](#oci-open-container-initiative-specifications)
   - [Docker API Architecture](#docker-api-architecture)
3. [Core Concepts](#core-concepts)
4. [Installation](#installation)
5. [Docker CLI Commands](#docker-cli-commands)
6. [Dockerfile Deep Dive](#dockerfile-deep-dive)
7. [Docker Networking](#docker-networking)
8. [Docker Storage and Volumes](#docker-storage-and-volumes)
9. [Docker Compose](#docker-compose)
10. [Docker Swarm](#docker-swarm)
11. [Security Best Practices](#security-best-practices)
12. [Performance Optimization](#performance-optimization)
13. [Troubleshooting](#troubleshooting)
14. [Real-World Use Cases](#real-world-use-cases)

---

## Introduction to Docker

### What is Docker?
[](2026-02-21_.md)
Docker is an open-source platform that automates the deployment, scaling, and management of applications using **containerization**. Containers package an application along with its dependencies, libraries, and configuration files into a single, portable unit that can run consistently across different computing environments.

### Containers vs Virtual Machines

```
┌─────────────────────────────────────────────────────────────────────┐
│                    CONTAINERS vs VIRTUAL MACHINES                    │
├─────────────────────────────────┬───────────────────────────────────┤
│         CONTAINERS              │       VIRTUAL MACHINES            │
├─────────────────────────────────┼───────────────────────────────────┤
│  ┌─────┐ ┌─────┐ ┌─────┐       │  ┌─────────┐ ┌─────────┐          │
│  │App A│ │App B│ │App C│       │  │  App A  │ │  App B  │          │
│  ├─────┤ ├─────┤ ├─────┤       │  ├─────────┤ ├─────────┤          │
│  │Bins/│ │Bins/│ │Bins/│       │  │Bins/Libs│ │Bins/Libs│          │
│  │Libs │ │Libs │ │Libs │       │  ├─────────┤ ├─────────┤          │
│  └──┬──┘ └──┬──┘ └──┬──┘       │  │Guest OS │ │Guest OS │          │
│     └───────┼───────┘          │  └────┬────┘ └────┬────┘          │
│      ┌──────┴──────┐           │       └─────┬─────┘               │
│      │Docker Engine│           │       ┌─────┴─────┐               │
│      ├─────────────┤           │       │Hypervisor │               │
│      │   Host OS   │           │       ├───────────┤               │
│      ├─────────────┤           │       │  Host OS  │               │
│      │Infrastructure│          │       ├───────────┤               │
│      └─────────────┘           │       │Infrastructure│            │
│                                │       └───────────┘               │
│  • Lightweight (MBs)           │  • Heavy (GBs)                    │
│  • Startup: Seconds            │  • Startup: Minutes               │
│  • Shares Host Kernel          │  • Full OS per VM                 │
│  • Process-level isolation     │  • Hardware-level isolation       │
└─────────────────────────────────┴───────────────────────────────────┘
```

### Key Benefits of Docker

| Benefit | Description |
|---------|-------------|
| **Portability** | "Build once, run anywhere" - containers work identically across development, staging, and production |
| **Isolation** | Each container runs in its own isolated environment |
| **Efficiency** | Containers share the host OS kernel, reducing overhead |
| **Scalability** | Easy to scale horizontally by spinning up more containers |
| **Version Control** | Images are versioned, enabling easy rollbacks |
| **DevOps Integration** | Seamlessly integrates with CI/CD pipelines |

---

## Docker Architecture

### High-Level Architecture

```
┌────────────────────────────────────────────────────────────────────────────┐
│                           DOCKER ARCHITECTURE                               │
├────────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│  ┌──────────────────┐                                                      │
│  │   Docker Client  │  docker build, docker pull, docker run               │
│  │    (docker CLI)  │                                                      │
│  └────────┬─────────┘                                                      │
│           │ REST API                                                       │
│           ▼                                                                │
│  ┌──────────────────────────────────────────────────────────────────────┐ │
│  │                        DOCKER HOST                                    │ │
│  │  ┌──────────────────────────────────────────────────────────────┐   │ │
│  │  │                     Docker Daemon (dockerd)                   │   │ │
│  │  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐   │   │ │
│  │  │  │   Images    │  │ Containers  │  │     Networks        │   │   │ │
│  │  │  │  Storage    │  │  Runtime    │  │     Volumes         │   │   │ │
│  │  │  └─────────────┘  └─────────────┘  └─────────────────────┘   │   │ │
│  │  └──────────────────────────────────────────────────────────────┘   │ │
│  │           │                                                          │ │
│  │           ▼                                                          │ │
│  │  ┌──────────────────────────────────────────────────────────────┐   │ │
│  │  │                      containerd                               │   │ │
│  │  │    (Industry-standard container runtime)                      │   │ │
│  │  └───────────────────────────┬──────────────────────────────────┘   │ │
│  │                              │                                       │ │
│  │                              ▼                                       │ │
│  │  ┌──────────────────────────────────────────────────────────────┐   │ │
│  │  │                        runc                                   │   │ │
│  │  │    (OCI-compliant container runtime)                          │   │ │
│  │  └──────────────────────────────────────────────────────────────┘   │ │
│  └──────────────────────────────────────────────────────────────────────┘ │
│           │                                                                │
│           ▼                                                                │
│  ┌──────────────────┐                                                      │
│  │  Docker Registry │  Docker Hub, ECR, GCR, Private Registry              │
│  └──────────────────┘                                                      │
└────────────────────────────────────────────────────────────────────────────┘
```

### Component Breakdown

#### 1. Docker Client
The primary interface for users to interact with Docker. Commands like `docker run`, `docker build`, and `docker pull` communicate with the Docker daemon via REST API.

#### 2. Docker Daemon (dockerd)
The background service running on the host that manages:
- Building, running, and distributing containers
- Docker images, networks, and volumes
- Listening to Docker API requests

#### 3. containerd
A high-level container runtime that manages:
- Container lifecycle (create, start, stop, delete)
- Image pull and push operations
- Storage and networking interfaces

#### 4. runc
A lightweight, OCI-compliant container runtime that:
- Spawns and runs containers according to OCI specification
- Interfaces directly with the Linux kernel (namespaces, cgroups)
- Is the reference implementation of the OCI runtime spec

#### 5. Docker Registry
A storage and distribution system for Docker images:
- **Docker Hub**: Default public registry
- **Amazon ECR**: AWS container registry
- **Google GCR**: Google Cloud container registry
- **Private Registries**: Self-hosted solutions

### Detailed Component Interaction

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                    DOCKER COMPONENT INTERACTION FLOW                              │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                   │
│   User: docker run nginx                                                         │
│           │                                                                       │
│           ▼                                                                       │
│   ┌───────────────────────┐                                                      │
│   │    Docker CLI         │  1. Parse command and options                        │
│   │   (docker client)     │  2. Create API request                               │
│   └───────────┬───────────┘                                                      │
│               │  HTTP/Unix Socket                                                │
│               ▼                                                                   │
│   ┌───────────────────────┐                                                      │
│   │    Docker Daemon      │  3. Receive request via REST API                     │
│   │      (dockerd)        │  4. Check if image exists locally                    │
│   │                       │  5. Pull image from registry if needed               │
│   └───────────┬───────────┘  6. Create container configuration                   │
│               │  gRPC                                                            │
│               ▼                                                                   │
│   ┌───────────────────────┐                                                      │
│   │     containerd        │  7. Receive container spec                           │
│   │  (container runtime)  │  8. Create container bundle                          │
│   │                       │  9. Set up networking, storage                       │
│   └───────────┬───────────┘                                                      │
│               │  OCI Runtime Spec                                                │
│               ▼                                                                   │
│   ┌───────────────────────┐                                                      │
│   │       runc            │  10. Create namespaces                               │
│   │ (OCI runtime binary)  │  11. Configure cgroups                               │
│   │                       │  12. Set up root filesystem                          │
│   └───────────┬───────────┘  13. Execute container process                       │
│               │                                                                   │
│               ▼                                                                   │
│   ┌───────────────────────┐                                                      │
│   │   Linux Kernel        │  Provides: namespaces, cgroups, capabilities,        │
│   │                       │  seccomp, AppArmor/SELinux                           │
│   └───────────────────────┘                                                      │
│                                                                                   │
└─────────────────────────────────────────────────────────────────────────────────┘
```

### Container Creation Process

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                       CONTAINER CREATION DEEP DIVE                                │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                   │
│  STEP 1: IMAGE RESOLUTION                                                        │
│  ─────────────────────────                                                       │
│  ┌─────────────┐      ┌─────────────┐      ┌─────────────┐                      │
│  │ Check Local │──NO──▶│  Pull from  │──────▶│ Store Image │                     │
│  │   Cache     │       │  Registry   │       │  Locally    │                     │
│  └──────┬──────┘       └─────────────┘       └─────────────┘                     │
│         │ YES                                                                     │
│         ▼                                                                         │
│  STEP 2: FILESYSTEM SETUP                                                        │
│  ────────────────────────                                                        │
│  ┌─────────────────────────────────────────────────────────────────────────┐    │
│  │                    Union Filesystem (OverlayFS)                          │    │
│  │  ┌─────────────────────────────────────────────────────────────────┐    │    │
│  │  │  Writable Container Layer (upperdir)                             │    │    │
│  │  │  • All writes go here                                            │    │    │
│  │  │  • Copy-on-write for modified files                              │    │    │
│  │  └─────────────────────────────────────────────────────────────────┘    │    │
│  │  ┌─────────────────────────────────────────────────────────────────┐    │    │
│  │  │  Read-Only Image Layers (lowerdir)                               │    │    │
│  │  │  • Layer n: Application                                          │    │    │
│  │  │  • Layer 2: Dependencies                                         │    │    │
│  │  │  • Layer 1: Base OS                                              │    │    │
│  │  └─────────────────────────────────────────────────────────────────┘    │    │
│  │  ┌─────────────────────────────────────────────────────────────────┐    │    │
│  │  │  Merged View (merged)                                            │    │    │
│  │  │  • What the container sees as /                                  │    │    │
│  │  └─────────────────────────────────────────────────────────────────┘    │    │
│  └─────────────────────────────────────────────────────────────────────────┘    │
│                                                                                   │
│  STEP 3: NAMESPACE CREATION                                                      │
│  ──────────────────────────                                                      │
│  ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐              │
│  │  PID   │ │  NET   │ │  MNT   │ │  UTS   │ │  IPC   │ │  USER  │              │
│  │Namespace│ │Namespace│ │Namespace│ │Namespace│ │Namespace│ │Namespace│             │
│  └────────┘ └────────┘ └────────┘ └────────┘ └────────┘ └────────┘              │
│       │          │          │          │          │          │                   │
│       └──────────┴──────────┴──────────┴──────────┴──────────┘                   │
│                              │                                                    │
│                              ▼                                                    │
│  STEP 4: CGROUP CONFIGURATION                                                    │
│  ────────────────────────────                                                    │
│  ┌─────────────────────────────────────────────────────────────────────────┐    │
│  │  /sys/fs/cgroup/                                                        │    │
│  │  ├── cpu/docker/<container-id>/                                         │    │
│  │  │   ├── cpu.cfs_quota_us      # CPU time quota                         │    │
│  │  │   └── cpu.shares            # CPU shares                             │    │
│  │  ├── memory/docker/<container-id>/                                      │    │
│  │  │   ├── memory.limit_in_bytes # Memory limit                           │    │
│  │  │   └── memory.memsw.limit_in_bytes # Memory+Swap                      │    │
│  │  └── pids/docker/<container-id>/                                        │    │
│  │      └── pids.max              # Max processes                          │    │
│  └─────────────────────────────────────────────────────────────────────────┘    │
│                                                                                   │
│  STEP 5: NETWORK CONFIGURATION                                                   │
│  ─────────────────────────────                                                   │
│  ┌─────────────────────────────────────────────────────────────────────────┐    │
│  │  1. Create veth pair (virtual ethernet)                                  │    │
│  │  2. Attach one end to container namespace (eth0)                         │    │
│  │  3. Attach other end to docker0 bridge                                   │    │
│  │  4. Assign IP address from bridge subnet                                 │    │
│  │  5. Set up iptables rules for NAT/port mapping                           │    │
│  └─────────────────────────────────────────────────────────────────────────┘    │
│                                                                                   │
│  STEP 6: PROCESS EXECUTION                                                       │
│  ─────────────────────────                                                       │
│  ┌─────────────────────────────────────────────────────────────────────────┐    │
│  │  runc:                                                                   │    │
│  │  1. Set up pivot_root to container filesystem                            │    │
│  │  2. Apply seccomp profile (system call filter)                           │    │
│  │  3. Apply AppArmor/SELinux profiles                                      │    │
│  │  4. Drop capabilities                                                    │    │
│  │  5. Execute ENTRYPOINT/CMD as PID 1                                      │    │
│  └─────────────────────────────────────────────────────────────────────────┘    │
│                                                                                   │
└─────────────────────────────────────────────────────────────────────────────────┘
```

### Image Build Architecture

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                         IMAGE BUILD PROCESS                                       │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                   │
│   Dockerfile                                                                      │
│   ┌─────────────────────────────────────────────────────────────────────────┐   │
│   │  FROM python:3.11-slim                                                   │   │
│   │  WORKDIR /app                                                            │   │
│   │  COPY requirements.txt .                                                 │   │
│   │  RUN pip install -r requirements.txt                                     │   │
│   │  COPY . .                                                                │   │
│   │  CMD ["python", "app.py"]                                                │   │
│   └───────────────────────────────────┬─────────────────────────────────────┘   │
│                                       │                                          │
│                                       ▼                                          │
│   ┌─────────────────────────────────────────────────────────────────────────┐   │
│   │                        BuildKit Engine                                   │   │
│   │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐    │   │
│   │  │   Parser    │──▶│   Solver   │──▶│  Executor  │──▶│  Exporter   │    │   │
│   │  │             │  │  (DAG)     │  │            │  │            │    │   │
│   │  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘    │   │
│   └───────────────────────────────────┬─────────────────────────────────────┘   │
│                                       │                                          │
│   LAYER CREATION PROCESS:             │                                          │
│   ─────────────────────               ▼                                          │
│                                                                                   │
│   Step 1/6: FROM python:3.11-slim                                                │
│   ┌──────────────────────────────────┐                                           │
│   │  Pull base image layers          │                                           │
│   │  sha256:abc123... (25MB)         │ ─── Layer 1: Debian slim                  │
│   │  sha256:def456... (45MB)         │ ─── Layer 2: Python runtime               │
│   └──────────────────────────────────┘                                           │
│                  │                                                                │
│                  ▼                                                                │
│   Step 2/6: WORKDIR /app                                                         │
│   ┌──────────────────────────────────┐                                           │
│   │  Create /app directory           │                                           │
│   │  sha256:ghi789... (0B)           │ ─── Layer 3: Metadata only                │
│   └──────────────────────────────────┘                                           │
│                  │                                                                │
│                  ▼                                                                │
│   Step 3/6: COPY requirements.txt .                                              │
│   ┌──────────────────────────────────┐                                           │
│   │  Copy file to image              │                                           │
│   │  sha256:jkl012... (1KB)          │ ─── Layer 4: requirements.txt             │
│   └──────────────────────────────────┘                                           │
│                  │                                                                │
│                  ▼                                                                │
│   Step 4/6: RUN pip install...       (CACHED if requirements.txt unchanged)      │
│   ┌──────────────────────────────────┐                                           │
│   │  Execute in temporary container  │                                           │
│   │  Commit changes as new layer     │                                           │
│   │  sha256:mno345... (50MB)         │ ─── Layer 5: Python packages              │
│   └──────────────────────────────────┘                                           │
│                  │                                                                │
│                  ▼                                                                │
│   Step 5/6: COPY . .                                                             │
│   ┌──────────────────────────────────┐                                           │
│   │  Copy application code           │                                           │
│   │  sha256:pqr678... (2MB)          │ ─── Layer 6: Application                  │
│   └──────────────────────────────────┘                                           │
│                  │                                                                │
│                  ▼                                                                │
│   Step 6/6: CMD ["python", "app.py"]                                             │
│   ┌──────────────────────────────────┐                                           │
│   │  Set default command             │                                           │
│   │  Image config metadata           │ ─── No new layer (config only)            │
│   └──────────────────────────────────┘                                           │
│                                                                                   │
│   FINAL IMAGE MANIFEST:                                                          │
│   ┌─────────────────────────────────────────────────────────────────────────┐   │
│   │  {                                                                       │   │
│   │    "schemaVersion": 2,                                                   │   │
│   │    "config": { "digest": "sha256:config..." },                           │   │
│   │    "layers": [                                                           │   │
│   │      { "digest": "sha256:abc123...", "size": 25000000 },                │   │
│   │      { "digest": "sha256:def456...", "size": 45000000 },                │   │
│   │      { "digest": "sha256:jkl012...", "size": 1024 },                    │   │
│   │      { "digest": "sha256:mno345...", "size": 50000000 },                │   │
│   │      { "digest": "sha256:pqr678...", "size": 2000000 }                  │   │
│   │    ]                                                                     │   │
│   │  }                                                                       │   │
│   └─────────────────────────────────────────────────────────────────────────┘   │
│                                                                                   │
└─────────────────────────────────────────────────────────────────────────────────┘
```

### Storage Driver Architecture

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                       STORAGE DRIVER ARCHITECTURE                                 │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                   │
│   Docker supports multiple storage drivers for managing image layers:             │
│                                                                                   │
│   ┌─────────────────────────────────────────────────────────────────────────┐   │
│   │                         OVERLAY2 (Recommended)                           │   │
│   ├─────────────────────────────────────────────────────────────────────────┤   │
│   │                                                                          │   │
│   │   /var/lib/docker/overlay2/                                              │   │
│   │   │                                                                      │   │
│   │   ├── l/                          # Shortened layer identifiers          │   │
│   │   │   ├── ABC123 -> ../abc123.../diff                                    │   │
│   │   │   └── DEF456 -> ../def456.../diff                                    │   │
│   │   │                                                                      │   │
│   │   ├── abc123.../                  # Layer directory                      │   │
│   │   │   ├── diff/                   # Layer contents                       │   │
│   │   │   ├── link                    # Shortened ID                         │   │
│   │   │   └── lower                   # Parent layer references              │   │
│   │   │                                                                      │   │
│   │   └── <container-id>/             # Container mount                      │   │
│   │       ├── diff/                   # Writable layer                       │   │
│   │       ├── merged/                 # Union mount (what container sees)    │   │
│   │       ├── work/                   # OverlayFS workdir                    │   │
│   │       └── lower                   # All lower layers                     │   │
│   │                                                                          │   │
│   │   Mount command (internal):                                              │   │
│   │   mount -t overlay overlay -o                                            │   │
│   │     lowerdir=/layer1:/layer2:/layer3,                                    │   │
│   │     upperdir=/container/diff,                                            │   │
│   │     workdir=/container/work                                              │   │
│   │     /container/merged                                                    │   │
│   │                                                                          │   │
│   └─────────────────────────────────────────────────────────────────────────┘   │
│                                                                                   │
│   STORAGE DRIVER COMPARISON:                                                      │
│   ┌─────────────┬─────────────┬─────────────┬─────────────┬─────────────────┐   │
│   │   Driver    │ Performance │ Stability   │  Use Case   │  Requirements   │   │
│   ├─────────────┼─────────────┼─────────────┼─────────────┼─────────────────┤   │
│   │  overlay2   │   High      │   Stable    │  Default    │ Kernel 4.0+     │   │
│   │  fuse-overlayfs │ Medium │   Stable    │ Rootless    │ FUSE            │   │
│   │  btrfs      │   High      │   Stable    │ BTRFS fs    │ BTRFS volume    │   │
│   │  zfs        │   High      │   Stable    │ ZFS fs      │ ZFS volume      │   │
│   │  vfs        │   Low       │   Stable    │ Testing     │ None            │   │
│   └─────────────┴─────────────┴─────────────┴─────────────┴─────────────────┘   │
│                                                                                   │
│   Copy-on-Write (CoW) Process:                                                   │
│   ┌─────────────────────────────────────────────────────────────────────────┐   │
│   │                                                                          │   │
│   │   1. Container reads /etc/config.txt                                     │   │
│   │      └── File found in lower layer → Read directly                       │   │
│   │                                                                          │   │
│   │   2. Container modifies /etc/config.txt                                  │   │
│   │      └── File copied to upper (writable) layer                           │   │
│   │      └── Modification applied to copy                                    │   │
│   │      └── Original in lower layer unchanged                               │   │
│   │                                                                          │   │
│   │   3. Container deletes /etc/hosts                                        │   │
│   │      └── Whiteout file created in upper layer                            │   │
│   │      └── Original still exists in lower layer                            │   │
│   │                                                                          │   │
│   └─────────────────────────────────────────────────────────────────────────┘   │
│                                                                                   │
└─────────────────────────────────────────────────────────────────────────────────┘
```

### Network Architecture Internals

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                       DOCKER NETWORK ARCHITECTURE                                 │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                   │
│   DEFAULT BRIDGE NETWORK:                                                        │
│   ──────────────────────                                                         │
│                                                                                   │
│   ┌─────────────────────────────────────────────────────────────────────────┐   │
│   │                           HOST MACHINE                                   │   │
│   │                                                                          │   │
│   │   ┌──────────┐        ┌──────────┐        ┌──────────┐                  │   │
│   │   │Container1│        │Container2│        │Container3│                  │   │
│   │   │          │        │          │        │          │                  │   │
│   │   │ eth0     │        │ eth0     │        │ eth0     │                  │   │
│   │   │172.17.0.2│        │172.17.0.3│        │172.17.0.4│                  │   │
│   │   └────┬─────┘        └────┬─────┘        └────┬─────┘                  │   │
│   │        │                   │                   │                         │   │
│   │        │ veth pair         │ veth pair         │ veth pair               │   │
│   │        │                   │                   │                         │   │
│   │   ┌────┴───────────────────┴───────────────────┴────┐                   │   │
│   │   │                  docker0 bridge                  │                   │   │
│   │   │                  172.17.0.1/16                   │                   │   │
│   │   └─────────────────────────┬────────────────────────┘                   │   │
│   │                             │                                            │   │
│   │                             │ NAT (iptables)                             │   │
│   │                             │                                            │   │
│   │   ┌─────────────────────────┴────────────────────────┐                   │   │
│   │   │                    eth0 (Host)                    │                   │   │
│   │   │                   192.168.1.100                   │                   │   │
│   │   └───────────────────────────────────────────────────┘                   │   │
│   │                                                                          │   │
│   └─────────────────────────────────────────────────────────────────────────┘   │
│                                                                                   │
│   IPTABLES RULES FOR PORT MAPPING (docker run -p 8080:80):                       │
│   ─────────────────────────────────────────────────────────                      │
│   ┌─────────────────────────────────────────────────────────────────────────┐   │
│   │  # NAT table - PREROUTING chain (incoming traffic)                       │   │
│   │  -A DOCKER -p tcp --dport 8080 -j DNAT --to 172.17.0.2:80                │   │
│   │                                                                          │   │
│   │  # NAT table - POSTROUTING chain (outgoing traffic)                      │   │
│   │  -A POSTROUTING -s 172.17.0.0/16 ! -o docker0 -j MASQUERADE              │   │
│   │                                                                          │   │
│   │  # Filter table - FORWARD chain                                          │   │
│   │  -A DOCKER -d 172.17.0.2 -p tcp --dport 80 -j ACCEPT                     │   │
│   └─────────────────────────────────────────────────────────────────────────┘   │
│                                                                                   │
│   USER-DEFINED BRIDGE NETWORK:                                                   │
│   ────────────────────────────                                                   │
│   ┌─────────────────────────────────────────────────────────────────────────┐   │
│   │                                                                          │   │
│   │   Advantages over default bridge:                                        │   │
│   │   ✓ Automatic DNS resolution between containers                          │   │
│   │   ✓ Better isolation                                                     │   │
│   │   ✓ Configurable subnet and gateway                                      │   │
│   │   ✓ Containers can be connected/disconnected on the fly                  │   │
│   │                                                                          │   │
│   │   docker network create --driver bridge \                                │   │
│   │     --subnet 10.0.0.0/24 \                                               │   │
│   │     --gateway 10.0.0.1 \                                                 │   │
│   │     my_network                                                           │   │
│   │                                                                          │   │
│   │   ┌──────────┐    DNS    ┌──────────┐                                   │   │
│   │   │   web    │◄─────────►│   api    │                                   │   │
│   │   │ 10.0.0.2 │           │ 10.0.0.3 │                                   │   │
│   │   └──────────┘           └──────────┘                                   │   │
│   │         │                      │                                         │   │
│   │         └──────────┬───────────┘                                         │   │
│   │                    │                                                     │   │
│   │   ┌────────────────┴────────────────┐                                   │   │
│   │   │     br-xxxxx (my_network)       │                                   │   │
│   │   │          10.0.0.1/24            │                                   │   │
│   │   └─────────────────────────────────┘                                   │   │
│   │                                                                          │   │
│   └─────────────────────────────────────────────────────────────────────────┘   │
│                                                                                   │
└─────────────────────────────────────────────────────────────────────────────────┘
```

### OCI (Open Container Initiative) Specifications

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                       OCI SPECIFICATION OVERVIEW                                  │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                   │
│   The Open Container Initiative defines standards for container formats and      │
│   runtimes, ensuring interoperability across different container platforms.       │
│                                                                                   │
│   ┌─────────────────────────────────────────────────────────────────────────┐   │
│   │                        OCI SPECIFICATIONS                                │   │
│   ├─────────────────┬───────────────────────────────────────────────────────┤   │
│   │                 │                                                        │   │
│   │   Image Spec    │  Defines how container images are built and stored:    │   │
│   │                 │  • Image manifest                                      │   │
│   │                 │  • Image index (multi-platform)                        │   │
│   │                 │  • Filesystem layers (tar+gzip)                        │   │
│   │                 │  • Image configuration                                 │   │
│   │                 │                                                        │   │
│   ├─────────────────┼───────────────────────────────────────────────────────┤   │
│   │                 │                                                        │   │
│   │  Runtime Spec   │  Defines how containers are executed:                  │   │
│   │                 │  • config.json (container configuration)               │   │
│   │                 │  • Filesystem bundle                                   │   │
│   │                 │  • Lifecycle operations (create, start, kill, delete) │   │
│   │                 │  • Linux-specific settings (namespaces, cgroups)       │   │
│   │                 │                                                        │   │
│   ├─────────────────┼───────────────────────────────────────────────────────┤   │
│   │                 │                                                        │   │
│   │ Distribution    │  Defines how images are distributed:                   │   │
│   │     Spec        │  • Registry API                                        │   │
│   │                 │  • Push/Pull operations                                │   │
│   │                 │  • Content addressable storage                         │   │
│   │                 │                                                        │   │
│   └─────────────────┴───────────────────────────────────────────────────────┘   │
│                                                                                   │
│   OCI RUNTIME CONFIG EXAMPLE (config.json):                                      │
│   ──────────────────────────────────────────                                     │
│   {                                                                              │
│     "ociVersion": "1.0.2",                                                       │
│     "process": {                                                                 │
│       "user": { "uid": 0, "gid": 0 },                                            │
│       "args": ["nginx", "-g", "daemon off;"],                                    │
│       "env": ["PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin"],         │
│       "cwd": "/",                                                                │
│       "capabilities": {                                                          │
│         "bounding": ["CAP_NET_BIND_SERVICE"],                                    │
│         "effective": ["CAP_NET_BIND_SERVICE"]                                    │
│       },                                                                         │
│       "rlimits": [{ "type": "RLIMIT_NOFILE", "hard": 1024, "soft": 1024 }]       │
│     },                                                                           │
│     "root": { "path": "rootfs", "readonly": false },                             │
│     "hostname": "my-container",                                                  │
│     "linux": {                                                                   │
│       "namespaces": [                                                            │
│         { "type": "pid" },                                                       │
│         { "type": "network" },                                                   │
│         { "type": "mount" },                                                     │
│         { "type": "uts" },                                                       │
│         { "type": "ipc" }                                                        │
│       ],                                                                         │
│       "resources": {                                                             │
│         "memory": { "limit": 536870912 },                                        │
│         "cpu": { "shares": 1024 }                                                │
│       }                                                                          │
│     }                                                                            │
│   }                                                                              │
│                                                                                   │
│   COMPATIBLE RUNTIMES:                                                           │
│   ┌──────────────┬──────────────────────────────────────────────────────────┐   │
│   │    runc      │ Reference implementation, default Docker runtime         │   │
│   │    crun      │ Fast, lightweight C implementation                       │   │
│   │   gVisor     │ User-space kernel (runsc), enhanced isolation            │   │
│   │   Kata       │ Lightweight VMs for stronger isolation                   │   │
│   │   youki      │ Rust implementation                                      │   │
│   └──────────────┴──────────────────────────────────────────────────────────┘   │
│                                                                                   │
└─────────────────────────────────────────────────────────────────────────────────┘
```

### Docker API Architecture

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                         DOCKER API ARCHITECTURE                                   │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                   │
│   ┌───────────────────────────────────────────────────────────────────────────┐ │
│   │                         API COMMUNICATION FLOW                             │ │
│   │                                                                            │ │
│   │   Docker CLI          SDK Libraries        HTTP Clients                    │ │
│   │   ┌────────┐          ┌────────┐          ┌────────┐                      │ │
│   │   │docker  │          │Go/Python│          │ curl   │                      │ │
│   │   │  CLI   │          │  /Java │          │ httpie │                      │ │
│   │   └───┬────┘          └───┬────┘          └───┬────┘                      │ │
│   │       │                   │                   │                            │ │
│   │       └───────────────────┼───────────────────┘                            │ │
│   │                           │                                                │ │
│   │                           ▼                                                │ │
│   │   ┌───────────────────────────────────────────────────────────────────┐   │ │
│   │   │                     Docker Engine API                              │   │ │
│   │   │                     (REST API v1.44+)                              │   │ │
│   │   ├───────────────────────────────────────────────────────────────────┤   │ │
│   │   │  Unix Socket: /var/run/docker.sock (default)                       │   │ │
│   │   │  TCP Socket:  tcp://host:2375 (unencrypted)                        │   │ │
│   │   │  TCP+TLS:     tcp://host:2376 (encrypted)                          │   │ │
│   │   └───────────────────────────────────────────────────────────────────┘   │ │
│   │                                                                            │ │
│   └───────────────────────────────────────────────────────────────────────────┘ │
│                                                                                   │
│   COMMON API ENDPOINTS:                                                          │
│   ┌─────────────────────────────────────────────────────────────────────────┐   │
│   │  Containers:                                                             │   │
│   │    GET    /containers/json          List containers                      │   │
│   │    POST   /containers/create        Create container                     │   │
│   │    POST   /containers/{id}/start    Start container                      │   │
│   │    POST   /containers/{id}/stop     Stop container                       │   │
│   │    DELETE /containers/{id}          Remove container                     │   │
│   │    GET    /containers/{id}/logs     Get container logs                   │   │
│   │    POST   /containers/{id}/exec     Create exec instance                 │   │
│   │                                                                          │   │
│   │  Images:                                                                 │   │
│   │    GET    /images/json              List images                          │   │
│   │    POST   /images/create            Pull image                           │   │
│   │    POST   /build                    Build image from Dockerfile          │   │
│   │    DELETE /images/{name}            Remove image                         │   │
│   │                                                                          │   │
│   │  Networks:                                                               │   │
│   │    GET    /networks                 List networks                        │   │
│   │    POST   /networks/create          Create network                       │   │
│   │    POST   /networks/{id}/connect    Connect container to network         │   │
│   │                                                                          │   │
│   │  Volumes:                                                                │   │
│   │    GET    /volumes                  List volumes                         │   │
│   │    POST   /volumes/create           Create volume                        │   │
│   │                                                                          │   │
│   │  System:                                                                 │   │
│   │    GET    /info                     System information                   │   │
│   │    GET    /version                  Docker version                       │   │
│   │    GET    /events                   Real-time events                     │   │
│   └─────────────────────────────────────────────────────────────────────────┘   │
│                                                                                   │
│   API EXAMPLE - List containers using curl:                                      │
│   ┌─────────────────────────────────────────────────────────────────────────┐   │
│   │  # Via Unix socket                                                       │   │
│   │  curl --unix-socket /var/run/docker.sock http://localhost/containers/json│   │
│   │                                                                          │   │
│   │  # Via TCP (if enabled)                                                  │   │
│   │  curl http://localhost:2375/containers/json                              │   │
│   │                                                                          │   │
│   │  # Create container                                                      │   │
│   │  curl --unix-socket /var/run/docker.sock \                               │   │
│   │    -H "Content-Type: application/json" \                                 │   │
│   │    -d '{"Image": "nginx", "ExposedPorts": {"80/tcp": {}}}' \             │   │
│   │    http://localhost/containers/create?name=my-nginx                      │   │
│   └─────────────────────────────────────────────────────────────────────────┘   │
│                                                                                   │
└─────────────────────────────────────────────────────────────────────────────────┘
```

---

## Core Concepts

### Images

An image is a read-only template containing instructions for creating a container. Images are built in layers using a Dockerfile.

```
┌─────────────────────────────────────────────────────────────────┐
│                     DOCKER IMAGE LAYERS                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│    ┌─────────────────────────────────────────────────────┐      │
│    │  Layer 5: CMD ["python", "app.py"]      (Read-Only) │      │
│    ├─────────────────────────────────────────────────────┤      │
│    │  Layer 4: COPY . /app                   (Read-Only) │      │
│    ├─────────────────────────────────────────────────────┤      │
│    │  Layer 3: RUN pip install -r req.txt    (Read-Only) │      │
│    ├─────────────────────────────────────────────────────┤      │
│    │  Layer 2: RUN apt-get update && install (Read-Only) │      │
│    ├─────────────────────────────────────────────────────┤      │
│    │  Layer 1: FROM python:3.9-slim          (Read-Only) │      │
│    └─────────────────────────────────────────────────────┘      │
│                              │                                   │
│                              ▼                                   │
│         Each layer represents a Dockerfile instruction           │
│         Layers are cached for faster builds                      │
│         Layers are shared between images                         │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### Containers

A container is a runnable instance of an image. Key characteristics:

```
┌─────────────────────────────────────────────────────────────────┐
│                     CONTAINER ANATOMY                            │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│   ┌─────────────────────────────────────────────────────────┐   │
│   │              Thin Writable Layer (Container Layer)       │   │
│   │         All changes made during runtime go here          │   │
│   └─────────────────────────────────────────────────────────┘   │
│                              │                                   │
│                              ▼                                   │
│   ┌─────────────────────────────────────────────────────────┐   │
│   │                     Image Layers                         │   │
│   │                    (Read-Only)                           │   │
│   │   ┌─────────────────────────────────────────────────┐   │   │
│   │   │  Application Layer                               │   │   │
│   │   ├─────────────────────────────────────────────────┤   │   │
│   │   │  Dependencies Layer                              │   │   │
│   │   ├─────────────────────────────────────────────────┤   │   │
│   │   │  Base Image Layer                                │   │   │
│   │   └─────────────────────────────────────────────────┘   │   │
│   └─────────────────────────────────────────────────────────┘   │
│                                                                  │
│   Container = Image + Writable Layer + Configuration             │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### Container Lifecycle States

```
                    ┌─────────────────────────────────────────────────────┐
                    │              CONTAINER LIFECYCLE                     │
                    └─────────────────────────────────────────────────────┘
                                           │
                                           ▼
                    ┌──────────────────────────────────────────────────────┐
                    │                     CREATED                           │
                    │            docker create <image>                      │
                    └──────────────────────┬───────────────────────────────┘
                                           │ docker start
                                           ▼
┌───────────────┐         ┌─────────────────────────────────────────────────┐
│    PAUSED     │◄────────│                    RUNNING                      │
│ docker pause  │         │              docker run / start                 │
│               │────────►│                                                 │
│docker unpause │         └───────────┬────────────────────┬────────────────┘
└───────────────┘                     │                    │
                                      │docker stop/kill    │ process exits
                                      ▼                    ▼
                    ┌──────────────────────────────────────────────────────┐
                    │                     STOPPED                          │
                    │            (Exited / Dead state)                     │
                    └──────────────────────┬───────────────────────────────┘
                                           │ docker rm
                                           ▼
                    ┌──────────────────────────────────────────────────────┐
                    │                     REMOVED                          │
                    │               Container deleted                       │
                    └──────────────────────────────────────────────────────┘
```

### Namespaces and cgroups

Docker leverages Linux kernel features for isolation:

#### Namespaces (Isolation)

| Namespace | Isolates |
|-----------|----------|
| **PID** | Process IDs - container sees its own PID tree |
| **NET** | Network interfaces, routing tables, ports |
| **MNT** | Mount points - filesystem isolation |
| **UTS** | Hostname and domain name |
| **IPC** | Inter-process communication |
| **USER** | User and group IDs |
| **CGROUP** | Cgroup root directory |

#### cgroups (Resource Limiting)

```bash
# CPU Limits
docker run --cpus="1.5" myapp          # Limit to 1.5 CPUs
docker run --cpu-shares=512 myapp       # Relative CPU weight

# Memory Limits
docker run --memory="512m" myapp        # Hard memory limit
docker run --memory-swap="1g" myapp     # Memory + swap limit
docker run --memory-reservation="256m"  # Soft limit

# I/O Limits
docker run --blkio-weight=500 myapp     # Block I/O weight (10-1000)
docker run --device-read-bps=/dev/sda:1mb  # Read rate limit
```

---

## Installation

### Linux (Ubuntu/Debian)

```bash
# Remove old versions
sudo apt-get remove docker docker-engine docker.io containerd runc

# Install prerequisites
sudo apt-get update
sudo apt-get install -y \
    ca-certificates \
    curl \
    gnupg \
    lsb-release

# Add Docker's official GPG key
sudo mkdir -m 0755 -p /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg

# Set up the repository
echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
  $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

# Install Docker Engine
sudo apt-get update
sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

# Add user to docker group (avoid using sudo)
sudo usermod -aG docker $USER
newgrp docker

# Verify installation
docker run hello-world
```

### macOS

```bash
# Using Homebrew
brew install --cask docker

# Or download Docker Desktop from:
# https://www.docker.com/products/docker-desktop

# Start Docker Desktop application
open /Applications/Docker.app

# Verify installation
docker version
docker run hello-world
```

### Windows

1. Enable WSL 2 (Windows Subsystem for Linux)
2. Download Docker Desktop from https://www.docker.com/products/docker-desktop
3. Run installer and follow prompts
4. Start Docker Desktop
5. Verify: `docker run hello-world`

---

## Docker CLI Commands

### Image Commands

```bash
# Pull an image
docker pull nginx:latest
docker pull ubuntu:22.04
docker pull python:3.11-slim

# List images
docker images
docker image ls
docker image ls -a              # Include intermediate images

# Build an image
docker build -t myapp:1.0 .
docker build -t myapp:latest -f Dockerfile.prod .
docker build --no-cache -t myapp:1.0 .
docker build --build-arg VERSION=1.0 -t myapp .

# Tag an image
docker tag myapp:1.0 myregistry.com/myapp:1.0
docker tag myapp:1.0 myapp:production

# Push an image
docker push myregistry.com/myapp:1.0

# Remove images
docker rmi myapp:1.0
docker image rm myapp:1.0
docker image prune              # Remove dangling images
docker image prune -a           # Remove all unused images

# Inspect an image
docker image inspect nginx:latest
docker history nginx:latest     # Show layer history

# Save/Load images (for offline transfer)
docker save -o myapp.tar myapp:1.0
docker load -i myapp.tar

# Export/Import containers
docker export container_id > container.tar
docker import container.tar newimage:tag
```

### Container Commands

```bash
# Run containers
docker run nginx                          # Run in foreground
docker run -d nginx                       # Run in background (detached)
docker run -it ubuntu bash                # Interactive with TTY
docker run --name webserver nginx         # Named container
docker run -p 8080:80 nginx               # Port mapping
docker run -P nginx                       # Map all exposed ports
docker run -v /host/path:/container/path  # Bind mount
docker run -v myvolume:/data nginx        # Named volume
docker run --rm nginx                     # Remove after exit
docker run -e MY_VAR=value nginx          # Environment variable
docker run --env-file .env nginx          # Env file
docker run --network mynetwork nginx      # Specific network
docker run --restart=always nginx         # Restart policy
docker run -w /app myimage                # Working directory
docker run --user 1000:1000 myimage       # Run as specific user
docker run --read-only myimage            # Read-only filesystem

# List containers
docker ps                     # Running containers
docker ps -a                  # All containers
docker ps -q                  # Only container IDs
docker ps -s                  # Include size
docker ps --filter "status=exited"

# Container lifecycle
docker start container_name
docker stop container_name
docker restart container_name
docker pause container_name
docker unpause container_name
docker kill container_name     # Force stop
docker rm container_name       # Remove stopped container
docker rm -f container_name    # Force remove running container

# Execute commands in container
docker exec -it container_name bash
docker exec -it container_name sh
docker exec container_name ls -la
docker exec -u root container_name command  # As root user

# Container logs
docker logs container_name
docker logs -f container_name              # Follow logs
docker logs --tail 100 container_name      # Last 100 lines
docker logs --since 1h container_name      # Last hour
docker logs --timestamps container_name    # With timestamps

# Container inspection
docker inspect container_name
docker stats                               # Real-time resource usage
docker stats container_name
docker top container_name                  # Running processes
docker diff container_name                 # Filesystem changes

# Copy files
docker cp file.txt container_name:/path/
docker cp container_name:/path/file.txt ./

# Commit changes to new image
docker commit container_name newimage:tag

# Attach to running container
docker attach container_name
# Detach: Ctrl+P, Ctrl+Q

# Wait for container to exit
docker wait container_name
```

### System Commands

```bash
# System information
docker info
docker version
docker system df              # Disk usage

# Cleanup
docker system prune           # Remove unused data
docker system prune -a        # Remove all unused data
docker system prune --volumes # Include volumes
docker container prune        # Remove stopped containers
docker image prune            # Remove dangling images
docker volume prune           # Remove unused volumes
docker network prune          # Remove unused networks

# Events
docker events                 # Real-time events
docker events --filter 'type=container'
```


---

## Dockerfile Deep Dive

### Dockerfile Instructions Reference

```dockerfile
# ============================================================
#                    DOCKERFILE REFERENCE
# ============================================================

# FROM - Base image (required as first instruction)
FROM ubuntu:22.04
FROM python:3.11-slim AS builder
FROM scratch                    # Empty base image

# LABEL - Metadata
LABEL maintainer="dev@example.com"
LABEL version="1.0"
LABEL description="My application"

# ARG - Build-time variables
ARG VERSION=1.0
ARG BUILD_DATE

# ENV - Environment variables (persist in running container)
ENV APP_HOME=/app
ENV PATH="$APP_HOME/bin:$PATH"
ENV NODE_ENV=production

# WORKDIR - Set working directory
WORKDIR /app
WORKDIR $APP_HOME

# USER - Set user for subsequent instructions
USER appuser
USER 1000:1000

# COPY - Copy files from build context
COPY . /app
COPY --chown=appuser:appgroup . /app
COPY package*.json ./
COPY --from=builder /app/dist ./dist

# ADD - Copy with extra features (URL download, tar extraction)
ADD https://example.com/file.tar.gz /tmp/
ADD archive.tar.gz /app/        # Auto-extracts

# RUN - Execute commands (creates new layer)
RUN apt-get update && apt-get install -y curl
RUN pip install --no-cache-dir -r requirements.txt
RUN useradd -m appuser

# EXPOSE - Document which ports the container listens on
EXPOSE 80
EXPOSE 443/tcp
EXPOSE 8080/udp

# VOLUME - Create mount point
VOLUME /data
VOLUME ["/var/log", "/var/db"]

# CMD - Default command (can be overridden)
CMD ["python", "app.py"]
CMD ["nginx", "-g", "daemon off;"]
CMD python app.py               # Shell form

# ENTRYPOINT - Main executable (harder to override)
ENTRYPOINT ["python"]
ENTRYPOINT ["./docker-entrypoint.sh"]

# HEALTHCHECK - Container health check
HEALTHCHECK --interval=30s --timeout=10s --retries=3 \
    CMD curl -f http://localhost/ || exit 1
HEALTHCHECK NONE                # Disable inherited healthcheck

# STOPSIGNAL - Signal to stop container
STOPSIGNAL SIGTERM

# SHELL - Change default shell
SHELL ["/bin/bash", "-c"]

# ONBUILD - Trigger for child images
ONBUILD COPY . /app
ONBUILD RUN npm install
```

### Multi-Stage Builds

Multi-stage builds allow you to use multiple FROM statements to create smaller, optimized images:

```dockerfile
# ============================================================
#              MULTI-STAGE BUILD EXAMPLE
# ============================================================

# Stage 1: Build stage
FROM golang:1.21-alpine AS builder

WORKDIR /build

# Copy dependency files first (for caching)
COPY go.mod go.sum ./
RUN go mod download

# Copy source code
COPY . .

# Build the application
RUN CGO_ENABLED=0 GOOS=linux go build -a -installsuffix cgo -o app .

# Stage 2: Production stage
FROM alpine:3.18

# Install CA certificates for HTTPS
RUN apk --no-cache add ca-certificates

WORKDIR /app

# Copy only the binary from builder stage
COPY --from=builder /build/app .

# Create non-root user
RUN adduser -D -g '' appuser
USER appuser

EXPOSE 8080

ENTRYPOINT ["./app"]
```

```
Build Size Comparison:
┌─────────────────────────────────────────────────────────────┐
│                                                             │
│  Single Stage (golang:1.21):     ~1.2 GB                   │
│  Multi-Stage (alpine final):     ~15 MB                    │
│                                                             │
│  Reduction: ~98% smaller image!                            │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### Best Practices for Dockerfiles

```dockerfile
# ============================================================
#              DOCKERFILE BEST PRACTICES
# ============================================================

# 1. Use specific base image tags (not 'latest')
FROM python:3.11.4-slim-bookworm    # ✓ Good
# FROM python:latest                 # ✗ Bad

# 2. Order instructions from least to most frequently changed
# Base and system dependencies first (rarely change)
FROM python:3.11-slim
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Dependencies next (change occasionally)
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Application code last (changes frequently)
COPY . .

# 3. Combine RUN commands to reduce layers
# ✓ Good - single layer
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        curl \
        wget \
        vim && \
    rm -rf /var/lib/apt/lists/*

# ✗ Bad - multiple layers
# RUN apt-get update
# RUN apt-get install -y curl
# RUN apt-get install -y wget
# RUN rm -rf /var/lib/apt/lists/*

# 4. Use .dockerignore file
# Create .dockerignore with:
# .git
# node_modules
# *.pyc
# __pycache__
# .env
# Dockerfile
# docker-compose.yml

# 5. Don't run as root
RUN useradd -r -u 1001 appuser
USER appuser

# 6. Use COPY instead of ADD (unless you need ADD features)
COPY . /app     # ✓ Preferred
# ADD . /app    # Only when downloading URLs or extracting tars

# 7. Set appropriate labels
LABEL org.opencontainers.image.source="https://github.com/user/repo"
LABEL org.opencontainers.image.version="1.0.0"

# 8. Include health checks
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8080/health || exit 1

# 9. Use ARG for build-time only variables
ARG BUILD_VERSION
RUN echo "Building version: $BUILD_VERSION"

# 10. Document exposed ports
EXPOSE 8080
```

### Sample Dockerfiles by Language

#### Python Application

```dockerfile
FROM python:3.11-slim-bookworm

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Create non-root user
RUN useradd -r -u 1001 -g root appuser
USER appuser

# Copy application code
COPY --chown=appuser:root . .

EXPOSE 8000

CMD ["gunicorn", "--bind", "0.0.0.0:8000", "app:app"]
```

#### Node.js Application

```dockerfile
FROM node:20-alpine AS builder

WORKDIR /app

# Copy package files
COPY package*.json ./

# Install dependencies
RUN npm ci --only=production

# Copy source
COPY . .

# Build (for TypeScript/compiled apps)
RUN npm run build

# Production stage
FROM node:20-alpine

WORKDIR /app

# Copy built assets and dependencies
COPY --from=builder /app/node_modules ./node_modules
COPY --from=builder /app/dist ./dist
COPY --from=builder /app/package*.json ./

# Create non-root user
RUN addgroup -g 1001 appgroup && \
    adduser -S -u 1001 -G appgroup appuser
USER appuser

EXPOSE 3000

CMD ["node", "dist/index.js"]
```

#### Java/Spring Boot Application

```dockerfile
FROM eclipse-temurin:17-jdk-alpine AS builder

WORKDIR /app

# Copy Maven/Gradle wrapper and pom.xml
COPY mvnw pom.xml ./
COPY .mvn .mvn

# Download dependencies
RUN ./mvnw dependency:resolve

# Copy source and build
COPY src ./src
RUN ./mvnw package -DskipTests

# Production stage
FROM eclipse-temurin:17-jre-alpine

WORKDIR /app

# Copy JAR from builder
COPY --from=builder /app/target/*.jar app.jar

# Create non-root user
RUN addgroup -g 1001 appgroup && \
    adduser -S -u 1001 -G appgroup appuser
USER appuser

EXPOSE 8080

ENTRYPOINT ["java", "-jar", "app.jar"]
```


---

## Docker Networking

### Network Drivers Overview

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        DOCKER NETWORK DRIVERS                                │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                           BRIDGE (default)                           │    │
│  │  • Default network for containers                                    │    │
│  │  • Isolated network on single host                                   │    │
│  │  • Containers can communicate via IP                                 │    │
│  │  • NAT for external access                                           │    │
│  │                                                                      │    │
│  │  ┌─────────┐    ┌─────────┐    ┌─────────┐                          │    │
│  │  │Container│    │Container│    │Container│                          │    │
│  │  │    A    │    │    B    │    │    C    │                          │    │
│  │  └────┬────┘    └────┬────┘    └────┬────┘                          │    │
│  │       └──────────────┼──────────────┘                               │    │
│  │                      │                                               │    │
│  │            ┌─────────┴─────────┐                                    │    │
│  │            │   docker0 bridge  │                                    │    │
│  │            │   (172.17.0.1)    │                                    │    │
│  │            └─────────┬─────────┘                                    │    │
│  │                      │ NAT                                          │    │
│  │            ┌─────────┴─────────┐                                    │    │
│  │            │    Host Network   │                                    │    │
│  │            └───────────────────┘                                    │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                              HOST                                    │    │
│  │  • Container shares host's network stack                             │    │
│  │  • No network isolation                                              │    │
│  │  • Best performance (no NAT overhead)                                │    │
│  │  • Container uses host's IP address                                  │    │
│  │  • Ports bind directly to host                                       │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                              NONE                                    │    │
│  │  • Complete network isolation                                        │    │
│  │  • Only loopback interface                                           │    │
│  │  • Useful for batch jobs, security-sensitive containers              │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                            OVERLAY                                   │    │
│  │  • Multi-host networking                                             │    │
│  │  • Used with Docker Swarm                                            │    │
│  │  • Encrypted communication (optional)                                │    │
│  │  • VXLAN encapsulation                                               │    │
│  │                                                                      │    │
│  │    Host A              Host B              Host C                    │    │
│  │  ┌─────────┐         ┌─────────┐         ┌─────────┐                │    │
│  │  │Container│◄───────►│Container│◄───────►│Container│                │    │
│  │  └─────────┘         └─────────┘         └─────────┘                │    │
│  │       │                   │                   │                      │    │
│  │       └───────────────────┼───────────────────┘                      │    │
│  │                    Overlay Network                                   │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                            MACVLAN                                   │    │
│  │  • Assigns MAC address to container                                  │    │
│  │  • Container appears as physical device                              │    │
│  │  • Direct connection to physical network                             │    │
│  │  • Useful for legacy applications                                    │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                            IPVLAN                                    │    │
│  │  • Similar to macvlan but shares host MAC                            │    │
│  │  • L2 mode: Similar to macvlan                                       │    │
│  │  • L3 mode: Routes traffic at IP layer                               │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Network Commands

```bash
# List networks
docker network ls

# Create networks
docker network create mynetwork                    # Bridge (default)
docker network create --driver bridge mybridge
docker network create --driver host myhost
docker network create --driver overlay myoverlay
docker network create --driver macvlan \
    --subnet=192.168.1.0/24 \
    --gateway=192.168.1.1 \
    -o parent=eth0 mymacvlan

# Create with subnet configuration
docker network create --driver bridge \
    --subnet=172.28.0.0/16 \
    --ip-range=172.28.5.0/24 \
    --gateway=172.28.0.1 \
    my-custom-network

# Inspect network
docker network inspect mynetwork
docker network inspect bridge

# Connect/disconnect containers
docker network connect mynetwork container_name
docker network disconnect mynetwork container_name

# Connect with specific IP
docker network connect --ip 172.28.5.10 mynetwork container_name

# Remove network
docker network rm mynetwork
docker network prune                               # Remove unused networks

# Run container with specific network
docker run --network=mynetwork nginx
docker run --network=host nginx
docker run --network=none nginx

# Container DNS resolution (user-defined networks)
docker run --network=mynetwork --name web nginx
docker run --network=mynetwork alpine ping web    # DNS resolution works!
```

### Port Mapping

```bash
# Port mapping formats
docker run -p 8080:80 nginx                        # hostPort:containerPort
docker run -p 192.168.1.100:8080:80 nginx         # hostIP:hostPort:containerPort
docker run -p 8080:80/tcp nginx                    # Protocol specific
docker run -p 8080:80/udp nginx
docker run -p 8080:80/tcp -p 8080:80/udp nginx    # Both TCP and UDP

# Random host port
docker run -p 80 nginx                             # Maps to random high port
docker run -P nginx                                # Map all exposed ports

# View port mappings
docker port container_name
docker port container_name 80/tcp
```

### Container Communication Patterns

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    CONTAINER COMMUNICATION PATTERNS                      │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  Pattern 1: Same Custom Network (Recommended)                            │
│  ─────────────────────────────────────────────────────────────────────  │
│                                                                          │
│  docker network create app-network                                       │
│  docker run -d --name db --network app-network postgres                 │
│  docker run -d --name web --network app-network myapp                   │
│                                                                          │
│  # In web container, connect using: postgres://db:5432                   │
│  # DNS resolution handles container name → IP                           │
│                                                                          │
│  ─────────────────────────────────────────────────────────────────────  │
│                                                                          │
│  Pattern 2: Container Links (Legacy - avoid)                             │
│  ─────────────────────────────────────────────────────────────────────  │
│                                                                          │
│  docker run -d --name db postgres                                        │
│  docker run -d --name web --link db:database myapp                      │
│                                                                          │
│  # In web container: DATABASE_PORT_5432_TCP_ADDR                         │
│                                                                          │
│  ─────────────────────────────────────────────────────────────────────  │
│                                                                          │
│  Pattern 3: Host Network                                                 │
│  ─────────────────────────────────────────────────────────────────────  │
│                                                                          │
│  docker run -d --network host nginx                                      │
│                                                                          │
│  # Container uses host's network directly                                │
│  # Access via localhost:80 from host                                    │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```


---

## Docker Storage and Volumes

### Storage Types

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          DOCKER STORAGE OPTIONS                              │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│   ┌─────────────────────────────────────────────────────────────────────┐   │
│   │                         VOLUMES (Recommended)                        │   │
│   │                                                                      │   │
│   │  • Managed by Docker                                                 │   │
│   │  • Stored in /var/lib/docker/volumes/                               │   │
│   │  • Isolated from host filesystem                                     │   │
│   │  • Can be shared between containers                                  │   │
│   │  • Supports volume drivers (cloud, NFS, etc.)                        │   │
│   │                                                                      │   │
│   │  Container          Docker Area                                      │   │
│   │  ┌─────────┐       ┌─────────────────────┐                          │   │
│   │  │ /data   │──────►│ /var/lib/docker/    │                          │   │
│   │  └─────────┘       │ volumes/myvolume    │                          │   │
│   │                    └─────────────────────┘                          │   │
│   └─────────────────────────────────────────────────────────────────────┘   │
│                                                                              │
│   ┌─────────────────────────────────────────────────────────────────────┐   │
│   │                         BIND MOUNTS                                  │   │
│   │                                                                      │   │
│   │  • Maps host path directly into container                            │   │
│   │  • Full path on host filesystem                                      │   │
│   │  • Good for development (live code reload)                           │   │
│   │  • Host dependent - not portable                                     │   │
│   │                                                                      │   │
│   │  Container          Host Filesystem                                  │   │
│   │  ┌─────────┐       ┌─────────────────────┐                          │   │
│   │  │ /app    │──────►│ /home/user/project  │                          │   │
│   │  └─────────┘       └─────────────────────┘                          │   │
│   └─────────────────────────────────────────────────────────────────────┘   │
│                                                                              │
│   ┌─────────────────────────────────────────────────────────────────────┐   │
│   │                            TMPFS                                     │   │
│   │                                                                      │   │
│   │  • Stored in host memory only                                        │   │
│   │  • Never written to filesystem                                       │   │
│   │  • Lost when container stops                                         │   │
│   │  • Good for sensitive data                                           │   │
│   │                                                                      │   │
│   │  Container          Host Memory                                      │   │
│   │  ┌─────────┐       ┌─────────────────────┐                          │   │
│   │  │ /tmp    │──────►│ RAM (tmpfs)         │                          │   │
│   │  └─────────┘       └─────────────────────┘                          │   │
│   └─────────────────────────────────────────────────────────────────────┘   │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Volume Commands

```bash
# Create volume
docker volume create myvolume
docker volume create --driver local \
    --opt type=nfs \
    --opt o=addr=192.168.1.1,rw \
    --opt device=:/path/to/dir \
    nfs-volume

# List volumes
docker volume ls
docker volume ls -q                      # Only names
docker volume ls --filter "dangling=true"

# Inspect volume
docker volume inspect myvolume

# Remove volume
docker volume rm myvolume
docker volume prune                      # Remove unused volumes
docker volume prune -f                   # Force without confirmation

# Use volume with container
docker run -v myvolume:/data nginx       # Named volume
docker run -v /host/path:/container/path nginx  # Bind mount

# Mount options with --mount (more explicit)
docker run --mount type=volume,source=myvolume,target=/data nginx
docker run --mount type=bind,source=/host/path,target=/app nginx
docker run --mount type=tmpfs,destination=/tmp nginx

# Read-only mount
docker run -v myvolume:/data:ro nginx
docker run --mount type=volume,source=myvolume,target=/data,readonly nginx

# Volume from another container
docker run --volumes-from other_container nginx

# Backup a volume
docker run --rm \
    -v myvolume:/source:ro \
    -v $(pwd):/backup \
    alpine tar cvf /backup/backup.tar /source

# Restore a volume
docker run --rm \
    -v myvolume:/target \
    -v $(pwd):/backup \
    alpine tar xvf /backup/backup.tar -C /target --strip-components=1
```

### Storage Comparison Table

| Feature | Volumes | Bind Mounts | tmpfs |
|---------|---------|-------------|-------|
| **Location** | Docker managed | Anywhere on host | RAM |
| **Persistence** | Yes | Yes | No |
| **Portability** | High | Low | N/A |
| **Performance** | Good | Good | Excellent |
| **Docker CLI Management** | Yes | No | No |
| **Sharing Between Containers** | Yes | Yes | No |
| **Cloud/Remote Storage** | Via drivers | No | No |
| **Security** | Isolated | Host access | Memory-only |

### When to Use Each Storage Type

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        STORAGE DECISION FLOWCHART                            │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  Need to persist data?                                                       │
│       │                                                                      │
│       ├── NO ──► tmpfs mount                                                │
│       │          docker run --tmpfs /tmp nginx                              │
│       │                                                                      │
│       └── YES                                                               │
│            │                                                                 │
│            └── Need host file access?                                       │
│                     │                                                        │
│                     ├── YES (development, config) ──► Bind Mount            │
│                     │   docker run -v ./code:/app nginx                     │
│                     │                                                        │
│                     └── NO (database, app data) ──► Volume                  │
│                         docker run -v dbdata:/var/lib/mysql mysql           │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Docker Compose

### What is Docker Compose?

Docker Compose is a tool for defining and running multi-container Docker applications using a YAML configuration file.

### docker-compose.yml Reference

```yaml
# ============================================================
#              DOCKER COMPOSE FILE REFERENCE
# ============================================================

version: "3.9"                    # Compose file version

# Services define containers
services:

  # Web application service
  web:
    image: nginx:alpine           # Use existing image
    # OR build from Dockerfile
    build:
      context: ./app              # Build context directory
      dockerfile: Dockerfile.prod # Dockerfile name
      args:                       # Build arguments
        - NODE_ENV=production
      target: production          # Multi-stage target
      cache_from:
        - myapp:cache

    container_name: my-web        # Container name

    # Port mappings
    ports:
      - "80:80"                   # host:container
      - "443:443"
      - "127.0.0.1:8080:8080"    # Bind to specific interface

    # Environment variables
    environment:
      - NODE_ENV=production
      - DATABASE_URL=postgres://db:5432/myapp
    env_file:
      - .env
      - .env.production

    # Volume mounts
    volumes:
      - ./app:/app                # Bind mount
      - app-data:/data            # Named volume
      - /var/log/nginx            # Anonymous volume

    # Networking
    networks:
      - frontend
      - backend

    # Dependencies
    depends_on:
      - db
      - redis
    # With condition (compose v3+)
    depends_on:
      db:
        condition: service_healthy
      redis:
        condition: service_started

    # Resource limits
    deploy:
      resources:
        limits:
          cpus: '0.5'
          memory: 512M
        reservations:
          cpus: '0.25'
          memory: 256M
      replicas: 3                 # For swarm mode
      restart_policy:
        condition: on-failure
        delay: 5s
        max_attempts: 3

    # Restart policy (standalone compose)
    restart: unless-stopped       # no, always, on-failure, unless-stopped

    # Health check
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s

    # Command override
    command: ["nginx", "-g", "daemon off;"]
    entrypoint: ["/docker-entrypoint.sh"]
    working_dir: /app

    # User
    user: "1000:1000"

    # Logging
    logging:
      driver: json-file
      options:
        max-size: "10m"
        max-file: "3"

    # Extra hosts
    extra_hosts:
      - "host.docker.internal:host-gateway"

  # Database service
  db:
    image: postgres:15-alpine
    environment:
      POSTGRES_USER: ${DB_USER:-admin}
      POSTGRES_PASSWORD: ${DB_PASSWORD}
      POSTGRES_DB: myapp
    volumes:
      - postgres-data:/var/lib/postgresql/data
      - ./init.sql:/docker-entrypoint-initdb.d/init.sql
    networks:
      - backend
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U admin"]
      interval: 10s
      timeout: 5s
      retries: 5

  # Redis cache service
  redis:
    image: redis:7-alpine
    command: redis-server --appendonly yes
    volumes:
      - redis-data:/data
    networks:
      - backend

# Named volumes
volumes:
  app-data:
    driver: local
  postgres-data:
    driver: local
    driver_opts:
      type: none
      o: bind
      device: /data/postgres
  redis-data:

# Networks
networks:
  frontend:
    driver: bridge
  backend:
    driver: bridge
    internal: true              # No external access

# Secrets (Swarm mode)
secrets:
  db_password:
    file: ./secrets/db_password.txt
  api_key:
    external: true

# Configs (Swarm mode)
configs:
  nginx_config:
    file: ./nginx.conf
```

### Docker Compose Commands

```bash
# Start services
docker compose up                   # Foreground
docker compose up -d                # Detached (background)
docker compose up --build           # Force rebuild
docker compose up --scale web=3     # Scale service
docker compose up web db            # Only specific services

# Stop services
docker compose stop                 # Stop without removing
docker compose down                 # Stop and remove containers
docker compose down -v              # Also remove volumes
docker compose down --rmi all       # Also remove images

# View status
docker compose ps
docker compose ps -a                # Include stopped
docker compose top                  # Running processes

# Logs
docker compose logs
docker compose logs -f              # Follow
docker compose logs web             # Specific service
docker compose logs --tail 100      # Last 100 lines

# Execute commands
docker compose exec web bash
docker compose exec db psql -U admin
docker compose run web npm test     # Run one-off command

# Build
docker compose build
docker compose build --no-cache
docker compose build web

# Pull images
docker compose pull

# Configuration
docker compose config               # Validate and view
docker compose config --services    # List services
docker compose config --volumes     # List volumes

# Other useful commands
docker compose restart
docker compose pause
docker compose unpause
docker compose port web 80          # Show port mapping
docker compose images               # List images used
```

### Development vs Production Compose Files

```yaml
# ============================================================
#              docker-compose.yml (base)
# ============================================================
version: "3.9"

services:
  web:
    image: myapp:${TAG:-latest}
    networks:
      - app-network

  db:
    image: postgres:15-alpine
    networks:
      - app-network

networks:
  app-network:
```

```yaml
# ============================================================
#              docker-compose.override.yml (development)
# ============================================================
# Automatically loaded with docker-compose.yml
version: "3.9"

services:
  web:
    build:
      context: .
      target: development
    volumes:
      - ./src:/app/src           # Live reload
      - /app/node_modules
    ports:
      - "3000:3000"
      - "9229:9229"              # Debug port
    environment:
      - DEBUG=true
      - NODE_ENV=development

  db:
    ports:
      - "5432:5432"              # Expose for local tools
    environment:
      - POSTGRES_PASSWORD=devpassword
```

```yaml
# ============================================================
#              docker-compose.prod.yml (production)
# ============================================================
version: "3.9"

services:
  web:
    deploy:
      replicas: 3
      resources:
        limits:
          cpus: '1'
          memory: 1G
    environment:
      - NODE_ENV=production
    logging:
      driver: json-file
      options:
        max-size: "10m"

  db:
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 4G
    volumes:
      - /data/postgres:/var/lib/postgresql/data
```

```bash
# Usage
docker compose up                                    # Uses override automatically
docker compose -f docker-compose.yml -f docker-compose.prod.yml up  # Production
```

---

## Docker Swarm

### What is Docker Swarm?

Docker Swarm is Docker's native container orchestration solution for deploying and managing containers across multiple Docker hosts.

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         DOCKER SWARM ARCHITECTURE                            │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│                           ┌─────────────────┐                               │
│                           │  Swarm Manager  │                               │
│                           │    (Leader)     │                               │
│                           └────────┬────────┘                               │
│                                    │                                         │
│              ┌─────────────────────┼─────────────────────┐                  │
│              │                     │                     │                  │
│     ┌────────▼────────┐   ┌────────▼────────┐   ┌────────▼────────┐       │
│     │  Swarm Manager  │   │  Swarm Manager  │   │   Worker Node   │       │
│     │   (Follower)    │   │   (Follower)    │   │                 │       │
│     └────────┬────────┘   └────────┬────────┘   └────────┬────────┘       │
│              │                     │                     │                  │
│     ┌────────▼────────┐   ┌────────▼────────┐   ┌────────▼────────┐       │
│     │   Worker Node   │   │   Worker Node   │   │   Worker Node   │       │
│     └─────────────────┘   └─────────────────┘   └─────────────────┘       │
│                                                                              │
│   Manager Nodes:                                                            │
│   • Maintain cluster state (Raft consensus)                                 │
│   • Schedule services                                                       │
│   • Serve Swarm API                                                         │
│                                                                              │
│   Worker Nodes:                                                             │
│   • Execute containers (tasks)                                              │
│   • Report to managers                                                      │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Swarm Commands

```bash
# Initialize swarm (on first manager)
docker swarm init
docker swarm init --advertise-addr 192.168.1.100

# Get join tokens
docker swarm join-token manager
docker swarm join-token worker

# Join as worker
docker swarm join --token SWMTKN-xxx 192.168.1.100:2377

# Join as manager
docker swarm join --token SWMTKN-xxx-mgr 192.168.1.100:2377

# Leave swarm
docker swarm leave
docker swarm leave --force    # For managers

# Node management
docker node ls
docker node inspect node-id
docker node promote node-id   # Worker → Manager
docker node demote node-id    # Manager → Worker
docker node rm node-id
docker node update --availability drain node-id  # Prepare for maintenance

# Service management
docker service create --name web -p 80:80 --replicas 3 nginx
docker service ls
docker service ps web
docker service inspect web
docker service logs web
docker service scale web=5
docker service update --image nginx:1.25 web
docker service rm web

# Stack deployment (from compose file)
docker stack deploy -c docker-compose.yml mystack
docker stack ls
docker stack ps mystack
docker stack services mystack
docker stack rm mystack

# Secrets management
echo "password123" | docker secret create db_password -
docker secret ls
docker secret inspect db_password
docker secret rm db_password

# Config management
docker config create nginx.conf ./nginx.conf
docker config ls
docker config rm nginx.conf
```

### Service Definition Example

```yaml
# docker-compose.yml for Swarm deployment
version: "3.9"

services:
  web:
    image: myapp:latest
    deploy:
      mode: replicated           # or 'global' for one per node
      replicas: 6
      placement:
        constraints:
          - node.role == worker
          - node.labels.zone == us-east
        preferences:
          - spread: node.labels.datacenter
      update_config:
        parallelism: 2           # Update 2 at a time
        delay: 10s
        failure_action: rollback
        order: start-first       # or 'stop-first'
      rollback_config:
        parallelism: 1
        delay: 10s
      restart_policy:
        condition: on-failure
        delay: 5s
        max_attempts: 3
        window: 120s
      resources:
        limits:
          cpus: '0.5'
          memory: 256M
        reservations:
          cpus: '0.25'
          memory: 128M
    ports:
      - target: 80
        published: 80
        mode: ingress            # or 'host'
    networks:
      - frontend
    secrets:
      - db_password
    configs:
      - source: nginx_config
        target: /etc/nginx/nginx.conf

secrets:
  db_password:
    external: true

configs:
  nginx_config:
    file: ./nginx.conf

networks:
  frontend:
    driver: overlay
```

---

## Security Best Practices

### Image Security

```bash
# 1. Use official/verified images
docker pull nginx                      # Official
docker pull bitnami/nginx             # Verified publisher

# 2. Scan images for vulnerabilities
docker scout quickview nginx:latest
docker scout cves nginx:latest

# 3. Use specific tags (not 'latest')
FROM python:3.11.4-slim-bookworm      # ✓ Good
# FROM python:latest                   # ✗ Bad

# 4. Use minimal base images
FROM alpine:3.18                       # ~5 MB
FROM debian:bookworm-slim             # ~80 MB
FROM scratch                          # 0 B (for static binaries)
FROM gcr.io/distroless/base           # Distroless

# 5. Sign and verify images
docker trust sign myregistry/myimage:tag
docker trust inspect --pretty myregistry/myimage
```

### Runtime Security

```dockerfile
# ============================================================
#              SECURITY-FOCUSED DOCKERFILE
# ============================================================

FROM python:3.11-slim-bookworm

# 1. Create non-root user
RUN groupadd -r appgroup && \
    useradd -r -g appgroup -d /app -s /sbin/nologin appuser

# 2. Set restrictive permissions
WORKDIR /app
COPY --chown=appuser:appgroup . .
RUN chmod -R 550 /app

# 3. Remove unnecessary packages
RUN apt-get purge -y --auto-remove && \
    rm -rf /var/lib/apt/lists/*

# 4. Use non-root user
USER appuser

# 5. Run read-only when possible
# docker run --read-only myimage

# 6. Drop capabilities
# docker run --cap-drop=ALL --cap-add=NET_BIND_SERVICE myimage

# 7. No new privileges
# docker run --security-opt=no-new-privileges myimage
```

### Security Checklist

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                      DOCKER SECURITY CHECKLIST                               │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  IMAGE SECURITY:                                                            │
│  □ Use official or verified images                                          │
│  □ Scan images for vulnerabilities                                          │
│  □ Use specific version tags                                                │
│  □ Use minimal base images                                                  │
│  □ Sign images with Docker Content Trust                                    │
│  □ Don't store secrets in images                                            │
│  □ Use multi-stage builds                                                   │
│                                                                              │
│  RUNTIME SECURITY:                                                          │
│  □ Run as non-root user                                                     │
│  □ Use read-only filesystem                                                 │
│  □ Drop unnecessary capabilities                                            │
│  □ Use --security-opt=no-new-privileges                                     │
│  □ Limit resources (CPU, memory)                                            │
│  □ Use user namespaces                                                      │
│  □ Don't run with --privileged                                              │
│                                                                              │
│  NETWORK SECURITY:                                                          │
│  □ Use custom bridge networks                                               │
│  □ Don't expose unnecessary ports                                           │
│  □ Use internal networks when possible                                      │
│  □ Enable encrypted overlay networks                                        │
│                                                                              │
│  HOST SECURITY:                                                             │
│  □ Keep Docker updated                                                      │
│  □ Limit Docker socket access                                               │
│  □ Use TLS for remote Docker API                                            │
│  □ Enable audit logging                                                     │
│  □ Use AppArmor/SELinux profiles                                            │
│                                                                              │
│  SECRETS MANAGEMENT:                                                        │
│  □ Use Docker secrets (Swarm) or external vault                             │
│  □ Never hardcode secrets in images                                         │
│  □ Use environment variables carefully                                      │
│  □ Mount secrets as read-only                                               │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Secure Container Commands

```bash
# Run with security options
docker run -d \
    --name secure-app \
    --user 1000:1000 \
    --read-only \
    --cap-drop=ALL \
    --cap-add=NET_BIND_SERVICE \
    --security-opt=no-new-privileges:true \
    --security-opt apparmor=docker-default \
    --pids-limit 100 \
    --memory 256m \
    --cpus 0.5 \
    --tmpfs /tmp:rw,noexec,nosuid,size=64m \
    --network my-isolated-network \
    myimage:tag

# Enable Docker Content Trust
export DOCKER_CONTENT_TRUST=1
docker pull nginx:latest          # Will verify signature

# Audit container runtime
docker inspect --format '{{.HostConfig.Privileged}}' container
docker inspect --format '{{.Config.User}}' container
```

---

## Performance Optimization

### Build Optimization

```dockerfile
# ============================================================
#              BUILD PERFORMANCE OPTIMIZATION
# ============================================================

# 1. ORDER: Least changing → Most changing
FROM python:3.11-slim

# System deps (rarely change)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential && \
    rm -rf /var/lib/apt/lists/*

# App deps (change occasionally)
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# App code (changes frequently)
COPY . .

CMD ["python", "app.py"]
```

```bash
# 2. Use BuildKit for faster builds
export DOCKER_BUILDKIT=1
docker build -t myapp .

# 3. Use cache mounts for package managers
# syntax=docker/dockerfile:1.4
FROM python:3.11-slim
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install -r requirements.txt

# 4. Parallel builds for multi-platform
docker buildx build --platform linux/amd64,linux/arm64 -t myapp .

# 5. Build specific stage only
docker build --target builder -t myapp:build-stage .
```

### Runtime Optimization

```bash
# CPU Optimization
docker run --cpus="2" myapp                 # Limit to 2 CPUs
docker run --cpu-shares=1024 myapp          # Relative weight
docker run --cpuset-cpus="0,1" myapp        # Pin to specific CPUs

# Memory Optimization
docker run --memory="1g" myapp              # Hard limit
docker run --memory-reservation="512m" myapp # Soft limit
docker run --memory-swap="2g" myapp         # Memory + swap

# I/O Optimization
docker run --blkio-weight=500 myapp         # Block I/O weight
docker run --device-read-bps=/dev/sda:100mb myapp
docker run --device-write-bps=/dev/sda:100mb myapp

# Network Optimization
docker run --network host myapp             # No NAT overhead

# Storage Optimization
docker run --storage-opt size=10G myapp     # Limit writable layer
```

### Image Size Optimization

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                      IMAGE SIZE REDUCTION STRATEGIES                         │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  1. Choose minimal base images:                                             │
│     alpine:3.18         ~5 MB                                               │
│     debian:slim         ~80 MB                                              │
│     ubuntu:22.04        ~77 MB                                              │
│     scratch             0 B                                                  │
│                                                                              │
│  2. Multi-stage builds:                                                     │
│     Build deps in builder stage, copy only artifacts                        │
│                                                                              │
│  3. Combine RUN commands:                                                   │
│     RUN apt-get update && apt-get install -y pkg && rm -rf /var/lib/apt    │
│                                                                              │
│  4. Remove unnecessary files:                                               │
│     - Package manager caches                                                 │
│     - Development dependencies                                               │
│     - Documentation                                                          │
│     - Test files                                                             │
│                                                                              │
│  5. Use .dockerignore:                                                      │
│     .git/                                                                    │
│     node_modules/                                                            │
│     *.md                                                                     │
│     tests/                                                                   │
│                                                                              │
│  6. Squash layers (experimental):                                           │
│     docker build --squash -t myapp .                                        │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Example: Optimized vs Unoptimized

```dockerfile
# ============================================================
#              UNOPTIMIZED (Don't do this!)
# ============================================================
FROM ubuntu:22.04
RUN apt-get update
RUN apt-get install -y python3 python3-pip
RUN pip install flask
COPY . /app
WORKDIR /app
CMD ["python3", "app.py"]
# Result: ~500+ MB

# ============================================================
#              OPTIMIZED (Do this!)
# ============================================================
FROM python:3.11-alpine
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY app.py .
CMD ["python", "app.py"]
# Result: ~50 MB
```

---

## Troubleshooting

### Common Issues and Solutions

```bash
# ============================================================
#              DOCKER TROUBLESHOOTING GUIDE
# ============================================================

# Container won't start
docker logs container_name              # Check logs
docker inspect container_name           # Check config
docker events --since '10m'             # Recent events

# Permission denied
docker exec -u root container_name ls   # Check as root
# Fix: Ensure correct ownership in Dockerfile
# COPY --chown=appuser:appgroup . .

# Out of disk space
docker system df                        # Check disk usage
docker system prune -a                  # Clean everything
docker volume prune                     # Clean volumes
docker image prune -a                   # Clean images

# Container exits immediately
docker run -it myimage sh               # Run interactively
docker logs container_name              # Check exit logs
# Fix: Ensure proper CMD or ENTRYPOINT

# Network connectivity issues
docker exec container_name ping google.com
docker exec container_name nslookup other-container
docker network inspect bridge
# Fix: Check network configuration

# Port already in use
docker ps -a                            # Check what's using port
sudo lsof -i :8080                      # Check host port usage
# Fix: Use different port or stop conflicting container

# Build cache issues
docker build --no-cache -t myapp .      # Rebuild without cache
docker builder prune                    # Clear build cache

# "Cannot connect to Docker daemon"
sudo systemctl status docker            # Check Docker status
sudo systemctl start docker             # Start Docker
sudo usermod -aG docker $USER           # Add user to docker group
# Then logout and login
```

### Debugging Containers

```bash
# ============================================================
#              DEBUGGING TECHNIQUES
# ============================================================

# 1. Execute commands in running container
docker exec -it container_name bash
docker exec -it container_name sh
docker exec container_name cat /etc/hosts
docker exec container_name env

# 2. View processes
docker top container_name
docker exec container_name ps aux

# 3. Resource usage
docker stats container_name
docker stats --no-stream               # One-time snapshot

# 4. Inspect container
docker inspect container_name
docker inspect -f '{{.State.Status}}' container_name
docker inspect -f '{{.NetworkSettings.IPAddress}}' container_name
docker inspect -f '{{json .Config.Env}}' container_name | jq

# 5. View filesystem changes
docker diff container_name

# 6. Copy files for inspection
docker cp container_name:/var/log/app.log ./app.log

# 7. Create debug container in same network
docker run --rm -it --network container:target_container nicolaka/netshoot

# 8. Override entrypoint for debugging
docker run --rm -it --entrypoint sh myimage

# 9. Health check status
docker inspect --format '{{json .State.Health}}' container_name | jq

# 10. Container events
docker events --filter 'container=container_name'
```

### Useful Debugging Images

```bash
# Network debugging
docker run --rm -it nicolaka/netshoot
# Contains: curl, ping, dig, nslookup, tcpdump, iptables, etc.

# General debugging
docker run --rm -it busybox
docker run --rm -it alpine sh

# Process debugging
docker run --rm -it --pid=container:target_container alpine ps aux
```

---

## Real-World Use Cases

### 1. Development Environment

```yaml
# docker-compose.yml for local development
version: "3.9"

services:
  app:
    build:
      context: .
      target: development
    volumes:
      - .:/app
      - /app/node_modules
    ports:
      - "3000:3000"
      - "9229:9229"    # Debugging
    environment:
      - NODE_ENV=development
      - DEBUG=app:*
    depends_on:
      - db
      - redis

  db:
    image: postgres:15-alpine
    environment:
      POSTGRES_USER: dev
      POSTGRES_PASSWORD: dev
      POSTGRES_DB: myapp_dev
    volumes:
      - postgres-data:/var/lib/postgresql/data
    ports:
      - "5432:5432"

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"

  mailhog:
    image: mailhog/mailhog
    ports:
      - "1025:1025"
      - "8025:8025"    # Web UI

volumes:
  postgres-data:
```

### 2. CI/CD Pipeline Integration

```yaml
# GitHub Actions example
name: Build and Push

on:
  push:
    branches: [main]

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Set up Docker Buildx
        uses: docker/setup-buildx-action@v3

      - name: Login to Registry
        uses: docker/login-action@v3
        with:
          registry: ghcr.io
          username: ${{ github.actor }}
          password: ${{ secrets.GITHUB_TOKEN }}

      - name: Build and Push
        uses: docker/build-push-action@v5
        with:
          context: .
          push: true
          tags: ghcr.io/${{ github.repository }}:${{ github.sha }}
          cache-from: type=gha
          cache-to: type=gha,mode=max
```

### 3. Microservices Architecture

```yaml
# docker-compose.yml for microservices
version: "3.9"

services:
  gateway:
    image: nginx:alpine
    ports:
      - "80:80"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf:ro
    depends_on:
      - api
      - frontend

  frontend:
    build: ./frontend
    environment:
      - API_URL=http://gateway/api

  api:
    build: ./api
    environment:
      - DATABASE_URL=postgres://db:5432/myapp
      - REDIS_URL=redis://redis:6379
    depends_on:
      - db
      - redis

  worker:
    build: ./worker
    environment:
      - REDIS_URL=redis://redis:6379
    depends_on:
      - redis

  db:
    image: postgres:15-alpine
    volumes:
      - postgres-data:/var/lib/postgresql/data

  redis:
    image: redis:7-alpine
    volumes:
      - redis-data:/data

volumes:
  postgres-data:
  redis-data:
```

### 4. Database Administration

```bash
# PostgreSQL backup
docker exec -t postgres pg_dump -U admin mydb > backup.sql

# PostgreSQL restore
docker exec -i postgres psql -U admin mydb < backup.sql

# MongoDB backup
docker exec mongodb mongodump --out /backup
docker cp mongodb:/backup ./mongo-backup

# MySQL/MariaDB backup
docker exec mysql mysqldump -u root -p mydb > backup.sql

# Interactive database access
docker exec -it postgres psql -U admin -d mydb
docker exec -it mongodb mongosh
docker exec -it mysql mysql -u root -p
docker exec -it redis redis-cli
```

### 5. Monitoring Stack

```yaml
# docker-compose.monitoring.yml
version: "3.9"

services:
  prometheus:
    image: prom/prometheus:latest
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml
      - prometheus-data:/prometheus
    ports:
      - "9090:9090"
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'
      - '--storage.tsdb.retention.time=15d'

  grafana:
    image: grafana/grafana:latest
    volumes:
      - grafana-data:/var/lib/grafana
    ports:
      - "3000:3000"
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=admin

  node-exporter:
    image: prom/node-exporter:latest
    ports:
      - "9100:9100"
    volumes:
      - /proc:/host/proc:ro
      - /sys:/host/sys:ro
      - /:/rootfs:ro
    command:
      - '--path.procfs=/host/proc'
      - '--path.sysfs=/host/sys'

  cadvisor:
    image: gcr.io/cadvisor/cadvisor:latest
    ports:
      - "8080:8080"
    volumes:
      - /:/rootfs:ro
      - /var/run:/var/run:ro
      - /sys:/sys:ro
      - /var/lib/docker:/var/lib/docker:ro

volumes:
  prometheus-data:
  grafana-data:
```

---

## Quick Reference Card

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        DOCKER QUICK REFERENCE                                │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  IMAGES                          CONTAINERS                                  │
│  ───────                         ──────────                                  │
│  docker pull <image>             docker run -d -p 80:80 <image>             │
│  docker build -t <name> .        docker ps / docker ps -a                   │
│  docker images                   docker start/stop/restart <id>             │
│  docker rmi <image>              docker rm <id>                             │
│  docker tag <src> <dest>         docker logs -f <id>                        │
│  docker push <image>             docker exec -it <id> bash                  │
│                                                                              │
│  VOLUMES                         NETWORKS                                    │
│  ───────                         ────────                                    │
│  docker volume create <name>     docker network create <name>               │
│  docker volume ls                docker network ls                          │
│  docker volume rm <name>         docker network connect <net> <container>   │
│  -v <name>:/path                 --network <name>                           │
│  -v /host:/container             docker network inspect <name>              │
│                                                                              │
│  COMPOSE                         CLEANUP                                     │
│  ───────                         ───────                                     │
│  docker compose up -d            docker system prune -a                     │
│  docker compose down             docker container prune                     │
│  docker compose logs -f          docker image prune -a                      │
│  docker compose exec <svc> bash  docker volume prune                        │
│  docker compose build            docker network prune                       │
│                                                                              │
│  DEBUGGING                       INFORMATION                                 │
│  ─────────                       ───────────                                 │
│  docker logs <id>                docker inspect <id>                        │
│  docker exec -it <id> sh         docker stats                               │
│  docker top <id>                 docker system df                           │
│  docker diff <id>                docker version                             │
│  docker events                   docker info                                │
│                                                                              │
│  COMMON FLAGS                                                                │
│  ────────────                                                                │
│  -d          Detached mode (background)                                     │
│  -it         Interactive with TTY                                           │
│  -p 80:80    Port mapping (host:container)                                  │
│  -v /h:/c    Volume mount                                                   │
│  -e VAR=val  Environment variable                                           │
│  --rm        Remove container on exit                                       │
│  --name      Container name                                                 │
│  --network   Network name                                                   │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Additional Resources

### Official Documentation
- [Docker Docs](https://docs.docker.com/)
- [Docker Hub](https://hub.docker.com/)
- [Docker Compose Specification](https://docs.docker.com/compose/compose-file/)

### Best Practices Guides
- [Dockerfile Best Practices](https://docs.docker.com/develop/develop-images/dockerfile_best-practices/)
- [Docker Security Best Practices](https://docs.docker.com/engine/security/)

### Tools and Extensions
- **Docker Desktop**: GUI for Docker on Mac/Windows
- **Portainer**: Web-based Docker management
- **Lazydocker**: Terminal UI for Docker
- **dive**: Tool for exploring Docker image layers
- **hadolint**: Dockerfile linter

---

*Document created: 2026-02-20*
*Last updated: 2026-02-20*
