# Item 50: Understand When It Makes Sense to Replace new and delete

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
