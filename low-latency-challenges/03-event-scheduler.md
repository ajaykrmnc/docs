# Challenge 03: Event Scheduler (With Cancellation)

## Leaderboard Reference

| Rank | Name | C++ | Rust |
|------|------|-----|------|
| 1st | Suntae L. / Hang | 682 cycles/op | 1426 cycles/op |
| 2nd | Roman Sztergbaum / Baseline | 768 cycles/op | 5952 cycles/op |
| 3rd | Przemek S. / Roman Sztergbaum | 868 cycles/op | 5952 cycles/op |

---

## Problem Description

Build a high-performance event scheduler that can handle millions of pending events with these operations:

1. **Schedule** — Add an event to fire at a future timestamp
2. **Cancel** — Remove a previously scheduled event before it fires
3. **Advance** — Move current time forward and fire all events whose timestamp ≤ current time
4. **Peek** — Check the next event to fire without removing it

This simulates the timer infrastructure in a trading system (e.g., order timeouts, heartbeat timers, scheduled auctions).

---

## Core Concepts

### Why This Is Hard

The naive approach (sorted list or `std::priority_queue`) fails because:
- `std::priority_queue` doesn't support O(1) cancel — you must lazy-delete or rebuild
- Sorted lists have O(n) insertion
- Tree-based structures (e.g., `std::set`) have O(log n) everything but terrible cache behavior

The challenge demands a data structure that supports all three operations efficiently with minimal overhead.

---

## Data Structure Options

### Option 1: Timer Wheel (Hashed Timing Wheel)

The gold standard for high-performance timer management. Used in Linux kernel, DPDK, and most trading systems.

```
┌───────────────────────────────────────────────────┐
│                    Timer Wheel                     │
│                                                    │
│  Slot 0: [Event A] → [Event D] → NULL             │
│  Slot 1: [Event B] → NULL                         │
│  Slot 2: (empty)                                   │
│  Slot 3: [Event C] → [Event F] → [Event G] → NULL │
│  ...                                               │
│  Slot N-1: [Event E] → NULL                       │
│                                                    │
│  Current pointer: ──→ Slot 0                       │
│  Tick resolution: 1 unit                           │
└───────────────────────────────────────────────────┘
```

```cpp
static constexpr int WHEEL_SIZE = 65536;  // Power of 2 for fast modulo
static constexpr int WHEEL_MASK = WHEEL_SIZE - 1;

struct TimerWheel {
    struct Event {
        uint64_t deadline;
        uint32_t id;
        int32_t next;  // Intrusive list
        int32_t prev;
        bool cancelled;
    };

    int32_t slots[WHEEL_SIZE];  // Head of each slot's linked list
    Event events[MAX_EVENTS];   // Pool-allocated events
    uint64_t current_tick;

    void schedule(uint32_t id, uint64_t deadline) {
        int slot = deadline & WHEEL_MASK;
        auto& e = events[id];
        e.deadline = deadline;
        e.id = id;
        e.cancelled = false;
        // Insert at head of slot's list
        e.next = slots[slot];
        e.prev = -1;
        if (slots[slot] != -1) events[slots[slot]].prev = id;
        slots[slot] = id;
    }

    void cancel(uint32_t id) {
        auto& e = events[id];
        e.cancelled = true;
        // Remove from linked list
        if (e.prev != -1) events[e.prev].next = e.next;
        else slots[e.deadline & WHEEL_MASK] = e.next;
        if (e.next != -1) events[e.next].prev = e.prev;
    }

    // Advance time and fire all due events
    template<typename Callback>
    void advance(uint64_t new_tick, Callback&& cb) {
        while (current_tick < new_tick) {
            int slot = current_tick & WHEEL_MASK;
            int cur = slots[slot];
            while (cur != -1) {
                auto& e = events[cur];
                int next = e.next;
                if (!e.cancelled && e.deadline <= current_tick) {
                    cb(e.id);
                    // Remove from list
                    remove_from_slot(cur, slot);
                }
                cur = next;
            }
            ++current_tick;
        }
    }
};
```

**Complexity:**
- Schedule: O(1)
- Cancel: O(1) with intrusive list
- Advance: O(1) amortized per expired event

### Option 2: Hierarchical Timer Wheel

For large time ranges, use multiple wheels at different granularities:

```
┌─────────────────────────────────────────────┐
│  Level 0 (fine):   256 slots × 1 tick each  │
│  Level 1 (medium): 256 slots × 256 ticks    │
│  Level 2 (coarse): 256 slots × 65536 ticks  │
└─────────────────────────────────────────────┘

When level 0 wraps around, cascade events from level 1 into level 0.
Like an odometer rolling over.
```

```cpp
struct HierarchicalWheel {
    static constexpr int BITS = 8;
    static constexpr int SLOTS = 1 << BITS;   // 256
    static constexpr int MASK = SLOTS - 1;
    static constexpr int LEVELS = 4;           // 4 levels = 32-bit time range

    int32_t wheels[LEVELS][SLOTS];  // Each slot is a linked list head
    uint64_t current_time = 0;

    int level_for(uint64_t deadline) {
        uint64_t diff = deadline - current_time;
        if (diff < SLOTS) return 0;
        if (diff < SLOTS * SLOTS) return 1;
        if (diff < SLOTS * SLOTS * SLOTS) return 2;
        return 3;
    }

    int slot_for(uint64_t deadline, int level) {
        return (deadline >> (level * BITS)) & MASK;
    }

    void schedule(uint32_t id, uint64_t deadline) {
        int lvl = level_for(deadline);
        int slot = slot_for(deadline, lvl);
        insert_into_list(wheels[lvl][slot], id);
        events[id].deadline = deadline;
    }

    void cascade(int level) {
        // Move events from higher level down to lower level
        int slot = slot_for(current_time, level);
        int cur = wheels[level][slot];
        wheels[level][slot] = -1;
        while (cur != -1) {
            int next = events[cur].next;
            int new_lvl = level_for(events[cur].deadline);
            int new_slot = slot_for(events[cur].deadline, new_lvl);
            insert_into_list(wheels[new_lvl][new_slot], cur);
            cur = next;
        }
    }
};
```

### Option 3: 4-ary Min-Heap with Lazy Cancel

```cpp
// A 4-ary heap has better cache performance than binary heap
// Use lazy cancellation — mark events as cancelled, skip them during pop

struct HeapScheduler {
    struct Entry {
        uint64_t deadline;
        uint32_t id;
    };

    Entry heap[MAX_EVENTS];
    int size = 0;
    bool cancelled[MAX_EVENTS] = {};

    void schedule(uint32_t id, uint64_t deadline) {
        heap[size] = {deadline, id};
        sift_up(size);
        ++size;
    }

    void cancel(uint32_t id) {
        cancelled[id] = true;  // Lazy cancel
    }

    uint32_t pop_next() {
        while (size > 0) {
            auto top = heap[0];
            pop_heap();
            if (!cancelled[top.id]) return top.id;
        }
        return UINT32_MAX;  // No events
    }

private:
    void sift_up(int i) {
        while (i > 0) {
            int parent = (i - 1) / 4;
            if (heap[i].deadline < heap[parent].deadline) {
                std::swap(heap[i], heap[parent]);
                i = parent;
            } else break;
        }
    }

    void sift_down(int i) {
        while (true) {
            int best = i;
            for (int c = 0; c < 4; ++c) {
                int child = 4 * i + 1 + c;
                if (child < size && heap[child].deadline < heap[best].deadline)
                    best = child;
            }
            if (best == i) break;
            std::swap(heap[i], heap[best]);
            i = best;
        }
    }
};
```

---

## Optimization Techniques

### 1. Pool Allocator for Events

```cpp
struct EventPool {
    struct Event {
        uint64_t deadline;
        uint32_t id;
        int32_t next, prev;
        bool active;
    };

    Event pool[MAX_EVENTS];
    int32_t free_head = 0;

    EventPool() {
        for (int i = 0; i < MAX_EVENTS - 1; i++)
            pool[i].next = i + 1;
        pool[MAX_EVENTS - 1].next = -1;
    }

    int32_t alloc() {
        int32_t id = free_head;
        free_head = pool[free_head].next;
        return id;
    }

    void free(int32_t id) {
        pool[id].next = free_head;
        free_head = id;
    }
};
```

### 2. Branchless Slot Selection

```cpp
// Power-of-2 wheel size means modulo is just a bitwise AND
int slot = deadline & WHEEL_MASK;  // No division, no branch

// For hierarchical wheels, use shift + mask
int slot_level0 = deadline & 0xFF;
int slot_level1 = (deadline >> 8) & 0xFF;
int slot_level2 = (deadline >> 16) & 0xFF;
```

### 3. Batch Advance

```cpp
// Instead of ticking one unit at a time, jump to next non-empty slot
void advance_fast(uint64_t target) {
    while (current_tick < target) {
        int slot = current_tick & WHEEL_MASK;
        if (slots[slot] != -1) {
            // Process this slot
            fire_slot(slot);
        }
        ++current_tick;
    }
}

// Even better: skip empty slots entirely using a bitmap
uint64_t slot_bitmap[WHEEL_SIZE / 64];  // 1 bit per slot

void advance_bitmap(uint64_t target) {
    while (current_tick < target) {
        int word = (current_tick & WHEEL_MASK) / 64;
        int bit = (current_tick & WHEEL_MASK) % 64;
        uint64_t mask = slot_bitmap[word] >> bit;
        if (mask == 0) {
            // Skip to next word boundary or target
            current_tick += 64 - bit;
            continue;
        }
        int skip = __builtin_ctzll(mask);
        current_tick += skip;
        if (current_tick >= target) break;
        fire_slot(current_tick & WHEEL_MASK);
        ++current_tick;
    }
}
```

---

## Benchmarking

### Workload Profile

```cpp
// Typical trading system timer workload:
// - Schedule: 40% of ops (new order timeouts, heartbeats)
// - Cancel: 35% of ops (order fills cancel their timeout timers)
// - Advance: 20% of ops (time progression)
// - Peek: 5% of ops

// Deadline distribution:
// - 70% near-term (within 1000 ticks)
// - 20% medium-term (1000-100000 ticks)
// - 10% long-term (100000+ ticks)
```

### Measurement Code

```cpp
void benchmark() {
    Scheduler sched;
    auto ops = generate_mixed_workload(1'000'000);

    // Warmup
    for (int i = 0; i < 10'000; i++) execute(sched, ops[i]);

    // Measure
    uint64_t start = __rdtsc();
    for (auto& op : ops) execute(sched, op);
    uint64_t end = __rdtsc();

    printf("Avg: %lu cycles/op\n", (end - start) / ops.size());
}
```

### Profiling Focus Areas

```bash
# Cache behavior — timer wheels can be large
perf stat -e L1-dcache-load-misses,LLC-load-misses ./bench

# Branch mispredictions — especially during advance (scanning empty slots)
perf stat -e branch-misses ./bench

# TLB misses — large data structures can thrash TLB
perf stat -e dTLB-load-misses ./bench
```

### Target Metrics

| Metric | Elite | Good | Needs Work |
|--------|-------|------|------------|
| cycles/op | < 750 | 750-1500 | > 1500 |
| Cancel overhead | < 10 cycles | 10-50 cycles | > 50 cycles |
| Empty slot skip rate | > 90% | 70-90% | < 70% |

---

## Common Pitfalls

1. **Using `std::priority_queue`** — No O(1) cancel; lazy deletion adds overhead during pop
2. **Ticking one unit at a time** — Use bitmap or skip-ahead for sparse event distributions
3. **Hash map for event lookup** — Use direct-indexed array by event ID
4. **Not handling time wraparound** — Use unsigned arithmetic and proper masking
5. **Cascading too frequently** — In hierarchical wheels, minimize cascade frequency
