# Chapter 10: Batch Processing

## Table of Contents

1. [Three Types of Systems](#three-types-of-systems)
2. [The Unix Philosophy](#the-unix-philosophy)
3. [MapReduce and Distributed Filesystems](#mapreduce-and-distributed-filesystems)
4. [MapReduce Joins](#mapreduce-joins)
5. [Beyond MapReduce — Dataflow Engines](#beyond-mapreduce--dataflow-engines)
6. [Interview Questions](#interview-questions)

---

## Three Types of Systems

```
┌──────────────────────────────────────────────────────────────────┐
│              THREE TYPES OF DATA SYSTEMS                          │
├──────────────────────────────────────────────────────────────────┤
│                                                                  │
│  1. ONLINE SERVICES (OLTP):                                     │
│     Request → Response. Low latency critical.                   │
│     Measure: response time, availability.                       │
│     Examples: web servers, APIs, databases.                     │
│                                                                  │
│  2. BATCH PROCESSING:                                            │
│     Process a LARGE AMOUNT of data at once.                     │
│     Input: bounded dataset. Output: derived dataset.            │
│     Measure: throughput (records/sec or time to complete).      │
│     Examples: MapReduce, Spark, data warehouse ETL.             │
│     Runs periodically (hourly, daily).                          │
│                                                                  │
│  3. STREAM PROCESSING:                                           │
│     Process events as they arrive (near real-time).             │
│     Input: unbounded stream. Output: derived data.              │
│     Measure: latency (event-to-output delay).                   │
│     Examples: Kafka Streams, Flink, Storm.                      │
│     Runs continuously.                                          │
│                                                                  │
│  This chapter: BATCH PROCESSING.                                │
│                                                                  │
└──────────────────────────────────────────────────────────────────┘
```

---

## The Unix Philosophy

Batch processing has deep roots in Unix pipes:

```bash
cat /var/log/nginx/access.log |
  awk '{print $7}' |
  sort |
  uniq -c |
  sort -rn |
  head -5
```

This pipeline finds the 5 most-requested URLs from a web server log.

### Unix Design Principles

```
┌──────────────────────────────────────────────────────────────────┐
│              UNIX PHILOSOPHY (Doug McIlroy, 1978)                │
├──────────────────────────────────────────────────────────────────┤
│                                                                  │
│  1. Make each program do ONE THING well.                        │
│     To do a new job → build a new program.                     │
│                                                                  │
│  2. Expect OUTPUT of every program to become INPUT              │
│     to another, as yet unknown, program.                        │
│                                                                  │
│  3. Design and build software to be TRIED early.               │
│     Don't hesitate to throw away clumsy parts and rebuild.     │
│                                                                  │
│  4. Use TOOLS to lighten a programming task,                   │
│     even if you have to detour to build the tools.             │
│                                                                  │
│  KEY IDEA: A uniform interface (text files on stdin/stdout)     │
│  allows programs to be composed freely.                         │
│                                                                  │
│  MapReduce is the Unix pipe for distributed systems:            │
│  • Input: files on HDFS (not stdin)                             │
│  • Output: files on HDFS (not stdout)                           │
│  • Programs: map/reduce functions (not shell commands)          │
│                                                                  │
└──────────────────────────────────────────────────────────────────┘
```

---

## MapReduce and Distributed Filesystems

### HDFS (Hadoop Distributed File System)

```
┌──────────────────────────────────────────────────────────────────┐
│              HDFS ARCHITECTURE                                    │
├──────────────────────────────────────────────────────────────────┤
│                                                                  │
│                    ┌──────────────┐                               │
│                    │  NameNode    │  Metadata: which blocks      │
│                    │  (master)    │  are on which DataNodes       │
│                    └──────┬───────┘                               │
│                           │                                      │
│          ┌────────────────┼────────────────┐                     │
│          ▼                ▼                ▼                     │
│   ┌──────────────┐ ┌──────────────┐ ┌──────────────┐           │
│   │  DataNode 1  │ │  DataNode 2  │ │  DataNode 3  │           │
│   │ ┌────┐┌────┐ │ │ ┌────┐┌────┐ │ │ ┌────┐┌────┐ │           │
│   │ │Blk1││Blk3│ │ │ │Blk1││Blk2│ │ │ │Blk2││Blk3│ │           │
│   │ └────┘└────┘ │ │ └────┘└────┘ │ │ └────┘└────┘ │           │
│   └──────────────┘ └──────────────┘ └──────────────┘           │
│                                                                  │
│   Each file split into blocks (128MB default).                  │
│   Each block replicated on 3 DataNodes.                         │
│   Optimized for large sequential reads/writes.                  │
│   NOT good for small files or low-latency access.              │
│                                                                  │
│   Based on Google's GFS (Google File System) paper.            │
│                                                                  │
└──────────────────────────────────────────────────────────────────┘
```

### MapReduce Execution

```
┌──────────────────────────────────────────────────────────────────┐
│              MAPREDUCE EXECUTION FLOW                             │
├──────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Input (HDFS files)                                              │
│  ┌──────┐ ┌──────┐ ┌──────┐                                    │
│  │Split1│ │Split2│ │Split3│                                     │
│  └──┬───┘ └──┬───┘ └──┬───┘                                    │
│     │        │        │                                          │
│     ▼        ▼        ▼                                          │
│  ┌──────┐ ┌──────┐ ┌──────┐                                    │
│  │ MAP  │ │ MAP  │ │ MAP  │  Read input, emit (key, value)     │
│  │Task 1│ │Task 2│ │Task 3│  pairs                              │
│  └──┬───┘ └──┬───┘ └──┬───┘                                    │
│     │        │        │                                          │
│     └────────┼────────┘                                          │
│              │                                                   │
│     ┌────────┼────────┐  SHUFFLE & SORT                         │
│     │        │        │  Group all values for same key           │
│     ▼        ▼        ▼  together (network transfer!)           │
│  ┌──────┐ ┌──────┐ ┌──────┐                                    │
│  │REDUCE│ │REDUCE│ │REDUCE│  Process all values for a key      │
│  │Task 1│ │Task 2│ │Task 3│  Emit final output                  │
│  └──┬───┘ └──┬───┘ └──┬───┘                                    │
│     │        │        │                                          │
│     ▼        ▼        ▼                                          │
│  ┌──────┐ ┌──────┐ ┌──────┐                                    │
│  │Output│ │Output│ │Output│  Written to HDFS                    │
│  │File 1│ │File 2│ │File 3│                                     │
│  └──────┘ └──────┘ └──────┘                                     │
│                                                                  │
│  Key properties:                                                 │
│  • Mapper: stateless, processes one record at a time            │
│  • Shuffle: sorts by key, groups values per key                 │
│  • Reducer: receives all values for a key, outputs result       │
│  • All intermediate data written to disk (fault tolerance)      │
│                                                                  │
└──────────────────────────────────────────────────────────────────┘
```

### Fault Tolerance in MapReduce

```
┌──────────────────────────────────────────────────────────────────┐
│  MapReduce achieves fault tolerance through:                    │
│                                                                  │
│  1. DETERMINISTIC functions: If a task fails, just re-run it.  │
│     Same input → same output. No side effects.                 │
│                                                                  │
│  2. Input/output on HDFS: Data is replicated (3 copies).       │
│     If a node dies, data is still available elsewhere.          │
│                                                                  │
│  3. Intermediate data on local disk: If a map task fails,      │
│     the framework reassigns it to another node.                │
│     If a reduce task fails, upstream map output is still        │
│     available (on map node's local disk).                       │
│                                                                  │
│  4. Speculative execution: If a task is slow, the framework    │
│     launches a duplicate on another node. First to finish wins.│
│                                                                  │
│  TRADE-OFF: This materialization to disk between stages is      │
│  SLOW but makes the system very ROBUST.                         │
│                                                                  │
└──────────────────────────────────────────────────────────────────┘
```

---

## MapReduce Joins

### Sort-Merge Join (Reduce-Side Join)

```
┌──────────────────────────────────────────────────────────────────┐
│              SORT-MERGE JOIN                                      │
├──────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Join user activity logs with user profiles:                    │
│                                                                  │
│  Activity log:                    User profiles:                 │
│  ┌────────────────────────┐      ┌──────────────────┐           │
│  │ user_id=123, page=/foo │      │ id=123, name=Bob │           │
│  │ user_id=456, page=/bar │      │ id=456, name=Amy │           │
│  │ user_id=123, page=/baz │      │ id=789, name=Eve │           │
│  └────────────────────────┘      └──────────────────┘           │
│                                                                  │
│  MAP PHASE:                                                      │
│  Both datasets emit (user_id, record) pairs:                    │
│  (123, {activity: /foo})                                        │
│  (123, {activity: /baz})                                        │
│  (123, {profile: name=Bob})                                     │
│  (456, {activity: /bar})                                        │
│  (456, {profile: name=Amy})                                     │
│                                                                  │
│  SHUFFLE: Groups by user_id                                     │
│                                                                  │
│  REDUCE PHASE (for user_id=123):                                │
│  Receives: [{profile: name=Bob}, {activity: /foo},              │
│             {activity: /baz}]                                   │
│  Outputs:  (Bob, /foo) and (Bob, /baz)                          │
│                                                                  │
│  Called "sort-merge" because the shuffle sorts by key,          │
│  and the reducer merges records from both datasets.             │
│                                                                  │
└──────────────────────────────────────────────────────────────────┘
```

### Broadcast Hash Join (Map-Side Join)

```
┌──────────────────────────────────────────────────────────────────┐
│              BROADCAST HASH JOIN                                  │
├──────────────────────────────────────────────────────────────────┤
│                                                                  │
│  If one dataset is SMALL enough to fit in memory:               │
│                                                                  │
│  ┌────────────────────┐                                          │
│  │ Small dataset      │  Loaded into EVERY mapper's memory     │
│  │ (user profiles)    │  as a hash table.                       │
│  │ id→name hash map   │                                         │
│  └────────────────────┘                                          │
│           ↓ broadcasted to all mappers                           │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐             │
│  │  Mapper 1   │  │  Mapper 2   │  │  Mapper 3   │             │
│  │ Read big    │  │ Read big    │  │ Read big    │             │
│  │ dataset,    │  │ dataset,    │  │ dataset,    │             │
│  │ look up in  │  │ look up in  │  │ look up in  │             │
│  │ hash table  │  │ hash table  │  │ hash table  │             │
│  └─────────────┘  └─────────────┘  └─────────────┘             │
│                                                                  │
│  NO REDUCE PHASE needed. No shuffle. Very fast!                 │
│  But only works when one side fits in RAM.                      │
│                                                                  │
└──────────────────────────────────────────────────────────────────┘
```

### Partitioned Hash Join

```
┌──────────────────────────────────────────────────────────────────┐
│  If both datasets are PARTITIONED the same way:                 │
│                                                                  │
│  Activity partition 1 ←→ Profiles partition 1  (same user_ids) │
│  Activity partition 2 ←→ Profiles partition 2  (same user_ids) │
│                                                                  │
│  Each mapper only needs to load the CORRESPONDING partition     │
│  of the small dataset → less memory needed than broadcast.     │
│                                                                  │
└──────────────────────────────────────────────────────────────────┘
```

---

## Beyond MapReduce — Dataflow Engines

MapReduce has limitations: every stage writes to disk, chaining jobs is awkward, and it doesn't optimize across stages.

### Spark, Tez, and Flink

```
┌──────────────────────────────────────────────────────────────────┐
│              DATAFLOW ENGINES vs MAPREDUCE                        │
├──────────────────────────────────────────────────────────────────┤
│                                                                  │
│  MAPREDUCE:                                                      │
│  ┌─────┐  disk  ┌─────┐  disk  ┌─────┐  disk  ┌─────┐        │
│  │Map 1│──────►│Red 1│──────►│Map 2│──────►│Red 2│         │
│  └─────┘       └─────┘       └─────┘       └─────┘         │
│  Every stage writes to HDFS. Slow!                              │
│  Each job is independent — no cross-stage optimization.        │
│                                                                  │
│  DATAFLOW ENGINE (Spark/Tez/Flink):                             │
│  ┌─────┐       ┌──────┐       ┌──────┐       ┌──────┐         │
│  │ Op1 │──────►│ Op2  │──────►│ Op3  │──────►│ Op4  │         │
│  └─────┘ pipe  └──────┘ pipe  └──────┘ pipe  └──────┘         │
│  Intermediate data kept in MEMORY or local disk.                │
│  Entire pipeline optimized as a single DAG.                     │
│                                                                  │
│  ADVANTAGES:                                                     │
│  • No unnecessary disk writes between stages                   │
│  • Operators generalized (not just map + reduce)               │
│  • Optimizer can reorder and combine operations                 │
│  • Much faster (10-100x for iterative algorithms)              │
│                                                                  │
│  TRADE-OFF:                                                      │
│  • If a node fails mid-pipeline, may need to recompute         │
│    from the beginning (no intermediate HDFS checkpoint)         │
│  • Spark mitigates with RDD lineage (recompute lost partition) │
│                                                                  │
└──────────────────────────────────────────────────────────────────┘
```

### Comparison

| Feature | MapReduce | Spark | Flink |
|---------|-----------|-------|-------|
| **Model** | Map → Shuffle → Reduce | DAG of operators | DAG of operators |
| **Intermediate data** | Always HDFS | In-memory (spill to disk) | In-memory / pipelined |
| **Fault tolerance** | Re-run failed task | Recompute from RDD lineage | Checkpoint + replay |
| **Iteration** | Chain multiple jobs | In-memory iterative | Native iteration |
| **Latency** | High (disk I/O) | Low (in-memory) | Very low |
| **Streaming** | No | Micro-batching | True streaming |

---

## Interview Questions

### Q1: How does MapReduce achieve fault tolerance?

MapReduce functions (map, reduce) are **deterministic** — same input always produces same output. All input/output goes through HDFS (replicated). If a map task fails, the framework simply reruns it on another node using the same input split from HDFS. If a reduce task fails, it's rerun — map outputs are still available on the map nodes' local disks. Slow tasks are handled with **speculative execution**: a duplicate task is run on another node, and whichever finishes first wins. The cost is materializing all intermediate data to disk, which is slow but robust.

### Q2: Explain the three types of joins in MapReduce.

1. **Sort-merge join (reduce-side)**: Both datasets are mapped to emit (join_key, record) pairs. The shuffle sorts and groups by key. The reducer receives all records for each key from both datasets and performs the join. Works for any size datasets but requires a full shuffle.
2. **Broadcast hash join (map-side)**: The small dataset is loaded into every mapper's memory as a hash table. Each mapper reads the large dataset and looks up the join key in the hash table. No shuffle needed — very fast, but the small dataset must fit in RAM.
3. **Partitioned hash join**: Both datasets are pre-partitioned by the join key. Each mapper loads only the corresponding partition of the small dataset. Requires less memory than broadcast.

### Q3: Why is Spark faster than MapReduce?

Spark keeps intermediate data **in memory** instead of writing to HDFS between stages. It models the entire computation as a **DAG of operators** (not just map and reduce), allowing the optimizer to pipeline operations and avoid unnecessary materializations. For iterative algorithms (machine learning, graph processing) that reuse the same dataset, Spark can keep it cached in memory across iterations — MapReduce would re-read from disk each time. Spark is typically 10-100x faster for iterative workloads.

### Q4: What is the Unix philosophy and how does MapReduce relate to it?

The Unix philosophy (Doug McIlroy): make each program do one thing well, design programs to work together, use a uniform interface (text streams). Unix pipes compose small programs into powerful pipelines. MapReduce is the distributed equivalent: map/reduce functions are composable processing steps, HDFS files are the "pipes" between stages, and the framework handles distribution, fault tolerance, and scheduling. The key difference: MapReduce operates on massive datasets across clusters, while Unix pipes run on a single machine.

### Q5: What are the limitations of MapReduce that led to dataflow engines like Spark?

(1) **Disk materialization**: Every intermediate result is written to HDFS — huge I/O overhead. (2) **Rigid two-phase model**: Only map and reduce — complex workflows require chaining multiple MapReduce jobs with intermediate HDFS files. (3) **No pipeline optimization**: Each job is independent; the framework can't optimize across job boundaries. (4) **No iteration support**: Iterative algorithms (ML training) must re-read data from disk each iteration. (5) **High latency**: Startup overhead per job makes small, interactive queries impractical.

---

*Based on Chapter 10 of "Designing Data-Intensive Applications" by Martin Kleppmann*
