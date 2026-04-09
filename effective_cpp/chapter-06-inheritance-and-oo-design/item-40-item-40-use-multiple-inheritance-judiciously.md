# Item 40: Use multiple inheritance judiciously

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
