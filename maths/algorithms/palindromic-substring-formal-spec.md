# Formal Mathematical Specification: Palindromic Substring Problem

## 1. Lamport-Style TLA+ Specification

### Basic Definitions

**Given:**
- A string S = s₁s₂...sₙ where sᵢ ∈ Σ (alphabet)
- Length n = |S|
- Index set I = {1, 2, ..., n}

**Define:**
```
IsPalindrome(i, j) ≜ 
  ∧ 1 ≤ i ≤ j ≤ n
  ∧ ∀k ∈ ℕ : (i + k ≤ j - k) ⇒ (sᵢ₊ₖ = sⱼ₋ₖ)
```

**Recurrence Relation:**
```
P(i, j) ≜ 
  CASE j - i OF
    0 → TRUE                           (single character)
    1 → (sᵢ = sⱼ)                      (two characters)
    _ → (sᵢ = sⱼ) ∧ P(i+1, j-1)       (general case)
```

---

## 2. Formal Logic Representation

### First-Order Logic

**Predicate Definition:**
```
Palindrome(S, i, j) ≡ 
  (i = j) ∨ 
  (i + 1 = j ∧ S[i] = S[j]) ∨
  (i < j ∧ S[i] = S[j] ∧ Palindrome(S, i+1, j-1))
```

**Optimization Problem:**
```
maximize L(i, j) = j - i + 1
subject to: Palindrome(S, i, j) = TRUE
            1 ≤ i ≤ j ≤ n
```

---

## 3. Dynamic Programming as State Transition

### State Space Definition

**State:** 
```
σ ∈ Σₛₜₐₜₑ = {0, 1}^(n×n)
where σ[i][j] represents P(i, j)
```

**Initial State:**
```
σ₀[i][j] = {
  1  if i = j
  ⊥  otherwise  (undefined)
}
```

**Transition Function:**
```
δ : Σₛₜₐₜₑ × (I × I) → Σₛₜₐₜₑ

δ(σ, (i, j)) = σ' where
  σ'[i][j] = {
    1  if (sᵢ = sⱼ) ∧ (j - i ≤ 1 ∨ σ[i+1][j-1] = 1)
    0  otherwise
  }
```

**Computation Order (Topological):**
```
Process pairs (i, j) in order of increasing length l = j - i + 1
∀l ∈ {1, 2, ..., n} : ∀i ∈ {1, ..., n-l+1} : compute P(i, i+l-1)
```

---

## 4. Set-Theoretic Formulation

**Define the set of all palindromic substrings:**
```
𝒫(S) = {(i, j) | 1 ≤ i ≤ j ≤ n ∧ IsPalindrome(i, j)}
```

**Longest palindromic substring:**
```
LPS(S) = argmax{(j - i + 1) | (i, j) ∈ 𝒫(S)}
```

**Count of palindromic substrings:**
```
Count(S) = |𝒫(S)| = |{(i, j) | (i, j) ∈ 𝒫(S)}|
```

---

## 5. Recursive Function Theory

**Function Signature:**
```
P : ℕ × ℕ → 𝔹
where 𝔹 = {⊤, ⊥} (Boolean domain)
```

**Base Cases:**
```
P(i, i) = ⊤                    ∀i ∈ [1, n]
P(i, i+1) = ⊤ ⟺ sᵢ = sᵢ₊₁     ∀i ∈ [1, n-1]
```

**Recursive Case:**
```
P(i, j) = {
  ⊤  if sᵢ = sⱼ ∧ P(i+1, j-1) = ⊤
  ⊥  otherwise
} for j - i ≥ 2
```

---

## 6. Memoization as Function Caching

**Pure Function:**
```
f : String × ℕ × ℕ → 𝔹
f(S, i, j) = IsPalindrome(S[i..j])
```

**Memoized Version:**
```
Let M : ℕ × ℕ ⇀ 𝔹 (partial function, initially empty)

f_memo(S, i, j) = {
  M[i, j]                           if (i, j) ∈ dom(M)
  M[i, j] ← f(S, i, j); M[i, j]    otherwise
}
```

---

## 7. Invariants and Correctness

### Loop Invariant

**For length l being processed:**
```
Inv(l) ≜ 
  ∧ ∀i, j : (j - i + 1 < l) ⇒ P(i, j) is correctly computed
  ∧ ∀i, j : (j - i + 1 = l) ∧ (processed(i, j)) ⇒ P(i, j) is correct
```

### Correctness Theorem

```
THEOREM: Palindrome_DP_Correct
  ASSUME: String S with length n
  PROVE:  ∀i, j ∈ [1, n] : i ≤ j ⇒ 
          (DP_Result[i][j] = 1) ⟺ IsPalindrome(S, i, j)
```

**Proof:** By induction on substring length l = j - i + 1

---

## 8. Complexity Analysis (Formal)

### Time Complexity

**Number of subproblems:**
```
T_space = |{(i, j) | 1 ≤ i ≤ j ≤ n}| = ∑ᵢ₌₁ⁿ (n - i + 1) = n(n+1)/2 = Θ(n²)
```

**Work per subproblem (WHY W(i,j) = Θ(1)):**

For each subproblem P(i, j), we perform:
```
W(i, j) = {
  c₁                          if j - i = 0  (base case check)
  c₂ + c₃                     if j - i = 1  (one comparison: sᵢ = sⱼ)
  c₄ + c₅ + c₆                if j - i ≥ 2  (comparison + two lookups)
}
```

Where:
- c₁ = cost of checking j - i = 0
- c₂ = cost of checking j - i = 1
- c₃ = cost of comparing sᵢ = sⱼ
- c₄ = cost of comparing sᵢ = sⱼ
- c₅ = cost of looking up P[i+1][j-1] (array access = O(1))
- c₆ = cost of AND operation

**Critical insight:** Because we've already computed P[i+1][j-1], we don't
recursively expand it. We just look it up in constant time O(1).

Without memoization: W(i, j) = Θ(2^(j-i))  (exponential - BAD!)
With memoization:    W(i, j) = Θ(1)        (constant - GOOD!)

**Total time:**
```
T(n) = ∑_{(i,j)} W(i, j) = Θ(n²) · Θ(1) = Θ(n²)
```

### Space Complexity

**DP Table:**
```
S(n) = Θ(n²)  (storing n² Boolean values)
```

**Space-optimized (for some variants):**
```
S_opt(n) = Θ(n)  (using only two previous diagonals)
```

---

## 9. Alternative: Manacher's Algorithm Formulation

**For odd-length palindromes centered at position c:**
```
R[c] = max{r | ∀k ∈ [0, r] : s_{c-k} = s_{c+k}}
```

**Recurrence with symmetry exploitation:**
```
R[c] = {
  min(R[2·mirror - c], mirror + R[mirror] - c)  if c < mirror + R[mirror]
  0                                                otherwise
} + expand_around_center(c)
```

**Time complexity:** Θ(n) due to amortized expansion

---

## 10. Summary: Key Mathematical Objects

| Aspect | Mathematical Representation |
|--------|---------------------------|
| **State** | σ ∈ {0,1}^(n×n) |
| **Predicate** | P : ℕ × ℕ → 𝔹 |
| **Recurrence** | P(i,j) = (sᵢ=sⱼ) ∧ P(i+1,j-1) |
| **Solution Set** | 𝒫(S) = {(i,j) \| P(i,j)} |
| **Objective** | max{j-i+1 \| (i,j) ∈ 𝒫(S)} |
| **Complexity** | T(n) ∈ Θ(n²), S(n) ∈ Θ(n²) |

