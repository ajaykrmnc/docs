"""
QUESTION 15: Concurrent HashMap (Rubrik/Databricks Critical!)
=============================================================

Problem: Implement a thread-safe hash map with good concurrency.

Key Concepts: Lock striping, Fine-grained locking, Read-write locks
"""

import threading
from typing import Any, Optional, List
import hashlib


class ConcurrentHashMapGlobal:
    """
    Simple approach: Global lock.
    
    EXPLANATION:
    One lock for entire map. Simple but poor concurrency.
    All operations serialize - not scalable!
    """
    
    def __init__(self):
        self._map = {}
        self._lock = threading.Lock()
    
    def put(self, key: Any, value: Any):
        with self._lock:
            self._map[key] = value
    
    def get(self, key: Any) -> Optional[Any]:
        with self._lock:
            return self._map.get(key)
    
    def remove(self, key: Any) -> bool:
        with self._lock:
            if key in self._map:
                del self._map[key]
                return True
            return False


class ConcurrentHashMapStriped:
    """
    Lock Striping: Multiple locks for different segments.
    
    EXPLANATION:
    Divide map into N segments, each with own lock.
    Operations on different segments can proceed in parallel.
    
    Design:
    - num_locks buckets, each with RLock
    - Hash key to determine which lock
    - Much better concurrency than global lock
    
    INTERVIEW TIP: This is how Java's ConcurrentHashMap works!
    """
    
    def __init__(self, num_locks: int = 16):
        self.num_locks = num_locks
        self._buckets: List[dict] = [{} for _ in range(num_locks)]
        self._locks = [threading.RLock() for _ in range(num_locks)]
    
    def _get_bucket_index(self, key: Any) -> int:
        return hash(key) % self.num_locks
    
    def put(self, key: Any, value: Any):
        idx = self._get_bucket_index(key)
        with self._locks[idx]:
            self._buckets[idx][key] = value
    
    def get(self, key: Any) -> Optional[Any]:
        idx = self._get_bucket_index(key)
        with self._locks[idx]:
            return self._buckets[idx].get(key)
    
    def remove(self, key: Any) -> bool:
        idx = self._get_bucket_index(key)
        with self._locks[idx]:
            if key in self._buckets[idx]:
                del self._buckets[idx][key]
                return True
            return False
    
    def contains(self, key: Any) -> bool:
        idx = self._get_bucket_index(key)
        with self._locks[idx]:
            return key in self._buckets[idx]
    
    def size(self) -> int:
        """Note: Not atomic across buckets!"""
        total = 0
        for i in range(self.num_locks):
            with self._locks[i]:
                total += len(self._buckets[i])
        return total


class ConcurrentHashMapRW:
    """
    Using Read-Write Locks per segment.
    
    EXPLANATION:
    Multiple readers can access same segment simultaneously.
    Writers still need exclusive access.
    Good when reads >> writes.
    """
    
    def __init__(self, num_segments: int = 16):
        self.num_segments = num_segments
        self._buckets = [{} for _ in range(num_segments)]
        # Each segment has reader count + write lock
        self._read_counts = [0] * num_segments
        self._locks = [threading.Lock() for _ in range(num_segments)]
        self._write_locks = [threading.Lock() for _ in range(num_segments)]
    
    def _get_idx(self, key):
        return hash(key) % self.num_segments
    
    def get(self, key: Any) -> Optional[Any]:
        idx = self._get_idx(key)
        with self._locks[idx]:
            self._read_counts[idx] += 1
            if self._read_counts[idx] == 1:
                self._write_locks[idx].acquire()
        
        try:
            return self._buckets[idx].get(key)
        finally:
            with self._locks[idx]:
                self._read_counts[idx] -= 1
                if self._read_counts[idx] == 0:
                    self._write_locks[idx].release()
    
    def put(self, key: Any, value: Any):
        idx = self._get_idx(key)
        with self._write_locks[idx]:
            self._buckets[idx][key] = value


def benchmark():
    import time
    N = 10000
    
    for name, MapClass in [("Global", ConcurrentHashMapGlobal),
                           ("Striped", ConcurrentHashMapStriped)]:
        m = MapClass()
        
        def writer(start):
            for i in range(start, start + N):
                m.put(f"key{i}", i)
        
        def reader(start):
            for i in range(start, start + N):
                m.get(f"key{i}")
        
        start = time.time()
        threads = [threading.Thread(target=writer, args=(i*N,)) for i in range(4)]
        threads += [threading.Thread(target=reader, args=(i*N,)) for i in range(4)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        
        print(f"{name}: {time.time()-start:.3f}s")


if __name__ == "__main__":
    benchmark()

