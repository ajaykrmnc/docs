# Design a Metrics and Monitoring System (Datadog / Prometheus)

## Table of Contents

1. [Problem Statement](#1-problem-statement)
2. [Functional Requirements](#2-functional-requirements)
3. [Non-Functional Requirements](#3-non-functional-requirements)
4. [Back-of-Envelope Estimation](#4-back-of-envelope-estimation)
5. [API Design](#5-api-design)
6. [Data Model](#6-data-model)
7. [High-Level Architecture](#7-high-level-architecture)
8. [Deep Dive](#8-deep-dive)
   - 8.1 [TSDB Storage Engine](#81-tsdb-storage-engine)
   - 8.2 [Ingestion Pipeline](#82-ingestion-pipeline)
   - 8.3 [Query Engine](#83-query-engine)
   - 8.4 [Alerting Engine](#84-alerting-engine)
9. [Partitioning Strategy](#9-partitioning-strategy)
10. [Caching Strategy](#10-caching-strategy)
11. [Replication](#11-replication)
12. [Fault Tolerance](#12-fault-tolerance)
13. [Scalability](#13-scalability)
14. [Monitoring the Monitoring System (Meta)](#14-monitoring-the-monitoring-system-meta)
15. [Trade-offs and Design Decisions](#15-trade-offs-and-design-decisions)
16. [Interview Questions and Answers](#16-interview-questions-and-answers)

---

## 1. Problem Statement

Modern distributed systems consist of thousands of microservices running across tens of
thousands of hosts, containers, and serverless functions. Each component emits hundreds
of metrics every few seconds -- CPU utilization, request latency percentiles, error rates,
queue depths, garbage collection pauses, disk IOPS, and custom business metrics. Operators
need a unified system to:

- **Collect** billions of time-series data points per day from heterogeneous sources
- **Store** this data efficiently for both real-time queries and historical analysis
- **Query** across dimensions (service, host, region, version) with sub-second latency
- **Alert** on anomalies, threshold breaches, and SLO violations with minimal delay
- **Visualize** system health through dashboards that update in real time

The challenge lies in the extreme write volume (potentially millions of data points per
second), the need for flexible multi-dimensional querying, long-term retention spanning
years, and the requirement that the monitoring system itself must be more reliable than
the systems it monitors.

### Real-World Context

| System      | Scale                                   | Approach                    |
|-------------|----------------------------------------|-----------------------------|
| Prometheus  | Single-node TSDB, federation for scale | Pull-based, local storage   |
| Datadog     | Billions of pts/sec across all tenants | Push-based, cloud SaaS      |
| Thanos      | Long-term Prometheus with object store | Sidecar + compactor         |
| Cortex/Mimir| Multi-tenant horizontally-scaled Prom  | Shared-nothing ingesters    |
| InfluxDB    | Write-optimized columnar TSDB          | Push, TSI index, TSM engine |
| VictoriaMetrics | Optimized single/cluster TSDB      | Pull/push, vmselect/vmstorage |

---

## 2. Functional Requirements

### Core Features

| # | Requirement                | Description                                                        |
|---|----------------------------|--------------------------------------------------------------------|
| 1 | Push ingestion             | Accept metrics via StatsD, OpenTelemetry, custom HTTP endpoints    |
| 2 | Pull ingestion             | Scrape Prometheus-format /metrics endpoints at configurable intervals |
| 3 | Time-series storage        | Store (metric_name, tags, timestamp, value) tuples efficiently     |
| 4 | PromQL-like queries        | rate(), avg_over_time(), histogram_quantile(), aggregation by labels |
| 5 | Dashboard creation         | Define panels with queries, layout, refresh intervals              |
| 6 | Alerting rules             | Define threshold/anomaly conditions, notification channels         |
| 7 | Tagging / labeling         | Arbitrary key-value labels on every metric for dimensional slicing |
| 8 | Aggregation                | Pre-aggregate across hosts, regions, clusters at ingestion time    |
| 9 | Downsampling               | Reduce resolution for older data (10s -> 1m -> 5m -> 1h)          |
| 10| Multi-tenancy              | Isolate metrics between teams/organizations                       |

### Out of Scope (for initial design)

- Log aggregation and full-text search (separate system like ELK)
- Distributed tracing (separate system like Jaeger/Tempo)
- Synthetic monitoring / uptime checks
- AIOps / ML-based anomaly detection (can be layered on later)

---

## 3. Non-Functional Requirements

| Property            | Target                                                      |
|---------------------|-------------------------------------------------------------|
| Ingestion throughput| 10M+ data points per second (cluster-wide)                  |
| Query latency       | < 1 second for dashboards over recent data (last 1-6 hours) |
| Query latency (long)| < 10 seconds for queries spanning days/weeks                |
| Retention           | Raw: 15 days, 1m avg: 6 months, 1h avg: 3+ years           |
| Availability        | 99.99% (52.6 min downtime/year) -- must exceed monitored systems |
| Durability          | No data loss for committed writes (WAL + replication)       |
| Alert latency       | < 30 seconds from metric arrival to alert firing            |
| Cardinality         | Support 50M+ active time series per tenant                  |
| Consistency         | Eventual consistency acceptable; prefer availability        |

---

## 4. Back-of-Envelope Estimation

### Ingestion Volume

```
Single cluster:
  1,000 hosts x 500 metrics/host x 1 sample/10s = 50,000 data points/sec

Medium org (100 clusters):
  100 x 50,000 = 5,000,000 data points/sec = 5M pts/sec

Large org / SaaS platform (10,000 clusters):
  10,000 x 50,000 = 500,000,000 data points/sec = 500M pts/sec
```

### Storage

```
Per data point (uncompressed):
  metric_name hash:    8 bytes
  tag set hash:        8 bytes
  timestamp:           8 bytes
  value (float64):     8 bytes
  overhead:           ~88 bytes (labels, index entries, etc.)
  Total:             ~120 bytes/data point

Daily raw volume (500M pts/sec):
  500M x 86,400 sec x 120 bytes = 5.18 PB/day (raw, uncompressed)

With Gorilla compression (~12x for timestamps + values):
  ~432 TB/day for values + timestamps

With delta encoding + dedup on tag indices:
  ~500 TB/day total (compressed)

15-day raw retention:
  500 TB x 15 = 7.5 PB

Downsampled (1m avg over 6 months):
  500M pts/sec / 6 (10s->1m) = 83M pts/sec
  83M x 86,400 x 180 days x 20 bytes(compressed) = ~26 PB
  (But much smaller per-point after compression: ~2-3 PB)
```

### Network Bandwidth

```
Ingestion at 500M pts/sec x 120 bytes:
  60 GB/sec inbound = 480 Gbps

After batching and compression (10x reduction):
  ~48 Gbps inbound across all ingestion nodes

Typical query: scan 1M data points x 16 bytes = 16 MB
  At 10,000 concurrent queries: 160 GB/sec read throughput
```

### Node Count Estimates

```
TSDB storage nodes:
  7.5 PB / 20 TB per node = 375 storage nodes (with replication: ~750-1125)

Ingestion nodes:
  500M pts/sec / 2M pts/sec per node = 250 ingestion nodes

Query nodes:
  10,000 QPS / 200 QPS per node = 50 query nodes

Kafka brokers:
  48 Gbps / 2 Gbps per broker = 24+ brokers
```

---

## 5. API Design

### 5.1 Metrics Ingestion API

```
POST /api/v1/metrics
Content-Type: application/json
Authorization: Bearer <api_key>

Request Body:
{
  "series": [
    {
      "metric": "system.cpu.utilization",
      "type": "gauge",                          // gauge | counter | histogram | summary
      "points": [
        [1700000000, 72.5],                      // [timestamp_epoch_sec, value]
        [1700000010, 74.1]
      ],
      "tags": {
        "host": "web-prod-001",
        "region": "us-east-1",
        "service": "api-gateway",
        "env": "production"
      },
      "interval": 10,                            // collection interval in seconds
      "unit": "percent"
    },
    {
      "metric": "http.request.duration",
      "type": "histogram",
      "points": [
        [1700000000, {"sum": 4520.5, "count": 1200, "buckets": {"0.1": 500, "0.5": 900, "1.0": 1100, "5.0": 1195, "+Inf": 1200}}]
      ],
      "tags": {
        "host": "web-prod-001",
        "method": "GET",
        "endpoint": "/api/users",
        "status_code": "200"
      }
    }
  ]
}

Response: 202 Accepted
{
  "status": "ok",
  "accepted": 2,
  "errors": []
}
```

### 5.2 Prometheus Remote Write (Pull-to-Push Bridge)

```
POST /api/v1/prom/write
Content-Type: application/x-protobuf
Content-Encoding: snappy
X-Prometheus-Remote-Write-Version: 0.1.0

Body: Snappy-compressed Protocol Buffer (prometheus.WriteRequest)
  - Each TimeSeries has []Label and []Sample
  - Label: name (string), value (string)
  - Sample: value (float64), timestamp (int64 ms)

Response: 204 No Content
```

### 5.3 Query API

```
GET /api/v1/query
Parameters:
  query:   rate(http_requests_total{service="api",status=~"5.."}[5m])
  time:    1700000000                            // evaluation timestamp (optional, default=now)

GET /api/v1/query_range
Parameters:
  query:   avg_over_time(system_cpu_utilization{region="us-east-1"}[5m])
  start:   1700000000
  end:     1700003600
  step:    60                                    // resolution in seconds

Response:
{
  "status": "success",
  "data": {
    "resultType": "matrix",
    "result": [
      {
        "metric": {
          "__name__": "system_cpu_utilization",
          "host": "web-prod-001",
          "region": "us-east-1"
        },
        "values": [
          [1700000000, "72.5"],
          [1700000060, "73.2"],
          [1700000120, "71.8"]
        ]
      }
    ]
  }
}
```

### 5.4 Alerting API

```
POST /api/v1/alerts/rules
{
  "name": "HighErrorRate",
  "expr": "rate(http_requests_total{status=~'5..'}[5m]) / rate(http_requests_total[5m]) > 0.05",
  "for": "5m",                                   // pending duration before firing
  "severity": "critical",
  "labels": {
    "team": "platform",
    "service": "api-gateway"
  },
  "annotations": {
    "summary": "Error rate above 5% for {{ $labels.service }}",
    "runbook": "https://wiki.internal/runbooks/high-error-rate"
  },
  "notifications": [
    {"channel": "pagerduty", "service_key": "abc123"},
    {"channel": "slack", "webhook": "https://hooks.slack.com/..."}
  ]
}

Response: 201 Created
{
  "id": "alert_rule_12345",
  "status": "active",
  "created_at": "2024-11-15T10:00:00Z"
}
```

### 5.5 Dashboard API

```
GET /api/v1/dashboards/{dashboard_id}

Response:
{
  "id": "dash_001",
  "title": "API Gateway Overview",
  "refresh_interval": 30,
  "time_range": {"from": "now-1h", "to": "now"},
  "panels": [
    {
      "id": "panel_01",
      "title": "Request Rate",
      "type": "timeseries",
      "gridPos": {"x": 0, "y": 0, "w": 12, "h": 8},
      "queries": [
        {
          "expr": "sum(rate(http_requests_total{service='api'}[5m])) by (status_code)",
          "legend": "{{status_code}}"
        }
      ],
      "thresholds": [
        {"value": 1000, "color": "yellow"},
        {"value": 5000, "color": "red"}
      ]
    }
  ],
  "variables": [
    {"name": "region", "query": "label_values(http_requests_total, region)", "type": "query"}
  ]
}
```

---

## 6. Data Model

### 6.1 Time-Series Data Model

A time series is uniquely identified by its metric name plus a set of key-value label pairs.

```
Identity:  metric_name + sorted(labels) --> unique time series

Example:
  http_requests_total{service="api", method="GET", status="200", host="web-001"}
                     {service="api", method="GET", status="200", host="web-002"}
  These are TWO distinct time series.

Data Points (samples):
  (timestamp_ms: int64, value: float64)

Cardinality = unique combinations of (metric_name, label_set)
  500 metrics x 1000 hosts x 5 methods x 10 endpoints x 5 status = 125M series
  (This is "cardinality explosion" -- a critical concern)
```

### 6.2 TSDB On-Disk Layout

```
┌─────────────────────────────────────────────────────────────────────┐
│                         TSDB Directory                              │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │ WAL (Write-Ahead Log)                                        │   │
│  │  segment-000001                                              │   │
│  │  segment-000002                                              │   │
│  │  segment-000003  (append-only, 128MB segments)               │   │
│  └──────────────────────────────────────────────────────────────┘   │
│                                                                     │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │ Head Block (in-memory, current 2h window)                    │   │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐         │   │
│  │  │ Series 1    │  │ Series 2    │  │ Series N    │         │   │
│  │  │ memChunk    │  │ memChunk    │  │ memChunk    │         │   │
│  │  │ (compressed)│  │ (compressed)│  │ (compressed)│         │   │
│  │  └─────────────┘  └─────────────┘  └─────────────┘         │   │
│  │  Posting Lists (inverted index in memory)                    │   │
│  └──────────────────────────────────────────────────────────────┘   │
│                                                                     │
│  ┌────────────────────┐  ┌────────────────────┐                    │
│  │ Block 01           │  │ Block 02           │  ...               │
│  │ [12:00 - 14:00]    │  │ [14:00 - 16:00]    │                    │
│  │                    │  │                    │                    │
│  │  meta.json         │  │  meta.json         │                    │
│  │  index             │  │  index             │                    │
│  │  chunks/           │  │  chunks/           │                    │
│  │    000001          │  │    000001          │                    │
│  │    000002          │  │    000002          │                    │
│  │  tombstones        │  │  tombstones        │                    │
│  └────────────────────┘  └────────────────────┘                    │
│                                                                     │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │ Compacted Blocks (merged, larger time ranges)                │   │
│  │  Block_C1 [12:00 - 18:00]  (3 blocks merged)                │   │
│  │  Block_C2 [18:00 - 06:00]  (6 blocks merged)                │   │
│  └──────────────────────────────────────────────────────────────┘   │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

### 6.3 Inverted Index for Labels

```
Label Pair          -->  Posting List (sorted series IDs)
────────────────────────────────────────────────────────
service="api"       -->  [1, 2, 3, 7, 15, 22, 45, ...]
service="web"       -->  [4, 5, 8, 9, 16, 23, ...]
host="web-001"      -->  [1, 4, 10, 33, ...]
host="web-002"      -->  [2, 5, 11, 34, ...]
status="200"        -->  [1, 2, 4, 5, 7, 8, 10, ...]
status="500"        -->  [3, 6, 9, 12, ...]
__name__="http_req" -->  [1, 2, 3, 4, 5, 6, 7, 8, ...]

Query: http_requests_total{service="api", status="500"}
  = Intersect(posting["__name__=http_requests_total"],
              posting["service=api"],
              posting["status=500"])
  = Intersect([1,2,3,4,5,6,7,8], [1,2,3,7,15,22,45], [3,6,9,12])
  = [3]
```

### 6.4 Metadata Store (MySQL / PostgreSQL)

```sql
-- Alert rules, dashboards, and tenant config stored in relational DB

CREATE TABLE tenants (
    tenant_id       BIGINT PRIMARY KEY AUTO_INCREMENT,
    name            VARCHAR(255) NOT NULL,
    api_key_hash    VARCHAR(64) NOT NULL,
    max_series      BIGINT DEFAULT 10000000,
    retention_days  INT DEFAULT 15,
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE alert_rules (
    rule_id         BIGINT PRIMARY KEY AUTO_INCREMENT,
    tenant_id       BIGINT NOT NULL REFERENCES tenants(tenant_id),
    name            VARCHAR(255) NOT NULL,
    expression      TEXT NOT NULL,
    for_duration    INT DEFAULT 0,           -- seconds
    severity        ENUM('info','warning','critical') DEFAULT 'warning',
    labels          JSON,
    annotations     JSON,
    notification_channels JSON,
    enabled         BOOLEAN DEFAULT TRUE,
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

CREATE TABLE alert_states (
    rule_id         BIGINT NOT NULL REFERENCES alert_rules(rule_id),
    series_hash     BIGINT NOT NULL,
    state           ENUM('inactive','pending','firing','resolved') DEFAULT 'inactive',
    active_since    TIMESTAMP NULL,
    fired_at        TIMESTAMP NULL,
    resolved_at     TIMESTAMP NULL,
    last_value      DOUBLE,
    PRIMARY KEY (rule_id, series_hash)
);

CREATE TABLE dashboards (
    dashboard_id    BIGINT PRIMARY KEY AUTO_INCREMENT,
    tenant_id       BIGINT NOT NULL REFERENCES tenants(tenant_id),
    title           VARCHAR(255) NOT NULL,
    panels          JSON NOT NULL,
    variables       JSON,
    refresh_interval INT DEFAULT 30,
    created_by      VARCHAR(255),
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

CREATE TABLE recording_rules (
    rule_id         BIGINT PRIMARY KEY AUTO_INCREMENT,
    tenant_id       BIGINT NOT NULL REFERENCES tenants(tenant_id),
    name            VARCHAR(255) NOT NULL,       -- new metric name
    expression      TEXT NOT NULL,               -- PromQL expression
    interval        INT DEFAULT 60,              -- evaluation interval in seconds
    labels          JSON,
    enabled         BOOLEAN DEFAULT TRUE
);

CREATE TABLE downsampling_policies (
    policy_id       BIGINT PRIMARY KEY AUTO_INCREMENT,
    tenant_id       BIGINT NOT NULL REFERENCES tenants(tenant_id),
    source_resolution INT NOT NULL,              -- e.g., 10 seconds
    target_resolution INT NOT NULL,              -- e.g., 60 seconds
    aggregations    JSON NOT NULL,               -- ["avg", "min", "max", "count"]
    after_age       INT NOT NULL,                -- seconds after which to downsample
    enabled         BOOLEAN DEFAULT TRUE
);
```

---

## 7. High-Level Architecture

### 7.1 System Overview

```
┌─────────────────────────────────────────────────────────────────────────────────────────┐
│                              METRICS SOURCES                                            │
│                                                                                         │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐  │
│  │App Server│  │  K8s     │  │ Database │  │  Load   │  │  Cache  │  │  Queue  │  │
│  │ (custom  │  │  Pods    │  │  (MySQL, │  │Balancer │  │ (Redis, │  │ (Kafka, │  │
│  │ metrics) │  │ (cAdvisor│  │  Postgres)│  │ (HAProxy│  │ Memcache│  │  SQS)  │  │
│  │          │  │  kubelet)│  │          │  │  Nginx) │  │        )│  │        │  │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘  └────┬─────┘  └────┬─────┘  └────┬─────┘  │
│       │              │              │              │              │              │       │
└───────┼──────────────┼──────────────┼──────────────┼──────────────┼──────────────┼───────┘
        │              │              │              │              │              │
        │   Push (StatsD/OTLP)        │   Pull (Prometheus scrape) │              │
        │              │              │              │              │              │
┌───────┼──────────────┼──────────────┼──────────────┼──────────────┼──────────────┼───────┐
│       ▼              ▼              ▼              ▼              ▼              ▼       │
│  ┌─────────────────────────────────────────────────────────────────────────────────────┐ │
│  │                         COLLECTION LAYER                                           │ │
│  │                                                                                     │ │
│  │  ┌──────────────────┐   ┌──────────────────┐   ┌──────────────────┐                │ │
│  │  │  Push Gateway    │   │  Scrape Manager  │   │   OTel Collector │                │ │
│  │  │  (StatsD/HTTP)   │   │  (Prom pull)     │   │  (gRPC/HTTP)     │                │ │
│  │  │                  │   │                  │   │                  │                │ │
│  │  │  - UDP/TCP recv  │   │  - Target disc.  │   │  - Receive       │                │ │
│  │  │  - Parse         │   │  - Health check  │   │  - Process       │                │ │
│  │  │  - Aggregate     │   │  - Scrape /metr. │   │  - Export        │                │ │
│  │  │  - Forward       │   │  - Parse Prom fmt│   │  - Batch + retry │                │ │
│  │  └───────┬──────────┘   └───────┬──────────┘   └───────┬──────────┘                │ │
│  │          │                      │                      │                           │ │
│  └──────────┼──────────────────────┼──────────────────────┼───────────────────────────┘ │
│             │                      │                      │                             │
│             └──────────────────────┼──────────────────────┘                             │
│                                    │                                                    │
│                                    ▼                                                    │
│  ┌─────────────────────────────────────────────────────────────────────────────────────┐ │
│  │                         KAFKA CLUSTER                                               │ │
│  │                                                                                     │ │
│  │  Topic: metrics-raw (partitioned by hash(metric_name + tenant_id))                 │ │
│  │  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐        ┌──────────┐          │ │
│  │  │ Part. 0  │ │ Part. 1  │ │ Part. 2  │ │ Part. 3  │  ...   │ Part. N  │          │ │
│  │  └──────────┘ └──────────┘ └──────────┘ └──────────┘        └──────────┘          │ │
│  │                                                                                     │ │
│  │  Retention: 24h (buffer for backpressure and replay)                               │ │
│  └──────────────────────────────────┬──────────────────────────────────────────────────┘ │
│                                     │                                                    │
│                                     ▼                                                    │
│  ┌─────────────────────────────────────────────────────────────────────────────────────┐ │
│  │                         INGESTION LAYER                                             │ │
│  │                                                                                     │ │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐               │ │
│  │  │ Ingester 0  │  │ Ingester 1  │  │ Ingester 2  │  │ Ingester N  │               │ │
│  │  │             │  │             │  │             │  │             │               │ │
│  │  │ - WAL write │  │ - WAL write │  │ - WAL write │  │ - WAL write │               │ │
│  │  │ - Head block│  │ - Head block│  │ - Head block│  │ - Head block│               │ │
│  │  │ - Validate  │  │ - Validate  │  │ - Validate  │  │ - Validate  │               │ │
│  │  │ - Replicate │  │ - Replicate │  │ - Replicate │  │ - Replicate │               │ │
│  │  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘               │ │
│  │         │                │                │                │                       │ │
│  └─────────┼────────────────┼────────────────┼────────────────┼───────────────────────┘ │
│            │                │                │                │                          │
│            ▼                ▼                ▼                ▼                          │
│  ┌─────────────────────────────────────────────────────────────────────────────────────┐ │
│  │                    TSDB STORAGE LAYER                                               │ │
│  │                                                                                     │ │
│  │  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐                  │ │
│  │  │  Store Node 0    │  │  Store Node 1    │  │  Store Node N    │                  │ │
│  │  │                  │  │                  │  │                  │                  │ │
│  │  │  ┌────────────┐  │  │  ┌────────────┐  │  │  ┌────────────┐  │                  │ │
│  │  │  │ Head Block  │  │  │  │ Head Block  │  │  │  │ Head Block  │  │                  │ │
│  │  │  │ (2h window) │  │  │  │ (2h window) │  │  │  │ (2h window) │  │                  │ │
│  │  │  └────────────┘  │  │  └────────────┘  │  │  └────────────┘  │                  │ │
│  │  │  ┌────────────┐  │  │  ┌────────────┐  │  │  ┌────────────┐  │                  │ │
│  │  │  │ Persisted  │  │  │  │ Persisted  │  │  │  │ Persisted  │  │                  │ │
│  │  │  │ Blocks     │  │  │  │ Blocks     │  │  │  │ Blocks     │  │                  │ │
│  │  │  │ (2h each)  │  │  │  │ (2h each)  │  │  │  │ (2h each)  │  │                  │ │
│  │  │  └────────────┘  │  │  └────────────┘  │  │  └────────────┘  │                  │ │
│  │  │  ┌────────────┐  │  │  ┌────────────┐  │  │  ┌────────────┐  │                  │ │
│  │  │  │ Compacted  │  │  │  │ Compacted  │  │  │  │ Compacted  │  │                  │ │
│  │  │  │ Blocks     │  │  │  │ Blocks     │  │  │  │ Blocks     │  │                  │ │
│  │  │  └────────────┘  │  │  └────────────┘  │  │  └────────────┘  │                  │ │
│  │  └──────────────────┘  └──────────────────┘  └──────────────────┘                  │ │
│  │                                                                                     │ │
│  │  Long-term: Upload compacted blocks to Object Storage (S3/GCS)                     │ │
│  └─────────────────────────────────────────────────────────────────────────────────────┘ │
│                                                                                          │
└──────────────────────────────────────────────────────────────────────────────────────────┘
```

### 7.2 Query Path

```
┌───────────────────────────────────────────────────────────────────────────┐
│                           QUERY PATH                                      │
│                                                                           │
│  ┌──────────┐    ┌───────────────┐    ┌─────────────────────────────┐    │
│  │Dashboard │    │  Grafana /    │    │    Query Frontend           │    │
│  │   UI     │───▶│  API Client   │───▶│                             │    │
│  │          │    │               │    │  - Auth + tenant isolation  │    │
│  └──────────┘    └───────────────┘    │  - Query parsing           │    │
│                                       │  - Time-range splitting    │    │
│                                       │  - Result cache check      │    │
│                                       │  - Rate limiting           │    │
│                                       └─────────────┬───────────────┘    │
│                                                     │                     │
│                                                     ▼                     │
│                                       ┌─────────────────────────────┐    │
│                                       │     Query Engine            │    │
│                                       │                             │    │
│                                       │  - PromQL parser + planner  │    │
│                                       │  - Parallel shard fanout    │    │
│                                       │  - Merge + aggregate        │    │
│                                       │  - Apply functions          │    │
│                                       └──┬──────────┬──────────┬────┘    │
│                                          │          │          │          │
│                          ┌───────────────┘          │          └────┐     │
│                          ▼                          ▼               ▼     │
│                   ┌────────────┐          ┌────────────┐    ┌──────────┐ │
│                   │Store Node 0│          │Store Node 1│    │Store N   │ │
│                   │ (local)    │          │ (local)    │    │(local)   │ │
│                   └──────┬─────┘          └──────┬─────┘    └────┬─────┘ │
│                          │                       │               │       │
│                          │        ┌──────────────┘               │       │
│                          ▼        ▼                              ▼       │
│                   ┌──────────────────┐                   ┌────────────┐  │
│                   │  Object Storage  │                   │ Result     │  │
│                   │  (S3/GCS) for    │                   │ Cache      │  │
│                   │  long-term data  │                   │ (Redis)    │  │
│                   └──────────────────┘                   └────────────┘  │
│                                                                           │
└───────────────────────────────────────────────────────────────────────────┘
```

### 7.3 Alerting Path

```
┌───────────────────────────────────────────────────────────────────────────┐
│                         ALERTING PATH                                     │
│                                                                           │
│  ┌─────────────────────────────────────────────────────────────────────┐  │
│  │                    Alert Evaluator (Rule Engine)                    │  │
│  │                                                                     │  │
│  │  For each rule (every eval_interval, e.g., 15s):                   │  │
│  │    1. Execute PromQL query against Query Engine                    │  │
│  │    2. Compare result to threshold                                  │  │
│  │    3. Update state machine: INACTIVE -> PENDING -> FIRING          │  │
│  │                                                                     │  │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐          │  │
│  │  │ Rule 1   │  │ Rule 2   │  │ Rule 3   │  │ Rule N   │          │  │
│  │  │ eval=15s │  │ eval=30s │  │ eval=15s │  │ eval=60s │          │  │
│  │  └────┬─────┘  └────┬─────┘  └────┬─────┘  └────┬─────┘          │  │
│  │       │              │              │              │               │  │
│  └───────┼──────────────┼──────────────┼──────────────┼───────────────┘  │
│          │              │              │              │                   │
│          └──────────────┼──────────────┼──────────────┘                   │
│                         ▼              ▼                                  │
│  ┌─────────────────────────────────────────────────────────────────────┐  │
│  │                    Alert Manager                                    │  │
│  │                                                                     │  │
│  │  ┌────────────┐  ┌────────────┐  ┌──────────────┐  ┌───────────┐  │  │
│  │  │ Grouping   │  │ Inhibition │  │  Silencing   │  │ Dedup     │  │  │
│  │  │            │  │            │  │  (Maint.     │  │           │  │  │
│  │  │ Combine    │  │ Suppress   │  │   windows)   │  │ Prevent   │  │  │
│  │  │ related    │  │ lower sev  │  │              │  │ duplicate │  │  │
│  │  │ alerts     │  │ if higher  │  │ Mute during  │  │ notifs    │  │  │
│  │  │            │  │ is firing  │  │ known issues │  │           │  │  │
│  │  └─────┬──────┘  └─────┬──────┘  └──────┬───────┘  └─────┬─────┘  │  │
│  │        │               │                │                │        │  │
│  └────────┼───────────────┼────────────────┼────────────────┼────────┘  │
│           │               │                │                │            │
│           └───────────────┼────────────────┘                │            │
│                           ▼                                 │            │
│  ┌─────────────────────────────────────────────────────────────────────┐  │
│  │                   NOTIFICATION DISPATCHER                          │  │
│  │                                                                     │  │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐          │  │
│  │  │PagerDuty │  │  Slack   │  │  Email   │  │ Webhook  │          │  │
│  │  │          │  │          │  │          │  │          │          │  │
│  │  └──────────┘  └──────────┘  └──────────┘  └──────────┘          │  │
│  │                                                                     │  │
│  │  + Escalation policies (if no ack in 15m, escalate to manager)    │  │
│  │  + On-call rotation integration                                    │  │
│  └─────────────────────────────────────────────────────────────────────┘  │
│                                                                           │
└───────────────────────────────────────────────────────────────────────────┘
```

---

## 8. Deep Dive

### 8.1 TSDB Storage Engine

#### Gorilla Compression (Facebook, 2015)

The key insight: consecutive samples from the same time series have highly predictable
patterns. Timestamps increase by a near-constant interval, and values change slowly.

**Timestamp Compression: Delta-of-Delta Encoding**

```
Raw timestamps:     1700000000, 1700000010, 1700000020, 1700000030, 1700000040
Deltas:                        10,          10,          10,          10
Delta-of-deltas:               0,           0,           0,           0

Encoding scheme:
  delta-of-delta = 0:          Store '0'                    (1 bit)
  delta-of-delta in [-63,64]:  Store '10' + value (7 bits)  (9 bits)
  delta-of-delta in [-255,256]:Store '110' + value (9 bits) (12 bits)
  delta-of-delta in [-2047,2048]: Store '1110' + value      (16 bits)
  Otherwise:                   Store '1111' + full 32 bits  (36 bits)

For regular 10s intervals: 1 bit per timestamp (vs 64 bits raw)
  Compression ratio: 64:1 for timestamps!
```

**Value Compression: XOR Encoding**

```
For float64 values that change slowly:

  v1 = 72.5   (IEEE 754: 0x4052200000000000)
  v2 = 72.8   (IEEE 754: 0x4052333333333333)

  XOR = v1 XOR v2 = 0x0000133333333333

  Encoding:
    XOR = 0:                 Store '0'                          (1 bit)
    XOR != 0, same position: Store '10' + meaningful bits       (2 + N bits)
    XOR != 0, new position:  Store '11' + leading zeros (5b)
                             + length of meaningful (6b) + bits (variable)

  For slowly changing values: ~15-25 bits per value (vs 64 bits raw)
  Compression ratio: ~3-4x for values
```

**Combined Compression**

```
Overall per sample:
  Timestamp: ~1-2 bits (best case) to ~36 bits (worst case)
  Value:     ~1 bit (best case) to ~77 bits (worst case)
  Average:   ~16 bits = 2 bytes per sample

  Raw: 16 bytes per sample (8 timestamp + 8 value)
  Compressed: ~2 bytes per sample
  Ratio: ~8x compression on data alone

  With index overhead factored in: ~12x overall compression
```

#### Head Block and Block Lifecycle

```
Timeline of block lifecycle:

Time ──────────────────────────────────────────────────────────▶

│◄──── Head Block (in-memory) ────▶│
│         0:00 - 2:00              │
│  Samples appended to memChunks   │
│  WAL entries written to disk     │
│                                  │
│                            ┌─────┴─────────────────┐
│                            │ CUT: Head persisted    │
│                            │ as Block_01 on disk    │
│                            │ New head starts 2:00   │
│                            └───────────────────────┘
│
│  Block_01         Block_02         Block_03
│  [0:00-2:00]      [2:00-4:00]      [4:00-6:00]
│       │                │                │
│       └────────────────┘                │
│              │                          │
│        ┌─────┴──────┐                   │
│        │ COMPACTION  │                   │
│        │ Merge into  │                   │
│        │ Block_C1    │                   │
│        │ [0:00-4:00] │                   │
│        └─────────────┘                   │
│                                          │
│        Block_C1              Block_03    │
│        [0:00-4:00]          [4:00-6:00]  │
│              │                    │      │
│              └────────────────────┘      │
│                       │                  │
│                 ┌─────┴──────┐           │
│                 │ COMPACTION  │           │
│                 │ Block_C2    │           │
│                 │ [0:00-6:00] │           │
│                 └─────────────┘           │
│                                          │
│  After retention period: delete or upload to object storage
```

#### Compaction Process

```
┌──────────────────────────────────────────────────────────────┐
│                    COMPACTION ENGINE                          │
│                                                              │
│  Input: Block_A [0:00-2:00] + Block_B [2:00-4:00]          │
│                                                              │
│  Steps:                                                      │
│  1. Merge-sort all series across blocks                      │
│  2. Re-encode chunks for optimal compression                 │
│  3. Rebuild inverted index                                   │
│  4. Apply tombstones (deleted series)                        │
│  5. Drop out-of-retention samples                            │
│  6. Write new block atomically                               │
│  7. Swap references, delete old blocks                       │
│                                                              │
│  Levels:                                                     │
│    L0: 2-hour blocks (raw from head)                         │
│    L1: 6-hour blocks (3 x L0 merged)                        │
│    L2: 24-hour blocks (4 x L1 merged)                       │
│    L3: 7-day blocks (7 x L2 merged) -- for long-term store  │
│                                                              │
│  Benefits:                                                   │
│  - Fewer blocks to scan for queries                          │
│  - Better compression (more data to find patterns)           │
│  - Cleanup of deleted series                                 │
│  - Reduced file handle count                                 │
│                                                              │
└──────────────────────────────────────────────────────────────┘
```

### 8.2 Ingestion Pipeline

#### Push vs Pull Model

```
┌─────────────────────────────────────┬────────────────────────────────────────┐
│           PUSH MODEL                │           PULL MODEL                   │
│        (StatsD / OTel / HTTP)       │       (Prometheus scrape)              │
│                                     │                                        │
│  ┌──────────┐    ┌──────────────┐   │   ┌──────────────┐    ┌──────────┐   │
│  │  App     │───▶│  Push       │   │   │  Scrape      │───▶│  Target  │   │
│  │  (client │    │  Gateway    │   │   │  Manager     │    │ /metrics │   │
│  │   SDK)   │    │             │   │   │              │    │ endpoint │   │
│  └──────────┘    └──────────────┘   │   └──────────────┘    └──────────┘   │
│                                     │                                        │
│  Pros:                              │   Pros:                                │
│  + Short-lived jobs supported       │   + No client SDK needed               │
│  + Client controls send rate        │   + Server controls load               │
│  + Events/fire-and-forget           │   + Automatic up/down detection        │
│  + Lower latency to ingestion       │   + Guaranteed freshness               │
│                                     │                                        │
│  Cons:                              │   Cons:                                │
│  - Client must handle backpressure  │   - Targets must expose HTTP endpoint  │
│  - Risk of overwhelming receiver    │   - Higher latency (poll interval)     │
│  - Client needs server address      │   - Needs service discovery            │
│  - Harder to detect "down"          │   - Not suitable for short-lived jobs  │
│                                     │                                        │
└─────────────────────────────────────┴────────────────────────────────────────┘
```

#### Write-Ahead Log (WAL)

```
┌──────────────────────────────────────────────────────────────────────┐
│                    WAL WRITE PATH                                    │
│                                                                      │
│   Incoming sample: (metric="cpu", host="web-1", ts=1700000010, 72.5)│
│                                                                      │
│   Step 1: Validate                                                   │
│     - Check label cardinality limits                                 │
│     - Verify timestamp within acceptable range (+/- 1 hour)          │
│     - Check tenant quotas                                            │
│                                                                      │
│   Step 2: WAL Append (fsync to disk)                                 │
│     ┌──────────────────────────────────────────────────┐             │
│     │ WAL Segment File (128 MB each)                   │             │
│     │                                                  │             │
│     │  Record Type │ Series ID │ Timestamp │ Value     │             │
│     │  (1 byte)    │ (8 bytes) │ (8 bytes) │ (8 bytes) │             │
│     │                                                  │             │
│     │  Types: SERIES (new series + labels)             │             │
│     │         SAMPLES (batch of data points)           │             │
│     │         TOMBSTONE (deletions)                    │             │
│     └──────────────────────────────────────────────────┘             │
│                                                                      │
│   Step 3: Append to Head Block (in-memory)                           │
│     - Lookup or create series by label hash                          │
│     - Append to memChunk (Gorilla-compressed in memory)              │
│     - Update inverted index posting lists                            │
│                                                                      │
│   Step 4: Acknowledge to client (after WAL + memory)                 │
│                                                                      │
│   Recovery after crash:                                               │
│     - Replay WAL segments from last checkpoint                       │
│     - Rebuild head block in memory                                   │
│     - Truncate WAL after successful head block persistence           │
│                                                                      │
└──────────────────────────────────────────────────────────────────────┘
```

#### Batching and Write Optimization

```
┌──────────────────────────────────────────────────────────────────────┐
│                 WRITE BATCHING PIPELINE                               │
│                                                                      │
│   Source ──▶ Agent Batch ──▶ Network ──▶ Ingester Batch ──▶ WAL     │
│                                                                      │
│   Client-Side Batching:                                              │
│     ┌─────────────────────────────────────────────┐                  │
│     │  Buffer: 1000 samples OR 10s flush interval │                  │
│     │  Compress: Snappy/zstd before sending       │                  │
│     │  Retry: exponential backoff on failure      │                  │
│     │  Queue: 100MB disk queue for offline buffer │                  │
│     └─────────────────────────────────────────────┘                  │
│                                                                      │
│   Server-Side Batching:                                              │
│     ┌─────────────────────────────────────────────┐                  │
│     │  Receive batch from network                 │                  │
│     │  Sort samples by series (locality)          │                  │
│     │  WAL: write single record for entire batch  │                  │
│     │  Head: batch append per series              │                  │
│     │  Fsync WAL every 100ms (tunable)            │                  │
│     └─────────────────────────────────────────────┘                  │
│                                                                      │
│   Throughput target per ingester node:                                │
│     - 2M samples/sec sustained                                       │
│     - WAL write: ~32 MB/sec (2M x 16 bytes)                         │
│     - Memory: ~4-8 GB for head block (2h window, compressed)         │
│                                                                      │
└──────────────────────────────────────────────────────────────────────┘
```

### 8.3 Query Engine

#### PromQL Execution Model

```
Query: rate(http_requests_total{service="api", status=~"5.."}[5m])

┌──────────────────────────────────────────────────────────────────────┐
│                    QUERY EXECUTION PIPELINE                           │
│                                                                      │
│  Step 1: PARSE                                                       │
│    ┌──────────────────────────────────────────────┐                  │
│    │  AST:                                        │                  │
│    │    Call("rate",                               │                  │
│    │      MatrixSelector(                         │                  │
│    │        name="http_requests_total",           │                  │
│    │        matchers=[                            │                  │
│    │          service="api",                      │                  │
│    │          status=~"5.."                       │                  │
│    │        ],                                    │                  │
│    │        range=5m                              │                  │
│    │      )                                       │                  │
│    │    )                                         │                  │
│    └──────────────────────────────────────────────┘                  │
│                                                                      │
│  Step 2: PLAN                                                        │
│    ┌──────────────────────────────────────────────┐                  │
│    │  1. Resolve time range: [now-5m, now]        │                  │
│    │  2. Identify shards that hold these series   │                  │
│    │  3. Determine which blocks to read           │                  │
│    │     - Head block: always (for recent data)   │                  │
│    │     - Persisted blocks overlapping [t-5m, t] │                  │
│    │  4. Check query result cache                 │                  │
│    └──────────────────────────────────────────────┘                  │
│                                                                      │
│  Step 3: FETCH (parallel across shards)                              │
│    ┌──────────────────────────────────────────────┐                  │
│    │  For each shard:                             │                  │
│    │    a. Inverted index lookup:                 │                  │
│    │       Intersect(posting["__name__=http_req"],│                  │
│    │                 posting["service=api"],      │                  │
│    │                 posting_regex["status=5.."])  │                  │
│    │       = matching series IDs                  │                  │
│    │                                              │                  │
│    │    b. For each series ID:                    │                  │
│    │       Read chunk data for [now-5m, now]      │                  │
│    │       Decompress Gorilla-encoded samples     │                  │
│    │       Return iterator of (timestamp, value)  │                  │
│    └──────────────────────────────────────────────┘                  │
│                                                                      │
│  Step 4: EVALUATE                                                    │
│    ┌──────────────────────────────────────────────┐                  │
│    │  For each matched series:                    │                  │
│    │    rate() = (last_value - first_value)        │                  │
│    │            / (last_ts - first_ts)             │                  │
│    │    (with counter reset handling)              │                  │
│    │                                              │                  │
│    │  Return vector of (labels, value) pairs      │                  │
│    └──────────────────────────────────────────────┘                  │
│                                                                      │
│  Step 5: MERGE (for distributed queries)                             │
│    ┌──────────────────────────────────────────────┐                  │
│    │  Collect partial results from all shards     │                  │
│    │  Merge series with same labels               │                  │
│    │  Apply outer aggregations (sum, avg)          │                  │
│    │  Cache result with TTL = step interval       │                  │
│    └──────────────────────────────────────────────┘                  │
│                                                                      │
└──────────────────────────────────────────────────────────────────────┘
```

#### Common PromQL Functions and Execution

```
┌────────────────────┬──────────────────────────────────────────────────┐
│ Function           │ Execution                                        │
├────────────────────┼──────────────────────────────────────────────────┤
│ rate(v[5m])        │ Per-second rate of counter increase over 5m.     │
│                    │ Handles counter resets. Extrapolates edges.      │
├────────────────────┼──────────────────────────────────────────────────┤
│ avg_over_time(     │ Average of all samples in the range window.      │
│   v[5m])           │ Simple mean: sum(values) / count(values).        │
├────────────────────┼──────────────────────────────────────────────────┤
│ histogram_quantile │ Calculates the q-th quantile from histogram      │
│ (0.99, v)          │ buckets using linear interpolation.              │
├────────────────────┼──────────────────────────────────────────────────┤
│ sum by (svc)(      │ Aggregation: sum across all series, group by     │
│   rate(...))       │ the "svc" label. Executed after inner function.  │
├────────────────────┼──────────────────────────────────────────────────┤
│ topk(10, ...)      │ Returns top-10 series by value. Requires full    │
│                    │ evaluation then sort. NOT distributable easily.  │
├────────────────────┼──────────────────────────────────────────────────┤
│ predict_linear(    │ Simple linear regression over range. Useful for  │
│   v[1h], 4*3600)   │ "disk full in 4 hours" alerts.                   │
└────────────────────┴──────────────────────────────────────────────────┘
```

#### Query Result Caching

```
┌──────────────────────────────────────────────────────────────────────┐
│                    QUERY RESULT CACHE                                 │
│                                                                      │
│  Cache Key: hash(tenant_id, query_string, aligned_time_range, step) │
│                                                                      │
│  Strategy: Split-and-Cache                                           │
│                                                                      │
│  Query: avg(cpu) from 10:00 to 12:00 step=60s                       │
│                                                                      │
│  ┌──────────────────────────────────────────────────────┐            │
│  │  Cache has:  [10:00 - 11:00]  HIT                    │            │
│  │  Missing:    [11:00 - 12:00]  MISS -> query TSDB     │            │
│  │  Result:     Merge cached + fresh, cache [11:00-12:00]│           │
│  └──────────────────────────────────────────────────────┘            │
│                                                                      │
│  Cache eviction:                                                     │
│  - TTL = step interval (e.g., 60s for step=60s queries)             │
│  - For "now" queries: short TTL (15s)                                │
│  - For historical queries: long TTL (1h)                             │
│  - LRU eviction when memory pressure                                │
│                                                                      │
│  Implementation: Redis cluster with ~100 GB capacity                 │
│  Hit rate target: 60-80% for dashboard queries                       │
│                                                                      │
└──────────────────────────────────────────────────────────────────────┘
```

### 8.4 Alerting Engine

#### Alert State Machine

```
┌──────────────────────────────────────────────────────────────────────┐
│                  ALERT STATE MACHINE                                 │
│                                                                      │
│                                                                      │
│   ┌───────────┐     condition      ┌───────────┐     "for"          │
│   │           │     becomes        │           │     duration       │
│   │ INACTIVE  │────────true───────▶│  PENDING  │──────elapsed──┐   │
│   │           │                    │           │                │   │
│   └───────────┘                    └─────┬─────┘                │   │
│        ▲                                 │                      │   │
│        │                          condition                     ▼   │
│        │                          becomes                ┌──────────┐│
│        │                          false                  │          ││
│        │                                │                │ FIRING   ││
│        │                                │                │          ││
│        │                                ▼                └────┬─────┘│
│        │                          ┌───────────┐              │      │
│        │                          │           │    condition │      │
│        │            resolve_      │ INACTIVE  │    becomes   │      │
│        │            timeout       │ (reset)   │    false     │      │
│        │               │         └───────────┘       │      │      │
│        │               │                             ▼      │      │
│        │               │                       ┌──────────┐ │      │
│        │               └──────────────────────▶│          │◀┘      │
│        │                                       │ RESOLVED │        │
│        │                                       │          │        │
│        │                                       └────┬─────┘        │
│        │                                            │              │
│        └────────────── after resolve_timeout ───────┘              │
│                                                                      │
│  Key timings:                                                        │
│    eval_interval:    15s (how often the rule is evaluated)           │
│    for:              5m  (PENDING must last this long before FIRING) │
│    resolve_timeout:  5m  (RESOLVED returns to INACTIVE)             │
│    repeat_interval:  4h  (re-send FIRING notification)              │
│                                                                      │
└──────────────────────────────────────────────────────────────────────┘
```

#### Grouping, Inhibition, and Silencing

```
┌──────────────────────────────────────────────────────────────────────┐
│                ALERT ROUTING PIPELINE                                 │
│                                                                      │
│  GROUPING:                                                           │
│  ┌──────────────────────────────────────────────────────────────┐    │
│  │  group_by: [service, region]                                 │    │
│  │                                                              │    │
│  │  Firing alerts:                                              │    │
│  │    HighErrorRate{service=api, host=web-001, region=us-east}  │    │
│  │    HighErrorRate{service=api, host=web-002, region=us-east}  │    │
│  │    HighErrorRate{service=api, host=web-003, region=us-east}  │    │
│  │                                                              │    │
│  │  Grouped into ONE notification:                              │    │
│  │    "3 instances of HighErrorRate for service=api,            │    │
│  │     region=us-east"                                          │    │
│  │                                                              │    │
│  │  Purpose: Reduce notification noise (3 alerts -> 1 notif)   │    │
│  └──────────────────────────────────────────────────────────────┘    │
│                                                                      │
│  INHIBITION:                                                         │
│  ┌──────────────────────────────────────────────────────────────┐    │
│  │  Rule: If "ClusterDown" is firing for service=X,             │    │
│  │        suppress all "HighLatency" alerts for service=X       │    │
│  │                                                              │    │
│  │  inhibit_rules:                                              │    │
│  │    - source_match: {alertname: ClusterDown}                  │    │
│  │      target_match: {alertname: HighLatency}                  │    │
│  │      equal: [service]                                        │    │
│  │                                                              │    │
│  │  Purpose: Don't alert on symptoms when root cause is known   │    │
│  └──────────────────────────────────────────────────────────────┘    │
│                                                                      │
│  SILENCING:                                                          │
│  ┌──────────────────────────────────────────────────────────────┐    │
│  │  Silence: {matchers: [service=api, region=us-east],          │    │
│  │           starts_at: 2024-01-15T02:00:00Z,                   │    │
│  │           ends_at: 2024-01-15T04:00:00Z,                     │    │
│  │           created_by: "oncall-engineer",                     │    │
│  │           comment: "Planned maintenance window"}             │    │
│  │                                                              │    │
│  │  Purpose: Mute alerts during known maintenance windows       │    │
│  └──────────────────────────────────────────────────────────────┘    │
│                                                                      │
│  ESCALATION:                                                         │
│  ┌──────────────────────────────────────────────────────────────┐    │
│  │  Level 1: Slack notification (immediate)                     │    │
│  │  Level 2: PagerDuty to on-call (after 5 min no ack)         │    │
│  │  Level 3: PagerDuty to manager (after 15 min no ack)        │    │
│  │  Level 4: Phone call to VP Eng (after 30 min no ack)        │    │
│  └──────────────────────────────────────────────────────────────┘    │
│                                                                      │
└──────────────────────────────────────────────────────────────────────┘
```

#### Dual Alert Evaluation for HA

```
┌──────────────────────────────────────────────────────────────────────┐
│             HIGH-AVAILABILITY ALERT EVALUATION                       │
│                                                                      │
│  Problem: Single alert evaluator is a SPOF for critical alerts      │
│                                                                      │
│  Solution: Run 2+ independent evaluators with deduplication         │
│                                                                      │
│  ┌────────────────┐          ┌────────────────┐                     │
│  │  Evaluator A   │          │  Evaluator B   │                     │
│  │  (primary)     │          │  (replica)     │                     │
│  │                │          │                │                     │
│  │  Eval Rule 1   │          │  Eval Rule 1   │                     │
│  │  Eval Rule 2   │          │  Eval Rule 2   │                     │
│  │  ...           │          │  ...           │                     │
│  └───────┬────────┘          └───────┬────────┘                     │
│          │                           │                               │
│          └──────────┬────────────────┘                               │
│                     ▼                                                │
│          ┌──────────────────┐                                        │
│          │  Alert Manager   │                                        │
│          │  Cluster (HA)    │                                        │
│          │                  │                                        │
│          │  Gossip protocol │                                        │
│          │  for dedup:      │                                        │
│          │  Same alert from │                                        │
│          │  A and B =       │                                        │
│          │  ONE notification│                                        │
│          └──────────────────┘                                        │
│                                                                      │
│  Dedup key: hash(alertname + sorted_labels + firing_since)          │
│  Clock sync requirement: NTP within 1 second across evaluators      │
│                                                                      │
└──────────────────────────────────────────────────────────────────────┘
```

---

## 9. Partitioning Strategy

### 9.1 Partitioning Dimensions

```
┌──────────────────────────────────────────────────────────────────────┐
│                   PARTITIONING STRATEGY                               │
│                                                                      │
│  Three dimensions of partitioning:                                   │
│                                                                      │
│  1. BY TENANT (for multi-tenant SaaS)                               │
│     ┌──────────┐  ┌──────────┐  ┌──────────┐                       │
│     │ Tenant A │  │ Tenant B │  │ Tenant C │                       │
│     │ (small)  │  │ (large)  │  │ (medium) │                       │
│     │ Shard 0  │  │ Shards   │  │ Shard 5  │                       │
│     │          │  │ 1,2,3,4  │  │          │                       │
│     └──────────┘  └──────────┘  └──────────┘                       │
│     Isolation: tenant B cannot impact tenant A's queries            │
│                                                                      │
│  2. BY METRIC NAME HASH (within a tenant)                           │
│     shard_id = hash(tenant_id + metric_name) % num_shards           │
│                                                                      │
│     Benefits:                                                        │
│     + All samples for same metric on same shard                     │
│     + Efficient range queries for single metric                      │
│     + Even distribution across shards                                │
│                                                                      │
│     Drawback:                                                        │
│     - Cross-metric queries (joins) require scatter-gather            │
│                                                                      │
│  3. BY TIME RANGE                                                    │
│     ┌────────────┐  ┌────────────┐  ┌────────────┐                  │
│     │  Recent    │  │  Mid-term  │  │  Long-term │                  │
│     │  (0-2d)    │  │  (2d-30d)  │  │  (30d-3y)  │                  │
│     │  SSD/NVMe  │  │  SSD       │  │ Object Stor│                  │
│     │  Hot tier  │  │  Warm tier │  │  Cold tier  │                  │
│     └────────────┘  └────────────┘  └────────────┘                  │
│                                                                      │
│     Queries automatically fan out to appropriate tiers               │
│                                                                      │
└──────────────────────────────────────────────────────────────────────┘
```

### 9.2 Consistent Hashing for Shard Assignment

```
┌──────────────────────────────────────────────────────────────────────┐
│              CONSISTENT HASH RING FOR INGESTERS                      │
│                                                                      │
│  Hash Ring (tokens per ingester = 128 virtual nodes):               │
│                                                                      │
│                        Token 0                                       │
│                          │                                           │
│                     ┌────┴────┐                                      │
│                ────▶│  Ing-A  │◀────                                 │
│               │     └─────────┘     │                                │
│               │                     │                                │
│         ┌─────┴───┐           ┌─────┴───┐                           │
│         │  Ing-D  │           │  Ing-B  │                           │
│         └─────┬───┘           └─────┬───┘                           │
│               │                     │                                │
│               │     ┌─────────┐     │                                │
│                ────▶│  Ing-C  │◀────                                 │
│                     └────┬────┘                                      │
│                          │                                           │
│                     Token 2^32                                       │
│                                                                      │
│  Series assignment:                                                  │
│    series_token = hash(tenant_id + sorted_labels)                   │
│    primary_ingester = first node clockwise from series_token        │
│    replica_ingesters = next N-1 nodes (for replication factor N)    │
│                                                                      │
│  Rebalancing on scale-out:                                           │
│    - New ingester gets tokens on the ring                            │
│    - Only ~1/N of series need to move                               │
│    - Transfer happens in background (WAL replay)                    │
│    - Dual-write during transition period                             │
│                                                                      │
└──────────────────────────────────────────────────────────────────────┘
```

---

## 10. Caching Strategy

```
┌──────────────────────────────────────────────────────────────────────┐
│                     CACHING LAYERS                                    │
│                                                                      │
│  LAYER 1: Head Block (In-Memory) -- Always Active                   │
│  ┌──────────────────────────────────────────────────────────────┐    │
│  │  What: Latest 2 hours of all active series                   │    │
│  │  Size: 4-16 GB per ingester (depends on cardinality)        │    │
│  │  Hit rate: 100% for "last N minutes" queries                │    │
│  │  Implementation: Custom memChunks with Gorilla compression  │    │
│  └──────────────────────────────────────────────────────────────┘    │
│                                                                      │
│  LAYER 2: Chunk Cache (LRU)                                         │
│  ┌──────────────────────────────────────────────────────────────┐    │
│  │  What: Recently accessed compressed chunks from disk blocks  │    │
│  │  Size: 16-64 GB per store node                              │    │
│  │  Key: (block_id, series_id, chunk_index)                    │    │
│  │  Hit rate: 70-85% (dashboards hit same chunks repeatedly)   │    │
│  │  Implementation: In-process LRU or external Memcached       │    │
│  └──────────────────────────────────────────────────────────────┘    │
│                                                                      │
│  LAYER 3: Index / Posting List Cache                                │
│  ┌──────────────────────────────────────────────────────────────┐    │
│  │  What: Inverted index posting lists for label lookups        │    │
│  │  Size: 2-8 GB per store node                                │    │
│  │  Key: (block_id, label_name, label_value)                   │    │
│  │  Hit rate: 90%+ (label cardinality is bounded)              │    │
│  │  Implementation: In-process concurrent hashmap              │    │
│  └──────────────────────────────────────────────────────────────┘    │
│                                                                      │
│  LAYER 4: Query Result Cache (Shared)                               │
│  ┌──────────────────────────────────────────────────────────────┐    │
│  │  What: Full query results for dashboard panels               │    │
│  │  Size: 50-200 GB (Redis cluster)                            │    │
│  │  Key: hash(tenant, query, time_range, step)                 │    │
│  │  TTL: min(step, 60s) for recent; 1h for historical          │    │
│  │  Hit rate: 60-80% for dashboard traffic                     │    │
│  │  Split-cache: partial hits for overlapping time ranges      │    │
│  └──────────────────────────────────────────────────────────────┘    │
│                                                                      │
│  LAYER 5: Metadata Cache                                             │
│  ┌──────────────────────────────────────────────────────────────┐    │
│  │  What: Tenant configs, alert rules, dashboard definitions    │    │
│  │  Size: 1-2 GB                                               │    │
│  │  TTL: 30-60 seconds (near real-time updates)                │    │
│  │  Implementation: Local in-process + Redis                   │    │
│  └──────────────────────────────────────────────────────────────┘    │
│                                                                      │
└──────────────────────────────────────────────────────────────────────┘
```

---

## 11. Replication

```
┌──────────────────────────────────────────────────────────────────────┐
│                    REPLICATION STRATEGY                               │
│                                                                      │
│  WRITE PATH (Quorum Writes, RF=3)                                   │
│  ┌──────────────────────────────────────────────────────────────┐    │
│  │                                                              │    │
│  │  Client ──▶ Distributor ──┬──▶ Ingester A (primary)   ✓     │    │
│  │                           ├──▶ Ingester B (replica 1) ✓     │    │
│  │                           └──▶ Ingester C (replica 2) ✓     │    │
│  │                                                              │    │
│  │  Write acknowledged when quorum (2 of 3) succeed             │    │
│  │  Third write completes asynchronously (hinted handoff)       │    │
│  │                                                              │    │
│  │  Each ingester independently:                                │    │
│  │    - Writes to its own WAL                                   │    │
│  │    - Appends to its own head block                           │    │
│  │    - Persists its own blocks to disk                         │    │
│  │    - Uploads compacted blocks to object storage              │    │
│  │                                                              │    │
│  └──────────────────────────────────────────────────────────────┘    │
│                                                                      │
│  READ PATH (Merge Query Results)                                    │
│  ┌──────────────────────────────────────────────────────────────┐    │
│  │                                                              │    │
│  │  Query Engine ──┬──▶ Store Node A ──▶ partial result A      │    │
│  │                 ├──▶ Store Node B ──▶ partial result B      │    │
│  │                 └──▶ Store Node C ──▶ partial result C      │    │
│  │                                                              │    │
│  │  Merge strategy:                                             │    │
│  │    - Deduplicate samples with same (series, timestamp)       │    │
│  │    - Prefer sample from primary replica                      │    │
│  │    - For range queries: union of samples, sort by time      │    │
│  │    - If one replica is slow/down: return partial results     │    │
│  │      with warning header                                     │    │
│  │                                                              │    │
│  └──────────────────────────────────────────────────────────────┘    │
│                                                                      │
│  LONG-TERM STORAGE (Eventual Consistency)                           │
│  ┌──────────────────────────────────────────────────────────────┐    │
│  │                                                              │    │
│  │  Object Storage (S3/GCS):                                    │    │
│  │    - Each ingester uploads its compacted blocks              │    │
│  │    - Blocks from replicas may overlap in time                │    │
│  │    - Compactor deduplicates overlapping blocks               │    │
│  │    - Eventually consistent: dedup happens asynchronously     │    │
│  │                                                              │    │
│  │  Downsampled data:                                           │    │
│  │    - Computed from compacted blocks (not from WAL)           │    │
│  │    - Eventual consistency is acceptable for historical data  │    │
│  │    - Downsampler runs as background job on object store data │    │
│  │                                                              │    │
│  └──────────────────────────────────────────────────────────────┘    │
│                                                                      │
└──────────────────────────────────────────────────────────────────────┘
```

---

## 12. Fault Tolerance

### 12.1 Failure Scenarios and Mitigations

```
┌──────────────────────────────────────────────────────────────────────┐
│                    FAULT TOLERANCE MATRIX                             │
│                                                                      │
│  FAILURE SCENARIO              │  MITIGATION                        │
│  ──────────────────────────────┼────────────────────────────────     │
│                                │                                     │
│  Single ingester crash         │  WAL recovery on restart.           │
│                                │  Replicas serve queries.            │
│                                │  Hash ring re-routes new writes.   │
│                                │                                     │
│  Ingester disk full            │  WAL truncation after checkpoint.   │
│                                │  Head block flush to free memory.   │
│                                │  Alert on disk usage > 80%.        │
│                                │                                     │
│  Kafka broker failure          │  Kafka RF=3, auto leader election.  │
│                                │  Producers retry with backoff.      │
│                                │  Consumer lag monitored.            │
│                                │                                     │
│  Store node failure            │  Query engine excludes failed node. │
│                                │  Returns partial results +warning.  │
│                                │  Data still available on replicas.  │
│                                │                                     │
│  Object storage unavailable    │  Local blocks serve recent queries. │
│                                │  Upload retried with exp backoff.   │
│                                │  Blocks cached on store nodes.      │
│                                │                                     │
│  Query engine OOM              │  Query limits: max samples, series. │
│                                │  Timeout enforcement (30s default). │
│                                │  Query splitting for large ranges.  │
│                                │                                     │
│  Network partition              │  Each side continues independently. │
│  (split-brain)                 │  Duplicate data reconciled later.   │
│                                │  Alert evaluators on both sides.    │
│                                │                                     │
│  Clock skew across hosts       │  Accept samples within +/- 1 hour. │
│                                │  Reject far-future timestamps.      │
│                                │  NTP monitoring as meta-metric.     │
│                                │                                     │
│  Cardinality explosion         │  Per-tenant series limit.           │
│  (label values unbounded)      │  Auto-detection + alert.            │
│                                │  Drop new series beyond limit.      │
│                                │                                     │
└──────────────────────────────────────────────────────────────────────┘
```

### 12.2 WAL Recovery Process

```
┌──────────────────────────────────────────────────────────────────────┐
│                    WAL RECOVERY ON RESTART                            │
│                                                                      │
│  1. Find last checkpoint file                                        │
│     checkpoint.000042                                                │
│       └─ Contains: snapshot of all active series + their labels     │
│                                                                      │
│  2. Find WAL segments after checkpoint                               │
│     segment-000043, segment-000044, segment-000045                   │
│                                                                      │
│  3. Replay segments sequentially                                     │
│     ┌─────────────────────────────────────────────┐                  │
│     │  For each record in segment:                │                  │
│     │    SERIES record: register series + labels  │                  │
│     │    SAMPLES record: append to head block     │                  │
│     │    TOMBSTONE record: mark series deleted     │                  │
│     │                                             │                  │
│     │  Skip samples older than head block window  │                  │
│     │  (already persisted to disk blocks)          │                  │
│     └─────────────────────────────────────────────┘                  │
│                                                                      │
│  4. Resume normal operation                                          │
│     - New head block with recovered data                             │
│     - WAL truncation of replayed segments                            │
│     - Create new checkpoint                                          │
│                                                                      │
│  Recovery time: ~30-60 seconds for 8 GB head block                   │
│  Data loss: zero (WAL is fsync'd)                                    │
│  Data gap: samples missed while node was down                        │
│    (covered by replicas for queries)                                 │
│                                                                      │
└──────────────────────────────────────────────────────────────────────┘
```

---

## 13. Scalability

### 13.1 Horizontal Scaling Strategy

```
┌──────────────────────────────────────────────────────────────────────┐
│                   SCALABILITY APPROACH                                │
│                                                                      │
│  INGESTION SCALING:                                                  │
│  ┌──────────────────────────────────────────────────────────────┐    │
│  │  Kafka partitions: scale from 64 to 1024 as load grows      │    │
│  │  Ingesters: stateless consumers, add more for throughput    │    │
│  │  Hash ring: auto-rebalance with new ingesters               │    │
│  │                                                              │    │
│  │  Scaling trigger: ingestion lag > 30s OR CPU > 70%          │    │
│  │  Scale step: add 10% more ingesters                         │    │
│  │  Cooldown: 10 minutes between scale events                  │    │
│  └──────────────────────────────────────────────────────────────┘    │
│                                                                      │
│  STORAGE SCALING:                                                    │
│  ┌──────────────────────────────────────────────────────────────┐    │
│  │  TSDB sharding:                                              │    │
│  │    Phase 1: 10 shards (50K series each)                     │    │
│  │    Phase 2: 100 shards (500K series each)                   │    │
│  │    Phase 3: 1000 shards (5M series each)                    │    │
│  │                                                              │    │
│  │  Each shard is an independent TSDB instance                 │    │
│  │  Shard splitting: when a shard exceeds size threshold       │    │
│  │    - Create two new shards with split hash range            │    │
│  │    - Copy relevant blocks to new shards                     │    │
│  │    - Redirect new writes via updated hash ring              │    │
│  │    - Drain old shard after verification                     │    │
│  │                                                              │    │
│  │  Object storage: virtually unlimited (S3/GCS)               │    │
│  │  Tier migration: hot (NVMe) -> warm (SSD) -> cold (S3)     │    │
│  └──────────────────────────────────────────────────────────────┘    │
│                                                                      │
│  QUERY SCALING:                                                      │
│  ┌──────────────────────────────────────────────────────────────┐    │
│  │  Read replicas:                                              │    │
│  │    - Query frontends are stateless, scale horizontally      │    │
│  │    - Store gateways: read-only access to object storage     │    │
│  │    - Add store gateways for long-range query throughput     │    │
│  │                                                              │    │
│  │  Query sharding:                                             │    │
│  │    - Time-range queries split into sub-ranges               │    │
│  │    - Each sub-range fetched from different store node       │    │
│  │    - Results merged at query frontend                       │    │
│  │                                                              │    │
│  │  Query limits (protect system):                              │    │
│  │    - max_samples_per_query: 50M                             │    │
│  │    - max_series_per_query: 100K                             │    │
│  │    - query_timeout: 120s                                    │    │
│  │    - max_concurrent_queries: 20 per tenant                  │    │
│  └──────────────────────────────────────────────────────────────┘    │
│                                                                      │
│  KAFKA BUFFERING:                                                    │
│  ┌──────────────────────────────────────────────────────────────┐    │
│  │  Purpose: Decouple ingestion speed from processing speed    │    │
│  │                                                              │    │
│  │  Normal: producer rate = consumer rate, lag ~0              │    │
│  │  Spike:  producer rate > consumer rate temporarily           │    │
│  │          Kafka buffers excess (24h retention)               │    │
│  │          Consumers catch up after spike subsides            │    │
│  │                                                              │    │
│  │  Benefits:                                                   │    │
│  │    - Absorbs burst traffic without data loss                │    │
│  │    - Allows ingester maintenance (drain + restart)          │    │
│  │    - Replay from offset for recovery / backfill             │    │
│  └──────────────────────────────────────────────────────────────┘    │
│                                                                      │
│  DOWNSAMPLING:                                                       │
│  ┌──────────────────────────────────────────────────────────────┐    │
│  │  Raw (10s) ──[after 15d]──▶ 1-minute avg/min/max/count     │    │
│  │  1-min     ──[after 90d]──▶ 5-minute avg/min/max/count     │    │
│  │  5-min     ──[after 1y] ──▶ 1-hour avg/min/max/count       │    │
│  │                                                              │    │
│  │  Storage savings:                                            │    │
│  │    10s -> 1m: 6x reduction in samples                       │    │
│  │    1m -> 5m:  5x reduction                                  │    │
│  │    5m -> 1h:  12x reduction                                 │    │
│  │    Total for 3-year data: ~360x fewer samples than raw      │    │
│  │                                                              │    │
│  │  Query engine auto-selects resolution based on time range:  │    │
│  │    Last 6h:  raw (10s)                                      │    │
│  │    Last 7d:  1-minute                                       │    │
│  │    Last 90d: 5-minute                                       │    │
│  │    Last 3y:  1-hour                                         │    │
│  └──────────────────────────────────────────────────────────────┘    │
│                                                                      │
└──────────────────────────────────────────────────────────────────────┘
```

---

## 14. Monitoring the Monitoring System (Meta)

The monitoring system must monitor itself. This is a bootstrapping problem -- if the
monitoring system is down, who alerts you?

```
┌──────────────────────────────────────────────────────────────────────┐
│              META-MONITORING METRICS                                  │
│                                                                      │
│  INGESTION HEALTH:                                                   │
│  ┌──────────────────────────────────────────────────────────────┐    │
│  │  monitoring_ingestion_rate_total          (target: baseline) │    │
│  │  monitoring_ingestion_errors_total        (target: 0)       │    │
│  │  monitoring_kafka_consumer_lag            (target: < 1000)  │    │
│  │  monitoring_wal_size_bytes                (target: < 4 GB)  │    │
│  │  monitoring_head_series_active            (track cardinality)│    │
│  │  monitoring_samples_rejected_total        (cardinality limit)│    │
│  └──────────────────────────────────────────────────────────────┘    │
│                                                                      │
│  QUERY HEALTH:                                                       │
│  ┌──────────────────────────────────────────────────────────────┐    │
│  │  monitoring_query_duration_seconds        (p99 < 2s)        │    │
│  │  monitoring_query_errors_total            (target: 0)       │    │
│  │  monitoring_query_samples_scanned         (detect expensive)│    │
│  │  monitoring_query_cache_hit_ratio         (target: > 0.6)   │    │
│  │  monitoring_query_concurrent_active       (limit: 200)      │    │
│  └──────────────────────────────────────────────────────────────┘    │
│                                                                      │
│  STORAGE HEALTH:                                                     │
│  ┌──────────────────────────────────────────────────────────────┐    │
│  │  monitoring_tsdb_blocks_total             (count per node)  │    │
│  │  monitoring_tsdb_compactions_total        (should be steady)│    │
│  │  monitoring_tsdb_compaction_duration_sec   (track slowdowns) │    │
│  │  monitoring_storage_disk_usage_bytes      (target: < 80%)   │    │
│  │  monitoring_object_store_upload_failures   (target: 0)      │    │
│  └──────────────────────────────────────────────────────────────┘    │
│                                                                      │
│  ALERTING HEALTH:                                                    │
│  ┌──────────────────────────────────────────────────────────────┐    │
│  │  monitoring_alert_eval_duration_sec       (p99 < 5s)        │    │
│  │  monitoring_alert_notification_latency    (target: < 30s)   │    │
│  │  monitoring_alert_notification_failures   (target: 0)       │    │
│  │  monitoring_alert_rules_active            (count)           │    │
│  │  monitoring_alert_firing_total            (track trends)    │    │
│  └──────────────────────────────────────────────────────────────┘    │
│                                                                      │
│  CARDINALITY EXPLOSION DETECTION:                                    │
│  ┌──────────────────────────────────────────────────────────────┐    │
│  │  monitoring_tsdb_head_series_created_total (rate of new)    │    │
│  │  monitoring_label_cardinality{label="X"}   (unique values)  │    │
│  │                                                              │    │
│  │  Alert: rate(head_series_created_total[10m]) > 10000        │    │
│  │  "More than 10K new series/min -- potential cardinality      │    │
│  │   explosion. Check for unbounded labels like request_id,    │    │
│  │   user_id, or trace_id being used as metric labels."        │    │
│  └──────────────────────────────────────────────────────────────┘    │
│                                                                      │
│  BOOTSTRAPPING SOLUTION:                                             │
│  ┌──────────────────────────────────────────────────────────────┐    │
│  │  Option A: Separate small Prometheus instance monitors      │    │
│  │            the main monitoring cluster (independent failure  │    │
│  │            domain, alerts via separate PagerDuty)            │    │
│  │                                                              │    │
│  │  Option B: Canary probes from external service (e.g.,       │    │
│  │            synthetic monitoring from cloud provider)         │    │
│  │                                                              │    │
│  │  Option C: Health check endpoints polled by load balancer   │    │
│  │            with automatic page if all nodes fail             │    │
│  └──────────────────────────────────────────────────────────────┘    │
│                                                                      │
└──────────────────────────────────────────────────────────────────────┘
```

---

## 15. Trade-offs and Design Decisions

### 15.1 Push vs Pull Ingestion

```
┌──────────────────────────────────────────────────────────────────────┐
│  DECISION: Support BOTH push and pull with push as primary          │
│                                                                      │
│  Rationale:                                                          │
│  - Pull (Prometheus-style) is ideal for long-running services with  │
│    HTTP endpoints and Kubernetes service discovery                   │
│  - Push is necessary for short-lived batch jobs, serverless          │
│    functions, and environments behind NAT/firewalls                  │
│  - OTel Collector bridges both: scrapes targets AND receives push   │
│  - At scale, push through Kafka provides better buffering and       │
│    decouples sources from ingesters                                  │
│                                                                      │
│  Implementation:                                                     │
│  - Pull targets: Scrape Manager converts to push (remote_write)    │
│  - Push sources: Direct to Kafka or Push Gateway                    │
│  - Both converge at Kafka topic -> Ingesters                        │
│                                                                      │
└──────────────────────────────────────────────────────────────────────┘
```

### 15.2 Custom TSDB vs Existing Solutions

```
┌──────────────────────────────────────────────────────────────────────┐
│  DECISION: Build custom TSDB layer on top of proven primitives      │
│                                                                      │
│  Option A: Use Prometheus TSDB directly                              │
│    + Battle-tested, excellent single-node performance                │
│    - No native horizontal scaling                                    │
│    - Limited multi-tenancy                                           │
│                                                                      │
│  Option B: Use InfluxDB / TimescaleDB                               │
│    + Feature-rich, SQL-like queries                                  │
│    - Different query language (Flux / SQL vs PromQL)                 │
│    - Licensing concerns at scale                                     │
│                                                                      │
│  Option C: Custom TSDB engine (our choice)                          │
│    + Optimized for our exact access patterns                         │
│    + Full control over sharding, replication, compaction             │
│    + PromQL compatibility by design                                  │
│    - Higher engineering investment                                    │
│    - Must implement Gorilla compression, index, compaction ourselves │
│                                                                      │
│  Hybrid approach: Use Prometheus TSDB library as embedded engine    │
│  within custom distributed wrapper (like Thanos/Mimir approach)     │
│                                                                      │
└──────────────────────────────────────────────────────────────────────┘
```

### 15.3 PromQL vs SQL for Query Language

```
┌──────────────────────────────────────────────────────────────────────┐
│  DECISION: PromQL as primary, with SQL adapter for analytics        │
│                                                                      │
│  PromQL advantages:                                                  │
│  + Purpose-built for time-series (rate, irate, histogram_quantile) │
│  + Concise: rate(http_req{svc="api"}[5m]) vs complex SQL           │
│  + Industry standard, huge ecosystem (Grafana, exporters)           │
│  + Implicit time alignment and step evaluation                      │
│                                                                      │
│  SQL advantages:                                                     │
│  + More familiar to data analysts                                    │
│  + Better for ad-hoc exploration and JOINs                          │
│  + Can express complex business logic                                │
│                                                                      │
│  Approach: PromQL for ops dashboards and alerts (95% of queries),   │
│  SQL adapter (translate SQL to PromQL) for analytics use cases      │
│                                                                      │
└──────────────────────────────────────────────────────────────────────┘
```

### 15.4 Memory vs Disk Trade-off

```
┌──────────────────────────────────────────────────────────────────────┐
│  DECISION: Large memory head blocks with aggressive disk tiering    │
│                                                                      │
│  More memory (larger head block):                                    │
│  + Faster queries for recent data (no disk I/O)                     │
│  + Better write throughput (batch WAL, no random I/O)               │
│  + Fewer blocks to compact                                           │
│  - Higher cost per node                                              │
│  - Longer WAL recovery on restart                                    │
│  - Risk of data loss if WAL is corrupted                             │
│                                                                      │
│  Less memory (smaller head block, more disk):                        │
│  + Cheaper per node                                                  │
│  + Faster recovery (less WAL to replay)                              │
│  + More data on disk = better durability                             │
│  - Slower queries for recent data                                    │
│  - More frequent block flushes = more compaction work                │
│                                                                      │
│  Our choice: 2-hour head block (Prometheus default) with:           │
│  - 16-32 GB memory per ingester for head block + index              │
│  - NVMe SSD for persisted blocks (fast random read for queries)    │
│  - Object storage for blocks older than 24h (cheap, durable)       │
│  - Chunk cache to avoid disk I/O for repeated queries               │
│                                                                      │
└──────────────────────────────────────────────────────────────────────┘
```

### 15.5 Summary of Key Trade-offs

```
┌─────────────────────┬──────────────────────┬──────────────────────────┐
│ Decision            │ Option Chosen         │ Key Reason               │
├─────────────────────┼──────────────────────┼──────────────────────────┤
│ Ingestion model     │ Both push + pull      │ Flexibility for all      │
│                     │                      │ deployment models        │
├─────────────────────┼──────────────────────┼──────────────────────────┤
│ Storage engine      │ Custom on Prom TSDB  │ Control + proven engine  │
│                     │ library              │                          │
├─────────────────────┼──────────────────────┼──────────────────────────┤
│ Query language      │ PromQL primary       │ Industry standard,       │
│                     │                      │ concise for time-series  │
├─────────────────────┼──────────────────────┼──────────────────────────┤
│ Consistency         │ Eventual             │ AP over CP; monitoring   │
│                     │                      │ favors availability      │
├─────────────────────┼──────────────────────┼──────────────────────────┤
│ Replication         │ RF=3, quorum write   │ Balance durability +     │
│                     │                      │ write latency            │
├─────────────────────┼──────────────────────┼──────────────────────────┤
│ Head block size     │ 2 hours in-memory    │ Sweet spot for query     │
│                     │                      │ speed vs recovery time   │
├─────────────────────┼──────────────────────┼──────────────────────────┤
│ Long-term storage   │ Object store (S3)    │ Cost-effective, durable, │
│                     │                      │ virtually unlimited      │
├─────────────────────┼──────────────────────┼──────────────────────────┤
│ Alert dedup         │ Gossip-based AM      │ No SPOF, distributed     │
│                     │ cluster              │ deduplication            │
├─────────────────────┼──────────────────────┼──────────────────────────┤
│ Compression         │ Gorilla (delta-of-   │ 8-12x compression,       │
│                     │ delta + XOR)         │ proven at Facebook scale │
└─────────────────────┴──────────────────────┴──────────────────────────┘
```

---

## 16. Interview Questions and Answers

### Q1: How do you handle high cardinality labels that cause a cardinality explosion?

**Answer:**
High cardinality occurs when label values are unbounded (e.g., user_id, request_id,
IP address). A metric with 500K unique user IDs creates 500K separate time series.

Mitigations:
1. **Per-tenant series limits**: Enforce a hard cap (e.g., 10M active series). Reject
   new series beyond the limit with a clear error.
2. **Label validation at ingestion**: Block known high-cardinality labels (user_id,
   trace_id, email) from being used as metric labels. These belong in logs/traces.
3. **Cardinality monitoring**: Track `rate(head_series_created[10m])` and alert when
   it spikes (> 10K new series/min).
4. **Relabeling rules**: Drop or aggregate high-cardinality labels before storage
   (e.g., replace IP with subnet, replace user_id with user_tier).
5. **Adaptive limiting**: When a specific metric exceeds cardinality threshold, auto-
   drop the highest-cardinality label and alert the team to fix their instrumentation.

The key insight is that cardinality explosion is an **operational** problem, not just
a technical one. Education and guardrails prevent it better than after-the-fact cleanup.

---

### Q2: Explain Gorilla compression and why it works so well for time-series data.

**Answer:**
Gorilla compression (Facebook, 2015 paper "Gorilla: A Fast, Scalable, In-Memory Time
Series Database") exploits two properties of monitoring data:

1. **Timestamps are regular**: Metrics arrive at fixed intervals (10s, 30s, 60s), so
   the delta between consecutive timestamps is nearly constant. Delta-of-delta encoding
   captures this: if delta is always 10s, the delta-of-delta is 0, stored in 1 bit.
   For perfectly regular data, timestamps compress from 64 bits to 1 bit (~64x).

2. **Values change slowly**: CPU at 72.5% then 72.8% -- the IEEE 754 representations
   share most bits. XOR of consecutive values has many leading and trailing zeros.
   We encode: (a) identical value = 1 bit, (b) similar value = 2 bits + meaningful bits
   (~15-25 bits), (c) very different = 77 bits worst case. Average ~15 bits (~4x).

Combined: ~2 bytes per sample vs 16 bytes raw = ~8x compression. This means a server
with 64 GB RAM can hold ~26 billion compressed samples in memory for sub-millisecond
queries. For on-disk blocks, additional compaction across chunks achieves 12-15x overall.

---

### Q3: How do you prevent alert fatigue in a large-scale monitoring system?

**Answer:**
Alert fatigue occurs when operators receive so many alerts that they ignore them all,
including critical ones. Prevention strategies:

1. **Grouping**: Combine related alerts into single notifications. If 50 hosts have
   high CPU, send one alert "50 hosts with HighCPU in us-east" not 50 separate pages.

2. **Inhibition**: Suppress symptom alerts when the root cause is known. If "ClusterDown"
   is firing, suppress all "HighLatency" and "HighErrorRate" alerts for that cluster.

3. **Severity tiers**: Only page for critical alerts. Warning = Slack. Info = dashboard.
   Audit alert severity quarterly -- if a critical alert hasn't led to action in 90 days,
   downgrade or delete it.

4. **"For" duration**: Require the condition to persist for N minutes before firing.
   This eliminates transient spikes that self-resolve. `for: 5m` prevents 99% of flaps.

5. **Dead-man's switch**: Instead of alerting on every metric individually, use absence-
   of-heartbeat alerts. If the system stops reporting, that single alert covers everything.

6. **Alert ownership**: Every alert must have a team owner. Unowned alerts are deleted.
   Track alert-to-action ratio: if an alert fires 100 times and is actioned 2 times,
   it needs to be tuned or removed.

---

### Q4: How do you handle clock skew when collecting metrics from thousands of hosts?

**Answer:**
Clock skew is inevitable in distributed systems. A host with a drifted clock will send
timestamps that are in the past or future relative to the monitoring system's clock.

Strategies:
1. **Acceptance window**: Accept samples with timestamps within +/- 1 hour of server time.
   Reject anything outside this window with a clear error to the sender.

2. **Server-side timestamping**: For push-based ingestion, the server can optionally
   ignore the client timestamp and use its own receipt time. This avoids skew entirely
   but loses precision about when the metric was actually measured.

3. **Out-of-order sample handling**: The TSDB must handle out-of-order samples within
   the head block window. Prometheus added OOO sample support (since 2.39). Samples
   arriving "late" (within the OOO window) are inserted into the correct position.

4. **NTP monitoring**: Monitor NTP sync status as a meta-metric on every host. Alert
   when clock drift exceeds 500ms. Most environments use chrony/ntpd for < 10ms drift.

5. **Query-time tolerance**: When aligning samples to step boundaries, use a tolerance
   window (e.g., +/- 5 seconds from the expected step timestamp) to accommodate minor
   skew without creating gaps in graphs.

---

### Q5: How would you design multi-tenant isolation in a shared monitoring platform?

**Answer:**
Multi-tenancy requires isolation across several dimensions:

1. **Data isolation**: Every sample is tagged with tenant_id. The inverted index includes
   tenant_id in all posting lists. Queries are automatically scoped: the query engine
   prepends `{tenant_id="X"}` to every query, even if the user doesn't specify it.

2. **Ingestion isolation**: Per-tenant rate limits (samples/sec), series limits (max
   active series), and label limits (max labels per series, max label length). Enforced
   at the distributor/ingester layer. One tenant's burst cannot starve another.

3. **Query isolation**: Per-tenant query concurrency limits, max samples per query,
   and query timeout. Implemented via per-tenant queues in the query frontend with
   fair scheduling (weighted round-robin based on tenant tier).

4. **Storage isolation**: Logical separation (all tenants in same TSDB but prefixed)
   or physical separation (dedicated shards for large tenants). Object storage uses
   tenant-prefixed paths: `s3://metrics/{tenant_id}/blocks/...`

5. **Cost attribution**: Track ingestion volume, storage bytes, and query cost per
   tenant for chargeback. This also incentivizes tenants to reduce cardinality.

---

### Q6: How does the system handle a sudden 10x spike in ingestion rate?

**Answer:**
Spikes occur during incidents (many error metrics), deployments (new metrics), or
cardinality explosions. The system absorbs spikes through multiple layers:

1. **Kafka buffering**: The primary defense. Kafka absorbs the spike with its 24-hour
   retention. Consumer lag increases but no data is lost. The system processes the
   backlog after the spike subsides.

2. **Client-side buffering**: Well-behaved agents (OTel Collector, Datadog Agent) have
   local disk queues (100 MB - 1 GB). If the server is slow, the agent buffers locally
   and retries with exponential backoff.

3. **Backpressure signaling**: When ingesters are overloaded, they return HTTP 429
   (Too Many Requests) with Retry-After header. Clients back off gracefully.

4. **Auto-scaling**: Ingestion nodes auto-scale based on Kafka consumer lag or CPU
   utilization. New ingesters join the hash ring and take ownership of partitions.
   Scale-up takes 2-5 minutes (container start + WAL catch-up).

5. **Shedding**: As a last resort, drop samples for non-critical metrics. Priority
   classes: P0 (SLO metrics, never drop), P1 (infrastructure metrics, drop under
   extreme load), P2 (debug metrics, drop first). Shedding is logged and alerted.

---

### Q7: How do you implement efficient range queries over months of data?

**Answer:**
Querying months of data efficiently requires a combination of strategies:

1. **Automatic downsampling**: Instead of scanning 10-second raw data for a 90-day
   query (777M samples per series), use 5-minute downsampled data (26K samples per
   series). The query engine selects resolution based on the query time range and
   step size.

2. **Block-level pruning**: The TSDB index records min/max time for each block. For
   a query [Jan 1 - Mar 31], skip blocks outside that range entirely. With compacted
   7-day blocks, only 13 blocks need to be opened (not hundreds of 2-hour blocks).

3. **Parallel block scanning**: Each relevant block is scanned in parallel. For a
   distributed setup, different blocks live on different store nodes, enabling natural
   parallelism across the cluster.

4. **Object storage gateway caching**: Blocks from object storage (S3) are cached
   locally on store gateway nodes. Frequently queried historical blocks stay warm in
   the local NVMe cache, avoiding S3 latency.

5. **Query result caching**: Historical queries are highly cacheable because the data
   doesn't change. Cache with long TTL (1 hour+). Split-cache enables partial hits
   for overlapping time ranges.

---

### Q8: What happens when a TSDB storage node runs out of disk space?

**Answer:**
This is a critical failure mode. Prevention and graceful handling:

1. **Prevention**: Monitor disk usage as a P0 meta-metric. Alert at 70% usage with
   automated remediation: trigger compaction (merges blocks, reclaims tombstoned space),
   upload old blocks to object storage and delete local copies, extend volume (if cloud).

2. **Graceful degradation**: At 85% disk, the ingester stops accepting new series
   (existing series still append). At 90%, the ingester marks itself unhealthy in the
   hash ring, and the distributor routes writes to replicas.

3. **Emergency actions**: At 95%, force-delete oldest blocks (data still available in
   object storage or on replicas). WAL truncation to the latest checkpoint.

4. **Recovery**: Add a new ingester with fresh disk, or expand the existing volume.
   The hash ring rebalances, and the recovered node receives its share of new writes.
   Historical data is served from object storage or replicas.

---

### Q9: How would you implement recording rules for pre-computed aggregations?

**Answer:**
Recording rules pre-compute expensive queries and store the results as new time series.
This is essential for dashboard performance.

Example: `recording_rule: job:http_requests:rate5m = sum(rate(http_requests_total[5m])) by (job)`

1. **Evaluation**: A dedicated rule evaluator runs each recording rule at its configured
   interval (e.g., every 60s). It executes the PromQL expression against the query
   engine and gets the result vector.

2. **Storage**: The result is written back into the TSDB as a new metric
   (`job:http_requests:rate5m`) with the original labels plus any additional labels
   from the rule definition.

3. **Query optimization**: Dashboards query the pre-computed metric instead of the
   raw expression. A query that would scan 10M samples now reads 1K pre-aggregated
   samples. This reduces query latency from seconds to milliseconds.

4. **Consistency**: Recording rules use "staleness" markers. If the source data has
   gaps, the recording rule produces NaN, which propagates correctly through PromQL
   functions.

5. **Naming convention**: Follow `level:metric:operations` (e.g.,
   `job:http_requests:rate5m`). This makes it clear the metric is derived, not raw.

---

### Q10: How do you handle the "thundering herd" problem when many dashboards refresh simultaneously?

**Answer:**
When 1000 dashboards all refresh every 30 seconds, the query layer receives burst
traffic at the refresh boundaries (especially if they're all aligned to :00/:30).

1. **Jittered refresh**: The dashboard frontend adds random jitter (0-5 seconds) to
   the refresh interval. Instead of all dashboards hitting at T=30.000s, they spread
   across T=30.0s to T=35.0s. This smooths the query load.

2. **Query deduplication**: The query frontend detects identical queries arriving within
   a short window (e.g., 100ms). Only one query is executed; all requesters receive the
   same result. This is extremely effective when multiple users view the same dashboard.

3. **Result caching**: The query result cache serves repeat queries instantly. With a
   cache TTL of 15 seconds for "now" queries, at most 2 actual TSDB queries are made
   per 30-second refresh cycle per unique query.

4. **Request queuing**: Per-tenant query queues with fair scheduling. If a tenant sends
   100 queries simultaneously, they are queued and processed at a controlled rate (e.g.,
   20 concurrent). This prevents one tenant's dashboard storm from impacting others.

5. **Query coalescing at the store level**: Multiple queries reading the same time-series
   chunks can share the I/O. The chunk cache ensures that once a chunk is read from disk,
   subsequent queries for the same chunk get a cache hit.

---

### Q11: How would you implement anomaly detection without ML?

**Answer:**
Simple statistical methods are surprisingly effective for monitoring:

1. **Z-score alerting**: Calculate the rolling mean and standard deviation over a
   baseline window (e.g., same hour last 7 days). Alert when the current value exceeds
   mean +/- 3 standard deviations. PromQL:
   `(metric - avg_over_time(metric[7d])) / stddev_over_time(metric[7d]) > 3`

2. **Seasonal decomposition**: For metrics with daily/weekly patterns (traffic peaks
   at noon, drops at night), compare to the same period last week rather than a rolling
   average. PromQL: `metric / (metric offset 7d) > 2` (2x last week's value).

3. **Rate-of-change detection**: Alert on sudden changes rather than absolute values.
   `deriv(metric[5m]) > threshold` catches rapid spikes before they hit absolute limits.

4. **predict_linear()**: PromQL's built-in linear regression. Predict future values:
   `predict_linear(disk_usage[6h], 4*3600) > 0.9` means "disk will be 90% full in
   4 hours at current rate."

5. **Histogram percentile shifts**: Monitor p50/p99 ratio. If p99 grows while p50 is
   stable, tail latency is increasing, indicating emerging issues.

---

### Q12: How do you ensure alert notifications are delivered even when the monitoring system is partially down?

**Answer:**
Alert delivery is the most critical path in the monitoring system. Failures here mean
outages go unnoticed.

1. **HA Alert Manager cluster**: Run 3+ AlertManager instances using gossip protocol
   (Hashicorp memberlist). They share alert state and deduplicate notifications. If one
   fails, others continue sending.

2. **Dual evaluators**: Two independent alert evaluators run the same rules against
   (potentially different) data replicas. Both send to the AlertManager cluster, which
   deduplicates. If one evaluator is down, the other still fires alerts.

3. **Notification retry with persistence**: Failed notification attempts are persisted
   to a durable queue (not just in-memory retry). Retry with exponential backoff for
   up to 24 hours. After 24 hours, escalate through a different channel.

4. **Multi-channel redundancy**: Critical alerts go to both PagerDuty AND SMS AND Slack.
   If one channel's API is down, others still deliver. The AlertManager tracks delivery
   status per channel.

5. **Dead-man's switch**: An external watchdog (separate infrastructure) expects a
   heartbeat from the monitoring system every 60 seconds. If the heartbeat stops, the
   watchdog pages the on-call engineer through a completely independent channel (e.g.,
   a simple cron job that calls the PagerDuty API directly).

---

### Q13: How would you migrate from Prometheus to this distributed system with zero downtime?

**Answer:**
Migration must be gradual and reversible:

1. **Phase 1 - Dual Write**: Configure Prometheus to remote_write to the new system
   while continuing to serve queries locally. Both systems have the same data. Duration:
   2-4 weeks to build confidence.

2. **Phase 2 - Shadow Read**: Dashboard queries go to both systems. Compare results
   automatically (< 1% divergence acceptable for floating-point). Flag discrepancies
   for investigation. Duration: 1-2 weeks.

3. **Phase 3 - Read Cutover**: Point Grafana to the new system's query API. Keep
   Prometheus running as fallback. If issues arise, switch back instantly by changing
   the Grafana datasource.

4. **Phase 4 - Alert Cutover**: Migrate alert rules to the new system. Run dual
   evaluation for 1 week (both systems fire alerts, dedup at AlertManager level).
   Then disable Prometheus alerting.

5. **Phase 5 - Decommission**: Stop Prometheus scraping (new system handles pull now).
   Keep Prometheus data accessible for historical queries during transition. Archive
   and decommission after 30 days of successful operation.

Key: At every phase, rollback is possible within minutes. Never burn bridges.

---

### Q14: How do you handle metrics from ephemeral containers and serverless functions?

**Answer:**
Ephemeral workloads (containers that live < 60 seconds, Lambda functions) break the
pull model because the target disappears before it can be scraped.

1. **Push-based ingestion**: Use StatsD or OTLP push. The function/container sends
   metrics before it terminates. The OTel Collector sidecar or DaemonSet receives
   and forwards. No scrape endpoint needed.

2. **Aggregation at the edge**: Instead of sending every invocation as a separate
   time series, aggregate at the collector level. Sum request counts, compute latency
   histograms across invocations, emit one aggregated sample per interval.

3. **Staleness handling**: When a series stops receiving samples, mark it "stale" after
   5 minutes (configurable). Stale series are excluded from queries but the data
   remains. This prevents graphs from showing flat lines at the last known value.

4. **Instance labeling**: Use a stable label like `function_name` or `deployment_id`
   rather than `container_id` or `pod_name` for aggregation. The container ID changes
   on every restart, creating cardinality explosion. The function name is stable.

5. **Pushgateway pattern**: For batch jobs, push final metrics to a Pushgateway that
   holds them until scraped. The Pushgateway persists the last-pushed value for each
   metric family, surviving the job's termination.

---

### Q15: What are the most critical SLOs for a monitoring system itself, and how do you measure them?

**Answer:**
A monitoring system must be more reliable than what it monitors. Key SLOs:

1. **Ingestion availability**: 99.99% of valid samples must be accepted within 5 seconds
   of receipt. Measured by: synthetic canary that sends known samples every 10s and
   verifies they appear in queries within 30s. Missing canary = ingestion failure.

2. **Query availability**: 99.9% of dashboard queries must return within 2 seconds.
   Measured by: synthetic queries against known data every 30s. Track p50, p95, p99
   query latency. Error budget: 43 minutes of query downtime per month.

3. **Alert latency**: 99% of threshold breaches must trigger a notification within
   60 seconds (eval_interval + notification pipeline). Measured by: inject a known
   metric value that triggers a test alert, measure time to notification receipt.
   Run every 5 minutes.

4. **Data completeness**: < 0.1% sample loss end-to-end. Measured by: canary metrics
   with known values. Query count of canary samples per hour and compare to expected
   count (360 for 10s interval). Missing samples = data loss.

5. **Data correctness**: 100% of query results must be numerically accurate (within
   floating-point tolerance). Measured by: inject known values, query with known
   functions, verify results against precomputed expected values.

SLO violation response:
- Burn rate alerts: If 1-hour burn rate exceeds 14.4x (exhausts monthly budget in 5 days),
  page immediately. If 6-hour burn rate exceeds 6x, create a P1 ticket.

---

## Summary

The metrics and monitoring system design balances several competing concerns:

| Concern                | Solution                                            |
|------------------------|-----------------------------------------------------|
| Write throughput       | Kafka buffering + horizontally-scaled ingesters     |
| Storage efficiency     | Gorilla compression + tiered storage + downsampling |
| Query performance      | In-memory head block + chunk cache + result cache   |
| Multi-dimensional query| Inverted index on labels + PromQL                   |
| Alert reliability      | Dual evaluators + HA AlertManager + multi-channel   |
| Multi-tenancy          | Per-tenant limits + data isolation + fair scheduling |
| Long-term retention    | Object storage + automatic downsampling             |
| Operational simplicity | Self-monitoring + auto-scaling + graceful degradation|

The architecture follows the pattern established by systems like Cortex/Mimir (Grafana),
Thanos, and VictoriaMetrics: use Prometheus TSDB as the embedded storage engine, add a
distributed layer for horizontal scaling, Kafka for ingestion buffering, and object
storage for durable long-term retention. This design handles 10M+ data points per
second with sub-second query latency and 99.99% availability.
