# Chapter 1: Accustoming Yourself to C++

> Items 1–4: The philosophical and practical foundation for effective C++ programming.

---

## Item 1: View C++ as a Federation of Languages

### Core Concept

C++ is not a single unified language — it is a **federation of four sub-languages**, each with its own 
conventions, idioms, and best practices. The rules for effective programming change depending on which 
sub-language you're working in.

### The Four Sub-Languages

#### 1. C — The Foundation
```cpp
// C-style programming: blocks, statements, preprocessor, built-in types,
// arrays, pointers, pass-by-value
void process_data(int* array, int size) {
  for (int i = 0; i < size; ++i) {
    array[i] *= 2;  // Direct pointer/array manipulation
  }
}

// Preprocessor macros (C heritage)
#define MAX(a, b) ((a) > (b) ? (a) : (b))
// Pitfall: macro arguments evaluated multiple times
int x = 5, y = 3;
int result = MAX(++x, y);  // x incremented TWICE! Undefined behavior territory
```

#### 2. Object-Oriented C++
```cpp
// Classes, encapsulation, inheritance, polymorphism, virtual functions
class Shape {
public:
  virtual ~Shape() = default;
  virtual double area() const = 0;
  virtual void draw() const = 0;

protected:
  std::string color_;
};

class Circle : public Shape {
public:
  explicit Circle(double radius) : radius_(radius) {}

  double area() const override {
    return M_PI * radius_ * radius_;
  }

  void draw() const override {
    std::cout << "Drawing circle with radius " << radius_ << "\n";
  }

private:
  double radius_;
};

// Polymorphic usage
void render(const Shape& shape) {
  shape.draw();  // Virtual dispatch — runtime polymorphism
  std::cout << "Area: " << shape.area() << "\n";
}
```

#### 3. Template C++
```cpp
// Generic programming and template metaprogramming
template<typename T>
class Stack {
public:
  void push(const T& value) {
    data_.push_back(value);
  }

  T pop() {
    if (data_.empty()) throw std::runtime_error("Stack empty");
    T top = data_.back();
    data_.pop_back();
    return top;
  }

  bool empty() const { return data_.empty(); }

private:
  std::vector<T> data_;
};

// Template metaprogramming — compile-time computation
template<unsigned N>
struct Factorial {
  static constexpr unsigned value = N * Factorial<N - 1>::value;
};

template<>
struct Factorial<0> {
  static constexpr unsigned value = 1;
};

// Factorial<5>::value == 120, computed at COMPILE TIME
static_assert(Factorial<5>::value == 120, "5! should be 120");
```

#### 4. The STL
```cpp
// Containers, iterators, algorithms, function objects
#include <vector>
#include <algorithm>
#include <numeric>
#include <functional>

void stl_example() {
  std::vector<int> nums = {5, 3, 1, 4, 2};

  // Algorithm + iterator paradigm
  std::sort(nums.begin(), nums.end());

  // Function objects
  auto sum = std::accumulate(nums.begin(), nums.end(), 0);

  // Lambda as function object
  auto count_even = std::count_if(nums.begin(), nums.end(),
                                  [](int n) { return n % 2 == 0; });

  // STL convention: pass by value for iterators and function objects
  // (they are designed to be cheap to copy)
}
```

### Why This Matters: Rules Change by Sub-Language

```cpp
// RULE: Pass-by-value vs. pass-by-reference depends on the sub-language

// C sub-language: pass by value for built-in types
void increment(int x) { /* efficient */ }

// OO C++: pass by reference-to-const for user-defined types
void process(const Widget& w) { /* avoids expensive copy */ }

// Template C++: depends on the type parameter
template<typename T>
void handle(const T& t) { /* safe default */ }

// STL: pass iterators and function objects by value
std::for_each(v.begin(), v.end(), MyFunctor());
```

### Things to Remember
- C++ rules vary depending on which part of C++ you're using
- Pass-by-value is fine for built-in types and STL iterators/function objects
- Pass-by-reference-to-const is preferred for user-defined types
- For template code, the right approach depends on the template parameter

---

## Item 2: Prefer `const`, `enum`, and `inline` to `#define`

### Core Concept

"Prefer the compiler to the preprocessor." `#define` operates before the compiler even sees your code, leading 
to confusing errors, no type safety, and no scope control.

### Problem: `#define` for Constants

```cpp
// BAD: Preprocessor macro
#define ASPECT_RATIO 1.653
// Problem 1: "ASPECT_RATIO" may never be seen by compiler — error messages
//            will refer to "1.653", making debugging confusing
// Problem 2: No type information
// Problem 3: No scope — pollutes entire translation unit

// GOOD: typed constant
const double AspectRatio = 1.653;
// - Appears in symbol table — better error messages and debugger support
// - Type-checked by the compiler
// - Respects scope rules
```

### Special Cases for Constants

#### Constant Pointers
```cpp
// For constant char* strings in headers, you need TWO consts
const char* const authorName = "Scott Meyers";
//  ^^^^^          ^^^^^
//  |              pointer itself is const
//  what pointer points to is const

// Better: use std::string
const std::string authorName("Scott Meyers");
```

#### Class-Specific Constants
```cpp
class GamePlayer {
private:
  // Declaration of a class-specific constant
  static const int NumTurns = 5;  // In-class initialization (integral types only)
  int scores[NumTurns];           // Use of the constant

  // For non-integral types or when you need an address:
  static const double FudgeFactor;  // Declaration only
};

// Definition in .cpp file (required if address is ever taken)
const int GamePlayer::NumTurns;  // Definition; no value given (already in declaration)
const double GamePlayer::FudgeFactor = 1.35;  // Definition with value
```

### The `enum` Hack

```cpp
class GamePlayer {
private:
  // When your compiler won't allow in-class initialization:
  enum { NumTurns = 5 };  // "the enum hack"
  int scores[NumTurns];   // Works fine

  // Advantages of enum hack:
  // 1. It's impossible to take the address of an enum (more like #define)
  // 2. No memory allocated for the enum value
  // 3. Pragmatic — widely used in template metaprogramming
};

// enum hack in template metaprogramming
template<typename T>
struct TypeTraits {
  enum { isPointer = 0 };
};

template<typename T>
struct TypeTraits<T*> {
  enum { isPointer = 1 };  // Specialization for pointer types
};
```

### Problem: `#define` for Function-Like Macros

```cpp
// BAD: macro "function"
#define CALL_WITH_MAX(a, b) f((a) > (b) ? (a) : (b))

// Despite all the parentheses, this is STILL broken:
int a = 5, b = 0;
CALL_WITH_MAX(++a, b);      // a incremented TWICE
CALL_WITH_MAX(++a, b + 10); // a incremented ONCE
// Behavior depends on what b is compared to! Nightmare.

// GOOD: inline template function
template<typename T>
inline void callWithMax(const T& a, const T& b) {
  f(a > b ? a : b);
  // - Type safe
  // - Predictable evaluation (arguments evaluated exactly once)
  // - Respects scope and access control
  // - Can be debugged with a debugger
}
```

### Comprehensive Example: Replacing All `#define` Patterns

```cpp
// ===== BEFORE: #define everywhere =====
#define PI 3.14159265358979
#define MAX_BUFFER_SIZE 1024
#define MIN(a, b) ((a) < (b) ? (a) : (b))
#define SQUARE(x) ((x) * (x))
#define DEBUG_LOG(msg) std::cout << __FILE__ << ":" << __LINE__ << " " << msg << "\n"

// ===== AFTER: Modern C++ =====
constexpr double Pi = 3.14159265358979;
constexpr int MaxBufferSize = 1024;

template<typename T>
inline const T& minOf(const T& a, const T& b) {
  return a < b ? a : b;
}

template<typename T>
inline T square(const T& x) {
  return x * x;
}

// For debug logging, consider a proper logging framework
// or at minimum an inline function:
inline void debugLog(const char* file, int line, const std::string& msg) {
  std::cout << file << ":" << line << " " << msg << "\n";
}
#define DEBUG_LOG(msg) debugLog(__FILE__, __LINE__, msg)
// ^-- One of the FEW legitimate uses of #define:
//     __FILE__ and __LINE__ MUST be macros to get caller context
```

### Things to Remember
- For simple constants, prefer `const` objects or `enum`s to `#define`s
- For function-like macros, prefer `inline` functions to `#define`s
- `#define` doesn't respect scope, lacks type safety, and produces confusing errors
- The enum hack is a useful technique for compile-time integer constants

---

## Item 3: Use `const` Whenever Possible

### Core Concept

`const` is one of C++'s most powerful and versatile tools. It allows you to communicate and enforce the 
semantic constraint that an object should not be modified. The compiler enforces this constraint, catching 
errors at compile time.

### `const` with Pointers

```cpp
char greeting[] = "Hello";

char* p = greeting;                // non-const pointer, non-const data
const char* p = greeting;          // non-const pointer, const data
char* const p = greeting;          // const pointer, non-const data
const char* const p = greeting;    // const pointer, const data

// Rule: If const appears to the LEFT of the *, the data is const
// Rule: If const appears to the RIGHT of the *, the pointer is const

// These two are equivalent:
const char* p;    // pointer to const char
char const* p;    // pointer to const char (same thing, different style)
```

### `const` with Iterators

```cpp
#include <vector>

std::vector<int> vec = {1, 2, 3, 4, 5};

// const iterator = const pointer (T* const)
// The iterator itself can't change, but what it points to can
const std::vector<int>::iterator iter = vec.begin();
*iter = 10;    // OK: changes what iter points to
// ++iter;     // ERROR: iter is const

// iterator to const = pointer to const (const T*)
// The iterator can change, but what it points to can't
std::vector<int>::const_iterator cIter = vec.begin();
// *cIter = 10; // ERROR: *cIter is const
++cIter;         // OK: cIter itself isn't const
```

### `const` Member Functions

```cpp
class TextBlock {
public:
  // Two overloaded operator[]s — one for const objects, one for non-const
  const char& operator[](std::size_t position) const {
    // ... bounds checking, logging, etc.
    return text[position];
  }

  char& operator[](std::size_t position) {
    // ... bounds checking, logging, etc.
    return text[position];
  }

private:
  std::string text;
};

// Usage:
void print(const TextBlock& ctb) {
  std::cout << ctb[0];  // Calls const operator[]
  // ctb[0] = 'x';      // ERROR: const char& can't be assigned to
}

void modify(TextBlock& tb) {
  std::cout << tb[0];   // Calls non-const operator[]
  tb[0] = 'x';          // OK: char& can be assigned to
}
```

### Bitwise vs. Logical Constness

```cpp
// Bitwise constness: the compiler's definition
// A member function is const if it doesn't modify any data members
// BUT this can be too strict OR too lenient:

// Too lenient: bitwise const but logically non-const
class CTextBlock {
public:
  char& operator[](std::size_t position) const {
    return pText[position];  // Compiles! But allows modification through pointer
  }

private:
  char* pText;  // The pointer isn't modified, but what it points to can be!
};

const CTextBlock cctb("Hello");
char* pc = &cctb[0];
*pc = 'J';  // Now cctb has value "Jello" — a "const" object was modified!

// Solution: logical constness with mutable
class TextBlock {
public:
  std::size_t length() const {
    if (!lengthIsValid) {
      textLength = std::strlen(text.c_str());  // OK: mutable members
      lengthIsValid = true;                     // can be modified in const functions
    }
    return textLength;
  }

private:
  std::string text;
  mutable std::size_t textLength;   // These may always be modified,
  mutable bool lengthIsValid;       // even in const member functions
};
```

### Avoiding Duplication Between `const` and Non-`const` Member Functions

```cpp
class TextBlock {
public:
  const char& operator[](std::size_t position) const {
    // Bounds checking
    if (position >= text.size()) {
      throw std::out_of_range("TextBlock::operator[]");
    }
    // Logging
    // Data integrity validation
    // ... lots of shared logic ...
    return text[position];
  }

  char& operator[](std::size_t position) {
    // Cast away const from the return value of the const version
    // This is safe because we KNOW the object is non-const
    // (otherwise the non-const version wouldn't have been called)
    return const_cast<char&>(
      static_cast<const TextBlock&>(*this)[position]
    );
    // Step 1: static_cast<const TextBlock&>(*this) — add const to *this
    // Step 2: call const operator[] — safe, we're calling const version
    // Step 3: const_cast<char&>(...) — remove const from return value
  }

private:
  std::string text;
};

// NEVER do it the other way around (having const call non-const)!
// That would cast away the const-ness of the object, which is dangerous.
```

### `const` in Function Declarations

```cpp
class Rational {
public:
  Rational(int numerator = 0, int denominator = 1);

  int numerator() const;
  int denominator() const;
};

// Return const value to prevent meaningless assignments
const Rational operator*(const Rational& lhs, const Rational& rhs);

// Why const return value?
Rational a, b, c;
// (a * b) = c;    // ERROR with const return value — catches typo
// Programmer probably meant: if (a * b == c)

// const parameters — prevent accidental modification
bool operator==(const Rational& lhs, const Rational& rhs) {
  return lhs.numerator() * rhs.denominator() ==
  rhs.numerator() * lhs.denominator();
}
```

### Things to Remember
- Declaring something `const` helps compilers detect usage errors
- Compilers enforce bitwise constness, but you should program using logical constness
- When `const` and non-`const` member functions have essentially identical implementations, use the 
non-`const` version calling the `const` version to avoid duplication
- `const` can be applied to objects, function parameters, return types, and member functions

---

## Item 4: Make Sure That Objects Are Initialized Before They're Used

### Core Concept

Reading uninitialized values yields **undefined behavior** — anything can happen. C++ is inconsistent about 
when things get initialized, so the best approach is to **always initialize everything**.

### The Initialization Rules

```cpp
// Built-in types: NOT guaranteed to be initialized
int x;           // Uninitialized in some contexts!
int* p;          // Uninitialized — points to garbage

// User-defined types: constructors handle initialization
std::string s;   // Initialized to "" by default constructor
std::vector<int> v;  // Initialized to empty by default constructor

// The inconsistency:
class Point {
  int x, y;    // NOT initialized unless constructor does it
};

void foo() {
  int x;       // Uninitialized
  Point p;     // x and y are uninitialized!
}

// Arrays of built-in types:
int arr[100];    // NOT initialized to 0 in local scope
int arr2[100] = {};  // Zero-initialized (the {} trick)
```

### Initialization vs. Assignment in Constructors

```cpp
class PhoneNumber { /* ... */ };

class ABEntry {
public:
  // BAD: This is ASSIGNMENT, not initialization
  ABEntry(const std::string& name, const std::string& address,
          const std::list<PhoneNumber>& phones) {
    theName = name;       // These are all ASSIGNMENTS
    theAddress = address;  // The members were already DEFAULT-CONSTRUCTED
    thePhones = phones;    // before the body of the constructor executed
    numTimesConsulted = 0;
    // Cost: default construction + assignment = 2 operations per member
  }

  // GOOD: Member initialization list
  ABEntry(const std::string& name, const std::string& address,
          const std::list<PhoneNumber>& phones)
    : theName(name),           // These are true INITIALIZATIONS
    theAddress(address),      // Copy constructor called directly
    thePhones(phones),        // No default construction + assignment
    numTimesConsulted(0) {    // Even built-in types should be initialized
    // Body is empty — all work done in init list
    // Cost: 1 copy construction per member
  }

private:
  std::string theName;
  std::string theAddress;
  std::list<PhoneNumber> thePhones;
  int numTimesConsulted;
};
```

### Order of Initialization

```cpp
class Widget {
public:
  Widget(int val)
    : b(val),     // WARNING: despite appearing first in the init list,
    a(b) {      // 'a' is initialized FIRST because it's declared first!
    // If b hasn't been initialized yet when a(b) runs,
    // 'a' gets an uninitialized value. Bug!
  }

private:
  int a;  // Declared first → initialized first
  int b;  // Declared second → initialized second
};

// RULE: Members are initialized in the order of DECLARATION, not the
// order in which they appear in the initialization list.
// ALWAYS write initialization list in declaration order to avoid confusion.

class WidgetFixed {
public:
  WidgetFixed(int val)
    : a(val),     // First in declaration order → first in init list
    b(val) {    // Second in declaration order → second in init list
  }

private:
  int a;
  int b;
};
```

### The Static Initialization Order Problem

```cpp
// === file: FileSystem.cpp ===
class FileSystem {
public:
  std::size_t numDisks() const;
  // ...
};
extern FileSystem tfs;  // Object for clients to use

// === file: Directory.cpp ===
class Directory {
public:
  Directory() {
    std::size_t disks = tfs.numDisks();  // Uses tfs!
    // BUT: Is tfs initialized yet? MAYBE NOT.
    // If Directory's constructor runs before FileSystem's constructor,
    // this is undefined behavior!
  }
};
Directory tempDir;  // Another non-local static object

// PROBLEM: The relative order of initialization of non-local static objects
// defined in different translation units is UNDEFINED.
```

### The Solution: Meyers' Singleton (Local Static Objects)

```cpp
// === file: FileSystem.cpp ===
class FileSystem {
public:
  std::size_t numDisks() const;
  // ...
};

FileSystem& tfs() {
  static FileSystem fs;  // Local static — initialized on first call
  return fs;              // Return reference to the singleton
  // Guaranteed to be initialized before first use!
  // C++11 guarantees thread-safe initialization of local statics
}

// === file: Directory.cpp ===
class Directory {
public:
  Directory() {
    std::size_t disks = tfs().numDisks();  // Note: tfs() not tfs
    // tfs() returns a reference to the FileSystem singleton
    // The first call initializes it; subsequent calls just return it
  }
};

Directory& tempDir() {
  static Directory td;
  return td;
}

// This technique is known as the "Construct On First Use" idiom
// It replaces non-local statics with functions returning references
// to local statics, giving you full control over initialization order.
```

### Complete Example: Safe Initialization Patterns

```cpp
#include <string>
#include <vector>
#include <iostream>
#include <mutex>

// Pattern 1: Always use member initialization lists
class DatabaseConnection {
public:
  DatabaseConnection(const std::string& host, int port,
                     const std::string& dbName)
    : host_(host),
    port_(port),
    dbName_(dbName),
    connectionCount_(0),     // Even built-in types
    isConnected_(false) {}   // Don't skip any member

private:
  std::string host_;
  int port_;
  std::string dbName_;
  int connectionCount_;
  bool isConnected_;
};

// Pattern 2: Meyers' Singleton for cross-TU dependencies
class Logger {
public:
  void log(const std::string& msg) {
    std::lock_guard<std::mutex> lock(mutex_);
    std::cout << msg << "\n";
  }

  // Non-copyable
  Logger(const Logger&) = delete;
  Logger& operator=(const Logger&) = delete;

  static Logger& instance() {
    static Logger logger;  // Thread-safe in C++11+
    return logger;
  }

private:
  Logger() = default;
  std::mutex mutex_;
};

// Pattern 3: Default member initializers (C++11)
class Config {
  int maxRetries_ = 3;               // Default right in declaration
  double timeout_ = 30.0;
  std::string logLevel_ = "INFO";
  bool verbose_ = false;

public:
  Config() = default;  // All members have sensible defaults

  Config(int retries, double timeout)
    : maxRetries_(retries),  // Override only what needs changing
    timeout_(timeout) {}   // logLevel_ and verbose_ keep defaults
};

// Usage
void example() {
  auto& logger = Logger::instance();
  logger.log("Application started");

  Config defaultConfig;               // Uses all defaults
  Config customConfig(5, 60.0);       // Overrides retries and timeout
}
```

### Things to Remember
- Manually initialize objects of built-in type — C++ doesn't always do it for you
- In constructors, prefer member initialization lists over assignment in the body; list members in the same 
order they're declared
- Avoid the initialization order problem across translation units by replacing non-local static objects with 
functions returning references to local static objects (Meyers' Singleton)
- C++11 default member initializers are a convenient modern alternative for default values
