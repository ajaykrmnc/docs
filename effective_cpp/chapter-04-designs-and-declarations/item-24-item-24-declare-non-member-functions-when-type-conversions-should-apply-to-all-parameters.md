# Item 24: Declare Non-Member Functions When Type Conversions Should Apply to All Parameters

## Visual Summary

```text
┌───────────────────────────────────────────────────────────────────────────┐
│ITEM 24: DECLARE NON-MEMBER FUNCTIONS WHEN TYPE CONVERSIONS SHOULD APPLY TO│
├───────────────────────────────────────────────────────────────────────────┤
│ 1. Binary operator as member -> left operand must already be class type.  │
│ 2. Implicit conversion only helps right operand.                          │
│ 3. Non-member operator -> both operands can be converted symmetrically.   │
│ 4. Friend only if private access is truly required.                       │
│ 5. Meaning: symmetric operations usually belong outside the class.        │
└───────────────────────────────────────────────────────────────────────────┘
```

This item addresses a specific but important situation: when you want implicit type
conversions to work for **all** arguments of a function, including the object on which
a member function would be called (i.e., `*this`).

## Visual Deep Dive

```text
┌───────────────────────────────────────────────────────────────────────────┐
│                         MEMBER OPERATOR ASYMMETRY                         │
├───────────────────────────────────────────────────────────────────────────┤
│ lhs.operator*(rhs) is required                                            │
│                                     ▼                                     │
│ lhs must already be class type                                            │
│                                     ▼                                     │
│ Only rhs can benefit from conversion                                      │
│                                     ▼                                     │
│ 2 * rational may fail while rational * 2 works                            │
└───────────────────────────────────────────────────────────────────────────┘
```

```text
┌───────────────────────────────────────────────────────────────────────────┐
│                            NON-MEMBER SYMMETRY                            │
├───────────────────────────────────────────────────────────────────────────┤
│ operator*(lhs, rhs) is ordinary function call                             │
│                                     ▼                                     │
│ Both operands participate in overload resolution                          │
│                                     ▼                                     │
│ Implicit conversions can apply to both sides                              │
│                                     ▼                                     │
│ Arithmetic feels natural                                                  │
└───────────────────────────────────────────────────────────────────────────┘
```

### The Rational Number Multiplication Problem

```cpp
class Rational {
public:
    Rational(int numerator = 0, int denominator = 1);  // Not explicit -- allows
                                                         // implicit int-to-Rational

    int numerator() const { return n_; }
    int denominator() const { return d_; }

    // Attempt: operator* as a member function
    const Rational operator*(const Rational& rhs) const;

private:
    int n_, d_;
};
```

This seems to work:

```cpp
Rational oneHalf(1, 2);
Rational result;

result = oneHalf * 2;   // OK! Same as: oneHalf.operator*(Rational(2))
                          // The int 2 is implicitly converted to Rational(2, 1)
                          // via the non-explicit constructor.

result = 2 * oneHalf;   // ERROR! Same as: 2.operator*(oneHalf)
                          // int doesn't have an operator* that takes a Rational!
                          // The compiler also tries:
                          //   operator*(2, oneHalf)
                          // but no such non-member function exists.
```

The asymmetry is the problem. When `operator*` is a member function, the left-hand operand
must be a `Rational` (it becomes `*this`). Implicit conversions are never applied to `*this` --
only to function arguments. So `2 * oneHalf` fails because `2` is not a `Rational` and can't
be implicitly converted in the `*this` position.

### The Solution: Make operator* a Non-Member Function

```cpp
class Rational {
public:
    Rational(int numerator = 0, int denominator = 1);  // Implicit conversion allowed
    int numerator() const { return n_; }
    int denominator() const { return d_; }

    // No operator* member function!

private:
    int n_, d_;
};

// Non-member operator*
const Rational operator*(const Rational& lhs, const Rational& rhs) {
    return Rational(lhs.numerator() * rhs.numerator(),
                    lhs.denominator() * rhs.denominator());
}
```

Now both forms work:

```cpp
Rational oneHalf(1, 2);
Rational result;

result = oneHalf * 2;   // OK! operator*(oneHalf, Rational(2))
                          // 2 is implicitly converted to Rational(2, 1)

result = 2 * oneHalf;   // OK! operator*(Rational(2), oneHalf)
                          // 2 is implicitly converted to Rational(2, 1)

result = 2 * 3;          // Still uses built-in int multiplication
                          // (no Rational involved, so no conversion)
```

### Should operator* Be a Friend?

Notice that the non-member `operator*` above only uses `numerator()` and `denominator()` --
both public member functions. It doesn't need private access. Therefore, **it should not be
a friend.**

```cpp
// BAD: unnecessary friendship
class Rational {
    friend const Rational operator*(const Rational& lhs, const Rational& rhs);
    // ...
};

// This works, but the friendship is gratuitous.
// operator* can do everything it needs through the public interface.

// GOOD: non-member non-friend (as shown above)
// Maximizes encapsulation (Item 23) while supporting type conversions.
```

The takeaway from Items 23 and 24 combined: if a function doesn't need private access,
it shouldn't be a member or a friend. The only reason to make it a friend would be if
it genuinely needs access to private data.

### What About Explicit Constructors?

If the `Rational` constructor were `explicit`, implicit conversions would be disabled:

```cpp
class Rational {
public:
    explicit Rational(int numerator = 0, int denominator = 1);
    // ...
};

Rational oneHalf(1, 2);
Rational result = oneHalf * 2;  // ERROR! Can't implicitly convert 2 to Rational
Rational result = oneHalf * Rational(2);  // OK -- explicit conversion
```

Whether to use `explicit` depends on your design goals. For a numeric type like `Rational`,
implicit conversion from `int` is usually desirable (it mirrors how `int` implicitly
converts to `double`). For other types, `explicit` is usually safer.

### Real-World Example: A Vector2D Class

```cpp
class Vector2D {
public:
    Vector2D(double x = 0, double y = 0) : x_(x), y_(y) {}

    double x() const { return x_; }
    double y() const { return y_; }

    // operator+= is a member -- it modifies *this
    Vector2D& operator+=(const Vector2D& rhs) {
        x_ += rhs.x_;
        y_ += rhs.y_;
        return *this;
    }

    // operator*= (scalar) is a member -- it modifies *this
    Vector2D& operator*=(double scalar) {
        x_ *= scalar;
        y_ *= scalar;
        return *this;
    }

private:
    double x_, y_;
};

// operator+ is a non-member -- both sides should support conversion
Vector2D operator+(const Vector2D& lhs, const Vector2D& rhs) {
    return Vector2D(lhs.x() + rhs.x(), lhs.y() + rhs.y());
}

// operator* (scalar) is a non-member -- we want both:
//   vector * scalar
//   scalar * vector
Vector2D operator*(const Vector2D& v, double scalar) {
    return Vector2D(v.x() * scalar, v.y() * scalar);
}

Vector2D operator*(double scalar, const Vector2D& v) {
    return v * scalar;  // Delegate to the other overload
}

// Usage:
Vector2D v(3, 4);
Vector2D w = v * 2.0;    // OK
Vector2D x = 2.0 * v;    // OK -- would fail if operator* were a member
Vector2D y = v + w;       // OK
```

### Real-World Example: Comparison Operators

```cpp
class Temperature {
public:
    Temperature(double kelvin) : kelvin_(kelvin) {}  // Implicit -- intentional

    double kelvin() const { return kelvin_; }
    double celsius() const { return kelvin_ - 273.15; }
    double fahrenheit() const { return kelvin_ * 9.0/5.0 - 459.67; }

private:
    double kelvin_;
};

// Non-member comparisons -- both sides can undergo implicit conversion
bool operator==(const Temperature& lhs, const Temperature& rhs) {
    return lhs.kelvin() == rhs.kelvin();
}

bool operator<(const Temperature& lhs, const Temperature& rhs) {
    return lhs.kelvin() < rhs.kelvin();
}

// etc. for !=, >, <=, >=

// Usage:
Temperature boiling(373.15);

if (boiling == 373.15) { /* ... */ }  // OK: 373.15 converts to Temperature
if (373.15 == boiling) { /* ... */ }  // OK: works because operator== is non-member
// If operator== were a member function, the second form would fail.
```

### Koenig Lookup (Argument-Dependent Lookup, ADL)

When you call a non-member function, the compiler searches for the function not only in
the usual scopes but also in the **namespaces of the argument types**. This is called
Argument-Dependent Lookup (ADL), or Koenig Lookup after Andrew Koenig who proposed it.

```cpp
namespace Geometry {

class Point {
public:
    Point(double x, double y) : x_(x), y_(y) {}
    double x() const { return x_; }
    double y() const { return y_; }
private:
    double x_, y_;
};

// Non-member function in the same namespace as Point
double distance(const Point& a, const Point& b) {
    double dx = a.x() - b.x();
    double dy = a.y() - b.y();
    return std::sqrt(dx*dx + dy*dy);
}

// Non-member operator
Point operator+(const Point& a, const Point& b) {
    return Point(a.x() + b.x(), a.y() + b.y());
}

}  // namespace Geometry

// Client code -- no "using" declaration needed!
int main() {
    Geometry::Point p1(1, 2);
    Geometry::Point p2(4, 6);

    double d = distance(p1, p2);   // Found via ADL! The compiler searches
                                    // Geometry:: because p1 and p2 are in Geometry.

    Geometry::Point p3 = p1 + p2;  // Also found via ADL.
}
```

ADL is the reason why `std::cout << "hello"` works -- `operator<<` is a non-member function
in namespace `std`, and it's found via ADL because `std::cout` is in namespace `std`.

### Things to Remember

- If you need type conversions on all parameters to a function (including the one that
  would otherwise be pointed to by `this`), the function must be a non-member.

---
