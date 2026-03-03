"""
QUESTION 20: Thread-Local Storage & Connection Pool (Rubrik/Databricks)
========================================================================

Problem: Implement a connection pool with thread-local connections.
Each thread gets its own connection, reused across calls.

Key Concepts: ThreadLocal, Connection pooling, Resource management
"""

import threading
import time
import random
from typing import Optional
from dataclasses import dataclass
from queue import Queue, Empty


@dataclass
class Connection:
    """Mock database connection."""
    id: int
    in_use: bool = False
    
    def execute(self, query: str):
        time.sleep(0.01)  # Simulate query
        return f"Result from conn-{self.id}: {query}"
    
    def close(self):
        print(f"Connection {self.id} closed")


class ThreadLocalConnectionManager:
    """
    Thread-Local Connection Manager.
    
    EXPLANATION:
    Each thread gets its own connection stored in ThreadLocal.
    Connection is reused for all operations in that thread.
    
    Benefits:
    - No lock contention (each thread has own connection)
    - Connection reuse (no create/destroy overhead)
    - Automatic cleanup with thread death (with weak refs)
    
    When to use:
    - Thread-per-request model
    - Connection affinity needed
    """
    
    _conn_id = 0
    _conn_lock = threading.Lock()
    
    def __init__(self):
        self._local = threading.local()
    
    def _create_connection(self) -> Connection:
        with self._conn_lock:
            ThreadLocalConnectionManager._conn_id += 1
            conn = Connection(id=self._conn_id)
            print(f"Created connection {conn.id} for thread {threading.current_thread().name}")
            return conn
    
    def get_connection(self) -> Connection:
        """Get connection for current thread (creates if needed)."""
        if not hasattr(self._local, 'connection'):
            self._local.connection = self._create_connection()
        return self._local.connection
    
    def close(self):
        """Close current thread's connection."""
        if hasattr(self._local, 'connection'):
            self._local.connection.close()
            del self._local.connection


class ConnectionPool:
    """
    Shared Connection Pool.
    
    EXPLANATION:
    Pool of connections shared by all threads.
    Threads borrow and return connections.
    
    Benefits:
    - Limits total connections (resource control)
    - Works with any threading model
    - Connections can be rebalanced
    
    Design:
    - Queue for available connections
    - Lock for creating new connections
    - Max size to limit resources
    """
    
    def __init__(self, max_size: int = 10, min_size: int = 2):
        self.max_size = max_size
        self.min_size = min_size
        self._pool: Queue = Queue()
        self._size = 0
        self._lock = threading.Lock()
        self._conn_id = 0
        
        # Pre-create minimum connections
        for _ in range(min_size):
            self._pool.put(self._create_connection())
    
    def _create_connection(self) -> Connection:
        self._conn_id += 1
        self._size += 1
        return Connection(id=self._conn_id)
    
    def get_connection(self, timeout: float = 5.0) -> Connection:
        """Get connection from pool (blocking if none available)."""
        try:
            conn = self._pool.get(timeout=0)  # Try non-blocking first
            conn.in_use = True
            return conn
        except Empty:
            pass
        
        # Try to create new connection
        with self._lock:
            if self._size < self.max_size:
                conn = self._create_connection()
                conn.in_use = True
                print(f"Created new connection {conn.id}, pool size: {self._size}")
                return conn
        
        # Wait for available connection
        conn = self._pool.get(timeout=timeout)
        conn.in_use = True
        return conn
    
    def return_connection(self, conn: Connection):
        """Return connection to pool."""
        conn.in_use = False
        self._pool.put(conn)
    
    def close_all(self):
        """Close all connections."""
        while not self._pool.empty():
            try:
                conn = self._pool.get_nowait()
                conn.close()
            except Empty:
                break


class ConnectionPoolContext:
    """Context manager for connection pool."""
    
    def __init__(self, pool: ConnectionPool):
        self.pool = pool
        self.conn: Optional[Connection] = None
    
    def __enter__(self) -> Connection:
        self.conn = self.pool.get_connection()
        return self.conn
    
    def __exit__(self, *args):
        if self.conn:
            self.pool.return_connection(self.conn)


def demo_thread_local():
    print("=== Thread-Local Demo ===")
    manager = ThreadLocalConnectionManager()
    
    def worker(worker_id: int):
        for i in range(3):
            conn = manager.get_connection()
            result = conn.execute(f"Query {i} from worker {worker_id}")
            print(result)
    
    threads = [threading.Thread(target=worker, args=(i,)) for i in range(3)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()


def demo_pool():
    print("\n=== Connection Pool Demo ===")
    pool = ConnectionPool(max_size=3, min_size=1)
    
    def worker(worker_id: int):
        for i in range(3):
            with ConnectionPoolContext(pool) as conn:
                result = conn.execute(f"Query {i} from worker {worker_id}")
                print(result)
                time.sleep(random.uniform(0.05, 0.1))
    
    threads = [threading.Thread(target=worker, args=(i,)) for i in range(5)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    
    pool.close_all()


if __name__ == "__main__":
    demo_thread_local()
    demo_pool()

