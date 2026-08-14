# Item 16: Use the same form in corresponding uses of new and delete

## Visual Summary

```text
┌───────────────────────────────────────────────────────────────────────────┐
│    ITEM 16: USE THE SAME FORM IN CORRESPONDING USES OF NEW AND DELETE     │
├───────────────────────────────────────────────────────────────────────────┤
│ 1. new T -> one object constructed -> delete T destroys one object.       │
│ 2. new T[n] -> n objects constructed plus array bookkeeping.              │
│ 3. delete[] required -> destroys every element and uses right             │
│ deallocation form.                                                        │
│ 4. Mismatch -> undefined behavior, leaks, or corrupted heap metadata.     │
│ 5. Meaning: allocation form and deallocation form are a matched pair.     │
└───────────────────────────────────────────────────────────────────────────┘
```

## Visual Deep Dive

```text
┌───────────────────────────────────────────────────────────────────────────┐
│                             ALLOCATION PAIRS                              │
├───────────────────────────────────────────────────────────────────────────┤
│ Allocation                        | Deallocation                          │
│ ----------------------------------+-------------------------------------  │
│ new T                             | delete p                              │
│ new T[n]                          | delete[] p                            │
└───────────────────────────────────────────────────────────────────────────┘
```

```text
┌───────────────────────────────────────────────────────────────────────────┐
│                           MISMATCH FAILURE FLOW                           │
├───────────────────────────────────────────────────────────────────────────┤
│ Array allocation stores element count/bookkeeping                         │
│                                     ▼                                     │
│ Plain delete does not know array form                                     │
│                                     ▼                                     │
│ Some destructors may not run                                              │
│                                     ▼                                     │
│ Heap metadata can be corrupted                                            │
└───────────────────────────────────────────────────────────────────────────┘
```

### The Rule

This item has the simplest guideline in the chapter, yet violations cause some of the most
insidious bugs in C++:

> If you use `[]` in a `new` expression, you must use `[]` in the corresponding `delete`
> expression. If you do not use `[]` in a `new` expression, you must not use `[]` in the
> corresponding `delete` expression.

### Understanding Memory Layout

When you use `new`, two things happen:
1. Memory is allocated (via `operator new`).
2. One or more constructors are called on that memory.

When you use `delete`, two things happen (in reverse):
1. One or more destructors are called.
2. Memory is deallocated (via `operator delete`).

The critical question for `delete` is: **how many objects reside in the memory being
deleted?** This determines how many destructors to call.

A single object and an array of objects have different memory layouts:

```
Single object:
+-------------------+
|      Object       |
+-------------------+

Array of objects:
+---+-------------------+-------------------+---+-------------------+
| n |     Object 0      |     Object 1      |...|    Object n-1     |
+---+-------------------+-------------------+---+-------------------+
  ^
  |-- Array size (stored by the implementation, typically before the first object)
```

When you say `delete[]`, the runtime reads the array size `n` from this header and calls
destructors for each of the `n` objects. When you say `delete` (without `[]`), the runtime
assumes there is a single object and calls one destructor.

### What Goes Wrong

#### BAD: Using delete on an array

```cpp
std::string* stringArray = new std::string[100];

// ...

delete stringArray;   // UNDEFINED BEHAVIOR!
// Only one destructor is called (for stringArray[0]).
// The other 99 std::string objects are never destroyed.
// Their internal memory (heap-allocated character buffers) is leaked.
// The memory layout is also misinterpreted, potentially corrupting the heap.
```

#### BAD: Using delete[] on a single object

```cpp
std::string* stringPtr = new std::string("hello");

// ...

delete[] stringPtr;   // UNDEFINED BEHAVIOR!
// The runtime tries to read an array size from memory before the object.
// That memory contains garbage (or part of another allocation).
// It then tries to call destructors on "objects" that do not exist.
// This can corrupt memory, crash, or cause silent data corruption.
```

#### Both are undefined behavior

The C++ Standard says the behavior is undefined in both cases. In practice:

- `delete` on an array may leak resources held by all but the first element.
- `delete[]` on a single object may read garbage as an array count and corrupt memory.
- Some implementations may appear to "work" for built-in types (like `int`) because their
  destructors are trivial, but the behavior is still technically undefined.

### The Correct Pairings

```cpp
// Correct: new with delete
std::string* ps = new std::string("hello");
delete ps;

// Correct: new[] with delete[]
std::string* psa = new std::string[100];
delete[] psa;

// Correct: Built-in types follow the same rule
int* pi = new int(42);
delete pi;

int* pia = new int[100];
delete[] pia;
```

### The Typedef Trap

Typedefs can obscure whether a type is an array, making this rule harder to follow:

```cpp
// BAD: A typedef that hides an array
typedef std::string AddressLines[4];

// This looks like a single object allocation, but it is an array!
std::string* pal = new AddressLines;
// This is equivalent to: new std::string[4]

// What form of delete is correct?
delete pal;     // UNDEFINED BEHAVIOR! This is actually an array.
delete[] pal;   // Correct, but non-obvious because AddressLines hides the array.
```

This is a compelling reason to prefer `std::array` or `std::vector` over raw arrays
and array typedefs:

```cpp
// GOOD: No ambiguity with std::array or std::vector
using AddressLines = std::array<std::string, 4>;

AddressLines* pal = new AddressLines;
delete pal;   // Correct: AddressLines is a single object (a struct containing an array)

// BETTER: No new/delete at all
AddressLines pal;   // Stack-allocated, no manual cleanup needed

// BEST: Use a vector if the size is dynamic
std::vector<std::string> pal(4);
```

### Smart Pointers and the new/delete Mismatch

This issue affects smart pointers as well:

```cpp
// BAD: shared_ptr uses delete by default, not delete[]
std::shared_ptr<int> sp(new int[100]);   // Will call delete, not delete[]!

// GOOD: Use a custom deleter
std::shared_ptr<int> sp(new int[100], std::default_delete<int[]>());

// GOOD: unique_ptr has array specialization
std::unique_ptr<int[]> up(new int[100]); // Correctly calls delete[]
up[5] = 42;                              // operator[] is available

// BEST: Avoid raw arrays entirely
auto v = std::make_shared<std::vector<int>>(100);
```

### Practical Impact: A Debugging Nightmare

Consider this class hierarchy:

```cpp
class Widget {
public:
    Widget() { data_ = new char[1024]; }
    virtual ~Widget() { delete[] data_; }
private:
    char* data_;
};

class SpecialWidget : public Widget {
public:
    SpecialWidget() { extra_ = new char[2048]; }
    ~SpecialWidget() override { delete[] extra_; }
private:
    char* extra_;
};
```

```cpp
// BAD: Mismatched new/delete with polymorphic types
Widget* widgets = new SpecialWidget[10];
delete[] widgets;   // UNDEFINED BEHAVIOR even with delete[]!
// The compiler uses sizeof(Widget) to compute element offsets,
// but the actual objects are SpecialWidget (which is larger).
// Destructors are called at wrong addresses. Catastrophic.

// GOOD: Use a container of smart pointers
std::vector<std::unique_ptr<Widget>> widgets;
for (int i = 0; i < 10; ++i) {
    widgets.push_back(std::make_unique<SpecialWidget>());
}
// Each widget is individually allocated and correctly destroyed
```

### Complete Example: Demonstrating the Mismatch

```cpp
#include <iostream>
#include <memory>

class Tracked {
public:
    Tracked(int id) : id_(id) {
        std::cout << "Tracked(" << id_ << ") constructed\n";
    }
    ~Tracked() {
        std::cout << "Tracked(" << id_ << ") destroyed\n";
    }
private:
    int id_;
};

int main() {
    // --- Correct usage ---
    std::cout << "=== Correct: new[] with delete[] ===\n";
    Tracked* arr = new Tracked[3]{{1}, {2}, {3}};
    delete[] arr;
    // Output:
    // Tracked(1) constructed
    // Tracked(2) constructed
    // Tracked(3) constructed
    // Tracked(3) destroyed
    // Tracked(2) destroyed
    // Tracked(1) destroyed

    std::cout << "\n=== Correct: new with delete ===\n";
    Tracked* single = new Tracked(42);
    delete single;
    // Output:
    // Tracked(42) constructed
    // Tracked(42) destroyed

    // --- Smart pointer approaches ---
    std::cout << "\n=== unique_ptr with array ===\n";
    {
        std::unique_ptr<Tracked[]> uarr(new Tracked[3]{{10}, {20}, {30}});
        // Automatically calls delete[] when uarr goes out of scope
    }

    std::cout << "\n=== Best: vector ===\n";
    {
        std::vector<Tracked> v;
        v.reserve(3);
        v.emplace_back(100);
        v.emplace_back(200);
        v.emplace_back(300);
        // Automatically destroyed when v goes out of scope
    }

    return 0;
}
```

### Things to Remember

- **If you use `[]` in a `new` expression, you must use `[]` in the corresponding `delete`
  expression. If you do not use `[]` in `new`, do not use `[]` in `delete`.**

- **Typedefs can obscure the array nature of a type. Prefer `std::vector`, `std::array`, or
  smart pointers to avoid the ambiguity entirely.**

- **When in doubt, avoid `new[]` altogether. Use `std::vector` for dynamic arrays and
  `std::array` for fixed-size arrays. These manage their own memory and eliminate the
  `new`/`delete` mismatch problem.**

---
