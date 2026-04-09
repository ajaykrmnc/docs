# Item 48: Be aware of template metaprogramming

### What is template metaprogramming?

Template metaprogramming (TMP) is the process of writing programs that execute during compilation. The C++ template system is Turing-complete -- it can compute anything that a general-purpose computer can compute (given enough resources). TMP programs are written in C++ template syntax but run at compile time, producing constants, types, or code as their output.

TMP has two great strengths:
1. It makes some things easy that would otherwise be hard or impossible.
2. It shifts work from runtime to compile time, leading to smaller executables, shorter runtimes, and earlier error detection.

The main downsides: longer compile times, difficult-to-read code, and notoriously inscrutable error messages.

### The classic example: compile-time factorial

```cpp
// TMP factorial: computes n! at compile time
template <unsigned N>
struct Factorial {
    static constexpr unsigned value = N * Factorial<N - 1>::value;
};

// Base case: 0! = 1
template <>
struct Factorial<0> {
    static constexpr unsigned value = 1;
};

// Usage:
static_assert(Factorial<5>::value == 120);
static_assert(Factorial<0>::value == 1);
static_assert(Factorial<10>::value == 3628800);

// The value 120 is computed at compile time -- no runtime computation.
int main() {
    // This array declaration proves the value is a compile-time constant:
    int arr[Factorial<5>::value];  // int arr[120]; -- legal only if value is constexpr
    std::cout << "5! = " << Factorial<5>::value << "\n";
}
```

The recursion unfolds at compile time:
- `Factorial<5>::value` = 5 * `Factorial<4>::value`
- `Factorial<4>::value` = 4 * `Factorial<3>::value`
- `Factorial<3>::value` = 3 * `Factorial<2>::value`
- `Factorial<2>::value` = 2 * `Factorial<1>::value`
- `Factorial<1>::value` = 1 * `Factorial<0>::value`
- `Factorial<0>::value` = 1 (base case)

### Compile-time Fibonacci

```cpp
template <unsigned N>
struct Fibonacci {
    static constexpr unsigned long long value =
        Fibonacci<N - 1>::value + Fibonacci<N - 2>::value;
};

template <>
struct Fibonacci<0> {
    static constexpr unsigned long long value = 0;
};

template <>
struct Fibonacci<1> {
    static constexpr unsigned long long value = 1;
};

static_assert(Fibonacci<0>::value == 0);
static_assert(Fibonacci<1>::value == 1);
static_assert(Fibonacci<10>::value == 55);
static_assert(Fibonacci<20>::value == 6765);
static_assert(Fibonacci<46>::value == 1836311903);
```

Note: this naive recursive approach has exponential compile-time complexity (each `Fibonacci<N>` instantiates `Fibonacci<N-1>` and `Fibonacci<N-2>`, and memoization depends on the compiler). A linear version:

```cpp
template <unsigned N, unsigned long long Prev = 0, unsigned long long Curr = 1>
struct FibLinear {
    static constexpr unsigned long long value =
        FibLinear<N - 1, Curr, Prev + Curr>::value;
};

template <unsigned long long Prev, unsigned long long Curr>
struct FibLinear<0, Prev, Curr> {
    static constexpr unsigned long long value = Prev;
};

static_assert(FibLinear<10>::value == 55);
static_assert(FibLinear<50>::value == 12586269025ULL);
```

### Compile-time greatest common divisor

```cpp
template <unsigned A, unsigned B>
struct GCD {
    static constexpr unsigned value = GCD<B, A % B>::value;
};

template <unsigned A>
struct GCD<A, 0> {
    static constexpr unsigned value = A;
};

static_assert(GCD<12, 8>::value == 4);
static_assert(GCD<100, 75>::value == 25);
static_assert(GCD<17, 13>::value == 1);  // Coprime
```

### Type-level computation: type lists

TMP can manipulate types themselves, not just values:

```cpp
#include <type_traits>
#include <iostream>
#include <string>

// A type list is a compile-time list of types
template <typename... Ts>
struct TypeList {};

// Length of a type list
template <typename List>
struct Length;

template <typename... Ts>
struct Length<TypeList<Ts...>> {
    static constexpr std::size_t value = sizeof...(Ts);
};

// Access the Nth type in a type list
template <typename List, std::size_t N>
struct TypeAt;

template <typename Head, typename... Tail>
struct TypeAt<TypeList<Head, Tail...>, 0> {
    using type = Head;
};

template <typename Head, typename... Tail, std::size_t N>
struct TypeAt<TypeList<Head, Tail...>, N> {
    using type = typename TypeAt<TypeList<Tail...>, N - 1>::type;
};

// Append a type to a type list
template <typename List, typename T>
struct Append;

template <typename... Ts, typename T>
struct Append<TypeList<Ts...>, T> {
    using type = TypeList<Ts..., T>;
};

// Prepend a type to a type list
template <typename List, typename T>
struct Prepend;

template <typename... Ts, typename T>
struct Prepend<TypeList<Ts...>, T> {
    using type = TypeList<T, Ts...>;
};

// Check if a type is in the list
template <typename List, typename T>
struct Contains;

template <typename T>
struct Contains<TypeList<>, T> {
    static constexpr bool value = false;
};

template <typename Head, typename... Tail, typename T>
struct Contains<TypeList<Head, Tail...>, T> {
    static constexpr bool value =
        std::is_same_v<Head, T> || Contains<TypeList<Tail...>, T>::value;
};

// Remove duplicates from a type list
template <typename List>
struct Unique;

template <>
struct Unique<TypeList<>> {
    using type = TypeList<>;
};

template <typename Head, typename... Tail>
struct Unique<TypeList<Head, Tail...>> {
private:
    using UniqueTail = typename Unique<TypeList<Tail...>>::type;
public:
    using type = std::conditional_t<
        Contains<UniqueTail, Head>::value,
        UniqueTail,
        typename Prepend<UniqueTail, Head>::type
    >;
};

// Usage:
using MyTypes = TypeList<int, double, std::string, float>;

static_assert(Length<MyTypes>::value == 4);
static_assert(std::is_same_v<typename TypeAt<MyTypes, 0>::type, int>);
static_assert(std::is_same_v<typename TypeAt<MyTypes, 2>::type, std::string>);
static_assert(Contains<MyTypes, double>::value);
static_assert(!Contains<MyTypes, char>::value);

using WithDups = TypeList<int, double, int, float, double>;
using NoDups = typename Unique<WithDups>::type;
static_assert(Length<NoDups>::value == 3);  // int, double, float
```

### TMP for compile-time dimensional analysis

A powerful real-world application of TMP is checking physical units at compile time:

```cpp
#include <iostream>
#include <ratio>

// Represent physical dimensions as compile-time integers
// (mass, length, time)
template <int Mass, int Length, int Time>
struct Dimension {
    static constexpr int mass = Mass;
    static constexpr int length = Length;
    static constexpr int time = Time;
};

// A quantity with a value and a dimension
template <typename Dim>
class Quantity {
public:
    explicit Quantity(double val) : value_(val) {}
    double value() const { return value_; }

    // Addition: only quantities of the same dimension can be added
    Quantity operator+(const Quantity& rhs) const {
        return Quantity(value_ + rhs.value_);
    }

    Quantity operator-(const Quantity& rhs) const {
        return Quantity(value_ - rhs.value_);
    }

    // Scalar multiplication
    Quantity operator*(double scalar) const {
        return Quantity(value_ * scalar);
    }

    // Multiplication of quantities: dimensions add
    template <typename OtherDim>
    auto operator*(const Quantity<OtherDim>& rhs) const {
        using ResultDim = Dimension<
            Dim::mass + OtherDim::mass,
            Dim::length + OtherDim::length,
            Dim::time + OtherDim::time
        >;
        return Quantity<ResultDim>(value_ * rhs.value());
    }

    // Division of quantities: dimensions subtract
    template <typename OtherDim>
    auto operator/(const Quantity<OtherDim>& rhs) const {
        using ResultDim = Dimension<
            Dim::mass - OtherDim::mass,
            Dim::length - OtherDim::length,
            Dim::time - OtherDim::time
        >;
        return Quantity<ResultDim>(value_ / rhs.value());
    }

private:
    double value_;
};

// Define common physical dimensions
using Scalar      = Dimension<0, 0, 0>;
using Mass        = Dimension<1, 0, 0>;     // kg
using Length      = Dimension<0, 1, 0>;     // m
using Time        = Dimension<0, 0, 1>;     // s
using Velocity    = Dimension<0, 1, -1>;    // m/s
using Accel       = Dimension<0, 1, -2>;    // m/s^2
using Force       = Dimension<1, 1, -2>;    // kg*m/s^2 = Newton
using Energy      = Dimension<1, 2, -2>;    // kg*m^2/s^2 = Joule

int main() {
    Quantity<Mass> m(10.0);        // 10 kg
    Quantity<Accel> a(9.8);        // 9.8 m/s^2
    auto force = m * a;            // Quantity<Force> -- 98 N (computed at compile time)

    Quantity<Length> d(100.0);      // 100 m
    auto energy = force * d;       // Quantity<Energy> -- 9800 J

    Quantity<Time> t(5.0);
    auto vel = d / t;              // Quantity<Velocity> -- 20 m/s

    std::cout << "Force: " << force.value() << " N\n";
    std::cout << "Energy: " << energy.value() << " J\n";
    std::cout << "Velocity: " << vel.value() << " m/s\n";

    // Compile-time error: cannot add mass and velocity!
    // auto bad = m + vel;  // ERROR: Quantity<Mass> + Quantity<Velocity> -- no match
}
```

The dimension checking happens entirely at compile time. The generated code is as efficient as raw `double` arithmetic -- zero runtime overhead.

### TMP for compile-time loop unrolling

```cpp
// Compile-time dot product with loop unrolling
template <int N>
struct DotProduct {
    template <typename T>
    static T compute(const T* a, const T* b) {
        return a[N-1] * b[N-1] + DotProduct<N-1>::compute(a, b);
    }
};

template <>
struct DotProduct<1> {
    template <typename T>
    static T compute(const T* a, const T* b) {
        return a[0] * b[0];
    }
};

// Usage:
double a[] = {1.0, 2.0, 3.0, 4.0};
double b[] = {5.0, 6.0, 7.0, 8.0};
double result = DotProduct<4>::compute(a, b);
// Compiler generates: a[3]*b[3] + a[2]*b[2] + a[1]*b[1] + a[0]*b[0]
// No loop overhead -- completely unrolled at compile time.
```

### Compile-time power function

```cpp
// Compute base^exp at compile time with fast exponentiation
template <unsigned Base, unsigned Exp>
struct Power {
    static constexpr unsigned long long value =
        (Exp % 2 == 0)
        ? Power<Base, Exp / 2>::value * Power<Base, Exp / 2>::value
        : Base * Power<Base, Exp - 1>::value;
};

template <unsigned Base>
struct Power<Base, 0> {
    static constexpr unsigned long long value = 1;
};

static_assert(Power<2, 10>::value == 1024);
static_assert(Power<3, 5>::value == 243);
static_assert(Power<10, 6>::value == 1000000);
```

### TMP for compile-time string processing (C++17)

```cpp
// Compile-time string hash (FNV-1a)
constexpr std::size_t fnv1a_hash(const char* str, std::size_t len) {
    std::size_t hash = 14695981039346656037ULL;
    for (std::size_t i = 0; i < len; ++i) {
        hash ^= static_cast<std::size_t>(str[i]);
        hash *= 1099511628211ULL;
    }
    return hash;
}

// A compile-time string wrapper
template <std::size_t N>
struct FixedString {
    char data[N];
    constexpr FixedString(const char (&str)[N]) {
        for (std::size_t i = 0; i < N; ++i) data[i] = str[i];
    }
    constexpr std::size_t hash() const { return fnv1a_hash(data, N - 1); }
};

// Usage in a compile-time switch-like construct:
constexpr auto h = FixedString("hello").hash();
static_assert(h != 0);  // Non-zero hash computed at compile time
```

### constexpr: the modern alternative to classic TMP

C++11 introduced `constexpr`, which provides a much more readable way to do compile-time computation. C++14 and C++17 further relaxed its restrictions:

```cpp
// constexpr factorial -- reads like normal code!
constexpr unsigned long long factorial(unsigned n) {
    unsigned long long result = 1;
    for (unsigned i = 2; i <= n; ++i)
        result *= i;
    return result;
}

static_assert(factorial(5) == 120);
static_assert(factorial(20) == 2432902008176640000ULL);

// constexpr Fibonacci
constexpr unsigned long long fibonacci(unsigned n) {
    if (n <= 1) return n;
    unsigned long long prev = 0, curr = 1;
    for (unsigned i = 2; i <= n; ++i) {
        unsigned long long next = prev + curr;
        prev = curr;
        curr = next;
    }
    return curr;
}

static_assert(fibonacci(10) == 55);
static_assert(fibonacci(50) == 12586269025ULL);

// constexpr GCD
constexpr unsigned gcd(unsigned a, unsigned b) {
    while (b != 0) {
        unsigned t = b;
        b = a % b;
        a = t;
    }
    return a;
}

static_assert(gcd(12, 8) == 4);
```

While `constexpr` replaces many uses of classic TMP for value computation, TMP remains essential for **type computation** -- selecting types, transforming type lists, and generating code based on type properties.

### Real-world uses of TMP

1. **Ensuring correctness at compile time** -- dimensional analysis (shown above), strong typedefs, and policy checking.

2. **Optimizing performance** -- expression templates in linear algebra libraries (Eigen, Blaze) eliminate temporary objects:

```cpp
// Without expression templates:
Matrix a, b, c, d;
Matrix result = a + b + c + d;
// Creates 3 temporaries: (a+b), ((a+b)+c), (((a+b)+c)+d)

// With expression templates (TMP):
// The expression a + b + c + d creates a lightweight expression object.
// Only when assigned to result does a single pass evaluate the sum.
// Zero temporaries, one loop -- as fast as hand-written code.
```

3. **Static interface checking** -- C++20 concepts are the modern way, but pre-C++20 code uses TMP:

```cpp
// Pre-C++20: SFINAE-based concept checking
template <typename T,
          typename = std::enable_if_t<
              std::is_default_constructible_v<T> &&
              std::is_copy_assignable_v<T>>>
class Container {
    // Only instantiates if T is default-constructible and copy-assignable
};

// C++20: concepts (built on top of TMP infrastructure)
template <typename T>
concept Storable = std::is_default_constructible_v<T> &&
                   std::is_copy_assignable_v<T>;

template <Storable T>
class Container {
    // Clean, readable constraint
};
```

4. **Compile-time state machines** -- verifying protocol compliance at compile time:

```cpp
// States
struct Disconnected {};
struct Connected {};
struct Authenticated {};

// Connection class with compile-time state tracking
template <typename State>
class Connection {
public:
    // Only callable in Disconnected state
    Connection<Connected> connect(const std::string& host)
        requires std::is_same_v<State, Disconnected>
    {
        // ... perform connection ...
        return Connection<Connected>{};
    }

    // Only callable in Connected state
    Connection<Authenticated> authenticate(const std::string& token)
        requires std::is_same_v<State, Connected>
    {
        // ... perform auth ...
        return Connection<Authenticated>{};
    }

    // Only callable in Authenticated state
    void sendData(const std::string& data)
        requires std::is_same_v<State, Authenticated>
    {
        // ... send data ...
    }
};

// Usage:
// Connection<Disconnected> conn;
// auto connected = conn.connect("example.com");
// auto authed = connected.authenticate("token123");
// authed.sendData("hello");
//
// conn.sendData("hello");  // COMPILE ERROR: wrong state!
// connected.sendData("x"); // COMPILE ERROR: not authenticated!
```

### Things to Remember

- Template metaprogramming can shift work from runtime to compile time, enabling earlier error detection and higher runtime performance.
- TMP can be used to generate custom code based on combinations of policy choices, and it can be used to avoid generating code inappropriate for particular types.
- Classic TMP uses recursive template instantiation for loops and template specialization for conditionals and base cases.
- `constexpr` functions (C++11/14/17/20) provide a more readable alternative to classic TMP for value computations, but TMP remains essential for type-level computation.
- Real-world applications of TMP include dimensional analysis, expression templates, compile-time interface checking, and static state machines.
- The trade-offs of TMP include longer compile times, harder-to-read code, and more difficult debugging -- use it when the benefits (correctness, performance) justify the costs.
