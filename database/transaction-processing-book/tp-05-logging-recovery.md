# Logging and Recovery

## Overview

Recovery is the mechanism that ensures database consistency after failures. Jim Gray's work on recovery algorithms, culminating in the ARIES algorithm, represents one of the most significant contributions to database systems.

---

## Failure Types

### Classification of Failures

| Failure Type | Examples | Data Loss | Recovery Approach |
|--------------|----------|-----------|-------------------|
| Transaction | Abort, deadlock | None | Undo transaction |
| System | OS crash, power failure | Buffer contents | Log-based recovery |
| Media | Disk failure | Stored data | Backup + archive logs |

### Failure Timeline

```
Normal Operation     System Crash      Recovery
      │                   │               │
──────┼───────────────────┼───────────────┼──────────►
      │                   │               │
  Transactions        Memory lost     Log replay
   in progress        Buffer contents   to restore
                      lost             consistency
```

---

## Write-Ahead Logging (WAL)

### The WAL Protocol

> **WAL Rule:** Before a data page is written to disk, all log records describing changes to that page must be written to stable storage.

### Why WAL Works

```
Without WAL (Problem):
1. Write data page to disk (with new value)
2. System crashes before log written
3. On recovery: No log record exists
4. Cannot undo the change → Inconsistency!

With WAL (Safe):
1. Write log record to stable storage
2. THEN write data page to disk
3. System crashes at any point
4. On recovery: Log contains all info needed
5. Can REDO or UNDO as needed → Consistency!
```

### Log Record Structure

```
┌──────────────────────────────────────────────────────────┐
│                    LOG RECORD                             │
├──────────────────────────────────────────────────────────┤
│ LSN          │ Log Sequence Number (unique, increasing)  │
│ TransID      │ Transaction that made the change          │
│ PrevLSN      │ Previous log record of this transaction   │
│ Type         │ UPDATE, COMMIT, ABORT, CHECKPOINT, etc.   │
│ PageID       │ Page that was modified                    │
│ Offset       │ Position within page                      │
│ BeforeImage  │ Old value (for UNDO)                      │
│ AfterImage   │ New value (for REDO)                      │
└──────────────────────────────────────────────────────────┘
```

### Log Types

| Log Type | Contains | Supports |
|----------|----------|----------|
| UNDO-only | Before images | Rollback |
| REDO-only | After images | Replay |
| UNDO-REDO | Both images | Full recovery |

---

## Buffer Management and Recovery

### STEAL vs NO-STEAL Policy

**STEAL:** Dirty pages can be flushed to disk before transaction commits
**NO-STEAL:** Dirty pages cannot be flushed until transaction commits

```
STEAL Policy:
┌─────────────────────────────────────────────────────────┐
│ T1 modifies page P                                      │
│ Buffer manager needs space → Flushes P to disk          │
│ T1 later ABORTS                                         │
│ Problem: P on disk has uncommitted changes!             │
│ Solution: UNDO using log (requires UNDO capability)     │
└─────────────────────────────────────────────────────────┘

NO-STEAL Policy:
┌─────────────────────────────────────────────────────────┐
│ T1 modifies page P                                      │
│ P stays in buffer until T1 commits                      │
│ If T1 aborts: Simply discard P from buffer              │
│ Advantage: No UNDO needed for recovery                  │
│ Disadvantage: May run out of buffer space               │
└─────────────────────────────────────────────────────────┘
```

### FORCE vs NO-FORCE Policy

**FORCE:** All dirty pages written to disk at commit
**NO-FORCE:** Dirty pages can remain in buffer after commit

```
FORCE Policy:
┌─────────────────────────────────────────────────────────┐
│ T1 commits → All T1's dirty pages written to disk       │
│ Advantage: No REDO needed (changes always on disk)      │
│ Disadvantage: High I/O at commit (slow commits)         │
└─────────────────────────────────────────────────────────┘

### Types of Checkpoints

#### Simple (Consistent) Checkpoint

```
1. Stop accepting new transactions
2. Wait for all active transactions to complete
3. Flush all dirty pages to disk
4. Write checkpoint record to log
5. Resume normal operation

Disadvantage: System unavailable during checkpoint
```

#### Fuzzy Checkpoint

```
1. Write BEGIN_CHECKPOINT to log
2. Record list of active transactions
3. Record list of dirty pages in buffer
4. Continue normal operation
5. Write END_CHECKPOINT to log

Advantage: System remains available
Disadvantage: More complex recovery
```

### Checkpoint Record Contents

```
CHECKPOINT RECORD:
┌──────────────────────────────────────────────────────────┐
│ Active Transaction Table (ATT)                           │
│ ┌────────────────────────────────────────────────────┐  │
│ │ TxnID │ Status │ LastLSN │ UndoNextLSN           │  │
│ │ T1    │ Active │ 1050    │ 1050                   │  │
│ │ T2    │ Active │ 1055    │ 1040                   │  │
│ └────────────────────────────────────────────────────┘  │
│                                                          │
│ Dirty Page Table (DPT)                                   │
│ ┌────────────────────────────────────────────────────┐  │
│ │ PageID │ RecLSN (first update to dirty page)       │  │
│ │ P1     │ 1020                                      │  │
│ │ P2     │ 1035                                      │  │
│ │ P3     │ 1048                                      │  │
│ └────────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────┘
```

---

## ARIES Recovery Algorithm

### Overview

ARIES (Algorithm for Recovery and Isolation Exploiting Semantics) is the gold standard recovery algorithm, developed by C. Mohan at IBM Research, building on Jim Gray's foundations.

### ARIES Principles

1. **Write-Ahead Logging:** Log before data
2. **Repeating History:** Redo all actions before selective undo
3. **Logging Changes During Undo:** Compensation Log Records (CLRs)

### The Three Phases of ARIES

```
┌─────────────────────────────────────────────────────────────┐
│                    ARIES RECOVERY                            │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  PHASE 1: ANALYSIS                                          │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ • Start from last checkpoint                         │   │
│  │ • Scan log forward                                   │   │
│  │ • Rebuild ATT (Active Transaction Table)             │   │
│  │ • Rebuild DPT (Dirty Page Table)                     │   │
│  │ • Determine: RedoLSN, loser transactions             │   │
│  └─────────────────────────────────────────────────────┘   │
│                         │                                   │
│                         ▼                                   │
│  PHASE 2: REDO                                              │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ • Start from RedoLSN (min RecLSN in DPT)            │   │
│  │ • Scan log forward                                   │   │
│  │ • For each update/CLR record:                        │   │
│  │   - If page in DPT and RecLSN ≤ LSN:                │   │
│  │     Redo the operation                               │   │
│  │ • Restores database to crash-time state              │   │
│  └─────────────────────────────────────────────────────┘   │
│                         │                                   │
│                         ▼                                   │
│  PHASE 3: UNDO                                              │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ • Process loser transactions (uncommitted at crash)  │   │
│  │ • Scan log backward                                  │   │
│  │ • For each loser's update:                           │   │
│  │   - Undo the operation                               │   │
│  │   - Write Compensation Log Record (CLR)              │   │
│  │ • Continue until all losers undone                   │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### Compensation Log Records (CLRs)

```
CLR Structure:
┌──────────────────────────────────────────────────────────┐
│ LSN          │ 2001 (new LSN for this CLR)               │
│ TransID      │ T1                                        │
│ PrevLSN      │ 1050 (previous record for T1)             │
│ Type         │ CLR                                       │
│ PageID       │ P5                                        │
│ UndoAction   │ Restore old value                         │
│ UndoNextLSN  │ 1030 (next record to undo for T1)         │
└──────────────────────────────────────────────────────────┘

Purpose:
• CLRs ensure undo operations are never undone
• If crash during recovery, CLRs prevent re-doing undos
```

### ARIES Example

```
Log before crash:
LSN  | Type   | TxnID | PageID | Before | After | PrevLSN
-----+--------+-------+--------+--------+-------+---------
100  | UPDATE | T1    | P1     | A      | B     | -
110  | UPDATE | T2    | P2     | X      | Y     | -
120  | UPDATE | T1    | P1     | B      | C     | 100
130  | COMMIT | T2    | -      | -      | -     | 110
140  | UPDATE | T1    | P3     | M      | N     | 120
150  | CHKPT  | -     | -      | -      | -     | -
      ATT: {T1: LastLSN=140}
      DPT: {P1: RecLSN=100, P3: RecLSN=140}
160  | UPDATE | T1    | P1     | C      | D     | 140
--- CRASH ---

ANALYSIS (from checkpoint 150):
• ATT: T1 is active (loser)
• DPT: P1 needs redo from LSN 100, P3 from LSN 140

REDO (from RedoLSN = 100):
• Redo all updates (100, 110, 120, 140, 160)

UNDO (T1 is loser):
• Undo LSN 160: D→C, write CLR
• Undo LSN 140: N→M, write CLR
• Undo LSN 120: C→B, write CLR
• Undo LSN 100: B→A, write CLR
• T1 fully undone
```

---

## Media Recovery

### Archive Logging

For recovering from disk failures:

```
┌───────────────────────────────────────────────────────────┐
│                    MEDIA RECOVERY                          │
│                                                           │
│  ┌────────────┐    ┌────────────┐    ┌────────────┐      │
│  │  Full      │───►│  Archive   │───►│  Archive   │      │
│  │  Backup    │    │  Log 1     │    │  Log 2     │...   │
│  │  (t=0)     │    │  (t=0→t1)  │    │  (t1→t2)   │      │
│  └────────────┘    └────────────┘    └────────────┘      │
│        │                 │                 │              │
│        └─────────────────┴─────────────────┘              │
│                         │                                 │
│                         ▼                                 │
│            Restore backup + apply archive logs            │
│            to recover to any point in time                │
│                                                           │
└───────────────────────────────────────────────────────────┘
```

### Point-in-Time Recovery

```
Timeline:
─────┬──────────────┬──────────────┬──────────────┬─────────
   Full           Archive        Archive       Disk
  Backup           Log 1          Log 2       Failure
   (t0)            (t1)           (t2)         (t3)

To recover to time T (t0 < T < t3):
1. Restore full backup from t0
2. Apply archive logs up to time T
3. Stop at T (partial archive log application)
```

---

## Key Takeaways

1. **WAL** is the foundation - log before writing data
2. **STEAL/NO-FORCE** provides best performance but needs both REDO and UNDO
3. **Checkpoints** limit recovery time
4. **ARIES** is the gold standard: Analysis → Redo → Undo
5. **CLRs** ensure idempotent recovery
6. **Archive logs** enable point-in-time recovery

---

## References

- Gray, J. & Reuter, A. (1993). Chapters 14-18: "Recovery"
- Mohan, C. et al. (1992). "ARIES: A Transaction Recovery Method Supporting Fine-Granularity Locking and Partial Rollbacks Using Write-Ahead Logging"
- Gray, J. (1978). "Notes on Data Base Operating Systems"


NO-FORCE Policy:
┌─────────────────────────────────────────────────────────┐
│ T1 commits → Only log record written to disk            │
│ Dirty pages may remain in buffer                        │
│ Advantage: Fast commits                                 │
│ Disadvantage: Must REDO committed changes after crash   │
└─────────────────────────────────────────────────────────┘
```

### Policy Combinations

| Policy | UNDO needed | REDO needed | Performance |
|--------|-------------|-------------|-------------|
| NO-STEAL + FORCE | No | No | Worst |
| NO-STEAL + NO-FORCE | No | Yes | Better |
| STEAL + FORCE | Yes | No | Better |
| STEAL + NO-FORCE | Yes | Yes | Best (ARIES uses this) |

---

## Checkpointing

### Purpose of Checkpoints

Limit the amount of log that must be scanned during recovery.

```
Without Checkpoints:
Log: |─────────────────────────────────────────────| Crash
     ^ Must scan from beginning                    ^

With Checkpoints:
Log: |────────|─────────|─────────|────────| Crash
            Checkpoint        Checkpoint    ^
                                           Start here
```

