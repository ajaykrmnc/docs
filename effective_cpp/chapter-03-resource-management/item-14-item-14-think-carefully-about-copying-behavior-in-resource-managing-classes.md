# Item 14: Think carefully about copying behavior in resource-managing classes

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
