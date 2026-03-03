"""
QUESTION 3: Thread-Safe Singleton Pattern (Databricks/Glean)
=============================================================

Problem Statement:
------------------
Implement a thread-safe singleton pattern that ensures only one instance is created
even when multiple threads try to create instances simultaneously.

Companies: Common at all three - used for database connections, config managers, caches

Key Concepts:
- Double-checked locking
- Memory barriers
- Class-level locking
- Python's GIL consideration
"""

import threading
import time


# ============================================================================
# SOLUTION 1: Double-Checked Locking (Classic Interview Answer)
# ============================================================================

class SingletonDoubleChecked:
    """
    Double-Checked Locking Singleton
    
    EXPLANATION:
    ------------
    1. First check: Avoid acquiring lock if instance exists (performance)
    2. Lock acquisition: Ensures only one thread creates instance
    3. Second check: Another thread might have created instance while we waited
    
    WHY DOUBLE CHECK?
    - Single check with lock: Every call acquires lock (slow)
    - Single check without lock: Race condition (two instances)
    - Double check: Fast path when instance exists, safe when creating
    
    PYTHON NOTE: Python's GIL makes this somewhat redundant, but this pattern
    is critical for Java/C++ interviews!
    """
    
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        # First check (no locking)
        if cls._instance is None:
            with cls._lock:
                # Second check (with locking)
                if cls._instance is None:
                    print(f"Creating singleton instance in thread {threading.current_thread().name}")
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if not self._initialized:
            self.value = 0
            self._initialized = True


# ============================================================================
# SOLUTION 2: Using Metaclass (Pythonic Way)
# ============================================================================

class SingletonMeta(type):
    """
    Thread-safe Singleton Metaclass
    
    EXPLANATION:
    ------------
    Metaclass controls class creation. __call__ is invoked when you do ClassName().
    This approach is cleaner and more Pythonic.
    """
    
    _instances = {}
    _lock = threading.Lock()
    
    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            with cls._lock:
                if cls not in cls._instances:
                    instance = super().__call__(*args, **kwargs)
                    cls._instances[cls] = instance
        return cls._instances[cls]


class DatabaseConnection(metaclass=SingletonMeta):
    """Example singleton using metaclass"""
    
    def __init__(self):
        self.connection_id = id(self)
        print(f"Database connection created: {self.connection_id}")


# ============================================================================
# SOLUTION 3: Module-Level (Simplest Pythonic Way)
# ============================================================================

class _Config:
    """Private config class"""
    def __init__(self):
        self.settings = {}

# Module-level singleton - Python imports are thread-safe
config = _Config()


# ============================================================================
# SOLUTION 4: Using threading.Lock with decorator
# ============================================================================

def synchronized(lock):
    """Decorator for thread-safe methods"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            with lock:
                return func(*args, **kwargs)
        return wrapper
    return decorator


class SingletonDecorator:
    _instance = None
    _lock = threading.Lock()
    
    @classmethod
    @synchronized(_lock)
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance


def test_singleton():
    """Test that singleton works correctly with multiple threads"""
    instances = []
    
    def create_instance():
        instance = SingletonDoubleChecked()
        instances.append(id(instance))
        time.sleep(0.01)
    
    threads = [threading.Thread(target=create_instance) for _ in range(10)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    
    # All instances should have the same id
    assert len(set(instances)) == 1, "Singleton violated!"
    print(f"Success! All {len(instances)} instances are the same: {instances[0]}")


if __name__ == "__main__":
    test_singleton()

