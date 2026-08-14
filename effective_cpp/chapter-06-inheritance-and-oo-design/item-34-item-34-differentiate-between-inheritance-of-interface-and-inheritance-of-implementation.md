# Item 34: Differentiate between inheritance of interface and inheritance of implementation

## Visual Summary

```text
┌───────────────────────────────────────────────────────────────────────────┐
│ITEM 34: DIFFERENTIATE BETWEEN INHERITANCE OF INTERFACE AND INHERITANCE OF │
├───────────────────────────────────────────────────────────────────────────┤
│ 1. Pure virtual -> inherit interface only; derived must implement.        │
│ 2. Impure virtual -> inherit interface plus overridable default           │
│ implementation.                                                           │
│ 3. Non-virtual -> inherit interface plus mandatory                        │
│ implementation/invariant.                                                 │
│ 4. Choose deliberately based on what derived classes may change.          │
│ 5. Meaning: each function form communicates a different inheritance       │
│ contract.                                                                 │
└───────────────────────────────────────────────────────────────────────────┘
```

## Visual Deep Dive

```text
┌───────────────────────────────────────────────────────────────────────────┐
│                        VIRTUAL FUNCTION CONTRACTS                         │
├───────────────────────────────────────────────────────────────────────────┤
│ Function form                     | Inheritance meaning                   │
│ ----------------------------------+-------------------------------------  │
│ pure virtual                      | interface only                        │
│ impure virtual                    | interface + default impl              │
│ non-virtual                       | interface + mandatory impl            │
└───────────────────────────────────────────────────────────────────────────┘
```

```text
┌───────────────────────────────────────────────────────────────────────────┐
│                          CHOOSING FUNCTION FORM                           │
├───────────────────────────────────────────────────────────────────────────┤
│ Must derived provide behavior? -> pure virtual                            │
│                                     ▼                                     │
│ Can base offer overridable default? -> virtual with body                  │
│                                     ▼                                     │
│ Must behavior never vary? -> non-virtual                                  │
└───────────────────────────────────────────────────────────────────────────┘
```

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
