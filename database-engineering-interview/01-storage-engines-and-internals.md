# Storage Engines & Internals — Hard Interview Questions

## Q1: B-Tree vs LSM-Tree Trade-offs Under Write Amplification

**Question:** Explain write amplification in both B-tree and LSM-tree storage engines. Under what workload
characteristics does each engine's write amplification become pathological? How does RocksDB's leveled
compaction vs universal compaction strategy affect write amplification differently?

**Expected Answer:**

**B-Tree Write Amplification:**

- Every page modification requires writing an entire page (typically 4KB-16KB) even for a single byte change
- WAL + dirty page flush = at minimum 2x write amplification
- Page splits cause cascading writes up the tree
- Random I/O pattern makes each write expensive on spinning disks
- Typical write amplification: 10x-30x depending on page size and fill factor

**LSM-Tree Write Amplification:**

- Sequential writes to memtable are cheap, but compaction is the hidden cost
- In leveled compaction (RocksDB default): each level is ~10x larger. A key-value pair may be rewritten once
  per level, yielding write amplification of ~10 \* number_of_levels (often 30-50x for large datasets)
- In universal compaction: sorts all sorted runs into one, write amplification is lower
  (~number_of_sorted_runs) but space amplification is much higher (up to 2x)
- Pathological case for LSM: large values with small keys — compaction rewrites the full value each time

**When each becomes pathological:**

- B-Tree: heavy random insert workloads with poor locality, page splits dominate
- LSM-Tree: update-heavy workloads on large datasets with leveled compaction, or when compaction cannot keep
  up with ingestion rate (write stalls)

---

## Q2: Buffer Pool Management — Clock vs LRU-K

**Question:** PostgreSQL uses a clock-sweep algorithm for buffer pool eviction while SQL Server uses LRU-K
(specifically LRU-2). Explain the fundamental difference in their eviction decisions. When does clock-sweep
fail compared to LRU-K, and why did PostgreSQL choose it anyway? How would you handle a sequential scan
flooding the buffer pool in each system?

**Expected Answer:**

**Clock-Sweep (PostgreSQL):**

- Circular buffer with a "usage count" per page (not a timestamp)
- Sweep hand decrements usage count; evicts when count reaches 0
- Simple, O(1) amortized, minimal contention on the eviction data structure
- Approximation of LRU — does not distinguish frequency from recency precisely

**LRU-K (SQL Server):**

- Tracks the last K (typically K=2) access timestamps per page
- Eviction priority: page whose Kth-most-recent access is oldest
- Naturally distinguishes "scanned once" from "accessed repeatedly" — a page accessed only once has its
  2nd-most-recent access at -infinity, making it first to evict
- Higher overhead: requires maintaining per-page timestamp history

**When clock-sweep fails:**

- Sequential scan of a large table inflates usage counts of pages that will never be re-read, evicting
  genuinely hot pages
- PostgreSQL mitigates this with the **ring buffer** strategy: large sequential scans get a small private ring
  buffer (~256KB) instead of polluting the shared buffer pool

**SQL Server's approach:**

- LRU-2 naturally handles this: sequentially scanned pages have only one access, so their "backward
  K-distance" is infinite and they're evicted first without any special case

**Why PostgreSQL chose clock-sweep:**

- Simplicity and low contention; maintaining sorted LRU-K structures under high concurrency requires expensive
  synchronization
- The ring buffer mitigation is good enough in practice

---

## Q3: Slotted Page Layout and TOAST

**Question:** Describe the slotted page layout used by most row-oriented databases. What happens when a
variable-length row update causes the row to no longer fit in its original page? Compare how PostgreSQL (HOT
updates, TOAST) and InnoDB (off-page columns, overflow pages) handle this differently. What is the consequence
for the index in each case?

**Expected Answer:**

**Slotted Page Layout:**

- Page header contains a slot array (line pointers) growing from the front
- Actual tuples are stored from the back of the page, growing toward the front
- Free space is in the middle; slot array maps slot_number -> (offset, length)
- Allows tuples to be rearranged within a page without changing external references (slot number stays the
  same)

**PostgreSQL HOT (Heap-Only Tuples):**

- If the updated row still fits on the same page AND no indexed columns changed, PostgreSQL creates a new
  tuple version on the same page and chains it from the original line pointer
- No index update required — indexes still point to the original line pointer, which follows the chain
- If the row doesn't fit or indexed columns changed: a full update with new index entries is required

**PostgreSQL TOAST:**

- Columns exceeding ~2KB are compressed and/or stored out-of-line in a separate TOAST table
- TOAST pointer (18 bytes) replaces the value in the main tuple
- Four strategies: PLAIN, EXTERNAL, EXTENDED, MAIN — controlling compression and out-of-line behavior

**InnoDB Off-Page Storage:**

- For DYNAMIC/COMPRESSED row formats: variable-length columns exceeding the page's capacity are stored in
  overflow pages
- A 20-byte pointer is left in the primary row
- COMPACT format stores the first 768 bytes inline + overflow pointer

**Index Consequences:**

- PostgreSQL: HOT avoids index bloat but only works under specific conditions; non-HOT updates create dead
  index entries requiring VACUUM
- InnoDB: clustered index means the row IS the index leaf; secondary indexes store the primary key, so row
  movement in the clustered index doesn't affect secondary indexes (they just look up the PK again)

---

## Q4: Columnar Storage and Vectorized Execution

**Question:** Explain the difference between the Volcano/iterator model of query execution and vectorized
execution. Why do columnar storage formats (like Parquet or Arrow) enable vectorized execution but
row-oriented formats do not? What specific CPU-level optimizations does vectorized execution exploit, and what
are its limitations?

**Expected Answer:**

**Volcano (Iterator) Model:**

- Each operator implements `next()` returning one tuple at a time
- Function call overhead per tuple: virtual dispatch, branch misprediction at each operator boundary
- Poor CPU cache utilization — touching many columns when only a few are needed
- Dominant model in traditional RDBMS (PostgreSQL, MySQL)

**Vectorized Execution:**

- Operators process a batch (vector) of values at a time (typically 1024-4096 values)
- Amortizes function call overhead across the batch
- Enables SIMD (Single Instruction Multiple Data) operations on the batch
- Tight inner loops over homogeneous data types → CPU branch predictor is happy, prefetcher works well

**Why Columnar Enables This:**

- All values of a column stored contiguously in memory → one cache line contains many values of the same
  column
- Homogeneous data type per column → SIMD works naturally (e.g., AVX-512 can compare 16 int32 values in one
  instruction)
- Better compression ratios (similar values adjacent → delta/RLE encoding effective)
- Dictionary encoding allows operations on encoded values without decompression

**Row-oriented limitation:**

- Values of different columns interleaved in memory
- Processing column `A` requires loading entire rows, wasting cache lines on columns B, C, D...
- Heterogeneous types in a cache line prevent SIMD

**Limitations of Vectorized Execution:**

- Point lookups and OLTP workloads don't benefit (batch size of 1)
- Complex expressions with many branches reduce SIMD effectiveness
- Materialization cost: if many columns needed, columnar requires stitching them back together
- Late materialization helps but adds complexity

---

## Q5: WAL Internals and Group Commit

**Question:** Describe the exact sequence of operations when a transaction commits in a WAL-based system. What
is the "WAL write bottleneck" and how does group commit solve it? Explain why PostgreSQL's `commit_delay` and
InnoDB's `innodb_flush_log_at_trx_commit` represent fundamentally different approaches to the same problem.
What is the difference between `fsync`, `fdatasync`, and `O_DIRECT`, and why does the choice matter for WAL
durability?

**Expected Answer:**

**Commit Sequence:**

1. Transaction writes its modifications as WAL records to the WAL buffer (in-memory)
2. At commit: WAL records up to this transaction's LSN must be flushed to durable storage
3. `write()` to WAL file → data goes to OS page cache
4. `fsync()` / `fdatasync()` → forces OS to flush to disk controller
5. Only after fsync returns successfully: commit is acknowledged to client
6. Dirty data pages can be flushed to disk lazily (checkpoint)

**WAL Write Bottleneck:**

- fsync is expensive (~1-10ms on SSD, much worse on HDD)
- One fsync per commit = throughput limited to ~100-1000 commits/sec
- The disk is often idle between fsyncs

**Group Commit:**

- Multiple concurrent transactions accumulate WAL records
- A single fsync flushes all accumulated records at once
- Throughput scales with concurrency: 100 concurrent commits sharing one fsync = 100x effective throughput

**PostgreSQL `commit_delay`:**

- After a transaction is ready to flush, it waits up to `commit_delay` microseconds for other transactions to
  join the group
- Only the "group leader" (first to arrive) pays the delay; followers piggyback
- Trades latency for throughput — adds artificial delay to increase batch size

**InnoDB `innodb_flush_log_at_trx_commit`:**

- Value 1: fsync on every commit (durable, default)
- Value 2: write to OS cache on commit, fsync once per second (survives MySQL crash, not OS crash)
- Value 0: no write/fsync on commit, handled by background thread (fastest, least durable)
- This is a durability-vs-performance knob, not a batching strategy

**fsync vs fdatasync vs O_DIRECT:**

- `fsync()`: flushes file data AND metadata (size, timestamps) — two disk writes if metadata changed
- `fdatasync()`: flushes file data and only metadata needed for data integrity (size, not timestamps) — avoids
  one disk write when file size didn't change
- `O_DIRECT`: bypasses OS page cache entirely, writes directly to disk controller cache — avoids
  double-buffering but loses OS caching benefits; still needs fsync to ensure disk controller cache is flushed
- PostgreSQL defaults to `fdatasync` on Linux for WAL; InnoDB uses `fsync` by default but supports `O_DIRECT`
  for data files

---

## Q6: SSTable and Bloom Filter Sizing

**Question:** In an LSM-tree engine, you have 1 billion keys uniformly distributed across 7 levels with a size
ratio of 10. Calculate the worst-case read amplification for a point lookup without bloom filters. Now, given
a total memory budget of 2GB for bloom filters, how would you optimally distribute bits across levels to
minimize the expected I/O cost per lookup? Why is it suboptimal to give each level the same false-positive
rate?

**Expected Answer:**

**Without Bloom Filters — Worst Case:**

- Level 0: may have multiple overlapping sorted runs (say 4)
- Levels 1-6: one sorted run per level, non-overlapping within level
- For a point lookup: must check each level in worst case
- Each level check = binary search within the sorted run = one I/O per level (assuming index blocks cached)
- Worst case: 4 (L0) + 6 (L1-L6) = **10 I/O operations**

**Optimal Bloom Filter Distribution:**

- Key insight: the cost of a false positive at each level is 1 I/O, but the probability of reaching each level
  differs
- For a negative lookup (key doesn't exist): must check ALL levels
- Each level's bloom filter has false positive rate `f_i`, and checking level i costs 1 I/O
- Expected I/O cost = sum of `f_i` across all levels (for negative lookups, which dominate)

**Why uniform FPR is suboptimal:**

- A bloom filter's FPR is `(1/2)^(bits_per_key * ln2)`
- Reducing FPR from 1% to 0.1% at one level costs ~3.3 extra bits per key
- At lower levels, there are exponentially more keys (10x per level)
- Spending bits at the largest level "buys" less FPR reduction per bit because there are so many keys
- The **Monkey** optimization: assign FPR proportional to the size of the level — give smaller levels lower
  FPR (cheaper in total bits) and tolerate higher FPR at large levels
- Optimal allocation: `f_i = total_false_positive_budget * (size_i / total_size)`
- With 2GB budget: allocate bits per key inversely proportional to level size, achieving ~10 bits/key at large
  levels and ~20+ at small levels

---

## Q7: Copy-on-Write B-Trees (LMDB / Bw-Tree)

**Question:** Explain how LMDB implements a copy-on-write B-tree without a WAL. What are the trade-offs
compared to an in-place-update B-tree with WAL? How does the Bw-tree (used in SQL Server Hekaton and Azure
Cosmos) achieve latch-free operations, and what problem does its "delta chain" solve?

**Expected Answer:**

**LMDB Copy-on-Write B-Tree:**

- Never modifies existing pages; every write creates new versions of modified pages
- Path from modified leaf to root is copied: modification cascades up as each parent must point to the new
  child page
- Two root pointers (meta pages) alternate: current transaction reads from one root, writer creates new tree
  rooted at the other
- Commit = single atomic write of the new meta page (pointing to new root)
- No WAL needed: either the new meta page is written (committed) or it isn't (aborted); old tree is still
  intact
- Readers never block writers and vice versa — MVCC via dual roots

**Trade-offs vs WAL-based:**

- Advantages: crash recovery is instant (no WAL replay), simpler code, readers are truly zero-copy (mmap)
- Disadvantages: write amplification is higher (entire root-to-leaf path copied per modification),
  fragmentation over time, single-writer limitation (can't have concurrent writers)
- Free space management is complex: must track which pages belong to which snapshot

**Bw-Tree:**

- Latch-free B-tree using CAS (Compare-and-Swap) operations instead of locks
- **Delta chains:** instead of modifying a page in place, prepend a "delta record" describing the change to
  the page's delta chain
- Page lookup: follow the mapping table → delta chain head → apply deltas to reconstruct current page state
- **Mapping table:** indirection layer that maps logical page IDs to physical addresses; CAS on the mapping
  table entry to install new delta chain head
- Consolidation: when delta chain grows too long, create a new consolidated page and CAS the mapping table
  entry

**Problems delta chains solve:**

- Avoid latching: multiple threads can append deltas using CAS without locks
- Avoid full page writes for small modifications
- But: long delta chains degrade read performance (must traverse chain), requiring periodic consolidation
-
