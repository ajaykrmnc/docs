# Query Optimization & Execution Plans — Hard Interview Questions

## Q1: Cost-Based Optimizer Cardinality Estimation Failures

**Question:** Cardinality estimation is often called the "Achilles' heel" of query optimization. Explain what
happens when a cost-based optimizer dramatically misestimates the cardinality of an intermediate join result.
Give three specific scenarios where traditional histogram-based cardinality estimation fails, and describe
what modern systems (e.g., adaptive query execution in Spark, PostgreSQL's JIT recompilation) do to mitigate
this.

**Expected Answer:**

**Impact of misestimation:**

- Optimizer chooses physical operators based on estimated cardinalities
- Underestimate → nested loop join chosen when hash join was appropriate; memory grant too small causing
  spills to disk
- Overestimate → hash join with excessive memory reservation; unnecessary parallelism overhead
- Wrong join order: for N tables, there are N! possible orderings; wrong cardinalities lead to joining large
  intermediates early

**Three failure scenarios:**

1. **Correlated columns (attribute independence assumption):**
   - Optimizer assumes `P(city='NYC' AND state='NY') = P(city='NYC') * P(state='NY')`
   - Actual selectivity is much higher because city and state are correlated
   - Multi-column statistics help but are rarely maintained for all combinations

2. **Join cardinality with skewed data:**
   - Uniform distribution assumption: `|R ⋈ S| = |R| * |S| / max(V(R.a), V(S.a))`
   - Fails badly with skewed foreign key distributions (power-law/Zipf)
   - A few hot keys produce far more join results than estimated

3. **Chained predicates after complex expressions:**
   - `WHERE f(x) > 10 AND g(y) < 5` — optimizer has no histogram for `f(x)` or `g(y)`
   - Falls back to "magic numbers" (e.g., 1/3 selectivity for range, 1/10 for equality on unknown)
   - After one bad estimate propagates through multiple operators, final estimate can be off by orders of
     magnitude

**Mitigations:**

- **Adaptive Query Execution (Spark 3.0+):** mid-execution re-optimization; after a shuffle, actual row counts
  are known; can change join strategy (sort-merge → broadcast), coalesce/split partitions
- **PostgreSQL adaptive approaches:** `pg_statistic` extended statistics (CREATE STATISTICS for multi-column
  dependencies), JIT compilation for expression evaluation (not re-optimization per se)
- **SQL Server Intelligent Query Processing:** interleaved execution (materializes a subquery, uses actual
  cardinality for outer query planning), adaptive joins (runtime switch between nested loop and hash based on
  actual input size)
- **LEO (Learning Optimizer, DB2):** monitors actual vs estimated cardinalities and feeds corrections back
  into future optimizations

---

## Q2: Join Algorithms — Hash Join Variants

**Question:** Explain the difference between a simple (in-memory) hash join, a grace hash join, and a hybrid
hash join. Under what memory conditions does each variant activate? Derive the I/O cost of a grace hash join
for relations R (with B_R pages) and S (with B_S pages) given M pages of memory. What is a "hash join
build-side spill" and how does it affect performance on modern column stores?

**Expected Answer:**

**Simple Hash Join:**

- Build phase: load entire smaller relation into an in-memory hash table
- Probe phase: scan larger relation, probe hash table for matches
- Requirement: smaller relation fits in memory (B_R ≤ M)
- I/O cost: B_R + B_S (one pass over each relation)

**Grace Hash Join:**

- When neither relation fits in memory
- Partition phase: hash both R and S into k partitions using the same hash function; write partitions to disk
- Join phase: for each partition pair (R_i, S_i), load the smaller into memory and probe with the other
- Requirement: each partition of the smaller relation fits in memory, so k ≥ B_R / M, typically k = M - 1
- I/O cost: 3 \* (B_R + B_S) — one pass to partition (read + write both), one pass to join

**Hybrid Hash Join:**

- Optimization of grace hash join when memory is slightly larger than one partition
- Keep "partition 0" of R in memory during the partitioning phase (don't write it to disk)
- Probe records from S that hash to partition 0 are joined immediately (also not written to disk)
- Remaining partitions are handled like grace hash join
- I/O cost: between simple and grace — saves 2 \* (B_R/k + B_S/k) I/O for the in-memory partition

**I/O Cost Derivation for Grace Hash Join:**

- Partitioning R: read B_R + write B_R
- Partitioning S: read B_S + write B_S
- Joining: read B_R + B_S (each partition read once)
- Total: 3(B_R + B_S)
- Assumes no partition overflow; if a partition exceeds memory → recursive partitioning adds another 2x I/O
  for that partition

**Build-side spill in column stores:**

- Column stores process data in compressed columnar batches
- Build-side spill means hash table exceeds memory, must partition and flush to disk
- Disrupts the vectorized pipeline: materialized rows must be written row-wise (or in mini-batches) and
  re-read
- Decompression/recompression overhead during spill
- Partition-wise processing loses cache locality benefits of sequential columnar scans

---

## Q3: Query Optimization for Correlated Subqueries

**Question:** Consider: `SELECT * FROM orders o WHERE o.total > (SELECT AVG(total) FROM orders o2 WHERE
o2.customer_id = o.customer_id)`. Explain why naively executing this correlated subquery is O(N^2). Describe
the "magic decorrelation" technique. How does the optimizer transform this into a join-based plan, and what
are the edge cases where decorrelation changes semantics?

**Expected Answer:**

**Naive execution — O(N^2):**

- For each row in `orders`, execute the subquery with that row's `customer_id`
- Subquery scans `orders` again with a filter
- N outer rows \* average N/k inner scan = O(N^2/k) ≈ O(N^2) for low cardinality customer_id

**Magic Decorrelation:**
The optimizer rewrites the correlated subquery into an uncorrelated form:

```sql
-- Step 1: Compute the aggregate separately
WITH customer_avg AS (
SELECT customer_id, AVG(total) as avg_total
FROM orders
GROUP BY customer_id
)
-- Step 2: Join back
SELECT o.*
FROM orders o
JOIN customer_avg ca ON o.customer_id = ca.customer_id
WHERE o.total > ca.avg_total
```

**Transformation steps:**

1. Identify the correlation variable (`o.customer_id`)
2. Pull the subquery out, grouping by the correlation variable
3. Replace the correlated scalar subquery with a join on the correlation variable
4. Move the comparison predicate to the WHERE clause of the join

**Edge cases where semantics change:**

1. **NULL handling:** If `customer_id` is NULL, the correlated subquery returns NULL for the comparison (which
   becomes UNKNOWN/false). A join with `ON o.customer_id = ca.customer_id` also won't match NULLs (correct), BUT
   if transformed to an outer join, NULL-handling may differ.

2. **Empty groups:** If a customer has only one order, `AVG(total) = total`, so the predicate `total > avg` is
   false. The correlated subquery correctly returns no rows for such customers. The join-based plan must also
   produce the same result — inner join naturally does this.

3. **COUNT vs other aggregates:** `COUNT(*)` returns 0 for empty sets, but a missing join match produces NULL.
   Decorrelating a `COUNT` subquery requires a LEFT JOIN + COALESCE(count, 0) to preserve semantics.

4. **EXISTS subqueries:** Decorrelating EXISTS into a semi-join is straightforward, but NOT EXISTS → anti-join
   must handle NULLs in the join key correctly (three-valued logic).

---

## Q4: Parallel Query Execution — Exchange Operators

**Question:** Explain the Volcano/Exchange operator model for parallel query execution. What are the three
types of exchange operators (gather, repartition, broadcast), and when is each used? What is the "skew
problem" in parallel hash joins, and how do systems like Presto/Trino handle it? What is "bushy parallelism"
vs "pipeline parallelism"?

**Expected Answer:**

**Exchange Operators (Volcano Model):**

- An Exchange operator is inserted into the query plan to redistribute data between parallel worker
  threads/processes
- Each worker executes a copy of the plan fragment below the exchange
- The exchange handles data routing between producers and consumers

**Three types:**

1. **Gather (N:1):** Collects results from multiple workers into a single stream. Used at the top of the plan
   to return results to the coordinator. May perform merge if input is sorted.

2. **Repartition (N:N):** Redistributes data by hash/range across workers. Used before a hash join or group-by
   to ensure matching keys land on the same worker. Each producer sends each tuple to the worker determined by
   hash(join_key) % num_workers.

3. **Broadcast (1:N or N:N with replication):** Sends a complete copy of the data to every worker. Used when
   one side of a join is small enough that replicating it is cheaper than repartitioning both sides.

**Skew Problem in Parallel Hash Joins:**

- After repartitioning by join key, a few hot keys may cause one worker to receive disproportionate data
- That worker becomes the bottleneck: builds a huge hash table, runs much longer than others
- All other workers finish and wait → resource waste

**Presto/Trino skew handling:**

- Skew detection during planning using statistics
- For known-skewed keys: broadcast the build side for those keys while hash-partitioning the rest
- Dynamic repartitioning: detect skew at runtime and split hot partitions further
- Spill-to-disk for workers that exceed memory

**Bushy vs Pipeline Parallelism:**

- **Pipeline parallelism:** operators in a pipeline run concurrently; a hash join's build and the next
  operator's probe overlap in time. Limited by the longest pipeline stage.
- **Bushy parallelism:** independent subtrees of the query plan execute simultaneously on different workers.
  E.g., in `(A ⋈ B) ⋈ (C ⋈ D)`, the two sub-joins run in parallel, then their results are joined. Exploits
  independent computation but requires materializing intermediate results.

---

## Q5: Query Plan Stability and Plan Regression

**Question:** A customer reports that a query that used to take 50ms now takes 30 seconds after a routine
`ANALYZE`/statistics update. Explain the root cause category. What is "plan regression" and why is it a harder
problem than it appears? Describe three approaches to preventing plan regression: plan guides/hints, plan
baselines (SQL Server SPM, Oracle SQL Plan Management), and parametric query optimization.

**Expected Answer:**

**Root Cause:**

- Updated statistics changed cardinality estimates
- Optimizer chose a different plan: possibly switched from index seek + nested loop to sequential scan + hash
  join (or vice versa)
- The new plan is optimal for the new estimated cardinalities but worse for the actual data distribution
- This is "plan regression": a plan change that degrades performance despite the optimizer believing it found
  a better plan

**Why plan regression is hard:**

- The optimizer is doing its job correctly given its cost model and statistics
- You can't just "keep the old plan" — sometimes the new plan IS better
- Plan quality depends on parameter values, data distribution, cache state, concurrent load
- A plan that's optimal for one parameter binding may be terrible for another (parameter sensitivity /
  "parameter sniffing")

**Three approaches:**

1. **Plan Guides / Hints:**
   - Force specific physical operators or join orders via query hints (e.g., `USE INDEX`, `LEADING`,
     `HASH_JOIN`)
   - Pros: immediate fix, full control
   - Cons: brittle — hints don't adapt to data changes; requires manual maintenance; violates the principle of
     declarative SQL
   - Used as emergency fixes, not long-term solutions

2. **Plan Baselines (SQL Server SPM, Oracle SPM):**
   - Capture known-good execution plans as "baselines"
   - When optimizer finds a new plan, it's only adopted if it's **verified** to be at least as good as the
     baseline (via test execution or comparison)
   - Oracle SQL Plan Management: plans move from "unaccepted" → "accepted" only after validation
   - SQL Server Query Store: identifies regressed queries and allows forcing a previous plan
   - Pros: automatic, data-driven, adapts over time
   - Cons: verification overhead, storage of plan history, may block genuinely better plans

3. **Parametric Query Optimization (PQO):**
   - Pre-compile multiple plans for different parameter ranges
   - At runtime, choose the best plan based on actual parameter values
   - SQL Server "optimize for unknown" + parameter-sensitive plan optimization (PSPO in SQL Server 2022):
     identifies parameter-sensitive queries and caches multiple plans
   - Pros: addresses parameter sniffing directly
   - Cons: increased plan cache usage, complexity in determining parameter range boundaries

---

## Q6: Materialized View Selection Problem

**Question:** Given a data warehouse workload of 200 queries, how would you decide which materialized views to
create? Formalize this as an optimization problem. Why is it NP-hard? Describe the lattice framework for
materialized view selection and explain the greedy algorithm with its approximation guarantees. How do modern
systems like BigQuery, Redshift, or Snowflake handle automated materialized view selection?

**Expected Answer:**

**Formalization:**

- Given: a set of queries Q = {q1, ..., q200}, each with a frequency, a storage budget S
- A materialized view V can answer one or more queries (if V contains all the data the query needs)
- Each view has a maintenance cost (update on base table changes) and a storage cost
- Objective: select a set of views to minimize total query processing time subject to storage ≤ S and
  acceptable maintenance cost
- This is a variant of the **weighted set cover problem**, which is NP-hard

**Lattice Framework (Harinarayan et al. 1996):**

- Model the space of possible group-bys as a lattice
- Each node represents an aggregate at a certain granularity (e.g., by (product, region, date) vs by (product,
  region))
- Edges represent "can be computed from" relationships (a finer granularity can compute coarser)
- Materializing a node benefits all queries that can be answered from it
- The "benefit" of materializing a view = sum of (cost_without_view - cost_with_view) \* frequency for all
  benefiting queries

**Greedy Algorithm:**

1. Start with the full base table materialized (must always be available)
2. In each iteration, select the view with the highest benefit-per-unit-storage
3. Update benefits of remaining views (some queries are already served by selected views)
4. Repeat until storage budget exhausted

- Approximation guarantee: greedy achieves at least (1 - 1/e) ≈ 63% of optimal benefit (submodularity of the
  benefit function)

**Modern Systems:**

- **BigQuery:** Automatic materialized views — system observes query patterns, suggests views, transparently
  rewrites queries to use them
- **Redshift:** Automatic materialized views (AutoMV) — monitors workload, creates/drops views based on
  cost-benefit analysis, handles refresh automatically
- **Snowflake:** Manual materialized views with automatic maintenance; the system doesn't auto-select but does
  auto-refresh
- Common pattern: workload analysis → candidate generation → cost-benefit filtering → creation → transparent
  query rewrite → periodic garbage collection of unused views
