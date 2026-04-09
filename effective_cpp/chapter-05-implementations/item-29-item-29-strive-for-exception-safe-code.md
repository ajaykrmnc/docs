# Item 29: Strive for exception-safe code

Exception safety is not about whether your code throws exceptions. It is about
how your code behaves when exceptions are thrown --- possibly by code you call.
Exception-safe functions offer one of three guarantees, and functions that offer
no guarantee at all are not acceptable in well-written C++.

### The Three Exception Safety Guarantees

**1. The Basic Guarantee:** If an exception is thrown, the program remains in a
valid state. No resources are leaked, and all objects remain in a self-consistent
state (i.e., all class invariants are satisfied). However, the exact state of
the program may not be predictable. For example, after an exception in a
"change the background image" function, the old image might be displayed, or
some default image, or something else --- but the object is not corrupt.

**2. The Strong Guarantee:** If an exception is thrown, the state of the program
is unchanged. Calls to functions offering the strong guarantee are atomic: they
either succeed completely or have no effect at all. This is a "commit or
rollback" model.

**3. The Nothrow Guarantee:** The function never throws exceptions. All
operations on built-in types (ints, pointers, etc.) are nothrow. This is the
strongest guarantee. Functions marked `noexcept` promise this guarantee.

### A Motivating Example

```cpp
// A class for GUI menus with a changeable background image.
class PrettyMenu {
public:
    void changeBackground(std::istream& imgSrc);

private:
    std::mutex mutex_;
    Image* bgImage_;        // Raw pointer: current background image
    int imageChanges_;      // Number of times image has been changed
};

// VERSION 1: Not exception-safe at all.
void PrettyMenu::changeBackground(std::istream& imgSrc) {
    mutex_.lock();                       // Acquire mutex

    delete bgImage_;                     // Destroy old image
    ++imageChanges_;                     // Increment change counter
    bgImage_ = new Image(imgSrc);       // Install new image

    mutex_.unlock();                     // Release mutex
}
```

**What goes wrong with Version 1:**

1. **Resource leak:** If `new Image(imgSrc)` throws, `mutex_` is never
   unlocked. The mutex is leaked (permanently locked).

2. **Corrupted state:** If `new Image(imgSrc)` throws, `bgImage_` points to
   a deleted object (dangling pointer), and `imageChanges_` has already been
   incremented even though the image was never actually changed.

### Fixing for the Basic Guarantee

```cpp
// VERSION 2: Offers the basic guarantee using RAII and careful ordering.
void PrettyMenu::changeBackground(std::istream& imgSrc) {
    // Use lock_guard for RAII-based mutex management.
    // The mutex will be released when the function exits, whether
    // normally or via an exception.
    std::lock_guard<std::mutex> lock(mutex_);

    // Allocate the new image BEFORE deleting the old one.
    // If new throws, the old image is still intact.
    Image* newImage = new Image(imgSrc);

    delete bgImage_;          // Delete old image (only after new one succeeded)
    bgImage_ = newImage;      // Install new image (no-throw: pointer assignment)
    ++imageChanges_;          // Increment counter (no-throw: integer increment)
}
```

This is better: the mutex cannot leak, and `bgImage_` always points to a
valid image. But it only offers the basic guarantee, not the strong guarantee.
If `new Image` throws, the state is valid but the caller cannot know whether
the image has changed or not.

### Achieving the Strong Guarantee with Copy-and-Swap

The copy-and-swap idiom is the classic technique for achieving the strong
guarantee:

```cpp
// VERSION 3: Offers the strong guarantee using copy-and-swap.

// Step 1: Move the data that might change into a separate implementation struct.
struct PMImpl {
    std::shared_ptr<Image> bgImage;
    int imageChanges = 0;
};

class PrettyMenu {
public:
    void changeBackground(std::istream& imgSrc);

private:
    std::mutex mutex_;
    std::shared_ptr<PMImpl> pImpl_;   // pImpl idiom (see Item 31)
};

void PrettyMenu::changeBackground(std::istream& imgSrc) {
    std::lock_guard<std::mutex> lock(mutex_);

    // STEP 1: Make a copy of the current state.
    auto pNew = std::make_shared<PMImpl>(*pImpl_);

    // STEP 2: Modify the copy. If this throws, the original is untouched.
    pNew->bgImage.reset(new Image(imgSrc));    // May throw
    ++pNew->imageChanges;                       // Won't throw

    // STEP 3: Swap the copy into place. swap for shared_ptr is noexcept.
    std::swap(pImpl_, pNew);

    // If we reach here, the change succeeded atomically.
    // If step 2 threw, we never reached step 3, so the original state
    // is completely unchanged --- the strong guarantee.
}
```

### Copy-and-Swap as a General Pattern

```cpp
// A strongly exception-safe assignment operator using copy-and-swap.
class String {
public:
    String(const char* s = "") : data_(new char[strlen(s) + 1]) {
        strcpy(data_, s);
    }

    ~String() { delete[] data_; }

    // Copy constructor: makes an independent copy.
    String(const String& rhs) : data_(new char[strlen(rhs.data_) + 1]) {
        strcpy(data_, rhs.data_);
    }

    // Copy-and-swap assignment operator.
    // Takes the parameter BY VALUE, which invokes the copy constructor.
    // Then we swap the copy's internals with ours.
    // This is exception-safe because:
    //   - The copy is made before any state is modified.
    //   - swap is noexcept (just swaps two pointers).
    //   - If the copy constructor throws, *this is unchanged.
    String& operator=(String rhs) {   // Note: pass by value!
        swap(rhs);
        return *this;
    }

    void swap(String& rhs) noexcept {
        std::swap(data_, rhs.data_);
    }

private:
    char* data_;
};
```

### The Nothrow Guarantee and `noexcept`

```cpp
// Functions that should be noexcept:

// 1. Move constructors and move assignment operators
class Buffer {
public:
    Buffer(Buffer&& other) noexcept
        : data_(other.data_), size_(other.size_) {
        other.data_ = nullptr;
        other.size_ = 0;
    }

    Buffer& operator=(Buffer&& other) noexcept {
        if (this != &other) {
            delete[] data_;
            data_ = other.data_;
            size_ = other.size_;
            other.data_ = nullptr;
            other.size_ = 0;
        }
        return *this;
    }

    // 2. Destructors (implicitly noexcept in C++11 and later)
    ~Buffer() noexcept {
        delete[] data_;
    }

    // 3. Swap functions
    void swap(Buffer& other) noexcept {
        std::swap(data_, other.data_);
        std::swap(size_, other.size_);
    }

private:
    char* data_ = nullptr;
    size_t size_ = 0;
};

// Why noexcept matters for performance:
// std::vector::push_back will use move semantics only if the move
// constructor is noexcept. Otherwise it falls back to copying, because
// a throwing move would leave the vector in an inconsistent state.
```

### A Complex Real-World Example: Transaction Processing

```cpp
class Database {
public:
    // Strong guarantee: either the entire transaction succeeds,
    // or the database is unchanged.
    void executeTransaction(const std::vector<Operation>& ops) {
        // Step 1: Create a snapshot (copy) of affected data.
        Snapshot snapshot = createSnapshot(ops);

        // Step 2: Apply operations to the snapshot.
        // If any operation throws, the real data is untouched.
        for (const auto& op : ops) {
            applyToSnapshot(snapshot, op);   // May throw
        }

        // Step 3: Commit the snapshot (swap into place).
        // This step must be noexcept.
        commitSnapshot(std::move(snapshot));  // noexcept
    }

private:
    Snapshot createSnapshot(const std::vector<Operation>& ops);
    void applyToSnapshot(Snapshot& snap, const Operation& op);
    void commitSnapshot(Snapshot&& snap) noexcept;
};
```

### RAII: The Foundation of Exception Safety

RAII (Resource Acquisition Is Initialization) is the single most important
technique for writing exception-safe code. Every resource should be managed
by an object whose destructor releases it.

```cpp
// BAD: Manual resource management is not exception-safe.
void processFile(const std::string& filename) {
    FILE* fp = fopen(filename.c_str(), "r");
    if (!fp) throw std::runtime_error("Cannot open file");

    char* buffer = new char[4096];

    // If readData throws, both fp and buffer are leaked.
    readData(fp, buffer);

    delete[] buffer;
    fclose(fp);
}

// GOOD: RAII manages all resources.
void processFile(const std::string& filename) {
    // ifstream closes itself on destruction (RAII).
    std::ifstream file(filename);
    if (!file) throw std::runtime_error("Cannot open file");

    // vector manages its own memory (RAII).
    std::vector<char> buffer(4096);

    // If readData throws, both file and buffer are cleaned up
    // automatically by their destructors.
    readData(file, buffer);
}
```

### When the Strong Guarantee Is Not Practical

The strong guarantee cannot always be achieved efficiently. Consider a
function that operates on two objects:

```cpp
void transferFunds(Account& from, Account& to, double amount) {
    from.withdraw(amount);    // Strong guarantee on 'from'
    to.deposit(amount);       // Strong guarantee on 'to'
}
```

Even though both `withdraw` and `deposit` individually offer the strong
guarantee, `transferFunds` as a whole does not. If `deposit` throws after
`withdraw` has succeeded, rolling back the withdrawal requires calling
`from.deposit(amount)`, which itself could throw.

In such cases, the basic guarantee is often the practical choice. The strong
guarantee would require either:
- A copy-and-swap of both Account objects (possibly expensive), or
- A transactional log with undo/redo capability (complex).

### Things to Remember

- **Exception-safe functions leak no resources and allow no data structures to
  become corrupted when exceptions are thrown**, even when those functions
  call other functions that might throw.

- **The strong guarantee can often be implemented via copy-and-swap**, but the
  strong guarantee is not practical for all functions (especially those that
  modify multiple independent objects).

- **A function can usually offer a guarantee no stronger than the weakest
  guarantee of the functions it calls.** If your function calls a function
  offering only the basic guarantee, the best your function can generally
  offer is the basic guarantee.

- **Use RAII to manage resources.** `lock_guard`, `unique_ptr`, `shared_ptr`,
  `fstream`, and similar types ensure cleanup happens automatically.

- **Mark functions `noexcept` when they truly cannot throw**, especially
  move operations, swap functions, and destructors.

---
