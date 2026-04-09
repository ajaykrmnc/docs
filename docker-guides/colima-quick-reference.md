# Colima Quick Reference Guide

**Last Updated:** March 23, 2026

---

## Quick Start

### Start Colima
```bash
colima start
```

### Stop Colima
```bash
colima stop
```

### Check Status
```bash
colima status
```

---

## Your Containers

### wifiap Container

**Start/Stop:**
```bash
docker start wifiap
docker stop wifiap
```

**Access Shell:**
```bash
docker exec -it wifiap /bin/bash
```

**View Logs:**
```bash
docker logs -f wifiap
```

**Restart:**
```bash
docker restart wifiap
```

### artools-base Container

**Start/Stop:**
```bash
docker start artools-base
docker stop artools-base
```

**Access Shell:**
```bash
docker exec -it artools-base /bin/bash
```

**View Logs:**
```bash
docker logs -f artools-base
```

**Restart:**
```bash
docker restart artools-base
```

---

## Common Tasks

### List Running Containers
```bash
docker ps
```

### List All Containers
```bash
docker ps -a
```

### List Images
```bash
docker images
```

### List Volumes
```bash
docker volume ls
```

### Check Resource Usage
```bash
docker stats
```

### Clean Up Unused Resources
```bash
# Remove stopped containers
docker container prune

# Remove unused images
docker image prune

# Remove unused volumes
docker volume prune

# Remove everything unused
docker system prune -a
```

---

## Troubleshooting

### Colima Won't Start
```bash
# Check status
colima status

# View logs
colima logs

# Try restarting
colima stop
colima start
```

### Container Won't Start
```bash
# Check container logs
docker logs CONTAINER_NAME

# Inspect container
docker inspect CONTAINER_NAME

# Try recreating (see main doc for full commands)
docker rm CONTAINER_NAME
# Then run the docker run command from the main documentation
```

### Out of Disk Space
```bash
# Check disk usage
docker system df

# Clean up
docker system prune -a --volumes
```

### Can't Connect to Docker
```bash
# Verify Colima is running
colima status

# Check context
docker context show

# Should show: colima
# If not, switch to colima:
docker context use colima
```

---

## Resource Management

### View Current Resources
```bash
colima status
```

### Modify Resources
```bash
# Stop Colima first
colima stop

# Start with new resources (example: 4 CPU, 8GB RAM, 100GB disk)
colima start --cpu 4 --memory 8 --disk 100
```

### Edit Configuration File
```bash
vim ~/.colima/default/colima.yaml
```

---

## Auto-Start on Login

### Enable Auto-Start
```bash
brew services start colima
```

### Disable Auto-Start
```bash
brew services stop colima
```

### Check Auto-Start Status
```bash
brew services list | grep colima
```

---

## Important Notes

⚠️ **Platform Warning:** Your containers are x86_64 (amd64) running on ARM64 via Rosetta 2 emulation. This is normal and expected.

⚠️ **Colima Must Be Running:** Unlike Docker Desktop, Colima doesn't start automatically. Run `colima start` after rebooting.

⚠️ **Volume Mounts:** Your containers have important volume mounts:
- wifiap: `/Volumes/linux-dev/garage`, `/Volumes/linux-dev/linux`
- artools-base: `/Users/ajay.kumar`, workspace volume

---

## Emergency Recovery

### If Everything Breaks

1. **Stop Colima:**
   ```bash
   colima stop
   ```

2. **Start Fresh:**
   ```bash
   colima start
   ```

3. **Check Images (should still be there):**
   ```bash
   docker images
   ```

4. **Recreate Containers:**
   See the full `docker run` commands in the main migration documentation.

### If You Need to Completely Reset

```bash
# WARNING: This deletes EVERYTHING
colima delete
colima start

# You'll need to re-import images and recreate containers
```

---

## Useful Links

- **Full Migration Documentation:** `~/docs/docker-desktop-to-colima-migration.md`
- **Colima GitHub:** https://github.com/abiosoft/colima
- **Docker Documentation:** https://docs.docker.com/

---

## Quick Health Check

Run this to verify everything is working:

```bash
echo "=== Colima Status ==="
colima status

echo -e "\n=== Docker Context ==="
docker context show

echo -e "\n=== Running Containers ==="
docker ps

echo -e "\n=== Container Health ==="
docker exec wifiap echo "✅ wifiap is healthy"
docker exec artools-base echo "✅ artools-base is healthy"
```

Expected output:
```
=== Colima Status ===
INFO[0000] colima is running

=== Docker Context ===
colima

=== Running Containers ===
CONTAINER ID   IMAGE                  COMMAND       CREATED   STATUS   PORTS   NAMES
...            artools-base:latest    ...           ...       Up ...           artools-base
...            barney-docker:latest   ...           ...       Up ...           wifiap

=== Container Health ===
✅ wifiap is healthy
✅ artools-base is healthy
```

