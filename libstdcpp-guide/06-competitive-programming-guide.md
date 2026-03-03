# libstdc++ for Competitive Programming: Complete Guide

## Table of Contents
1. [Essential STL for Competitive Programming](#essential-stl-for-competitive-programming)
2. [Fast Input/Output Techniques](#fast-inputoutput-techniques)
3. [Container Selection Guide](#container-selection-guide)
4. [Algorithm Cheat Sheet](#algorithm-cheat-sheet)
5. [Common Patterns and Idioms](#common-patterns-and-idioms)
6. [Advanced Data Structures](#advanced-data-structures)
7. [Optimization Tricks](#optimization-tricks)
8. [Common Pitfalls and Solutions](#common-pitfalls-and-solutions)
9. [Template Library for Contests](#template-library-for-contests)

---

## Essential STL for Competitive Programming

### Must-Know Containers

#### 1. vector - Dynamic Array

```cpp
#include <vector>

// Declaration
vector<int> v;
vector<int> v(n);           // Size n, default initialized
vector<int> v(n, val);      // Size n, all elements = val
vector<int> v = {1, 2, 3};  // Initializer list

// Common operations - O(1) amortized
v.push_back(x);             // Add to end
v.pop_back();               // Remove from end
v[i];                       // Access (no bounds check)
v.at(i);                    // Access (with bounds check)
v.front();                  // First element
v.back();                   // Last element
v.size();                   // Number of elements
v.empty();                  // Check if empty
v.clear();                  // Remove all elements

// Iteration
for (int x : v) { }         // Range-based for
for (auto& x : v) { }       // By reference
for (int i = 0; i < v.size(); i++) { }

// Useful operations
v.resize(n);                // Change size
v.reserve(n);               // Reserve capacity (avoid reallocation)
v.assign(n, val);           // Assign n copies of val
v.insert(v.begin() + i, x); // Insert at position i - O(n)
v.erase(v.begin() + i);     // Erase at position i - O(n)

// 2D vector
vector<vector<int>> grid(n, vector<int>(m, 0));  // n×m grid
```

**When to use:** Default choice, random access needed, dynamic size

#### 2. set - Ordered Unique Elements

```cpp
#include <set>

set<int> s;

// Operations - O(log n)
s.insert(x);                // Insert element
s.erase(x);                 // Remove element by value
s.erase(it);                // Remove element by iterator
s.count(x);                 // Check if exists (0 or 1)
s.find(x);                  // Find element, returns iterator
s.size();                   // Number of elements
s.empty();                  // Check if empty
s.clear();                  // Remove all elements

// Ordered operations
s.lower_bound(x);           // First element >= x
s.upper_bound(x);           // First element > x
*s.begin();                 // Minimum element
*s.rbegin();                // Maximum element

// Iteration (sorted order)
for (int x : s) { }

// Custom comparator
set<int, greater<int>> s;   // Descending order
auto cmp = [](int a, int b) { return a > b; };
set<int, decltype(cmp)> s(cmp);
```

**When to use:** Need sorted unique elements, range queries

#### 3. multiset - Ordered Elements (Duplicates Allowed)

```cpp
#include <set>

multiset<int> ms;

// Same as set, but allows duplicates
ms.insert(x);               // Insert (can insert duplicates)
ms.erase(x);                // Remove ALL occurrences
ms.erase(ms.find(x));       // Remove single occurrence
ms.count(x);                // Count occurrences

// Find k-th smallest element
auto it = ms.begin();
advance(it, k);             // O(k)
```

**When to use:** Need sorted elements with duplicates, frequency tracking

#### 4. map - Key-Value Pairs (Ordered)

```cpp
#include <map>

map<string, int> m;

// Operations - O(log n)
m[key] = value;             // Insert or update
m.insert({key, value});     // Insert
m.erase(key);               // Remove by key
m.count(key);               // Check if exists (0 or 1)
m.find(key);                // Find, returns iterator
m.size();                   // Number of pairs

// Access (creates if not exists)
int val = m[key];           // Returns 0 if key doesn't exist

// Safe access
if (m.count(key)) {
    int val = m[key];
}

// Iteration (sorted by key)
for (auto& [key, value] : m) {
    // C++17 structured binding
}
for (auto& p : m) {
    // p.first = key, p.second = value
}

// Ordered operations
m.lower_bound(key);
m.upper_bound(key);
```

**When to use:** Key-value mapping, need sorted keys

#### 5. unordered_map - Hash Table

```cpp
#include <unordered_map>

unordered_map<string, int> um;

// Operations - O(1) average, O(n) worst
um[key] = value;
um.insert({key, value});
um.erase(key);
um.count(key);
um.find(key);

// Custom hash for pairs
struct hash_pair {
    template <class T1, class T2>
    size_t operator()(const pair<T1, T2>& p) const {
        auto h1 = hash<T1>{}(p.first);
        auto h2 = hash<T2>{}(p.second);
        return h1 ^ h2;
    }
};
unordered_map<pair<int,int>, int, hash_pair> um;
```

**When to use:** Fast lookups, order doesn't matter

#### 6. priority_queue - Heap

```cpp
#include <queue>

// Max heap (default)
priority_queue<int> pq;

// Min heap
priority_queue<int, vector<int>, greater<int>> pq;

// Custom comparator
auto cmp = [](int a, int b) { return a > b; };
priority_queue<int, vector<int>, decltype(cmp)> pq(cmp);

// Operations - O(log n)
pq.push(x);                 // Insert
pq.pop();                   // Remove top
pq.top();                   // Access top (max/min)
pq.size();
pq.empty();

// Pairs (sorted by first, then second)
priority_queue<pair<int,int>> pq;
pq.push({priority, value});
```

**When to use:** Need min/max element efficiently, Dijkstra, greedy algorithms

#### 7. deque - Double-Ended Queue

```cpp
#include <deque>

deque<int> dq;

// Operations - O(1)
dq.push_back(x);            // Add to end
dq.push_front(x);           // Add to front
dq.pop_back();              // Remove from end
dq.pop_front();             // Remove from front
dq[i];                      // Random access - O(1)
dq.front();
dq.back();
```

**When to use:** Need efficient insertion/deletion at both ends, sliding window

#### 8. stack and queue

```cpp
#include <stack>
#include <queue>

// Stack (LIFO)
stack<int> st;
st.push(x);
st.pop();
st.top();
st.empty();
st.size();

// Queue (FIFO)
queue<int> q;
q.push(x);
q.pop();
q.front();
q.back();
q.empty();
q.size();
```

---

## Fast Input/Output Techniques

### Standard Fast I/O

```cpp
#include <iostream>
using namespace std;

int main() {
    // Disable synchronization with C stdio
    ios_base::sync_with_stdio(false);
    
    // Untie cin from cout
    cin.tie(nullptr);
    
    // Optional: untie cout (use with caution)
    cout.tie(nullptr);
    
    int n;
    cin >> n;
    
    // Your code here
    
    return 0;
}
```

**Speed improvement:** 2-3x faster than default

### Reading Multiple Values

```cpp
// Read n integers
int n;
cin >> n;
vector<int> a(n);
for (int& x : a) cin >> x;

// Read until EOF
int x;
while (cin >> x) {
    // process x
}

// Read line
string line;
getline(cin, line);

// Read entire input
string s;
while (getline(cin, s)) {
    // process line
}
```

### Custom Fast Input (For Extreme Cases)

```cpp
inline int read() {
    int x = 0, f = 1;
    char ch = getchar();
    while (ch < '0' || ch > '9') {
        if (ch == '-') f = -1;
        ch = getchar();
    }
    while (ch >= '0' && ch <= '9') {
        x = x * 10 + ch - '0';
        ch = getchar();
    }
    return x * f;
}

inline void write(int x) {
    if (x < 0) {
        putchar('-');
        x = -x;
    }
    if (x > 9) write(x / 10);
    putchar(x % 10 + '0');
}
```

### Output Formatting

```cpp
#include <iomanip>

// Fixed precision
cout << fixed << setprecision(6) << 3.14159 << '\n';  // 3.141590

// Width and fill
cout << setw(5) << setfill('0') << 42 << '\n';  // 00042

// Use '\n' instead of endl (faster)
cout << x << '\n';  // Preferred
cout << x << endl;  // Slower (flushes buffer)
```

---

## Container Selection Guide

### Quick Reference Table

| Need | Container | Time Complexity |
|------|-----------|----------------|
| Random access | `vector`, `deque` | O(1) |
| Insert/delete at end | `vector` | O(1) amortized |
| Insert/delete at front | `deque`, `list` | O(1) |
| Insert/delete anywhere | `list` | O(1) with iterator |
| Sorted unique elements | `set` | O(log n) |
| Sorted with duplicates | `multiset` | O(log n) |
| Key-value (sorted) | `map` | O(log n) |
| Key-value (fast) | `unordered_map` | O(1) average |
| Min/max element | `priority_queue` | O(log n) insert, O(1) access |
| LIFO | `stack` | O(1) |
| FIFO | `queue` | O(1) |

### Decision Tree

```
Need key-value mapping?
├─ Yes
│  ├─ Need sorted keys? → map
│  └─ Don't need sorted? → unordered_map
│
└─ No
   ├─ Need sorted elements?
   │  ├─ Unique? → set
   │  └─ Duplicates? → multiset
   │
   ├─ Need min/max? → priority_queue
   │
   ├─ Need LIFO? → stack
   │
   ├─ Need FIFO? → queue
   │
   └─ Need random access?
      ├─ Insert/delete at both ends? → deque
      └─ Otherwise → vector
```

---

## Algorithm Cheat Sheet

### Sorting

```cpp
#include <algorithm>

vector<int> v = {3, 1, 4, 1, 5, 9};

// Sort ascending - O(n log n)
sort(v.begin(), v.end());

// Sort descending
sort(v.begin(), v.end(), greater<int>());

// Custom comparator
sort(v.begin(), v.end(), [](int a, int b) {
    return a > b;  // Descending
});

// Sort pairs (by first, then second)
vector<pair<int,int>> vp = {{3,1}, {1,4}, {1,2}};
sort(vp.begin(), vp.end());  // {1,2}, {1,4}, {3,1}

// Sort by second element
sort(vp.begin(), vp.end(), [](auto& a, auto& b) {
    return a.second < b.second;
});

// Stable sort (preserves relative order)
stable_sort(v.begin(), v.end());

// Partial sort (sort first k elements)
partial_sort(v.begin(), v.begin() + k, v.end());

// nth_element (partition around nth element)
nth_element(v.begin(), v.begin() + k, v.end());  // k-th smallest at position k

// Check if sorted
bool sorted = is_sorted(v.begin(), v.end());
```

### Searching

```cpp
vector<int> v = {1, 2, 3, 4, 5, 6, 7, 8, 9};

// Binary search (requires sorted array) - O(log n)
bool found = binary_search(v.begin(), v.end(), 5);

// Lower bound: first element >= x
auto it = lower_bound(v.begin(), v.end(), 5);
int idx = it - v.begin();

// Upper bound: first element > x
auto it = upper_bound(v.begin(), v.end(), 5);

// Equal range: [lower_bound, upper_bound)
auto [lo, hi] = equal_range(v.begin(), v.end(), 5);

// Linear search - O(n)
auto it = find(v.begin(), v.end(), 5);
if (it != v.end()) {
    // Found at position: it - v.begin()
}

// Find with condition
auto it = find_if(v.begin(), v.end(), [](int x) {
    return x % 2 == 0;  // Find first even
});

// Count occurrences - O(n)
int cnt = count(v.begin(), v.end(), 5);

// Count with condition
int cnt = count_if(v.begin(), v.end(), [](int x) {
    return x % 2 == 0;  // Count evens
});
```

### Min/Max

```cpp
vector<int> v = {3, 1, 4, 1, 5, 9};

// Min/max element - O(n)
int minVal = *min_element(v.begin(), v.end());
int maxVal = *max_element(v.begin(), v.end());

// Min/max of two values
int minVal = min(a, b);
int maxVal = max(a, b);

// Min/max of multiple values (C++11)
int minVal = min({a, b, c, d});
int maxVal = max({a, b, c, d});

// Min/max with custom comparator
auto it = min_element(v.begin(), v.end(), [](int a, int b) {
    return abs(a) < abs(b);
});

// Both min and max - O(n)
auto [minIt, maxIt] = minmax_element(v.begin(), v.end());
```

### Permutations and Combinations

```cpp
vector<int> v = {1, 2, 3};

// Next permutation
do {
    // Process permutation
    for (int x : v) cout << x << ' ';
    cout << '\n';
} while (next_permutation(v.begin(), v.end()));

// Previous permutation
while (prev_permutation(v.begin(), v.end())) {
    // Process
}

// Check if permutation
vector<int> a = {1, 2, 3};
vector<int> b = {3, 1, 2};
bool isPerm = is_permutation(a.begin(), a.end(), b.begin());
```

### Reversing and Rotating

```cpp
vector<int> v = {1, 2, 3, 4, 5};

// Reverse - O(n)
reverse(v.begin(), v.end());  // {5, 4, 3, 2, 1}

// Rotate left by k positions - O(n)
rotate(v.begin(), v.begin() + k, v.end());
// {1,2,3,4,5} with k=2 → {3,4,5,1,2}

// Rotate right by k positions
rotate(v.rbegin(), v.rbegin() + k, v.rend());
```

### Removing and Unique

```cpp
vector<int> v = {1, 2, 2, 3, 3, 3, 4, 5, 5};

// Remove specific value - O(n)
v.erase(remove(v.begin(), v.end(), 3), v.end());

// Remove if condition
v.erase(remove_if(v.begin(), v.end(), [](int x) {
    return x % 2 == 0;  // Remove evens
}), v.end());

// Remove consecutive duplicates (requires sorted) - O(n)
v.erase(unique(v.begin(), v.end()), v.end());

// Remove all duplicates
sort(v.begin(), v.end());
v.erase(unique(v.begin(), v.end()), v.end());
```

### Accumulation and Reduction

```cpp
#include <numeric>

vector<int> v = {1, 2, 3, 4, 5};

// Sum - O(n)
int sum = accumulate(v.begin(), v.end(), 0);

// Product
int prod = accumulate(v.begin(), v.end(), 1, multiplies<int>());

// Custom operation
int result = accumulate(v.begin(), v.end(), 0, [](int acc, int x) {
    return acc + x * x;  // Sum of squares
});

// GCD of array
int g = accumulate(v.begin(), v.end(), 0, [](int a, int b) {
    return __gcd(a, b);
});

// Partial sum (prefix sum) - O(n)
vector<int> prefix(n);
partial_sum(v.begin(), v.end(), prefix.begin());

// Adjacent difference
vector<int> diff(n);
adjacent_difference(v.begin(), v.end(), diff.begin());

// Inner product (dot product)
vector<int> a = {1, 2, 3};
vector<int> b = {4, 5, 6};
int dot = inner_product(a.begin(), a.end(), b.begin(), 0);
```

### Filling and Generating

```cpp
vector<int> v(n);

// Fill with value - O(n)
fill(v.begin(), v.end(), 42);

// Fill n elements
fill_n(v.begin(), n, 42);

// Generate with function
int counter = 0;
generate(v.begin(), v.end(), [&counter]() {
    return counter++;
});

// Iota (fill with incrementing values)
iota(v.begin(), v.end(), 0);  // {0, 1, 2, 3, ...}
```

### Set Operations (Requires Sorted Ranges)

```cpp
vector<int> a = {1, 2, 3, 4, 5};
vector<int> b = {3, 4, 5, 6, 7};
vector<int> result;

// Union
set_union(a.begin(), a.end(), b.begin(), b.end(), 
          back_inserter(result));
// {1, 2, 3, 4, 5, 6, 7}

// Intersection
set_intersection(a.begin(), a.end(), b.begin(), b.end(),
                back_inserter(result));
// {3, 4, 5}

// Difference (a - b)
set_difference(a.begin(), a.end(), b.begin(), b.end(),
              back_inserter(result));
// {1, 2}

// Symmetric difference (a XOR b)
set_symmetric_difference(a.begin(), a.end(), b.begin(), b.end(),
                        back_inserter(result));
// {1, 2, 6, 7}

// Check if b is subset of a
bool isSubset = includes(a.begin(), a.end(), b.begin(), b.end());
```

---

## Common Patterns and Idioms

### Two Pointers

```cpp
// Find pair with sum = target
vector<int> v = {1, 2, 3, 4, 5, 6};
sort(v.begin(), v.end());
int target = 7;

int left = 0, right = v.size() - 1;
while (left < right) {
    int sum = v[left] + v[right];
    if (sum == target) {
        cout << v[left] << " + " << v[right] << " = " << target << '\n';
        break;
    } else if (sum < target) {
        left++;
    } else {
        right--;
    }
}

// Remove duplicates from sorted array
int j = 0;
for (int i = 1; i < n; i++) {
    if (v[i] != v[j]) {
        v[++j] = v[i];
    }
}
v.resize(j + 1);
```

### Sliding Window

```cpp
// Maximum sum subarray of size k
int maxSum = 0, windowSum = 0;
for (int i = 0; i < k; i++) {
    windowSum += v[i];
}
maxSum = windowSum;

for (int i = k; i < n; i++) {
    windowSum += v[i] - v[i - k];
    maxSum = max(maxSum, windowSum);
}

// Longest substring with at most k distinct characters
unordered_map<char, int> freq;
int left = 0, maxLen = 0;
for (int right = 0; right < s.length(); right++) {
    freq[s[right]]++;
    
    while (freq.size() > k) {
        freq[s[left]]--;
        if (freq[s[left]] == 0) {
            freq.erase(s[left]);
        }
        left++;
    }
    
    maxLen = max(maxLen, right - left + 1);
}
```

### Prefix Sum

```cpp
// Build prefix sum
vector<int> prefix(n + 1, 0);
for (int i = 0; i < n; i++) {
    prefix[i + 1] = prefix[i] + v[i];
}

// Range sum query [l, r]
int rangeSum = prefix[r + 1] - prefix[l];

// 2D prefix sum
vector<vector<int>> prefix(n + 1, vector<int>(m + 1, 0));
for (int i = 1; i <= n; i++) {
    for (int j = 1; j <= m; j++) {
        prefix[i][j] = grid[i-1][j-1] 
                     + prefix[i-1][j] 
                     + prefix[i][j-1] 
                     - prefix[i-1][j-1];
    }
}

// 2D range sum query [r1,c1] to [r2,c2]
int sum = prefix[r2+1][c2+1] 
        - prefix[r1][c2+1] 
        - prefix[r2+1][c1] 
        + prefix[r1][c1];
```

### Difference Array

```cpp
// Range update: add val to [l, r]
vector<int> diff(n + 1, 0);

void rangeUpdate(int l, int r, int val) {
    diff[l] += val;
    diff[r + 1] -= val;
}

// Apply all updates
for (int i = 0; i < n; i++) {
    diff[i + 1] += diff[i];
    v[i] += diff[i];
}
```

### Frequency Counting

```cpp
// Using map
map<int, int> freq;
for (int x : v) {
    freq[x]++;
}

// Using unordered_map (faster)
unordered_map<int, int> freq;
for (int x : v) {
    freq[x]++;
}

// Using array (if range is small)
int freq[MAX_VAL] = {0};
for (int x : v) {
    freq[x]++;
}

// Find most frequent element
int maxFreq = 0, mostFrequent;
for (auto& [val, cnt] : freq) {
    if (cnt > maxFreq) {
        maxFreq = cnt;
        mostFrequent = val;
    }
}
```

### Coordinate Compression

```cpp
// Compress large values to small indices
vector<int> v = {1000000, 5, 1000000, 42, 5};
vector<int> sorted = v;
sort(sorted.begin(), sorted.end());
sorted.erase(unique(sorted.begin(), sorted.end()), sorted.end());

map<int, int> compress;
for (int i = 0; i < sorted.size(); i++) {
    compress[sorted[i]] = i;
}

// Use compressed values
for (int& x : v) {
    x = compress[x];
}
// v = {1, 0, 1, 2, 0}
```

---

## Advanced Data Structures

### Policy-Based Data Structures (PBDS)

```cpp
#include <ext/pb_ds/assoc_container.hpp>
#include <ext/pb_ds/tree_policy.hpp>
using namespace __gnu_pbds;

// Ordered set (supports order statistics)
template<typename T>
using ordered_set = tree<T, null_type, less<T>, rb_tree_tag,
                        tree_order_statistics_node_update>;

ordered_set<int> os;

os.insert(5);
os.insert(2);
os.insert(8);
os.insert(1);

// Find by order (0-indexed)
cout << *os.find_by_order(2) << '\n';  // 3rd smallest = 5

// Order of key (number of elements < x)
cout << os.order_of_key(5) << '\n';    // 2 elements < 5

// Erase
os.erase(5);

// Lower/upper bound
auto it = os.lower_bound(3);

// Ordered multiset
template<typename T>
using ordered_multiset = tree<T, null_type, less_equal<T>, rb_tree_tag,
                             tree_order_statistics_node_update>;
```

### Segment Tree (Using Array)

```cpp
class SegmentTree {
    vector<int> tree;
    int n;
    
    void build(vector<int>& arr, int node, int start, int end) {
        if (start == end) {
            tree[node] = arr[start];
        } else {
            int mid = (start + end) / 2;
            build(arr, 2*node, start, mid);
            build(arr, 2*node+1, mid+1, end);
            tree[node] = tree[2*node] + tree[2*node+1];
        }
    }
    
    void update(int node, int start, int end, int idx, int val) {
        if (start == end) {
            tree[node] = val;
        } else {
            int mid = (start + end) / 2;
            if (idx <= mid) {
                update(2*node, start, mid, idx, val);
            } else {
                update(2*node+1, mid+1, end, idx, val);
            }
            tree[node] = tree[2*node] + tree[2*node+1];
        }
    }
    
    int query(int node, int start, int end, int l, int r) {
        if (r < start || end < l) return 0;
        if (l <= start && end <= r) return tree[node];
        int mid = (start + end) / 2;
        return query(2*node, start, mid, l, r) +
               query(2*node+1, mid+1, end, l, r);
    }
    
public:
    SegmentTree(vector<int>& arr) {
        n = arr.size();
        tree.resize(4 * n);
        build(arr, 1, 0, n-1);
    }
    
    void update(int idx, int val) {
        update(1, 0, n-1, idx, val);
    }
    
    int query(int l, int r) {
        return query(1, 0, n-1, l, r);
    }
};
```

### Fenwick Tree (Binary Indexed Tree)

```cpp
class FenwickTree {
    vector<int> tree;
    int n;
    
public:
    FenwickTree(int n) : n(n), tree(n + 1, 0) {}
    
    // Add val to index i
    void update(int i, int val) {
        for (++i; i <= n; i += i & -i) {
            tree[i] += val;
        }
    }
    
    // Sum of [0, i]
    int query(int i) {
        int sum = 0;
        for (++i; i > 0; i -= i & -i) {
            sum += tree[i];
        }
        return sum;
    }
    
    // Sum of [l, r]
    int query(int l, int r) {
        return query(r) - (l > 0 ? query(l - 1) : 0);
    }
};
```

### Disjoint Set Union (DSU / Union-Find)

```cpp
class DSU {
    vector<int> parent, rank;
    
public:
    DSU(int n) : parent(n), rank(n, 0) {
        iota(parent.begin(), parent.end(), 0);
    }
    
    int find(int x) {
        if (parent[x] != x) {
            parent[x] = find(parent[x]);  // Path compression
        }
        return parent[x];
    }
    
    bool unite(int x, int y) {
        int px = find(x), py = find(y);
        if (px == py) return false;
        
        // Union by rank
        if (rank[px] < rank[py]) swap(px, py);
        parent[py] = px;
        if (rank[px] == rank[py]) rank[px]++;
        
        return true;
    }
    
    bool connected(int x, int y) {
        return find(x) == find(y);
    }
};
```

### Trie (Prefix Tree)

```cpp
struct TrieNode {
    map<char, TrieNode*> children;
    bool isEnd = false;
};

class Trie {
    TrieNode* root;
    
public:
    Trie() {
        root = new TrieNode();
    }
    
    void insert(string word) {
        TrieNode* node = root;
        for (char c : word) {
            if (!node->children[c]) {
                node->children[c] = new TrieNode();
            }
            node = node->children[c];
        }
        node->isEnd = true;
    }
    
    bool search(string word) {
        TrieNode* node = root;
        for (char c : word) {
            if (!node->children[c]) return false;
            node = node->children[c];
        }
        return node->isEnd;
    }
    
    bool startsWith(string prefix) {
        TrieNode* node = root;
        for (char c : prefix) {
            if (!node->children[c]) return false;
            node = node->children[c];
        }
        return true;
    }
};
```

---

## Optimization Tricks

### Bit Manipulation

```cpp
// Check if power of 2
bool isPowerOf2 = (n & (n - 1)) == 0;

// Get i-th bit
int bit = (n >> i) & 1;

// Set i-th bit
n |= (1 << i);

// Clear i-th bit
n &= ~(1 << i);

// Toggle i-th bit
n ^= (1 << i);

// Count set bits
int bits = __builtin_popcount(n);      // int
int bits = __builtin_popcountll(n);    // long long

// Leading zeros
int lz = __builtin_clz(n);             // int
int lz = __builtin_clzll(n);           // long long

// Trailing zeros
int tz = __builtin_ctz(n);             // int
int tz = __builtin_ctzll(n);           // long long

// Parity (1 if odd number of 1s)
int parity = __builtin_parity(n);

// Iterate through all subsets of mask
for (int sub = mask; sub > 0; sub = (sub - 1) & mask) {
    // Process subset
}

// Iterate through all masks with k bits set
for (int mask = (1 << k) - 1; mask < (1 << n); ) {
    // Process mask
    int c = mask & -mask;
    int r = mask + c;
    mask = (((r ^ mask) >> 2) / c) | r;
}
```

### Math Utilities

```cpp
// GCD and LCM
int g = __gcd(a, b);
long long l = (long long)a * b / __gcd(a, b);

// Power with modulo
long long power(long long a, long long b, long long mod) {
    long long res = 1;
    a %= mod;
    while (b > 0) {
        if (b & 1) res = res * a % mod;
        a = a * a % mod;
        b >>= 1;
    }
    return res;
}

// Modular inverse (when mod is prime)
long long modInv(long long a, long long mod) {
    return power(a, mod - 2, mod);
}

// Sieve of Eratosthenes
vector<bool> sieve(int n) {
    vector<bool> isPrime(n + 1, true);
    isPrime[0] = isPrime[1] = false;
    for (int i = 2; i * i <= n; i++) {
        if (isPrime[i]) {
            for (int j = i * i; j <= n; j += i) {
                isPrime[j] = false;
            }
        }
    }
    return isPrime;
}

// Prime factorization
vector<pair<int,int>> factorize(int n) {
    vector<pair<int,int>> factors;
    for (int i = 2; i * i <= n; i++) {
        int cnt = 0;
        while (n % i == 0) {
            cnt++;
            n /= i;
        }
        if (cnt > 0) factors.push_back({i, cnt});
    }
    if (n > 1) factors.push_back({n, 1});
    return factors;
}
```

### String Algorithms

```cpp
// KMP pattern matching
vector<int> computeLPS(string pattern) {
    int m = pattern.length();
    vector<int> lps(m, 0);
    int len = 0, i = 1;
    
    while (i < m) {
        if (pattern[i] == pattern[len]) {
            lps[i++] = ++len;
        } else {
            if (len != 0) {
                len = lps[len - 1];
            } else {
                lps[i++] = 0;
            }
        }
    }
    return lps;
}

vector<int> KMP(string text, string pattern) {
    vector<int> lps = computeLPS(pattern);
    vector<int> matches;
    int n = text.length(), m = pattern.length();
    int i = 0, j = 0;
    
    while (i < n) {
        if (text[i] == pattern[j]) {
            i++; j++;
        }
        if (j == m) {
            matches.push_back(i - j);
            j = lps[j - 1];
        } else if (i < n && text[i] != pattern[j]) {
            if (j != 0) {
                j = lps[j - 1];
            } else {
                i++;
            }
        }
    }
    return matches;
}

// Z-algorithm
vector<int> zAlgorithm(string s) {
    int n = s.length();
    vector<int> z(n);
    int l = 0, r = 0;
    
    for (int i = 1; i < n; i++) {
        if (i > r) {
            l = r = i;
            while (r < n && s[r - l] == s[r]) r++;
            z[i] = r - l;
            r--;
        } else {
            int k = i - l;
            if (z[k] < r - i + 1) {
                z[i] = z[k];
            } else {
                l = i;
                while (r < n && s[r - l] == s[r]) r++;
                z[i] = r - l;
                r--;
            }
        }
    }
    return z;
}
```

---

## Common Pitfalls and Solutions

### 1. Integer Overflow

```cpp
// Problem
int a = 1000000, b = 1000000;
int product = a * b;  // Overflow!

// Solution
long long product = (long long)a * b;
```

### 2. Division by Zero

```cpp
// Always check
if (b != 0) {
    int result = a / b;
}
```

### 3. Array Index Out of Bounds

```cpp
// Use .at() for bounds checking during development
try {
    int val = v.at(i);
} catch (out_of_range& e) {
    cerr << "Index out of bounds\n";
}

// Or check manually
if (i >= 0 && i < v.size()) {
    int val = v[i];
}
```

### 4. Comparing Signed and Unsigned

```cpp
// Problem
for (int i = 0; i < v.size() - 1; i++) { }  // Warning if v.size() == 0

// Solution
for (int i = 0; i < (int)v.size() - 1; i++) { }
// Or
for (size_t i = 0; i + 1 < v.size(); i++) { }
```

### 5. Modifying Container While Iterating

```cpp
// Problem
for (auto it = v.begin(); it != v.end(); it++) {
    if (*it % 2 == 0) {
        v.erase(it);  // Iterator invalidated!
    }
}

// Solution
for (auto it = v.begin(); it != v.end(); ) {
    if (*it % 2 == 0) {
        it = v.erase(it);  // erase returns next valid iterator
    } else {
        ++it;
    }
}

// Or use remove-erase idiom
v.erase(remove_if(v.begin(), v.end(), [](int x) {
    return x % 2 == 0;
}), v.end());
```

### 6. Floating Point Comparison

```cpp
// Problem
if (a == b) { }  // May fail due to precision

// Solution
const double EPS = 1e-9;
if (abs(a - b) < EPS) { }
```

### 7. Stack Overflow with Large Arrays

```cpp
// Problem
int main() {
    int arr[10000000];  // Stack overflow!
}

// Solution 1: Use vector
int main() {
    vector<int> arr(10000000);
}

// Solution 2: Global array
int arr[10000000];
int main() {
    // ...
}

// Solution 3: Dynamic allocation
int main() {
    int* arr = new int[10000000];
    // ... use arr ...
    delete[] arr;
}
```

---

## Template Library for Contests

### Complete Template

```cpp
#include <bits/stdc++.h>
using namespace std;

// Type aliases
using ll = long long;
using ull = unsigned long long;
using ld = long double;
using pii = pair<int, int>;
using pll = pair<ll, ll>;
using vi = vector<int>;
using vll = vector<ll>;
using vvi = vector<vi>;
using vvll = vector<vll>;

// Macros
#define all(x) (x).begin(), (x).end()
#define rall(x) (x).rbegin(), (x).rend()
#define pb push_back
#define eb emplace_back
#define mp make_pair
#define fi first
#define se second
#define sz(x) (int)(x).size()
#define rep(i, a, b) for (int i = (a); i < (b); ++i)
#define per(i, a, b) for (int i = (b) - 1; i >= (a); --i)
#define trav(a, x) for (auto& a : x)

// Constants
const int MOD = 1e9 + 7;
const int INF = 1e9;
const ll LINF = 1e18;
const ld PI = acos(-1.0);
const ld EPS = 1e-9;

// Directions (4-directional)
const int dx4[] = {-1, 0, 1, 0};
const int dy4[] = {0, 1, 0, -1};

// Directions (8-directional)
const int dx8[] = {-1, -1, -1, 0, 0, 1, 1, 1};
const int dy8[] = {-1, 0, 1, -1, 1, -1, 0, 1};

// Utility functions
template<typename T>
void chmin(T& a, T b) { a = min(a, b); }

template<typename T>
void chmax(T& a, T b) { a = max(a, b); }

template<typename T>
T gcd(T a, T b) { return b ? gcd(b, a % b) : a; }

template<typename T>
T lcm(T a, T b) { return a / gcd(a, b) * b; }

template<typename T>
T power(T a, T b, T mod) {
    T res = 1;
    a %= mod;
    while (b > 0) {
        if (b & 1) res = res * a % mod;
        a = a * a % mod;
        b >>= 1;
    }
    return res;
}

// Debug
#ifdef LOCAL
#define debug(x) cerr << #x << " = " << (x) << endl
#define debug2(x, y) cerr << #x << " = " << (x) << ", " << #y << " = " << (y) << endl
#else
#define debug(x)
#define debug2(x, y)
#endif

// Fast I/O
void fastIO() {
    ios_base::sync_with_stdio(false);
    cin.tie(nullptr);
    cout.tie(nullptr);
}

// Main function
void solve() {
    // Your solution here
}

int main() {
    fastIO();
    
    int t = 1;
    // cin >> t;  // Uncomment for multiple test cases
    
    while (t--) {
        solve();
    }
    
    return 0;
}
```

### Modular Arithmetic Template

```cpp
template<int MOD>
struct ModInt {
    int val;
    
    ModInt(ll v = 0) : val(v % MOD) {
        if (val < 0) val += MOD;
    }
    
    ModInt& operator+=(const ModInt& other) {
        val += other.val;
        if (val >= MOD) val -= MOD;
        return *this;
    }
    
    ModInt& operator-=(const ModInt& other) {
        val -= other.val;
        if (val < 0) val += MOD;
        return *this;
    }
    
    ModInt& operator*=(const ModInt& other) {
        val = (1LL * val * other.val) % MOD;
        return *this;
    }
    
    ModInt pow(ll p) const {
        ModInt res = 1, a = *this;
        while (p > 0) {
            if (p & 1) res *= a;
            a *= a;
            p >>= 1;
        }
        return res;
    }
    
    ModInt inv() const {
        return pow(MOD - 2);
    }
    
    ModInt& operator/=(const ModInt& other) {
        return *this *= other.inv();
    }
    
    friend ModInt operator+(ModInt a, const ModInt& b) { return a += b; }
    friend ModInt operator-(ModInt a, const ModInt& b) { return a -= b; }
    friend ModInt operator*(ModInt a, const ModInt& b) { return a *= b; }
    friend ModInt operator/(ModInt a, const ModInt& b) { return a /= b; }
    
    friend ostream& operator<<(ostream& os, const ModInt& m) {
        return os << m.val;
    }
};

using mint = ModInt<MOD>;
```

---

## Practice Problems by Topic

### Beginner
- **Sorting**: Codeforces 71A, 158A
- **Binary Search**: Codeforces 279B, 165B
- **Two Pointers**: Codeforces 6C, 279B
- **Greedy**: Codeforces 230A, 339B

### Intermediate
- **DP**: Codeforces 189A, 466C
- **Graphs**: Codeforces 580C, 115A
- **Data Structures**: Codeforces 540C, 459D
- **Number Theory**: Codeforces 230B, 385C

### Advanced
- **Segment Tree**: Codeforces 380C, 459D
- **DSU**: Codeforces 25D, 277A
- **String Algorithms**: Codeforces 126B, 432D
- **Game Theory**: Codeforces 337A, 268B

---

**Happy Competitive Programming! Practice makes perfect!** 🚀

