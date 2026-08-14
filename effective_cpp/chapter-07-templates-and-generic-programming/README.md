# Chapter 7: Templates and Generic Programming

## Chapter Flow

```text
┌───────────────────────────────────────────────────────────────────────────┐
│               CHAPTER 7: TEMPLATES AND GENERIC PROGRAMMING                │
├───────────────────────────────────────────────────────────────────────────┤
│ Item 41 -> template interfaces are implicit expression requirements.      │
│ Items 42-43 -> mark dependent types/names explicitly for the compiler.    │
│ Items 44-46 -> avoid template bloat and enable compatible conversions.    │
│ Items 47-48 -> use traits/TMP for compile-time knowledge when benefit     │
│ exceeds complexity.                                                       │
└───────────────────────────────────────────────────────────────────────────┘
```

Templates are the foundation of generic programming in C++. They move part of the type-checking work from runtime to compile time, enable code reuse without sacrificing type safety, and open the door to an entirely separate computation model -- template metaprogramming -- that executes during compilation. This chapter covers Items 41-48 of Scott Meyers' *Effective C++* (Third Edition), spanning implicit interfaces, the `typename` disambiguator, accessing names in templatized base classes, code bloat, member function templates, friend functions in templates, traits classes, and template metaprogramming.

---
