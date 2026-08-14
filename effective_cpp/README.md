# Effective C++ — Complete Book Study Guide

## Based on Scott Meyers' "Effective C++" (Third Edition)

> *55 Specific Ways to Improve Your Programs and Designs*

---

## Overview

## Visual Reading Map

```text
┌───────────────────────────────────────────────────────────────────────────┐
│                         EFFECTIVE C++ READING FLOW                         │
├───────────────────────────────────────────────────────────────────────────┤
│  1. Language rules        -> const, initialization, compiler-generated code│
│  2. Object lifetime       -> constructors, destructors, assignment         │
│  3. Resource ownership    -> RAII, smart pointers, new/delete pairing      │
│  4. Interface design      -> hard-to-misuse APIs and encapsulation         │
│  5. Implementation safety -> casts, handles, exceptions, dependencies      │
│  6. Inheritance choices   -> is-a, composition, virtual dispatch, MI       │
│  7. Templates             -> compile-time interfaces, traits, TMP          │
│  8. Allocation hooks      -> new-handler, custom new/delete, placement new │
│  9. Ecosystem habits      -> warnings, standard library, Boost             │
│                                                                           │
│  Read each item as:                                                        │
│  Problem -> Rule -> Failure Mode -> Safer Design -> Code Details           │
└───────────────────────────────────────────────────────────────────────────┘
```

This guide provides an extensive, in-depth coverage of every item in Scott Meyers' seminal C++ book. Each chapter file contains detailed explanations, real-world code examples, pitfall demonstrations, and practical guidelines.

## Chapters

| # | Chapter | Items | File |
|---|---------|-------|------|
| 1 | [Accustoming Yourself to C++](01-accustoming-yourself-to-cpp.md) | Items 1–4 | Foundations: C++ as a federation, `const`, `enum`, `inline`, initialization |
| 2 | [Constructors, Destructors, and Assignment Operators](02-constructors-destructors-assignment.md) | Items 5–12 | What C++ generates, disabling, virtual destructors, exceptions, `operator=`, copying |
| 3 | [Resource Management](03-resource-management.md) | Items 13–17 | RAII, smart pointers, copying semantics, raw access, `new`/`delete` pairing |
| 4 | [Designs and Declarations](04-designs-and-declarations.md) | Items 18–26 | Interface design, type safety, pass-by-reference, data members, non-member functions |
| 5 | [Implementations](05-implementations.md) | Items 27–31 | Casting, exception safety, inlining, compilation dependencies |
| 6 | [Inheritance and Object-Oriented Design](06-inheritance-and-oo-design.md) | Items 32–40 | public inheritance, virtual functions, alternatives to virtuals, MI, private inheritance |
| 7 | [Templates and Generic Programming](07-templates-and-generic-programming.md) | Items 41–48 | Implicit interfaces, `typename`, dependent names, TMP, traits |
| 8 | [Customizing new and delete](08-customizing-new-and-delete.md) | Items 49–52 | Custom allocators, placement new, handler functions |
| 9 | [Miscellany](09-miscellany.md) | Items 53–55 | Compiler warnings, standard library, Boost |

## How to Use This Guide

- **Sequential study**: Read chapters 1–9 in order for a complete understanding
- **Reference lookup**: Jump to any specific item when you encounter a related problem
- **Code examples**: All examples are self-contained and compilable with C++11 or later
- **Key takeaways**: Each item ends with a "Things to Remember" summary

## Prerequisites

- Basic C++ syntax and OOP concepts
- Familiarity with standard library containers and algorithms
- A C++11 (or later) compiler for running examples

---

*"The best way to learn C++ is to learn from the mistakes of others."* — Scott Meyers
