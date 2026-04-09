# Item 18: Make Interfaces Easy to Use Correctly and Hard to Use Incorrectly

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
