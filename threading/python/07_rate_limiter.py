"""
QUESTION 7: Implement a Rate Limiter (Glean/Databricks)
=======================================================

Problem: Limit requests to N per second using various algorithms.

Key Concepts: Semaphores, Token bucket, Sliding window
"""

import threading
import time
from collections import deque


class TokenBucketRateLimiter:
    """
    Token Bucket Rate Limiter (Classic Algorithm).
    
    EXPLANATION:
    1. Bucket holds tokens (up to capacity)
    2. Tokens added at fixed rate per second
    3. Each request consumes one token
    4. If no tokens, request rejected or waits
    
    Properties:
    - Allows bursts up to capacity
    - Smooths traffic over time
    """
    
    def __init__(self, rate: float, capacity: int):
        self.rate = rate  # tokens per second
        self.capacity = capacity
        self.tokens = capacity
        self.last_update = time.time()
        self._lock = threading.Lock()
    
    def _refill(self):
        now = time.time()
        elapsed = now - self.last_update
        self.tokens = min(self.capacity, self.tokens + elapsed * self.rate)
        self.last_update = now
    
    def acquire(self, tokens: int = 1) -> bool:
        """Try to acquire tokens. Returns True if successful."""
        with self._lock:
            self._refill()
            if self.tokens >= tokens:
                self.tokens -= tokens
                return True
            return False
    
    def acquire_blocking(self, tokens: int = 1, timeout: float = None) -> bool:
        """Acquire tokens, blocking if necessary."""
        start = time.time()
        while True:
            if self.acquire(tokens):
                return True
            if timeout and (time.time() - start) >= timeout:
                return False
            time.sleep(0.01)


class SlidingWindowRateLimiter:
    """
    Sliding Window Rate Limiter.
    
    EXPLANATION:
    Tracks request timestamps in sliding window.
    More accurate than fixed windows but uses more memory.
    
    Algorithm:
    1. Remove timestamps older than window
    2. If count < limit, allow and add timestamp
    3. Otherwise reject
    """
    
    def __init__(self, max_requests: int, window_seconds: float):
        self.max_requests = max_requests
        self.window = window_seconds
        self.timestamps = deque()
        self._lock = threading.Lock()
    
    def allow_request(self) -> bool:
        with self._lock:
            now = time.time()
            cutoff = now - self.window
            
            while self.timestamps and self.timestamps[0] < cutoff:
                self.timestamps.popleft()
            
            if len(self.timestamps) < self.max_requests:
                self.timestamps.append(now)
                return True
            return False


class LeakyBucketRateLimiter:
    """
    Leaky Bucket Rate Limiter.
    
    EXPLANATION:
    - Requests enter bucket
    - Bucket "leaks" at constant rate
    - If bucket full, requests rejected
    - Produces smooth, constant output rate
    """
    
    def __init__(self, rate: float, capacity: int):
        self.rate = rate
        self.capacity = capacity
        self.water = 0.0
        self.last_leak = time.time()
        self._lock = threading.Lock()
    
    def _leak(self):
        now = time.time()
        elapsed = now - self.last_leak
        self.water = max(0, self.water - elapsed * self.rate)
        self.last_leak = now
    
    def allow_request(self) -> bool:
        with self._lock:
            self._leak()
            if self.water < self.capacity:
                self.water += 1
                return True
            return False


def demo():
    limiter = SlidingWindowRateLimiter(max_requests=5, window_seconds=1.0)
    
    for i in range(10):
        if limiter.allow_request():
            print(f"Request {i}: ALLOWED at {time.time():.3f}")
        else:
            print(f"Request {i}: REJECTED at {time.time():.3f}")
        time.sleep(0.1)


if __name__ == "__main__":
    demo()

