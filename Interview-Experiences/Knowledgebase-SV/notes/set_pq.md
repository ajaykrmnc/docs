## Set vs Priority Queue

### Priority Queue
- Only gives access to one element in sorted order: the highest priority 
element. When we remove it, we get the next highest priority element.
- It is backed by a heap (implemented by a vector)
- In a heap `P < L` and `P < R` (Parent, Left, Right)
- The highest priority element is at top of tree (or front of vector)
- O(1) access to top element
- Deletion is `O(logn)` (We replace the top of tree with the extreme element
and then perform swapping to maintain heap property)
- Insertion is `O(logn)` (We put new element at the new extreme and then perform
swapping to maintain heap property)
- One point to note, is that operations in PQ involve a lot of swapping of 
elements.


### Set
- A set allows you full access in sorted order.
- We can do: find two elements somewhere in the middle of the set, then 
traverse in order from one to the other.
- Insert any element `O(log n)` and the constant factor is greater than in PQ.
- Much more operations (LB, UB, element lookup, iteration, etc).
- Backed by self balancing BSTs.
- In a binary tree `L < P < R`.
- Insert and erase operations slightly slower than PQ because `std::set` makes 
many memory allocations. Every element of `std::set` is stored at its own 
allocation.
- Good thing is it only involves pointer swapping. 