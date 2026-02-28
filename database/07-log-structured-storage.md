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

---

## Read Path

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    LSM-TREE READ PATH                                       │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  READ OPERATION FLOW                                                        │
│  ═══════════════════                                                        │
│                                                                             │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │                                                                       │  │
│  │   GET(key="user:75")                                                  │  │
│  │         │                                                             │  │
│  │         ▼                                                             │  │
│  │   ┌──────────────┐                                                    │  │
│  │   │ 1. Check     │ ← Most recent data                                 │  │
│  │   │    Memtable  │   O(log n) lookup                                  │  │
│  │   └──────┬───────┘                                                    │  │
│  │          │ Not found?                                                 │  │
│  │          ▼                                                            │  │
│  │   ┌──────────────┐                                                    │  │
│  │   │ 2. Check     │ ← Being flushed, still in memory                   │  │
│  │   │   Immutable  │                                                    │  │
│  │   │   Memtables  │                                                    │  │
│  │   └──────┬───────┘                                                    │  │
│  │          │ Not found?                                                 │  │
│  │          ▼                                                            │  │
│  │   ┌──────────────┐                                                    │  │
│  │   │ 3. Check     │ ← Newest SSTables (unsorted among L0)              │  │
│  │   │   L0 SSTs    │   May need to check ALL L0 files                   │  │
│  │   └──────┬───────┘                                                    │  │
│  │          │ Not found?                                                 │  │
│  │          ▼                                                            │  │
│  │   ┌──────────────┐                                                    │  │
│  │   │ 4. Check     │ ← Binary search (non-overlapping)                  │  │
│  │   │   L1 SSTs    │   Only ONE file to check per level                 │  │
│  │   └──────┬───────┘                                                    │  │
│  │          │ Not found?                                                 │  │
│  │          ▼                                                            │  │
│  │   ┌──────────────┐                                                    │  │
│  │   │ 5. Check     │                                                    │  │
│  │   │   L2, L3...  │ ← Continue until found or exhausted                │  │
│  │   └──────────────┘                                                    │  │
│  │                                                                       │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                                                                             │
│  LEVEL 0 vs OTHER LEVELS                                                    │
│  ═══════════════════════                                                    │
│                                                                             │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │                                                                       │  │
│  │  L0: SSTables may have OVERLAPPING key ranges                         │  │
│  │      (each is a direct memtable flush)                                │  │
│  │                                                                       │  │
│  │  ┌──────────────────────────────────────────────────────────────┐     │  │
│  │  │ L0:  [1─────20]  [5────25]  [15────30]   ← OVERLAPPING!      │     │  │
│  │  │       SST-1       SST-2      SST-3                           │     │  │
│  │  └──────────────────────────────────────────────────────────────┘     │  │
│  │                                                                       │  │
│  │  To find key 18: Must check ALL three L0 files!                       │  │
│  │                                                                       │  │
│  │  L1+: SSTables have NON-OVERLAPPING key ranges                        │  │
│  │       (result of compaction/merge)                                    │  │
│  │                                                                       │  │
│  │  ┌──────────────────────────────────────────────────────────────┐     │  │
│  │  │ L1:  [1───10]  [11───20]  [21───30]     ← NO OVERLAP        │     │  │
│  │  │       SST-A      SST-B       SST-C                           │     │  │
│  │  └──────────────────────────────────────────────────────────────┘     │  │
│  │                                                                       │  │
│  │  To find key 18: Binary search → only check SST-B                     │  │
│  │                                                                       │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                                                                             │
│  READ AMPLIFICATION                                                         │
│  ══════════════════                                                         │
│                                                                             │
│  Worst case: Key doesn't exist                                              │
│  Must check: Memtable + Immutable + ALL L0 + one per level                  │
│                                                                             │
│  Mitigation: BLOOM FILTERS (covered later)                                  │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Compaction Strategies

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    COMPACTION STRATEGIES                                    │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  WHY COMPACTION?                                                            │
│  ═══════════════                                                            │
│                                                                             │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │                                                                       │  │
│  │  Without compaction:                                                  │  │
│  │  • Files accumulate indefinitely                                      │  │
│  │  • Read performance degrades (more files to check)                    │  │
│  │  • Deleted data still takes space (tombstones)                        │  │
│  │  • Duplicate keys waste space                                         │  │
│  │                                                                       │  │
│  │  Compaction: Merge multiple SSTables into fewer, larger ones          │  │
│  │  • Remove deleted records (tombstones)                                │  │
│  │  • Keep only latest version of each key                               │  │
│  │  • Create non-overlapping key ranges                                  │  │
│  │                                                                       │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                                                                             │
│  SIZE-TIERED COMPACTION (STCS)                                              │
│  ═════════════════════════════                                              │
│                                                                             │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │                                                                       │  │
│  │  Group SSTables by size, merge when enough of similar size:           │  │
│  │                                                                       │  │
│  │  ┌──────────────────────────────────────────────────────────────┐     │  │
│  │  │ Small:   [4MB] [4MB] [4MB] [4MB]  → MERGE → [16MB]           │     │  │
│  │  │ Medium:  [16MB] [16MB] [16MB] [16MB] → MERGE → [64MB]        │     │  │
│  │  │ Large:   [64MB] [64MB] [64MB] [64MB] → MERGE → [256MB]       │     │  │
│  │  └──────────────────────────────────────────────────────────────┘     │  │
│  │                                                                       │  │
│  │  Pros:                                                                │  │
│  │  • Simple to implement                                                │  │
│  │  • Good write throughput                                              │  │
│  │  • Files tend to be similar size                                      │  │
│  │                                                                       │  │
│  │  Cons:                                                                │  │
│  │  • Space amplification (up to 2x before compaction)                   │  │
│  │  • Read amplification (overlapping ranges)                            │  │
│  │                                                                       │  │
│  │  Used by: Cassandra (default), HBase                                  │  │
│  │                                                                       │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                                                                             │
│  LEVELED COMPACTION (LCS)                                                   │
│  ═════════════════════════                                                  │
│                                                                             │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │                                                                       │  │
│  │  Organize into levels, each level 10x larger than previous:           │  │
│  │                                                                       │  │
│  │  ┌──────────────────────────────────────────────────────────────┐     │  │
│  │  │                                                              │     │  │
│  │  │  L0: [SST] [SST] [SST]     (overlapping OK, ~4 files max)    │     │  │
│  │  │         └───┬───┘                                            │     │  │
│  │  │             │ compact with overlapping L1 files              │     │  │
│  │  │             ▼                                                │     │  │
│  │  │  L1: [SST][SST][SST][SST]    (10MB total, non-overlapping)   │     │  │
│  │  │              └─┬─┘                                           │     │  │
│  │  │                │ when L1 too big, compact with L2            │     │  │
│  │  │                ▼                                             │     │  │
│  │  │  L2: [SST][SST][SST][SST][SST][SST]...  (100MB, non-overlap) │     │  │
│  │  │                    └──┬──┘                                   │     │  │
│  │  │                       ▼                                      │     │  │
│  │  │  L3: [..........]  (1GB, non-overlapping)                    │     │  │
│  │  │                                                              │     │  │
│  │  └──────────────────────────────────────────────────────────────┘     │  │
│  │                                                                       │  │
│  │  Pros:                                                                │  │
│  │  • Low space amplification (~10%)                                     │  │
│  │  • Bounded read amplification                                         │  │
│  │  • Predictable read performance                                       │  │
│  │                                                                       │  │
│  │  Cons:                                                                │  │
│  │  • Higher write amplification (10-30x typical)                        │  │
│  │  • More I/O during compaction                                         │  │
│  │                                                                       │  │
│  │  Used by: RocksDB (default), LevelDB                                  │  │
│  │                                                                       │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                                                                             │
│  COMPACTION COMPARISON                                                      │
│  ═════════════════════                                                      │
│                                                                             │
│  ┌────────────────────┬────────────────────┬────────────────────┐           │
│  │                    │  Size-Tiered       │  Leveled           │           │
│  ├────────────────────┼────────────────────┼────────────────────┤           │
│  │ Write Amp.         │  Low (~3-5x)       │  High (~10-30x)    │           │
│  │ Read Amp.          │  High              │  Low               │           │
│  │ Space Amp.         │  High (~2x)        │  Low (~10%)        │           │
│  │ Best for           │  Write-heavy       │  Read-heavy        │           │
│  └────────────────────┴────────────────────┴────────────────────┘           │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Bloom Filters

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    BLOOM FILTERS                                            │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  PURPOSE                                                                    │
│  ═══════                                                                    │
│                                                                             │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │                                                                       │  │
│  │  Problem: LSM-Tree read amplification                                 │  │
│  │  - Without optimization: must check ALL SSTables until key found     │  │
│  │  - Most checks will be negative (key not in file)                    │  │
│  │  - Each check = disk I/O                                             │  │
│  │                                                                       │  │
│  │  Solution: Bloom Filter per SSTable                                   │  │
│  │  - Space-efficient probabilistic data structure                      │  │
│  │  - Can tell "definitely NOT in set" or "probably in set"             │  │
│  │  - Avoid unnecessary disk reads                                      │  │
│  │                                                                       │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                                                                             │
│  HOW BLOOM FILTERS WORK                                                     │
│  ══════════════════════                                                     │
│                                                                             │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │                                                                       │  │
│  │  Components:                                                          │  │
│  │  • Bit array of m bits (all initialized to 0)                        │  │
│  │  • k independent hash functions                                       │  │
│  │                                                                       │  │
│  │  INSERT key "user:42":                                                │  │
│  │  ┌────────────────────────────────────────────────────────────┐       │  │
│  │  │                                                            │       │  │
│  │  │  "user:42" ──┬── h1() = 2 ──┐                              │       │  │
│  │  │              ├── h2() = 5 ──┼── Set bits                   │       │  │
│  │  │              └── h3() = 9 ──┘                              │       │  │
│  │  │                                                            │       │  │
│  │  │  Bit Array:                                                │       │  │
│  │  │  Index: 0   1   2   3   4   5   6   7   8   9   10  11     │       │  │
│  │  │        ┌───┬───┬───┬───┬───┬───┬───┬───┬───┬───┬───┬───┐   │       │  │
│  │  │        │ 0 │ 0 │ 1 │ 0 │ 0 │ 1 │ 0 │ 0 │ 0 │ 1 │ 0 │ 0 │   │       │  │
│  │  │        └───┴───┴─▲─┴───┴───┴─▲─┴───┴───┴───┴─▲─┴───┴───┘   │       │  │
│  │  │                  │           │               │             │       │  │
│  │  │                 h1          h2              h3             │       │  │
│  │  │                                                            │       │  │
│  │  └────────────────────────────────────────────────────────────┘       │  │
│  │                                                                       │  │
│  │  LOOKUP key "user:99":                                                │  │
│  │  ┌────────────────────────────────────────────────────────────┐       │  │
│  │  │                                                            │       │  │
│  │  │  "user:99" ──┬── h1() = 2 ─── bit[2] = 1 ✓                 │       │  │
│  │  │              ├── h2() = 7 ─── bit[7] = 0 ✗ ← NOT IN SET!   │       │  │
│  │  │              └── h3() = 9 ─── bit[9] = 1 ✓                 │       │  │
│  │  │                                                            │       │  │
│  │  │  If ANY bit is 0: Key definitely NOT in set                │       │  │
│  │  │  If ALL bits are 1: Key PROBABLY in set (check SSTable)    │       │  │
│  │  │                                                            │       │  │
│  │  └────────────────────────────────────────────────────────────┘       │  │
│  │                                                                       │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                                                                             │
│  FALSE POSITIVES                                                            │
│  ═══════════════                                                            │
│                                                                             │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │                                                                       │  │
│  │  Bloom Filter can say "yes" when key NOT actually present:            │  │
│  │                                                                       │  │
│  │  Bit Array after many inserts:                                        │  │
│  │  Index: 0   1   2   3   4   5   6   7   8   9   10  11                │  │
│  │        ┌───┬───┬───┬───┬───┬───┬───┬───┬───┬───┬───┬───┐              │  │
│  │        │ 1 │ 0 │ 1 │ 1 │ 0 │ 1 │ 1 │ 1 │ 0 │ 1 │ 1 │ 0 │              │  │
│  │        └───┴───┴───┴───┴───┴───┴───┴───┴───┴───┴───┴───┘              │  │
│  │                                                                       │  │
│  │  Query "NOTEXIST": h1()=2, h2()=5, h3()=9                             │  │
│  │  All bits happen to be 1 → FALSE POSITIVE                             │  │
│  │                                                                       │  │
│  │  False Positive Rate (FPR):                                           │  │
│  │  ┌──────────────────────────────────────────────────┐                 │  │
│  │  │                              k                   │                 │  │
│  │  │  FPR ≈ (1 - e^(-kn/m))                          │                 │  │
│  │  │                                                  │                 │  │
│  │  │  m = number of bits                              │                 │  │
│  │  │  n = number of elements inserted                 │                 │  │
│  │  │  k = number of hash functions                    │                 │  │
│  │  └──────────────────────────────────────────────────┘                 │  │
│  │                                                                       │  │
│  │  Typical configurations:                                              │  │
│  │  • 10 bits per key → ~1% FPR                                         │  │
│  │  • 15 bits per key → ~0.1% FPR                                       │  │
│  │  • Optimal k = (m/n) × ln(2) ≈ 0.7 × (m/n)                           │  │
│  │                                                                       │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                                                                             │
│  READ PATH WITH BLOOM FILTER                                                │
│  ═══════════════════════════                                                │
│                                                                             │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │                                                                       │  │
│  │   GET(key)                                                            │  │
│  │      │                                                                │  │
│  │      ▼                                                                │  │
│  │   ┌──────────────┐                                                    │  │
│  │   │  Memtable    │ ──(not found)──┐                                   │  │
│  │   └──────────────┘                │                                   │  │
│  │                                   ▼                                   │  │
│  │   For each SSTable (newest to oldest):                                │  │
│  │   ┌──────────────────────────────────────────────────────────────┐    │  │
│  │   │                                                              │    │  │
│  │   │  ┌────────────────┐     ┌──────────────────┐                 │    │  │
│  │   │  │ Bloom Filter   │────▶│ Key in filter?   │                 │    │  │
│  │   │  │ (in memory)    │     └────────┬─────────┘                 │    │  │
│  │   │  └────────────────┘              │                           │    │  │
│  │   │                         ┌────────┴────────┐                  │    │  │
│  │   │                         │                 │                  │    │  │
│  │   │                        NO                YES                 │    │  │
│  │   │                         │                 │                  │    │  │
│  │   │                         ▼                 ▼                  │    │  │
│  │   │              ┌──────────────┐   ┌──────────────────┐         │    │  │
│  │   │              │ Skip SSTable │   │ Search SSTable   │         │    │  │
│  │   │              │ (no I/O!)    │   │ (disk I/O)       │         │    │  │
│  │   │              └──────────────┘   └──────────────────┘         │    │  │
│  │   │                                                              │    │  │
│  │   └──────────────────────────────────────────────────────────────┘    │  │
│  │                                                                       │  │
│  │  Impact: With 1% FPR, avoid 99% of unnecessary disk reads!            │  │
│  │                                                                       │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## LSM-Tree vs B-Tree

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    LSM-TREE VS B-TREE COMPARISON                            │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ARCHITECTURE COMPARISON                                                    │
│  ═══════════════════════                                                    │
│                                                                             │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │                                                                       │  │
│  │  B-TREE                           LSM-TREE                            │  │
│  │  ══════                           ════════                            │  │
│  │                                                                       │  │
│  │  ┌─────────────┐                  ┌─────────────┐                     │  │
│  │  │    Root     │                  │  Memtable   │ (Memory)            │  │
│  │  └──────┬──────┘                  └──────┬──────┘                     │  │
│  │         │                                │ flush                      │  │
│  │    ┌────┴────┐                           ▼                            │  │
│  │    │         │                    ┌─────────────┐                     │  │
│  │  ┌─┴─┐     ┌─┴─┐                  │ L0 SSTables │                     │  │
│  │  │   │     │   │                  └──────┬──────┘                     │  │
│  │  └─┬─┘     └─┬─┘                         │ compact                    │  │
│  │    │         │                           ▼                            │  │
│  │  ┌─┴─┐ ┌─┴─┐ ┌─┴─┐                ┌─────────────┐                     │  │
│  │  │ L │ │ L │ │ L │ (Leaf)        │ L1 SSTables │                     │  │
│  │  └───┘ └───┘ └───┘                └──────┬──────┘                     │  │
│  │                                          │                            │  │
│  │  In-place updates                        ▼                            │  │
│  │  on disk                           ┌─────────────┐                    │  │
│  │                                    │ L2, L3...   │ (Disk)             │  │
│  │                                    └─────────────┘                    │  │
│  │                                    Append-only writes                 │  │
│  │                                                                       │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                                                                             │
│  DETAILED COMPARISON                                                        │
│  ═══════════════════                                                        │
│                                                                             │
│  ┌──────────────────────┬────────────────────────┬────────────────────────┐ │
│  │ Aspect               │ B-Tree                 │ LSM-Tree               │ │
│  ├──────────────────────┼────────────────────────┼────────────────────────┤ │
│  │ Write Pattern        │ Random I/O             │ Sequential I/O         │ │
│  │ Write Amplification  │ ~2-3x (split, WAL)     │ ~10-30x (compaction)   │ │
│  │ Write Throughput     │ Lower (seeks)          │ Higher (sequential)    │ │
│  ├──────────────────────┼────────────────────────┼────────────────────────┤ │
│  │ Read Pattern         │ Tree traversal         │ Multiple sources       │ │
│  │ Read Amplification   │ Low (O(log n))         │ Higher (memtbl + SSTs) │ │
│  │ Point Query          │ Fast, predictable      │ Variable               │ │
│  │ Range Query          │ Excellent              │ Good (with merge)      │ │
│  ├──────────────────────┼────────────────────────┼────────────────────────┤ │
│  │ Space Amplification  │ ~67% utilization       │ ~10% with LCS          │ │
│  │ Storage Efficiency   │ Page fragmentation     │ No fragmentation       │ │
│  ├──────────────────────┼────────────────────────┼────────────────────────┤ │
│  │ Concurrency          │ Complex (lock mgmt)    │ Simpler (immutable)    │ │
│  │ Recovery             │ WAL replay             │ WAL + SSTable scan     │ │
│  └──────────────────────┴────────────────────────┴────────────────────────┘ │
│                                                                             │
│  WRITE AMPLIFICATION VISUALIZATION                                          │
│  ═════════════════════════════════                                          │
│                                                                             │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │                                                                       │  │
│  │  B-TREE: Write 1 row                                                  │  │
│  │  ┌─────────────────────────────────────────────────────────┐          │  │
│  │  │                                                         │          │  │
│  │  │  1. Write to WAL                    [1 I/O]             │          │  │
│  │  │  2. Read page from disk             [1 I/O]             │          │  │
│  │  │  3. Modify page in memory                               │          │  │
│  │  │  4. Write page back to disk         [1 I/O]             │          │  │
│  │  │  (occasionally: page splits)        [+2 I/O]            │          │  │
│  │  │                                     ──────────          │          │  │
│  │  │  Total: ~2-3x write amplification                       │          │  │
│  │  │                                                         │          │  │
│  │  └─────────────────────────────────────────────────────────┘          │  │
│  │                                                                       │  │
│  │  LSM-TREE: Write 1 row                                                │  │
│  │  ┌─────────────────────────────────────────────────────────┐          │  │
│  │  │                                                         │          │  │
│  │  │  1. Write to WAL                    [1 I/O]             │          │  │
│  │  │  2. Write to memtable (memory)      [0 I/O]             │          │  │
│  │  │  3. Later: flush memtable to L0     [1 I/O]             │          │  │
│  │  │  4. Compact L0 → L1                 [~10 I/O]           │          │  │
│  │  │  5. Compact L1 → L2                 [~10 I/O]           │          │  │
│  │  │  ... (continues through levels)                         │          │  │
│  │  │                                     ──────────          │          │  │
│  │  │  Total: ~10-30x write amplification                     │          │  │
│  │  │  BUT: All writes are sequential!                        │          │  │
│  │  │                                                         │          │  │
│  │  └─────────────────────────────────────────────────────────┘          │  │
│  │                                                                       │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                                                                             │
│  WHEN TO USE WHICH                                                          │
│  ═════════════════                                                          │
│                                                                             │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │                                                                       │  │
│  │  USE B-TREE WHEN:                                                     │  │
│  │  ┌───────────────────────────────────────────────────────────────┐    │  │
│  │  │ • Read-heavy workloads (OLTP with many reads)                 │    │  │
│  │  │ • Need fast, predictable point queries                        │    │  │
│  │  │ • Range scans are common                                      │    │  │
│  │  │ • Strong transaction isolation required                       │    │  │
│  │  │ • Using SSDs (random I/O less expensive)                      │    │  │
│  │  │ • Examples: PostgreSQL, MySQL/InnoDB, Oracle                  │    │  │
│  │  └───────────────────────────────────────────────────────────────┘    │  │
│  │                                                                       │  │
│  │  USE LSM-TREE WHEN:                                                   │  │
│  │  ┌───────────────────────────────────────────────────────────────┐    │  │
│  │  │ • Write-heavy workloads (logging, time-series, IoT)           │    │  │
│  │  │ • Sequential write performance is critical                    │    │  │
│  │  │ • Using HDDs (sequential I/O much faster)                     │    │  │
│  │  │ • Can tolerate some read latency variability                  │    │  │
│  │  │ • Need high write throughput                                  │    │  │
│  │  │ • Examples: Cassandra, RocksDB, LevelDB, HBase                │    │  │
│  │  └───────────────────────────────────────────────────────────────┘    │  │
│  │                                                                       │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                                                                             │
│  SSD CONSIDERATIONS                                                         │
│  ═════════════════                                                          │
│                                                                             │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │                                                                       │  │
│  │  SSDs change the tradeoffs:                                           │  │
│  │                                                                       │  │
│  │  • Random I/O penalty much smaller than HDD                          │  │
│  │  • Write amplification more concerning (SSD wear)                     │  │
│  │  • LSM-Trees can cause SSD wear due to compaction                     │  │
│  │  • B-Trees benefit more from SSD random read performance              │  │
│  │                                                                       │  │
│  │  Many modern databases use hybrid approaches:                         │  │
│  │  • RocksDB: Optimized for SSDs, used by many modern systems           │  │
│  │  • TiKV: LSM-based storage for distributed databases                  │  │
│  │  • MyRocks: MySQL with RocksDB backend                                │  │
│  │                                                                       │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Summary

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    CHAPTER 7 SUMMARY                                        │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  KEY CONCEPTS                                                               │
│  ════════════                                                               │
│                                                                             │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │                                                                       │  │
│  │  LSM-Tree Architecture:                                               │  │
│  │  • Memtable: In-memory sorted structure (skip list/red-black tree)   │  │
│  │  • WAL: Write-ahead log for durability                               │  │
│  │  • SSTables: Immutable sorted files on disk                          │  │
│  │  • Levels: Organized hierarchy (L0 overlapping, L1+ non-overlapping) │  │
│  │                                                                       │  │
│  │  Write Path:                                                          │  │
│  │  1. Append to WAL (durability)                                        │  │
│  │  2. Insert into memtable (fast, in-memory)                           │  │
│  │  3. When full, flush to L0 SSTable                                   │  │
│  │  4. Background compaction merges and promotes files                  │  │
│  │                                                                       │  │
│  │  Read Path:                                                           │  │
│  │  1. Check memtable (newest data)                                     │  │
│  │  2. Check immutable memtables                                        │  │
│  │  3. Check L0 SSTables (all of them - overlapping)                    │  │
│  │  4. Check L1+ SSTables (binary search - non-overlapping)             │  │
│  │  5. Use Bloom filters to skip negative lookups                       │  │
│  │                                                                       │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                                                                             │
│  COMPACTION STRATEGIES                                                      │
│  ═════════════════════                                                      │
│                                                                             │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │                                                                       │  │
│  │  Size-Tiered (STCS):                                                  │  │
│  │  • Group similarly-sized files, merge when threshold reached         │  │
│  │  • Lower write amplification (~3-5x)                                 │  │
│  │  • Higher space amplification (~2x)                                  │  │
│  │  • Used by: Cassandra (default), HBase                               │  │
│  │                                                                       │  │
│  │  Leveled (LCS):                                                       │  │
│  │  • Fixed-size files organized into levels (10x size ratio)          │  │
│  │  • Higher write amplification (~10-30x)                              │  │
│  │  • Lower space amplification (~10%)                                  │  │
│  │  • Predictable read performance                                      │  │
│  │  • Used by: RocksDB, LevelDB                                         │  │
│  │                                                                       │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                                                                             │
│  BLOOM FILTERS                                                              │
│  ═════════════                                                              │
│                                                                             │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │                                                                       │  │
│  │  • Probabilistic data structure for set membership                   │  │
│  │  • Can definitively say "not in set" (no false negatives)            │  │
│  │  • May incorrectly say "in set" (false positives possible)           │  │
│  │  • ~10 bits per key = ~1% false positive rate                        │  │
│  │  • Dramatically reduces unnecessary disk reads                       │  │
│  │                                                                       │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                                                                             │
│  LSM-TREE vs B-TREE SUMMARY                                                 │
│  ══════════════════════════                                                 │
│                                                                             │
│  ┌──────────────────┬─────────────────────┬─────────────────────┐           │
│  │                  │ LSM-Tree            │ B-Tree              │           │
│  ├──────────────────┼─────────────────────┼─────────────────────┤           │
│  │ Write Speed      │ ★★★★★ (sequential) │ ★★★ (random)       │           │
│  │ Read Speed       │ ★★★ (variable)     │ ★★★★★ (predictable)│           │
│  │ Space Efficiency │ ★★★★ (with LCS)    │ ★★★ (~67% full)    │           │
│  │ Complexity       │ ★★★ (compaction)   │ ★★ (simpler)       │           │
│  │ Best For         │ Write-heavy         │ Read-heavy          │           │
│  └──────────────────┴─────────────────────┴─────────────────────┘           │
│                                                                             │
│  REAL-WORLD USAGE                                                           │
│  ════════════════                                                           │
│                                                                             │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │                                                                       │  │
│  │  LSM-Tree Based:                                                      │  │
│  │  • RocksDB (Facebook) - embedded storage engine                      │  │
│  │  • LevelDB (Google) - original implementation                        │  │
│  │  • Cassandra (Apache) - distributed wide-column store                │  │
│  │  • HBase (Apache) - Hadoop-based database                            │  │
│  │  • CockroachDB - distributed SQL (uses RocksDB/Pebble)               │  │
│  │  • TiDB/TiKV - distributed database                                  │  │
│  │                                                                       │  │
│  │  B-Tree Based:                                                        │  │
│  │  • PostgreSQL - traditional RDBMS                                    │  │
│  │  • MySQL/InnoDB - traditional RDBMS                                  │  │
│  │  • Oracle - enterprise RDBMS                                         │  │
│  │  • SQLite - embedded database                                        │  │
│  │                                                                       │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

**Next Chapter: [Chapter 8 - Distributed Systems Introduction](08-distributed-systems-intro.md)**
