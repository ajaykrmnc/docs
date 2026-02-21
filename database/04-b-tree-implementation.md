# Chapter 4: B-Tree Implementation Details

## Table of Contents

1. [Page Structure and Layout](#page-structure-and-layout)
2. [Slotted Page Organization](#slotted-page-organization)
3. [Variable-Length Data](#variable-length-data)
4. [Overflow Pages](#overflow-pages)
5. [Page Splits Implementation](#page-splits-implementation)
6. [Page Merges Implementation](#page-merges-implementation)
7. [Free Space Management](#free-space-management)
8. [Checksum and Validation](#checksum-and-validation)

---

## Page Structure and Layout

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    ANATOMY OF A B-TREE PAGE                                  │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  A B-Tree node is stored as a single disk PAGE (typically 4KB-16KB)         │
│                                                                             │
│  PAGE STRUCTURE OVERVIEW                                                    │
│  ═══════════════════════                                                    │
│                                                                             │
│  ┌──────────────────────────────────────────────────────────────────┐       │
│  │                        PAGE HEADER                                │       │
│  │  (page type, LSN, checksum, free space info, item count)         │       │
│  ├──────────────────────────────────────────────────────────────────┤       │
│  │                                                                   │       │
│  │                     ITEM POINTERS / SLOTS                         │       │
│  │           (offsets to actual data within page)                    │       │
│  │                                                                   │       │
│  ├──────────────────────────────────────────────────────────────────┤       │
│  │                                                                   │       │
│  │                                                                   │       │
│  │                      FREE SPACE                                   │       │
│  │                  (grows toward each other)                        │       │
│  │                                                                   │       │
│  ├──────────────────────────────────────────────────────────────────┤       │
│  │                                                                   │       │
│  │                     ACTUAL DATA / TUPLES                          │       │
│  │               (keys, values, child pointers)                      │       │
│  │                                                                   │       │
│  └──────────────────────────────────────────────────────────────────┘       │
│                                                                             │
│  Low Address ───────────────────────────────────────────▶ High Address      │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Page Header Details

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    PAGE HEADER STRUCTURE                                     │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  TYPICAL HEADER FIELDS (varies by implementation)                           │
│  ═══════════════════════════════════════════════                            │
│                                                                             │
│  Byte Offset    Field               Size     Description                    │
│  ───────────    ─────               ────     ───────────                    │
│  0              page_id             4-8B     Unique page identifier         │
│  4/8            page_type           1B       Leaf/Internal/Root/Overflow    │
│  5/9            flags               1B       Is_leaf, has_overflow, etc.    │
│  6/10           item_count          2B       Number of items in page        │
│  8/12           free_space_start    2B       Offset where slots end         │
│  10/14          free_space_end      2B       Offset where data starts       │
│  12/16          page_lsn            8B       Log sequence number            │
│  20/24          checksum            4B       CRC32 or similar               │
│  24/28          right_sibling       4-8B     B-link tree: next page         │
│  28/36          high_key_offset     2B       B-link tree: high key          │
│  ...            ...                 ...      Additional metadata            │
│                                                                             │
│  TYPICAL HEADER SIZE: 24-64 bytes                                           │
│                                                                             │
│  EXAMPLE: PostgreSQL Page Header                                            │
│  ════════════════════════════════                                           │
│                                                                             │
│  ┌─────────────────────────────────────────────────┐                        │
│  │ pd_lsn          │ 8 bytes  │ WAL position       │                        │
│  │ pd_checksum     │ 2 bytes  │ Page checksum      │                        │
│  │ pd_flags        │ 2 bytes  │ Flag bits          │                        │
│  │ pd_lower        │ 2 bytes  │ Offset to start    │                        │
│  │ pd_upper        │ 2 bytes  │ Offset to end      │                        │
│  │ pd_special      │ 2 bytes  │ Special space      │                        │
│  │ pd_pagesize_ver │ 2 bytes  │ Size and version   │                        │
│  │ pd_prune_xid    │ 4 bytes  │ Oldest prunable XID│                        │
│  └─────────────────────────────────────────────────┘                        │
│  Total: 24 bytes                                                            │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Internal vs Leaf Page Layout

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    INTERNAL NODE PAGE LAYOUT                                 │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  Internal nodes store: keys + child page pointers                           │
│                                                                             │
│  STRUCTURE                                                                  │
│  ═════════                                                                  │
│                                                                             │
│  ┌────────────────────────────────────────────────────────────────┐         │
│  │ HEADER (24B)                                                    │         │
│  ├────────────────────────────────────────────────────────────────┤         │
│  │ Special: leftmost_child_ptr (8B)                               │         │
│  ├────────────────────────────────────────────────────────────────┤         │
│  │ Slot[0]: offset=100, len=20                                    │         │
│  │ Slot[1]: offset=120, len=22                                    │         │
│  │ Slot[2]: offset=142, len=18                                    │         │
│  │ ...                                                            │         │
│  ├────────────────────────────────────────────────────────────────┤         │
│  │                    FREE SPACE                                   │         │
│  ├────────────────────────────────────────────────────────────────┤         │
│  │ @142: [key₂ | child_ptr₂]                                      │         │
│  │ @120: [key₁ | child_ptr₁]                                      │         │
│  │ @100: [key₀ | child_ptr₀]                                      │         │
│  └────────────────────────────────────────────────────────────────┘         │
│                                                                             │
│  KEY ARRANGEMENT: K₀ < K₁ < K₂ ...                                          │
│  ROUTING: key < K₀ → leftmost_child                                         │
│           K₀ ≤ key < K₁ → child_ptr₀                                        │
│           K₁ ≤ key < K₂ → child_ptr₁                                        │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    LEAF NODE PAGE LAYOUT                                     │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  Leaf nodes store: keys + values (or row pointers)                          │
│                                                                             │
│  CLUSTERED INDEX (Primary Key)                                              │
│  ═════════════════════════════                                              │
│  ┌────────────────────────────────────────────────────────────────┐         │
│  │ HEADER                                                          │         │
│  ├────────────────────────────────────────────────────────────────┤         │
│  │ Slots: [0]→@500, [1]→@400, [2]→@300, ...                       │         │
│  ├────────────────────────────────────────────────────────────────┤         │
│  │                    FREE SPACE                                   │         │
│  ├────────────────────────────────────────────────────────────────┤         │
│  │ @300: [key₂ | col1 | col2 | col3 | ... | colN]  (full row)     │         │
│  │ @400: [key₁ | col1 | col2 | col3 | ... | colN]  (full row)     │         │
│  │ @500: [key₀ | col1 | col2 | col3 | ... | colN]  (full row)     │         │
│  └────────────────────────────────────────────────────────────────┘         │
│                                                                             │
│  NON-CLUSTERED / SECONDARY INDEX                                            │
│  ═══════════════════════════════                                            │
│  ┌────────────────────────────────────────────────────────────────┐         │
│  │ HEADER                                                          │         │
│  ├────────────────────────────────────────────────────────────────┤         │
│  │ Slots: [0]→@500, [1]→@480, [2]→@460, ...                       │         │
│  ├────────────────────────────────────────────────────────────────┤         │
│  │                    FREE SPACE                                   │         │
│  ├────────────────────────────────────────────────────────────────┤         │
│  │ @460: [idx_key₂ | primary_key / row_ptr]                       │         │
│  │ @480: [idx_key₁ | primary_key / row_ptr]                       │         │
│  │ @500: [idx_key₀ | primary_key / row_ptr]                       │         │
│  └────────────────────────────────────────────────────────────────┘         │
│                                                                             │
│  LEAF SIBLING POINTERS                                                      │
│  ═════════════════════                                                      │
│  For range scans, leaves are linked:                                        │
│                                                                             │
│  [Leaf 1] ←prev─────next→ [Leaf 2] ←prev─────next→ [Leaf 3]                 │
│                                                                             │
│  Some implementations: doubly-linked (PostgreSQL)                           │
│  Others: singly-linked right pointers (simpler)                             │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Slotted Page Organization

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    SLOTTED PAGE STRUCTURE                                    │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  WHY SLOTTED PAGES?                                                         │
│  ═══════════════════                                                        │
│                                                                             │
│  Problem: Variable-length records need flexible storage                     │
│                                                                             │
│  Fixed-offset approach:                                                     │
│  ┌──────┬──────┬──────┬──────┬──────┐                                       │
│  │Rec 0 │Rec 1 │Rec 2 │Rec 3 │ ...  │  (each at fixed offset)              │
│  └──────┴──────┴──────┴──────┴──────┘                                       │
│  ✗ Wastes space for variable-length data                                    │
│  ✗ Hard to handle different record sizes                                    │
│                                                                             │
│  Slotted page approach:                                                     │
│  ┌─────────────────────────────────────────────────────────────────┐        │
│  │ Header │ Slots →      │ ← Free →       │ ← Records (var size) │        │
│  └─────────────────────────────────────────────────────────────────┘        │
│  ✓ Efficient for variable-length records                                    │
│  ✓ Records can be any size                                                  │
│  ✓ Easy to add/remove/compact                                               │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Slot Array Details

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    SLOT ARRAY STRUCTURE                                      │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  Each SLOT contains:                                                        │
│  ┌────────────────────────────────┐                                         │
│  │ offset: 2 bytes │ length: 2B  │  = 4 bytes per slot                      │
│  └────────────────────────────────┘                                         │
│                                                                             │
│  Or sometimes:                                                              │
│  ┌────────────────────────────────────────────┐                             │
│  │ offset: 2B │ flags: 1B │ length: 2B       │  = 5 bytes                   │
│  └────────────────────────────────────────────┘                             │
│                                                                             │
│  DETAILED PAGE LAYOUT                                                       │
│  ════════════════════                                                       │
│                                                                             │
│  Byte: 0        24       28       32       36       ...    8000     8192    │
│        │        │        │        │        │        │      │        │       │
│        ▼        ▼        ▼        ▼        ▼        ▼      ▼        ▼       │
│  ┌─────────┬────────┬────────┬────────┬────────┬────────────┬───────────┐   │
│  │ HEADER  │ Slot 0 │ Slot 1 │ Slot 2 │ Slot 3 │   FREE     │ Records   │   │
│  │  24B    │(off,ln)│(off,ln)│(off,ln)│(off,ln)│   SPACE    │ (packed)  │   │
│  └─────────┴────────┴────────┴────────┴────────┴────────────┴───────────┘   │
│            │                                                  ▲             │
│            │ Slots grow this way ────────────────────────────┘              │
│            │                     Records grow this way ◀─────               │
│            ▼                                                                │
│     pd_lower (free space start)          pd_upper (free space end)          │
│                                                                             │
│  SLOT EXAMPLE                                                               │
│  ════════════                                                               │
│                                                                             │
│  Slot 0: {offset: 8100, length: 92}  → Record at byte 8100, 92 bytes        │
│  Slot 1: {offset: 8000, length: 100} → Record at byte 8000, 100 bytes       │
│  Slot 2: {offset: 7900, length: 100} → Record at byte 7900, 100 bytes       │
│                                                                             │
│  Free space = pd_upper - pd_lower                                           │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Record Insertion

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    INSERTING A RECORD                                        │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  BEFORE INSERT (3 records, 1 free slot worth of space)                      │
│  ═════════════════════════════════════════════════════                      │
│                                                                             │
│  ┌────────┬────┬────┬────┬─────────────────────┬───────────────────────┐    │
│  │ Header │ S0 │ S1 │ S2 │     FREE SPACE      │  Rec2 │ Rec1 │ Rec0  │    │
│  └────────┴────┴────┴────┴─────────────────────┴───────────────────────┘    │
│                     ▲ pd_lower     pd_upper ▲                               │
│                                                                             │
│  INSERT new 50-byte record                                                  │
│  ═════════════════════════                                                  │
│                                                                             │
│  1. Check: Is there enough free space? (need 50 + 4 = 54 bytes)             │
│     Free = pd_upper - pd_lower = OK!                                        │
│                                                                             │
│  2. Add slot entry at pd_lower:                                             │
│     Slot 3: {offset: pd_upper - 50, length: 50}                             │
│     pd_lower += 4                                                           │
│                                                                             │
│  3. Copy record data at pd_upper - 50:                                      │
│     Write record bytes                                                      │
│     pd_upper -= 50                                                          │
│                                                                             │
│  AFTER INSERT                                                               │
│  ════════════                                                               │
│                                                                             │
│  ┌────────┬────┬────┬────┬────┬────────────┬─────┬─────┬─────┬─────┐        │
│  │ Header │ S0 │ S1 │ S2 │ S3 │   FREE     │Rec3 │Rec2 │Rec1 │Rec0 │        │
│  └────────┴────┴────┴────┴────┴────────────┴─────┴─────┴─────┴─────┘        │
│                          ▲ pd_lower  pd_upper ▲                             │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Record Deletion and Compaction

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    DELETING A RECORD                                         │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  OPTION 1: Mark slot as dead (lazy deletion)                                │
│  ═══════════════════════════════════════════                                │
│                                                                             │
│  ┌────────┬────┬────┬────┬────┬────────────┬─────┬─────┬─────┬─────┐        │
│  │ Header │ S0 │DEAD│ S2 │ S3 │   FREE     │Rec3 │Rec2 │ XXX │Rec0 │        │
│  └────────┴────┴────┴────┴────┴────────────┴─────┴─────┴─────┴─────┘        │
│                 ▲ Slot 1 marked as deleted                                  │
│                   (Rec1 space not immediately reclaimed)                    │
│                                                                             │
│  Advantages: Fast deletion, slot can be reused                              │
│  Disadvantage: Fragmentation until compaction                               │
│                                                                             │
│  OPTION 2: Compact immediately                                              │
│  ═════════════════════════════                                              │
│                                                                             │
│  Move all records to close the gap:                                         │
│                                                                             │
│  ┌────────┬────┬────┬────┬─────────────────┬─────┬─────┬─────┐              │
│  │ Header │ S0 │ S2 │ S3 │     FREE        │Rec3 │Rec2 │Rec0 │              │
│  └────────┴────┴────┴────┴─────────────────┴─────┴─────┴─────┘              │
│                                                                             │
│  Advantage: No fragmentation                                                │
│  Disadvantage: Expensive (must move data and update slots)                  │
│                                                                             │
│  PAGE COMPACTION ALGORITHM                                                  │
│  ═════════════════════════                                                  │
│                                                                             │
│  1. Create temporary sorted list of all live records                        │
│  2. Starting from page end, rewrite records contiguously                    │
│  3. Update all slot offsets to point to new locations                       │
│  4. Update pd_upper to reflect new free space                               │
│                                                                             │
│  Triggered when:                                                            │
│  • Free space fragmented beyond threshold                                   │
│  • Insert fails despite sufficient total free space                         │
│  • Background vacuum/cleanup process                                        │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Variable-Length Data

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    HANDLING VARIABLE-LENGTH FIELDS                           │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  RECORD FORMAT FOR VARIABLE-LENGTH COLUMNS                                  │
│  ═════════════════════════════════════════                                  │
│                                                                             │
│  Option 1: LENGTH-PREFIXED                                                  │
│  ┌────────────────────────────────────────────────────────────┐             │
│  │ len1 │ data1 ... │ len2 │ data2 ... │ len3 │ data3 ...    │             │
│  └────────────────────────────────────────────────────────────┘             │
│                                                                             │
│  Example: VARCHAR columns                                                   │
│  ┌───┬─────────┬───┬───────────────┬───┬─────┐                              │
│  │ 5 │ "hello" │ 3 │ "bye"         │ 0 │ ""  │                              │
│  └───┴─────────┴───┴───────────────┴───┴─────┘                              │
│                                                                             │
│  Option 2: OFFSET ARRAY (like slotted page within record)                   │
│  ┌─────────────────────────────────────────────────────────────┐            │
│  │ offset_array │ fixed_cols │ var_col1 │ var_col2 │ var_col3 │            │
│  └─────────────────────────────────────────────────────────────┘            │
│                                                                             │
│  ┌───────────────────────────────────────────────────────────────────┐      │
│  │ offsets: [20,25,28] │ id=42 │ age=30 │ "hello" │ "bye" │ ""      │      │
│  └───────────────────────────────────────────────────────────────────┘      │
│    Fixed part first, variable part after, offsets at beginning              │
│                                                                             │
│  NULL HANDLING                                                              │
│  ═════════════                                                              │
│                                                                             │
│  Common approach: NULL BITMAP                                               │
│  ┌─────────────────────────────────────────────────────────────────┐        │
│  │ null_bitmap │ fixed_cols │ var_cols ...                         │        │
│  └─────────────────────────────────────────────────────────────────┘        │
│                                                                             │
│  Example: 8 columns, cols 2 and 5 are NULL                                  │
│  null_bitmap: 0b00100100 = columns 2,5 are NULL                             │
│  NULL columns take NO space in data portion!                                │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Overflow Pages

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    HANDLING LARGE VALUES                                     │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  PROBLEM: What if a value exceeds page size?                                │
│                                                                             │
│  8 KB page, 4 KB BLOB = won't fit with other records!                       │
│                                                                             │
│  SOLUTION: OVERFLOW PAGES (TOAST in PostgreSQL, Off-page in InnoDB)         │
│  ═══════════════════════════════════════════════════════════════            │
│                                                                             │
│  Main Page                          Overflow Page(s)                        │
│  ┌──────────────────────────┐      ┌──────────────────────────┐             │
│  │ Record:                  │      │ OVERFLOW HEADER          │             │
│  │  col1: 42                │      │  page_type: OVERFLOW     │             │
│  │  col2: "short"           │      │  total_size: 50000       │             │
│  │  col3: OVERFLOW_PTR ─────┼──────▶  chunk_num: 1/5          │             │
│  │        {page: 1234,      │      │  next_page: 1235         │             │
│  │         size: 50000}     │      ├──────────────────────────┤             │
│  │  col4: 3.14              │      │                          │             │
│  └──────────────────────────┘      │  [10KB of BLOB data]     │             │
│                                    │                          │             │
│                                    └──────────────────────────┘             │
│                                              │                              │
│                                              ▼                              │
│                                    ┌──────────────────────────┐             │
│                                    │ OVERFLOW chunk 2/5       │             │
│                                    │  next_page: 1236         │             │
│                                    │  [10KB of BLOB data]     │             │
│                                    └──────────────────────────┘             │
│                                              │                              │
│                                              ▼ (and so on...)               │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### PostgreSQL TOAST

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    POSTGRESQL TOAST (The Oversized-Attribute Storage)        │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  TOAST STRATEGIES                                                           │
│  ════════════════                                                           │
│                                                                             │
│  1. PLAIN: No compression, no out-of-line storage                           │
│     • Used for small fixed-length types                                     │
│                                                                             │
│  2. EXTENDED: Compression AND out-of-line storage allowed                   │
│     • Default for TEXT, BYTEA, etc.                                         │
│     • First tries compression                                               │
│     • If still too big, moves to TOAST table                                │
│                                                                             │
│  3. EXTERNAL: Out-of-line storage, no compression                           │
│     • Good for pre-compressed data (JPEG, etc.)                             │
│                                                                             │
│  4. MAIN: Try compression first, avoid out-of-line if possible              │
│     • Will only TOAST as last resort                                        │
│                                                                             │
│  TOAST THRESHOLD                                                            │
│  ═══════════════                                                            │
│                                                                             │
│  Default: ~2KB (TOAST_TUPLE_THRESHOLD)                                      │
│  If tuple > 2KB, PostgreSQL will attempt to:                                │
│  1. Compress large columns (if EXTENDED/MAIN)                               │
│  2. Move columns to TOAST table (if EXTENDED/EXTERNAL)                      │
│                                                                             │
│  TOAST TABLE STRUCTURE                                                      │
│  ═════════════════════                                                      │
│                                                                             │
│  ┌────────────────────────────────────────────────────────────────┐         │
│  │ Main Table: users                                               │         │
│  │ ┌─────┬─────────┬─────────────┐                                 │         │
│  │ │ id  │ name    │ bio (TEXT)  │                                 │         │
│  │ │ 1   │ "Alice" │ TOAST_PTR   │ ──────────┐                     │         │
│  │ │ 2   │ "Bob"   │ "short bio" │           │                     │         │
│  │ └─────┴─────────┴─────────────┘           │                     │         │
│  │                                           ▼                     │         │
│  │ TOAST Table: pg_toast.pg_toast_12345                            │         │
│  │ ┌────────┬───────────┬────────────────────┐                     │         │
│  │ │chunk_id│ chunk_seq │ chunk_data         │                     │         │
│  │ │ 1001   │ 0         │ [first 2KB chunk]  │                     │         │
│  │ │ 1001   │ 1         │ [second 2KB chunk] │                     │         │
│  │ │ 1001   │ 2         │ [third 2KB chunk]  │                     │         │
│  │ └────────┴───────────┴────────────────────┘                     │         │
│  └────────────────────────────────────────────────────────────────┘         │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Page Splits

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    B-TREE PAGE SPLIT OPERATION                              │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  WHEN DOES A SPLIT OCCUR?                                                   │
│  ════════════════════════                                                   │
│                                                                             │
│  A page split is triggered when:                                            │
│  • Insert requires more space than available                                │
│  • After compaction, still insufficient space                               │
│  • Node exceeds maximum key count                                           │
│                                                                             │
│  LEAF NODE SPLIT ALGORITHM                                                  │
│  ════════════════════════════                                               │
│                                                                             │
│  BEFORE: Full leaf node, inserting key "35"                                 │
│                                                                             │
│  ┌────────────────────────────────────────────────────────────────┐         │
│  │ Leaf Node (FULL)                                               │         │
│  │ [10, 20, 30, 40, 50, 60, 70, 80]                               │         │
│  └────────────────────────────────────────────────────────────────┘         │
│                                                                             │
│  STEP 1: Allocate new page                                                  │
│  ════════════════════════════                                               │
│                                                                             │
│  ┌─────────────────────────────────┐  ┌─────────────────────────────────┐   │
│  │ Old Page                        │  │ New Page (empty)                │   │
│  │ [10, 20, 30, 40, 50, 60, 70, 80]│  │ []                              │   │
│  └─────────────────────────────────┘  └─────────────────────────────────┘   │
│                                                                             │
│  STEP 2: Find split point (typically middle)                                │
│  ════════════════════════════════════════════                               │
│                                                                             │
│  Keys: [10, 20, 30, 35(new), 40, 50, 60, 70, 80]                            │
│                          ↑                                                  │
│                    Split point = 40                                         │
│                                                                             │
│  STEP 3: Redistribute keys                                                  │
│  ═════════════════════════                                                  │
│                                                                             │
│  ┌─────────────────────────────────┐  ┌─────────────────────────────────┐   │
│  │ Old Page (Left)                 │  │ New Page (Right)                │   │
│  │ [10, 20, 30, 35]                │  │ [40, 50, 60, 70, 80]            │   │
│  └─────────────────────────────────┘  └─────────────────────────────────┘   │
│                                                                             │
│  STEP 4: Update sibling pointers                                            │
│  ═══════════════════════════════                                            │
│                                                                             │
│  [Left] ←prev─ [Old/Left] ─next→ [New/Right] ─next→ [Original Right]        │
│                                                                             │
│  STEP 5: Propagate separator to parent                                      │
│  ═════════════════════════════════════                                      │
│                                                                             │
│  Push separator key "40" UP to parent (may cause parent split!)             │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Internal Node Split

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    INTERNAL NODE SPLIT                                      │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  Internal splits differ: middle key moves UP (not copied)                   │
│                                                                             │
│  BEFORE: Full internal node, need to add separator "45"                     │
│                                                                             │
│       ┌───────────────────────────────────────────────────────────────┐     │
│       │ [20│ptr] [40│ptr] [60│ptr] [80│ptr] [leftmost_ptr]            │     │
│       └───────────────────────────────────────────────────────────────┘     │
│           ↓        ↓        ↓        ↓           ↓                          │
│         ...      ...      ...      ...         ...                          │
│                                                                             │
│  AFTER SPLIT:                                                               │
│                                                                             │
│                     ┌─────────┐                                             │
│                     │   [60]  │  ← "60" pushed to parent                    │
│                     └────┬────┘                                             │
│                ┌─────────┴─────────┐                                        │
│                ↓                   ↓                                        │
│  ┌─────────────────────────┐   ┌─────────────────────────┐                  │
│  │ [20│ptr] [40│ptr] [45│] │   │ [80│ptr] [leftmost_ptr] │                  │
│  │ [leftmost_ptr]          │   │                         │                  │
│  └─────────────────────────┘   └─────────────────────────┘                  │
│       Left child                    Right child                             │
│                                                                             │
│  KEY DIFFERENCE FROM LEAF SPLIT                                             │
│  ═══════════════════════════════                                            │
│                                                                             │
│  • Leaf: Separator is COPIED up (exists in both parent and right leaf)     │
│  • Internal: Separator MOVES up (only exists in parent after split)        │
│                                                                             │
│  CASCADING SPLITS                                                           │
│  ════════════════                                                           │
│                                                                             │
│       Root: [K₁] ← might split!                                             │
│              ↓                                                              │
│       [K₂, K₃, K₄] ← might split!                                           │
│              ↓                                                              │
│       [K₅, K₆, K₇, K₈] ← Split here propagates up!                          │
│                                                                             │
│  Worst case: Split cascades all the way to root                             │
│  → Root splits → Tree height increases by 1                                 │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Split Strategies

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    SPLIT POINT STRATEGIES                                   │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  1. MIDDLE SPLIT (Standard)                                                 │
│  ══════════════════════════                                                 │
│                                                                             │
│  Split at 50% point:                                                        │
│  [1,2,3,4,5,6,7,8] → [1,2,3,4] | [5,6,7,8]                                  │
│                                                                             │
│  Pros: Balanced tree, good for random workloads                             │
│  Cons: Only 50% fill after split                                            │
│                                                                             │
│  2. SUFFIX TRUNCATION SPLIT                                                 │
│  ══════════════════════════                                                 │
│                                                                             │
│  Choose split point that minimizes separator key size:                      │
│                                                                             │
│  Keys: ["application", "apple", "apricot", "banana", "berry"]               │
│  Best split: between "apricot" and "banana"                                 │
│  Separator: "b" (single byte!) instead of full "banana"                     │
│                                                                             │
│  3. SEQUENTIAL INSERT OPTIMIZATION                                          │
│  ═════════════════════════════════                                          │
│                                                                             │
│  For monotonically increasing keys (auto-increment IDs):                    │
│                                                                             │
│  Standard split:                                                            │
│  [1,2,3,4,5] + insert 6 → [1,2,3] | [4,5,6]  (both 50%)                     │
│                                                                             │
│  Optimized (90-10 split):                                                   │
│  [1,2,3,4,5] + insert 6 → [1,2,3,4,5] | [6]  (left 90%, right 10%)          │
│                                                                             │
│  PostgreSQL uses this for indexes on serial columns                         │
│                                                                             │
│  4. BULK LOADING OPTIMIZATION                                               │
│  ═══════════════════════════                                                │
│                                                                             │
│  When loading sorted data:                                                  │
│  • Fill pages to 100% (or configurable fillfactor)                          │
│  • No splits during load!                                                   │
│  • Build bottom-up (leaves first, then internal nodes)                      │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Page Merges

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    B-TREE PAGE MERGE OPERATION                              │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  WHEN DOES A MERGE OCCUR?                                                   │
│  ═════════════════════════                                                  │
│                                                                             │
│  A merge is considered when:                                                │
│  • Node falls below minimum fill (typically 50%)                            │
│  • After deletion, node is "underfull"                                      │
│  • Sibling can accommodate all keys                                         │
│                                                                             │
│  MERGE ALGORITHM                                                            │
│  ═══════════════                                                            │
│                                                                             │
│  BEFORE: Two underfull siblings                                             │
│                                                                             │
│       Parent: [..., 40, ...]                                                │
│                    ↓                                                        │
│       ┌────────────┴────────────┐                                           │
│       ↓                         ↓                                           │
│  ┌─────────────┐         ┌─────────────┐                                    │
│  │ [10, 20]    │  ←───→  │ [50, 60]    │                                    │
│  └─────────────┘         └─────────────┘                                    │
│   Left sibling           Right sibling                                      │
│                                                                             │
│  STEP 1: Pull down separator from parent                                    │
│  ═══════════════════════════════════════                                    │
│                                                                             │
│  Parent's "40" comes down to join the merged node                           │
│                                                                             │
│  STEP 2: Combine all keys                                                   │
│  ════════════════════════                                                   │
│                                                                             │
│  ┌───────────────────────────────┐                                          │
│  │ [10, 20, 40, 50, 60]          │  ← merged node                           │
│  └───────────────────────────────┘                                          │
│                                                                             │
│  STEP 3: Update parent (remove separator)                                   │
│  ═════════════════════════════════════════                                  │
│                                                                             │
│  Parent: [..., ...] (40 removed, pointer to right sibling removed)          │
│                                                                             │
│  STEP 4: Free the empty page                                                │
│  ═══════════════════════════                                                │
│                                                                             │
│  Add empty page to free list for reuse                                      │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Redistribution (Alternative to Merge)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    REDISTRIBUTION INSTEAD OF MERGE                          │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  Sometimes merging isn't possible (sibling is too full)                     │
│  → Redistribute keys between siblings instead!                              │
│                                                                             │
│  BEFORE: Left underfull, Right has space but can't absorb all               │
│                                                                             │
│       Parent: [..., 40, ...]                                                │
│                    ↓                                                        │
│       ┌────────────┴────────────┐                                           │
│       ↓                         ↓                                           │
│  ┌─────────────┐         ┌─────────────────────────┐                        │
│  │ [10]        │  ←───→  │ [50, 55, 60, 65, 70]    │                        │
│  └─────────────┘         └─────────────────────────┘                        │
│   1 key (underfull)       5 keys (can't absorb 1 more)                      │
│                                                                             │
│  REDISTRIBUTION:                                                            │
│                                                                             │
│       Parent: [..., 55, ...]  ← separator updated!                          │
│                    ↓                                                        │
│       ┌────────────┴────────────┐                                           │
│       ↓                         ↓                                           │
│  ┌─────────────────────┐   ┌─────────────────────┐                          │
│  │ [10, 40, 50]        │   │ [60, 65, 70]        │                          │
│  └─────────────────────┘   └─────────────────────┘                          │
│   3 keys (balanced)         3 keys (balanced)                               │
│                                                                             │
│  ALGORITHM:                                                                 │
│  1. Calculate total keys in both siblings + separator                       │
│  2. Find new split point (balanced distribution)                            │
│  3. Move keys from full sibling to underfull sibling                        │
│  4. Update parent separator to new boundary key                             │
│                                                                             │
│  ADVANTAGE: Avoids merge + potential cascading merges                       │
│  DISADVANTAGE: More complex, requires more modifications                    │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Free Space Management

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    FREE PAGE MANAGEMENT                                     │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  When pages are freed (after merge), we need to track them for reuse        │
│                                                                             │
│  OPTION 1: FREE PAGE LIST                                                   │
│  ═════════════════════════                                                  │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │ File Header (page 0)                                                │    │
│  │  first_free_page: 42                                                │    │
│  │  num_free_pages: 15                                                 │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                  │                                                          │
│                  ↓                                                          │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │ Free Page 42                                                        │    │
│  │  next_free: 87                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                  │                                                          │
│                  ↓                                                          │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │ Free Page 87                                                        │    │
│  │  next_free: 123                                                     │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                  │                                                          │
│                  ↓ ... and so on                                            │
│                                                                             │
│  OPTION 2: BITMAP (Free Space Map)                                          │
│  ══════════════════════════════════                                         │
│                                                                             │
│  PostgreSQL uses FSM (Free Space Map) files:                                │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │ FSM Page                                                            │    │
│  │ ┌───┬───┬───┬───┬───┬───┬───┬───┬───┬───┬───┬───┬───┬───┬───┬───┐  │    │
│  │ │ 0 │ 2 │ 0 │ 5 │ 0 │ 0 │ 3 │ 0 │ 1 │ 0 │ 0 │ 4 │ 0 │ 0 │ 0 │ 2 │  │    │
│  │ └───┴───┴───┴───┴───┴───┴───┴───┴───┴───┴───┴───┴───┴───┴───┴───┘  │    │
│  │ Each value = free space category (0-255 → space ranges)            │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                             │
│  Organized as a tree for fast lookup:                                       │
│                                                                             │
│         [max of children]                                                   │
│              /    \                                                         │
│       [max]        [max]                                                    │
│       /   \        /   \                                                    │
│      [5] [3]      [4] [2]  ← leaf entries point to heap pages               │
│                                                                             │
│  ALLOCATION STRATEGY                                                        │
│  ═══════════════════                                                        │
│                                                                             │
│  1. Check free list/FSM for reusable page                                   │
│  2. If found → reuse (update free list)                                     │
│  3. If not → extend file (append new page at end)                           │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Checksum and Validation

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    PAGE CHECKSUMS AND VALIDATION                            │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  WHY CHECKSUMS?                                                             │
│  ═══════════════                                                            │
│                                                                             │
│  • Detect silent data corruption (bit rot, disk errors)                     │
│  • Catch bugs in storage layer                                              │
│  • Verify data integrity during replication                                 │
│                                                                             │
│  PAGE HEADER WITH CHECKSUM                                                  │
│  ═════════════════════════                                                  │
│                                                                             │
│  ┌───────────────────────────────────────────────────────────────────┐      │
│  │ page_id       │ 8 bytes │ Identifies the page                    │      │
│  │ checksum      │ 4 bytes │ CRC32 or xxHash of page contents       │      │
│  │ page_lsn      │ 8 bytes │ Last WAL position that modified page   │      │
│  │ flags         │ 2 bytes │ Page type, hints                       │      │
│  │ version       │ 2 bytes │ Page format version                    │      │
│  │ ...           │         │                                        │      │
│  └───────────────────────────────────────────────────────────────────┘      │
│                                                                             │
│  CHECKSUM ALGORITHMS                                                        │
│  ═══════════════════                                                        │
│                                                                             │
│  CRC32                                                                      │
│  ├── Widely used, hardware acceleration (SSE4.2)                            │
│  ├── Good error detection for short corruptions                             │
│  └── PostgreSQL default (when enabled)                                      │
│                                                                             │
│  xxHash                                                                     │
│  ├── Extremely fast                                                         │
│  ├── Good distribution                                                      │
│  └── Used by some modern systems                                            │
│                                                                             │
│  WHEN CHECKSUMS ARE VERIFIED                                                │
│  ═══════════════════════════                                                │
│                                                                             │
│  1. Page read from disk → verify checksum                                   │
│  2. Page written to disk → compute & store checksum                         │
│  3. Replication → verify on standby                                         │
│  4. Backup verification                                                     │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                      CHECKSUM VERIFICATION FLOW                     │    │
│  │                                                                     │    │
│  │   READ PAGE                    WRITE PAGE                          │    │
│  │   ══════════                   ════════════                        │    │
│  │   1. Read page from disk       1. Modify page in memory            │    │
│  │   2. Compute checksum          2. Compute checksum                 │    │
│  │   3. Compare with stored       3. Store in page header             │    │
│  │   4. If mismatch → ERROR!      4. Write to disk                    │    │
│  │      "checksum failure"                                            │    │
│  │                                                                     │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                             │
│  ADDITIONAL VALIDATIONS                                                     │
│  ═══════════════════════                                                    │
│                                                                             │
│  • Page ID matches expected (not reading wrong page)                        │
│  • Page version is compatible                                               │
│  • LSN is reasonable (not in the future)                                    │
│  • Key ordering invariant (keys are sorted)                                 │
│  • Slot array doesn't overflow into record area                             │
│  • All record offsets within page bounds                                    │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Summary

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    B-TREE IMPLEMENTATION - KEY TAKEAWAYS                    │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  PAGE STRUCTURE                                                             │
│  ══════════════                                                             │
│  • Fixed-size pages (4KB-16KB typical)                                      │
│  • Header contains metadata (page ID, LSN, checksums)                       │
│  • Slotted page design for variable-length records                          │
│  • Slots grow forward, records grow backward                                │
│                                                                             │
│  NODE TYPES                                                                 │
│  ══════════════                                                             │
│  • Internal nodes: keys + child pointers (routing)                          │
│  • Leaf nodes: keys + values/row-pointers (data)                            │
│  • Sibling pointers in leaves for range scans                               │
│                                                                             │
│  VARIABLE-LENGTH DATA                                                       │
│  ══════════════════════                                                     │
│  • Length-prefixed fields                                                   │
│  • Offset arrays for random access                                          │
│  • NULL bitmaps save space                                                  │
│  • Overflow pages for large values (TOAST)                                  │
│                                                                             │
│  PAGE SPLITS                                                                │
│  ═══════════                                                                │
│  • Triggered when page is full                                              │
│  • Leaf: separator copied up                                                │
│  • Internal: separator moves up                                             │
│  • May cascade to root → tree grows taller                                  │
│                                                                             │
│  PAGE MERGES                                                                │
│  ═══════════                                                                │
│  • Triggered when page underfull                                            │
│  • Pull separator down from parent                                          │
│  • Combine with sibling                                                     │
│  • Alternative: redistribute keys                                           │
│                                                                             │
│  FREE SPACE MANAGEMENT                                                      │
│  ══════════════════════                                                     │
│  • Free list or bitmap (FSM)                                                │
│  • Reuse freed pages before extending file                                  │
│  • Compaction reclaims fragmented space                                     │
│                                                                             │
│  DATA INTEGRITY                                                             │
│  ═══════════════                                                            │
│  • Checksums detect corruption                                              │
│  • LSN tracks modifications                                                 │
│  • Invariant checks catch bugs                                              │
│                                                                             │
│  ┌───────────────────────────────────────────────────────────────────┐      │
│  │ PERFORMANCE CONSIDERATIONS                                        │      │
│  │                                                                   │      │
│  │ • Larger pages → fewer splits, better sequential I/O              │      │
│  │ • Smaller pages → less wasted space, better cache                 │      │
│  │ • Fill factor trade-off: full pages vs split frequency            │      │
│  │ • Prefix compression reduces I/O and memory usage                 │      │
│  │ • Bulk loading: build bottom-up for optimal layout                │      │
│  └───────────────────────────────────────────────────────────────────┘      │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

