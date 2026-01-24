# C Language Concepts for Systems/Database Programming

## Table of Contents

1. [Overview](#overview)
2. [Storage Classes](#storage-classes)
3. [Type Qualifiers](#type-qualifiers)
4. [Common System Types](#common-system-types)
5. [Pointers Deep Dive](#pointers-deep-dive)
6. [Structures and Memory Layout](#structures-and-memory-layout)
7. [Unions and Type Punning](#unions-and-type-punning)
8. [Bitfields and Bit Manipulation](#bitfields-and-bit-manipulation)
9. [Function Pointers and Callbacks](#function-pointers-and-callbacks)
10. [Preprocessor and Macros](#preprocessor-and-macros)
11. [Memory Management](#memory-management)
12. [Error Handling Patterns](#error-handling-patterns)
13. [File I/O and System Calls](#file-io-and-system-calls)
14. [Concurrency Primitives](#concurrency-primitives)
15. [Common Patterns in Database Code](#common-patterns-in-database-code)

---

## Overview

This document covers C language concepts essential for understanding systems-level code, particularly database
implementations. Database code relies heavily on:

- Efficient memory management
- Low-level data manipulation
- Concurrency control
- File I/O operations
- Complex data structures

---

## Storage Classes

Storage classes determine the **lifetime**, **visibility**, and **storage location** of variables.

### `static`

**Purpose**: Controls visibility and lifetime

#### 1. Static Local Variables

- **Lifetime**: Entire program duration (not destroyed when function exits)
- **Visibility**: Only within the function
- **Initialized**: Only once, at program start

```c
void counter(void) {
  static int count = 0;  // Initialized once, persists across calls
  count++;
  printf("Called %d times\n", count);
}

// First call:  "Called 1 times"
// Second call: "Called 2 times"
// Third call:  "Called 3 times"
```

#### 2. Static Global Variables

- **Lifetime**: Entire program duration
- **Visibility**: Only within the current file (internal linkage)
- **Use**: Hide implementation details from other files

```c
// file: database.c
static int internal_state = 0;      // Only visible in database.c
static void helper_function(void);  // Only callable from database.c

int public_api(void) {              // Visible to other files
  return internal_state;
}
```

#### 3. Static Functions

- **Visibility**: Only within the current file
- **Use**: Private/internal functions

```c
// Only this file can call this function
static int parse_header(const char *data) {
  // Internal implementation
}
```

### `extern`

**Purpose**: Declare a variable/function defined elsewhere

```c
// file: globals.h
extern int global_counter;        // Declaration (no memory allocated)
extern void initialize_db(void);  // Function declaration

// file: globals.c
int global_counter = 0;           // Definition (memory allocated here)

void initialize_db(void) {        // Function definition
  global_counter = 1;
}

// file: main.c
#include "globals.h"
int main(void) {
  initialize_db();              // Uses the function from globals.c
  printf("%d\n", global_counter); // Uses variable from globals.c
}
```

**Key Points**:

- `extern` = "this exists somewhere else"
- Without `extern`, each file would create its own copy
- Functions are `extern` by default (but explicit is clearer)

### `register`

**Purpose**: Hint to compiler to store in CPU register (rarely used today)

```c
register int i;  // Compiler may ignore this hint
for (i = 0; i < 1000000; i++) {
  // Fast access to i
}
```

### `auto`

**Purpose**: Default for local variables (rarely written explicitly)

```c
auto int x = 5;  // Same as: int x = 5;
```

### Storage Class Summary

| Class             | Scope  | Lifetime | Default Value | Storage      |
| ----------------- | ------ | -------- | ------------- | ------------ |
| `auto`            | Block  | Block    | Garbage       | Stack        |
| `static` (local)  | Block  | Program  | 0             | Data segment |
| `static` (global) | File   | Program  | 0             | Data segment |
| `extern`          | Global | Program  | 0             | Data segment |
| `register`        | Block  | Block    | Garbage       | CPU register |

---

## Type Qualifiers

### `const`

**Purpose**: Value cannot be modified after initialization

```c
const int MAX_SIZE = 1024;           // Cannot change MAX_SIZE
MAX_SIZE = 2048;                     // ERROR: assignment to const

const char *ptr = "hello";           // Pointer to const data
ptr[0] = 'H';                        // ERROR: cannot modify data
ptr = "world";                       // OK: can change pointer

char *const ptr2 = buffer;           // Const pointer to data
ptr2[0] = 'H';                       // OK: can modify data
ptr2 = other_buffer;                 // ERROR: cannot change pointer

const char *const ptr3 = "hello";    // Const pointer to const data
```

**Reading Rule**: Read right-to-left

- `const int *p` → pointer to const int
- `int *const p` → const pointer to int
- `const int *const p` → const pointer to const int

### `volatile`

**Purpose**: Tells compiler the value can change unexpectedly (don't optimize)

```c
volatile int hardware_register;  // May be changed by hardware
volatile int shared_flag;        // May be changed by another thread

while (shared_flag == 0) {
  // Without volatile, compiler might optimize this to infinite loop
  // because it doesn't see shared_flag changing in this loop
}
```

**Use Cases**:

- Memory-mapped I/O registers
- Variables modified by interrupt handlers
- Variables shared between threads (though use atomics instead)

### `restrict` (C99)

**Purpose**: Promise that pointer is the only way to access that memory

````c
// Without restrict: compiler assumes a and b might overlap
void add_arrays(int *a, int *b, int *result, int n) {
  for (int i = 0; i < n; i++) {
    result[i] = a[i] + b[i];
  }
}

// With restrict: compiler can optimize more aggressively
void add_arrays_fast(int *restrict a, int *restrict b,
                     int *restrict result, int n) {
  for (int i = 0; i < n; i++) {
    result[i] = a[i] + b[i];  // Compiler knows no aliasing
  }
}

---

## Common System Types

These types are defined in system headers and provide portable, explicit sizes.

### Size Types

```c
#include <stddef.h>
#include <sys/types.h>

size_t   len;    // Unsigned, for sizes and counts (sizeof returns this)
ssize_t  ret;    // Signed size, for functions that can return -1 on error
ptrdiff_t diff;  // Difference between two pointers
````

**Why `size_t`?**

- Guaranteed to hold the size of any object
- Platform-appropriate: 32-bit on 32-bit systems, 64-bit on 64-bit
- Unsigned (sizes can't be negative)

```c
size_t len = strlen(str);        // strlen returns size_t
void *malloc(size_t size);       // malloc takes size_t
ssize_t read(int fd, void *buf, size_t count);  // read returns ssize_t (-1 on error)
```

### Fixed-Width Integer Types (C99)

```c
#include <stdint.h>

// Exact width (guaranteed size)
int8_t    i8;    // Exactly 8 bits, signed   (-128 to 127)
int16_t   i16;   // Exactly 16 bits, signed  (-32768 to 32767)
int32_t   i32;   // Exactly 32 bits, signed
int64_t   i64;   // Exactly 64 bits, signed

uint8_t   u8;    // Exactly 8 bits, unsigned  (0 to 255)
uint16_t  u16;   // Exactly 16 bits, unsigned (0 to 65535)
uint32_t  u32;   // Exactly 32 bits, unsigned
uint64_t  u64;   // Exactly 64 bits, unsigned

// Minimum width (at least N bits)
int_least8_t   li8;   // At least 8 bits
int_least16_t  li16;  // At least 16 bits

// Fastest with at least N bits
int_fast8_t    fi8;   // Fastest with at least 8 bits
int_fast16_t   fi16;  // Fastest with at least 16 bits

// Pointer-sized integers
intptr_t   iptr;   // Can hold a pointer value (signed)
uintptr_t  uptr;   // Can hold a pointer value (unsigned)

// Maximum width
intmax_t   imax;   // Largest signed integer type
uintmax_t  umax;   // Largest unsigned integer type
```

**Why Fixed-Width Types?**

```c
// PROBLEM: Size varies by platform
int x;      // 16, 32, or 64 bits depending on platform
long y;     // 32 or 64 bits depending on platform

// SOLUTION: Explicit sizes for data structures
struct disk_header {
  uint32_t magic;      // Always 4 bytes
  uint64_t file_size;  // Always 8 bytes
  uint16_t version;    // Always 2 bytes
};
```

### Boolean Type (C99)

```c
#include <stdbool.h>

bool flag = true;
bool done = false;

if (flag) {
  // ...
}
```

### NULL and nullptr

```c
#include <stddef.h>

void *ptr = NULL;       // Null pointer constant
int *p = NULL;

// C23 introduces nullptr (like C++)
// int *p = nullptr;
```

### Printing Fixed-Width Types

```c
#include <inttypes.h>

uint64_t size = 12345678901234ULL;
int32_t offset = -42;

printf("Size: %" PRIu64 "\n", size);    // PRIu64 = format for uint64_t
printf("Offset: %" PRId32 "\n", offset); // PRId32 = format for int32_t
printf("Pointer: %p\n", (void *)ptr);
printf("Size_t: %zu\n", sizeof(int));   // %zu for size_t
printf("ssize_t: %zd\n", bytes_read);   // %zd for ssize_t
```

| Type        | Printf Format |
| ----------- | ------------- |
| `int8_t`    | `PRId8`       |
| `uint8_t`   | `PRIu8`       |
| `int16_t`   | `PRId16`      |
| `uint16_t`  | `PRIu16`      |
| `int32_t`   | `PRId32`      |
| `uint32_t`  | `PRIu32`      |
| `int64_t`   | `PRId64`      |
| `uint64_t`  | `PRIu64`      |
| `size_t`    | `%zu`         |
| `ssize_t`   | `%zd`         |
| `ptrdiff_t` | `%td`         |
| `void *`    | `%p`          |

---

## Pointers Deep Dive

### Pointer Basics

```c
int x = 42;
int *ptr = &x;     // ptr holds the address of x

printf("%p\n", (void *)ptr);  // Print address
printf("%d\n", *ptr);         // Dereference: print value (42)

*ptr = 100;        // Modify x through pointer
printf("%d\n", x); // x is now 100
```

### Pointer Arithmetic

```c
int arr[5] = {10, 20, 30, 40, 50};
int *p = arr;      // p points to arr[0]

printf("%d\n", *p);       // 10 (arr[0])
printf("%d\n", *(p + 1)); // 20 (arr[1])
printf("%d\n", *(p + 2)); // 30 (arr[2])

p++;               // Move to next element
printf("%d\n", *p); // 20

// Pointer arithmetic is scaled by element size
// p + 1 moves sizeof(int) bytes, not 1 byte
```

### Double Pointers (Pointer to Pointer)

```c
int x = 42;
int *p = &x;
int **pp = &p;     // Pointer to pointer

printf("%d\n", **pp);  // 42

// Common use: Modifying a pointer in a function
void allocate(int **ptr) {
  *ptr = malloc(sizeof(int));
  **ptr = 42;
}

int *myptr = NULL;
allocate(&myptr);      // myptr now points to allocated memory
printf("%d\n", *myptr); // 42
```

### Void Pointers

```c
void *generic_ptr;   // Can point to any type

int x = 42;
float f = 3.14f;
char c = 'A';

generic_ptr = &x;    // OK
generic_ptr = &f;    // OK
generic_ptr = &c;    // OK

// Must cast before dereferencing
int *ip = (int *)generic_ptr;
printf("%d\n", *ip);

// Cannot do pointer arithmetic on void*
// generic_ptr++;    // ERROR
```

**Use in Database Code**:

```c
// Generic data storage
struct node {
  void *data;      // Can store any type
  struct node *next;
};

// Generic comparison function
typedef int (*compare_fn)(const void *, const void *);
void sort(void *base, size_t count, size_t size, compare_fn cmp);
```

### Function Pointers

```c
// Declare function pointer type
typedef int (*compare_fn)(const void *, const void *);

// Example function matching the signature
int compare_ints(const void *a, const void *b) {
  int ia = *(const int *)a;
  int ib = *(const int *)b;
  return ia - ib;
}

// Use the function pointer
compare_fn cmp = compare_ints;
int result = cmp(&x, &y);

// Common in database code for callbacks
struct table_ops {
  int (*insert)(struct table *, void *key, void *value);
  int (*lookup)(struct table *, void *key, void **value);
  int (*delete)(struct table *, void *key);
};
```

### Const with Pointers (Important!)

```c
// Read right-to-left for understanding

const int *p1;        // Pointer to const int
// Can't modify *p1, can modify p1

int *const p2;        // Const pointer to int
// Can modify *p2, can't modify p2

const int *const p3;  // Const pointer to const int
// Can't modify *p3, can't modify p3

// Common in function parameters
void print_buffer(const char *buf, size_t len);  // Won't modify buf
```

---

## Structures and Memory Layout

### Basic Structure

```c
struct person {
  char name[32];
  int age;
  float height;
};

struct person p1;
p1.age = 25;
strcpy(p1.name, "Alice");

struct person p2 = {"Bob", 30, 5.9f};  // Initialization
struct person p3 = {.age = 35, .name = "Charlie"};  // Designated (C99)
```

### Structure Padding and Alignment

**Problem**: CPUs access memory most efficiently at aligned addresses.

```c
struct unoptimized {
  char a;      // 1 byte
  // 3 bytes padding (to align int)
  int b;       // 4 bytes
  char c;      // 1 byte
  // 3 bytes padding (to align to 4-byte boundary)
};
// Total: 12 bytes (not 6!)

struct optimized {
  int b;       // 4 bytes
  char a;      // 1 byte
  char c;      // 1 byte
  // 2 bytes padding
};
// Total: 8 bytes
```

**Visualizing Memory Layout**:

```
struct unoptimized (12 bytes):
┌───┬───┬───┬───┬───┬───┬───┬───┬───┬───┬───┬───┐
│ a │pad│pad│pad│   b (4 bytes)   │ c │pad│pad│pad│
└───┴───┴───┴───┴───┴───┴───┴───┴───┴───┴───┴───┘
0   1   2   3   4   5   6   7   8   9  10  11

struct optimized (8 bytes):
┌───┬───┬───┬───┬───┬───┬───┬───┐
│   b (4 bytes)   │ a │ c │pad│pad│
└───┴───┴───┴───┴───┴───┴───┴───┘
0   1   2   3   4   5   6   7
```

### Controlling Alignment

```c
// Check size and alignment
printf("Size: %zu\n", sizeof(struct person));
printf("Alignment: %zu\n", _Alignof(struct person));

// Pack structure (remove padding) - compiler-specific
struct __attribute__((packed)) packed_header {
  uint8_t type;
  uint32_t length;
  uint16_t checksum;
};
// Size: 7 bytes (no padding), but slower access

// Align to specific boundary
struct __attribute__((aligned(64))) cache_aligned {
  int data[16];
};
// Aligned to 64-byte cache line boundary
```

### Flexible Array Member (C99)

```c
struct packet {
  uint32_t length;
  uint8_t type;
  uint8_t data[];  // Flexible array member (must be last)
};

// Allocate with extra space for data
size_t data_size = 1024;
struct packet *pkt = malloc(sizeof(struct packet) + data_size);
pkt->length = data_size;
memcpy(pkt->data, source, data_size);
```

### Anonymous Structures and Unions (C11)

```c
struct outer {
  int x;
  struct {
    int a;
    int b;
  };  // Anonymous struct
};

struct outer o;
o.a = 1;  // Direct access (no intermediate name)
o.b = 2;
```

---

## Unions and Type Punning

### Basic Union

A union stores different types in the **same memory location**.

```c
union data {
  int i;
  float f;
  char bytes[4];
};

union data d;
d.i = 0x41424344;  // Store as int

// Access the same memory as different types
printf("As int: %d\n", d.i);
printf("As bytes: %c %c %c %c\n",
       d.bytes[0], d.bytes[1], d.bytes[2], d.bytes[3]);
```

### Union Size

```c
union example {
  char c;      // 1 byte
  int i;       // 4 bytes
  double d;    // 8 bytes
};
// Size = 8 (largest member)
```

### Tagged Union (Discriminated Union)

Common pattern in database code for variant types:

```c
enum value_type { TYPE_INT, TYPE_FLOAT, TYPE_STRING };

struct value {
  enum value_type type;  // Tag
  union {
    int64_t i;
    double f;
    char *s;
  } data;
};

void print_value(struct value *v) {
  switch (v->type) {
    case TYPE_INT:
      printf("%lld\n", v->data.i);
      break;
    case TYPE_FLOAT:
      printf("%f\n", v->data.f);
      break;
    case TYPE_STRING:
      printf("%s\n", v->data.s);
      break;
  }
}
```

### Type Punning with Unions

```c
// View float bits as integer
union float_bits {
  float f;
  uint32_t u;
};

union float_bits fb;
fb.f = 3.14159f;
printf("Float bits: 0x%08X\n", fb.u);

// Network byte order conversion
union {
  uint32_t value;
  uint8_t bytes[4];
} converter;

converter.value = 0x12345678;
// bytes[0] = 0x78 (little-endian) or 0x12 (big-endian)
```

---

## Bitfields and Bit Manipulation

### Bitfields in Structures

```c
struct tcp_flags {
  uint8_t fin : 1;   // 1 bit
  uint8_t syn : 1;   // 1 bit
  uint8_t rst : 1;   // 1 bit
  uint8_t psh : 1;   // 1 bit
  uint8_t ack : 1;   // 1 bit
  uint8_t urg : 1;   // 1 bit
  uint8_t ece : 1;   // 1 bit
  uint8_t cwr : 1;   // 1 bit
};

struct tcp_flags flags = {0};
flags.syn = 1;
flags.ack = 1;

if (flags.syn && flags.ack) {
  // SYN-ACK packet
}
```

### Bit Manipulation Operators

```c
// Operators
&   // AND
|   // OR
^   // XOR
~   // NOT (complement)
<<  // Left shift
>>  // Right shift
```

### Common Bit Operations

```c
#define BIT(n)              (1U << (n))
#define SET_BIT(x, n)       ((x) |= BIT(n))
#define CLEAR_BIT(x, n)     ((x) &= ~BIT(n))
#define TOGGLE_BIT(x, n)    ((x) ^= BIT(n))
#define CHECK_BIT(x, n)     (((x) >> (n)) & 1U)

// Example: Flag manipulation
#define FLAG_DIRTY      BIT(0)   // 0x01
#define FLAG_VALID      BIT(1)   // 0x02
#define FLAG_LOCKED     BIT(2)   // 0x04
#define FLAG_CACHED     BIT(3)   // 0x08

uint32_t page_flags = 0;

SET_BIT(page_flags, 0);           // Set dirty flag
page_flags |= FLAG_VALID;         // Set valid flag
page_flags &= ~FLAG_LOCKED;       // Clear locked flag

if (page_flags & FLAG_DIRTY) {
  // Page is dirty
}
```

### Extracting Bit Ranges

```c
// Extract bits [start:end] from value
#define EXTRACT_BITS(value, start, end) \
(((value) >> (start)) & ((1U << ((end) - (start) + 1)) - 1))

// Example: Extract bits 4-7 from 0xABCD
uint16_t val = 0xABCD;  // Binary: 1010 1011 1100 1101
uint8_t nibble = EXTRACT_BITS(val, 4, 7);  // Gets 0xC (1100)
```

### Bitmask for Page/Block Status

```c
// Database page status flags
typedef uint32_t page_flags_t;

#define PAGE_FLAG_NONE       0x00000000
#define PAGE_FLAG_DIRTY      0x00000001
#define PAGE_FLAG_PINNED     0x00000002
#define PAGE_FLAG_LOCKED     0x00000004
#define PAGE_FLAG_IN_FLUSH   0x00000008
#define PAGE_FLAG_EVICTABLE  0x00000010

static inline bool page_is_dirty(page_flags_t flags) {
  return (flags & PAGE_FLAG_DIRTY) != 0;
}

static inline void page_set_dirty(page_flags_t *flags) {
  *flags |= PAGE_FLAG_DIRTY;
}

static inline void page_clear_dirty(page_flags_t *flags) {
  *flags &= ~PAGE_FLAG_DIRTY;
}

```

## Function Pointers and Callbacks

### Basic Function Pointer

```c
// Declare a function pointer
int (*operation)(int, int);

// Functions that match the signature
int add(int a, int b) { return a + b; }
int multiply(int a, int b) { return a * b; }

// Assign and call
operation = add;
int result = operation(5, 3);  // result = 8

operation = multiply;
result = operation(5, 3);      // result = 15
```

### Typedef for Function Pointers

```c
// Cleaner syntax with typedef
typedef int (*math_op)(int, int);

math_op op = add;
int result = op(5, 3);

// Function that takes a function pointer
int apply(math_op op, int a, int b) {
  return op(a, b);
}

int sum = apply(add, 10, 20);  // sum = 30
```

### Callback Pattern

```c
// Callback function type
typedef void (*callback_fn)(void *context, int result);

// Async operation with callback
void async_read(int fd, callback_fn on_complete, void *context) {
  // ... perform read ...
  int result = 42;
  on_complete(context, result);
}

// User's callback
void my_callback(void *context, int result) {
  int *counter = (int *)context;
  (*counter)++;
  printf("Read completed: %d\n", result);
}

// Usage
int call_count = 0;
async_read(fd, my_callback, &call_count);
```

### Virtual Table Pattern (OOP in C)

```c
// "Interface" as struct of function pointers
struct storage_ops {
  int (*open)(struct storage *s, const char *path);
  int (*close)(struct storage *s);
  ssize_t (*read)(struct storage *s, void *buf, size_t len);
  ssize_t (*write)(struct storage *s, const void *buf, size_t len);
};

struct storage {
  const struct storage_ops *ops;  // Virtual table pointer
  void *private_data;
};

// "Implement" for file storage
static int file_open(struct storage *s, const char *path) { /* ... */ }
static int file_close(struct storage *s) { /* ... */ }
static ssize_t file_read(struct storage *s, void *buf, size_t len) { /* ... */ }
static ssize_t file_write(struct storage *s, const void *buf, size_t len) { /* ... */ }

static const struct storage_ops file_ops = {
  .open = file_open,
  .close = file_close,
  .read = file_read,
  .write = file_write,
};

// Usage (polymorphism)
struct storage *s = create_file_storage();
s->ops->read(s, buffer, 1024);  // Calls file_read
```

---

## Preprocessor and Macros

### Include Guards

```c
// header.h
#ifndef HEADER_H
#define HEADER_H

// ... header contents ...

#endif // HEADER_H

// Modern alternative (not standard but widely supported)
#pragma once
```

### Macros vs Functions

```c
// Simple macros (text substitution)
#define MAX(a, b) ((a) > (b) ? (a) : (b))
#define MIN(a, b) ((a) < (b) ? (a) : (b))
#define ABS(x) ((x) < 0 ? -(x) : (x))

// DANGER: Arguments evaluated multiple times
int x = 5;
int y = MAX(x++, 3);  // x++ evaluated twice!

// Safer: inline functions (C99)
static inline int max_int(int a, int b) {
  return a > b ? a : b;
}
```

### Common Macro Patterns

```c
// Stringify
#define STR(x) #x
#define XSTR(x) STR(x)
printf("%s\n", STR(hello));  // Prints: hello

// Concatenation
#define CONCAT(a, b) a##b
int CONCAT(my, var) = 42;    // Creates: int myvar = 42;

// Array size
#define ARRAY_SIZE(arr) (sizeof(arr) / sizeof((arr)[0]))

int numbers[] = {1, 2, 3, 4, 5};
size_t count = ARRAY_SIZE(numbers);  // count = 5

// Container of (get struct from member pointer)
#define container_of(ptr, type, member) \
((type *)((char *)(ptr) - offsetof(type, member)))

struct list_node {
  struct list_node *next;
};

struct my_item {
  int data;
  struct list_node node;  // Embedded list node
};

// Get my_item from list_node pointer
struct list_node *n = get_next_node();
struct my_item *item = container_of(n, struct my_item, node);
```

### Variadic Macros

```c
// Debug logging macro
#define DEBUG_LOG(fmt, ...) \
fprintf(stderr, "[DEBUG] %s:%d: " fmt "\n", \
        __FILE__, __LINE__, ##__VA_ARGS__)

DEBUG_LOG("Starting operation");
DEBUG_LOG("Value: %d", 42);
DEBUG_LOG("x=%d, y=%d", x, y);
```

### Conditional Compilation

```c
#ifdef DEBUG
#define LOG(msg) printf("[DEBUG] %s\n", msg)
#else
#define LOG(msg)  // Empty, compiles to nothing
#endif

#if defined(__linux__)
// Linux-specific code
#elif defined(__APPLE__)
// macOS-specific code
#elif defined(_WIN32)
// Windows-specific code
#endif

// Check compiler features
#if __STDC_VERSION__ >= 199901L
// C99 or later
#endif

#if __STDC_VERSION__ >= 201112L
// C11 or later
#endif
```

### Predefined Macros

| Macro              | Description                 |
| ------------------ | --------------------------- |
| `__FILE__`         | Current source file name    |
| `__LINE__`         | Current line number         |
| `__func__`         | Current function name (C99) |
| `__DATE__`         | Compilation date            |
| `__TIME__`         | Compilation time            |
| `__STDC__`         | 1 if standard-conforming    |
| `__STDC_VERSION__` | C standard version          |

---

## Memory Management

### Stack vs Heap

```
┌─────────────────────────────────────────────────────────────────┐
│                     Process Memory Layout                       │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  High Address ───────────────────────────────────────────────── │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │                    STACK                                 │   │
│  │  - Local variables                                       │   │
│  │  - Function parameters                                   │   │
│  │  - Return addresses                                      │   │
│  │  - Grows downward ↓                                      │   │
│  └─────────────────────────────────────────────────────────┘   │
│                           ↓                                     │
│                                                                 │
│                     (free space)                                │
│                                                                 │
│                           ↑                                     │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │                    HEAP                                  │   │
│  │  - Dynamic allocations (malloc)                          │   │
│  │  - Grows upward ↑                                        │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │                    BSS (uninitialized data)              │   │
│  │  - Global/static variables initialized to 0              │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │                    DATA (initialized data)               │   │
│  │  - Global/static variables with initial values           │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │                    TEXT (code)                           │   │
│  │  - Executable instructions                               │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
│  Low Address ────────────────────────────────────────────────── │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Memory Allocation Functions

```c
#include <stdlib.h>

// Allocate uninitialized memory
void *malloc(size_t size);

// Allocate and zero-initialize
void *calloc(size_t count, size_t size);

// Resize allocation
void *realloc(void *ptr, size_t new_size);

// Free allocation
void free(void *ptr);

// Aligned allocation (C11)
void *aligned_alloc(size_t alignment, size_t size);
```

### Safe Allocation Patterns

```c
// Always check for NULL
int *arr = malloc(n * sizeof(int));
if (arr == NULL) {
  perror("malloc failed");
  return -1;
}

// Use sizeof with the variable, not the type
int *ptr = malloc(sizeof(*ptr));      // Better: adapts if type changes
int *ptr = malloc(sizeof(int));       // Works but fragile

// Allocate array
int *arr = malloc(count * sizeof(*arr));

// Allocate struct
struct node *n = malloc(sizeof(*n));

// Zero-initialize
int *arr = calloc(count, sizeof(*arr));
// or
int *arr = malloc(count * sizeof(*arr));
if (arr) memset(arr, 0, count * sizeof(*arr));
```

### Memory Deallocation

```c
// Free and NULL pattern
void safe_free(void **ptr) {
  if (ptr && *ptr) {
    free(*ptr);
    *ptr = NULL;
  }
}

#define FREE(ptr) safe_free((void **)&(ptr))

// Usage
int *arr = malloc(100 * sizeof(int));
// ... use arr ...
FREE(arr);  // arr is now NULL
```

### Common Memory Bugs

```c
// 1. Memory leak (forgetting to free)
void leak() {
  int *p = malloc(100);
  return;  // Leaked!
}

// 2. Use after free
int *p = malloc(sizeof(int));
free(p);
*p = 42;  // UNDEFINED BEHAVIOR!

// 3. Double free
free(p);
free(p);  // UNDEFINED BEHAVIOR!

// 4. Buffer overflow
int *arr = malloc(10 * sizeof(int));
arr[10] = 42;  // Out of bounds!

// 5. Integer overflow in size calculation
size_t count = UINT32_MAX;
int *arr = malloc(count * sizeof(int));  // Overflow!
```

---

## Error Handling Patterns

### Return Code Pattern

```c
// Convention: 0 = success, negative = error
#define SUCCESS       0
#define ERR_NOMEM    -1
#define ERR_INVALID  -2
#define ERR_IO       -3

int open_database(const char *path, struct db **out) {
  if (path == NULL || out == NULL) {
    return ERR_INVALID;
  }

  struct db *db = malloc(sizeof(*db));
  if (db == NULL) {
    return ERR_NOMEM;
  }

  if (load_file(path, db) < 0) {
    free(db);
    return ERR_IO;
  }

  *out = db;
  return SUCCESS;
}

// Usage
struct db *db;
int ret = open_database("data.db", &db);
if (ret != SUCCESS) {
  fprintf(stderr, "Failed: %d\n", ret);
  return ret;
}
```

### errno Pattern

```c
#include <errno.h>
#include <string.h>

int fd = open("file.txt", O_RDONLY);
if (fd < 0) {
  // errno is set by the system call
  fprintf(stderr, "open failed: %s (errno=%d)\n",
          strerror(errno), errno);
  return -1;
}

// Common errno values
ENOENT   // No such file or directory
EACCES   // Permission denied
ENOMEM   // Out of memory
EINVAL   // Invalid argument
EIO      // I/O error
EEXIST   // File exists
EAGAIN   // Try again (non-blocking)
EINTR    // Interrupted system call
```

### Goto for Cleanup

```c
int process_file(const char *path) {
  int ret = -1;
  FILE *file = NULL;
  char *buffer = NULL;
  struct data *data = NULL;

  file = fopen(path, "r");
  if (file == NULL) {
    goto cleanup;
  }

  buffer = malloc(BUFFER_SIZE);
  if (buffer == NULL) {
    goto cleanup;
  }

  data = malloc(sizeof(*data));
  if (data == NULL) {
    goto cleanup;
  }

  // Do work...
  ret = 0;  // Success

cleanup:
  if (data) free(data);
  if (buffer) free(buffer);
  if (file) fclose(file);
  return ret;
}
```

### Error Struct Pattern

```c
struct error {
  int code;
  char message[256];
};

int do_operation(int input, struct error *err) {
  if (input < 0) {
    if (err) {
      err->code = ERR_INVALID;
      snprintf(err->message, sizeof(err->message),
               "Invalid input: %d", input);
    }
    return -1;
  }
  return input * 2;
}

// Usage
struct error err;
int result = do_operation(-5, &err);
if (result < 0) {
  fprintf(stderr, "Error %d: %s\n", err.code, err.message);
}
```

---

## File I/O and System Calls

### Standard C File I/O (Buffered)

```c
#include <stdio.h>

// Open file
FILE *fp = fopen("data.txt", "r");   // Read
FILE *fp = fopen("data.txt", "w");   // Write (truncate)
FILE *fp = fopen("data.txt", "a");   // Append
FILE *fp = fopen("data.txt", "rb");  // Binary read
FILE *fp = fopen("data.txt", "wb");  // Binary write

// Read/Write
char line[256];
fgets(line, sizeof(line), fp);       // Read line
fputs("hello\n", fp);                // Write string
fprintf(fp, "Value: %d\n", 42);      // Formatted write

size_t n = fread(buf, 1, len, fp);   // Binary read
size_t n = fwrite(buf, 1, len, fp);  // Binary write

// Position
fseek(fp, offset, SEEK_SET);         // From beginning
fseek(fp, offset, SEEK_CUR);         // From current
fseek(fp, offset, SEEK_END);         // From end
long pos = ftell(fp);                // Get position
rewind(fp);                          // Go to beginning

// Close
fclose(fp);
```

### POSIX System Calls (Unbuffered)

```c
#include <fcntl.h>
#include <unistd.h>

// Open file (returns file descriptor)
int fd = open("data.txt", O_RDONLY);
int fd = open("data.txt", O_WRONLY | O_CREAT | O_TRUNC, 0644);
int fd = open("data.txt", O_RDWR | O_CREAT, 0644);

// Read/Write
ssize_t n = read(fd, buf, len);
ssize_t n = write(fd, buf, len);

// Position
off_t pos = lseek(fd, offset, SEEK_SET);

// Sync to disk
fsync(fd);       // Sync data and metadata
fdatasync(fd);   // Sync data only

// Close
close(fd);
```

### Memory-Mapped Files

```c
#include <sys/mman.h>

// Map file into memory
int fd = open("data.bin", O_RDWR);
size_t size = get_file_size(fd);

void *addr = mmap(NULL, size, PROT_READ | PROT_WRITE,
                  MAP_SHARED, fd, 0);
if (addr == MAP_FAILED) {
  perror("mmap");
  return -1;
}

// Access file as memory
char *data = (char *)addr;
data[0] = 'H';  // Writes to file

// Sync changes
msync(addr, size, MS_SYNC);

// Unmap
munmap(addr, size);
close(fd);
```

### Direct I/O (Bypass OS Cache)

```c
// Aligned buffer for direct I/O
void *buf;
posix_memalign(&buf, 4096, buffer_size);  // 4KB aligned

int fd = open("data.bin", O_RDWR | O_DIRECT);
read(fd, buf, buffer_size);  // Direct from disk

free(buf);
```

---

## Concurrency Primitives

### POSIX Threads (pthreads)

```c
#include <pthread.h>

// Thread function
void *thread_func(void *arg) {
  int *id = (int *)arg;
  printf("Thread %d running\n", *id);
  return NULL;
}

// Create thread
pthread_t thread;
int id = 1;
pthread_create(&thread, NULL, thread_func, &id);

// Wait for thread
pthread_join(thread, NULL);
```

### Mutex (Mutual Exclusion)

```c
pthread_mutex_t mutex = PTHREAD_MUTEX_INITIALIZER;

void *worker(void *arg) {
  pthread_mutex_lock(&mutex);
  // Critical section - only one thread at a time
  shared_counter++;
  pthread_mutex_unlock(&mutex);
  return NULL;
}
```

### Condition Variables

```c
pthread_mutex_t mutex = PTHREAD_MUTEX_INITIALIZER;
pthread_cond_t cond = PTHREAD_COND_INITIALIZER;
int ready = 0;

// Producer
pthread_mutex_lock(&mutex);
ready = 1;
pthread_cond_signal(&cond);  // Wake one waiter
pthread_mutex_unlock(&mutex);

// Consumer
pthread_mutex_lock(&mutex);
while (!ready) {  // Always use while, not if
  pthread_cond_wait(&cond, &mutex);
}
// ready is now true
pthread_mutex_unlock(&mutex);
```

### Read-Write Locks

```c
pthread_rwlock_t rwlock = PTHREAD_RWLOCK_INITIALIZER;

// Reader (multiple allowed)
pthread_rwlock_rdlock(&rwlock);
// Read shared data
pthread_rwlock_unlock(&rwlock);

// Writer (exclusive)
pthread_rwlock_wrlock(&rwlock);
// Modify shared data
pthread_rwlock_unlock(&rwlock);
```

### Atomic Operations (C11)

```c
#include <stdatomic.h>

atomic_int counter = ATOMIC_VAR_INIT(0);

// Atomic increment
atomic_fetch_add(&counter, 1);

// Atomic load/store
int value = atomic_load(&counter);
atomic_store(&counter, 42);

// Compare and swap
int expected = 10;
bool success = atomic_compare_exchange_strong(&counter, &expected, 20);
// If counter == 10, set to 20 and return true
// Else, expected = current value and return false
```

---

## Common Patterns in Database Code

### Object-Oriented Style in C

```c
// "Class" definition
struct buffer_pool {
  struct page *pages;
  size_t num_pages;
  pthread_mutex_t lock;

  // "Methods" via function pointers (optional)
  struct buffer_pool_ops *ops;
};

// "Constructor"
struct buffer_pool *buffer_pool_create(size_t num_pages) {
  struct buffer_pool *pool = calloc(1, sizeof(*pool));
  if (!pool) return NULL;

  pool->pages = calloc(num_pages, sizeof(*pool->pages));
  if (!pool->pages) {
    free(pool);
    return NULL;
  }

  pool->num_pages = num_pages;
  pthread_mutex_init(&pool->lock, NULL);
  return pool;
}

// "Destructor"
void buffer_pool_destroy(struct buffer_pool *pool) {
  if (!pool) return;
  pthread_mutex_destroy(&pool->lock);
  free(pool->pages);
  free(pool);
}

// "Method"
struct page *buffer_pool_get_page(struct buffer_pool *pool,
                                  page_id_t page_id) {
  pthread_mutex_lock(&pool->lock);
  // ... find or load page ...
  pthread_mutex_unlock(&pool->lock);
  return page;
}
```

### Intrusive Linked List

```c
// List node embedded in data structure
struct list_head {
  struct list_head *next;
  struct list_head *prev;
};

// Data structure with embedded node
struct page {
  page_id_t id;
  void *data;
  struct list_head lru_node;  // For LRU list
  struct list_head free_node; // For free list
};

// List operations
#define LIST_HEAD_INIT(name) { &(name), &(name) }

static inline void list_add(struct list_head *new,
                            struct list_head *head) {
  new->next = head->next;
  new->prev = head;
  head->next->prev = new;
  head->next = new;
}

static inline void list_del(struct list_head *entry) {
  entry->prev->next = entry->next;
  entry->next->prev = entry->prev;
}

// Get struct from embedded node
#define list_entry(ptr, type, member) \
container_of(ptr, type, member)
```

### Hash Table Pattern

```c
struct hash_entry {
  uint64_t key;
  void *value;
  struct hash_entry *next;  // Chaining
};

struct hash_table {
  struct hash_entry **buckets;
  size_t num_buckets;
  size_t count;
};

static inline size_t hash_func(uint64_t key, size_t num_buckets) {
  return key % num_buckets;  // Simple modulo hash
}

void *hash_lookup(struct hash_table *ht, uint64_t key) {
  size_t bucket = hash_func(key, ht->num_buckets);
  struct hash_entry *entry = ht->buckets[bucket];

  while (entry) {
    if (entry->key == key) {
      return entry->value;
    }
    entry = entry->next;
  }
  return NULL;
}
```

### Reference Counting

```c
struct object {
  atomic_int refcount;
  void (*destructor)(struct object *);
  // ... other fields ...
};

static inline void object_ref(struct object *obj) {
  atomic_fetch_add(&obj->refcount, 1);
}

static inline void object_unref(struct object *obj) {
  if (atomic_fetch_sub(&obj->refcount, 1) == 1) {
    // Last reference, destroy object
    if (obj->destructor) {
      obj->destructor(obj);
    }
    free(obj);
  }
}
```

### Slab Allocator Pattern

```c
struct slab {
  void *memory;
  size_t object_size;
  size_t capacity;
  struct free_list *free_head;
};

struct free_list {
  struct free_list *next;
};

void *slab_alloc(struct slab *slab) {
  if (slab->free_head == NULL) {
    return NULL;  // Slab full
  }
  void *obj = slab->free_head;
  slab->free_head = slab->free_head->next;
  return obj;
}

void slab_free(struct slab *slab, void *obj) {
  struct free_list *entry = obj;
  entry->next = slab->free_head;
  slab->free_head = entry;
}
```

---

## Glossary of Key Terms

| Term           | Description                                       |
| -------------- | ------------------------------------------------- |
| `static`       | Limits scope (file/function) and extends lifetime |
| `extern`       | Declares symbol defined in another file           |
| `const`        | Value cannot be modified                          |
| `volatile`     | Compiler must not optimize access                 |
| `restrict`     | Pointer is the only access to memory              |
| `size_t`       | Unsigned type for sizes (platform-sized)          |
| `ssize_t`      | Signed size (can be -1 for error)                 |
| `uint32_t`     | Exactly 32-bit unsigned integer                   |
| `intptr_t`     | Integer that can hold a pointer                   |
| `offsetof`     | Byte offset of member in struct                   |
| `container_of` | Get struct pointer from member pointer            |
| Stack          | Automatic storage (local variables)               |
| Heap           | Dynamic storage (malloc/free)                     |
| BSS            | Uninitialized global/static data                  |
| Data segment   | Initialized global/static data                    |
| Text segment   | Executable code                                   |
| mmap           | Memory-map a file                                 |
| mutex          | Mutual exclusion lock                             |
| atomic         | Operations that can't be interrupted              |

---

## Further Reading

- "The C Programming Language" by Kernighan & Ritchie
- "Expert C Programming" by Peter van der Linden
- "C Interfaces and Implementations" by David Hanson
- "Computer Systems: A Programmer's Perspective" by Bryant & O'Hallaron
- POSIX.1-2017 specification for system calls

```

```
