/*
 * QUESTION 20: Thread-Local Storage & Connection Pool (Rubrik/Databricks)
 * ========================================================================
 * 
 * Problem: Implement connection pool with thread-local connections.
 * 
 * Key Concepts: thread_local, connection pooling, resource management
 * 
 * Compile: g++ -std=c++17 -pthread 20_thread_local_connection_pool.cpp -o conn_pool
 */

#include <iostream>
#include <queue>
#include <thread>
#include <mutex>
#include <condition_variable>
#include <memory>
#include <atomic>
#include <vector>

class Connection {
    static std::atomic<int> id_counter_;
public:
    int id;
    Connection() : id(++id_counter_) {
        std::cout << "Connection " << id << " created" << std::endl;
    }
    ~Connection() {
        std::cout << "Connection " << id << " destroyed" << std::endl;
    }
    std::string execute(const std::string& query) {
        return "Result from conn-" + std::to_string(id) + ": " + query;
    }
};
std::atomic<int> Connection::id_counter_{0};

// SOLUTION 1: Thread-Local Connection
class ThreadLocalConnectionManager {
    /*
     * EXPLANATION:
     * thread_local gives each thread its own instance.
     * Connection reused for all operations in that thread.
     * 
     * Benefits:
     * - No lock contention
     * - Connection reuse
     * - Automatic cleanup with thread death
     */
private:
    static thread_local std::unique_ptr<Connection> connection_;

public:
    static Connection& getConnection() {
        if (!connection_) {
            connection_ = std::make_unique<Connection>();
        }
        return *connection_;
    }
};
thread_local std::unique_ptr<Connection> ThreadLocalConnectionManager::connection_;

// SOLUTION 2: Shared Connection Pool
class ConnectionPool {
    /*
     * EXPLANATION:
     * Pool of connections shared by all threads.
     * Threads borrow and return connections.
     * 
     * Benefits:
     * - Limits total connections
     * - Works with any threading model
     * - Connections can be rebalanced
     */
private:
    std::queue<std::unique_ptr<Connection>> pool_;
    std::mutex mutex_;
    std::condition_variable cv_;
    size_t max_size_;
    size_t current_size_ = 0;

public:
    ConnectionPool(size_t max_size) : max_size_(max_size) {}

    std::unique_ptr<Connection> acquire() {
        std::unique_lock<std::mutex> lock(mutex_);
        
        if (!pool_.empty()) {
            auto conn = std::move(pool_.front());
            pool_.pop();
            return conn;
        }
        
        if (current_size_ < max_size_) {
            ++current_size_;
            return std::make_unique<Connection>();
        }
        
        cv_.wait(lock, [this] { return !pool_.empty(); });
        auto conn = std::move(pool_.front());
        pool_.pop();
        return conn;
    }

    void release(std::unique_ptr<Connection> conn) {
        std::lock_guard<std::mutex> lock(mutex_);
        pool_.push(std::move(conn));
        cv_.notify_one();
    }
};

// RAII wrapper
class PooledConnection {
    ConnectionPool& pool_;
    std::unique_ptr<Connection> conn_;
public:
    PooledConnection(ConnectionPool& pool) : pool_(pool), conn_(pool.acquire()) {}
    ~PooledConnection() { pool_.release(std::move(conn_)); }
    Connection& get() { return *conn_; }
};

void demo_thread_local() {
    std::cout << "=== Thread-Local Demo ===" << std::endl;
    
    auto worker = [](int id) {
        for (int i = 0; i < 3; ++i) {
            auto& conn = ThreadLocalConnectionManager::getConnection();
            std::cout << conn.execute("Query " + std::to_string(i)) << std::endl;
        }
    };
    
    std::vector<std::thread> threads;
    for (int i = 0; i < 3; ++i) threads.emplace_back(worker, i);
    for (auto& t : threads) t.join();
}

void demo_pool() {
    std::cout << "\n=== Connection Pool Demo ===" << std::endl;
    
    ConnectionPool pool(3);
    
    auto worker = [&pool](int id) {
        for (int i = 0; i < 3; ++i) {
            PooledConnection conn(pool);
            std::cout << conn.get().execute("Query from worker " + std::to_string(id)) << std::endl;
            std::this_thread::sleep_for(std::chrono::milliseconds(50));
        }
    };
    
    std::vector<std::thread> threads;
    for (int i = 0; i < 5; ++i) threads.emplace_back(worker, i);
    for (auto& t : threads) t.join();
}

int main() {
    demo_thread_local();
    demo_pool();
    return 0;
}

