# Item 21: Don't Try to Return a Reference When You Must Return an Object

## Visual Summary

```text
┌───────────────────────────────────────────────────────────────────────────┐
│  ITEM 21: DON'T TRY TO RETURN A REFERENCE WHEN YOU MUST RETURN AN OBJECT  │
├───────────────────────────────────────────────────────────────────────────┤
│ 1. Need a result value -> ask where the referenced object would live.     │
│ 2. Local object -> reference dangles after return.                        │
│ 3. Heap object -> caller must delete; leak risk.                          │
│ 4. Static object -> shared mutable state and wrong repeated results.      │
│ 5. Return by value -> compiler can optimize with RVO/move.                │
│ 6. Meaning: references are aliases, not storage for new results.          │
└───────────────────────────────────────────────────────────────────────────┘
```

Once programmers learn about the efficiency costs of pass-by-value (Item 20), they sometimes
become crusaders, determined to eliminate all pass-by-value from their code -- including in
contexts where returning by reference leads to disaster. The result: returning references to
objects that no longer exist.

The key insight: **a reference is just a name for an existing object.** Whenever you see a
reference, you should ask yourself what object it is another name for. If there is no such
object, the reference is dangling and the program has undefined behavior.

## Visual Deep Dive

```text
┌───────────────────────────────────────────────────────────────────────────┐
│                           BAD REFERENCE TARGETS                           │
├───────────────────────────────────────────────────────────────────────────┤
│ Where result lives                | Failure mode                          │
│ ----------------------------------+-------------------------------------  │
│ Local variable                    | Dangling reference                    │
│ Heap allocation                   | Who deletes it?                       │
│ Static object                     | Shared overwritten state              │
└───────────────────────────────────────────────────────────────────────────┘
```

```text
┌───────────────────────────────────────────────────────────────────────────┐
│                             RETURN VALUE FLOW                             │
├───────────────────────────────────────────────────────────────────────────┤
│ Operation creates a new logical value                                     │
│                                     ▼                                     │
│ Return object by value                                                    │
│                                     ▼                                     │
│ Compiler applies RVO/move when possible                                   │
│                                     ▼                                     │
│ Caller receives valid independent result                                  │
└───────────────────────────────────────────────────────────────────────────┘
```

### The Rational Number Example

```cpp
class Rational {
public:
    Rational(int numerator = 0, int denominator = 1);

private:
    int n, d;  // numerator and denominator

    friend const Rational operator*(const Rational& lhs, const Rational& rhs);
};
```

The natural implementation of `operator*` would return a new `Rational`. But a performance-
obsessed programmer might try to avoid the copy by returning a reference:

```cpp
// BAD Attempt #1: Return a reference to a local stack object
const Rational& operator*(const Rational& lhs, const Rational& rhs) {
    Rational result(lhs.n * rhs.n, lhs.d * rhs.d);
    return result;  // DISASTER! result is destroyed when the function exits.
                     // The caller receives a dangling reference.
}

// Any use of the returned reference is undefined behavior:
Rational a(1, 2);
Rational b(3, 5);
Rational c = a * b;  // c is initialized from a reference to a destroyed object.
                       // Might appear to work, might crash, might corrupt memory.
```

```cpp
// BAD Attempt #2: Return a reference to a heap-allocated object
const Rational& operator*(const Rational& lhs, const Rational& rhs) {
    Rational* result = new Rational(lhs.n * rhs.n, lhs.d * rhs.d);
    return *result;  // Who deletes this? The caller? How?
}

// Memory leak -- the caller has no way to delete the object:
Rational w, x, y, z;
w = x * y * z;  // This calls operator* twice:
                  // temp = operator*(x, y)    -- allocates on heap (leak #1)
                  // w = operator*(temp, z)    -- allocates on heap (leak #2)
                  // We have a reference to the second result (assigned to w),
                  // but the first result is leaked forever.
                  // There is no way to retrieve a pointer to it.
```

```cpp
// BAD Attempt #3: Return a reference to a local static object
const Rational& operator*(const Rational& lhs, const Rational& rhs) {
    static Rational result;  // Only one instance, shared across all calls!
    result = Rational(lhs.n * rhs.n, lhs.d * rhs.d);
    return result;
}

// This is broken in a subtle way:
Rational a(1, 2);
Rational b(3, 4);
Rational c(5, 6);
Rational d(7, 8);

if ((a * b) == (c * d)) {
    // This is ALWAYS true!
    // Both calls to operator* modify the SAME static object.
    // By the time == is evaluated, both references point to the same object
    // (which holds the value from the most recent call, c * d).
    // So the comparison is: static_result == static_result
    // which is always true.
    std::cout << "This always prints!\n";
} else {
    std::cout << "This never prints!\n";
}
```

Even an array of statics wouldn't fix the problem -- you'd need to know how many simultaneous
results might be needed, and the comparison issue remains.

### The Correct Solution: Return by Value

```cpp
// GOOD: Just return a new object by value
const Rational operator*(const Rational& lhs, const Rational& rhs) {
    return Rational(lhs.n * rhs.n, lhs.d * rhs.d);
}
```

Yes, this incurs the cost of constructing and destroying the return value. But that cost is
**correct** -- you are paying for the creation of a new object, which is exactly what you need.
Moreover, compilers are allowed to (and routinely do) apply **Return Value Optimization (RVO)
and Named Return Value Optimization (NRVO)**, which eliminate the copy entirely by
constructing the result directly in the caller's memory.

```cpp
// With RVO, this code:
Rational c = a * b;

// is optimized to construct the result directly in c's memory.
// No copy constructor is called. The cost is just one constructor call.
```

In C++11 and later, move semantics provide an additional optimization: even when RVO doesn't
apply, the return value is **moved** rather than copied.

### Real-World Example: String Concatenation

```cpp
// BAD: trying to avoid copies leads to bugs
class MyString {
public:
    // Don't do this!
    const MyString& operator+(const MyString& rhs) const {
        // Where does the result live? Can't be on the stack (dangling).
        // Can't be on the heap (leak). Can't be static (shared state).
        // There is no good answer.
    }
};

// GOOD: return by value
class MyString {
public:
    MyString operator+(const MyString& rhs) const {
        MyString result;
        result.data_ = data_ + rhs.data_;
        return result;  // RVO will likely eliminate the copy.
    }

private:
    std::string data_;
};
```

### When References ARE Appropriate to Return

References are appropriate when the object already exists and will outlive the reference:

```cpp
class Container {
public:
    // GOOD: the element exists in the container and will outlive the call
    int& operator[](size_t index) { return data_[index]; }
    const int& operator[](size_t index) const { return data_[index]; }

    // GOOD: returning *this for chaining
    Container& add(int value) {
        data_.push_back(value);
        return *this;
    }

private:
    std::vector<int> data_;
};

// GOOD: singleton pattern -- the object is static and lives forever
DatabaseManager& DatabaseManager::instance() {
    static DatabaseManager mgr;
    return mgr;
}
```

### Things to Remember

- Never return a pointer or reference to a local stack object, a reference to a heap-
  allocated object, or a pointer or reference to a local static object if there is a
  chance that more than one such object will be needed. (Item 4 provides an example
  of a design where returning a reference to a local static is reasonable: the singleton
  pattern for avoiding the static initialization order problem.)

---
