"""
QUESTION 10: Print In Order (LeetCode 1114 - Databricks/Glean)
==============================================================

Problem Statement:
------------------
Three threads will call first(), second(), third() potentially in any order.
Ensure they print "first", "second", "third" in order regardless of 
which thread starts first.

Companies: Databricks, Glean - Tests understanding of thread ordering

Key Concepts:
- Thread ordering/sequencing
- Condition variables
- Semaphores for ordering
"""

import threading
import time


# ============================================================================
# SOLUTION 1: Using Condition Variables
# ============================================================================

class PrintInOrderCondition:
    """
    EXPLANATION:
    ------------
    Use a state variable to track progress.
    Each method waits until the previous method has completed.
    
    State transitions: 0 -> 1 -> 2 -> done
    """
    
    def __init__(self):
        self.state = 0
        self.condition = threading.Condition()
    
    def first(self, print_first):
        with self.condition:
            print_first()
            self.state = 1
            self.condition.notify_all()
    
    def second(self, print_second):
        with self.condition:
            while self.state < 1:
                self.condition.wait()
            print_second()
            self.state = 2
            self.condition.notify_all()
    
    def third(self, print_third):
        with self.condition:
            while self.state < 2:
                self.condition.wait()
            print_third()


# ============================================================================
# SOLUTION 2: Using Semaphores (More Elegant)
# ============================================================================

class PrintInOrderSemaphore:
    """
    EXPLANATION:
    ------------
    Use semaphores as gates between methods.
    - gate1: Blocks second() until first() completes
    - gate2: Blocks third() until second() completes
    
    Initial state: Both gates closed (0)
    first() opens gate1 -> second() proceeds -> opens gate2 -> third() proceeds
    """
    
    def __init__(self):
        self.gate1 = threading.Semaphore(0)  # Blocks second
        self.gate2 = threading.Semaphore(0)  # Blocks third
    
    def first(self, print_first):
        print_first()
        self.gate1.release()  # Open gate for second
    
    def second(self, print_second):
        self.gate1.acquire()  # Wait for first
        print_second()
        self.gate2.release()  # Open gate for third
    
    def third(self, print_third):
        self.gate2.acquire()  # Wait for second
        print_third()


# ============================================================================
# SOLUTION 3: Using Events (Simplest)
# ============================================================================

class PrintInOrderEvent:
    """
    EXPLANATION:
    ------------
    Events are like boolean flags with wait capability.
    Each method waits for the previous event and sets its own.
    """
    
    def __init__(self):
        self.first_done = threading.Event()
        self.second_done = threading.Event()
    
    def first(self, print_first):
        print_first()
        self.first_done.set()
    
    def second(self, print_second):
        self.first_done.wait()
        print_second()
        self.second_done.set()
    
    def third(self, print_third):
        self.second_done.wait()
        print_third()


# ============================================================================
# Test all solutions
# ============================================================================

def test_solution(solution_class):
    print(f"\nTesting {solution_class.__name__}:")
    
    obj = solution_class()
    output = []
    
    def print_first():
        output.append("first")
        print("first", end=" ")
    
    def print_second():
        output.append("second")
        print("second", end=" ")
    
    def print_third():
        output.append("third")
        print("third")
    
    # Start threads in REVERSE order to test synchronization
    t3 = threading.Thread(target=obj.third, args=(print_third,))
    t2 = threading.Thread(target=obj.second, args=(print_second,))
    t1 = threading.Thread(target=obj.first, args=(print_first,))
    
    t3.start()
    time.sleep(0.01)  # Give t3 time to start waiting
    t2.start()
    time.sleep(0.01)  # Give t2 time to start waiting
    t1.start()
    
    t1.join()
    t2.join()
    t3.join()
    
    assert output == ["first", "second", "third"], f"Wrong order: {output}"
    print("✓ Test passed!")


if __name__ == "__main__":
    test_solution(PrintInOrderCondition)
    test_solution(PrintInOrderSemaphore)
    test_solution(PrintInOrderEvent)

