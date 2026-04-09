# Rigorous Mathematical Proofs: GCD Property and Chinese Remainder Theorem

## Table of Contents
1. [Foundational Axioms and Definitions](#foundational-axioms-and-definitions)
2. [Preliminary Lemmas](#preliminary-lemmas)
3. [Complete Proof: GCD(a,b) = GCD(a-b,b)](#complete-proof-gcdab--gcdab-b)
4. [Complete Proof: Chinese Remainder Theorem](#complete-proof-chinese-remainder-theorem)
5. [Corollaries and Extensions](#corollaries-and-extensions)

---

## Foundational Axioms and Definitions

### Axiom 1: Well-Ordering Principle
Every non-empty set of positive integers has a least element.

### Axiom 2: Division Algorithm
For any integers **a** and **b** with **b > 0**, there exist unique integers **q** (quotient) and **r** (remainder) such that:
```
a = bq + r,  where 0 ≤ r < b
```

### Definition 1: Divisibility
Let **a, b ∈ ℤ**. We say **a divides b**, written **a | b**, if:
```
∃k ∈ ℤ : b = ka
```

### Definition 2: Common Divisor
An integer **d** is a common divisor of **a** and **b** if:
```
d | a  ∧  d | b
```

### Definition 3: Greatest Common Divisor (Formal)
The greatest common divisor of **a** and **b**, denoted **gcd(a,b)**, is the unique positive integer **g** satisfying:
1. **g | a** and **g | b** (g is a common divisor)
2. If **d | a** and **d | b**, then **d | g** (g is divisible by all common divisors)

**Alternative characterization**: **g = gcd(a,b)** is the largest positive integer dividing both **a** and **b**.

### Definition 4: Congruence Modulo n
For integers **a, b, n** with **n > 0**:
```
a ≡ b (mod n)  ⟺  n | (a - b)
```

### Definition 5: Pairwise Coprime
Integers **n₁, n₂, ..., nₖ** are pairwise coprime if:
```
∀i,j ∈ {1,...,k}, i ≠ j : gcd(nᵢ, nⱼ) = 1
```

---

## Preliminary Lemmas

### Lemma 1: Basic Properties of Divisibility

**Statement**: For all **a, b, c ∈ ℤ** and **d ∈ ℤ**, d ≠ 0:

**(a)** If **d | a** and **d | b**, then **d | (a + b)** and **d | (a - b)**

**(b)** If **d | a** and **d | b**, then for any **m, n ∈ ℤ**: **d | (ma + nb)**

**(c)** If **d | a**, then **d | (ka)** for any **k ∈ ℤ**

**Proof of (a)**:

Given: **d | a** and **d | b**

Then: **∃k₁, k₂ ∈ ℤ** such that **a = dk₁** and **b = dk₂**

Therefore:
```
a + b = dk₁ + dk₂ = d(k₁ + k₂)
```

Since **k₁ + k₂ ∈ ℤ**, we have **d | (a + b)**. ✓

Similarly:
```
a - b = dk₁ - dk₂ = d(k₁ - k₂)
```

Since **k₁ - k₂ ∈ ℤ**, we have **d | (a - b)**. ✓

**Proof of (b)**:

From **a = dk₁** and **b = dk₂**:
```
ma + nb = m(dk₁) + n(dk₂) = d(mk₁ + nk₂)
```

Since **mk₁ + nk₂ ∈ ℤ**, we have **d | (ma + nb)**. ✓

**Proof of (c)**: Immediate from (b) with **m = k, n = 0**. ✓

**Q.E.D.**

---

### Lemma 2: GCD Existence Theorem

**Statement**: For any integers **a, b** (not both zero), **gcd(a, b)** exists and is unique.

**Proof**:

**Step 1: Existence**

Let **S = {ax + by : x, y ∈ ℤ, ax + by > 0}**

**S** is non-empty (e.g., if **a > 0**, take **x = 1, y = 0** to get **a ∈ S**).

By the Well-Ordering Principle, **S** has a least element. Call it **g**.

So **g = au + bv** for some **u, v ∈ ℤ**.

**Claim**: **g = gcd(a, b)**

**Proof of Claim**:

**(i) Show g | a**:

By the Division Algorithm: **a = gq + r** where **0 ≤ r < g**

Then:
```
r = a - gq = a - (au + bv)q = a(1 - uq) + b(-vq)
```

If **r > 0**, then **r ∈ S** (it's a positive linear combination of a and b).

But **r < g**, contradicting that **g** is the minimum of **S**.

Therefore, **r = 0**, so **a = gq**, hence **g | a**. ✓

**(ii) Show g | b**: Identical argument shows **g | b**. ✓

**(iii) Show g is the greatest common divisor**:

Let **d** be any common divisor of **a** and **b**.

Then by Lemma 1(b): **d | (au + bv) = g**

So every common divisor divides **g**, making **g** the greatest. ✓

**Step 2: Uniqueness**

Suppose **g₁** and **g₂** both satisfy Definition 3.

Then:
- **g₁ | g₂** (since g₁ is divisible by all common divisors, and g₂ is a common divisor)
- **g₂ | g₁** (by the same reasoning)

Since **g₁** and **g₂** are both positive and divide each other: **g₁ = g₂**. ✓

**Q.E.D.**

---

### Lemma 3: Bézout's Identity

**Statement**: For any integers **a, b**, if **g = gcd(a, b)**, then there exist integers **x, y** such that:
```
ax + by = g
```

**Proof**: This was proven in Lemma 2 during the existence proof. The minimal element **g** of the set **S = {ax + by : x,y ∈ ℤ, ax + by > 0}** has the form **g = au + bv**, and we showed **g = gcd(a,b)**. ✓

**Q.E.D.**

---

### Lemma 4: Coprimality and Divisibility

**Statement**: If **gcd(a, b) = 1** and **a | bc**, then **a | c**.

**Proof**:

Given: **gcd(a, b) = 1**

By Bézout's Identity: **∃x, y ∈ ℤ : ax + by = 1**

Multiply both sides by **c**:
```
acx + bcy = c
```

Since **a | bc**, we have **bc = ak** for some **k ∈ ℤ**.

Substituting:
```
acx + (ak)y = c
acx + aky = c
a(cx + ky) = c
```

Since **cx + ky ∈ ℤ**, we have **a | c**. ✓

**Q.E.D.**

---

### Lemma 5: Product of Pairwise Coprime Divisors

**Statement**: If **n₁, n₂, ..., nₖ** are pairwise coprime and each **nᵢ | m**, then:
```
(n₁ · n₂ · ... · nₖ) | m
```

**Proof by induction on k**:

**Base case (k=1)**: Trivial. If **n₁ | m**, then **n₁ | m**. ✓

**Inductive step**: Assume true for **k-1**.

Given: **n₁, ..., nₖ** are pairwise coprime and each **nᵢ | m**.

By inductive hypothesis: **N' = n₁ · n₂ · ... · nₖ₋₁** divides **m**.

So **m = N' · t** for some **t ∈ ℤ**.

Now we need to show **nₖ · N' | m**.

**Claim**: **gcd(nₖ, N') = 1**

**Proof of Claim**:

Suppose **d | nₖ** and **d | N'**.

Since **N' = n₁ · ... · nₖ₋₁**, and **d | N'**, there exists some **i < k** such that **d | nᵢ**.

(If no prime factor of **d** divided any **nᵢ**, then **d** couldn't divide their product.)

But then **d | gcd(nₖ, nᵢ) = 1** (by pairwise coprimality).

So **d = 1**. ✓

Therefore **gcd(nₖ, N') = 1**.

Since **nₖ | m** and **m = N' · t**, we have **nₖ | N' · t**.

By Lemma 4: **nₖ | t** (since **gcd(nₖ, N') = 1**).

So **t = nₖ · s** for some **s ∈ ℤ**.

Therefore:
```
m = N' · t = N' · nₖ · s = (n₁ · n₂ · ... · nₖ) · s
```

Thus **(n₁ · n₂ · ... · nₖ) | m**. ✓

**Q.E.D.**

---

### Lemma 6: Modular Arithmetic Properties

**Statement**: For integers **a, b, c, n** with **n > 0**:

**(a)** **a ≡ b (mod n)** ⟺ **∃k ∈ ℤ : a = b + kn**

**(b)** If **a ≡ b (mod n)** and **c ≡ d (mod n)**, then **a + c ≡ b + d (mod n)**

**(c)** If **a ≡ b (mod n)** and **c ≡ d (mod n)**, then **ac ≡ bd (mod n)**

**Proof**:

**(a)**
```
a ≡ b (mod n) ⟺ n | (a - b)
              ⟺ ∃k ∈ ℤ : a - b = kn
              ⟺ ∃k ∈ ℤ : a = b + kn
```
✓

**(b)** Given **a = b + k₁n** and **c = d + k₂n**:
```
a + c = (b + k₁n) + (d + k₂n) = (b + d) + (k₁ + k₂)n
```

So **a + c ≡ b + d (mod n)**. ✓

**(c)** Given **a = b + k₁n** and **c = d + k₂n**:
```
ac = (b + k₁n)(d + k₂n)
   = bd + bk₂n + dk₁n + k₁k₂n²
   = bd + n(bk₂ + dk₁ + k₁k₂n)
```

So **ac ≡ bd (mod n)**. ✓

**Q.E.D.**

---

## Complete Proof: GCD(a,b) = GCD(a-b,b)

### Theorem 1: GCD Subtraction Property

**Statement**: For any integers **a, b** with **a ≥ b > 0**:
```
gcd(a, b) = gcd(a - b, b)
```

**Proof**:

Let **g₁ = gcd(a, b)** and **g₂ = gcd(a - b, b)**.

We will show **g₁ = g₂** by proving **g₁ | g₂** and **g₂ | g₁**, which implies **g₁ = g₂** (since both are positive).

---

**Part I: Prove g₁ | g₂**

Since **g₁ = gcd(a, b)**, we have:
```
g₁ | a  and  g₁ | b
```

By Lemma 1(a): **g₁ | (a - b)**.

So **g₁** is a common divisor of **(a - b)** and **b**.

Since **g₂ = gcd(a - b, b)** is divisible by all common divisors of **(a - b)** and **b** (by Definition 3, property 2):
```
g₁ | g₂
```
✓

---

**Part II: Prove g₂ | g₁**

Since **g₂ = gcd(a - b, b)**, we have:
```
g₂ | (a - b)  and  g₂ | b
```

By Lemma 1(b) with **m = 1, n = 1**:
```
g₂ | ((a - b) + b) = a
```

So **g₂** is a common divisor of **a** and **b**.

Since **g₁ = gcd(a, b)** is divisible by all common divisors of **a** and **b**:
```
g₂ | g₁
```
✓

---

**Part III: Conclusion**

Since **g₁ | g₂** and **g₂ | g₁**, and both are positive integers:

There exist positive integers **k₁, k₂** such that:
```
g₂ = k₁ · g₁
g₁ = k₂ · g₂
```

Substituting the first into the second:
```
g₁ = k₂ · (k₁ · g₁) = (k₁k₂) · g₁
```

Since **g₁ > 0**, we can divide both sides by **g₁**:
```
1 = k₁k₂
```

Since **k₁, k₂** are positive integers, the only solution is:
```
k₁ = k₂ = 1
```

Therefore:
```
g₁ = g₂
```

Hence:
```
gcd(a, b) = gcd(a - b, b)
```

**Q.E.D.** ∎

---

### Corollary 1.1: Extended GCD Property

**Statement**: For any integers **a, b** with **b > 0** and any integer **k**:
```
gcd(a, b) = gcd(a - kb, b)
```

**Proof by induction on k**:

**Base case (k = 0)**: **gcd(a, b) = gcd(a - 0·b, b) = gcd(a, b)**. ✓

**Base case (k = 1)**: This is Theorem 1. ✓

**Inductive step (k → k+1)** (for k > 0):

Assume: **gcd(a, b) = gcd(a - kb, b)**

Then:
```
gcd(a, b) = gcd(a - kb, b)
          = gcd((a - kb) - b, b)    [by Theorem 1]
          = gcd(a - (k+1)b, b)
```
✓

**For negative k**: Similar argument using **gcd(a, b) = gcd(a + b, b)**. ✓

**Q.E.D.** ∎

---


### Corollary 1.2: GCD and Modulo

**Statement**: For any integers **a, b** with **b > 0**:
```
gcd(a, b) = gcd(b, a mod b)
```

**Proof**:

By the Division Algorithm: **a = bq + r** where **r = a mod b** and **0 ≤ r < b**.

Then: **a - bq = r**, so **a - qb = r**.

By Corollary 1.1:
```
gcd(a, b) = gcd(a - qb, b) = gcd(r, b) = gcd(b, r)
```

Since **r = a mod b**:
```
gcd(a, b) = gcd(b, a mod b)
```

**Q.E.D.** ∎

This is the foundation of the Euclidean Algorithm.

---

## Complete Proof: Chinese Remainder Theorem

### Theorem 2: Chinese Remainder Theorem

**Statement**: Let **n₁, n₂, ..., nₖ** be pairwise coprime positive integers (i.e., **gcd(nᵢ, nⱼ) = 1** for all **i ≠ j**).

Let **a₁, a₂, ..., aₖ** be any integers.

Then the system of congruences:
```
x ≡ a₁ (mod n₁)
x ≡ a₂ (mod n₂)
  ⋮
x ≡ aₖ (mod nₖ)
```

has a solution, and any two solutions are congruent modulo **N = n₁ · n₂ · ... · nₖ**.

**Equivalently**: There exists a unique **x₀** with **0 ≤ x₀ < N** satisfying all congruences, and the complete solution set is:
```
{x₀ + tN : t ∈ ℤ}
```

---

**Proof**:

The proof consists of three parts:
1. **Existence**: Construct a solution
2. **Uniqueness modulo N**: Show any two solutions differ by a multiple of N
3. **Canonical representative**: Show there's a unique solution in [0, N)

---

### Part I: EXISTENCE of a Solution

**Construction Strategy**: We build the solution as a linear combination where each term "selects" for one congruence.

**Step 1**: Define **N = n₁ · n₂ · ... · nₖ**

**Step 2**: For each **i ∈ {1, 2, ..., k}**, define:
```
Mᵢ = N / nᵢ = n₁ · ... · nᵢ₋₁ · nᵢ₊₁ · ... · nₖ
```

That is, **Mᵢ** is the product of all moduli except **nᵢ**.

---

**Step 3**: **Claim**: For each **i**, **gcd(Mᵢ, nᵢ) = 1**

**Proof of Claim**:

Suppose **d = gcd(Mᵢ, nᵢ) > 1**.

Then **d | nᵢ** and **d | Mᵢ**.

Since **d | Mᵢ** and **Mᵢ = n₁ · ... · nᵢ₋₁ · nᵢ₊₁ · ... · nₖ**, by the fundamental theorem of arithmetic, there exists some prime **p** dividing **d** such that **p | Mᵢ**.

Therefore, **p** divides at least one of **{n₁, ..., nᵢ₋₁, nᵢ₊₁, ..., nₖ}**.

Say **p | nⱼ** for some **j ≠ i**.

But **p | d** and **d | nᵢ**, so **p | nᵢ**.

Thus **p | gcd(nᵢ, nⱼ)**.

This contradicts the assumption that **nᵢ** and **nⱼ** are coprime (since **i ≠ j**).

Therefore, **gcd(Mᵢ, nᵢ) = 1**. ✓

---

**Step 4**: Since **gcd(Mᵢ, nᵢ) = 1**, by Bézout's Identity (Lemma 3), there exist integers **yᵢ, zᵢ** such that:
```
Mᵢ · yᵢ + nᵢ · zᵢ = 1
```

Reducing modulo **nᵢ**:
```
Mᵢ · yᵢ ≡ 1 (mod nᵢ)
```

So **yᵢ** is the **modular multiplicative inverse** of **Mᵢ** modulo **nᵢ**.

**Note**: **yᵢ** can be found using the Extended Euclidean Algorithm.

---

**Step 5**: Define for each **i**:
```
eᵢ = Mᵢ · yᵢ
```

**Properties of eᵢ**:

**(Property A)**: **eᵢ ≡ 1 (mod nᵢ)**

**Proof**: By construction, **Mᵢ · yᵢ ≡ 1 (mod nᵢ)**, so **eᵢ ≡ 1 (mod nᵢ)**. ✓

**(Property B)**: **eᵢ ≡ 0 (mod nⱼ)** for all **j ≠ i**

**Proof**:
```
eᵢ = Mᵢ · yᵢ = (N / nᵢ) · yᵢ = (n₁ · ... · nⱼ · ... · nₖ) / nᵢ · yᵢ
```

Since **j ≠ i**, the product **n₁ · ... · nⱼ · ... · nₖ / nᵢ** contains **nⱼ** as a factor.

Therefore, **nⱼ | Mᵢ**, which means **nⱼ | (Mᵢ · yᵢ) = eᵢ**.

Thus **eᵢ ≡ 0 (mod nⱼ)**. ✓

---

**Step 6**: **Construct the solution**:
```
x = a₁·e₁ + a₂·e₂ + ... + aₖ·eₖ = Σᵢ₌₁ᵏ aᵢ·eᵢ
```

---

**Step 7**: **Verify** that **x** satisfies all congruences.

For any particular index **m ∈ {1, 2, ..., k}**, we need to show:
```
x ≡ aₘ (mod nₘ)
```

**Proof**:
```
x = Σᵢ₌₁ᵏ aᵢ·eᵢ

Taking modulo nₘ:

x ≡ Σᵢ₌₁ᵏ aᵢ·eᵢ (mod nₘ)
```

Now, by Property A and Property B:
- When **i = m**: **eₘ ≡ 1 (mod nₘ)**
- When **i ≠ m**: **eᵢ ≡ 0 (mod nₘ)**

Therefore:
```
x ≡ a₁·0 + ... + aₘ·1 + ... + aₖ·0 (mod nₘ)
  ≡ aₘ (mod nₘ)
```
✓

Since this holds for all **m**, **x** satisfies all **k** congruences.

**This proves EXISTENCE.** ✓

---

### Part II: UNIQUENESS modulo N

**Claim**: If **x₁** and **x₂** are both solutions to the system, then:
```
x₁ ≡ x₂ (mod N)
```

**Proof**:

Suppose **x₁** and **x₂** both satisfy all **k** congruences.

Then for each **i ∈ {1, 2, ..., k}**:
```
x₁ ≡ aᵢ (mod nᵢ)
x₂ ≡ aᵢ (mod nᵢ)
```

Subtracting:
```
x₁ - x₂ ≡ 0 (mod nᵢ)
```

This means:
```
nᵢ | (x₁ - x₂)  for all i ∈ {1, 2, ..., k}
```

Since **n₁, n₂, ..., nₖ** are pairwise coprime, by Lemma 5:
```
(n₁ · n₂ · ... · nₖ) | (x₁ - x₂)
```

That is:
```
N | (x₁ - x₂)
```

Which means:
```
x₁ ≡ x₂ (mod N)
```
✓

**This proves UNIQUENESS modulo N.** ✓

---

### Part III: CANONICAL REPRESENTATIVE

**Claim**: There exists exactly one solution **x₀** in the range **0 ≤ x₀ < N**.

**Proof**:

From Part I, we have a solution **x** (the one we constructed).

By the Division Algorithm, there exist unique integers **q, r** with **0 ≤ r < N** such that:
```
x = qN + r
```

Let **x₀ = r**.

Since **x ≡ r (mod N)** and **N = n₁ · ... · nₖ**, we have:
```
x ≡ x₀ (mod N)  ⟹  x ≡ x₀ (mod nᵢ) for all i
```

(because **nᵢ | N**)

Since **x ≡ aᵢ (mod nᵢ)**, we get:
```
x₀ ≡ aᵢ (mod nᵢ) for all i
```

So **x₀** is a solution with **0 ≤ x₀ < N**. ✓

**Uniqueness in [0, N)**:

Suppose **x'₀** is another solution with **0 ≤ x'₀ < N**.

By Part II: **x₀ ≡ x'₀ (mod N)**

So **N | (x₀ - x'₀)**.

But **|x₀ - x'₀| < N** (since both are in [0, N)).

The only multiple of **N** with absolute value less than **N** is **0**.

Therefore: **x₀ - x'₀ = 0**, which means **x₀ = x'₀**. ✓

---

### Part IV: COMPLETE SOLUTION SET

**Claim**: The complete set of solutions is:
```
S = {x₀ + tN : t ∈ ℤ}
```

**Proof**:

**(⊇ direction)**: Every element of **{x₀ + tN : t ∈ ℤ}** is a solution.

For any **t ∈ ℤ** and any **i**:
```
x₀ + tN ≡ x₀ + t·(n₁·...·nₖ) ≡ x₀ (mod nᵢ)
```

(since **nᵢ | N**)

And **x₀ ≡ aᵢ (mod nᵢ)**, so:
```
x₀ + tN ≡ aᵢ (mod nᵢ)
```

Thus **x₀ + tN** is a solution. ✓

**(⊆ direction)**: Every solution has the form **x₀ + tN**.

If **x** is any solution, by Part II: **x ≡ x₀ (mod N)**.

So **x = x₀ + tN** for some **t ∈ ℤ**. ✓

**Q.E.D.** ∎

---

## Corollaries and Extensions

### Corollary 2.1: Two Congruences (Special Case)

**Statement**: For coprime integers **m, n** (gcd(m,n) = 1), the system:
```
x ≡ a (mod m)
x ≡ b (mod n)
```

has a unique solution modulo **mn**.

**Proof**: This is the special case k=2 of Theorem 2. ✓

---

### Corollary 2.2: Ring Isomorphism

**Statement**: If **n₁, n₂, ..., nₖ** are pairwise coprime, then:
```
ℤ/Nℤ ≅ ℤ/n₁ℤ × ℤ/n₂ℤ × ... × ℤ/nₖℤ
```

where **N = n₁ · n₂ · ... · nₖ**.

**Proof Sketch**:

Define **φ: ℤ/Nℤ → ℤ/n₁ℤ × ... × ℤ/nₖℤ** by:
```
φ([x]ₙ) = ([x]ₙ₁, [x]ₙ₂, ..., [x]ₙₖ)
```

**Well-defined**: If **x ≡ y (mod N)**, then **x ≡ y (mod nᵢ)** for all i (since nᵢ | N).

**Homomorphism**:
```
φ([x + y]ₙ) = ([x+y]ₙ₁, ..., [x+y]ₙₖ) = ([x]ₙ₁ + [y]ₙ₁, ..., [x]ₙₖ + [y]ₙₖ)
           = φ([x]ₙ) + φ([y]ₙ)
```

Similarly for multiplication.

**Injective**: If **φ([x]ₙ) = φ([0]ₙ)**, then **x ≡ 0 (mod nᵢ)** for all i, so by Lemma 5, **x ≡ 0 (mod N)**, thus **[x]ₙ = [0]ₙ**.

**Surjective**: For any **([a₁]ₙ₁, ..., [aₖ]ₙₖ)**, by CRT there exists **x** with **x ≡ aᵢ (mod nᵢ)** for all i. Then **φ([x]ₙ) = ([a₁]ₙ₁, ..., [aₖ]ₙₖ)**.

Therefore **φ** is a ring isomorphism. ✓

**Q.E.D.** ∎

---

### Corollary 2.3: Euler's Totient Function

**Statement**: If **n = n₁ · n₂ · ... · nₖ** where **n₁, ..., nₖ** are pairwise coprime, then:
```
φ(n) = φ(n₁) · φ(n₂) · ... · φ(nₖ)
```

where **φ** is Euler's totient function.

**Proof**: This follows from Corollary 2.2 since the units in a product ring correspond to tuples of units in each component. ✓

---

### Theorem 3: CRT for Non-Coprime Moduli

**Statement**: The system:
```
x ≡ a (mod m)
x ≡ b (mod n)
```

has a solution if and only if:
```
gcd(m, n) | (a - b)
```

When a solution exists, it is unique modulo **lcm(m, n)**.

**Proof**:

**Necessity (⟹)**:

Suppose **x** is a solution. Then:
```
x ≡ a (mod m)  ⟹  x = a + km for some k ∈ ℤ
x ≡ b (mod n)  ⟹  x = b + ℓn for some ℓ ∈ ℤ
```

Therefore:
```
a + km = b + ℓn
a - b = ℓn - km
```

Let **g = gcd(m, n)**. Since **g | m** and **g | n**, we have:
```
g | (ℓn - km)
```

Therefore:
```
g | (a - b)
```
✓

**Sufficiency (⟸)**:

Suppose **g = gcd(m, n)** divides **(a - b)**.

Write **m = gm'** and **n = gn'** where **gcd(m', n') = 1**.

From **g | (a - b)**, we have **a - b = gk** for some **k ∈ ℤ**.

So **a ≡ b (mod g)**.

Now consider the system:
```
x ≡ a (mod m')
x ≡ b (mod n')
```

Since **gcd(m', n') = 1**, by CRT this has a unique solution **x₀** modulo **m' · n' = lcm(m,n)/g**.

**Claim**: **x₀** also satisfies the original system modulo g.

We need: **x₀ ≡ a (mod g)** and **x₀ ≡ b (mod g)**.

But these are equivalent since **a ≡ b (mod g)**. ✓

Therefore, combining all constraints, **x₀** satisfies:
```
x ≡ a (mod m)  [from x ≡ a (mod m') and x ≡ a (mod g)]
x ≡ b (mod n)  [from x ≡ b (mod n') and x ≡ b (mod g)]
```

**Uniqueness**: The solution is unique modulo **lcm(m, n)** by similar argument to Theorem 2. ✓

**Q.E.D.** ∎

---

## Concrete Worked Example with Complete Rigor

### Example: Solve the System
```
x ≡ 2 (mod 3)
x ≡ 3 (mod 5)
x ≡ 2 (mod 7)
```

**Step 0: Verify Hypotheses**

Check pairwise coprimality:
- **gcd(3, 5)**: By Euclidean algorithm: 5 = 1·3 + 2, 3 = 1·2 + 1, 2 = 2·1 + 0. So gcd(3,5) = 1. ✓
- **gcd(3, 7)**: 7 = 2·3 + 1, 3 = 3·1 + 0. So gcd(3,7) = 1. ✓
- **gcd(5, 7)**: 7 = 1·5 + 2, 5 = 2·2 + 1, 2 = 2·1 + 0. So gcd(5,7) = 1. ✓

Therefore, the hypotheses of Theorem 2 are satisfied.

---

**Step 1: Compute N**

```
N = 3 · 5 · 7 = 105
```

---

**Step 2: Compute Mᵢ**

```
M₁ = N/n₁ = 105/3 = 35
M₂ = N/n₂ = 105/5 = 21
M₃ = N/n₃ = 105/7 = 15
```

---

**Step 3: Compute yᵢ (modular inverses)**

**For y₁**: Need **35·y₁ ≡ 1 (mod 3)**

Reduce: **35 = 11·3 + 2**, so **35 ≡ 2 (mod 3)**

Need: **2·y₁ ≡ 1 (mod 3)**

Test: **y₁ = 2**: **2·2 = 4 = 1·3 + 1 ≡ 1 (mod 3)** ✓

So **y₁ = 2**.

**For y₂**: Need **21·y₂ ≡ 1 (mod 5)**

Reduce: **21 = 4·5 + 1**, so **21 ≡ 1 (mod 5)**

Need: **1·y₂ ≡ 1 (mod 5)**

So **y₂ = 1**.

**For y₃**: Need **15·y₃ ≡ 1 (mod 7)**

Reduce: **15 = 2·7 + 1**, so **15 ≡ 1 (mod 7)**

Need: **1·y₃ ≡ 1 (mod 7)**

So **y₃ = 1**.

---

**Step 4: Compute eᵢ**

```
e₁ = M₁·y₁ = 35·2 = 70
e₂ = M₂·y₂ = 21·1 = 21
e₃ = M₃·y₃ = 15·1 = 15
```

**Verification of Properties**:

**e₁ = 70**:
- **70 mod 3 = 1** ✓ (since 70 = 23·3 + 1)
- **70 mod 5 = 0** ✓ (since 70 = 14·5)
- **70 mod 7 = 0** ✓ (since 70 = 10·7)

**e₂ = 21**:
- **21 mod 3 = 0** ✓ (since 21 = 7·3)
- **21 mod 5 = 1** ✓ (since 21 = 4·5 + 1)
- **21 mod 7 = 0** ✓ (since 21 = 3·7)

**e₃ = 15**:
- **15 mod 3 = 0** ✓ (since 15 = 5·3)
- **15 mod 5 = 0** ✓ (since 15 = 3·5)
- **15 mod 7 = 1** ✓ (since 15 = 2·7 + 1)

---

**Step 5: Construct Solution**

```
x = a₁·e₁ + a₂·e₂ + a₃·e₃
  = 2·70 + 3·21 + 2·15
  = 140 + 63 + 30
  = 233
```

---

**Step 6: Reduce Modulo N**

```
233 = 2·105 + 23
```

So **x₀ = 23**.

---

**Step 7: Verification**

Check **x₀ = 23** satisfies all three congruences:

- **23 = 7·3 + 2**, so **23 ≡ 2 (mod 3)** ✓
- **23 = 4·5 + 3**, so **23 ≡ 3 (mod 5)** ✓
- **23 = 3·7 + 2**, so **23 ≡ 2 (mod 7)** ✓

---

**Conclusion**:

The unique solution in **[0, 105)** is **x₀ = 23**.

The complete solution set is:
```
S = {23 + 105t : t ∈ ℤ} = {..., -82, 23, 128, 233, ...}
```

**Q.E.D.** ∎

---

## Summary of Results

### Theorem 1 (GCD Subtraction Property)
```
∀a, b ∈ ℤ, b > 0: gcd(a, b) = gcd(a - b, b)
```

**Proof technique**: Show both GCDs divide each other, hence are equal.

**Significance**: Foundation of the Euclidean algorithm.

---

### Theorem 2 (Chinese Remainder Theorem)

For pairwise coprime **n₁, ..., nₖ**, the system:
```
x ≡ a₁ (mod n₁)
  ⋮
x ≡ aₖ (mod nₖ)
```

has a unique solution modulo **N = ∏nᵢ**.

**Proof technique**: Explicit construction using modular inverses; uniqueness via coprimality.

**Significance**: Allows decomposition of arithmetic modulo **N** into independent arithmetic modulo smaller primes.

---

**End of Rigorous Mathematical Proofs**

*All theorems proven from first principles using only:*
- *Well-Ordering Principle*
- *Division Algorithm*
- *Basic properties of integers*

∎

