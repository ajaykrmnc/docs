/*
 * QUESTION 3: Thread-Safe Singleton Pattern (Databricks/Glean)
 * =============================================================
 * 
 * Problem: Ensure only one instance is created even with concurrent access.
 * 
 * Key Concepts: Double-checked locking, std::call_once, Meyer's Singleton
 * 
 * Compile: g++ -std=c++17 -pthread 03_thread_safe_singleton.cpp -o singleton
 */

#include <iostream>
#include <thread>
#include <mutex>
#include <vector>
#include <atomic>

// SOLUTION 1: Double-Checked Locking Pattern (DCLP)
class SingletonDCLP {
    /*
     * EXPLANATION:
     * 1. First check (no lock): Fast path when instance exists
     * 2. Lock acquisition: Only one thread creates
     * 3. Second check: Another thread might have created while waiting
     * 
     * CRITICAL: Use std::atomic for instance_ to prevent memory reordering!
     * Without atomic, compiler might reorder writes (allocate -> assign -> construct)
     */
private:
    static std::atomic<SingletonDCLP*> instance_;
    static std::mutex mutex_;
    int value_ = 0;

    SingletonDCLP() {
        std::cout << "SingletonDCLP created by thread " 
                  << std::this_thread::get_id() << std::endl;
    }

public:
    static SingletonDCLP* getInstance() {
        SingletonDCLP* tmp = instance_.load(std::memory_order_acquire);
        if (tmp == nullptr) {
            std::lock_guard<std::mutex> lock(mutex_);
            tmp = instance_.load(std::memory_order_relaxed);
            if (tmp == nullptr) {
                tmp = new SingletonDCLP();
                instance_.store(tmp, std::memory_order_release);
            }
        }
        return tmp;
    }

    void setValue(int v) { value_ = v; }
    int getValue() const { return value_; }
};

std::atomic<SingletonDCLP*> SingletonDCLP::instance_{nullptr};
std::mutex SingletonDCLP::mutex_;


// SOLUTION 2: std::call_once (Recommended)
class SingletonCallOnce {
    /*
     * EXPLANATION:
     * std::call_once guarantees the callable is executed exactly once.
     * Thread-safe by standard. Simple and clean!
     */
private:
    static std::unique_ptr<SingletonCallOnce> instance_;
    static std::once_flag once_flag_;

    SingletonCallOnce() {
        std::cout << "SingletonCallOnce created by thread "
                  << std::this_thread::get_id() << std::endl;
    }

public:
    static SingletonCallOnce* getInstance() {
        std::call_once(once_flag_, []() {
            instance_.reset(new SingletonCallOnce());
        });
        return instance_.get();
    }
};

std::unique_ptr<SingletonCallOnce> SingletonCallOnce::instance_;
std::once_flag SingletonCallOnce::once_flag_;


// SOLUTION 3: Meyer's Singleton (C++11 Guaranteed Thread-Safe)
class SingletonMeyer {
    /*
     * EXPLANATION:
     * C++11 guarantees static local variable initialization is thread-safe.
     * The simplest and most elegant solution!
     * 
     * "If control enters the declaration concurrently while the variable
     *  is being initialized, the concurrent execution shall wait."
     */
private:
    SingletonMeyer() {
        std::cout << "SingletonMeyer created by thread "
                  << std::this_thread::get_id() << std::endl;
    }

public:
    static SingletonMeyer& getInstance() {
        static SingletonMeyer instance;  // Thread-safe in C++11!
        return instance;
    }

    SingletonMeyer(const SingletonMeyer&) = delete;
    SingletonMeyer& operator=(const SingletonMeyer&) = delete;
};


void testSingleton() {
    // Test Meyer's Singleton
    auto* s1 = &SingletonMeyer::getInstance();
    auto* s2 = &SingletonMeyer::getInstance();
    std::cout << "Same instance: " << (s1 == s2 ? "YES" : "NO") << std::endl;
}

int main() {
    std::vector<std::thread> threads;
    
    // Multiple threads try to get singleton
    for (int i = 0; i < 10; ++i) {
        threads.emplace_back(testSingleton);
    }
    
    for (auto& t : threads) t.join();
    
    std::cout << "All tests passed!" << std::endl;
    return 0;
}

