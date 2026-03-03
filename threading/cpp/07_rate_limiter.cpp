/*
 * QUESTION 7: Implement a Rate Limiter (Glean/Databricks)
 * =======================================================
 * 
 * Problem: Limit requests to N per second using various algorithms.
 * 
 * Key Concepts: Token bucket, Sliding window, Atomic operations
 * 
 * Compile: g++ -std=c++17 -pthread 07_rate_limiter.cpp -o rate_limiter
 */

#include <iostream>
#include <mutex>
#include <chrono>
#include <deque>
#include <thread>
#include <atomic>

using Clock = std::chrono::steady_clock;
using TimePoint = Clock::time_point;

class TokenBucketRateLimiter {
    /*
     * EXPLANATION (Token Bucket Algorithm):
     * 1. Bucket holds tokens (up to capacity)
     * 2. Tokens added at fixed rate per second
     * 3. Each request consumes one token
     * 4. If no tokens, request rejected
     * 
     * Properties:
     * - Allows bursts up to capacity
     * - Smooths traffic over time
     */
private:
    double tokens_;
    double rate_;         // tokens per second
    size_t capacity_;
    TimePoint last_refill_;
    std::mutex mutex_;

    void refill() {
        auto now = Clock::now();
        double elapsed = std::chrono::duration<double>(now - last_refill_).count();
        tokens_ = std::min(static_cast<double>(capacity_), tokens_ + elapsed * rate_);
        last_refill_ = now;
    }

public:
    TokenBucketRateLimiter(double rate, size_t capacity)
        : tokens_(capacity), rate_(rate), capacity_(capacity), last_refill_(Clock::now()) {}

    bool acquire(size_t tokens = 1) {
        std::lock_guard<std::mutex> lock(mutex_);
        refill();
        if (tokens_ >= tokens) {
            tokens_ -= tokens;
            return true;
        }
        return false;
    }
};

class SlidingWindowRateLimiter {
    /*
     * EXPLANATION (Sliding Window Algorithm):
     * Track request timestamps in sliding window.
     * More accurate than fixed windows but uses more memory.
     * 
     * Algorithm:
     * 1. Remove timestamps older than window
     * 2. If count < limit, allow and add timestamp
     * 3. Otherwise reject
     */
private:
    std::deque<TimePoint> timestamps_;
    size_t max_requests_;
    std::chrono::milliseconds window_;
    std::mutex mutex_;

public:
    SlidingWindowRateLimiter(size_t max_requests, std::chrono::milliseconds window)
        : max_requests_(max_requests), window_(window) {}

    bool allow_request() {
        std::lock_guard<std::mutex> lock(mutex_);
        auto now = Clock::now();
        auto cutoff = now - window_;
        
        // Remove old timestamps
        while (!timestamps_.empty() && timestamps_.front() < cutoff) {
            timestamps_.pop_front();
        }
        
        if (timestamps_.size() < max_requests_) {
            timestamps_.push_back(now);
            return true;
        }
        return false;
    }
};

class LeakyBucketRateLimiter {
    /*
     * EXPLANATION (Leaky Bucket Algorithm):
     * - Requests fill bucket
     * - Bucket "leaks" at constant rate
     * - If bucket full, requests rejected
     * - Produces smooth, constant output rate
     */
private:
    double water_;
    double rate_;         // leak rate per second
    double capacity_;
    TimePoint last_leak_;
    std::mutex mutex_;

public:
    LeakyBucketRateLimiter(double rate, double capacity)
        : water_(0), rate_(rate), capacity_(capacity), last_leak_(Clock::now()) {}

    bool allow_request() {
        std::lock_guard<std::mutex> lock(mutex_);
        auto now = Clock::now();
        double elapsed = std::chrono::duration<double>(now - last_leak_).count();
        water_ = std::max(0.0, water_ - elapsed * rate_);
        last_leak_ = now;
        
        if (water_ < capacity_) {
            water_ += 1.0;
            return true;
        }
        return false;
    }
};

int main() {
    SlidingWindowRateLimiter limiter(5, std::chrono::milliseconds(1000));
    
    for (int i = 0; i < 10; ++i) {
        bool allowed = limiter.allow_request();
        std::cout << "Request " << i << ": " << (allowed ? "ALLOWED" : "REJECTED") << std::endl;
        std::this_thread::sleep_for(std::chrono::milliseconds(100));
    }
    
    return 0;
}

