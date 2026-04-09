# Design a Notification System
**Difficulty:** Medium-Hard | **Companies:** Amazon, Google, Meta, Apple, Netflix, Uber

> For the low-level class design, see [LLD: Notification System](/lld/12-notification-system)

---

## Table of Contents
1. [Problem Statement and Scope](#1-problem-statement-and-scope)
2. [Functional Requirements](#2-functional-requirements)
3. [Non-Functional Requirements](#3-non-functional-requirements)
4. [Back-of-Envelope Estimation](#4-back-of-envelope-estimation)
5. [API Design](#5-api-design)
6. [Data Model and Database Selection](#6-data-model-and-database-selection)
7. [High-Level Architecture](#7-high-level-architecture)
8. [Deep Dive: Core Components](#8-deep-dive-core-components)
9. [Data Partitioning and Sharding](#9-data-partitioning-and-sharding)
10. [Caching Strategy](#10-caching-strategy)
11. [Replication and Consistency](#11-replication-and-consistency)
12. [Fault Tolerance and Failure Handling](#12-fault-tolerance-and-failure-handling)
13. [Scalability](#13-scalability)
14. [Monitoring and Observability](#14-monitoring-and-observability)
15. [Trade-offs and Design Decisions](#15-trade-offs-and-design-decisions)
16. [Interview Deep-Dive Questions](#16-interview-deep-dive-questions)

---

## 1. Problem Statement and Scope

Design a scalable, highly available notification system that delivers notifications
across multiple channels -- push notifications (iOS/Android), SMS, email, and in-app --
with support for prioritization, rate limiting, user preference management, template-based
rendering, deduplication, and guaranteed delivery.

The system must handle billions of notifications per day across a global user base,
integrating with third-party providers (APNs, FCM, Twilio, SES) while providing
consistent delivery tracking and analytics.

### Scope Boundaries

```
┌─────────────────────────────────────────────────────────────────────┐
│                     SCOPE DEFINITION                                │
├────────────────────────────┬────────────────────────────────────────┤
│       IN SCOPE             │         OUT OF SCOPE                   │
├────────────────────────────┼────────────────────────────────────────┤
│ Push notifications (APNs,  │ Content moderation / filtering        │
│   FCM)                     │                                        │
│ Email delivery (SES,       │ Marketing campaign management UI      │
│   SendGrid)                │                                        │
│ SMS delivery (Twilio, SNS) │ Email/SMS content authoring tools     │
│ In-app notifications       │ User authentication / authorization   │
│ User preferences           │ Billing for SMS/email usage           │
│ Template management        │ A/B testing platform (referenced      │
│ Delivery tracking          │   but not built)                       │
│ Priority-based routing     │ Rich media processing (image          │
│ Rate limiting              │   resize, video transcode)             │
│ Scheduled notifications    │ Regulatory compliance engine          │
│ Batch/bulk sending         │   (GDPR/CAN-SPAM details)             │
│ Deduplication              │                                        │
│ Retry and DLQ handling     │                                        │
└────────────────────────────┴────────────────────────────────────────┘
```

---

## 2. Functional Requirements

### Core Features

| # | Requirement | Description |
|---|-------------|-------------|
| F1 | **Multi-channel delivery** | Push (iOS/Android), SMS, Email, In-App |
| F2 | **User preferences** | Opt-in/out per channel, quiet hours, frequency caps |
| F3 | **Template management** | Parameterized templates with personalization |
| F4 | **Delivery tracking** | Status: created, queued, sent, delivered, read, clicked |
| F5 | **Priority levels** | Urgent (P0), High (P1), Normal (P2), Low (P3) |
| F6 | **Rate limiting** | Per-user, per-channel, per-notification-type limits |
| F7 | **Batch notifications** | Bulk send to segments (millions of users) |
| F8 | **Scheduled delivery** | Send at a future time, timezone-aware |
| F9 | **Digest/aggregation** | Group related notifications into a single digest |
| F10 | **Deduplication** | Prevent duplicate notifications within a time window |

### Notification Lifecycle

```
┌──────────────────────────────────────────────────────────────────────────┐
│                    NOTIFICATION LIFECYCLE                                 │
├──────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  ┌─────────┐   ┌────────┐   ┌────────┐   ┌──────┐   ┌───────────┐      │
│  │ CREATED │──►│ QUEUED │──►│  SENT  │──►│ DLVD │──►│READ/CLICK │      │
│  └─────────┘   └────────┘   └────────┘   └──────┘   └───────────┘      │
│       │             │            │            │                           │
│       │             │            │            └──► Delivery confirmed     │
│       │             │            │                  by provider           │
│       │             │            └──► Handed off to                       │
│       │             │                 APNs/FCM/SES/Twilio                 │
│       │             └──► Passed validation,                               │
│       │                  preferences, rate limits                         │
│       └──► Notification received                                         │
│            via API                                                        │
│                                                                          │
│  FAILURE STATES:                                                         │
│  ┌─────────────┐   ┌──────────┐   ┌──────────┐                          │
│  │  RATE_      │   │ FILTERED │   │  FAILED  │                          │
│  │  LIMITED    │   │ (prefs)  │   │ (→ DLQ)  │                          │
│  └─────────────┘   └──────────┘   └──────────┘                          │
│                                                                          │
└──────────────────────────────────────────────────────────────────────────┘
```

### Channel-Specific Features

```
┌──────────────────────────────────────────────────────────────────────────┐
│                    CHANNEL CAPABILITIES                                   │
├───────────┬────────────┬────────────┬───────────┬────────────────────────┤
│  Feature  │   Push     │   Email    │   SMS     │      In-App            │
├───────────┼────────────┼────────────┼───────────┼────────────────────────┤
│ Rich text │  Limited   │    Yes     │    No     │       Yes              │
│ Images    │  Small     │    Yes     │    No     │       Yes              │
│ Actions   │  2-3 btns  │   Links   │  Reply    │    Buttons/Links       │
│ Delivery  │  Provider  │  Bounce/  │  Carrier  │    Instant             │
│  confirm  │  callback  │  receipt  │  receipt  │    (WebSocket)         │
│ Cost      │  Free      │  ~$0.001  │ ~$0.01    │       Free             │
│ Latency   │  <1s       │  1-30s    │  1-5s     │       <100ms           │
│ Read rate │  ~60%      │  ~20%     │  ~95%     │       ~40%             │
│ Offline   │  Stored    │  Inbox    │  Carrier  │    Stored server-side  │
│  delivery │  by APNs   │           │  retry    │                        │
└───────────┴────────────┴────────────┴───────────┴────────────────────────┘
```

---

## 3. Non-Functional Requirements

| Requirement | Target | Rationale |
|-------------|--------|-----------|
| **Delivery latency** | <1s urgent, <5s high, <30s normal | User expectation by priority |
| **Availability** | 99.99% (52 min downtime/year) | Notifications are business-critical |
| **Throughput** | 1B notifications/day, 50K/sec peak | Scale for large user base |
| **Delivery guarantee** | At-least-once | Missed notification > duplicate |
| **Deduplication** | Within 5-minute window | Prevent spam from retries |
| **Data retention** | 90 days hot, 1 year cold | Analytics and audit trail |
| **Global distribution** | Multi-region deployment | Low latency worldwide |
| **Provider failover** | <30s switchover | No single provider dependency |

### Latency Budget Breakdown

```
┌─────────────────────────────────────────────────────────────────────────┐
│              LATENCY BUDGET (Urgent P0 Notification)                    │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  API Gateway          ███  50ms                                         │
│  Validation           ██   30ms                                         │
│  Preference check     ██   20ms  (Redis cached)                         │
│  Rate limit check     █    10ms  (Redis)                                │
│  Template render      ██   30ms                                         │
│  Kafka produce        ███  50ms                                         │
│  Kafka consume        ██   30ms                                         │
│  Provider API call    ████████████████████████████  500ms (APNs/FCM)    │
│  ─────────────────────────────────────────────                          │
│  Total:               ███████████████████████████████████ ~720ms        │
│                                                                         │
│  NOTE: Provider API call dominates. We cannot control APNs/FCM          │
│  latency. Our internal processing target: <250ms.                       │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 4. Back-of-Envelope Estimation

### Traffic Estimates

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    TRAFFIC ESTIMATION                                    │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  Total notifications:     1,000,000,000 / day                           │
│  Average rate:            1B / 86400 ≈ 11,574 / sec                     │
│  Peak rate (4x avg):      ~50,000 / sec                                 │
│  Burst rate (10x avg):    ~120,000 / sec (flash sales, breaking news)   │
│                                                                         │
│  CHANNEL BREAKDOWN:                                                     │
│  ┌──────────────────────────────────────────────────────────┐           │
│  │  Push (40%):     400M/day  =  4,630/sec avg             │           │
│  │  Email (30%):    300M/day  =  3,472/sec avg             │           │
│  │  In-App (20%):   200M/day  =  2,315/sec avg             │           │
│  │  SMS (10%):      100M/day  =  1,157/sec avg             │           │
│  └──────────────────────────────────────────────────────────┘           │
│                                                                         │
│  PRIORITY BREAKDOWN:                                                    │
│  ┌──────────────────────────────────────────────────────────┐           │
│  │  Urgent (P0):   1%   =  10M/day   =  ~115/sec           │           │
│  │  High (P1):     9%   =  90M/day   =  ~1,040/sec         │           │
│  │  Normal (P2):   70%  =  700M/day  =  ~8,100/sec         │           │
│  │  Low (P3):      20%  =  200M/day  =  ~2,315/sec         │           │
│  └──────────────────────────────────────────────────────────┘           │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

### Storage Estimates

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    STORAGE ESTIMATION                                    │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  NOTIFICATION RECORD:                                                   │
│  ┌──────────────────────────────────────────┐                           │
│  │  notification_id:    16 bytes (UUID)     │                           │
│  │  user_id:            16 bytes            │                           │
│  │  channel:             4 bytes (enum)     │                           │
│  │  priority:            4 bytes            │                           │
│  │  template_id:        16 bytes            │                           │
│  │  rendered_content:  200 bytes (avg)      │                           │
│  │  metadata/payload:  150 bytes            │                           │
│  │  status:              4 bytes            │                           │
│  │  timestamps:         40 bytes (5x8)      │                           │
│  │  provider_response:  50 bytes            │                           │
│  │  ─────────────────────────────           │                           │
│  │  Total per record: ~500 bytes            │                           │
│  └──────────────────────────────────────────┘                           │
│                                                                         │
│  DAILY STORAGE:                                                         │
│  Notifications:  1B * 500B  = 500 GB/day                                │
│  Delivery logs:  1B * 200B  = 200 GB/day  (status updates)             │
│  Analytics:      1B * 100B  = 100 GB/day                                │
│  ──────────────────────────────                                         │
│  Total daily:                 ~800 GB/day                                │
│  90-day hot storage:          ~72 TB                                     │
│  1-year cold storage:         ~292 TB                                    │
│                                                                         │
│  ANCILLARY STORAGE:                                                     │
│  User preferences:  500M users * 1KB   = 500 GB (MySQL)                 │
│  Device tokens:     500M users * 200B  = 100 GB (Redis + MySQL)         │
│  Templates:         100K * 5KB         = 500 MB (MySQL)                  │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

### Bandwidth Estimates

```
  Ingress (API requests):   50K/sec * 1KB avg payload  = 50 MB/sec
  Egress (to providers):    50K/sec * 2KB avg payload  = 100 MB/sec
  Internal (Kafka):         50K/sec * 1.5KB            = 75 MB/sec
```

---

## 5. API Design

### 5.1 Send Notification

```
POST /v1/notifications/send
Authorization: Bearer <api-key>
X-Idempotency-Key: <uuid>
Content-Type: application/json

{
  "recipients": [
    {
      "user_id": "user_12345",
      "channels": ["push", "email"],      // optional override
      "data": {                            // per-recipient personalization
        "first_name": "Ajay",
        "order_id": "ORD-98765"
      }
    }
  ],
  "template_id": "order_shipped_v2",
  "channel": "push",                       // default channel
  "priority": "high",                      // urgent | high | normal | low
  "category": "transactional",             // transactional | marketing | system
  "schedule_time": "2026-04-10T09:00:00Z", // optional, null = immediate
  "ttl_seconds": 86400,                    // notification expiry
  "collapse_key": "order_update_98765",    // replaces prior with same key
  "data": {                                // global template data
    "company_name": "Acme Corp"
  },
  "options": {
    "respect_quiet_hours": true,
    "allow_digest": true,
    "track_clicks": true
  }
}

Response 202 Accepted:
{
  "request_id": "req_abc123",
  "notifications": [
    {
      "notification_id": "notif_xyz789",
      "user_id": "user_12345",
      "status": "queued",
      "estimated_delivery": "2026-04-10T09:00:00Z"
    }
  ]
}
```

### 5.2 Get In-App Notifications

```
GET /v1/notifications/users/{user_id}?status=unread&limit=20&cursor=abc123
Authorization: Bearer <token>

Response 200:
{
  "notifications": [
    {
      "notification_id": "notif_xyz789",
      "title": "Your order has shipped!",
      "body": "Order ORD-98765 is on its way...",
      "type": "order_update",
      "priority": "high",
      "created_at": "2026-04-09T14:30:00Z",
      "read_at": null,
      "action_url": "/orders/ORD-98765",
      "image_url": "https://cdn.example.com/icons/shipping.png",
      "metadata": { "order_id": "ORD-98765" }
    }
  ],
  "cursor": "def456",
  "unread_count": 12,
  "has_more": true
}
```

### 5.3 Update User Preferences

```
PUT /v1/users/{user_id}/preferences
Authorization: Bearer <token>

{
  "channels": {
    "push": {
      "enabled": true,
      "categories": {
        "transactional": true,
        "marketing": false,
        "social": true
      }
    },
    "email": {
      "enabled": true,
      "categories": {
        "transactional": true,
        "marketing": true,       // subscribed to marketing emails
        "social": false
      },
      "digest": {
        "enabled": true,
        "frequency": "daily",    // daily | weekly
        "time": "09:00",
        "timezone": "America/New_York"
      }
    },
    "sms": { "enabled": false },
    "in_app": { "enabled": true }
  },
  "quiet_hours": {
    "enabled": true,
    "start": "22:00",
    "end": "08:00",
    "timezone": "America/New_York",
    "override_for_urgent": true    // P0 bypasses quiet hours
  },
  "frequency_cap": {
    "max_per_day": 50,
    "max_push_per_hour": 5
  }
}
```

### 5.4 Template Management

```
POST /v1/templates
Authorization: Bearer <admin-api-key>

{
  "template_id": "order_shipped_v2",
  "name": "Order Shipped Notification",
  "channels": {
    "push": {
      "title": "Your order is on its way! {{emoji}}",
      "body": "Hi {{first_name}}, order {{order_id}} has shipped.",
      "action": "OPEN_ORDER",
      "image": "{{product_image_url}}"
    },
    "email": {
      "subject": "Order {{order_id}} has shipped",
      "html_template": "<html>...</html>",
      "text_template": "Hi {{first_name}}, your order..."
    },
    "sms": {
      "body": "Hi {{first_name}}, order {{order_id}} shipped. Track: {{tracking_url}}"
    },
    "in_app": {
      "title": "Order Shipped",
      "body": "Your order {{order_id}} is on its way!",
      "icon": "shipping",
      "action_url": "/orders/{{order_id}}"
    }
  },
  "category": "transactional",
  "variables": ["first_name", "order_id", "tracking_url", "product_image_url"],
  "version": 2,
  "active": true
}
```

### 5.5 Delivery Status Webhook

```
POST /v1/webhooks/delivery-status   (registered callback URL)

{
  "notification_id": "notif_xyz789",
  "user_id": "user_12345",
  "channel": "push",
  "status": "delivered",           // delivered | bounced | failed | clicked
  "provider": "fcm",
  "provider_message_id": "fcm_msg_abc",
  "timestamp": "2026-04-09T14:30:05Z",
  "metadata": {
    "device_type": "android",
    "device_token": "abc...xyz"
  }
}
```

---

## 6. Data Model and Database Selection

### Database Selection Rationale

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    DATABASE SELECTION                                    │
├─────────────────────┬───────────────────────────────────────────────────┤
│     Data Type       │     Database          │ Rationale                 │
├─────────────────────┼───────────────────────┼───────────────────────────┤
│ Notification        │ Cassandra             │ Write-heavy, time-series, │
│ records             │                       │ horizontal scaling,       │
│                     │                       │ TTL support               │
├─────────────────────┼───────────────────────┼───────────────────────────┤
│ User preferences    │ MySQL (Aurora)        │ Read-heavy, relational,   │
│                     │                       │ strong consistency for    │
│                     │                       │ preference updates        │
├─────────────────────┼───────────────────────┼───────────────────────────┤
│ Templates           │ MySQL (Aurora)        │ Structured, versioned,    │
│                     │                       │ low volume, needs ACID    │
├─────────────────────┼───────────────────────┼───────────────────────────┤
│ Delivery status     │ Cassandra             │ Append-only, high write   │
│ logs                │                       │ throughput, time-based    │
│                     │                       │ partitioning              │
├─────────────────────┼───────────────────────┼───────────────────────────┤
│ In-app              │ Redis (hot) +         │ Fast reads for unread     │
│ notifications       │ Cassandra (cold)      │ count; Cassandra for      │
│                     │                       │ historical feed           │
├─────────────────────┼───────────────────────┼───────────────────────────┤
│ Device tokens       │ Redis (cache) +       │ Frequent lookups, needs   │
│                     │ MySQL (source)        │ persistence               │
├─────────────────────┼───────────────────────┼───────────────────────────┤
│ Rate limit          │ Redis                 │ Atomic counters, TTL,     │
│ counters            │                       │ in-memory speed           │
├─────────────────────┼───────────────────────┼───────────────────────────┤
│ Dedup keys          │ Redis                 │ Fast lookup, auto-expire  │
│                     │                       │ with TTL                  │
├─────────────────────┼───────────────────────┼───────────────────────────┤
│ Analytics /         │ ClickHouse or         │ Columnar, fast aggregates │
│ Reporting           │ BigQuery              │ on billions of rows       │
└─────────────────────┴───────────────────────┴───────────────────────────┘
```

### Schema Design

#### Cassandra: Notification Records

```sql
CREATE TABLE notifications (
    user_id         UUID,
    created_date    DATE,             -- partition by day for TTL cleanup
    notification_id TIMEUUID,         -- clustering, sorted by time
    channel         TEXT,             -- push | email | sms | in_app
    priority        INT,
    template_id     TEXT,
    title           TEXT,
    body            TEXT,
    status          TEXT,             -- created | queued | sent | delivered | read
    category        TEXT,
    metadata        MAP<TEXT, TEXT>,
    created_at      TIMESTAMP,
    sent_at         TIMESTAMP,
    delivered_at    TIMESTAMP,
    read_at         TIMESTAMP,
    PRIMARY KEY ((user_id, created_date), notification_id)
) WITH CLUSTERING ORDER BY (notification_id DESC)
  AND default_time_to_live = 7776000;   -- 90 days
```

#### Cassandra: Delivery Logs

```sql
CREATE TABLE delivery_logs (
    notification_id TIMEUUID,
    attempt_num     INT,
    channel         TEXT,
    provider        TEXT,             -- apns | fcm | ses | twilio
    status          TEXT,             -- sent | delivered | bounced | failed
    provider_msg_id TEXT,
    error_code      TEXT,
    error_message   TEXT,
    latency_ms      INT,
    timestamp       TIMESTAMP,
    PRIMARY KEY ((notification_id), attempt_num)
) WITH default_time_to_live = 7776000;
```

#### MySQL: User Preferences

```sql
CREATE TABLE user_preferences (
    user_id             VARCHAR(36) PRIMARY KEY,
    push_enabled        BOOLEAN DEFAULT TRUE,
    email_enabled       BOOLEAN DEFAULT TRUE,
    sms_enabled         BOOLEAN DEFAULT FALSE,
    in_app_enabled      BOOLEAN DEFAULT TRUE,
    quiet_hours_enabled BOOLEAN DEFAULT FALSE,
    quiet_hours_start   TIME,
    quiet_hours_end     TIME,
    timezone            VARCHAR(50) DEFAULT 'UTC',
    max_per_day         INT DEFAULT 100,
    max_push_per_hour   INT DEFAULT 10,
    digest_enabled      BOOLEAN DEFAULT FALSE,
    digest_frequency    ENUM('daily', 'weekly') DEFAULT 'daily',
    digest_time         TIME DEFAULT '09:00:00',
    updated_at          TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_updated_at (updated_at)
);

CREATE TABLE user_channel_category_preferences (
    user_id     VARCHAR(36),
    channel     ENUM('push', 'email', 'sms', 'in_app'),
    category    VARCHAR(50),         -- transactional, marketing, social, system
    enabled     BOOLEAN DEFAULT TRUE,
    PRIMARY KEY (user_id, channel, category),
    FOREIGN KEY (user_id) REFERENCES user_preferences(user_id)
);
```

#### MySQL: Device Tokens

```sql
CREATE TABLE device_tokens (
    device_token_id  VARCHAR(36) PRIMARY KEY,
    user_id          VARCHAR(36) NOT NULL,
    platform         ENUM('ios', 'android', 'web') NOT NULL,
    token            VARCHAR(512) NOT NULL,
    app_version      VARCHAR(20),
    is_active        BOOLEAN DEFAULT TRUE,
    created_at       TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_used_at     TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_user_id (user_id),
    UNIQUE INDEX idx_token (token)
);
```

#### MySQL: Templates

```sql
CREATE TABLE notification_templates (
    template_id     VARCHAR(100),
    version         INT,
    name            VARCHAR(255),
    category        VARCHAR(50),
    push_title      TEXT,
    push_body       TEXT,
    email_subject   TEXT,
    email_html      MEDIUMTEXT,
    email_text      TEXT,
    sms_body        TEXT,
    in_app_title    TEXT,
    in_app_body     TEXT,
    in_app_icon     VARCHAR(100),
    variables       JSON,              -- list of required variables
    is_active       BOOLEAN DEFAULT TRUE,
    created_by      VARCHAR(36),
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (template_id, version)
);
```

#### Redis: In-App Notification Feed

```
Key:    in_app:{user_id}             (Sorted Set)
Score:  timestamp (epoch ms)
Value:  notification_id

Key:    in_app:unread:{user_id}      (Counter)
Value:  integer count

Key:    in_app:detail:{notif_id}     (Hash)
Fields: title, body, type, action_url, image_url, read, created_at

TTL:    30 days
```

---

## 7. High-Level Architecture

### Overall System Architecture

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                         NOTIFICATION SYSTEM ARCHITECTURE                        │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                 │
│  EVENT SOURCES                                                                  │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐              │
│  │ Order    │ │ Payment  │ │ Social   │ │ Marketing│ │ System   │              │
│  │ Service  │ │ Service  │ │ Service  │ │ Platform │ │ Alerts   │              │
│  └────┬─────┘ └────┬─────┘ └────┬─────┘ └────┬─────┘ └────┬─────┘              │
│       │             │            │             │            │                    │
│       └──────┬──────┴─────┬──────┴──────┬──────┘            │                    │
│              │            │             │                   │                    │
│              ▼            ▼             ▼                   ▼                    │
│  ┌───────────────────────────────────────────────────────────────────┐           │
│  │                      API GATEWAY                                  │           │
│  │              (Auth, Throttling, Routing)                          │           │
│  └──────────────────────────┬────────────────────────────────────────┘           │
│                              │                                                   │
│                              ▼                                                   │
│  ┌───────────────────────────────────────────────────────────────────┐           │
│  │                   NOTIFICATION SERVICE                            │           │
│  │  ┌─────────────┐ ┌──────────────┐ ┌───────────────┐              │           │
│  │  │  Validator   │ │  Preference  │ │ Rate Limiter  │              │           │
│  │  │              │ │  Checker     │ │               │              │           │
│  │  └──────┬───────┘ └──────┬───────┘ └──────┬────────┘              │           │
│  │         │                │                │                       │           │
│  │  ┌──────┴────────────────┴────────────────┴───────┐               │           │
│  │  │            Template Engine                      │               │           │
│  │  │        (render + personalize)                   │               │           │
│  │  └────────────────────┬───────────────────────────┘               │           │
│  └───────────────────────┼───────────────────────────────────────────┘           │
│                          │                                                       │
│                          ▼                                                       │
│  ┌───────────────────────────────────────────────────────────────────┐           │
│  │                    KAFKA CLUSTER                                   │           │
│  │  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐             │           │
│  │  │ P0-Urgent│ │ P1-High  │ │ P2-Normal│ │ P3-Low   │             │           │
│  │  │  Topic   │ │  Topic   │ │  Topic   │ │  Topic   │             │           │
│  │  └────┬─────┘ └────┬─────┘ └────┬─────┘ └────┬─────┘             │           │
│  └───────┼─────────────┼────────────┼────────────┼───────────────────┘           │
│          │             │            │            │                                │
│          ▼             ▼            ▼            ▼                                │
│  ┌───────────────────────────────────────────────────────────────────┐           │
│  │                   CHANNEL WORKERS                                 │           │
│  │                                                                   │           │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐            │           │
│  │  │ Push Worker   │  │ Email Worker │  │ SMS Worker   │            │           │
│  │  │ (APNs + FCM) │  │ (SES/Grid)   │  │ (Twilio/SNS) │            │           │
│  │  └──────┬────────┘  └──────┬───────┘  └──────┬───────┘            │           │
│  │         │                  │                  │                    │           │
│  │  ┌──────┴──────────────────┴──────────────────┴──────────┐        │           │
│  │  │              In-App Worker (WebSocket/SSE)             │        │           │
│  │  └───────────────────────────────────────────────────────┘        │           │
│  └───────────────────────────────────────────────────────────────────┘           │
│          │                  │                  │            │                     │
│          ▼                  ▼                  ▼            ▼                     │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐         │
│  │    APNs      │  │  Amazon SES  │  │   Twilio     │  │  WebSocket   │         │
│  │    FCM       │  │  SendGrid    │  │   AWS SNS    │  │  Server      │         │
│  └──────────────┘  └──────────────┘  └──────────────┘  └──────────────┘         │
│                                                                                  │
│  ┌───────────────────────────────────────────────────────────────────┐           │
│  │                   SUPPORTING SERVICES                             │           │
│  │  ┌─────────────┐ ┌─────────────┐ ┌───────────────┐ ┌──────────┐  │           │
│  │  │ Analytics   │ │  Scheduler  │ │ Delivery      │ │  DLQ     │  │           │
│  │  │ Service     │ │  Service    │ │ Tracker       │ │ Processor│  │           │
│  │  └─────────────┘ └─────────────┘ └───────────────┘ └──────────┘  │           │
│  └───────────────────────────────────────────────────────────────────┘           │
│                                                                                  │
│  ┌───────────────────────────────────────────────────────────────────┐           │
│  │                   DATA STORES                                     │           │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────────────┐  │           │
│  │  │Cassandra │  │  MySQL   │  │  Redis   │  │  ClickHouse     │  │           │
│  │  │(notifs,  │  │(prefs,   │  │(cache,   │  │  (analytics)    │  │           │
│  │  │ logs)    │  │ tokens,  │  │ rate     │  │                  │  │           │
│  │  │          │  │ templ.)  │  │ limits)  │  │                  │  │           │
│  │  └──────────┘  └──────────┘  └──────────┘  └──────────────────┘  │           │
│  └───────────────────────────────────────────────────────────────────┘           │
│                                                                                  │
└─────────────────────────────────────────────────────────────────────────────────┘
```

### 7.1 Component Breakdown

#### Notification Service (Core Orchestrator)

The central service that receives notification requests and orchestrates the processing
pipeline. It is stateless and horizontally scalable.

```
┌─────────────────────────────────────────────────────────────────────────┐
│                NOTIFICATION SERVICE INTERNALS                           │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  Incoming Request                                                       │
│       │                                                                 │
│       ▼                                                                 │
│  ┌─────────────────┐     ┌──────────────────────────────┐               │
│  │   1. VALIDATE   │────►│ Schema validation, auth,     │               │
│  │                 │     │ idempotency key check        │               │
│  └────────┬────────┘     └──────────────────────────────┘               │
│           │                                                              │
│           ▼                                                              │
│  ┌─────────────────┐     ┌──────────────────────────────┐               │
│  │  2. DEDUP CHECK │────►│ Redis: check idempotency key │               │
│  │                 │     │ within 5-min window          │               │
│  └────────┬────────┘     └──────────────────────────────┘               │
│           │                                                              │
│           ▼                                                              │
│  ┌─────────────────┐     ┌──────────────────────────────┐               │
│  │  3. PREFERENCE  │────►│ Redis cache → MySQL fallback │               │
│  │     CHECK       │     │ Channel enabled? Category    │               │
│  │                 │     │ allowed? Quiet hours?        │               │
│  └────────┬────────┘     └──────────────────────────────┘               │
│           │                                                              │
│           ▼                                                              │
│  ┌─────────────────┐     ┌──────────────────────────────┐               │
│  │  4. RATE LIMIT  │────►│ Redis: sliding window check  │               │
│  │     CHECK       │     │ per user/channel/type        │               │
│  └────────┬────────┘     └──────────────────────────────┘               │
│           │                                                              │
│           ▼                                                              │
│  ┌─────────────────┐     ┌──────────────────────────────┐               │
│  │  5. CHANNEL     │────►│ Resolve which channels       │               │
│  │     SELECTION   │     │ based on prefs + fallback    │               │
│  └────────┬────────┘     └──────────────────────────────┘               │
│           │                                                              │
│           ▼                                                              │
│  ┌─────────────────┐     ┌──────────────────────────────┐               │
│  │  6. TEMPLATE    │────►│ Fetch template, render with  │               │
│  │     RENDER      │     │ Mustache/Handlebars engine   │               │
│  └────────┬────────┘     └──────────────────────────────┘               │
│           │                                                              │
│           ▼                                                              │
│  ┌─────────────────┐     ┌──────────────────────────────┐               │
│  │  7. ENQUEUE     │────►│ Kafka: produce to priority   │               │
│  │                 │     │ topic, partitioned by        │               │
│  │                 │     │ user_id % partition_count    │               │
│  └────────┬────────┘     └──────────────────────────────┘               │
│           │                                                              │
│           ▼                                                              │
│  ┌─────────────────┐     ┌──────────────────────────────┐               │
│  │  8. PERSIST     │────►│ Cassandra: write notification│               │
│  │                 │     │ record with status=queued    │               │
│  └─────────────────┘     └──────────────────────────────┘               │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

#### Channel Workers

Each channel has its own fleet of worker instances that consume from Kafka topics
and deliver to the respective third-party provider.

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    CHANNEL WORKER ARCHITECTURE                           │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  KAFKA TOPIC (e.g., notif-push-p0)                                     │
│  ┌────┬────┬────┬────┬────┬────┬────┬────┐                              │
│  │ P0 │ P1 │ P2 │ P3 │ P4 │ P5 │ P6 │ P7 │  (8 partitions)            │
│  └──┬─┴──┬─┴──┬─┴──┬─┴──┬─┴──┬─┴──┬─┴──┬─┘                            │
│     │    │    │    │    │    │    │    │                                  │
│     ▼    ▼    ▼    ▼    ▼    ▼    ▼    ▼                                  │
│  ┌────────────────────────────────────────────┐                         │
│  │         PUSH WORKER CONSUMER GROUP          │                         │
│  │                                             │                         │
│  │  ┌──────────┐ ┌──────────┐ ┌──────────┐    │                         │
│  │  │Worker #1 │ │Worker #2 │ │Worker #3 │    │                         │
│  │  │(P0,P1,P2)│ │(P3,P4,P5)│ │(P6,P7)  │    │                         │
│  │  └────┬─────┘ └────┬─────┘ └────┬─────┘    │                         │
│  └───────┼─────────────┼────────────┼──────────┘                         │
│          │             │            │                                     │
│          ▼             ▼            ▼                                     │
│  ┌──────────────────────────────────────────────┐                        │
│  │           PROVIDER ROUTER                     │                        │
│  │                                               │                        │
│  │   iOS device?  ──► APNs (HTTP/2 persistent)  │                        │
│  │   Android?     ──► FCM  (HTTP/2 batch API)   │                        │
│  │   Web?         ──► Web Push (VAPID)          │                        │
│  └──────────────────────────────────────────────┘                        │
│          │                                                               │
│          ▼                                                               │
│  ┌──────────────────────────────────────────────┐                        │
│  │        DELIVERY CALLBACK HANDLER              │                        │
│  │                                               │                        │
│  │   Success    ──► Update status = delivered    │                        │
│  │   Invalid    ──► Deactivate device token      │                        │
│  │   Throttled  ──► Re-enqueue with backoff     │                        │
│  │   Failed     ──► Retry (max 3) then DLQ      │                        │
│  └──────────────────────────────────────────────┘                        │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

#### Scheduler Service

Handles deferred and timezone-aware notification delivery.

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    SCHEDULER SERVICE                                    │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  ┌────────────────────────────────────────────────────────┐             │
│  │  Scheduled Notification Store (MySQL / Redis ZSET)     │             │
│  │                                                        │             │
│  │  Key: scheduled:notifications                          │             │
│  │  Score: delivery_timestamp (epoch ms)                  │             │
│  │  Value: notification_id                                │             │
│  │                                                        │             │
│  │  Example entries:                                      │             │
│  │  ┌────────────────────┬──────────────────────────┐     │             │
│  │  │ Score (epoch ms)   │ notification_id          │     │             │
│  │  ├────────────────────┼──────────────────────────┤     │             │
│  │  │ 1744300800000      │ notif_abc_001            │     │             │
│  │  │ 1744300860000      │ notif_abc_002            │     │             │
│  │  │ 1744301400000      │ notif_abc_003            │     │             │
│  │  └────────────────────┴──────────────────────────┘     │             │
│  └────────────────────────────────────────────────────────┘             │
│                                                                         │
│  SCHEDULER LOOP (runs every 1 second):                                 │
│                                                                         │
│  1. ZRANGEBYSCORE scheduled:notifications 0 <now> LIMIT 0 1000         │
│  2. For each notification_id:                                           │
│     a. Fetch full notification from Cassandra                          │
│     b. Produce to appropriate Kafka priority topic                     │
│     c. ZREM scheduled:notifications notification_id                    │
│  3. Use distributed lock (Redlock) to prevent                          │
│     multiple scheduler instances processing same batch                 │
│                                                                         │
│  TIMEZONE HANDLING:                                                     │
│  ─────────────────                                                     │
│  schedule_time=09:00, user_tz=America/New_York                         │
│  → Convert to UTC: 13:00 UTC                                          │
│  → Store as epoch in ZSET                                              │
│  → Scheduler polls and fires when now >= epoch                         │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 8. Deep Dive: Core Components

### 8.1 Notification Processing Pipeline

The end-to-end flow from event source to user device:

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                  END-TO-END NOTIFICATION PIPELINE                                │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                  │
│  ┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐   │
│  │  EVENT   │    │ VALIDATE │    │ FILTER   │    │  RENDER  │    │ ENQUEUE  │   │
│  │  SOURCE  │───►│  & DEDUP │───►│ & CHECK  │───►│ TEMPLATE │───►│ (KAFKA)  │   │
│  └──────────┘    └──────────┘    └──────────┘    └──────────┘    └──────────┘   │
│                       │               │                               │          │
│                  Idempotency     Preferences                    Priority-based   │
│                  key check       Rate limits                    topic routing    │
│                  Schema valid.   Quiet hours                                     │
│                                                                       │          │
│                                                                       ▼          │
│  ┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐   │
│  │  USER    │    │ ANALYTICS│    │ DELIVERY │    │ PROVIDER │    │ CHANNEL  │   │
│  │  DEVICE  │◄───│ TRACKING │◄───│ CALLBACK │◄───│ CALL     │◄───│ WORKER   │   │
│  └──────────┘    └──────────┘    └──────────┘    └──────────┘    └──────────┘   │
│                                       │                               │          │
│                                  Update status                   Consume from   │
│                                  in Cassandra                    Kafka topic     │
│                                                                                  │
│  TIMING (Normal Priority):                                                       │
│  ────────────────────────                                                        │
│  Event → Validate:     ~30ms                                                     │
│  Validate → Filter:    ~50ms  (Redis lookups for prefs + rate limits)            │
│  Filter → Render:      ~30ms  (template + personalization)                       │
│  Render → Enqueue:     ~50ms  (Kafka produce ack)                                │
│  Enqueue → Worker:     ~30ms  (Kafka consumer lag)                               │
│  Worker → Provider:    ~500ms (APNs/FCM/SES call)                                │
│  Provider → Device:    variable (APNs internal routing)                           │
│  ─────────────────────────────                                                   │
│  Total internal:       ~190ms                                                    │
│  Total with provider:  ~690ms                                                    │
│                                                                                  │
└─────────────────────────────────────────────────────────────────────────────────┘
```

#### Pipeline Step Details

**Step 1: Validation and Deduplication**
- Verify API key and permissions
- Schema validation (required fields, valid channel, valid priority)
- Check idempotency key in Redis: `SETNX dedup:{idempotency_key} 1 EX 300`
- If key exists, return cached response (deduplicated)

**Step 2: Preference and Rate Limit Check**
- Fetch user preferences from Redis (cache hit ~95%) or MySQL (cache miss)
- Check if channel is enabled for user
- Check if notification category is enabled for user on this channel
- Check quiet hours: convert current time to user timezone, compare with quiet window
  - If in quiet hours and priority != P0, hold until quiet hours end
- Rate limit check: `INCR rate:{user_id}:{channel}:{window}` with TTL
  - Exceeds limit? Drop notification with status=RATE_LIMITED

**Step 3: Channel Selection and Template Rendering**
- If sender specified channels, intersect with user-enabled channels
- If no channels specified, use all user-enabled channels (fan-out)
- Fetch template from local cache (TTL 5 minutes) or MySQL
- Render template with user-specific data using Mustache/Handlebars engine
- Generate channel-specific payloads (different formats for push vs. email vs. SMS)

**Step 4: Kafka Enqueue**
- Select Kafka topic by priority: `notif-{channel}-p{priority}`
- Partition key: `user_id` (ensures ordering per user)
- Message includes: notification_id, rendered content, device tokens, metadata
- Async produce with acks=all for durability

### 8.2 Priority Queue and Ordering

#### Kafka Topic Design

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    KAFKA TOPIC TOPOLOGY                                  │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  PRIORITY TOPICS (per channel):                                        │
│                                                                         │
│  notif-push-p0-urgent   (4 partitions,  replication=3)                 │
│  notif-push-p1-high     (8 partitions,  replication=3)                 │
│  notif-push-p2-normal   (32 partitions, replication=3)                 │
│  notif-push-p3-low      (16 partitions, replication=3)                 │
│                                                                         │
│  notif-email-p0-urgent  (4 partitions,  replication=3)                 │
│  notif-email-p1-high    (8 partitions,  replication=3)                 │
│  notif-email-p2-normal  (32 partitions, replication=3)                 │
│  notif-email-p3-low     (16 partitions, replication=3)                 │
│                                                                         │
│  notif-sms-p0-urgent    (4 partitions,  replication=3)                 │
│  notif-sms-p1-high      (4 partitions,  replication=3)                 │
│  notif-sms-p2-normal    (16 partitions, replication=3)                 │
│  notif-sms-p3-low       (8 partitions,  replication=3)                 │
│                                                                         │
│  notif-inapp-p0-urgent  (4 partitions,  replication=3)                 │
│  notif-inapp-p2-normal  (16 partitions, replication=3)                 │
│                                                                         │
│  SPECIAL TOPICS:                                                       │
│  notif-dlq               (8 partitions)   Dead letter queue            │
│  notif-delivery-events   (16 partitions)  Delivery status updates      │
│  notif-analytics         (8 partitions)   Analytics events             │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

#### Consumer Group Allocation

```
┌─────────────────────────────────────────────────────────────────────────┐
│                CONSUMER GROUP ALLOCATION STRATEGY                       │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  PRIORITY      │ CONSUMERS │ POLL RATE  │ BATCH SIZE │ RATIONALE        │
│  ──────────────┼───────────┼───────────┼────────────┼──────────────     │
│  P0 (Urgent)   │  20       │ 50ms      │  10        │ Min latency      │
│  P1 (High)     │  40       │ 100ms     │  50        │ Fast, batched    │
│  P2 (Normal)   │  100      │ 500ms     │  200       │ Throughput       │
│  P3 (Low)      │  30       │ 1000ms    │  500       │ Cost-efficient   │
│                                                                         │
│  STARVATION PREVENTION:                                                │
│  ────────────────────────                                              │
│  Each consumer thread uses weighted fair queuing:                      │
│  - P0 gets 40% of processing capacity                                  │
│  - P1 gets 30%                                                         │
│  - P2 gets 20%                                                         │
│  - P3 gets 10%                                                         │
│                                                                         │
│  When P0 queue is empty, its capacity shifts to lower priorities.       │
│  This ensures P3 notifications still get processed even under load.    │
│                                                                         │
│  CONSUMER ORDERING GUARANTEE:                                          │
│  ──────────────────────────                                            │
│  Partition key = user_id                                               │
│  → All notifications for a user land on same partition                 │
│  → Single consumer processes them in order                             │
│  → Prevents "order shipped" arriving before "order placed"            │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

### 8.3 Push Notification Delivery

#### APNs (Apple Push Notification Service)

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    APNs INTEGRATION                                     │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  Push Worker                                                            │
│  ┌──────────────────────────────────────────┐                           │
│  │  1. Get device token from cache/DB       │                           │
│  │  2. Build APNs payload:                  │                           │
│  │     {                                    │                           │
│  │       "aps": {                           │                           │
│  │         "alert": {                       │                           │
│  │           "title": "Order Shipped",      │                           │
│  │           "body": "Your order is...",    │                           │
│  │           "loc-key": "ORDER_SHIP"        │                           │
│  │         },                               │                           │
│  │         "badge": 5,                      │                           │
│  │         "sound": "default",              │                           │
│  │         "category": "ORDER_UPDATE",      │                           │
│  │         "mutable-content": 1             │                           │
│  │       },                                 │                           │
│  │       "order_id": "ORD-98765"            │                           │
│  │     }                                    │                           │
│  │                                          │                           │
│  │  3. Send via HTTP/2 persistent conn      │                           │
│  │     POST /3/device/{device_token}        │                           │
│  │     Headers:                             │                           │
│  │       authorization: bearer <jwt>        │                           │
│  │       apns-topic: com.app.bundle         │                           │
│  │       apns-priority: 10 (immediate)      │                           │
│  │       apns-collapse-id: order_98765      │                           │
│  │       apns-expiration: <epoch>           │                           │
│  └──────────────────────────────────────────┘                           │
│                                                                         │
│  APNs RESPONSE HANDLING:                                               │
│  ┌──────────────────────────────────────────────────────────┐           │
│  │  200 OK              → Status = sent, await feedback    │           │
│  │  400 BadRequest      → Log error, don't retry           │           │
│  │  403 Forbidden       → Certificate issue, alert ops     │           │
│  │  404 NotFound        → Invalid token, deactivate device │           │
│  │  410 Gone            → Token expired, remove from DB    │           │
│  │  429 TooManyRequests → Back off, retry after delay      │           │
│  │  500/503             → Retry with exponential backoff   │           │
│  └──────────────────────────────────────────────────────────┘           │
│                                                                         │
│  DEVICE TOKEN MANAGEMENT:                                              │
│  ┌──────────────────────────────────────────────────────────┐           │
│  │  • Tokens stored in MySQL, cached in Redis (TTL 24h)    │           │
│  │  • On 410 Gone: DELETE from device_tokens table         │           │
│  │  • On app uninstall: APNs feedback service reports      │           │
│  │    invalid tokens (polled every 15 min)                 │           │
│  │  • On token refresh: client sends new token via API,    │           │
│  │    old token invalidated                                │           │
│  │  • Multi-device: user may have 1-5 iOS devices,         │           │
│  │    send to all active tokens                            │           │
│  └──────────────────────────────────────────────────────────┘           │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

#### FCM (Firebase Cloud Messaging)

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    FCM INTEGRATION                                      │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  FCM PAYLOAD:                                                          │
│  {                                                                      │
│    "message": {                                                        │
│      "token": "device_token_here",                                     │
│      "notification": {                                                 │
│        "title": "Order Shipped",                                       │
│        "body": "Your order ORD-98765 is on its way!"                  │
│      },                                                                │
│      "data": {                                                         │
│        "order_id": "ORD-98765",                                        │
│        "click_action": "OPEN_ORDER"                                    │
│      },                                                                │
│      "android": {                                                      │
│        "priority": "high",                                             │
│        "notification": {                                               │
│          "channel_id": "order_updates",                                │
│          "icon": "ic_shipping"                                         │
│        },                                                              │
│        "ttl": "86400s"                                                 │
│      }                                                                 │
│    }                                                                   │
│  }                                                                      │
│                                                                         │
│  BATCH SENDING:                                                        │
│  ┌──────────────────────────────────────────────────────────┐           │
│  │  FCM supports batch API: up to 500 messages per request │           │
│  │  POST https://fcm.googleapis.com/batch                  │           │
│  │                                                          │           │
│  │  Worker batches messages for efficiency:                 │           │
│  │  • Accumulate up to 500 msgs or 100ms window            │           │
│  │  • Send as single HTTP request                          │           │
│  │  • Parse individual responses from batch                │           │
│  │  • Handle per-token errors independently                │           │
│  └──────────────────────────────────────────────────────────┘           │
│                                                                         │
│  FCM ERROR HANDLING:                                                   │
│  ┌──────────────────────────────────────────────────────────┐           │
│  │  UNREGISTERED       → Remove device token               │           │
│  │  INVALID_ARGUMENT   → Log, don't retry                  │           │
│  │  SENDER_ID_MISMATCH → Config error, alert ops           │           │
│  │  QUOTA_EXCEEDED     → Back off, retry in 60s            │           │
│  │  UNAVAILABLE        → Retry with exponential backoff    │           │
│  │  INTERNAL           → Retry with exponential backoff    │           │
│  └──────────────────────────────────────────────────────────┘           │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

#### APNs vs FCM Comparison

```
┌─────────────────────────────────────────────────────────────────────────┐
│                   APNs vs FCM COMPARISON                                │
├──────────────────┬─────────────────────┬────────────────────────────────┤
│     Feature      │       APNs          │          FCM                   │
├──────────────────┼─────────────────────┼────────────────────────────────┤
│ Protocol         │ HTTP/2              │ HTTP/1.1 or HTTP/2            │
│ Auth             │ JWT or Certificate  │ OAuth 2.0 (service account)   │
│ Max payload      │ 4 KB                │ 4 KB (data+notif combined)    │
│ Batch send       │ No (one-by-one)     │ Yes (up to 500)              │
│ Topic messaging  │ Yes (subscribe)     │ Yes (subscribe to topics)    │
│ Delivery confirm │ Feedback service    │ Delivery receipts (limited)  │
│ Rate limit       │ Per device token    │ Per project (quota)          │
│ Token format     │ Hex string (64ch)   │ Opaque string (~150ch)       │
│ Silent push      │ content-available:1 │ data-only message            │
│ Priority levels  │ 5 (immediately) /   │ high / normal                │
│                  │ 10 (power-aware)    │                              │
└──────────────────┴─────────────────────┴────────────────────────────────┘
```

### 8.4 Email Delivery

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    EMAIL DELIVERY ARCHITECTURE                          │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  Email Worker                                                           │
│       │                                                                 │
│       ▼                                                                 │
│  ┌──────────────────────────────────────┐                               │
│  │  1. RENDER EMAIL                     │                               │
│  │     - HTML template (MJML → HTML)    │                               │
│  │     - Plain text fallback            │                               │
│  │     - Inline CSS for compatibility   │                               │
│  │     - Tracking pixel injection       │                               │
│  │     - Click tracking URL rewrite     │                               │
│  └──────────────┬───────────────────────┘                               │
│                 │                                                        │
│                 ▼                                                        │
│  ┌──────────────────────────────────────┐                               │
│  │  2. PROVIDER SELECTION               │                               │
│  │     Primary: Amazon SES              │                               │
│  │     Fallback: SendGrid               │                               │
│  │     Selection based on:              │                               │
│  │     - Provider health score          │                               │
│  │     - Current error rate             │                               │
│  │     - Sending quota remaining        │                               │
│  └──────────────┬───────────────────────┘                               │
│                 │                                                        │
│                 ▼                                                        │
│  ┌──────────────────────────────────────┐                               │
│  │  3. SEND via SES API                 │                               │
│  │     - DKIM signing                   │                               │
│  │     - SPF alignment                  │                               │
│  │     - Custom return-path for bounces │                               │
│  └──────────────┬───────────────────────┘                               │
│                 │                                                        │
│                 ▼                                                        │
│  ┌──────────────────────────────────────┐                               │
│  │  4. WEBHOOK PROCESSING               │                               │
│  │     SES/SendGrid → SNS → Lambda     │                               │
│  │                                      │                               │
│  │     Events received:                 │                               │
│  │     - Delivery  → status=delivered   │                               │
│  │     - Bounce    → status=bounced,    │                               │
│  │                   mark email invalid │                               │
│  │     - Complaint → status=complained, │                               │
│  │                   auto-unsubscribe   │                               │
│  │     - Open      → status=read       │                               │
│  │     - Click     → status=clicked    │                               │
│  └──────────────────────────────────────┘                               │
│                                                                         │
│  BOUNCE MANAGEMENT:                                                    │
│  ┌──────────────────────────────────────────────────────────┐           │
│  │  Hard bounce (invalid email)   → Permanently suppress   │           │
│  │  Soft bounce (inbox full)      → Retry 3x over 24h     │           │
│  │  Complaint (marked as spam)    → Auto-unsubscribe,      │           │
│  │                                  add to suppression list │           │
│  │  Suppression list checked BEFORE sending every email     │           │
│  └──────────────────────────────────────────────────────────┘           │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

### 8.5 Deduplication and Idempotency

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    DEDUPLICATION STRATEGY                                │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  LAYER 1: API-LEVEL IDEMPOTENCY                                        │
│  ┌──────────────────────────────────────────────────────────┐           │
│  │  Client sends X-Idempotency-Key header                   │           │
│  │                                                          │           │
│  │  Redis command:                                          │           │
│  │    SET idempotency:{key} {response_json} NX EX 300      │           │
│  │                                                          │           │
│  │  If SET succeeds (NX) → Process notification            │           │
│  │  If SET fails (exists) → Return cached response         │           │
│  │                                                          │           │
│  │  TTL: 5 minutes (configurable)                           │           │
│  └──────────────────────────────────────────────────────────┘           │
│                                                                         │
│  LAYER 2: CONTENT-BASED DEDUPLICATION                                  │
│  ┌──────────────────────────────────────────────────────────┐           │
│  │  Fingerprint = SHA256(user_id + template_id + channel    │           │
│  │                       + data_hash)                       │           │
│  │                                                          │           │
│  │  Redis command:                                          │           │
│  │    SET dedup:{fingerprint} 1 NX EX 300                  │           │
│  │                                                          │           │
│  │  Prevents duplicate sends even with different            │           │
│  │  idempotency keys but same content                       │           │
│  └──────────────────────────────────────────────────────────┘           │
│                                                                         │
│  LAYER 3: KAFKA CONSUMER IDEMPOTENCY                                   │
│  ┌──────────────────────────────────────────────────────────┐           │
│  │  Problem: Kafka at-least-once delivery can cause         │           │
│  │  duplicate processing on consumer rebalance              │           │
│  │                                                          │           │
│  │  Solution:                                               │           │
│  │  1. Check processed:{notification_id} in Redis           │           │
│  │  2. If exists → Skip (already processed)                │           │
│  │  3. If not exists → Process and SET with TTL 1 hour     │           │
│  │  4. Commit Kafka offset after successful processing     │           │
│  └──────────────────────────────────────────────────────────┘           │
│                                                                         │
│  DEDUP FLOW:                                                           │
│                                                                         │
│  Request ──► API Idempotency ──► Content Dedup ──► Kafka ──►           │
│              (Layer 1)           (Layer 2)              Consumer        │
│                │                    │                   Idempotency     │
│                │                    │                   (Layer 3)       │
│              Duplicate?           Duplicate?           Duplicate?      │
│              Return cached        Drop silently        Skip            │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

### 8.6 Rate Limiting

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    RATE LIMITING DESIGN                                  │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  MULTI-LEVEL RATE LIMITING:                                            │
│                                                                         │
│  Level 1: API Gateway                                                  │
│  ┌──────────────────────────────────────────────────────────┐           │
│  │  Per API key: 10,000 req/min (token bucket)             │           │
│  │  Global: 100,000 req/min                                 │           │
│  │  Burst: 2x sustained rate for 10 seconds                │           │
│  └──────────────────────────────────────────────────────────┘           │
│                                                                         │
│  Level 2: Per User                                                     │
│  ┌──────────────────────────────────────────────────────────┐           │
│  │  Max notifications per user per day: 50 (default)        │           │
│  │  Max push per user per hour: 5                           │           │
│  │  Max SMS per user per day: 3                             │           │
│  │  Max email per user per day: 10                          │           │
│  │                                                          │           │
│  │  Implementation: Redis sliding window                    │           │
│  │                                                          │           │
│  │  EVAL "                                                  │           │
│  │    local key = KEYS[1]                                   │           │
│  │    local window = ARGV[1]                                │           │
│  │    local limit = ARGV[2]                                 │           │
│  │    local now = ARGV[3]                                   │           │
│  │                                                          │           │
│  │    redis.call('ZREMRANGEBYSCORE', key, 0, now - window) │           │
│  │    local count = redis.call('ZCARD', key)                │           │
│  │    if count < tonumber(limit) then                       │           │
│  │      redis.call('ZADD', key, now, now .. math.random()) │           │
│  │      redis.call('EXPIRE', key, window)                  │           │
│  │      return 1  -- allowed                                │           │
│  │    end                                                   │           │
│  │    return 0    -- rate limited                            │           │
│  │  " 1 rate:{user}:{channel} {window_sec} {limit} {now}  │           │
│  └──────────────────────────────────────────────────────────┘           │
│                                                                         │
│  Level 3: Per Provider                                                 │
│  ┌──────────────────────────────────────────────────────────┐           │
│  │  APNs:    Respect per-device rate limits                 │           │
│  │  FCM:     600K msg/min per project                       │           │
│  │  SES:     200 emails/sec (adjustable)                    │           │
│  │  Twilio:  Carrier-specific limits                        │           │
│  │                                                          │           │
│  │  Implementation: Token bucket at worker level            │           │
│  │  If approaching limit → slow down consumer poll rate     │           │
│  └──────────────────────────────────────────────────────────┘           │
│                                                                         │
│  RATE LIMIT EXCEEDED BEHAVIOR:                                         │
│  ┌──────────────────────────────────────────────────────────┐           │
│  │  Option A: Drop silently (for low-priority marketing)   │           │
│  │  Option B: Queue for later (within TTL window)          │           │
│  │  Option C: Aggregate into digest (if digest enabled)    │           │
│  │  Option D: Return 429 to caller (API-level)             │           │
│  └──────────────────────────────────────────────────────────┘           │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

### 8.7 In-App Notification Delivery

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    IN-APP NOTIFICATION SYSTEM                           │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  TWO DELIVERY MODES:                                                   │
│                                                                         │
│  MODE 1: REAL-TIME (WebSocket / SSE)                                   │
│  ┌──────────────────────────────────────────────────────────┐           │
│  │                                                          │           │
│  │  In-App Worker                                          │           │
│  │       │                                                  │           │
│  │       ├──► Redis Pub/Sub: PUBLISH user:{user_id} {msg}  │           │
│  │       │                                                  │           │
│  │       │    WebSocket Server Farm (clustered)             │           │
│  │       │    ┌──────────┐ ┌──────────┐ ┌──────────┐       │           │
│  │       │    │  WS #1   │ │  WS #2   │ │  WS #3   │       │           │
│  │       │    │ (users   │ │ (users   │ │ (users   │       │           │
│  │       │    │  A-G)    │ │  H-P)    │ │  Q-Z)    │       │           │
│  │       │    └────┬─────┘ └────┬─────┘ └────┬─────┘       │           │
│  │       │         │            │            │              │           │
│  │       │    Each subscribes to Redis channels for        │           │
│  │       │    its connected users                          │           │
│  │       │         │            │            │              │           │
│  │       │         ▼            ▼            ▼              │           │
│  │       │    ┌─────────┐ ┌─────────┐ ┌─────────┐          │           │
│  │       │    │ Browser │ │ Browser │ │ Browser │          │           │
│  │       │    │ Client  │ │ Client  │ │ Client  │          │           │
│  │       │    └─────────┘ └─────────┘ └─────────┘          │           │
│  │       │                                                  │           │
│  │       └──► Cassandra: persist notification               │           │
│  │       └──► Redis ZADD: add to user's in-app feed        │           │
│  │       └──► Redis INCR: increment unread count           │           │
│  └──────────────────────────────────────────────────────────┘           │
│                                                                         │
│  MODE 2: PULL (REST API polling)                                       │
│  ┌──────────────────────────────────────────────────────────┐           │
│  │  Client polls GET /v1/notifications/users/{id}           │           │
│  │  every 30-60 seconds when WebSocket unavailable          │           │
│  │                                                          │           │
│  │  Response served from Redis (hot data, last 30 days)     │           │
│  │  Falls back to Cassandra for older notifications         │           │
│  └──────────────────────────────────────────────────────────┘           │
│                                                                         │
│  UNREAD COUNT MANAGEMENT:                                              │
│  ┌──────────────────────────────────────────────────────────┐           │
│  │  On new notification:                                    │           │
│  │    INCR in_app:unread:{user_id}                         │           │
│  │                                                          │           │
│  │  On mark-as-read:                                        │           │
│  │    DECR in_app:unread:{user_id}                         │           │
│  │    HSET in_app:detail:{notif_id} read true              │           │
│  │                                                          │           │
│  │  On mark-all-read:                                       │           │
│  │    SET in_app:unread:{user_id} 0                        │           │
│  │    Batch update read flag in Cassandra (async)          │           │
│  └──────────────────────────────────────────────────────────┘           │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

### 8.8 Digest and Aggregation

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    DIGEST / AGGREGATION ENGINE                          │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  USE CASE: User receives 20 "new follower" notifications in 1 hour.   │
│  Instead of 20 separate pushes, aggregate into:                        │
│  "You have 20 new followers including @alice and @bob"                 │
│                                                                         │
│  AGGREGATION RULES:                                                    │
│  ┌──────────────────────────────────────────────────────────┐           │
│  │  Rule: {                                                 │           │
│  │    "category": "social.follow",                          │           │
│  │    "aggregate_window": "1h",                             │           │
│  │    "min_count_to_aggregate": 3,                          │           │
│  │    "digest_template": "new_followers_digest",            │           │
│  │    "channels": ["push", "email"]                         │           │
│  │  }                                                       │           │
│  └──────────────────────────────────────────────────────────┘           │
│                                                                         │
│  IMPLEMENTATION:                                                       │
│                                                                         │
│  ┌─────────┐    ┌────────────────┐    ┌──────────────────┐              │
│  │ Notif   │───►│ Aggregation    │───►│ Redis buffer:    │              │
│  │ arrives │    │ check: does    │    │ LPUSH digest:    │              │
│  │         │    │ this category  │    │ {user}:{cat}     │              │
│  │         │    │ support digest?│    │ {notif_data}     │              │
│  └─────────┘    └────────────────┘    └──────────────────┘              │
│                                             │                           │
│                                             ▼                           │
│                 ┌────────────────────────────────────────────┐          │
│                 │  Digest Scheduler (cron every 5 min):      │          │
│                 │                                            │          │
│                 │  For each user with buffered notifications:│          │
│                 │  1. LLEN digest:{user}:{cat}               │          │
│                 │  2. If count >= min_count_to_aggregate:     │          │
│                 │     a. LRANGE to get all buffered notifs   │          │
│                 │     b. Render digest template              │          │
│                 │     c. Send single aggregated notification │          │
│                 │     d. DEL digest:{user}:{cat}             │          │
│                 │  3. If window expired and count < min:      │          │
│                 │     a. Send individual notifications       │          │
│                 │     b. DEL buffer                           │          │
│                 └────────────────────────────────────────────┘          │
│                                                                         │
│  DAILY EMAIL DIGEST:                                                   │
│  ┌──────────────────────────────────────────────────────────┐           │
│  │  For users with digest_frequency=daily:                  │           │
│  │  1. Collect all notifications from past 24h              │           │
│  │  2. Group by category                                    │           │
│  │  3. Render daily digest email template                   │           │
│  │  4. Send at user's preferred digest_time in their TZ     │           │
│  │  5. Mark individual notifications as "digested"          │           │
│  └──────────────────────────────────────────────────────────┘           │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 9. Data Partitioning and Sharding

### Partitioning Strategy

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    PARTITIONING STRATEGY                                 │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  CASSANDRA: NOTIFICATION RECORDS                                       │
│  ┌──────────────────────────────────────────────────────────┐           │
│  │  Partition key: (user_id, created_date)                  │           │
│  │  Clustering key: notification_id (TIMEUUID DESC)         │           │
│  │                                                          │           │
│  │  WHY user_id + date?                                     │           │
│  │  • user_id alone → partitions grow unbounded             │           │
│  │  • Adding date → bounded partition size                  │           │
│  │  • Typical user: 5-20 notifs/day → small partitions     │           │
│  │  • Power users: 100-200/day → still manageable          │           │
│  │                                                          │           │
│  │  Access patterns:                                        │           │
│  │  ✓ Get user's notifications for today (single partition)│           │
│  │  ✓ Get user's recent notifications (few partitions)     │           │
│  │  ✗ Get all notifications by template (full scan)        │           │
│  │    → Use analytics DB (ClickHouse) for this             │           │
│  └──────────────────────────────────────────────────────────┘           │
│                                                                         │
│  CASSANDRA: DELIVERY LOGS                                              │
│  ┌──────────────────────────────────────────────────────────┐           │
│  │  Partition key: notification_id                          │           │
│  │  Clustering key: attempt_num                             │           │
│  │                                                          │           │
│  │  Typically 1-3 rows per notification (1 + retries)      │           │
│  │  TTL: 90 days (auto-cleanup)                             │           │
│  └──────────────────────────────────────────────────────────┘           │
│                                                                         │
│  MYSQL: USER PREFERENCES (Aurora)                                      │
│  ┌──────────────────────────────────────────────────────────┐           │
│  │  500M users → shard by user_id hash                     │           │
│  │  16 shards → ~31M rows per shard                        │           │
│  │                                                          │           │
│  │  Shard routing: shard_id = hash(user_id) % 16           │           │
│  │                                                          │           │
│  │  Each shard: Aurora cluster (1 writer + 2 readers)      │           │
│  │  Read replicas handle preference lookups                 │           │
│  │  Writer handles preference updates                       │           │
│  └──────────────────────────────────────────────────────────┘           │
│                                                                         │
│  KAFKA: PARTITION STRATEGY                                             │
│  ┌──────────────────────────────────────────────────────────┐           │
│  │  Partition key: user_id                                  │           │
│  │                                                          │           │
│  │  Benefits:                                               │           │
│  │  • Per-user ordering guaranteed within a partition       │           │
│  │  • Even distribution (user IDs are UUIDs)               │           │
│  │                                                          │           │
│  │  Partition count per topic:                              │           │
│  │  • P0: 4 (low volume, fast processing)                  │           │
│  │  • P1: 8                                                 │           │
│  │  • P2: 32 (highest volume)                               │           │
│  │  • P3: 16                                                │           │
│  └──────────────────────────────────────────────────────────┘           │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

### Hot Partition Mitigation

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    HOT PARTITION SCENARIOS                               │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  PROBLEM: Bulk notification to 10M users lands on all Kafka partitions │
│  at once, but some partitions may be temporarily slower.                │
│                                                                         │
│  SOLUTION 1: Bulk Request Throttling                                   │
│  ┌──────────────────────────────────────────────────────────┐           │
│  │  Bulk API accepts segment_id instead of user list        │           │
│  │  Background job resolves segment to user list             │           │
│  │  Produces to Kafka at controlled rate (10K/sec)          │           │
│  │  Prevents overwhelming any single partition              │           │
│  └──────────────────────────────────────────────────────────┘           │
│                                                                         │
│  SOLUTION 2: Salted Partition Keys                                     │
│  ┌──────────────────────────────────────────────────────────┐           │
│  │  For broadcast/bulk: key = user_id + random_salt         │           │
│  │  Spreads load across all partitions                      │           │
│  │  Trade-off: loses per-user ordering for bulk sends       │           │
│  │  Acceptable because bulk sends don't need ordering       │           │
│  └──────────────────────────────────────────────────────────┘           │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 10. Caching Strategy

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    CACHING ARCHITECTURE                                  │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  CACHE LAYER 1: REDIS (Shared Cache)                                   │
│  ┌──────────────────────────────────────────────────────────────┐       │
│  │                                                              │       │
│  │  User Preferences:                                          │       │
│  │  Key:    pref:{user_id}                                     │       │
│  │  Value:  JSON blob of full preferences                      │       │
│  │  TTL:    1 hour                                              │       │
│  │  Hit rate: ~95%                                              │       │
│  │  Write-through: on preference update, invalidate + re-cache │       │
│  │                                                              │       │
│  │  Device Tokens:                                             │       │
│  │  Key:    tokens:{user_id}                                   │       │
│  │  Value:  List of {platform, token, app_version}             │       │
│  │  TTL:    24 hours                                            │       │
│  │  Hit rate: ~90%                                              │       │
│  │  Invalidation: on token refresh or 410 Gone from APNs       │       │
│  │                                                              │       │
│  │  Rate Limit Counters:                                       │       │
│  │  Key:    rate:{user_id}:{channel}:{window}                  │       │
│  │  Value:  Sorted Set (sliding window) or Counter             │       │
│  │  TTL:    Matches rate limit window                           │       │
│  │                                                              │       │
│  │  Deduplication Keys:                                        │       │
│  │  Key:    dedup:{fingerprint}                                │       │
│  │  Value:  1                                                   │       │
│  │  TTL:    5 minutes                                           │       │
│  │                                                              │       │
│  │  In-App Feed:                                               │       │
│  │  Key:    in_app:{user_id}                                   │       │
│  │  Value:  Sorted Set (score=timestamp, value=notif_id)       │       │
│  │  Size:   Last 100 notifications per user                    │       │
│  │  TTL:    30 days                                             │       │
│  │                                                              │       │
│  └──────────────────────────────────────────────────────────────┘       │
│                                                                         │
│  CACHE LAYER 2: LOCAL (In-Process Cache)                               │
│  ┌──────────────────────────────────────────────────────────────┐       │
│  │                                                              │       │
│  │  Templates:                                                 │       │
│  │  Storage:  Caffeine / Guava Cache (JVM heap)                │       │
│  │  TTL:      5 minutes                                         │       │
│  │  Max size: 10,000 templates                                  │       │
│  │  Hit rate: ~99% (templates change rarely)                   │       │
│  │  Invalidation: TTL-based + listen to template update events │       │
│  │                                                              │       │
│  │  Provider Health Scores:                                    │       │
│  │  Storage:  Local map, updated by circuit breaker            │       │
│  │  TTL:      10 seconds                                        │       │
│  │  Used for provider selection (SES vs SendGrid, etc.)        │       │
│  │                                                              │       │
│  └──────────────────────────────────────────────────────────────┘       │
│                                                                         │
│  CACHE SIZING:                                                         │
│  ┌──────────────────────────────────────────────────────────────┐       │
│  │  Redis cluster for notification system:                      │       │
│  │                                                              │       │
│  │  Preferences:  500M * 1KB * 20% hot  = 100 GB               │       │
│  │  Device tokens: 500M * 200B * 15% hot = 15 GB                │       │
│  │  Rate counters: 100M active * 200B    = 20 GB                │       │
│  │  Dedup keys:    5M active * 100B      = 0.5 GB               │       │
│  │  In-app feeds:  100M active * 10KB    = 1 TB                 │       │
│  │  ──────────────────────────────────────                      │       │
│  │  Total Redis:                          ~1.14 TB              │       │
│  │                                                              │       │
│  │  Redis Cluster: 24 nodes * 64GB each = 1.5 TB capacity      │       │
│  │  (with replication factor 2)                                 │       │
│  └──────────────────────────────────────────────────────────────┘       │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 11. Replication and Consistency

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    CONSISTENCY MODEL                                     │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  COMPONENT              │ CONSISTENCY  │ RATIONALE                      │
│  ───────────────────────┼──────────────┼───────────────────────────     │
│  Notification records   │ Eventual     │ Write-heavy; seconds-level    │
│  (Cassandra)            │ (QUORUM)     │ lag OK. CL=QUORUM for writes  │
│                         │              │ ensures durability.            │
│                         │              │                                │
│  Delivery status        │ Eventual     │ Append-only logs, no conflict │
│  (Cassandra)            │ (ONE)        │ CL=ONE for writes (speed),    │
│                         │              │ CL=ONE for reads.              │
│                         │              │                                │
│  User preferences       │ Eventual     │ Strong consistency not needed. │
│  (MySQL Aurora)         │ (seconds)    │ Read from replica; brief lag   │
│                         │              │ after update is acceptable.    │
│                         │              │ Worst case: one notification   │
│                         │              │ sent with old preferences.     │
│                         │              │                                │
│  Templates              │ Eventual     │ Cached locally with 5-min TTL.│
│  (MySQL Aurora)         │ (minutes)    │ Template update takes up to    │
│                         │              │ 5 min to propagate.            │
│                         │              │                                │
│  Rate limit counters    │ Best-effort  │ Redis cluster; slightly        │
│  (Redis)                │              │ overcounting is acceptable     │
│                         │              │ (user gets rate limited        │
│                         │              │ slightly early, better than    │
│                         │              │ not at all).                   │
│                         │              │                                │
│  In-app feed            │ Eventual     │ New notifications appear       │
│  (Redis + Cassandra)    │ (sub-second) │ within 1s. Read-your-writes   │
│                         │              │ via Redis primary.             │
│                         │              │                                │
│  Dedup keys             │ Best-effort  │ False negative (duplicate sent)│
│  (Redis)                │              │ is rare; false positive        │
│                         │              │ (notif dropped) never happens  │
│                         │              │ because SETNX is atomic.       │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

### Multi-Region Replication

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    MULTI-REGION DEPLOYMENT                              │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  ┌──────────────────────────┐    ┌──────────────────────────┐           │
│  │     US-EAST (Primary)    │    │     EU-WEST (Secondary)  │           │
│  │                          │    │                          │           │
│  │  ┌────────────────────┐  │    │  ┌────────────────────┐  │           │
│  │  │ Notification Svc   │  │    │  │ Notification Svc   │  │           │
│  │  │ (stateless)        │  │    │  │ (stateless)        │  │           │
│  │  └────────────────────┘  │    │  └────────────────────┘  │           │
│  │                          │    │                          │           │
│  │  ┌────────────────────┐  │    │  ┌────────────────────┐  │           │
│  │  │ Kafka Cluster      │◄─┼────┼──│ Kafka Mirror Maker │  │           │
│  │  │ (source of truth)  │──┼────┼─►│ (replicated topics)│  │           │
│  │  └────────────────────┘  │    │  └────────────────────┘  │           │
│  │                          │    │                          │           │
│  │  ┌────────────────────┐  │    │  ┌────────────────────┐  │           │
│  │  │ Cassandra DC1      │◄─┼────┼──│ Cassandra DC2      │  │           │
│  │  │ (LOCAL_QUORUM)     │──┼────┼─►│ (LOCAL_QUORUM)     │  │           │
│  │  └────────────────────┘  │    │  └────────────────────┘  │           │
│  │                          │    │                          │           │
│  │  ┌────────────────────┐  │    │  ┌────────────────────┐  │           │
│  │  │ Redis Cluster      │  │    │  │ Redis Cluster      │  │           │
│  │  │ (independent)      │  │    │  │ (independent)      │  │           │
│  │  └────────────────────┘  │    │  └────────────────────┘  │           │
│  │                          │    │                          │           │
│  │  ┌────────────────────┐  │    │  ┌────────────────────┐  │           │
│  │  │ Aurora Global DB   │──┼────┼─►│ Aurora Read Replica │  │           │
│  │  │ (writer)           │  │    │  │ (reader)           │  │           │
│  │  └────────────────────┘  │    │  └────────────────────┘  │           │
│  └──────────────────────────┘    └──────────────────────────┘           │
│                                                                         │
│  ROUTING:                                                              │
│  • Users routed to nearest region via GeoDNS                           │
│  • Each region processes notifications for its local users             │
│  • Cassandra async replication ensures global read availability         │
│  • Redis caches are region-local (no cross-region replication)          │
│  • On region failover: DNS switches, warm-up cache from Cassandra     │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 12. Fault Tolerance and Failure Handling

### Failure Scenarios and Mitigations

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    FAILURE HANDLING MATRIX                               │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  SCENARIO 1: THIRD-PARTY PROVIDER DOWN (APNs/FCM/SES/Twilio)          │
│  ┌──────────────────────────────────────────────────────────┐           │
│  │  Detection:                                              │           │
│  │    Circuit breaker monitors error rate (threshold: 50%)  │           │
│  │    5xx errors, timeouts, connection refused               │           │
│  │                                                          │           │
│  │  Response:                                               │           │
│  │    1. Circuit breaker trips → OPEN state                 │           │
│  │    2. Switch to fallback provider:                       │           │
│  │       Push:  APNs down → queue for retry (no fallback)  │           │
│  │       Email: SES down → switch to SendGrid               │           │
│  │       SMS:   Twilio down → switch to AWS SNS             │           │
│  │    3. Retry with exponential backoff:                    │           │
│  │       Attempt 1: immediate                               │           │
│  │       Attempt 2: 5 seconds                               │           │
│  │       Attempt 3: 30 seconds                              │           │
│  │       Attempt 4: 5 minutes                               │           │
│  │       Attempt 5: 30 minutes                              │           │
│  │    4. After max retries → DLQ for manual review          │           │
│  │    5. Half-open probe every 30 seconds to check recovery│           │
│  └──────────────────────────────────────────────────────────┘           │
│                                                                         │
│  SCENARIO 2: KAFKA BROKER FAILURE                                      │
│  ┌──────────────────────────────────────────────────────────┐           │
│  │  Detection: Producer timeout, consumer disconnection     │           │
│  │                                                          │           │
│  │  Response:                                               │           │
│  │    • Kafka replication (RF=3): 1 broker down = no impact │           │
│  │    • Producer: acks=all, retries=3, retry.backoff.ms=100│           │
│  │    • Consumer: auto rebalance assigns orphaned partitions│           │
│  │    • If 2+ brokers down: temporary write to local disk  │           │
│  │      queue, drain when Kafka recovers                    │           │
│  └──────────────────────────────────────────────────────────┘           │
│                                                                         │
│  SCENARIO 3: REDIS CLUSTER FAILURE                                     │
│  ┌──────────────────────────────────────────────────────────┐           │
│  │  Impact: Preferences, rate limits, dedup unavailable     │           │
│  │                                                          │           │
│  │  Response:                                               │           │
│  │    • Rate limiting: FAIL OPEN (allow all, risk over-send)│           │
│  │    • Preferences: Fall back to MySQL directly            │           │
│  │    • Dedup: Fall back to Cassandra lookup (slower)       │           │
│  │    • In-app feed: Serve from Cassandra (higher latency) │           │
│  │    • Redis Cluster auto-failover: replica promotion <30s │           │
│  └──────────────────────────────────────────────────────────┘           │
│                                                                         │
│  SCENARIO 4: NOTIFICATION SERVICE CRASH                                │
│  ┌──────────────────────────────────────────────────────────┐           │
│  │  Detection: Health check failure, load balancer removes  │           │
│  │                                                          │           │
│  │  Response:                                               │           │
│  │    • Stateless service → other instances handle traffic  │           │
│  │    • API Gateway retries to healthy instances             │           │
│  │    • Auto-scaling replaces crashed instance               │           │
│  │    • In-flight requests: client retries with idempotency │           │
│  │      key prevents duplicates                             │           │
│  └──────────────────────────────────────────────────────────┘           │
│                                                                         │
│  SCENARIO 5: CASSANDRA NODE FAILURE                                    │
│  ┌──────────────────────────────────────────────────────────┐           │
│  │  RF=3 with CL=QUORUM:                                   │           │
│  │    1 node down → reads/writes still succeed (2 of 3)    │           │
│  │    2 nodes down → writes fail, reads may succeed (1 of 3)│           │
│  │                                                          │           │
│  │  Response:                                               │           │
│  │    • Hinted handoff catches up when node recovers        │           │
│  │    • Anti-entropy repair runs daily                       │           │
│  │    • If prolonged failure: replace node, stream data     │           │
│  └──────────────────────────────────────────────────────────┘           │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

### Dead Letter Queue (DLQ) Processing

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    DLQ PROCESSING PIPELINE                              │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  Channel Worker                                                        │
│       │                                                                 │
│       │  Max retries exhausted (5 attempts)                            │
│       │  or non-retryable error (invalid token, bad template)          │
│       │                                                                 │
│       ▼                                                                 │
│  ┌──────────────────────────────────────┐                               │
│  │  Kafka Topic: notif-dlq              │                               │
│  │                                      │                               │
│  │  Message includes:                   │                               │
│  │  • Original notification             │                               │
│  │  • Error history (all attempts)      │                               │
│  │  • Last error code and message       │                               │
│  │  • Timestamp of each retry           │                               │
│  └──────────────┬───────────────────────┘                               │
│                 │                                                        │
│                 ▼                                                        │
│  ┌──────────────────────────────────────┐                               │
│  │  DLQ Processor                       │                               │
│  │                                      │                               │
│  │  1. Classify error:                  │                               │
│  │     PERMANENT:                       │                               │
│  │       • Invalid device token         │                               │
│  │       • Invalid email address        │                               │
│  │       → Mark notification as FAILED  │                               │
│  │       → Update device/email status   │                               │
│  │                                      │                               │
│  │     TRANSIENT:                       │                               │
│  │       • Provider temporary error     │                               │
│  │       • Timeout                      │                               │
│  │       → Re-enqueue with delay (1h)   │                               │
│  │       → Max DLQ retries: 3           │                               │
│  │                                      │                               │
│  │     UNKNOWN:                         │                               │
│  │       → Alert on-call engineer       │                               │
│  │       → Store for manual inspection  │                               │
│  │                                      │                               │
│  │  2. Update notification status       │                               │
│  │  3. Log to analytics for reporting   │                               │
│  └──────────────────────────────────────┘                               │
│                                                                         │
│  DLQ DASHBOARD METRICS:                                                │
│  • Messages in DLQ by error type                                       │
│  • DLQ ingestion rate (should be <0.1% of total)                       │
│  • Average time in DLQ before resolution                               │
│  • Auto-resolved vs manually-resolved ratio                            │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 13. Scalability

### Scaling Strategy

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    SCALABILITY ARCHITECTURE                             │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  HORIZONTAL SCALING POINTS:                                            │
│                                                                         │
│  ┌─────────────────────────────────────────────────────────────┐        │
│  │  Component              │ Scaling Mechanism      │ Trigger  │        │
│  │  ───────────────────────┼───────────────────────┼──────────│        │
│  │  API Gateway            │ Auto-scale pods       │ CPU >60% │        │
│  │  Notification Service   │ Auto-scale pods       │ CPU >60% │        │
│  │  Push Workers           │ Auto-scale + Kafka    │ Consumer │        │
│  │                         │ partition increase    │ lag >1K  │        │
│  │  Email Workers          │ Auto-scale (+ SES     │ Queue    │        │
│  │                         │ rate increase)        │ depth    │        │
│  │  SMS Workers            │ Auto-scale            │ Queue    │        │
│  │                         │                       │ depth    │        │
│  │  In-App Workers         │ Auto-scale + WS pods  │ Conn     │        │
│  │                         │                       │ count    │        │
│  │  Kafka Cluster          │ Add brokers + rebal.  │ Disk/CPU │        │
│  │  Cassandra              │ Add nodes to ring     │ Disk >70%│        │
│  │  Redis                  │ Add shards (resharding)│ Mem >80%│        │
│  └─────────────────────────────────────────────────────────────┘        │
│                                                                         │
│  KAFKA SCALING:                                                        │
│  ┌──────────────────────────────────────────────────────────┐           │
│  │  Current: 32 partitions for P2-Normal push topic         │           │
│  │  At 50K/sec: each partition handles ~1.5K msg/sec        │           │
│  │                                                          │           │
│  │  To scale to 200K/sec (4x):                              │           │
│  │  1. Increase partitions: 32 → 128                        │           │
│  │  2. Add more consumer instances: 32 → 128                │           │
│  │  3. Add Kafka brokers: 6 → 12                            │           │
│  │                                                          │           │
│  │  NOTE: Increasing partitions is one-way in Kafka.        │           │
│  │  Plan partition count for 2x expected peak.              │           │
│  └──────────────────────────────────────────────────────────┘           │
│                                                                         │
│  WORKER SCALING:                                                       │
│  ┌──────────────────────────────────────────────────────────┐           │
│  │  Each channel worker type scales independently:          │           │
│  │                                                          │           │
│  │  Normal load (12K/sec total):                            │           │
│  │    Push workers:  20 instances                           │           │
│  │    Email workers: 15 instances                           │           │
│  │    SMS workers:   5 instances                            │           │
│  │    In-app workers: 10 instances                          │           │
│  │                                                          │           │
│  │  Peak load (50K/sec total):                              │           │
│  │    Push workers:  80 instances                           │           │
│  │    Email workers: 60 instances                           │           │
│  │    SMS workers:   20 instances                           │           │
│  │    In-app workers: 30 instances                          │           │
│  │                                                          │           │
│  │  Auto-scaling trigger: Kafka consumer lag > 1000 msgs    │           │
│  │  Scale-down delay: 10 minutes after lag < 100            │           │
│  └──────────────────────────────────────────────────────────┘           │
│                                                                         │
│  HANDLING NOTIFICATION STORMS (Flash Sale, Breaking News):             │
│  ┌──────────────────────────────────────────────────────────┐           │
│  │  1. Pre-warm workers before scheduled events             │           │
│  │  2. Bulk sends are split into micro-batches              │           │
│  │     (10K recipients per batch, 100ms delay between)      │           │
│  │  3. Priority queue ensures P0/P1 are not starved         │           │
│  │  4. Auto-scaler kicks in within 2 minutes                │           │
│  │  5. Provider rate limits enforced to avoid throttling    │           │
│  │  6. Kafka buffers absorb temporary spikes                │           │
│  └──────────────────────────────────────────────────────────┘           │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 14. Monitoring and Observability

### Key Metrics Dashboard

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    MONITORING DASHBOARD                                  │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  DELIVERY METRICS:                                                     │
│  ┌──────────────────────────────────────────────────────────┐           │
│  │  • delivery_success_rate (by channel, by priority)       │           │
│  │    Target: >99.5% for push, >99% for email, >98% for SMS│           │
│  │                                                          │           │
│  │  • delivery_latency_p50 / p95 / p99 (by channel)        │           │
│  │    Target: p99 < 2s for push, p99 < 30s for email       │           │
│  │                                                          │           │
│  │  • notifications_sent_total (counter, by channel)        │           │
│  │  • notifications_failed_total (counter, by error type)   │           │
│  │  • notifications_rate_limited_total (counter)            │           │
│  │  • notifications_deduplicated_total (counter)            │           │
│  └──────────────────────────────────────────────────────────┘           │
│                                                                         │
│  QUEUE METRICS:                                                        │
│  ┌──────────────────────────────────────────────────────────┐           │
│  │  • kafka_consumer_lag (by topic, by consumer group)      │           │
│  │    ALERT: if lag > 10K for P0 topic                      │           │
│  │    ALERT: if lag > 100K for P2 topic                     │           │
│  │                                                          │           │
│  │  • kafka_produce_rate (msg/sec, by topic)                │           │
│  │  • kafka_consume_rate (msg/sec, by consumer group)       │           │
│  │  • dlq_depth (messages in dead letter queue)             │           │
│  │    ALERT: if > 1000 messages                             │           │
│  └──────────────────────────────────────────────────────────┘           │
│                                                                         │
│  PROVIDER METRICS:                                                     │
│  ┌──────────────────────────────────────────────────────────┐           │
│  │  • provider_error_rate (by provider: APNs/FCM/SES/etc)  │           │
│  │    ALERT: if > 5% error rate                             │           │
│  │                                                          │           │
│  │  • provider_latency_p95 (by provider)                    │           │
│  │  • provider_throttle_count (429 responses)               │           │
│  │  • circuit_breaker_state (OPEN/CLOSED/HALF_OPEN)         │           │
│  │  • invalid_token_rate (indicates stale device tokens)    │           │
│  └──────────────────────────────────────────────────────────┘           │
│                                                                         │
│  USER ENGAGEMENT METRICS:                                              │
│  ┌──────────────────────────────────────────────────────────┐           │
│  │  • notification_open_rate (by channel, by category)      │           │
│  │  • notification_click_rate (for actionable notifications)│           │
│  │  • opt_out_rate (by channel, by category)                │           │
│  │    ALERT: if opt-out rate spikes >2x normal              │           │
│  │  • unsubscribe_rate (email)                              │           │
│  └──────────────────────────────────────────────────────────┘           │
│                                                                         │
│  INFRASTRUCTURE METRICS:                                               │
│  ┌──────────────────────────────────────────────────────────┐           │
│  │  • Redis memory_usage / hit_rate / eviction_count        │           │
│  │  • Cassandra read_latency / write_latency / compactions  │           │
│  │  • Worker CPU / memory / instance_count                  │           │
│  │  • WebSocket active_connections / messages_per_sec       │           │
│  └──────────────────────────────────────────────────────────┘           │
│                                                                         │
│  ALERTING RULES:                                                       │
│  ┌──────────────────────────────────────────────────────────┐           │
│  │  P1 (Page on-call):                                      │           │
│  │    • Delivery success rate < 95% for 5 min               │           │
│  │    • P0 consumer lag > 10K for 2 min                     │           │
│  │    • All providers for a channel in OPEN state           │           │
│  │    • DLQ depth > 10K                                     │           │
│  │                                                          │           │
│  │  P2 (Slack alert):                                       │           │
│  │    • Delivery success rate < 99% for 10 min              │           │
│  │    • P2 consumer lag > 50K for 5 min                     │           │
│  │    • Single provider error rate > 10% for 5 min          │           │
│  │    • Opt-out rate 2x above weekly average                │           │
│  └──────────────────────────────────────────────────────────┘           │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

### Distributed Tracing

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    DISTRIBUTED TRACE (Single Notification)              │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  trace_id: abc-123-def-456                                             │
│                                                                         │
│  ┌─ API Gateway ─────────────────────────────────┐  50ms               │
│  │  span: gateway.receive                        │                      │
│  │  tags: method=POST, path=/v1/notifications    │                      │
│  └──────────────┬────────────────────────────────┘                      │
│                 │                                                        │
│  ┌─ Notification Service ────────────────────────┐  180ms              │
│  │  ┌─ validate ────────────┐  30ms              │                      │
│  │  └──────────────────────-┘                    │                      │
│  │  ┌─ dedup.check ─────────┐  10ms              │                      │
│  │  └──────────────────────-┘                    │                      │
│  │  ┌─ preferences.check ──┐  20ms (Redis hit)  │                      │
│  │  └──────────────────────-┘                    │                      │
│  │  ┌─ ratelimit.check ────┐  10ms              │                      │
│  │  └──────────────────────-┘                    │                      │
│  │  ┌─ template.render ────┐  30ms              │                      │
│  │  └──────────────────────-┘                    │                      │
│  │  ┌─ kafka.produce ──────┐  50ms              │                      │
│  │  └──────────────────────-┘                    │                      │
│  │  ┌─ cassandra.write ────┐  30ms              │                      │
│  │  └──────────────────────-┘                    │                      │
│  └───────────────────────────────────────────────┘                      │
│                 │  (async from here)                                     │
│  ┌─ Push Worker ─────────────────────────────────┐  550ms              │
│  │  ┌─ kafka.consume ──────┐  30ms              │                      │
│  │  └──────────────────────-┘                    │                      │
│  │  ┌─ device.tokens.get ──┐  5ms (Redis hit)   │                      │
│  │  └──────────────────────-┘                    │                      │
│  │  ┌─ apns.send ──────────┐  500ms             │                      │
│  │  └──────────────────────-┘                    │                      │
│  │  ┌─ delivery.track ────┐  10ms               │                      │
│  │  └──────────────────────-┘                    │                      │
│  └───────────────────────────────────────────────┘                      │
│                                                                         │
│  Total trace duration: ~780ms                                          │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 15. Trade-offs and Design Decisions

### Decision Matrix

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    KEY DESIGN DECISIONS                                  │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  DECISION 1: Push vs Pull for In-App Notifications                     │
│  ┌──────────────────────────────────────────────────────────┐           │
│  │  Option A: WebSocket (Push)                              │           │
│  │    ✓ Real-time delivery (<100ms)                         │           │
│  │    ✓ Reduces server load (no polling)                    │           │
│  │    ✗ Connection management complexity                     │           │
│  │    ✗ Sticky sessions or Redis pub/sub needed             │           │
│  │                                                          │           │
│  │  Option B: Long Polling (Pull)                           │           │
│  │    ✓ Simpler infrastructure                              │           │
│  │    ✓ Works through all proxies/firewalls                 │           │
│  │    ✗ Higher latency (seconds)                            │           │
│  │    ✗ More server load from frequent polls                │           │
│  │                                                          │           │
│  │  CHOSEN: Hybrid                                          │           │
│  │    WebSocket as primary (real-time for connected users)  │           │
│  │    REST polling as fallback (for environments where      │           │
│  │    WebSocket is blocked)                                 │           │
│  └──────────────────────────────────────────────────────────┘           │
│                                                                         │
│  DECISION 2: At-Least-Once vs Exactly-Once Delivery                    │
│  ┌──────────────────────────────────────────────────────────┐           │
│  │  Option A: At-Least-Once                                 │           │
│  │    ✓ Simpler implementation                              │           │
│  │    ✓ Higher delivery guarantee                           │           │
│  │    ✗ Possible duplicates (mitigated by dedup layers)     │           │
│  │                                                          │           │
│  │  Option B: Exactly-Once                                  │           │
│  │    ✓ No duplicates                                       │           │
│  │    ✗ Significantly more complex (2PC or idempotent       │           │
│  │      consumers with transactional outbox)               │           │
│  │    ✗ Higher latency                                      │           │
│  │    ✗ Not achievable end-to-end (providers don't          │           │
│  │      guarantee exactly-once)                            │           │
│  │                                                          │           │
│  │  CHOSEN: At-Least-Once with multi-layer deduplication    │           │
│  │    Rationale: Exactly-once is impossible with external    │           │
│  │    providers. 3-layer dedup makes duplicates extremely    │           │
│  │    rare (<0.001%).                                        │           │
│  └──────────────────────────────────────────────────────────┘           │
│                                                                         │
│  DECISION 3: Single Queue vs Per-Channel Queues                        │
│  ┌──────────────────────────────────────────────────────────┐           │
│  │  Option A: Single Queue (all channels in one topic)      │           │
│  │    ✓ Simpler topology                                    │           │
│  │    ✗ Slow channel (email) blocks fast channel (push)     │           │
│  │    ✗ Cannot scale channels independently                 │           │
│  │                                                          │           │
│  │  Option B: Per-Channel + Per-Priority Topics             │           │
│  │    ✓ Independent scaling per channel                     │           │
│  │    ✓ Slow channel doesn't affect others                  │           │
│  │    ✓ Different consumer configurations per priority      │           │
│  │    ✗ More Kafka topics to manage (16 total)             │           │
│  │    ✗ More operational complexity                         │           │
│  │                                                          │           │
│  │  CHOSEN: Per-Channel + Per-Priority                      │           │
│  │    Rationale: Isolation is critical for availability.     │           │
│  │    A Twilio outage should not affect push delivery.      │           │
│  └──────────────────────────────────────────────────────────┘           │
│                                                                         │
│  DECISION 4: Template Rendering Location                               │
│  ┌──────────────────────────────────────────────────────────┐           │
│  │  Option A: Render in Notification Service (before queue) │           │
│  │    ✓ Rendered content stored in Kafka (debuggable)       │           │
│  │    ✓ Template version locked at send time                │           │
│  │    ✗ Larger Kafka messages (rendered content > template) │           │
│  │                                                          │           │
│  │  Option B: Render in Channel Worker (after queue)        │           │
│  │    ✓ Smaller Kafka messages                              │           │
│  │    ✗ Template may change between enqueue and delivery    │           │
│  │    ✗ Channel workers need template engine + cache        │           │
│  │                                                          │           │
│  │  CHOSEN: Render before queue (Option A)                  │           │
│  │    Rationale: Template version consistency is important.  │           │
│  │    Message size increase is modest (~500B vs ~200B).     │           │
│  └──────────────────────────────────────────────────────────┘           │
│                                                                         │
│  DECISION 5: Vendor Lock-in vs Abstraction                             │
│  ┌──────────────────────────────────────────────────────────┐           │
│  │  CHOSEN: Provider abstraction layer                      │           │
│  │                                                          │           │
│  │  Each channel has a provider interface:                  │           │
│  │    interface PushProvider {                               │           │
│  │      send(token, payload): DeliveryResult                │           │
│  │      isHealthy(): boolean                                │           │
│  │    }                                                     │           │
│  │                                                          │           │
│  │  Implementations: APNsProvider, FCMProvider               │           │
│  │                                                          │           │
│  │  Benefits:                                               │           │
│  │  • Switch providers without code changes                 │           │
│  │  • A/B test providers for deliverability                 │           │
│  │  • Automatic failover between providers                  │           │
│  │  • Gradual migration to new provider                     │           │
│  └──────────────────────────────────────────────────────────┘           │
│                                                                         │
│  DECISION 6: Cassandra vs DynamoDB for Notification Storage            │
│  ┌──────────────────────────────────────────────────────────┐           │
│  │  Cassandra:                                              │           │
│  │    ✓ No vendor lock-in                                   │           │
│  │    ✓ Predictable performance at scale                    │           │
│  │    ✓ Built-in TTL for automatic data expiry              │           │
│  │    ✓ Multi-DC replication built-in                       │           │
│  │    ✗ Operational overhead (manage cluster)               │           │
│  │                                                          │           │
│  │  DynamoDB:                                               │           │
│  │    ✓ Fully managed                                       │           │
│  │    ✓ Auto-scaling                                        │           │
│  │    ✗ Cost at 1B writes/day can be significant            │           │
│  │    ✗ TTL deletes are eventual (up to 48h lag)            │           │
│  │    ✗ AWS-only                                            │           │
│  │                                                          │           │
│  │  CHOSEN: Cassandra (for cost control at scale and        │           │
│  │  multi-cloud flexibility)                                │           │
│  └──────────────────────────────────────────────────────────┘           │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 16. Interview Deep-Dive Questions

### Q1: How do you handle notification storms (e.g., everyone gets notified at once)?

**A:** Notification storms (flash sales, breaking news, system-wide announcements) can
generate millions of notifications simultaneously. We handle this through several
mechanisms:

1. **Bulk API with micro-batching:** The bulk send API does not produce all messages to
   Kafka at once. Instead, it creates a background job that produces in micro-batches
   (10K messages per batch with 100ms delay between batches), spreading the load over
   minutes rather than seconds.

2. **Pre-warming:** For planned events (scheduled sale), we pre-scale workers 30 minutes
   before. The scheduler service exposes an API for capacity planning.

3. **Priority isolation:** Storm notifications are typically P2 or P3. The separate
   Kafka topics ensure P0 urgent notifications (password reset, security alerts) are
   unaffected.

4. **Provider rate limiting:** Workers enforce provider-specific rate limits (SES: 200/sec,
   FCM: 600K/min) using token bucket algorithms, preventing provider throttling.

5. **Kafka as buffer:** With 32 partitions and replication, Kafka can buffer millions of
   messages while workers process at sustainable rates.

---

### Q2: How do you prevent duplicate notifications?

**A:** Three-layer deduplication:

- **Layer 1 (API):** Idempotency key in Redis with 5-min TTL. Same request ID returns
  cached response.
- **Layer 2 (Content):** SHA256 fingerprint of (user_id + template + channel + data).
  Prevents duplicate sends from different API calls with same content.
- **Layer 3 (Consumer):** Kafka consumer checks `processed:{notification_id}` in Redis
  before processing. Handles at-least-once delivery duplication from consumer rebalance.

Combined, these reduce duplicate delivery to <0.001% of total notifications.

---

### Q3: How do you handle timezone-aware scheduling?

**A:** When a notification is scheduled for "9:00 AM user's local time":

1. Fetch user's timezone from preferences (e.g., "America/New_York").
2. Convert "9:00 AM America/New_York" to UTC epoch timestamp.
3. Store in Redis ZSET (sorted set) with score = UTC epoch.
4. Scheduler polls ZRANGEBYSCORE every 1 second for due notifications.
5. Handle DST transitions: use IANA timezone database, which accounts for DST
   shifts (e.g., 2:00 AM might not exist during spring-forward).

For bulk sends across timezones: the system fans out into multiple scheduled entries,
one per timezone cohort. For example, "send at 9 AM local" for global users creates ~24
batches, one per major timezone offset.

---

### Q4: What happens when APNs/FCM is down?

**A:** Unlike email and SMS, push notifications have no alternative provider -- APNs is the
only way to reach iOS devices, FCM for Android. Our strategy:

1. **Circuit breaker trips** after 50% error rate over 30 seconds.
2. **Messages stay in Kafka** (retention: 7 days). Workers pause consumption.
3. **Circuit breaker half-open probe** every 30 seconds sends a test push.
4. **When provider recovers**, circuit closes, workers resume, backlog drains.
5. **TTL enforcement:** Notifications older than their TTL are discarded (a "flash sale"
   notification 6 hours late is worse than no notification).
6. **Channel fallback:** If push fails and notification is high priority, fallback to
   in-app + email based on user preferences.

---

### Q5: How do you A/B test notification content?

**A:** Template versioning supports A/B testing:

1. Template has multiple variants: `order_shipped_v2_A`, `order_shipped_v2_B`.
2. Notification Service hashes `user_id` to deterministically assign variant
   (consistent hashing ensures same user always sees same variant).
3. Variant ID is stored in the notification record.
4. Analytics pipeline correlates variant with engagement metrics (open rate, click
   rate, conversion).
5. After statistical significance reached, winning variant becomes the default.

---

### Q6: How do you ensure ordering of related notifications?

**A:** Kafka partition key is `user_id`, which guarantees all notifications for a user
land on the same partition and are consumed in order by a single consumer. This ensures
"Order Placed" arrives before "Order Shipped."

For cross-channel ordering (push before email for same event), we use sequence numbers
in the notification metadata and a small delay (2 seconds) between channel dispatches.

---

### Q7: How do you handle user preference updates propagating to in-flight notifications?

**A:** We use a "snapshot at send time" approach:

1. When the Notification Service processes a request, it reads current preferences.
2. The preference snapshot (channel enabled, quiet hours, etc.) is included in the
   Kafka message.
3. Channel workers use the snapshotted preferences, not a fresh lookup.
4. This means a preference change made after the notification is queued but before
   delivery will not affect that notification.
5. Trade-off: A user who unsubscribes may receive 1-2 more notifications that were
   already in the pipeline. This is acceptable and common in the industry.

---

### Q8: How do you handle multi-device push delivery?

**A:** A single user may have multiple devices (phone, tablet, watch):

1. Device token table stores all active tokens per user, with platform and last-used
   timestamp.
2. When sending a push notification, the worker fetches ALL active device tokens.
3. Sends to each device independently (separate APNs/FCM calls).
4. Each delivery is tracked independently (device A delivered, device B failed).
5. Collapse key ensures only the latest notification shows if multiple arrive while
   device was offline.
6. Stale token cleanup: if a device token returns 410 Gone, it is deactivated.
   Additionally, devices not used for 90 days are proactively cleaned up.

---

### Q9: How would you add a new notification channel (e.g., WhatsApp)?

**A:** The provider abstraction makes this straightforward:

1. Create new Kafka topics: `notif-whatsapp-p{0-3}`.
2. Implement `WhatsAppProvider` conforming to the `Channel` interface.
3. Create WhatsApp worker fleet that consumes from the new topics.
4. Add `whatsapp` to the channel enum in templates and preferences.
5. Add WhatsApp-specific fields to the template table.
6. Deploy worker fleet, update API schema, publish new template format.

No changes needed to the Notification Service core pipeline -- it is channel-agnostic.
Estimated effort: 1-2 weeks for a senior engineer.

---

### Q10: How do you handle cost optimization for SMS?

**A:** SMS is the most expensive channel (~$0.01 per message). Cost controls:

1. **SMS opt-in required:** Users must explicitly enable SMS (default: off).
2. **Rate limits:** Max 3 SMS per user per day (configurable).
3. **Priority gating:** Only P0 and P1 notifications sent via SMS.
4. **Smart routing:** Use local carrier gateways for domestic SMS (cheaper than
   international routes via Twilio).
5. **Message length optimization:** Keep SMS under 160 characters to avoid multi-part
   messages (each part billed separately).
6. **Fallback:** If SMS budget exhausted, fall back to push + email.
7. **Cost monitoring:** Real-time SMS spend tracking with daily budget alerts.

---

### Q11: What is the retry strategy, and how do you prevent retry storms?

**A:** Retry strategy uses exponential backoff with jitter:

```
delay = min(base_delay * 2^attempt + random_jitter, max_delay)

Attempt 1: 0s (immediate)
Attempt 2: 5s + jitter (0-2s)
Attempt 3: 30s + jitter (0-10s)
Attempt 4: 5 min + jitter (0-30s)
Attempt 5: 30 min + jitter (0-60s)
Max attempts: 5, then DLQ
```

**Retry storm prevention:**
- Jitter spreads retry attempts across time, preventing synchronized retries.
- Per-provider circuit breaker stops retries when provider is confirmed down.
- Retry count is tracked per notification; DLQ after max attempts.
- Global retry rate limiter caps total retry throughput at 10% of normal throughput.

---

### Q12: How do you handle notification preferences at scale (500M users)?

**A:** Preferences are read-heavy (read on every notification, written rarely):

1. **MySQL Aurora** as source of truth, sharded by `user_id` (16 shards).
2. **Redis cache** with 1-hour TTL, ~95% hit rate.
3. **Write-through caching:** On preference update, write to MySQL, then invalidate
   Redis cache. Next read populates cache from MySQL.
4. **Bulk preference queries:** For segment-based sends, pre-fetch preferences in
   batch (WHERE user_id IN (...)) rather than one-by-one.
5. **Default preferences:** New users get sensible defaults (push + email enabled,
   SMS disabled). Only store deviations from default to reduce storage.

---

### Q13: How do you ensure compliance with regulations (CAN-SPAM, GDPR)?

**A:** Regulatory compliance is enforced at multiple levels:

1. **CAN-SPAM (email):**
   - Every marketing email includes unsubscribe link.
   - Unsubscribe requests processed within 10 minutes (regulatory requirement: 10 days).
   - Physical mailing address in email footer.
   - Accurate From/Subject lines.

2. **GDPR (EU users):**
   - Explicit consent recorded before sending marketing notifications.
   - Right to erasure: API to delete all notification history for a user.
   - Data retention: automatic purge after 90 days (hot) / 1 year (cold).
   - Data portability: export user's notification history as JSON.

3. **TCPA (SMS in US):**
   - Prior express written consent for marketing SMS.
   - Easy opt-out (reply STOP).
   - Time-of-day restrictions (no SMS before 8 AM or after 9 PM local).

---

### Q14: How do you design the collapse/replace notification feature?

**A:** Collapse key groups related notifications so only the latest is shown:

1. Sender includes `collapse_key` (e.g., `"order_update_98765"`).
2. **For push:** APNs `apns-collapse-id` and FCM `collapse_key` natively replace
   prior notifications with the same key on the device.
3. **For in-app:** Before inserting new notification into Redis ZSET, check if a
   notification with the same collapse_key exists. If yes, update it in-place rather
   than adding a new entry.
4. **For email:** Collapse key is less useful (emails can't be replaced). Instead,
   use a dedup window: if another email with the same collapse_key was sent in the last
   5 minutes, skip this one.

Use case: Ride-sharing app sends "Driver is 5 min away," then "Driver is 2 min away."
With collapse, only the latest ETA shows on the user's lock screen.

---

### Q15: How would you migrate from a monolithic notification system to this architecture?

**A:** Phased migration strategy:

1. **Phase 1 - Dual Write (2 weeks):**
   - Deploy new system alongside monolith.
   - Monolith sends to both old path and new system (shadow mode).
   - Compare delivery results, fix discrepancies.
   - New system does NOT deliver to users yet.

2. **Phase 2 - Canary (2 weeks):**
   - Route 1% of traffic to new system (by user_id hash).
   - Monitor delivery rates, latency, error rates.
   - Gradually increase: 5% → 10% → 25% → 50%.

3. **Phase 3 - Full Migration (1 week):**
   - Route 100% to new system.
   - Keep monolith on standby for 1 week.
   - Monitor for regressions.

4. **Phase 4 - Decommission (1 week):**
   - Shut down monolith notification path.
   - Archive monolith notification data.

Key risk mitigation: Feature flags control routing percentage. Instant rollback by
flipping flag to 0%.

---

## Summary: System at a Glance

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    NOTIFICATION SYSTEM SUMMARY                          │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  SCALE:          1B notifications/day, 50K/sec peak                    │
│  CHANNELS:       Push (APNs/FCM), Email (SES), SMS (Twilio), In-App   │
│  LATENCY:        <1s urgent, <30s normal (internal <250ms)             │
│  AVAILABILITY:   99.99% (multi-region, stateless services)             │
│  DELIVERY:       At-least-once with 3-layer deduplication              │
│  QUEUE:          Kafka (per-channel, per-priority topics)              │
│  STORAGE:        Cassandra (notifs), MySQL (prefs), Redis (cache)     │
│  SCALING:        Independent channel workers, Kafka partition scaling  │
│  FAULT TOL.:     Circuit breakers, DLQ, provider failover              │
│                                                                         │
│  KEY PATTERNS:                                                         │
│  • Fan-out on write (multi-channel delivery)                           │
│  • Priority queues (topic-per-priority)                                │
│  • Provider abstraction (swap/failover providers)                      │
│  • Idempotent processing (3-layer dedup)                               │
│  • Circuit breaker (provider health management)                        │
│  • Event sourcing (notification lifecycle tracking)                    │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```
