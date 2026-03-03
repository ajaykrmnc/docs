"""
QUESTION 8: Dining Philosophers Problem (Classic Interview Question)
=====================================================================

Problem Statement:
------------------
Five philosophers sit at a round table with five forks. Each needs two forks to eat.
Implement a solution that prevents deadlock and starvation.

Companies: Databricks, Rubrik, Glean - Classic concurrency problem!

Key Concepts:
- Deadlock prevention
- Resource hierarchy solution
- Arbitrator solution
- Chandry-Misra solution
"""

import threading
import time
import random


class Fork:
    """Represents a fork (shared resource)"""
    
    def __init__(self, fork_id: int):
        self.id = fork_id
        self._lock = threading.Lock()
    
    def pickup(self):
        self._lock.acquire()
    
    def putdown(self):
        self._lock.release()


# ============================================================================
# SOLUTION 1: Resource Hierarchy (Lock Ordering)
# ============================================================================

class PhilosopherOrdered(threading.Thread):
    """
    Philosopher using resource hierarchy solution.
    
    EXPLANATION:
    ------------
    Always pick up the lower-numbered fork first.
    This breaks the circular wait condition.
    
    Without ordering: Each philosopher picks up left, waits for right -> DEADLOCK
    With ordering: At least one philosopher picks up right first -> NO DEADLOCK
    """
    
    def __init__(self, philosopher_id: int, left_fork: Fork, right_fork: Fork):
        super().__init__()
        self.id = philosopher_id
        # Order forks by ID
        if left_fork.id < right_fork.id:
            self.first_fork = left_fork
            self.second_fork = right_fork
        else:
            self.first_fork = right_fork
            self.second_fork = left_fork
    
    def run(self):
        for _ in range(3):
            self.think()
            self.eat()
    
    def think(self):
        print(f"Philosopher {self.id} is thinking")
        time.sleep(random.uniform(0.1, 0.3))
    
    def eat(self):
        # Always acquire lower-numbered fork first
        self.first_fork.pickup()
        print(f"Philosopher {self.id} picked up fork {self.first_fork.id}")
        
        self.second_fork.pickup()
        print(f"Philosopher {self.id} picked up fork {self.second_fork.id}")
        
        print(f"Philosopher {self.id} is EATING")
        time.sleep(random.uniform(0.1, 0.2))
        
        self.second_fork.putdown()
        self.first_fork.putdown()
        print(f"Philosopher {self.id} finished eating")


# ============================================================================
# SOLUTION 2: Arbitrator (Waiter) Solution
# ============================================================================

class Waiter:
    """
    Arbitrator that controls fork access.
    
    EXPLANATION:
    ------------
    Only 4 philosophers can attempt to eat at once.
    This guarantees at least one can get both forks.
    
    Uses a semaphore to limit concurrent eaters.
    """
    
    def __init__(self, max_diners: int):
        self._semaphore = threading.Semaphore(max_diners)
    
    def request_to_eat(self):
        self._semaphore.acquire()
    
    def done_eating(self):
        self._semaphore.release()


class PhilosopherWithWaiter(threading.Thread):
    """Philosopher that asks waiter for permission to eat"""
    
    def __init__(self, philosopher_id: int, left_fork: Fork, 
                 right_fork: Fork, waiter: Waiter):
        super().__init__()
        self.id = philosopher_id
        self.left_fork = left_fork
        self.right_fork = right_fork
        self.waiter = waiter
    
    def run(self):
        for _ in range(3):
            self.think()
            self.eat()
    
    def think(self):
        print(f"Philosopher {self.id} is thinking")
        time.sleep(random.uniform(0.1, 0.3))
    
    def eat(self):
        # Ask waiter for permission first
        self.waiter.request_to_eat()
        
        try:
            self.left_fork.pickup()
            self.right_fork.pickup()
            
            print(f"Philosopher {self.id} is EATING")
            time.sleep(random.uniform(0.1, 0.2))
            
            self.right_fork.putdown()
            self.left_fork.putdown()
        finally:
            self.waiter.done_eating()


# ============================================================================
# SOLUTION 3: Timeout with Retry (Practical Solution)
# ============================================================================

class PhilosopherTimeout(threading.Thread):
    """
    Philosopher using timeout to avoid deadlock.
    
    EXPLANATION:
    ------------
    Try to acquire forks with timeout.
    If can't get both, release and retry.
    """
    
    def __init__(self, philosopher_id: int, left_fork: Fork, right_fork: Fork):
        super().__init__()
        self.id = philosopher_id
        self.left_fork = left_fork
        self.right_fork = right_fork
        self.left_lock = left_fork._lock
        self.right_lock = right_fork._lock
    
    def run(self):
        for _ in range(3):
            self.think()
            self.eat()
    
    def think(self):
        time.sleep(random.uniform(0.1, 0.3))
    
    def eat(self):
        while True:
            if self.left_lock.acquire(timeout=0.1):
                if self.right_lock.acquire(timeout=0.1):
                    # Got both forks!
                    print(f"Philosopher {self.id} is EATING")
                    time.sleep(random.uniform(0.1, 0.2))
                    self.right_lock.release()
                    self.left_lock.release()
                    return
                else:
                    # Couldn't get right fork, release left
                    self.left_lock.release()
            # Random backoff
            time.sleep(random.uniform(0.01, 0.05))


def run_dining_philosophers():
    """Run dining philosophers with resource hierarchy solution"""
    forks = [Fork(i) for i in range(5)]
    
    philosophers = [
        PhilosopherOrdered(
            i,
            forks[i],  # left fork
            forks[(i + 1) % 5]  # right fork
        )
        for i in range(5)
    ]
    
    for p in philosophers:
        p.start()
    for p in philosophers:
        p.join()
    
    print("All philosophers finished dining!")


if __name__ == "__main__":
    run_dining_philosophers()

