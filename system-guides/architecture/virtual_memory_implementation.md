# Virtual Memory Implementation for System Programmers

## Introduction

Virtual memory is a memory management technique that provides each process with its own address space, 
enabling memory protection, sharing, and efficient physical memory usage. This document covers the 
implementation details of virtual memory systems.

**Key Learning Objectives:**
- Understand virtual to physical address translation
- Learn page table structures (single-level, multi-level, inverted)
- Understand Translation Lookaside Buffer (TLB)
- Learn page fault handling and demand paging
- Understand huge pages and their performance benefits

## 1. Virtual Memory Basics

### 1.1 Address Translation

**Virtual Address** → **Physical Address**

```
┌──────────────────────────────────────────────┐
│         Virtual Address (64-bit)              │
│  ┌──────────────────┬─────────────────────┐  │
│  │   VPN (52 bits)  │  Offset (12 bits)   │  │
│  └──────────────────┴─────────────────────┘  │
└──────────────────────┬───────────────────────┘
                       │ Translation
                       ▼
┌──────────────────────────────────────────────┐
│        Physical Address (52-bit PA)           │
│  ┌──────────────────┬─────────────────────┐  │
│  │   PPN (40 bits)  │  Offset (12 bits)   │  │
│  └──────────────────┴─────────────────────┘  │
└──────────────────────────────────────────────┘

Page size: 4 KB (2^12 bytes)
VPN: Virtual Page Number
PPN: Physical Page Number
Offset: Unchanged (4096 bytes within page)
```

### 1.2 Page Table Structure

**Single-level page table:**
```
VPN → Page Table Entry (PTE)

PTE format (64-bit):
┌───────────────────────────────────────────────────────┐
│ PPN (40) │ Flags (24)                                   │
│          │ [Present|R/W|User|Dirty|Accessed|...]       │
└───────────────────────────────────────────────────────┘
```

**Flags:**
- **P (Present)**: Page in physical memory (1) or swapped out (0)
- **R/W**: Read-only (0) or Read/Write (1)
- **U/S**: User (1) or Supervisor (0)
- **D (Dirty)**: Page modified since loaded
- **A (Accessed)**: Page accessed (read/write) since last cleared
- **NX (No Execute)**: Prevent code execution from this page

### 1.3 Multi-Level Page Tables

**Problem with single-level**: 64-bit address space needs huge page table.

**Example:**
- 48-bit virtual address
- 4 KB pages
- VPN = 48 - 12 = 36 bits
- Page table entries = 2^36 = 68 billion
- Size = 68B × 8 bytes = 544 GB per process!

**Solution: Multi-level (hierarchical) page tables**

**x86-64 4-level paging:**
```
Virtual Address (48-bit):
┌──────┬──────┬──────┬──────┬──────────────┐
│  L4  │  L3  │  L2  │  L1  │   Offset     │
│(9bit)│(9bit)│(9bit)│(9bit)│   (12bit)    │
└──────┴──────┴──────┴──────┴──────────────┘
  PML4   PDPT    PD     PT     Page offset

Translation process:
1. CR3 register → PML4 base address
2. L4 index → PML4 entry → PDPT base
3. L3 index → PDPT entry → PD base
4. L2 index → PD entry → PT base
5. L1 index → PT entry → PPN
6. PPN + Offset → Physical Address
```

**Advantages:**
- Sparse address spaces (only allocate needed tables)
- Typical process: ~few MB page tables vs 544 GB

**Example: Sparse mapping**
```
Process uses:
- Stack: 0x00007fff0000 - 0x00007fffffff (16 MB)
- Heap: 0x0000555500000000 - 0x0000555500100000 (1 MB)
- Code: 0x0000555555554000 - 0x0000555555600000 (704 KB)

Page tables needed:
- 1 PML4 table (always needed)
- 3 PDPT tables (one per distinct L4 index)
- ~10 PD tables
- ~100 PT tables
Total: ~1 MB (vs 544 GB!)
```

## 2. Translation Lookaside Buffer (TLB)

### 2.1 The Performance Problem

**Page table walk cost:**
- 4 levels × memory access
- 4 × ~200 cycles = 800 cycles per translation
- **Every** memory access needs translation!

**Example:**
```c
int sum = 0;
for (int i = 0; i < n; i++) {
    sum += array[i];  // Load requires: TLB lookup + memory access
}
```

Without TLB: 800 + 4 = 804 cycles per load! (200× slowdown)

### 2.1 TLB Structure

**TLB**: Cache for VPN → PPN translations.

**TLB Entry:**
```
┌──────────────────────────────────────────────┐
│ Tag (VPN) │ PPN │ Flags │ Valid │ ASID      │
└──────────────────────────────────────────────┘

ASID: Address Space ID (process ID) to avoid flushing on context switch
```

**Typical TLB:**
- L1 DTLB (Data): 64 entries (4-way set-associative)
- L1 ITLB (Instruction): 128 entries
- L2 TLB (Unified): 1536 entries (12-way)

### 2.2 TLB Lookup

```
Virtual Address → TLB

TLB Hit:
  Physical Address = TLB[VPN].PPN || Offset
  Cost: 1 cycle

TLB Miss:
  Page Table Walk (4 levels)
  Insert into TLB
  Cost: ~200 cycles
```

**Hit rate:** Typically 99%+ for most applications.

### 2.3 TLB Performance Impact

**Example: Memory-intensive loop**
```c
#define SIZE (1024 * 1024)  // 1M elements
int array[SIZE];            // 4 MB

// Sequential access
for (int i = 0; i < SIZE; i++) {
    sum += array[i];
}
```

**TLB analysis:**
- Array size: 4 MB
- Page size: 4 KB
- Pages accessed: 4 MB / 4 KB = 1024 pages
- TLB capacity: 64 entries (L1 DTLB)
- **TLB misses**: ~960 (every 64 accesses)

**With huge pages (2 MB):**
- Pages accessed: 4 MB / 2 MB = 2 pages
- TLB misses: 2 (initial misses only)
- **94× reduction in TLB misses!**

## 3. Page Fault Handling

### 3.1 Page Fault Types

**Minor page fault**: Page not in TLB, but in physical memory
- **Cause**: TLB miss, page table walk needed
- **Handler**: Update TLB
- **Cost**: ~200 cycles

**Major page fault**: Page not in physical memory
- **Cause**: Page swapped to disk, never allocated, copy-on-write
- **Handler**: Load from disk / allocate / copy
- **Cost**: ~5-10 million cycles (disk I/O)

### 3.2 Page Fault Flow

```
1. Instruction accesses virtual address
2. TLB miss → Page table walk
3. PTE.Present == 0 → Page fault exception
4. CPU saves state, jumps to page fault handler
5. OS determines fault type:
   a. Demand paging: Load page from disk
   b. Copy-on-write: Allocate new page, copy
   c. Lazy allocation: Allocate new page, zero
   d. Protection violation: SIGSEGV
6. Update page table
7. Resume instruction (retry)
```

### 3.3 Demand Paging

**Idea**: Don't load pages until accessed.

```c
// Process starts
void* ptr = mmap(NULL, 1GB, PROT_READ|PROT_WRITE, MAP_PRIVATE|MAP_ANONYMOUS, -1, 0);

// No physical memory allocated yet!
// Page tables mark pages as "not present"

ptr[0] = 42;  // First access → Page fault
              // OS allocates one 4KB page
              // Only 4KB of 1GB allocated!
```

**Benefits:**
- Fast process startup
- Efficient memory use (only allocate what's accessed)
- Enables overcommit

### 3.4 Copy-on-Write (COW)

**Scenario**: fork() creates child process

**Naive approach**: Copy all parent pages (slow, wastes memory)

**COW approach**:
```
1. fork(): Mark all pages read-only in both parent and child
2. Both processes share same physical pages
3. On write: Page fault → OS allocates new page, copies data
```

**Example:**
```c
int main() {
    char data[1GB];  // 1 GB data
    pid_t pid = fork();
    
    if (pid == 0) {
        // Child: Reads data (no fault, shares parent's pages)
        printf("%d\n", data[0]);
        
        // Child: Writes data (page fault, copy needed)
        data[0] = 42;  // Triggers COW for one page
    }
}
```

## 4. Huge Pages

### 4.1 Huge Page Sizes

**x86-64 supports:**
- 4 KB (standard)
- 2 MB (huge page, -DHUGE
