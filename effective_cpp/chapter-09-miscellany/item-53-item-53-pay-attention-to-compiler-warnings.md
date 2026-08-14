# Item 53: Pay Attention to Compiler Warnings

## Visual Summary

```text
┌───────────────────────────────────────────────────────────────────────────┐
│                ITEM 53: PAY ATTENTION TO COMPILER WARNINGS                │
├───────────────────────────────────────────────────────────────────────────┤
│ 1. Compiler warning appears -> compiler found a suspicious construct.     │
│ 2. Ignoring warnings -> portability and correctness risk accumulates.     │
│ 3. Fix source cause or document intentional suppression narrowly.         │
│ 4. Different compilers warn about different bugs.                         │
│ 5. Meaning: warning-clean code lets real regressions stand out.           │
└───────────────────────────────────────────────────────────────────────────┘
```

## Visual Deep Dive

```text
┌───────────────────────────────────────────────────────────────────────────┐
│                           WARNING HYGIENE FLOW                            │
├───────────────────────────────────────────────────────────────────────────┤
│ Compiler warns about suspicious construct                                 │
│                                     ▼                                     │
│ Fix root cause or document narrow suppression                             │
│                                     ▼                                     │
│ Keep build warning-clean                                                  │
│                                     ▼                                     │
│ New warning becomes visible regression signal                             │
└───────────────────────────────────────────────────────────────────────────┘
```

```text
┌───────────────────────────────────────────────────────────────────────────┐
│                              WARNING POLICY                               │
├───────────────────────────────────────────────────────────────────────────┤
│ Weak policy                       | Strong policy                         │
│ ----------------------------------+-------------------------------------  │
│ Warnings ignored                  | Warnings treated seriously            │
│ Different compilers surprise you  | Portable clean code                   │
│ Real bugs hidden in noise         | Signal stays high                     │
└───────────────────────────────────────────────────────────────────────────┘
```

### Core Concept

Compiler warnings are not optional noise to be silenced. They represent the compiler's best effort to tell you about code that is **technically legal** but **almost certainly wrong**. Experienced C++ programmers treat warnings as errors. Many of the most insidious bugs in C++ programs are things the compiler warned about and the programmer ignored.

### Warning Level Settings

Before examining specific warnings, know how to maximize your compiler's help:

```bash
# GCC / Clang: Maximum useful warnings
g++ -Wall -Wextra -Wpedantic -Werror -Wshadow -Wconversion -Wsign-conversion \
    -Wnon-virtual-dtor -Wold-style-cast -Wcast-align -Wunused \
    -Woverloaded-virtual -Wmisleading-indentation -Wduplicated-cond \
    -Wduplicated-branches -Wlogical-op -Wnull-dereference \
    -Wdouble-promotion -Wformat=2 -Wimplicit-fallthrough \
    -std=c++17 source.cpp

# MSVC: Maximum useful warnings
cl /W4 /WX /permissive- /analyze source.cpp

# CMake: Setting warning levels properly
# In CMakeLists.txt:
# target_compile_options(mylib PRIVATE
#     $<$<CXX_COMPILER_ID:GNU,Clang>:-Wall -Wextra -Wpedantic -Werror>
#     $<$<CXX_COMPILER_ID:MSVC>:/W4 /WX>
# )
```

### Warning 1: Hiding Inherited Virtual Functions

This is the most famous and dangerous warning — the one Meyers specifically highlights in the book. Redefining a non-virtual function in a derived class **hides** the base class version rather than overriding it:

```cpp
// BAD: Accidentally hiding a virtual function due to different parameter types
class Base {
public:
    virtual void display(int value) const {
        std::cout << "Base::display(int): " << value << "\n";
    }
    virtual ~Base() = default;
};

class Derived : public Base {
public:
    // WARNING: 'Derived::display' hides 'Base::display'
    // This has a DIFFERENT parameter type — it's hiding, not overriding!
    virtual void display(double value) const {
        std::cout << "Derived::display(double): " << value << "\n";
    }
};

void demonstrate() {
    Derived d;
    Base* pb = &d;

    pb->display(42);     // Calls Base::display(int) — NOT Derived::display(double)!
    d.display(42);       // Calls Derived::display(double) — implicit int-to-double conversion
    // d.display(42) behaves differently from pb->display(42) — this is almost always a bug
}
```

```cpp
// GOOD: Use override (C++11) to catch this at compile time
class Derived : public Base {
public:
    // COMPILE ERROR: 'display' marked 'override' but does not override any base class method
    void display(double value) const override {  // <-- override catches the mistake
        std::cout << "Derived::display(double): " << value << "\n";
    }
};

// CORRECT version:
class Derived : public Base {
public:
    void display(int value) const override {  // Correct parameter type
        std::cout << "Derived::display(int): " << value << "\n";
    }
};
```

### Warning 2: Implicit Conversions and Narrowing

```cpp
// BAD: Implicit narrowing conversion
void processData(int count) {
    // WARNING: conversion from 'size_t' (aka 'unsigned long') to 'int', possible loss of data
    std::vector<double> data(100);
    int size = data.size();  // size_t -> int: potential data loss on large vectors

    // WARNING: comparing signed and unsigned integers
    for (int i = 0; i < data.size(); ++i) {  // int vs. size_t comparison
        data[i] = i * 1.5;
    }
}

// WARNING: implicit conversion loses integer precision
void sendPacket(uint16_t port) {
    int userPort = 80443;  // Larger than uint16_t can hold
    sendPacket(userPort);  // Silently truncated! Port becomes garbage
}
```

```cpp
// GOOD: Be explicit about conversions
void processData(int count) {
    std::vector<double> data(100);
    auto size = data.size();  // auto deduces size_t — no conversion

    for (std::size_t i = 0; i < data.size(); ++i) {
        data[i] = static_cast<double>(i) * 1.5;
    }

    // Or better yet, use range-based for:
    for (auto& val : data) {
        val = 0.0;
    }
}

void sendPacket(uint16_t port);

void setupNetwork() {
    int userPort = 80443;
    if (userPort < 0 || userPort > 65535) {
        throw std::out_of_range("Port number out of range");
    }
    sendPacket(static_cast<uint16_t>(userPort));
}
```

### Warning 3: Unused Variables and Parameters

```cpp
// BAD: Unused variables — often indicate logic errors
int computeResult(int input) {
    int intermediateResult = input * 42;  // WARNING: unused variable
    int finalResult = input + 1;
    return finalResult;
    // Was intermediateResult supposed to be used? Probably a bug.
}

// BAD: Unused parameters
class EventHandler {
public:
    // WARNING: unused parameter 'event'
    virtual void onMouseMove(int x, int y, const MouseEvent& event) {
        drawCursor(x, y);
        // 'event' is unused — but it's part of the interface
    }
};
```

```cpp
// GOOD: Make intent explicit
int computeResult(int input) {
    int intermediateResult = input * 42;
    int finalResult = intermediateResult + 1;  // Actually use it!
    return finalResult;
}

// GOOD: Suppress unused parameter warnings explicitly
class EventHandler {
public:
    // Option 1: Comment out or omit the parameter name
    virtual void onMouseMove(int x, int y, const MouseEvent& /*event*/) {
        drawCursor(x, y);
    }

    // Option 2 (C++17): Use [[maybe_unused]]
    virtual void onClick([[maybe_unused]] int x, [[maybe_unused]] int y) {
        // Parameters intentionally unused in base class
    }
};
```

### Warning 4: Uninitialized Variables

```cpp
// BAD: Using uninitialized variables — undefined behavior
int calculateScore(bool bonusRound) {
    int score;  // WARNING: 'score' may be used uninitialized
    if (bonusRound) {
        score = 100;
    }
    return score;  // If bonusRound is false, score is uninitialized — UB!
}

// BAD: Partially initialized struct
struct Config {
    int width;
    int height;
    bool fullscreen;
    int refreshRate;
};

Config loadConfig() {
    Config cfg;
    cfg.width = 1920;
    cfg.height = 1080;
    // WARNING: 'cfg.fullscreen' and 'cfg.refreshRate' not initialized
    return cfg;
}
```

```cpp
// GOOD: Always initialize
int calculateScore(bool bonusRound) {
    int score = 0;  // Default value
    if (bonusRound) {
        score = 100;
    }
    return score;
}

// GOOD: Use designated initializers (C++20) or value-initialization
struct Config {
    int width = 0;
    int height = 0;
    bool fullscreen = false;
    int refreshRate = 60;
};

Config loadConfig() {
    Config cfg{
        .width = 1920,
        .height = 1080,
        // fullscreen and refreshRate get their default values
    };
    return cfg;
}
```

### Warning 5: Order of Member Initialization

```cpp
// BAD: Member initializer list order doesn't match declaration order
class TextRenderer {
public:
    // WARNING: member initializer for 'fontSize_' will be executed after
    //          member initializer for 'lineHeight_' because of declaration order
    TextRenderer(int fontSize)
        : fontSize_(fontSize)           // This is written first but executed SECOND
        , lineHeight_(fontSize_ * 1.5)  // This is written second but executed FIRST!
    {
        // lineHeight_ is initialized before fontSize_, so fontSize_ is garbage
        // when lineHeight_ is computed. lineHeight_ gets a garbage value.
    }

private:
    double lineHeight_;  // Declared first — initialized first!
    int fontSize_;       // Declared second — initialized second!
};
```

```cpp
// GOOD: Match initializer order to declaration order
class TextRenderer {
public:
    TextRenderer(int fontSize)
        : lineHeight_(fontSize * 1.5)  // Use constructor parameter, not member
        , fontSize_(fontSize)
    {}

    // BETTER: Reorder declarations to match logical initialization order
    // Or rewrite so the order doesn't matter:

private:
    int fontSize_;       // Now declared first
    double lineHeight_;  // Now declared second
};

class TextRenderer {
public:
    TextRenderer(int fontSize)
        : fontSize_(fontSize)
        , lineHeight_(fontSize_ * 1.5)  // Safe — fontSize_ is initialized first
    {}

private:
    int fontSize_;
    double lineHeight_;
};
```

### Warning 6: Missing Return Statements

```cpp
// BAD: Not all control paths return a value
// WARNING: control reaches end of non-void function
int classify(int value) {
    if (value > 0) return 1;
    if (value < 0) return -1;
    // What about value == 0? Missing return! Undefined behavior!
}

// BAD: Switch without default
enum class Color { Red, Green, Blue };

const char* colorName(Color c) {
    switch (c) {
        case Color::Red:   return "Red";
        case Color::Green: return "Green";
        // WARNING: not all enum values handled, and no default
        // If Color::Blue is passed, UB!
    }
}
```

```cpp
// GOOD: All paths return
int classify(int value) {
    if (value > 0) return 1;
    if (value < 0) return -1;
    return 0;
}

// GOOD: Handle all cases
const char* colorName(Color c) {
    switch (c) {
        case Color::Red:   return "Red";
        case Color::Green: return "Green";
        case Color::Blue:  return "Blue";
    }
    // Some compilers still warn without this, even though all enum values are covered:
    return "Unknown";
}
```

### Warning 7: Dangling References and Lifetime Issues

```cpp
// BAD: Returning reference to local
// WARNING: reference to local variable returned
const std::string& greet(const std::string& name) {
    std::string greeting = "Hello, " + name + "!";
    return greeting;  // greeting is destroyed when the function returns!
}

// BAD: Dangling reference from temporary (C++20 compilers catch more of these)
std::string_view getName() {
    std::string name = "Alice";
    return name;  // WARNING: returning string_view of local string
}
```

```cpp
// GOOD: Return by value
std::string greet(const std::string& name) {
    return "Hello, " + name + "!";  // Return by value — move semantics makes this efficient
}

// GOOD: Ensure the string outlives the string_view
class User {
public:
    std::string_view getName() const { return name_; }  // OK — member outlives the call
private:
    std::string name_;
};
```

### Warning 8: Implicit Fallthrough in Switch

```cpp
// BAD: Accidental fallthrough
void handleEvent(int eventType) {
    switch (eventType) {
        case 1:
            startAnimation();
            // WARNING: implicit fallthrough
        case 2:
            playSound();
            break;
        case 3:
            logEvent();
            break;
    }
}
```

```cpp
// GOOD: Use [[fallthrough]] (C++17) when intentional, break otherwise
void handleEvent(int eventType) {
    switch (eventType) {
        case 1:
            startAnimation();
            [[fallthrough]];  // Explicit: "yes, I intend to fall through"
        case 2:
            playSound();
            break;
        case 3:
            logEvent();
            break;
        default:
            break;
    }
}
```

### Warning 9: Shadowed Variables

```cpp
// BAD: Variable shadowing
int count = 10;  // Global

void process() {
    int count = 5;  // WARNING: declaration shadows a global variable
    for (int i = 0; i < count; ++i) {
        int count = i * 2;  // WARNING: declaration shadows a local variable
        std::cout << count << "\n";  // Which count? The innermost one.
    }
}
```

```cpp
// GOOD: Use distinct names
int globalCount = 10;

void process() {
    int localCount = 5;
    for (int i = 0; i < localCount; ++i) {
        int doubled = i * 2;
        std::cout << doubled << "\n";
    }
}
```

### Warning 10: Non-Virtual Destructor in Base Class

```cpp
// BAD: Base class with virtual functions but non-virtual destructor
// WARNING: class 'Base' has virtual functions but a non-virtual destructor
class Base {
public:
    virtual void doWork() = 0;
    ~Base() {}  // Non-virtual destructor!
};

class Derived : public Base {
public:
    void doWork() override { /* ... */ }
    ~Derived() { delete[] data_; }  // This won't be called via Base*!
private:
    int* data_ = new int[100];
};

void leak() {
    Base* pb = new Derived;
    delete pb;  // Undefined behavior! Only ~Base() runs, ~Derived() is skipped
    // data_ is leaked
}
```

```cpp
// GOOD: Virtual destructor in polymorphic base classes
class Base {
public:
    virtual void doWork() = 0;
    virtual ~Base() = default;  // Virtual destructor
};
```

### The -Werror Philosophy

```cpp
// In your build system, treat warnings as errors:
// This prevents "warning debt" from accumulating.

// CMake:
// target_compile_options(myproject PRIVATE
//     $<$<CXX_COMPILER_ID:GNU,Clang>:-Werror>
//     $<$<CXX_COMPILER_ID:MSVC>:/WX>
// )

// EXCEPTION: Third-party headers may produce warnings you can't fix.
// Use system includes to suppress them:
// target_include_directories(myproject SYSTEM PRIVATE ${THIRD_PARTY_INCLUDE_DIR})

// Or selectively suppress specific warnings:
#pragma GCC diagnostic push
#pragma GCC diagnostic ignored "-Wunused-parameter"
#include <third_party_header.h>
#pragma GCC diagnostic pop
```

### Modern C++ Attributes That Help

```cpp
// C++11: [[noreturn]] — function never returns
[[noreturn]] void fatalError(const std::string& msg) {
    std::cerr << "FATAL: " << msg << "\n";
    std::abort();
}

// C++14: [[deprecated]] — mark APIs for removal
[[deprecated("Use newFunction() instead")]]
void oldFunction() { /* ... */ }

// C++17: [[nodiscard]] — warn if return value is ignored
[[nodiscard]] std::error_code saveFile(const std::string& path) {
    // ...
    return {};
}

void usage() {
    saveFile("data.txt");  // WARNING: ignoring return value with 'nodiscard' attribute
    // GOOD:
    auto ec = saveFile("data.txt");
    if (ec) handleError(ec);

    // Or explicitly discard:
    (void)saveFile("data.txt");  // Intentionally ignoring
}

// C++20: [[likely]] / [[unlikely]] — branch prediction hints
int processInput(int value) {
    if (value > 0) [[likely]] {
        return value * 2;
    } else [[unlikely]] {
        throw std::invalid_argument("Negative value");
    }
}
```

### Things to Remember

- Take compiler warnings seriously. Strive for warning-free code at the maximum warning level supported by your compilers.

- Don't become dependent on compiler warnings to catch errors. What one compiler warns about, another may not. Moving to a new compiler may eliminate warnings you've been relying on.

- Use `override` (C++11) to catch virtual function signature mismatches at compile time rather than relying on warnings.

- Treat warnings as errors (`-Werror` / `/WX`) in your build system to prevent warning debt from accumulating.

- Modern C++ attributes (`[[nodiscard]]`, `[[deprecated]]`, `[[maybe_unused]]`, `[[fallthrough]]`) replace many situations where you'd previously rely on warnings or suppress them.

---
