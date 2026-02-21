# Chapter 6: B-Tree Concurrency

## Table of Contents
- [Concurrency Challenges](#concurrency-challenges)
- [Latches vs Locks](#latches-vs-locks)
- [Latch Coupling (Crabbing)](#latch-coupling-crabbing)
- [B-link Trees](#b-link-trees)
- [Lock-Free Structures](#lock-free-structures)
- [Optimistic Concurrency](#optimistic-concurrency)
- [Summary](#summary)

---

## Concurrency Challenges

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    B-TREE CONCURRENCY CHALLENGES                            │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  WHY IS B-TREE CONCURRENCY HARD?                                            │
│  ═══════════════════════════════                                            │
│                                                                             │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │                                                                       │  │
│  │  Consider two concurrent operations:                                  │  │
│  │                                                                       │  │
│  │       ┌─────────┐                                                     │  │
│  │       │  ROOT   │                                                     │  │
│  │       │ [50,100]│                                                     │  │
│  │       └────┬────┘                                                     │  │
│  │      ┌─────┼─────┐                                                    │  │
│  │      ▼     ▼     ▼                                                    │  │
│  │  ┌──────┐┌──────┐┌──────┐                                             │  │
│  │  │<50   ││50-100││>100  │                                             │  │
│  │  └──────┘└──────┘└──────┘                                             │  │
│  │      ↑               ↑                                                │  │
│  │      │               │                                                │  │
│  │   Thread A        Thread B                                            │  │
│  │   INSERT(25)      INSERT(150)                                         │  │
│  │                                                                       │  │
│  │  Problems:                                                            │  │
│  │  1. Both might try to split nodes simultaneously                      │  │
│  │  2. A split propagates upward - might conflict at root                │  │
│  │  3. While A reads a node, B might modify it                           │  │
│  │  4. Structural Modification Operations (SMOs) change tree shape       │  │
│  │                                                                       │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                                                                             │
│  STRUCTURAL MODIFICATION OPERATIONS (SMOs)                                  │
│  ═════════════════════════════════════════                                  │
│                                                                             │
│  • Node splits (insert causes overflow)                                     │
│  • Node merges (delete causes underflow)                                    │
│  • Node redistribution (rebalancing keys)                                   │
│  • Height changes (root split, tree shrink)                                 │
│                                                                             │
│  These operations change pointers that other threads might be following!    │
│                                                                             │
│  RACE CONDITION EXAMPLE                                                     │
│  ═════════════════════                                                      │
│                                                                             │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │  Thread A (reading):                Thread B (splitting):             │  │
│  │                                                                       │  │
│  │  1. Read root, follow ptr to leaf                                     │  │
│  │  2. ...traversing...                 1. Split leaf node               │  │
│  │                                      2. Key moved to new sibling      │  │
│  │  3. Arrive at leaf                                                    │  │
│  │  4. Search for key 42                                                 │  │
│  │  5. NOT FOUND! (it moved!)                                            │  │
│  │                                                                       │  │
│  │  Thread A sees INCONSISTENT view of the tree!                         │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Latches vs Locks

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    LATCHES vs LOCKS                                         │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  These terms are often confused! They are DIFFERENT things:                 │
│                                                                             │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │                                                                       │  │
│  │  ┌────────────────────────┬────────────────────────────────────────┐  │  │
│  │  │        LOCKS           │            LATCHES                    │  │  │
│  │  ├────────────────────────┼────────────────────────────────────────┤  │  │
│  │  │ Protect DATA (tuples,  │ Protect IN-MEMORY data structures     │  │  │
│  │  │ tables, databases)     │ (B-tree nodes, buffer pool pages)     │  │  │
│  │  ├────────────────────────┼────────────────────────────────────────┤  │  │
│  │  │ Held for TRANSACTION   │ Held for OPERATION duration           │  │  │
│  │  │ duration               │ (microseconds)                        │  │  │
│  │  ├────────────────────────┼────────────────────────────────────────┤  │  │
│  │  │ Deadlock DETECTION/    │ Deadlock AVOIDANCE (careful coding)   │  │  │
│  │  │ resolution needed      │                                       │  │  │
│  │  ├────────────────────────┼────────────────────────────────────────┤  │  │
│  │  │ Stored in LOCK MANAGER │ Stored IN the data structure itself   │  │  │
│  │  │ (hash table)           │                                       │  │  │
│  │  ├────────────────────────┼────────────────────────────────────────┤  │  │
│  │  │ Support ROLLBACK       │ NO rollback (not logged)              │  │  │
│  │  ├────────────────────────┼────────────────────────────────────────┤  │  │
│  │  │ User-visible           │ Internal implementation detail        │  │  │
│  │  └────────────────────────┴────────────────────────────────────────┘  │  │
│  │                                                                       │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                                                                             │
│  LATCH MODES                                                                │
│  ════════════                                                               │
│                                                                             │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │                                                                       │  │
│  │  READ (Shared) Latch:                                                 │  │
│  │  • Multiple threads can hold simultaneously                           │  │
│  │  • Used for reading node contents                                     │  │
│  │                                                                       │  │
│  │  WRITE (Exclusive) Latch:                                             │  │
│  │  • Only one thread can hold                                           │  │
│  │  • Blocks all other latches (read or write)                           │  │
│  │  • Used for modifying node contents                                   │  │
│  │                                                                       │  │
│  │  Compatibility Matrix:                                                │  │
│  │  ┌───────────┬─────────┬─────────┐                                    │  │
│  │  │           │  READ   │  WRITE  │                                    │  │
│  │  ├───────────┼─────────┼─────────┤                                    │  │
│  │  │   READ    │    ✓    │    ✗    │                                    │  │
│  │  │   WRITE   │    ✗    │    ✗    │                                    │  │
│  │  └───────────┴─────────┴─────────┘                                    │  │
│  │                                                                       │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Latch Coupling (Crabbing)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    LATCH COUPLING / CRABBING PROTOCOL                       │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  Basic idea: Hold latch on parent while acquiring latch on child,           │
│  then release parent when safe.                                             │
│                                                                             │
│  SEARCH (Read-Only) PROTOCOL                                                │
│  ═══════════════════════════                                                │
│                                                                             │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │                                                                       │  │
│  │  1. Acquire READ latch on root                                        │  │
│  │  2. Find appropriate child pointer                                    │  │
│  │  3. Acquire READ latch on child                                       │  │
│  │  4. Release READ latch on parent (safe - we have child)               │  │
│  │  5. Repeat until leaf                                                 │  │
│  │  6. Search in leaf, release latch                                     │  │
│  │                                                                       │  │
│  │       ┌─────────┐                                                     │  │
│  │       │  ROOT   │ ← R-latch, then release                             │  │
│  │       └────┬────┘                                                     │  │
│  │            │                                                          │  │
│  │            ▼                                                          │  │
│  │       ┌─────────┐                                                     │  │
│  │       │ INTERNAL│ ← R-latch, then release                             │  │
│  │       └────┬────┘                                                     │  │
│  │            │                                                          │  │
│  │            ▼                                                          │  │
│  │       ┌─────────┐                                                     │  │
│  │       │  LEAF   │ ← R-latch, search, release                          │  │
│  │       └─────────┘                                                     │  │
│  │                                                                       │  │
│  │  Only ONE latch held at a time after initial descent!                 │  │
│  │                                                                       │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                                                                             │
│  INSERT/DELETE (Write) PROTOCOL - Pessimistic                               │
│  ════════════════════════════════════════════                               │
│                                                                             │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │                                                                       │  │
│  │  Must handle case where modification triggers SPLIT or MERGE          │  │
│  │  which propagates upward!                                             │  │
│  │                                                                       │  │
│  │  1. Acquire WRITE latch on root                                       │  │
│  │  2. Find appropriate child                                            │  │
│  │  3. Acquire WRITE latch on child                                      │  │
│  │  4. Is child SAFE?                                                    │  │
│  │     - For INSERT: Not full (won't split)                              │  │
│  │     - For DELETE: More than half full (won't merge)                   │  │
│  │     → If SAFE: Release ALL ancestor latches                           │  │
│  │     → If UNSAFE: Keep all latches                                     │  │
│  │  5. Repeat until leaf                                                 │  │
│  │  6. Perform operation                                                 │  │
│  │                                                                       │  │
│  │       ┌─────────┐                                                     │  │
│  │       │  ROOT   │ ← W-latch (might split if child splits)             │  │
│  │       └────┬────┘                                                     │  │
│  │            │                                                          │  │
│  │            ▼                                                          │  │
│  │       ┌─────────┐                                                     │  │
│  │       │INTERNAL │ ← W-latch (SAFE → release root!)                    │  │
│  │       │ (SAFE)  │                                                     │  │
│  │       └────┬────┘                                                     │  │
│  │            │                                                          │  │
│  │            ▼                                                          │  │
│  │       ┌─────────┐                                                     │  │
│  │       │  LEAF   │ ← W-latch, modify                                   │  │
│  │       └─────────┘                                                     │  │
│  │                                                                       │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                                                                             │
│  PROBLEM: Root becomes a BOTTLENECK!                                        │
│  ═══════════════════════════════════                                        │
│                                                                             │
│  Every write starts with WRITE latch on root.                               │
│  Even if most operations don't need it, they must wait.                     │
│                                                                             │
│  OPTIMISTIC LATCH COUPLING                                                  │
│  ══════════════════════════                                                 │
│                                                                             │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │                                                                       │  │
│  │  1. Traverse down using READ latches (like search)                    │  │
│  │  2. Only acquire WRITE latch on leaf                                  │  │
│  │  3. If leaf is SAFE → Done! (common case)                             │  │
│  │  4. If leaf is UNSAFE (needs split):                                  │  │
│  │     - Release all latches                                             │  │
│  │     - RESTART with pessimistic protocol                               │  │
│  │                                                                       │  │
│  │  ✓ Most operations succeed on first try (trees are usually not full)  │  │
│  │  ✓ Root not blocked for reads                                         │  │
│  │                                                                       │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## B-link Trees

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    B-LINK TREES (Lehman & Yao, 1981)                        │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  Key insight: Add SIBLING POINTERS at every level + HIGH KEY marker         │
│                                                                             │
│  STRUCTURE                                                                  │
│  ═════════                                                                  │
│                                                                             │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │                                                                       │  │
│  │       ┌─────────────────────┐                                         │  │
│  │       │ ROOT: [50|∞]        │                                         │  │
│  │       │ high_key = ∞        │                                         │  │
│  │       └──────────┬──────────┘                                         │  │
│  │                  │                                                    │  │
│  │      ┌───────────┴───────────┐                                        │  │
│  │      ▼                       ▼                                        │  │
│  │  ┌────────────┐ ──────▶ ┌────────────┐                                │  │
│  │  │ [20,40|50] │ link    │ [70,90|∞]  │                                │  │
│  │  │ high_key=50│ ──────▶ │ high_key=∞ │                                │  │
│  │  └─────┬──────┘         └─────┬──────┘                                │  │
│  │        │                      │                                       │  │
│  │   ┌────┴────┐            ┌────┴────┐                                  │  │
│  │   ▼    ▼    ▼            ▼    ▼    ▼                                  │  │
│  │  ┌──┐ ┌──┐ ┌──┐ ──▶  ┌──┐ ┌──┐ ┌──┐                                   │  │
│  │  │L1│→│L2│→│L3│ ───▶ │L4│→│L5│→│L6│→ NULL                             │  │
│  │  └──┘ └──┘ └──┘      └──┘ └──┘ └──┘                                   │  │
│  │                                                                       │  │
│  │  Each node has:                                                       │  │
│  │  • high_key: Maximum key this subtree can contain                     │  │
│  │  • link: Pointer to right sibling (same level)                        │  │
│  │                                                                       │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                                                                             │
│  HOW SPLITS WORK (Non-blocking!)                                            │
│  ═══════════════════════════════                                            │
│                                                                             │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │                                                                       │  │
│  │  Step 1: Node is full, need to split                                  │  │
│  │                                                                       │  │
│  │  ┌─────────────────────────┐                                          │  │
│  │  │ [10,20,30,40] h_k=50    │→ (sibling)                               │  │
│  │  └─────────────────────────┘                                          │  │
│  │                                                                       │  │
│  │  Step 2: Create new node, move half the keys                          │  │
│  │                                                                       │  │
│  │  ┌────────────────┐   ┌────────────────┐                              │  │
│  │  │ [10,20] h_k=30 │──▶│ [30,40] h_k=50 │→ (old sibling)               │  │
│  │  └────────────────┘   └────────────────┘                              │  │
│  │                        ↑ new right link points here                   │  │
│  │                                                                       │  │
│  │  Step 3: Update parent (separately, can be delayed!)                  │  │
│  │                                                                       │  │
│  │  Parent: add pointer to new node [30,40]                              │  │
│  │                                                                       │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                                                                             │
│  CONCURRENT SEARCH WITH SPLITS                                              │
│  ═════════════════════════════                                              │
│                                                                             │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │                                                                       │  │
│  │  If we're searching for key 35:                                       │  │
│  │                                                                       │  │
│  │  1. Follow parent pointer to [10,20] (based on old parent state)      │  │
│  │  2. Check: Is 35 > high_key (30)? YES!                                │  │
│  │  3. Follow right-link to [30,40]                                      │  │
│  │  4. Check: Is 35 > high_key (50)? NO                                  │  │
│  │  5. Search in this node                                               │  │
│  │                                                                       │  │
│  │  The right-link lets us find keys that "moved" during concurrent      │  │
│  │  splits, even before parent is updated!                               │  │
│  │                                                                       │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                                                                             │
│  BENEFITS                                                                   │
│  ════════                                                                   │
│                                                                             │
│  • Only need latch on ONE node at a time (no crabbing needed!)              │
│  • Splits don't block readers                                               │
│  • Parent update can be done lazily                                         │
│  • Deadlock-free by design                                                  │
│                                                                             │
│  Used by: PostgreSQL (nbtree), many modern databases                        │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Lock-Free Structures

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    LOCK-FREE B-TREE STRUCTURES                              │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  Goal: Eliminate latches entirely using atomic hardware operations          │
│                                                                             │
│  COMPARE-AND-SWAP (CAS) OPERATION                                           │
│  ═════════════════════════════════                                          │
│                                                                             │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │                                                                       │  │
│  │  CAS(memory_location, expected_value, new_value):                     │  │
│  │    ATOMICALLY:                                                        │  │
│  │      if *memory_location == expected_value:                           │  │
│  │        *memory_location = new_value                                   │  │
│  │        return SUCCESS                                                 │  │
│  │      else:                                                            │  │
│  │        return FAILURE (someone else modified it)                      │  │
│  │                                                                       │  │
│  │  Example: Atomically update a pointer                                 │  │
│  │                                                                       │  │
│  │    Thread A                    Thread B                               │  │
│  │    ────────                    ────────                               │  │
│  │    read ptr = 0x100           read ptr = 0x100                        │  │
│  │    CAS(ptr, 0x100, 0x200)     CAS(ptr, 0x100, 0x300)                   │  │
│  │         ↓                          ↓                                  │  │
│  │      SUCCESS!                   FAILURE! (ptr is now 0x200)           │  │
│  │                                                                       │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                                                                             │
│  BW-TREE (Microsoft Research, 2013)                                         │
│  ═══════════════════════════════════                                        │
│                                                                             │
│  Key innovation: DELTA UPDATES instead of in-place modification            │
│                                                                             │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │                                                                       │  │
│  │  Instead of:                                                          │  │
│  │    Latch node → Modify in place → Release latch                       │  │
│  │                                                                       │  │
│  │  Do:                                                                  │  │
│  │    Create delta record → CAS to prepend to delta chain               │  │
│  │                                                                       │  │
│  │         ┌─────────────┐                                               │  │
│  │         │ Mapping Table│                                               │  │
│  │         │  Page ID → *│─────┐                                          │  │
│  │         └─────────────┘     │                                          │  │
│  │                             ▼                                          │  │
│  │                      ┌──────────────┐                                  │  │
│  │                      │ Delta: +key55│  ← Latest update                 │  │
│  │                      └──────┬───────┘                                  │  │
│  │                             │                                          │  │
│  │                             ▼                                          │  │
│  │                      ┌──────────────┐                                  │  │
│  │                      │ Delta: -key30│  ← Previous update               │  │
│  │                      └──────┬───────┘                                  │  │
│  │                             │                                          │  │
│  │                             ▼                                          │  │
│  │                      ┌──────────────┐                                  │  │
│  │                      │ Base Page    │  ← Original page                 │  │
│  │                      │ [10,20,30,40]│                                  │  │
│  │                      └──────────────┘                                  │  │
│  │                                                                       │  │
│  │  To INSERT key 55:                                                    │  │
│  │  1. Create delta record: "+55"                                        │  │
│  │  2. Point delta's next to current head                                │  │
│  │  3. CAS mapping table entry to point to new delta                     │  │
│  │                                                                       │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                                                                             │
│  CONSOLIDATION                                                              │
│  ═════════════                                                              │
│                                                                             │
│  When delta chain gets too long, consolidate into new base page:            │
│                                                                             │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │                                                                       │  │
│  │  Before:                          After:                              │  │
│  │                                                                       │  │
│  │  Δ(+55) → Δ(-30) → [10,20,30,40]  →  [10,20,40,55]                   │  │
│  │                                                                       │  │
│  │  New consolidated page created, then CAS to update mapping table      │  │
│  │  Old pages become garbage (epoch-based reclamation)                   │  │
│  │                                                                       │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                                                                             │
│  EPOCH-BASED MEMORY RECLAMATION                                             │
│  ═══════════════════════════════                                            │
│                                                                             │
│  Problem: When can we free old pages? Other threads might be reading!       │
│                                                                             │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │                                                                       │  │
│  │  Global Epoch: 5                                                      │  │
│  │                                                                       │  │
│  │  Thread A: epoch = 5 (active)                                         │  │
│  │  Thread B: epoch = 5 (active)                                         │  │
│  │  Thread C: epoch = 4 (slower, still in old epoch)                     │  │
│  │                                                                       │  │
│  │  Garbage from epoch 3: SAFE to free (no thread in epoch ≤ 3)          │  │
│  │  Garbage from epoch 4: NOT safe (Thread C might access)               │  │
│  │  Garbage from epoch 5: NOT safe (current epoch)                       │  │
│  │                                                                       │  │
│  │  Rule: Free garbage only when all threads have moved past that epoch  │  │
│  │                                                                       │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                                                                             │
│  ADVANTAGES OF LOCK-FREE                                                    │
│  • No blocking - threads make progress independently                        │
│  • No deadlocks - no locks to create cycles                                 │
│  • Better scalability on many-core systems                                  │
│                                                                             │
│  DISADVANTAGES                                                              │
│  • Complex implementation                                                   │
│  • Memory overhead (delta chains, garbage tracking)                         │
│  • Potential for high retry rates under contention                          │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Optimistic Concurrency

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    OPTIMISTIC CONCURRENCY CONTROL                           │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  Philosophy: Assume conflicts are RARE. Don't lock; validate at the end.    │
│                                                                             │
│  THREE PHASES                                                               │
│  ════════════                                                               │
│                                                                             │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │                                                                       │  │
│  │  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐               │  │
│  │  │    READ     │ →  │  VALIDATE   │ →  │   WRITE     │               │  │
│  │  │   PHASE     │    │   PHASE     │    │   PHASE     │               │  │
│  │  └─────────────┘    └─────────────┘    └─────────────┘               │  │
│  │        │                  │                  │                        │  │
│  │        ▼                  ▼                  ▼                        │  │
│  │  • Read data        • Check if data     • Apply changes             │  │
│  │  • Record versions    changed since      • Make visible              │  │
│  │  • No locks held      we read it         • Short lock held           │  │
│  │                     • Abort if conflict                              │  │
│  │                                                                       │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                                                                             │
│  VERSION NUMBERS / TIMESTAMPS                                               │
│  ═══════════════════════════                                                │
│                                                                             │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │                                                                       │  │
│  │  Each node has a version number that increments on modification:      │  │
│  │                                                                       │  │
│  │  ┌──────────────────────────────────────┐                             │  │
│  │  │  Node                                │                             │  │
│  │  ├──────────────────────────────────────┤                             │  │
│  │  │  version: 42                         │                             │  │
│  │  │  keys: [10, 20, 30, 40]              │                             │  │
│  │  │  ...                                 │                             │  │
│  │  └──────────────────────────────────────┘                             │  │
│  │                                                                       │  │
│  │  Read Operation:                                                      │  │
│  │  1. Read version (42)                                                 │  │
│  │  2. Read data                                                         │  │
│  │  3. Read version again                                                │  │
│  │  4. If version changed → data may be inconsistent → RETRY            │  │
│  │                                                                       │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                                                                             │
│  OPTIMISTIC LOCK COUPLING (OLC)                                             │
│  ═══════════════════════════════                                            │
│                                                                             │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │                                                                       │  │
│  │  Combines optimistic reads with latch coupling for writes:            │  │
│  │                                                                       │  │
│  │  Search (Read):                                                       │  │
│  │  ┌─────────────────────────────────────────────────────────────────┐  │  │
│  │  │  current = root                                                 │  │  │
│  │  │  while current is not leaf:                                     │  │  │
│  │  │      version = read_version(current)                            │  │  │
│  │  │      child_ptr = find_child(current, key)                       │  │  │
│  │  │      if version_changed(current, version):                      │  │  │
│  │  │          RESTART from root                                      │  │  │
│  │  │      current = child_ptr                                        │  │  │
│  │  │  // At leaf - validate and read                                 │  │  │
│  │  │  version = read_version(current)                                │  │  │
│  │  │  result = search_in_leaf(current, key)                          │  │  │
│  │  │  if version_changed(current, version):                          │  │  │
│  │  │      RESTART from root                                          │  │  │
│  │  │  return result                                                  │  │  │
│  │  └─────────────────────────────────────────────────────────────────┘  │  │
│  │                                                                       │  │
│  │  Insert (Write):                                                      │  │
│  │  ┌─────────────────────────────────────────────────────────────────┐  │  │
│  │  │  // Phase 1: Optimistic descent (no locks)                      │  │  │
│  │  │  path = []                                                      │  │  │
│  │  │  current = root                                                 │  │  │
│  │  │  while current is not leaf:                                     │  │  │
│  │  │      path.push((current, read_version(current)))                │  │  │
│  │  │      current = find_child(current, key)                         │  │  │
│  │  │                                                                 │  │  │
│  │  │  // Phase 2: Lock leaf and validate path                        │  │  │
│  │  │  LOCK(current)                                                  │  │  │
│  │  │  for (node, version) in path:                                   │  │  │
│  │  │      if version_changed(node, version):                         │  │  │
│  │  │          UNLOCK(current)                                        │  │  │
│  │  │          RESTART                                                │  │  │
│  │  │                                                                 │  │  │
│  │  │  // Phase 3: Perform insert                                     │  │  │
│  │  │  if leaf_needs_split:                                           │  │  │
│  │  │      // Need to lock ancestors - restart pessimistically        │  │  │
│  │  │      UNLOCK(current)                                            │  │  │
│  │  │      pessimistic_insert(key, value)                             │  │  │
│  │  │  else:                                                          │  │  │
│  │  │      insert_in_leaf(current, key, value)                        │  │  │
│  │  │      UNLOCK(current)                                            │  │  │
│  │  └─────────────────────────────────────────────────────────────────┘  │  │
│  │                                                                       │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                                                                             │
│  WHEN TO USE OPTIMISTIC VS PESSIMISTIC                                      │
│  ═══════════════════════════════════════                                    │
│                                                                             │
│  ┌────────────────────────────┬────────────────────────────┐                │
│  │      OPTIMISTIC            │       PESSIMISTIC          │                │
│  ├────────────────────────────┼────────────────────────────┤                │
│  │ Low contention workloads   │ High contention workloads  │                │
│  │ Read-heavy workloads       │ Write-heavy workloads      │                │
│  │ Short operations           │ Long operations            │                │
│  │ When retries are cheap     │ When retries are expensive │                │
│  │ OLTP point queries         │ Batch updates              │                │
│  └────────────────────────────┴────────────────────────────┘                │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Summary

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    CHAPTER 6 SUMMARY: B-TREE CONCURRENCY                    │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  KEY CONCEPTS                                                               │
│  ════════════                                                               │
│                                                                             │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │                                                                       │  │
│  │  1. CONCURRENCY CHALLENGES                                            │  │
│  │     • SMOs (splits, merges) change tree structure                     │  │
│  │     • Race conditions between readers and writers                     │  │
│  │     • Need to balance correctness with performance                    │  │
│  │                                                                       │  │
│  │  2. LATCHES vs LOCKS                                                  │  │
│  │     • Latches: Short-term, protect physical structure                 │  │
│  │     • Locks: Long-term, protect logical data                          │  │
│  │     • Different purposes, different lifetimes                         │  │
│  │                                                                       │  │
│  │  3. LATCH COUPLING (CRABBING)                                         │  │
│  │     • Hold parent while acquiring child                               │  │
│  │     • Release when child is "safe"                                    │  │
│  │     • Pessimistic: Always prepare for worst case                      │  │
│  │     • Optimistic: Assume best case, retry if wrong                    │  │
│  │                                                                       │  │
│  │  4. B-LINK TREES                                                      │  │
│  │     • Right-sibling pointers + high-key markers                       │  │
│  │     • Handle concurrent splits gracefully                             │  │
│  │     • Only one latch at a time                                        │  │
│  │     • Used by PostgreSQL                                              │  │
│  │                                                                       │  │
│  │  5. LOCK-FREE STRUCTURES                                              │  │
│  │     • Use CAS instead of latches                                      │  │
│  │     • Bw-Tree: Delta updates + mapping table                          │  │
│  │     • Epoch-based garbage collection                                  │  │
│  │                                                                       │  │
│  │  6. OPTIMISTIC CONCURRENCY                                            │  │
│  │     • Read-validate-write phases                                      │  │
│  │     • Version numbers detect conflicts                                │  │
│  │     • Best for low-contention workloads                               │  │
│  │                                                                       │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                                                                             │
│  TECHNIQUE COMPARISON                                                       │
│  ════════════════════                                                       │
│                                                                             │
│  ┌─────────────────┬───────────┬───────────┬───────────┬──────────────┐    │
│  │   Technique     │Complexity │Throughput │ Best For  │  Used By     │    │
│  ├─────────────────┼───────────┼───────────┼───────────┼──────────────┤    │
│  │ Crabbing        │  Low      │  Medium   │ Simplicity│ Educational  │    │
│  │ (Pessimistic)   │           │           │           │              │    │
│  ├─────────────────┼───────────┼───────────┼───────────┼──────────────┤    │
│  │ Crabbing        │  Medium   │  High     │ Read-heavy│ Common       │    │
│  │ (Optimistic)    │           │           │           │              │    │
│  ├─────────────────┼───────────┼───────────┼───────────┼──────────────┤    │
│  │ B-link Trees    │  Medium   │  High     │ OLTP      │ PostgreSQL   │    │
│  ├─────────────────┼───────────┼───────────┼───────────┼──────────────┤    │
│  │ Lock-Free       │  High     │ Very High │ Many cores│ Bw-Tree      │    │
│  │ (Bw-Tree)       │           │           │           │ (SQL Server) │    │
│  └─────────────────┴───────────┴───────────┴───────────┴──────────────┘    │
│                                                                             │
│  PRACTICAL TIPS                                                             │
│  ═══════════════                                                            │
│                                                                             │
│  • Start simple (optimistic crabbing works for most workloads)              │
│  • B-link trees offer excellent read/write balance                          │
│  • Lock-free only worth it for extreme scalability needs                    │
│  • Profile your workload - is contention actually a problem?                │
│  • Consider read replicas for read-heavy workloads                          │
│                                                                             │
│  NEXT: Chapter 7 - Log-Structured Storage (LSM-Trees)                       │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

