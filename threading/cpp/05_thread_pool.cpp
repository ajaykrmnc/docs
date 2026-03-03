/*
 * QUESTION 5: Implement a Thread Pool (Databricks/Glean Favorite)
 * ===============================================================
 * 
 * Problem: Create a fixed-size thread pool with task submission and futures.
 * 
 * Key Concepts: std::future, std::packaged_task, condition_variable
 * 
 * Compile: g++ -std=c++17 -pthread 05_thread_pool.cpp -o thread_pool
 */

#include <iostream>
#include <vector>
#include <queue>
#include <thread>
#include <mutex>
#include <condition_variable>
#include <future>
#include <functional>

class ThreadPool {
    /*
     * EXPLANATION:
     * Architecture:
     * 1. Task Queue: Holds std::function objects
     * 2. Worker Threads: Pull and execute tasks
     * 3. Futures: Allow caller to get results
     * 
     * Key Components:
     * - std::packaged_task: Wraps callable, provides future
     * - condition_variable: Workers wait for tasks
     * - atomic stop flag: Graceful shutdown
     */
private:
    std::vector<std::thread> workers_;
    std::queue<std::function<void()>> tasks_;
    std::mutex mutex_;
    std::condition_variable condition_;
    bool stop_ = false;

public:
    explicit ThreadPool(size_t num_threads) {
        for (size_t i = 0; i < num_threads; ++i) {
            workers_.emplace_back([this] {
                while (true) {
                    std::function<void()> task;
                    {
                        std::unique_lock<std::mutex> lock(mutex_);
                        condition_.wait(lock, [this] {
                            return stop_ || !tasks_.empty();
                        });
                        
                        if (stop_ && tasks_.empty()) return;
                        
                        task = std::move(tasks_.front());
                        tasks_.pop();
                    }
                    task();
                }
            });
        }
    }

    template<typename F, typename... Args>
    auto submit(F&& f, Args&&... args) -> std::future<decltype(f(args...))> {
        /*
         * EXPLANATION:
         * 1. Create packaged_task from callable
         * 2. Get future from packaged_task
         * 3. Wrap in function<void()> and enqueue
         * 4. Return future to caller
         */
        using return_type = decltype(f(args...));
        
        auto task = std::make_shared<std::packaged_task<return_type()>>(
            std::bind(std::forward<F>(f), std::forward<Args>(args)...)
        );
        
        std::future<return_type> result = task->get_future();
        
        {
            std::lock_guard<std::mutex> lock(mutex_);
            if (stop_) {
                throw std::runtime_error("ThreadPool is stopped");
            }
            tasks_.emplace([task]() { (*task)(); });
        }
        
        condition_.notify_one();
        return result;
    }

    ~ThreadPool() {
        {
            std::lock_guard<std::mutex> lock(mutex_);
            stop_ = true;
        }
        condition_.notify_all();
        
        for (auto& worker : workers_) {
            worker.join();
        }
    }
};

int square(int x) {
    std::this_thread::sleep_for(std::chrono::milliseconds(100));
    return x * x;
}

int main() {
    ThreadPool pool(4);
    
    std::vector<std::future<int>> results;
    
    for (int i = 0; i < 10; ++i) {
        results.push_back(pool.submit(square, i));
    }
    
    std::cout << "Results: ";
    for (auto& r : results) {
        std::cout << r.get() << " ";
    }
    std::cout << std::endl;
    
    // Lambda example
    auto future = pool.submit([](int a, int b) { return a + b; }, 10, 20);
    std::cout << "Lambda result: " << future.get() << std::endl;
    
    return 0;
}

