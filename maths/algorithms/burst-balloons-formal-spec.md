# Formal Mathematical Specification: Burst Balloons Problem

## 1. Lamport-Style TLA+ Specification

### Basic Definitions

**Given:**
- An array of balloons nums = [n₁, n₂, ..., nₖ] where nᵢ ∈ ℕ⁺
- Length k = |nums|
- Extended array A = [1, n₁, n₂, ..., nₖ, 1] with virtual balloons at boundaries
- Index set I = {0, 1, 2, ..., k+1} for extended array

**Problem:** Find the maximum coins obtainable by bursting all balloons optimally.

---

### Coin Calculation

**When bursting balloon i:**
```
Coins(i, left, right) = A[left] × A[i] × A[right]

where:
  left = index of nearest remaining balloon to the left of i
  right = index of nearest remaining balloon to the right of i
```

---

### State Representation

**Define:**
```
MaxCoins(i, j) ≜ Maximum coins obtainable by bursting all balloons
                 in the OPEN interval (i, j)

Where:
  - i, j are indices in extended array A
  - (i, j) = {i+1, i+2, ..., j-1} (open interval, excludes i and j)
  - Balloons i and j remain UN-burst (they are boundaries)
```

---

### Recurrence Relation (The Trick!)

**Key Insight:** Think about which balloon to burst LAST, not first!

```
MaxCoins(i, j) ≜
  CASE j - i OF
    1 → 0                                    (no balloons between i and j)
    2 → A[i] × A[i+1] × A[j]               (only one balloon between)
    _ → max{A[i] × A[k] × A[j] + MaxCoins(i,k) + MaxCoins(k,j)
            | k ∈ (i, j)}                   (choose last balloon k to burst)
```

**Critical observation:**
When k is the LAST balloon burst in (i,j):
- All balloons in (i,k) are already burst
- All balloons in (k,j) are already burst
- Only i, k, j remain → bursting k gives: A[i] × A[k] × A[j]

---

## 2. Formal Logic Representation

### First-Order Logic

**Predicate Definition:**
```
OptimalBurst(i, j, coins) ≡
  (j - i ≤ 1 ∧ coins = 0) ∨
  ∃k ∈ (i,j) : coins = A[i] × A[k] × A[j] +
                        OptimalBurst(i,k) + OptimalBurst(k,j) ∧
                        ∀k' ∈ (i,j) : coins ≥ BurstValue(i,j,k')
```

**Optimization Problem:**
```
maximize ∑ᵢ (coins from bursting balloon i)
subject to: Each balloon burst exactly once
            Order affects coin calculation

Solution: MaxCoins(0, k+1)  (all balloons in extended array)
```

---

## 3. Dynamic Programming as State Transition

### State Space Definition

**State:**
```
σ ∈ Σₛₜₐₜₑ = ℕ^((k+2)×(k+2))
where σ[i][j] represents MaxCoins(i, j)
```

**Initial State:**
```
σ₀[i][j] = {
  0     if j - i ≤ 1  (no balloons between)
  ⊥     otherwise     (undefined)
}
```

**Transition Function:**
```
δ : Σₛₜₐₜₑ × (I × I) → Σₛₜₐₜₑ

δ(σ, (i, j)) = σ' where
  σ'[i][j] = max{A[i] × A[k] × A[j] + σ[i][k] + σ[k][j]
                 | k ∈ {i+1, i+2, ..., j-1}}
```

**Computation Order:**
```
Process pairs (i, j) in order of increasing gap g = j - i
∀g ∈ {2, 3, ..., k+1} : ∀i ∈ {0, ..., k+1-g} : compute MaxCoins(i, i+g)
```

---

## 4. Set-Theoretic Formulation

### Permutations and Orderings

**Define the set of all valid burst sequences:**
```
𝒮 = {π | π is a permutation of {1, 2, ..., k}}

where π = (π₁, π₂, ..., πₖ) means:
  - Burst balloon π₁ first
  - Then burst balloon π₂
  - ...
  - Burst balloon πₖ last
```

**Coin function for a sequence:**
```
Coins(π) = ∑ᵢ₌₁ᵏ CoinAtStep(π, i)

where CoinAtStep(π, i) = left(π,i) × A[πᵢ] × right(π,i)
  left(π,i)  = A[max{0} ∪ {πⱼ | j < i}]
  right(π,i) = A[min{k+1} ∪ {πⱼ | j < i}]
```

**Optimal solution:**
```


**WHY W(i,j) is NOT Θ(1) for Burst Balloons:**
```
Unlike palindrome problem where W(i,j) = Θ(1), here:

W(i, j) = Θ(j - i) because we must try ALL k ∈ (i,j)

For each k:
  - Operations are O(1) ✓
  - But number of k values = j - i - 1 ✗

We can't avoid trying all k because each gives different value!
```

**Total Time Complexity:**
```
T(n) = ∑_{all (i,j)} W(i, j)
     = ∑_{g=2}^{k+1} ∑_{i=0}^{k+1-g} O(g)
     = ∑_{g=2}^{k+1} (k+2-g) × O(g)
     = O(∑_{g=2}^{k+1} g²)
     = O(k³)
```

**Detailed calculation:**
```
∑_{g=2}^{k+1} (k+2-g) × g = ∑_{g=2}^{k+1} (kg + 2g - g²)
                           ≈ k × ∑g + O(∑g²)
                           = O(k³)
```

### Space Complexity

**DP Table:**
```
S(k) = Θ(k²)  (storing (k+2)×(k+2) table)
```

**Cannot optimize to O(k)** like palindrome because dependencies are not diagonal.

---

## 9. Invariants and Correctness

### Loop Invariant

**For gap g being processed:**
```
Inv(g) ≜
  ∧ ∀i, j : (j - i < g) ⇒ M[i][j] is correctly computed
  ∧ ∀i, j : (j - i = g) ∧ (processed(i, j)) ⇒ M[i][j] is correct
```

### Correctness Theorem

```
THEOREM: BurstBalloons_DP_Correct
  ASSUME: Array nums with k balloons, extended to A[0..k+1]
  PROVE:  M[0][k+1] = maximum coins obtainable
```

**Proof sketch:**
```
By induction on gap g = j - i:

Base case (g ≤ 1): M[i][j] = 0 (no balloons) ✓

Inductive step:
  Assume M[i][j] correct for all j - i < g.

  For M[i][j] with j - i = g:
    Consider optimal burst sequence for (i,j).
    Let k* be the LAST balloon burst.

    When k* is burst:
      - All (i,k*) balloons already burst
      - All (k*,j) balloons already burst
      - Coins from k*: A[i] × A[k*] × A[j]
      - Coins from (i,k*): M[i][k*] (optimal by IH)
      - Coins from (k*,j): M[k*][j] (optimal by IH)

    Total: A[i] × A[k*] × A[j] + M[i][k*] + M[k*][j]

    Our algorithm tries all k, including k*, so:
      M[i][j] ≥ A[i] × A[k*] × A[j] + M[i][k*] + M[k*][j]

    Since k* is optimal, M[i][j] = this value.

By induction, M[0][k+1] is correct. □
```

---

## 10. Comparison: Palindrome vs Burst Balloons

| Aspect | Palindrome DP | Burst Balloons DP |
|--------|---------------|-------------------|
| **Subproblems** | Θ(n²) | Θ(k²) |
| **Work per subproblem** | Θ(1) | Θ(gap) |
| **Total Time** | Θ(n²) | Θ(k³) |
| **Space** | Θ(n²) or Θ(n) | Θ(k²) |
| **Dependency** | P(i,j) needs 1 subproblem | M(i,j) needs gap-1 subproblems |
| **Key insight** | Match endpoints | Choose LAST balloon |
| **Why different complexity?** | Fixed dependency count | Variable dependency count |

**Critical difference:**
```
Palindrome: P(i,j) = f(s[i], s[j], P(i+1,j-1))
            → Depends on 1 subproblem → O(1) work

Burst Balloons: M(i,j) = max over all k {f(k, M(i,k), M(k,j))}
                → Depends on (j-i-1) subproblems → O(j-i) work
```

---

## 11. Alternative Formulation: Matrix Chain Multiplication Style

**Observation:** Burst Balloons is similar to Matrix Chain Multiplication!

**Matrix Chain Multiplication:**
```
M[i][j] = minimum multiplications to multiply matrices Aᵢ...Aⱼ
M[i][j] = min{M[i][k] + M[k+1][j] + cost(i,k,j) | k ∈ [i,j)}
```

**Burst Balloons:**
```
M[i][j] = maximum coins from bursting balloons in (i,j)
M[i][j] = max{M[i][k] + M[k][j] + A[i]×A[k]×A[j] | k ∈ (i,j)}
```

**Both have:**
- Θ(n²) subproblems
- Θ(n³) total time
- Interval DP structure
- Optimal substructure via splitting

---

## 12. Memoization vs Tabulation

### Top-Down Memoization

```python
memo = {}

def maxCoins(i, j):
    if j - i <= 1:
        return 0
    if (i, j) in memo:
        return memo[(i, j)]

    result = 0
    for k in range(i+1, j):
        coins = A[i] * A[k] * A[j] + maxCoins(i, k) + maxCoins(k, j)
        result = max(result, coins)

    memo[(i, j)] = result
    return result
```

**Complexity:**
- Each subproblem computed once
- Work per call: O(j - i)
- Total: Θ(k³)

### Bottom-Up Tabulation

```python
dp = [[0] * (k+2) for _ in range(k+2)]

for gap in range(2, k+2):
    for i in range(k+2-gap):
        j = i + gap
        for k in range(i+1, j):
            dp[i][j] = max(dp[i][j],
                          A[i] * A[k] * A[j] + dp[i][k] + dp[k][j])
```

**Complexity:**
- Three nested loops
- Outer: O(k)
- Middle: O(k)
- Inner: O(k)
- Total: Θ(k³)

**Both approaches:** Same asymptotic complexity!

---

## 13. Mathematical Beauty

**This problem exhibits:**
```
1. Non-obvious optimal substructure
   (LAST balloon, not first!)

2. Independence of subproblems
   (Left and right are independent)

3. Interval DP pattern
   (Similar to matrix chain multiplication)

4. Boundary trick
   (Virtual balloons at ends)

5. Gap-based processing order
   (Natural topological sort)
```

**Pedagogical value:**
- Shows not all DP problems have Θ(1) work per subproblem
- Demonstrates importance of formulation (last vs first)
- Illustrates interval DP technique
- Connects to other classic problems (MCM)

---

## 14. Summary

### Key Mathematical Objects

| Aspect | Mathematical Representation |
|--------|---------------------------|
| **State** | M ∈ ℕ^((k+2)×(k+2)) |
| **Recurrence** | M(i,j) = max{A[i]×A[k]×A[j] + M(i,k) + M(k,j) \| k∈(i,j)} |
| **Solution Set** | All permutations π ∈ 𝒮 |
| **Objective** | max{Coins(π) \| π ∈ 𝒮} = M(0,k+1) |
| **Complexity** | T(k) ∈ Θ(k³), S(k) ∈ Θ(k²) |
| **Work per subproblem** | W(i,j) = Θ(j-i) ≠ Θ(1) |

### Critical Insights

1. **Why LAST balloon:** Creates independent subproblems
2. **Why O(k³):** Must try all k for each (i,j), can't optimize to O(1) per subproblem
3. **Virtual boundaries:** Simplifies edge cases
4. **Interval DP:** Process by increasing gap size

---

## Appendix A: Complete Algorithm

```
Algorithm: BurstBalloonsDP(nums[1..k])
Input: Array of k balloon values
Output: Maximum coins obtainable

1. Create extended array A[0..k+1]
2. A[0] ← 1, A[k+1] ← 1
3. for i ← 1 to k do
4.     A[i] ← nums[i]
5.
6. Initialize dp[0..k+1][0..k+1] with zeros
7.
8. // Process by increasing gap
9. for gap ← 2 to k+1 do
10.    for i ← 0 to k+1-gap do
11.        j ← i + gap
12.        dp[i][j] ← 0
13.
14.        // Try each k as last balloon to burst
15.        for k ← i+1 to j-1 do
16.            coins ← A[i] × A[k] × A[j] + dp[i][k] + dp[k][j]
17.            dp[i][j] ← max(dp[i][j], coins)
18.
19. return dp[0][k+1]

Time Complexity: Θ(k³)
Space Complexity: Θ(k²)
```

---

**End of Formal Specification**

---

## 5. Recursive Function Theory

**Function Signature:**
```
M : ℕ × ℕ → ℕ
M(i, j) = maximum coins from bursting all balloons in (i, j)
```

**Base Case:**
```
M(i, i+1) = 0    ∀i ∈ [0, k]     (no balloons between consecutive indices)
M(i, i) = 0      ∀i              (no gap)
```

**Recursive Case:**
```
M(i, j) = max{A[i] × A[k] × A[j] + M(i,k) + M(k,j)
          | k ∈ {i+1, i+2, ..., j-1}}

for j - i ≥ 2
```

---

## 6. Why "Last Balloon" Not "First Balloon"?

### Problem with "First Balloon" Approach

**If we think about which balloon to burst FIRST:**
```
Subproblem dependency becomes CIRCULAR!

Example: nums = [3, 1, 5, 8]
If we burst balloon 1 (value=1) first:
  - Remaining: [3, 5, 8]
  - But balloon indices change!
  - Balloon 2 (value=5) is now at position 1
  - Can't express subproblems cleanly
```

**Why it fails:**
```
Bursting first balloon at position k splits array into:
  - Left part: [1..k-1]
  - Right part: [k+1..n]

BUT: The boundaries of these subproblems depend on what's burst later!
     This creates dependency cycles.
```

---

### Why "Last Balloon" Works

**If we think about which balloon to burst LAST:**
```
When k is the LAST balloon burst in (i,j):
  - All balloons in (i,k) are already gone
  - All balloons in (k,j) are already gone
  - So k is sandwiched between i and j
  - Coins from bursting k: A[i] × A[k] × A[j]
  - Total: A[i]×A[k]×A[j] + MaxCoins(i,k) + MaxCoins(k,j)
```

**Why it works:**
```
Subproblems are INDEPENDENT:
  - MaxCoins(i,k) doesn't depend on what happens in (k,j)
  - MaxCoins(k,j) doesn't depend on what happens in (i,k)
  - When computing MaxCoins(i,j), we assume i and j are boundaries

This creates a clean DAG of dependencies!
```

---

## 7. Dependency DAG Structure

**Definition 7.1 (Dependency Graph):**
```
Let G = (V, E) where:
  V = {(i, j) | 0 ≤ i < j ≤ k+1}
  E = {((i,j), (i,k)) | i < k < j} ∪
      {((i,j), (k,j)) | i < k < j}
```

**Lemma 7.1:** G is a DAG.

**Proof:**
```
For any edge (i,j) → (i',j'):
  Either (i',j') = (i,k) with k < j, so j' < j
  Or (i',j') = (k,j) with i < k, so i' > i

In both cases: j' - i' < j - i (gap decreases)

Since gap strictly decreases along any path, no cycles exist. □
```

**Topological Order:**
```
Process by increasing gap g = j - i:
  g = 1: All base cases (no balloons between)
  g = 2: One balloon between
  ...
  g = k+1: All balloons (solution)
```

---

## 8. Complexity Analysis

### Time Complexity

**Number of subproblems:**
```
|{(i,j) | 0 ≤ i < j ≤ k+1}| = C(k+2, 2) = (k+2)(k+1)/2 = Θ(k²)
```

**Work per subproblem:**
```
For M(i, j) with gap g = j - i:
  Must try all k ∈ (i, j)
  Number of choices: j - i - 1 = g - 1

  For each k:
    - Compute A[i] × A[k] × A[j]:  O(1)
    - Lookup M[i][k]:               O(1)
    - Lookup M[k][j]:               O(1)
    - Addition:                      O(1)
  Total per k: O(1)

  Finding maximum over g-1 choices: O(g)

Therefore: W(i, j) = O(j - i) = O(g)
```

