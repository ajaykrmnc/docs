# Item 20: Prefer Pass-by-Reference-to-const to Pass-by-Value

By default, C++ passes objects to and from functions by value (a trait inherited from C).
Unless you tell it otherwise, function parameters are initialized with **copies** of the
actual arguments, and function callers get back a **copy** of the value returned by the
function. These copies are produced by the objects' copy constructors. This can make
pass-by-value an expensive operation.

### The Cost of Pass-by-Value

```cpp
class Person {
public:
    Person();
    virtual ~Person();

private:
    std::string name;
    std::string address;
};

class Student : public Person {
public:
    Student();
    ~Student();

private:
    std::string schoolName;
    std::string schoolAddress;
};
```

Now consider this function:

```cpp
// BAD: pass by value -- expensive!
bool validateStudent(Student s);

Student plato;
bool platoIsOK = validateStudent(plato);
```

What happens when `validateStudent` is called? The parameter `s` is initialized by calling
the `Student` copy constructor with `plato` as the argument. Similarly, `s` is destroyed when
`validateStudent` returns. The cost of passing by value:

1. One call to the `Student` copy constructor
2. One call to the `Student` destructor
3. But `Student` contains two `std::string` objects, so that's two more copy constructions
   and two more destructions
4. `Student` derives from `Person`, which also has two `std::string` objects -- two more
   copy constructions, two more destructions
5. Plus the `Person` copy construction and destruction

**Total: 6 constructors and 6 destructors** just to pass a single parameter.

```cpp
// GOOD: pass by reference-to-const -- no copies at all
bool validateStudent(const Student& s);

// Same calling syntax, but no constructors or destructors are invoked.
// The const guarantees that validateStudent won't modify the caller's Student.
```

### The Slicing Problem

Pass-by-value doesn't just hurt performance -- it causes a subtle and dangerous bug called
the **slicing problem**. When a derived class object is passed by value to a function
expecting a base class object, the derived class's data members and virtual function
implementations are "sliced off."

```cpp
class Window {
public:
    std::string name() const;
    virtual void display() const;  // Base class version
};

class WindowWithScrollBars : public Window {
public:
    virtual void display() const;  // Overridden version -- draws scroll bars
};
```

Now consider a function that prints window information:

```cpp
// BAD: pass by value -- causes slicing!
void printNameAndDisplay(Window w) {
    std::cout << w.name();
    w.display();  // ALWAYS calls Window::display, never WindowWithScrollBars::display!
}

WindowWithScrollBars wwsb;
printNameAndDisplay(wwsb);
// wwsb is SLICED: it becomes a plain Window inside the function.
// The WindowWithScrollBars-specific data is chopped off.
// Virtual dispatch is broken -- display() calls the base class version.
```

The parameter `w` is constructed as a `Window` object (it's passed by value, and the
parameter type is `Window`). All the specialization that makes `wwsb` a `WindowWithScrollBars`
is sliced off. Inside `printNameAndDisplay`, `w` always behaves like a `Window`, regardless
of the type of the object actually passed. In particular, `w.display()` calls `Window::display`,
not `WindowWithScrollBars::display`.

```cpp
// GOOD: pass by reference-to-const -- preserves polymorphic behavior
void printNameAndDisplay(const Window& w) {
    std::cout << w.name();
    w.display();  // Calls the correct version via virtual dispatch!
}

WindowWithScrollBars wwsb;
printNameAndDisplay(wwsb);
// No slicing. w refers to the original wwsb object.
// w.display() correctly calls WindowWithScrollBars::display.
```

### A More Dramatic Slicing Example

```cpp
class Shape {
public:
    virtual ~Shape() {}
    virtual double area() const = 0;
    virtual std::string description() const { return "Shape"; }
};

class Circle : public Shape {
    double radius_;
public:
    explicit Circle(double r) : radius_(r) {}
    double area() const override { return 3.14159 * radius_ * radius_; }
    std::string description() const override {
        return "Circle(r=" + std::to_string(radius_) + ")";
    }
};

class Rectangle : public Shape {
    double width_, height_;
public:
    Rectangle(double w, double h) : width_(w), height_(h) {}
    double area() const override { return width_ * height_; }
    std::string description() const override {
        return "Rectangle(" + std::to_string(width_) + "x" + std::to_string(height_) + ")";
    }
};

// BAD: Taking a vector of Shapes by value is impossible (Shape is abstract),
// but even if it weren't, it would slice all derived objects.

// BAD: Taking Shape by value in a utility function
// void logShape(Shape s);  // Won't even compile -- Shape is abstract!

// GOOD: Take by reference-to-const
void logShape(const Shape& s) {
    std::cout << s.description() << " has area " << s.area() << "\n";
}

Circle c(5.0);
Rectangle r(3.0, 4.0);
logShape(c);  // "Circle(r=5.000000) has area 78.539750"
logShape(r);  // "Rectangle(3.000000x4.000000) has area 12.000000"
```

### When Pass-by-Value Is Acceptable

References are typically implemented as pointers under the hood. For **small, built-in types**
and **STL iterators and function objects**, pass-by-value is often more efficient:

```cpp
// These are fine to pass by value:
void f(int x);              // Built-in type -- cheaper to copy than to indirect
void f(double x);           // Built-in type
void f(char c);             // Built-in type

// STL iterators are designed to be passed by value:
void processRange(std::vector<int>::iterator begin,
                  std::vector<int>::iterator end);

// STL function objects are designed to be passed by value:
void sortWithComparator(std::vector<int>& v, std::less<int> comp);
```

**But be careful.** Just because a type is small does not mean pass-by-value is cheap.
A class with a single `std::string*` is only the size of a pointer, but copying it might
trigger a deep copy if the class's copy constructor does so. Furthermore, just because a
class is small today does not mean it will be small tomorrow -- the implementation may grow.

```cpp
// DANGEROUS ASSUMPTION: "It's small, so pass by value is fine"
class SmallButExpensive {
    std::shared_ptr<HugeDataStructure> data_;
    // Only 8 bytes (one pointer)!
    // But copying increments a reference count (atomic operation)
    // and may involve other bookkeeping.
public:
    SmallButExpensive(const SmallButExpensive&);  // Might be more expensive than you think
};

// Safe default: pass by reference-to-const
void process(const SmallButExpensive& obj);  // No copies, no surprises
```

### The General Rule

```cpp
// For user-defined types, the safe default is always reference-to-const:
void doWork(const MyClass& obj);

// Only pass by value when ALL of these are true:
// 1. The type is a built-in type (int, double, char, pointers), OR
// 2. The type is an STL iterator or function object, OR
// 3. The type is specifically designed to be passed by value and you've measured
//    that pass-by-value is actually more efficient.
```

### Things to Remember

- Prefer pass-by-reference-to-const over pass-by-value. It's typically more efficient
  and it avoids the slicing problem.
- The rule doesn't apply to built-in types and STL iterator and function object types.
  For them, pass-by-value is usually appropriate.

---
