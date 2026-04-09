# Item 30: Understand the ins and outs of inlining

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
