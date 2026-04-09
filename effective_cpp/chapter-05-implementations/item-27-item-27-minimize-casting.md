# Item 27: Minimize casting

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
