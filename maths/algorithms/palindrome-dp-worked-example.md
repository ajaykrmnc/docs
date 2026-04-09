# Worked Example: Palindrome DP with Complete Mathematics

## Example String: S = "ABBA"

Let's trace through the complete algorithm with full mathematical detail.

---

## Step 0: Setup

**Given:**
```
S = "ABBA"
n = 4
S[1] = 'A', S[2] = 'B', S[3] = 'B', S[4] = 'A'
```

**Initialize DP table:**
```
P[i][j] for 1 ≤ i ≤ j ≤ 4

Initial state (all zeros):
    j=1  j=2  j=3  j=4
i=1  0    0    0    0
i=2  -    0    0    0
i=3  -    -    0    0
i=4  -    -    -    0
```

(We use '-' for i > j since those are invalid/unused)

---

## Step 1: Base Case (Length = 1)

**Mathematical definition:**
```
∀i ∈ [1, n] : P(i, i) = 1
```

**Why?** Single characters are always palindromes.

**Computation:**
```
P[1][1] = 1  (substring "A")
P[2][2] = 1  (substring "B")
P[3][3] = 1  (substring "B")
P[4][4] = 1  (substring "A")
```

**Work per cell:** W(i, i) = c₁ (constant, just assignment)
**Total work:** 4 × c₁ = Θ(n) = Θ(4)

**DP table after length 1:**
```
    j=1  j=2  j=3  j=4
i=1  1    0    0    0
i=2  -    1    0    0
i=3  -    -    1    0
i=4  -    -    -    1
```

---

## Step 2: Length = 2

**Mathematical definition:**
```
P(i, i+1) = [S[i] = S[i+1]]
```

**Number of subproblems:** n - length + 1 = 4 - 2 + 1 = 3

### Subproblem (1, 2): S[1..2] = "AB"

**Computation:**
```
i = 1, j = 2
P[1][2] = [S[1] = S[2]]
        = ['A' = 'B']
        = [False]
        = 0
```

**Substring "AB" is NOT a palindrome.** ✗

### Subproblem (2, 3): S[2..3] = "BB"

**Computation:**
```
i = 2, j = 3
P[2][3] = [S[2] = S[3]]
        = ['B' = 'B']
        = [True]
        = 1
```

**Substring "BB" IS a palindrome!** ✓

### Subproblem (3, 4): S[3..4] = "BA"

**Computation:**
```
i = 3, j = 4
P[3][4] = [S[3] = S[4]]
        = ['B' = 'A']
        = [False]
        = 0
```

**Substring "BA" is NOT a palindrome.** ✗

**Work per cell:** W(i, j) = c₂ + c₃ (one comparison + assignment) = Θ(1)
**Total work for length 2:** 3 × Θ(1) = Θ(3)

**DP table after length 2:**
```
    j=1  j=2  j=3  j=4
i=1  1    0    0    0
i=2  -    1    1    0
i=3  -    -    1    0
i=4  -    -    -    1
```

---

## Step 3: Length = 3

**Mathematical definition:**
```
P(i, j) = [S[i] = S[j]] ∧ P(i+1, j-1)
```

**Number of subproblems:** n - length + 1 = 4 - 3 + 1 = 2

### Subproblem (1, 3): S[1..3] = "ABB"

**Computation:**
```
i = 1, j = 3
P[1][3] = [S[1] = S[3]] ∧ P[2][2]
        = ['A' = 'B'] ∧ P[2][2]
        = [False] ∧ 1
        = 0 ∧ 1
        = 0
```

**Detail:**
- First check: S[1] = 'A' vs S[3] = 'B' → NOT equal
- Short-circuit: No need to check P[2][2]


### Space Complexity

```
DP table size: n × n = 4 × 4 = 16 entries
Used entries: n(n+1)/2 = 10 entries (where i ≤ j)
Space: Θ(n²) = Θ(16)
```

---

## Reading the Final Table

**All palindromic substrings found:**
```
P[1][1] = 1 → "A"       (position 1)
P[2][2] = 1 → "B"       (position 2)
P[3][3] = 1 → "B"       (position 3)
P[4][4] = 1 → "A"       (position 4)
P[2][3] = 1 → "BB"      (positions 2-3)
P[1][4] = 1 → "ABBA"    (positions 1-4, entire string)

Total: 6 palindromic substrings
```

**Longest palindromic substring:**
```
max{j - i + 1 | P[i][j] = 1}
Candidates: (1,1)→1, (2,2)→1, (3,3)→1, (4,4)→1, (2,3)→2, (1,4)→4
Maximum: 4 from P[1][4]
Answer: "ABBA" (length 4)
```

---

## Detailed Work Analysis: Why Each Cell is O(1)

### Length 1 cells: P[i][i]
```
Work: Just set to 1
Cost: c₁
Operations: 1
Total: Θ(1)
```

### Length 2 cells: P[i][i+1]
```
Work:
  1. Load S[i] from memory
  2. Load S[i+1] from memory
  3. Compare equality
  4. Store result in P[i][i+1]
Cost: c₂ + c₃ + c₄ + c₅
Operations: 4
Total: Θ(1)
```

### Length ≥ 3 cells: P[i][j]
```
Work:
  1. Load S[i] from memory       → Θ(1)
  2. Load S[j] from memory       → Θ(1)
  3. Compare S[i] = S[j]         → Θ(1)
  4. Load P[i+1][j-1] from table → Θ(1)  ← KEY!
  5. Compute AND                 → Θ(1)
  6. Store result in P[i][j]    → Θ(1)
Cost: 6 constants
Operations: 6
Total: Θ(1)

Critical: Step 4 is LOOKUP (array indexing), NOT recursion!
```

---

## Contrast: What if We Used Naive Recursion?

### Naive Recursive Solution (No Memoization)

```python
def is_palindrome_naive(s, i, j):
    if i >= j:
        return True
    if s[i] != s[j]:
        return False
    return is_palindrome_naive(s, i+1, j-1)  # RECURSIVE CALL
```

### Recursion Tree for "ABBA" checking P[1][4]

```
P(1,4)
├─ Compare S[1]='A', S[4]='A' ✓
└─ Call P(2,3)
   ├─ Compare S[2]='B', S[3]='B' ✓
   └─ Call P(3,2)
      └─ Base case: return True

Depth: 3
Work: Θ(j - i) = Θ(4 - 1) = Θ(3)
```

**For all substrings:**
```
T_naive = ∑ᵢ₌₁⁴ ∑ⱼ₌ᵢ⁴ Θ(j - i)

Detailed:
(1,1): Θ(0) = 1
(1,2): Θ(1) = 1
(1,3): Θ(2) = 2
(1,4): Θ(3) = 3
(2,2): Θ(0) = 1
(2,3): Θ(1) = 1
(2,4): Θ(2) = 2
(3,3): Θ(0) = 1
(3,4): Θ(1) = 1
(4,4): Θ(0) = 1

Total: 1+1+2+3+1+1+2+1+1+1 = 14 units

For general n:
T_naive = Θ(n³)
```

### DP Solution Work

```
Each cell: Θ(1)
Total cells: n(n+1)/2 = 10
Total work: 10 × Θ(1) = Θ(10) = Θ(n²)

Speedup: Θ(n³)/Θ(n²) = Θ(n) = 4x faster for n=4!
```

---

## Mathematical Proof of W(i,j) = Θ(1)

**Theorem:** For the DP approach, W(i,j) = Θ(1) for all (i,j).

**Proof:**

**Claim:** When computing P[i][j], all required dependencies are already computed.

**Proof of Claim:**
```
We process by increasing length l = j - i + 1.
When processing P[i][j] with length l:
  - We need P[i+1][j-1]
  - Length of (i+1, j-1) is (j-1)-(i+1)+1 = j-i-1 = l-2 < l
  - Therefore P[i+1][j-1] was computed in earlier iteration
  - It's stored in the DP table
```

**Claim:** Array lookup is O(1).

**Proof of Claim:**
```
P is implemented as 2D array (or hash table with O(1) access)
Access P[i+1][j-1] requires:
  - Compute address: base + (i+1)*n + (j-1)  [O(1) arithmetic]
  - Memory load from computed address         [O(1) hardware operation]
Total: O(1)
```

**Combining Claims:**
```
Work for P[i][j]:
  - Character comparisons: O(1) each
  - Array lookups: O(1) each
  - Boolean operations: O(1) each
  - Total: O(1) + O(1) + ... + O(1) = O(1)

Since all operations are constant-time and there's a constant number of them:
W(i,j) = Θ(1) □
```

---

## Visualization: Dependency Graph for "ABBA"

```
Nodes: (i,j) pairs representing subproblems
Edges: (i,j) → (i+1,j-1) representing dependencies

Length 1:  (1,1)  (2,2)  (3,3)  (4,4)
             ↓      ↓      ↓      ↓
Length 2:  (1,2)  (2,3)  (3,4)
             ↓      ↓
Length 3:  (1,3)  (2,4)
             ↓
Length 4:  (1,4)

Processing order (topological): Level by level from bottom to top
This ensures when we compute a node, all its children are done!
```

**Graph properties:**
```
Vertices V: All (i,j) with i ≤ j
Edges E: (i,j) → (i+1,j-1) if j > i+1
|V| = n(n+1)/2 = 10
|E| = number of pairs with length ≥ 3 = 3

This is a DAG (Directed Acyclic Graph)
Topological sort exists: process by increasing length!
```

---

## Final Answer to "Why W(i,j) = Θ(1)?"

**Answer in One Sentence:**
```
W(i,j) = Θ(1) because we LOOK UP (not recompute) already-solved
subproblems from our memoization table using constant-time array indexing.
```

**The Three Keys:**
1. **Memoization**: Store results in a table
2. **Topological order**: Process so dependencies are ready
3. **Constant lookup**: Array indexing is O(1)

**Without any of these three, W(i,j) would NOT be Θ(1)!**

---

## Appendix: Running the Algorithm Step-by-Step

```
Input: S = "ABBA", n = 4

Initialization: P = 4×4 zero matrix

Iteration 1 (length=1):
  P[1][1] ← 1, P[2][2] ← 1, P[3][3] ← 1, P[4][4] ← 1

Iteration 2 (length=2):
  P[1][2] ← [A=B] = 0
  P[2][3] ← [B=B] = 1
  P[3][4] ← [B=A] = 0

Iteration 3 (length=3):
  P[1][3] ← [A=B] ∧ P[2][2] = 0 ∧ 1 = 0
  P[2][4] ← [B=A] ∧ P[3][3] = 0 ∧ 1 = 0

Iteration 4 (length=4):
  P[1][4] ← [A=A] ∧ P[2][3] = 1 ∧ 1 = 1

Output:
  - DP table P complete
  - Longest palindrome: "ABBA" (length 4)
  - Count: 6 palindromes
```

**Total operations: 10 subproblems × Θ(1) = Θ(10) = Θ(n²)**

---

**End of Worked Example**
**Why W(1,3) = Θ(1)?**
```
Operations performed:
1. Array access S[1]:    O(1)
2. Array access S[3]:    O(1)
3. Comparison 'A' = 'B': O(1)
4. Short-circuit AND:    O(1) (didn't even look up P[2][2])
Total: Θ(1)
```

### Subproblem (2, 4): S[2..4] = "BBA"

**Computation:**
```
i = 2, j = 4
P[2][4] = [S[2] = S[4]] ∧ P[3][3]
        = ['B' = 'A'] ∧ P[3][3]
        = [False] ∧ 1
        = 0 ∧ 1
        = 0
```

**Detail:**
- First check: S[2] = 'B' vs S[4] = 'A' → NOT equal
- Short-circuit: No need to check P[3][3]
- Result: 0

**Substring "BBA" is NOT a palindrome.** ✗

**Work per cell:** W(i, j) = c₄ + c₅ + c₆ = Θ(1)
**Total work for length 3:** 2 × Θ(1) = Θ(2)

**DP table after length 3:**
```
    j=1  j=2  j=3  j=4
i=1  1    0    0    0
i=2  -    1    1    0
i=3  -    -    1    0
i=4  -    -    -    1
```

---

## Step 4: Length = 4

**Mathematical definition:**
```
P(i, j) = [S[i] = S[j]] ∧ P(i+1, j-1)
```

**Number of subproblems:** n - length + 1 = 4 - 4 + 1 = 1

### Subproblem (1, 4): S[1..4] = "ABBA"

**Computation:**
```
i = 1, j = 4
P[1][4] = [S[1] = S[4]] ∧ P[2][3]
        = ['A' = 'A'] ∧ P[2][3]
        = [True] ∧ P[2][3]
        = 1 ∧ P[2][3]
```

Now we need P[2][3]. **Critical:** We already computed it in Step 2!

```
P[2][3] = 1  (from our table, computed in Step 2)
```

**Continue:**
```
P[1][4] = 1 ∧ 1
        = 1
```

**Substring "ABBA" IS a palindrome!** ✓

**Why W(1,4) = Θ(1)? THE KEY INSIGHT:**
```
Operations performed:
1. Array access S[1]:       O(1)
2. Array access S[4]:       O(1)
3. Comparison 'A' = 'A':    O(1)
4. Array access P[2][3]:    O(1)  ← LOOKUP, NOT RECURSION!
5. Boolean AND 1 ∧ 1:       O(1)
6. Array write P[1][4] = 1: O(1)
Total: 6 × O(1) = Θ(1)
```

**This is why W(i,j) = Θ(1)!** We don't recursively compute P[2][3].
We just look it up from our table in constant time!

**Work for length 4:** 1 × Θ(1) = Θ(1)

**Final DP table:**
```
    j=1  j=2  j=3  j=4
i=1  1    0    0    1     ← "ABBA" is palindrome!
i=2  -    1    1    0
i=3  -    -    1    0
i=4  -    -    -    1
```

---

## Summary: Total Complexity

### Time Complexity Breakdown

```
Length 1: n = 4 subproblems × Θ(1) work = Θ(4)
Length 2: 3 subproblems × Θ(1) work = Θ(3)
Length 3: 2 subproblems × Θ(1) work = Θ(2)
Length 4: 1 subproblem  × Θ(1) work = Θ(1)

Total: Θ(4 + 3 + 2 + 1) = Θ(10) = Θ(n(n+1)/2) = Θ(n²)
```

**For general n:**
```
T(n) = ∑ₗ₌₁ⁿ (n - l + 1) × Θ(1)
     = Θ(∑ₗ₌₁ⁿ (n - l + 1))
     = Θ(∑ₖ₌₁ⁿ k)
     = Θ(n(n+1)/2)
     = Θ(n²)
```

