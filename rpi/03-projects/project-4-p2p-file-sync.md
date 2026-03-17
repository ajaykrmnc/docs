# Project 4: P2P File Sync System

> Build a complete peer-to-peer file synchronization system combining all learned concepts.

**Previous:** [Project 3: Distributed KV Store](./project-3-distributed-kv-store.md) | **Next:** [Raft Implementation](../04-implementation/raft-implementation.md)

---

## System Overview

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         P2P FILE SYNC SYSTEM                            │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐         │
│  │   Office Node   │  │  Personal Node  │  │    RPi Node     │         │
│  │                 │  │                 │  │                 │         │
│  │ ┌─────────────┐ │  │ ┌─────────────┐ │  │ ┌─────────────┐ │         │
│  │ │File Watcher │ │  │ │File Watcher │ │  │ │File Watcher │ │         │
│  │ └──────┬──────┘ │  │ └──────┬──────┘ │  │ └──────┬──────┘ │         │
│  │        ▼        │  │        ▼        │  │        ▼        │         │
│  │ ┌─────────────┐ │  │ ┌─────────────┐ │  │ ┌─────────────┐ │         │
│  │ │ Sync Engine │ │  │ │ Sync Engine │ │  │ │ Sync Engine │ │         │
│  │ │  - CRDTs    │ │  │ │  - CRDTs    │ │  │ │  - CRDTs    │ │         │
│  │ │  - VClocks  │ │  │ │  - VClocks  │ │  │ │  - VClocks  │ │         │
│  │ └──────┬──────┘ │  │ └──────┬──────┘ │  │ └──────┬──────┘ │         │
│  │        ▼        │  │        ▼        │  │        ▼        │         │
│  │ ┌─────────────┐ │  │ ┌─────────────┐ │  │ ┌─────────────┐ │         │
│  │ │   Gossip    │◄┼──┼►│   Gossip    │◄┼──┼►│   Gossip    │ │         │
│  │ │  Protocol   │ │  │ │  Protocol   │ │  │ │  Protocol   │ │         │
│  │ └─────────────┘ │  │ └─────────────┘ │  │ └─────────────┘ │         │
│  │                 │  │                 │  │        │        │         │
│  └─────────────────┘  └─────────────────┘  │        ▼        │         │
│                                            │   ┌─────────┐   │         │
│                                            │   │   SSD   │   │         │
│                                            │   │ Storage │   │         │
│                                            │   └─────────┘   │         │
│                                            └─────────────────┘         │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## Core Components

### 1. File Metadata with Vector Clock

```python
# file_metadata.py
import hashlib
import os
from dataclasses import dataclass, field
from typing import Dict, List
import time

@dataclass
class FileMetadata:
    path: str
    content_hash: str
    size: int
    vector_clock: Dict[str, int]
    chunks: List[str] = field(default_factory=list)
    deleted: bool = False
    modified_at: float = field(default_factory=time.time)
    
    def to_dict(self):
        return {
            "path": self.path,
            "content_hash": self.content_hash,
            "size": self.size,
            "vector_clock": self.vector_clock,
            "chunks": self.chunks,
            "deleted": self.deleted,
            "modified_at": self.modified_at
        }

def compute_file_hash(filepath: str, chunk_size: int = 4 * 1024 * 1024):
    """Compute hash and chunk hashes for a file."""
    file_hasher = hashlib.sha256()
    chunk_hashes = []
    
    with open(filepath, 'rb') as f:
        while chunk := f.read(chunk_size):
            chunk_hash = hashlib.sha256(chunk).hexdigest()
            chunk_hashes.append(chunk_hash)
            file_hasher.update(chunk)
    
    return file_hasher.hexdigest(), chunk_hashes

def create_metadata(filepath: str, node_id: str, nodes: List[str]):
    """Create metadata for a file."""
    stat = os.stat(filepath)
    content_hash, chunks = compute_file_hash(filepath)
    
    return FileMetadata(
        path=filepath,
        content_hash=content_hash,
        size=stat.st_size,
        vector_clock={n: 0 for n in nodes},
        chunks=chunks,
        modified_at=stat.st_mtime
    )
```

### 2. Sync Engine with CRDTs

```python
# sync_engine.py
from typing import Dict, List, Optional, Tuple
from file_metadata import FileMetadata

class FileIndex:
    """CRDT-based file index using OR-Set semantics."""
    
    def __init__(self, node_id: str):
        self.node_id = node_id
        self.files: Dict[str, FileMetadata] = {}
        self.counter = 0
    
    def add_file(self, metadata: FileMetadata):
        """Add or update a file in the index."""
        self.counter += 1
        metadata.vector_clock[self.node_id] = self.counter
        self.files[metadata.path] = metadata
    
    def remove_file(self, path: str):
        """Mark a file as deleted (tombstone)."""
        if path in self.files:
            self.counter += 1
            self.files[path].deleted = True
            self.files[path].vector_clock[self.node_id] = self.counter
    
    def merge(self, remote_index: 'FileIndex') -> List[Tuple[str, str]]:
        """
        Merge remote index into local.
        Returns list of (path, action) for sync operations.
        """
        actions = []
        
        for path, remote_meta in remote_index.files.items():
            if path not in self.files:
                # New file from remote
                self.files[path] = remote_meta
                actions.append((path, 'download'))
            else:
                local_meta = self.files[path]
                comparison = self._compare_vector_clocks(
                    local_meta.vector_clock,
                    remote_meta.vector_clock
                )
                
                if comparison == 'before':
                    # Remote is newer
                    self.files[path] = remote_meta
                    actions.append((path, 'download'))
                elif comparison == 'concurrent':
                    # Conflict!
                    actions.append((path, 'conflict'))
        
        return actions
    
    def _compare_vector_clocks(self, vc1: Dict, vc2: Dict) -> str:
        """Compare two vector clocks."""
        less = any(vc1.get(k, 0) < vc2.get(k, 0) for k in set(vc1) | set(vc2))
        greater = any(vc1.get(k, 0) > vc2.get(k, 0) for k in set(vc1) | set(vc2))
        
        if less and not greater:
            return 'before'
        elif greater and not less:
            return 'after'
        return 'concurrent'
```

### 3. Gossip-Based Synchronization

```python
# gossip_sync.py
import random
import threading
import time
import requests
from typing import List

class GossipSync:
    def __init__(self, node_id: str, peers: List[str], file_index: 'FileIndex'):
        self.node_id = node_id
        self.peers = peers
        self.file_index = file_index
        self.running = False
        self.interval = 5.0  # seconds
    
    def start(self):
        self.running = True
        self.thread = threading.Thread(target=self._gossip_loop)
        self.thread.daemon = True
        self.thread.start()
    
    def stop(self):
        self.running = False
    
    def _gossip_loop(self):
        while self.running:
            self._do_gossip()
            time.sleep(self.interval)
    
    def _do_gossip(self):
        if not self.peers:
            return
        
        # Select random peer
        peer = random.choice(self.peers)
        
        try:
            # Exchange digests
            response = requests.post(
                f"http://{peer}/sync/exchange",
                json=self._create_digest(),
                timeout=5
            )
            
            if response.ok:
                actions = self.file_index.merge(response.json())
                self._process_actions(actions, peer)
        except Exception as e:
            print(f"Gossip to {peer} failed: {e}")
    
    def _create_digest(self):
        """Create digest of local file index."""
        return {
            path: {
                "hash": meta.content_hash,
                "vc": meta.vector_clock
            }
            for path, meta in self.file_index.files.items()
        }
    
    def _process_actions(self, actions, peer):
        """Process sync actions from merge."""
        for path, action in actions:
            if action == 'download':
                self._download_file(path, peer)
            elif action == 'conflict':
                self._handle_conflict(path, peer)
```

---

## Chunk-Based Transfer

```python
# chunk_transfer.py
CHUNK_SIZE = 4 * 1024 * 1024  # 4MB

def upload_file(filepath: str, peer: str, metadata: FileMetadata):
    """Upload file in chunks."""
    with open(filepath, 'rb') as f:
        for i, chunk_hash in enumerate(metadata.chunks):
            chunk_data = f.read(CHUNK_SIZE)
            
            # Check if peer needs this chunk
            response = requests.get(
                f"http://{peer}/chunks/{chunk_hash}/exists"
            )
            
            if not response.json()['exists']:
                requests.post(
                    f"http://{peer}/chunks/{chunk_hash}",
                    data=chunk_data
                )

def download_file(filepath: str, peer: str, metadata: FileMetadata):
    """Download file in chunks."""
    with open(filepath, 'wb') as f:
        for chunk_hash in metadata.chunks:
            response = requests.get(
                f"http://{peer}/chunks/{chunk_hash}"
            )
            f.write(response.content)
```

---

## Conflict Resolution Strategies

```python
# conflict_resolution.py
from enum import Enum

class ConflictStrategy(Enum):
    LAST_WRITE_WINS = "lww"
    KEEP_BOTH = "both"
    MANUAL = "manual"

def resolve_conflict(local: FileMetadata, remote: FileMetadata, 
                     strategy: ConflictStrategy):
    if strategy == ConflictStrategy.LAST_WRITE_WINS:
        return remote if remote.modified_at > local.modified_at else local
    
    elif strategy == ConflictStrategy.KEEP_BOTH:
        # Rename remote to include conflict marker
        conflict_path = f"{remote.path}.conflict-{remote.node_id}"
        return (local, remote._replace(path=conflict_path))
    
    elif strategy == ConflictStrategy.MANUAL:
        # Save both, let user decide
        return None  # Signal manual resolution needed
```

---

## Running the System

```bash
# On each node
python3 p2p_sync.py \
  --node-id rpi \
  --sync-dir /mnt/ssd/distributed-lab/sync \
  --peers office-laptop.local:8080,personal-laptop.local:8080 \
  --port 8080
```

---

## Complete Project Structure

```
distributed-lab/
├── src/
│   ├── __init__.py
│   ├── file_metadata.py
│   ├── sync_engine.py
│   ├── gossip_sync.py
│   ├── chunk_transfer.py
│   ├── conflict_resolution.py
│   ├── file_watcher.py
│   └── api_server.py
├── config/
│   └── config.yaml
├── tests/
│   ├── test_sync_engine.py
│   └── test_vector_clock.py
└── p2p_sync.py  # Main entry point
```

---

**Next:** [Raft Implementation Guide →](../04-implementation/raft-implementation.md)

