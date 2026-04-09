# Item 36: Never redefine an inherited non-virtual function

### The Problem

Non-virtual functions are statically bound. The function called depends on the *declared type* of the pointer or reference, not the *actual type* of the object.

```cpp
// BAD -- redefining a non-virtual function
class Base {
public:
    void doWork() {
        std::cout << "Base::doWork()\n";
    }
};

class Derived : public Base {
public:
    void doWork() {      // hides Base::doWork -- NOT an override!
        std::cout << "Derived::doWork()\n";
    }
};

Derived d;
Base* bp = &d;
Derived* dp = &d;

bp->doWork();    // calls Base::doWork()     -- static binding!
dp->doWork();    // calls Derived::doWork()  -- static binding!
```

Both `bp` and `dp` point to the **same object** `d`, yet they call **different functions**. This is deeply confusing and almost always a bug.

### Why This is Always Wrong

The argument is both theoretical and practical:

**Theoretical argument (from Item 32 and Item 34):**

1. Public inheritance means "is-a" (Item 32).
2. Non-virtual functions establish an invariant over specialization (Item 34).
3. If `Derived` redefines a non-virtual function, either:
   - `Derived` is not really "is-a" `Base` (contradicts point 1), or
   - The function is not really invariant over specialization and should have been virtual (contradicts point 2).

Either way, the design is flawed.

**Practical argument:**

```cpp
// BAD -- causes bizarre behavior in real code
class Document {
public:
    std::string fileExtension() { return ".doc"; }
};

class SpreadSheet : public Document {
public:
    std::string fileExtension() { return ".xls"; }  // redefines non-virtual!
};

void saveToFile(Document& doc) {
    std::string name = "report" + doc.fileExtension();
    // ALWAYS saves as "report.doc" even for SpreadSheets!
    std::cout << "Saving as: " << name << "\n";
}

SpreadSheet ss;
saveToFile(ss);  // Saves as "report.doc" -- WRONG!
```

### The Fix

If the function should differ by type, make it virtual. If it should not differ, do not redefine it.

```cpp
// GOOD -- make it virtual if behavior should vary
class Document {
public:
    virtual ~Document() = default;
    virtual std::string fileExtension() const { return ".doc"; }
};

class SpreadSheet : public Document {
public:
    std::string fileExtension() const override { return ".xls"; }
};

class Presentation : public Document {
public:
    std::string fileExtension() const override { return ".ppt"; }
};

void saveToFile(Document& doc) {
    std::string name = "report" + doc.fileExtension();
    std::cout << "Saving as: " << name << "\n";  // Now correct for all types
}
```

### Another Example: Logger Hierarchy

```cpp
// BAD -- non-virtual function redefined
class Logger {
public:
    void log(const std::string& msg) {
        std::cout << "[INFO] " << msg << "\n";
    }
};

class ErrorLogger : public Logger {
public:
    void log(const std::string& msg) {  // hides Logger::log!
        std::cerr << "[ERROR] " << msg << "\n";
    }
};

void processAndLog(Logger& logger, const std::string& action) {
    // Always calls Logger::log, even if passed an ErrorLogger!
    logger.log("Processing: " + action);
}
```

```cpp
// GOOD -- use virtual functions
class Logger {
public:
    virtual ~Logger() = default;
    virtual void log(const std::string& msg) {
        std::cout << "[INFO] " << msg << "\n";
    }
};

class ErrorLogger : public Logger {
public:
    void log(const std::string& msg) override {
        std::cerr << "[ERROR] " << msg << "\n";
    }
};

class FileLogger : public Logger {
public:
    explicit FileLogger(const std::string& filename)
        : file_(filename) {}

    void log(const std::string& msg) override {
        file_ << msg << "\n";
    }
private:
    std::ofstream file_;
};
```

### Things to Remember

- Never redefine an inherited non-virtual function. Non-virtual functions are statically bound; virtual functions are dynamically bound. Redefining a non-virtual function causes the called function to depend on the declared type of the pointer/reference, not the actual object type.
- If you need different behavior in a derived class, the function should be virtual. If the behavior truly must be invariant, do not redefine it in derived classes.

---
