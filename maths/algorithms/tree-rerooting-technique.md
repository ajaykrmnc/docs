# Tree Rerooting Technique — A Complete Guide

## Table of Contents

1. [Motivation: Why Rerooting?](#1-motivation-why-rerooting)
2. [Prerequisites](#2-prerequisites)
3. [The Core Idea](#3-the-core-idea)
4. [The Two-Pass Framework](#4-the-two-pass-framework)
5. [Mathematical Formalism](#5-mathematical-formalism)
6. [Worked Example 1 — Sum of Distances to All Nodes](#6-worked-example-1--sum-of-distances-to-all-nodes)
7. [Worked Example 2 — Maximum Depth When Rooted at Each Node](#7-worked-example-2--maximum-depth-when-rooted-at-each-node)
8. [Worked Example 3 — Subtree Sum Product (Weighted Trees)](#8-worked-example-3--subtree-sum-product-weighted-trees)
9. [Worked Example 4 — Count Nodes at Even Distance](#9-worked-example-4--count-nodes-at-even-distance)
10. [Worked Example 5 — Minimum Height Trees](#10-worked-example-5--minimum-height-trees)
11. [General Template (C++ Pseudocode)](#11-general-template-c-pseudocode)
12. [Common Pitfalls](#12-common-pitfalls)
13. [When Rerooting Does NOT Work](#13-when-rerooting-does-not-work)
14. [Complexity Analysis](#14-complexity-analysis)
15. [Practice Problems](#15-practice-problems)

---

## 1. Motivation: Why Rerooting?

Many tree problems ask you to compute some quantity **for every node as if that node were the root**. For example:

- *"For each node `v`, find the sum of distances from `v` to all other nodes."*
- *"For each node `v`, find the height of the tree when rooted at `v`."*

### The Brute-Force Approach

Root the tree at each node separately and run a DFS/BFS to compute the answer.

- Time: **O(N) per root x N roots = O(N²)**
- This is too slow when N reaches 10⁵ or 10⁶.

### The Key Observation

When you **move the root from a node `u` to its neighbor `v`**, the structure of the tree changes only *locally* — specifically along the edge `(u, v)`. Everything in the subtree of `v` moves one level closer to the root, and everything outside the subtree of `v` moves one level farther.

**Rerooting exploits this local change to update the answer in O(1) per edge, giving O(N) total.**

---

## 2. Prerequisites

| Concept | What You Need to Know |
|---|---|
| Tree as a graph | N nodes, N-1 edges, connected, acyclic |
| DFS on trees | Pre-order, post-order traversals |
| Tree DP (rooted) | Computing subtree-aggregate values bottom-up |
| Parent-child relationship | In a rooted tree, every node except the root has exactly one parent |

---

## 3. The Core Idea

Consider a tree rooted at node `0`. For each node `v`, define:

- **`down[v]`** = the answer computed considering only the subtree of `v` (i.e., `v` and its descendants).
- **`up[v]`** = the answer computed considering everything *outside* the subtree of `v` (i.e., the "complement" of `v`'s subtree).

Then the **full answer when `v` is the root** is some combination of `down[v]` and `up[v]`.

```
           0  (root)
          / \
         1   2
        / \   \
       3   4   5
```

When we root at node 0:
- down[1] considers {1, 3, 4}
- up[1] considers {0, 2, 5}

When we reroot at node 1:
- The subtree of 1 (when rooted at 0) becomes "above" node 0
- Node 0's subtree excluding node 1's branch becomes "below" node 0

The rerooting technique computes `up[v]` for every node using a top-down pass, after computing `down[v]` with a bottom-up pass.

---

## 4. The Two-Pass Framework

### Pass 1: Bottom-Up (Post-Order DFS) — Compute `down[v]`

Root the tree at an arbitrary node (say node `0`). Traverse in post-order so that when you process node `v`, all its children are already processed.

```
down[v] = BASE_VALUE
for each child c of v:
    down[v] = MERGE(down[v], LIFT(down[c], edge(v,c)))
```

- **`BASE_VALUE`**: the answer for a single isolated node (a leaf with no children).
- **`LIFT(x, e)`**: transforms a child's aggregated value to account for the edge connecting it to its parent. For distance problems, this often means adding 1. For height problems, adding edge weight, etc.
- **`MERGE(a, b)`**: combines two aggregated values. For sum problems this is addition; for height problems this is `max`.

### Pass 2: Top-Down (Pre-Order DFS) — Compute `up[v]`

Now traverse in pre-order. When processing node `v`, you already know `up[v]` (for the root, `up[root]` is a known base case, often the identity of MERGE). For each child `c` of `v`:

```
up[c] = LIFT(
    MERGE(up[v], MERGE_ALL_CHILDREN_OF_v_EXCEPT_c),
    edge(v,c)
)
```

This says: the "outside" answer for child `c` consists of:
1. Everything outside `v`'s subtree (`up[v]`), plus
2. All sibling subtrees of `c` (all children of `v` except `c`), plus
3. The edge `(v, c)` itself.

### The "All Children Except One" Problem

Computing `MERGE_ALL_CHILDREN_OF_v_EXCEPT_c` naively takes O(degree(v)) per child, giving O(degree(v)²) per node — which can be O(N²) for star graphs.

**Solution: Prefix-Suffix Decomposition**

For each node `v` with children `c₁, c₂, ..., cₖ`:

```
values[i] = LIFT(down[cᵢ], edge(v, cᵢ))

prefix[0] = IDENTITY
prefix[i] = MERGE(prefix[i-1], values[i-1])

suffix[k] = IDENTITY
suffix[i] = MERGE(values[i], suffix[i+1])

ALL_EXCEPT_cᵢ = MERGE(prefix[i], suffix[i+1])
```

This computes the "all-except-one" aggregate in O(1) per child after O(k) preprocessing.

### Final Answer

```
answer[v] = MERGE(down[v], LIFT_UP(up[v]))
```

Or, equivalently, re-derive from `up[v]` and `down[v]` depending on the problem.

---

## 5. Mathematical Formalism

Let **(M, ⊕, e)** be a monoid where:
- `M` is the set of aggregate values
- `⊕` is the MERGE operation (associative, has identity `e`)
- `e` is the identity element

Let `lift: M × E → M` be the LIFT function where `E` is the set of edge labels.

**Requirements for rerooting to work:**

1. **MERGE must be associative**: `(a ⊕ b) ⊕ c = a ⊕ (b ⊕ c)`.
   - This is needed for the prefix-suffix decomposition.
2. **MERGE must have an identity**: `a ⊕ e = e ⊕ a = a`.
3. **LIFT must distribute over MERGE** (or the problem must be decomposable).

If MERGE is **commutative** (like `+` or `max`), the implementation simplifies: you can compute the total and subtract one child, instead of needing prefix/suffix arrays. But prefix-suffix works in both commutative and non-commutative cases.

> **Important:** If the operation is not a monoid (e.g., median, mode), rerooting in O(N) is generally not possible.

---

## 6. Worked Example 1 — Sum of Distances to All Nodes

> **Problem (LeetCode 834):** Given a tree with N nodes, for each node `i`, compute the sum of distances from `i` to every other node.

### Step-by-step

**Tree:**
```
        0
       / \
      1   2
     / \   \
    3   4   5
```

**Pass 1: Bottom-Up** — Compute `sz[v]` (subtree size) and `down[v]` (sum of distances within subtree, from `v`).

```
sz[v] = 1 + Σ sz[c]       for each child c of v
down[v] = Σ (down[c] + sz[c])   for each child c of v
```

The `+ sz[c]` accounts for the fact that every node in `c`'s subtree is 1 edge farther from `v` than from `c`.

Compute bottom-up (leaves first):

| Node | sz | down | Explanation |
|------|-----|------|---|
| 3 | 1 | 0 | Leaf |
| 4 | 1 | 0 | Leaf |
| 5 | 1 | 0 | Leaf |
| 1 | 3 | (0+1)+(0+1) = 2 | Children: 3,4 each contribute sz=1 |
| 2 | 2 | (0+1) = 1 | Child: 5 contributes sz=1 |
| 0 | 6 | (2+3)+(1+2) = 8 | Children: 1 (sz=3), 2 (sz=2) |

So `down[0] = 8` — the sum of distances from node 0 to all others.

**Verify:** dist(0→1)=1, dist(0→2)=1, dist(0→3)=2, dist(0→4)=2, dist(0→5)=2. Sum = 1+1+2+2+2 = 8. Correct!

**Pass 2: Top-Down** — Compute `up[v]` and the final answer.

`up[root=0] = 0` (nothing outside the root's subtree).

For each child `c` of node `v`:
```
up[c] = up[v] + (N - sz[v]) + (down[v] - down[c] - sz[c]) + (sz[v] - sz[c])
```

But there's a simpler standard recurrence for this particular problem. When we move the root from `v` to its child `c`:
- All `sz[c]` nodes in `c`'s subtree get 1 closer → subtract `sz[c]`
- All `N - sz[c]` nodes outside get 1 farther → add `N - sz[c]`

So:
```
answer[c] = answer[v] - sz[c] + (N - sz[c])
          = answer[v] + N - 2·sz[c]
```

where `answer[v]` is the full answer for `v` (which equals `down[v] + up[v]`).

Start with `answer[0] = 8`, N = 6:

| Move | Computation | answer |
|------|-------------|--------|
| 0 → 1 | 8 + 6 - 2·3 = 8 | 8 |
| 0 → 2 | 8 + 6 - 2·2 = 10 | 10 |
| 1 → 3 | 8 + 6 - 2·1 = 12 | 12 |
| 1 → 4 | 8 + 6 - 2·1 = 12 | 12 |
| 2 → 5 | 10 + 6 - 2·1 = 14 | 14 |

**Final answers:** `[8, 8, 10, 12, 12, 14]`

**Verify node 3:** dist(3→0)=2, 3→1=1, 3→2=3, 3→4=2, 3→5=4. Sum = 12. Correct!

### C++ Implementation

```cpp
#include <vector>
using namespace std;

vector<int> sumOfDistancesInTree(int n, vector<vector<int>>& edges) {
    vector<vector<int>> adj(n);
    for (auto& e : edges) {
        adj[e[0]].push_back(e[1]);
        adj[e[1]].push_back(e[0]);
    }

    vector<int> sz(n, 1);
    vector<long long> down(n, 0), answer(n, 0);

    // Pass 1: bottom-up from root 0
    // Iterative post-order using a stack
    vector<int> order, parent(n, -1);
    vector<bool> visited(n, false);
    order.reserve(n);
    vector<int> stk = {0};
    visited[0] = true;
    while (!stk.empty()) {
        int u = stk.back(); stk.pop_back();
        order.push_back(u);
        for (int v : adj[u]) {
            if (!visited[v]) {
                visited[v] = true;
                parent[v] = u;
                stk.push_back(v);
            }
        }
    }

    // Process in reverse order (post-order)
    for (int i = n - 1; i >= 0; i--) {
        int u = order[i];
        for (int v : adj[u]) {
            if (v != parent[u]) {
                sz[u] += sz[v];
                down[u] += down[v] + sz[v];
            }
        }
    }

    // Pass 2: top-down (pre-order)
    answer[0] = down[0];
    for (int i = 0; i < n; i++) {
        int u = order[i];
        for (int v : adj[u]) {
            if (v != parent[u]) {
                answer[v] = answer[u] + n - 2 * sz[v];
            }
        }
    }

    return vector<int>(answer.begin(), answer.end());
}
```

**Time: O(N), Space: O(N).**

---

## 7. Worked Example 2 — Maximum Depth When Rooted at Each Node

> **Problem:** Given a tree, for each node `v`, find the height (maximum depth of any node) when the tree is rooted at `v`.

**Tree:**
```
        0
       / \
      1   2
     /     \
    3       4
   /
  5
```

### Pass 1: Bottom-Up — Compute `down[v]` = height of subtree rooted at `v`

```
down[leaf] = 0
down[v] = max over children c of (down[c] + 1)
```

| Node | down | Explanation |
|------|------|---|
| 5 | 0 | Leaf |
| 4 | 0 | Leaf |
| 3 | 1 | child 5: 0+1=1 |
| 1 | 2 | child 3: 1+1=2 |
| 2 | 1 | child 4: 0+1=1 |
| 0 | 3 | max(2+1, 1+1) = 3 |

### Pass 2: Top-Down — Compute `up[v]`

`up[v]` = the longest path starting from `v` going through its parent and beyond.

For the root: `up[0] = 0`.

For each child `c` of `v`:
```
up[c] = 1 + max(up[v], best_down_among_siblings_of_c)
```

Here's the catch: `best_down_among_siblings_of_c` is the maximum `(down[s] + 1)` over all children `s` of `v` where `s ≠ c`. If `c` is the child that *achieves* the maximum, we need the **second maximum**.

**Solution:** For each node, store the top-2 `(down[c]+1)` values among its children.

For node 0, children are 1 and 2:
- Values: down[1]+1=3, down[2]+1=2
- Top-2: [3, 2]

For computing `up[1]`: `c=1` achieves the max (3), so use second-best = 2.
```
up[1] = 1 + max(up[0], 2) = 1 + max(0, 2) = 3
```

For computing `up[2]`: `c=2` does not achieve the max, so use best = 3.
```
up[2] = 1 + max(up[0], 3) = 1 + max(0, 3) = 4
```

Continue:

For node 1, child is 3:
- Values: down[3]+1=2
- `up[3] = 1 + max(up[1], 0) = 1 + 3 = 4`
  (0 because there are no siblings of 3)

For node 3, child is 5:
- `up[5] = 1 + max(up[3], 0) = 1 + 4 = 5`

For node 2, child is 4:
- `up[4] = 1 + max(up[2], 0) = 1 + 4 = 5`

### Final answers

```
answer[v] = max(down[v], up[v])
```

| Node | down | up | answer (height when rooted at v) |
|------|------|-----|---|
| 0 | 3 | 0 | 3 |
| 1 | 2 | 3 | 3 |
| 2 | 1 | 4 | 4 |
| 3 | 1 | 4 | 4 |
| 4 | 0 | 5 | 5 |
| 5 | 0 | 5 | 5 |

**Verify node 3:** Rooted at 3, the farthest node is 4 (path: 3→1→0→2→4, length=4). Correct!

**Verify node 1:** Rooted at 1, farthest is either 5 (path: 1→3→5, length=2) or 4 (path: 1→0→2→4, length=3). Max = 3. Correct!

### C++ Implementation

```cpp
#include <vector>
#include <algorithm>
using namespace std;

vector<int> heightWhenRooted(int n, vector<vector<int>>& adj) {
    vector<int> parent(n, -1), order;
    vector<int> down(n, 0), up(n, 0);
    // top1[v], top2[v] = best and second-best (down[c]+1) among children of v
    // top1_child[v] = which child achieves top1
    vector<int> top1(n, 0), top2(n, 0), top1_child(n, -1);

    // BFS to get order and parents
    vector<bool> visited(n, false);
    vector<int> stk = {0};
    visited[0] = true;
    while (!stk.empty()) {
        int u = stk.back(); stk.pop_back();
        order.push_back(u);
        for (int v : adj[u]) {
            if (!visited[v]) {
                visited[v] = true;
                parent[v] = u;
                stk.push_back(v);
            }
        }
    }

    // Pass 1: bottom-up
    for (int i = n - 1; i >= 0; i--) {
        int u = order[i];
        for (int v : adj[u]) {
            if (v == parent[u]) continue;
            int val = down[v] + 1;
            if (val >= top1[u]) {
                top2[u] = top1[u];
                top1[u] = val;
                top1_child[u] = v;
            } else if (val > top2[u]) {
                top2[u] = val;
            }
            down[u] = max(down[u], val);
        }
    }

    // Pass 2: top-down
    up[0] = 0;
    for (int i = 0; i < n; i++) {
        int u = order[i];
        for (int v : adj[u]) {
            if (v == parent[u]) continue;
            // Best from siblings: if v achieved top1, use top2; else use top1
            int best_sibling = (v == top1_child[u]) ? top2[u] : top1[u];
            up[v] = 1 + max(up[u], best_sibling);
        }
    }

    vector<int> answer(n);
    for (int i = 0; i < n; i++) {
        answer[i] = max(down[i], up[i]);
    }
    return answer;
}
```

---

## 8. Worked Example 3 — Subtree Sum Product (Weighted Trees)

> **Problem:** Given a tree where each node `v` has a weight `w[v]`, for each node `v` as root, compute the sum over all nodes `u` of `w[u] * depth(u)`, where `depth(u)` is the distance from `v` to `u`.

This is a generalization of "sum of distances" where distances are weighted by node values.

**Tree (weights in parentheses):**
```
       0 (2)
      / \
    1(3)  2(1)
    |      |
   3(4)   4(5)
```

### Pass 1: Bottom-Up

We need two values per subtree:
- `sz[v]` = sum of weights in subtree: `sz[v] = w[v] + Σ sz[c]`
- `down[v]` = Σ over nodes u in subtree of v: `w[u] * dist(v, u)`

Recurrence:
```
down[v] = Σ_c (down[c] + sz[c])
```
(Each node in child c's subtree is 1 farther from v than from c, contributing `sz[c]` extra.)

| Node | w | sz | down |
|------|---|-----|------|
| 3 | 4 | 4 | 0 |
| 4 | 5 | 5 | 0 |
| 1 | 3 | 7 | 0+4 = 4 |
| 2 | 1 | 6 | 0+5 = 5 |
| 0 | 2 | 15 | (4+7)+(5+6) = 22 |

**Verify `down[0]`:** 2·0 + 3·1 + 1·1 + 4·2 + 5·2 = 0+3+1+8+10 = 22. Correct!

### Pass 2: Top-Down

When we move root from `v` to child `c`:
```
answer[c] = answer[v] - sz[c] + (total_weight - sz[c])
          = answer[v] + total_weight - 2·sz[c]
```

where `total_weight = sz[root] = 15`.

| Move | Computation | answer |
|------|-------------|--------|
| root=0 | — | 22 |
| 0→1 | 22 + 15 - 2·7 = 23 | 23 |
| 0→2 | 22 + 15 - 2·6 = 25 | 25 |
| 1→3 | 23 + 15 - 2·4 = 30 | 30 |
| 2→4 | 25 + 15 - 2·5 = 30 | 30 |

**Verify `answer[3]` (root at node 3):**
- dist(3→1)=1, dist(3→0)=2, dist(3→2)=3, dist(3→4)=4
- 4·0 + 3·1 + 2·2 + 1·3 + 5·4 = 0+3+4+3+20 = 30. Correct!

---

## 9. Worked Example 4 — Count Nodes at Even Distance

> **Problem:** For each node `v`, count how many other nodes are at an even distance from `v`.

**Key Insight:** Parity of distance only depends on the *depth parity* relative to the root. If we root at 0, nodes at even depth have even distance to 0; nodes at odd depth have odd distance. When we move the root by one edge, all parities flip.

**Tree:**
```
       0
      /|\
     1  2  3
    / \
   4   5
```

### Pass 1: Bottom-Up

Track two counts per subtree:
- `even[v]` = number of nodes at even distance from `v` within its subtree (including `v` itself)
- `odd[v]` = number of nodes at odd distance from `v` within its subtree

```
even[leaf] = 1, odd[leaf] = 0
even[v] = 1 + Σ odd[c]     (children at dist 1 are odd, their even-dist descendants become odd+1=even)
odd[v] = Σ even[c]          (children's even-dist nodes become odd-dist from v)
```

| Node | even | odd |
|------|------|-----|
| 4 | 1 | 0 |
| 5 | 1 | 0 |
| 1 | 1+0+0=1 | 1+1=2 |
| 2 | 1 | 0 |
| 3 | 1 | 0 |
| 0 | 1+2+0+0=3 | 1+1+1=3 |

**Verify node 0:** Even-dist nodes from 0: {0, 4, 5} → 3. Odd-dist: {1, 2, 3} → 3. Correct!

### Pass 2: Top-Down

For each child `c` of `v`:
```
up_even[c] = 1 + up_odd[v] + (odd[v] - even[c])
up_odd[c] = up_even[v] + (even[v] - odd[c] - 1)
```

The `-even[c]` and `-odd[c]-1` terms exclude child `c`'s own contribution from `v`'s totals.

Starting: `up_even[0] = 0, up_odd[0] = 0` (nothing outside root).

**For child 1 of node 0:**
```
up_even[1] = 1 + up_odd[0] + (odd[0] - even[1])
           = 1 + 0 + (3 - 1) = 3
up_odd[1]  = up_even[0] + (even[0] - odd[1] - 1)
           = 0 + (3 - 2 - 1) = 0
```

**For child 2 of node 0:**
```
up_even[2] = 1 + 0 + (3 - 1) = 3
up_odd[2]  = 0 + (3 - 0 - 1) = 2
```

**For child 3 of node 0:**
```
up_even[3] = 1 + 0 + (3 - 1) = 3
up_odd[3]  = 0 + (3 - 0 - 1) = 2
```

**For child 4 of node 1:**
```
up_even[4] = 1 + up_odd[1] + (odd[1] - even[4])
           = 1 + 0 + (2 - 1) = 2
up_odd[4]  = up_even[1] + (even[1] - odd[4] - 1)
           = 3 + (1 - 0 - 1) = 3
```

**For child 5 of node 1:** (symmetric to child 4)
```
up_even[5] = 1 + 0 + (2 - 1) = 2
up_odd[5]  = 3 + (1 - 0 - 1) = 3
```

### Final Answers

```
answer[v] = (even[v] + up_even[v]) - 1    (-1 to exclude v itself if needed)
```

| Node | even+up_even (total even-dist including self) | answer (excluding self) |
|------|---|---|
| 0 | 3+0 = 3 | 2 |
| 1 | 1+3 = 4 | 3 |
| 2 | 1+3 = 4 | 3 |
| 3 | 1+3 = 4 | 3 |
| 4 | 1+2 = 3 | 2 |
| 5 | 1+2 = 3 | 2 |

**Verify node 1:** Distances from 1: 0→1, 2→2, 3→2, 4→1, 5→1. Even distances: {0(self), 2, 3} → 3 (excluding self). Correct!

---

## 10. Worked Example 5 — Minimum Height Trees

> **Problem (LeetCode 310):** Find all nodes such that the tree has minimum possible height when rooted at that node.

This is a direct application of Example 2. Compute the height for every root using rerooting, then return nodes with the minimum height.

**But there's an elegant insight:** The answer is always 1 or 2 nodes — the center(s) of the tree's longest path (diameter). However, the rerooting technique gives a general O(N) solution and extends to variations where this nice structural property doesn't hold.

Using the technique from Example 2:

```cpp
vector<int> findMinHeightTrees(int n, vector<vector<int>>& edges) {
    if (n == 1) return {0};

    vector<vector<int>> adj(n);
    for (auto& e : edges) {
        adj[e[0]].push_back(e[1]);
        adj[e[1]].push_back(e[0]);
    }

    vector<int> heights = heightWhenRooted(n, adj); // from Example 2

    int minH = *min_element(heights.begin(), heights.end());
    vector<int> result;
    for (int i = 0; i < n; i++) {
        if (heights[i] == minH) result.push_back(i);
    }
    return result;
}
```

---

## 11. General Template (C++ Pseudocode)

Here is a generic rerooting template using prefix-suffix decomposition that handles both commutative and non-commutative MERGE operations:

```cpp
#include <vector>
#include <functional>
using namespace std;

template<typename T>
struct Reroot {
    int n;
    vector<vector<pair<int,int>>> adj; // adj[u] = {(v, edge_id), ...}
    vector<T> down;    // subtree answer
    vector<T> up;      // complement answer
    vector<T> answer;  // full answer per root

    T identity;                         // identity element for merge
    function<T(T, T)> merge;            // associative merge
    function<T(T, int)> lift;           // lift child value across edge
    function<T(T, T)> combine;          // combine down and up for final answer

    vector<int> parent, order;

    void build(int root = 0) {
        down.assign(n, identity);
        up.assign(n, identity);
        answer.resize(n);
        parent.assign(n, -1);
        order.reserve(n);

        // BFS for ordering
        vector<bool> vis(n, false);
        vector<int> stk = {root};
        vis[root] = true;
        while (!stk.empty()) {
            int u = stk.back(); stk.pop_back();
            order.push_back(u);
            for (auto [v, eid] : adj[u]) {
                if (!vis[v]) {
                    vis[v] = true;
                    parent[v] = u;
                    stk.push_back(v);
                }
            }
        }

        // Pass 1: bottom-up
        for (int i = n - 1; i >= 0; i--) {
            int u = order[i];
            for (auto [v, eid] : adj[u]) {
                if (v == parent[u]) continue;
                down[u] = merge(down[u], lift(down[v], eid));
            }
        }

        // Pass 2: top-down with prefix-suffix
        up[root] = identity;
        for (int i = 0; i < n; i++) {
            int u = order[i];

            // Collect children's lifted values
            vector<pair<int,T>> children; // (child_node, lifted_value)
            for (auto [v, eid] : adj[u]) {
                if (v == parent[u]) continue;
                children.push_back({v, lift(down[v], eid)});
            }

            int k = children.size();
            // Prefix and suffix merges
            vector<T> prefix(k + 1, identity), suffix(k + 1, identity);
            for (int j = 0; j < k; j++)
                prefix[j + 1] = merge(prefix[j], children[j].second);
            for (int j = k - 1; j >= 0; j--)
                suffix[j] = merge(children[j].second, suffix[j + 1]);

            for (int j = 0; j < k; j++) {
                int c = children[j].first;
                int eid = -1; // find edge id for (u,c) if needed
                for (auto [v, e] : adj[u]) {
                    if (v == c) { eid = e; break; }
                }
                T siblings = merge(prefix[j], suffix[j + 1]);
                T from_parent = merge(up[u], siblings);
                up[c] = lift(from_parent, eid);
            }
        }

        // Final answer
        for (int i = 0; i < n; i++) {
            answer[i] = combine(down[i], up[i]);
        }
    }
};
```

### Usage Pattern

```cpp
Reroot<long long> solver;
solver.n = n;
solver.adj = adj;
solver.identity = 0;
solver.merge = [](long long a, long long b) { return a + b; };
solver.lift = [](long long val, int eid) { return val + 1; };
solver.combine = [](long long d, long long u) { return d + u; };
solver.build(0);
// solver.answer[v] is the answer for each root v
```

---

## 12. Common Pitfalls

### 1. Forgetting the Identity Element

If your MERGE is `max`, the identity is `0` (or `-∞` for negative values), not `1`.
If your MERGE is `+`, the identity is `0`.
If your MERGE is `*`, the identity is `1`.

Getting the identity wrong corrupts the prefix-suffix decomposition.

### 2. Confusing "Exclude One Child" Logic

When computing `up[c]`, you need to exclude `c`'s contribution from `v`'s downward answer. A common bug is subtracting from a `max` — **you cannot subtract from max**. Use the top-2 approach or prefix-suffix, not subtraction.

```
WRONG:  up[c] = 1 + max(up[v], down[v] - (down[c]+1))   // can't "undo" max
RIGHT:  up[c] = 1 + max(up[v], second_best_among_siblings)
```

### 3. Off-by-One in Depth/Distance

Be consistent about whether a node's distance to itself is 0 or whether you count edges or nodes.

### 4. Directed vs Undirected Edges

The tree must be treated as undirected (each edge stored in both directions). When processing, skip the parent edge with `if (v == parent[u]) continue`.

### 5. Not Handling the Root's `up` Value

`up[root]` must be explicitly initialized to the identity. It has no parent contribution.

### 6. Star Graph Performance

A star graph (one center connected to N-1 leaves) gives one node degree N-1. Without prefix-suffix decomposition, the "exclude one child" step is O(N-1) per child = O(N²) total. Always use prefix-suffix or the top-2 trick for max-based problems.

---

## 13. When Rerooting Does NOT Work

Rerooting requires that the answer decomposes into **independent subtree contributions** that can be merged and unmerged (or excluded). It does **not** work when:

1. **The answer depends on global tree structure** in a non-decomposable way.
   - Example: "For each root, find the number of distinct paths of length exactly k." (Path counting across subtrees involves convolution, not simple merging.)

2. **The merge operation has no inverse and is not cancellable.**
   - Median, mode, count-distinct are not monoids with efficient "remove one element."
   - However, for `max` (no inverse), the top-2 trick or prefix-suffix still works.

3. **The answer depends on the ordering of children** in a way that changes with rerooting.

4. **The problem involves edge directionality** that fundamentally changes with rerooting.

---

## 14. Complexity Analysis

| Phase | Time | Space |
|-------|------|-------|
| Build adjacency list | O(N) | O(N) |
| Pass 1 (bottom-up) | O(N) | O(N) |
| Pass 2 (top-down) with prefix-suffix | O(N) total | O(N) |
| **Total** | **O(N)** | **O(N)** |

**Why O(N) total for Pass 2?**
Each node `v` with degree `d(v)` does O(d(v)) work for prefix-suffix arrays. Summing over all nodes: Σ d(v) = 2(N-1) = O(N). This holds even for star graphs.

**Comparison:**

| Approach | Time | Space |
|---|---|---|
| Brute force (reroot + DFS each time) | O(N²) | O(N) |
| Rerooting technique | O(N) | O(N) |

For N = 10⁶, that's the difference between ~10¹² operations (hours) and ~10⁶ operations (milliseconds).

---

## 15. Practice Problems

| Problem | Source | Key Rerooting Aspect |
|---|---|---|
| [Sum of Distances in Tree](https://leetcode.com/problems/sum-of-distances-in-tree/) | LeetCode 834 | Sum + count rerooting |
| [Minimum Height Trees](https://leetcode.com/problems/minimum-height-trees/) | LeetCode 310 | Max-based rerooting (or trimming) |
| [Count Nodes at Even Distance](https://codeforces.com/problemset/problem/1092/F) | Codeforces | Parity tracking |
| [Tree Distances I](https://cses.fi/problemset/task/1132) | CSES | Max distance from each node |
| [Tree Distances II](https://cses.fi/problemset/task/1133) | CSES | Sum of distances (classic) |
| [Choosing Capital for Treeland](https://codeforces.com/problemset/problem/219/D) | Codeforces | Directed edge counting |
| [Subtree Sum Queries](https://codeforces.com/blog/entry/68138) | Codeforces | Weighted rerooting |
| [Distance in Tree](https://codeforces.com/problemset/problem/161/D) | Codeforces | Count pairs at distance k |

---

## Summary

The rerooting technique follows a clean recipe:

```
1. Pick any root. Run bottom-up DFS to compute down[v] for all v.
2. Run top-down DFS to compute up[v] for all v.
   - Use prefix-suffix decomposition to exclude each child in O(1).
3. Combine: answer[v] = combine(down[v], up[v]).
```

The entire technique boils down to one insight: **moving the root by one edge changes the answer locally, and that local change can be precomputed**. This transforms an O(N²) brute force into an elegant O(N) algorithm.
