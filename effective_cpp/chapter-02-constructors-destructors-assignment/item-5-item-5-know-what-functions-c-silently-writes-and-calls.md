# Item 5: Know What Functions C++ Silently Writes and Calls

### Core Concept

When you declare an empty class, C++ does not leave it truly empty. The compiler will **automatically 
generate** certain special member functions if you don't declare them yourself. Understanding exactly what 
gets generated — and under what conditions — is essential to avoiding subtle bugs.

### What the Compiler Generates

For an apparently empty class:

```cpp
class Empty {};
```

The compiler behaves as though you had written:

```cpp
class Empty {
public:
  Empty() { }                             // default constructor
  Empty(const Empty& rhs) { }             // copy constructor
  ~Empty() { }                            // destructor
  Empty& operator=(const Empty& rhs) { }  // copy assignment operator
};
```

These are generated **only if they are needed** (i.e., only if your code actually calls them). They are all 
`public` and `inline`.

### The Default Constructor

The compiler generates a default constructor only if you declare **no constructors at all**.

```cpp
// CASE 1: Compiler generates a default constructor
class Widget {
  int value_;   // left uninitialized by generated default ctor!
  std::string name_;  // default-constructed (empty string)
};

Widget w;  // Fine — compiler-generated default ctor is called
// w.value_ is UNINITIALIZED (undefined behavior to read it)
// w.name_ is ""

// CASE 2: No default constructor generated — you declared a constructor
class Gadget {
public:
  Gadget(int id) : id_(id) {}  // user-declared constructor
private:
  int id_;
};

Gadget g1(42);  // Fine
// Gadget g2;   // ERROR! No default constructor available
// The compiler does NOT generate one because you declared a ctor
```

**Real-world consequence — STL containers:**

```cpp
class DatabaseRecord {
public:
  // Only this constructor — no default ctor generated
  DatabaseRecord(int id, const std::string& table) : id_(id), table_(table) {}
private:
  int id_;
  std::string table_;
};

// This is a problem for certain container operations:
std::vector<DatabaseRecord> records;
records.resize(10);  // ERROR! resize() needs to default-construct objects
// No default constructor available

// FIX: Provide a default constructor or use a different approach
std::vector<DatabaseRecord> records2;
records2.reserve(10);  // reserve does NOT construct objects — OK
records2.push_back(DatabaseRecord(1, "users"));  // explicit construction
```

### The Copy Constructor

The compiler-generated copy constructor performs **member-wise copy construction** — it copies each non-static 
data member from the source object to the new object.

```cpp
class NamedObject {
public:
  NamedObject(const std::string& name, int value)
  : name_(name), value_(value) {}

  // Compiler generates:
  // NamedObject(const NamedObject& rhs)
  //     : name_(rhs.name_),       // calls std::string copy ctor
  //       value_(rhs.value_) {}   // copies the int bitwise

private:
  std::string name_;   // has its own copy constructor
  int value_;          // built-in type — bitwise copy
};

NamedObject obj1("Widget", 42);
NamedObject obj2(obj1);  // Compiler-generated copy ctor called
// obj2.name_ is "Widget" (independent copy)
// obj2.value_ is 42
```

**When member-wise copy is dangerous:**

```cpp
// BAD: Raw pointer member with compiler-generated copy ctor
class RawBuffer {
public:
  RawBuffer(size_t size) : data_(new char[size]), size_(size) {
    std::memset(data_, 0, size_);
  }
  ~RawBuffer() { delete[] data_; }  // free the memory

  // Compiler generates a copy ctor that copies the POINTER, not the data:
  // RawBuffer(const RawBuffer& rhs) //     : data_(rhs.data_),    // SHALLOW COPY! Two objects share same 
  memory!
  //       size_(rhs.size_) {}

private:
  char* data_;
  size_t size_;
};

void disaster() {
  RawBuffer buf1(1024);
  RawBuffer buf2(buf1);   // Both buf1 and buf2 point to the same memory!
  // When buf2 is destroyed: delete[] data_ frees the memory
  // When buf1 is destroyed: delete[] data_ frees ALREADY-FREED memory
  // DOUBLE FREE — undefined behavior, likely crash
}

// GOOD: Proper deep copy
class SafeBuffer {
public:
  SafeBuffer(size_t size) : data_(new char[size]), size_(size) {
    std::memset(data_, 0, size_);
  }

  SafeBuffer(const SafeBuffer& rhs) : data_(new char[rhs.size_]),   // allocate own memory
    size_(rhs.size_) {
    std::memcpy(data_, rhs.data_, size_);  // copy the DATA, not the pointer
  }

  ~SafeBuffer() { delete[] data_; }

private:
  char* data_;
  size_t size_;
};
```

### The Copy Assignment Operator

The generated copy assignment operator also performs member-wise copy, but via assignment rather than 
construction. It behaves the same way — and has the same dangers with pointer members.

```cpp
class Employee {
public:
  Employee(const std::string& name, int id) : name_(name), id_(id) {}
  // Compiler generates:
  // Employee& operator=(const Employee& rhs) {
  //     name_ = rhs.name_;   // calls std::string::operator=
  //     id_ = rhs.id_;       // bitwise copy of int
  //     return *this;
  // }
private:
  std::string name_;
  int id_;
};

Employee e1("Alice", 1001);
Employee e2("Bob", 1002);
e2 = e1;  // e2 is now a copy of e1
```

### When the Compiler REFUSES to Generate Copy Assignment

The compiler will not generate `operator=` in certain cases where member-wise assignment would be illegal or 
ambiguous.

**Case 1: Reference members**

```cpp
class BindingRef {
public:
  BindingRef(std::string& ref, int val) : nameRef_(ref), value_(val) {}

  // Compiler WILL NOT generate operator=
  // Because you cannot rebind a reference — nameRef_ was bound at construction
  // and C++ references cannot be reseated

private:
  std::string& nameRef_;   // reference member
  int value_;
};

std::string s1 = "hello", s2 = "world";
BindingRef br1(s1, 1);
BindingRef br2(s2, 2);
// br1 = br2;  // ERROR: compiler cannot generate operator=
// Should it rebind the reference? (Illegal in C++)
// Should it modify the referred-to object? (Surprising semantics)
// Compiler's answer: refuse to decide — you write it
```

**Case 2: const members**

```cpp
class ImmutableId {
public:
  ImmutableId(int id, const std::string& name) : id_(id), name_(name) {}

  // Compiler WILL NOT generate operator=
  // Because const members cannot be assigned to

private:
  const int id_;           // const member — cannot be modified after construction
  std::string name_;
};

ImmutableId a(1, "alpha");
ImmutableId b(2, "beta");
// a = b;  // ERROR: cannot assign to const member id_
```

**Case 3: Base class with private/deleted operator=**

```cpp
class Uncopyable {
public:
  Uncopyable() = default;
private:
  Uncopyable& operator=(const Uncopyable&);  // private — inaccessible
};

class Derived : public Uncopyable {
public:
  Derived(int x) : x_(x) {}
  // Compiler WILL NOT generate operator= for Derived
  // because it would need to call Uncopyable::operator=, which is private
private:
  int x_;
};
```

### The Destructor

The compiler-generated destructor is **non-virtual** (unless the class inherits from a base class that already 
has a virtual destructor). It invokes the destructors of each non-static data member and each base class in 
reverse order of construction.

```cpp
class Composite {
public:
  Composite() : name_("default"), id_(0) {}
  // Compiler generates:
  // ~Composite() {
  //     // id_ is int — no destructor to call
  //     // name_ is std::string — calls std::string::~string()
  //     // Then base class destructors (if any) in reverse order
  // }
private:
  std::string name_;
  int id_;
};
```

**Critical: the generated destructor is NOT virtual:**

```cpp
class Base {
public:
  // Compiler-generated destructor is NON-VIRTUAL
  // ~Base() {}  // implicitly generated
};

class Derived : public Base {
public:
  Derived() : data_(new int[100]) {}
  ~Derived() { delete[] data_; }
private:
  int* data_;
};

// This leaks memory!
Base* ptr = new Derived();
delete ptr;  // Calls Base::~Base() only — Derived::~Derived() never runs
// The int[100] is leaked
// (Technically undefined behavior)
```

### Real-World Example: Understanding All Four Together

```cpp
#include <string>
#include <iostream>

class LogEntry {
public:
  // User-declared constructor — no default ctor generated
  LogEntry(const std::string& msg, int severity)
  : message_(msg), severity_(severity) {
    std::cout << "LogEntry constructed: " << message_ << "\n";
  }

  // No copy ctor declared — compiler generates one (member-wise copy)
  // No operator= declared — compiler generates one (member-wise assignment)
  // No destructor declared — compiler generates one (non-virtual)

  void print() const {
    std::cout << "[" << severity_ << "] " << message_ << "\n";
  }

private:
  std::string message_;    // copy ctor/assignment via std::string's
  int severity_;           // copy ctor/assignment via bitwise copy
};

void demonstrate() {
  LogEntry entry1("System started", 0);   // user-declared ctor
  LogEntry entry2(entry1);                // compiler-generated copy ctor
  LogEntry entry3("Placeholder", 99);     // user-declared ctor
  entry3 = entry1;                        // compiler-generated operator=

  // LogEntry entry4;  // ERROR: no default ctor (because user declared a ctor)

  entry2.print();  // [0] System started
  entry3.print();  // [0] System started
}
// All three LogEntry objects destroyed here by compiler-generated destructors
```

### Things to Remember

- Compilers may implicitly generate a default constructor, copy constructor, copy assignment operator, and 
destructor for a class.
- The default constructor is generated only if you declare no constructors at all.
- The generated copy operations perform member-wise copy — shallow, not deep. This is dangerous for classes 
managing raw resources (pointers, file handles, etc.).
- The generated destructor is non-virtual unless the class inherits from a base with a virtual destructor.
- The compiler will refuse to generate `operator=` if the class contains reference members, const members, or 
if a base class has an inaccessible `operator=`.

---
