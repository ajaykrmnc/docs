# Chapter 4: Designs and Declarations

## Chapter Flow

```text
┌───────────────────────────────────────────────────────────────────────────┐
│                    CHAPTER 4: DESIGNS AND DECLARATIONS                    │
├───────────────────────────────────────────────────────────────────────────┤
│ Items 18-19 -> design APIs/types so invalid use is hard.                  │
│ Items 20-21 -> avoid unnecessary copies, return real objects when         │
│ needed.                                                                   │
│ Items 22-24 -> protect representation and use non-members for             │
│ symmetry/encapsulation.                                                   │
│ Items 25-26 -> provide efficient no-throw swap and delay variable         │
│ creation.                                                                 │
└───────────────────────────────────────────────────────────────────────────┘
```

This chapter is the heart of "Effective C++" -- it addresses the design decisions that determine
whether your C++ software is correct, efficient, and maintainable. Good interfaces are easy to
use correctly and hard to use incorrectly. Good class designs mirror the thought that goes into
designing built-in types. The items here cover parameter passing, return values, encapsulation,
namespace design, swap mechanics, and variable lifetime -- all critical to writing professional C++.

---
