## Placement New in C++

- Allocation and construction are different.
- A memory allocator is simply supposed to return uninitialized bits of memory.
- It is not supposed to produce “objects”.
- Constructing the object is role of the constructor, which runs after the
memory allocator.

```cpp
// assume we have a allocator object pool
Pool pool;
void* raw = pool.alloc(sizeof(Foo));
Foo* p = new(raw) Foo(); 

// the above is equivalent to
Foo* p = new Foo();
```
- It is used to place an object at a particular location in memory. This is 
done by supplying the place as a pointer parameter to the new part of a new 
expression:

```cpp
#include <new>        // Must #include this to use "placement new"
int main ()
{
  char memory[sizeof(Fred)];     // creating memory big enough to hold fred
  void* place = memory;          // unnecessary step
  Fred* f = new(place) Fred();   // Contructing the object (call Fred::Fred())
  // The pointers f and place will be equal
  
  // Remark: 
  // We are taking sole responsibility that the pointer we pass to the 
  // “placement new” operator points to a region of memory that is big enough 
  // and is properly aligned for the object type that you’re creating.

  // Neither the compiler nor the run-time system will make any attempt to check 
  // whether we did this right.

  f->~Fred();
  // We need to explicitly call the destructor
}
```

- We may want to do this for optimization when we need to construct multiple 
instances of an object, and it is faster not to re-allocate memory each time 
we need a new instance. Instead, it might be more efficient to perform a 
single allocation for a chunk of memory that can hold multiple objects, 
even though we don't want to use all of it at once.

### How std::vector uses Placement New

- Take containers like unordered_map, vector, or deque. These all allocate 
more memory than is minimally required for the elements you've inserted so 
far to avoid requiring a heap allocation for every single insertion.

```cpp
vector<Foo> vec;

// Allocate memory for a thousand Foos:
vec.reserve(1000);
```
... that doesn't actually construct a thousand Foos. It simply allocates/reserves
memory for them. If vector did not use placement new here, it would be 
default-constructing Foos all over the place as well as having to invoke their 
destructors even for elements you never even inserted in the first place.

Vector Example: [Link](https://medium.com/@dgodfrey206/c-placement-new-1298ccbb076e)
