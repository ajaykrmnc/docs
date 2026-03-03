/*
 * QUESTION 1: Producer-Consumer Problem (Databricks/Rubrik Favorite)
 * ===================================================================
 * 
 * Problem: Implement a thread-safe bounded buffer where multiple producers
 * add items and multiple consumers remove items.
 * 
 * Key Concepts: std::mutex, std::condition_variable, std::unique_lock
 * 
 * Compile: g++ -std=c++17 -pthread 01_producer_consumer.cpp -o producer_consumer
 */

#include <iostream>
#include <queue>
#include <thread>
#include <mutex>
#include <condition_variable>
#include <chrono>
#include <vector>
#include <string>

template<typename T>
class BoundedBuffer {
    /*
     * EXPLANATION:
     * - mutex protects the buffer
     * - not_full: producers wait when buffer is full
     * - not_empty: consumers wait when buffer is empty
     * - Use while loop for condition check (handles spurious wakeups)
     * 
     * Why unique_lock instead of lock_guard?
     * - condition_variable::wait() needs to unlock/relock
     * - unique_lock supports manual unlock/lock
     */
private:
    std::queue<T> buffer_;
    size_t capacity_;
    std::mutex mutex_;
    std::condition_variable not_full_;
    std::condition_variable not_empty_;

public:
    explicit BoundedBuffer(size_t capacity) : capacity_(capacity) {}

    void put(const T& item) {
        std::unique_lock<std::mutex> lock(mutex_);
        
        // Wait while buffer is full
        not_full_.wait(lock, [this]() { 
            return buffer_.size() < capacity_; 
        });
        
        buffer_.push(item);
        std::cout << "Produced: " << item << ", Buffer size: " << buffer_.size() << std::endl;
        
        // Notify one waiting consumer
        not_empty_.notify_one();
    }

    T get() {
        std::unique_lock<std::mutex> lock(mutex_);
        
        // Wait while buffer is empty
        not_empty_.wait(lock, [this]() { 
            return !buffer_.empty(); 
        });
        
        T item = buffer_.front();
        buffer_.pop();
        std::cout << "Consumed: " << item << ", Buffer size: " << buffer_.size() << std::endl;
        
        // Notify one waiting producer
        not_full_.notify_one();
        return item;
    }

    size_t size() {
        std::lock_guard<std::mutex> lock(mutex_);
        return buffer_.size();
    }
};

void producer(BoundedBuffer<std::string>& buffer, int id, int count) {
    for (int i = 0; i < count; ++i) {
        std::string item = "Item-" + std::to_string(id) + "-" + std::to_string(i);
        buffer.put(item);
        std::this_thread::sleep_for(std::chrono::milliseconds(100));
    }
}

void consumer(BoundedBuffer<std::string>& buffer, int id, int count) {
    for (int i = 0; i < count; ++i) {
        buffer.get();
        std::this_thread::sleep_for(std::chrono::milliseconds(150));
    }
}

int main() {
    BoundedBuffer<std::string> buffer(5);
    
    std::vector<std::thread> threads;
    
    // 2 producers, each producing 5 items
    threads.emplace_back(producer, std::ref(buffer), 0, 5);
    threads.emplace_back(producer, std::ref(buffer), 1, 5);
    
    // 2 consumers, each consuming 5 items
    threads.emplace_back(consumer, std::ref(buffer), 0, 5);
    threads.emplace_back(consumer, std::ref(buffer), 1, 5);
    
    for (auto& t : threads) {
        t.join();
    }
    
    std::cout << "All producers and consumers finished!" << std::endl;
    return 0;
}

