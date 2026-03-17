# Design a Distributed Lock Manager
**Difficulty:** Hard | **Companies:** Google, Amazon, Microsoft, Netflix

---

## Problem Statement

Design a distributed lock service for coordination across multiple nodes, supporting mutual exclusion, lock timeout, reentrant locks, and deadlock detection.

---

## Requirements

### Functional Requirements
1. Mutual exclusion guarantee
2. Lock timeout and auto-release (lease-based)
3. Fencing tokens to prevent stale operations
4. Reentrant lock support
5. Read-write locks
6. Lock fairness policies
7. Deadlock detection

### Non-Functional Requirements
1. High availability
2. Low latency acquisition
3. Consistency guarantees (safety)
4. Liveness (eventual progress)

---

## Class Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                  DistributedLockManager                         │
├─────────────────────────────────────────────────────────────────┤
│ - lockStore: LockStore                                          │
│ - leaseManager: LeaseManager                                    │
│ - fencingTokenGenerator: FencingTokenGenerator                  │
│ - deadlockDetector: DeadlockDetector                            │
│ - waitQueue: Map<String, Queue<LockWaiter>>                     │
├─────────────────────────────────────────────────────────────────┤
│ + acquire(lockId: String, timeout: Duration): LockHandle        │
│ + acquireRead(lockId: String, timeout: Duration): LockHandle    │
│ + acquireWrite(lockId: String, timeout: Duration): LockHandle   │
│ + release(handle: LockHandle): void                             │
│ + tryAcquire(lockId: String): Optional<LockHandle>              │
│ + extend(handle: LockHandle, duration: Duration): boolean       │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                         Lock                                    │
├─────────────────────────────────────────────────────────────────┤
│ - lockId: String                                                │
│ - owner: String                                                 │
│ - fencingToken: long                                            │
│ - acquiredAt: Instant                                           │
│ - expiresAt: Instant                                            │
│ - lockType: LockType                                            │
│ - reentrantCount: int                                           │
├─────────────────────────────────────────────────────────────────┤
│ + isExpired(): boolean                                          │
│ + isOwnedBy(clientId: String): boolean                          │
│ + extend(duration: Duration): void                              │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                      LockHandle                                 │
├─────────────────────────────────────────────────────────────────┤
│ - lockId: String                                                │
│ - fencingToken: long                                            │
│ - owner: String                                                 │
│ - expiresAt: Instant                                            │
├─────────────────────────────────────────────────────────────────┤
│ + getFencingToken(): long                                       │
│ + isValid(): boolean                                            │
└─────────────────────────────────────────────────────────────────┘
```

---

## Class Implementations

### 1. Lock and LockHandle
```java
public class Lock {
    private final String lockId;
    private String owner;
    private long fencingToken;
    private Instant acquiredAt;
    private Instant expiresAt;
    private LockType lockType;
    private int reentrantCount;
    private Set<String> readers;  // For read-write locks
    
    public Lock(String lockId) {
        this.lockId = lockId;
        this.readers = new HashSet<>();
        this.reentrantCount = 0;
    }
    
    public boolean isExpired() {
        return Instant.now().isAfter(expiresAt);
    }
    
    public boolean isOwnedBy(String clientId) {
        return owner != null && owner.equals(clientId);
    }
    
    public boolean canAcquireRead(String clientId) {
        if (lockType == LockType.WRITE && !isOwnedBy(clientId)) {
            return false;
        }
        return true;
    }
    
    public boolean canAcquireWrite(String clientId) {
        if (lockType == LockType.WRITE) {
            return isOwnedBy(clientId);  // Reentrant
        }
        if (lockType == LockType.READ) {
            // Can upgrade if only reader
            return readers.size() == 1 && readers.contains(clientId);
        }
        return true;
    }
    
    public void extend(Duration duration) {
        this.expiresAt = Instant.now().plus(duration);
    }
}

public class LockHandle implements AutoCloseable {
    private final String lockId;
    private final long fencingToken;
    private final String owner;
    private final Instant expiresAt;
    private final DistributedLockManager manager;
    private volatile boolean released;
    
    public long getFencingToken() {
        return fencingToken;
    }
    
    public boolean isValid() {
        return !released && Instant.now().isBefore(expiresAt);
    }
    
    @Override
    public void close() {
        if (!released) {
            manager.release(this);
            released = true;
        }
    }
}

public enum LockType {
    EXCLUSIVE, READ, WRITE
}
```

### 2. Distributed Lock Manager
```java
public class DistributedLockManager {
    private final LockStore lockStore;
    private final LeaseManager leaseManager;
    private final AtomicLong fencingTokenCounter;
    private final DeadlockDetector deadlockDetector;
    private final Map<String, Queue<LockWaiter>> waitQueues;
    private final String nodeId;
    
    public DistributedLockManager(LockStore store, String nodeId) {
        this.lockStore = store;
        this.nodeId = nodeId;
        this.fencingTokenCounter = new AtomicLong(System.currentTimeMillis());
        this.leaseManager = new LeaseManager(this);
        this.deadlockDetector = new DeadlockDetector();
        this.waitQueues = new ConcurrentHashMap<>();
    }
    
    public LockHandle acquire(String lockId, Duration timeout) throws LockException {
        return acquire(lockId, timeout, LockType.EXCLUSIVE);
    }
    
    public LockHandle acquire(String lockId, Duration timeout, LockType type) {
        String clientId = getClientId();
        Instant deadline = Instant.now().plus(timeout);
        
        // Check for potential deadlock
        if (deadlockDetector.wouldCauseDeadlock(clientId, lockId)) {
            throw new DeadlockException("Acquiring this lock would cause deadlock");
        }
        
        while (Instant.now().isBefore(deadline)) {
            Optional<LockHandle> handle = tryAcquireInternal(lockId, clientId, type);
            if (handle.isPresent()) {
                return handle.get();
            }
            
            // Wait in queue
            LockWaiter waiter = new LockWaiter(clientId, type);
            waitQueues.computeIfAbsent(lockId, k -> new LinkedBlockingQueue<>())
                .offer(waiter);
            
            deadlockDetector.addWaitingFor(clientId, lockId);
            
            try {
                Duration remaining = Duration.between(Instant.now(), deadline);
                waiter.await(remaining);
            } catch (InterruptedException e) {
                Thread.currentThread().interrupt();
                throw new LockException("Interrupted while waiting for lock");
            } finally {
                deadlockDetector.removeWaitingFor(clientId, lockId);
            }
        }
        
        throw new LockTimeoutException("Failed to acquire lock within timeout");
    }
    
    private Optional<LockHandle> tryAcquireInternal(String lockId, String clientId, 
                                                     LockType type) {
        return lockStore.executeAtomically(lockId, lock -> {
            if (lock == null || lock.isExpired()) {
                // Lock is free
                lock = new Lock(lockId);
            }
            
            if (type == LockType.READ && !lock.canAcquireRead(clientId)) {
                return Optional.empty();
            }
            if (type == LockType.WRITE && !lock.canAcquireWrite(clientId)) {
                return Optional.empty();
            }
            
            // Handle reentrant acquisition
            if (lock.isOwnedBy(clientId)) {
                lock.incrementReentrantCount();
            } else {
                long token = fencingTokenCounter.incrementAndGet();
                lock.setOwner(clientId);
                lock.setFencingToken(token);
                lock.setAcquiredAt(Instant.now());
                lock.setLockType(type);
            }
            
            Duration leaseDuration = Duration.ofSeconds(30);
            lock.extend(leaseDuration);
            
            lockStore.save(lock);
            leaseManager.scheduleLease(lock);
            
            return Optional.of(new LockHandle(
                lockId, lock.getFencingToken(), clientId, 
                lock.getExpiresAt(), this
            ));
        });
    }
    
    public void release(LockHandle handle) {
        lockStore.executeAtomically(handle.getLockId(), lock -> {
            if (lock == null || !lock.isOwnedBy(handle.getOwner())) {
                return null;
            }
            
            if (lock.getFencingToken() != handle.getFencingToken()) {
                // Stale handle - lock was already released and reacquired
                return null;
            }
            
            if (lock.getReentrantCount() > 1) {
                lock.decrementReentrantCount();
            } else {
                lockStore.delete(handle.getLockId());
                notifyWaiters(handle.getLockId());
            }
            
            return null;
        });
    }
}
```

### 3. Deadlock Detector
```java
public class DeadlockDetector {
    private final Map<String, String> waitingFor;  // client -> lockId
    private final Map<String, Set<String>> heldBy;  // lockId -> clients
    
    public DeadlockDetector() {
        this.waitingFor = new ConcurrentHashMap<>();
        this.heldBy = new ConcurrentHashMap<>();
    }
    
    public boolean wouldCauseDeadlock(String clientId, String lockId) {
        // DFS to detect cycle
        Set<String> visited = new HashSet<>();
        return hasCycle(clientId, lockId, visited);
    }
    
    private boolean hasCycle(String startClient, String targetLock, Set<String> visited) {
        Set<String> holders = heldBy.get(targetLock);
        if (holders == null || holders.isEmpty()) {
            return false;
        }
        
        for (String holder : holders) {
            if (holder.equals(startClient)) {
                return true;  // Cycle detected
            }
            
            if (visited.contains(holder)) {
                continue;
            }
            visited.add(holder);
            
            String holderWaiting = waitingFor.get(holder);
            if (holderWaiting != null && hasCycle(startClient, holderWaiting, visited)) {
                return true;
            }
        }
        
        return false;
    }
    
    public void addWaitingFor(String clientId, String lockId) {
        waitingFor.put(clientId, lockId);
    }
    
    public void removeWaitingFor(String clientId, String lockId) {
        waitingFor.remove(clientId);
    }
    
    public void addHolder(String lockId, String clientId) {
        heldBy.computeIfAbsent(lockId, k -> ConcurrentHashMap.newKeySet())
            .add(clientId);
    }
    
    public void removeHolder(String lockId, String clientId) {
        Set<String> holders = heldBy.get(lockId);
        if (holders != null) {
            holders.remove(clientId);
        }
    }
}
```

