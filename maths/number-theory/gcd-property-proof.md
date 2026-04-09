# Why GCD(a, b) = GCD(a - b, b): An Extensive Explanation

## Table of Contents
1. [Introduction](#introduction)
2. [Fundamental Definitions](#fundamental-definitions)
3. [The Main Theorem](#the-main-theorem)
4. [Detailed Proof](#detailed-proof)
5. [Intuitive Understanding](#intuitive-understanding)
6. [Examples](#examples)
7. [Connection to Euclidean Algorithm](#connection-to-euclidean-algorithm)
8. [Generalization](#generalization)
9. [Applications](#applications)

---

## Introduction

The property **GCD(a, b) = GCD(a - b, b)** is one of the most fundamental results in number theory and forms the theoretical foundation of the Euclidean algorithm for computing greatest common divisors. This document provides a comprehensive exploration of why this property holds, its implications, and its applications.

## Fundamental Definitions

### Definition 1: Divisibility
An integer **d** divides an integer **n** (written as **d | n**) if there exists an integer **k** such that:
```
n = k · d
```

### Definition 2: Common Divisor
An integer **d** is a **common divisor** of integers **a** and **b** if:
```
d | a  AND  d | b
```

### Definition 3: Greatest Common Divisor (GCD)
The **greatest common divisor** of integers **a** and **b**, denoted **GCD(a, b)** or **gcd(a, b)**, is the largest positive integer that divides both **a** and **b**.

### Key Properties of Divisibility
For any integers a, b, c, and d:
1. If **d | a** and **d | b**, then **d | (a + b)** and **d | (a - b)**
2. If **d | a**, then **d | (k · a)** for any integer k
3. Transitivity: If **d | a** and **a | b**, then **d | b**

---

## The Main Theorem

**Theorem**: For any integers **a** and **b** where **a ≥ b > 0**:
```
GCD(a, b) = GCD(a - b, b)
```

**More Generally**: For any integer **k**:
```
GCD(a, b) = GCD(a - k·b, b)
```

---

## Detailed Proof

We will prove this theorem by showing that the set of common divisors of **(a, b)** is identical to the set of common divisors of **(a - b, b)**.

### Proof Strategy
To prove **GCD(a, b) = GCD(a - b, b)**, we need to show:
1. Every common divisor of **(a, b)** is also a common divisor of **(a - b, b)**
2. Every common divisor of **(a - b, b)** is also a common divisor of **(a, b)**

If both sets of common divisors are identical, their maximum elements (the GCDs) must be equal.

### Part 1: Any divisor of (a, b) divides (a - b, b)

**Given**: Let **d** be any common divisor of **a** and **b**.

**To Prove**: **d** is also a common divisor of **(a - b)** and **b**.

**Proof**:
- Since **d** is a common divisor of **(a, b)**, we have:
  - **d | a** (d divides a)
  - **d | b** (d divides b)

- By the fundamental property of divisibility:
  - If **d | a** and **d | b**, then **d | (a - b)**

- We already know **d | b**

- Therefore, **d | (a - b)** and **d | b**

- Thus, **d** is a common divisor of **(a - b, b)** ✓

### Part 2: Any divisor of (a - b, b) divides (a, b)

**Given**: Let **d** be any common divisor of **(a - b)** and **b**.

**To Prove**: **d** is also a common divisor of **a** and **b**.

**Proof**:
- Since **d** is a common divisor of **(a - b, b)**, we have:
  - **d | (a - b)** (d divides a - b)
  - **d | b** (d divides b)

- By the fundamental property of divisibility:
  - If **d | (a - b)** and **d | b**, then **d | ((a - b) + b)**
  - Simplifying: **d | a**

- We already know **d | b**

- Therefore, **d | a** and **d | b**

- Thus, **d** is a common divisor of **(a, b)** ✓

### Conclusion

Since:
- Every common divisor of **(a, b)** is a common divisor of **(a - b, b)**
- Every common divisor of **(a - b, b)** is a common divisor of **(a, b)**

The two pairs **(a, b)** and **(a - b, b)** have **exactly the same set of common divisors**.

Therefore, they must have the same **greatest** common divisor:
```
GCD(a, b) = GCD(a - b, b)
```

**Q.E.D.** (Quod Erat Demonstrandum - "which was to be demonstrated")

---

## Intuitive Understanding

### Geometric Interpretation

Imagine you have two sticks:
- Stick A has length **a** units
- Stick B has length **b** units

The GCD represents the **longest unit stick** that can measure both A and B exactly (with no remainder).

Now, if we create a new stick C with length **a - b**:
- Any unit stick that measures both A and B can also measure C (because C = A - B)
- Any unit stick that measures both C and B can also measure A (because A = C + B)

Therefore, the longest such unit stick (the GCD) remains the same!

### Algebraic Perspective

If **g = GCD(a, b)**, then we can write:
```
a = g · m
b = g · n
```
where **m** and **n** are coprime integers (GCD(m, n) = 1).

Then:
```
a - b = g · m - g · n = g · (m - n)
```

So **g** divides both **(a - b)** and **b**. Moreover, since **m** and **n** are coprime, **(m - n)** and **n** are also coprime, making **g** the GCD of **(a - b, b)** as well.

---

## Examples

### Example 1: GCD(48, 18)

Let's compute GCD(48, 18) using the property repeatedly:

```
GCD(48, 18) = GCD(48 - 18, 18)
            = GCD(30, 18)
            = GCD(30 - 18, 18)
            = GCD(12, 18)
            = GCD(12, 18 - 12)    [we can also subtract the smaller from the larger]
            = GCD(12, 6)
            = GCD(12 - 6, 6)
            = GCD(6, 6)
            = GCD(6 - 6, 6)
            = GCD(0, 6)
            = 6
```

**Verification**: 48 = 6 × 8, and 18 = 6 × 3, where GCD(8, 3) = 1 ✓

### Example 2: GCD(105, 35)

```
GCD(105, 35) = GCD(105 - 35, 35)
             = GCD(70, 35)
             = GCD(70 - 35, 35)
             = GCD(35, 35)
             = GCD(0, 35)
             = 35
```

**Verification**: 105 = 35 × 3, so 35 divides 105 evenly ✓

### Example 3: GCD(97, 37)

```
GCD(97, 37) = GCD(97 - 37, 37)
            = GCD(60, 37)
            = GCD(60 - 37, 37)
            = GCD(23, 37)
            = GCD(23, 37 - 23)
            = GCD(23, 14)
            = GCD(23 - 14, 14)
            = GCD(9, 14)
            = GCD(9, 14 - 9)
            = GCD(9, 5)
            = GCD(9 - 5, 5)
            = GCD(4, 5)
            = GCD(4, 5 - 4)
            = GCD(4, 1)
            = GCD(4 - 4·1, 1)
            = GCD(0, 1)
            = 1
```

**Interpretation**: 97 and 37 are coprime (share no common factors except 1)

---

## Connection to Euclidean Algorithm

### The Subtraction-Based Euclidean Algorithm

The property **GCD(a, b) = GCD(a - b, b)** directly gives us an algorithm:

```python
def gcd_subtraction(a, b):
    while a != b:
        if a > b:
            a = a - b
        else:
            b = b - a
    return a
```

**Time Complexity**: O(max(a, b)) in the worst case (e.g., GCD(n, 1) requires n steps)

### The Division-Based Euclidean Algorithm

The more efficient version uses the observation that we can subtract **b** from **a** multiple times:

```
GCD(a, b) = GCD(a - b, b) = GCD(a - 2b, b) = ... = GCD(a - kb, b)
```

The optimal **k** is **⌊a/b⌋**, which gives us:
```
GCD(a, b) = GCD(a mod b, b)
```

This is the standard Euclidean algorithm:

```python
def gcd_division(a, b):
    while b != 0:
        a, b = b, a % b
    return a
```

**Time Complexity**: O(log(min(a, b))) - exponentially faster!

### Why the Division Method Works

The division-based method is simply an optimization of the subtraction method:

- Instead of subtracting **b** from **a** one time: **a - b**
- We subtract **b** from **a** multiple times: **a - kb** where **k = ⌊a/b⌋**
- This is exactly the remainder: **a mod b**

Since **GCD(a, b) = GCD(a - b, b)**, and we can apply this repeatedly:
```
GCD(a, b) = GCD(a - b, b)
          = GCD(a - 2b, b)
          = GCD(a - 3b, b)
          ...
          = GCD(a - kb, b)    where k = ⌊a/b⌋
          = GCD(a mod b, b)
```

---

## Generalization

### Extended Property 1: Multiple Subtractions

For any integer **k**:
```
GCD(a, b) = GCD(a - kb, b)
```

**Proof**: Apply the basic property **k** times:
```
GCD(a, b) = GCD(a - b, b) = GCD((a - b) - b, b) = ... = GCD(a - kb, b)
```

### Extended Property 2: Linear Combinations

For any integers **m** and **n** (not both zero):
```
GCD(a, b) = GCD(ma + nb, b)
```

This is a direct consequence of the fact that the GCD divides all linear combinations.

### Extended Property 3: Symmetric Form

```
GCD(a, b) = GCD(a - b, b) = GCD(a, b - a) = GCD(a - b, a) = GCD(a - b, b - a)
```

All of these transformations preserve the GCD.

### Extended Property 4: Generalization to Multiple Numbers

For three numbers:
```
GCD(a, b, c) = GCD(GCD(a, b), c) = GCD(a - b, b, c)
```

---


## Applications

### 1. Algorithm Design

The property is the foundation of:
- **Euclidean Algorithm**: Fast GCD computation
- **Extended Euclidean Algorithm**: Finding integer solutions to **ax + by = GCD(a, b)**
- **Binary GCD Algorithm** (Stein's Algorithm): Using binary operations for hardware efficiency

### 2. Cryptography

- **RSA Algorithm**: Relies on GCD computations for key generation
- **Modular Arithmetic**: GCD determines when modular inverses exist
- **Diffie-Hellman**: Uses coprimality checks (GCD = 1)

### 3. Fraction Simplification

To simplify a fraction **a/b**:
```
a/b = (a ÷ GCD(a,b)) / (b ÷ GCD(a,b))
```

Using GCD(a, b) = GCD(a - b, b) makes this efficient.

### 4. Solving Diophantine Equations

Linear Diophantine equations **ax + by = c** have integer solutions if and only if **GCD(a, b) | c**.

### 5. Chinese Remainder Theorem

The CRT requires pairwise coprime moduli, which is verified using GCD = 1.

### 6. Rational Reconstruction

Used in computer algebra systems to recover rational numbers from modular arithmetic.

---

## Mathematical Rigor: Formal Proof Using Set Theory

### Theorem (Formal Statement)

Let **D(n)** denote the set of positive divisors of **n**. For integers **a, b** with **a ≥ b > 0**:
```
D(a) ∩ D(b) = D(a - b) ∩ D(b)
```

Therefore:
```
max(D(a) ∩ D(b)) = max(D(a - b) ∩ D(b))
```

Which means:
```
GCD(a, b) = GCD(a - b, b)
```

### Proof of Set Equality

**Step 1**: Show **D(a) ∩ D(b) ⊆ D(a - b) ∩ D(b)**

Let **d ∈ D(a) ∩ D(b)**. Then:
- **d | a**, so **a = dq₁** for some integer **q₁**
- **d | b**, so **b = dq₂** for some integer **q₂**

Then:
```
a - b = dq₁ - dq₂ = d(q₁ - q₂)
```

So **d | (a - b)**, meaning **d ∈ D(a - b)**.

Since **d ∈ D(b)** already, we have **d ∈ D(a - b) ∩ D(b)**.

**Step 2**: Show **D(a - b) ∩ D(b) ⊆ D(a) ∩ D(b)**

Let **d ∈ D(a - b) ∩ D(b)**. Then:
- **d | (a - b)**, so **a - b = dq₁** for some integer **q₁**
- **d | b**, so **b = dq₂** for some integer **q₂**

Then:
```
a = (a - b) + b = dq₁ + dq₂ = d(q₁ + q₂)
```

So **d | a**, meaning **d ∈ D(a)**.

Since **d ∈ D(b)** already, we have **d ∈ D(a) ∩ D(b)**.

**Step 3**: Conclusion

Since both subset relations hold:
```
D(a) ∩ D(b) = D(a - b) ∩ D(b)
```

The maximum element of both sets must be equal:
```
GCD(a, b) = max(D(a) ∩ D(b)) = max(D(a - b) ∩ D(b)) = GCD(a - b, b)
```

**Q.E.D.**

---

## Summary

The property **GCD(a, b) = GCD(a - b, b)** is fundamental because:

1. **It preserves the set of common divisors** - subtracting one number from another doesn't change what divides both
2. **It enables efficient algorithms** - the Euclidean algorithm is based on repeated application
3. **It has beautiful generalizations** - extends to linear combinations and multiple numbers
4. **It has practical applications** - cryptography, fraction arithmetic, equation solving

This simple property connects elementary number theory to practical computation and advanced mathematics!
