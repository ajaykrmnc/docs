# Design a Ride-Sharing Service (Uber / Lyft)

**Difficulty:** Hard | **Companies:** Uber, Lyft, Google, Amazon, Grab, Ola, DiDi, Bolt

---

## 1. Problem Statement and Scope

Design a **ride-sharing platform** that matches riders with nearby drivers in real time,
supports live location tracking, dynamic (surge) pricing, fare estimation, payments,
and end-to-end ride lifecycle management -- from requesting a ride to completing payment.

### In Scope

| Area                      | Details                                                      |
|---------------------------|--------------------------------------------------------------|
| Ride Request & Matching   | Rider requests ride, system finds and dispatches best driver  |
| Real-Time Location        | Driver location tracked every 3-4 seconds                    |
| Dynamic Pricing           | Surge pricing based on supply-demand ratio per geo-cell      |
| Fare Estimation & Payment | Upfront fare estimate, metered billing, payment processing    |
| Ride Lifecycle            | Request -> Match -> Pickup -> In-Progress -> Complete -> Pay  |
| Rating & Feedback         | Bidirectional ratings after ride completion                   |
| Multiple Ride Types       | UberX, UberXL, UberBlack, Pool (shared rides)                |

### Out of Scope

- Autonomous vehicles / self-driving integration
- Food delivery (Uber Eats) or package delivery
- Driver background checks and detailed onboarding workflows
- Detailed fraud detection ML pipelines (mentioned at high level only)
- Multi-modal transport (bikes, scooters, public transit)

---

## 2. Functional Requirements

### 2.1 Rider Functions

| #  | Function              | Description                                                     |
|----|-----------------------|-----------------------------------------------------------------|
| R1 | Request Ride          | Specify pickup, dropoff, ride type; receive fare estimate       |
| R2 | See Nearby Drivers    | View available drivers on the map within radius                 |
| R3 | Fare Estimation       | Get upfront price based on distance, time, surge multiplier     |
| R4 | Real-Time Tracking    | Track assigned driver en route and during trip                  |
| R5 | Ride History          | View past rides, receipts, routes                               |
| R6 | Payment               | Pay via credit card, wallet, or cash; split fare                |
| R7 | Rating                | Rate driver (1-5 stars) and leave optional comment              |
| R8 | Cancel Ride           | Cancel before or after matching with applicable fee             |
| R9 | Ride Pooling          | Share ride with other riders heading in similar direction        |
| R10| Schedule Ride         | Book ride in advance for a future time                          |

### 2.2 Driver Functions

| #  | Function              | Description                                                     |
|----|-----------------------|-----------------------------------------------------------------|
| D1 | Toggle Availability   | Go online/offline to accept ride requests                       |
| D2 | Accept/Decline Ride   | Receive ride request with pickup info; accept or decline/timeout|
| D3 | Navigation            | Turn-by-turn directions to pickup and dropoff                   |
| D4 | Start/End Trip        | Mark pickup complete and trip end for billing                   |
| D5 | Earnings Tracking     | View daily/weekly earnings, trip details, surge bonuses         |
| D6 | Rating                | Rate rider after trip completion                                |
| D7 | Location Broadcast    | App continuously sends GPS coordinates while online             |

### 2.3 Admin / Platform Functions

| #  | Function              | Description                                                     |
|----|-----------------------|-----------------------------------------------------------------|
| A1 | Driver Onboarding     | Approve new driver registrations, document verification         |
| A2 | Surge Management      | Configure surge pricing rules, caps, and geo-cell granularity   |
| A3 | Analytics Dashboard   | Real-time metrics: rides, wait times, supply-demand heatmaps    |
| A4 | Dispute Resolution    | Handle payment disputes, ride complaints                        |
| A5 | Geo-Fencing           | Define service areas, airports, restricted zones                |

---

## 3. Non-Functional Requirements

| Requirement          | Target                                                             |
|----------------------|--------------------------------------------------------------------|
| Matching Latency     | < 3 seconds from ride request to driver notification               |
| Location Update Rate | Every 3-4 seconds per active driver                                |
| Availability         | 99.99% uptime (< 52.6 min downtime/year)                          |
| Concurrent Rides     | Support 1M+ concurrent active rides                                |
| Concurrent Drivers   | Support 5M+ online drivers sending location updates                |
| Global Coverage      | Multi-region deployment across continents                          |
| Data Durability      | Zero loss of trip and payment records                              |
| Consistency          | Strong consistency for trip state and payments                     |
| Scalability          | Horizontal scaling; handle 10x traffic spikes (NYE, events)       |
| Security             | Encrypt PII, PCI-DSS compliance for payments, end-to-end TLS      |

---

## 4. Back-of-Envelope Estimation

### 4.1 Traffic Estimates

```
Daily Active Riders:       30M
Daily Active Drivers:      5M
Daily Rides:               20M
Average Ride Duration:     15 minutes

Peak concurrent rides:     20M / (24 * 4) = ~833K, round to 1M with peak factor
Concurrent online drivers: 5M (sending location updates)
```

### 4.2 Location Update Throughput

```
Online drivers:                   5,000,000
Location update interval:        4 seconds
Updates per second:               5,000,000 / 4 = 1,250,000 updates/sec

Each update payload:              ~60 bytes (driver_id, lat, lng, heading, speed, timestamp)
Location ingestion bandwidth:     1.25M * 60 B = 75 MB/sec = 600 Mbps

Location updates per day:         1.25M * 86,400 = ~108 billion
```

### 4.3 Storage Estimates

```
Trip Data:
  - Per trip record:     ~1 KB (IDs, locations, timestamps, fare, status)
  - Daily:               20M * 1 KB = 20 GB/day
  - Yearly:              20 GB * 365 = ~7.3 TB/year

Location History (for analytics, not real-time):
  - Per update:          60 bytes
  - Daily:               108B * 60 B = ~6.5 TB/day  (hot: Redis, cold: object store)
  - Retention:           7 days hot = ~45 TB, then archive to S3/GCS

Ride Route (polyline):
  - Per ride:            ~5 KB (encoded polyline of GPS points during trip)
  - Daily:               20M * 5 KB = 100 GB/day

User Profiles:
  - 100M riders + 10M drivers = 110M profiles * 2 KB = ~220 GB (fits one DB)
```

### 4.4 Bandwidth Estimates

```
Rider tracking updates:       1M concurrent rides * 1 update/3 sec * 100 B = ~33 MB/sec
Driver location ingestion:    75 MB/sec (calculated above)
API requests (ride ops):      ~50K ride-related API calls/sec at peak

Total inbound bandwidth:      ~110 MB/sec = ~880 Mbps
Total outbound bandwidth:     ~150 MB/sec = ~1.2 Gbps (includes map tiles, tracking)
```

---

## 5. API Design

### 5.1 Ride APIs

```
POST   /v1/rides/request
  Body: {
    rider_id:    "uuid",
    pickup:      { lat: 37.7749, lng: -122.4194, address: "123 Market St" },
    dropoff:     { lat: 37.7849, lng: -122.4094, address: "456 Mission St" },
    ride_type:   "UBER_X" | "UBER_XL" | "UBER_BLACK" | "POOL",
    payment_method_id: "pm_xxx",
    scheduled_at: null | "2026-04-09T18:00:00Z"    // null = now
  }
  Response: 201 {
    ride_id: "ride_xxx",
    status: "MATCHING",
    estimated_fare: { min: 12.50, max: 16.00, currency: "USD", surge: 1.2 },
    estimated_pickup_time: "3 min"
  }

GET    /v1/rides/estimate
  Params: pickup_lat, pickup_lng, dropoff_lat, dropoff_lng, ride_type
  Response: 200 {
    estimates: [
      { ride_type: "UBER_X",     fare: { min: 12, max: 16 }, eta: "3 min", surge: 1.0 },
      { ride_type: "UBER_XL",    fare: { min: 18, max: 24 }, eta: "5 min", surge: 1.0 },
      { ride_type: "UBER_BLACK", fare: { min: 30, max: 40 }, eta: "7 min", surge: 1.5 }
    ]
  }

POST   /v1/rides/{ride_id}/accept
  Body: { driver_id: "uuid" }
  Response: 200 { status: "ACCEPTED", pickup_eta: "4 min" }

POST   /v1/rides/{ride_id}/cancel
  Body: { cancelled_by: "RIDER" | "DRIVER", reason: "string" }
  Response: 200 { cancellation_fee: 5.00 }

POST   /v1/rides/{ride_id}/start
  Body: { driver_id: "uuid", odometer: 45230.5 }
  Response: 200 { status: "IN_PROGRESS", started_at: "timestamp" }

POST   /v1/rides/{ride_id}/complete
  Body: { driver_id: "uuid", odometer: 45238.2 }
  Response: 200 {
    status: "COMPLETED",
    fare: { base: 2.50, distance: 8.40, time: 3.20, surge: 1.50, total: 18.60 },
    payment_status: "CHARGED"
  }

GET    /v1/rides/{ride_id}/track
  Response: 200 {
    driver_location: { lat: 37.775, lng: -122.418 },
    eta_to_pickup: "2 min" | null,
    eta_to_dropoff: "12 min" | null,
    route_polyline: "encoded_polyline_string"
  }
```

### 5.2 Driver Location API (High Frequency)

```
PUT    /v1/drivers/{driver_id}/location
  Body: {
    lat:       37.7749,
    lng:       -122.4194,
    heading:   270.0,        // degrees
    speed:     35.5,         // km/h
    accuracy:  5.0,          // meters
    timestamp: 1712678400000 // epoch ms
  }
  Response: 200 { ack: true }

  Notes:
  - Called every 3-4 seconds by driver app
  - Use UDP or persistent WebSocket for reduced overhead
  - Batching: driver app can batch 3-5 updates and send every 12-15 sec
```

### 5.3 Driver Availability API

```
PUT    /v1/drivers/{driver_id}/availability
  Body: { status: "ONLINE" | "OFFLINE", vehicle_type: "SEDAN" }
  Response: 200 { status: "ONLINE" }

GET    /v1/drivers/nearby
  Params: lat, lng, radius_km=5, vehicle_type=SEDAN
  Response: 200 {
    drivers: [
      { driver_id: "uuid", lat: 37.776, lng: -122.419, eta: "3 min", rating: 4.8 },
      ...
    ]
  }
```

### 5.4 Rating API

```
POST   /v1/rides/{ride_id}/rate
  Body: {
    rated_by:  "RIDER" | "DRIVER",
    rating:    5,              // 1-5
    comment:   "Great ride!",
    tags:      ["clean_car", "good_navigation"]
  }
  Response: 201 { success: true }
```

---

## 6. Data Model and Database Selection

### 6.1 Core Entities and Schema

```
┌─────────────────────────────────────────────────────────────────┐
│                          users                                  │
├─────────────────────────────────────────────────────────────────┤
│ user_id          UUID  PK                                       │
│ type             ENUM('RIDER','DRIVER')                         │
│ name             VARCHAR(100)                                   │
│ email            VARCHAR(255) UNIQUE                            │
│ phone            VARCHAR(20) UNIQUE                             │
│ password_hash    VARCHAR(255)                                   │
│ rating_avg       DECIMAL(3,2)                                   │
│ rating_count     INT                                            │
│ status           ENUM('ACTIVE','SUSPENDED','DEACTIVATED')       │
│ created_at       TIMESTAMP                                      │
│ updated_at       TIMESTAMP                                      │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                         drivers                                 │
├─────────────────────────────────────────────────────────────────┤
│ driver_id        UUID  PK  FK(users.user_id)                    │
│ license_number   VARCHAR(50)                                    │
│ vehicle_type     ENUM('SEDAN','SUV','LUXURY','VAN')             │
│ vehicle_make     VARCHAR(50)                                    │
│ vehicle_model    VARCHAR(50)                                    │
│ vehicle_year     INT                                            │
│ vehicle_plate    VARCHAR(20)                                    │
│ is_online        BOOLEAN                                        │
│ current_ride_id  UUID  NULLABLE                                 │
│ city_id          UUID  FK(cities.city_id)                       │
│ acceptance_rate  DECIMAL(5,2)                                   │
│ cancellation_rate DECIMAL(5,2)                                  │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                          trips                                  │
├─────────────────────────────────────────────────────────────────┤
│ trip_id          UUID  PK                                       │
│ rider_id         UUID  FK(users.user_id)                        │
│ driver_id        UUID  FK(users.user_id)  NULLABLE              │
│ ride_type        ENUM('UBER_X','UBER_XL','UBER_BLACK','POOL')   │
│ status           ENUM('REQUESTED','MATCHING','ACCEPTED',        │
│                       'ARRIVING','IN_PROGRESS','COMPLETED',     │
│                       'CANCELLED')                              │
│ pickup_lat       DECIMAL(10,7)                                  │
│ pickup_lng       DECIMAL(10,7)                                  │
│ pickup_address   VARCHAR(500)                                   │
│ dropoff_lat      DECIMAL(10,7)                                  │
│ dropoff_lng      DECIMAL(10,7)                                  │
│ dropoff_address  VARCHAR(500)                                   │
│ fare_estimate    JSONB                                          │
│ fare_actual      JSONB                                          │
│ surge_multiplier DECIMAL(3,2)                                   │
│ distance_km      DECIMAL(8,2)                                   │
│ duration_min     DECIMAL(8,2)                                   │
│ requested_at     TIMESTAMP                                      │
│ accepted_at      TIMESTAMP                                      │
│ pickup_at        TIMESTAMP                                      │
│ dropoff_at       TIMESTAMP                                      │
│ cancelled_at     TIMESTAMP                                      │
│ cancelled_by     ENUM('RIDER','DRIVER','SYSTEM')                │
│ city_id          UUID                                           │
│ payment_id       UUID  FK(payments.payment_id)                  │
│ route_polyline   TEXT                                            │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                        payments                                 │
├─────────────────────────────────────────────────────────────────┤
│ payment_id       UUID  PK                                       │
│ trip_id          UUID  FK(trips.trip_id)                         │
│ rider_id         UUID  FK(users.user_id)                        │
│ driver_id        UUID  FK(users.user_id)                        │
│ amount           DECIMAL(10,2)                                  │
│ currency         VARCHAR(3)                                     │
│ payment_method   ENUM('CARD','WALLET','CASH')                   │
│ status           ENUM('PENDING','AUTHORIZED','CAPTURED',        │
│                       'REFUNDED','FAILED')                      │
│ stripe_charge_id VARCHAR(100)                                   │
│ platform_fee     DECIMAL(10,2)                                  │
│ driver_payout    DECIMAL(10,2)                                  │
│ created_at       TIMESTAMP                                      │
│ updated_at       TIMESTAMP                                      │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                        ratings                                  │
├─────────────────────────────────────────────────────────────────┤
│ rating_id        UUID  PK                                       │
│ trip_id          UUID  FK(trips.trip_id)                         │
│ rated_by         UUID  FK(users.user_id)                        │
│ rated_user       UUID  FK(users.user_id)                        │
│ score            INT  CHECK(1..5)                               │
│ comment          TEXT                                            │
│ tags             TEXT[]                                          │
│ created_at       TIMESTAMP                                      │
└─────────────────────────────────────────────────────────────────┘
```

### 6.2 Database Selection per Data Type

```
┌──────────────────────┬─────────────────┬────────────────────────────────────────┐
│ Data Type            │ Database        │ Rationale                              │
├──────────────────────┼─────────────────┼────────────────────────────────────────┤
│ User Profiles        │ PostgreSQL      │ Relational, ACID, moderate size        │
│ Driver Profiles      │ PostgreSQL      │ Joins with users, transactional        │
│ Active Trips         │ PostgreSQL      │ Strong consistency for state machine   │
│ Trip History         │ Cassandra       │ High write volume, time-series,        │
│                      │                 │ partition by city + date               │
│ Driver Locations     │ Redis (GeoSet)  │ In-memory, GEOADD/GEORADIUS, ultra    │
│ (real-time)          │                 │ low latency, 1.25M writes/sec         │
│ Location History     │ Apache Kafka    │ Stream to S3/HDFS for analytics        │
│ (archival)           │ + S3/HDFS       │                                        │
│ Payments             │ PostgreSQL      │ ACID required, audit trail             │
│ Surge Pricing Config │ Redis           │ Fast reads per geo-cell, TTL-based     │
│ Notifications        │ Redis Pub/Sub   │ Real-time push to driver/rider         │
│ Search/Analytics     │ Elasticsearch   │ Full-text search, aggregations         │
└──────────────────────┴─────────────────┴────────────────────────────────────────┘
```

### 6.3 Geospatial Index Design

```
Approach: Redis GeoHash + Application-Level QuadTree Hybrid

Redis GeoSet for Real-Time Queries:
  GEOADD drivers:online:sedan <lng> <lat> <driver_id>
  GEORADIUS drivers:online:sedan <lng> <lat> 5 km WITHCOORD WITHDIST COUNT 20 ASC

  - Separate GeoSets per vehicle type: drivers:online:sedan, drivers:online:suv
  - Separate GeoSets per city for scalability: drivers:nyc:sedan, drivers:sf:sedan
  - O(N+log(M)) where N = elements returned, M = elements in set
  - Redis cluster with ~16 shards handles 1.25M updates/sec

S2 Geometry (Google-style) for Advanced Queries:
  - Earth divided into hierarchical cells at multiple levels
  - Level 12 cell ~ 3.3 km^2 (good for surge pricing zones)
  - Level 14 cell ~ 0.2 km^2 (good for driver proximity)
  - Cell IDs are 64-bit integers - fast indexing and range queries
```

---

## 7. High-Level Architecture

### 7.1 System Architecture Overview

```
┌─────────────┐  ┌─────────────┐  ┌─────────────┐
│  Rider App  │  │ Driver App  │  │  Admin UI   │
│  (iOS/And)  │  │  (iOS/And)  │  │   (Web)     │
└──────┬──────┘  └──────┬──────┘  └──────┬──────┘
       │                │                │
       │     WebSocket  │  WebSocket     │  HTTPS
       │     + HTTPS    │  + HTTPS       │
       ▼                ▼                ▼
┌─────────────────────────────────────────────────────────────────┐
│                     CDN + Global Load Balancer                  │
│                   (CloudFront / Cloud LB)                       │
└───────────────────────────┬─────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│                        API Gateway                              │
│              (Auth, Rate Limiting, Routing)                     │
│         Protocol: REST for CRUD, WebSocket for real-time        │
└──────┬─────────┬──────────┬──────────┬──────────┬───────────────┘
       │         │          │          │          │
       ▼         ▼          ▼          ▼          ▼
┌──────────┐┌──────────┐┌──────────┐┌──────────┐┌──────────┐
│   Ride   ││ Location ││ Matching ││ Pricing  ││ Payment  │
│ Service  ││ Service  ││ Service  ││ Service  ││ Service  │
│          ││          ││(Dispatch)││ (Surge)  ││          │
└────┬─────┘└────┬─────┘└────┬─────┘└────┬─────┘└────┬─────┘
     │           │           │           │           │
     │           │           │           │           │
     ▼           ▼           ▼           ▼           ▼
┌──────────┐┌──────────┐┌──────────┐┌──────────┐┌──────────┐
│Notificat.││   ETA    ││  Route   ││ Analytics││  Rating  │
│ Service  ││ Service  ││ Service  ││ Service  ││ Service  │
│(Push/SMS)││          ││(Maps API)││          ││          │
└────┬─────┘└────┬─────┘└────┬─────┘└────┬─────┘└────┬─────┘
     │           │           │           │           │
     ▼           ▼           ▼           ▼           ▼
┌─────────────────────────────────────────────────────────────────┐
│                      Data Layer                                 │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐          │
│  │PostgreSQL│ │  Redis   │ │Cassandra │ │  Kafka   │          │
│  │(Trips,   │ │(Location,│ │(Trip     │ │(Events,  │          │
│  │ Users,   │ │ Surge,   │ │ History, │ │ Location │          │
│  │ Payments)│ │ Cache)   │ │ Logs)    │ │ Stream)  │          │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘          │
└─────────────────────────────────────────────────────────────────┘
```

### 7.2 Ride Request and Dispatch Flow

```
┌───────┐          ┌───────────┐       ┌──────────┐       ┌──────────┐
│ Rider │          │   Ride    │       │ Pricing  │       │ Matching │
│  App  │          │  Service  │       │ Service  │       │ Service  │
└───┬───┘          └─────┬─────┘       └────┬─────┘       └────┬─────┘
    │                    │                  │                   │
    │  1. Request Ride   │                  │                   │
    │  (pickup, dropoff) │                  │                   │
    │───────────────────>│                  │                   │
    │                    │                  │                   │
    │                    │ 2. Get Fare      │                   │
    │                    │ Estimate + Surge │                   │
    │                    │─────────────────>│                   │
    │                    │                  │                   │
    │                    │ 3. {fare, surge} │                   │
    │                    │<─────────────────│                   │
    │                    │                  │                   │
    │  4. Show Estimate  │                  │                   │
    │<───────────────────│                  │                   │
    │                    │                  │                   │
    │  5. Confirm Ride   │                  │                   │
    │───────────────────>│                  │                   │
    │                    │                  │                   │
    │                    │ 6. Find Nearby   │                   │
    │                    │ Drivers & Rank   │                   │
    │                    │────────────────────────────────────> │
    │                    │                  │                   │
    │                    │                  │     ┌──────────┐  │
    │                    │                  │     │ Location │  │
    │                    │                  │     │ Service  │  │
    │                    │                  │     └────┬─────┘  │
    │                    │                  │          │        │
    │                    │                  │  7. GEORADIUS     │
    │                    │                  │  nearby drivers   │
    │                    │                  │<─────────┤        │
    │                    │                  │          │        │
    │                    │ 8. Ranked driver │          │        │
    │                    │ list             │          │        │
    │                    │<────────────────────────────────────│
    │                    │                  │                   │
    │                    │                  │                   │

┌───────┐          ┌──────────┐       ┌──────────┐       ┌──────────┐
│ Rider │          │   Ride   │       │  Driver  │       │  Notif.  │
│  App  │          │ Service  │       │   App    │       │ Service  │
└───┬───┘          └────┬─────┘       └────┬─────┘       └────┬─────┘
    │                   │                  │                   │
    │                   │  9. Push ride    │                   │
    │                   │  request to      │                   │
    │                   │  top driver      │                   │
    │                   │─────────────────────────────────────>│
    │                   │                  │                   │
    │                   │                  │ 10. Notify driver │
    │                   │                  │<──────────────────│
    │                   │                  │                   │
    │                   │ 11. Driver       │                   │
    │                   │ accepts/declines │                   │
    │                   │<─────────────────│                   │
    │                   │                  │                   │
    │  12. Driver       │  (if accept)     │                   │
    │  assigned!        │                  │                   │
    │<──────────────────│                  │                   │
    │                   │                  │                   │
    │                   │  (if decline or  │                   │
    │                   │   timeout 15s)   │                   │
    │                   │  -> Try next     │                   │
    │                   │  ranked driver   │                   │
    │                   │                  │                   │
```

### 7.3 Component Breakdown

| Component           | Responsibility                                    | Tech Stack                |
|---------------------|---------------------------------------------------|---------------------------|
| **Ride Service**    | Trip lifecycle (CRUD), state machine               | Go/Java, PostgreSQL       |
| **Location Service**| Ingest driver GPS, geospatial queries              | Go, Redis GeoSet, Kafka   |
| **Matching Service**| Find best driver, dispatch, handle retries         | Go/Java, in-memory ranking|
| **Pricing Service** | Fare calculation, surge multiplier, estimates      | Python/Go, Redis          |
| **Payment Service** | Authorization, capture, refund, driver payout      | Java, PostgreSQL, Stripe  |
| **ETA Service**     | Time estimate using road network + traffic         | Go, Maps API, ML models   |
| **Route Service**   | Path computation, turn-by-turn directions          | Go, OSRM / Google Maps    |
| **Notification Svc**| Push notifications, SMS, in-app messages           | Go, FCM/APNs, Twilio      |
| **Rating Service**  | Store ratings, update averages                     | Go, PostgreSQL            |
| **Analytics Service**| Real-time dashboards, supply-demand heatmaps      | Spark, Flink, Elasticsearch|

---

## 8. Deep Dive: Core Components

### 8.1 Location Service and Geospatial Indexing

The Location Service is the most write-heavy component in the system, handling
**1.25 million location updates per second** from online drivers.

#### Architecture

```
┌──────────┐     ┌──────────┐     ┌──────────┐     ┌──────────┐
│ Driver   │     │ Driver   │     │ Driver   │     │ Driver   │
│  App 1   │     │  App 2   │     │  App 3   │     │  App N   │
└────┬─────┘     └────┬─────┘     └────┬─────┘     └────┬─────┘
     │                │                │                │
     │   UDP / WebSocket (batched updates every 12-15s) │
     └────────────────┼────────────────┼────────────────┘
                      │                │
                      ▼                ▼
         ┌────────────────────────────────────────┐
         │        Location Ingestion Layer        │
         │     (Stateless Go services, 50 pods)   │
         │  - Validate coordinates                │
         │  - Deduplicate                         │
         │  - Fan-out to Redis + Kafka            │
         └──────────┬────────────┬────────────────┘
                    │            │
              ┌─────┘            └─────┐
              ▼                        ▼
   ┌──────────────────┐    ┌───────────────────┐
   │   Redis Cluster  │    │   Apache Kafka    │
   │  (16 shards)     │    │  (location-stream │
   │                  │    │   topic, 128      │
   │  GeoSet per      │    │   partitions)     │
   │  city + vehicle  │    │                   │
   │                  │    │  Consumers:       │
   │  GEOADD + TTL    │    │  - S3 archival    │
   │  (expire after   │    │  - Analytics      │
   │   30 seconds)    │    │  - Trip tracking  │
   └──────────────────┘    └───────────────────┘
```

#### GeoHash vs QuadTree vs S2 Geometry

```
┌──────────────┬───────────────┬───────────────┬───────────────┐
│ Criteria     │   GeoHash     │   QuadTree    │  S2 Geometry  │
├──────────────┼───────────────┼───────────────┼───────────────┤
│ How it works │ Encode lat/lng│ Recursive     │ Project sphere│
│              │ into string,  │ subdivision   │ onto cube,    │
│              │ prefix = area │ of 2D space   │ Hilbert curve │
│              │               │ into quadrants│ cell IDs      │
├──────────────┼───────────────┼───────────────┼───────────────┤
│ Precision    │ Fixed levels  │ Adaptive      │ 30 levels,    │
│              │ (1-12 chars)  │ (split/merge  │ from 85 km^2  │
│              │               │ based on      │ to < 1 cm^2   │
│              │               │ density)      │               │
├──────────────┼───────────────┼───────────────┼───────────────┤
│ Edge problem │ Adjacent cells│ None (tree    │ None (Hilbert │
│              │ may have very │ traversal)    │ curve ensures │
│              │ different     │               │ spatial       │
│              │ prefixes      │               │ locality)     │
├──────────────┼───────────────┼───────────────┼───────────────┤
│ Query perf   │ O(1) per cell │ O(log N)      │ O(1) cell     │
│              │ lookup, need  │ traversal     │ lookup, range │
│              │ multi-cell    │               │ scan for      │
│              │ for radius    │               │ neighbors     │
├──────────────┼───────────────┼───────────────┼───────────────┤
│ Redis support│ Built-in      │ Custom        │ Custom        │
│              │ GEOADD/       │ implementation│ implementation│
│              │ GEORADIUS     │               │               │
├──────────────┼───────────────┼───────────────┼───────────────┤
│ Used by      │ Redis, many   │ Uber (H3 is  │ Google Maps,  │
│              │ startups      │ hex variant)  │ Foursquare    │
├──────────────┼───────────────┼───────────────┼───────────────┤
│ Best for     │ Simple radius │ Dynamic       │ Global-scale, │
│              │ queries, quick│ density       │ covering      │
│              │ MVP           │ handling      │ queries       │
└──────────────┴───────────────┴───────────────┴───────────────┘

Recommendation: Use Redis GeoHash for real-time driver queries (simple,
built-in, performant). Layer H3/S2 cells for surge pricing zones and
analytics where uniform cell sizing matters.
```

#### Finding Drivers Within 5 km Radius

```
Step 1: Rider requests ride at (37.7749, -122.4194)

Step 2: Location Service executes:
        GEORADIUS drivers:sf:sedan -122.4194 37.7749 5 km
                 WITHCOORD WITHDIST COUNT 20 ASC

Step 3: Redis returns up to 20 nearest drivers within 5 km:
        [
          { driver_id: "d1", dist: 0.8 km, lat: 37.776, lng: -122.420 },
          { driver_id: "d5", dist: 1.2 km, lat: 37.772, lng: -122.415 },
          { driver_id: "d3", dist: 2.1 km, lat: 37.780, lng: -122.425 },
          ...
        ]

Step 4: Filter out drivers who are:
        - Currently on a trip (check drivers table: current_ride_id != NULL)
        - Have low acceptance rate (< 60%)
        - Vehicle type mismatch

Step 5: For remaining candidates, compute ETA via road network
        (GEORADIUS gives straight-line distance; actual ETA needs routing)

Step 6: Rank by: ETA (50%), rating (30%), acceptance_rate (20%)
```

#### Handling 1.25M Location Updates/sec

```
Strategy: Batching + Sharding + Pipelining

1. Client-Side Batching:
   - Driver app collects GPS samples every 3-4 seconds
   - Batches 3-5 samples (12-15 seconds of data)
   - Sends batch in single request
   - Reduces network calls by 4x -> 312K requests/sec

2. Redis Sharding:
   - 16-shard Redis cluster
   - Shard key: city_id (drivers in same city on same shard)
   - Per shard: ~78K updates/sec (well within Redis capacity)

3. Redis Pipelining:
   - Location ingestion service pipelines 100-500 GEOADD commands
   - Single round-trip for batch of updates
   - Redis single-threaded but handles 100K+ ops/sec per instance

4. Write-Behind to Kafka:
   - Fire-and-forget to Kafka for archival
   - Kafka handles 1M+ messages/sec easily

5. TTL-Based Expiry:
   - GEOADD does not support TTL natively
   - Use separate EXPIRE key per driver or background cleanup job
   - Drivers not updating for 30 seconds are removed from GeoSet
```

### 8.2 Matching / Dispatch Algorithm

The Matching Service is the brain of the ride-sharing platform. It finds the
optimal driver for each ride request.

#### Dispatch Flow

```
┌───────────────────────────────────────────────────────────────────────┐
│                        DISPATCH ALGORITHM                            │
├───────────────────────────────────────────────────────────────────────┤
│                                                                       │
│  1. NEARBY SEARCH                                                     │
│  ┌─────────────────────────────┐                                      │
│  │ GEORADIUS(pickup, 3 km)     │──> Found 0 drivers?                  │
│  │ Get up to 30 candidates     │    ├─ Yes: Expand to 5 km            │
│  └─────────────────────────────┘    │       Expand to 8 km            │
│                                      │       Still 0? -> No drivers   │
│                                      └─ No: Continue                  │
│                                                                       │
│  2. FILTER                                                            │
│  ┌─────────────────────────────┐                                      │
│  │ Remove:                     │                                      │
│  │  - Drivers on active trips  │                                      │
│  │  - Wrong vehicle type       │                                      │
│  │  - Drivers who declined     │                                      │
│  │    this rider recently      │                                      │
│  │  - Suspended drivers        │                                      │
│  └─────────────────────────────┘                                      │
│                                                                       │
│  3. RANK (Scoring Function)                                           │
│  ┌─────────────────────────────┐                                      │
│  │ Score = w1*ETA_score         │   w1 = 0.50 (ETA weight)            │
│  │       + w2*Rating_score      │   w2 = 0.25 (rating weight)         │
│  │       + w3*Acceptance_score  │   w3 = 0.15 (acceptance rate)       │
│  │       + w4*Earnings_score    │   w4 = 0.10 (fairness: prefer      │
│  │                              │         drivers with fewer trips)   │
│  │ ETA_score = 1 - (eta / max_eta)                                   │
│  │ Rating_score = (rating - 4.0) / 1.0                               │
│  │ Acceptance_score = acceptance_rate / 100                           │
│  └─────────────────────────────┘                                      │
│                                                                       │
│  4. DISPATCH (Sequential Offer)                                       │
│  ┌─────────────────────────────┐                                      │
│  │ For each driver by rank:    │                                      │
│  │  - Send ride offer via push │                                      │
│  │  - Wait 15 sec for response │                                      │
│  │  - If ACCEPT -> Match!      │                                      │
│  │  - If DECLINE or TIMEOUT    │                                      │
│  │    -> Try next driver       │                                      │
│  │  - After 3 failures:        │                                      │
│  │    -> Expand radius, re-rank│                                      │
│  │  - After 5 total failures:  │                                      │
│  │    -> "No drivers available" │                                     │
│  └─────────────────────────────┘                                      │
│                                                                       │
└───────────────────────────────────────────────────────────────────────┘
```

#### Broadcast vs Sequential Dispatch

```
┌────────────────────┬────────────────────────┬────────────────────────┐
│                    │  Sequential (Uber)     │  Broadcast (early Lyft)│
├────────────────────┼────────────────────────┼────────────────────────┤
│ How it works       │ Offer to one driver at │ Offer to multiple      │
│                    │ a time, wait for       │ drivers simultaneously,│
│                    │ response               │ first to accept wins   │
├────────────────────┼────────────────────────┼────────────────────────┤
│ Matching time      │ Slower (15s per attempt│ Faster (parallel)      │
│                    │ worst case)            │                        │
├────────────────────┼────────────────────────┼────────────────────────┤
│ Driver experience  │ Better (guaranteed if  │ Worse (race condition, │
│                    │ you accept)            │ frustrating to lose)   │
├────────────────────┼────────────────────────┼────────────────────────┤
│ Optimal match      │ Better (can send to    │ Worse (closest driver  │
│                    │ best-fit driver)       │ may not be best fit)   │
├────────────────────┼────────────────────────┼────────────────────────┤
│ Recommendation     │ Use sequential with    │ Use broadcast only     │
│                    │ smart ranking          │ during extreme surge   │
└────────────────────┴────────────────────────┴────────────────────────┘
```

#### Supply-Demand Balancing

```
For each H3 cell (hexagonal geo-cell, ~1 km^2):

  Supply = count of online, available drivers in cell
  Demand = count of ride requests in cell in last 5 minutes

  If Demand > Supply * 1.5:
    -> Trigger surge pricing in this cell
    -> Send "high demand" notification to nearby drivers
    -> Nudge drivers to reposition toward this cell

  If Supply > Demand * 3:
    -> Reduce surge to 1.0x
    -> Send "low demand" notification

  Rebalancing: Show "demand heatmap" to drivers so they can
  voluntarily reposition to high-demand areas.
```

### 8.3 Dynamic Pricing (Surge)

#### Surge Multiplier Calculation

```
┌─────────────────────────────────────────────────────────────────┐
│                 SURGE PRICING PIPELINE                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Input: Per geo-cell (H3 resolution 8, ~0.74 km^2)             │
│                                                                 │
│  1. Compute Supply-Demand Ratio                                 │
│     ┌──────────────────────────────────────────┐                │
│     │ supply = active_drivers_in_cell           │                │
│     │ demand = requests_last_5_min_in_cell      │                │
│     │ ratio  = demand / max(supply, 1)          │                │
│     └──────────────────────────────────────────┘                │
│                                                                 │
│  2. Map Ratio to Multiplier                                     │
│     ┌──────────────────────────────────────────┐                │
│     │ ratio < 1.0  -> surge = 1.0x (no surge)  │                │
│     │ ratio 1.0-2.0 -> surge = 1.0 + 0.3*(r-1) │               │
│     │ ratio 2.0-3.0 -> surge = 1.3 + 0.5*(r-2) │               │
│     │ ratio 3.0-5.0 -> surge = 1.8 + 0.4*(r-3) │               │
│     │ ratio > 5.0  -> surge = cap at 3.0x       │               │
│     └──────────────────────────────────────────┘                │
│                                                                 │
│  3. Smoothing                                                   │
│     ┌──────────────────────────────────────────┐                │
│     │ Use exponential moving average to prevent │                │
│     │ surge from spiking/dropping instantly:    │                │
│     │                                           │                │
│     │ new_surge = 0.7 * current_surge           │                │
│     │           + 0.3 * calculated_surge        │                │
│     │                                           │                │
│     │ Update every 60 seconds per cell          │                │
│     └──────────────────────────────────────────┘                │
│                                                                 │
│  4. Store in Redis                                              │
│     ┌──────────────────────────────────────────┐                │
│     │ SET surge:cell:<h3_cell_id> 1.5 EX 120   │                │
│     │ (auto-expire after 2 min if not refreshed)│               │
│     └──────────────────────────────────────────┘                │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

#### Fare Calculation

```
fare = base_fare
     + (distance_km * per_km_rate)
     + (duration_min * per_min_rate)
     + booking_fee
     + tolls

surged_fare = fare * surge_multiplier

final_fare = max(surged_fare, minimum_fare)

Example (UberX in San Francisco):
  base_fare    = $2.55
  per_km_rate  = $1.15
  per_min_rate = $0.22
  booking_fee  = $2.75
  surge        = 1.5x

  Trip: 8.5 km, 18 min
  fare = 2.55 + (8.5 * 1.15) + (18 * 0.22) + 2.75 = $19.03
  surged = $19.03 * 1.5 = $28.55
```

#### Price Transparency and Capping

```
Rider Experience:
  1. Before confirming ride, show:
     "Prices are higher due to increased demand"
     "Surge: 1.5x  |  Estimated fare: $25-$30"

  2. Require explicit confirmation for surge > 2.0x:
     "Type the surge multiplier (2.3) to confirm"

  3. Hard cap at 3.0x to prevent public backlash

  4. Show fare range (min-max) not exact number for better UX

Business Rules:
  - No surge during natural disasters (regulatory compliance)
  - Gradual ramp-up: surge changes by at most 0.5x per minute
  - Notify riders when surge drops: "Prices are back to normal"
```

### 8.4 ETA Calculation

#### ETA Service Architecture

```
┌──────────────────────────────────────────────────────────────────┐
│                      ETA SERVICE                                 │
├──────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Input: origin (lat, lng), destination (lat, lng)                │
│  Output: estimated_time_minutes, estimated_distance_km           │
│                                                                  │
│  ┌──────────────────────────────────────────────────────┐        │
│  │            Layer 1: Road Network Graph               │        │
│  │                                                      │        │
│  │  - OpenStreetMap data loaded into memory              │        │
│  │  - Nodes: intersections (~50M globally)               │        │
│  │  - Edges: road segments with:                         │        │
│  │    - Distance (meters)                                │        │
│  │    - Speed limit                                      │        │
│  │    - Road type (highway, local, one-way)              │        │
│  │    - Number of lanes                                  │        │
│  │  - Contraction Hierarchies for fast shortest path     │        │
│  └──────────────────────────────────────────────────────┘        │
│                         │                                        │
│                         ▼                                        │
│  ┌──────────────────────────────────────────────────────┐        │
│  │         Layer 2: Real-Time Traffic Overlay           │        │
│  │                                                      │        │
│  │  - Aggregate speed data from driver GPS traces       │        │
│  │  - Per road segment: current_speed vs free_flow_speed│        │
│  │  - Update edge weights every 2-5 minutes             │        │
│  │  - Traffic factor = free_flow_speed / current_speed  │        │
│  └──────────────────────────────────────────────────────┘        │
│                         │                                        │
│                         ▼                                        │
│  ┌──────────────────────────────────────────────────────┐        │
│  │           Layer 3: ML Correction Model               │        │
│  │                                                      │        │
│  │  - Trained on (predicted_ETA, actual_trip_duration)   │        │
│  │  - Features: time_of_day, day_of_week, weather,      │        │
│  │    origin_zone, destination_zone, road_type_mix       │        │
│  │  - Corrects systematic biases in graph-based ETA     │        │
│  │  - Reduces median error from 25% to ~11%             │        │
│  └──────────────────────────────────────────────────────┘        │
│                                                                  │
│  Algorithms:                                                     │
│  - Dijkstra's: O(E log V), good for single-source               │
│  - A*: O(E log V) with heuristic, faster in practice             │
│  - Contraction Hierarchies: O(log^2 V) query time after          │
│    O(V * E * log V) preprocessing. Used by OSRM.                 │
│    10,000x faster than Dijkstra for continental-scale graphs.    │
│                                                                  │
└──────────────────────────────────────────────────────────────────┘
```

#### ETA Caching

```
Popular Route Caching:
  - Pre-compute ETAs for top 10K origin-destination pairs per city
  - Cache in Redis with 5-minute TTL
  - Key: eta:<origin_h3_cell>:<dest_h3_cell>:<time_bucket>
  - Covers ~40% of all ETA requests from cache

Cell-to-Cell ETA Matrix:
  - For each city, maintain N x N matrix where N = number of H3 cells
  - San Francisco: ~800 cells -> 640K entries
  - Update every 5 minutes using traffic data
  - Lookup: O(1) from matrix -> sub-millisecond
```

---

## 9. Data Partitioning and Sharding

### 9.1 Sharding Strategy by Data Type

```
┌─────────────────────────────────────────────────────────────────────┐
│                     SHARDING STRATEGY                               │
├──────────────┬──────────────┬───────────────────────────────────────┤
│  Data Type   │  Shard Key   │  Rationale                           │
├──────────────┼──────────────┼───────────────────────────────────────┤
│ Driver       │ city_id      │ Drivers operate in one city; all     │
│ Locations    │ (Redis)      │ location queries are city-scoped.    │
│              │              │ GeoSet per city+vehicle type.        │
│              │              │                                       │
│              │              │ Key: drivers:<city>:<vehicle_type>    │
│              │              │ Shards: ~200 (one per major city)    │
├──────────────┼──────────────┼───────────────────────────────────────┤
│ Trips        │ city_id +    │ Queries mostly by city and date      │
│ (Active)     │ date         │ range. Active trips queried by       │
│              │              │ city. Historical trips by date.      │
│              │              │                                       │
│              │              │ PostgreSQL: partition by city_id     │
│              │              │ Sub-partition by month for history   │
├──────────────┼──────────────┼───────────────────────────────────────┤
│ Trip History │ city_id      │ Cassandra partition key: (city_id,   │
│ (Archival)   │ + year_month │ year_month). Clustering key: trip_id │
│              │              │ Even distribution across nodes.      │
├──────────────┼──────────────┼───────────────────────────────────────┤
│ Users        │ user_id      │ Hash-based sharding on user_id.     │
│              │ (hash)       │ Queries are always by specific user. │
│              │              │ Consistent hashing for rebalancing.  │
├──────────────┼──────────────┼───────────────────────────────────────┤
│ Payments     │ user_id      │ Co-locate with user data for joins.  │
│              │ (hash)       │ Payment queries always include       │
│              │              │ rider_id or driver_id.               │
├──────────────┼──────────────┼───────────────────────────────────────┤
│ Surge        │ h3_cell_id   │ Natural geographic distribution.     │
│ Pricing      │              │ Each cell's surge is independent.    │
│              │              │ Fits entirely in Redis.              │
└──────────────┴──────────────┴───────────────────────────────────────┘
```

### 9.2 Cross-Shard Query Handling

```
Problem: A rider in City A requests a ride near the boundary of City B.
         Drivers in City B are on a different shard.

Solution: Boundary Zone Overlap
  - Define overlap zones (5 km buffer) around city boundaries
  - Drivers within 5 km of a boundary are indexed in BOTH city GeoSets
  - Location Service writes to both: drivers:cityA:sedan AND drivers:cityB:sedan
  - Matching Service queries only the rider's city shard
  - Overlap zone doubles writes for ~5% of drivers but avoids cross-shard reads

Alternative: Global Driver Index
  - Single global Redis GeoSet with ALL drivers (simpler but doesn't scale)
  - Only viable up to ~500K drivers, not at 5M scale
```

---

## 10. Caching Strategy

### 10.1 Cache Layers

```
┌─────────────────────────────────────────────────────────────────┐
│                      CACHING ARCHITECTURE                       │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Layer 1: Client-Side Cache (Mobile App)                        │
│  ┌─────────────────────────────────────────────────────┐        │
│  │ - Map tiles: cached for offline use                  │        │
│  │ - Last known driver locations: 5 sec stale OK        │        │
│  │ - Fare estimates: cached for same pickup/dropoff     │        │
│  │ - User profile: cached until update                  │        │
│  └─────────────────────────────────────────────────────┘        │
│                                                                 │
│  Layer 2: CDN Cache                                             │
│  ┌─────────────────────────────────────────────────────┐        │
│  │ - Static assets (images, map tiles)                  │        │
│  │ - City configuration (service areas, ride types)     │        │
│  │ - TTL: 1 hour for config, 24 hours for static        │        │
│  └─────────────────────────────────────────────────────┘        │
│                                                                 │
│  Layer 3: Application Cache (Redis)                             │
│  ┌─────────────────────────────────────────────────────┐        │
│  │ - Driver locations (GeoSet, TTL 30 sec)              │        │
│  │ - Surge pricing per cell (TTL 2 min)                 │        │
│  │ - ETA estimates for popular routes (TTL 5 min)       │        │
│  │ - Driver availability status (TTL 30 sec)            │        │
│  │ - Active ride state (for fast reads during tracking) │        │
│  │ - Session tokens and auth data                       │        │
│  └─────────────────────────────────────────────────────┘        │
│                                                                 │
│  Layer 4: Database Query Cache (PostgreSQL)                     │
│  ┌─────────────────────────────────────────────────────┐        │
│  │ - User profiles: read-through cache in Redis         │        │
│  │ - Trip details: cached during active ride             │        │
│  │ - Payment methods: cached per session                 │        │
│  └─────────────────────────────────────────────────────┘        │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 10.2 Cache Invalidation

```
Driver Location:
  - Self-invalidating: new GEOADD overwrites old position
  - TTL of 30 seconds: if driver stops sending updates, they disappear
  - No explicit invalidation needed

Surge Pricing:
  - Recomputed every 60 seconds by pricing pipeline
  - Stored with TTL 120 seconds (2 min)
  - If pipeline fails, surge naturally expires to 1.0x (safe default)

Active Ride State:
  - Write-through cache: every trip state change updates Redis + PostgreSQL
  - Redis key: ride:<ride_id> -> JSON of current ride state
  - TTL: 2 hours (rides rarely last longer)
  - Explicitly deleted on ride completion

User Profiles:
  - Cache-aside pattern
  - TTL: 15 minutes
  - Explicit invalidation on profile update via pub/sub
```

---

## 11. Replication and Consistency

### 11.1 Consistency Model per Data Type

```
┌──────────────────┬────────────────┬────────────────────────────────────┐
│ Data Type        │ Consistency    │ Justification                      │
├──────────────────┼────────────────┼────────────────────────────────────┤
│ Driver Locations │ Eventually     │ Stale by 3-4 sec is acceptable.    │
│                  │ Consistent     │ Driver moves; next update corrects.│
│                  │                │ No need for strong consistency.    │
├──────────────────┼────────────────┼────────────────────────────────────┤
│ Trip State       │ Strongly       │ State transitions must be atomic:  │
│ (status field)   │ Consistent     │ MATCHING->ACCEPTED->IN_PROGRESS.  │
│                  │                │ Race conditions could cause double │
│                  │                │ dispatch or lost rides.            │
├──────────────────┼────────────────┼────────────────────────────────────┤
│ Payments         │ Strongly       │ Financial data requires ACID.      │
│                  │ Consistent     │ Double-charge is unacceptable.     │
│                  │                │ Use PostgreSQL with serializable   │
│                  │                │ isolation for payment operations.  │
├──────────────────┼────────────────┼────────────────────────────────────┤
│ Surge Pricing    │ Eventually     │ 60-second staleness is fine.       │
│                  │ Consistent     │ Surge changes gradually.           │
│                  │                │ All riders in same cell see same   │
│                  │                │ surge (read from same Redis key).  │
├──────────────────┼────────────────┼────────────────────────────────────┤
│ User Profiles    │ Read-Your-     │ User should see own updates        │
│                  │ Writes         │ immediately. Other users can see   │
│                  │                │ stale data briefly.                │
├──────────────────┼────────────────┼────────────────────────────────────┤
│ Ratings          │ Eventually     │ Small delay in average update is   │
│                  │ Consistent     │ acceptable. Batch recalculation.   │
└──────────────────┴────────────────┴────────────────────────────────────┘
```

### 11.2 Replication Topology

```
PostgreSQL (Trips, Users, Payments):
  ┌──────────┐     Sync Replication     ┌──────────┐
  │ Primary  │ ────────────────────────> │ Standby  │ (same AZ, sync)
  │ (us-west)│                           │ (us-west)│
  └──────────┘                           └──────────┘
       │
       │  Async Replication
       ▼
  ┌──────────┐
  │ Read     │ (different AZ, async, for read scaling)
  │ Replica  │
  └──────────┘

Redis (Locations, Cache):
  ┌──────────┐     ┌──────────┐     ┌──────────┐
  │ Shard 1  │     │ Shard 2  │     │ Shard 3  │
  │ Master   │     │ Master   │     │ Master   │
  └────┬─────┘     └────┬─────┘     └────┬─────┘
       │                │                │
       ▼                ▼                ▼
  ┌──────────┐     ┌──────────┐     ┌──────────┐
  │ Shard 1  │     │ Shard 2  │     │ Shard 3  │
  │ Replica  │     │ Replica  │     │ Replica  │
  └──────────┘     └──────────┘     └──────────┘

  - Redis Cluster with automatic failover
  - Replica serves read queries (GEORADIUS) to offload master
  - Master handles writes (GEOADD)

Cassandra (Trip History):
  - Replication Factor = 3
  - Consistency Level: QUORUM for writes, ONE for reads
  - Multi-datacenter replication for disaster recovery
```

### 11.3 Trip State Machine with Consistency

```
                    ┌───────────────────────────────┐
                    │         REQUESTED             │
                    │  (rider submitted request)    │
                    └──────────────┬────────────────┘
                                   │
                    ┌──────────────▼────────────────┐
                    │          MATCHING             │
                    │  (searching for driver)       │
                    └──────┬───────────┬────────────┘
                           │           │
              ┌────────────▼──┐  ┌─────▼────────────┐
              │   ACCEPTED    │  │  NO_DRIVERS       │
              │ (driver found)│  │  (matching failed)│
              └──────┬────────┘  └──────────────────┘
                     │
              ┌──────▼────────┐
              │   ARRIVING    │
              │(driver en     │
              │ route to      │
              │ pickup)       │
              └──────┬────────┘
                     │
              ┌──────▼────────┐
              │  IN_PROGRESS  │
              │ (trip started,│
              │  meter on)    │
              └──────┬────────┘
                     │
              ┌──────▼────────┐
              │  COMPLETED    │
              │ (arrived at   │
              │  dropoff)     │
              └──────┬────────┘
                     │
              ┌──────▼────────┐
              │    PAID       │
              │ (payment      │
              │  processed)   │
              └───────────────┘

    CANCELLED can occur from: REQUESTED, MATCHING, ACCEPTED, ARRIVING

    State Transition Enforcement:
    - Use PostgreSQL advisory locks or optimistic locking (version column)
    - UPDATE trips SET status = 'ACCEPTED', version = version + 1
      WHERE trip_id = ? AND status = 'MATCHING' AND version = ?
    - If affected_rows = 0 -> concurrent modification, retry or reject
```

---

## 12. Fault Tolerance and Failure Handling

### 12.1 Failure Scenarios and Mitigations

```
┌──────────────────────────┬────────────────────────────────────────────┐
│ Failure Scenario         │ Mitigation                                 │
├──────────────────────────┼────────────────────────────────────────────┤
│ Matching timeout         │ Retry with expanded radius (3km -> 5km    │
│ (no driver responds)     │ -> 8km). After 3 expansions, notify rider │
│                          │ "No drivers available" with retry option. │
├──────────────────────────┼────────────────────────────────────────────┤
│ Driver app disconnects   │ If no location update for 30 sec, mark   │
│ mid-ride                 │ driver as disconnected. Hold trip in      │
│                          │ IN_PROGRESS state. If > 5 min, notify    │
│                          │ rider, offer to cancel or wait. Use last │
│                          │ known location for partial fare calc.    │
├──────────────────────────┼────────────────────────────────────────────┤
│ Payment processing       │ Pre-authorize card before matching. If   │
│ failure                  │ capture fails at ride end: retry 3x with │
│                          │ exponential backoff. Queue for manual     │
│                          │ review. Still pay driver from platform    │
│                          │ float.                                   │
├──────────────────────────┼────────────────────────────────────────────┤
│ Location Service down    │ Redis cluster failover (< 15 sec). During│
│ (Redis failure)          │ outage, use last known positions (stale   │
│                          │ by seconds). Active rides use WebSocket   │
│                          │ direct connection as fallback.            │
├──────────────────────────┼────────────────────────────────────────────┤
│ Ride Service crash       │ Stateless service; restart on any node.   │
│                          │ Trip state in PostgreSQL survives crash.  │
│                          │ Kubernetes restarts pod in < 10 sec.     │
├──────────────────────────┼────────────────────────────────────────────┤
│ Double dispatch          │ Optimistic locking on trip.status.        │
│ (two drivers assigned)   │ Only one UPDATE can succeed (MATCHING ->  │
│                          │ ACCEPTED). Losing driver gets "ride no    │
│                          │ longer available" response.               │
├──────────────────────────┼────────────────────────────────────────────┤
│ Kafka consumer lag       │ Location archival is async; lag is OK.    │
│                          │ Monitor consumer lag. Scale consumers.    │
│                          │ Real-time queries use Redis, not Kafka.  │
├──────────────────────────┼────────────────────────────────────────────┤
│ Network partition        │ City-level isolation: partition in one    │
│ between regions          │ city doesn't affect other cities.         │
│                          │ Each city can operate independently.     │
├──────────────────────────┼────────────────────────────────────────────┤
│ Surge pricing service    │ Default to 1.0x (no surge) if service is │
│ down                     │ unavailable. Redis TTL ensures stale     │
│                          │ surge expires. Riders get normal pricing. │
├──────────────────────────┼────────────────────────────────────────────┤
│ GPS drift / inaccuracy   │ Kalman filter on driver app to smooth    │
│                          │ GPS readings. Reject updates with        │
│                          │ accuracy > 50m. Snap-to-road algorithm   │
│                          │ to place driver on nearest road.         │
└──────────────────────────┴────────────────────────────────────────────┘
```

### 12.2 Circuit Breaker Pattern

```
┌────────────────────────────────────────────────────────────────┐
│                 CIRCUIT BREAKER: Payment Service               │
├────────────────────────────────────────────────────────────────┤
│                                                                │
│  States:                                                       │
│                                                                │
│  CLOSED (normal) ──> OPEN (failing) ──> HALF-OPEN (testing)   │
│       ▲                                       │                │
│       └───────────────────────────────────────┘                │
│                                                                │
│  CLOSED -> OPEN:                                               │
│    When 5 failures in 60 seconds to Stripe API                 │
│    Action: Stop sending requests, return "payment pending"     │
│                                                                │
│  OPEN -> HALF-OPEN:                                            │
│    After 30 seconds cooldown, allow 1 test request             │
│                                                                │
│  HALF-OPEN -> CLOSED:                                          │
│    Test request succeeds -> resume normal operation             │
│                                                                │
│  HALF-OPEN -> OPEN:                                            │
│    Test request fails -> back to OPEN, wait another 30 sec     │
│                                                                │
│  During OPEN state:                                            │
│    - Complete ride, record fare                                │
│    - Queue payment for later processing                        │
│    - Notify rider: "Payment will be charged shortly"           │
│    - Process queued payments when circuit closes               │
│                                                                │
└────────────────────────────────────────────────────────────────┘
```

---

## 13. Scalability

### 13.1 Scaling Strategy

```
┌─────────────────────────────────────────────────────────────────┐
│                   SCALABILITY ARCHITECTURE                      │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Dimension 1: Horizontal Service Scaling                        │
│  ┌─────────────────────────────────────────────────────┐        │
│  │ All services are stateless (state in DB/Redis)      │        │
│  │ Kubernetes HPA: auto-scale on CPU/request rate      │        │
│  │                                                     │        │
│  │ Service          Baseline    Peak (NYE)             │        │
│  │ ────────────────────────────────────────             │        │
│  │ Ride Service     50 pods     500 pods               │        │
│  │ Location Service 100 pods    300 pods               │        │
│  │ Matching Service 30 pods     200 pods               │        │
│  │ Pricing Service  20 pods     100 pods               │        │
│  │ Payment Service  30 pods     150 pods               │        │
│  │ Notification Svc 40 pods     200 pods               │        │
│  └─────────────────────────────────────────────────────┘        │
│                                                                 │
│  Dimension 2: Data Layer Scaling                                │
│  ┌─────────────────────────────────────────────────────┐        │
│  │ PostgreSQL:                                         │        │
│  │  - Vertical scaling to 64-core, 512GB RAM           │        │
│  │  - Read replicas for read-heavy queries             │        │
│  │  - Partitioning by city_id for trips table          │        │
│  │  - Connection pooling via PgBouncer (10K+ conns)    │        │
│  │                                                     │        │
│  │ Redis:                                              │        │
│  │  - Cluster mode: 16 shards -> 64 shards             │        │
│  │  - Each shard: 64GB RAM, handles 100K ops/sec       │        │
│  │  - Total cluster: 1.6M+ ops/sec capacity            │        │
│  │                                                     │        │
│  │ Cassandra:                                          │        │
│  │  - Add nodes for storage growth                      │        │
│  │  - Rebalance with vnodes                             │        │
│  │  - Target: 3-5 TB per node                           │        │
│  │                                                     │        │
│  │ Kafka:                                              │        │
│  │  - 128 partitions for location topic                 │        │
│  │  - Add brokers for throughput                        │        │
│  │  - Target: 2M messages/sec per cluster               │        │
│  └─────────────────────────────────────────────────────┘        │
│                                                                 │
│  Dimension 3: Geographic Isolation                              │
│  ┌─────────────────────────────────────────────────────┐        │
│  │ City-level isolation for blast radius containment   │        │
│  │                                                     │        │
│  │ Each city cluster:                                  │        │
│  │  - Own Redis GeoSet shard                            │        │
│  │  - Own PostgreSQL partition                          │        │
│  │  - Own surge pricing computation                     │        │
│  │  - Can operate independently during outages          │        │
│  │                                                     │        │
│  │ Regional grouping:                                  │        │
│  │  US-West: SF, LA, Seattle, Portland                  │        │
│  │  US-East: NYC, Boston, DC, Miami                     │        │
│  │  Europe:  London, Paris, Berlin, Amsterdam           │        │
│  │  APAC:    Singapore, Mumbai, Sydney, Tokyo           │        │
│  └─────────────────────────────────────────────────────┘        │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 13.2 Handling 10x Traffic Spikes (New Year's Eve)

```
Preparation (weeks before):
  1. Pre-scale all services to 3x baseline capacity
  2. Warm up Redis with additional shards
  3. Pre-authorize Kafka topic partitions
  4. Alert on-call teams across all time zones

During spike:
  1. Auto-scaling kicks in based on request rate metrics
  2. Surge pricing activates in high-demand cells
  3. Enable "broadcast dispatch" mode (offer ride to 3 drivers simultaneously)
  4. Relax matching criteria (accept drivers up to 10 km away)
  5. Enable ride request queue: "All drivers busy, estimated wait: 8 min"

Graceful degradation order:
  1. Disable ride history queries (non-critical)
  2. Disable analytics pipeline (async, can catch up)
  3. Simplify ETA to straight-line estimate (skip road network)
  4. Increase location update interval to 8 seconds (halve write load)
  5. Last resort: limit new ride requests by city (queue with ETA)
```

---

## 14. Monitoring and Observability

### 14.1 Key Metrics Dashboard

```
┌─────────────────────────────────────────────────────────────────────┐
│                    RIDE-SHARING METRICS DASHBOARD                   │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  MATCHING METRICS                          RIDE METRICS             │
│  ┌─────────────────────────────┐  ┌─────────────────────────────┐  │
│  │ Avg Match Time:    2.4 sec  │  │ Active Rides:      847,293  │  │
│  │ P99 Match Time:    8.1 sec  │  │ Rides/min:           14,200 │  │
│  │ Match Success %:   94.7%    │  │ Completion Rate:     96.2%  │  │
│  │ No Driver Rate:    3.1%     │  │ Cancellation Rate:   3.8%   │  │
│  │ Avg Attempts:      1.3      │  │ Avg Ride Duration:   14 min │  │
│  └─────────────────────────────┘  └─────────────────────────────┘  │
│                                                                     │
│  LOCATION METRICS                          PRICING METRICS          │
│  ┌─────────────────────────────┐  ┌─────────────────────────────┐  │
│  │ Updates/sec:    1,247,000   │  │ Avg Surge:           1.12x  │  │
│  │ Update Lag P99: 120 ms      │  │ % Rides Surged:      18.4%  │  │
│  │ Stale Drivers:  0.3%        │  │ Max Surge:           2.8x   │  │
│  │ GeoQuery P99:   12 ms       │  │ Avg Fare:            $18.50 │  │
│  │ Redis Memory:   78% used    │  │ Revenue/hour:        $2.1M  │  │
│  └─────────────────────────────┘  └─────────────────────────────┘  │
│                                                                     │
│  DRIVER METRICS                            SYSTEM HEALTH            │
│  ┌─────────────────────────────┐  ┌─────────────────────────────┐  │
│  │ Online Drivers: 4,821,000   │  │ API P99 Latency:   180 ms  │  │
│  │ Busy (on trip):  847,293    │  │ Error Rate:        0.02%   │  │
│  │ Available:      3,973,707   │  │ CPU Util (avg):    42%     │  │
│  │ Avg Wait (idle): 6.2 min    │  │ Redis Hit Rate:    99.1%   │  │
│  │ Driver Churn:   2.1%/month  │  │ Kafka Consumer Lag: 1.2s   │  │
│  └─────────────────────────────┘  └─────────────────────────────┘  │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

### 14.2 Alerting Rules

```
CRITICAL (Page immediately):
  - Match success rate < 85% for 5 min
  - Location update ingestion drops > 30% suddenly
  - Payment failure rate > 5% for 2 min
  - Active rides count drops > 20% in 5 min (data loss?)
  - Redis cluster node down (failover should be automatic)
  - API error rate > 1% for 3 min

WARNING (Slack notification):
  - P99 matching time > 10 seconds
  - Surge multiplier > 2.5x in any cell for > 30 min
  - Driver churn rate > 3% in a week
  - Kafka consumer lag > 60 seconds
  - PostgreSQL replication lag > 5 seconds
  - Redis memory usage > 85%

INFO (Dashboard only):
  - New peak concurrent rides record
  - Surge activated/deactivated per city
  - Service auto-scaling events
```

### 14.3 Distributed Tracing

```
Trace: Ride Request to Completion

  [Rider App] ──POST /rides/request──>
    [API Gateway: 2ms] ──>
      [Ride Service: 5ms] ──>
        [Pricing Service: 8ms] (fare estimate + surge lookup)
        [Matching Service: 15ms] ──>
          [Location Service: 3ms] (GEORADIUS query)
          [ETA Service: 25ms] (road network calculation)
        [Notification Service: 5ms] (push to driver)

  Total E2E Latency for ride request: ~50ms server-side
  Driver notification received: ~200ms (including push network)
  Driver response (accept): 5-15 sec (human decision time)

  Trace ID propagated through all services via X-Trace-ID header.
  Stored in Jaeger/Zipkin for debugging.
```

---

## 15. Trade-offs and Design Decisions

### 15.1 Key Trade-offs

```
┌──────────────────────────────────────────────────────────────────────┐
│                        DESIGN TRADE-OFFS                             │
├─────────────────────┬──────────────────────┬─────────────────────────┤
│ Decision            │ Option A             │ Option B                │
├─────────────────────┼──────────────────────┼─────────────────────────┤
│ Geospatial Index    │ Redis GeoHash        │ Custom QuadTree/H3      │
│                     │ + Simple, built-in   │ + Adaptive density      │
│                     │ + Fast integration   │ + Better for analytics  │
│                     │ - Edge case at cell  │ - Build & maintain      │
│                     │   boundaries         │ - Higher complexity     │
│                     │ CHOSE: Redis for MVP │                         │
│                     │ + H3 for surge/      │                         │
│                     │   analytics          │                         │
├─────────────────────┼──────────────────────┼─────────────────────────┤
│ Dispatch Model      │ Sequential (one-by-  │ Broadcast (send to      │
│                     │ one offer)           │ multiple drivers)       │
│                     │ + Better match       │ + Faster matching       │
│                     │ + Driver UX          │ - Wastes driver         │
│                     │ - Slower (15s/try)   │   attention             │
│                     │ CHOSE: Sequential    │                         │
│                     │ with fast timeout    │                         │
│                     │ (10s) and broadcast  │                         │
│                     │ fallback in surge    │                         │
├─────────────────────┼──────────────────────┼─────────────────────────┤
│ Location Protocol   │ HTTP REST (poll)     │ WebSocket (push)        │
│                     │ + Simpler            │ + Lower overhead        │
│                     │ + Stateless          │ + Bidirectional         │
│                     │ - HTTP overhead per  │ - Stateful connections  │
│                     │   update (headers)   │ - Reconnection logic    │
│                     │ CHOSE: WebSocket for │                         │
│                     │ active drivers, REST │                         │
│                     │ for infrequent calls │                         │
├─────────────────────┼──────────────────────┼─────────────────────────┤
│ Pricing Model       │ Post-trip metered    │ Upfront fixed pricing   │
│                     │ (actual distance/    │ (estimate at request    │
│                     │  time)               │  time, locked in)       │
│                     │ + Accurate billing   │ + Price transparency    │
│                     │ - Rider anxiety      │ + Rider confidence      │
│                     │   about final fare   │ - Platform absorbs      │
│                     │                      │   routing risk          │
│                     │ CHOSE: Upfront with  │                         │
│                     │ adjustment for major │                         │
│                     │ route deviations     │                         │
├─────────────────────┼──────────────────────┼─────────────────────────┤
│ Trip Storage        │ Single PostgreSQL    │ PostgreSQL (active) +   │
│                     │ with partitions      │ Cassandra (historical)  │
│                     │ + Simpler ops        │ + Scale reads for       │
│                     │ + SQL joins          │   history queries       │
│                     │ - Scale ceiling      │ - Dual-write complexity │
│                     │ CHOSE: Dual-store    │                         │
│                     │ (PG for active +     │                         │
│                     │  Cassandra for cold) │                         │
├─────────────────────┼──────────────────────┼─────────────────────────┤
│ ETA Approach        │ Simple (straight-    │ Full road network       │
│                     │ line * factor)       │ with traffic            │
│                     │ + Fast, no external  │ + Accurate              │
│                     │   dependency         │ + Trusted by users      │
│                     │ - Inaccurate in      │ - Expensive to compute  │
│                     │   complex road nets  │ - Map data dependency   │
│                     │ CHOSE: Full road     │                         │
│                     │ network with fallback│                         │
│                     │ to simple method     │                         │
└─────────────────────┴──────────────────────┴─────────────────────────┘
```

### 15.2 Why Not a Single Database?

```
Why we split across PostgreSQL, Redis, and Cassandra:

PostgreSQL alone:
  - Cannot handle 1.25M geo-writes/sec (write bottleneck)
  - PostGIS is good for geo queries but not at this write volume
  - Fine for trips (20M/day = ~230 writes/sec) and users

Redis alone:
  - No ACID for trip state transitions (data loss risk)
  - No durable storage (persistence is slow / lossy)
  - Perfect for ephemeral location data with TTL

Cassandra alone:
  - No multi-key transactions (trip + payment atomicity)
  - Eventual consistency not suitable for payments
  - Great for append-only trip history (time-series pattern)

Hybrid approach gives best of each:
  PostgreSQL: Transactional data (trips, payments, users)
  Redis: Real-time ephemeral data (locations, cache, surge)
  Cassandra: High-volume historical data (trip logs, analytics)
  Kafka: Event streaming (location stream, trip events)
```

---

## 16. Interview Deep-Dive Questions

### Q1: How do you handle drivers at city boundaries?

**Answer:** We define overlap zones -- 5 km buffer areas around city boundaries.
Drivers within these zones are indexed in GeoSets for both adjacent cities.
When the Location Service receives an update from a boundary driver, it writes
to both city shards. This doubles writes for ~5% of drivers but eliminates
cross-shard reads during matching. The rider's pickup location determines which
city shard is queried. If a driver is 3 km away but in a different city shard,
the overlap zone ensures they still appear in the query results.

For country boundaries (e.g., US-Mexico border), regulatory restrictions may
prevent cross-border matching entirely, enforced via geo-fencing rules.

---

### Q2: How do you prevent surge pricing abuse?

**Answer:** Several mechanisms:

1. **Smoothing:** Surge multiplier uses exponential moving average, changing by at
   most 0.3x per computation cycle (60 sec). Prevents artificial spikes.

2. **Minimum duration:** Surge must persist for at least 3 computation cycles (3 min)
   before being displayed to riders. Brief demand spikes are absorbed.

3. **Hard cap:** Maximum surge is 3.0x. Above that, we absorb the cost differential.

4. **Driver gaming detection:** If multiple drivers go offline simultaneously in the
   same cell (colluding to create artificial shortage), flag for review. Use
   historical patterns to detect anomalies.

5. **Rider-side protection:** Riders must explicitly confirm rides above 2.0x surge.
   Show "prices are higher than normal" warning with clear multiplier.

6. **Regulatory compliance:** Disable surge during declared emergencies (natural
   disasters, severe weather events). Configurable per city.

---

### Q3: How do you handle ride cancellation mid-trip?

**Answer:** Several scenarios:

**Rider cancels mid-trip:**
- Trip status transitions to CANCELLED
- Rider is charged a partial fare based on distance/time so far
- Driver receives partial payment + cancellation compensation
- Trip route is saved up to the cancellation point
- If rider frequently cancels, their reliability score decreases

**Driver cancels mid-trip:**
- Platform reassigns trip to another nearby driver if possible
- Current driver penalized (affects acceptance rate, future dispatch priority)
- Rider is not charged for the cancelled portion
- If no replacement driver found, rider gets full refund + credit
- Repeated driver cancellations trigger review/suspension

**System cancellation (driver disconnect):**
- If driver's location updates stop for > 2 minutes during active trip
- System attempts to contact driver via push notification + SMS
- After 5 minutes, system auto-cancels and attempts reassignment
- Rider notified with options: wait, cancel, or accept new driver
- Fare calculated based on last known position

---

### Q4: How would you design ride pooling/sharing?

**Answer:** Ride pooling (UberPool/Lyft Shared) adds significant complexity:

```
Pooling Matching Algorithm:
  1. Rider A requests Pool from point X to point Y
  2. Before matching a dedicated driver, check active Pool trips:
     - Find trips where adding this rider has < 40% detour
     - Detour = (new_total_distance - original_distance) / original_distance
  3. If compatible trip found:
     - Update route to include Rider A's pickup and dropoff
     - Notify existing riders of slight route change
     - Adjust fare: each rider pays ~60% of solo fare
  4. If no compatible trip: match with new driver, keep trip "open"
     for 2 minutes to accept additional riders

  Route Optimization:
  - Given N pickup/dropoff points, find optimal ordering
  - This is a variant of the Traveling Salesman Problem
  - For N <= 4 riders (8 points): brute force is feasible (8! = 40,320)
  - Constraint: never pass a rider's dropoff before their pickup
  - Use greedy insertion heuristic for real-time response

  Data Model Addition:
  - pool_trip_id: groups individual rider trips
  - seat_count: available seats (start at 3, decrement per rider)
  - detour_tolerance: configurable per rider (10-40%)
```

---

### Q5: How do you ensure payment consistency?

**Answer:** We use a two-phase approach:

**Phase 1: Pre-Authorization (at ride request)**
- When rider confirms ride, we authorize (hold) the estimated fare on their card
- Stripe: `PaymentIntent.create(amount, capture_method='manual')`
- If auth fails -> reject ride request immediately
- Hold expires after 7 days if not captured

**Phase 2: Capture (at ride completion)**
- When driver marks trip complete, calculate actual fare
- If actual fare <= authorized amount: capture actual amount
- If actual fare > authorized amount (e.g., route change): capture original, charge difference separately
- Use idempotency keys to prevent double-charging
- All payment operations wrapped in PostgreSQL transaction with trip status update

```
BEGIN;
  UPDATE trips SET status = 'COMPLETED', fare_actual = $28.50
    WHERE trip_id = ? AND status = 'IN_PROGRESS';
  INSERT INTO payments (trip_id, amount, status)
    VALUES (?, 28.50, 'CAPTURED');
  -- Call Stripe async, update payment status on callback
COMMIT;
```

For cash payments (common in emerging markets): trip completes, driver collects
cash, platform debits driver's earnings balance for platform commission.

---

### Q6: How does the system handle GPS inaccuracy?

**Answer:**

1. **Kalman Filter:** Driver app applies Kalman filtering to smooth raw GPS
   readings, reducing noise from urban canyons, tunnels, and buildings.

2. **Snap-to-Road:** Server-side algorithm maps GPS coordinates to the nearest
   road segment using road network graph. Prevents drivers from appearing
   inside buildings or rivers.

3. **Accuracy Threshold:** Reject location updates with accuracy > 50 meters.
   Wait for better GPS fix.

4. **Speed Validation:** If implied speed between two updates > 200 km/h
   (impossible for car), discard the outlier update.

5. **Interpolation:** During GPS blackouts (tunnels), interpolate position along
   the expected route using last known speed and heading.

---

### Q7: How do you handle a complete data center failure?

**Answer:**

- **Active-Active:** Deploy in 2+ regions per continent. US-West and US-East both
  serve US traffic, partitioned by city.

- **City-level failover:** Each city is assigned to a primary region. If US-West
  fails, SF/LA/Seattle traffic fails over to US-East.

- **DNS failover:** Route53/Cloud DNS health checks detect region failure within
  30 seconds, update DNS to redirect traffic.

- **Data sync:** PostgreSQL cross-region async replication. Accept ~1 second of
  data loss during failover (trips in flight get reconciled from driver app
  state on reconnection).

- **Redis:** No cross-region replication for location data. Drivers reconnect and
  re-send current location to the new region's Redis. Recovery time: ~15 seconds
  as all drivers re-register.

- **Stateless services:** All microservices are stateless; they start fresh in the
  failover region using the replicated databases.

---

### Q8: How do you calculate the optimal pickup point?

**Answer:**

The rider's GPS pin may be in a building, park, or wrong side of a highway.
The pickup point optimization involves:

1. **Snap to nearest road:** Map the GPS coordinate to the closest drivable road.
2. **Consider road directionality:** Place pickup on the correct side of a one-way
   street or divided highway.
3. **Accessibility check:** Ensure the point is not in a no-stop zone (bus lane,
   highway ramp, fire lane).
4. **Landmarks:** Cross-reference with known pickup spots (building entrances,
   designated rideshare zones at airports).
5. **Historical data:** Use ML model trained on where drivers actually stopped for
   previous pickups at similar GPS coordinates.

---

### Q9: How does the system handle peak events (concerts, sports)?

**Answer:**

1. **Geo-fence the venue:** Define virtual boundary around the event location.
2. **Pre-positioning:** 1-2 hours before event ends, send drivers "high demand
   expected" notifications with bonus incentives to position near venue.
3. **Queuing system:** When event ends (mass demand spike), implement virtual
   queue: "You are #47 in line. Estimated wait: 12 min."
4. **Staged pickup zones:** Define specific pickup lanes (Zone A, B, C) to
   prevent congestion. Assign riders to zones based on destination direction.
5. **Pre-surge:** Gradually increase surge 30 min before event ends (predicted
   demand), attracting drivers before the actual spike hits.
6. **Capacity pre-scaling:** Auto-scale services 1 hour before event based on
   historical data for this venue.

---

### Q10: How do you prevent fraud (fake rides, GPS spoofing)?

**Answer:**

1. **GPS spoofing detection:** Compare reported GPS with cell tower triangulation
   and WiFi positioning. If GPS reports driver in Manhattan but cell tower says
   Brooklyn, flag the trip.

2. **Trip anomaly detection:** ML model flags trips where:
   - Distance is 10x the straight-line distance (circular driving)
   - Trip speed is suspiciously consistent (fake GPS replay)
   - Pickup and dropoff are the same location

3. **Collusion detection:** Flag driver-rider pairs who:
   - Ride together > 5 times in a week
   - Always rate each other 5 stars
   - Rides consistently happen during promo/bonus periods

4. **Device fingerprinting:** Track device changes. If a driver account switches
   devices frequently or runs on emulators, flag for review.

5. **Photo verification:** Periodically ask drivers to take a selfie; compare
   against registered photo using face recognition.

---

### Q11: How do you design the notification system for ride updates?

**Answer:**

```
Notification Flow:
  ┌──────────┐    ┌──────────────┐    ┌───────────────┐
  │ Ride     │    │ Notification │    │  Push Gateway  │
  │ Service  │───>│   Service    │───>│  (FCM / APNs) │───> Device
  └──────────┘    └──────┬───────┘    └───────────────┘
                         │
                         ├───> SMS Gateway (Twilio) ───> Phone
                         │
                         └───> WebSocket (in-app real-time)

  Notification Types:
  - RIDE_MATCHED: "Your driver John is 3 min away" (push + in-app)
  - DRIVER_ARRIVING: "Your driver is arriving now" (push + in-app)
  - TRIP_STARTED: "Your trip has started" (in-app)
  - TRIP_COMPLETED: "Trip complete. $18.50" (push + in-app + email)
  - DRIVER_RIDE_REQUEST: "New ride request: 0.8 mi away" (push + sound)

  Reliability:
  - Primary: WebSocket for in-app users (instant)
  - Fallback: Push notification if WebSocket disconnected
  - Last resort: SMS for critical messages (ride matched, safety alerts)
  - Each notification has a TTL; expired ride requests are not delivered
```

---

### Q12: How do you handle international expansion?

**Answer:**

1. **Multi-region deployment:** Deploy service clusters per continent (US, EU,
   APAC, LATAM). Each region handles its own cities independently.

2. **Regulatory compliance:** Different cities have different rules:
   - License requirements (London requires specific driver licenses)
   - Pricing regulations (some cities cap surge)
   - Data residency (EU: GDPR requires data to stay in EU)
   - Cash payment support (India, Brazil)

3. **Currency handling:** Store all amounts in minor units (cents) with currency
   code. Convert at payment time using real-time exchange rates.

4. **Localization:** Ride types, UI strings, support channels localized per market.
   Right-to-left support for Arabic-speaking markets.

5. **Map provider flexibility:** Google Maps in most markets, local providers where
   required (Baidu Maps in China, Yandex in Russia).

---

### Q13: How do you ensure driver and rider safety?

**Answer:**

1. **Real-time trip sharing:** Rider can share trip link with contacts showing live
   location. Emergency button sends location to local authorities.

2. **Trip recording:** Audio recording (opt-in) stored for dispute resolution.
   Video recording in some markets.

3. **Route deviation alerts:** If driver deviates significantly from expected route,
   alert rider and safety team.

4. **Identity verification:** Rider sees driver photo, name, license plate before
   pickup. Driver sees rider name and rating.

5. **Trusted contacts:** Automated notification to rider's emergency contacts for
   late-night rides or when trip takes unexpectedly long.

6. **RideCheck:** ML model monitors trip sensors (sudden stops, long unexpected
   pauses, unusual route). Proactively asks "Is everything OK?" to both parties.

---

### Q14: How do you handle scheduled (future) rides?

**Answer:**

```
Scheduled Ride Flow:
  1. Rider requests ride for future time T
  2. System stores scheduled_ride record:
     {rider_id, pickup, dropoff, scheduled_at: T, ride_type}
  3. No driver is matched at this point

  At T - 15 minutes:
  4. Scheduler (cron-like service) picks up the record
  5. Creates a normal ride request
  6. Matching Service finds and dispatches driver
  7. Driver receives: "Scheduled pickup at 6:00 PM at 123 Market St"

  Why not pre-match?
  - Driver availability 15 min from now is unpredictable
  - Driver may go offline, be on another trip, or relocate
  - Pre-matching wastes driver time (idle waiting)
  - 15-min window balances reliability with efficiency

  Reliability:
  - If first matching attempt fails, retry every 2 min
  - If no driver found by T - 5 min, notify rider
  - Offer to try on-demand or cancel with full refund
  - For premium service: guarantee with pre-matched dedicated drivers
```

---

### Q15: How would you redesign the matching algorithm using ML?

**Answer:**

Move from rule-based scoring to ML-based matching:

**Training Data:**
- Historical trips: (driver, rider, context) -> outcome
- Outcome: acceptance probability, trip completion, rider rating

**Features:**
- Driver: current location, heading, time online, trips today, rating, vehicle type
- Rider: pickup/dropoff locations, ride history, rating, payment reliability
- Context: time of day, day of week, weather, surge level, event proximity

**Model:**
- Multi-objective optimization:
  - Minimize rider wait time (ETA)
  - Maximize match acceptance probability
  - Maximize trip completion probability
  - Maximize driver earnings fairness (distribute trips evenly)
- Use gradient-boosted trees (XGBoost) for real-time inference (< 5ms)
- Retrain daily on last 30 days of data

**A/B Testing:**
- Run ML matching alongside rule-based matching in shadow mode
- Compare: match rate, cancellation rate, rider satisfaction, driver satisfaction
- Gradually shift traffic: 1% -> 5% -> 25% -> 100%

**Advanced: Batched Matching (Uber's approach):**
- Instead of matching rides one-by-one, batch all pending requests in a 2-second window
- Solve a global optimization: assign N riders to M drivers to minimize total wait time
- This is a bipartite matching problem solvable with the Hungarian algorithm: O(N^3)
- For N = 100 pending requests per batch in a city: feasible in < 50ms

---

## 17. System Evolution and Future Considerations

### Phase 1: MVP (Months 1-3)
- Single city, one ride type (sedan)
- Redis GeoHash for driver locations
- PostgreSQL for everything else
- Basic sequential matching
- Fixed pricing (no surge)
- Stripe integration for payments

### Phase 2: Scale (Months 4-8)
- Multi-city expansion with city-level sharding
- Surge pricing pipeline
- Multiple ride types (XL, Black)
- Cassandra for trip history archival
- ETA service with road network routing
- Driver/rider ratings

### Phase 3: Optimization (Months 9-12)
- ML-based ETA prediction
- ML-based matching (batched optimization)
- Ride pooling
- Scheduled rides
- Advanced fraud detection
- International expansion framework

### Phase 4: Platform (Year 2+)
- Multi-modal transport (bikes, scooters)
- Autonomous vehicle integration
- Food delivery (shared driver fleet)
- Enterprise solutions (business accounts)
- Real-time ML model serving at edge

---

## 18. Quick Reference Card

```
┌─────────────────────────────────────────────────────────────────────┐
│              RIDE-SHARING SYSTEM DESIGN CHEAT SHEET                 │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  Scale Numbers:                                                     │
│    20M rides/day, 5M online drivers, 1.25M location updates/sec    │
│                                                                     │
│  Key Components:                                                    │
│    Location Svc (Redis GeoHash) -> Matching Svc -> Ride Svc (PG)   │
│    Pricing Svc (surge) -> Payment Svc (Stripe) -> Notification Svc │
│                                                                     │
│  Critical Design Choices:                                           │
│    1. Redis GeoHash for real-time driver queries (not PostGIS)      │
│    2. Sequential dispatch with broadcast fallback                   │
│    3. WebSocket for location streaming (not HTTP polling)           │
│    4. City-level sharding for blast radius containment              │
│    5. Upfront pricing with post-trip adjustment                     │
│    6. Pre-authorize payment before matching                         │
│                                                                     │
│  Consistency Model:                                                 │
│    Eventually consistent: locations, surge, ratings                 │
│    Strongly consistent: trip state, payments                        │
│                                                                     │
│  Failure Modes to Discuss:                                          │
│    Double dispatch -> optimistic locking                            │
│    Payment failure -> circuit breaker + queue                       │
│    DC failure -> city-level failover                                │
│    GPS inaccuracy -> Kalman filter + snap-to-road                   │
│                                                                     │
│  Impress the Interviewer:                                           │
│    - Mention S2/H3 cells for surge zones (not just lat/lng grid)   │
│    - Contraction Hierarchies for fast ETA (not raw Dijkstra)       │
│    - Batched matching as global optimization (Hungarian algorithm)  │
│    - Exponential smoothing for surge (not instant spikes)           │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

---

*Last updated: 2026-04-09*
