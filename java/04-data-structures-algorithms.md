# Data Structures and Algorithms in Java

## Table of Contents
1. [Time/Space Complexity Analysis](#complexity-analysis)
2. [Arrays and Strings](#arrays-and-strings)
3. [Linked Lists](#linked-lists)
4. [Stacks and Queues](#stacks-and-queues)
5. [Trees and Graphs](#trees-and-graphs)
6. [Heaps and Priority Queues](#heaps)
7. [Hashing Techniques](#hashing)
8. [Sorting Algorithms](#sorting)
9. [Searching Algorithms](#searching)
10. [Dynamic Programming](#dynamic-programming)
11. [Graph Algorithms](#graph-algorithms)
12. [Competitive Programming Patterns](#competitive-patterns)

---

## Time/Space Complexity Analysis

### Big-O Complexity Chart

```
Time Complexity Growth Rates:

O(1)       ─────────────────────────────────────────  Constant
O(log n)   ─────────────────────                      Logarithmic
O(n)       ─────────────────────────────              Linear
O(n log n) ─────────────────────────────────────      Linearithmic
O(n²)      ─────────────────────────────────────────  Quadratic
O(2^n)     ─────────────────────────────────────────  Exponential
O(n!)      ─────────────────────────────────────────  Factorial

Common Operations:
┌───────────────────┬─────────┬──────────┬────────────┐
│ Data Structure    │ Access  │ Search   │ Insert/Del │
├───────────────────┼─────────┼──────────┼────────────┤
│ Array             │ O(1)    │ O(n)     │ O(n)       │
│ Sorted Array      │ O(1)    │ O(log n) │ O(n)       │
│ Linked List       │ O(n)    │ O(n)     │ O(1)*      │
│ Hash Table        │ N/A     │ O(1)*    │ O(1)*      │
│ BST (balanced)    │ O(log n)│ O(log n) │ O(log n)   │
│ Heap              │ O(1)†   │ O(n)     │ O(log n)   │
└───────────────────┴─────────┴──────────┴────────────┘
* Amortized  † For min/max only
```

---

## Arrays and Strings

### Two Pointer Technique

```java
// Pattern: Two pointers moving towards each other
public boolean isPalindrome(String s) {
    int left = 0, right = s.length() - 1;
    while (left < right) {
        while (left < right && !Character.isLetterOrDigit(s.charAt(left))) left++;
        while (left < right && !Character.isLetterOrDigit(s.charAt(right))) right--;
        if (Character.toLowerCase(s.charAt(left)) != 
            Character.toLowerCase(s.charAt(right))) {
            return false;
        }
        left++;
        right--;
    }
    return true;
}

// Pattern: Two Sum with sorted array
public int[] twoSumSorted(int[] nums, int target) {
    int left = 0, right = nums.length - 1;
    while (left < right) {
        int sum = nums[left] + nums[right];
        if (sum == target) return new int[]{left, right};
        else if (sum < target) left++;
        else right--;
    }
    return new int[]{-1, -1};
}
```

### Sliding Window Pattern

```java
// Fixed-size window: Maximum sum of k consecutive elements
public int maxSumSubarray(int[] arr, int k) {
    int windowSum = 0, maxSum = Integer.MIN_VALUE;
    
    for (int i = 0; i < arr.length; i++) {
        windowSum += arr[i];
        
        if (i >= k - 1) {
            maxSum = Math.max(maxSum, windowSum);
            windowSum -= arr[i - k + 1];  // Remove leftmost element
        }
    }
    return maxSum;
}

// Variable-size window: Longest substring without repeating characters
public int lengthOfLongestSubstring(String s) {
    Map<Character, Integer> lastSeen = new HashMap<>();
    int maxLen = 0, start = 0;
    
    for (int end = 0; end < s.length(); end++) {
        char c = s.charAt(end);
        if (lastSeen.containsKey(c) && lastSeen.get(c) >= start) {
            start = lastSeen.get(c) + 1;  // Shrink window
        }
        lastSeen.put(c, end);
        maxLen = Math.max(maxLen, end - start + 1);
    }
    return maxLen;
}

// Minimum window substring (Classic sliding window)
public String minWindow(String s, String t) {
    if (t.isEmpty()) return "";
    
    Map<Character, Integer> need = new HashMap<>();
    Map<Character, Integer> window = new HashMap<>();
    for (char c : t.toCharArray()) need.merge(c, 1, Integer::sum);
    
    int left = 0, right = 0;
    int valid = 0;
    int start = 0, minLen = Integer.MAX_VALUE;
    
    while (right < s.length()) {
        char c = s.charAt(right++);
        if (need.containsKey(c)) {
            window.merge(c, 1, Integer::sum);
            if (window.get(c).equals(need.get(c))) valid++;
        }
        
        while (valid == need.size()) {
            if (right - left < minLen) {
                start = left;
                minLen = right - left;
            }
            char d = s.charAt(left++);
            if (need.containsKey(d)) {
                if (window.get(d).equals(need.get(d))) valid--;
                window.merge(d, -1, Integer::sum);
            }
        }
    }
    return minLen == Integer.MAX_VALUE ? "" : s.substring(start, start + minLen);
}
```

### Prefix Sum Pattern

```java
// Subarray sum equals K
public int subarraySum(int[] nums, int k) {
    Map<Integer, Integer> prefixCount = new HashMap<>();
    prefixCount.put(0, 1);  // Empty prefix
    
    int sum = 0, count = 0;
    for (int num : nums) {
        sum += num;
        // If (sum - k) exists, there's a subarray with sum k
        count += prefixCount.getOrDefault(sum - k, 0);
        prefixCount.merge(sum, 1, Integer::sum);
    }
    return count;
}

// 2D Prefix Sum
public class NumMatrix {
    private int[][] prefix;

    public NumMatrix(int[][] matrix) {
        int m = matrix.length, n = matrix[0].length;
        prefix = new int[m + 1][n + 1];

        for (int i = 1; i <= m; i++) {
            for (int j = 1; j <= n; j++) {
                prefix[i][j] = matrix[i-1][j-1]
                             + prefix[i-1][j]
                             + prefix[i][j-1]
                             - prefix[i-1][j-1];
            }
        }
    }

    public int sumRegion(int r1, int c1, int r2, int c2) {
        return prefix[r2+1][c2+1] - prefix[r1][c2+1]
             - prefix[r2+1][c1] + prefix[r1][c1];
    }
}
```

---

## Linked Lists

### Common Techniques

```java
// Fast and Slow Pointer (Floyd's Algorithm)
// Detect cycle, find middle, find nth from end

public class LinkedListTechniques {

    // Find middle of linked list
    public ListNode findMiddle(ListNode head) {
        ListNode slow = head, fast = head;
        while (fast != null && fast.next != null) {
            slow = slow.next;
            fast = fast.next.next;
        }
        return slow;  // Middle (or second middle if even length)
    }

    // Detect cycle
    public boolean hasCycle(ListNode head) {
        ListNode slow = head, fast = head;
        while (fast != null && fast.next != null) {
            slow = slow.next;
            fast = fast.next.next;
            if (slow == fast) return true;
        }
        return false;
    }

    // Find cycle start (Floyd's algorithm part 2)
    public ListNode detectCycleStart(ListNode head) {
        ListNode slow = head, fast = head;
        while (fast != null && fast.next != null) {
            slow = slow.next;
            fast = fast.next.next;
            if (slow == fast) {
                // Reset one pointer to head
                slow = head;
                while (slow != fast) {
                    slow = slow.next;
                    fast = fast.next;
                }
                return slow;  // Cycle start
            }
        }
        return null;
    }

    // Reverse linked list (iterative)
    public ListNode reverse(ListNode head) {
        ListNode prev = null, curr = head;
        while (curr != null) {
            ListNode next = curr.next;
            curr.next = prev;
            prev = curr;
            curr = next;
        }
        return prev;
    }

    // Reverse in groups of k
    public ListNode reverseKGroup(ListNode head, int k) {
        ListNode dummy = new ListNode(0);
        dummy.next = head;
        ListNode prevGroup = dummy;

        while (true) {
            ListNode kth = getKth(prevGroup, k);
            if (kth == null) break;

            ListNode nextGroup = kth.next;
            ListNode prev = nextGroup, curr = prevGroup.next;

            while (curr != nextGroup) {
                ListNode next = curr.next;
                curr.next = prev;
                prev = curr;
                curr = next;
            }

            ListNode temp = prevGroup.next;
            prevGroup.next = kth;
            prevGroup = temp;
        }
        return dummy.next;
    }

    private ListNode getKth(ListNode node, int k) {
        while (node != null && k > 0) {
            node = node.next;
            k--;
        }
        return node;
    }
}
```

---

## Trees and Graphs

### Tree Traversals

```java
public class TreeTraversals {

    // Inorder (Left, Root, Right) - BST gives sorted order
    public List<Integer> inorder(TreeNode root) {
        List<Integer> result = new ArrayList<>();
        inorderHelper(root, result);
        return result;
    }

    private void inorderHelper(TreeNode node, List<Integer> result) {
        if (node == null) return;
        inorderHelper(node.left, result);
        result.add(node.val);
        inorderHelper(node.right, result);
    }

    // Iterative Inorder with Stack
    public List<Integer> inorderIterative(TreeNode root) {
        List<Integer> result = new ArrayList<>();
        Deque<TreeNode> stack = new ArrayDeque<>();
        TreeNode curr = root;

        while (curr != null || !stack.isEmpty()) {
            while (curr != null) {
                stack.push(curr);
                curr = curr.left;
            }
            curr = stack.pop();
            result.add(curr.val);
            curr = curr.right;
        }
        return result;
    }

    // Level Order (BFS)
    public List<List<Integer>> levelOrder(TreeNode root) {
        List<List<Integer>> result = new ArrayList<>();
        if (root == null) return result;

        Queue<TreeNode> queue = new LinkedList<>();
        queue.offer(root);

        while (!queue.isEmpty()) {
            int size = queue.size();
            List<Integer> level = new ArrayList<>();

            for (int i = 0; i < size; i++) {
                TreeNode node = queue.poll();
                level.add(node.val);
                if (node.left != null) queue.offer(node.left);
                if (node.right != null) queue.offer(node.right);
            }
            result.add(level);
        }
        return result;
    }

    // Morris Traversal (O(1) space inorder)
    public List<Integer> morrisInorder(TreeNode root) {
        List<Integer> result = new ArrayList<>();
        TreeNode curr = root;

        while (curr != null) {
            if (curr.left == null) {
                result.add(curr.val);
                curr = curr.right;
            } else {
                // Find inorder predecessor
                TreeNode pred = curr.left;
                while (pred.right != null && pred.right != curr) {
                    pred = pred.right;
                }

                if (pred.right == null) {
                    // Create thread
                    pred.right = curr;
                    curr = curr.left;
                } else {
                    // Remove thread
                    pred.right = null;
                    result.add(curr.val);
                    curr = curr.right;
                }
            }
        }
        return result;
    }
}
```

### Binary Search Tree Operations

```java
public class BSTOperations {

    // Search O(log n) average, O(n) worst
    public TreeNode search(TreeNode root, int target) {
        if (root == null || root.val == target) return root;
        return target < root.val
            ? search(root.left, target)
            : search(root.right, target);
    }

    // Insert
    public TreeNode insert(TreeNode root, int val) {
        if (root == null) return new TreeNode(val);
        if (val < root.val) root.left = insert(root.left, val);
        else root.right = insert(root.right, val);
        return root;
    }

    // Delete
    public TreeNode delete(TreeNode root, int key) {
        if (root == null) return null;

        if (key < root.val) {
            root.left = delete(root.left, key);
        } else if (key > root.val) {
            root.right = delete(root.right, key);
        } else {
            // Node to delete found
            if (root.left == null) return root.right;
            if (root.right == null) return root.left;

            // Node has two children
            TreeNode successor = findMin(root.right);
            root.val = successor.val;
            root.right = delete(root.right, successor.val);
        }
        return root;
    }

    private TreeNode findMin(TreeNode node) {
        while (node.left != null) node = node.left;
        return node;
    }

    // Validate BST
    public boolean isValidBST(TreeNode root) {
        return validate(root, Long.MIN_VALUE, Long.MAX_VALUE);
    }

    private boolean validate(TreeNode node, long min, long max) {
        if (node == null) return true;
        if (node.val <= min || node.val >= max) return false;
        return validate(node.left, min, node.val) &&
               validate(node.right, node.val, max);
    }

    // Lowest Common Ancestor in BST
    public TreeNode lcaBST(TreeNode root, TreeNode p, TreeNode q) {
        if (p.val < root.val && q.val < root.val)
            return lcaBST(root.left, p, q);
        if (p.val > root.val && q.val > root.val)
            return lcaBST(root.right, p, q);
        return root;
    }

    // LCA in Binary Tree (not BST)
    public TreeNode lcaBinaryTree(TreeNode root, TreeNode p, TreeNode q) {
        if (root == null || root == p || root == q) return root;

        TreeNode left = lcaBinaryTree(root.left, p, q);
        TreeNode right = lcaBinaryTree(root.right, p, q);

        if (left != null && right != null) return root;
        return left != null ? left : right;
    }
}
```

---

## Graph Algorithms

### Graph Representations

```java
public class GraphRepresentations {

    // Adjacency List (most common, space-efficient for sparse graphs)
    List<List<Integer>> adjList;

    public void buildAdjList(int n, int[][] edges) {
        adjList = new ArrayList<>();
        for (int i = 0; i < n; i++) {
            adjList.add(new ArrayList<>());
        }
        for (int[] edge : edges) {
            adjList.get(edge[0]).add(edge[1]);
            adjList.get(edge[1]).add(edge[0]);  // For undirected
        }
    }

    // Adjacency Matrix (good for dense graphs, O(1) edge lookup)
    int[][] adjMatrix;

    public void buildAdjMatrix(int n, int[][] edges) {
        adjMatrix = new int[n][n];
        for (int[] edge : edges) {
            adjMatrix[edge[0]][edge[1]] = 1;
            adjMatrix[edge[1]][edge[0]] = 1;
        }
    }

    // Edge List (good for Kruskal's algorithm)
    List<int[]> edgeList;
}
```

### BFS and DFS

```java
public class GraphTraversal {

    // BFS - Level-by-level, shortest path in unweighted graph
    public List<Integer> bfs(List<List<Integer>> graph, int start) {
        List<Integer> result = new ArrayList<>();
        boolean[] visited = new boolean[graph.size()];
        Queue<Integer> queue = new LinkedList<>();

        queue.offer(start);
        visited[start] = true;

        while (!queue.isEmpty()) {
            int node = queue.poll();
            result.add(node);

            for (int neighbor : graph.get(node)) {
                if (!visited[neighbor]) {
                    visited[neighbor] = true;
                    queue.offer(neighbor);
                }
            }
        }
        return result;
    }

    // DFS - Go deep first
    public List<Integer> dfs(List<List<Integer>> graph, int start) {
        List<Integer> result = new ArrayList<>();
        boolean[] visited = new boolean[graph.size()];
        dfsHelper(graph, start, visited, result);
        return result;
    }

    private void dfsHelper(List<List<Integer>> graph, int node,
                           boolean[] visited, List<Integer> result) {
        visited[node] = true;
        result.add(node);

        for (int neighbor : graph.get(node)) {
            if (!visited[neighbor]) {
                dfsHelper(graph, neighbor, visited, result);
            }
        }
    }

    // Iterative DFS
    public List<Integer> dfsIterative(List<List<Integer>> graph, int start) {
        List<Integer> result = new ArrayList<>();
        boolean[] visited = new boolean[graph.size()];
        Deque<Integer> stack = new ArrayDeque<>();

        stack.push(start);

        while (!stack.isEmpty()) {
            int node = stack.pop();
            if (visited[node]) continue;

            visited[node] = true;
            result.add(node);

            // Add neighbors in reverse order for consistent ordering
            List<Integer> neighbors = graph.get(node);
            for (int i = neighbors.size() - 1; i >= 0; i--) {
                if (!visited[neighbors.get(i)]) {
                    stack.push(neighbors.get(i));
                }
            }
        }
        return result;
    }
}
```

### Dijkstra's Algorithm

```java
public class Dijkstra {

    // Single-source shortest path (non-negative weights)
    public int[] dijkstra(int[][] graph, int source) {
        int n = graph.length;
        int[] dist = new int[n];
        Arrays.fill(dist, Integer.MAX_VALUE);
        dist[source] = 0;

        // Min-heap: [distance, node]
        PriorityQueue<int[]> pq = new PriorityQueue<>((a, b) -> a[0] - b[0]);
        pq.offer(new int[]{0, source});

        while (!pq.isEmpty()) {
            int[] curr = pq.poll();
            int d = curr[0], u = curr[1];

            // Skip if we already found a shorter path
            if (d > dist[u]) continue;

            for (int v = 0; v < n; v++) {
                if (graph[u][v] > 0) {  // Edge exists
                    int newDist = dist[u] + graph[u][v];
                    if (newDist < dist[v]) {
                        dist[v] = newDist;
                        pq.offer(new int[]{newDist, v});
                    }
                }
            }
        }
        return dist;
    }
}
```

### Topological Sort

```java
public class TopologicalSort {

    // Kahn's Algorithm (BFS-based)
    public int[] topologicalSort(int n, int[][] edges) {
        List<List<Integer>> graph = new ArrayList<>();
        int[] inDegree = new int[n];

        for (int i = 0; i < n; i++) graph.add(new ArrayList<>());

        for (int[] edge : edges) {
            graph.get(edge[0]).add(edge[1]);
            inDegree[edge[1]]++;
        }

        Queue<Integer> queue = new LinkedList<>();
        for (int i = 0; i < n; i++) {
            if (inDegree[i] == 0) queue.offer(i);
        }

        int[] result = new int[n];
        int index = 0;

        while (!queue.isEmpty()) {
            int node = queue.poll();
            result[index++] = node;

            for (int neighbor : graph.get(node)) {
                if (--inDegree[neighbor] == 0) {
                    queue.offer(neighbor);
                }
            }
        }

        return index == n ? result : new int[0];  // Empty if cycle exists
    }

    // DFS-based Topological Sort
    public List<Integer> topologicalSortDFS(int n, int[][] edges) {
        List<List<Integer>> graph = new ArrayList<>();
        for (int i = 0; i < n; i++) graph.add(new ArrayList<>());

        for (int[] edge : edges) {
            graph.get(edge[0]).add(edge[1]);
        }

        int[] state = new int[n];  // 0: unvisited, 1: visiting, 2: visited
        List<Integer> result = new ArrayList<>();

        for (int i = 0; i < n; i++) {
            if (state[i] == 0) {
                if (!dfs(graph, i, state, result)) {
                    return Collections.emptyList();  // Cycle detected
                }
            }
        }

        Collections.reverse(result);
        return result;
    }

    private boolean dfs(List<List<Integer>> graph, int node,
                       int[] state, List<Integer> result) {
        state[node] = 1;  // Visiting

        for (int neighbor : graph.get(node)) {
            if (state[neighbor] == 1) return false;  // Cycle!
            if (state[neighbor] == 0) {
                if (!dfs(graph, neighbor, state, result)) return false;
            }
        }

        state[node] = 2;  // Visited
        result.add(node);
        return true;
    }
}
```

---

## Dynamic Programming

### DP Patterns

```java
public class DynamicProgramming {

    // Pattern 1: 0/1 Knapsack
    public int knapsack(int[] weights, int[] values, int capacity) {
        int n = weights.length;
        int[][] dp = new int[n + 1][capacity + 1];

        for (int i = 1; i <= n; i++) {
            for (int w = 1; w <= capacity; w++) {
                if (weights[i-1] <= w) {
                    dp[i][w] = Math.max(
                        dp[i-1][w],  // Don't take item
                        dp[i-1][w - weights[i-1]] + values[i-1]  // Take item
                    );
                } else {
                    dp[i][w] = dp[i-1][w];
                }
            }
        }
        return dp[n][capacity];
    }

    // Space-optimized 1D
    public int knapsackOptimized(int[] weights, int[] values, int capacity) {
        int[] dp = new int[capacity + 1];

        for (int i = 0; i < weights.length; i++) {
            // Traverse backwards to avoid using same item twice
            for (int w = capacity; w >= weights[i]; w--) {
                dp[w] = Math.max(dp[w], dp[w - weights[i]] + values[i]);
            }
        }
        return dp[capacity];
    }

    // Pattern 2: Unbounded Knapsack (items can be used multiple times)
    public int unboundedKnapsack(int[] weights, int[] values, int capacity) {
        int[] dp = new int[capacity + 1];

        for (int w = 1; w <= capacity; w++) {
            for (int i = 0; i < weights.length; i++) {
                if (weights[i] <= w) {
                    dp[w] = Math.max(dp[w], dp[w - weights[i]] + values[i]);
                }
            }
        }
        return dp[capacity];
    }

    // Pattern 3: Longest Common Subsequence
    public int longestCommonSubsequence(String text1, String text2) {
        int m = text1.length(), n = text2.length();
        int[][] dp = new int[m + 1][n + 1];

        for (int i = 1; i <= m; i++) {
            for (int j = 1; j <= n; j++) {
                if (text1.charAt(i-1) == text2.charAt(j-1)) {
                    dp[i][j] = dp[i-1][j-1] + 1;
                } else {
                    dp[i][j] = Math.max(dp[i-1][j], dp[i][j-1]);
                }
            }
        }
        return dp[m][n];
    }

    // Pattern 4: Longest Increasing Subsequence
    // O(n log n) using binary search
    public int lengthOfLIS(int[] nums) {
        List<Integer> tails = new ArrayList<>();

        for (int num : nums) {
            int pos = Collections.binarySearch(tails, num);
            if (pos < 0) pos = -(pos + 1);

            if (pos == tails.size()) {
                tails.add(num);
            } else {
                tails.set(pos, num);
            }
        }
        return tails.size();
    }

    // Pattern 5: Coin Change (minimum coins)
    public int coinChange(int[] coins, int amount) {
        int[] dp = new int[amount + 1];
        Arrays.fill(dp, amount + 1);  // Use invalid value instead of MAX_VALUE
        dp[0] = 0;

        for (int i = 1; i <= amount; i++) {
            for (int coin : coins) {
                if (coin <= i) {
                    dp[i] = Math.min(dp[i], dp[i - coin] + 1);
                }
            }
        }
        return dp[amount] > amount ? -1 : dp[amount];
    }

    // Pattern 6: Edit Distance
    public int minDistance(String word1, String word2) {
        int m = word1.length(), n = word2.length();
        int[][] dp = new int[m + 1][n + 1];

        // Base cases
        for (int i = 0; i <= m; i++) dp[i][0] = i;  // Delete all
        for (int j = 0; j <= n; j++) dp[0][j] = j;  // Insert all

        for (int i = 1; i <= m; i++) {
            for (int j = 1; j <= n; j++) {
                if (word1.charAt(i-1) == word2.charAt(j-1)) {
                    dp[i][j] = dp[i-1][j-1];  // No operation
                } else {
                    dp[i][j] = 1 + Math.min(
                        dp[i-1][j-1],  // Replace
                        Math.min(dp[i-1][j], dp[i][j-1])  // Delete, Insert
                    );
                }
            }
        }
        return dp[m][n];
    }
}
```

---

## Sorting Algorithms

### Comparison of Sorting Algorithms

```
┌───────────────┬────────────┬────────────┬────────────┬────────────┬──────────┐
│ Algorithm     │ Best       │ Average    │ Worst      │ Space      │ Stable   │
├───────────────┼────────────┼────────────┼────────────┼────────────┼──────────┤
│ Bubble Sort   │ O(n)       │ O(n²)      │ O(n²)      │ O(1)       │ Yes      │
│ Selection Sort│ O(n²)      │ O(n²)      │ O(n²)      │ O(1)       │ No       │
│ Insertion Sort│ O(n)       │ O(n²)      │ O(n²)      │ O(1)       │ Yes      │
│ Merge Sort    │ O(n log n) │ O(n log n) │ O(n log n) │ O(n)       │ Yes      │
│ Quick Sort    │ O(n log n) │ O(n log n) │ O(n²)      │ O(log n)   │ No       │
│ Heap Sort     │ O(n log n) │ O(n log n) │ O(n log n) │ O(1)       │ No       │
│ Counting Sort │ O(n + k)   │ O(n + k)   │ O(n + k)   │ O(k)       │ Yes      │
│ Radix Sort    │ O(nk)      │ O(nk)      │ O(nk)      │ O(n + k)   │ Yes      │
└───────────────┴────────────┴────────────┴────────────┴────────────┴──────────┘
```

### Quick Sort Implementation

```java
public class QuickSort {

    public void quickSort(int[] arr, int low, int high) {
        if (low < high) {
            int pi = partition(arr, low, high);
            quickSort(arr, low, pi - 1);
            quickSort(arr, pi + 1, high);
        }
    }

    private int partition(int[] arr, int low, int high) {
        // Random pivot to avoid worst case
        int randomIdx = low + (int)(Math.random() * (high - low + 1));
        swap(arr, randomIdx, high);

        int pivot = arr[high];
        int i = low - 1;

        for (int j = low; j < high; j++) {
            if (arr[j] < pivot) {
                i++;
                swap(arr, i, j);
            }
        }
        swap(arr, i + 1, high);
        return i + 1;
    }

    private void swap(int[] arr, int i, int j) {
        int temp = arr[i];
        arr[i] = arr[j];
        arr[j] = temp;
    }
}
```

### Merge Sort Implementation

```java
public class MergeSort {

    public void mergeSort(int[] arr, int left, int right) {
        if (left < right) {
            int mid = left + (right - left) / 2;
            mergeSort(arr, left, mid);
            mergeSort(arr, mid + 1, right);
            merge(arr, left, mid, right);
        }
    }

    private void merge(int[] arr, int left, int mid, int right) {
        int[] temp = new int[right - left + 1];
        int i = left, j = mid + 1, k = 0;

        while (i <= mid && j <= right) {
            if (arr[i] <= arr[j]) {
                temp[k++] = arr[i++];
            } else {
                temp[k++] = arr[j++];
            }
        }

        while (i <= mid) temp[k++] = arr[i++];
        while (j <= right) temp[k++] = arr[j++];

        System.arraycopy(temp, 0, arr, left, temp.length);
    }
}
```


