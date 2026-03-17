# Design an API Gateway
**Difficulty:** Hard | **Companies:** Netflix, Amazon, Google, Microsoft

---

## Problem Statement

Design an API Gateway with dynamic routing, middleware support, authentication, circuit breakers, and request aggregation.

---

## Requirements

### Functional Requirements
1. Dynamic route matching with path parameters
2. Request/Response transformation
3. Authentication and authorization middleware
4. Circuit breaker pattern for downstream services
5. Rate limiting per client/route
6. Request aggregation from multiple services
7. API versioning support
8. Load balancing across service instances

### Non-Functional Requirements
1. Low latency overhead (< 10ms)
2. High throughput
3. Fault tolerance
4. Real-time configuration updates

---

## Class Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                        APIGateway                               │
├─────────────────────────────────────────────────────────────────┤
│ - router: Router                                                │
│ - middlewareChain: MiddlewareChain                              │
│ - serviceRegistry: ServiceRegistry                              │
│ - circuitBreakerRegistry: CircuitBreakerRegistry                │
│ - loadBalancer: LoadBalancer                                    │
├─────────────────────────────────────────────────────────────────┤
│ + handle(request: Request): Response                            │
│ + registerRoute(route: Route): void                             │
│ + addMiddleware(middleware: Middleware): void                   │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                          Route                                  │
├─────────────────────────────────────────────────────────────────┤
│ - id: String                                                    │
│ - pathPattern: String                                           │
│ - methods: Set<HttpMethod>                                      │
│ - targetService: String                                         │
│ - targetPath: String                                            │
│ - middlewares: List<Middleware>                                 │
│ - timeout: Duration                                             │
│ - retryPolicy: RetryPolicy                                      │
├─────────────────────────────────────────────────────────────────┤
│ + matches(request: Request): RouteMatch                         │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                  <<interface>> Middleware                       │
├─────────────────────────────────────────────────────────────────┤
│ + process(ctx: RequestContext, next: MiddlewareChain): Response │
│ + getOrder(): int                                               │
└─────────────────────────────────────────────────────────────────┘
         △
    ┌────┴────┬──────────┬────────────┬─────────────┐
    │         │          │            │             │
  Auth     RateLimit  Logging    Transform   CircuitBreaker
```

---

## Class Implementations

### 1. Request and Response
```java
public class Request {
    private final String method;
    private final String path;
    private final Map<String, String> headers;
    private final Map<String, String> queryParams;
    private final Map<String, String> pathParams;
    private final byte[] body;
    private final String clientId;
    private final Instant timestamp;
    
    public Request withPathParams(Map<String, String> params) {
        return new Request(method, path, headers, queryParams, params, body, clientId);
    }
}

public class Response {
    private final int statusCode;
    private final Map<String, String> headers;
    private final byte[] body;
    
    public static Response ok(byte[] body) {
        return new Response(200, Map.of(), body);
    }
    
    public static Response error(int status, String message) {
        return new Response(status, Map.of(), message.getBytes());
    }
}

public class RequestContext {
    private final Request request;
    private final Route route;
    private final Map<String, Object> attributes;
    private Principal principal;
    
    public void setAttribute(String key, Object value) {
        attributes.put(key, value);
    }
    
    public <T> T getAttribute(String key, Class<T> type) {
        return type.cast(attributes.get(key));
    }
}
```

### 2. Router Implementation
```java
public class Router {
    private final List<Route> routes;
    private final TrieNode pathTrie;
    
    public RouteMatch match(Request request) {
        for (Route route : routes) {
            RouteMatch match = route.matches(request);
            if (match.isMatched()) {
                return match;
            }
        }
        return RouteMatch.notFound();
    }
}

public class Route {
    private final String id;
    private final PathPattern pathPattern;
    private final Set<String> methods;
    private final String targetService;
    private final String targetPath;
    private final List<Middleware> middlewares;
    private final Duration timeout;
    
    public RouteMatch matches(Request request) {
        if (!methods.contains(request.getMethod())) {
            return RouteMatch.notMatched();
        }
        
        Map<String, String> pathParams = pathPattern.match(request.getPath());
        if (pathParams == null) {
            return RouteMatch.notMatched();
        }
        
        return new RouteMatch(this, pathParams);
    }
}

public class PathPattern {
    private final String pattern;  // e.g., "/users/{userId}/orders/{orderId}"
    private final List<PathSegment> segments;
    
    public Map<String, String> match(String path) {
        String[] parts = path.split("/");
        if (parts.length != segments.size()) return null;
        
        Map<String, String> params = new HashMap<>();
        for (int i = 0; i < segments.size(); i++) {
            PathSegment segment = segments.get(i);
            if (segment.isVariable()) {
                params.put(segment.getName(), parts[i]);
            } else if (!segment.getValue().equals(parts[i])) {
                return null;
            }
        }
        return params;
    }
}
```

### 3. Middleware Chain
```java
public class MiddlewareChain {
    private final List<Middleware> middlewares;
    private final int index;
    private final RequestHandler finalHandler;
    
    public Response proceed(RequestContext ctx) {
        if (index >= middlewares.size()) {
            return finalHandler.handle(ctx);
        }
        
        Middleware current = middlewares.get(index);
        MiddlewareChain next = new MiddlewareChain(middlewares, index + 1, finalHandler);
        return current.process(ctx, next);
    }
}

public class AuthMiddleware implements Middleware {
    private final AuthService authService;
    
    @Override
    public Response process(RequestContext ctx, MiddlewareChain next) {
        String token = ctx.getRequest().getHeader("Authorization");
        
        if (token == null) {
            return Response.error(401, "Missing authorization header");
        }
        
        try {
            Principal principal = authService.authenticate(token);
            ctx.setPrincipal(principal);
            return next.proceed(ctx);
        } catch (AuthException e) {
            return Response.error(401, "Invalid token");
        }
    }
    
    @Override
    public int getOrder() { return 10; }  // Run early
}

public class RateLimitMiddleware implements Middleware {
    private final RateLimiter rateLimiter;
    
    @Override
    public Response process(RequestContext ctx, MiddlewareChain next) {
        String clientId = ctx.getRequest().getClientId();
        String routeId = ctx.getRoute().getId();
        
        if (!rateLimiter.tryAcquire(clientId, routeId)) {
            return Response.error(429, "Rate limit exceeded")
                .withHeader("Retry-After", String.valueOf(rateLimiter.getRetryAfter(clientId)));
        }
        
        return next.proceed(ctx);
    }
}
```

### 4. Circuit Breaker
```java
public class CircuitBreaker {
    private final String name;
    private final int failureThreshold;
    private final Duration openDuration;
    private final AtomicInteger failureCount;
    private final AtomicReference<State> state;
    private volatile Instant openedAt;
    
    public enum State { CLOSED, OPEN, HALF_OPEN }
    
    public boolean allowRequest() {
        State current = state.get();
        if (current == State.CLOSED) return true;
        if (current == State.OPEN) {
            if (Instant.now().isAfter(openedAt.plus(openDuration))) {
                state.compareAndSet(State.OPEN, State.HALF_OPEN);
                return true;
            }
            return false;
        }
        return true;  // HALF_OPEN: allow limited requests
    }
    
    public void recordSuccess() {
        failureCount.set(0);
        state.set(State.CLOSED);
    }
    
    public void recordFailure() {
        int failures = failureCount.incrementAndGet();
        if (failures >= failureThreshold) {
            state.set(State.OPEN);
            openedAt = Instant.now();
        }
    }
}
```

### 5. Load Balancer
```java
public interface LoadBalancer {
    ServiceInstance select(String serviceName, List<ServiceInstance> instances);
}

public class RoundRobinLoadBalancer implements LoadBalancer {
    private final Map<String, AtomicInteger> counters = new ConcurrentHashMap<>();
    
    @Override
    public ServiceInstance select(String serviceName, List<ServiceInstance> instances) {
        if (instances.isEmpty()) return null;
        
        AtomicInteger counter = counters.computeIfAbsent(serviceName, k -> new AtomicInteger());
        int idx = Math.abs(counter.getAndIncrement() % instances.size());
        return instances.get(idx);
    }
}

public class WeightedLoadBalancer implements LoadBalancer {
    @Override
    public ServiceInstance select(String serviceName, List<ServiceInstance> instances) {
        int totalWeight = instances.stream().mapToInt(ServiceInstance::getWeight).sum();
        int random = ThreadLocalRandom.current().nextInt(totalWeight);
        
        int cumulative = 0;
        for (ServiceInstance instance : instances) {
            cumulative += instance.getWeight();
            if (random < cumulative) return instance;
        }
        return instances.get(0);
    }
}
```

