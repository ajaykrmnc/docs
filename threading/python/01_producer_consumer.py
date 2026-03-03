"""
QUESTION 1: Producer-Consumer Problem (Databricks/Rubrik Favorite)
===================================================================

Problem Statement:
------------------
Implement a thread-safe bounded buffer where multiple producer threads add items
and multiple consumer threads remove items. The buffer has a fixed capacity.
Producers must wait when buffer is full, consumers must wait when buffer is empty.

Companies: Databricks, Rubrik, Glean - This is a CLASSIC interview question!

Key Concepts:
- Thread synchronization
- Condition variables
- Bounded buffers
- Blocking operations
"""

import threading
import time
import random
from collections import deque
from typing import Any, Optional


class BoundedBuffer:
    """
    Thread-safe bounded buffer implementation using locks and condition variables.
    
    EXPLANATION:
    ------------
    1. We use a Lock to ensure mutual exclusion when accessing the buffer
    2. Two Condition variables:
       - not_full: Producers wait on this when buffer is full
       - not_empty: Consumers wait on this when buffer is empty
    3. Condition.wait() releases the lock and blocks until notified
    4. Condition.notify() wakes up one waiting thread
    
    Why Condition Variables?
    - They allow threads to wait for specific conditions
    - They automatically release/reacquire locks during wait
    - More efficient than busy-waiting (spinning)
    """
    
    def __init__(self, capacity: int):
        self.capacity = capacity
        self.buffer = deque()
        self.lock = threading.Lock()
        self.not_full = threading.Condition(self.lock)
        self.not_empty = threading.Condition(self.lock)
    
    def put(self, item: Any) -> None:
        """
        Add item to buffer. Blocks if buffer is full.
        
        CRITICAL INSIGHT: We use 'while' not 'if' for the condition check!
        This handles spurious wakeups - threads can wake up without being notified.
        """
        with self.not_full:  # Acquires the underlying lock
            # Wait while buffer is full
            while len(self.buffer) >= self.capacity:
                print(f"Producer waiting - buffer full (size={len(self.buffer)})")
                self.not_full.wait()  # Releases lock, blocks, reacquires lock when notified
            
            self.buffer.append(item)
            print(f"Produced: {item}, Buffer size: {len(self.buffer)}")
            
            # Notify one waiting consumer
            self.not_empty.notify()
    
    def get(self) -> Any:
        """
        Remove and return item from buffer. Blocks if buffer is empty.
        """
        with self.not_empty:
            # Wait while buffer is empty
            while len(self.buffer) == 0:
                print(f"Consumer waiting - buffer empty")
                self.not_empty.wait()
            
            item = self.buffer.popleft()
            print(f"Consumed: {item}, Buffer size: {len(self.buffer)}")
            
            # Notify one waiting producer
            self.not_full.notify()
            return item


def producer(buffer: BoundedBuffer, producer_id: int, num_items: int):
    """Producer thread function"""
    for i in range(num_items):
        item = f"Item-{producer_id}-{i}"
        buffer.put(item)
        time.sleep(random.uniform(0.1, 0.3))  # Simulate work


def consumer(buffer: BoundedBuffer, consumer_id: int, num_items: int):
    """Consumer thread function"""
    for _ in range(num_items):
        item = buffer.get()
        time.sleep(random.uniform(0.1, 0.5))  # Simulate processing


def main():
    """
    Demo: 2 producers, 2 consumers, buffer capacity 5
    Each producer produces 5 items, each consumer consumes 5 items
    """
    buffer = BoundedBuffer(capacity=5)
    
    producers = [
        threading.Thread(target=producer, args=(buffer, i, 5))
        for i in range(2)
    ]
    consumers = [
        threading.Thread(target=consumer, args=(buffer, i, 5))
        for i in range(2)
    ]
    
    # Start all threads
    for t in producers + consumers:
        t.start()
    
    # Wait for completion
    for t in producers + consumers:
        t.join()
    
    print("All producers and consumers finished!")


if __name__ == "__main__":
    main()

