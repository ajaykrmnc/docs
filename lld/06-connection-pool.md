# Design a Connection Pool
**Difficulty:** Medium-Hard | **Companies:** All Tier-1 (Google, Amazon, Meta, Microsoft)

---

## Problem Statement

Design a generic, thread-safe connection pool for managing database connections with configurable pool sizing, health checking, and fair queuing.

---

## Requirements

### Functional Requirements
1. Configurable minimum and maximum pool size
2. Connection acquisition with timeout
3. Connection health checking and auto-recovery
4. Fair queuing for connection requests
5. Idle connection timeout and cleanup
6. Connection validation before returning to client

### Non-Functional Requirements
1. Thread-safe with minimal contention
2. Efficient resource utilization
3. Metrics and monitoring support
4. Graceful shutdown

---

## Class Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                   ConnectionPool<T>                             │
├─────────────────────────────────────────────────────────────────┤
│ - availableConnections: BlockingQueue<PooledConnection<T>>      │
│ - allConnections: Set<PooledConnection<T>>                      │
│ - config: PoolConfig                                            │
│ - factory: ConnectionFactory<T>                                 │
│ - healthChecker: HealthChecker<T>                               │
│ - metrics: PoolMetrics                                          │
│ - state: PoolState                                              │
├─────────────────────────────────────────────────────────────────┤
│ + acquire(): PooledConnection<T>                                │
│ + acquire(timeout: Duration): PooledConnection<T>               │
│ + release(connection: PooledConnection<T>): void                │
│ + shutdown(): void                                              │
│ + getMetrics(): PoolMetrics                                     │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                  PooledConnection<T>                            │
├─────────────────────────────────────────────────────────────────┤
│ - connection: T                                                 │
│ - createdAt: Instant                                            │
│ - lastUsedAt: Instant                                           │
│ - lastValidatedAt: Instant                                      │
│ - state: ConnectionState                                        │
│ - pool: ConnectionPool<T>                                       │
├─────────────────────────────────────────────────────────────────┤
│ + getConnection(): T                                            │
│ + close(): void                                                 │
│ + isValid(): boolean                                            │
│ + markInUse(): void                                             │
│ + markIdle(): void                                              │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                       PoolConfig                                │
├─────────────────────────────────────────────────────────────────┤
│ - minPoolSize: int                                              │
│ - maxPoolSize: int                                              │
│ - acquireTimeout: Duration                                      │
│ - idleTimeout: Duration                                         │
│ - maxLifetime: Duration                                         │
│ - validationInterval: Duration                                  │
│ - validationQuery: String                                       │
└─────────────────────────────────────────────────────────────────┘
```

---

## Class Implementations

### 1. PoolConfig with Builder
```java
public class PoolConfig {
    private final int minPoolSize;
    private final int maxPoolSize;
    private final Duration acquireTimeout;
    private final Duration idleTimeout;
    private final Duration maxLifetime;
    private final Duration validationInterval;
    private final boolean testOnBorrow;
    private final boolean testOnReturn;
    
    private PoolConfig(Builder builder) {
        this.minPoolSize = builder.minPoolSize;
        this.maxPoolSize = builder.maxPoolSize;
        this.acquireTimeout = builder.acquireTimeout;
        this.idleTimeout = builder.idleTimeout;
        this.maxLifetime = builder.maxLifetime;
        this.validationInterval = builder.validationInterval;
        this.testOnBorrow = builder.testOnBorrow;
        this.testOnReturn = builder.testOnReturn;
    }
    
    public static class Builder {
        private int minPoolSize = 5;
        private int maxPoolSize = 20;
        private Duration acquireTimeout = Duration.ofSeconds(30);
        private Duration idleTimeout = Duration.ofMinutes(10);
        private Duration maxLifetime = Duration.ofMinutes(30);
        private Duration validationInterval = Duration.ofSeconds(30);
        private boolean testOnBorrow = true;
        private boolean testOnReturn = false;
        
        public Builder minPoolSize(int size) { this.minPoolSize = size; return this; }
        public Builder maxPoolSize(int size) { this.maxPoolSize = size; return this; }
        public Builder acquireTimeout(Duration timeout) { this.acquireTimeout = timeout; return this; }
        public PoolConfig build() { return new PoolConfig(this); }
    }
}
```

### 2. ConnectionPool Implementation
```java
public class ConnectionPool<T> implements AutoCloseable {
    private final LinkedBlockingQueue<PooledConnection<T>> available;
    private final Set<PooledConnection<T>> allConnections;
    private final PoolConfig config;
    private final ConnectionFactory<T> factory;
    private final HealthChecker<T> healthChecker;
    private final PoolMetrics metrics;
    private final ReentrantLock lock;
    private final Condition notEmpty;
    private final AtomicInteger currentSize;
    private volatile PoolState state;
    private final ScheduledExecutorService maintenanceExecutor;
    
    public ConnectionPool(PoolConfig config, ConnectionFactory<T> factory) {
        this.config = config;
        this.factory = factory;
        this.available = new LinkedBlockingQueue<>();
        this.allConnections = ConcurrentHashMap.newKeySet();
        this.healthChecker = new HealthChecker<>(factory);
        this.metrics = new PoolMetrics();
        this.lock = new ReentrantLock(true);  // Fair lock
        this.notEmpty = lock.newCondition();
        this.currentSize = new AtomicInteger(0);
        this.state = PoolState.RUNNING;
        this.maintenanceExecutor = Executors.newSingleThreadScheduledExecutor();
        
        initializePool();
        startMaintenanceTask();
    }
    
    private void initializePool() {
        for (int i = 0; i < config.getMinPoolSize(); i++) {
            createConnection();
        }
    }
    
    public PooledConnection<T> acquire() throws InterruptedException {
        return acquire(config.getAcquireTimeout());
    }
    
    public PooledConnection<T> acquire(Duration timeout) throws InterruptedException {
        checkState();
        long startTime = System.nanoTime();
        metrics.recordAcquireAttempt();
        
        PooledConnection<T> conn = available.poll();
        
        if (conn == null) {
            // Try to create new connection if under max
            if (currentSize.get() < config.getMaxPoolSize()) {
                conn = createConnection();
            }
        }
        
        if (conn == null) {
            // Wait for available connection
            conn = available.poll(timeout.toMillis(), TimeUnit.MILLISECONDS);
        }
        
        if (conn == null) {
            metrics.recordTimeout();
            throw new ConnectionPoolException("Timeout waiting for connection");
        }
        
        // Validate connection
        if (config.isTestOnBorrow() && !healthChecker.isHealthy(conn)) {
            destroyConnection(conn);
            return acquire(remainingTimeout(startTime, timeout));
        }
        
        conn.markInUse();
        metrics.recordAcquire(System.nanoTime() - startTime);
        return conn;
    }
    
    public void release(PooledConnection<T> connection) {
        if (connection == null) return;
        
        if (state != PoolState.RUNNING) {
            destroyConnection(connection);
            return;
        }
        
        if (config.isTestOnReturn() && !healthChecker.isHealthy(connection)) {
            destroyConnection(connection);
            ensureMinConnections();
            return;
        }
        
        connection.markIdle();
        available.offer(connection);
        metrics.recordRelease();
    }
    
    private PooledConnection<T> createConnection() {
        T raw = factory.create();
        PooledConnection<T> conn = new PooledConnection<>(raw, this);
        allConnections.add(conn);
        currentSize.incrementAndGet();
        return conn;
    }
    
    private void destroyConnection(PooledConnection<T> conn) {
        allConnections.remove(conn);
        currentSize.decrementAndGet();
        factory.destroy(conn.getConnection());
    }
    
    @Override
    public void close() {
        state = PoolState.SHUTDOWN;
        maintenanceExecutor.shutdown();
        for (PooledConnection<T> conn : allConnections) {
            destroyConnection(conn);
        }
    }
}
```

### 3. PooledConnection Wrapper
```java
public class PooledConnection<T> implements AutoCloseable {
    private final T connection;
    private final ConnectionPool<T> pool;
    private final Instant createdAt;
    private volatile Instant lastUsedAt;
    private volatile ConnectionState state;
    
    public PooledConnection(T connection, ConnectionPool<T> pool) {
        this.connection = connection;
        this.pool = pool;
        this.createdAt = Instant.now();
        this.lastUsedAt = this.createdAt;
        this.state = ConnectionState.IDLE;
    }
    
    public T getConnection() { return connection; }
    
    public void markInUse() {
        this.state = ConnectionState.IN_USE;
        this.lastUsedAt = Instant.now();
    }
    
    public void markIdle() {
        this.state = ConnectionState.IDLE;
        this.lastUsedAt = Instant.now();
    }
    
    @Override
    public void close() {
        pool.release(this);
    }
    
    public boolean isExpired(Duration maxLifetime) {
        return Instant.now().isAfter(createdAt.plus(maxLifetime));
    }
    
    public boolean isIdle(Duration idleTimeout) {
        return state == ConnectionState.IDLE && 
               Instant.now().isAfter(lastUsedAt.plus(idleTimeout));
    }
}
```

