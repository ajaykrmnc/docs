# Item 1: View C++ as a Federation of Languages

## Visual Summary

```text
┌───────────────────────────────────────────────────────────────────────────┐
│               ITEM 1: VIEW C++ AS A FEDERATION OF LANGUAGES               │
├───────────────────────────────────────────────────────────────────────────┤
│ 1. Problem: treating C++ like one language makes rules feel               │
│ inconsistent.                                                             │
│ 2. C layer -> built-ins, pointers, macros: cheap values, manual           │
│ discipline.                                                               │
│ 3. OO layer -> classes and virtual dispatch: interfaces, invariants,      │
│ refs.                                                                     │
│ 4. Template layer -> type parameters: compile-time contracts and code     │
│ gen.                                                                      │
│ 5. STL layer -> containers + iterators + algorithms: value-like           │
│ conventions.                                                              │
│ 6. Meaning: first identify the sub-language, then choose the matching     │
│ rule.                                                                     │
└───────────────────────────────────────────────────────────────────────────┘
```

## Visual Deep Dive

```text
┌───────────────────────────────────────────────────────────────────────────┐
│                       RULES CHANGE BY SUB-LANGUAGE                        │
├───────────────────────────────────────────────────────────────────────────┤
│ If you think...                   | Better model...                       │
│ ----------------------------------+-------------------------------------  │
│ One C++ rule fits all             | C / OO / Template / STL               │
│ Macros feel normal                | Compiler-visible constructs           │
│ Copies always same cost           | Cost depends on abstraction           │
│ Runtime polymorphism only         | Runtime and compile-time polymorphis  │
└───────────────────────────────────────────────────────────────────────────┘
```

```text
┌───────────────────────────────────────────────────────────────────────────┐
│                         HOW TO READ ANY C++ IDIOM                         │
├───────────────────────────────────────────────────────────────────────────┤
│ See the code style                                                        │
│                                     ▼                                     │
│ Identify sub-language: C, OO, Template, or STL                            │
│                                     ▼                                     │
│ Apply that layer's performance and safety rules                           │
│                                     ▼                                     │
│ Avoid mixing rules blindly                                                │
└───────────────────────────────────────────────────────────────────────────┘
```

### Core Concept

C++ is not a single unified language — it is a **federation of four sub-languages**, each with its own 
conventions, idioms, and best practices. The rules for effective programming change depending on which 
sub-language you're working in.

### The Four Sub-Languages

#### 1. C — The Foundation
```cpp
// C-style programming: blocks, statements, preprocessor, built-in types,
// arrays, pointers, pass-by-value
void process_data(int* array, int size) {
  for (int i = 0; i < size; ++i) {
    array[i] *= 2;  // Direct pointer/array manipulation
  }
}

// Preprocessor macros (C heritage)
#define MAX(a, b) ((a) > (b) ? (a) : (b))
// Pitfall: macro arguments evaluated multiple times
int x = 5, y = 3;
int result = MAX(++x, y);  // x incremented TWICE! Undefined behavior territory
```

#### 2. Object-Oriented C++
```cpp
// Classes, encapsulation, inheritance, polymorphism, virtual functions
class Shape {
public:
  virtual ~Shape() = default;
  virtual double area() const = 0;
  virtual void draw() const = 0;

protected:
  std::string color_;
};

class Circle : public Shape {
public:
  explicit Circle(double radius) : radius_(radius) {}

  double area() const override {
    return M_PI * radius_ * radius_;
  }

  void draw() const override {
    std::cout << "Drawing circle with radius " << radius_ << "\n";
  }

private:
  double radius_;
};

// Polymorphic usage
void render(const Shape& shape) {
  shape.draw();  // Virtual dispatch — runtime polymorphism
  std::cout << "Area: " << shape.area() << "\n";
}
```

#### 3. Template C++
```cpp
// Generic programming and template metaprogramming
template<typename T>
class Stack {
public:
  void push(const T& value) {
    data_.push_back(value);
  }

  T pop() {
    if (data_.empty()) throw std::runtime_error("Stack empty");
    T top = data_.back();
    data_.pop_back();
    return top;
  }

  bool empty() const { return data_.empty(); }

private:
  std::vector<T> data_;
};

// Template metaprogramming — compile-time computation
template<unsigned N>
struct Factorial {
  static constexpr unsigned value = N * Factorial<N - 1>::value;
};

template<>
struct Factorial<0> {
  static constexpr unsigned value = 1;
};

// Factorial<5>::value == 120, computed at COMPILE TIME
static_assert(Factorial<5>::value == 120, "5! should be 120");
```

#### 4. The STL
```cpp
// Containers, iterators, algorithms, function objects
#include <vector>
#include <algorithm>
#include <numeric>
#include <functional>

void stl_example() {
  std::vector<int> nums = {5, 3, 1, 4, 2};

  // Algorithm + iterator paradigm
  std::sort(nums.begin(), nums.end());

  // Function objects
  auto sum = std::accumulate(nums.begin(), nums.end(), 0);

  // Lambda as function object
  auto count_even = std::count_if(nums.begin(), nums.end(),
                                  [](int n) { return n % 2 == 0; });

  // STL convention: pass by value for iterators and function objects
  // (they are designed to be cheap to copy)
}
```

### Why This Matters: Rules Change by Sub-Language

```cpp
// RULE: Pass-by-value vs. pass-by-reference depends on the sub-language

// C sub-language: pass by value for built-in types
void increment(int x) { /* efficient */ }

// OO C++: pass by reference-to-const for user-defined types
void process(const Widget& w) { /* avoids expensive copy */ }

// Template C++: depends on the type parameter
template<typename T>
void handle(const T& t) { /* safe default */ }

// STL: pass iterators and function objects by value
std::for_each(v.begin(), v.end(), MyFunctor());
```

### Things to Remember
- C++ rules vary depending on which part of C++ you're using
- Pass-by-value is fine for built-in types and STL iterators/function objects
- Pass-by-reference-to-const is preferred for user-defined types
- For template code, the right approach depends on the template parameter

---
