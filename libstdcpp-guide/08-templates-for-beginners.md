# C++ Templates: Simple Beginner's Guide

## Table of Contents
1. [Why No Semicolon After template?](#why-no-semicolon-after-template)
2. [What Are Templates? (The Simple Truth)](#what-are-templates-the-simple-truth)
3. [Your First Template](#your-first-template)
4. [Understanding T - It's NOT a Variable!](#understanding-t---its-not-a-variable)
5. [Function Templates Step by Step](#function-templates-step-by-step)
6. [Class Templates Step by Step](#class-templates-step-by-step)
7. [Common Beginner Mistakes](#common-beginner-mistakes)
8. [When to Use Templates](#when-to-use-templates)
9. [Practice Examples](#practice-examples)

---

## Why No Semicolon After template?

### The Confusion

You might wonder:
```cpp
template<typename T>  // ← Why no semicolon here?
T add(T a, T b) {
    return a + b;
}
```

### The Answer: It's NOT a Statement!

**`template<typename T>` is NOT a complete statement - it's a MODIFIER for the next thing!**

Think of it like other modifiers in C++:

```cpp
// These don't end with semicolon either:
static int x = 10;     // "static" modifies the variable
const double pi = 3.14; // "const" modifies the variable
inline void func() { }  // "inline" modifies the function

// Similarly:
template<typename T>    // "template<typename T>" modifies the function
T add(T a, T b) {
    return a + b;
}
```

### Visual Explanation

```cpp
// WRONG - semicolon makes it incomplete
template<typename T>;  // ❌ Modifier with nothing to modify!
T add(T a, T b) {      // ❌ What is T? Compiler doesn't know!
    return a + b;
}

// CORRECT - template modifies the function
template<typename T>   // ✅ This modifies the next declaration
T add(T a, T b) {      // ✅ This is what gets modified
    return a + b;
}
```

### Think of It as a Label

```cpp
template<typename T>  ← "Hey compiler, the next thing is a template!"
T add(T a, T b) {     ← "This is the thing that's a template"
    return a + b;
}
```

### Comparison with Other Languages

If you know other languages:

```python
# Python decorator (similar concept)
@decorator          # No semicolon - it modifies the next function
def function():
    pass
```

```java
// Java annotation (similar concept)
@Override          // No semicolon - it modifies the next method
public void method() {
}
```

### Where the Semicolon DOES Go

```cpp
// Function declaration - semicolon at the end
template<typename T>
T add(T a, T b);  // ← Semicolon HERE (after the declaration)

// Function definition - semicolon after the closing brace? NO!
template<typename T>
T add(T a, T b) {
    return a + b;
}  // ← No semicolon here (just like regular functions)

// Class declaration - semicolon after the class
template<typename T>
class Box {
    T value;
};  // ← Semicolon HERE (after the class)
```

### Complete Examples

```cpp
// Example 1: Template function declaration
template<typename T>
T max(T a, T b);  // Semicolon ends the declaration

// Example 2: Template function definition
template<typename T>
T max(T a, T b) {
    return (a > b) ? a : b;
}  // No semicolon (like regular functions)

// Example 3: Template class
template<typename T>
class Container {
    T value;
public:
    Container(T v) : value(v) {}
};  // Semicolon ends the class

// Example 4: Multiple templates in a row
template<typename T>
T add(T a, T b) { return a + b; }

template<typename T>  // Each template modifies its own function
T subtract(T a, T b) { return a - b; }

template<typename T>
T multiply(T a, T b) { return a * b; }
```

### The Rule

**`template<typename T>` is glued to the next declaration/definition. They are ONE unit!**

```cpp
┌─────────────────────────────────┐
│ template<typename T>            │  ← Part 1: Template declaration
│ T add(T a, T b) {               │  ← Part 2: Function definition
│     return a + b;                │
│ }                                │
└─────────────────────────────────┘
    This is ONE complete unit!
```

### What Happens If You Add a Semicolon?

```cpp
// If you write this:
template<typename T>;  // ❌ ERROR!
T add(T a, T b) {
    return a + b;
}

// Compiler sees:
// 1. A template declaration with nothing to declare (ERROR!)
// 2. A function using unknown type T (ERROR!)
```

### Summary

| Code | Semicolon? | Why? |
|------|-----------|------|
| `template<typename T>` | ❌ NO | It's a modifier, not a statement |
| `T add(T a, T b);` | ✅ YES | Function declaration ends with ; |
| `T add(T a, T b) { }` | ❌ NO | Function definition doesn't end with ; |
| `class Box { };` | ✅ YES | Class definition ends with ; |

---

## What Are Templates? (The Simple Truth)

### The Problem Templates Solve

Imagine you need to write a function to find the maximum of two numbers:

```cpp
// For integers
int max_int(int a, int b) {
    if (a > b)
        return a;
    else
        return b;
}

// For doubles
double max_double(double a, double b) {
    if (a > b)
        return a;
    else
        return b;
}

// For strings
string max_string(string a, string b) {
    if (a > b)
        return a;
    else
        return b;
}
```

**Problem:** Same logic, but we need to write it 3 times (or more)!

### The Template Solution

```cpp
template<typename T>
T max_value(T a, T b) {
    if (a > b)
        return a;
    else
        return b;
}

// Now use it with ANY type!
int i = max_value(10, 20);           // Works with int
double d = max_value(3.14, 2.71);    // Works with double
string s = max_value("hello", "world"); // Works with string
```

**Solution:** Write once, use with any type!

---

## Your First Template

### Step 1: Write a Normal Function First

Always start with a normal function:

```cpp
// Normal function for integers
int add(int a, int b) {
    return a + b;
}
```

### Step 2: Identify What Changes

What would change if we wanted this for `double`? Only the **type**!

```cpp
// For double
double add(double a, double b) {
    return a + b;
}
```

### Step 3: Replace the Type with T

```cpp
// Template version
template<typename T>
T add(T a, T b) {
    return a + b;
}
```

**That's it!** You've created a template!

### Step 4: Use It

```cpp
int main() {
    // Compiler creates add<int> automatically
    int result1 = add(5, 10);           // result1 = 15
    
    // Compiler creates add<double> automatically
    double result2 = add(3.14, 2.86);   // result2 = 6.0
    
    // You can also be explicit
    int result3 = add<int>(5, 10);
    
    cout << result1 << endl;  // 15
    cout << result2 << endl;  // 6.0
    
    return 0;
}
```

---

## Understanding T - It's NOT a Variable!

### ❌ WRONG: T is NOT a Variable

```cpp
template<typename T>
T add(T a, T b) {
    return a + b;
}

// You CANNOT do this:
T x = 10;  // ERROR! T is not a variable
T y = 20;  // ERROR! T is not a type you can use directly
```

### ✅ CORRECT: T is a Type Placeholder

Think of `T` like a blank space that gets filled in:

```cpp
template<typename T>
//              ↑
//              This is like saying "fill in the blank with a type"

T add(T a, T b) {
//↑   ↑    ↑
// These all get replaced with the SAME type
    return a + b;
}
```

### How the Compiler Sees It

When you write:
```cpp
int result = add(5, 10);
```

The compiler **generates** this code:
```cpp
int add(int a, int b) {  // T was replaced with int
    return a + b;
}
```

When you write:
```cpp
double result = add(3.14, 2.86);
```

The compiler **generates** this code:
```cpp
double add(double a, double b) {  // T was replaced with double
    return a + b;
}
```

### Visual Explanation

```
Template (Blueprint):
┌─────────────────────────┐
│ template<typename T>    │
│ T add(T a, T b) {       │
│     return a + b;       │
│ }                       │
└─────────────────────────┘
            │
            │ Compiler fills in T
            ↓
┌─────────────────────────┬─────────────────────────┐
│ int add(int a, int b) { │ double add(double a,    │
│     return a + b;       │            double b) {  │
│ }                       │     return a + b;       │
│                         │ }                       │
└─────────────────────────┴─────────────────────────┘
```

### Real-World Analogy

Think of a template like a **cookie cutter**:

- The cookie cutter (template) is the **shape**
- The dough (type) is what you **fill it with**
- You can make cookies with chocolate dough, vanilla dough, etc.
- But the cookie cutter itself is NOT a cookie!

Similarly:
- The template is the **pattern**
- `T` is the **placeholder** for the type
- You can use it with `int`, `double`, `string`, etc.
- But `T` itself is NOT a type you can use directly!

---

## Function Templates Step by Step

### Example 1: Simple Print Function

**Step 1: Normal function**
```cpp
void print(int value) {
    cout << "Value: " << value << endl;
}
```

**Step 2: Make it a template**
```cpp
template<typename T>
void print(T value) {
    cout << "Value: " << value << endl;
}
```

**Step 3: Use it**
```cpp
int main() {
    print(42);           // Prints: Value: 42
    print(3.14);         // Prints: Value: 3.14
    print("Hello");      // Prints: Value: Hello
    
    return 0;
}
```

### Example 2: Swap Function

**Step 1: Normal function**
```cpp
void swap(int& a, int& b) {
    int temp = a;
    a = b;
    b = temp;
}
```

**Step 2: Make it a template**
```cpp
template<typename T>
void swap(T& a, T& b) {
    T temp = a;  // T is used as a type here!
    a = b;
    b = temp;
}
```

**Step 3: Use it**
```cpp
int main() {
    int x = 10, y = 20;
    swap(x, y);
    cout << x << " " << y << endl;  // 20 10
    
    string s1 = "hello", s2 = "world";
    swap(s1, s2);
    cout << s1 << " " << s2 << endl;  // world hello
    
    return 0;
}
```

### Example 3: Array Minimum

**Step 1: Normal function**
```cpp
int findMin(int arr[], int size) {
    int min = arr[0];
    for (int i = 1; i < size; i++) {
        if (arr[i] < min) {
            min = arr[i];
        }
    }
    return min;
}
```

**Step 2: Make it a template**
```cpp
template<typename T>
T findMin(T arr[], int size) {
    T min = arr[0];  // T is used as a type!
    for (int i = 1; i < size; i++) {
        if (arr[i] < min) {
            min = arr[i];
        }
    }
    return min;
}
```

**Step 3: Use it**
```cpp
int main() {
    int intArr[] = {5, 2, 8, 1, 9};
    cout << findMin(intArr, 5) << endl;  // 1
    
    double doubleArr[] = {5.5, 2.2, 8.8, 1.1};
    cout << findMin(doubleArr, 4) << endl;  // 1.1
    
    return 0;
}
```

### Example 4: Multiple Template Parameters

You can have more than one type placeholder!

```cpp
template<typename T, typename U>
void printPair(T first, U second) {
    cout << "First: " << first << ", Second: " << second << endl;
}

int main() {
    printPair(42, 3.14);           // T=int, U=double
    printPair("Age", 25);          // T=const char*, U=int
    printPair(true, "Success");    // T=bool, U=const char*
    
    return 0;
}
```

---

## Class Templates Step by Step

### Example 1: Simple Box Class

**Step 1: Normal class for integers**
```cpp
class IntBox {
private:
    int value;
    
public:
    IntBox(int v) : value(v) {}
    
    int getValue() {
        return value;
    }
    
    void setValue(int v) {
        value = v;
    }
};
```

**Step 2: Make it a template**
```cpp
template<typename T>
class Box {
private:
    T value;  // T is used as a type!
    
public:
    Box(T v) : value(v) {}
    
    T getValue() {  // T is the return type!
        return value;
    }
    
    void setValue(T v) {  // T is the parameter type!
        value = v;
    }
};
```

**Step 3: Use it**
```cpp
int main() {
    Box<int> intBox(42);
    cout << intBox.getValue() << endl;  // 42
    
    Box<double> doubleBox(3.14);
    cout << doubleBox.getValue() << endl;  // 3.14
    
    Box<string> stringBox("Hello");
    cout << stringBox.getValue() << endl;  // Hello
    
    return 0;
}
```

**Important:** With class templates, you MUST specify the type:
```cpp
Box<int> intBox(42);     // ✅ Correct
Box intBox(42);          // ❌ Error! (before C++17)
```

### Example 2: Pair Class

```cpp
template<typename T1, typename T2>
class Pair {
private:
    T1 first;
    T2 second;
    
public:
    Pair(T1 f, T2 s) : first(f), second(s) {}
    
    T1 getFirst() { return first; }
    T2 getSecond() { return second; }
    
    void print() {
        cout << "(" << first << ", " << second << ")" << endl;
    }
};

int main() {
    Pair<int, double> p1(10, 3.14);
    p1.print();  // (10, 3.14)
    
    Pair<string, int> p2("Age", 25);
    p2.print();  // (Age, 25)
    
    return 0;
}
```

### Example 3: Simple Array Class

```cpp
template<typename T>
class SimpleArray {
private:
    T* data;
    int size;
    
public:
    SimpleArray(int s) : size(s) {
        data = new T[size];
    }
    
    ~SimpleArray() {
        delete[] data;
    }
    
    T& operator[](int index) {
        return data[index];
    }
    
    int getSize() {
        return size;
    }
};

int main() {
    SimpleArray<int> intArray(5);
    intArray[0] = 10;
    intArray[1] = 20;
    cout << intArray[0] << endl;  // 10
    
    SimpleArray<string> stringArray(3);
    stringArray[0] = "Hello";
    stringArray[1] = "World";
    cout << stringArray[0] << endl;  // Hello
    
    return 0;
}
```

---

## Common Beginner Mistakes

### Mistake 1: Using T as a Variable

```cpp
❌ WRONG:
template<typename T>
void func() {
    T = 10;  // ERROR! T is not a variable!
}

✅ CORRECT:
template<typename T>
void func() {
    T value = 10;  // T is a type, value is a variable
}
```

### Mistake 2: Forgetting Template Syntax

```cpp
❌ WRONG:
T add(T a, T b) {  // Where does T come from?
    return a + b;
}

✅ CORRECT:
template<typename T>
T add(T a, T b) {
    return a + b;
}
```

### Mistake 3: Mixing Types

```cpp
template<typename T>
T add(T a, T b) {
    return a + b;
}

int main() {
    // This might cause issues:
    auto result = add(5, 3.14);  // 5 is int, 3.14 is double
    // Compiler doesn't know if T should be int or double!
    
    // Solution 1: Make them the same type
    auto result = add(5.0, 3.14);  // Both double
    
    // Solution 2: Use explicit type
    auto result = add<double>(5, 3.14);  // Force T = double
    
    return 0;
}
```

### Mistake 4: Forgetting <Type> for Classes

```cpp
template<typename T>
class Box {
    T value;
public:
    Box(T v) : value(v) {}
};

int main() {
    ❌ WRONG:
    Box myBox(42);  // Error! (before C++17)
    
    ✅ CORRECT:
    Box<int> myBox(42);
    
    return 0;
}
```

### Mistake 5: Template Definition in .cpp File

```cpp
❌ WRONG:
// header.h
template<typename T>
T add(T a, T b);

// source.cpp
template<typename T>
T add(T a, T b) {
    return a + b;
}
// This won't work! Linker error!

✅ CORRECT:
// header.h
template<typename T>
T add(T a, T b) {
    return a + b;
}
// Keep template definitions in header files!
```

---

## When to Use Templates

### ✅ Use Templates When:

1. **Same logic, different types**
```cpp
// Good use case
template<typename T>
T max(T a, T b) {
    return a > b ? a : b;
}
```

2. **Container classes**
```cpp
// Good use case
template<typename T>
class Stack {
    // Stack can hold any type
};
```

3. **Generic algorithms**
```cpp
// Good use case
template<typename T>
void sort(T arr[], int size) {
    // Sorting logic works for any comparable type
}
```

### ❌ Don't Use Templates When:

1. **Logic is type-specific**
```cpp
// Bad use case
template<typename T>
void processEmployee(T emp) {
    // If this only makes sense for Employee type,
    // don't use a template!
}

// Better:
void processEmployee(Employee emp) {
    // Clear and simple
}
```

2. **Only one type will ever be used**
```cpp
// Bad use case
template<typename T>
void printInt(T value) {
    // If you only ever use int, why template?
}

// Better:
void printInt(int value) {
    // Simple and clear
}
```

---

## Practice Examples

### Exercise 1: Absolute Value

Write a template function that returns the absolute value of a number.

**Solution:**
```cpp
template<typename T>
T absolute(T value) {
    if (value < 0)
        return -value;
    else
        return value;
}

int main() {
    cout << absolute(-5) << endl;      // 5
    cout << absolute(-3.14) << endl;   // 3.14
    cout << absolute(10) << endl;      // 10
    
    return 0;
}
```

### Exercise 2: Array Sum

Write a template function that sums all elements in an array.

**Solution:**
```cpp
template<typename T>
T arraySum(T arr[], int size) {
    T sum = 0;  // T is used as a type!
    for (int i = 0; i < size; i++) {
        sum += arr[i];
    }
    return sum;
}

int main() {
    int intArr[] = {1, 2, 3, 4, 5};
    cout << arraySum(intArr, 5) << endl;  // 15
    
    double doubleArr[] = {1.1, 2.2, 3.3};
    cout << arraySum(doubleArr, 3) << endl;  // 6.6
    
    return 0;
}
```

### Exercise 3: Triple Class

Create a template class that holds three values of the same type.

**Solution:**
```cpp
template<typename T>
class Triple {
private:
    T first, second, third;
    
public:
    Triple(T f, T s, T t) : first(f), second(s), third(t) {}
    
    T getFirst() { return first; }
    T getSecond() { return second; }
    T getThird() { return third; }
    
    T sum() {
        return first + second + third;
    }
    
    void print() {
        cout << "(" << first << ", " << second << ", " << third << ")" << endl;
    }
};

int main() {
    Triple<int> t1(1, 2, 3);
    t1.print();  // (1, 2, 3)
    cout << "Sum: " << t1.sum() << endl;  // Sum: 6
    
    Triple<double> t2(1.1, 2.2, 3.3);
    t2.print();  // (1.1, 2.2, 3.3)
    cout << "Sum: " << t2.sum() << endl;  // Sum: 6.6
    
    return 0;
}
```

### Exercise 4: Compare Function

Write a template function that compares two values and returns the larger one.

**Solution:**
```cpp
template<typename T>
T larger(T a, T b) {
    return (a > b) ? a : b;
}

int main() {
    cout << larger(10, 20) << endl;           // 20
    cout << larger(3.14, 2.71) << endl;       // 3.14
    cout << larger('a', 'z') << endl;         // z
    cout << larger("apple", "banana") << endl; // banana
    
    return 0;
}
```

### Exercise 5: Calculator Class

Create a template calculator class with basic operations.

**Solution:**
```cpp
template<typename T>
class Calculator {
public:
    T add(T a, T b) {
        return a + b;
    }
    
    T subtract(T a, T b) {
        return a - b;
    }
    
    T multiply(T a, T b) {
        return a * b;
    }
    
    T divide(T a, T b) {
        if (b == 0) {
            cout << "Error: Division by zero!" << endl;
            return 0;
        }
        return a / b;
    }
};

int main() {
    Calculator<int> intCalc;
    cout << intCalc.add(10, 5) << endl;      // 15
    cout << intCalc.subtract(10, 5) << endl; // 5
    cout << intCalc.multiply(10, 5) << endl; // 50
    cout << intCalc.divide(10, 5) << endl;   // 2
    
    Calculator<double> doubleCalc;
    cout << doubleCalc.add(10.5, 5.5) << endl;      // 16
    cout << doubleCalc.divide(10.0, 3.0) << endl;   // 3.33333
    
    return 0;
}
```

---

## Quick Reference Card

### Function Template Syntax
```cpp
template<typename T>
T functionName(T parameter) {
    // function body
    return something;
}
```

### Class Template Syntax
```cpp
template<typename T>
class ClassName {
private:
    T member;
public:
    ClassName(T param) : member(param) {}
    T getMember() { return member; }
};
```

### Using Function Templates
```cpp
// Automatic type deduction
result = functionName(value);

// Explicit type specification
result = functionName<int>(value);
```

### Using Class Templates
```cpp
// Must specify type
ClassName<int> object(value);
```

### Multiple Type Parameters
```cpp
template<typename T, typename U>
void function(T param1, U param2) {
    // body
}

template<typename T, typename U>
class ClassName {
    T member1;
    U member2;
};
```

---

## Key Takeaways

1. **T is NOT a variable** - it's a type placeholder
2. **Templates are blueprints** - compiler generates actual code
3. **Write normal code first** - then convert to template
4. **Function templates** - compiler can deduce type
5. **Class templates** - you must specify type (before C++17)
6. **Keep templates in headers** - don't put in .cpp files
7. **Use templates for generic code** - same logic, different types

---

## What's Next?

Once you're comfortable with basic templates, you can learn:
- Template specialization (custom behavior for specific types)
- Variadic templates (templates with variable number of parameters)
- SFINAE (advanced type checking)
- C++20 Concepts (cleaner way to constrain templates)

But master the basics first! Practice writing simple templates until they feel natural.

---

## Final Example: Putting It All Together

```cpp
#include <iostream>
#include <string>
using namespace std;

// Function template
template<typename T>
T max(T a, T b) {
    return (a > b) ? a : b;
}

// Class template
template<typename T>
class Container {
private:
    T value;
    
public:
    Container(T v) : value(v) {}
    
    T getValue() { return value; }
    void setValue(T v) { value = v; }
    
    void print() {
        cout << "Value: " << value << endl;
    }
};

int main() {
    // Using function template
    cout << "Max of 10 and 20: " << max(10, 20) << endl;
    cout << "Max of 3.14 and 2.71: " << max(3.14, 2.71) << endl;
    
    // Using class template
    Container<int> intContainer(42);
    intContainer.print();
    
    Container<string> stringContainer("Hello");
    stringContainer.print();
    
    return 0;
}
```

**Output:**
```
Max of 10 and 20: 20
Max of 3.14 and 2.71: 3.14
Value: 42
Value: Hello
```

---

**Remember: Templates are just a way to write code once and use it with many types. Start simple, practice, and gradually build your understanding!** 🚀

