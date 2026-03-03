/*
 * QUESTION 17: Scheduled Executor Service (Rubrik/Glean)
 * ======================================================
 * 
 * Problem: Execute tasks at specified times or intervals.
 * 
 * Key Concepts: Priority queues, timer threads, periodic execution
 * 
 * Compile: g++ -std=c++17 -pthread 17_scheduled_executor.cpp -o scheduler
 */

#include <iostream>
#include <queue>
#include <thread>
#include <mutex>
#include <condition_variable>
#include <functional>
#include <chrono>
#include <atomic>
#include <memory>

using Clock = std::chrono::steady_clock;
using TimePoint = Clock::time_point;

struct ScheduledTask {
    TimePoint execute_time;
    int task_id;
    std::function<void()> func;
    std::chrono::milliseconds interval{0};  // 0 = one-time
    std::atomic<bool> cancelled{false};
    
    bool operator>(const ScheduledTask& other) const {
        return execute_time > other.execute_time;
    }
};

class ScheduledExecutor {
    /*
     * EXPLANATION:
     * - Min-heap priority queue (ordered by execute_time)
     * - Worker waits until next task is due
     * - Supports one-time and periodic tasks
     * - Wake when new task added (might be earlier)
     */
private:
    std::priority_queue<std::shared_ptr<ScheduledTask>,
                        std::vector<std::shared_ptr<ScheduledTask>>,
                        std::greater<std::shared_ptr<ScheduledTask>>> tasks_;
    std::mutex mutex_;
    std::condition_variable cv_;
    std::atomic<bool> shutdown_{false};
    std::thread worker_;
    std::atomic<int> next_id_{0};

    void workerLoop() {
        while (!shutdown_) {
            std::shared_ptr<ScheduledTask> task;
            {
                std::unique_lock<std::mutex> lock(mutex_);
                
                if (tasks_.empty()) {
                    cv_.wait(lock, [this] { return shutdown_ || !tasks_.empty(); });
                    continue;
                }
                
                auto wait_time = tasks_.top()->execute_time - Clock::now();
                if (wait_time > std::chrono::milliseconds(0)) {
                    cv_.wait_for(lock, wait_time);
                    continue;
                }
                
                task = tasks_.top();
                tasks_.pop();
            }
            
            if (task && !task->cancelled) {
                task->func();
                
                // Re-schedule periodic tasks
                if (task->interval.count() > 0 && !task->cancelled) {
                    task->execute_time = Clock::now() + task->interval;
                    std::lock_guard<std::mutex> lock(mutex_);
                    tasks_.push(task);
                }
            }
        }
    }

public:
    ScheduledExecutor() : worker_(&ScheduledExecutor::workerLoop, this) {}

    ~ScheduledExecutor() {
        shutdown_ = true;
        cv_.notify_all();
        if (worker_.joinable()) worker_.join();
    }

    int schedule(std::function<void()> func, std::chrono::milliseconds delay) {
        auto task = std::make_shared<ScheduledTask>();
        task->task_id = next_id_++;
        task->execute_time = Clock::now() + delay;
        task->func = std::move(func);
        
        {
            std::lock_guard<std::mutex> lock(mutex_);
            tasks_.push(task);
        }
        cv_.notify_one();
        
        return task->task_id;
    }

    int schedulePeriodic(std::function<void()> func,
                         std::chrono::milliseconds delay,
                         std::chrono::milliseconds interval) {
        auto task = std::make_shared<ScheduledTask>();
        task->task_id = next_id_++;
        task->execute_time = Clock::now() + delay;
        task->func = std::move(func);
        task->interval = interval;
        
        {
            std::lock_guard<std::mutex> lock(mutex_);
            tasks_.push(task);
        }
        cv_.notify_one();
        
        return task->task_id;
    }
};

int main() {
    ScheduledExecutor executor;
    
    std::cout << "Scheduling tasks..." << std::endl;
    
    executor.schedule([]() {
        std::cout << "One-time task executed!" << std::endl;
    }, std::chrono::milliseconds(500));
    
    executor.schedulePeriodic([]() {
        static int count = 0;
        std::cout << "Periodic task #" << ++count << std::endl;
    }, std::chrono::milliseconds(200), std::chrono::milliseconds(300));
    
    std::this_thread::sleep_for(std::chrono::milliseconds(1500));
    std::cout << "Shutting down..." << std::endl;
    
    return 0;
}

