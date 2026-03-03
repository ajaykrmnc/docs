# Understanding libstdc++ Containers: Deep Dive

## Table of Contents
1. [Container Overview](#container-overview)
2. [Sequence Containers](#sequence-containers)
3. [Associative Containers](#associative-containers)
4. [Unordered Containers](#unordered-containers)
5. [Container Adaptors](#container-adaptors)
6. [Memory Management and Allocators](#memory-management-and-allocators)
7. [Iterator Implementation](#iterator-implementation)

---

## Container Overview

### Container Hierarchy

```
Containers
├── Sequence Containers
│   ├── array          (Fixed-size array)
│   ├── vector         (Dynamic array)
│   ├── deque          (Double-ended queue)
│   ├── list           (Doubly-linked list)
│   └── forward_list   (Singly-linked list)
│
├── Associative Containers (Ordered)
│   ├── set            (Unique keys, sorted)
│   ├── multiset       (Duplicate keys, sorted)
│   ├── map            (Key-value, unique keys, sorted)
│   └── multimap       (Key-value, duplicate keys, sorted)
│
├── Unordered Containers (Hash-based)
│   ├── unordered_set
│   ├── unordered_multiset
│   ├── unordered_map
│   └── unordered_multimap
│
└── Container Adaptors
    ├── stack          (LIFO)
    ├── queue          (FIFO)
    └── priority_queue (Heap)
```

---

## Sequence Containers

### 1. std::vector - Dynamic Array

**Location:** `include/bits/stl_vector.h`, `include/bits/vector.tcc`

#### Internal Structure

```cpp
template<typename _Tp, typename _Alloc = allocator<_Tp>>
class vector : protected _Vector_base<_Tp, _Alloc>
{
  // Inherits from _Vector_base for memory management
};

template<typename _Tp, typename _Alloc>
struct _Vector_base
{
  struct _Vector_impl : public _Alloc
  {
    pointer _M_start;          // Points to first element
    pointer _M_finish;         // Points one past last element
    pointer _M_end_of_storage; // Points to end of allocated memory
  };
  
  _Vector_impl _M_impl;
};
```

**Memory Layout:**
```
_M_start          _M_finish      _M_end_of_storage
    ↓                 ↓                  ↓
    [elem0][elem1][elem2][unused][unused]
    |<---- size() ---->|
    |<-------- capacity() -------->|
```

#### Key Operations

**push_back Implementation:**
```cpp
void push_back(const value_type& __x)
{
  if (this->_M_impl._M_finish != this->_M_impl._M_end_of_storage)
  {
    // Fast path: space available
    _Alloc_traits::construct(this->_M_impl, 
                            this->_M_impl._M_finish, __x);
    ++this->_M_impl._M_finish;
  }
  else
  {
    // Slow path: reallocation needed
    _M_realloc_insert(end(), __x);
  }
}
```

**Growth Strategy:**
```cpp
size_type _M_check_len(size_type __n, const char* __s) const
{
  if (max_size() - size() < __n)
    __throw_length_error(__N(__s));
  
  // Growth formula: new_size = old_size + max(old_size, n)
  const size_type __len = size() + std::max(size(), __n);
  
  return (__len < size() || __len > max_size()) ? max_size() : __len;
}
```

**Typical growth:** Capacity doubles each time
- Initial: 0
- After 1st push: 1
- After 2nd push: 2
- After 3rd push: 4
- After 5th push: 8
- ...

**Complexity:**
- `push_back`: Amortized O(1)
- `insert`: O(n)
- `erase`: O(n)
- `operator[]`: O(1)
- `at`: O(1) with bounds checking

#### Special Case: vector<bool>

**Location:** `include/bits/stl_bvector.h`

```cpp
template<typename _Alloc>
class vector<bool, _Alloc>
{
  typedef unsigned long _WordT;
  static const int _S_word_bit = __CHAR_BIT__ * sizeof(_WordT);
  
  // Storage: array of words, each word holds multiple bits
  _WordT* _M_start;
  
  // Proxy reference class
  struct reference
  {
    _WordT* _M_p;      // Pointer to word
    _WordT _M_mask;    // Bit mask
    
    operator bool() const noexcept
    { return !!(*_M_p & _M_mask); }
    
    reference& operator=(bool __x) noexcept
    {
      if (__x)
        *_M_p |= _M_mask;   // Set bit
      else
        *_M_p &= ~_M_mask;  // Clear bit
      return *this;
    }
  };
};
```

**Why different?**
- Space optimization: 1 bit per bool vs 1 byte
- Can't return `bool&` (no bit references)
- Returns proxy object
- Not a standard container (doesn't meet requirements)

---

### 2. std::deque - Double-Ended Queue

**Location:** `include/bits/stl_deque.h`, `include/bits/deque.tcc`

#### Internal Structure

```cpp
template<typename _Tp, typename _Alloc = allocator<_Tp>>
class deque : protected _Deque_base<_Tp, _Alloc>
{
  // Map of pointers to fixed-size chunks
};

template<typename _Tp, typename _Alloc>
struct _Deque_base
{
  struct _Deque_impl : public _Alloc
  {
    _Tp** _M_map;           // Array of pointers to chunks
    size_t _M_map_size;     // Size of map array
    iterator _M_start;      // Points to first element
    iterator _M_finish;     // Points past last element
  };
};
```

**Memory Layout:**
```
_M_map:
  [0] → [chunk0: elem elem elem elem elem elem]
  [1] → [chunk1: elem elem elem elem elem elem]
  [2] → [chunk2: elem elem elem elem elem elem]
  [3] → [chunk3: elem elem elem elem elem elem]
         ↑                              ↑
      _M_start                      _M_finish
```

**Chunk size:** Typically 512 bytes / sizeof(T)

#### Deque Iterator

```cpp
template<typename _Tp, typename _Ref, typename _Ptr>
struct _Deque_iterator
{
  _Tp* _M_cur;        // Current element
  _Tp* _M_first;      // Start of current chunk
  _Tp* _M_last;       // End of current chunk
  _Tp** _M_node;      // Pointer to map entry
  
  // Increment: handle chunk boundaries
  _Self& operator++()
  {
    ++_M_cur;
    if (_M_cur == _M_last)  // End of chunk?
    {
      _M_set_node(_M_node + 1);  // Move to next chunk
      _M_cur = _M_first;
    }
    return *this;
  }
};
```

**Advantages over vector:**
- O(1) push_front and pop_front
- No reallocation of existing elements
- Stable iterators (except at ends)

**Disadvantages:**
- More complex iterator
- Slightly slower random access
- More memory overhead

---

### 3. std::list - Doubly-Linked List

**Location:** `include/bits/stl_list.h`, `include/bits/list.tcc`

#### Internal Structure

```cpp
template<typename _Tp, typename _Alloc = allocator<_Tp>>
class list : protected _List_base<_Tp, _Alloc>
{
  // Circular doubly-linked list with sentinel node
};

struct _List_node_base
{
  _List_node_base* _M_next;
  _List_node_base* _M_prev;
};

template<typename _Tp>
struct _List_node : public _List_node_base
{
  _Tp _M_data;  // Actual element
};

template<typename _Tp, typename _Alloc>
struct _List_base
{
  struct _List_impl : public _Alloc
  {
    _List_node_base _M_node;  // Sentinel node (not an element)
  };
};
```

**Memory Layout:**
```
Sentinel node (header)
     ↓
  [_M_node] ←→ [node1] ←→ [node2] ←→ [node3] ←→ [_M_node]
     ↑                                              ↑
  _M_prev                                       _M_next
  
  Circular: _M_node._M_next points to first element
           _M_node._M_prev points to last element
```

#### Key Operations

**push_back:**
```cpp
void push_back(const value_type& __x)
{
  this->_M_insert(end(), __x);
}

iterator _M_insert(iterator __position, const value_type& __x)
{
  _Node* __tmp = _M_create_node(__x);  // Allocate and construct
  __tmp->_M_next = __position._M_node;
  __tmp->_M_prev = __position._M_node->_M_prev;
  __position._M_node->_M_prev->_M_next = __tmp;
  __position._M_node->_M_prev = __tmp;
  return iterator(__tmp);
}
```

**splice (move elements from another list):**
```cpp
void splice(iterator __position, list& __x, iterator __i)
{
  iterator __j = __i;
  ++__j;
  
  // Unlink from source
  __i._M_node->_M_prev->_M_next = __j._M_node;
  __j._M_node->_M_prev = __i._M_node->_M_prev;
  
  // Link into destination
  __i._M_node->_M_next = __position._M_node;
  __i._M_node->_M_prev = __position._M_node->_M_prev;
  __position._M_node->_M_prev->_M_next = __i._M_node;
  __position._M_node->_M_prev = __i._M_node;
}
```

**Advantages:**
- O(1) insertion/deletion anywhere (with iterator)
- O(1) splice operations
- Stable iterators (never invalidated except erased elements)

**Disadvantages:**
- No random access
- Higher memory overhead (2 pointers per element)
- Poor cache locality

---

### 4. std::array - Fixed-Size Array

**Location:** `include/array`

#### Internal Structure

```cpp
template<typename _Tp, std::size_t _Nm>
struct array
{
  typedef _Tp value_type;
  typedef value_type* pointer;
  typedef const value_type* const_pointer;
  typedef value_type& reference;
  typedef const value_type& const_reference;
  typedef value_type* iterator;
  typedef const value_type* const_iterator;
  typedef std::size_t size_type;
  typedef std::ptrdiff_t difference_type;
  
  // The actual array
  value_type _M_elems[_Nm ? _Nm : 1];  // Avoid zero-size array
  
  // No constructor, destructor, or assignment operator
  // Aggregate initialization
};
```

**Key features:**
- Zero overhead wrapper around C array
- Aggregate type (can use brace initialization)
- No dynamic allocation
- Size is part of type
- Provides STL container interface

**Usage:**
```cpp
std::array<int, 5> arr = {1, 2, 3, 4, 5};
arr[0] = 10;
arr.at(1) = 20;  // Bounds checked
```

---

## Associative Containers

### 1. std::map and std::set - Red-Black Trees

**Location:** `include/bits/stl_map.h`, `include/bits/stl_tree.h`

#### Internal Structure

Both `map` and `set` are implemented using red-black trees:

```cpp
template<typename _Key, typename _Val, typename _Compare = less<_Key>>
class _Rb_tree
{
  struct _Rb_tree_node_base
  {
    typedef _Rb_tree_node_base* _Base_ptr;
    typedef const _Rb_tree_node_base* _Const_Base_ptr;
    
    _Rb_tree_color _M_color;  // Red or black
    _Base_ptr _M_parent;
    _Base_ptr _M_left;
    _Base_ptr _M_right;
  };
  
  template<typename _Val>
  struct _Rb_tree_node : public _Rb_tree_node_base
  {
    _Val _M_value_field;  // The actual data
  };
  
  _Rb_tree_node_base _M_header;  // Sentinel node
  size_type _M_node_count;
  _Compare _M_key_compare;
};
```

**Tree Structure:**
```
         [header]
            ↓
         [root:B]
         /      \
     [5:R]      [15:R]
     /   \      /    \
  [3:B] [7:B] [12:B] [20:B]
  
  B = Black node
  R = Red node
```

**Red-Black Tree Properties:**
1. Every node is red or black
2. Root is black
3. All leaves (NULL) are black
4. Red nodes have black children
5. All paths from root to leaves have same number of black nodes

#### Map Implementation

```cpp
template<typename _Key, typename _Tp, typename _Compare = less<_Key>,
         typename _Alloc = allocator<pair<const _Key, _Tp>>>
class map
{
  typedef _Key key_type;
  typedef _Tp mapped_type;
  typedef pair<const _Key, _Tp> value_type;
  typedef _Compare key_compare;
  
  // Uses red-black tree
  typedef _Rb_tree<key_type, value_type, _Select1st<value_type>,
                   key_compare, _Alloc> _Rep_type;
  
  _Rep_type _M_t;  // The actual tree
  
public:
  mapped_type& operator[](const key_type& __k)
  {
    iterator __i = lower_bound(__k);
    if (__i == end() || key_comp()(__k, (*__i).first))
      __i = insert(__i, value_type(__k, mapped_type()));
    return (*__i).second;
  }
};
```

**Complexity:**
- `insert`: O(log n)
- `find`: O(log n)
- `erase`: O(log n)
- Iteration: O(n) in sorted order

---

## Unordered Containers

### std::unordered_map - Hash Table

**Location:** `include/bits/hashtable.h`, `include/bits/unordered_map.h`

#### Internal Structure

```cpp
template<typename _Key, typename _Value, typename _Hash = hash<_Key>,
         typename _Pred = equal_to<_Key>, typename _Alloc = allocator<_Value>>
class _Hashtable
{
  // Separate chaining with linked lists
  struct _Hash_node_base
  {
    _Hash_node_base* _M_next;  // Next in bucket chain
  };
  
  template<typename _Value>
  struct _Hash_node : _Hash_node_base
  {
    _Value _M_value;  // The actual key-value pair
  };
  
  _Hash_node_base** _M_buckets;     // Array of bucket heads
  size_type _M_bucket_count;        // Number of buckets
  size_type _M_element_count;       // Number of elements
  _Hash_node_base _M_before_begin;  // Sentinel
  float _M_max_load_factor;         // Rehash threshold
};
```

**Memory Layout:**
```
_M_buckets:
  [0] → node → node → nullptr
  [1] → nullptr
  [2] → node → nullptr
  [3] → node → node → node → nullptr
  [4] → nullptr
  ...
```

#### Hash Function

```cpp
template<typename _Key>
struct hash;  // Primary template (undefined)

// Specializations for built-in types
template<>
struct hash<int>
{
  size_t operator()(int __val) const noexcept
  { return static_cast<size_t>(__val); }
};

template<>
struct hash<string>
{
  size_t operator()(const string& __s) const noexcept
  {
    // MurmurHash or similar
    return _Hash_impl::hash(__s.data(), __s.length());
  }
};
```

#### Rehashing

```cpp
void _M_rehash(size_type __n)
{
  // Allocate new bucket array
  _Hash_node_base** __new_buckets = _M_allocate_buckets(__n);
  
  // Reinsert all elements
  for (size_type __i = 0; __i < _M_bucket_count; ++__i)
  {
    _Hash_node_base* __p = _M_buckets[__i];
    while (__p)
    {
      _Hash_node_base* __next = __p->_M_next;
      size_type __new_index = _M_bucket_index(__p, __n);
      __p->_M_next = __new_buckets[__new_index];
      __new_buckets[__new_index] = __p;
      __p = __next;
    }
  }
  
  // Swap buckets
  _M_deallocate_buckets(_M_buckets, _M_bucket_count);
  _M_buckets = __new_buckets;
  _M_bucket_count = __n;
}
```

**Load factor:** `element_count / bucket_count`
- Default max load factor: 1.0
- Rehashes when load factor exceeds max
- New bucket count: typically 2x old count

**Complexity:**
- `insert`: Average O(1), worst O(n)
- `find`: Average O(1), worst O(n)
- `erase`: Average O(1), worst O(n)

---

## Container Adaptors

### std::stack

**Location:** `include/bits/stl_stack.h`

```cpp
template<typename _Tp, typename _Sequence = deque<_Tp>>
class stack
{
protected:
  _Sequence c;  // Underlying container
  
public:
  void push(const value_type& __x) { c.push_back(__x); }
  void pop() { c.pop_back(); }
  reference top() { return c.back(); }
  bool empty() const { return c.empty(); }
  size_type size() const { return c.size(); }
};
```

**Adapter pattern:** Wraps another container (default: deque)

### std::priority_queue

**Location:** `include/bits/stl_queue.h`

```cpp
template<typename _Tp, typename _Sequence = vector<_Tp>,
         typename _Compare = less<typename _Sequence::value_type>>
class priority_queue
{
protected:
  _Sequence c;      // Underlying container (heap)
  _Compare comp;    // Comparison function
  
public:
  void push(const value_type& __x)
  {
    c.push_back(__x);
    std::push_heap(c.begin(), c.end(), comp);  // Restore heap property
  }
  
  void pop()
  {
    std::pop_heap(c.begin(), c.end(), comp);
    c.pop_back();
  }
  
  const_reference top() const { return c.front(); }
};
```

**Heap implementation:** Binary max-heap using vector

---

## Memory Management and Allocators

### Allocator Interface

```cpp
template<typename _Tp>
class allocator
{
public:
  typedef _Tp value_type;
  typedef _Tp* pointer;
  typedef const _Tp* const_pointer;
  typedef _Tp& reference;
  typedef const _Tp& const_reference;
  typedef size_t size_type;
  typedef ptrdiff_t difference_type;
  
  pointer allocate(size_type __n)
  {
    return static_cast<_Tp*>(::operator new(__n * sizeof(_Tp)));
  }
  
  void deallocate(pointer __p, size_type)
  {
    ::operator delete(__p);
  }
  
  template<typename... _Args>
  void construct(pointer __p, _Args&&... __args)
  {
    ::new((void*)__p) _Tp(std::forward<_Args>(__args)...);
  }
  
  void destroy(pointer __p)
  {
    __p->~_Tp();
  }
};
```

### Allocator Traits

```cpp
template<typename _Alloc>
struct allocator_traits
{
  typedef _Alloc allocator_type;
  typedef typename _Alloc::value_type value_type;
  typedef typename _Alloc::pointer pointer;
  
  static pointer allocate(_Alloc& __a, size_type __n)
  { return __a.allocate(__n); }
  
  static void deallocate(_Alloc& __a, pointer __p, size_type __n)
  { __a.deallocate(__p, __n); }
  
  template<typename _Tp, typename... _Args>
  static void construct(_Alloc& __a, _Tp* __p, _Args&&... __args)
  {
    __a.construct(__p, std::forward<_Args>(__args)...);
  }
};
```

---

## Iterator Implementation

### Iterator Categories

```cpp
struct input_iterator_tag { };
struct output_iterator_tag { };
struct forward_iterator_tag : public input_iterator_tag { };
struct bidirectional_iterator_tag : public forward_iterator_tag { };
struct random_access_iterator_tag : public bidirectional_iterator_tag { };
struct contiguous_iterator_tag : public random_access_iterator_tag { };  // C++20
```

### Vector Iterator

```cpp
template<typename _Iterator, typename _Container>
class __normal_iterator
{
protected:
  _Iterator _M_current;  // Pointer to element
  
public:
  reference operator*() const { return *_M_current; }
  pointer operator->() const { return _M_current; }
  
  __normal_iterator& operator++()
  {
    ++_M_current;
    return *this;
  }
  
  __normal_iterator& operator+=(difference_type __n)
  {
    _M_current += __n;
    return *this;
  }
};
```

**For vector:** Iterator is essentially a pointer wrapper

---

## Performance Characteristics Summary

| Container | Access | Insert (end) | Insert (middle) | Find | Memory |
|-----------|--------|--------------|-----------------|------|--------|
| vector | O(1) | O(1)* | O(n) | O(n) | Compact |
| deque | O(1) | O(1) | O(n) | O(n) | Chunked |
| list | O(n) | O(1) | O(1)† | O(n) | High overhead |
| array | O(1) | N/A | N/A | O(n) | Minimal |
| map | O(log n) | O(log n) | O(log n) | O(log n) | Moderate |
| unordered_map | N/A | O(1)* | O(1)* | O(1)* | High |

\* Amortized  
† With iterator

---

## Next Steps

Continue to **Document 04: Algorithms and Iterators** to understand how algorithms work with these containers.

