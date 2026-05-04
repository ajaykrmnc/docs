# Challenge 09: FIX Parser

## Leaderboard Reference

| Rank | Name | C++ | Rust |
|------|------|-----|------|
| 1st | Przemek S. / Jakub Koszuliński | 696 cycles/KB | 741 cycles/op |
| 2nd | Malacarne / Baseline | 760 cycles/KB | 743 cycles/op |
| 3rd | blumper m. / — | 761 cycles/KB | — |

---

## Problem Description

Build a high-performance FIX protocol parser for order messages.

**FIX (Financial Information eXchange)** is the dominant protocol for electronic trading. Every order, execution report, and market data update flows as FIX messages.

---

## FIX Protocol Primer

### Message Format

FIX messages are ASCII text with fields separated by the SOH character (0x01):

```
8=FIX.4.4|9=176|35=D|49=SENDER|56=TARGET|34=1|52=20230601-12:00:00.000|
11=ORDER123|55=AAPL|54=1|38=100|40=2|44=150.50|59=0|10=128|

Where | represents SOH (0x01)
```

### Field Structure

Each field is: `TAG=VALUE<SOH>`

- **Tag**: Integer field identifier (e.g., 35 = MsgType, 55 = Symbol)
- **Value**: String, integer, float, or timestamp
- **SOH**: Field separator (ASCII 0x01)

### Key Fields for Order Messages

| Tag | Name | Example | Description |
|-----|------|---------|-------------|
| 8 | BeginString | FIX.4.4 | Protocol version |
| 9 | BodyLength | 176 | Message body length |
| 35 | MsgType | D | New Order Single |
| 11 | ClOrdID | ORDER123 | Client order ID |
| 55 | Symbol | AAPL | Ticker symbol |
| 54 | Side | 1 | 1=Buy, 2=Sell |
| 38 | OrderQty | 100 | Quantity |
| 40 | OrdType | 2 | 1=Market, 2=Limit |
| 44 | Price | 150.50 | Limit price |
| 10 | Checksum | 128 | Message checksum |

---

## Parsing Approaches

### Approach 1: Naive — Linear Scan with String Operations

```cpp
// BAD: ~5000+ cycles/KB
struct NaiveParser {
    struct ParsedOrder {
        char cl_ord_id[32];
        char symbol[16];
        int side;
        int qty;
        double price;
    };

    ParsedOrder parse(const char* msg, int len) {
        ParsedOrder order{};
        const char* pos = msg;
        const char* end = msg + len;

        while (pos < end) {
            // Find '='
            const char* eq = (const char*)memchr(pos, '=', end - pos);
            if (!eq) break;

            int tag = atoi_simple(pos, eq - pos);

            // Find SOH
            const char* soh = (const char*)memchr(eq + 1, '\x01', end - eq - 1);
            if (!soh) break;

            int vlen = soh - eq - 1;

            switch (tag) {
                case 11: memcpy(order.cl_ord_id, eq + 1, vlen); break;
                case 55: memcpy(order.symbol, eq + 1, vlen); break;
                case 54: order.side = eq[1] - '0'; break;
                case 38: order.qty = atoi_simple(eq + 1, vlen); break;
                case 44: order.price = parse_double(eq + 1, vlen); break;
            }

            pos = soh + 1;
        }
        return order;
    }
};
```

### Approach 2: Optimized — SIMD SOH Scanning

```cpp
#include <immintrin.h>

struct SimdParser {
    // Find all SOH (0x01) positions using SIMD
    // Then parse fields between consecutive SOH positions

    void find_soh_positions(const char* msg, int len, int* positions, int& count) {
        __m256i soh = _mm256_set1_epi8(0x01);
        count = 0;

        for (int i = 0; i + 32 <= len; i += 32) {
            __m256i chunk = _mm256_loadu_si256((__m256i*)(msg + i));
            __m256i cmp = _mm256_cmpeq_epi8(chunk, soh);
            uint32_t mask = _mm256_movemask_epi8(cmp);

            while (mask) {
                int bit = __builtin_ctz(mask);
                positions[count++] = i + bit;
                mask &= mask - 1;
            }
        }

        // Handle remainder
        for (int i = (len / 32) * 32; i < len; ++i) {
            if (msg[i] == 0x01) positions[count++] = i;
        }
    }

    // Also SIMD-scan for '=' characters
    void find_eq_positions(const char* msg, int len, int* positions, int& count) {
        __m256i eq = _mm256_set1_epi8('=');
        count = 0;
        for (int i = 0; i + 32 <= len; i += 32) {
            __m256i chunk = _mm256_loadu_si256((__m256i*)(msg + i));
            uint32_t mask = _mm256_movemask_epi8(_mm256_cmpeq_epi8(chunk, eq));
            while (mask) {
                positions[count++] = i + __builtin_ctz(mask);
                mask &= mask - 1;
            }
        }
    }
};
```

### Approach 3: State Machine Parser (Branchless)

```cpp
// Parse the tag number as we scan bytes, avoiding atoi altogether
// Recognize common 1-2 digit tags without branching

struct StateMachineParser {
    enum State { READING_TAG, READING_VALUE };

    struct ParsedMessage {
        int64_t values[256];       // Direct-indexed by tag number
        const char* strings[256];  // Pointers into original message
        int lengths[256];
    };

    void parse(const char* msg, int len, ParsedMessage& result) {
        int tag = 0;
        State state = READING_TAG;
        const char* value_start = nullptr;

        for (int i = 0; i < len; ++i) {
            char c = msg[i];

            if (state == READING_TAG) {
                if (c == '=') {
                    state = READING_VALUE;
                    value_start = msg + i + 1;
                } else {
                    tag = tag * 10 + (c - '0');
                }
            } else {
                if (c == 0x01) {
                    // End of value
                    int vlen = (msg + i) - value_start;
                    result.strings[tag] = value_start;
                    result.lengths[tag] = vlen;

                    // Parse numeric values inline
                    if (tag < 256) {
                        result.values[tag] = parse_int_fast(value_start, vlen);
                    }

                    tag = 0;
                    state = READING_TAG;
                }
            }
        }
    }

    static int64_t parse_int_fast(const char* s, int len) {
        int64_t val = 0;
        for (int i = 0; i < len; ++i) {
            val = val * 10 + (s[i] - '0');
        }
        return val;
    }
};
```

### Approach 4: Zero-Copy with Tag Jump Table

```cpp
// For known message types, pre-build a jump table of expected tag positions
// Skip directly to fields of interest

struct JumpTableParser {
    // For a NewOrderSingle (35=D), we know which tags to expect:
    // Tags: 11, 38, 40, 44, 54, 55
    // Build a 256-entry lookup: tag → handler function

    using Handler = void(*)(const char* value, int len, void* output);
    Handler handlers[256] = {};

    JumpTableParser() {
        handlers[11] = [](const char* v, int l, void* o) {
            memcpy(((ParsedOrder*)o)->cl_ord_id, v, l);
        };
        handlers[55] = [](const char* v, int l, void* o) {
            memcpy(((ParsedOrder*)o)->symbol, v, l);
        };
        handlers[54] = [](const char* v, int l, void* o) {
            ((ParsedOrder*)o)->side = v[0] - '0';
        };
        handlers[38] = [](const char* v, int l, void* o) {
            ((ParsedOrder*)o)->qty = parse_int_fast(v, l);
        };
        handlers[44] = [](const char* v, int l, void* o) {
            ((ParsedOrder*)o)->price = parse_price_fast(v, l);
        };
    }

    void parse(const char* msg, int len, ParsedOrder& order) {
        int tag = 0;
        const char* vstart = nullptr;

        for (int i = 0; i < len; ++i) {
            if (msg[i] == '=') {
                vstart = msg + i + 1;
            } else if (msg[i] == 0x01) {
                if (tag < 256 && handlers[tag]) {
                    handlers[tag](vstart, (msg + i) - vstart, &order);
                }
                tag = 0;
            } else if (!vstart || msg + i < vstart) {
                tag = tag * 10 + (msg[i] - '0');
            }
        }
    }
};
```

---

## Number Parsing Optimization

### Fast Integer Parsing

```cpp
// Parsing "12345" → 12345 without atoi()

// Unrolled for common lengths (1-6 digits)
inline int parse_int_branchless(const char* s, int len) {
    // SWAR (SIMD Within A Register) approach
    uint64_t val;
    memcpy(&val, s, 8);

    // Subtract '0' from each byte
    val -= 0x3030303030303030ULL;

    // Mask unused bytes
    val &= (1ULL << (len * 8)) - 1;

    // Multiply-accumulate using magic constants
    val = (val * 10 + (val >> 8)) & 0x00FF00FF00FF00FFULL;
    val = (val * 100 + (val >> 16)) & 0x0000FFFF0000FFFFULL;
    val = (val * 10000 + (val >> 32)) & 0x00000000FFFFFFFFULL;

    return (int)val;
}
```

### Fast Price Parsing (Fixed-Point)

```cpp
// Parse "150.50" as fixed-point integer (15050 with scale 100)
// Avoids floating-point entirely

struct FixedPrice {
    int64_t mantissa;  // 15050
    int8_t decimals;   // 2

    static FixedPrice parse(const char* s, int len) {
        FixedPrice p{0, 0};
        bool after_dot = false;
        for (int i = 0; i < len; ++i) {
            if (s[i] == '.') {
                after_dot = true;
            } else {
                p.mantissa = p.mantissa * 10 + (s[i] - '0');
                if (after_dot) p.decimals++;
            }
        }
        return p;
    }
};
```

---

## Benchmarking

### Workload

```cpp
// Generate realistic FIX messages
std::string generate_new_order() {
    char buf[512];
    int len = snprintf(buf, sizeof(buf),
        "8=FIX.4.4\x01"
        "9=176\x01"
        "35=D\x01"
        "49=SENDER01\x01"
        "56=TARGET01\x01"
        "34=12345\x01"
        "52=20230601-12:00:00.000\x01"
        "11=ORD%06d\x01"
        "55=AAPL\x01"
        "54=1\x01"
        "38=100\x01"
        "40=2\x01"
        "44=150.50\x01"
        "59=0\x01"
        "10=128\x01",
        rand() % 1000000);
    return std::string(buf, len);
}
```

### Measurement

```cpp
void benchmark() {
    auto messages = generate_messages(100000);
    size_t total_bytes = 0;
    for (auto& m : messages) total_bytes += m.size();

    uint64_t start = __rdtsc();
    for (auto& m : messages) {
        ParsedOrder order;
        parser.parse(m.data(), m.size(), order);
    }
    uint64_t elapsed = __rdtsc() - start;

    double kb = total_bytes / 1024.0;
    printf("%.0f cycles/KB\n", elapsed / kb);
}
```

### Target Metrics

| Metric | Elite | Good | Needs Work |
|--------|-------|------|------------|
| cycles/KB | < 750 | 750-1500 | > 1500 |
| Throughput | > 4 GB/s | 2-4 GB/s | < 2 GB/s |
| Branch miss rate | < 1% | 1-3% | > 3% |

---

## Common Pitfalls

1. **Using `std::string` for field values** — Zero-copy: store pointers into the original message buffer
2. **Calling `atoi()`/`atof()`** — Locale-aware, slow; use inline integer parsing
3. **`switch` on tag with many cases** — Use a lookup table (array indexed by tag number)
4. **Scanning byte-by-byte for SOH** — Use SIMD to find delimiters in 32-byte chunks
5. **Parsing all fields** — Only parse fields you need; skip unknown tags
6. **Dynamic memory allocation** — Pre-allocate parse result buffer
