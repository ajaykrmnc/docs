# Advanced libstdc++ Topics: Template Metaprogramming, Threading, and More

## Table of Contents
1. [Template Metaprogramming](#template-metaprogramming)
2. [Type Traits](#type-traits)
3. [Smart Pointers](#smart-pointers)
4. [Threading and Concurrency](#threading-and-concurrency)
5. [Move Semantics and Perfect Forwarding](#move-semantics-and-perfect-forwarding)
6. [Exception Handling](#exception-handling)
7. [String Implementation](#string-implementation)
8. [Filesystem Library](#filesystem-library)

---

## Template Metaprogramming

### SFINAE (Substitution Failure Is Not An Error)

**Location:** `include/bits/cpp_type_traits.h`, `include/type_traits`

#### Basic SFINAE Pattern

```cpp
// Enable function only if T is integral
template<typename T>
typename std::enable_if<std::is_integral<T>::value, T>::type
process(T value)
{
  return value * 2;
}

// Enable function only if T is floating point
template<typename T>
typename std::enable_if<std::is_floating_point<T>::value, T>::type
process(T value)
{
  return value * 1.5;
}
```

#### Implementation in libstdc++

```cpp
// enable_if implementation
template<bool _Cond, typename _Tp = void>
struct enable_if
{ };

template<typename _Tp>
struct enable_if<true, _Tp>
{
  typedef _Tp type;
};

// C++14 alias template
template<bool _Cond, typename _Tp = void>
using enable_if_t = typename enable_if<_Cond, _Tp>::type;
```

**Usage in vector:**
```cpp
// Constructor only enabled for input iterators
template<typename _InputIterator,
         typename = std::_RequireInputIter<_InputIterator>>
vector(_InputIterator __first, _InputIterator __last,
       const allocator_type& __a = allocator_type())
{
  _M_range_initialize(__first, __last,
                     std::__iterator_category(__first));
}

// Helper type alias
template<typename _InIter>
using _RequireInputIter = typename
  enable_if<is_convertible<typename
    iterator_traits<_InIter>::iterator_category,
    input_iterator_tag>::value>::type;
```

### Tag Dispatch

Alternative to SFINAE for compile-time dispatch:

```cpp
// Public interface
template<typename _InputIterator>
void algorithm(_InputIterator __first, _InputIterator __last)
{
  __algorithm_impl(__first, __last,
                  typename iterator_traits<_InputIterator>::iterator_category());
}

// Implementation for input iterators
template<typename _InputIterator>
void __algorithm_impl(_InputIterator __first, _InputIterator __last,
                     input_iterator_tag)
{
  // Slow but general implementation
}

// Implementation for random access iterators
template<typename _RandomAccessIterator>
void __algorithm_impl(_RandomAccessIterator __first,
                     _RandomAccessIterator __last,
                     random_access_iterator_tag)
{
  // Fast implementation using random access
}
```

### Concepts (C++20)

**Location:** `include/bits/ranges_base.h`, `include/concepts`

```cpp
// Concept definition
template<typename _Iter>
concept input_iterator =
  std::input_or_output_iterator<_Iter> &&
  std::indirectly_readable<_Iter> &&
  requires { typename std::iterator_traits<_Iter>::iterator_category; } &&
  std::derived_from<typename std::iterator_traits<_Iter>::iterator_category,
                   std::input_iterator_tag>;

// Usage
template<std::input_iterator _Iter>
void algorithm(_Iter __first, _Iter __last)
{
  // Implementation
}
```

**Advantages over SFINAE:**
- More readable error messages
- Clearer intent
- Better compile times
- Can be used in requires clauses

---

## Type Traits

**Location:** `include/type_traits`

### Primary Type Categories

```cpp
// is_integral
template<typename _Tp>
struct is_integral
  : public __is_integral_helper<typename remove_cv<_Tp>::type>::type
{ };

template<typename>
struct __is_integral_helper
  : public false_type { };

template<>
struct __is_integral_helper<bool>
  : public true_type { };

template<>
struct __is_integral_helper<int>
  : public true_type { };

// ... specializations for all integral types

// C++17 variable template
template<typename _Tp>
inline constexpr bool is_integral_v = is_integral<_Tp>::value;
```

### Type Transformations

```cpp
// remove_const
template<typename _Tp>
struct remove_const
{ typedef _Tp type; };

template<typename _Tp>
struct remove_const<_Tp const>
{ typedef _Tp type; };

// remove_reference
template<typename _Tp>
struct remove_reference
{ typedef _Tp type; };

template<typename _Tp>
struct remove_reference<_Tp&>
{ typedef _Tp type; };

template<typename _Tp>
struct remove_reference<_Tp&&>
{ typedef _Tp type; };

// decay (remove cv-qualifiers and references)
template<typename _Tp>
struct decay
{
private:
  typedef typename remove_reference<_Tp>::type _Up;
  
public:
  typedef typename conditional<
    is_array<_Up>::value,
    typename remove_extent<_Up>::type*,
    typename conditional<
      is_function<_Up>::value,
      typename add_pointer<_Up>::type,
      typename remove_cv<_Up>::type
    >::type
  >::type type;
};
```

### Type Relations

```cpp
// is_same
template<typename, typename>
struct is_same
  : public false_type { };

template<typename _Tp>
struct is_same<_Tp, _Tp>
  : public true_type { };

// is_base_of (compiler intrinsic)
template<typename _Base, typename _Derived>
struct is_base_of
  : public integral_constant<bool, __is_base_of(_Base, _Derived)>
{ };

// is_convertible (compiler intrinsic)
template<typename _From, typename _To>
struct is_convertible
  : public __bool_constant<__is_convertible(_From, _To)>
{ };
```

### Compile-Time Conditionals

```cpp
// conditional (compile-time if)
template<bool _Cond, typename _Iftrue, typename _Iffalse>
struct conditional
{ typedef _Iftrue type; };

template<typename _Iftrue, typename _Iffalse>
struct conditional<false, _Iftrue, _Iffalse>
{ typedef _Iffalse type; };

// Usage
using result_type = typename conditional<
  is_integral<T>::value,
  long long,
  double
>::type;
```

---

## Smart Pointers

### unique_ptr - Exclusive Ownership

**Location:** `include/bits/unique_ptr.h`

```cpp
template<typename _Tp, typename _Dp = default_delete<_Tp>>
class unique_ptr
{
  // Compressed pair: pointer + deleter (EBO optimization)
  __uniq_ptr_impl<_Tp, _Dp> _M_t;
  
public:
  // Constructor
  constexpr unique_ptr() noexcept
    : _M_t()
  { }
  
  explicit unique_ptr(pointer __p) noexcept
    : _M_t(__p)
  { }
  
  // Move constructor (no copy!)
  unique_ptr(unique_ptr&& __u) noexcept
    : _M_t(__u.release(), std::forward<deleter_type>(__u.get_deleter()))
  { }
  
  // Destructor
  ~unique_ptr() noexcept
  {
    auto& __ptr = _M_t._M_ptr();
    if (__ptr != nullptr)
      get_deleter()(__ptr);
    __ptr = pointer();
  }
  
  // Move assignment
  unique_ptr& operator=(unique_ptr&& __u) noexcept
  {
    reset(__u.release());
    get_deleter() = std::forward<deleter_type>(__u.get_deleter());
    return *this;
  }
  
  // Deleted copy operations
  unique_ptr(const unique_ptr&) = delete;
  unique_ptr& operator=(const unique_ptr&) = delete;
  
  // Access
  pointer get() const noexcept
  { return _M_t._M_ptr(); }
  
  typename add_lvalue_reference<element_type>::type
  operator*() const
  { return *get(); }
  
  pointer operator->() const noexcept
  { return get(); }
  
  // Modifiers
  pointer release() noexcept
  {
    pointer __p = get();
    _M_t._M_ptr() = pointer();
    return __p;
  }
  
  void reset(pointer __p = pointer()) noexcept
  {
    using std::swap;
    swap(_M_t._M_ptr(), __p);
    if (__p != pointer())
      get_deleter()(__p);
  }
};
```

**Key features:**
- Zero overhead (same size as raw pointer with default deleter)
- Move-only semantics
- Custom deleters
- Array specialization

### shared_ptr - Shared Ownership

**Location:** `include/bits/shared_ptr.h`, `include/bits/shared_ptr_base.h`

```cpp
template<typename _Tp>
class shared_ptr : public __shared_ptr<_Tp>
{
  // Implementation in __shared_ptr
};

template<typename _Tp, _Lock_policy _Lp>
class __shared_ptr
{
  element_type* _M_ptr;         // Pointer to object
  __shared_count<_Lp> _M_refcount;  // Reference count
  
public:
  constexpr shared_ptr() noexcept
    : _M_ptr(0), _M_refcount()
  { }
  
  template<typename _Yp>
  explicit shared_ptr(_Yp* __p)
    : _M_ptr(__p), _M_refcount(__p)
  {
    static_assert(sizeof(_Yp) > 0, "incomplete type");
    __enable_shared_from_this_helper(_M_refcount, __p, __p);
  }
  
  // Copy constructor (increment ref count)
  shared_ptr(const shared_ptr& __r) noexcept
    : _M_ptr(__r._M_ptr), _M_refcount(__r._M_refcount)
  { }
  
  // Move constructor (transfer ownership)
  shared_ptr(shared_ptr&& __r) noexcept
    : _M_ptr(__r._M_ptr), _M_refcount()
  {
    _M_refcount._M_swap(__r._M_refcount);
    __r._M_ptr = 0;
  }
  
  ~shared_ptr() noexcept = default;  // __shared_count handles cleanup
  
  long use_count() const noexcept
  { return _M_refcount._M_get_use_count(); }
};
```

#### Reference Counting Implementation

```cpp
template<_Lock_policy _Lp>
class __shared_count
{
  _Sp_counted_base<_Lp>* _M_pi;
  
public:
  __shared_count() noexcept : _M_pi(0)
  { }
  
  template<typename _Ptr>
  explicit __shared_count(_Ptr __p) : _M_pi(0)
  {
    __try
    {
      _M_pi = new _Sp_counted_ptr<_Ptr, _Lp>(__p);
    }
    __catch(...)
    {
      delete __p;
      __throw_exception_again;
    }
  }
  
  ~__shared_count() noexcept
  {
    if (_M_pi != 0)
      _M_pi->_M_release();
  }
  
  __shared_count(const __shared_count& __r) noexcept
    : _M_pi(__r._M_pi)
  {
    if (_M_pi != 0)
      _M_pi->_M_add_ref_copy();
  }
};

template<_Lock_policy _Lp>
class _Sp_counted_base
{
  _Atomic_word _M_use_count;     // Strong references
  _Atomic_word _M_weak_count;    // Weak references
  
public:
  void _M_add_ref_copy()
  { __gnu_cxx::__atomic_add_dispatch(&_M_use_count, 1); }
  
  void _M_release() noexcept
  {
    if (__gnu_cxx::__exchange_and_add_dispatch(&_M_use_count, -1) == 1)
    {
      _M_dispose();  // Delete object
      if (__gnu_cxx::__exchange_and_add_dispatch(&_M_weak_count, -1) == 1)
        _M_destroy();  // Delete control block
    }
  }
  
  virtual void _M_dispose() noexcept = 0;  // Delete object
  virtual void _M_destroy() noexcept { delete this; }  // Delete control block
};
```

**Memory layout:**
```
shared_ptr:
  _M_ptr ────────────────┐
  _M_refcount._M_pi ──┐  │
                      │  │
                      ↓  ↓
Control Block:     [Object]
  _M_use_count: 3
  _M_weak_count: 1
  deleter
  allocator
```

### weak_ptr - Non-Owning Observer

```cpp
template<typename _Tp>
class weak_ptr : public __weak_ptr<_Tp>
{
public:
  shared_ptr<_Tp> lock() const noexcept
  {
    return shared_ptr<_Tp>(*this, std::nothrow);
  }
  
  bool expired() const noexcept
  { return _M_refcount._M_get_use_count() == 0; }
};
```

**Use case:** Break circular references

---

## Threading and Concurrency

### std::thread

**Location:** `include/thread`

```cpp
class thread
{
  id _M_id;  // Thread identifier
  
public:
  thread() noexcept = default;
  
  template<typename _Callable, typename... _Args>
  explicit thread(_Callable&& __f, _Args&&... __args)
  {
    _M_start_thread(_S_make_state(
      __make_invoker(std::forward<_Callable>(__f),
                    std::forward<_Args>(__args)...)));
  }
  
  ~thread()
  {
    if (joinable())
      std::terminate();  // Must join or detach!
  }
  
  thread(const thread&) = delete;  // Not copyable
  thread(thread&& __t) noexcept { swap(__t); }  // Movable
  
  void join();
  void detach();
  bool joinable() const noexcept;
  id get_id() const noexcept;
};
```

### std::mutex

**Location:** `include/mutex`

```cpp
class mutex
{
  __gthread_mutex_t _M_mutex;
  
public:
  constexpr mutex() noexcept : _M_mutex(__GTHREAD_MUTEX_INIT)
  { }
  
  ~mutex() { __gthread_mutex_destroy(&_M_mutex); }
  
  mutex(const mutex&) = delete;
  mutex& operator=(const mutex&) = delete;
  
  void lock()
  {
    int __e = __gthread_mutex_lock(&_M_mutex);
    if (__e)
      __throw_system_error(__e);
  }
  
  bool try_lock() noexcept
  {
    return !__gthread_mutex_trylock(&_M_mutex);
  }
  
  void unlock()
  {
    __gthread_mutex_unlock(&_M_mutex);
  }
  
  native_handle_type native_handle() noexcept
  { return &_M_mutex; }
};
```

### std::lock_guard and std::unique_lock

```cpp
// lock_guard: Simple RAII wrapper
template<typename _Mutex>
class lock_guard
{
  _Mutex& _M_device;
  
public:
  typedef _Mutex mutex_type;
  
  explicit lock_guard(mutex_type& __m) : _M_device(__m)
  { _M_device.lock(); }
  
  ~lock_guard()
  { _M_device.unlock(); }
  
  lock_guard(const lock_guard&) = delete;
  lock_guard& operator=(const lock_guard&) = delete;
};

// unique_lock: Flexible RAII wrapper
template<typename _Mutex>
class unique_lock
{
  _Mutex* _M_device;
  bool _M_owns;
  
public:
  unique_lock() noexcept : _M_device(0), _M_owns(false)
  { }
  
  explicit unique_lock(mutex_type& __m)
    : _M_device(std::__addressof(__m)), _M_owns(false)
  {
    lock();
    _M_owns = true;
  }
  
  unique_lock(mutex_type& __m, defer_lock_t) noexcept
    : _M_device(std::__addressof(__m)), _M_owns(false)
  { }
  
  unique_lock(mutex_type& __m, try_to_lock_t)
    : _M_device(std::__addressof(__m)), _M_owns(_M_device->try_lock())
  { }
  
  unique_lock(mutex_type& __m, adopt_lock_t) noexcept
    : _M_device(std::__addressof(__m)), _M_owns(true)
  { }
  
  ~unique_lock()
  {
    if (_M_owns)
      unlock();
  }
  
  void lock()
  {
    _M_device->lock();
    _M_owns = true;
  }
  
  void unlock()
  {
    _M_device->unlock();
    _M_owns = false;
  }
  
  bool owns_lock() const noexcept { return _M_owns; }
};
```

### std::atomic

**Location:** `include/atomic`

```cpp
template<typename _Tp>
struct atomic
{
  _Tp _M_i;
  
  atomic() noexcept = default;
  constexpr atomic(_Tp __i) noexcept : _M_i(__i) { }
  
  atomic(const atomic&) = delete;
  atomic& operator=(const atomic&) = delete;
  
  _Tp load(memory_order __m = memory_order_seq_cst) const noexcept
  {
    return __atomic_load_n(&_M_i, int(__m));
  }
  
  void store(_Tp __i, memory_order __m = memory_order_seq_cst) noexcept
  {
    __atomic_store_n(&_M_i, __i, int(__m));
  }
  
  _Tp exchange(_Tp __i, memory_order __m = memory_order_seq_cst) noexcept
  {
    return __atomic_exchange_n(&_M_i, __i, int(__m));
  }
  
  bool compare_exchange_weak(_Tp& __e, _Tp __i,
                            memory_order __m = memory_order_seq_cst) noexcept
  {
    return __atomic_compare_exchange_n(&_M_i, &__e, __i, true,
                                      int(__m), int(__m));
  }
  
  _Tp fetch_add(_Tp __i, memory_order __m = memory_order_seq_cst) noexcept
  {
    return __atomic_fetch_add(&_M_i, __i, int(__m));
  }
};
```

---

## Move Semantics and Perfect Forwarding

### std::move

**Location:** `include/bits/move.h`

```cpp
template<typename _Tp>
constexpr typename std::remove_reference<_Tp>::type&&
move(_Tp&& __t) noexcept
{
  return static_cast<typename std::remove_reference<_Tp>::type&&>(__t);
}
```

**What it does:** Casts to rvalue reference (doesn't actually move anything)

### std::forward

```cpp
template<typename _Tp>
constexpr _Tp&&
forward(typename std::remove_reference<_Tp>::type& __t) noexcept
{
  return static_cast<_Tp&&>(__t);
}

template<typename _Tp>
constexpr _Tp&&
forward(typename std::remove_reference<_Tp>::type&& __t) noexcept
{
  static_assert(!std::is_lvalue_reference<_Tp>::value,
               "template argument substituting _Tp is an lvalue reference type");
  return static_cast<_Tp&&>(__t);
}
```

**Perfect forwarding pattern:**
```cpp
template<typename... _Args>
void emplace_back(_Args&&... __args)
{
  _Alloc_traits::construct(_M_impl, _M_impl._M_finish,
                          std::forward<_Args>(__args)...);
  ++_M_impl._M_finish;
}
```

---

## Exception Handling

### Exception Hierarchy

**Location:** `libsupc++/exception`, `include/stdexcept`

```cpp
namespace std
{
  class exception
  {
  public:
    exception() noexcept { }
    virtual ~exception() noexcept;
    virtual const char* what() const noexcept;
  };
  
  class logic_error : public exception
  {
    string _M_msg;
  public:
    explicit logic_error(const string& __arg);
    virtual const char* what() const noexcept;
  };
  
  class runtime_error : public exception
  {
    string _M_msg;
  public:
    explicit runtime_error(const string& __arg);
    virtual const char* what() const noexcept;
  };
}
```

### Exception Safety Guarantees

1. **No-throw guarantee:** Never throws exceptions
2. **Strong guarantee:** Operation succeeds or has no effect
3. **Basic guarantee:** No resource leaks, object in valid state
4. **No guarantee:** May leak resources or corrupt state

**Example in vector:**
```cpp
void push_back(const value_type& __x)
{
  if (_M_finish != _M_end_of_storage)
  {
    // No-throw if constructor doesn't throw
    _Alloc_traits::construct(_M_impl, _M_finish, __x);
    ++_M_finish;
  }
  else
  {
    // Strong guarantee: either succeeds or vector unchanged
    _M_realloc_insert(end(), __x);
  }
}
```

---

## String Implementation

**Location:** `include/bits/basic_string.h`, `include/bits/basic_string.tcc`

### Small String Optimization (SSO)

```cpp
template<typename _CharT, typename _Traits, typename _Alloc>
class basic_string
{
  struct _Alloc_hider : allocator_type
  {
    pointer _M_p;  // Pointer to data
  };
  
  _Alloc_hider _M_dataplus;
  size_type _M_string_length;
  
  enum { _S_local_capacity = 15 / sizeof(_CharT) };
  
  union
  {
    _CharT _M_local_buf[_S_local_capacity + 1];  // Small string buffer
    size_type _M_allocated_capacity;              // Large string capacity
  };
  
  bool _M_is_local() const
  { return _M_dataplus._M_p == _M_local_data(); }
  
  pointer _M_local_data()
  { return pointer(_M_local_buf); }
};
```

**Optimization:** Strings ≤ 15 chars stored inline (no heap allocation)

---

## Filesystem Library

**Location:** `include/bits/fs_path.h`, `src/c++17/fs_ops.cc`

### path Class

```cpp
class path
{
  string_type _M_pathname;
  
public:
  path() noexcept = default;
  path(const path& __p) = default;
  path(path&& __p) noexcept = default;
  
  template<typename _Source>
  path(_Source const& __source);
  
  path& operator/=(const path& __p);
  
  path filename() const;
  path extension() const;
  path parent_path() const;
  
  bool is_absolute() const;
  bool is_relative() const;
};
```

**Usage:**
```cpp
std::filesystem::path p = "/usr/local/include/vector";
std::cout << p.filename() << '\n';      // "vector"
std::cout << p.parent_path() << '\n';   // "/usr/local/include"
std::cout << p.extension() << '\n';     // ""
```

---

## Summary

This document covered:
- Template metaprogramming techniques (SFINAE, tag dispatch, concepts)
- Type traits implementation
- Smart pointer internals
- Threading primitives
- Move semantics
- Exception handling
- String optimization
- Filesystem library

**Congratulations!** You now have a comprehensive understanding of libstdc++ internals. Continue exploring the source code and contributing to open-source projects!

