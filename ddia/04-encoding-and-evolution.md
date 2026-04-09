# Chapter 4: Encoding and Evolution

## Table of Contents

1. [Formats for Encoding Data](#formats-for-encoding-data)
2. [Language-Specific Formats](#language-specific-formats)
3. [JSON, XML, and Binary Variants](#json-xml-and-binary-variants)
4. [Thrift and Protocol Buffers](#thrift-and-protocol-buffers)
5. [Avro](#avro)
6. [Schema Evolution Rules](#schema-evolution-rules)
7. [Modes of Dataflow](#modes-of-dataflow)
8. [Interview Questions](#interview-questions)

---

## Formats for Encoding Data

Programs work with data in two representations:

```
┌─────────────────────────────────────────────────────────────────┐
│              IN-MEMORY vs ON-WIRE REPRESENTATION                │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  IN MEMORY:                        ON DISK / NETWORK:           │
│  ──────────                        ──────────────────           │
│  Objects, structs, arrays,         Self-contained sequence      │
│  hash tables, trees, graphs.       of bytes (no pointers).      │
│  Optimized for CPU access          Optimized for storage        │
│  (pointers, indexes).              and transmission.            │
│                                                                 │
│         ENCODING                                                │
│  Memory ──────────────► Bytes   (also: serialization,           │
│                                  marshalling)                   │
│         DECODING                                                │
│  Memory ◄──────────────  Bytes  (also: deserialization,         │
│                                  unmarshalling, parsing)        │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## Language-Specific Formats

Many languages have built-in serialization: Java `Serializable`, Python `pickle`, Ruby `Marshal`.

**Problems with language-specific encoding**:

| Problem              | Details                                                            |
| -------------------- | ------------------------------------------------------------------ |
| **Language lock-in** | Data encoded with Java's Serializable can only be read by Java     |
| **Security**         | Decoding can instantiate arbitrary classes → remote code execution |
| **Versioning**       | Poor support for forward/backward compatibility                    |
| **Efficiency**       | Java's built-in serialization is notoriously slow and bloated      |

**Rule**: Never use language-specific serialization for anything beyond very transient purposes.

---

## JSON, XML, and Binary Variants

### Problems with JSON and XML

```
┌─────────────────────────────────────────────────────────────────┐
│              JSON/XML ENCODING ISSUES                            │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  1. NUMBER AMBIGUITY                                            │
│     JSON: no distinction between int and float                  │
│     JavaScript: Numbers > 2^53 lose precision                   │
│     Twitter API returns tweet IDs as both number AND string     │
│     because JavaScript mangles large numbers.                   │
│                                                                 │
│  2. NO BINARY STRING SUPPORT                                    │
│     JSON/XML: text only. Binary data must be Base64 encoded     │
│     → 33% size increase.                                        │
│                                                                 │
│  3. SCHEMA SUPPORT                                              │
│     XML: XSD exists but complex and rarely used                 │
│     JSON: JSON Schema exists but not widely adopted             │
│     Without schema → application must hardcode field names      │
│                                                                 │
│  4. VERBOSITY                                                   │
│     XML: <firstName>John</firstName>                            │
│     JSON: {"firstName": "John"}                                 │
│     Field names repeated in every record → wastes space         │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Binary JSON Encodings

```
┌─────────────────────────────────────────────────────────────────┐
│              BINARY JSON VARIANTS                                │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Format      │ Used By        │ Key Feature                     │
│  ────────────┼────────────────┼───────────────────────────      │
│  MessagePack │ Redis, Fluentd │ Simple binary JSON              │
│  BSON        │ MongoDB        │ Adds date, binary, int types    │
│  BJSON       │ Various        │ Binary JSON encoding            │
│  UBJSON      │ Various        │ Universal Binary JSON           │
│                                                                 │
│  Problem: These still include field names in every record.      │
│  Savings are modest (~15-30%) compared to text JSON.            │
│  For significant compression, need a SCHEMA-based approach.     │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## Thrift and Protocol Buffers

Both use a **schema** to define the structure, then encode data using field tags (numbers) instead of field
names.

### Protocol Buffers Schema Example

```protobuf
message Person {
required string user_name = 1;
optional int64  favorite_number = 2;
repeated string interests = 3;
}
```

### Thrift Schema Example

```thrift
struct Person {
  1: required string userName,
  2: optional i64 favoriteNumber,
  3: optional list<string> interests,
}
```

### Binary Encoding Comparison

```
┌─────────────────────────────────────────────────────────────────┐
│              ENCODING SIZE COMPARISON                            │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Example record: {"userName":"Martin","favoriteNumber":1337,    │
│                    "interests":["daydreaming","hacking"]}       │
│                                                                 │
│  Format                  │ Size (bytes) │ Notes                 │
│  ────────────────────────┼──────────────┼────────────────────── │
│  JSON (text)             │     81       │ Field names repeated  │
│  JSON (whitespace removed│     67       │ Still has field names │
│  MessagePack (binary)    │     66       │ Barely smaller!       │
│  Thrift BinaryProtocol   │     59       │ Field TAGS not names  │
│  Thrift CompactProtocol  │     34       │ Var-int encoding      │
│  Protocol Buffers        │     33       │ Very compact          │
│                                                                 │
│  Key insight: Schema-based encodings replace field NAMES with   │
│  numeric TAGS (1, 2, 3) → much smaller, and the schema serves  │
│  as documentation.                                              │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Schema Evolution with Field Tags

```
┌─────────────────────────────────────────────────────────────────┐
│              FORWARD & BACKWARD COMPATIBILITY                    │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  FORWARD COMPATIBILITY: Old code can read new data              │
│  BACKWARD COMPATIBILITY: New code can read old data             │
│                                                                 │
│  Adding a new field (tag = 4):                                  │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ Old code reading new data:                               │   │
│  │ Sees unknown tag 4 → IGNORES it (forward compatible)     │   │
│  │                                                          │   │
│  │ New code reading old data:                               │   │
│  │ Tag 4 not present → uses DEFAULT value (backward compat) │   │
│  │ BUT: new field must be optional or have a default!       │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
│  Removing a field:                                              │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ • Can only remove OPTIONAL fields                        │   │
│  │ • The tag number must NEVER be reused                    │   │
│  │   (old data in the wild still uses that tag)             │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
│  Changing data types:                                           │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ • int32 → int64: OK (new code reads old 32-bit values)   │   │
│  │ • int64 → int32: RISKY (values may be truncated)         │   │
│  │ • single → repeated: Protobuf OK, Thrift not             │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
│  GOLDEN RULE: Never change a field's tag number.                │
│  Tags are the identity of fields in the binary encoding.        │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## Avro

Apache Avro uses a schema but takes a **different approach**: no field tags in the binary encoding at all.

### Avro Schema

```json
{
  "type": "record",
  "name": "Person",
  "fields": [
    { "name": "userName", "type": "string" },
    { "name": "favoriteNumber", "type": ["null", "long"], "default": null },
    { "name": "interests", "type": { "type": "array", "items": "string" } }
  ]
}
```

### Avro Binary Encoding

```
┌─────────────────────────────────────────────────────────────────┐
│              AVRO ENCODING: NO FIELD TAGS OR NAMES              │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Binary data (32 bytes):                                        │
│  ┌────────────────────────────────────────────────────────┐    │
│  │ 06 4D 61 72 74 69 6E │ 02 │ A4 14 │ 04 │ 0D... │ 0D..│    │
│  └────────────────────────────────────────────────────────┘    │
│    ▲ string "Martin"      ▲    ▲ 1337   ▲    2 strings        │
│                         union           array                  │
│                         branch          length                 │
│                                                                │
│  NO field names. NO field tags. Just values concatenated!       │
│  Reader MUST have the EXACT SAME SCHEMA to decode.             │
│                                                                │
│  But wait — how does schema evolution work without tags?        │
│                                                                │
└─────────────────────────────────────────────────────────────────┘
```

### Writer's Schema vs Reader's Schema

```
┌─────────────────────────────────────────────────────────────────┐
│              AVRO SCHEMA RESOLUTION                              │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Writer's Schema (v1):          Reader's Schema (v2):           │
│  ┌───────────────────┐         ┌───────────────────────┐       │
│  │ userName: string  │         │ userName: string      │       │
│  │ favoriteNumber: ? │         │ favoriteNumber: ?     │       │
│  │                   │         │ favoriteColor: string │ NEW!  │
│  └───────────────────┘         └───────────────────────┘       │
│                                                                 │
│  Avro library resolves differences by FIELD NAME:               │
│  • userName: in both → transfer                                │
│  • favoriteNumber: in both → transfer                          │
│  • favoriteColor: in reader but NOT writer → use default        │
│  • (If writer has field reader doesn't → ignore)               │
│                                                                 │
│  Field matching by NAME (not position or tag).                  │
│  This is why Avro uses names, not numeric tags.                 │
│                                                                 │
│  How does the reader know the writer's schema?                  │
│  • Large file (Hadoop): writer's schema in file header          │
│  • DB records: version number → schema registry lookup          │
│  • Network RPC: schema negotiated at connection setup           │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Why Avro for Hadoop?

```
┌─────────────────────────────────────────────────────────────────┐
│  Avro is ideal for Hadoop because:                              │
│                                                                 │
│  1. Schema in file header → self-describing files               │
│  2. No code generation required (dynamically typed languages)   │
│  3. Schema evolution by field name (not tags)                   │
│  4. Very compact encoding (no tag overhead per field)           │
│  5. Splittable container format (MapReduce can split files)     │
│                                                                 │
│  Protobuf/Thrift require code generation for each schema        │
│  change → not practical for Hadoop pipelines with hundreds      │
│  of schemas that evolve independently.                          │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## Schema Evolution Rules

```
┌──────────────────────────────────────────────────────────────────┐
│              SCHEMA EVOLUTION COMPARISON                         │
├──────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Operation            │ Protobuf/Thrift   │ Avro                │
│  ─────────────────────┼───────────────────┼──────────────────── │
│  Add optional field   │ ✓ (new tag)       │ ✓ (with default)   │
│  Remove optional field│ ✓ (never reuse tag)│ ✓ (keep in writer)│
│  Add required field   │ ✗ (breaks old)    │ ✗ (breaks old)     │
│  Rename field         │ ✓ (tag unchanged) │ ✗ (name = identity)│
│  Change field type    │ Risky (truncation)│ Limited             │
│  Field identification │ Numeric tags      │ Field names         │
│                                                                  │
│  Forward compatibility = old readers ignore unknown fields       │
│  Backward compatibility = new readers handle missing fields      │
│                                                                  │
│  Both directions needed for rolling upgrades where old and       │
│  new code coexist simultaneously.                                │
│                                                                  │
└──────────────────────────────────────────────────────────────────┘
```

---

## Modes of Dataflow

Data flows between processes in three main ways:

### 1. Dataflow Through Databases

```
┌─────────────────────────────────────────────────────────────────┐
│              DATABASE AS DATAFLOW                                │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Process A (new code)                                           │
│  writes data ────────► DATABASE ────────► Process B (old code)  │
│  with new fields                          reads data,           │
│                                           ignores new fields    │
│                                                                 │
│  The database is like "sending a message to your future self."  │
│                                                                 │
│  DANGER: If old code reads a record, modifies it, and writes   │
│  it back — the new fields may be LOST (rewritten without them).│
│                                                                 │
│  ┌──────────┐    Read     ┌──────────┐   Write    ┌──────────┐│
│  │ DB record│───────────►│ Old code │──────────►│ DB record ││
│  │ {a,b,c}  │            │ knows a,b│           │ {a,b}     ││
│  └──────────┘            └──────────┘           └──────────┘│ │
│                                                   field c LOST!│
│                                                                 │
│  Solution: Application code must preserve unknown fields        │
│  when reading and re-writing records.                           │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 2. Dataflow Through Services (REST and RPC)

```
┌─────────────────────────────────────────────────────────────────┐
│              REST vs RPC                                         │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  REST (Representational State Transfer):                        │
│  • Based on HTTP, uses URLs to identify resources               │
│  • Formats: JSON (most common), XML                            │
│  • Good for public APIs, browser clients                        │
│  • OpenAPI / Swagger for documentation                          │
│                                                                 │
│  RPC (Remote Procedure Call):                                   │
│  • Tries to make network calls look like local function calls  │
│  • Formats: Protobuf (gRPC), Thrift, Avro                     │
│  • Good for internal service-to-service communication           │
│                                                                 │
│  PROBLEMS WITH RPC:                                             │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ Local function call:          Network call:              │   │
│  │ • Predictable (returns or     • May be lost, delayed,   │   │
│  │   throws exception)            or duplicated             │   │
│  │ • Same parameters =           • Timeout: did it         │   │
│  │   same result                   succeed or not?          │   │
│  │ • Can pass references         • Must serialize all data │   │
│  │ • Same language               • Cross-language needed   │   │
│  │ • Negligible latency          • Network latency varies  │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
│  Modern RPC frameworks (gRPC, Finagle, Rest.li) embrace         │
│  the difference rather than hiding it:                          │
│  • Futures/promises for async calls                             │
│  • Streaming (gRPC bidirectional streams)                      │
│  • Service discovery                                            │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 3. Dataflow Through Asynchronous Message Passing

```
┌─────────────────────────────────────────────────────────────────┐
│              MESSAGE BROKERS / MESSAGE QUEUES                    │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Producer ──► Message Broker ──► Consumer                       │
│               (RabbitMQ,                                        │
│                Kafka, etc.)                                     │
│                                                                 │
│  Advantages over direct RPC:                                    │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ • BUFFER: Broker stores messages if consumer is slow    │   │
│  │ • RETRY: Automatically redeliver failed messages        │   │
│  │ • DECOUPLE: Producer doesn't need to know consumer     │   │
│  │ • FAN-OUT: One message → multiple consumers            │   │
│  │ • ASYNC: Producer doesn't wait for consumer response   │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
│  Actor Model (Akka, Orleans, Erlang OTP):                       │
│  • Each actor = single-threaded process with a mailbox          │
│  • Actors communicate by sending async messages                 │
│  • Location transparency: actors can be on different nodes      │
│  • No shared state between actors → no locks needed             │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Rolling Upgrades and Compatibility

```
┌─────────────────────────────────────────────────────────────────┐
│              WHY BOTH FORWARD AND BACKWARD COMPATIBILITY?        │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  During a rolling upgrade:                                      │
│                                                                 │
│  ┌──────┐  ┌──────┐  ┌──────┐  ┌──────┐  ┌──────┐            │
│  │Node 1│  │Node 2│  │Node 3│  │Node 4│  │Node 5│            │
│  │v2 NEW│  │v2 NEW│  │v1 OLD│  │v1 OLD│  │v1 OLD│            │
│  └──────┘  └──────┘  └──────┘  └──────┘  └──────┘            │
│                                                                 │
│  Node 1 (v2) sends data to Node 4 (v1):                        │
│  → v1 must handle v2's data → FORWARD COMPATIBILITY             │
│                                                                 │
│  Node 4 (v1) sends data to Node 1 (v2):                        │
│  → v2 must handle v1's data → BACKWARD COMPATIBILITY            │
│                                                                 │
│  Both are needed simultaneously during rollout period.           │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## Interview Questions

### Q1: Why is language-specific serialization (Java Serializable, Python pickle) a bad idea?

It locks you into a single programming language (can't read the data from any other language). It has security
vulnerabilities (deserialization can instantiate arbitrary classes). It has poor support for schema evolution
and versioning. And it's often slow and produces bloated output. Use a language-agnostic format (JSON,
Protobuf, Avro) instead.

### Q2: Compare Protocol Buffers, Thrift, and Avro.

All three use schemas for compact binary encoding. **Protobuf** and **Thrift** use numeric **field tags** —
each field has a number that never changes, and this number appears in the binary encoding instead of the
field name. **Avro** uses **field names** for resolution and includes no tags in the binary encoding, making
it the most compact. Avro requires the writer's schema to be available at read time (stored in file headers or
a schema registry). Protobuf/Thrift are better for RPC (code generation); Avro is better for Hadoop/big data
(dynamic schemas, self-describing files).

### Q3: What is forward and backward compatibility?

**Backward compatibility**: Newer code can read data written by older code. **Forward compatibility**: Older
code can read data written by newer code. Both are needed during rolling upgrades when old and new code
versions coexist. Schema evolution rules (don't remove required fields, don't reuse field tags, provide
defaults for new fields) enable both directions of compatibility.

### Q4: What are the three modes of dataflow?

1. **Through databases**: One process writes, another reads later. Must handle schema evolution in stored data
   (old records coexist with new records).
2. **Through services (REST/RPC)**: Client sends request, server responds. Must agree on API contract with
   versioning.
3. **Through async message passing**: Producer sends messages to a broker, consumer reads them. Decouples
   sender and receiver in time and availability.

### Q5: Why does Avro not use field tags?

Avro was designed for Hadoop, where you have hundreds of schemas evolving independently, and generating code
for each schema change is impractical. By using field **names** instead of numeric tags, Avro enables: (1)
dynamic schema resolution at read time without code generation, (2) extremely compact encoding (no tag bytes),
(3) easier schema evolution for dynamically-typed languages. The trade-off is that the reader must always have
access to the writer's schema.

---

_Based on Chapter 4 of "Designing Data-Intensive Applications" by Martin Kleppmann_
