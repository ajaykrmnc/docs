# Chapter 7: Log-Structured Storage

## Table of Contents
- [Introduction to LSM-Trees](#introduction-to-lsm-trees)
- [Write Path](#write-path)
- [Memtables](#memtables)
- [SSTables](#sstables)
- [Read Path](#read-path)
- [Compaction Strategies](#compaction-strategies)
- [Bloom Filters](#bloom-filters)
- [LSM-Tree vs B-Tree](#lsm-tree-vs-b-tree)
- [Summary](#summary)

---

## Introduction to LSM-Trees

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    LOG-STRUCTURED MERGE TREES (LSM-TREES)                   │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  THE PROBLEM WITH B-TREES                                                   │
│  ════════════════════════                                                   │
│                                                                             │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │                                                                       │  │
│  │  B-Trees require RANDOM WRITES to disk:                               │  │
│  │                                                                       │  │
│  │    INSERT key 42:                                                     │  │
│  │    1. Read page from disk (random read)                               │  │
│  │    2. Modify page in memory                                           │  │
│  │    3. Write page back to disk (random write)                          │  │
│  │                                                                       │  │
│  │    ┌─────────┐                                                        │  │
│  │    │ Disk    │  Random I/O: ~100-200 ops/sec (HDD)                    │  │
│  │    │ ═══════ │  Sequential I/O: ~100+ MB/sec (HDD)                    │  │
│  │    │         │                                                        │  │
│  │    │  ←───── │  Random writes are 1000x slower than sequential!       │  │
│  │    │  ─────→ │                                                        │  │
│  │    └─────────┘                                                        │  │
│  │                                                                       │  │
│  │  SSDs are better but still prefer sequential writes:                  │  │
│  │  • No seek time, but write amplification concerns                     │  │
│  │  • Flash cells wear out with each write cycle                         │  │
│  │                                                                       │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                                                                             │
│  THE LSM-TREE SOLUTION                                                      │
│  ═════════════════════                                                      │
│                                                                             │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │                                                                       │  │
│  │  Key insight: Turn random writes into SEQUENTIAL writes               │  │
│  │                                                                       │  │
│  │                Memory                    Disk                         │  │
│  │             ┌──────────┐           ┌──────────────┐                   │  │
│  │   Writes →  │ Memtable │  ─────→   │ SSTable L0   │                   │  │
│  │             │ (sorted) │  flush    │ SSTable L0   │                   │  │
│  │             └──────────┘           ├──────────────┤                   │  │
│  │                                    │ SSTable L1   │ (merged)          │  │
│  │                                    │ SSTable L1   │                   │  │
│  │                                    ├──────────────┤                   │  │
│  │                                    │ SSTable L2   │ (larger)          │  │
│  │                                    └──────────────┘                   │  │
│  │                                                                       │  │
│  │  • Writes go to in-memory buffer (fast!)                              │  │
│  │  • Buffer flushed sequentially to disk                                │  │
│  │  • Background compaction merges files                                 │  │
│  │                                                                       │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                                                                             │
│  WHO USES LSM-TREES?                                                        │
│  ═══════════════════                                                        │
│                                                                             │
│  • LevelDB (Google) - embedded key-value store                              │
│  • RocksDB (Facebook) - LevelDB fork, widely used                           │
│  • Cassandra - distributed database                                         │
│  • HBase - Hadoop database                                                  │
│  • ScyllaDB - Cassandra-compatible, high performance                        │
│  • InfluxDB - time-series database                                          │
│  • CockroachDB - uses RocksDB as storage engine                             │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Write Path

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    LSM-TREE WRITE PATH                                      │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │                                                                       │  │
│  │   Client                                                              │  │
│  │     │                                                                 │  │
│  │     │ PUT(key="user:123", value="{name: 'Alice'}")                    │  │
│  │     ▼                                                                 │  │
│  │  ┌──────────────────┐                                                 │  │
│  │  │ 1. Write to WAL  │ ← Append-only, sequential write                 │  │
│  │  │    (on disk)     │   For durability in case of crash               │  │
│  │  └────────┬─────────┘                                                 │  │
│  │           │                                                           │  │
│  │           ▼                                                           │  │
│  │  ┌──────────────────┐                                                 │  │
│  │  │ 2. Write to      │ ← In-memory, sorted structure                   │  │
│  │  │    Memtable      │   Very fast! No disk I/O                        │  │
│  │  └────────┬─────────┘                                                 │  │
│  │           │                                                           │  │
│  │           ▼                                                           │  │
│  │  ┌──────────────────┐                                                 │  │
│  │  │ 3. Return ACK    │ ← Write is "committed"                          │  │
│  │  │    to client     │   (WAL ensures durability)                      │  │
│  │  └──────────────────┘                                                 │  │
│  │                                                                       │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                                                                             │
│  WRITE-AHEAD LOG (WAL) DETAILS                                              │
│  ═════════════════════════════                                              │
│                                                                             │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │                                                                       │  │
│  │  WAL ensures durability without random writes:                        │  │
│  │                                                                       │  │
│  │  ┌─────────────────────────────────────────────────────────────────┐  │  │
│  │  │ WAL File (append-only)                                          │  │  │
│  │  ├─────────────────────────────────────────────────────────────────┤  │  │
│  │  │ [seq:1][PUT][key:user:100][value:...]                           │  │  │
│  │  │ [seq:2][PUT][key:user:101][value:...]                           │  │  │
│  │  │ [seq:3][DELETE][key:user:50]                                    │  │  │
│  │  │ [seq:4][PUT][key:user:102][value:...]  ← append here            │  │  │
│  │  └─────────────────────────────────────────────────────────────────┘  │  │
│  │                                                                       │  │
│  │  On crash recovery:                                                   │  │
│  │  1. Read WAL from last checkpoint                                     │  │
│  │  2. Replay operations into new memtable                               │  │
│  │  3. Resume normal operation                                           │  │
│  │                                                                       │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Memtables

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    MEMTABLES                                                │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  WHAT IS A MEMTABLE?                                                        │
│  ═══════════════════                                                        │
│                                                                             │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │                                                                       │  │
│  │  An in-memory sorted data structure that buffers writes:              │  │
│  │                                                                       │  │
│  │  Common implementations:                                              │  │
│  │  • Red-Black Tree - balanced BST, O(log n) operations                 │  │
│  │  • Skip List - probabilistic, simpler concurrency (LevelDB/RocksDB)   │  │
│  │  • AVL Tree - strictly balanced                                       │  │
│  │                                                                       │  │
│  │  Skip List Example:                                                   │  │
│  │                                                                       │  │
│  │  Level 3: HEAD ────────────────────────────────────────────→ 100      │  │
│  │  Level 2: HEAD ───────────→ 30 ─────────────────→ 70 ──────→ 100      │  │
│  │  Level 1: HEAD ────→ 10 ──→ 30 ────→ 50 ────────→ 70 ──→ 90→ 100      │  │
│  │  Level 0: HEAD → 5→ 10→ 20→ 30→ 40→ 50→ 60→ 70→ 80→ 90→ 100           │  │
│  │                                                                       │  │
│  │  Search for 60:                                                       │  │
│  │  L3: HEAD→100 (too big, drop)                                         │  │
│  │  L2: HEAD→30→70 (too big, drop)                                       │  │
│  │  L1: HEAD→30→50→70 (too big, drop)                                    │  │
│  │  L0: 50→60 (found!)                                                   │  │
│  │                                                                       │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                                                                             │
│  MEMTABLE LIFECYCLE                                                         │
│  ══════════════════                                                         │
│                                                                             │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │                                                                       │  │
│  │           Writes                                                      │  │
│  │              │                                                        │  │
│  │              ▼                                                        │  │
│  │       ┌────────────┐                                                  │  │
│  │       │  ACTIVE    │  ← Currently receiving writes                    │  │
│  │       │  Memtable  │    Mutable                                       │  │
│  │       └─────┬──────┘                                                  │  │
│  │             │ When size >= threshold (e.g., 64MB)                     │  │
│  │             ▼                                                         │  │
│  │       ┌────────────┐                                                  │  │
│  │       │  IMMUTABLE │  ← No more writes accepted                       │  │
│  │       │  Memtable  │    Being flushed to disk                         │  │
│  │       └─────┬──────┘                                                  │  │
│  │             │ Background flush thread                                 │  │
│  │             ▼                                                         │  │
│  │       ┌────────────┐                                                  │  │
│  │       │  SSTable   │  ← Written to disk as SSTable                    │  │
│  │       │  (L0)      │    Immutable once written                        │  │
│  │       └────────────┘                                                  │  │
│  │                                                                       │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                                                                             │
│  HANDLING DELETES                                                           │
│  ════════════════                                                           │
│                                                                             │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │                                                                       │  │
│  │  LSM-trees don't delete immediately - they use TOMBSTONES:            │  │
│  │                                                                       │  │
│  │  DELETE(key="user:50")                                                │  │
│  │     │                                                                 │  │
│  │     └─→ Insert special marker: (key="user:50", value=TOMBSTONE)       │  │
│  │                                                                       │  │
│  │  ┌──────────────────────────────────────────────────────────────┐     │  │
│  │  │ Memtable                                                     │     │  │
│  │  ├──────────────────────────────────────────────────────────────┤     │  │
│  │  │ user:48  →  {data...}                                        │     │  │
│  │  │ user:49  →  {data...}                                        │     │  │
│  │  │ user:50  →  🪦 TOMBSTONE                                      │     │  │
│  │  │ user:51  →  {data...}                                        │     │  │
│  │  └──────────────────────────────────────────────────────────────┘     │  │
│  │                                                                       │  │
│  │  Tombstone masks older values during reads.                           │  │
│  │  Actual deletion happens during compaction.                           │  │
│  │                                                                       │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## SSTables

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    SORTED STRING TABLES (SSTABLES)                          │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  WHAT IS AN SSTABLE?                                                        │
│  ═══════════════════                                                        │
│                                                                             │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │                                                                       │  │
│  │  Immutable, sorted file on disk:                                      │  │
│  │                                                                       │  │
│  │  Key properties:                                                      │  │
│  │  • Keys are SORTED - enables efficient search and merging             │  │
│  │  • IMMUTABLE - never modified after creation                          │  │
│  │  • Self-contained - has own index and metadata                        │  │
│  │                                                                       │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                                                                             │
│  SSTABLE STRUCTURE                                                          │
│  ═════════════════                                                          │
│                                                                             │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │                                                                       │  │
│  │  ┌─────────────────────────────────────────────────────────────────┐  │  │
│  │  │                        SSTable File                             │  │  │
│  │  ├─────────────────────────────────────────────────────────────────┤  │  │
│  │  │                                                                 │  │  │
│  │  │  ┌──────────────────────────────────────────────────────────┐   │  │  │
│  │  │  │ DATA BLOCKS                                              │   │  │  │
│  │  │  ├──────────────────────────────────────────────────────────┤   │  │  │
│  │  │  │ Block 0: [key1:val1][key2:val2][key3:val3]...            │   │  │  │
│  │  │  │ Block 1: [key50:val][key51:val][key52:val]...            │   │  │  │
│  │  │  │ Block 2: [key100:val][key101:val]...                     │   │  │  │
│  │  │  │ ...                                                      │   │  │  │
│  │  │  └──────────────────────────────────────────────────────────┘   │  │  │
│  │  │                                                                 │  │  │
│  │  │  ┌──────────────────────────────────────────────────────────┐   │  │  │
│  │  │  │ INDEX BLOCK                                              │   │  │  │
│  │  │  ├──────────────────────────────────────────────────────────┤   │  │  │
│  │  │  │ key1   → offset 0                                        │   │  │  │
│  │  │  │ key50  → offset 4096                                     │   │  │  │
│  │  │  │ key100 → offset 8192                                     │   │  │  │
│  │  │  │ (first key of each data block)                           │   │  │  │
│  │  │  └──────────────────────────────────────────────────────────┘   │  │  │
│  │  │                                                                 │  │  │
│  │  │  ┌──────────────────────────────────────────────────────────┐   │  │  │
│  │  │  │ BLOOM FILTER                                             │   │  │  │
│  │  │  ├──────────────────────────────────────────────────────────┤   │  │  │
│  │  │  │ [bit array for probabilistic membership test]            │   │  │  │
│  │  │  └──────────────────────────────────────────────────────────┘   │  │  │
│  │  │                                                                 │  │  │
│  │  │  ┌──────────────────────────────────────────────────────────┐   │  │  │
│  │  │  │ FOOTER                                                   │   │  │  │
│  │  │  ├──────────────────────────────────────────────────────────┤   │  │  │
│  │  │  │ index_offset | bloom_offset | metadata | magic_number    │   │  │  │
│  │  │  └──────────────────────────────────────────────────────────┘   │  │  │
│  │  │                                                                 │  │  │
│  │  └─────────────────────────────────────────────────────────────────┘  │  │
│  │                                                                       │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

