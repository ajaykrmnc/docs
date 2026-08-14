# Item 17: Store newed objects in smart pointers in standalone statements

## Visual Summary

```text
┌───────────────────────────────────────────────────────────────────────────┐
│  ITEM 17: STORE NEWED OBJECTS IN SMART POINTERS IN STANDALONE STATEMENTS  │
├───────────────────────────────────────────────────────────────────────────┤
│ 1. Function call arguments may be evaluated in flexible order.            │
│ 2. new object happens -> another argument throws before smart pointer     │
│ construction.                                                             │
│ 3. Raw pointer is stranded -> resource leaks.                             │
│ 4. Standalone smart pointer statement -> ownership captured before risky  │
│ work.                                                                     │
│ 5. Meaning: never leave a freshly newed object temporarily unowned.       │
└───────────────────────────────────────────────────────────────────────────┘
```

## Visual Deep Dive

```text
┌───────────────────────────────────────────────────────────────────────────┐
│                         ARGUMENT EVALUATION LEAK                          │
├───────────────────────────────────────────────────────────────────────────┤
│ new Widget happens                                                        │
│                                     ▼                                     │
│ Another function argument is evaluated                                    │
│                                     ▼                                     │
│ That argument throws                                                      │
│                                     ▼                                     │
│ Smart pointer was not constructed yet -> leak                             │
└───────────────────────────────────────────────────────────────────────────┘
```

```text
┌───────────────────────────────────────────────────────────────────────────┐
│                         SAFE STANDALONE STATEMENT                         │
├───────────────────────────────────────────────────────────────────────────┤
│ Create smart pointer in its own statement                                 │
│                                     ▼                                     │
│ Ownership captured immediately                                            │
│                                     ▼                                     │
│ Then call functions that may throw                                        │
│                                     ▼                                     │
│ Destructor releases on failure                                            │
└───────────────────────────────────────────────────────────────────────────┘
```

### The Subtle Bug

Consider this seemingly innocent code:

```cpp
int priority();
void processWidget(std::shared_ptr<Widget> pw, int priority);
```

You might call `processWidget` like this:

```cpp
// BAD: Potential resource leak!
processWidget(std::shared_ptr<Widget>(new Widget), priority());
```

This looks safe -- we are using a smart pointer. But it can leak!

### Why It Leaks: Evaluation Order

The C++ standard gives compilers significant freedom in the order they evaluate function
arguments. In the call above, three things must happen before `processWidget` can be called:

1. Execute `new Widget`
2. Construct the `shared_ptr<Widget>`
3. Call `priority()`

The C++ standard requires that step 2 happens after step 1 (the `shared_ptr` constructor
needs the result of `new Widget`). But **step 3 can happen at any point** -- before step 1,
between steps 1 and 2, or after step 2.

A compiler might choose this order:

1. Execute `new Widget`          -- Widget is allocated on the heap
2. Call `priority()`             -- **If this throws, the Widget is leaked!**
3. Construct `shared_ptr<Widget>`  -- This never executes

The `Widget` was `new`ed in step 1, but the `shared_ptr` that would manage it is not
constructed until step 3. If `priority()` throws in step 2, the `Widget` leaks because
nothing is responsible for deleting it.

### The Fix: Standalone Statements

The solution is to separate the creation of the smart pointer into its own statement:

```cpp
// GOOD: Store the newed object in a smart pointer in a standalone statement
std::shared_ptr<Widget> pw(new Widget);  // Statement 1: no leak possible
processWidget(pw, priority());           // Statement 2: no leak possible
```

Now the sequence is deterministic:
1. `new Widget` is executed and immediately handed to the `shared_ptr` constructor.
2. `priority()` is called.
3. `processWidget` is called.

If `priority()` throws, `pw` has already been constructed and its destructor will delete
the `Widget`.

### The Modern Fix: make_shared and make_unique

C++11's `std::make_shared` and C++14's `std::make_unique` eliminate this problem entirely:

```cpp
// BEST: make_shared combines allocation and smart pointer construction
processWidget(std::make_shared<Widget>(), priority());
```

With `make_shared`, the allocation and the `shared_ptr` construction are a single,
indivisible operation. There is no window where the `Widget` exists but is not yet managed
by a smart pointer.

```cpp
// BEST: make_unique (C++14)
void processWidget(std::unique_ptr<Widget> pw, int priority);

processWidget(std::make_unique<Widget>(), priority());
```

### Detailed Walkthrough: Why the Order Matters

Let us trace through the problem step by step with a concrete example:

```cpp
class Widget {
public:
    Widget() {
        std::cout << "Widget constructed at " << this << "\n";
        data_ = new int[1000];  // Widget allocates its own resources
    }
    ~Widget() {
        std::cout << "Widget destroyed at " << this << "\n";
        delete[] data_;
    }
private:
    int* data_;
};

int priority() {
    // Imagine this reads from a database, a file, or does complex computation
    throw std::runtime_error("Priority database unavailable!");
    return 0;  // Never reached
}

void processWidget(std::shared_ptr<Widget> pw, int p) {
    std::cout << "Processing widget with priority " << p << "\n";
}
```

#### BAD path (compiler chooses unfortunate evaluation order):

```cpp
try {
    // Compiler may evaluate in this order:
    // 1. new Widget        -> Widget constructed, raw pointer exists
    // 2. priority()        -> THROWS! Stack unwinding begins.
    // 3. shared_ptr(...)   -> Never reached. Widget is leaked.
    processWidget(std::shared_ptr<Widget>(new Widget), priority());
}
catch (const std::exception& e) {
    std::cout << "Caught: " << e.what() << "\n";
    // Output: "Widget constructed at 0x..."
    //         "Caught: Priority database unavailable!"
    // Note: NO "Widget destroyed" message -- the Widget leaked!
}
```

#### GOOD path (standalone statement):

```cpp
try {
    std::shared_ptr<Widget> pw(new Widget);  // Widget is safely managed
    processWidget(pw, priority());           // If priority() throws...
}
catch (const std::exception& e) {
    std::cout << "Caught: " << e.what() << "\n";
    // Output: "Widget constructed at 0x..."
    //         "Widget destroyed at 0x..."  <-- pw's destructor cleans up!
    //         "Caught: Priority database unavailable!"
}
```

### This Problem Extends Beyond Function Arguments

The same issue can arise in any expression where a `new` and other potentially-throwing
operations are interleaved:

```cpp
// BAD: Multiple news in one expression
auto p = std::make_pair(
    std::shared_ptr<Widget>(new Widget),
    std::shared_ptr<Gadget>(new Gadget)
);
// If the second new succeeds but the first shared_ptr hasn't been constructed yet
// (or vice versa), a throw would leak.

// GOOD: Separate statements
auto pw = std::make_shared<Widget>();
auto pg = std::make_shared<Gadget>();
auto p = std::make_pair(pw, pg);
```

```cpp
// BAD: new in a ternary expression
std::shared_ptr<Widget> pw(
    condition ? new SpecialWidget : new Widget
);
// This is actually fine because only one new is evaluated, and it is directly
// passed to the shared_ptr constructor. But it is easier to reason about:

// GOOD: Clear and unambiguous
std::shared_ptr<Widget> pw;
if (condition) {
    pw = std::make_shared<SpecialWidget>();
} else {
    pw = std::make_shared<Widget>();
}
```

### C++17 Changes

Starting with C++17, the evaluation order of function arguments was tightened. Specifically,
the expressions associated with a single parameter must be fully evaluated before the
evaluation of any other parameter begins. This means:

```cpp
// In C++17 and later, this is safe:
processWidget(std::shared_ptr<Widget>(new Widget), priority());
// Because: either (new Widget + shared_ptr construction) happens entirely before
// priority(), or priority() happens entirely before (new Widget + shared_ptr construction).
```

However, even in C++17, using `make_shared` / `make_unique` is still recommended because:

1. It communicates intent more clearly.
2. It avoids the `new`/`delete` asymmetry (no raw `new` at all).
3. `make_shared` can be more efficient (single allocation for object + control block).
4. Code may need to compile on pre-C++17 compilers.

### Complete Example: A Factory with Exception Safety

```cpp
#include <memory>
#include <string>
#include <stdexcept>
#include <iostream>

class Config {
public:
    explicit Config(const std::string& filename) {
        std::cout << "Loading config from " << filename << "\n";
        // Might throw if file not found
    }
};

class Logger {
public:
    explicit Logger(const std::string& logfile) {
        std::cout << "Opening log: " << logfile << "\n";
    }
};

class Database {
public:
    Database(const std::string& connStr, int timeout) {
        std::cout << "Connecting to " << connStr << "\n";
        if (timeout < 0) throw std::runtime_error("Invalid timeout");
    }
};

int computeTimeout(const Config& cfg) {
    // Might throw
    return 30;
}

// BAD: Multiple potential leaks
void initializeSystem_bad() {
    processResources(
        std::shared_ptr<Config>(new Config("app.cfg")),
        std::shared_ptr<Logger>(new Logger("app.log")),
        std::shared_ptr<Database>(new Database("db://host",
                                               computeTimeout(*new Config("app.cfg"))))
    );
    // This is a mess: raw new of Config that is never managed,
    // multiple unsequenced new operations, etc.
}

// GOOD: Each resource created in a standalone statement
void initializeSystem_good() {
    auto config = std::make_shared<Config>("app.cfg");
    auto logger = std::make_shared<Logger>("app.log");

    int timeout = computeTimeout(*config);  // Might throw -- but nothing leaks
    auto database = std::make_shared<Database>("db://host", timeout);

    processResources(config, logger, database);
    // If any step throws, all previously created resources are cleaned up
    // by their shared_ptr destructors during stack unwinding.
}
```

### Guideline Summary

```
Rule of thumb:
  NEVER write "new" inside a function call's argument list.
  Always store the result of "new" in a named smart pointer first,
  or use make_shared / make_unique.

// BAD patterns:
f(shared_ptr<T>(new T), g());
f(unique_ptr<T>(new T), g());
f(shared_ptr<T>(new T), shared_ptr<U>(new U));

// GOOD patterns:
auto p = make_shared<T>();     // or make_unique<T>()
f(p, g());

auto p1 = make_shared<T>();
auto p2 = make_shared<U>();
f(p1, p2);
```

### Things to Remember

- **Store `new`ed objects in smart pointers in standalone statements. Failure to do this can
  lead to subtle resource leaks when exceptions are thrown, because compilers have latitude
  to reorder operations within a single statement.**

- **Prefer `std::make_shared` (C++11) and `std::make_unique` (C++14) over raw `new` with
  smart pointer constructors. These functions combine allocation and smart pointer
  construction into a single, atomic operation, eliminating the window for leaks.**

---

## Summary of Chapter 3

| Item | Key Principle |
|---|---|
| 13 | Use RAII objects to manage resources. Acquire in constructors, release in destructors. |
| 14 | Choose the right copying strategy: prohibit, reference-count, deep copy, or transfer ownership. |
| 15 | Provide `get()` or conversion operators so RAII objects work with raw-resource APIs. |
| 16 | Match `new` with `delete` and `new[]` with `delete[]`. Prefer containers over raw arrays. |
| 17 | Store `new`ed objects in smart pointers in standalone statements. Prefer `make_shared`/`make_unique`. |

The overarching theme: **make resource management automatic and exception-safe by tying
resource lifetimes to object lifetimes**. When you follow RAII consistently, resource leaks
become nearly impossible, and your code becomes simpler, safer, and easier to maintain.
