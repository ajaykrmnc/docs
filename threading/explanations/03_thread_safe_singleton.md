# Problem 3: Thread-Safe Singleton Pattern

## 🎯 Problem Statement
Implement a singleton pattern that ensures only one instance is created even when multiple threads try to create instances simultaneously.

## 🏢 Companies
**Databricks, Glean, Rubrik** - Used for database connections, config managers, caches

## 🔑 Core Principles

### 1. The Singleton Problem
```
Thread 1: if (instance == null) → [CONTEXT SWITCH]
Thread 2: if (instance == null) → instance = new Singleton()
Thread 1: [RESUMES] → instance = new Singleton()  // OOPS! Two instances!
```

### 2. Double-Checked Locking Pattern (DCLP)
```
┌─────────────────────────────────────────────────────┐
│  1. First Check (no lock) - Fast path               │
│     if instance exists → return immediately         │
│                                                     │
│  2. Acquire Lock - Only if instance might be null   │
│                                                     │
│  3. Second Check (with lock) - Verify again         │
│     Another thread might have created it            │
│                                                     │
│  4. Create Instance - Safe, we have the lock        │
└─────────────────────────────────────────────────────┘
```

### 3. Why Double Check?
| Approach | Problem |
|----------|---------|
| No lock | Race condition → multiple instances |
| Lock every time | Performance hit on every access |
| Single check + lock | Still slow (lock always acquired) |
| **Double check** | Fast when exists, safe when creating |

### 4. Memory Ordering (Critical for C++/Java!)
```
WITHOUT proper ordering:
  Thread 1: ptr = allocate()    // Step 1
            ptr = assign        // Step 2 (reordered before Step 3!)
            construct(ptr)      // Step 3
  
  Thread 2: sees non-null ptr but UNCONSTRUCTED object! 💥

WITH atomic/volatile:
  Proper memory barriers prevent reordering
```

## 📊 Solutions Comparison

| Solution | Thread-Safe | Performance | Complexity |
|----------|-------------|-------------|------------|
| Naive (no sync) | ❌ | Fast | Simple |
| Global lock | ✅ | Slow | Simple |
| Double-checked | ✅ | Fast | Medium |
| `std::call_once` | ✅ | Fast | Simple |
| **Meyer's Singleton** | ✅ | Fast | **Simplest** |

## 🧠 Best Solutions by Language

### C++ (Meyer's Singleton - BEST)
```cpp
class Singleton {
public:
    static Singleton& getInstance() {
        static Singleton instance;  // C++11 guarantees thread-safety!
        return instance;
    }
};
```

### C++ (std::call_once)
```cpp
std::once_flag flag;
static Singleton* instance;

static Singleton* getInstance() {
    std::call_once(flag, []() {
        instance = new Singleton();
    });
    return instance;
}
```

### Python (Module-level)
```python
# Simplest - Python imports are thread-safe
# singleton.py
class _Singleton:
    pass

instance = _Singleton()  # Created once on import
```

### Python (Metaclass)
```python
class SingletonMeta(type):
    _instances = {}
    _lock = threading.Lock()
    
    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            with cls._lock:
                if cls not in cls._instances:
                    cls._instances[cls] = super().__call__(*args, **kwargs)
        return cls._instances[cls]
```

## ⚠️ Common Mistakes

| Mistake | Problem | Fix |
|---------|---------|-----|
| No memory barrier (C++) | Partially constructed object visible | Use `std::atomic` with proper ordering |
| Forgetting second check | Race condition | Always double-check |
| Not making constructor private | Direct instantiation possible | Hide constructor |

## 🎓 Interview Tips

1. **Start with Meyer's Singleton** for C++ - simplest and correct
2. **Explain memory ordering** - shows deep understanding
3. **Mention lazy vs eager initialization** trade-offs
4. **Know that Python's GIL** helps but isn't sufficient
5. **Discuss testability concerns** - singletons can make testing hard

