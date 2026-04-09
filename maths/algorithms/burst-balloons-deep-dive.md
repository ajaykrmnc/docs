# Deep Mathematical Analysis: Burst Balloons Dynamic Programming

## Part I: Foundation & Problem Definition

### 1.1 Formal Problem Statement

**Definition 1.1 (Balloon Array):**
```
Let nums = [n₁, n₂, ..., nₖ] where nᵢ ∈ ℕ⁺ (positive integers)
Each nᵢ represents the value of balloon i.
```

**Definition 1.2 (Bursting Operation):**
```
When balloon i is burst:
  - It is removed from the array
  - Adjacent balloons become neighbors
  - Coins earned = left_neighbor × nums[i] × right_neighbor
```

**Definition 1.3 (Boundary Conditions):**
```
If balloon i has no left neighbor → left_neighbor = 1
If balloon i has no right neighbor → right_neighbor = 1

This is implemented by extending the array:
A = [1, n₁, n₂, ..., nₖ, 1]
where A[0] = A[k+1] = 1 are virtual balloons.
```

**Definition 1.4 (Burst Sequence):**
```
A burst sequence is a permutation π of {1, 2, ..., k}
π = (πᵢ, π₂, ..., πₖ) means:
  - First burst balloon at index π₁
  - Second burst balloon at index π₂
  - ...
  - Last burst balloon at index πₖ
```

**Problem:** Find the burst sequence that maximizes total coins.

---

### 1.2 Why This is Hard

**Naive approach:**
```
Try all k! permutations: O(k!)
For each permutation, simulate bursting: O(k)
Total: O(k! × k) — EXPONENTIAL!
```

**Why greedy fails:**
```
Example: nums = [3, 1, 5, 8]

Greedy (burst lowest first):
  Burst 1 (index 1): 3 × 1 × 5 = 15
  Remaining: [3, 5, 8]
  Burst 3: 1 × 3 × 5 = 15
  Burst 5: 1 × 5 × 8 = 40
  Burst 8: 1 × 8 × 1 = 8
  Total: 15 + 15 + 40 + 8 = 78

Optimal sequence:
  Burst 1: 3 × 1 × 5 = 15
  Burst 5: 3 × 5 × 8 = 120
  Burst 3: 1 × 3 × 8 = 24
  Burst 8: 1 × 8 × 1 = 8
  Total: 15 + 120 + 24 + 8 = 167

Greedy gives suboptimal solution!
```

---

## Part II: The Key Insight - Think BACKWARDS!

### 2.1 Why "First Balloon" Doesn't Work

**Attempt: Choose which balloon to burst FIRST**

**Problem:**
```
If we burst balloon k first:
  - Left subarray: [1..k-1]
  - Right subarray: [k+1..n]

But what are the boundaries of these subarrays?

After bursting k:
  - Element k-1 and k+1 are now adjacent
  - Future bursts in left array affect right array and vice versa!
  - Subproblems are NOT independent
```

**Mathematical formalization:**
```
Let F(i, j) = max coins bursting balloons [i..j]

If we burst k ∈ [i, j] FIRST:
  Coins from k: ???  (depends on what remains later!)
  F(i, j) = ??? + F(i, k-1) + F(k+1, j)

Problem: When computing F(i, k-1) and F(k+1, j),
        their boundary values are undefined!
```

---

### 2.2 The Brilliant Trick - Think LAST!

**Insight:** Choose which balloon to burst LAST instead!

**Why this works:**
```
If balloon k is the LAST to burst in interval (i, j):

Before bursting k:
  - ALL balloons in (i, k) have been burst
  - ALL balloons in (k, j) have been burst
  - Only balloons i, k, j remain

Coins from bursting k: A[i] × A[k] × A[j]

Total coins:
  = coins from bursting (i, k) + coins from bursting (k, j) + A[i]×A[k]×A[j]
  = M(i, k) + M(k, j) + A[i]×A[k]×A[j]
```

**Critical property:**
```
M(i, k) and M(k, j) are INDEPENDENT!

When computing M(i, k):
  - We assume balloons i and k are boundaries
  - Don't care about anything outside (i, k)

When computing M(k, j):
  - We assume balloons k and j are boundaries
  - Don't care about anything outside (k, j)

This independence allows dynamic programming!
```

---

### 2.3 Formal Optimal Substructure Theorem



**Topological Order:**
```
Process by increasing gap g = j - i:
  g = 1: All base cases
  g = 2: One balloon between boundaries
  g = 3: Two balloons between boundaries
  ...
  g = k+1: All k balloons (final answer)
```

---

## Part IV: Why W(i,j) = Θ(gap) - The Critical Analysis

### 4.1 Work Without Memoization

**Naive Recursive Solution:**
```python
def maxCoins(i, j):
    if j - i <= 1:
        return 0

    result = 0
    for k in range(i+1, j):
        left = maxCoins(i, k)      # RECURSIVE CALL
        right = maxCoins(k, j)     # RECURSIVE CALL
        coins = A[i] * A[k] * A[j] + left + right
        result = max(result, coins)
    return result
```

**Recurrence for work:**
```
W_naive(i, j) = {
  c₁                                      if j - i ≤ 1
  ∑ₖ₌ᵢ₊₁ʲ⁻¹ (c₂ + W_naive(i,k) + W_naive(k,j))  otherwise
}
```

**This is exponential!**
```
W_naive(i, j) = Θ(2^(j-i)) without memoization
```

---

### 4.2 Work WITH Memoization (Dynamic Programming)

**DP Solution:**
```python
# Assume dp[i][j] already computed for all smaller gaps
def compute_dp(i, j):
    result = 0
    for k in range(i+1, j):           # Loop over k values
        coins = A[i] * A[k] * A[j]    # O(1)
        coins += dp[i][k]              # O(1) LOOKUP, not recursion!
        coins += dp[k][j]              # O(1) LOOKUP, not recursion!
        result = max(result, coins)    # O(1)
    dp[i][j] = result
```

**Critical observation:**
```
The loop: for k in range(i+1, j)

Iterations: j - i - 1 times

For each iteration:
  1. Compute A[i] × A[k] × A[j]:  O(1)
  2. Lookup dp[i][k]:              O(1)  ← KEY! This is LOOKUP!
  3. Lookup dp[k][j]:              O(1)  ← KEY! This is LOOKUP!
  4. Addition:                      O(1)
  5. Max comparison:                O(1)

Work per iteration: Θ(1)
Number of iterations: j - i - 1 = Θ(j - i)

Total work: Θ(j - i) × Θ(1) = Θ(j - i)
```

**Mathematical formalization:**
```
Let M : [0,k+1] × [0,k+1] → ℕ be the memoization table.

W_DP(i, j | M) = {
  c₁                                    if (i,j) ∈ dom(M)  (already computed)
  c₂ × (j - i - 1)                     otherwise
}

where c₂ = cost of one iteration (constant)

Since we compute each (i,j) once:
  W_DP(i, j) = Θ(j - i) for first computation
```

---

### 4.3 Why Can't We Make W(i,j) = Θ(1)?

**Comparison with Palindrome:**

**Palindrome:**
```
P(i, j) = [s[i] = s[j]] ∧ P(i+1, j-1)

Dependencies: Exactly 1 subproblem (i+1, j-1)
Work: O(1) comparison + O(1) lookup = Θ(1)
```

**Burst Balloons:**
```
M(i, j) = max{A[i]×A[k]×A[j] + M(i,k) + M(k,j) | k ∈ (i,j)}

Dependencies: (j-i-1) subproblems — one for EACH k!
Work: Must try ALL k values = Θ(j - i)
```

**Why we can't avoid trying all k:**
```
Each k gives a DIFFERENT value!

We can't predict which k is optimal without trying all.

Unlike palindrome where the subproblem is deterministic
(always i+1, j-1), here the optimal k varies.
```

**Fundamental difference:**
```
Palindrome: Fixed dependency structure
  P(i,j) → P(i+1,j-1)  (one edge)

Burst Balloons: Variable dependency structure
  M(i,j) → M(i,k) and M(k,j) for ALL k ∈ (i,j)
            (2×(j-i-1) edges)
```

---

### 4.4 Total Time Complexity Derivation

**Number of subproblems:**
```
|{(i,j) | 0 ≤ i < j ≤ k+1}| = C(k+2, 2) = (k+2)(k+1)/2 = Θ(k²)
```

**Work per subproblem:**
```
For M(i,j) with gap g = j - i:
  W(i,j) = Θ(g)
```

**Total work:**
```
T(k) = ∑_{all (i,j)} W(i,j)
     = ∑_{g=2}^{k+1} ∑_{i=0}^{k+1-g} Θ(g)
     = ∑_{g=2}^{k+1} (k+2-g) × Θ(g)
     = Θ(∑_{g=2}^{k+1} g(k+2-g))
     = Θ(∑_{g=2}^{k+1} (kg + 2g - g²))
```

**Simplifying:**
```
∑_{g=2}^{k+1} (kg + 2g - g²)
  = k × ∑_{g=2}^{k+1} g + 2 × ∑_{g=2}^{k+1} g - ∑_{g=2}^{k+1} g²

  ∑_{g=2}^{k+1} g ≈ k²/2
  ∑_{g=2}^{k+1} g² ≈ k³/3

  = k × (k²/2) + 2 × (k²/2) - (k³/3)
  = k³/2 + k² - k³/3
  = k³(1/2 - 1/3) + k²
  = k³/6 + k²
  = Θ(k³)
```

**Therefore: T(k) = Θ(k³)**

---

## Part V: Detailed Counting Arguments

### 5.1 Number of Subproblems by Gap

**Theorem 5.1:**
```
For each gap g ∈ [1, k+1], there are exactly (k+2-g) subproblems.
```

**Proof:**
```
For fixed gap g, we have j = i + g.

Valid values of i:
  0 ≤ i and i + g ≤ k+1
  0 ≤ i ≤ k+1-g

Count = (k+1-g) - 0 + 1 = k+2-g □
```

**Verification:**
```
∑_{g=1}^{k+1} (k+2-g) = ∑_{m=1}^{k+1} m = (k+1)(k+2)/2 ✓
```

**Distribution:**
```
Gap g=1:   k+1 subproblems (all base cases)
Gap g=2:   k   subproblems
Gap g=3:   k-1 subproblems
...
Gap g=k+1: 1   subproblem (entire array)
```

---

### 5.2 Work Distribution

**Theorem 5.2:**
```
Total work = ∑_{g=1}^{k+1} (k+2-g) × O(g) = Θ(k³)
```

**Proof:**
```
W_total = ∑_{g=1}^{k+1} (number of subproblems with gap g) × (work per subproblem)
        = ∑_{g=1}^{k+1} (k+2-g) × g

Let's compute exactly:
  = ∑_{g=1}^{k+1} (kg + 2g - g²)
  = k∑g + 2∑g - ∑g²
  = k × (k+1)(k+2)/2 + 2 × (k+1)(k+2)/2 - (k+1)(k+2)(2k+3)/6
  = (k+1)(k+2)/2 × (k + 2 - (2k+3)/3)
  = (k+1)(k+2)/2 × (3k + 6 - 2k - 3)/3
  = (k+1)(k+2)/2 × (k+3)/3
  = (k+1)(k+2)(k+3)/6
  = O(k³)  □
```

---

### 5.3 Comparison of Work Across Different Gaps

**Example: k = 10**

```
Gap  | Subproblems | Work/Sub | Total Work
-----|-------------|----------|------------
 1   |     11      |   O(1)   |    11
 2   |     10      |   O(2)   |    20
 3   |      9      |   O(3)   |    27
 4   |      8      |   O(4)   |    32
 5   |      7      |   O(5)   |    35
 6   |      6      |   O(6)   |    36
 7   |      5      |   O(7)   |    35
 8   |      4      |   O(8)   |    32
 9   |      3      |   O(9)   |    27
10   |      2      |  O(10)   |    20
11   |      1      |  O(11)   |    11

Total: 286 = (10+1)(10+2)(10+3)/6 = 11×12×13/6 = 286 ✓
```

**Observation:**
```
Middle gaps contribute most work!
Gap ≈ k/2 has maximum total work per gap.
```

---

## Part VI: Space Complexity

### 6.1 DP Table Structure

**Storage:**
```
dp[0..k+1][0..k+1]
Total cells: (k+2)²
Used cells: C(k+2, 2) = (k+2)(k+1)/2 (where i < j)
```

**Space complexity: S(k) = Θ(k²)**

---

### 6.2 Why We Can't Optimize Space to O(k)

**Palindrome could optimize because:**
```
P(i, j) only depends on P(i+1, j-1)
Dependencies form a diagonal pattern.
Can keep only 2 diagonals.
```

**Burst Balloons cannot optimize because:**
```
M(i, j) depends on:
  - M(i, i+1), M(i, i+2), ..., M(i, j-1)  (entire row from i)
  - M(i+1, j), M(i+2, j), ..., M(j-1, j)  (entire column to j)

Cannot discard previous rows/columns!
Need to keep entire table.
```

**Dependency pattern:**
```
M[i][j] depends on:
  All M[i][*] where * < j
  All M[*][j] where * > i

This creates a complex 2D dependency pattern,
not the simple diagonal pattern of palindrome.
```

---

## Part VII: Correctness Proof

### 7.1 Loop Invariant

**Definition 7.1:**
```
After processing all intervals of gap < g:
  Processed(g) = {(i,j) | j - i < g}
```

**Invariant 7.1:**
```
Inv(g) ≜ ∀(i,j) ∈ Processed(g) :
  M[i][j] = maximum coins obtainable by bursting all balloons in (i,j)
```


**Theorem 2.1 (Optimal Substructure):**
```
Let M(i, j) = maximum coins from bursting all balloons in (i, j)
              where i and j are NOT burst (they are boundaries)

Then:
M(i, j) = max{A[i] × A[k] × A[j] + M(i, k) + M(k, j) | k ∈ (i, j)}
```

**Proof:**
```
(⟹) Forward: Optimal solution uses optimal subsolutions

Let σ* be an optimal burst sequence for (i, j).
Let k* be the LAST balloon burst in σ*.

When k* is burst:
  - All balloons in (i, k*) already burst → σₗ subsolution
  - All balloons in (k*, j) already burst → σᵣ subsolution
  - Only i, k*, j remain
  - Coins from k*: A[i] × A[k*] × A[j]

Total: Coins(σ*) = Coins(σₗ) + Coins(σᵣ) + A[i]×A[k*]×A[j]

Claim: σₗ must be optimal for (i, k*).

Proof by contradiction:
  Suppose ∃σ'ₗ with Coins(σ'ₗ) > Coins(σₗ)

  Then: σ' = σ'ₗ + σᵣ + {k*} would give:
        Coins(σ') = Coins(σ'ₗ) + Coins(σᵣ) + A[i]×A[k*]×A[j]
                  > Coins(σₗ) + Coins(σᵣ) + A[i]×A[k*]×A[j]
                  = Coins(σ*)

  This contradicts optimality of σ*. □

Similarly, σᵣ must be optimal for (k*, j).

Therefore: M(i, j) = A[i]×A[k*]×A[j] + M(i,k*) + M(k*,j)

(⟸) Backward: Our recurrence finds optimal solution

Our recurrence tries all k ∈ (i, j), including k*.
Since M(i, k) and M(k, j) are optimal (by induction),
and we try k*, we achieve M(i, j). □
```

---

## Part III: Recurrence Relation - Complete Analysis

### 3.1 Mathematical Definition

**Definition 3.1 (DP Function):**
```
M : [0, k+1] × [0, k+1] → ℕ

M(i, j) = ⎧ 0                                           if j - i ≤ 1
           ⎨ max{A[i]×A[k]×A[j] + M(i,k) + M(k,j)    otherwise
           ⎩      | k ∈ {i+1, i+2, ..., j-1}}
```

**Base case explanation:**
```
M(i, i+1) = 0  (no balloons between i and i+1)
M(i, i) = 0    (same balloon, no interval)
```

---

### 3.2 Dependency Graph

**Definition 3.2 (Dependency DAG):**
```
Let G = (V, E) where:
  V = {(i, j) | 0 ≤ i < j ≤ k+1}

  E = {((i,j), (i,k)) | i < k < j} ∪
      {((i,j), (k,j)) | i < k < j}
```

**Interpretation:**
```
(i, j) depends on:
  - All (i, k) for k ∈ (i, j)
  - All (k, j) for k ∈ (i, j)
```

**Lemma 3.1:** G is a DAG.

**Proof:**
```
Define weight: w(i, j) = j - i (gap size)

For any edge (i,j) → (i',j'):
  Case 1: (i',j') = (i,k) with k < j
    w(i',j') = k - i < j - i = w(i,j)

  Case 2: (i',j') = (k,j) with i < k
    w(i',j') = j - k < j - i = w(i,j)

In both cases: w(i',j') < w(i,j)

Since weight strictly decreases along edges, no cycles exist. □
```

