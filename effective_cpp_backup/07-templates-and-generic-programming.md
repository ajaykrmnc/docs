# Chapter 7: Templates and Generic Programming

Templates are the foundation of generic programming in C++. They move part of the type-checking work from runtime to compile time, enable code reuse without sacrificing type safety, and open the door to an entirely separate computation model -- template metaprogramming -- that executes during compilation. This chapter covers Items 41-48 of Scott Meyers' *Effective C++* (Third Edition), spanning implicit interfaces, the `typename` disambiguator, accessing names in templatized base classes, code bloat, member function templates, friend functions in templates, traits classes, and template metaprogramming.

---

## Item 41: Understand implicit interfaces and compile-time polymorphism

### The two worlds of polymorphism

Object-oriented programming revolves around **explicit interfaces** and **runtime polymorphism**:

```cpp
// Explicit interface: the class declaration spells out every operation.
class Widget {
public:
    Widget();
    virtual ~Widget();
    virtual std::size_t size() const;
    virtual void normalize();
    void swap(Widget& other);
};

// Runtime polymorphism: which size() runs is determined at runtime
// via the vtable.
void doProcessing(Widget& w) {
    if (w.size() > 10 && w != someNastyWidget) {
        Widget temp(w);
        temp.normalize();
        temp.swap(w);
    }
}
```

The interface of `Widget` is explicit -- you can open the header file and see every member function signature, every typedef, every data member. Polymorphism happens at runtime through virtual functions and the vtable mechanism.

Templates flip both of these on their head:

```cpp
template <typename T>
void doProcessing(T& w) {
    if (w.size() > 10 && w != someNastyWidget) {
        T temp(w);
        temp.normalize();
        temp.swap(w);
    }
}
```

Now `T` must support an **implicit interface**: it must have a `size()` member function that returns something comparable to `int`, it must support `operator!=`, it must be copy-constructible, and it must have a `normalize()` and `swap()` member function. But none of this is stated in any single class declaration -- it is implied by how `T` is used in the template body.

The polymorphism here is **compile-time**: which `size()` to call, which `operator!=` to invoke, etc., is resolved when the template is instantiated. The mechanism is template instantiation, not vtable dispatch.

### Implicit interfaces in detail

An implicit interface is defined by the set of valid expressions that appear in the template, not by specific function signatures. Consider:

```cpp
template <typename T>
void process(T& obj) {
    // Implicit interface requirement: T must support .begin() and .end()
    // returning iterators, and the iterators must be dereferenceable.
    for (auto it = obj.begin(); it != obj.end(); ++it) {
        std::cout << *it << "\n";
    }
}
```

Any type that satisfies these constraints works:

```cpp
std::vector<int> v = {1, 2, 3};
process(v);  // OK: vector has begin(), end(), iterators support * and !=

std::list<std::string> l = {"hello", "world"};
process(l);  // OK: list also satisfies the implicit interface

std::map<int, double> m = {{1, 1.1}, {2, 2.2}};
process(m);  // OK: map's iterators dereference to std::pair, which supports <<
              // only if operator<< is defined for pair -- this would fail at
              // compile time, illustrating the implicit interface check.
```

### Constraints are on expressions, not types

A crucial insight: the implicit interface does not require that `size()` returns an integral type. It requires that the expression `w.size() > 10` is valid and yields something convertible to `bool`. This is far more flexible:

```cpp
class Gadget {
public:
    // size() returns a custom type, not size_t
    SizeProxy size() const;
    void normalize();
    void swap(Gadget& other);
};

// This is fine as long as SizeProxy supports operator>(int)
// and the result is convertible to bool.
class SizeProxy {
public:
    bool operator>(int rhs) const { return value_ > rhs; }
private:
    int value_;
};
```

### Compile-time polymorphism with CRTP

The Curiously Recurring Template Pattern (CRTP) is a powerful form of compile-time polymorphism:

```cpp
template <typename Derived>
class Shape {
public:
    double area() const {
        // Compile-time dispatch: calls the derived class's implementation
        return static_cast<const Derived*>(this)->area_impl();
    }

    void print() const {
        std::cout << "Area: " << area() << "\n";
    }
};

class Circle : public Shape<Circle> {
    double radius_;
public:
    explicit Circle(double r) : radius_(r) {}
    double area_impl() const { return 3.14159265 * radius_ * radius_; }
};

class Rectangle : public Shape<Rectangle> {
    double w_, h_;
public:
    Rectangle(double w, double h) : w_(w), h_(h) {}
    double area_impl() const { return w_ * h_; }
};

template <typename ShapeType>
void displayArea(const Shape<ShapeType>& s) {
    s.print();  // Compile-time polymorphism, no vtable
}

int main() {
    Circle c(5.0);
    Rectangle r(3.0, 4.0);
    displayArea(c);  // "Area: 78.5398"
    displayArea(r);  // "Area: 12"
}
```

No virtual functions, no vtable overhead -- the dispatch is resolved entirely at compile time.

### Combining both kinds of polymorphism

In real systems you often use both. Runtime polymorphism lets you store heterogeneous objects in containers; compile-time polymorphism gives you zero-overhead abstraction:

```cpp
// Runtime polymorphism for a plugin system
class Renderer {
public:
    virtual ~Renderer() = default;
    virtual void render(const Scene& scene) = 0;
};

// Compile-time polymorphism for a high-performance math library
template <typename T>
T dot(const std::vector<T>& a, const std::vector<T>& b) {
    T result = T();
    for (std::size_t i = 0; i < a.size(); ++i)
        result += a[i] * b[i];
    return result;
}
```

### Things to Remember

- Both classes and templates support interfaces and polymorphism.
- For classes, interfaces are explicit and centered on function signatures. Polymorphism occurs at runtime through virtual functions.
- For template parameters, interfaces are implicit and based on valid expressions. Polymorphism occurs at compile time through template instantiation and function overloading resolution.
- Implicit interface constraints are on expressions, not on types. An expression like `w.size() > 10` does not mandate a particular return type for `size()` -- only that the complete expression is valid and yields something convertible to `bool`.

---

## Item 42: Understand the two meanings of typename

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

## Item 43: Know how to access names in templatized base classes

### The problem: names in dependent base classes are invisible

Consider a messaging system with compile-time selection of the transport:

```cpp
class CompanyA {
public:
    void sendCleartext(const std::string& msg) { /* ... */ }
    void sendEncrypted(const std::string& msg) { /* ... */ }
};

class CompanyB {
public:
    void sendCleartext(const std::string& msg) { /* ... */ }
    void sendEncrypted(const std::string& msg) { /* ... */ }
};

template <typename Company>
class MsgSender {
public:
    void sendClear(const std::string& info) {
        Company c;
        c.sendCleartext(info);
    }

    void sendSecret(const std::string& info) {
        Company c;
        c.sendEncrypted(info);
    }
};
```

Now a derived class that logs every message:

```cpp
template <typename Company>
class LoggingMsgSender : public MsgSender<Company> {
public:
    void sendClearMsg(const std::string& info) {
        // write "before sending" to log
        sendClear(info);  // ERROR! Won't compile!
        // write "after sending" to log
    }
};
```

This fails because the compiler refuses to look inside `MsgSender<Company>` for `sendClear`. Why? Because `Company` is a template parameter, and there could be a **total specialization** of `MsgSender` that does not have `sendClear`:

```cpp
// A company for which encrypted-only communication is mandated.
class CompanyZ {
public:
    void sendEncrypted(const std::string& msg) { /* ... */ }
    // No sendCleartext!
};

// Total specialization: MsgSender<CompanyZ> has no sendClear()
template <>
class MsgSender<CompanyZ> {
public:
    void sendSecret(const std::string& info) {
        CompanyZ c;
        c.sendEncrypted(info);
    }
    // No sendClear() here!
};
```

Because `MsgSender<CompanyZ>` does not have `sendClear`, the compiler is right to refuse to assume it exists in the general case. The standard says: **names in dependent base classes are not examined during unqualified lookup**.

### Solution 1: `this->`

Prefix the call with `this->` to make it a dependent expression, deferring lookup to instantiation time:

```cpp
template <typename Company>
class LoggingMsgSender : public MsgSender<Company> {
public:
    void sendClearMsg(const std::string& info) {
        logToFile("Before sending");
        this->sendClear(info);  // OK: defers lookup to instantiation time
        logToFile("After sending");
    }
};
```

This is the most common and recommended approach.

### Solution 2: `using` declaration

Bring the base class name into the derived class's scope:

```cpp
template <typename Company>
class LoggingMsgSender : public MsgSender<Company> {
public:
    using MsgSender<Company>::sendClear;  // Make sendClear visible

    void sendClearMsg(const std::string& info) {
        logToFile("Before sending");
        sendClear(info);  // OK: using declaration made it visible
        logToFile("After sending");
    }
};
```

### Solution 3: Explicit qualification

Qualify the call with the base class name:

```cpp
template <typename Company>
class LoggingMsgSender : public MsgSender<Company> {
public:
    void sendClearMsg(const std::string& info) {
        logToFile("Before sending");
        MsgSender<Company>::sendClear(info);  // OK but problematic
        logToFile("After sending");
    }
};
```

This works but has a significant drawback: **it suppresses virtual dispatch**. If `sendClear` were virtual, this would always call the base class version, never an overridden version. For this reason, `this->` or `using` declarations are generally preferred.

### A comprehensive real-world example

Consider a policy-based design for database operations:

```cpp
// Policy for SQL generation
template <typename Dialect>
class SQLGenerator {
public:
    std::string generateSelect(const std::string& table,
                               const std::vector<std::string>& cols) {
        return Dialect::selectPrefix() + buildColumnList(cols) + " FROM " + table;
    }

protected:
    std::string buildColumnList(const std::vector<std::string>& cols) {
        std::string result;
        for (size_t i = 0; i < cols.size(); ++i) {
            if (i > 0) result += ", ";
            result += Dialect::quoteIdentifier(cols[i]);
        }
        return result;
    }

    std::string escapeString(const std::string& s) {
        return Dialect::escapeImpl(s);
    }
};

// Extended generator that adds WHERE clause support
template <typename Dialect>
class FilteredSQLGenerator : public SQLGenerator<Dialect> {
public:
    // Must use this-> or using declarations to access base class members

    using SQLGenerator<Dialect>::generateSelect;
    using SQLGenerator<Dialect>::escapeString;

    std::string generateFilteredSelect(
            const std::string& table,
            const std::vector<std::string>& cols,
            const std::string& whereClause) {
        // Without the using declarations above, these calls would fail:
        std::string base = generateSelect(table, cols);
        return base + " WHERE " + escapeString(whereClause);
    }
};

// Even deeper inheritance -- same rules apply at every level
template <typename Dialect>
class PaginatedSQLGenerator : public FilteredSQLGenerator<Dialect> {
public:
    std::string generatePaginatedSelect(
            const std::string& table,
            const std::vector<std::string>& cols,
            const std::string& whereClause,
            int limit, int offset) {
        // this-> needed because FilteredSQLGenerator<Dialect> is a dependent base
        std::string query = this->generateFilteredSelect(table, cols, whereClause);
        return query + " LIMIT " + std::to_string(limit)
                     + " OFFSET " + std::to_string(offset);
    }
};
```

### Accessing dependent base class types

The problem extends to types as well. Accessing a typedef or nested type from a dependent base class requires both `typename` (Item 42) and one of the three solutions above:

```cpp
template <typename T>
class Base {
public:
    using value_type = T;
    using container_type = std::vector<T>;
};

template <typename T>
class Derived : public Base<T> {
public:
    // WRONG: Base<T>::value_type is not found
    // value_type getData();

    // CORRECT: use typename + full qualification
    typename Base<T>::value_type getData() {
        typename Base<T>::container_type storage;
        storage.push_back(T());
        return storage.front();
    }

    // ALTERNATIVE: bring the type in with using
    using typename Base<T>::value_type;
    // Now value_type can be used unqualified in this class
};
```

### Multiple dependent base classes

When inheriting from multiple templatized bases, you need to resolve ambiguity for each:

```cpp
template <typename T>
class Serializable {
public:
    std::string serialize() const { /* ... */ return ""; }
};

template <typename T>
class Printable {
public:
    void print() const { /* ... */ }
};

template <typename T>
class Document : public Serializable<T>, public Printable<T> {
public:
    void save() {
        std::string data = this->serialize();  // From Serializable<T>
        this->print();                          // From Printable<T>
        // store data...
    }
};
```

### Things to Remember

- In derived class templates, refer to names in base class templates via a `this->` prefix, via `using` declarations, or via an explicit base class qualification.
- The compiler does not search dependent base classes during unqualified name lookup because a specialization of the base class template might not contain the name.
- Prefer `this->` or `using` declarations over explicit qualification, because explicit qualification inhibits virtual dispatch.

---

## Item 44: Factor parameter-independent code out of templates

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

## Item 45: Use member function templates to accept "all compatible types"

### The problem: implicit conversions don't work across template instantiations

In a class hierarchy, raw pointers support implicit conversions:

```cpp
class Base { };
class Derived : public Base { };
class AnotherDerived : public Base { };

Base* pb = new Derived;          // OK: implicit upcast
Base* pb2 = new AnotherDerived;  // OK
```

But smart pointer templates do not automatically support these conversions:

```cpp
template <typename T>
class SmartPtr {
public:
    explicit SmartPtr(T* rawPtr) : ptr_(rawPtr) {}
    T& operator*() const { return *ptr_; }
    T* operator->() const { return ptr_; }
private:
    T* ptr_;
};

SmartPtr<Base> pb = SmartPtr<Derived>(new Derived);  // ERROR!
// SmartPtr<Derived> and SmartPtr<Base> are completely unrelated types.
```

You cannot enumerate all possible conversions -- new derived classes can be added at any time. You need a **generalized** copy constructor and assignment operator.

### Solution: member function templates (generalized copy operations)

```cpp
template <typename T>
class SmartPtr {
public:
    explicit SmartPtr(T* rawPtr = nullptr) : ptr_(rawPtr) {}

    // Generalized copy constructor: accepts SmartPtr of any compatible type
    template <typename U>
    SmartPtr(const SmartPtr<U>& other)
        : ptr_(other.get()) {   // Compiles only if U* converts to T*
    }

    // Generalized assignment operator
    template <typename U>
    SmartPtr& operator=(const SmartPtr<U>& other) {
        ptr_ = other.get();     // Compiles only if U* converts to T*
        return *this;
    }

    T* get() const { return ptr_; }
    T& operator*() const { return *ptr_; }
    T* operator->() const { return ptr_; }

private:
    T* ptr_;
};
```

The key line is `ptr_(other.get())`. This initializes a `T*` from a `U*`. If `U*` is not implicitly convertible to `T*`, the code will not compile. This means:

```cpp
SmartPtr<Base> pb = SmartPtr<Derived>(new Derived);          // OK: Derived* -> Base*
SmartPtr<Derived> pd = SmartPtr<Base>(new Base);             // ERROR: Base* -/-> Derived*
SmartPtr<const Base> pcb = SmartPtr<Derived>(new Derived);   // OK: Derived* -> const Base*
```

The type system enforces the same conversion rules as raw pointers, but automatically.

### How std::shared_ptr does it

`std::shared_ptr` uses exactly this technique:

```cpp
// Simplified sketch of std::shared_ptr
template <typename T>
class shared_ptr {
public:
    // Normal constructor
    explicit shared_ptr(T* ptr = nullptr);

    // Generalized copy constructor
    template <typename Y>
    shared_ptr(const shared_ptr<Y>& r);

    // Generalized move constructor
    template <typename Y>
    shared_ptr(shared_ptr<Y>&& r) noexcept;

    // Generalized copy assignment
    template <typename Y>
    shared_ptr& operator=(const shared_ptr<Y>& r);

    // Generalized move assignment
    template <typename Y>
    shared_ptr& operator=(shared_ptr<Y>&& r) noexcept;

    // Construct from unique_ptr (taking ownership)
    template <typename Y, typename Deleter>
    shared_ptr(std::unique_ptr<Y, Deleter>&& r);

    // ...
};
```

This allows all of the following:

```cpp
class Base { public: virtual ~Base() = default; };
class Derived : public Base { };

std::shared_ptr<Derived> pd = std::make_shared<Derived>();
std::shared_ptr<Base> pb = pd;                    // Generalized copy ctor
std::shared_ptr<const Base> pcb = pd;             // Also works
std::shared_ptr<Base> pb2 = std::move(pd);        // Generalized move ctor

std::unique_ptr<Derived> ud = std::make_unique<Derived>();
std::shared_ptr<Base> pb3 = std::move(ud);        // From unique_ptr
```

### Critical: member templates do NOT suppress compiler-generated functions

A member template that looks like a copy constructor is NOT a copy constructor. The compiler will still generate the default copy constructor and copy assignment operator:

```cpp
template <typename T>
class SmartPtr {
public:
    // Generalized copy constructor (member template)
    template <typename U>
    SmartPtr(const SmartPtr<U>& other) : ptr_(other.get()) {
        std::cout << "generalized copy ctor\n";
    }

    // The compiler STILL generates:
    // SmartPtr(const SmartPtr<T>& other);  -- default copy ctor
    // SmartPtr& operator=(const SmartPtr<T>& other);  -- default copy assignment
};

SmartPtr<int> a(new int(42));
SmartPtr<int> b(a);  // Calls the COMPILER-GENERATED copy ctor, NOT the template!
```

If the compiler-generated versions do the wrong thing (and for resource-managing classes they usually do), you must declare them explicitly:

```cpp
template <typename T>
class SmartPtr {
public:
    // Normal copy constructor -- must be declared explicitly
    SmartPtr(const SmartPtr& other) : ptr_(other.ptr_) {
        // proper reference counting, deep copy, etc.
    }

    // Normal copy assignment -- must be declared explicitly
    SmartPtr& operator=(const SmartPtr& other) {
        if (this != &other) {
            // proper cleanup and copy
            ptr_ = other.ptr_;
        }
        return *this;
    }

    // Generalized copy constructor
    template <typename U>
    SmartPtr(const SmartPtr<U>& other) : ptr_(other.get()) {
        // proper reference counting, deep copy, etc.
    }

    // Generalized copy assignment
    template <typename U>
    SmartPtr& operator=(const SmartPtr<U>& other) {
        ptr_ = other.get();
        return *this;
    }

    T* get() const { return ptr_; }

private:
    T* ptr_;
};
```

### A complete real-world example: a reference-counted smart pointer

```cpp
#include <atomic>
#include <iostream>
#include <utility>

struct RefCount {
    std::atomic<int> count{1};
};

template <typename T>
class SharedPtr {
    template <typename U> friend class SharedPtr;  // All SharedPtr<U> are friends

public:
    explicit SharedPtr(T* p = nullptr)
        : ptr_(p), refCount_(p ? new RefCount : nullptr) {}

    // Copy constructor (same type)
    SharedPtr(const SharedPtr& other)
        : ptr_(other.ptr_), refCount_(other.refCount_) {
        incrementRef();
    }

    // Generalized copy constructor (different compatible type)
    template <typename U>
    SharedPtr(const SharedPtr<U>& other)
        : ptr_(other.ptr_),           // Compiles only if U* -> T*
          refCount_(other.refCount_) {
        incrementRef();
    }

    // Move constructor (same type)
    SharedPtr(SharedPtr&& other) noexcept
        : ptr_(other.ptr_), refCount_(other.refCount_) {
        other.ptr_ = nullptr;
        other.refCount_ = nullptr;
    }

    // Generalized move constructor
    template <typename U>
    SharedPtr(SharedPtr<U>&& other) noexcept
        : ptr_(other.ptr_), refCount_(other.refCount_) {
        other.ptr_ = nullptr;
        other.refCount_ = nullptr;
    }

    ~SharedPtr() { decrementRef(); }

    // Copy assignment (same type)
    SharedPtr& operator=(const SharedPtr& other) {
        SharedPtr tmp(other);
        swap(tmp);
        return *this;
    }

    // Generalized copy assignment
    template <typename U>
    SharedPtr& operator=(const SharedPtr<U>& other) {
        SharedPtr tmp(other);
        swap(tmp);
        return *this;
    }

    T* get() const { return ptr_; }
    T& operator*() const { return *ptr_; }
    T* operator->() const { return ptr_; }

    int useCount() const {
        return refCount_ ? refCount_->count.load() : 0;
    }

private:
    void incrementRef() {
        if (refCount_) refCount_->count.fetch_add(1);
    }

    void decrementRef() {
        if (refCount_ && refCount_->count.fetch_sub(1) == 1) {
            delete ptr_;
            delete refCount_;
        }
    }

    void swap(SharedPtr& other) noexcept {
        std::swap(ptr_, other.ptr_);
        std::swap(refCount_, other.refCount_);
    }

    T* ptr_;
    RefCount* refCount_;
};

// Usage:
struct Animal { virtual ~Animal() = default; virtual void speak() = 0; };
struct Dog : Animal { void speak() override { std::cout << "Woof!\n"; } };
struct Cat : Animal { void speak() override { std::cout << "Meow!\n"; } };

int main() {
    SharedPtr<Dog> dog(new Dog);
    SharedPtr<Animal> animal = dog;         // Generalized copy ctor
    animal->speak();                         // "Woof!"
    std::cout << "Use count: " << dog.useCount() << "\n";  // 2

    SharedPtr<Cat> cat(new Cat);
    animal = cat;                            // Generalized copy assignment
    animal->speak();                         // "Meow!"
    std::cout << "Use count: " << cat.useCount() << "\n";  // 2
}
```

### Things to Remember

- Use member function templates to generate functions that accept all compatible types.
- If you declare member templates for generalized copy construction or generalized assignment, you still need to declare the normal copy constructor and copy assignment operator. The compiler will generate them even when member templates exist.
- The conversion safety comes from the underlying pointer assignment -- if `U*` cannot convert to `T*`, the template instantiation will fail at compile time.

---

## Item 46: Define non-member functions inside templates when type conversions are desired

### The problem: templates and implicit type conversions don't mix

Recall from Item 24 that mixed-mode arithmetic (e.g., `Rational * int`) requires non-member functions so that implicit conversions can apply to all arguments. When you templatize `Rational`, this breaks:

```cpp
template <typename T>
class Rational {
public:
    Rational(const T& numerator = 0, const T& denominator = 1)
        : num_(numerator), den_(denominator) {}

    const T& numerator() const { return num_; }
    const T& denominator() const { return den_; }

private:
    T num_, den_;
};

// Non-member operator*
template <typename T>
const Rational<T> operator*(const Rational<T>& lhs, const Rational<T>& rhs) {
    return Rational<T>(lhs.numerator() * rhs.numerator(),
                       lhs.denominator() * rhs.denominator());
}

Rational<int> oneHalf(1, 2);
Rational<int> result = oneHalf * 2;  // ERROR!
```

Why does this fail? During template argument deduction, implicit conversions are **not** considered. The compiler sees `oneHalf * 2` and tries to deduce `T` for `operator*`:
- From `oneHalf` (type `Rational<int>`), it deduces `T = int`.
- From `2` (type `int`), it cannot deduce `T` because `int` is not `Rational<something>`.

Template argument deduction fails, and the compiler never even considers the implicit conversion from `int` to `Rational<int>`.

### Solution: declare the function as a friend inside the class template

When a class template is instantiated, the declarations of its friend functions become known. Since they are not themselves templates (they are specific functions associated with a specific instantiation), implicit conversions apply to their arguments:

```cpp
template <typename T>
class Rational {
public:
    Rational(const T& numerator = 0, const T& denominator = 1)
        : num_(numerator), den_(denominator) {}

    const T& numerator() const { return num_; }
    const T& denominator() const { return den_; }

    // Friend declaration AND definition inside the class
    friend const Rational operator*(const Rational& lhs, const Rational& rhs) {
        return Rational(lhs.numerator() * rhs.numerator(),
                        lhs.denominator() * rhs.denominator());
    }

private:
    T num_, den_;
};
```

Now:

```cpp
Rational<int> oneHalf(1, 2);
Rational<int> result = oneHalf * 2;  // OK!
// 1) oneHalf is Rational<int>, so the compiler instantiates Rational<int>
// 2) This makes the friend function operator*(const Rational<int>&, const Rational<int>&)
//    a known, non-template function
// 3) For non-template functions, implicit conversions ARE considered
// 4) 2 is converted to Rational<int>(2) via the converting constructor

Rational<int> result2 = 2 * oneHalf;  // Also OK -- conversion on first arg
```

### Why the friend must be defined inside the class

If you only declare the friend inside the class but define it outside, you get a linker error:

```cpp
template <typename T>
class Rational {
public:
    // ...
    friend const Rational operator*(const Rational& lhs, const Rational& rhs);
    // Just a declaration -- the linker won't find the definition
};

// This is a function TEMPLATE, not the friend function!
template <typename T>
const Rational<T> operator*(const Rational<T>& lhs, const Rational<T>& rhs) {
    return Rational<T>(lhs.numerator() * rhs.numerator(),
                       lhs.denominator() * rhs.denominator());
}
```

The friend declaration creates a non-template function `operator*(const Rational<int>&, const Rational<int>&)`. The definition outside the class is a function template. They are different entities. The linker finds the declaration but no matching definition.

Defining the friend inside the class body solves this because the definition is right there.

### Using a helper to keep the friend function short

If the implementation is long, you can delegate to a helper function template:

```cpp
// Helper: a function template (not subject to implicit conversion, but
// that's OK -- it's only called from the friend function)
template <typename T>
const Rational<T> doMultiply(const Rational<T>& lhs, const Rational<T>& rhs) {
    return Rational<T>(lhs.numerator() * rhs.numerator(),
                       lhs.denominator() * rhs.denominator());
}

template <typename T>
class Rational {
public:
    Rational(const T& numerator = 0, const T& denominator = 1)
        : num_(numerator), den_(denominator) {}

    const T& numerator() const { return num_; }
    const T& denominator() const { return den_; }

    // Short friend: just delegates
    friend const Rational operator*(const Rational& lhs, const Rational& rhs) {
        return doMultiply(lhs, rhs);
        // Here, lhs and rhs are already Rational<T>, so template argument
        // deduction for doMultiply succeeds.
    }

private:
    T num_, den_;
};
```

### A more complete example: arithmetic on a Vector class

```cpp
#include <iostream>
#include <cmath>

template <typename T>
class Vec3 {
public:
    Vec3(T x = T(), T y = T(), T z = T()) : x_(x), y_(y), z_(z) {}

    T x() const { return x_; }
    T y() const { return y_; }
    T z() const { return z_; }

    T length() const { return std::sqrt(x_*x_ + y_*y_ + z_*z_); }

    // All arithmetic operators need type conversions on both sides,
    // so they are friends defined inside the class.

    friend Vec3 operator+(const Vec3& a, const Vec3& b) {
        return Vec3(a.x_ + b.x_, a.y_ + b.y_, a.z_ + b.z_);
    }

    friend Vec3 operator-(const Vec3& a, const Vec3& b) {
        return Vec3(a.x_ - b.x_, a.y_ - b.y_, a.z_ - b.z_);
    }

    // Scalar multiplication: Vec3 * scalar and scalar * Vec3
    friend Vec3 operator*(const Vec3& v, const T& s) {
        return Vec3(v.x_ * s, v.y_ * s, v.z_ * s);
    }

    friend Vec3 operator*(const T& s, const Vec3& v) {
        return v * s;
    }

    // Dot product
    friend T dot(const Vec3& a, const Vec3& b) {
        return a.x_ * b.x_ + a.y_ * b.y_ + a.z_ * b.z_;
    }

    // Cross product
    friend Vec3 cross(const Vec3& a, const Vec3& b) {
        return Vec3(a.y_ * b.z_ - a.z_ * b.y_,
                    a.z_ * b.x_ - a.x_ * b.z_,
                    a.x_ * b.y_ - a.y_ * b.x_);
    }

    friend std::ostream& operator<<(std::ostream& os, const Vec3& v) {
        return os << "(" << v.x_ << ", " << v.y_ << ", " << v.z_ << ")";
    }

private:
    T x_, y_, z_;
};

int main() {
    Vec3<double> a(1.0, 2.0, 3.0);
    Vec3<double> b(4.0, 5.0, 6.0);

    std::cout << "a + b = " << (a + b) << "\n";           // (5, 7, 9)
    std::cout << "a * 2 = " << (a * 2) << "\n";           // (2, 4, 6) -- int 2 converts to double
    std::cout << "3 * b = " << (3 * b) << "\n";           // (12, 15, 18) -- int 3 converts
    std::cout << "dot(a,b) = " << dot(a, b) << "\n";      // 32
    std::cout << "cross(a,b) = " << cross(a, b) << "\n";  // (-3, 6, -3)
}
```

### Comparison operators with friend in templates

```cpp
template <typename T>
class Money {
public:
    explicit Money(T amount) : amount_(amount) {}

    T amount() const { return amount_; }

    friend bool operator==(const Money& a, const Money& b) {
        return a.amount_ == b.amount_;
    }

    friend bool operator<(const Money& a, const Money& b) {
        return a.amount_ < b.amount_;
    }

    friend bool operator!=(const Money& a, const Money& b) { return !(a == b); }
    friend bool operator>(const Money& a, const Money& b) { return b < a; }
    friend bool operator<=(const Money& a, const Money& b) { return !(b < a); }
    friend bool operator>=(const Money& a, const Money& b) { return !(a < b); }

private:
    T amount_;
};
```

### Things to Remember

- When writing a class template that offers functions related to the template that support implicit type conversions on all parameters, define those functions as friends inside the class template.
- Template argument deduction does not consider implicit conversions. A friend function declared inside a class template instantiation is a non-template function, and implicit conversions apply to its arguments normally.
- If the friend function body is long, have it call a helper function template defined outside the class.

---

## Item 47: Use traits classes for information about types

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

## Item 48: Be aware of template metaprogramming

### What is template metaprogramming?

Template metaprogramming (TMP) is the process of writing programs that execute during compilation. The C++ template system is Turing-complete -- it can compute anything that a general-purpose computer can compute (given enough resources). TMP programs are written in C++ template syntax but run at compile time, producing constants, types, or code as their output.

TMP has two great strengths:
1. It makes some things easy that would otherwise be hard or impossible.
2. It shifts work from runtime to compile time, leading to smaller executables, shorter runtimes, and earlier error detection.

The main downsides: longer compile times, difficult-to-read code, and notoriously inscrutable error messages.

### The classic example: compile-time factorial

```cpp
// TMP factorial: computes n! at compile time
template <unsigned N>
struct Factorial {
    static constexpr unsigned value = N * Factorial<N - 1>::value;
};

// Base case: 0! = 1
template <>
struct Factorial<0> {
    static constexpr unsigned value = 1;
};

// Usage:
static_assert(Factorial<5>::value == 120);
static_assert(Factorial<0>::value == 1);
static_assert(Factorial<10>::value == 3628800);

// The value 120 is computed at compile time -- no runtime computation.
int main() {
    // This array declaration proves the value is a compile-time constant:
    int arr[Factorial<5>::value];  // int arr[120]; -- legal only if value is constexpr
    std::cout << "5! = " << Factorial<5>::value << "\n";
}
```

The recursion unfolds at compile time:
- `Factorial<5>::value` = 5 * `Factorial<4>::value`
- `Factorial<4>::value` = 4 * `Factorial<3>::value`
- `Factorial<3>::value` = 3 * `Factorial<2>::value`
- `Factorial<2>::value` = 2 * `Factorial<1>::value`
- `Factorial<1>::value` = 1 * `Factorial<0>::value`
- `Factorial<0>::value` = 1 (base case)

### Compile-time Fibonacci

```cpp
template <unsigned N>
struct Fibonacci {
    static constexpr unsigned long long value =
        Fibonacci<N - 1>::value + Fibonacci<N - 2>::value;
};

template <>
struct Fibonacci<0> {
    static constexpr unsigned long long value = 0;
};

template <>
struct Fibonacci<1> {
    static constexpr unsigned long long value = 1;
};

static_assert(Fibonacci<0>::value == 0);
static_assert(Fibonacci<1>::value == 1);
static_assert(Fibonacci<10>::value == 55);
static_assert(Fibonacci<20>::value == 6765);
static_assert(Fibonacci<46>::value == 1836311903);
```

Note: this naive recursive approach has exponential compile-time complexity (each `Fibonacci<N>` instantiates `Fibonacci<N-1>` and `Fibonacci<N-2>`, and memoization depends on the compiler). A linear version:

```cpp
template <unsigned N, unsigned long long Prev = 0, unsigned long long Curr = 1>
struct FibLinear {
    static constexpr unsigned long long value =
        FibLinear<N - 1, Curr, Prev + Curr>::value;
};

template <unsigned long long Prev, unsigned long long Curr>
struct FibLinear<0, Prev, Curr> {
    static constexpr unsigned long long value = Prev;
};

static_assert(FibLinear<10>::value == 55);
static_assert(FibLinear<50>::value == 12586269025ULL);
```

### Compile-time greatest common divisor

```cpp
template <unsigned A, unsigned B>
struct GCD {
    static constexpr unsigned value = GCD<B, A % B>::value;
};

template <unsigned A>
struct GCD<A, 0> {
    static constexpr unsigned value = A;
};

static_assert(GCD<12, 8>::value == 4);
static_assert(GCD<100, 75>::value == 25);
static_assert(GCD<17, 13>::value == 1);  // Coprime
```

### Type-level computation: type lists

TMP can manipulate types themselves, not just values:

```cpp
#include <type_traits>
#include <iostream>
#include <string>

// A type list is a compile-time list of types
template <typename... Ts>
struct TypeList {};

// Length of a type list
template <typename List>
struct Length;

template <typename... Ts>
struct Length<TypeList<Ts...>> {
    static constexpr std::size_t value = sizeof...(Ts);
};

// Access the Nth type in a type list
template <typename List, std::size_t N>
struct TypeAt;

template <typename Head, typename... Tail>
struct TypeAt<TypeList<Head, Tail...>, 0> {
    using type = Head;
};

template <typename Head, typename... Tail, std::size_t N>
struct TypeAt<TypeList<Head, Tail...>, N> {
    using type = typename TypeAt<TypeList<Tail...>, N - 1>::type;
};

// Append a type to a type list
template <typename List, typename T>
struct Append;

template <typename... Ts, typename T>
struct Append<TypeList<Ts...>, T> {
    using type = TypeList<Ts..., T>;
};

// Prepend a type to a type list
template <typename List, typename T>
struct Prepend;

template <typename... Ts, typename T>
struct Prepend<TypeList<Ts...>, T> {
    using type = TypeList<T, Ts...>;
};

// Check if a type is in the list
template <typename List, typename T>
struct Contains;

template <typename T>
struct Contains<TypeList<>, T> {
    static constexpr bool value = false;
};

template <typename Head, typename... Tail, typename T>
struct Contains<TypeList<Head, Tail...>, T> {
    static constexpr bool value =
        std::is_same_v<Head, T> || Contains<TypeList<Tail...>, T>::value;
};

// Remove duplicates from a type list
template <typename List>
struct Unique;

template <>
struct Unique<TypeList<>> {
    using type = TypeList<>;
};

template <typename Head, typename... Tail>
struct Unique<TypeList<Head, Tail...>> {
private:
    using UniqueTail = typename Unique<TypeList<Tail...>>::type;
public:
    using type = std::conditional_t<
        Contains<UniqueTail, Head>::value,
        UniqueTail,
        typename Prepend<UniqueTail, Head>::type
    >;
};

// Usage:
using MyTypes = TypeList<int, double, std::string, float>;

static_assert(Length<MyTypes>::value == 4);
static_assert(std::is_same_v<typename TypeAt<MyTypes, 0>::type, int>);
static_assert(std::is_same_v<typename TypeAt<MyTypes, 2>::type, std::string>);
static_assert(Contains<MyTypes, double>::value);
static_assert(!Contains<MyTypes, char>::value);

using WithDups = TypeList<int, double, int, float, double>;
using NoDups = typename Unique<WithDups>::type;
static_assert(Length<NoDups>::value == 3);  // int, double, float
```

### TMP for compile-time dimensional analysis

A powerful real-world application of TMP is checking physical units at compile time:

```cpp
#include <iostream>
#include <ratio>

// Represent physical dimensions as compile-time integers
// (mass, length, time)
template <int Mass, int Length, int Time>
struct Dimension {
    static constexpr int mass = Mass;
    static constexpr int length = Length;
    static constexpr int time = Time;
};

// A quantity with a value and a dimension
template <typename Dim>
class Quantity {
public:
    explicit Quantity(double val) : value_(val) {}
    double value() const { return value_; }

    // Addition: only quantities of the same dimension can be added
    Quantity operator+(const Quantity& rhs) const {
        return Quantity(value_ + rhs.value_);
    }

    Quantity operator-(const Quantity& rhs) const {
        return Quantity(value_ - rhs.value_);
    }

    // Scalar multiplication
    Quantity operator*(double scalar) const {
        return Quantity(value_ * scalar);
    }

    // Multiplication of quantities: dimensions add
    template <typename OtherDim>
    auto operator*(const Quantity<OtherDim>& rhs) const {
        using ResultDim = Dimension<
            Dim::mass + OtherDim::mass,
            Dim::length + OtherDim::length,
            Dim::time + OtherDim::time
        >;
        return Quantity<ResultDim>(value_ * rhs.value());
    }

    // Division of quantities: dimensions subtract
    template <typename OtherDim>
    auto operator/(const Quantity<OtherDim>& rhs) const {
        using ResultDim = Dimension<
            Dim::mass - OtherDim::mass,
            Dim::length - OtherDim::length,
            Dim::time - OtherDim::time
        >;
        return Quantity<ResultDim>(value_ / rhs.value());
    }

private:
    double value_;
};

// Define common physical dimensions
using Scalar      = Dimension<0, 0, 0>;
using Mass        = Dimension<1, 0, 0>;     // kg
using Length      = Dimension<0, 1, 0>;     // m
using Time        = Dimension<0, 0, 1>;     // s
using Velocity    = Dimension<0, 1, -1>;    // m/s
using Accel       = Dimension<0, 1, -2>;    // m/s^2
using Force       = Dimension<1, 1, -2>;    // kg*m/s^2 = Newton
using Energy      = Dimension<1, 2, -2>;    // kg*m^2/s^2 = Joule

int main() {
    Quantity<Mass> m(10.0);        // 10 kg
    Quantity<Accel> a(9.8);        // 9.8 m/s^2
    auto force = m * a;            // Quantity<Force> -- 98 N (computed at compile time)

    Quantity<Length> d(100.0);      // 100 m
    auto energy = force * d;       // Quantity<Energy> -- 9800 J

    Quantity<Time> t(5.0);
    auto vel = d / t;              // Quantity<Velocity> -- 20 m/s

    std::cout << "Force: " << force.value() << " N\n";
    std::cout << "Energy: " << energy.value() << " J\n";
    std::cout << "Velocity: " << vel.value() << " m/s\n";

    // Compile-time error: cannot add mass and velocity!
    // auto bad = m + vel;  // ERROR: Quantity<Mass> + Quantity<Velocity> -- no match
}
```

The dimension checking happens entirely at compile time. The generated code is as efficient as raw `double` arithmetic -- zero runtime overhead.

### TMP for compile-time loop unrolling

```cpp
// Compile-time dot product with loop unrolling
template <int N>
struct DotProduct {
    template <typename T>
    static T compute(const T* a, const T* b) {
        return a[N-1] * b[N-1] + DotProduct<N-1>::compute(a, b);
    }
};

template <>
struct DotProduct<1> {
    template <typename T>
    static T compute(const T* a, const T* b) {
        return a[0] * b[0];
    }
};

// Usage:
double a[] = {1.0, 2.0, 3.0, 4.0};
double b[] = {5.0, 6.0, 7.0, 8.0};
double result = DotProduct<4>::compute(a, b);
// Compiler generates: a[3]*b[3] + a[2]*b[2] + a[1]*b[1] + a[0]*b[0]
// No loop overhead -- completely unrolled at compile time.
```

### Compile-time power function

```cpp
// Compute base^exp at compile time with fast exponentiation
template <unsigned Base, unsigned Exp>
struct Power {
    static constexpr unsigned long long value =
        (Exp % 2 == 0)
        ? Power<Base, Exp / 2>::value * Power<Base, Exp / 2>::value
        : Base * Power<Base, Exp - 1>::value;
};

template <unsigned Base>
struct Power<Base, 0> {
    static constexpr unsigned long long value = 1;
};

static_assert(Power<2, 10>::value == 1024);
static_assert(Power<3, 5>::value == 243);
static_assert(Power<10, 6>::value == 1000000);
```

### TMP for compile-time string processing (C++17)

```cpp
// Compile-time string hash (FNV-1a)
constexpr std::size_t fnv1a_hash(const char* str, std::size_t len) {
    std::size_t hash = 14695981039346656037ULL;
    for (std::size_t i = 0; i < len; ++i) {
        hash ^= static_cast<std::size_t>(str[i]);
        hash *= 1099511628211ULL;
    }
    return hash;
}

// A compile-time string wrapper
template <std::size_t N>
struct FixedString {
    char data[N];
    constexpr FixedString(const char (&str)[N]) {
        for (std::size_t i = 0; i < N; ++i) data[i] = str[i];
    }
    constexpr std::size_t hash() const { return fnv1a_hash(data, N - 1); }
};

// Usage in a compile-time switch-like construct:
constexpr auto h = FixedString("hello").hash();
static_assert(h != 0);  // Non-zero hash computed at compile time
```

### constexpr: the modern alternative to classic TMP

C++11 introduced `constexpr`, which provides a much more readable way to do compile-time computation. C++14 and C++17 further relaxed its restrictions:

```cpp
// constexpr factorial -- reads like normal code!
constexpr unsigned long long factorial(unsigned n) {
    unsigned long long result = 1;
    for (unsigned i = 2; i <= n; ++i)
        result *= i;
    return result;
}

static_assert(factorial(5) == 120);
static_assert(factorial(20) == 2432902008176640000ULL);

// constexpr Fibonacci
constexpr unsigned long long fibonacci(unsigned n) {
    if (n <= 1) return n;
    unsigned long long prev = 0, curr = 1;
    for (unsigned i = 2; i <= n; ++i) {
        unsigned long long next = prev + curr;
        prev = curr;
        curr = next;
    }
    return curr;
}

static_assert(fibonacci(10) == 55);
static_assert(fibonacci(50) == 12586269025ULL);

// constexpr GCD
constexpr unsigned gcd(unsigned a, unsigned b) {
    while (b != 0) {
        unsigned t = b;
        b = a % b;
        a = t;
    }
    return a;
}

static_assert(gcd(12, 8) == 4);
```

While `constexpr` replaces many uses of classic TMP for value computation, TMP remains essential for **type computation** -- selecting types, transforming type lists, and generating code based on type properties.

### Real-world uses of TMP

1. **Ensuring correctness at compile time** -- dimensional analysis (shown above), strong typedefs, and policy checking.

2. **Optimizing performance** -- expression templates in linear algebra libraries (Eigen, Blaze) eliminate temporary objects:

```cpp
// Without expression templates:
Matrix a, b, c, d;
Matrix result = a + b + c + d;
// Creates 3 temporaries: (a+b), ((a+b)+c), (((a+b)+c)+d)

// With expression templates (TMP):
// The expression a + b + c + d creates a lightweight expression object.
// Only when assigned to result does a single pass evaluate the sum.
// Zero temporaries, one loop -- as fast as hand-written code.
```

3. **Static interface checking** -- C++20 concepts are the modern way, but pre-C++20 code uses TMP:

```cpp
// Pre-C++20: SFINAE-based concept checking
template <typename T,
          typename = std::enable_if_t<
              std::is_default_constructible_v<T> &&
              std::is_copy_assignable_v<T>>>
class Container {
    // Only instantiates if T is default-constructible and copy-assignable
};

// C++20: concepts (built on top of TMP infrastructure)
template <typename T>
concept Storable = std::is_default_constructible_v<T> &&
                   std::is_copy_assignable_v<T>;

template <Storable T>
class Container {
    // Clean, readable constraint
};
```

4. **Compile-time state machines** -- verifying protocol compliance at compile time:

```cpp
// States
struct Disconnected {};
struct Connected {};
struct Authenticated {};

// Connection class with compile-time state tracking
template <typename State>
class Connection {
public:
    // Only callable in Disconnected state
    Connection<Connected> connect(const std::string& host)
        requires std::is_same_v<State, Disconnected>
    {
        // ... perform connection ...
        return Connection<Connected>{};
    }

    // Only callable in Connected state
    Connection<Authenticated> authenticate(const std::string& token)
        requires std::is_same_v<State, Connected>
    {
        // ... perform auth ...
        return Connection<Authenticated>{};
    }

    // Only callable in Authenticated state
    void sendData(const std::string& data)
        requires std::is_same_v<State, Authenticated>
    {
        // ... send data ...
    }
};

// Usage:
// Connection<Disconnected> conn;
// auto connected = conn.connect("example.com");
// auto authed = connected.authenticate("token123");
// authed.sendData("hello");
//
// conn.sendData("hello");  // COMPILE ERROR: wrong state!
// connected.sendData("x"); // COMPILE ERROR: not authenticated!
```

### Things to Remember

- Template metaprogramming can shift work from runtime to compile time, enabling earlier error detection and higher runtime performance.
- TMP can be used to generate custom code based on combinations of policy choices, and it can be used to avoid generating code inappropriate for particular types.
- Classic TMP uses recursive template instantiation for loops and template specialization for conditionals and base cases.
- `constexpr` functions (C++11/14/17/20) provide a more readable alternative to classic TMP for value computations, but TMP remains essential for type-level computation.
- Real-world applications of TMP include dimensional analysis, expression templates, compile-time interface checking, and static state machines.
- The trade-offs of TMP include longer compile times, harder-to-read code, and more difficult debugging -- use it when the benefits (correctness, performance) justify the costs.
