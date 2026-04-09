# Item 8: Prevent Exceptions from Leaving Destructors

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
