/*
 * QUESTION 11: Print FooBar Alternately (LeetCode 1115)
 * =====================================================
 * 
 * Problem: Two threads call foo() and bar() n times each.
 * Ensure output is "foobar" repeated n times.
 * 
 * Key Concepts: Thread alternation, semaphores, condition variables
 * 
 * Compile: g++ -std=c++20 -pthread 11_print_foobar_alternately.cpp -o foobar
 */

#include <iostream>
#include <thread>
#include <mutex>
#include <condition_variable>
#include <semaphore>
#include <functional>

// SOLUTION 1: Semaphores
class FooBar_Sem {
    /*
     * EXPLANATION:
     * Two semaphores as turn signals:
     * - foo_sem: Initially 1 (foo goes first)
     * - bar_sem: Initially 0 (bar waits)
     * 
     * Sequence:
     * 1. foo acquires foo_sem, prints, releases bar_sem
     * 2. bar acquires bar_sem, prints, releases foo_sem
     */
private:
    int n_;
    std::binary_semaphore foo_sem_{1};  // foo starts
    std::binary_semaphore bar_sem_{0};  // bar waits

public:
    FooBar_Sem(int n) : n_(n) {}

    void foo(std::function<void()> printFoo) {
        for (int i = 0; i < n_; ++i) {
            foo_sem_.acquire();
            printFoo();
            bar_sem_.release();
        }
    }

    void bar(std::function<void()> printBar) {
        for (int i = 0; i < n_; ++i) {
            bar_sem_.acquire();
            printBar();
            foo_sem_.release();
        }
    }
};

// SOLUTION 2: Condition Variable
class FooBar_CV {
    /*
     * EXPLANATION:
     * Boolean flag indicates whose turn.
     * Each method waits for its turn, then flips flag.
     */
private:
    int n_;
    std::mutex mutex_;
    std::condition_variable cv_;
    bool foo_turn_ = true;

public:
    FooBar_CV(int n) : n_(n) {}

    void foo(std::function<void()> printFoo) {
        for (int i = 0; i < n_; ++i) {
            std::unique_lock<std::mutex> lock(mutex_);
            cv_.wait(lock, [this] { return foo_turn_; });
            printFoo();
            foo_turn_ = false;
            cv_.notify_one();
        }
    }

    void bar(std::function<void()> printBar) {
        for (int i = 0; i < n_; ++i) {
            std::unique_lock<std::mutex> lock(mutex_);
            cv_.wait(lock, [this] { return !foo_turn_; });
            printBar();
            foo_turn_ = true;
            cv_.notify_one();
        }
    }
};

// SOLUTION 3: Atomic with spin-wait
class FooBar_Atomic {
private:
    int n_;
    std::atomic<bool> foo_turn_{true};

public:
    FooBar_Atomic(int n) : n_(n) {}

    void foo(std::function<void()> printFoo) {
        for (int i = 0; i < n_; ++i) {
            while (!foo_turn_.load()) std::this_thread::yield();
            printFoo();
            foo_turn_.store(false);
        }
    }

    void bar(std::function<void()> printBar) {
        for (int i = 0; i < n_; ++i) {
            while (foo_turn_.load()) std::this_thread::yield();
            printBar();
            foo_turn_.store(true);
        }
    }
};

template<typename FooBarClass>
void test(const std::string& name, int n) {
    std::cout << "Testing " << name << ": ";
    
    FooBarClass fb(n);
    std::string output;
    std::mutex m;
    
    auto printFoo = [&]() { std::lock_guard<std::mutex> l(m); output += "foo"; };
    auto printBar = [&]() { std::lock_guard<std::mutex> l(m); output += "bar"; };
    
    // Start bar first to test synchronization
    std::thread t2([&]() { fb.bar(printBar); });
    std::thread t1([&]() { fb.foo(printFoo); });
    
    t1.join(); t2.join();
    
    std::string expected;
    for (int i = 0; i < n; ++i) expected += "foobar";
    
    std::cout << output;
    std::cout << (output == expected ? " ✓ PASSED" : " ✗ FAILED") << std::endl;
}

int main() {
    test<FooBar_Sem>("Semaphore", 3);
    test<FooBar_CV>("Condition Variable", 3);
    test<FooBar_Atomic>("Atomic", 3);
    return 0;
}

