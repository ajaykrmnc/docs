# Design a Ticket Booking System (BookMyShow / Ticketmaster)
**Difficulty:** Hard | **Companies:** Amazon, Google, Microsoft, Uber, Swiggy

> For the low-level class design, see [LLD: Movie Ticket Booking](/lld/17-movie-ticket-booking)

---

## 1. Problem Statement and Scope

Design a large-scale ticket booking system (similar to BookMyShow, Ticketmaster, or Fandango) that
allows users to browse events -- movies, concerts, sports, theatre -- search by location, date, and
genre, view real-time seat maps, select seats, make payments, and receive confirmations.

The system must handle **extreme concurrency** during flash sales (e.g. a BTS concert where 500K
fans compete for 50K seats in seconds) while guaranteeing **zero double bookings** and maintaining
sub-second response times for seat availability queries.

### In Scope
- Event/movie/show catalog management and discovery
- Real-time seat map with availability status
- Concurrent seat selection with temporary holds
- Payment processing with timeout and retry logic
- Booking confirmation, history, and cancellation
- Flash sale / high-demand event handling
- Notifications (email, SMS, push)
- Search and recommendations

### Out of Scope
- Theater/venue onboarding and admin panel (CMS)
- Content streaming (for virtual events)
- Loyalty points / reward programs
- Third-party affiliate and reseller integrations
- Ticket transfer or secondary marketplace

---

## 2. Functional Requirements

| ID   | Requirement                          | Priority |
|------|--------------------------------------|----------|
| FR-1 | Browse events/movies by city, date   | P0       |
| FR-2 | Search with filters (genre, language) | P0       |
| FR-3 | View seat map with real-time status   | P0       |
| FR-4 | Select seats and hold temporarily     | P0       |
| FR-5 | Process payment and confirm booking   | P0       |
| FR-6 | Booking cancellation and refund       | P0       |
| FR-7 | Booking history and e-ticket          | P0       |
| FR-8 | Notifications (confirmation, remind)  | P1       |
| FR-9 | Reviews and ratings for events        | P1       |
| FR-10| Dynamic pricing for high-demand shows | P2       |
| FR-11| Group booking (10+ seats together)    | P2       |
| FR-12| Waiting list for sold-out events      | P2       |

### User Journeys

```
┌───────────────────────────────────────────────────────────────────────────┐
│                         PRIMARY BOOKING FLOW                             │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  ┌──────────┐   ┌──────────┐   ┌──────────┐   ┌──────────┐   ┌────────┐│
│  │  Browse   │──▸│  Select  │──▸│  Select  │──▸│  Make    │──▸│ Receive││
│  │  Events   │   │  Show    │   │  Seats   │   │ Payment  │   │ Ticket ││
│  └──────────┘   └──────────┘   └──────────┘   └──────────┘   └────────┘│
│       │                             │               │                    │
│       ▼                             ▼               ▼                    │
│  Filter by city,             Seats held for    On failure,               │
│  date, genre,                5-10 minutes      seats auto-released       │
│  language                    (TTL-based)                                  │
│                                                                          │
└───────────────────────────────────────────────────────────────────────────┘
```

---

## 3. Non-Functional Requirements

| Requirement              | Target                                              |
|--------------------------|-----------------------------------------------------|
| Availability             | 99.99% (52 min downtime/year)                       |
| Seat consistency         | **Zero** double bookings (strong consistency)        |
| Booking flow latency     | End-to-end < 30 seconds (excluding payment gateway) |
| Seat map load time       | < 500ms at P99                                      |
| Flash sale concurrency   | 500K concurrent users competing for 50K seats       |
| Search latency           | < 200ms at P95                                      |
| Notification delivery    | < 60 seconds after booking confirmation             |
| Data durability          | Zero booking data loss                              |
| Eventual consistency     | Event metadata, reviews: < 5 seconds propagation    |
| Horizontal scalability   | Scale to 10x load within 15 minutes (auto-scaling)  |

### Consistency Requirements by Data Type

```
┌──────────────────────────┬─────────────────────┬───────────────────────┐
│       Data Type          │  Consistency Model   │       Rationale       │
├──────────────────────────┼─────────────────────┼───────────────────────┤
│ Seat inventory / holds   │ Strong consistency   │ No double booking     │
│ Booking records          │ Strong consistency   │ Financial accuracy    │
│ Payment transactions     │ Strong consistency   │ Idempotency required  │
│ Event catalog / metadata │ Eventual consistency │ Reads >> Writes       │
│ Search index             │ Near-real-time (~2s) │ Acceptable lag        │
│ Reviews and ratings      │ Eventual consistency │ Non-critical path     │
│ User sessions            │ Session consistency  │ Per-user state        │
└──────────────────────────┴─────────────────────┴───────────────────────┘
```

---

## 4. Back-of-Envelope Estimation

### Traffic Estimates

```
Daily active users (DAU):            50M
Daily bookings:                      10M
Avg seats per booking:               2.5
Daily seat transactions:             25M
Daily seat availability checks:      50M (5x bookings -- browsing without buying)
Peak QPS (normal):                   10M / 86400 ≈ 115 bookings/sec
Peak QPS (flash sale, 10s burst):    500K users / 10s = 50K req/sec
```

### Storage Estimates

```
┌───────────────────────────────────────────────────────────────────┐
│                     STORAGE ESTIMATION                            │
├─────────────────────────────┬─────────────────────────────────────┤
│ Booking record              │ ~2 KB each                          │
│ Daily booking storage       │ 2 KB × 10M = 20 GB/day             │
│ Annual booking storage      │ 20 GB × 365 = 7.3 TB/year          │
│                             │                                     │
│ Event metadata              │ ~5 KB each (includes images refs)   │
│ Total events (active)       │ 100K events × 5 KB = 500 MB        │
│                             │                                     │
│ Seat inventory (per show)   │ ~100 bytes/seat                     │
│ Active seat inventory       │ 100K shows × 1K seats × 100B = 10GB│
│                             │                                     │
│ User profiles               │ ~1 KB each                          │
│ Total users                 │ 200M × 1 KB = 200 GB               │
│                             │                                     │
│ Search index (Elasticsearch)│ ~2 GB (event + show metadata)       │
└─────────────────────────────┴─────────────────────────────────────┘
```

### Bandwidth Estimates

```
Seat map response:          ~50 KB (1000 seats with status, coordinates, pricing)
Seat map peak bandwidth:    50 KB × 50K req/sec = 2.5 GB/sec (flash sale)
Event listing response:     ~10 KB (paginated, 20 events)
Average API response:       ~5 KB
Normal bandwidth:           5 KB × 5000 req/sec = 25 MB/sec
```

### Redis Memory for Seat Holds

```
Active holds at any moment: ~500K seats (assuming 5-min hold, 10M daily bookings)
Per-hold Redis entry:       ~200 bytes (key + metadata)
Redis memory for holds:     500K × 200B = 100 MB (trivial)
Flash sale spike:           50K holds × 200B = 10 MB additional
```

---

## 5. API Design

### 5.1 Event Discovery APIs

```
GET /v1/events
    ?city=mumbai
    &date=2026-04-15
    &category=movies|concerts|sports
    &genre=action
    &language=hindi
    &page=1
    &limit=20
    
Response 200:
{
  "events": [
    {
      "id": "evt_abc123",
      "title": "Avengers: Secret Wars",
      "category": "movie",
      "genre": ["action", "sci-fi"],
      "rating": 4.5,
      "languages": ["hindi", "english"],
      "thumbnail_url": "https://cdn.example.com/...",
      "min_price": 150,
      "shows_available": 42
    }
  ],
  "pagination": { "page": 1, "total_pages": 12, "total_results": 235 }
}
```

```
GET /v1/events/{event_id}/shows
    ?city=mumbai
    &date=2026-04-15
    
Response 200:
{
  "shows": [
    {
      "show_id": "shw_xyz789",
      "event_id": "evt_abc123",
      "venue": { "id": "ven_001", "name": "PVR Phoenix", "city": "mumbai" },
      "screen": "Screen 3",
      "start_time": "2026-04-15T14:30:00+05:30",
      "end_time": "2026-04-15T17:15:00+05:30",
      "available_seats": 180,
      "total_seats": 250,
      "pricing": {
        "silver": 150,
        "gold": 250,
        "platinum": 400
      }
    }
  ]
}
```

### 5.2 Seat Map API

```
GET /v1/shows/{show_id}/seats

Response 200:
{
  "show_id": "shw_xyz789",
  "layout": {
    "rows": 15,
    "columns": 20,
    "screen_position": "top"
  },
  "sections": [
    {
      "type": "platinum",
      "price": 400,
      "seats": [
        { "id": "A1", "row": "A", "number": 1, "status": "available" },
        { "id": "A2", "row": "A", "number": 2, "status": "held" },
        { "id": "A3", "row": "A", "number": 3, "status": "booked" }
      ]
    }
  ],
  "last_updated": "2026-04-15T14:25:00Z",
  "cache_ttl_seconds": 5
}
```

### 5.3 Booking APIs

```
POST /v1/bookings/hold
Headers: Authorization: Bearer <token>
         Idempotency-Key: <uuid>

Body:
{
  "show_id": "shw_xyz789",
  "seat_ids": ["A1", "A4", "A5"],
  "user_id": "usr_456"
}

Response 200:
{
  "hold_token": "hld_abc123def456",
  "seats_held": ["A1", "A4", "A5"],
  "hold_expires_at": "2026-04-15T14:35:00Z",
  "ttl_seconds": 480,
  "total_amount": 1200.00,
  "breakdown": [
    { "seat": "A1", "type": "platinum", "price": 400 },
    { "seat": "A4", "type": "platinum", "price": 400 },
    { "seat": "A5", "type": "platinum", "price": 400 }
  ]
}

Response 409 (Conflict):
{
  "error": "SEATS_UNAVAILABLE",
  "unavailable_seats": ["A4"],
  "message": "Some selected seats are no longer available"
}
```

```
POST /v1/bookings/confirm
Headers: Authorization: Bearer <token>
         Idempotency-Key: <uuid>

Body:
{
  "hold_token": "hld_abc123def456",
  "payment_info": {
    "method": "upi",
    "upi_id": "user@upi",
    "amount": 1200.00
  }
}

Response 200:
{
  "booking_id": "bkg_789xyz",
  "status": "confirmed",
  "e_ticket_url": "https://tickets.example.com/bkg_789xyz",
  "qr_code_url": "https://cdn.example.com/qr/bkg_789xyz.png",
  "seats": ["A1", "A4", "A5"],
  "show_details": { ... },
  "payment_receipt_id": "pay_receipt_123"
}
```

```
DELETE /v1/bookings/{booking_id}

Response 200:
{
  "booking_id": "bkg_789xyz",
  "status": "cancelled",
  "refund": {
    "amount": 1080.00,
    "deduction": 120.00,
    "reason": "cancellation_fee_10_percent",
    "refund_to": "original_payment_method",
    "estimated_completion": "2026-04-18T00:00:00Z"
  }
}
```

### 5.4 Search API

```
GET /v1/search
    ?q=avengers
    &city=mumbai
    &lat=19.076
    &lon=72.877
    &radius_km=10
    &category=movies
    &sort=relevance|date|rating|price_low

Response 200:
{
  "results": [ ... ],
  "facets": {
    "genres": [{"name": "action", "count": 12}, ...],
    "languages": [{"name": "hindi", "count": 8}, ...],
    "price_ranges": [{"range": "100-200", "count": 15}, ...]
  }
}
```

### Rate Limiting Strategy

```
┌──────────────────────────────────────────────────────────────────────────┐
│                        API RATE LIMITS                                   │
├─────────────────────┬──────────────────┬─────────────────────────────────┤
│ Endpoint            │ Rate Limit       │ Notes                           │
├─────────────────────┼──────────────────┼─────────────────────────────────┤
│ GET /events         │ 100 req/min/user │ Cacheable, lenient              │
│ GET /shows/{}/seats │ 30 req/min/user  │ Higher during flash sale        │
│ POST /bookings/hold │ 5 req/min/user   │ Prevent seat hoarding           │
│ POST /bookings/conf │ 3 req/min/user   │ Tied to active hold             │
│ GET /search         │ 60 req/min/user  │ Elasticsearch backed            │
│ Flash sale queue    │ 1 req/event/user │ One entry per user per event    │
└─────────────────────┴──────────────────┴─────────────────────────────────┘
```

---

## 6. Data Model and Database Selection

### 6.1 Entity-Relationship Overview

```
┌──────────┐     ┌───────────┐     ┌───────────┐     ┌──────────┐
│  User    │     │   Event   │     │   Venue   │     │  Screen  │
├──────────┤     ├───────────┤     ├───────────┤     ├──────────┤
│ user_id  │     │ event_id  │     │ venue_id  │     │screen_id │
│ name     │     │ title     │     │ name      │     │venue_id  │
│ email    │     │ category  │     │ city      │     │name      │
│ phone    │     │ genre     │     │ address   │     │capacity  │
│ city     │     │ language  │     │ lat/lon   │     │layout    │
│ password │     │ duration  │     │ screens   │     │seat_map  │
│ created  │     │ rating    │     │ amenities │     │          │
└──────────┘     │ poster_url│     └─────┬─────┘     └────┬─────┘
     │           └─────┬─────┘           │                 │
     │                 │                 │                 │
     │           ┌─────▼─────────────────▼─────────────────▼───┐
     │           │              Show (Showtime)                 │
     │           ├──────────────────────────────────────────────┤
     │           │ show_id, event_id, venue_id, screen_id       │
     │           │ start_time, end_time, status                 │
     │           │ pricing: { silver: 150, gold: 250, ... }     │
     │           └──────────────────────┬───────────────────────┘
     │                                  │
     │                            ┌─────▼──────┐
     │                            │  ShowSeat   │
     │                            ├────────────┤
     │                            │ seat_id     │
     │                            │ show_id     │
     │                            │ row         │
     │                            │ number      │
     │                            │ type        │
     │                            │ status      │  AVAILABLE|HELD|BOOKED
     │                            │ price       │
     │                            │ held_by     │
     │                            │ held_until  │
     │                            │ version     │  (optimistic lock)
     │                            └──────┬──────┘
     │                                   │
     │           ┌───────────────────────▼────────────────────┐
     │           │                Booking                      │
     └──────────▸├─────────────────────────────────────────────┤
                 │ booking_id, user_id, show_id                 │
                 │ seats: [A1, A4, A5]                          │
                 │ total_amount, status                         │
                 │ payment_id, booked_at                        │
                 │ cancelled_at, refund_id                      │
                 └──────────────────────┬──────────────────────┘
                                        │
                                  ┌─────▼──────┐
                                  │  Payment   │
                                  ├────────────┤
                                  │ payment_id │
                                  │ booking_id │
                                  │ amount     │
                                  │ method     │
                                  │ status     │
                                  │ gateway_ref│
                                  │ idempotency│
                                  │ created_at │
                                  └────────────┘
```

### 6.2 Database Selection

```
┌─────────────────────────┬──────────────────┬──────────────────────────────┐
│        Data             │    Database       │         Rationale            │
├─────────────────────────┼──────────────────┼──────────────────────────────┤
│ Users, Events, Venues,  │ MySQL (InnoDB)    │ ACID, relational joins,      │
│ Shows, Bookings,        │                  │ mature tooling, strong       │
│ Payments                │                  │ consistency                  │
├─────────────────────────┼──────────────────┼──────────────────────────────┤
│ Seat inventory          │ Redis (primary)   │ O(1) lookups, atomic SET NX, │
│ (real-time holds)       │ + MySQL (durable) │ TTL-based auto-expiry,       │
│                         │                  │ sub-ms latency               │
├─────────────────────────┼──────────────────┼──────────────────────────────┤
│ Search index            │ Elasticsearch     │ Full-text search, faceted    │
│                         │                  │ filters, geo queries         │
├─────────────────────────┼──────────────────┼──────────────────────────────┤
│ Session / cart state    │ Redis             │ Fast reads, TTL expiry       │
├─────────────────────────┼──────────────────┼──────────────────────────────┤
│ Event images / assets   │ S3 + CDN          │ Blob storage, edge caching   │
├─────────────────────────┼──────────────────┼──────────────────────────────┤
│ Analytics / event logs  │ ClickHouse /      │ Column-oriented, aggregation │
│                         │ Apache Druid      │ queries                      │
└─────────────────────────┴──────────────────┴──────────────────────────────┘
```

### 6.3 Seat Status State Machine

```
                           User selects seats
                    ┌─────────────────────────────┐
                    │                             │
                    ▼                             │
             ┌────────────┐                       │
             │ AVAILABLE  │◂──────────────────────┤
             └─────┬──────┘                       │
                   │                              │
                   │ POST /bookings/hold           │
                   │ Redis SET NX + TTL            │
                   ▼                              │
             ┌────────────┐     TTL expires        │
             │   HELD     │───────────────────────┘
             └─────┬──────┘     (auto-release)
                   │
                   │ POST /bookings/confirm
                   │ Payment success
                   ▼
             ┌────────────┐
             │  BOOKED    │
             └─────┬──────┘
                   │
                   │ DELETE /bookings/{id}
                   │ Cancellation
                   ▼
             ┌────────────┐
             │ CANCELLED  │───▸ Seat returns to AVAILABLE
             └────────────┘
```

### 6.4 Key Table Schemas

```sql
-- Show Seats with optimistic locking
CREATE TABLE show_seats (
    id              BIGINT PRIMARY KEY AUTO_INCREMENT,
    show_id         VARCHAR(36) NOT NULL,
    seat_id         VARCHAR(10) NOT NULL,       -- e.g., "A1", "B12"
    row_label       CHAR(2) NOT NULL,
    seat_number     SMALLINT NOT NULL,
    seat_type       ENUM('silver','gold','platinum') NOT NULL,
    status          ENUM('available','held','booked','cancelled') DEFAULT 'available',
    price           DECIMAL(10,2) NOT NULL,
    held_by_user    VARCHAR(36),
    held_until      TIMESTAMP NULL,
    booked_by_user  VARCHAR(36),
    booking_id      VARCHAR(36),
    version         INT DEFAULT 0,              -- optimistic lock version
    
    UNIQUE INDEX idx_show_seat (show_id, seat_id),
    INDEX idx_show_status (show_id, status),
    INDEX idx_held_until (held_until)           -- for cleanup of expired holds
) ENGINE=InnoDB;

-- Bookings
CREATE TABLE bookings (
    booking_id      VARCHAR(36) PRIMARY KEY,
    user_id         VARCHAR(36) NOT NULL,
    show_id         VARCHAR(36) NOT NULL,
    seats           JSON NOT NULL,              -- ["A1", "A4", "A5"]
    seat_count      SMALLINT NOT NULL,
    total_amount    DECIMAL(10,2) NOT NULL,
    status          ENUM('pending','confirmed','cancelled','refunded') NOT NULL,
    hold_token      VARCHAR(64),
    payment_id      VARCHAR(36),
    booked_at       TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    cancelled_at    TIMESTAMP NULL,
    
    INDEX idx_user (user_id),
    INDEX idx_show (show_id),
    INDEX idx_status_time (status, booked_at)
) ENGINE=InnoDB;

-- Payments with idempotency
CREATE TABLE payments (
    payment_id      VARCHAR(36) PRIMARY KEY,
    booking_id      VARCHAR(36) NOT NULL,
    user_id         VARCHAR(36) NOT NULL,
    amount          DECIMAL(10,2) NOT NULL,
    currency        CHAR(3) DEFAULT 'INR',
    method          ENUM('upi','card','netbanking','wallet') NOT NULL,
    status          ENUM('initiated','processing','success','failed','refunded') NOT NULL,
    gateway_ref     VARCHAR(128),
    idempotency_key VARCHAR(64) UNIQUE NOT NULL,
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    INDEX idx_booking (booking_id),
    INDEX idx_idempotency (idempotency_key)
) ENGINE=InnoDB;
```

---

## 7. High-Level Architecture

### 7.1 System Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                              CLIENTS                                            │
│   ┌──────────┐  ┌──────────┐  ┌──────────┐                                     │
│   │  Mobile  │  │   Web    │  │  Partner │                                     │
│   │   App    │  │   App    │  │   API    │                                     │
│   └────┬─────┘  └────┬─────┘  └────┬─────┘                                     │
└────────┼─────────────┼─────────────┼────────────────────────────────────────────┘
         │             │             │
         ▼             ▼             ▼
┌─────────────────────────────────────────┐
│              CDN (CloudFront)           │    Static assets, event images,
│         Edge caching, SSL/TLS           │    seat map layouts
└────────────────────┬────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────┐
│          Global Load Balancer           │    Geographic routing,
│         (Route53 + ALB/NLB)             │    health checks
└────────────────────┬────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────┐
│            API Gateway                  │    Auth, rate limiting,
│     (Kong / AWS API Gateway)            │    request validation,
│                                         │    throttling
└──────┬──────┬──────┬──────┬─────┬───────┘
       │      │      │      │     │
       ▼      ▼      ▼      ▼     ▼
┌──────────────────────────────────────────────────────────────────────────────┐
│                         MICROSERVICES LAYER                                  │
│                                                                              │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌──────────────┐          │
│  │   Event     │ │  Booking    │ │  Payment    │ │ Notification │          │
│  │  Service    │ │  Service    │ │  Service    │ │   Service    │          │
│  │             │ │             │ │             │ │              │          │
│  │ - Catalog   │ │ - Seat hold │ │ - Charge    │ │ - Email/SMS  │          │
│  │ - Shows     │ │ - Confirm   │ │ - Refund    │ │ - Push       │          │
│  │ - Venue     │ │ - Cancel    │ │ - Idempotent│ │ - Templates  │          │
│  └──────┬──────┘ └──────┬──────┘ └──────┬──────┘ └──────┬───────┘          │
│         │               │               │               │                   │
│  ┌──────┴──────┐ ┌──────┴──────┐        │               │                   │
│  │   Search    │ │  Inventory  │        │               │                   │
│  │  Service    │ │  Service    │        │               │                   │
│  │             │ │             │        │               │                   │
│  │ - Full-text │ │ - Seat map  │        │               │                   │
│  │ - Geo query │ │ - Real-time │        │               │                   │
│  │ - Facets    │ │ - Flash sale│        │               │                   │
│  └──────┬──────┘ └──────┬──────┘        │               │                   │
│         │               │               │               │                   │
│  ┌──────┴──────┐ ┌──────┴──────┐        │               │                   │
│  │  Queue /    │ │  User       │        │               │                   │
│  │ WaitingRoom │ │  Service    │        │               │                   │
│  │  Service    │ │             │        │               │                   │
│  │             │ │ - Profile   │        │               │                   │
│  │ - Flash sale│ │ - Auth      │        │               │                   │
│  │ - Throttle  │ │ - History   │        │               │                   │
│  └─────────────┘ └─────────────┘        │               │                   │
│                                          │               │                   │
└──────────────────────────────────────────┼───────────────┼───────────────────┘
                                           │               │
┌──────────────────────────────────────────┼───────────────┼───────────────────┐
│                     DATA LAYER           │               │                   │
│                                          │               │                   │
│  ┌────────────┐  ┌────────────┐  ┌───────┴──────┐  ┌────┴──────┐           │
│  │   MySQL    │  │   Redis    │  │   Payment    │  │   Kafka   │           │
│  │  Cluster   │  │  Cluster   │  │   Gateway    │  │  Cluster  │           │
│  │            │  │            │  │  (Stripe/    │  │           │           │
│  │ - Events   │  │ - Seat     │  │   Razorpay)  │  │ - Events  │           │
│  │ - Bookings │  │   holds    │  │              │  │ - Booking │           │
│  │ - Payments │  │ - Cache    │  │              │  │   events  │           │
│  │ - Users    │  │ - Sessions │  │              │  │ - Notif   │           │
│  └────────────┘  └────────────┘  └──────────────┘  └───────────┘           │
│                                                                             │
│  ┌────────────────┐  ┌──────────────┐  ┌──────────────────┐                │
│  │ Elasticsearch  │  │     S3       │  │   ClickHouse     │                │
│  │                │  │              │  │                  │                │
│  │ - Event search │  │ - Images     │  │ - Analytics      │                │
│  │ - Geo queries  │  │ - E-tickets  │  │ - Booking trends │                │
│  └────────────────┘  └──────────────┘  └──────────────────┘                │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 7.2 Booking Flow -- Sequence Diagram

```
 Client          API GW        Booking Svc     Inventory Svc    Redis         MySQL       Payment Svc    Notification
   │                │               │               │             │              │              │              │
   │  Select Seats  │               │               │             │              │              │              │
   │───────────────▸│               │               │             │              │              │              │
   │                │  POST /hold   │               │             │              │              │              │
   │                │──────────────▸│               │             │              │              │              │
   │                │               │  Lock seats   │             │              │              │              │
   │                │               │──────────────▸│             │              │              │              │
   │                │               │               │  SET NX     │              │              │              │
   │                │               │               │  + TTL 480s │              │              │              │
   │                │               │               │────────────▸│              │              │              │
   │                │               │               │             │              │              │              │
   │                │               │               │  OK / FAIL  │              │              │              │
   │                │               │               │◂────────────│              │              │              │
   │                │               │  Hold result  │             │              │              │              │
   │                │               │◂──────────────│             │              │              │              │
   │                │  hold_token   │               │             │              │              │              │
   │                │◂──────────────│               │             │              │              │              │
   │  hold_token    │               │               │             │              │              │              │
   │◂───────────────│               │               │             │              │              │              │
   │                │               │               │             │              │              │              │
   │  Confirm + Pay │               │               │             │              │              │              │
   │───────────────▸│               │               │             │              │              │              │
   │                │ POST /confirm │               │             │              │              │              │
   │                │──────────────▸│               │             │              │              │              │
   │                │               │  Validate hold│             │              │              │              │
   │                │               │──────────────▸│             │              │              │              │
   │                │               │               │  GET hold   │              │              │              │
   │                │               │               │────────────▸│              │              │              │
   │                │               │               │  hold valid │              │              │              │
   │                │               │               │◂────────────│              │              │              │
   │                │               │               │             │              │              │              │
   │                │               │  Process payment             │              │              │              │
   │                │               │─────────────────────────────────────────────────────────▸│              │
   │                │               │               │             │              │   Charge     │              │
   │                │               │               │             │              │   Customer   │              │
   │                │               │  Payment OK   │             │              │              │              │
   │                │               │◂─────────────────────────────────────────────────────────│              │
   │                │               │               │             │              │              │              │
   │                │               │  Persist booking             │              │              │              │
   │                │               │────────────────────────────────────────────▸│              │              │
   │                │               │               │  Mark BOOKED│              │              │              │
   │                │               │               │────────────▸│  UPDATE seats│              │              │
   │                │               │               │             │─────────────▸│              │              │
   │                │               │               │             │              │              │              │
   │                │               │  Send notification (async via Kafka)        │              │              │
   │                │               │──────────────────────────────────────────────────────────────────────────▸│
   │                │               │               │             │              │              │              │
   │                │  Booking confirmed             │             │              │              │              │
   │                │◂──────────────│               │             │              │              │              │
   │  Confirmation  │               │               │             │              │              │              │
   │◂───────────────│               │               │             │              │              │              │
   │                │               │               │             │              │              │              │
```

### 7.3 Component Breakdown

| Component            | Responsibility                                       | Scaling Model             |
|----------------------|------------------------------------------------------|---------------------------|
| **API Gateway**      | Auth, rate limiting, request routing, SSL termination | Horizontal, stateless     |
| **Event Service**    | CRUD for events, venues, shows; schedule management  | Horizontal, read replicas |
| **Booking Service**  | Orchestrate hold → confirm → cancel flows            | Horizontal, stateless     |
| **Inventory Service**| Seat availability, holds, real-time updates          | Horizontal, Redis-backed  |
| **Payment Service**  | Gateway integration, idempotent charges, refunds     | Horizontal, stateless     |
| **Search Service**   | Full-text search, geo queries, facets, autocomplete  | Elasticsearch cluster     |
| **Notification Svc** | Email, SMS, push via Kafka consumers                 | Horizontal, async         |
| **User Service**     | Profile, auth, booking history                       | Horizontal, read replicas |
| **Queue/WaitRoom**   | Flash sale traffic management, fair ordering         | Horizontal, Redis-backed  |

---

## 8. Deep Dive: Core Components

### 8.1 Seat Inventory and Locking

This is the **single most critical component** of the system. Every seat must have exactly one
owner -- zero double bookings, even under extreme concurrency.

#### Locking Strategy Comparison

```
┌─────────────────────────┬────────────────────────────────────────────────────┐
│      Strategy           │              Details                              │
├─────────────────────────┼────────────────────────────────────────────────────┤
│                         │                                                    │
│  Pessimistic Locking    │  SELECT ... FOR UPDATE on seat rows               │
│  (DB-level row locks)   │                                                    │
│                         │  Pros: Simple, strong guarantees                   │
│                         │  Cons: Blocks concurrent readers, lock contention  │
│                         │        at scale, DB becomes bottleneck             │
│                         │  Use: Low-traffic events                           │
│                         │                                                    │
├─────────────────────────┼────────────────────────────────────────────────────┤
│                         │                                                    │
│  Optimistic Locking     │  UPDATE ... WHERE version = X; check affected rows │
│  (Version-based)        │                                                    │
│                         │  Pros: No blocking, better throughput              │
│                         │  Cons: Retry storms under high contention          │
│                         │  Use: Medium-traffic events                        │
│                         │                                                    │
├─────────────────────────┼────────────────────────────────────────────────────┤
│                         │                                                    │
│  Distributed Lock       │  Redis SET NX with TTL                             │
│  (Redis-based)          │                                                    │
│                         │  Pros: Sub-ms latency, automatic TTL expiry,       │
│                         │        no DB load for holds, horizontally scalable │
│                         │  Cons: Redis failure risks, need dual-write to DB  │
│                         │  Use: Flash sales, high-traffic events   ◂── BEST │
│                         │                                                    │
└─────────────────────────┴────────────────────────────────────────────────────┘
```

#### Redis-Based Seat Hold Implementation

```
Key Pattern:    seat_hold:{show_id}:{seat_id}
Value:          { "user_id": "usr_456", "hold_token": "hld_abc", "held_at": "..." }
TTL:            480 seconds (8 minutes)

-- Hold a seat (atomic operation)
SET seat_hold:shw_xyz789:A1 '{"user_id":"usr_456","hold_token":"hld_abc"}' NX EX 480

-- Result: "OK"    → seat successfully held
-- Result: (nil)   → seat already held by another user, return 409

-- Release a seat (on timeout or cancellation)
DEL seat_hold:shw_xyz789:A1

-- Check seat availability for entire show (pipeline)
MGET seat_hold:shw_xyz789:A1 seat_hold:shw_xyz789:A2 ... seat_hold:shw_xyz789:A250
-- Returns: [nil, nil, "...", nil, "...", ...]
-- nil = available, non-nil = held/booked
```

#### Multi-Seat Atomic Hold (Lua Script)

When a user selects multiple seats, all must be held atomically -- either all succeed or none:

```lua
-- Redis Lua script for atomic multi-seat hold
-- KEYS: seat keys to hold
-- ARGV[1]: hold value (JSON), ARGV[2]: TTL in seconds

local held = {}
for i, key in ipairs(KEYS) do
    local result = redis.call('SET', key, ARGV[1], 'NX', 'EX', tonumber(ARGV[2]))
    if result then
        table.insert(held, key)
    else
        -- Rollback: release all seats held in this batch
        for _, held_key in ipairs(held) do
            redis.call('DEL', held_key)
        end
        -- Return the conflicting seat
        return { 'CONFLICT', key }
    end
end
return { 'OK', unpack(held) }
```

#### Seat State Machine (Detailed)

```
                    ┌──────────────────────────────────────────────────────┐
                    │              SEAT STATE TRANSITIONS                   │
                    └──────────────────────────────────────────────────────┘

     ┌───────────────────────────────────────────────────────────────────┐
     │                                                                   │
     │   ┌─────────────┐                                                 │
     │   │  AVAILABLE  │◂─────────────────────────────┐                  │
     │   │             │◂──────────────────┐          │                  │
     │   └──────┬──────┘                   │          │                  │
     │          │                          │          │                  │
     │          │ User calls               │          │                  │
     │          │ POST /hold               │          │                  │
     │          │                          │          │                  │
     │          │ Redis: SET NX EX 480     │          │                  │
     │          │                          │          │                  │
     │          ▼                          │          │                  │
     │   ┌─────────────┐          TTL expires    Cancellation            │
     │   │    HELD     │──────────────────┘   (refund processed)        │
     │   │             │                          │                      │
     │   │ TTL: 8 min  │                          │                      │
     │   └──────┬──────┘                          │                      │
     │          │                                 │                      │
     │          │ Payment succeeds                │                      │
     │          │ POST /confirm                   │                      │
     │          │                                 │                      │
     │          │ Redis: persist to MySQL          │                      │
     │          │ MySQL: UPDATE status='booked'    │                      │
     │          │                                 │                      │
     │          ▼                                 │                      │
     │   ┌─────────────┐                          │                      │
     │   │   BOOKED    │──────────────────────────┘                      │
     │   │             │                                                 │
     │   │ Permanent   │     Payment fails                               │
     │   └──────┬──────┘──────────────────────────────────── AVAILABLE   │
     │          │                                                        │
     │          │ Explicit cancellation                                   │
     │          │ DELETE /bookings/{id}                                   │
     │          ▼                                                        │
     │   ┌─────────────┐                                                 │
     │   │  CANCELLED  │────────────────────────────────────────────────┘
     │   │             │  Seat released back to pool
     │   └─────────────┘
     │
     └───────────────────────────────────────────────────────────────────┘

     Transition Guards:
     ─────────────────
     AVAILABLE → HELD:    Only if Redis SET NX succeeds (atomic)
     HELD → BOOKED:       Only if hold_token matches AND not expired
     HELD → AVAILABLE:    Automatic via Redis TTL expiry
     BOOKED → CANCELLED:  Only by hold owner OR admin
     BOOKED → AVAILABLE:  Via cancellation + refund flow
```

#### Race Condition Handling

**Scenario:** 1000 users click seat "A1" at the exact same instant.

```
User 1 ──▸ Redis SET seat_hold:shw_x:A1 NX EX 480 ──▸ "OK"    ← WINS
User 2 ──▸ Redis SET seat_hold:shw_x:A1 NX EX 480 ──▸ (nil)   ← 409 Conflict
User 3 ──▸ Redis SET seat_hold:shw_x:A1 NX EX 480 ──▸ (nil)   ← 409 Conflict
  ...
User 1000──▸ Redis SET seat_hold:shw_x:A1 NX EX 480──▸ (nil)  ← 409 Conflict
```

Redis SET NX is **single-threaded and atomic** -- only one writer wins. There is no race condition
possible at the Redis level. The losing users receive an immediate 409 and can select alternative
seats.

#### Dual-Write Consistency (Redis + MySQL)

```
┌─────────────────────────────────────────────────────────────────────┐
│                  DUAL-WRITE STRATEGY                                │
│                                                                     │
│  Phase 1: HOLD (Redis is source of truth)                          │
│  ─────────────────────────────────────────                          │
│  1. SET NX in Redis (atomic, with TTL)                              │
│  2. Async: write hold record to MySQL (for audit)                   │
│  3. If Redis fails: no hold, no MySQL write                         │
│  4. If MySQL async fails: hold still valid in Redis, retry later    │
│                                                                     │
│  Phase 2: CONFIRM (MySQL becomes source of truth)                  │
│  ─────────────────────────────────────────                          │
│  1. Validate hold in Redis (still active?)                          │
│  2. Process payment                                                 │
│  3. BEGIN TRANSACTION in MySQL:                                     │
│     - UPDATE show_seats SET status='booked' WHERE show_id=? AND     │
│       seat_id IN (?) AND status='held'                              │
│     - INSERT INTO bookings (...)                                    │
│     - INSERT INTO payments (...)                                    │
│  4. COMMIT                                                          │
│  5. Update Redis: remove hold key, set permanent booked flag        │
│  6. If MySQL COMMIT fails: release Redis hold, refund payment       │
│                                                                     │
│  Invariant: After confirmation, MySQL is the permanent record.      │
│  Redis can be rebuilt from MySQL state on cold start.               │
└─────────────────────────────────────────────────────────────────────┘
```

---

### 8.2 Flash Sale / High-Demand Event Handling

Flash sales represent the hardest scaling challenge: 500K users competing for 50K seats in seconds.
Naive first-come-first-served would overwhelm the system.

#### Virtual Waiting Room Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    VIRTUAL WAITING ROOM FLOW                                │
│                                                                             │
│                                                                             │
│  500K Users                                                                 │
│     │                                                                       │
│     ▼                                                                       │
│  ┌──────────────────────────┐                                               │
│  │    CloudFront Edge       │  Static waiting room page                     │
│  │    (Waiting Room UI)     │  served from CDN -- zero                      │
│  │                          │  backend load                                 │
│  │  "You are #142,857       │                                               │
│  │   in line. Estimated     │                                               │
│  │   wait: 4 minutes"       │                                               │
│  └────────────┬─────────────┘                                               │
│               │                                                             │
│               │  Polls every 5 seconds:                                     │
│               │  GET /v1/queue/status?ticket=<queue_ticket>                 │
│               │                                                             │
│               ▼                                                             │
│  ┌──────────────────────────┐     ┌───────────────────────────────┐         │
│  │    Queue Service         │     │     Redis Sorted Set          │         │
│  │                          │────▸│                               │         │
│  │  - Assigns queue ticket  │     │  Key: flash_queue:{event_id}  │         │
│  │  - Tracks position       │     │  Score: timestamp (arrival)   │         │
│  │  - Token bucket release  │     │  Member: user_id              │         │
│  │                          │     │                               │         │
│  └────────────┬─────────────┘     └───────────────────────────────┘         │
│               │                                                             │
│               │  Rate-limited admission:                                    │
│               │  5,000 users/second → booking page                          │
│               │                                                             │
│               ▼                                                             │
│  ┌──────────────────────────┐                                               │
│  │   Booking Flow           │  User has 8-minute window                     │
│  │   (Seat Selection +      │  to complete booking                          │
│  │    Payment)              │                                               │
│  └──────────────────────────┘                                               │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

#### Token Bucket for Controlled Admission

```
┌─────────────────────────────────────────────────────────────────┐
│                TOKEN BUCKET ADMISSION CONTROL                    │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Configuration for a 50K-seat event:                            │
│  ────────────────────────────────────                            │
│  Bucket capacity:           5,000 tokens                        │
│  Refill rate:               5,000 tokens/second                 │
│  Expected fill time:        50K / 5K = 10 seconds               │
│  Buffer for drop-offs:      2x admission = 100K users admitted  │
│                                                                  │
│  Timeline:                                                       │
│  ──────────                                                      │
│  T+0s:    Sale opens. 500K users land on waiting room page.     │
│  T+0-1s:  First 5,000 users admitted to booking page.           │
│  T+1-2s:  Next 5,000 admitted. First batch selecting seats.     │
│  T+10s:   50,000 users admitted. ~30K seats likely held.        │
│  T+20s:   100K total admitted. Most seats held or booked.       │
│  T+30s:   Remaining queue users see "event likely sold out."    │
│  T+8min:  Expired holds release. Waitlisted users notified.    │
│                                                                  │
│  Benefits:                                                       │
│  ─────────                                                       │
│  - Backend never sees more than ~5K concurrent booking requests │
│  - Predictable load regardless of demand                        │
│  - Fair ordering (FIFO by arrival time)                          │
│  - Graceful degradation (waiting room is static CDN page)       │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

#### Pre-Generated Booking Tokens

For ultra-high-demand events, pre-generate a limited number of booking tokens:

```
Before sale opens (T-10 minutes):
─────────────────────────────────
1. Generate exactly 60,000 booking tokens (for 50K seats + 20% buffer)
2. Store in Redis list: LPUSH flash_tokens:{event_id} token_1 token_2 ... token_60000

During sale:
────────────
1. Queue service admits user → RPOP flash_tokens:{event_id}
2. If token received → proceed to seat selection
3. If (nil) → all tokens distributed, show "sold out" immediately

Advantage: Hard cap on concurrent booking flow users. Once tokens exhausted,
           the system immediately stops admitting new users.
```

#### Overselling Prevention

```
┌─────────────────────────────────────────────────────────────────┐
│              OVERSELLING PREVENTION LAYERS                       │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Layer 1: Redis SET NX                                          │
│  ─────────────────────                                          │
│  Each seat can only have one holder. Atomic guarantee.          │
│                                                                  │
│  Layer 2: Token budget                                          │
│  ────────────────────                                           │
│  Pre-generated tokens limit total concurrent booking attempts   │
│  to (seats + buffer).                                           │
│                                                                  │
│  Layer 3: MySQL optimistic lock on confirm                      │
│  ──────────────────────────────────────────                     │
│  UPDATE show_seats SET status='booked', version=version+1       │
│  WHERE seat_id=? AND status='held' AND version=?                │
│  If affected_rows=0 → seat was already booked, reject.          │
│                                                                  │
│  Layer 4: Total booked count check                              │
│  ─────────────────────────────────                              │
│  Before confirming, verify: COUNT(booked) < total_capacity      │
│  Acts as a circuit breaker against any edge cases.              │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

#### Circuit Breaker for Payment Failures

```
                    ┌─────────────────────┐
                    │   Payment Gateway   │
                    └─────────┬───────────┘
                              │
                  ┌───────────┴───────────┐
                  │                       │
            Success (< 200ms)       Failure / Timeout
                  │                       │
                  ▼                       ▼
          Confirm booking        ┌─────────────────┐
                                 │ Circuit Breaker  │
                                 ├─────────────────┤
                                 │ CLOSED (normal): │
                                 │  Pass requests   │
                                 │  through          │
                                 │                  │
                                 │ OPEN (>50% fail  │
                                 │  in 30s window): │
                                 │  Reject immediately│
                                 │  "Payment service │
                                 │   temporarily     │
                                 │   unavailable"   │
                                 │  Hold preserved   │
                                 │                  │
                                 │ HALF-OPEN:        │
                                 │  Allow 10% of     │
                                 │  requests to probe│
                                 └─────────────────┘
```

---

### 8.3 Payment Integration

#### Two-Phase Booking Protocol

```
┌─────────────────────────────────────────────────────────────────────────┐
│                TWO-PHASE BOOKING PROTOCOL                               │
│                                                                         │
│  Phase 1: RESERVE (Optimistic)                                         │
│  ──────────────────────────────                                        │
│                                                                         │
│  ┌──────────┐        ┌──────────┐        ┌──────────┐                  │
│  │  Client  │──hold─▸│ Booking  │──lock──▸│  Redis   │                  │
│  │          │◂─token─│ Service  │◂──ok────│          │                  │
│  └──────────┘        └──────────┘        └──────────┘                  │
│                                                                         │
│  - Seats locked in Redis with 8-min TTL                                │
│  - No payment processed yet                                            │
│  - User sees "seats held for 8 minutes" countdown                      │
│                                                                         │
│                                                                         │
│  Phase 2: COMMIT (Confirm with Payment)                                │
│  ──────────────────────────────────────                                 │
│                                                                         │
│  ┌──────────┐       ┌──────────┐       ┌──────────┐       ┌──────────┐│
│  │  Client  │─pay──▸│ Booking  │─charg─▸│ Payment  │─call─▸│ Gateway  ││
│  │          │       │ Service  │       │ Service  │       │(Razorpay)││
│  │          │       │          │◂──ok──│          │◂──ok──│          ││
│  │          │       │          │       └──────────┘       └──────────┘│
│  │          │       │          │                                       │
│  │          │       │          │──────────▸ MySQL: BEGIN               │
│  │          │       │          │            INSERT booking             │
│  │          │       │          │            UPDATE seats → booked      │
│  │          │       │          │            INSERT payment             │
│  │          │       │          │            COMMIT                     │
│  │          │       │          │                                       │
│  │          │       │          │──────────▸ Kafka: booking.confirmed   │
│  │          │◂─ok───│          │                                       │
│  └──────────┘       └──────────┘                                      │
│                                                                         │
│                                                                         │
│  Failure Scenarios:                                                     │
│  ─────────────────                                                     │
│  Payment timeout → Retry up to 3 times with exponential backoff        │
│  Payment failure → Release holds in Redis, return error to user        │
│  MySQL commit fail → Initiate payment refund, release holds            │
│  Client disconnects → Hold auto-expires via Redis TTL                  │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

#### Payment Timeout Handling

```
┌───────────────────────────────────────────────────────────────────────┐
│                   PAYMENT TIMEOUT STRATEGY                            │
│                                                                       │
│  Timeline for a single booking attempt:                              │
│                                                                       │
│  T+0:00   Seats held (8-min TTL starts)                              │
│  T+0:05   User enters payment details                                │
│  T+0:15   Payment initiated → Gateway                                │
│  T+0:15   ...waiting for gateway response...                         │
│                                                                       │
│  Scenario A: Gateway responds in 3s                                  │
│  T+0:18   Payment SUCCESS → Confirm booking                         │
│                                                                       │
│  Scenario B: Gateway timeout at 30s                                  │
│  T+0:45   Timeout → Check payment status via GET /payments/{id}     │
│  T+0:46   Status: "processing" → Wait + retry check                 │
│  T+1:00   Status: "success" → Confirm booking                       │
│           Status: "failed" → Release seats, show error               │
│           Status: "unknown" → Hold payment, retry in 30s             │
│                                                                       │
│  Scenario C: Repeated failures                                       │
│  T+2:00   3 attempts exhausted → Release seats                      │
│  T+2:01   Show user: "Payment failed. Seats released.               │
│            Please try again."                                        │
│                                                                       │
│  Scenario D: User abandons (closes app)                              │
│  T+8:00   Redis TTL expires → Seats auto-released                   │
│  T+8:01   If payment was initiated:                                  │
│            → Async reconciliation job checks gateway                 │
│            → If payment succeeded: auto-confirm booking              │
│            → If payment failed/absent: no action needed              │
│                                                                       │
└───────────────────────────────────────────────────────────────────────┘
```

#### Idempotent Payment Requests

```
POST /v1/payments/charge
Headers:
    Idempotency-Key: idem_a1b2c3d4e5f6    ← Client generates once per booking attempt

Server logic:
─────────────
1. Check: SELECT * FROM payments WHERE idempotency_key = 'idem_a1b2c3d4e5f6'
2. If found AND status = 'success': return cached response (no re-charge)
3. If found AND status = 'processing': return 202 (still processing)
4. If found AND status = 'failed': allow retry with NEW idempotency key
5. If not found: process payment, store with idempotency_key

Why:
────
- Network retries may duplicate payment requests
- User may click "Pay" multiple times
- Gateway timeout doesn't mean payment failed
- Without idempotency: user charged 2x or 3x (catastrophic)
```

#### Refund Processing

```
┌─────────────────────────────────────────────────────────────────┐
│                   REFUND FLOW                                    │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  User cancels booking                                           │
│       │                                                          │
│       ▼                                                          │
│  ┌─────────────────────────────────┐                            │
│  │  Calculate refund amount         │                            │
│  │  based on cancellation policy:   │                            │
│  │                                  │                            │
│  │  > 24h before show: 90% refund  │                            │
│  │  4-24h before show: 50% refund  │                            │
│  │  < 4h before show:  No refund   │                            │
│  └──────────────┬──────────────────┘                            │
│                 │                                                │
│                 ▼                                                │
│  ┌─────────────────────────────────┐                            │
│  │  MySQL Transaction:              │                            │
│  │  1. UPDATE booking status=cancel │                            │
│  │  2. UPDATE seats status=available│                            │
│  │  3. INSERT refund record         │                            │
│  │  4. COMMIT                       │                            │
│  └──────────────┬──────────────────┘                            │
│                 │                                                │
│                 ▼                                                │
│  ┌─────────────────────────────────┐                            │
│  │  Publish: booking.cancelled      │──▸ Kafka                  │
│  │  → Payment Service: refund       │                            │
│  │  → Notification: cancellation    │                            │
│  │  → Inventory: seat released      │                            │
│  └─────────────────────────────────┘                            │
│                                                                  │
│  Refund is ASYNC: processed within 5-7 business days            │
│  User receives notification when refund is credited             │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

### 8.4 Search and Discovery

#### Search Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    SEARCH ARCHITECTURE                                   │
│                                                                          │
│  ┌──────────┐     ┌──────────────┐     ┌────────────────────────────┐  │
│  │  Event   │────▸│  Change Data │────▸│     Elasticsearch          │  │
│  │ Service  │     │  Capture     │     │                            │  │
│  │ (MySQL)  │     │  (Debezium)  │     │  Index: events             │  │
│  │          │     │              │     │  ├── title (text, analyzed) │  │
│  │          │     │  Kafka topic:│     │  ├── genre (keyword)        │  │
│  │          │     │  db.events   │     │  ├── language (keyword)     │  │
│  └──────────┘     └──────────────┘     │  ├── city (keyword)        │  │
│                                        │  ├── location (geo_point)  │  │
│                                        │  ├── date (date)           │  │
│                                        │  ├── rating (float)        │  │
│                                        │  ├── price_min (integer)   │  │
│                                        │  ├── category (keyword)    │  │
│                                        │  └── available_shows (int) │  │
│                                        │                            │  │
│                                        │  Refresh: Near real-time   │  │
│                                        │  (~2 second lag via CDC)   │  │
│                                        └────────────────────────────┘  │
│                                                                          │
│                                                                          │
│  Search Features:                                                       │
│  ────────────────                                                       │
│  1. Full-text: "avengers" → fuzzy match on title, description           │
│  2. Faceted: genre count, language count, price distribution             │
│  3. Geo: events within 10km of user's location                          │
│  4. Autocomplete: prefix-based suggestions as user types                │
│  5. Recommendations: based on user history + collaborative filtering    │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

#### Geospatial Query for Nearby Theaters

```json
{
  "query": {
    "bool": {
      "must": [
        { "match": { "title": "avengers" } },
        { "term": { "city": "mumbai" } }
      ],
      "filter": [
        {
          "geo_distance": {
            "distance": "10km",
            "location": { "lat": 19.076, "lon": 72.877 }
          }
        },
        {
          "range": {
            "date": { "gte": "2026-04-15", "lte": "2026-04-22" }
          }
        }
      ]
    }
  },
  "sort": [
    { "_score": "desc" },
    {
      "_geo_distance": {
        "location": { "lat": 19.076, "lon": 72.877 },
        "order": "asc"
      }
    }
  ],
  "aggs": {
    "genres": { "terms": { "field": "genre" } },
    "price_ranges": {
      "range": {
        "field": "price_min",
        "ranges": [
          { "to": 200 },
          { "from": 200, "to": 500 },
          { "from": 500 }
        ]
      }
    }
  }
}
```

#### Recommendation Engine

```
┌─────────────────────────────────────────────────────────────────┐
│                  RECOMMENDATION APPROACH                         │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Input signals:                                                 │
│  ─────────────                                                  │
│  - Booking history (genres, languages, price range)             │
│  - Browse history (events viewed but not booked)                │
│  - Location (city, preferred theaters)                          │
│  - Time preferences (weekday vs weekend, afternoon vs evening)  │
│  - Similar users' behavior (collaborative filtering)            │
│                                                                  │
│  Implementation:                                                │
│  ───────────────                                                │
│  Phase 1: Rule-based (trending in city + genre affinity)        │
│  Phase 2: Collaborative filtering (users who booked X also Y)  │
│  Phase 3: ML model (embeddings, real-time re-ranking)           │
│                                                                  │
│  Served via:                                                    │
│  ──────────                                                     │
│  Pre-computed recommendations stored in Redis                   │
│  Updated every 6 hours by batch pipeline                        │
│  Real-time re-ranked based on current availability              │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## 9. Data Partitioning and Sharding

### Sharding Strategy

```
┌──────────────────────────────────────────────────────────────────────────┐
│                       SHARDING STRATEGY                                  │
├──────────────────┬───────────────┬────────────────────────────────────────┤
│    Entity        │  Shard Key    │  Rationale                            │
├──────────────────┼───────────────┼────────────────────────────────────────┤
│ Events / Shows   │ city_id       │ Queries are almost always city-scoped │
│                  │               │ Keeps related data co-located         │
│                  │               │ ~50 shards for major cities           │
├──────────────────┼───────────────┼────────────────────────────────────────┤
│ Bookings         │ user_id       │ User queries own booking history      │
│                  │ (hash-based)  │ Even distribution across shards       │
│                  │               │ 16 shards with consistent hashing     │
├──────────────────┼───────────────┼────────────────────────────────────────┤
│ Seat inventory   │ show_id       │ All seats for a show on same shard    │
│ (MySQL)          │               │ Enables single-shard transactions     │
│                  │               │ Important for atomicity               │
├──────────────────┼───────────────┼────────────────────────────────────────┤
│ Payments         │ booking_id    │ Co-located with booking data          │
│                  │               │ Enables join without cross-shard      │
├──────────────────┼───────────────┼────────────────────────────────────────┤
│ Redis seat holds │ show_id       │ All holds for a show on same Redis    │
│                  │ (hash tag)    │ node; enables Lua script atomicity    │
│                  │               │ Key: {shw_xyz}:A1 (hash tag routing)  │
└──────────────────┴───────────────┴────────────────────────────────────────┘
```

### Hot Partition Mitigation for Popular Events

```
Problem:
────────
A BTS concert (show_id: shw_bts_001) has 50K seats. During flash sale,
ALL requests hit the SAME Redis shard (because all keys share show_id).

Solutions:
──────────

1. Dedicated Redis instance for flash sale events
   ┌──────────────────────────────────────────────────────────┐
   │  Normal events  → Redis Cluster (shared, 6 nodes)       │
   │  Flash events   → Dedicated Redis (single node, 128GB)  │
   │                   Provisioned 1 hour before sale         │
   └──────────────────────────────────────────────────────────┘

2. Seat-range partitioning within the event
   ┌──────────────────────────────────────────────────────────┐
   │  Seats A1-F20   → Redis shard 1  (Section: Front)       │
   │  Seats G1-L20   → Redis shard 2  (Section: Middle)      │
   │  Seats M1-R20   → Redis shard 3  (Section: Back)        │
   │                                                          │
   │  Key pattern: {shw_bts_001:front}:A1                     │
   │  Different hash tags → different shards                  │
   └──────────────────────────────────────────────────────────┘

3. Pre-partitioned queue with per-section admission
   ┌──────────────────────────────────────────────────────────┐
   │  User selects preferred section BEFORE entering queue    │
   │  Each section has independent queue + inventory          │
   │  Reduces per-shard contention by 3-5x                   │
   └──────────────────────────────────────────────────────────┘
```

---

## 10. Caching Strategy

### Multi-Layer Cache Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                      CACHING LAYERS                                         │
│                                                                             │
│  Layer 1: CDN (CloudFront)                                                 │
│  ─────────────────────────                                                 │
│  ┌──────────────────────────────────────────────────────────┐              │
│  │  Event listings page (city-level)        TTL: 5 min      │              │
│  │  Event detail page (static metadata)     TTL: 15 min     │              │
│  │  Venue/theater info                      TTL: 1 hour     │              │
│  │  Images, posters, banners                TTL: 24 hours   │              │
│  │  Seat map layout (structure, not status) TTL: 1 hour     │              │
│  └──────────────────────────────────────────────────────────┘              │
│                                                                             │
│  Layer 2: Redis (Application Cache)                                        │
│  ──────────────────────────────────                                        │
│  ┌──────────────────────────────────────────────────────────┐              │
│  │  Seat availability (per show)            TTL: 5 sec      │              │
│  │  → During flash sale:                    TTL: 1 sec      │              │
│  │  Show listings (per city + date)         TTL: 2 min      │              │
│  │  User session / cart state               TTL: 30 min     │              │
│  │  Rate limiting counters                  TTL: 1 min      │              │
│  │  Pre-computed recommendations            TTL: 6 hours    │              │
│  └──────────────────────────────────────────────────────────┘              │
│                                                                             │
│  Layer 3: Local/In-Process Cache (Caffeine / Guava)                        │
│  ──────────────────────────────────────────────────                         │
│  ┌──────────────────────────────────────────────────────────┐              │
│  │  Venue metadata (rarely changes)         TTL: 10 min     │              │
│  │  Pricing rules                           TTL: 5 min      │              │
│  │  Feature flags                           TTL: 1 min      │              │
│  └──────────────────────────────────────────────────────────┘              │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Cache Invalidation Strategy

```
┌────────────────────────────────────────────────────────────────────────┐
│                  CACHE INVALIDATION                                    │
├────────────────────────────────────────────────────────────────────────┤
│                                                                        │
│  Seat Availability (most critical):                                   │
│  ──────────────────────────────────                                   │
│  - NOT cached in traditional sense; Redis IS the source of truth      │
│  - Seat map API reads directly from Redis                             │
│  - No stale data risk (queries are always live)                       │
│  - For UI display: client-side polling every 5s (normal),             │
│    every 1s (flash sale) via WebSocket/SSE                            │
│                                                                        │
│  Event Metadata (moderate staleness OK):                              │
│  ────────────────────────────────────────                              │
│  - Write-through: update MySQL → invalidate Redis → invalidate CDN   │
│  - Event: Kafka topic "event.updated" → cache invalidation consumer  │
│  - Max staleness: 5 seconds (Redis) + 5 minutes (CDN)                │
│                                                                        │
│  Search Index:                                                        │
│  ─────────────                                                        │
│  - CDC (Debezium) captures MySQL changes → Kafka → ES consumer       │
│  - Near-real-time: ~2 second lag                                      │
│  - Bulk re-index weekly for consistency verification                  │
│                                                                        │
└────────────────────────────────────────────────────────────────────────┘
```

---

## 11. Replication and Consistency

### Replication Topology

```
┌─────────────────────────────────────────────────────────────────────────┐
│                   REPLICATION TOPOLOGY                                   │
│                                                                          │
│  MySQL (Bookings, Payments, Seat Inventory):                            │
│  ──────────────────────────────────────────                             │
│  ┌────────────┐     sync repl     ┌────────────┐                       │
│  │   Primary  │──────────────────▸│  Standby   │  (failover target)    │
│  │  (Region 1)│                   │ (Region 1) │                       │
│  └──────┬─────┘                   └────────────┘                       │
│         │                                                               │
│         │ async repl                                                    │
│         ▼                                                               │
│  ┌────────────┐                                                         │
│  │  Read      │  Event browsing, booking history queries                │
│  │  Replica 1 │  (acceptable ~100ms lag for reads)                     │
│  └────────────┘                                                         │
│  ┌────────────┐                                                         │
│  │  Read      │  Analytics, reporting queries                           │
│  │  Replica 2 │  (isolated from production traffic)                    │
│  └────────────┘                                                         │
│                                                                          │
│                                                                          │
│  Redis (Seat Holds, Sessions):                                          │
│  ─────────────────────────────                                          │
│  ┌────────────┐     replication    ┌────────────┐                       │
│  │   Primary  │──────────────────▸│  Replica   │  (read scaling)       │
│  │  (writes)  │                   │ (reads)    │                       │
│  └────────────┘                   └────────────┘                       │
│                                                                          │
│  IMPORTANT: Seat hold writes MUST go to primary.                        │
│  Reads for seat map display can use replica (1-2ms lag acceptable).     │
│                                                                          │
│                                                                          │
│  Elasticsearch:                                                          │
│  ──────────────                                                         │
│  3-node cluster with 1 primary + 2 replica shards per index            │
│  All nodes can serve read queries                                       │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

### Consistency Guarantees by Operation

```
┌─────────────────────────────┬────────────────┬────────────────────────────┐
│     Operation               │  Consistency   │  Implementation            │
├─────────────────────────────┼────────────────┼────────────────────────────┤
│ Seat hold (SET NX)          │ Linearizable   │ Redis single-thread        │
│ Booking confirmation        │ Serializable   │ MySQL transaction          │
│ Payment processing          │ Serializable   │ Idempotency key + txn     │
│ Seat map display            │ Read-your-write│ Read from Redis primary    │
│ Event browsing              │ Eventual        │ Read replicas + cache     │
│ Booking history             │ Read-your-write│ Route to primary after     │
│                             │                │ write, replicas otherwise  │
│ Search results              │ Eventual (~2s) │ CDC pipeline lag           │
│ Reviews                     │ Eventual (~5s) │ Async write + cache       │
└─────────────────────────────┴────────────────┴────────────────────────────┘
```

---

## 12. Fault Tolerance and Failure Handling

### Failure Modes and Recovery

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    FAILURE MODE ANALYSIS                                     │
├─────────────────────────┬───────────────────────────────────────────────────┤
│  Failure                │  Impact and Recovery                              │
├─────────────────────────┼───────────────────────────────────────────────────┤
│                         │                                                   │
│  Redis primary down     │  Impact: Cannot hold seats (booking halted)       │
│                         │  Recovery:                                        │
│                         │  - Redis Sentinel promotes replica to primary     │
│                         │    (< 30 seconds failover)                        │
│                         │  - During failover: return 503 for hold requests  │
│                         │  - Existing holds preserved if replica has them   │
│                         │  - Rebuild holds from MySQL if data loss          │
│                         │                                                   │
├─────────────────────────┼───────────────────────────────────────────────────┤
│                         │                                                   │
│  MySQL primary down     │  Impact: Cannot confirm bookings                  │
│                         │  Recovery:                                        │
│                         │  - Synchronous standby promoted (< 60 seconds)    │
│                         │  - In-flight transactions rolled back             │
│                         │  - Held seats remain valid (Redis-based TTL)      │
│                         │  - Users can retry confirmation after failover    │
│                         │                                                   │
├─────────────────────────┼───────────────────────────────────────────────────┤
│                         │                                                   │
│  Payment gateway down   │  Impact: Cannot process payments                  │
│                         │  Recovery:                                        │
│                         │  - Circuit breaker opens after 50% failure rate   │
│                         │  - Display "Payment temporarily unavailable"      │
│                         │  - Extend seat hold TTL by 5 minutes             │
│                         │  - Failover to secondary gateway if available     │
│                         │  - Users notified when gateway recovers           │
│                         │                                                   │
├─────────────────────────┼───────────────────────────────────────────────────┤
│                         │                                                   │
│  Booking service crash  │  Impact: In-flight bookings interrupted           │
│                         │  Recovery:                                        │
│                         │  - Stateless: new instance picks up immediately   │
│                         │  - Unconfirmed holds auto-expire via Redis TTL    │
│                         │  - Saga-based rollback for partial confirmations  │
│                         │                                                   │
├─────────────────────────┼───────────────────────────────────────────────────┤
│                         │                                                   │
│  Kafka broker down      │  Impact: Notifications delayed                    │
│                         │  Recovery:                                        │
│                         │  - 3-broker cluster: tolerates 1 broker failure   │
│                         │  - Notifications are async, non-blocking          │
│                         │  - Bookings still succeed without notifications   │
│                         │  - Messages replayed after recovery               │
│                         │                                                   │
├─────────────────────────┼───────────────────────────────────────────────────┤
│                         │                                                   │
│  Elasticsearch down     │  Impact: Search unavailable                       │
│                         │  Recovery:                                        │
│                         │  - Fallback to MySQL direct queries (slower)      │
│                         │  - Serve cached popular searches from Redis       │
│                         │  - Homepage shows trending/popular events         │
│                         │  - Browsing by city/date still works via MySQL    │
│                         │                                                   │
└─────────────────────────┴───────────────────────────────────────────────────┘
```

### Graceful Degradation Strategy

```
┌─────────────────────────────────────────────────────────────────────┐
│              GRACEFUL DEGRADATION TIERS                              │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  Tier 0 (Fully healthy):                                            │
│    All features operational                                         │
│                                                                      │
│  Tier 1 (Search degraded):                                          │
│    Search → fallback to MySQL + cached results                      │
│    Browsing still works via category/city navigation                │
│    Booking fully operational                                        │
│                                                                      │
│  Tier 2 (Notifications degraded):                                   │
│    Booking works; confirmation shown in UI                          │
│    Email/SMS notifications queued for later delivery                │
│    User can check booking status in-app                             │
│                                                                      │
│  Tier 3 (Payment degraded):                                         │
│    Browse and search work normally                                  │
│    Seat selection and hold work                                     │
│    Payment page shows "temporarily unavailable"                     │
│    Hold TTL extended; user notified when payment is back            │
│                                                                      │
│  Tier 4 (Booking degraded):                                         │
│    Browse and search work (cached data)                             │
│    Seat map shows "booking temporarily unavailable"                 │
│    System serves read-only event information                        │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

### Expired Hold Cleanup

```
┌─────────────────────────────────────────────────────────────────┐
│              HOLD EXPIRY AND CLEANUP                              │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Primary mechanism: Redis TTL auto-expiry                       │
│  ─────────────────────────────────────────                      │
│  SET seat_hold:shw_x:A1 ... EX 480                              │
│  After 480 seconds: key auto-deleted, seat becomes available    │
│  No background job needed for Redis cleanup                     │
│                                                                  │
│  MySQL cleanup (for audit trail):                               │
│  ────────────────────────────────                               │
│  Scheduled job every 1 minute:                                  │
│  UPDATE show_seats                                              │
│  SET status = 'available', held_by_user = NULL,                 │
│      held_until = NULL                                          │
│  WHERE status = 'held' AND held_until < NOW();                  │
│                                                                  │
│  Redis keyspace notifications (optional):                       │
│  ─────────────────────────────────────────                      │
│  Subscribe to expired key events:                               │
│  CONFIG SET notify-keyspace-events Ex                           │
│  SUBSCRIBE __keyevent@0__:expired                               │
│  → On expiry: update MySQL status + notify waiting users        │
│                                                                  │
│  Waiting list notification:                                     │
│  ──────────────────────────                                     │
│  When held seat expires for a sold-out event:                   │
│  → Check waiting list for this show                             │
│  → Send push notification: "A seat is now available!"           │
│  → First user to hold wins                                      │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## 13. Scalability

### Horizontal Scaling Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    SCALING ARCHITECTURE                                      │
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                    Auto-Scaling Groups                               │    │
│  │                                                                      │    │
│  │  Event Service:     2-20 instances (CPU-based scaling)              │    │
│  │  Booking Service:   4-50 instances (QPS-based scaling)              │    │
│  │  Payment Service:   2-20 instances (queue depth scaling)            │    │
│  │  Search Service:    2-10 instances (CPU + memory scaling)           │    │
│  │  Notification Svc:  2-10 instances (Kafka lag scaling)              │    │
│  │  Queue/WaitRoom:    2-20 instances (connection count scaling)       │    │
│  │                                                                      │    │
│  │  Flash sale override: pre-scale Booking + Queue to max             │    │
│  │  15 minutes before sale opens                                       │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                    Database Scaling                                   │    │
│  │                                                                      │    │
│  │  MySQL:                                                              │    │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐            │    │
│  │  │ Primary  │  │ Standby  │  │ Read     │  │ Read     │            │    │
│  │  │ (writes) │  │ (sync)   │  │ Replica 1│  │ Replica 2│            │    │
│  │  └──────────┘  └──────────┘  └──────────┘  └──────────┘            │    │
│  │                                                                      │    │
│  │  Redis Cluster (6+ nodes):                                          │    │
│  │  ┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐            │    │
│  │  │Node 1│ │Node 2│ │Node 3│ │Node 4│ │Node 5│ │Node 6│            │    │
│  │  │Master│ │Master│ │Master│ │Repl 1│ │Repl 2│ │Repl 3│            │    │
│  │  │Slots │ │Slots │ │Slots │ │      │ │      │ │      │            │    │
│  │  │0-5460│ │5461- │ │10923-│ │      │ │      │ │      │            │    │
│  │  │      │ │10922 │ │16383 │ │      │ │      │ │      │            │    │
│  │  └──────┘ └──────┘ └──────┘ └──────┘ └──────┘ └──────┘            │    │
│  │                                                                      │    │
│  │  Elasticsearch (3-node cluster):                                    │    │
│  │  5 primary shards + 1 replica each = 10 total shards               │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Scaling Bottleneck Analysis

```
┌────────────────────────┬────────────────────────┬───────────────────────────┐
│   Bottleneck           │  Symptom               │  Solution                 │
├────────────────────────┼────────────────────────┼───────────────────────────┤
│ Single Redis shard for │ High latency on hold   │ Seat-range partitioning,  │
│ popular show           │ requests, timeouts     │ dedicated instance for    │
│                        │                        │ flash sale events         │
├────────────────────────┼────────────────────────┼───────────────────────────┤
│ MySQL write throughput │ Booking confirmation   │ Batch confirms, write     │
│ during flash sale      │ latency spikes         │ buffering via queue,      │
│                        │                        │ shard by show_id          │
├────────────────────────┼────────────────────────┼───────────────────────────┤
│ API Gateway under      │ 429 errors, connection │ Pre-scale, connection     │
│ 500K concurrent conns  │ drops                  │ pooling, waiting room     │
│                        │                        │ at CDN layer              │
├────────────────────────┼────────────────────────┼───────────────────────────┤
│ Elasticsearch under    │ Search latency > 1s    │ Warm cache, pre-compute   │
│ flash sale traffic     │                        │ popular queries, circuit  │
│                        │                        │ breaker + fallback        │
├────────────────────────┼────────────────────────┼───────────────────────────┤
│ Payment gateway rate   │ Payment timeouts       │ Multiple gateways,       │
│ limits hit             │                        │ circuit breaker,          │
│                        │                        │ request queuing           │
└────────────────────────┴────────────────────────┴───────────────────────────┘
```

---

## 14. Monitoring and Observability

### Key Metrics Dashboard

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                      MONITORING DASHBOARD                                    │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  BUSINESS METRICS (Grafana)                                                 │
│  ──────────────────────────                                                 │
│  ┌────────────────────────────────────────────────────────────────┐         │
│  │ Booking success rate          Target: > 95%     Alert: < 90%  │         │
│  │ Booking completion rate       Target: > 70%     Alert: < 50%  │         │
│  │ (hold → confirm conversion)                                    │         │
│  │ Revenue per hour              Baseline: ₹50L   Alert: < ₹20L │         │
│  │ Seat hold expiry rate         Target: < 30%     Alert: > 50%  │         │
│  │ Cancellation rate             Target: < 10%     Alert: > 20%  │         │
│  │ Average booking value         Track trend                      │         │
│  └────────────────────────────────────────────────────────────────┘         │
│                                                                              │
│  SYSTEM METRICS (Prometheus + Grafana)                                      │
│  ─────────────────────────────────────                                      │
│  ┌────────────────────────────────────────────────────────────────┐         │
│  │ API latency (P50/P95/P99)     Target P99: < 500ms             │         │
│  │ Seat hold latency (P99)       Target: < 10ms                  │         │
│  │ Payment processing time       Target P95: < 5s                │         │
│  │ Redis operations/sec          Capacity: 100K ops/sec/node     │         │
│  │ MySQL QPS (reads/writes)      Alert: > 80% capacity           │         │
│  │ Kafka consumer lag            Alert: > 10K messages            │         │
│  │ Error rate (5xx)              Target: < 0.1%   Alert: > 1%    │         │
│  │ Connection pool utilization   Alert: > 80%                     │         │
│  └────────────────────────────────────────────────────────────────┘         │
│                                                                              │
│  FLASH SALE SPECIFIC                                                        │
│  ────────────────────                                                       │
│  ┌────────────────────────────────────────────────────────────────┐         │
│  │ Queue depth (waiting users)   Display on war-room dashboard   │         │
│  │ Queue wait time (P50/P95)     Target P95: < 10 minutes        │         │
│  │ Admission rate (users/sec)    Target: 5K/sec                  │         │
│  │ Seats remaining               Real-time countdown             │         │
│  │ Hold/Confirm ratio            Target: > 60%                   │         │
│  │ Time to sell out              Track for capacity planning     │         │
│  └────────────────────────────────────────────────────────────────┘         │
│                                                                              │
│  DISTRIBUTED TRACING (Jaeger / Zipkin)                                      │
│  ─────────────────────────────────────                                      │
│  Trace ID propagated across:                                                │
│  Client → Gateway → Booking Svc → Inventory Svc → Redis                    │
│                   → Payment Svc → Gateway (external)                        │
│                   → Notification Svc → Kafka → Email/SMS provider           │
│                                                                              │
│  SLO: End-to-end booking trace < 30 seconds                                │
│                                                                              │
│  ALERTING (PagerDuty)                                                       │
│  ─────────────────────                                                      │
│  P1: Double booking detected, payment service down, Redis primary down     │
│  P2: Booking success rate < 90%, API P99 > 2s, seat hold expiry > 50%     │
│  P3: Search latency > 1s, notification delay > 5 min                       │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Anomaly Detection

```
┌───────────────────────────────────────────────────────────────────┐
│              ANOMALY DETECTION RULES                              │
├───────────────────────────────────────────────────────────────────┤
│                                                                   │
│  Rule 1: Double Booking Detection (CRITICAL)                     │
│  ─────────────────────────────────────────────                   │
│  Periodic check (every 30 seconds):                              │
│  SELECT show_id, seat_id, COUNT(*) as cnt                        │
│  FROM bookings WHERE status = 'confirmed'                        │
│  GROUP BY show_id, seat_id HAVING cnt > 1;                       │
│  If cnt > 1: PAGE ON-CALL IMMEDIATELY                            │
│                                                                   │
│  Rule 2: Revenue Anomaly                                         │
│  ────────────────────────                                        │
│  If hourly revenue drops below 40% of same-hour-last-week:      │
│  Alert P2 with potential causes (payment down, traffic drop)     │
│                                                                   │
│  Rule 3: Bot Detection                                           │
│  ─────────────────────                                           │
│  If single IP/user holds > 20 seats across shows in 1 hour:     │
│  Flag as potential bot, apply stricter rate limits               │
│                                                                   │
└───────────────────────────────────────────────────────────────────┘
```

---

## 15. Trade-offs and Design Decisions

### Decision 1: Optimistic vs Pessimistic Locking

```
┌────────────────────────────────────────────────────────────────────────┐
│  DECISION: Use Redis SET NX (distributed lock) as primary mechanism   │
│            with MySQL optimistic lock as secondary safety net          │
│                                                                        │
│  Why not pessimistic (SELECT FOR UPDATE)?                             │
│  ─────────────────────────────────────────                            │
│  - Row-level locks block ALL readers during hold period (8 min!)     │
│  - Under 50K concurrent requests, lock wait timeouts are guaranteed  │
│  - DB connection pool exhausted within seconds                        │
│  - MySQL is designed for sub-second transactions, not 8-min locks    │
│                                                                        │
│  Why not pure optimistic (version-based)?                             │
│  ────────────────────────────────────────                             │
│  - Works well for low-medium contention                               │
│  - Under flash sale (1000 users on same seat): 999 retries per round │
│  - Retry storms amplify load instead of reducing it                   │
│  - Still hits MySQL for every attempt                                 │
│                                                                        │
│  Why Redis SET NX + MySQL optimistic?                                 │
│  ─────────────────────────────────────                                │
│  - SET NX: single-threaded, O(1), sub-ms, no retry needed            │
│  - Loser gets immediate (nil) → show alternative seats               │
│  - MySQL optimistic lock only during confirm (low contention)        │
│  - Best of both: speed + durability                                   │
│                                                                        │
└────────────────────────────────────────────────────────────────────────┘
```

### Decision 2: Queue vs First-Come-First-Served

```
┌────────────────────────────────────────────────────────────────────────┐
│  DECISION: Virtual waiting room with queue for flash sales            │
│            Direct access for normal events                            │
│                                                                        │
│  First-Come-First-Served (no queue):                                  │
│  ────────────────────────────────────                                 │
│  + Simpler architecture                                               │
│  + Lower latency for first arrivals                                   │
│  - 500K simultaneous requests overwhelm backend                      │
│  - Unfair: users with faster connections/bots win                    │
│  - Thundering herd on seat selection page                             │
│  - Poor UX: most users see errors or timeouts                        │
│                                                                        │
│  Queue-based (chosen for flash sales):                                │
│  ──────────────────────────────────────                               │
│  + Controlled backend load (5K/sec admission)                        │
│  + Fair: FIFO ordering by arrival time                                │
│  + Predictable wait time for users                                    │
│  + Backend never overloaded                                           │
│  + Waiting room page is static (CDN-served, zero backend cost)       │
│  - Extra component to build and maintain                              │
│  - Slight delay for users (but they get a working experience)        │
│                                                                        │
│  Hybrid approach:                                                     │
│  ────────────────                                                     │
│  - Events with < 80% fill rate: direct access, no queue             │
│  - Events flagged as "high demand": queue enabled automatically      │
│  - Queue activation trigger: > 10x normal traffic in 60s window     │
│                                                                        │
└────────────────────────────────────────────────────────────────────────┘
```

### Decision 3: Pre-Allocated vs Dynamic Seat Selection

```
┌────────────────────────────────────────────────────────────────────────┐
│  DECISION: User-selected seats (primary) with auto-assign option      │
│                                                                        │
│  User-Selected (BookMyShow model):                                    │
│  ──────────────────────────────────                                   │
│  + Users see exact seat map and pick preferred seats                  │
│  + Higher satisfaction (users control their experience)               │
│  + Premium seats can be priced higher (visible on map)                │
│  - More complex UI and more API calls                                 │
│  - Higher contention (everyone wants Row A center)                   │
│  - Seat map must update in near-real-time                             │
│                                                                        │
│  Auto-Assigned (Ticketmaster "best available"):                       │
│  ──────────────────────────────────────────────                       │
│  + Simpler: user just picks count + section                           │
│  + Lower contention (system distributes demand)                       │
│  + Faster booking flow                                                │
│  - Less user control                                                  │
│  - May assign split seats (A1 + C15 instead of A1 + A2)             │
│                                                                        │
│  Our hybrid:                                                          │
│  ────────────                                                         │
│  - Default: user-selected with real-time seat map                    │
│  - "Quick book" option: auto-assign best available N adjacent seats  │
│  - Flash sales: can default to auto-assign to reduce contention      │
│                                                                        │
└────────────────────────────────────────────────────────────────────────┘
```

### Decision 4: Monolith vs Microservices

```
┌────────────────────────────────────────────────────────────────────────┐
│  DECISION: Microservices with domain-based decomposition              │
│                                                                        │
│  Why not monolith?                                                    │
│  ─────────────────                                                    │
│  - Booking service needs independent scaling during flash sales      │
│  - Payment service needs circuit breaker isolation                    │
│  - Search service has different scaling characteristics (CPU-bound)   │
│  - Team ownership boundaries align with service boundaries            │
│  - Failure isolation: payment crash should not affect browsing        │
│                                                                        │
│  Service boundaries (Domain-Driven Design):                           │
│  ──────────────────────────────────────────                           │
│  Event Bounded Context:    Event, Venue, Show, Screen                │
│  Booking Bounded Context:  Booking, Hold, SeatInventory              │
│  Payment Bounded Context:  Payment, Refund                           │
│  User Bounded Context:     User, Auth, Preferences                   │
│  Search Bounded Context:   Index, Query, Recommendations             │
│                                                                        │
│  Inter-service communication:                                         │
│  ────────────────────────────                                         │
│  Synchronous (gRPC):  Booking → Inventory (hold seats)               │
│                       Booking → Payment (charge)                      │
│  Asynchronous (Kafka): Booking → Notification (confirm email)        │
│                        Event → Search (index update)                  │
│                        Booking → Analytics (event stream)             │
│                                                                        │
└────────────────────────────────────────────────────────────────────────┘
```

### Decision 5: Hold Duration

```
┌────────────────────────────────────────────────────────────────────────┐
│  DECISION: 8-minute hold with dynamic adjustment                      │
│                                                                        │
│  Too short (2 min):                                                   │
│  - User can't enter payment details in time                          │
│  - High hold expiry rate → frustrated users                          │
│  - Especially bad for UPI/netbanking (OTP delays)                    │
│                                                                        │
│  Too long (15 min):                                                   │
│  - Seats locked unnecessarily by users who abandoned                 │
│  - During flash sale: 50K seats held for 15 min blocks everyone     │
│  - Reduces effective inventory                                        │
│                                                                        │
│  Chosen: 8 minutes (default), dynamically adjusted:                   │
│  ───────────────────────────────────────────────                      │
│  - Normal event: 8 minutes                                           │
│  - High-demand event (>80% full): 5 minutes                         │
│  - Flash sale: 5 minutes with 1-min payment extension on request     │
│  - Group booking (10+ seats): 12 minutes                             │
│                                                                        │
└────────────────────────────────────────────────────────────────────────┘
```

---

## 16. Interview Deep-Dive Questions

### Q1: How do you prevent double booking?

**Answer:** We use a multi-layer defense:

1. **Redis SET NX (primary guard):** The `SET seat_hold:{show_id}:{seat_id} NX EX 480` command is
   atomic and single-threaded. Only one caller can succeed for a given seat. All others receive
   `(nil)` immediately. This is the first and most critical barrier.

2. **MySQL optimistic locking (secondary guard):** During confirmation, we execute:
   ```sql
   UPDATE show_seats SET status='booked', version=version+1
   WHERE show_id=? AND seat_id=? AND status='held' AND version=?
   ```
   If `affected_rows = 0`, the seat was already booked (version mismatch) -- reject.

3. **Unique constraint:** `UNIQUE(show_id, seat_id, status='booked')` ensures the database itself
   rejects duplicate bookings even if application logic has a bug.

4. **Post-hoc validation:** Background job runs every 30 seconds checking for duplicate
   `(show_id, seat_id)` combinations with `status='confirmed'`. Any duplicates trigger P1 alert.

---

### Q2: How do you handle 500K users trying to book 50K seats simultaneously?

**Answer:** The virtual waiting room is key:

1. **CDN-served waiting room:** Users land on a static HTML page served entirely by CloudFront.
   Zero backend load for the initial stampede.

2. **Queue assignment:** Users poll `GET /queue/status` which reads their position from a Redis
   sorted set (ZRANK). Server load: simple Redis reads at ~500K/5s = 100K reads/sec -- well within
   Redis capacity.

3. **Controlled admission:** Token bucket releases 5,000 users/second to the actual booking page.
   Backend sees max 5K concurrent booking requests -- manageable.

4. **Pre-generated tokens:** For extra safety, we pre-generate 60K tokens. Once exhausted, the
   system immediately shows "sold out" instead of processing more requests.

5. **Pre-scaling:** 15 minutes before sale, we pre-scale all services to peak capacity. No
   auto-scaling delay during the critical window.

---

### Q3: What happens if payment fails after seats are held?

**Answer:** The seats remain held until either:

1. **User retries payment** (within hold TTL): The hold_token remains valid. User can retry with a
   different payment method. We generate a new `idempotency_key` for each retry to prevent
   double-charging.

2. **Hold expires (TTL):** After 8 minutes, Redis auto-deletes the hold keys. The MySQL cleanup job
   marks seats as `available`. Seats return to the pool for other users.

3. **Explicit release:** If the user clicks "Cancel" or navigates away, we proactively `DEL` the
   hold keys in Redis and update MySQL immediately, freeing seats faster.

4. **Payment in limbo (timeout):** If the payment gateway timed out but actually processed the
   charge, a reconciliation job checks pending payments every 5 minutes. If the gateway confirms
   success, we auto-confirm the booking (if hold is still valid) or initiate a refund (if hold
   expired).

---

### Q4: How do you handle seat selection for group bookings (10+ seats)?

**Answer:**

1. **Atomic multi-seat hold:** We use the Redis Lua script that attempts to `SET NX` all requested
   seats atomically. If any single seat fails, all previously acquired seats in the batch are
   released. This ensures the group gets all seats or none.

2. **Adjacent seat algorithm:** The system finds contiguous blocks of available seats:
   - Query available seats for the row, find consecutive sequences >= group size
   - Prefer center-of-row positions (better view)
   - If no single row has enough, split across 2 adjacent rows

3. **Extended hold:** Group bookings get 12-minute hold instead of 8 minutes, because payment
   coordination may take longer (e.g., one person paying for 15 friends).

4. **Concurrency safety:** The Lua script runs atomically on a single Redis thread, so there is no
   risk of a partial group hold.

---

### Q5: How would you design dynamic pricing?

**Answer:**

```
┌───────────────────────────────────────────────────────────────────┐
│  Dynamic Pricing Formula:                                        │
│  ────────────────────────                                        │
│  final_price = base_price × demand_multiplier × time_multiplier  │
│                                                                   │
│  demand_multiplier:                                              │
│    fill_rate < 30%:   0.8  (discount to drive sales)             │
│    fill_rate 30-70%:  1.0  (base price)                          │
│    fill_rate 70-90%:  1.3  (high demand premium)                 │
│    fill_rate > 90%:   1.5  (near sold-out premium)               │
│                                                                   │
│  time_multiplier:                                                │
│    > 7 days before:   0.9  (early bird discount)                 │
│    1-7 days before:   1.0  (standard)                            │
│    < 24h before:      1.2  (last-minute surge)                   │
│    < 4h before:       0.7  (fire sale for empty seats)           │
│                                                                   │
│  Implementation:                                                 │
│  - Price computed at seat-map load time (not stored statically)  │
│  - Locked at hold time (price stored in hold_token)              │
│  - Price honored during confirmation (no bait-and-switch)        │
│  - Pricing rules stored in config service with 5-min cache       │
└───────────────────────────────────────────────────────────────────┘
```

---

### Q6: How do you handle the thundering herd problem when a hold expires during a flash sale?

**Answer:** When a popular seat's hold expires during a flash sale, many users may be watching that
seat on their seat map and try to grab it simultaneously.

1. **Server-side jitter:** When sending seat availability updates via WebSocket, each client
   receives the update with a random jitter of 0-500ms. This spreads the thundering herd over
   half a second.

2. **Client-side exponential backoff:** If a hold attempt returns 409, the client waits
   `100ms * random(1, 2^attempt)` before retrying.

3. **Redis SET NX:** Even if 1000 users try simultaneously, Redis handles this with zero contention
   -- exactly one wins, 999 get `(nil)` in microseconds. The thundering herd is a non-issue at the
   Redis level.

---

### Q7: How do you ensure exactly-once payment processing?

**Answer:** Exactly-once semantics in payment through idempotency keys:

1. Client generates a UUID `idempotency_key` per booking attempt.
2. Server stores `(idempotency_key, status, response)` in the payments table.
3. On retry: if key exists with `status=success`, return the cached response without re-charging.
4. On retry: if key exists with `status=processing`, return 202 (try again later).
5. The payment gateway itself uses our `idempotency_key` in its API call, so even if we send the
   same request twice, the gateway charges only once.
6. Critical: the `INSERT payment` and `UPDATE booking status=confirmed` happen in the same MySQL
   transaction. Either both succeed or neither does.

---

### Q8: How do you handle multi-region deployment?

**Answer:**

- **Event catalog:** Replicated across regions via MySQL async replication. Users in Mumbai see
  Mumbai events; the data is region-local.
- **Seat inventory:** Seats for a given show exist on a single Redis primary in the show's home
  region. All booking requests for that show route to the home region, even from remote users.
  This ensures strong consistency without cross-region coordination.
- **User data:** Partitioned by home region but accessible cross-region with slight latency.
- **Search:** Region-local Elasticsearch clusters indexed with region-relevant events only.
- **Latency:** Users booking events in their own city see <50ms latency. Users booking events in
  another city (rare) see ~200ms additional latency due to cross-region routing.

---

### Q9: How do you handle partial failures in the booking confirmation flow?

**Answer:** We use a saga pattern with compensating transactions:

```
Step 1: Validate hold      → Success → Continue
                            → Failure → Return error (hold expired)

Step 2: Charge payment      → Success → Continue
                            → Failure → Release hold, return error

Step 3: Persist booking     → Success → Continue
(MySQL transaction)         → Failure → Refund payment, release hold

Step 4: Update seat status  → Success → Continue
(Redis → MySQL)             → Failure → Reconciliation job fixes later
                                        (booking is confirmed, seats
                                         will be marked booked eventually)

Step 5: Send notification   → Success → Done
(async via Kafka)           → Failure → Retry via dead-letter queue
                                        (booking is confirmed regardless)
```

Each step has a compensating action. Steps 4-5 are eventually consistent and non-blocking.

---

### Q10: How would you handle a scenario where Redis loses data (e.g., server crash without persistence)?

**Answer:**

1. **Prevention:** Redis AOF persistence with `appendfsync everysec`. Maximum 1 second of data
   loss. For critical flash sales, use `appendfsync always` (slight performance hit).

2. **Detection:** Monitoring alert when Redis restarts. Health check detects empty key space.

3. **Recovery:**
   - Query MySQL for all seats with `status='held'` and `held_until > NOW()`
   - Re-create Redis hold keys with TTL = `held_until - NOW()`
   - Recovery time: ~5 seconds for a typical show (1000 seats)

4. **During recovery:** Hold requests return 503. The 8-minute hold window provides a buffer --
   users are unlikely to notice a 5-second recovery window.

5. **Worst case (total Redis loss during flash sale):** Switch to MySQL pessimistic locking
   (SELECT FOR UPDATE) as fallback. Higher latency but correct behavior. Feature flag controls
   this failover.

---

### Q11: How do you prevent bots and scalpers from hoarding tickets?

**Answer:**

1. **CAPTCHA:** Required before entering the waiting room queue for high-demand events.
2. **Rate limiting:** Max 5 hold requests per minute per user. Max 1 queue entry per event per user.
3. **Device fingerprinting:** Detect multiple accounts from the same device/browser.
4. **IP-based limits:** Max 10 bookings per IP per hour (accommodates office networks).
5. **Purchase limits:** Max 6 tickets per user per event (policy-enforced).
6. **Behavioral analysis:** ML model scores suspicious patterns (instant selection, no browsing,
   API-only access) and adds CAPTCHA challenges.
7. **Phone verification:** Require verified phone number before booking high-demand events.

---

### Q12: How do you design the seat map for real-time updates?

**Answer:**

- **Initial load:** `GET /shows/{id}/seats` returns full seat map (~50KB for 1000 seats).
- **Real-time updates:** WebSocket connection per user viewing a seat map:
  ```
  ws://api.example.com/v1/shows/{show_id}/seats/live
  ```
- **Server broadcasts deltas:** When a seat status changes, the server publishes only the diff:
  ```json
  { "type": "seat_update", "seats": [{ "id": "A1", "status": "held" }] }
  ```
- **Fan-out:** Redis Pub/Sub per show_id. Each WebSocket server subscribes to the show's channel
  and pushes updates to connected clients.
- **Scaling concern:** If 500K users view the same seat map, fan-out is massive. Solution: batch
  updates every 1 second and send consolidated diffs. Clients don't need per-millisecond accuracy
  for display.

---

### Q13: How do you handle timezone and scheduling for global events?

**Answer:**

- All times stored in UTC in the database.
- Show records include a `timezone` field (e.g., `Asia/Kolkata`, `America/New_York`).
- API responses include both UTC and local time for display.
- Client converts to user's local timezone for display.
- For global events (e.g., virtual concert), sale open time is in UTC; the client shows "Sale opens
  at 10 PM IST / 12:30 PM ET."
- Scheduled jobs (hold cleanup, sale opening) run on UTC cron.

---

### Q14: How do you handle inventory sync between the online system and box office (walk-in) sales?

**Answer:**

- Box office terminals connect to the same Inventory Service via internal API.
- Same Redis-based seat holds apply for box office selections.
- Box office has a reserved quota (e.g., 10% of seats) that can only be sold offline. This prevents
  a scenario where online sales consume 100% of seats, leaving nothing for walk-ins.
- Reserved quota is released to online pool 2 hours before showtime if unsold.
- Both channels write to the same MySQL booking table -- single source of truth.

---

### Q15: How would you add a waitlist feature for sold-out events?

**Answer:**

1. **Join waitlist:** `POST /v1/events/{id}/waitlist` adds user to Redis sorted set
   (`ZADD waitlist:{show_id} <timestamp> <user_id>`).

2. **Notification on availability:** When a booked seat is cancelled or a held seat expires for a
   sold-out show:
   - Pop the first N users from the waitlist (ZPOPMIN).
   - Send push notification: "A seat is now available! You have 3 minutes to claim it."
   - Generate a pre-authorized booking token with 3-minute TTL.

3. **Fair ordering:** Waitlist is FIFO (sorted by join time). First on the list gets notified first.

4. **Expiry:** If the notified user doesn't book within 3 minutes, the next user in the waitlist is
   notified. This cascades until someone books or the waitlist is exhausted.

5. **Limits:** Max 5,000 users per waitlist. Beyond that: "Waitlist is full. Check back later."

---

## 17. Summary

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                      SYSTEM DESIGN SUMMARY                                   │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  Core challenge:    Sell limited inventory (seats) to massive concurrent     │
│                     demand with zero overselling and sub-second latency.     │
│                                                                              │
│  Key decisions:                                                              │
│  ──────────────                                                             │
│  1. Redis SET NX for seat locking (sub-ms, atomic, auto-expiry via TTL)    │
│  2. Virtual waiting room for flash sales (CDN-served, controlled admission) │
│  3. Two-phase booking (hold → pay → confirm) with saga-based rollback      │
│  4. Idempotent payments with per-request idempotency keys                   │
│  5. Microservices with event-driven async processing (Kafka)                │
│  6. Elasticsearch for search with CDC-based near-real-time indexing         │
│                                                                              │
│  Scaling numbers:                                                            │
│  ────────────────                                                           │
│  - 10M daily bookings, 50M seat availability checks                        │
│  - Flash sale: 500K users → 5K/sec admission → 50K seats in ~20 seconds   │
│  - Redis: <1ms seat hold, 100K ops/sec per node                            │
│  - MySQL: sharded by show_id (seats), user_id (bookings)                   │
│  - 99.99% availability with multi-layer failover                            │
│                                                                              │
│  What makes this design "hard":                                              │
│  ──────────────────────────────                                             │
│  - Strong consistency for inventory + eventual consistency for rest         │
│  - Flash sale thundering herd mitigation                                    │
│  - Payment failure handling with distributed saga                           │
│  - Real-time seat map updates at scale                                      │
│  - Bot prevention without degrading legitimate user experience              │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```
