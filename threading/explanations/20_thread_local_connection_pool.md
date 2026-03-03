# Problem 20: Thread-Local Storage & Connection Pool

## 🎯 Problem Statement
Implement a connection pool with thread-local connections. Each thread gets its own connection, reused across calls.

## 🏢 Companies
**Rubrik, Databricks** - Essential for database-heavy applications

## 🔑 Core Principles

### 1. Thread-Local Storage (TLS)

```
REGULAR VARIABLE:               THREAD-LOCAL VARIABLE:
┌─────────────────┐             ┌─────────────────┐
│    Shared       │             │   Thread 1: X=1 │
│    Variable     │             │   Thread 2: X=2 │
│     X = ?       │             │   Thread 3: X=3 │
│                 │             │                 │
│ All threads see │             │ Each thread has │
│ same value      │             │ its own copy    │
└─────────────────┘             └─────────────────┘
```

### 2. Why Thread-Local Connections?

```
WITHOUT TLS:
┌────────────┐     ┌──────────────────┐
│ Thread 1   │────►│                  │
│ Thread 2   │────►│  Connection Pool │ ← Lock contention!
│ Thread 3   │────►│  (shared lock)   │
└────────────┘     └──────────────────┘

WITH TLS:
┌────────────┐     ┌──────────────────┐
│ Thread 1   │────►│  Connection 1    │ ← No contention!
├────────────┤     ├──────────────────┤
│ Thread 2   │────►│  Connection 2    │
├────────────┤     ├──────────────────┤
│ Thread 3   │────►│  Connection 3    │
└────────────┘     └──────────────────┘

Each thread has own connection - NO LOCKS needed for access!
```

### 3. Thread-Local Implementation

```python
# Python
class ThreadLocalConnectionManager:
    def __init__(self):
        self._local = threading.local()
    
    def get_connection(self):
        if not hasattr(self._local, 'connection'):
            self._local.connection = create_connection()
        return self._local.connection
```

```cpp
// C++
class ConnectionManager {
    static thread_local std::unique_ptr<Connection> connection_;
    
public:
    static Connection& getConnection() {
        if (!connection_) {
            connection_ = std::make_unique<Connection>();
        }
        return *connection_;
    }
};

thread_local std::unique_ptr<Connection> 
    ConnectionManager::connection_;
```

### 4. Connection Pool (Shared)

```
┌─────────────────────────────────────────────────────────┐
│                   CONNECTION POOL                        │
│                                                          │
│   Available:  [Conn1] [Conn2] [Conn3] [    ] [    ]    │
│                  ↑                                       │
│                  │ acquire()                            │
│   ┌──────────────┴──────────────┐                       │
│   │                             │                       │
│   ▼                             ▼                       │
│ Thread 1                    Thread 2                    │
│ (uses Conn1)               (uses Conn2)                │
│   │                             │                       │
│   │ release()                   │                       │
│   ▼                             ▼                       │
│   [Conn1] returns to pool                              │
└─────────────────────────────────────────────────────────┘
```

### 5. Pool Implementation

```python
class ConnectionPool:
    def __init__(self, max_size=10):
        self.max_size = max_size
        self.pool = Queue()
        self.size = 0
        self.lock = Lock()
    
    def acquire(self, timeout=None):
        try:
            return self.pool.get(timeout=0)  # Try non-blocking
        except Empty:
            pass
        
        with self.lock:
            if self.size < self.max_size:
                self.size += 1
                return Connection()  # Create new
        
        # Wait for available connection
        return self.pool.get(timeout=timeout)
    
    def release(self, conn):
        self.pool.put(conn)
```

### 6. RAII Pattern for Connection

```cpp
class PooledConnection {
    ConnectionPool& pool_;
    std::unique_ptr<Connection> conn_;
    
public:
    PooledConnection(ConnectionPool& pool) 
        : pool_(pool), conn_(pool.acquire()) {}
    
    ~PooledConnection() {
        pool_.release(std::move(conn_));
    }
    
    Connection& get() { return *conn_; }
};

// Usage
void doWork() {
    PooledConnection conn(pool);  // Acquire
    conn.get().execute("SELECT...");
}  // Auto-release when scope ends
```

## 📊 Comparison

| Approach | Lock Contention | Memory | Use Case |
|----------|-----------------|--------|----------|
| **Thread-Local** | None | High (1 per thread) | Thread-per-request |
| **Shared Pool** | Some | Low (fixed pool) | Task-based |
| **Per-Request** | None | Very High | Stateless |

## 🧠 Key Insights

### When to Use Thread-Local
```
GOOD FOR:
✓ Thread-per-request model (web servers)
✓ Connection affinity needed (transactions)
✓ Avoiding lock overhead critical

BAD FOR:
✗ Many short-lived threads (connection per thread)
✗ Need connection limits (no upper bound)
✗ Task-based parallelism (thread pool reuse)
```

### Pool Sizing
```
GUIDELINES:
- Web app: connections = num_workers
- Background jobs: connections = num_concurrent_jobs
- General: connections = CPU_cores × 2

TOO FEW: Threads wait for connections
TOO MANY: Database overwhelmed
```

## ⚠️ Common Mistakes

| Mistake | Problem | Fix |
|---------|---------|-----|
| Not returning to pool | Connection leak | Use RAII/context manager |
| No timeout on acquire | Deadlock possible | Set reasonable timeout |
| Thread-local without cleanup | Memory leak | Clean on thread exit |
| Unlimited pool | Resource exhaustion | Set max_size |

## 💻 Python Context Manager

```python
class PooledConnection:
    def __init__(self, pool):
        self.pool = pool
        self.conn = None
    
    def __enter__(self):
        self.conn = self.pool.acquire()
        return self.conn
    
    def __exit__(self, *args):
        self.pool.release(self.conn)

# Usage
with PooledConnection(pool) as conn:
    conn.execute("SELECT...")
# Auto-released!
```

## 🔗 Real-World Libraries
- **Python**: `psycopg2.pool`, `sqlalchemy.pool`
- **Java**: HikariCP, C3P0
- **C++**: cpp-redis, libpqxx

