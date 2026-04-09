# Chapter 2: Data Models and Query Languages

## Table of Contents

1. [The Importance of Data Models](#the-importance-of-data-models)
2. [Relational Model](#relational-model)
3. [Document Model](#document-model)
4. [Relational vs Document Today](#relational-vs-document-today)
5. [Graph-Like Data Models](#graph-like-data-models)
6. [Query Languages](#query-languages)
7. [MapReduce Querying](#mapreduce-querying)
8. [Interview Questions](#interview-questions)

---

## The Importance of Data Models

Data models are the **most important** part of developing software. They affect not only how the software is written, but also how we **think about the problem** we are solving.

```
┌─────────────────────────────────────────────────────────────────┐
│                    LAYERS OF DATA MODELS                        │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Layer 1:  Application developer models the real world          │
│            ──► Objects, data structures, APIs                   │
│                                                                 │
│  Layer 2:  Store those data structures                           │
│            ──► JSON, XML, tables, graphs                        │
│                                                                 │
│  Layer 3:  Database engineers represent JSON/tables              │
│            ──► Bytes in memory, on disk, on network             │
│                                                                 │
│  Layer 4:  Hardware engineers represent bytes                    │
│            ──► Electrical currents, magnetic fields, photons    │
│                                                                 │
│  Each layer HIDES the complexity of the layers below it         │
│  through a clean data model (abstraction).                      │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## Relational Model

Proposed by **Edgar Codd** in 1970. Data is organized into **relations** (tables), where each relation is an unordered collection of **tuples** (rows).

### The Dominance of Relational Databases

```
Timeline of Database Models:
─────────────────────────────────────────────────────────────────

1960s-70s  │  Hierarchical Model (IMS) ──── Tree structure
           │  Network Model (CODASYL)  ──── Graph with manual pointers
           │
1970       │  Relational Model (Codd)  ──── Tables with SQL
           │  ↓ Won because:
           │  • Query optimizer handles access paths
           │  • Declarative (WHAT not HOW)
           │  • Simpler programming model
           │
1980s-2000s│  Relational dominance (Oracle, MySQL, PostgreSQL)
           │  Object-relational attempted (failed to take over)
           │  XML databases attempted (niche use)
           │
2010s+     │  NoSQL movement ──── Document + Graph models
           │  Polyglot persistence (use the right DB for the job)
```

### The Object-Relational Mismatch (Impedance Mismatch)

Most application development is done in object-oriented languages, creating an awkward translation layer between objects and relational tables:

```
┌──────────────────────────────────────────────────────────────────┐
│              IMPEDANCE MISMATCH EXAMPLE: LinkedIn Profile        │
├──────────────────────────────────────────────────────────────────┤
│                                                                  │
│  In-Memory Object:                  In Relational Tables:        │
│  ─────────────────                  ─────────────────────        │
│                                                                  │
│  {                                  users                        │
│    name: "Bill Gates",              ┌────┬───────────┐           │
│    positions: [                     │ id │ name      │           │
│      {title: "Co-chair",           │  1 │ Bill Gates│           │
│       org: "Gates Foundation"},     └────┴───────────┘           │
│      {title: "Co-founder",                                      │
│       org: "Microsoft"}            positions                     │
│    ],                               ┌────┬────────┬──────────┐  │
│    education: [                     │user│ title  │ org      │  │
│      {school: "Harvard",           │  1 │Co-chair│Gates Fdn │  │
│       year: 1973}                   │  1 │Co-found│Microsoft │  │
│    ],                               └────┴────────┴──────────┘  │
│    contact: {                                                    │
│      twitter: "@BillGates",        education                     │
│      blog: "gatesnotes.com"        ┌────┬────────┬──────┐       │
│    }                                │user│ school │ year │       │
│  }                                  │  1 │Harvard │ 1973 │       │
│                                     └────┴────────┴──────┘       │
│                                                                  │
│  ONE object ──► MULTIPLE tables with foreign keys                │
│  This mismatch requires an ORM layer (Hibernate, ActiveRecord)   │
│                                                                  │
└──────────────────────────────────────────────────────────────────┘
```

**Solutions to impedance mismatch**:
1. **ORM frameworks** (Hibernate, SQLAlchemy) — reduce boilerplate but don't eliminate mismatch
2. **JSON/XML columns** in SQL (PostgreSQL JSONB, MySQL JSON)
3. **Document databases** — store the object as-is

### Many-to-One and Many-to-Many Relationships

```
┌─────────────────────────────────────────────────────────────────┐
│          WHY NORMALIZE? (Many-to-One Relationships)             │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  WITHOUT normalization (denormalized):                           │
│  ┌───────────────────────────────────────┐                      │
│  │ User: region = "Greater Seattle Area" │  ← String duplicated │
│  │ User: region = "Greater Seattle Area" │    in every row      │
│  │ User: region = "Greater Seatle Area"  │  ← Typo possible!   │
│  └───────────────────────────────────────┘                      │
│                                                                 │
│  WITH normalization (use IDs):                                  │
│  ┌────────────────────┐    ┌────────────────────────────┐      │
│  │ User: region_id=42 │───►│ Region 42: Greater Seattle │      │
│  │ User: region_id=42 │───►│           Area             │      │
│  │ User: region_id=42 │───►│                            │      │
│  └────────────────────┘    └────────────────────────────┘      │
│                                                                 │
│  Benefits of normalization:                                     │
│  • Consistent style and spelling                                │
│  • Easy to update (change in one place)                         │
│  • Better internationalization (localization by ID)             │
│  • Better search (ID → structured data)                         │
│                                                                 │
│  Cost: Need JOINS to resolve IDs back to human-readable text    │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## Document Model

Document databases (MongoDB, CouchDB, RethinkDB) store data as self-contained **documents** (usually JSON):

### Advantages of the Document Model

| Advantage | Explanation |
|-----------|-------------|
| **Schema flexibility** | No rigid schema; each document can have different fields |
| **Data locality** | Entire document stored together; one read fetches everything |
| **Closer to application objects** | Less impedance mismatch with OOP code |
| **Better for 1:many (tree-structured)** | Nested structures fit naturally |

### Disadvantages of the Document Model

| Disadvantage | Explanation |
|-------------|-------------|
| **Poor for many-to-many** | No joins; must denormalize or do application-level joins |
| **Data duplication** | Denormalization leads to inconsistency risks |
| **Can't reference nested items** | Hard to say "the second item in user X's positions list" |
| **Large documents** | Loading the whole document when you only need a small part is wasteful |

---

## Relational vs Document Today

### Schema-on-Read vs Schema-on-Write

```
┌─────────────────────────────────────────────────────────────────┐
│                                                                 │
│  SCHEMA-ON-WRITE (Relational)       SCHEMA-ON-READ (Document)  │
│  ─────────────────────────          ─────────────────────────   │
│                                                                 │
│  Schema enforced at WRITE time      Schema interpreted at       │
│  (like static typing)               READ time (like dynamic    │
│                                     typing)                     │
│                                                                 │
│  ALTER TABLE users                  // Just start writing       │
│    ADD COLUMN email VARCHAR(255);   // documents with email     │
│  UPDATE users SET email = '...'     // field. Handle missing    │
│    WHERE ...;                       // fields in app code.      │
│                                                                 │
│  ✓ Data integrity guaranteed        ✓ Flexible, no migrations  │
│  ✓ Clear data documentation         ✓ Heterogeneous data OK    │
│  ✗ ALTER TABLE can be slow          ✗ No guarantee of structure │
│  ✗ Schema migrations painful        ✗ Bugs hide in bad data    │
│                                                                 │
│  BEST WHEN:                         BEST WHEN:                  │
│  • Structure is well-known          • Structure varies per item │
│  • All items have same structure    • Schema changes frequently │
│  • Data integrity is critical       • External data (no control)│
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Data Locality

```
┌─────────────────────────────────────────────────────────────────┐
│                    DATA LOCALITY                                 │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Document DB:                                                   │
│  ┌──────────────────────────────────────────────────┐          │
│  │ { name, positions[], education[], contact{} }     │          │
│  └──────────────────────────────────────────────────┘          │
│  ▲ Everything stored contiguously on disk                       │
│  ▲ ONE disk seek to load entire document                        │
│  ✗ But: must load ENTIRE document even for small queries        │
│  ✗ Writes often rewrite entire document                         │
│                                                                 │
│  Relational DB:                                                 │
│  ┌──────┐  ┌───────────┐  ┌───────────┐  ┌─────────┐         │
│  │users │  │positions  │  │education  │  │contact  │         │
│  └──────┘  └───────────┘  └───────────┘  └─────────┘         │
│  ▲ Data spread across multiple tables                           │
│  ▲ Multiple disk seeks / index lookups (JOINs)                  │
│  ✓ But: can read just the table you need                        │
│  ✓ Can update individual fields efficiently                     │
│                                                                 │
│  Some relational DBs also offer locality features:              │
│  • Google Spanner (interleaved tables)                          │
│  • Oracle (multi-table index cluster tables)                    │
│  • Cassandra/HBase (column family model)                        │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Convergence of Document and Relational

Modern databases increasingly support **both** models:
- **PostgreSQL** (9.4+): JSONB columns with indexing and querying
- **MySQL** (5.7+): JSON data type with path expressions
- **MongoDB** (3.2+): `$lookup` for joins (like LEFT OUTER JOIN)
- **RethinkDB**: Supports joins in its query language

---

## Graph-Like Data Models

When your data has many **many-to-many** relationships, a graph model is the most natural.

```
┌─────────────────────────────────────────────────────────────────┐
│              GRAPH DATA MODEL BASICS                             │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Vertices (nodes)                Edges (relationships)          │
│  ┌─────────┐                     ────────────►                  │
│  │ Person  │ ──born_in──►  ┌──────────┐                        │
│  │ "Lucy"  │               │  City    │                        │
│  └────┬────┘               │ "London" │                        │
│       │                    └──────────┘                         │
│       │                         ▲                               │
│   lives_in                   within                             │
│       │                         │                               │
│       ▼                    ┌──────────┐                         │
│  ┌─────────┐               │ Country  │                        │
│  │  City   │ ──within──►   │   "UK"   │                        │
│  │"Seattle"│               └────┬─────┘                        │
│  └─────────┘                    │                               │
│       ▲                      part_of                            │
│    within                       │                               │
│       │                    ┌────▼─────┐                        │
│  ┌─────────┐               │Continent │                        │
│  │ State   │               │ "Europe" │                        │
│  │  "WA"   │               └──────────┘                        │
│  └─────────┘                                                    │
│                                                                 │
│  Key insight: Vertices can represent DIFFERENT types of things  │
│  (people, locations, events) — very flexible schema.            │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Property Graph Model (Neo4j, Titan)

Each **vertex** has:
- A unique identifier
- A set of outgoing edges
- A set of incoming edges
- A collection of properties (key-value pairs)

Each **edge** has:
- A unique identifier
- The tail vertex (start)
- The head vertex (end)
- A label describing the relationship
- A collection of properties (key-value pairs)

```sql
-- Representing a property graph in relational tables:

CREATE TABLE vertices (
    vertex_id   INTEGER PRIMARY KEY,
    properties  JSON
);

CREATE TABLE edges (
    edge_id     INTEGER PRIMARY KEY,
    tail_vertex INTEGER REFERENCES vertices(vertex_id),
    head_vertex INTEGER REFERENCES vertices(vertex_id),
    label       TEXT,
    properties  JSON
);

-- Index for traversals
CREATE INDEX edges_tails ON edges(tail_vertex);
CREATE INDEX edges_heads ON edges(head_vertex);
```

### Triple Stores (SPARQL, Datomic)

All information stored as **(subject, predicate, object)** triples:

```
(lucy,      age,        33)
(lucy,      born_in,    london)
(london,    name,       "London")
(london,    within,     england)
(england,   name,       "England")
(england,   within,     europe)
```

---

## Query Languages

### Declarative vs Imperative

```
┌─────────────────────────────────────────────────────────────────┐
│     IMPERATIVE (HOW)                 DECLARATIVE (WHAT)         │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  function getSharks(animals) {      SELECT * FROM animals       │
│    let sharks = [];                 WHERE family = 'Sharks';    │
│    for (let a of animals) {                                     │
│      if (a.family === 'Sharks') {   • Database chooses HOW     │
│        sharks.push(a);              • Optimizer picks best plan │
│      }                              • Parallel execution free   │
│    }                                • Order doesn't matter      │
│    return sharks;                                               │
│  }                                                              │
│                                                                 │
│  • YOU specify HOW                                              │
│  • You choose the algorithm                                     │
│  • Sequential execution                                        │
│  • Order matters                                                │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Cypher (Neo4j's Graph Query Language)

```cypher
-- Find all people who emigrated from the US to Europe:

MATCH
  (person) -[:BORN_IN]->  () -[:WITHIN*0..]-> (us:Location {name: 'United States'}),
  (person) -[:LIVES_IN]-> () -[:WITHIN*0..]-> (eu:Location {name: 'Europe'})
RETURN person.name
```

The `WITHIN*0..` means "follow a chain of WITHIN edges, zero or more times" — powerful graph traversal.

### SPARQL (for Triple Stores)

```sparql
PREFIX : <urn:example:>

SELECT ?personName WHERE {
  ?person :name ?personName .
  ?person :bornIn / :within* / :name "United States" .
  ?person :livesIn / :within* / :name "Europe" .
}
```

### SQL Recursive Queries (Graph Traversal in SQL)

```sql
-- Same query in SQL using recursive CTEs (verbose!):

WITH RECURSIVE
  in_usa(vertex_id) AS (
    SELECT vertex_id FROM vertices WHERE properties->>'name' = 'United States'
    UNION
    SELECT edges.tail_vertex
    FROM edges JOIN in_usa ON edges.head_vertex = in_usa.vertex_id
    WHERE edges.label = 'within'
  ),
  in_europe(vertex_id) AS (
    SELECT vertex_id FROM vertices WHERE properties->>'name' = 'Europe'
    UNION
    SELECT edges.tail_vertex
    FROM edges JOIN in_europe ON edges.head_vertex = in_europe.vertex_id
    WHERE edges.label = 'within'
  )
SELECT v.properties->>'name' AS person_name
FROM vertices v
JOIN edges born ON born.tail_vertex = v.vertex_id AND born.label = 'born_in'
JOIN edges lives ON lives.tail_vertex = v.vertex_id AND lives.label = 'lives_in'
WHERE born.head_vertex IN (SELECT vertex_id FROM in_usa)
  AND lives.head_vertex IN (SELECT vertex_id FROM in_europe);
```

This shows why **graph databases exist** — the same query is dramatically simpler in Cypher.

---

## MapReduce Querying

MapReduce is a programming model for processing large amounts of data in bulk across many machines (popularized by Google, implemented by MongoDB and Hadoop).

```
┌─────────────────────────────────────────────────────────────────┐
│              MapReduce: COUNT SHARKS PER MONTH                  │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  MongoDB MapReduce:                                             │
│                                                                 │
│  db.observations.mapReduce(                                     │
│    function map() {                     // Called once per doc  │
│      var year = this.observedAt.getFullYear();                  │
│      var month = this.observedAt.getMonth() + 1;               │
│      emit(year + "-" + month, this.numAnimals);                │
│    },                                                           │
│    function reduce(key, values) {       // Called per group     │
│      return Array.sum(values);                                  │
│    },                                                           │
│    {                                                            │
│      query: { family: "Sharks" },       // Filter first        │
│      out: "monthlySharkReport"          // Output collection   │
│    }                                                            │
│  );                                                             │
│                                                                 │
│  Pipeline:                                                      │
│  ┌───────────────┐    ┌───────────────┐    ┌───────────────┐   │
│  │  Filter docs  │───►│  MAP function │───►│REDUCE function│   │
│  │(family=Sharks)│    │ emit(key,val) │    │ sum(values)   │   │
│  └───────────────┘    └───────────────┘    └───────────────┘   │
│                                                                 │
│  Equivalent MongoDB Aggregation Pipeline (preferred today):     │
│                                                                 │
│  db.observations.aggregate([                                    │
│    { $match: { family: "Sharks" } },                           │
│    { $group: {                                                  │
│        _id: { year: {$year: "$observedAt"},                    │
│               month: {$month: "$observedAt"} },                │
│        totalAnimals: { $sum: "$numAnimals" }                   │
│    } }                                                          │
│  ]);                                                            │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## Interview Questions

### Q1: What is impedance mismatch?

The disconnect between the object-oriented model used in application code and the relational model used in databases. Objects have nested structures, lists, and references, but relational tables are flat rows with foreign keys. ORMs (Hibernate, SQLAlchemy) reduce boilerplate but don't eliminate the fundamental mismatch. Document databases reduce this by storing objects as JSON directly.

### Q2: When would you choose a document database over a relational database?

Choose document DB when: (1) your data has a natural document structure (1-to-many, tree-like), (2) the schema varies between records, (3) you need data locality (load everything about an entity in one read), (4) relationships between documents are rare. Choose relational when: data has many-to-many relationships, joins are common, referential integrity matters, or you need complex ad-hoc queries.

### Q3: Explain schema-on-read vs schema-on-write.

**Schema-on-write** (relational DBs): The database enforces a schema at write time — writes that don't conform are rejected. Like static typing. **Schema-on-read** (document DBs): No schema is enforced; the structure is interpreted by the application when data is read. Like dynamic typing. Schema-on-read is better when items don't all have the same structure or when the schema changes frequently.

### Q4: When should you use a graph database?

When your data has many **many-to-many** relationships and you need to traverse connections (shortest path, recommendation engines, social networks, fraud detection, knowledge graphs). Graph databases excel at queries like "find all people who live in Europe but were born in the US" which require recursive traversal — something that's verbose and slow in SQL but natural in Cypher/SPARQL.

### Q5: Why are declarative query languages preferred?

Declarative languages (SQL, Cypher) specify **what** data you want, not **how** to get it. This allows the database query optimizer to choose the best execution strategy (which indexes to use, which join order, whether to parallelize). Imperative code locks in a specific algorithm. When the database adds a new index or optimization, declarative queries benefit automatically without code changes.

### Q6: Compare the relational, document, and graph data models.

| Aspect | Relational | Document | Graph |
|--------|-----------|----------|-------|
| **Structure** | Tables with rows/columns | JSON/BSON documents | Vertices and edges |
| **Schema** | Schema-on-write (rigid) | Schema-on-read (flexible) | Schema-on-read (flexible) |
| **Relationships** | Foreign keys + JOINs | Embedded or references | Edges (first-class) |
| **Best for** | Structured, relational data | Tree-like, self-contained data | Highly connected data |
| **Joins** | Native, efficient | Weak/absent | Traversals (native) |
| **Examples** | PostgreSQL, MySQL | MongoDB, CouchDB | Neo4j, Amazon Neptune |

---

*Based on Chapter 2 of "Designing Data-Intensive Applications" by Martin Kleppmann*
