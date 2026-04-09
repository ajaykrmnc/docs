# Item 3: Use `const` Whenever Possible

### Core Concept

`const` is one of C++'s most powerful and versatile tools. It allows you to communicate and enforce the 
semantic constraint that an object should not be modified. The compiler enforces this constraint, catching 
errors at compile time.

### `const` with Pointers

```cpp
char greeting[] = "Hello";

char* p = greeting;                // non-const pointer, non-const data
const char* p = greeting;          // non-const pointer, const data
char* const p = greeting;          // const pointer, non-const data
const char* const p = greeting;    // const pointer, const data

// Rule: If const appears to the LEFT of the *, the data is const
// Rule: If const appears to the RIGHT of the *, the pointer is const

// These two are equivalent:
const char* p;    // pointer to const char
char const* p;    // pointer to const char (same thing, different style)
```

### `const` with Iterators

```cpp
#include <vector>

std::vector<int> vec = {1, 2, 3, 4, 5};

// const iterator = const pointer (T* const)
// The iterator itself can't change, but what it points to can
const std::vector<int>::iterator iter = vec.begin();
*iter = 10;    // OK: changes what iter points to
// ++iter;     // ERROR: iter is const

// iterator to const = pointer to const (const T*)
// The iterator can change, but what it points to can't
std::vector<int>::const_iterator cIter = vec.begin();
// *cIter = 10; // ERROR: *cIter is const
++cIter;         // OK: cIter itself isn't const
```

### `const` Member Functions

```cpp
class TextBlock {
public:
  // Two overloaded operator[]s — one for const objects, one for non-const
  const char& operator[](std::size_t position) const {
    // ... bounds checking, logging, etc.
    return text[position];
  }

  char& operator[](std::size_t position) {
    // ... bounds checking, logging, etc.
    return text[position];
  }

private:
  std::string text;
};

// Usage:
void print(const TextBlock& ctb) {
  std::cout << ctb[0];  // Calls const operator[]
  // ctb[0] = 'x';      // ERROR: const char& can't be assigned to
}

void modify(TextBlock& tb) {
  std::cout << tb[0];   // Calls non-const operator[]
  tb[0] = 'x';          // OK: char& can be assigned to
}
```

### Bitwise vs. Logical Constness

```cpp
// Bitwise constness: the compiler's definition
// A member function is const if it doesn't modify any data members
// BUT this can be too strict OR too lenient:

// Too lenient: bitwise const but logically non-const
class CTextBlock {
public:
  char& operator[](std::size_t position) const {
    return pText[position];  // Compiles! But allows modification through pointer
  }

private:
  char* pText;  // The pointer isn't modified, but what it points to can be!
};

const CTextBlock cctb("Hello");
char* pc = &cctb[0];
*pc = 'J';  // Now cctb has value "Jello" — a "const" object was modified!

// Solution: logical constness with mutable
class TextBlock {
public:
  std::size_t length() const {
    if (!lengthIsValid) {
      textLength = std::strlen(text.c_str());  // OK: mutable members
      lengthIsValid = true;                     // can be modified in const functions
    }
    return textLength;
  }

private:
  std::string text;
  mutable std::size_t textLength;   // These may always be modified,
  mutable bool lengthIsValid;       // even in const member functions
};
```

### Avoiding Duplication Between `const` and Non-`const` Member Functions

```cpp
class TextBlock {
public:
  const char& operator[](std::size_t position) const {
    // Bounds checking
    if (position >= text.size()) {
      throw std::out_of_range("TextBlock::operator[]");
    }
    // Logging
    // Data integrity validation
    // ... lots of shared logic ...
    return text[position];
  }

  char& operator[](std::size_t position) {
    // Cast away const from the return value of the const version
    // This is safe because we KNOW the object is non-const
    // (otherwise the non-const version wouldn't have been called)
    return const_cast<char&>(
      static_cast<const TextBlock&>(*this)[position]
    );
    // Step 1: static_cast<const TextBlock&>(*this) — add const to *this
    // Step 2: call const operator[] — safe, we're calling const version
    // Step 3: const_cast<char&>(...) — remove const from return value
  }

private:
  std::string text;
};

// NEVER do it the other way around (having const call non-const)!
// That would cast away the const-ness of the object, which is dangerous.
```

### `const` in Function Declarations

```cpp
class Rational {
public:
  Rational(int numerator = 0, int denominator = 1);

  int numerator() const;
  int denominator() const;
};

// Return const value to prevent meaningless assignments
const Rational operator*(const Rational& lhs, const Rational& rhs);

// Why const return value?
Rational a, b, c;
// (a * b) = c;    // ERROR with const return value — catches typo
// Programmer probably meant: if (a * b == c)

// const parameters — prevent accidental modification
bool operator==(const Rational& lhs, const Rational& rhs) {
  return lhs.numerator() * rhs.denominator() ==
  rhs.numerator() * lhs.denominator();
}
```

### Things to Remember
- Declaring something `const` helps compilers detect usage errors
- Compilers enforce bitwise constness, but you should program using logical constness
- When `const` and non-`const` member functions have essentially identical implementations, use the 
non-`const` version calling the `const` version to avoid duplication
- `const` can be applied to objects, function parameters, return types, and member functions

---
