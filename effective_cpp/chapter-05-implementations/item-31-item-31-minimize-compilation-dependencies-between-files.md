# Item 31: Minimize compilation dependencies between files

C++ does not do a great job of separating interfaces from implementations.
A class definition includes not just the interface (public member functions)
but also a substantial amount of implementation detail (private members,
private functions). This means that if you change a private member of a class,
every file that `#include`s that class's header must be recompiled --- even if
no client code uses the private member.

In a large project, this can lead to devastating build times. A single change
to a private data member in a core header can trigger recompilation of
hundreds of source files.

### The Problem

```cpp
// person.h
#include <string>         // Needed for std::string data member
#include <memory>         // Needed for std::shared_ptr
#include "date.h"         // Needed for Date data member
#include "address.h"      // Needed for Address data member

class Person {
public:
    Person(const std::string& name, const Date& birthday,
           const Address& addr);

    std::string name() const;
    std::string birthDate() const;
    std::string address() const;

private:
    std::string name_;     // Implementation detail!
    Date birthDate_;       // Implementation detail!
    Address address_;      // Implementation detail!
};
```

**The dependency chain:**

Any file that `#include`s `person.h` also transitively includes `<string>`,
`<memory>`, `date.h`, and `address.h`. If `date.h` or `address.h` changes,
every file that includes `person.h` must be recompiled --- even if the change
was to a private implementation detail of `Date` or `Address`.

If `Person` is a widely used class, this can mean that changing a private
member of `Address` triggers recompilation of your entire project.

### Solution 1: The pImpl (Pointer to Implementation) Idiom

The key insight: **you can replace data members with a pointer to a struct
that contains them.** The class definition then depends only on a forward
declaration of the implementation struct, not on the full definitions of the
member types.

```cpp
// =====================================================
// person.h --- the public header (interface)
// =====================================================
#include <string>
#include <memory>

// Forward declarations: no #include needed for Date or Address!
class Date;
class Address;

class Person {
public:
    Person(const std::string& name, const Date& birthday,
           const Address& addr);
    ~Person();                          // Must be declared (see below)

    // Move and copy operations must also be declared here if you want
    // them, because the compiler cannot generate them in headers that
    // do not see the full definition of PersonImpl.
    Person(const Person& rhs);
    Person& operator=(const Person& rhs);
    Person(Person&& rhs) noexcept;
    Person& operator=(Person&& rhs) noexcept;

    std::string name() const;
    std::string birthDate() const;
    std::string address() const;

private:
    // The only data member: a pointer to the implementation.
    // This is the "pImpl" (pointer-to-implementation).
    struct Impl;                         // Forward declaration of nested struct
    std::unique_ptr<Impl> pImpl_;        // Pointer to implementation
};

// =====================================================
// person.cpp --- the implementation file
// =====================================================
#include "person.h"
#include "date.h"        // Now these includes are only in the .cpp file.
#include "address.h"     // Changes to date.h or address.h only trigger
                         // recompilation of person.cpp, NOT of all the
                         // files that include person.h.

// Define the implementation struct.
struct Person::Impl {
    std::string name;
    Date birthDate;
    Address address;

    Impl(const std::string& n, const Date& bd, const Address& a)
        : name(n), birthDate(bd), address(a) {}
};

// Constructor: create the Impl on the heap.
Person::Person(const std::string& name, const Date& birthday,
               const Address& addr)
    : pImpl_(std::make_unique<Impl>(name, birthday, addr)) {}

// Destructor: must be defined in the .cpp file where Impl is complete.
// If it were defined in the header (or defaulted in the header), the
// compiler would try to generate ~unique_ptr<Impl>, which needs the
// full definition of Impl. This would fail or produce undefined behavior.
Person::~Person() = default;

// Copy constructor: deep copy the Impl.
Person::Person(const Person& rhs)
    : pImpl_(std::make_unique<Impl>(*rhs.pImpl_)) {}

// Copy assignment: deep copy the Impl.
Person& Person::operator=(const Person& rhs) {
    if (this != &rhs) {
        *pImpl_ = *rhs.pImpl_;
    }
    return *this;
}

// Move constructor.
Person::Person(Person&& rhs) noexcept = default;

// Move assignment.
Person& Person::operator=(Person&& rhs) noexcept = default;

// Member functions: delegate to Impl.
std::string Person::name() const { return pImpl_->name; }
std::string Person::birthDate() const { return pImpl_->birthDate.toString(); }
std::string Person::address() const { return pImpl_->address.toString(); }
```

**What we achieved:** Files that `#include "person.h"` no longer depend on
`date.h` or `address.h`. If we change `Date` or `Address` (or even add new
private data members to `Person`), only `person.cpp` needs to be recompiled.

### Solution 2: Abstract Base Classes (Interface Classes)

An alternative to pImpl is to define the interface as an abstract base class
with pure virtual functions, and provide the implementation in a derived class
visible only in the `.cpp` file:

```cpp
// =====================================================
// person.h --- the public header (interface class)
// =====================================================
#include <string>
#include <memory>

class Date;      // Forward declaration
class Address;   // Forward declaration

// Person is an abstract base class (interface).
// It has no data members, so it depends on nothing except the
// types used in its public interface.
class Person {
public:
    virtual ~Person() = default;

    virtual std::string name() const = 0;
    virtual std::string birthDate() const = 0;
    virtual std::string address() const = 0;

    // Factory function: clients call this to create Person objects.
    // They never see the concrete class.
    static std::unique_ptr<Person> create(
        const std::string& name,
        const Date& birthday,
        const Address& addr
    );
};

// =====================================================
// person.cpp --- the implementation file
// =====================================================
#include "person.h"
#include "date.h"
#include "address.h"

// RealPerson is the concrete implementation. It is NOT visible
// in person.h, so clients have no dependency on it.
class RealPerson : public Person {
public:
    RealPerson(const std::string& name, const Date& bd, const Address& a)
        : name_(name), birthDate_(bd), address_(a) {}

    std::string name() const override { return name_; }
    std::string birthDate() const override { return birthDate_.toString(); }
    std::string address() const override { return address_.toString(); }

private:
    std::string name_;
    Date birthDate_;
    Address address_;
};

// Factory function implementation.
std::unique_ptr<Person> Person::create(
    const std::string& name, const Date& birthday, const Address& addr)
{
    return std::make_unique<RealPerson>(name, birthday, addr);
}
```

**Usage:**

```cpp
// client.cpp
#include "person.h"
// No need to include date.h or address.h here if we use forward declarations
// or if Date and Address are only used to pass to the factory.

#include "date.h"     // Needed here only because we construct Date/Address objects
#include "address.h"

void processPersons() {
    auto p = Person::create(
        "Alice",
        Date(1990, 3, 15),
        Address("123 Main St", "Springfield", "IL")
    );

    std::cout << p->name() << "\n";
    std::cout << p->birthDate() << "\n";
    std::cout << p->address() << "\n";
}
```

### pImpl vs. Interface Classes: Trade-offs

| Aspect | pImpl | Interface Class |
|--------|-------|-----------------|
| Runtime cost | One indirection (pointer dereference) per member access | Virtual function call per member access (vtable lookup) |
| Memory | Extra heap allocation for Impl | Extra vptr per object |
| Extensibility | Internal; clients cannot extend | Clients can derive new implementations |
| Binary compatibility | Excellent: adding private members does not break ABI | Excellent: adding new pure virtual functions breaks ABI, but adding non-pure virtual functions may not |
| Boilerplate | Must forward all public functions to Impl | Must implement all pure virtual functions in derived class |

### Forward Declarations: The Foundation of Dependency Reduction

The key principle is: **depend on declarations, not definitions.** You can
use forward declarations instead of `#include` whenever you only need to know
that a type exists, not what it contains:

```cpp
// You CAN use a forward declaration when:
class Widget;    // Forward declaration is enough for:

// Widget* ptr;              // Pointers to Widget
// Widget& ref;              // References to Widget (in declarations)
// Widget func();            // Functions that return Widget by value (declaration only)
// void func(Widget w);      // Functions that take Widget by value (declaration only)
// std::unique_ptr<Widget>;  // Smart pointers to Widget (with caveats)

// You CANNOT use a forward declaration when:
// - You need to know the size of Widget (to allocate it on the stack)
// - You need to call Widget's member functions
// - You need to access Widget's data members
// - You need to inherit from Widget
```

### A Comprehensive Real-World Example

Consider a graphics engine with complex interdependencies:

```cpp
// =====================================================
// BEFORE: Tight coupling --- one change rebuilds everything
// =====================================================

// renderer.h
#include "texture.h"      // Full definition of Texture
#include "shader.h"       // Full definition of Shader
#include "mesh.h"         // Full definition of Mesh
#include "camera.h"       // Full definition of Camera
#include "light.h"        // Full definition of Light

class Renderer {
public:
    void render(const Camera& cam, const std::vector<Light>& lights);
    void loadTexture(const std::string& path);
    void setShader(const Shader& shader);
    void addMesh(const Mesh& mesh);

private:
    Texture currentTexture_;     // Requires full definition of Texture
    Shader currentShader_;       // Requires full definition of Shader
    std::vector<Mesh> meshes_;   // Requires full definition of Mesh
    Camera mainCamera_;          // Requires full definition of Camera
    std::vector<Light> lights_;  // Requires full definition of Light
};

// Any change to Texture, Shader, Mesh, Camera, or Light forces
// recompilation of renderer.h and EVERY file that includes it.
```

```cpp
// =====================================================
// AFTER: Loose coupling with pImpl
// =====================================================

// renderer.h
#include <string>
#include <memory>
#include <vector>

// Forward declarations --- no #includes for our types!
class Texture;
class Shader;
class Mesh;
class Camera;
class Light;

class Renderer {
public:
    Renderer();
    ~Renderer();
    Renderer(Renderer&&) noexcept;
    Renderer& operator=(Renderer&&) noexcept;

    void render(const Camera& cam, const std::vector<Light*>& lights);
    void loadTexture(const std::string& path);
    void setShader(const Shader& shader);
    void addMesh(const Mesh& mesh);

private:
    struct Impl;
    std::unique_ptr<Impl> pImpl_;
};

// renderer.cpp
#include "renderer.h"
#include "texture.h"     // Includes are now localized to the .cpp file.
#include "shader.h"
#include "mesh.h"
#include "camera.h"
#include "light.h"

struct Renderer::Impl {
    Texture currentTexture;
    Shader currentShader;
    std::vector<Mesh> meshes;
    Camera mainCamera;
    std::vector<Light> lights;
};

Renderer::Renderer() : pImpl_(std::make_unique<Impl>()) {}
Renderer::~Renderer() = default;
Renderer::Renderer(Renderer&&) noexcept = default;
Renderer& Renderer::operator=(Renderer&&) noexcept = default;

void Renderer::render(const Camera& cam, const std::vector<Light*>& lights) {
    pImpl_->mainCamera = cam;
    // ... rendering logic using pImpl_->currentShader, pImpl_->meshes, etc.
}

void Renderer::loadTexture(const std::string& path) {
    pImpl_->currentTexture.loadFromFile(path);
}

void Renderer::setShader(const Shader& shader) {
    pImpl_->currentShader = shader;
}

void Renderer::addMesh(const Mesh& mesh) {
    pImpl_->meshes.push_back(mesh);
}
```

Now, changing `Texture`, `Shader`, `Mesh`, `Camera`, or `Light` only requires
recompiling `renderer.cpp` --- not the hundreds of files that include
`renderer.h`.

### Practical Tips for Reducing Compilation Dependencies

**1. Prefer forward declarations to `#include` in headers:**

```cpp
// BAD: header includes everything
// widget.h
#include "gadget.h"       // Only needed for Gadget* parameter

class Widget {
public:
    void useGadget(Gadget* g);   // Only uses pointer; forward decl suffices
};

// GOOD: forward declare in header, include in source
// widget.h
class Gadget;   // Forward declaration

class Widget {
public:
    void useGadget(Gadget* g);
};

// widget.cpp
#include "widget.h"
#include "gadget.h"   // Include only where the full definition is needed

void Widget::useGadget(Gadget* g) {
    g->activate();   // Need full definition here, which we have via #include
}
```

**2. Use `<iosfwd>` instead of `<iostream>` in headers:**

```cpp
// BAD: <iostream> is a heavy header
#include <iostream>

class Logger {
public:
    void log(std::ostream& os, const std::string& msg);
};

// GOOD: <iosfwd> is a lightweight header with only forward declarations
#include <iosfwd>
#include <string>

class Logger {
public:
    void log(std::ostream& os, const std::string& msg);
};

// logger.cpp
#include "logger.h"
#include <iostream>   // Full definition needed only in the implementation
```

**3. Provide separate "fwd" headers for your own types:**

```cpp
// geometry_fwd.h --- lightweight forward declarations
class Point;
class Line;
class Circle;
class Rectangle;
class Polygon;

// geometry.h --- full definitions
#include "geometry_fwd.h"

class Point {
    double x_, y_;
public:
    Point(double x = 0, double y = 0);
    // ...
};

class Line {
    Point start_, end_;
public:
    Line(const Point& s, const Point& e);
    // ...
};
// ... etc.

// client.h --- only needs forward declarations
#include "geometry_fwd.h"   // Lightweight: no dependency on geometry details

class Renderer {
public:
    void drawPoint(const Point& p);
    void drawLine(const Line& l);
};

// client.cpp --- needs full definitions for implementation
#include "client.h"
#include "geometry.h"   // Full definitions needed here

void Renderer::drawPoint(const Point& p) {
    // ... uses Point's members
}
```

**4. Use `unique_ptr` rather than `shared_ptr` for pImpl:**

```cpp
// Prefer unique_ptr for pImpl. It has no overhead beyond a raw pointer
// and clearly expresses sole ownership.

class Widget {
public:
    Widget();
    ~Widget();   // Must be declared in header, defined in .cpp where Impl is complete
    Widget(Widget&&) noexcept;
    Widget& operator=(Widget&&) noexcept;

private:
    struct Impl;
    std::unique_ptr<Impl> pImpl_;   // Preferred
};

// Note: shared_ptr does not require the destructor trick because
// shared_ptr stores its deleter at construction time. But shared_ptr
// has higher overhead (reference counting, separate control block),
// and shared ownership semantics are usually not what you want for pImpl.
```

**5. Include-what-you-use (IWYU) discipline:**

```cpp
// Every header should include exactly the headers it needs and no more.
// Every source file should include the headers for every type it uses
// directly, not relying on transitive includes.

// BAD: relying on transitive include
// foo.h includes <vector>
#include "foo.h"
std::vector<int> v;   // Works by accident (through foo.h's include)

// GOOD: include what you use
#include "foo.h"
#include <vector>      // Explicitly include what you use
std::vector<int> v;    // Works by design
```

### Things to Remember

- **The general idea behind minimizing compilation dependencies is to depend
  on declarations instead of definitions.** Two approaches based on this idea
  are the pImpl idiom and interface classes.

- **Library header files should exist in full and declaration-only forms.**
  The Standard Library provides `<iosfwd>` as a model. Your own libraries
  should provide similar `_fwd.h` headers.

- **The pImpl idiom replaces data members with a pointer to an implementation
  struct.** This moves `#include` dependencies from the header to the source
  file, making recompilation cheaper when implementation details change.

- **Interface classes (abstract base classes with factory functions) achieve
  the same decoupling.** Clients program to the abstract interface and never
  see the concrete implementation class.

- **Both pImpl and interface classes have a small runtime cost** (pointer
  indirection and heap allocation for pImpl; virtual function dispatch for
  interface classes), but the improvement in build times for large projects
  more than compensates.
