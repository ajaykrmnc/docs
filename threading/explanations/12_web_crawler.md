# Problem 12: Multithreaded Web Crawler (LeetCode 1242)

## 🎯 Problem Statement
Crawl URLs starting from a seed, staying within same hostname. Use multiple threads for parallel crawling.

## 🏢 Companies
**Glean** (search indexing), **Databricks** (data ingestion) - Real-world application!

## 🔑 Core Principles

### 1. Why Parallelism?

```
SEQUENTIAL:                    PARALLEL (4 threads):
URL1 → [fetch 100ms]          URL1 → [fetch 100ms] ┐
URL2 → [fetch 100ms]          URL2 → [fetch 100ms] ├→ 100ms total!
URL3 → [fetch 100ms]          URL3 → [fetch 100ms] │
URL4 → [fetch 100ms]          URL4 → [fetch 100ms] ┘
       ═══════════
       400ms total            4× FASTER (I/O bound)
```

### 2. Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    WEB CRAWLER                           │
│                                                          │
│  ┌─────────────┐    ┌──────────────────────────────┐    │
│  │ URL QUEUE   │    │       WORKER THREADS         │    │
│  │ (thread-    │    │  ┌────┐ ┌────┐ ┌────┐ ┌────┐│    │
│  │  safe)      │───►│  │ W1 │ │ W2 │ │ W3 │ │ W4 ││    │
│  │             │    │  └────┘ └────┘ └────┘ └────┘│    │
│  └─────────────┘    └──────────────────────────────┘    │
│         ▲                        │                       │
│         │    new URLs discovered │                       │
│         └────────────────────────┘                       │
│                                                          │
│  ┌─────────────┐                                        │
│  │ VISITED SET │ ← Thread-safe, prevents duplicates     │
│  │ (with lock) │                                        │
│  └─────────────┘                                        │
└─────────────────────────────────────────────────────────┘
```

### 3. BFS with Multiple Threads

```
LEVEL 0: [seed_url]
            │
    ┌───────┼───────┐
    ▼       ▼       ▼
LEVEL 1: [url_a] [url_b] [url_c]  ← Fetch in parallel!
            │       │       │
         ┌──┴──┐ ┌──┴──┐ ┌──┴──┐
         ▼     ▼ ▼     ▼ ▼     ▼
LEVEL 2: [...]  ← All fetched in parallel!
```

### 4. Thread-Safe Components

```python
class WebCrawler:
    def __init__(self):
        self.visited = set()        # Needs lock!
        self.visited_lock = Lock()
        
        self.queue = Queue()        # Thread-safe
        
        self.active_workers = 0     # Track busy workers
        self.done = Event()         # Termination signal
```

### 5. Termination Detection

```
CHALLENGE: When are we done?

WRONG: Queue is empty
  → Workers might be processing, will add more URLs!

RIGHT: Queue empty AND all workers idle
  
┌─────────────────────────────────────────┐
│ Worker finishes task:                    │
│   1. Decrement active_workers            │
│   2. If active_workers == 0 AND          │
│      queue is empty:                     │
│      → Signal done!                      │
│                                          │
│ Worker picks up task:                    │
│   1. Increment active_workers            │
└─────────────────────────────────────────┘
```

## 📊 Implementation Strategy

```python
def crawl(self, start_url, html_parser):
    hostname = get_hostname(start_url)
    visited = {start_url}
    queue = Queue()
    queue.put(start_url)
    
    def worker():
        while True:
            url = queue.get()
            if url is None:  # Poison pill
                break
            
            # Fetch and process
            for next_url in html_parser.getUrls(url):
                if get_hostname(next_url) == hostname:
                    with lock:
                        if next_url not in visited:
                            visited.add(next_url)
                            queue.put(next_url)
            
            queue.task_done()
    
    # Start workers
    threads = [Thread(target=worker) for _ in range(NUM_WORKERS)]
    for t in threads: t.start()
    
    queue.join()  # Wait for all tasks
    
    # Shutdown workers
    for _ in threads: queue.put(None)
    for t in threads: t.join()
    
    return list(visited)
```

## 🧠 Key Insights

### Why Lock the Visited Set?
```
WITHOUT lock:
  Thread 1: if url not in visited: → True
  Thread 2: if url not in visited: → True  (race!)
  Thread 1: visited.add(url)
  Thread 2: visited.add(url)  → Duplicate processing!

WITH lock:
  Thread 1: [LOCK] check + add [UNLOCK]
  Thread 2: ──waiting── [LOCK] check → already visited!
```

### Hostname Filtering
```python
def get_hostname(url):
    # "http://example.com/path" → "example.com"
    parsed = urlparse(url)
    return parsed.netloc

# Only crawl same hostname
if get_hostname(next_url) == hostname:
    process(next_url)
```

## ⚠️ Common Mistakes

| Mistake | Problem | Fix |
|---------|---------|-----|
| No visited check | Infinite loops | Check before enqueue |
| Race on visited set | Duplicate work | Lock around check+add |
| Wrong termination | Hang or early exit | Track active workers |
| No hostname filter | Crawl entire internet | Filter by hostname |

## 💻 Simpler with ThreadPoolExecutor

```python
def crawl(self, start_url, html_parser):
    hostname = get_hostname(start_url)
    visited = {start_url}
    lock = Lock()
    
    with ThreadPoolExecutor(max_workers=4) as executor:
        futures = {executor.submit(html_parser.getUrls, start_url)}
        
        while futures:
            done, futures = wait(futures, return_when=FIRST_COMPLETED)
            for future in done:
                for url in future.result():
                    if get_hostname(url) == hostname:
                        with lock:
                            if url not in visited:
                                visited.add(url)
                                futures.add(executor.submit(
                                    html_parser.getUrls, url
                                ))
    
    return list(visited)
```

## 📈 Performance Considerations

| Factor | Impact | Optimization |
|--------|--------|--------------|
| Network latency | Main bottleneck | More threads |
| DNS lookups | Adds latency | DNS caching |
| Connection reuse | Reduces overhead | HTTP keep-alive |
| Memory (URLs) | Can grow large | Bloom filter |

