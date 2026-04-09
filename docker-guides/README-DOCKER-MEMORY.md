# Docker/Colima Memory Documentation Index

This directory contains comprehensive documentation about Docker and Colima memory management, created to address performance issues with the dev-arm64 container.

## 📚 Documentation Files

### 1. [Docker Memory Comprehensive Guide](./docker-memory-comprehensive-guide.md)
**Purpose**: In-depth explanation of all memory types and concepts

**Topics Covered**:
- Memory types overview (RAM, Swap, Shared Memory)
- Container memory limits (`--memory`, `--memory-swap`, `--shm-size`)
- Understanding `free -h` output (total, used, free, available, buff/cache)
- Process memory (VSZ, RSS, %MEM)
- Docker stats and monitoring
- OOM Killer explained
- Best practices and guidelines
- Real-world examples

**When to Read**: 
- You want to deeply understand Docker memory
- You're troubleshooting memory issues
- You need to optimize container performance

**Length**: ~730 lines, comprehensive

---

### 2. [Docker Memory Quick Reference](./docker-memory-quick-reference.md)
**Purpose**: Quick lookup for common commands and settings

**Topics Covered**:
- Memory flags cheat sheet
- Quick diagnostic commands
- Common issues and solutions
- Memory formulas
- Recommended settings
- Colima-specific commands

**When to Read**:
- You need a quick answer
- You're setting up a new container
- You want to check container health

**Length**: ~150 lines, concise

---

## 🎯 Quick Start

### I want to understand what each memory metric means
→ Read: [Comprehensive Guide - Section 4: Memory Inside Container](./docker-memory-comprehensive-guide.md#memory-inside-container)

### I want to fix slow container performance
→ Read: [Quick Reference - Common Issues](./docker-memory-quick-reference.md#common-issues)

### I want to know what flags to use
→ Read: [Quick Reference - Recommended Settings](./docker-memory-quick-reference.md#recommended-settings)

### I want to understand OOM Killer
→ Read: [Comprehensive Guide - Section 7: OOM Killer](./docker-memory-comprehensive-guide.md#oom-killer)

### I want to monitor container memory
→ Read: [Quick Reference - Monitoring Commands](./docker-memory-quick-reference.md#monitoring-commands)

---

## 🔍 Key Concepts Summary

### Memory Types

| Type | Flag | Purpose | Typical Value |
|------|------|---------|---------------|
| **RAM** | `--memory` | Max RAM for container | 6GB (dev), 512MB (prod) |
| **Swap** | `--memory-swap` | Total RAM+Swap | 8GB (2GB swap) |
| **Shared** | `--shm-size` | /dev/shm for IPC | 1GB (dev), 64MB (prod) |

### Important Metrics

| Metric | Command | What It Means |
|--------|---------|---------------|
| **Memory %** | `docker stats` | % of limit used |
| **Available** | `free -h` | Memory available for apps |
| **OOMKilled** | `docker inspect` | Was container killed? |
| **RSS** | `ps aux` | Real memory used by process |

### Health Indicators

```
✅ Healthy:   Memory < 50%, Available > 1GB, OOMKilled: false
⚠️  Warning:  Memory 50-70%, Available 500MB-1GB
❌ Critical:  Memory > 85%, Available < 500MB, OOMKilled: true
```

---

## 🛠️ Common Commands

```bash
# Check container stats
docker stats dev-arm64 --no-stream

# Check memory inside container
docker exec dev-arm64 free -h

# Check if OOM killed
docker inspect dev-arm64 | grep OOMKilled

# Top memory processes
docker exec dev-arm64 ps aux --sort=-%mem | head -10

# Increase Colima memory
colima stop
colima start --cpu 4 --memory 8 --disk 100
```

---

## 📖 Related Documentation

### In This Repository:
- `~/ajaywifi/arm64-native/CONTAINER_OPTIMIZED.md` - Container optimization results
- `~/ajaywifi/arm64-native/PERFORMANCE_FIX.md` - Performance fix guide
- `~/ajaywifi/arm64-native/dev-arm64.sh` - Container management script

### External Resources:
- [Docker Resource Constraints](https://docs.docker.com/config/containers/resource_constraints/)
- [Linux Memory Management](https://www.kernel.org/doc/html/latest/admin-guide/mm/index.html)
- [Colima Documentation](https://github.com/abiosoft/colima)

---

## 🎓 Learning Path

### Beginner
1. Read [Quick Reference](./docker-memory-quick-reference.md)
2. Try the monitoring commands
3. Understand the recommended settings

### Intermediate
1. Read [Comprehensive Guide - Sections 1-3](./docker-memory-comprehensive-guide.md)
2. Understand memory types and limits
3. Learn to interpret `free -h` output

### Advanced
1. Read [Comprehensive Guide - Complete](./docker-memory-comprehensive-guide.md)
2. Understand OOM Killer
3. Learn memory sizing formulas
4. Master monitoring and optimization

---

## 💡 Real-World Example

### Problem
```
Container: dev-arm64
Issue: Auggie very slow, first prompt takes minutes
Symptoms: OOMKilled: true, Memory: 59%, Free: 50MB
```

### Solution
```bash
# 1. Increase Colima resources
colima stop
colima start --cpu 4 --memory 8 --disk 100

# 2. Update container script (~/ajaywifi/arm64-native/dev-arm64.sh)
docker run \
  --memory="6g" \
  --memory-swap="8g" \
  --shm-size="1g" \
  --cpus="4" \
  -e NODE_OPTIONS="--max-old-space-size=1024" \
  ...

# 3. Recreate container
cd ~/ajaywifi/arm64-native
./dev-arm64.sh clean
./dev-arm64.sh start
```

### Result
```
Before: Memory 59%, Free 50MB, OOMKilled: true ❌
After:  Memory 2.92%, Free 6.9GB, OOMKilled: false ✅
Performance: 138x more free memory, Auggie starts instantly!
```

---

## 📝 Document History

| Date | Event | Files |
|------|-------|-------|
| 2026-03-23 | Initial creation | All files |
| 2026-03-23 | Container optimization | CONTAINER_OPTIMIZED.md |
| 2026-03-23 | Comprehensive guide | docker-memory-comprehensive-guide.md |
| 2026-03-23 | Quick reference | docker-memory-quick-reference.md |

---

**Maintained by**: Augment Agent  
**Last Updated**: 2026-03-23  
**Version**: 1.0

