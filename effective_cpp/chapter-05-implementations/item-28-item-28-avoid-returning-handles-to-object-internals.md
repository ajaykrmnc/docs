# Item 28: Avoid returning "handles" to object internals

## Visual Summary

```text
┌───────────────────────────────────────────────────────────────────────────┐
│          ITEM 28: AVOID RETURNING "HANDLES" TO OBJECT INTERNALS           │
├───────────────────────────────────────────────────────────────────────────┤
│ 1. Method returns pointer/reference/iterator to private internals.        │
│ 2. Caller can mutate private state or keep handle after object            │
│ changes/dies.                                                             │
│ 3. Const handle helps mutation but not dangling lifetime.                 │
│ 4. Return value/proxy/operation instead when possible.                    │
│ 5. Meaning: do not let encapsulation escape through a handle.             │
└───────────────────────────────────────────────────────────────────────────┘
```

A handle is anything that provides access to an object's internals: a
reference, a pointer, or an iterator. Returning handles to object internals
undermines encapsulation, can allow const member functions to enable
modification of object state, and creates the risk of dangling handles.

## Visual Deep Dive

```text
┌───────────────────────────────────────────────────────────────────────────┐
│                            HANDLE ESCAPE FLOW                             │
├───────────────────────────────────────────────────────────────────────────┤
│ Object returns reference/pointer/iterator to internals                    │
│                                     ▼                                     │
│ Caller stores it                                                          │
│                                     ▼                                     │
│ Object mutates or dies                                                    │
│                                     ▼                                     │
│ Handle dangles or breaks invariant                                        │
└───────────────────────────────────────────────────────────────────────────┘
```

```text
┌───────────────────────────────────────────────────────────────────────────┐
│                            SAFER ALTERNATIVES                             │
├───────────────────────────────────────────────────────────────────────────┤
│ Instead of                        | Prefer                                │
│ ----------------------------------+-------------------------------------  │
│ Return mutable ref                | Return value                          │
│ Return pointer to member          | Return const view briefly             │
│ Expose iterator forever           | Provide operation method              │
└───────────────────────────────────────────────────────────────────────────┘
```

### Problem 1: Encapsulation Violation

```cpp
struct Point {
    int x, y;
};

class Rectangle {
public:
    Rectangle(const Point& topLeft, const Point& bottomRight)
        : topLeft_(topLeft), bottomRight_(bottomRight) {}

    // DANGEROUS: Returns a non-const reference to internal data.
    // Client code can modify the internals directly, bypassing any
    // invariant-checking logic that Rectangle might want to enforce.
    Point& upperLeft() const { return topLeft_; }
    Point& lowerRight() const { return bottomRight_; }

private:
    Point topLeft_;
    Point bottomRight_;
};

// Client code:
Rectangle rect(Point{0, 0}, Point{100, 50});

// This compiles and runs! A const-qualified member function is allowing
// modification of the object's internal state through the returned reference.
rect.upperLeft().x = 999;   // Modifies the "private" data!
```

The member functions `upperLeft()` and `lowerRight()` are declared `const`,
promising not to modify the Rectangle. But they return non-const references
to private data members, allowing clients to modify the data anyway.

The core issue: **a data member is only as encapsulated as the most accessible
function returning a reference to it.** Here, `topLeft_` and `bottomRight_` are
declared private but are effectively public because of the returned references.

### Problem 2: Const Member Functions Enabling Mutation

Even if you meant for the class to be fully const-correct:

```cpp
class StringWrapper {
public:
    explicit StringWrapper(const std::string& s) : data_(s) {}

    // The const on the member function only protects the pointer/reference
    // itself (i.e., which object data_ refers to), not the object it
    // points to. Returning a non-const reference to the internal string
    // allows callers to modify the string through a const StringWrapper.
    std::string& get() const { return data_; }

private:
    std::string data_;
};

const StringWrapper sw("hello");
sw.get() = "hacked";   // Compiles! Const-correctness is defeated.
```

### Solution: Return const References (But Beware Dangling)

```cpp
class Rectangle {
public:
    Rectangle(const Point& topLeft, const Point& bottomRight)
        : topLeft_(topLeft), bottomRight_(bottomRight) {}

    // BETTER: Return const references. Callers can read but not modify.
    const Point& upperLeft() const { return topLeft_; }
    const Point& lowerRight() const { return bottomRight_; }

private:
    Point topLeft_;
    Point bottomRight_;
};

// Now this will not compile:
// rect.upperLeft().x = 999;   // Error: assignment to member of const reference
```

This addresses the mutation problem but introduces a new one: **dangling handles**.

### Problem 3: Dangling Handles

A dangling handle is a reference (or pointer or iterator) that refers to an
object that no longer exists. This is one of the most pernicious bugs in C++.

```cpp
class GUIObject { /* ... */ };

// Suppose this function returns a Rectangle by value (a temporary):
const Rectangle boundingBox(const GUIObject& obj);

// Client code:
GUIObject button;

// pUpperLeft points into the temporary Rectangle returned by boundingBox().
// At the semicolon, the temporary is destroyed, and pUpperLeft dangles.
const Point* pUpperLeft = &(boundingBox(button).upperLeft());

// UNDEFINED BEHAVIOR: dereferencing a dangling pointer.
std::cout << pUpperLeft->x << "\n";
```

The temporary `Rectangle` returned by `boundingBox()` is destroyed at the end
of the full expression (the semicolon). The pointer `pUpperLeft` now points
to memory that has been reclaimed. Any use of it is undefined behavior.

### Real-World Dangling Handle Scenarios

**Scenario 1: Returning references from containers of smart pointers**

```cpp
class WidgetCache {
public:
    // DANGEROUS: If the shared_ptr is reset or the Widget is removed from
    // the cache, the reference dangles.
    const Widget& getWidget(int id) const {
        auto it = cache_.find(id);
        if (it == cache_.end()) throw std::runtime_error("not found");
        return *(it->second);   // Reference into the object owned by shared_ptr
    }

    void removeWidget(int id) {
        cache_.erase(id);   // The Widget is destroyed here...
    }

private:
    std::map<int, std::shared_ptr<Widget>> cache_;
};

// Usage:
WidgetCache cache;
// cache.addWidget(1, std::make_shared<Widget>(/* ... */));

const Widget& w = cache.getWidget(1);  // Reference is valid here.
cache.removeWidget(1);                  // Widget is destroyed!
w.doSomething();                        // UNDEFINED BEHAVIOR: dangling reference.

// SAFER ALTERNATIVE: Return a shared_ptr so the caller shares ownership.
// std::shared_ptr<Widget> getWidget(int id) const {
//     auto it = cache_.find(id);
//     if (it == cache_.end()) return nullptr;
//     return it->second;   // Caller holds a shared_ptr; Widget stays alive.
// }
```

**Scenario 2: Returning iterators or pointers to internal containers**

```cpp
class MessageQueue {
public:
    // DANGEROUS: The returned pointer is invalidated if the internal
    // vector reallocates (e.g., on the next push).
    const std::string* front() const {
        if (messages_.empty()) return nullptr;
        return &messages_.front();
    }

    void push(const std::string& msg) {
        messages_.push_back(msg);   // May reallocate, invalidating pointers!
    }

private:
    std::vector<std::string> messages_;
};

// Usage:
MessageQueue q;
q.push("hello");
const std::string* msg = q.front();   // Valid pointer.
q.push("world");                       // Vector may reallocate!
std::cout << *msg << "\n";             // POTENTIALLY UNDEFINED BEHAVIOR.

// SAFER ALTERNATIVE: Return by value.
// std::string front() const {
//     if (messages_.empty()) throw std::runtime_error("empty");
//     return messages_.front();   // Returns a copy; no dangling possible.
// }
```

**Scenario 3: Storing references returned from temporary expressions**

```cpp
class Config {
public:
    const std::string& getHostname() const { return hostname_; }
private:
    std::string hostname_ = "localhost";
};

// A factory function that returns a Config by value:
Config loadConfig();

// DANGEROUS:
const std::string& host = loadConfig().getHostname();
// The temporary Config is destroyed at the semicolon.
// 'host' is now a dangling reference.

// SAFE:
Config config = loadConfig();              // Keep the Config alive.
const std::string& host2 = config.getHostname();  // Now it is fine.

// ALSO SAFE:
std::string host3 = loadConfig().getHostname();   // Copy the string.
```

### When Returning Handles Is Acceptable

There are cases where returning handles is appropriate:

```cpp
// operator[] for containers MUST return a reference to be useful.
// This is an accepted, well-understood convention.
template <typename T>
class MyVector {
public:
    T& operator[](size_t index) { return data_[index]; }
    const T& operator[](size_t index) const { return data_[index]; }
private:
    T* data_;
    size_t size_;
};

// std::string::c_str() returns a pointer to internal data. This is
// acceptable because the documentation clearly states the pointer is
// invalidated by any non-const operation on the string, and the
// convention is universally understood.
```

Even `operator[]` and similar functions constitute exceptions to the rule, not
refutations of it. The general guideline stands: avoid returning handles to
internals whenever you can.

### Things to Remember

- **Avoid returning handles** (references, pointers, iterators) **to object
  internals.** Not returning handles increases encapsulation, helps `const`
  member functions act `const`, and minimizes the creation of dangling handles.

- **If you must return a handle, return a `const` handle** to prevent callers
  from modifying the object's internals through the handle.

- **Even `const` handles can dangle.** A handle to data inside a temporary
  object becomes invalid when the temporary is destroyed. Be especially careful
  with function return values.

- **When handles are part of the interface contract** (like `operator[]`),
  document the lifetime guarantees clearly.

---
