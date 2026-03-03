/*
 * QUESTION 8: Dining Philosophers Problem (Classic!)
 * ===================================================
 * 
 * Problem: 5 philosophers, 5 forks. Each needs 2 forks to eat. Prevent deadlock.
 * 
 * Key Concepts: Resource hierarchy, std::scoped_lock, semaphores
 * 
 * Compile: g++ -std=c++17 -pthread 08_dining_philosophers.cpp -o dining
 */

#include <iostream>
#include <thread>
#include <mutex>
#include <vector>
#include <chrono>
#include <random>
#include <semaphore>

constexpr int NUM_PHILOSOPHERS = 5;
std::mutex forks[NUM_PHILOSOPHERS];
std::mutex cout_mutex;

void safe_print(const std::string& msg) {
    std::lock_guard<std::mutex> lock(cout_mutex);
    std::cout << msg << std::endl;
}

// SOLUTION 1: Resource Hierarchy (Lock Ordering)
void philosopher_ordered(int id) {
    /*
     * EXPLANATION:
     * Always pick up lower-numbered fork first.
     * Breaks CIRCULAR WAIT -> No deadlock!
     */
    int left = id;
    int right = (id + 1) % NUM_PHILOSOPHERS;
    
    // Order forks by index
    if (left > right) std::swap(left, right);
    
    for (int i = 0; i < 3; ++i) {
        // Think
        safe_print("Philosopher " + std::to_string(id) + " thinking");
        std::this_thread::sleep_for(std::chrono::milliseconds(100));
        
        // Pick up forks in order
        std::lock_guard<std::mutex> lock1(forks[left]);
        std::lock_guard<std::mutex> lock2(forks[right]);
        
        // Eat
        safe_print("Philosopher " + std::to_string(id) + " EATING");
        std::this_thread::sleep_for(std::chrono::milliseconds(100));
    }
}

// SOLUTION 2: std::scoped_lock (C++17 - Deadlock-free)
void philosopher_scoped(int id) {
    /*
     * EXPLANATION:
     * std::scoped_lock handles deadlock avoidance automatically!
     * Recommended modern C++ approach.
     */
    int left = id;
    int right = (id + 1) % NUM_PHILOSOPHERS;
    
    for (int i = 0; i < 3; ++i) {
        std::this_thread::sleep_for(std::chrono::milliseconds(100));
        
        // scoped_lock acquires both without deadlock
        std::scoped_lock lock(forks[left], forks[right]);
        
        safe_print("Philosopher " + std::to_string(id) + " EATING");
        std::this_thread::sleep_for(std::chrono::milliseconds(100));
    }
}

// SOLUTION 3: Semaphore as Waiter (Limit concurrent eaters)
std::counting_semaphore<NUM_PHILOSOPHERS - 1> waiter(NUM_PHILOSOPHERS - 1);

void philosopher_waiter(int id) {
    /*
     * EXPLANATION:
     * Allow only N-1 philosophers to try eating simultaneously.
     * Guarantees at least one gets both forks.
     */
    int left = id;
    int right = (id + 1) % NUM_PHILOSOPHERS;
    
    for (int i = 0; i < 3; ++i) {
        std::this_thread::sleep_for(std::chrono::milliseconds(100));
        
        waiter.acquire();  // Ask waiter permission
        
        std::lock_guard<std::mutex> lock1(forks[left]);
        std::lock_guard<std::mutex> lock2(forks[right]);
        
        safe_print("Philosopher " + std::to_string(id) + " EATING");
        std::this_thread::sleep_for(std::chrono::milliseconds(100));
        
        waiter.release();  // Done eating
    }
}

int main() {
    std::vector<std::thread> philosophers;
    
    std::cout << "=== Using std::scoped_lock ===" << std::endl;
    
    for (int i = 0; i < NUM_PHILOSOPHERS; ++i) {
        philosophers.emplace_back(philosopher_scoped, i);
    }
    
    for (auto& p : philosophers) {
        p.join();
    }
    
    std::cout << "All philosophers finished dining!" << std::endl;
    return 0;
}

