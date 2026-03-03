"""
QUESTION 13: Building H2O (LeetCode 1117 - Databricks)
======================================================

Problem: Multiple threads call hydrogen() and oxygen().
Ensure they proceed in groups of 2 hydrogen + 1 oxygen.

Key Concepts: Thread synchronization, Barrier patterns, Resource matching
"""

import threading
import time
import random


class H2O:
    """
    H2O Molecule Builder.
    
    EXPLANATION:
    Use semaphores and barriers to synchronize:
    - Hydrogen semaphore: Allows 2 hydrogen threads
    - Oxygen semaphore: Allows 1 oxygen thread
    - Barrier: All 3 must arrive before proceeding
    - After barrier, reset semaphores for next molecule
    """
    
    def __init__(self):
        self.h_semaphore = threading.Semaphore(2)  # 2 H allowed
        self.o_semaphore = threading.Semaphore(1)  # 1 O allowed
        self.barrier = threading.Barrier(3)  # 3 threads to form H2O
        self._lock = threading.Lock()
    
    def hydrogen(self, release_hydrogen):
        self.h_semaphore.acquire()  # Wait for H slot
        
        release_hydrogen()  # Output 'H'
        
        self.barrier.wait()  # Wait for 2H + 1O
        
        # Reset for next molecule
        self.h_semaphore.release()
    
    def oxygen(self, release_oxygen):
        self.o_semaphore.acquire()  # Wait for O slot
        
        release_oxygen()  # Output 'O'
        
        self.barrier.wait()  # Wait for 2H + 1O
        
        # Reset for next molecule
        self.o_semaphore.release()


class H2OAlternative:
    """
    Alternative using Condition Variables.
    
    EXPLANATION:
    Track counts and use conditions:
    - H threads wait if 2 H already waiting
    - O threads wait if 1 O already waiting
    - Form molecule when 2H + 1O ready
    """
    
    def __init__(self):
        self.h_count = 0
        self.o_count = 0
        self.condition = threading.Condition()
    
    def hydrogen(self, release_hydrogen):
        with self.condition:
            while self.h_count == 2:
                self.condition.wait()
            self.h_count += 1
            release_hydrogen()
            self._try_form_molecule()
    
    def oxygen(self, release_oxygen):
        with self.condition:
            while self.o_count == 1:
                self.condition.wait()
            self.o_count += 1
            release_oxygen()
            self._try_form_molecule()
    
    def _try_form_molecule(self):
        if self.h_count == 2 and self.o_count == 1:
            self.h_count = 0
            self.o_count = 0
            self.condition.notify_all()


def test_h2o():
    h2o = H2O()
    output = []
    lock = threading.Lock()
    
    def release_h():
        with lock:
            output.append('H')
    
    def release_o():
        with lock:
            output.append('O')
    
    # Create threads: 4H + 2O = 2 molecules
    threads = []
    for _ in range(4):
        threads.append(threading.Thread(target=h2o.hydrogen, args=(release_h,)))
    for _ in range(2):
        threads.append(threading.Thread(target=h2o.oxygen, args=(release_o,)))
    
    random.shuffle(threads)  # Random order
    
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    
    result = ''.join(output)
    print(f"Output: {result}")
    
    # Verify: Should have valid H2O molecules
    # Count H and O in each group of 3
    for i in range(0, len(result), 3):
        group = sorted(result[i:i+3])
        assert group == ['H', 'H', 'O'], f"Invalid molecule: {result[i:i+3]}"
    
    print("✓ All molecules valid!")


if __name__ == "__main__":
    test_h2o()

