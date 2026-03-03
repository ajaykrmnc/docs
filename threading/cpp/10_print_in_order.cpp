/*
 * QUESTION 10: Print In Order (LeetCode 1114)
 * ===========================================
 * 
 * Problem: Three threads call first(), second(), third() in any order.
 * Ensure output is always "first", "second", "third".
 * 
 * Key Concepts: condition_variable, semaphores, atomic flags
 * 
 * Compile: g++ -std=c++20 -pthread 10_print_in_order.cpp -o print_in_order
 */

#include <iostream>
#include <thread>
#include <mutex>
#include <condition_variable>
#include <semaphore>
#include <functional>

// SOLUTION 1: Condition Variable
class Foo_CV {
    /*
     * EXPLANATION:
     * State tracks progress: 0 -> 1 -> 2 -> done
     * Each method waits for previous state.
     */
private:
    std::mutex mutex_;
    std::condition_variable cv_;
    int state_ = 0;

public:
    void first(std::function<void()> printFirst) {
        std::unique_lock<std::mutex> lock(mutex_);
        printFirst();
        state_ = 1;
        cv_.notify_all();
    }

    void second(std::function<void()> printSecond) {
        std::unique_lock<std::mutex> lock(mutex_);
        cv_.wait(lock, [this] { return state_ >= 1; });
        printSecond();
        state_ = 2;
        cv_.notify_all();
    }

    void third(std::function<void()> printThird) {
        std::unique_lock<std::mutex> lock(mutex_);
        cv_.wait(lock, [this] { return state_ >= 2; });
        printThird();
    }
};

// SOLUTION 2: Semaphores (C++20)
class Foo_Sem {
    /*
     * EXPLANATION:
     * Semaphores as gates:
     * - sem1: Blocks second until first completes
     * - sem2: Blocks third until second completes
     */
private:
    std::binary_semaphore sem1_{0};
    std::binary_semaphore sem2_{0};

public:
    void first(std::function<void()> printFirst) {
        printFirst();
        sem1_.release();
    }

    void second(std::function<void()> printSecond) {
        sem1_.acquire();
        printSecond();
        sem2_.release();
    }

    void third(std::function<void()> printThird) {
        sem2_.acquire();
        printThird();
    }
};

// SOLUTION 3: Atomic flags
class Foo_Atomic {
    /*
     * EXPLANATION:
     * Atomic flags with spin-wait.
     * Simple but wastes CPU cycles (busy waiting).
     */
private:
    std::atomic<bool> first_done_{false};
    std::atomic<bool> second_done_{false};

public:
    void first(std::function<void()> printFirst) {
        printFirst();
        first_done_.store(true, std::memory_order_release);
    }

    void second(std::function<void()> printSecond) {
        while (!first_done_.load(std::memory_order_acquire)) {
            std::this_thread::yield();
        }
        printSecond();
        second_done_.store(true, std::memory_order_release);
    }

    void third(std::function<void()> printThird) {
        while (!second_done_.load(std::memory_order_acquire)) {
            std::this_thread::yield();
        }
        printThird();
    }
};

template<typename FooClass>
void test(const std::string& name) {
    std::cout << "Testing " << name << ": ";
    
    FooClass foo;
    std::string output;
    std::mutex output_mutex;
    
    auto printFirst = [&]() {
        std::lock_guard<std::mutex> lock(output_mutex);
        output += "first";
    };
    auto printSecond = [&]() {
        std::lock_guard<std::mutex> lock(output_mutex);
        output += "second";
    };
    auto printThird = [&]() {
        std::lock_guard<std::mutex> lock(output_mutex);
        output += "third";
    };
    
    // Start in REVERSE order to test synchronization
    std::thread t3([&]() { foo.third(printThird); });
    std::this_thread::sleep_for(std::chrono::milliseconds(10));
    std::thread t2([&]() { foo.second(printSecond); });
    std::this_thread::sleep_for(std::chrono::milliseconds(10));
    std::thread t1([&]() { foo.first(printFirst); });
    
    t1.join(); t2.join(); t3.join();
    
    std::cout << output;
    std::cout << (output == "firstsecondthird" ? " ✓ PASSED" : " ✗ FAILED") << std::endl;
}

int main() {
    test<Foo_CV>("Condition Variable");
    test<Foo_Sem>("Semaphore");
    test<Foo_Atomic>("Atomic");
    return 0;
}

