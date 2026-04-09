# Design a Chat Messaging System (WhatsApp / Messenger)

**Difficulty:** Hard | **Category:** Real-Time Communication | **Time:** 45 min  
**Companies:** Meta, Google, Microsoft, Uber, Slack, Discord, LinkedIn, Telegram

---

## 1. Problem Statement and Scope

Design a real-time chat messaging system similar to WhatsApp or Facebook Messenger that
supports billions of users with low-latency message delivery, reliable storage, and
rich communication features including media sharing and group chats.

### In Scope

- 1-on-1 private messaging with real-time delivery
- Group messaging (up to 256 members per group)
- Message delivery status tracking (sent, delivered, read)
- Online/offline presence indicators
- Push notifications for offline users
- Message history retrieval and search
- Media sharing (images, videos, documents)
- End-to-end encryption (E2E)
- Multi-device synchronization

### Out of Scope

- Voice and video calling (separate system)
- Stories / Status features
- Payment integration
- Bot platform and business API
- Sticker / GIF marketplace

---

## 2. Functional Requirements

### Core Messaging

| # | Requirement                          | Priority |
|---|--------------------------------------|----------|
| 1 | Send and receive 1-on-1 text messages in real-time | P0 |
| 2 | Group chat with up to 256 members    | P0       |
| 3 | Message ordering within a conversation | P0      |
| 4 | Delivery receipts: sent / delivered / read | P0   |
| 5 | Push notifications for offline users | P0       |
| 6 | Message history and scroll-back      | P0       |
| 7 | Media sharing (images, video, files up to 100MB) | P1 |
| 8 | Online / offline / last-seen presence | P1      |
| 9 | End-to-end encryption                | P1       |
| 10| Multi-device sync (phone, tablet, web) | P1     |
| 11| Message search across conversations  | P2       |
| 12| Message deletion (for me / for everyone) | P2   |
| 13| Typing indicators                    | P2       |
| 14| Message reactions (emoji)            | P3       |

### User Stories

1. **Send Message:** User A types a message and sends it to User B. User B receives it
   instantly if online, or via push notification and offline queue if not.

2. **Group Chat:** User creates a group, adds members. Each message sent is delivered to
   all active members in real-time. Offline members get notifications and catch up later.

3. **Read Receipts:** When User B opens the chat and views the message, User A sees a
   "read" indicator with a timestamp.

4. **Media Share:** User selects a photo, the client uploads it to the media service,
   gets a URL, and sends a message referencing the media URL.

---

## 3. Non-Functional Requirements

| Requirement        | Target                                    | Rationale                        |
|--------------------|-------------------------------------------|----------------------------------|
| Latency            | < 100ms message delivery (same region)    | Real-time conversation feel      |
| Availability       | 99.99% (52 min downtime/year)             | Critical communication service   |
| Durability         | 99.9999% (no message loss)                | Users expect zero data loss      |
| Throughput         | 230K+ messages/sec sustained              | 500M DAU, 40 msgs/user/day      |
| Consistency        | Causal ordering within conversation       | Messages must appear in order    |
| Presence           | Eventual consistency (< 10s lag)          | Acceptable for online status     |
| Scalability        | Support 2B registered, 500M DAU           | WhatsApp-scale                   |
| Message size       | Up to 64KB text, 100MB media              | Support rich content             |
| Connection scale   | 500M concurrent WebSocket connections     | One per active user              |
| Security           | End-to-end encryption for all messages    | Privacy requirement              |

### SLA Breakdown

```
Message Delivery Latency (p50/p95/p99):
  Same region:    30ms / 80ms  / 150ms
  Cross-region:   80ms / 200ms / 500ms

Availability per component:
  WebSocket Gateway:    99.99%
  Chat Service:         99.99%
  Message Store:        99.999%
  Push Notifications:   99.9%
```

---

## 4. Back-of-Envelope Estimation

### Traffic Estimates

```
Registered users:          2 Billion
Daily Active Users (DAU):  500 Million
Avg messages sent/day:     40 per user

Daily messages:            500M x 40 = 20 Billion messages/day
Messages per second:       20B / 86400 = ~230,000 msg/sec
Peak (3x average):         ~700,000 msg/sec

Group messages:            30% of total = 6B/day
  Avg group size:          20 members
  Fan-out messages:        6B x 20 = 120B fan-out deliveries/day
  Fan-out per second:      120B / 86400 = ~1.4M deliveries/sec
```

### Storage Estimates

```
Average message size:      1 KB (text + metadata)
Daily message storage:     20B x 1KB = 20 TB/day
Yearly message storage:    20TB x 365 = 7.3 PB/year
With replication (3x):     ~22 PB/year

Media messages:            5% of messages = 1B/day
Average media size:        200 KB (thumbnails) + 2 MB (original)
Daily media storage:       1B x 2.2MB = 2.2 PB/day
Yearly media storage:      ~800 PB/year (with CDN offloading)
```

### Connection Estimates

```
Concurrent connections:    500 Million WebSocket connections
Per connection memory:     ~10 KB (buffers, session state)
Total connection memory:   500M x 10KB = 5 TB

Connection servers needed: 500M / 100K connections each = 5,000 servers
  (each server: 64GB RAM, 100K concurrent connections)

Heartbeat traffic:         500M heartbeats every 30s = 16.7M/sec
```

### Bandwidth Estimates

```
Inbound messages:    230K/sec x 1KB = 230 MB/sec = 1.84 Gbps
Fan-out outbound:    1.4M/sec x 1KB = 1.4 GB/sec = 11.2 Gbps
Media uploads:       1B/day x 2MB / 86400 = 23 GB/sec = 184 Gbps
Media downloads:     3x uploads (views) = ~550 Gbps (served from CDN)
```

### Summary Table

| Resource               | Daily        | Yearly     |
|------------------------|-------------|------------|
| Messages               | 20 Billion  | 7.3T       |
| Message storage        | 20 TB       | 7.3 PB     |
| Media storage          | 2.2 PB      | 800 PB     |
| Fan-out deliveries     | 120 Billion | 43.8T      |
| WebSocket connections  | 500M peak   | -          |
| Connection servers     | 5,000       | -          |

---

## 5. API Design

### 5.1 WebSocket Protocol (Real-Time)

The primary communication channel uses WebSocket with a custom binary protocol
for efficiency. Messages are framed with a type byte followed by protobuf payload.

```
WebSocket Frame Format:
┌──────────┬──────────┬───────────────────────────────┐
│ Type (1B)│ Len (4B) │ Protobuf Payload (variable)   │
└──────────┴──────────┴───────────────────────────────┘

Message Types:
  0x01 = SEND_MESSAGE
  0x02 = ACK_MESSAGE
  0x03 = DELIVER_MESSAGE
  0x04 = READ_RECEIPT
  0x05 = TYPING_INDICATOR
  0x06 = PRESENCE_UPDATE
  0x07 = HEARTBEAT / PONG
```

#### sendMessage

```
Client -> Server (0x01 SEND_MESSAGE):
{
  "client_msg_id": "uuid-v4",          // Client-generated for dedup
  "conversation_id": "conv_abc123",
  "sender_id": "user_123",
  "recipient_id": "user_456",          // null for group messages
  "group_id": "grp_789",              // null for 1-on-1
  "content": {
    "type": "TEXT | IMAGE | VIDEO | FILE",
    "text": "Hello!",
    "media_url": null,
    "thumbnail_url": null,
    "encryption_key": "base64_key"
  },
  "reply_to_msg_id": null,
  "timestamp": 1680000000000
}

Server -> Client (0x02 ACK_MESSAGE):
{
  "client_msg_id": "uuid-v4",
  "server_msg_id": "msg_snowflake_id",
  "server_timestamp": 1680000000005,
  "status": "SENT"
}
```

#### deliverMessage

```
Server -> Recipient (0x03 DELIVER_MESSAGE):
{
  "server_msg_id": "msg_snowflake_id",
  "conversation_id": "conv_abc123",
  "sender_id": "user_123",
  "content": { ... },
  "server_timestamp": 1680000000005,
  "sequence_number": 42            // Per-conversation ordering
}

Recipient -> Server (0x02 ACK_MESSAGE):
{
  "server_msg_id": "msg_snowflake_id",
  "status": "DELIVERED",
  "timestamp": 1680000000050
}
```

#### readReceipt

```
Client -> Server (0x04 READ_RECEIPT):
{
  "conversation_id": "conv_abc123",
  "last_read_msg_id": "msg_snowflake_id",
  "last_read_seq": 42,
  "timestamp": 1680000000100
}
```

### 5.2 REST APIs

#### Group Management

```
POST /api/v1/groups
{
  "name": "Engineering Team",
  "members": ["user_123", "user_456", "user_789"],
  "avatar_url": "https://media.example.com/..."
}
Response: 201 Created
{
  "group_id": "grp_abc",
  "conversation_id": "conv_grp_abc",
  "created_at": "2024-01-01T00:00:00Z"
}

PUT /api/v1/groups/{group_id}/members
{
  "action": "ADD | REMOVE",
  "user_ids": ["user_999"]
}

GET /api/v1/groups/{group_id}
Response: { group metadata, member list, admin list }
```

#### Message History

```
GET /api/v1/conversations/{conv_id}/messages
    ?before_seq=100
    &limit=50
    &direction=BACKWARD

Response: 200 OK
{
  "messages": [ ... ],
  "has_more": true,
  "oldest_seq": 51
}
```

#### Media Upload

```
POST /api/v1/media/upload
Content-Type: multipart/form-data

Fields:
  file: <binary>
  type: "IMAGE | VIDEO | FILE"
  conversation_id: "conv_abc123"

Response: 200 OK
{
  "media_id": "media_xyz",
  "url": "https://media-cdn.example.com/...",
  "thumbnail_url": "https://media-cdn.example.com/.../thumb",
  "encryption_key": "base64_key",
  "size_bytes": 2048000,
  "expires_at": null
}
```

#### Presence

```
PUT /api/v1/users/{user_id}/presence
{
  "status": "ONLINE | OFFLINE | AWAY",
  "last_seen": "2024-01-01T12:00:00Z"
}

GET /api/v1/users/{user_id}/presence
Response: { "status": "ONLINE", "last_seen": "..." }
```

---

## 6. Data Model and Database Selection

### 6.1 Database Selection Rationale

```
┌─────────────────┬──────────────────┬──────────────────────────────────────┐
│ Data             │ Database         │ Rationale                            │
├─────────────────┼──────────────────┼──────────────────────────────────────┤
│ Messages         │ Apache Cassandra │ Write-heavy, time-series, horizontal │
│                  │                  │ scaling, tunable consistency          │
├─────────────────┼──────────────────┼──────────────────────────────────────┤
│ Users, Groups    │ MySQL (Vitess)   │ Strong consistency, relational data, │
│                  │                  │ complex queries, ACID transactions   │
├─────────────────┼──────────────────┼──────────────────────────────────────┤
│ Sessions/Presence│ Redis Cluster    │ In-memory, sub-ms reads, TTL-based   │
│                  │                  │ expiry for sessions                  │
├─────────────────┼──────────────────┼──────────────────────────────────────┤
│ Message Queue    │ Apache Kafka     │ Ordered, durable, high-throughput    │
│                  │                  │ message delivery pipeline            │
├─────────────────┼──────────────────┼──────────────────────────────────────┤
│ Media/Files      │ S3 + CloudFront  │ Blob storage with CDN for global     │
│                  │                  │ distribution                         │
├─────────────────┼──────────────────┼──────────────────────────────────────┤
│ Search Index     │ Elasticsearch    │ Full-text search across messages     │
│                  │                  │ (async indexing via Kafka)            │
└─────────────────┴──────────────────┴──────────────────────────────────────┘
```

### 6.2 Messages Table (Cassandra)

```sql
-- Primary message store: partitioned by conversation for efficient retrieval
CREATE TABLE messages (
    conversation_id  UUID,
    sequence_number  BIGINT,          -- Monotonically increasing per conversation
    message_id       UUID,            -- Globally unique (Snowflake ID)
    sender_id        UUID,
    content_type     TEXT,            -- TEXT, IMAGE, VIDEO, FILE
    content_text     TEXT,            -- Encrypted text body
    media_url        TEXT,
    thumbnail_url    TEXT,
    encryption_key   BLOB,
    reply_to_msg_id  UUID,
    created_at       TIMESTAMP,
    deleted_at       TIMESTAMP,       -- Soft delete
    PRIMARY KEY ((conversation_id), sequence_number)
) WITH CLUSTERING ORDER BY (sequence_number DESC);
-- Partition key: conversation_id
-- Clustering key: sequence_number DESC (newest first for scroll-back)

-- Per-user inbox: tracks conversations and unread counts
CREATE TABLE user_conversations (
    user_id          UUID,
    last_activity    TIMESTAMP,
    conversation_id  UUID,
    last_msg_seq     BIGINT,
    last_read_seq    BIGINT,
    unread_count     INT,
    is_muted         BOOLEAN,
    PRIMARY KEY ((user_id), last_activity, conversation_id)
) WITH CLUSTERING ORDER BY (last_activity DESC, conversation_id ASC);

-- Offline message queue: messages pending delivery
CREATE TABLE pending_messages (
    recipient_id     UUID,
    message_id       UUID,
    conversation_id  UUID,
    sender_id        UUID,
    content          BLOB,            -- Serialized message
    created_at       TIMESTAMP,
    retry_count      INT,
    PRIMARY KEY ((recipient_id), created_at, message_id)
) WITH CLUSTERING ORDER BY (created_at ASC);
-- Messages delivered oldest-first when user comes online
```

### 6.3 Users and Groups (MySQL via Vitess)

```sql
-- Users table: sharded by user_id
CREATE TABLE users (
    user_id        BIGINT PRIMARY KEY AUTO_INCREMENT,
    phone_number   VARCHAR(20) UNIQUE NOT NULL,
    display_name   VARCHAR(100),
    avatar_url     VARCHAR(500),
    public_key     BLOB,             -- For E2E encryption key exchange
    status_text    VARCHAR(200),
    created_at     DATETIME NOT NULL,
    updated_at     DATETIME NOT NULL,
    INDEX idx_phone (phone_number)
);

-- Groups table
CREATE TABLE groups (
    group_id        BIGINT PRIMARY KEY AUTO_INCREMENT,
    conversation_id BIGINT UNIQUE NOT NULL,
    name            VARCHAR(100),
    description     VARCHAR(500),
    avatar_url      VARCHAR(500),
    max_members     INT DEFAULT 256,
    created_by      BIGINT NOT NULL,
    created_at      DATETIME NOT NULL,
    updated_at      DATETIME NOT NULL,
    FOREIGN KEY (created_by) REFERENCES users(user_id)
);

-- Group membership: sharded by group_id
CREATE TABLE group_members (
    group_id    BIGINT,
    user_id     BIGINT,
    role        ENUM('ADMIN', 'MEMBER') DEFAULT 'MEMBER',
    joined_at   DATETIME NOT NULL,
    PRIMARY KEY (group_id, user_id),
    INDEX idx_user_groups (user_id)
);

-- Conversations: maps 1-on-1 and groups to conversation_id
CREATE TABLE conversations (
    conversation_id  BIGINT PRIMARY KEY AUTO_INCREMENT,
    type             ENUM('DIRECT', 'GROUP') NOT NULL,
    created_at       DATETIME NOT NULL
);

-- Direct conversation participants
CREATE TABLE conversation_participants (
    conversation_id  BIGINT,
    user_id          BIGINT,
    PRIMARY KEY (conversation_id, user_id),
    INDEX idx_user_convs (user_id, conversation_id)
);
```

### 6.4 Session and Presence (Redis)

```
# User session: maps user to their WebSocket connection server
SET user:session:{user_id} -> {
    "server_id": "ws-server-042",
    "connection_id": "conn_abc123",
    "device_type": "MOBILE",
    "connected_at": 1680000000000
} EX 300   # 5-minute TTL, refreshed by heartbeat

# Multi-device: set of active sessions
SADD user:devices:{user_id} -> ["device_1", "device_2"]

# Presence
SET user:presence:{user_id} -> {
    "status": "ONLINE",
    "last_seen": 1680000000000
} EX 60    # 60-second TTL, refreshed by heartbeat

# Conversation recent cache (last message for conversation list)
HSET conv:last_msg:{user_id} {conversation_id} -> {serialized_last_msg}
```

### 6.5 Entity Relationship Diagram

```
┌──────────────┐       ┌───────────────────┐       ┌──────────────┐
│    Users     │       │  Conversations     │       │   Groups     │
├──────────────┤       ├───────────────────┤       ├──────────────┤
│ user_id (PK) │──┐    │ conversation_id(PK)│───────│ group_id(PK) │
│ phone_number │  │    │ type              │       │ conv_id (FK) │
│ display_name │  │    │ created_at        │       │ name         │
│ public_key   │  │    └───────────────────┘       │ max_members  │
└──────────────┘  │             │                   └──────────────┘
                  │             │                          │
                  │    ┌────────┴────────┐                 │
                  │    │  Conversation   │         ┌───────┴───────┐
                  └────│  Participants   │         │ Group Members │
                       ├─────────────────┤         ├───────────────┤
                       │ conv_id (PK,FK) │         │ group_id(PK)  │
                       │ user_id (PK,FK) │         │ user_id (PK)  │
                       └─────────────────┘         │ role          │
                                                   └───────────────┘
                  ┌──────────────────────────┐
                  │    Messages (Cassandra)   │
                  ├──────────────────────────┤
                  │ conversation_id (PK)     │
                  │ sequence_number (CK)     │
                  │ message_id               │
                  │ sender_id                │
                  │ content_type             │
                  │ content_text (encrypted) │
                  │ media_url                │
                  │ created_at               │
                  └──────────────────────────┘
```

---

## 7. High-Level Architecture

### 7.0 System Overview Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              CLIENT LAYER                                   │
│                                                                             │
│   ┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐             │
│   │  Mobile   │    │  Mobile   │    │   Web    │    │ Desktop  │             │
│   │ (iOS)     │    │(Android)  │    │ Client   │    │ Client   │             │
│   └─────┬────┘    └─────┬────┘    └─────┬────┘    └─────┬────┘             │
│         │               │               │               │                   │
└─────────┼───────────────┼───────────────┼───────────────┼───────────────────┘
          │  WebSocket    │  WebSocket    │  WebSocket    │  WebSocket
          │               │               │               │
┌─────────┼───────────────┼───────────────┼───────────────┼───────────────────┐
│         ▼               ▼               ▼               ▼                   │
│   ┌─────────────────────────────────────────────────────────────┐           │
│   │              LOAD BALANCER (L4 - TCP/WebSocket)             │           │
│   │              (HAProxy / AWS NLB / Envoy)                    │           │
│   └───────────────────────┬─────────────────────────────────────┘           │
│                           │                                                 │
│   ┌───────────┬───────────┼───────────┬───────────┐                        │
│   ▼           ▼           ▼           ▼           ▼                        │
│ ┌─────┐   ┌─────┐   ┌─────┐   ┌─────┐   ┌─────┐                         │
│ │WS-1 │   │WS-2 │   │WS-3 │   │... │   │WS-N │  WebSocket Gateway       │
│ │100K │   │100K │   │100K │   │     │   │100K │  (5,000 servers)         │
│ │conns│   │conns│   │conns│   │     │   │conns│                           │
│ └──┬──┘   └──┬──┘   └──┬──┘   └──┬──┘   └──┬──┘                          │
│    │         │         │         │         │                               │
│    └─────────┴─────────┴────┬────┴─────────┘                              │
│                             │                                              │
│                     ┌───────▼────────┐                                     │
│                     │  Service Mesh  │                                      │
│                     │  (Envoy/Istio) │                                      │
│                     └───────┬────────┘                                      │
│                             │                                              │
│   ┌─────────────────────────┼─────────────────────────────┐                │
│   │                         │                             │                │
│   ▼                         ▼                             ▼                │
│ ┌──────────────┐  ┌──────────────────┐  ┌──────────────────┐              │
│ │ Chat Service │  │ Presence Service │  │  Group Service   │              │
│ │              │  │                  │  │                  │              │
│ │ - Message    │  │ - Online/Offline │  │ - Create/Update  │              │
│ │   routing    │  │ - Last seen      │  │ - Membership     │              │
│ │ - Ordering   │  │ - Heartbeat mgmt│  │ - Fan-out list   │              │
│ │ - Delivery   │  │ - Status pub/sub│  │ - Permissions    │              │
│ │   tracking   │  │                  │  │                  │              │
│ └──────┬───────┘  └────────┬─────────┘  └────────┬─────────┘              │
│        │                   │                      │                        │
│   ┌────▼───────────────────▼──────────────────────▼───────┐                │
│   │                    Apache Kafka                        │                │
│   │  ┌──────────┐  ┌──────────────┐  ┌────────────────┐  │                │
│   │  │ messages │  │   presence   │  │  notifications │  │                │
│   │  │  topic   │  │    topic     │  │     topic      │  │                │
│   │  │(256 part)│  │ (64 parts)   │  │  (128 parts)   │  │                │
│   │  └──────────┘  └──────────────┘  └────────────────┘  │                │
│   └────┬───────────────────┬──────────────────────┬──────┘                │
│        │                   │                      │                        │
│        ▼                   ▼                      ▼                        │
│ ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐              │
│ │   Message    │  │    Redis     │  │  Push Notification   │              │
│ │    Store     │  │   Cluster    │  │      Service         │              │
│ │ (Cassandra)  │  │  (Presence)  │  │                      │              │
│ │              │  │              │  │  ┌──────┐ ┌───────┐  │              │
│ │  RF=3        │  │  128 shards  │  │  │ APNs │ │ FCM   │  │              │
│ │  20TB/day    │  │  5TB memory  │  │  └──────┘ └───────┘  │              │
│ └──────────────┘  └──────────────┘  └──────────────────────┘              │
│                                                                            │
│                   ┌──────────────────────────────────┐                     │
│                   │        Media Service              │                    │
│                   │                                   │                    │
│                   │  ┌─────────┐    ┌─────────────┐  │                    │
│                   │  │   S3    │───▶│  CloudFront  │  │                    │
│                   │  │ (Media  │    │    (CDN)     │  │                    │
│                   │  │  Store) │    │              │  │                    │
│                   │  └─────────┘    └─────────────┘  │                    │
│                   └──────────────────────────────────┘                     │
│                                                                            │
│                           BACKEND SERVICES                                 │
└────────────────────────────────────────────────────────────────────────────┘
```

### 7.1 Component Breakdown

#### WebSocket Gateway (Connection Servers)

- **Purpose:** Maintain persistent WebSocket connections with clients
- **Scale:** 5,000 servers, each handling ~100K concurrent connections
- **Responsibilities:**
  - Accept and authenticate WebSocket connections
  - Route incoming messages to the Chat Service
  - Push outgoing messages to connected clients
  - Manage heartbeat and connection lifecycle
  - TLS termination and protocol handling

#### Chat Service

- **Purpose:** Core message processing, routing, and delivery logic
- **Responsibilities:**
  - Validate and process incoming messages
  - Assign server-side message IDs (Snowflake) and sequence numbers
  - Route messages to recipient connection servers
  - Persist messages to Cassandra
  - Track delivery status (sent, delivered, read)
  - Handle message deduplication using client_msg_id

#### Presence Service

- **Purpose:** Track and distribute user online/offline status
- **Responsibilities:**
  - Process heartbeats from connection servers
  - Update user presence in Redis with TTL
  - Publish presence changes to interested subscribers
  - Optimize fan-out for users with many contacts

#### Group Service

- **Purpose:** Manage group metadata and membership
- **Responsibilities:**
  - CRUD operations for groups
  - Member management (add, remove, promote)
  - Provide fan-out list for group messages
  - Enforce group policies (max members, admin permissions)

#### Push Notification Service

- **Purpose:** Deliver notifications to offline users
- **Responsibilities:**
  - Consume from notification topic in Kafka
  - Format and send via APNs (iOS) and FCM (Android)
  - Manage device tokens and notification preferences
  - Rate limiting and notification batching

#### Media Service

- **Purpose:** Handle file uploads and media processing
- **Responsibilities:**
  - Accept media uploads via HTTP multipart
  - Generate thumbnails and compressed versions
  - Store originals in S3, serve via CDN
  - Client-side encryption key management

---

## 8. Deep Dive: Core Components

### 8.1 WebSocket Connection Management

#### Connection Lifecycle

```
┌──────────┐                    ┌──────────────┐              ┌──────────┐
│  Client  │                    │  WS Gateway  │              │  Redis   │
└────┬─────┘                    └──────┬───────┘              └────┬─────┘
     │                                 │                           │
     │  1. WS Handshake + Auth Token   │                           │
     │────────────────────────────────▶│                           │
     │                                 │                           │
     │                                 │  2. Validate JWT token    │
     │                                 │──────────────────────────▶│
     │                                 │  Token valid, user_id     │
     │                                 │◀──────────────────────────│
     │                                 │                           │
     │                                 │  3. Register session      │
     │                                 │  SET user:session:{uid}   │
     │                                 │  -> {server_id, conn_id}  │
     │                                 │──────────────────────────▶│
     │                                 │                           │
     │  4. WS Connection Established   │                           │
     │◀────────────────────────────────│                           │
     │                                 │                           │
     │  5. Deliver pending messages    │                           │
     │◀────────────────────────────────│                           │
     │                                 │                           │
     │  6. Heartbeat (every 30s)       │                           │
     │────────────────────────────────▶│                           │
     │                                 │  7. Refresh session TTL   │
     │                                 │──────────────────────────▶│
     │  8. Pong                        │                           │
     │◀────────────────────────────────│                           │
     │                                 │                           │
     │  ... (no heartbeat for 60s) ... │                           │
     │                                 │  9. Session expires (TTL) │
     │                                 │         ┌─────────────────│
     │                                 │         │ DEL session     │
     │                                 │         └────────────────▶│
     │                                 │                           │
     │                                 │  10. Mark user OFFLINE    │
     │                                 │──────────────────────────▶│
     │                                 │                           │
```

#### Connection Server Internal Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    WebSocket Gateway Server                      │
│                                                                  │
│  ┌───────────────────┐  ┌──────────────────────────────────┐    │
│  │  Connection       │  │   Connection Registry             │    │
│  │  Acceptor         │  │                                   │    │
│  │                   │  │   HashMap<UserId, Connection>     │    │
│  │  - TLS handshake  │  │   HashMap<ConnId, UserId>         │    │
│  │  - Auth validation│  │                                   │    │
│  │  - Rate limiting  │  │   Capacity: 100K connections      │    │
│  └────────┬──────────┘  └────────────────┬──────────────────┘    │
│           │                              │                       │
│  ┌────────▼──────────────────────────────▼──────────────────┐    │
│  │              Event Loop (epoll / io_uring)                │    │
│  │                                                           │    │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐               │    │
│  │  │ Worker 1 │  │ Worker 2 │  │ Worker N │  (N = CPU cores)│   │
│  │  │ thread   │  │ thread   │  │ thread   │               │    │
│  │  └──────────┘  └──────────┘  └──────────┘               │    │
│  └───────────────────────────────────────────────────────────┘    │
│                                                                  │
│  ┌──────────────────┐  ┌──────────────────────┐                  │
│  │ Heartbeat        │  │  Outbound Message    │                  │
│  │ Manager          │  │  Queue               │                  │
│  │                  │  │                      │                  │
│  │ - Track last     │  │  - Per-connection    │                  │
│  │   heartbeat      │  │    bounded queue     │                  │
│  │ - Evict stale    │  │  - Backpressure      │                  │
│  │   connections    │  │    handling           │                  │
│  └──────────────────┘  └──────────────────────┘                  │
│                                                                  │
│  Memory Budget per server:                                       │
│    Connections: 100K x 10KB = 1 GB                               │
│    Buffers:     100K x 16KB = 1.6 GB                             │
│    App logic:   ~2 GB                                            │
│    OS/Runtime:  ~2 GB                                            │
│    Total:       ~7 GB (fits in 16GB server)                      │
└─────────────────────────────────────────────────────────────────┘
```

#### Session Management for Multi-Device

When a user has multiple devices (phone, tablet, web), each device maintains
its own WebSocket connection. The session registry tracks all active sessions:

```
Redis Multi-Device Session:

HSET user:sessions:user_123
  "device_mobile_ios"    -> {"server": "ws-042", "conn": "c1", "ts": 168...}
  "device_tablet_ipad"   -> {"server": "ws-107", "conn": "c2", "ts": 168...}
  "device_web_chrome"    -> {"server": "ws-233", "conn": "c3", "ts": 168...}

Message delivery: fan-out to ALL active devices
Read receipt sync: propagate across devices via sync protocol
```

### 8.2 Message Delivery and Ordering

#### 1-on-1 Message Flow

```
┌────────┐    ┌────────┐    ┌────────┐    ┌────────┐    ┌────────┐    ┌────────┐
│Sender  │    │ WS GW  │    │  Chat  │    │Cassandra│   │ WS GW  │    │Receiver│
│Client  │    │Server A│    │Service │    │        │    │Server B│    │Client  │
└───┬────┘    └───┬────┘    └───┬────┘    └───┬────┘    └───┬────┘    └───┬────┘
    │             │             │             │             │             │
    │ 1. SEND_MSG │             │             │             │             │
    │────────────▶│             │             │             │             │
    │             │ 2. Forward  │             │             │             │
    │             │────────────▶│             │             │             │
    │             │             │             │             │             │
    │             │             │ 3. Generate │             │             │
    │             │             │ msg_id +    │             │             │
    │             │             │ seq_number  │             │             │
    │             │             │             │             │             │
    │             │             │ 4. Persist  │             │             │
    │             │             │────────────▶│             │             │
    │             │             │     ACK     │             │             │
    │             │             │◀────────────│             │             │
    │             │             │             │             │             │
    │             │ 5. ACK_MSG  │             │             │             │
    │             │ (status:SENT│             │             │             │
    │◀────────────│◀────────────│             │             │             │
    │             │             │             │             │             │
    │             │             │ 6. Lookup   │             │             │
    │             │             │ receiver    │             │             │
    │             │             │ session     │             │             │
    │             │             │ (Redis)     │             │             │
    │             │             │             │             │             │
    │             │             │ 7. Route to │             │             │
    │             │             │ Server B    │             │             │
    │             │             │────────────────────────▶ │             │
    │             │             │             │             │             │
    │             │             │             │             │8. DELIVER   │
    │             │             │             │             │────────────▶│
    │             │             │             │             │             │
    │             │             │             │             │9. ACK       │
    │             │             │             │             │(DELIVERED)  │
    │             │             │◀────────────────────────── │◀────────────│
    │             │             │             │             │             │
    │             │10.Delivery  │             │             │             │
    │             │  receipt    │             │             │             │
    │◀────────────│◀────────────│             │             │             │
    │             │             │             │             │             │
```

**Key steps explained:**

1. Sender transmits message via WebSocket with a client-generated `client_msg_id`.
2. WS Gateway forwards to Chat Service (via gRPC or internal queue).
3. Chat Service generates a globally unique `msg_id` (Snowflake) and assigns a
   monotonically increasing `sequence_number` for the conversation.
4. Message is persisted to Cassandra (write quorum: LOCAL_QUORUM = 2 of 3 replicas).
5. ACK with status SENT returned to sender -- message is now durable.
6. Look up receiver's active session in Redis.
7. If receiver is online: route to their connection server.
8. Connection server pushes message to receiver's WebSocket.
9. Receiver ACKs delivery -- status changes from SENT to DELIVERED.
10. Delivery receipt pushed back to sender.

#### Sequence Number Generation

Each conversation maintains an atomic counter for message ordering:

```
┌─────────────────────────────────────────────────────────────┐
│              Sequence Number Service                         │
│                                                              │
│   Approach: Redis INCR per conversation                      │
│                                                              │
│   INCR conv:seq:{conversation_id}  -> next sequence number   │
│                                                              │
│   For high-throughput conversations (large groups):          │
│   - Pre-allocate ranges: INCRBY conv:seq:{cid} 100          │
│   - Chat Service caches range [n, n+100) locally            │
│   - Assign from local range without Redis round-trip        │
│                                                              │
│   Alternative: Hybrid Logical Clocks (HLC) for              │
│   cross-datacenter ordering without centralized counter      │
│                                                              │
│   Ordering guarantee:                                        │
│   - Within a conversation: total order via sequence_number   │
│   - Across conversations: no ordering guarantee needed       │
│   - Ties broken by (sequence_number, msg_id)                 │
└─────────────────────────────────────────────────────────────┘
```

#### At-Least-Once Delivery and Deduplication

```
Sender-side retry:
  1. Client sends message with client_msg_id (UUID)
  2. If no ACK within 5 seconds, retry (exponential backoff)
  3. Server deduplicates using client_msg_id
     Redis SET: dedup:{client_msg_id} -> msg_id  EX 3600  (1-hour TTL)

Server-side retry:
  1. After persisting message, attempt delivery
  2. If recipient offline or delivery fails, enqueue to pending_messages
  3. Delivery consumer retries with exponential backoff
  4. Recipient deduplicates using server msg_id

Dedup flow:
┌────────────┐     ┌──────────────────────────────────────┐
│   Client   │     │            Chat Service               │
│ sends msg  │     │                                       │
│ client_id  │────▶│  1. Check Redis: dedup:{client_id}   │
│ = "abc123" │     │     EXISTS? ──▶ Return cached ACK    │
│            │     │     NOT EXISTS?                        │
│            │     │  2. Process message                    │
│            │     │  3. SET dedup:{client_id} = msg_id    │
│            │     │  4. Return ACK with msg_id             │
└────────────┘     └──────────────────────────────────────┘
```

#### Offline Message Handling

```
When recipient is OFFLINE:
┌─────────────────────────────────────────────────────────┐
│                                                          │
│  1. Chat Service persists message to Cassandra           │
│  2. ACK SENT to sender                                   │
│  3. Lookup recipient session in Redis -> NOT FOUND       │
│  4. Enqueue to pending_messages table (Cassandra)        │
│  5. Publish to Kafka notifications topic                 │
│  6. Push Notification Service sends APNs/FCM             │
│                                                          │
│  When recipient comes ONLINE:                            │
│  1. WS Gateway registers session in Redis                │
│  2. Chat Service queries pending_messages for user       │
│  3. Deliver messages in sequence_number order            │
│  4. Recipient ACKs each -> update status to DELIVERED    │
│  5. Delete from pending_messages                         │
│  6. Fan out delivery receipts to senders                 │
│                                                          │
│  Optimization: batch delivery of pending messages        │
│  - Fetch up to 100 pending messages per batch            │
│  - Single WebSocket frame with multiple messages         │
│  - Single batch ACK from client                          │
└─────────────────────────────────────────────────────────┘
```

### 8.3 Presence Service

#### Architecture

```
┌──────────────────────────────────────────────────────────────────┐
│                     Presence Service                              │
│                                                                   │
│  ┌──────────────────┐    ┌─────────────────────┐                 │
│  │  Heartbeat       │    │  Presence Store      │                 │
│  │  Processor       │    │  (Redis Cluster)     │                 │
│  │                  │    │                      │                 │
│  │  WS Gateway      │    │  user:presence:{uid} │                 │
│  │  sends heartbeat │───▶│  = {ONLINE, ts}      │                 │
│  │  every 30s       │    │  TTL: 60 seconds     │                 │
│  │                  │    │                      │                 │
│  │  If no heartbeat │    │  No heartbeat ->     │                 │
│  │  in 60s -> key   │    │  TTL expires ->      │                 │
│  │  expires         │    │  user goes OFFLINE   │                 │
│  └──────────────────┘    └──────────┬──────────┘                 │
│                                     │                             │
│                            ┌────────▼────────┐                   │
│                            │  Change         │                   │
│                            │  Detection      │                   │
│                            │                 │                   │
│                            │  Redis Keyspace │                   │
│                            │  Notifications  │                   │
│                            │  on key expiry  │                   │
│                            └────────┬────────┘                   │
│                                     │                             │
│                            ┌────────▼────────┐                   │
│                            │  Fan-Out        │                   │
│                            │  Service        │                   │
│                            │                 │                   │
│                            │  Notify friends │                   │
│                            │  / contacts of  │                   │
│                            │  status change  │                   │
│                            └─────────────────┘                   │
└──────────────────────────────────────────────────────────────────┘
```

#### Presence Fan-Out Optimization

The naive approach of notifying all contacts when a user comes online creates
a fan-out storm for popular users. Optimizations:

```
Problem: User with 1000 friends comes online
  Naive: push ONLINE to all 1000 friends = 1000 messages instantly
  At scale: 500M users x avg 200 friends = 100B presence events/day

Optimization 1: Lazy Presence (Pull-based)
  - Don't push presence changes proactively
  - When User A opens chat with User B, query B's presence
  - Cache locally for 30 seconds
  - Reduces presence traffic by ~95%

Optimization 2: Active-Contact Subscription
  - Only subscribe to presence of users you've chatted with recently
  - Presence Service maintains subscription list per user
  - Fan-out only to subscribed users (typically 10-20, not 200+)

  ┌─────────────────────────────────────────┐
  │  Subscription Model                      │
  │                                          │
  │  User A opens chat with User B:          │
  │    SADD presence:subs:B -> A             │
  │    (A subscribes to B's presence)        │
  │                                          │
  │  User A closes chat / goes idle (5min):  │
  │    SREM presence:subs:B -> A             │
  │    (A unsubscribes from B's presence)    │
  │                                          │
  │  B comes online:                         │
  │    SMEMBERS presence:subs:B              │
  │    -> notify only active subscribers     │
  │    (typically 5-10 users, not 200+)      │
  └─────────────────────────────────────────┘

Optimization 3: Presence Batching
  - Batch presence updates every 5 seconds
  - Aggregate ONLINE/OFFLINE transitions
  - If user toggles rapidly (flaky connection), only send final state
```

### 8.4 Group Messaging

#### Group Message Delivery Flow

```
┌──────────┐   ┌────────┐   ┌──────────┐   ┌─────────┐   ┌──────────┐
│  Sender  │   │ WS GW  │   │  Chat    │   │  Group  │   │  Kafka   │
│          │   │        │   │ Service  │   │ Service │   │          │
└────┬─────┘   └───┬────┘   └────┬─────┘   └────┬────┘   └────┬─────┘
     │             │             │              │              │
     │  SEND_MSG   │             │              │              │
     │  group_id=G │             │              │              │
     │────────────▶│────────────▶│              │              │
     │             │             │              │              │
     │             │             │  Get members │              │
     │             │             │─────────────▶│              │
     │             │             │  [U1,U2,...   │              │
     │             │             │   U256]      │              │
     │             │             │◀─────────────│              │
     │             │             │              │              │
     │             │             │  Persist msg │              │
     │             │             │  to Cassandra│              │
     │             │             │              │              │
     │  ACK (SENT) │             │              │              │
     │◀────────────│◀────────────│              │              │
     │             │             │              │              │
     │             │             │  Fan-out:    │              │
     │             │             │  Publish to  │              │
     │             │             │  Kafka per   │              │
     │             │             │  recipient   │──────────────▶
     │             │             │              │              │
     │             │             │              │              │
```

```
Kafka Fan-Out Detail:

  Group G has 256 members.
  Message M sent to group G.

  Option A: Write-time fan-out (small groups, < 256 members)
    - Chat Service writes 256 delivery tasks to Kafka
    - Each task: {msg_id, recipient_id, conversation_id}
    - Delivery workers consume and push to each recipient's WS Gateway
    - Pro: simple, low read amplification
    - Con: 256x write amplification per message

  Option B: Read-time fan-out (large broadcast channels)
    - Store message once in group timeline
    - Each user reads from group timeline on demand
    - Pro: single write, efficient for large groups
    - Con: read amplification, harder real-time delivery

  WhatsApp approach: Write-time fan-out (groups max 256)
  Facebook Messenger: Hybrid (small groups: write-time, pages: read-time)
```

#### Group Message Ordering

```
Challenge: Ensuring all group members see messages in the same order

Solution: Single-writer sequencing per group

┌─────────────────────────────────────────────────────────────┐
│                                                              │
│  Each group has a single sequence counter:                   │
│    Redis: INCR group:seq:{group_id}                          │
│                                                              │
│  All messages for a group are serialized through             │
│  a single partition in Kafka:                                │
│    Kafka partition key = group_id                             │
│    -> All messages for a group go to same partition           │
│    -> Partition guarantees ordering                           │
│                                                              │
│  Sequence assignment:                                        │
│    1. Chat Service receives group message                    │
│    2. INCR group:seq:{group_id} -> seq = 42                  │
│    3. Message stored with seq=42                             │
│    4. All members receive message with seq=42                │
│    5. Clients insert message at correct position             │
│       based on sequence_number                               │
│                                                              │
│  Handling gaps (missed seq):                                 │
│    Client detects gap: has seq 40, receives seq 42           │
│    -> Request message for seq 41 from server                 │
│    -> Hold seq 42 in buffer until gap filled                 │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

#### Group Membership Management

```
Operations and their effects:

ADD MEMBER:
  1. Update group_members table (MySQL)
  2. Invalidate cached member list in Redis
  3. Send system message to group: "User X was added"
  4. New member receives conversation history (last 100 messages)

REMOVE MEMBER:
  1. Update group_members table
  2. Invalidate cache
  3. System message: "User X was removed"
  4. Removed user still has local copy (E2E: rotate group encryption key)

ADMIN PROMOTION:
  1. Update role in group_members
  2. System message: "User X is now an admin"

Consistency concern:
  - Member list cached in Redis with 5-minute TTL
  - Cache invalidated on membership changes
  - Stale cache risk: message might be delivered to removed member
    (acceptable: E2E encryption key rotation prevents decryption)
```

---

## 9. Data Partitioning and Sharding

### 9.1 Message Data (Cassandra)

```
┌──────────────────────────────────────────────────────────────────┐
│                Cassandra Partitioning Strategy                    │
│                                                                   │
│  Partition Key: conversation_id                                   │
│  Clustering Key: sequence_number DESC                             │
│                                                                   │
│  Why conversation_id?                                             │
│  - All messages in a conversation are co-located                  │
│  - Efficient scroll-back queries (pagination by seq range)        │
│  - Natural time-series data within a conversation                 │
│                                                                   │
│  Why NOT user_id?                                                 │
│  - User has many conversations -> hot partition for active users  │
│  - Group messages would be duplicated per user                    │
│  - conversation_id distributes more evenly                        │
│                                                                   │
│  Partition sizing:                                                │
│  - Avg conversation: 1000 messages x 1KB = 1MB per partition      │
│  - Active conversation: 100K msgs x 1KB = 100MB (well within     │
│    Cassandra's ~100MB recommended partition limit)                │
│                                                                   │
│  Ring distribution example (12-node cluster):                     │
│                                                                   │
│        Node 1          Node 2          Node 3                     │
│     ┌──────────┐    ┌──────────┐    ┌──────────┐                 │
│     │ conv_a   │    │ conv_d   │    │ conv_g   │                 │
│     │ conv_b   │    │ conv_e   │    │ conv_h   │                 │
│     │ conv_c   │    │ conv_f   │    │ conv_i   │                 │
│     │ ...      │    │ ...      │    │ ...      │                 │
│     └──────────┘    └──────────┘    └──────────┘                 │
│                                                                   │
│  Replication: NetworkTopologyStrategy                              │
│    DC-East: 3 replicas                                            │
│    DC-West: 3 replicas                                            │
│  Read consistency:  LOCAL_QUORUM (2 of 3)                         │
│  Write consistency: LOCAL_QUORUM (2 of 3)                         │
│                                                                   │
│  Compaction: TimeWindowCompactionStrategy (TWCS)                  │
│    - Optimized for time-series append-only data                   │
│    - 1-day time windows                                           │
│    - Old SSTables compacted into larger files                     │
│                                                                   │
│  TTL: Messages older than 1 year auto-expire (configurable)       │
└──────────────────────────────────────────────────────────────────┘
```

### 9.2 User Data (MySQL via Vitess)

```
┌──────────────────────────────────────────────────────────────────┐
│                   Vitess Sharding Strategy                        │
│                                                                   │
│  Shard key: user_id (hash-based sharding)                        │
│  Number of shards: 256 (expandable via Vitess resharding)        │
│                                                                   │
│  Shard 0:    user_id % 256 == 0                                  │
│  Shard 1:    user_id % 256 == 1                                  │
│  ...                                                              │
│  Shard 255:  user_id % 256 == 255                                │
│                                                                   │
│  Cross-shard queries (e.g., group members from different shards):│
│    - Handled by Vitess VTGate with scatter-gather                │
│    - Group_members table co-sharded by group_id (separate        │
│      keyspace) for efficient member lookups                      │
│                                                                   │
│  Each shard: MySQL primary + 2 replicas                          │
│  Total: 256 x 3 = 768 MySQL instances                            │
└──────────────────────────────────────────────────────────────────┘
```

### 9.3 Connection Server Routing

```
┌──────────────────────────────────────────────────────────────────┐
│            Connection Server Assignment                          │
│                                                                   │
│  Strategy: Consistent hashing on user_id                         │
│                                                                   │
│  Load Balancer assigns user to WS Gateway server based on:       │
│  1. Geographic proximity (nearest PoP / data center)             │
│  2. Server load (least connections)                              │
│  3. Sticky sessions (same server on reconnection for 5 min)      │
│                                                                   │
│  Service discovery:                                               │
│  - Chat Service needs to find which WS Gateway serves a user     │
│  - Redis lookup: user:session:{user_id} -> server_id             │
│  - Then direct gRPC call to that server for message push         │
│                                                                   │
│  Routing topology:                                                │
│                                                                   │
│  Chat Service                                                     │
│       │                                                           │
│       │  1. Redis: GET user:session:user_456                     │
│       │     -> {server: "ws-042"}                                │
│       │                                                           │
│       │  2. gRPC: ws-042.PushMessage(msg)                        │
│       ▼                                                           │
│  ws-042 Connection Server                                         │
│       │                                                           │
│       │  3. Lookup connection: user_456 -> conn_abc              │
│       │                                                           │
│       │  4. WebSocket push to conn_abc                           │
│       ▼                                                           │
│  User 456's device                                                │
└──────────────────────────────────────────────────────────────────┘
```

---

## 10. Caching Strategy

### 10.1 Cache Architecture

```
┌──────────────────────────────────────────────────────────────────┐
│                    Redis Cache Layers                             │
│                                                                   │
│  Layer 1: Session Cache (Hot)                                    │
│  ┌────────────────────────────────────────────┐                  │
│  │  user:session:{user_id}                    │                  │
│  │  -> {server_id, conn_id, device, ts}       │                  │
│  │  TTL: 5 min (refreshed by heartbeat)       │                  │
│  │  Size: 500M entries x 200B = 100 GB        │                  │
│  │  Read QPS: ~16M/sec (heartbeats)           │                  │
│  └────────────────────────────────────────────┘                  │
│                                                                   │
│  Layer 2: Conversation List Cache (Warm)                         │
│  ┌────────────────────────────────────────────┐                  │
│  │  user:convlist:{user_id}                   │                  │
│  │  -> sorted set of {conv_id, last_activity} │                  │
│  │  Each entry includes last_msg preview       │                  │
│  │  TTL: 30 min                                │                  │
│  │  Size: 100M active users x 2KB = 200 GB    │                  │
│  │  Read QPS: ~500K/sec (app opens)           │                  │
│  └────────────────────────────────────────────┘                  │
│                                                                   │
│  Layer 3: Group Metadata Cache (Warm)                            │
│  ┌────────────────────────────────────────────┐                  │
│  │  group:meta:{group_id}                     │                  │
│  │  -> {name, avatar, member_count}           │                  │
│  │  group:members:{group_id}                  │                  │
│  │  -> set of user_ids                        │                  │
│  │  TTL: 5 min (invalidated on change)        │                  │
│  │  Size: 50M groups x 5KB = 250 GB           │                  │
│  └────────────────────────────────────────────┘                  │
│                                                                   │
│  Layer 4: Presence Cache (Hot)                                   │
│  ┌────────────────────────────────────────────┐                  │
│  │  user:presence:{user_id}                   │                  │
│  │  -> {ONLINE/OFFLINE, last_seen_ts}         │                  │
│  │  TTL: 60 sec (heartbeat refresh)           │                  │
│  │  Size: 500M entries x 50B = 25 GB          │                  │
│  └────────────────────────────────────────────┘                  │
│                                                                   │
│  Total Redis memory: ~600 GB                                     │
│  Redis cluster: 128 shards x 8GB = 1 TB capacity                │
│  Replication: each shard has 1 replica = 256 instances           │
└──────────────────────────────────────────────────────────────────┘
```

### 10.2 What We Do NOT Cache

```
Message content:
  - Too much volume: 20B messages/day x 1KB = 20TB/day
  - Low cache hit rate: messages are read once and rarely revisited
  - Cassandra with SSD storage provides ~5ms reads for recent messages
  - SSTable caching in Cassandra serves as an implicit cache

User profile data (full):
  - Profile photo URLs and display names change rarely
  - Client-side caching with ETag/If-None-Match is sufficient
  - CDN caches avatars

Message search results:
  - Highly personalized, low reuse potential
  - Elasticsearch maintains its own internal caches
```

### 10.3 Cache Invalidation Strategy

```
Strategy: Event-driven invalidation via Kafka

  ┌──────────┐     ┌─────────┐     ┌────────────┐     ┌─────────┐
  │  Write   │────▶│  Kafka  │────▶│  Cache     │────▶│  Redis  │
  │  Service │     │  Event  │     │  Invalidator│    │  DEL    │
  └──────────┘     └─────────┘     └────────────┘     └─────────┘

  Events triggering invalidation:
  - New message:     Update user:convlist:{uid} (add conv to top)
  - Group change:    DEL group:meta:{gid}, group:members:{gid}
  - Profile update:  DEL user:profile:{uid}
  - Message delete:  Update user:convlist if last_msg affected

  Consistency guarantee:
  - Cache is eventually consistent (writes to DB first, then invalidate)
  - Stale cache window: typically < 1 second
  - For session data: immediate write-through (critical for routing)
```

---

## 11. Replication and Consistency

### 11.1 Multi-Region Architecture

```
┌────────────────────────────────────────────────────────────────────┐
│                    Global Multi-Region Setup                        │
│                                                                     │
│  ┌─────────────────────────┐    ┌─────────────────────────┐        │
│  │      US-East (Primary)  │    │      US-West            │        │
│  │                         │    │                         │        │
│  │  ┌─────────┐ ┌───────┐ │    │  ┌─────────┐ ┌───────┐ │        │
│  │  │ WS GWs  │ │ Chat  │ │    │  │ WS GWs  │ │ Chat  │ │        │
│  │  │ (1500)  │ │ Svc   │ │    │  │ (1000)  │ │ Svc   │ │        │
│  │  └─────────┘ └───────┘ │    │  └─────────┘ └───────┘ │        │
│  │                         │    │                         │        │
│  │  ┌─────────┐ ┌───────┐ │    │  ┌─────────┐ ┌───────┐ │        │
│  │  │Cassandra│ │ MySQL │ │    │  │Cassandra│ │ MySQL │ │        │
│  │  │ DC-East │ │Primary│ │◀──▶│  │ DC-West │ │Replica│ │        │
│  │  │ (RF=3)  │ │       │ │    │  │ (RF=3)  │ │       │ │        │
│  │  └─────────┘ └───────┘ │    │  └─────────┘ └───────┘ │        │
│  │                         │    │                         │        │
│  │  ┌─────────┐ ┌───────┐ │    │  ┌─────────┐ ┌───────┐ │        │
│  │  │ Redis   │ │ Kafka │ │    │  │ Redis   │ │ Kafka │ │        │
│  │  │ Cluster │ │Cluster│ │◀──▶│  │ Cluster │ │Mirror │ │        │
│  │  └─────────┘ └───────┘ │    │  └─────────┘ └───────┘ │        │
│  └─────────────────────────┘    └─────────────────────────┘        │
│              ▲                             ▲                        │
│              │     Async Replication       │                        │
│              └─────────────────────────────┘                        │
│                                                                     │
│  ┌─────────────────────────┐    ┌─────────────────────────┐        │
│  │      EU-West            │    │      AP-Southeast       │        │
│  │                         │    │                         │        │
│  │  (Same topology as      │    │  (Same topology as      │        │
│  │   US regions)           │    │   US regions)           │        │
│  └─────────────────────────┘    └─────────────────────────┘        │
│                                                                     │
│  Inter-region replication lag: 50-200ms (acceptable)                │
│  Users always connect to nearest region                             │
│  Cross-region messages: sender writes local, async replication      │
│  to recipient's region                                              │
└────────────────────────────────────────────────────────────────────┘
```

### 11.2 Consistency Model per Data Type

```
┌──────────────────┬────────────────────┬──────────────────────────────┐
│ Data Type        │ Consistency Level   │ Rationale                    │
├──────────────────┼────────────────────┼──────────────────────────────┤
│ Messages         │ Causal consistency  │ Messages must appear in      │
│                  │ within conversation │ correct order within a chat  │
│                  │                    │ but not across chats          │
├──────────────────┼────────────────────┼──────────────────────────────┤
│ Delivery status  │ Eventual           │ DELIVERED/READ receipts can  │
│                  │ consistency        │ have seconds-level lag        │
├──────────────────┼────────────────────┼──────────────────────────────┤
│ Presence         │ Eventual           │ 5-10 second lag acceptable;  │
│                  │ consistency        │ users tolerate "last seen"   │
│                  │                    │ being slightly stale          │
├──────────────────┼────────────────────┼──────────────────────────────┤
│ User profiles    │ Eventual           │ Name/avatar changes can take │
│                  │ consistency        │ minutes to propagate          │
├──────────────────┼────────────────────┼──────────────────────────────┤
│ Group membership │ Strong within DC,  │ Critical for message routing  │
│                  │ eventual across DC │ but brief staleness OK        │
├──────────────────┼────────────────────┼──────────────────────────────┤
│ User sessions    │ Strong per DC      │ Must be accurate for message  │
│                  │ (Redis)            │ routing; stale = missed msg   │
└──────────────────┴────────────────────┴──────────────────────────────┘
```

### 11.3 Cross-Region Message Delivery

```
Scenario: User A (US-East) sends message to User B (EU-West)

┌───────────┐       ┌────────────┐       ┌───────────┐       ┌───────────┐
│  User A   │       │  US-East   │       │  EU-West  │       │  User B   │
│  (US-East)│       │  Chat Svc  │       │  Chat Svc │       │ (EU-West) │
└─────┬─────┘       └─────┬──────┘       └─────┬─────┘       └─────┬─────┘
      │                   │                     │                   │
      │  1. Send msg      │                     │                   │
      │──────────────────▶│                     │                   │
      │                   │                     │                   │
      │                   │  2. Persist locally │                   │
      │                   │  (Cassandra US-East)│                   │
      │                   │                     │                   │
      │  3. ACK (SENT)    │                     │                   │
      │◀──────────────────│                     │                   │
      │                   │                     │                   │
      │                   │  4. Lookup User B   │                   │
      │                   │  session -> EU-West │                   │
      │                   │                     │                   │
      │                   │  5. Publish to      │                   │
      │                   │  cross-region Kafka │                   │
      │                   │────────────────────▶│                   │
      │                   │                     │                   │
      │                   │                     │  6. Deliver       │
      │                   │                     │─────────────────▶│
      │                   │                     │                   │
      │                   │                     │  7. ACK DELIVERED │
      │                   │                     │◀─────────────────│
      │                   │                     │                   │
      │  8. Delivery      │  Async replication  │                   │
      │  receipt          │◀────────────────────│                   │
      │◀──────────────────│                     │                   │

Latency: Steps 1-3 (~30ms local), Steps 4-7 (~150ms cross-region)
Total: ~180ms end-to-end for cross-region delivery
```

---

## 12. Fault Tolerance and Failure Handling

### 12.1 Failure Scenarios and Mitigations

```
┌──────────────────────────────────────────────────────────────────────────┐
│ Failure Scenario          │ Detection          │ Mitigation             │
├───────────────────────────┼────────────────────┼────────────────────────┤
│ WS Gateway crashes        │ Heartbeat timeout  │ Client auto-reconnects │
│                           │ (60s)              │ to different server via │
│                           │                    │ load balancer. Pending  │
│                           │                    │ messages delivered from  │
│                           │                    │ offline queue.           │
├───────────────────────────┼────────────────────┼────────────────────────┤
│ Chat Service instance     │ Health checks      │ Load balancer routes to │
│ goes down                 │ (5s interval)      │ healthy instances.      │
│                           │                    │ Kafka retains unprocessed│
│                           │                    │ messages.                │
├───────────────────────────┼────────────────────┼────────────────────────┤
│ Cassandra node failure    │ Gossip protocol    │ RF=3: other 2 replicas  │
│                           │                    │ serve reads/writes.     │
│                           │                    │ Hinted handoff on       │
│                           │                    │ recovery.               │
├───────────────────────────┼────────────────────┼────────────────────────┤
│ Redis shard failure       │ Sentinel / Cluster │ Automatic failover to  │
│                           │ monitoring         │ replica. Sessions       │
│                           │                    │ re-registered on next   │
│                           │                    │ heartbeat.              │
├───────────────────────────┼────────────────────┼────────────────────────┤
│ Kafka broker failure      │ ZooKeeper / KRaft  │ Partition leadership   │
│                           │                    │ transferred. ISR        │
│                           │                    │ replicas continue.      │
├───────────────────────────┼────────────────────┼────────────────────────┤
│ Entire DC failure         │ Cross-DC health    │ DNS failover to other  │
│                           │ monitoring         │ DC. Users reconnect.   │
│                           │                    │ Cassandra serves from   │
│                           │                    │ remaining DCs.          │
├───────────────────────────┼────────────────────┼────────────────────────┤
│ Network partition between │ Split-brain        │ Each DC continues       │
│ data centers              │ detection          │ independently. Messages │
│                           │                    │ reconciled after        │
│                           │                    │ partition heals via     │
│                           │                    │ Cassandra anti-entropy. │
└──────────────────────────────────────────────────────────────────────────┘
```

### 12.2 Client-Side Reliability

```
┌─────────────────────────────────────────────────────────────┐
│              Client Reconnection Protocol                    │
│                                                              │
│  1. Connection drops detected (no pong for 60s)              │
│  2. Client enters reconnection mode:                         │
│     - Attempt 1: immediate retry                             │
│     - Attempt 2: 1 second delay                              │
│     - Attempt 3: 2 seconds delay                             │
│     - Attempt 4: 4 seconds delay                             │
│     - ...                                                    │
│     - Max delay: 30 seconds (with jitter)                    │
│                                                              │
│  3. On reconnection:                                         │
│     - Re-authenticate with JWT                               │
│     - Send last_received_seq per conversation                │
│     - Server sends missed messages (gap fill)                │
│                                                              │
│  4. While disconnected:                                      │
│     - Messages queued locally (SQLite on device)             │
│     - Sent in order on reconnection                          │
│     - Each has client_msg_id for dedup                       │
│                                                              │
│  5. Idempotency guarantee:                                   │
│     - Client retries with same client_msg_id                 │
│     - Server deduplicates: if already processed,             │
│       returns cached ACK without re-processing               │
└─────────────────────────────────────────────────────────────┘
```

### 12.3 Message Delivery Guarantee

```
Guarantee: At-least-once delivery with client-side dedup

End-to-end flow with failure handling:

  Sender -> Server:
    ✓ Client retries until ACK received (at-least-once send)
    ✓ Server deduplicates via client_msg_id (exactly-once processing)

  Server -> Recipient:
    ✓ If online: push via WebSocket, wait for DELIVERED ACK
    ✓ If ACK not received: retry from Kafka consumer
    ✓ If offline: queue in pending_messages table
    ✓ On reconnection: deliver all pending messages
    ✓ Recipient deduplicates via server msg_id (exactly-once display)

  Failure during persist:
    ✓ Write to Cassandra with LOCAL_QUORUM
    ✓ If write fails: do NOT ACK to sender -> sender retries
    ✓ If ACK to sender fails after write: sender retries,
      server deduplicates and returns cached ACK

  Result: Messages are never lost (durability)
          Messages are never duplicated (dedup at both ends)
          Messages may be delivered out of order briefly
          (client reorders by sequence_number)
```

---

## 13. Scalability

### 13.1 Scaling Strategy per Component

```
┌──────────────────────────────────────────────────────────────────┐
│              Horizontal Scaling Plan                              │
│                                                                   │
│  Component          │ Current    │ 2x Scale   │ Scaling Method   │
│  ────────────────── │ ─────────  │ ──────────  │ ────────────── │
│  WS Gateways        │ 5,000      │ 10,000     │ Add servers,    │
│                     │            │            │ LB distributes  │
│                     │            │            │                  │
│  Chat Service       │ 500        │ 1,000      │ Stateless, add  │
│                     │            │            │ pods behind LB  │
│                     │            │            │                  │
│  Cassandra          │ 100 nodes  │ 200 nodes  │ Add nodes, auto │
│                     │ (12 racks) │            │ rebalance ring  │
│                     │            │            │                  │
│  MySQL (Vitess)     │ 256 shards │ 512 shards │ Vitess reshard  │
│                     │            │            │ (online)         │
│                     │            │            │                  │
│  Redis              │ 128 shards │ 256 shards │ Redis Cluster   │
│                     │            │            │ resharding       │
│                     │            │            │                  │
│  Kafka              │ 30 brokers │ 60 brokers │ Add brokers,    │
│                     │ 256 parts  │ 512 parts  │ rebalance parts  │
│                     │            │            │                  │
│  Push Notification  │ 50 workers │ 100 workers│ Add consumers   │
│                     │            │            │                  │
│  Media Service      │ 100 pods   │ 200 pods   │ Stateless,      │
│                     │            │            │ S3 scales auto   │
└──────────────────────────────────────────────────────────────────┘
```

### 13.2 Bottleneck Analysis

```
Bottleneck 1: WebSocket connections
  Problem:  500M concurrent connections need 5,000 servers
  Solution: Connection pooling, binary protocol, OS tuning
            (net.core.somaxconn, ulimit -n 1000000)
  Growth:   Linear scaling -- add servers as users grow

Bottleneck 2: Group message fan-out
  Problem:  Large group (256 members) = 256 Kafka messages per send
  Solution: Batch fan-out, Kafka partitioning by recipient
            Pre-compute fan-out list, cache in Redis

Bottleneck 3: Sequence number generation
  Problem:  Redis INCR for per-conversation seq is centralized
  Solution: Range pre-allocation (INCRBY 100)
            Local caching of ranges in Chat Service
            At 230K msg/sec, Redis handles this comfortably
            (Redis can do ~1M ops/sec per shard)

Bottleneck 4: Cross-region latency
  Problem:  User A in US, User B in EU = 150ms+ network latency
  Solution: Write locally, async replication
            Accept 150-200ms delivery latency for cross-region
            Local read for message history

Bottleneck 5: Media upload throughput
  Problem:  1B media uploads/day = ~12K uploads/sec
  Solution: Direct-to-S3 upload with pre-signed URLs
            Client uploads directly, bypassing our servers
            Server only stores the media reference
```

### 13.3 Connection Server Scaling Detail

```
┌──────────────────────────────────────────────────────────────────┐
│         Connection Server Auto-Scaling                           │
│                                                                   │
│  Scaling triggers:                                                │
│  - Connection count > 80K per server -> scale up                 │
│  - Connection count < 30K per server -> scale down               │
│  - CPU > 70% or Memory > 80% -> scale up                        │
│                                                                   │
│  Graceful scaling down:                                           │
│  1. Mark server as "draining" in service registry                │
│  2. Stop accepting new connections                               │
│  3. Wait for existing connections to naturally disconnect         │
│     (heartbeat timeout: 60 seconds)                              │
│  4. After 5 minutes: forcefully close remaining connections      │
│  5. Clients auto-reconnect to other servers                      │
│  6. Decommission server                                          │
│                                                                   │
│  Rolling deployment:                                              │
│  1. Deploy to 1% of servers (canary)                             │
│  2. Monitor error rates, latency for 15 minutes                  │
│  3. If healthy: roll to 10%, then 50%, then 100%                 │
│  4. If unhealthy: rollback canary, investigate                   │
│  5. Connections gracefully migrate during rollout                │
└──────────────────────────────────────────────────────────────────┘
```

---

## 14. Monitoring and Observability

### 14.1 Key Metrics Dashboard

```
┌──────────────────────────────────────────────────────────────────────┐
│                    Chat System Metrics Dashboard                      │
│                                                                       │
│  ┌─────────────────────────────────────────────────────────────┐     │
│  │  MESSAGE DELIVERY                                            │     │
│  │                                                              │     │
│  │  Delivery latency (p50/p95/p99): 30ms / 80ms / 150ms       │     │
│  │  Messages sent/sec:              230,000                     │     │
│  │  Messages delivered/sec:         1,400,000 (inc. fan-out)   │     │
│  │  Delivery success rate:          99.97%                      │     │
│  │  Pending message queue depth:    50,000                      │     │
│  │  Message dedup rate:             0.01%                       │     │
│  └─────────────────────────────────────────────────────────────┘     │
│                                                                       │
│  ┌─────────────────────────────────────────────────────────────┐     │
│  │  CONNECTIONS                                                  │     │
│  │                                                              │     │
│  │  Active WebSocket connections:   487,000,000                 │     │
│  │  Connection rate (new/sec):      50,000                      │     │
│  │  Disconnection rate (/sec):      48,000                      │     │
│  │  Avg connection duration:        45 minutes                  │     │
│  │  Connection errors/sec:          200                         │     │
│  │  Servers at > 80% capacity:      12 / 5,000                 │     │
│  └─────────────────────────────────────────────────────────────┘     │
│                                                                       │
│  ┌─────────────────────────────────────────────────────────────┐     │
│  │  INFRASTRUCTURE                                               │     │
│  │                                                              │     │
│  │  Kafka consumer lag:             2,000 msgs (< 1 second)    │     │
│  │  Cassandra write latency (p99):  15ms                       │     │
│  │  Cassandra read latency (p99):   8ms                        │     │
│  │  Redis memory usage:             480 GB / 1 TB              │     │
│  │  Redis hit rate:                 99.2%                       │     │
│  │  Push notification success:      98.5%                       │     │
│  └─────────────────────────────────────────────────────────────┘     │
│                                                                       │
│  ALERTS:                                                              │
│  ┌─────────────────────────────────────────────────────────────┐     │
│  │  P1: Delivery latency p99 > 500ms                           │     │
│  │  P1: Delivery success rate < 99.9%                          │     │
│  │  P1: Kafka consumer lag > 100K messages                     │     │
│  │  P2: WS connection errors > 1000/sec                        │     │
│  │  P2: Cassandra write latency p99 > 50ms                     │     │
│  │  P3: Push notification failure > 5%                         │     │
│  │  P3: Redis memory > 80%                                     │     │
│  └─────────────────────────────────────────────────────────────┘     │
└──────────────────────────────────────────────────────────────────────┘
```

### 14.2 Distributed Tracing

```
Trace: Send Message (end-to-end)

  TraceID: abc-123-def-456

  ┌─ Client: sendMessage                                    [0ms]
  │  ├─ WS Gateway: receiveFrame                            [2ms]
  │  │  ├─ Auth: validateToken                              [1ms]
  │  │  └─ Forward: toChatService (gRPC)                    [3ms]
  │  │     ├─ ChatService: dedup check (Redis)              [1ms]
  │  │     ├─ ChatService: assignSeqNum (Redis INCR)        [1ms]
  │  │     ├─ ChatService: persist (Cassandra)              [8ms]
  │  │     ├─ ChatService: ACK to sender                    [1ms] ← SENT
  │  │     ├─ ChatService: lookupSession (Redis)            [1ms]
  │  │     ├─ ChatService: route to WS Gateway B (gRPC)     [5ms]
  │  │     │  └─ WS Gateway B: pushToClient                 [2ms]
  │  │     │     └─ Client B: ACK (DELIVERED)               [3ms]
  │  │     └─ ChatService: update delivery status            [2ms]
  │  └─ Total: 28ms (same region)
  │
  │  Spans breakdown:
  │    Network hops:     4 x 2ms = 8ms
  │    Redis operations: 3 x 1ms = 3ms
  │    Cassandra write:  1 x 8ms = 8ms
  │    Processing:       ~9ms
  └─ Total:              ~28ms (p50 target: 30ms) ✓
```

### 14.3 Health Check Strategy

```
Component health checks:

WS Gateway:
  - /health/live   -> process is running (Kubernetes liveness)
  - /health/ready  -> can accept connections (readiness)
  - /health/deep   -> Redis connectivity, can register sessions

Chat Service:
  - /health/live   -> process running
  - /health/ready  -> Kafka producer connected, Cassandra reachable
  - Dependency check: Redis, Cassandra, Kafka all reachable

Presence Service:
  - /health/live   -> process running
  - /health/ready  -> Redis cluster connected

Circuit Breaker Pattern:
  - Each service wraps downstream calls in circuit breakers
  - Thresholds: 50% failure rate over 30-second window
  - Open state: fail fast, return cached/default response
  - Half-open: allow 10% traffic to probe recovery
  - Closed: normal operation
```

---

## 15. Trade-offs and Design Decisions

### 15.1 Push vs Pull for Message Delivery

```
┌──────────────────────────────────────────────────────────────────┐
│                                                                   │
│  PUSH Model (chosen):                                            │
│  ┌────────┐  WebSocket  ┌────────┐                               │
│  │ Server │────────────▶│ Client │                               │
│  └────────┘             └────────┘                               │
│  + Real-time delivery (< 100ms)                                  │
│  + No unnecessary network requests                               │
│  + Server controls delivery rate                                 │
│  - Requires persistent connections (resource-intensive)          │
│  - Complex connection management at scale                        │
│                                                                   │
│  PULL Model (rejected):                                          │
│  ┌────────┐  HTTP poll  ┌────────┐                               │
│  │ Client │────────────▶│ Server │                               │
│  └────────┘             └────────┘                               │
│  + Simpler server architecture                                   │
│  + Stateless servers                                             │
│  - High latency (polling interval)                               │
│  - Wasted bandwidth (empty polls)                                │
│  - At 500M users polling every 1s = 500M req/sec (unsustainable) │
│                                                                   │
│  HYBRID (what we actually do):                                   │
│  - Push via WebSocket when user is online (primary)              │
│  - Pull via REST when loading message history (on-demand)        │
│  - Push notification (APNs/FCM) when user is offline             │
│                                                                   │
│  Decision: Push for real-time, Pull for historical data          │
└──────────────────────────────────────────────────────────────────┘
```

### 15.2 WebSocket vs Long Polling vs SSE

```
┌─────────────┬──────────────┬──────────────┬──────────────┐
│ Criterion   │ WebSocket    │ Long Polling │ SSE          │
├─────────────┼──────────────┼──────────────┼──────────────┤
│ Latency     │ ~1ms         │ ~100ms       │ ~1ms         │
│ Direction   │ Bidirectional│ Client->Srvr │ Server->Clnt │
│ Overhead    │ 2B per frame │ HTTP headers │ HTTP headers │
│ Connections │ Persistent   │ Repeated     │ Persistent   │
│ Mobile      │ Good (w/     │ Battery-     │ One-way only │
│ battery     │ heartbeat)   │ intensive    │              │
│ Proxy/FW    │ Some issues  │ Works always │ Works mostly │
│ Binary data │ Yes          │ Yes          │ No (text)    │
├─────────────┼──────────────┼──────────────┼──────────────┤
│ Verdict     │ CHOSEN ✓     │ Fallback     │ Not suitable │
└─────────────┴──────────────┴──────────────┴──────────────┘

Decision: WebSocket primary with long-polling fallback for
restrictive network environments (corporate proxies).
```

### 15.3 Cassandra vs HBase vs MongoDB

```
┌─────────────────┬──────────────┬──────────────┬──────────────┐
│ Criterion       │ Cassandra    │ HBase        │ MongoDB      │
├─────────────────┼──────────────┼──────────────┼──────────────┤
│ Write perf      │ Excellent    │ Good         │ Good         │
│ Read perf       │ Good (by PK) │ Good (by RK) │ Flexible     │
│ Scalability     │ Linear       │ Linear       │ Complex      │
│ Multi-DC        │ Native       │ Complex      │ Supported    │
│ Consistency     │ Tunable      │ Strong (row) │ Tunable      │
│ Operations      │ Simple       │ Complex (HDP)│ Moderate     │
│ Schema flex     │ Limited      │ Limited      │ Flexible     │
│ Time-series     │ Excellent    │ Good         │ Moderate     │
│ Compaction      │ TWCS ideal   │ Manual       │ WiredTiger   │
├─────────────────┼──────────────┼──────────────┼──────────────┤
│ Verdict         │ CHOSEN ✓     │ Viable alt   │ Not ideal    │
└─────────────────┴──────────────┴──────────────┴──────────────┘

Decision: Cassandra for its native multi-DC replication,
tunable consistency, and excellent write throughput.
Write path is critical -- 230K messages/sec sustained.
```

### 15.4 End-to-End Encryption Trade-offs

```
┌─────────────────────────────────────────────────────────────────┐
│                 E2E Encryption (Signal Protocol)                 │
│                                                                  │
│  How it works (simplified):                                      │
│  1. Each user generates identity key pair (Curve25519)           │
│  2. Key exchange via server (public keys only)                   │
│  3. Derive shared secret using Double Ratchet Algorithm          │
│  4. Each message encrypted with unique key (forward secrecy)     │
│  5. Server stores only encrypted blobs, cannot decrypt           │
│                                                                  │
│  Trade-offs:                                                     │
│  ┌────────────────────┬──────────────────────────────┐           │
│  │ Benefit            │ Cost                          │           │
│  ├────────────────────┼──────────────────────────────┤           │
│  │ Privacy: server    │ No server-side search         │           │
│  │ cannot read msgs   │ (search must be client-side)  │           │
│  ├────────────────────┼──────────────────────────────┤           │
│  │ Security: even if  │ Complex key management        │           │
│  │ DB breached, msgs  │ (key exchange, rotation)      │           │
│  │ are unreadable     │                               │           │
│  ├────────────────────┼──────────────────────────────┤           │
│  │ Forward secrecy:   │ Multi-device sync is harder   │           │
│  │ past msgs safe if  │ (each device has own keys)    │           │
│  │ key compromised    │                               │           │
│  ├────────────────────┼──────────────────────────────┤           │
│  │ Regulatory         │ Cannot comply with lawful     │           │
│  │ compliance         │ interception (by design)      │           │
│  └────────────────────┴──────────────────────────────┘           │
│                                                                  │
│  Group E2E encryption:                                           │
│  - Sender encrypts message once with group key                   │
│  - Group key rotated when members join/leave                     │
│  - Pairwise keys for 256 members = key management overhead       │
│  - Alternative: Sender Key protocol (one encrypt, all decrypt)   │
│                                                                  │
│  Decision: Implement E2E for 1-on-1 (mandatory),                │
│  optional for groups (performance vs security trade-off)         │
└─────────────────────────────────────────────────────────────────┘
```

### 15.5 Message Storage: Store Per-Conversation vs Per-User

```
Option A: Per-Conversation (chosen)
  Partition key: conversation_id
  + Group messages stored once (not per-member)
  + Efficient conversation scroll-back
  + Natural data locality
  - Cross-conversation queries (search) require secondary index

Option B: Per-User Inbox
  Partition key: user_id
  + All user's messages in one partition
  + Easy "all conversations" listing
  - Group messages duplicated per member (256x for large group)
  - Hot partition for active users
  - Massive storage amplification

Decision: Per-conversation storage with a separate
user_conversations table for the conversation list.
```

---

## 16. Interview Deep-Dive Questions

### Q1: How do you handle message ordering in group chats?

**Answer:** We use a per-conversation monotonic sequence counter stored in Redis.
When a message arrives for a group, the Chat Service atomically increments the
counter (`INCR group:seq:{group_id}`) and assigns the resulting sequence number
to the message. Since all messages for a group are routed through the same Kafka
partition (keyed by `group_id`), we get total ordering within the partition.

On the client side, messages are displayed sorted by `sequence_number`. If the
client detects a gap (e.g., receives seq 42 but last seen was 40), it requests
the missing message (seq 41) from the server before displaying seq 42. This
handles out-of-order delivery while maintaining causal consistency.

For very high-throughput groups, we can pre-allocate sequence ranges
(`INCRBY 100`) to reduce Redis round-trips, though this creates non-contiguous
sequences that the client must handle gracefully.

---

### Q2: How does end-to-end encryption work in this system?

**Answer:** We implement the Signal Protocol (Double Ratchet Algorithm):

1. **Key Generation:** Each user generates an identity key pair (Curve25519), a
   signed pre-key, and a set of one-time pre-keys. Public keys are uploaded to
   the server.

2. **Key Exchange:** When User A wants to message User B for the first time, A
   fetches B's public keys from the server and performs an X3DH (Extended Triple
   Diffie-Hellman) key agreement to establish a shared secret.

3. **Message Encryption:** Each message is encrypted with a unique symmetric key
   derived from the Double Ratchet. The ratchet advances with each message,
   providing forward secrecy (compromising the current key does not reveal past
   messages).

4. **Server Role:** The server only stores encrypted ciphertext. It cannot
   decrypt messages. It acts as a relay and key distribution service (for public
   keys only).

5. **Group Encryption:** Uses the Sender Key protocol. The sender generates a
   Sender Key, distributes it to all group members (encrypted with pairwise
   keys), then encrypts the message once with the Sender Key. All members can
   decrypt. When a member leaves, the Sender Key is rotated.

---

### Q3: How do you sync messages across multiple devices?

**Answer:** Multi-device sync requires careful handling:

1. **Session Registry:** Each device maintains its own WebSocket connection.
   Redis tracks all active sessions: `HSET user:sessions:{uid} {device_id} ->
   {server_id, conn_id}`.

2. **Fan-out to All Devices:** When a message arrives for a user, the Chat
   Service looks up all active sessions and delivers to each device.

3. **Sync Protocol:** Each device tracks its `last_synced_seq` per conversation.
   On reconnection, the device sends its sync state, and the server sends only
   messages with `seq > last_synced_seq`.

4. **Conflict Resolution:** If a user reads a message on Device A, the read
   receipt is propagated to Device B. We use "latest writer wins" for
   conflicting actions (e.g., muting a conversation on two devices
   simultaneously).

5. **E2E Encryption Complication:** Each device has its own encryption keys.
   Messages must be encrypted separately for each device. We use the
   multi-device Signal Protocol, where each device is treated as a separate
   recipient.

---

### Q4: What happens when a user comes back online after being offline for days?

**Answer:** We handle this through a staged sync process:

1. **Pending Queue:** While offline, messages are stored in the `pending_messages`
   table in Cassandra, keyed by `(recipient_id, created_at)`.

2. **Reconnection Sync:** When the user reconnects:
   - The client sends its `last_received_seq` per conversation.
   - The server queries `pending_messages` for the user.
   - Messages are delivered in batches of 100, oldest first.
   - Each batch is ACKed before the next is sent.

3. **Large Backlog:** If the user has been offline for days, there might be
   thousands of pending messages. We prioritize:
   - First: conversation list with unread counts (fast UI rendering).
   - Then: messages from recent conversations first.
   - Background: older conversations load on-demand.

4. **Storage Limits:** Pending messages are retained for 30 days. Beyond that,
   the client fetches from the permanent message store (Cassandra) when the user
   scrolls back.

5. **Push Notifications:** While offline, the user received push notifications
   (batched to avoid notification spam). On reconnect, push delivery is
   suppressed in favor of WebSocket delivery.

---

### Q5: How do you handle message deletion for everyone?

**Answer:**

1. **Soft Delete:** We do not physically delete the message immediately. Instead,
   we set a `deleted_at` timestamp and a `deleted_for` field (ALL or specific
   user_ids).

2. **Deletion Message:** A "delete" control message is sent to all conversation
   participants via the normal message delivery pipeline. This message contains
   the `msg_id` to delete and the deletion type.

3. **Time Window:** WhatsApp allows "Delete for Everyone" only within a window
   (e.g., 1 hour 8 minutes after sending). We enforce this server-side.

4. **Client Handling:** Recipients' clients receive the delete event and remove
   the message from local display, replacing it with "This message was deleted."

5. **Consistency:** If a recipient is offline when the delete is issued, the
   delete event is queued. When they come online, they receive the delete event
   and remove the message from their local store. There is a window where the
   recipient might have already read and cached the message locally.

6. **Media Cleanup:** If the deleted message had media, the media file is
   scheduled for deletion from S3 (with a grace period for CDN cache
   expiration).

---

### Q6: How do you handle the "thundering herd" problem when a popular user comes online?

**Answer:** A celebrity with millions of followers coming online could trigger
millions of presence update fan-outs. We mitigate this:

1. **Subscription-Based Presence:** Only users who have the chat window open
   subscribe to another user's presence. This reduces fan-out from "all
   contacts" to "users actively viewing the chat" (typically < 10).

2. **Presence Coalescing:** If a user toggles online/offline rapidly (flaky
   connection), we debounce presence updates with a 5-second window. Only the
   final state is broadcast.

3. **Lazy Presence:** For the conversation list view, presence is fetched
   on-demand (pull model) rather than pushed. The client requests presence for
   visible conversations only.

4. **Rate Limiting:** Cap presence fan-out at 1,000 recipients per second. If a
   user has more subscribers, updates are spread over multiple seconds.

---

### Q7: How do you ensure exactly-once message delivery?

**Answer:** We achieve exactly-once semantics through at-least-once delivery
combined with idempotency:

1. **Sender Side:** The client generates a `client_msg_id` (UUID v4) for each
   message. If the server ACK is not received within 5 seconds, the client
   retries with the same `client_msg_id`.

2. **Server Dedup:** The Chat Service maintains a dedup cache in Redis:
   `SET dedup:{client_msg_id} -> server_msg_id EX 3600`. If a duplicate arrives,
   the server returns the cached ACK without re-processing.

3. **Recipient Side:** The server assigns a globally unique `server_msg_id`
   (Snowflake ID). The recipient client deduplicates incoming messages by
   `server_msg_id`. This handles the case where the server delivered the
   message but the recipient's ACK was lost, causing the server to retry.

4. **Idempotent Persistence:** Cassandra writes are naturally idempotent (same
   primary key overwrites). Writing the same message twice is a no-op.

---

### Q8: How would you implement message search?

**Answer:**

1. **Architecture:** Message content is indexed asynchronously via Kafka into
   Elasticsearch. The search index is separate from the message store.

2. **Index Design:** Documents are indexed per-message with fields: `user_id`,
   `conversation_id`, `content_text`, `sender_name`, `timestamp`. The index is
   sharded by `user_id` so each user's search is a single-shard query.

3. **E2E Encryption Challenge:** With E2E encryption, the server cannot index
   message content. Two approaches:
   - **Client-side search:** Search is performed locally on the device using a
     local index (SQLite FTS). This works for recent messages.
   - **Encrypted search index:** The client builds an encrypted search index
     and uploads it. The server can perform token-based search without seeing
     plaintext. This is complex and has limitations.

4. **Performance:** Elasticsearch returns message IDs. Full message content is
   fetched from Cassandra. Results are paginated (20 per page) and sorted by
   relevance/recency.

---

### Q9: How do you handle rate limiting and abuse prevention?

**Answer:**

1. **Per-User Rate Limits:**
   - Messages: 100 messages per minute per user.
   - Group creation: 10 groups per day.
   - Media upload: 50 files per hour.

2. **Implementation:** Token bucket algorithm in Redis.
   `DECR ratelimit:{user_id}:msg` with TTL reset.

3. **Spam Detection:** ML model scores messages based on:
   - Send rate pattern (burst detection).
   - Number of unique recipients in short window.
   - Message content similarity (duplicate messages).
   - Account age and verification status.

4. **Abuse Actions:** Graduated response: warning, temporary mute (1 hour),
   temporary ban (24 hours), permanent ban.

---

### Q10: How do you handle schema evolution and backward compatibility?

**Answer:**

1. **Protocol Buffers:** All wire formats use protobuf, which supports backward-
   compatible schema evolution (new fields have defaults, old clients ignore
   unknown fields).

2. **API Versioning:** REST APIs are versioned (`/api/v1/`, `/api/v2/`). Old
   versions are supported for at least 2 years.

3. **Cassandra Schema:** New columns are added (not removed or renamed).
   Cassandra supports adding columns without downtime. Data migration is handled
   via dual-write during transition periods.

4. **Feature Flags:** New features are gated behind feature flags. Clients
   advertise their capabilities during WebSocket handshake, and the server
   adapts its behavior accordingly.

---

### Q11: How do you handle typing indicators efficiently?

**Answer:**

1. **Ephemeral Messages:** Typing indicators are NOT persisted. They are
   fire-and-forget via WebSocket.

2. **Throttling:** The client sends "typing" events at most once every 3 seconds.
   The event has a 5-second implicit TTL (if no new typing event, UI shows
   "stopped typing").

3. **Fan-out:** For 1-on-1 chats, it is a single message to the recipient. For
   groups, it fans out only to members who currently have the chat open
   (determined by presence subscription).

4. **No Reliability Needed:** If a typing indicator is lost, the impact is
   negligible. No retries, no persistence, no ACKs.

---

### Q12: How do you implement read receipts for group chats?

**Answer:**

1. **Per-User Tracking:** Each user's read position is tracked via
   `last_read_seq` in the `user_conversations` table.

2. **Aggregation:** For a group message, the sender sees "delivered to 15/20
   members, read by 10/20 members." This is computed by aggregating
   `last_read_seq` across all group members.

3. **Optimization:** We do not push individual read receipts for every member in
   a group. Instead, the read count is fetched on-demand when the sender views
   the message info screen.

4. **Privacy:** Some users disable read receipts. The server respects the
   `read_receipts_enabled` flag per user and omits them from the count.

---

### Q13: How would you handle message reactions (emoji reactions)?

**Answer:**

1. **Data Model:** Reactions are stored as a separate table:
   `reactions(message_id, user_id, emoji, timestamp)`.

2. **Delivery:** Reactions are sent as control messages via the same delivery
   pipeline. They reference the original `message_id`.

3. **Aggregation:** The client displays aggregated reactions (e.g., "5 people
   reacted with thumbs-up"). The aggregation can be computed client-side from
   the reaction events.

4. **Removal:** Users can remove their reaction. A "remove reaction" event is
   sent and processed the same way.

5. **Scale:** Reactions add relatively low traffic compared to messages. A
   popular message might get 256 reactions in a group (one per member), which
   is manageable.

---

### Q14: How do you design the notification batching system?

**Answer:**

1. **Problem:** A user in 50 active groups might receive hundreds of
   notifications while offline, which is overwhelming.

2. **Batching Logic:**
   - First message in a conversation: immediate notification.
   - Subsequent messages within 30 seconds: batch into "5 new messages in
     Engineering Group."
   - If more than 5 conversations have unread messages: collapse into "You
     have messages in 5 conversations."

3. **Implementation:** The Push Notification Service maintains a per-user
   notification buffer in Redis with a 30-second flush window. When the timer
   fires, it sends the batched notification.

4. **Priority:** Direct messages have higher priority than group messages.
   Mentions ("@user") in groups are treated as high-priority.

5. **Muting:** Muted conversations do not generate push notifications, but
   unread counts still update (visible when the user opens the app).

---

### Q15: How would you migrate from a monolithic chat system to this microservices architecture?

**Answer:**

1. **Strangler Fig Pattern:** Gradually route traffic from monolith to
   microservices, one feature at a time.

2. **Migration Order:**
   - Phase 1: Extract Media Service (lowest risk, independent).
   - Phase 2: Extract Push Notification Service.
   - Phase 3: Extract Presence Service.
   - Phase 4: Extract Group Service.
   - Phase 5: Migrate message storage from MySQL to Cassandra (dual-write).
   - Phase 6: Extract Chat Service and WebSocket Gateway.

3. **Dual-Write:** During migration, write to both old and new systems. Read
   from old system. Verify consistency. Switch reads to new system. Stop
   writing to old system.

4. **Feature Flags:** Each migration phase is gated behind feature flags.
   Roll out to 1% of users, validate, then expand.

5. **Rollback Plan:** Each phase has a rollback procedure. The old system
   remains operational until the new system is validated at full scale.

---

## 17. End-to-End Message Flow Summary

```
┌──────────────────────────────────────────────────────────────────────────┐
│                   Complete Message Lifecycle                              │
│                                                                          │
│   1. COMPOSE                                                             │
│   ┌──────────┐                                                           │
│   │  User A  │  Types message, client encrypts with E2E key             │
│   │  Client  │  Generates client_msg_id (UUID)                          │
│   └────┬─────┘                                                           │
│        │ WebSocket                                                       │
│   2. TRANSMIT                                                            │
│   ┌────▼─────┐                                                           │
│   │  WS GW   │  Validates auth, forwards to Chat Service                │
│   │ Server A │  via gRPC                                                │
│   └────┬─────┘                                                           │
│        │ gRPC                                                            │
│   3. PROCESS                                                             │
│   ┌────▼─────┐                                                           │
│   │  Chat    │  Dedup check (Redis) ──▶ Assign seq_num (Redis)          │
│   │ Service  │  Persist to Cassandra ──▶ ACK SENT to sender             │
│   └────┬─────┘                                                           │
│        │                                                                 │
│   4. ROUTE                                                               │
│   ┌────▼─────┐                                                           │
│   │  Redis   │  Lookup recipient session                                │
│   │ (Session)│  -> server_id: "ws-server-B"                             │
│   └────┬─────┘                                                           │
│        │                                                                 │
│   5a. DELIVER (online)          5b. QUEUE (offline)                      │
│   ┌────▼─────┐                  ┌──────────────┐                         │
│   │  WS GW   │                  │  Cassandra   │  pending_messages       │
│   │ Server B │                  │              │                         │
│   └────┬─────┘                  └──────┬───────┘                         │
│        │ WebSocket                     │                                 │
│   ┌────▼─────┐                  ┌──────▼───────┐                         │
│   │  User B  │                  │  Push Notif  │  APNs / FCM            │
│   │  Client  │                  │   Service    │                         │
│   └────┬─────┘                  └──────────────┘                         │
│        │                                                                 │
│   6. ACKNOWLEDGE                                                         │
│        │  ACK DELIVERED ──▶ Chat Service ──▶ Update status              │
│        │  ──▶ Notify sender (delivery receipt)                          │
│        │                                                                 │
│   7. READ                                                                │
│        │  User B reads message ──▶ READ_RECEIPT                         │
│        │  ──▶ Chat Service ──▶ Update last_read_seq                     │
│        │  ──▶ Notify sender (read receipt)                              │
│        │                                                                 │
│   Total latency (same region, both online): ~30ms                       │
│   Total latency (cross-region, both online): ~180ms                     │
│   Offline delivery: < 2 seconds after reconnection                      │
└──────────────────────────────────────────────────────────────────────────┘
```

---

## 18. Quick Reference: Interview Checklist

```
┌──────────────────────────────────────────────────────────────────┐
│              45-Minute Interview Time Allocation                  │
│                                                                   │
│  [0-5 min]   Requirements & scope clarification                  │
│              - Clarify: 1-on-1 vs group, scale, E2E encryption  │
│              - State assumptions: 500M DAU, 40 msgs/day          │
│                                                                   │
│  [5-10 min]  Back-of-envelope estimation                         │
│              - 230K msg/sec, 20TB/day, 500M WS connections       │
│              - Identify key bottlenecks early                    │
│                                                                   │
│  [10-15 min] API design (WebSocket + REST)                       │
│              - Show WebSocket protocol for real-time              │
│              - REST for history, groups, media                    │
│                                                                   │
│  [15-25 min] High-level architecture                             │
│              - Draw the architecture diagram                     │
│              - Explain each component's role                     │
│              - Message flow: send -> process -> deliver          │
│                                                                   │
│  [25-40 min] Deep dives (interviewer's choice)                   │
│              - Message ordering and delivery guarantees          │
│              - WebSocket connection management                   │
│              - Group messaging fan-out                            │
│              - Presence service optimization                     │
│              - E2E encryption                                     │
│                                                                   │
│  [40-45 min] Scalability and trade-offs                          │
│              - How each component scales horizontally            │
│              - Key trade-offs: push vs pull, consistency model   │
│              - Monitoring and failure handling                    │
└──────────────────────────────────────────────────────────────────┘
```

---

## 19. References and Further Reading

- **WhatsApp Architecture:** "The WhatsApp Architecture Facebook Bought For $19 Billion"
  (High Scalability blog)
- **Signal Protocol:** Double Ratchet Algorithm specification
  (signal.org/docs)
- **Facebook Messenger:** "Building Mobile-First Infrastructure for Messenger"
  (Engineering at Meta blog)
- **Cassandra at Discord:** "How Discord Stores Trillions of Messages"
  (Discord Engineering blog)
- **Apache Kafka:** "Kafka: a Distributed Messaging System for Log Processing"
  (LinkedIn Engineering)
- **Consistent Hashing:** Karger et al., "Consistent Hashing and Random Trees"
