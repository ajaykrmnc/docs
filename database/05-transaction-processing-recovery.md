# Chapter 5: Transaction Processing and Recovery

## Table of Contents
- [Buffer Pool Management](#buffer-pool-management)
- [Page Eviction Policies](#page-eviction-policies)
- [Write-Ahead Logging (WAL)](#write-ahead-logging-wal)
- [Log Record Structure](#log-record-structure)
- [Recovery Concepts](#recovery-concepts)
- [ARIES Recovery Algorithm](#aries-recovery-algorithm)
- [Checkpointing](#checkpointing)
- [Transaction Isolation](#transaction-isolation)
- [Concurrency Control Overview](#concurrency-control-overview)
- [Summary](#summary)

---

## Buffer Pool Management

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    THE BUFFER POOL                                          │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  The buffer pool is CRITICAL - it's the bridge between disk and memory     │
│                                                                             │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │                         APPLICATION                                   │  │
│  │                             │                                         │  │
│  │                             ▼                                         │  │
│  │  ┌─────────────────────────────────────────────────────────────────┐  │  │
│  │  │                     BUFFER POOL                                 │  │  │
│  │  │  ┌─────┬─────┬─────┬─────┬─────┬─────┬─────┬─────┬─────┬─────┐  │  │  │
│  │  │  │Frame│Frame│Frame│Frame│Frame│Frame│Frame│Frame│Frame│Frame│  │  │  │
│  │  │  │  0  │  1  │  2  │  3  │  4  │  5  │  6  │  7  │  8  │  9  │  │  │  │
│  │  │  │     │     │     │     │     │     │     │     │     │     │  │  │  │
│  │  │  │ P42 │ P17 │ P23 │ --- │ P89 │ P03 │ --- │ P12 │ P45 │ P78 │  │  │  │
│  │  │  │dirty│clean│dirty│empty│clean│dirty│empty│clean│dirty│clean│  │  │  │
│  │  │  └─────┴─────┴─────┴─────┴─────┴─────┴─────┴─────┴─────┴─────┘  │  │  │
│  │  │                                                                 │  │  │
│  │  │  Page Table: {42→0, 17→1, 23→2, 89→4, 3→5, 12→7, 45→8, 78→9}   │  │  │
│  │  └─────────────────────────────────────────────────────────────────┘  │  │
│  │                             │                                         │  │
│  │                             ▼                                         │  │
│  │  ┌─────────────────────────────────────────────────────────────────┐  │  │
│  │  │                      DISK STORAGE                               │  │  │
│  │  │  [Page 0][Page 1][Page 2][Page 3][Page 4] ... [Page N]          │  │  │
│  │  └─────────────────────────────────────────────────────────────────┘  │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                                                                             │
│  BUFFER POOL COMPONENTS                                                     │
│  ═══════════════════════                                                    │
│                                                                             │
│  1. FRAME ARRAY: Fixed-size slots in memory                                 │
│     • Each frame can hold one page                                          │
│     • Frame count = buffer pool size / page size                            │
│                                                                             │
│  2. PAGE TABLE: Maps page_id → frame_id                                     │
│     • Hash table for O(1) lookup                                            │
│     • Answers: "Is page X in memory? Where?"                                │
│                                                                             │
│  3. METADATA per frame:                                                     │
│     • dirty bit: Has page been modified?                                    │
│     • pin count: How many transactions using this page?                     │
│     • reference bit: Recently accessed? (for eviction)                      │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Page Operations

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    BUFFER POOL OPERATIONS                                   │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  FETCH PAGE (page_id)                                                       │
│  ═══════════════════                                                        │
│                                                                             │
│  1. Check page table                                                        │
│     ├─ Page in buffer? → return frame pointer, increment pin count          │
│     └─ Page not in buffer? → continue to step 2                             │
│                                                                             │
│  2. Find free frame                                                         │
│     ├─ Empty frame available? → use it                                      │
│     └─ No empty frame? → EVICT a page (see eviction policies)               │
│                                                                             │
│  3. If evicting dirty page                                                  │
│     └─ Write page to disk FIRST (flush)                                     │
│                                                                             │
│  4. Read requested page from disk into frame                                │
│                                                                             │
│  5. Update page table, set pin count = 1, return frame pointer              │
│                                                                             │
│                                                                             │
│  UNPIN PAGE (page_id, is_dirty)                                             │
│  ═════════════════════════════                                              │
│                                                                             │
│  1. Decrement pin count                                                     │
│  2. If is_dirty → set dirty bit                                             │
│  3. If pin count = 0 → page is eligible for eviction                        │
│                                                                             │
│                                                                             │
│  FLUSH PAGE (page_id)                                                       │
│  ═════════════════════                                                      │
│                                                                             │
│  1. Write page contents to disk                                             │
│  2. Clear dirty bit                                                         │
│  3. Update page LSN (Log Sequence Number)                                   │
│                                                                             │
│                                                                             │
│  PIN COUNT INVARIANT                                                        │
│  ═══════════════════                                                        │
│                                                                             │
│  • Pin count > 0: Page is being used, CANNOT be evicted                     │
│  • Pin count = 0: Page can be evicted if needed                             │
│  • Never evict a pinned page!                                               │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Page Eviction Policies

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    PAGE REPLACEMENT / EVICTION POLICIES                     │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  When buffer pool is full, which page to evict?                             │
│                                                                             │
│  1. LRU (Least Recently Used)                                               │
│  ═══════════════════════════                                                │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │  Access order: A, B, C, D, E, F (newest)                            │    │
│  │                                                                     │    │
│  │  LRU List:  HEAD ←→ F ←→ E ←→ D ←→ C ←→ B ←→ A ←→ TAIL              │    │
│  │                 ↑                                      ↑             │    │
│  │            Most recent                          Least recent        │    │
│  │                                                (evict first)        │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                             │
│  ✓ Simple to implement                                                      │
│  ✗ Sequential scan pollutes cache (reads entire table once)                 │
│  ✗ Expensive to maintain (update list on every access)                      │
│                                                                             │
│  2. CLOCK (Second-Chance)                                                   │
│  ═════════════════════════                                                  │
│                                                                             │
│  Approximates LRU with less overhead                                        │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                     │    │
│  │              ┌───────┐                                              │    │
│  │         ┌────│ ref=1 │────┐                                         │    │
│  │         │    └───────┘    │                                         │    │
│  │    ┌────┴───┐        ┌────┴───┐                                     │    │
│  │    │ ref=0  │        │ ref=1  │                                     │    │
│  │    └────┬───┘        └────┬───┘                                     │    │
│  │         │    ┌───────┐    │                                         │    │
│  │         └────│ ref=1 │◄───┘  ← clock hand                           │    │
│  │              └───────┘                                              │    │
│  │                                                                     │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                             │
│  Algorithm:                                                                 │
│  1. Clock hand sweeps through frames                                        │
│  2. If ref=1: Clear it (second chance), move hand                           │
│  3. If ref=0: Evict this page                                               │
│  4. On page access: Set ref=1                                               │
│                                                                             │
│  ✓ O(1) average case                                                        │
│  ✓ No list maintenance                                                      │
│  ✗ Worst case: full sweep (O(n))                                            │
│                                                                             │
│  3. LRU-K                                                                   │
│  ════════                                                                   │
│                                                                             │
│  Track last K accesses, evict based on K-th most recent                     │
│  LRU-2: Consider "backward K-distance" (time to 2nd-last access)            │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │  Page A: [t=100, t=50, t=10, ...]  K-distance = 50                  │    │
│  │  Page B: [t=90, t=5, ...]          K-distance = 85  ← evict first   │    │
│  │  Page C: [t=80, t=70, ...]         K-distance = 10                  │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                             │
│  ✓ Resistant to scan pollution                                              │
│  ✓ Distinguishes between hot and cold pages                                 │
│  ✗ More memory overhead (track K timestamps)                                │
│                                                                             │
│  4. 2Q (Two Queue)                                                          │
│  ══════════════════                                                         │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                     │    │
│  │   New pages → [A1 Queue (FIFO)] ─→ [Am Queue (LRU)]                 │    │
│  │                    │                     ↑                          │    │
│  │                    │   If accessed       │                          │    │
│  │                    │   while in A1  ─────┘                          │    │
│  │                    │                                                │    │
│  │                    └──→ Evict if not re-accessed                    │    │
│  │                                                                     │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                             │
│  • A1: probationary queue (FIFO), holds new pages                           │
│  • Am: main queue (LRU), holds "hot" pages                                  │
│  • Page promoted to Am on second access                                     │
│                                                                             │
│  ✓ Great scan resistance                                                    │
│  ✓ Used by PostgreSQL (with variations)                                     │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Write-Ahead Logging (WAL)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    WRITE-AHEAD LOGGING (WAL)                                │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  THE GOLDEN RULE OF WAL                                                     │
│  ═══════════════════════                                                    │
│                                                                             │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │                                                                       │  │
│  │   "Before ANY modification is written to the database,                │  │
│  │    the corresponding log record MUST be written to disk"              │  │
│  │                                                                       │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                                                                             │
│  WHY WAL?                                                                   │
│  ════════                                                                   │
│                                                                             │
│  Without WAL:                                                               │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │  Transaction: INSERT INTO accounts VALUES (100, 'Alice', 1000)      │    │
│  │                                                                     │    │
│  │  1. Modify page in buffer pool                                      │    │
│  │  2. ... (later) ...                                                 │    │
│  │  3. Write dirty page to disk                                        │    │
│  │                                                                     │    │
│  │       CRASH BETWEEN STEP 2 AND 3!                                   │    │
│  │       ↓                                                             │    │
│  │       Data lost! Transaction was "committed" but data gone!         │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                             │
│  With WAL:                                                                  │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │  1. Write log record: "INSERT (100, 'Alice', 1000) at page X"       │    │
│  │  2. FORCE log to disk (fsync)                                       │    │
│  │  3. Return "committed" to user                                      │    │
│  │  4. ... (later, lazily) ...                                         │    │
│  │  5. Write dirty page to disk                                        │    │
│  │                                                                     │    │
│  │       CRASH ANYTIME AFTER STEP 2?                                   │    │
│  │       ↓                                                             │    │
│  │       Replay log on recovery → Data restored!                       │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                             │
│  WAL BENEFITS                                                               │
│  ════════════                                                               │
│                                                                             │
│  1. DURABILITY: Committed transactions survive crashes                      │
│  2. ATOMICITY: Uncommitted transactions can be rolled back                  │
│  3. PERFORMANCE: Sequential log writes faster than random page writes       │
│  4. REPLICATION: Stream log to replicas for consistent copies               │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### WAL Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    WAL ARCHITECTURE                                         │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │                                                                       │  │
│  │    Transaction                                                        │  │
│  │        │                                                              │  │
│  │        ▼                                                              │  │
│  │   ┌────────────┐    ┌────────────────────────────────────────────┐    │  │
│  │   │ WAL Buffer │───▶│ WAL Files (on disk)                        │    │  │
│  │   │ (in memory)│    │ wal_000001 │ wal_000002 │ wal_000003 │ ... │    │  │
│  │   └────────────┘    └────────────────────────────────────────────┘    │  │
│  │        │                                                              │  │
│  │        │ (also modifies)                                              │  │
│  │        ▼                                                              │  │
│  │   ┌─────────────┐    ┌────────────────────────────────────────────┐   │  │
│  │   │ Buffer Pool │───▶│ Data Files (lazy write)                    │   │  │
│  │   │ (dirty pages│    │ base/12345/16384 (tables)                  │   │  │
│  │   └─────────────┘    └────────────────────────────────────────────┘   │  │
│  │                                                                       │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                                                                             │
│  LOG SEQUENCE NUMBER (LSN)                                                  │
│  ═════════════════════════                                                  │
│                                                                             │
│  Every log record has a unique, monotonically increasing LSN                │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │  LSN: 1001  │  LSN: 1002  │  LSN: 1003  │  LSN: 1004  │ ...        │    │
│  │  INSERT ... │  UPDATE ... │  DELETE ... │  COMMIT T1  │            │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                             │
│  Each PAGE also tracks its PAGE_LSN (LSN of last modification):             │
│                                                                             │
│  ┌────────────────────────────────────────┐                                 │
│  │ Page Header:                           │                                 │
│  │   page_lsn: 1003  ← Last log record    │                                 │
│  │                     that modified page │                                 │
│  └────────────────────────────────────────┘                                 │
│                                                                             │
│  FLUSHED_LSN: Highest LSN that has been flushed to disk                     │
│                                                                             │
│  RULE: Cannot flush page to disk until page_lsn <= flushed_lsn              │
│        (Must flush log before data!)                                        │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Log Record Structure

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    LOG RECORD TYPES AND STRUCTURE                           │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  PHYSICAL LOG RECORD (Most Common)                                          │
│  ══════════════════════════════════                                         │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │ Log Record:                                                         │    │
│  │ ┌─────────────────────────────────────────────────────────────────┐ │    │
│  │ │ LSN        │ 8 bytes │ Log Sequence Number                     │ │    │
│  │ │ prev_lsn   │ 8 bytes │ Previous LSN for this transaction       │ │    │
│  │ │ txn_id     │ 8 bytes │ Transaction ID                          │ │    │
│  │ │ type       │ 1 byte  │ INSERT/UPDATE/DELETE/COMMIT/ABORT/...   │ │    │
│  │ │ page_id    │ 8 bytes │ Which page was modified                 │ │    │
│  │ │ offset     │ 2 bytes │ Where on page                           │ │    │
│  │ │ length     │ 2 bytes │ How much data                           │ │    │
│  │ │ before_img │ variable│ Data BEFORE modification (for UNDO)     │ │    │
│  │ │ after_img  │ variable│ Data AFTER modification (for REDO)      │ │    │
│  │ └─────────────────────────────────────────────────────────────────┘ │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                             │
│  LOG RECORD TYPES                                                           │
│  ═════════════════                                                          │
│                                                                             │
│  Data Modification:                                                         │
│  • INSERT: New record added                                                 │
│  • UPDATE: Existing record modified                                         │
│  • DELETE: Record removed                                                   │
│                                                                             │
│  Transaction Control:                                                       │
│  • BEGIN: Transaction started                                               │
│  • COMMIT: Transaction completed successfully                               │
│  • ABORT: Transaction rolled back                                           │
│                                                                             │
│  Compensation (for rollback):                                               │
│  • CLR (Compensation Log Record): Records an UNDO operation                 │
│                                                                             │
│  Checkpoint:                                                                │
│  • BEGIN_CHECKPOINT: Checkpoint starting                                    │
│  • END_CHECKPOINT: Checkpoint complete, includes metadata                   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Recovery Concepts

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    RECOVERY FUNDAMENTALS                                    │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  CRASH SCENARIOS                                                            │
│  ═══════════════                                                            │
│                                                                             │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │                                                                       │  │
│  │  T1: ──────[BEGIN]──────[INSERT]──────[COMMIT]────────────────────── │  │
│  │                                                                       │  │
│  │  T2: ──────────[BEGIN]──────[UPDATE]──────[UPDATE]──────────────────  │  │
│  │                                                      ↑                │  │
│  │  T3: ────────────────[BEGIN]──────[DELETE]──────────│─[COMMIT]─────  │  │
│  │                                                      │                │  │
│  │                                                   CRASH               │  │
│  │                                                                       │  │
│  │  After recovery:                                                      │  │
│  │  • T1: REDO (committed before crash) ✓                                │  │
│  │  • T2: UNDO (never committed) ✗                                       │  │
│  │  • T3: REDO (committed before crash) ✓                                │  │
│  │                                                                       │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                                                                             │
│  STEAL vs NO-STEAL POLICY                                                   │
│  ═════════════════════════                                                  │
│                                                                             │
│  Can we write UNCOMMITTED changes to disk?                                  │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                     │    │
│  │  STEAL (Most databases use this):                                   │    │
│  │  ┌─────────┐                                                        │    │
│  │  │ Buffer  │  Dirty page with uncommitted                           │    │
│  │  │  Pool   │  changes CAN be written to disk                        │    │
│  │  └────┬────┘  (we "steal" the frame for other pages)                │    │
│  │       │                                                             │    │
│  │       ▼                                                             │    │
│  │  ┌─────────┐                                                        │    │
│  │  │  Disk   │  ⚠ Requires UNDO during recovery                       │    │
│  │  └─────────┘                                                        │    │
│  │                                                                     │    │
│  │  ✓ Better memory utilization                                        │    │
│  │  ✗ More complex recovery (need before-images)                       │    │
│  │                                                                     │    │
│  │  NO-STEAL:                                                          │    │
│  │  • Dirty pages stay pinned until commit                             │    │
│  │  • No UNDO needed (uncommitted never on disk)                       │    │
│  │  ✗ Can run out of buffer space                                      │    │
│  │                                                                     │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                             │
│  FORCE vs NO-FORCE POLICY                                                   │
│  ═════════════════════════                                                  │
│                                                                             │
│  Must we write ALL changes to disk at commit time?                          │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                     │    │
│  │  FORCE:                                                             │    │
│  │  • ALL dirty pages written to disk before commit returns            │    │
│  │  • No REDO needed (all committed changes on disk)                   │    │
│  │  ✗ SLOW commits (must wait for all I/O)                             │    │
│  │                                                                     │    │
│  │  NO-FORCE (Most databases use this):                                │    │
│  │  • Commit only requires LOG to be on disk                           │    │
│  │  • Data pages written lazily                                        │    │
│  │  ⚠ Requires REDO during recovery                                    │    │
│  │  ✓ FAST commits                                                     │    │
│  │                                                                     │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                             │
│  MOST DATABASES: STEAL + NO-FORCE                                           │
│  ─────────────────────────────────                                          │
│  • Best performance                                                         │
│  • Requires both UNDO and REDO during recovery                              │
│  • ARIES algorithm handles this!                                            │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## ARIES Recovery Algorithm

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    ARIES: Algorithms for Recovery and                       │
│                    Isolation Exploiting Semantics                           │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ARIES is THE standard recovery algorithm (IBM, 1992)                       │
│  Used by: PostgreSQL, MySQL/InnoDB, SQL Server, DB2, Oracle                 │
│                                                                             │
│  THREE PHASES OF RECOVERY                                                   │
│  ════════════════════════                                                   │
│                                                                             │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │                                                                       │  │
│  │   LOG FILE                                                            │  │
│  │   ┌──────────────────────────────────────────────────────────────┐   │  │
│  │   │  ... │ CKPT │ ... │ ... │ ... │ ... │ ... │ ... │ CRASH│    │   │  │
│  │   └──────────────────────────────────────────────────────────────┘   │  │
│  │         ↑                                                      ↑     │  │
│  │         │                                                      │     │  │
│  │         │            ┌───────────────────────────────┐         │     │  │
│  │         │            │    PHASE 1: ANALYSIS          │         │     │  │
│  │         └────────────│    Scan forward →             │─────────┘     │  │
│  │                      │    Build ATT and DPT          │               │  │
│  │                      └───────────────────────────────┘               │  │
│  │                                                                       │  │
│  │         ↑                                                      ↑     │  │
│  │         │            ┌───────────────────────────────┐         │     │  │
│  │         │            │    PHASE 2: REDO              │         │     │  │
│  │         └────────────│    Scan forward →             │─────────┘     │  │
│  │                      │    Repeat history             │               │  │
│  │                      └───────────────────────────────┘               │  │
│  │                                                                       │  │
│  │                                                      ↑               │  │
│  │                      ┌───────────────────────────────┐│              │  │
│  │                      │    PHASE 3: UNDO              ││              │  │
│  │                      │    Scan backward ←            │┘              │  │
│  │                      │    Rollback losers            │               │  │
│  │                      └───────────────────────────────┘               │  │
│  │                                                                       │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Phase 1: Analysis

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    ANALYSIS PHASE                                           │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  PURPOSE: Figure out database state at crash time                           │
│                                                                             │
│  BUILDS TWO DATA STRUCTURES:                                                │
│  ═══════════════════════════                                                │
│                                                                             │
│  1. ACTIVE TRANSACTION TABLE (ATT)                                          │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │  txn_id  │  status     │  last_lsn  │  undo_next_lsn                  │  │
│  ├──────────┼─────────────┼────────────┼─────────────────────────────────┤  │
│  │  T1      │  COMMITTED  │  1050      │  NULL                           │  │
│  │  T2      │  RUNNING    │  1045      │  1045  ← needs UNDO             │  │
│  │  T3      │  ABORTED    │  1040      │  1030  ← needs UNDO             │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                                                                             │
│  2. DIRTY PAGE TABLE (DPT)                                                  │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │  page_id  │  rec_lsn (Recovery LSN)                                   │  │
│  ├───────────┼───────────────────────────────────────────────────────────┤  │
│  │  P42      │  1020  ← First LSN that dirtied page since last flush     │  │
│  │  P17      │  1035                                                     │  │
│  │  P89      │  1025                                                     │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                                                                             │
│  ALGORITHM:                                                                 │
│  ──────────                                                                 │
│  1. Start from last checkpoint                                              │
│  2. Scan log forward to end                                                 │
│  3. For each log record:                                                    │
│     • If BEGIN → Add transaction to ATT                                     │
│     • If COMMIT/ABORT → Mark status in ATT                                  │
│     • If UPDATE → Add page to DPT if not present (rec_lsn = this LSN)       │
│                   Update last_lsn in ATT                                    │
│  4. Result: Know which txns to undo, which pages might need redo            │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Phase 2: Redo

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    REDO PHASE                                               │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  PURPOSE: Restore database to state at crash time ("Repeat History")        │
│                                                                             │
│  WHY REDO EVERYTHING?                                                       │
│  ═════════════════════                                                      │
│                                                                             │
│  • Even uncommitted transactions are redone!                                │
│  • Restores database to exact crash-time state                              │
│  • Simplifies recovery: can then cleanly undo losers                        │
│                                                                             │
│  ALGORITHM:                                                                 │
│  ──────────                                                                 │
│                                                                             │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │  For each log record (from smallest rec_lsn in DPT to end):           │  │
│  │                                                                       │  │
│  │  1. Is page in DPT?                                                   │  │
│  │     NO → Skip (page wasn't dirty)                                     │  │
│  │                                                                       │  │
│  │  2. Is log_record.LSN < page's rec_lsn?                               │  │
│  │     YES → Skip (effect already on disk before this log record)        │  │
│  │                                                                       │  │
│  │  3. Fetch page from disk                                              │  │
│  │                                                                       │  │
│  │  4. Is page_lsn >= log_record.LSN?                                    │  │
│  │     YES → Skip (effect already applied to this page)                  │  │
│  │                                                                       │  │
│  │  5. OTHERWISE: Apply the redo! (use after_image from log)             │  │
│  │                                                                       │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                                                                             │
│  KEY INSIGHT: page_lsn comparison ensures IDEMPOTENCE                       │
│  • Safe to crash during recovery and restart                                │
│  • Already-applied changes won't be re-applied                              │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Phase 3: Undo

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    UNDO PHASE                                               │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  PURPOSE: Rollback all uncommitted transactions ("Loser" transactions)      │
│                                                                             │
│  ALGORITHM:                                                                 │
│  ──────────                                                                 │
│                                                                             │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │  1. Build ToUndo set = {last_lsn of each loser txn from ATT}          │  │
│  │                                                                       │  │
│  │  2. While ToUndo is not empty:                                        │  │
│  │     a. Pick largest LSN from ToUndo                                   │  │
│  │     b. Fetch log record                                               │  │
│  │     c. If CLR (Compensation Log Record):                              │  │
│  │        - Add undo_next_lsn to ToUndo (if not null)                    │  │
│  │     d. If regular UPDATE:                                             │  │
│  │        - UNDO the operation (use before_image)                        │  │
│  │        - Write CLR to log (records that we undid this)                │  │
│  │        - Add prev_lsn to ToUndo                                       │  │
│  │     e. If BEGIN record:                                               │  │
│  │        - Write ABORT record to log                                    │  │
│  │        - Remove this txn from processing                              │  │
│  │                                                                       │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                                                                             │
│  COMPENSATION LOG RECORDS (CLR)                                             │
│  ══════════════════════════════                                             │
│                                                                             │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │                                                                       │  │
│  │  Original:  LSN=100  UPDATE page P42, offset 10: "A" → "B"            │  │
│  │                                                                       │  │
│  │  CLR:       LSN=200  CLR for LSN=100                                  │  │
│  │                      undo_next_lsn = 95 (prev of original)            │  │
│  │                      "B" → "A" (reverses the change)                  │  │
│  │                                                                       │  │
│  │  Purpose:                                                             │  │
│  │  • CLRs are NEVER undone (only redone if needed)                      │  │
│  │  • undo_next_lsn lets us skip already-undone work after crash         │  │
│  │  • Ensures bounded recovery time                                      │  │
│  │                                                                       │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Checkpointing

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    CHECKPOINTING                                            │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  WHY CHECKPOINT?                                                            │
│  ═══════════════                                                            │
│                                                                             │
│  Without checkpoints:                                                       │
│  • Recovery must scan ENTIRE log from beginning                             │
│  • Could be gigabytes of log records                                        │
│  • Recovery takes forever!                                                  │
│                                                                             │
│  With checkpoints:                                                          │
│  • Recovery starts from last checkpoint                                     │
│  • Bounded recovery time                                                    │
│                                                                             │
│  TYPES OF CHECKPOINTS                                                       │
│  ════════════════════                                                       │
│                                                                             │
│  1. CONSISTENT CHECKPOINT (Naive)                                           │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │  1. Stop accepting new transactions                                   │  │
│  │  2. Wait for all active transactions to finish                        │  │
│  │  3. Flush ALL dirty pages to disk                                     │  │
│  │  4. Write checkpoint record                                           │  │
│  │  5. Resume transactions                                               │  │
│  │                                                                       │  │
│  │  ✗ BLOCKS ALL WORK! Unacceptable for production.                      │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                                                                             │
│  2. FUZZY CHECKPOINT (ARIES-style)                                          │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │  1. Write BEGIN_CHECKPOINT record                                     │  │
│  │  2. While system keeps running:                                       │  │
│  │     - Snapshot ATT (Active Transaction Table)                         │  │
│  │     - Snapshot DPT (Dirty Page Table)                                 │  │
│  │  3. Write END_CHECKPOINT record with ATT and DPT                      │  │
│  │  4. Update master record to point to BEGIN_CHECKPOINT                 │  │
│  │                                                                       │  │
│  │  ✓ NON-BLOCKING! System keeps processing transactions                 │  │
│  │  ✓ Fuzzy = checkpoint state might not reflect exact point in time     │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                                                                             │
│  CHECKPOINT RECORD CONTENTS                                                 │
│  ══════════════════════════                                                 │
│                                                                             │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │  END_CHECKPOINT Record:                                               │  │
│  │  ┌────────────────────────────────────────────────────────────────┐   │  │
│  │  │ ATT Snapshot:                                                  │   │  │
│  │  │   T1: status=RUNNING, last_lsn=1050                            │   │  │
│  │  │   T2: status=RUNNING, last_lsn=1045                            │   │  │
│  │  │                                                                │   │  │
│  │  │ DPT Snapshot:                                                  │   │  │
│  │  │   P42: rec_lsn=1020                                            │   │  │
│  │  │   P17: rec_lsn=1035                                            │   │  │
│  │  │   P89: rec_lsn=1025                                            │   │  │
│  │  └────────────────────────────────────────────────────────────────┘   │  │
│  │                                                                       │  │
│  │  This lets ANALYSIS phase start with these tables instead of empty   │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                                                                             │
│  CHECKPOINT FREQUENCY                                                       │
│  ════════════════════                                                       │
│                                                                             │
│  Trade-off:                                                                 │
│  • More frequent → Faster recovery, but more I/O overhead                   │
│  • Less frequent → Less overhead, but slower recovery                       │
│                                                                             │
│  Typical triggers:                                                          │
│  • Time-based: Every N minutes                                              │
│  • Size-based: After N MB of WAL written                                    │
│  • Combined: Whichever comes first                                          │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Transaction Isolation

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    TRANSACTION ISOLATION LEVELS                             │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ACID PROPERTIES REMINDER                                                   │
│  ════════════════════════                                                   │
│                                                                             │
│  A - Atomicity:   All or nothing                                            │
│  C - Consistency: Valid state to valid state                                │
│  I - Isolation:   Concurrent txns don't interfere (focus of this section)   │
│  D - Durability:  Committed = survives crash                                │
│                                                                             │
│  READ PHENOMENA (Anomalies)                                                 │
│  ══════════════════════════                                                 │
│                                                                             │
│  1. DIRTY READ                                                              │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │  T1: UPDATE balance SET amt=100 WHERE id=1;                           │  │
│  │  T2:                   SELECT amt FROM balance WHERE id=1; → 100      │  │
│  │  T1: ROLLBACK;                                                        │  │
│  │                                                                       │  │
│  │  T2 read uncommitted data that was never committed!                   │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                                                                             │
│  2. NON-REPEATABLE READ                                                     │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │  T1: SELECT amt FROM balance WHERE id=1; → 100                        │  │
│  │  T2:                   UPDATE balance SET amt=200 WHERE id=1; COMMIT; │  │
│  │  T1: SELECT amt FROM balance WHERE id=1; → 200  (different!)          │  │
│  │                                                                       │  │
│  │  Same query, different results within same transaction                │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                                                                             │
│  3. PHANTOM READ                                                            │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │  T1: SELECT * FROM orders WHERE status='pending'; → 5 rows            │  │
│  │  T2:           INSERT INTO orders VALUES (..., 'pending'); COMMIT;    │  │
│  │  T1: SELECT * FROM orders WHERE status='pending'; → 6 rows (phantom!) │  │
│  │                                                                       │  │
│  │  New rows appeared that match the query predicate                     │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                                                                             │
│  ISOLATION LEVELS (SQL Standard)                                            │
│  ═══════════════════════════════                                            │
│                                                                             │
│  ┌───────────────────┬─────────────┬──────────────────┬─────────────────┐   │
│  │ Isolation Level   │ Dirty Read  │ Non-Repeatable   │ Phantom Read    │   │
│  │                   │             │ Read             │                 │   │
│  ├───────────────────┼─────────────┼──────────────────┼─────────────────┤   │
│  │ READ UNCOMMITTED  │ Possible    │ Possible         │ Possible        │   │
│  │ READ COMMITTED    │ Prevented   │ Possible         │ Possible        │   │
│  │ REPEATABLE READ   │ Prevented   │ Prevented        │ Possible        │   │
│  │ SERIALIZABLE      │ Prevented   │ Prevented        │ Prevented       │   │
│  └───────────────────┴─────────────┴──────────────────┴─────────────────┘   │
│                                                                             │
│  COMMON DEFAULTS:                                                           │
│  • PostgreSQL: READ COMMITTED                                               │
│  • MySQL/InnoDB: REPEATABLE READ (but with gap locks prevents phantoms)     │
│  • SQL Server: READ COMMITTED                                               │
│  • Oracle: READ COMMITTED                                                   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Concurrency Control Overview

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    CONCURRENCY CONTROL MECHANISMS                           │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  How do we achieve isolation while allowing concurrency?                    │
│                                                                             │
│  1. TWO-PHASE LOCKING (2PL)                                                 │
│  ══════════════════════════                                                 │
│                                                                             │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │                                                                       │  │
│  │   Transaction Lifetime:                                               │  │
│  │                                                                       │  │
│  │   │ locks │                                                           │  │
│  │   │ held  │                                                           │  │
│  │   │       │      ┌──────────────┐                                     │  │
│  │   │       │     /│              │\                                    │  │
│  │   │       │    / │              │ \                                   │  │
│  │   │       │   /  │              │  \                                  │  │
│  │   │       │  /   │              │   \                                 │  │
│  │   │       │ /    │              │    \                                │  │
│  │   └───────┴──────┴──────────────┴─────┴───────────▶ time              │  │
│  │           GROWING   LOCK POINT     SHRINKING                          │  │
│  │           PHASE                    PHASE                              │  │
│  │                                                                       │  │
│  │   RULE: Once you release ANY lock, cannot acquire new locks           │  │
│  │                                                                       │  │
│  │   Lock Types:                                                         │  │
│  │   • S-lock (Shared): For reading, multiple readers OK                 │  │
│  │   • X-lock (Exclusive): For writing, only one holder                  │  │
│  │                                                                       │  │
│  │   Compatibility:                                                      │  │
│  │   ┌───────┬───────┬───────┐                                           │  │
│  │   │       │   S   │   X   │                                           │  │
│  │   ├───────┼───────┼───────┤                                           │  │
│  │   │   S   │  ✓    │  ✗    │                                           │  │
│  │   │   X   │  ✗    │  ✗    │                                           │  │
│  │   └───────┴───────┴───────┘                                           │  │
│  │                                                                       │  │
│  │   ⚠ Problem: DEADLOCKS!                                               │  │
│  │   T1: holds lock on A, wants lock on B                                │  │
│  │   T2: holds lock on B, wants lock on A                                │  │
│  │   → Detect and abort one transaction                                  │  │
│  │                                                                       │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                                                                             │
│  2. MULTIVERSION CONCURRENCY CONTROL (MVCC)                                 │
│  ═══════════════════════════════════════════                                │
│                                                                             │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │                                                                       │  │
│  │   Keep multiple versions of data!                                     │  │
│  │                                                                       │  │
│  │   ┌──────────────────────────────────────────────────────────────┐    │  │
│  │   │ Row "id=1":                                                  │    │  │
│  │   │                                                              │    │  │
│  │   │ Version 1: amt=100, created by T1, visible to T1-T10         │    │  │
│  │   │     ↓                                                        │    │  │
│  │   │ Version 2: amt=150, created by T5, visible to T5-T20         │    │  │
│  │   │     ↓                                                        │    │  │
│  │   │ Version 3: amt=200, created by T15, visible to T15+          │    │  │
│  │   │                                                              │    │  │
│  │   └──────────────────────────────────────────────────────────────┘    │  │
│  │                                                                       │  │
│  │   Each transaction sees appropriate version based on snapshot         │  │
│  │                                                                       │  │
│  │   Benefits:                                                           │  │
│  │   • Readers don't block writers                                       │  │
│  │   • Writers don't block readers                                       │  │
│  │   • No deadlocks for read operations                                  │  │
│  │                                                                       │  │
│  │   Used by: PostgreSQL, MySQL/InnoDB, Oracle, SQL Server (snapshot)    │  │
│  │                                                                       │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                                                                             │
│  3. OPTIMISTIC CONCURRENCY CONTROL (OCC)                                    │
│  ═══════════════════════════════════════                                    │
│                                                                             │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │                                                                       │  │
│  │   Assume conflicts are rare. Validate at commit time.                 │  │
│  │                                                                       │  │
│  │   Three Phases:                                                       │  │
│  │   1. READ: Execute transaction, track read/write sets                 │  │
│  │   2. VALIDATE: Check for conflicts with concurrent transactions       │  │
│  │   3. WRITE: If valid, commit; otherwise abort and retry               │  │
│  │                                                                       │  │
│  │   Best for: Read-heavy workloads with low contention                  │  │
│  │                                                                       │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Summary

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    CHAPTER 5 SUMMARY                                        │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  BUFFER POOL                                                                │
│  ───────────                                                                │
│  • Bridge between disk and memory                                           │
│  • Frame array + page table + metadata (dirty bit, pin count)               │
│  • Eviction policies: LRU, CLOCK, LRU-K, 2Q                                 │
│  • Never evict pinned pages!                                                │
│                                                                             │
│  WRITE-AHEAD LOGGING                                                        │
│  ───────────────────                                                        │
│  • Log before data: ensures durability                                      │
│  • LSN: unique identifier for each log record                               │
│  • page_lsn: tracks which changes applied to page                           │
│  • REDO + UNDO information in log records                                   │
│                                                                             │
│  ARIES RECOVERY                                                             │
│  ──────────────                                                             │
│  • Analysis: Build ATT (transactions) and DPT (dirty pages)                 │
│  • Redo: Repeat history to crash-time state                                 │
│  • Undo: Rollback uncommitted transactions                                  │
│  • CLRs: Ensure bounded recovery, idempotent operations                     │
│                                                                             │
│  CHECKPOINTING                                                              │
│  ─────────────                                                              │
│  • Limits recovery time                                                     │
│  • Fuzzy checkpoints: non-blocking, snapshot ATT/DPT                        │
│                                                                             │
│  ISOLATION LEVELS                                                           │
│  ────────────────                                                           │
│  • Read anomalies: dirty read, non-repeatable read, phantom                 │
│  • Levels: READ UNCOMMITTED → READ COMMITTED → REPEATABLE READ              │
│            → SERIALIZABLE                                                   │
│                                                                             │
│  CONCURRENCY CONTROL                                                        │
│  ───────────────────                                                        │
│  • 2PL: Growing/shrinking lock phases, deadlock possible                    │
│  • MVCC: Multiple versions, readers don't block writers                     │
│  • OCC: Optimistic, validate at commit                                      │
│                                                                             │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │                                                                       │  │
│  │   KEY INSIGHT: WAL + ARIES + MVCC = Modern Database Recovery          │  │
│  │                                                                       │  │
│  │   This combination enables:                                           │  │
│  │   • Fast commits (no-force)                                           │  │
│  │   • Good memory utilization (steal)                                   │  │
│  │   • Crash recovery                                                    │  │
│  │   • High concurrency                                                  │  │
│  │                                                                       │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

