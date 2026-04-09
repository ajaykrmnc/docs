# Distributed Databases — Hard Interview Questions

## Q1: Raft vs Multi-Paxos in Practice

**Question:** Compare Raft and Multi-Paxos consensus protocols at a detailed level. What specific
simplifications does Raft make compared to Multi-Paxos, and what performance do those simplifications cost?
Explain how leader election works differently in each. Why does CockroachDB use Raft while Google Spanner uses
Paxos? Describe the "joint consensus" approach to membership changes in Raft and why it was later simplified
to single-server changes.

**Expected Answer:**

**Multi-Paxos:**

- Separates leader election (Phase 1) from log replication (Phase 2)
- After a leader is established, only Phase 2 (Accept) messages are needed for each log entry — one round trip
- Allows "holes" in the log — entries can be committed out of order, filled in later
- Leader can be implicit (any node that completed Phase 1 most recently); multiple nodes may believe they're
  leader simultaneously (dueling proposers), which is safe but reduces throughput
- Configuration changes via Paxos on a configuration log

**Raft Simplifications:**

1. **Sequential log with no holes:** entries must be committed in order; a leader won't commit entry N+1 until
   entry N is committed. This simplifies log management but limits parallelism.
2. **Strong leader:** only the leader can accept client requests and append entries. Log entries flow only
   from leader to followers (never the reverse).
3. **Leader election via term numbers:** each election starts a new "term"; candidate must have the most
   up-to-date log to win (log comparison check). Eliminates the possibility of an out-of-date leader overwriting
   committed entries.
4. **Randomized election timeouts:** prevents split votes from becoming persistent (unlike Paxos which can
   livelock with dueling proposers without external help).

**Performance Costs of Raft's Simplifications:**

- No out-of-order commits: can't pipeline independent entries as aggressively as Multi-Paxos
- Strong leader: all traffic goes through one node, creating a bottleneck; Multi-Paxos can distribute
  leadership across entries
- Sequential commit: higher latency under concurrent requests compared to Multi-Paxos which can batch and
  commit entries in parallel

**Why CockroachDB uses Raft:**

- Each range (partition) has its own Raft group — parallelism comes from many groups, not within one group
- Raft's simplicity reduces engineering complexity for a startup-scale team
- The strong leader aligns well with CockroachDB's leaseholder model

**Why Spanner uses Paxos:**

- Spanner's workload requires high throughput per Paxos group
- Multi-Paxos allows pipelining multiple writes within a group
- Google has extensive Paxos expertise and infrastructure (Chubby, Megastore)

**Joint Consensus (Raft Membership Changes):**

- Original Raft: membership changes via a two-phase approach:
  1. Enter "joint consensus" mode: both old and new configurations must agree
  2. Switch to new configuration
- Joint consensus requires majority of OLD config AND majority of NEW config to agree on every decision during
  transition
- **Simplified to single-server changes:** add/remove one server at a time; this guarantees that old and new
  configurations always overlap in a majority, so no explicit joint consensus is needed
- The simplification works because any single-server change preserves the quorum overlap property

---

## Q2: Google Spanner's TrueTime and External Consistency

**Question:** Explain how Google Spanner achieves external consistency (also called strict serializability or
linearizability of transactions) across globally distributed datacenters. What is TrueTime, and why is the
bounded clock uncertainty critical? Walk through the commit protocol for a read-write transaction. What
happens during the "commit wait" period, and why can't you eliminate it? How does CockroachDB approximate this
without atomic clocks?

**Expected Answer:**

**External Consistency:**

- If transaction T1 commits before transaction T2 starts (in real time), then T1's commit timestamp < T2's
  commit timestamp
- This means the transaction ordering matches real-world causality — stronger than serializability

**TrueTime:**

- API: `TT.now()` returns an interval `[earliest, latest]` guaranteed to contain the true current time
- Backed by GPS receivers and atomic clocks in each datacenter
- Uncertainty ε is typically 1-7ms (average ~4ms)
- Key guarantee: if `TT.now()` returns `[t - ε, t + ε]`, the true time is definitely within that interval

**Read-Write Transaction Commit Protocol:**

1. Client sends writes to the Paxos leader of each involved partition
2. If multi-partition: two-phase commit (2PC) coordinated by one partition's leader
3. Coordinator leader chooses commit timestamp `s`:
   - `s ≥ TT.now().latest` (must be after the current time upper bound)
   - `s ≥` any prepare timestamps from participants
   - `s >` any previously assigned timestamps from this leader
4. **Commit wait:** leader waits until `TT.now().earliest > s` (i.e., waits until it's certain that real time
   has passed `s`)
5. Only then: apply the commit and make it visible

**Why commit wait is necessary:**

- Without commit wait, there's a window where the commit timestamp `s` might actually be in the future (due to
  clock uncertainty)
- Another transaction T2 starting at a different datacenter might get a start timestamp < s (if its clock is
  slightly ahead), violating external consistency
- Commit wait ensures: by the time the commit is visible, the true time has definitely passed `s`, so any
  subsequently starting transaction will get a timestamp > s
- Commit wait duration = 2ε (typically ~7-14ms) — this is the direct cost of clock uncertainty

**Why you can't eliminate commit wait:**

- Without perfect clock synchronization, there's always uncertainty
- The wait is proportional to uncertainty — reducing ε (better clocks) reduces wait
- Eliminating ε = 0 requires perfect clocks, which don't exist

**CockroachDB Without Atomic Clocks:**

- Uses NTP-synchronized clocks with much higher uncertainty (100-250ms typical)
- If commit wait were used, it would add 200-500ms latency — unacceptable
- Instead: CockroachDB uses a combination of:
  1. **Uncertainty intervals:** each transaction has an uncertainty window. If a read encounters a value with
     a timestamp within its uncertainty window, it restarts at a higher timestamp
  2. **Clock skew detection:** nodes compare clocks via gossip; transactions are aborted if clock skew exceeds
     the configured maximum (default 500ms)
  3. **Causal ordering through Lamport-like timestamps:** piggybacked on RPCs
- Trade-off: CockroachDB's external consistency guarantee is weaker — it's linearizable assuming clock skew
  stays within bounds, but violations are possible under extreme clock drift

---

## Q3: Distributed Transaction Protocols — 2PC, 3PC, and Percolator

**Question:** Explain why two-phase commit (2PC) is a blocking protocol. What specific failure scenario causes
blocking, and how does the coordinator's failure affect participants? Why doesn't three-phase commit (3PC)
solve the problem in practice? Describe Google Percolator's transaction model and how it achieves distributed
transactions without a centralized coordinator using a timestamp oracle and lock columns in Bigtable.

**Expected Answer:**

**2PC Blocking Scenario:**

1. Phase 1: Coordinator sends PREPARE; all participants respond YES
2. Coordinator crashes after receiving all YES votes but BEFORE sending COMMIT/ABORT
3. Participants are stuck: they voted YES (promised to commit if told to) but don't know the decision
4. They can't abort (coordinator might have decided COMMIT and told others)
5. They can't commit (coordinator might have decided ABORT)
6. They hold locks and wait indefinitely until coordinator recovers — **blocking**

**Why 3PC Doesn't Work in Practice:**

- 3PC adds a PRE-COMMIT phase between PREPARE and COMMIT
- After PRE-COMMIT: participants know the decision is COMMIT, so if coordinator crashes, they can commit
  independently
- **The fundamental issue:** 3PC assumes reliable failure detection — it requires distinguishing a crashed
  node from a slow/partitioned node
- In asynchronous networks (real networks), you cannot reliably distinguish crash from delay (FLP
  impossibility)
- A network partition during 3PC can cause split-brain: one partition commits, another aborts
- 3PC is correct only in synchronous systems with bounded message delays — which real networks aren't

**Percolator Transaction Model:**

- Designed for incremental processing at Google, runs on top of Bigtable
- No centralized transaction coordinator — uses Bigtable's single-row transactional guarantees

**Key components:**

1. **Timestamp Oracle (TSO):** centralized service that issues strictly increasing timestamps. Each
   transaction gets a `start_ts` and a `commit_ts`.
2. **Lock column, Data column, Write column:** each row in Bigtable has these extra columns managed by
   Percolator

**Protocol:**

1. **Prewrite phase:**
   - Choose a "primary" key (one of the keys being written)
   - For each key: write the value to the data column at `start_ts`, AND write a lock pointing to the primary
     key
   - If any key is already locked by another transaction → conflict, abort
   - Primary key is written first (if primary lock fails, transaction aborts)

2. **Commit phase:**
   - Write to the "write" column of the primary key at `commit_ts`, pointing to `start_ts` (this makes the
     write visible)
   - Remove the lock on the primary key
   - This is the **commit point** — a single Bigtable row operation (atomic)
   - Asynchronously: write the "write" column and remove locks for secondary keys

**Crash Recovery:**

- If a transaction crashes during prewrite: other transactions encountering its locks check if the primary
  lock exists. If primary lock is missing → the transaction either committed or aborted; check the write column
  of the primary key to decide
- If primary lock still exists and the transaction has timed out: clean up (rollback) by removing the lock
- No blocking: participants are never stuck waiting for a coordinator

---

## Q4: Consistent Hashing and Virtual Nodes

**Question:** Explain consistent hashing and why it's used in distributed databases like Cassandra and
DynamoDB. What problem does it solve compared to simple modular hashing? Describe the "hot spot" problem with
basic consistent hashing and how virtual nodes (vnodes) address it. What are the trade-offs of vnodes vs
range-based partitioning (as used in CockroachDB/Spanner)? How does rebalancing work when a node joins or
leaves?

**Expected Answer:**

**Consistent Hashing:**

- Map both keys and nodes onto a circular hash space (ring) using a hash function
- Each key is assigned to the first node encountered clockwise from the key's position on the ring
- When a node joins/leaves: only keys between the new/departing node and its predecessor are affected
- **Key advantage:** only ~1/N of keys need to move (where N = number of nodes), vs modular hashing where
  almost all keys need remapping

**vs Modular Hashing:**

- `hash(key) % N` — adding/removing a node changes N, causing nearly all keys to remap
- Consistent hashing: adding a node only moves keys from one neighbor, O(K/N) keys instead of O(K)

**Hot Spot Problem:**

- With few physical nodes, the ring is unevenly divided
- Some nodes own much larger arc segments than others → load imbalance
- A popular key range landing on one node creates a hot spot
- E.g., with 3 nodes, one might own 50% of the ring

**Virtual Nodes (Vnodes):**

- Each physical node is represented by many virtual nodes (e.g., 256) on the ring
- Virtual nodes are spread across the ring, so each physical node owns many small non-contiguous segments
- Result: much more uniform distribution — each physical node owns approximately 1/N of the ring
- Fine-grained rebalancing: can move individual vnodes between physical nodes

**Vnodes vs Range-Based Partitioning:**

_Vnodes (Cassandra, DynamoDB):_

- Pros: automatic load balancing, simple rebalancing (move vnodes)
- Cons: range queries are expensive (data for a key range is scattered across many nodes), more metadata to
  track
- Recovery: when a node dies, its vnodes are distributed among all remaining nodes — fast parallel recovery

_Range-Based (CockroachDB, Spanner, HBase):_

- Pros: range queries are efficient (contiguous key ranges on one node), simpler for ordered data
- Cons: requires explicit range splitting/merging; hot ranges need manual or automatic splitting
- Rebalancing: split a range in half, move one half to another node; or merge small ranges

**Rebalancing on Join/Leave:**

_Join (vnodes):_

- New node gets a set of vnodes; for each vnode, the previous owner transfers the corresponding key range
- Multiple predecessors transfer in parallel → fast

_Leave (vnodes):_

- Departing node's vnodes are redistributed to remaining nodes
- Each remaining node takes a few vnodes — load is spread evenly

---

## Q5: CAP Theorem Nuances and PACELC

**Question:** Most explanations of the CAP theorem are oversimplified. Explain precisely what CAP actually
says (Gilbert and Lynch's formal proof). Why is it misleading to say you "choose 2 of 3"? What is the
difference between CAP consistency and ACID consistency? Explain the PACELC framework and categorize the
following systems: Cassandra, DynamoDB, CockroachDB, Spanner, MongoDB, PostgreSQL.

**Expected Answer:**

**What CAP Actually Says (Gilbert & Lynch 2002):**

- In a distributed system subject to network partitions, it is impossible to simultaneously guarantee:
  - **Consistency:** every read receives the most recent write (linearizability)
  - **Availability:** every non-failing node returns a response for every request
  - **Partition tolerance:** the system continues to operate despite arbitrary message loss between nodes
- The formal proof shows: during a network partition, a write on one side cannot be known on the other side,
  so the other side must either return stale data (sacrificing C) or not respond (sacrificing A)

**Why "Choose 2 of 3" Is Misleading:**

- Partition tolerance is not optional — network partitions WILL happen in distributed systems
- The real choice is: during a partition, do you sacrifice C or A?
- When there's no partition (normal operation), you CAN have both C and A
- CAP is about the behavior **during failures**, not during normal operation
- "CA systems" in CAP terms are just single-node databases — they avoid partitions by not being distributed

**CAP Consistency vs ACID Consistency:**

- CAP consistency = **linearizability** (a specific agreement on read/write ordering across replicas)
- ACID consistency = **application-level invariants** (constraints, triggers, referential integrity)
- Completely different concepts sharing the same word
- A system can be CAP-consistent but ACID-inconsistent (linearizable reads but no constraints) and vice versa

**PACELC Framework:**

- Extends CAP: "If there is a Partition, choose between Availability and Consistency; Else (normal operation),
  choose between Latency and Consistency"
- PA/EL: during partition → available; normally → low latency (sacrifice consistency)
- PC/EC: during partition → consistent; normally → consistent (sacrifice latency)
- PA/EC and PC/EL are also possible

**System Classification:**

| System          | During Partition                                                                       | Normal Operation                                  | PACELC |
| --------------- | -------------------------------------------------------------------------------------- | ------------------------------------------------- | ------ |
| **Cassandra**   | Availability (tunable, but defaults to AP)                                             | Low Latency (eventual consistency)                | PA/EL  |
| **DynamoDB**    | Availability (eventually consistent reads default)                                     | Low Latency (eventual consistent)                 |
| PA/EL           |
| **CockroachDB** | Consistency (refuses writes to minority partition)                                     | Consistency (serializable, Raft                   |
| consensus)      | PC/EC                                                                                  |
| **Spanner**     | Consistency (Paxos majority required)                                                  | Consistency (external consistency, TrueTime wait) |
| PC/EC           |
| **MongoDB**     | Default PA (can be configured PC with majority writes)                                 | Default EL (can be EC with majority               |
| read concern)   | PA/EL default, configurable                                                            |
| **PostgreSQL**  | Not distributed by default; with streaming replication: consistency (primary failure = |
| downtime)       | Consistency (single node ACID)                                                         | PC/EC (when extended with sync replication)       |

---

## Q6: Distributed Joins and Data Shuffling

**Question:** You need to join two large tables (each ~1TB) that are hash-partitioned on different keys in a
distributed database. What are your options? Calculate the network cost for each approach. Explain the concept
of "colocation" and how systems like CockroachDB, YugabyteDB, and Citus handle colocated joins. What is a
"broadcast join" threshold, and how do you determine it?

**Expected Answer:**

**The Problem:**

- Table A hash-partitioned on `A.id` across N nodes
- Table B hash-partitioned on `B.name` across N nodes
- Join: `A JOIN B ON A.customer_id = B.customer_id`
- Neither table is partitioned on the join key → data is not colocated

**Options:**

1. **Repartition Both Tables (Shuffle Join):**
   - Hash-repartition both A and B by `customer_id` across all nodes
   - Each node then performs a local join on its partition
   - Network cost: all data from both tables may need to move = ~2TB transferred
   - Actual: each row has 1/N probability of being on the right node already, so ~(N-1)/N \* 2TB ≈ 2TB for
     large N

2. **Repartition One Table (Directed Join):**
   - If one table is much smaller, repartition only the smaller one to match the larger one's partitioning
   - If B is 100GB and A is 1TB: repartition B by `customer_id` = ~100GB transferred
   - Still requires A to be repartitioned too unless A is already partitioned by `customer_id`

3. **Broadcast Join:**
   - Send a complete copy of the smaller table to every node
   - Each node joins its local partition of the larger table with the complete smaller table
   - Network cost: (N-1) \* size_of_small_table (sent to N-1 nodes)
   - For 100GB small table, 10 nodes: 900GB — worse than repartitioning!
   - For 1GB small table, 10 nodes: 9GB — much better

**Broadcast Join Threshold:**

- Broadcast is cheaper when: `(N-1) * |small| < |small| + |large| * (N-1)/N`
  - Simplified: `|small| < |large| / (N-1)` approximately
  - Typical threshold: broadcast when small table < a few hundred MB (configurable)
  - Systems like Spark use `spark.sql.autoBroadcastJoinThreshold` (default 10MB)

**Colocation:**

- Partition related tables by the same key, so joins on that key are always local
- **CockroachDB:** interleaved tables (deprecated) / co-partitioning by family
- **YugabyteDB:** colocated tables feature — tables in the same colocated group are stored on the same tablet
  (partition)
- **Citus:** distributed tables can be colocated by choosing the same distribution column; reference tables
  are automatically replicated to all nodes (implicit broadcast)
- **Trade-off:** colocation optimizes joins on one key but may create hot spots and prevents optimal
  partitioning for other access patterns
