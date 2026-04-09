# Worked Example: Burst Balloons DP with Complete Mathematics

## Example Array: nums = [3, 1, 5, 8]

Let's trace through the complete algorithm with full mathematical detail.

---

## Step 0: Setup

**Given:**
```
nums = [3, 1, 5, 8]
k = 4
```

**Create Extended Array:**
```
A = [1, 3, 1, 5, 8, 1]
Indices: 0, 1, 2, 3, 4, 5

A[0] = 1  (virtual left boundary)
A[1] = 3  (balloon 1)
A[2] = 1  (balloon 2)
A[3] = 5  (balloon 3)
A[4] = 8  (balloon 4)
A[5] = 1  (virtual right boundary)
```

**Initialize DP table:**
```
dp[i][j] for 0 ≤ i < j ≤ 5

Initial state (all zeros):
    j=0  j=1  j=2  j=3  j=4  j=5
i=0  0    0    0    0    0    0
i=1  -    0    0    0    0    0
i=2  -    -    0    0    0    0
i=3  -    -    -    0    0    0
i=4  -    -    -    -    0    0
i=5  -    -    -    -    -    0
```

---

## Step 1: Gap = 1 (Base Cases)

**All adjacent pairs have no balloons between them.**

```
dp[0][1] = 0  (no balloons between 0 and 1)
dp[1][2] = 0  (no balloons between 1 and 2)
dp[2][3] = 0  (no balloons between 2 and 3)
dp[3][4] = 0  (no balloons between 3 and 4)
dp[4][5] = 0  (no balloons between 4 and 5)
```

**Work:** 5 assignments = O(k)

---

## Step 2: Gap = 2 (One Balloon Between)

**Subproblems:** (k+2-2) = 4 subproblems

### Subproblem (0,2): Interval (0,2) contains balloon 1

```
i = 0, j = 2
Balloons in (0,2): {1}
Only one k to try: k = 1

Computation:
  k = 1:
    coins = A[0] × A[1] × A[2] + dp[0][1] + dp[1][2]
          = 1 × 3 × 1 + 0 + 0
          = 3

dp[0][2] = max{3} = 3
```

**Meaning:** Burst balloon 1 (value 3) while boundaries are virtual balloons.
**Coins:** 1 × 3 × 1 = 3

---

### Subproblem (1,3): Interval (1,3) contains balloon 2

```
i = 1, j = 3
Balloons in (1,3): {2}
Only one k to try: k = 2

Computation:
  k = 2:
    coins = A[1] × A[2] × A[3] + dp[1][2] + dp[2][3]
          = 3 × 1 × 5 + 0 + 0
          = 15

dp[1][3] = max{15} = 15
```

**Meaning:** Burst balloon 2 (value 1) while boundaries are 3 and 5.
**Coins:** 3 × 1 × 5 = 15

---

### Subproblem (2,4): Interval (2,4) contains balloon 3

```
i = 2, j = 4
Balloons in (2,4): {3}
Only one k to try: k = 3

Computation:
  k = 3:
    coins = A[2] × A[3] × A[4] + dp[2][3] + dp[3][4]
          = 1 × 5 × 8 + 0 + 0
          = 40

dp[2][4] = max{40} = 40
```

**Coins:** 1 × 5 × 8 = 40

---

### Subproblem (3,5): Interval (3,5) contains balloon 4

```
i = 3, j = 5
Balloons in (3,5): {4}
Only one k to try: k = 4

Computation:
  k = 4:
    coins = A[3] × A[4] × A[5] + dp[3][4] + dp[4][5]
          = 5 × 8 × 1 + 0 + 0
          = 40

dp[3][5] = max{40} = 40
```

**Coins:** 5 × 8 × 1 = 40

**Work for gap 2:** 4 subproblems × 1 iteration each × O(1) = O(4)

**Table after gap 2:**
```
    j=0  j=1  j=2  j=3  j=4  j=5


---

## Final DP Table

```
    j=0  j=1  j=2  j=3  j=4  j=5
i=0  0    0    3   30  159  167  ← Answer is dp[0][5] = 167
i=1  -    0    0   15  135  159
i=2  -    -    0    0   40   48
i=3  -    -    -    0    0   40
i=4  -    -    -    -    0    0
i=5  -    -    -    -    -    0
```

---

## Reconstructing the Optimal Sequence

**From dp[0][5] = 167, we chose k = 4**
- Burst balloon 4 LAST
- Subproblems: dp[0][4] and dp[4][5]

**From dp[0][4] = 159, we chose k = 1**
- Burst balloon 1 LAST (among balloons 1,2,3)
- Subproblems: dp[0][1] and dp[1][4]

**From dp[1][4] = 135, we chose k = 3**
- Burst balloon 3 LAST (among balloons 2,3)
- Subproblems: dp[1][3] and dp[3][4]

**From dp[1][3] = 15, we chose k = 2**
- Burst balloon 2 (only one balloon)

**Bursting order (from FIRST to LAST):**
```
1. Burst balloon 2 first
2. Burst balloon 3 second
3. Burst balloon 1 third
4. Burst balloon 4 last
```

**Verification:**
```
State: [1, 3, 1, 5, 8, 1]  (extended array)

1. Burst balloon 2 (value 1):
   Neighbors: 3 and 5
   Coins: 3 × 1 × 5 = 15
   Remaining: [1, 3, 5, 8, 1]

2. Burst balloon 3 (value 5):
   Neighbors: 3 and 8
   Coins: 3 × 5 × 8 = 120
   Remaining: [1, 3, 8, 1]

3. Burst balloon 1 (value 3):
   Neighbors: 1 and 8
   Coins: 1 × 3 × 8 = 24
   Remaining: [1, 8, 1]

4. Burst balloon 4 (value 8):
   Neighbors: 1 and 1
   Coins: 1 × 8 × 1 = 8
   Remaining: [1, 1]

Total: 15 + 120 + 24 + 8 = 167 ✓
```

---

## Summary: Total Complexity for This Example

### Time Complexity Breakdown

```
Gap 1: 5 subproblems × 0 iterations = 0 work
Gap 2: 4 subproblems × 1 iteration  = 4 work
Gap 3: 3 subproblems × 2 iterations = 6 work
Gap 4: 2 subproblems × 3 iterations = 6 work
Gap 5: 1 subproblem  × 4 iterations = 4 work

Total: 0 + 4 + 6 + 6 + 4 = 20 units of work
```

**Formula verification:**
```
For k = 4:
Total work = (k+1)(k+2)(k+3)/6 = 5×6×7/6 = 35

Wait, this doesn't match! Why?

Because base cases (gap 1) don't need iteration.
Actual formula for work:
  = ∑_{g=2}^{k+1} (k+2-g) × (g-1)
  = ∑_{g=2}^5 (6-g) × (g-1)
  = 4×1 + 3×2 + 2×3 + 1×4
  = 4 + 6 + 6 + 4
  = 20 ✓
```

**General formula: T(k) = Θ(k³)**

---

## Detailed Work Analysis Per Cell

### Why W(i,j) = Θ(j - i)?

**Example: Computing dp[0][5]**

```
for k in range(1, 5):  # k = 1, 2, 3, 4
    # Each iteration does:
    coins = A[0] * A[k] * A[5]     # O(1): 2 multiplications
    coins += dp[0][k]               # O(1): array lookup + addition
    coins += dp[k][5]               # O(1): array lookup + addition
    result = max(result, coins)    # O(1): comparison

Number of iterations: 4 = j - i - 1 = 5 - 0 - 1
Work per iteration: O(1)
Total work: 4 × O(1) = Θ(4) = Θ(j - i)
```

**Generalization:**
```
W(i, j) = (j - i - 1) × O(1) = Θ(j - i)
```

**Key difference from Palindrome:**
```
Palindrome: P(i,j) uses ONE fixed subproblem P(i+1,j-1)
            → W(i,j) = Θ(1)

Burst Balloons: M(i,j) must try ALL k ∈ (i,j)
                → W(i,j) = Θ(j - i)
```

---

## Why Must We Try All k?

**Question:** Can we predict which k is optimal without trying all?

**Answer:** No! The optimal k depends on the values.

**Example comparison:**

**Case 1: nums = [3, 1, 5, 8]**
```
For interval (0,5):
  Optimal k = 4 (gives 167)
```

**Case 2: nums = [1, 100, 1, 1]**
```
Extended: A = [1, 1, 100, 1, 1, 1]
For interval (0,5):
  Try k = 1: ... (small value)
  Try k = 2: ... (optimal! balloon with value 100)
  Try k = 3: ... (small value)
  Try k = 4: ... (small value)
  Optimal k = 2 (different from Case 1!)
```

**Conclusion:** The optimal k varies with input values. We MUST try all k!

---

## Mathematical Proof of W(i,j) = Θ(j-i)

**Theorem:** For Burst Balloons DP, W(i,j) = Θ(j - i).

**Proof:**

**Lower bound: W(i,j) = Ω(j - i)**
```
To compute M(i,j), we must consider all k ∈ (i,j).
Number of k values = j - i - 1 = Θ(j - i)

Even if we could process each k in O(1):
  W(i,j) ≥ (j - i - 1) × 1 = Ω(j - i)
```

**Upper bound: W(i,j) = O(j - i)**
```
For each k ∈ (i,j):
  - Multiply A[i] × A[k] × A[j]:  O(1)
  - Lookup M[i][k] from table:    O(1) (array indexing)
  - Lookup M[k][j] from table:    O(1) (array indexing)
  - Addition and max:             O(1)

Work per k: O(1)
Number of k: j - i - 1

Total: (j - i - 1) × O(1) = O(j - i)
```

**Combining:** W(i,j) = Θ(j - i) □

---

## Comparison: Palindrome vs Burst Balloons

| Aspect | Palindrome | Burst Balloons |
|--------|-----------|----------------|
| **Subproblems** | Θ(n²) | Θ(k²) |
| **Dependencies per subproblem** | 1 fixed | j-i-1 variable |
| **Work per subproblem** | Θ(1) | Θ(j-i) |
| **Total time** | Θ(n²) | Θ(k³) |
| **Can optimize to O(1) work?** | Yes | No |
| **Reason** | Fixed dependency | Must try all splits |

---

## Key Takeaways

### 1. Why Think LAST, Not FIRST?
```
Thinking LAST creates independent subproblems.
When k is burst last, (i,k) and (k,j) don't interact.
```

### 2. Why W(i,j) ≠ Θ(1)?
```
Must try all k ∈ (i,j) because optimal k is unpredictable.
Each k gives different value.
Can't reduce iterations without losing correctness.
```

### 3. Why Θ(k³) Total Time?
```
T(k) = ∑_{all (i,j)} W(i,j)
     = ∑_{all (i,j)} Θ(j - i)
     = Θ(k³)

The cube comes from summing: gap × (number of subproblems with that gap)
```

### 4. Interval DP Pattern
```
This is a classic "interval DP" problem.
Similar to: Matrix Chain Multiplication
All interval DP has Θ(n³) time complexity.
```

---

**End of Worked Example**

i=0  0    0    3    0    0    0
i=1  -    0    0   15    0    0
i=2  -    -    0    0   40    0
i=3  -    -    -    0    0   40
i=4  -    -    -    -    0    0
i=5  -    -    -    -    -    0
```

---

## Step 3: Gap = 3 (Two Balloons Between)

**Subproblems:** (k+2-3) = 3 subproblems

### Subproblem (0,3): Interval (0,3) contains balloons {1, 2}

```
i = 0, j = 3
Balloons in (0,3): {1, 2}
Try k = 1 and k = 2

Computation:
  k = 1 (burst balloon 1 LAST):
    coins = A[0] × A[1] × A[3] + dp[0][1] + dp[1][3]
          = 1 × 3 × 5 + 0 + 15
          = 15 + 15
          = 30

  k = 2 (burst balloon 2 LAST):
    coins = A[0] × A[2] × A[3] + dp[0][2] + dp[2][3]
          = 1 × 1 × 5 + 3 + 0
          = 5 + 3
          = 8

dp[0][3] = max{30, 8} = 30
```

**Optimal:** Burst balloon 2 first (gets 15), then balloon 1 last (gets 15).

**Why W(0,3) = Θ(2):**
```
Number of k values to try: 2
Each k requires:
  - 3 multiplications: O(1)
  - 2 table lookups: O(1)
  - 1 addition: O(1)
Total per k: O(1)
Total: 2 × O(1) = O(2) = Θ(gap)
```

---

### Subproblem (1,4): Interval (1,4) contains balloons {2, 3}

```
i = 1, j = 4
Balloons in (1,4): {2, 3}
Try k = 2 and k = 3

Computation:
  k = 2:
    coins = A[1] × A[2] × A[4] + dp[1][2] + dp[2][4]
          = 3 × 1 × 8 + 0 + 40
          = 24 + 40
          = 64

  k = 3:
    coins = A[1] × A[3] × A[4] + dp[1][3] + dp[3][4]
          = 3 × 5 × 8 + 15 + 0
          = 120 + 15
          = 135

dp[1][4] = max{64, 135} = 135
```

**Optimal:** Burst balloon 2 first (gets 15), then balloon 3 last (gets 120).

---

### Subproblem (2,5): Interval (2,5) contains balloons {3, 4}

```
i = 2, j = 5
Balloons in (2,5): {3, 4}
Try k = 3 and k = 4

Computation:
  k = 3:
    coins = A[2] × A[3] × A[5] + dp[2][3] + dp[3][5]
          = 1 × 5 × 1 + 0 + 40
          = 5 + 40
          = 45

  k = 4:
    coins = A[2] × A[4] × A[5] + dp[2][4] + dp[4][5]
          = 1 × 8 × 1 + 40 + 0
          = 8 + 40
          = 48

dp[2][5] = max{45, 48} = 48
```

**Work for gap 3:** 3 subproblems × 2 iterations each × O(1) = O(6)

**Table after gap 3:**
```
    j=0  j=1  j=2  j=3  j=4  j=5
i=0  0    0    3   30    0    0
i=1  -    0    0   15  135    0
i=2  -    -    0    0   40   48
i=3  -    -    -    0    0   40
i=4  -    -    -    -    0    0
i=5  -    -    -    -    -    0
```

---

## Step 4: Gap = 4 (Three Balloons Between)

**Subproblems:** (k+2-4) = 2 subproblems

### Subproblem (0,4): Interval (0,4) contains balloons {1, 2, 3}

```
i = 0, j = 4
Balloons in (0,4): {1, 2, 3}
Try k = 1, k = 2, k = 3

Computation:
  k = 1:
    coins = A[0] × A[1] × A[4] + dp[0][1] + dp[1][4]
          = 1 × 3 × 8 + 0 + 135
          = 24 + 135
          = 159

  k = 2:
    coins = A[0] × A[2] × A[4] + dp[0][2] + dp[2][4]
          = 1 × 1 × 8 + 3 + 40
          = 8 + 3 + 40
          = 51

  k = 3:
    coins = A[0] × A[3] × A[4] + dp[0][3] + dp[3][4]
          = 1 × 5 × 8 + 30 + 0
          = 40 + 30
          = 70

dp[0][4] = max{159, 51, 70} = 159
```

**Optimal choice:** k = 1 (burst balloon 1 last)

**Work:** W(0,4) = 3 iterations × O(1) = Θ(3) = Θ(gap)

---

### Subproblem (1,5): Interval (1,5) contains balloons {2, 3, 4}

```
i = 1, j = 5
Balloons in (1,5): {2, 3, 4}
Try k = 2, k = 3, k = 4

Computation:
  k = 2:
    coins = A[1] × A[2] × A[5] + dp[1][2] + dp[2][5]
          = 3 × 1 × 1 + 0 + 48
          = 3 + 48
          = 51

  k = 3:
    coins = A[1] × A[3] × A[5] + dp[1][3] + dp[3][5]
          = 3 × 5 × 1 + 15 + 40
          = 15 + 15 + 40
          = 70

  k = 4:
    coins = A[1] × A[4] × A[5] + dp[1][4] + dp[4][5]
          = 3 × 8 × 1 + 135 + 0
          = 24 + 135
          = 159

dp[1][5] = max{51, 70, 159} = 159
```

**Work for gap 4:** 2 subproblems × 3 iterations each × O(1) = O(6)

---

## Step 5: Gap = 5 (All Four Balloons) - FINAL ANSWER

**Subproblems:** (k+2-5) = 1 subproblem

### Subproblem (0,5): Interval (0,5) contains ALL balloons {1, 2, 3, 4}

```
i = 0, j = 5
Balloons in (0,5): {1, 2, 3, 4}
Try k = 1, k = 2, k = 3, k = 4

Computation:
  k = 1:
    coins = A[0] × A[1] × A[5] + dp[0][1] + dp[1][5]
          = 1 × 3 × 1 + 0 + 159
          = 3 + 159
          = 162

  k = 2:
    coins = A[0] × A[2] × A[5] + dp[0][2] + dp[2][5]
          = 1 × 1 × 1 + 3 + 48
          = 1 + 3 + 48
          = 52

  k = 3:
    coins = A[0] × A[3] × A[5] + dp[0][3] + dp[3][5]
          = 1 × 5 × 1 + 30 + 40
          = 5 + 30 + 40
          = 75

  k = 4:
    coins = A[0] × A[4] × A[5] + dp[0][4] + dp[4][5]
          = 1 × 8 × 1 + 159 + 0
          = 8 + 159
          = 167

dp[0][5] = max{162, 52, 75, 167} = 167
```

**OPTIMAL ANSWER: 167 coins**

**Optimal choice:** k = 4 (burst balloon 4 last)

**Work:** W(0,5) = 4 iterations × O(1) = Θ(4) = Θ(gap)

