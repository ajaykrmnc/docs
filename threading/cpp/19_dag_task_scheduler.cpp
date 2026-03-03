/*
 * QUESTION 19: Async Task Scheduler with Dependencies (Databricks/Glean)
 * ======================================================================
 * 
 * Problem: Execute tasks respecting dependencies. Maximize parallelism.
 * 
 * Key Concepts: DAG scheduling, topological sort, dependency resolution
 * 
 * Compile: g++ -std=c++17 -pthread 19_dag_task_scheduler.cpp -o dag_scheduler
 */

#include <iostream>
#include <vector>
#include <unordered_map>
#include <unordered_set>
#include <queue>
#include <thread>
#include <mutex>
#include <condition_variable>
#include <functional>
#include <future>

class DAGTaskScheduler {
    /*
     * EXPLANATION (Kahn's Algorithm with Parallelism):
     * 1. Build dependency graph
     * 2. Find tasks with no dependencies (ready)
     * 3. Run ready tasks in parallel
     * 4. When task completes, update dependents
     * 5. Add newly ready tasks
     */
private:
    struct Task {
        std::string id;
        std::function<void()> func;
        std::unordered_set<std::string> dependencies;
        std::unordered_set<std::string> dependents;
    };
    
    std::unordered_map<std::string, Task> tasks_;
    size_t num_workers_;

public:
    DAGTaskScheduler(size_t num_workers = 4) : num_workers_(num_workers) {}

    void addTask(const std::string& id, std::function<void()> func,
                 const std::vector<std::string>& deps = {}) {
        Task task;
        task.id = id;
        task.func = std::move(func);
        task.dependencies = {deps.begin(), deps.end()};
        tasks_[id] = std::move(task);
        
        // Update dependents
        for (const auto& dep : deps) {
            if (tasks_.count(dep)) {
                tasks_[dep].dependents.insert(id);
            }
        }
    }

    void execute() {
        std::unordered_map<std::string, int> in_degree;
        for (const auto& [id, task] : tasks_) {
            in_degree[id] = task.dependencies.size();
        }
        
        std::queue<std::string> ready;
        for (const auto& [id, degree] : in_degree) {
            if (degree == 0) ready.push(id);
        }
        
        std::mutex mutex;
        std::condition_variable cv;
        size_t remaining = tasks_.size();
        
        std::vector<std::thread> workers;
        
        for (size_t i = 0; i < num_workers_; ++i) {
            workers.emplace_back([&]() {
                while (true) {
                    std::string task_id;
                    {
                        std::unique_lock<std::mutex> lock(mutex);
                        cv.wait(lock, [&] { return !ready.empty() || remaining == 0; });
                        
                        if (remaining == 0) return;
                        if (ready.empty()) continue;
                        
                        task_id = ready.front();
                        ready.pop();
                    }
                    
                    // Execute task
                    tasks_[task_id].func();
                    
                    // Update dependents
                    {
                        std::lock_guard<std::mutex> lock(mutex);
                        for (const auto& dep_id : tasks_[task_id].dependents) {
                            if (--in_degree[dep_id] == 0) {
                                ready.push(dep_id);
                            }
                        }
                        --remaining;
                        cv.notify_all();
                    }
                }
            });
        }
        
        cv.notify_all();
        for (auto& w : workers) w.join();
    }
};

int main() {
    DAGTaskScheduler scheduler(4);
    std::mutex cout_mutex;
    
    auto makeTask = [&](const std::string& name) {
        return [&cout_mutex, name]() {
            {
                std::lock_guard<std::mutex> lock(cout_mutex);
                std::cout << "Executing " << name << std::endl;
            }
            std::this_thread::sleep_for(std::chrono::milliseconds(100));
        };
    };
    
    //     A
    //    / \
    //   B   C
    //    \ /
    //     D
    
    scheduler.addTask("A", makeTask("A"));
    scheduler.addTask("B", makeTask("B"), {"A"});
    scheduler.addTask("C", makeTask("C"), {"A"});
    scheduler.addTask("D", makeTask("D"), {"B", "C"});
    
    std::cout << "Starting DAG execution..." << std::endl;
    scheduler.execute();
    std::cout << "All tasks completed!" << std::endl;
    
    return 0;
}

