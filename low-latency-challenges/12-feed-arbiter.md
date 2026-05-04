# Challenge 12: Feed Arbiter

## Leaderboard Reference

| Rank | Name | C++ | Rust |
|------|------|-----|------|
| 1st | blumper m. / Jakub Koszuliński | 17 cycles/op | 925 cycles/op |
| 2nd | Przemek S. / Baseline | 20 cycles/op | 933 cycles/op |
| 3rd | Malacarne / — | 20 cycles/op | — |

---

## Problem Description

Build a feed arbitration system. In real trading, exchanges typically provide multiple redundant market data feeds (Feed A and Feed B). A feed arbiter:

1. Receives messages from multiple feeds for the same instrument
2. Deduplicates messages (same update received from both feeds)
3. Detects and recovers from gaps (missed sequence numbers)
4. Outputs a single, clean, ordered stream of market data

---

## Core Concepts

### Why Feed Arbitration Exists

```
Exchange sends same data on two paths:

Feed A:  msg1 → msg2 → msg3 → [dropped] → msg5 → msg6
Feed B:  msg1 → msg2 → [delayed] → msg3 → msg4 → msg5 → msg6

Arbiter output: msg1 → msg2 → msg3 → msg4 → msg5 → msg6
                                        ↑ recovered from Feed B
```

Exchanges provide redundant feeds because:
- Network packets can be dropped (UDP-based feeds)
- One path may be faster than another
- Hardware failures can affect one feed but not the other

### Arbitration Rules

1. **First arrival wins** — If both feeds deliver the same message, take the first one
2. **Sequence number tracking** — Each feed has monotonically increasing sequence numbers
3. **Gap detection** — If sequence N arrives but N-1 hasn't been seen, flag a gap
4. **Gap fill** — If the other feed fills the gap, recover; otherwise request a snapshot

---

## Data Structure Design

### Core State

```cpp
struct FeedArbiter {
    // Track the next expected sequence number for the output stream
    uint64_t next_expected_seq = 1;

    // Per-feed state
    struct FeedState {
        uint64_t last_seen_seq = 0;
        bool is_active = true;
    };

    FeedState feeds[2];  // Feed A (0) and Feed B (1)

    // Deduplication: track which sequence numbers we've already processed
    // Use a bitmap for O(1) lookup
    static constexpr int WINDOW_SIZE = 65536;  // Track last 64K messages
    static constexpr int WINDOW_MASK = WINDOW_SIZE - 1;
    uint64_t processed_bitmap[WINDOW_SIZE / 64] = {};

    bool is_processed(uint64_t seq) const {
        int word = (seq & WINDOW_MASK) / 64;
        int bit = (seq & WINDOW_MASK) % 64;
        return (processed_bitmap[word] >> bit) & 1;
    }

    void mark_processed(uint64_t seq) {
        int word = (seq & WINDOW_MASK) / 64;
        int bit = (seq & WINDOW_MASK) % 64;
        processed_bitmap[word] |= (1ULL << bit);
    }

    enum Result { ACCEPTED, DUPLICATE, GAP_DETECTED };

    Result on_message(int feed_id, uint64_t seq, const void* data) {
        // Already seen this sequence number?
        if (is_processed(seq)) {
            return DUPLICATE;
        }

        // Gap detection
        if (seq > next_expected_seq) {
            // Messages between next_expected_seq and seq-1 are missing
            return GAP_DETECTED;
        }

        // Accept and process
        mark_processed(seq);
        feeds[feed_id].last_seen_seq = seq;

        if (seq == next_expected_seq) {
            next_expected_seq++;
            // Check if we can advance further (buffered out-of-order messages)
            while (is_processed(next_expected_seq)) {
                next_expected_seq++;
            }
        }

        return ACCEPTED;
    }
};
```

### Optimized Version: Branchless Arbitration

```cpp
struct FastArbiter {
    static constexpr int BITMAP_SIZE = 1024;  // 1024 × 64 = 65536 bits
    static constexpr int SEQ_MASK = 65535;

    alignas(64) uint64_t bitmap[BITMAP_SIZE] = {};
    uint64_t next_seq = 1;

    // Returns true if message should be processed (not duplicate)
    bool arbitrate(uint64_t seq) {
        int word = (seq >> 6) & (BITMAP_SIZE - 1);
        uint64_t bit = 1ULL << (seq & 63);

        // Test-and-set in one operation
        bool is_new = !(bitmap[word] & bit);
        bitmap[word] |= bit;

        // Advance next_seq if this was the next expected
        // Branchless: only advances if seq == next_seq
        next_seq += (seq == next_seq);

        return is_new;
    }

    // Bulk advance past consecutive processed sequences
    void advance_sequence() {
        while (true) {
            int word = (next_seq >> 6) & (BITMAP_SIZE - 1);
            uint64_t bit = 1ULL << (next_seq & 63);
            if (!(bitmap[word] & bit)) break;
            next_seq++;
        }
    }

    // Periodically clear old bitmap entries
    void clear_old(uint64_t up_to_seq) {
        int start_word = ((up_to_seq - 65536) >> 6) & (BITMAP_SIZE - 1);
        int end_word = (up_to_seq >> 6) & (BITMAP_SIZE - 1);
        // Clear words that are fully behind us
        // (careful with wraparound)
    }
};
```

### With Out-of-Order Buffering

```cpp
struct BufferingArbiter {
    static constexpr int BUFFER_SIZE = 4096;

    struct BufferedMsg {
        uint64_t seq;
        char data[64];  // Message payload
        bool valid;
    };

    BufferedMsg buffer[BUFFER_SIZE];
    uint64_t bitmap[1024] = {};
    uint64_t next_seq = 1;

    template<typename Callback>
    void on_message(uint64_t seq, const void* data, int len, Callback&& cb) {
        // Dedup
        int word = (seq >> 6) & 1023;
        uint64_t bit = 1ULL << (seq & 63);
        if (bitmap[word] & bit) return;  // Duplicate
        bitmap[word] |= bit;

        if (seq == next_seq) {
            // In-order: process immediately
            cb(seq, data, len);
            next_seq++;

            // Drain buffer
            while (buffer[next_seq & (BUFFER_SIZE - 1)].valid &&
                   buffer[next_seq & (BUFFER_SIZE - 1)].seq == next_seq) {
                auto& b = buffer[next_seq & (BUFFER_SIZE - 1)];
                cb(b.seq, b.data, sizeof(b.data));
                b.valid = false;
                next_seq++;
            }
        } else if (seq > next_seq) {
            // Out of order: buffer for later
            auto& slot = buffer[seq & (BUFFER_SIZE - 1)];
            slot.seq = seq;
            memcpy(slot.data, data, len);
            slot.valid = true;
        }
        // seq < next_seq: already processed, ignore
    }
};
```

---

## Optimization Techniques

### 1. Bitmap-Based Deduplication

```cpp
// O(1) dedup using bitmap test-and-set
// Much faster than hash set or sorted array

bool test_and_set(uint64_t seq) {
    uint64_t& word = bitmap[(seq >> 6) & BITMAP_MASK];
    uint64_t bit = 1ULL << (seq & 63);
    bool was_set = word & bit;
    word |= bit;
    return !was_set;  // true if newly set
}
```

### 2. Branch Prediction Hints

```cpp
// Most messages arrive in order → optimize for that case
if (__builtin_expect(seq == next_seq, 1)) {
    // Fast path: in-order message
    process(data);
    next_seq++;
} else if (__builtin_expect(seq > next_seq, 0)) {
    // Slow path: gap detected
    buffer_message(seq, data);
}
```

### 3. Sequence Advance with CTZ

```cpp
// When draining buffered messages, use ctz to skip consecutive set bits
void advance_fast() {
    while (true) {
        int word_idx = (next_seq >> 6) & BITMAP_MASK;
        int bit_pos = next_seq & 63;

        uint64_t remaining = bitmap[word_idx] >> bit_pos;
        if (remaining == 0) break;

        // Count trailing zeros → number of unset bits before next set bit
        // But we want trailing ONES (consecutive processed messages)
        uint64_t consecutive = ~remaining;
        if (consecutive == 0) {
            // All remaining bits are set
            next_seq += 64 - bit_pos;
            continue;
        }
        int advance = __builtin_ctzll(consecutive);
        next_seq += advance;
        if (advance == 0) break;
    }
}
```

---

## Benchmarking

### Workload

```cpp
// Simulate dual-feed with realistic characteristics:
// - Feed A arrives ~2μs before Feed B on average
// - 0.01% packet loss per feed
// - 99.9% of messages arrive in order
// - Sequence numbers are dense (no gaps in numbering)

struct FeedMessage {
    int feed_id;      // 0 or 1
    uint64_t seq;
    uint64_t timestamp;
    char data[32];
};

std::vector<FeedMessage> generate_workload(int n) {
    std::vector<FeedMessage> msgs;
    std::mt19937 rng(42);

    for (uint64_t seq = 1; seq <= n; ++seq) {
        // Feed A
        if (rng() % 10000 != 0) {  // 0.01% drop rate
            msgs.push_back({0, seq, seq * 1000, {}});
        }
        // Feed B (arrives later)
        if (rng() % 10000 != 0) {
            msgs.push_back({1, seq, seq * 1000 + 2000, {}});
        }
    }

    // Sort by arrival time
    std::sort(msgs.begin(), msgs.end(),
              [](auto& a, auto& b) { return a.timestamp < b.timestamp; });
    return msgs;
}
```

### Target Metrics

| Metric | Elite | Good | Needs Work |
|--------|-------|------|------------|
| cycles/op | < 20 | 20-50 | > 50 |
| Duplicate rejection | < 5 cycles | 5-15 cycles | > 15 cycles |
| Gap recovery | < 30 cycles | 30-100 cycles | > 100 cycles |

---

## C++ vs Rust Gap

Massive gap (17 vs 925 cycles/op). Likely causes:
1. The Rust baseline implementations may not be heavily optimized yet
2. Bitmap operations with bounds checking add overhead in Rust
3. The C++ solutions likely use very compact, branchless code paths

---

## Common Pitfalls

1. **Using `std::set`/`BTreeSet` for dedup** — O(log n); use bitmap for O(1)
2. **Not caching the next expected sequence** — Forces full bitmap scan on every message
3. **Handling gaps by requesting snapshots immediately** — Buffer briefly; the other feed may fill the gap
4. **Forgetting to clear old bitmap entries** — Bitmap wraps around; old entries cause false dedup
5. **Processing out-of-order messages immediately** — Must buffer and deliver in sequence order
