/*
 * QUESTION 9: Barrier and Latch (Databricks/Rubrik)
 * ==================================================
 * 
 * Problem: Implement synchronization primitives for phase-based computation.
 * 
 * Key Concepts: std::barrier (C++20), std::latch (C++20), custom implementations
 * 
 * Compile: g++ -std=c++20 -pthread 09_barrier_latch.cpp -o barrier_latch
 */

#include <iostream>
#include <thread>
#include <mutex>
#include <condition_variable>
#include <vector>
#include <chrono>
#include <barrier>
#include <latch>

// Custom Barrier (for C++11/14/17)
class Barrier {
    /*
     * EXPLANATION:
     * All N threads must arrive before any can proceed.
     * 
     * Use Cases:
     * - Parallel algorithms with phases
     * - MapReduce: All mappers finish before reduce
     */
private:
    std::mutex mutex_;
    std::condition_variable cv_;
    size_t parties_;
    size_t count_;
    size_t generation_ = 0;

public:
    explicit Barrier(size_t parties) : parties_(parties), count_(parties) {}

    void wait() {
        std::unique_lock<std::mutex> lock(mutex_);
        size_t gen = generation_;
        
        if (--count_ == 0) {
            // Last to arrive - reset and wake all
            count_ = parties_;
            ++generation_;
            cv_.notify_all();
        } else {
            // Wait for others
            cv_.wait(lock, [this, gen] { return gen != generation_; });
        }
    }
};

// Custom CountDownLatch (for C++11/14/17)
class CountDownLatch {
    /*
     * EXPLANATION:
     * - Initialize with count N
     * - Some threads await(), others count_down()
     * - When count=0, all waiters proceed
     * - NOT reusable (one-shot)
     */
private:
    std::mutex mutex_;
    std::condition_variable cv_;
    size_t count_;

public:
    explicit CountDownLatch(size_t count) : count_(count) {}

    void count_down() {
        std::lock_guard<std::mutex> lock(mutex_);
        if (count_ > 0 && --count_ == 0) {
            cv_.notify_all();
        }
    }

    void wait() {
        std::unique_lock<std::mutex> lock(mutex_);
        cv_.wait(lock, [this] { return count_ == 0; });
    }
};

void barrier_demo() {
    std::cout << "=== Barrier Demo ===" << std::endl;
    
    constexpr int NUM_WORKERS = 4;
    constexpr int NUM_PHASES = 3;
    Barrier barrier(NUM_WORKERS);
    std::mutex cout_mutex;
    
    auto worker = [&](int id) {
        for (int phase = 0; phase < NUM_PHASES; ++phase) {
            {
                std::lock_guard<std::mutex> lock(cout_mutex);
                std::cout << "Worker " << id << " phase " << phase << std::endl;
            }
            std::this_thread::sleep_for(std::chrono::milliseconds(100 * (id + 1)));
            barrier.wait();
        }
    };
    
    std::vector<std::thread> threads;
    for (int i = 0; i < NUM_WORKERS; ++i) {
        threads.emplace_back(worker, i);
    }
    for (auto& t : threads) t.join();
}

void latch_demo() {
    std::cout << "\n=== CountDownLatch Demo ===" << std::endl;
    
    CountDownLatch latch(3);
    
    auto init_service = [&](const std::string& name, int delay_ms) {
        std::cout << name << " initializing..." << std::endl;
        std::this_thread::sleep_for(std::chrono::milliseconds(delay_ms));
        std::cout << name << " ready!" << std::endl;
        latch.count_down();
    };
    
    std::thread t1(init_service, "Database", 300);
    std::thread t2(init_service, "Cache", 200);
    std::thread t3(init_service, "MessageQueue", 400);
    
    std::cout << "Main: Waiting for services..." << std::endl;
    latch.wait();
    std::cout << "Main: All services ready!" << std::endl;
    
    t1.join(); t2.join(); t3.join();
}

// C++20 std::barrier and std::latch demo
void cpp20_demo() {
    std::cout << "\n=== C++20 std::barrier ===" << std::endl;
    
    auto on_completion = []() noexcept {
        std::cout << "Phase complete!" << std::endl;
    };
    
    std::barrier sync_point(3, on_completion);
    
    auto task = [&](int id) {
        std::cout << "Thread " << id << " working" << std::endl;
        sync_point.arrive_and_wait();
    };
    
    std::thread t1(task, 1), t2(task, 2), t3(task, 3);
    t1.join(); t2.join(); t3.join();
}

int main() {
    barrier_demo();
    latch_demo();
    cpp20_demo();
    return 0;
}

