# Item 47: Use traits classes for information about types

## Visual Summary

```text
┌───────────────────────────────────────────────────────────────────────────┐
│          ITEM 47: USE TRAITS CLASSES FOR INFORMATION ABOUT TYPES          │
├───────────────────────────────────────────────────────────────────────────┤
│ 1. Generic algorithm needs type-specific facts.                           │
│ 2. Traits class maps type -> compile-time properties/tags.                │
│ 3. Algorithm dispatches by tag or constexpr condition.                    │
│ 4. Specialize traits for new types without rewriting algorithm.           │
│ 5. Meaning: traits move type knowledge into reusable compile-time         │
│ metadata.                                                                 │
└───────────────────────────────────────────────────────────────────────────┘
```

## Visual Deep Dive

```text
┌───────────────────────────────────────────────────────────────────────────┐
│                           TRAITS DISPATCH FLOW                            │
├───────────────────────────────────────────────────────────────────────────┤
│ Generic algorithm receives iterator/type T                                │
│                                     ▼                                     │
│ traits<T> exposes category/properties                                     │
│                                     ▼                                     │
│ Algorithm selects optimized implementation by tag                         │
│                                     ▼                                     │
│ New types specialize traits, not the algorithm                            │
└───────────────────────────────────────────────────────────────────────────┘
```

```text
┌───────────────────────────────────────────────────────────────────────────┐
│                               TRAITS SHAPE                                │
├───────────────────────────────────────────────────────────────────────────┤
│ Input type -> traits class -> compile-time metadata                       │
│ Examples: value_type, iterator_category, is_pointer, is_integral          │
│ Purpose: ask questions about types without runtime cost                   │
└───────────────────────────────────────────────────────────────────────────┘
```

### The need for type information at compile time

Consider writing an `advance` function that moves an iterator forward by `n` positions:

```cpp
template <typename IterT, typename DistT>
void advance(IterT& iter, DistT d) {
    iter += d;  // Only works for random access iterators!
}
```

For input iterators, you must use `++iter` in a loop. For bidirectional iterators, you can go backward with `--iter`. For random access iterators, you can use `iter += d`. The optimal implementation depends on the **iterator category**, which is a compile-time property.

### Iterator categories (the five kinds)

The C++ standard defines five iterator categories, forming a hierarchy:

```
input iterator         output iterator
       \                  /
        forward iterator
              |
        bidirectional iterator
              |
        random access iterator
```

Each category has a tag type:

```cpp
struct input_iterator_tag { };
struct output_iterator_tag { };
struct forward_iterator_tag : input_iterator_tag { };
struct bidirectional_iterator_tag : forward_iterator_tag { };
struct random_access_iterator_tag : bidirectional_iterator_tag { };
```

### Traits: a convention for compile-time type information

A traits class is a template that provides information about a type. The standard library's `iterator_traits` works like this:

```cpp
template <typename IterT>
struct iterator_traits {
    typedef typename IterT::iterator_category iterator_category;
    typedef typename IterT::value_type        value_type;
    typedef typename IterT::difference_type   difference_type;
    typedef typename IterT::pointer           pointer;
    typedef typename IterT::reference         reference;
};
```

For user-defined iterators, you embed the information in the class:

```cpp
template <typename T>
class LinkedListIterator {
public:
    // Nested typedefs that iterator_traits will pick up
    using iterator_category = std::bidirectional_iterator_tag;
    using value_type        = T;
    using difference_type   = std::ptrdiff_t;
    using pointer           = T*;
    using reference         = T&;

    // Iterator operations...
    LinkedListIterator& operator++() { node_ = node_->next; return *this; }
    LinkedListIterator& operator--() { node_ = node_->prev; return *this; }
    T& operator*() { return node_->data; }
    // ...

private:
    struct Node { T data; Node* next; Node* prev; };
    Node* node_;
};
```

### Handling raw pointers with partial specialization

Raw pointers are iterators too, but they have no nested typedefs. `iterator_traits` uses partial specialization:

```cpp
// Partial specialization for pointer types
template <typename T>
struct iterator_traits<T*> {
    typedef random_access_iterator_tag iterator_category;
    typedef T                          value_type;
    typedef std::ptrdiff_t             difference_type;
    typedef T*                         pointer;
    typedef T&                         reference;
};

// Partial specialization for const pointer types
template <typename T>
struct iterator_traits<const T*> {
    typedef random_access_iterator_tag iterator_category;
    typedef T                          value_type;
    typedef std::ptrdiff_t             difference_type;
    typedef const T*                   pointer;
    typedef const T&                   reference;
};
```

Now `iterator_traits<int*>::iterator_category` is `random_access_iterator_tag`, which is correct -- raw pointers support random access.

### Using traits: tag dispatch

You cannot use `if` statements with types -- `if (typeid(...) == ...)` evaluates at runtime and would require all branches to compile. Instead, use **tag dispatch** (also known as compile-time dispatch):

```cpp
// Implementation for input iterators: increment one at a time
template <typename IterT, typename DistT>
void doAdvance(IterT& iter, DistT d, std::input_iterator_tag) {
    if (d < 0) {
        throw std::out_of_range("Negative distance on input iterator");
    }
    while (d--) ++iter;
}

// Implementation for bidirectional iterators: can go backward
template <typename IterT, typename DistT>
void doAdvance(IterT& iter, DistT d, std::bidirectional_iterator_tag) {
    if (d >= 0) { while (d--) ++iter; }
    else        { while (d++) --iter; }
}

// Implementation for random access iterators: O(1)
template <typename IterT, typename DistT>
void doAdvance(IterT& iter, DistT d, std::random_access_iterator_tag) {
    iter += d;
}

// The public interface: uses traits to dispatch
template <typename IterT, typename DistT>
void advance(IterT& iter, DistT d) {
    doAdvance(iter, d,
              typename std::iterator_traits<IterT>::iterator_category());
    //        ^^^^^^^^
    //        Creates a temporary tag object; overload resolution picks
    //        the right doAdvance at compile time.
}
```

The tag inheritance hierarchy means that `forward_iterator_tag` inherits from `input_iterator_tag`, so a forward iterator will match the input iterator overload (which is correct -- forward iterators can only advance forward).

### Building your own traits class: a complete example

Suppose you have a serialization library and need different strategies for different types:

```cpp
#include <iostream>
#include <string>
#include <vector>
#include <type_traits>

// Step 1: Define tag types for serialization categories
struct PrimitiveSerialization {};
struct StringSerialization {};
struct ContainerSerialization {};
struct CustomSerialization {};

// Step 2: Define the traits template (default: custom)
template <typename T, typename Enable = void>
struct serialization_traits {
    using category = CustomSerialization;
};

// Step 3: Specialize for primitive types using SFINAE
template <typename T>
struct serialization_traits<T, std::enable_if_t<std::is_arithmetic_v<T>>> {
    using category = PrimitiveSerialization;
};

// Step 4: Specialize for strings
template <>
struct serialization_traits<std::string> {
    using category = StringSerialization;
};

// Step 5: Specialize for containers (anything with begin/end and value_type)
template <typename T>
struct serialization_traits<std::vector<T>> {
    using category = ContainerSerialization;
};

// Step 6: Implement the overloaded serialization functions
template <typename T>
void doSerialize(const T& value, std::ostream& os, PrimitiveSerialization) {
    os.write(reinterpret_cast<const char*>(&value), sizeof(T));
}

template <typename T>
void doSerialize(const T& value, std::ostream& os, StringSerialization) {
    auto size = value.size();
    os.write(reinterpret_cast<const char*>(&size), sizeof(size));
    os.write(value.data(), size);
}

template <typename T>
void doSerialize(const T& container, std::ostream& os, ContainerSerialization) {
    auto size = container.size();
    os.write(reinterpret_cast<const char*>(&size), sizeof(size));
    for (const auto& elem : container) {
        serialize(elem, os);  // Recursive: each element uses its own traits
    }
}

// Step 7: Public interface with tag dispatch
template <typename T>
void serialize(const T& value, std::ostream& os) {
    doSerialize(value, os,
                typename serialization_traits<T>::category());
}
```

### C++17 and beyond: `if constexpr` as an alternative to tag dispatch

In C++17, `if constexpr` provides a more direct way to branch on compile-time conditions:

```cpp
template <typename IterT, typename DistT>
void advance(IterT& iter, DistT d) {
    using category = typename std::iterator_traits<IterT>::iterator_category;

    if constexpr (std::is_base_of_v<std::random_access_iterator_tag, category>) {
        iter += d;  // O(1) for random access
    } else if constexpr (std::is_base_of_v<std::bidirectional_iterator_tag, category>) {
        if (d >= 0) { while (d--) ++iter; }
        else        { while (d++) --iter; }
    } else {
        if (d < 0) throw std::out_of_range("Negative distance");
        while (d--) ++iter;
    }
}
```

With `if constexpr`, branches that do not match are discarded at compile time, so they do not need to be valid for the given type. This is a significant advantage over regular `if` statements.

### SFINAE: Substitution Failure Is Not An Error

SFINAE is the mechanism that enables `enable_if` and many advanced traits techniques. When the compiler substitutes template arguments and the result is invalid, it does not produce a hard error -- it simply removes that overload from consideration:

```cpp
// Only enabled for integral types
template <typename T>
std::enable_if_t<std::is_integral_v<T>, T>
safeDivide(T a, T b) {
    if (b == 0) throw std::domain_error("Division by zero");
    return a / b;
}

// Only enabled for floating-point types
template <typename T>
std::enable_if_t<std::is_floating_point_v<T>, T>
safeDivide(T a, T b) {
    if (b == T(0)) return std::numeric_limits<T>::infinity();
    return a / b;
}

int main() {
    std::cout << safeDivide(10, 3) << "\n";     // Calls integral version: 3
    std::cout << safeDivide(10.0, 3.0) << "\n"; // Calls floating version: 3.33333
    // safeDivide("hello", "world");             // No matching overload -- SFINAE
}
```

### Type traits in the standard library

The `<type_traits>` header provides a rich set of compile-time type queries:

```cpp
#include <type_traits>

// Primary type categories
static_assert(std::is_integral_v<int>);
static_assert(std::is_floating_point_v<double>);
static_assert(std::is_pointer_v<int*>);
static_assert(std::is_reference_v<int&>);
static_assert(std::is_class_v<std::string>);
static_assert(std::is_enum_v<std::byte>);

// Type properties
static_assert(std::is_const_v<const int>);
static_assert(std::is_trivially_copyable_v<int>);
static_assert(std::is_polymorphic_v<std::ostream>);

// Type relationships
static_assert(std::is_base_of_v<std::ios_base, std::ostream>);
static_assert(std::is_convertible_v<int, double>);
static_assert(std::is_same_v<int, int>);

// Type transformations
using T1 = std::remove_const_t<const int>;         // int
using T2 = std::remove_reference_t<int&>;           // int
using T3 = std::add_pointer_t<int>;                  // int*
using T4 = std::decay_t<const int&>;                 // int
using T5 = std::conditional_t<true, int, double>;    // int
```

### Implementing a simple type trait

```cpp
// is_same: check if two types are the same
template <typename T, typename U>
struct my_is_same {
    static constexpr bool value = false;
};

template <typename T>
struct my_is_same<T, T> {  // Partial specialization when both types match
    static constexpr bool value = true;
};

// is_pointer
template <typename T>
struct my_is_pointer {
    static constexpr bool value = false;
};

template <typename T>
struct my_is_pointer<T*> {
    static constexpr bool value = true;
};

// has_type_member: detect if a type has a nested ::type typedef (using SFINAE)
template <typename T, typename = void>
struct has_type_member : std::false_type {};

template <typename T>
struct has_type_member<T, std::void_t<typename T::type>> : std::true_type {};

// Usage:
struct WithType { using type = int; };
struct WithoutType { int value; };

static_assert(has_type_member<WithType>::value);
static_assert(!has_type_member<WithoutType>::value);
```

### Things to Remember

- Traits classes make information about types available during compilation. They are implemented using templates and template specializations.
- In conjunction with overloading, traits classes make it possible to perform compile-time `if...else` tests on types (tag dispatch).
- The standard library provides `iterator_traits`, `char_traits`, `numeric_limits`, `allocator_traits`, and the extensive `<type_traits>` header as pre-built traits facilities.
- SFINAE (Substitution Failure Is Not An Error) is the mechanism that makes many traits techniques possible, including `std::enable_if`.
- In C++17, `if constexpr` provides a more readable alternative to tag dispatch for compile-time branching.

---
