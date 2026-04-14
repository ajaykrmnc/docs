## Atomics

To implement locks, we need hardware support for atomic instructions. This can't
alone be done by software.

### CMPXCHG (Compare-And-Exchange/Swap)
Atomically compares the value in memory to a register. If the values are equal, 
it writes a new value; otherwise, it leaves the memory unchanged and sets flags
indicating failure.

`CMPXCHG [mem], reg`

```cpp
bool CAS(int* addr, int expected, int new_val) {
    if (*addr == expected) {
        *addr = new_val; // update the memory with new_val
        return true;     // return success
    } else {
        return false;    // return failure
    }
}
```

### XCHG (Exchange)
Atomically swaps the contents of a register and a memory location.

`XCHG reg, [mem]`

### LOCK Prefix
In x86, certain instructions can be prefixed with the LOCK instruction to make 
them atomic, meaning the instruction will operate atomically on the memory location.

Applies to instructions like ADD, SUB, INC, DEC, XOR, OR, AND, etc. 
These operations can then modify memory atomically.

`LOCK ADD [mem], reg`

### Simple spinlock using CAS
```cpp
typedef int spinlock_t; // 0 = unlocked, 1 = locked

void spinlock_init(spinlock_t* lock) {
    *lock = 0; // Initialize the lock as unlocked
}

void spinlock_acquire(spinlock_t* lock) {
    while (!CAS(lock, 0, 1)) {
        // Spin until we successfully acquire the lock
    }
}

void spinlock_release(spinlock_t* lock) {
    *lock = 0; // Release the lock by setting it to unlocked
}
```
```assembly
spinlock_acquire:
    mov eax, 0          ; expected value (unlocked)
acquire_retry:
    mov ebx, 1          ; new value (locked)
    lock cmpxchg [lock], ebx ; compare and swap
    jne acquire_retry   ; if lock was not acquired, retry
    ret

spinlock_release:
    mov [lock], 0       ; set lock to unlocked
    ret
```

More on different types of spinlocks can be found 
[here](https://github.com/Shivam5022/Spin-Locks-and-Contention) in my second 
assignment of COL818.

### How hardware supports atomic instructions:

<mark>The simplest CAS implementations (and the easiest mental model) will simply freeze the local cache coherence protocol state machine after the load part of the CAS brings the relevant cache line into the nearest (e.g. L1) cache in exclusive mode, and will unfreeze it after the (optional) store completes. This, by definition, makes the CAS operation as a whole atomic with relation to any other participant in the cache coherence protocol. </mark>

