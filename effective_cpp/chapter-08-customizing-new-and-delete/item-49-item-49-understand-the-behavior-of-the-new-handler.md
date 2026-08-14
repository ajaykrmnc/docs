# Item 49: Understand the Behavior of the new-handler

## Visual Summary

```text
┌───────────────────────────────────────────────────────────────────────────┐
│            ITEM 49: UNDERSTAND THE BEHAVIOR OF THE NEW-HANDLER            │
├───────────────────────────────────────────────────────────────────────────┤
│ 1. operator new fails to allocate -> checks current new-handler.          │
│ 2. Handler may free memory, install another handler, uninstall itself,    │
│ throw, or abort.                                                          │
│ 3. If handler returns -> operator new retries allocation.                 │
│ 4. No handler -> std::bad_alloc is thrown.                                │
│ 5. Meaning: new-handler is a retry policy hook for allocation failure.    │
└───────────────────────────────────────────────────────────────────────────┘
```

## Visual Deep Dive

```text
┌───────────────────────────────────────────────────────────────────────────┐
│                          NEW-HANDLER RETRY LOOP                           │
├───────────────────────────────────────────────────────────────────────────┤
│ operator new cannot allocate                                              │
│                                     ▼                                     │
│ Fetch current new-handler                                                 │
│                                     ▼                                     │
│ Handler frees memory / changes handler / throws / aborts                  │
│                                     ▼                                     │
│ If handler returns, allocation is retried                                 │
└───────────────────────────────────────────────────────────────────────────┘
```

```text
┌───────────────────────────────────────────────────────────────────────────┐
│                           VALID HANDLER ACTIONS                           │
├───────────────────────────────────────────────────────────────────────────┤
│ Make more memory available                                                │
│ Install a different handler                                               │
│ Uninstall handler                                                         │
│ Throw bad_alloc or derived exception                                      │
│ Terminate/abort program                                                   │
└───────────────────────────────────────────────────────────────────────────┘
```

### Core Concept

When `operator new` cannot satisfy a memory allocation request, it does **not** immediately throw `std::bad_alloc`. Instead, it first calls a **new-handler** function — a client-installable error-handling function. Understanding this mechanism is essential because it gives you a last-chance hook to free memory, log diagnostics, or gracefully shut down before allocation failure propagates.

### How set_new_handler Works

```cpp
#include <new>
#include <cstdlib>
#include <iostream>

// The new_handler type is simply a pointer to a function taking and returning nothing
// namespace std {
//     typedef void (*new_handler)();
//     new_handler set_new_handler(new_handler p) noexcept;
// }

void outOfMemory() {
    std::cerr << "FATAL: Unable to allocate memory. Shutting down.\n";
    std::abort();
}

int main() {
    // Install our custom handler; set_new_handler returns the previously installed one
    std::new_handler oldHandler = std::set_new_handler(outOfMemory);

    // Now if any new expression fails, outOfMemory() is called before bad_alloc is thrown
    try {
        // Attempt a ludicrously large allocation
        int* p = new int[100000000000L];
        // If outOfMemory() didn't abort, we'd never get here
        delete[] p;
    } catch (const std::bad_alloc& e) {
        std::cerr << "Caught bad_alloc: " << e.what() << "\n";
    }

    // Restore the old handler
    std::set_new_handler(oldHandler);
}
```

### The new-handler Contract

A well-designed new-handler must do one of the following things. If it does not, `operator new` will call it in an infinite loop:

1. **Make more memory available** — so that the next allocation attempt inside `operator new` might succeed.
2. **Install a different new-handler** — if the current handler cannot make more memory available, perhaps it knows of another handler that can.
3. **Deinstall the new-handler** — pass `nullptr` to `set_new_handler`. With no handler installed, `operator new` will throw `std::bad_alloc`.
4. **Throw an exception** — of type `std::bad_alloc` or derived from it.
5. **Not return** — call `std::abort()` or `std::exit()`.

```cpp
// STRATEGY 1: Make more memory available
// Pre-allocate a reserve block that can be freed under pressure

class EmergencyMemoryPool {
public:
    EmergencyMemoryPool(size_t reserveSize = 1024 * 1024 * 64)  // 64 MB reserve
        : reserve_(static_cast<char*>(std::malloc(reserveSize)))
        , reserveSize_(reserveSize)
    {
        if (!reserve_) {
            throw std::runtime_error("Cannot allocate emergency reserve");
        }
    }

    ~EmergencyMemoryPool() {
        std::free(reserve_);
    }

    static void handler() {
        // Release the emergency reserve to make memory available
        if (instance_ && instance_->reserve_) {
            std::cerr << "WARNING: Memory pressure detected. "
                      << "Releasing " << instance_->reserveSize_ << " byte reserve.\n";
            std::free(instance_->reserve_);
            instance_->reserve_ = nullptr;

            // Deinstall this handler — we've done all we can
            // Next failure will throw bad_alloc
            std::set_new_handler(nullptr);
            return;
        }

        // No reserve left — throw
        throw std::bad_alloc();
    }

    static EmergencyMemoryPool* instance_;

private:
    char* reserve_;
    size_t reserveSize_;
};

EmergencyMemoryPool* EmergencyMemoryPool::instance_ = nullptr;

void setupEmergencyPool() {
    static EmergencyMemoryPool pool;
    EmergencyMemoryPool::instance_ = &pool;
    std::set_new_handler(EmergencyMemoryPool::handler);
}
```

```cpp
// STRATEGY 2: Install a different handler (chain of responsibility)

void lastResortHandler() {
    std::cerr << "All memory recovery strategies exhausted. Aborting.\n";
    std::abort();
}

void tryCompactHandler() {
    std::cerr << "Attempting memory compaction...\n";
    // ... attempt to compact or coalesce free blocks ...

    // If compaction didn't help, escalate to the last resort
    std::set_new_handler(lastResortHandler);
}

void tryCacheFlushHandler() {
    std::cerr << "Flushing caches to free memory...\n";
    // ... flush application caches ...

    // If cache flush didn't free enough, try compaction next
    std::set_new_handler(tryCompactHandler);
}

// Install the first link in the chain:
// std::set_new_handler(tryCacheFlushHandler);
```

### Per-Class new-handlers

C++ does not directly provide per-class new-handlers, but you can implement them yourself by overriding `operator new` in your class:

```cpp
#include <new>
#include <mutex>

class Widget {
public:
    static std::new_handler set_new_handler(std::new_handler p) noexcept {
        std::new_handler old = currentHandler_;
        currentHandler_ = p;
        return old;
    }

    static void* operator new(std::size_t size) {
        // Install Widget's handler, save the global one
        NewHandlerHolder h(std::set_new_handler(currentHandler_));
        // Now allocate — if it fails, Widget's handler is called
        return ::operator new(size);
    }

    static void operator delete(void* p) noexcept {
        ::operator delete(p);
    }

private:
    // RAII class to restore the global handler on scope exit
    class NewHandlerHolder {
    public:
        explicit NewHandlerHolder(std::new_handler h) noexcept : handler_(h) {}
        ~NewHandlerHolder() { std::set_new_handler(handler_); }

        NewHandlerHolder(const NewHandlerHolder&) = delete;
        NewHandlerHolder& operator=(const NewHandlerHolder&) = delete;
    private:
        std::new_handler handler_;
    };

    static std::new_handler currentHandler_;
};

std::new_handler Widget::currentHandler_ = nullptr;
```

### Templatizing the Per-Class new-handler (CRTP Mixin)

The above pattern can be generalized using the Curiously Recurring Template Pattern (CRTP) so that any class can gain per-class new-handler support:

```cpp
template<typename T>
class NewHandlerSupport {
public:
    static std::new_handler set_new_handler(std::new_handler p) noexcept {
        std::new_handler old = currentHandler_;
        currentHandler_ = p;
        return old;
    }

    static void* operator new(std::size_t size) {
        // Install T's handler, saving the global one for later restoration
        NewHandlerHolder h(std::set_new_handler(currentHandler_));
        return ::operator new(size);
    }

    static void operator delete(void* p) noexcept {
        ::operator delete(p);
    }

private:
    class NewHandlerHolder {
    public:
        explicit NewHandlerHolder(std::new_handler h) noexcept : handler_(h) {}
        ~NewHandlerHolder() { std::set_new_handler(handler_); }
        NewHandlerHolder(const NewHandlerHolder&) = delete;
        NewHandlerHolder& operator=(const NewHandlerHolder&) = delete;
    private:
        std::new_handler handler_;
    };

    static std::new_handler currentHandler_;
};

template<typename T>
std::new_handler NewHandlerSupport<T>::currentHandler_ = nullptr;

// Usage — just inherit from the mixin:
class Widget : public NewHandlerSupport<Widget> {
    // Widget gets its own static currentHandler_ due to the template instantiation
    // No additional code needed for per-class new-handler support
};

class Gadget : public NewHandlerSupport<Gadget> {
    // Gadget gets its own independent currentHandler_
};

// Now each class can have its own handler:
void widgetOutOfMem() { std::cerr << "Widget allocation failed!\n"; std::abort(); }
void gadgetOutOfMem() { std::cerr << "Gadget allocation failed!\n"; std::abort(); }

void setup() {
    Widget::set_new_handler(widgetOutOfMem);
    Gadget::set_new_handler(gadgetOutOfMem);
}
```

### nothrow new

C++ also provides a nothrow form of `new` that returns `nullptr` instead of throwing:

```cpp
#include <new>

// nothrow form — returns nullptr on failure instead of throwing
Widget* pw = new (std::nothrow) Widget;
if (pw == nullptr) {
    // Allocation failed — handle gracefully
    std::cerr << "Widget allocation failed.\n";
}
```

**Critical caveat**: `nothrow new` only guarantees that `operator new` itself won't throw. The **constructor** of the object being created can still throw. So `new (std::nothrow) Widget` is **not** a guarantee of no exceptions:

```cpp
class Widget {
public:
    Widget() {
        // This constructor allocates memory internally using regular (throwing) new
        data_ = new int[1000000];  // THIS CAN STILL THROW std::bad_alloc!
    }
private:
    int* data_;
};

// BAD: False sense of safety
Widget* pw = new (std::nothrow) Widget;
// The nothrow only applies to the raw memory allocation for the Widget object itself.
// If Widget's constructor internally uses throwing new, you still get bad_alloc.
// You've gained essentially nothing.
```

```cpp
// GOOD: If you truly need no-throw allocation, ensure the constructor is also nothrow
class SafeWidget {
public:
    SafeWidget() noexcept {
        data_ = static_cast<int*>(std::malloc(1000000 * sizeof(int)));
        // Use malloc (returns nullptr on failure) instead of new
    }

    ~SafeWidget() {
        std::free(data_);
    }

    bool isValid() const noexcept { return data_ != nullptr; }

private:
    int* data_ = nullptr;
};
```

### Modern C++ Update (C++11/14/17/20)

In modern C++, `set_new_handler` remains relevant, but direct use of `new` is discouraged in favor of smart pointers:

```cpp
// C++14 and later — prefer make_unique/make_shared
// These still go through operator new internally, so the new-handler mechanism applies
auto widget = std::make_unique<Widget>();    // throws bad_alloc on failure
auto shared = std::make_shared<Widget>();    // throws bad_alloc on failure

// If you need nothrow semantics with smart pointers, you must do it manually:
Widget* raw = new (std::nothrow) Widget;
std::unique_ptr<Widget> safeWidget(raw);     // Wrap in unique_ptr after nothrow new
if (!safeWidget) {
    // Handle failure
}
```

### Things to Remember

- `set_new_handler` lets you specify a function to be called when memory allocation requests cannot be satisfied.

- Nothrow `new` is of limited value because it only prevents `operator new` from throwing, not the object's constructor.

- A new-handler must either make more memory available, install a different handler, deinstall itself, throw `bad_alloc` (or a derived type), or not return at all.

- You can implement per-class new-handlers by overriding `operator new` in your class, saving and restoring the global handler using RAII.

- The CRTP mixin `NewHandlerSupport<T>` lets any class gain per-class new-handler support with zero boilerplate.

---
