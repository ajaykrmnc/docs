# Chapter 3: B-Tree Variants - Optimizations for Different Workloads

## Table of Contents

1. [B*-Trees: Higher Fill Factor](#b-trees-higher-fill-factor)
2. [B-link Trees: Better Concurrency](#b-link-trees-better-concurrency)
3. [Copy-on-Write B-Trees](#copy-on-write-b-trees)
4. [Fractal Trees and Buffer Trees](#fractal-trees-and-buffer-trees)
5. [Prefix and Suffix Compression](#prefix-and-suffix-compression)
6. [Adaptive Indexing](#adaptive-indexing)

---

## B*-Trees: Higher Fill Factor

Standard B-Trees guarantee only 50% minimum fill. B*-Trees improve this to ~67%.

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    B*-TREE: DELAYED SPLITS                                   │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  KEY INNOVATION: Delay splits by redistributing to siblings first          │
│                                                                             │
│  STANDARD B-TREE SPLIT                                                      │
│  ══════════════════════                                                     │
│                                                                             │
│  Node is full → Split immediately                                           │
│                                                                             │
│      [10|20|30|40] → FULL!                                                  │
│            │                                                                │
│            ▼ Split                                                          │
│      [10|20]  [30|40]     (each 50% full)                                   │
│                                                                             │
│  B*-TREE APPROACH                                                           │
│  ═════════════════                                                          │
│                                                                             │
│  Step 1: Try to redistribute to sibling                                     │
│                                                                             │
│  Before insert 35:                                                          │
│      Parent: [25 | 50]                                                      │
│             /    |    \                                                     │
│      [10|20] [30|40|45] [60|70]                                             │
│                  ↑                                                          │
│                 FULL                                                        │
│                                                                             │
│  Instead of split, redistribute:                                            │
│      Parent: [25 | 45]                                                      │
│             /    |    \                                                     │
│      [10|20] [30|35|40] [45|60|70]                                          │
│                                                                             │
│  Step 2: Only split when both siblings are full                             │
│                                                                             │
│  When node AND sibling both full:                                           │
│      Split 2 nodes into 3 nodes                                             │
│      [A|A|A|A] + [B|B|B|B] → [X|X|X] [Y|Y|Y] [Z|Z|Z]                         │
│                                                                             │
│  RESULT: Minimum fill factor = 2/3 (67%) instead of 1/2 (50%)               │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### B*-Tree Trade-offs

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    B*-TREE ANALYSIS                                          │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ADVANTAGES                                                                 │
│  ══════════                                                                 │
│  ✓ Higher space utilization (67% vs 50% minimum)                            │
│  ✓ Fewer nodes → potentially lower tree height                              │
│  ✓ Better cache utilization                                                 │
│  ✓ Less wasted disk space                                                   │
│                                                                             │
│  DISADVANTAGES                                                              │
│  ═════════════                                                              │
│  ✗ More complex insertion algorithm                                         │
│  ✗ May need to read/write sibling during insert                             │
│  ✗ Harder to implement concurrency correctly                                │
│  ✗ Redistribution may touch more pages                                      │
│                                                                             │
│  WHEN TO USE                                                                │
│  ═══════════                                                                │
│  • Read-heavy workloads (space savings help caching)                        │
│  • Space-constrained environments                                           │
│  • When concurrent access is limited                                        │
│                                                                             │
│  REAL-WORLD USAGE                                                           │
│  ════════════════                                                           │
│  • Less common than standard B+Trees                                        │
│  • Some file systems (NTFS uses B+ with delayed splits)                     │
│  • Embedded databases with limited memory                                   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## B-link Trees: Better Concurrency

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    THE CONCURRENT B-TREE PROBLEM                             │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  SCENARIO: Concurrent insert and search                                     │
│                                                                             │
│  Thread A: INSERT 35 (causes split)                                         │
│  Thread B: SEARCH for 40                                                    │
│                                                                             │
│  INITIAL STATE                                                              │
│  ═════════════                                                              │
│          [30 | 50]                                                          │
│         /    |    \                                                         │
│      [20]  [35|40|45] [60]                                                  │
│               ↑                                                             │
│    Thread A inserts 38 here (causes split)                                  │
│                                                                             │
│  PROBLEM: Race condition during split                                       │
│  ════════════════════════════════════                                       │
│                                                                             │
│  Time 1: Thread B reads parent [30|50], decides to go to middle child       │
│  Time 2: Thread A splits [35|38|40|45] into [35|38] and [40|45]             │
│  Time 3: Thread A updates parent to [30|40|50]                              │
│  Time 4: Thread B reads middle child... but finds [35|38], not 40!          │
│                                                                             │
│  Thread B went to the WRONG leaf!                                           │
│                                                                             │
│  TRADITIONAL SOLUTION: Lock from root down                                  │
│  • Severely limits concurrency                                              │
│  • Hot path becomes bottleneck                                              │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### B-link Tree Structure

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    B-LINK TREE SOLUTION                                      │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  KEY INNOVATION: Right-link pointers + high-key markers                     │
│                                                                             │
│  STANDARD B+TREE NODE                                                       │
│  ┌────────────────────────────────────────┐                                 │
│  │ Keys: [K₁|K₂|K₃]  Ptrs: [P₀|P₁|P₂|P₃] │                                 │
│  └────────────────────────────────────────┘                                 │
│                                                                             │
│  B-LINK TREE NODE                                                           │
│  ┌────────────────────────────────────────────────────────────┐             │
│  │ High-Key│ Keys: [K₁|K₂|K₃]  Ptrs: [P₀|P₁|P₂|P₃] │ Right →│             │
│  └────────────────────────────────────────────────────────────┘             │
│                                                                             │
│  NEW FIELDS:                                                                │
│  • High-Key: Maximum key that CAN be in this subtree                        │
│  • Right-Link: Pointer to right sibling at same level                       │
│                                                                             │
│  VISUALIZATION                                                              │
│  ═════════════                                                              │
│                                                                             │
│         ┌─────────────────┐                                                 │
│         │ HK:∞ [30|50]    │ ────────────▶ NULL                              │
│         └────────┬────────┘                                                 │
│                  │                                                          │
│      ┌───────────┼───────────┐                                              │
│      │           │           │                                              │
│      ▼           ▼           ▼                                              │
│  ┌───────┐   ┌───────┐   ┌───────┐                                          │
│  │HK:30  │──▶│HK:50  │──▶│HK:∞   │──▶ NULL                                  │
│  │[10|20]│   │[35|40]│   │[60|70]│                                          │
│  └───────┘   └───────┘   └───────┘                                          │
│                                                                             │
│  High-Key tells you: "If your search key > HK, follow right-link"           │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### B-link Tree Algorithm

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    B-LINK TREE SEARCH ALGORITHM                              │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  SEARCH(key):                                                               │
│  ════════════                                                               │
│                                                                             │
│  1. current = root                                                          │
│  2. WHILE current is not a leaf:                                            │
│       a. Read current node                                                  │
│       b. IF key > high_key(current):                                        │
│            current = right_link(current)    // Move right!                  │
│            GOTO 2a                          // Re-read                      │
│       c. ELSE:                                                              │
│            current = child pointer for key  // Move down                    │
│  3. WHILE key > high_key(current):          // May need to move right       │
│       current = right_link(current)         // at leaf level too            │
│  4. RETURN search within current leaf                                       │
│                                                                             │
│  KEY INSIGHT: If we land in wrong node due to concurrent split,             │
│               we detect it (key > high_key) and move right!                 │
│                                                                             │
│  EXAMPLE: Search for 40 during concurrent split                             │
│  ═══════════════════════════════════════════════                            │
│                                                                             │
│  Before split:  [35|38|40|45] with HK=50                                    │
│  During split:  [35|38] HK=38 ──▶ [40|45] HK=50                             │
│                                                                             │
│  Thread B lands on [35|38]:                                                 │
│  - Search key 40 > high_key 38                                              │
│  - Follow right-link to [40|45]                                             │
│  - Search key 40 ≤ high_key 50                                              │
│  - Search in this node → FOUND!                                             │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Safe vs Unsafe Operations

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    B-LINK TREE LOCK COUPLING                                 │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  LOCK COUPLING (Crabbing)                                                   │
│  ════════════════════════                                                   │
│                                                                             │
│  Basic idea: Hold lock on parent until child is locked                      │
│                                                                             │
│  Traditional B-Tree:                                                        │
│  • Must hold locks from root to leaf (pessimistic)                          │
│  • Or hold latches and restart if split needed                              │
│                                                                             │
│  B-link Tree advantage:                                                     │
│  • Only need to lock ONE node at a time                                     │
│  • Right-links provide recovery path                                        │
│                                                                             │
│  OPERATION CLASSIFICATION                                                   │
│  ═════════════════════════                                                  │
│                                                                             │
│  ┌─────────────┬────────────────────────────────────────────────────┐       │
│  │ Operation   │ Locking Strategy                                   │       │
│  ├─────────────┼────────────────────────────────────────────────────┤       │
│  │ Search      │ No locks needed! Just read + follow right-links    │       │
│  │ Insert      │ Lock only the leaf being modified                  │       │
│  │ Split       │ Lock node + new sibling + parent (3 nodes max)     │       │
│  │ Delete      │ Lock affected nodes                                │       │
│  └─────────────┴────────────────────────────────────────────────────┘       │
│                                                                             │
│  SPLIT SEQUENCE (Lock-free for readers!)                                    │
│  ═══════════════════════════════════════                                    │
│                                                                             │
│  1. Create new node with high keys                                          │
│  2. Set new node's right-link to old node's right-link                      │
│  3. Set new node's high-key to old node's high-key                          │
│  4. Atomically update old node's high-key and right-link                    │
│  5. Insert separator in parent (may need to wait/retry)                     │
│                                                                             │
│  At any point, readers can still navigate correctly!                        │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### B-link Tree Benefits Summary

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    B-LINK TREE ANALYSIS                                      │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ADVANTAGES                                                                 │
│  ══════════                                                                 │
│  ✓ Lock-free reads (readers never block)                                    │
│  ✓ Minimal locking for writes (single node at a time)                       │
│  ✓ No deadlocks (always acquire locks in one direction)                     │
│  ✓ Split operations don't block readers                                     │
│  ✓ Recovery is simpler (incomplete splits are detectable)                   │
│                                                                             │
│  DISADVANTAGES                                                              │
│  ═════════════                                                              │
│  ✗ Extra storage per node (high-key + right-link)                           │
│  ✗ Readers may need to traverse right-links (extra I/O)                     │
│  ✗ More complex implementation                                              │
│  ✗ Right-link traversal adds latency in worst case                          │
│                                                                             │
│  REAL-WORLD USAGE                                                           │
│  ════════════════                                                           │
│  • PostgreSQL uses B-link trees for its indexes                             │
│  • Many modern database systems adopt this approach                         │
│  • Lehman & Yao paper (1981) - foundational algorithm                       │
│                                                                             │
│  PERFORMANCE COMPARISON                                                     │
│  ══════════════════════                                                     │
│                                                                             │
│  Scenario              │ Traditional │ B-link Tree                          │
│  ──────────────────────┼─────────────┼──────────────────────                │
│  Read-heavy workload   │ Contention  │ Excellent (lock-free)                │
│  Write-heavy workload  │ Bottleneck  │ Good (minimal locks)                 │
│  Mixed workload        │ Poor        │ Very Good                            │
│  High concurrency      │ Degrades    │ Scales well                          │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Copy-on-Write B-Trees

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    COPY-ON-WRITE (COW) B-TREES                               │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  KEY IDEA: Never modify pages in place - always create new versions         │
│                                                                             │
│  TRADITIONAL UPDATE                                                         │
│  ══════════════════                                                         │
│                                                                             │
│  Page on disk: [A|B|C|D]                                                    │
│        │                                                                    │
│        ▼ Update B to B'                                                     │
│  Page on disk: [A|B'|C|D]  (same location, modified in place)               │
│                                                                             │
│  COPY-ON-WRITE UPDATE                                                       │
│  ════════════════════                                                       │
│                                                                             │
│  Page at loc 100: [A|B|C|D]                                                 │
│        │                                                                    │
│        ▼ Update B to B'                                                     │
│  NEW page at loc 200: [A|B'|C|D]  (new location, original unchanged)        │
│                                                                             │
│  But wait... parent points to old location!                                 │
│  → Must also copy parent with updated pointer                               │
│  → And grandparent... up to root!                                           │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### COW B-Tree Update Process

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    COW UPDATE PROPAGATION                                    │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  BEFORE UPDATE (insert key 35)                                              │
│  ═════════════════════════════                                              │
│                                                                             │
│  Root Pointer ──▶ [Root: 30|60]  (Page 1)                                   │
│                      /      \                                               │
│               [10|20]      [40|50]  (Pages 2, 3)                            │
│                             ▲                                               │
│                             │                                               │
│                     Insert 35 here                                          │
│                                                                             │
│  STEP 1: Copy leaf with modification                                        │
│  ═══════════════════════════════════                                        │
│                                                                             │
│  Page 3: [40|50]     (unchanged, still valid)                               │
│  Page 4: [35|40|50]  (NEW - copy with 35 inserted)                          │
│                                                                             │
│  STEP 2: Copy parent with new pointer                                       │
│  ════════════════════════════════════                                       │
│                                                                             │
│  Page 1: [30|60] → P2, P3  (unchanged)                                      │
│  Page 5: [30|60] → P2, P4  (NEW - copy with updated pointer)                │
│                                                                             │
│  STEP 3: Atomically update root pointer                                     │
│  ═══════════════════════════════════════                                    │
│                                                                             │
│  Root Pointer: 1 → 5  (single atomic write!)                                │
│                                                                             │
│  AFTER UPDATE                                                               │
│  ════════════                                                               │
│                                                                             │
│  Old tree (still accessible!):                                              │
│     [Root: 30|60] → [10|20], [40|50]                                        │
│                                                                             │
│  New tree (current):                                                        │
│     [Root: 30|60] → [10|20], [35|40|50]                                     │
│                         │                                                   │
│                    (shared - not copied!)                                   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### COW B-Tree Benefits

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    COW B-TREE ANALYSIS                                       │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ADVANTAGES                                                                 │
│  ══════════                                                                 │
│                                                                             │
│  1. ATOMIC COMMITS                                                          │
│     • Single pointer update makes entire transaction visible                │
│     • No partial updates visible (all or nothing)                           │
│     • Crash recovery is trivial                                             │
│                                                                             │
│  2. FREE SNAPSHOTS                                                          │
│     • Old root = point-in-time snapshot                                     │
│     • Just keep old root pointer around                                     │
│     • Perfect for MVCC (Multi-Version Concurrency Control)                  │
│                                                                             │
│  3. NO WRITE-AHEAD LOG NEEDED                                               │
│     • Old pages are never modified                                          │
│     • Old version is always consistent                                      │
│     • Can recover by reverting to old root                                  │
│                                                                             │
│  4. READERS NEVER BLOCKED                                                   │
│     • Readers use consistent snapshot                                       │
│     • Writers create new version independently                              │
│     • No locks needed for reads                                             │
│                                                                             │
│  DISADVANTAGES                                                              │
│  ═════════════                                                              │
│                                                                             │
│  1. WRITE AMPLIFICATION                                                     │
│     • Modifying leaf requires copying path to root                          │
│     • O(log N) pages written per update                                     │
│     • Not ideal for write-heavy workloads                                   │
│                                                                             │
│  2. GARBAGE COLLECTION                                                      │
│     • Old pages must be reclaimed                                           │
│     • Need to track which pages are still referenced                        │
│     • Adds complexity and overhead                                          │
│                                                                             │
│  3. FRAGMENTATION                                                           │
│     • Sequential data becomes scattered on disk                             │
│     • May hurt range scan performance over time                             │
│                                                                             │
│  REAL-WORLD USAGE                                                           │
│  ════════════════                                                           │
│  • LMDB (Lightning Memory-Mapped Database)                                  │
│  • Btrfs file system                                                        │
│  • CouchDB (append-only B-trees)                                            │
│  • Apple APFS file system                                                   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Fractal Trees and Buffer Trees

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    THE WRITE AMPLIFICATION PROBLEM                           │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  B-TREE RANDOM WRITE PATTERN                                                │
│  ═══════════════════════════                                                │
│                                                                             │
│  Insert keys: 5, 100, 42, 78, 3, 99, 50, 12, ...                            │
│                                                                             │
│  Each insert:                                                               │
│  1. Read root page (possibly cached)                                        │
│  2. Read internal pages down to leaf                                        │
│  3. Write modified leaf page                                                │
│  4. Possibly write split pages                                              │
│                                                                             │
│  Problem: RANDOM I/O for each insert                                        │
│                                                                             │
│  For N inserts: O(N × log N) random I/Os                                    │
│                                                                             │
│  With HDDs: ~100 random writes/sec                                          │
│  1 million inserts = 10,000+ seconds!                                       │
│                                                                             │
│  SEQUENTIAL vs RANDOM I/O                                                   │
│  ═════════════════════════                                                  │
│                                                                             │
│  ┌─────────────────────┬───────────────┬───────────────┐                    │
│  │ Operation           │ HDD           │ SSD           │                    │
│  ├─────────────────────┼───────────────┼───────────────┤                    │
│  │ Sequential Write    │ ~100 MB/s     │ ~500 MB/s     │                    │
│  │ Random Write        │ ~1 MB/s       │ ~100 MB/s     │                    │
│  │ Ratio               │ 100x          │ 5x            │                    │
│  └─────────────────────┴───────────────┴───────────────┘                    │
│                                                                             │
│  KEY INSIGHT: Batch random writes into sequential writes                    │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Buffer Tree Concept

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    BUFFER TREE STRUCTURE                                     │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  KEY INNOVATION: Each internal node has a buffer for pending operations     │
│                                                                             │
│  STANDARD B-TREE NODE                                                       │
│  ┌─────────────────────────────────────────────────────────────┐            │
│  │ Keys: [K₁|K₂|K₃]   Pointers: [P₀|P₁|P₂|P₃]                 │            │
│  └─────────────────────────────────────────────────────────────┘            │
│                                                                             │
│  BUFFER TREE NODE                                                           │
│  ┌─────────────────────────────────────────────────────────────┐            │
│  │ Keys: [K₁|K₂|K₃]   Pointers: [P₀|P₁|P₂|P₃]                 │            │
│  ├─────────────────────────────────────────────────────────────┤            │
│  │ Buffer: [op₁|op₂|op₃|op₄|op₅|...|opₙ]                      │            │
│  │         (pending inserts, updates, deletes)                 │            │
│  └─────────────────────────────────────────────────────────────┘            │
│                                                                             │
│  VISUALIZATION                                                              │
│  ═════════════                                                              │
│                                                                             │
│           ┌─────────────────────────────────────┐                           │
│           │ [30|60]                             │                           │
│           │ Buffer: [ins(5), ins(45), del(62)] │                           │
│           └──────────────┬──────────────────────┘                           │
│                    ┌─────┴─────┐                                            │
│                    ▼           ▼                                            │
│           ┌─────────────┐  ┌─────────────┐                                  │
│           │ [10|20]     │  │ [40|50]     │                                  │
│           │ Buffer: []  │  │ Buffer: []  │                                  │
│           └─────────────┘  └─────────────┘                                  │
│                                                                             │
│  Operations accumulate in buffers, get flushed down in batches              │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Fractal Tree Operations

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    FRACTAL TREE INSERT ALGORITHM                             │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  INSERT(key, value):                                                        │
│  ═══════════════════                                                        │
│                                                                             │
│  1. Add (INSERT, key, value) to root's buffer                               │
│  2. IF root's buffer is full:                                               │
│       Flush buffer contents to appropriate children                         │
│  3. Recursively flush if child buffers become full                          │
│  4. Eventually, operations reach leaves and get applied                     │
│                                                                             │
│  FLUSH PROCESS                                                              │
│  ═════════════                                                              │
│                                                                             │
│  Buffer full:                                                               │
│           ┌─────────────────────────────────────────┐                       │
│           │ [30|60]                                 │                       │
│           │ Buffer: [5,12,25,35,45,55,65,72,88,95] │ ← FULL!                │
│           └──────────────────┬──────────────────────┘                       │
│                              │                                              │
│                              ▼ Flush                                        │
│                                                                             │
│           ┌──────────────────────────────────────────┐                      │
│           │ [30|60]                                  │                      │
│           │ Buffer: []                               │ ← Empty              │
│           └─────────────┬────────────────────────────┘                      │
│              ┌──────────┼──────────┐                                        │
│              ▼          ▼          ▼                                        │
│        ┌───────────┐ ┌───────────┐ ┌───────────┐                            │
│        │<30        │ │30-60      │ │>60        │                            │
│        │Buf:[5,12, │ │Buf:[35,   │ │Buf:[65,72,│                            │
│        │    25]    │ │    45,55] │ │    88,95] │                            │
│        └───────────┘ └───────────┘ └───────────┘                            │
│                                                                             │
│  One I/O flushes MANY operations to each child!                             │
│                                                                             │
│  AMORTIZED COST                                                             │
│  ══════════════                                                             │
│                                                                             │
│  • Buffer size: B/ε (where ε is a tuning parameter, e.g., 1/4)              │
│  • Each item moves down one level per flush                                 │
│  • Cost per insert: O(logᵦ N / B) I/Os amortized                            │
│  • Much better than B-Tree's O(logᵦ N) for random inserts                   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Fractal Tree Analysis

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    FRACTAL TREE vs B-TREE COMPARISON                         │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  WRITE PERFORMANCE                                                          │
│  ═════════════════                                                          │
│                                                                             │
│  Operation      │ B-Tree              │ Fractal Tree                        │
│  ───────────────┼─────────────────────┼─────────────────────────────────    │
│  Random Insert  │ O(log N) I/Os       │ O(log N / B) I/Os amortized         │
│  1M Inserts     │ ~20M I/Os           │ ~1M I/Os                            │
│  Sequential     │ Optimal             │ Optimal (similar)                   │
│                                                                             │
│  READ PERFORMANCE                                                           │
│  ════════════════                                                           │
│                                                                             │
│  Operation      │ B-Tree              │ Fractal Tree                        │
│  ───────────────┼─────────────────────┼─────────────────────────────────    │
│  Point Query    │ O(log N) I/Os       │ O(log N) I/Os (must check buffers)  │
│  Range Scan     │ O(K/B + log N)      │ O(K/B + log N) (after compaction)   │
│                                                                             │
│  TRADE-OFFS                                                                 │
│  ══════════                                                                 │
│                                                                             │
│  Fractal Tree Advantages:                                                   │
│  ✓ 10-100x better random write performance                                  │
│  ✓ Better for write-heavy workloads                                         │
│  ✓ Competitive read performance                                             │
│                                                                             │
│  Fractal Tree Disadvantages:                                                │
│  ✗ More complex implementation                                              │
│  ✗ Point queries must check buffers (slight overhead)                       │
│  ✗ More memory needed for in-memory buffers                                 │
│  ✗ Compaction/flush scheduling adds complexity                              │
│                                                                             │
│  REAL-WORLD USAGE                                                           │
│  ════════════════                                                           │
│  • TokuDB (MySQL storage engine) - uses Fractal Tree indexes                │
│  • Tokutek (acquired by Percona)                                            │
│  • FoundationDB (uses similar buffering techniques)                         │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Prefix and Suffix Compression

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    KEY COMPRESSION TECHNIQUES                                │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  MOTIVATION                                                                 │
│  ══════════                                                                 │
│                                                                             │
│  Keys in a B-Tree node often share common prefixes:                         │
│                                                                             │
│  Example: URL keys                                                          │
│  ┌──────────────────────────────────────────────────────────────┐           │
│  │ https://www.example.com/products/electronics/phones/iphone   │           │
│  │ https://www.example.com/products/electronics/phones/samsung  │           │
│  │ https://www.example.com/products/electronics/phones/pixel    │           │
│  │ https://www.example.com/products/electronics/tablets/ipad    │           │
│  └──────────────────────────────────────────────────────────────┘           │
│                                                                             │
│  54 bytes × 4 = 216 bytes                                                   │
│  With compression: 54 + 7 + 5 + 13 = 79 bytes (63% savings!)                │
│                                                                             │
│  Higher fanout = lower tree height = fewer I/Os                             │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Prefix Compression

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    PREFIX COMPRESSION                                        │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  BASIC IDEA: Store common prefix once, then only differences                │
│                                                                             │
│  UNCOMPRESSED NODE                                                          │
│  ══════════════════                                                         │
│  ┌───────────────────────────────────────────────────────────────┐          │
│  │ customer_john_smith                                           │          │
│  │ customer_john_williams                                        │          │
│  │ customer_johnson_bob                                          │          │
│  │ customer_jones_alice                                          │          │
│  └───────────────────────────────────────────────────────────────┘          │
│  Total: 76 bytes                                                            │
│                                                                             │
│  COMPRESSED NODE                                                            │
│  ════════════════                                                           │
│  ┌───────────────────────────────────────────────────────────────┐          │
│  │ Prefix: "customer_joh" (12 bytes)                             │          │
│  │ Keys:                                                         │          │
│  │   [0]: "n_smith"     (7 bytes)  → customer_john_smith         │          │
│  │   [1]: "n_williams"  (10 bytes) → customer_john_williams      │          │
│  │   [2]: "nson_bob"    (8 bytes)  → customer_johnson_bob        │          │
│  │   [3]: ..RESTART.."jones_alice" → customer_jones_alice        │          │
│  └───────────────────────────────────────────────────────────────┘          │
│  Total: 12 + 7 + 10 + 8 + 11 = 48 bytes (37% savings)                       │
│                                                                             │
│  IMPLEMENTATION APPROACHES                                                  │
│  ═════════════════════════                                                  │
│                                                                             │
│  1. FRONT COMPRESSION (incremental)                                         │
│     Store: prefix_len, suffix for each key                                  │
│     ┌────────────────────────────────────────────┐                          │
│     │ Key 1: "customer_john_smith"               │                          │
│     │ Key 2: [14]"williams"  (14 chars same)     │                          │
│     │ Key 3: [13]"son_bob"   (13 chars same)     │                          │
│     │ Key 4: [10]"nes_alice" (10 chars same)     │                          │
│     └────────────────────────────────────────────┘                          │
│                                                                             │
│  2. DICTIONARY COMPRESSION                                                  │
│     Common prefixes stored in dictionary, referenced by ID                  │
│     ┌────────────────────────────────────────────┐                          │
│     │ Dict: {1: "customer_", 2: "john", 3: "son"}│                          │
│     │ Key 1: [1][2]"_smith"                      │                          │
│     │ Key 2: [1][2]"_williams"                   │                          │
│     │ Key 3: [1][2][3]"_bob"                     │                          │
│     └────────────────────────────────────────────┘                          │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Suffix Truncation

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    SUFFIX TRUNCATION FOR SEPARATORS                          │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  KEY INSIGHT: Internal node separators only need to DISTINGUISH             │
│               They don't need to be exact copies of leaf keys               │
│                                                                             │
│  EXAMPLE: Split leaf node                                                   │
│  ═══════════════════════                                                    │
│                                                                             │
│  Leaf 1: ["customer_john_smith", "customer_john_williams"]                  │
│  Leaf 2: ["customer_mary_johnson", "customer_mary_williams"]                │
│                                                                             │
│  Full separator key: "customer_mary_johnson" (21 bytes)                     │
│  Truncated separator: "customer_m" (10 bytes)                               │
│                                                                             │
│  Why it works:                                                              │
│  • "customer_john_williams" < "customer_m" ✓                                │
│  • "customer_m" ≤ "customer_mary_johnson" ✓                                 │
│                                                                             │
│  TRUNCATION ALGORITHM                                                       │
│  ════════════════════                                                       │
│                                                                             │
│  Given: last_key_left = "customer_john_williams"                            │
│         first_key_right = "customer_mary_johnson"                           │
│                                                                             │
│  Find shortest separator S where:                                           │
│      last_key_left < S ≤ first_key_right                                    │
│                                                                             │
│  Algorithm:                                                                 │
│  1. Find common prefix: "customer_"                                         │
│  2. First differing chars: 'j' vs 'm'                                       │
│  3. Shortest separator: "customer_m" (prefix + first char of right)         │
│                                                                             │
│  VISUALIZATION                                                              │
│  ═════════════                                                              │
│                                                                             │
│  WITHOUT truncation:             WITH truncation:                           │
│  ┌───────────────────────┐      ┌───────────────────────┐                   │
│  │ customer_mary_johnson │      │ customer_m            │                   │
│  │ customer_tom_brown    │      │ customer_t            │                   │
│  │ customer_zack_wilson  │      │ customer_z            │                   │
│  └───────────────────────┘      └───────────────────────┘                   │
│  63 bytes                        30 bytes (52% savings)                     │
│                                                                             │
│  More keys per node = higher fanout = shallower tree!                       │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Compression Trade-offs

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    KEY COMPRESSION ANALYSIS                                  │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ADVANTAGES                                                                 │
│  ══════════                                                                 │
│  ✓ Higher fanout (more keys per node)                                       │
│  ✓ Lower tree height                                                        │
│  ✓ Better cache utilization                                                 │
│  ✓ Reduced I/O for large keys                                               │
│                                                                             │
│  DISADVANTAGES                                                              │
│  ═════════════                                                              │
│  ✗ CPU overhead for compression/decompression                               │
│  ✗ Random access within node may require decompressing                      │
│  ✗ More complex implementation                                              │
│  ✗ May complicate concurrency                                               │
│                                                                             │
│  WHEN TO USE                                                                │
│  ═══════════                                                                │
│  • Large keys (URLs, file paths, compound keys)                             │
│  • Keys with common prefixes                                                │
│  • Read-heavy workloads (compression cost amortized)                        │
│  • Memory-constrained environments                                          │
│                                                                             │
│  REAL-WORLD IMPLEMENTATIONS                                                 │
│  ═══════════════════════════                                                │
│  • PostgreSQL: supports prefix compression in certain index types           │
│  • SQLite: prefix compression in FTS indexes                                │
│  • InnoDB: key prefix compression in secondary indexes                      │
│  • WiredTiger (MongoDB): extensive prefix compression                       │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Adaptive Indexing

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    ADAPTIVE INDEXING: DATABASE CRACKING                      │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  THE PROBLEM                                                                │
│  ═══════════                                                                │
│                                                                             │
│  Traditional B-Tree:                                                        │
│  • Build index upfront (expensive)                                          │
│  • Must predict which columns to index                                      │
│  • Index everything = wasted space                                          │
│  • Index nothing = slow queries                                             │
│                                                                             │
│  ADAPTIVE IDEA: Build index incrementally as queries arrive                 │
│                                                                             │
│  DATABASE CRACKING                                                          │
│  ═════════════════                                                          │
│                                                                             │
│  Initial state: Unsorted column data                                        │
│  ┌─────────────────────────────────────────────────────────────┐            │
│  │ 50 │ 10 │ 80 │ 30 │ 90 │ 20 │ 70 │ 40 │ 60 │ 15 │ ...      │            │
│  └─────────────────────────────────────────────────────────────┘            │
│                                                                             │
│  Query: SELECT * WHERE x < 25                                               │
│                                                                             │
│  CRACK the column: partition around 25                                      │
│  ┌────────────────────┬────────────────────────────────────────┐            │
│  │ 10 │ 20 │ 15      │ 50 │ 80 │ 30 │ 90 │ 70 │ 40 │ 60 │... │            │
│  └────────────────────┴────────────────────────────────────────┘            │
│        < 25                        ≥ 25                                     │
│                                                                             │
│  Cracker Index: {25: position_of_split}                                     │
│                                                                             │
│  Next query: WHERE x > 60                                                   │
│                                                                             │
│  CRACK again: partition ≥25 region around 60                                │
│  ┌───────────┬─────────────────────┬───────────────────────────┐            │
│  │ <25       │ 30 │ 40 │ 50       │ 80 │ 90 │ 70 │ 60 │ ...   │            │
│  └───────────┴─────────────────────┴───────────────────────────┘            │
│      < 25         25-60                    > 60                             │
│                                                                             │
│  Cracker Index: {25: pos1, 60: pos2}                                        │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Adaptive B-Trees

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    ADAPTIVE B-TREE VARIATIONS                                │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ADAPTIVE MERGING                                                           │
│  ════════════════                                                           │
│                                                                             │
│  Combine cracking with B-Tree structure:                                    │
│                                                                             │
│  1. Initial: Unsorted partitions (runs)                                     │
│     ┌─────────┐ ┌─────────┐ ┌─────────┐                                     │
│     │ Run 1   │ │ Run 2   │ │ Run 3   │  (created by bulk inserts)          │
│     └─────────┘ └─────────┘ └─────────┘                                     │
│                                                                             │
│  2. Query arrives: Crack relevant runs, merge into index                    │
│     ┌─────────┐ ┌─────────┐ ┌─────────┐                                     │
│     │ Cracked │ │ Run 2   │ │ Run 3   │                                     │
│     └────┬────┘ └─────────┘ └─────────┘                                     │
│          │                                                                  │
│          ▼                                                                  │
│     ┌─────────────┐                                                         │
│     │  B-Tree     │  (incrementally built)                                  │
│     │  Index      │                                                         │
│     └─────────────┘                                                         │
│                                                                             │
│  3. Over time: More runs merged into B-Tree                                 │
│     Eventually: Full B-Tree index (if needed)                               │
│                                                                             │
│  BENEFITS                                                                   │
│  ════════                                                                   │
│  ✓ No upfront index creation cost                                           │
│  ✓ Index adapts to actual query patterns                                    │
│  ✓ First query already faster than full scan                                │
│  ✓ Gradual transition to full index performance                             │
│                                                                             │
│  PARTIAL INDEXES                                                            │
│  ════════════════                                                           │
│                                                                             │
│  Another form of adaptive indexing:                                         │
│  Index only rows matching a predicate                                       │
│                                                                             │
│  CREATE INDEX active_users_idx ON users(id)                                 │
│      WHERE status = 'active';                                               │
│                                                                             │
│  • Smaller index (only relevant rows)                                       │
│  • Faster to maintain                                                       │
│  • Better cache utilization                                                 │
│                                                                             │
│  REAL-WORLD USAGE                                                           │
│  ════════════════                                                           │
│  • MonetDB: pioneered database cracking                                     │
│  • PostgreSQL: partial indexes                                              │
│  • Research systems: adaptive merging, learned indexes                      │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Summary

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    CHAPTER 3 KEY TAKEAWAYS                                   │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  B-TREE VARIANTS COMPARISON                                                 │
│  ══════════════════════════                                                 │
│                                                                             │
│  ┌───────────────┬─────────────────────┬────────────────────────────────┐   │
│  │ Variant       │ Optimizes For       │ Trade-off                      │   │
│  ├───────────────┼─────────────────────┼────────────────────────────────┤   │
│  │ B*-Tree       │ Space utilization   │ Complex inserts                │   │
│  │ B-link Tree   │ Concurrency         │ Extra storage per node         │   │
│  │ CoW B-Tree    │ Snapshots/Recovery  │ Write amplification            │   │
│  │ Fractal Tree  │ Write performance   │ Complexity, memory             │   │
│  │ Compressed    │ Fanout/Space        │ CPU overhead                   │   │
│  │ Adaptive      │ No upfront cost     │ Initial query overhead         │   │
│  └───────────────┴─────────────────────┴────────────────────────────────┘   │
│                                                                             │
│  CHOOSING THE RIGHT VARIANT                                                 │
│  ══════════════════════════                                                 │
│                                                                             │
│  Read-Heavy + High Concurrency:                                             │
│  → B-link Tree (PostgreSQL style)                                           │
│                                                                             │
│  Write-Heavy + Random Inserts:                                              │
│  → Fractal Tree or LSM-Tree (next chapter)                                  │
│                                                                             │
│  Need Point-in-Time Recovery / MVCC:                                        │
│  → Copy-on-Write B-Tree (LMDB style)                                        │
│                                                                             │
│  Space-Constrained + Large Keys:                                            │
│  → Prefix/Suffix Compression                                                │
│                                                                             │
│  Ad-hoc Queries + Unknown Patterns:                                         │
│  → Adaptive Indexing / Database Cracking                                    │
│                                                                             │
│  General Purpose OLTP:                                                      │
│  → Standard B+Tree with compression                                         │
│                                                                             │
│  KEY INSIGHT                                                                │
│  ═══════════                                                                │
│  No single variant is best for all workloads.                               │
│  Modern databases often combine multiple techniques:                        │
│  • B-link for concurrency + prefix compression for space                    │
│  • Different index types for different access patterns                      │
│                                                                             │
│  WHAT'S NEXT                                                                │
│  ──────────                                                                 │
│  Chapter 4: B-Tree Implementation Details                                   │
│  • On-disk page layouts                                                     │
│  • Overflow pages and variable-length data                                  │
│  • Slotted page organization                                                │
│  • Page splits and merges implementation                                    │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

