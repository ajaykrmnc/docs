# Item 6: Explicitly Disallow the Use of Compiler-Generated Functions You Do Not Want

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
