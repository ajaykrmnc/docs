# The Chinese Remainder Theorem: An Extensive Guide

## Table of Contents

1. [Introduction](#introduction)
2. [Historical Background](#historical-background)
3. [Fundamental Definitions](#fundamental-definitions)
4. [Statement of the Theorem](#statement-of-the-theorem)
5. [Simple Examples](#simple-examples)
6. [Detailed Proof](#detailed-proof)
7. [The Construction Algorithm](#the-construction-algorithm)
8. [Extended Examples](#extended-examples)
9. [Uniqueness of Solutions](#uniqueness-of-solutions)
10. [Generalizations](#generalizations)
11. [Applications](#applications)
12. [Computational Complexity](#computational-complexity)

---

## Introduction

The **Chinese Remainder Theorem (CRT)** is one of the most elegant and practical results in number theory. It
provides a method for solving systems of simultaneous congruences with pairwise coprime moduli. The theorem
not only guarantees the existence of a solution but also ensures its uniqueness within a certain range.

In essence, the CRT allows us to work with large numbers by breaking them down into smaller, more manageable
pieces using modular arithmetic.

---

## Historical Background

### Origins in Ancient China

The theorem gets its name from ancient Chinese mathematical texts. The earliest known appearance is in the
3rd-century work **"Sun Zi Suan Jing"** (The Mathematical Classic of Sun Zi), where Sun Tzu (not the military
strategist) posed the following problem:

> **The Sun Tzu Problem** (circa 300 CE):
> "There are certain things whose number is unknown. When divided by 3, the remainder is 2; when divided by 5,
> the remainder is 3; and when divided by 7, the remainder is 2. What will be the number?"

This translates to the system:

```
x ≡ 2 (mod 3)
x ≡ 3 (mod 5)
x ≡ 2 (mod 7)
```

The solution given was **x = 23** (and all numbers of the form 23 + 105k).

### Development Through History

- **Qin Jiushao** (1247): Provided a general algorithm in "Mathematical Treatise in Nine Sections"
- **Leonhard Euler** (18th century): Formalized the theorem in modern mathematical language
- **Carl Friedrich Gauss** (1801): Included it in "Disquisitiones Arithmeticae" and proved the general case

---

## Fundamental Definitions

### Definition 1: Modular Congruence

Two integers **a** and **b** are **congruent modulo n**, written:

```
a ≡ b (mod n)
```

if **n** divides **(a - b)**, or equivalently, if **a** and **b** have the same remainder when divided by
**n**.

**Example**: 17 ≡ 5 (mod 12) because 17 - 5 = 12 is divisible by 12.

### Definition 2: Coprime (Relatively Prime)

Two integers **a** and **b** are **coprime** if **GCD(a, b) = 1**.

**Example**: 15 and 28 are coprime because GCD(15, 28) = 1.

### Definition 3: Pairwise Coprime

A set of integers **{n₁, n₂, ..., nₖ}** is **pairwise coprime** if every pair is coprime:

```
GCD(nᵢ, nⱼ) = 1  for all i ≠ j
```

**Important**: Pairwise coprime is stronger than just coprime.

- **Pairwise coprime example**: {3, 5, 7} - every pair has GCD = 1
- **Not pairwise coprime**: {6, 10, 15} - GCD(6,10,15) = 1, but GCD(6,10) = 2

### Definition 4: Residue Class

The **residue class of a modulo n** is the set of all integers congruent to **a** modulo **n**:

```
[a]ₙ = {a + kn : k ∈ ℤ}
```

---

## Statement of the Theorem

### Theorem (Chinese Remainder Theorem)

Let **n₁, n₂, ..., nₖ** be **pairwise coprime** positive integers (i.e., GCD(nᵢ, nⱼ) = 1 for i ≠ j).

Let **a₁, a₂, ..., aₖ** be any integers.

Then the system of congruences:

```
x ≡ a₁ (mod n₁)
x ≡ a₂ (mod n₂)
⋮
x ≡ aₖ (mod nₖ)
```

has **exactly one solution** modulo **N = n₁ · n₂ · ... · nₖ**.

That is, there exists a unique integer **x₀** with **0 ≤ x₀ < N** such that **x₀** satisfies all the
congruences, and the complete set of solutions is:

```
x = x₀ + kN,  where k ∈ ℤ
```

### Key Points

1. **Existence**: A solution always exists
2. **Uniqueness**: The solution is unique modulo N
3. **Requirement**: The moduli must be pairwise coprime (crucial!)

---

## Simple Examples

### Example 1: Two Congruences

**Problem**: Find **x** such that:

```
x ≡ 2 (mod 3)
x ≡ 3 (mod 5)
```

**Solution**:

Since 3 and 5 are coprime, CRT guarantees a unique solution modulo 3 × 5 = 15.

**Method 1 - Trial and Error** (for small numbers):

- Numbers satisfying x ≡ 2 (mod 3): 2, 5, 8, 11, 14, 17, 20, 23, ...
- Check which also satisfies x ≡ 3 (mod 5):
  - 2 mod 5 = 2 ✗
  - 5 mod 5 = 0 ✗
  - 8 mod 5 = 3 ✓

**Answer**: x = 8 (and all numbers of the form 8 + 15k)

**Verification**:

- 8 ÷ 3 = 2 remainder **2** ✓
- 8 ÷ 5 = 1 remainder **3** ✓

### Example 2: Three Congruences

**Problem**: Find **x** such that:

```
x ≡ 1 (mod 2)
x ≡ 2 (mod 3)
x ≡ 3 (mod 5)
```

**Solution**:

Moduli are pairwise coprime: GCD(2,3) = GCD(2,5) = GCD(3,5) = 1 ✓

N = 2 × 3 × 5 = 30

**Method - Systematic Search** (we'll learn the algorithm later):

- Numbers satisfying x ≡ 1 (mod 2): 1, 3, 5, 7, 9, 11, 13, 15, 17, 19, 21, 23, ...
- Which also satisfy x ≡ 2 (mod 3)? Need remainder 2 when divided by 3:
  - 1 mod 3 = 1 ✗
  - 3 mod 3 = 0 ✗
  - 5 mod 3 = 2 ✓ (candidate)
  - Check: 5 mod 5 = 0 ✗
  - Continue: 11 mod 3 = 2 ✓
  - Check: 11 mod 5 = 1 ✗
  - Continue: 17 mod 3 = 2 ✓
  - Check: 17 mod 5 = 2 ✗
  - Continue: 23 mod 3 = 2 ✓
  - Check: 23 mod 5 = 3 ✓

**Answer**: x = 23 (and all numbers of the form 23 + 30k)

This is the classic Sun Tzu problem with adjusted remainders!

---

## Detailed Proof

The proof of the Chinese Remainder Theorem has two parts: **existence** and **uniqueness**.

### Part 1: Existence of a Solution

We need to prove that there exists at least one **x** that satisfies all the congruences.

**Construction Strategy**: We'll build the solution **x** as a sum:

```
x = a₁·M₁·y₁ + a₂·M₂·y₂ + ... + aₖ·Mₖ·yₖ
```

where each term is carefully chosen so that:

- The **i-th** term satisfies the **i-th** congruence
- The **i-th** term is divisible by all other moduli

**Detailed Construction**:

**Step 1**: Define **N = n₁ · n₂ · ... · nₖ** (the product of all moduli)

**Step 2**: For each **i**, define **Mᵢ = N / nᵢ**

This means:

- **M₁ = n₂ · n₃ · ... · nₖ** (all moduli except n₁)
- **M₂ = n₁ · n₃ · ... · nₖ** (all moduli except n₂)
- And so on...

**Key Observation**: **Mᵢ** is divisible by all moduli **except** **nᵢ**.

**Step 3**: Since **GCD(Mᵢ, nᵢ) = 1** (because nᵢ shares no factors with the product of other coprime
numbers), by Bézout's identity, there exist integers **yᵢ** and **zᵢ** such that:

```
Mᵢ · yᵢ + nᵢ · zᵢ = 1
```

This means:

```
Mᵢ · yᵢ ≡ 1 (mod nᵢ)
```

In other words, **yᵢ** is the **modular multiplicative inverse** of **Mᵢ** modulo **nᵢ**.

**Step 4**: Define:

```
eᵢ = Mᵢ · yᵢ
```

**Properties of eᵢ**:

- **eᵢ ≡ 1 (mod nᵢ)** (by construction)
- **eᵢ ≡ 0 (mod nⱼ)** for all **j ≠ i** (because Mᵢ contains nⱼ as a factor)

This means **eᵢ** acts like a "selector" that is 1 modulo nᵢ and 0 modulo all other nⱼ.

**Step 5**: Construct the solution:

```
x = a₁·e₁ + a₂·e₂ + ... + aₖ·eₖ
```

**Step 6**: Verify that **x** satisfies all congruences:

For any particular **i**:

```
x = a₁·e₁ + a₂·e₂ + ... + aᵢ·eᵢ + ... + aₖ·eₖ
```

Taking this modulo **nᵢ**:

```
x ≡ a₁·e₁ + a₂·e₂ + ... + aᵢ·eᵢ + ... + aₖ·eₖ (mod nᵢ)
≡ a₁·0 + a₂·0 + ... + aᵢ·1 + ... + aₖ·0    (mod nᵢ)
≡ aᵢ (mod nᵢ)
```

Thus, **x** satisfies all the congruences! ✓

### Part 2: Uniqueness of the Solution

We need to prove that if **x₁** and **x₂** both satisfy all the congruences, then:

```
x₁ ≡ x₂ (mod N)
```

**Proof**:

**Given**: Both **x₁** and **x₂** satisfy:

```
x₁ ≡ aᵢ (mod nᵢ)  for all i
x₂ ≡ aᵢ (mod nᵢ)  for all i
```

**Therefore**:

```
x₁ ≡ x₂ (mod nᵢ)  for all i
```

This means:

```
nᵢ | (x₁ - x₂)  for all i
```

**Since n₁, n₂, ..., nₖ are pairwise coprime**, by a fundamental theorem of number theory:

```
If nᵢ | d for all i, and the nᵢ are pairwise coprime,
then (n₁ · n₂ · ... · nₖ) | d
```

Therefore:

```
N | (x₁ - x₂)
```

Which means:

```
x₁ ≡ x₂ (mod N)
```

**Q.E.D.**

This proves that the solution is unique modulo **N**.

---

## The Construction Algorithm

Based on the proof, here's the step-by-step algorithm to find the solution.

### Algorithm: Solving CRT System

**Input**:

- Pairwise coprime moduli: **n₁, n₂, ..., nₖ**
- Remainders: **a₁, a₂, ..., aₖ**

**Output**: The unique solution **x** where **0 ≤ x < N**

**Steps**:

1. **Compute N**:

   ```
   N = n₁ · n₂ · ... · nₖ
   ```

2. **For each i from 1 to k**:

   a. Compute **Mᵢ**:

   ```
   Mᵢ = N / nᵢ
   ```

   b. Find **yᵢ** such that:

   ```
   Mᵢ · yᵢ ≡ 1 (mod nᵢ)
   ```

   (Use Extended Euclidean Algorithm to find the modular inverse)

   c. Compute **eᵢ**:

   ```
   eᵢ = Mᵢ · yᵢ
   ```

3. **Compute the solution**:

   ```
   x = Σ(aᵢ · eᵢ) mod N
   x = (a₁·e₁ + a₂·e₂ + ... + aₖ·eₖ) mod N
   ```

4. **Return x**

---

## Extended Examples

### Example 3: Detailed Walkthrough

**Problem**: Solve:

```
x ≡ 2 (mod 3)
x ≡ 3 (mod 5)
x ≡ 2 (mod 7)
```

**Solution using the CRT Algorithm**:

**Step 1**: Verify pairwise coprimality:

- GCD(3, 5) = 1 ✓
- GCD(3, 7) = 1 ✓
- GCD(5, 7) = 1 ✓

Compute N:

```
N = 3 · 5 · 7 = 105
```

**Step 2**: Compute Mᵢ values:

```
M₁ = N / n₁ = 105 / 3 = 35
M₂ = N / n₂ = 105 / 5 = 21
M₃ = N / n₃ = 105 / 7 = 15
```

**Step 3**: Find modular inverses yᵢ:

**For y₁**: Find y₁ such that M₁ · y₁ ≡ 1 (mod n₁)

```
35 · y₁ ≡ 1 (mod 3)
```

Since 35 ≡ 2 (mod 3):

```
2 · y₁ ≡ 1 (mod 3)
```

Testing: 2 · 2 = 4 ≡ 1 (mod 3) ✓

So **y₁ = 2**

**For y₂**: Find y₂ such that M₂ · y₂ ≡ 1 (mod n₂)

```
21 · y₂ ≡ 1 (mod 5)
```

Since 21 ≡ 1 (mod 5):

```
1 · y₂ ≡ 1 (mod 5)
```

So **y₂ = 1**

**For y₃**: Find y₃ such that M₃ · y₃ ≡ 1 (mod n₃)

```
15 · y₃ ≡ 1 (mod 7)
```

Since 15 ≡ 1 (mod 7):

```
1 · y₃ ≡ 1 (mod 7)
```

So **y₃ = 1**

**Step 4**: Compute eᵢ values:

```
e₁ = M₁ · y₁ = 35 · 2 = 70
e₂ = M₂ · y₂ = 21 · 1 = 21
e₃ = M₃ · y₃ = 15 · 1 = 15
```

**Step 5**: Compute the solution:

```
x = a₁·e₁ + a₂·e₂ + a₃·e₃
= 2·70 + 3·21 + 2·15
= 140 + 63 + 30
= 233
```

**Step 6**: Reduce modulo N:

```
x = 233 mod 105 = 23
```

**Final Answer**: **x = 23** (and all numbers of form 23 + 105k)

**Verification**:

- 23 ÷ 3 = 7 remainder **2** ✓
- 23 ÷ 5 = 4 remainder **3** ✓
- 23 ÷ 7 = 3 remainder **2** ✓

This is the original Sun Tzu problem!

### Example 4: Larger Numbers

**Problem**: Solve:

```
x ≡ 5 (mod 11)
x ≡ 3 (mod 13)
x ≡ 10 (mod 17)
```

**Solution**:

**Step 1**: Check coprimality (11, 13, 17 are all prime, so pairwise coprime ✓)

```
N = 11 · 13 · 17 = 2431
```

**Step 2**: Compute Mᵢ:

```
M₁ = 2431 / 11 = 221
M₂ = 2431 / 13 = 187
M₃ = 2431 / 17 = 143
```

**Step 3**: Find yᵢ:

**For y₁**: 221 · y₁ ≡ 1 (mod 11)

```
221 ≡ 1 (mod 11)  [since 221 = 11·20 + 1]
So y₁ = 1
```

**For y₂**: 187 · y₂ ≡ 1 (mod 13)

```
187 = 13·14 + 5, so 187 ≡ 5 (mod 13)
Need: 5 · y₂ ≡ 1 (mod 13)

Testing: 5 · 8 = 40 = 3·13 + 1 ≡ 1 (mod 13) ✓
So y₂ = 8
```

**For y₃**: 143 · y₃ ≡ 1 (mod 17)

```
143 = 17·8 + 7, so 143 ≡ 7 (mod 17)
Need: 7 · y₃ ≡ 1 (mod 17)

Testing: 7 · 5 = 35 = 2·17 + 1 ≡ 1 (mod 17) ✓
So y₃ = 5
```

**Step 4**: Compute eᵢ:

```
e₁ = 221 · 1 = 221
e₂ = 187 · 8 = 1496
e₃ = 143 · 5 = 715
```

**Step 5**: Compute x:

```
x = 5·221 + 3·1496 + 10·715
= 1105 + 4488 + 7150
= 12743
```

**Step 6**: Reduce modulo N:

```
x = 12743 mod 2431
12743 = 5·2431 + 588
x = 588
```

**Final Answer**: **x = 588**

**Verification**:

- 588 = 11·53 + 5, so 588 ≡ 5 (mod 11) ✓
- 588 = 13·45 + 3, so 588 ≡ 3 (mod 13) ✓
- 588 = 17·34 + 10, so 588 ≡ 10 (mod 17) ✓

---

## Uniqueness of Solutions

### The Solution Space

The CRT tells us there is exactly one solution in the range **[0, N)**.

However, the complete set of all solutions is:

```
S = {x₀ + kN : k ∈ ℤ}
```

where **x₀** is the unique solution in **[0, N)**.

### Why N is the Period

**Theorem**: If **x₀** is a solution, then **x₀ + N** is also a solution.

**Proof**:

```
(x₀ + N) mod nᵢ = (x₀ + n₁·n₂·...·nₖ) mod nᵢ
= x₀ mod nᵢ    [since N is divisible by nᵢ]
= aᵢ
```

So adding **N** preserves all the congruences.

### Minimality of N

**Theorem**: **N** is the smallest positive period.

**Proof**: Suppose there's a smaller period **P < N** such that **x₀ + P** is also a solution.

Then:

```
x₀ + P ≡ x₀ (mod nᵢ)  for all i
```

This means:

```
P ≡ 0 (mod nᵢ)  for all i
```

Since the **nᵢ** are pairwise coprime, this implies:

```
P ≡ 0 (mod N)
```

But **P < N** and **P ≥ 0**, so **P** cannot be divisible by **N** unless **P = 0**.

Therefore, **N** is the minimal positive period.

---

## Generalizations

### Generalization 1: Non-Coprime Moduli

**Question**: What if the moduli are not pairwise coprime?

The system may have:

1. **No solution** (inconsistent system)
2. **Infinitely many solutions modulo some smaller period** (consistent but redundant system)

**Theorem**: The system:

```
x ≡ a₁ (mod n₁)
x ≡ a₂ (mod n₂)
```

has a solution if and only if:

```
GCD(n₁, n₂) | (a₁ - a₂)
```

**Example (No Solution)**:

```
x ≡ 1 (mod 4)
x ≡ 3 (mod 6)
```

Check: GCD(4, 6) = 2, and (1 - 3) = -2

Since 2 | -2, the system should have solutions. Let's verify:

- x ≡ 1 (mod 4) means x = 1, 5, 9, 13, 17, 21, 25, ...
- x ≡ 3 (mod 6) means x = 3, 9, 15, 21, 27, ...
- Common values: 9, 21, 33, ... (pattern: 9 + 12k)

So x ≡ 9 (mod 12), where 12 = LCM(4, 6).

**Example (Inconsistent - No Solution)**:

```
x ≡ 1 (mod 4)
x ≡ 2 (mod 6)
```

Check: GCD(4, 6) = 2, but (1 - 2) = -1

Since 2 does not divide -1, **no solution exists**.

Verification:

- x ≡ 1 (mod 4) means x = 1, 5, 9, 13, 17, 21, ...
- x ≡ 2 (mod 6) means x = 2, 8, 14, 20, 26, ...
- No overlap! ✗

### Generalization 2: Abstract Algebra Formulation

In the language of ring theory:

**Theorem (Ring Isomorphism)**:

If **n₁, n₂, ..., nₖ** are pairwise coprime, then:

```
ℤ/Nℤ ≅ ℤ/n₁ℤ × ℤ/n₂ℤ × ... × ℤ/nₖℤ
```

where **N = n₁ · n₂ · ... · nₖ**.

This isomorphism is given by:

```
x mod N ↦ (x mod n₁, x mod n₂, ..., x mod nₖ)
```

This means we can represent integers modulo **N** as tuples of smaller residues!

### Generalization 3: Polynomial Chinese Remainder Theorem

The CRT also works for polynomials over a field.

**Theorem**: Let **F** be a field and **p₁(x), p₂(x), ..., pₖ(x)** be pairwise coprime polynomials in
**F[x]**.

Then for any polynomials **a₁(x), a₂(x), ..., aₖ(x)**, the system:

```
f(x) ≡ a₁(x) (mod p₁(x))
f(x) ≡ a₂(x) (mod p₂(x))
⋮
f(x) ≡ aₖ(x) (mod pₖ(x))
```

has a unique solution modulo **P(x) = p₁(x) · p₂(x) · ... · pₖ(x)**.

---

## Applications

The Chinese Remainder Theorem has numerous practical applications across computer science, cryptography, and
mathematics.

### 1. Fast Modular Arithmetic

**Application**: Computing with large numbers by working with smaller moduli.

**Example**: Compute **123456 × 789012 mod 1000000007** (a common large prime in competitive programming).

Instead of computing directly with large numbers, choose small coprime moduli:

- Let n₁ = 97, n₂ = 101, n₃ = 103 (all prime)
- N = 97 × 101 × 103 = 1,008,991 > 1,000,000,007... (need adjustment)

Better: Use moduli like 2^32, 2^31-1, etc., depending on the application.

**Benefits**:

- Smaller intermediate results
- Parallelization (compute each modulus independently)
- Reduced precision requirements

### 2. RSA Cryptography

**Application**: Speed up RSA decryption using the Chinese Remainder Theorem.

In RSA:

- Public key: **(n, e)** where **n = p · q** (product of two large primes)
- Private key: **(n, d)**
- Decryption: **m = c^d mod n**

**CRT Optimization**:

Instead of computing **c^d mod n** directly, compute:

```
m₁ = c^d mod p
m₂ = c^d mod q
```

Then use CRT to find **m mod n**.

**Speed-up**: This is approximately **4× faster** because:

- Exponentiation modulo p and q are done with smaller numbers
- Each can be computed in parallel

This is the **RSA-CRT** algorithm used in practice!

### 3. Secret Sharing

**Application**: Asmuth-Bloom secret sharing scheme.

**Idea**: Split a secret **S** into **n** shares such that any **k** shares can reconstruct the secret.

**Method**:

1. Choose pairwise coprime moduli **m₁ < m₂ < ... < mₙ** such that:

   ```
   m₁ · m₂ · ... · mₖ > mₖ₊₁ · mₖ₊₂ · ... · mₙ · S
   ```

2. Generate shares:

   ```
   sᵢ = S mod mᵢ
   ```

3. Any **k** shares can use CRT to recover **S**.

### 4. Calendrical Calculations

**Application**: Determining recurring events.

**Example**: When do three events that recur every 3, 5, and 7 days align?

This is asking: When is **x ≡ 0 (mod 3)**, **x ≡ 0 (mod 5)**, and **x ≡ 0 (mod 7)**?

Answer: Every **LCM(3, 5, 7) = 105** days.

More generally, CRT solves problems like:

- When will specific days of week align with dates?
- Computing Easter date (involves modular arithmetic with 19, 7, 4)

### 5. Solving Diophantine Equations

**Application**: Finding integer solutions to linear systems.

**Example**: Find all integers **n** such that:

- n leaves remainder 2 when divided by 5
- n leaves remainder 3 when divided by 7
- n leaves remainder 4 when divided by 9

CRT gives: **n = 193 + 315k** for any integer **k**.

### 6. Computer Architecture

**Application**: Residue Number Systems (RNS).

**Idea**: Represent numbers as tuples of residues modulo pairwise coprime bases.

**Example**: Using bases {3, 5, 7}:

```
23 → (2, 3, 2) because 23 ≡ 2 (mod 3), 23 ≡ 3 (mod 5), 23 ≡ 2 (mod 7)
```

**Benefits**:

- Carry-free addition and multiplication
- Parallelizable operations
- Used in digital signal processing

### 7. Error Detection and Correction

**Application**: CRT-based error-correcting codes.

**Idea**: Encode data using multiple moduli; errors in some moduli can be detected and corrected.

### 8. Competitive Programming

**Application**: Solving problems with multiple modular constraints.

**Common Pattern**:

```
"Find the nth Fibonacci number modulo 10^9+7"
"Find the number of ways to ... modulo 998244353"
```

When dealing with multiple constraints, CRT allows combining results.

---

## Computational Complexity

### Time Complexity of CRT Algorithm

For a system with **k** congruences and moduli of size up to **B** bits:

1. **Computing N**: O(k) multiplications → O(k · B²) time

2. **Computing Mᵢ**: O(k) divisions → O(k · B²) time

3. **Finding modular inverses yᵢ**:
   - Using Extended Euclidean Algorithm: O(B²) per inverse
   - Total: O(k · B²) time

4. **Computing final sum**: O(k) multiplications and additions → O(k · B²) time

**Overall**: **O(k · B²)** time

### Space Complexity

**O(k · B)** space to store the moduli, remainders, and intermediate results.

### Practical Considerations

**Optimizations**:

1. **Precompute** inverses if solving multiple systems with same moduli
2. **Use fast multiplication** algorithms (Karatsuba, FFT) for very large numbers
3. **Parallel computation** - each Mᵢ and yᵢ can be computed independently
4. **Garner's algorithm** - an alternative that avoids large intermediate values

**Garner's Algorithm**:

Instead of summing large products, build the solution incrementally:

```
x = a₁ + n₁(a₂ + n₂(a₃ + n₃(...)))
```

This keeps intermediate values smaller.

---

## Common Mistakes and Edge Cases

### Mistake 1: Assuming non-pairwise coprime moduli work

**Wrong**: Thinking CRT applies when GCD(n₁, n₂, n₃) = 1 but pairs share factors.

**Example**: {6, 10, 15}

- GCD(6, 10, 15) = 1 ✓
- But GCD(6, 10) = 2 ✗ (not pairwise coprime)

CRT does **not** apply directly!

### Mistake 2: Forgetting to reduce the final answer

Always reduce **x** modulo **N** to get the canonical answer in **[0, N)**.

### Mistake 3: Incorrect modular inverse calculation

Remember: **yᵢ** must satisfy **Mᵢ · yᵢ ≡ 1 (mod nᵢ)**, not (mod N)!

### Edge Case 1: Single congruence

When **k = 1**, the "system" is just:

```
x ≡ a₁ (mod n₁)
```

Solution: **x = a₁** (with period n₁).

### Edge Case 2: Negative remainders

If **aᵢ < 0**, convert to positive: **aᵢ + nᵢ**.

Example: **x ≡ -2 (mod 5)** is equivalent to **x ≡ 3 (mod 5)**.

---

## Summary

The Chinese Remainder Theorem is a powerful tool that:

1. **Guarantees** unique solutions to systems of congruences with pairwise coprime moduli
2. **Provides** an explicit construction algorithm
3. **Generalizes** to non-coprime cases (with conditions) and abstract algebra
4. **Enables** practical applications in cryptography, computing, and engineering
5. **Connects** modular arithmetic to ring theory and number systems

The theorem's elegance lies in reducing complex problems with large moduli to simpler problems with smaller,
independent moduli—a divide-and-conquer approach that has stood the test of time for over 1700 years!

---

## Further Reading

### Books

- **"An Introduction to the Theory of Numbers"** by Hardy & Wright
- **"Elementary Number Theory"** by David Burton
- **"Concrete Mathematics"** by Knuth, Patashnik, and Graham

### Papers

- Original formulations in "Mathematical Treatise in Nine Sections" (Qin Jiushao, 1247)
- Gauss's "Disquisitiones Arithmeticae" (1801)

### Online Resources

- Art of Problem Solving: CRT tutorials and practice problems
- Brilliant.org: Interactive CRT lessons
- Mathematics Stack Exchange: Advanced discussions and edge cases

---

**End of Document**

_Created: 2026-03-27_
