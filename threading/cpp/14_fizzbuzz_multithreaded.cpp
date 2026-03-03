/*
 * QUESTION 14: FizzBuzz Multithreaded (LeetCode 1195)
 * ===================================================
 * 
 * Problem: 4 threads print numbers 1 to n:
 * - Thread A: "fizz" for div by 3 (not 5)
 * - Thread B: "buzz" for div by 5 (not 3)
 * - Thread C: "fizzbuzz" for div by both
 * - Thread D: the number for others
 * 
 * Compile: g++ -std=c++17 -pthread 14_fizzbuzz_multithreaded.cpp -o fizzbuzz
 */

#include <iostream>
#include <thread>
#include <mutex>
#include <condition_variable>
#include <functional>
#include <vector>
#include <string>

class FizzBuzz {
    /*
     * EXPLANATION:
     * - Shared counter tracks current number
     * - Each thread waits for its turn (matches condition)
     * - After printing, increment and notify all
     * - Threads exit when counter > n
     */
private:
    int n_;
    int current_ = 1;
    std::mutex mutex_;
    std::condition_variable cv_;

public:
    FizzBuzz(int n) : n_(n) {}

    void fizz(std::function<void()> printFizz) {
        while (true) {
            std::unique_lock<std::mutex> lock(mutex_);
            cv_.wait(lock, [this] {
                return current_ > n_ || (current_ % 3 == 0 && current_ % 5 != 0);
            });
            if (current_ > n_) return;
            printFizz();
            ++current_;
            cv_.notify_all();
        }
    }

    void buzz(std::function<void()> printBuzz) {
        while (true) {
            std::unique_lock<std::mutex> lock(mutex_);
            cv_.wait(lock, [this] {
                return current_ > n_ || (current_ % 5 == 0 && current_ % 3 != 0);
            });
            if (current_ > n_) return;
            printBuzz();
            ++current_;
            cv_.notify_all();
        }
    }

    void fizzbuzz(std::function<void()> printFizzBuzz) {
        while (true) {
            std::unique_lock<std::mutex> lock(mutex_);
            cv_.wait(lock, [this] {
                return current_ > n_ || (current_ % 15 == 0);
            });
            if (current_ > n_) return;
            printFizzBuzz();
            ++current_;
            cv_.notify_all();
        }
    }

    void number(std::function<void(int)> printNumber) {
        while (true) {
            std::unique_lock<std::mutex> lock(mutex_);
            cv_.wait(lock, [this] {
                return current_ > n_ || (current_ % 3 != 0 && current_ % 5 != 0);
            });
            if (current_ > n_) return;
            printNumber(current_);
            ++current_;
            cv_.notify_all();
        }
    }
};

int main() {
    int n = 15;
    FizzBuzz fb(n);
    
    std::vector<std::string> output;
    std::mutex m;
    
    auto printFizz = [&]() { 
        std::lock_guard<std::mutex> l(m); 
        output.push_back("fizz"); 
    };
    auto printBuzz = [&]() { 
        std::lock_guard<std::mutex> l(m); 
        output.push_back("buzz"); 
    };
    auto printFizzBuzz = [&]() { 
        std::lock_guard<std::mutex> l(m); 
        output.push_back("fizzbuzz"); 
    };
    auto printNumber = [&](int x) { 
        std::lock_guard<std::mutex> l(m); 
        output.push_back(std::to_string(x)); 
    };
    
    std::thread t1([&]() { fb.fizz(printFizz); });
    std::thread t2([&]() { fb.buzz(printBuzz); });
    std::thread t3([&]() { fb.fizzbuzz(printFizzBuzz); });
    std::thread t4([&]() { fb.number(printNumber); });
    
    t1.join(); t2.join(); t3.join(); t4.join();
    
    std::cout << "Output: ";
    for (const auto& s : output) std::cout << s << " ";
    std::cout << std::endl;
    
    // Verify
    std::vector<std::string> expected;
    for (int i = 1; i <= n; ++i) {
        if (i % 15 == 0) expected.push_back("fizzbuzz");
        else if (i % 3 == 0) expected.push_back("fizz");
        else if (i % 5 == 0) expected.push_back("buzz");
        else expected.push_back(std::to_string(i));
    }
    
    std::cout << (output == expected ? "✓ PASSED" : "✗ FAILED") << std::endl;
    
    return 0;
}

