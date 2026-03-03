"""
QUESTION 6: Implement a Blocking Queue (Rubrik/Databricks)
==========================================================

Problem Statement:
------------------
Implement a thread-safe blocking queue with the following operations:
1. put(item) - blocks if queue is full
2. get() - blocks if queue is empty
3. put_nowait(item) - raises exception if full
4. get_nowait() - raises exception if empty

Companies: Rubrik, Databricks - Core data structure for pipeline processing

Key Concepts:
- Thread-safe collections
- Blocking vs non-blocking operations
- Condition variables
- Queue capacity management
"""

import threading
import time
from typing import Any, Optional, Generic, TypeVar
from collections import deque

T = TypeVar('T')


class Empty(Exception):
    """Raised when queue is empty and non-blocking get is called"""
    pass


class Full(Exception):
    """Raised when queue is full and non-blocking put is called"""
    pass


class BlockingQueue(Generic[T]):
    """
    Thread-safe blocking queue implementation.
    
    EXPLANATION:
    ------------
    This is a fundamental building block for concurrent programming.
    
    Key Design Decisions:
    1. Use deque for O(1) append/popleft operations
    2. Single lock + two conditions (simpler than multiple locks)
    3. Bounded capacity to prevent memory issues
    
    Conditions:
    - not_empty: Signaled when item is added
    - not_full: Signaled when item is removed
    
    INTERVIEW TIP: Explain why we use notify() vs notify_all()
    - notify(): Wakes one thread (more efficient)
    - notify_all(): Wakes all threads (use when multiple might proceed)
    """
    
    def __init__(self, capacity: int = 0):
        """
        Initialize blocking queue.
        
        Args:
            capacity: Max size. 0 or negative means unlimited.
        """
        self.capacity = capacity if capacity > 0 else float('inf')
        self._queue = deque()
        self._lock = threading.Lock()
        self._not_empty = threading.Condition(self._lock)
        self._not_full = threading.Condition(self._lock)
    
    def put(self, item: T, timeout: Optional[float] = None) -> None:
        """
        Put an item into the queue.
        
        Blocks if necessary until space is available.
        
        Args:
            item: Item to put
            timeout: Max time to wait (None = infinite)
        
        Raises:
            Full: If timeout expires
        """
        with self._not_full:
            if timeout is None:
                # Wait indefinitely
                while len(self._queue) >= self.capacity:
                    self._not_full.wait()
            else:
                # Wait with timeout
                end_time = time.time() + timeout
                while len(self._queue) >= self.capacity:
                    remaining = end_time - time.time()
                    if remaining <= 0:
                        raise Full("Queue is full")
                    self._not_full.wait(timeout=remaining)
            
            self._queue.append(item)
            self._not_empty.notify()
    
    def get(self, timeout: Optional[float] = None) -> T:
        """
        Remove and return an item from the queue.
        
        Blocks if necessary until an item is available.
        """
        with self._not_empty:
            if timeout is None:
                while len(self._queue) == 0:
                    self._not_empty.wait()
            else:
                end_time = time.time() + timeout
                while len(self._queue) == 0:
                    remaining = end_time - time.time()
                    if remaining <= 0:
                        raise Empty("Queue is empty")
                    self._not_empty.wait(timeout=remaining)
            
            item = self._queue.popleft()
            self._not_full.notify()
            return item
    
    def put_nowait(self, item: T) -> None:
        """Put item without blocking. Raises Full if no space."""
        with self._lock:
            if len(self._queue) >= self.capacity:
                raise Full("Queue is full")
            self._queue.append(item)
            self._not_empty.notify()
    
    def get_nowait(self) -> T:
        """Get item without blocking. Raises Empty if no items."""
        with self._lock:
            if len(self._queue) == 0:
                raise Empty("Queue is empty")
            item = self._queue.popleft()
            self._not_full.notify()
            return item
    
    def size(self) -> int:
        """Return current queue size."""
        with self._lock:
            return len(self._queue)
    
    def is_empty(self) -> bool:
        return self.size() == 0
    
    def is_full(self) -> bool:
        return self.size() >= self.capacity


def demo():
    """Demonstrate blocking queue with producers and consumers"""
    q = BlockingQueue[int](capacity=5)
    
    def producer(pid: int):
        for i in range(5):
            q.put(pid * 100 + i)
            print(f"Producer {pid} put {pid * 100 + i}")
            time.sleep(0.05)
    
    def consumer(cid: int):
        for _ in range(5):
            item = q.get(timeout=2)
            print(f"Consumer {cid} got {item}")
            time.sleep(0.1)
    
    threads = [
        threading.Thread(target=producer, args=(1,)),
        threading.Thread(target=producer, args=(2,)),
        threading.Thread(target=consumer, args=(1,)),
        threading.Thread(target=consumer, args=(2,)),
    ]
    
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    
    print("Done!")


if __name__ == "__main__":
    demo()

