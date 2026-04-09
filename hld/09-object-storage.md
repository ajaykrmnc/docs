# Design an Object Storage Service (Amazon S3)

**Difficulty:** Hard | **Companies:** Amazon, Google, Microsoft, Alibaba, MinIO

---

## 1. Problem Statement and Scope

### Problem

Design a highly durable, scalable object storage service---akin to Amazon S3---that stores
and retrieves arbitrary-sized objects (files, images, videos, backups, logs, ML datasets)
with **99.999999999% (11 nines) durability**. The service must handle petabyte-scale
storage, serve millions of requests per second, and provide strong read-after-write
consistency while remaining cost-efficient through tiered storage.

### Scope

**In Scope:**
- Object CRUD operations (PUT, GET, DELETE, HEAD)
- Bucket management (create, list, delete, configure)
- Versioning (object-level version history)
- Multipart upload for large objects (up to 5 TB)
- Access control: ACLs, bucket policies, IAM integration
- Pre-signed URLs for temporary access
- Lifecycle policies (transition between storage tiers, expiration)
- Object metadata and tagging
- Listing with prefix filtering and delimiter support (virtual directory hierarchy)
- Cross-region replication
- Storage classes (hot, warm, cold, archive)

**Out of Scope:**
- File-system semantics (POSIX compliance, rename atomicity)
- Real-time streaming or append operations
- SQL-style querying over object contents (S3 Select is a separate deep-dive)
- CDN edge caching design (assume integration with existing CDN)
- Billing and metering subsystem internals

---

## 2. Functional Requirements

| # | Requirement | Details |
|---|-------------|---------|
| FR-1 | **PUT Object** | Upload objects from 1 byte to 5 TB. Support streaming uploads. |
| FR-2 | **GET Object** | Download full object or byte-range requests. |
| FR-3 | **DELETE Object** | Mark object for deletion; reclaim space asynchronously. |
| FR-4 | **HEAD Object** | Retrieve metadata without downloading the object body. |
| FR-5 | **Bucket Management** | Create, list, delete buckets. Globally unique bucket names. |
| FR-6 | **Object Listing** | List objects in a bucket with prefix, delimiter, marker-based pagination. |
| FR-7 | **Versioning** | Enable per-bucket versioning; each PUT creates a new version. |
| FR-8 | **Multipart Upload** | Initiate, upload parts (5 MB - 5 GB each), complete/abort. |
| FR-9 | **Access Control** | Bucket policies (JSON), object ACLs, IAM policy evaluation. |
| FR-10 | **Pre-signed URLs** | Time-limited signed URLs for upload or download. |
| FR-11 | **Lifecycle Policies** | Transition objects between storage classes; auto-expire objects. |
| FR-12 | **Object Metadata** | System metadata (size, ETag, content-type) + user-defined metadata. |
| FR-13 | **Cross-Region Replication** | Async replication of objects to a target bucket in another region. |
| FR-14 | **Storage Classes** | Standard, Infrequent Access, Glacier (archive), Deep Archive. |

---

## 3. Non-Functional Requirements

| # | Requirement | Target |
|---|-------------|--------|
| NFR-1 | **Durability** | 99.999999999% (11 nines) annual durability |
| NFR-2 | **Availability** | 99.99% (four nines) for standard storage class |
| NFR-3 | **Scale** | Support petabytes of storage, trillions of objects |
| NFR-4 | **Throughput** | Sustain millions of requests/sec globally |
| NFR-5 | **Latency** | p50 < 50ms for GET, p99 < 200ms for GET, p50 < 100ms for PUT |
| NFR-6 | **Consistency** | Strong read-after-write consistency |
| NFR-7 | **Cost Efficiency** | Erasure coding (1.5x overhead) over triple replication (3x) |
| NFR-8 | **Security** | Encryption at rest (SSE-S3, SSE-KMS, SSE-C), encryption in transit (TLS) |
| NFR-9 | **Compliance** | WORM (Write Once Read Many) support for regulatory compliance |
| NFR-10 | **Operability** | Zero-downtime upgrades, automated failure recovery |

### Durability Math: What Does 11 Nines Mean?

```
11 nines = 99.999999999% durability per year
Probability of losing an object in a year = 0.000000001% = 1e-11

If you store 10 billion objects:
  Expected objects lost per year = 10^10 * 10^-11 = 0.1

  => Statistically, you lose LESS THAN 1 object per 10 billion per year.

For 10 PB of data (100 billion 100KB objects):
  Expected loss = 100 * 10^9 * 10^-11 = 1 object/year
```

---

## 4. Back-of-Envelope Estimation

### Storage Scale

```
Total objects stored:        100 billion (10^11)
Average object size:         100 KB
Total raw data:              100 * 10^9 * 100 KB = 10 PB

Erasure coding overhead:     1.5x
Total physical storage:      10 PB * 1.5 = 15 PB

Metadata per object:         ~1 KB (key, bucket, version, ETag, timestamps, ACL ref)
Total metadata:              100 * 10^9 * 1 KB = 100 TB
```

### Traffic Estimates

```
Write (PUT) requests:        1 million/sec
Read (GET) requests:         10 million/sec (10:1 read-write ratio)
DELETE requests:             100K/sec

Average PUT payload:         100 KB
Write throughput:            1M * 100 KB = 100 GB/sec = 800 Gbps
Read throughput:             10M * 100 KB = 1 TB/sec = 8 Tbps

Daily new data:              1M/sec * 100 KB * 86400 = ~8.6 PB/day
Annual growth:               ~3 EB/year (before erasure coding)
```

### Hardware Estimates

```
Storage node capacity:       100 TB usable per node (12 x 16TB HDDs, ~80% utilization)
Nodes for 15 PB:             15,000 TB / 100 TB = 150 nodes (initial)
With growth headroom (2x):   300 storage nodes

API servers:
  Each handles ~10K req/sec
  For 11M total req/sec:     ~1,100 API servers

Metadata servers:
  100 TB metadata, sharded
  With caching, ~50 servers
```

### Erasure Coding vs Replication Cost

```
                        Replication (3x)    Erasure Coding (8+4)
─────────────────────────────────────────────────────────────────
Storage overhead:       3.0x                1.5x
For 10 PB raw data:     30 PB               15 PB
Fault tolerance:        2 failures           4 failures
Repair cost:            Copy full replica    Reconstruct from k chunks
Read latency:           Fast (any replica)   Slightly higher (decode)
Write latency:          Slightly lower       Slightly higher (encode)
Cost per PB/month:      ~$30K               ~$15K
─────────────────────────────────────────────────────────────────
Winner for scale:       Erasure Coding (50% cheaper, more fault tolerant)
```

---

## 5. API Design

### 5.1 Object Operations

```
PUT /v1/{bucket}/{key}
  Headers:
    Content-Type: application/octet-stream
    Content-Length: <size>
    x-amz-storage-class: STANDARD | IA | GLACIER
    x-amz-meta-{key}: {value}         # user-defined metadata
    x-amz-server-side-encryption: AES256 | aws:kms
  Body: <object data>
  Response: 200 OK
    ETag: "d41d8cd98f00b204e9800998ecf8427e"
    x-amz-version-id: "v3.2.1"

GET /v1/{bucket}/{key}
  Headers:
    Range: bytes=0-1023               # byte-range request (optional)
    If-None-Match: "<etag>"           # conditional GET
  Query Params:
    versionId=<version>               # specific version
  Response: 200 OK | 206 Partial Content | 304 Not Modified
    Body: <object data>

DELETE /v1/{bucket}/{key}
  Query Params:
    versionId=<version>               # delete specific version
  Response: 204 No Content
    x-amz-delete-marker: true         # if versioning enabled

HEAD /v1/{bucket}/{key}
  Response: 200 OK
    Content-Length: 1048576
    Content-Type: image/png
    ETag: "d41d8cd98f00b204e9800998ecf8427e"
    Last-Modified: Thu, 01 Jan 2026 00:00:00 GMT
    x-amz-version-id: "v3.2.1"
```

### 5.2 Bucket Operations

```
PUT /v1/{bucket}
  Headers:
    x-amz-bucket-region: us-east-1
  Body: <CreateBucketConfiguration>
  Response: 200 OK

GET /v1/{bucket}?prefix=photos/2026/&delimiter=/&max-keys=1000&marker=<last-key>
  Response: 200 OK
    <ListBucketResult>
      <Contents>
        <Key>photos/2026/jan/photo1.jpg</Key>
        <Size>2048576</Size>
        <ETag>"abc123"</ETag>
        <LastModified>2026-01-15T10:30:00Z</LastModified>
        <StorageClass>STANDARD</StorageClass>
      </Contents>
      <CommonPrefixes>
        <Prefix>photos/2026/feb/</Prefix>
      </CommonPrefixes>
      <IsTruncated>true</IsTruncated>
      <NextMarker>photos/2026/jan/photo999.jpg</NextMarker>
    </ListBucketResult>

DELETE /v1/{bucket}
  Precondition: bucket must be empty
  Response: 204 No Content
```

### 5.3 Multipart Upload

```
# Step 1: Initiate
POST /v1/{bucket}/{key}?uploads
  Response: 200 OK
    <UploadId>abc123</UploadId>

# Step 2: Upload Parts (parallelizable)
PUT /v1/{bucket}/{key}?partNumber=1&uploadId=abc123
  Body: <part data, 5MB - 5GB>
  Response: 200 OK
    ETag: "part1-etag"

PUT /v1/{bucket}/{key}?partNumber=2&uploadId=abc123
  Body: <part data>
  Response: 200 OK
    ETag: "part2-etag"

# Step 3: Complete
POST /v1/{bucket}/{key}?uploadId=abc123
  Body:
    <CompleteMultipartUpload>
      <Part><PartNumber>1</PartNumber><ETag>"part1-etag"</ETag></Part>
      <Part><PartNumber>2</PartNumber><ETag>"part2-etag"</ETag></Part>
    </CompleteMultipartUpload>
  Response: 200 OK
    ETag: "final-composite-etag"

# Abort (cleanup)
DELETE /v1/{bucket}/{key}?uploadId=abc123
  Response: 204 No Content
```

### 5.4 Pre-signed URL Generation (Server-side)

```
# Generate pre-signed URL (internal API, not HTTP-facing):
GeneratePresignedURL(
  bucket:     "my-bucket",
  key:        "private/report.pdf",
  method:     "GET",
  expiry:     3600,           # seconds
  conditions: {content-type: "application/pdf"}
)

# Returns:
https://s3.example.com/v1/my-bucket/private/report.pdf
  ?X-Amz-Algorithm=AWS4-HMAC-SHA256
  &X-Amz-Credential=AKID/20260101/us-east-1/s3/aws4_request
  &X-Amz-Date=20260101T000000Z
  &X-Amz-Expires=3600
  &X-Amz-Signature=<computed-signature>
```

---

## 6. Data Model and Database Selection

### 6.1 Data Categories and Storage Choices

```
┌──────────────────────┬───────────────────────────┬─────────────────────────────────┐
│ Data Category        │ Storage Engine            │ Rationale                       │
├──────────────────────┼───────────────────────────┼─────────────────────────────────┤
│ Object data (blobs)  │ Custom distributed store  │ Raw disk I/O, erasure coded,    │
│                      │ on bare metal / HDDs      │ no filesystem overhead          │
├──────────────────────┼───────────────────────────┼─────────────────────────────────┤
│ Object metadata      │ Distributed KV store      │ High write throughput, range     │
│                      │ (RocksDB + Raft) or       │ queries for listing, sharded    │
│                      │ CockroachDB / Vitess      │ by bucket hash                  │
├──────────────────────┼───────────────────────────┼─────────────────────────────────┤
│ Bucket metadata      │ MySQL (Vitess sharded)    │ Relatively small dataset,       │
│                      │ + Redis cache             │ strong consistency needed        │
├──────────────────────┼───────────────────────────┼─────────────────────────────────┤
│ IAM / Policies       │ MySQL + local cache       │ Read-heavy, infrequent updates  │
├──────────────────────┼───────────────────────────┼─────────────────────────────────┤
│ Placement map        │ etcd / ZooKeeper          │ Small, critical config data,    │
│                      │                           │ strong consistency via Raft      │
└──────────────────────┴───────────────────────────┴─────────────────────────────────┘
```

### 6.2 Object Metadata Schema

```
ObjectMetadata {
  bucket_id:        uint64          # FK to bucket (hashed bucket name)
  object_key:       string          # full key path (e.g., "photos/2026/img.jpg")
  version_id:       string          # UUID, null if versioning disabled
  object_id:        UUID            # internal unique identifier
  size:             uint64          # object size in bytes
  etag:             string          # MD5 or multipart composite hash
  content_type:     string          # MIME type
  storage_class:    enum            # STANDARD, IA, GLACIER, DEEP_ARCHIVE
  encryption:       enum            # NONE, SSE_S3, SSE_KMS, SSE_C
  kms_key_id:       string          # if SSE_KMS
  created_at:       timestamp
  last_modified:    timestamp
  delete_marker:    bool            # true if this is a delete marker (versioned)
  user_metadata:    map<str, str>   # x-amz-meta-* headers
  tags:             map<str, str>   # object tagging
  acl:              bytes           # serialized ACL
  data_locations:   []ChunkLocation # pointers to erasure-coded chunks
}

ChunkLocation {
  chunk_index:      uint8           # 0..k+m-1
  node_id:          uint32          # storage node identifier
  disk_id:          uint16          # disk within node
  offset:           uint64          # byte offset on disk
  length:           uint32          # chunk size
  checksum:         uint32          # CRC32C of this chunk
}
```

### 6.3 Bucket Metadata Schema

```
BucketMetadata {
  bucket_id:        uint64          # hash of bucket_name
  bucket_name:      string          # globally unique
  owner_id:         uint64          # account ID
  region:           string          # primary region
  created_at:       timestamp
  versioning:       enum            # DISABLED, ENABLED, SUSPENDED
  encryption_config: EncryptionConfig
  lifecycle_rules:  []LifecycleRule
  cors_config:      CORSConfig
  replication_config: ReplicationConfig
  policy:           string          # JSON bucket policy
  acl:              bytes
  logging_config:   LoggingConfig
  object_count:     uint64          # approximate, updated async
  total_size:       uint64          # approximate
}
```

### 6.4 Why Not a Filesystem for Object Data?

```
Traditional filesystem (ext4, XFS):
  - Inode overhead per file: ~256 bytes + directory entry
  - 1 billion small objects = massive inode table, slow lookups
  - Journal overhead, metadata sync costs
  - Not optimized for erasure coding chunk layout

Custom storage engine:
  - Objects packed into large "extent files" (e.g., 1 GB segments)
  - Offset-based addressing within segments
  - No inode overhead; metadata is external (in metadata store)
  - Can align chunks for direct I/O (bypass page cache for large objects)
  - Better control over disk scheduling and repair I/O
```

---

## 7. High-Level Architecture

### 7.1 System Overview

```
                                 ┌──────────────────┐
                                 │   DNS / Global    │
                                 │   Load Balancer   │
                                 └────────┬─────────┘
                                          │
                          ┌───────────────┼───────────────┐
                          │               │               │
                   ┌──────▼──────┐ ┌──────▼──────┐ ┌──────▼──────┐
                   │  API Server │ │  API Server │ │  API Server │
                   │  (Stateless)│ │  (Stateless)│ │  (Stateless)│
                   └──────┬──────┘ └──────┬──────┘ └──────┬──────┘
                          │               │               │
              ┌───────────┼───────────────┼───────────────┼──────────┐
              │           │               │               │          │
     ┌────────▼────┐ ┌────▼─────┐ ┌───────▼──────┐ ┌─────▼───┐ ┌───▼────────┐
     │  IAM /Auth  │ │ Metadata │ │  Placement   │ │  Data   │ │ Namespace  │
     │  Service    │ │ Service  │ │  Service     │ │ Service │ │ Service    │
     └─────────────┘ └────┬─────┘ └───────┬──────┘ └────┬────┘ └────────────┘
                          │               │              │
                   ┌──────▼──────┐  ┌─────▼──────┐ ┌────▼──────────────────┐
                   │  Metadata   │  │  Placement │ │    Data Node Cluster  │
                   │  Store      │  │  Map (etcd)│ │                       │
                   │ (CockroachDB│  └────────────┘ │  ┌─────┐ ┌─────┐     │
                   │  / Vitess)  │                 │  │DN-1 │ │DN-2 │ ... │
                   └─────────────┘                 │  │12xHDD│ │12xHDD│    │
                                                   │  └─────┘ └─────┘     │
                                                   └──────────────────────┘
                                                          │
                                              ┌───────────┼───────────┐
                                              │           │           │
                                        ┌─────▼────┐ ┌───▼──────┐ ┌──▼────────┐
                                        │ Garbage  │ │ Data     │ │ Integrity │
                                        │ Collector│ │ Compactor│ │ Scrubber  │
                                        └──────────┘ └──────────┘ └───────────┘
```

### 7.2 Request Flow: PUT Object

```
Client                 API Server         IAM         Metadata Svc    Placement Svc    Data Nodes
  │                        │                │               │               │              │
  │──PUT /bucket/key──────▶│                │               │               │              │
  │                        │──AuthZ check──▶│               │               │              │
  │                        │◀──Allow────────│               │               │              │
  │                        │                │               │               │              │
  │                        │──Get placement────────────────────────────────▶│              │
  │                        │◀──Node list [DN1,DN3,DN5,...] (12 nodes)───────│              │
  │                        │                │               │               │              │
  │                        │  ┌─────────────────────────────────────────────┐              │
  │                        │  │ Erasure encode: split into 8 data +        │              │
  │                        │  │ 4 parity chunks (Reed-Solomon 8,4)         │              │
  │                        │  └─────────────────────────────────────────────┘              │
  │                        │                │               │               │              │
  │                        │──Write chunk 0─────────────────────────────────────────────▶ DN1
  │                        │──Write chunk 1─────────────────────────────────────────────▶ DN3
  │                        │──Write chunk 2─────────────────────────────────────────────▶ DN5
  │                        │  ... (parallel writes to 12 nodes) ...        │              │
  │                        │◀──ACK (all 12 chunks written)─────────────────────────────── │
  │                        │                │               │               │              │
  │                        │──Store metadata───────────────▶│               │              │
  │                        │  (key, version, chunk locations, etag, size)   │              │
  │                        │◀──Metadata committed──────────│               │              │
  │                        │                │               │               │              │
  │◀──200 OK (ETag)────────│                │               │               │              │
  │                        │                │               │               │              │
```

### 7.3 Request Flow: GET Object

```
Client              API Server       IAM       Metadata Svc     Data Nodes
  │                     │              │             │               │
  │──GET /bucket/key──▶│              │             │               │
  │                     │──AuthZ──────▶│             │               │
  │                     │◀──Allow──────│             │               │
  │                     │              │             │               │
  │                     │──Lookup key─────────────▶│               │
  │                     │◀──Metadata (chunk locations, size)────────│
  │                     │              │             │               │
  │                     │  ┌────────────────────────────────────┐   │
  │                     │  │ Need any 8 of 12 chunks to decode │   │
  │                     │  │ Select 8 closest/fastest nodes    │   │
  │                     │  └────────────────────────────────────┘   │
  │                     │              │             │               │
  │                     │──Read chunk 0────────────────────────────▶DN1
  │                     │──Read chunk 1────────────────────────────▶DN3
  │                     │  ... (parallel reads from 8 nodes) ...    │
  │                     │◀──8 chunks received──────────────────────│
  │                     │              │             │               │
  │                     │  ┌──────────────────────────────────┐     │
  │                     │  │ Reed-Solomon decode: 8 data      │     │
  │                     │  │ chunks → reconstruct full object │     │
  │                     │  └──────────────────────────────────┘     │
  │                     │              │             │               │
  │◀──200 OK (body)─────│              │             │               │
```

### 7.4 Component Breakdown

| Component | Responsibility | Stateless? | Scale Strategy |
|-----------|---------------|------------|----------------|
| **API Server** | Parse HTTP, auth routing, erasure encode/decode, stream data | Yes | Horizontal auto-scale |
| **IAM / Auth Service** | Evaluate bucket policies, ACLs, IAM policies, signature verification | Yes | Cache policies locally |
| **Metadata Service** | CRUD for object/bucket metadata, listing queries | Stateless tier; stateful store | Shard by bucket hash |
| **Namespace Service** | Global bucket name uniqueness, bucket-to-region mapping | Stateless tier; backed by global DB | Small, replicated |
| **Placement Service** | Map objects to data node sets using CRUSH-like algorithm | Yes (reads placement map) | Replicate placement map |
| **Data Service** | Route data reads/writes to correct data nodes | Yes | Horizontal |
| **Data Node** | Store/retrieve erasure-coded chunks on raw disks | Stateful | Add nodes, rebalance |
| **Garbage Collector** | Reclaim space from deleted objects, incomplete multipart uploads | Background daemon | Partition work by node |
| **Data Compactor** | Compact fragmented extent files, reclaim gaps | Background daemon | Per-node |
| **Integrity Scrubber** | Periodically verify chunk checksums, trigger repair | Background daemon | Per-node |

---

## 8. Deep Dive: Core Components

### 8.1 Data Storage and Durability

#### 8.1.1 Erasure Coding: Reed-Solomon (8,4)

Erasure coding is the backbone of achieving 11 nines of durability at reasonable cost.
Instead of storing 3 full copies (replication), we split data into `k` data chunks and
compute `m` parity chunks. Any `k` of `k+m` chunks are sufficient to reconstruct the
original data.

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    Reed-Solomon Erasure Coding (8,4)                     │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  Original Object (800 KB)                                               │
│  ┌──────────────────────────────────────────────────────────────────┐    │
│  │ AAAABBBBCCCCDDDDEEEEFFFFGGGGHHHH                                │    │
│  └──────────────────────────────────────────────────────────────────┘    │
│                              │                                          │
│                     Split into 8 data chunks                            │
│                              │                                          │
│  ┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐
│  │D0    │ │D1    │ │D2    │ │D3    │ │D4    │ │D5    │ │D6    │ │D7    │
│  │100KB │ │100KB │ │100KB │ │100KB │ │100KB │ │100KB │ │100KB │ │100KB │
│  │AAAA  │ │BBBB  │ │CCCC  │ │DDDD  │ │EEEE  │ │FFFF  │ │GGGG  │ │HHHH │
│  └──────┘ └──────┘ └──────┘ └──────┘ └──────┘ └──────┘ └──────┘ └──────┘
│                              │                                          │
│              Compute 4 parity chunks (Galois Field math)                │
│                              │                                          │
│  ┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐                                   │
│  │P0    │ │P1    │ │P2    │ │P3    │                                    │
│  │100KB │ │100KB │ │100KB │ │100KB │                                    │
│  │parity│ │parity│ │parity│ │parity│                                    │
│  └──────┘ └──────┘ └──────┘ └──────┘                                    │
│                                                                         │
│  Total stored: 12 * 100KB = 1200KB  (1.5x overhead)                    │
│  Can tolerate: up to 4 simultaneous chunk losses                        │
│  Reconstruction: any 8 of 12 chunks → full object                      │
│                                                                         │
└───────────────────────────────────────────────────────────────────────────┘
```

#### 8.1.2 Chunk Placement Across Failure Domains

Each of the 12 chunks must be placed on different failure domains to maximize durability:

```
┌─── Region: us-east ──────────────────────────────────────────────────────┐
│                                                                          │
│  ┌─── AZ-1 ────────────────┐   ┌─── AZ-2 ────────────────┐             │
│  │                          │   │                          │             │
│  │  ┌── Rack A ──────────┐  │   │  ┌── Rack C ──────────┐  │            │
│  │  │ Node-1: [D0]       │  │   │  │ Node-5: [D4]       │  │            │
│  │  │ Node-2: [D1]       │  │   │  │ Node-6: [D5]       │  │            │
│  │  └────────────────────┘  │   │  └────────────────────┘  │            │
│  │                          │   │                          │             │
│  │  ┌── Rack B ──────────┐  │   │  ┌── Rack D ──────────┐  │            │
│  │  │ Node-3: [D2]       │  │   │  │ Node-7: [D6]       │  │            │
│  │  │ Node-4: [D3]       │  │   │  │ Node-8: [D7]       │  │            │
│  │  └────────────────────┘  │   │  └────────────────────┘  │            │
│  │                          │   │                          │             │
│  └──────────────────────────┘   └──────────────────────────┘            │
│                                                                          │
│  ┌─── AZ-3 ────────────────┐                                            │
│  │                          │   Failure tolerance:                       │
│  │  ┌── Rack E ──────────┐  │   - Any 4 disks:     SURVIVES            │
│  │  │ Node-9:  [P0]      │  │   - Any 4 nodes:     SURVIVES            │
│  │  │ Node-10: [P1]      │  │   - Any 2 racks:     SURVIVES            │
│  │  └────────────────────┘  │   - Any 1 AZ:        SURVIVES            │
│  │                          │   - 2 AZ failure:     at risk (5-8 chunks │
│  │  ┌── Rack F ──────────┐  │                       could be lost)      │
│  │  │ Node-11: [P2]      │  │                                           │
│  │  │ Node-12: [P3]      │  │                                           │
│  │  └────────────────────┘  │                                           │
│  │                          │                                           │
│  └──────────────────────────┘                                           │
│                                                                          │
└──────────────────────────────────────────────────────────────────────────┘
```

#### 8.1.3 Durability Calculation

```
Given:
  - 12 chunks per object (8 data + 4 parity)
  - Annual disk failure rate (AFR): 2%
  - Mean time to repair (MTTR): 4 hours
  - Object is lost only if > 4 chunks fail simultaneously

P(losing an object) = C(12,5) * (AFR * MTTR/8760)^5 * (1 - AFR * MTTR/8760)^7

  AFR * MTTR/8760 = 0.02 * 4/8760 = 9.13e-6  (prob of a disk being down at any moment)

  P = 792 * (9.13e-6)^5 * (0.999991)^7
    = 792 * 6.8e-26 * 0.99994
    = 5.4e-23

  Annual durability = 1 - 5.4e-23 = 99.9999999999999999999999%  (>22 nines!)

  Even with correlated failures (whole-node, whole-rack), multi-AZ placement
  ensures the effective durability stays well above 11 nines.
```

#### 8.1.4 Data Node Internal Architecture

```
┌─── Data Node ──────────────────────────────────────────────────────────┐
│                                                                        │
│  ┌─── Node Manager ─────────────────────────────────────────────────┐  │
│  │  - Heartbeat to Placement Service (every 10s)                    │  │
│  │  - Reports: disk health, capacity, I/O load                      │  │
│  │  - Manages chunk lifecycle: write, read, delete, repair          │  │
│  └──────────────────────────────────────────────────────────────────┘  │
│                                                                        │
│  ┌─── Disk 0 ──────────┐  ┌─── Disk 1 ──────────┐       ┌─ Disk 11 ─┐│
│  │                      │  │                      │       │           ││
│  │ ┌── Extent File 0 ─┐│  │ ┌── Extent File 0 ─┐│       │  ...      ││
│  │ │ [chunk][chunk]... ││  │ │ [chunk][chunk]... ││       │           ││
│  │ │ (1 GB segment)    ││  │ │ (1 GB segment)    ││       │           ││
│  │ └──────────────────┘│  │ └──────────────────┘│       │           ││
│  │                      │  │                      │       │           ││
│  │ ┌── Extent File 1 ─┐│  │ ┌── Extent File 1 ─┐│       │           ││
│  │ │ [chunk][chunk]... ││  │ │ [chunk][chunk]... ││       │           ││
│  │ └──────────────────┘│  │ └──────────────────┘│       │           ││
│  │                      │  │                      │       │           ││
│  │ ┌── Chunk Index ───┐│  │ ┌── Chunk Index ───┐│       │           ││
│  │ │ chunk_id → offset ││  │ │ chunk_id → offset ││       │           ││
│  │ │ (RocksDB / LevelDB)│  │ │ (RocksDB)        ││       │           ││
│  │ └──────────────────┘│  │ └──────────────────┘│       │           ││
│  │                      │  │                      │       │           ││
│  │ Capacity: 16 TB     │  │ Capacity: 16 TB     │       │ 16 TB     ││
│  └──────────────────────┘  └──────────────────────┘       └───────────┘│
│                                                                        │
│  Total raw: 12 x 16 TB = 192 TB                                       │
│  Usable (~80%): ~154 TB                                                │
│                                                                        │
└────────────────────────────────────────────────────────────────────────┘
```

### 8.2 Metadata Service

#### 8.2.1 Architecture

```
┌──────────────────────────────────────────────────────────────────────────┐
│                        Metadata Service                                  │
├──────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  ┌─── Stateless Metadata Router ────────────────────────────────────┐   │
│  │  - Routes requests to correct shard based on hash(bucket_id)     │   │
│  │  - Caches shard map from etcd                                    │   │
│  │  - Handles read/write splitting                                  │   │
│  └───────────────┬───────────────────────┬──────────────────────────┘   │
│                  │                       │                               │
│     ┌────────────▼────────┐   ┌──────────▼──────────┐                   │
│     │   Shard 0           │   │   Shard 1           │    ... Shard N    │
│     │   (Raft group)      │   │   (Raft group)      │                   │
│     │                     │   │                     │                   │
│     │ ┌─ Leader ────────┐ │   │ ┌─ Leader ────────┐ │                   │
│     │ │ RocksDB         │ │   │ │ RocksDB         │ │                   │
│     │ │ bucket_0..999   │ │   │ │ bucket_1000..   │ │                   │
│     │ └─────────────────┘ │   │ └─────────────────┘ │                   │
│     │ ┌─ Follower 1 ────┐ │   │ ┌─ Follower 1 ────┐ │                   │
│     │ │ RocksDB (replica)│ │   │ │ RocksDB (replica)│ │                   │
│     │ └─────────────────┘ │   │ └─────────────────┘ │                   │
│     │ ┌─ Follower 2 ────┐ │   │ ┌─ Follower 2 ────┐ │                   │
│     │ │ RocksDB (replica)│ │   │ │ RocksDB (replica)│ │                   │
│     │ └─────────────────┘ │   │ └─────────────────┘ │                   │
│     └─────────────────────┘   └─────────────────────┘                   │
│                                                                          │
└──────────────────────────────────────────────────────────────────────────┘
```

#### 8.2.2 Key Design for Efficient Listing

Objects within a bucket are stored with a composite key that enables efficient prefix
listing:

```
Key format in RocksDB:
  [bucket_id (8 bytes)][object_key (variable)][version_id (16 bytes)]

Example entries (sorted lexicographically):
  [bucket_42]["photos/2025/dec/img001.jpg"][v1]  → metadata
  [bucket_42]["photos/2025/dec/img002.jpg"][v1]  → metadata
  [bucket_42]["photos/2026/jan/img001.jpg"][v1]  → metadata
  [bucket_42]["photos/2026/jan/img001.jpg"][v2]  → metadata  (new version)
  [bucket_42]["photos/2026/jan/img002.jpg"][v1]  → metadata
  [bucket_42]["videos/clip1.mp4"][v1]            → metadata

List with prefix="photos/2026/" and delimiter="/":
  → Seek to [bucket_42]["photos/2026/"]
  → Scan until key no longer starts with "photos/2026/"
  → Group by delimiter: CommonPrefixes = ["photos/2026/jan/"]
  → Return grouped result
```

#### 8.2.3 Metadata Versioning

```
Versioning States per Bucket:

  DISABLED (default):
    PUT key → overwrite single metadata entry
    DELETE key → remove metadata entry (data GC'd later)

  ENABLED:
    PUT key → insert new version with generated version_id
    DELETE key → insert "delete marker" version
    GET key → return latest non-delete-marker version
    GET key?versionId=X → return specific version

  SUSPENDED:
    PUT key → overwrite the "null" version only
    Existing versions preserved

┌─────────────────────────────────────────────────────────┐
│ Key: "report.pdf", Versioning: ENABLED                  │
├─────────────────────────────────────────────────────────┤
│ Version v3 (latest) ── DELETE MARKER                    │
│ Version v2           ── 2.1 MB, modified 2026-03-15     │
│ Version v1           ── 1.8 MB, modified 2026-01-10     │
├─────────────────────────────────────────────────────────┤
│ GET report.pdf → 404 (delete marker)                    │
│ GET report.pdf?versionId=v2 → 200 OK, returns v2       │
│ DELETE report.pdf?versionId=v3 → removes delete marker  │
│ GET report.pdf → 200 OK, returns v2 (now latest)        │
└─────────────────────────────────────────────────────────┘
```

### 8.3 Data Placement and Rebalancing

#### 8.3.1 CRUSH-Inspired Placement Algorithm

Instead of maintaining a massive lookup table mapping each object to its nodes, we use a
deterministic algorithm (inspired by Ceph's CRUSH) that computes placement from the object
ID and a small cluster map.

```
┌─────────────────────────────────────────────────────────────────────────┐
│                     Placement Algorithm                                  │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  Input:  object_id (UUID), cluster_map, replication_config              │
│  Output: ordered list of 12 node IDs (one per chunk)                    │
│                                                                         │
│  Step 1: Compute placement group (PG)                                   │
│          pg_id = hash(object_id) % num_placement_groups                  │
│          (num_placement_groups = 4096, tuned per cluster size)           │
│                                                                         │
│  Step 2: CRUSH algorithm maps PG → 12 nodes                            │
│          - Start at root of cluster topology tree                       │
│          - For each chunk i (0..11):                                    │
│            - Descend tree: root → AZ → rack → node                     │
│            - At each level, select bucket using hash(pg_id, i, level)   │
│            - Enforce failure domain separation:                         │
│              chunks spread across >= 3 AZs, >= 6 racks                  │
│            - Skip nodes that are down or over-capacity                  │
│                                                                         │
│  Step 3: Return [node_1, node_2, ..., node_12]                         │
│                                                                         │
│  Properties:                                                            │
│  - Deterministic: same input always produces same output                │
│  - Minimal data movement when nodes added/removed                       │
│  - No central lookup table needed                                       │
│  - O(log N) computation per object                                      │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

#### 8.3.2 Cluster Topology Tree

```
                          ┌──────────┐
                          │  Root    │
                          │ (cluster)│
                          └────┬─────┘
                   ┌───────────┼───────────┐
                   │           │           │
              ┌────▼───┐  ┌───▼────┐  ┌───▼────┐
              │  AZ-1  │  │  AZ-2  │  │  AZ-3  │
              └────┬───┘  └───┬────┘  └───┬────┘
              ┌────┼────┐    ┌┼────┐    ┌──┼────┐
              │    │    │    ││    │    │  │    │
           ┌──▼┐┌─▼─┐┌─▼┐ ┌▼─┐┌─▼─┐ ┌▼──┐┌──▼┐┌──▼┐
           │R-A││R-B││R-C│ │R-D││R-E│ │R-F││R-G││R-H│
           └─┬─┘└─┬─┘└─┬┘ └─┬─┘└─┬─┘ └─┬─┘└─┬─┘└─┬┘
          ┌──┼──┐  │  ┌─┼─┐  │  ┌─┼─┐  │  ┌─┼─┐   │
          │  │  │  │  │ │ │  │  │ │ │  │  │ │ │   │
         N1 N2 N3 N4 N5 N6 N7 N8 N9 N10 N11 N12 N13 ...
```

#### 8.3.3 Rebalancing on Node Add/Remove

```
Before: 3 nodes, 9 PGs                After: 4 nodes, 9 PGs (add Node-D)
┌──────────┬──────────┬──────────┐     ┌──────────┬──────────┬──────────┬──────────┐
│ Node-A   │ Node-B   │ Node-C   │     │ Node-A   │ Node-B   │ Node-C   │ Node-D   │
│ PG: 0,1,2│ PG: 3,4,5│ PG: 6,7,8│     │ PG: 0,1  │ PG: 3,4  │ PG: 6,7  │ PG: 2,5,8│
│ (3 PGs)  │ (3 PGs)  │ (3 PGs)  │     │ (2 PGs)  │ (2 PGs)  │ (2 PGs)  │ (3 PGs)  │
└──────────┴──────────┴──────────┘     └──────────┴──────────┴──────────┴──────────┘

Key properties:
  - Only ~1/N of data moves when adding Nth node (minimal disruption)
  - Rebalancing is background, throttled to avoid impacting live traffic
  - Placement map version is incremented; old and new maps coexist during transition
  - Reads try new placement first, fall back to old placement during migration
```

### 8.4 Multipart Upload

#### 8.4.1 Flow

```
┌───────────────────────────────────────────────────────────────────────────┐
│                      Multipart Upload: 10 GB File                        │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                           │
│  Client                    API Server              Data Layer             │
│    │                           │                       │                  │
│    │── POST /bucket/key?uploads ──▶│                    │                  │
│    │◀── uploadId=U1 ──────────│                       │                  │
│    │                           │                       │                  │
│    │  ┌─ Split 10 GB into 100 MB parts (100 parts) ─┐ │                  │
│    │  │ Parts can be uploaded in parallel             │ │                  │
│    │  └──────────────────────────────────────────────┘ │                  │
│    │                           │                       │                  │
│    │── PUT part 1 (100 MB) ──▶│──erasure code + store──▶│                │
│    │── PUT part 2 (100 MB) ──▶│──erasure code + store──▶│  (parallel)   │
│    │── PUT part 3 (100 MB) ──▶│──erasure code + store──▶│               │
│    │   ...                     │                       │                  │
│    │── PUT part 100 ─────────▶│──erasure code + store──▶│               │
│    │                           │                       │                  │
│    │◀── ETag for each part ───│                       │                  │
│    │                           │                       │                  │
│    │── POST complete ─────────▶│                       │                  │
│    │   (list of part ETags)    │──compose metadata──────▶│               │
│    │                           │  (link all parts as    │                  │
│    │                           │   one logical object)  │                  │
│    │◀── 200 OK, final ETag ───│                       │                  │
│    │                           │                       │                  │
│                                                                           │
│  Part metadata stored temporarily:                                        │
│  ┌──────────────────────────────────────────────────┐                    │
│  │ upload_id: U1                                    │                    │
│  │ bucket: my-bucket                                │                    │
│  │ key: large-file.tar.gz                           │                    │
│  │ parts:                                           │                    │
│  │   part 1: etag=abc, size=100MB, chunk_locs=[...]│                    │
│  │   part 2: etag=def, size=100MB, chunk_locs=[...]│                    │
│  │   ...                                            │                    │
│  │ created_at: 2026-04-09T10:00:00Z                 │                    │
│  │ expires_at: 2026-04-16T10:00:00Z (7-day TTL)     │                    │
│  └──────────────────────────────────────────────────┘                    │
│                                                                           │
└───────────────────────────────────────────────────────────────────────────┘
```

#### 8.4.2 Failure Handling in Multipart Upload

```
Scenario 1: Part upload fails mid-transfer
  → Client retries that specific part (idempotent by part number)
  → Server discards incomplete chunk data
  → Same part number can be re-uploaded any number of times

Scenario 2: Client crashes, upload never completed
  → Incomplete upload metadata has TTL (default 7 days)
  → Lifecycle policy: AbortIncompleteMultipartUpload (configurable days)
  → GC daemon scans for expired uploads, deletes orphaned chunks

Scenario 3: Complete request fails after partial metadata commit
  → Retry the complete request (idempotent with same uploadId + parts)
  → If parts list differs, reject with error

Scenario 4: Part uploaded to a node that crashes
  → Part data is erasure-coded across 12 nodes
  → If < 5 nodes for that part fail, data is recoverable
  → Scrubber detects missing chunks, triggers repair from parity
```

---

## 9. Data Partitioning and Sharding

### 9.1 Data Layer Partitioning

```
┌──────────────────────────────────────────────────────────────────────┐
│                    Data Partitioning Strategy                         │
├──────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  Object Data: Placement Groups (PGs)                                 │
│  ─────────────────────────────────────                               │
│  - 4096 placement groups distributed across storage nodes            │
│  - PG assignment: pg_id = hash(object_id) % 4096                     │
│  - Each PG maps to 12 nodes via CRUSH algorithm                      │
│  - PG is the unit of rebalancing (not individual objects)            │
│                                                                      │
│  ┌─────────┐  ┌─────────┐  ┌─────────┐       ┌─────────┐           │
│  │ PG-0    │  │ PG-1    │  │ PG-2    │  ...  │ PG-4095 │           │
│  │ → 12    │  │ → 12    │  │ → 12    │       │ → 12    │           │
│  │ nodes   │  │ nodes   │  │ nodes   │       │ nodes   │           │
│  └─────────┘  └─────────┘  └─────────┘       └─────────┘           │
│                                                                      │
│  Metadata: Sharded by Bucket Hash                                    │
│  ─────────────────────────────────                                   │
│  - Shard key: hash(bucket_id)                                        │
│  - 256 logical shards, each a Raft group (3 replicas)                │
│  - All objects in a bucket are on the same shard                     │
│    (enables efficient listing within a bucket)                       │
│  - Hot buckets: further sub-shard by key prefix                      │
│                                                                      │
│  Bucket Metadata: Sharded by Account                                 │
│  ────────────────────────────────                                    │
│  - Relatively small dataset (~100M buckets)                          │
│  - Sharded by hash(account_id)                                       │
│  - Vitess-managed MySQL cluster                                      │
│                                                                      │
└──────────────────────────────────────────────────────────────────────┘
```

### 9.2 Cross-Region Replication Architecture

```
┌─── Region: us-east-1 ──────────────────┐   ┌─── Region: eu-west-1 ──────────────────┐
│                                         │   │                                         │
│  Source Bucket: "my-bucket"             │   │  Destination Bucket: "my-bucket-replica"│
│                                         │   │                                         │
│  ┌─────────────────────┐               │   │  ┌─────────────────────┐               │
│  │ Object Store        │               │   │  │ Object Store        │               │
│  │ + Metadata          │               │   │  │ + Metadata          │               │
│  └─────────┬───────────┘               │   │  └─────────▲───────────┘               │
│            │                            │   │            │                            │
│  ┌─────────▼───────────┐               │   │  ┌─────────┴───────────┐               │
│  │ Replication Queue   │───────────────────────▶ Replication Worker  │               │
│  │ (Kafka / Kinesis)   │  async, ordered │   │  │ (applies changes)  │               │
│  │                     │  per-key         │   │  └─────────────────────┘               │
│  │ Events:             │               │   │                                         │
│  │  PUT key=X, ver=v3  │               │   │  Conflict resolution:                   │
│  │  DELETE key=Y       │               │   │  - Last-writer-wins (by timestamp)      │
│  │  PUT key=Z, ver=v1  │               │   │  - Or source-wins (configurable)        │
│  └─────────────────────┘               │   │                                         │
│                                         │   │                                         │
└─────────────────────────────────────────┘   └─────────────────────────────────────────┘

Replication metrics:
  - Replication lag: p50 < 15 min, p99 < 1 hour
  - Bandwidth: throttled to avoid impacting primary traffic
  - Filtering: replicate only objects matching prefix/tag rules
```

---

## 10. Caching Strategy

### 10.1 Multi-Layer Caching Architecture

```
┌──────────────────────────────────────────────────────────────────────────┐
│                          Caching Layers                                   │
├──────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  Layer 1: CDN Edge Cache (for public/cacheable objects)                  │
│  ┌──────────────────────────────────────────────────────────────────┐   │
│  │  - Cache-Control / Expires headers honored                       │   │
│  │  - Pre-signed URL objects: NOT cached (unique per request)       │   │
│  │  - Hit ratio: ~60-80% for static content workloads               │   │
│  │  - Invalidation: TTL-based or explicit purge API                 │   │
│  └──────────────────────────────────────────────────────────────────┘   │
│                                                                          │
│  Layer 2: API Server In-Memory Cache                                     │
│  ┌──────────────────────────────────────────────────────────────────┐   │
│  │  - Bucket metadata: policy, CORS, versioning config              │   │
│  │  - IAM policy evaluation results (short TTL: 60s)                │   │
│  │  - Routing tables: shard map, placement map                      │   │
│  │  - Size: ~1 GB per API server                                    │   │
│  │  - Invalidation: watch on etcd for config changes                │   │
│  └──────────────────────────────────────────────────────────────────┘   │
│                                                                          │
│  Layer 3: Metadata Cache (distributed, Redis/Memcached)                  │
│  ┌──────────────────────────────────────────────────────────────────┐   │
│  │  - Hot object metadata: avoid hitting metadata DB                │   │
│  │  - Bucket listing results (prefix queries, short TTL: 5s)        │   │
│  │  - Cache key: hash(bucket_id, object_key, version_id)            │   │
│  │  - Size: ~10 TB distributed across cluster                       │   │
│  │  - Write-through: PUT/DELETE invalidates cache entry             │   │
│  │  - Hit ratio: ~90% for metadata lookups                          │   │
│  └──────────────────────────────────────────────────────────────────┘   │
│                                                                          │
│  Layer 4: Data Node Page Cache (OS-level)                                │
│  ┌──────────────────────────────────────────────────────────────────┐   │
│  │  - OS page cache for recently accessed extent files              │   │
│  │  - Hot objects served from memory, no disk I/O                   │   │
│  │  - Large objects: direct I/O bypasses page cache                 │   │
│  │  - Per-node: 128 GB RAM, ~64 GB for page cache                  │   │
│  └──────────────────────────────────────────────────────────────────┘   │
│                                                                          │
└──────────────────────────────────────────────────────────────────────────┘
```

### 10.2 Cache Invalidation Strategy

```
Write path (PUT/DELETE):
  1. Write to metadata store (source of truth)
  2. Invalidate metadata cache entry (delete from Redis)
  3. Subsequent reads go to metadata store (miss), then populate cache

Strong consistency requirement:
  - No stale reads after a successful PUT
  - Solution: metadata cache uses write-through invalidation
  - Read path: check cache → if miss, read from metadata store leader
  - For listing: short TTL (5s) since listings are eventually consistent
    for performance (configurable)
```

---

## 11. Replication and Consistency

### 11.1 Strong Read-After-Write Consistency

Amazon S3 achieved strong read-after-write consistency in December 2020. Here is how this
can be designed.

```
┌──────────────────────────────────────────────────────────────────────────┐
│              Strong Read-After-Write Consistency Protocol                 │
├──────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  Approach: "Witness" protocol on metadata                                │
│                                                                          │
│  PUT object flow:                                                        │
│    1. Write data chunks to data nodes                                    │
│    2. Write metadata to metadata store (Raft-based, linearizable)        │
│    3. Metadata write commits only when Raft leader + majority ACK        │
│    4. Return success to client only after metadata commit                │
│                                                                          │
│  GET object flow:                                                        │
│    1. Read metadata from Raft leader (linearizable read)                 │
│    2. Leader confirms it is still leader (lease check / read index)      │
│    3. Return latest committed version                                    │
│                                                                          │
│  Why this guarantees read-after-write:                                   │
│    - PUT returns only after metadata is committed in Raft                │
│    - GET always reads from leader with confirmed leadership              │
│    - Therefore, any GET after a successful PUT sees the new version      │
│                                                                          │
│  Performance optimization:                                               │
│    - Follower reads with "read index" (avoid overloading leader)         │
│    - Follower asks leader for current commit index                       │
│    - Waits until follower's applied index >= leader's commit index       │
│    - Then serves the read locally                                        │
│                                                                          │
│  Timeline:                                                               │
│  ┌──────────────────────────────────────────────────────────────────┐   │
│  │ Client A:  PUT key=X, data=v2                                    │   │
│  │            ─────────────────────▶ committed at Raft index 42     │   │
│  │                                  │                               │   │
│  │ Client B:  GET key=X             │                               │   │
│  │            ──────▶ read from leader at index >= 42 → returns v2  │   │
│  │                                                                  │   │
│  │ Without consistency: Client B might read from a stale follower   │   │
│  │ and see old value v1. With Raft read index, this is prevented.   │   │
│  └──────────────────────────────────────────────────────────────────┘   │
│                                                                          │
└──────────────────────────────────────────────────────────────────────────┘
```

### 11.2 Consistency Levels by Operation

```
┌───────────────────────┬──────────────────────┬──────────────────────────┐
│ Operation             │ Consistency Level    │ Implementation           │
├───────────────────────┼──────────────────────┼──────────────────────────┤
│ PUT (new object)      │ Strong R-A-W         │ Raft commit before ACK   │
│ PUT (overwrite)       │ Strong R-A-W         │ Raft commit before ACK   │
│ DELETE                │ Strong R-A-W         │ Delete marker via Raft   │
│ GET (by key)          │ Strong               │ Leader read / read index │
│ HEAD (by key)         │ Strong               │ Leader read / read index │
│ LIST (prefix)         │ Strong               │ Leader read / read index │
│ Cross-region GET      │ Eventual             │ Async replication lag    │
│ Bucket config update  │ Strong               │ Raft on bucket metadata  │
└───────────────────────┴──────────────────────┴──────────────────────────┘
```

### 11.3 Cross-Region Consistency

```
Cross-region replication is always asynchronous (eventual consistency):

  us-east-1 (primary)              eu-west-1 (replica)
       │                                │
  PUT v2 ─── committed ──┐             │
       │                  │             │
       │            replication         │
       │            queue               │
       │                  │             │
       │                  └────────────▶│ v2 applied (lag: seconds to minutes)
       │                                │
  During lag window:
    GET in us-east-1 → v2 (strong)
    GET in eu-west-1 → v1 (stale, eventually v2)

  For applications needing strong cross-region consistency:
    → Route all reads/writes to primary region
    → Or use multi-region Raft (at significant latency cost)
```

---

## 12. Fault Tolerance and Failure Handling

### 12.1 Failure Modes and Recovery

```
┌────────────────────┬─────────────────────────┬──────────────────────────────┐
│ Failure Mode       │ Detection               │ Recovery                     │
├────────────────────┼─────────────────────────┼──────────────────────────────┤
│ Single disk        │ SMART monitoring,       │ Reconstruct chunks from      │
│ failure            │ I/O errors, CRC         │ remaining 11 chunks on       │
│                    │ mismatch                │ other disks (Reed-Solomon)   │
├────────────────────┼─────────────────────────┼──────────────────────────────┤
│ Node failure       │ Heartbeat timeout       │ Mark node down in placement  │
│                    │ (30s), health checks    │ map; reads route to other    │
│                    │                         │ 11 nodes; repair copies      │
│                    │                         │ chunks to new nodes          │
├────────────────────┼─────────────────────────┼──────────────────────────────┤
│ Rack failure       │ Multiple node failures  │ 4 chunks max per rack;       │
│ (power/network)    │ in same rack            │ remaining 8+ chunks on       │
│                    │                         │ other racks suffice          │
├────────────────────┼─────────────────────────┼──────────────────────────────┤
│ AZ failure         │ Network partition or    │ Chunks spread across 3 AZs;  │
│                    │ DC-wide outage          │ losing 1 AZ = losing ~4      │
│                    │                         │ chunks; 8 remaining suffice  │
├────────────────────┼─────────────────────────┼──────────────────────────────┤
│ Region failure     │ All AZs down            │ Cross-region replication;    │
│                    │                         │ failover to replica region   │
│                    │                         │ (RPO: replication lag)       │
├────────────────────┼─────────────────────────┼──────────────────────────────┤
│ Metadata node      │ Raft leader election    │ Automatic failover to Raft   │
│ failure            │ timeout                 │ follower; new leader elected │
│                    │                         │ in < 10 seconds              │
├────────────────────┼─────────────────────────┼──────────────────────────────┤
│ Bit rot /          │ Background scrubber     │ CRC mismatch detected;       │
│ silent corruption  │ checksums every chunk   │ chunk reconstructed from     │
│                    │ every 30 days           │ parity and rewritten         │
├────────────────────┼─────────────────────────┼──────────────────────────────┤
│ Network partition  │ Split-brain detection   │ Raft requires majority;      │
│ between AZs       │ via Raft consensus      │ minority partition becomes   │
│                    │                         │ read-only or unavailable     │
└────────────────────┴─────────────────────────┴──────────────────────────────┘
```

### 12.2 Data Scrubbing and Integrity

```
┌──────────────────────────────────────────────────────────────────────────┐
│                    Background Integrity Scrubber                         │
├──────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  Purpose: Detect and repair silent data corruption (bit rot)             │
│                                                                          │
│  Process (per data node):                                                │
│  ┌────────────────────────────────────────────────────────────────┐     │
│  │  1. Iterate through all chunks on each disk                    │     │
│  │  2. For each chunk:                                            │     │
│  │     a. Read chunk data                                         │     │
│  │     b. Compute CRC32C checksum                                 │     │
│  │     c. Compare with stored checksum (in chunk index)           │     │
│  │     d. If mismatch:                                            │     │
│  │        - Mark chunk as corrupt                                 │     │
│  │        - Notify repair service                                 │     │
│  │        - Repair service reads k healthy chunks from peers      │     │
│  │        - Reed-Solomon decode to reconstruct corrupt chunk      │     │
│  │        - Write repaired chunk, update checksum                 │     │
│  │  3. Throttle I/O to 10% of disk bandwidth (low priority)      │     │
│  │  4. Complete full scan every 30 days                           │     │
│  └────────────────────────────────────────────────────────────────┘     │
│                                                                          │
│  Scrubbing rate per node:                                                │
│  - 154 TB usable / 30 days = ~5.1 TB/day = ~60 MB/s continuous          │
│  - At 10% throttle: ~6 MB/s background I/O                              │
│                                                                          │
│  Metrics tracked:                                                        │
│  - Chunks scanned per day                                                │
│  - Corrupt chunks detected (should be near zero)                         │
│  - Repair success rate                                                   │
│  - Repair latency (time from detection to fixed)                         │
│                                                                          │
└──────────────────────────────────────────────────────────────────────────┘
```

### 12.3 Automatic Repair Pipeline

```
  Failure Detected
       │
       ▼
  ┌──────────────┐    ┌───────────────┐    ┌──────────────────┐
  │ Repair Queue │───▶│ Repair Worker │───▶│ Reconstruct Chunk│
  │ (priority    │    │ (per-node     │    │ from k healthy   │
  │  queue)      │    │  daemon)      │    │ chunks via RS    │
  └──────────────┘    └───────────────┘    └────────┬─────────┘
                                                    │
                                                    ▼
                                           ┌──────────────────┐
                                           │ Write to New Node│
                                           │ (selected by     │
                                           │  placement svc)  │
                                           └────────┬─────────┘
                                                    │
                                                    ▼
                                           ┌──────────────────┐
                                           │ Update Metadata  │
                                           │ (new chunk loc)  │
                                           └──────────────────┘

  Priority levels:
    CRITICAL: Object has <= k healthy chunks (at risk of data loss)
    HIGH:     Object has k+1 healthy chunks
    MEDIUM:   Object has k+2 healthy chunks
    LOW:      Object has k+3 healthy chunks (still fully redundant)

  Repair throughput:
    - Single disk failure (16 TB): ~4 hours at 1 GB/s network per node
    - Node failure (192 TB): ~8 hours with parallel repair from 100+ peers
    - Goal: repair before a second correlated failure
```

---

## 13. Scalability

### 13.1 Scaling Dimensions

```
┌──────────────────────────────────────────────────────────────────────────┐
│                        Scalability Strategy                              │
├──────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  ┌─ Storage Capacity ────────────────────────────────────────────────┐  │
│  │  Current: 300 nodes x 154 TB = ~46 PB                            │  │
│  │  Scale to 1 EB:                                                   │  │
│  │    - Add nodes (linear scaling)                                   │  │
│  │    - Increase PG count (4096 → 16384) as cluster grows            │  │
│  │    - Rebalance existing PGs across new nodes                      │  │
│  │    - No changes to API servers or metadata layer                  │  │
│  │    - Timeline: add 50 nodes/week, reach 1 EB in ~6 months        │  │
│  └───────────────────────────────────────────────────────────────────┘  │
│                                                                          │
│  ┌─ Request Throughput ──────────────────────────────────────────────┐  │
│  │  API servers: stateless, auto-scale behind LB                     │  │
│  │    - Current: 1,100 servers for 11M req/sec                       │  │
│  │    - Scale: add more servers (linear)                             │  │
│  │    - CPU-bound (erasure encode/decode): ~10K req/sec per server   │  │
│  │                                                                   │  │
│  │  Read throughput bottleneck: disk I/O on data nodes               │  │
│  │    - Mitigation: CDN for hot objects, page cache for warm data    │  │
│  │    - SSD cache tier for frequently accessed small objects         │  │
│  └───────────────────────────────────────────────────────────────────┘  │
│                                                                          │
│  ┌─ Metadata Scale ──────────────────────────────────────────────────┐  │
│  │  Current: 256 shards, 100 TB total metadata                       │  │
│  │  At 1 trillion objects: 1 PB metadata                             │  │
│  │    - Increase shard count: 256 → 1024 → 4096                     │  │
│  │    - Each shard: ~250 GB (manageable for RocksDB)                 │  │
│  │    - Shard splitting: transparent to clients                      │  │
│  │                                                                   │  │
│  │  Hot bucket problem (single bucket with billions of objects):     │  │
│  │    - Sub-shard by key prefix hash within bucket                   │  │
│  │    - Listing queries fan out across sub-shards                    │  │
│  └───────────────────────────────────────────────────────────────────┘  │
│                                                                          │
│  ┌─ Network Bandwidth ──────────────────────────────────────────────┐  │
│  │  Per data node: 25 Gbps NIC (~3 GB/s)                            │  │
│  │  Cluster total: 300 nodes x 25 Gbps = 7.5 Tbps                   │  │
│  │  Read throughput: 1 TB/sec requires ~8 Tbps (with coding overhead)│  │
│  │    - Solution: tiered network, spine-leaf topology                │  │
│  │    - Spine switches: 100 Gbps uplinks                             │  │
│  └───────────────────────────────────────────────────────────────────┘  │
│                                                                          │
└──────────────────────────────────────────────────────────────────────────┘
```

### 13.2 Storage Class Tiering

```
┌──────────────────────────────────────────────────────────────────────────┐
│                     Storage Classes and Tiering                          │
├──────────────┬──────────┬───────────┬────────────┬──────────┬───────────┤
│ Class        │ Media    │ Erasure   │ Latency    │ Cost/GB  │ Durability│
│              │          │ Scheme    │ (GET p50)  │ /month   │           │
├──────────────┼──────────┼───────────┼────────────┼──────────┼───────────┤
│ Standard     │ HDD+SSD  │ 8+4 (3AZ)│ <50ms      │ $0.023   │ 11 nines  │
│              │ cache    │           │            │          │           │
├──────────────┼──────────┼───────────┼────────────┼──────────┼───────────┤
│ Infrequent   │ HDD      │ 8+4 (3AZ)│ <50ms      │ $0.0125  │ 11 nines  │
│ Access (IA)  │          │           │            │ +retriev.│           │
├──────────────┼──────────┼───────────┼────────────┼──────────┼───────────┤
│ One-Zone IA  │ HDD      │ 8+4 (1AZ)│ <50ms      │ $0.010   │ 11 nines* │
│              │          │           │            │          │ *same AZ  │
├──────────────┼──────────┼───────────┼────────────┼──────────┼───────────┤
│ Glacier      │ HDD      │ 12+6     │ 1-5 min    │ $0.004   │ 11 nines  │
│ (Archive)    │ (dense)  │ (cold)   │ (restore)  │          │           │
├──────────────┼──────────┼───────────┼────────────┼──────────┼───────────┤
│ Deep Archive │ Tape +   │ 12+6     │ 12-48 hrs  │ $0.00099 │ 11 nines  │
│              │ cold HDD │ (offline)│ (restore)  │          │           │
└──────────────┴──────────┴───────────┴────────────┴──────────┴───────────┘

Lifecycle Transition Example:
  ┌────────┐  30 days  ┌────────┐  90 days  ┌────────┐  365 days ┌──────────┐
  │Standard│──────────▶│  IA    │──────────▶│Glacier │──────────▶│Deep      │
  │        │           │        │           │        │           │Archive   │
  └────────┘           └────────┘           └────────┘           └──────────┘
```

---

## 14. Monitoring and Observability

### 14.1 Key Metrics Dashboard

```
┌──────────────────────────────────────────────────────────────────────────┐
│                    Object Storage Monitoring                             │
├──────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  ┌─ Durability Metrics ──────────────────────────────────────────────┐  │
│  │  - chunks_healthy_ratio:          target > 99.99%                 │  │
│  │  - chunks_degraded (< 12 copies): alert if > 0.1% of chunks      │  │
│  │  - chunks_critical (< 9 copies):  page on-call immediately       │  │
│  │  - repair_queue_depth:            should trend toward 0           │  │
│  │  - repair_throughput_bytes/sec:   capacity planning               │  │
│  │  - scrub_errors_total:            corrupt chunks found            │  │
│  └───────────────────────────────────────────────────────────────────┘  │
│                                                                          │
│  ┌─ Availability Metrics ────────────────────────────────────────────┐  │
│  │  - request_success_rate:          target > 99.99% (per 5m window) │  │
│  │  - 5xx_error_rate:                alert if > 0.01%                │  │
│  │  - nodes_down_count:              alert if > 5% of cluster        │  │
│  │  - metadata_leader_elections/hr:  alert if > 2                    │  │
│  └───────────────────────────────────────────────────────────────────┘  │
│                                                                          │
│  ┌─ Performance Metrics ─────────────────────────────────────────────┐  │
│  │  - get_latency_p50:               target < 50ms                   │  │
│  │  - get_latency_p99:               target < 200ms                  │  │
│  │  - put_latency_p50:               target < 100ms                  │  │
│  │  - put_latency_p99:               target < 500ms                  │  │
│  │  - time_to_first_byte_p50:        target < 20ms                   │  │
│  │  - erasure_encode_time_p99:       compute bottleneck indicator    │  │
│  │  - metadata_lookup_latency_p99:   target < 10ms                   │  │
│  └───────────────────────────────────────────────────────────────────┘  │
│                                                                          │
│  ┌─ Capacity Metrics ────────────────────────────────────────────────┐  │
│  │  - total_storage_used_bytes:      capacity planning               │  │
│  │  - storage_utilization_percent:   alert if > 80%                  │  │
│  │  - objects_total:                 trend tracking                   │  │
│  │  - daily_ingest_bytes:            growth rate                     │  │
│  │  - gc_reclaimed_bytes/day:        space reclamation rate          │  │
│  │  - disk_utilization per node:     hotspot detection               │  │
│  └───────────────────────────────────────────────────────────────────┘  │
│                                                                          │
│  ┌─ Operational Metrics ─────────────────────────────────────────────┐  │
│  │  - rebalance_progress_percent:    during node add/remove          │  │
│  │  - multipart_uploads_incomplete:  GC candidate count              │  │
│  │  - cross_region_replication_lag:  SLA tracking                    │  │
│  │  - api_server_cpu_utilization:    auto-scale trigger (> 70%)      │  │
│  └───────────────────────────────────────────────────────────────────┘  │
│                                                                          │
│  Alerting Tiers:                                                         │
│  ┌─────────────┬─────────────────────────────────────────────────────┐  │
│  │ P0 (PAGE)   │ chunks_critical > 0, 5xx_rate > 1%, node_down > 20%│  │
│  │ P1 (URGENT) │ durability < 99.9999%, repair_queue > 1M           │  │
│  │ P2 (WARNING)│ storage_util > 80%, replication_lag > 1h            │  │
│  │ P3 (INFO)   │ scrub_errors > 0, daily_ingest exceeds forecast    │  │
│  └─────────────┴─────────────────────────────────────────────────────┘  │
│                                                                          │
└──────────────────────────────────────────────────────────────────────────┘
```

### 14.2 Distributed Tracing

```
Trace: PUT /v1/my-bucket/large-file.bin (multipart, 1 GB)

Span 1: api_server.handle_put               [0ms ────────────── 1200ms]
  Span 1.1: auth.evaluate_policy             [2ms ── 15ms]
  Span 1.2: namespace.resolve_bucket         [16ms ── 22ms]
  Span 1.3: placement.get_nodes              [23ms ── 35ms]
  Span 1.4: data.erasure_encode              [36ms ─── 180ms]
  Span 1.5: data.write_chunks (parallel)     [181ms ────────── 1100ms]
    Span 1.5.1: write_chunk_to_dn1           [181ms ──── 650ms]
    Span 1.5.2: write_chunk_to_dn3           [181ms ─────── 800ms]
    Span 1.5.3: write_chunk_to_dn5           [181ms ───────── 950ms]
    ... (12 parallel writes)
    Span 1.5.12: write_chunk_to_dn23         [181ms ────────── 1100ms]
  Span 1.6: metadata.store_object            [1101ms ── 1180ms]
  Span 1.7: response.send                    [1181ms ── 1200ms]

Attributes: bucket=my-bucket, key=large-file.bin, size=1073741824,
            storage_class=STANDARD, erasure_scheme=8+4, chunks=12,
            slowest_node=dn23 (919ms)
```

---

## 15. Trade-offs and Design Decisions

### 15.1 Key Trade-offs

```
┌──────────────────────────────────────────────────────────────────────────┐
│ Trade-off 1: Erasure Coding vs Replication                               │
├──────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  We chose: Erasure Coding (Reed-Solomon 8,4)                            │
│                                                                          │
│  Pros:                                      Cons:                        │
│  + 50% less storage cost (1.5x vs 3x)      - Higher CPU for encode/     │
│  + Higher fault tolerance (4 vs 2 failures)   decode                     │
│  + Better durability mathematically         - Higher read latency (need  │
│                                               8 chunks vs 1 replica)    │
│                                             - More complex repair logic  │
│                                             - Small objects: overhead     │
│                                               disproportionate           │
│                                                                          │
│  Mitigation for cons:                                                    │
│  - SIMD-optimized erasure coding libraries (ISA-L): ~10 GB/s per core   │
│  - Read from closest 8 nodes, latency dominated by slowest              │
│  - Small objects (<1 MB): batch into larger extent files                 │
│  - Hot objects: replicate to SSD cache tier for fast reads               │
│                                                                          │
└──────────────────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────────────────┐
│ Trade-off 2: Strong vs Eventual Consistency                              │
├──────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  We chose: Strong read-after-write (within region)                      │
│                                                                          │
│  Pros:                                      Cons:                        │
│  + Simpler application logic               - Higher metadata read        │
│  + No stale reads after writes               latency (must go to        │
│  + Eliminates class of subtle bugs           leader or use read index)  │
│  + Matches S3's actual behavior            - Cannot cache metadata      │
│                                               aggressively              │
│                                             - Cross-region: still        │
│                                               eventual (acceptable)     │
│                                                                          │
│  Why it works at scale:                                                  │
│  - Metadata is small; Raft overhead is microseconds per operation       │
│  - Read index optimization avoids overloading leader                     │
│  - 90%+ of reads served from metadata cache (cache invalidation         │
│    ensures consistency)                                                  │
│                                                                          │
└──────────────────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────────────────┐
│ Trade-off 3: Flat Namespace vs Hierarchical                              │
├──────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  We chose: Flat namespace (keys are opaque strings)                     │
│                                                                          │
│  Pros:                                      Cons:                        │
│  + Simpler metadata model (just KV store)  - "Directories" are          │
│  + No rename overhead (rename = copy+delete  simulated with prefix      │
│    in hierarchical FS)                       + delimiter                │
│  + Infinite nesting depth                  - LIST with delimiter has     │
│  + No directory inode overhead               O(n) scan cost within      │
│                                              prefix range               │
│  S3 uses this approach:                    - No atomic "directory        │
│    "photos/2026/jan/img.jpg" is just a       rename"                    │
│    key, not a path                                                       │
│                                                                          │
└──────────────────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────────────────┐
│ Trade-off 4: Small Object Handling Strategy                              │
├──────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  Problem: Erasure coding 8+4 on a 1 KB object creates 12 x 125-byte    │
│  chunks. The per-chunk metadata overhead dominates.                      │
│                                                                          │
│  Solution: Object packing                                                │
│  - Small objects (< 256 KB) are batched into "packed extents"           │
│  - A packed extent is ~1 MB of aggregated small objects                  │
│  - The packed extent is erasure-coded as one unit                        │
│  - Metadata stores: extent_id + offset within extent                     │
│                                                                          │
│  Trade-off:                                                              │
│  + Amortizes erasure coding overhead                                     │
│  + Reduces chunk count dramatically for small-object workloads          │
│  - DELETE of packed object: mark tombstone, space reclaimed on          │
│    compaction (delayed reclamation)                                      │
│  - Read amplification: must read 8 chunks even for tiny object          │
│    (mitigated by extent-level caching)                                  │
│                                                                          │
└──────────────────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────────────────┐
│ Trade-off 5: Centralized vs Decentralized Placement                      │
├──────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  We chose: CRUSH-like algorithmic placement (decentralized)             │
│                                                                          │
│  Centralized (lookup table):               Algorithmic (CRUSH):          │
│  - Need massive table: 100B objects x      - O(log N) computation       │
│    12 locations = 1.2 trillion entries     - Cluster map is tiny (KB)    │
│  - Bottleneck at lookup service            - Any node can compute        │
│  - Hot spot for all operations               placement independently   │
│  - Complex to keep consistent              - Minimal data movement on   │
│                                              cluster changes            │
│                                            - Harder to implement         │
│                                              perfectly balanced load    │
│                                                                          │
└──────────────────────────────────────────────────────────────────────────┘
```

---

## 16. Interview Deep-Dive Questions

### Q1: How do you achieve 11 nines of durability?

**Answer:** We combine multiple strategies. First, **erasure coding (Reed-Solomon 8,4)**: each
object is split into 8 data chunks and 4 parity chunks, stored across 12 different nodes in
at least 3 availability zones. The object survives up to 4 simultaneous chunk losses. Second,
**failure domain separation**: chunks are spread across different disks, nodes, racks, and AZs,
so correlated failures (rack power loss, AZ outage) don't take out enough chunks. Third,
**background data scrubbing**: every chunk is checksummed and verified every 30 days, catching
silent bit rot before it accumulates. Fourth, **rapid repair**: when a disk or node fails, the
repair pipeline reconstructs affected chunks within hours, well before a second failure is
likely. The mathematical probability of losing an object under these conditions is approximately
10^-23 per year, far exceeding the 11-nines target.

---

### Q2: How does erasure coding work, and why prefer it over replication?

**Answer:** Erasure coding treats data as a polynomial over a Galois field (GF(2^8)). The object
is split into `k=8` data chunks. We evaluate this polynomial at `m=4` additional points to
produce 4 parity chunks. Any 8 of the 12 total chunks can reconstruct the original data via
polynomial interpolation.

Compared to triple replication:
- **Cost:** 1.5x storage overhead vs 3x---50% cheaper at petabyte scale (savings of ~$15K/PB/month).
- **Fault tolerance:** Survives 4 failures vs 2.
- **Durability:** Higher mathematical durability due to more independent failure events needed.
- **Downsides:** Reads require fetching 8 chunks and decoding (vs reading any 1 replica). Writes
  require encoding. Both are mitigated by SIMD-optimized libraries (Intel ISA-L achieves ~10 GB/s
  encode throughput per core) and caching hot objects in replicated form.

---

### Q3: How do you handle consistency for read-after-write?

**Answer:** We use Raft-based consensus for the metadata layer. Every PUT commits metadata to a
Raft group (leader + majority of followers). The PUT returns success only after Raft commit. For
reads, we use one of two approaches: (1) always read from the Raft leader, which is guaranteed to
have the latest committed state, or (2) use the "read index" optimization where a follower asks
the leader for the current commit index, waits until its local state catches up, then serves the
read locally. This guarantees that any GET issued after a successful PUT returns the new version.
For cache invalidation, we use write-through: every PUT/DELETE invalidates the corresponding
cache entry, so subsequent reads either hit the fresh cache or go to the metadata store.

---

### Q4: How do you implement storage classes (hot/warm/cold/archive)?

**Answer:** Storage classes differ in three dimensions: media type, erasure coding scheme, and
access latency. **Standard** uses HDD with SSD caching, 8+4 across 3 AZs, sub-50ms latency.
**Infrequent Access** uses the same scheme but charges retrieval fees, encouraging users to
self-select. **Glacier** uses dense HDD (high capacity, slower seek), 12+6 coding for cheaper
storage, and requires an explicit restore request (data is "thawed" from cold pools to a
temporary staging area, available in minutes). **Deep Archive** may use tape or offline HDD
arrays, with restore times of 12-48 hours. Lifecycle policies automate transitions: metadata
is updated with the new storage class, and background workers physically migrate data between
storage tiers, re-encoding with the target erasure scheme.

---

### Q5: How does multipart upload handle failures mid-upload?

**Answer:** Each part is uploaded independently and erasure-coded immediately upon receipt. The
server stores part metadata (part number, ETag, chunk locations) in a temporary upload record
keyed by the `uploadId`. If a part fails, the client simply retries that specific part number
(idempotent---same part number overwrites the previous attempt). If the client crashes and
never calls "complete," the incomplete upload is subject to a TTL (default 7 days) or a
lifecycle rule (`AbortIncompleteMultipartUpload`). The garbage collector periodically scans
for expired incomplete uploads, deletes their orphaned chunks, and removes the upload metadata.
The "complete" call itself is idempotent: calling it again with the same part list returns the
same result.

---

### Q6: How do you handle the "hot bucket" problem (one bucket with billions of objects)?

**Answer:** If all objects in a bucket map to a single metadata shard, that shard becomes a
bottleneck. We address this by **sub-sharding hot buckets**: when a shard's load exceeds a
threshold, we split it by key prefix hash. For example, a bucket with key prefix "a-m" goes
to shard A, "n-z" to shard B. Listing queries fan out across sub-shards and merge results
(similar to scatter-gather). The sub-shard boundaries are stored in the shard routing table
(etcd). This is transparent to the client. Additionally, rate limiting per bucket prevents
a single tenant from overwhelming the system.

---

### Q7: How do you design the garbage collection system?

**Answer:** GC operates in several layers. (1) **Deleted objects**: a DELETE marks the object
with a tombstone in metadata (or inserts a delete marker if versioned). A background GC worker
periodically scans for tombstoned metadata older than a grace period (e.g., 24 hours to allow
for replication and rollback), then issues chunk deletion commands to data nodes. (2)
**Orphaned chunks**: if metadata commits but some chunk writes fail, the chunks that were
written become orphans. The scrubber detects chunks not referenced by any metadata entry and
queues them for deletion. (3) **Incomplete multipart uploads**: as described in Q5, TTL-based
cleanup. (4) **Compaction**: when packed extents have many deleted small objects, the compactor
rewrites live objects into new extents, releasing the old ones. GC is always throttled to
avoid impacting live traffic.

---

### Q8: How do you handle encryption at rest?

**Answer:** We support three modes. **SSE-S3**: the service manages keys; each object is
encrypted with a unique data encryption key (DEK), and the DEK is encrypted with a master
key (envelope encryption). DEKs are stored alongside object metadata. Master keys are rotated
periodically; re-encryption is lazy (re-encrypt DEK, not re-encrypt data). **SSE-KMS**: the
customer provides a KMS key ID. The service calls KMS to generate a DEK for each object. The
encrypted DEK is stored in metadata. On GET, the service calls KMS to decrypt the DEK, then
decrypts the object. **SSE-C**: the customer provides the encryption key in the request header.
The service encrypts/decrypts in memory, never stores the key. Encryption happens before
erasure coding: the plaintext is encrypted, then the ciphertext is erasure-coded and stored.

---

### Q9: How does listing with prefix and delimiter work efficiently?

**Answer:** Objects in each metadata shard are stored in a RocksDB instance with the key format
`[bucket_id][object_key][version_id]`, sorted lexicographically. A prefix query translates to
a RocksDB range scan: seek to `[bucket_id][prefix]` and iterate until the key no longer starts
with the prefix. The delimiter (typically "/") is applied in-memory: keys between two delimiters
are grouped into "common prefixes" (virtual directories). Pagination uses a "marker" (the last
key returned), and the next request seeks to just after the marker. For hot buckets sub-sharded
across multiple metadata nodes, the API server sends the listing query to all relevant sub-shards
in parallel, merges the sorted results, and applies the max-keys limit. This is efficient because
RocksDB's LSM-tree structure provides fast range scans.

---

### Q10: What happens when you need to add a new availability zone?

**Answer:** Adding an AZ is a multi-step operation. (1) Deploy new data nodes in the new AZ and
register them in the cluster topology tree (under the new AZ node). (2) Update the CRUSH map to
include the new AZ. (3) The placement algorithm now considers the new AZ for new objects. (4) For
existing objects, a background rebalancer gradually moves a subset of chunks to the new AZ to
improve distribution. Because CRUSH is deterministic, changing the map causes only a fraction of
placement groups to shift---roughly proportional to the new AZ's weight relative to total cluster
weight. (5) During the transition, the system maintains dual placement maps (old and new); reads
try the new placement first, fall back to old. (6) Once migration completes, the old map is
retired. The entire process is online with no downtime.

---

### Q11: How do you implement pre-signed URLs securely?

**Answer:** A pre-signed URL embeds the access credentials and a cryptographic signature directly
in the URL query parameters. The server generates it by: (1) constructing a "string to sign"
that includes the HTTP method, bucket, key, expiration timestamp, and any conditions (e.g.,
content-type); (2) computing an HMAC-SHA256 signature using the user's secret key (or a
service-managed signing key); (3) encoding the signature and credential info into query params.
When a request arrives with a pre-signed URL, the API server: (a) checks the expiration---reject
if expired; (b) reconstructs the string to sign from the request; (c) looks up the signing key
and verifies the signature; (d) evaluates IAM/bucket policies to ensure the signer had permission
at signing time. The URL is usable by anyone (no auth header needed), but only for the specified
method, key, and time window.

---

### Q12: How do you handle the "small file problem" in an erasure-coded system?

**Answer:** For objects smaller than 256 KB, erasure coding individually is wasteful: a 1 KB
object would produce 12 chunks of ~125 bytes each, but each chunk has metadata overhead
(checksum, location, index entry) of ~100 bytes. Our solution is **object packing**: small
objects are buffered in memory on the API server and aggregated into a "packed extent" of ~1 MB.
The packed extent is then erasure-coded as a single unit. Each small object's metadata stores
the extent ID and its offset/length within the extent. Reads require fetching the extent (8
chunks) and extracting the relevant bytes. We mitigate read amplification by caching entire
extents (they tend to have temporal locality---objects uploaded together are often accessed
together). Deletes mark the object as tombstoned within the extent; space is reclaimed when the
compactor rewrites the extent without the deleted objects.

---

### Q13: How does the system handle a correlated failure (e.g., software bug that corrupts all replicas)?

**Answer:** This is the nightmare scenario that replication and erasure coding within a single
software stack cannot protect against. Defenses: (1) **Immutable writes**: once written,
chunk data is never modified in place, only appended or deleted. (2) **End-to-end checksums**:
the client computes a checksum (Content-MD5) that is verified at every stage---API server,
data node write, data node read, API server response. (3) **Diverse storage codepaths**: repair
and scrubbing code runs a separate checksum verification path from the write path, reducing
the chance of a shared bug. (4) **Cross-region replication**: regions may run different
software versions, so a bug in one region's stack does not affect the replica. (5) **Object
versioning**: even if the latest version is corrupted, previous versions (stored as
independent data) may be intact. (6) **Periodic offline validation**: sample objects are
periodically downloaded and verified by an independent system.

---

### Q14: How do you design rate limiting for a multi-tenant object storage service?

**Answer:** Rate limiting operates at multiple levels. (1) **Per-account**: each account has a
default request rate limit (e.g., 3,500 PUT/sec and 5,500 GET/sec per prefix). Exceeding this
returns HTTP 503 SlowDown. (2) **Per-bucket**: configurable limits via bucket policies. (3)
**Global**: the API server fleet has a total capacity; if aggregate load approaches capacity,
adaptive throttling kicks in (prioritize existing connections, reject new ones). Implementation
uses a **token bucket** algorithm with distributed state: each API server maintains a local
token bucket and periodically syncs with a centralized rate limiter (Redis-based). For burst
tolerance, the token bucket allows short bursts up to 2x the sustained rate. Clients receive
`Retry-After` headers to implement exponential backoff.

---

### Q15: How would you design the system to support WORM (Write Once Read Many) compliance?

**Answer:** WORM compliance (for regulatory requirements like SEC 17a-4 or GDPR) requires that
objects cannot be modified or deleted for a specified retention period. Implementation: (1)
**Object Lock** at the bucket level: once enabled, every object version gets a retention
configuration (retain-until date + legal hold flag). (2) **Retention enforcement**: the metadata
service checks retention before allowing DELETE. If retention is active, DELETE is rejected
with HTTP 403. (3) **Governance mode**: allows users with special IAM permissions to bypass
retention (for correcting mistakes). **Compliance mode**: even root/admin cannot delete before
retention expires---the system enforces this at the storage layer, not just IAM. (4) **Legal
hold**: independently locks an object (regardless of retention date) until explicitly removed
by an authorized user. (5) **Clock trust**: the system uses NTP-synced clocks with skew
detection; retention expiry checks use the cluster's consensus-agreed time to prevent clock
manipulation.

---

## 17. References and Further Reading

- **Amazon S3 Design:** Dynamo paper (DeCandia et al., 2007) influenced S3's metadata layer.
  S3 strong consistency announcement (Dec 2020) describes the witness protocol.
- **Erasure Coding:** Reed-Solomon codes, Intel ISA-L library for SIMD-optimized implementations.
- **Ceph CRUSH:** Weil et al., "CRUSH: Controlled, Scalable, Decentralized Placement of
  Replicated Data" (SC'06). The placement algorithm described here is inspired by CRUSH.
- **Facebook f4:** Muralidhar et al., "f4: Facebook's Warm BLOB Storage System" (OSDI 2014).
  Demonstrates erasure coding at scale for warm storage.
- **Windows Azure Storage:** Calder et al., "Windows Azure Storage: A Highly Available Cloud
  Storage Service with Strong Consistency" (SOSP 2011).
- **MinIO:** Open-source S3-compatible object storage. Good reference implementation for
  understanding erasure coding and distributed object storage.
- **Google Colossus:** Successor to GFS, uses Reed-Solomon erasure coding for storage efficiency.

---

## 18. Summary Cheat Sheet

```
┌──────────────────────────────────────────────────────────────────────────┐
│                    Object Storage (S3) - Quick Reference                 │
├──────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  Durability:     11 nines (99.999999999%) via erasure coding 8+4        │
│  Availability:   99.99% via multi-AZ, auto-failover                     │
│  Consistency:    Strong read-after-write (Raft-based metadata)          │
│  Scale:          Petabytes data, trillions of objects, millions req/sec  │
│                                                                          │
│  Data path:      Client → API Server → erasure encode → 12 data nodes  │
│  Metadata path:  API Server → Metadata Store (Raft, sharded by bucket) │
│  Placement:      CRUSH algorithm (deterministic, no lookup table)       │
│                                                                          │
│  Key components:                                                         │
│    API Server:       stateless, erasure encode/decode                    │
│    Metadata Service: Raft groups, RocksDB, sharded by bucket            │
│    Data Nodes:       raw disk, extent files, chunk index                 │
│    Placement Svc:    CRUSH algorithm + cluster topology map             │
│    GC / Scrubber:    background integrity + space reclamation           │
│                                                                          │
│  Storage cost:   1.5x raw data (vs 3x for replication) = 50% savings   │
│  Storage tiers:  Standard → IA → Glacier → Deep Archive                │
│                                                                          │
│  Interview signals:                                                      │
│    - Understand erasure coding trade-offs (cost, latency, complexity)   │
│    - Explain 11-nines durability math                                    │
│    - Articulate strong consistency via Raft + read index                 │
│    - Discuss failure domains and correlated failure mitigation          │
│    - Know multipart upload lifecycle and GC                             │
│                                                                          │
└──────────────────────────────────────────────────────────────────────────┘
```
