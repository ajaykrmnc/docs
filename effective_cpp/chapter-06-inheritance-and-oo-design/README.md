# Chapter 6: Inheritance and Object-Oriented Design

## Chapter Flow

```text
┌───────────────────────────────────────────────────────────────────────────┐
│             CHAPTER 6: INHERITANCE AND OBJECT-ORIENTED DESIGN             │
├───────────────────────────────────────────────────────────────────────────┤
│ Item 32 -> public inheritance means substitutable is-a.                   │
│ Items 33-37 -> understand name hiding, virtual contracts, non-virtual     │
│ invariants, defaults.                                                     │
│ Items 38-39 -> prefer composition; use private inheritance only for       │
│ implementation needs.                                                     │
│ Item 40 -> use multiple inheritance only when ambiguity and diamond       │
│ costs are controlled.                                                     │
└───────────────────────────────────────────────────────────────────────────┘
```

Inheritance and object-oriented design in C++ is deceptively rich. The language offers public, protected, and private inheritance; single and multiple inheritance; virtual and non-virtual functions; pure virtual, simple virtual, and non-virtual member functions; and interactions between inheritance and other language features such as default parameter values and names in enclosing scopes. This chapter explains what these features really mean -- not what they look like, but what they actually *express* in a well-designed C++ program.

---
