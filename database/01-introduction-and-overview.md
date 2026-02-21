# Chapter 1: Introduction and Overview - Database Storage Engines

## Table of Contents

1. [The Essence of Database Systems](#the-essence-of-database-systems)
2. [Storage Engine Architecture](#storage-engine-architecture)
3. [OLTP vs OLAP: The Fundamental Divide](#oltp-vs-olap-the-fundamental-divide)
4. [Row-Oriented vs Column-Oriented Storage](#row-oriented-vs-column-oriented-storage)
5. [Memory-Based vs Disk-Based Engines](#memory-based-vs-disk-based-engines)
6. [Data Files and Index Files](#data-files-and-index-files)
7. [Buffer Management and Caching](#buffer-management-and-caching)
8. [Storage Engine Classification](#storage-engine-classification)
9. [Real-World Storage Engine Examples](#real-world-storage-engine-examples)

---

## The Essence of Database Systems

A database management system (DBMS) is fundamentally a sophisticated system for **storing**, **retrieving**, and **manipulating** data efficiently. At its core, every database must solve a fundamental tension:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                     THE DATABASE TRILEMMA                                   │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│     PERFORMANCE                                                             │
│         │                                                                   │
│         │    "Fast reads OR fast writes OR low storage"                     │
│         │    "Pick two, optimize for one"                                   │
│         ▼                                                                   │
│    ┌─────────────────────────────────────────┐                              │
│    │                                         │                              │
│    │   Every database design is a series    │                              │
│    │   of tradeoffs optimized for specific  │                              │
│    │   workloads and access patterns        │                              │
│    │                                         │                              │
│    └─────────────────────────────────────────┘                              │
│         │                         │                                         │
│         ▼                         ▼                                         │
│    DURABILITY              STORAGE EFFICIENCY                               │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Why Storage Engines Matter

The storage engine is the **lowest level component** responsible for:
- How data is physically laid out on disk
- How indexes are structured and maintained
- How writes are persisted durably
- How reads traverse data structures efficiently
- How concurrent operations are coordinated

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        DATABASE ARCHITECTURE STACK                          │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌───────────────────────────────────────────────────────────────────┐     │
│  │                    APPLICATION LAYER                               │     │
│  │              (SQL Queries, Client Connections)                     │     │
│  └───────────────────────────────────────────────────────────────────┘     │
│                              │                                              │
│                              ▼                                              │
│  ┌───────────────────────────────────────────────────────────────────┐     │
│  │                     QUERY PROCESSOR                                │     │
│  │         (Parser, Optimizer, Execution Engine)                      │     │
│  └───────────────────────────────────────────────────────────────────┘     │
│                              │                                              │
│                              ▼                                              │
│  ┌───────────────────────────────────────────────────────────────────┐     │
│  │                  TRANSACTION MANAGER                               │     │
│  │         (Concurrency Control, Recovery)                            │     │
│  └───────────────────────────────────────────────────────────────────┘     │
│                              │                                              │
│                              ▼                                              │
│  ┌───────────────────────────────────────────────────────────────────┐     │
│  │              ★ STORAGE ENGINE ★                                    │     │
│  │                                                                    │     │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐             │     │
│  │  │ Buffer Pool  │  │   Indexes    │  │  Data Files  │             │     │
│  │  └──────────────┘  └──────────────┘  └──────────────┘             │     │
│  │                                                                    │     │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐             │     │
│  │  │     WAL      │  │  Lock Mgr    │  │ Page Cache   │             │     │
│  │  └──────────────┘  └──────────────┘  └──────────────┘             │     │
│  └───────────────────────────────────────────────────────────────────┘     │
│                              │                                              │
│                              ▼                                              │
│  ┌───────────────────────────────────────────────────────────────────┐     │
│  │                   FILE SYSTEM / OS                                 │     │
│  └───────────────────────────────────────────────────────────────────┘     │
│                              │                                              │
│                              ▼                                              │
│  ┌───────────────────────────────────────────────────────────────────┐     │
│  │                    DISK STORAGE                                    │     │
│  │              (HDD, SSD, NVMe, Network Storage)                     │     │
│  └───────────────────────────────────────────────────────────────────┘     │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Storage Engine Architecture

The storage engine can be decomposed into several critical subsystems:

### Core Components

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    STORAGE ENGINE INTERNALS                                 │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  1. BUFFER POOL MANAGER                                                     │
│     ├── Page cache for frequently accessed data                             │
│     ├── LRU/Clock replacement policies                                      │
│     ├── Dirty page tracking                                                 │
│     └── Prefetching and read-ahead                                          │
│                                                                             │
│  2. INDEX MANAGER                                                           │
│     ├── Primary indexes (clustered)                                         │
│     ├── Secondary indexes (non-clustered)                                   │
│     ├── B-Tree, B+Tree, LSM-Tree, Hash indexes                              │
│     └── Index maintenance and reorganization                                │
│                                                                             │
│  3. RECORD MANAGER                                                          │
│     ├── Row/tuple storage format                                            │
│     ├── Variable-length field handling                                      │
│     ├── NULL value representation                                           │
│     └── Row versioning for MVCC                                             │
│                                                                             │
│  4. PAGE MANAGER                                                            │
│     ├── Fixed-size page allocation                                          │
│     ├── Free space management                                               │
│     ├── Page splits and merges                                              │
│     └── Slotted page organization                                           │
│                                                                             │
│  5. LOG MANAGER (WAL)                                                       │
│     ├── Write-ahead logging                                                 │
│     ├── Log record formatting                                               │
│     ├── Checkpointing                                                       │
│     └── Recovery protocols                                                  │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## OLTP vs OLAP: The Fundamental Divide

Databases are designed for fundamentally different workloads, and this distinction drives nearly every architectural decision.

### OLTP (Online Transaction Processing)

OLTP systems handle **high volumes of short, atomic transactions** typical of operational databases.

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           OLTP CHARACTERISTICS                              │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  WORKLOAD PATTERN                                                           │
│  ────────────────                                                           │
│  • High transaction throughput (thousands/sec)                              │
│  • Small, random read/write operations                                      │
│  • Point queries and range scans on indexes                                 │
│  • Insert, Update, Delete heavy                                             │
│  • Low latency requirements (milliseconds)                                  │
│                                                                             │
│  TYPICAL QUERIES                                                            │
│  ───────────────                                                            │
│  SELECT * FROM orders WHERE order_id = 12345;                               │
│  UPDATE accounts SET balance = balance - 100 WHERE account_id = 789;        │
│  INSERT INTO transactions VALUES (...);                                     │
│                                                                             │
│  DESIGN PRIORITIES                                                          │
│  ─────────────────                                                          │
│  1. Low latency for individual operations                                   │
│  2. High concurrency (many simultaneous users)                              │
│  3. ACID transaction guarantees                                             │
│  4. Fast index lookups                                                      │
│  5. Efficient write paths                                                   │
│                                                                             │
│  EXAMPLE SYSTEMS                                                            │
│  ───────────────                                                            │
│  • Banking transaction systems                                              │
│  • E-commerce order processing                                              │
│  • Session management                                                       │
│  • Real-time inventory                                                      │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### OLAP (Online Analytical Processing)

OLAP systems are optimized for **complex analytical queries** over large datasets.

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           OLAP CHARACTERISTICS                              │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  WORKLOAD PATTERN                                                           │
│  ────────────────                                                           │
│  • Complex aggregation queries                                              │
│  • Full table scans and large range scans                                   │
│  • Read-heavy (writes are batch/bulk loads)                                 │
│  • High throughput over latency                                             │
│  • Query response in seconds to minutes                                     │
│                                                                             │
│  TYPICAL QUERIES                                                            │
│  ───────────────                                                            │
│  SELECT region, SUM(sales), AVG(profit)                                     │
│  FROM sales_data                                                            │
│  WHERE date BETWEEN '2024-01-01' AND '2024-12-31'                           │
│  GROUP BY region                                                            │
│  ORDER BY SUM(sales) DESC;                                                  │
│                                                                             │
│  DESIGN PRIORITIES                                                          │
│  ─────────────────                                                          │
│  1. High scan throughput                                                    │
│  2. Efficient compression                                                   │
│  3. Columnar access patterns                                                │
│  4. Parallel query execution                                                │
│  5. Aggregation optimization                                                │
│                                                                             │
│  EXAMPLE SYSTEMS                                                            │
│  ───────────────                                                            │
│  • Business intelligence dashboards                                         │
│  • Data warehouses                                                          │
│  • Financial reporting                                                      │
│  • Machine learning pipelines                                               │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### OLTP vs OLAP Comparison

```
┌──────────────────┬──────────────────────────────┬──────────────────────────────┐
│   DIMENSION      │           OLTP               │           OLAP               │
├──────────────────┼──────────────────────────────┼──────────────────────────────┤
│ Query Type       │ Simple, point queries        │ Complex, aggregations        │
│ Data Access      │ Random access patterns       │ Sequential scan patterns     │
│ Transactions     │ Many short transactions      │ Few long-running queries     │
│ Data Freshness   │ Real-time, current data      │ Historical, periodic refresh │
│ Schema           │ Normalized (3NF)             │ Denormalized (star/snowflake)│
│ Index Strategy   │ Many indexes for lookups     │ Fewer indexes, more scans    │
│ Storage Layout   │ Row-oriented                 │ Column-oriented              │
│ Concurrency      │ Thousands of users           │ Dozens of analysts           │
│ Response Time    │ Milliseconds                 │ Seconds to minutes           │
│ Data Volume      │ Gigabytes to Terabytes       │ Terabytes to Petabytes       │
└──────────────────┴──────────────────────────────┴──────────────────────────────┘
```

---

## Row-Oriented vs Column-Oriented Storage

The physical layout of data on disk has profound implications for query performance.

### Row-Oriented Storage (N-ary Storage Model / NSM)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        ROW-ORIENTED STORAGE                                 │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  PHYSICAL LAYOUT (How data is stored on disk)                               │
│  ──────────────────────────────────────────────                             │
│                                                                             │
│  Table: employees                                                           │
│  ┌────────┬────────────┬─────┬────────┬──────────┐                          │
│  │ emp_id │ name       │ age │ dept   │ salary   │                          │
│  ├────────┼────────────┼─────┼────────┼──────────┤                          │
│  │ 1      │ Alice      │ 30  │ Eng    │ 100000   │                          │
│  │ 2      │ Bob        │ 25  │ Sales  │ 80000    │                          │
│  │ 3      │ Carol      │ 35  │ Eng    │ 120000   │                          │
│  └────────┴────────────┴─────┴────────┴──────────┘                          │
│                                                                             │
│  Disk Layout (Row Store):                                                   │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ Page 1                                                              │   │
│  │ ┌─────────────────────────────────────────────────────────────────┐ │   │
│  │ │ [1, Alice, 30, Eng, 100000] [2, Bob, 25, Sales, 80000] [3,...]  │ │   │
│  │ └─────────────────────────────────────────────────────────────────┘ │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  All columns of a row are stored CONTIGUOUSLY                               │
│                                                                             │
│  ADVANTAGES                                                                 │
│  ──────────                                                                 │
│  ✓ Excellent for point queries (SELECT * FROM emp WHERE id = 1)             │
│  ✓ Efficient INSERT/UPDATE/DELETE (single I/O for entire row)               │
│  ✓ Natural representation of tuples                                         │
│  ✓ Good cache locality for row-at-a-time access                             │
│                                                                             │
│  DISADVANTAGES                                                              │
│  ─────────────                                                              │
│  ✗ Inefficient for analytical queries (must read all columns)               │
│  ✗ Poor compression (mixed data types per row)                              │
│  ✗ Wasted I/O for partial column reads                                      │
│                                                                             │
│  EXAMPLES: PostgreSQL, MySQL/InnoDB, Oracle, SQL Server                     │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Column-Oriented Storage (Decomposed Storage Model / DSM)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                      COLUMN-ORIENTED STORAGE                                │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  PHYSICAL LAYOUT (How data is stored on disk)                               │
│  ──────────────────────────────────────────────                             │
│                                                                             │
│  Same table stored as SEPARATE column files:                                │
│                                                                             │
│  emp_id.col:   ┌─────────────────────────────┐                              │
│                │ [1] [2] [3] [4] [5] ...     │                              │
│                └─────────────────────────────┘                              │
│                                                                             │
│  name.col:     ┌─────────────────────────────┐                              │
│                │ [Alice] [Bob] [Carol] ...   │                              │
│                └─────────────────────────────┘                              │
│                                                                             │
│  age.col:      ┌─────────────────────────────┐                              │
│                │ [30] [25] [35] [28] ...     │                              │
│                └─────────────────────────────┘                              │
│                                                                             │
│  dept.col:     ┌─────────────────────────────┐                              │
│                │ [Eng] [Sales] [Eng] ...     │                              │
│                └─────────────────────────────┘                              │
│                                                                             │
│  salary.col:   ┌─────────────────────────────┐                              │
│                │ [100000] [80000] [120000]   │                              │
│                └─────────────────────────────┘                              │
│                                                                             │
│  Each column stored SEPARATELY and CONTIGUOUSLY                             │
│                                                                             │
│  ADVANTAGES                                                                 │
│  ──────────                                                                 │
│  ✓ Excellent compression (similar values together)                          │
│  ✓ Read only needed columns (reduced I/O)                                   │
│  ✓ SIMD vectorized operations                                               │
│  ✓ Better cache utilization for aggregations                                │
│  ✓ Late materialization optimization                                        │
│                                                                             │
│  DISADVANTAGES                                                              │
│  ─────────────                                                              │
│  ✗ Expensive tuple reconstruction (joining columns)                         │
│  ✗ Slower point queries (must access multiple files)                        │
│  ✗ Complex INSERT/UPDATE (modify multiple files)                            │
│                                                                             │
│  EXAMPLES: ClickHouse, Apache Parquet, DuckDB, Vertica, Amazon Redshift     │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Compression in Column Stores

Column stores achieve exceptional compression ratios through several techniques:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    COLUMN COMPRESSION TECHNIQUES                            │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  1. RUN-LENGTH ENCODING (RLE)                                               │
│     ─────────────────────────                                               │
│     Original: [Eng] [Eng] [Eng] [Eng] [Sales] [Sales]                       │
│     Encoded:  [(Eng, 4), (Sales, 2)]                                        │
│                                                                             │
│     Best for: sorted columns with many repeated values                      │
│                                                                             │
│  2. DICTIONARY ENCODING                                                     │
│     ─────────────────────                                                   │
│     Dictionary: {0: "Engineering", 1: "Sales", 2: "Marketing"}              │
│     Original:   [Engineering, Sales, Engineering, Marketing]                │
│     Encoded:    [0, 1, 0, 2]  (using small integers)                        │
│                                                                             │
│     Best for: low cardinality string columns                                │
│                                                                             │
│  3. BIT-PACKING                                                             │
│     ───────────                                                             │
│     If values range 0-15, use 4 bits instead of 32 bits                     │
│     8x compression for small integer ranges                                 │
│                                                                             │
│  4. DELTA ENCODING                                                          │
│     ──────────────                                                          │
│     Original: [1000, 1001, 1003, 1004, 1010]                                │
│     Encoded:  [1000, +1, +2, +1, +6]                                        │
│                                                                             │
│     Best for: sorted or sequential values (timestamps, IDs)                 │
│                                                                             │
│  5. FRAME OF REFERENCE (FOR)                                                │
│     ───────────────────────                                                 │
│     Store base value + small offsets                                        │
│     [10000, 10005, 10003] → base=10000, offsets=[0, 5, 3]                   │
│                                                                             │
│  COMPRESSION RATIOS                                                         │
│  ───────────────────                                                        │
│  Row stores: typically 2-4x compression                                     │
│  Column stores: typically 10-100x compression                               │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```


---

## Memory-Based vs Disk-Based Engines

The choice between memory-resident and disk-based storage fundamentally shapes engine design.

### Disk-Based Storage Engines

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                      DISK-BASED STORAGE ENGINES                             │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  DESIGN PHILOSOPHY                                                          │
│  ─────────────────                                                          │
│  "Data is too large to fit in memory; disk is primary storage"              │
│                                                                             │
│  ARCHITECTURE                                                               │
│  ────────────                                                               │
│                                                                             │
│  ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐         │
│  │    Application  │───▶│   Buffer Pool   │◀──▶│    Disk Files   │         │
│  │    (Queries)    │    │   (Memory)      │    │   (Persistent)  │         │
│  └─────────────────┘    └─────────────────┘    └─────────────────┘         │
│                               │                        │                    │
│                               │  Page-based I/O        │                    │
│                               │  (4KB, 8KB, 16KB)      │                    │
│                               ▼                        ▼                    │
│                         ┌─────────────────────────────────┐                 │
│                         │  Write-Ahead Log (WAL)          │                 │
│                         │  (Durability guarantee)         │                 │
│                         └─────────────────────────────────┘                 │
│                                                                             │
│  KEY CHARACTERISTICS                                                        │
│  ───────────────────                                                        │
│  • Page-oriented: Data organized in fixed-size pages (typically 4-16 KB)    │
│  • Buffer pool: In-memory cache of frequently accessed pages                │
│  • WAL for durability: Log writes before data page writes                   │
│  • Optimized for disk I/O: Minimize random seeks, maximize sequential I/O   │
│  • B-Tree indexes: Minimize tree height to reduce disk reads                │
│                                                                             │
│  DISK I/O CONSIDERATIONS                                                    │
│  ───────────────────────                                                    │
│                                                                             │
│  HDD (Hard Disk Drive):                                                     │
│  • Random read: ~10ms (seek + rotation)                                     │
│  • Sequential read: ~100 MB/s                                               │
│  • Random reads are 100-1000x slower than sequential!                       │
│                                                                             │
│  SSD (Solid State Drive):                                                   │
│  • Random read: ~0.1ms                                                      │
│  • Sequential read: ~500 MB/s - 7 GB/s (NVMe)                               │
│  • Random/sequential gap much smaller than HDD                              │
│                                                                             │
│  EXAMPLES: PostgreSQL, MySQL/InnoDB, SQLite, Oracle, RocksDB                │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Memory-Based (In-Memory) Storage Engines

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                     IN-MEMORY STORAGE ENGINES                               │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  DESIGN PHILOSOPHY                                                          │
│  ─────────────────                                                          │
│  "Memory is primary storage; disk is for durability only"                   │
│                                                                             │
│  ARCHITECTURE                                                               │
│  ────────────                                                               │
│                                                                             │
│  ┌─────────────────┐    ┌─────────────────────────────────────────────┐    │
│  │    Application  │───▶│            Main Memory (RAM)                │    │
│  │    (Queries)    │    │   ┌─────────────────────────────────────┐   │    │
│  └─────────────────┘    │   │  Complete Database + Indexes        │   │    │
│                         │   │  (No buffer pool abstraction)       │   │    │
│                         │   └─────────────────────────────────────┘   │    │
│                         └─────────────────────────────────────────────┘    │
│                               │                                             │
│                               │ Async persistence / snapshots               │
│                               ▼                                             │
│                         ┌─────────────────────────────────────────────┐    │
│                         │  Disk (WAL + Snapshots)                      │    │
│                         │  • Append-only command log                   │    │
│                         │  • Periodic snapshots                        │    │
│                         └─────────────────────────────────────────────┘    │
│                                                                             │
│  KEY CHARACTERISTICS                                                        │
│  ───────────────────                                                        │
│  • Pointer-based: Direct memory pointers (no page indirection)              │
│  • No buffer pool: Entire database resident in memory                       │
│  • Lock-free structures: Optimized for CPU cache efficiency                 │
│  • Different index structures: T-Trees, skip lists, hash tables             │
│  • Microsecond latencies: 100-1000x faster than disk-based                  │
│                                                                             │
│  DURABILITY STRATEGIES                                                      │
│  ─────────────────────                                                      │
│  1. Command logging: Log operations, replay on restart                      │
│  2. Periodic snapshots: Full database dump + recent log replay              │
│  3. Replication: Synchronous replication to standby nodes                   │
│  4. Non-volatile memory: Emerging persistent memory technologies            │
│                                                                             │
│  TRADE-OFFS                                                                 │
│  ──────────                                                                 │
│  ✓ Extreme performance for OLTP workloads                                   │
│  ✓ Simpler concurrency (no disk I/O waits)                                  │
│  ✗ Limited by RAM capacity (expensive for large datasets)                   │
│  ✗ Longer recovery times (must reload entire database)                      │
│  ✗ Durability complexity (risk of data loss)                                │
│                                                                             │
│  EXAMPLES: Redis, Memcached, VoltDB, MemSQL/SingleStore, SAP HANA           │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Memory Hierarchy Perspective

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                      STORAGE HIERARCHY LATENCIES                            │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  LEVEL              SIZE        LATENCY         RELATIVE TO L1              │
│  ─────              ────        ───────         ────────────                │
│                                                                             │
│  L1 Cache           64 KB       ~1 ns           1x (baseline)               │
│  L2 Cache           256 KB      ~4 ns           4x                          │
│  L3 Cache           8 MB        ~12 ns          12x                         │
│  Main Memory        64+ GB      ~100 ns         100x                        │
│  NVMe SSD           TB          ~100 μs         100,000x                    │
│  SATA SSD           TB          ~500 μs         500,000x                    │
│  HDD                TB          ~10 ms          10,000,000x                 │
│  Network (DC)       ∞           ~500 μs         500,000x                    │
│  Network (WAN)      ∞           ~100 ms         100,000,000x                │
│                                                                             │
│  VISUAL SCALE (if L1 = 1 second)                                            │
│  ────────────────────────────────                                           │
│  L1 Cache:     1 second                                                     │
│  L2 Cache:     4 seconds                                                    │
│  L3 Cache:     12 seconds                                                   │
│  RAM:          1.5 minutes                                                  │
│  NVMe SSD:     1 day                                                        │
│  HDD:          4 months                                                     │
│  Network:      3 years (WAN)                                                │
│                                                                             │
│  ═══════════════════════════════════════════════════════════════════════   │
│  IMPLICATION: Disk-based engines MUST minimize I/O operations               │
│               Memory-based engines optimize for CPU cache efficiency        │
│  ═══════════════════════════════════════════════════════════════════════   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Data Files and Index Files

Storage engines maintain two primary types of files:

### Data Files (Heap Files)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           DATA FILE ORGANIZATION                            │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  HEAP FILE STRUCTURE                                                        │
│  ───────────────────                                                        │
│  An unordered collection of records (tuples) stored in pages                │
│                                                                             │
│  ┌────────────────────────────────────────────────────────────────────┐    │
│  │                         Heap File                                  │    │
│  │  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐ │    │
│  │  │  Page 0  │ │  Page 1  │ │  Page 2  │ │  Page 3  │ │  Page N  │ │    │
│  │  │ ──────── │ │ ──────── │ │ ──────── │ │ ──────── │ │ ──────── │ │    │
│  │  │ Record 1 │ │ Record 4 │ │ Record 7 │ │ Record 9 │ │   ...    │ │    │
│  │  │ Record 2 │ │ Record 5 │ │ Record 8 │ │ Record10 │ │          │ │    │
│  │  │ Record 3 │ │ Record 6 │ │          │ │          │ │          │ │    │
│  │  └──────────┘ └──────────┘ └──────────┘ └──────────┘ └──────────┘ │    │
│  └────────────────────────────────────────────────────────────────────┘    │
│                                                                             │
│  HEAP FILE TYPES                                                            │
│  ───────────────                                                            │
│                                                                             │
│  1. UNORDERED HEAP                                                          │
│     • Records inserted at any location with free space                      │
│     • Fast inserts, slow sequential scans for specific values               │
│     • Requires full table scan without index                                │
│                                                                             │
│  2. CLUSTERED (INDEX-ORGANIZED)                                             │
│     • Records ordered by primary key                                        │
│     • Data stored in leaf nodes of B-Tree                                   │
│     • Range queries on primary key are efficient                            │
│     • Examples: InnoDB clustered index, SQLite without ROWID                │
│                                                                             │
│  RECORD IDENTIFIERS (RIDs / TIDs / CTIDs)                                   │
│  ─────────────────────────────────────────                                  │
│  Each record has a physical address: (page_id, slot_number)                 │
│                                                                             │
│  PostgreSQL CTID: (42, 7) = Page 42, Slot 7                                 │
│  Oracle ROWID: encoded as base64 string                                     │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```



### Index Files

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                             INDEX STRUCTURES                                │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  PURPOSE: Speed up data retrieval without scanning all records              │
│                                                                             │
│  PRIMARY INDEX TYPES                                                        │
│  ───────────────────                                                        │
│                                                                             │
│  1. HASH INDEX                                                              │
│     ┌─────────────────────────────────────────────────────────┐             │
│     │  Key → Hash(Key) → Bucket → Record                      │             │
│     │                                                         │             │
│     │  hash(key) = bucket_id                                  │             │
│     │  ┌────────┐    ┌────────────┐                           │             │
│     │  │ "alice"│───▶│ Bucket 42  │───▶ [Record Pointer]      │             │
│     │  └────────┘    └────────────┘                           │             │
│     │                                                         │             │
│     │  ✓ O(1) point lookups                                   │             │
│     │  ✗ No range queries (keys not ordered)                  │             │
│     │  ✗ Resize (rehash) can be expensive                     │             │
│     └─────────────────────────────────────────────────────────┘             │
│                                                                             │
│  2. B-TREE / B+TREE INDEX                                                   │
│     ┌─────────────────────────────────────────────────────────┐             │
│     │          [Root: 50, 100]                                │             │
│     │          /      |       \                               │             │
│     │    [10,30]   [60,80]    [120,150]                       │             │
│     │    /  |  \   /  |  \    /   |   \                       │             │
│     │  [leafs with actual data pointers]                      │             │
│     │                                                         │             │
│     │  ✓ O(log n) lookups, inserts, deletes                   │             │
│     │  ✓ Efficient range queries (leaves are linked)          │             │
│     │  ✓ Self-balancing                                       │             │
│     │  → Dominant index type in disk-based databases          │             │
│     └─────────────────────────────────────────────────────────┘             │
│                                                                             │
│  3. LSM-TREE (Log-Structured Merge Tree)                                    │
│     ┌─────────────────────────────────────────────────────────┐             │
│     │  Write Path:                                            │             │
│     │  Write → MemTable (in-memory) → SSTable (on disk)       │             │
│     │                                                         │             │
│     │  ┌─────────┐                                            │             │
│     │  │MemTable│  (sorted, in-memory)                        │             │
│     │  └────┬────┘                                            │             │
│     │       ▼ (flush when full)                               │             │
│     │  ┌─────────┐ ┌─────────┐ ┌─────────┐                    │             │
│     │  │SSTable 1│ │SSTable 2│ │SSTable 3│  Level 0           │             │
│     │  └─────────┘ └─────────┘ └─────────┘                    │             │
│     │       ↓ (compaction merges tables)                      │             │
│     │  ┌──────────────────────────────────┐                   │             │
│     │  │        Larger SSTables           │  Level 1+         │             │
│     │  └──────────────────────────────────┘                   │             │
│     │                                                         │             │
│     │  ✓ O(1) sequential writes (very fast)                   │             │
│     │  ✗ Read amplification (check multiple levels)           │             │
│     │  → Optimized for write-heavy workloads                  │             │
│     └─────────────────────────────────────────────────────────┘             │
│                                                                             │
│  CLUSTERED vs NON-CLUSTERED INDEXES                                         │
│  ──────────────────────────────────                                         │
│                                                                             │
│  CLUSTERED (Primary Index):                                                 │
│  • Data stored WITH the index (in leaf nodes)                               │
│  • Only ONE clustered index per table                                       │
│  • Defines physical order of data                                           │
│                                                                             │
│  NON-CLUSTERED (Secondary Index):                                           │
│  • Index stores pointers to actual data                                     │
│  • Multiple secondary indexes per table                                     │
│  • Requires extra I/O to fetch actual data                                  │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Buffer Management and Caching

The buffer pool is arguably the most critical component of a disk-based storage engine.

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         BUFFER POOL ARCHITECTURE                            │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  PURPOSE: Cache frequently accessed disk pages in memory                    │
│                                                                             │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │                          BUFFER POOL                                  │  │
│  │  ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐  │  │
│  │  │Frame 0 │ │Frame 1 │ │Frame 2 │ │Frame 3 │ │Frame 4 │ │Frame N │  │  │
│  │  │────────│ │────────│ │────────│ │────────│ │────────│ │────────│  │  │
│  │  │Page 42 │ │Page 17 │ │ (free) │ │Page 99 │ │Page 3  │ │  ...   │  │  │
│  │  │[dirty] │ │[clean] │ │        │ │[pinned]│ │[clean] │ │        │  │  │
│  │  └────────┘ └────────┘ └────────┘ └────────┘ └────────┘ └────────┘  │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                                                                             │
│  PAGE TABLE (Hash map: page_id → frame_id)                                  │
│  ──────────────────────────────────────────                                 │
│  { page_42: frame_0, page_17: frame_1, page_99: frame_3, ... }              │
│                                                                             │
│  PAGE STATES                                                                │
│  ───────────                                                                │
│  • Clean: Page matches disk version                                         │
│  • Dirty: Page modified, needs write-back                                   │
│  • Pinned: Page in use, cannot be evicted                                   │
│  • Free: Frame available for new page                                       │
│                                                                             │
│  EVICTION POLICIES                                                          │
│  ─────────────────                                                          │
│                                                                             │
│  1. LRU (Least Recently Used)                                               │
│     • Evict page that hasn't been accessed longest                          │
│     • Simple but vulnerable to sequential scan pollution                    │
│                                                                             │
│  2. CLOCK (Second Chance)                                                   │
│     • Approximation of LRU with lower overhead                              │
│     • Each page has "reference bit"                                         │
│     • Clock hand sweeps, giving pages second chance                         │
│                                                                             │
│  3. LRU-K                                                                   │
│     • Track K most recent references                                        │
│     • Better resistance to sequential scans                                 │
│     • Used in modern databases (PostgreSQL, SQL Server)                     │
│                                                                             │
│  4. 2Q (Two Queues)                                                         │
│     • Hot queue (frequently accessed)                                       │
│     • Cold queue (recently added)                                           │
│     • Prevents scan pollution                                               │
│                                                                             │
│  WRITE-BACK STRATEGIES                                                      │
│  ─────────────────────                                                      │
│  • Periodic flushing (checkpoint)                                           │
│  • On eviction (when frame needed)                                          │
│  • WAL-coordinated (ensure log written first)                               │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Storage Engine Classification

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    STORAGE ENGINE TAXONOMY                                  │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  BY PRIMARY INDEX STRUCTURE                                                 │
│  ──────────────────────────                                                 │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  B-Tree Based              │  LSM-Tree Based                        │   │
│  │  ─────────────             │  ──────────────                        │   │
│  │  • InnoDB (MySQL)          │  • RocksDB                             │   │
│  │  • PostgreSQL              │  • LevelDB                             │   │
│  │  • SQLite                  │  • Cassandra                           │   │
│  │  • Oracle                  │  • HBase                               │   │
│  │  • SQL Server              │  • ScyllaDB                            │   │
│  │                            │  • FoundationDB                        │   │
│  │  Better for:               │  Better for:                           │   │
│  │  • Read-heavy workloads    │  • Write-heavy workloads               │   │
│  │  • Range queries           │  • Append-mostly data                  │   │
│  │  • Update-in-place         │  • Time-series data                    │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  BY STORAGE LOCATION                                                        │
│  ───────────────────                                                        │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  Disk-Based                │  In-Memory                             │   │
│  │  ──────────                │  ─────────                             │   │
│  │  • PostgreSQL              │  • Redis                               │   │
│  │  • MySQL                   │  • Memcached                           │   │
│  │  • RocksDB                 │  • VoltDB                              │   │
│  │  • SQLite                  │  • MemSQL                              │   │
│  │                            │  • SAP HANA                            │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  BY DATA LAYOUT                                                             │
│  ──────────────                                                             │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  Row-Oriented              │  Column-Oriented                       │   │
│  │  ────────────              │  ───────────────                       │   │
│  │  • PostgreSQL              │  • ClickHouse                          │   │
│  │  • MySQL                   │  • Apache Parquet                      │   │
│  │  • Oracle                  │  • Vertica                             │   │
│  │  • SQL Server              │  • Amazon Redshift                     │   │
│  │                            │  • DuckDB                              │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Real-World Storage Engine Examples

### PostgreSQL Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    POSTGRESQL STORAGE ARCHITECTURE                          │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  CLIENT CONNECTIONS                                                         │
│        │                                                                    │
│        ▼                                                                    │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                    POSTMASTER PROCESS                               │   │
│  │               (Connection management)                               │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│        │                                                                    │
│        ▼                                                                    │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                    BACKEND PROCESSES                                │   │
│  │    (One per connection: Parser → Planner → Executor)                │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│        │                                                                    │
│        ▼                                                                    │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                    SHARED BUFFER POOL                               │   │
│  │  • 8KB pages                                                        │   │
│  │  • Clock sweep eviction                                             │   │
│  │  • Ring buffer for sequential scans                                 │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│        │                                                                    │
│        ▼                                                                    │
│  ┌──────────────────────┐   ┌──────────────────────┐                       │
│  │     DATA FILES       │   │        WAL           │                       │
│  │  • Heap files        │   │  • 16MB segments     │                       │
│  │  • B-Tree indexes    │   │  • Synchronous write │                       │
│  │  • TOAST storage     │   │  • Streaming replic. │                       │
│  └──────────────────────┘   └──────────────────────┘                       │
│                                                                             │
│  KEY CHARACTERISTICS                                                        │
│  • MVCC with tuple versioning (no in-place updates)                         │
│  • Heap-organized tables with separate B-Tree indexes                       │
│  • VACUUM required to reclaim dead tuple space                              │
│  • Multiple storage engines planned (zheap, zedstore)                       │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### InnoDB (MySQL) Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                      INNODB STORAGE ARCHITECTURE                            │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                       BUFFER POOL                                   │   │
│  │  ┌───────────┐ ┌───────────┐ ┌───────────┐ ┌───────────┐           │   │
│  │  │Data Pages │ │Index Pages│ │Change Buf │ │ Adaptive  │           │   │
│  │  │           │ │           │ │           │ │Hash Index │           │   │
│  │  └───────────┘ └───────────┘ └───────────┘ └───────────┘           │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│        │                   │                                                │
│        ▼                   ▼                                                │
│  ┌───────────────┐   ┌───────────────┐                                     │
│  │  REDO LOG     │   │  UNDO LOG     │                                     │
│  │  (WAL)        │   │  (MVCC)       │                                     │
│  │  • Circular   │   │  • Rollback   │                                     │
│  │  • Group commit│  │  • Purge      │                                     │
│  └───────────────┘   └───────────────┘                                     │
│        │                                                                    │
│        ▼                                                                    │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                      TABLESPACE FILES                               │   │
│  │  ┌───────────────────────────────────────────────────────────────┐ │   │
│  │  │  ibdata1 (System Tablespace)                                  │ │   │
│  │  │  • Data dictionary                                            │ │   │
│  │  │  • Doublewrite buffer                                         │ │   │
│  │  │  • Undo logs (configurable)                                   │ │   │
│  │  └───────────────────────────────────────────────────────────────┘ │   │
│  │  ┌───────────────────────────────────────────────────────────────┐ │   │
│  │  │  table.ibd (File-per-table tablespaces)                       │ │   │
│  │  │  • Clustered index (data + primary key)                       │ │   │
│  │  │  • Secondary indexes                                          │ │   │
│  │  └───────────────────────────────────────────────────────────────┘ │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  KEY CHARACTERISTICS                                                        │
│  • Clustered index: Primary key determines physical order                   │
│  • Secondary indexes store primary key (not row pointer)                    │
│  • MVCC using undo log chains                                               │
│  • Doublewrite buffer for crash safety                                      │
│  • 16KB default page size                                                   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Summary: Making Storage Engine Decisions

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                 STORAGE ENGINE DECISION FRAMEWORK                           │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  QUESTION 1: What is your primary workload?                                 │
│  ───────────────────────────────────────────                                │
│  OLTP (transactions)     → Row-oriented, B-Tree based                       │
│  OLAP (analytics)        → Column-oriented                                  │
│  Mixed (HTAP)            → Hybrid solutions (TiDB, CockroachDB)             │
│                                                                             │
│  QUESTION 2: What is your read/write ratio?                                 │
│  ───────────────────────────────────────────                                │
│  Read-heavy (90%+ reads) → B-Tree, heavily indexed                          │
│  Write-heavy             → LSM-Tree (RocksDB, Cassandra)                    │
│  Balanced                → B-Tree with careful tuning                       │
│                                                                             │
│  QUESTION 3: What is your data size?                                        │
│  ─────────────────────────────────────                                      │
│  Fits in memory          → Consider in-memory database                      │
│  Exceeds memory          → Disk-based with large buffer pool                │
│  Massive (petabytes)     → Distributed storage (Cassandra, CockroachDB)     │
│                                                                             │
│  QUESTION 4: What consistency guarantees do you need?                       │
│  ─────────────────────────────────────────────────────                      │
│  Strong consistency      → Traditional RDBMS (PostgreSQL, MySQL)            │
│  Eventual consistency    → Distributed NoSQL (Cassandra, DynamoDB)          │
│  Tunable consistency     → CockroachDB, YugabyteDB                          │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## What's Next

This chapter provided the foundation for understanding database storage engines. In subsequent chapters, we'll dive deep into:

- **Chapter 2**: B-Tree fundamentals and algorithms
- **Chapter 3**: B-Tree variants and optimizations
- **Chapter 4**: Implementing B-Trees with slotted pages
- **Chapter 5**: Transaction processing and recovery
- **Chapter 7**: LSM-Trees and log-structured storage

Each chapter builds on this foundation, providing increasingly detailed knowledge of how modern databases store and retrieve data efficiently.