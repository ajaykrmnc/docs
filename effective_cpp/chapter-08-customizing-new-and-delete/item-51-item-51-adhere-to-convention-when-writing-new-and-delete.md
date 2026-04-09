# Item 51: Adhere to Convention When Writing new and delete

### Core Concept

If you decide to write custom `operator new` and `operator delete`, you must follow the conventions established by the C++ standard. Violating these conventions leads to undefined behavior, subtle bugs, and code that breaks when others (or the standard library) rely on the expected semantics.

### Convention 1: operator new Must Return a Legitimate Pointer Even for Zero-Byte Requests

The C++ standard says that `operator new(0)` must succeed and return a legitimate, unique pointer. This is typically handled by treating zero-byte requests as one-byte requests:

```cpp
// CORRECT: Handling zero-byte requests
void* operator new(std::size_t size) {
    if (size == 0) {
        size = 1;  // Treat zero-byte requests as one-byte requests
    }

    while (true) {
        // Attempt allocation
        void* p = std::malloc(size);
        if (p) return p;

        // Allocation failed — get the current new-handler
        std::new_handler handler = std::get_new_handler();
        if (handler) {
            handler();
            // Handler should either make memory available, throw, or abort
            // Loop back and try again
        } else {
            throw std::bad_alloc();
        }
    }
}
```

### Convention 2: operator new Must Have an Infinite Loop Calling the new-handler

This is the most commonly violated convention. `operator new` must keep trying to allocate, calling the new-handler each time it fails, until either the allocation succeeds or the handler throws/aborts/deinstalls itself:

```cpp
// BAD: Only tries once
void* operator new(std::size_t size) {
    void* p = std::malloc(size);
    if (!p) throw std::bad_alloc();  // Wrong! Must call new-handler first
    return p;
}

// BAD: Calls handler but doesn't loop
void* operator new(std::size_t size) {
    void* p = std::malloc(size);
    if (!p) {
        std::new_handler handler = std::get_new_handler();
        if (handler) handler();
        p = std::malloc(size);  // One retry only — wrong!
        if (!p) throw std::bad_alloc();
    }
    return p;
}

// GOOD: Correct infinite-loop convention
void* operator new(std::size_t size) {
    if (size == 0) size = 1;

    while (true) {
        void* p = std::malloc(size);
        if (p) return p;

        // Allocation failed — invoke the new-handler
        std::new_handler handler = std::get_new_handler();
        if (!handler) throw std::bad_alloc();
        handler();
        // The handler must have done one of the five things (see Item 49)
        // or we loop forever. That's by design — it's the handler's contract.
    }
}
```

### Convention 3: Class-Specific operator new Must Handle "Wrong-Size" Requests

When a class provides `operator new`, it is designed for objects of exactly that class's size. But if a derived class inherits the `operator new` without overriding it, the `size` parameter will be **larger** than expected:

```cpp
class Base {
public:
    static void* operator new(std::size_t size) {
        // BAD: Assumes size == sizeof(Base)
        return pool_.allocate();  // Pool is sized for Base objects only!
    }

    static void operator delete(void* p, std::size_t size) noexcept {
        pool_.deallocate(p);  // Also wrong for derived classes
    }

private:
    int x_, y_;
    static FixedSizePool<Base> pool_;
};

class Derived : public Base {
    int z_;           // Derived is larger than Base
    double w_;
};

// When you do: Derived* d = new Derived;
// Base::operator new is called with size == sizeof(Derived), not sizeof(Base)!
// The pool allocator returns a block sized for Base — buffer overflow!
```

```cpp
// GOOD: Check the size and fall back to global new for wrong sizes
class Base {
public:
    static void* operator new(std::size_t size) {
        if (size != sizeof(Base)) {
            // Derived class — use global operator new
            return ::operator new(size);
        }
        // Exact match — use our pool
        return pool_.allocate();
    }

    static void operator delete(void* p, std::size_t size) noexcept {
        if (!p) return;  // C++ guarantees delete(nullptr) is safe
        if (size != sizeof(Base)) {
            ::operator delete(p);
            return;
        }
        pool_.deallocate(p);
    }

private:
    int x_, y_;
    static FixedSizePool<Base> pool_;
};
```

Note: The size check `size != sizeof(Base)` also implicitly handles the zero-byte case on most platforms, because `sizeof(Base) > 0` for any class with data members. However, for an empty class, `sizeof(Base)` is typically 1, and the zero-byte-to-one-byte promotion means you'd get `size == 1 == sizeof(Base)`, which is correct.

### Convention 4: operator delete Must Handle nullptr

```cpp
// GOOD: operator delete must tolerate null pointers
void operator delete(void* p) noexcept {
    if (!p) return;  // Do nothing for nullptr — standard requires this
    // ... actual deallocation logic ...
    std::free(p);
}
```

### Convention 5: operator new[] and operator delete[] Must Be Consistent

Array forms have their own set of subtleties:

```cpp
class Widget {
public:
    // For operator new[], the size parameter includes extra space for
    // the array element count (typically sizeof(size_t) bytes prepended)
    static void* operator new[](std::size_t size) {
        // size = N * sizeof(Widget) + overhead for element count
        // You generally CANNOT deduce the number of elements from size
        return ::operator new(size);
    }

    static void operator delete[](void* p) noexcept {
        ::operator delete(p);
    }
};
```

### Putting It All Together: A Correct Class-Level operator new/delete

```cpp
#include <new>
#include <cstdlib>

class GameObject {
public:
    // Per-class operator new with all conventions followed
    static void* operator new(std::size_t size) {
        // Convention 1: Handle zero-byte requests (unlikely for a real class, but correct)
        if (size == 0) size = 1;

        // Convention 3: Handle wrong-size requests from derived classes
        if (size != sizeof(GameObject)) {
            return ::operator new(size);
        }

        // Convention 2: Infinite loop with new-handler
        while (true) {
            void* p = allocateFromPool(size);
            if (p) return p;

            // Allocation failed — try the new-handler
            std::new_handler handler = std::get_new_handler();
            if (!handler) throw std::bad_alloc();
            handler();
        }
    }

    // Per-class operator delete
    static void operator delete(void* p, std::size_t size) noexcept {
        // Convention 4: Handle nullptr
        if (!p) return;

        // Convention 3: Handle wrong-size (derived class) requests
        if (size != sizeof(GameObject)) {
            ::operator delete(p);
            return;
        }

        returnToPool(p);
    }

    virtual ~GameObject() = default;

private:
    static void* allocateFromPool(std::size_t size);
    static void returnToPool(void* p) noexcept;

    // ... class members ...
};
```

### C++17 Aligned Allocation Conventions

C++17 introduced aligned versions of `operator new` and `operator delete`. If you replace one, you should replace all matching forms:

```cpp
// C++17: The full set of operator new/delete for a class

class AlignedWidget {
public:
    // Regular forms
    static void* operator new(std::size_t size);
    static void operator delete(void* p) noexcept;
    static void operator delete(void* p, std::size_t size) noexcept;  // C++14 sized delete

    // Array forms
    static void* operator new[](std::size_t size);
    static void operator delete[](void* p) noexcept;
    static void operator delete[](void* p, std::size_t size) noexcept;

    // Aligned forms (C++17) — called when alignof(AlignedWidget) > __STDCPP_DEFAULT_NEW_ALIGNMENT__
    static void* operator new(std::size_t size, std::align_val_t al);
    static void operator delete(void* p, std::align_val_t al) noexcept;
    static void operator delete(void* p, std::size_t size, std::align_val_t al) noexcept;

    // Aligned array forms (C++17)
    static void* operator new[](std::size_t size, std::align_val_t al);
    static void operator delete[](void* p, std::align_val_t al) noexcept;
    static void operator delete[](void* p, std::size_t size, std::align_val_t al) noexcept;
};
```

### Complete Example: Thread-Safe Pool Allocator Following All Conventions

```cpp
#include <new>
#include <cstdlib>
#include <mutex>
#include <vector>

class Particle {
public:
    Particle(float x, float y, float z, float life)
        : x_(x), y_(y), z_(z), life_(life) {}

    static void* operator new(std::size_t size) {
        if (size != sizeof(Particle)) {
            return ::operator new(size);  // Wrong size — delegate
        }

        while (true) {
            {
                std::lock_guard<std::mutex> lock(poolMutex_);
                if (freeList_) {
                    void* p = freeList_;
                    freeList_ = *static_cast<void**>(freeList_);
                    return p;
                }
                // Free list empty — expand the pool
                expandPool();
                if (freeList_) {
                    void* p = freeList_;
                    freeList_ = *static_cast<void**>(freeList_);
                    return p;
                }
            }
            // Pool expansion failed — try the new-handler
            std::new_handler handler = std::get_new_handler();
            if (!handler) throw std::bad_alloc();
            handler();
        }
    }

    static void operator delete(void* p, std::size_t size) noexcept {
        if (!p) return;
        if (size != sizeof(Particle)) {
            ::operator delete(p);
            return;
        }
        std::lock_guard<std::mutex> lock(poolMutex_);
        *static_cast<void**>(p) = freeList_;
        freeList_ = p;
    }

    static void operator delete(void* p) noexcept {
        // Fallback for when size is not available
        operator delete(p, sizeof(Particle));
    }

private:
    float x_, y_, z_, life_;

    static constexpr std::size_t BLOCK_SIZE =
        sizeof(Particle) < sizeof(void*) ? sizeof(void*) : sizeof(Particle);
    static constexpr std::size_t POOL_GROWTH = 1024;

    static void expandPool() {
        // Must be called with poolMutex_ held
        char* chunk = static_cast<char*>(std::malloc(BLOCK_SIZE * POOL_GROWTH));
        if (!chunk) return;  // Caller will check freeList_ or invoke new-handler
        chunks_.push_back(chunk);
        for (std::size_t i = 0; i < POOL_GROWTH; ++i) {
            void* block = chunk + i * BLOCK_SIZE;
            *static_cast<void**>(block) = freeList_;
            freeList_ = block;
        }
    }

    static std::mutex poolMutex_;
    static void* freeList_;
    static std::vector<char*> chunks_;
};

std::mutex Particle::poolMutex_;
void* Particle::freeList_ = nullptr;
std::vector<char*> Particle::chunks_;
```

### Things to Remember

- `operator new` should contain an infinite loop trying to allocate memory, should call the new-handler if it can't satisfy a memory request, and should handle zero-byte requests. Class-specific versions should handle requests for blocks larger than expected (from derived classes).

- `operator delete` should do nothing if passed a null pointer. Class-specific versions should handle blocks that are larger than expected.

- Always pair `operator new` with a matching `operator delete`. If you provide a class-level `operator new`, provide the corresponding `operator delete` in the same class.

- For class-level `operator new`, always check the size parameter against `sizeof(YourClass)` and fall back to `::operator new` for mismatches — this correctly handles derived classes.

---
