# Item 45: Use member function templates to accept "all compatible types"

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
