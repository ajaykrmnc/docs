# Item 4: Make Sure That Objects Are Initialized Before They're Used

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
