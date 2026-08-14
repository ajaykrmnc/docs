# Item 7: Declare Destructors Virtual in Polymorphic Base Classes

## Visual Summary

```text
┌───────────────────────────────────────────────────────────────────────────┐
│      ITEM 7: DECLARE DESTRUCTORS VIRTUAL IN POLYMORPHIC BASE CLASSES      │
├───────────────────────────────────────────────────────────────────────────┤
│ 1. Base pointer points to derived object -> delete through base pointer.  │
│ 2. Base destructor non-virtual -> only base part is destroyed: undefined  │
│ behavior risk.                                                            │
│ 3. Base destructor virtual -> derived destructor runs, then base          │
│ destructor.                                                               │
│ 4. No polymorphic deletion needed -> non-virtual destructor is fine and   │
│ smaller.                                                                  │
│ 5. Meaning: virtual functions in a base usually imply a virtual           │
│ destructor.                                                               │
└───────────────────────────────────────────────────────────────────────────┘
```

## Visual Deep Dive

```text
┌───────────────────────────────────────────────────────────────────────────┐
│                        DELETE THROUGH BASE POINTER                        │
├───────────────────────────────────────────────────────────────────────────┤
│ Base* p = new Derived                                                     │
│                                     ▼                                     │
│ delete p                                                                  │
│                                     ▼                                     │
│ Non-virtual destructor -> base cleanup only / undefined behavior          │
│                                     ▼                                     │
│ Virtual destructor -> Derived cleanup, then Base cleanup                  │
└───────────────────────────────────────────────────────────────────────────┘
```

```text
┌───────────────────────────────────────────────────────────────────────────┐
│                     WHEN VIRTUAL DESTRUCTOR IS NEEDED                     │
├───────────────────────────────────────────────────────────────────────────┤
│ Needed                            | Not needed                            │
│ ----------------------------------+-------------------------------------  │
│ Base has virtual functions        | No polymorphic deletion               │
│ Delete via base pointer           | Value-like tiny class                 │
│ Polymorphic ownership             | No virtual interface                  │
└───────────────────────────────────────────────────────────────────────────┘
```

### Core Concept

When a derived class object is deleted through a base class pointer, and the base class has a **non-virtual 
destructor**, the behavior is **undefined**. In practice, the derived class's destructor typically never runs, 
leading to resource leaks and corruption. Any class designed to be used polymorphically must have a virtual 
destructor.

### The Problem: Non-Virtual Destructor with Polymorphic Deletion

```cpp
// BAD: Non-virtual destructor in a polymorphic base class
class TimeKeeper {
public:
  TimeKeeper() {}
  ~TimeKeeper() {}  // NON-VIRTUAL destructor!

  virtual int getCurrentTime() const = 0;  // virtual function => polymorphic use
};

class AtomicClock : public TimeKeeper {
public:
  AtomicClock() : calibrationData_(new double[1000]) {
    // Expensive calibration data
  }
  ~AtomicClock() {
    delete[] calibrationData_;  // Free calibration data
    std::cout << "AtomicClock resources freed\n";
  }
  int getCurrentTime() const override { return /* atomic time */0; }

private:
  double* calibrationData_;
};

class WaterClock : public TimeKeeper {
public:
  WaterClock() : waterLevel_(new float[500]) {}
  ~WaterClock() {
    delete[] waterLevel_;
    std::cout << "WaterClock resources freed\n";
  }
  int getCurrentTime() const override { return /* water time */0; }

private:
  float* waterLevel_;
};

// Factory function returns base class pointer
TimeKeeper* getTimeKeeper(const std::string& type) {
  if (type == "atomic") return new AtomicClock();
  if (type == "water")  return new WaterClock();
  return nullptr;
}

void disaster() {
  TimeKeeper* tk = getTimeKeeper("atomic");
  // ... use tk ...
  delete tk;  // UNDEFINED BEHAVIOR!
  // TimeKeeper::~TimeKeeper() is non-virtual
  // Only the TimeKeeper part is destroyed
  // AtomicClock::~AtomicClock() is NOT called
  // calibrationData_ is LEAKED
  // The "AtomicClock resources freed" message never prints
}
```

### The Fix: Virtual Destructor

```cpp
// GOOD: Virtual destructor in polymorphic base class
class TimeKeeper {
public:
  TimeKeeper() {}
  virtual ~TimeKeeper() {}  // VIRTUAL destructor

  virtual int getCurrentTime() const = 0;
};

class AtomicClock : public TimeKeeper {
public:
  AtomicClock() : calibrationData_(new double[1000]) {}
  ~AtomicClock() override {  // 'override' for safety (C++11)
    delete[] calibrationData_;
    std::cout << "AtomicClock resources freed\n";
  }
  int getCurrentTime() const override { return 0; }

private:
  double* calibrationData_;
};

void correct() {
  TimeKeeper* tk = getTimeKeeper("atomic");
  delete tk;  // CORRECT: virtual dispatch calls AtomicClock::~AtomicClock()
  // then TimeKeeper::~TimeKeeper()
  // "AtomicClock resources freed" prints
  // No leak
}
```

### The Rule: Virtual Destructor IFF Polymorphic

The rule is not "always make destructors virtual." It is: **if the class has any virtual functions, the 
destructor should be virtual.**

**Why not make ALL destructors virtual?**

```cpp
// BAD: Gratuitous virtual destructor on a non-polymorphic class
class Point {
public:
  Point(int x, int y) : x_(x), y_(y) {}
  virtual ~Point() {}  // Unnecessary virtual — this class is not polymorphic

private:
  int x_, y_;
};
// sizeof(Point) without virtual: typically 8 bytes (two ints)
// sizeof(Point) with virtual: typically 16 bytes (two ints + vptr)
// That's a 100% overhead! And it breaks C-compatibility for layout.

// GOOD: No virtual destructor — this class is not meant for polymorphism
class Point {
public:
  Point(int x, int y) : x_(x), y_(y) {}
  // No virtual destructor — and no virtual functions at all
  // sizeof(Point) == 8 bytes, C-compatible layout

private:
  int x_, y_;
};
```

A virtual function adds a **vptr** (virtual table pointer) to each object instance, typically 8 bytes on a 
64-bit system. For small value-type objects, this overhead is unacceptable.

### The Dangers of Inheriting from Non-Virtual-Destructor Classes

Standard library classes like `std::string`, `std::vector`, and `std::unordered_map` do **not** have virtual 
destructors. Inheriting from them is dangerous:

```cpp
// BAD: Inheriting from std::string (which has a non-virtual destructor)
class SpecialString : public std::string {
public:
  SpecialString(const char* s) : std::string(s), metadata_(new int(42)) {}
  ~SpecialString() { delete metadata_; }  // cleanup

private:
  int* metadata_;
};

void danger() {
  std::string* sp = new SpecialString("hello");
  delete sp;  // UNDEFINED BEHAVIOR!
  // std::string::~string() is non-virtual
  // SpecialString::~SpecialString() never runs
  // metadata_ is leaked
}

// BAD: Inheriting from std::vector
class AuditedVector : public std::vector<int> {
public:
  ~AuditedVector() {
    logToAuditTrail("Vector destroyed with " + std::to_string(size()) + " elements");
  }
};
// Same problem: deleting through a std::vector<int>* skips the audit log
```

**The safe alternative — composition over inheritance:**

```cpp
// GOOD: Use composition instead of inheriting from standard containers
class AuditedVector {
public:
  void push_back(int val) {
    data_.push_back(val);
    logToAuditTrail("Element added: " + std::to_string(val));
  }

  size_t size() const { return data_.size(); }

  ~AuditedVector() {
    logToAuditTrail("Vector destroyed with " + std::to_string(data_.size()) + " elements");
  }

private:
  std::vector<int> data_;  // composition, not inheritance
};
```

### Pure Virtual Destructor for Abstract Base Classes

Sometimes you want an abstract class but have no natural pure virtual function. You can make the destructor 
pure virtual — but you **must still provide a definition**.

```cpp
class AbstractAnimal {
public:
  virtual ~AbstractAnimal() = 0;  // pure virtual destructor
  // Makes the class abstract — cannot be instantiated directly
};

// You MUST provide a definition! Derived class destructors call the base destructor.
AbstractAnimal::~AbstractAnimal() {
  // Base cleanup (if any)
  // This body can be empty, but the definition must exist
}

class Dog : public AbstractAnimal {
public:
  Dog(const std::string& name) : name_(name) {}
  ~Dog() override {
    std::cout << name_ << " destroyed\n";
    // After this, AbstractAnimal::~AbstractAnimal() is called automatically
  }
private:
  std::string name_;
};

void test() {
  // AbstractAnimal a;              // ERROR: cannot instantiate abstract class
  AbstractAnimal* pet = new Dog("Rex");
  delete pet;  // Correctly calls Dog::~Dog() then AbstractAnimal::~AbstractAnimal()
}
```

### Real-World Example: Plugin System

```cpp
// A plugin system where plugins are loaded dynamically and destroyed
// through base class pointers — virtual destructor is ESSENTIAL

class Plugin {
public:
  virtual ~Plugin() = default;  // MUST be virtual

  virtual std::string name() const = 0;
  virtual void initialize() = 0;
  virtual void execute() = 0;
  virtual void shutdown() = 0;
};

class ImageProcessorPlugin : public Plugin {
public:
  ImageProcessorPlugin() : buffer_(nullptr), bufferSize_(0) {}

  ~ImageProcessorPlugin() override {
    delete[] buffer_;  // Must run! Only runs if base dtor is virtual.
    std::cout << "ImageProcessor plugin destroyed, buffer freed\n";
  }

  std::string name() const override { return "ImageProcessor"; }

  void initialize() override {
    bufferSize_ = 1024 * 1024;  // 1MB
    buffer_ = new unsigned char[bufferSize_];
  }

  void execute() override {
    // Process image data in buffer_
  }

  void shutdown() override {
    // Graceful shutdown
  }

private:
  unsigned char* buffer_;
  size_t bufferSize_;
};

class PluginManager {
public:
  void loadPlugin(std::unique_ptr<Plugin> plugin) {
    plugin->initialize();
    plugins_.push_back(std::move(plugin));
  }

  ~PluginManager() {
    for (auto& p : plugins_) {
      p->shutdown();
    }
    // unique_ptr calls delete on Plugin* pointers
    // Virtual destructor ensures derived destructors run correctly
    plugins_.clear();
  }

private:
  std::vector<std::unique_ptr<Plugin>> plugins_;
};
```

### Real-World Example: Shape Hierarchy

```cpp
class Shape {
public:
  virtual ~Shape() = default;  // Virtual destructor — this is a polymorphic base

  virtual double area() const = 0;
  virtual double perimeter() const = 0;
  virtual void draw() const = 0;

  // Non-virtual interface pattern (NVI) — see Item 35
  std::string describe() const {
    return "Shape with area=" + std::to_string(area()) +
    " perimeter=" + std::to_string(perimeter());
  }
};

class Circle : public Shape {
public:
  explicit Circle(double radius) : radius_(radius) {}
  // No explicit destructor needed — default is fine
  // But it IS virtual because base class destructor is virtual

  double area() const override { return M_PI * radius_ * radius_; }
  double perimeter() const override { return 2 * M_PI * radius_; }
  void draw() const override { /* ... */ }

private:
  double radius_;
};

class Polygon : public Shape {
public:
  Polygon(std::vector<Point> vertices)
    : vertices_(std::move(vertices)),
    texture_(new Texture("default.png")) {}  // heap resource

  ~Polygon() override {
    delete texture_;  // Properly called through virtual dispatch
  }

  double area() const override { /* shoelace formula */ return 0; }
  double perimeter() const override { /* sum of edge lengths */ return 0; }
  void draw() const override { /* ... */ }

private:
  std::vector<Point> vertices_;
  Texture* texture_;
};

void render(const std::vector<std::unique_ptr<Shape>>& shapes) {
  for (const auto& shape : shapes) {
    std::cout << shape->describe() << "\n";
  }
}
// When shapes vector is destroyed, each unique_ptr calls delete on Shape*
// Virtual destructor ensures Polygon::~Polygon runs and texture_ is freed
```

### Things to Remember

- Polymorphic base classes should declare virtual destructors. If a class has any virtual functions, it should 
have a virtual destructor.
- Classes not designed to be base classes or not designed for polymorphic use should **not** declare virtual 
destructors.
- Never inherit from standard library container classes (`std::string`, `std::vector`, etc.) — they have 
non-virtual destructors.
- A pure virtual destructor makes a class abstract but must still have a definition (the body can be empty).

---
