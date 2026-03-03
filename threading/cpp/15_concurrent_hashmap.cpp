/*
 * QUESTION 15: Concurrent HashMap (Rubrik/Databricks Critical!)
 * =============================================================
 * 
 * Problem: Implement a thread-safe hash map with good concurrency.
 * 
 * Key Concepts: Lock striping, fine-grained locking, std::shared_mutex
 * 
 * Compile: g++ -std=c++17 -pthread 15_concurrent_hashmap.cpp -o concurrent_map
 */

#include <iostream>
#include <unordered_map>
#include <shared_mutex>
#include <mutex>
#include <vector>
#include <thread>
#include <optional>
#include <chrono>

// SOLUTION 1: Global Lock (Simple but poor concurrency)
template<typename K, typename V>
class ConcurrentMapGlobal {
private:
    std::unordered_map<K, V> map_;
    mutable std::mutex mutex_;

public:
    void put(const K& key, const V& value) {
        std::lock_guard<std::mutex> lock(mutex_);
        map_[key] = value;
    }

    std::optional<V> get(const K& key) const {
        std::lock_guard<std::mutex> lock(mutex_);
        auto it = map_.find(key);
        return it != map_.end() ? std::optional<V>(it->second) : std::nullopt;
    }
};

// SOLUTION 2: Lock Striping (Better concurrency)
template<typename K, typename V, size_t NUM_BUCKETS = 16>
class ConcurrentMapStriped {
    /*
     * EXPLANATION:
     * Divide map into N segments, each with own lock.
     * Operations on different segments proceed in parallel.
     * 
     * This is how Java's ConcurrentHashMap works!
     */
private:
    struct Bucket {
        std::unordered_map<K, V> map;
        mutable std::shared_mutex mutex;  // RW lock for each bucket
    };
    
    std::array<Bucket, NUM_BUCKETS> buckets_;
    
    size_t getBucketIndex(const K& key) const {
        return std::hash<K>{}(key) % NUM_BUCKETS;
    }

public:
    void put(const K& key, const V& value) {
        auto& bucket = buckets_[getBucketIndex(key)];
        std::unique_lock<std::shared_mutex> lock(bucket.mutex);
        bucket.map[key] = value;
    }

    std::optional<V> get(const K& key) const {
        const auto& bucket = buckets_[getBucketIndex(key)];
        std::shared_lock<std::shared_mutex> lock(bucket.mutex);  // Read lock
        auto it = bucket.map.find(key);
        return it != bucket.map.end() ? std::optional<V>(it->second) : std::nullopt;
    }

    bool remove(const K& key) {
        auto& bucket = buckets_[getBucketIndex(key)];
        std::unique_lock<std::shared_mutex> lock(bucket.mutex);
        return bucket.map.erase(key) > 0;
    }

    bool contains(const K& key) const {
        const auto& bucket = buckets_[getBucketIndex(key)];
        std::shared_lock<std::shared_mutex> lock(bucket.mutex);
        return bucket.map.find(key) != bucket.map.end();
    }

    size_t size() const {
        size_t total = 0;
        for (const auto& bucket : buckets_) {
            std::shared_lock<std::shared_mutex> lock(bucket.mutex);
            total += bucket.map.size();
        }
        return total;
    }
};

template<typename MapType>
void benchmark(const std::string& name) {
    MapType map;
    constexpr int N = 10000;
    
    auto writer = [&](int start) {
        for (int i = start; i < start + N; ++i) {
            map.put("key" + std::to_string(i), i);
        }
    };
    
    auto reader = [&](int start) {
        for (int i = start; i < start + N; ++i) {
            map.get("key" + std::to_string(i));
        }
    };
    
    auto start_time = std::chrono::high_resolution_clock::now();
    
    std::vector<std::thread> threads;
    for (int i = 0; i < 4; ++i) {
        threads.emplace_back(writer, i * N);
        threads.emplace_back(reader, i * N);
    }
    
    for (auto& t : threads) t.join();
    
    auto end_time = std::chrono::high_resolution_clock::now();
    auto duration = std::chrono::duration_cast<std::chrono::milliseconds>(end_time - start_time);
    
    std::cout << name << ": " << duration.count() << "ms, size=" << map.size() << std::endl;
}

int main() {
    benchmark<ConcurrentMapGlobal<std::string, int>>("Global Lock");
    benchmark<ConcurrentMapStriped<std::string, int>>("Lock Striping");
    return 0;
}

