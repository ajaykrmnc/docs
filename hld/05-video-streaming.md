# Design a Video Streaming Platform (YouTube / Netflix)

**Difficulty:** Hard | **Companies:** Google, Netflix, Amazon, Meta, Apple

---

## 1. Problem Statement and Scope

Design a globally distributed video streaming platform that supports video upload,
transcoding, storage, and adaptive bitrate streaming to hundreds of millions of
concurrent viewers. The system must handle the full lifecycle of video content --
from the moment a creator uploads a raw file to the instant a viewer presses play
on any device, anywhere in the world.

### In Scope

- Video upload (resumable, chunked) with progress tracking
- Video transcoding pipeline (multiple resolutions and codecs)
- On-demand video streaming with adaptive bitrate (ABR)
- Video search, discovery, and recommendation
- User interactions: likes, comments, subscriptions, playlists
- Content moderation and copyright detection
- Live streaming (extension)
- Analytics and view counting
- Global CDN distribution

### Out of Scope

- Payment/subscription billing (Stripe/payment gateway integration)
- Detailed ad-serving pipeline (ad tech is its own system)
- Creator Studio analytics dashboard (BI system)
- Social features beyond comments (messaging, community posts)

---

## 2. Functional Requirements

| # | Requirement                  | Description                                                        |
|---|------------------------------|--------------------------------------------------------------------|
| 1 | Upload videos                | Creators upload videos up to 12 hours / 256GB via resumable upload |
| 2 | Stream/watch videos          | Viewers watch on-demand with instant playback start                |
| 3 | Adaptive bitrate streaming   | Automatic quality adjustment based on network conditions            |
| 4 | Video quality selection       | Manual override to choose 240p through 4K                          |
| 5 | Search videos                | Full-text search on titles, descriptions, tags, captions           |
| 6 | Like / dislike videos        | Engagement signals stored per user per video                       |
| 7 | Comment on videos            | Threaded comments with pagination                                  |
| 8 | Subscribe to channels        | Follow creators, get feed updates                                  |
| 9 | Recommendations              | Personalized home feed and "up next" suggestions                   |
| 10| Playlists                    | User-created ordered video collections                             |
| 11| Video thumbnails             | Auto-generated + custom upload thumbnails                          |
| 12| Live streaming               | Real-time broadcast to large audiences                             |
| 13| Content moderation           | Automated + manual review for policy violations                    |
| 14| Copyright detection          | Content ID / fingerprinting for copyrighted material               |

---

## 3. Non-Functional Requirements

| Requirement            | Target                                                          |
|------------------------|-----------------------------------------------------------------|
| Playback start latency | < 2 seconds (time to first frame)                               |
| Rebuffering ratio      | < 0.5% of total playback time                                   |
| Availability           | 99.99% (< 52.6 minutes downtime/year)                           |
| Upload success rate    | > 99.5% for files under 10GB                                    |
| Global distribution    | Content served from edge within 50ms RTT of 95% of users        |
| Scale                  | 100M+ daily video views, 800M DAU                               |
| Transcoding latency    | < 30 minutes for a 1-hour video (all resolutions)               |
| Search latency         | < 200ms p99                                                     |
| Storage durability     | 99.999999999% (11 nines, matching S3)                           |
| Content moderation     | Automated scan within 10 minutes of upload                      |
| Consistency            | Eventual consistency acceptable for views/likes; strong for uploads |

---

## 4. Back-of-Envelope Estimation

### Traffic Estimates

```
DAU:                     800M users
Videos watched/user/day: 5
Total daily views:       800M * 5 = 4 Billion views/day
Views per second:        4B / 86400 = ~46,000 views/sec
Peak views/sec:          ~46K * 3 (peak multiplier) = ~140K views/sec

Uploads per day:         500K new videos/day
Uploads per second:      500K / 86400 = ~6 uploads/sec
Peak uploads/sec:        ~18 uploads/sec
```

### Storage Estimates

```
Average raw upload size:       1 GB
Transcoded output per video:   5 resolutions * avg 60MB each = 300MB total
                               (240p: 15MB, 360p: 30MB, 480p: 50MB,
                                720p: 80MB, 1080p: 125MB)
4K videos (10% of uploads):   Additional 500MB per 4K video

Daily new storage:
  Base: 500K * 300MB          = 150 TB/day
  4K:   50K * 500MB           = 25 TB/day
  Thumbnails: 500K * 5 * 50KB = 125 GB/day (5 thumbnails per video)
  Total:                      ~175 TB/day

Annual storage:               175 TB * 365 = ~64 PB/year
After 5 years:                ~320 PB total
```

### Bandwidth Estimates

```
Average video duration:       3 minutes
Average bitrate served:       5 Mbps (mix of qualities)
Data per view:                5 Mbps * 180 sec / 8 = ~112 MB per view

Daily egress:                 4B * 112 MB = ~448 PB/day
Peak egress bandwidth:        448 PB / 86400 * 3 (peak) = ~155 Tbps peak

CDN cache hit ratio target:   > 95%
Origin bandwidth:             155 Tbps * 0.05 = ~7.8 Tbps from origin
```

### Compute Estimates (Transcoding)

```
Transcoding time per video:
  1 hour video, single resolution = ~30 min on modern hardware
  5 resolutions = ~2.5 hours of compute per video (parallelized to ~30 min)

Daily transcoding compute:
  500K videos * 2.5 hours = 1.25M compute-hours/day
  = ~52,000 concurrent transcoding workers (if each runs 24h)
  With spot/preemptible: target ~20,000 workers at peak
```

### Summary Table

| Metric                  | Value              |
|-------------------------|--------------------|
| DAU                     | 800M               |
| Daily video views       | 4 Billion          |
| Views/sec (avg / peak)  | 46K / 140K         |
| Daily uploads           | 500K videos        |
| Daily new storage       | ~175 TB            |
| Daily egress bandwidth  | ~448 PB            |
| Peak egress             | ~155 Tbps          |
| CDN cache hit target    | > 95%              |
| Transcoding workers     | ~20K concurrent    |

---

## 5. API Design

### 5.1 Video Upload

```
POST /v1/videos/upload/initiate
Headers:
  Authorization: Bearer <token>
  Content-Type: application/json
Body:
{
  "title": "My Video",
  "description": "A great video about...",
  "tags": ["tutorial", "coding"],
  "visibility": "public",           // public | unlisted | private
  "file_size_bytes": 1073741824,     // 1GB
  "file_type": "video/mp4",
  "thumbnail": "<base64 or URL>"     // optional custom thumbnail
}
Response 201:
{
  "video_id": "v_abc123",
  "upload_url": "https://upload.streamcdn.com/v_abc123",
  "upload_token": "tok_xyz789",
  "chunk_size": 8388608,             // 8MB recommended chunk size
  "expires_at": "2026-04-09T13:00:00Z"
}
```

```
PUT /v1/videos/upload/{video_id}/chunks/{chunk_number}
Headers:
  Authorization: Bearer <token>
  Content-Range: bytes 0-8388607/1073741824
  Content-Type: application/octet-stream
  X-Upload-Token: tok_xyz789
Body: <binary chunk data>
Response 200:
{
  "chunk_number": 0,
  "bytes_received": 8388608,
  "total_received": 8388608,
  "status": "uploading"              // uploading | processing | complete
}
```

```
POST /v1/videos/upload/{video_id}/complete
Headers:
  Authorization: Bearer <token>
Body:
{
  "upload_token": "tok_xyz789",
  "checksum_sha256": "a1b2c3d4..."
}
Response 200:
{
  "video_id": "v_abc123",
  "status": "processing",
  "estimated_ready_at": "2026-04-09T12:45:00Z"
}
```

### 5.2 Video Streaming

```
GET /v1/videos/{video_id}/manifest.m3u8
Headers:
  Authorization: Bearer <token>      // optional for public videos
Response 200:
  Content-Type: application/vnd.apple.mpegurl
  #EXTM3U
  #EXT-X-STREAM-INF:BANDWIDTH=800000,RESOLUTION=640x360
  360p/playlist.m3u8
  #EXT-X-STREAM-INF:BANDWIDTH=1400000,RESOLUTION=854x480
  480p/playlist.m3u8
  #EXT-X-STREAM-INF:BANDWIDTH=2800000,RESOLUTION=1280x720
  720p/playlist.m3u8
  #EXT-X-STREAM-INF:BANDWIDTH=5000000,RESOLUTION=1920x1080
  1080p/playlist.m3u8
```

```
GET /v1/videos/{video_id}/segments/{quality}/{segment_number}.ts
Headers:
  Range: bytes=0-1048575              // optional range request
Response 200/206:
  Content-Type: video/MP2T
  <binary segment data>
```

### 5.3 Video Metadata and Interactions

```
GET /v1/videos/{video_id}
Response 200:
{
  "video_id": "v_abc123",
  "title": "My Video",
  "description": "...",
  "channel": { "id": "ch_456", "name": "TechCreator" },
  "duration_seconds": 624,
  "view_count": 1542387,
  "like_count": 45200,
  "published_at": "2026-04-01T10:00:00Z",
  "thumbnails": {
    "default": "https://cdn.stream.com/thumbs/v_abc123/default.jpg",
    "medium": "https://cdn.stream.com/thumbs/v_abc123/medium.jpg",
    "high": "https://cdn.stream.com/thumbs/v_abc123/high.jpg"
  },
  "available_qualities": ["240p","360p","480p","720p","1080p"],
  "tags": ["tutorial", "coding"]
}
```

```
GET /v1/videos/search?q=system+design&page=1&page_size=20&sort=relevance
POST /v1/videos/{video_id}/like          // toggle like
DELETE /v1/videos/{video_id}/like        // remove like
POST /v1/videos/{video_id}/comments      // add comment
GET /v1/videos/{video_id}/comments?page=1&sort=top
GET /v1/users/{user_id}/feed?page=1      // subscription feed
GET /v1/videos/recommendations?video_id={id}&count=20  // related videos
GET /v1/home/feed?page=1                 // personalized home feed
```

---

## 6. Data Model and Database Selection

### 6.1 Data Models

**Video Metadata**
```
videos {
  video_id         VARCHAR(16) PK       -- globally unique, base62 encoded
  creator_id       VARCHAR(16) FK       -- references users.user_id
  title            VARCHAR(500)
  description      TEXT
  duration_seconds INT
  status           ENUM('uploading','processing','ready','failed','removed')
  visibility       ENUM('public','unlisted','private')
  upload_timestamp TIMESTAMP
  publish_timestamp TIMESTAMP
  raw_file_url     VARCHAR(1024)        -- S3 path to original upload
  manifest_url     VARCHAR(1024)        -- S3 path to HLS manifest
  file_size_bytes  BIGINT
  codec            VARCHAR(32)          -- h264, h265, vp9, av1
  resolution_max   VARCHAR(16)          -- highest available resolution
  language         VARCHAR(8)
  category_id      INT FK
  is_age_restricted BOOLEAN
  copyright_status ENUM('clear','claimed','blocked')
  created_at       TIMESTAMP
  updated_at       TIMESTAMP
}
INDEX: (creator_id, publish_timestamp), (status), (category_id, publish_timestamp)
```

**User**
```
users {
  user_id          VARCHAR(16) PK
  username         VARCHAR(64) UNIQUE
  email            VARCHAR(256) UNIQUE
  display_name     VARCHAR(128)
  avatar_url       VARCHAR(1024)
  subscriber_count BIGINT DEFAULT 0
  total_views      BIGINT DEFAULT 0
  created_at       TIMESTAMP
  updated_at       TIMESTAMP
}
```

**Subscription**
```
subscriptions {
  subscriber_id    VARCHAR(16) PK       -- user who subscribes
  channel_id       VARCHAR(16) PK       -- user being subscribed to
  subscribed_at    TIMESTAMP
  notifications    BOOLEAN DEFAULT true
}
INDEX: (channel_id, subscribed_at)
```

**Comment**
```
comments {
  comment_id       VARCHAR(16) PK
  video_id         VARCHAR(16)          -- partition key
  user_id          VARCHAR(16)
  parent_id        VARCHAR(16) NULL     -- for threaded replies
  content          TEXT
  like_count       INT DEFAULT 0
  created_at       TIMESTAMP
  updated_at       TIMESTAMP
}
PARTITION KEY: video_id
CLUSTERING KEY: created_at DESC
```

**Engagement (Likes)**
```
video_likes {
  user_id          VARCHAR(16)
  video_id         VARCHAR(16)
  like_type        ENUM('like','dislike')
  created_at       TIMESTAMP
  PRIMARY KEY (user_id, video_id)
}
```

**View Count (Redis + Async Flush)**
```
-- Redis structure:
video:{video_id}:views        -> INT (atomic increment)
video:{video_id}:views:daily  -> SORTED SET { date -> count }

-- Periodic flush to persistent store:
video_view_counts {
  video_id         VARCHAR(16) PK
  total_views      BIGINT
  views_24h        BIGINT
  views_7d         BIGINT
  views_30d        BIGINT
  last_updated     TIMESTAMP
}
```

**Watch History**
```
watch_history {
  user_id          VARCHAR(16)          -- partition key
  video_id         VARCHAR(16)
  watched_at       TIMESTAMP            -- clustering key
  watch_duration   INT                  -- seconds watched
  completed        BOOLEAN
}
```

### 6.2 Database Selection

```
┌──────────────────────┬────────────────────┬──────────────────────────────────┐
│ Data Type            │ Database           │ Justification                    │
├──────────────────────┼────────────────────┼──────────────────────────────────┤
│ Video metadata       │ PostgreSQL         │ ACID, complex queries, joins     │
│ User data            │ PostgreSQL         │ Relational integrity, auth       │
│ Video files          │ S3 / Blob Storage  │ Scalable object store, 11-nines  │
│ Thumbnails           │ S3 + CDN           │ Static assets, high read volume  │
│ Comments             │ Cassandra          │ Write-heavy, partition by video  │
│ Watch history        │ Cassandra          │ Append-heavy, time-series data   │
│ Search index         │ Elasticsearch      │ Full-text search, faceted        │
│ View counts          │ Redis + PostgreSQL │ Real-time counts + durable store │
│ Session/cache        │ Redis              │ Low latency, TTL support         │
│ Recommendations      │ Redis + Feature DB │ Pre-computed, real-time serving  │
│ Subscriptions feed   │ Redis (fan-out)    │ Timeline generation              │
│ Content fingerprints │ Dedicated DB       │ Audio/video hash matching        │
└──────────────────────┴────────────────────┴──────────────────────────────────┘
```

---

## 7. High-Level Architecture

### Overall System Architecture

```
┌──────────────────────────────────────────────────────────────────────────────┐
│                            CLIENT DEVICES                                    │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐      │
│  │  Mobile   │  │  Web     │  │ Smart TV │  │ Desktop  │  │ Console  │      │
│  │  App      │  │ Browser  │  │  App     │  │  App     │  │  App     │      │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘  └────┬─────┘  └────┬─────┘      │
│       │              │              │              │              │           │
└───────┼──────────────┼──────────────┼──────────────┼──────────────┼───────────┘
        │              │              │              │              │
        └──────────────┴──────┬───────┴──────────────┴──────────────┘
                              │
                   ┌──────────▼──────────┐
                   │    Global DNS       │
                   │  (GeoDNS routing)   │
                   └──────────┬──────────┘
                              │
              ┌───────────────┼───────────────┐
              │               │               │
    ┌─────────▼─────┐ ┌──────▼──────┐ ┌──────▼──────┐
    │  CDN Edge     │ │  CDN Edge   │ │  CDN Edge   │
    │  (US-West)    │ │  (EU)       │ │  (Asia)     │
    │  Video Cache  │ │  Video Cache│ │  Video Cache│
    └───────┬───────┘ └──────┬──────┘ └──────┬──────┘
            │                │               │
            └────────────────┼───────────────┘
                             │ (cache miss)
                   ┌─────────▼─────────┐
                   │   CDN Origin      │
                   │   Shield Layer    │
                   └─────────┬─────────┘
                             │
                   ┌─────────▼─────────┐
                   │   Load Balancer   │
                   │   (L7 / ALB)      │
                   └─────────┬─────────┘
                             │
                   ┌─────────▼─────────┐
                   │   API Gateway     │
                   │  ┌─────────────┐  │
                   │  │ Rate Limit  │  │
                   │  │ Auth/AuthZ  │  │
                   │  │ Routing     │  │
                   │  └─────────────┘  │
                   └─────────┬─────────┘
                             │
        ┌────────────────────┼───────────────────────┐
        │                    │                        │
  ┌─────▼──────┐    ┌───────▼───────┐    ┌───────────▼──────────┐
  │  Upload    │    │  Streaming   │    │  Metadata / Social   │
  │  Service   │    │  Service     │    │  Services            │
  │            │    │              │    │  ┌──────────────────┐ │
  └─────┬──────┘    └───────┬──────┘    │  │ Search Service   │ │
        │                   │           │  │ Comment Service  │ │
        │                   │           │  │ User Service     │ │
        │                   │           │  │ Like Service     │ │
        ▼                   │           │  │ Subscription Svc │ │
  ┌───────────┐             │           │  │ Recommendation   │ │
  │ Object    │◄────────────┘           │  └──────────────────┘ │
  │ Storage   │                         └───────────┬──────────┘
  │ (S3)      │                                     │
  └─────┬─────┘                              ┌──────▼──────┐
        │                                    │  Databases  │
        ▼                                    │  ┌────────┐ │
  ┌───────────┐                              │  │Postgres│ │
  │ Message   │                              │  │Cassandr│ │
  │ Queue     │                              │  │Elastic │ │
  │ (Kafka)   │                              │  │Redis   │ │
  └─────┬─────┘                              │  └────────┘ │
        │                                    └─────────────┘
        ▼
  ┌────────────────────────────┐
  │  Video Processing Pipeline │
  │  ┌──────┐ ┌──────┐ ┌────┐ │
  │  │Trans-│ │Thumb-│ │DRM │ │
  │  │coder │ │nail  │ │    │ │
  │  │Worker│ │Gen   │ │Enc │ │
  │  └──────┘ └──────┘ └────┘ │
  └────────────┬───────────────┘
               │
               ▼
  ┌──────────────────┐
  │ Processed Video  │
  │ Storage (S3)     │──────────► CDN Push/Pull
  │ HLS Segments     │
  └──────────────────┘
```

### Upload Path (Write Path)

```
┌────────┐     ┌──────────┐     ┌──────────┐     ┌─────────┐     ┌──────────┐
│Creator │────►│  Upload  │────►│ Temp     │────►│  Kafka  │────►│Transcoder│
│ Client │chunk│  Service │     │ Storage  │     │  Queue  │     │ Workers  │
│        │     │          │     │  (S3)    │     │         │     │          │
└────────┘     └──────────┘     └──────────┘     └─────────┘     └────┬─────┘
                    │                                                  │
                    │ metadata                          ┌──────────────┤
                    ▼                                   │              │
              ┌──────────┐                         ┌────▼────┐   ┌────▼────┐
              │ Postgres │                         │ 240p    │   │ 1080p   │
              │ (status: │                         │ segment │   │ segment │
              │ uploading│                         │ files   │   │ files   │
              │  )       │                         └────┬────┘   └────┬────┘
              └──────────┘                              │             │
                                                        └──────┬──────┘
                                                               │
                                                          ┌────▼─────┐
                                                          │ Processed│
                                                          │ Storage  │
                                                          │ (S3)     │
                                                          └────┬─────┘
                                                               │
                                                          ┌────▼─────┐
                                                          │ CDN      │
                                                          │ Ingest   │
                                                          └──────────┘
```

### Watch Path (Read Path)

```
┌────────┐     ┌──────────┐     ┌──────────┐
│Viewer  │────►│ CDN Edge │────►│ Video    │     CACHE HIT (>95%)
│ Client │     │ (nearest │     │ Segment  │────────────────────────► Client
│        │     │  PoP)    │     │ Cache    │
└────────┘     └────┬─────┘     └──────────┘
                    │
                    │ CACHE MISS (<5%)
                    ▼
              ┌──────────┐
              │ CDN      │
              │ Origin   │
              │ Shield   │
              └────┬─────┘
                   │
                   ▼
              ┌──────────┐
              │ Object   │
              │ Storage  │
              │ (S3)     │
              └──────────┘
```

### 7.1 Component Breakdown

| Component                  | Responsibility                                         | Tech Stack           |
|----------------------------|--------------------------------------------------------|----------------------|
| API Gateway                | Auth, rate limiting, request routing                   | Kong / Envoy         |
| Upload Service             | Chunked upload, checksum validation                    | Go / Java            |
| Video Processing Pipeline  | Transcoding, thumbnails, DRM, watermark                | FFmpeg + custom DAG  |
| Streaming Service          | Manifest generation, segment serving                   | Go / Rust            |
| Search Service             | Full-text video search, autocomplete                   | Elasticsearch        |
| Recommendation Service     | Personalized feeds, related videos                     | Python + ML models   |
| User Service               | Registration, auth, profile management                 | Java / Go            |
| Comment Service            | CRUD comments, threading, moderation                   | Java                 |
| Like Service               | Like/dislike toggle, aggregation                       | Go                   |
| Subscription Service       | Subscribe/unsubscribe, feed fan-out                    | Go                   |
| Notification Service       | Push notifications for new uploads                     | Go + FCM/APNs        |
| Content Moderation Service | Automated policy checks, copyright detection           | Python + ML          |
| CDN                        | Edge caching, geo-distributed delivery                 | CloudFront / Akamai  |
| Object Storage             | Raw and processed video storage                        | S3 / GCS             |
| Message Queue              | Async pipeline orchestration                           | Apache Kafka         |

---

## 8. Deep Dive: Core Components

### 8.1 Video Upload and Processing Pipeline

#### Resumable Chunked Upload

Large video files cannot be uploaded in a single HTTP request reliably. We use
a chunked, resumable upload protocol inspired by the tus protocol:

```
┌────────────────────────────────────────────────────────────────────────────┐
│                    RESUMABLE UPLOAD PROTOCOL                               │
│                                                                            │
│  Creator                 Upload Service              Temp Storage (S3)     │
│    │                          │                            │               │
│    │  POST /upload/initiate   │                            │               │
│    │─────────────────────────►│                            │               │
│    │  ◄── upload_url + token  │                            │               │
│    │                          │                            │               │
│    │  PUT /chunks/0 (8MB)     │                            │               │
│    │─────────────────────────►│───── store chunk 0 ──────►│               │
│    │  ◄── ack chunk 0         │                            │               │
│    │                          │                            │               │
│    │  PUT /chunks/1 (8MB)     │                            │               │
│    │─────────────────────────►│───── store chunk 1 ──────►│               │
│    │  ◄── ack chunk 1         │                            │               │
│    │                          │                            │               │
│    │     ... (network drop)   │                            │               │
│    │                          │                            │               │
│    │  GET /upload/status      │                            │               │
│    │─────────────────────────►│                            │               │
│    │  ◄── chunks 0,1 received │                            │               │
│    │                          │                            │               │
│    │  PUT /chunks/2 (resume)  │                            │               │
│    │─────────────────────────►│───── store chunk 2 ──────►│               │
│    │  ◄── ack chunk 2         │                            │               │
│    │                          │                            │               │
│    │  POST /upload/complete   │                            │               │
│    │─────────────────────────►│  assemble + checksum       │               │
│    │  ◄── status: processing  │─── publish to Kafka ──►   │               │
│    │                          │                            │               │
└────────────────────────────────────────────────────────────────────────────┘
```

**Key design decisions:**
- **Chunk size:** 8 MB default, adjustable based on client bandwidth
- **Checksums:** Each chunk has a CRC32 checksum; final file has SHA-256 verification
- **Expiry:** Incomplete uploads expire after 24 hours; temp storage is cleaned up
- **Multipart upload to S3:** Chunks map directly to S3 multipart upload parts
- **Idempotency:** Chunk numbers are idempotent keys; re-uploading same chunk is safe

#### Video Processing Pipeline (DAG-based)

Once the raw video is uploaded, a Directed Acyclic Graph (DAG) of processing
tasks is created. This allows parallelism where possible and clear dependency
management.

```
┌────────────────────────────────────────────────────────────────────────────────┐
│                    VIDEO PROCESSING DAG                                        │
│                                                                                │
│                        ┌──────────────┐                                        │
│                        │  Raw Video   │                                        │
│                        │  (S3 input)  │                                        │
│                        └──────┬───────┘                                        │
│                               │                                                │
│                        ┌──────▼───────┐                                        │
│                        │  Validate &  │                                        │
│                        │  Inspect     │                                        │
│                        │  (ffprobe)   │                                        │
│                        └──────┬───────┘                                        │
│                               │                                                │
│              ┌────────────────┼────────────────┐                               │
│              │                │                │                                │
│       ┌──────▼──────┐  ┌─────▼──────┐  ┌──────▼──────┐                        │
│       │  Audio      │  │  Video     │  │  Thumbnail  │                        │
│       │  Extract    │  │  Split     │  │  Generation │                        │
│       │             │  │  (scenes)  │  │  (5 frames) │                        │
│       └──────┬──────┘  └─────┬──────┘  └──────┬──────┘                        │
│              │               │                │                                │
│              │    ┌──────────┼──────────┐      │                                │
│              │    │          │          │      │                                │
│              │ ┌──▼───┐ ┌───▼──┐ ┌─────▼─┐   │                                │
│              │ │ 240p │ │ 480p │ │ 1080p │   │                                │
│              │ │ H264 │ │ H264 │ │ H264  │   │                                │
│              │ └──┬───┘ └───┬──┘ └───┬───┘   │                                │
│              │    │         │        │        │                                │
│              │    └─────────┼────────┘        │                                │
│              │              │                 │                                │
│              │       ┌──────▼──────┐          │                                │
│              │       │  Segment    │          │                                │
│              │       │  into HLS   │          │                                │
│              │       │  chunks     │          │                                │
│              │       │  (6s each)  │          │                                │
│              │       └──────┬──────┘          │                                │
│              │              │                 │                                │
│              │       ┌──────▼──────┐          │                                │
│              │       │  DRM        │          │                                │
│              │       │  Encryption │          │                                │
│              │       │  (Widevine/ │          │                                │
│              │       │   FairPlay) │          │                                │
│              │       └──────┬──────┘          │                                │
│              │              │                 │                                │
│              └──────┬───────┘                 │                                │
│                     │                         │                                │
│              ┌──────▼──────┐           ┌──────▼──────┐                         │
│              │  Generate   │           │  Upload     │                         │
│              │  HLS        │           │  Thumbnails │                         │
│              │  Manifest   │           │  to CDN     │                         │
│              └──────┬──────┘           └──────┬──────┘                         │
│                     │                         │                                │
│                     └────────────┬────────────┘                                │
│                                 │                                              │
│                          ┌──────▼──────┐                                       │
│                          │  Upload to  │                                       │
│                          │  Processed  │                                       │
│                          │  Storage    │                                       │
│                          └──────┬──────┘                                       │
│                                 │                                              │
│                          ┌──────▼──────┐                                       │
│                          │  Update DB  │                                       │
│                          │  status:    │                                       │
│                          │  "ready"    │                                       │
│                          └──────┬──────┘                                       │
│                                 │                                              │
│                          ┌──────▼──────┐                                       │
│                          │  Content    │                                       │
│                          │  Moderation │                                       │
│                          │  (async)    │                                       │
│                          └─────────────┘                                       │
│                                                                                │
└────────────────────────────────────────────────────────────────────────────────┘
```

#### Transcoding Details

| Resolution | Bitrate (H.264) | Bitrate (H.265) | Bitrate (AV1)  | Segment Size (6s) |
|------------|-----------------|-----------------|----------------|-------------------|
| 240p       | 400 Kbps        | 250 Kbps        | 150 Kbps       | ~300 KB           |
| 360p       | 800 Kbps        | 500 Kbps        | 300 Kbps       | ~600 KB           |
| 480p       | 1.5 Mbps        | 1.0 Mbps        | 600 Kbps       | ~1.1 MB           |
| 720p       | 3.0 Mbps        | 2.0 Mbps        | 1.2 Mbps       | ~2.3 MB           |
| 1080p      | 5.0 Mbps        | 3.5 Mbps        | 2.0 Mbps       | ~3.8 MB           |
| 4K         | 15.0 Mbps       | 10.0 Mbps       | 6.0 Mbps       | ~11.3 MB          |

**Codec strategy:**
- **H.264 (AVC):** Universal baseline -- supported on all devices. Always generated.
- **H.265 (HEVC):** 40-50% better compression. Generated for 720p+ content.
  Requires licensing fees.
- **VP9:** Royalty-free Google codec. Generated for YouTube-like platforms.
- **AV1:** Next-gen royalty-free codec. 30% better than HEVC but very slow to
  encode. Generated only for popular content or as background job.

**Per-title encoding:** Netflix pioneered analyzing each video's complexity to
determine optimal bitrate ladders. A simple animation may only need 1.5 Mbps
at 1080p, while an action scene needs 6+ Mbps. We analyze each title and
generate custom encoding parameters.

#### Transcoding Worker Architecture

```
┌────────────────────────────────────────────────────────────────────┐
│                   TRANSCODING WORKER POOL                          │
│                                                                    │
│  ┌────────────┐    ┌──────────────────────────────────────────┐    │
│  │   Kafka    │    │         Worker Autoscaler                │    │
│  │  Consumer  │───►│  ┌────────┐ ┌────────┐ ┌────────┐       │    │
│  │  Group     │    │  │Worker 1│ │Worker 2│ │Worker N│       │    │
│  │            │    │  │GPU/CPU │ │GPU/CPU │ │GPU/CPU │       │    │
│  │  Topics:   │    │  │FFmpeg  │ │FFmpeg  │ │FFmpeg  │       │    │
│  │  -transcode│    │  └────────┘ └────────┘ └────────┘       │    │
│  │  -thumbnail│    │                                          │    │
│  │  -drm      │    │  Scale: 2,000 - 20,000 workers          │    │
│  └────────────┘    │  Instance: GPU (P3/T4) for H.265/AV1    │    │
│                    │  Spot/Preemptible: 80% of fleet          │    │
│                    └──────────────────────────────────────────┘    │
│                                                                    │
│  Retry policy: 3 retries with exponential backoff                  │
│  Dead letter queue for permanently failed jobs                     │
│  Checkpointing: resume transcoding from last completed segment     │
└────────────────────────────────────────────────────────────────────┘
```

---

### 8.2 Adaptive Bitrate Streaming (ABR)

Adaptive bitrate streaming is the core technology that enables smooth playback
across varying network conditions. The video is pre-segmented into small chunks
at multiple quality levels, and the client player dynamically switches between
quality levels based on available bandwidth.

#### HLS (HTTP Live Streaming) vs DASH

| Feature               | HLS                        | DASH                          |
|-----------------------|----------------------------|-------------------------------|
| Developer             | Apple                      | MPEG consortium (open std)    |
| Container format      | MPEG-TS (.ts) or fMP4      | fMP4 (.m4s)                   |
| Manifest format       | .m3u8 (playlist)           | .mpd (XML)                    |
| Segment duration      | 6 seconds typical          | 2-6 seconds                   |
| DRM support           | FairPlay                   | Widevine, PlayReady           |
| Browser support       | Safari native, others MSE  | All browsers via MSE          |
| Latency               | 15-30 sec (standard)       | 3-10 sec (low latency)        |
| Industry adoption     | Apple ecosystem, broad     | YouTube, Netflix              |

**Our choice:** Support both HLS and DASH. Generate fMP4 segments that work
with both protocols (CMAF -- Common Media Application Format). The manifest
is generated dynamically per protocol.

#### HLS Manifest Structure

```
Master Playlist (master.m3u8)
├── 240p/playlist.m3u8   → 240p/seg-0.ts, seg-1.ts, seg-2.ts, ...
├── 360p/playlist.m3u8   → 360p/seg-0.ts, seg-1.ts, seg-2.ts, ...
├── 480p/playlist.m3u8   → 480p/seg-0.ts, seg-1.ts, seg-2.ts, ...
├── 720p/playlist.m3u8   → 720p/seg-0.ts, seg-1.ts, seg-2.ts, ...
├── 1080p/playlist.m3u8  → 1080p/seg-0.ts, seg-1.ts, seg-2.ts, ...
└── audio/playlist.m3u8  → audio/seg-0.aac, seg-1.aac, seg-2.aac, ...
```

#### ABR Algorithm Flow

```
┌──────────────────────────────────────────────────────────────────────────────┐
│                    CLIENT-SIDE ABR ALGORITHM                                 │
│                                                                              │
│  ┌──────────┐                                                                │
│  │  Start   │                                                                │
│  │ Playback │                                                                │
│  └────┬─────┘                                                                │
│       │                                                                      │
│       ▼                                                                      │
│  ┌────────────┐     ┌───────────────────────────────────────────┐            │
│  │ Fetch      │     │         ABR Decision Engine               │            │
│  │ Master     │     │                                           │            │
│  │ Manifest   │     │  Inputs:                                  │            │
│  └────┬───────┘     │  ┌─────────────────────────────────┐      │            │
│       │             │  │ 1. Throughput history (EWMA)     │      │            │
│       ▼             │  │ 2. Buffer level (seconds ahead)  │      │            │
│  ┌────────────┐     │  │ 3. Screen resolution             │      │            │
│  │ Start with │     │  │ 4. Device capability              │      │            │
│  │ lowest     │     │  │ 5. User preference (if manual)    │      │            │
│  │ quality    │     │  └─────────────────────────────────┘      │            │
│  └────┬───────┘     │                                           │            │
│       │             │  Algorithm (hybrid):                      │            │
│       ▼             │  ┌─────────────────────────────────┐      │            │
│  ┌──────────────┐   │  │ IF buffer < 5s:                 │      │            │
│  │ Fetch next   │◄──┤  │   → switch DOWN (panic mode)    │      │            │
│  │ segment at   │   │  │ ELIF buffer < 15s:              │      │            │
│  │ chosen       │   │  │   → use throughput-based:       │      │            │
│  │ quality      │   │  │     pick highest quality where  │      │            │
│  └──────┬───────┘   │  │     bitrate < 0.8 * EWMA_bw    │      │            │
│         │           │  │ ELIF buffer > 30s:              │      │            │
│         ▼           │  │   → can switch UP               │      │            │
│  ┌──────────────┐   │  │ ELSE:                           │      │            │
│  │ Measure      │   │  │   → maintain current quality    │      │            │
│  │ download     │   │  └─────────────────────────────────┘      │            │
│  │ throughput   │───┤                                           │            │
│  └──────┬───────┘   │  Safety margin: 0.8x ensures we never    │            │
│         │           │  request more than available bandwidth    │            │
│         ▼           │                                           │            │
│  ┌──────────────┐   └───────────────────────────────────────────┘            │
│  │ Update EWMA  │                                                            │
│  │ throughput   │     EWMA = alpha * measured + (1-alpha) * EWMA_prev        │
│  │ estimate     │     alpha = 0.3 (smoothing factor)                         │
│  └──────┬───────┘                                                            │
│         │                                                                    │
│         └──────────────────► Repeat for each segment                         │
│                                                                              │
└──────────────────────────────────────────────────────────────────────────────┘
```

#### Quality Switching Timeline Example

```
Bandwidth:  ████████████████░░░░░░░░████████████████████████████████████████

Time:       0s    5s    10s   15s   20s   25s   30s   35s   40s   45s

Quality:    360p──720p──1080p─720p──480p──360p──480p──720p──1080p─1080p──►

Buffer:     ▂▃▅▇██████████▇▅▃▂▂▃▅▇██████████████████████████████████████

Events:     Start  ↑     ↑    Network   ↑    Recovery    Stabilized
                   |     |    drop      |    begins      at 1080p
                   ABR   ABR            ABR
                   up    up             down
```

---

### 8.3 CDN Architecture

Content Delivery Networks are absolutely critical for a video streaming platform.
Without CDN, every view would hit origin storage, requiring petabits of bandwidth
from a single region. CDN caches video segments at edge locations close to viewers.

#### Multi-Tier CDN Architecture

```
┌──────────────────────────────────────────────────────────────────────────────┐
│                         MULTI-TIER CDN                                       │
│                                                                              │
│  TIER 1: Edge PoPs (200+ locations worldwide)                                │
│  ┌───────────────────────────────────────────────────────────────────┐       │
│  │                                                                   │       │
│  │   ┌─────────┐   ┌─────────┐   ┌─────────┐   ┌─────────┐        │       │
│  │   │ NYC     │   │ London  │   │ Tokyo   │   │ Mumbai  │  ...    │       │
│  │   │ Edge    │   │ Edge    │   │ Edge    │   │ Edge    │        │       │
│  │   │         │   │         │   │         │   │         │        │       │
│  │   │ ~50TB   │   │ ~50TB   │   │ ~50TB   │   │ ~30TB   │        │       │
│  │   │ SSD     │   │ SSD     │   │ SSD     │   │ SSD     │        │       │
│  │   │ cache   │   │ cache   │   │ cache   │   │ cache   │        │       │
│  │   └────┬────┘   └────┬────┘   └────┬────┘   └────┬────┘        │       │
│  │        │              │              │              │             │       │
│  │   Cache hit           │         Cache hit           │             │       │
│  │   ratio: 85%          │         ratio: 85%          │             │       │
│  └────────┼──────────────┼──────────────┼──────────────┼─────────────┘       │
│           │              │              │              │                      │
│           │ miss         │ miss         │ miss         │ miss                 │
│           ▼              ▼              ▼              ▼                      │
│  TIER 2: Regional Shield (8-12 locations)                                    │
│  ┌───────────────────────────────────────────────────────────────────┐       │
│  │                                                                   │       │
│  │   ┌──────────────┐     ┌──────────────┐     ┌──────────────┐     │       │
│  │   │ US Shield    │     │ EU Shield    │     │ APAC Shield  │     │       │
│  │   │ (Virginia)   │     │ (Frankfurt)  │     │ (Singapore)  │     │       │
│  │   │              │     │              │     │              │     │       │
│  │   │ ~500TB HDD   │     │ ~500TB HDD   │     │ ~300TB HDD   │     │       │
│  │   │ cache        │     │ cache        │     │ cache        │     │       │
│  │   └──────┬───────┘     └──────┬───────┘     └──────┬───────┘     │       │
│  │          │                    │                    │              │       │
│  │   Cache hit ratio: 95%       │              Cache hit: 93%       │       │
│  └──────────┼────────────────────┼────────────────────┼─────────────┘       │
│             │ miss               │ miss               │ miss                 │
│             ▼                    ▼                    ▼                      │
│  TIER 3: Origin                                                              │
│  ┌───────────────────────────────────────────────────────────────────┐       │
│  │   ┌──────────────────────────────────────────────────────┐       │       │
│  │   │            Object Storage (S3 / GCS)                 │       │       │
│  │   │                                                      │       │       │
│  │   │  All video segments, all resolutions, all codecs     │       │       │
│  │   │  Multi-region replication for durability              │       │       │
│  │   │  Capacity: hundreds of petabytes                     │       │       │
│  │   └──────────────────────────────────────────────────────┘       │       │
│  └───────────────────────────────────────────────────────────────────┘       │
│                                                                              │
│  Overall CDN cache hit ratio: > 95% (edge + shield combined)                 │
│  Origin traffic: < 5% of total views                                         │
└──────────────────────────────────────────────────────────────────────────────┘
```

#### CDN Cache Warming and Popularity

Not all content is equal. The top 10% of videos typically account for 80%+ of
views (Zipf distribution). We optimize caching based on content popularity:

```
┌───────────────────────────────────────────────────────────────────┐
│                   CONTENT POPULARITY TIERS                        │
│                                                                   │
│  Tier    │ % of Videos │ % of Views │ CDN Strategy               │
│  ────────┼─────────────┼────────────┼──────────────────────────── │
│  Hot     │    0.1%     │    30%     │ Pre-push to ALL edge PoPs  │
│  Warm    │    5%       │    50%     │ Push to regional shields   │
│  Cool    │    20%      │    15%     │ Pull-through cache         │
│  Cold    │    74.9%    │    5%      │ Origin-only, no caching    │
│                                                                   │
│  Viral detection:                                                 │
│  ┌────────────────────────────────────────────────────┐           │
│  │  Views/min > 10x baseline → Promote to Hot tier   │           │
│  │  Views/min > 3x baseline  → Promote to Warm tier  │           │
│  │  No views for 7 days      → Demote to Cold tier   │           │
│  └────────────────────────────────────────────────────┘           │
│                                                                   │
└───────────────────────────────────────────────────────────────────┘
```

#### Cache Eviction Policy

- **Edge PoPs:** LRU with frequency boost (LFU-hybrid). Segments from popular
  videos get a "stickiness" bonus to avoid premature eviction.
- **Shield layer:** TTL-based (24h for hot, 72h for warm) + LRU fallback.
- **Segment granularity:** Cache individual segments (6-second chunks), not
  entire videos. First few segments of popular videos are prioritized since
  many viewers watch only the first 30 seconds.

---

### 8.4 Recommendation Engine

The recommendation engine is what keeps users engaged. It powers the home feed,
"Up Next" sidebar, and search ranking signals.

#### Architecture Overview

```
┌──────────────────────────────────────────────────────────────────────────┐
│                    RECOMMENDATION SYSTEM                                 │
│                                                                          │
│  ┌─────────────┐                                                         │
│  │ User Action │   (watch, like, subscribe, search, skip, share)         │
│  └──────┬──────┘                                                         │
│         │                                                                │
│         ▼                                                                │
│  ┌──────────────┐     ┌──────────────────────────────────────────┐       │
│  │ Event Stream │────►│  Feature Pipeline (Flink / Spark)        │       │
│  │ (Kafka)      │     │                                          │       │
│  └──────────────┘     │  Real-time features:                     │       │
│                       │  - User watch history (last 100 videos)  │       │
│                       │  - Trending videos (last 1h, 6h, 24h)   │       │
│                       │  - User embedding vector                 │       │
│                       │                                          │       │
│                       │  Batch features (daily):                 │       │
│                       │  - Video co-watch matrix                 │       │
│                       │  - Creator graph                         │       │
│                       │  - Content category affinity             │       │
│                       └───────────┬──────────────────────────────┘       │
│                                   │                                      │
│                                   ▼                                      │
│                       ┌───────────────────────┐                          │
│                       │   Feature Store        │                         │
│                       │   (Redis + DynamoDB)   │                         │
│                       └───────────┬────────────┘                         │
│                                   │                                      │
│         ┌─────────────────────────┼──────────────────────┐               │
│         │                         │                      │               │
│         ▼                         ▼                      ▼               │
│  ┌──────────────┐     ┌───────────────────┐   ┌──────────────────┐      │
│  │  Candidate   │     │   Ranking Model   │   │  Diversity &     │      │
│  │  Generation  │     │   (Deep Neural    │   │  Business Rules  │      │
│  │              │     │    Network)        │   │                  │      │
│  │  Sources:    │     │                   │   │  - No duplicate  │      │
│  │  - Collab.   │────►│  Input:           │──►│    creators in   │      │
│  │    filtering │     │  - user features  │   │    top 5         │      │
│  │  - Content-  │     │  - video features │   │  - Mix categories│      │
│  │    based     │     │  - context (time, │   │  - Age-gate      │      │
│  │  - Trending  │     │    device, geo)   │   │  - Freshness     │      │
│  │  - Following │     │                   │   │    boost         │      │
│  │              │     │  Output:          │   │                  │      │
│  │  ~1000       │     │  P(watch > 50%)   │   │  Final top 50   │      │
│  │  candidates  │     │  P(like)          │   │  videos          │      │
│  │              │     │  P(subscribe)     │   │                  │      │
│  └──────────────┘     │  E(watch time)    │   └──────────────────┘      │
│                       └───────────────────┘                              │
│                                                                          │
│  Cold start strategy:                                                    │
│  ┌─────────────────────────────────────────────────────────────────┐     │
│  │  New user:  → Show trending + popular by geo + onboarding quiz │     │
│  │  New video: → Use content features (title, tags, description)  │     │
│  │             → Boost exposure to small sample for signal         │     │
│  │             → Creator's subscriber base as initial audience     │     │
│  └─────────────────────────────────────────────────────────────────┘     │
│                                                                          │
└──────────────────────────────────────────────────────────────────────────┘
```

#### Collaborative vs Content-Based Filtering

```
┌──────────────────────────────┐    ┌──────────────────────────────┐
│  COLLABORATIVE FILTERING     │    │  CONTENT-BASED FILTERING     │
│                              │    │                              │
│  "Users who watched X also   │    │  "This video is similar to   │
│   watched Y"                 │    │   videos you liked"          │
│                              │    │                              │
│  User-Item Matrix:           │    │  Video Feature Vector:       │
│                              │    │                              │
│       V1  V2  V3  V4  V5    │    │  Title embedding:  [0.2,...]│
│  U1 [ 5   .   3   .   1 ]  │    │  Visual features:  [0.8,...]│
│  U2 [ 4   .   .   3   . ]  │    │  Audio features:   [0.1,...]│
│  U3 [ .   3   .   .   4 ]  │    │  Tags/categories:  [1,0,...] │
│  U4 [ .   .   5   4   . ]  │    │  Duration:         [0.3]     │
│  U5 [ 1   .   .   .   5 ]  │    │  Creator profile:  [0.5,...]│
│                              │    │                              │
│  → Matrix factorization      │    │  → Cosine similarity to      │
│    (ALS, SVD)                │    │    user's positive history    │
│  → Predict missing values    │    │                              │
│                              │    │  Pros: Works for new videos  │
│  Pros: Serendipitous finds   │    │  Cons: Filter bubble risk    │
│  Cons: Cold start problem    │    │                              │
└──────────────────────────────┘    └──────────────────────────────┘
```

---

## 9. Data Partitioning and Sharding

### Sharding Strategy by Data Type

```
┌──────────────────────────────────────────────────────────────────────────────┐
│                          SHARDING STRATEGY                                   │
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐     │
│  │ VIDEO METADATA (PostgreSQL)                                        │     │
│  │                                                                     │     │
│  │ Shard key: video_id (consistent hashing)                           │     │
│  │ Shards: 256 logical shards → mapped to 32 physical DB clusters     │     │
│  │                                                                     │     │
│  │   video_id ──► hash(video_id) % 256 ──► shard_45 ──► cluster_7    │     │
│  │                                                                     │     │
│  │   ┌─────────┐ ┌─────────┐ ┌─────────┐     ┌─────────┐            │     │
│  │   │Cluster 0│ │Cluster 1│ │Cluster 2│ ... │Cluster31│            │     │
│  │   │Shard 0-7│ │Shard 8-F│ │Shard G-N│     │Shard ..│            │     │
│  │   │ Primary │ │ Primary │ │ Primary │     │ Primary │            │     │
│  │   │ +2 repl │ │ +2 repl │ │ +2 repl │     │ +2 repl │            │     │
│  │   └─────────┘ └─────────┘ └─────────┘     └─────────┘            │     │
│  └─────────────────────────────────────────────────────────────────────┘     │
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐     │
│  │ USER DATA (PostgreSQL)                                              │     │
│  │                                                                     │     │
│  │ Shard key: user_id                                                  │     │
│  │ Shards: 64 logical shards → 16 physical clusters                   │     │
│  │ Note: user_id lookup needed for auth on every request               │     │
│  │       → cache user profiles in Redis (TTL 15 min)                   │     │
│  └─────────────────────────────────────────────────────────────────────┘     │
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐     │
│  │ COMMENTS (Cassandra)                                                │     │
│  │                                                                     │     │
│  │ Partition key: video_id                                             │     │
│  │ Clustering key: created_at DESC                                     │     │
│  │ Replication factor: 3 (across availability zones)                   │     │
│  │                                                                     │     │
│  │ Hot partition risk: viral videos with millions of comments           │     │
│  │ Mitigation: bucket partition key as (video_id, bucket_id)           │     │
│  │   bucket_id = comment_count / 10000                                 │     │
│  │   → Each partition holds at most ~10K comments                      │     │
│  └─────────────────────────────────────────────────────────────────────┘     │
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐     │
│  │ VIDEO FILES (Object Storage / S3)                                   │     │
│  │                                                                     │     │
│  │ Path structure:                                                     │     │
│  │   s3://video-processed/{shard}/{video_id}/{quality}/{segment}.ts    │     │
│  │                                                                     │     │
│  │ Shard prefix: first 2 chars of video_id hash                        │     │
│  │   → Avoids S3 partition hotspots (S3 partitions by key prefix)      │     │
│  │   → 256 prefix shards (00-ff)                                       │     │
│  │                                                                     │     │
│  │ Multi-region replication:                                           │     │
│  │   Primary: us-east-1                                                │     │
│  │   Replicas: eu-west-1, ap-southeast-1                               │     │
│  │   → CDN pulls from nearest region's S3                              │     │
│  └─────────────────────────────────────────────────────────────────────┘     │
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐     │
│  │ SEARCH INDEX (Elasticsearch)                                        │     │
│  │                                                                     │     │
│  │ Index: videos (50 shards, 1 replica)                                │     │
│  │ Routing: video_id (co-locate with metadata for efficient updates)   │     │
│  │ Fields indexed: title, description, tags, captions, category        │     │
│  │ Refresh interval: 30 seconds (near-real-time, not instant)          │     │
│  └─────────────────────────────────────────────────────────────────────┘     │
│                                                                              │
└──────────────────────────────────────────────────────────────────────────────┘
```

### Cross-Shard Query Handling

Some queries span multiple shards:
- **"All videos by creator X":** Creator-to-videos mapping stored in a secondary
  index (denormalized table sharded by creator_id). Not a cross-shard join.
- **"Trending videos":** Pre-computed by a batch/stream pipeline, stored as a
  sorted list in Redis. No cross-shard query needed.
- **"Search":** Elasticsearch handles its own sharding. A coordinating node
  scatters the query to all shards and gathers results.

---

## 10. Caching Strategy

### Multi-Layer Cache Architecture

```
┌──────────────────────────────────────────────────────────────────────────────┐
│                         CACHING LAYERS                                       │
│                                                                              │
│  Layer 1: Client-Side Cache                                                  │
│  ┌────────────────────────────────────────────────────────────────────┐      │
│  │  - Video player buffer: 30-60 seconds of prefetched segments      │      │
│  │  - Thumbnail cache: browser/app image cache                       │      │
│  │  - Manifest cache: 5-minute TTL                                   │      │
│  │  - User preferences: local storage                                │      │
│  └────────────────────────────────────────────────────────────────────┘      │
│                                                                              │
│  Layer 2: CDN Edge Cache                                                     │
│  ┌────────────────────────────────────────────────────────────────────┐      │
│  │  - Video segments: TTL 24h (immutable content, cache-friendly)    │      │
│  │  - Thumbnails: TTL 24h                                            │      │
│  │  - Manifests: TTL 5 min (may change if new qualities added)       │      │
│  │  - Cache hit ratio target: > 85% at edge                         │      │
│  │  - Total edge cache: ~50 TB per PoP * 200 PoPs = 10 PB          │      │
│  └────────────────────────────────────────────────────────────────────┘      │
│                                                                              │
│  Layer 3: CDN Shield Cache                                                   │
│  ┌────────────────────────────────────────────────────────────────────┐      │
│  │  - All content that missed edge cache                             │      │
│  │  - TTL 72h for video segments                                     │      │
│  │  - Cache hit ratio: > 95% (edge + shield combined)               │      │
│  │  - Total shield cache: ~500 TB per shield * 10 = 5 PB            │      │
│  └────────────────────────────────────────────────────────────────────┘      │
│                                                                              │
│  Layer 4: Application Cache (Redis Cluster)                                  │
│  ┌────────────────────────────────────────────────────────────────────┐      │
│  │  Key                          │ TTL    │ Size Estimate             │      │
│  │  ─────────────────────────────┼────────┼─────────────────────────  │      │
│  │  video:{id}:metadata          │ 15 min │ ~2 KB per video           │      │
│  │  video:{id}:views             │ none   │ 8 bytes (counter)         │      │
│  │  user:{id}:profile            │ 15 min │ ~1 KB per user            │      │
│  │  user:{id}:subscriptions      │ 30 min │ ~10 KB (list of IDs)      │      │
│  │  user:{id}:recommendations    │ 1 hour │ ~5 KB (pre-computed)      │      │
│  │  trending:global              │ 5 min  │ ~50 KB (top 200 videos)   │      │
│  │  trending:{country}           │ 5 min  │ ~50 KB per country        │      │
│  │  search:autocomplete:{prefix} │ 10 min │ ~1 KB per prefix          │      │
│  │                                                                    │      │
│  │  Total Redis cluster: ~2 TB across 50 nodes                       │      │
│  └────────────────────────────────────────────────────────────────────┘      │
│                                                                              │
│  Layer 5: Database Query Cache                                               │
│  ┌────────────────────────────────────────────────────────────────────┐      │
│  │  - PostgreSQL shared_buffers: 25% of RAM per instance             │      │
│  │  - Elasticsearch OS page cache: caches frequently accessed shards │      │
│  └────────────────────────────────────────────────────────────────────┘      │
│                                                                              │
└──────────────────────────────────────────────────────────────────────────────┘
```

### Cache Invalidation Strategy

```
Content Type        │ Invalidation Strategy
────────────────────┼──────────────────────────────────────────────────
Video segments      │ Immutable (never change once transcoded).
                    │ Unique URL per version. No invalidation needed.
                    │ New transcode = new segment URLs.
                    │
Thumbnails          │ Versioned URL: /thumbs/{video_id}/v2/default.jpg
                    │ Creator uploads new thumbnail → new version URL
                    │
Video metadata      │ Event-driven: on metadata update, publish event
                    │ to Kafka → consumer invalidates Redis key
                    │ Short TTL (15 min) as safety net
                    │
View counts         │ No invalidation. Redis counter is source of truth.
                    │ Periodic flush to PostgreSQL (every 30 seconds)
                    │
Recommendations     │ Regenerated every hour per user.
                    │ Redis key overwritten (not invalidated).
                    │
Search index        │ Elasticsearch near-real-time refresh (30s)
                    │ No cache invalidation; index is the cache.
```

---

## 11. Replication and Consistency

### Consistency Requirements by Data Type

```
┌──────────────────────────────────────────────────────────────────────────────┐
│                   CONSISTENCY MODEL                                          │
│                                                                              │
│  ┌───────────────────┬──────────────┬────────────────────────────────┐       │
│  │ Data              │ Consistency  │ Rationale                      │       │
│  ├───────────────────┼──────────────┼────────────────────────────────┤       │
│  │ Video upload      │ Strong       │ Creator must see upload status │       │
│  │ status            │              │ accurately. No lost uploads.   │       │
│  ├───────────────────┼──────────────┼────────────────────────────────┤       │
│  │ Video metadata    │ Strong       │ Title, description changes     │       │
│  │ (writes)          │ (read-your- │ must be visible to creator     │       │
│  │                   │  writes)     │ immediately. Viewers can see   │       │
│  │                   │              │ stale data for a few seconds.  │       │
│  ├───────────────────┼──────────────┼────────────────────────────────┤       │
│  │ View counts       │ Eventual     │ Approximate counts are fine.   │       │
│  │                   │              │ "1.2M views" vs "1,200,347"    │       │
│  │                   │              │ does not matter to viewers.    │       │
│  ├───────────────────┼──────────────┼────────────────────────────────┤       │
│  │ Like counts       │ Eventual     │ Same as view counts.           │       │
│  │                   │              │ User's own like status: strong │       │
│  │                   │              │ (read-your-writes via session) │       │
│  ├───────────────────┼──────────────┼────────────────────────────────┤       │
│  │ Comments          │ Eventual     │ Delay of a few seconds is      │       │
│  │                   │              │ acceptable. User sees own      │       │
│  │                   │              │ comment immediately (optimistic│       │
│  │                   │              │ client-side rendering).        │       │
│  ├───────────────────┼──────────────┼────────────────────────────────┤       │
│  │ Subscriptions     │ Strong       │ User expects immediate effect  │       │
│  │                   │              │ of subscribe/unsubscribe.      │       │
│  ├───────────────────┼──────────────┼────────────────────────────────┤       │
│  │ Recommendations   │ Eventual     │ Pre-computed, hourly refresh.  │       │
│  │                   │              │ Staleness is inherent.         │       │
│  ├───────────────────┼──────────────┼────────────────────────────────┤       │
│  │ Search index      │ Eventual     │ Near-real-time (30s delay).    │       │
│  │                   │              │ New uploads searchable within  │       │
│  │                   │              │ a minute.                      │       │
│  └───────────────────┴──────────────┴────────────────────────────────┘       │
│                                                                              │
└──────────────────────────────────────────────────────────────────────────────┘
```

### Replication Topology

```
┌──────────────────────────────────────────────────────────────────────┐
│                   REPLICATION TOPOLOGY                                │
│                                                                      │
│  PostgreSQL (Video Metadata, User Data)                              │
│  ┌────────────────────────────────────────────────────────────┐      │
│  │                                                            │      │
│  │    ┌─────────────┐                                         │      │
│  │    │   Primary   │                                         │      │
│  │    │ (us-east-1a)│                                         │      │
│  │    └──┬──────┬───┘                                         │      │
│  │       │sync  │async                                        │      │
│  │       ▼      ▼                                             │      │
│  │  ┌────────┐ ┌────────┐  ┌────────┐                        │      │
│  │  │Standby │ │Read    │  │Read    │                        │      │
│  │  │(1b)    │ │Replica │  │Replica │                        │      │
│  │  │sync    │ │(1c)    │  │(eu-w-1)│  ← cross-region       │      │
│  │  │replica │ │for read│  │for EU  │    async replication   │      │
│  │  └────────┘ │queries │  │reads   │    (lag: 50-200ms)     │      │
│  │             └────────┘  └────────┘                        │      │
│  │                                                            │      │
│  │  Failover: automatic via Patroni/RDS Multi-AZ             │      │
│  │  RPO: 0 (synchronous standby), RTO: < 30 seconds          │      │
│  └────────────────────────────────────────────────────────────┘      │
│                                                                      │
│  Cassandra (Comments, Watch History)                                 │
│  ┌────────────────────────────────────────────────────────────┐      │
│  │                                                            │      │
│  │  Replication factor: 3                                     │      │
│  │  Write consistency: QUORUM (2 of 3 acks)                   │      │
│  │  Read consistency:  LOCAL_QUORUM (for single-region)       │      │
│  │                                                            │      │
│  │    AZ-1          AZ-2          AZ-3                       │      │
│  │  ┌────────┐   ┌────────┐   ┌────────┐                    │      │
│  │  │Node A  │   │Node B  │   │Node C  │                    │      │
│  │  │Replica │   │Replica │   │Replica │                    │      │
│  │  └────────┘   └────────┘   └────────┘                    │      │
│  │                                                            │      │
│  └────────────────────────────────────────────────────────────┘      │
│                                                                      │
│  Object Storage (S3)                                                 │
│  ┌────────────────────────────────────────────────────────────┐      │
│  │  Cross-Region Replication (CRR)                            │      │
│  │                                                            │      │
│  │  us-east-1 ──async──► eu-west-1                            │      │
│  │            ──async──► ap-southeast-1                       │      │
│  │                                                            │      │
│  │  Within region: S3 stores 3+ copies across AZs (built-in) │      │
│  │  Durability: 99.999999999% (11 nines)                      │      │
│  └────────────────────────────────────────────────────────────┘      │
│                                                                      │
└──────────────────────────────────────────────────────────────────────┘
```

---

## 12. Fault Tolerance and Failure Handling

### Failure Scenarios and Mitigations

```
┌──────────────────────────────────────────────────────────────────────────────┐
│                    FAILURE HANDLING MATRIX                                    │
│                                                                              │
│  ┌──────────────────┬─────────────────────────────────────────────────────┐  │
│  │ Failure          │ Mitigation                                          │  │
│  ├──────────────────┼─────────────────────────────────────────────────────┤  │
│  │ CDN edge PoP     │ GeoDNS reroutes to next-nearest PoP.               │  │
│  │ goes down        │ User sees ~50ms latency increase, not outage.       │  │
│  │                  │ Shield layer absorbs the miss traffic.              │  │
│  ├──────────────────┼─────────────────────────────────────────────────────┤  │
│  │ CDN origin       │ Fallback to direct S3 access with signed URLs.     │  │
│  │ shield fails     │ Higher latency but no data loss.                    │  │
│  │                  │ Multiple shield nodes with health checks.           │  │
│  ├──────────────────┼─────────────────────────────────────────────────────┤  │
│  │ Transcoding      │ Kafka retries: message stays in queue until        │  │
│  │ worker crashes   │ another worker picks it up. Checkpointing          │  │
│  │                  │ allows resume from last completed segment.          │  │
│  │                  │ Dead letter queue after 3 retries.                  │  │
│  ├──────────────────┼─────────────────────────────────────────────────────┤  │
│  │ Upload           │ Resumable protocol: client queries upload status   │  │
│  │ interrupted      │ and resumes from last acknowledged chunk.           │  │
│  │                  │ Incomplete uploads auto-cleaned after 24h.          │  │
│  ├──────────────────┼─────────────────────────────────────────────────────┤  │
│  │ Database primary │ Automatic failover to synchronous standby.         │  │
│  │ fails            │ RTO < 30s. Read replicas continue serving reads.   │  │
│  │                  │ Write operations queue briefly, then resume.        │  │
│  ├──────────────────┼─────────────────────────────────────────────────────┤  │
│  │ Redis cluster    │ Redis Sentinel/Cluster auto-failover.              │  │
│  │ node fails       │ View counts: in-memory batch flushed on recovery.  │  │
│  │                  │ Worst case: lose a few seconds of count increments. │  │
│  ├──────────────────┼─────────────────────────────────────────────────────┤  │
│  │ Elasticsearch    │ Replica shards serve reads during primary shard    │  │
│  │ node fails       │ recovery. Cluster rebalances automatically.         │  │
│  │                  │ Temporary search result staleness acceptable.       │  │
│  ├──────────────────┼─────────────────────────────────────────────────────┤  │
│  │ Recommendation   │ Serve cached recommendations from Redis.           │  │
│  │ service down     │ Fallback to trending/popular videos (no persona).  │  │
│  │                  │ Graceful degradation, not failure.                  │  │
│  ├──────────────────┼─────────────────────────────────────────────────────┤  │
│  │ Entire region    │ DNS failover to healthy region.                     │  │
│  │ outage           │ Cross-region S3 replication ensures data available. │  │
│  │                  │ Viewers served from CDN cache during transition.    │  │
│  │                  │ Uploads rerouted to healthy region.                 │  │
│  ├──────────────────┼─────────────────────────────────────────────────────┤  │
│  │ Viral video      │ CDN auto-caches under load. Shield absorbs burst.  │  │
│  │ traffic spike    │ Rate limiting on non-critical APIs (comments).      │  │
│  │                  │ Video streaming itself has highest priority.        │  │
│  └──────────────────┴─────────────────────────────────────────────────────┘  │
│                                                                              │
└──────────────────────────────────────────────────────────────────────────────┘
```

### Degraded Mode Strategy

When the system is under extreme load, we apply progressive degradation:

```
Level 0 (Normal):     All features operational
Level 1 (Elevated):   Disable recommendations, serve trending instead
                      Reduce search result freshness (5 min cache)
Level 2 (High):       Disable comments loading on initial page load
                      Reduce video quality options (drop 240p, 360p)
                      Rate limit uploads to 50% capacity
Level 3 (Critical):   Serve only cached content from CDN
                      Disable uploads entirely
                      Static home page with top 100 trending videos
                      All writes rejected except critical auth flows
```

---

## 13. Scalability

### Horizontal Scaling Approach

```
┌──────────────────────────────────────────────────────────────────────────────┐
│                      SCALABILITY DIMENSIONS                                  │
│                                                                              │
│  ┌───────────────────────────────────────────────────────────────────┐       │
│  │ COMPUTE SCALING                                                   │       │
│  │                                                                   │       │
│  │ Component           │ Scaling Trigger              │ Max Scale    │       │
│  │ ────────────────────┼──────────────────────────────┼──────────── │       │
│  │ API Gateway         │ Requests/sec > 80% capacity  │ 200 nodes   │       │
│  │ Upload Service      │ Active uploads > threshold   │ 100 nodes   │       │
│  │ Streaming Service   │ Concurrent streams           │ 500 nodes   │       │
│  │ Transcoding Workers │ Queue depth > 1000 jobs      │ 20K workers │       │
│  │ Search Service      │ Query latency p99 > 200ms    │ 100 nodes   │       │
│  │ Comment Service     │ Write throughput > threshold  │ 50 nodes    │       │
│  │ Recommendation Svc  │ Request latency p99 > 100ms  │ 200 nodes   │       │
│  │                                                                   │       │
│  │ Autoscaler: Kubernetes HPA + custom metrics from Prometheus       │       │
│  │ Scale-up time: < 2 minutes (warm pool of pre-provisioned nodes)   │       │
│  │ Scale-down: gradual (10% reduction every 5 minutes, with cooldown)│       │
│  └───────────────────────────────────────────────────────────────────┘       │
│                                                                              │
│  ┌───────────────────────────────────────────────────────────────────┐       │
│  │ STORAGE SCALING                                                   │       │
│  │                                                                   │       │
│  │ S3: Effectively unlimited. No manual scaling needed.              │       │
│  │ PostgreSQL: Add read replicas for read scaling.                   │       │
│  │             Reshard for write scaling (rare, planned event).       │       │
│  │ Cassandra: Add nodes to ring. Data rebalances automatically.      │       │
│  │ Redis: Add shards to Redis Cluster for memory scaling.            │       │
│  │ Elasticsearch: Add data nodes, increase shard count at reindex.   │       │
│  └───────────────────────────────────────────────────────────────────┘       │
│                                                                              │
│  ┌───────────────────────────────────────────────────────────────────┐       │
│  │ NETWORK / CDN SCALING                                             │       │
│  │                                                                   │       │
│  │ CDN capacity scales with number of edge PoPs.                     │       │
│  │ For viral events: CDN providers (Akamai, CloudFront) have burst   │       │
│  │ capacity built in. No action needed from our side.                │       │
│  │                                                                   │       │
│  │ Multi-CDN strategy for extreme scale:                             │       │
│  │   Primary CDN handles 70% of traffic                              │       │
│  │   Secondary CDN handles 30% as overflow + failover                │       │
│  │   DNS-based traffic splitting with health checks                  │       │
│  └───────────────────────────────────────────────────────────────────┘       │
│                                                                              │
└──────────────────────────────────────────────────────────────────────────────┘
```

### Handling Viral Videos

```
┌──────────────────────────────────────────────────────────────────┐
│              VIRAL VIDEO SCALING TIMELINE                         │
│                                                                  │
│  T+0 min:  Video uploaded, transcoded, available                 │
│  T+5 min:  Views spike to 10x normal for a new video             │
│            → Anomaly detector flags as "potentially viral"       │
│                                                                  │
│  T+10 min: Views at 50x normal                                   │
│            → Promote to "Hot" tier                                │
│            → Pre-push all segments to ALL edge PoPs (~200)       │
│            → Warm CDN shield caches globally                     │
│                                                                  │
│  T+30 min: Views at 500x normal, trending globally               │
│            → CDN cache hit ratio at 99%+                          │
│            → Origin sees minimal traffic (< 1%)                  │
│            → API servers auto-scaled for metadata requests       │
│            → Comment service rate-limited to prevent overload     │
│                                                                  │
│  T+2 hr:   Peak traffic. Millions of concurrent viewers.         │
│            → System stable: CDN absorbs 99%+ of bandwidth       │
│            → View counter batching: aggregate in Redis,           │
│              flush to DB every 30 seconds instead of per-view    │
│                                                                  │
│  T+24 hr:  Traffic declining. Begin cache demotion.              │
│            → Remove from some edge PoPs, keep in shields         │
│                                                                  │
│  T+7 days: Traffic normalized. Standard caching policy resumes.  │
│                                                                  │
└──────────────────────────────────────────────────────────────────┘
```

---

## 14. Monitoring and Observability

### Key Metrics Dashboard

```
┌──────────────────────────────────────────────────────────────────────────────┐
│                    OBSERVABILITY FRAMEWORK                                    │
│                                                                              │
│  ┌────────────────────────────────────────────────────────────────────┐      │
│  │ VIEWER EXPERIENCE METRICS (most important -- user-facing)         │      │
│  │                                                                    │      │
│  │  Metric                    │ Target     │ Alert Threshold          │      │
│  │  ──────────────────────────┼────────────┼────────────────────────  │      │
│  │  Time to First Frame (TTFF)│ < 2s p50   │ > 3s p50 for 5 min     │      │
│  │                            │ < 4s p99   │ > 5s p99 for 5 min     │      │
│  │  Rebuffering ratio         │ < 0.5%     │ > 1% for 10 min        │      │
│  │  Video start failure rate  │ < 0.1%     │ > 0.5% for 5 min       │      │
│  │  Average bitrate served    │ Monitor    │ Drop > 20% in 10 min   │      │
│  │  Quality switches/min      │ < 2        │ > 5 for 10 min         │      │
│  │  Playback error rate       │ < 0.05%    │ > 0.2% for 5 min       │      │
│  └────────────────────────────────────────────────────────────────────┘      │
│                                                                              │
│  ┌────────────────────────────────────────────────────────────────────┐      │
│  │ INFRASTRUCTURE METRICS                                             │      │
│  │                                                                    │      │
│  │  CDN cache hit ratio       │ > 95%      │ < 90% for 15 min       │      │
│  │  CDN edge latency (p99)    │ < 50ms     │ > 100ms for 10 min     │      │
│  │  Origin 5xx rate           │ < 0.01%    │ > 0.1% for 5 min       │      │
│  │  API latency (p99)         │ < 200ms    │ > 500ms for 5 min      │      │
│  │  Kafka consumer lag        │ < 1000 msg │ > 10000 for 10 min     │      │
│  │  DB connection pool usage  │ < 70%      │ > 90% for 5 min        │      │
│  │  Redis memory usage        │ < 80%      │ > 90%                  │      │
│  └────────────────────────────────────────────────────────────────────┘      │
│                                                                              │
│  ┌────────────────────────────────────────────────────────────────────┐      │
│  │ PIPELINE METRICS                                                   │      │
│  │                                                                    │      │
│  │  Upload success rate       │ > 99.5%    │ < 98% for 30 min       │      │
│  │  Transcoding queue depth   │ < 5000     │ > 20000 for 15 min     │      │
│  │  Transcoding time (1h vid) │ < 30 min   │ > 60 min for 30 min    │      │
│  │  Transcoding failure rate  │ < 0.5%     │ > 2% for 15 min        │      │
│  │  Content moderation time   │ < 10 min   │ > 30 min for 30 min    │      │
│  └────────────────────────────────────────────────────────────────────┘      │
│                                                                              │
│  ┌────────────────────────────────────────────────────────────────────┐      │
│  │ BUSINESS METRICS                                                   │      │
│  │                                                                    │      │
│  │  Daily active viewers      │ Monitor    │ Drop > 10% day-over-day│      │
│  │  Average watch time/user   │ Monitor    │ Drop > 15%             │      │
│  │  Upload volume             │ Monitor    │ Drop > 30%             │      │
│  │  Search click-through rate │ Monitor    │ Drop > 20%             │      │
│  │  Recommendation CTR        │ Monitor    │ Drop > 15%             │      │
│  └────────────────────────────────────────────────────────────────────┘      │
│                                                                              │
│  Tech stack: Prometheus + Grafana (infra), custom telemetry SDK              │
│  in video player (viewer experience), ELK for logs, PagerDuty for alerts.    │
│                                                                              │
└──────────────────────────────────────────────────────────────────────────────┘
```

### Distributed Tracing for Video Playback

```
Trace: viewer_playback_session_abc123

[DNS Resolution]        |████|                                    12ms
[CDN Edge Connect]      |██|                                       8ms
[TLS Handshake]         |██████|                                  22ms
[Fetch Master Manifest] |████|                                    15ms
[Parse Manifest]        |█|                                        3ms
[ABR: Select 720p]      |█|                                        1ms
[Fetch Segment 0]       |██████████|                              38ms
  └─[CDN Cache HIT]     |████|                                    16ms
[Decode + Render]       |████████|                                30ms
[TTFF Total]            ├─────────────────────────────────────┤  129ms
                                                              
[Fetch Segment 1]              |█████████|                        35ms
  └─[CDN Cache HIT]            |████|                             14ms
[Fetch Segment 2]                     |██████████████|            55ms
  └─[CDN Cache MISS → Shield]         |████████████|              48ms
```

---

## 15. Trade-offs and Design Decisions

### Decision 1: Pre-Transcode All Resolutions vs On-Demand Transcoding

```
┌──────────────────────────────────────────────────────────────────────────┐
│                                                                          │
│  OPTION A: Pre-Transcode (Our Choice)                                    │
│  ─────────────────────────────────────                                   │
│  + Instant playback: no transcoding delay when viewer requests quality   │
│  + CDN-friendly: static files, highly cacheable                          │
│  + Simpler streaming service: just serve files                           │
│  - Higher storage cost: 5-7x per video (all resolutions)                 │
│  - Wasted compute: 80% of videos get < 100 views; many resolutions       │
│    are never watched                                                     │
│                                                                          │
│  OPTION B: On-Demand Transcoding                                         │
│  ─────────────────────────────────                                       │
│  + Lower storage: only store raw + most-requested resolutions            │
│  + Less wasted compute for unpopular content                             │
│  - Playback delay on first request for a resolution                      │
│  - Complex real-time transcoding infrastructure                          │
│  - CDN caching less effective (dynamic content)                          │
│                                                                          │
│  HYBRID APPROACH (Netflix-style):                                        │
│  - Popular content (top 20%): pre-transcode all resolutions              │
│  - Long-tail (bottom 80%): pre-transcode only 360p + 720p               │
│  - On-demand transcode other resolutions if requested                    │
│  - Background job promotes videos to full pre-transcode once popular     │
│                                                                          │
└──────────────────────────────────────────────────────────────────────────┘
```

### Decision 2: HLS vs DASH vs Both (CMAF)

```
┌──────────────────────────────────────────────────────────────────────────┐
│                                                                          │
│  Our Choice: CMAF (Common Media Application Format)                      │
│                                                                          │
│  Generate fMP4 segments once → serve with both HLS and DASH manifests    │
│                                                                          │
│  ┌──────────────────┐                                                    │
│  │  fMP4 Segments   │──── HLS manifest (.m3u8) ──► Apple devices         │
│  │  (single encode) │──── DASH manifest (.mpd) ──► Android / Web         │
│  └──────────────────┘                                                    │
│                                                                          │
│  Benefits:                                                               │
│  - Single set of segments reduces storage by ~40% vs separate formats    │
│  - Universal device support                                              │
│  - Simplified transcoding pipeline                                       │
│  - Industry convergence direction                                        │
│                                                                          │
│  Trade-off:                                                              │
│  - Slightly more complex manifest generation                             │
│  - Some older devices may not support fMP4 in HLS (fallback to .ts)      │
│                                                                          │
└──────────────────────────────────────────────────────────────────────────┘
```

### Decision 3: Push vs Pull CDN Strategy

```
┌──────────────────────────────────────────────────────────────────────────┐
│                                                                          │
│  PUSH (Proactive): Upload segments to CDN before anyone requests them    │
│  PULL (Reactive):  CDN fetches from origin on first cache miss           │
│                                                                          │
│  Our Choice: HYBRID                                                      │
│                                                                          │
│  ┌─────────────────────────────────────────────────────────┐             │
│  │  Content Tier    │ Strategy │ Rationale                  │             │
│  │  ────────────────┼──────────┼──────────────────────────  │             │
│  │  Hot (0.1%)      │ PUSH     │ Guaranteed instant start   │             │
│  │                  │          │ everywhere. Worth the cost. │             │
│  │  Warm (5%)       │ PUSH to  │ Cover major markets.       │             │
│  │                  │ shields  │ Edge pulls from shield.    │             │
│  │  Cool (20%)      │ PULL     │ CDN fetches on first view. │             │
│  │                  │          │ First viewer gets slower    │             │
│  │                  │          │ start; subsequent are fast. │             │
│  │  Cold (74.9%)    │ PULL     │ May not even be cached.    │             │
│  │                  │          │ Direct S3 serving is fine   │             │
│  │                  │          │ for very low view counts.   │             │
│  └─────────────────────────────────────────────────────────┘             │
│                                                                          │
└──────────────────────────────────────────────────────────────────────────┘
```

### Decision 4: Monolith vs Microservices

```
┌──────────────────────────────────────────────────────────────────────────┐
│                                                                          │
│  Our Choice: Microservices (for a platform at this scale)                 │
│                                                                          │
│  Justification:                                                          │
│  - Upload, transcoding, streaming, search, and recommendations have      │
│    vastly different scaling characteristics                               │
│  - Transcoding is GPU-heavy; streaming is bandwidth-heavy;               │
│    search is CPU+memory heavy. Different hardware requirements.          │
│  - Independent deployability: update recommendation algorithm             │
│    without touching video streaming                                      │
│  - Team autonomy: separate teams own separate services                   │
│                                                                          │
│  Service boundaries:                                                     │
│  ┌──────────────────────────────────────────────────────────────┐        │
│  │ Upload Service ──► Video Processing Pipeline (async)         │        │
│  │ Streaming Service (stateless, horizontally scalable)         │        │
│  │ Metadata Service (CRUD + caching)                            │        │
│  │ Search Service (Elasticsearch wrapper)                       │        │
│  │ Recommendation Service (ML model serving)                    │        │
│  │ User Service (auth, profiles)                                │        │
│  │ Social Service (comments, likes, subscriptions)              │        │
│  │ Notification Service (async, fan-out)                        │        │
│  └──────────────────────────────────────────────────────────────┘        │
│                                                                          │
│  Trade-off:                                                              │
│  - Increased operational complexity (service mesh, distributed tracing)  │
│  - Network overhead for inter-service communication                      │
│  - Data consistency across services requires careful design              │
│                                                                          │
└──────────────────────────────────────────────────────────────────────────┘
```

### Decision 5: Segment Duration

```
┌──────────────────────────────────────────────────────────────────────────┐
│                                                                          │
│  Shorter segments (2s)          vs          Longer segments (10s)         │
│  ─────────────────────                     ──────────────────────         │
│  + Faster quality switches                 + Fewer HTTP requests          │
│  + Lower latency for live                  + Better compression           │
│  + Finer-grained ABR control               + Lower CDN overhead           │
│  - More HTTP requests                      - Slower quality switches      │
│  - Higher CDN overhead                     - Higher live latency          │
│  - Worse compression ratio                 - Coarser ABR control          │
│                                                                          │
│  Our choice: 6 seconds                                                   │
│  Industry standard compromise. Apple recommends 6s for HLS.              │
│  For low-latency live: use 2s segments with chunked transfer encoding.   │
│                                                                          │
└──────────────────────────────────────────────────────────────────────────┘
```

---

## 16. Interview Deep-Dive Questions

### Q1: How do you handle viral videos with sudden traffic spikes?

**Answer:** Viral videos are handled through a multi-layered defense:

1. **CDN absorbs the burst.** Since video segments are static, immutable files,
   CDN caching is extremely effective. Once a segment is cached at an edge PoP,
   all subsequent requests from that region are served from cache without touching
   origin. A viral video with 10M views might only result in ~200 origin fetches
   (one per edge PoP for each segment).

2. **Anomaly detection promotes content.** A real-time monitoring pipeline tracks
   view velocity (views/minute) per video. When a video exceeds 10x its baseline,
   we proactively push its segments to all edge PoPs globally (instead of waiting
   for pull-through caching). This reduces first-viewer latency in new regions.

3. **View counting uses batching.** Under viral load, per-view database writes
   would overwhelm the database. Instead, view counts are atomically incremented
   in Redis (O(1) per view), and a background job flushes the aggregated count to
   PostgreSQL every 30 seconds. The displayed count is approximate and that is
   acceptable -- "1.2M views" vs "1,234,567 views" does not matter to viewers.

4. **Non-critical services are rate-limited.** Comments, likes, and other
   engagement features are rate-limited to protect the core streaming path.
   Viewers can always watch the video even if commenting is temporarily degraded.

---

### Q2: How does adaptive bitrate streaming work end-to-end?

**Answer:** ABR streaming works through a tight feedback loop between the server
(which provides multiple quality options) and the client player (which chooses):

**Server side:** The transcoding pipeline generates the same video at multiple
quality levels (240p through 4K), each split into small segments (6 seconds).
A master manifest file lists all available quality levels with their bitrates
and resolution. Each quality level has its own sub-manifest listing all segment
URLs.

**Client side:** The video player uses an ABR algorithm that continuously
monitors: (a) measured download throughput (exponentially weighted moving
average of recent segment downloads), (b) current buffer level (how many
seconds of video are buffered ahead), and (c) device capabilities.

The algorithm picks the highest quality whose bitrate is safely below the
measured throughput (with a 20% safety margin). If buffer drops dangerously
low (< 5 seconds), it aggressively drops quality. If buffer is healthy
(> 30 seconds), it can cautiously try a higher quality.

Since each segment is an independent HTTP request, the client can switch quality
at every segment boundary (every 6 seconds) without interruption.

---

### Q3: How do you detect and handle copyrighted content?

**Answer:** Copyright detection uses a two-phase approach:

**Phase 1: Audio/Video Fingerprinting (Content ID)**
- During transcoding, we extract perceptual fingerprints from both the audio
  track and video frames. Audio fingerprinting uses spectral analysis (similar
  to Shazam) to create a compact representation of the audio. Video
  fingerprinting uses perceptual hashing of keyframes.
- These fingerprints are compared against a reference database of copyrighted
  content provided by rights holders. The reference database contains
  fingerprints of millions of songs, movies, and TV shows.
- Matching is fuzzy -- it detects copyrighted content even if the video has
  been re-encoded, cropped, sped up, or has overlaid commentary.

**Phase 2: Policy Application**
- If a match is found, the rights holder's policy determines the action:
  - **Block:** Video is prevented from publishing.
  - **Monetize:** Video is published but ad revenue goes to rights holder.
  - **Track:** Video is published normally; rights holder just wants analytics.
- Creators can dispute claims through an appeal process.

**Technical implementation:**
- Fingerprint extraction runs as a DAG step in the transcoding pipeline
- Reference database is stored in a specialized similarity search index
  (approximate nearest neighbor search)
- Matching runs in parallel with transcoding to avoid adding latency
- New reference fingerprints from rights holders are ingested via a batch
  pipeline and retroactively scanned against existing content

---

### Q4: How would you design live streaming on top of this architecture?

**Answer:** Live streaming reuses much of the VOD infrastructure but with key
differences for low latency:

```
┌──────────────────────────────────────────────────────────────────┐
│              LIVE STREAMING ARCHITECTURE                          │
│                                                                  │
│  Broadcaster ──► RTMP/SRT Ingest ──► Live Transcoder             │
│                  Server              (real-time, not offline)     │
│                                          │                       │
│                                     ┌────┼────┐                  │
│                                     │    │    │                   │
│                                    360p 720p 1080p               │
│                                     │    │    │                   │
│                                     └────┼────┘                  │
│                                          │                       │
│                                     Segmenter                    │
│                                     (2s segments                 │
│                                      for low latency)            │
│                                          │                       │
│                                     Live Manifest                │
│                                     (sliding window              │
│                                      of last 30s)                │
│                                          │                       │
│                                     CDN Push                     │
│                                     (real-time)                  │
│                                          │                       │
│                                     Viewers                      │
│                                     (3-10s latency)              │
└──────────────────────────────────────────────────────────────────┘
```

**Key differences from VOD:**
- **Ingest protocol:** RTMP or SRT from broadcaster software (OBS, Streamlabs)
  to our ingest servers. These are stateful, long-lived connections.
- **Real-time transcoding:** Must keep up with the live feed. Uses dedicated
  GPU instances, not batch processing. One transcoder per stream.
- **Shorter segments:** 2-second segments (vs 6s for VOD) for lower latency.
  Trade-off: more HTTP requests, worse compression.
- **Sliding window manifest:** The HLS manifest only contains the last ~30
  seconds of segments (sliding window), not the entire video.
- **CDN push, not pull:** Segments are pushed to CDN as soon as they are
  generated, rather than waiting for viewer requests.
- **DVR / rewind:** Store recent segments (last 2-4 hours) for DVR
  functionality. After stream ends, hand off to standard VOD pipeline for
  archival transcoding.

---

### Q5: How do you optimize for mobile vs desktop clients?

**Answer:** Mobile and desktop have fundamentally different constraints:

| Factor           | Mobile                          | Desktop                     |
|------------------|---------------------------------|-----------------------------|
| Screen size      | 5-7 inches                      | 13-32 inches                |
| Max useful res.  | 720p (most), 1080p (flagship)   | 1080p-4K                    |
| Network          | Variable (4G/5G/WiFi)           | Stable broadband            |
| Battery          | Limited, decode costs power     | Not a concern               |
| Data caps        | Common (2-50 GB/month)          | Rare                        |

**Optimizations:**
- **Resolution capping:** Mobile app does not request > 1080p even on WiFi.
  No point sending 4K to a 6-inch screen.
- **Codec selection:** Prefer H.265/HEVC on iOS (hardware decode support).
  Prefer VP9/AV1 on Android (better software decode). These save 40-50%
  bandwidth vs H.264.
- **Lower initial quality:** Mobile starts at 360p and ramps up (vs 720p on
  desktop) to minimize time-to-first-frame on cellular.
- **Prefetch strategy:** On mobile WiFi, aggressively prefetch next 30s.
  On cellular, only prefetch next 10s to conserve data.
- **Offline download:** Mobile app supports downloading videos at chosen
  quality for offline viewing. Desktop typically does not.
- **Thumbnail quality:** Serve smaller thumbnails (320px) on mobile vs
  full-size (1280px) on desktop to reduce page load time.

---

### Q6: How do you handle view counting at scale without losing accuracy?

**Answer:** View counting at our scale (46K views/sec average, 140K peak)
requires careful architecture:

**Not a simple database increment.** A naive `UPDATE videos SET views = views + 1`
would cause massive lock contention on hot rows (viral videos could get
thousands of increments per second on the same row).

**Our approach (multi-tier counting):**

1. **Client-side deduplication:** The video player only reports a "view" after
   30 seconds of watch time (prevents accidental/bot views). A session token
   prevents duplicate reports from the same session.

2. **Redis atomic counter:** View events hit a Redis cluster where we do
   `INCR video:{id}:views`. Redis handles 100K+ increments/sec per node
   easily. This is the "real-time" count shown to users.

3. **Kafka event stream:** Every view event is also published to Kafka for
   durable recording. This is the source of truth for analytics.

4. **Periodic DB flush:** A background consumer reads from Redis every 30
   seconds and batch-updates PostgreSQL. This coalesces thousands of
   increments into a single UPDATE per video.

5. **Anti-fraud pipeline:** A separate Kafka consumer runs view validation
   (IP rate limiting, bot detection, engagement scoring) and may subtract
   fraudulent views in a daily batch job.

---

### Q7: What is your content moderation strategy?

**Answer:** Content moderation operates at multiple levels:

1. **Pre-publish automated scan** (within the transcoding pipeline):
   - Nudity/violence detection (computer vision model, ~95% accuracy)
   - Audio transcription + toxicity classification
   - Copyright fingerprint matching (Content ID)
   - Known-bad content hash matching (CSAM database via PhotoDNA)

2. **Post-publish monitoring:**
   - User reports (flagging system)
   - Continued ML scanning on reported content at higher sensitivity
   - Trending content gets priority review

3. **Human review:**
   - Content flagged by ML with confidence 60-95% goes to human reviewers
   - Content flagged with confidence > 95% is auto-removed (pending appeal)
   - Content with confidence < 60% is published but monitored
   - Human review team for appeals and edge cases

4. **Actions:**
   - Age-restrict, demonetize, hide from recommendations, remove, or ban

---

### Q8: How do you design the subscription feed (timeline)?

**Answer:** When a creator publishes a video, all subscribers should see it in
their feed. This is a classic fan-out problem:

**Hybrid fan-out approach:**
- **Small creators (< 10K subscribers):** Fan-out on write. When creator
  publishes, push the video_id into each subscriber's feed (stored in Redis
  sorted set by publish_time). This makes reads O(1) -- just fetch the sorted
  set.
- **Large creators (> 10K subscribers):** Fan-out on read. Store the video in
  the creator's publish list. When a subscriber opens their feed, pull from all
  subscribed creators and merge/rank. Cache the result in Redis for 5 minutes.
- **Mega creators (> 1M subscribers):** Same as large, but with additional
  optimizations -- most subscribers are inactive on any given day, so fan-out
  on write would waste 90%+ of the work.

---

### Q9: How do you ensure smooth playback across different network conditions?

**Answer:** Beyond ABR (covered in Q2), several techniques ensure smoothness:

- **Buffer management:** The player maintains a 30-60 second buffer when
  bandwidth allows. This absorbs short network hiccups without visible impact.
- **Segment prefetching:** While playing segment N, we start downloading
  segment N+1 and N+2 in parallel.
- **Quality floor:** Even in worst conditions, we serve at least 240p rather
  than buffering. Low quality is better than no video.
- **Server-side bandwidth estimation:** CDN can analyze TCP throughput and
  include hints in HTTP headers, giving the client better initial estimates.
- **Multi-CDN failover:** If one CDN PoP is slow, the client can failover to
  an alternative CDN mid-stream.
- **Persistent connections:** HTTP/2 multiplexing avoids per-segment TCP
  handshake overhead.

---

### Q10: How do you handle video search at scale?

**Answer:** Video search is powered by Elasticsearch with custom ranking:

**Indexing pipeline:**
- On video publish, metadata (title, description, tags) is indexed in
  Elasticsearch via a Kafka consumer.
- Auto-generated captions (speech-to-text) are indexed for spoken content
  search.
- Refresh interval: 30 seconds (newly uploaded video searchable within a minute).

**Ranking signals:**
- Text relevance (BM25 on title, description, tags, captions)
- Recency boost (newer videos ranked higher)
- Popularity (view count, engagement rate)
- Creator authority (subscriber count, historical performance)
- Personalization (user's watch history, preferred categories)

**Performance:**
- 50 Elasticsearch shards, 1 replica each = 100 shard copies across cluster
- Query latency: < 100ms p50, < 200ms p99
- Autocomplete: trie-based suggestions with Redis cache (< 50ms)

---

### Q11: What is the data retention and storage tiering strategy?

**Answer:** Not all data has equal access patterns. We use storage tiering:

```
Tier            │ Storage Class       │ Content                    │ Cost
────────────────┼─────────────────────┼────────────────────────────┼────────
Hot (0-30 days) │ S3 Standard         │ All new videos             │ $$$
Warm (30-180d)  │ S3 Infrequent Access│ Videos with declining views│ $$
Cold (180d+)    │ S3 Glacier Instant  │ Rarely viewed archive      │ $
Deep (2yr+)     │ S3 Glacier Deep     │ Raw uploads (legal hold)   │ $0.1
```

- Processed segments stay in Hot/Warm tiers (since CDN caches the popular ones).
- Raw uploads are moved to deep archive after transcoding is confirmed successful.
  Kept for re-transcoding needs (new codec support) and legal compliance.
- Lifecycle policies automate tier transitions based on access patterns.

---

### Q12: How do you handle DRM (Digital Rights Management)?

**Answer:** DRM is essential for premium/paid content (Netflix model):

- **Widevine** (Google): Android, Chrome, smart TVs
- **FairPlay** (Apple): iOS, Safari, Apple TV
- **PlayReady** (Microsoft): Edge, Xbox, Windows apps

Each DRM system requires separate encryption of the same content. With CMAF,
we use Common Encryption (CENC) so the same encrypted segments work with both
Widevine and PlayReady. FairPlay requires its own encryption (SAMPLE-AES).

**License server flow:**
1. Client requests video manifest
2. Manifest includes DRM initialization data
3. Client sends license request to DRM license server
4. License server validates entitlement (does user have subscription?)
5. Returns decryption key with usage rules (expiry, device limits)
6. Client decrypts and plays segments in hardware-protected pipeline

---

### Q13: How do you handle multi-language and subtitles?

**Answer:**
- **Subtitle formats:** WebVTT (streaming) and SRT (upload). Stored alongside
  video segments in S3.
- **Auto-generated captions:** Speech-to-text ML model runs as a transcoding
  DAG step. Supports 50+ languages.
- **Community contributions:** Viewers can submit subtitle corrections.
- **Manifest integration:** Subtitle tracks listed in HLS/DASH manifest as
  separate streams. Client selects based on user preference.
- **Storage:** Subtitles are tiny (< 100 KB per language per video) so all
  language variants are pre-pushed to CDN.

---

### Q14: What is your approach to A/B testing the video player and recommendation algorithm?

**Answer:**
- **Player A/B testing:** Different ABR algorithms, buffer sizes, or initial
  quality selection. Metrics: TTFF, rebuffering ratio, average quality served.
  Use consistent hashing on user_id to ensure stable assignment.
- **Recommendation A/B testing:** Different ranking models or candidate
  generation strategies. Metrics: watch time, click-through rate, user
  retention. Careful about novelty effects -- run tests for at least 2 weeks.
- **Gradual rollout:** New algorithms start at 1% of traffic, monitored for
  regressions, then scaled to 5%, 20%, 50%, 100%.
- **Holdback group:** Always maintain a small control group (1%) on the
  previous algorithm for continuous comparison.

---

### Q15: How would you estimate the total infrastructure cost?

**Answer:** Rough order-of-magnitude for a platform at YouTube scale:

```
Component              │ Monthly Estimate
───────────────────────┼──────────────────
CDN bandwidth (448 PB) │ $500M - $800M (at volume discounts)
Object storage (64 PB) │ $1.5M - $2M
Compute (API + services)│ $10M - $20M
Transcoding compute    │ $30M - $50M (heavy spot instance usage)
Databases              │ $5M - $10M
Redis / caching        │ $2M - $5M
Elasticsearch          │ $3M - $5M
ML / Recommendations   │ $10M - $20M
───────────────────────┼──────────────────
Total                  │ ~$560M - $910M / month
```

CDN bandwidth dominates cost (70-80%+ of total). This is why Netflix and
Google built their own CDN (Open Connect, Google Global Cache) -- at their
scale, owning the CDN infrastructure is vastly cheaper than paying a third
party. Netflix places its own servers (Open Connect Appliances) directly
inside ISP networks, eliminating transit costs entirely.

---

## Appendix: Quick Reference Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                                                                             │
│                    VIDEO STREAMING PLATFORM                                  │
│                    COMPLETE ARCHITECTURE                                     │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                        UPLOAD PATH                                  │    │
│  │  Creator → Chunked Upload API → S3 (raw) → Kafka → Transcoder     │    │
│  │  Workers → S3 (processed: HLS segments) → CDN pre-push            │    │
│  │  Parallel: Thumbnail gen, Content ID, Moderation, Search index     │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                        WATCH PATH                                   │    │
│  │  Viewer → GeoDNS → CDN Edge (cache hit 85%) → CDN Shield (95%)    │    │
│  │  → S3 origin. Client ABR selects quality per segment.              │    │
│  │  Metadata: API Gateway → Metadata Service → Redis cache / PG      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                        DATA STORES                                  │    │
│  │  PostgreSQL: video metadata, users, subscriptions                   │    │
│  │  Cassandra: comments, watch history                                 │    │
│  │  Elasticsearch: search index                                        │    │
│  │  Redis: view counts, caching, session, recommendations              │    │
│  │  S3: video files (raw + processed), thumbnails                      │    │
│  │  Kafka: async pipeline orchestration, event streaming               │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                        KEY NUMBERS                                   │    │
│  │  800M DAU | 4B views/day | 46K views/sec | 500K uploads/day        │    │
│  │  175 TB new storage/day | 448 PB egress/day | 155 Tbps peak        │    │
│  │  CDN hit ratio > 95% | TTFF < 2s | Availability 99.99%            │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```
