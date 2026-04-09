# Item 11: Handle Assignment to Self in `operator=`

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
