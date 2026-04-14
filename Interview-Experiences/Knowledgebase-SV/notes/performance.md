## Follow these guidelines

1. No unnecessary work
    - No extra copying
    - No extra allocations

2. Use all your computing power
    - Use all the cores available
    - SIMD

3. Avoid waits and stalls
    - Lockless Data Structures
    - Async APIs
    - Job Systems

4. Use Hardware efficiently
    - Cache friendly
    - Well predictable code

5. OS Level Efficiency

## Efficient C++

### Use constexpr wherever possible
Computation already done at compile time, saving us time during runtime. 

### Make Variables `const`
Knowing a variable is const allows the compiler to perform various 
optimisations. 

For example:
```cpp
{
    const float sum = std:: accumulate(data.begin(), data.end(),0.01);
    for (auto& num : data) {
        num -= sum / data.size():
    }
    return data;
}

// can be optimised to below code by compiler since sum is const

{
    const float sum = std:: accumulate(data.begin(), data.end(),0.01);
    const float __mean = sum / data.size(): // this expression is loop invariant
    for (auto& num : data) {
        num -= __mean; // no expensive division inside loop now
    }
    return data;
}
```

Also it can help compiler to do this optimization:

```cpp
bool condition = getBool();
for (int i {}; i < n; i++) {
    if (condition) {
        A(i);
    } else {
        B(i);
    }
}

// if variable was declared const:

const bool condition = getBool();
if (condition()) {
    for (int i = 0; i < n; i++) {
        A(i);
    }
} else {
    for (int i = 0; i < n; i++) {
        B(i);
    }
}
```
Here we have reduced branching. In earlier case when bool was not const, compiler
may be afraid that functions A or B, might change its value, thus preventing the
opportunity to optimise.

### Noexcept all the things
void f(); `could throw exception`

void f() noexcept; `WILL NEVER throw an exception`

In the functions call stack, the compiler can now not do exception handling, 
which reduces some overhead.

### Use static for internal linkage
The functions which are to be used only in this source file should be marked
static. It is another hint to the compiler to inline it, apart from using the
inline keyword.

### Use `[[likely]]` and `[[unlikely]]` in conditionals
Better branch predicting, if the conditionals are marked `[[likely]]` or 
`[[unlikely]]`.

### Avoid Copying in str. bindings

`auto [first person, age] = *map. begin();` is bad

`const auto& [first person, age] = *map.begin();` use this instead

### Cache Friendly

```plaintext
CONTIGUOUS          SCATTERED

std::array          std::list
std::vector         std::set
std::deque          std::unordered_set
std::flat_map       std::map
std::flat_set       std::unordered_map
```

Also while designing classes, we have certain member varibles which will be 
used very rarely, for example debugging info.

So instead of having an object of `debugInfo` inside our class, we can instead 
keep a `unique_ptr` to it. So that everytime our class' object is fetched into
cache, large non-important things are not pre-fetched (size of pointer will be
small, and small non-important thing will be feteched here.)

### False Sharing
Data on same cache line, being accessed by different threads.

Use `alignas` to prevent this.

### Avoid Indirect Calls
Virtual function call are indirect calls, as they require `vtable` lookup.
