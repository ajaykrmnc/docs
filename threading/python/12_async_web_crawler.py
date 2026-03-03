"""
QUESTION 12: Multithreaded Web Crawler (LeetCode 1242 - Glean Favorite!)
========================================================================

Problem: Crawl URLs starting from a seed, staying within same hostname.
Use multiple threads for parallel crawling.

Key Concepts: Thread-safe sets, Work distribution, BFS with threads
"""

import threading
from collections import deque
from typing import List, Set
from urllib.parse import urlparse
import time


class HtmlParser:
    """Mock HTML parser for demo."""
    def __init__(self, graph):
        self.graph = graph  # url -> list of linked urls
    
    def getUrls(self, url: str) -> List[str]:
        time.sleep(0.01)  # Simulate network
        return self.graph.get(url, [])


class WebCrawler:
    """
    Multithreaded Web Crawler.
    
    EXPLANATION:
    1. Thread-safe visited set (with lock)
    2. Thread-safe URL queue
    3. Multiple worker threads process URLs
    4. Termination: All workers idle + queue empty
    
    Why not just BFS?
    - Network I/O is slow
    - Parallel requests dramatically faster
    """
    
    def crawl(self, startUrl: str, htmlParser: HtmlParser) -> List[str]:
        hostname = urlparse(startUrl).netloc
        
        visited = set()
        visited_lock = threading.Lock()
        
        queue = deque([startUrl])
        queue_lock = threading.Lock()
        queue_condition = threading.Condition(queue_lock)
        
        active_workers = [0]  # Track active workers
        done = [False]
        
        def worker():
            while True:
                url = None
                
                with queue_condition:
                    while not queue and not done[0]:
                        active_workers[0] -= 1
                        if active_workers[0] == 0 and not queue:
                            done[0] = True
                            queue_condition.notify_all()
                            return
                        queue_condition.wait()
                        active_workers[0] += 1
                    
                    if done[0]:
                        return
                    
                    url = queue.popleft()
                
                # Fetch and process outside lock
                urls = htmlParser.getUrls(url)
                
                for next_url in urls:
                    if urlparse(next_url).netloc == hostname:
                        with visited_lock:
                            if next_url not in visited:
                                visited.add(next_url)
                                with queue_condition:
                                    queue.append(next_url)
                                    queue_condition.notify()
        
        # Initialize
        visited.add(startUrl)
        NUM_WORKERS = 4
        active_workers[0] = NUM_WORKERS
        
        threads = [threading.Thread(target=worker) for _ in range(NUM_WORKERS)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        
        return list(visited)


class WebCrawlerSimple:
    """
    Simpler approach using ThreadPoolExecutor.
    
    EXPLANATION:
    Uses concurrent.futures for cleaner code.
    Submit new URLs as futures complete.
    """
    
    def crawl(self, startUrl: str, htmlParser: HtmlParser) -> List[str]:
        from concurrent.futures import ThreadPoolExecutor, as_completed
        
        hostname = urlparse(startUrl).netloc
        visited = {startUrl}
        lock = threading.Lock()
        
        with ThreadPoolExecutor(max_workers=4) as executor:
            futures = {executor.submit(htmlParser.getUrls, startUrl)}
            
            while futures:
                done_futures = set()
                for future in as_completed(futures):
                    done_futures.add(future)
                    for url in future.result():
                        if urlparse(url).netloc == hostname:
                            with lock:
                                if url not in visited:
                                    visited.add(url)
                                    futures.add(executor.submit(htmlParser.getUrls, url))
                
                futures -= done_futures
        
        return list(visited)


def demo():
    # Create mock web graph
    graph = {
        "http://example.com": ["http://example.com/a", "http://example.com/b"],
        "http://example.com/a": ["http://example.com/c", "http://other.com/x"],
        "http://example.com/b": ["http://example.com/a"],
        "http://example.com/c": [],
    }
    
    parser = HtmlParser(graph)
    crawler = WebCrawler()
    
    result = crawler.crawl("http://example.com", parser)
    print(f"Crawled URLs: {sorted(result)}")


if __name__ == "__main__":
    demo()

