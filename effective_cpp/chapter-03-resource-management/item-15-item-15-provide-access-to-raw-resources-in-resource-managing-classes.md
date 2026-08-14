# Item 15: Provide access to raw resources in resource-managing classes

## Visual Summary

```text
┌───────────────────────────────────────────────────────────────────────────┐
│   ITEM 15: PROVIDE ACCESS TO RAW RESOURCES IN RESOURCE-MANAGING CLASSES   │
├───────────────────────────────────────────────────────────────────────────┤
│ 1. RAII wrapper protects resource -> APIs may still require raw handle.   │
│ 2. Explicit get() -> caller consciously borrows the raw resource.         │
│ 3. Implicit conversion -> convenient but can hide lifetime mistakes.      │
│ 4. Never give ownership accidentally -> raw access should not mean raw    │
│ ownership.                                                                │
│ 5. Meaning: expose handles for interoperability while preserving          │
│ ownership semantics.                                                      │
└───────────────────────────────────────────────────────────────────────────┘
```

## Visual Deep Dive

```text
┌───────────────────────────────────────────────────────────────────────────┐
│                         BORROWED RAW HANDLE FLOW                          │
├───────────────────────────────────────────────────────────────────────────┤
│ RAII wrapper owns resource                                                │
│                                     ▼                                     │
│ Legacy API needs raw pointer/handle                                       │
│                                     ▼                                     │
│ wrapper.get() exposes borrowed handle                                     │
│                                     ▼                                     │
│ Ownership remains with wrapper                                            │
└───────────────────────────────────────────────────────────────────────────┘
```

```text
┌───────────────────────────────────────────────────────────────────────────┐
│                             RAW ACCESS CHOICE                             │
├───────────────────────────────────────────────────────────────────────────┤
│ Explicit get()                    | Implicit conversion                   │
│ ----------------------------------+-------------------------------------  │
│ Clear borrowing point             | Convenient                            │
│ Safer API boundary                | Can hide lifetime bugs                │
│ Slightly verbose                  | Use sparingly                         │
└───────────────────────────────────────────────────────────────────────────┘
```

### The Reality of APIs

RAII classes are wonderful, but the world is full of APIs that deal in raw resources. If
you are going to use RAII, you need a way to convert an RAII object into the raw resource
it wraps, because sooner or later you will need to pass it to an API that expects the raw
type.

```cpp
// Suppose we have an Investment hierarchy managed by shared_ptr
std::shared_ptr<Investment> pInv(createInvestment());

// And an API function that takes a raw pointer:
int daysHeld(const Investment* pi);        // How many days has this been held?
double creditRating(const Investment* pi); // What is the credit rating?

// We need to convert from shared_ptr<Investment> to const Investment*
```

### Explicit Conversion: The get() Member Function

Smart pointers provide a `get()` member function that returns a copy of the raw pointer
inside the smart pointer:

```cpp
std::shared_ptr<Investment> pInv(createInvestment());

int days = daysHeld(pInv.get());           // Pass raw pointer to the API
double rating = creditRating(pInv.get());
```

Smart pointers also overload `operator->` and `operator*`, so you can use them like raw
pointers in most contexts:

```cpp
class Investment {
public:
    bool isTaxFree() const;
    double currentValue() const;
};

std::shared_ptr<Investment> pInv(createInvestment());

bool taxFree = pInv->isTaxFree();         // operator->
double val = (*pInv).currentValue();       // operator*
```

### Designing Your Own RAII Classes: Explicit vs. Implicit Conversion

When you write your own RAII class, you must decide how clients will access the underlying
resource. There are two approaches: explicit conversion and implicit conversion.

#### Explicit Conversion via get()

```cpp
// A RAII wrapper for a C-style font handle
class Font {
public:
    explicit Font(const std::string& name, int size)
        : handle_(createFont(name.c_str(), size))
    {
        if (!handle_) throw std::runtime_error("Failed to create font");
    }

    ~Font() {
        if (handle_) destroyFont(handle_);
    }

    // Explicit conversion: client must call get()
    FontHandle get() const { return handle_; }

    Font(const Font&) = delete;
    Font& operator=(const Font&) = delete;

private:
    FontHandle handle_;   // Raw C handle
};
```

Usage:

```cpp
// C API function
void drawText(FontHandle font, const char* text, int x, int y);

Font f("Arial", 12);
drawText(f.get(), "Hello, World!", 10, 20);   // Must explicitly call get()
```

This is safe but verbose. Every time you use the font with a C API, you type `.get()`.

#### Implicit Conversion via operator

You can provide an implicit conversion operator:

```cpp
class Font {
public:
    explicit Font(const std::string& name, int size)
        : handle_(createFont(name.c_str(), size))
    {}

    ~Font() {
        if (handle_) destroyFont(handle_);
    }

    // Implicit conversion to FontHandle
    operator FontHandle() const { return handle_; }

    Font(const Font&) = delete;
    Font& operator=(const Font&) = delete;

private:
    FontHandle handle_;
};
```

Usage becomes seamless:

```cpp
Font f("Arial", 12);
drawText(f, "Hello, World!", 10, 20);   // Implicit conversion -- looks natural
```

But implicit conversions open the door to accidental misuse:

```cpp
// BAD: Implicit conversion can lead to dangling handles
Font f1("Arial", 12);
FontHandle h = f1;        // Implicit conversion -- h is a copy of the raw handle

// Now suppose f1 is destroyed (goes out of scope)...
// h is a dangling handle! Using it is undefined behavior.
```

```cpp
// BAD: Accidentally passing the wrong type
void changeFontSize(FontHandle fh, int newSize);  // C API

Font f("Arial", 12);
changeFontSize(f, 14);  // Compiles fine due to implicit conversion
// But did the programmer mean to modify the font managed by f?
// The C API might reallocate the handle, leaving f holding a stale value.
```

### The Trade-off: Safety vs. Convenience

The choice between explicit and implicit conversion is a design decision that involves
a trade-off:

| Aspect | Explicit (`get()`) | Implicit (`operator T()`) |
|---|---|---|
| Safety | Higher -- conversions are visible | Lower -- accidental conversions possible |
| Convenience | Lower -- verbose | Higher -- seamless with C APIs |
| Dangling risk | Lower -- deliberate action | Higher -- easy to extract and outlive |

**Meyers' recommendation**: Lean toward explicit conversion (`get()`), because the cost
of inadvertent type conversions usually outweighs the inconvenience of explicit calls.
However, the right choice depends on the specific use case and how the RAII class interacts
with existing APIs.

### Real-World Examples from the Standard Library

The standard library generally favors explicit conversion:

```cpp
// std::shared_ptr and std::unique_ptr use get()
std::shared_ptr<Widget> sp = std::make_shared<Widget>();
Widget* raw = sp.get();    // Explicit

// std::string provides c_str() for explicit conversion
std::string s = "hello";
const char* cstr = s.c_str();  // Explicit conversion to C string

// std::vector provides data() for explicit conversion
std::vector<int> v = {1, 2, 3};
int* arr = v.data();            // Explicit conversion to raw array
```

But some classes do provide implicit conversions:

```cpp
// std::string has an implicit conversion via operator basic_string_view (C++17)
// std::reference_wrapper has an implicit conversion to T&
std::reference_wrapper<int> ref(someInt);
int& r = ref;   // Implicit conversion
```

### Complete Example: A RAII Wrapper with Both Access Methods

```cpp
// A RAII class managing an OpenGL texture
class Texture {
public:
    explicit Texture(int width, int height, const unsigned char* pixels)
        : id_(0)
    {
        glGenTextures(1, &id_);
        glBindTexture(GL_TEXTURE_2D, id_);
        glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, width, height,
                     0, GL_RGBA, GL_UNSIGNED_BYTE, pixels);
    }

    ~Texture() {
        if (id_ != 0) {
            glDeleteTextures(1, &id_);
        }
    }

    // Explicit access -- preferred
    GLuint id() const { return id_; }

    // Move semantics (textures are GPU resources, not copyable)
    Texture(Texture&& other) noexcept : id_(other.id_) {
        other.id_ = 0;
    }

    Texture& operator=(Texture&& other) noexcept {
        if (this != &other) {
            if (id_ != 0) glDeleteTextures(1, &id_);
            id_ = other.id_;
            other.id_ = 0;
        }
        return *this;
    }

    Texture(const Texture&) = delete;
    Texture& operator=(const Texture&) = delete;

private:
    GLuint id_;
};

// Usage:
Texture tex(256, 256, pixelData);
glBindTexture(GL_TEXTURE_2D, tex.id());   // Explicit -- clear and safe
```

### Accessing Raw Resources Does Not Violate Encapsulation

It might seem that providing access to the raw resource defeats the purpose of the RAII
class. But the purpose of the RAII class is not to encapsulate the resource -- it is to
**ensure the resource is released**. Encapsulation is a secondary concern. If providing
access to the raw resource is necessary for the class to be useful, that access does not
undermine the class's primary mission.

Think of RAII classes as a careful layer on top of the resource, not a wall around it.
`shared_ptr` and `unique_ptr` both provide `get()`, and no one considers them poorly
designed.

Some RAII classes combine both roles (resource management AND encapsulation), but these
are the minority. Most RAII classes exist solely to guarantee cleanup.

### Things to Remember

- **APIs often require access to raw resources, so each RAII class should offer a way to
  get at the resource it manages.**

- **Access may be via explicit conversion (e.g., a `get()` member function) or implicit
  conversion (e.g., `operator RawType()`). Explicit conversion is generally safer; implicit
  conversion is more convenient for callers.**

- **Providing access to the raw resource does not violate encapsulation. RAII classes exist
  to guarantee resource release, not to hide the resource.**

---
