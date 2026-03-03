/*
 * QUESTION 2: Reader-Writer Lock (Rubrik/Glean Favorite)
 * =======================================================
 * 
 * Problem: Implement a lock allowing multiple readers OR one exclusive writer.
 * 
 * Key Concepts: std::shared_mutex (C++17), custom RW lock implementation
 * 
 * Compile: g++ -std=c++17 -pthread 02_reader_writer_lock.cpp -o rw_lock
 */

#include <iostream>
#include <thread>
#include <mutex>
#include <shared_mutex>
#include <condition_variable>
#include <vector>
#include <chrono>

// Custom Reader-Writer Lock (Reader Preference)
class ReadWriteLock {
    /*
     * EXPLANATION:
     * - First reader acquires write_mutex (blocks writers)
     * - Additional readers increment count
     * - Last reader releases write_mutex
     * - WARNING: Can starve writers!
     */
private:
    std::mutex read_mutex_;
    std::mutex write_mutex_;
    int readers_ = 0;

public:
    void lock_read() {
        std::lock_guard<std::mutex> lock(read_mutex_);
        if (++readers_ == 1) {
            write_mutex_.lock();  // First reader blocks writers
        }
    }

    void unlock_read() {
        std::lock_guard<std::mutex> lock(read_mutex_);
        if (--readers_ == 0) {
            write_mutex_.unlock();  // Last reader allows writers
        }
    }

    void lock_write() {
        write_mutex_.lock();
    }

    void unlock_write() {
        write_mutex_.unlock();
    }
};

// Fair Reader-Writer Lock (No Starvation)
class FairReadWriteLock {
    /*
     * EXPLANATION:
     * order_mutex ensures FIFO ordering.
     * Writers block new readers when waiting.
     */
private:
    std::mutex read_mutex_;
    std::mutex write_mutex_;
    std::mutex order_mutex_;
    int readers_ = 0;

public:
    void lock_read() {
        std::lock_guard<std::mutex> order_lock(order_mutex_);
        std::lock_guard<std::mutex> lock(read_mutex_);
        if (++readers_ == 1) {
            write_mutex_.lock();
        }
    }

    void unlock_read() {
        std::lock_guard<std::mutex> lock(read_mutex_);
        if (--readers_ == 0) {
            write_mutex_.unlock();
        }
    }

    void lock_write() {
        order_mutex_.lock();
        write_mutex_.lock();
        order_mutex_.unlock();
    }

    void unlock_write() {
        write_mutex_.unlock();
    }
};

// Using C++17 std::shared_mutex (Recommended in production)
class SharedData {
private:
    mutable std::shared_mutex mutex_;
    int value_ = 0;

public:
    int read() const {
        std::shared_lock<std::shared_mutex> lock(mutex_);  // Multiple readers OK
        return value_;
    }

    void write(int value) {
        std::unique_lock<std::shared_mutex> lock(mutex_);  // Exclusive access
        value_ = value;
    }
};

SharedData shared_data;
FairReadWriteLock rw_lock;

void reader(int id) {
    for (int i = 0; i < 5; ++i) {
        rw_lock.lock_read();
        std::cout << "Reader " << id << " read: " << shared_data.read() << std::endl;
        std::this_thread::sleep_for(std::chrono::milliseconds(50));
        rw_lock.unlock_read();
    }
}

void writer(int id) {
    for (int i = 0; i < 3; ++i) {
        rw_lock.lock_write();
        shared_data.write(shared_data.read() + 1);
        std::cout << "Writer " << id << " wrote: " << shared_data.read() << std::endl;
        std::this_thread::sleep_for(std::chrono::milliseconds(100));
        rw_lock.unlock_write();
    }
}

int main() {
    std::vector<std::thread> threads;
    
    for (int i = 0; i < 3; ++i) threads.emplace_back(reader, i);
    for (int i = 0; i < 2; ++i) threads.emplace_back(writer, i);
    
    for (auto& t : threads) t.join();
    
    std::cout << "Final value: " << shared_data.read() << std::endl;
    return 0;
}

