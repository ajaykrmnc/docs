# Item 10: Have Assignment Operators Return a Reference to `*this`

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
