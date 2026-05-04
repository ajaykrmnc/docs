# Advanced Indexing — Hard Interview Questions

## Q1: B+Tree Concurrency and Latch Coupling

1. Explain latch coupling (crabbing) for concurrent B+tree access. A thread traverses from root to leaf. At
   what point can it release the latch on the parent node?
2. Describe optimistic latch coupling. Why is it more scalable than pessimistic crabbing? What happens when
   the optimistic assumption fails?
3. Explain the Blink-tree (B-link tree) design. What is the "right-link" pointer and how does it handle
   concurrent splits without holding latches on multiple levels?
4. You observe high latch contention on a B+tree's root node during a write-heavy workload. The tree has 1
   billion keys. Propose three strategies to reduce root contention.

### Expected Answer Outline

- **Latch coupling (crabbing)**: Acquire latch on child before releasing latch on parent. For reads (shared
  latches): acquire S-latch on child, release S-latch on parent. For writes (exclusive latches): acquire X-latch
  on child; if the child is "safe" (won't split or merge), release all ancestor latches. If unsafe, hold latches
  up the tree.
- **Optimistic latch coupling**: Traverse with shared latches (or no latches), only acquiring exclusive latch
  at the leaf. If the leaf operation triggers a split, restart with pessimistic approach. Works well because
  splits are rare (~1/fanout of insertions trigger a leaf split). Failure (restart) is infrequent, so overall
  throughput is higher.
- **Blink-tree**: Each node has a right-link pointer to its right sibling at the same level. During a split,
  the new node is linked before the parent pointer is updated. A concurrent traversal that lands on the wrong
  node (due to an in-progress split) follows the right-link to find the correct node. This eliminates the need
  to hold latches on multiple levels during splits.
- **Reducing root contention**: (a) Increase fanout (larger page size) to reduce tree height — fewer
  traversals touch the root. (b) Use latch-free (lock-free) index structures (e.g., Masstree). (c) Partition the
  index into multiple subtrees (partitioned B+trees). (d) Cache the root and upper levels in thread-local
  storage with version checks.

---

## Q2: LSM-Tree Compaction Strategies

1. Compare leveled compaction (LevelDB/RocksDB), tiered compaction (Cassandra), and FIFO compaction. For each,
   state the write amplification, read amplification, and space amplification in Big-O terms.
2. Explain the "write stall" problem in RocksDB. What triggers it, and how does rate limiting help?
3. Describe the "universal compaction" strategy in RocksDB. How does it differ from leveled and tiered? When
   is it appropriate?
4. You are running an LSM-tree database with 95% reads and 5% writes. The P99 read latency spikes every 30
   minutes. Diagnose the likely cause and propose a fix.

### Expected Answer Outline

- **Compaction comparison**: Leveled: write amp = O(size_ratio _ levels), read amp = O(1) per level (one
  sorted run), space amp = O(1/size_ratio). Tiered: write amp = O(levels), read amp = O(size_ratio _ levels)
  (multiple sorted runs per level), space amp = O(size_ratio) (need space for all runs). FIFO: write amp = O(1),
  read amp = O(total_runs), space amp = O(total_runs). FIFO is for TTL workloads only.
- **Write stall**: Triggered when L0 file count exceeds a threshold (too many unsorted files), or compaction
  falls behind. The write path is throttled (or blocked) to let compaction catch up. Rate limiting smooths write
  throughput to match compaction capacity, preventing sudden stalls.
- **Universal compaction**: A hybrid approach. All sorted runs are at a single "logical level." Compaction is
  triggered based on the space amplification ratio or the number of sorted runs. It tries to minimize write
  amplification while keeping space amplification bounded. Appropriate for write-heavy workloads where leveled
  compaction's write amplification is too high, but tiered's read amplification is unacceptable.
- **P99 spike diagnosis**: Compaction is the likely cause. Every ~30 minutes, a major compaction (merging
  large levels) causes I/O contention and CPU spikes. Reads compete for I/O bandwidth. Fix: (a) Rate-limit
  compaction I/O. (b) Use direct I/O for compaction to avoid polluting the OS page cache. (c) Spread compaction
  across smaller, more frequent operations. (d) Use a separate disk for compaction I/O.

---

## Q3: Bloom Filters and Probabilistic Data Structures

1. You design a Bloom filter for an LSM-tree with 10 million keys, using 10 bits per key. Calculate the false
   positive rate. How does changing to 15 bits per key affect it?
2. Explain "prefix Bloom filters" as used in RocksDB. How do they accelerate range scans while Bloom filters
   typically only support point lookups?
3. Compare Bloom filters with Cuckoo filters and Xor filters. Under what conditions does each outperform the
   others?
4. An LSM-tree has 5 levels. Each level has a Bloom filter with 1% FPR. A point lookup for a non-existent key
   must check all levels. What is the probability that at least one filter returns a false positive? How does
   this affect overall read latency?

### Expected Answer Outline

- **FPR calculation**: FPR = `(1 - e^(-k*n/m))^k` where k = optimal hash count, n = keys, m = total bits. With
  10 bits/key, optimal k ≈ 7, FPR ≈ 0.82%. With 15 bits/key, k ≈ 10, FPR ≈ 0.05%. Memory cost increases 50% but
  FPR drops ~16x.
- **Prefix Bloom filters**: Instead of hashing the full key, hash a prefix of the key (e.g., the first N
  bytes). A range scan with a known prefix (e.g., `WHERE key LIKE 'user:123:%'`) can check the filter to skip
  entire SST files that don't contain any keys with that prefix. Doesn't help for arbitrary range queries, only
  prefix-based ones.
- **Filter comparison**: Bloom: simple, fast, no deletion support, ~1.44 bits per element per unit FPR.
  Cuckoo: supports deletion, slightly higher memory per element, better cache performance (fewer memory
  accesses). Xor: static (build once, no insert/delete), most space-efficient (~1.23 bits per element per unit
  FPR), fastest lookup.
- **Multi-level FPR**: Probability of at least one false positive = `1 - (1 - 0.01)^5 = 1 - 0.99^5 ≈ 4.9%`.
  For ~5% of non-existent key lookups, the engine will perform an unnecessary I/O to read an SST block that
  doesn't contain the key. This can be mitigated with per-level FPR tuning (lower FPR for larger levels that are
  more expensive to read).

---

## Q4: Learned Indexes

1. Explain the core idea behind the "Learned Index" paper (Kraska et al., 2018). How can a neural network
   replace a B-tree index?
2. What is a Recursive Model Index (RMI)? How does it achieve sub-B-tree lookup times for read-only, static
   datasets?
3. What are the limitations of learned indexes for dynamic workloads (inserts/updates/deletes)? How do systems
   like ALEX and PGM-Index address these?
4. Compare a learned index to a B+tree for: (a) a uniformly distributed integer key, (b) a highly skewed key
   distribution, (c) string keys with common prefixes. Which performs better in each case and why?

### Expected Answer Outline

- **Core idea**: A B-tree is essentially a function that maps a key to a position in a sorted array. A model
  (e.g., linear regression, neural network) can approximate this function. The model predicts the position; a
  small local search corrects the prediction error. If the model is accurate, lookup is O(1) with small error
  correction.
- **RMI**: A hierarchy of models. The top-level model predicts which sub-model to use. Each sub-model handles
  a subset of the key range. Leaf models make the final position prediction. For a sorted, static dataset, RMI
  can achieve ~100ns lookups vs ~300ns for B-tree (due to fewer cache misses and no pointer chasing).
- **Dynamic workloads**: Pure learned indexes don't support inserts because the model assumes a static sorted
  array. ALEX uses a gapped array with in-place inserts and periodically retrains models for nodes that become
  inaccurate. PGM-Index uses a segmented approach where each segment has a simple linear model, and new segments
  are added for inserted data. Both trade some lookup performance for mutability.
- **Comparison**: (a) Uniform keys: learned index excels — a simple linear model perfectly predicts positions.
  (b) Skewed keys: learned index needs complex models for the dense region; B-tree handles skew naturally. (c)
  String keys with common prefixes: B-tree with prefix compression works well; learned indexes struggle because
  the CDF over string keys is complex and high-dimensional.

---

## Q5: Partial, Expression, and Covering Indexes

1. PostgreSQL supports partial indexes: `CREATE INDEX idx ON orders(status) WHERE status = 'pending'`. How
   does the query planner decide when to use a partial index? What happens if the query predicate is `status =
'shipped'`?
2. Explain expression indexes. Given `CREATE INDEX idx ON users(LOWER(email))`, how does PostgreSQL handle
   updates to the `email` column? What is the overhead?
3. What is a covering index (INCLUDE clause)? Given `CREATE INDEX idx ON orders(customer_id) INCLUDE (total,
created_at)`, explain why `SELECT total, created_at FROM orders WHERE customer_id = 5` can be satisfied with
   an index-only scan. What are the storage trade-offs?
4. A table has 100 million rows. 99% of queries filter by `status = 'active'` (which matches 1% of rows).
   Compare: (a) full index on `status`, (b) partial index for `status = 'active'`, (c) no index with a sequential
   scan. Analyze the storage cost, insert overhead, and query performance of each.

### Expected Answer Outline

- **Partial index usage**: The planner uses a partial index only if the query's WHERE clause logically implies
  the index's predicate. For `status = 'pending'`, the query matches the index predicate — the index is used.
  For `status = 'shipped'`, the predicate doesn't match — the index is ignored, and a sequential scan or other
  index is used.
- **Expression index updates**: On every INSERT or UPDATE of `email`, PostgreSQL computes `LOWER(email)` and
  inserts the result into the index. Overhead: extra computation (function evaluation) plus maintaining an
  additional index. The expression result is stored in the index, not the original value.
- **Covering index**: The INCLUDE columns are stored in the leaf nodes of the index but are NOT part of the
  search key (not used for ordering/searching). For the given query, all required columns (`total`,
  `created_at`) are in the index leaf. The engine doesn't need to visit the heap ("index-only scan"). Trade-off:
  larger index (more storage), wider leaf nodes (fewer entries per page, deeper tree).
- **Analysis**: (a) Full index on `status`: indexes all 100M rows, large (hundreds of MB), maintained on every
  insert/update/delete. Efficient for `status = 'active'` (1M rows). (b) Partial index: indexes only 1M rows (1%
  matching `active`). Much smaller (~1/100 of full index), lower maintenance overhead (only triggered for rows
  matching the predicate). Same query performance. (c) Sequential scan: scans 100M rows to find 1M. No storage
  overhead. Terrible query performance (~100x slower). **Partial index is clearly optimal here.**
