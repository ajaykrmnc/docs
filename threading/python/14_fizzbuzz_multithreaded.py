"""
QUESTION 14: FizzBuzz Multithreaded (LeetCode 1195)
===================================================

Problem: 4 threads print numbers 1 to n. Each thread handles specific cases:
- Thread A: prints "fizz" for numbers divisible by 3 (not 5)
- Thread B: prints "buzz" for numbers divisible by 5 (not 3)
- Thread C: prints "fizzbuzz" for numbers divisible by both
- Thread D: prints the number for other cases

Key Concepts: Thread coordination, Turn-based execution, Condition variables
"""

import threading


class FizzBuzz:
    """
    FizzBuzz with 4 synchronized threads.
    
    EXPLANATION:
    - Shared counter tracks current number
    - Each thread waits for its turn (number matches its condition)
    - After printing, increments counter and notifies all
    - Threads exit when counter > n
    """
    
    def __init__(self, n: int):
        self.n = n
        self.current = 1
        self.condition = threading.Condition()
    
    def fizz(self, printFizz):
        """Print fizz for numbers divisible by 3 only."""
        while True:
            with self.condition:
                while self.current <= self.n and not (
                    self.current % 3 == 0 and self.current % 5 != 0
                ):
                    self.condition.wait()
                
                if self.current > self.n:
                    return
                
                printFizz()
                self.current += 1
                self.condition.notify_all()
    
    def buzz(self, printBuzz):
        """Print buzz for numbers divisible by 5 only."""
        while True:
            with self.condition:
                while self.current <= self.n and not (
                    self.current % 5 == 0 and self.current % 3 != 0
                ):
                    self.condition.wait()
                
                if self.current > self.n:
                    return
                
                printBuzz()
                self.current += 1
                self.condition.notify_all()
    
    def fizzbuzz(self, printFizzBuzz):
        """Print fizzbuzz for numbers divisible by both 3 and 5."""
        while True:
            with self.condition:
                while self.current <= self.n and not (
                    self.current % 3 == 0 and self.current % 5 == 0
                ):
                    self.condition.wait()
                
                if self.current > self.n:
                    return
                
                printFizzBuzz()
                self.current += 1
                self.condition.notify_all()
    
    def number(self, printNumber):
        """Print number for numbers not divisible by 3 or 5."""
        while True:
            with self.condition:
                while self.current <= self.n and not (
                    self.current % 3 != 0 and self.current % 5 != 0
                ):
                    self.condition.wait()
                
                if self.current > self.n:
                    return
                
                printNumber(self.current)
                self.current += 1
                self.condition.notify_all()


def test_fizzbuzz():
    n = 15
    fb = FizzBuzz(n)
    output = []
    lock = threading.Lock()
    
    def print_fizz():
        with lock:
            output.append("fizz")
    
    def print_buzz():
        with lock:
            output.append("buzz")
    
    def print_fizzbuzz():
        with lock:
            output.append("fizzbuzz")
    
    def print_number(x):
        with lock:
            output.append(str(x))
    
    threads = [
        threading.Thread(target=fb.fizz, args=(print_fizz,)),
        threading.Thread(target=fb.buzz, args=(print_buzz,)),
        threading.Thread(target=fb.fizzbuzz, args=(print_fizzbuzz,)),
        threading.Thread(target=fb.number, args=(print_number,)),
    ]
    
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    
    print("Output:", output)
    
    # Verify
    expected = []
    for i in range(1, n + 1):
        if i % 15 == 0:
            expected.append("fizzbuzz")
        elif i % 3 == 0:
            expected.append("fizz")
        elif i % 5 == 0:
            expected.append("buzz")
        else:
            expected.append(str(i))
    
    assert output == expected, f"Mismatch!\nGot: {output}\nExp: {expected}"
    print("✓ PASSED")


if __name__ == "__main__":
    test_fizzbuzz()

