# Chapter 8: Customizing new and delete

> Items 49-52: Mastering C++ memory allocation — from new-handlers and custom allocators to placement new/delete and the conventions that keep everything safe.

---

## Item 49: Understand the Behavior of the new-handler

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

## Item 50: Understand When It Makes Sense to Replace new and delete

### Core Concept

The default implementations of `operator new` and `operator delete` provided by the C++ runtime are designed for **general-purpose** use. They must handle allocation patterns ranging from a single `int` to millions of heterogeneous objects. This generality comes at a cost. There are several legitimate reasons to replace them with custom versions.

### Reason 1: Detecting Usage Errors

Memory bugs — writing past the end of an allocated block, writing before the beginning, double-deletes, forgetting to delete — are among the most pernicious in C++. A custom allocator can catch them early:

```cpp
#include <cstdint>
#include <cstdlib>
#include <cstring>
#include <iostream>
#include <new>

// Debugging allocator that adds signature bytes before and after each allocation
// to detect buffer overruns and underruns.

static const uint32_t FRONT_SIGNATURE = 0xDEADBEEF;
static const uint32_t BACK_SIGNATURE  = 0xCAFEBABE;
static const unsigned char FILL_BYTE   = 0xCD;  // Uninitialized memory pattern
static const unsigned char FREED_BYTE  = 0xDD;  // Freed memory pattern

struct AllocationHeader {
    uint32_t frontSignature;
    std::size_t requestedSize;
    const char* file;
    int line;
    // Padding to maintain alignment (see alignment discussion below)
};

void* operator new(std::size_t size) {
    // Calculate total size: header + requested bytes + back signature
    const std::size_t totalSize = sizeof(AllocationHeader) + size + sizeof(uint32_t);

    void* rawMemory = std::malloc(totalSize);
    if (!rawMemory) {
        throw std::bad_alloc();
    }

    // Write header
    auto* header = static_cast<AllocationHeader*>(rawMemory);
    header->frontSignature = FRONT_SIGNATURE;
    header->requestedSize = size;
    header->file = nullptr;
    header->line = 0;

    // Fill user memory with a pattern to detect reads of uninitialized memory
    void* userMemory = header + 1;
    std::memset(userMemory, FILL_BYTE, size);

    // Write back signature
    auto* backSig = reinterpret_cast<uint32_t*>(
        static_cast<char*>(userMemory) + size
    );
    *backSig = BACK_SIGNATURE;

    return userMemory;
}

void operator delete(void* p) noexcept {
    if (!p) return;

    auto* header = static_cast<AllocationHeader*>(p) - 1;

    // Check front signature — detects underruns
    if (header->frontSignature != FRONT_SIGNATURE) {
        std::cerr << "HEAP CORRUPTION: front signature destroyed at " << p << "\n";
        std::abort();
    }

    // Check back signature — detects overruns
    auto* backSig = reinterpret_cast<uint32_t*>(
        static_cast<char*>(p) + header->requestedSize
    );
    if (*backSig != BACK_SIGNATURE) {
        std::cerr << "HEAP CORRUPTION: buffer overrun detected at " << p
                  << " (allocated " << header->requestedSize << " bytes)\n";
        std::abort();
    }

    // Scribble freed memory so use-after-free is more likely to crash immediately
    std::memset(header, FREED_BYTE, sizeof(AllocationHeader) + header->requestedSize + sizeof(uint32_t));

    std::free(header);
}

// Sized deallocation (C++14)
void operator delete(void* p, std::size_t size) noexcept {
    // Delegate to the unsized version; we track size in the header anyway
    ::operator delete(p);
}
```

### Reason 2: Improving Performance (Speed)

The default allocator must handle all sizes and patterns. If you know your allocation pattern, you can beat it significantly:

```cpp
// Fixed-size allocator (memory pool) for a specific class
// Eliminates per-allocation overhead and fragmentation for uniform-sized objects.

template<typename T>
class FixedSizePool {
public:
    explicit FixedSizePool(std::size_t blockCount = 1024)
        : blockSize_(sizeof(T) < sizeof(FreeBlock*) ? sizeof(FreeBlock*) : sizeof(T))
        , blockCount_(blockCount)
    {
        expandPool();
    }

    ~FixedSizePool() {
        for (auto* chunk : chunks_) {
            ::operator delete(chunk);
        }
    }

    void* allocate() {
        if (!freeList_) {
            expandPool();  // All blocks used — allocate a new chunk
        }
        FreeBlock* block = freeList_;
        freeList_ = block->next;
        return block;
    }

    void deallocate(void* p) noexcept {
        if (!p) return;
        auto* block = static_cast<FreeBlock*>(p);
        block->next = freeList_;
        freeList_ = block;
    }

private:
    struct FreeBlock {
        FreeBlock* next;
    };

    void expandPool() {
        // Allocate a contiguous chunk of blockCount_ blocks
        std::size_t chunkSize = blockSize_ * blockCount_;
        char* chunk = static_cast<char*>(::operator new(chunkSize));
        chunks_.push_back(chunk);

        // Thread all blocks in the chunk onto the free list
        for (std::size_t i = 0; i < blockCount_; ++i) {
            auto* block = reinterpret_cast<FreeBlock*>(chunk + i * blockSize_);
            block->next = freeList_;
            freeList_ = block;
        }
    }

    std::size_t blockSize_;
    std::size_t blockCount_;
    FreeBlock* freeList_ = nullptr;
    std::vector<char*> chunks_;
};

// Using the pool in a class:
class Bullet {
public:
    static void* operator new(std::size_t size) {
        if (size != sizeof(Bullet)) {
            // If a derived class is larger, fall back to global new
            return ::operator new(size);
        }
        return pool_.allocate();
    }

    static void operator delete(void* p, std::size_t size) noexcept {
        if (size != sizeof(Bullet)) {
            ::operator delete(p);
            return;
        }
        pool_.deallocate(p);
    }

    // ... Bullet members ...

private:
    double x_, y_, z_;
    double vx_, vy_, vz_;
    float damage_;
    int ownerId_;

    static FixedSizePool<Bullet> pool_;
};

FixedSizePool<Bullet> Bullet::pool_(4096);  // Pre-allocate 4096 bullet slots
```

### Reason 3: Improving Performance (Memory Usage / Reducing Fragmentation)

The general-purpose allocator typically adds bookkeeping overhead per allocation (often 8-16 bytes on 64-bit systems). For small objects, this overhead can be a massive percentage of the total memory used:

```cpp
// Consider allocating millions of 4-byte objects:
// With default allocator: each 4-byte object may consume 32+ bytes (header + alignment padding)
// That's 8x overhead!

// BAD: Allocating small objects individually
std::vector<int*> pointers;
for (int i = 0; i < 1000000; ++i) {
    pointers.push_back(new int(i));
    // Each new int likely costs 32 bytes total on a 64-bit system
    // Total: ~32 MB for 4 MB of actual data
}

// GOOD: Use a pool allocator or just use a vector
std::vector<int> values;
values.reserve(1000000);
for (int i = 0; i < 1000000; ++i) {
    values.push_back(i);
    // All data contiguous, no per-element overhead
    // Total: ~4 MB
}
```

### Reason 4: Improving Locality of Reference

Objects allocated close in time are often used close in time. The default allocator may scatter them across pages. A custom allocator can cluster related objects:

```cpp
// Arena allocator for scene graph nodes — all nodes for one frame
// are allocated from a contiguous arena, giving excellent cache locality.

class ArenaAllocator {
public:
    explicit ArenaAllocator(std::size_t arenaSize = 1024 * 1024)
        : arenaSize_(arenaSize)
        , current_(nullptr)
        , end_(nullptr)
    {}

    ~ArenaAllocator() {
        for (auto* block : blocks_) {
            std::free(block);
        }
    }

    void* allocate(std::size_t size, std::size_t alignment = alignof(std::max_align_t)) {
        // Align the current pointer
        std::size_t space = static_cast<std::size_t>(end_ - current_);
        void* aligned = current_;
        if (!std::align(alignment, size, aligned, space)) {
            // Not enough room in current block — allocate a new one
            allocateBlock(std::max(arenaSize_, size + alignment));
            space = static_cast<std::size_t>(end_ - current_);
            aligned = current_;
            if (!std::align(alignment, size, aligned, space)) {
                throw std::bad_alloc();
            }
        }
        current_ = static_cast<char*>(aligned) + size;
        return aligned;
    }

    // Reset the arena — "free" everything at once (O(1))
    void reset() noexcept {
        for (auto* block : blocks_) {
            std::free(block);
        }
        blocks_.clear();
        current_ = nullptr;
        end_ = nullptr;
    }

    // No individual deallocation — everything freed together via reset()
    // This is the key advantage: allocation is a pointer bump, deallocation is free

private:
    void allocateBlock(std::size_t size) {
        auto* block = static_cast<char*>(std::malloc(size));
        if (!block) throw std::bad_alloc();
        blocks_.push_back(block);
        current_ = block;
        end_ = block + size;
    }

    std::size_t arenaSize_;
    char* current_;
    char* end_;
    std::vector<char*> blocks_;
};

// Usage in a game engine:
class SceneNode {
public:
    static void* operator new(std::size_t size) {
        return currentArena_->allocate(size);
    }

    // delete is a no-op — memory is freed when the arena is reset
    static void operator delete(void*) noexcept {}

    static void setArena(ArenaAllocator* arena) { currentArena_ = arena; }

private:
    static thread_local ArenaAllocator* currentArena_;
    // ... node data ...
};
```

### Reason 5: Gathering Allocation Statistics

Before optimizing, you need data. A custom allocator can collect detailed statistics:

```cpp
#include <map>
#include <mutex>
#include <iostream>

struct AllocationStats {
    std::size_t totalAllocations = 0;
    std::size_t totalDeallocations = 0;
    std::size_t currentBytesAllocated = 0;
    std::size_t peakBytesAllocated = 0;
    std::size_t totalBytesAllocated = 0;
    std::map<std::size_t, std::size_t> sizeHistogram;  // size -> count
    std::mutex mutex;

    void recordAllocation(std::size_t size) {
        std::lock_guard<std::mutex> lock(mutex);
        ++totalAllocations;
        currentBytesAllocated += size;
        totalBytesAllocated += size;
        peakBytesAllocated = std::max(peakBytesAllocated, currentBytesAllocated);
        ++sizeHistogram[size];
    }

    void recordDeallocation(std::size_t size) {
        std::lock_guard<std::mutex> lock(mutex);
        ++totalDeallocations;
        currentBytesAllocated -= size;
    }

    void report() const {
        std::cout << "=== Allocation Statistics ===\n";
        std::cout << "Total allocations:   " << totalAllocations << "\n";
        std::cout << "Total deallocations: " << totalDeallocations << "\n";
        std::cout << "Leaked allocations:  " << (totalAllocations - totalDeallocations) << "\n";
        std::cout << "Peak memory usage:   " << peakBytesAllocated << " bytes\n";
        std::cout << "Total memory used:   " << totalBytesAllocated << " bytes\n";
        std::cout << "\nSize distribution:\n";
        for (const auto& [size, count] : sizeHistogram) {
            std::cout << "  " << size << " bytes: " << count << " allocations\n";
        }
    }
};

static AllocationStats globalStats;

void* operator new(std::size_t size) {
    // Store the size at the beginning of the block so we can track deallocation
    void* p = std::malloc(size + sizeof(std::size_t));
    if (!p) throw std::bad_alloc();
    *static_cast<std::size_t*>(p) = size;
    globalStats.recordAllocation(size);
    return static_cast<char*>(p) + sizeof(std::size_t);
}

void operator delete(void* p) noexcept {
    if (!p) return;
    void* real = static_cast<char*>(p) - sizeof(std::size_t);
    std::size_t size = *static_cast<std::size_t*>(real);
    globalStats.recordDeallocation(size);
    std::free(real);
}

// Call globalStats.report() at program exit via atexit() or a destructor
```

### Reason 6: Alignment Requirements

The default `operator new` is guaranteed to return memory aligned for any standard type (`alignof(std::max_align_t)`, typically 8 or 16 bytes). But some hardware requires stricter alignment:

```cpp
// SSE/AVX require 16-byte or 32-byte alignment
// GPU buffers may require 256-byte alignment

// BAD: Default new may not provide sufficient alignment
float* data = new float[1024];  // Only guaranteed 8- or 16-byte aligned
// __m256* avxData = reinterpret_cast<__m256*>(data);  // May crash on misaligned access!

// GOOD: Custom allocator with explicit alignment (pre-C++17)
void* alignedNew(std::size_t size, std::size_t alignment) {
    // Allocate extra space for alignment and a pointer to the real start
    std::size_t totalSize = size + alignment + sizeof(void*);
    void* rawMemory = std::malloc(totalSize);
    if (!rawMemory) throw std::bad_alloc();

    // Align the user pointer
    char* aligned = reinterpret_cast<char*>(
        (reinterpret_cast<std::uintptr_t>(rawMemory) + sizeof(void*) + alignment - 1)
        & ~(alignment - 1)
    );

    // Store the real pointer just before the aligned pointer
    reinterpret_cast<void**>(aligned)[-1] = rawMemory;
    return aligned;
}

void alignedDelete(void* p) noexcept {
    if (p) {
        std::free(reinterpret_cast<void**>(p)[-1]);
    }
}

// BETTER (C++17): Use aligned new directly
struct alignas(32) AVXData {
    float values[8];
};

// C++17 guarantees that new respects alignas for over-aligned types
AVXData* data = new AVXData[1024];  // Guaranteed 32-byte aligned in C++17

// Or use the explicit aligned allocation functions:
void* p = ::operator new(sizeof(AVXData), std::align_val_t{32});
::operator delete(p, std::align_val_t{32});
```

### When NOT to Replace new and delete

Sometimes the default allocator is perfectly fine. Do not replace it just because you can:

```cpp
// BAD: Premature optimization — replacing new/delete without profiling
// The default allocator in modern C++ runtimes (glibc, tcmalloc, jemalloc)
// is already highly optimized for most workloads.

// GOOD: Profile first, then decide
// Use tools like:
// - Valgrind (memcheck, massif)
// - AddressSanitizer / LeakSanitizer
// - HeapTrack
// - Custom profiling via LD_PRELOAD
// Only replace new/delete when you have data showing it's a bottleneck.
```

### Summary: Legitimate Reasons to Replace

| Reason | Description |
|--------|-------------|
| **Detect usage errors** | Overrun/underrun detection, double-delete detection, leak detection |
| **Improve speed** | Pool allocators for fixed-size objects, arena allocators for batch allocation |
| **Reduce memory overhead** | Eliminate per-allocation bookkeeping for small objects |
| **Reduce fragmentation** | Custom strategies for known allocation patterns |
| **Improve locality** | Cluster related objects in memory for cache performance |
| **Alignment** | Guarantee alignment beyond the default (e.g., SIMD, DMA) |
| **Statistics** | Gather data about allocation patterns to inform optimization |
| **Security** | Overwrite freed memory to prevent information leakage |

### Things to Remember

- There are many valid reasons to write custom versions of `new` and `delete`, including improving performance, debugging heap usage errors, and collecting heap usage information.

- The default allocator is a general-purpose compromise. If you understand your allocation patterns, you can often do significantly better.

- Profile before replacing. Modern allocators (tcmalloc, jemalloc, mimalloc) are very good, and replacing the global `operator new`/`delete` has program-wide consequences.

- When replacing `operator new`, always also replace `operator delete`, and vice versa. They must be a matched pair.

---

## Item 51: Adhere to Convention When Writing new and delete

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

## Item 52: Write Placement delete If You Write Placement new

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
