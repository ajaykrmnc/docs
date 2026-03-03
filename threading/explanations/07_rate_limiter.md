# Problem 7: Rate Limiter

## 🎯 Problem Statement
Implement a rate limiter that allows at most N requests per second. Support multiple algorithms: Token Bucket, Sliding Window, and Leaky Bucket.

## 🏢 Companies
**Glean** (API rate limiting), **Databricks** (resource management)

## 🔑 Core Principles

### 1. Token Bucket Algorithm

```
┌────────────────────────────────────────────┐
│              TOKEN BUCKET                   │
│                                             │
│    Tokens added at rate R per second        │
│              ↓ ↓ ↓                          │
│         ┌─────────────┐                     │
│         │ ○ ○ ○ ○ ○   │ ← Capacity C        │
│         │   BUCKET    │                     │
│         └──────┬──────┘                     │
│                │                            │
│    Request consumes 1 token                 │
│                ↓                            │
│         [If tokens > 0: ALLOW]              │
│         [If tokens = 0: DENY]               │
└────────────────────────────────────────────┘

Properties:
- Allows BURSTS up to capacity
- Smooth rate limiting over time
- Simple and memory efficient
```

**Formula:**
```
tokens = min(capacity, tokens + elapsed_time × rate)
```

### 2. Sliding Window Algorithm

```
TIME WINDOW (1 second)
├────────────────────────────────────────┤
│ R1   R2     R3   R4   R5   │   NOW    │
│ ↓    ↓      ↓    ↓    ↓    │    ↓     │
├─●────●──────●────●────●────┼──────────┤
│      │                     │          │
│   ←──┴─ These count ──────→│          │
│                            │          │
│ Requests in window: 5      │          │
│ Limit: 5                   │          │
│ New request: DENIED ❌     │          │
└────────────────────────────┴──────────┘

As time moves:
├───────────────────────────────────────────┤
│    R2     R3   R4   R5   │   NOW    R6  │
│    ↓      ↓    ↓    ↓    │    ↓      ↓  │
│  ──●──────●────●────●────┼──────────●── │
│    │                     │              │
│ R1 falls out of window   │              │
│ Requests in window: 4    │  ALLOWED ✓  │
└──────────────────────────┴──────────────┘
```

### 3. Leaky Bucket Algorithm

```
┌────────────────────────────────────────────┐
│              LEAKY BUCKET                   │
│                                             │
│    Requests fill the bucket                 │
│              ↓ ↓ ↓                          │
│         ┌─────────────┐                     │
│         │ ■ ■ ■ ■     │ ← If full, DENY    │
│         │   BUCKET    │                     │
│         └──────┬──────┘                     │
│                │ drip drip                  │
│                ↓                            │
│         Leaks at constant rate R            │
│                                             │
└────────────────────────────────────────────┘

Properties:
- CONSTANT output rate (no bursts!)
- Good for smoothing traffic
- Used in network traffic shaping
```

## 📊 Algorithm Comparison

| Algorithm | Burst Handling | Precision | Memory | Use Case |
|-----------|---------------|-----------|--------|----------|
| **Token Bucket** | Allows bursts | Good | O(1) | API rate limiting |
| **Sliding Window** | No bursts | Exact | O(n) | Strict limiting |
| **Leaky Bucket** | Smooths bursts | Good | O(1) | Traffic shaping |
| **Fixed Window** | Edge bursts* | Poor | O(1) | Simple cases |

*Fixed window allows 2× burst at window boundaries

## 🧠 Key Insights

### Token Bucket vs Leaky Bucket
```
TOKEN BUCKET:                  LEAKY BUCKET:
Input  → [Bucket] → Output    Input  → [Bucket] → Output
         Variable              Fixed burst       Constant
         rate out              allowed           rate out

Use for: Allowing bursts      Use for: Smooth output
```

### Thread Safety
```cpp
class TokenBucket {
    std::mutex mutex_;
    double tokens_;
    
    bool acquire() {
        std::lock_guard<std::mutex> lock(mutex_);
        refill();  // Must be inside lock!
        if (tokens_ >= 1) {
            tokens_ -= 1;
            return true;
        }
        return false;
    }
};
```

## 💻 Implementation Tips

### Token Bucket (Recommended for APIs)
```python
def acquire(self):
    with self.lock:
        now = time.time()
        # Refill tokens based on elapsed time
        self.tokens = min(
            self.capacity,
            self.tokens + (now - self.last_refill) * self.rate
        )
        self.last_refill = now
        
        if self.tokens >= 1:
            self.tokens -= 1
            return True
        return False
```

### Distributed Rate Limiting
```
For distributed systems, use:
- Redis with Lua scripts (atomic operations)
- Centralized token bucket service
- Approximate algorithms (less coordination)
```

## ⚠️ Common Mistakes

| Mistake | Problem | Fix |
|---------|---------|-----|
| Not handling clock drift | Inconsistent limiting | Use monotonic clock |
| Race in refill | Over-granting tokens | Lock during refill |
| Integer overflow | Incorrect token count | Use floating point |
| No distributed coordination | Per-node limits only | Use Redis/central store |

