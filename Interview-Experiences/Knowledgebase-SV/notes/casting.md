
### Explicit Keyword

By default, C++ allows implicit conversions for single-argument constructors. 
This means that if you have a constructor with one parameter, the compiler 
will automatically convert objects of that parameter’s type into objects of 
your class if needed.

- The explicit keyword prevents these implicit conversions.

```cpp
#include <iostream>

class MyClass {
public:
    // Constructor with 'explicit'
    explicit MyClass(int x) {
        std::cout << "MyClass constructor called with value: " << x << std::endl;
    }
};

void func(MyClass obj) {
    std::cout << "In func()" << std::endl;
}

int main() {
    // func(5);  // Error: implicit conversion from int to MyClass is not allowed!
    func(MyClass(5));  // This works because we explicitly create a MyClass object
    return 0;
}
```

### Casting

#### Static Casting

`static_cast` is used for compile-time type conversions between compatible 
types. It performs the conversion at compile time, ensuring type safety in 
most cases, *but it does not perform runtime checks (unlike dynamic_cast).*

```cpp
#include <iostream>

int main() {
    // Basic type conversion
    float f = 9.5;
    int i = static_cast<int>(f);  // Converts float to int
    std::cout << "int i: " << i << std::endl;

    // Upcasting (Derived to Base)
    class Base {};
    class Derived : public Base {};
    Derived d;
    Base* basePtr = static_cast<Base*>(&d);  // Safe upcast (Derived* -> Base*)

    return 0;
}
```
*static_cast performs no runtime checks, so downcasting (casting from base to 
derived) is unsafe unless you’re sure of the object type.*

#### Dynamic Casting

`dynamic_cast` is used for runtime type checking and safe downcasting in 
inheritance hierarchies. It is primarily used for casting between base and 
derived class pointers or references when polymorphism is involved (i.e., 
when you have a virtual function in the base class).

```cpp
#include <iostream>

class Base {
public:
    virtual ~Base() = default;  // Must have at least one virtual function
};

class Derived : public Base {};

int main() {
    Base* basePtr = new Derived();  // Pointer to Base, but actually a Derived object

    // Safe downcast: checks at runtime if basePtr actually points to a Derived object
    Derived* derivedPtr = dynamic_cast<Derived*>(basePtr);
    if (derivedPtr) {
        std::cout << "Successfully casted to Derived" << std::endl;
    } else {
        std::cout << "Failed to cast to Derived" << std::endl;
    }

    delete basePtr;
    return 0;
}
```

*dynamic_cast only works with pointers or references to polymorphic types (classes with at least one virtual function).*

#### Re-interpret Casting

`reinterpret_cast` is the most dangerous cast, used for low-level type 
reinterpretation. It allows you to treat a block of memory as if it were a 
different type entirely. This is often used for pointer conversions or 
type-punning.

This example shows how to use reinterpret_cast to interpret a 32-bit integer 
(std::uint32_t) as an array of bytes. This kind of operation can be useful in 
networking or binary file I/O, where you need to break a larger value into 
its individual bytes (little-endian or big-endian conversion).

```cpp
#include <iostream>
#include <cstdint>  // For uint32_t

void printBytes(const std::uint8_t* byteArray, std::size_t size) {
    for (std::size_t i = 0; i < size; ++i) {
        std::cout << "Byte " << i << ": 0x" << std::hex << static_cast<int>(byteArray[i]) << std::endl;
    }
}

int main() {
    std::uint32_t value = 0x12345678;  // A 32-bit integer (hexadecimal representation)
    
    // Reinterpret the 32-bit integer as a byte array
    const std::uint8_t* byteArray = reinterpret_cast<const std::uint8_t*>(&value);
    
    // Print the individual bytes
    std::cout << "Value as bytes:" << std::endl;
    printBytes(byteArray, sizeof(value));  // Should print the 4 bytes of the integer

    return 0;
}
```
**Output in Little Endian Machine:**
```
Value as bytes:
Byte 0: 0x78
Byte 1: 0x56
Byte 2: 0x34
Byte 3: 0x12
```

#### Const Casting
Refer [these](./const_constexpr.md) notes.