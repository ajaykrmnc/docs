# Item 9: Never Call Virtual Functions During Construction or Destruction

## Visual Summary

```text
┌───────────────────────────────────────────────────────────────────────────┐
│  ITEM 9: NEVER CALL VIRTUAL FUNCTIONS DURING CONSTRUCTION OR DESTRUCTION  │
├───────────────────────────────────────────────────────────────────────────┤
│ 1. Base constructor runs -> derived part is not constructed yet.          │
│ 2. Virtual call here -> dispatches as base, not derived.                  │
│ 3. Base destructor runs -> derived part is already gone.                  │
│ 4. Need customization -> pass data to base constructor or use             │
│ non-virtual hooks after construction.                                     │
│ 5. Meaning: virtual dispatch is unsafe while object identity is           │
│ changing.                                                                 │
└───────────────────────────────────────────────────────────────────────────┘
```

## Visual Deep Dive

```text
┌───────────────────────────────────────────────────────────────────────────┐
│                      CONSTRUCTION DISPATCH TIMELINE                       │
├───────────────────────────────────────────────────────────────────────────┤
│ Base constructor starts                                                   │
│                                     ▼                                     │
│ Derived members are not initialized yet                                   │
│                                     ▼                                     │
│ Virtual call dispatches to Base version                                   │
│                                     ▼                                     │
│ Derived override cannot safely run                                        │
└───────────────────────────────────────────────────────────────────────────┘
```

```text
┌───────────────────────────────────────────────────────────────────────────┐
│                       DESTRUCTION DISPATCH TIMELINE                       │
├───────────────────────────────────────────────────────────────────────────┤
│ Derived destructor finishes first                                         │
│                                     ▼                                     │
│ Derived part is gone                                                      │
│                                     ▼                                     │
│ Base destructor runs                                                      │
│                                     ▼                                     │
│ Virtual call dispatches to Base version                                   │
└───────────────────────────────────────────────────────────────────────────┘
```

### Core Concept

During base class construction, virtual functions **do not** behave polymorphically. When a base class 
constructor is executing, the object's dynamic type is the **base class**, not the derived class. Virtual 
function calls resolve to the base class version. The same is true during base class destruction. This is not 
a bug — it is a deliberate design decision, because the derived class's members have not yet been initialized 
(during construction) or have already been destroyed (during destruction).

### The Problem: Virtual Calls in Constructors

```cpp
// BAD: Calling a virtual function in a constructor
class Transaction {
public:
  Transaction() {
    // ... setup code ...
    logTransaction();  // Virtual call — but which version runs?
  }

  virtual void logTransaction() const {
    std::cout << "Logging base Transaction\n";
  }

  virtual ~Transaction() {}
};

class BuyTransaction : public Transaction {
public:
  BuyTransaction(const std::string& stock, int shares)
  : stock_(stock), shares_(shares) {
    // Before this body runs, Transaction::Transaction() already ran
    // and called logTransaction() — but BuyTransaction's version? NO!
  }

  void logTransaction() const override {
    // This version is NEVER called from the base constructor
    std::cout << "BUY " << shares_ << " shares of " << stock_ << "\n";
  }

private:
  std::string stock_;
  int shares_;
};

void demonstrate() {
  BuyTransaction bt("AAPL", 100);
  // Output: "Logging base Transaction"
  // NOT: "BUY 100 shares of AAPL"
  //
  // During Transaction::Transaction(), the object's type IS Transaction,
  // not BuyTransaction. BuyTransaction's members (stock_, shares_) don't
  // even exist yet — they haven't been initialized!
}
```

### Why This Behavior Exists

The rationale is safety. During `Transaction::Transaction()`:

1. The `BuyTransaction` part of the object has not been constructed yet.
2. `BuyTransaction::stock_` and `BuyTransaction::shares_` are **uninitialized**.
3. If `BuyTransaction::logTransaction()` were called, it would access `stock_` and `shares_` — reading 
uninitialized memory.
4. C++ prevents this by treating the object as a `Transaction` during `Transaction`'s constructor.

```cpp
// What would happen if C++ DID allow derived virtual calls in base ctor:
class Derived : public Base {
public:
  Derived() : data_(new int[100]) {}  // data_ not yet allocated

  void doWork() override {
    // If called from Base::Base(), data_ is UNINITIALIZED
    data_[0] = 42;  // Writing to a random memory address — CRASH
  }

private:
  int* data_;
};
```

### The Problem Gets Worse: Indirect Virtual Calls

The danger is not always obvious. The constructor might call a non-virtual function that internally calls a 
virtual function:

```cpp
// BAD: Indirect virtual call — harder to spot
class Transaction {
public:
  Transaction() {
    init();  // Non-virtual — but calls a virtual function inside!
  }

  virtual ~Transaction() {}

private:
  void init() {
    // ... common setup ...
    logTransaction();  // VIRTUAL CALL during construction!
    // Still resolves to Transaction::logTransaction()
  }

  virtual void logTransaction() const = 0;  // pure virtual!
};

class SellTransaction : public Transaction {
public:
  SellTransaction() {}

  void logTransaction() const override {
    std::cout << "SELL transaction logged\n";
  }
};

void test() {
  // SellTransaction st;  // RUNTIME ERROR or UNDEFINED BEHAVIOR
  // Transaction::Transaction() calls init() which calls logTransaction()
  // logTransaction() is pure virtual in Transaction
  // Calling a pure virtual function => typically std::terminate() / crash
  // Some compilers: "pure virtual function called" error message
}
```

### The Same Problem in Destructors

Virtual functions during destruction have the same issue, in reverse order:

```cpp
class Transaction {
public:
  virtual ~Transaction() {
    logTransaction();  // Virtual call during destruction
    // By the time Transaction::~Transaction() runs,
    // the derived part (BuyTransaction) has ALREADY been destroyed
    // So this calls Transaction::logTransaction(), not the derived version
  }

  virtual void logTransaction() const {
    std::cout << "Base transaction cleanup\n";
  }
};

class BuyTransaction : public Transaction {
public:
  BuyTransaction() : stock_("AAPL") {}

  ~BuyTransaction() override {
    std::cout << "BuyTransaction destroyed\n";
    // After this, stock_ is destroyed, then Transaction::~Transaction() runs
  }

  void logTransaction() const override {
    std::cout << "Logging BUY of " << stock_ << "\n";  // stock_ is destroyed!
  }

private:
  std::string stock_;
};

void test() {
  BuyTransaction* bt = new BuyTransaction();
  delete bt;
  // Output:
  //   "BuyTransaction destroyed"       (BuyTransaction::~BuyTransaction)
  //   "Base transaction cleanup"        (Transaction::~Transaction calls
  //                                      Transaction::logTransaction, NOT
  //                                      BuyTransaction::logTransaction)
}
```

### Solution 1: Pass Information Up to the Base Class

Instead of calling down (via virtual functions), pass information **up** (via constructor parameters).

```cpp
// GOOD: Pass derived-class-specific data up to the base constructor
class Transaction {
public:
  explicit Transaction(const std::string& logInfo) {
    logTransaction(logInfo);  // Non-virtual call — safe
  }

  virtual ~Transaction() {}

  // Non-virtual — no polymorphism needed
  void logTransaction(const std::string& info) const {
    std::cout << "Transaction: " << info << "\n";
    // Write to log file, database, etc.
  }
};

class BuyTransaction : public Transaction {
public:
  BuyTransaction(const std::string& stock, int shares)
    : Transaction(createLogString(stock, shares)),  // pass info UP
    stock_(stock), shares_(shares) {}

private:
  // Static helper — can be called before the object is fully constructed
  // because it doesn't access any member variables
  static std::string createLogString(const std::string& stock, int shares) {
    return "BUY " + std::to_string(shares) + " shares of " + stock;
  }

  std::string stock_;
  int shares_;
};

class SellTransaction : public Transaction {
public:
  SellTransaction(const std::string& stock, int shares)
    : Transaction(createLogString(stock, shares)),
    stock_(stock), shares_(shares) {}

private:
  static std::string createLogString(const std::string& stock, int shares) {
    return "SELL " + std::to_string(shares) + " shares of " + stock;
  }

  std::string stock_;
  int shares_;
};

void test() {
  BuyTransaction bt("AAPL", 100);
  // Output: "Transaction: BUY 100 shares of AAPL" — correct!

  SellTransaction st("GOOG", 50);
  // Output: "Transaction: SELL 50 shares of GOOG" — correct!
}
```

**Note the use of a `static` helper function:** The function `createLogString` is `static`, so it doesn't 
depend on any member of the not-yet-constructed derived object. This is critical for safety.

### Solution 2: Post-Construction Initialization

Use a two-phase initialization pattern where virtual dispatch works correctly:

```cpp
// GOOD: Two-phase initialization with factory function
class Widget {
public:
  virtual ~Widget() = default;

  // Factory method ensures init() is called AFTER construction
  template<typename T, typename... Args>
  static std::unique_ptr<T> create(Args&&... args) {
    auto widget = std::unique_ptr<T>(new T(std::forward<Args>(args)...));
    widget->init();  // Virtual call AFTER full construction — safe!
    return widget;
  }

  virtual void doWork() = 0;

protected:
  Widget() {}  // Protected — force use of factory

  // Called after construction — virtual dispatch works correctly
  virtual void init() {
    std::cout << "Widget base init\n";
  }
};

class FancyWidget : public Widget {
public:
  void doWork() override {
    std::cout << "FancyWidget doing work with buffer of size " << bufferSize_ << "\n";
  }

protected:
  FancyWidget() : bufferSize_(0), buffer_(nullptr) {}

  void init() override {
    Widget::init();  // call base init
    bufferSize_ = 1024;
    buffer_ = new char[bufferSize_];
    std::cout << "FancyWidget initialized with buffer\n";
  }

  friend class Widget;  // allow Widget::create to call constructor

private:
  size_t bufferSize_;
  char* buffer_;
};

void test() {
  auto w = Widget::create<FancyWidget>();
  // Output:
  //   "Widget base init"
  //   "FancyWidget initialized with buffer"
  w->doWork();
  // Output: "FancyWidget doing work with buffer of size 1024"
}
```

### Real-World Example: GUI Widget Hierarchy

```cpp
// BAD version — virtual calls in constructor
class GUIWidget {
public:
  GUIWidget(int x, int y, int width, int height)
  : x_(x), y_(y), width_(width), height_(height) {
    // These virtual calls don't dispatch to derived classes!
    applyDefaultStyle();      // virtual — BAD
    calculateLayout();        // virtual — BAD
    registerEventHandlers();  // virtual — BAD
  }

  virtual ~GUIWidget() = default;
  virtual void applyDefaultStyle() { /* base style */ }
  virtual void calculateLayout() { /* base layout */ }
  virtual void registerEventHandlers() { /* base handlers */ }

protected:
  int x_, y_, width_, height_;
};

class Button : public GUIWidget {
public:
  Button(int x, int y, int w, int h, const std::string& label)
  : GUIWidget(x, y, w, h), label_(label) {}

  void applyDefaultStyle() override {
    // This is NEVER called from GUIWidget's constructor!
    // label_ is uninitialized when GUIWidget ctor runs
    std::cout << "Button style for: " << label_ << "\n";
  }

  void calculateLayout() override {
    // Calculates text position — but label_ doesn't exist yet!
    textWidth_ = label_.length() * 8;  // ACCESSING UNINITIALIZED MEMBER
  }

  void registerEventHandlers() override {
    onClick_ = [this]() { std::cout << "Clicked: " << label_ << "\n"; };
  }

private:
  std::string label_;
  int textWidth_;
  std::function<void()> onClick_;
};

// GOOD version — pass info up, or use post-construction init
class GUIWidget {
public:
  virtual ~GUIWidget() = default;

  // Factory with post-construction initialization
  template<typename T, typename... Args>
  static std::unique_ptr<T> create(Args&&... args) {
    auto widget = std::unique_ptr<T>(new T(std::forward<Args>(args)...));
    widget->applyDefaultStyle();
    widget->calculateLayout();
    widget->registerEventHandlers();
    return widget;
  }

  virtual void applyDefaultStyle() {}
  virtual void calculateLayout() {}
  virtual void registerEventHandlers() {}

protected:
  GUIWidget(int x, int y, int width, int height)
  : x_(x), y_(y), width_(width), height_(height) {}

  int x_, y_, width_, height_;
};

class Button : public GUIWidget {
protected:
  friend class GUIWidget;
  Button(int x, int y, int w, int h, const std::string& label)
  : GUIWidget(x, y, w, h), label_(label) {}

public:
  void applyDefaultStyle() override {
    std::cout << "Button style for: " << label_ << "\n";  // label_ is valid!
  }

  void calculateLayout() override {
    textWidth_ = label_.length() * 8;  // Safe — label_ exists
  }

  void registerEventHandlers() override {
    onClick_ = [this]() { std::cout << "Clicked: " << label_ << "\n"; };
  }

private:
  std::string label_;
  int textWidth_ = 0;
  std::function<void()> onClick_;
};

void test() {
  auto btn = GUIWidget::create<Button>(10, 20, 100, 30, "OK");
  // All virtual functions called AFTER full construction — correct behavior
}
```

### Things to Remember

- Don't call virtual functions during construction or destruction. During base class construction/destruction, 
virtual functions resolve to the base class version, never the derived class version.
- This behavior exists for safety: during base class construction, derived class members are uninitialized; 
during base class destruction, they have already been destroyed.
- Instead of virtual calls in constructors, pass derived-class-specific information **up** to the base class 
constructor (using static helper functions if necessary).
- Alternatively, use a post-construction initialization pattern (e.g., factory functions that call virtual 
`init()` after the object is fully constructed).

---
