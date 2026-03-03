# 20 Low-Level Design (LLD) Interview Questions for Tier-1 Companies
## Google, Meta, Amazon, Apple, Microsoft, Netflix Level

---

## 1. Design a Rate Limiter
**Difficulty:** Hard | **Company Focus:** Google, Stripe, Cloudflare

Design a rate limiter that supports multiple algorithms (Token Bucket, Sliding Window, Leaky Bucket).

**Requirements:**
- Support different rate limiting strategies per user/API
- Handle distributed rate limiting across multiple servers
- Provide real-time analytics on rate limit violations
- Support dynamic rule updates without restart

**Key Classes:** `RateLimiter`, `TokenBucketStrategy`, `SlidingWindowStrategy`, `RateLimitRule`, `DistributedCounter`

---

## 2. Design an In-Memory Cache with LRU Eviction
**Difficulty:** Hard | **Company Focus:** Google, Amazon, Redis

Design a thread-safe, high-performance cache supporting multiple eviction policies.

**Requirements:**
- O(1) get/put operations
- Support LRU, LFU, and TTL-based eviction
- Thread-safe with minimal lock contention
- Support cache statistics and monitoring
- Implement write-through and write-back policies

**Key Classes:** `Cache<K,V>`, `EvictionPolicy`, `CacheEntry`, `CacheStatistics`, `LRUEvictionPolicy`, `LFUEvictionPolicy`

---

## 3. Design a Pub-Sub Messaging System
**Difficulty:** Hard | **Company Focus:** Google (Pub/Sub), AWS (SNS/SQS)

Design a publisher-subscriber system with guaranteed delivery.

**Requirements:**
- Support topic-based and content-based filtering
- At-least-once and exactly-once delivery semantics
- Message ordering guarantees within partitions
- Dead letter queue for failed messages
- Support both push and pull subscription models

**Key Classes:** `MessageBroker`, `Topic`, `Subscription`, `Message`, `Publisher`, `Subscriber`, `DeadLetterQueue`

---

## 4. Design a Distributed Task Scheduler
**Difficulty:** Hard | **Company Focus:** Google, Airbnb, Uber

Design a task scheduler supporting cron expressions and one-time tasks.

**Requirements:**
- Support recurring tasks with cron expressions
- Handle task dependencies (DAG execution)
- Retry logic with exponential backoff
- Distributed execution across worker nodes
- Task prioritization and resource limits

**Key Classes:** `TaskScheduler`, `Task`, `CronExpression`, `TaskExecutor`, `TaskDependencyGraph`, `RetryPolicy`, `WorkerNode`

---

## 5. Design a File System (In-Memory)
**Difficulty:** Hard | **Company Focus:** Google, Dropbox, Apple

Design an in-memory file system with Unix-like operations.

**Requirements:**
- Support files, directories, and symbolic links
- Implement permissions (read/write/execute) with user/group/other
- Support hard links and reference counting
- Implement `ls`, `cd`, `mkdir`, `rm`, `mv`, `cp`, `chmod`
- Watch for file changes (inotify-like)

**Key Classes:** `FileSystem`, `INode`, `File`, `Directory`, `SymLink`, `Permission`, `FileWatcher`

---

## 6. Design a Connection Pool
**Difficulty:** Medium-Hard | **Company Focus:** All Tier-1

Design a generic, thread-safe connection pool for database connections.

**Requirements:**
- Configurable min/max pool size
- Connection health checking and auto-recovery
- Fair queuing for connection requests
- Connection timeout and idle timeout handling
- Metrics: active connections, wait time, pool exhaustion

**Key Classes:** `ConnectionPool<T>`, `PooledConnection`, `ConnectionFactory`, `HealthChecker`, `PoolConfig`, `PoolMetrics`

---

## 7. Design a Logging Framework
**Difficulty:** Medium-Hard | **Company Focus:** All Tier-1

Design a high-performance, extensible logging framework.

**Requirements:**
- Multiple log levels with hierarchical loggers
- Async logging with bounded queue
- Multiple appenders (File, Console, Network)
- Structured logging with context propagation
- Log rotation and compression
- MDC (Mapped Diagnostic Context) support

**Key Classes:** `Logger`, `LogLevel`, `LogEvent`, `Appender`, `FileAppender`, `AsyncAppender`, `LogFormatter`, `MDC`

---

## 8. Design an Elevator System
**Difficulty:** Medium-Hard | **Company Focus:** Google, Amazon

Design an elevator control system for a building with multiple elevators.

**Requirements:**
- Multiple scheduling algorithms (SCAN, LOOK, FCFS)
- Handle multiple elevators with load balancing
- Support VIP/emergency override
- Weight limit enforcement
- Maintenance mode for individual elevators

**Key Classes:** `ElevatorController`, `Elevator`, `Request`, `SchedulingStrategy`, `Floor`, `Button`, `Display`

---

## 9. Design a Parking Lot System
**Difficulty:** Medium | **Company Focus:** Amazon, Google

Design a parking lot system with multiple floors and vehicle types.

**Requirements:**
- Support multiple vehicle types (Motorcycle, Car, Bus)
- Multiple floors with different spot sizes
- Real-time spot availability tracking
- Payment processing with hourly rates
- Reservation system with time slots

**Key Classes:** `ParkingLot`, `ParkingFloor`, `ParkingSpot`, `Vehicle`, `Ticket`, `PaymentProcessor`, `ParkingStrategy`

---

## 10. Design a Library Management System
**Difficulty:** Medium | **Company Focus:** Amazon, Microsoft

Design a comprehensive library management system.

**Requirements:**
- Book catalog with search (title, author, ISBN)
- Member management with borrowing limits
- Reservation and waitlist system
- Fine calculation for overdue books
- Notification system for due dates and availability

**Key Classes:** `Library`, `Book`, `BookItem`, `Member`, `Librarian`, `BookReservation`, `Fine`, `NotificationService`

---

## 11. Design an Online Chess Game
**Difficulty:** Hard | **Company Focus:** Meta, Google, Microsoft

Design a real-time multiplayer chess game system.

**Requirements:**
- Valid move validation for all piece types
- Game state management (check, checkmate, stalemate)
- Undo/redo functionality
- Time control (Fischer, Increment, Blitz)
- Game replay and move history (PGN format)
- Observer pattern for spectators

**Key Classes:** `Game`, `Board`, `Piece`, `Move`, `Player`, `GameTimer`, `MoveValidator`, `GameObserver`

---

## 12. Design a Notification System
**Difficulty:** Hard | **Company Focus:** Meta, Google, Apple

Design a multi-channel notification system with priorities.

**Requirements:**
- Multiple channels: Push, SMS, Email, In-App
- Priority-based delivery with rate limiting
- User preference management
- Template engine with personalization
- Delivery tracking and analytics
- Batching and digest notifications

**Key Classes:** `NotificationService`, `Notification`, `Channel`, `NotificationTemplate`, `UserPreference`, `DeliveryTracker`, `NotificationQueue`

---

## 13. Design an API Gateway
**Difficulty:** Hard | **Company Focus:** Netflix, Amazon, Google

Design an API Gateway with routing and middleware support.

**Requirements:**
- Dynamic route matching with path parameters
- Request/Response transformation
- Authentication and authorization middleware
- Circuit breaker pattern for downstream services
- Request aggregation from multiple services
- API versioning support

**Key Classes:** `APIGateway`, `Route`, `Middleware`, `RequestContext`, `CircuitBreaker`, `LoadBalancer`, `ServiceRegistry`

---

## 14. Design a Search Autocomplete System
**Difficulty:** Hard | **Company Focus:** Google, Amazon, Microsoft

Design a search autocomplete/typeahead system.

**Requirements:**
- Real-time suggestions as user types
- Trie-based prefix matching
- Ranking based on frequency and recency
- Personalized suggestions per user
- Support for fuzzy matching (typo tolerance)
- Phrase suggestions, not just words

**Key Classes:** `AutocompleteService`, `Trie`, `TrieNode`, `SuggestionRanker`, `UserHistory`, `FuzzyMatcher`, `PhraseIndex`

---

## 15. Design a URL Shortener
**Difficulty:** Medium-Hard | **Company Focus:** All Tier-1

Design a URL shortening service with analytics.

**Requirements:**
- Generate unique short URLs (base62 encoding)
- Custom alias support with collision handling
- Expiration time support
- Click analytics (geolocation, referrer, device)
- Rate limiting per user
- Bulk URL shortening API

**Key Classes:** `URLShortener`, `URLMapping`, `ShortCodeGenerator`, `AnalyticsCollector`, `ClickEvent`, `ExpirationManager`

---

## 16. Design an Order Management System
**Difficulty:** Hard | **Company Focus:** Amazon, Uber, DoorDash

Design an e-commerce order management system.

**Requirements:**
- Order lifecycle management (state machine)
- Inventory reservation with rollback
- Payment processing with retry logic
- Split shipments and partial fulfillment
- Order modification and cancellation
- Event sourcing for order history

**Key Classes:** `Order`, `OrderItem`, `OrderStateMachine`, `InventoryService`, `PaymentService`, `Shipment`, `OrderEvent`

---

## 17. Design a Movie Ticket Booking System
**Difficulty:** Medium-Hard | **Company Focus:** Amazon, Google

Design a movie ticket booking system like BookMyShow.

**Requirements:**
- Seat selection with real-time availability
- Concurrent booking handling (optimistic locking)
- Temporary seat hold during payment
- Multiple theaters and show timings
- Discount codes and offers
- Booking confirmation and e-tickets

**Key Classes:** `BookingService`, `Show`, `Seat`, `SeatLock`, `Booking`, `Theater`, `Movie`, `PaymentGateway`

---

## 18. Design a Vending Machine
**Difficulty:** Medium | **Company Focus:** Google, Amazon

Design a vending machine with state machine pattern.

**Requirements:**
- State machine (Idle, HasMoney, Dispensing, Error)
- Multiple payment methods (Cash, Card, UPI)
- Inventory management with low stock alerts
- Change calculation with optimal coin selection
- Refund handling
- Admin interface for restocking

**Key Classes:** `VendingMachine`, `State`, `Product`, `Inventory`, `PaymentProcessor`, `CoinDispenser`, `Display`

---

## 19. Design a Distributed Lock Manager
**Difficulty:** Hard | **Company Focus:** Google, Amazon, Microsoft

Design a distributed lock service for coordination.

**Requirements:**
- Mutual exclusion guarantees
- Lock timeout and auto-release (fencing tokens)
- Reentrant lock support
- Read-write locks
- Lock fairness policies
- Deadlock detection

**Key Classes:** `DistributedLockManager`, `Lock`, `LockHandle`, `FencingToken`, `LeaseManager`, `DeadlockDetector`, `LockWaiter`

---

## 20. Design a Real-Time Collaborative Editor
**Difficulty:** Very Hard | **Company Focus:** Google (Docs), Microsoft, Notion

Design a collaborative document editing system.

**Requirements:**
- Operational Transformation (OT) or CRDT for conflict resolution
- Real-time cursor and selection sync
- Version history and branching
- Offline editing with sync
- Access control (view, comment, edit)
- Comments and suggestions

**Key Classes:** `Document`, `Operation`, `OperationalTransformer`, `VersionVector`, `Cursor`, `Collaborator`, `ConflictResolver`, `SyncManager`

---

# Evaluation Criteria for Tier-1 Interviews

| Aspect | What They Look For |
|--------|-------------------|
| **OOP Principles** | Encapsulation, Inheritance, Polymorphism, Abstraction |
| **SOLID Principles** | Single Responsibility, Open/Closed, Liskov Substitution, Interface Segregation, Dependency Inversion |
| **Design Patterns** | Factory, Strategy, Observer, State, Singleton, Builder, Decorator |
| **Concurrency** | Thread safety, Race conditions, Deadlock prevention |
| **Scalability** | How design scales with data/users |
| **Extensibility** | How easy to add new features |
| **Trade-offs** | Explaining why you chose certain approaches |

---

## Tips for Tier-1 LLD Interviews

1. **Clarify Requirements** - Spend 5-10 minutes understanding scope
2. **Identify Core Objects** - Start with nouns in requirements
3. **Define Relationships** - Use UML class diagrams
4. **Apply Design Patterns** - Show pattern knowledge
5. **Handle Edge Cases** - Concurrent access, failures, limits
6. **Write Clean Code** - Use interfaces, avoid god classes
7. **Discuss Trade-offs** - Memory vs Speed, Simplicity vs Flexibility

