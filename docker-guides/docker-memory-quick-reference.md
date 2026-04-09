# Docker Memory Quick Reference

## TL;DR - Memory Flags

```bash
docker run \
  --memory="6g" \          # Max RAM (hard limit)
  --memory-swap="8g" \     # Total RAM+Swap (8g-6g = 2g swap)
  --shm-size="1g" \        # Shared memory (/dev/shm)
  --cpus="4" \             # CPU limit
  -e NODE_OPTIONS="--max-old-space-size=1024" \  # Node.js heap
  myimage
```

---

## Memory Types Cheat Sheet

| Flag | What It Does | Example | Notes |
|------|--------------|---------|-------|
| `--memory` | Max RAM container can use | `--memory="6g"` | Hard limit, triggers OOM if exceeded |
| `--memory-swap` | Total RAM + Swap | `--memory-swap="8g"` | Swap = memory-swap - memory |
| `--shm-size` | Shared memory size | `--shm-size="1g"` | For /dev/shm, IPC, Node.js |
| `--cpus` | CPU limit | `--cpus="4"` | Number of CPUs |

---

## Quick Diagnostics

### Check Container Memory
```bash
# Quick stats
docker stats dev-arm64 --no-stream

# Inside container
docker exec dev-arm64 free -h

# Top processes
docker exec dev-arm64 ps aux --sort=-%mem | head -10

# Check OOM status
docker inspect dev-arm64 | grep OOMKilled
```

### Healthy vs Unhealthy

| Metric | Healthy ✅ | Warning ⚠️ | Critical ❌ |
|--------|-----------|-----------|------------|
| Memory % | < 50% | 50-70% | > 85% |
| Free RAM | > 1GB | 500MB-1GB | < 500MB |
| OOMKilled | false | - | true |
| Swap Usage | 0 | < 500MB | > 1GB |

---

## Common Issues

### Issue: Container Slow / OOM Killed
```bash
# Check if OOM killed
docker inspect mycontainer | grep OOMKilled

# Solution: Increase memory
docker run --memory="8g" --memory-swap="10g" ...
```

### Issue: "Bus error" or "Cannot allocate memory"
```bash
# Cause: Shared memory too small
# Solution: Increase shm-size
docker run --shm-size="1g" ...
```

### Issue: High Swap Usage
```bash
# Check swap
docker exec mycontainer free -h

# Solution: Increase RAM, reduce swap
docker run --memory="8g" --memory-swap="8g" ...  # No swap
```

---

## Memory Formulas

### Swap Calculation
```
Actual Swap = memory-swap - memory

Examples:
--memory="6g" --memory-swap="8g"  → 2GB swap
--memory="4g" --memory-swap="8g"  → 4GB swap
--memory="6g" --memory-swap="6g"  → 0GB swap (no swap)
```

### Memory Percentage
```
Memory % = (Used / Limit) × 100

Example:
Used: 179MB, Limit: 6GB
Memory % = (179 / 6144) × 100 = 2.91%
```

### Available Memory
```
Available = Free + Reclaimable(buff/cache)

Example from free -h:
Free: 6.9GB, Buff/Cache: 624MB
Available ≈ 6.9GB + 500MB = 7.4GB
```

---

## Recommended Settings

### Development Container
```bash
docker run \
  --memory="6g" \
  --memory-swap="8g" \
  --shm-size="1g" \
  --cpus="4" \
  myimage
```

### Production Container
```bash
docker run \
  --memory="512m" \
  --memory-swap="512m" \
  --shm-size="64m" \
  --cpus="1" \
  myimage
```

### Node.js Application
```bash
docker run \
  --memory="2g" \
  --memory-swap="3g" \
  --shm-size="512m" \
  -e NODE_OPTIONS="--max-old-space-size=1536" \
  node-app
```

---

## Monitoring Commands

```bash
# Real-time stats
docker stats

# Container memory limit
docker inspect mycontainer | grep '"Memory"'

# Memory usage inside container
docker exec mycontainer free -h

# Top memory processes
docker exec mycontainer ps aux --sort=-%mem | head -10

# Shared memory usage
docker exec mycontainer df -h /dev/shm

# Watch memory continuously
watch -n 1 'docker stats mycontainer --no-stream'
```

---

## Colima-Specific

### Check Colima Resources
```bash
colima list
```

### Increase Colima Memory
```bash
# Stop Colima
colima stop

# Start with more resources
colima start --cpu 4 --memory 8 --disk 100

# Verify
colima list
docker info | grep -E "CPUs|Total Memory"
```

### Colima Configuration File
```bash
# View config
cat ~/.colima/default/colima.yaml

# Edit manually (advanced)
vim ~/.colima/default/colima.yaml
```

---

## See Also

- **Comprehensive Guide**: `~/docs/docker-memory-comprehensive-guide.md`
- **Container Optimization**: `~/ajaywifi/arm64-native/CONTAINER_OPTIMIZED.md`
- **Performance Fix**: `~/ajaywifi/arm64-native/PERFORMANCE_FIX.md`

---

**Last Updated**: 2026-03-23

