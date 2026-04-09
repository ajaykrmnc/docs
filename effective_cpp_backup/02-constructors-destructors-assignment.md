# Chapter 2: Constructors, Destructors, and Assignment Operators

[>](2026-04-09_>.md) Items 5-12: The special member functions that control object lifecycle — creation, destruction, and copying. 
> Getting these right is fundamental to writing correct, efficient, and exception-safe C++.

---

## Item 5: Know What Functions C++ Silently Writes and Calls

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

## Item 6: Explicitly Disallow the Use of Compiler-Generated Functions You Do Not Want

### Core Concept

Sometimes copying an object makes no sense. A class representing a unique system resource — a database 
connection, a singleton, a log file handle — should not be copyable. But if you don't take action, the 
compiler will happily generate copy operations for you. You must **explicitly prevent** unwanted copying.

### The Problem: Accidental Copies of Unique Resources

```cpp
// BAD: This class manages a unique resource but is implicitly copyable!
class DatabaseConnection {
public:
  DatabaseConnection(const std::string& connStr) {
    handle_ = db_connect(connStr.c_str());  // acquire unique resource
  }
  ~DatabaseConnection() {
    db_disconnect(handle_);  // release resource
  }

  void executeQuery(const std::string& sql) { /* ... */ }

private:
  db_handle_t handle_;
  // Compiler generates copy ctor and operator= that copy the handle!
  // Two objects would share the same connection handle
  // Double-close on destruction — undefined behavior
};

void oops() {
  DatabaseConnection conn("host=localhost dbname=mydb");
  DatabaseConnection conn2 = conn;  // Compiles! But it shouldn't!
  // Both conn and conn2 now hold the same db handle
  // When conn2 is destroyed: db_disconnect(handle_)
  // When conn is destroyed: db_disconnect(handle_) again — DOUBLE CLOSE!
}
```

### Solution 1: Declare Private and Don't Define (C++03 Approach)

The classic Effective C++ technique — declare the copy operations `private` and don't provide a definition.

```cpp
class DatabaseConnection {
public:
  DatabaseConnection(const std::string& connStr) {
    handle_ = db_connect(connStr.c_str());
  }
  ~DatabaseConnection() {
    db_disconnect(handle_);
  }

  void executeQuery(const std::string& sql) { /* ... */ }

private:
  // Declared private — prevents external code from copying
  // Not defined — prevents member functions and friends from copying
  DatabaseConnection(const DatabaseConnection&);             // no definition
  DatabaseConnection& operator=(const DatabaseConnection&);  // no definition

  db_handle_t handle_;
};

void test() {
  DatabaseConnection conn("host=localhost");
  // DatabaseConnection conn2(conn);       // ERROR: copy ctor is private
  // DatabaseConnection conn3 = conn;      // ERROR: copy ctor is private
  // conn3 = conn;                         // ERROR: operator= is private
}
```

If a member function or friend tries to copy, the error surfaces as a **link-time** error (undefined symbol) 
rather than a compile-time error — not ideal, but it still catches the mistake.

```cpp
class DatabaseConnection {
  // ... same as above ...
    
  friend void backup(DatabaseConnection& conn) {
    DatabaseConnection copy(conn);  // Compiles (friend can access private)
    // but LINKER ERROR: undefined reference
  }
};
```

### Solution 2: Inherit from an Uncopyable Base Class (C++03)

Move the private-and-undefined trick into a reusable base class:

```cpp
class Uncopyable {
protected:
  Uncopyable() {}                                    // allow construction
  ~Uncopyable() {}                                   // allow destruction

private:
  Uncopyable(const Uncopyable&);                     // prevent copying
  Uncopyable& operator=(const Uncopyable&);          // prevent assignment
};

// Now any class that inherits from Uncopyable is non-copyable
class UniqueFile : private Uncopyable {  // private inheritance — is-implemented-in-terms-of
public:
  UniqueFile(const std::string& path) {
    file_ = fopen(path.c_str(), "r");
  }
  ~UniqueFile() {
    if (file_) fclose(file_);
  }

private:
  FILE* file_;
};

void test() {
  UniqueFile f1("/etc/passwd");
  // UniqueFile f2(f1);   // ERROR: copy ctor of Uncopyable is private
  // f2 = f1;             // ERROR: operator= of Uncopyable is private
}
```

Boost provides `boost::noncopyable` for exactly this purpose:

```cpp
#include <boost/noncopyable.hpp>

class Singleton : private boost::noncopyable {
public:
  static Singleton& instance() {
    static Singleton s;
    return s;
  }
  void doWork() { /* ... */ }

private:
  Singleton() {}  // private ctor for singleton pattern
};
```

### Solution 3: `= delete` (C++11 and Beyond — Preferred)

Modern C++ provides a much cleaner mechanism: explicitly deleting functions.

```cpp
class DatabaseConnection {
public:
  DatabaseConnection(const std::string& connStr) {
    handle_ = db_connect(connStr.c_str());
  }
  ~DatabaseConnection() {
    db_disconnect(handle_);
  }

  // Explicitly deleted — clear intent, better error messages
  DatabaseConnection(const DatabaseConnection&) = delete;
  DatabaseConnection& operator=(const DatabaseConnection&) = delete;

  void executeQuery(const std::string& sql) { /* ... */ }

private:
  db_handle_t handle_;
};

void test() {
  DatabaseConnection conn("host=localhost");
  // DatabaseConnection conn2(conn);  // ERROR: "use of deleted function 'DatabaseConnection(const 
  DatabaseConnection&)'"
  // Much clearer error message than "private within this context"
}
```

**Advantages of `= delete` over the private-and-undefined approach:**

```cpp
class NetworkSocket {
public:
  NetworkSocket(int port) : fd_(socket(AF_INET, SOCK_STREAM, 0)) {
    // bind and listen...
  }
  ~NetworkSocket() { close(fd_); }

  // = delete works even when declared public — and SHOULD be public
  // Why public? Because the error message is better:
  //   "deleted function" vs "private within this context"
  // The user sees immediately that copying was intentionally forbidden,
  // not accidentally hidden
  NetworkSocket(const NetworkSocket&) = delete;
  NetworkSocket& operator=(const NetworkSocket&) = delete;

  // You can also delete specific overloads to prevent implicit conversions:
  void send(const char* data, size_t len);
  void send(int) = delete;       // prevent accidental send(42)
  void send(double) = delete;    // prevent accidental send(3.14)
  void send(bool) = delete;      // prevent accidental send(true)

private:
  int fd_;
};

void test() {
  NetworkSocket sock(8080);
  sock.send("hello", 5);  // Fine
  // sock.send(42);        // ERROR: use of deleted function
  // sock.send(3.14);      // ERROR: use of deleted function
  // Without the deleted overloads, 42 would silently convert to const char*!
}
```

### Real-World Example: Thread-Safe Logger (Non-Copyable but Movable)

```cpp
#include <mutex>
#include <fstream>
#include <string>

class Logger {
public:
  explicit Logger(const std::string& filepath)
  : file_(filepath, std::ios::app) {
    if (!file_.is_open()) {
      throw std::runtime_error("Cannot open log file: " + filepath);
    }
  }

  ~Logger() {
    if (file_.is_open()) {
      file_.flush();
      file_.close();
    }
  }

  // Copying a logger makes no sense — two loggers writing to the same file
  // with separate mutexes would cause interleaved output
  Logger(const Logger&) = delete;
  Logger& operator=(const Logger&) = delete;

  // Moving is fine — transfer ownership of the file handle
  Logger(Logger&& other) noexcept
  : file_(std::move(other.file_)) {}

  Logger& operator=(Logger&& other) noexcept {
    if (this != &other) {
      file_ = std::move(other.file_);
    }
    return *this;
  }

  void log(const std::string& message) {
    std::lock_guard<std::mutex> lock(mutex_);
    file_ << message << "\n";
  }

private:
  std::ofstream file_;
  std::mutex mutex_;  // std::mutex is itself non-copyable and non-movable
};

void test() {
  Logger logger("app.log");
  logger.log("Application started");

  // Logger copy = logger;         // ERROR: deleted
  Logger moved = std::move(logger);  // Fine — ownership transferred
  moved.log("Continuing after move");
}
```

### Real-World Example: Unique Handle Wrapper

```cpp
// A RAII wrapper for OS handles that must not be duplicated
template<typename HandleTraits>
class UniqueHandle {
public:
  explicit UniqueHandle(typename HandleTraits::Type h = HandleTraits::Invalid())
  : handle_(h) {}

  ~UniqueHandle() {
    if (handle_ != HandleTraits::Invalid()) {
      HandleTraits::Close(handle_);
    }
  }

  // Non-copyable
  UniqueHandle(const UniqueHandle&) = delete;
  UniqueHandle& operator=(const UniqueHandle&) = delete;

  // Movable
  UniqueHandle(UniqueHandle&& other) noexcept : handle_(other.handle_) {
    other.handle_ = HandleTraits::Invalid();
  }

  UniqueHandle& operator=(UniqueHandle&& other) noexcept {
    if (this != &other) {
      if (handle_ != HandleTraits::Invalid()) {
        HandleTraits::Close(handle_);
      }
      handle_ = other.handle_;
      other.handle_ = HandleTraits::Invalid();
    }
    return *this;
  }

  typename HandleTraits::Type get() const { return handle_; }
  bool isValid() const { return handle_ != HandleTraits::Invalid(); }

private:
  typename HandleTraits::Type handle_;
};

// Usage with file descriptors
struct FileDescriptorTraits {
  using Type = int;
  static Type Invalid() { return -1; }
  static void Close(Type fd) { ::close(fd); }
};

using UniqueFd = UniqueHandle<FileDescriptorTraits>;

void example() {
  UniqueFd fd(open("/tmp/test.txt", O_RDONLY));
  // UniqueFd fd2 = fd;              // ERROR: deleted copy ctor
  UniqueFd fd2 = std::move(fd);      // Fine — ownership transfer
  // fd is now invalid, fd2 owns the file descriptor
}
```

### Things to Remember

- The compiler will generate copy constructor and copy assignment operator if you don't declare them. If 
copying is inappropriate for your class, you must explicitly prevent it.
- In C++03, declare copy operations `private` and don't define them, or inherit from an `Uncopyable` base 
class.
- In C++11 and later, use `= delete` — it's clearer, produces better error messages, and works for any 
function, not just copy operations.
- Declare deleted functions `public` for the best error messages.
- Consider whether your non-copyable class should still be **movable** (like `std::unique_ptr`).

---

## Item 7: Declare Destructors Virtual in Polymorphic Base Classes

### Core Concept

When a derived class object is deleted through a base class pointer, and the base class has a **non-virtual 
destructor**, the behavior is **undefined**. In practice, the derived class's destructor typically never runs, 
leading to resource leaks and corruption. Any class designed to be used polymorphically must have a virtual 
destructor.

### The Problem: Non-Virtual Destructor with Polymorphic Deletion

```cpp
// BAD: Non-virtual destructor in a polymorphic base class
class TimeKeeper {
public:
  TimeKeeper() {}
  ~TimeKeeper() {}  // NON-VIRTUAL destructor!

  virtual int getCurrentTime() const = 0;  // virtual function => polymorphic use
};

class AtomicClock : public TimeKeeper {
public:
  AtomicClock() : calibrationData_(new double[1000]) {
    // Expensive calibration data
  }
  ~AtomicClock() {
    delete[] calibrationData_;  // Free calibration data
    std::cout << "AtomicClock resources freed\n";
  }
  int getCurrentTime() const override { return /* atomic time */0; }

private:
  double* calibrationData_;
};

class WaterClock : public TimeKeeper {
public:
  WaterClock() : waterLevel_(new float[500]) {}
  ~WaterClock() {
    delete[] waterLevel_;
    std::cout << "WaterClock resources freed\n";
  }
  int getCurrentTime() const override { return /* water time */0; }

private:
  float* waterLevel_;
};

// Factory function returns base class pointer
TimeKeeper* getTimeKeeper(const std::string& type) {
  if (type == "atomic") return new AtomicClock();
  if (type == "water")  return new WaterClock();
  return nullptr;
}

void disaster() {
  TimeKeeper* tk = getTimeKeeper("atomic");
  // ... use tk ...
  delete tk;  // UNDEFINED BEHAVIOR!
  // TimeKeeper::~TimeKeeper() is non-virtual
  // Only the TimeKeeper part is destroyed
  // AtomicClock::~AtomicClock() is NOT called
  // calibrationData_ is LEAKED
  // The "AtomicClock resources freed" message never prints
}
```

### The Fix: Virtual Destructor

```cpp
// GOOD: Virtual destructor in polymorphic base class
class TimeKeeper {
public:
  TimeKeeper() {}
  virtual ~TimeKeeper() {}  // VIRTUAL destructor

  virtual int getCurrentTime() const = 0;
};

class AtomicClock : public TimeKeeper {
public:
  AtomicClock() : calibrationData_(new double[1000]) {}
  ~AtomicClock() override {  // 'override' for safety (C++11)
    delete[] calibrationData_;
    std::cout << "AtomicClock resources freed\n";
  }
  int getCurrentTime() const override { return 0; }

private:
  double* calibrationData_;
};

void correct() {
  TimeKeeper* tk = getTimeKeeper("atomic");
  delete tk;  // CORRECT: virtual dispatch calls AtomicClock::~AtomicClock()
  // then TimeKeeper::~TimeKeeper()
  // "AtomicClock resources freed" prints
  // No leak
}
```

### The Rule: Virtual Destructor IFF Polymorphic

The rule is not "always make destructors virtual." It is: **if the class has any virtual functions, the 
destructor should be virtual.**

**Why not make ALL destructors virtual?**

```cpp
// BAD: Gratuitous virtual destructor on a non-polymorphic class
class Point {
public:
  Point(int x, int y) : x_(x), y_(y) {}
  virtual ~Point() {}  // Unnecessary virtual — this class is not polymorphic

private:
  int x_, y_;
};
// sizeof(Point) without virtual: typically 8 bytes (two ints)
// sizeof(Point) with virtual: typically 16 bytes (two ints + vptr)
// That's a 100% overhead! And it breaks C-compatibility for layout.

// GOOD: No virtual destructor — this class is not meant for polymorphism
class Point {
public:
  Point(int x, int y) : x_(x), y_(y) {}
  // No virtual destructor — and no virtual functions at all
  // sizeof(Point) == 8 bytes, C-compatible layout

private:
  int x_, y_;
};
```

A virtual function adds a **vptr** (virtual table pointer) to each object instance, typically 8 bytes on a 
64-bit system. For small value-type objects, this overhead is unacceptable.

### The Dangers of Inheriting from Non-Virtual-Destructor Classes

Standard library classes like `std::string`, `std::vector`, and `std::unordered_map` do **not** have virtual 
destructors. Inheriting from them is dangerous:

```cpp
// BAD: Inheriting from std::string (which has a non-virtual destructor)
class SpecialString : public std::string {
public:
  SpecialString(const char* s) : std::string(s), metadata_(new int(42)) {}
  ~SpecialString() { delete metadata_; }  // cleanup

private:
  int* metadata_;
};

void danger() {
  std::string* sp = new SpecialString("hello");
  delete sp;  // UNDEFINED BEHAVIOR!
  // std::string::~string() is non-virtual
  // SpecialString::~SpecialString() never runs
  // metadata_ is leaked
}

// BAD: Inheriting from std::vector
class AuditedVector : public std::vector<int> {
public:
  ~AuditedVector() {
    logToAuditTrail("Vector destroyed with " + std::to_string(size()) + " elements");
  }
};
// Same problem: deleting through a std::vector<int>* skips the audit log
```

**The safe alternative — composition over inheritance:**

```cpp
// GOOD: Use composition instead of inheriting from standard containers
class AuditedVector {
public:
  void push_back(int val) {
    data_.push_back(val);
    logToAuditTrail("Element added: " + std::to_string(val));
  }

  size_t size() const { return data_.size(); }

  ~AuditedVector() {
    logToAuditTrail("Vector destroyed with " + std::to_string(data_.size()) + " elements");
  }

private:
  std::vector<int> data_;  // composition, not inheritance
};
```

### Pure Virtual Destructor for Abstract Base Classes

Sometimes you want an abstract class but have no natural pure virtual function. You can make the destructor 
pure virtual — but you **must still provide a definition**.

```cpp
class AbstractAnimal {
public:
  virtual ~AbstractAnimal() = 0;  // pure virtual destructor
  // Makes the class abstract — cannot be instantiated directly
};

// You MUST provide a definition! Derived class destructors call the base destructor.
AbstractAnimal::~AbstractAnimal() {
  // Base cleanup (if any)
  // This body can be empty, but the definition must exist
}

class Dog : public AbstractAnimal {
public:
  Dog(const std::string& name) : name_(name) {}
  ~Dog() override {
    std::cout << name_ << " destroyed\n";
    // After this, AbstractAnimal::~AbstractAnimal() is called automatically
  }
private:
  std::string name_;
};

void test() {
  // AbstractAnimal a;              // ERROR: cannot instantiate abstract class
  AbstractAnimal* pet = new Dog("Rex");
  delete pet;  // Correctly calls Dog::~Dog() then AbstractAnimal::~AbstractAnimal()
}
```

### Real-World Example: Plugin System

```cpp
// A plugin system where plugins are loaded dynamically and destroyed
// through base class pointers — virtual destructor is ESSENTIAL

class Plugin {
public:
  virtual ~Plugin() = default;  // MUST be virtual

  virtual std::string name() const = 0;
  virtual void initialize() = 0;
  virtual void execute() = 0;
  virtual void shutdown() = 0;
};

class ImageProcessorPlugin : public Plugin {
public:
  ImageProcessorPlugin() : buffer_(nullptr), bufferSize_(0) {}

  ~ImageProcessorPlugin() override {
    delete[] buffer_;  // Must run! Only runs if base dtor is virtual.
    std::cout << "ImageProcessor plugin destroyed, buffer freed\n";
  }

  std::string name() const override { return "ImageProcessor"; }

  void initialize() override {
    bufferSize_ = 1024 * 1024;  // 1MB
    buffer_ = new unsigned char[bufferSize_];
  }

  void execute() override {
    // Process image data in buffer_
  }

  void shutdown() override {
    // Graceful shutdown
  }

private:
  unsigned char* buffer_;
  size_t bufferSize_;
};

class PluginManager {
public:
  void loadPlugin(std::unique_ptr<Plugin> plugin) {
    plugin->initialize();
    plugins_.push_back(std::move(plugin));
  }

  ~PluginManager() {
    for (auto& p : plugins_) {
      p->shutdown();
    }
    // unique_ptr calls delete on Plugin* pointers
    // Virtual destructor ensures derived destructors run correctly
    plugins_.clear();
  }

private:
  std::vector<std::unique_ptr<Plugin>> plugins_;
};
```

### Real-World Example: Shape Hierarchy

```cpp
class Shape {
public:
  virtual ~Shape() = default;  // Virtual destructor — this is a polymorphic base

  virtual double area() const = 0;
  virtual double perimeter() const = 0;
  virtual void draw() const = 0;

  // Non-virtual interface pattern (NVI) — see Item 35
  std::string describe() const {
    return "Shape with area=" + std::to_string(area()) +
    " perimeter=" + std::to_string(perimeter());
  }
};

class Circle : public Shape {
public:
  explicit Circle(double radius) : radius_(radius) {}
  // No explicit destructor needed — default is fine
  // But it IS virtual because base class destructor is virtual

  double area() const override { return M_PI * radius_ * radius_; }
  double perimeter() const override { return 2 * M_PI * radius_; }
  void draw() const override { /* ... */ }

private:
  double radius_;
};

class Polygon : public Shape {
public:
  Polygon(std::vector<Point> vertices)
    : vertices_(std::move(vertices)),
    texture_(new Texture("default.png")) {}  // heap resource

  ~Polygon() override {
    delete texture_;  // Properly called through virtual dispatch
  }

  double area() const override { /* shoelace formula */ return 0; }
  double perimeter() const override { /* sum of edge lengths */ return 0; }
  void draw() const override { /* ... */ }

private:
  std::vector<Point> vertices_;
  Texture* texture_;
};

void render(const std::vector<std::unique_ptr<Shape>>& shapes) {
  for (const auto& shape : shapes) {
    std::cout << shape->describe() << "\n";
  }
}
// When shapes vector is destroyed, each unique_ptr calls delete on Shape*
// Virtual destructor ensures Polygon::~Polygon runs and texture_ is freed
```

### Things to Remember

- Polymorphic base classes should declare virtual destructors. If a class has any virtual functions, it should 
have a virtual destructor.
- Classes not designed to be base classes or not designed for polymorphic use should **not** declare virtual 
destructors.
- Never inherit from standard library container classes (`std::string`, `std::vector`, etc.) — they have 
non-virtual destructors.
- A pure virtual destructor makes a class abstract but must still have a definition (the body can be empty).

---

## Item 8: Prevent Exceptions from Leaving Destructors

### Core Concept

Destructors should **never** emit exceptions. If an exception escapes a destructor while another exception is 
already propagating (during stack unwinding), C++ calls `std::terminate()`, which kills the program 
immediately. Even without double-exception scenarios, throwing destructors make it impossible to write correct 
cleanup code.

### Why Throwing Destructors Are Catastrophic

```cpp
// BAD: Destructor that throws
class DatabaseSession {
public:
  DatabaseSession() { /* open connection */ }

  ~DatabaseSession() {
    // What if commit() throws? commit();  // might throw std::runtime_error
    disconnect();
  }

  void commit() {
    if (!changes_.empty()) {
      // Might fail — network error, constraint violation, etc.
      throw std::runtime_error("Commit failed");
    }
  }

  void disconnect() { /* close connection */ }

private:
  std::vector<std::string> changes_;
};

void catastrophe() {
  try {
    DatabaseSession s1;
    DatabaseSession s2;
    // ... do work ...
    throw std::runtime_error("Application error");
    // Stack unwinding begins:
    // s2.~DatabaseSession() is called — if commit() throws here,
    //   we now have TWO active exceptions
    //   C++ calls std::terminate() — program dies immediately
  } catch (...) {
    // We never reach this handler
  }
}
```

**The double-exception problem with containers:**

```cpp
// Even worse with containers
void containerProblem() {
  std::vector<DatabaseSession> sessions(10);
  // Vector destruction calls ~DatabaseSession() for each element
  // If the 3rd destructor throws, stack unwinding destroys elements 4-10
  // If the 7th destructor ALSO throws during that unwinding:
  //   std::terminate() — immediate program death
}
```

### Solution 1: Swallow the Exception (Log and Continue)

```cpp
class DatabaseSession {
public:
  DatabaseSession() : connected_(true) {}

  ~DatabaseSession() {
    try {
      if (connected_) {
        commit();
        disconnect();
        connected_ = false;
      }
    } catch (const std::exception& e) {
      // Log the error — don't let it escape
      std::cerr << "WARNING: Exception in ~DatabaseSession: " << e.what() << "\n";
      // Swallow the exception — destructor completes normally
      // This is acceptable when the failure is non-critical
    } catch (...) {
      std::cerr << "WARNING: Unknown exception in ~DatabaseSession\n";
    }
  }

  void commit() { /* might throw */ }
  void disconnect() { connected_ = false; }

private:
  bool connected_;
  std::vector<std::string> changes_;
};
```

### Solution 2: Abort on Failure (When Continuing Is Dangerous)

```cpp
class CriticalResource {
public:
  CriticalResource() { /* acquire */ }

  ~CriticalResource() {
    try {
      release();
    } catch (...) {
      // If we can't release a critical resource, the program state
      // is corrupted. Better to abort cleanly than continue in an
      // undefined state.
      std::cerr << "FATAL: Cannot release critical resource. Aborting.\n";
      std::abort();  // Immediate, clean termination
    }
  }

  void release() { /* might throw */ }
};
```

### Solution 3: Give Clients a Chance to Handle It (Preferred)

The best approach: provide a separate function that clients can call to perform the operation that might 
throw, then have the destructor serve as a fallback safety net.

```cpp
// GOOD: Two-phase close pattern
class DatabaseSession {
public:
  DatabaseSession(const std::string& connStr)
  : connected_(true), closed_(false) {
    // Open connection
  }

  // Public close function — clients SHOULD call this
  // It CAN throw, and clients can handle the exception
  void close() {
    if (!closed_) {
      commit();       // might throw — client can catch
      disconnect();   // might throw — client can catch
      closed_ = true;
    }
  }

  // Destructor — safety net, never throws
  ~DatabaseSession() {
    if (!closed_) {
      try {
        commit();
        disconnect();
        closed_ = true;
      } catch (const std::exception& e) {
        std::cerr << "WARNING: Cleanup failed in destructor: "
          << e.what() << "\n";
        // Swallow — destructor must not throw
        // The client had their chance to call close() and handle errors
      } catch (...) {
        std::cerr << "WARNING: Unknown cleanup failure in destructor\n";
      }
    }
  }

  void addChange(const std::string& change) {
    changes_.push_back(change);
  }

private:
  void commit() { /* might throw */ }
  void disconnect() { connected_ = false; }

  bool connected_;
  bool closed_;
  std::vector<std::string> changes_;
};

// Client code — proper usage
void properUsage() {
  DatabaseSession session("host=localhost");
  session.addChange("INSERT INTO users ...");
  session.addChange("UPDATE accounts ...");

  try {
    session.close();  // Try to close explicitly
  } catch (const std::exception& e) {
    std::cerr << "Failed to commit: " << e.what() << "\n";
    // Handle the error — retry, rollback, alert user, etc.
  }
  // Even if close() threw, the destructor will try again as a safety net
  // But the client had the opportunity to handle the error properly
}
```

### Real-World Example: File Writer with Flush

```cpp
#include <fstream>
#include <stdexcept>

class BufferedFileWriter {
public:
  explicit BufferedFileWriter(const std::string& path)
  : file_(path, std::ios::binary), flushed_(false) {
    if (!file_.is_open()) {
      throw std::runtime_error("Cannot open file: " + path);
    }
  }

  // Write data to buffer
  void write(const char* data, size_t len) {
    buffer_.append(data, len);
    if (buffer_.size() > flushThreshold_) {
      flush();  // auto-flush when buffer is large
    }
  }

  // Public flush — CAN throw, client CAN handle
  void flush() {
    if (!buffer_.empty()) {
      file_.write(buffer_.data(), buffer_.size());
      if (file_.fail()) {
        throw std::runtime_error("Write to file failed");
      }
      file_.flush();
      if (file_.fail()) {
        throw std::runtime_error("Flush to file failed");
      }
      buffer_.clear();
      flushed_ = true;
    }
  }

  // Public close — CAN throw, client CAN handle
  void close() {
    flush();       // write remaining data
    file_.close();
    if (file_.fail()) {
      throw std::runtime_error("Close file failed");
    }
  }

  // Destructor — safety net, NEVER throws
  ~BufferedFileWriter() {
    if (file_.is_open()) {
      try {
        if (!buffer_.empty()) {
          file_.write(buffer_.data(), buffer_.size());
          file_.flush();
        }
        file_.close();
      } catch (...) {
        // Last resort — data may be lost, but program doesn't crash
        std::cerr << "WARNING: Could not flush/close file in destructor\n";
      }
    }
  }

private:
  std::ofstream file_;
  std::string buffer_;
  bool flushed_;
  static constexpr size_t flushThreshold_ = 4096;
};

void example() {
  BufferedFileWriter writer("/tmp/output.bin");
  writer.write("important data", 14);
  writer.write("more data", 9);

  try {
    writer.close();  // Explicit close — can handle errors
    std::cout << "Data safely written to disk\n";
  } catch (const std::exception& e) {
    std::cerr << "WRITE FAILED: " << e.what() << "\n";
    // Take corrective action: retry, write to backup location, etc.
  }
}
```

### Real-World Example: Transaction Scope Guard

```cpp
class TransactionGuard {
public:
  explicit TransactionGuard(Database& db)
  : db_(db), committed_(false) {
    db_.beginTransaction();
  }

  void commit() {
    db_.commitTransaction();  // might throw — client handles it
    committed_ = true;
  }

  // Destructor rolls back if not committed — safe fallback
  ~TransactionGuard() {
    if (!committed_) {
      try {
        db_.rollbackTransaction();
      } catch (const std::exception& e) {
        // Rollback failed in destructor — log but don't throw
        std::cerr << "CRITICAL: Rollback failed: " << e.what() << "\n";
        // At this point we may have an inconsistent DB state
        // but throwing from destructor would be worse
      }
    }
  }

private:
  Database& db_;
  bool committed_;
};

void transferFunds(Database& db, int from, int to, double amount) {
  TransactionGuard txn(db);

  db.execute("UPDATE accounts SET balance = balance - ? WHERE id = ?",
             amount, from);
  db.execute("UPDATE accounts SET balance = balance + ? WHERE id = ?",
             amount, to);

  txn.commit();  // If this throws, the destructor will rollback
  // If any db.execute() throws, destructor runs and rolls back automatically
}
```

### Things to Remember

- Destructors should never emit exceptions. If functions called in a destructor may throw, the destructor 
should catch them and either swallow them or terminate the program.
- If clients need the ability to react to exceptions thrown during a cleanup operation, provide a separate 
function (like `close()` or `flush()`) that they can call before the destructor runs.
- The destructor then serves as a last-resort safety net, not the primary mechanism for error-prone 
operations.

---

## Item 9: Never Call Virtual Functions During Construction or Destruction

### Core Concept

During base class construction, virtual functions **do not** behave polymorphically. When a base class 
constructor is executing, the object's dynamic type is the **base class**, not the derived class. Virtual 
function calls resolve to the base class version. The same is true during base class destruction. This is not 
a bug — it is a deliberate design decision, because the derived class's members have not yet been initialized 
(during construction) or have already been destroyed (during destruction).

### The Problem: Virtual Calls in Constructors

```cpp
// BAD: Calling a virtual function in a constructor
class Transaction {
public:
  Transaction() {
    // ... setup code ...
    logTransaction();  // Virtual call — but which version runs?
  }

  virtual void logTransaction() const {
    std::cout << "Logging base Transaction\n";
  }

  virtual ~Transaction() {}
};

class BuyTransaction : public Transaction {
public:
  BuyTransaction(const std::string& stock, int shares)
  : stock_(stock), shares_(shares) {
    // Before this body runs, Transaction::Transaction() already ran
    // and called logTransaction() — but BuyTransaction's version? NO!
  }

  void logTransaction() const override {
    // This version is NEVER called from the base constructor
    std::cout << "BUY " << shares_ << " shares of " << stock_ << "\n";
  }

private:
  std::string stock_;
  int shares_;
};

void demonstrate() {
  BuyTransaction bt("AAPL", 100);
  // Output: "Logging base Transaction"
  // NOT: "BUY 100 shares of AAPL"
  //
  // During Transaction::Transaction(), the object's type IS Transaction,
  // not BuyTransaction. BuyTransaction's members (stock_, shares_) don't
  // even exist yet — they haven't been initialized!
}
```

### Why This Behavior Exists

The rationale is safety. During `Transaction::Transaction()`:

1. The `BuyTransaction` part of the object has not been constructed yet.
2. `BuyTransaction::stock_` and `BuyTransaction::shares_` are **uninitialized**.
3. If `BuyTransaction::logTransaction()` were called, it would access `stock_` and `shares_` — reading 
uninitialized memory.
4. C++ prevents this by treating the object as a `Transaction` during `Transaction`'s constructor.

```cpp
// What would happen if C++ DID allow derived virtual calls in base ctor:
class Derived : public Base {
public:
  Derived() : data_(new int[100]) {}  // data_ not yet allocated

  void doWork() override {
    // If called from Base::Base(), data_ is UNINITIALIZED
    data_[0] = 42;  // Writing to a random memory address — CRASH
  }

private:
  int* data_;
};
```

### The Problem Gets Worse: Indirect Virtual Calls

The danger is not always obvious. The constructor might call a non-virtual function that internally calls a 
virtual function:

```cpp
// BAD: Indirect virtual call — harder to spot
class Transaction {
public:
  Transaction() {
    init();  // Non-virtual — but calls a virtual function inside!
  }

  virtual ~Transaction() {}

private:
  void init() {
    // ... common setup ...
    logTransaction();  // VIRTUAL CALL during construction!
    // Still resolves to Transaction::logTransaction()
  }

  virtual void logTransaction() const = 0;  // pure virtual!
};

class SellTransaction : public Transaction {
public:
  SellTransaction() {}

  void logTransaction() const override {
    std::cout << "SELL transaction logged\n";
  }
};

void test() {
  // SellTransaction st;  // RUNTIME ERROR or UNDEFINED BEHAVIOR
  // Transaction::Transaction() calls init() which calls logTransaction()
  // logTransaction() is pure virtual in Transaction
  // Calling a pure virtual function => typically std::terminate() / crash
  // Some compilers: "pure virtual function called" error message
}
```

### The Same Problem in Destructors

Virtual functions during destruction have the same issue, in reverse order:

```cpp
class Transaction {
public:
  virtual ~Transaction() {
    logTransaction();  // Virtual call during destruction
    // By the time Transaction::~Transaction() runs,
    // the derived part (BuyTransaction) has ALREADY been destroyed
    // So this calls Transaction::logTransaction(), not the derived version
  }

  virtual void logTransaction() const {
    std::cout << "Base transaction cleanup\n";
  }
};

class BuyTransaction : public Transaction {
public:
  BuyTransaction() : stock_("AAPL") {}

  ~BuyTransaction() override {
    std::cout << "BuyTransaction destroyed\n";
    // After this, stock_ is destroyed, then Transaction::~Transaction() runs
  }

  void logTransaction() const override {
    std::cout << "Logging BUY of " << stock_ << "\n";  // stock_ is destroyed!
  }

private:
  std::string stock_;
};

void test() {
  BuyTransaction* bt = new BuyTransaction();
  delete bt;
  // Output:
  //   "BuyTransaction destroyed"       (BuyTransaction::~BuyTransaction)
  //   "Base transaction cleanup"        (Transaction::~Transaction calls
  //                                      Transaction::logTransaction, NOT
  //                                      BuyTransaction::logTransaction)
}
```

### Solution 1: Pass Information Up to the Base Class

Instead of calling down (via virtual functions), pass information **up** (via constructor parameters).

```cpp
// GOOD: Pass derived-class-specific data up to the base constructor
class Transaction {
public:
  explicit Transaction(const std::string& logInfo) {
    logTransaction(logInfo);  // Non-virtual call — safe
  }

  virtual ~Transaction() {}

  // Non-virtual — no polymorphism needed
  void logTransaction(const std::string& info) const {
    std::cout << "Transaction: " << info << "\n";
    // Write to log file, database, etc.
  }
};

class BuyTransaction : public Transaction {
public:
  BuyTransaction(const std::string& stock, int shares)
    : Transaction(createLogString(stock, shares)),  // pass info UP
    stock_(stock), shares_(shares) {}

private:
  // Static helper — can be called before the object is fully constructed
  // because it doesn't access any member variables
  static std::string createLogString(const std::string& stock, int shares) {
    return "BUY " + std::to_string(shares) + " shares of " + stock;
  }

  std::string stock_;
  int shares_;
};

class SellTransaction : public Transaction {
public:
  SellTransaction(const std::string& stock, int shares)
    : Transaction(createLogString(stock, shares)),
    stock_(stock), shares_(shares) {}

private:
  static std::string createLogString(const std::string& stock, int shares) {
    return "SELL " + std::to_string(shares) + " shares of " + stock;
  }

  std::string stock_;
  int shares_;
};

void test() {
  BuyTransaction bt("AAPL", 100);
  // Output: "Transaction: BUY 100 shares of AAPL" — correct!

  SellTransaction st("GOOG", 50);
  // Output: "Transaction: SELL 50 shares of GOOG" — correct!
}
```

**Note the use of a `static` helper function:** The function `createLogString` is `static`, so it doesn't 
depend on any member of the not-yet-constructed derived object. This is critical for safety.

### Solution 2: Post-Construction Initialization

Use a two-phase initialization pattern where virtual dispatch works correctly:

```cpp
// GOOD: Two-phase initialization with factory function
class Widget {
public:
  virtual ~Widget() = default;

  // Factory method ensures init() is called AFTER construction
  template<typename T, typename... Args>
  static std::unique_ptr<T> create(Args&&... args) {
    auto widget = std::unique_ptr<T>(new T(std::forward<Args>(args)...));
    widget->init();  // Virtual call AFTER full construction — safe!
    return widget;
  }

  virtual void doWork() = 0;

protected:
  Widget() {}  // Protected — force use of factory

  // Called after construction — virtual dispatch works correctly
  virtual void init() {
    std::cout << "Widget base init\n";
  }
};

class FancyWidget : public Widget {
public:
  void doWork() override {
    std::cout << "FancyWidget doing work with buffer of size " << bufferSize_ << "\n";
  }

protected:
  FancyWidget() : bufferSize_(0), buffer_(nullptr) {}

  void init() override {
    Widget::init();  // call base init
    bufferSize_ = 1024;
    buffer_ = new char[bufferSize_];
    std::cout << "FancyWidget initialized with buffer\n";
  }

  friend class Widget;  // allow Widget::create to call constructor

private:
  size_t bufferSize_;
  char* buffer_;
};

void test() {
  auto w = Widget::create<FancyWidget>();
  // Output:
  //   "Widget base init"
  //   "FancyWidget initialized with buffer"
  w->doWork();
  // Output: "FancyWidget doing work with buffer of size 1024"
}
```

### Real-World Example: GUI Widget Hierarchy

```cpp
// BAD version — virtual calls in constructor
class GUIWidget {
public:
  GUIWidget(int x, int y, int width, int height)
  : x_(x), y_(y), width_(width), height_(height) {
    // These virtual calls don't dispatch to derived classes!
    applyDefaultStyle();      // virtual — BAD
    calculateLayout();        // virtual — BAD
    registerEventHandlers();  // virtual — BAD
  }

  virtual ~GUIWidget() = default;
  virtual void applyDefaultStyle() { /* base style */ }
  virtual void calculateLayout() { /* base layout */ }
  virtual void registerEventHandlers() { /* base handlers */ }

protected:
  int x_, y_, width_, height_;
};

class Button : public GUIWidget {
public:
  Button(int x, int y, int w, int h, const std::string& label)
  : GUIWidget(x, y, w, h), label_(label) {}

  void applyDefaultStyle() override {
    // This is NEVER called from GUIWidget's constructor!
    // label_ is uninitialized when GUIWidget ctor runs
    std::cout << "Button style for: " << label_ << "\n";
  }

  void calculateLayout() override {
    // Calculates text position — but label_ doesn't exist yet!
    textWidth_ = label_.length() * 8;  // ACCESSING UNINITIALIZED MEMBER
  }

  void registerEventHandlers() override {
    onClick_ = [this]() { std::cout << "Clicked: " << label_ << "\n"; };
  }

private:
  std::string label_;
  int textWidth_;
  std::function<void()> onClick_;
};

// GOOD version — pass info up, or use post-construction init
class GUIWidget {
public:
  virtual ~GUIWidget() = default;

  // Factory with post-construction initialization
  template<typename T, typename... Args>
  static std::unique_ptr<T> create(Args&&... args) {
    auto widget = std::unique_ptr<T>(new T(std::forward<Args>(args)...));
    widget->applyDefaultStyle();
    widget->calculateLayout();
    widget->registerEventHandlers();
    return widget;
  }

  virtual void applyDefaultStyle() {}
  virtual void calculateLayout() {}
  virtual void registerEventHandlers() {}

protected:
  GUIWidget(int x, int y, int width, int height)
  : x_(x), y_(y), width_(width), height_(height) {}

  int x_, y_, width_, height_;
};

class Button : public GUIWidget {
protected:
  friend class GUIWidget;
  Button(int x, int y, int w, int h, const std::string& label)
  : GUIWidget(x, y, w, h), label_(label) {}

public:
  void applyDefaultStyle() override {
    std::cout << "Button style for: " << label_ << "\n";  // label_ is valid!
  }

  void calculateLayout() override {
    textWidth_ = label_.length() * 8;  // Safe — label_ exists
  }

  void registerEventHandlers() override {
    onClick_ = [this]() { std::cout << "Clicked: " << label_ << "\n"; };
  }

private:
  std::string label_;
  int textWidth_ = 0;
  std::function<void()> onClick_;
};

void test() {
  auto btn = GUIWidget::create<Button>(10, 20, 100, 30, "OK");
  // All virtual functions called AFTER full construction — correct behavior
}
```

### Things to Remember

- Don't call virtual functions during construction or destruction. During base class construction/destruction, 
virtual functions resolve to the base class version, never the derived class version.
- This behavior exists for safety: during base class construction, derived class members are uninitialized; 
during base class destruction, they have already been destroyed.
- Instead of virtual calls in constructors, pass derived-class-specific information **up** to the base class 
constructor (using static helper functions if necessary).
- Alternatively, use a post-construction initialization pattern (e.g., factory functions that call virtual 
`init()` after the object is fully constructed).

---

## Item 10: Have Assignment Operators Return a Reference to `*this`

### Core Concept

C++ built-in types support **chained assignment**:

```cpp
int x, y, z;
x = y = z = 15;  // Right-to-left: z = 15, then y = z, then x = y
```

This works because assignment returns a reference to the left-hand operand. For your user-defined types to 
support the same convention, your assignment operators should return a reference to `*this`.

### The Convention

```cpp
class Widget {
public:
  // Copy assignment operator
  Widget& operator=(const Widget& rhs) {
    // ... do the assignment work ...
    return *this;   // return reference to left-hand object
  }

  // Move assignment operator
  Widget& operator=(Widget&& rhs) noexcept {
    // ... do the move ...
    return *this;   // same convention
  }

  // Assignment from other types
  Widget& operator=(int value) {
    // ... assign from int ...
    return *this;   // same convention
  }
};
```

### Why This Matters

```cpp
// Without returning *this, chaining doesn't work
class BadWidget {
public:
  void operator=(const BadWidget& rhs) {  // returns void — BAD
    data_ = rhs.data_;
    // no return statement
  }
private:
  int data_;
};

BadWidget a, b, c;
// a = b = c;  // ERROR: b = c returns void, can't assign void to a

// With returning *this, chaining works naturally
class GoodWidget {
public:
  GoodWidget& operator=(const GoodWidget& rhs) {  // returns reference — GOOD
    data_ = rhs.data_;
    return *this;
  }
private:
  int data_;
};

GoodWidget x, y, z;
x = y = z;  // Works: z assigned to y (returns y), then y assigned to x (returns x)
```

### Applies to ALL Assignment Operators

This convention applies to all assignment-like operators, not just `operator=`:

```cpp
class Matrix {
public:
  Matrix(int rows, int cols)
  : rows_(rows), cols_(cols), data_(rows * cols, 0.0) {}

  // Copy assignment
  Matrix& operator=(const Matrix& rhs) {
    if (this != &rhs) {
      rows_ = rhs.rows_;
      cols_ = rhs.cols_;
      data_ = rhs.data_;
    }
    return *this;
  }

  // Compound assignment operators — same convention
  Matrix& operator+=(const Matrix& rhs) {
    for (size_t i = 0; i < data_.size(); ++i) {
      data_[i] += rhs.data_[i];
    }
    return *this;
  }

  Matrix& operator-=(const Matrix& rhs) {
    for (size_t i = 0; i < data_.size(); ++i) {
      data_[i] -= rhs.data_[i];
    }
    return *this;
  }

  Matrix& operator*=(double scalar) {
    for (auto& val : data_) {
      val *= scalar;
    }
    return *this;
  }

  // Assignment from initializer list
  Matrix& operator=(std::initializer_list<double> values) {
    size_t i = 0;
    for (auto val : values) {
      if (i >= data_.size()) break;
      data_[i++] = val;
    }
    return *this;
  }

private:
  int rows_, cols_;
  std::vector<double> data_;
};

void example() {
  Matrix a(2, 2), b(2, 2), c(2, 2);
  a = b = c;        // chained assignment
  (a += b) *= 2.0;  // compound assignment chaining
  a = {1.0, 2.0, 3.0, 4.0};  // initializer list assignment
}
```

### Real-World Example: String Class

```cpp
class MyString {
public:
  MyString() : data_(nullptr), len_(0) {}

  MyString(const char* s) {
    len_ = std::strlen(s);
    data_ = new char[len_ + 1];
    std::strcpy(data_, s);
  }

  ~MyString() { delete[] data_; }

  // Copy assignment — returns *this
  MyString& operator=(const MyString& rhs) {
    if (this != &rhs) {
      delete[] data_;
      len_ = rhs.len_;
      data_ = new char[len_ + 1];
      std::strcpy(data_, rhs.data_);
    }
    return *this;
  }

  // Move assignment — returns *this
  MyString& operator=(MyString&& rhs) noexcept {
    if (this != &rhs) {
      delete[] data_;
      data_ = rhs.data_;
      len_ = rhs.len_;
      rhs.data_ = nullptr;
      rhs.len_ = 0;
    }
    return *this;
  }

  // Assignment from C-string — returns *this
  MyString& operator=(const char* s) {
    MyString temp(s);
    std::swap(data_, temp.data_);
    std::swap(len_, temp.len_);
    return *this;
  }

  // Append — returns *this
  MyString& operator+=(const MyString& rhs) {
    size_t newLen = len_ + rhs.len_;
    char* newData = new char[newLen + 1];
    std::strcpy(newData, data_);
    std::strcat(newData, rhs.data_);
    delete[] data_;
    data_ = newData;
    len_ = newLen;
    return *this;
  }

private:
  char* data_;
  size_t len_;
};

void test() {
  MyString a("Hello"), b, c;

  // All of these work because each operator returns *this:
  c = b = a;           // chain assignment
  (a += MyString(" World")) += MyString("!");  // chain append
  a = "Reset";         // assign from C-string
}
```

### Things to Remember

- Have assignment operators return a reference to `*this`. This is a convention followed by all built-in types 
and all standard library types (like `std::string`, `std::vector`, etc.).
- This applies to all forms of assignment: `operator=`, `operator+=`, `operator-=`, `operator*=`, and so 
forth.
- While returning by value or `const` reference would technically compile, it breaks chaining and contradicts 
universal convention.

---

## Item 11: Handle Assignment to Self in `operator=`

### Core Concept

Self-assignment (`a = a`) happens more often than you might think, and it can be catastrophic if your 
`operator=` doesn't handle it. When an object manages resources, a naive `operator=` that deletes the old 
resource before copying the new one will **delete the resource it's supposed to copy from** during 
self-assignment.

### How Self-Assignment Happens

Self-assignment is not always as obvious as `w = w`:

```cpp
Widget w;
w = w;  // Obvious self-assignment

// Less obvious cases:
Widget* a = &w;
Widget* b = &w;     // a and b point to the same object
*a = *b;            // Self-assignment!

// Through references:
void process(Widget& lhs, Widget& rhs) {
  lhs = rhs;     // Self-assignment if lhs and rhs refer to same object
}
process(w, w);      // Oops

// Through containers:
std::vector<Widget> widgets(10);
int i = 3, j = 3;
widgets[i] = widgets[j];  // Self-assignment if i == j

// Through inheritance:
class Derived : public Base { /* ... */ };
Derived d;
Base& br = d;
br = d;  // Self-assignment! Both refer to same object
```

### The Problem: Naive operator=

```cpp
// BAD: Unsafe self-assignment
class Bitmap { /* large image data */ };

class Widget {
public:
  Widget(Bitmap* pb) : pb_(pb) {}

  Widget& operator=(const Widget& rhs) {
    delete pb_;             // Step 1: delete current bitmap
    pb_ = new Bitmap(*rhs.pb_);  // Step 2: copy rhs's bitmap
    return *this;
  }

  ~Widget() { delete pb_; }

private:
  Bitmap* pb_;  // heap-allocated bitmap
};

void disaster() {
  Bitmap* bm = new Bitmap();
  Widget w(bm);
  w = w;  // SELF-ASSIGNMENT!
  // Step 1: delete pb_ — destroys the only Bitmap
  // Step 2: pb_ = new Bitmap(*rhs.pb_) — rhs.pb_ IS pb_ IS DELETED
  //         Dereferencing a deleted pointer — UNDEFINED BEHAVIOR
}
```

### Solution 1: Identity Test (Partial Fix)

```cpp
// PARTIAL FIX: Identity test
class Widget {
public:
  Widget& operator=(const Widget& rhs) {
    if (this == &rhs) return *this;  // Identity test — handle self-assignment

    delete pb_;
    pb_ = new Bitmap(*rhs.pb_);  // What if this throws? pb_ is dangling!
    return *this;
  }

private:
  Bitmap* pb_;
};
```

This handles self-assignment but is **not exception-safe**. If `new Bitmap(*rhs.pb_)` throws (out of memory, 
for example), `this->pb_` is left pointing to deleted memory.

### Solution 2: Copy-and-Swap (Preferred — Both Self-Assignment-Safe AND Exception-Safe)

```cpp
// GOOD: Copy-and-swap idiom
class Widget {
public:
  Widget(Bitmap* pb = nullptr) : pb_(pb) {}

  Widget(const Widget& rhs) : pb_(new Bitmap(*rhs.pb_)) {}

  Widget& operator=(const Widget& rhs) {
    Widget temp(rhs);      // Step 1: copy rhs into a temporary
    swap(temp);            // Step 2: swap this with the temporary
    return *this;          // Step 3: temp (holding old data) is destroyed
  }

  // Or even more concise — pass by value (copy made by caller):
  // Widget& operator=(Widget rhs) {  // rhs is a copy
  //     swap(rhs);
  //     return *this;
  // }

  ~Widget() { delete pb_; }

  void swap(Widget& other) noexcept {
    using std::swap;
    swap(pb_, other.pb_);
  }

private:
  Bitmap* pb_;
};

void test() {
  Widget w1(new Bitmap());
  w1 = w1;  // Safe!
  // temp is constructed as a copy of w1
  // swap exchanges pb_ pointers
  // temp destroys the old pb_ — which is a valid copy
  // No dangling pointers, no double deletes

  Widget w2(new Bitmap());
  w1 = w2;  // Also safe, and exception-safe
  // If new Bitmap() in copy ctor throws, w1 is unchanged
}
```

### Solution 3: Careful Ordering (Exception-Safe Without Copy-and-Swap)

```cpp
// GOOD: Exception-safe via careful ordering
class Widget {
public:
  Widget& operator=(const Widget& rhs) {
    Bitmap* pOrig = pb_;           // Step 1: remember old pointer
    pb_ = new Bitmap(*rhs.pb_);    // Step 2: copy rhs's bitmap FIRST
    //   If this throws, pb_ still points
    //   to the original bitmap — safe!
    delete pOrig;                  // Step 3: delete old bitmap
    return *this;
  }

private:
  Bitmap* pb_;
};

// Self-assignment analysis:
// w = w;
// pOrig = pb_           (save pointer to our bitmap)
// pb_ = new Bitmap(*pb_) (copy our own bitmap — it's still valid)
// delete pOrig          (delete old bitmap — it's a different object now)
// Everything is fine!
```

This approach handles self-assignment correctly **without** an identity test, and it's exception-safe. The 
identity test (`if (this == &rhs)`) can still be added as an optimization for the self-assignment case, but 
it's not required for correctness.

### Real-World Example: Resource-Managing Class with Multiple Resources

```cpp
class TextDocument {
public:
  TextDocument(const std::string& content, const std::string& fontPath)
    : text_(new std::string(content)),
    font_(new Font(fontPath)),
    metadata_(new Metadata()) {}

  TextDocument(const TextDocument& rhs)
    : text_(new std::string(*rhs.text_)),
    font_(new Font(*rhs.font_)),
    metadata_(new Metadata(*rhs.metadata_)) {}

  ~TextDocument() {
    delete text_;
    delete font_;
    delete metadata_;
  }

  // BAD: Unsafe with multiple resources
  // If font copy throws after text was already replaced, we have
  // a partially-assigned, inconsistent object
  TextDocument& BAD_operator_assign(const TextDocument& rhs) {
    if (this == &rhs) return *this;
    delete text_;
    text_ = new std::string(*rhs.text_);  // OK so far
    delete font_;
    font_ = new Font(*rhs.font_);          // If this THROWS: text_ has new
    // value but font_ is deleted!
    // Object is in an inconsistent state
    delete metadata_;
    metadata_ = new Metadata(*rhs.metadata_);
    return *this;
  }

  // GOOD: Copy-and-swap — atomic, exception-safe, self-assignment-safe
  TextDocument& operator=(const TextDocument& rhs) {
    TextDocument temp(rhs);  // All-or-nothing copy
    swap(temp);              // noexcept swap
    return *this;            // temp cleans up old data
  }

  void swap(TextDocument& other) noexcept {
    using std::swap;
    swap(text_, other.text_);
    swap(font_, other.font_);
    swap(metadata_, other.metadata_);
  }

private:
  std::string* text_;
  Font* font_;
  Metadata* metadata_;
};
```

### Real-World Example: Smart Array with Copy-and-Swap

```cpp
template<typename T>
class Array {
public:
  explicit Array(size_t size = 0)
  : size_(size), data_(size ? new T[size] : nullptr) {}

  Array(const Array& rhs)
  : size_(rhs.size_), data_(rhs.size_ ? new T[rhs.size_] : nullptr) {
    std::copy(rhs.data_, rhs.data_ + size_, data_);
  }

  // Pass-by-value copy-and-swap (combines copy ctor + swap)
  Array& operator=(Array rhs) {  // rhs is a COPY — copy already made
    swap(rhs);                 // swap with the copy
    return *this;              // old data destroyed when rhs goes out of scope
  }

  // Move constructor
  Array(Array&& rhs) noexcept
  : size_(rhs.size_), data_(rhs.data_) {
    rhs.size_ = 0;
    rhs.data_ = nullptr;
  }

  ~Array() { delete[] data_; }

  T& operator[](size_t index) { return data_[index]; }
  const T& operator[](size_t index) const { return data_[index]; }
  size_t size() const { return size_; }

  void swap(Array& other) noexcept {
    using std::swap;
    swap(size_, other.size_);
    swap(data_, other.data_);
  }

private:
  size_t size_;
  T* data_;
};

// ADL-findable swap for use with std::swap
template<typename T>
void swap(Array<T>& a, Array<T>& b) noexcept {
  a.swap(b);
}

void test() {
  Array<int> a(100);
  for (size_t i = 0; i < 100; ++i) a[i] = static_cast<int>(i);

  a = a;  // Self-assignment — safe!
  // operator= receives a copy of a (by value)
  // Swaps internal state with the copy
  // Copy (holding old data) is destroyed
  // a still contains 0..99

  Array<int> b(50);
  b = std::move(a);  // Move — also works through copy-and-swap
  // rhs is move-constructed (no copy), then swapped
}
```

### Things to Remember

- Make sure `operator=` is well-behaved when an object is assigned to itself. Techniques include comparing 
addresses of source and target objects, careful statement ordering, and copy-and-swap.
- Make sure that any function operating on more than one object behaves correctly if two or more of the 
objects are actually the same object.
- The copy-and-swap idiom is the gold standard — it provides self-assignment safety and exception safety in 
one clean technique.

---

## Item 12: Copy All Parts of an Object

### Core Concept

When you write your own copy constructor or copy assignment operator, you are taking full responsibility for 
copying. The compiler will not warn you if you forget to copy a member. Two common bugs arise: **(1)** 
forgetting to copy a newly added data member, and **(2)** forgetting to copy the base class part of a derived 
class. Both lead to **partial copies** — objects that look fully constructed but have uninitialized or 
default-initialized members.

### Bug 1: Forgetting to Copy New Members

```cpp
class Customer {
public:
  Customer(const std::string& name) : name_(name) {}

  Customer(const Customer& rhs) : name_(rhs.name_) {}

  Customer& operator=(const Customer& rhs) {
    name_ = rhs.name_;
    return *this;
  }

private:
  std::string name_;
};
// Everything is fine so far...

// Months later, a new member is added:
class Customer {
public:
  Customer(const std::string& name, int priority)
  : name_(name), priority_(priority) {}

  // OOPS: Copy constructor was NOT updated!
  Customer(const Customer& rhs) : name_(rhs.name_) {
    // priority_ is NOT copied — it's default-initialized (0 or garbage)
  }

  // OOPS: Copy assignment was NOT updated!
  Customer& operator=(const Customer& rhs) {
    name_ = rhs.name_;
    // priority_ is NOT assigned — the target keeps its old value
    return *this;
  }

private:
  std::string name_;
  int priority_;    // NEW MEMBER — but copy operations don't know about it!
};

void demonstrate() {
  Customer c1("Alice", 5);    // priority_ = 5
  Customer c2(c1);            // c2.priority_ = 0 or garbage — NOT 5!
  Customer c3("Bob", 1);
  c3 = c1;                    // c3.priority_ is still 1, NOT 5!
}
```

The compiler will **not** warn you about this. It generated the copy operations itself before, and it 
considers the fact that you've written them to mean you know what you're doing.

**The fix is obvious but easy to forget:**

```cpp
// GOOD: Copy ALL members
class Customer {
public:
  Customer(const std::string& name, int priority)
  : name_(name), priority_(priority) {}

  Customer(const Customer& rhs)
    : name_(rhs.name_),
    priority_(rhs.priority_) {}  // DON'T FORGET THIS!

  Customer& operator=(const Customer& rhs) {
    name_ = rhs.name_;
    priority_ = rhs.priority_;     // DON'T FORGET THIS!
    return *this;
  }

private:
  std::string name_;
  int priority_;
};
```

### Bug 2: Forgetting to Copy the Base Class Part

This is the more insidious bug. When writing copy operations for a derived class, you must explicitly copy the 
base class portion.

```cpp
class PriorityCustomer : public Customer {
public:
  PriorityCustomer(const std::string& name, int priority, int vipLevel)
  : Customer(name, priority), vipLevel_(vipLevel) {}

  // BAD: Copies derived part but FORGETS base part
  PriorityCustomer(const PriorityCustomer& rhs)
  : vipLevel_(rhs.vipLevel_) {
    // Customer base class is DEFAULT-CONSTRUCTED (if possible)
    // rhs.name_ and rhs.priority_ are NOT copied!
    // The base class portion of this object has empty name and 0 priority
  }

  // BAD: Assigns derived part but FORGETS base part
  PriorityCustomer& operator=(const PriorityCustomer& rhs) {
    vipLevel_ = rhs.vipLevel_;
    // Customer::operator= is NOT called!
    // name_ and priority_ are NOT assigned!
    return *this;
  }

private:
  int vipLevel_;
};

void bug() {
  PriorityCustomer pc1("VIP Alice", 10, 3);
  PriorityCustomer pc2(pc1);
  // pc2.vipLevel_ == 3 (copied)
  // pc2.name_ == "" (NOT copied — default constructed)
  // pc2.priority_ == 0 (NOT copied — default constructed)

  PriorityCustomer pc3("Regular", 1, 1);
  pc3 = pc1;
  // pc3.vipLevel_ == 3 (assigned)
  // pc3.name_ is still "Regular" (NOT assigned!)
  // pc3.priority_ is still 1 (NOT assigned!)
}
```

### The Fix: Explicitly Call Base Class Copy Operations

```cpp
// GOOD: Copy ALL parts — including the base class
class PriorityCustomer : public Customer {
public:
  PriorityCustomer(const std::string& name, int priority, int vipLevel)
  : Customer(name, priority), vipLevel_(vipLevel) {}

  // Copy constructor: invoke base class copy constructor
  PriorityCustomer(const PriorityCustomer& rhs)
    : Customer(rhs),              // IMPORTANT: copy the base class part!
    vipLevel_(rhs.vipLevel_) {   // copy the derived class part
    // Customer's copy ctor receives a PriorityCustomer& but takes
    // a const Customer& — slicing extracts the Customer part
  }

  // Copy assignment: invoke base class operator=
  PriorityCustomer& operator=(const PriorityCustomer& rhs) {
    Customer::operator=(rhs);      // IMPORTANT: assign the base class part!
    vipLevel_ = rhs.vipLevel_;     // assign the derived class part
    return *this;
  }

private:
  int vipLevel_;
};
```

### Don't Implement One in Terms of the Other

A common temptation is to avoid code duplication by having the copy constructor call `operator=` or vice 
versa. Both are wrong:

```cpp
// BAD: Copy constructor calling operator=
class Widget {
public:
  Widget(const Widget& rhs) {
    *this = rhs;  // Calls operator= on a not-yet-fully-constructed object!
    // operator= may delete resources that were never allocated
    // (because ctor hasn't finished initializing them)
  }

  Widget& operator=(const Widget& rhs) {
    if (this == &rhs) return *this;
    delete data_;                    // Deletes uninitialized pointer in copy ctor!
    data_ = new int(*rhs.data_);
    return *this;
  }

private:
  int* data_;
};

// BAD: operator= calling copy constructor (via placement new)
class Widget {
public:
  Widget& operator=(const Widget& rhs) {
    this->~Widget();                     // Destroy current object
    new (this) Widget(rhs);              // Construct a new one in the same memory
    // If the copy ctor throws, the object is in a destroyed state!
    // Any subsequent access (including the destructor) is undefined behavior
    return *this;
  }
};
```

**The correct approach: extract common code into a private helper:**

```cpp
// GOOD: Common code in a private init/copyFrom function
class Widget {
public:
  Widget(int value, const std::string& name)
  : data_(new int(value)), name_(name), cache_(nullptr) {
    rebuildCache();
  }

  Widget(const Widget& rhs)
    : data_(new int(*rhs.data_)),   // allocate and copy
    name_(rhs.name_),
    cache_(nullptr) {
    rebuildCache();                  // shared logic in private helper
  }

  Widget& operator=(const Widget& rhs) {
    if (this == &rhs) return *this;

    int* newData = new int(*rhs.data_);  // copy first (exception safety)
    delete data_;                         // then delete old
    data_ = newData;
    name_ = rhs.name_;
    rebuildCache();                       // shared logic in private helper
    return *this;
  }

  ~Widget() {
    delete data_;
    delete cache_;
  }

private:
  void rebuildCache() {
    delete cache_;
    cache_ = new CacheData(*data_, name_);
  }

  int* data_;
  std::string name_;
  CacheData* cache_;
};
```

### Real-World Example: Deep Hierarchy

```cpp
class Shape {
public:
  Shape(const Color& color, double opacity)
  : color_(color), opacity_(opacity) {}

  Shape(const Shape& rhs)
  : color_(rhs.color_), opacity_(rhs.opacity_) {}

  Shape& operator=(const Shape& rhs) {
    color_ = rhs.color_;
    opacity_ = rhs.opacity_;
    return *this;
  }

  virtual ~Shape() = default;

protected:
  Color color_;
  double opacity_;
};

class Polygon : public Shape {
public:
  Polygon(const Color& color, double opacity, std::vector<Point> vertices)
  : Shape(color, opacity), vertices_(std::move(vertices)) {}

  Polygon(const Polygon& rhs)
    : Shape(rhs),                           // copy Shape part
    vertices_(rhs.vertices_) {}            // copy Polygon part

  Polygon& operator=(const Polygon& rhs) {
    Shape::operator=(rhs);                   // assign Shape part
    vertices_ = rhs.vertices_;               // assign Polygon part
    return *this;
  }

protected:
  std::vector<Point> vertices_;
};

class TexturedPolygon : public Polygon {
public:
  TexturedPolygon(const Color& color, double opacity,
                  std::vector<Point> vertices,
                  const std::string& texturePath)
    : Polygon(color, opacity, std::move(vertices)),
    texture_(new Texture(texturePath)),
    uvCoords_(vertices_.size()) {}

  // Copy constructor — must copy ALL THREE levels
  TexturedPolygon(const TexturedPolygon& rhs)
    : Polygon(rhs),                          // copies Shape AND Polygon parts
    texture_(new Texture(*rhs.texture_)),   // deep copy of texture
    uvCoords_(rhs.uvCoords_) {}             // copy UV coordinates

  // Copy assignment — must assign ALL THREE levels
  TexturedPolygon& operator=(const TexturedPolygon& rhs) {
    Polygon::operator=(rhs);                  // assigns Shape AND Polygon parts

    Texture* newTex = new Texture(*rhs.texture_);  // copy first (exception safe)
    delete texture_;
    texture_ = newTex;
    uvCoords_ = rhs.uvCoords_;

    return *this;
  }

  ~TexturedPolygon() override {
    delete texture_;
  }

private:
  Texture* texture_;
  std::vector<UV> uvCoords_;
};

void test() {
  TexturedPolygon tp1(Color::Red, 0.8,
                      {{0,0}, {1,0}, {1,1}},
                      "brick.png");

  TexturedPolygon tp2(tp1);  // Copies ALL parts:
  // Shape:           color_ = Red, opacity_ = 0.8
  // Polygon:         vertices_ = {{0,0},{1,0},{1,1}}
  // TexturedPolygon: texture_ = deep copy of brick texture,
  //                  uvCoords_ = copied

  TexturedPolygon tp3(Color::Blue, 0.5,
                      {{0,0}, {2,0}, {2,2}, {0,2}},
                      "stone.png");
  tp3 = tp1;  // Assigns ALL parts — nothing is left behind
}
```

### Real-World Example: Configuration Object with Many Members

```cpp
class ServerConfig {
public:
  ServerConfig()
    : host_("localhost"), port_(8080), maxConnections_(100),
    timeout_(30), useTLS_(false), logLevel_(LogLevel::INFO),
    threadPoolSize_(4), maxRequestSize_(1 << 20),
    keepAliveEnabled_(true), keepAliveTimeout_(60),
    compressionEnabled_(false),
    certPath_(""), keyPath_("") {}

  // When there are many members, it's easy to miss one.
  // A disciplined approach: list members in the SAME ORDER as declaration.

  ServerConfig(const ServerConfig& rhs)
    : host_(rhs.host_),
    port_(rhs.port_),
    maxConnections_(rhs.maxConnections_),
    timeout_(rhs.timeout_),
    useTLS_(rhs.useTLS_),
    logLevel_(rhs.logLevel_),
    threadPoolSize_(rhs.threadPoolSize_),
    maxRequestSize_(rhs.maxRequestSize_),
    keepAliveEnabled_(rhs.keepAliveEnabled_),
    keepAliveTimeout_(rhs.keepAliveTimeout_),
    compressionEnabled_(rhs.compressionEnabled_),
    certPath_(rhs.certPath_),
    keyPath_(rhs.keyPath_) {
    // Every. Single. Member. Copied.
    // If someone adds a new member and forgets to add it here,
    // the compiler won't warn — this is a maintenance burden.
  }

  ServerConfig& operator=(const ServerConfig& rhs) {
    host_ = rhs.host_;
    port_ = rhs.port_;
    maxConnections_ = rhs.maxConnections_;
    timeout_ = rhs.timeout_;
    useTLS_ = rhs.useTLS_;
    logLevel_ = rhs.logLevel_;
    threadPoolSize_ = rhs.threadPoolSize_;
    maxRequestSize_ = rhs.maxRequestSize_;
    keepAliveEnabled_ = rhs.keepAliveEnabled_;
    keepAliveTimeout_ = rhs.keepAliveTimeout_;
    compressionEnabled_ = rhs.compressionEnabled_;
    certPath_ = rhs.certPath_;
    keyPath_ = rhs.keyPath_;
    return *this;
  }

  // Modern alternative: if compiler-generated copy is correct
  // (no raw pointers, all members are copyable), just use = default:
  // ServerConfig(const ServerConfig&) = default;
  // ServerConfig& operator=(const ServerConfig&) = default;
  // The compiler copies ALL members — no risk of forgetting one!

private:
  std::string host_;
  int port_;
  int maxConnections_;
  int timeout_;
  bool useTLS_;
  LogLevel logLevel_;
  int threadPoolSize_;
  size_t maxRequestSize_;
  bool keepAliveEnabled_;
  int keepAliveTimeout_;
  bool compressionEnabled_;
  std::string certPath_;
  std::string keyPath_;
};
```

### Checklist: When Writing Copy Operations

Every time you write a copy constructor or copy assignment operator, go through this checklist:

1. **Copy every data member** declared in the class, in the same order they're declared.
2. **Invoke the base class copy operation** — `Base(rhs)` in the copy ctor's initializer list, 
`Base::operator=(rhs)` in `operator=`.
3. **If a new member is added later**, update both the copy constructor AND `operator=`.
4. **Don't implement one in terms of the other.** Extract shared code into a private helper function instead.
5. **Consider whether `= default` is sufficient.** If your class doesn't manage raw resources, 
compiler-generated copy operations may be correct and maintainable.

```cpp
// Modern approach: when possible, use = default and let the compiler do it
class ModernConfig {
public:
  ModernConfig() = default;
  ModernConfig(const ModernConfig&) = default;             // copies ALL members
  ModernConfig& operator=(const ModernConfig&) = default;  // assigns ALL members
  ~ModernConfig() = default;

  // If you add a new member, the compiler automatically includes it
  // in the generated copy operations. No maintenance burden!

private:
  std::string host_ = "localhost";
  int port_ = 8080;
  bool useTLS_ = false;
  // Add a new member here — copy operations automatically updated
};
```

### Things to Remember

- Copying functions should be sure to copy all of an object's data members and all of its base class parts.
- When adding a new data member to a class, update every copy constructor and every copy assignment operator. 
The compiler will not warn you if you forget.
- Don't try to implement one of the copying functions in terms of the other. Instead, put common functionality 
in a third function that both call.
- When your class doesn't manage raw resources, prefer `= default` to hand-written copy operations — the 
compiler will automatically include all members, including ones added later.
