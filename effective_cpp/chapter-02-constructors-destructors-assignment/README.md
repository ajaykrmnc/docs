# Chapter 2: Constructors, Destructors, and Assignment Operators

## Chapter Flow

```text
┌───────────────────────────────────────────────────────────────────────────┐
│      CHAPTER 2: CONSTRUCTORS, DESTRUCTORS, AND ASSIGNMENT OPERATORS       │
├───────────────────────────────────────────────────────────────────────────┤
│ Item 5 -> know compiler-generated lifecycle functions.                    │
│ Item 6 -> delete/disallow lifecycle operations that violate your type.    │
│ Item 7 -> virtual destructor when deleting polymorphically.               │
│ Item 8 -> destructors must not leak exceptions.                           │
│ Item 9 -> no virtual calls while constructing/destructing.                │
│ Items 10-12 -> assignment returns *this, handles self-assignment, copies  │
│ every part.                                                               │
└───────────────────────────────────────────────────────────────────────────┘
```

[>](2026-04-09_>.md) Items 5-12: The special member functions that control object lifecycle — creation, destruction, and copying. 
> Getting these right is fundamental to writing correct, efficient, and exception-safe C++.

---
