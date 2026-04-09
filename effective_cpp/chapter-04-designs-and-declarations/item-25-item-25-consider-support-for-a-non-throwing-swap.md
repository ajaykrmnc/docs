# Item 25: Consider Support for a Non-Throwing Swap

`swap` is one of the most important functions in C++. It is central to exception-safe
programming (see Item 29), to the copy-and-swap idiom for assignment operators, and to
guarding against self-assignment (see Item 11). This item explains how to write an
efficient, non-throwing swap for your types.

### The Default std::swap

The default `std::swap` implementation uses a temporary and three copies:

```cpp
namespace std {

template<typename T>
void swap(T& a, T& b) {
    T temp(a);   // Copy a
    a = b;       // Copy b into a
    b = temp;    // Copy temp into b
}

}  // namespace std
```

For types that are expensive to copy, this is wasteful. Many types can be swapped far
more efficiently -- for example, by just swapping internal pointers.

### The Pimpl Idiom: Where Default Swap Hurts

```cpp
// A Widget that uses the Pimpl (Pointer to Implementation) idiom
class WidgetImpl {
public:
    // ... lots of data ...
private:
    int a, b, c;
    std::vector<double> v;
    std::map<std::string, std::string> m;
    // ... potentially huge ...
};

class Widget {
public:
    Widget(const Widget& rhs);
    Widget& operator=(const Widget& rhs) {
        // Copy all of rhs's WidgetImpl data
        *pImpl = *(rhs.pImpl);
        return *this;
    }

private:
    WidgetImpl* pImpl;  // Pointer to the implementation
};
```

Swapping two `Widget` objects using the default `std::swap` copies three `Widget` objects,
which means copying three `WidgetImpl` objects -- extremely expensive. But all we really
need to do is swap the `pImpl` pointers.

### Step 1: Write a Member swap Function

```cpp
class Widget {
public:
    void swap(Widget& other) {
        using std::swap;           // Make std::swap available as a fallback
        swap(pImpl, other.pImpl);  // Just swap the pointers -- O(1)!
    }

    // ...

private:
    WidgetImpl* pImpl;
};
```

### Step 2: Specialize std::swap for Your Non-Template Class

```cpp
namespace std {

// Total specialization of std::swap for Widget
template<>
void swap<Widget>(Widget& a, Widget& b) {
    a.swap(b);  // Delegate to the member function
}

}  // namespace std
```

This is legal -- the C++ standard allows you to **totally specialize** templates in `std`
for user-defined types.

### Step 3: For Class Templates, Use a Non-Member swap in Your Namespace

If `Widget` is itself a class template, you **cannot** partially specialize `std::swap`:

```cpp
// Widget is now a template
template<typename T>
class Widget {
public:
    void swap(Widget<T>& other) {
        using std::swap;
        swap(pImpl, other.pImpl);
    }

private:
    WidgetImpl<T>* pImpl;
};

// BAD: You CANNOT partially specialize a function template!
namespace std {
template<typename T>
void swap<Widget<T>>(Widget<T>& a, Widget<T>& b) {  // ILLEGAL!
    a.swap(b);
}
}

// BAD: You could OVERLOAD std::swap, but adding new functions to std is
// undefined behavior (only specializations are allowed):
namespace std {
template<typename T>
void swap(Widget<T>& a, Widget<T>& b) {  // Technically undefined behavior!
    a.swap(b);
}
}
```

The solution: declare a non-member `swap` in **your own namespace**:

```cpp
namespace WidgetStuff {

template<typename T>
class Widget { /* ... as above ... */ };

// Non-member swap in the same namespace as Widget
template<typename T>
void swap(Widget<T>& a, Widget<T>& b) {
    a.swap(b);
}

}  // namespace WidgetStuff
```

ADL (Koenig Lookup) ensures that when client code calls `swap` on two `Widget<T>` objects,
the compiler finds `WidgetStuff::swap` because it looks in the namespace of the argument types.

### The Correct Way to Call swap

When writing generic code that uses `swap`, you need to ensure both the `std::swap` default
and any type-specific `swap` are considered:

```cpp
template<typename T>
void doSomething(T& obj1, T& obj2) {
    using std::swap;       // Make std::swap visible as a fallback
    swap(obj1, obj2);      // Let the compiler choose the best swap:
                            // 1. If there's a T-specific swap in T's namespace, ADL finds it.
                            // 2. If there's a std::swap<T> specialization, it's considered.
                            // 3. Otherwise, the default std::swap is used.
}
```

```cpp
// BAD: Qualifying the call prevents ADL from finding type-specific swap:
template<typename T>
void doSomething(T& obj1, T& obj2) {
    std::swap(obj1, obj2);  // ALWAYS uses std::swap!
                             // Will NOT find WidgetStuff::swap<Widget<T>>
                             // even though it's more efficient.
}
```

### Complete Example: Putting It All Together

```cpp
// For a non-template class:

class NetworkBuffer {
public:
    NetworkBuffer() : data_(nullptr), size_(0) {}
    NetworkBuffer(size_t size) : data_(new char[size]), size_(size) {}

    NetworkBuffer(const NetworkBuffer& rhs)
        : data_(new char[rhs.size_]), size_(rhs.size_) {
        std::memcpy(data_, rhs.data_, size_);
    }

    // Copy-and-swap idiom for exception-safe assignment
    NetworkBuffer& operator=(NetworkBuffer rhs) {  // Note: pass by value
        swap(rhs);        // Swap our guts with the copy's guts
        return *this;     // The copy's destructor cleans up our old data
    }

    ~NetworkBuffer() { delete[] data_; }

    // Member swap -- efficient, non-throwing
    void swap(NetworkBuffer& other) noexcept {
        using std::swap;
        swap(data_, other.data_);    // Swap pointers -- O(1), noexcept
        swap(size_, other.size_);    // Swap sizes -- O(1), noexcept
    }

private:
    char* data_;
    size_t size_;
};

// Non-member swap in the same namespace
void swap(NetworkBuffer& a, NetworkBuffer& b) noexcept {
    a.swap(b);
}

// Also specialize std::swap
namespace std {
template<>
void swap<NetworkBuffer>(NetworkBuffer& a, NetworkBuffer& b) noexcept {
    a.swap(b);
}
}
```

### The noexcept Guarantee

Highly efficient swaps are almost always non-throwing. This is important because:

1. The copy-and-swap idiom depends on a non-throwing swap for strong exception safety.
2. Many standard library operations (e.g., `std::sort`, `std::vector` reallocation)
   work more efficiently when swap doesn't throw.

```cpp
class Widget {
public:
    // The member swap should be noexcept
    void swap(Widget& other) noexcept {
        using std::swap;
        swap(pImpl, other.pImpl);  // Pointer swap never throws
    }
};

// Built-in types (pointers, ints, etc.) can always be swapped without throwing.
// If your class's swap only swaps built-in types (like pointers), it should be noexcept.
```

### Summary of the swap Protocol

| Scenario | What to do |
|----------|------------|
| Non-template class | 1. Write a public `swap` member function (noexcept). <br> 2. Write a non-member `swap` in your namespace that calls the member. <br> 3. Specialize `std::swap` to call the member. |
| Class template | 1. Write a public `swap` member function (noexcept). <br> 2. Write a non-member `swap` in your namespace that calls the member. <br> 3. Do NOT partially specialize or overload `std::swap`. |
| Calling swap in generic code | Always do `using std::swap;` followed by an unqualified call to `swap`. |

### Things to Remember

- Provide a `swap` member function when `std::swap` would be inefficient for your type.
  Make sure your `swap` doesn't throw exceptions.
- If you offer a member `swap`, also offer a non-member `swap` that calls the member.
  For classes (not templates), specialize `std::swap`, too.
- When calling `swap`, employ a `using` declaration for `std::swap`, then call `swap`
  without namespace qualification.
- It's fine to totally specialize `std` templates for user-defined types, but never try
  to add something completely new to `std`.

---
