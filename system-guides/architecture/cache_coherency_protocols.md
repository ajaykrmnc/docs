# Cache Coherency Protocols for System Programmers

## Introduction

Cache coherency ensures that multiple processor cores have a consistent view of memory despite having private caches. This document explains the cache coherency problem, protocols (MESI, MOESI), and their implications for concurrent programming.

**Key Learning Objectives:**
- Understand the cache coherency problem in multiprocessor systems
- Learn MESI and MOESI coherency protocols
- Understand false sharing and its performance impact
- Recognize memory ordering and synchronization implications
- Write cache-coherent code for multicore systems

## 1. The Cache Coherency Problem

### 1.1 Why Coherency Matters

**Modern multicore system:**
```
┌─────────┐        ┌─────────┐        ┌─────────┐
│ Core 0  │        │ Core 1  │        │ Core 2  │
│  L1-I   │        │  L1-I   │        │  L1-I   │
│  L1-D   │        │  L1-D   │        │  L1-D   │
└────┬────┘        └────┬────┘        └────┬────┘
     │                  │                  │
     └──────────┬───────┴──────────┬───────┘
                │                  │
           ┌────▼────┐        ┌────▼────┐
           │   L2    │        │   L2    │
           └────┬────┘        └────┬────┘
                │                  │
                └────────┬─────────┘
                         │
                    ┌────▼────┐
                    │   L3    │
                    │(Shared) │
                    └────┬────┘
                         │
                    ┌────▼────┐
                    │  Memory │
                    └─────────┘
```

**Problem**: Each core has private L1/L2 caches.

**Example scenario:**
```c
// Shared variable in memory
int x = 0;  // Address 0x1000

// Core 0
x = 1;      // Writes to L1 cache

// Core 1
int y = x;  // Reads from L1 cache - should see value 1!
```

**Without coherency**: Core 1's L1 cache still has old value (0).

### 1.2 Cache Coherency Requirements

**Definition**: A memory system is coherent if:

1. **Read returns latest write**: If P1 writes X and P2 reads X (with no intervening writes), P2 must see P1's value
2. **Write serialization**: Two writes to X must be seen in same order by all processors
3. **Write propagation**: Write must eventually be visible to all processors

### 1.3 Coherency vs. Consistency

**Coherency**: Defines behavior for *single* memory location
**Consistency**: Defines behavior for *multiple* memory locations (memory ordering)

```c
// Thread 1          // Thread 2
x = 1;               y = 1;
r1 = y;              r2 = x;

// Can we observe r1 == 0 && r2 == 0?
// Coherency: No (each location updated correctly)
// Consistency: Depends on memory model! (covered in other docs)
```

## 2. Snooping-Based Coherency

### 2.1 Bus-Based Snooping

**Concept**: All caches monitor (snoop) shared bus for memory operations.

**Components:**
- **Shared bus**: Connects all caches and memory
- **Snooping logic**: Each cache monitors bus traffic
- **State tracking**: Each cache line has coherency state

**Operation:**
```
Core 0 writes X:
1. Broadcast write on bus
2. All other caches snoop
3. Caches with X invalidate or update their copy
4. Memory updated (or marked dirty)
```

### 2.2 Write-Invalidate vs. Write-Update

**Write-Invalidate** (more common):
- Writer invalidates other copies
- Next read causes cache miss
- **Benefit**: Less bus traffic (single invalidate message)

**Write-Update**:
- Writer updates all copies
- Next read hits in cache
- **Benefit**: Lower read latency
- **Cost**: More bus traffic (update for every write)

**Modern systems**: Use write-invalidate (MESI/MOESI family).

## 3. MESI Protocol

### 3.1 The Four States

Each cache line can be in one of four states:

**M - Modified**:
- Cache line is dirty (modified)
- Only this cache has the line
- Memory is stale (out of date)
- **Responsibility**: Must write back to memory on eviction

**E - Exclusive**:
- Cache line is clean (matches memory)
- Only this cache has the line
- Can transition to M without bus transaction

**S - Shared**:
- Cache line is clean
- Multiple caches may have the line
- Matches memory

**I - Invalid**:
- Cache line is invalid
- Must fetch from memory/other cache if needed

### 3.2 State Transitions

**Processor events:**
- **PrRd**: Processor read
- **PrWr**: Processor write

**Bus events:**
- **BusRd**: Another processor read (snooped)
- **BusRdX**: Another processor read-exclusive/write (snooped)
- **BusUpgr**: Another processor upgrades S→M (snooped)
- **Flush**: Write-back to memory

**State diagram:**

```
                    PrWr/BusUpgr
             ┌──────────────────────┐
             │                      │
             ▼                      │
┌─────┐  PrWr   ┌─────┐  PrRd    ┌─────┐
│  M  │◄────────│  E  │◄─────────│  I  │
└──┬──┘         └──┬──┘          └──┬──┘
   │               │                │
   │ BusRd         │ BusRd          │ PrRd (shared)
   │               │                │
   └───────┬───────┴────────────────┘
           │
           ▼
        ┌─────┐
        │  S  │
        └──┬──┘
           │
           │ PrWr
           ▼
        ┌─────┐
        │  M  │
        └─────┘
```

### 3.3 MESI Example

**Initial state**:
```
Memory[X] = 0
Core 0 cache: - (Invalid)
Core 1 cache: - (Invalid)
```

**Step 1: Core 0 reads X**
```
Action: PrRd
Core 0: I → E (exclusive, clean)
Bus: BusRd
Memory: Provides value 0
```

**Step 2: Core 1 reads X**
```
Action: PrRd
Core 0: E → S (shared, clean)
Core 1: I → S (shared, clean)
Bus: BusRd
Core 0: Provides value 0 (or memory)
```

**Step 3: Core 0 writes X = 1**
```
Action: PrWr
Core 0: S → M (modified, dirty)
Core 1: S → I (invalidated)
Bus: BusUpgr (or BusRdX)
Core 1: Invalidates its copy
```

**Step 4: Core 1 reads X**
```
Action: PrRd
Core 0: M → S (flush to memory/provide to Core 1)
Core 1: I → S
Bus: BusRd
Core 0: Provides value 1
Memory: Updated to 1 (write-back)
```

## 4. MOESI Protocol

### 4.1 The Fifth State: Owned

**O - Owned**:
- Cache line is dirty (modified)
- Multiple caches may have the line (shared)
- **This cache owns the line** (responsible for write-back)
- Other caches have line in S state

**Benefit**: Avoid writing back to memory when sharing dirty data.

**Example: M → O transition**
```
Core 0 has X in M state (dirty, value = 5)
Core 1 reads X

MESI: M → S (must flush to memory first)
MOESI: M → O (provide directly to Core 1, no memory write)

Result:
Core 0: O (dirty, owns)
Core 1: S (clean copy of dirty data)
Memory: Still old value (will be updated when Core 0 evicts)
```

### 4.2 MOESI States Summary

```
M: Modified (exclusive, dirty)
O: Owned (shared, dirty)
E: Exclusive (exclusive, clean)
S: Shared (shared, clean)
I: Invalid
```

**Key difference**: O allows sharing of dirty data without memory write-back.

## 5. Performance Implications

### 5.1 Cache Line Size

**Typical cache line**: 64 bytes

**Important**: Coherency operates at cache line granularity, not byte granularity.

```c
struct {
    int a;  // Offset 0
    int b;  // Offset 4
    int c;  // Offset 8
    int d;  // Offset 12
} data;  // All in same 64-byte cache line
```

**If Core 0 writes `a` and Core 1 writes `b`**:
- Both modify same cache line
- Coherency protocol invalidates between cores
- **False sharing** (explained below)

### 5.2 False Sharing

**Definition**: Multiple cores access different data in the same cache line.

**Example:**
```c
// Bad: False sharing
struct {
    int counter0;  // Used by Core 0
    int counter1;  // Used by Core 1
} shared;  // Both in same cache line!

// Core 0
while (1) shared.counter0++;

// Core 1
while (1) shared.counter1++;
```

**Performance impact:**
```
Core 0 writes counter0:
- Core 0: E/M state
- Core 1: I state (invalidated!)

Core 1 writes counter1:
- Core 1: E/M state
- Core 0: I state (invalidated!)

Result: Ping-pong cache line between cores (100× slowdown!)
```

**Solution: Padding**
```c
// Good: No false sharing
struct {
    int counter0;
    char pad0[60];  // Pad to 64 bytes
    int counter1;
    char pad1[60];
} shared;

// Or use cache line alignment
struct alignas(64) {
    int counter0;
} core0_data;

struct alignas(64) {
    int counter1;
} core1_data;
```

### 5.3 True Sharing Performance
