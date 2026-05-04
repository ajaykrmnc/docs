# Challenge 10: FIX Encoder

## Leaderboard Reference

| Rank | Name | C++ | Rust |
|------|------|-----|------|
| 1st | blumper m. / Baseline | 107 cycles/msg | 3831 cycles/op |
| 2nd | Przemek S. / Jakub Koszuliński | 118 cycles/msg | 3909 cycles/op |
| 3rd | Malacarne / — | 161 cycles/msg | — |

---

## Problem Description

Build a high-performance FIX message encoder for order entry. Convert structured order data into FIX protocol wire format.

This is the inverse of Challenge 09. While parsing breaks messages apart, encoding assembles them.

---

## What Makes Encoding Hard

The challenge is not logical complexity — it's raw throughput. Each message requires:
1. Convert integers to ASCII decimal strings
2. Convert prices/doubles to ASCII with correct precision
3. Concatenate tag=value pairs with SOH delimiters
4. Calculate body length (tag 9) and checksum (tag 10)
5. Build the message header (tags 8, 9) and trailer (tag 10)

**The body length problem**: You need to know the length of the body to write tag 9, but you haven't written the body yet. This forces either two passes or a clever single-pass approach.

---

## Encoding Approaches

### Approach 1: Template-Based Encoding

```cpp
// Pre-build message templates with placeholder positions
// At encoding time, just fill in the variable parts

struct TemplateEncoder {
    // Template for NewOrderSingle (35=D)
    // Fields with known positions:
    // "8=FIX.4.4\x019=XXX\x0135=D\x0149=SENDER\x0156=TARGET\x01..."

    char template_buf[512];
    int template_len;

    // Positions of variable fields in the template
    int body_len_pos;    // Where to write tag 9 value
    int cl_ord_id_pos;   // Where to write tag 11 value
    int symbol_pos;      // Where to write tag 55 value
    int side_pos;        // Where to write tag 54 value
    int qty_pos;         // Where to write tag 38 value
    int price_pos;       // Where to write tag 44 value
    int checksum_pos;    // Where to write tag 10 value

    void build_template() {
        // Pre-fill all static parts
        // Mark variable positions
        // This is called once at startup
    }

    int encode(char* out, const Order& order) {
        // Copy template
        memcpy(out, template_buf, template_len);

        // Fill in variable fields
        int len = template_len;
        len += write_string(out + cl_ord_id_pos, order.cl_ord_id);
        len += write_string(out + symbol_pos, order.symbol);
        out[side_pos] = '0' + order.side;
        len += write_int(out + qty_pos, order.qty);
        len += write_price(out + price_pos, order.price);

        // Calculate and write body length
        write_body_length(out + body_len_pos, len);

        // Calculate and write checksum
        write_checksum(out + checksum_pos, out, len);

        return len;
    }
};
```

### Approach 2: Sequential Write with Fast Integer-to-String

```cpp
struct SequentialEncoder {
    // Write directly into output buffer, field by field
    // Use a two-phase approach:
    // Phase 1: Write body (all fields except 8, 9, 10) into a temp buffer
    // Phase 2: Write header (8, 9) + body + trailer (10) into final buffer

    int encode(char* out, const Order& order) {
        char body[512];
        char* p = body;

        // Write body fields
        p = write_field(p, 35, "D", 1);
        p = write_field(p, 49, "SENDER", 6);
        p = write_field(p, 56, "TARGET", 6);
        p = write_int_field(p, 34, order.seq_num);
        p = write_field(p, 11, order.cl_ord_id, strlen(order.cl_ord_id));
        p = write_field(p, 55, order.symbol, strlen(order.symbol));
        p = write_int_field(p, 54, order.side);
        p = write_int_field(p, 38, order.qty);
        p = write_price_field(p, 44, order.price);

        int body_len = p - body;

        // Write header
        char* out_p = out;
        out_p = write_field(out_p, 8, "FIX.4.4", 7);
        out_p = write_int_field(out_p, 9, body_len);

        // Copy body
        memcpy(out_p, body, body_len);
        out_p += body_len;

        // Calculate checksum
        uint8_t sum = 0;
        for (char* c = out; c < out_p; ++c) sum += (uint8_t)*c;
        char chk[4];
        snprintf(chk, 4, "%03d", sum % 256);
        out_p = write_field(out_p, 10, chk, 3);

        return out_p - out;
    }

private:
    char* write_field(char* p, int tag, const char* val, int vlen) {
        p += itoa_fast(p, tag);
        *p++ = '=';
        memcpy(p, val, vlen);
        p += vlen;
        *p++ = 0x01;
        return p;
    }
};
```

### Approach 3: Single-Pass with Reserved Space

```cpp
struct SinglePassEncoder {
    // Reserve space for header, write body, then go back and fill header

    int encode(char* out, const Order& order) {
        // Reserve 20 bytes for "8=FIX.4.4\x019=XXX\x01"
        // (body length is typically 3 digits)
        static constexpr int HEADER_RESERVE = 20;

        char* body_start = out + HEADER_RESERVE;
        char* p = body_start;

        // Write body directly
        p = write_tag_value(p, 35, 'D');
        p = write_tag_str(p, 49, "SENDER");
        p = write_tag_str(p, 56, "TARGET");
        p = write_tag_int(p, 34, order.seq_num);
        p = write_tag_str(p, 11, order.cl_ord_id);
        p = write_tag_str(p, 55, order.symbol);
        p = write_tag_int(p, 54, order.side);
        p = write_tag_int(p, 38, order.qty);
        p = write_tag_price(p, 44, order.price);

        int body_len = p - body_start;

        // Go back and write header with exact body length
        char header[20];
        char* h = header;
        memcpy(h, "8=FIX.4.4\x01", 11);
        h += 11;
        h += sprintf(h, "9=%d\x01", body_len);

        int header_len = h - header;

        // Shift body if header is shorter than reserved space
        if (header_len < HEADER_RESERVE) {
            memmove(out + header_len, body_start, body_len);
        }
        memcpy(out, header, header_len);

        // Checksum
        char* msg_end = out + header_len + body_len;
        uint8_t sum = 0;
        for (char* c = out; c < msg_end; ++c) sum += (uint8_t)*c;
        msg_end += sprintf((char*)msg_end, "10=%03d\x01", sum % 256);

        return msg_end - out;
    }
};
```

---

## Critical Speed Techniques

### 1. Fast Integer-to-String (itoa)

```cpp
// The biggest bottleneck is converting integers to decimal ASCII

// Lookup table approach (2 digits at a time)
static const char digit_pairs[200] = {
    '0','0','0','1','0','2','0','3','0','4',
    '0','5','0','6','0','7','0','8','0','9',
    '1','0','1','1','1','2','1','3','1','4',
    // ... up to '9','9'
};

int itoa_fast(char* buf, uint32_t val) {
    if (val < 10) {
        buf[0] = '0' + val;
        return 1;
    }
    if (val < 100) {
        memcpy(buf, &digit_pairs[val * 2], 2);
        return 2;
    }

    // For larger numbers, divide by 100 and use pairs
    char temp[12];
    int pos = 12;
    while (val >= 100) {
        uint32_t remainder = val % 100;
        val /= 100;
        pos -= 2;
        memcpy(temp + pos, &digit_pairs[remainder * 2], 2);
    }
    if (val >= 10) {
        pos -= 2;
        memcpy(temp + pos, &digit_pairs[val * 2], 2);
    } else {
        temp[--pos] = '0' + val;
    }

    int len = 12 - pos;
    memcpy(buf, temp + pos, len);
    return len;
}
```

### 2. Checksum Computation

```cpp
// FIX checksum = sum of all bytes mod 256
// This is trivially SIMD-parallelizable

uint8_t checksum_simd(const char* msg, int len) {
    __m256i sum = _mm256_setzero_si256();

    int i = 0;
    for (; i + 32 <= len; i += 32) {
        __m256i chunk = _mm256_loadu_si256((__m256i*)(msg + i));
        // Use sad (sum of absolute differences) against zero to accumulate bytes
        sum = _mm256_add_epi64(sum,
            _mm256_sad_epu8(chunk, _mm256_setzero_si256()));
    }

    // Horizontal sum
    uint64_t parts[4];
    _mm256_storeu_si256((__m256i*)parts, sum);
    uint64_t total = parts[0] + parts[1] + parts[2] + parts[3];

    // Scalar remainder
    for (; i < len; ++i) total += (uint8_t)msg[i];

    return (uint8_t)(total & 0xFF);
}
```

### 3. Pre-Computed Field Prefixes

```cpp
// Tags like "11=", "55=", "38=" are constant — pre-compute their ASCII bytes
// Store as uint32_t or uint64_t for single-instruction writes

struct FieldPrefix {
    uint32_t bytes;  // "55=" stored as 3 bytes
    int len;         // 3
};

static constexpr FieldPrefix TAG_55 = {0x003D3535, 3};  // "55="
static constexpr FieldPrefix TAG_38 = {0x003D3833, 3};  // "38="
static constexpr FieldPrefix TAG_11 = {0x003D3131, 3};  // "11="

// Write tag prefix in one instruction
void write_prefix(char* p, FieldPrefix pf) {
    memcpy(p, &pf.bytes, 4);  // Compiler optimizes to single store
}
```

### 4. Compile-Time Message Building

```cpp
// Use constexpr to pre-compute static parts at compile time

template<int Tag>
struct TagPrefix {
    static constexpr auto value = [] {
        std::array<char, 8> buf{};
        int pos = 0;
        int t = Tag;
        if (t >= 100) buf[pos++] = '0' + t / 100;
        if (t >= 10) buf[pos++] = '0' + (t / 10) % 10;
        buf[pos++] = '0' + t % 10;
        buf[pos++] = '=';
        return std::pair{buf, pos};
    }();
};

// Usage: TagPrefix<55>::value gives "55=" at compile time
```

---

## Benchmarking

### Setup

```cpp
void benchmark_encoder() {
    Encoder encoder;
    constexpr int N = 1'000'000;

    // Pre-generate orders
    std::vector<Order> orders(N);
    for (int i = 0; i < N; ++i) {
        orders[i] = generate_random_order(i);
    }

    char out[512];
    uint64_t start = __rdtsc();
    for (int i = 0; i < N; ++i) {
        int len = encoder.encode(out, orders[i]);
        // Prevent optimizer from eliminating the call
        asm volatile("" : : "r"(len) : "memory");
    }
    uint64_t elapsed = __rdtsc() - start;

    printf("%.0f cycles/msg\n", (double)elapsed / N);
}
```

### Target Metrics

| Metric | Elite | Good | Needs Work |
|--------|-------|------|------------|
| cycles/msg | < 120 | 120-250 | > 250 |
| itoa throughput | < 5 cycles/digit | 5-10 cycles/digit | > 10 cycles/digit |
| Checksum overhead | < 10 cycles | 10-30 cycles | > 30 cycles |

---

## C++ vs Rust Gap

The massive gap (107 vs 3831 cycles/op) suggests:
1. Rust baseline is unoptimized — Rust implementations are still early
2. String building in Rust has more overhead (UTF-8 validation, bounds checks)
3. `unsafe` is needed for competitive performance but requires careful implementation
4. C++ can use raw pointer arithmetic without any runtime checks

---

## Common Pitfalls

1. **Using `sprintf`/`snprintf`** — Locale-aware, format string parsing; use custom itoa
2. **Two-pass for body length** — Reserve space and write in one pass
3. **String concatenation with `std::string`** — Dynamic allocation; write to fixed buffer
4. **Not pre-computing static field prefixes** — Every "55=" is the same; compute once
5. **Byte-by-byte checksum** — Use SIMD for bulk checksum computation
6. **Floating-point for price** — Use fixed-point integer arithmetic
