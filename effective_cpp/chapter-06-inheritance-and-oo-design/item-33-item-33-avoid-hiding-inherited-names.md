# Item 33: Avoid hiding inherited names

## Visual Summary

```text
┌───────────────────────────────────────────────────────────────────────────┐
│                   ITEM 33: AVOID HIDING INHERITED NAMES                   │
├───────────────────────────────────────────────────────────────────────────┤
│ 1. Derived declares function named f -> base overloads named f become     │
│ hidden.                                                                   │
│ 2. Caller expects overload set -> only derived names are visible.         │
│ 3. using Base::f -> reintroduces base overloads.                          │
│ 4. Forwarding functions -> expose selected base functions only.           │
│ 5. Meaning: name lookup is by name first, not by full signature first.    │
└───────────────────────────────────────────────────────────────────────────┘
```

## Visual Deep Dive

```text
┌───────────────────────────────────────────────────────────────────────────┐
│                             NAME HIDING FLOW                              │
├───────────────────────────────────────────────────────────────────────────┤
│ Base has overloads f(int), f(double)                                      │
│                                     ▼                                     │
│ Derived declares f(string)                                                │
│                                     ▼                                     │
│ Lookup finds Derived::f name first                                        │
│                                     ▼                                     │
│ All Base::f overloads are hidden unless reintroduced                      │
└───────────────────────────────────────────────────────────────────────────┘
```

```text
┌───────────────────────────────────────────────────────────────────────────┐
│                                FIX OPTIONS                                │
├───────────────────────────────────────────────────────────────────────────┤
│ using Base::f; brings all base overloads back                             │
│ Forwarding function exposes selected overloads                            │
│ Avoid accidental same-name declarations when not intended                 │
└───────────────────────────────────────────────────────────────────────────┘
```

### How Name Hiding Works in C++

C++ name hiding in inheritance follows the same principle as name hiding in nested scopes: names in an inner scope hide names in an outer scope. The types and parameter lists are irrelevant -- it is purely about the *name*.

```cpp
// Demonstration of scope-based name hiding
int x = 5;             // global x

void someFunc() {
    double x = 3.14;   // local x HIDES global x
    std::cout << x;    // uses the local double x, not global int x
}
```

The same thing happens with inheritance:

```cpp
// BAD -- derived class hides base class overloads
class Base {
public:
    virtual void mf1() { std::cout << "Base::mf1()\n"; }
    virtual void mf1(int x) { std::cout << "Base::mf1(int)\n"; }

    virtual void mf2() { std::cout << "Base::mf2()\n"; }

    void mf3() { std::cout << "Base::mf3()\n"; }
    void mf3(double d) { std::cout << "Base::mf3(double)\n"; }
};

class Derived : public Base {
public:
    void mf1() override {   // hides ALL Base::mf1 overloads!
        std::cout << "Derived::mf1()\n";
    }

    void mf3() {             // hides ALL Base::mf3 overloads!
        std::cout << "Derived::mf3()\n";
    }
};

Derived d;
d.mf1();       // OK: calls Derived::mf1()
d.mf1(42);     // ERROR! Base::mf1(int) is hidden!
d.mf2();       // OK: calls Base::mf2()
d.mf3();       // OK: calls Derived::mf3()
d.mf3(3.14);   // ERROR! Base::mf3(double) is hidden!
```

### The Fix: Using Declarations

The `using` declaration brings the hidden base class names into the derived class scope:

```cpp
// GOOD -- using declarations unhide base class names
class Derived : public Base {
public:
    using Base::mf1;    // make all Base::mf1 overloads visible
    using Base::mf3;    // make all Base::mf3 overloads visible

    void mf1() override {
        std::cout << "Derived::mf1()\n";
    }

    void mf3() {
        std::cout << "Derived::mf3()\n";
    }
};

Derived d;
d.mf1();       // OK: calls Derived::mf1()
d.mf1(42);     // OK: calls Base::mf1(int) -- no longer hidden!
d.mf2();       // OK: calls Base::mf2()
d.mf3();       // OK: calls Derived::mf3()
d.mf3(3.14);   // OK: calls Base::mf3(double) -- no longer hidden!
```

### Private Inheritance and Forwarding Functions

Under private inheritance, you might not want all inherited overloads to be visible. In that case, use a forwarding function instead of a `using` declaration:

```cpp
// GOOD -- forwarding function selectively exposes base functionality
class Base {
public:
    virtual void mf1() { std::cout << "Base::mf1()\n"; }
    virtual void mf1(int x) { std::cout << "Base::mf1(" << x << ")\n"; }
    virtual void mf1(double d, int x) { std::cout << "Base::mf1(double,int)\n"; }
};

class Derived : private Base {
public:
    // Only expose the no-arg version
    virtual void mf1() {
        Base::mf1();    // forwarding function
    }
    // Base::mf1(int) and Base::mf1(double, int) remain inaccessible
};

Derived d;
d.mf1();         // OK: calls Derived::mf1() which forwards to Base::mf1()
d.mf1(42);       // ERROR: hidden, as intended
```

### A More Realistic Example: Widget Hierarchy

```cpp
// BAD -- name hiding breaks the interface
class Widget {
public:
    virtual ~Widget() = default;

    virtual void draw() {
        std::cout << "Widget::draw() -- default rendering\n";
    }
    virtual void draw(const Rect& clipRect) {
        std::cout << "Widget::draw(Rect) -- clipped rendering\n";
    }
    virtual void draw(const Rect& clipRect, int opacity) {
        std::cout << "Widget::draw(Rect, int) -- clipped + opacity\n";
    }

    void resize(int w, int h) { width_ = w; height_ = h; }
    void resize(const Size& s) { width_ = s.w; height_ = s.h; }

protected:
    int width_ = 100, height_ = 100;
};

class Button : public Widget {
public:
    // Override only the no-arg version, but ACCIDENTALLY hides the others!
    void draw() override {
        std::cout << "Button::draw() -- button-specific rendering\n";
    }
};

Button b;
b.draw();                        // OK
b.draw(Rect{0, 0, 50, 50});     // ERROR! Hidden!
b.draw(Rect{0, 0, 50, 50}, 128);// ERROR! Hidden!
```

```cpp
// GOOD -- using declaration preserves the full interface
class Button : public Widget {
public:
    using Widget::draw;   // unhide all draw overloads

    void draw() override {
        std::cout << "Button::draw() -- button-specific rendering\n";
    }
};

Button b;
b.draw();                         // OK: Button::draw()
b.draw(Rect{0, 0, 50, 50});      // OK: Widget::draw(Rect)
b.draw(Rect{0, 0, 50, 50}, 128); // OK: Widget::draw(Rect, int)
```

### Template Base Classes and Name Hiding

Name hiding also interacts with template base classes. The compiler does not look into dependent base classes:

```cpp
// BAD -- name not found in dependent base class
template <typename T>
class LoggingBase {
public:
    void log(const std::string& msg) {
        std::cout << "[LOG] " << msg << "\n";
    }
};

template <typename T>
class Processor : public LoggingBase<T> {
public:
    void process() {
        log("Processing...");  // ERROR! Compiler doesn't look in LoggingBase<T>
    }
};
```

```cpp
// GOOD -- three ways to fix it
template <typename T>
class Processor : public LoggingBase<T> {
public:
    using LoggingBase<T>::log;  // Approach 1: using declaration

    void process() {
        log("Processing...");          // works with Approach 1
        this->log("Processing...");    // Approach 2: qualify with this->
        LoggingBase<T>::log("Proc.."); // Approach 3: fully qualified (suppresses virtual)
    }
};
```

### Things to Remember

- Names in derived classes hide names in base classes. Under public inheritance, this is never desirable because it violates the "is-a" relationship.
- To make hidden names visible again, employ `using` declarations or forwarding functions.
- A `using` declaration brings *all* overloads of a given name into the derived class scope. Use forwarding functions when you want to expose only specific overloads.

---
