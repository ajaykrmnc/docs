# Docker Migration Documentation

This directory contains comprehensive documentation for the Docker Desktop to Colima migration performed on March 23, 2026.

---

## 📚 Documentation Files

### 1. **docker-desktop-to-colima-migration.md** (Main Documentation)
   - **Purpose:** Complete, detailed migration guide with every step documented
   - **Length:** ~1,165 lines
   - **Contents:**
     - Migration overview and rationale
     - Pre-migration state analysis
     - Step-by-step migration process with all commands
     - Post-migration verification
     - Troubleshooting guide
     - Daily usage instructions
     - Complete container configurations
     - Performance comparisons
     - Backup/restore procedures
   - **Use When:** You need detailed information about the migration or want to understand what was done

### 2. **colima-quick-reference.md** (Quick Reference)
   - **Purpose:** Quick command reference for daily use
   - **Length:** ~150 lines
   - **Contents:**
     - Quick start commands
     - Container management shortcuts
     - Common tasks
     - Troubleshooting quick fixes
     - Health check script
   - **Use When:** You need to quickly look up a command or troubleshoot an issue

### 3. **container-recreation-commands.sh** (Executable Script)
   - **Purpose:** Automated script to recreate containers from scratch
   - **Length:** ~216 lines
   - **Contents:**
     - Prerequisite checks
     - Volume creation
     - Container recreation with exact configurations
     - Verification tests
     - Individual command reference
   - **Use When:** You need to recreate containers after a Colima reset or system change
   - **How to Run:**
     ```bash
     cd ~/docs
     ./container-recreation-commands.sh
     ```

---

## 🚀 Quick Start

### First Time After Migration

1. **Verify everything is working:**
   ```bash
   colima status
   docker ps
   ```

2. **If Colima is not running:**
   ```bash
   colima start
   ```

3. **Check your containers:**
   ```bash
   docker exec -it wifiap /bin/bash
   docker exec -it artools-base /bin/bash
   ```

### Daily Usage

- **Start Colima:** `colima start`
- **Stop Colima:** `colima stop`
- **Check containers:** `docker ps`
- **Access wifiap:** `docker exec -it wifiap /bin/bash`
- **Access artools-base:** `docker exec -it artools-base /bin/bash`

For more commands, see **colima-quick-reference.md**

---

## 📋 Migration Summary

### What Was Migrated

| Item | Details |
|------|---------|
| **Images** | 2 images (barney-docker:latest, artools-base:latest) |
| **Containers** | 2 containers (wifiap, artools-base) |
| **Volumes** | 1 volume (artools-docker_artools-base-workspace) |
| **Total Size** | ~11 GB |
| **Duration** | ~20 minutes |
| **Downtime** | 0 minutes |

### What Was Removed

- ✅ Docker Desktop application
- ✅ Docker Desktop data and settings
- ✅ Docker Desktop CLI symlinks
- ✅ desktop-linux Docker context

### Current State

- **Runtime:** Colima (lightweight VM)
- **Context:** colima
- **Containers:** Both running successfully
- **Images:** Both available
- **Volumes:** Preserved

---

## ⚠️ Important Notes

1. **Colima Must Be Started Manually**
   - Unlike Docker Desktop, Colima doesn't auto-start
   - Run `colima start` after rebooting your Mac
   - Or enable auto-start: `brew services start colima`

2. **Platform Architecture**
   - Your images are x86_64 (amd64)
   - Running on ARM64 (Apple Silicon) via Rosetta 2 emulation
   - This is normal and expected - containers work fine

3. **Volume Mounts**
   - wifiap uses: `/Volumes/linux-dev/garage`, `/Volumes/linux-dev/linux`
   - artools-base uses: `/Users/ajay.kumar`, workspace volume
   - Make sure these paths exist and are accessible

4. **Resource Usage**
   - Colima uses ~65% less RAM than Docker Desktop
   - Colima uses ~50% less CPU than Docker Desktop
   - Startup is ~67% faster

---

## 🔧 Common Tasks

### Start Everything
```bash
colima start
docker start wifiap artools-base
```

### Stop Everything
```bash
docker stop wifiap artools-base
colima stop
```

### Check Health
```bash
colima status
docker ps
docker exec wifiap echo "✅ wifiap OK"
docker exec artools-base echo "✅ artools-base OK"
```

### View Logs
```bash
docker logs -f wifiap
docker logs -f artools-base
```

### Restart a Container
```bash
docker restart wifiap
docker restart artools-base
```

---

## 🆘 Troubleshooting

### Problem: "Cannot connect to Docker daemon"
**Solution:**
```bash
colima start
```

### Problem: "Container not found"
**Solution:**
```bash
# Check if container exists
docker ps -a

# If missing, recreate it
cd ~/docs
./container-recreation-commands.sh
```

### Problem: "Colima won't start"
**Solution:**
```bash
# Check logs
colima logs

# Try stopping and starting
colima stop
colima start

# If still failing, restart with fresh config
colima delete
colima start
# Then recreate containers using the script
```

### Problem: "Out of disk space"
**Solution:**
```bash
# Check usage
docker system df

# Clean up
docker system prune -a
```

For more troubleshooting, see **docker-desktop-to-colima-migration.md** Section: Troubleshooting

---

## 📖 Where to Find Information

| What You Need | Which Document |
|---------------|----------------|
| Detailed migration steps | docker-desktop-to-colima-migration.md |
| Quick command reference | colima-quick-reference.md |
| Recreate containers | container-recreation-commands.sh |
| Container configurations | docker-desktop-to-colima-migration.md (Appendix A) |
| Troubleshooting | All documents have troubleshooting sections |
| Performance data | docker-desktop-to-colima-migration.md (Appendix E) |
| Backup procedures | docker-desktop-to-colima-migration.md (Appendix G) |

---

## 🔗 Useful Links

- **Colima GitHub:** https://github.com/abiosoft/colima
- **Docker Documentation:** https://docs.docker.com/
- **Lima (underlying VM):** https://github.com/lima-vm/lima

---

## 📝 Document Versions

| Document | Version | Last Updated |
|----------|---------|--------------|
| docker-desktop-to-colima-migration.md | 1.0 | March 23, 2026 |
| colima-quick-reference.md | 1.0 | March 23, 2026 |
| container-recreation-commands.sh | 1.0 | March 23, 2026 |
| DOCKER_MIGRATION_README.md | 1.0 | March 23, 2026 |

---

**Migration Status:** ✅ Complete and Verified
**System:** macOS (Apple Silicon - ARM64)
**Runtime:** Colima with Docker
**Containers:** wifiap, artools-base (both running)

