# Item 52: Write Placement delete If You Write Placement new

## Visual Summary

```text
┌───────────────────────────────────────────────────────────────────────────┐
│        ITEM 52: WRITE PLACEMENT DELETE IF YOU WRITE PLACEMENT NEW         │
├───────────────────────────────────────────────────────────────────────────┤
│ 1. Placement new called -> memory allocation succeeds, constructor then   │
│ runs.                                                                     │
│ 2. Constructor throws -> compiler looks for matching placement delete.    │
│ 3. No matching placement delete -> allocated storage may leak.            │
│ 4. Provide delete with same extra parameters as placement new.            │
│ 5. Meaning: placement new needs matching cleanup for construction         │
│ failure.                                                                  │
└───────────────────────────────────────────────────────────────────────────┘
```

## Visual Deep Dive

```text
┌───────────────────────────────────────────────────────────────────────────┐
│                        PLACEMENT NEW FAILURE FLOW                         │
├───────────────────────────────────────────────────────────────────────────┤
│ Custom placement new allocates storage                                    │
│                                     ▼                                     │
│ Constructor starts                                                        │
│                                     ▼                                     │
│ Constructor throws                                                        │
│                                     ▼                                     │
│ Compiler searches matching placement delete                               │
│                                     ▼                                     │
│ If missing, storage can leak                                              │
└───────────────────────────────────────────────────────────────────────────┘
```

```text
┌───────────────────────────────────────────────────────────────────────────┐
│                               MATCHING RULE                               │
├───────────────────────────────────────────────────────────────────────────┤
│ operator new(size_t, Extra...)                                            │
│ must pair with                                                            │
│ operator delete(void*, Extra...)                                          │
│ Extra parameter list must match exactly                                   │
└───────────────────────────────────────────────────────────────────────────┘
```

### Core Concept

This item addresses a subtle but critical requirement: **if you write a placement version of `operator new`, you must also write the corresponding placement version of `operator delete`**. Failing to do so causes memory leaks when constructors throw exceptions. Understanding why requires understanding the relationship between `new` expressions and `operator new` functions.

### The new Expression vs. operator new

A `new` expression like `Widget* pw = new Widget;` does **two** things:

1. Calls `operator new` to allocate raw memory
2. Calls the `Widget` constructor on that raw memory

If step 2 (the constructor) throws an exception, the memory from step 1 must be freed. The C++ runtime automatically does this by calling the matching `operator delete`. But which `operator delete` is "matching"?

```
new expression          =>    operator new called       =>    operator delete called
                                                              (if constructor throws)

Widget* pw = new Widget;      operator new(size_t)            operator delete(void*)
Widget* pw = new (arena) W;   operator new(size_t, Arena&)    operator delete(void*, Arena&)
Widget* pw = new (nothrow) W; operator new(size_t, nothrow_t) operator delete(void*, nothrow_t)
```

The rule: **the runtime calls the `operator delete` whose extra parameters match the extra parameters of the `operator new` that was used.**

### What Happens Without a Matching Placement delete

```cpp
// BAD: Placement new without matching placement delete — MEMORY LEAK

class Widget {
public:
    // Placement new that logs allocations
    static void* operator new(std::size_t size, std::ostream& logStream) {
        logStream << "Allocating " << size << " bytes for Widget\n";
        return ::operator new(size);
    }

    // No matching placement delete!
    // static void operator delete(void* p, std::ostream& logStream) noexcept { ... }

    Widget() {
        // Suppose this throws...
        throw std::runtime_error("Widget construction failed");
    }
};

void createWidget() {
    try {
        // Step 1: operator new(size_t, ostream&) is called — memory allocated
        // Step 2: Widget() constructor is called — it throws
        // Step 3: Runtime looks for operator delete(void*, ostream&) — NOT FOUND
        // Step 4: Runtime does NOTHING — memory is leaked!
        Widget* pw = new (std::cerr) Widget;
    } catch (...) {
        // The memory allocated in step 1 has been leaked
        // There is no way to recover it
    }
}
```

```cpp
// GOOD: Matching placement delete

class Widget {
public:
    static void* operator new(std::size_t size, std::ostream& logStream) {
        logStream << "Allocating " << size << " bytes for Widget\n";
        return ::operator new(size);
    }

    // Matching placement delete — called by runtime if constructor throws
    static void operator delete(void* p, std::ostream& logStream) noexcept {
        logStream << "Deallocating Widget memory (constructor threw)\n";
        ::operator delete(p);
    }

    // Normal delete — called by delete expressions (e.g., delete pw;)
    static void operator delete(void* p) noexcept {
        ::operator delete(p);
    }
};
```

### Important Distinction: Placement delete Is NEVER Called Directly

Placement `operator delete` is **only** called by the runtime when a constructor throws during a placement `new` expression. Client code never directly invokes it:

```cpp
Widget* pw = new (std::cerr) Widget;  // Uses placement new

// When you're done with the object, you call normal delete:
delete pw;  // Calls Widget::operator delete(void*), NOT the placement version!

// There is no "placement delete expression" syntax in C++.
// You cannot write: delete (std::cerr) pw;  // Syntax error!
```

### Real-World Example: Debug Allocation with Source Location

```cpp
#include <new>
#include <cstdio>
#include <cstring>

class TrackedObject {
public:
    // Placement new that records source location
    static void* operator new(std::size_t size, const char* file, int line) {
        std::printf("[ALLOC] %zu bytes at %s:%d\n", size, file, line);

        // Store the source location alongside the allocation
        void* p = ::operator new(size);
        recordAllocation(p, size, file, line);
        return p;
    }

    // MATCHING placement delete — critical for exception safety
    static void operator delete(void* p, const char* file, int line) noexcept {
        std::printf("[DEALLOC-EXCEPTION] at %s:%d\n", file, line);
        removeAllocationRecord(p);
        ::operator delete(p);
    }

    // Normal delete — used by delete expressions
    static void operator delete(void* p) noexcept {
        if (p) {
            reportDeallocation(p);
            removeAllocationRecord(p);
        }
        ::operator delete(p);
    }

    virtual ~TrackedObject() = default;

private:
    static void recordAllocation(void*, std::size_t, const char*, int);
    static void removeAllocationRecord(void*);
    static void reportDeallocation(void*);
};

// Macro to capture source location automatically
#define NEW_TRACKED new (__FILE__, __LINE__)

// Usage:
// TrackedObject* obj = NEW_TRACKED TrackedObject;
// delete obj;  // Calls normal operator delete
```

### The Name-Hiding Problem

A class-specific `operator new` **hides** both the global `operator new` and all inherited versions. This is a separate but related trap:

```cpp
// BAD: Class-specific operator new hides the normal form

class Base {
public:
    // Only provides a placement form — hides the normal operator new!
    static void* operator new(std::size_t size, const MemoryPool& pool) {
        return pool.allocate(size);
    }

    static void operator delete(void* p, const MemoryPool& pool) noexcept {
        pool.deallocate(p);
    }

    static void operator delete(void* p) noexcept {
        ::operator delete(p);
    }
};

// This breaks:
// Base* pb = new Base;  // Error! Normal operator new is hidden!
// Only this works:
// Base* pb = new (myPool) Base;
```

```cpp
// GOOD: Provide all standard forms alongside custom forms

class Base {
public:
    // Normal new/delete
    static void* operator new(std::size_t size) {
        return ::operator new(size);
    }

    static void operator delete(void* p) noexcept {
        ::operator delete(p);
    }

    // Nothrow new/delete
    static void* operator new(std::size_t size, const std::nothrow_t& nt) noexcept {
        return ::operator new(size, nt);
    }

    static void operator delete(void* p, const std::nothrow_t&) noexcept {
        ::operator delete(p);
    }

    // Custom placement new/delete
    static void* operator new(std::size_t size, const MemoryPool& pool) {
        return pool.allocate(size);
    }

    static void operator delete(void* p, const MemoryPool& pool) noexcept {
        pool.deallocate(p);
    }
};
```

### A Convenient Base Class to Avoid Hiding

You can create a base class that declares all the standard forms, then inherit from it:

```cpp
class StandardNewDeleteForms {
public:
    // Normal new/delete
    static void* operator new(std::size_t size) {
        return ::operator new(size);
    }
    static void operator delete(void* p) noexcept {
        ::operator delete(p);
    }

    // Nothrow new/delete
    static void* operator new(std::size_t size, const std::nothrow_t& nt) noexcept {
        return ::operator new(size, nt);
    }
    static void operator delete(void* p, const std::nothrow_t&) noexcept {
        ::operator delete(p);
    }

    // Standard placement new/delete (construct in pre-allocated memory)
    static void* operator new(std::size_t, void* ptr) noexcept {
        return ptr;  // Standard placement new — just returns the pointer
    }
    static void operator delete(void*, void*) noexcept {
        // Standard placement delete — does nothing
    }
};

class Widget : public StandardNewDeleteForms {
public:
    // Bring the base class versions into scope so they aren't hidden
    using StandardNewDeleteForms::operator new;
    using StandardNewDeleteForms::operator delete;

    // Now add custom placement forms — they won't hide the standard ones
    static void* operator new(std::size_t size, std::ostream& log) {
        log << "Allocating Widget (" << size << " bytes)\n";
        return ::operator new(size);
    }

    static void operator delete(void* p, std::ostream& log) noexcept {
        log << "Deallocating Widget (constructor threw)\n";
        ::operator delete(p);
    }
};

// All of these work:
// Widget* w1 = new Widget;                          // Normal
// Widget* w2 = new (std::nothrow) Widget;           // Nothrow
// Widget* w3 = new (std::cerr) Widget;              // Custom placement
// char buffer[sizeof(Widget)];
// Widget* w4 = new (buffer) Widget;                 // Standard placement
```

### Real Placement new (Constructing in Pre-Allocated Memory)

The term "placement new" originally referred specifically to constructing an object in memory you've already allocated. This is the standard library's `operator new(size_t, void*)`:

```cpp
#include <new>
#include <cstdlib>
#include <memory>

// Constructing objects in pre-allocated memory (the "real" placement new)

class Entity {
public:
    Entity(int id, const std::string& name)
        : id_(id), name_(name) {
        std::cout << "Entity " << id_ << " (" << name_ << ") constructed\n";
    }

    ~Entity() {
        std::cout << "Entity " << id_ << " (" << name_ << ") destroyed\n";
    }

private:
    int id_;
    std::string name_;
};

void demonstratePlacementNew() {
    // 1. Allocate raw memory (no constructor called)
    void* rawMemory = ::operator new(sizeof(Entity));

    // 2. Construct an Entity in that raw memory using placement new
    Entity* entity = new (rawMemory) Entity(42, "Player");

    // 3. When done, you must manually call the destructor
    entity->~Entity();  // Explicit destructor call — normally never done except with placement new

    // 4. Then free the raw memory
    ::operator delete(rawMemory);
}

// A more realistic example: pre-allocated buffer of objects
class EntityPool {
public:
    explicit EntityPool(std::size_t maxEntities)
        : maxEntities_(maxEntities)
        , count_(0)
    {
        // Allocate raw memory for maxEntities Entity objects
        buffer_ = static_cast<Entity*>(::operator new(maxEntities * sizeof(Entity)));
    }

    ~EntityPool() {
        // Destroy all constructed entities
        for (std::size_t i = 0; i < count_; ++i) {
            buffer_[i].~Entity();
        }
        // Free the raw memory
        ::operator delete(buffer_);
    }

    template<typename... Args>
    Entity* construct(Args&&... args) {
        if (count_ >= maxEntities_) {
            throw std::runtime_error("EntityPool full");
        }
        // Placement new: construct in pre-allocated memory
        Entity* e = new (&buffer_[count_]) Entity(std::forward<Args>(args)...);
        ++count_;
        return e;
    }

private:
    Entity* buffer_;
    std::size_t maxEntities_;
    std::size_t count_;
};
```

### Interaction with Smart Pointers

When using placement new with smart pointers, you need custom deleters:

```cpp
// Custom deleter for objects constructed via placement new in a pool
class PoolDeleter {
public:
    explicit PoolDeleter(MemoryPool& pool) : pool_(&pool) {}

    void operator()(Widget* p) const noexcept {
        if (p) {
            p->~Widget();           // Call destructor
            pool_->deallocate(p);   // Return memory to pool (not free/delete)
        }
    }

private:
    MemoryPool* pool_;
};

// Usage:
MemoryPool pool(1024);
void* mem = pool.allocate(sizeof(Widget));
Widget* raw = new (mem) Widget(args);
std::unique_ptr<Widget, PoolDeleter> pw(raw, PoolDeleter(pool));
// pw's destructor will properly clean up using the custom deleter
```

### Complete Example: Logging Allocator with Full Placement new/delete Support

```cpp
#include <new>
#include <iostream>
#include <fstream>

class LoggedAllocation {
public:
    // --- Standard forms (must not be hidden) ---

    static void* operator new(std::size_t size) {
        return ::operator new(size);
    }

    static void operator delete(void* p) noexcept {
        ::operator delete(p);
    }

    static void* operator new(std::size_t size, const std::nothrow_t& nt) noexcept {
        return ::operator new(size, nt);
    }

    static void operator delete(void* p, const std::nothrow_t&) noexcept {
        ::operator delete(p);
    }

    // --- Custom placement form: log to a stream ---

    static void* operator new(std::size_t size, std::ostream& log) {
        void* p = ::operator new(size);
        log << "[ALLOC] " << size << " bytes at " << p << "\n";
        return p;
    }

    // Matching placement delete (called only when constructor throws)
    static void operator delete(void* p, std::ostream& log) noexcept {
        log << "[DEALLOC-EXCEPTION] at " << p << "\n";
        ::operator delete(p);
    }

    // --- Custom placement form: log to a file by name ---

    static void* operator new(std::size_t size, const char* logFile) {
        void* p = ::operator new(size);
        std::ofstream log(logFile, std::ios::app);
        log << "[ALLOC] " << size << " bytes at " << p << "\n";
        return p;
    }

    // Matching placement delete
    static void operator delete(void* p, const char* logFile) noexcept {
        std::ofstream log(logFile, std::ios::app);
        log << "[DEALLOC-EXCEPTION] at " << p << "\n";
        ::operator delete(p);
    }

    // --- Array forms ---

    static void* operator new[](std::size_t size) {
        return ::operator new[](size);
    }

    static void operator delete[](void* p) noexcept {
        ::operator delete[](p);
    }

    static void* operator new[](std::size_t size, std::ostream& log) {
        void* p = ::operator new[](size);
        log << "[ALLOC[]] " << size << " bytes at " << p << "\n";
        return p;
    }

    static void operator delete[](void* p, std::ostream& log) noexcept {
        log << "[DEALLOC[]-EXCEPTION] at " << p << "\n";
        ::operator delete[](p);
    }
};

// Usage:
// LoggedAllocation* la1 = new LoggedAllocation;                 // Normal
// LoggedAllocation* la2 = new (std::nothrow) LoggedAllocation;  // Nothrow
// LoggedAllocation* la3 = new (std::cerr) LoggedAllocation;     // Logged to cerr
// LoggedAllocation* la4 = new ("alloc.log") LoggedAllocation;   // Logged to file
// delete la1;  // Always uses normal operator delete
```

### Things to Remember

- When you write a placement version of `operator new`, be sure to write the corresponding placement version of `operator delete`. If you don't, your program will have subtle, intermittent memory leaks whenever the constructed object's constructor throws an exception.

- When you declare placement versions of `new` and `delete` in a class, be sure not to unintentionally hide the normal (non-placement) versions. Use `using` declarations or inherit from a base class that provides all standard forms.

- Placement `operator delete` is **only** called by the runtime during exception handling (when a constructor throws in a placement `new` expression). It is **never** called by a `delete` expression — `delete pw` always calls the normal `operator delete(void*)`.

- The standard placement `new` (constructing in pre-allocated memory) requires explicit destructor calls and manual memory management. Wrap such objects in smart pointers with custom deleters for safety.

---

## Summary of Chapter 8

| Item | Core Message |
|------|-------------|
| **49** | `set_new_handler` gives you a last-chance hook before allocation failure. The handler must follow a strict five-option contract. `nothrow new` is less useful than it appears because constructors can still throw. |
| **50** | Replace `new`/`delete` for debugging, performance, statistics, alignment, or locality — but profile first and know the conventions. |
| **51** | Follow the standard's conventions: infinite retry loop with new-handler, handle zero-byte requests, handle wrong-size requests from derived classes, and handle `nullptr` in `delete`. |
| **52** | Every placement `operator new` needs a matching placement `operator delete` or you get memory leaks when constructors throw. Use `using` declarations to avoid hiding the standard forms. |
