# Docker/Colima Memory: Comprehensive Guide

## Table of Contents
1. [Memory Types Overview](#memory-types-overview)
2. [Container Memory Limits](#container-memory-limits)
3. [Memory Swap](#memory-swap)
4. [Shared Memory (shm)](#shared-memory-shm)
5. [Memory Inside Container](#memory-inside-container)
6. [Memory Metrics and Monitoring](#memory-metrics-and-monitoring)
7. [OOM Killer](#oom-killer)
8. [Best Practices](#best-practices)

---

## Memory Types Overview

When working with Docker/Colima containers, there are several layers of memory to understand:

```
┌─────────────────────────────────────────────────────────────┐
│ Host Machine (macOS)                                        │
│ ┌─────────────────────────────────────────────────────────┐ │
│ │ Colima VM (Virtual Machine)                             │ │
│ │ ┌─────────────────────────────────────────────────────┐ │ │
│ │ │ Docker Container                                    │ │ │
│ │ │                                                     │ │ │
│ │ │  - Container Memory Limit (--memory)               │ │ │
│ │ │  - Container Swap (--memory-swap)                  │ │ │
│ │ │  - Shared Memory (--shm-size)                      │ │ │
│ │ │  - Process Memory (RSS, VSZ)                       │ │ │
│ │ └─────────────────────────────────────────────────────┘ │ │
│ └─────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

---

## Container Memory Limits

### 1. `--memory` (or `-m`)

**What it is**: The maximum amount of RAM the container can use.

**Purpose**:
- Prevents a single container from consuming all host memory
- Protects other containers and the host system
- Triggers OOM killer if exceeded

**Syntax**:
```bash
docker run --memory="6g" ...    # 6 gigabytes
docker run --memory="512m" ...  # 512 megabytes
docker run -m 2g ...            # Short form
```

**Example**:
```bash
# Container can use up to 6GB of RAM
docker run --memory="6g" --name mycontainer ubuntu
```

**What happens when limit is reached**:
1. Container processes cannot allocate more memory
2. OOM (Out of Memory) killer is invoked
3. OOM killer selects and kills processes to free memory
4. Container may crash or become unstable

**How to check**:
```bash
# View memory limit
docker inspect mycontainer | grep '"Memory"'

# Output: "Memory": 6442450944  (bytes = 6GB)
```

**Real-world analogy**:
Think of it as a bucket. The `--memory` flag sets the bucket size. Once full, water (memory) overflows and the OOM killer starts bailing out water by killing processes.

---

## Memory Swap

### 2. `--memory-swap`

**What it is**: The total amount of memory + swap the container can use.

**Important**: `--memory-swap` is NOT just swap space. It's the TOTAL of RAM + Swap.

**Formula**:
```
Actual Swap Available = memory-swap - memory
```

**Examples**:

```bash
# Example 1: 6GB RAM, 2GB Swap
docker run --memory="6g" --memory-swap="8g" ...
# RAM: 6GB
# Swap: 8GB - 6GB = 2GB

# Example 2: 4GB RAM, 4GB Swap
docker run --memory="4g" --memory-swap="8g" ...
# RAM: 4GB
# Swap: 8GB - 4GB = 4GB

# Example 3: No swap (memory-swap = memory)
docker run --memory="6g" --memory-swap="6g" ...
# RAM: 6GB
# Swap: 6GB - 6GB = 0GB

# Example 4: Unlimited swap
docker run --memory="6g" --memory-swap="-1" ...
# RAM: 6GB
# Swap: Unlimited (not recommended)
```

**What is Swap?**:
- Swap is disk space used as "overflow" memory
- When RAM is full, inactive pages are moved to swap
- Swap is MUCH slower than RAM (100-1000x slower)
- Too much swapping = "thrashing" = very slow system

**When to use swap**:
- ✅ Safety buffer for memory spikes
- ✅ Prevent OOM kills during temporary high usage
- ❌ NOT a substitute for insufficient RAM
- ❌ Constant swapping = performance disaster

**Recommended ratio**:
```
RAM:Swap ratio recommendations:
- 8GB RAM  → 2-4GB swap  (25-50% of RAM)
- 4GB RAM  → 2-4GB swap  (50-100% of RAM)
- 2GB RAM  → 2GB swap    (100% of RAM)
```

---

## Shared Memory (shm)

### 3. `--shm-size`

**What it is**: Size of `/dev/shm` - a tmpfs (RAM-based filesystem) for inter-process communication.

**Purpose**:
- Fast shared memory between processes
- Used for IPC (Inter-Process Communication)
- Stored in RAM, not on disk
- Much faster than disk-based IPC

**Default**: 64MB (often too small!)

**Syntax**:
```bash
docker run --shm-size="1g" ...    # 1 gigabyte
docker run --shm-size="512m" ...  # 512 megabytes
```

**Who uses shared memory?**:

1. **Node.js / V8 Engine**:
   - Used for large objects and buffers
   - Chrome/Chromium-based tools (Puppeteer, Playwright)
   - Electron apps

2. **Databases**:
   - PostgreSQL (shared buffers)
   - MySQL/MariaDB (InnoDB buffer pool)
   - Redis (memory snapshots)

3. **Scientific Computing**:
   - NumPy, SciPy (large arrays)
   - TensorFlow, PyTorch (model weights)
   - Parallel processing libraries

4. **Browsers/Headless Browsers**:
   - Chrome, Firefox
   - Selenium, Puppeteer
   - Playwright

**Common Issues with Small shm**:

```bash
# Error with 64MB default shm:
ERROR: Failed to create shared memory segment
ERROR: Bus error (core dumped)
ERROR: Cannot allocate memory
```

**Example - Auggie/Node.js**:
```bash
# Auggie is a Node.js app that may use:
# - V8 heap for JavaScript objects
# - Shared memory for large buffers
# - IPC with LSP servers (clangd, etc.)

# Too small (default):
--shm-size="64m"   # ❌ May cause crashes

# Better:
--shm-size="512m"  # ✅ Good for most apps

# Best for development:
--shm-size="1g"    # ✅ Plenty of headroom
```

**How to check shm usage**:
```bash
# Inside container:
df -h /dev/shm

# Output:
Filesystem      Size  Used Avail Use% Mounted on
shm             1.0G  128M  896M  13% /dev/shm
```

**Important Notes**:
- Shared memory counts AGAINST your `--memory` limit
- If shm-size=1GB and you use 500MB in /dev/shm, that's 500MB less available for processes
- Unused shm doesn't consume RAM (it's allocated on-demand)

---

## Memory Inside Container

### 4. Understanding `free -h` Output

When you run `free -h` inside a container, you see:

```bash
$ docker exec dev-arm64 free -h
               total        used        free      shared  buff/cache   available
Mem:           7.7Gi       373Mi       6.9Gi       0.0Ki       624Mi       7.4Gi
Swap:             0B          0B          0B
```

**Let's break down each column**:

#### `total` - Total Memory
- **What**: Total RAM allocated to the container
- **In example**: 7.7Gi
- **Note**: Slightly less than `--memory` limit due to kernel overhead
- **Formula**: `total ≈ --memory limit - kernel overhead`

#### `used` - Used Memory
- **What**: Memory currently in use by processes
- **In example**: 373Mi (373 megabytes)
- **Includes**:
  - Process memory (RSS - Resident Set Size)
  - Kernel memory
  - Slab caches
- **Formula**: `used = total - free - buff/cache`

#### `free` - Free Memory
- **What**: Completely unused memory
- **In example**: 6.9Gi
- **Note**: This is "wasted" memory from Linux's perspective
- **Linux philosophy**: "Free memory is wasted memory"
- **Why low free is OK**: Linux uses "free" memory for caching

#### `shared` - Shared Memory
- **What**: Memory used by tmpfs (like /dev/shm)
- **In example**: 0.0Ki (nothing in /dev/shm currently)
- **Max**: Limited by `--shm-size` flag
- **Check**: `df -h /dev/shm`

#### `buff/cache` - Buffers and Cache
- **What**: Memory used for disk caching and buffers
- **In example**: 624Mi
- **Purpose**: Speed up disk I/O by caching frequently accessed data
- **Important**: This memory is "reclaimable"
- **Behavior**: Automatically freed when processes need it

**Buffers vs Cache**:
```
Buffers: Metadata about disk blocks (inodes, directory entries)
Cache:   Actual file contents cached in RAM
```

#### `available` - Available Memory
- **What**: Memory available for starting new applications
- **In example**: 7.4Gi
- **Formula**: `available = free + reclaimable(buff/cache)`
- **Most important metric**: This is what you should monitor!
- **Why**: Shows how much memory you can actually use

**Key Insight**:
```
available > free

Because:
available = free + (most of buff/cache)
```

### Memory States Explained

```
┌─────────────────────────────────────────────────────────┐
│ Total Memory: 7.7Gi                                     │
├─────────────────────────────────────────────────────────┤
│ Used (373Mi)          │ Actually used by processes      │
├─────────────────────────────────────────────────────────┤
│ Buff/Cache (624Mi)    │ Disk cache (reclaimable)        │
├─────────────────────────────────────────────────────────┤
│ Free (6.9Gi)          │ Completely unused               │
└─────────────────────────────────────────────────────────┘

Available = Free + (most of Buff/Cache) = 7.4Gi
```

### Process Memory (ps aux)

```bash
$ docker exec dev-arm64 ps aux --sort=-%mem | head -5
USER       PID %CPU %MEM    VSZ   RSS TTY      STAT START   TIME COMMAND
root       123  0.3 23.0 941688 462292 ?       Ssl  17:10   0:01 clangd
root       456 20.2 22.1 18892188 444972 pts/2 Sl+ 17:18   0:17 node auggie
```

#### `VSZ` - Virtual Memory Size
- **What**: Total virtual memory allocated to the process
- **Includes**:
  - Actual RAM used
  - Shared libraries
  - Swapped memory
  - Memory-mapped files
  - Allocated but not used memory
- **Example**: clangd VSZ = 941688 KB ≈ 920 MB
- **Note**: VSZ is often MUCH larger than actual RAM usage
- **Why**: Modern apps allocate virtual memory optimistically

#### `RSS` - Resident Set Size
- **What**: Actual physical RAM used by the process
- **This is the "real" memory usage**
- **Example**: clangd RSS = 462292 KB ≈ 451 MB
- **Includes**:
  - Process code
  - Process data
  - Process stack
  - Shared libraries (counted for each process)
- **Note**: RSS can be misleading for shared libraries

#### `%MEM` - Memory Percentage
- **What**: Percentage of total container memory used
- **Formula**: `%MEM = (RSS / total_memory) * 100`
- **Example**: clangd %MEM = 23.0% = (462292 KB / 2GB) * 100

**Memory Hierarchy**:
```
VSZ (Virtual)     ≥  RSS (Physical)  ≥  Shared
920 MB                451 MB             varies

VSZ: What the process thinks it has
RSS: What the process actually uses in RAM
```

---


## Memory Metrics and Monitoring

### 5. `docker stats` Output

```bash
$ docker stats dev-arm64 --no-stream
CONTAINER ID   NAME        CPU %     MEM USAGE / LIMIT   MEM %
33f8006dcf14   dev-arm64   0.00%     179.4MiB / 6GiB     2.92%
```

#### `MEM USAGE` - Current Memory Usage
- **What**: Total memory used by the container
- **In example**: 179.4 MiB
- **Includes**: All process RSS + kernel memory + cache
- **Roughly equals**: `used` from `free -h`

#### `LIMIT` - Memory Limit
- **What**: The `--memory` limit you set
- **In example**: 6 GiB
- **This is the hard cap**: Container cannot exceed this

#### `MEM %` - Memory Percentage
- **What**: Percentage of limit used
- **Formula**: `MEM % = (MEM USAGE / LIMIT) * 100`
- **In example**: 2.92% = (179.4 MiB / 6 GiB) * 100
- **Healthy range**:
  - < 50%: Excellent ✅
  - 50-70%: Good ✅
  - 70-85%: Warning ⚠️
  - 85-95%: Critical ❌
  - > 95%: OOM imminent ❌❌

### 6. `docker inspect` Memory Settings

```bash
$ docker inspect dev-arm64 | grep -E '"Memory"|"MemorySwap"|"ShmSize"'
"Memory": 6442450944,
"MemorySwap": 8589934592,
"ShmSize": 1073741824,
```

**Values are in bytes**:
```
Memory:     6442450944 bytes  = 6 GB
MemorySwap: 8589934592 bytes  = 8 GB
ShmSize:    1073741824 bytes  = 1 GB
```

**Conversion**:
```
1 KB = 1024 bytes
1 MB = 1024 KB = 1,048,576 bytes
1 GB = 1024 MB = 1,073,741,824 bytes

To convert bytes to GB:
GB = bytes / 1073741824
```

---

## OOM Killer

### 7. Out of Memory Killer

**What is OOM Killer?**:
- Linux kernel mechanism that kills processes when memory is exhausted
- Prevents entire system from crashing
- Selects "best" process to kill based on heuristics

**When does it trigger?**:
```
Container memory usage ≥ --memory limit
AND
No more memory can be freed from cache
```

**How it selects victims**:
1. Calculates OOM score for each process
2. Higher score = more likely to be killed
3. Factors:
   - Memory usage (more = higher score)
   - Process age (newer = higher score)
   - Root processes (lower score)
   - OOM adjust value (manual tuning)

**OOM Score Example**:
```bash
# Inside container, check OOM scores:
$ cat /proc/*/oom_score | sort -rn | head -5

# Or with process names:
$ for pid in $(ps -eo pid --no-headers); do
    echo "$(cat /proc/$pid/oom_score 2>/dev/null || echo 0) $(cat /proc/$pid/comm 2>/dev/null)";
  done | sort -rn | head -5

# Output:
850 node        # Auggie - high memory usage
720 clangd      # LSP server - high memory usage
120 bash        # Shell - low memory usage
```

**Detecting OOM Kills**:

```bash
# Check if container was OOM killed:
$ docker inspect dev-arm64 | grep OOMKilled
"OOMKilled": true,   # ❌ Container was killed!
"OOMKilled": false,  # ✅ Container is healthy

# Check system logs:
$ dmesg | grep -i oom
[12345.678] Out of memory: Kill process 1234 (node) score 850

# Check container logs:
$ docker logs dev-arm64 | grep -i "killed\|memory"
```

**Preventing OOM Kills**:

1. **Increase memory limit**:
```bash
docker run --memory="8g" ...  # More RAM
```

2. **Add swap space**:
```bash
docker run --memory="6g" --memory-swap="8g" ...  # 2GB swap buffer
```

3. **Optimize application**:
```bash
# Limit Node.js heap:
export NODE_OPTIONS="--max-old-space-size=1024"  # 1GB max

# Limit Java heap:
export JAVA_OPTS="-Xmx2g -Xms512m"
```

4. **Monitor and alert**:
```bash
# Alert when memory > 80%
docker stats --format "{{.MemPerc}}" dev-arm64
```

**OOM Killer vs Memory Limit**:
```
Without --memory limit:
  Container can use ALL host memory → Host crashes ❌

With --memory limit:
  Container limited → OOM kills container processes → Host survives ✅
```

---

## Best Practices

### 8. Memory Configuration Guidelines

#### For Development Containers (like dev-arm64):

```bash
# Recommended settings:
docker run \
  --memory="6g" \          # 6GB RAM (generous for dev work)
  --memory-swap="8g" \     # 2GB swap (safety buffer)
  --shm-size="1g" \        # 1GB shared memory (for Node.js, browsers)
  --cpus="4" \             # 4 CPUs
  ...
```

**Rationale**:
- **6GB RAM**: Enough for IDE, LSP servers, compilers, debuggers
- **2GB Swap**: Safety net for memory spikes
- **1GB shm**: Handles Node.js, Electron apps, headless browsers
- **4 CPUs**: Parallel compilation, multi-threaded tools

#### For Production Containers:

```bash
# Minimal, optimized settings:
docker run \
  --memory="512m" \        # Tight limit
  --memory-swap="512m" \   # No swap (fail fast)
  --shm-size="64m" \       # Minimal shm
  --cpus="1" \             # Single CPU
  ...
```

**Rationale**:
- Tight limits expose memory leaks early
- No swap = predictable performance
- Fail fast = easier debugging

#### Memory Sizing Formula:

```
Container Memory = Base + (Processes × Per-Process) + Buffer

Example for dev-arm64:
  Base OS:        200 MB
  Neovim:         100 MB
  clangd:         500 MB
  Node.js/Auggie: 500 MB
  Go tools:       200 MB
  Buffer (30%):   1500 MB
  ─────────────────────────
  Total:          3000 MB ≈ 3GB minimum

Recommended: 2× minimum = 6GB
```

#### Monitoring Commands:

```bash
# Quick health check:
docker stats dev-arm64 --no-stream

# Detailed memory breakdown:
docker exec dev-arm64 free -h

# Top memory consumers:
docker exec dev-arm64 ps aux --sort=-%mem | head -10

# Shared memory usage:
docker exec dev-arm64 df -h /dev/shm

# Check for OOM kills:
docker inspect dev-arm64 | grep OOMKilled

# Watch memory in real-time:
watch -n 1 'docker stats dev-arm64 --no-stream'
```

#### Warning Signs:

```
⚠️  Memory > 70%:
   - Monitor closely
   - Consider increasing limit

❌ Memory > 85%:
   - Increase limit immediately
   - Check for memory leaks
   - Optimize applications

❌❌ OOMKilled: true:
   - Container was killed
   - MUST increase memory or optimize
   - Check logs for culprit process
```

---

## Real-World Example: Your dev-arm64 Container

### Before Optimization:
```bash
Colima:        2 CPUs, 2GB RAM
Container:     No limits (unlimited)
Result:        OOMKilled: true ❌

$ docker stats dev-arm64
MEM USAGE / LIMIT: 1.139GB / 1.913GB (59.54%)

$ docker exec dev-arm64 free -h
              total   used   free   shared  buff/cache  available
Mem:          1.9Gi  1.2Gi  50Mi   0.0Ki   766Mi       727Mi

Problems:
- Only 50MB free memory
- 59% memory usage (too high)
- OOM killer active
- Auggie very slow to start
```

### After Optimization:
```bash
Colima:        4 CPUs, 8GB RAM ✅
Container:     6GB RAM, 8GB swap, 1GB shm ✅
Result:        OOMKilled: false ✅

$ docker stats dev-arm64
MEM USAGE / LIMIT: 179.4MiB / 6GiB (2.92%)

$ docker exec dev-arm64 free -h
              total   used   free   shared  buff/cache  available
Mem:          7.7Gi  373Mi  6.9Gi  0.0Ki   624Mi       7.4Gi

Improvements:
- 6.9GB free memory (138x more!)
- 2.92% memory usage (excellent)
- No OOM kills
- Auggie starts instantly
```

### Configuration Used:
```bash
# Colima:
colima start --cpu 4 --memory 8 --disk 100

# Container:
docker run \
  --memory="6g" \
  --memory-swap="8g" \
  --shm-size="1g" \
  --cpus="4" \
  -e NODE_OPTIONS="--max-old-space-size=1024" \
  ...
```

---

## Summary

### Memory Types Quick Reference:

| Type | Flag | Purpose | Your Setting |
|------|------|---------|--------------|
| **RAM** | `--memory` | Max RAM for container | 6GB |
| **Swap** | `--memory-swap` | Total RAM+Swap | 8GB (2GB swap) |
| **Shared** | `--shm-size` | /dev/shm for IPC | 1GB |
| **Node.js** | `NODE_OPTIONS` | V8 heap limit | 1GB |

### Key Metrics to Monitor:

| Metric | Command | Healthy Range |
|--------|---------|---------------|
| **Memory %** | `docker stats` | < 70% |
| **Available** | `free -h` | > 30% of total |
| **OOM Killed** | `docker inspect` | false |
| **Swap Usage** | `free -h` | 0 (or minimal) |

### Common Issues and Solutions:

| Problem | Symptom | Solution |
|---------|---------|----------|
| **OOM Kills** | Container crashes | Increase `--memory` |
| **Slow Performance** | High swap usage | Increase RAM, reduce swap |
| **Bus Error** | App crashes | Increase `--shm-size` |
| **Memory Leak** | Usage grows over time | Fix app, restart container |

---

## Additional Resources

### Documentation:
- [Docker Memory Limits](https://docs.docker.com/config/containers/resource_constraints/)
- [Linux Memory Management](https://www.kernel.org/doc/html/latest/admin-guide/mm/index.html)
- [OOM Killer](https://www.kernel.org/doc/gorman/html/understand/understand016.html)

### Tools:
```bash
# Memory profiling:
docker exec dev-arm64 top
docker exec dev-arm64 htop
docker exec dev-arm64 vmstat 1

# Memory debugging:
docker exec dev-arm64 valgrind --leak-check=full ./myapp
docker exec dev-arm64 heaptrack ./myapp

# Container monitoring:
docker stats
docker events --filter event=oom
```

---

**Document Version**: 1.0
**Last Updated**: 2026-03-23
**Author**: Augment Agent
**Related**: `~/ajaywifi/arm64-native/CONTAINER_OPTIMIZED.md`
