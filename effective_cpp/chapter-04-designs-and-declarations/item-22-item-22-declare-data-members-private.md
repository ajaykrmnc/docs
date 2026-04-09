# Item 22: Declare Data Members Private

This item is about encapsulation. It argues that data members should **always** be `private`.
The reasoning is based on access control, flexibility, and a fundamental truth about
software evolution: implementations change, but interfaces should be stable.

### Why Not Public?

**Reason 1: Syntactic consistency.** If data members aren't public, the only way for clients
to access an object is via member functions. The client never has to wonder whether to use
parentheses or not -- it's always parentheses.

```cpp
// BAD: public data members lead to inconsistent access syntax
class SpreadsheetCell {
public:
    double value;           // Accessed as: cell.value
    double cachedValue();   // Accessed as: cell.cachedValue()
    // Client must remember: is it 'value' or 'value()'?
};

// GOOD: all access through functions -- consistent syntax
class SpreadsheetCell {
public:
    double value() const;       // Always use ()
    double cachedValue() const; // Always use ()
private:
    double value_;
    mutable double cachedValue_;
    mutable bool cacheValid_;
};
```

**Reason 2: Fine-grained access control.** With member functions, you can implement
no access, read-only access, write-only access, or read-write access. Public data
members give you only read-write -- all or nothing.

```cpp
class AccessControlled {
public:
    // Read-only: temperature can be read but not set externally
    double temperature() const { return temperature_; }

    // Write-only: password can be set but never read back
    void setPassword(const std::string& pwd) { passwordHash_ = hash(pwd); }

    // Read-write: name can be read and written
    std::string name() const { return name_; }
    void setName(const std::string& n) { name_ = n; }

    // No access: internalState is completely hidden
    // (no getter or setter provided)

private:
    double temperature_;
    size_t passwordHash_;
    std::string name_;
    int internalState_;
};
```

**Reason 3: Encapsulation -- the ability to change the implementation.**

If data members are public, changing them breaks all client code that uses them. If data
members are private and accessed through functions, you can change the internal representation
without changing the interface.

```cpp
// Version 1: SpeedOMeter stores speed as mph
class SpeedOMeter {
public:
    double speedInMph() const { return speed_; }
    double speedInKph() const { return speed_ * 1.60934; }
    void setSpeed(double mph) { speed_ = mph; }

private:
    double speed_;  // stored in mph
};

// Version 2: Decision to store in kph instead (internal change)
// Client code doesn't change AT ALL
class SpeedOMeter {
public:
    double speedInMph() const { return speed_ / 1.60934; }  // Compute from kph
    double speedInKph() const { return speed_; }             // Direct return
    void setSpeed(double mph) { speed_ = mph * 1.60934; }   // Convert to kph

private:
    double speed_;  // now stored in kph -- internal change only
};
```

### Encapsulation and Breakage: The Quantitative Argument

The encapsulation of a data member is inversely proportional to the amount of code that
might be broken if that data member changes. If a data member is `public`, the amount of
code that could be affected is **all client code** -- an unknowably large amount. If it's
`private`, the amount of code that could be affected is limited to the **member functions
and friends** of the class.

```cpp
// If x is public:
class Point {
public:
    double x, y;  // Every piece of code that uses Point::x is coupled
                    // to the fact that x is a double data member.
                    // Changing it breaks an unknowable number of clients.
};

// If x is private with accessor:
class Point {
public:
    double x() const { return x_; }
    double y() const { return y_; }
    void setX(double newX) { x_ = newX; }
    void setY(double newY) { y_ = newY; }

private:
    double x_, y_;
    // Can later change to:
    //   double r_, theta_;  (polar coordinates)
    // without changing the public interface.
};
```

### Why Not Protected?

The same arguments apply to `protected` data members. Protected is not much more encapsulated
than public.

```cpp
// BAD: Protected data members are almost as bad as public
class Base {
protected:
    int protectedData;  // All derived classes can access this directly.
                         // Changing or removing it breaks all derived classes.
};

class Derived1 : public Base {
    void f() { protectedData = 42; }  // Direct access
};

class Derived2 : public Base {
    void g() { int x = protectedData; }  // Direct access
};

// If we need to change protectedData (rename it, change its type, compute it
// on the fly instead of storing it), ALL derived classes break.
// In a class hierarchy with many derived classes, this can be catastrophic.
```

```cpp
// GOOD: Private data with protected accessor
class Base {
public:
    int getData() const { return data_; }

protected:
    void setData(int d) { data_ = d; }  // Only derived classes can set

private:
    int data_;
    // Can change implementation without breaking derived classes,
    // as long as getData() and setData() maintain their contracts.
};
```

### Real-World Example: Validating Invariants

```cpp
// BAD: Public members can't enforce invariants
class Rectangle {
public:
    double width, height;
    // Nothing stops a client from writing:
    //   rect.width = -5;   // Negative width?!
};

// GOOD: Private members with validation
class Rectangle {
public:
    double width() const { return width_; }
    double height() const { return height_; }

    void setWidth(double w) {
        if (w <= 0) throw std::invalid_argument("Width must be positive");
        width_ = w;
        updateCachedArea();
    }

    void setHeight(double h) {
        if (h <= 0) throw std::invalid_argument("Height must be positive");
        height_ = h;
        updateCachedArea();
    }

    double area() const { return cachedArea_; }  // O(1) lookup

private:
    double width_;
    double height_;
    double cachedArea_;

    void updateCachedArea() { cachedArea_ = width_ * height_; }
};
```

### Real-World Example: Thread-Safe Access

```cpp
// BAD: Public data is impossible to make thread-safe
class Counter {
public:
    int count;  // Data races galore
};

// GOOD: Private data can be made thread-safe without changing the interface
class Counter {
public:
    int count() const {
        std::lock_guard<std::mutex> lock(mutex_);
        return count_;
    }

    void increment() {
        std::lock_guard<std::mutex> lock(mutex_);
        ++count_;
    }

private:
    mutable std::mutex mutex_;
    int count_ = 0;
};
// Clients never know (or need to know) about the locking.
// Thread safety is an implementation detail hidden behind the interface.
```

### Things to Remember

- Declare data members `private`. It gives clients syntactically uniform access to data,
  affords fine-grained access control, allows invariants to be enforced, and offers class
  authors implementation flexibility.
- `protected` is no more encapsulated than `public`.

---
