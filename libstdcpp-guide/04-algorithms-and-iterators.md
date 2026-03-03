# Understanding libstdc++ Algorithms and Iterators

## Table of Contents
1. [Algorithm Overview](#algorithm-overview)
2. [Iterator Deep Dive](#iterator-deep-dive)
3. [Algorithm Implementation Patterns](#algorithm-implementation-patterns)
4. [Non-Modifying Algorithms](#non-modifying-algorithms)
5. [Modifying Algorithms](#modifying-algorithms)
6. [Sorting and Searching](#sorting-and-searching)
7. [Numeric Algorithms](#numeric-algorithms)
8. [Parallel Algorithms](#parallel-algorithms)

---

## Algorithm Overview

### Design Philosophy

STL algorithms follow these principles:

1. **Generic**: Work with any container through iterators
2. **Efficient**: Optimized for different iterator categories
3. **Composable**: Can be combined to solve complex problems
4. **Type-safe**: Compile-time type checking

### Algorithm Categories

```
Algorithms
├── Non-modifying
│   ├── find, find_if, find_if_not
│   ├── count, count_if
│   ├── all_of, any_of, none_of
│   ├── for_each
│   └── search, mismatch, equal
│
├── Modifying
│   ├── copy, copy_if, copy_n
│   ├── move, move_backward
│   ├── fill, fill_n, generate
│   ├── transform
│   ├── replace, replace_if
│   ├── remove, remove_if, unique
│   └── reverse, rotate
│
├── Sorting & Searching
│   ├── sort, stable_sort, partial_sort
│   ├── nth_element, partition
│   ├── binary_search, lower_bound, upper_bound
│   └── merge, inplace_merge
│
├── Set Operations
│   ├── set_union, set_intersection
│   ├── set_difference, set_symmetric_difference
│   └── includes
│
├── Heap Operations
│   ├── make_heap, push_heap, pop_heap
│   └── sort_heap
│
└── Numeric
    ├── accumulate, reduce
    ├── inner_product, transform_reduce
    ├── partial_sum, adjacent_difference
    └── iota
```

**Location:** `include/bits/stl_algo.h`, `include/bits/stl_algobase.h`

---

## Iterator Deep Dive

### Iterator Categories

```cpp
// Base iterator tags
struct input_iterator_tag { };
struct output_iterator_tag { };
struct forward_iterator_tag : public input_iterator_tag { };
struct bidirectional_iterator_tag : public forward_iterator_tag { };
struct random_access_iterator_tag : public bidirectional_iterator_tag { };
struct contiguous_iterator_tag : public random_access_iterator_tag { };  // C++20
```

**Hierarchy:**
```
input_iterator_tag
    ↓
forward_iterator_tag
    ↓
bidirectional_iterator_tag
    ↓
random_access_iterator_tag
    ↓
contiguous_iterator_tag
```

### Iterator Traits

```cpp
template<typename _Iterator>
struct iterator_traits
{
  typedef typename _Iterator::iterator_category iterator_category;
  typedef typename _Iterator::value_type        value_type;
  typedef typename _Iterator::difference_type   difference_type;
  typedef typename _Iterator::pointer           pointer;
  typedef typename _Iterator::reference         reference;
};

// Specialization for pointers
template<typename _Tp>
struct iterator_traits<_Tp*>
{
  typedef random_access_iterator_tag iterator_category;
  typedef _Tp                        value_type;
  typedef ptrdiff_t                  difference_type;
  typedef _Tp*                       pointer;
  typedef _Tp&                       reference;
};
```

### Iterator Operations

**Location:** `include/bits/stl_iterator_base_funcs.h`

#### distance - Calculate Distance Between Iterators

```cpp
// Input iterator version (linear time)
template<typename _InputIterator>
inline typename iterator_traits<_InputIterator>::difference_type
__distance(_InputIterator __first, _InputIterator __last,
           input_iterator_tag)
{
  typename iterator_traits<_InputIterator>::difference_type __n = 0;
  while (__first != __last)
  {
    ++__first;
    ++__n;
  }
  return __n;
}

// Random access iterator version (constant time)
template<typename _RandomAccessIterator>
inline typename iterator_traits<_RandomAccessIterator>::difference_type
__distance(_RandomAccessIterator __first, _RandomAccessIterator __last,
           random_access_iterator_tag)
{
  return __last - __first;  // O(1) subtraction
}

// Public interface (tag dispatch)
template<typename _InputIterator>
inline typename iterator_traits<_InputIterator>::difference_type
distance(_InputIterator __first, _InputIterator __last)
{
  return std::__distance(__first, __last,
                        std::__iterator_category(__first));
}
```

**Key technique:** Tag dispatch for optimization based on iterator category

#### advance - Move Iterator Forward/Backward

```cpp
// Input iterator version
template<typename _InputIterator, typename _Distance>
inline void
__advance(_InputIterator& __i, _Distance __n, input_iterator_tag)
{
  // Only forward movement
  while (__n--)
    ++__i;
}

// Bidirectional iterator version
template<typename _BidirectionalIterator, typename _Distance>
inline void
__advance(_BidirectionalIterator& __i, _Distance __n,
          bidirectional_iterator_tag)
{
  if (__n > 0)
    while (__n--) ++__i;
  else
    while (__n++) --__i;  // Can move backward
}

// Random access iterator version
template<typename _RandomAccessIterator, typename _Distance>
inline void
__advance(_RandomAccessIterator& __i, _Distance __n,
          random_access_iterator_tag)
{
  __i += __n;  // O(1) jump
}

// Public interface
template<typename _InputIterator, typename _Distance>
inline void
advance(_InputIterator& __i, _Distance __n)
{
  typename iterator_traits<_InputIterator>::difference_type __d = __n;
  std::__advance(__i, __d, std::__iterator_category(__i));
}
```

### Iterator Adaptors

#### reverse_iterator

**Location:** `include/bits/stl_iterator.h`

```cpp
template<typename _Iterator>
class reverse_iterator
{
protected:
  _Iterator current;  // The underlying iterator
  
public:
  typedef typename iterator_traits<_Iterator>::iterator_category
    iterator_category;
  typedef typename iterator_traits<_Iterator>::value_type
    value_type;
  typedef typename iterator_traits<_Iterator>::difference_type
    difference_type;
  typedef typename iterator_traits<_Iterator>::pointer
    pointer;
  typedef typename iterator_traits<_Iterator>::reference
    reference;
  
  // Key: dereference returns element before current
  reference operator*() const
  {
    _Iterator __tmp = current;
    return *--__tmp;
  }
  
  reverse_iterator& operator++()
  {
    --current;  // Reverse direction
    return *this;
  }
  
  reverse_iterator& operator--()
  {
    ++current;  // Reverse direction
    return *this;
  }
};
```

**Why `*--tmp`?**
```
Forward:  [a] [b] [c] [d] [e] [end]
                           ↑
                        current

Reverse:  [end] [e] [d] [c] [b] [a]
           ↑
        current (points to end)
        
*current would be invalid, so we use *--tmp to get [e]
```

#### back_insert_iterator

```cpp
template<typename _Container>
class back_insert_iterator
{
protected:
  _Container* container;
  
public:
  back_insert_iterator& operator=(const typename _Container::value_type& __value)
  {
    container->push_back(__value);
    return *this;
  }
  
  back_insert_iterator& operator*() { return *this; }
  back_insert_iterator& operator++() { return *this; }
  back_insert_iterator& operator++(int) { return *this; }
};

// Helper function
template<typename _Container>
inline back_insert_iterator<_Container>
back_inserter(_Container& __x)
{
  return back_insert_iterator<_Container>(__x);
}
```

**Usage:**
```cpp
std::vector<int> src = {1, 2, 3};
std::vector<int> dest;
std::copy(src.begin(), src.end(), std::back_inserter(dest));
// dest now contains {1, 2, 3}
```

---

## Algorithm Implementation Patterns

### Pattern 1: Tag Dispatch

Optimize based on iterator category:

```cpp
// Public interface
template<typename _InputIterator>
inline typename iterator_traits<_InputIterator>::difference_type
distance(_InputIterator __first, _InputIterator __last)
{
  return __distance(__first, __last, __iterator_category(__first));
}

// Implementation for input iterators (O(n))
template<typename _InputIterator>
inline typename iterator_traits<_InputIterator>::difference_type
__distance(_InputIterator __first, _InputIterator __last,
           input_iterator_tag)
{
  // Linear time implementation
}

// Implementation for random access iterators (O(1))
template<typename _RandomAccessIterator>
inline typename iterator_traits<_RandomAccessIterator>::difference_type
__distance(_RandomAccessIterator __first, _RandomAccessIterator __last,
           random_access_iterator_tag)
{
  return __last - __first;  // Constant time
}
```

### Pattern 2: SFINAE with enable_if

Enable/disable overloads based on type properties:

```cpp
// Only enabled for input iterators
template<typename _InputIterator,
         typename = _RequireInputIter<_InputIterator>>
void algorithm(_InputIterator __first, _InputIterator __last)
{
  // Implementation
}
```

### Pattern 3: Perfect Forwarding

Preserve value categories:

```cpp
template<typename _InputIterator, typename _Function>
_Function
for_each(_InputIterator __first, _InputIterator __last, _Function __f)
{
  for (; __first != __last; ++__first)
    __f(*__first);  // Forward to function
  return __f;
}
```

---

## Non-Modifying Algorithms

### find - Linear Search

**Location:** `include/bits/stl_algo.h`

```cpp
template<typename _InputIterator, typename _Tp>
inline _InputIterator
find(_InputIterator __first, _InputIterator __last, const _Tp& __val)
{
  return std::__find_if(__first, __last,
                       __gnu_cxx::__ops::__iter_equals_val(__val));
}

// Internal implementation
template<typename _InputIterator, typename _Predicate>
inline _InputIterator
__find_if(_InputIterator __first, _InputIterator __last,
          _Predicate __pred)
{
  return std::__find_if(__first, __last, __pred,
                       std::__iterator_category(__first));
}

// Optimized for random access iterators
template<typename _RandomAccessIterator, typename _Predicate>
_RandomAccessIterator
__find_if(_RandomAccessIterator __first, _RandomAccessIterator __last,
          _Predicate __pred, random_access_iterator_tag)
{
  typename iterator_traits<_RandomAccessIterator>::difference_type
    __trip_count = (__last - __first) >> 2;  // Divide by 4
  
  // Loop unrolling for better performance
  for (; __trip_count > 0; --__trip_count)
  {
    if (__pred(__first)) return __first;
    ++__first;
    
    if (__pred(__first)) return __first;
    ++__first;
    
    if (__pred(__first)) return __first;
    ++__first;
    
    if (__pred(__first)) return __first;
    ++__first;
  }
  
  // Handle remaining elements
  switch (__last - __first)
  {
    case 3:
      if (__pred(__first)) return __first;
      ++__first;
    case 2:
      if (__pred(__first)) return __first;
      ++__first;
    case 1:
      if (__pred(__first)) return __first;
      ++__first;
    case 0:
    default:
      return __last;
  }
}
```

**Optimization:** Loop unrolling reduces branch mispredictions

### count_if - Count Elements Satisfying Predicate

```cpp
template<typename _InputIterator, typename _Predicate>
typename iterator_traits<_InputIterator>::difference_type
count_if(_InputIterator __first, _InputIterator __last, _Predicate __pred)
{
  typename iterator_traits<_InputIterator>::difference_type __n = 0;
  for (; __first != __last; ++__first)
    if (__pred(*__first))
      ++__n;
  return __n;
}
```

### for_each - Apply Function to Range

```cpp
template<typename _InputIterator, typename _Function>
_Function
for_each(_InputIterator __first, _InputIterator __last, _Function __f)
{
  for (; __first != __last; ++__first)
    __f(*__first);
  return __f;  // Return function object (may have state)
}
```

**C++17 parallel version:**
```cpp
template<typename _ExecutionPolicy, typename _ForwardIterator, typename _Function>
void
for_each(_ExecutionPolicy&& __policy,
         _ForwardIterator __first, _ForwardIterator __last,
         _Function __f)
{
  // Parallel execution based on policy
}
```

---

## Modifying Algorithms

### copy - Copy Range

**Location:** `include/bits/stl_algobase.h`

```cpp
template<typename _InputIterator, typename _OutputIterator>
inline _OutputIterator
copy(_InputIterator __first, _InputIterator __last,
     _OutputIterator __result)
{
  return std::__copy_move_a2<__is_move_iterator<_InputIterator>::__value>
    (std::__miter_base(__first), std::__miter_base(__last), __result);
}

// Optimized for trivially copyable types
template<typename _Tp>
inline _Tp*
__copy_move_a2(const _Tp* __first, const _Tp* __last, _Tp* __result)
{
  const ptrdiff_t _Num = __last - __first;
  if (_Num)
    __builtin_memmove(__result, __first, sizeof(_Tp) * _Num);
  return __result + _Num;
}
```

**Optimization:** Uses `memmove` for trivially copyable types

### transform - Apply Function and Store Result

```cpp
// Unary version
template<typename _InputIterator, typename _OutputIterator,
         typename _UnaryOperation>
_OutputIterator
transform(_InputIterator __first, _InputIterator __last,
          _OutputIterator __result, _UnaryOperation __op)
{
  for (; __first != __last; ++__first, ++__result)
    *__result = __op(*__first);
  return __result;
}

// Binary version
template<typename _InputIterator1, typename _InputIterator2,
         typename _OutputIterator, typename _BinaryOperation>
_OutputIterator
transform(_InputIterator1 __first1, _InputIterator1 __last1,
          _InputIterator2 __first2,
          _OutputIterator __result, _BinaryOperation __binary_op)
{
  for (; __first1 != __last1; ++__first1, ++__first2, ++__result)
    *__result = __binary_op(*__first1, *__first2);
  return __result;
}
```

### remove_if - Remove Elements Satisfying Predicate

```cpp
template<typename _ForwardIterator, typename _Predicate>
_ForwardIterator
remove_if(_ForwardIterator __first, _ForwardIterator __last,
          _Predicate __pred)
{
  // Find first element to remove
  __first = std::find_if(__first, __last, __pred);
  if (__first == __last)
    return __first;
  
  // Compact remaining elements
  _ForwardIterator __result = __first;
  ++__first;
  for (; __first != __last; ++__first)
    if (!__pred(*__first))
    {
      *__result = std::move(*__first);
      ++__result;
    }
  return __result;
}
```

**Important:** Doesn't actually erase elements, returns new logical end

**Usage:**
```cpp
vec.erase(std::remove_if(vec.begin(), vec.end(), predicate), vec.end());
```

---

## Sorting and Searching

### sort - Introsort (Hybrid Algorithm)

**Location:** `include/bits/stl_algo.h`

libstdc++ uses **introsort**: hybrid of quicksort, heapsort, and insertion sort

```cpp
template<typename _RandomAccessIterator, typename _Compare>
inline void
sort(_RandomAccessIterator __first, _RandomAccessIterator __last,
     _Compare __comp)
{
  if (__first != __last)
  {
    std::__introsort_loop(__first, __last,
                         std::__lg(__last - __first) * 2,
                         __comp);
    std::__final_insertion_sort(__first, __last, __comp);
  }
}

// Introsort loop (quicksort with depth limit)
template<typename _RandomAccessIterator, typename _Size, typename _Compare>
void
__introsort_loop(_RandomAccessIterator __first,
                 _RandomAccessIterator __last,
                 _Size __depth_limit, _Compare __comp)
{
  while (__last - __first > int(_S_threshold))  // Threshold = 16
  {
    if (__depth_limit == 0)
    {
      // Depth limit exceeded, switch to heapsort
      std::__partial_sort(__first, __last, __last, __comp);
      return;
    }
    --__depth_limit;
    
    // Partition using median-of-three
    _RandomAccessIterator __cut =
      std::__unguarded_partition_pivot(__first, __last, __comp);
    
    // Recurse on larger partition, iterate on smaller (tail recursion)
    std::__introsort_loop(__cut, __last, __depth_limit, __comp);
    __last = __cut;
  }
}

// Final insertion sort for small ranges
template<typename _RandomAccessIterator, typename _Compare>
void
__final_insertion_sort(_RandomAccessIterator __first,
                      _RandomAccessIterator __last, _Compare __comp)
{
  if (__last - __first > int(_S_threshold))
  {
    std::__insertion_sort(__first, __first + int(_S_threshold), __comp);
    std::__unguarded_insertion_sort(__first + int(_S_threshold), __last, __comp);
  }
  else
    std::__insertion_sort(__first, __last, __comp);
}
```

**Algorithm strategy:**
1. **Quicksort** for large ranges (fast average case)
2. **Heapsort** when recursion depth exceeds limit (avoid O(n²) worst case)
3. **Insertion sort** for small ranges (< 16 elements, low overhead)

**Complexity:** O(n log n) worst case, O(n log n) average case

### binary_search - Binary Search

```cpp
template<typename _ForwardIterator, typename _Tp, typename _Compare>
inline bool
binary_search(_ForwardIterator __first, _ForwardIterator __last,
              const _Tp& __val, _Compare __comp)
{
  _ForwardIterator __i = std::lower_bound(__first, __last, __val, __comp);
  return __i != __last && !__comp(__val, *__i);
}

// lower_bound: first element >= val
template<typename _ForwardIterator, typename _Tp, typename _Compare>
_ForwardIterator
lower_bound(_ForwardIterator __first, _ForwardIterator __last,
            const _Tp& __val, _Compare __comp)
{
  typename iterator_traits<_ForwardIterator>::difference_type
    __len = std::distance(__first, __last);
  
  while (__len > 0)
  {
    typename iterator_traits<_ForwardIterator>::difference_type
      __half = __len >> 1;
    _ForwardIterator __middle = __first;
    std::advance(__middle, __half);
    
    if (__comp(*__middle, __val))
    {
      __first = __middle;
      ++__first;
      __len = __len - __half - 1;
    }
    else
      __len = __half;
  }
  return __first;
}
```

---

## Numeric Algorithms

### accumulate - Sum or Fold

**Location:** `include/bits/stl_numeric.h`

```cpp
template<typename _InputIterator, typename _Tp>
_Tp
accumulate(_InputIterator __first, _InputIterator __last, _Tp __init)
{
  for (; __first != __last; ++__first)
    __init = __init + *__first;
  return __init;
}

// With custom binary operation
template<typename _InputIterator, typename _Tp, typename _BinaryOperation>
_Tp
accumulate(_InputIterator __first, _InputIterator __last,
           _Tp __init, _BinaryOperation __binary_op)
{
  for (; __first != __last; ++__first)
    __init = __binary_op(__init, *__first);
  return __init;
}
```

### transform_reduce - Parallel-Friendly Reduction

**C++17:**
```cpp
template<typename _InputIterator1, typename _InputIterator2, typename _Tp>
_Tp
transform_reduce(_InputIterator1 __first1, _InputIterator1 __last1,
                 _InputIterator2 __first2, _Tp __init)
{
  for (; __first1 != __last1; ++__first1, ++__first2)
    __init = std::move(__init) + (*__first1 * *__first2);
  return __init;
}
```

**Difference from `inner_product`:** Order of operations not specified, allowing parallelization

---

## Parallel Algorithms

**C++17 Execution Policies:**

```cpp
namespace std::execution
{
  // Sequential execution
  struct sequenced_policy { };
  inline constexpr sequenced_policy seq{ };
  
  // Parallel execution
  struct parallel_policy { };
  inline constexpr parallel_policy par{ };
  
  // Parallel + vectorized execution
  struct parallel_unsequenced_policy { };
  inline constexpr parallel_unsequenced_policy par_unseq{ };
}
```

**Usage:**
```cpp
std::vector<int> vec = {3, 1, 4, 1, 5, 9, 2, 6};

// Sequential
std::sort(vec.begin(), vec.end());

// Parallel
std::sort(std::execution::par, vec.begin(), vec.end());

// Parallel + vectorized
std::sort(std::execution::par_unseq, vec.begin(), vec.end());
```

**Implementation:** Uses threading library (TBB, OpenMP, or custom)

---

## Algorithm Complexity Summary

| Algorithm | Time Complexity | Space Complexity |
|-----------|----------------|------------------|
| find | O(n) | O(1) |
| binary_search | O(log n) | O(1) |
| sort | O(n log n) | O(log n) |
| stable_sort | O(n log n) | O(n) |
| partial_sort | O(n log k) | O(1) |
| nth_element | O(n) average | O(1) |
| copy | O(n) | O(1) |
| transform | O(n) | O(1) |
| accumulate | O(n) | O(1) |
| unique | O(n) | O(1) |
| reverse | O(n) | O(1) |
| rotate | O(n) | O(1) |

---

## Best Practices

1. **Use algorithms instead of raw loops**
   - More expressive
   - Better optimized
   - Less error-prone

2. **Choose the right iterator category**
   - Random access for best performance
   - Forward for flexibility

3. **Leverage parallel algorithms (C++17+)**
   - Easy parallelization
   - Automatic load balancing

4. **Understand complexity guarantees**
   - Choose appropriate algorithm
   - Avoid unnecessary work

---

## Next Steps

Continue to **Document 05: Advanced Topics** for template metaprogramming, threading, and more advanced libstdc++ features.

