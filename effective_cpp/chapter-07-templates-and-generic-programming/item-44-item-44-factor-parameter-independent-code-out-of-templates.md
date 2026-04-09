# Item 44: Factor parameter-independent code out of templates

### The code bloat problem

Templates generate code for each set of template arguments. If the generated code contains logic that does not actually depend on the template parameters, you get **code bloat** -- multiple identical (or nearly identical) copies of functions in your binary.

```cpp
// Naive implementation: generates separate code for every N
template <typename T, std::size_t N>
class SquareMatrix {
public:
    void invert() {
        // Complex matrix inversion algorithm
        // This code is identical for SquareMatrix<double, 5> and
        // SquareMatrix<double, 10> except for the value of N.
        // But the compiler generates it twice.
    }

private:
    T data_[N * N];
};

// Each of these generates a SEPARATE copy of invert():
SquareMatrix<double, 5> m5;
SquareMatrix<double, 10> m10;
SquareMatrix<double, 5> m5b;   // Same as m5 -- no new code generated
SquareMatrix<float, 5> mf5;    // Different T -- new code is expected
```

`SquareMatrix<double, 5>::invert()` and `SquareMatrix<double, 10>::invert()` will be separate functions even though their logic is fundamentally the same -- only the dimension differs.

### Solution: factor parameter-independent code into a base class

Move the code that does not depend on the non-type parameter into a base class that takes the dimension as a runtime parameter:

```cpp
// Base class: knows dimension at runtime, not compile time
template <typename T>
class SquareMatrixBase {
protected:
    SquareMatrixBase(std::size_t n, T* pMem)
        : size_(n), pData_(pMem) {}

    void invert() {
        // Single copy of inversion code, parameterized by size_
        // Works for any dimension
        doInversion(pData_, size_);
    }

    void setDataPtr(T* ptr) { pData_ = ptr; }

private:
    std::size_t size_;
    T* pData_;

    void doInversion(T* data, std::size_t n) {
        // Actual inversion logic -- only one copy exists per T
        // ...
    }
};

// Derived class: adds the compile-time dimension and storage
template <typename T, std::size_t N>
class SquareMatrix : private SquareMatrixBase<T> {
public:
    SquareMatrix()
        : SquareMatrixBase<T>(N, data_) {}

    // Thin inline wrapper -- compiled per N, but trivially small
    void invert() {
        SquareMatrixBase<T>::invert();
    }

private:
    T data_[N * N];
};
```

Now `SquareMatrix<double, 5>::invert()` and `SquareMatrix<double, 10>::invert()` both call the same `SquareMatrixBase<double>::invert()`. The per-N code is just a tiny inline forwarding function.

### Storage strategies

The base class needs access to the matrix data. There are several strategies:

**Strategy 1: Pointer from derived (shown above)**

```cpp
template <typename T>
class SquareMatrixBase {
protected:
    SquareMatrixBase(std::size_t n, T* pMem) : size_(n), pData_(pMem) {}
    // ...
private:
    std::size_t size_;
    T* pData_;
};

template <typename T, std::size_t N>
class SquareMatrix : private SquareMatrixBase<T> {
    T data_[N * N];  // Storage is in the derived class
public:
    SquareMatrix() : SquareMatrixBase<T>(N, data_) {}
};
```

**Strategy 2: Heap allocation in the base class**

```cpp
template <typename T>
class SquareMatrixBase {
protected:
    explicit SquareMatrixBase(std::size_t n)
        : size_(n), pData_(new T[n * n]()) {}

    ~SquareMatrixBase() { delete[] pData_; }

    void invert() { /* uses pData_ and size_ */ }

private:
    std::size_t size_;
    T* pData_;
};

template <typename T, std::size_t N>
class SquareMatrix : private SquareMatrixBase<T> {
public:
    SquareMatrix() : SquareMatrixBase<T>(N) {}
    using SquareMatrixBase<T>::invert;
};
```

### Non-type parameters are the most common bloat source

Non-type template parameters (like `std::size_t N`) are the most obvious source of bloat because the code is often identical across different values of N. But type parameters can also cause bloat:

```cpp
// These three instantiations generate three copies of all member functions,
// but on most platforms int*, long*, and Widget* are all the same size.
template <typename T>
class SmartPtr {
public:
    T* get() const { return ptr_; }
    void reset(T* p) { delete ptr_; ptr_ = p; }
    // 20 more member functions...
private:
    T* ptr_;
};

SmartPtr<int> p1;
SmartPtr<long> p2;
SmartPtr<Widget> p3;
```

The fix: implement the core logic in terms of `void*` and have the typed template provide thin inline wrappers:

```cpp
// Untyped base -- one copy of the implementation
class SmartPtrBase {
protected:
    SmartPtrBase(void* p) : ptr_(p) {}
    void* get() const { return ptr_; }
    void setPtr(void* p) { ptr_ = p; }
private:
    void* ptr_;
};

// Typed wrapper -- only inline casts, no real code duplication
template <typename T>
class SmartPtr : private SmartPtrBase {
public:
    explicit SmartPtr(T* p = nullptr) : SmartPtrBase(p) {}

    T* get() const {
        return static_cast<T*>(SmartPtrBase::get());
    }

    void reset(T* p) {
        delete static_cast<T*>(SmartPtrBase::get());
        SmartPtrBase::setPtr(p);
    }
};
```

This pattern is used in real-world standard library implementations. For example, many implementations of `std::vector` share a single implementation for all pointer types.

### Measuring bloat

Before optimizing, measure:

```bash
# On Linux/Mac, list symbol sizes in an object file
nm --size-sort --print-size your_binary | c++filt | grep "SquareMatrix"

# Or use bloaty for a higher-level view
bloaty your_binary -d compileunits
```

### The trade-off

Factoring out parameter-independent code reduces binary size but can:
- Reduce compile-time optimization opportunities (the compiler knows the dimension at compile time and can unroll loops, vectorize, etc.)
- Add indirection through base class pointers
- Make the code harder to read

For hot inner loops (matrix math, signal processing), keeping the non-type parameter may be worth the bloat because the compiler can aggressively optimize. For less performance-critical code, factoring it out is usually the right call.

```cpp
// When performance is critical, keep the compile-time parameter:
template <typename T, std::size_t N>
class SmallMatrix {
public:
    // Compiler can fully unroll this loop for small N
    void multiply(const SmallMatrix& rhs, SmallMatrix& result) const {
        for (std::size_t i = 0; i < N; ++i)
            for (std::size_t j = 0; j < N; ++j) {
                T sum = T();
                for (std::size_t k = 0; k < N; ++k)
                    sum += data_[i * N + k] * rhs.data_[k * N + j];
                result.data_[i * N + j] = sum;
            }
    }
private:
    T data_[N * N];
};
```

### Things to Remember

- Templates generate multiple classes and multiple functions, so any template code not dependent on a template parameter causes bloat.
- Bloat due to non-type template parameters can often be eliminated by replacing template parameters with function parameters or class data members.
- Bloat due to type parameters can be reduced by sharing implementations for instantiation types that have the same binary representations (e.g., all pointer types can share a single `void*`-based implementation).

---
