# Item 39: Use private inheritance judiciously

## Visual Summary

```text
┌───────────────────────────────────────────────────────────────────────────┐
│               ITEM 39: USE PRIVATE INHERITANCE JUDICIOUSLY                │
├───────────────────────────────────────────────────────────────────────────┤
│ 1. private inheritance -> implemented-in-terms-of, not is-a.              │
│ 2. Composition usually expresses this with less coupling.                 │
│ 3. Use private inheritance when you need protected access or virtual      │
│ override hooks.                                                           │
│ 4. Empty base optimization can be a special storage reason.               │
│ 5. Meaning: private inheritance is an implementation tool, not a public   │
│ model.                                                                    │
└───────────────────────────────────────────────────────────────────────────┘
```

## Visual Deep Dive

```text
┌───────────────────────────────────────────────────────────────────────────┐
│                    PRIVATE INHERITANCE VS COMPOSITION                     │
├───────────────────────────────────────────────────────────────────────────┤
│ Composition                       | Private inheritance                   │
│ ----------------------------------+-------------------------------------  │
│ Default choice                    | Need protected access                 │
│ Lower coupling                    | Need virtual override hook            │
│ Clear has-a/use-a                 | Maybe empty base optimization         │
└───────────────────────────────────────────────────────────────────────────┘
```

```text
┌───────────────────────────────────────────────────────────────────────────┐
│                        PRIVATE INHERITANCE MEANING                        │
├───────────────────────────────────────────────────────────────────────────┤
│ Derived privately inherits Base                                           │
│                                     ▼                                     │
│ Users cannot treat Derived as Base                                        │
│                                     ▼                                     │
│ Base is implementation detail                                             │
│                                     ▼                                     │
│ Relationship means implemented-in-terms-of                                │
└───────────────────────────────────────────────────────────────────────────┘
```

### What Private Inheritance Means

Private inheritance means "is-implemented-in-terms-of." It has nothing to do with "is-a." If `Derived` privately inherits from `Base`:

- All public and protected members of `Base` become private in `Derived`.
- There is no implicit conversion from `Derived*` to `Base*`.
- Compilers will not convert a `Derived` object to a `Base` object.

```cpp
class Timer {
public:
    explicit Timer(int intervalMs) : interval_(intervalMs) {}
    virtual void onTick() {
        std::cout << "Timer tick\n";
    }
    void start() {
        // simulate periodic ticking
        for (int i = 0; i < 5; ++i) {
            onTick();
        }
    }
private:
    int interval_;
};

// Private inheritance: Widget is-implemented-in-terms-of Timer
class Widget : private Timer {
public:
    Widget() : Timer(500) {}

    void startMonitoring() {
        start();  // can call Timer::start() from within Widget
    }

private:
    void onTick() override {
        std::cout << "Widget: checking for updates...\n";
    }
};

Widget w;
w.startMonitoring();  // OK
// Timer* tp = &w;    // ERROR -- private inheritance prevents conversion
// w.start();         // ERROR -- start() is private in Widget
```

### Composition is Usually Preferable

Private inheritance achieves the same thing as composition, and composition is generally preferable because:
- Composition allows you to control what is exposed.
- Composition is easier to understand.
- Composition does not create implicit coupling.

```cpp
// GOOD -- prefer composition over private inheritance
class Widget {
public:
    void startMonitoring() {
        timer_.start();
    }

private:
    // Inner class that overrides onTick
    class WidgetTimer : public Timer {
    public:
        WidgetTimer() : Timer(500) {}
    private:
        void onTick() override {
            std::cout << "Widget: checking for updates...\n";
        }
    };

    WidgetTimer timer_;  // composition: Widget has-a WidgetTimer
};
```

This composition approach has two additional advantages over private inheritance:
1. **Prevents derived classes from overriding `onTick`**. If `Widget` privately inherits from `Timer`, classes derived from `Widget` can still override `onTick`. With composition, the `WidgetTimer` class is private, so derived classes cannot interfere.
2. **Minimizes compilation dependencies**. With composition, `Timer` can be forward-declared and the `WidgetTimer` can be defined in the `.cpp` file (using the Pimpl idiom), breaking the compile-time dependency.

### When Private Inheritance is the Right Choice

**Case 1: The Empty Base Optimization (EBO)**

When the base class has no data members (it is "empty"), private inheritance can save space:

```cpp
class Empty {
    // No data members, but may have typedefs, enums, static members,
    // or non-virtual functions
    using DataType = int;
    static int count();
    void doSomething() {}
};

// With composition:
class Widget1 {
    int data_;
    Empty e_;  // typically takes 1 byte + padding = 4 or 8 bytes wasted
};
// sizeof(Widget1) > sizeof(int)

// With private inheritance:
class Widget2 : private Empty {
    int data_;
};
// sizeof(Widget2) == sizeof(int) -- EBO kicks in!
```

The Empty Base Optimization (EBO) means that an empty base class need not occupy any space. This matters when you are dealing with policy classes, traits, or allocator classes that contain no data.

```cpp
// GOOD -- EBO with allocator (real-world usage)
template <typename T, typename Allocator = std::allocator<T>>
class SmallVector : private Allocator {
    // Allocator is typically empty. Private inheritance + EBO means
    // SmallVector is no bigger than it needs to be.
public:
    using Allocator::allocate;    // selectively expose if needed
    using Allocator::deallocate;

    // ... vector implementation
private:
    T* data_;
    std::size_t size_;
    std::size_t capacity_;
};
```

**Case 2: You need access to protected members**

```cpp
// Private inheritance is needed when you must access protected members
// or override virtual functions, AND you want to hide the base interface.

class DatabaseDriver {
protected:
    virtual void onConnect() {
        std::cout << "Default connection setup\n";
    }
    virtual void onDisconnect() {
        std::cout << "Default disconnection cleanup\n";
    }

    void rawQuery(const std::string& sql) {
        std::cout << "Executing raw SQL: " << sql << "\n";
    }
};

// Cannot use composition here because we need to override
// protected virtual functions and call protected members.
class DatabaseConnection : private DatabaseDriver {
public:
    void connect() {
        onConnect();  // access protected member
    }
    void disconnect() {
        onDisconnect();  // access protected member
    }
    void executeQuery(const std::string& sql) {
        rawQuery(sql);  // access protected member
    }

private:
    void onConnect() override {
        std::cout << "Custom connection: setting timeout, charset...\n";
    }
    void onDisconnect() override {
        std::cout << "Custom disconnect: flushing logs...\n";
    }
};
```

### A Practical Comparison

```cpp
// Scenario: Implement a widget that needs to react to timer events
// and also needs an allocator

// Approach 1: All composition (possibly wastes space)
class WidgetV1 {
    class TimerImpl : public Timer {
        void onTick() override { /* ... */ }
    };
    TimerImpl timer_;
    std::allocator<int> alloc_;  // wastes space -- allocator is empty
    int data_;
};

// Approach 2: Private inheritance for EBO, composition for timer
class WidgetV2 : private std::allocator<int> {
    class TimerImpl : public Timer {
        void onTick() override { /* ... */ }
    };
    TimerImpl timer_;
    int data_;
    // std::allocator<int> takes zero space via EBO
};
```

### Things to Remember

- Private inheritance means "is-implemented-in-terms-of." It is usually inferior to composition, but it makes sense when a derived class needs access to protected base class members or needs to redefine inherited virtual functions.
- Unlike composition, private inheritance enables the empty base optimization (EBO). This can be important for library developers who work hard to minimize object sizes.
- Use private inheritance judiciously. Use it only when composition truly cannot do the job.

---
