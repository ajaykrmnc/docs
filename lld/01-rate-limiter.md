# Design a Rate Limiter
**Difficulty:** Hard | **Companies:** Google, Stripe, Cloudflare, Amazon

---

## Problem Statement

Design a rate limiter that can limit the number of requests a client can make to an API within a time window. The system should support multiple rate limiting algorithms and work in a distributed environment.

---

## Requirements

### Functional Requirements
1. Limit requests based on user ID, IP address, or API key
2. Support multiple algorithms: Token Bucket, Sliding Window, Leaky Bucket, Fixed Window
3. Return appropriate headers (X-RateLimit-Remaining, X-RateLimit-Reset)
4. Support different limits for different API endpoints
5. Allow dynamic rule updates without system restart

### Non-Functional Requirements
1. Low latency (< 1ms overhead)
2. Highly available - system should work even if rate limiter fails
3. Distributed rate limiting across multiple servers
4. Accurate counting in distributed environment

---

## Core Classes

```
┌─────────────────────────────────────────────────────────────────┐
│                        RateLimiter                              │
├─────────────────────────────────────────────────────────────────┤
│ - rules: Map<String, RateLimitRule>                             │
│ - strategy: RateLimitStrategy                                   │
│ - counter: DistributedCounter                                   │
├─────────────────────────────────────────────────────────────────┤
│ + isAllowed(clientId: String, endpoint: String): RateLimitResult│
│ + addRule(rule: RateLimitRule): void                            │
│ + removeRule(ruleId: String): void                              │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                    <<interface>>                                │
│                   RateLimitStrategy                             │
├─────────────────────────────────────────────────────────────────┤
│ + tryAcquire(key: String, limit: int, window: Duration): bool   │
│ + getRemainingTokens(key: String): int                          │
│ + getResetTime(key: String): Instant                            │
└─────────────────────────────────────────────────────────────────┘
          △
          │
    ┌─────┴─────┬──────────────┬─────────────────┐
    │           │              │                 │
┌───┴───┐  ┌────┴────┐  ┌──────┴──────┐  ┌───────┴───────┐
│Token  │  │Sliding  │  │   Leaky     │  │    Fixed      │
│Bucket │  │Window   │  │   Bucket    │  │    Window     │
└───────┘  └─────────┘  └─────────────┘  └───────────────┘
```

---

## Class Definitions

### 1. RateLimitRule
```java
public class RateLimitRule {
    private String ruleId;
    private String endpoint;           // API endpoint pattern
    private int maxRequests;           // Maximum requests allowed
    private Duration timeWindow;       // Time window for the limit
    private RateLimitType type;        // USER, IP, API_KEY
    private int priority;              // Higher priority rules take precedence
    
    // Getters and Builder pattern
}

public enum RateLimitType {
    USER, IP_ADDRESS, API_KEY, GLOBAL
}
```

### 2. RateLimitResult
```java
public class RateLimitResult {
    private boolean allowed;
    private int remainingTokens;
    private Instant resetTime;
    private Duration retryAfter;
    
    public static RateLimitResult allowed(int remaining, Instant reset) {
        return new RateLimitResult(true, remaining, reset, null);
    }
    
    public static RateLimitResult blocked(Instant reset, Duration retryAfter) {
        return new RateLimitResult(false, 0, reset, retryAfter);
    }
}
```

### 3. Token Bucket Strategy
```java
public class TokenBucketStrategy implements RateLimitStrategy {
    private final DistributedCounter counter;
    private final int bucketCapacity;
    private final int refillRate;        // tokens per second
    private final Duration refillInterval;
    
    @Override
    public boolean tryAcquire(String key, int limit, Duration window) {
        TokenBucket bucket = getOrCreateBucket(key, limit);
        bucket.refill();
        
        if (bucket.getTokens() >= 1) {
            bucket.consume(1);
            return true;
        }
        return false;
    }
    
    private TokenBucket getOrCreateBucket(String key, int capacity) {
        return counter.computeIfAbsent(key, k -> new TokenBucket(capacity));
    }
}

class TokenBucket {
    private double tokens;
    private long lastRefillTimestamp;
    private final int capacity;
    private final double refillRate;
    
    public synchronized void refill() {
        long now = System.currentTimeMillis();
        double tokensToAdd = (now - lastRefillTimestamp) * refillRate / 1000.0;
        tokens = Math.min(capacity, tokens + tokensToAdd);
        lastRefillTimestamp = now;
    }
    
    public synchronized boolean consume(int count) {
        if (tokens >= count) {
            tokens -= count;
            return true;
        }
        return false;
    }
}
```

### 4. Sliding Window Strategy
```java
public class SlidingWindowStrategy implements RateLimitStrategy {
    private final DistributedCounter counter;
    
    @Override
    public boolean tryAcquire(String key, int limit, Duration window) {
        long currentWindow = getCurrentWindowStart(window);
        long previousWindow = currentWindow - window.toMillis();
        
        // Get counts from current and previous windows
        long currentCount = counter.get(key + ":" + currentWindow);
        long previousCount = counter.get(key + ":" + previousWindow);
        
        // Calculate weighted count based on time position in current window
        double windowProgress = getWindowProgress(currentWindow, window);
        double weightedCount = previousCount * (1 - windowProgress) + currentCount;
        
        if (weightedCount < limit) {
            counter.increment(key + ":" + currentWindow);
            return true;
        }
        return false;
    }
    
    private double getWindowProgress(long windowStart, Duration window) {
        long now = System.currentTimeMillis();
        return (double)(now - windowStart) / window.toMillis();
    }
}
```

### 5. Distributed Counter (Redis-based)
```java
public class RedisDistributedCounter implements DistributedCounter {
    private final RedisClient redis;
    
    @Override
    public long increment(String key) {
        return redis.incr(key);
    }
    
    @Override
    public long incrementWithExpiry(String key, Duration ttl) {
        // Lua script for atomic increment with expiry
        String script = """
            local current = redis.call('INCR', KEYS[1])
            if current == 1 then
                redis.call('PEXPIRE', KEYS[1], ARGV[1])
            end
            return current
        """;
        return redis.eval(script, key, ttl.toMillis());
    }
    
    @Override
    public long get(String key) {
        String value = redis.get(key);
        return value != null ? Long.parseLong(value) : 0;
    }
}
```

