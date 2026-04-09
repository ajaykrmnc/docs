# Item 12: Copy All Parts of an Object

### Core Concept

When you write your own copy constructor or copy assignment operator, you are taking full responsibility for 
copying. The compiler will not warn you if you forget to copy a member. Two common bugs arise: **(1)** 
forgetting to copy a newly added data member, and **(2)** forgetting to copy the base class part of a derived 
class. Both lead to **partial copies** — objects that look fully constructed but have uninitialized or 
default-initialized members.

### Bug 1: Forgetting to Copy New Members

```cpp
class Customer {
public:
  Customer(const std::string& name) : name_(name) {}

  Customer(const Customer& rhs) : name_(rhs.name_) {}

  Customer& operator=(const Customer& rhs) {
    name_ = rhs.name_;
    return *this;
  }

private:
  std::string name_;
};
// Everything is fine so far...

// Months later, a new member is added:
class Customer {
public:
  Customer(const std::string& name, int priority)
  : name_(name), priority_(priority) {}

  // OOPS: Copy constructor was NOT updated!
  Customer(const Customer& rhs) : name_(rhs.name_) {
    // priority_ is NOT copied — it's default-initialized (0 or garbage)
  }

  // OOPS: Copy assignment was NOT updated!
  Customer& operator=(const Customer& rhs) {
    name_ = rhs.name_;
    // priority_ is NOT assigned — the target keeps its old value
    return *this;
  }

private:
  std::string name_;
  int priority_;    // NEW MEMBER — but copy operations don't know about it!
};

void demonstrate() {
  Customer c1("Alice", 5);    // priority_ = 5
  Customer c2(c1);            // c2.priority_ = 0 or garbage — NOT 5!
  Customer c3("Bob", 1);
  c3 = c1;                    // c3.priority_ is still 1, NOT 5!
}
```

The compiler will **not** warn you about this. It generated the copy operations itself before, and it 
considers the fact that you've written them to mean you know what you're doing.

**The fix is obvious but easy to forget:**

```cpp
// GOOD: Copy ALL members
class Customer {
public:
  Customer(const std::string& name, int priority)
  : name_(name), priority_(priority) {}

  Customer(const Customer& rhs)
    : name_(rhs.name_),
    priority_(rhs.priority_) {}  // DON'T FORGET THIS!

  Customer& operator=(const Customer& rhs) {
    name_ = rhs.name_;
    priority_ = rhs.priority_;     // DON'T FORGET THIS!
    return *this;
  }

private:
  std::string name_;
  int priority_;
};
```

### Bug 2: Forgetting to Copy the Base Class Part

This is the more insidious bug. When writing copy operations for a derived class, you must explicitly copy the 
base class portion.

```cpp
class PriorityCustomer : public Customer {
public:
  PriorityCustomer(const std::string& name, int priority, int vipLevel)
  : Customer(name, priority), vipLevel_(vipLevel) {}

  // BAD: Copies derived part but FORGETS base part
  PriorityCustomer(const PriorityCustomer& rhs)
  : vipLevel_(rhs.vipLevel_) {
    // Customer base class is DEFAULT-CONSTRUCTED (if possible)
    // rhs.name_ and rhs.priority_ are NOT copied!
    // The base class portion of this object has empty name and 0 priority
  }

  // BAD: Assigns derived part but FORGETS base part
  PriorityCustomer& operator=(const PriorityCustomer& rhs) {
    vipLevel_ = rhs.vipLevel_;
    // Customer::operator= is NOT called!
    // name_ and priority_ are NOT assigned!
    return *this;
  }

private:
  int vipLevel_;
};

void bug() {
  PriorityCustomer pc1("VIP Alice", 10, 3);
  PriorityCustomer pc2(pc1);
  // pc2.vipLevel_ == 3 (copied)
  // pc2.name_ == "" (NOT copied — default constructed)
  // pc2.priority_ == 0 (NOT copied — default constructed)

  PriorityCustomer pc3("Regular", 1, 1);
  pc3 = pc1;
  // pc3.vipLevel_ == 3 (assigned)
  // pc3.name_ is still "Regular" (NOT assigned!)
  // pc3.priority_ is still 1 (NOT assigned!)
}
```

### The Fix: Explicitly Call Base Class Copy Operations

```cpp
// GOOD: Copy ALL parts — including the base class
class PriorityCustomer : public Customer {
public:
  PriorityCustomer(const std::string& name, int priority, int vipLevel)
  : Customer(name, priority), vipLevel_(vipLevel) {}

  // Copy constructor: invoke base class copy constructor
  PriorityCustomer(const PriorityCustomer& rhs)
    : Customer(rhs),              // IMPORTANT: copy the base class part!
    vipLevel_(rhs.vipLevel_) {   // copy the derived class part
    // Customer's copy ctor receives a PriorityCustomer& but takes
    // a const Customer& — slicing extracts the Customer part
  }

  // Copy assignment: invoke base class operator=
  PriorityCustomer& operator=(const PriorityCustomer& rhs) {
    Customer::operator=(rhs);      // IMPORTANT: assign the base class part!
    vipLevel_ = rhs.vipLevel_;     // assign the derived class part
    return *this;
  }

private:
  int vipLevel_;
};
```

### Don't Implement One in Terms of the Other

A common temptation is to avoid code duplication by having the copy constructor call `operator=` or vice 
versa. Both are wrong:

```cpp
// BAD: Copy constructor calling operator=
class Widget {
public:
  Widget(const Widget& rhs) {
    *this = rhs;  // Calls operator= on a not-yet-fully-constructed object!
    // operator= may delete resources that were never allocated
    // (because ctor hasn't finished initializing them)
  }

  Widget& operator=(const Widget& rhs) {
    if (this == &rhs) return *this;
    delete data_;                    // Deletes uninitialized pointer in copy ctor!
    data_ = new int(*rhs.data_);
    return *this;
  }

private:
  int* data_;
};

// BAD: operator= calling copy constructor (via placement new)
class Widget {
public:
  Widget& operator=(const Widget& rhs) {
    this->~Widget();                     // Destroy current object
    new (this) Widget(rhs);              // Construct a new one in the same memory
    // If the copy ctor throws, the object is in a destroyed state!
    // Any subsequent access (including the destructor) is undefined behavior
    return *this;
  }
};
```

**The correct approach: extract common code into a private helper:**

```cpp
// GOOD: Common code in a private init/copyFrom function
class Widget {
public:
  Widget(int value, const std::string& name)
  : data_(new int(value)), name_(name), cache_(nullptr) {
    rebuildCache();
  }

  Widget(const Widget& rhs)
    : data_(new int(*rhs.data_)),   // allocate and copy
    name_(rhs.name_),
    cache_(nullptr) {
    rebuildCache();                  // shared logic in private helper
  }

  Widget& operator=(const Widget& rhs) {
    if (this == &rhs) return *this;

    int* newData = new int(*rhs.data_);  // copy first (exception safety)
    delete data_;                         // then delete old
    data_ = newData;
    name_ = rhs.name_;
    rebuildCache();                       // shared logic in private helper
    return *this;
  }

  ~Widget() {
    delete data_;
    delete cache_;
  }

private:
  void rebuildCache() {
    delete cache_;
    cache_ = new CacheData(*data_, name_);
  }

  int* data_;
  std::string name_;
  CacheData* cache_;
};
```

### Real-World Example: Deep Hierarchy

```cpp
class Shape {
public:
  Shape(const Color& color, double opacity)
  : color_(color), opacity_(opacity) {}

  Shape(const Shape& rhs)
  : color_(rhs.color_), opacity_(rhs.opacity_) {}

  Shape& operator=(const Shape& rhs) {
    color_ = rhs.color_;
    opacity_ = rhs.opacity_;
    return *this;
  }

  virtual ~Shape() = default;

protected:
  Color color_;
  double opacity_;
};

class Polygon : public Shape {
public:
  Polygon(const Color& color, double opacity, std::vector<Point> vertices)
  : Shape(color, opacity), vertices_(std::move(vertices)) {}

  Polygon(const Polygon& rhs)
    : Shape(rhs),                           // copy Shape part
    vertices_(rhs.vertices_) {}            // copy Polygon part

  Polygon& operator=(const Polygon& rhs) {
    Shape::operator=(rhs);                   // assign Shape part
    vertices_ = rhs.vertices_;               // assign Polygon part
    return *this;
  }

protected:
  std::vector<Point> vertices_;
};

class TexturedPolygon : public Polygon {
public:
  TexturedPolygon(const Color& color, double opacity,
                  std::vector<Point> vertices,
                  const std::string& texturePath)
    : Polygon(color, opacity, std::move(vertices)),
    texture_(new Texture(texturePath)),
    uvCoords_(vertices_.size()) {}

  // Copy constructor — must copy ALL THREE levels
  TexturedPolygon(const TexturedPolygon& rhs)
    : Polygon(rhs),                          // copies Shape AND Polygon parts
    texture_(new Texture(*rhs.texture_)),   // deep copy of texture
    uvCoords_(rhs.uvCoords_) {}             // copy UV coordinates

  // Copy assignment — must assign ALL THREE levels
  TexturedPolygon& operator=(const TexturedPolygon& rhs) {
    Polygon::operator=(rhs);                  // assigns Shape AND Polygon parts

    Texture* newTex = new Texture(*rhs.texture_);  // copy first (exception safe)
    delete texture_;
    texture_ = newTex;
    uvCoords_ = rhs.uvCoords_;

    return *this;
  }

  ~TexturedPolygon() override {
    delete texture_;
  }

private:
  Texture* texture_;
  std::vector<UV> uvCoords_;
};

void test() {
  TexturedPolygon tp1(Color::Red, 0.8,
                      {{0,0}, {1,0}, {1,1}},
                      "brick.png");

  TexturedPolygon tp2(tp1);  // Copies ALL parts:
  // Shape:           color_ = Red, opacity_ = 0.8
  // Polygon:         vertices_ = {{0,0},{1,0},{1,1}}
  // TexturedPolygon: texture_ = deep copy of brick texture,
  //                  uvCoords_ = copied

  TexturedPolygon tp3(Color::Blue, 0.5,
                      {{0,0}, {2,0}, {2,2}, {0,2}},
                      "stone.png");
  tp3 = tp1;  // Assigns ALL parts — nothing is left behind
}
```

### Real-World Example: Configuration Object with Many Members

```cpp
class ServerConfig {
public:
  ServerConfig()
    : host_("localhost"), port_(8080), maxConnections_(100),
    timeout_(30), useTLS_(false), logLevel_(LogLevel::INFO),
    threadPoolSize_(4), maxRequestSize_(1 << 20),
    keepAliveEnabled_(true), keepAliveTimeout_(60),
    compressionEnabled_(false),
    certPath_(""), keyPath_("") {}

  // When there are many members, it's easy to miss one.
  // A disciplined approach: list members in the SAME ORDER as declaration.

  ServerConfig(const ServerConfig& rhs)
    : host_(rhs.host_),
    port_(rhs.port_),
    maxConnections_(rhs.maxConnections_),
    timeout_(rhs.timeout_),
    useTLS_(rhs.useTLS_),
    logLevel_(rhs.logLevel_),
    threadPoolSize_(rhs.threadPoolSize_),
    maxRequestSize_(rhs.maxRequestSize_),
    keepAliveEnabled_(rhs.keepAliveEnabled_),
    keepAliveTimeout_(rhs.keepAliveTimeout_),
    compressionEnabled_(rhs.compressionEnabled_),
    certPath_(rhs.certPath_),
    keyPath_(rhs.keyPath_) {
    // Every. Single. Member. Copied.
    // If someone adds a new member and forgets to add it here,
    // the compiler won't warn — this is a maintenance burden.
  }

  ServerConfig& operator=(const ServerConfig& rhs) {
    host_ = rhs.host_;
    port_ = rhs.port_;
    maxConnections_ = rhs.maxConnections_;
    timeout_ = rhs.timeout_;
    useTLS_ = rhs.useTLS_;
    logLevel_ = rhs.logLevel_;
    threadPoolSize_ = rhs.threadPoolSize_;
    maxRequestSize_ = rhs.maxRequestSize_;
    keepAliveEnabled_ = rhs.keepAliveEnabled_;
    keepAliveTimeout_ = rhs.keepAliveTimeout_;
    compressionEnabled_ = rhs.compressionEnabled_;
    certPath_ = rhs.certPath_;
    keyPath_ = rhs.keyPath_;
    return *this;
  }

  // Modern alternative: if compiler-generated copy is correct
  // (no raw pointers, all members are copyable), just use = default:
  // ServerConfig(const ServerConfig&) = default;
  // ServerConfig& operator=(const ServerConfig&) = default;
  // The compiler copies ALL members — no risk of forgetting one!

private:
  std::string host_;
  int port_;
  int maxConnections_;
  int timeout_;
  bool useTLS_;
  LogLevel logLevel_;
  int threadPoolSize_;
  size_t maxRequestSize_;
  bool keepAliveEnabled_;
  int keepAliveTimeout_;
  bool compressionEnabled_;
  std::string certPath_;
  std::string keyPath_;
};
```

### Checklist: When Writing Copy Operations

Every time you write a copy constructor or copy assignment operator, go through this checklist:

1. **Copy every data member** declared in the class, in the same order they're declared.
2. **Invoke the base class copy operation** — `Base(rhs)` in the copy ctor's initializer list, 
`Base::operator=(rhs)` in `operator=`.
3. **If a new member is added later**, update both the copy constructor AND `operator=`.
4. **Don't implement one in terms of the other.** Extract shared code into a private helper function instead.
5. **Consider whether `= default` is sufficient.** If your class doesn't manage raw resources, 
compiler-generated copy operations may be correct and maintainable.

```cpp
// Modern approach: when possible, use = default and let the compiler do it
class ModernConfig {
public:
  ModernConfig() = default;
  ModernConfig(const ModernConfig&) = default;             // copies ALL members
  ModernConfig& operator=(const ModernConfig&) = default;  // assigns ALL members
  ~ModernConfig() = default;

  // If you add a new member, the compiler automatically includes it
  // in the generated copy operations. No maintenance burden!

private:
  std::string host_ = "localhost";
  int port_ = 8080;
  bool useTLS_ = false;
  // Add a new member here — copy operations automatically updated
};
```

### Things to Remember

- Copying functions should be sure to copy all of an object's data members and all of its base class parts.
- When adding a new data member to a class, update every copy constructor and every copy assignment operator. 
The compiler will not warn you if you forget.
- Don't try to implement one of the copying functions in terms of the other. Instead, put common functionality 
in a third function that both call.
- When your class doesn't manage raw resources, prefer `= default` to hand-written copy operations — the 
compiler will automatically include all members, including ones added later.
