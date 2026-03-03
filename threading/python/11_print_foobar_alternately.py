"""
QUESTION 11: Print FooBar Alternately (LeetCode 1115)
=====================================================

Problem: Two threads call foo() and bar() n times each.
Ensure output is "foobar" repeated n times (alternating).

Key Concepts: Thread alternation, Semaphores, Condition variables
"""

import threading


class FooBarSemaphore:
    """
    Solution using Semaphores.

    EXPLANATION:
    Two semaphores act as turn signals:
    - foo_sem: Initially 1 (foo goes first)
    - bar_sem: Initially 0 (bar waits)

    Sequence:
    1. foo acquires foo_sem, prints, releases bar_sem
    2. bar acquires bar_sem, prints, releases foo_sem
    3. Repeat
    """

    def __init__(self, n: int):
        self.n = n
        self.foo_sem = threading.Semaphore(1)  # foo starts
        self.bar_sem = threading.Semaphore(0)  # bar waits

    def foo(self, printFoo):
        for _ in range(self.n):
            self.foo_sem.acquire()
            printFoo()
            self.bar_sem.release()

    def bar(self, printBar):
        for _ in range(self.n):
            self.bar_sem.acquire()
            printBar()
            self.foo_sem.release()


class FooBarCondition:
    """
    Solution using Condition Variable.

    EXPLANATION:
    Boolean flag indicates whose turn it is.
    Each method waits for its turn, then flips the flag.
    """

    def __init__(self, n: int):
        self.n = n
        self.foo_turn = True
        self.condition = threading.Condition()

    def foo(self, printFoo):
        for _ in range(self.n):
            with self.condition:
                while not self.foo_turn:
                    self.condition.wait()
                printFoo()
                self.foo_turn = False
                self.condition.notify()

    def bar(self, printBar):
        for _ in range(self.n):
            with self.condition:
                while self.foo_turn:
                    self.condition.wait()
                printBar()
                self.foo_turn = True
                self.condition.notify()


class FooBarEvent:
    """
    Solution using Events.

    EXPLANATION:
    Two events signal completion of each part.
    Must manually reset events for next iteration.
    """

    def __init__(self, n: int):
        self.n = n
        self.foo_done = threading.Event()
        self.bar_done = threading.Event()
        self.bar_done.set()  # foo goes first

    def foo(self, printFoo):
        for _ in range(self.n):
            self.bar_done.wait()
            self.bar_done.clear()
            printFoo()
            self.foo_done.set()

    def bar(self, printBar):
        for _ in range(self.n):
            self.foo_done.wait()
            self.foo_done.clear()
            printBar()
            self.bar_done.set()


def test(cls):
    print(f"\nTesting {cls.__name__}:")
    n = 3
    obj = cls(n)
    output = []

    def print_foo():
        output.append("foo")

    def print_bar():
        output.append("bar")

    t1 = threading.Thread(target=obj.foo, args=(print_foo,))
    t2 = threading.Thread(target=obj.bar, args=(print_bar,))

    # Start bar first to test synchronization
    t2.start()
    t1.start()

    t1.join()
    t2.join()

    result = ''.join(output)
    expected = "foobar" * n

    print(f"Output: {result}")
    assert result == expected, f"FAILED: expected {expected}"
    print("✓ PASSED")


if __name__ == "__main__":
    test(FooBarSemaphore)
    test(FooBarCondition)
    test(FooBarEvent)
