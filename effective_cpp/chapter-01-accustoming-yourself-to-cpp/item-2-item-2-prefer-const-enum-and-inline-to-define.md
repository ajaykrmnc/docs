# Item 2: Prefer `const`, `enum`, and `inline` to `#define`

## Visual Summary

```text
┌───────────────────────────────────────────────────────────────────────────┐
│         ITEM 2: PREFER `CONST`, `ENUM`, AND `INLINE` TO `#DEFINE`         │
├───────────────────────────────────────────────────────────────────────────┤
│ 1. Macro enters preprocessor -> compiler sees only substituted text.      │
│ 2. Consequence -> no scope, weak type checking, poor debugger names.      │
│ 3. Constant value? -> use const or enum so compiler owns the symbol.      │
│ 4. Function-like macro? -> use inline/template function for one           │
│ evaluation.                                                               │
│ 5. Meaning: prefer language constructs because the compiler can protect   │
│ you.                                                                      │
└───────────────────────────────────────────────────────────────────────────┘
```

## Visual Deep Dive

```text
┌───────────────────────────────────────────────────────────────────────────┐
│                            MACRO FAILURE FLOW                             │
├───────────────────────────────────────────────────────────────────────────┤
│ #define is expanded before compilation                                    │
│                                     ▼                                     │
│ Compiler loses symbol name, scope, and type information                   │
│                                     ▼                                     │
│ Debugger/error messages point at substituted text                         │
│                                     ▼                                     │
│ Side effects may run more than once                                       │
└───────────────────────────────────────────────────────────────────────────┘
```

```text
┌───────────────────────────────────────────────────────────────────────────┐
│                              REPLACEMENT MAP                              │
├───────────────────────────────────────────────────────────────────────────┤
│ Old habit                         | Safer construct                       │
│ ----------------------------------+-------------------------------------  │
│ #define VALUE                     | const / constexpr                     │
│ #define F(x)                      | inline function/template              │
│ Magic integer in class            | enum or static const member           │
└───────────────────────────────────────────────────────────────────────────┘
```

### Core Concept

"Prefer the compiler to the preprocessor." `#define` operates before the compiler even sees your code, leading 
to confusing errors, no type safety, and no scope control.

### Problem: `#define` for Constants

```cpp
// BAD: Preprocessor macro
#define ASPECT_RATIO 1.653
// Problem 1: "ASPECT_RATIO" may never be seen by compiler — error messages
//            will refer to "1.653", making debugging confusing
// Problem 2: No type information
// Problem 3: No scope — pollutes entire translation unit

// GOOD: typed constant
const double AspectRatio = 1.653;
// - Appears in symbol table — better error messages and debugger support
// - Type-checked by the compiler
// - Respects scope rules
```

### Special Cases for Constants

#### Constant Pointers
```cpp
// For constant char* strings in headers, you need TWO consts
const char* const authorName = "Scott Meyers";
//  ^^^^^          ^^^^^
//  |              pointer itself is const
//  what pointer points to is const

// Better: use std::string
const std::string authorName("Scott Meyers");
```

#### Class-Specific Constants
```cpp
class GamePlayer {
private:
  // Declaration of a class-specific constant
  static const int NumTurns = 5;  // In-class initialization (integral types only)
  int scores[NumTurns];           // Use of the constant

  // For non-integral types or when you need an address:
  static const double FudgeFactor;  // Declaration only
};

// Definition in .cpp file (required if address is ever taken)
const int GamePlayer::NumTurns;  // Definition; no value given (already in declaration)
const double GamePlayer::FudgeFactor = 1.35;  // Definition with value
```

### The `enum` Hack

```cpp
class GamePlayer {
private:
  // When your compiler won't allow in-class initialization:
  enum { NumTurns = 5 };  // "the enum hack"
  int scores[NumTurns];   // Works fine

  // Advantages of enum hack:
  // 1. It's impossible to take the address of an enum (more like #define)
  // 2. No memory allocated for the enum value
  // 3. Pragmatic — widely used in template metaprogramming
};

// enum hack in template metaprogramming
template<typename T>
struct TypeTraits {
  enum { isPointer = 0 };
};

template<typename T>
struct TypeTraits<T*> {
  enum { isPointer = 1 };  // Specialization for pointer types
};
```

### Problem: `#define` for Function-Like Macros

```cpp
// BAD: macro "function"
#define CALL_WITH_MAX(a, b) f((a) > (b) ? (a) : (b))

// Despite all the parentheses, this is STILL broken:
int a = 5, b = 0;
CALL_WITH_MAX(++a, b);      // a incremented TWICE
CALL_WITH_MAX(++a, b + 10); // a incremented ONCE
// Behavior depends on what b is compared to! Nightmare.

// GOOD: inline template function
template<typename T>
inline void callWithMax(const T& a, const T& b) {
  f(a > b ? a : b);
  // - Type safe
  // - Predictable evaluation (arguments evaluated exactly once)
  // - Respects scope and access control
  // - Can be debugged with a debugger
}
```

### Comprehensive Example: Replacing All `#define` Patterns

```cpp
// ===== BEFORE: #define everywhere =====
#define PI 3.14159265358979
#define MAX_BUFFER_SIZE 1024
#define MIN(a, b) ((a) < (b) ? (a) : (b))
#define SQUARE(x) ((x) * (x))
#define DEBUG_LOG(msg) std::cout << __FILE__ << ":" << __LINE__ << " " << msg << "\n"

// ===== AFTER: Modern C++ =====
constexpr double Pi = 3.14159265358979;
constexpr int MaxBufferSize = 1024;

template<typename T>
inline const T& minOf(const T& a, const T& b) {
  return a < b ? a : b;
}

template<typename T>
inline T square(const T& x) {
  return x * x;
}

// For debug logging, consider a proper logging framework
// or at minimum an inline function:
inline void debugLog(const char* file, int line, const std::string& msg) {
  std::cout << file << ":" << line << " " << msg << "\n";
}
#define DEBUG_LOG(msg) debugLog(__FILE__, __LINE__, msg)
// ^-- One of the FEW legitimate uses of #define:
//     __FILE__ and __LINE__ MUST be macros to get caller context
```

### Things to Remember
- For simple constants, prefer `const` objects or `enum`s to `#define`s
- For function-like macros, prefer `inline` functions to `#define`s
- `#define` doesn't respect scope, lacks type safety, and produces confusing errors
- The enum hack is a useful technique for compile-time integer constants

---
