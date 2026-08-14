# Item 19: Treat Class Design as Type Design

## Visual Summary

```text
┌───────────────────────────────────────────────────────────────────────────┐
│                ITEM 19: TREAT CLASS DESIGN AS TYPE DESIGN                 │
├───────────────────────────────────────────────────────────────────────────┤
│ 1. New class -> new type in the language of your program.                 │
│ 2. Decide construction, destruction, copying, comparison, conversion,     │
│ invariants.                                                               │
│ 3. Decide performance, exception safety, ownership, and threading         │
│ assumptions.                                                              │
│ 4. Only then implement members.                                           │
│ 5. Meaning: class design is semantic design, not just data plus           │
│ functions.                                                                │
└───────────────────────────────────────────────────────────────────────────┘
```

In C++, defining a new class defines a new type. You are not just a class designer -- you
are a **type designer**. Overloaded functions and operators, controlling memory allocation and
deallocation, defining object initialization and finalization -- it's all in your hands. You
should approach class design with the same care that language designers lavish on the design
of built-in types.

Designing good classes is challenging because designing good types is challenging. Good types
have natural syntax, intuitive semantics, and one or more efficient implementations. Here
are the questions you should consider every time you design a class:

## Visual Deep Dive

```text
┌───────────────────────────────────────────────────────────────────────────┐
│                           TYPE DESIGN CHECKLIST                           │
├───────────────────────────────────────────────────────────────────────────┤
│ Construction/destruction                                                  │
│ Copy/move/assignment                                                      │
│ Valid states and invariants                                               │
│ Conversions and operators                                                 │
│ Performance and exception guarantees                                      │
└───────────────────────────────────────────────────────────────────────────┘
```

```text
┌───────────────────────────────────────────────────────────────────────────┐
│                             CLASS DESIGN FLOW                             │
├───────────────────────────────────────────────────────────────────────────┤
│ Name the abstraction                                                      │
│                                     ▼                                     │
│ Define valid values and operations                                        │
│                                     ▼                                     │
│ Decide ownership and copying                                              │
│                                     ▼                                     │
│ Only then write representation and member functions                       │
└───────────────────────────────────────────────────────────────────────────┘
```

### The Comprehensive Design Checklist

**1. How should objects of your new type be created and destroyed?**

This determines the design of your constructors, destructor, and memory allocation/deallocation
functions (`operator new`, `operator delete`, `operator new[]`, `operator delete[]`) if you
write them.

```cpp
// Example: A MemoryPool type that manages its own allocation
class MemoryPool {
public:
    // Custom allocation for pooled objects
    static void* operator new(size_t size);
    static void operator delete(void* ptr, size_t size);

    // Constructor initializes the pool
    explicit MemoryPool(size_t blockSize, size_t numBlocks);

    // Destructor releases all pooled memory
    ~MemoryPool();

    // No copy -- pools are not copyable resources
    MemoryPool(const MemoryPool&) = delete;
    MemoryPool& operator=(const MemoryPool&) = delete;

    // Move is fine -- transfer ownership
    MemoryPool(MemoryPool&& other) noexcept;
    MemoryPool& operator=(MemoryPool&& other) noexcept;
};
```

**2. How should object initialization differ from object assignment?**

This determines how your constructors differ from your assignment operators. Don't confuse
initialization with assignment -- they correspond to different function calls.

```cpp
class Widget {
public:
    Widget(int value);                          // Initialization
    Widget(const Widget& rhs);                  // Initialization (copy ctor)
    Widget& operator=(const Widget& rhs);       // Assignment

    // These are fundamentally different operations.
    // Initialization creates a new object; assignment changes an existing one.
};

Widget w1(10);       // Calls constructor -- initialization
Widget w2 = w1;      // Calls copy constructor -- initialization (NOT assignment!)
w1 = w2;             // Calls operator= -- assignment
```

**3. What does it mean for objects of your new type to be passed by value?**

The copy constructor defines what pass-by-value means for your type. If copying is expensive
or doesn't make semantic sense, consider disabling it or making it explicit.

```cpp
// BAD: Large class that is expensive to copy, yet allows pass-by-value silently
class LargeMatrix {
    double data[1000][1000];  // ~8 MB per copy!
public:
    // Implicit copy constructor copies 8 MB of data every time
    // the matrix is passed by value or returned. Probably not what you want.
};

// GOOD: Either make it non-copyable or provide explicit clone
class LargeMatrix {
    std::unique_ptr<double[]> data_;
    size_t rows_, cols_;
public:
    LargeMatrix(const LargeMatrix&) = delete;             // No accidental copies
    LargeMatrix& operator=(const LargeMatrix&) = delete;

    LargeMatrix(LargeMatrix&&) noexcept = default;        // Move is fine
    LargeMatrix& operator=(LargeMatrix&&) noexcept = default;

    LargeMatrix clone() const;  // Explicit copy when you really need one
};
```

**4. What are the restrictions on legal values for your new type?**

Not all combinations of data member values are valid. The invariants determine the error
checking inside your member functions, especially constructors, assignment operators, and
setters.

```cpp
class Probability {
public:
    explicit Probability(double value) : value_(value) {
        if (value < 0.0 || value > 1.0) {
            throw std::out_of_range("Probability must be in [0.0, 1.0]");
        }
    }

    Probability operator+(const Probability& rhs) const {
        return Probability(std::min(value_ + rhs.value_, 1.0));
    }

    // Every mutating operation must maintain the invariant.

private:
    double value_;  // Invariant: 0.0 <= value_ <= 1.0
};
```

**5. Does your new type fit into an inheritance graph?**

If you inherit from existing classes, you are constrained by those classes -- particularly
whether their functions are virtual or non-virtual. If you intend others to inherit from
your class, that affects whether you declare functions virtual, especially the destructor.

```cpp
// If this is a base class that will be used polymorphically:
class Shape {
public:
    virtual ~Shape();                      // Virtual destructor -- essential!
    virtual double area() const = 0;       // Pure virtual -- must override
    virtual void draw() const;             // Virtual -- may override
    int objectID() const;                  // Non-virtual -- should NOT override
};

// If this is a concrete class NOT meant to be inherited from:
class Point {
public:
    // No virtual functions, no virtual destructor
    // Consider making it final in C++11 and later:
    // class Point final { ... };
    double x, y;
};
```

**6. What kind of type conversions are allowed?**

Do you want implicit conversions? If so, write a non-explicit single-argument constructor
or an implicit conversion function. If you want only explicit conversions, declare them
`explicit`.

```cpp
class Rational {
public:
    // Allows implicit conversion from int to Rational:
    Rational(int numerator = 0, int denominator = 1);

    // This permits: Rational r = 42;    -- int implicitly converts to Rational
    // This permits: doSomething(42);     -- if doSomething takes a Rational
};

class BigNumber {
public:
    // Only explicit conversion from int -- no surprises
    explicit BigNumber(int value);

    // BigNumber b = 42;       -- Error! No implicit conversion.
    // BigNumber b(42);        -- OK, explicit construction.
    // BigNumber b = BigNumber(42); -- OK, explicit construction.
};
```

**7. What operators and functions make sense for the new type?**

Some will be member functions, some will be non-members. See Items 23, 24, and 46.

**8. What standard functions should be disallowed?**

Those are the ones you declare deleted (or in older C++, declare private and don't implement).

```cpp
class Uncopyable {
public:
    Uncopyable() = default;
    Uncopyable(const Uncopyable&) = delete;
    Uncopyable& operator=(const Uncopyable&) = delete;
};
```

**9. Who should have access to the members of your new type?**

This determines which members are `public`, `protected`, and `private`. It also determines
which classes and functions are friends, and whether nesting one class inside another makes
sense.

**10. What is the "undeclared interface" of your new type?**

What guarantees does your type offer with respect to performance, exception safety
(see Item 29), and resource usage (e.g., locks, dynamic memory)? These guarantees
constrain your implementation.

**11. How general is your new type?**

Maybe you're not really defining a new type -- maybe you're defining a whole **family** of
types. If so, you should define a class template rather than a class.

**12. Is a new type really what you need?**

If you're defining a new derived class only to add functionality to an existing class,
perhaps non-member functions or templates would achieve the goal better without creating
a new type.

### Things to Remember

- Class design is type design. Before defining a new type, be sure to consider all the
  issues discussed in this Item.

---
