# Chapter 4: Designs and Declarations

This chapter is the heart of "Effective C++" -- it addresses the design decisions that determine
whether your C++ software is correct, efficient, and maintainable. Good interfaces are easy to
use correctly and hard to use incorrectly. Good class designs mirror the thought that goes into
designing built-in types. The items here cover parameter passing, return values, encapsulation,
namespace design, swap mechanics, and variable lifetime -- all critical to writing professional C++.

---

## Item 18: Make Interfaces Easy to Use Correctly and Hard to Use Incorrectly

Good interfaces are a joy to use. Bad interfaces lead to bugs that compile without warnings and
blow up at runtime. The cardinal rule of interface design: if a client can use your interface
incorrectly, the interface shares at least part of the blame. You should design interfaces that
**prevent** misuse rather than merely documenting correct usage.

### The Date Constructor Problem

Consider a class for representing dates:

```cpp
// BAD: Easy to misuse -- what order are the parameters?
class Date {
public:
    Date(int month, int day, int year);
    // ...
};

// Client code -- spot the bugs:
Date d1(30, 3, 1995);    // Oops: day and month swapped (should be 3, 30, 1995)
Date d2(3, 40, 1995);    // Oops: day 40 doesn't exist
Date d3(2, 30, 1995);    // Oops: Feb 30 doesn't exist

// All three compile without error. All three are wrong.
```

The problem is that `int` carries no semantic meaning. A month is not just an integer --
it is a value in the range [1, 12]. A day is not just an integer -- it is a value whose
valid range depends on the month and year. Using raw `int` for both loses this information
at the type level.

### Solution: Introduce Wrapper Types

```cpp
// GOOD: Distinct types prevent argument transposition errors
struct Day {
    explicit Day(int d) : val(d) {}
    int val;
};

struct Month {
    explicit Month(int m) : val(m) {}
    int val;
};

struct Year {
    explicit Year(int y) : val(y) {}
    int val;
};

class Date {
public:
    Date(const Month& m, const Day& d, const Year& y);
    // ...
};

// Now the compiler catches transposition errors:
Date d1(30, 3, 1995);                          // Error! Can't convert int to Month
Date d2(Day(30), Month(3), Year(1995));         // Error! Wrong argument types
Date d3(Month(3), Day(30), Year(1995));         // OK -- reads naturally
```

### Restricting the Value Space with Enums or Static Factory Methods

Even with wrapper types, `Month(13)` still compiles. We can restrict the set of valid values:

```cpp
// GOOD: Month as a class with only 12 valid values
class Month {
public:
    static Month Jan() { return Month(1); }
    static Month Feb() { return Month(2); }
    static Month Mar() { return Month(3); }
    static Month Apr() { return Month(4); }
    static Month May() { return Month(5); }
    static Month Jun() { return Month(6); }
    static Month Jul() { return Month(7); }
    static Month Aug() { return Month(8); }
    static Month Sep() { return Month(9); }
    static Month Oct() { return Month(10); }
    static Month Nov() { return Month(11); }
    static Month Dec() { return Month(12); }

    int asInt() const { return val_; }

private:
    explicit Month(int m) : val_(m) {}  // Private! Only the static methods can create Months.
    int val_;
};

// Usage is clear and impossible to misuse:
Date d(Month::Mar(), Day(30), Year(1995));

// Month(13) won't compile -- the constructor is private.
// The only way to get a Month is through the 12 named factory functions.
```

Why functions returning `Month` instead of `static const Month` objects? The latter risks the
"static initialization order fiasco" (see Item 4). Functions returning local statics avoid this.

### Restricting Operations -- Multiplication of Ints

```cpp
// BAD: if operator* returns a bare int, the user can write:
//     if (a * b = c) ...     // Assignment instead of comparison -- compiles!
//
// GOOD: return const to prevent assignment to temporaries
const Rational operator*(const Rational& lhs, const Rational& rhs);

// Now:
Rational a, b, c;
if (a * b = c) ...  // Error! Can't assign to a const Rational
```

### Consistent Interfaces -- Behave Like Built-in Types

One of the most important rules: **make your types behave consistently with built-in types.**
If users already know how `int` works, they should be able to guess how your type works.

```cpp
// BAD: inconsistent naming across container types
class Array {
public:
    int length() const;     // "length"
};

class LinkedList {
public:
    int size() const;       // "size" -- different name, same concept
};

class HashTable {
public:
    int count() const;      // "count" -- yet another name
};

// GOOD: use consistent naming (the STL does this with size())
class Array {
public:
    size_t size() const;
};

class LinkedList {
public:
    size_t size() const;
};

class HashTable {
public:
    size_t size() const;
};
```

### Eliminating Client Resource Management with Smart Pointers

One of the most impactful applications of this principle: don't force clients to manage
resources. If a factory function returns a raw pointer, the client must remember to delete
it -- and must delete it with the right mechanism.

```cpp
// BAD: raw pointer -- client must remember to delete
Investment* createInvestment();

// The client might:
// 1. Forget to delete entirely (memory leak)
// 2. Delete twice (undefined behavior)
// 3. Use delete[] instead of delete (undefined behavior)
// 4. Delete but then continue using the pointer (dangling pointer)

void f() {
    Investment* pInv = createInvestment();
    // ... code that might throw or return early ...
    delete pInv;  // Might never execute!
}
```

```cpp
// GOOD: return a smart pointer -- resource management is automatic
std::shared_ptr<Investment> createInvestment() {
    // The deleter can be baked in at creation time
    std::shared_ptr<Investment> retVal(new Stock(...),
                                       getRidOfInvestment);  // Custom deleter!
    return retVal;
}

void f() {
    std::shared_ptr<Investment> pInv = createInvestment();
    // ... use pInv ...
    // No delete needed. Automatic cleanup, even if exceptions are thrown.
    // Even the custom deleter is handled automatically.
}
```

This is especially powerful because the **custom deleter is embedded in the smart pointer
at creation time**. The client doesn't need to know or care what cleanup mechanism is needed.
The factory function's author -- who knows how the resource was allocated -- bakes in the
correct cleanup strategy.

### Cross-DLL Resource Management

A particularly nasty bug: an object allocated with `new` in one DLL but `delete`d in another.
On many platforms this causes undefined behavior because each DLL may have its own heap.
`std::shared_ptr` solves this: the deleter is captured at construction time, so `delete` is
always called in the same DLL that called `new`.

```cpp
// GOOD: shared_ptr ensures delete is called in the right DLL
std::shared_ptr<Investment> createInvestment() {
    // 'new' happens in this DLL
    // The default deleter (which calls 'delete') is bound here
    return std::shared_ptr<Investment>(new Stock(...));
    // Even if the shared_ptr crosses DLL boundaries,
    // delete will be called using this DLL's delete operator.
}
```

### Real-World Example: Database Connection Handle

```cpp
// BAD: raw handle -- client must remember to close
class DatabaseConnection {
public:
    static DBHandle open(const std::string& connStr);
    // Client must call close(handle) when done. Will they?
};

// GOOD: RAII wrapper with interface that prevents misuse
class DatabaseConnection {
public:
    // Factory returns a managed connection
    static std::shared_ptr<DatabaseConnection> open(const std::string& connStr) {
        auto conn = std::shared_ptr<DatabaseConnection>(
            new DatabaseConnection(connStr),
            [](DatabaseConnection* c) {
                c->close();     // Guaranteed cleanup
                delete c;
            }
        );
        return conn;
    }

    void executeQuery(const std::string& sql);

private:
    DatabaseConnection(const std::string& connStr);  // Private -- must use open()
    void close();                                      // Private -- handled by deleter
};

// Client code is clean and safe:
void processData() {
    auto conn = DatabaseConnection::open("host=localhost;db=mydb");
    conn->executeQuery("SELECT * FROM users");
    // Connection is automatically closed when conn goes out of scope.
    // No possibility of forgetting to close.
}
```

### Things to Remember

- Good interfaces are easy to use correctly and hard to use incorrectly. You should strive
  for these characteristics in all your interfaces.
- Ways to facilitate correct use include consistency in interfaces and behavioral
  compatibility with built-in types.
- Ways to prevent errors include creating new types, restricting operations on types,
  constraining object values, and eliminating client resource management responsibilities.
- `std::shared_ptr` supports custom deleters. This prevents the cross-DLL problem, can
  be used to automatically unlock mutexes (see Item 14), and more.

---

## Item 19: Treat Class Design as Type Design

In C++, defining a new class defines a new type. You are not just a class designer -- you
are a **type designer**. Overloaded functions and operators, controlling memory allocation and
deallocation, defining object initialization and finalization -- it's all in your hands. You
should approach class design with the same care that language designers lavish on the design
of built-in types.

Designing good classes is challenging because designing good types is challenging. Good types
have natural syntax, intuitive semantics, and one or more efficient implementations. Here
are the questions you should consider every time you design a class:

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

## Item 20: Prefer Pass-by-Reference-to-const to Pass-by-Value

By default, C++ passes objects to and from functions by value (a trait inherited from C).
Unless you tell it otherwise, function parameters are initialized with **copies** of the
actual arguments, and function callers get back a **copy** of the value returned by the
function. These copies are produced by the objects' copy constructors. This can make
pass-by-value an expensive operation.

### The Cost of Pass-by-Value

```cpp
class Person {
public:
    Person();
    virtual ~Person();

private:
    std::string name;
    std::string address;
};

class Student : public Person {
public:
    Student();
    ~Student();

private:
    std::string schoolName;
    std::string schoolAddress;
};
```

Now consider this function:

```cpp
// BAD: pass by value -- expensive!
bool validateStudent(Student s);

Student plato;
bool platoIsOK = validateStudent(plato);
```

What happens when `validateStudent` is called? The parameter `s` is initialized by calling
the `Student` copy constructor with `plato` as the argument. Similarly, `s` is destroyed when
`validateStudent` returns. The cost of passing by value:

1. One call to the `Student` copy constructor
2. One call to the `Student` destructor
3. But `Student` contains two `std::string` objects, so that's two more copy constructions
   and two more destructions
4. `Student` derives from `Person`, which also has two `std::string` objects -- two more
   copy constructions, two more destructions
5. Plus the `Person` copy construction and destruction

**Total: 6 constructors and 6 destructors** just to pass a single parameter.

```cpp
// GOOD: pass by reference-to-const -- no copies at all
bool validateStudent(const Student& s);

// Same calling syntax, but no constructors or destructors are invoked.
// The const guarantees that validateStudent won't modify the caller's Student.
```

### The Slicing Problem

Pass-by-value doesn't just hurt performance -- it causes a subtle and dangerous bug called
the **slicing problem**. When a derived class object is passed by value to a function
expecting a base class object, the derived class's data members and virtual function
implementations are "sliced off."

```cpp
class Window {
public:
    std::string name() const;
    virtual void display() const;  // Base class version
};

class WindowWithScrollBars : public Window {
public:
    virtual void display() const;  // Overridden version -- draws scroll bars
};
```

Now consider a function that prints window information:

```cpp
// BAD: pass by value -- causes slicing!
void printNameAndDisplay(Window w) {
    std::cout << w.name();
    w.display();  // ALWAYS calls Window::display, never WindowWithScrollBars::display!
}

WindowWithScrollBars wwsb;
printNameAndDisplay(wwsb);
// wwsb is SLICED: it becomes a plain Window inside the function.
// The WindowWithScrollBars-specific data is chopped off.
// Virtual dispatch is broken -- display() calls the base class version.
```

The parameter `w` is constructed as a `Window` object (it's passed by value, and the
parameter type is `Window`). All the specialization that makes `wwsb` a `WindowWithScrollBars`
is sliced off. Inside `printNameAndDisplay`, `w` always behaves like a `Window`, regardless
of the type of the object actually passed. In particular, `w.display()` calls `Window::display`,
not `WindowWithScrollBars::display`.

```cpp
// GOOD: pass by reference-to-const -- preserves polymorphic behavior
void printNameAndDisplay(const Window& w) {
    std::cout << w.name();
    w.display();  // Calls the correct version via virtual dispatch!
}

WindowWithScrollBars wwsb;
printNameAndDisplay(wwsb);
// No slicing. w refers to the original wwsb object.
// w.display() correctly calls WindowWithScrollBars::display.
```

### A More Dramatic Slicing Example

```cpp
class Shape {
public:
    virtual ~Shape() {}
    virtual double area() const = 0;
    virtual std::string description() const { return "Shape"; }
};

class Circle : public Shape {
    double radius_;
public:
    explicit Circle(double r) : radius_(r) {}
    double area() const override { return 3.14159 * radius_ * radius_; }
    std::string description() const override {
        return "Circle(r=" + std::to_string(radius_) + ")";
    }
};

class Rectangle : public Shape {
    double width_, height_;
public:
    Rectangle(double w, double h) : width_(w), height_(h) {}
    double area() const override { return width_ * height_; }
    std::string description() const override {
        return "Rectangle(" + std::to_string(width_) + "x" + std::to_string(height_) + ")";
    }
};

// BAD: Taking a vector of Shapes by value is impossible (Shape is abstract),
// but even if it weren't, it would slice all derived objects.

// BAD: Taking Shape by value in a utility function
// void logShape(Shape s);  // Won't even compile -- Shape is abstract!

// GOOD: Take by reference-to-const
void logShape(const Shape& s) {
    std::cout << s.description() << " has area " << s.area() << "\n";
}

Circle c(5.0);
Rectangle r(3.0, 4.0);
logShape(c);  // "Circle(r=5.000000) has area 78.539750"
logShape(r);  // "Rectangle(3.000000x4.000000) has area 12.000000"
```

### When Pass-by-Value Is Acceptable

References are typically implemented as pointers under the hood. For **small, built-in types**
and **STL iterators and function objects**, pass-by-value is often more efficient:

```cpp
// These are fine to pass by value:
void f(int x);              // Built-in type -- cheaper to copy than to indirect
void f(double x);           // Built-in type
void f(char c);             // Built-in type

// STL iterators are designed to be passed by value:
void processRange(std::vector<int>::iterator begin,
                  std::vector<int>::iterator end);

// STL function objects are designed to be passed by value:
void sortWithComparator(std::vector<int>& v, std::less<int> comp);
```

**But be careful.** Just because a type is small does not mean pass-by-value is cheap.
A class with a single `std::string*` is only the size of a pointer, but copying it might
trigger a deep copy if the class's copy constructor does so. Furthermore, just because a
class is small today does not mean it will be small tomorrow -- the implementation may grow.

```cpp
// DANGEROUS ASSUMPTION: "It's small, so pass by value is fine"
class SmallButExpensive {
    std::shared_ptr<HugeDataStructure> data_;
    // Only 8 bytes (one pointer)!
    // But copying increments a reference count (atomic operation)
    // and may involve other bookkeeping.
public:
    SmallButExpensive(const SmallButExpensive&);  // Might be more expensive than you think
};

// Safe default: pass by reference-to-const
void process(const SmallButExpensive& obj);  // No copies, no surprises
```

### The General Rule

```cpp
// For user-defined types, the safe default is always reference-to-const:
void doWork(const MyClass& obj);

// Only pass by value when ALL of these are true:
// 1. The type is a built-in type (int, double, char, pointers), OR
// 2. The type is an STL iterator or function object, OR
// 3. The type is specifically designed to be passed by value and you've measured
//    that pass-by-value is actually more efficient.
```

### Things to Remember

- Prefer pass-by-reference-to-const over pass-by-value. It's typically more efficient
  and it avoids the slicing problem.
- The rule doesn't apply to built-in types and STL iterator and function object types.
  For them, pass-by-value is usually appropriate.

---

## Item 21: Don't Try to Return a Reference When You Must Return an Object

Once programmers learn about the efficiency costs of pass-by-value (Item 20), they sometimes
become crusaders, determined to eliminate all pass-by-value from their code -- including in
contexts where returning by reference leads to disaster. The result: returning references to
objects that no longer exist.

The key insight: **a reference is just a name for an existing object.** Whenever you see a
reference, you should ask yourself what object it is another name for. If there is no such
object, the reference is dangling and the program has undefined behavior.

### The Rational Number Example

```cpp
class Rational {
public:
    Rational(int numerator = 0, int denominator = 1);

private:
    int n, d;  // numerator and denominator

    friend const Rational operator*(const Rational& lhs, const Rational& rhs);
};
```

The natural implementation of `operator*` would return a new `Rational`. But a performance-
obsessed programmer might try to avoid the copy by returning a reference:

```cpp
// BAD Attempt #1: Return a reference to a local stack object
const Rational& operator*(const Rational& lhs, const Rational& rhs) {
    Rational result(lhs.n * rhs.n, lhs.d * rhs.d);
    return result;  // DISASTER! result is destroyed when the function exits.
                     // The caller receives a dangling reference.
}

// Any use of the returned reference is undefined behavior:
Rational a(1, 2);
Rational b(3, 5);
Rational c = a * b;  // c is initialized from a reference to a destroyed object.
                       // Might appear to work, might crash, might corrupt memory.
```

```cpp
// BAD Attempt #2: Return a reference to a heap-allocated object
const Rational& operator*(const Rational& lhs, const Rational& rhs) {
    Rational* result = new Rational(lhs.n * rhs.n, lhs.d * rhs.d);
    return *result;  // Who deletes this? The caller? How?
}

// Memory leak -- the caller has no way to delete the object:
Rational w, x, y, z;
w = x * y * z;  // This calls operator* twice:
                  // temp = operator*(x, y)    -- allocates on heap (leak #1)
                  // w = operator*(temp, z)    -- allocates on heap (leak #2)
                  // We have a reference to the second result (assigned to w),
                  // but the first result is leaked forever.
                  // There is no way to retrieve a pointer to it.
```

```cpp
// BAD Attempt #3: Return a reference to a local static object
const Rational& operator*(const Rational& lhs, const Rational& rhs) {
    static Rational result;  // Only one instance, shared across all calls!
    result = Rational(lhs.n * rhs.n, lhs.d * rhs.d);
    return result;
}

// This is broken in a subtle way:
Rational a(1, 2);
Rational b(3, 4);
Rational c(5, 6);
Rational d(7, 8);

if ((a * b) == (c * d)) {
    // This is ALWAYS true!
    // Both calls to operator* modify the SAME static object.
    // By the time == is evaluated, both references point to the same object
    // (which holds the value from the most recent call, c * d).
    // So the comparison is: static_result == static_result
    // which is always true.
    std::cout << "This always prints!\n";
} else {
    std::cout << "This never prints!\n";
}
```

Even an array of statics wouldn't fix the problem -- you'd need to know how many simultaneous
results might be needed, and the comparison issue remains.

### The Correct Solution: Return by Value

```cpp
// GOOD: Just return a new object by value
const Rational operator*(const Rational& lhs, const Rational& rhs) {
    return Rational(lhs.n * rhs.n, lhs.d * rhs.d);
}
```

Yes, this incurs the cost of constructing and destroying the return value. But that cost is
**correct** -- you are paying for the creation of a new object, which is exactly what you need.
Moreover, compilers are allowed to (and routinely do) apply **Return Value Optimization (RVO)
and Named Return Value Optimization (NRVO)**, which eliminate the copy entirely by
constructing the result directly in the caller's memory.

```cpp
// With RVO, this code:
Rational c = a * b;

// is optimized to construct the result directly in c's memory.
// No copy constructor is called. The cost is just one constructor call.
```

In C++11 and later, move semantics provide an additional optimization: even when RVO doesn't
apply, the return value is **moved** rather than copied.

### Real-World Example: String Concatenation

```cpp
// BAD: trying to avoid copies leads to bugs
class MyString {
public:
    // Don't do this!
    const MyString& operator+(const MyString& rhs) const {
        // Where does the result live? Can't be on the stack (dangling).
        // Can't be on the heap (leak). Can't be static (shared state).
        // There is no good answer.
    }
};

// GOOD: return by value
class MyString {
public:
    MyString operator+(const MyString& rhs) const {
        MyString result;
        result.data_ = data_ + rhs.data_;
        return result;  // RVO will likely eliminate the copy.
    }

private:
    std::string data_;
};
```

### When References ARE Appropriate to Return

References are appropriate when the object already exists and will outlive the reference:

```cpp
class Container {
public:
    // GOOD: the element exists in the container and will outlive the call
    int& operator[](size_t index) { return data_[index]; }
    const int& operator[](size_t index) const { return data_[index]; }

    // GOOD: returning *this for chaining
    Container& add(int value) {
        data_.push_back(value);
        return *this;
    }

private:
    std::vector<int> data_;
};

// GOOD: singleton pattern -- the object is static and lives forever
DatabaseManager& DatabaseManager::instance() {
    static DatabaseManager mgr;
    return mgr;
}
```

### Things to Remember

- Never return a pointer or reference to a local stack object, a reference to a heap-
  allocated object, or a pointer or reference to a local static object if there is a
  chance that more than one such object will be needed. (Item 4 provides an example
  of a design where returning a reference to a local static is reasonable: the singleton
  pattern for avoiding the static initialization order problem.)

---

## Item 22: Declare Data Members Private

This item is about encapsulation. It argues that data members should **always** be `private`.
The reasoning is based on access control, flexibility, and a fundamental truth about
software evolution: implementations change, but interfaces should be stable.

### Why Not Public?

**Reason 1: Syntactic consistency.** If data members aren't public, the only way for clients
to access an object is via member functions. The client never has to wonder whether to use
parentheses or not -- it's always parentheses.

```cpp
// BAD: public data members lead to inconsistent access syntax
class SpreadsheetCell {
public:
    double value;           // Accessed as: cell.value
    double cachedValue();   // Accessed as: cell.cachedValue()
    // Client must remember: is it 'value' or 'value()'?
};

// GOOD: all access through functions -- consistent syntax
class SpreadsheetCell {
public:
    double value() const;       // Always use ()
    double cachedValue() const; // Always use ()
private:
    double value_;
    mutable double cachedValue_;
    mutable bool cacheValid_;
};
```

**Reason 2: Fine-grained access control.** With member functions, you can implement
no access, read-only access, write-only access, or read-write access. Public data
members give you only read-write -- all or nothing.

```cpp
class AccessControlled {
public:
    // Read-only: temperature can be read but not set externally
    double temperature() const { return temperature_; }

    // Write-only: password can be set but never read back
    void setPassword(const std::string& pwd) { passwordHash_ = hash(pwd); }

    // Read-write: name can be read and written
    std::string name() const { return name_; }
    void setName(const std::string& n) { name_ = n; }

    // No access: internalState is completely hidden
    // (no getter or setter provided)

private:
    double temperature_;
    size_t passwordHash_;
    std::string name_;
    int internalState_;
};
```

**Reason 3: Encapsulation -- the ability to change the implementation.**

If data members are public, changing them breaks all client code that uses them. If data
members are private and accessed through functions, you can change the internal representation
without changing the interface.

```cpp
// Version 1: SpeedOMeter stores speed as mph
class SpeedOMeter {
public:
    double speedInMph() const { return speed_; }
    double speedInKph() const { return speed_ * 1.60934; }
    void setSpeed(double mph) { speed_ = mph; }

private:
    double speed_;  // stored in mph
};

// Version 2: Decision to store in kph instead (internal change)
// Client code doesn't change AT ALL
class SpeedOMeter {
public:
    double speedInMph() const { return speed_ / 1.60934; }  // Compute from kph
    double speedInKph() const { return speed_; }             // Direct return
    void setSpeed(double mph) { speed_ = mph * 1.60934; }   // Convert to kph

private:
    double speed_;  // now stored in kph -- internal change only
};
```

### Encapsulation and Breakage: The Quantitative Argument

The encapsulation of a data member is inversely proportional to the amount of code that
might be broken if that data member changes. If a data member is `public`, the amount of
code that could be affected is **all client code** -- an unknowably large amount. If it's
`private`, the amount of code that could be affected is limited to the **member functions
and friends** of the class.

```cpp
// If x is public:
class Point {
public:
    double x, y;  // Every piece of code that uses Point::x is coupled
                    // to the fact that x is a double data member.
                    // Changing it breaks an unknowable number of clients.
};

// If x is private with accessor:
class Point {
public:
    double x() const { return x_; }
    double y() const { return y_; }
    void setX(double newX) { x_ = newX; }
    void setY(double newY) { y_ = newY; }

private:
    double x_, y_;
    // Can later change to:
    //   double r_, theta_;  (polar coordinates)
    // without changing the public interface.
};
```

### Why Not Protected?

The same arguments apply to `protected` data members. Protected is not much more encapsulated
than public.

```cpp
// BAD: Protected data members are almost as bad as public
class Base {
protected:
    int protectedData;  // All derived classes can access this directly.
                         // Changing or removing it breaks all derived classes.
};

class Derived1 : public Base {
    void f() { protectedData = 42; }  // Direct access
};

class Derived2 : public Base {
    void g() { int x = protectedData; }  // Direct access
};

// If we need to change protectedData (rename it, change its type, compute it
// on the fly instead of storing it), ALL derived classes break.
// In a class hierarchy with many derived classes, this can be catastrophic.
```

```cpp
// GOOD: Private data with protected accessor
class Base {
public:
    int getData() const { return data_; }

protected:
    void setData(int d) { data_ = d; }  // Only derived classes can set

private:
    int data_;
    // Can change implementation without breaking derived classes,
    // as long as getData() and setData() maintain their contracts.
};
```

### Real-World Example: Validating Invariants

```cpp
// BAD: Public members can't enforce invariants
class Rectangle {
public:
    double width, height;
    // Nothing stops a client from writing:
    //   rect.width = -5;   // Negative width?!
};

// GOOD: Private members with validation
class Rectangle {
public:
    double width() const { return width_; }
    double height() const { return height_; }

    void setWidth(double w) {
        if (w <= 0) throw std::invalid_argument("Width must be positive");
        width_ = w;
        updateCachedArea();
    }

    void setHeight(double h) {
        if (h <= 0) throw std::invalid_argument("Height must be positive");
        height_ = h;
        updateCachedArea();
    }

    double area() const { return cachedArea_; }  // O(1) lookup

private:
    double width_;
    double height_;
    double cachedArea_;

    void updateCachedArea() { cachedArea_ = width_ * height_; }
};
```

### Real-World Example: Thread-Safe Access

```cpp
// BAD: Public data is impossible to make thread-safe
class Counter {
public:
    int count;  // Data races galore
};

// GOOD: Private data can be made thread-safe without changing the interface
class Counter {
public:
    int count() const {
        std::lock_guard<std::mutex> lock(mutex_);
        return count_;
    }

    void increment() {
        std::lock_guard<std::mutex> lock(mutex_);
        ++count_;
    }

private:
    mutable std::mutex mutex_;
    int count_ = 0;
};
// Clients never know (or need to know) about the locking.
// Thread safety is an implementation detail hidden behind the interface.
```

### Things to Remember

- Declare data members `private`. It gives clients syntactically uniform access to data,
  affords fine-grained access control, allows invariants to be enforced, and offers class
  authors implementation flexibility.
- `protected` is no more encapsulated than `public`.

---

## Item 23: Prefer Non-Member Non-Friend Functions to Member Functions

This item contains one of the most counterintuitive pieces of advice in the book. Many
programmers believe that putting a function inside a class (making it a member) increases
encapsulation because the function "belongs" to the class. In fact, the opposite is true:
in many cases, a **non-member non-friend function** provides **more** encapsulation, **more**
packaging flexibility, and **more** functional extensibility.

### The Web Browser Example

```cpp
class WebBrowser {
public:
    void clearCache();
    void clearHistory();
    void removeCookies();

    // Should clearEverything() be a member function?
    void clearEverything();   // Calls clearCache, clearHistory, removeCookies
};
```

```cpp
// Attempt 1 (member function):
void WebBrowser::clearEverything() {
    clearCache();
    clearHistory();
    removeCookies();
}

// Attempt 2 (non-member non-friend function):
void clearBrowser(WebBrowser& wb) {
    wb.clearCache();
    wb.clearHistory();
    wb.removeCookies();
}
```

Which is better? The non-member non-friend function. Here's why.

### The Encapsulation Argument

Encapsulation means that something is hidden from view. The more things are hidden, the
greater the flexibility to change them. The more things that are encapsulated, the greater
our ability to change them without affecting other code.

The number of functions that can access the private members of a class is a measure of
how **un-encapsulated** those members are. The more functions that can access private data,
the less encapsulated that data is.

- A **member function** can access all private members.
- A **non-member non-friend function** cannot access any private members.

Therefore, choosing a non-member non-friend function over a member function **increases
encapsulation** (all else being equal). The non-member function `clearBrowser` can only
call public functions on `WebBrowser`. It adds no new access to private data.

Note: this reasoning only applies when you're choosing between a member function and a
non-member **non-friend** function. Friends have the same access as members, so choosing
a friend over a member doesn't improve encapsulation.

### Namespace-Based Organization

The natural home for non-member functions associated with a class is the **same namespace**
as the class. This is the C++ way of saying "these functions are related to this class"
without granting them private access.

```cpp
// WebBrowser.h
namespace WebBrowserStuff {

class WebBrowser {
public:
    void clearCache();
    void clearHistory();
    void removeCookies();
    // ...
};

// Convenience function in the same namespace
void clearBrowser(WebBrowser& wb);

}  // namespace WebBrowserStuff
```

### Splitting Functionality Across Headers

Unlike classes, namespaces can be split across multiple header files. This is enormously
useful for managing large interfaces. The standard library does exactly this: `std::vector`
is in `<vector>`, `std::sort` is in `<algorithm>`, etc. -- all in namespace `std`, but
spread across many headers.

```cpp
// webbrowser.h -- core WebBrowser class
namespace WebBrowserStuff {

class WebBrowser { /* ... */ };

// Core non-member functions that nearly everyone needs
void clearBrowser(WebBrowser& wb);

}  // namespace WebBrowserStuff


// webbrowserbookmarks.h -- bookmark-related convenience functions
namespace WebBrowserStuff {

void addBookmark(WebBrowser& wb, const std::string& url);
void removeBookmark(WebBrowser& wb, const std::string& url);
std::vector<std::string> getBookmarks(const WebBrowser& wb);

}  // namespace WebBrowserStuff


// webbrowsercookies.h -- cookie-related convenience functions
namespace WebBrowserStuff {

void importCookies(WebBrowser& wb, const std::string& file);
void exportCookies(const WebBrowser& wb, const std::string& file);
Cookie getCookie(const WebBrowser& wb, const std::string& domain);

}  // namespace WebBrowserStuff
```

Clients include only the headers they need, reducing compilation dependencies. This is
**impossible** with member functions -- all member functions must be declared in the class
definition, which lives in a single header. A client who wants to use `addBookmark` must
include the entire class definition, including declarations for cookie-related and
cache-related functions they don't need.

### Extensibility by Clients

Because namespaces are open, clients can add their own convenience functions:

```cpp
// In the client's own header:
namespace WebBrowserStuff {

// Client-defined convenience function
void clearBrowserAndNotifyUser(WebBrowser& wb, const User& user) {
    clearBrowser(wb);
    user.notify("Browser cleared");
}

}  // namespace WebBrowserStuff
```

A client cannot add member functions to a class they don't control. But they can add
non-member functions to a namespace. This is one of the key extensibility benefits.

### When Member Functions ARE Appropriate

This item does not say "never use member functions." Member functions are appropriate
when the function:

1. Needs access to private data (and no public interface can provide that access), or
2. Is a virtual function (virtual dispatch requires membership), or
3. Is an operator that must be a member (`operator=`, `operator[]`, `operator->`, `operator()`), or
4. Affects the object's internal invariants in a way that can only be done with private access.

```cpp
class String {
public:
    // These MUST be members:
    String& operator=(const String& rhs);  // Assignment operator must be a member
    char& operator[](size_t index);        // Subscript operator must be a member
    size_t size() const;                   // Needs access to internal length_ member

    // This SHOULD be a non-member:
    // friend String operator+(const String& lhs, const String& rhs);
    // See Item 24 for why.

private:
    char* data_;
    size_t length_;
};

// Non-member convenience functions:
bool isAllUpperCase(const String& s) {
    for (size_t i = 0; i < s.size(); ++i) {
        if (!std::isupper(s[i])) return false;
    }
    return true;
}
// isAllUpperCase uses only the public interface. Making it a member would
// decrease encapsulation for no benefit.
```

### Real-World Example: Algorithm-Style Functions

```cpp
class Matrix {
public:
    size_t rows() const;
    size_t cols() const;
    double& operator()(size_t r, size_t c);
    const double& operator()(size_t r, size_t c) const;

private:
    std::vector<double> data_;
    size_t rows_, cols_;
};

// These should be non-member non-friend functions:
// They operate entirely through the public interface.

Matrix transpose(const Matrix& m) {
    Matrix result(m.cols(), m.rows());
    for (size_t r = 0; r < m.rows(); ++r)
        for (size_t c = 0; c < m.cols(); ++c)
            result(c, r) = m(r, c);
    return result;
}

Matrix multiply(const Matrix& a, const Matrix& b) {
    assert(a.cols() == b.rows());
    Matrix result(a.rows(), b.cols());
    for (size_t i = 0; i < a.rows(); ++i)
        for (size_t j = 0; j < b.cols(); ++j) {
            double sum = 0;
            for (size_t k = 0; k < a.cols(); ++k)
                sum += a(i, k) * b(k, j);
            result(i, j) = sum;
        }
    return result;
}

bool isSymmetric(const Matrix& m) {
    if (m.rows() != m.cols()) return false;
    for (size_t r = 0; r < m.rows(); ++r)
        for (size_t c = r + 1; c < m.cols(); ++c)
            if (m(r, c) != m(c, r)) return false;
    return true;
}

// None of these functions need private access.
// Making them non-member non-friend improves encapsulation.
// They can live in different headers for reduced coupling.
// Clients can add their own algorithms (e.g., determinant, inverse)
// without modifying the Matrix class.
```

### Things to Remember

- Prefer non-member non-friend functions to member functions. Doing so increases
  encapsulation, packaging flexibility, and functional extensibility.

---

## Item 24: Declare Non-Member Functions When Type Conversions Should Apply to All Parameters

This item addresses a specific but important situation: when you want implicit type
conversions to work for **all** arguments of a function, including the object on which
a member function would be called (i.e., `*this`).

### The Rational Number Multiplication Problem

```cpp
class Rational {
public:
    Rational(int numerator = 0, int denominator = 1);  // Not explicit -- allows
                                                         // implicit int-to-Rational

    int numerator() const { return n_; }
    int denominator() const { return d_; }

    // Attempt: operator* as a member function
    const Rational operator*(const Rational& rhs) const;

private:
    int n_, d_;
};
```

This seems to work:

```cpp
Rational oneHalf(1, 2);
Rational result;

result = oneHalf * 2;   // OK! Same as: oneHalf.operator*(Rational(2))
                          // The int 2 is implicitly converted to Rational(2, 1)
                          // via the non-explicit constructor.

result = 2 * oneHalf;   // ERROR! Same as: 2.operator*(oneHalf)
                          // int doesn't have an operator* that takes a Rational!
                          // The compiler also tries:
                          //   operator*(2, oneHalf)
                          // but no such non-member function exists.
```

The asymmetry is the problem. When `operator*` is a member function, the left-hand operand
must be a `Rational` (it becomes `*this`). Implicit conversions are never applied to `*this` --
only to function arguments. So `2 * oneHalf` fails because `2` is not a `Rational` and can't
be implicitly converted in the `*this` position.

### The Solution: Make operator* a Non-Member Function

```cpp
class Rational {
public:
    Rational(int numerator = 0, int denominator = 1);  // Implicit conversion allowed
    int numerator() const { return n_; }
    int denominator() const { return d_; }

    // No operator* member function!

private:
    int n_, d_;
};

// Non-member operator*
const Rational operator*(const Rational& lhs, const Rational& rhs) {
    return Rational(lhs.numerator() * rhs.numerator(),
                    lhs.denominator() * rhs.denominator());
}
```

Now both forms work:

```cpp
Rational oneHalf(1, 2);
Rational result;

result = oneHalf * 2;   // OK! operator*(oneHalf, Rational(2))
                          // 2 is implicitly converted to Rational(2, 1)

result = 2 * oneHalf;   // OK! operator*(Rational(2), oneHalf)
                          // 2 is implicitly converted to Rational(2, 1)

result = 2 * 3;          // Still uses built-in int multiplication
                          // (no Rational involved, so no conversion)
```

### Should operator* Be a Friend?

Notice that the non-member `operator*` above only uses `numerator()` and `denominator()` --
both public member functions. It doesn't need private access. Therefore, **it should not be
a friend.**

```cpp
// BAD: unnecessary friendship
class Rational {
    friend const Rational operator*(const Rational& lhs, const Rational& rhs);
    // ...
};

// This works, but the friendship is gratuitous.
// operator* can do everything it needs through the public interface.

// GOOD: non-member non-friend (as shown above)
// Maximizes encapsulation (Item 23) while supporting type conversions.
```

The takeaway from Items 23 and 24 combined: if a function doesn't need private access,
it shouldn't be a member or a friend. The only reason to make it a friend would be if
it genuinely needs access to private data.

### What About Explicit Constructors?

If the `Rational` constructor were `explicit`, implicit conversions would be disabled:

```cpp
class Rational {
public:
    explicit Rational(int numerator = 0, int denominator = 1);
    // ...
};

Rational oneHalf(1, 2);
Rational result = oneHalf * 2;  // ERROR! Can't implicitly convert 2 to Rational
Rational result = oneHalf * Rational(2);  // OK -- explicit conversion
```

Whether to use `explicit` depends on your design goals. For a numeric type like `Rational`,
implicit conversion from `int` is usually desirable (it mirrors how `int` implicitly
converts to `double`). For other types, `explicit` is usually safer.

### Real-World Example: A Vector2D Class

```cpp
class Vector2D {
public:
    Vector2D(double x = 0, double y = 0) : x_(x), y_(y) {}

    double x() const { return x_; }
    double y() const { return y_; }

    // operator+= is a member -- it modifies *this
    Vector2D& operator+=(const Vector2D& rhs) {
        x_ += rhs.x_;
        y_ += rhs.y_;
        return *this;
    }

    // operator*= (scalar) is a member -- it modifies *this
    Vector2D& operator*=(double scalar) {
        x_ *= scalar;
        y_ *= scalar;
        return *this;
    }

private:
    double x_, y_;
};

// operator+ is a non-member -- both sides should support conversion
Vector2D operator+(const Vector2D& lhs, const Vector2D& rhs) {
    return Vector2D(lhs.x() + rhs.x(), lhs.y() + rhs.y());
}

// operator* (scalar) is a non-member -- we want both:
//   vector * scalar
//   scalar * vector
Vector2D operator*(const Vector2D& v, double scalar) {
    return Vector2D(v.x() * scalar, v.y() * scalar);
}

Vector2D operator*(double scalar, const Vector2D& v) {
    return v * scalar;  // Delegate to the other overload
}

// Usage:
Vector2D v(3, 4);
Vector2D w = v * 2.0;    // OK
Vector2D x = 2.0 * v;    // OK -- would fail if operator* were a member
Vector2D y = v + w;       // OK
```

### Real-World Example: Comparison Operators

```cpp
class Temperature {
public:
    Temperature(double kelvin) : kelvin_(kelvin) {}  // Implicit -- intentional

    double kelvin() const { return kelvin_; }
    double celsius() const { return kelvin_ - 273.15; }
    double fahrenheit() const { return kelvin_ * 9.0/5.0 - 459.67; }

private:
    double kelvin_;
};

// Non-member comparisons -- both sides can undergo implicit conversion
bool operator==(const Temperature& lhs, const Temperature& rhs) {
    return lhs.kelvin() == rhs.kelvin();
}

bool operator<(const Temperature& lhs, const Temperature& rhs) {
    return lhs.kelvin() < rhs.kelvin();
}

// etc. for !=, >, <=, >=

// Usage:
Temperature boiling(373.15);

if (boiling == 373.15) { /* ... */ }  // OK: 373.15 converts to Temperature
if (373.15 == boiling) { /* ... */ }  // OK: works because operator== is non-member
// If operator== were a member function, the second form would fail.
```

### Koenig Lookup (Argument-Dependent Lookup, ADL)

When you call a non-member function, the compiler searches for the function not only in
the usual scopes but also in the **namespaces of the argument types**. This is called
Argument-Dependent Lookup (ADL), or Koenig Lookup after Andrew Koenig who proposed it.

```cpp
namespace Geometry {

class Point {
public:
    Point(double x, double y) : x_(x), y_(y) {}
    double x() const { return x_; }
    double y() const { return y_; }
private:
    double x_, y_;
};

// Non-member function in the same namespace as Point
double distance(const Point& a, const Point& b) {
    double dx = a.x() - b.x();
    double dy = a.y() - b.y();
    return std::sqrt(dx*dx + dy*dy);
}

// Non-member operator
Point operator+(const Point& a, const Point& b) {
    return Point(a.x() + b.x(), a.y() + b.y());
}

}  // namespace Geometry

// Client code -- no "using" declaration needed!
int main() {
    Geometry::Point p1(1, 2);
    Geometry::Point p2(4, 6);

    double d = distance(p1, p2);   // Found via ADL! The compiler searches
                                    // Geometry:: because p1 and p2 are in Geometry.

    Geometry::Point p3 = p1 + p2;  // Also found via ADL.
}
```

ADL is the reason why `std::cout << "hello"` works -- `operator<<` is a non-member function
in namespace `std`, and it's found via ADL because `std::cout` is in namespace `std`.

### Things to Remember

- If you need type conversions on all parameters to a function (including the one that
  would otherwise be pointed to by `this`), the function must be a non-member.

---

## Item 25: Consider Support for a Non-Throwing Swap

`swap` is one of the most important functions in C++. It is central to exception-safe
programming (see Item 29), to the copy-and-swap idiom for assignment operators, and to
guarding against self-assignment (see Item 11). This item explains how to write an
efficient, non-throwing swap for your types.

### The Default std::swap

The default `std::swap` implementation uses a temporary and three copies:

```cpp
namespace std {

template<typename T>
void swap(T& a, T& b) {
    T temp(a);   // Copy a
    a = b;       // Copy b into a
    b = temp;    // Copy temp into b
}

}  // namespace std
```

For types that are expensive to copy, this is wasteful. Many types can be swapped far
more efficiently -- for example, by just swapping internal pointers.

### The Pimpl Idiom: Where Default Swap Hurts

```cpp
// A Widget that uses the Pimpl (Pointer to Implementation) idiom
class WidgetImpl {
public:
    // ... lots of data ...
private:
    int a, b, c;
    std::vector<double> v;
    std::map<std::string, std::string> m;
    // ... potentially huge ...
};

class Widget {
public:
    Widget(const Widget& rhs);
    Widget& operator=(const Widget& rhs) {
        // Copy all of rhs's WidgetImpl data
        *pImpl = *(rhs.pImpl);
        return *this;
    }

private:
    WidgetImpl* pImpl;  // Pointer to the implementation
};
```

Swapping two `Widget` objects using the default `std::swap` copies three `Widget` objects,
which means copying three `WidgetImpl` objects -- extremely expensive. But all we really
need to do is swap the `pImpl` pointers.

### Step 1: Write a Member swap Function

```cpp
class Widget {
public:
    void swap(Widget& other) {
        using std::swap;           // Make std::swap available as a fallback
        swap(pImpl, other.pImpl);  // Just swap the pointers -- O(1)!
    }

    // ...

private:
    WidgetImpl* pImpl;
};
```

### Step 2: Specialize std::swap for Your Non-Template Class

```cpp
namespace std {

// Total specialization of std::swap for Widget
template<>
void swap<Widget>(Widget& a, Widget& b) {
    a.swap(b);  // Delegate to the member function
}

}  // namespace std
```

This is legal -- the C++ standard allows you to **totally specialize** templates in `std`
for user-defined types.

### Step 3: For Class Templates, Use a Non-Member swap in Your Namespace

If `Widget` is itself a class template, you **cannot** partially specialize `std::swap`:

```cpp
// Widget is now a template
template<typename T>
class Widget {
public:
    void swap(Widget<T>& other) {
        using std::swap;
        swap(pImpl, other.pImpl);
    }

private:
    WidgetImpl<T>* pImpl;
};

// BAD: You CANNOT partially specialize a function template!
namespace std {
template<typename T>
void swap<Widget<T>>(Widget<T>& a, Widget<T>& b) {  // ILLEGAL!
    a.swap(b);
}
}

// BAD: You could OVERLOAD std::swap, but adding new functions to std is
// undefined behavior (only specializations are allowed):
namespace std {
template<typename T>
void swap(Widget<T>& a, Widget<T>& b) {  // Technically undefined behavior!
    a.swap(b);
}
}
```

The solution: declare a non-member `swap` in **your own namespace**:

```cpp
namespace WidgetStuff {

template<typename T>
class Widget { /* ... as above ... */ };

// Non-member swap in the same namespace as Widget
template<typename T>
void swap(Widget<T>& a, Widget<T>& b) {
    a.swap(b);
}

}  // namespace WidgetStuff
```

ADL (Koenig Lookup) ensures that when client code calls `swap` on two `Widget<T>` objects,
the compiler finds `WidgetStuff::swap` because it looks in the namespace of the argument types.

### The Correct Way to Call swap

When writing generic code that uses `swap`, you need to ensure both the `std::swap` default
and any type-specific `swap` are considered:

```cpp
template<typename T>
void doSomething(T& obj1, T& obj2) {
    using std::swap;       // Make std::swap visible as a fallback
    swap(obj1, obj2);      // Let the compiler choose the best swap:
                            // 1. If there's a T-specific swap in T's namespace, ADL finds it.
                            // 2. If there's a std::swap<T> specialization, it's considered.
                            // 3. Otherwise, the default std::swap is used.
}
```

```cpp
// BAD: Qualifying the call prevents ADL from finding type-specific swap:
template<typename T>
void doSomething(T& obj1, T& obj2) {
    std::swap(obj1, obj2);  // ALWAYS uses std::swap!
                             // Will NOT find WidgetStuff::swap<Widget<T>>
                             // even though it's more efficient.
}
```

### Complete Example: Putting It All Together

```cpp
// For a non-template class:

class NetworkBuffer {
public:
    NetworkBuffer() : data_(nullptr), size_(0) {}
    NetworkBuffer(size_t size) : data_(new char[size]), size_(size) {}

    NetworkBuffer(const NetworkBuffer& rhs)
        : data_(new char[rhs.size_]), size_(rhs.size_) {
        std::memcpy(data_, rhs.data_, size_);
    }

    // Copy-and-swap idiom for exception-safe assignment
    NetworkBuffer& operator=(NetworkBuffer rhs) {  // Note: pass by value
        swap(rhs);        // Swap our guts with the copy's guts
        return *this;     // The copy's destructor cleans up our old data
    }

    ~NetworkBuffer() { delete[] data_; }

    // Member swap -- efficient, non-throwing
    void swap(NetworkBuffer& other) noexcept {
        using std::swap;
        swap(data_, other.data_);    // Swap pointers -- O(1), noexcept
        swap(size_, other.size_);    // Swap sizes -- O(1), noexcept
    }

private:
    char* data_;
    size_t size_;
};

// Non-member swap in the same namespace
void swap(NetworkBuffer& a, NetworkBuffer& b) noexcept {
    a.swap(b);
}

// Also specialize std::swap
namespace std {
template<>
void swap<NetworkBuffer>(NetworkBuffer& a, NetworkBuffer& b) noexcept {
    a.swap(b);
}
}
```

### The noexcept Guarantee

Highly efficient swaps are almost always non-throwing. This is important because:

1. The copy-and-swap idiom depends on a non-throwing swap for strong exception safety.
2. Many standard library operations (e.g., `std::sort`, `std::vector` reallocation)
   work more efficiently when swap doesn't throw.

```cpp
class Widget {
public:
    // The member swap should be noexcept
    void swap(Widget& other) noexcept {
        using std::swap;
        swap(pImpl, other.pImpl);  // Pointer swap never throws
    }
};

// Built-in types (pointers, ints, etc.) can always be swapped without throwing.
// If your class's swap only swaps built-in types (like pointers), it should be noexcept.
```

### Summary of the swap Protocol

| Scenario | What to do |
|----------|------------|
| Non-template class | 1. Write a public `swap` member function (noexcept). <br> 2. Write a non-member `swap` in your namespace that calls the member. <br> 3. Specialize `std::swap` to call the member. |
| Class template | 1. Write a public `swap` member function (noexcept). <br> 2. Write a non-member `swap` in your namespace that calls the member. <br> 3. Do NOT partially specialize or overload `std::swap`. |
| Calling swap in generic code | Always do `using std::swap;` followed by an unqualified call to `swap`. |

### Things to Remember

- Provide a `swap` member function when `std::swap` would be inefficient for your type.
  Make sure your `swap` doesn't throw exceptions.
- If you offer a member `swap`, also offer a non-member `swap` that calls the member.
  For classes (not templates), specialize `std::swap`, too.
- When calling `swap`, employ a `using` declaration for `std::swap`, then call `swap`
  without namespace qualification.
- It's fine to totally specialize `std` templates for user-defined types, but never try
  to add something completely new to `std`.

---

## Item 26: Postpone Variable Definitions as Long as Possible

Whenever you define a variable of a type with a constructor and destructor, you incur
the cost of construction when control reaches the variable's definition, and the cost
of destruction when the variable leaves scope. This cost is wasted if the variable is
never used -- and that happens more often than you might think.

### The Obvious Case: Variables Before Early Returns

```cpp
// BAD: encrypted is constructed even if the password is too short
std::string encryptPassword(const std::string& password) {
    using namespace std;
    string encrypted;  // Constructed here -- default constructor

    if (password.length() < MinimumPasswordLength) {
        throw logic_error("Password is too short");
        // If we throw, 'encrypted' was constructed and destroyed for nothing.
    }

    encrypted = password;  // Assignment operator (second cost!)
    encrypt(encrypted);
    return encrypted;
}
```

```cpp
// BETTER: postpone until after the check
std::string encryptPassword(const std::string& password) {
    using namespace std;

    if (password.length() < MinimumPasswordLength) {
        throw logic_error("Password is too short");
    }

    string encrypted;      // Not constructed if we threw above
    encrypted = password;  // But still: default construction + assignment
    encrypt(encrypted);
    return encrypted;
}
```

```cpp
// BEST: postpone AND initialize directly -- skip the default construction
std::string encryptPassword(const std::string& password) {
    using namespace std;

    if (password.length() < MinimumPasswordLength) {
        throw logic_error("Password is too short");
    }

    string encrypted(password);  // Copy constructor -- one operation instead of two!
    encrypt(encrypted);
    return encrypted;
}
```

The final version avoids both the unnecessary default construction and the assignment.
It directly initializes `encrypted` with `password` using the copy constructor.

### The General Rule

You should postpone a variable's definition until:
1. You can give it an initial value, AND
2. You're certain the variable will actually be used.

```cpp
// BAD: defining variables long before they're needed
void processData(const std::vector<int>& data) {
    int sum = 0;             // Defined here...
    double average = 0.0;    // ...and here...
    std::string report;      // ...and here...

    if (data.empty()) {
        return;  // sum, average, and report were never used!
    }

    // ... 50 lines of validation code ...

    for (int x : data) {
        sum += x;            // First use of sum -- 60 lines after definition!
    }
    average = static_cast<double>(sum) / data.size();  // First use of average
    report = generateReport(average);                   // First use of report
}

// GOOD: define each variable at the point of first use
void processData(const std::vector<int>& data) {
    if (data.empty()) {
        return;
    }

    // ... 50 lines of validation code ...

    int sum = 0;               // Right where it's needed
    for (int x : data) {
        sum += x;
    }

    double average = static_cast<double>(sum) / data.size();  // Right here
    std::string report = generateReport(average);              // Right here
}
```

### Variables in Loops

What about variables used only inside a loop? There are two approaches:

```cpp
// Approach A: Define outside the loop
Widget w;
for (int i = 0; i < n; ++i) {
    w = some_value_dependent_on_i;
    // ... use w ...
}
// Cost: 1 constructor + 1 destructor + n assignments

// Approach B: Define inside the loop
for (int i = 0; i < n; ++i) {
    Widget w(some_value_dependent_on_i);
    // ... use w ...
}
// Cost: n constructors + n destructors
```

The costs are:

| Approach | Cost |
|----------|------|
| A (outside) | 1 construction + 1 destruction + n assignments |
| B (inside) | n constructions + n destructions |

Approach A is more efficient **if** an assignment is cheaper than a constructor-destructor pair.
Otherwise, Approach B is better.

**The recommendation: default to Approach B** (define inside the loop) unless:
1. You know that the assignment is significantly cheaper than a construction-destruction pair, **AND**
2. You are dealing with a performance-sensitive part of your code.

Approach B is preferred because:
- It limits the variable's scope to the loop body (better readability, fewer bugs).
- The variable can't be accidentally used after the loop.
- It's easier to reason about correctness.

```cpp
// GOOD (default choice): define inside the loop
for (int i = 0; i < n; ++i) {
    std::string s = computeString(i);  // Fresh string each iteration
    processString(s);
    // s is destroyed here -- can't leak into the next iteration or beyond the loop
}

// ACCEPTABLE (performance-critical path with expensive construction):
std::string s;
for (int i = 0; i < n; ++i) {
    s = computeString(i);  // Reuse s's memory allocation
    processString(s);
}
// But now s is visible after the loop -- wider scope, more potential for bugs.
```

### Real-World Example: Database Query Processing

```cpp
// BAD: premature definitions
void processQuery(Database& db, const std::string& queryStr) {
    Connection conn = db.getConnection();        // Expensive! Opens a connection.
    PreparedStatement stmt = conn.prepare(queryStr); // Expensive! Parses SQL.
    ResultSet results;                             // Default-constructed.

    if (!db.isAvailable()) {
        throw DatabaseException("Database unavailable");
        // conn, stmt, and results were all constructed for nothing!
        // The connection was opened and must now be closed in the destructor.
    }

    if (!isValidQuery(queryStr)) {
        throw QueryException("Invalid query");
        // conn was opened for nothing!
    }

    results = stmt.execute();  // Assignment, not initialization
    processResults(results);
}

// GOOD: postpone everything
void processQuery(Database& db, const std::string& queryStr) {
    if (!db.isAvailable()) {
        throw DatabaseException("Database unavailable");
        // No resources acquired yet
    }

    if (!isValidQuery(queryStr)) {
        throw QueryException("Invalid query");
        // Still no resources acquired
    }

    Connection conn = db.getConnection();              // NOW open the connection
    PreparedStatement stmt = conn.prepare(queryStr);   // NOW parse the SQL
    ResultSet results = stmt.execute();                 // Direct initialization!
    processResults(results);
}
```

### Real-World Example: File Processing with Multiple Error Paths

```cpp
// BAD: all variables at the top
bool convertFile(const std::string& inputPath, const std::string& outputPath) {
    std::ifstream input;
    std::ofstream output;
    std::string line;
    std::vector<std::string> processedLines;
    size_t lineCount = 0;
    bool success = false;

    input.open(inputPath);
    if (!input.is_open()) return false;

    output.open(outputPath);
    if (!output.is_open()) return false;  // input constructed, output default-constructed
                                           // then opened -- wasteful

    while (std::getline(input, line)) {
        processedLines.push_back(transformLine(line));
        ++lineCount;
    }

    for (const auto& pl : processedLines) {
        output << pl << "\n";
    }

    success = true;
    return success;
}

// GOOD: each variable defined at the point of first use
bool convertFile(const std::string& inputPath, const std::string& outputPath) {
    std::ifstream input(inputPath);         // Open immediately via constructor
    if (!input.is_open()) return false;

    std::ofstream output(outputPath);       // Only open if input succeeded
    if (!output.is_open()) return false;

    std::vector<std::string> processedLines;
    std::string line;
    while (std::getline(input, line)) {     // 'line' reused in the loop (Approach A)
        processedLines.push_back(transformLine(line));
    }

    for (const auto& pl : processedLines) {
        output << pl << "\n";
    }

    return true;                            // No need for a 'success' variable
}
```

### The Relationship to const

Postponing definitions also enables more uses of `const`:

```cpp
// BAD: can't make x const because it's defined before the value is known
int x;
// ... lots of code ...
x = computeValue();
// x is non-const even though it never changes after this point.

// GOOD: define at the point of initialization -- now it can be const
// ... lots of code ...
const int x = computeValue();
// x is const, which communicates intent and enables optimizations.
```

### Things to Remember

- Postpone variable definitions as long as possible. It increases program clarity and
  improves program efficiency.

---

## Summary

Chapter 4 covers the core design decisions in C++ software:

| Item | Key Principle |
|------|--------------|
| 18 | Design interfaces that are easy to use correctly and hard to misuse |
| 19 | Treat class design as type design -- ask the right questions |
| 20 | Pass by reference-to-const by default; avoid the slicing problem |
| 21 | Return objects by value when you must; don't return dangling references |
| 22 | Make data members private for encapsulation and flexibility |
| 23 | Prefer non-member non-friend functions for better encapsulation |
| 24 | Use non-member functions when type conversions should apply to all parameters |
| 25 | Implement efficient, non-throwing swap for your types |
| 26 | Define variables at the latest possible point, initialized with their real values |

These principles work together: good type design (Item 19) leads to interfaces that are
hard to misuse (Item 18), with private data members (Item 22) accessed through well-designed
functions that are members only when necessary (Items 23, 24), passed by reference (Item 20),
returned by value when needed (Item 21), with efficient swap support (Item 25) and minimal
variable lifetimes (Item 26).
