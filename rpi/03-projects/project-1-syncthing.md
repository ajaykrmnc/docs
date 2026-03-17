# Project 1: Syncthing Setup

> Learn distributed sync concepts by using a battle-tested P2P sync tool.

**Previous:** [Gossip Protocol](../02-concepts/gossip-protocol.md) | **Next:** [Project 2: rsync Watcher](./project-2-rsync-watcher.md)

---

## Why Start with Syncthing?

Before building your own sync, understand what good sync looks like:

- **Decentralized**: No central server
- **Encrypted**: End-to-end encryption
- **Conflict handling**: Automatic conflict resolution
- **Versioning**: File history preserved
- **Cross-platform**: Works on all your devices

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                  SYNCTHING NETWORK                          │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│   ┌────────────┐      Block Exchange     ┌────────────┐    │
│   │   Office   │◄───────────────────────►│  Personal  │    │
│   │   Laptop   │         Protocol        │   Laptop   │    │
│   │            │                         │            │    │
│   │ Device ID: │                         │ Device ID: │    │
│   │ AAAA-BBBB  │                         │ CCCC-DDDD  │    │
│   └─────┬──────┘                         └─────┬──────┘    │
│         │                                      │           │
│         │         ┌────────────┐               │           │
│         └────────►│    RPi     │◄──────────────┘           │
│                   │            │                           │
│                   │ Device ID: │                           │
│                   │ EEEE-FFFF  │                           │
│                   │            │                           │
│                   │ Storage:   │                           │
│                   │ /mnt/ssd   │                           │
│                   └────────────┘                           │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## Installation

### macOS (Laptops)

```bash
# Install via Homebrew
brew install syncthing

# Start as a service
brew services start syncthing

# Or run manually
syncthing
```

### Raspberry Pi

```bash
# Add Syncthing repository
curl -s https://syncthing.net/release-key.txt | sudo apt-key add -
echo "deb https://apt.syncthing.net/ syncthing stable" | \
    sudo tee /etc/apt/sources.list.d/syncthing.list

# Install
sudo apt update
sudo apt install syncthing

# Enable as service for user 'pi'
sudo systemctl enable syncthing@pi
sudo systemctl start syncthing@pi
```

---

## Configuration

### Access Web UI

- **Local**: http://localhost:8384
- **RPi from laptop**: http://rpi-sync.local:8384

### Step 1: Get Device IDs

Each device has a unique ID. Find it in:
- Web UI → Actions → Show ID
- Or: `syncthing -device-id`

Record all three:
```
Office Laptop:  AAAAAAA-BBBBBBB-CCCCCCC-DDDDDDD-EEEEEEE-FFFFFFF-GGGGGGG-HHHHHHH
Personal Laptop: IIIIIII-JJJJJJJ-KKKKKKK-LLLLLLL-MMMMMMM-NNNNNNN-OOOOOOO-PPPPPPP
RPi:             QQQQQQQ-RRRRRRR-SSSSSSS-TTTTTTT-UUUUUUU-VVVVVVV-WWWWWWW-XXXXXXX
```

### Step 2: Add Remote Devices

On each device, add the other two:
1. Web UI → Add Remote Device
2. Enter Device ID
3. Give it a name (e.g., "RPi", "Office Laptop")
4. Accept on the other device when prompted

### Step 3: Create Shared Folder

On RPi (primary storage):
1. Add Folder
2. Folder Path: `/mnt/ssd/distributed-lab/sync`
3. Folder Label: `distributed-lab`
4. Share with: Office Laptop, Personal Laptop

On laptops, accept the folder share and set local path:
```
~/distributed-lab/sync
```

---

## Configuration File (Reference)

Syncthing config: `~/.config/syncthing/config.xml` (Linux/RPi)
or `~/Library/Application Support/Syncthing/config.xml` (macOS)

```xml
<configuration version="35">
    <folder id="distributed-lab" label="Distributed Lab" path="/mnt/ssd/distributed-lab/sync">
        <device id="OFFICE-DEVICE-ID"></device>
        <device id="PERSONAL-DEVICE-ID"></device>
        <versioning type="simple">
            <param key="keep" val="5"></param>
        </versioning>
    </folder>
    <device id="OFFICE-DEVICE-ID" name="Office Laptop">
        <address>dynamic</address>
    </device>
    <device id="PERSONAL-DEVICE-ID" name="Personal Laptop">
        <address>dynamic</address>
    </device>
</configuration>
```

---

## Test the Setup

### Basic Sync Test

```bash
# On RPi, create a test file
echo "Hello from RPi at $(date)" > /mnt/ssd/distributed-lab/sync/test.txt

# Wait a few seconds, then check on laptops
cat ~/distributed-lab/sync/test.txt
```

### Conflict Test

```bash
# IMPORTANT: Disconnect devices first (or work fast!)

# On Office Laptop
echo "Edit from Office" > ~/distributed-lab/sync/conflict-test.txt

# On Personal Laptop (simultaneously)
echo "Edit from Personal" > ~/distributed-lab/sync/conflict-test.txt

# Reconnect - observe how Syncthing handles conflict
ls ~/distributed-lab/sync/
# You'll see: conflict-test.txt and conflict-test.sync-conflict-*.txt
```

---

## Observe & Learn

### What to Monitor

1. **Web UI Statistics**: 
   - Transfer rates
   - Connected devices
   - Folder status

2. **Logs**:
```bash
# RPi
journalctl -u syncthing@pi -f

# macOS
tail -f ~/Library/Application\ Support/Syncthing/syncthing.log
```

3. **Block Exchange Protocol**: How files are chunked and transferred

---

## Concepts Demonstrated

| Concept | How Syncthing Shows It |
|---------|----------------------|
| **Eventual Consistency** | Changes propagate over time |
| **Conflict Detection** | sync-conflict files created |
| **Gossip-like Discovery** | Devices find each other |
| **Merkle Trees** | File blocks are hashed |
| **Vector Clocks** | File versions tracked |

---

## Learning Exercises

### Exercise 1: Offline Editing
1. Disconnect RPi from network
2. Edit files on both laptops
3. Edit same file on RPi
4. Reconnect - observe resolution

### Exercise 2: Large File Sync
1. Create a large file (100MB+)
2. Observe block-based transfer
3. Modify small portion
4. See only changed blocks transfer

### Exercise 3: Version History
1. Enable versioning in folder settings
2. Edit a file multiple times
3. Check `.stversions` folder
4. Recover old version

---

## What You'll Build Next

Now that you understand sync behavior, Project 2 builds a simpler version:

```
Syncthing                 Your Custom Sync
─────────                 ────────────────
Block Exchange Protocol → rsync delta transfer
Global Discovery        → mDNS local discovery
Merkle Trees            → Simple file hashing
BEP                     → REST API or gRPC
```

---

**Next:** [Project 2: Custom rsync Watcher →](./project-2-rsync-watcher.md)

