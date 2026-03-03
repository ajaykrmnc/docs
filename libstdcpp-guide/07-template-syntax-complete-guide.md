# C++ Templates: Complete Syntax Guide

## Table of Contents
1. [Template Basics](#template-basics)
2. [Function Templates](#function-templates)
3. [Class Templates](#class-templates)
4. [Template Specialization](#template-specialization)
5. [Variadic Templates](#variadic-templates)
6. [Template Template Parameters](#template-template-parameters)
7. [SFINAE and enable_if](#sfinae-and-enable_if)
8. [Concepts (C++20)](#concepts-c20)
9. [Advanced Template Techniques](#advanced-template-techniques)
10. [Template Metaprogramming](#template-metaprogramming)

---

## Template Basics

### What Are Templates?

Templates allow you to write generic code that works with any data type. They are a compile-time feature - the 
compiler generates specific code for each type you use.

```cpp
// Without templates - need separate functions
int max_int(int a, int b) { return a > b ? a : b; }
double max_double(double a, double b) { return a > b ? a : b; }
string max_string(string a, string b) { return a > b ? a : b; }

// With templates - one function for all types
template<typename T>
T max_value(T a, T b) {
  return a > b ? a : b;
}

// Usage
int i = max_value(10, 20);           // T = int
double d = max_value(3.14, 2.71);    // T = double
string s = max_value("hello", "world"); // T = string
```

### Template Syntax

```cpp
// Using 'typename' keyword
template<typename T>
void function(T param) { }

// Using 'class' keyword (equivalent to typename)
template<class T>
void function(T param) { }

// Multiple template parameters
template<typename T, typename U>
void function(T param1, U param2) { }

// Non-type template parameters
template<typename T, int N>
void function(T (&array)[N]) { }

// Default template arguments
template<typename T = int>
void function(T param) { }
```

### Template Parameter Naming Conventions

```cpp
// Common conventions
template<typename T>        // Generic type
template<typename Key>      // Key type
template<typename Value>    // Value type
template<typename Iter>     // Iterator type
template<typename Func>     // Function/functor type
template<typename Alloc>    // Allocator type

// In libstdc++
template<typename _Tp>      // Leading underscore (reserved)
template<typename _Key, typename _Value>
```

---

## Function Templates

### Basic Function Template

```cpp
template<typename T>
T add(T a, T b) {
  return a + b;
}

// Usage
int i = add(5, 10);              // T = int
double d = add(3.14, 2.71);      // T = double
string s = add("Hello", "World"); // T = const char* (may not work as expected)
```

### Explicit Template Arguments

```cpp
template<typename T>
T convert(int value) {
  return static_cast<T>(value);
}

// Explicit specification
double d = convert<double>(42);
float f = convert<float>(42);
```

### Multiple Template Parameters

```cpp
template<typename T, typename U>
auto add(T a, U b) -> decltype(a + b) {
  return a + b;
}

// C++14: auto return type deduction
template<typename T, typename U>
auto add(T a, U b) {
  return a + b;
}

// Usage
auto result = add(5, 3.14);  // T = int, U = double, result = double
```

### Template Overloading

```cpp
// Generic version
template<typename T>
void print(T value) {
  cout << "Generic: " << value << '\n';
}

// Specialized for pointers
template<typename T>
void print(T* ptr) {
  cout << "Pointer: " << *ptr << '\n';
}

// Non-template version (highest priority)
void print(int value) {
  cout << "Int: " << value << '\n';
}

// Usage
int x = 42;
print(x);      // Calls non-template version
print(3.14);   // Calls generic template
print(&x);     // Calls pointer template
```

### Template Argument Deduction

```cpp
template<typename T>
void func(T param) { }

// Deduction rules
int x = 42;
const int cx = x;
const int& rx = x;

func(x);   // T = int, param = int
func(cx);  // T = int, param = int (const removed)
func(rx);  // T = int, param = int (const and & removed)

// By reference
template<typename T>
void func_ref(T& param) { }

func_ref(x);   // T = int, param = int&
func_ref(cx);  // T = const int, param = const int&
func_ref(rx);  // T = const int, param = const int&

// Universal reference (forwarding reference)
template<typename T>
void func_forward(T&& param) { }

func_forward(x);   // T = int&, param = int&
func_forward(42);  // T = int, param = int&&
```

### Trailing Return Type

```cpp
// C++11 style
template<typename T, typename U>
auto add(T a, U b) -> decltype(a + b) {
  return a + b;
}

// C++14 style (simpler)
template<typename T, typename U>
auto add(T a, U b) {
  return a + b;
}

// C++20 style (with concepts)
template<typename T, typename U>
requires requires(T a, U b) { a + b; }
auto add(T a, U b) {
  return a + b;
}
```

### constexpr Templates

```cpp
template<typename T>
constexpr T square(T x) {
  return x * x;
}

// Can be used at compile time
constexpr int result = square(5);  // Computed at compile time
static_assert(square(5) == 25);

// Or at runtime
int x = 10;
int runtime_result = square(x);    // Computed at runtime
```

---

## Class Templates

### Basic Class Template

```cpp
template<typename T>
class Container {
private:
  T value;
    
public:
  Container(T val) : value(val) { }
    
  T get() const { return value; }
  void set(T val) { value = val; }
    
  void print() const {
    cout << "Value: " << value << '\n';
  }
};

// Usage
Container<int> c1(42);
Container<string> c2("Hello");
c1.print();  // Value: 42
c2.print();  // Value: Hello
```

### Member Function Definitions Outside Class

```cpp
template<typename T>
class Container {
private:
  T value;
    
public:
  Container(T val);
  T get() const;
  void set(T val);
};

// Definition outside class
template<typename T>
Container<T>::Container(T val) : value(val) { }

template<typename T>
T Container<T>::get() const {
  return value;
}

template<typename T>
void Container<T>::set(T val) {
  value = val;
}
```

### Multiple Template Parameters

```cpp
template<typename Key, typename Value>
class KeyValuePair {
private:
  Key key;
  Value value;
    
public:
  KeyValuePair(Key k, Value v) : key(k), value(v) { }
    
  Key getKey() const { return key; }
  Value getValue() const { return value; }
};

// Usage
KeyValuePair<string, int> pair("age", 25);
cout << pair.getKey() << ": " << pair.getValue() << '\n';
```

### Non-Type Template Parameters

```cpp
// Array with compile-time size
template<typename T, int Size>
class Array {
private:
  T data[Size];
    
public:
  int size() const { return Size; }
    
  T& operator[](int index) {
    return data[index];
  }
    
  const T& operator[](int index) const {
    return data[index];
  }
};

// Usage
Array<int, 10> arr;
arr[0] = 42;
cout << "Size: " << arr.size() << '\n';  // Size: 10

// Different sizes are different types
Array<int, 10> arr1;
Array<int, 20> arr2;  // Different type from arr1
```

### Default Template Arguments

```cpp
template<typename T = int, int Size = 10>
class Array {
  T data[Size];
public:
  int size() const { return Size; }
};

// Usage
Array<> arr1;              // T = int, Size = 10
Array<double> arr2;        // T = double, Size = 10
Array<char, 20> arr3;      // T = char, Size = 20
```

### Static Members in Templates

```cpp
template<typename T>
class Counter {
private:
  static int count;
    
public:
  Counter() { ++count; }
  ~Counter() { --count; }
    
  static int getCount() { return count; }
};

// Definition of static member
template<typename T>
int Counter<T>::count = 0;

// Usage
Counter<int> c1, c2, c3;
cout << Counter<int>::getCount() << '\n';  // 3

Counter<double> d1;
cout << Counter<double>::getCount() << '\n';  // 1 (separate counter)
```

### Friend Functions in Templates

```cpp
template<typename T>
class Container {
private:
  T value;
    
public:
  Container(T val) : value(val) { }
    
  // Friend function template
  template<typename U>
  friend ostream& operator<<(ostream& os, const Container<U>& c);
};

// Definition
template<typename T>
ostream& operator<<(ostream& os, const Container<T>& c) {
  os << c.value;
  return os;
}

// Usage
Container<int> c(42);
cout << c << '\n';  // 42
```

---

## Template Specialization

### Full Specialization

```cpp
// Primary template
template<typename T>
class Printer {
public:
  void print(T value) {
    cout << "Generic: " << value << '\n';
  }
};

// Full specialization for bool
template<>
class Printer<bool> {
public:
  void print(bool value) {
    cout << "Bool: " << (value ? "true" : "false") << '\n';
  }
};

// Full specialization for char*
template<>
class Printer<char*> {
public:
  void print(char* value) {
    cout << "C-string: " << value << '\n';
  }
};

// Usage
Printer<int> p1;
p1.print(42);        // Generic: 42

Printer<bool> p2;
p2.print(true);      // Bool: true

Printer<char*> p3;
char str[] = "Hello";
p3.print(str);       // C-string: Hello
```

### Partial Specialization

```cpp
// Primary template
template<typename T, typename U>
class Pair {
public:
  void print() {
    cout << "Generic pair\n";
  }
};

// Partial specialization: both types are the same
template<typename T>
class Pair<T, T> {
public:
  void print() {
    cout << "Same type pair\n";
  }
};

// Partial specialization: second type is int
template<typename T>
class Pair<T, int> {
public:
  void print() {
    cout << "Second is int\n";
  }
};

// Partial specialization: both are pointers
template<typename T, typename U>
class Pair<T*, U*> {
public:
  void print() {
    cout << "Pointer pair\n";
  }
};

// Usage
Pair<double, string> p1;
p1.print();  // Generic pair

Pair<int, int> p2;
p2.print();  // Same type pair

Pair<double, int> p3;
p3.print();  // Second is int

Pair<int*, double*> p4;
p4.print();  // Pointer pair
```

### Function Template Specialization

```cpp
// Primary template
template<typename T>
void print(T value) {
  cout << "Generic: " << value << '\n';
}

// Full specialization
template<>
void print<bool>(bool value) {
  cout << "Bool: " << (value ? "true" : "false") << '\n';
}

// Note: Function templates cannot be partially specialized
// Use overloading instead

// Overload for pointers
template<typename T>
void print(T* ptr) {
  cout << "Pointer: " << *ptr << '\n';
}

// Usage
print(42);       // Generic: 42
print(true);     // Bool: true
int x = 10;
print(&x);       // Pointer: 10
```

---

## Variadic Templates

### Basic Variadic Template

```cpp
// Base case (no arguments)
void print() {
  cout << '\n';
}

// Recursive case
template<typename T, typename... Args>
void print(T first, Args... rest) {
  cout << first << ' ';
  print(rest...);  // Recursive call
}

// Usage
print(1, 2, 3, 4, 5);           // 1 2 3 4 5
print("Hello", 42, 3.14, 'x');  // Hello 42 3.14 x
```

### sizeof... Operator

```cpp
template<typename... Args>
void printCount(Args... args) {
  cout << "Number of arguments: " << sizeof...(Args) << '\n';
  cout << "Number of arguments: " << sizeof...(args) << '\n';
}

// Usage
printCount(1, 2, 3);           // 3
printCount("a", "b", "c", "d"); // 4
```

### Parameter Pack Expansion

```cpp
// Expand in function call
template<typename... Args>
void callFunc(Args... args) {
  someFunction(args...);  // Expands to: someFunction(arg1, arg2, arg3, ...)
}

// Expand with transformation
template<typename... Args>
void printDoubled(Args... args) {
  print((args * 2)...);  // Expands to: print(arg1*2, arg2*2, arg3*2, ...)
}

// Expand in initializer list
template<typename... Args>
vector<int> makeVector(Args... args) {
  return {args...};  // Expands to: {arg1, arg2, arg3, ...}
}
```

### Fold Expressions (C++17)

```cpp
// Unary left fold: (... op pack)
template<typename... Args>
auto sum(Args... args) {
  return (... + args);  // ((arg1 + arg2) + arg3) + ...
}

// Unary right fold: (pack op ...)
template<typename... Args>
auto sum_right(Args... args) {
  return (args + ...);  // arg1 + (arg2 + (arg3 + ...))
}

// Binary left fold: (init op ... op pack)
template<typename... Args>
auto sum_with_init(Args... args) {
  return (0 + ... + args);  // (((0 + arg1) + arg2) + arg3) + ...
}

// Usage
cout << sum(1, 2, 3, 4, 5) << '\n';  // 15

// Logical operations
template<typename... Args>
bool all(Args... args) {
  return (... && args);  // arg1 && arg2 && arg3 && ...
}

template<typename... Args>
bool any(Args... args) {
  return (... || args);  // arg1 || arg2 || arg3 || ...
}

// Print with fold
template<typename... Args>
void print(Args... args) {
  ((cout << args << ' '), ...);  // Uses comma operator
  cout << '\n';
}
```

### Variadic Class Templates

```cpp
// Tuple-like class
template<typename... Types>
class Tuple;

// Base case: empty tuple
template<>
class Tuple<> { };

// Recursive case
template<typename Head, typename... Tail>
class Tuple<Head, Tail...> : private Tuple<Tail...> {
  Head value;
    
public:
  Tuple(Head h, Tail... t) : Tuple<Tail...>(t...), value(h) { }
    
  Head& getHead() { return value; }
  Tuple<Tail...>& getTail() { return *this; }
};

// Usage
Tuple<int, double, string> t(42, 3.14, "Hello");
```

### Perfect Forwarding with Variadic Templates

```cpp
template<typename... Args>
void wrapper(Args&&... args) {
  // Forward all arguments to another function
  actualFunction(std::forward<Args>(args)...);
}

// Example: make_unique implementation
template<typename T, typename... Args>
unique_ptr<T> make_unique(Args&&... args) {
  return unique_ptr<T>(new T(std::forward<Args>(args)...));
}

// Usage
auto ptr = make_unique<vector<int>>(10, 42);  // vector with 10 elements = 42
```

---

## Template Template Parameters

### Basic Template Template Parameter

```cpp
// Template that takes another template as parameter
template<typename T, template<typename> class Container>
class Stack {
private:
  Container<T> data;
    
public:
  void push(const T& value) {
    data.push_back(value);
  }
    
  T pop() {
    T value = data.back();
    data.pop_back();
    return value;
  }
    
  bool empty() const {
    return data.empty();
  }
};

// Usage
Stack<int, vector> intStack;
Stack<string, deque> stringStack;
```

### Template Template with Multiple Parameters

```cpp
// Container template with allocator
template<typename T, template<typename, typename> class Container,
typename Allocator = allocator<T>>
class Wrapper {
private:
  Container<T, Allocator> data;
    
public:
  void add(const T& value) {
    data.push_back(value);
  }
};

// Usage
Wrapper<int, vector> w1;
Wrapper<string, deque> w2;
```

### C++17 Template Template Parameter Simplification

```cpp
// C++17: Can use typename instead of class
template<typename T, template<typename...> typename Container>
class Stack {
  Container<T> data;
public:
  // ...
};

// Works with templates that have default parameters
Stack<int, vector> s;  // vector has default allocator parameter
```

---

## SFINAE and enable_if

### SFINAE (Substitution Failure Is Not An Error)

```cpp
// Function enabled only for integral types
template<typename T>
typename enable_if<is_integral<T>::value, T>::type
process(T value) {
  return value * 2;
}

// Function enabled only for floating point types
template<typename T>
typename enable_if<is_floating_point<T>::value, T>::type
process(T value) {
  return value * 1.5;
}

// Usage
cout << process(10) << '\n';      // 20 (integral)
cout << process(3.14) << '\n';    // 4.71 (floating point)
```

### enable_if in Template Parameters

```cpp
// C++11 style
template<typename T, typename = typename enable_if<is_integral<T>::value>::type>
void func(T value) {
  cout << "Integral: " << value << '\n';
}

// C++14 style (using enable_if_t)
template<typename T, typename = enable_if_t<is_integral<T>::value>>
void func(T value) {
  cout << "Integral: " << value << '\n';
}

// Alternative: in return type
template<typename T>
enable_if_t<is_integral<T>::value, void>
func(T value) {
  cout << "Integral: " << value << '\n';
}
```

### Multiple Constraints

```cpp
// Require integral and not bool
template<typename T>
enable_if_t<is_integral<T>::value && !is_same<T, bool>::value, void>
process(T value) {
  cout << "Integral (not bool): " << value << '\n';
}

// Require arithmetic (integral or floating point)
template<typename T>
enable_if_t<is_arithmetic<T>::value, void>
process(T value) {
  cout << "Arithmetic: " << value << '\n';
}
```

### SFINAE with decltype

```cpp
// Check if type has begin() method
template<typename T>
auto hasBegin(T& t) -> decltype(t.begin(), void()) {
  cout << "Has begin()\n";
}

// Fallback
void hasBegin(...) {
  cout << "No begin()\n";
}

// Usage
vector<int> v;
hasBegin(v);   // Has begin()
hasBegin(42);  // No begin()
```

### Detection Idiom (C++17)

```cpp
#include <type_traits>

// Detect if type has size() method
template<typename T, typename = void>
struct has_size : false_type { };

template<typename T>
struct has_size<T, void_t<decltype(declval<T>().size())>> : true_type { };

// Helper variable template
template<typename T>
inline constexpr bool has_size_v = has_size<T>::value;

// Usage
static_assert(has_size_v<vector<int>>);
static_assert(!has_size_v<int>);
```

---

## Concepts (C++20)

### Basic Concepts

```cpp
#include <concepts>

// Define a concept
template<typename T>
concept Integral = std::is_integral_v<T>;

// Use concept in function
template<Integral T>
T add(T a, T b) {
  return a + b;
}

// Alternative syntax
template<typename T>
requires Integral<T>
T add(T a, T b) {
  return a + b;
}

// Trailing requires clause
template<typename T>
T add(T a, T b) requires Integral<T> {
  return a + b;
}

// Usage
add(5, 10);      // OK
// add(3.14, 2.71); // Error: doesn't satisfy Integral
```

### Standard Concepts

```cpp
#include <concepts>

// Arithmetic types
template<std::integral T>
void func1(T value) { }

template<std::floating_point T>
void func2(T value) { }

template<std::signed_integral T>
void func3(T value) { }

template<std::unsigned_integral T>
void func4(T value) { }

// Comparison concepts
template<std::equality_comparable T>
void func5(T value) { }

template<std::totally_ordered T>
void func6(T value) { }

// Iterator concepts
template<std::input_iterator Iter>
void func7(Iter first, Iter last) { }

template<std::random_access_iterator Iter>
void func8(Iter first, Iter last) { }

// Range concepts
template<std::ranges::range R>
void func9(R&& range) { }
```

### Custom Concepts

```cpp
// Simple concept
template<typename T>
concept Addable = requires(T a, T b) {
a + b;  // Must support addition
};

// Concept with type requirements
template<typename T>
concept Container = requires(T t) {
typename T::value_type;
typename T::iterator;
{ t.begin() } -> std::same_as<typename T::iterator>;
{ t.end() } -> std::same_as<typename T::iterator>;
{ t.size() } -> std::convertible_to<std::size_t>;
};

// Concept with multiple requirements
template<typename T>
concept Numeric = requires(T a, T b) {
{ a + b } -> std::convertible_to<T>;
{ a - b } -> std::convertible_to<T>;
{ a * b } -> std::convertible_to<T>;
{ a / b } -> std::convertible_to<T>;
};

// Usage
template<Numeric T>
T average(T a, T b) {
  return (a + b) / 2;
}
```

### Concept Composition

```cpp
// Combine concepts with &&
template<typename T>
concept SignedIntegral = std::integral<T> && std::signed_integral<T>;

// Combine concepts with ||
template<typename T>
concept Number = std::integral<T> || std::floating_point<T>;

// Negate concept with !
template<typename T>
concept NotPointer = !std::is_pointer_v<T>;

// Usage
template<SignedIntegral T>
void func(T value) { }
```

### Requires Expressions

```cpp
// Simple requirement
template<typename T>
concept HasSize = requires(T t) {
t.size();  // Must have size() method
};

// Type requirement
template<typename T>
concept HasValueType = requires {
typename T::value_type;  // Must have value_type typedef
};

// Compound requirement
template<typename T>
concept Comparable = requires(T a, T b) {
{ a < b } -> std::convertible_to<bool>;
{ a > b } -> std::convertible_to<bool>;
{ a == b } -> std::convertible_to<bool>;
};

// Nested requirement
template<typename T>
concept Sortable = requires(T t) {
requires std::random_access_iterator<typename T::iterator>;
{ t.begin() } -> std::same_as<typename T::iterator>;
{ t.end() } -> std::same_as<typename T::iterator>;
};
```

### Concept Overloading

```cpp
template<typename T>
concept SmallType = sizeof(T) <= 4;

template<typename T>
concept LargeType = sizeof(T) > 4;

// Different implementations based on size
template<SmallType T>
void process(T value) {
  cout << "Small type: " << value << '\n';
}

template<LargeType T>
void process(T value) {
  cout << "Large type: " << value << '\n';
}

// Usage
process(42);           // Small type
process(3.14159265);   // Large type (double is 8 bytes)
```

---

## Advanced Template Techniques

### CRTP (Curiously Recurring Template Pattern)

```cpp
// Base class template
template<typename Derived>
class Base {
public:
  void interface() {
    // Call derived class method
    static_cast<Derived*>(this)->implementation();
  }
    
  void commonMethod() {
    cout << "Common functionality\n";
  }
};

// Derived class
class Derived : public Base<Derived> {
public:
  void implementation() {
    cout << "Derived implementation\n";
  }
};

// Usage
Derived d;
d.interface();      // Calls Derived::implementation()
d.commonMethod();   // Calls Base::commonMethod()
```

### Expression Templates

```cpp
// Lazy evaluation for vector operations
template<typename E>
class VecExpression {
public:
  double operator[](size_t i) const {
    return static_cast<const E&>(*this)[i];
  }
    
  size_t size() const {
    return static_cast<const E&>(*this).size();
  }
};

// Actual vector
class Vec : public VecExpression<Vec> {
  vector<double> data;
    
public:
  Vec(size_t n) : data(n) { }
    
  double operator[](size_t i) const { return data[i]; }
  double& operator[](size_t i) { return data[i]; }
  size_t size() const { return data.size(); }
};

// Addition expression
template<typename E1, typename E2>
class VecSum : public VecExpression<VecSum<E1, E2>> {
  const E1& u;
  const E2& v;
    
public:
  VecSum(const E1& u, const E2& v) : u(u), v(v) { }
    
  double operator[](size_t i) const {
    return u[i] + v[i];  // Lazy evaluation
  }
    
  size_t size() const { return u.size(); }
};

// Operator overload
template<typename E1, typename E2>
VecSum<E1, E2> operator+(const VecExpression<E1>& u,
                         const VecExpression<E2>& v) {
  return VecSum<E1, E2>(static_cast<const E1&>(u),
                        static_cast<const E2&>(v));
}

// Usage: a + b + c creates expression tree, evaluated on access
Vec a(1000), b(1000), c(1000);
auto result = a + b + c;  // No temporaries created
double val = result[0];   // Evaluated here
```

### Type Traits Implementation

```cpp
// is_pointer implementation
template<typename T>
struct is_pointer : false_type { };

template<typename T>
struct is_pointer<T*> : true_type { };

// is_const implementation
template<typename T>
struct is_const : false_type { };

template<typename T>
struct is_const<const T> : true_type { };

// remove_const implementation
template<typename T>
struct remove_const {
  using type = T;
};

template<typename T>
struct remove_const<const T> {
  using type = T;
};

// conditional implementation
template<bool B, typename T, typename F>
struct conditional {
  using type = T;
};

template<typename T, typename F>
struct conditional<false, T, F> {
  using type = F;
};

// Usage
using T1 = conditional<true, int, double>::type;   // int
using T2 = conditional<false, int, double>::type;  // double
```

### Tag Dispatching

```cpp
// Iterator category tags
struct input_iterator_tag { };
struct forward_iterator_tag : input_iterator_tag { };
struct bidirectional_iterator_tag : forward_iterator_tag { };
struct random_access_iterator_tag : bidirectional_iterator_tag { };

// Generic advance function
template<typename Iter, typename Distance>
void advance(Iter& it, Distance n) {
  advance_impl(it, n, typename iterator_traits<Iter>::iterator_category());
}

// Implementation for input iterators
template<typename Iter, typename Distance>
void advance_impl(Iter& it, Distance n, input_iterator_tag) {
  while (n--) ++it;  // O(n)
}

// Implementation for random access iterators
template<typename Iter, typename Distance>
void advance_impl(Iter& it, Distance n, random_access_iterator_tag) {
  it += n;  // O(1)
}
```

---

## Template Metaprogramming

### Compile-Time Computation

```cpp
// Factorial at compile time
template<int N>
struct Factorial {
  static constexpr int value = N * Factorial<N - 1>::value;
};

template<>
struct Factorial<0> {
  static constexpr int value = 1;
};

// Usage
constexpr int fact5 = Factorial<5>::value;  // 120
static_assert(Factorial<5>::value == 120);

// C++14: constexpr function (simpler)
constexpr int factorial(int n) {
  return n <= 1 ? 1 : n * factorial(n - 1);
}

constexpr int fact5_v2 = factorial(5);
```

### Type Lists

```cpp
// Type list
template<typename... Types>
struct TypeList { };

// Get size of type list
template<typename List>
struct Length;

template<typename... Types>
struct Length<TypeList<Types...>> {
  static constexpr size_t value = sizeof...(Types);
};

// Get type at index
template<size_t Index, typename List>
struct TypeAt;

template<typename Head, typename... Tail>
struct TypeAt<0, TypeList<Head, Tail...>> {
  using type = Head;
};

template<size_t Index, typename Head, typename... Tail>
struct TypeAt<Index, TypeList<Head, Tail...>> {
  using type = typename TypeAt<Index - 1, TypeList<Tail...>>::type;
};

// Usage
using MyTypes = TypeList<int, double, string>;
static_assert(Length<MyTypes>::value == 3);
using FirstType = TypeAt<0, MyTypes>::type;  // int
using SecondType = TypeAt<1, MyTypes>::type; // double
```

### Compile-Time If (C++17)

```cpp
template<typename T>
auto getValue(T t) {
  if constexpr (is_pointer_v<T>) {
    return *t;  // Dereference if pointer
  } else {
    return t;   // Return as-is otherwise
  }
}

// Usage
int x = 42;
int* ptr = &x;
cout << getValue(x) << '\n';    // 42
cout << getValue(ptr) << '\n';  // 42
```

### Template Recursion

```cpp
// Print tuple elements
template<size_t Index = 0, typename... Types>
void printTuple(const tuple<Types...>& t) {
  if constexpr (Index < sizeof...(Types)) {
    cout << get<Index>(t) << ' ';
    printTuple<Index + 1>(t);
  }
}

// Usage
tuple<int, double, string> t(42, 3.14, "Hello");
printTuple(t);  // 42 3.14 Hello
```

### Compile-Time String

```cpp
// C++20: Template parameter can be string literal
template<size_t N>
struct CompileTimeString {
  char data[N];
    
  constexpr CompileTimeString(const char (&str)[N]) {
    for (size_t i = 0; i < N; ++i) {
      data[i] = str[i];
    }
  }
};

// C++20: Non-type template parameter
template<CompileTimeString Str>
void printMessage() {
  cout << Str.data << '\n';
}

// Usage
printMessage<"Hello, World!">();
```

---

## Best Practices

### 1. Use Concepts (C++20) Over SFINAE

```cpp
// Old way (SFINAE)
template<typename T>
enable_if_t<is_integral_v<T>, void>
process(T value) { }

// New way (Concepts)
template<std::integral T>
void process(T value) { }
```

### 2. Prefer `typename` Over `class` for Type Parameters

```cpp
// Preferred
template<typename T>
void func(T param) { }

// Less clear (class suggests class types only)
template<class T>
void func(T param) { }
```

### 3. Use Alias Templates

```cpp
// Instead of typedef
template<typename T>
using Vec = vector<T>;

Vec<int> v;  // Clearer than vector<int>
```

### 4. Avoid Deep Template Nesting

```cpp
// Bad: hard to read
template<typename T>
using ComplexType = map<string, vector<pair<int, T>>>;

// Better: break it down
template<typename T>
using ValuePair = pair<int, T>;

template<typename T>
using ValueList = vector<ValuePair<T>>;

template<typename T>
using ComplexType = map<string, ValueList<T>>;
```

### 5. Document Template Requirements

```cpp
/**
 * @brief Sorts a container
 * @tparam Container Must have begin(), end(), and support random access
 * @tparam Compare Must be callable with two Container::value_type arguments
 */
template<typename Container, typename Compare>
void sort(Container& c, Compare comp) {
  std::sort(c.begin(), c.end(), comp);
}
```

---

## Common Template Errors and Solutions

### Error 1: Missing typename

```cpp
// Error
template<typename T>
void func() {
  T::value_type x;  // Error: need typename
}

// Fix
template<typename T>
void func() {
  typename T::value_type x;  // OK
}
```

### Error 2: Missing template Keyword

```cpp
// Error
template<typename T>
void func(T& t) {
  t.template_method<int>();  // Error: need template keyword
}

// Fix
template<typename T>
void func(T& t) {
  t.template template_method<int>();  // OK
}
```

### Error 3: Template Definition in .cpp File

```cpp
// header.h
template<typename T>
class MyClass {
  void func();
};

// source.cpp - WRONG!
template<typename T>
void MyClass<T>::func() { }  // Won't link

// Fix: Define in header or explicitly instantiate
template<typename T>
void MyClass<T>::func() { }  // In header

// Or explicit instantiation in .cpp
template class MyClass<int>;
template class MyClass<double>;
```

---

## Summary

This guide covered:
- Template basics and syntax
- Function and class templates
- Template specialization
- Variadic templates and fold expressions
- Template template parameters
- SFINAE and enable_if
- C++20 Concepts
- Advanced techniques (CRTP, expression templates)
- Template metaprogramming
- Best practices

**Templates are powerful but complex. Start simple and gradually explore advanced features!**

