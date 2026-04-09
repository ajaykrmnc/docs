# Deep Mathematical Analysis: Palindromic Substring Dynamic Programming

## Part I: Foundation & Problem Definition

### 1.1 Formal Problem Statement

**Definition 1.1 (Alphabet and String):**
```
Let Σ be a finite alphabet.
A string S over Σ is a finite sequence S = s₁s₂...sₙ where sᵢ ∈ Σ.
The length of S is |S| = n.
```

**Definition 1.2 (Substring):**
```
A substring S[i..j] is the contiguous sequence sᵢsᵢ₊₁...sⱼ where 1 ≤ i ≤ j ≤ n.
The set of all substrings is:
  SUB(S) = {S[i..j] | 1 ≤ i ≤ j ≤ n}
```

**Definition 1.3 (Reverse):**
```
The reverse of string S, denoted S^R, is:
  S^R = sₙsₙ₋₁...s₂s₁
```

**Definition 1.4 (Palindrome - Formal):**
```
A string S is a palindrome iff S = S^R
Equivalently: ∀k ∈ [1, ⌊n/2⌋] : sₖ = sₙ₋ₖ₊₁
```

**Problem:** Given string S, find all pairs (i, j) such that S[i..j] is a palindrome.

---

### 1.2 Why This is Non-Trivial

**Naive Approach Complexity:**
```
For each substring (i, j):  O(n²) substrings
  Check if palindrome:      O(n) comparison
Total: O(n³)
```

**Question:** Can we do better? **Answer:** Yes! Using optimal substructure.

---

## Part II: Mathematical Structure of Palindromes

### 2.1 Optimal Substructure Property

**Theorem 2.1 (Optimal Substructure):**
```
S[i..j] is a palindrome ⟺
  (sᵢ = sⱼ) ∧ S[i+1..j-1] is a palindrome
```

**Proof:**
```
(⟹) Forward direction:
  Assume S[i..j] is a palindrome.
  Then ∀k : sᵢ₊ₖ = sⱼ₋ₖ

  For k = 0: sᵢ = sⱼ ✓

  For k ∈ [1, ⌊(j-i)/2⌋]:
    sᵢ₊ₖ = sⱼ₋ₖ
    Let i' = i+1, j' = j-1, k' = k-1
    Then sᵢ'₊ₖ' = sⱼ'₋ₖ'
    Therefore S[i+1..j-1] is a palindrome ✓

(⟸) Backward direction:
  Assume sᵢ = sⱼ and S[i+1..j-1] is a palindrome.

  S[i+1..j-1] palindrome means:
    ∀k ∈ [0, ⌊(j-i-2)/2⌋] : sᵢ₊₁₊ₖ = sⱼ₋₁₋ₖ

  For S[i..j], need to show ∀k : sᵢ₊ₖ = sⱼ₋ₖ

  k = 0: sᵢ = sⱼ (given) ✓
  k > 0: sᵢ₊ₖ = s₍ᵢ₊₁₎₊₍ₖ₋₁₎ = sⱼ₋₁₋₍ₖ₋₁₎ = sⱼ₋ₖ ✓

  Therefore S[i..j] is a palindrome. □
```

**Corollary 2.1:** This allows recursive decomposition - the heart of DP!

---

### 2.2 Base Cases - Mathematical Necessity

**Lemma 2.2 (Single Character):**
```
∀i ∈ [1, n] : S[i..i] is always a palindrome
```

**Proof:** Trivial. A single character equals its reverse. □

**Lemma 2.3 (Two Characters):**
```
S[i..i+1] is a palindrome ⟺ sᵢ = sᵢ₊₁
```

**Proof:**
```
S[i..i+1] = sᵢsᵢ₊₁
(S[i..i+1])^R = sᵢ₊₁sᵢ
S[i..i+1] = (S[i..i+1])^R ⟺ sᵢ = sᵢ₊₁ □
```

**Why we need explicit base cases:**
```
For S[i..i+1], the recursion would check:
  P(i, i+1) = (sᵢ = sᵢ₊₁) ∧ P(i+1, i)

But P(i+1, i) is undefined (i+1 > i violates i ≤ j).
Therefore, j - i ≤ 1 must be handled as base cases.
```

---

## Part III: The Recurrence Relation - Deep Dive

### 3.1 Complete Mathematical Definition

**Definition 3.1 (Palindrome Predicate Function):**
```
P : [1,n] × [1,n] → {0, 1}

P(i, j) = ⎧ 1                                    if i = j
           ⎪ [sᵢ = sⱼ]                          if j = i + 1
           ⎨ [sᵢ = sⱼ] ∧ P(i+1, j-1)           if j > i + 1
           ⎪ undefined                           if i > j
           ⎩
```

Where [condition] = 1 if condition is true, 0 otherwise (Iverson bracket).

---

### 3.2 Dependency Graph

**Definition 3.2 (Dependency DAG):**
```
Let G = (V, E) where:
  V = {(i, j) | 1 ≤ i ≤ j ≤ n}
  E = {((i, j), (i+1, j-1)) | j > i + 1}
```

---

### 4.2 Work Analysis WITH Memoization (Dynamic Programming)

**DP Solution:**
```python
# Assume dp[i][j] is already computed for all dependencies
def compute_palindrome_dp(i, j):
    if i == j:
        dp[i][j] = 1              # c₁ operations
    elif j == i + 1:
        dp[i][j] = (s[i] == s[j]) # c₂ operations
    else:
        dp[i][j] = (s[i] == s[j]) and dp[i+1][j-1]  # c₃ operations
```

**Critical observation:**
```
The line: dp[i][j] = (s[i] == s[j]) and dp[i+1][j-1]

Performs exactly:
1. Array access s[i]:        O(1)
2. Array access s[j]:        O(1)
3. Comparison s[i] == s[j]:  O(1)
4. Array access dp[i+1][j-1]: O(1)  ← KEY! This is a LOOKUP, not recursion
5. Boolean AND:              O(1)
6. Array assignment:         O(1)

Total: O(1) = Θ(1)
```

**Mathematical formalization:**
```
Let M : [1,n] × [1,n] → {0,1} be the memoization table.

W_DP(i, j | M) = {
  c₁                                    if (i,j) ∈ dom(M)  (already computed)
  c₂ + lookup_cost(M, i+1, j-1)        otherwise
}

Since M is implemented as a 2D array:
  lookup_cost(M, i+1, j-1) = Θ(1)

Therefore: W_DP(i, j | M) = Θ(1) for all (i,j)
```

**Total work for DP:**
```
T_DP = ∑_{all (i,j)} W_DP(i, j)
     = |{(i,j) | 1 ≤ i ≤ j ≤ n}| · Θ(1)
     = (n² + n)/2 · Θ(1)
     = Θ(n²)                            GOOD!
```

---

### 4.3 The Power of Memoization - Formal Analysis

**Definition 4.1 (Overlapping Subproblems):**
```
A problem exhibits overlapping subproblems if the same subproblem
is encountered multiple times in the naive recursive solution.
```

**Example:**
```
Computing P(1, 5) and P(2, 6) both require P(2, 5).
Without memoization: P(2, 5) computed twice.
With memoization: P(2, 5) computed once, looked up once.
```

**Theorem 4.1 (Memoization Efficiency):**
```
Let R(n) = number of distinct subproblems
Let C(n) = number of times subproblems are called without memoization

Without memo: T = C(n) · cost_per_call
With memo:    T = R(n) · cost_per_computation

For palindrome: R(n) = Θ(n²), cost_per_computation = Θ(1)
Therefore: T_memo = Θ(n²)
```

---

## Part V: Counting Arguments - Combinatorial Analysis

### 5.1 Number of Subproblems

**Theorem 5.1:**
```
The number of subproblems is exactly n(n+1)/2.
```

**Proof (Combinatorial):**
```
Each subproblem corresponds to choosing a pair (i, j) with i ≤ j.

Method 1: Direct counting
  For each i ∈ [1, n], j can be chosen from {i, i+1, ..., n}
  Count_i = n - i + 1

  Total = ∑ᵢ₌₁ⁿ (n - i + 1)
        = ∑ₖ₌₁ⁿ k                (substituting k = n - i + 1)
        = n(n + 1)/2

Method 2: Binomial coefficient
  We need to choose 2 positions from n with repetition allowed,
  and order matters (i before j), but i ≤ j.

  This is equivalent to: C(n+1, 2) = (n+1)!/[2!(n-1)!] = n(n+1)/2 □
```

---

### 5.2 Subproblems by Length

**Theorem 5.2 (Length Distribution):**
```
For each length l ∈ [1, n], the number of subproblems of length l is n - l + 1.
```

**Proof:**
```
For fixed length l, we have j - i + 1 = l, so j = i + l - 1.

Valid values of i: must satisfy 1 ≤ i and i + l - 1 ≤ n
  1 ≤ i ≤ n - l + 1

Count = n - l + 1 □
```

**Verification:**
```
∑ₗ₌₁ⁿ (n - l + 1) = ∑ₖ₌₁ⁿ k = n(n+1)/2 ✓
```

**Computational Order:**
```
Length l=1: n subproblems     (all base cases)
Length l=2: n-1 subproblems
Length l=3: n-2 subproblems
...
Length l=n: 1 subproblem      (entire string)

Total: n + (n-1) + (n-2) + ... + 1 = n(n+1)/2
```

---

## Part VI: Space Complexity Analysis

### 6.1 Full DP Table

**Theorem 6.1:**
```
The space complexity of the standard DP solution is Θ(n²).
```

**Proof:**
```
We store a 2D table M[1..n][1..n].
Only entries where i ≤ j are used.

Used entries: n(n+1)/2 = Θ(n²)
Wasted entries: n(n-1)/2 = Θ(n²) (where i > j)

Total allocated: n² = Θ(n²) □
```

---

### 6.2 Space Optimization

**Observation:**
```
P(i, j) only depends on P(i+1, j-1).
This is a diagonal dependency pattern.
```

**Theorem 6.2 (Diagonal Dependency):**
```
When processing by increasing length l:
  - Computing all subproblems of length l
  - Only requires subproblems of length l-2 (already computed)
  - Can discard subproblems of length l-3 and smaller
```

**Space-Optimized Approach:**
```
Keep only 2 diagonals:
  - Current diagonal (length l)
  - Previous diagonal (length l-2)

Space = 2n = Θ(n)
```

**Trade-off:**
```
Standard DP: Space Θ(n²), easy to reconstruct all palindromes
Optimized:   Space Θ(n), harder to track all palindromes
```

---

## Part VII: Correctness Proof

### 7.1 Loop Invariant

**Definition 7.1 (Processed Set):**
```
After processing all substrings of length ≤ l:
  Processed(l) = {(i, j) | j - i + 1 ≤ l}
```

**Invariant 7.1:**
```
Inv(l) ≜ ∀(i, j) ∈ Processed(l) :
  P(i, j) = 1 ⟺ S[i..j] is a palindrome
```

**Proof by Induction:**

**Base case (l = 1):**
```
All substrings of length 1 are single characters.
P(i, i) = 1 for all i.
All single characters are palindromes.
Inv(1) holds. ✓
```

**Inductive step:**
```
Assume Inv(l-1) holds.
Prove Inv(l) holds.

Consider any (i, j) with j - i + 1 = l.

Case 1: l = 2
  P(i, i+1) = [sᵢ = sᵢ₊₁]
  S[i..i+1] = sᵢsᵢ₊₁ is palindrome ⟺ sᵢ = sᵢ₊₁
  Therefore P(i, i+1) correct. ✓

Case 2: l > 2
  We compute: P(i, j) = [sᵢ = sⱼ] ∧ P(i+1, j-1)

  Note: j-1 - (i+1) + 1 = l - 2 < l
  So (i+1, j-1) ∈ Processed(l-1)

  By IH: P(i+1, j-1) = 1 ⟺ S[i+1..j-1] is palindrome

  By Theorem 2.1:
    S[i..j] palindrome ⟺ sᵢ = sⱼ ∧ S[i+1..j-1] palindrome
                        ⟺ [sᵢ = sⱼ] = 1 ∧ P(i+1, j-1) = 1
                        ⟺ P(i, j) = 1

  Therefore P(i, j) correct. ✓

By induction, Inv(n) holds, proving correctness. □
```

---

## Part VIII: Advanced Topics

### 8.1 Generating Function Approach

**Definition 8.1:**
```
Let pₙ = number of palindromes in a random string of length n over alphabet Σ.

Expected value: E[pₙ] = ∑_{i,j} Pr[S[i..j] is palindrome]
```

**For uniform random strings over alphabet size σ:**
```
Pr[S[i..j] palindrome] = σ^(-⌊(j-i+1)/2⌋)

E[pₙ] = ∑ₗ₌₁ⁿ (n-l+1) · σ^(-⌊l/2⌋)
```

**For large n and σ = 2 (binary):**
```
E[pₙ] ≈ 2n (approximately 2n palindromes expected)
```

---

### 8.2 Information-Theoretic View

**Entropy of palindrome structure:**
```
H(Palindrome) = -∑ₚ P(p) log₂ P(p)

For a palindrome of length l:
  - Only first ⌈l/2⌉ characters are "free"
  - Remaining characters determined

Information content: ⌈l/2⌉ · log₂(σ) bits
Regular string: l · log₂(σ) bits

Palindromes have ~50% redundancy!
```

---

## Part IX: Comparison with Other Approaches

### 9.1 Comparison Table

| Approach | Time | Space | Description |
|----------|------|-------|-------------|
| Brute Force | Θ(n³) | Θ(1) | Check each substring |
| DP (this) | Θ(n²) | Θ(n²) | Memoized recurrence |
| DP Optimized | Θ(n²) | Θ(n) | Space-efficient DP |
| Manacher's | Θ(n) | Θ(n) | Linear time algorithm |

**Why DP beats brute force:**
```
Brute force: Recomputes inner palindrome checks
DP: Each subproblem solved exactly once
Speedup: n³/n² = n times faster!
```

---

### 9.2 Manacher's Algorithm - Mathematical Insight

**Key observation:** Palindromes have symmetry we can exploit.

**Radius function:**
```
R[c] = max{r | S[c-r..c+r] is a palindrome}
```

**Mirror property:**
```
If S[L..R] is a palindrome with center C:
  For any position i within [L, R]:
  R[i] ≥ min(R[2C - i], R - i)
```

This allows amortized O(1) expansion, giving O(n) total time!

---

## Part X: Summary and Key Takeaways

### 10.1 Why W(i,j) = Θ(1) - Final Answer

**The fundamental reason:**
```
1. We process subproblems in topological order (by increasing length)
2. When computing P(i, j), all dependencies are ALREADY computed
3. Looking up dp[i+1][j-1] is array indexing = O(1)
4. Character comparison s[i] == s[j] is O(1)
5. Boolean AND is O(1)

Therefore: W(i, j) = O(1) + O(1) + O(1) = Θ(1)
```

**Without memoization:**
```
W(i, j) = Θ(j - i) because we recursively expand
With memoization: W(i, j) = Θ(1) because we just look up!
```

**This is the power of dynamic programming!**

---

### 10.2 The Mathematics Behind DP

**Three pillars:**
```
1. Optimal substructure: P(i,j) = (sᵢ=sⱼ) ∧ P(i+1,j-1)
2. Overlapping subproblems: Same subproblems reused
3. Topological ordering: Ensures dependencies satisfied
```

**Result:**
```
Transform exponential recursion → polynomial iteration
O(2ⁿ) → O(n²)
```

---

### 10.3 Mathematical Beauty

**Palindrome DP exhibits:**
```
- Elegant recurrence relation
- Clear dependency structure (DAG)
- Perfect example of optimal substructure
- Natural topological ordering
- Information-theoretic redundancy
- Symmetry properties
```

**This makes it a pedagogically perfect example for teaching:**
- Dynamic programming
- Recurrence relations
- Complexity analysis
- Memoization vs recursion
- DAG processing

---

## Appendix A: Complete Algorithm Pseudocode

```
Algorithm: PalindromeDP(S[1..n])
Input: String S of length n
Output: Boolean table P[1..n][1..n] where P[i][j] = 1 iff S[i..j] is palindrome

1. Initialize P[1..n][1..n] with all zeros
2.
3. // Base case: single characters
4. for i ← 1 to n do
5.     P[i][i] ← 1
6.
7. // Process by increasing length
8. for length ← 2 to n do
9.     for i ← 1 to n - length + 1 do
10.        j ← i + length - 1
11.
12.        if length = 2 then
13.            P[i][j] ← [S[i] = S[j]]
14.        else
15.            P[i][j] ← [S[i] = S[j]] ∧ P[i+1][j-1]
16.
17. return P

Time Complexity: Θ(n²)
Space Complexity: Θ(n²)
Correctness: Proved by induction on length (Section VII)
```

---

## Appendix B: Common Variants

### B.1 Count All Palindromic Substrings
```
count = 0
for i ← 1 to n do
    for j ← i to n do
        if P[i][j] = 1 then
            count ← count + 1
return count

Time: Θ(n²) (table already computed)
```

### B.2 Find Longest Palindromic Substring
```
maxLen ← 0
start ← 1

for i ← 1 to n do
    for j ← i to n do
        if P[i][j] = 1 and (j - i + 1) > maxLen then
            maxLen ← j - i + 1
            start ← i

return S[start..start+maxLen-1]

Time: Θ(n²)
```

### B.3 Check if Entire String is Palindrome
```
return P[1][n]

Time: Θ(1) (after DP table computed)
```

---

## Appendix C: Mathematical Notation Reference

| Symbol | Meaning |
|--------|---------|
| Σ | Alphabet (set of characters) |
| n | Length of string |
| S[i..j] | Substring from index i to j |
| P(i,j) | Boolean: is S[i..j] a palindrome? |
| Θ(f(n)) | Tight asymptotic bound |
| ⊤, ⊥ | True, False (Boolean values) |
| ∀ | For all (universal quantifier) |
| ∃ | There exists (existential quantifier) |
| ∧ | Logical AND |
| ∨ | Logical OR |
| ⟹ | Implies |
| ⟺ | If and only if (iff) |
| [condition] | Iverson bracket: 1 if true, 0 if false |
| ∑ | Summation |
| ∏ | Product |
| □ | End of proof (Q.E.D.) |

---

**End of Deep Mathematical Analysis**
```
Suppose there's a cycle: (i₁, j₁) → (i₂, j₂) → ... → (iₖ, jₖ) → (i₁, j₁)

By edge definition: iₘ₊₁ = iₘ + 1 and jₘ₊₁ = jₘ - 1

After k steps:
  i₁ + k = i₁  ⟹ k = 0
  j₁ - k = j₁  ⟹ k = 0

Therefore, no non-trivial cycles exist. G is a DAG. □
```

**Corollary 3.1:** Topological ordering exists for computing P(i, j).

---

### 3.3 Topological Order by Length

**Theorem 3.2 (Length-Based Ordering):**
```
Define length function: L(i, j) = j - i + 1

Process (i, j) in increasing order of L(i, j) guarantees
that P(i+1, j-1) is computed before P(i, j).
```

**Proof:**
```
For any edge (i, j) → (i+1, j-1):
  L(i+1, j-1) = (j-1) - (i+1) + 1 = j - i - 1
  L(i, j) = j - i + 1

  L(i+1, j-1) = L(i, j) - 2 < L(i, j)

Therefore, processing by increasing length ensures all
dependencies are satisfied. □
```

---

## Part IV: Why W(i,j) = Θ(1) - The Critical Insight

### 4.1 Work Analysis Without Memoization

**Naive Recursive Solution:**
```python
def is_palindrome(i, j):
    if i >= j:
        return True
    if s[i] != s[j]:
        return False
    return is_palindrome(i+1, j-1)  # RECURSIVE CALL
```

**Recurrence for work:**
```
W_naive(i, j) = {
  c₁                           if j - i ≤ 1
  c₂ + W_naive(i+1, j-1)      if j > i + 1
}
```

**Solution:**
```
W_naive(i, j) = Θ(j - i) = Θ(n) for a substring of length n
```

**Total work for all substrings:**
```
T_naive = ∑ᵢ₌₁ⁿ ∑ⱼ₌ᵢⁿ W_naive(i, j)
        = ∑ᵢ₌₁ⁿ ∑ⱼ₌ᵢⁿ Θ(j - i)
        = ∑ᵢ₌₁ⁿ ∑ₗ₌₀ⁿ⁻ⁱ Θ(l)        (substituting l = j - i)
        = Θ(∑ᵢ₌₁ⁿ n²)
        = Θ(n³)                      BAD!
```

