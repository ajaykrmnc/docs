# Item 13: Use objects to manage resources

## Visual Summary

```text
┌───────────────────────────────────────────────────────────────────────────┐
│                 ITEM 13: USE OBJECTS TO MANAGE RESOURCES                  │
├───────────────────────────────────────────────────────────────────────────┤
│ 1. Raw resource acquired -> every exit path must release it.              │
│ 2. Manual delete/close -> return, exception, or edit can skip cleanup.    │
│ 3. RAII wrapper constructed -> resource ownership moves into an object.   │
│ 4. Scope exits any way -> destructor releases automatically.              │
│ 5. Meaning: bind resource lifetime to object lifetime.                    │
└───────────────────────────────────────────────────────────────────────────┘
```

## Visual Deep Dive

```text
┌───────────────────────────────────────────────────────────────────────────┐
│                        MANUAL CLEANUP FAILURE FLOW                        │
├───────────────────────────────────────────────────────────────────────────┤
│ Resource acquired                                                         │
│                                     ▼                                     │
│ Many lines of work run                                                    │
│                                     ▼                                     │
│ return / throw / goto skips cleanup                                       │
│                                     ▼                                     │
│ Resource leaks or remains locked                                          │
└───────────────────────────────────────────────────────────────────────────┘
```

```text
┌───────────────────────────────────────────────────────────────────────────┐
│                            RAII LIFETIME FLOW                             │
├───────────────────────────────────────────────────────────────────────────┤
│ Acquire resource during object construction                               │
│                                     ▼                                     │
│ Use object normally                                                       │
│                                     ▼                                     │
│ Any scope exit path occurs                                                │
│                                     ▼                                     │
│ Destructor releases resource automatically                                │
└───────────────────────────────────────────────────────────────────────────┘
```

```text
┌───────────────────────────────────────────────────────────────────────────┐
│                          SMART POINTER OWNERSHIP                          │
├───────────────────────────────────────────────────────────────────────────┤
│ unique_ptr                        | shared_ptr                            │
│ ----------------------------------+-------------------------------------  │
│ One owner                         | Many owners                           │
│ Move only                         | Reference counted                     │
│ Delete at scope exit              | Delete at last owner                  │
└───────────────────────────────────────────────────────────────────────────┘
```

### The Problem: Manual Resource Management

Consider a factory function that returns a pointer to a dynamically allocated object:

```cpp
class Investment {
public:
    virtual ~Investment() {}
    virtual double netAssetValue() const = 0;
    // ...
};

class Stock : public Investment { /* ... */ };
class Bond : public Investment { /* ... */ };

// Factory function
Investment* createInvestment() {
    // Analyze parameters, return appropriate derived type
    return new Stock();  // simplified
}
```

Callers of `createInvestment` are responsible for deleting the returned object. This seems
straightforward, but in practice it is remarkably fragile.

#### BAD: Manual delete

```cpp
void f() {
    Investment* pInv = createInvestment();

    // ... use pInv ...

    delete pInv;   // Release the resource
}
```

This looks correct, but there are numerous ways the `delete` can fail to execute:

1. A premature `return` statement somewhere in the "use pInv" block.
2. The "use pInv" code throws an exception.
3. A `continue` or `goto` jumps past the `delete`.
4. A maintainer later restructures the function and accidentally removes the `delete`.

```cpp
// BAD: Exception-unsafe manual management
void f() {
    Investment* pInv = createInvestment();

    doSomethingRisky();   // If this throws, pInv is never deleted!

    if (someCondition) {
        return;           // pInv is leaked here too
    }

    // Imagine 50 more lines of code...

    delete pInv;          // Reached only on the "happy path"
}
```

Even diligent programmers eventually forget or are defeated by exceptions. The fundamental
issue is that **relying on manual cleanup is fragile and unscalable**.

### The Solution: RAII (Resource Acquisition Is Initialization)

The C++ language guarantees that destructors of local objects are called when control leaves
their scope, regardless of _how_ it leaves -- whether by normal flow, an exception, or a
return statement. RAII exploits this guarantee: put the resource inside an object, and let
the destructor release it.

Two critical aspects of RAII:

1. **Resources are acquired and immediately turned over to resource-managing objects.**
   The resource is acquired in the same statement that initializes the managing object.
   "Resource Acquisition Is Initialization" -- the resource is acquired during the
   object's initialization (construction).

2. **Resource-managing objects use their destructors to ensure resources are released.**
   Destructors are called automatically when objects go out of scope, so resources are
   released regardless of how control leaves a block.

#### GOOD: Using auto_ptr (C++98/03 style)

```cpp
void f() {
    std::auto_ptr<Investment> pInv(createInvestment());

    // Use pInv exactly as before, via -> and *
    double nav = pInv->netAssetValue();

    // auto_ptr's destructor deletes pInv automatically
    // -- no leak, even if an exception is thrown
}
```

`auto_ptr` was the original standard smart pointer. It has a peculiar property: **copying
an auto_ptr transfers ownership** (the source becomes null). This means auto_ptrs cannot
be stored in standard containers, and passing one by value silently strips ownership from
the caller.

```cpp
// auto_ptr's unusual copy behavior
std::auto_ptr<Investment> pInv1(createInvestment());
std::auto_ptr<Investment> pInv2(pInv1);    // pInv2 owns it; pInv1 is now null!
pInv1 = pInv2;                             // pInv1 owns it; pInv2 is now null!
```

#### GOOD: Using shared_ptr (C++11 and TR1)

`shared_ptr` is a reference-counted smart pointer. Multiple `shared_ptr`s can point to the
same object, and the object is destroyed when the last `shared_ptr` pointing to it is
destroyed or reset.

```cpp
void f() {
    std::shared_ptr<Investment> pInv(createInvestment());

    // Use pInv exactly as before
    double nav = pInv->netAssetValue();

    // shared_ptr's destructor decrements the reference count.
    // When the count reaches zero, the object is deleted.
}
```

Unlike `auto_ptr`, `shared_ptr` behaves like a normal value during copying:

```cpp
std::shared_ptr<Investment> pInv1(createInvestment());
std::shared_ptr<Investment> pInv2(pInv1);   // Both point to same object, refcount = 2
pInv1 = pInv2;                              // Still both point to same object

// Object is deleted when both pInv1 and pInv2 are destroyed
```

This makes `shared_ptr` safe for use in STL containers:

```cpp
std::vector<std::shared_ptr<Investment>> portfolio;
portfolio.push_back(std::make_shared<Stock>());
portfolio.push_back(std::make_shared<Bond>());
// All Investments are automatically deleted when portfolio is destroyed
```

#### GOOD: Using unique_ptr (Modern C++11+)

`unique_ptr` is the modern replacement for `auto_ptr`. It enforces sole ownership and
cannot be copied -- only moved. This eliminates the confusing implicit ownership transfer
of `auto_ptr`.

```cpp
void f() {
    std::unique_ptr<Investment> pInv(createInvestment());

    // Use pInv normally
    double nav = pInv->netAssetValue();

    // unique_ptr's destructor deletes the object
}
```

```cpp
std::unique_ptr<Investment> pInv1(createInvestment());

// std::unique_ptr<Investment> pInv2(pInv1);   // ERROR: copy constructor is deleted
std::unique_ptr<Investment> pInv2(std::move(pInv1)); // OK: explicit ownership transfer
// pInv1 is now null
```

`unique_ptr` can be stored in move-aware containers:

```cpp
std::vector<std::unique_ptr<Investment>> portfolio;
portfolio.push_back(std::make_unique<Stock>());    // C++14
portfolio.push_back(std::make_unique<Bond>());
// All Investments are automatically deleted when portfolio is destroyed
```

### RAII Applied to Other Resource Types

RAII is not limited to heap memory. It applies to any resource that must be acquired and
then released.

#### Example: File Handles

```cpp
// BAD: Manual file management
void processFile(const std::string& filename) {
    FILE* fp = fopen(filename.c_str(), "r");
    if (!fp) return;

    processData(fp);   // If this throws, fp is leaked!

    fclose(fp);
}

// GOOD: RAII wrapper for FILE*
class FileHandle {
public:
    explicit FileHandle(const std::string& filename, const char* mode)
        : fp_(fopen(filename.c_str(), mode))
    {
        if (!fp_) throw std::runtime_error("Cannot open file: " + filename);
    }

    ~FileHandle() {
        if (fp_) fclose(fp_);
    }

    FILE* get() const { return fp_; }

    // Prevent copying
    FileHandle(const FileHandle&) = delete;
    FileHandle& operator=(const FileHandle&) = delete;

private:
    FILE* fp_;
};

void processFile(const std::string& filename) {
    FileHandle fh(filename, "r");
    processData(fh.get());
    // fclose happens automatically, even if processData throws
}
```

#### Example: Mutex Locks

```cpp
// BAD: Manual lock management
void processSharedData() {
    mutex.lock();

    // ... process data ...
    // If an exception is thrown here, the mutex is never unlocked!
    // Other threads will deadlock.

    mutex.unlock();
}

// GOOD: RAII lock guard
void processSharedData() {
    std::lock_guard<std::mutex> guard(mutex);  // Lock acquired

    // ... process data ...
    // If an exception is thrown, ~lock_guard() unlocks the mutex

    // Mutex automatically unlocked when guard goes out of scope
}
```

#### Example: Database Connections

```cpp
// GOOD: RAII for database connections
class DBConnection {
public:
    static DBConnection open(const std::string& connStr) {
        DBConnection conn;
        conn.handle_ = db_connect(connStr.c_str());
        if (!conn.handle_) throw std::runtime_error("DB connection failed");
        return conn;
    }

    ~DBConnection() {
        if (handle_) db_disconnect(handle_);
    }

    // Move-only semantics
    DBConnection(DBConnection&& other) noexcept : handle_(other.handle_) {
        other.handle_ = nullptr;
    }
    DBConnection& operator=(DBConnection&& other) noexcept {
        if (this != &other) {
            if (handle_) db_disconnect(handle_);
            handle_ = other.handle_;
            other.handle_ = nullptr;
        }
        return *this;
    }
    DBConnection(const DBConnection&) = delete;
    DBConnection& operator=(const DBConnection&) = delete;

private:
    DBConnection() : handle_(nullptr) {}
    db_handle_t handle_;
};

void doWork() {
    auto conn = DBConnection::open("host=db.example.com;db=mydb");
    // Use conn...
    // Connection automatically closed when conn goes out of scope
}
```

### Using shared_ptr with Custom Deleters

Both `auto_ptr` and `unique_ptr` call `delete` in their destructors. But not all resources
are released by calling `delete`. For non-`new` resources, `shared_ptr` (and `unique_ptr`)
can be given custom deleters:

```cpp
// Using shared_ptr with a custom deleter for a C-style resource
void processFile(const std::string& filename) {
    // shared_ptr with a custom deleter that calls fclose
    std::shared_ptr<FILE> fp(
        fopen(filename.c_str(), "r"),
        [](FILE* f) {
            if (f) fclose(f);
        }
    );

    if (!fp) throw std::runtime_error("Cannot open file");

    // Use fp.get() to access the raw FILE*
    char buffer[256];
    while (fgets(buffer, sizeof(buffer), fp.get())) {
        // process buffer
    }
    // fclose is called automatically via the custom deleter
}
```

```cpp
// Using unique_ptr with a custom deleter
struct FileCloser {
    void operator()(FILE* f) const {
        if (f) fclose(f);
    }
};

using UniqueFile = std::unique_ptr<FILE, FileCloser>;

void processFile(const std::string& filename) {
    UniqueFile fp(fopen(filename.c_str(), "r"));
    if (!fp) throw std::runtime_error("Cannot open file");
    // ...
    // fclose called automatically
}
```

### An Important Warning

Both `auto_ptr` and `shared_ptr` (and `unique_ptr`) use `delete` in their destructors,
not `delete[]`. This means that using them with dynamically allocated arrays is a bad idea
(though `unique_ptr` has a partial specialization for arrays):

```cpp
// BAD: undefined behavior with auto_ptr and shared_ptr
std::auto_ptr<std::string> aps(new std::string[10]);   // delete called, not delete[]
std::shared_ptr<int> spi(new int[1024]);                // Same problem

// OK: unique_ptr has array specialization
std::unique_ptr<int[]> upi(new int[1024]);              // delete[] called correctly
// upi[0] = 42;  // operator[] is available

// OK: shared_ptr with custom deleter for arrays
std::shared_ptr<int> spi(new int[1024], std::default_delete<int[]>());

// BEST: Use std::vector or std::array instead of raw arrays
std::vector<int> v(1024);
```

### Things to Remember

- **To prevent resource leaks, use RAII objects that acquire resources in their constructors
  and release them in their destructors.**

- **Two commonly useful RAII classes are `shared_ptr` and `unique_ptr` (formerly `auto_ptr`).
  `shared_ptr` uses reference counting and supports copying. `unique_ptr` enforces sole
  ownership and supports only moving. `auto_ptr` is deprecated and should not be used in
  new code.**

- **`auto_ptr`'s copy operations transfer ownership, making the source null. This makes it
  unsuitable for use in containers. Prefer `unique_ptr` instead.**

---
