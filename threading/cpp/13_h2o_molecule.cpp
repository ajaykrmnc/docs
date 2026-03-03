/*
 * QUESTION 13: Building H2O (LeetCode 1117 - Databricks)
 * ======================================================
 * 
 * Problem: Multiple threads call hydrogen() and oxygen().
 * Ensure they proceed in groups of 2 hydrogen + 1 oxygen.
 * 
 * Key Concepts: Barrier patterns, semaphores, resource matching
 * 
 * Compile: g++ -std=c++20 -pthread 13_h2o_molecule.cpp -o h2o
 */

#include <iostream>
#include <thread>
#include <mutex>
#include <condition_variable>
#include <semaphore>
#include <barrier>
#include <functional>
#include <vector>
#include <random>

// SOLUTION 1: Semaphores + Barrier
class H2O_Sem {
    /*
     * EXPLANATION:
     * - h_sem: Allows 2 hydrogen threads
     * - o_sem: Allows 1 oxygen thread
     * - barrier: All 3 must arrive before proceeding
     * - After barrier, semaphores released for next molecule
     */
private:
    std::counting_semaphore<2> h_sem_{2};
    std::counting_semaphore<1> o_sem_{1};
    std::barrier<> barrier_{3};

public:
    void hydrogen(std::function<void()> releaseHydrogen) {
        h_sem_.acquire();
        releaseHydrogen();
        barrier_.arrive_and_wait();
        h_sem_.release();
    }

    void oxygen(std::function<void()> releaseOxygen) {
        o_sem_.acquire();
        releaseOxygen();
        barrier_.arrive_and_wait();
        o_sem_.release();
    }
};

// SOLUTION 2: Condition Variables
class H2O_CV {
    /*
     * EXPLANATION:
     * Track counts and use condition to synchronize.
     * Form molecule when 2H + 1O ready.
     */
private:
    std::mutex mutex_;
    std::condition_variable cv_;
    int h_count_ = 0;
    int o_count_ = 0;

    void tryFormMolecule() {
        if (h_count_ >= 2 && o_count_ >= 1) {
            h_count_ -= 2;
            o_count_ -= 1;
            cv_.notify_all();
        }
    }

public:
    void hydrogen(std::function<void()> releaseHydrogen) {
        std::unique_lock<std::mutex> lock(mutex_);
        cv_.wait(lock, [this] { return h_count_ < 2; });
        ++h_count_;
        releaseHydrogen();
        tryFormMolecule();
    }

    void oxygen(std::function<void()> releaseOxygen) {
        std::unique_lock<std::mutex> lock(mutex_);
        cv_.wait(lock, [this] { return o_count_ < 1; });
        ++o_count_;
        releaseOxygen();
        tryFormMolecule();
    }
};

void test_h2o() {
    H2O_Sem h2o;
    std::string output;
    std::mutex m;
    
    auto releaseH = [&]() { std::lock_guard<std::mutex> l(m); output += 'H'; };
    auto releaseO = [&]() { std::lock_guard<std::mutex> l(m); output += 'O'; };
    
    std::vector<std::thread> threads;
    
    // 4H + 2O = 2 molecules
    for (int i = 0; i < 4; ++i) {
        threads.emplace_back([&]() { h2o.hydrogen(releaseH); });
    }
    for (int i = 0; i < 2; ++i) {
        threads.emplace_back([&]() { h2o.oxygen(releaseO); });
    }
    
    // Shuffle thread start order
    std::random_device rd;
    std::mt19937 g(rd());
    std::shuffle(threads.begin(), threads.end(), g);
    
    for (auto& t : threads) {
        if (t.joinable()) t.join();
    }
    
    std::cout << "Output: " << output << std::endl;
    
    // Verify: Each group of 3 should be HHO
    bool valid = true;
    for (size_t i = 0; i < output.size(); i += 3) {
        std::string group = output.substr(i, 3);
        std::sort(group.begin(), group.end());
        if (group != "HHO") valid = false;
    }
    
    std::cout << (valid ? "✓ Valid H2O molecules!" : "✗ Invalid!") << std::endl;
}

int main() {
    test_h2o();
    return 0;
}

