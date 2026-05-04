# Indexing Deep Dive — Hard Interview Questions

## Q1: B+Tree Internal Structure and Concurrency

**Question:** Explain the difference between a B-tree and a B+tree and why databases universally use B+trees
for disk-based indexes. Describe the "crabbing" (lock coupling) protocol for concurrent B+tree access. What is
the Blink-tree optimization, and how does it reduce lock contention? What are the implications of
variable-length keys on B+tree node fan-out and how do prefix-compressed keys work?

**Expected Answer:**

**B-tree vs B+tree:**

- B-tree: data (or pointers to data) stored in BOTH internal nodes and leaf nodes
- B+tree: data stored ONLY in leaf nodes; internal nodes contain only keys and child pointers
- B+tree advantages for databases:
  - Higher fan-out in internal nodes (no data, so more keys fit per node) → shallower tree → fewer I/Os
  - Leaf nodes linked in a doubly-linked list → efficient range scans (just follow pointers)
  - All searches go to leaf level → more predictable I/O cost
  - Easier to cache internal nodes (they're smaller and fewer)

**Crabbing (Lock Coupling) Protocol:**

- To traverse the tree safely under concurrent modifications:
  1.  Lock the root node
  2.  Lock the child node
  3.  Release the parent lock IF the child is "safe" (won't split or merge due to this operation)
  4.  A node is "safe" if: for inserts, it's not full; for deletes, it's more than half full
  5.  Continue down, releasing ancestors as safe nodes are found
- Worst case: hold locks from root to leaf (if every node on the path might split)
- This serializes access at the root for split-heavy workloads → bottleneck

**Blink-Tree Optimization (Lehman & Yao):**

- Add a "right link" pointer in each node, pointing to its right sibling at the same level
- If you arrive at a node and it's been split (the key you're looking for is beyond this node's range), follow
  the right link to the new sibling
- **Key benefit:** you only need to hold one latch at a time (no lock coupling needed for reads)
- Writers still need to hold latches during split, but splits are local: split the node, then update the
  parent (which might also need splitting)
- Used by PostgreSQL's nbtree implementation

**Variable-Length Keys:**

- Variable-length keys (e.g., VARCHAR) reduce fan-out unpredictably
- A node that fits 100 integer keys might fit only 20 varchar keys
- Lower fan-out → taller tree → more I/Os

**Prefix Compression:**

- In a sorted B+tree, adjacent keys often share long prefixes (e.g., URLs, paths)
- Store the full key only for the first entry; subsequent entries store only the differing suffix
- Reduces space → higher effective fan-out
- Variations:
  - **Prefix truncation in internal nodes:** internal nodes only need to separate children, so they can store
    the shortest distinguishing prefix (e.g., "Smith" vs "Snyder" → separator can be "Sn" instead of "Snyder")
  - **Front compression:** store shared prefix once per node, then deltas

---

## Q2: Hash Index, Extendible Hashing, and Linear Hashing

**Question:** Explain why most databases support B+tree indexes by default but only some support hash indexes.
What are the exact operations where hash indexes win, and where do they lose? Describe extendible hashing and
linear hashing — how each handles bucket overflow and grows. Why did PostgreSQL not support persistent hash
indexes until version 10, and what changed?

**Expected Answer:**

**Hash Indexes — When They Win:**

- O(1) average-case for exact-match lookups (vs O(log N) for B+tree)
- Point queries on high-cardinality columns: hash index is theoretically faster
- No key ordering overhead

**When Hash Indexes Lose:**

- No range queries (`>`, `<`, `BETWEEN`) — hash destroys ordering
- No prefix matching (`LIKE 'abc%'`)
- No index-only scans on sorted results (`ORDER BY`)
- No multi-column prefix searches (can't use hash(a,b) for queries on just `a`)
- Concurrency and recovery are harder (B+trees have well-studied concurrent algorithms)
- B+trees are "good enough" for point queries (3-4 I/Os for a billion rows)

**Extendible Hashing:**

- Uses a directory (array of pointers) and buckets
- **Global depth** d: the directory has 2^d entries
- **Local depth** d_i: the number of bits used by bucket i
- On overflow: if local depth < global depth, split the bucket and redistribute (no directory growth). If
  local depth = global depth, double the directory (2^d → 2^(d+1)), then split the bucket
- Directory doubling is O(2^d) but doesn't move data — just pointer updates
- Good for in-memory or when directory fits in memory

**Linear Hashing:**

- No directory — uses a split pointer
- Grows one bucket at a time (linear growth, not doubling)
- **Round-robin splitting:** maintain a split pointer `p` starting at 0; when ANY bucket overflows, split
  bucket `p` (not the overflowing bucket!) and increment `p`
- Use two hash functions: h_0(key) = key % N and h_1(key) = key % 2N
- If h_0(key) < p → use h_1(key) (that bucket has been split); else use h_0(key)
- When p reaches N, reset p=0, N=2N, advance to next round
- Overflowing bucket uses overflow chains until it's split
- Advantage: no directory, graceful growth
- Disadvantage: overflowing bucket may wait a long time for its split; overflow chains degrade performance

**PostgreSQL Hash Indexes:**

- Pre-v10: hash indexes were NOT WAL-logged → not crash-safe (no recovery possible)
- Required full index rebuild after crash — made them impractical for production
- PostgreSQL 10: added WAL support for hash indexes → crash-safe
- Still limited: no support for unique constraints via hash indexes, no index-only scans
- Community recommendation: B+tree is almost always preferred unless proven otherwise

---

## Q3: Covering Indexes, Index-Only Scans, and Include Columns

**Question:** Explain the concept of a covering index and why it eliminates random I/O to the heap. What is
the "visibility map" optimization in PostgreSQL for index-only scans, and why is it necessary? Compare the
`INCLUDE` clause (PostgreSQL 11+, SQL Server) with simply adding columns to the index key. Describe the
trade-offs of wide covering indexes on write performance, index size, and maintenance.

**Expected Answer:**

**Covering Index:**

- An index that contains ALL columns needed by a query — no heap/table lookup required
- Query can be answered entirely from the index → "index-only scan"
- Eliminates random I/O to the heap (which is the dominant cost of non-covering index scans)
- Example: `CREATE INDEX idx ON orders(customer_id, order_date, total)` covers `SELECT total FROM orders WHERE
customer_id = 5 AND order_date > '2024-01-01'`

**PostgreSQL Visibility Map:**

- PostgreSQL's MVCC stores all tuple versions in the heap
- Even with a covering index, PostgreSQL must check if the tuple is visible to the current transaction
- **Problem:** the index doesn't contain visibility information (xmin, xmax) — normally requires a heap fetch
  to check
- **Visibility map:** a bitmap with one bit per heap page. Bit = 1 means ALL tuples on that page are visible
  to all transactions (all-frozen or all-visible)
- If the visibility map bit is set for a page, the index-only scan can skip the heap fetch — the tuple is
  guaranteed visible
- If the bit is NOT set (page has recently-modified tuples), a heap fetch is required even for index-only
  scans
- VACUUM sets the visibility map bits → freshly-vacuumed tables get better index-only scan performance

**INCLUDE vs Key Columns:**

- `CREATE INDEX idx ON orders(customer_id) INCLUDE (total, order_date)`
- **Key columns:** included in the B+tree's sort order; used for search, ordering, and uniqueness
- **INCLUDE columns:** stored only in leaf nodes; NOT part of the sort order; NOT used for search
- Differences:
  1.  INCLUDE columns don't increase internal node size → fan-out preserved → tree stays shallow
  2.  INCLUDE columns can't be used for range predicates or ORDER BY
  3.  INCLUDE columns can be types that don't have a B-tree operator class (e.g., JSON)
  4.  Unique index with INCLUDE: uniqueness enforced only on key columns, but INCLUDE columns are available for
      covering

**Trade-offs of Wide Covering Indexes:**

- **Write performance:** every INSERT/UPDATE/DELETE must update the index → more columns = more data written
  per modification
- **Index size:** larger indexes = more disk, more memory for caching, more I/O for maintenance operations
- **HOT updates (PostgreSQL):** if ANY indexed column is modified, a HOT update is impossible → wider indexes
  make HOT less likely
- **Maintenance:** larger indexes take longer to VACUUM, REINDEX, and rebuild
- **Rule of thumb:** include columns that are frequently queried together but rarely updated

---

## Q4: Partial Indexes, Expression Indexes, and GIN/GiST

**Question:** Explain partial indexes (filtered indexes) and give a scenario where they dramatically
outperform a full index. Describe expression indexes and their impact on the optimizer. Compare GIN
(Generalized Inverted Index) and GiST (Generalized Search Tree) — their internal structure, supported
operations, and performance characteristics. When would you choose one over the other for full-text search,
JSONB queries, and PostGIS spatial queries?

**Expected Answer:**

**Partial Indexes:**

- Index only a subset of rows, defined by a WHERE predicate
- `CREATE INDEX idx ON orders(created_at) WHERE status = 'pending'`
- If only 1% of orders are 'pending', this index is ~100x smaller than a full index
- Benefits: smaller index = faster scans, less memory, faster maintenance, less write amplification
- Optimizer uses partial indexes only when the query's WHERE clause implies the index predicate

**Dramatic Improvement Scenario:**

- Table `events` with 10 billion rows, column `processed BOOLEAN`
- At any time, only ~10,000 rows have `processed = false`
- Full index on `processed`: 10B entries, huge
- Partial index: `CREATE INDEX ON events(id) WHERE processed = false` — 10K entries
- Queue-like access pattern: `SELECT * FROM events WHERE processed = false ORDER BY id LIMIT 100`

**Expression Indexes:**

- Index on a computed expression: `CREATE INDEX ON users(lower(email))`
- The optimizer matches the expression in the query to the index expression
- `WHERE lower(email) = 'foo@bar.com'` → uses the index
- `WHERE email = 'foo@bar.com'` → does NOT use the index (different expression)
- The indexed expression must be immutable (deterministic)
- Internally: the expression value is computed and stored in the index at INSERT/UPDATE time

**GIN (Generalized Inverted Index):**

- Internal structure: B-tree of keys, where each key maps to a posting list (sorted list of row IDs)
- Optimized for "contains" queries: which rows contain a given value?
- Supported types: arrays (`@>`), full-text search (`@@`), JSONB (`@>`, `?`, `?|`, `?&`), trigrams
- Performance:
  - Exact match/containment lookups: very fast (direct posting list lookup)
  - Build time: slow (must decompose values into keys, build posting lists)
  - Update: slow (pending list technique: new entries go to an unsorted "pending" list, merged into main index
    lazily)
  - Size: can be large (each element of an array/document generates an index entry)

**GiST (Generalized Search Tree):**

- Internal structure: balanced tree where internal nodes contain bounding predicates (e.g., bounding boxes)
- Supports "nearest neighbor" and "overlap" queries, not just containment
- Supported types: geometric types, PostGIS spatial, ranges, full-text search (with less precision than GIN),
  ltree
- Performance:
  - Insert: faster than GIN (single tree traversal, no posting lists)
  - Lookup: slower than GIN for exact containment (may need to traverse multiple subtrees due to overlapping
    bounding boxes)
  - Size: typically smaller than GIN
  - KNN (K-Nearest Neighbor): native support via `ORDER BY <-> point`

**When to Choose Which:**
| Use Case | GIN | GiST |
|----------|-----|------|
| Full-text search (high query volume, rare updates) | Preferred — exact match on terms | Acceptable for lower
volume; supports phrase proximity |
| JSONB containment queries | Preferred — fast posting list lookup | Not typically used |
| PostGIS spatial queries | Not suitable | Preferred — bounding box hierarchy, supports KNN |
| Range types (overlaps, contains) | Supported but GiST may be better | Preferred for complex range operations
|
| Frequently updated data | Worse (pending list overhead) | Better (simple tree update) |

---

## Q5: Index Selection and the Index Merging Problem

**Question:** A table has 50 million rows and 20 columns. The application runs 15 distinct query patterns.
Describe a systematic approach to determine the optimal set of indexes. What is the "index interaction"
problem (where adding one index makes another less useful)? Explain bitmap index scan and how PostgreSQL
combines multiple indexes via BitmapAnd/BitmapOr. When is a multi-column index superior to combining
single-column indexes?

**Expected Answer:**

**Systematic Index Selection Approach:**

1. **Workload Analysis:**
   - Collect all query patterns with their frequencies and importance (SLA weight)
   - For each query: identify columns in WHERE, JOIN ON, ORDER BY, GROUP BY, SELECT
   - Classify access patterns: point lookup, range scan, prefix match, sort

2. **Candidate Generation:**
   - For each query: what index would make it optimal?
   - Consider column order in multi-column indexes (most selective / equality predicates first, then range,
     then sort)
   - Consider covering indexes for high-frequency read-only queries

3. **Cost-Benefit Analysis:**
   - For each candidate index: estimate read benefit (queries sped up _ frequency) and write cost
     (INSERT/UPDATE/DELETE penalty _ write frequency)
   - Net benefit = read benefit - write cost - storage cost
   - Diminishing returns: each additional index provides less marginal benefit

4. **Pruning and Consolidation:**
   - Merge indexes where possible: if one index is a prefix of another, the shorter one is redundant
   - E.g., `(a, b, c)` makes `(a)` and `(a, b)` redundant for search (but not for covering)
   - Check: do any queries ONLY need `(a)` for ordering? If yes, the prefix of `(a, b, c)` still works

**Index Interaction Problem:**

- Adding index I1 changes the optimizer's cost estimates, potentially making index I2 less used
- E.g., index on `(status)` and index on `(date)`: for `WHERE status = 'active' AND date > X`, the optimizer
  may choose one or the other, but not benefit from both via simple index scan
- Adding a composite `(status, date)` makes both single-column indexes less valuable for this query
- The "interaction" means optimal index selection requires considering the full set holistically, not greedily

**Bitmap Index Scan (PostgreSQL):**

- Used to combine results from multiple indexes
- Process: each index scan produces a bitmap (bit per heap page or per row)
- BitmapAnd: intersection of bitmaps (both conditions must match)
- BitmapOr: union of bitmaps (either condition matches)
- After bitmap construction: scan the heap in physical page order (sequential I/O, not random)
- Lossy bitmaps: when too many rows, bitmap becomes per-page (not per-row) → recheck needed on the heap

**When Multi-Column Index > Combined Single-Column:**

1. **Highly selective compound predicate:** `WHERE a = 5 AND b = 10` — composite `(a, b)` goes directly to the
   matching leaf; bitmap merge requires two separate scans + AND
2. **Range + Equality:** `WHERE a = 5 AND b > 100` — composite `(a, b)` does one range scan in the B+tree;
   single-column indexes can't navigate this efficiently
3. **ORDER BY:** `WHERE a = 5 ORDER BY b` — composite `(a, b)` returns results already sorted; single-column
   index on `a` requires a sort step
4. **Index-only scan:** composite index can cover multiple columns; combining single-column indexes still
   requires heap access for non-indexed columns

**When Bitmap Merge > Composite:**

- Many ad-hoc query combinations on different column subsets
- Can't afford to create composite indexes for every combination
- Low selectivity per column but high selectivity when combined
