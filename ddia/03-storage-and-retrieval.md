# Chapter 3: Storage and Retrieval

## Table of Contents

1. [The Simplest Database](#the-simplest-database)
2. [Hash Indexes](#hash-indexes)
3. [SSTables and LSM-Trees](#sstables-and-lsm-trees)
4. [B-Trees](#b-trees)
5. [B-Trees vs LSM-Trees](#b-trees-vs-lsm-trees)
6. [Other Indexing Structures](#other-indexing-structures)
7. [Transaction Processing vs Analytics (OLTP vs OLAP)](#transaction-processing-vs-analytics-oltp-vs-olap)
8. [Column-Oriented Storage](#column-oriented-storage)
9. [Interview Questions](#interview-questions)

---

## The Simplest Database

The world's simplest database — two Bash functions:

```bash
#!/bin/bash
db_set() {
    echo "$1,$2" >> database        # Append to end of file
}

db_get() {
    grep "^$1," database | sed -e "s/^$1,//" | tail -n 1   # Scan for last occurrence
}
```

- **Writes are O(1)**: Appending to a file is very fast
- **Reads are O(n)**: Must scan entire file to find the latest value for a key
- **Key insight**: An **index** is an additional data structure that speeds up reads at the cost of slower writes

```
┌─────────────────────────────────────────────────────────────────┐
│              THE FUNDAMENTAL TRADE-OFF OF INDEXES               │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│         No Index              With Index                        │
│         ────────              ──────────                        │
│  Write: O(1) append          O(1) append + O(log n) index update│
│  Read:  O(n) scan            O(log n) or O(1) lookup           │
│                                                                 │
│  Well-chosen indexes speed up reads enormously.                 │
│  Every index slows down writes.                                 │
│  Database doesn't index everything by default —                 │
│  the developer must choose indexes manually.                    │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## Hash Indexes

The simplest indexing strategy: keep an in-memory **hash map** of key → byte offset.

```
┌─────────────────────────────────────────────────────────────────┐
│              HASH INDEX (e.g., Bitcask in Riak)                 │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  In-Memory Hash Map:             On-Disk Log File:              │
│  ┌──────────────────┐           ┌──────────────────────────┐   │
│  │ key123 → offset 0│──────────►│ key123,{"name":"Alice"}  │   │
│  │ key456 → offset 64│─────────►│ key456,{"name":"Bob"}    │   │
│  │ key789 → offset 128│────────►│ key789,{"name":"Carol"}  │   │
│  │ key123 → offset 192│───────►│ key123,{"name":"Updated"}│   │
│  └──────────────────┘           └──────────────────────────┘   │
│                                                                 │
│  • Hash map always points to LATEST value for each key          │
│  • Reads: Look up key in hash map → seek to byte offset → read │
│  • Writes: Append to log → update hash map entry                │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Compaction and Segment Merging

The log file grows forever — solved by **compaction** (removing duplicate keys, keeping only the latest):

```
┌─────────────────────────────────────────────────────────────────┐
│              COMPACTION & SEGMENT MERGING                        │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Segment 1 (old):          Segment 2 (newer):                   │
│  ┌─────────────────┐      ┌─────────────────┐                  │
│  │ a=1, b=2, a=3,  │      │ b=7, c=3, c=9   │                  │
│  │ c=4, a=5        │      │                   │                  │
│  └─────────────────┘      └─────────────────┘                  │
│          │                         │                            │
│          └────────┬────────────────┘                            │
│                   ▼                                             │
│  Merged & Compacted Segment:                                    │
│  ┌─────────────────┐                                           │
│  │ a=5, b=7, c=9   │  ← Only latest value per key             │
│  └─────────────────┘                                           │
│                                                                 │
│  Merging happens in background. Old segments are deleted        │
│  after the merged segment is written.                           │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Practical Considerations

| Concern | Solution |
|---------|----------|
| **File format** | Binary format (length-prefixed strings) faster than CSV |
| **Deleting records** | Append a **tombstone** marker; merging discards tombstoned keys |
| **Crash recovery** | Rebuild hash map by scanning segments (slow); or keep hash map snapshots on disk |
| **Partially written records** | Use checksums to detect and ignore corrupted records |
| **Concurrency** | Single writer thread; reads can be concurrent (immutable segments) |

### Limitations of Hash Indexes

- **Must fit in memory**: Entire hash map must be in RAM
- **Range queries inefficient**: Can't scan all keys between `kitty00000` and `kitty99999`

---

## SSTables and LSM-Trees

### SSTable (Sorted String Table)

An improvement over hash-indexed segments: **keys are sorted** within each segment.

```
┌─────────────────────────────────────────────────────────────────┐
│              SSTABLE vs HASH-INDEXED SEGMENT                    │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Hash-Indexed Segment:                                          │
│  ┌────────────────────────────────────────┐                    │
│  │ zebra=9, apple=3, mango=5, banana=2   │  Keys in write     │
│  └────────────────────────────────────────┘  order (random)    │
│                                                                 │
│  SSTable (Sorted String Table):                                 │
│  ┌────────────────────────────────────────┐                    │
│  │ apple=3, banana=2, mango=5, zebra=9   │  Keys sorted!      │
│  └────────────────────────────────────────┘                    │
│                                                                 │
│  Advantages of sorting:                                         │
│  1. Merging is efficient (merge sort — O(n))                   │
│  2. Sparse index: don't need every key in memory               │
│  3. Range queries are possible (scan from start to end)        │
│  4. Blocks can be compressed (keys in same block share prefix) │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Sparse Index for SSTables

```
┌─────────────────────────────────────────────────────────────────┐
│              SPARSE IN-MEMORY INDEX                              │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  In-Memory Index (sparse):        SSTable on disk:              │
│  ┌───────────────────┐           ┌──────────────────────┐      │
│  │ apple   → 0       │──────────►│ apple=3              │      │
│  │                    │           │ apricot=7            │      │
│  │                    │           │ avocado=1            │      │
│  │ banana  → 48      │──────────►│ banana=2             │      │
│  │                    │           │ blueberry=8          │      │
│  │                    │           │ cantaloupe=4         │      │
│  │ durian  → 112     │──────────►│ durian=6             │      │
│  └───────────────────┘           └──────────────────────┘      │
│                                                                 │
│  To find "cherry":                                              │
│  1. Not in sparse index                                         │
│  2. Must be between "banana" (offset 48) and "durian" (112)    │
│  3. Scan from offset 48 to 112 — much smaller than full scan   │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Constructing SSTables from a Memtable (LSM-Tree)

You can't sort writes as they arrive (random order). Solution: use an **in-memory balanced tree** (red-black tree or AVL tree) called a **memtable**:

```
┌─────────────────────────────────────────────────────────────────┐
│              LSM-TREE WRITE PATH                                │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  1. Write arrives                                               │
│     ▼                                                           │
│  2. Add to MEMTABLE (in-memory balanced tree)                   │
│     ┌──────────────┐                                           │
│     │   Red-Black  │  Keeps keys sorted in memory              │
│     │     Tree     │                                           │
│     └──────┬───────┘                                           │
│            │  When memtable exceeds threshold (e.g., few MB)   │
│            ▼                                                    │
│  3. Flush to disk as new SSTable SEGMENT                        │
│     ┌────────────────────────────────────────────┐             │
│     │ SSTable: sorted key-value pairs on disk    │             │
│     └────────────────────────────────────────────┘             │
│            │                                                    │
│            ▼                                                    │
│  4. Background COMPACTION merges SSTables                       │
│     ┌──────────┐ ┌──────────┐    ┌──────────────────┐         │
│     │ Level 0  │+│ Level 0  │ ──►│ Level 1 (merged) │         │
│     └──────────┘ └──────────┘    └──────────────────┘         │
│                                                                 │
│  READ PATH:                                                     │
│  1. Check memtable first                                        │
│  2. Then most recent SSTable on disk                            │
│  3. Then next-oldest SSTable                                    │
│  4. ... and so on                                               │
│                                                                 │
│  WAL (Write-Ahead Log):                                         │
│  Every write also appended to WAL for crash recovery.           │
│  If process crashes, memtable is lost but WAL can rebuild it.   │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### LSM-Tree Compaction Strategies

```
┌─────────────────────────────────────────────────────────────────┐
│              SIZE-TIERED vs LEVELED COMPACTION                   │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  SIZE-TIERED (HBase, Cassandra default):                        │
│  ─────────────────────────────────────                          │
│  • Newer, smaller SSTables merged into older, larger ones       │
│  • Each tier has SSTables of similar size                        │
│  • Simpler, better write throughput                              │
│  • More space amplification (temporarily stores duplicates)     │
│                                                                 │
│  LEVELED (LevelDB, RocksDB, Cassandra LCS):                    │
│  ──────────────────────────────────────────                     │
│  • Key range split into smaller SSTables                        │
│  • Each level has non-overlapping key ranges                    │
│  • Level N is ~10x the size of Level N-1                        │
│  • Better read performance, less space amplification            │
│  • More write amplification (rewrites data more often)          │
│                                                                 │
│  Level 0:  ┌──┐ ┌──┐ ┌──┐  (may overlap)                      │
│  Level 1:  ┌───────┐ ┌───────┐  (non-overlapping)              │
│  Level 2:  ┌────┐┌────┐┌────┐┌────┐  (non-overlapping, 10x)   │
│  Level 3:  (even more SSTables, 10x larger total)               │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Bloom Filters — Optimizing Non-Existent Key Lookups

A key that doesn't exist forces checking every SSTable level. **Bloom filters** short-circuit this:

```
┌─────────────────────────────────────────────────────────────────┐
│              BLOOM FILTER                                        │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  A memory-efficient probabilistic data structure:               │
│  • "Definitely NOT in the set" — 100% certain (no false neg)   │
│  • "Probably in the set" — might be wrong (false positive OK)  │
│                                                                 │
│  Used by LSM-tree to skip SSTables that definitely don't        │
│  contain the requested key. Saves many unnecessary disk reads.  │
│                                                                 │
│  Bit array: [0, 1, 0, 1, 1, 0, 0, 1, 0, 1, 0, 0, 1, 0, 1]   │
│              ▲        ▲  ▲           ▲        ▲     ▲          │
│              └────────┴──┴───────────┴────────┴─────┘          │
│              Hash functions set these bits for each key         │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## B-Trees

The most widely used index structure. Used by virtually every relational database.

```
┌─────────────────────────────────────────────────────────────────┐
│              B-TREE STRUCTURE                                    │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│                        ┌───────────────────┐                   │
│                        │  100  |  200  | 300│  ROOT PAGE       │
│                        └──┬───────┬───────┬─┘                  │
│                   ┌───────┘       │       └───────┐            │
│                   ▼               ▼               ▼            │
│          ┌──────────────┐ ┌──────────────┐ ┌──────────────┐   │
│          │ 10 | 30 | 70 │ │120|150|180   │ │210|250|280   │   │
│          └─┬──┬───┬──┬──┘ └──────────────┘ └──────────────┘   │
│            │  │   │  │     INTERNAL PAGES   INTERNAL PAGES     │
│            ▼  ▼   ▼  ▼                                         │
│          ┌──┐┌──┐┌──┐┌──┐                                     │
│          │  ││  ││  ││  │  LEAF PAGES contain actual values    │
│          └──┘└──┘└──┘└──┘  (or pointers to rows)               │
│                                                                 │
│  Each page = fixed-size block (typically 4KB)                   │
│  Branching factor = ~500 (number of children per node)          │
│  4 levels deep → 500^4 = 62.5 billion keys!                    │
│                                                                 │
│  LOOKUP: Start at root, binary search within page,              │
│          follow child pointer, repeat until leaf. O(log n)      │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### B-Tree Updates

```
┌─────────────────────────────────────────────────────────────────┐
│              B-TREE WRITE PATH                                   │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  UPDATE existing key:                                           │
│  1. Search for leaf page containing the key                     │
│  2. Overwrite the value IN PLACE on that page                   │
│  3. Write the page back to disk                                 │
│                                                                 │
│  INSERT new key (page has space):                               │
│  1. Find the leaf page where key belongs                        │
│  2. Add key-value to that page                                  │
│  3. Write page back to disk                                     │
│                                                                 │
│  INSERT new key (page is FULL → SPLIT):                         │
│  ┌────────────────────────┐                                    │
│  │  10 | 20 | 30 | 40 |50│  FULL! Can't add 25               │
│  └────────────────────────┘                                    │
│              │                                                  │
│              ▼  Split into two pages                            │
│  ┌──────────────┐  ┌──────────────┐                            │
│  │  10 | 20 | 25│  │  30 | 40 | 50│                            │
│  └──────────────┘  └──────────────┘                            │
│              │           │                                      │
│              └─────┬─────┘                                      │
│                    ▼                                             │
│            Parent updated with new child pointer                │
│            (may cascade if parent is also full)                 │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Write-Ahead Log (WAL) for B-Trees

Every B-tree modification is first written to a **write-ahead log** (WAL / redo log) before modifying the tree pages. On crash, the WAL is replayed to restore the B-tree to a consistent state.

```
Write flow:  Write → WAL (append-only) → Modify B-tree page(s)
Crash:       Replay WAL to fix any partially-written pages
```

---

## B-Trees vs LSM-Trees

```
┌─────────────────────────────────────────────────────────────────┐
│              B-TREES vs LSM-TREES COMPARISON                    │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Aspect          │ B-Tree              │ LSM-Tree              │
│  ────────────────┼─────────────────────┼───────────────────── │
│  Write pattern   │ Random I/O (update  │ Sequential I/O        │
│                  │ in place)           │ (append-only)         │
│  Write throughput│ Lower               │ Higher                │
│  Write amplific. │ Lower (1 WAL + 1    │ Higher (compaction    │
│                  │ page write)         │ rewrites data)        │
│  Read performance│ Faster (one lookup) │ Slower (check multiple│
│                  │                     │ SSTables/levels)      │
│  Space usage     │ Fragmentation       │ Compaction reclaims   │
│                  │ possible            │ space; but temp dup.  │
│  Predictability  │ More predictable    │ Compaction can cause  │
│                  │ latency             │ latency spikes        │
│  Concurrency     │ Latch per page      │ Simpler (immutable    │
│                  │                     │ SSTables)             │
│  Range queries   │ Excellent (sorted   │ Good (sorted within   │
│                  │ leaf pages linked)  │ SSTables)             │
│  Key uniqueness  │ Easy (one place     │ Harder (key may exist │
│                  │ per key)            │ in multiple SSTables) │
│  Transaction     │ Easier (lock        │ Harder                │
│  isolation       │ ranges of keys)     │                       │
│                                                                 │
│  Used by:                                                       │
│  B-Tree: PostgreSQL, MySQL/InnoDB, Oracle, SQL Server           │
│  LSM-Tree: RocksDB, LevelDB, Cassandra, HBase, ScyllaDB        │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Write Amplification

```
┌─────────────────────────────────────────────────────────────────┐
│              WRITE AMPLIFICATION                                 │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  One database write → multiple disk writes                      │
│                                                                 │
│  B-Tree:                                                        │
│  App write → WAL write + Page write = 2x amplification          │
│  (Sometimes more if page splits cascade)                        │
│                                                                 │
│  LSM-Tree:                                                      │
│  App write → WAL + Memtable flush + L0→L1 compaction +          │
│              L1→L2 compaction + ... = 10-30x amplification      │
│                                                                 │
│  High write amplification concerns:                             │
│  • SSD lifetime (limited write cycles per cell)                 │
│  • Disk bandwidth consumed by compaction vs. actual writes      │
│                                                                 │
│  But LSM writes are SEQUENTIAL → much faster on SSDs/HDDs       │
│  than B-tree's RANDOM writes. Net throughput often better.      │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## Other Indexing Structures

### Clustered vs Non-Clustered Indexes

```
┌─────────────────────────────────────────────────────────────────┐
│  NON-CLUSTERED INDEX              CLUSTERED INDEX               │
│  (most secondary indexes)        (InnoDB primary key)           │
│                                                                 │
│  Index leaf page:                 Index leaf page:               │
│  ┌─────────────────┐             ┌─────────────────────────┐   │
│  │ key → pointer   │──►heap      │ key → actual row data   │   │
│  │      to heap    │   file      │      (stored in index)  │   │
│  └─────────────────┘             └─────────────────────────┘   │
│                                                                 │
│  Extra hop to read data           No extra hop (data locality) │
│  Write: update heap + index       Write: update index directly │
│  Multiple indexes → same heap     Only ONE clustered index     │
│                                                                 │
│  COVERING INDEX (compromise):                                   │
│  Store SOME columns in the index (not just the key).            │
│  Queries reading only those columns are answered from the       │
│  index alone — no heap lookup. Called an "index-only scan."     │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Multi-Column Indexes

```
┌─────────────────────────────────────────────────────────────────┐
│  CONCATENATED INDEX:                                            │
│  (last_name, first_name) → sorted by last_name, then first     │
│  Good for: WHERE last_name = 'Smith' AND first_name = 'John'   │
│  Good for: WHERE last_name = 'Smith' (prefix)                  │
│  Bad for:  WHERE first_name = 'John' (not a prefix!)           │
│                                                                 │
│  MULTI-DIMENSIONAL INDEX (R-tree):                              │
│  For geospatial queries:                                        │
│  SELECT * FROM restaurants                                      │
│  WHERE latitude BETWEEN 51.4 AND 51.6                           │
│    AND longitude BETWEEN -0.2 AND 0.1;                         │
│  B-tree can only search one dimension efficiently.              │
│  R-tree indexes 2D+ space for bounding-box queries.             │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## Transaction Processing vs Analytics (OLTP vs OLAP)

```
┌──────────────────────────────────────────────────────────────────┐
│              OLTP vs OLAP                                        │
├──────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Property          │ OLTP                 │ OLAP (Data Warehouse)│
│  ──────────────────┼──────────────────────┼─────────────────── │
│  Read pattern      │ Few records per query│ Aggregate over many  │
│                    │ fetched by key       │ records              │
│  Write pattern     │ Random-access, low-  │ Bulk import (ETL)    │
│                    │ latency user input   │ or event stream      │
│  Used by           │ End users via web app│ Internal analysts    │
│  Data represents   │ Latest state (now)   │ History of events    │
│  Dataset size      │ GB to TB             │ TB to PB             │
│  Bottleneck        │ Disk seek time       │ Disk bandwidth       │
│                                                                  │
│  ┌────────────┐    ETL     ┌─────────────────┐                  │
│  │ OLTP DB 1  │──────────►│                 │                  │
│  └────────────┘    Extract │  Data Warehouse │                  │
│  ┌────────────┐  Transform│  (OLAP)         │                  │
│  │ OLTP DB 2  │──── Load ►│                 │                  │
│  └────────────┘           │  Optimized for  │                  │
│  ┌────────────┐           │  analytics      │                  │
│  │ OLTP DB 3  │──────────►│  queries        │                  │
│  └────────────┘           └─────────────────┘                  │
│                                                                  │
│  Examples:                                                       │
│  OLTP: PostgreSQL, MySQL, Oracle (operational)                   │
│  OLAP: Amazon Redshift, Snowflake, ClickHouse, BigQuery          │
│                                                                  │
└──────────────────────────────────────────────────────────────────┘
```

### Star Schema (Dimensional Modeling)

```
┌──────────────────────────────────────────────────────────────────┐
│              STAR SCHEMA                                         │
├──────────────────────────────────────────────────────────────────┤
│                                                                  │
│              ┌──────────────┐                                    │
│              │ dim_product  │                                    │
│              │ ─────────── │                                    │
│              │ product_id   │                                    │
│              │ name         │                                    │
│              │ category     │                                    │
│              │ brand        │                                    │
│              └──────┬───────┘                                    │
│                     │                                            │
│  ┌──────────────┐   │   ┌──────────────────────────┐            │
│  │  dim_date    │   │   │    fact_sales             │            │
│  │ ──────────  │   │   │    ──────────             │            │
│  │  date_id    ├───┼───┤  sale_id                  │            │
│  │  day        │   │   │  date_id (FK)             │            │
│  │  month      │   │   │  product_id (FK)          │            │
│  │  quarter    │   │   │  store_id (FK)            │            │
│  │  year       │   │   │  customer_id (FK)         │            │
│  └─────────────┘   │   │  quantity                 │            │
│                     │   │  price                    │            │
│  ┌──────────────┐   │   │  discount                │            │
│  │ dim_store    ├───┘   └──────────┬───────────────┘            │
│  │ ──────────  │                   │                            │
│  │ store_id    │                   │                            │
│  │ city        │        ┌──────────┴───────┐                    │
│  │ state       │        │  dim_customer    │                    │
│  │ country     │        │  ────────────   │                    │
│  └─────────────┘        │  customer_id    │                    │
│                          │  name           │                    │
│                          │  segment        │                    │
│                          └─────────────────┘                    │
│                                                                  │
│  FACT TABLE: Each row = an event (sale, click, shipment)         │
│  DIMENSION TABLES: Who, what, where, when, how                   │
│  The "star" shape comes from fact table at center,               │
│  dimension tables radiating outward.                             │
│                                                                  │
│  SNOWFLAKE SCHEMA: Dimensions further normalized                 │
│  (dim_product → dim_category → dim_department)                   │
│                                                                  │
└──────────────────────────────────────────────────────────────────┘
```

---

## Column-Oriented Storage

In OLAP queries, you typically access only 3-5 columns out of 100+ in a table. Column-oriented storage stores all values of a column together:

```
┌──────────────────────────────────────────────────────────────────┐
│              ROW-ORIENTED vs COLUMN-ORIENTED STORAGE             │
├──────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ROW-ORIENTED (traditional):                                     │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │ Row 1: date=2024-01-01, product=68, store=4, qty=1  ... │   │
│  │ Row 2: date=2024-01-01, product=69, store=5, qty=3  ... │   │
│  │ Row 3: date=2024-01-02, product=68, store=4, qty=2  ... │   │
│  └──────────────────────────────────────────────────────────┘   │
│  Reading 3 columns out of 100 → must load ALL 100 columns       │
│                                                                  │
│  COLUMN-ORIENTED:                                                │
│  ┌──────────────────────────────────────┐                       │
│  │ date column:    [2024-01-01, 2024-01-01, 2024-01-02, ...]  │ │
│  │ product column: [68, 69, 68, ...]                           │ │
│  │ store column:   [4, 5, 4, ...]                              │ │
│  │ qty column:     [1, 3, 2, ...]                              │ │
│  └──────────────────────────────────────┘                       │
│  Reading 3 columns → load ONLY those 3 column files             │
│                                                                  │
│  Query: SELECT product_id, SUM(quantity)                         │
│         FROM fact_sales                                          │
│         WHERE date BETWEEN '2024-01-01' AND '2024-01-31'        │
│         GROUP BY product_id;                                     │
│                                                                  │
│  Row-oriented: Must read entire rows (100 columns × millions)   │
│  Column-oriented: Read only date + product + quantity columns   │
│                                                                  │
└──────────────────────────────────────────────────────────────────┘
```

### Column Compression

```
┌──────────────────────────────────────────────────────────────────┐
│              BITMAP ENCODING (Column Compression)                │
├──────────────────────────────────────────────────────────────────┤
│                                                                  │
│  product_id column has values: [69, 69, 69, 74, 31, 31, ...]   │
│                                                                  │
│  Bitmap for product_id = 69:  [1, 1, 1, 0, 0, 0, ...]          │
│  Bitmap for product_id = 74:  [0, 0, 0, 1, 0, 0, ...]          │
│  Bitmap for product_id = 31:  [0, 0, 0, 0, 1, 1, ...]          │
│                                                                  │
│  WHERE product_id IN (69, 74):                                   │
│  → Bitwise OR of bitmaps for 69 and 74                          │
│  → [1, 1, 1, 1, 0, 0, ...] — very fast!                       │
│                                                                  │
│  Run-Length Encoding (RLE):                                      │
│  [1,1,1,0,0,0,0,0,0,0,0,0,...] → "3 ones, then 9 zeros, ..."  │
│  Extremely compact for sparse bitmaps.                           │
│                                                                  │
│  Vectorized processing:                                          │
│  Compressed columns loaded into CPU L1 cache → bitwise ops      │
│  process thousands of values in single CPU cycle (SIMD).        │
│                                                                  │
└──────────────────────────────────────────────────────────────────┘
```

### Materialized Views and Data Cubes

```
┌──────────────────────────────────────────────────────────────────┐
│              DATA CUBE (OLAP Cube)                                │
├──────────────────────────────────────────────────────────────────┤
│                                                                  │
│           Product                                                │
│           ┌────┬────┬────┬────┬──────┐                          │
│           │ P1 │ P2 │ P3 │ P4 │ TOTAL│                          │
│  ┌────┬───┼────┼────┼────┼────┼──────┤                          │
│  │Date│ D1│ 52 │ 30 │ 18 │ 44 │  144 │                          │
│  │    │ D2│ 63 │ 41 │ 22 │ 35 │  161 │                          │
│  │    │ D3│ 48 │ 28 │ 25 │ 51 │  152 │                          │
│  │    │TOT│163 │ 99 │ 65 │130 │  457 │                          │
│  └────┴───┴────┴────┴────┴────┴──────┘                          │
│                                                                  │
│  Pre-aggregated totals along each dimension.                     │
│  Fast for known aggregate queries.                               │
│  Inflexible — can't answer queries not in the cube's dimensions.│
│                                                                  │
└──────────────────────────────────────────────────────────────────┘
```

---

## Interview Questions

### Q1: Explain the difference between B-Trees and LSM-Trees.

B-Trees update data **in place** on fixed-size pages, using a balanced tree structure with O(log n) reads. LSM-Trees use an **append-only** approach: writes go to an in-memory memtable, which is periodically flushed to sorted SSTables on disk. Background compaction merges SSTables. B-Trees have faster reads (single lookup path) but slower writes (random I/O). LSM-Trees have faster writes (sequential I/O) but slower reads (must check multiple levels). B-Trees are used by most relational DBs; LSM-Trees by RocksDB, Cassandra, HBase.

### Q2: What is write amplification and why does it matter?

Write amplification is when one application write causes multiple actual disk writes. In B-Trees: WAL write + page write = ~2x. In LSM-Trees: WAL + memtable flush + multiple compaction levels = 10-30x. It matters because: (1) it consumes disk bandwidth that could serve other operations, (2) on SSDs it reduces drive lifetime (limited write cycles per cell). However, LSM-Trees compensate with sequential writes which are much faster than B-Tree's random writes.

### Q3: Why do analytics databases use column-oriented storage?

OLAP queries typically read only 3-5 columns out of 100+ in a wide fact table. Row-oriented storage must load all columns for each row. Column-oriented storage stores each column separately, so a query reads only the needed columns. Additional benefits: (1) better compression (similar values in a column compress well — bitmap encoding, RLE), (2) vectorized processing (compressed column chunks fit in CPU L1 cache for SIMD operations), (3) sort order can cluster related values for even better compression and locality.

### Q4: What is a Bloom filter and why is it used in LSM-Trees?

A Bloom filter is a memory-efficient probabilistic data structure that tells you either "definitely NOT in the set" or "possibly in the set" (with a small false-positive rate). In LSM-Trees, looking up a non-existent key requires checking every SSTable level — very expensive. A Bloom filter per SSTable lets you skip SSTables that definitely don't contain the key, dramatically reducing unnecessary disk reads.

### Q5: Explain the star schema in data warehousing.

The star schema has a central **fact table** (each row = an event, like a sale) surrounded by **dimension tables** (who, what, where, when). The fact table contains foreign keys to dimensions plus metric columns (quantity, price). It's called "star" because the fact table sits at the center with dimension tables radiating outward. A variant called the **snowflake schema** further normalizes dimensions into sub-dimensions. Star schemas are simpler to query and are the standard for OLAP workloads.

---

*Based on Chapter 3 of "Designing Data-Intensive Applications" by Martin Kleppmann*
