/*
 * QUESTION 12: Multithreaded Web Crawler (LeetCode 1242 - Glean Favorite!)
 * ========================================================================
 * 
 * Problem: Crawl URLs starting from seed, staying within same hostname.
 * Use multiple threads for parallel crawling.
 * 
 * Key Concepts: Thread-safe sets, work distribution, BFS with threads
 * 
 * Compile: g++ -std=c++17 -pthread 12_web_crawler.cpp -o web_crawler
 */

#include <iostream>
#include <string>
#include <vector>
#include <queue>
#include <unordered_set>
#include <mutex>
#include <condition_variable>
#include <thread>
#include <functional>

// Mock HTML Parser
class HtmlParser {
    std::unordered_map<std::string, std::vector<std::string>> graph_;
public:
    HtmlParser() {
        graph_["http://example.com"] = {"http://example.com/a", "http://example.com/b"};
        graph_["http://example.com/a"] = {"http://example.com/c", "http://other.com/x"};
        graph_["http://example.com/b"] = {"http://example.com/a"};
        graph_["http://example.com/c"] = {};
    }
    
    std::vector<std::string> getUrls(const std::string& url) {
        std::this_thread::sleep_for(std::chrono::milliseconds(10));
        auto it = graph_.find(url);
        return it != graph_.end() ? it->second : std::vector<std::string>{};
    }
};

std::string getHostname(const std::string& url) {
    size_t start = url.find("://");
    if (start == std::string::npos) return "";
    start += 3;
    size_t end = url.find("/", start);
    return url.substr(start, end - start);
}

class WebCrawler {
    /*
     * EXPLANATION:
     * 1. Thread-safe visited set (with mutex)
     * 2. Thread-safe URL queue
     * 3. Workers process URLs in parallel
     * 4. Termination: All workers idle + queue empty
     */
public:
    std::vector<std::string> crawl(const std::string& startUrl, HtmlParser& parser) {
        std::string hostname = getHostname(startUrl);
        
        std::unordered_set<std::string> visited;
        std::queue<std::string> queue;
        std::mutex visited_mutex, queue_mutex;
        std::condition_variable cv;
        
        int active_workers = 0;
        bool done = false;
        
        visited.insert(startUrl);
        queue.push(startUrl);
        
        constexpr int NUM_WORKERS = 4;
        
        auto worker = [&]() {
            while (true) {
                std::string url;
                {
                    std::unique_lock<std::mutex> lock(queue_mutex);
                    cv.wait(lock, [&] { return !queue.empty() || done; });
                    
                    if (done && queue.empty()) return;
                    
                    url = queue.front();
                    queue.pop();
                    ++active_workers;
                }
                
                auto urls = parser.getUrls(url);
                
                {
                    std::lock_guard<std::mutex> vlock(visited_mutex);
                    std::lock_guard<std::mutex> qlock(queue_mutex);
                    
                    for (const auto& next : urls) {
                        if (getHostname(next) == hostname && 
                            visited.find(next) == visited.end()) {
                            visited.insert(next);
                            queue.push(next);
                            cv.notify_one();
                        }
                    }
                    
                    --active_workers;
                    if (active_workers == 0 && queue.empty()) {
                        done = true;
                        cv.notify_all();
                    }
                }
            }
        };
        
        std::vector<std::thread> workers;
        for (int i = 0; i < NUM_WORKERS; ++i) {
            workers.emplace_back(worker);
        }
        
        cv.notify_all();
        
        for (auto& w : workers) w.join();
        
        return {visited.begin(), visited.end()};
    }
};

int main() {
    HtmlParser parser;
    WebCrawler crawler;
    
    auto result = crawler.crawl("http://example.com", parser);
    
    std::cout << "Crawled URLs:" << std::endl;
    for (const auto& url : result) {
        std::cout << "  " << url << std::endl;
    }
    
    return 0;
}

