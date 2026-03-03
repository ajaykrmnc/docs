/*
 * QUESTION 4: Deadlock Detection and Prevention (Rubrik/Databricks Critical!)
 * ============================================================================
 * 
 * Problem: Implement mechanisms to detect and prevent deadlocks.
 * 
 * Key Concepts: std::lock, std::scoped_lock, lock ordering, try_lock
 * 
 * COFFMAN CONDITIONS (all 4 needed for deadlock):
 * 1. Mutual Exclusion   2. Hold and Wait
 * 3. No Preemption      4. Circular Wait
 * 
 * Compile: g++ -std=c++17 -pthread 04_deadlock_prevention.cpp -o deadlock
 */

#include <iostream>
#include <thread>
#include <mutex>
#include <chrono>
#include <vector>

// SOLUTION 1: std::scoped_lock (C++17) - Deadlock-free multiple lock acquisition
class Account {
public:
    std::mutex mutex;
    int balance;
    int id;
    
    Account(int id, int balance) : id(id), balance(balance) {}
};

void transfer_safe(Account& from, Account& to, int amount) {
    /*
     * EXPLANATION:
     * std::scoped_lock acquires multiple locks in deadlock-free manner.
     * Uses deadlock avoidance algorithm internally (try-and-back-off).
     * This is the RECOMMENDED approach in modern C++!
     */
    std::scoped_lock lock(from.mutex, to.mutex);
    
    if (from.balance >= amount) {
        from.balance -= amount;
        to.balance += amount;
        std::cout << "Transferred " << amount << " from " << from.id 
                  << " to " << to.id << std::endl;
    }
}

// SOLUTION 2: std::lock + std::adopt_lock (C++11)
void transfer_safe_cpp11(Account& from, Account& to, int amount) {
    /*
     * EXPLANATION:
     * std::lock() locks multiple mutexes without deadlock.
     * std::adopt_lock tells lock_guard the mutex is already locked.
     */
    std::lock(from.mutex, to.mutex);
    std::lock_guard<std::mutex> lock1(from.mutex, std::adopt_lock);
    std::lock_guard<std::mutex> lock2(to.mutex, std::adopt_lock);
    
    if (from.balance >= amount) {
        from.balance -= amount;
        to.balance += amount;
    }
}

// SOLUTION 3: Lock Ordering (Manual approach)
void transfer_ordered(Account& from, Account& to, int amount) {
    /*
     * EXPLANATION:
     * Always acquire locks in consistent order (by ID).
     * Breaks CIRCULAR WAIT condition -> No deadlock!
     */
    Account* first = &from;
    Account* second = &to;
    
    if (from.id > to.id) {
        std::swap(first, second);
    }
    
    std::lock_guard<std::mutex> lock1(first->mutex);
    std::lock_guard<std::mutex> lock2(second->mutex);
    
    if (from.balance >= amount) {
        from.balance -= amount;
        to.balance += amount;
    }
}

// SOLUTION 4: try_lock with timeout (Avoiding indefinite wait)
void transfer_try(Account& from, Account& to, int amount) {
    /*
     * EXPLANATION:
     * Try to acquire locks. If fail, release and retry.
     * Breaks HOLD AND WAIT condition.
     */
    while (true) {
        if (from.mutex.try_lock()) {
            if (to.mutex.try_lock()) {
                // Got both locks
                if (from.balance >= amount) {
                    from.balance -= amount;
                    to.balance += amount;
                }
                to.mutex.unlock();
                from.mutex.unlock();
                return;
            }
            from.mutex.unlock();  // Release first lock
        }
        std::this_thread::sleep_for(std::chrono::milliseconds(1));  // Backoff
    }
}

int main() {
    Account acc1(1, 1000);
    Account acc2(2, 1000);
    
    std::vector<std::thread> threads;
    
    // Multiple threads transferring in both directions
    for (int i = 0; i < 5; ++i) {
        threads.emplace_back(transfer_safe, std::ref(acc1), std::ref(acc2), 100);
        threads.emplace_back(transfer_safe, std::ref(acc2), std::ref(acc1), 50);
    }
    
    for (auto& t : threads) t.join();
    
    std::cout << "Account 1: " << acc1.balance << std::endl;
    std::cout << "Account 2: " << acc2.balance << std::endl;
    std::cout << "Total: " << acc1.balance + acc2.balance << " (should be 2000)" << std::endl;
    
    return 0;
}

