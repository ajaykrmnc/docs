# Design a URL Shortener
**Difficulty:** Medium-Hard | **Companies:** All Tier-1 (Google, Meta, Amazon)

---

## Problem Statement

Design a URL shortening service with custom aliases, expiration, click analytics, and high availability.

---

## Requirements

### Functional Requirements
1. Generate unique short URLs (base62 encoding)
2. Custom alias support with collision handling
3. URL expiration time support
4. Click analytics (geolocation, referrer, device, timestamp)
5. Rate limiting per user
6. Bulk URL shortening API
7. QR code generation

### Non-Functional Requirements
1. High availability (99.99%)
2. Low latency redirects (< 10ms)
3. Handle 100M+ URLs
4. Eventually consistent analytics

---

## Class Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                      URLShortener                               │
├─────────────────────────────────────────────────────────────────┤
│ - urlStore: URLMappingStore                                     │
│ - codeGenerator: ShortCodeGenerator                             │
│ - analytics: AnalyticsCollector                                 │
│ - rateLimiter: RateLimiter                                      │
│ - cache: URLCache                                               │
├─────────────────────────────────────────────────────────────────┤
│ + shorten(request: ShortenRequest): ShortURL                    │
│ + resolve(shortCode: String): String                            │
│ + getAnalytics(shortCode: String): URLAnalytics                 │
│ + bulkShorten(requests: List<ShortenRequest>): List<ShortURL>   │
│ + delete(shortCode: String, userId: String): boolean            │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                       URLMapping                                │
├─────────────────────────────────────────────────────────────────┤
│ - shortCode: String                                             │
│ - originalUrl: String                                           │
│ - userId: String                                                │
│ - createdAt: Instant                                            │
│ - expiresAt: Instant                                            │
│ - customAlias: boolean                                          │
│ - clickCount: AtomicLong                                        │
├─────────────────────────────────────────────────────────────────┤
│ + isExpired(): boolean                                          │
│ + incrementClicks(): void                                       │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                    ShortCodeGenerator                           │
├─────────────────────────────────────────────────────────────────┤
│ - counter: DistributedCounter                                   │
│ - nodeId: int                                                   │
├─────────────────────────────────────────────────────────────────┤
│ + generate(): String                                            │
│ + encode(id: long): String                                      │
│ + decode(code: String): long                                    │
└─────────────────────────────────────────────────────────────────┘
```

---

## Class Implementations

### 1. Short Code Generator (Base62)
```java
public class ShortCodeGenerator {
    private static final String BASE62 = 
        "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz";
    private static final int CODE_LENGTH = 7;
    
    private final DistributedCounter counter;
    private final int nodeId;
    private final int nodeBits;
    
    public ShortCodeGenerator(DistributedCounter counter, int nodeId) {
        this.counter = counter;
        this.nodeId = nodeId;
        this.nodeBits = 10;  // Support 1024 nodes
    }
    
    public String generate() {
        // Snowflake-like ID: timestamp + nodeId + sequence
        long id = generateUniqueId();
        return encode(id);
    }
    
    private long generateUniqueId() {
        long timestamp = System.currentTimeMillis();
        long sequence = counter.getAndIncrement() & 0xFFF;  // 12 bits
        
        return (timestamp << 22) | ((long) nodeId << 12) | sequence;
    }
    
    public String encode(long num) {
        StringBuilder sb = new StringBuilder();
        while (num > 0) {
            sb.append(BASE62.charAt((int) (num % 62)));
            num /= 62;
        }
        
        // Pad to minimum length
        while (sb.length() < CODE_LENGTH) {
            sb.append('0');
        }
        
        return sb.reverse().toString();
    }
    
    public long decode(String code) {
        long num = 0;
        for (char c : code.toCharArray()) {
            num = num * 62 + BASE62.indexOf(c);
        }
        return num;
    }
}
```

### 2. URL Mapping and Store
```java
public class URLMapping {
    private final String shortCode;
    private final String originalUrl;
    private final String userId;
    private final Instant createdAt;
    private final Instant expiresAt;
    private final boolean customAlias;
    private final AtomicLong clickCount;
    
    public URLMapping(String shortCode, String originalUrl, String userId,
                      Duration ttl, boolean customAlias) {
        this.shortCode = shortCode;
        this.originalUrl = originalUrl;
        this.userId = userId;
        this.createdAt = Instant.now();
        this.expiresAt = ttl != null ? createdAt.plus(ttl) : null;
        this.customAlias = customAlias;
        this.clickCount = new AtomicLong(0);
    }
    
    public boolean isExpired() {
        return expiresAt != null && Instant.now().isAfter(expiresAt);
    }
    
    public void incrementClicks() {
        clickCount.incrementAndGet();
    }
}

public interface URLMappingStore {
    void save(URLMapping mapping);
    Optional<URLMapping> findByShortCode(String shortCode);
    boolean exists(String shortCode);
    void delete(String shortCode);
    List<URLMapping> findByUserId(String userId, int limit, int offset);
}
```

### 3. Analytics Collector
```java
public class ClickEvent {
    private final String shortCode;
    private final Instant timestamp;
    private final String ipAddress;
    private final String userAgent;
    private final String referrer;
    private final GeoLocation location;
    private final DeviceInfo device;
    
    public static ClickEvent from(String shortCode, HttpRequest request) {
        return new ClickEvent(
            shortCode,
            Instant.now(),
            request.getRemoteAddress(),
            request.getHeader("User-Agent"),
            request.getHeader("Referer"),
            GeoLocation.fromIp(request.getRemoteAddress()),
            DeviceInfo.parse(request.getHeader("User-Agent"))
        );
    }
}

public class AnalyticsCollector {
    private final BlockingQueue<ClickEvent> eventQueue;
    private final ClickEventStore eventStore;
    private final ExecutorService workers;
    
    public AnalyticsCollector(ClickEventStore store, int numWorkers) {
        this.eventQueue = new LinkedBlockingQueue<>(100000);
        this.eventStore = store;
        this.workers = Executors.newFixedThreadPool(numWorkers);
        startWorkers(numWorkers);
    }
    
    public void recordClick(ClickEvent event) {
        if (!eventQueue.offer(event)) {
            // Queue full - sample or drop
            handleOverflow(event);
        }
    }
    
    public URLAnalytics getAnalytics(String shortCode, TimeRange range) {
        List<ClickEvent> events = eventStore.query(shortCode, range);
        
        return URLAnalytics.builder()
            .totalClicks(events.size())
            .uniqueVisitors(countUnique(events, ClickEvent::getIpAddress))
            .clicksByCountry(groupBy(events, e -> e.getLocation().getCountry()))
            .clicksByDevice(groupBy(events, e -> e.getDevice().getType()))
            .clicksByReferrer(groupBy(events, ClickEvent::getReferrer))
            .clicksOverTime(groupByTime(events, range.getGranularity()))
            .build();
    }
}
```

### 4. URL Shortener Service
```java
public class URLShortener {
    private final URLMappingStore urlStore;
    private final ShortCodeGenerator codeGenerator;
    private final AnalyticsCollector analytics;
    private final RateLimiter rateLimiter;
    private final Cache<String, URLMapping> cache;
    private final URLValidator validator;
    
    public ShortURL shorten(ShortenRequest request) {
        // Rate limiting
        if (!rateLimiter.tryAcquire(request.getUserId())) {
            throw new RateLimitException("Rate limit exceeded");
        }
        
        // Validate URL
        if (!validator.isValid(request.getUrl())) {
            throw new InvalidURLException("Invalid URL format");
        }
        
        String shortCode;
        if (request.getCustomAlias() != null) {
            shortCode = request.getCustomAlias();
            if (urlStore.exists(shortCode)) {
                throw new AliasConflictException("Alias already taken");
            }
        } else {
            shortCode = generateUniqueCode();
        }
        
        URLMapping mapping = new URLMapping(
            shortCode,
            request.getUrl(),
            request.getUserId(),
            request.getTtl(),
            request.getCustomAlias() != null
        );
        
        urlStore.save(mapping);
        cache.put(shortCode, mapping);
        
        return new ShortURL(shortCode, buildFullUrl(shortCode), mapping.getExpiresAt());
    }
    
    public String resolve(String shortCode, HttpRequest request) {
        URLMapping mapping = cache.get(shortCode);
        if (mapping == null) {
            mapping = urlStore.findByShortCode(shortCode)
                .orElseThrow(() -> new URLNotFoundException("URL not found"));
            cache.put(shortCode, mapping);
        }
        
        if (mapping.isExpired()) {
            throw new URLExpiredException("URL has expired");
        }
        
        // Record analytics asynchronously
        analytics.recordClick(ClickEvent.from(shortCode, request));
        mapping.incrementClicks();
        
        return mapping.getOriginalUrl();
    }
    
    private String generateUniqueCode() {
        for (int i = 0; i < 3; i++) {
            String code = codeGenerator.generate();
            if (!urlStore.exists(code)) {
                return code;
            }
        }
        throw new CodeGenerationException("Failed to generate unique code");
    }
}
```

