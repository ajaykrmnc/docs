"""
QUESTION 4: Deadlock Detection and Prevention (Rubrik/Databricks Critical!)
============================================================================

Problem Statement:
------------------
Given a system where multiple threads acquire multiple locks, implement:
1. A mechanism to detect potential deadlocks
2. A lock ordering strategy to prevent deadlocks
3. A timeout-based approach to avoid deadlocks

Companies: Rubrik (distributed storage), Databricks (distributed computing) - CRITICAL topic!

Key Concepts:
- Coffman conditions for deadlock
- Lock ordering
- Timeout-based acquisition
- Deadlock detection graphs
"""

import threading
import time
from contextlib import contextmanager
from typing import List, Set, Dict
import random


# ============================================================================
# DEADLOCK EXAMPLE - What NOT to do
# ============================================================================

def deadlock_example():
    """
    CLASSIC DEADLOCK SCENARIO:
    Thread 1: Lock A -> Lock B
    Thread 2: Lock B -> Lock A
    
    If Thread 1 holds A and waits for B, while Thread 2 holds B and waits for A,
    neither can proceed = DEADLOCK!
    """
    lock_a = threading.Lock()
    lock_b = threading.Lock()
    
    def thread1():
        with lock_a:
            print("Thread 1 acquired Lock A")
            time.sleep(0.1)  # Increase chance of deadlock
            with lock_b:
                print("Thread 1 acquired Lock B")
    
    def thread2():
        with lock_b:
            print("Thread 2 acquired Lock B")
            time.sleep(0.1)
            with lock_a:
                print("Thread 2 acquired Lock A")
    
    # This WILL deadlock!
    # t1 = threading.Thread(target=thread1)
    # t2 = threading.Thread(target=thread2)
    # t1.start(); t2.start()


# ============================================================================
# SOLUTION 1: Lock Ordering (Most Common Interview Answer)
# ============================================================================

class OrderedLock:
    """
    Lock with ordering to prevent deadlocks.
    
    EXPLANATION:
    ------------
    Assign a unique ID to each lock. Always acquire locks in ID order.
    This breaks the circular wait condition (one of the 4 Coffman conditions).
    
    COFFMAN CONDITIONS (all 4 needed for deadlock):
    1. Mutual Exclusion: Resources cannot be shared
    2. Hold and Wait: Thread holds resources while waiting for others
    3. No Preemption: Resources cannot be forcibly taken
    4. Circular Wait: Circular chain of threads waiting for each other
    
    Breaking ANY ONE condition prevents deadlock!
    """
    
    _id_counter = 0
    _id_lock = threading.Lock()
    
    def __init__(self, name: str = ""):
        with OrderedLock._id_lock:
            self._id = OrderedLock._id_counter
            OrderedLock._id_counter += 1
        self._lock = threading.Lock()
        self.name = name or f"Lock-{self._id}"
    
    @property
    def id(self):
        return self._id
    
    def acquire(self):
        self._lock.acquire()
    
    def release(self):
        self._lock.release()
    
    def __enter__(self):
        self.acquire()
        return self
    
    def __exit__(self, *args):
        self.release()


@contextmanager
def acquire_locks_ordered(*locks: OrderedLock):
    """
    Acquire multiple locks in consistent order to prevent deadlock.
    """
    # Sort locks by ID
    sorted_locks = sorted(locks, key=lambda x: x.id)
    
    acquired = []
    try:
        for lock in sorted_locks:
            lock.acquire()
            acquired.append(lock)
            print(f"Acquired {lock.name}")
        yield
    finally:
        # Release in reverse order
        for lock in reversed(acquired):
            lock.release()
            print(f"Released {lock.name}")


# ============================================================================
# SOLUTION 2: Timeout-Based Lock Acquisition
# ============================================================================

class TimeoutLock:
    """
    Lock with timeout to avoid deadlocks.
    
    EXPLANATION:
    ------------
    If we can't acquire a lock within timeout, back off and retry.
    This breaks the "hold and wait" condition.
    """
    
    def __init__(self, name: str = ""):
        self._lock = threading.Lock()
        self.name = name
    
    def acquire_with_timeout(self, timeout: float = 1.0) -> bool:
        """Try to acquire lock with timeout. Returns True if acquired."""
        return self._lock.acquire(timeout=timeout)
    
    def release(self):
        self._lock.release()


def acquire_multiple_with_timeout(locks: List[TimeoutLock], timeout: float = 1.0) -> bool:
    """
    Try to acquire all locks. If any fails, release all and return False.
    """
    acquired = []
    try:
        for lock in locks:
            if lock.acquire_with_timeout(timeout):
                acquired.append(lock)
            else:
                # Failed to acquire - release all and return
                for l in acquired:
                    l.release()
                return False
        return True
    except Exception:
        for l in acquired:
            l.release()
        raise


def demo_ordered_locking():
    """Demonstrate deadlock-free locking with ordering"""
    lock_a = OrderedLock("A")
    lock_b = OrderedLock("B")
    
    def thread1():
        with acquire_locks_ordered(lock_a, lock_b):
            print("Thread 1 working with both locks")
            time.sleep(0.1)
    
    def thread2():
        # Even though we pass B first, they'll be acquired in order
        with acquire_locks_ordered(lock_b, lock_a):
            print("Thread 2 working with both locks")
            time.sleep(0.1)
    
    t1 = threading.Thread(target=thread1)
    t2 = threading.Thread(target=thread2)
    t1.start(); t2.start()
    t1.join(); t2.join()
    print("No deadlock!")


if __name__ == "__main__":
    demo_ordered_locking()

