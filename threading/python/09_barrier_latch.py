"""
QUESTION 9: Barrier and CountDownLatch (Databricks/Rubrik)
==========================================================

Problem: Implement synchronization primitives for phase-based computation.

Key Concepts: Synchronization points, MapReduce patterns
"""

import threading
import time


class Barrier:
    """
    Reusable Barrier Implementation.
    
    EXPLANATION:
    All N threads must arrive before any can proceed.
    
    Use Cases:
    - Parallel algorithms with phases
    - MapReduce: All mappers finish before reduce
    - Simulations: All update before render
    """
    
    def __init__(self, parties: int):
        self.parties = parties
        self.count = parties
        self.generation = 0
        self._condition = threading.Condition()
    
    def wait(self) -> int:
        """Wait for all parties. Returns arrival index."""
        with self._condition:
            gen = self.generation
            index = self.parties - self.count
            self.count -= 1
            
            if self.count == 0:
                # Last to arrive - reset and wake all
                self.count = self.parties
                self.generation += 1
                self._condition.notify_all()
            else:
                while gen == self.generation:
                    self._condition.wait()
            
            return index


class CountDownLatch:
    """
    One-shot CountDownLatch.
    
    EXPLANATION:
    - Initialize with count N
    - Some threads await(), others count_down()
    - When count=0, all waiters proceed
    - NOT reusable
    
    DIFFERENCE from Barrier:
    - Barrier: All threads wait AND signal
    - Latch: Some wait, others signal
    """
    
    def __init__(self, count: int):
        self.count = count
        self._condition = threading.Condition()
    
    def count_down(self):
        with self._condition:
            if self.count > 0:
                self.count -= 1
                if self.count == 0:
                    self._condition.notify_all()
    
    def await_latch(self, timeout: float = None) -> bool:
        with self._condition:
            return self._condition.wait_for(
                lambda: self.count == 0, timeout
            )


def barrier_demo():
    """Parallel matrix processing simulation."""
    NUM_WORKERS, NUM_PHASES = 4, 3
    barrier = Barrier(NUM_WORKERS)
    
    def worker(wid):
        for phase in range(NUM_PHASES):
            print(f"Worker {wid} phase {phase}")
            time.sleep(0.1 * (wid + 1))
            barrier.wait()
        print(f"Worker {wid} done")
    
    threads = [threading.Thread(target=worker, args=(i,)) for i in range(NUM_WORKERS)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()


def latch_demo():
    """Service initialization simulation."""
    latch = CountDownLatch(3)
    
    def init_service(name, duration):
        print(f"{name} initializing...")
        time.sleep(duration)
        print(f"{name} ready!")
        latch.count_down()
    
    for name, dur in [("DB", 0.3), ("Cache", 0.2), ("MQ", 0.4)]:
        threading.Thread(target=init_service, args=(name, dur)).start()
    
    print("Main: Waiting for services...")
    latch.await_latch()
    print("Main: All services ready!")


if __name__ == "__main__":
    print("=== Barrier Demo ===")
    barrier_demo()
    print("\n=== Latch Demo ===")
    latch_demo()

