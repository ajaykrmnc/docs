# libstdc++ Complete Learning Guide

Welcome to the comprehensive guide for understanding libstdc++ (GNU C++ Standard Library)!

## 📚 Guide Structure

This guide contains **9 extensive documents** covering everything from libstdc++ internals to competitive programming, C++ templates, and performance optimization.

---

## 📖 Documents Overview

### 🔰 For Beginners

#### **08-templates-for-beginners.md** ⭐ START HERE!
**Perfect for:** Complete beginners to C++ templates
**Topics:**
- Why no semicolon after `template<typename T>`?
- What are templates? (Simple explanation)
- Understanding that T is NOT a variable!
- Step-by-step function templates
- Step-by-step class templates
- Common beginner mistakes
- Practice exercises with solutions

**Key Takeaway:** Templates let you write code once and use it with many types!

---

### ⚡ Performance Optimization

#### **09-cache-friendly-code.md** ⭐ NEW!
**Perfect for:** Writing high-performance code
**Topics:**
- What is cache and why it matters (10-100x speed difference!)
- How CPU cache works (L1, L2, L3, cache lines)
- Cache terminology explained simply
- Golden rules of cache-friendly code
- Data structure layout (SoA vs AoS)
- Array access patterns (row-major vs column-major)
- Loop optimization techniques
- Common cache killers and how to avoid them
- STL containers and cache performance
- Practical examples with benchmarks
- Measuring cache performance

**Key Takeaway:** Cache-friendly code can be 10-100x faster! Use vectors, access sequentially, keep data compact.

---

### 🎯 For Competitive Programmers

#### **06-competitive-programming-guide.md**
**Perfect for:** Competitive programming and coding contests  
**Topics:**
- Essential STL containers (vector, set, map, priority_queue)
- Fast I/O techniques
- Container selection guide
- Algorithm cheat sheet (sort, binary_search, etc.)
- Common patterns (two pointers, sliding window, prefix sum)
- Advanced data structures (segment tree, Fenwick tree, DSU)
- Optimization tricks
- Complete contest template library

**Key Takeaway:** Master STL for faster problem-solving!

---

### 🏗️ Understanding libstdc++ Internals

#### **01-introduction-and-overview.md**
**Perfect for:** Understanding what libstdc++ is  
**Topics:**
- What is libstdc++?
- Why read the source code?
- Architecture overview
- Directory structure
- Getting started with the codebase

#### **02-navigating-source-code.md**
**Perfect for:** Learning to read libstdc++ source  
**Topics:**
- Include hierarchy (3-layer system)
- Reading techniques
- Naming conventions (_M_, _S_, etc.)
- Following code flow
- Preprocessor macros
- Tools and techniques

#### **03-understanding-containers.md**
**Perfect for:** Deep dive into containers  
**Topics:**
- Vector, deque, list, array internals
- Map, set (red-black trees)
- Unordered_map (hash tables)
- Container adaptors (stack, queue, priority_queue)
- Memory management and allocators
- Iterator implementation

#### **04-algorithms-and-iterators.md**
**Perfect for:** Understanding STL algorithms  
**Topics:**
- Iterator categories and traits
- Algorithm implementation patterns
- Sorting algorithms (introsort)
- Searching algorithms
- Tag dispatch and SFINAE
- Parallel algorithms (C++17)

#### **05-advanced-topics.md**
**Perfect for:** Advanced C++ features  
**Topics:**
- Template metaprogramming
- Type traits
- Smart pointers (unique_ptr, shared_ptr)
- Threading and concurrency
- Move semantics and perfect forwarding
- Exception handling

---

### 🎓 Advanced Template Learning

#### **07-template-syntax-complete-guide.md**
**Perfect for:** After mastering basics, go deeper  
**Topics:**
- Advanced function templates
- Class template specialization
- Variadic templates
- Template template parameters
- SFINAE and enable_if
- C++20 Concepts
- CRTP and expression templates
- Template metaprogramming

**Note:** This is comprehensive but complex. Start with document 08 first!

---

## 🗺️ Learning Paths

### Path 1: Complete Beginner to Templates
```
08-templates-for-beginners.md
    ↓
Practice writing simple templates
    ↓
07-template-syntax-complete-guide.md (when ready)
```

### Path 2: Competitive Programming
```
08-templates-for-beginners.md (understand templates)
    ↓
06-competitive-programming-guide.md (master STL)
    ↓
Practice on Codeforces, LeetCode, etc.
```

### Path 3: Understanding libstdc++ Source Code
```
01-introduction-and-overview.md
    ↓
02-navigating-source-code.md
    ↓
03-understanding-containers.md
    ↓
04-algorithms-and-iterators.md
    ↓
05-advanced-topics.md
    ↓
07-template-syntax-complete-guide.md
```

### Path 4: Job Interview Preparation
```
08-templates-for-beginners.md
    ↓
06-competitive-programming-guide.md
    ↓
03-understanding-containers.md (complexity analysis)
    ↓
04-algorithms-and-iterators.md (algorithm complexity)
```

---

## 🎯 Quick Reference

### Common Questions Answered

**Q: Is T in `template<typename T>` a variable?**  
**A:** NO! T is a TYPE placeholder, not a variable. See document 08, section 3.

**Q: Why no semicolon after `template<typename T>`?**  
**A:** Because it's a modifier for the next declaration, not a complete statement. See document 08, section 1.

**Q: Which container should I use?**  
**A:** See document 06, "Container Selection Guide" with decision tree.

**Q: How does vector grow?**  
**A:** Typically doubles capacity. See document 03, "Vector Growth Strategy".

**Q: What's the difference between map and unordered_map?**  
**A:** map is sorted (O(log n)), unordered_map is hash-based (O(1) average). See document 06.

**Q: How to make input/output faster?**  
**A:** Use `ios_base::sync_with_stdio(false)` and `cin.tie(nullptr)`. See document 06, "Fast I/O".

---

## 📊 Document Statistics

| Document | Lines | Difficulty | Time to Read |
|----------|-------|------------|--------------|
| 01-introduction-and-overview.md | ~3,500 | Beginner | 1-2 hours |
| 02-navigating-source-code.md | ~2,800 | Intermediate | 1-2 hours |
| 03-understanding-containers.md | ~4,200 | Intermediate | 2-3 hours |
| 04-algorithms-and-iterators.md | ~3,900 | Intermediate | 2-3 hours |
| 05-advanced-topics.md | ~4,100 | Advanced | 2-3 hours |
| 06-competitive-programming-guide.md | ~6,500 | Beginner-Int | 2-3 hours |
| 07-template-syntax-complete-guide.md | ~7,600 | Advanced | 3-4 hours |
| 08-templates-for-beginners.md | ~4,000 | Beginner | 1-2 hours |
| 09-cache-friendly-code.md | ~5,500 | Intermediate | 2-3 hours |
| **TOTAL** | **~42,100** | | **17-25 hours** |

---

## 🚀 Getting Started

### If you're new to templates:
1. Start with **08-templates-for-beginners.md**
2. Practice writing simple templates
3. Move to **06-competitive-programming-guide.md** for practical usage

### If you want to understand libstdc++:
1. Read **01-introduction-and-overview.md**
2. Follow the "Understanding libstdc++ Internals" path above

### If you're preparing for contests:
1. Skim **08-templates-for-beginners.md** (if needed)
2. Focus on **06-competitive-programming-guide.md**
3. Practice, practice, practice!

### If you want to write fast code:
1. Read **09-cache-friendly-code.md**
2. Learn about cache, memory layout, and access patterns
3. Apply techniques to your hot code paths

---

## 💡 Key Concepts Summary

### Templates
- **T is a TYPE placeholder**, not a variable
- `template<typename T>` modifies the next declaration (no semicolon)
- Write code once, use with many types
- Compiler generates specific code for each type

### STL Containers
- **vector**: Dynamic array, O(1) random access
- **map**: Sorted key-value, O(log n) operations
- **unordered_map**: Hash table, O(1) average operations
- **set**: Sorted unique elements, O(log n) operations
- **priority_queue**: Heap, O(log n) insert, O(1) access min/max

### Algorithms
- **sort**: O(n log n) introsort (quicksort + heapsort + insertion sort)
- **binary_search**: O(log n) on sorted data
- **lower_bound/upper_bound**: O(log n) find position
- **accumulate**: O(n) sum/reduce

### Performance Tips
- Use `reserve()` for vector if size is known
- Use `unordered_map` for faster lookups (if order doesn't matter)
- Use `emplace_back()` instead of `push_back()` for efficiency
- Disable sync with stdio for faster I/O in contests
- **Cache optimization**: Use vectors (not lists), access sequentially, keep structs small
- **Memory layout**: Structure of Arrays (SoA) for better cache performance
- **Access patterns**: Row-major order for 2D arrays in C++

---

## 🔗 External Resources

### Official Documentation
- [libstdc++ Manual](https://gcc.gnu.org/onlinedocs/libstdc++/manual/)
- [cppreference.com](https://en.cppreference.com/)
- [C++ Standard Drafts](https://eel.is/c++draft/)

### Online Code Browsers
- [Woboq Code Browser](https://code.woboq.org/gcc/)
- [Bootlin Elixir](https://elixir.bootlin.com/gcc/)
- [GitHub Mirror](https://github.com/gcc-mirror/gcc)

### Practice Platforms
- [Codeforces](https://codeforces.com/)
- [LeetCode](https://leetcode.com/)
- [AtCoder](https://atcoder.jp/)
- [HackerRank](https://www.hackerrank.com/)

---

## 📝 Contributing

Found an error or want to improve something? These documents are meant to be living guides that grow and improve over time.

---

## 🎓 Final Words

**Learning C++ and libstdc++ is a journey, not a destination.**

- Start simple (document 08)
- Practice regularly
- Read source code when curious
- Don't try to learn everything at once
- Focus on understanding concepts, not memorizing syntax

**Happy Learning!** 🚀

---

## 📋 Quick Navigation

- [Templates for Beginners](08-templates-for-beginners.md) ⭐ START HERE
- [Cache-Friendly Code](09-cache-friendly-code.md) ⭐ NEW - Performance!
- [Competitive Programming Guide](06-competitive-programming-guide.md)
- [Introduction and Overview](01-introduction-and-overview.md)
- [Navigating Source Code](02-navigating-source-code.md)
- [Understanding Containers](03-understanding-containers.md)
- [Algorithms and Iterators](04-algorithms-and-iterators.md)
- [Advanced Topics](05-advanced-topics.md)
- [Template Syntax Complete Guide](07-template-syntax-complete-guide.md)

