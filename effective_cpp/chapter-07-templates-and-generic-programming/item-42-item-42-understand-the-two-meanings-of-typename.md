# Item 42: Understand the two meanings of typename

### Meaning 1: declaring template type parameters

In a template parameter list, `typename` and `class` are interchangeable:

```cpp
template <typename T>   // typename
class Widget { };

template <class T>      // class -- means exactly the same thing
class Widget { };
```

There is no semantic difference. `typename` was introduced later, and some programmers prefer it because it makes clear that `T` need not be a class type -- it could be `int`, `double`, or any other type. But both are valid, and the choice is purely stylistic.

### Meaning 2: disambiguating dependent names

This second meaning is where subtlety and real-world bugs live.

#### Dependent and non-dependent names

Inside a template, names that depend on a template parameter are called **dependent names**. Names that do not depend on a template parameter are **non-dependent names**:

```cpp
template <typename T>
void print(const T& container) {
    // "std::cout" is a non-dependent name -- it doesn't depend on T.
    // "container.size()" involves a dependent name -- size() depends on T.

    // T::const_iterator is a dependent name -- it depends on T.
    typename T::const_iterator it = container.begin();

    for (; it != container.end(); ++it)
        std::cout << *it << "\n";
}
```

#### The parsing ambiguity

When the compiler sees `T::const_iterator`, it does not know whether `const_iterator` is a type or a value. `T` is a template parameter, and until instantiation, the compiler cannot look inside `T` to find out. Consider:

```cpp
template <typename T>
void foo() {
    T::something * ptr;  // Ambiguity!
    // Is this a declaration of a pointer named "ptr" of type T::something?
    // Or is this a multiplication of T::something by ptr?
}
```

The C++ standard resolves this ambiguity with a rule: **a dependent qualified name is assumed to be a non-type (a value) unless preceded by `typename`.**

```cpp
template <typename T>
void foo() {
    typename T::something * ptr;  // Now unambiguous: ptr is a pointer to T::something
}
```

#### Real-world examples of when typename is required

**Accessing nested typedefs from template parameters:**

```cpp
template <typename Container>
void printAll(const Container& c) {
    // ERROR without typename: compiler assumes value_type is a value
    // typename Container::value_type element;

    typename Container::value_type element;  // Correct
    typename Container::const_iterator it;   // Correct

    for (it = c.begin(); it != c.end(); ++it) {
        element = *it;
        std::cout << element << " ";
    }
    std::cout << "\n";
}
```

**Using nested types in function return types:**

```cpp
template <typename Container>
typename Container::iterator findFirst(Container& c,
                                       const typename Container::value_type& val) {
    return std::find(c.begin(), c.end(), val);
}
```

**With `std::iterator_traits`:**

```cpp
template <typename Iterator>
void printIteratorValue(Iterator it) {
    // iterator_traits<Iterator>::value_type is a dependent type
    typename std::iterator_traits<Iterator>::value_type val = *it;
    std::cout << val << "\n";
}
```

**Inside class templates with dependent base classes:**

```cpp
template <typename T>
class Derived : public Base<T> {
public:
    void doWork() {
        // Base<T>::NestedType is a dependent name
        typename Base<T>::NestedType obj;
        // ...
    }
};
```

#### Where typename must NOT appear

There are two contexts where `typename` is not allowed even though a dependent name appears:

1. **Base class lists:**

```cpp
template <typename T>
class Derived : public Base<T>::Nested {  // typename NOT allowed here
    // ...
};
```

2. **Member initialization lists:**

```cpp
template <typename T>
class Derived : public Base<T>::Nested {
public:
    explicit Derived(int x)
        : Base<T>::Nested(x) {  // typename NOT allowed here
    }
};
```

The rationale: in both of these positions, the name can only be a type, so no disambiguation is needed.

#### Simplifying with typedef and using

The verbosity of `typename` can be tamed with type aliases:

```cpp
template <typename Iterator>
void workWithIterator(Iterator begin, Iterator end) {
    // Verbose:
    // typename std::iterator_traits<Iterator>::value_type temp = *begin;

    // Better: create a local typedef
    typedef typename std::iterator_traits<Iterator>::value_type value_type;
    value_type temp = *begin;

    // Or with C++11 using:
    using difference_type = typename std::iterator_traits<Iterator>::difference_type;
    difference_type dist = std::distance(begin, end);

    std::cout << "First: " << temp << ", distance: " << dist << "\n";
}
```

#### Compiler-specific behavior and portability

Some compilers (notably older versions of MSVC) historically did not enforce the `typename` requirement strictly, accepting code without `typename` where it was technically required. This means code that compiles on one compiler may fail on another. Always use `typename` where the standard demands it.

#### C++20 relaxation

C++20 relaxed the requirement for `typename` in many contexts where the compiler can unambiguously determine that a dependent name must be a type (e.g., in `static_cast`, `new` expressions, trailing return types, default arguments of type parameters). However, understanding the original rule remains important for reading legacy code and for contexts where the relaxation does not apply.

```cpp
// C++20: typename not required here because static_cast target must be a type
template <typename T>
void convert(T val) {
    auto result = static_cast<T::value_type>(val);  // OK in C++20
}
```

### Things to Remember

- When declaring template parameters, `class` and `typename` are interchangeable.
- Use `typename` to identify nested dependent type names, except in base class lists or as a base class identifier in a member initialization list.
- A nested dependent name is assumed to be a non-type unless you precede it with `typename`.
- Use `typedef` or `using` to create convenient aliases for long `typename`-qualified dependent names.

---
