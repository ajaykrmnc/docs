# Project 2: Custom rsync Watcher

> Build your first distributed sync system using file watching and rsync.

**Previous:** [Project 1: Syncthing](./project-1-syncthing.md) | **Next:** [Project 3: Distributed KV Store](./project-3-distributed-kv-store.md)

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    RSYNC WATCHER SYSTEM                     │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│   Laptop A                              Laptop B            │
│   ┌──────────────┐                     ┌──────────────┐    │
│   │ File Watcher │                     │ File Watcher │    │
│   │  (fswatch)   │                     │  (fswatch)   │    │
│   └──────┬───────┘                     └──────┬───────┘    │
│          │                                     │            │
│          ▼                                     ▼            │
│   ┌──────────────┐                     ┌──────────────┐    │
│   │ Change Queue │                     │ Change Queue │    │
│   └──────┬───────┘                     └──────┬───────┘    │
│          │                                     │            │
│          ▼                                     ▼            │
│   ┌──────────────┐                     ┌──────────────┐    │
│   │ rsync client │                     │ rsync client │    │
│   └──────┬───────┘                     └──────┬───────┘    │
│          │                                     │            │
│          └──────────────┬──────────────────────┘            │
│                         │                                   │
│                         ▼                                   │
│                  ┌─────────────┐                           │
│                  │     RPi     │                           │
│                  │ rsync daemon│                           │
│                  │  /mnt/ssd   │                           │
│                  └─────────────┘                           │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## Prerequisites

### All Devices

```bash
# macOS
brew install fswatch rsync

# Linux/RPi
sudo apt install inotify-tools rsync
```

### SSH Keys Setup

```bash
# Generate key (if not exists)
ssh-keygen -t ed25519 -f ~/.ssh/distributed_lab

# Copy to RPi
ssh-copy-id -i ~/.ssh/distributed_lab pi@rpi-sync.local
```

---

## Part 1: Simple One-Way Sync

### Basic Watch Script (macOS)

```bash
#!/bin/bash
# file: sync-to-rpi.sh

WATCH_DIR="$HOME/distributed-lab/sync"
REMOTE="pi@rpi-sync.local:/mnt/ssd/distributed-lab/sync/"

echo "Watching $WATCH_DIR for changes..."

fswatch -o "$WATCH_DIR" | while read -r event; do
    echo "[$(date)] Change detected, syncing..."
    rsync -avz --delete \
        -e "ssh -i ~/.ssh/distributed_lab" \
        "$WATCH_DIR/" "$REMOTE"
    echo "[$(date)] Sync complete"
done
```

### Basic Watch Script (Linux/RPi)

```bash
#!/bin/bash
# file: sync-watch.sh

WATCH_DIR="/mnt/ssd/distributed-lab/sync"

inotifywait -m -r -e modify,create,delete,move "$WATCH_DIR" |
while read -r directory event filename; do
    echo "[$(date)] $event: $directory$filename"
    # Sync to other nodes...
done
```

---

## Part 2: Bidirectional Sync

### Enhanced Sync Script

```python
#!/usr/bin/env python3
"""
bidirectional_sync.py - Two-way sync between nodes
"""

import os
import sys
import time
import subprocess
import hashlib
from pathlib import Path
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

class SyncConfig:
    LOCAL_DIR = Path.home() / "distributed-lab/sync"
    REMOTE_HOST = "pi@rpi-sync.local"
    REMOTE_DIR = "/mnt/ssd/distributed-lab/sync"
    SSH_KEY = Path.home() / ".ssh/distributed_lab"
    SYNC_DELAY = 2  # Seconds to wait before syncing

class ChangeHandler(FileSystemEventHandler):
    def __init__(self):
        self.pending_sync = False
        self.last_change = 0
    
    def on_any_event(self, event):
        if event.is_directory:
            return
        if '.sync-tmp' in event.src_path:
            return
        
        print(f"[Local] {event.event_type}: {event.src_path}")
        self.pending_sync = True
        self.last_change = time.time()

class SyncManager:
    def __init__(self, config):
        self.config = config
        self.handler = ChangeHandler()
        self.observer = Observer()
    
    def start(self):
        self.observer.schedule(
            self.handler,
            str(self.config.LOCAL_DIR),
            recursive=True
        )
        self.observer.start()
        print(f"Watching: {self.config.LOCAL_DIR}")
        
        try:
            while True:
                self.check_and_sync()
                time.sleep(1)
        except KeyboardInterrupt:
            self.observer.stop()
        self.observer.join()
    
    def check_and_sync(self):
        if not self.handler.pending_sync:
            return
        
        # Wait for changes to settle
        if time.time() - self.handler.last_change < self.config.SYNC_DELAY:
            return
        
        self.handler.pending_sync = False
        self.do_sync()
    
    def do_sync(self):
        print(f"[Sync] Starting bidirectional sync...")
        
        # Push local changes to remote
        self.rsync_push()
        
        # Pull remote changes to local
        self.rsync_pull()
        
        print(f"[Sync] Complete")
    
    def rsync_push(self):
        cmd = [
            "rsync", "-avz",
            "-e", f"ssh -i {self.config.SSH_KEY}",
            f"{self.config.LOCAL_DIR}/",
            f"{self.config.REMOTE_HOST}:{self.config.REMOTE_DIR}/"
        ]
        subprocess.run(cmd, capture_output=True)
    
    def rsync_pull(self):
        cmd = [
            "rsync", "-avz",
            "-e", f"ssh -i {self.config.SSH_KEY}",
            f"{self.config.REMOTE_HOST}:{self.config.REMOTE_DIR}/",
            f"{self.config.LOCAL_DIR}/"
        ]
        subprocess.run(cmd, capture_output=True)

if __name__ == "__main__":
    manager = SyncManager(SyncConfig())
    manager.start()
```

---

## Part 3: Conflict Detection

```python
def detect_conflicts(local_dir, remote_manifest):
    """Compare local files with remote manifest."""
    conflicts = []
    
    for filepath in local_dir.rglob("*"):
        if filepath.is_dir():
            continue
        
        rel_path = filepath.relative_to(local_dir)
        local_hash = hash_file(filepath)
        local_mtime = filepath.stat().st_mtime
        
        if str(rel_path) in remote_manifest:
            remote = remote_manifest[str(rel_path)]
            
            # Both modified since last sync
            if (local_hash != remote['hash'] and
                local_mtime > remote['last_sync'] and
                remote['mtime'] > remote['last_sync']):
                conflicts.append({
                    'path': rel_path,
                    'local_hash': local_hash,
                    'remote_hash': remote['hash']
                })
    
    return conflicts

def hash_file(filepath):
    """Create MD5 hash of file."""
    hasher = hashlib.md5()
    with open(filepath, 'rb') as f:
        for chunk in iter(lambda: f.read(8192), b''):
            hasher.update(chunk)
    return hasher.hexdigest()
```

---

## Run as Service

### macOS (launchd)

```xml
<!-- ~/Library/LaunchAgents/com.distributed-lab.sync.plist -->
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" 
    "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.distributed-lab.sync</string>
    <key>ProgramArguments</key>
    <array>
        <string>/usr/bin/python3</string>
        <string>/Users/YOU/distributed-lab/bidirectional_sync.py</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
</dict>
</plist>
```

```bash
launchctl load ~/Library/LaunchAgents/com.distributed-lab.sync.plist
```

### Linux (systemd)

```ini
# ~/.config/systemd/user/distributed-sync.service
[Unit]
Description=Distributed Lab Sync
After=network.target

[Service]
ExecStart=/usr/bin/python3 /home/user/distributed-lab/bidirectional_sync.py
Restart=always

[Install]
WantedBy=default.target
```

```bash
systemctl --user enable distributed-sync
systemctl --user start distributed-sync
```

---

## Limitations & Next Steps

| This Project | Next Project (KV Store) |
|--------------|------------------------|
| File-level sync | Key-level operations |
| Last-write-wins | Versioning + CRDTs |
| Pull-based | Event-driven |
| No coordination | Raft consensus |

---

**Next:** [Project 3: Distributed KV Store →](./project-3-distributed-kv-store.md)

