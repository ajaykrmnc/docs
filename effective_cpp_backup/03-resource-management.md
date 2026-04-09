# Chapter 3: Resource Management

C++ programs manage many kinds of resources: dynamically allocated memory, file descriptors,
mutex locks, database connections, network sockets, GUI fonts and brushes. Regardless of the
resource type, the fundamental challenge is the same: once you acquire a resource, you must
eventually release it. Failure to do so leads to resource leaks, which degrade performance,
cause data corruption, or crash programs.

This chapter covers five items that together form a coherent philosophy for resource management
in C++. The central idea is **RAII** (Resource Acquisition Is Initialization): bind the
lifetime of a resource to the lifetime of an object, so that C++'s deterministic destruction
guarantees cleanup even in the presence of exceptions or early returns.

---

## Item 13: Use objects to manage resources

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

## Item 14: Think carefully about copying behavior in resource-managing classes

### Beyond Heap Memory

Not all resources live on the heap. For non-heap resources, smart pointers like `shared_ptr`
and `unique_ptr` are often inappropriate as resource handlers. When that is the case, you
need to craft your own resource-managing class, and when you do, you must confront a
fundamental question: **what should happen when an RAII object is copied?**

### The Motivating Example: Mutex Locks

Consider a class that manages the locking of a `Mutex`:

```cpp
// A C-style API for mutexes
void lock(Mutex* pm);     // Lock the mutex pointed to by pm
void unlock(Mutex* pm);   // Unlock the mutex

// RAII class for mutex locks
class Lock {
public:
    explicit Lock(Mutex* pm) : mutexPtr_(pm) {
        lock(mutexPtr_);   // Acquire resource (lock) in constructor
    }
    ~Lock() {
        unlock(mutexPtr_); // Release resource (unlock) in destructor
    }

private:
    Mutex* mutexPtr_;
};
```

Usage follows the RAII pattern:

```cpp
Mutex m;

{
    Lock ml(&m);   // Lock the mutex
    // ... critical section ...
}                  // Automatically unlock the mutex at end of block
```

But what should happen if a `Lock` object is copied?

```cpp
Lock ml1(&m);
Lock ml2(ml1);   // What should happen here?
```

This question arises for every RAII class. There are four common strategies.

### Strategy 1: Prohibit Copying

In many cases, it makes no sense to copy an RAII object. A mutex lock is owned by exactly
one scope; copying it is semantically meaningless. The right response is to make copying
illegal.

```cpp
// C++11 style: delete the copy operations
class Lock {
public:
    explicit Lock(Mutex* pm) : mutexPtr_(pm) {
        lock(mutexPtr_);
    }
    ~Lock() {
        unlock(mutexPtr_);
    }

    // Prohibit copying
    Lock(const Lock&) = delete;
    Lock& operator=(const Lock&) = delete;

private:
    Mutex* mutexPtr_;
};
```

```cpp
// C++98 style: declare copy operations private and don't define them
// (or inherit from boost::noncopyable / a custom Uncopyable base class)
class Lock : private Uncopyable {
public:
    // ...
};
```

This is the approach taken by `std::lock_guard`, `std::unique_lock` (it supports moving
but not copying), and `std::unique_ptr`.

```cpp
Lock ml1(&m);
// Lock ml2(ml1);   // Compile-time error: copy constructor is deleted
```

### Strategy 2: Reference-Count the Underlying Resource

Sometimes you want to hold on to a resource until the last object using it is destroyed.
In that case, copying an RAII object should increment a reference count. This is the
behavior of `std::shared_ptr`.

Conveniently, `shared_ptr` allows a custom deleter, so you can use it directly:

```cpp
class Lock {
public:
    explicit Lock(Mutex* pm) : mutexPtr_(pm, unlock) {
        lock(mutexPtr_.get());
    }
    // No need for a destructor! shared_ptr's destructor calls unlock(mutexPtr_.get())
    // when the reference count drops to zero.

private:
    std::shared_ptr<Mutex> mutexPtr_;
};
```

Now copying works naturally:

```cpp
Mutex m;
Lock ml1(&m);      // Locks the mutex, refcount = 1
{
    Lock ml2(ml1); // Copies the shared_ptr, refcount = 2
    // Both ml1 and ml2 "share" the lock
}                  // ml2 destroyed, refcount = 1 -- mutex NOT unlocked yet
// ...
// ml1 destroyed, refcount = 0 -- mutex IS unlocked
```

Note that the `Lock` class no longer declares a destructor. The default destructor destroys
`mutexPtr_`, which is a `shared_ptr` whose custom deleter calls `unlock`. This is an
elegant example of composition.

### Strategy 3: Copy the Underlying Resource (Deep Copy)

Sometimes you can -- and should -- copy the managed resource itself. This is "deep copying."
When you copy the RAII object, you also create a copy of the resource it wraps.

The canonical example is `std::string`. When you copy a `std::string`, the underlying
character buffer is duplicated:

```cpp
// Deep-copying RAII class
class Bitmap {
public:
    Bitmap(int width, int height)
        : width_(width), height_(height),
          data_(new unsigned char[width * height * 4])
    {
        std::memset(data_, 0, width * height * 4);
    }

    ~Bitmap() {
        delete[] data_;
    }

    // Deep copy: allocate new buffer and copy contents
    Bitmap(const Bitmap& rhs)
        : width_(rhs.width_), height_(rhs.height_),
          data_(new unsigned char[width_ * height_ * 4])
    {
        std::memcpy(data_, rhs.data_, width_ * height_ * 4);
    }

    Bitmap& operator=(const Bitmap& rhs) {
        if (this != &rhs) {
            // Allocate new buffer first (strong exception safety)
            unsigned char* newData = new unsigned char[rhs.width_ * rhs.height_ * 4];
            std::memcpy(newData, rhs.data_, rhs.width_ * rhs.height_ * 4);

            // Now safe to modify *this
            delete[] data_;
            data_ = newData;
            width_ = rhs.width_;
            height_ = rhs.height_;
        }
        return *this;
    }

private:
    int width_, height_;
    unsigned char* data_;
};
```

#### A Complete Deep-Copy RAII Example: Managing a Temporary File

```cpp
class TempFile {
public:
    explicit TempFile(const std::string& prefix) {
        filename_ = prefix + "_" + generateUniqueId() + ".tmp";
        fp_ = fopen(filename_.c_str(), "w+");
        if (!fp_) throw std::runtime_error("Cannot create temp file");
    }

    ~TempFile() {
        if (fp_) fclose(fp_);
        std::remove(filename_.c_str());  // Delete the file from disk
    }

    // Deep copy: create a new temp file and copy contents
    TempFile(const TempFile& rhs) : fp_(nullptr) {
        filename_ = rhs.filename_ + ".copy_" + generateUniqueId();
        fp_ = fopen(filename_.c_str(), "w+");
        if (!fp_) throw std::runtime_error("Cannot create temp file copy");

        // Copy the contents of the original file
        if (rhs.fp_) {
            long pos = ftell(rhs.fp_);      // Save current position
            fseek(rhs.fp_, 0, SEEK_SET);    // Rewind
            char buffer[4096];
            size_t n;
            while ((n = fread(buffer, 1, sizeof(buffer), rhs.fp_)) > 0) {
                fwrite(buffer, 1, n, fp_);
            }
            fseek(rhs.fp_, pos, SEEK_SET);  // Restore original position
        }
    }

    // Assignment: similar logic with self-assignment check
    TempFile& operator=(const TempFile& rhs);

    FILE* get() const { return fp_; }
    const std::string& filename() const { return filename_; }

private:
    static std::string generateUniqueId();
    std::string filename_;
    FILE* fp_;
};
```

### Strategy 4: Transfer Ownership of the Underlying Resource

In rare cases, you want to ensure that only one RAII object ever refers to a raw resource,
and copying transfers ownership from the source to the destination, leaving the source in
a null or empty state. This is what `auto_ptr` does and what `unique_ptr` achieves via
move semantics.

```cpp
// Move-only RAII class (modern C++ approach)
class SocketConnection {
public:
    explicit SocketConnection(const std::string& host, int port)
        : fd_(connectToHost(host, port))
    {
        if (fd_ < 0) throw std::runtime_error("Connection failed");
    }

    ~SocketConnection() {
        if (fd_ >= 0) close(fd_);
    }

    // Move constructor: transfer ownership
    SocketConnection(SocketConnection&& other) noexcept : fd_(other.fd_) {
        other.fd_ = -1;   // Source no longer owns the socket
    }

    // Move assignment: transfer ownership
    SocketConnection& operator=(SocketConnection&& other) noexcept {
        if (this != &other) {
            if (fd_ >= 0) close(fd_);
            fd_ = other.fd_;
            other.fd_ = -1;
        }
        return *this;
    }

    // Copying is prohibited -- there is only one socket
    SocketConnection(const SocketConnection&) = delete;
    SocketConnection& operator=(const SocketConnection&) = delete;

    int fd() const { return fd_; }

private:
    int fd_;
};

// Usage:
SocketConnection conn1("example.com", 80);
// SocketConnection conn2(conn1);               // ERROR: cannot copy
SocketConnection conn2(std::move(conn1));        // OK: ownership transferred
// conn1.fd() is now -1; conn2 owns the socket
```

### Choosing the Right Strategy: A Decision Framework

```
Is copying semantically meaningful?
  |
  +-- No  --> Prohibit copying (Strategy 1)
  |           Examples: mutex locks, unique hardware handles
  |
  +-- Yes --> Is the resource shareable?
                |
                +-- Yes --> Reference-count it (Strategy 2)
                |           Examples: shared memory, reference-counted handles
                |
                +-- No  --> Can the resource be duplicated?
                              |
                              +-- Yes --> Deep copy (Strategy 3)
                              |           Examples: buffers, strings, bitmaps
                              |
                              +-- No  --> Transfer ownership (Strategy 4)
                                          Examples: sockets, file descriptors,
                                                    unique system resources
```

### A Real-World Example: Combining Strategies

In practice, a single class might use different strategies for different resources:

```cpp
class RenderContext {
public:
    RenderContext(int width, int height, const std::string& shaderFile)
        : framebuffer_(new unsigned char[width * height * 4]),       // Deep copy
          width_(width), height_(height),
          shaderProgram_(loadShader(shaderFile), deleteShader),       // Ref-counted
          gpuContext_(acquireGPUContext())                            // Non-copyable
    {}

    // The compiler-generated copy constructor would:
    // - Deep copy framebuffer_ (if we use a vector)
    // - Share shaderProgram_ (shared_ptr copies increment refcount)
    // - Fail on gpuContext_ (unique_ptr is non-copyable)
    //
    // Since gpuContext_ is non-copyable, the whole class is non-copyable
    // unless we explicitly decide what to do.

    RenderContext(const RenderContext&) = delete;
    RenderContext& operator=(const RenderContext&) = delete;

    // But we can support move semantics
    RenderContext(RenderContext&&) = default;
    RenderContext& operator=(RenderContext&&) = default;

private:
    std::vector<unsigned char> framebuffer_;          // Deep-copyable (via vector)
    std::shared_ptr<ShaderProgram> shaderProgram_;    // Reference-counted
    std::unique_ptr<GPUContext> gpuContext_;           // Non-copyable, movable
};
```

### Things to Remember

- **Copying an RAII object entails copying the resource it manages, so the copying behavior
  of the resource determines the copying behavior of the RAII object.**

- **Common RAII class copying behaviors are: disallowing copying (the most common),
  reference counting, deep copying, and transferring ownership.**

---

## Item 15: Provide access to raw resources in resource-managing classes

### The Reality of APIs

RAII classes are wonderful, but the world is full of APIs that deal in raw resources. If
you are going to use RAII, you need a way to convert an RAII object into the raw resource
it wraps, because sooner or later you will need to pass it to an API that expects the raw
type.

```cpp
// Suppose we have an Investment hierarchy managed by shared_ptr
std::shared_ptr<Investment> pInv(createInvestment());

// And an API function that takes a raw pointer:
int daysHeld(const Investment* pi);        // How many days has this been held?
double creditRating(const Investment* pi); // What is the credit rating?

// We need to convert from shared_ptr<Investment> to const Investment*
```

### Explicit Conversion: The get() Member Function

Smart pointers provide a `get()` member function that returns a copy of the raw pointer
inside the smart pointer:

```cpp
std::shared_ptr<Investment> pInv(createInvestment());

int days = daysHeld(pInv.get());           // Pass raw pointer to the API
double rating = creditRating(pInv.get());
```

Smart pointers also overload `operator->` and `operator*`, so you can use them like raw
pointers in most contexts:

```cpp
class Investment {
public:
    bool isTaxFree() const;
    double currentValue() const;
};

std::shared_ptr<Investment> pInv(createInvestment());

bool taxFree = pInv->isTaxFree();         // operator->
double val = (*pInv).currentValue();       // operator*
```

### Designing Your Own RAII Classes: Explicit vs. Implicit Conversion

When you write your own RAII class, you must decide how clients will access the underlying
resource. There are two approaches: explicit conversion and implicit conversion.

#### Explicit Conversion via get()

```cpp
// A RAII wrapper for a C-style font handle
class Font {
public:
    explicit Font(const std::string& name, int size)
        : handle_(createFont(name.c_str(), size))
    {
        if (!handle_) throw std::runtime_error("Failed to create font");
    }

    ~Font() {
        if (handle_) destroyFont(handle_);
    }

    // Explicit conversion: client must call get()
    FontHandle get() const { return handle_; }

    Font(const Font&) = delete;
    Font& operator=(const Font&) = delete;

private:
    FontHandle handle_;   // Raw C handle
};
```

Usage:

```cpp
// C API function
void drawText(FontHandle font, const char* text, int x, int y);

Font f("Arial", 12);
drawText(f.get(), "Hello, World!", 10, 20);   // Must explicitly call get()
```

This is safe but verbose. Every time you use the font with a C API, you type `.get()`.

#### Implicit Conversion via operator

You can provide an implicit conversion operator:

```cpp
class Font {
public:
    explicit Font(const std::string& name, int size)
        : handle_(createFont(name.c_str(), size))
    {}

    ~Font() {
        if (handle_) destroyFont(handle_);
    }

    // Implicit conversion to FontHandle
    operator FontHandle() const { return handle_; }

    Font(const Font&) = delete;
    Font& operator=(const Font&) = delete;

private:
    FontHandle handle_;
};
```

Usage becomes seamless:

```cpp
Font f("Arial", 12);
drawText(f, "Hello, World!", 10, 20);   // Implicit conversion -- looks natural
```

But implicit conversions open the door to accidental misuse:

```cpp
// BAD: Implicit conversion can lead to dangling handles
Font f1("Arial", 12);
FontHandle h = f1;        // Implicit conversion -- h is a copy of the raw handle

// Now suppose f1 is destroyed (goes out of scope)...
// h is a dangling handle! Using it is undefined behavior.
```

```cpp
// BAD: Accidentally passing the wrong type
void changeFontSize(FontHandle fh, int newSize);  // C API

Font f("Arial", 12);
changeFontSize(f, 14);  // Compiles fine due to implicit conversion
// But did the programmer mean to modify the font managed by f?
// The C API might reallocate the handle, leaving f holding a stale value.
```

### The Trade-off: Safety vs. Convenience

The choice between explicit and implicit conversion is a design decision that involves
a trade-off:

| Aspect | Explicit (`get()`) | Implicit (`operator T()`) |
|---|---|---|
| Safety | Higher -- conversions are visible | Lower -- accidental conversions possible |
| Convenience | Lower -- verbose | Higher -- seamless with C APIs |
| Dangling risk | Lower -- deliberate action | Higher -- easy to extract and outlive |

**Meyers' recommendation**: Lean toward explicit conversion (`get()`), because the cost
of inadvertent type conversions usually outweighs the inconvenience of explicit calls.
However, the right choice depends on the specific use case and how the RAII class interacts
with existing APIs.

### Real-World Examples from the Standard Library

The standard library generally favors explicit conversion:

```cpp
// std::shared_ptr and std::unique_ptr use get()
std::shared_ptr<Widget> sp = std::make_shared<Widget>();
Widget* raw = sp.get();    // Explicit

// std::string provides c_str() for explicit conversion
std::string s = "hello";
const char* cstr = s.c_str();  // Explicit conversion to C string

// std::vector provides data() for explicit conversion
std::vector<int> v = {1, 2, 3};
int* arr = v.data();            // Explicit conversion to raw array
```

But some classes do provide implicit conversions:

```cpp
// std::string has an implicit conversion via operator basic_string_view (C++17)
// std::reference_wrapper has an implicit conversion to T&
std::reference_wrapper<int> ref(someInt);
int& r = ref;   // Implicit conversion
```

### Complete Example: A RAII Wrapper with Both Access Methods

```cpp
// A RAII class managing an OpenGL texture
class Texture {
public:
    explicit Texture(int width, int height, const unsigned char* pixels)
        : id_(0)
    {
        glGenTextures(1, &id_);
        glBindTexture(GL_TEXTURE_2D, id_);
        glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, width, height,
                     0, GL_RGBA, GL_UNSIGNED_BYTE, pixels);
    }

    ~Texture() {
        if (id_ != 0) {
            glDeleteTextures(1, &id_);
        }
    }

    // Explicit access -- preferred
    GLuint id() const { return id_; }

    // Move semantics (textures are GPU resources, not copyable)
    Texture(Texture&& other) noexcept : id_(other.id_) {
        other.id_ = 0;
    }

    Texture& operator=(Texture&& other) noexcept {
        if (this != &other) {
            if (id_ != 0) glDeleteTextures(1, &id_);
            id_ = other.id_;
            other.id_ = 0;
        }
        return *this;
    }

    Texture(const Texture&) = delete;
    Texture& operator=(const Texture&) = delete;

private:
    GLuint id_;
};

// Usage:
Texture tex(256, 256, pixelData);
glBindTexture(GL_TEXTURE_2D, tex.id());   // Explicit -- clear and safe
```

### Accessing Raw Resources Does Not Violate Encapsulation

It might seem that providing access to the raw resource defeats the purpose of the RAII
class. But the purpose of the RAII class is not to encapsulate the resource -- it is to
**ensure the resource is released**. Encapsulation is a secondary concern. If providing
access to the raw resource is necessary for the class to be useful, that access does not
undermine the class's primary mission.

Think of RAII classes as a careful layer on top of the resource, not a wall around it.
`shared_ptr` and `unique_ptr` both provide `get()`, and no one considers them poorly
designed.

Some RAII classes combine both roles (resource management AND encapsulation), but these
are the minority. Most RAII classes exist solely to guarantee cleanup.

### Things to Remember

- **APIs often require access to raw resources, so each RAII class should offer a way to
  get at the resource it manages.**

- **Access may be via explicit conversion (e.g., a `get()` member function) or implicit
  conversion (e.g., `operator RawType()`). Explicit conversion is generally safer; implicit
  conversion is more convenient for callers.**

- **Providing access to the raw resource does not violate encapsulation. RAII classes exist
  to guarantee resource release, not to hide the resource.**

---

## Item 16: Use the same form in corresponding uses of new and delete

### The Rule

This item has the simplest guideline in the chapter, yet violations cause some of the most
insidious bugs in C++:

> If you use `[]` in a `new` expression, you must use `[]` in the corresponding `delete`
> expression. If you do not use `[]` in a `new` expression, you must not use `[]` in the
> corresponding `delete` expression.

### Understanding Memory Layout

When you use `new`, two things happen:
1. Memory is allocated (via `operator new`).
2. One or more constructors are called on that memory.

When you use `delete`, two things happen (in reverse):
1. One or more destructors are called.
2. Memory is deallocated (via `operator delete`).

The critical question for `delete` is: **how many objects reside in the memory being
deleted?** This determines how many destructors to call.

A single object and an array of objects have different memory layouts:

```
Single object:
+-------------------+
|      Object       |
+-------------------+

Array of objects:
+---+-------------------+-------------------+---+-------------------+
| n |     Object 0      |     Object 1      |...|    Object n-1     |
+---+-------------------+-------------------+---+-------------------+
  ^
  |-- Array size (stored by the implementation, typically before the first object)
```

When you say `delete[]`, the runtime reads the array size `n` from this header and calls
destructors for each of the `n` objects. When you say `delete` (without `[]`), the runtime
assumes there is a single object and calls one destructor.

### What Goes Wrong

#### BAD: Using delete on an array

```cpp
std::string* stringArray = new std::string[100];

// ...

delete stringArray;   // UNDEFINED BEHAVIOR!
// Only one destructor is called (for stringArray[0]).
// The other 99 std::string objects are never destroyed.
// Their internal memory (heap-allocated character buffers) is leaked.
// The memory layout is also misinterpreted, potentially corrupting the heap.
```

#### BAD: Using delete[] on a single object

```cpp
std::string* stringPtr = new std::string("hello");

// ...

delete[] stringPtr;   // UNDEFINED BEHAVIOR!
// The runtime tries to read an array size from memory before the object.
// That memory contains garbage (or part of another allocation).
// It then tries to call destructors on "objects" that do not exist.
// This can corrupt memory, crash, or cause silent data corruption.
```

#### Both are undefined behavior

The C++ Standard says the behavior is undefined in both cases. In practice:

- `delete` on an array may leak resources held by all but the first element.
- `delete[]` on a single object may read garbage as an array count and corrupt memory.
- Some implementations may appear to "work" for built-in types (like `int`) because their
  destructors are trivial, but the behavior is still technically undefined.

### The Correct Pairings

```cpp
// Correct: new with delete
std::string* ps = new std::string("hello");
delete ps;

// Correct: new[] with delete[]
std::string* psa = new std::string[100];
delete[] psa;

// Correct: Built-in types follow the same rule
int* pi = new int(42);
delete pi;

int* pia = new int[100];
delete[] pia;
```

### The Typedef Trap

Typedefs can obscure whether a type is an array, making this rule harder to follow:

```cpp
// BAD: A typedef that hides an array
typedef std::string AddressLines[4];

// This looks like a single object allocation, but it is an array!
std::string* pal = new AddressLines;
// This is equivalent to: new std::string[4]

// What form of delete is correct?
delete pal;     // UNDEFINED BEHAVIOR! This is actually an array.
delete[] pal;   // Correct, but non-obvious because AddressLines hides the array.
```

This is a compelling reason to prefer `std::array` or `std::vector` over raw arrays
and array typedefs:

```cpp
// GOOD: No ambiguity with std::array or std::vector
using AddressLines = std::array<std::string, 4>;

AddressLines* pal = new AddressLines;
delete pal;   // Correct: AddressLines is a single object (a struct containing an array)

// BETTER: No new/delete at all
AddressLines pal;   // Stack-allocated, no manual cleanup needed

// BEST: Use a vector if the size is dynamic
std::vector<std::string> pal(4);
```

### Smart Pointers and the new/delete Mismatch

This issue affects smart pointers as well:

```cpp
// BAD: shared_ptr uses delete by default, not delete[]
std::shared_ptr<int> sp(new int[100]);   // Will call delete, not delete[]!

// GOOD: Use a custom deleter
std::shared_ptr<int> sp(new int[100], std::default_delete<int[]>());

// GOOD: unique_ptr has array specialization
std::unique_ptr<int[]> up(new int[100]); // Correctly calls delete[]
up[5] = 42;                              // operator[] is available

// BEST: Avoid raw arrays entirely
auto v = std::make_shared<std::vector<int>>(100);
```

### Practical Impact: A Debugging Nightmare

Consider this class hierarchy:

```cpp
class Widget {
public:
    Widget() { data_ = new char[1024]; }
    virtual ~Widget() { delete[] data_; }
private:
    char* data_;
};

class SpecialWidget : public Widget {
public:
    SpecialWidget() { extra_ = new char[2048]; }
    ~SpecialWidget() override { delete[] extra_; }
private:
    char* extra_;
};
```

```cpp
// BAD: Mismatched new/delete with polymorphic types
Widget* widgets = new SpecialWidget[10];
delete[] widgets;   // UNDEFINED BEHAVIOR even with delete[]!
// The compiler uses sizeof(Widget) to compute element offsets,
// but the actual objects are SpecialWidget (which is larger).
// Destructors are called at wrong addresses. Catastrophic.

// GOOD: Use a container of smart pointers
std::vector<std::unique_ptr<Widget>> widgets;
for (int i = 0; i < 10; ++i) {
    widgets.push_back(std::make_unique<SpecialWidget>());
}
// Each widget is individually allocated and correctly destroyed
```

### Complete Example: Demonstrating the Mismatch

```cpp
#include <iostream>
#include <memory>

class Tracked {
public:
    Tracked(int id) : id_(id) {
        std::cout << "Tracked(" << id_ << ") constructed\n";
    }
    ~Tracked() {
        std::cout << "Tracked(" << id_ << ") destroyed\n";
    }
private:
    int id_;
};

int main() {
    // --- Correct usage ---
    std::cout << "=== Correct: new[] with delete[] ===\n";
    Tracked* arr = new Tracked[3]{{1}, {2}, {3}};
    delete[] arr;
    // Output:
    // Tracked(1) constructed
    // Tracked(2) constructed
    // Tracked(3) constructed
    // Tracked(3) destroyed
    // Tracked(2) destroyed
    // Tracked(1) destroyed

    std::cout << "\n=== Correct: new with delete ===\n";
    Tracked* single = new Tracked(42);
    delete single;
    // Output:
    // Tracked(42) constructed
    // Tracked(42) destroyed

    // --- Smart pointer approaches ---
    std::cout << "\n=== unique_ptr with array ===\n";
    {
        std::unique_ptr<Tracked[]> uarr(new Tracked[3]{{10}, {20}, {30}});
        // Automatically calls delete[] when uarr goes out of scope
    }

    std::cout << "\n=== Best: vector ===\n";
    {
        std::vector<Tracked> v;
        v.reserve(3);
        v.emplace_back(100);
        v.emplace_back(200);
        v.emplace_back(300);
        // Automatically destroyed when v goes out of scope
    }

    return 0;
}
```

### Things to Remember

- **If you use `[]` in a `new` expression, you must use `[]` in the corresponding `delete`
  expression. If you do not use `[]` in `new`, do not use `[]` in `delete`.**

- **Typedefs can obscure the array nature of a type. Prefer `std::vector`, `std::array`, or
  smart pointers to avoid the ambiguity entirely.**

- **When in doubt, avoid `new[]` altogether. Use `std::vector` for dynamic arrays and
  `std::array` for fixed-size arrays. These manage their own memory and eliminate the
  `new`/`delete` mismatch problem.**

---

## Item 17: Store newed objects in smart pointers in standalone statements

### The Subtle Bug

Consider this seemingly innocent code:

```cpp
int priority();
void processWidget(std::shared_ptr<Widget> pw, int priority);
```

You might call `processWidget` like this:

```cpp
// BAD: Potential resource leak!
processWidget(std::shared_ptr<Widget>(new Widget), priority());
```

This looks safe -- we are using a smart pointer. But it can leak!

### Why It Leaks: Evaluation Order

The C++ standard gives compilers significant freedom in the order they evaluate function
arguments. In the call above, three things must happen before `processWidget` can be called:

1. Execute `new Widget`
2. Construct the `shared_ptr<Widget>`
3. Call `priority()`

The C++ standard requires that step 2 happens after step 1 (the `shared_ptr` constructor
needs the result of `new Widget`). But **step 3 can happen at any point** -- before step 1,
between steps 1 and 2, or after step 2.

A compiler might choose this order:

1. Execute `new Widget`          -- Widget is allocated on the heap
2. Call `priority()`             -- **If this throws, the Widget is leaked!**
3. Construct `shared_ptr<Widget>`  -- This never executes

The `Widget` was `new`ed in step 1, but the `shared_ptr` that would manage it is not
constructed until step 3. If `priority()` throws in step 2, the `Widget` leaks because
nothing is responsible for deleting it.

### The Fix: Standalone Statements

The solution is to separate the creation of the smart pointer into its own statement:

```cpp
// GOOD: Store the newed object in a smart pointer in a standalone statement
std::shared_ptr<Widget> pw(new Widget);  // Statement 1: no leak possible
processWidget(pw, priority());           // Statement 2: no leak possible
```

Now the sequence is deterministic:
1. `new Widget` is executed and immediately handed to the `shared_ptr` constructor.
2. `priority()` is called.
3. `processWidget` is called.

If `priority()` throws, `pw` has already been constructed and its destructor will delete
the `Widget`.

### The Modern Fix: make_shared and make_unique

C++11's `std::make_shared` and C++14's `std::make_unique` eliminate this problem entirely:

```cpp
// BEST: make_shared combines allocation and smart pointer construction
processWidget(std::make_shared<Widget>(), priority());
```

With `make_shared`, the allocation and the `shared_ptr` construction are a single,
indivisible operation. There is no window where the `Widget` exists but is not yet managed
by a smart pointer.

```cpp
// BEST: make_unique (C++14)
void processWidget(std::unique_ptr<Widget> pw, int priority);

processWidget(std::make_unique<Widget>(), priority());
```

### Detailed Walkthrough: Why the Order Matters

Let us trace through the problem step by step with a concrete example:

```cpp
class Widget {
public:
    Widget() {
        std::cout << "Widget constructed at " << this << "\n";
        data_ = new int[1000];  // Widget allocates its own resources
    }
    ~Widget() {
        std::cout << "Widget destroyed at " << this << "\n";
        delete[] data_;
    }
private:
    int* data_;
};

int priority() {
    // Imagine this reads from a database, a file, or does complex computation
    throw std::runtime_error("Priority database unavailable!");
    return 0;  // Never reached
}

void processWidget(std::shared_ptr<Widget> pw, int p) {
    std::cout << "Processing widget with priority " << p << "\n";
}
```

#### BAD path (compiler chooses unfortunate evaluation order):

```cpp
try {
    // Compiler may evaluate in this order:
    // 1. new Widget        -> Widget constructed, raw pointer exists
    // 2. priority()        -> THROWS! Stack unwinding begins.
    // 3. shared_ptr(...)   -> Never reached. Widget is leaked.
    processWidget(std::shared_ptr<Widget>(new Widget), priority());
}
catch (const std::exception& e) {
    std::cout << "Caught: " << e.what() << "\n";
    // Output: "Widget constructed at 0x..."
    //         "Caught: Priority database unavailable!"
    // Note: NO "Widget destroyed" message -- the Widget leaked!
}
```

#### GOOD path (standalone statement):

```cpp
try {
    std::shared_ptr<Widget> pw(new Widget);  // Widget is safely managed
    processWidget(pw, priority());           // If priority() throws...
}
catch (const std::exception& e) {
    std::cout << "Caught: " << e.what() << "\n";
    // Output: "Widget constructed at 0x..."
    //         "Widget destroyed at 0x..."  <-- pw's destructor cleans up!
    //         "Caught: Priority database unavailable!"
}
```

### This Problem Extends Beyond Function Arguments

The same issue can arise in any expression where a `new` and other potentially-throwing
operations are interleaved:

```cpp
// BAD: Multiple news in one expression
auto p = std::make_pair(
    std::shared_ptr<Widget>(new Widget),
    std::shared_ptr<Gadget>(new Gadget)
);
// If the second new succeeds but the first shared_ptr hasn't been constructed yet
// (or vice versa), a throw would leak.

// GOOD: Separate statements
auto pw = std::make_shared<Widget>();
auto pg = std::make_shared<Gadget>();
auto p = std::make_pair(pw, pg);
```

```cpp
// BAD: new in a ternary expression
std::shared_ptr<Widget> pw(
    condition ? new SpecialWidget : new Widget
);
// This is actually fine because only one new is evaluated, and it is directly
// passed to the shared_ptr constructor. But it is easier to reason about:

// GOOD: Clear and unambiguous
std::shared_ptr<Widget> pw;
if (condition) {
    pw = std::make_shared<SpecialWidget>();
} else {
    pw = std::make_shared<Widget>();
}
```

### C++17 Changes

Starting with C++17, the evaluation order of function arguments was tightened. Specifically,
the expressions associated with a single parameter must be fully evaluated before the
evaluation of any other parameter begins. This means:

```cpp
// In C++17 and later, this is safe:
processWidget(std::shared_ptr<Widget>(new Widget), priority());
// Because: either (new Widget + shared_ptr construction) happens entirely before
// priority(), or priority() happens entirely before (new Widget + shared_ptr construction).
```

However, even in C++17, using `make_shared` / `make_unique` is still recommended because:

1. It communicates intent more clearly.
2. It avoids the `new`/`delete` asymmetry (no raw `new` at all).
3. `make_shared` can be more efficient (single allocation for object + control block).
4. Code may need to compile on pre-C++17 compilers.

### Complete Example: A Factory with Exception Safety

```cpp
#include <memory>
#include <string>
#include <stdexcept>
#include <iostream>

class Config {
public:
    explicit Config(const std::string& filename) {
        std::cout << "Loading config from " << filename << "\n";
        // Might throw if file not found
    }
};

class Logger {
public:
    explicit Logger(const std::string& logfile) {
        std::cout << "Opening log: " << logfile << "\n";
    }
};

class Database {
public:
    Database(const std::string& connStr, int timeout) {
        std::cout << "Connecting to " << connStr << "\n";
        if (timeout < 0) throw std::runtime_error("Invalid timeout");
    }
};

int computeTimeout(const Config& cfg) {
    // Might throw
    return 30;
}

// BAD: Multiple potential leaks
void initializeSystem_bad() {
    processResources(
        std::shared_ptr<Config>(new Config("app.cfg")),
        std::shared_ptr<Logger>(new Logger("app.log")),
        std::shared_ptr<Database>(new Database("db://host",
                                               computeTimeout(*new Config("app.cfg"))))
    );
    // This is a mess: raw new of Config that is never managed,
    // multiple unsequenced new operations, etc.
}

// GOOD: Each resource created in a standalone statement
void initializeSystem_good() {
    auto config = std::make_shared<Config>("app.cfg");
    auto logger = std::make_shared<Logger>("app.log");

    int timeout = computeTimeout(*config);  // Might throw -- but nothing leaks
    auto database = std::make_shared<Database>("db://host", timeout);

    processResources(config, logger, database);
    // If any step throws, all previously created resources are cleaned up
    // by their shared_ptr destructors during stack unwinding.
}
```

### Guideline Summary

```
Rule of thumb:
  NEVER write "new" inside a function call's argument list.
  Always store the result of "new" in a named smart pointer first,
  or use make_shared / make_unique.

// BAD patterns:
f(shared_ptr<T>(new T), g());
f(unique_ptr<T>(new T), g());
f(shared_ptr<T>(new T), shared_ptr<U>(new U));

// GOOD patterns:
auto p = make_shared<T>();     // or make_unique<T>()
f(p, g());

auto p1 = make_shared<T>();
auto p2 = make_shared<U>();
f(p1, p2);
```

### Things to Remember

- **Store `new`ed objects in smart pointers in standalone statements. Failure to do this can
  lead to subtle resource leaks when exceptions are thrown, because compilers have latitude
  to reorder operations within a single statement.**

- **Prefer `std::make_shared` (C++11) and `std::make_unique` (C++14) over raw `new` with
  smart pointer constructors. These functions combine allocation and smart pointer
  construction into a single, atomic operation, eliminating the window for leaks.**

---

## Summary of Chapter 3

| Item | Key Principle |
|---|---|
| 13 | Use RAII objects to manage resources. Acquire in constructors, release in destructors. |
| 14 | Choose the right copying strategy: prohibit, reference-count, deep copy, or transfer ownership. |
| 15 | Provide `get()` or conversion operators so RAII objects work with raw-resource APIs. |
| 16 | Match `new` with `delete` and `new[]` with `delete[]`. Prefer containers over raw arrays. |
| 17 | Store `new`ed objects in smart pointers in standalone statements. Prefer `make_shared`/`make_unique`. |

The overarching theme: **make resource management automatic and exception-safe by tying
resource lifetimes to object lifetimes**. When you follow RAII consistently, resource leaks
become nearly impossible, and your code becomes simpler, safer, and easier to maintain.
