# Item 32: Make sure public inheritance models "is-a"

## Visual Summary

```text
┌───────────────────────────────────────────────────────────────────────────┐
│            ITEM 32: MAKE SURE PUBLIC INHERITANCE MODELS "IS-A"            │
├───────────────────────────────────────────────────────────────────────────┤
│ 1. public Derived : Base -> every Derived must be usable as a Base.       │
│ 2. If base promises behavior -> derived must honor it for all callers.    │
│ 3. Square-rectangle style mismatch -> mathematical relation is not        │
│ enough.                                                                   │
│ 4. If not true is-a -> use composition or private inheritance.            │
│ 5. Meaning: public inheritance is a substitutability contract.            │
└───────────────────────────────────────────────────────────────────────────┘
```

## Visual Deep Dive

```text
┌───────────────────────────────────────────────────────────────────────────┐
│                        PUBLIC INHERITANCE CONTRACT                        │
├───────────────────────────────────────────────────────────────────────────┤
│ Derived publicly inherits Base                                            │
│                                     ▼                                     │
│ Every Base operation must make sense for Derived                          │
│                                     ▼                                     │
│ Any Base* or Base& may refer to Derived                                   │
│                                     ▼                                     │
│ Derived must preserve Base promises                                       │
└───────────────────────────────────────────────────────────────────────────┘
```

```text
┌───────────────────────────────────────────────────────────────────────────┐
│                            RELATIONSHIP CHOICE                            │
├───────────────────────────────────────────────────────────────────────────┤
│ Use public inheritance            | Use composition                       │
│ ----------------------------------+-------------------------------------  │
│ True substitutable is-a           | Has-a                                 │
│ Base interface applies fully      | Implemented using                     │
│                                   | Only partial behavior matches         │
└───────────────────────────────────────────────────────────────────────────┘
```

### The Fundamental Rule

Public inheritance means **"is-a."** Every object of the derived class *is* an object of the base class. The base class represents a more general concept; the derived class represents a more specialized concept. Anywhere the base class can appear, the derived class can appear in its place. This is a direct expression of the **Liskov Substitution Principle (LSP)**.

```cpp
class Person { ... };
class Student : public Person { ... };
```

Every student is a person, but not every person is a student. This is precisely what C++ expresses via public inheritance. Any function expecting a `Person` (or `Person&`, or `Person*`) will also accept a `Student` (or `Student&`, or `Student*`).

```cpp
void eat(const Person& p);        // anyone can eat
void study(const Student& s);     // only students study

Person p;
Student s;

eat(p);     // fine -- p is a Person
eat(s);     // fine -- s is a Person (Student is-a Person)
study(s);   // fine -- s is a Student
study(p);   // ERROR -- p is not a Student
```

### The Classic Pitfall: Penguins and Birds

Consider this seemingly reasonable hierarchy:

```cpp
// BAD -- violates Liskov Substitution Principle
class Bird {
public:
    virtual void fly() {
        std::cout << "Flying through the air!\n";
    }
};

class Penguin : public Bird {
    // Penguins can't fly, but Bird says they can!
};
```

A penguin is a bird, but penguins cannot fly. The hierarchy above says that all birds can fly, which is simply wrong. There are several ways to handle this.

**Approach 1: Refine the hierarchy**

```cpp
// GOOD -- more accurate hierarchy
class Bird {
public:
    virtual ~Bird() = default;
    // ... general bird things (lay eggs, have feathers, etc.)
};

class FlyingBird : public Bird {
public:
    virtual void fly() {
        std::cout << "Flying through the air!\n";
    }
};

class NonFlyingBird : public Bird {
    // no fly() member at all
};

class Penguin : public NonFlyingBird {
    // penguins are non-flying birds
};

class Eagle : public FlyingBird {
    // eagles can fly
};
```

**Approach 2: Runtime error (less desirable but sometimes pragmatic)**

```cpp
// ACCEPTABLE but not ideal -- runtime enforcement
class Bird {
public:
    virtual ~Bird() = default;
    virtual void fly() {
        std::cout << "Flying through the air!\n";
    }
};

class Penguin : public Bird {
public:
    void fly() override {
        throw std::runtime_error("Penguins can't fly!");
    }
};
```

This says: "Penguins can try to fly, but it's an error for them to actually do it." The problem is moved from compile time to runtime, which is inferior but sometimes necessary when the hierarchy cannot be restructured.

### The Rectangle/Square Problem

This is another classic violation:

```cpp
// BAD -- Square is NOT a behavioral substitute for Rectangle
class Rectangle {
public:
    virtual void setHeight(int h) { height_ = h; }
    virtual void setWidth(int w)  { width_ = w; }
    int getHeight() const { return height_; }
    int getWidth() const  { return width_; }
    int area() const { return height_ * width_; }

private:
    int height_;
    int width_;
};

class Square : public Rectangle {
public:
    // Must maintain the invariant: height == width
    void setHeight(int h) override {
        Rectangle::setHeight(h);
        Rectangle::setWidth(h);    // force width = height
    }
    void setWidth(int w) override {
        Rectangle::setHeight(w);   // force height = width
        Rectangle::setWidth(w);
    }
};
```

Now consider any code that uses a `Rectangle&`:

```cpp
void makeBigger(Rectangle& r) {
    int oldHeight = r.getHeight();
    r.setWidth(r.getWidth() + 10);
    assert(r.getHeight() == oldHeight);  // FAILS for Square!
}
```

The postcondition that `setWidth` does not change the height is violated by `Square`. Mathematically a square is a rectangle, but *behaviorally* a `Square` object cannot be substituted for a `Rectangle` object. This is a Liskov Substitution Principle violation.

```cpp
// GOOD -- separate types, or use a single Shape with appropriate constraints
class Shape {
public:
    virtual ~Shape() = default;
    virtual int area() const = 0;
};

class Rectangle : public Shape {
public:
    Rectangle(int w, int h) : width_(w), height_(h) {}
    void setHeight(int h) { height_ = h; }
    void setWidth(int w) { width_ = w; }
    int area() const override { return width_ * height_; }
private:
    int width_, height_;
};

class Square : public Shape {
public:
    explicit Square(int side) : side_(side) {}
    void setSide(int s) { side_ = s; }
    int area() const override { return side_ * side_; }
private:
    int side_;
};
```

### Real-World Example: Vehicle Hierarchy

```cpp
// GOOD -- well-modeled public inheritance hierarchy
class Vehicle {
public:
    virtual ~Vehicle() = default;
    virtual void start() = 0;
    virtual void stop() = 0;
    virtual double fuelRemaining() const = 0;
    virtual std::string description() const = 0;
};

class Car : public Vehicle {
public:
    void start() override {
        ignition_ = true;
        std::cout << "Car engine started\n";
    }
    void stop() override {
        ignition_ = false;
        std::cout << "Car engine stopped\n";
    }
    double fuelRemaining() const override { return fuelGallons_; }
    std::string description() const override { return "Sedan"; }

    // Car-specific
    void openTrunk() { /* ... */ }

private:
    bool ignition_ = false;
    double fuelGallons_ = 15.0;
};

class Truck : public Vehicle {
public:
    void start() override {
        dieselPreheat();
        ignition_ = true;
        std::cout << "Truck diesel engine started\n";
    }
    void stop() override {
        ignition_ = false;
        std::cout << "Truck engine stopped\n";
    }
    double fuelRemaining() const override { return dieselGallons_; }
    std::string description() const override { return "18-Wheeler"; }

    // Truck-specific
    void attachTrailer() { /* ... */ }

private:
    void dieselPreheat() { /* ... */ }
    bool ignition_ = false;
    double dieselGallons_ = 150.0;
};

// Any function dealing with Vehicle works seamlessly with both
void refuelIfNeeded(Vehicle& v) {
    if (v.fuelRemaining() < 5.0) {
        std::cout << v.description() << " needs refueling!\n";
    }
}
```

### Things to Remember

- Public inheritance means "is-a." Everything that applies to base class objects must also apply to derived class objects, because every derived class object *is* a base class object.
- The Liskov Substitution Principle states: if `D` is publicly derived from `B`, then any property provable about objects of type `B` should also be provable about objects of type `D`.
- Intuitions from the real world (penguins are birds, squares are rectangles) do not always translate correctly into class hierarchies. What matters is *behavioral* substitutability, not taxonomic relationships.

---
