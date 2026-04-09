# Chapter 6: Inheritance and Object-Oriented Design

Inheritance and object-oriented design in C++ is deceptively rich. The language offers public, protected, and private inheritance; single and multiple inheritance; virtual and non-virtual functions; pure virtual, simple virtual, and non-virtual member functions; and interactions between inheritance and other language features such as default parameter values and names in enclosing scopes. This chapter explains what these features really mean -- not what they look like, but what they actually *express* in a well-designed C++ program.

---

## Item 32: Make sure public inheritance models "is-a"

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

## Item 33: Avoid hiding inherited names

### How Name Hiding Works in C++

C++ name hiding in inheritance follows the same principle as name hiding in nested scopes: names in an inner scope hide names in an outer scope. The types and parameter lists are irrelevant -- it is purely about the *name*.

```cpp
// Demonstration of scope-based name hiding
int x = 5;             // global x

void someFunc() {
    double x = 3.14;   // local x HIDES global x
    std::cout << x;    // uses the local double x, not global int x
}
```

The same thing happens with inheritance:

```cpp
// BAD -- derived class hides base class overloads
class Base {
public:
    virtual void mf1() { std::cout << "Base::mf1()\n"; }
    virtual void mf1(int x) { std::cout << "Base::mf1(int)\n"; }

    virtual void mf2() { std::cout << "Base::mf2()\n"; }

    void mf3() { std::cout << "Base::mf3()\n"; }
    void mf3(double d) { std::cout << "Base::mf3(double)\n"; }
};

class Derived : public Base {
public:
    void mf1() override {   // hides ALL Base::mf1 overloads!
        std::cout << "Derived::mf1()\n";
    }

    void mf3() {             // hides ALL Base::mf3 overloads!
        std::cout << "Derived::mf3()\n";
    }
};

Derived d;
d.mf1();       // OK: calls Derived::mf1()
d.mf1(42);     // ERROR! Base::mf1(int) is hidden!
d.mf2();       // OK: calls Base::mf2()
d.mf3();       // OK: calls Derived::mf3()
d.mf3(3.14);   // ERROR! Base::mf3(double) is hidden!
```

### The Fix: Using Declarations

The `using` declaration brings the hidden base class names into the derived class scope:

```cpp
// GOOD -- using declarations unhide base class names
class Derived : public Base {
public:
    using Base::mf1;    // make all Base::mf1 overloads visible
    using Base::mf3;    // make all Base::mf3 overloads visible

    void mf1() override {
        std::cout << "Derived::mf1()\n";
    }

    void mf3() {
        std::cout << "Derived::mf3()\n";
    }
};

Derived d;
d.mf1();       // OK: calls Derived::mf1()
d.mf1(42);     // OK: calls Base::mf1(int) -- no longer hidden!
d.mf2();       // OK: calls Base::mf2()
d.mf3();       // OK: calls Derived::mf3()
d.mf3(3.14);   // OK: calls Base::mf3(double) -- no longer hidden!
```

### Private Inheritance and Forwarding Functions

Under private inheritance, you might not want all inherited overloads to be visible. In that case, use a forwarding function instead of a `using` declaration:

```cpp
// GOOD -- forwarding function selectively exposes base functionality
class Base {
public:
    virtual void mf1() { std::cout << "Base::mf1()\n"; }
    virtual void mf1(int x) { std::cout << "Base::mf1(" << x << ")\n"; }
    virtual void mf1(double d, int x) { std::cout << "Base::mf1(double,int)\n"; }
};

class Derived : private Base {
public:
    // Only expose the no-arg version
    virtual void mf1() {
        Base::mf1();    // forwarding function
    }
    // Base::mf1(int) and Base::mf1(double, int) remain inaccessible
};

Derived d;
d.mf1();         // OK: calls Derived::mf1() which forwards to Base::mf1()
d.mf1(42);       // ERROR: hidden, as intended
```

### A More Realistic Example: Widget Hierarchy

```cpp
// BAD -- name hiding breaks the interface
class Widget {
public:
    virtual ~Widget() = default;

    virtual void draw() {
        std::cout << "Widget::draw() -- default rendering\n";
    }
    virtual void draw(const Rect& clipRect) {
        std::cout << "Widget::draw(Rect) -- clipped rendering\n";
    }
    virtual void draw(const Rect& clipRect, int opacity) {
        std::cout << "Widget::draw(Rect, int) -- clipped + opacity\n";
    }

    void resize(int w, int h) { width_ = w; height_ = h; }
    void resize(const Size& s) { width_ = s.w; height_ = s.h; }

protected:
    int width_ = 100, height_ = 100;
};

class Button : public Widget {
public:
    // Override only the no-arg version, but ACCIDENTALLY hides the others!
    void draw() override {
        std::cout << "Button::draw() -- button-specific rendering\n";
    }
};

Button b;
b.draw();                        // OK
b.draw(Rect{0, 0, 50, 50});     // ERROR! Hidden!
b.draw(Rect{0, 0, 50, 50}, 128);// ERROR! Hidden!
```

```cpp
// GOOD -- using declaration preserves the full interface
class Button : public Widget {
public:
    using Widget::draw;   // unhide all draw overloads

    void draw() override {
        std::cout << "Button::draw() -- button-specific rendering\n";
    }
};

Button b;
b.draw();                         // OK: Button::draw()
b.draw(Rect{0, 0, 50, 50});      // OK: Widget::draw(Rect)
b.draw(Rect{0, 0, 50, 50}, 128); // OK: Widget::draw(Rect, int)
```

### Template Base Classes and Name Hiding

Name hiding also interacts with template base classes. The compiler does not look into dependent base classes:

```cpp
// BAD -- name not found in dependent base class
template <typename T>
class LoggingBase {
public:
    void log(const std::string& msg) {
        std::cout << "[LOG] " << msg << "\n";
    }
};

template <typename T>
class Processor : public LoggingBase<T> {
public:
    void process() {
        log("Processing...");  // ERROR! Compiler doesn't look in LoggingBase<T>
    }
};
```

```cpp
// GOOD -- three ways to fix it
template <typename T>
class Processor : public LoggingBase<T> {
public:
    using LoggingBase<T>::log;  // Approach 1: using declaration

    void process() {
        log("Processing...");          // works with Approach 1
        this->log("Processing...");    // Approach 2: qualify with this->
        LoggingBase<T>::log("Proc.."); // Approach 3: fully qualified (suppresses virtual)
    }
};
```

### Things to Remember

- Names in derived classes hide names in base classes. Under public inheritance, this is never desirable because it violates the "is-a" relationship.
- To make hidden names visible again, employ `using` declarations or forwarding functions.
- A `using` declaration brings *all* overloads of a given name into the derived class scope. Use forwarding functions when you want to expose only specific overloads.

---

## Item 34: Differentiate between inheritance of interface and inheritance of implementation

### The Three Kinds of Member Functions

When you design a base class with member functions, you must decide among three choices for each function:

1. **Pure virtual functions**: derived classes inherit the *interface only*. Each derived class *must* provide its own implementation.
2. **Simple (impure) virtual functions**: derived classes inherit *both interface and a default implementation*. They may override but are not required to.
3. **Non-virtual functions**: derived classes inherit *both interface and a mandatory implementation*. They should not override it (see Item 36).

```cpp
class Shape {
public:
    virtual ~Shape() = default;

    // Pure virtual: interface only
    virtual void draw() const = 0;

    // Simple virtual: interface + default implementation
    virtual void resize(double factor) {
        // Default: scale uniformly
        scale_ *= factor;
    }

    // Non-virtual: interface + mandatory implementation
    int objectID() const {
        return id_;
    }

private:
    double scale_ = 1.0;
    int id_ = nextID();
    static int nextID() { static int n = 0; return n++; }
};
```

### Pure Virtual Functions: Interface Inheritance

A pure virtual function tells derived classes: "You *must* provide this function, but I have no opinion about how you implement it."

```cpp
class Shape {
public:
    virtual ~Shape() = default;
    virtual double area() const = 0;
    virtual void draw() const = 0;
    virtual std::string name() const = 0;
};

class Circle : public Shape {
public:
    explicit Circle(double r) : radius_(r) {}

    double area() const override {
        return 3.14159265 * radius_ * radius_;
    }
    void draw() const override {
        std::cout << "Drawing circle with radius " << radius_ << "\n";
    }
    std::string name() const override { return "Circle"; }

private:
    double radius_;
};

class Triangle : public Shape {
public:
    Triangle(double b, double h) : base_(b), height_(h) {}

    double area() const override {
        return 0.5 * base_ * height_;
    }
    void draw() const override {
        std::cout << "Drawing triangle " << base_ << "x" << height_ << "\n";
    }
    std::string name() const override { return "Triangle"; }

private:
    double base_, height_;
};
```

Pure virtual functions *can* have implementations -- they just can't be called through the normal virtual dispatch mechanism. They must be called with full qualification:

```cpp
class Shape {
public:
    virtual ~Shape() = default;
    virtual void draw() const = 0;
};

// Definition of a pure virtual function
void Shape::draw() const {
    std::cout << "Shape::draw() -- default wireframe drawing\n";
}

class Circle : public Shape {
public:
    void draw() const override {
        // Can explicitly call the pure virtual's implementation
        Shape::draw();  // use the default wireframe
        std::cout << "  ...now filling in the circle\n";
    }
};
```

### The Danger of Simple Virtual Functions

Simple virtual functions provide both an interface and a default implementation, but this creates a risk: a derived class may accidentally inherit a default that is inappropriate, simply by failing to override.

```cpp
// BAD -- dangerous default that a new derived class might accidentally inherit
class Airport { /* ... */ };

class Airplane {
public:
    virtual ~Airplane() = default;

    virtual void fly(const Airport& from, const Airport& to) {
        // default flight plan: fly in a straight line at 30,000 ft
        std::cout << "Flying default route at 30,000 ft\n";
    }
};

class ModelA : public Airplane {
    // inherits default fly() -- works fine for Model A
};

class ModelB : public Airplane {
    // inherits default fly() -- works fine for Model B too
};

// Later, a new model is added...
class ModelC : public Airplane {
    // Forgot to override fly()!
    // ModelC needs a different flight plan, but silently gets the default.
    // This could be a disaster.
};
```

**Solution 1: Pure virtual + protected default (Meyers' preferred approach)**

```cpp
// GOOD -- separate interface from default implementation
class Airplane {
public:
    virtual ~Airplane() = default;
    virtual void fly(const Airport& from, const Airport& to) = 0;

protected:
    void defaultFly(const Airport& from, const Airport& to) {
        std::cout << "Flying default route at 30,000 ft\n";
    }
};

class ModelA : public Airplane {
public:
    void fly(const Airport& from, const Airport& to) override {
        defaultFly(from, to);  // explicitly opt in to default
    }
};

class ModelC : public Airplane {
public:
    void fly(const Airport& from, const Airport& to) override {
        // ModelC MUST provide its own implementation -- compiler enforces it
        std::cout << "Flying ModelC-specific route at 25,000 ft\n";
    }
};
```

**Solution 2: Pure virtual with a definition**

```cpp
// GOOD -- use the pure virtual function's own body as the default
class Airplane {
public:
    virtual ~Airplane() = default;
    virtual void fly(const Airport& from, const Airport& to) = 0;
};

// Provide the default as the pure virtual's body
void Airplane::fly(const Airport& from, const Airport& to) {
    std::cout << "Flying default route at 30,000 ft\n";
}

class ModelA : public Airplane {
public:
    void fly(const Airport& from, const Airport& to) override {
        Airplane::fly(from, to);  // explicitly invoke default
    }
};

class ModelC : public Airplane {
public:
    void fly(const Airport& from, const Airport& to) override {
        std::cout << "ModelC-specific route\n";  // forced to provide own impl
    }
};
```

### Non-Virtual Functions: Invariant over Specialization

Non-virtual functions represent behavior that is *invariant* across the hierarchy -- behavior that should never change regardless of how specialized a derived class becomes.

```cpp
class Transaction {
public:
    virtual ~Transaction() = default;

    // Non-virtual: every transaction has a unique ID, period.
    std::string transactionID() const { return id_; }

    // Non-virtual: the audit trail format is standardized.
    std::string auditRecord() const {
        return "[" + id_ + "] " + description();
    }

    // Pure virtual: each transaction type describes itself differently.
    virtual std::string description() const = 0;

private:
    std::string id_ = generateUUID();
};

class Purchase : public Transaction {
public:
    std::string description() const override {
        return "Purchase of " + item_ + " for $" + std::to_string(amount_);
    }
private:
    std::string item_ = "Widget";
    double amount_ = 9.99;
};

class Refund : public Transaction {
public:
    std::string description() const override {
        return "Refund of $" + std::to_string(amount_);
    }
private:
    double amount_ = 4.50;
};
```

### Summary Table

| Declaration | What is inherited | Derived class must override? |
|---|---|---|
| Pure virtual | Interface only | Yes |
| Simple virtual | Interface + default impl | No (may override) |
| Non-virtual | Interface + mandatory impl | No (should not override) |

### Things to Remember

- Pure virtual functions specify *interface inheritance only*. Derived classes must provide their own implementation.
- Simple (impure) virtual functions specify *interface inheritance plus default implementation inheritance*. Derived classes may override or accept the default.
- Non-virtual functions specify *interface inheritance plus mandatory implementation inheritance*. Derived classes should not redefine them (see Item 36).
- The danger of simple virtual functions is that a derived class can accidentally inherit an inappropriate default. Consider using pure virtual + a separate protected default to avoid this.

---

## Item 35: Consider alternatives to virtual functions

### The Problem with a Straightforward Virtual Function Design

Consider a simple health computation for game characters:

```cpp
// Straightforward but rigid approach
class GameCharacter {
public:
    virtual ~GameCharacter() = default;
    virtual int healthValue() const {
        // default algorithm for computing health
        return baseHealth_ - damage_;
    }
private:
    int baseHealth_ = 100;
    int damage_ = 0;
};
```

This works, but there are several alternatives that offer greater flexibility. Meyers presents four alternatives, each with different tradeoffs.

### Alternative 1: The Template Method Pattern via the Non-Virtual Interface (NVI) Idiom

The NVI idiom wraps virtual functions with non-virtual public functions. The non-virtual wrapper does "before" and "after" work, while the virtual function is private or protected.

```cpp
// GOOD -- NVI idiom (Template Method Pattern)
class GameCharacter {
public:
    virtual ~GameCharacter() = default;

    // Non-virtual interface: the public entry point
    int healthValue() const {
        // "before" work: lock mutex, log, validate invariants, etc.
        logHealthQuery();

        int result = doHealthValue();  // delegate to virtual

        // "after" work: unlock mutex, verify postconditions, etc.
        assert(result >= 0 && result <= maxHealth_);
        return result;
    }

private:
    virtual int doHealthValue() const {
        // default health calculation
        return baseHealth_ - damage_;
    }

    void logHealthQuery() const {
        std::cout << "[LOG] Health queried for character\n";
    }

    int baseHealth_ = 100;
    int damage_ = 0;
    int maxHealth_ = 100;
};

class Warrior : public GameCharacter {
private:
    int doHealthValue() const override {
        // Warriors get bonus health from armor
        return GameCharacter::doHealthValue() + armorBonus_;
    }
    int armorBonus_ = 20;
};

class Mage : public GameCharacter {
private:
    int doHealthValue() const override {
        // Mages have lower base health but get mana shield
        return GameCharacter::doHealthValue() + manaShield_;
    }
    int manaShield_ = 15;
};
```

Key advantages of NVI:
- Pre-conditions and post-conditions are always enforced.
- Logging, locking, and instrumentation happen in one place.
- Derived classes customize *what* is done, while the base class controls *when* and *how* it's done.

### Alternative 2: The Strategy Pattern via Function Pointers

Decouple the health calculation entirely from the class hierarchy by using a function pointer:

```cpp
// GOOD -- Strategy Pattern via function pointers
class GameCharacter;  // forward declaration

// Health calculation is a free function (a "strategy")
int defaultHealthCalc(const GameCharacter& gc);
int conservativeHealthCalc(const GameCharacter& gc);
int aggressiveHealthCalc(const GameCharacter& gc);

class GameCharacter {
public:
    using HealthCalcFunc = int (*)(const GameCharacter&);

    explicit GameCharacter(HealthCalcFunc hcf = defaultHealthCalc)
        : healthFunc_(hcf) {}

    int healthValue() const {
        return healthFunc_(*this);
    }

    // Can change strategy at runtime!
    void setHealthCalculator(HealthCalcFunc hcf) {
        healthFunc_ = hcf;
    }

    int getBaseHealth() const { return baseHealth_; }
    int getDamage() const { return damage_; }

private:
    HealthCalcFunc healthFunc_;
    int baseHealth_ = 100;
    int damage_ = 0;
};

int defaultHealthCalc(const GameCharacter& gc) {
    return gc.getBaseHealth() - gc.getDamage();
}

int conservativeHealthCalc(const GameCharacter& gc) {
    return static_cast<int>((gc.getBaseHealth() - gc.getDamage()) * 0.8);
}

int aggressiveHealthCalc(const GameCharacter& gc) {
    return static_cast<int>((gc.getBaseHealth() - gc.getDamage()) * 1.2);
}

// Usage
GameCharacter warrior(aggressiveHealthCalc);
GameCharacter healer(conservativeHealthCalc);

// Switch strategies at runtime
warrior.setHealthCalculator(conservativeHealthCalc);
```

Key advantages:
- Different instances of the *same* class can have different health strategies.
- Strategies can be swapped at runtime.
- Health calculation is fully decoupled from the class hierarchy.

Key disadvantage:
- The function pointer has no access to private/protected members. You may need to weaken encapsulation (provide public accessors or declare friends).

### Alternative 3: The Strategy Pattern via `std::function`

`std::function` generalizes function pointers to accept any callable: regular functions, lambdas, functors, bound member functions, etc.

```cpp
// GOOD -- Strategy Pattern via std::function (most flexible)
#include <functional>

class GameCharacter {
public:
    using HealthCalcFunc = std::function<int(const GameCharacter&)>;

    explicit GameCharacter(HealthCalcFunc hcf = defaultHealthCalc)
        : healthFunc_(std::move(hcf)) {}

    int healthValue() const {
        return healthFunc_(*this);
    }

    void setHealthCalculator(HealthCalcFunc hcf) {
        healthFunc_ = std::move(hcf);
    }

    int getBaseHealth() const { return baseHealth_; }
    int getDamage() const { return damage_; }

private:
    HealthCalcFunc healthFunc_;
    int baseHealth_ = 100;
    int damage_ = 0;

    static int defaultHealthCalc(const GameCharacter& gc) {
        return gc.baseHealth_ - gc.damage_;
    }
};

// Now we can use ANYTHING callable:

// 1. Regular function
int heroCalc(const GameCharacter& gc) {
    return gc.getBaseHealth() * 2 - gc.getDamage();
}

// 2. Lambda
auto timidCalc = [](const GameCharacter& gc) -> int {
    return std::max(0, gc.getBaseHealth() / 2 - gc.getDamage());
};

// 3. Functor
struct LevelAdjustedCalc {
    int level;
    int operator()(const GameCharacter& gc) const {
        return gc.getBaseHealth() + level * 10 - gc.getDamage();
    }
};

// 4. Bound member function of another class
class GameLevel {
public:
    int environmentalHealthAdjust(const GameCharacter& gc) const {
        // Poison swamp reduces health
        return gc.getBaseHealth() - gc.getDamage() - poisonDamage_;
    }
private:
    int poisonDamage_ = 15;
};

// Usage:
GameCharacter c1(heroCalc);                          // function pointer
GameCharacter c2(timidCalc);                         // lambda
GameCharacter c3(LevelAdjustedCalc{5});              // functor

GameLevel swamp;
GameCharacter c4(std::bind(&GameLevel::environmentalHealthAdjust,
                           &swamp, std::placeholders::_1));  // bound member
// Or with a lambda (preferred over std::bind in modern C++):
GameCharacter c5([&swamp](const GameCharacter& gc) {
    return swamp.environmentalHealthAdjust(gc);
});
```

### Alternative 4: The Classic Strategy Pattern

Extract the strategy into its own class hierarchy:

```cpp
// GOOD -- Classic Strategy Pattern with its own hierarchy
class GameCharacter;  // forward declaration

class HealthCalcStrategy {
public:
    virtual ~HealthCalcStrategy() = default;
    virtual int calc(const GameCharacter& gc) const = 0;
};

class DefaultHealthCalc : public HealthCalcStrategy {
public:
    int calc(const GameCharacter& gc) const override;
};

class SlowRegenHealthCalc : public HealthCalcStrategy {
public:
    int calc(const GameCharacter& gc) const override {
        // Regenerates slowly over time
        return gc.getBaseHealth() - gc.getDamage() + regenRate_ * turnCount_;
    }
private:
    int regenRate_ = 2;
    int turnCount_ = 0;
};

class PoisonedHealthCalc : public HealthCalcStrategy {
public:
    int calc(const GameCharacter& gc) const override {
        return gc.getBaseHealth() - gc.getDamage() - poisonPerTurn_ * turns_;
    }
private:
    int poisonPerTurn_ = 5;
    int turns_ = 3;
};

class GameCharacter {
public:
    explicit GameCharacter(std::shared_ptr<HealthCalcStrategy> strategy
                           = std::make_shared<DefaultHealthCalc>())
        : strategy_(std::move(strategy)) {}

    int healthValue() const {
        return strategy_->calc(*this);
    }

    void setStrategy(std::shared_ptr<HealthCalcStrategy> s) {
        strategy_ = std::move(s);
    }

    int getBaseHealth() const { return baseHealth_; }
    int getDamage() const { return damage_; }

private:
    std::shared_ptr<HealthCalcStrategy> strategy_;
    int baseHealth_ = 100;
    int damage_ = 0;
};

int DefaultHealthCalc::calc(const GameCharacter& gc) const {
    return gc.getBaseHealth() - gc.getDamage();
}
```

This is the most elaborate approach but offers the greatest extensibility: new strategies can be added as new classes without modifying existing code. Strategies can carry their own state, be configured independently, and be shared among multiple characters.

### Comparison of Approaches

| Approach | Flexibility | Complexity | Encapsulation Impact |
|---|---|---|---|
| Virtual functions | Low | Low | None |
| NVI (Template Method) | Low-Medium | Low | None |
| Function pointers | Medium | Low | May need public accessors |
| `std::function` | High | Medium | May need public accessors |
| Classic Strategy | High | High | May need public accessors |

### Things to Remember

- Alternatives to virtual functions include the NVI idiom and various forms of the Strategy design pattern. The NVI idiom is the Template Method design pattern; it wraps public non-virtual member functions around less accessible virtual functions.
- Moving functionality from a member function to a function outside the class means the non-member function has no special access to non-public members.
- `std::function` objects act like generalized function pointers. They accept any callable entity compatible with the target signature.
- The classic Strategy pattern replaces virtual functions in the primary hierarchy with a separate hierarchy of strategy objects.

---

## Item 36: Never redefine an inherited non-virtual function

### The Problem

Non-virtual functions are statically bound. The function called depends on the *declared type* of the pointer or reference, not the *actual type* of the object.

```cpp
// BAD -- redefining a non-virtual function
class Base {
public:
    void doWork() {
        std::cout << "Base::doWork()\n";
    }
};

class Derived : public Base {
public:
    void doWork() {      // hides Base::doWork -- NOT an override!
        std::cout << "Derived::doWork()\n";
    }
};

Derived d;
Base* bp = &d;
Derived* dp = &d;

bp->doWork();    // calls Base::doWork()     -- static binding!
dp->doWork();    // calls Derived::doWork()  -- static binding!
```

Both `bp` and `dp` point to the **same object** `d`, yet they call **different functions**. This is deeply confusing and almost always a bug.

### Why This is Always Wrong

The argument is both theoretical and practical:

**Theoretical argument (from Item 32 and Item 34):**

1. Public inheritance means "is-a" (Item 32).
2. Non-virtual functions establish an invariant over specialization (Item 34).
3. If `Derived` redefines a non-virtual function, either:
   - `Derived` is not really "is-a" `Base` (contradicts point 1), or
   - The function is not really invariant over specialization and should have been virtual (contradicts point 2).

Either way, the design is flawed.

**Practical argument:**

```cpp
// BAD -- causes bizarre behavior in real code
class Document {
public:
    std::string fileExtension() { return ".doc"; }
};

class SpreadSheet : public Document {
public:
    std::string fileExtension() { return ".xls"; }  // redefines non-virtual!
};

void saveToFile(Document& doc) {
    std::string name = "report" + doc.fileExtension();
    // ALWAYS saves as "report.doc" even for SpreadSheets!
    std::cout << "Saving as: " << name << "\n";
}

SpreadSheet ss;
saveToFile(ss);  // Saves as "report.doc" -- WRONG!
```

### The Fix

If the function should differ by type, make it virtual. If it should not differ, do not redefine it.

```cpp
// GOOD -- make it virtual if behavior should vary
class Document {
public:
    virtual ~Document() = default;
    virtual std::string fileExtension() const { return ".doc"; }
};

class SpreadSheet : public Document {
public:
    std::string fileExtension() const override { return ".xls"; }
};

class Presentation : public Document {
public:
    std::string fileExtension() const override { return ".ppt"; }
};

void saveToFile(Document& doc) {
    std::string name = "report" + doc.fileExtension();
    std::cout << "Saving as: " << name << "\n";  // Now correct for all types
}
```

### Another Example: Logger Hierarchy

```cpp
// BAD -- non-virtual function redefined
class Logger {
public:
    void log(const std::string& msg) {
        std::cout << "[INFO] " << msg << "\n";
    }
};

class ErrorLogger : public Logger {
public:
    void log(const std::string& msg) {  // hides Logger::log!
        std::cerr << "[ERROR] " << msg << "\n";
    }
};

void processAndLog(Logger& logger, const std::string& action) {
    // Always calls Logger::log, even if passed an ErrorLogger!
    logger.log("Processing: " + action);
}
```

```cpp
// GOOD -- use virtual functions
class Logger {
public:
    virtual ~Logger() = default;
    virtual void log(const std::string& msg) {
        std::cout << "[INFO] " << msg << "\n";
    }
};

class ErrorLogger : public Logger {
public:
    void log(const std::string& msg) override {
        std::cerr << "[ERROR] " << msg << "\n";
    }
};

class FileLogger : public Logger {
public:
    explicit FileLogger(const std::string& filename)
        : file_(filename) {}

    void log(const std::string& msg) override {
        file_ << msg << "\n";
    }
private:
    std::ofstream file_;
};
```

### Things to Remember

- Never redefine an inherited non-virtual function. Non-virtual functions are statically bound; virtual functions are dynamically bound. Redefining a non-virtual function causes the called function to depend on the declared type of the pointer/reference, not the actual object type.
- If you need different behavior in a derived class, the function should be virtual. If the behavior truly must be invariant, do not redefine it in derived classes.

---

## Item 37: Never redefine a function's inherited default parameter value

### The Core Issue

Virtual functions are dynamically bound, but **default parameter values are statically bound**. This mismatch leads to bizarre behavior:

```cpp
// BAD -- redefining inherited default parameter value
class Shape {
public:
    virtual ~Shape() = default;

    enum class Color { Red, Green, Blue };

    virtual void draw(Color color = Color::Red) const = 0;
};

class Circle : public Shape {
public:
    // Redefines the default parameter! BAD!
    void draw(Color color = Color::Green) const override {
        std::cout << "Circle::draw with color "
                  << static_cast<int>(color) << "\n";
    }
};

class Rectangle : public Shape {
public:
    // Also redefines the default! BAD!
    void draw(Color color = Color::Blue) const override {
        std::cout << "Rectangle::draw with color "
                  << static_cast<int>(color) << "\n";
    }
};

// The horror:
Shape* pc = new Circle;
Shape* pr = new Rectangle;

pc->draw();  // Calls Circle::draw(Color::Red)!
             // Virtual dispatch picks Circle::draw (dynamic binding)
             // BUT default parameter comes from Shape (static binding)
             // User sees Red, not Green!

pr->draw();  // Calls Rectangle::draw(Color::Red)!
             // Same issue: dynamic body, static default

Circle c;
c.draw();    // Calls Circle::draw(Color::Green)
             // When called via Circle*, uses Circle's default!
```

The same object, the same function call, but different results depending on the *declared type* of the pointer. This is exactly the kind of insanity you want to avoid.

### Why C++ Works This Way

Default parameters are statically bound for runtime efficiency. If default parameter values were dynamically bound, the runtime would need a mechanism to determine the appropriate default at each call site, which would be slower and more complex than the current approach.

### The Fix: NVI Idiom

The NVI idiom elegantly sidesteps this problem. Make the public function non-virtual (with the default parameter), and delegate to a private virtual function (without a default parameter).

```cpp
// GOOD -- NVI idiom avoids the default parameter problem entirely
class Shape {
public:
    virtual ~Shape() = default;

    enum class Color { Red, Green, Blue };

    // Non-virtual: owns the default parameter
    void draw(Color color = Color::Red) const {
        doDraw(color);  // pass explicit argument to virtual
    }

private:
    // Virtual: no default parameter to worry about
    virtual void doDraw(Color color) const = 0;
};

class Circle : public Shape {
private:
    void doDraw(Color color) const override {
        std::cout << "Circle::draw with color "
                  << static_cast<int>(color) << "\n";
    }
};

class Rectangle : public Shape {
private:
    void doDraw(Color color) const override {
        std::cout << "Rectangle::draw with color "
                  << static_cast<int>(color) << "\n";
    }
};

// Now it works correctly:
Shape* pc = new Circle;
Shape* pr = new Rectangle;

pc->draw();              // Circle::draw(Color::Red) -- always consistent!
pr->draw();              // Rectangle::draw(Color::Red) -- always consistent!
pc->draw(Shape::Color::Blue);  // Circle::draw(Color::Blue)
```

### A More Elaborate Example

```cpp
// BAD -- complex hierarchy with inconsistent defaults
class Widget {
public:
    virtual ~Widget() = default;
    virtual void render(int opacity = 255, bool shadow = true) const {
        std::cout << "Widget::render opacity=" << opacity
                  << " shadow=" << shadow << "\n";
    }
};

class Button : public Widget {
public:
    // Changes opacity default -- BAD!
    void render(int opacity = 200, bool shadow = true) const override {
        std::cout << "Button::render opacity=" << opacity
                  << " shadow=" << shadow << "\n";
    }
};

class FlatButton : public Button {
public:
    // Changes shadow default -- BAD!
    void render(int opacity = 200, bool shadow = false) const override {
        std::cout << "FlatButton::render opacity=" << opacity
                  << " shadow=" << shadow << "\n";
    }
};

Widget* w = new FlatButton;
w->render();   // FlatButton::render(255, true) -- Widget's defaults!
               // User expected opacity=200, shadow=false
```

```cpp
// GOOD -- NVI with clean defaults
class Widget {
public:
    virtual ~Widget() = default;

    void render(int opacity = 255, bool shadow = true) const {
        doRender(opacity, shadow);
    }

private:
    virtual void doRender(int opacity, bool shadow) const {
        std::cout << "Widget::render opacity=" << opacity
                  << " shadow=" << shadow << "\n";
    }
};

class Button : public Widget {
private:
    void doRender(int opacity, bool shadow) const override {
        std::cout << "Button::render opacity=" << opacity
                  << " shadow=" << shadow << "\n";
    }
};

class FlatButton : public Button {
private:
    void doRender(int opacity, bool shadow) const override {
        std::cout << "FlatButton::render opacity=" << opacity
                  << " shadow=" << shadow << "\n";
    }
};

Widget* w = new FlatButton;
w->render();   // FlatButton::doRender(255, true) -- consistent!
```

### What if the Derived Class Genuinely Needs a Different Default?

If you truly need different defaults when calling through different types, you probably have a design problem. But if you must, overload instead of changing the default:

```cpp
// ACCEPTABLE -- overloads instead of changing defaults
class Shape {
public:
    virtual ~Shape() = default;

    enum class Color { Red, Green, Blue };

    void draw() const { doDraw(defaultColor()); }
    void draw(Color c) const { doDraw(c); }

protected:
    virtual Color defaultColor() const { return Color::Red; }

private:
    virtual void doDraw(Color color) const = 0;
};

class OceanShape : public Shape {
protected:
    Color defaultColor() const override { return Color::Blue; }
private:
    void doDraw(Color color) const override {
        std::cout << "OceanShape with color " << static_cast<int>(color) << "\n";
    }
};
```

### Things to Remember

- Never redefine an inherited default parameter value, because default parameter values are statically bound, while virtual functions -- the only functions you should be overriding -- are dynamically bound.
- Use the NVI idiom (Item 35) to have the non-virtual public function specify the default, delegating to a private virtual with no default parameter.

---

## Item 38: Model "has-a" or "is-implemented-in-terms-of" through composition

### Composition vs. Inheritance

Composition (also called layering, containment, aggregation, or embedding) is the relationship where one class *contains* an object of another class as a data member. It models two different relationships depending on the domain:

1. **"Has-a"**: in the application domain (objects modeling real-world things).
2. **"Is-implemented-in-terms-of"**: in the implementation domain (objects that are implementation artifacts).

### "Has-a" Relationship

```cpp
// GOOD -- Person "has-a" name, address, and phone numbers
class Address {
public:
    std::string street;
    std::string city;
    std::string state;
    std::string zip;
};

class PhoneNumber {
public:
    std::string areaCode;
    std::string number;
    std::string extension;
};

class Person {
public:
    const std::string& name() const { return name_; }
    const Address& address() const { return address_; }

private:
    std::string name_;             // Person has-a name
    Address address_;              // Person has-a address
    std::vector<PhoneNumber> phones_;  // Person has phone numbers
};
```

A `Person` is *not* a `string`, an `Address`, or a `PhoneNumber`. A person *has* those things. This is obvious, and nobody would use public inheritance here.

### "Is-Implemented-In-Terms-Of" Relationship

This is less obvious and is the more common source of confusion. Consider implementing a `Set` using a `std::list`:

```cpp
// BAD -- Set is NOT a list!
template <typename T>
class Set : public std::list<T> {
    // A list can contain duplicates; a set cannot.
    // A list has push_front, push_back, etc. -- inappropriate for a set.
    // This violates "is-a": a Set is NOT a list.
};
```

A set is not a list. A list allows duplicates and preserves insertion order; a set does not. Public inheritance is wrong here.

```cpp
// GOOD -- Set is-implemented-in-terms-of list
template <typename T>
class Set {
public:
    bool contains(const T& item) const {
        return std::find(rep_.begin(), rep_.end(), item) != rep_.end();
    }

    void insert(const T& item) {
        if (!contains(item)) {
            rep_.push_back(item);
        }
    }

    void remove(const T& item) {
        auto it = std::find(rep_.begin(), rep_.end(), item);
        if (it != rep_.end()) {
            rep_.erase(it);
        }
    }

    std::size_t size() const { return rep_.size(); }
    bool empty() const { return rep_.empty(); }

    // Iterators for range-based for
    auto begin() const { return rep_.begin(); }
    auto end() const { return rep_.end(); }

private:
    std::list<T> rep_;   // Set is-implemented-in-terms-of list
};
```

The `Set` *uses* a `list` for its implementation, but it is not *a kind of* list. Users of `Set` never see the `list`; it is a hidden implementation detail.

### Real-World Example: Connection Pool

```cpp
// GOOD -- ConnectionPool uses a queue internally
class Connection {
public:
    explicit Connection(const std::string& host) : host_(host) {
        std::cout << "Connected to " << host_ << "\n";
    }
    void execute(const std::string& query) {
        std::cout << "Executing on " << host_ << ": " << query << "\n";
    }
    void reset() {
        std::cout << "Resetting connection to " << host_ << "\n";
    }
private:
    std::string host_;
};

// BAD -- trying to inherit from deque
// class ConnectionPool : public std::deque<Connection> { ... };
// A pool is NOT a deque!

// GOOD -- composition (is-implemented-in-terms-of)
class ConnectionPool {
public:
    explicit ConnectionPool(const std::string& host, int poolSize)
        : host_(host)
    {
        for (int i = 0; i < poolSize; ++i) {
            pool_.push(std::make_unique<Connection>(host));
        }
    }

    std::unique_ptr<Connection> acquire() {
        if (pool_.empty()) {
            return std::make_unique<Connection>(host_);  // grow if needed
        }
        auto conn = std::move(pool_.front());
        pool_.pop();
        return conn;
    }

    void release(std::unique_ptr<Connection> conn) {
        conn->reset();
        pool_.push(std::move(conn));
    }

    std::size_t available() const { return pool_.size(); }

private:
    std::string host_;
    std::queue<std::unique_ptr<Connection>> pool_;  // implemented in terms of queue
};
```

### Real-World Example: A Timer-Based Notification System

```cpp
// BAD -- a NotificationScheduler is NOT a priority_queue
// class NotificationScheduler : public std::priority_queue<...> { };

// GOOD
struct Notification {
    std::chrono::system_clock::time_point when;
    std::string message;
    std::string recipient;

    bool operator<(const Notification& rhs) const {
        // Earlier notifications have higher priority (min-heap behavior)
        return when > rhs.when;
    }
};

class NotificationScheduler {
public:
    void schedule(Notification n) {
        queue_.push(std::move(n));
    }

    bool hasReady() const {
        if (queue_.empty()) return false;
        return queue_.top().when <= std::chrono::system_clock::now();
    }

    Notification getNext() {
        Notification n = queue_.top();
        queue_.pop();
        return n;
    }

    bool empty() const { return queue_.empty(); }

private:
    std::priority_queue<Notification> queue_;  // implemented in terms of pq
};
```

### Things to Remember

- Composition has meaning very different from that of public inheritance. It means either "has-a" (in the application domain) or "is-implemented-in-terms-of" (in the implementation domain).
- In the application domain, composition means "has-a." A `Person` has-a name, an address, phone numbers.
- In the implementation domain, composition means "is-implemented-in-terms-of." A `Set` can be implemented in terms of a `list`, but a `Set` is not a `list`.

---

## Item 39: Use private inheritance judiciously

### What Private Inheritance Means

Private inheritance means "is-implemented-in-terms-of." It has nothing to do with "is-a." If `Derived` privately inherits from `Base`:

- All public and protected members of `Base` become private in `Derived`.
- There is no implicit conversion from `Derived*` to `Base*`.
- Compilers will not convert a `Derived` object to a `Base` object.

```cpp
class Timer {
public:
    explicit Timer(int intervalMs) : interval_(intervalMs) {}
    virtual void onTick() {
        std::cout << "Timer tick\n";
    }
    void start() {
        // simulate periodic ticking
        for (int i = 0; i < 5; ++i) {
            onTick();
        }
    }
private:
    int interval_;
};

// Private inheritance: Widget is-implemented-in-terms-of Timer
class Widget : private Timer {
public:
    Widget() : Timer(500) {}

    void startMonitoring() {
        start();  // can call Timer::start() from within Widget
    }

private:
    void onTick() override {
        std::cout << "Widget: checking for updates...\n";
    }
};

Widget w;
w.startMonitoring();  // OK
// Timer* tp = &w;    // ERROR -- private inheritance prevents conversion
// w.start();         // ERROR -- start() is private in Widget
```

### Composition is Usually Preferable

Private inheritance achieves the same thing as composition, and composition is generally preferable because:
- Composition allows you to control what is exposed.
- Composition is easier to understand.
- Composition does not create implicit coupling.

```cpp
// GOOD -- prefer composition over private inheritance
class Widget {
public:
    void startMonitoring() {
        timer_.start();
    }

private:
    // Inner class that overrides onTick
    class WidgetTimer : public Timer {
    public:
        WidgetTimer() : Timer(500) {}
    private:
        void onTick() override {
            std::cout << "Widget: checking for updates...\n";
        }
    };

    WidgetTimer timer_;  // composition: Widget has-a WidgetTimer
};
```

This composition approach has two additional advantages over private inheritance:
1. **Prevents derived classes from overriding `onTick`**. If `Widget` privately inherits from `Timer`, classes derived from `Widget` can still override `onTick`. With composition, the `WidgetTimer` class is private, so derived classes cannot interfere.
2. **Minimizes compilation dependencies**. With composition, `Timer` can be forward-declared and the `WidgetTimer` can be defined in the `.cpp` file (using the Pimpl idiom), breaking the compile-time dependency.

### When Private Inheritance is the Right Choice

**Case 1: The Empty Base Optimization (EBO)**

When the base class has no data members (it is "empty"), private inheritance can save space:

```cpp
class Empty {
    // No data members, but may have typedefs, enums, static members,
    // or non-virtual functions
    using DataType = int;
    static int count();
    void doSomething() {}
};

// With composition:
class Widget1 {
    int data_;
    Empty e_;  // typically takes 1 byte + padding = 4 or 8 bytes wasted
};
// sizeof(Widget1) > sizeof(int)

// With private inheritance:
class Widget2 : private Empty {
    int data_;
};
// sizeof(Widget2) == sizeof(int) -- EBO kicks in!
```

The Empty Base Optimization (EBO) means that an empty base class need not occupy any space. This matters when you are dealing with policy classes, traits, or allocator classes that contain no data.

```cpp
// GOOD -- EBO with allocator (real-world usage)
template <typename T, typename Allocator = std::allocator<T>>
class SmallVector : private Allocator {
    // Allocator is typically empty. Private inheritance + EBO means
    // SmallVector is no bigger than it needs to be.
public:
    using Allocator::allocate;    // selectively expose if needed
    using Allocator::deallocate;

    // ... vector implementation
private:
    T* data_;
    std::size_t size_;
    std::size_t capacity_;
};
```

**Case 2: You need access to protected members**

```cpp
// Private inheritance is needed when you must access protected members
// or override virtual functions, AND you want to hide the base interface.

class DatabaseDriver {
protected:
    virtual void onConnect() {
        std::cout << "Default connection setup\n";
    }
    virtual void onDisconnect() {
        std::cout << "Default disconnection cleanup\n";
    }

    void rawQuery(const std::string& sql) {
        std::cout << "Executing raw SQL: " << sql << "\n";
    }
};

// Cannot use composition here because we need to override
// protected virtual functions and call protected members.
class DatabaseConnection : private DatabaseDriver {
public:
    void connect() {
        onConnect();  // access protected member
    }
    void disconnect() {
        onDisconnect();  // access protected member
    }
    void executeQuery(const std::string& sql) {
        rawQuery(sql);  // access protected member
    }

private:
    void onConnect() override {
        std::cout << "Custom connection: setting timeout, charset...\n";
    }
    void onDisconnect() override {
        std::cout << "Custom disconnect: flushing logs...\n";
    }
};
```

### A Practical Comparison

```cpp
// Scenario: Implement a widget that needs to react to timer events
// and also needs an allocator

// Approach 1: All composition (possibly wastes space)
class WidgetV1 {
    class TimerImpl : public Timer {
        void onTick() override { /* ... */ }
    };
    TimerImpl timer_;
    std::allocator<int> alloc_;  // wastes space -- allocator is empty
    int data_;
};

// Approach 2: Private inheritance for EBO, composition for timer
class WidgetV2 : private std::allocator<int> {
    class TimerImpl : public Timer {
        void onTick() override { /* ... */ }
    };
    TimerImpl timer_;
    int data_;
    // std::allocator<int> takes zero space via EBO
};
```

### Things to Remember

- Private inheritance means "is-implemented-in-terms-of." It is usually inferior to composition, but it makes sense when a derived class needs access to protected base class members or needs to redefine inherited virtual functions.
- Unlike composition, private inheritance enables the empty base optimization (EBO). This can be important for library developers who work hard to minimize object sizes.
- Use private inheritance judiciously. Use it only when composition truly cannot do the job.

---

## Item 40: Use multiple inheritance judiciously

### The Basics of Multiple Inheritance

Multiple inheritance (MI) means a class inherits from more than one base class. It introduces several complications that single inheritance does not have.

### Problem 1: Ambiguity from Multiple Bases

```cpp
// BAD -- ambiguity
class BorrowableItem {
public:
    void checkOut() {
        std::cout << "Checking out from library\n";
    }
};

class ElectronicGadget {
public:
    void checkOut() {
        std::cout << "Running diagnostic check\n";
    }
};

class MP3Player : public BorrowableItem, public ElectronicGadget {
    // Inherits TWO checkOut() functions
};

MP3Player mp;
// mp.checkOut();  // ERROR! Ambiguous: which checkOut()?
```

You must disambiguate explicitly:

```cpp
mp.BorrowableItem::checkOut();    // OK
mp.ElectronicGadget::checkOut();  // OK
```

Note that the ambiguity exists even if one of the functions would be inaccessible (e.g., private in one base). C++ resolves ambiguity *before* checking accessibility.

### Problem 2: The Diamond Inheritance Problem

The diamond problem occurs when a class inherits from two classes that share a common base:

```cpp
// The diamond problem
class File {
public:
    std::string filename;
    int size;
};

class InputFile : public File {
public:
    void read() { std::cout << "Reading " << filename << "\n"; }
};

class OutputFile : public File {
public:
    void write() { std::cout << "Writing " << filename << "\n"; }
};

class IOFile : public InputFile, public OutputFile {
    // IOFile has TWO copies of File!
    // IOFile::InputFile::filename and IOFile::OutputFile::filename
};

IOFile f;
// f.filename;    // ERROR! Ambiguous -- which filename?
f.InputFile::filename = "input.txt";   // one copy
f.OutputFile::filename = "output.txt"; // different copy!
```

### The Solution: Virtual Inheritance

Virtual inheritance ensures that only one copy of the common base class exists:

```cpp
// GOOD -- virtual inheritance solves the diamond
class File {
public:
    std::string filename;
    int size = 0;
};

class InputFile : virtual public File {
public:
    void read() { std::cout << "Reading " << filename << "\n"; }
};

class OutputFile : virtual public File {
public:
    void write() { std::cout << "Writing " << filename << "\n"; }
};

class IOFile : public InputFile, public OutputFile {
    // Only ONE copy of File thanks to virtual inheritance
};

IOFile f;
f.filename = "data.txt";   // unambiguous -- only one filename
f.read();                   // "Reading data.txt"
f.write();                  // "Writing data.txt"
```

### The Costs of Virtual Inheritance

Virtual inheritance is not free. It imposes costs in:

1. **Size**: Objects with virtual bases are larger (they contain vpointers or equivalent to navigate to the virtual base subobject).
2. **Speed**: Accessing members of virtual base classes is slower (indirection through vpointers).
3. **Initialization**: The most derived class must initialize the virtual base, even if it is several levels up the hierarchy.

```cpp
class Animal {
public:
    Animal(const std::string& name) : name_(name) {}
    std::string name_;
};

class Mammal : virtual public Animal {
public:
    // Must pass Animal's constructor arguments
    Mammal(const std::string& name) : Animal(name) {}
};

class WingedAnimal : virtual public Animal {
public:
    WingedAnimal(const std::string& name) : Animal(name) {}
};

class Bat : public Mammal, public WingedAnimal {
public:
    // Bat (the most derived class) MUST initialize Animal directly
    Bat(const std::string& name)
        : Animal(name)           // required! Virtual base init
        , Mammal(name)           // Mammal's Animal init is IGNORED
        , WingedAnimal(name)     // WingedAnimal's Animal init is IGNORED
    {}
};
```

### Advice on Virtual Inheritance

1. Do not use virtual inheritance unless you truly need it.
2. If you must use virtual inheritance, try to avoid putting data in virtual base classes. This sidesteps the initialization complexity. Virtual base classes with no data (like interfaces) have minimal overhead.

```cpp
// GOOD -- virtual base class with no data (like a Java/C# interface)
class IPrintable {
public:
    virtual ~IPrintable() = default;
    virtual void print() const = 0;
    // No data members!
};

class ISerializable {
public:
    virtual ~ISerializable() = default;
    virtual std::string serialize() const = 0;
    // No data members!
};
```

### The Legitimate Use Case: Interface + Implementation

The most defensible use of multiple inheritance combines a public interface (abstract base class) with a private implementation:

```cpp
// GOOD -- practical MI: public interface inheritance + private implementation

// Pure interface
class IDatabase {
public:
    virtual ~IDatabase() = default;
    virtual void connect(const std::string& connStr) = 0;
    virtual void disconnect() = 0;
    virtual void execute(const std::string& query) = 0;
    virtual bool isConnected() const = 0;
};

// Reusable implementation detail
class ConnectionManager {
public:
    void openConnection(const std::string& connStr) {
        connStr_ = connStr;
        connected_ = true;
        std::cout << "Connection opened to: " << connStr_ << "\n";
    }
    void closeConnection() {
        connected_ = false;
        std::cout << "Connection closed\n";
    }
    bool connected() const { return connected_; }
    const std::string& connectionString() const { return connStr_; }
private:
    std::string connStr_;
    bool connected_ = false;
};

// Concrete class: inherits interface publicly, implementation privately
class PostgresDB : public IDatabase, private ConnectionManager {
public:
    void connect(const std::string& connStr) override {
        openConnection(connStr);  // from ConnectionManager
    }
    void disconnect() override {
        closeConnection();         // from ConnectionManager
    }
    void execute(const std::string& query) override {
        if (!connected()) {
            throw std::runtime_error("Not connected");
        }
        std::cout << "Postgres executing: " << query << "\n";
    }
    bool isConnected() const override {
        return connected();        // from ConnectionManager
    }
};

// Client code uses only the interface
void runMigration(IDatabase& db) {
    db.connect("host=localhost dbname=mydb");
    db.execute("CREATE TABLE users (id SERIAL PRIMARY KEY, name TEXT)");
    db.execute("INSERT INTO users (name) VALUES ('Alice')");
    db.disconnect();
}
```

### Full Example: Observer Pattern with Multiple Interfaces

```cpp
// GOOD -- MI to implement multiple interfaces (common and legitimate pattern)

class IObserver {
public:
    virtual ~IObserver() = default;
    virtual void onEvent(const std::string& event) = 0;
};

class ILogger {
public:
    virtual ~ILogger() = default;
    virtual void log(const std::string& msg) = 0;
};

class IConfigurable {
public:
    virtual ~IConfigurable() = default;
    virtual void configure(const std::map<std::string, std::string>& opts) = 0;
};

// A monitoring agent implements all three interfaces
class MonitoringAgent : public IObserver,
                        public ILogger,
                        public IConfigurable {
public:
    void onEvent(const std::string& event) override {
        log("Event received: " + event);
        events_.push_back(event);
    }

    void log(const std::string& msg) override {
        std::cout << "[Monitor] " << msg << "\n";
    }

    void configure(const std::map<std::string, std::string>& opts) override {
        auto it = opts.find("verbose");
        if (it != opts.end()) {
            verbose_ = (it->second == "true");
        }
    }

private:
    std::vector<std::string> events_;
    bool verbose_ = false;
};

// Each subsystem works with only the interface it needs:
void attachObserver(IObserver& obs) {
    obs.onEvent("system_start");
}

void setupLogging(ILogger& logger) {
    logger.log("Logging initialized");
}

void loadConfig(IConfigurable& conf) {
    conf.configure({{"verbose", "true"}});
}

// One object, many roles:
MonitoringAgent agent;
attachObserver(agent);
setupLogging(agent);
loadConfig(agent);
```

### The Diamond Problem in Practice with Virtual Inheritance

A more complete real-world example showing the diamond pattern properly handled:

```cpp
// Virtual base: shared interface/state
class StreamBase {
public:
    virtual ~StreamBase() = default;

    void setBufferSize(std::size_t sz) { bufferSize_ = sz; }
    std::size_t bufferSize() const { return bufferSize_; }

    virtual void flush() = 0;

protected:
    std::size_t bufferSize_ = 4096;
    std::string name_ = "unnamed";
};

class InputStream : virtual public StreamBase {
public:
    virtual std::string read(std::size_t bytes) = 0;

    void flush() override {
        std::cout << "Flushing input buffer for " << name_ << "\n";
    }
};

class OutputStream : virtual public StreamBase {
public:
    virtual void write(const std::string& data) = 0;

    void flush() override {
        std::cout << "Flushing output buffer for " << name_ << "\n";
    }
};

class IOStream : public InputStream, public OutputStream {
public:
    IOStream(const std::string& name) {
        name_ = name;  // only one name_ thanks to virtual inheritance
    }

    std::string read(std::size_t bytes) override {
        std::cout << "Reading " << bytes << " bytes from " << name_ << "\n";
        return "data";
    }

    void write(const std::string& data) override {
        std::cout << "Writing " << data.size()
                  << " bytes to " << name_ << "\n";
    }

    // Must resolve the flush() ambiguity from InputStream and OutputStream
    void flush() override {
        InputStream::flush();
        OutputStream::flush();
    }
};

IOStream io("socket://localhost:8080");
io.setBufferSize(8192);  // unambiguous -- one StreamBase
io.write("Hello");
io.read(1024);
io.flush();
```

### Decision Framework for Multiple Inheritance

1. **Is it multiple *interface* inheritance?** (All or most bases are pure abstract classes with no data.) This is almost always fine and is the most common legitimate use of MI.

2. **Is it one interface + one implementation base?** This is the classic "public interface, private implementation" pattern and is usually fine.

3. **Is it a diamond pattern?** Use virtual inheritance, but be aware of the costs. Prefer keeping virtual bases data-free.

4. **Are you inheriting from multiple concrete classes with data?** Strongly reconsider your design. Composition is almost certainly the better approach.

### Things to Remember

- Multiple inheritance is more complex than single inheritance. It can lead to ambiguity issues and the diamond inheritance problem.
- Virtual inheritance imposes costs in size, speed, and complexity of initialization. It is most practical when virtual base classes have no data.
- Multiple inheritance does have legitimate uses. One scenario involves combining public inheritance from an interface class with private inheritance from a class that helps with implementation.
- When faced with MI complexity, prefer composition when possible. Use MI primarily for implementing multiple pure interfaces.

---

## Summary

The nine items in this chapter cover the fundamental principles of inheritance and OO design in C++:

| Item | Core Principle |
|---|---|
| 32 | Public inheritance = "is-a" (Liskov Substitution Principle) |
| 33 | Use `using` declarations to prevent name hiding |
| 34 | Pure virtual = interface; simple virtual = interface + default; non-virtual = invariant |
| 35 | NVI, function pointers, `std::function`, and Strategy pattern as alternatives to virtual |
| 36 | Non-virtual functions are statically bound -- never redefine them |
| 37 | Default parameters are statically bound -- never redefine them in overrides |
| 38 | Composition = "has-a" or "is-implemented-in-terms-of" |
| 39 | Private inheritance = "is-implemented-in-terms-of" (prefer composition, use for EBO) |
| 40 | MI is complex but legitimate for multiple interface inheritance |

The overarching theme: understand what each C++ construct *means* in terms of design, and use each construct to express exactly the design relationship you intend. Do not use a language feature simply because it is available; use it because it precisely communicates your architectural intent.
