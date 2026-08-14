# Item 23: Prefer Non-Member Non-Friend Functions to Member Functions

## Visual Summary

```text
┌───────────────────────────────────────────────────────────────────────────┐
│    ITEM 23: PREFER NON-MEMBER NON-FRIEND FUNCTIONS TO MEMBER FUNCTIONS    │
├───────────────────────────────────────────────────────────────────────────┤
│ 1. Function needs no private access -> it does not need to be a member.   │
│ 2. Member function -> increases class surface and coupling.               │
│ 3. Non-member non-friend -> same capability with better encapsulation.    │
│ 4. Group related helpers in namespaces/headers for discoverability.       │
│ 5. Meaning: fewer privileged functions means stronger encapsulation.      │
└───────────────────────────────────────────────────────────────────────────┘
```

This item contains one of the most counterintuitive pieces of advice in the book. Many
programmers believe that putting a function inside a class (making it a member) increases
encapsulation because the function "belongs" to the class. In fact, the opposite is true:
in many cases, a **non-member non-friend function** provides **more** encapsulation, **more**
packaging flexibility, and **more** functional extensibility.

## Visual Deep Dive

```text
┌───────────────────────────────────────────────────────────────────────────┐
│                            ENCAPSULATION TEST                             │
├───────────────────────────────────────────────────────────────────────────┤
│ Does function need private data?                                          │
│                                     ▼                                     │
│ No -> make non-member non-friend                                          │
│                                     ▼                                     │
│ Place in same namespace for discovery                                     │
│                                     ▼                                     │
│ Class privileged surface stays small                                      │
└───────────────────────────────────────────────────────────────────────────┘
```

```text
┌───────────────────────────────────────────────────────────────────────────┐
│                            FUNCTION PLACEMENT                             │
├───────────────────────────────────────────────────────────────────────────┤
│ Member/friend                     | Non-member                            │
│ ----------------------------------+-------------------------------------  │
│ Needs internals                   | Uses public API only                  │
│ Part of invariant                 | Composes operations                   │
│ Privileged coupling               | Better encapsulation                  │
└───────────────────────────────────────────────────────────────────────────┘
```

### The Web Browser Example

```cpp
class WebBrowser {
public:
    void clearCache();
    void clearHistory();
    void removeCookies();

    // Should clearEverything() be a member function?
    void clearEverything();   // Calls clearCache, clearHistory, removeCookies
};
```

```cpp
// Attempt 1 (member function):
void WebBrowser::clearEverything() {
    clearCache();
    clearHistory();
    removeCookies();
}

// Attempt 2 (non-member non-friend function):
void clearBrowser(WebBrowser& wb) {
    wb.clearCache();
    wb.clearHistory();
    wb.removeCookies();
}
```

Which is better? The non-member non-friend function. Here's why.

### The Encapsulation Argument

Encapsulation means that something is hidden from view. The more things are hidden, the
greater the flexibility to change them. The more things that are encapsulated, the greater
our ability to change them without affecting other code.

The number of functions that can access the private members of a class is a measure of
how **un-encapsulated** those members are. The more functions that can access private data,
the less encapsulated that data is.

- A **member function** can access all private members.
- A **non-member non-friend function** cannot access any private members.

Therefore, choosing a non-member non-friend function over a member function **increases
encapsulation** (all else being equal). The non-member function `clearBrowser` can only
call public functions on `WebBrowser`. It adds no new access to private data.

Note: this reasoning only applies when you're choosing between a member function and a
non-member **non-friend** function. Friends have the same access as members, so choosing
a friend over a member doesn't improve encapsulation.

### Namespace-Based Organization

The natural home for non-member functions associated with a class is the **same namespace**
as the class. This is the C++ way of saying "these functions are related to this class"
without granting them private access.

```cpp
// WebBrowser.h
namespace WebBrowserStuff {

class WebBrowser {
public:
    void clearCache();
    void clearHistory();
    void removeCookies();
    // ...
};

// Convenience function in the same namespace
void clearBrowser(WebBrowser& wb);

}  // namespace WebBrowserStuff
```

### Splitting Functionality Across Headers

Unlike classes, namespaces can be split across multiple header files. This is enormously
useful for managing large interfaces. The standard library does exactly this: `std::vector`
is in `<vector>`, `std::sort` is in `<algorithm>`, etc. -- all in namespace `std`, but
spread across many headers.

```cpp
// webbrowser.h -- core WebBrowser class
namespace WebBrowserStuff {

class WebBrowser { /* ... */ };

// Core non-member functions that nearly everyone needs
void clearBrowser(WebBrowser& wb);

}  // namespace WebBrowserStuff


// webbrowserbookmarks.h -- bookmark-related convenience functions
namespace WebBrowserStuff {

void addBookmark(WebBrowser& wb, const std::string& url);
void removeBookmark(WebBrowser& wb, const std::string& url);
std::vector<std::string> getBookmarks(const WebBrowser& wb);

}  // namespace WebBrowserStuff


// webbrowsercookies.h -- cookie-related convenience functions
namespace WebBrowserStuff {

void importCookies(WebBrowser& wb, const std::string& file);
void exportCookies(const WebBrowser& wb, const std::string& file);
Cookie getCookie(const WebBrowser& wb, const std::string& domain);

}  // namespace WebBrowserStuff
```

Clients include only the headers they need, reducing compilation dependencies. This is
**impossible** with member functions -- all member functions must be declared in the class
definition, which lives in a single header. A client who wants to use `addBookmark` must
include the entire class definition, including declarations for cookie-related and
cache-related functions they don't need.

### Extensibility by Clients

Because namespaces are open, clients can add their own convenience functions:

```cpp
// In the client's own header:
namespace WebBrowserStuff {

// Client-defined convenience function
void clearBrowserAndNotifyUser(WebBrowser& wb, const User& user) {
    clearBrowser(wb);
    user.notify("Browser cleared");
}

}  // namespace WebBrowserStuff
```

A client cannot add member functions to a class they don't control. But they can add
non-member functions to a namespace. This is one of the key extensibility benefits.

### When Member Functions ARE Appropriate

This item does not say "never use member functions." Member functions are appropriate
when the function:

1. Needs access to private data (and no public interface can provide that access), or
2. Is a virtual function (virtual dispatch requires membership), or
3. Is an operator that must be a member (`operator=`, `operator[]`, `operator->`, `operator()`), or
4. Affects the object's internal invariants in a way that can only be done with private access.

```cpp
class String {
public:
    // These MUST be members:
    String& operator=(const String& rhs);  // Assignment operator must be a member
    char& operator[](size_t index);        // Subscript operator must be a member
    size_t size() const;                   // Needs access to internal length_ member

    // This SHOULD be a non-member:
    // friend String operator+(const String& lhs, const String& rhs);
    // See Item 24 for why.

private:
    char* data_;
    size_t length_;
};

// Non-member convenience functions:
bool isAllUpperCase(const String& s) {
    for (size_t i = 0; i < s.size(); ++i) {
        if (!std::isupper(s[i])) return false;
    }
    return true;
}
// isAllUpperCase uses only the public interface. Making it a member would
// decrease encapsulation for no benefit.
```

### Real-World Example: Algorithm-Style Functions

```cpp
class Matrix {
public:
    size_t rows() const;
    size_t cols() const;
    double& operator()(size_t r, size_t c);
    const double& operator()(size_t r, size_t c) const;

private:
    std::vector<double> data_;
    size_t rows_, cols_;
};

// These should be non-member non-friend functions:
// They operate entirely through the public interface.

Matrix transpose(const Matrix& m) {
    Matrix result(m.cols(), m.rows());
    for (size_t r = 0; r < m.rows(); ++r)
        for (size_t c = 0; c < m.cols(); ++c)
            result(c, r) = m(r, c);
    return result;
}

Matrix multiply(const Matrix& a, const Matrix& b) {
    assert(a.cols() == b.rows());
    Matrix result(a.rows(), b.cols());
    for (size_t i = 0; i < a.rows(); ++i)
        for (size_t j = 0; j < b.cols(); ++j) {
            double sum = 0;
            for (size_t k = 0; k < a.cols(); ++k)
                sum += a(i, k) * b(k, j);
            result(i, j) = sum;
        }
    return result;
}

bool isSymmetric(const Matrix& m) {
    if (m.rows() != m.cols()) return false;
    for (size_t r = 0; r < m.rows(); ++r)
        for (size_t c = r + 1; c < m.cols(); ++c)
            if (m(r, c) != m(c, r)) return false;
    return true;
}

// None of these functions need private access.
// Making them non-member non-friend improves encapsulation.
// They can live in different headers for reduced coupling.
// Clients can add their own algorithms (e.g., determinant, inverse)
// without modifying the Matrix class.
```

### Things to Remember

- Prefer non-member non-friend functions to member functions. Doing so increases
  encapsulation, packaging flexibility, and functional extensibility.

---
