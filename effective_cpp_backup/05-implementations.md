# Chapter 5: Implementations

Most of the time, coming up with appropriate definitions for your classes and
declarations for your functions is the lion's share of the battle. Once you have
those right, the corresponding implementations are largely straightforward. Still,
there are things to watch out for. Defining variables too soon can cause a drag on
performance. Overuse of casts can lead to code that is slow, hard to maintain, and
infected with subtle bugs. Returning handles to an object's internals can defeat
encapsulation and leave clients with dangling handles. Failure to consider the
impact of exceptions can lead to leaked resources and corrupted data structures.
Overzealous inlining can cause code bloat. And excessive coupling can result in
unacceptably long build times.

Each of these problems is addressed in the Items that follow.

---

## Item 27: Minimize casting

The rules of C++ are designed to guarantee that type errors are impossible.
In theory, if your program compiles cleanly, it is not trying to perform any
unsafe or nonsensical operations on any objects. This guarantee is valuable, and
you should not lightly abandon it. Unfortunately, casts subvert the type system.
That can lead to trouble of all kinds, some easy to recognize, some insidiously
subtle.

### The Old C-Style Casts

C-style casts look like this:

```cpp
// C-style cast
(T) expression          // cast expression to be of type T

// Function-style cast (same semantics, different syntax)
T(expression)           // cast expression to be of type T
```

There is no difference in meaning between these forms. It is purely a matter of
where you put the parentheses. These are called old-style casts.

**Problem with old-style casts:** They are blunt instruments. You cannot tell at a
glance what kind of conversion is taking place --- whether the cast is removing
const, reinterpreting a pointer type, performing a safe numeric conversion, or
something else entirely. They are also essentially impossible to search for in
code, since the syntax `(int)x` or `int(x)` blends in with surrounding code.

### The Four C++ Casts

C++ offers four new cast forms, each with a specific, narrow purpose:

#### 1. `const_cast`: Casting Away Constness

`const_cast` is used to add or remove `const` (or `volatile`) from an object.
It is the only C++ cast that can do this.

```cpp
class TextBlock {
public:
    // Non-const operator[] wants to reuse the const version to avoid
    // code duplication (see Item 3).
    const char& operator[](std::size_t position) const {
        // ... bounds checking, logging, data integrity verification ...
        return text[position];
    }

    char& operator[](std::size_t position) {
        // Cast *this to const to call the const version, then cast
        // away const from the return value. This is safe because the
        // caller must have a non-const object (otherwise this non-const
        // overload would not have been called).
        return const_cast<char&>(
            static_cast<const TextBlock&>(*this)[position]
        );
    }

private:
    std::string text;
};
```

A real-world scenario where `const_cast` is necessary: interfacing with
legacy C APIs that do not use `const` correctly:

```cpp
// Legacy C library header
// void legacy_print(char* str);   // should be const char*, but isn't

void printMessage(const std::string& msg) {
    // We know legacy_print does not modify str, but the API is not
    // const-correct. const_cast is the appropriate escape hatch.
    legacy_print(const_cast<char*>(msg.c_str()));
}
```

**Warning:** Using `const_cast` to modify an object that was originally declared
`const` is undefined behavior:

```cpp
const int x = 42;
int* p = const_cast<int*>(&x);
*p = 99;   // UNDEFINED BEHAVIOR! x was declared const.
```

#### 2. `dynamic_cast`: Safe Downcasting in Inheritance Hierarchies

`dynamic_cast` is used to perform safe downcasts in polymorphic class
hierarchies (classes that have at least one virtual function). It checks at
runtime whether the cast is valid.

```cpp
class Shape {
public:
    virtual ~Shape() = default;
    virtual void draw() const = 0;
};

class Circle : public Shape {
public:
    void draw() const override { /* ... */ }
    double radius() const { return radius_; }
private:
    double radius_ = 1.0;
};

class Rectangle : public Shape {
public:
    void draw() const override { /* ... */ }
    double width() const { return width_; }
    double height() const { return height_; }
private:
    double width_ = 1.0;
    double height_ = 1.0;
};

// Pointer form: returns nullptr on failure
void processShape(Shape* shape) {
    if (Circle* circle = dynamic_cast<Circle*>(shape)) {
        // Safe: we verified that shape really is a Circle
        std::cout << "Circle with radius " << circle->radius() << "\n";
    }
    else if (Rectangle* rect = dynamic_cast<Rectangle*>(shape)) {
        std::cout << "Rectangle " << rect->width()
                  << " x " << rect->height() << "\n";
    }
}

// Reference form: throws std::bad_cast on failure
void mustBeCircle(Shape& shape) {
    try {
        Circle& circle = dynamic_cast<Circle&>(shape);
        std::cout << "Confirmed circle, radius = "
                  << circle.radius() << "\n";
    }
    catch (const std::bad_cast& e) {
        std::cerr << "Not a circle: " << e.what() << "\n";
    }
}
```

**Performance concern:** `dynamic_cast` can be slow. Many implementations use
string comparisons of class names (derived from `typeid`), and in deep
hierarchies this may require traversing the entire inheritance chain. In
performance-sensitive code, consider alternatives:

```cpp
// ALTERNATIVE 1: Use virtual functions instead of dynamic_cast.
// This is almost always the right answer.
class Shape {
public:
    virtual ~Shape() = default;
    virtual void draw() const = 0;
    virtual void processSpecifics() const {}  // default: do nothing
};

class Circle : public Shape {
public:
    void draw() const override { /* ... */ }
    void processSpecifics() const override {
        std::cout << "Circle with radius " << radius_ << "\n";
    }
private:
    double radius_ = 1.0;
};

// Now you can process shapes without any casting at all:
void processShape(Shape& shape) {
    shape.draw();
    shape.processSpecifics();  // polymorphism does the dispatching
}

// ALTERNATIVE 2: Store the derived pointer directly if you know the type.
// Use containers of typed pointers rather than casting from a base.
class Window {
    std::vector<std::unique_ptr<Circle>> circles_;
    std::vector<std::unique_ptr<Rectangle>> rectangles_;
    // No need for dynamic_cast; you already know the types.
};
```

**Cascading `dynamic_cast` is a code smell:**

```cpp
// BAD: This is brittle and violates the open/closed principle.
// Every time you add a new Shape subclass, you must update this function.
void handleShape(Shape* shape) {
    if (auto* c = dynamic_cast<Circle*>(shape)) {
        // handle circle
    } else if (auto* r = dynamic_cast<Rectangle*>(shape)) {
        // handle rectangle
    } else if (auto* t = dynamic_cast<Triangle*>(shape)) {
        // handle triangle
    }
    // ... and so on for every subclass
}

// GOOD: Use virtual functions. The Shape hierarchy handles itself.
void handleShape(Shape* shape) {
    shape->handle();   // Each subclass implements its own behavior.
}
```

#### 3. `static_cast`: Explicit Type Conversions

`static_cast` is the workhorse cast. It performs conversions that are
reasonable but not guaranteed safe at runtime. It can do implicit conversions
(int to double, pointer-to-derived to pointer-to-base), and it can do the
reverse of many implicit conversions (but not remove `const`).

```cpp
// Numeric conversions
int totalItems = 97;
int numberOfBuckets = 7;

// Without cast: integer division truncates to 13
double avgBad = totalItems / numberOfBuckets;

// With static_cast: floating-point division gives 13.857...
double avgGood = static_cast<double>(totalItems) / numberOfBuckets;

// Enum conversions
enum class Color { Red, Green, Blue };
int colorValue = static_cast<int>(Color::Green);   // 1

// Pointer conversions in a known hierarchy (no runtime check)
class Base { public: virtual ~Base() = default; };
class Derived : public Base { public: void specificMethod() {} };

Base* bp = new Derived;
// You (the programmer) assert that bp really points to a Derived.
// No runtime check is performed. If you are wrong, behavior is undefined.
Derived* dp = static_cast<Derived*>(bp);
dp->specificMethod();   // OK only if bp truly points to a Derived.
delete bp;

// void* conversions (common in C callback interfaces)
void timerCallback(void* userData) {
    auto* connection = static_cast<Connection*>(userData);
    connection->onTimeout();
}

// Calling an explicit constructor
class Widget {
public:
    explicit Widget(int size);
};

void doSomething(const Widget& w);

doSomething(static_cast<Widget>(15));   // Calls Widget(int) explicitly
```

**Beware: `static_cast` within an inheritance hierarchy can silently produce
the wrong pointer value.**

This is one of the most subtle and important points about casting. When you
have multiple inheritance or even single inheritance with virtual functions,
the base class subobject may be at a different offset within the derived
object. A cast actually adjusts the pointer value:

```cpp
class Window {
public:
    virtual ~Window() = default;
    int windowId = 1;
};

class ScrollBar {
public:
    virtual ~ScrollBar() = default;
    int scrollPos = 0;
};

class FancyWindow : public Window, public ScrollBar {
public:
    int fancyLevel = 5;
};

FancyWindow fw;

// These two pointers may have DIFFERENT numeric values!
Window*    wp = &fw;      // Points to the Window subobject
ScrollBar* sp = &fw;      // Points to the ScrollBar subobject

// The compiler knows the layout and adjusts the pointer correctly.
// But if you bypass the type system with reinterpret_cast, you get garbage.
```

**Another critical subtlety --- casting `*this` in a derived class:**

```cpp
class Window {
public:
    virtual void onResize() {
        // ... base class resize logic ...
        std::cout << "Window::onResize for " << this << "\n";
    }
};

class SpecialWindow : public Window {
public:
    virtual void onResize() override {
        // WRONG! This creates a TEMPORARY COPY of the Window part of *this,
        // then calls onResize on that temporary. The original object is
        // NOT affected by anything Window::onResize does to its members.
        static_cast<Window>(*this).onResize();   // BUG!

        // CORRECT: Call the base class version on *this.
        Window::onResize();

        // ... SpecialWindow-specific resize logic ...
    }
};
```

This is a real pitfall. The cast `static_cast<Window>(*this)` creates a
temporary copy. Any side effects of `Window::onResize()` (such as modifying
data members) happen on the temporary, not on the actual object. The fix is
simply to use the qualified call `Window::onResize()`.

#### 4. `reinterpret_cast`: Low-Level Bit Reinterpretation

`reinterpret_cast` performs low-level, implementation-dependent casts. The
result is almost always unportable. The most common legitimate use is casting
between pointer types and integer types, or between unrelated pointer types
when interfacing with hardware or very low-level system code.

```cpp
// Legitimate use 1: Interfacing with hardware memory-mapped registers
volatile uint32_t* timerRegister =
    reinterpret_cast<volatile uint32_t*>(0x40000C00);

// Legitimate use 2: Implementing type-punning for serialization
// (Note: in modern C++, std::bit_cast from <bit> is preferred for this.)
float f = 3.14f;
uint32_t bits = *reinterpret_cast<uint32_t*>(&f);
// bits now contains the IEEE 754 representation of 3.14f.
// WARNING: This technically violates strict aliasing. Use std::bit_cast
// in C++20 or memcpy in earlier standards for well-defined behavior.

// Legitimate use 3: Hash functions that need to examine pointer bits
struct Hasher {
    size_t operator()(const void* ptr) const {
        return reinterpret_cast<uintptr_t>(ptr) >> 4;
    }
};
```

**`reinterpret_cast` should almost never appear in application-level code.**
Its presence is a strong signal that something unusual and potentially
non-portable is happening.

### A Comprehensive Example: Why Casts Are Dangerous

```cpp
#include <iostream>
#include <vector>
#include <memory>

class Animal {
public:
    virtual ~Animal() = default;
    virtual std::string speak() const = 0;
    int age_ = 0;
};

class Dog : public Animal {
public:
    std::string speak() const override { return "Woof!"; }
    std::string favoriteToy_ = "ball";
};

class Cat : public Animal {
public:
    std::string speak() const override { return "Meow!"; }
    bool isIndoor_ = true;
};

void demonstrateCastingDangers() {
    std::vector<std::unique_ptr<Animal>> zoo;
    zoo.push_back(std::make_unique<Dog>());
    zoo.push_back(std::make_unique<Cat>());

    for (auto& animal : zoo) {
        // BAD: Casting every animal to Dog*. When animal is a Cat,
        // static_cast succeeds (no runtime check!) and you get UB.
        Dog* dog = static_cast<Dog*>(animal.get());
        std::cout << dog->favoriteToy_ << "\n";   // UB when animal is a Cat

        // GOOD: Use dynamic_cast which checks at runtime.
        if (Dog* dog2 = dynamic_cast<Dog*>(animal.get())) {
            std::cout << dog2->favoriteToy_ << "\n";   // Safe
        }

        // BEST: Use virtual functions --- no casting at all.
        std::cout << animal->speak() << "\n";
    }
}
```

### Summary of When Each Cast Is Appropriate

| Cast | Purpose | Runtime check? | Can remove const? |
|------|---------|---------------|-------------------|
| `const_cast` | Add/remove const or volatile | No | Yes (only cast that can) |
| `static_cast` | "Reasonable" conversions, force explicit conversions | No | No |
| `dynamic_cast` | Safe downcast in polymorphic hierarchies | Yes | No |
| `reinterpret_cast` | Low-level bit reinterpretation | No | No |

### Things to Remember

- **Avoid casts whenever practical.** Code that requires casts often indicates
  a design that could be improved. This is especially true for `dynamic_cast`
  in performance-sensitive code.

- **When casting is necessary, prefer C++-style casts** (`static_cast`,
  `const_cast`, `dynamic_cast`, `reinterpret_cast`) over old-style casts.
  They are easier to identify in code (both for humans and for tools like
  `grep`), and their more narrowly specified purpose makes it possible for
  compilers to diagnose usage errors.

- **Beware the hidden copy when casting `*this`.** Casting `*this` to a base
  class value type creates a temporary copy; side effects on that copy do not
  affect the real object.

- **Consider alternatives to `dynamic_cast`**, especially cascading
  `dynamic_cast`s. Virtual function calls and container-of-typed-pointer
  designs are almost always better.

---

## Item 28: Avoid returning "handles" to object internals

A handle is anything that provides access to an object's internals: a
reference, a pointer, or an iterator. Returning handles to object internals
undermines encapsulation, can allow const member functions to enable
modification of object state, and creates the risk of dangling handles.

### Problem 1: Encapsulation Violation

```cpp
struct Point {
    int x, y;
};

class Rectangle {
public:
    Rectangle(const Point& topLeft, const Point& bottomRight)
        : topLeft_(topLeft), bottomRight_(bottomRight) {}

    // DANGEROUS: Returns a non-const reference to internal data.
    // Client code can modify the internals directly, bypassing any
    // invariant-checking logic that Rectangle might want to enforce.
    Point& upperLeft() const { return topLeft_; }
    Point& lowerRight() const { return bottomRight_; }

private:
    Point topLeft_;
    Point bottomRight_;
};

// Client code:
Rectangle rect(Point{0, 0}, Point{100, 50});

// This compiles and runs! A const-qualified member function is allowing
// modification of the object's internal state through the returned reference.
rect.upperLeft().x = 999;   // Modifies the "private" data!
```

The member functions `upperLeft()` and `lowerRight()` are declared `const`,
promising not to modify the Rectangle. But they return non-const references
to private data members, allowing clients to modify the data anyway.

The core issue: **a data member is only as encapsulated as the most accessible
function returning a reference to it.** Here, `topLeft_` and `bottomRight_` are
declared private but are effectively public because of the returned references.

### Problem 2: Const Member Functions Enabling Mutation

Even if you meant for the class to be fully const-correct:

```cpp
class StringWrapper {
public:
    explicit StringWrapper(const std::string& s) : data_(s) {}

    // The const on the member function only protects the pointer/reference
    // itself (i.e., which object data_ refers to), not the object it
    // points to. Returning a non-const reference to the internal string
    // allows callers to modify the string through a const StringWrapper.
    std::string& get() const { return data_; }

private:
    std::string data_;
};

const StringWrapper sw("hello");
sw.get() = "hacked";   // Compiles! Const-correctness is defeated.
```

### Solution: Return const References (But Beware Dangling)

```cpp
class Rectangle {
public:
    Rectangle(const Point& topLeft, const Point& bottomRight)
        : topLeft_(topLeft), bottomRight_(bottomRight) {}

    // BETTER: Return const references. Callers can read but not modify.
    const Point& upperLeft() const { return topLeft_; }
    const Point& lowerRight() const { return bottomRight_; }

private:
    Point topLeft_;
    Point bottomRight_;
};

// Now this will not compile:
// rect.upperLeft().x = 999;   // Error: assignment to member of const reference
```

This addresses the mutation problem but introduces a new one: **dangling handles**.

### Problem 3: Dangling Handles

A dangling handle is a reference (or pointer or iterator) that refers to an
object that no longer exists. This is one of the most pernicious bugs in C++.

```cpp
class GUIObject { /* ... */ };

// Suppose this function returns a Rectangle by value (a temporary):
const Rectangle boundingBox(const GUIObject& obj);

// Client code:
GUIObject button;

// pUpperLeft points into the temporary Rectangle returned by boundingBox().
// At the semicolon, the temporary is destroyed, and pUpperLeft dangles.
const Point* pUpperLeft = &(boundingBox(button).upperLeft());

// UNDEFINED BEHAVIOR: dereferencing a dangling pointer.
std::cout << pUpperLeft->x << "\n";
```

The temporary `Rectangle` returned by `boundingBox()` is destroyed at the end
of the full expression (the semicolon). The pointer `pUpperLeft` now points
to memory that has been reclaimed. Any use of it is undefined behavior.

### Real-World Dangling Handle Scenarios

**Scenario 1: Returning references from containers of smart pointers**

```cpp
class WidgetCache {
public:
    // DANGEROUS: If the shared_ptr is reset or the Widget is removed from
    // the cache, the reference dangles.
    const Widget& getWidget(int id) const {
        auto it = cache_.find(id);
        if (it == cache_.end()) throw std::runtime_error("not found");
        return *(it->second);   // Reference into the object owned by shared_ptr
    }

    void removeWidget(int id) {
        cache_.erase(id);   // The Widget is destroyed here...
    }

private:
    std::map<int, std::shared_ptr<Widget>> cache_;
};

// Usage:
WidgetCache cache;
// cache.addWidget(1, std::make_shared<Widget>(/* ... */));

const Widget& w = cache.getWidget(1);  // Reference is valid here.
cache.removeWidget(1);                  // Widget is destroyed!
w.doSomething();                        // UNDEFINED BEHAVIOR: dangling reference.

// SAFER ALTERNATIVE: Return a shared_ptr so the caller shares ownership.
// std::shared_ptr<Widget> getWidget(int id) const {
//     auto it = cache_.find(id);
//     if (it == cache_.end()) return nullptr;
//     return it->second;   // Caller holds a shared_ptr; Widget stays alive.
// }
```

**Scenario 2: Returning iterators or pointers to internal containers**

```cpp
class MessageQueue {
public:
    // DANGEROUS: The returned pointer is invalidated if the internal
    // vector reallocates (e.g., on the next push).
    const std::string* front() const {
        if (messages_.empty()) return nullptr;
        return &messages_.front();
    }

    void push(const std::string& msg) {
        messages_.push_back(msg);   // May reallocate, invalidating pointers!
    }

private:
    std::vector<std::string> messages_;
};

// Usage:
MessageQueue q;
q.push("hello");
const std::string* msg = q.front();   // Valid pointer.
q.push("world");                       // Vector may reallocate!
std::cout << *msg << "\n";             // POTENTIALLY UNDEFINED BEHAVIOR.

// SAFER ALTERNATIVE: Return by value.
// std::string front() const {
//     if (messages_.empty()) throw std::runtime_error("empty");
//     return messages_.front();   // Returns a copy; no dangling possible.
// }
```

**Scenario 3: Storing references returned from temporary expressions**

```cpp
class Config {
public:
    const std::string& getHostname() const { return hostname_; }
private:
    std::string hostname_ = "localhost";
};

// A factory function that returns a Config by value:
Config loadConfig();

// DANGEROUS:
const std::string& host = loadConfig().getHostname();
// The temporary Config is destroyed at the semicolon.
// 'host' is now a dangling reference.

// SAFE:
Config config = loadConfig();              // Keep the Config alive.
const std::string& host2 = config.getHostname();  // Now it is fine.

// ALSO SAFE:
std::string host3 = loadConfig().getHostname();   // Copy the string.
```

### When Returning Handles Is Acceptable

There are cases where returning handles is appropriate:

```cpp
// operator[] for containers MUST return a reference to be useful.
// This is an accepted, well-understood convention.
template <typename T>
class MyVector {
public:
    T& operator[](size_t index) { return data_[index]; }
    const T& operator[](size_t index) const { return data_[index]; }
private:
    T* data_;
    size_t size_;
};

// std::string::c_str() returns a pointer to internal data. This is
// acceptable because the documentation clearly states the pointer is
// invalidated by any non-const operation on the string, and the
// convention is universally understood.
```

Even `operator[]` and similar functions constitute exceptions to the rule, not
refutations of it. The general guideline stands: avoid returning handles to
internals whenever you can.

### Things to Remember

- **Avoid returning handles** (references, pointers, iterators) **to object
  internals.** Not returning handles increases encapsulation, helps `const`
  member functions act `const`, and minimizes the creation of dangling handles.

- **If you must return a handle, return a `const` handle** to prevent callers
  from modifying the object's internals through the handle.

- **Even `const` handles can dangle.** A handle to data inside a temporary
  object becomes invalid when the temporary is destroyed. Be especially careful
  with function return values.

- **When handles are part of the interface contract** (like `operator[]`),
  document the lifetime guarantees clearly.

---

## Item 29: Strive for exception-safe code

Exception safety is not about whether your code throws exceptions. It is about
how your code behaves when exceptions are thrown --- possibly by code you call.
Exception-safe functions offer one of three guarantees, and functions that offer
no guarantee at all are not acceptable in well-written C++.

### The Three Exception Safety Guarantees

**1. The Basic Guarantee:** If an exception is thrown, the program remains in a
valid state. No resources are leaked, and all objects remain in a self-consistent
state (i.e., all class invariants are satisfied). However, the exact state of
the program may not be predictable. For example, after an exception in a
"change the background image" function, the old image might be displayed, or
some default image, or something else --- but the object is not corrupt.

**2. The Strong Guarantee:** If an exception is thrown, the state of the program
is unchanged. Calls to functions offering the strong guarantee are atomic: they
either succeed completely or have no effect at all. This is a "commit or
rollback" model.

**3. The Nothrow Guarantee:** The function never throws exceptions. All
operations on built-in types (ints, pointers, etc.) are nothrow. This is the
strongest guarantee. Functions marked `noexcept` promise this guarantee.

### A Motivating Example

```cpp
// A class for GUI menus with a changeable background image.
class PrettyMenu {
public:
    void changeBackground(std::istream& imgSrc);

private:
    std::mutex mutex_;
    Image* bgImage_;        // Raw pointer: current background image
    int imageChanges_;      // Number of times image has been changed
};

// VERSION 1: Not exception-safe at all.
void PrettyMenu::changeBackground(std::istream& imgSrc) {
    mutex_.lock();                       // Acquire mutex

    delete bgImage_;                     // Destroy old image
    ++imageChanges_;                     // Increment change counter
    bgImage_ = new Image(imgSrc);       // Install new image

    mutex_.unlock();                     // Release mutex
}
```

**What goes wrong with Version 1:**

1. **Resource leak:** If `new Image(imgSrc)` throws, `mutex_` is never
   unlocked. The mutex is leaked (permanently locked).

2. **Corrupted state:** If `new Image(imgSrc)` throws, `bgImage_` points to
   a deleted object (dangling pointer), and `imageChanges_` has already been
   incremented even though the image was never actually changed.

### Fixing for the Basic Guarantee

```cpp
// VERSION 2: Offers the basic guarantee using RAII and careful ordering.
void PrettyMenu::changeBackground(std::istream& imgSrc) {
    // Use lock_guard for RAII-based mutex management.
    // The mutex will be released when the function exits, whether
    // normally or via an exception.
    std::lock_guard<std::mutex> lock(mutex_);

    // Allocate the new image BEFORE deleting the old one.
    // If new throws, the old image is still intact.
    Image* newImage = new Image(imgSrc);

    delete bgImage_;          // Delete old image (only after new one succeeded)
    bgImage_ = newImage;      // Install new image (no-throw: pointer assignment)
    ++imageChanges_;          // Increment counter (no-throw: integer increment)
}
```

This is better: the mutex cannot leak, and `bgImage_` always points to a
valid image. But it only offers the basic guarantee, not the strong guarantee.
If `new Image` throws, the state is valid but the caller cannot know whether
the image has changed or not.

### Achieving the Strong Guarantee with Copy-and-Swap

The copy-and-swap idiom is the classic technique for achieving the strong
guarantee:

```cpp
// VERSION 3: Offers the strong guarantee using copy-and-swap.

// Step 1: Move the data that might change into a separate implementation struct.
struct PMImpl {
    std::shared_ptr<Image> bgImage;
    int imageChanges = 0;
};

class PrettyMenu {
public:
    void changeBackground(std::istream& imgSrc);

private:
    std::mutex mutex_;
    std::shared_ptr<PMImpl> pImpl_;   // pImpl idiom (see Item 31)
};

void PrettyMenu::changeBackground(std::istream& imgSrc) {
    std::lock_guard<std::mutex> lock(mutex_);

    // STEP 1: Make a copy of the current state.
    auto pNew = std::make_shared<PMImpl>(*pImpl_);

    // STEP 2: Modify the copy. If this throws, the original is untouched.
    pNew->bgImage.reset(new Image(imgSrc));    // May throw
    ++pNew->imageChanges;                       // Won't throw

    // STEP 3: Swap the copy into place. swap for shared_ptr is noexcept.
    std::swap(pImpl_, pNew);

    // If we reach here, the change succeeded atomically.
    // If step 2 threw, we never reached step 3, so the original state
    // is completely unchanged --- the strong guarantee.
}
```

### Copy-and-Swap as a General Pattern

```cpp
// A strongly exception-safe assignment operator using copy-and-swap.
class String {
public:
    String(const char* s = "") : data_(new char[strlen(s) + 1]) {
        strcpy(data_, s);
    }

    ~String() { delete[] data_; }

    // Copy constructor: makes an independent copy.
    String(const String& rhs) : data_(new char[strlen(rhs.data_) + 1]) {
        strcpy(data_, rhs.data_);
    }

    // Copy-and-swap assignment operator.
    // Takes the parameter BY VALUE, which invokes the copy constructor.
    // Then we swap the copy's internals with ours.
    // This is exception-safe because:
    //   - The copy is made before any state is modified.
    //   - swap is noexcept (just swaps two pointers).
    //   - If the copy constructor throws, *this is unchanged.
    String& operator=(String rhs) {   // Note: pass by value!
        swap(rhs);
        return *this;
    }

    void swap(String& rhs) noexcept {
        std::swap(data_, rhs.data_);
    }

private:
    char* data_;
};
```

### The Nothrow Guarantee and `noexcept`

```cpp
// Functions that should be noexcept:

// 1. Move constructors and move assignment operators
class Buffer {
public:
    Buffer(Buffer&& other) noexcept
        : data_(other.data_), size_(other.size_) {
        other.data_ = nullptr;
        other.size_ = 0;
    }

    Buffer& operator=(Buffer&& other) noexcept {
        if (this != &other) {
            delete[] data_;
            data_ = other.data_;
            size_ = other.size_;
            other.data_ = nullptr;
            other.size_ = 0;
        }
        return *this;
    }

    // 2. Destructors (implicitly noexcept in C++11 and later)
    ~Buffer() noexcept {
        delete[] data_;
    }

    // 3. Swap functions
    void swap(Buffer& other) noexcept {
        std::swap(data_, other.data_);
        std::swap(size_, other.size_);
    }

private:
    char* data_ = nullptr;
    size_t size_ = 0;
};

// Why noexcept matters for performance:
// std::vector::push_back will use move semantics only if the move
// constructor is noexcept. Otherwise it falls back to copying, because
// a throwing move would leave the vector in an inconsistent state.
```

### A Complex Real-World Example: Transaction Processing

```cpp
class Database {
public:
    // Strong guarantee: either the entire transaction succeeds,
    // or the database is unchanged.
    void executeTransaction(const std::vector<Operation>& ops) {
        // Step 1: Create a snapshot (copy) of affected data.
        Snapshot snapshot = createSnapshot(ops);

        // Step 2: Apply operations to the snapshot.
        // If any operation throws, the real data is untouched.
        for (const auto& op : ops) {
            applyToSnapshot(snapshot, op);   // May throw
        }

        // Step 3: Commit the snapshot (swap into place).
        // This step must be noexcept.
        commitSnapshot(std::move(snapshot));  // noexcept
    }

private:
    Snapshot createSnapshot(const std::vector<Operation>& ops);
    void applyToSnapshot(Snapshot& snap, const Operation& op);
    void commitSnapshot(Snapshot&& snap) noexcept;
};
```

### RAII: The Foundation of Exception Safety

RAII (Resource Acquisition Is Initialization) is the single most important
technique for writing exception-safe code. Every resource should be managed
by an object whose destructor releases it.

```cpp
// BAD: Manual resource management is not exception-safe.
void processFile(const std::string& filename) {
    FILE* fp = fopen(filename.c_str(), "r");
    if (!fp) throw std::runtime_error("Cannot open file");

    char* buffer = new char[4096];

    // If readData throws, both fp and buffer are leaked.
    readData(fp, buffer);

    delete[] buffer;
    fclose(fp);
}

// GOOD: RAII manages all resources.
void processFile(const std::string& filename) {
    // ifstream closes itself on destruction (RAII).
    std::ifstream file(filename);
    if (!file) throw std::runtime_error("Cannot open file");

    // vector manages its own memory (RAII).
    std::vector<char> buffer(4096);

    // If readData throws, both file and buffer are cleaned up
    // automatically by their destructors.
    readData(file, buffer);
}
```

### When the Strong Guarantee Is Not Practical

The strong guarantee cannot always be achieved efficiently. Consider a
function that operates on two objects:

```cpp
void transferFunds(Account& from, Account& to, double amount) {
    from.withdraw(amount);    // Strong guarantee on 'from'
    to.deposit(amount);       // Strong guarantee on 'to'
}
```

Even though both `withdraw` and `deposit` individually offer the strong
guarantee, `transferFunds` as a whole does not. If `deposit` throws after
`withdraw` has succeeded, rolling back the withdrawal requires calling
`from.deposit(amount)`, which itself could throw.

In such cases, the basic guarantee is often the practical choice. The strong
guarantee would require either:
- A copy-and-swap of both Account objects (possibly expensive), or
- A transactional log with undo/redo capability (complex).

### Things to Remember

- **Exception-safe functions leak no resources and allow no data structures to
  become corrupted when exceptions are thrown**, even when those functions
  call other functions that might throw.

- **The strong guarantee can often be implemented via copy-and-swap**, but the
  strong guarantee is not practical for all functions (especially those that
  modify multiple independent objects).

- **A function can usually offer a guarantee no stronger than the weakest
  guarantee of the functions it calls.** If your function calls a function
  offering only the basic guarantee, the best your function can generally
  offer is the basic guarantee.

- **Use RAII to manage resources.** `lock_guard`, `unique_ptr`, `shared_ptr`,
  `fstream`, and similar types ensure cleanup happens automatically.

- **Mark functions `noexcept` when they truly cannot throw**, especially
  move operations, swap functions, and destructors.

---

## Item 30: Understand the ins and outs of inlining

Inline functions --- what a wonderful idea! They look like functions, they act
like functions, they are vastly better than macros (see Item 2), and you can
call them without incurring the overhead of a function call. What is not to love?

Actually, quite a lot. The basic idea behind inlining is to replace each call
of a function with its code body, and this has implications you need to
understand before you wield this tool.

### What Inlining Actually Does

When a function is inlined, the compiler replaces every call site with a copy
of the function body. This eliminates:
- The function call overhead (pushing arguments, jumping, returning)
- The opportunity for instruction cache misses at the call target

But it also means:
- The generated code is larger (one copy per call site)
- Larger code means more instruction cache pressure
- More instruction cache misses can slow down the program

**The net effect of inlining can be positive or negative.** For small functions,
inlining almost always wins. For large functions, inlining almost always loses.

### Implicit Inlining: Functions Defined Inside a Class

Functions defined inside a class definition are implicitly declared `inline`:

```cpp
class Person {
public:
    // Implicitly inline: defined inside the class body.
    int age() const { return age_; }

    // Implicitly inline.
    const std::string& name() const { return name_; }

    // This is also implicitly inline, but it is too complex to be
    // a good candidate for inlining. The compiler may choose NOT
    // to inline it despite the implicit request.
    std::string toString() const {
        std::ostringstream oss;
        oss << name_ << " (age " << age_ << ")";
        return oss.str();
    }

private:
    std::string name_;
    int age_;
};
```

**Friend functions defined inside a class are also implicitly inline:**

```cpp
class Widget {
public:
    // This friend function is defined inside the class, so it is
    // implicitly inline.
    friend bool operator==(const Widget& lhs, const Widget& rhs) {
        return lhs.id_ == rhs.id_;
    }

private:
    int id_;
};
```

### Explicit Inlining: The `inline` Keyword

```cpp
// Explicit inline function.
inline int square(int x) { return x * x; }

// Explicit inline template function.
// (Note: templates are often defined in headers anyway, but they
// are NOT automatically inline just because they are templates.)
template <typename T>
inline T clamp(T value, T lo, T hi) {
    return (value < lo) ? lo : (value > hi) ? hi : value;
}
```

**Important:** The `inline` keyword is a request, not a command. The compiler
is free to ignore it. Most modern compilers make their own inlining decisions
based on heuristics (function size, call frequency, optimization level) and
largely ignore the `inline` keyword for optimization purposes. The `inline`
keyword's primary practical effect in modern C++ is to relax the
one-definition rule (ODR), allowing the function to be defined in a header
included by multiple translation units.

### What the Compiler Cannot Inline

**1. Virtual function calls (through a base pointer/reference):**

```cpp
class Shape {
public:
    virtual double area() const = 0;
};

class Circle : public Shape {
public:
    // Even though this is defined in the class (implicitly inline),
    // calls through a Shape pointer/reference cannot be inlined because
    // the compiler does not know (at compile time) which function to call.
    double area() const override { return 3.14159 * r_ * r_; }
private:
    double r_ = 1.0;
};

void printArea(const Shape& s) {
    // Virtual call --- cannot be inlined (in general).
    std::cout << s.area() << "\n";
}

void printCircleArea(const Circle& c) {
    // Non-virtual call --- CAN be inlined because the compiler knows
    // the exact type is Circle.
    std::cout << c.area() << "\n";
}
```

**2. Calls through function pointers:**

```cpp
inline int add(int a, int b) { return a + b; }

int (*funcPtr)(int, int) = add;

int result1 = add(3, 4);       // Likely inlined
int result2 = funcPtr(3, 4);   // Likely NOT inlined: called via pointer
```

**3. Recursive functions (cannot be fully inlined):**

```cpp
// The compiler may inline one or two levels of recursion, but it
// cannot inline all of them (there are infinitely many).
inline unsigned factorial(unsigned n) {
    return (n <= 1) ? 1 : n * factorial(n - 1);
}
```

### Constructors and Destructors: Deceptively Complex

Constructors and destructors are often poor candidates for inlining, even if
they appear short, because the compiler inserts substantial hidden code:

```cpp
class Base {
public:
    Base() { std::cout << "Base constructed\n"; }
    ~Base() { std::cout << "Base destroyed\n"; }
private:
    std::string name_;
    std::vector<int> data_;
};

class Derived : public Base {
public:
    // This constructor LOOKS empty, but the compiler generates code to:
    //   1. Call Base::Base()
    //   2. Construct value1_ (call std::string constructor)
    //   3. Construct value2_ (call std::string constructor)
    //   4. If step 2 or 3 throws, destroy already-constructed members
    //      and call Base::~Base()
    Derived() {}   // Implicitly inline, but the generated code is large!

    ~Derived() {}  // Similarly, the destructor must destroy value2_,
                    // then value1_, then call Base::~Base().

private:
    std::string value1_;
    std::string value2_;
};
```

The compiler-generated code for `Derived::Derived()` might look something like:

```cpp
// Pseudocode: what the compiler actually generates for Derived::Derived()
Derived::Derived() {
    Base::Base();                     // Construct base class

    try {
        value1_.std::string::string(); // Construct first member
    } catch (...) {
        Base::~Base();                // Destroy base if member construction fails
        throw;
    }

    try {
        value2_.std::string::string(); // Construct second member
    } catch (...) {
        value1_.std::string::~string(); // Destroy first member
        Base::~Base();                  // Destroy base
        throw;
    }
}
```

Inlining this at every call site would generate a lot of code.

### Inlining and Libraries: Binary Compatibility

**Inlined functions are baked into the caller's object code.** If you change
the body of an inline function in a library, every client that uses the
function must recompile. With a non-inline function, clients need only
relink.

```cpp
// header: mathlib.h (version 1)
inline double computeTax(double income) {
    return income * 0.25;   // 25% flat tax
}

// If you change this to:
inline double computeTax(double income) {
    return income * 0.30;   // 30% flat tax
}
// Every source file that #includes mathlib.h must be RECOMPILED.
// With a non-inline function, you would only need to recompile
// mathlib.cpp and relink.
```

This is a serious concern for library authors. Inline functions in public
headers become part of your binary interface.

### Inlining and Debugging

Most debuggers cannot set breakpoints inside inlined functions. The inlined
code exists at the call site, not as a separate function, so stepping "into"
an inlined function does not work the way you expect. During development and
debugging, it can be helpful to minimize inlining (compile with `-O0` or
equivalent).

### Guidelines for When to Inline

```cpp
// GOOD candidates for inlining:
// Small, frequently called functions with simple bodies.
class Point {
public:
    double x() const { return x_; }    // Trivial accessor
    double y() const { return y_; }    // Trivial accessor

    void setX(double x) { x_ = x; }   // Trivial mutator
    void setY(double y) { y_ = y; }   // Trivial mutator

    // Small computation
    double distanceTo(const Point& other) const {
        double dx = x_ - other.x_;
        double dy = y_ - other.y_;
        return std::sqrt(dx * dx + dy * dy);
    }

private:
    double x_ = 0.0;
    double y_ = 0.0;
};

// BAD candidates for inlining:
// Large functions, functions that are rarely called, virtual functions
// called through base pointers, constructors/destructors of complex classes.

class DatabaseConnection {
public:
    // Do NOT inline: complex function with error handling, logging,
    // resource management, etc.
    void executeQuery(const std::string& sql) {
        validateConnection();
        logQuery(sql);
        auto result = sendToServer(sql);
        parseResponse(result);
        updateStatistics();
    }
};
```

### `constexpr` and Inlining (C++11 and later)

`constexpr` functions are implicitly inline (in the ODR sense), and when
evaluated at compile time, they are "inlined" in the most extreme way
possible: the function call is replaced with a constant:

```cpp
constexpr int fibonacci(int n) {
    if (n <= 1) return n;
    return fibonacci(n - 1) + fibonacci(n - 2);
}

// At compile time, this is evaluated to 55. No function call at runtime.
constexpr int fib10 = fibonacci(10);

// At runtime, this may or may not be inlined, just like any other function.
int n;
std::cin >> n;
int result = fibonacci(n);   // Runtime call
```

### Things to Remember

- **Limit most inlining to small, frequently called functions.** This
  facilitates debugging and binary upgradability, minimizes potential code
  bloat, and maximizes the chances of greater program speed.

- **Do not declare function templates `inline` just because they appear in
  header files.** Templates in headers are there because the compiler needs
  to see the definition to instantiate them, not because they should be
  inlined. Only add `inline` if the function is genuinely a good inlining
  candidate.

- **The `inline` keyword is a request, not a command.** The compiler decides
  whether to actually inline a function based on its own heuristics. Many
  compilers issue warnings (at the right warning level) when they fail to
  inline a function you asked to be inlined.

- **Constructors and destructors are often poor inlining candidates**, because
  the compiler-generated code for them is often much longer than it appears
  in source.

---

## Item 31: Minimize compilation dependencies between files

C++ does not do a great job of separating interfaces from implementations.
A class definition includes not just the interface (public member functions)
but also a substantial amount of implementation detail (private members,
private functions). This means that if you change a private member of a class,
every file that `#include`s that class's header must be recompiled --- even if
no client code uses the private member.

In a large project, this can lead to devastating build times. A single change
to a private data member in a core header can trigger recompilation of
hundreds of source files.

### The Problem

```cpp
// person.h
#include <string>         // Needed for std::string data member
#include <memory>         // Needed for std::shared_ptr
#include "date.h"         // Needed for Date data member
#include "address.h"      // Needed for Address data member

class Person {
public:
    Person(const std::string& name, const Date& birthday,
           const Address& addr);

    std::string name() const;
    std::string birthDate() const;
    std::string address() const;

private:
    std::string name_;     // Implementation detail!
    Date birthDate_;       // Implementation detail!
    Address address_;      // Implementation detail!
};
```

**The dependency chain:**

Any file that `#include`s `person.h` also transitively includes `<string>`,
`<memory>`, `date.h`, and `address.h`. If `date.h` or `address.h` changes,
every file that includes `person.h` must be recompiled --- even if the change
was to a private implementation detail of `Date` or `Address`.

If `Person` is a widely used class, this can mean that changing a private
member of `Address` triggers recompilation of your entire project.

### Solution 1: The pImpl (Pointer to Implementation) Idiom

The key insight: **you can replace data members with a pointer to a struct
that contains them.** The class definition then depends only on a forward
declaration of the implementation struct, not on the full definitions of the
member types.

```cpp
// =====================================================
// person.h --- the public header (interface)
// =====================================================
#include <string>
#include <memory>

// Forward declarations: no #include needed for Date or Address!
class Date;
class Address;

class Person {
public:
    Person(const std::string& name, const Date& birthday,
           const Address& addr);
    ~Person();                          // Must be declared (see below)

    // Move and copy operations must also be declared here if you want
    // them, because the compiler cannot generate them in headers that
    // do not see the full definition of PersonImpl.
    Person(const Person& rhs);
    Person& operator=(const Person& rhs);
    Person(Person&& rhs) noexcept;
    Person& operator=(Person&& rhs) noexcept;

    std::string name() const;
    std::string birthDate() const;
    std::string address() const;

private:
    // The only data member: a pointer to the implementation.
    // This is the "pImpl" (pointer-to-implementation).
    struct Impl;                         // Forward declaration of nested struct
    std::unique_ptr<Impl> pImpl_;        // Pointer to implementation
};

// =====================================================
// person.cpp --- the implementation file
// =====================================================
#include "person.h"
#include "date.h"        // Now these includes are only in the .cpp file.
#include "address.h"     // Changes to date.h or address.h only trigger
                         // recompilation of person.cpp, NOT of all the
                         // files that include person.h.

// Define the implementation struct.
struct Person::Impl {
    std::string name;
    Date birthDate;
    Address address;

    Impl(const std::string& n, const Date& bd, const Address& a)
        : name(n), birthDate(bd), address(a) {}
};

// Constructor: create the Impl on the heap.
Person::Person(const std::string& name, const Date& birthday,
               const Address& addr)
    : pImpl_(std::make_unique<Impl>(name, birthday, addr)) {}

// Destructor: must be defined in the .cpp file where Impl is complete.
// If it were defined in the header (or defaulted in the header), the
// compiler would try to generate ~unique_ptr<Impl>, which needs the
// full definition of Impl. This would fail or produce undefined behavior.
Person::~Person() = default;

// Copy constructor: deep copy the Impl.
Person::Person(const Person& rhs)
    : pImpl_(std::make_unique<Impl>(*rhs.pImpl_)) {}

// Copy assignment: deep copy the Impl.
Person& Person::operator=(const Person& rhs) {
    if (this != &rhs) {
        *pImpl_ = *rhs.pImpl_;
    }
    return *this;
}

// Move constructor.
Person::Person(Person&& rhs) noexcept = default;

// Move assignment.
Person& Person::operator=(Person&& rhs) noexcept = default;

// Member functions: delegate to Impl.
std::string Person::name() const { return pImpl_->name; }
std::string Person::birthDate() const { return pImpl_->birthDate.toString(); }
std::string Person::address() const { return pImpl_->address.toString(); }
```

**What we achieved:** Files that `#include "person.h"` no longer depend on
`date.h` or `address.h`. If we change `Date` or `Address` (or even add new
private data members to `Person`), only `person.cpp` needs to be recompiled.

### Solution 2: Abstract Base Classes (Interface Classes)

An alternative to pImpl is to define the interface as an abstract base class
with pure virtual functions, and provide the implementation in a derived class
visible only in the `.cpp` file:

```cpp
// =====================================================
// person.h --- the public header (interface class)
// =====================================================
#include <string>
#include <memory>

class Date;      // Forward declaration
class Address;   // Forward declaration

// Person is an abstract base class (interface).
// It has no data members, so it depends on nothing except the
// types used in its public interface.
class Person {
public:
    virtual ~Person() = default;

    virtual std::string name() const = 0;
    virtual std::string birthDate() const = 0;
    virtual std::string address() const = 0;

    // Factory function: clients call this to create Person objects.
    // They never see the concrete class.
    static std::unique_ptr<Person> create(
        const std::string& name,
        const Date& birthday,
        const Address& addr
    );
};

// =====================================================
// person.cpp --- the implementation file
// =====================================================
#include "person.h"
#include "date.h"
#include "address.h"

// RealPerson is the concrete implementation. It is NOT visible
// in person.h, so clients have no dependency on it.
class RealPerson : public Person {
public:
    RealPerson(const std::string& name, const Date& bd, const Address& a)
        : name_(name), birthDate_(bd), address_(a) {}

    std::string name() const override { return name_; }
    std::string birthDate() const override { return birthDate_.toString(); }
    std::string address() const override { return address_.toString(); }

private:
    std::string name_;
    Date birthDate_;
    Address address_;
};

// Factory function implementation.
std::unique_ptr<Person> Person::create(
    const std::string& name, const Date& birthday, const Address& addr)
{
    return std::make_unique<RealPerson>(name, birthday, addr);
}
```

**Usage:**

```cpp
// client.cpp
#include "person.h"
// No need to include date.h or address.h here if we use forward declarations
// or if Date and Address are only used to pass to the factory.

#include "date.h"     // Needed here only because we construct Date/Address objects
#include "address.h"

void processPersons() {
    auto p = Person::create(
        "Alice",
        Date(1990, 3, 15),
        Address("123 Main St", "Springfield", "IL")
    );

    std::cout << p->name() << "\n";
    std::cout << p->birthDate() << "\n";
    std::cout << p->address() << "\n";
}
```

### pImpl vs. Interface Classes: Trade-offs

| Aspect | pImpl | Interface Class |
|--------|-------|-----------------|
| Runtime cost | One indirection (pointer dereference) per member access | Virtual function call per member access (vtable lookup) |
| Memory | Extra heap allocation for Impl | Extra vptr per object |
| Extensibility | Internal; clients cannot extend | Clients can derive new implementations |
| Binary compatibility | Excellent: adding private members does not break ABI | Excellent: adding new pure virtual functions breaks ABI, but adding non-pure virtual functions may not |
| Boilerplate | Must forward all public functions to Impl | Must implement all pure virtual functions in derived class |

### Forward Declarations: The Foundation of Dependency Reduction

The key principle is: **depend on declarations, not definitions.** You can
use forward declarations instead of `#include` whenever you only need to know
that a type exists, not what it contains:

```cpp
// You CAN use a forward declaration when:
class Widget;    // Forward declaration is enough for:

// Widget* ptr;              // Pointers to Widget
// Widget& ref;              // References to Widget (in declarations)
// Widget func();            // Functions that return Widget by value (declaration only)
// void func(Widget w);      // Functions that take Widget by value (declaration only)
// std::unique_ptr<Widget>;  // Smart pointers to Widget (with caveats)

// You CANNOT use a forward declaration when:
// - You need to know the size of Widget (to allocate it on the stack)
// - You need to call Widget's member functions
// - You need to access Widget's data members
// - You need to inherit from Widget
```

### A Comprehensive Real-World Example

Consider a graphics engine with complex interdependencies:

```cpp
// =====================================================
// BEFORE: Tight coupling --- one change rebuilds everything
// =====================================================

// renderer.h
#include "texture.h"      // Full definition of Texture
#include "shader.h"       // Full definition of Shader
#include "mesh.h"         // Full definition of Mesh
#include "camera.h"       // Full definition of Camera
#include "light.h"        // Full definition of Light

class Renderer {
public:
    void render(const Camera& cam, const std::vector<Light>& lights);
    void loadTexture(const std::string& path);
    void setShader(const Shader& shader);
    void addMesh(const Mesh& mesh);

private:
    Texture currentTexture_;     // Requires full definition of Texture
    Shader currentShader_;       // Requires full definition of Shader
    std::vector<Mesh> meshes_;   // Requires full definition of Mesh
    Camera mainCamera_;          // Requires full definition of Camera
    std::vector<Light> lights_;  // Requires full definition of Light
};

// Any change to Texture, Shader, Mesh, Camera, or Light forces
// recompilation of renderer.h and EVERY file that includes it.
```

```cpp
// =====================================================
// AFTER: Loose coupling with pImpl
// =====================================================

// renderer.h
#include <string>
#include <memory>
#include <vector>

// Forward declarations --- no #includes for our types!
class Texture;
class Shader;
class Mesh;
class Camera;
class Light;

class Renderer {
public:
    Renderer();
    ~Renderer();
    Renderer(Renderer&&) noexcept;
    Renderer& operator=(Renderer&&) noexcept;

    void render(const Camera& cam, const std::vector<Light*>& lights);
    void loadTexture(const std::string& path);
    void setShader(const Shader& shader);
    void addMesh(const Mesh& mesh);

private:
    struct Impl;
    std::unique_ptr<Impl> pImpl_;
};

// renderer.cpp
#include "renderer.h"
#include "texture.h"     // Includes are now localized to the .cpp file.
#include "shader.h"
#include "mesh.h"
#include "camera.h"
#include "light.h"

struct Renderer::Impl {
    Texture currentTexture;
    Shader currentShader;
    std::vector<Mesh> meshes;
    Camera mainCamera;
    std::vector<Light> lights;
};

Renderer::Renderer() : pImpl_(std::make_unique<Impl>()) {}
Renderer::~Renderer() = default;
Renderer::Renderer(Renderer&&) noexcept = default;
Renderer& Renderer::operator=(Renderer&&) noexcept = default;

void Renderer::render(const Camera& cam, const std::vector<Light*>& lights) {
    pImpl_->mainCamera = cam;
    // ... rendering logic using pImpl_->currentShader, pImpl_->meshes, etc.
}

void Renderer::loadTexture(const std::string& path) {
    pImpl_->currentTexture.loadFromFile(path);
}

void Renderer::setShader(const Shader& shader) {
    pImpl_->currentShader = shader;
}

void Renderer::addMesh(const Mesh& mesh) {
    pImpl_->meshes.push_back(mesh);
}
```

Now, changing `Texture`, `Shader`, `Mesh`, `Camera`, or `Light` only requires
recompiling `renderer.cpp` --- not the hundreds of files that include
`renderer.h`.

### Practical Tips for Reducing Compilation Dependencies

**1. Prefer forward declarations to `#include` in headers:**

```cpp
// BAD: header includes everything
// widget.h
#include "gadget.h"       // Only needed for Gadget* parameter

class Widget {
public:
    void useGadget(Gadget* g);   // Only uses pointer; forward decl suffices
};

// GOOD: forward declare in header, include in source
// widget.h
class Gadget;   // Forward declaration

class Widget {
public:
    void useGadget(Gadget* g);
};

// widget.cpp
#include "widget.h"
#include "gadget.h"   // Include only where the full definition is needed

void Widget::useGadget(Gadget* g) {
    g->activate();   // Need full definition here, which we have via #include
}
```

**2. Use `<iosfwd>` instead of `<iostream>` in headers:**

```cpp
// BAD: <iostream> is a heavy header
#include <iostream>

class Logger {
public:
    void log(std::ostream& os, const std::string& msg);
};

// GOOD: <iosfwd> is a lightweight header with only forward declarations
#include <iosfwd>
#include <string>

class Logger {
public:
    void log(std::ostream& os, const std::string& msg);
};

// logger.cpp
#include "logger.h"
#include <iostream>   // Full definition needed only in the implementation
```

**3. Provide separate "fwd" headers for your own types:**

```cpp
// geometry_fwd.h --- lightweight forward declarations
class Point;
class Line;
class Circle;
class Rectangle;
class Polygon;

// geometry.h --- full definitions
#include "geometry_fwd.h"

class Point {
    double x_, y_;
public:
    Point(double x = 0, double y = 0);
    // ...
};

class Line {
    Point start_, end_;
public:
    Line(const Point& s, const Point& e);
    // ...
};
// ... etc.

// client.h --- only needs forward declarations
#include "geometry_fwd.h"   // Lightweight: no dependency on geometry details

class Renderer {
public:
    void drawPoint(const Point& p);
    void drawLine(const Line& l);
};

// client.cpp --- needs full definitions for implementation
#include "client.h"
#include "geometry.h"   // Full definitions needed here

void Renderer::drawPoint(const Point& p) {
    // ... uses Point's members
}
```

**4. Use `unique_ptr` rather than `shared_ptr` for pImpl:**

```cpp
// Prefer unique_ptr for pImpl. It has no overhead beyond a raw pointer
// and clearly expresses sole ownership.

class Widget {
public:
    Widget();
    ~Widget();   // Must be declared in header, defined in .cpp where Impl is complete
    Widget(Widget&&) noexcept;
    Widget& operator=(Widget&&) noexcept;

private:
    struct Impl;
    std::unique_ptr<Impl> pImpl_;   // Preferred
};

// Note: shared_ptr does not require the destructor trick because
// shared_ptr stores its deleter at construction time. But shared_ptr
// has higher overhead (reference counting, separate control block),
// and shared ownership semantics are usually not what you want for pImpl.
```

**5. Include-what-you-use (IWYU) discipline:**

```cpp
// Every header should include exactly the headers it needs and no more.
// Every source file should include the headers for every type it uses
// directly, not relying on transitive includes.

// BAD: relying on transitive include
// foo.h includes <vector>
#include "foo.h"
std::vector<int> v;   // Works by accident (through foo.h's include)

// GOOD: include what you use
#include "foo.h"
#include <vector>      // Explicitly include what you use
std::vector<int> v;    // Works by design
```

### Things to Remember

- **The general idea behind minimizing compilation dependencies is to depend
  on declarations instead of definitions.** Two approaches based on this idea
  are the pImpl idiom and interface classes.

- **Library header files should exist in full and declaration-only forms.**
  The Standard Library provides `<iosfwd>` as a model. Your own libraries
  should provide similar `_fwd.h` headers.

- **The pImpl idiom replaces data members with a pointer to an implementation
  struct.** This moves `#include` dependencies from the header to the source
  file, making recompilation cheaper when implementation details change.

- **Interface classes (abstract base classes with factory functions) achieve
  the same decoupling.** Clients program to the abstract interface and never
  see the concrete implementation class.

- **Both pImpl and interface classes have a small runtime cost** (pointer
  indirection and heap allocation for pImpl; virtual function dispatch for
  interface classes), but the improvement in build times for large projects
  more than compensates.
