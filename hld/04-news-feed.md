# Design a News Feed System (Twitter / Facebook)

**Difficulty:** Hard | **Companies:** Meta, Twitter/X, Google, LinkedIn, Pinterest, ByteDance

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

### What is a News Feed?

A **news feed** is a continuously updating list of stories in the middle of a social
network's homepage. It includes status updates, photos, videos, links, app activity,
and "likes" from people, pages, and groups that a user follows or is connected to.

The core challenge: given hundreds of millions of users who each follow hundreds or
thousands of accounts, generate a personalized, ranked, real-time feed for every single
user -- and do it in under 200 milliseconds.

### Scope Definition

```
┌───────────────────────────────────────────────────────────────────────┐
│                        SYSTEM SCOPE                                   │
├───────────────────┬───────────────────────────────────────────────────┤
│   IN SCOPE        │   OUT OF SCOPE                                   │
├───────────────────┼───────────────────────────────────────────────────┤
│ Post creation     │ Ads insertion (separate system)                   │
│ Feed generation   │ Content moderation (separate pipeline)           │
│ Feed ranking      │ Full-text search                                  │
│ Follow/unfollow   │ Direct messaging                                  │
│ Like/comment      │ Stories/reels (ephemeral content)                 │
│ Real-time updates │ Marketplace/shopping                              │
│ Media handling    │ Video streaming infrastructure                    │
│ Pagination        │ User authentication (assume handled)             │
│ Trending/hashtags │ Recommendation engine (mention briefly)          │
└───────────────────┴───────────────────────────────────────────────────┘
```

### Key Actors

| Actor             | Description                                          |
|-------------------|------------------------------------------------------|
| **Content Creator**   | Creates posts (text, images, video)              |
| **Content Consumer**  | Views the news feed, scrolls, interacts          |
| **Celebrity/Influencer** | Has millions of followers (special handling)  |
| **System (Internal)** | Fan-out workers, ranking pipelines, caches       |

---

## 2. Functional Requirements

### Core Features

| ID   | Requirement                    | Description                                                              |
|------|--------------------------------|--------------------------------------------------------------------------|
| FR-1 | **Post Creation**              | Users can create posts with text (up to 10K chars), images, and videos  |
| FR-2 | **News Feed Generation**       | Generate a personalized feed from posts by followed users                |
| FR-3 | **Follow / Unfollow**          | Users can follow/unfollow other users; asymmetric relationship           |
| FR-4 | **Like / Comment / Share**     | Users can interact with posts; interactions influence ranking             |
| FR-5 | **Real-time Feed Updates**     | New posts from followed users appear in the feed with minimal delay      |
| FR-6 | **Feed Ranking**               | Posts are ranked by relevance, not just chronological order               |
| FR-7 | **Pagination**                 | Cursor-based infinite scroll with consistent ordering                    |
| FR-8 | **Hashtags / Trending**        | Aggregate trending topics from recent posts                              |
| FR-9 | **Media Support**              | Support images (JPEG, PNG, WebP) and videos (MP4) with transcoding       |
| FR-10| **Notifications**              | Notify users of new interactions on their posts                          |

### User Flows

```
┌──────────────────────────────────────────────────────────────────────────┐
│                        POST CREATION FLOW                                │
│                                                                          │
│   User ──► Compose Post ──► Attach Media ──► Submit                     │
│                                                    │                     │
│                                                    ▼                     │
│                                              Validate Post               │
│                                                    │                     │
│                                          ┌─────────┴──────────┐         │
│                                          │                    │         │
│                                          ▼                    ▼         │
│                                    Store Post          Upload Media     │
│                                          │                    │         │
│                                          ▼                    ▼         │
│                                    Fan-out to           Transcode &     │
│                                    Followers            Store in CDN    │
│                                          │                    │         │
│                                          └─────────┬──────────┘         │
│                                                    ▼                     │
│                                          Feed Updated for               │
│                                          All Followers                   │
└──────────────────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────────────────┐
│                        FEED RETRIEVAL FLOW                               │
│                                                                          │
│   User ──► Open App ──► Request Feed                                    │
│                              │                                           │
│                              ▼                                           │
│                    Check Pre-computed Feed Cache                         │
│                              │                                           │
│                    ┌─────────┴──────────┐                                │
│                    │ Cache Hit          │ Cache Miss                     │
│                    ▼                    ▼                                 │
│              Read from            Fetch Followed Users                   │
│              Redis Sorted Set     Fetch Their Recent Posts               │
│                    │              Merge & Rank                            │
│                    │                    │                                 │
│                    └─────────┬──────────┘                                │
│                              ▼                                           │
│                    Apply Ranking Model                                   │
│                              │                                           │
│                              ▼                                           │
│                    Paginate & Return                                     │
│                    (cursor-based)                                         │
└──────────────────────────────────────────────────────────────────────────┘
```

---

## 3. Non-Functional Requirements

| Requirement          | Target                | Rationale                                           |
|----------------------|-----------------------|-----------------------------------------------------|
| **Latency**          | Feed generation <200ms| Users expect instant feed loading                   |
| **Availability**     | 99.99% uptime         | Core engagement feature; downtime = revenue loss    |
| **Consistency**      | Eventual (seconds)    | Feed does not need strong consistency               |
| **Throughput**       | ~6K feed reads/sec    | Based on 500M DAU estimation                        |
| **Durability**       | No data loss for posts| Posts are user-generated content; must persist       |
| **Scalability**      | Handle 500M DAU       | Must scale horizontally                             |
| **Global Reach**     | Multi-region           | Users are worldwide; CDN for media                  |
| **Fan-out Handling** | Celebrity w/ 100M followers | Must not block on massive fan-out             |

### Consistency vs Availability Trade-off

```
┌─────────────────────────────────────────────────────────────────────┐
│                   CONSISTENCY SPECTRUM                               │
│                                                                     │
│   Strong ◄──────────────────────────────────────────► Eventual      │
│                                                                     │
│   Post writes          Feed generation          Feed reads          │
│   ┌──────────┐         ┌──────────────┐         ┌──────────┐      │
│   │ Lineariz │         │  Bounded     │         │ Eventual │      │
│   │ -able    │         │  Staleness   │         │          │      │
│   └──────────┘         └──────────────┘         └──────────┘      │
│   (my post must        (feed may lag            (seeing a post    │
│    appear when I        by a few secs)           1-2s late is     │
│    refresh)                                      acceptable)      │
│                                                                     │
│   CAP choice: AP system (Availability + Partition tolerance)       │
│   Accept eventual consistency for higher availability              │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 4. Back-of-Envelope Estimation

### User and Traffic Assumptions

| Metric                        | Value             | Derivation                                |
|-------------------------------|-------------------|-------------------------------------------|
| Total registered users        | 2 billion         | Given                                     |
| Daily Active Users (DAU)      | 500 million       | ~25% of total                             |
| Avg posts per user per day    | 2                 | Most users post less, power users more    |
| Total posts per day           | 1 billion         | 500M x 2                                  |
| Avg followers per user        | 300               | Power-law distribution                    |
| Feed refreshes per user/day   | 10                | Open app ~10 times                        |
| Avg feed page size            | 20 posts          | Per page/scroll                           |

### QPS Calculations

```
┌─────────────────────────────────────────────────────────────────────┐
│                        QPS ESTIMATION                               │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  Post Creation:                                                     │
│    1B posts/day ÷ 86,400 sec = ~11,574 QPS                        │
│    Peak (3x avg) = ~35K QPS                                        │
│                                                                     │
│  Feed Reads:                                                        │
│    500M DAU × 10 refreshes/day = 5B requests/day                   │
│    5B ÷ 86,400 = ~58,000 QPS                                      │
│    Peak (3x avg) = ~174K QPS                                       │
│                                                                     │
│  Fan-out Writes (push model):                                       │
│    1B posts × 300 avg followers = 300B fan-out operations/day      │
│    300B ÷ 86,400 = ~3.47M operations/sec                          │
│    Peak = ~10.4M operations/sec                                     │
│                                                                     │
│  Read:Write ratio ≈ 5:1 (reads dominate, but fan-out              │
│                          amplifies writes massively)               │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

### Storage Estimation

```
┌─────────────────────────────────────────────────────────────────────┐
│                      STORAGE ESTIMATION                             │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  Post Metadata (text + metadata):                                   │
│    Avg post size: ~1 KB (text) + 0.5 KB (metadata) = 1.5 KB       │
│    Daily: 1B posts × 1.5 KB = 1.5 TB/day                          │
│    Yearly: 1.5 TB × 365 = ~548 TB/year                            │
│                                                                     │
│  Media Storage:                                                     │
│    20% of posts have images: 200M × 500 KB avg = 100 TB/day       │
│    5% of posts have videos: 50M × 10 MB avg = 500 TB/day          │
│    Total media: ~600 TB/day                                         │
│                                                                     │
│  Feed Cache (Redis):                                                │
│    Each user's feed: 500 post IDs × 8 bytes = 4 KB                 │
│    500M users: 500M × 4 KB = 2 TB                                  │
│    With scores + overhead: ~6 TB total Redis                        │
│                                                                     │
│  Social Graph:                                                      │
│    2B users × 300 avg connections × 16 bytes = ~9.6 TB             │
│                                                                     │
│  TOTAL (5 years):                                                   │
│    Posts: ~2.7 PB                                                   │
│    Media: ~1 EB (with dedup/compression savings)                   │
│    Feed cache: ~6 TB (rolling, not cumulative)                      │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

### Bandwidth Estimation

| Direction  | Calculation                              | Result         |
|------------|------------------------------------------|----------------|
| Ingress    | 35K posts/sec × 1.5KB + media uploads    | ~500 MB/s      |
| Egress     | 174K feed reads/sec × 20 posts × 1.5KB   | ~5 GB/s (text) |
| Media CDN  | Images + video serving                   | ~50-100 GB/s   |

---

## 5. API Design

### 5.1 Post Creation

```
POST /v1/feed/posts
Authorization: Bearer <token>
Content-Type: multipart/form-data

{
  "content": "string (max 10,000 chars)",
  "media_ids": ["media_id_1", "media_id_2"],   // pre-uploaded via media service
  "visibility": "public | followers | private",
  "reply_to": "post_id (optional)",
  "hashtags": ["tech", "systemdesign"]
}

Response 201:
{
  "post_id": "uuid-v7",
  "created_at": "2026-04-09T10:30:00Z",
  "author_id": "user_123",
  "content": "...",
  "media": [
    {
      "media_id": "m_456",
      "type": "image",
      "url": "https://cdn.example.com/images/m_456.webp",
      "thumbnail_url": "https://cdn.example.com/thumbs/m_456.webp"
    }
  ],
  "stats": { "likes": 0, "comments": 0, "shares": 0 }
}
```

### 5.2 Get News Feed (Cursor-Based Pagination)

```
GET /v1/feed?cursor=<cursor>&limit=20&ranking=ranked
Authorization: Bearer <token>

Response 200:
{
  "posts": [
    {
      "post_id": "uuid-v7",
      "author": {
        "user_id": "user_789",
        "username": "janedoe",
        "avatar_url": "https://cdn.example.com/avatars/user_789.webp"
      },
      "content": "...",
      "media": [...],
      "created_at": "2026-04-09T10:25:00Z",
      "stats": { "likes": 142, "comments": 23, "shares": 5 },
      "user_interaction": {
        "liked": false,
        "shared": false,
        "bookmarked": true
      },
      "ranking_score": 0.87
    },
    ...
  ],
  "pagination": {
    "next_cursor": "eyJ0IjoxNjk...",    // opaque, base64-encoded
    "has_more": true
  }
}
```

**Why Cursor-Based Over Offset-Based Pagination?**

```
┌──────────────────────────────────────────────────────────────────────┐
│              PAGINATION COMPARISON                                   │
├──────────────────────────┬───────────────────────────────────────────┤
│  Offset-Based            │  Cursor-Based                            │
│  GET /feed?offset=20     │  GET /feed?cursor=abc123                 │
├──────────────────────────┼───────────────────────────────────────────┤
│  ✗ Skips/duplicates on   │  ✓ Stable across inserts/deletes        │
│    concurrent inserts    │                                           │
│  ✗ O(N) for large offsets│  ✓ O(1) seek using indexed cursor       │
│  ✗ Poor for real-time    │  ✓ Works with real-time data            │
│  ✓ Easy to implement     │  ✗ Can't jump to arbitrary page         │
│  ✓ Supports "go to page" │  ✓ Perfect for infinite scroll          │
└──────────────────────────┴───────────────────────────────────────────┘

Cursor encoding: base64({ "ts": 1712654400, "post_id": "abc123" })
```

### 5.3 Follow / Unfollow

```
POST /v1/users/{user_id}/follow
Authorization: Bearer <token>

Response 200: { "status": "following", "follower_count": 1024 }

DELETE /v1/users/{user_id}/follow
Authorization: Bearer <token>

Response 200: { "status": "unfollowed", "follower_count": 1023 }
```

### 5.4 Like / Comment

```
POST /v1/feed/posts/{post_id}/like
Authorization: Bearer <token>

Response 200: { "liked": true, "like_count": 143 }

POST /v1/feed/posts/{post_id}/comments
Authorization: Bearer <token>
{
  "content": "Great post!",
  "reply_to_comment_id": "comment_456 (optional)"
}

Response 201:
{
  "comment_id": "comment_789",
  "content": "Great post!",
  "author_id": "user_123",
  "created_at": "2026-04-09T10:35:00Z"
}

GET /v1/feed/posts/{post_id}/comments?cursor=<cursor>&limit=20
```

### 5.5 Trending / Hashtags

```
GET /v1/feed/trending?region=US&limit=10

Response 200:
{
  "trending": [
    { "hashtag": "#systemdesign", "post_count": 45200, "trend_score": 0.95 },
    { "hashtag": "#tech",         "post_count": 38100, "trend_score": 0.88 },
    ...
  ],
  "updated_at": "2026-04-09T10:30:00Z"
}
```

### Rate Limiting

| Endpoint               | Rate Limit           | Window  |
|------------------------|----------------------|---------|
| `POST /feed/posts`     | 50 requests          | 1 hour  |
| `GET /feed`            | 300 requests         | 1 min   |
| `POST /like`           | 200 requests         | 1 hour  |
| `POST /follow`         | 100 requests         | 1 hour  |
| `POST /comments`       | 100 requests         | 1 hour  |

---

## 6. Data Model and Database Selection

### 6.1 Database Selection Rationale

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    DATABASE SELECTION MAP                                  │
├───────────────────┬──────────────────┬────────────────────────────────────┤
│  Data Type        │  Database        │  Why                               │
├───────────────────┼──────────────────┼────────────────────────────────────┤
│  Posts            │  Cassandra       │  High write throughput, tunable    │
│                   │  (or DynamoDB)   │  consistency, time-series friendly│
├───────────────────┼──────────────────┼────────────────────────────────────┤
│  Social Graph     │  Neo4j +         │  Graph queries (followers of      │
│  (follow edges)   │  MySQL (adjlist) │  followers), MySQL for simple     │
│                   │                  │  follower lookups                  │
├───────────────────┼──────────────────┼────────────────────────────────────┤
│  Feed Cache       │  Redis           │  Sorted sets for ranked feeds,    │
│                   │  (Cluster mode)  │  sub-ms reads, TTL support        │
├───────────────────┼──────────────────┼────────────────────────────────────┤
│  User Profiles    │  MySQL / Aurora  │  Relational data, strong          │
│                   │                  │  consistency for account data     │
├───────────────────┼──────────────────┼────────────────────────────────────┤
│  Media Files      │  S3 + CloudFront │  Blob storage + CDN for global    │
│                   │  (CDN)           │  low-latency delivery             │
├───────────────────┼──────────────────┼────────────────────────────────────┤
│  Counters         │  Redis           │  Atomic increments for likes,     │
│  (likes, views)   │  (+ async sync)  │  comments; async persist to DB   │
├───────────────────┼──────────────────┼────────────────────────────────────┤
│  Analytics/       │  Apache Kafka    │  Event streaming for engagement   │
│  Events           │  + ClickHouse    │  data, trending computation       │
└───────────────────┴──────────────────┴────────────────────────────────────┘
```

### 6.2 Schema Definitions

#### Posts Table (Cassandra)

```
CREATE TABLE posts (
    post_id       UUID,          -- UUID v7 (time-ordered)
    author_id     UUID,
    content       TEXT,
    media_ids     LIST<UUID>,
    visibility    TEXT,          -- 'public', 'followers', 'private'
    hashtags      SET<TEXT>,
    reply_to      UUID,
    like_count    COUNTER,
    comment_count COUNTER,
    share_count   COUNTER,
    created_at    TIMESTAMP,
    updated_at    TIMESTAMP,
    is_deleted    BOOLEAN,
    PRIMARY KEY ((author_id), created_at, post_id)
) WITH CLUSTERING ORDER BY (created_at DESC, post_id DESC);

-- Secondary index for post lookups by ID
CREATE TABLE posts_by_id (
    post_id       UUID,
    author_id     UUID,
    content       TEXT,
    media_ids     LIST<UUID>,
    visibility    TEXT,
    hashtags      SET<TEXT>,
    reply_to      UUID,
    like_count    COUNTER,
    comment_count COUNTER,
    share_count   COUNTER,
    created_at    TIMESTAMP,
    updated_at    TIMESTAMP,
    is_deleted    BOOLEAN,
    PRIMARY KEY (post_id)
);
```

**Partition key rationale:** `author_id` groups all posts by a single user on the
same partition, making "get user's posts" a single-partition query. `created_at DESC`
allows efficient time-ordered retrieval.

#### Social Graph (MySQL + Graph DB)

```sql
-- MySQL adjacency list for simple lookups
CREATE TABLE follows (
    follower_id   BIGINT NOT NULL,
    followee_id   BIGINT NOT NULL,
    created_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    status        ENUM('active', 'muted', 'blocked') DEFAULT 'active',
    PRIMARY KEY (follower_id, followee_id),
    INDEX idx_followee (followee_id, follower_id),
    INDEX idx_created (follower_id, created_at)
) ENGINE=InnoDB;

-- Follower counts (denormalized for performance)
CREATE TABLE user_follow_counts (
    user_id         BIGINT PRIMARY KEY,
    follower_count  INT UNSIGNED DEFAULT 0,
    following_count INT UNSIGNED DEFAULT 0
) ENGINE=InnoDB;
```

#### User Profiles (MySQL / Aurora)

```sql
CREATE TABLE users (
    user_id       BIGINT AUTO_INCREMENT PRIMARY KEY,
    username      VARCHAR(50) UNIQUE NOT NULL,
    display_name  VARCHAR(100),
    email         VARCHAR(255) UNIQUE,
    avatar_url    VARCHAR(500),
    bio           VARCHAR(500),
    is_verified   BOOLEAN DEFAULT FALSE,
    is_celebrity  BOOLEAN DEFAULT FALSE,   -- flag for fan-out strategy
    follower_count INT UNSIGNED DEFAULT 0,
    created_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_username (username)
) ENGINE=InnoDB;
```

#### Feed Cache Structure (Redis)

```
-- Each user has a Redis Sorted Set for their feed
-- Key: feed:{user_id}
-- Members: post_id
-- Score: timestamp (epoch milliseconds) or ranking_score

ZADD feed:user_123 1712654400000 "post_abc"
ZADD feed:user_123 1712654300000 "post_def"
ZADD feed:user_123 1712654200000 "post_ghi"

-- Retrieve latest 20 posts (descending by score)
ZREVRANGE feed:user_123 0 19 WITHSCORES

-- Cursor-based: get posts older than cursor timestamp
ZREVRANGEBYSCORE feed:user_123 (1712654300000 -inf LIMIT 0 20

-- TTL: feed expires after 7 days of inactivity
EXPIRE feed:user_123 604800
```

#### Comments Table (Cassandra)

```
CREATE TABLE comments (
    post_id       UUID,
    comment_id    UUID,          -- UUID v7 (time-ordered)
    author_id     UUID,
    content       TEXT,
    reply_to      UUID,          -- null for top-level comments
    like_count    COUNTER,
    created_at    TIMESTAMP,
    is_deleted    BOOLEAN,
    PRIMARY KEY ((post_id), created_at, comment_id)
) WITH CLUSTERING ORDER BY (created_at ASC, comment_id ASC);
```

### 6.3 Entity Relationship Overview

```
┌──────────────────────────────────────────────────────────────────────────┐
│                      ENTITY RELATIONSHIPS                                │
│                                                                          │
│  ┌──────────┐      follows       ┌──────────┐                          │
│  │          │ ──────────────────► │          │                          │
│  │   User   │ ◄────────────────── │   User   │                          │
│  │          │     followed_by     │          │                          │
│  └────┬─────┘                     └──────────┘                          │
│       │                                                                  │
│       │ creates                                                          │
│       ▼                                                                  │
│  ┌──────────┐                     ┌──────────┐                          │
│  │          │ ──────────────────► │          │                          │
│  │   Post   │     has_media       │  Media   │                          │
│  │          │                     │          │                          │
│  └────┬─────┘                     └──────────┘                          │
│       │                                                                  │
│       │ has_comments / has_likes                                         │
│       ▼                                                                  │
│  ┌──────────┐                     ┌──────────┐                          │
│  │          │                     │          │                          │
│  │ Comment  │                     │   Like   │                          │
│  │          │                     │          │                          │
│  └──────────┘                     └──────────┘                          │
│                                                                          │
│  Feed Cache (Redis): user_id ──► [post_id_1, post_id_2, ...]           │
│  (denormalized, pre-computed view of the feed)                          │
│                                                                          │
└──────────────────────────────────────────────────────────────────────────┘
```

---

## 7. High-Level Architecture

### 7.1 System Overview

```
┌──────────────────────────────────────────────────────────────────────────────────┐
│                              NEWS FEED SYSTEM                                    │
│                                                                                  │
│   ┌──────────┐  ┌──────────┐  ┌──────────┐                                     │
│   │  Mobile  │  │   Web    │  │  3rd     │                                     │
│   │   App    │  │  Client  │  │  Party   │                                     │
│   └────┬─────┘  └────┬─────┘  └────┬─────┘                                     │
│        │              │              │                                            │
│        └──────────────┼──────────────┘                                            │
│                       ▼                                                           │
│              ┌────────────────┐                                                   │
│              │  CDN (Media)   │  ◄── Serves images/videos                       │
│              └────────────────┘                                                   │
│                       │                                                           │
│                       ▼                                                           │
│              ┌────────────────┐                                                   │
│              │ Load Balancer  │  (L7, with health checks)                        │
│              │   (HAProxy /   │                                                   │
│              │    AWS ALB)    │                                                   │
│              └───────┬────────┘                                                   │
│                      │                                                            │
│                      ▼                                                            │
│              ┌────────────────┐                                                   │
│              │  API Gateway   │  Auth, rate limiting, routing                    │
│              │  (Kong/Envoy)  │                                                   │
│              └───────┬────────┘                                                   │
│                      │                                                            │
│        ┌─────────────┼─────────────┬──────────────┬──────────────┐               │
│        ▼             ▼             ▼              ▼              ▼               │
│  ┌───────────┐ ┌───────────┐ ┌──────────┐ ┌───────────┐ ┌───────────┐          │
│  │   Post    │ │   Feed    │ │  Social  │ │   Media   │ │  Notif.   │          │
│  │  Service  │ │  Service  │ │  Graph   │ │  Service  │ │  Service  │          │
│  │           │ │           │ │  Service │ │           │ │           │          │
│  └─────┬─────┘ └─────┬─────┘ └────┬─────┘ └─────┬─────┘ └─────┬─────┘          │
│        │             │            │              │              │               │
│        │             │            │              │              │               │
│  ┌─────┴─────────────┴────────────┴──────────────┴──────────────┘               │
│  │                                                                               │
│  │  ┌─────────────────┐    ┌──────────────────┐    ┌────────────────┐           │
│  │  │  Message Queue  │    │   Feed Cache     │    │  Post Store    │           │
│  │  │  (Kafka)        │    │   (Redis Cluster)│    │  (Cassandra)   │           │
│  │  └────────┬────────┘    └──────────────────┘    └────────────────┘           │
│  │           │                                                                   │
│  │           ▼                                                                   │
│  │  ┌─────────────────┐    ┌──────────────────┐    ┌────────────────┐           │
│  │  │  Fan-out        │    │  Social Graph    │    │   Media Store  │           │
│  │  │  Workers        │    │  (MySQL + Neo4j) │    │   (S3 + CDN)  │           │
│  │  └─────────────────┘    └──────────────────┘    └────────────────┘           │
│  │                                                                               │
│  └───────────────────────────────────────────────────────────────────────────────┘
└──────────────────────────────────────────────────────────────────────────────────┘
```

### 7.2 Post Creation Path (Write Path)

```
┌──────────────────────────────────────────────────────────────────────────────┐
│                          POST CREATION (WRITE PATH)                          │
│                                                                              │
│   Client                                                                     │
│     │                                                                        │
│     │  POST /v1/feed/posts                                                  │
│     ▼                                                                        │
│   ┌──────────────┐                                                           │
│   │ API Gateway  │  Auth + Rate Limit                                       │
│   └──────┬───────┘                                                           │
│          │                                                                    │
│          ▼                                                                    │
│   ┌──────────────┐     ┌──────────────────┐                                  │
│   │ Post Service │────►│ Content Validator │  (text length, profanity, spam) │
│   └──────┬───────┘     └──────────────────┘                                  │
│          │                                                                    │
│          │  (validated)                                                       │
│          │                                                                    │
│          ├───────────────────────┐                                            │
│          │                       │                                            │
│          ▼                       ▼                                            │
│   ┌──────────────┐       ┌──────────────┐                                    │
│   │  Cassandra   │       │  Kafka Topic │                                    │
│   │  (persist    │       │  "new-posts" │                                    │
│   │   post)      │       │              │                                    │
│   └──────────────┘       └──────┬───────┘                                    │
│                                  │                                            │
│                    ┌─────────────┼──────────────┐                             │
│                    ▼             ▼              ▼                             │
│             ┌───────────┐ ┌───────────┐ ┌────────────┐                       │
│             │ Fan-out   │ │ Fan-out   │ │ Fan-out    │  (N workers)          │
│             │ Worker 1  │ │ Worker 2  │ │ Worker N   │                       │
│             └─────┬─────┘ └─────┬─────┘ └──────┬─────┘                       │
│                   │             │              │                              │
│                   │   For each follower of post author:                       │
│                   │   ZADD feed:{follower_id} <timestamp> <post_id>          │
│                   │             │              │                              │
│                   ▼             ▼              ▼                              │
│             ┌─────────────────────────────────────────┐                       │
│             │         Redis Cluster (Feed Cache)       │                       │
│             │                                          │                       │
│             │  feed:user_A  → [post_new, post_2, ...]  │                       │
│             │  feed:user_B  → [post_new, post_5, ...]  │                       │
│             │  feed:user_C  → [post_new, post_8, ...]  │                       │
│             └─────────────────────────────────────────┘                       │
│                                                                              │
└──────────────────────────────────────────────────────────────────────────────┘
```

### 7.3 Feed Retrieval Path (Read Path)

```
┌──────────────────────────────────────────────────────────────────────────────┐
│                        FEED RETRIEVAL (READ PATH)                            │
│                                                                              │
│   Client                                                                     │
│     │                                                                        │
│     │  GET /v1/feed?cursor=xxx&limit=20                                     │
│     ▼                                                                        │
│   ┌──────────────┐                                                           │
│   │ API Gateway  │                                                           │
│   └──────┬───────┘                                                           │
│          │                                                                    │
│          ▼                                                                    │
│   ┌──────────────┐                                                           │
│   │ Feed Service │                                                           │
│   └──────┬───────┘                                                           │
│          │                                                                    │
│          ├─── Step 1: Get pre-computed feed ──────────┐                       │
│          │                                             ▼                      │
│          │                                    ┌──────────────┐               │
│          │                                    │ Redis Cache  │               │
│          │                                    │ ZREVRANGE    │               │
│          │                                    │ feed:user_X  │               │
│          │                                    └──────┬───────┘               │
│          │                                           │                       │
│          │    ◄──── [post_id_1, post_id_2, ...] ─────┘                       │
│          │                                                                    │
│          ├─── Step 2: Merge celebrity posts (pull) ───┐                       │
│          │                                             ▼                      │
│          │                                    ┌──────────────┐               │
│          │                                    │ Cassandra    │               │
│          │                                    │ (celebrity   │               │
│          │                                    │  posts)      │               │
│          │                                    └──────┬───────┘               │
│          │                                           │                       │
│          │    ◄──── [celeb_post_1, celeb_post_2] ────┘                       │
│          │                                                                    │
│          ├─── Step 3: Fetch full post data ──────────┐                       │
│          │                                             ▼                      │
│          │                                    ┌──────────────┐               │
│          │                                    │ Post Cache   │               │
│          │                                    │ (Redis) or   │               │
│          │                                    │ Cassandra     │               │
│          │                                    └──────┬───────┘               │
│          │                                           │                       │
│          │    ◄──── [full post objects] ──────────────┘                       │
│          │                                                                    │
│          ├─── Step 4: Rank and Personalize ──────────┐                       │
│          │                                             ▼                      │
│          │                                    ┌──────────────┐               │
│          │                                    │ Ranking      │               │
│          │                                    │ Service      │               │
│          │                                    │ (ML model)   │               │
│          │                                    └──────┬───────┘               │
│          │                                           │                       │
│          │    ◄──── [ranked, paginated posts] ────────┘                       │
│          │                                                                    │
│          ▼                                                                    │
│   Return top 20 ranked posts with cursor for next page                       │
│                                                                              │
└──────────────────────────────────────────────────────────────────────────────┘
```

### 7.4 Component Breakdown

| Component            | Responsibilities                                        | Scale              |
|----------------------|---------------------------------------------------------|--------------------|
| **API Gateway**      | Auth, rate limiting, request routing, SSL termination   | 50+ instances      |
| **Post Service**     | CRUD for posts, validation, media orchestration         | 100+ instances     |
| **Feed Service**     | Feed retrieval, celebrity merge, pagination              | 200+ instances     |
| **Fan-out Service**  | Distribute new posts to follower feed caches            | 500+ workers       |
| **Social Graph Svc** | Follow/unfollow, follower lists, recommendations        | 50+ instances      |
| **Media Service**    | Upload, transcode, thumbnail generation                  | 100+ instances     |
| **Notification Svc** | Push notifications for interactions                      | 50+ instances      |
| **Ranking Service**  | ML-based feed ranking and personalization                | 100+ instances     |
| **Trending Service** | Compute trending hashtags from event stream              | 20+ instances      |

---

## 8. Deep Dive: Core Components

### 8.1 Fan-out Service

The fan-out service is the heart of the news feed system. When a user creates a post,
the system must deliver that post to all followers' feeds. There are three fundamental
strategies:

#### Strategy 1: Fan-out on Write (Push Model)

When a user publishes a post, immediately push it to all followers' feed caches.

```
┌──────────────────────────────────────────────────────────────────────────┐
│                    FAN-OUT ON WRITE (PUSH MODEL)                         │
│                                                                          │
│   User A creates post_123                                                │
│     │                                                                    │
│     ▼                                                                    │
│   ┌───────────────┐                                                      │
│   │ Post Service  │──── Store post in Cassandra                         │
│   └───────┬───────┘                                                      │
│           │                                                              │
│           ▼                                                              │
│   ┌───────────────┐     ┌──────────────────────┐                        │
│   │ Kafka Topic   │────►│ Fan-out Workers       │                        │
│   │ "new-posts"   │     │ (parallel processing) │                        │
│   └───────────────┘     └──────────┬───────────┘                        │
│                                    │                                     │
│                     Get User A's followers: [B, C, D, E, F]             │
│                                    │                                     │
│                     For each follower:                                    │
│                     ┌──────────────┼──────────────┐                      │
│                     ▼              ▼              ▼                      │
│              ┌────────────┐ ┌────────────┐ ┌────────────┐               │
│              │ Redis      │ │ Redis      │ │ Redis      │               │
│              │ feed:B     │ │ feed:C     │ │ feed:D     │               │
│              │ ZADD       │ │ ZADD       │ │ ZADD       │               │
│              │ post_123   │ │ post_123   │ │ post_123   │               │
│              └────────────┘ └────────────┘ └────────────┘               │
│                                                                          │
│   Pros:                        Cons:                                     │
│   ✓ Fast reads (O(1) cache)   ✗ Slow writes for celebrities            │
│   ✓ Pre-computed feed          ✗ Wasted work for inactive users         │
│   ✓ Simple read path           ✗ Celebrity post = millions of writes    │
│                                ✗ High storage for feed caches            │
└──────────────────────────────────────────────────────────────────────────┘
```

**Time complexity for a user with N followers:**
- Write: O(N) -- one write to each follower's feed cache
- Read: O(1) -- single sorted set query

#### Strategy 2: Fan-out on Read (Pull Model)

When a user requests their feed, fetch posts from all followed users at read time.

```
┌──────────────────────────────────────────────────────────────────────────┐
│                    FAN-OUT ON READ (PULL MODEL)                          │
│                                                                          │
│   User B requests feed                                                   │
│     │                                                                    │
│     ▼                                                                    │
│   ┌───────────────┐                                                      │
│   │ Feed Service  │                                                      │
│   └───────┬───────┘                                                      │
│           │                                                              │
│           ▼                                                              │
│   ┌───────────────┐                                                      │
│   │ Social Graph  │──── Get B's following list: [A, X, Y, Z]           │
│   │ Service       │                                                      │
│   └───────┬───────┘                                                      │
│           │                                                              │
│           │  For each followed user, get recent posts:                   │
│           │                                                              │
│           ├───────────────┬───────────────┬───────────────┐              │
│           ▼               ▼               ▼               ▼              │
│    ┌────────────┐  ┌────────────┐  ┌────────────┐  ┌────────────┐      │
│    │ Cassandra  │  │ Cassandra  │  │ Cassandra  │  │ Cassandra  │      │
│    │ posts by A │  │ posts by X │  │ posts by Y │  │ posts by Z │      │
│    └─────┬──────┘  └─────┬──────┘  └─────┬──────┘  └─────┬──────┘      │
│          │               │               │               │              │
│          └───────────────┴───────┬───────┴───────────────┘              │
│                                  │                                       │
│                                  ▼                                       │
│                        ┌──────────────────┐                              │
│                        │  Merge + Sort    │                              │
│                        │  + Rank          │                              │
│                        │  + Paginate      │                              │
│                        └──────────────────┘                              │
│                                                                          │
│   Pros:                        Cons:                                     │
│   ✓ Fast writes (O(1))        ✗ Slow reads (O(following_count))         │
│   ✓ No wasted work            ✗ Must query many partitions              │
│   ✓ Always fresh data         ✗ Hard to rank across sources             │
│   ✓ No celebrity problem       ✗ Higher read latency                    │
└──────────────────────────────────────────────────────────────────────────┘
```

**Time complexity for a user following M users:**
- Write: O(1) -- just store the post
- Read: O(M) -- fetch from each followed user's partition

#### Strategy 3: Hybrid Approach (Production Solution)

This is what Twitter and Facebook actually use. Combine push for normal users and pull
for celebrities.

```
┌──────────────────────────────────────────────────────────────────────────────┐
│                        HYBRID FAN-OUT APPROACH                               │
│                                                                              │
│   THRESHOLD: Users with > 10,000 followers = "celebrity" (pull-based)       │
│              Users with ≤ 10,000 followers = "normal"    (push-based)       │
│                                                                              │
│   ┌─────────────────────────────────────────────────────────────────────┐    │
│   │                    POST CREATION                                     │    │
│   │                                                                      │    │
│   │   New post arrives                                                   │    │
│   │        │                                                             │    │
│   │        ▼                                                             │    │
│   │   ┌────────────────┐                                                 │    │
│   │   │ Is author a    │                                                 │    │
│   │   │ celebrity?     │                                                 │    │
│   │   └───┬────────┬───┘                                                 │    │
│   │       │        │                                                     │    │
│   │      YES      NO                                                     │    │
│   │       │        │                                                     │    │
│   │       ▼        ▼                                                     │    │
│   │   Store in   Fan-out to all                                          │    │
│   │   post DB    followers' caches                                       │    │
│   │   ONLY       (push model)                                            │    │
│   │                                                                      │    │
│   └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│   ┌─────────────────────────────────────────────────────────────────────┐    │
│   │                    FEED RETRIEVAL                                     │    │
│   │                                                                      │    │
│   │   User requests feed                                                 │    │
│   │        │                                                             │    │
│   │        ├──── Step 1: Read pre-computed feed from Redis              │    │
│   │        │     (contains posts from normal users, already pushed)     │    │
│   │        │     Result: [post_A, post_B, post_C, ...]                 │    │
│   │        │                                                             │    │
│   │        ├──── Step 2: Identify celebrities user follows              │    │
│   │        │     Query: social_graph.get_celebrity_followees(user_id)   │    │
│   │        │     Result: [celeb_1, celeb_2]                             │    │
│   │        │                                                             │    │
│   │        ├──── Step 3: Pull recent posts from each celebrity          │    │
│   │        │     Query: posts_by_author WHERE author_id IN (celeb_1,   │    │
│   │        │            celeb_2) AND created_at > 24h ago              │    │
│   │        │     Result: [celeb_post_X, celeb_post_Y]                  │    │
│   │        │                                                             │    │
│   │        ├──── Step 4: Merge both lists                               │    │
│   │        │     merged = push_feed + pull_celebrity_posts             │    │
│   │        │                                                             │    │
│   │        ├──── Step 5: Rank using ML model                            │    │
│   │        │     ranked = ranking_service.rank(merged, user_features)   │    │
│   │        │                                                             │    │
│   │        └──── Step 6: Paginate and return top 20                     │    │
│   │                                                                      │    │
│   └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
└──────────────────────────────────────────────────────────────────────────────┘
```

#### Fan-out Strategy Comparison

```
┌──────────────────┬──────────────────┬──────────────────┬──────────────────┐
│   Dimension      │  Fan-out Write   │  Fan-out Read    │  Hybrid          │
├──────────────────┼──────────────────┼──────────────────┼──────────────────┤
│ Write latency    │ High (O(N))      │ O(1)             │ Low-Medium       │
│ Read latency     │ O(1)             │ High (O(M))      │ Low              │
│ Celebrity problem│ Severe           │ None             │ Solved           │
│ Storage (cache)  │ Very high        │ Low              │ Moderate         │
│ Freshness        │ Near real-time   │ Always fresh     │ Near real-time   │
│ Complexity       │ Low              │ Medium           │ High             │
│ Wasted work      │ Inactive users   │ None             │ Minimal          │
│ Used by          │ Early Twitter    │ (rarely pure)    │ Twitter, Meta    │
└──────────────────┴──────────────────┴──────────────────┴──────────────────┘
```

#### The Celebrity Problem in Detail

```
┌──────────────────────────────────────────────────────────────────────────┐
│                       THE CELEBRITY PROBLEM                              │
│                                                                          │
│   Scenario: Celebrity C has 100 million followers, posts once.          │
│                                                                          │
│   Fan-out on Write:                                                      │
│   ┌─────────────────────────────────────────────────────────────────┐    │
│   │  100,000,000 Redis ZADD operations                              │    │
│   │  At 100K ops/sec per Redis node = 1,000 seconds = ~17 minutes  │    │
│   │  Even with 100 fan-out workers: ~10 seconds lag                 │    │
│   │  Memory: 100M × 8 bytes = 800 MB per celebrity post             │    │
│   └─────────────────────────────────────────────────────────────────┘    │
│                                                                          │
│   Hybrid Solution:                                                       │
│   ┌─────────────────────────────────────────────────────────────────┐    │
│   │  Celebrity C's post stored ONLY in Cassandra                    │    │
│   │  Write cost: O(1) -- single DB write                            │    │
│   │  Read cost: each follower pulls from C's post timeline          │    │
│   │  Since user follows ~5-10 celebrities on average:               │    │
│   │    Extra read cost per feed request = 5-10 Cassandra queries    │    │
│   │    ~5ms extra latency (well within 200ms budget)                │    │
│   └─────────────────────────────────────────────────────────────────┘    │
│                                                                          │
│   How to determine the threshold?                                        │
│   ┌─────────────────────────────────────────────────────────────────┐    │
│   │  Followers < 1K     : Always push (fast fan-out)                │    │
│   │  1K - 10K           : Push (manageable fan-out)                 │    │
│   │  10K - 100K         : Configurable (analyze cost)               │    │
│   │  > 100K             : Always pull (celebrity)                   │    │
│   │                                                                  │    │
│   │  The threshold is tunable. Twitter reportedly uses ~5K-10K.     │    │
│   │  The flag is_celebrity on the user record controls this.        │    │
│   └─────────────────────────────────────────────────────────────────┘    │
│                                                                          │
└──────────────────────────────────────────────────────────────────────────┘
```

### 8.2 Feed Ranking Algorithm

Modern news feeds do not show posts in pure chronological order. They use ML-based
ranking to maximize user engagement and relevance.

#### Ranking Architecture

```
┌──────────────────────────────────────────────────────────────────────────┐
│                      FEED RANKING PIPELINE                               │
│                                                                          │
│   Candidate Posts (from cache + celebrity pull)                          │
│        │                                                                 │
│        │  ~500 candidate posts                                           │
│        ▼                                                                 │
│   ┌──────────────────────────┐                                          │
│   │ Stage 1: Candidate       │  Remove duplicates, deleted posts,       │
│   │          Filtering       │  posts user has already seen,            │
│   │                          │  blocked users, muted hashtags            │
│   └────────────┬─────────────┘                                          │
│                │  ~300 candidates                                        │
│                ▼                                                         │
│   ┌──────────────────────────┐                                          │
│   │ Stage 2: Feature         │  Extract features for each candidate:    │
│   │          Extraction      │  - Post features (age, media type)       │
│   │                          │  - Author features (relationship)        │
│   │                          │  - User features (interests)             │
│   │                          │  - Interaction features (past likes)     │
│   └────────────┬─────────────┘                                          │
│                │  Feature vectors                                        │
│                ▼                                                         │
│   ┌──────────────────────────┐                                          │
│   │ Stage 3: ML Scoring      │  Run through trained model:              │
│   │          (Lightweight)   │  - P(like), P(comment), P(share)         │
│   │                          │  - P(click), P(hide/report)              │
│   │                          │  Weighted score = Σ(weight_i × P_i)      │
│   └────────────┬─────────────┘                                          │
│                │  Scored candidates                                       │
│                ▼                                                         │
│   ┌──────────────────────────┐                                          │
│   │ Stage 4: Business Rules  │  - Diversity (don't show 5 posts         │
│   │          & Re-ranking    │    from same author in a row)            │
│   │                          │  - Content type mixing (text, img, vid)  │
│   │                          │  - Freshness boost (newer = higher)      │
│   │                          │  - Anti-echo-chamber rules               │
│   └────────────┬─────────────┘                                          │
│                │  ~20 posts (page 1)                                     │
│                ▼                                                         │
│   Return ranked, paginated feed                                          │
│                                                                          │
└──────────────────────────────────────────────────────────────────────────┘
```

#### Feature Vector and Scoring Function

```
┌──────────────────────────────────────────────────────────────────────────┐
│                    RANKING FEATURE VECTOR                                 │
│                                                                          │
│  For each candidate post, we compute:                                    │
│                                                                          │
│  Post Features:                                                          │
│  ┌────────────────────────────────────────────────────────────────┐      │
│  │ post_age_hours        : float  (0.5 = 30 min ago)              │      │
│  │ has_image             : bool   (1/0)                           │      │
│  │ has_video             : bool   (1/0)                           │      │
│  │ text_length           : int    (normalized 0-1)                │      │
│  │ hashtag_count         : int                                    │      │
│  │ current_like_count    : int    (log-normalized)                │      │
│  │ current_comment_count : int    (log-normalized)                │      │
│  │ current_share_count   : int    (log-normalized)                │      │
│  │ engagement_velocity   : float  (likes/min in last hour)        │      │
│  └────────────────────────────────────────────────────────────────┘      │
│                                                                          │
│  Author Features:                                                        │
│  ┌────────────────────────────────────────────────────────────────┐      │
│  │ is_verified           : bool                                   │      │
│  │ follower_count        : int    (log-normalized)                │      │
│  │ avg_engagement_rate   : float  (past 30 days)                  │      │
│  │ post_frequency        : float  (posts per day)                 │      │
│  └────────────────────────────────────────────────────────────────┘      │
│                                                                          │
│  User-Author Relationship Features:                                      │
│  ┌────────────────────────────────────────────────────────────────┐      │
│  │ relationship_strength : float  (0-1, based on past interactions│      │
│  │ times_liked_author    : int    (in last 30 days)               │      │
│  │ times_commented       : int    (in last 30 days)               │      │
│  │ times_shared          : int    (in last 30 days)               │      │
│  │ profile_visits        : int    (visited author's profile?)     │      │
│  │ is_close_friend       : bool                                   │      │
│  │ mutual_friends_count  : int                                    │      │
│  └────────────────────────────────────────────────────────────────┘      │
│                                                                          │
│  Scoring Function:                                                       │
│  ┌────────────────────────────────────────────────────────────────┐      │
│  │                                                                │      │
│  │  score = w1 × P(like)                                          │      │
│  │        + w2 × P(comment)                                       │      │
│  │        + w3 × P(share)                                         │      │
│  │        + w4 × P(click_through)                                 │      │
│  │        - w5 × P(hide)                                          │      │
│  │        - w6 × P(report)                                        │      │
│  │        + w7 × freshness_decay(post_age)                        │      │
│  │        + w8 × relationship_strength                            │      │
│  │                                                                │      │
│  │  Where:                                                        │      │
│  │    w1=1.0, w2=2.0, w3=3.0, w4=0.5, w5=5.0, w6=10.0           │      │
│  │    w7=0.3, w8=1.5                                              │      │
│  │                                                                │      │
│  │  freshness_decay(age) = 1 / (1 + age_hours/24)                │      │
│  │  (posts older than 24h get significantly lower scores)         │      │
│  │                                                                │      │
│  └────────────────────────────────────────────────────────────────┘      │
│                                                                          │
└──────────────────────────────────────────────────────────────────────────┘
```

#### Chronological vs Ranked Feed

| Aspect              | Chronological               | Ranked (ML-based)                    |
|---------------------|-----------------------------|--------------------------------------|
| Ordering            | Newest first                | Relevance score                      |
| User expectation    | Simple, predictable         | "Best" content surfaces              |
| Engagement          | Lower                       | Higher (typically +10-30%)           |
| Cold start          | Works perfectly             | Needs interaction history            |
| Transparency        | High (user understands)     | Low (black box)                      |
| Implementation      | Simple                      | Complex (ML pipeline)                |
| Celebrity advantage | Low (buried quickly)        | High (engagement begets visibility)  |
| Used by             | Mastodon, RSS readers       | Facebook, Twitter, Instagram, TikTok |

### 8.3 Post Storage and Retrieval

#### Write Path (Detailed)

```
┌──────────────────────────────────────────────────────────────────────────┐
│                    POST WRITE PATH (DETAILED)                            │
│                                                                          │
│   1. Client submits post                                                 │
│      │                                                                   │
│      ▼                                                                   │
│   2. API Gateway: authenticate, rate limit                              │
│      │                                                                   │
│      ▼                                                                   │
│   3. Post Service: validate content                                      │
│      ├── Text length check (≤ 10,000 chars)                             │
│      ├── Media reference validation (do media_ids exist?)               │
│      ├── Spam detection (basic heuristics)                               │
│      └── Profanity filter (if enabled)                                   │
│      │                                                                   │
│      ▼                                                                   │
│   4. Generate post_id (UUID v7 -- time-ordered for natural sorting)     │
│      │                                                                   │
│      ▼                                                                   │
│   5. Write to Cassandra (posts + posts_by_id tables)                    │
│      │  Consistency level: LOCAL_QUORUM (strong within DC)               │
│      │                                                                   │
│      ├──────── Success ─────────┐                                        │
│      │                          │                                        │
│      ▼                          ▼                                        │
│   6. Publish to Kafka        7. Return 201 to client                    │
│      topic: "new-posts"        (don't wait for fan-out)                 │
│      │                                                                   │
│      ▼                                                                   │
│   8. Fan-out workers consume from Kafka                                  │
│      ├── Check if author is_celebrity                                    │
│      ├── If NO: get follower list, ZADD to each feed cache             │
│      ├── If YES: skip fan-out (pull-based)                              │
│      └── Trim each feed cache to last 500 entries (ZREMRANGEBYRANK)    │
│      │                                                                   │
│      ▼                                                                   │
│   9. Publish to Kafka topic: "post-events"                              │
│      (for trending, analytics, notifications)                            │
│                                                                          │
└──────────────────────────────────────────────────────────────────────────┘
```

#### Read Path (Detailed)

```
┌──────────────────────────────────────────────────────────────────────────┐
│                    POST READ PATH (DETAILED)                             │
│                                                                          │
│   1. Client requests GET /v1/feed?cursor=xxx&limit=20                   │
│      │                                                                   │
│      ▼                                                                   │
│   2. Feed Service decodes cursor (timestamp + post_id)                  │
│      │                                                                   │
│      ▼                                                                   │
│   3. Query pre-computed feed from Redis                                  │
│      │  ZREVRANGEBYSCORE feed:{user_id} (cursor_ts) -inf LIMIT 0 50    │
│      │  (fetch 50 to have enough after filtering)                       │
│      │                                                                   │
│      ├── Cache HIT ──────────────────────────────────────────┐          │
│      │                                                        │          │
│      ├── Cache MISS ──────────────┐                           │          │
│      │                            ▼                           │          │
│      │               Regenerate feed:                         │          │
│      │               a) Get following list                    │          │
│      │               b) For each, query recent posts          │          │
│      │               c) Merge by timestamp                    │          │
│      │               d) Store in Redis cache                  │          │
│      │               e) Set TTL = 7 days                      │          │
│      │                            │                           │          │
│      │                            └───────────────────────────┤          │
│      │                                                        │          │
│      ▼                                                        ▼          │
│   4. Merge with celebrity posts (pull-based)                             │
│      │  Get user's celebrity followee list (cached in Redis)            │
│      │  For each celebrity: query Cassandra for recent posts            │
│      │  Merge into candidate list                                        │
│      │                                                                   │
│      ▼                                                                   │
│   5. Hydrate post IDs into full post objects                             │
│      │  Multi-get from post cache (Redis) → fallback to Cassandra       │
│      │  Batch fetch author profiles (user cache)                        │
│      │  Fetch engagement counts (counter cache)                          │
│      │                                                                   │
│      ▼                                                                   │
│   6. Filter out:                                                         │
│      │  - Deleted posts (is_deleted = true)                              │
│      │  - Posts from blocked users                                       │
│      │  - Posts user has already seen (seen_posts bloom filter)          │
│      │  - Muted hashtags                                                 │
│      │                                                                   │
│      ▼                                                                   │
│   7. Apply ranking model                                                 │
│      │                                                                   │
│      ▼                                                                   │
│   8. Take top 20, encode next cursor, return response                   │
│                                                                          │
│   Total latency budget:                                                  │
│   ┌────────────────────────────────┬─────────────┐                       │
│   │ Step                           │ Target (ms) │                       │
│   ├────────────────────────────────┼─────────────┤                       │
│   │ Redis feed read                │     5       │                       │
│   │ Celebrity post fetch           │    20       │                       │
│   │ Post hydration (batch)         │    30       │                       │
│   │ Filtering                      │     5       │                       │
│   │ Ranking model inference        │    50       │                       │
│   │ Serialization + network        │    20       │                       │
│   │ Buffer                         │    70       │                       │
│   ├────────────────────────────────┼─────────────┤                       │
│   │ TOTAL                          │   200       │                       │
│   └────────────────────────────────┴─────────────┘                       │
│                                                                          │
└──────────────────────────────────────────────────────────────────────────┘
```

### 8.4 Social Graph Service

The social graph manages follow relationships and powers follower list queries for
fan-out.

```
┌──────────────────────────────────────────────────────────────────────────┐
│                    SOCIAL GRAPH SERVICE                                   │
│                                                                          │
│  ┌─────────────────────────────────────────────────────────────┐        │
│  │                    API Layer                                  │        │
│  │                                                               │        │
│  │  follow(A, B)       unfollow(A, B)                           │        │
│  │  get_followers(A)   get_following(A)                          │        │
│  │  get_mutual(A, B)   is_following(A, B)                       │        │
│  │  get_celebrity_followees(A)                                   │        │
│  │  suggest_users(A)                                             │        │
│  └──────┬──────────────────────────────────────────┬─────────────┘        │
│         │                                          │                      │
│         ▼                                          ▼                      │
│  ┌──────────────────┐                    ┌──────────────────┐            │
│  │   MySQL          │                    │   Redis Cache    │            │
│  │   (follows table)│                    │                  │            │
│  │                  │                    │ followers:{uid}  │            │
│  │  follower_id     │                    │ = SET of user_ids│            │
│  │  followee_id     │                    │                  │            │
│  │  created_at      │                    │ following:{uid}  │            │
│  │  status          │                    │ = SET of user_ids│            │
│  └──────────────────┘                    │                  │            │
│                                          │ celebrity_followees│           │
│                                          │ :{uid} = SET     │            │
│                                          └──────────────────┘            │
│                                                                          │
│  Follow Operation:                                                       │
│  1. Write to MySQL (INSERT INTO follows)                                │
│  2. Update follower/following counts                                     │
│  3. Invalidate Redis cache for both users                               │
│  4. Publish event to Kafka (for feed backfill)                          │
│                                                                          │
│  Unfollow Operation:                                                     │
│  1. Soft-delete in MySQL (UPDATE status = 'inactive')                   │
│  2. Update counts                                                        │
│  3. Invalidate caches                                                    │
│  4. Remove unfollowed user's posts from follower's feed cache           │
│     (async, via Kafka consumer)                                          │
│                                                                          │
│  Friend Recommendations (Graph Traversal):                               │
│  ┌──────────────────────────────────────────────────────────┐            │
│  │                                                          │            │
│  │   User A follows [B, C]                                  │            │
│  │   B follows [D, E, F]                                    │            │
│  │   C follows [D, G, H]                                    │            │
│  │                                                          │            │
│  │   "Friends of friends" = {D(2), E(1), F(1), G(1), H(1)} │            │
│  │   Recommend D first (common connection = 2)              │            │
│  │                                                          │            │
│  │   This is a 2-hop BFS -- efficient with Neo4j            │            │
│  │   For simple use: MySQL with JOIN on follows table       │            │
│  │                                                          │            │
│  └──────────────────────────────────────────────────────────┘            │
│                                                                          │
└──────────────────────────────────────────────────────────────────────────┘
```

---

## 9. Data Partitioning and Sharding

### Sharding Strategy Overview

```
┌──────────────────────────────────────────────────────────────────────────┐
│                     SHARDING STRATEGY                                    │
│                                                                          │
│  ┌─────────────────────────────────────────────────────────────────┐    │
│  │  Data Store      │  Shard Key      │  Rationale                 │    │
│  ├───────────────────┼─────────────────┼────────────────────────────┤    │
│  │  Posts            │  author_id      │  "Get user's posts" is a  │    │
│  │  (Cassandra)      │  (partition key)│  single-partition query    │    │
│  ├───────────────────┼─────────────────┼────────────────────────────┤    │
│  │  Feed Cache       │  user_id        │  Each user's feed lives   │    │
│  │  (Redis)          │  (hash slot)    │  on one Redis node        │    │
│  ├───────────────────┼─────────────────┼────────────────────────────┤    │
│  │  Social Graph     │  user_id        │  Follower/following lists │    │
│  │  (MySQL)          │  (range shard)  │  accessed per-user        │    │
│  ├───────────────────┼─────────────────┼────────────────────────────┤    │
│  │  User Profiles    │  user_id        │  Direct lookups by user   │    │
│  │  (MySQL)          │  (hash shard)   │                            │    │
│  └───────────────────┴─────────────────┴────────────────────────────┘    │
│                                                                          │
└──────────────────────────────────────────────────────────────────────────┘
```

### Cassandra Partitioning for Posts

```
┌──────────────────────────────────────────────────────────────────────────┐
│              CASSANDRA PARTITION LAYOUT FOR POSTS                         │
│                                                                          │
│  Partition Key: author_id                                                │
│  Clustering Keys: (created_at DESC, post_id DESC)                       │
│                                                                          │
│  ┌─────────────────────────────────────────┐                            │
│  │  Partition: author_id = user_A          │                            │
│  │  ┌──────────────────────────────────┐   │                            │
│  │  │ 2026-04-09 10:30 │ post_abc │ ...│   │                            │
│  │  │ 2026-04-09 08:15 │ post_def │ ...│   │                            │
│  │  │ 2026-04-08 22:00 │ post_ghi │ ...│   │                            │
│  │  │ ...                               │   │                            │
│  │  └──────────────────────────────────┘   │                            │
│  └─────────────────────────────────────────┘                            │
│                                                                          │
│  ┌─────────────────────────────────────────┐                            │
│  │  Partition: author_id = user_B          │                            │
│  │  ┌──────────────────────────────────┐   │                            │
│  │  │ 2026-04-09 09:45 │ post_jkl │ ...│   │                            │
│  │  │ 2026-04-08 14:30 │ post_mno │ ...│   │                            │
│  │  └──────────────────────────────────┘   │                            │
│  └─────────────────────────────────────────┘                            │
│                                                                          │
│  Hot partition risk: celebrity with 50K posts/year → large partition    │
│  Mitigation: Add time bucket to partition key                            │
│                                                                          │
│  PRIMARY KEY ((author_id, year_month), created_at, post_id)             │
│  This caps each partition to ~1 month of posts per user                 │
│                                                                          │
└──────────────────────────────────────────────────────────────────────────┘
```

### Redis Cluster Sharding for Feed Cache

```
┌──────────────────────────────────────────────────────────────────────────┐
│              REDIS CLUSTER FOR FEED CACHE                                │
│                                                                          │
│  Redis Cluster: 100 nodes, 16384 hash slots                            │
│  Key: feed:{user_id} → hash(user_id) mod 16384 → slot → node          │
│                                                                          │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐                  │
│  │ Redis Node 0 │  │ Redis Node 1 │  │ Redis Node 2 │  ...            │
│  │ Slots 0-163  │  │ Slots 164-327│  │ Slots 328-491│                  │
│  │              │  │              │  │              │                  │
│  │ feed:u_001   │  │ feed:u_200   │  │ feed:u_450   │                  │
│  │ feed:u_034   │  │ feed:u_189   │  │ feed:u_503   │                  │
│  │ feed:u_088   │  │ feed:u_277   │  │ feed:u_612   │                  │
│  │ ...          │  │ ...          │  │ ...          │                  │
│  └──────────────┘  └──────────────┘  └──────────────┘                  │
│                                                                          │
│  Each node:                                                              │
│  - Primary: handles reads and writes                                     │
│  - 2 Replicas: handle read scaling + failover                           │
│  - Memory: ~60 GB per node (6 TB total across 100 nodes)               │
│                                                                          │
│  Each sorted set:                                                        │
│  - Max 500 entries (post_ids with timestamp scores)                     │
│  - Size: ~4-8 KB per user's feed                                        │
│  - ZREMRANGEBYRANK trims to keep size bounded                            │
│                                                                          │
└──────────────────────────────────────────────────────────────────────────┘
```

### MySQL Sharding for Social Graph

```
┌──────────────────────────────────────────────────────────────────────────┐
│               MYSQL SHARDING FOR SOCIAL GRAPH                            │
│                                                                          │
│  Strategy: Hash-based sharding on follower_id                           │
│  Shards: 256 MySQL shards (Vitess or ProxySQL for routing)             │
│                                                                          │
│  Query: "Get all users that user_A follows"                             │
│  → Route to shard: hash(user_A) mod 256                                │
│  → Single-shard query (efficient)                                       │
│                                                                          │
│  Query: "Get all followers of user_A"                                   │
│  → Needs secondary index on followee_id                                 │
│  → Option A: Global secondary index (scatter-gather)                   │
│  → Option B: Denormalized reverse table (followers_of)                 │
│              sharded by followee_id                                     │
│                                                                          │
│  ┌────────────────────────────────────────────────────────────┐          │
│  │  Table: follows (sharded by follower_id)                   │          │
│  │  "Who does user X follow?"  → single shard                │          │
│  │                                                            │          │
│  │  Table: followers_of (sharded by followee_id)              │          │
│  │  "Who follows user X?"  → single shard                    │          │
│  │  (denormalized copy, maintained via async replication)     │          │
│  └────────────────────────────────────────────────────────────┘          │
│                                                                          │
│  This denormalization doubles storage but eliminates scatter-gather     │
│  queries, which is critical for fan-out performance.                    │
│                                                                          │
└──────────────────────────────────────────────────────────────────────────┘
```

---

## 10. Caching Strategy

### Multi-Layer Cache Architecture

```
┌──────────────────────────────────────────────────────────────────────────┐
│                    CACHING LAYERS                                        │
│                                                                          │
│   Layer 1: Client-Side Cache                                            │
│   ┌─────────────────────────────────────────────────────────────┐       │
│   │  Mobile app / browser cache                                  │       │
│   │  - Last loaded feed stored locally                           │       │
│   │  - Shown instantly on app open (stale-while-revalidate)     │       │
│   │  - ETags for conditional requests                            │       │
│   │  TTL: session-based                                          │       │
│   └─────────────────────────────────────────────────────────────┘       │
│                         │                                                │
│                         ▼                                                │
│   Layer 2: CDN Cache (Media Only)                                       │
│   ┌─────────────────────────────────────────────────────────────┐       │
│   │  CloudFront / Akamai / Fastly                                │       │
│   │  - Images, video thumbnails, profile pictures                │       │
│   │  - Cache-Control: public, max-age=31536000 (immutable URLs) │       │
│   │  - Global edge locations for low-latency media delivery      │       │
│   │  Hit ratio: 95%+                                             │       │
│   └─────────────────────────────────────────────────────────────┘       │
│                         │                                                │
│                         ▼                                                │
│   Layer 3: Application Cache (Redis)                                    │
│   ┌─────────────────────────────────────────────────────────────┐       │
│   │                                                              │       │
│   │  3a. Feed Cache (Redis Sorted Sets)                          │       │
│   │  ┌──────────────────────────────────────────────────┐       │       │
│   │  │ Key: feed:{user_id}                               │       │       │
│   │  │ Type: Sorted Set (score = timestamp)              │       │       │
│   │  │ Max entries: 500 post IDs                         │       │       │
│   │  │ TTL: 7 days (for inactive users)                  │       │       │
│   │  │ Hit ratio: 90%                                    │       │       │
│   │  └──────────────────────────────────────────────────┘       │       │
│   │                                                              │       │
│   │  3b. Post Cache (Redis Hash)                                 │       │
│   │  ┌──────────────────────────────────────────────────┐       │       │
│   │  │ Key: post:{post_id}                               │       │       │
│   │  │ Type: Hash (all post fields)                      │       │       │
│   │  │ TTL: 24 hours (hot posts stay cached)             │       │       │
│   │  │ Hit ratio: 85%                                    │       │       │
│   │  └──────────────────────────────────────────────────┘       │       │
│   │                                                              │       │
│   │  3c. User Cache (Redis Hash)                                 │       │
│   │  ┌──────────────────────────────────────────────────┐       │       │
│   │  │ Key: user:{user_id}                               │       │       │
│   │  │ Type: Hash (profile fields)                       │       │       │
│   │  │ TTL: 1 hour                                       │       │       │
│   │  │ Hit ratio: 95%                                    │       │       │
│   │  └──────────────────────────────────────────────────┘       │       │
│   │                                                              │       │
│   │  3d. Follower List Cache (Redis Set)                         │       │
│   │  ┌──────────────────────────────────────────────────┐       │       │
│   │  │ Key: followers:{user_id}                          │       │       │
│   │  │ Type: Set of user_ids                             │       │       │
│   │  │ TTL: 1 hour                                       │       │       │
│   │  │ Invalidated on follow/unfollow                    │       │       │
│   │  └──────────────────────────────────────────────────┘       │       │
│   │                                                              │       │
│   │  3e. Engagement Counters (Redis)                             │       │
│   │  ┌──────────────────────────────────────────────────┐       │       │
│   │  │ Key: likes:{post_id}, comments:{post_id}         │       │       │
│   │  │ Type: Integer (INCR/DECR)                         │       │       │
│   │  │ Async-synced to Cassandra every 30 seconds        │       │       │
│   │  └──────────────────────────────────────────────────┘       │       │
│   │                                                              │       │
│   └─────────────────────────────────────────────────────────────┘       │
│                         │                                                │
│                         ▼                                                │
│   Layer 4: Database (Source of Truth)                                    │
│   ┌─────────────────────────────────────────────────────────────┐       │
│   │  Cassandra (posts), MySQL (users, social graph)              │       │
│   │  Only hit on cache miss                                      │       │
│   └─────────────────────────────────────────────────────────────┘       │
│                                                                          │
└──────────────────────────────────────────────────────────────────────────┘
```

### Cache Invalidation Strategy

```
┌──────────────────────────────────────────────────────────────────────────┐
│                  CACHE INVALIDATION STRATEGIES                           │
│                                                                          │
│  Event                │  Invalidation Action                            │
│  ─────────────────────┼─────────────────────────────────────────────────│
│  New post created     │  Fan-out adds to followers' feed caches        │
│                       │  No invalidation needed (additive)              │
│  ─────────────────────┼─────────────────────────────────────────────────│
│  Post deleted         │  ZREM feed:{follower_id} post_id               │
│                       │  DEL post:{post_id}                             │
│                       │  (async via Kafka event)                        │
│  ─────────────────────┼─────────────────────────────────────────────────│
│  Post edited          │  Update post:{post_id} hash in Redis           │
│                       │  Feed cache unchanged (only has post_id)       │
│  ─────────────────────┼─────────────────────────────────────────────────│
│  User unfollowed      │  Remove unfollowed user's posts from           │
│                       │  follower's feed cache (async scan + ZREM)     │
│  ─────────────────────┼─────────────────────────────────────────────────│
│  User blocked         │  Same as unfollow + add to block list          │
│  ─────────────────────┼─────────────────────────────────────────────────│
│  Profile updated      │  DEL user:{user_id} (TTL will repopulate)     │
│  ─────────────────────┼─────────────────────────────────────────────────│
│  Like/comment         │  INCR likes:{post_id}                          │
│                       │  (no feed cache change needed)                  │
│                                                                          │
│  Pattern: Write-through for feed cache, write-behind for counters,     │
│           TTL-based expiry for user/post caches.                        │
│                                                                          │
└──────────────────────────────────────────────────────────────────────────┘
```

---

## 11. Replication and Consistency

### Consistency Model Per Data Store

```
┌──────────────────────────────────────────────────────────────────────────┐
│                  CONSISTENCY AND REPLICATION                              │
│                                                                          │
│  ┌────────────────┬───────────────┬──────────────┬───────────────────┐  │
│  │ Data Store     │ Consistency   │ Replication  │ Notes             │  │
│  ├────────────────┼───────────────┼──────────────┼───────────────────┤  │
│  │ Posts          │ LOCAL_QUORUM  │ RF=3 per DC  │ Strong within DC, │  │
│  │ (Cassandra)    │ (write)       │ 3 DCs        │ eventually across │  │
│  │                │ LOCAL_ONE     │              │ DCs               │  │
│  │                │ (read)        │              │                   │  │
│  ├────────────────┼───────────────┼──────────────┼───────────────────┤  │
│  │ Feed Cache     │ Eventual      │ 1 primary +  │ Feed is a view,  │  │
│  │ (Redis)        │               │ 2 replicas   │ can be rebuilt   │  │
│  ├────────────────┼───────────────┼──────────────┼───────────────────┤  │
│  │ Social Graph   │ Strong        │ Primary +    │ Follow/unfollow  │  │
│  │ (MySQL)        │ (single DC)   │ 2 replicas   │ must be correct  │  │
│  │                │ Eventual      │ + cross-DC   │                   │  │
│  │                │ (cross DC)    │ async replica │                   │  │
│  ├────────────────┼───────────────┼──────────────┼───────────────────┤  │
│  │ User Profiles  │ Strong        │ Primary +    │ Account data is  │  │
│  │ (MySQL/Aurora) │               │ 2 read       │ critical          │  │
│  │                │               │ replicas     │                   │  │
│  ├────────────────┼───────────────┼──────────────┼───────────────────┤  │
│  │ Media          │ Eventual      │ S3 cross-    │ Immutable; once  │  │
│  │ (S3)           │               │ region       │ uploaded, never  │  │
│  │                │               │ replication  │ changes           │  │
│  └────────────────┴───────────────┴──────────────┴───────────────────┘  │
│                                                                          │
└──────────────────────────────────────────────────────────────────────────┘
```

### Multi-Region Architecture

```
┌──────────────────────────────────────────────────────────────────────────┐
│                    MULTI-REGION DEPLOYMENT                                │
│                                                                          │
│   ┌─────────────────────────┐        ┌─────────────────────────┐        │
│   │    US-EAST (Primary)    │        │    EU-WEST (Secondary)  │        │
│   │                         │        │                         │        │
│   │  ┌───────────────────┐  │        │  ┌───────────────────┐  │        │
│   │  │ API + Services    │  │        │  │ API + Services    │  │        │
│   │  └─────────┬─────────┘  │        │  └─────────┬─────────┘  │        │
│   │            │             │        │            │             │        │
│   │  ┌─────────┴─────────┐  │        │  ┌─────────┴─────────┐  │        │
│   │  │ Cassandra DC1     │◄─┼────────┼──│ Cassandra DC2     │  │        │
│   │  │ (RF=3)            │──┼────────┼─►│ (RF=3)            │  │        │
│   │  └───────────────────┘  │  async │  └───────────────────┘  │        │
│   │                         │  repli │                         │        │
│   │  ┌───────────────────┐  │  cation│  ┌───────────────────┐  │        │
│   │  │ Redis Cluster     │  │        │  │ Redis Cluster     │  │        │
│   │  │ (independent)     │  │        │  │ (independent)     │  │        │
│   │  └───────────────────┘  │        │  └───────────────────┘  │        │
│   │                         │        │                         │        │
│   │  ┌───────────────────┐  │        │  ┌───────────────────┐  │        │
│   │  │ MySQL Primary     │──┼────────┼─►│ MySQL Read Replica│  │        │
│   │  └───────────────────┘  │  async │  └───────────────────┘  │        │
│   │                         │        │                         │        │
│   └─────────────────────────┘        └─────────────────────────┘        │
│                                                                          │
│   ┌─────────────────────────┐                                           │
│   │    AP-SOUTHEAST          │                                           │
│   │    (Secondary)          │                                           │
│   │                         │                                           │
│   │  Same structure as      │                                           │
│   │  EU-WEST               │                                           │
│   └─────────────────────────┘                                           │
│                                                                          │
│   Notes:                                                                 │
│   - Each region has independent Redis clusters (feeds are local)        │
│   - Cassandra replicates across DCs asynchronously                      │
│   - Users are routed to nearest region via GeoDNS                       │
│   - Feed cache is rebuilt per-region (not replicated)                   │
│   - Writes go to local DC first, then replicate                         │
│   - Cross-region lag: typically 100-500ms                                │
│                                                                          │
└──────────────────────────────────────────────────────────────────────────┘
```

### Read-After-Write Consistency

A critical requirement: when a user creates a post, they must see it in their own feed
immediately (read-your-writes consistency). Solutions:

1. **Optimistic UI**: Client adds the post to local feed immediately before server confirms.
2. **Sticky sessions**: Route the user to the same DC/replica that processed the write.
3. **Direct injection**: After successful write, the Post Service directly returns the
   post object. The client injects it into the local feed view.
4. **Write to own feed synchronously**: In the fan-out step, always write to the author's
   own feed cache synchronously (before async fan-out to followers).

---

## 12. Fault Tolerance and Failure Handling

### Failure Scenarios and Mitigations

```
┌──────────────────────────────────────────────────────────────────────────┐
│                 FAILURE SCENARIOS AND HANDLING                            │
│                                                                          │
│  ┌─────────────────────┬─────────────────────────────────────────────┐  │
│  │ Failure             │ Mitigation                                   │  │
│  ├─────────────────────┼─────────────────────────────────────────────┤  │
│  │ Redis feed cache    │ Regenerate from DB on-demand:               │  │
│  │ node dies           │ 1. Get following list                       │  │
│  │                     │ 2. Fetch recent posts from each             │  │
│  │                     │ 3. Merge, store in new Redis node           │  │
│  │                     │ Cost: ~500ms for first request, then cached │  │
│  │                     │ Redis replicas auto-promote (Sentinel/      │  │
│  │                     │ Cluster failover in ~15s)                   │  │
│  ├─────────────────────┼─────────────────────────────────────────────┤  │
│  │ Kafka broker fails  │ Kafka replication (RF=3) handles this.      │  │
│  │                     │ Consumer group rebalancing.                  │  │
│  │                     │ Fan-out paused but not lost.                │  │
│  │                     │ Feeds become stale until Kafka recovers.    │  │
│  ├─────────────────────┼─────────────────────────────────────────────┤  │
│  │ Fan-out worker      │ Kafka retains messages until consumed.      │  │
│  │ crashes mid-process │ Worker restart resumes from last committed  │  │
│  │                     │ offset. Some feeds may get duplicate         │  │
│  │                     │ entries (idempotent ZADD handles this).     │  │
│  ├─────────────────────┼─────────────────────────────────────────────┤  │
│  │ Cassandra node      │ RF=3 with LOCAL_QUORUM ensures reads/      │  │
│  │ failure             │ writes continue with 2/3 nodes available.  │  │
│  │                     │ Hinted handoff for temporary failures.      │  │
│  │                     │ Anti-entropy repair for longer outages.     │  │
│  ├─────────────────────┼─────────────────────────────────────────────┤  │
│  │ Ranking service     │ Fall back to chronological ordering.        │  │
│  │ unavailable         │ Set circuit breaker with 5s timeout.        │  │
│  │                     │ Degraded but functional experience.         │  │
│  ├─────────────────────┼─────────────────────────────────────────────┤  │
│  │ MySQL (social       │ Promote read replica to primary.            │  │
│  │ graph) primary      │ Follower lists served from Redis cache     │  │
│  │ fails               │ during failover (~30s).                     │  │
│  ├─────────────────────┼─────────────────────────────────────────────┤  │
│  │ Complete region     │ GeoDNS routes traffic to another region.   │  │
│  │ outage              │ Users see slightly stale feeds.             │  │
│  │                     │ Writes queued and replicated when region    │  │
│  │                     │ comes back.                                  │  │
│  └─────────────────────┴─────────────────────────────────────────────┘  │
│                                                                          │
└──────────────────────────────────────────────────────────────────────────┘
```

### Degraded Mode Strategy

```
┌──────────────────────────────────────────────────────────────────────────┐
│                    GRACEFUL DEGRADATION LEVELS                            │
│                                                                          │
│   Level 0: NORMAL                                                        │
│   ┌─────────────────────────────────────────────────────────┐           │
│   │  Full ranking, real-time updates, all features active   │           │
│   └─────────────────────────────────────────────────────────┘           │
│                         │                                                │
│                         ▼  (ranking service down)                        │
│   Level 1: DEGRADED RANKING                                              │
│   ┌─────────────────────────────────────────────────────────┐           │
│   │  Chronological feed (no ML ranking)                      │           │
│   │  All other features active                               │           │
│   └─────────────────────────────────────────────────────────┘           │
│                         │                                                │
│                         ▼  (feed cache partially unavailable)            │
│   Level 2: STALE FEED                                                    │
│   ┌─────────────────────────────────────────────────────────┐           │
│   │  Serve last known cached feed (may be minutes old)       │           │
│   │  Show "feed may be delayed" banner                       │           │
│   │  New posts still accepted and queued                     │           │
│   └─────────────────────────────────────────────────────────┘           │
│                         │                                                │
│                         ▼  (primary DB also degraded)                    │
│   Level 3: READ-ONLY MODE                                               │
│   ┌─────────────────────────────────────────────────────────┐           │
│   │  Serve whatever cached data is available                 │           │
│   │  Disable post creation, likes, comments                  │           │
│   │  Show "limited functionality" banner                     │           │
│   └─────────────────────────────────────────────────────────┘           │
│                         │                                                │
│                         ▼  (catastrophic failure)                        │
│   Level 4: MAINTENANCE PAGE                                              │
│   ┌─────────────────────────────────────────────────────────┐           │
│   │  Static page from CDN: "We'll be back soon"             │           │
│   └─────────────────────────────────────────────────────────┘           │
│                                                                          │
└──────────────────────────────────────────────────────────────────────────┘
```

### Idempotency in Fan-out

Fan-out operations must be idempotent because Kafka consumers can receive the same
message multiple times (at-least-once delivery):

```
Operation: ZADD feed:{follower_id} <timestamp> <post_id>

ZADD is naturally idempotent:
  - If post_id already exists in the sorted set, the score is updated.
  - If it doesn't exist, it is added.
  - Running ZADD twice with the same args = same result.
  - This makes the fan-out worker safe to retry without side effects.
```

---

## 13. Scalability

### Horizontal Scaling Strategy

```
┌──────────────────────────────────────────────────────────────────────────┐
│                    SCALABILITY DIMENSIONS                                 │
│                                                                          │
│  ┌─────────────────────────────────────────────────────────────────┐    │
│  │  Component         │ Scaling Strategy           │ Scale Target  │    │
│  ├─────────────────────┼────────────────────────────┼───────────────┤    │
│  │  API Gateway        │ Horizontal (stateless)    │ 50-200 nodes  │    │
│  │  Post Service       │ Horizontal (stateless)    │ 100+ nodes    │    │
│  │  Feed Service       │ Horizontal (stateless)    │ 200+ nodes    │    │
│  │  Fan-out Workers    │ Horizontal (Kafka CG)     │ 500-2000      │    │
│  │  Ranking Service    │ GPU-backed, horizontal    │ 100+ nodes    │    │
│  │  Redis Cluster      │ Add shards + replicas     │ 100+ nodes    │    │
│  │  Cassandra          │ Add nodes to ring         │ 200+ nodes    │    │
│  │  MySQL              │ Add shards (Vitess)       │ 256+ shards   │    │
│  │  Kafka              │ Add brokers + partitions  │ 50+ brokers   │    │
│  └─────────────────────┴────────────────────────────┴───────────────┘    │
│                                                                          │
└──────────────────────────────────────────────────────────────────────────┘
```

### Fan-out Worker Scaling

```
┌──────────────────────────────────────────────────────────────────────────┐
│                    FAN-OUT WORKER SCALING                                 │
│                                                                          │
│  Kafka Topic: "new-posts"                                                │
│  Partitions: 256                                                         │
│  Consumer Group: "fanout-workers"                                        │
│                                                                          │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐       ┌──────────┐           │
│  │Partition 0│  │Partition 1│  │Partition 2│  ...  │Partition │           │
│  │          │  │          │  │          │       │   255    │           │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘       └────┬─────┘           │
│       │              │              │                   │                │
│       ▼              ▼              ▼                   ▼                │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐       ┌──────────┐           │
│  │ Worker 0 │  │ Worker 1 │  │ Worker 2 │  ...  │Worker 255│           │
│  └──────────┘  └──────────┘  └──────────┘       └──────────┘           │
│                                                                          │
│  Each worker:                                                            │
│  1. Consumes a post event from its partition                             │
│  2. Looks up author's follower list (Redis cache → MySQL fallback)      │
│  3. For non-celebrity authors:                                           │
│     - Batch ZADD to each follower's feed cache                          │
│     - Pipeline Redis commands (100 ZADDs per pipeline)                  │
│     - ~1000 followers/sec per worker                                     │
│  4. Commits Kafka offset after all followers processed                   │
│                                                                          │
│  Scaling rule:                                                           │
│  - Max workers = number of Kafka partitions                              │
│  - If fan-out lag > 5 seconds: add partitions + workers                 │
│  - Auto-scale based on consumer lag metric                               │
│                                                                          │
│  Optimization: Batch fan-out                                             │
│  - Buffer 100ms of posts, then fan-out in batches                        │
│  - Reduces Redis round trips via pipelining                              │
│  - 10x throughput improvement over single-post fan-out                   │
│                                                                          │
└──────────────────────────────────────────────────────────────────────────┘
```

### Handling Traffic Spikes (Viral Posts)

```
┌──────────────────────────────────────────────────────────────────────────┐
│                    VIRAL POST HANDLING                                    │
│                                                                          │
│  Scenario: A post goes viral -- 1M likes in 1 hour                      │
│                                                                          │
│  Problem: Counter hotspot on single Redis key likes:{post_id}           │
│                                                                          │
│  Solution: Distributed counters                                          │
│  ┌──────────────────────────────────────────────────────────┐            │
│  │                                                          │            │
│  │  Instead of: INCR likes:post_abc                         │            │
│  │                                                          │            │
│  │  Use N counter shards:                                   │            │
│  │    INCR likes:post_abc:shard_0                           │            │
│  │    INCR likes:post_abc:shard_1                           │            │
│  │    ...                                                   │            │
│  │    INCR likes:post_abc:shard_15                          │            │
│  │                                                          │            │
│  │  Read: SUM(all shards) -- mget + sum                     │            │
│  │  Write: random shard assignment                           │            │
│  │                                                          │            │
│  │  16 shards → 16x write throughput                        │            │
│  │  Read cost: 16 gets instead of 1 (still fast with mget) │            │
│  │                                                          │            │
│  └──────────────────────────────────────────────────────────┘            │
│                                                                          │
│  Additional mitigation:                                                  │
│  - Rate limit like/comment API per user (200/hour)                      │
│  - Circuit breaker on fan-out for viral posts                            │
│  - Pre-warm popular posts in all cache layers                            │
│  - Async counter sync to DB (batch every 30s)                            │
│                                                                          │
└──────────────────────────────────────────────────────────────────────────┘
```

---

## 14. Monitoring and Observability

### Key Metrics Dashboard

```
┌──────────────────────────────────────────────────────────────────────────┐
│                    MONITORING & OBSERVABILITY                             │
│                                                                          │
│  ┌─────────────────────────────────────────────────────────────────┐    │
│  │                 TIER 1: BUSINESS METRICS (SLOs)                  │    │
│  ├─────────────────────────────────────────────────────────────────┤    │
│  │  Feed latency P50 / P95 / P99           Target: 50/150/200ms   │    │
│  │  Feed generation success rate           Target: 99.99%          │    │
│  │  Post creation success rate             Target: 99.95%          │    │
│  │  Feed freshness (age of newest post)    Target: < 30s           │    │
│  └─────────────────────────────────────────────────────────────────┘    │
│                                                                          │
│  ┌─────────────────────────────────────────────────────────────────┐    │
│  │                 TIER 2: SYSTEM METRICS                            │    │
│  ├─────────────────────────────────────────────────────────────────┤    │
│  │  Fan-out lag (Kafka consumer lag)       Alert: > 5 sec          │    │
│  │  Redis cache hit ratio                  Alert: < 85%            │    │
│  │  Redis memory utilization               Alert: > 80%            │    │
│  │  Cassandra read/write latency P99       Alert: > 50ms           │    │
│  │  Kafka partition lag                    Alert: > 10K messages   │    │
│  │  API error rate (5xx)                   Alert: > 0.1%           │    │
│  │  Post creation QPS                      Monitor trend           │    │
│  │  Feed read QPS                          Monitor trend           │    │
│  └─────────────────────────────────────────────────────────────────┘    │
│                                                                          │
│  ┌─────────────────────────────────────────────────────────────────┐    │
│  │                 TIER 3: INFRASTRUCTURE METRICS                   │    │
│  ├─────────────────────────────────────────────────────────────────┤    │
│  │  CPU / Memory / Network across all services                     │    │
│  │  Disk I/O on Cassandra / MySQL nodes                            │    │
│  │  Connection pool utilization                                    │    │
│  │  GC pause times (JVM services)                                  │    │
│  │  Thread pool queue sizes                                        │    │
│  └─────────────────────────────────────────────────────────────────┘    │
│                                                                          │
│  Observability Stack:                                                    │
│  ┌───────────────┬────────────────────────────────────────────────┐     │
│  │ Metrics       │ Prometheus + Grafana                           │     │
│  │ Logging       │ ELK Stack (Elasticsearch, Logstash, Kibana)   │     │
│  │ Tracing       │ Jaeger / Zipkin (distributed tracing)         │     │
│  │ Alerting      │ PagerDuty + Grafana Alerts                    │     │
│  │ Dashboards    │ Real-time feed health dashboard               │     │
│  └───────────────┴────────────────────────────────────────────────┘     │
│                                                                          │
└──────────────────────────────────────────────────────────────────────────┘
```

### Distributed Tracing Example

```
┌──────────────────────────────────────────────────────────────────────────┐
│          TRACE: GET /v1/feed (200 OK, 142ms total)                       │
│                                                                          │
│  ├── API Gateway (auth + routing)                    [0ms - 8ms]        │
│  │                                                                       │
│  ├── Feed Service                                    [8ms - 140ms]      │
│  │   │                                                                   │
│  │   ├── Redis: ZREVRANGEBYSCORE feed:user_123       [10ms - 14ms]     │
│  │   │   └── 45 post IDs returned                                       │
│  │   │                                                                   │
│  │   ├── Redis: GET celebrity_followees:user_123     [14ms - 16ms]     │
│  │   │   └── [celeb_A, celeb_B] returned                                │
│  │   │                                                                   │
│  │   ├── Cassandra: SELECT posts WHERE author_id     [16ms - 35ms]     │
│  │   │   IN (celeb_A, celeb_B)                                          │
│  │   │   └── 8 celebrity posts returned                                  │
│  │   │                                                                   │
│  │   ├── Redis: MGET post:p1, post:p2, ...           [35ms - 42ms]     │
│  │   │   └── 48 post objects (5 cache misses)                           │
│  │   │                                                                   │
│  │   ├── Cassandra: SELECT posts WHERE post_id       [42ms - 55ms]     │
│  │   │   IN (5 cache misses)                                             │
│  │   │                                                                   │
│  │   ├── Ranking Service: score(53 posts, user_feat) [55ms - 120ms]    │
│  │   │   └── ML inference, 53 candidates scored                         │
│  │   │                                                                   │
│  │   └── Serialize + paginate top 20                 [120ms - 138ms]   │
│  │                                                                       │
│  └── Response serialization                          [138ms - 142ms]   │
│                                                                          │
└──────────────────────────────────────────────────────────────────────────┘
```

---

## 15. Trade-offs and Design Decisions

### Decision 1: Fan-out Strategy

```
┌──────────────────────────────────────────────────────────────────────────┐
│  DECISION: Use hybrid fan-out (push for normal, pull for celebrities)   │
│                                                                          │
│  Alternatives Considered:                                                │
│  ┌──────────────────────┬──────────────┬────────────────────────────┐   │
│  │ Option               │ Rejected?    │ Reason                      │   │
│  ├──────────────────────┼──────────────┼────────────────────────────┤   │
│  │ Pure push (fan-out   │ Yes          │ Celebrity problem makes    │   │
│  │ on write)            │              │ this O(100M) per post.     │   │
│  │                      │              │ Unsustainable at scale.    │   │
│  ├──────────────────────┼──────────────┼────────────────────────────┤   │
│  │ Pure pull (fan-out   │ Yes          │ Every feed read requires   │   │
│  │ on read)             │              │ querying 300 partitions.   │   │
│  │                      │              │ P99 latency too high.      │   │
│  ├──────────────────────┼──────────────┼────────────────────────────┤   │
│  │ Hybrid (selected)    │ No           │ Best of both: fast reads   │   │
│  │                      │              │ + manageable writes.       │   │
│  │                      │              │ Complexity is worth it.    │   │
│  └──────────────────────┴──────────────┴────────────────────────────┘   │
│                                                                          │
└──────────────────────────────────────────────────────────────────────────┘
```

### Decision 2: Feed Ranking

```
┌──────────────────────────────────────────────────────────────────────────┐
│  DECISION: ML-based ranking with chronological fallback                  │
│                                                                          │
│  ┌─────────────────────┬─────────────────────────────────────────────┐  │
│  │ Chronological       │ Simpler, transparent, but lower engagement  │  │
│  │                     │ and important posts get buried.             │  │
│  ├─────────────────────┼─────────────────────────────────────────────┤  │
│  │ ML-ranked           │ Higher engagement (+15-30%), but opaque,   │  │
│  │ (selected)          │ requires ML infra, cold start problem.     │  │
│  ├─────────────────────┼─────────────────────────────────────────────┤  │
│  │ User-togglable      │ Best UX but doubles serving complexity.    │  │
│  │ (nice to have)      │ Twitter offers this as an option.          │  │
│  └─────────────────────┴─────────────────────────────────────────────┘  │
│                                                                          │
│  Fallback: If ranking service is down, serve chronological feed.        │
│  This is a circuit-breaker-protected degradation.                       │
│                                                                          │
└──────────────────────────────────────────────────────────────────────────┘
```

### Decision 3: Pre-compute vs On-Demand Feed

```
┌──────────────────────────────────────────────────────────────────────────┐
│  DECISION: Pre-compute feeds in Redis with on-demand fallback            │
│                                                                          │
│  ┌─────────────────────┬──────────────────────┬──────────────────────┐  │
│  │ Dimension           │ Pre-computed         │ On-Demand            │  │
│  ├─────────────────────┼──────────────────────┼──────────────────────┤  │
│  │ Read latency        │ ~5ms (Redis ZRANGE)  │ ~200-500ms           │  │
│  │ Write cost          │ Fan-out per post     │ None                 │  │
│  │ Storage             │ ~6 TB Redis          │ Minimal              │  │
│  │ Freshness           │ Near real-time       │ Always fresh         │  │
│  │ Wasted computation  │ Inactive users       │ None                 │  │
│  │ Cache miss penalty  │ High (rebuild feed)  │ N/A                  │  │
│  └─────────────────────┴──────────────────────┴──────────────────────┘  │
│                                                                          │
│  Selected: Pre-computed with on-demand rebuild as fallback               │
│  Rationale: Read-heavy workload (5B reads vs 1B writes/day)             │
│  The 6 TB Redis cost is justified by the 100x read latency improvement. │
│                                                                          │
└──────────────────────────────────────────────────────────────────────────┘
```

### Decision 4: Database Selection for Posts

```
┌──────────────────────────────────────────────────────────────────────────┐
│  DECISION: Cassandra for posts (over DynamoDB, MongoDB, PostgreSQL)      │
│                                                                          │
│  ┌──────────────┬──────────────────────────────────────────────────┐    │
│  │ Cassandra    │ ✓ Linear horizontal scaling                     │    │
│  │ (selected)   │ ✓ Tunable consistency (LOCAL_QUORUM)            │    │
│  │              │ ✓ Time-series friendly (clustering by timestamp)│    │
│  │              │ ✓ Multi-DC replication built-in                 │    │
│  │              │ ✗ No secondary indexes (need materialized views)│    │
│  │              │ ✗ Operational complexity                        │    │
│  ├──────────────┼──────────────────────────────────────────────────┤    │
│  │ DynamoDB     │ ✓ Managed (less ops)                            │    │
│  │              │ ✓ Auto-scaling                                  │    │
│  │              │ ✗ AWS vendor lock-in                            │    │
│  │              │ ✗ Expensive at this scale                       │    │
│  ├──────────────┼──────────────────────────────────────────────────┤    │
│  │ PostgreSQL   │ ✓ Rich queries, ACID                            │    │
│  │              │ ✗ Does not scale writes horizontally             │    │
│  │              │ ✗ Cannot handle 35K writes/sec natively         │    │
│  └──────────────┴──────────────────────────────────────────────────┘    │
│                                                                          │
└──────────────────────────────────────────────────────────────────────────┘
```

### Decision 5: Cursor-Based vs Offset-Based Pagination

| Factor              | Cursor-Based (selected) | Offset-Based              |
|---------------------|-------------------------|---------------------------|
| Stability           | Stable on inserts       | Rows shift on inserts     |
| Performance         | O(1) with index         | O(offset) scan            |
| Infinite scroll     | Perfect fit             | Works but fragile         |
| Jump to page N      | Not supported           | Supported                 |
| Cache-friendliness  | High (immutable cursor) | Low (offset changes)      |

**Selected**: Cursor-based because feeds are infinite-scroll UIs where jump-to-page
is not needed, and data changes constantly.

---

## 16. Interview Deep-Dive Questions

### Q1: How do you handle the celebrity problem?

**Answer:** Use the hybrid fan-out approach. Maintain a threshold (e.g., 10K followers).
Users below the threshold: fan-out on write (push their posts to all followers' feed
caches). Users above the threshold: fan-out on read (store the post only, and merge it
into the feed at read time). The `is_celebrity` flag on the user record controls the
routing. At read time, the Feed Service fetches the user's pre-computed feed from Redis,
then separately pulls recent posts from the ~5-10 celebrities the user follows, merges
them, ranks, and returns. The extra 5-10 Cassandra queries add ~20ms, well within the
200ms budget.

---

### Q2: What happens when a user unfollows someone?

**Answer:** Three things must happen:
1. **Social graph update**: Delete the follow edge in MySQL (or soft-delete).
2. **Cache invalidation**: Invalidate the follower list cache in Redis for both users.
3. **Feed cleanup (async)**: A Kafka event triggers a worker to scan the unfollower's
   feed cache and remove all post_ids from the unfollowed user. This is done via
   `ZRANGEBYSCORE` + `ZREM` and can be deferred (seconds-level delay is acceptable).

If the unfollowed user is a celebrity, no feed cleanup is needed because their posts
were never pushed -- they are simply no longer pulled at read time.

---

### Q3: How do you handle deleted or hidden posts in pre-computed feeds?

**Answer:** Two strategies work together:
1. **Lazy deletion**: When a post is deleted, set `is_deleted = true` in Cassandra and
   publish a deletion event to Kafka. Fan-out workers remove the post_id from all
   followers' feed caches (same as fan-out but in reverse -- this is also a push
   operation). Since feeds only store post_ids, the actual deletion is a simple `ZREM`.
2. **Read-time filtering**: As a safety net, when hydrating post_ids into full objects,
   check the `is_deleted` flag. If true, skip the post. This handles the window between
   deletion and cache cleanup.

---

### Q4: How do you rank posts for new users with no interaction history?

**Answer:** Cold start problem. Solutions:
1. **Default ranking signals**: Use non-personalized signals: post recency, global
   engagement rate (likes/impressions), author popularity, media type preferences
   from demographic data.
2. **Explore/exploit**: Show a diverse mix of content types and track what the new user
   interacts with. After ~20-30 interactions, the model starts personalizing.
3. **Onboarding flow**: Ask users to pick topics/interests during signup. Use these
   as initial features.
4. **Social bootstrapping**: If the user imported contacts or follows some accounts,
   use "users similar to you liked these posts" collaborative filtering.

---

### Q5: How do you prevent feed staleness?

**Answer:** Multiple mechanisms:
1. **Pull-refresh**: Client polls every 30-60 seconds (or on user scroll-to-top).
2. **WebSocket/SSE**: Maintain a persistent connection for real-time updates. When a
   new post is added to the user's feed cache, send a "new posts available" signal.
   The client shows a "N new posts" banner.
3. **Feed TTL**: Feed cache entries have TTL. If a user is inactive for 7 days, the
   feed cache expires and is rebuilt on next visit.
4. **Background refresh**: For highly active users, a background job re-ranks their
   feed every few minutes to ensure the "best" posts float to the top.

---

### Q6: How does the system handle a Kafka outage? Will users not see new posts?

**Answer:** During a Kafka outage:
1. **Post creation still works**: Posts are written to Cassandra synchronously. The
   Kafka publish is async. If Kafka is down, the post is persisted but fan-out is
   paused.
2. **Feeds become stale**: New posts from non-celebrity users won't appear in
   followers' feeds until Kafka recovers and fan-out catches up.
3. **Fallback**: The Feed Service can detect fan-out lag. If lag exceeds a threshold
   (e.g., 5 minutes), it temporarily switches to pull-based feed generation for all
   users -- querying Cassandra directly for recent posts from followed users.
4. **Recovery**: When Kafka recovers, consumer group rebalancing resumes processing
   from the last committed offset. Backlog is processed at accelerated speed.

---

### Q7: How do you handle pagination when the feed is being modified concurrently?

**Answer:** Cursor-based pagination with composite cursor = `(timestamp, post_id)`.
When the user requests the next page, the cursor points to the exact position in the
sorted set. Even if new posts are inserted (higher timestamps), the cursor is stable
because it uses `ZREVRANGEBYSCORE (cursor_ts) -inf LIMIT 0 20` -- it always fetches
posts *older* than the cursor. New posts appear when the user scrolls back to the top,
not in the middle of their scroll. This gives a consistent reading experience.

---

### Q8: What if a user follows 10,000 accounts? How does fan-out on read scale?

**Answer:** In the hybrid model, only celebrity posts are pulled at read time. A user
following 10,000 accounts might follow ~50-100 celebrities (10K+ follower threshold).
The pull query fetches recent posts from each celebrity's timeline in parallel (50-100
Cassandra queries). With async I/O and connection pooling, this completes in ~30-50ms.
Posts from the other 9,900+ non-celebrity accounts are already in the pre-computed feed
cache via push. The merge step combines both sources and ranks them.

If even 100 pull queries is too slow, we can cache the "merged celebrity feed" for
each user with a short TTL (~60 seconds), avoiding repeated Cassandra hits.

---

### Q9: How do you handle media (images/videos) in posts?

**Answer:** Media is handled separately from text to avoid bloating the feed pipeline:
1. **Upload**: Client uploads media to the Media Service *before* creating the post.
   The Media Service stores the file in S3 and returns a `media_id`.
2. **Transcoding**: An async pipeline (triggered via SQS/Kafka) transcodes images to
   multiple sizes (thumbnail, medium, full) and videos to multiple bitrates. Stored
   in S3 with deterministic URLs.
3. **CDN**: All media is served via CloudFront/Akamai. URLs are immutable (content-
   addressed), so cache TTLs can be infinite.
4. **Feed integration**: The post object only stores `media_ids`. At hydration time,
   the Feed Service resolves `media_ids` to CDN URLs (simple lookup, cacheable).
5. **Lazy loading**: The client renders text first, then loads media progressively.

---

### Q10: How do you implement trending topics?

**Answer:** Trending is computed from a real-time event stream:
1. **Event stream**: Every post creation publishes hashtags to a Kafka topic
   `post-events`.
2. **Sliding window aggregation**: A Flink/Spark Streaming job maintains a sliding
   window (e.g., last 1 hour, 4 hours, 24 hours) counting hashtag occurrences.
3. **Trend detection**: A hashtag is "trending" if its current frequency significantly
   exceeds its historical baseline (z-score > 2.0). This filters out always-popular
   tags like #love and surfaces genuinely spiking topics.
4. **Regional trending**: Trending is computed per-region using the user's location
   from the post metadata.
5. **Caching**: Trending lists are computed every 5 minutes and cached in Redis with
   a 5-minute TTL. No real-time requirement -- a few minutes of staleness is fine.

---

### Q11: How do you handle a user who has been inactive for months and returns?

**Answer:** Their feed cache has likely expired (7-day TTL). On their first request:
1. **Cache miss detected**: Redis returns empty for `feed:{user_id}`.
2. **On-demand rebuild**: Feed Service fetches the user's following list, queries
   recent posts from each followed user (last 24-48 hours), merges them, and stores
   the result in Redis.
3. **Performance**: This rebuild takes 200-500ms (higher than the normal 50ms), but
   it only happens once. Subsequent requests are served from cache.
4. **Optimization**: For the initial load, show the top 20 posts from the rebuild
   immediately while the full 500-post cache is populated asynchronously.

---

### Q12: How do you prevent spam in the news feed?

**Answer:** Multi-layered approach:
1. **Rate limiting**: Post creation capped at 50/hour per user.
2. **Content filtering**: NLP-based spam detection at post creation time (block known
   spam patterns, URLs, excessive hashtags).
3. **Behavioral signals**: Accounts that post identical content, follow/unfollow
   rapidly, or have low engagement ratios are flagged.
4. **User reporting**: "Report spam" adds negative signals to the ranking model,
   reducing the post's visibility.
5. **Throttled fan-out**: New accounts have limited fan-out (posts not pushed to all
   followers until the account is N days old or verified).

---

### Q13: How would you add "Stories" (ephemeral content) to this system?

**Answer:** Stories differ from feed posts in two key ways: they expire after 24 hours
and are displayed in a separate UI (horizontal scroll). The architecture adapts:
1. **Separate storage**: Stories go in a Redis sorted set per user with TTL=24h.
   No Cassandra persistence needed.
2. **Separate feed**: Stories feed is a simple aggregation of followed users who have
   active stories. No ranking needed -- just chronological per-user.
3. **Fan-out**: Same hybrid approach. Normal users push, celebrities pull.
4. **Compact payload**: Stories are just media_ids + timestamps. Very lightweight.
5. **View tracking**: Track which stories a user has seen (Redis bitmap per user per
   day) to show the unread indicator.

---

### Q14: How do you ensure data consistency when the same post is stored in Cassandra and cached in Redis?

**Answer:** The post in Cassandra is the source of truth. Redis caches are derived views.
1. **Write path**: Write to Cassandra first (synchronous), then update Redis (async).
   If Redis update fails, the cache has stale data but will expire via TTL.
2. **Read path**: Always try Redis first (fast). On cache miss, read from Cassandra
   and populate Redis.
3. **Inconsistency window**: Between a Cassandra write and Redis update, there is a
   brief window (~10-100ms) where Redis has stale data. This is acceptable for a
   feed system (eventual consistency).
4. **Counter consistency**: Like/comment counts are incremented in Redis atomically
   and async-synced to Cassandra every 30 seconds. The Redis value is the "hot" value
   shown to users. If Redis loses data, the last-synced Cassandra value is used.

---

### Q15: How would you design the system differently if the requirement changed to a bidirectional "friend" model (like Facebook) instead of unidirectional "follow" (like Twitter)?

**Answer:** Key differences:
1. **Social graph**: The follows table becomes symmetric. A friendship is a single
   edge, not two directional edges. This halves storage but adds complexity for
   friend requests (pending/accepted states).
2. **Fan-out volume**: Friend counts are typically lower than follower counts
   (avg 300 friends vs. potentially millions of followers). This makes pure fan-out
   on write more viable -- no celebrity problem if friend count is capped at ~5,000.
3. **Privacy**: Every post has an implicit "friends only" visibility. No public posts
   by default. This simplifies ranking (no need to handle public viral content).
4. **Feed diversity**: With fewer sources (~300 friends vs. potentially 10K+ follows),
   feed diversity is lower. Ranking must balance showing enough from each friend
   without being repetitive.
5. **Fan-out strategy**: Pure push becomes feasible because max friends ~5K means
   max 5K writes per post. No need for the hybrid model.

---

## Summary

```
┌──────────────────────────────────────────────────────────────────────────┐
│                    NEWS FEED SYSTEM: KEY TAKEAWAYS                        │
│                                                                          │
│  1. HYBRID FAN-OUT is the production-grade solution.                    │
│     Push for normal users, pull for celebrities.                        │
│                                                                          │
│  2. PRE-COMPUTED FEEDS in Redis give sub-10ms reads.                    │
│     On-demand rebuild as fallback for cache misses.                     │
│                                                                          │
│  3. ML-BASED RANKING maximizes engagement.                               │
│     Chronological as fallback for ranking service failures.             │
│                                                                          │
│  4. CASSANDRA for posts (write throughput + multi-DC).                  │
│     Redis for caches. MySQL for relational data.                        │
│                                                                          │
│  5. KAFKA decouples post creation from fan-out.                         │
│     Enables async, scalable, retryable fan-out.                         │
│                                                                          │
│  6. EVENTUAL CONSISTENCY is acceptable for feeds.                        │
│     Strong consistency only for post writes and account data.           │
│                                                                          │
│  7. GRACEFUL DEGRADATION through circuit breakers.                       │
│     Always serve something, even if stale.                               │
│                                                                          │
│  8. The CELEBRITY PROBLEM is the defining challenge.                     │
│     Everything else is standard distributed systems.                    │
│                                                                          │
└──────────────────────────────────────────────────────────────────────────┘
```

---

*Last updated: 2026-04-09*
