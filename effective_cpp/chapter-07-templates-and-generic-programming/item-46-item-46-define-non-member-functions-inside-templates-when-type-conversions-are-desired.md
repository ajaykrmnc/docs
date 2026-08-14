# Item 46: Define non-member functions inside templates when type conversions are desired

## Visual Summary

```text
┌───────────────────────────────────────────────────────────────────────────┐
│ITEM 46: DEFINE NON-MEMBER FUNCTIONS INSIDE TEMPLATES WHEN TYPE CONVERSIONS│
├───────────────────────────────────────────────────────────────────────────┤
│ 1. Class template + non-member operator -> conversions on both operands   │
│ desired.                                                                  │
│ 2. Function template argument deduction does not use implicit             │
│ conversions.                                                              │
│ 3. Define friend non-member inside class template -> concrete function    │
│ generated with class.                                                     │
│ 4. Then ordinary overload resolution can use conversions.                 │
│ 5. Meaning: inside-template friend functions combine symmetry with        │
│ usable conversions.                                                       │
└───────────────────────────────────────────────────────────────────────────┘
```

## Visual Deep Dive

```text
┌───────────────────────────────────────────────────────────────────────────┐
│                     FUNCTION TEMPLATE DEDUCTION LIMIT                     │
├───────────────────────────────────────────────────────────────────────────┤
│ operator* is a separate function template                                 │
│                                     ▼                                     │
│ Compiler tries to deduce T from arguments                                 │
│                                     ▼                                     │
│ Implicit conversions are not used for deduction                           │
│                                     ▼                                     │
│ Mixed Rational/int call may fail                                          │
└───────────────────────────────────────────────────────────────────────────┘
```

```text
┌───────────────────────────────────────────────────────────────────────────┐
│                        FRIEND INSIDE TEMPLATE FLOW                        │
├───────────────────────────────────────────────────────────────────────────┤
│ Class template instantiates Rational<T>                                   │
│                                     ▼                                     │
│ Friend non-member operator for that T is generated                        │
│                                     ▼                                     │
│ Overload resolution sees concrete function                                │
│                                     ▼                                     │
│ Implicit conversions can now apply                                        │
└───────────────────────────────────────────────────────────────────────────┘
```

### The problem: templates and implicit type conversions don't mix

Recall from Item 24 that mixed-mode arithmetic (e.g., `Rational * int`) requires non-member functions so that implicit conversions can apply to all arguments. When you templatize `Rational`, this breaks:

```cpp
template <typename T>
class Rational {
public:
    Rational(const T& numerator = 0, const T& denominator = 1)
        : num_(numerator), den_(denominator) {}

    const T& numerator() const { return num_; }
    const T& denominator() const { return den_; }

private:
    T num_, den_;
};

// Non-member operator*
template <typename T>
const Rational<T> operator*(const Rational<T>& lhs, const Rational<T>& rhs) {
    return Rational<T>(lhs.numerator() * rhs.numerator(),
                       lhs.denominator() * rhs.denominator());
}

Rational<int> oneHalf(1, 2);
Rational<int> result = oneHalf * 2;  // ERROR!
```

Why does this fail? During template argument deduction, implicit conversions are **not** considered. The compiler sees `oneHalf * 2` and tries to deduce `T` for `operator*`:
- From `oneHalf` (type `Rational<int>`), it deduces `T = int`.
- From `2` (type `int`), it cannot deduce `T` because `int` is not `Rational<something>`.

Template argument deduction fails, and the compiler never even considers the implicit conversion from `int` to `Rational<int>`.

### Solution: declare the function as a friend inside the class template

When a class template is instantiated, the declarations of its friend functions become known. Since they are not themselves templates (they are specific functions associated with a specific instantiation), implicit conversions apply to their arguments:

```cpp
template <typename T>
class Rational {
public:
    Rational(const T& numerator = 0, const T& denominator = 1)
        : num_(numerator), den_(denominator) {}

    const T& numerator() const { return num_; }
    const T& denominator() const { return den_; }

    // Friend declaration AND definition inside the class
    friend const Rational operator*(const Rational& lhs, const Rational& rhs) {
        return Rational(lhs.numerator() * rhs.numerator(),
                        lhs.denominator() * rhs.denominator());
    }

private:
    T num_, den_;
};
```

Now:

```cpp
Rational<int> oneHalf(1, 2);
Rational<int> result = oneHalf * 2;  // OK!
// 1) oneHalf is Rational<int>, so the compiler instantiates Rational<int>
// 2) This makes the friend function operator*(const Rational<int>&, const Rational<int>&)
//    a known, non-template function
// 3) For non-template functions, implicit conversions ARE considered
// 4) 2 is converted to Rational<int>(2) via the converting constructor

Rational<int> result2 = 2 * oneHalf;  // Also OK -- conversion on first arg
```

### Why the friend must be defined inside the class

If you only declare the friend inside the class but define it outside, you get a linker error:

```cpp
template <typename T>
class Rational {
public:
    // ...
    friend const Rational operator*(const Rational& lhs, const Rational& rhs);
    // Just a declaration -- the linker won't find the definition
};

// This is a function TEMPLATE, not the friend function!
template <typename T>
const Rational<T> operator*(const Rational<T>& lhs, const Rational<T>& rhs) {
    return Rational<T>(lhs.numerator() * rhs.numerator(),
                       lhs.denominator() * rhs.denominator());
}
```

The friend declaration creates a non-template function `operator*(const Rational<int>&, const Rational<int>&)`. The definition outside the class is a function template. They are different entities. The linker finds the declaration but no matching definition.

Defining the friend inside the class body solves this because the definition is right there.

### Using a helper to keep the friend function short

If the implementation is long, you can delegate to a helper function template:

```cpp
// Helper: a function template (not subject to implicit conversion, but
// that's OK -- it's only called from the friend function)
template <typename T>
const Rational<T> doMultiply(const Rational<T>& lhs, const Rational<T>& rhs) {
    return Rational<T>(lhs.numerator() * rhs.numerator(),
                       lhs.denominator() * rhs.denominator());
}

template <typename T>
class Rational {
public:
    Rational(const T& numerator = 0, const T& denominator = 1)
        : num_(numerator), den_(denominator) {}

    const T& numerator() const { return num_; }
    const T& denominator() const { return den_; }

    // Short friend: just delegates
    friend const Rational operator*(const Rational& lhs, const Rational& rhs) {
        return doMultiply(lhs, rhs);
        // Here, lhs and rhs are already Rational<T>, so template argument
        // deduction for doMultiply succeeds.
    }

private:
    T num_, den_;
};
```

### A more complete example: arithmetic on a Vector class

```cpp
#include <iostream>
#include <cmath>

template <typename T>
class Vec3 {
public:
    Vec3(T x = T(), T y = T(), T z = T()) : x_(x), y_(y), z_(z) {}

    T x() const { return x_; }
    T y() const { return y_; }
    T z() const { return z_; }

    T length() const { return std::sqrt(x_*x_ + y_*y_ + z_*z_); }

    // All arithmetic operators need type conversions on both sides,
    // so they are friends defined inside the class.

    friend Vec3 operator+(const Vec3& a, const Vec3& b) {
        return Vec3(a.x_ + b.x_, a.y_ + b.y_, a.z_ + b.z_);
    }

    friend Vec3 operator-(const Vec3& a, const Vec3& b) {
        return Vec3(a.x_ - b.x_, a.y_ - b.y_, a.z_ - b.z_);
    }

    // Scalar multiplication: Vec3 * scalar and scalar * Vec3
    friend Vec3 operator*(const Vec3& v, const T& s) {
        return Vec3(v.x_ * s, v.y_ * s, v.z_ * s);
    }

    friend Vec3 operator*(const T& s, const Vec3& v) {
        return v * s;
    }

    // Dot product
    friend T dot(const Vec3& a, const Vec3& b) {
        return a.x_ * b.x_ + a.y_ * b.y_ + a.z_ * b.z_;
    }

    // Cross product
    friend Vec3 cross(const Vec3& a, const Vec3& b) {
        return Vec3(a.y_ * b.z_ - a.z_ * b.y_,
                    a.z_ * b.x_ - a.x_ * b.z_,
                    a.x_ * b.y_ - a.y_ * b.x_);
    }

    friend std::ostream& operator<<(std::ostream& os, const Vec3& v) {
        return os << "(" << v.x_ << ", " << v.y_ << ", " << v.z_ << ")";
    }

private:
    T x_, y_, z_;
};

int main() {
    Vec3<double> a(1.0, 2.0, 3.0);
    Vec3<double> b(4.0, 5.0, 6.0);

    std::cout << "a + b = " << (a + b) << "\n";           // (5, 7, 9)
    std::cout << "a * 2 = " << (a * 2) << "\n";           // (2, 4, 6) -- int 2 converts to double
    std::cout << "3 * b = " << (3 * b) << "\n";           // (12, 15, 18) -- int 3 converts
    std::cout << "dot(a,b) = " << dot(a, b) << "\n";      // 32
    std::cout << "cross(a,b) = " << cross(a, b) << "\n";  // (-3, 6, -3)
}
```

### Comparison operators with friend in templates

```cpp
template <typename T>
class Money {
public:
    explicit Money(T amount) : amount_(amount) {}

    T amount() const { return amount_; }

    friend bool operator==(const Money& a, const Money& b) {
        return a.amount_ == b.amount_;
    }

    friend bool operator<(const Money& a, const Money& b) {
        return a.amount_ < b.amount_;
    }

    friend bool operator!=(const Money& a, const Money& b) { return !(a == b); }
    friend bool operator>(const Money& a, const Money& b) { return b < a; }
    friend bool operator<=(const Money& a, const Money& b) { return !(b < a); }
    friend bool operator>=(const Money& a, const Money& b) { return !(a < b); }

private:
    T amount_;
};
```

### Things to Remember

- When writing a class template that offers functions related to the template that support implicit type conversions on all parameters, define those functions as friends inside the class template.
- Template argument deduction does not consider implicit conversions. A friend function declared inside a class template instantiation is a non-template function, and implicit conversions apply to its arguments normally.
- If the friend function body is long, have it call a helper function template defined outside the class.

---
