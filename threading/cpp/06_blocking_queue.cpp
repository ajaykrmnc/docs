/*
 * QUESTION 6: Implement a Blocking Queue (Rubrik/Databricks)
 * ==========================================================
 * 
 * Problem: Thread-safe queue with blocking put/get and timeout variants.
 * 
 * Key Concepts: condition_variable, wait_for, RAII
 * 
 * Compile: g++ -std=c++17 -pthread 06_blocking_queue.cpp -o blocking_queue
 */

#include <iostream>
#include <queue>
#include <thread>
#include <mutex>
#include <condition_variable>
#include <chrono>
#include <optional>
#include <vector>

template<typename T>
class BlockingQueue {
    /*
     * EXPLANATION:
     * - std::queue for O(1) push/pop
     * - Single mutex + two condition variables
     * - Bounded capacity prevents OOM
     * 
     * wait() vs wait_for():
     * - wait(): Blocks indefinitely
     * - wait_for(): Returns after timeout (cv_status::timeout)
     */
private:
    std::queue<T> queue_;
    size_t capacity_;
    mutable std::mutex mutex_;
    std::condition_variable not_empty_;
    std::condition_variable not_full_;

public:
    explicit BlockingQueue(size_t capacity = SIZE_MAX) : capacity_(capacity) {}

    void put(const T& item) {
        std::unique_lock<std::mutex> lock(mutex_);
        not_full_.wait(lock, [this] { return queue_.size() < capacity_; });
        queue_.push(item);
        not_empty_.notify_one();
    }

    bool put(const T& item, std::chrono::milliseconds timeout) {
        std::unique_lock<std::mutex> lock(mutex_);
        if (!not_full_.wait_for(lock, timeout, [this] { return queue_.size() < capacity_; })) {
            return false;  // Timeout
        }
        queue_.push(item);
        not_empty_.notify_one();
        return true;
    }

    T get() {
        std::unique_lock<std::mutex> lock(mutex_);
        not_empty_.wait(lock, [this] { return !queue_.empty(); });
        T item = std::move(queue_.front());
        queue_.pop();
        not_full_.notify_one();
        return item;
    }

    std::optional<T> get(std::chrono::milliseconds timeout) {
        std::unique_lock<std::mutex> lock(mutex_);
        if (!not_empty_.wait_for(lock, timeout, [this] { return !queue_.empty(); })) {
            return std::nullopt;  // Timeout
        }
        T item = std::move(queue_.front());
        queue_.pop();
        not_full_.notify_one();
        return item;
    }

    bool try_get(T& item) {
        std::lock_guard<std::mutex> lock(mutex_);
        if (queue_.empty()) return false;
        item = std::move(queue_.front());
        queue_.pop();
        not_full_.notify_one();
        return true;
    }

    size_t size() const {
        std::lock_guard<std::mutex> lock(mutex_);
        return queue_.size();
    }

    bool empty() const {
        std::lock_guard<std::mutex> lock(mutex_);
        return queue_.empty();
    }
};

void producer(BlockingQueue<int>& q, int id) {
    for (int i = 0; i < 5; ++i) {
        int item = id * 100 + i;
        q.put(item);
        std::cout << "Producer " << id << " put " << item << std::endl;
    }
}

void consumer(BlockingQueue<int>& q, int id) {
    for (int i = 0; i < 5; ++i) {
        auto item = q.get(std::chrono::milliseconds(2000));
        if (item) {
            std::cout << "Consumer " << id << " got " << *item << std::endl;
        }
    }
}

int main() {
    BlockingQueue<int> q(5);
    
    std::vector<std::thread> threads;
    
    threads.emplace_back(producer, std::ref(q), 1);
    threads.emplace_back(producer, std::ref(q), 2);
    threads.emplace_back(consumer, std::ref(q), 1);
    threads.emplace_back(consumer, std::ref(q), 2);
    
    for (auto& t : threads) t.join();
    
    std::cout << "Done!" << std::endl;
    return 0;
}

