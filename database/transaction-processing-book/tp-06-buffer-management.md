# Buffer Management

## Overview

Buffer management is the subsystem responsible for transferring pages between disk and main memory. As Jim Gray emphasized, effective buffer management is crucial for database performance since disk I/O is orders of magnitude slower than memory access.

---

## Buffer Pool Architecture

### Basic Structure

```
┌──────────────────────────────────────────────────────────────┐
│                        BUFFER POOL                            │
├──────────────────────────────────────────────────────────────┤
│                                                              │
│   ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐   │
│   │ Frame  │ │ Frame  │ │ Frame  │ │ Frame  │ │ Frame  │   │
│   │   0    │ │   1    │ │   2    │ │   3    │ │  ...   │   │
│   │        │ │        │ │        │ │        │ │        │   │
│   │ Page   │ │ Page   │ │ Page   │ │ Empty  │ │        │   │
│   │ P101   │ │ P205   │ │ P42    │ │        │ │        │   │
│   └────────┘ └────────┘ └────────┘ └────────┘ └────────┘   │
│       │          │          │                               │
│       ▼          ▼          ▼                               │
│   ┌─────────────────────────────────────────────────────┐  │
│   │              PAGE TABLE / HASH TABLE                 │  │
│   │  PageID → FrameID, PinCount, DirtyBit, LSN          │  │
│   └─────────────────────────────────────────────────────┘  │
│                                                              │
└──────────────────────────────────────────────────────────────┘
                            │
                            │ I/O Subsystem
                            ▼
┌──────────────────────────────────────────────────────────────┐
│                          DISK                                 │
│  ┌────┐ ┌────┐ ┌────┐ ┌────┐ ┌────┐ ┌────┐ ┌────┐         │
│  │P1  │ │P2  │ │P3  │ │... │ │P42 │ │... │ │Pn  │         │
│  └────┘ └────┘ └────┘ └────┘ └────┘ └────┘ └────┘         │
└──────────────────────────────────────────────────────────────┘
```

### Buffer Pool Metadata

```
Page Table Entry:
┌────────────────────────────────────────────────────┐
│ PageID       │ Identifier of page in this frame    │
│ FrameID      │ Buffer frame number                 │
│ PinCount     │ Number of transactions using page   │
│ DirtyBit     │ True if page modified since load    │
│ PageLSN      │ LSN of last update to this page     │
│ RecLSN       │ LSN of first update (for recovery)  │
│ RefBit       │ Used by clock algorithm             │
└────────────────────────────────────────────────────┘
```

---

## Page Replacement Policies

### When Replacement is Needed

```
Request for Page P (not in buffer):
1. No free frames available
2. Must evict an existing page
3. Choose victim using replacement policy
4. If victim is dirty, write to disk first
5. Load requested page P into frame
```

### Common Replacement Algorithms

| Algorithm | Description | Pros | Cons |
|-----------|-------------|------|------|
| LRU | Evict least recently used | Good general performance | High overhead |
| Clock | Approximation of LRU | Lower overhead | Less precise |
| LRU-K | Consider K-th access | Better for scans | Complex |
| 2Q | Two queues (hot/cold) | Scan resistant | More memory |

### LRU (Least Recently Used)

```
LRU Queue: [Most Recent] ←────────────→ [Least Recent]

Access page P5:
Before: P1 → P3 → P5 → P2 → P4
After:  P5 → P1 → P3 → P2 → P4
        ↑                    ↑
    Moved to front      Victim candidate

Eviction: Remove from tail (P4)
```

### Clock Algorithm (Second Chance)

```
           ┌───────────────────┐
           │                   │
           ▼                   │
     ┌──────────┐              │
     │  Frame 0 │ RefBit: 1    │
     │  (Page A)│              │
     └──────────┘              │
           │                   │
           ▼                   │
     ┌──────────┐              │
     │  Frame 1 │ RefBit: 0  ◄─── Clock hand (victim!)
     │  (Page B)│              │
     └──────────┘              │
           │                   │
           ▼                   │
     ┌──────────┐              │
     │  Frame 2 │ RefBit: 1    │
     │  (Page C)│              │
     └──────────┘              │

---

## Buffer Management and Recovery

### STEAL Policy

Dirty pages CAN be written to disk before transaction commits.

```
┌─────────────────────────────────────────────────────────────┐
│                    STEAL POLICY                              │
│                                                             │
│  T1 modifies Page P                                         │
│       │                                                     │
│       ▼                                                     │
│  Buffer Manager needs frame                                 │
│       │                                                     │
│       ▼                                                     │
│  P is victim (even though T1 not committed)                 │
│       │                                                     │
│       ▼                                                     │
│  Write dirty page P to disk                                 │
│       │                                                     │
│       ▼                                                     │
│  P now on disk with uncommitted changes!                    │
│                                                             │
│  If T1 aborts: Must UNDO changes using log                  │
│  If system crashes before T1 commits: Must UNDO on recovery │
│                                                             │
│  Implication: REQUIRES UNDO CAPABILITY                      │
└─────────────────────────────────────────────────────────────┘
```

### NO-STEAL Policy

Dirty pages CANNOT be written to disk until transaction commits.

```
┌─────────────────────────────────────────────────────────────┐
│                   NO-STEAL POLICY                            │
│                                                             │
│  T1 modifies Page P                                         │
│       │                                                     │
│       ▼                                                     │
│  P is dirty, pinned by T1                                   │
│       │                                                     │
│       ▼                                                     │
│  Buffer Manager cannot evict P                              │
│       │                                                     │
│       ▼                                                     │
│  If T1 aborts: Just discard P from buffer                   │
│  No UNDO needed!                                            │
│                                                             │
│  Problem: May run out of buffer space                       │
│  Problem: Long transactions hold many frames                │
│                                                             │
│  Implication: NO UNDO NEEDED, BUT LIMITED SCALABILITY       │
└─────────────────────────────────────────────────────────────┘
```

### FORCE Policy

All dirty pages written to disk at commit time.

```
┌─────────────────────────────────────────────────────────────┐
│                    FORCE POLICY                              │
│                                                             │
│  T1 commits:                                                │
│       │                                                     │
│       ▼                                                     │
│  Find all dirty pages modified by T1                        │
│       │                                                     │
│       ▼                                                     │
│  Write ALL of them to disk                                  │
│       │                                                     │
│       ▼                                                     │
│  Then write COMMIT record                                   │
│                                                             │
│  If system crashes after commit:                            │
│  All changes already on disk - NO REDO NEEDED               │
│                                                             │
│  Problem: Random I/O at commit time (slow)                  │
│  Problem: Hot pages written repeatedly                      │
│                                                             │
│  Implication: NO REDO NEEDED, BUT SLOW COMMITS              │
└─────────────────────────────────────────────────────────────┘
```

### NO-FORCE Policy

Dirty pages MAY remain in buffer after transaction commits.

```
┌─────────────────────────────────────────────────────────────┐
│                   NO-FORCE POLICY                            │
│                                                             │
│  T1 commits:                                                │
│       │                                                     │
│       ▼                                                     │
│  Write COMMIT record to log                                 │
│       │                                                     │
│       ▼                                                     │
│  Return success to application                              │
│  (Dirty pages may still be in buffer!)                      │
│                                                             │
│  Background: Eventually write dirty pages                   │
│                                                             │
│  If system crashes before pages written:                    │
│  Must REDO committed changes from log                       │
│                                                             │
│  Advantage: Fast commits (sequential log write only)        │
│                                                             │
│  Implication: REQUIRES REDO CAPABILITY                      │
└─────────────────────────────────────────────────────────────┘
```

### Policy Matrix Summary

```
                    │     FORCE      │    NO-FORCE    │
────────────────────┼────────────────┼────────────────┤
                    │ UNDO: No       │ UNDO: No       │
    NO-STEAL        │ REDO: No       │ REDO: Yes      │
                    │ Worst Perf     │ Shadow Paging  │
────────────────────┼────────────────┼────────────────┤
                    │ UNDO: Yes      │ UNDO: Yes      │
    STEAL           │ REDO: No       │ REDO: Yes      │
                    │ Rare           │ ARIES (Best)   │
────────────────────┴────────────────┴────────────────┘
```

---

## Buffer Manager Interface

### Core Operations

```
PIN(PageID):
    IF page in buffer:
        frame = lookup(PageID)
        frame.pinCount++
    ELSE:
        frame = allocate_frame()  // May need replacement
        read_page(PageID, frame)
        frame.pinCount = 1
    RETURN frame

UNPIN(PageID, dirty):
    frame = lookup(PageID)
    frame.pinCount--
    IF dirty:
        frame.dirtyBit = true

FLUSH(PageID):
    frame = lookup(PageID)
    IF frame.dirtyBit:
        write_page(frame, disk)
        frame.dirtyBit = false
```

### Pin Count Semantics

```
Pin Count = Number of transactions currently using the page

┌────────────────────────────────────────────────────────┐
│ PinCount > 0: Page is in use, cannot be evicted        │
│ PinCount = 0: Page can be selected as victim           │
│                                                        │
│ Example:                                               │
│ T1: PIN(P5)         → PinCount(P5) = 1                 │
│ T2: PIN(P5)         → PinCount(P5) = 2                 │
│ T1: UNPIN(P5)       → PinCount(P5) = 1                 │
│ T2: UNPIN(P5)       → PinCount(P5) = 0  ← Can evict    │
└────────────────────────────────────────────────────────┘
```

---

## Advanced Topics

### Double Buffering

```
Prefetch next page while processing current:

┌──────────────────────────────────────────────────────┐
│                                                      │
│  Buffer A ◄── Reading P2      Processing P1 ──► App │
│                                                      │
│  When P1 done:                                       │
│  - Switch: Process P2, Read P3 into A               │
│                                                      │
└──────────────────────────────────────────────────────┘
```

### Write-Behind (Background Writing)

```
Dedicated thread writes dirty pages to disk:
- Reduces work at checkpoint
- Smooths I/O load
- Prioritizes cold dirty pages
```

### Buffer Pool Sizing

Jim Gray's Five-Minute Rule:
> If a page is accessed more often than every 5 minutes, keep it in memory.

```
Break-even calculation:
Cost of memory to cache page = Cost of I/O to fetch on demand

Factors:
- Memory cost per MB
- Disk I/O rate
- Access frequency
```

---

## Key Takeaways

1. **Buffer pool** is critical for database performance
2. **Page replacement** algorithms trade accuracy for overhead
3. **STEAL/NO-FORCE** provides best performance (used by ARIES)
4. **Pin counts** prevent eviction of in-use pages
5. **Background writing** smooths I/O load
6. **Buffer sizing** follows Gray's Five-Minute Rule

---

## References

- Gray, J. & Reuter, A. (1993). Chapter 7: "System Structure"
- O'Neil, E. et al. (1993). "The LRU-K Page Replacement Algorithm for Database Disk Buffering"
- Gray, J. & Graefe, G. (1997). "The Five-Minute Rule Ten Years Later"

           │                   │
           └───────────────────┘

Algorithm:
1. Check frame at clock hand
2. If RefBit = 0: This is the victim
3. If RefBit = 1: Set RefBit = 0, advance clock
4. Repeat until victim found
```

### LRU-K Algorithm

Considers the K-th most recent access, not just the most recent.
```
LRU-2 Example (K=2):
Page A: Last accesses at t=100, t=50   → 2nd-last = 50
Page B: Last accesses at t=90, t=80    → 2nd-last = 80
Page C: Last accesses at t=95, t=20    → 2nd-last = 20

Evict page with oldest K-th access: Page C (2nd-last = 20)

Benefit: Filters out sequential scans
- Scan touches each page once
- With LRU-2, scan pages have no K-th access
- They're evicted immediately
```

