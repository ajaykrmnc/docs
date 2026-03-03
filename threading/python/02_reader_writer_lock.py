"""
QUESTION 2: Reader-Writer Lock (Rubrik/Glean Favorite)
======================================================

Problem Statement:
------------------
Implement a read-write lock that allows:
- Multiple readers to access shared resource simultaneously
- Only one writer at a time with exclusive access
- No readers while a writer is writing

Companies: Rubrik (storage systems), Glean (search indexing), Databricks (data processing)

Key Concepts:
- Shared vs Exclusive locks
- Reader preference vs Writer preference
- Starvation prevention
"""

import threading
import time
import random


class ReadWriteLock:
    """
    Read-Write Lock Implementation (Reader Preference)
    
    EXPLANATION:
    ------------
    This implementation gives preference to readers - as long as readers are active,
    new readers can acquire the lock even if writers are waiting.
    
    TRADE-OFF: This can cause writer starvation!
    
    State tracking:
    - readers: Count of active readers
    - writer: Boolean indicating if a writer is active
    - read_lock: Lock for updating reader count
    - write_lock: Lock for exclusive write access
    """
    
    def __init__(self):
        self.readers = 0
        self.read_lock = threading.Lock()  # Protects reader count
        self.write_lock = threading.Lock()  # Ensures exclusive write access
    
    def acquire_read(self):
        """
        Acquire read lock.
        
        CRITICAL INSIGHT:
        First reader blocks writers by acquiring write_lock.
        Subsequent readers just increment the count.
        """
        with self.read_lock:
            self.readers += 1
            if self.readers == 1:
                # First reader blocks writers
                self.write_lock.acquire()
    
    def release_read(self):
        """Release read lock."""
        with self.read_lock:
            self.readers -= 1
            if self.readers == 0:
                # Last reader allows writers
                self.write_lock.release()
    
    def acquire_write(self):
        """Acquire exclusive write lock."""
        self.write_lock.acquire()
    
    def release_write(self):
        """Release write lock."""
        self.write_lock.release()


class ReadWriteLockFair:
    """
    Fair Read-Write Lock (No Starvation)
    
    EXPLANATION:
    ------------
    Uses an additional lock to ensure fairness.
    When a writer is waiting, new readers must wait too.
    """
    
    def __init__(self):
        self.readers = 0
        self.read_lock = threading.Lock()
        self.write_lock = threading.Lock()
        self.order_lock = threading.Lock()  # Ensures FIFO ordering
    
    def acquire_read(self):
        with self.order_lock:  # Wait in line
            with self.read_lock:
                self.readers += 1
                if self.readers == 1:
                    self.write_lock.acquire()
    
    def release_read(self):
        with self.read_lock:
            self.readers -= 1
            if self.readers == 0:
                self.write_lock.release()
    
    def acquire_write(self):
        self.order_lock.acquire()  # Block new readers
        self.write_lock.acquire()
        self.order_lock.release()
    
    def release_write(self):
        self.write_lock.release()


# Shared resource
shared_data = {"value": 0}
rw_lock = ReadWriteLockFair()


def reader(reader_id: int, iterations: int):
    """Reader thread function"""
    for _ in range(iterations):
        rw_lock.acquire_read()
        try:
            print(f"Reader {reader_id} reading: {shared_data['value']}")
            time.sleep(random.uniform(0.05, 0.1))
        finally:
            rw_lock.release_read()
        time.sleep(random.uniform(0.01, 0.05))


def writer(writer_id: int, iterations: int):
    """Writer thread function"""
    for i in range(iterations):
        rw_lock.acquire_write()
        try:
            shared_data['value'] += 1
            print(f"Writer {writer_id} wrote: {shared_data['value']}")
            time.sleep(random.uniform(0.1, 0.2))
        finally:
            rw_lock.release_write()
        time.sleep(random.uniform(0.05, 0.1))


def main():
    threads = []
    # 3 readers, 2 writers
    for i in range(3):
        threads.append(threading.Thread(target=reader, args=(i, 5)))
    for i in range(2):
        threads.append(threading.Thread(target=writer, args=(i, 3)))
    
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    
    print(f"Final value: {shared_data['value']}")


if __name__ == "__main__":
    main()

