# Item 41: Understand implicit interfaces and compile-time polymorphism

### The two worlds of polymorphism

Object-oriented programming revolves around **explicit interfaces** and **runtime polymorphism**:

```cpp
// Explicit interface: the class declaration spells out every operation.
class Widget {
public:
    Widget();
    virtual ~Widget();
    virtual std::size_t size() const;
    virtual void normalize();
    void swap(Widget& other);
};

// Runtime polymorphism: which size() runs is determined at runtime
// via the vtable.
void doProcessing(Widget& w) {
    if (w.size() > 10 && w != someNastyWidget) {
        Widget temp(w);
        temp.normalize();
        temp.swap(w);
    }
}
```

The interface of `Widget` is explicit -- you can open the header file and see every member function signature, every typedef, every data member. Polymorphism happens at runtime through virtual functions and the vtable mechanism.

Templates flip both of these on their head:

```cpp
template <typename T>
void doProcessing(T& w) {
    if (w.size() > 10 && w != someNastyWidget) {
        T temp(w);
        temp.normalize();
        temp.swap(w);
    }
}
```

Now `T` must support an **implicit interface**: it must have a `size()` member function that returns something comparable to `int`, it must support `operator!=`, it must be copy-constructible, and it must have a `normalize()` and `swap()` member function. But none of this is stated in any single class declaration -- it is implied by how `T` is used in the template body.

The polymorphism here is **compile-time**: which `size()` to call, which `operator!=` to invoke, etc., is resolved when the template is instantiated. The mechanism is template instantiation, not vtable dispatch.

### Implicit interfaces in detail

An implicit interface is defined by the set of valid expressions that appear in the template, not by specific function signatures. Consider:

```cpp
template <typename T>
void process(T& obj) {
    // Implicit interface requirement: T must support .begin() and .end()
    // returning iterators, and the iterators must be dereferenceable.
    for (auto it = obj.begin(); it != obj.end(); ++it) {
        std::cout << *it << "\n";
    }
}
```

Any type that satisfies these constraints works:

```cpp
std::vector<int> v = {1, 2, 3};
process(v);  // OK: vector has begin(), end(), iterators support * and !=

std::list<std::string> l = {"hello", "world"};
process(l);  // OK: list also satisfies the implicit interface

std::map<int, double> m = {{1, 1.1}, {2, 2.2}};
process(m);  // OK: map's iterators dereference to std::pair, which supports <<
              // only if operator<< is defined for pair -- this would fail at
              // compile time, illustrating the implicit interface check.
```

### Constraints are on expressions, not types

A crucial insight: the implicit interface does not require that `size()` returns an integral type. It requires that the expression `w.size() > 10` is valid and yields something convertible to `bool`. This is far more flexible:

```cpp
class Gadget {
public:
    // size() returns a custom type, not size_t
    SizeProxy size() const;
    void normalize();
    void swap(Gadget& other);
};

// This is fine as long as SizeProxy supports operator>(int)
// and the result is convertible to bool.
class SizeProxy {
public:
    bool operator>(int rhs) const { return value_ > rhs; }
private:
    int value_;
};
```

### Compile-time polymorphism with CRTP

The Curiously Recurring Template Pattern (CRTP) is a powerful form of compile-time polymorphism:

```cpp
template <typename Derived>
class Shape {
public:
    double area() const {
        // Compile-time dispatch: calls the derived class's implementation
        return static_cast<const Derived*>(this)->area_impl();
    }

    void print() const {
        std::cout << "Area: " << area() << "\n";
    }
};

class Circle : public Shape<Circle> {
    double radius_;
public:
    explicit Circle(double r) : radius_(r) {}
    double area_impl() const { return 3.14159265 * radius_ * radius_; }
};

class Rectangle : public Shape<Rectangle> {
    double w_, h_;
public:
    Rectangle(double w, double h) : w_(w), h_(h) {}
    double area_impl() const { return w_ * h_; }
};

template <typename ShapeType>
void displayArea(const Shape<ShapeType>& s) {
    s.print();  // Compile-time polymorphism, no vtable
}

int main() {
    Circle c(5.0);
    Rectangle r(3.0, 4.0);
    displayArea(c);  // "Area: 78.5398"
    displayArea(r);  // "Area: 12"
}
```

No virtual functions, no vtable overhead -- the dispatch is resolved entirely at compile time.

### Combining both kinds of polymorphism

In real systems you often use both. Runtime polymorphism lets you store heterogeneous objects in containers; compile-time polymorphism gives you zero-overhead abstraction:

```cpp
// Runtime polymorphism for a plugin system
class Renderer {
public:
    virtual ~Renderer() = default;
    virtual void render(const Scene& scene) = 0;
};

// Compile-time polymorphism for a high-performance math library
template <typename T>
T dot(const std::vector<T>& a, const std::vector<T>& b) {
    T result = T();
    for (std::size_t i = 0; i < a.size(); ++i)
        result += a[i] * b[i];
    return result;
}
```

### Things to Remember

- Both classes and templates support interfaces and polymorphism.
- For classes, interfaces are explicit and centered on function signatures. Polymorphism occurs at runtime through virtual functions.
- For template parameters, interfaces are implicit and based on valid expressions. Polymorphism occurs at compile time through template instantiation and function overloading resolution.
- Implicit interface constraints are on expressions, not on types. An expression like `w.size() > 10` does not mandate a particular return type for `size()` -- only that the complete expression is valid and yields something convertible to `bool`.

---
