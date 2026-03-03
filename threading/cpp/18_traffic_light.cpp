/*
 * QUESTION 18: Traffic Light Controlled Intersection (LeetCode 1279)
 * ==================================================================
 * 
 * Problem: Cars from two roads approach intersection. Control traffic light
 * to ensure cars from only one road pass at a time.
 * 
 * Key Concepts: Mutual exclusion, state machines, thread coordination
 * 
 * Compile: g++ -std=c++17 -pthread 18_traffic_light.cpp -o traffic_light
 */

#include <iostream>
#include <thread>
#include <mutex>
#include <vector>
#include <random>
#include <functional>

enum class Road { A = 1, B = 2 };

class TrafficLight {
    /*
     * EXPLANATION:
     * Only one road has green at a time.
     * Change light only when car from other road arrives.
     * Minimize unnecessary light changes.
     */
private:
    Road current_green_ = Road::A;
    std::mutex mutex_;

public:
    void carArrived(int carId, Road road,
                    std::function<void()> turnGreen,
                    std::function<void()> crossCar) {
        std::lock_guard<std::mutex> lock(mutex_);
        
        if (current_green_ != road) {
            turnGreen();
            current_green_ = road;
        }
        
        crossCar();
    }
};

class TrafficLightFair {
    /*
     * EXPLANATION:
     * Fair version: Track consecutive cars per road.
     * Switch after N cars to prevent starvation.
     */
private:
    Road current_green_ = Road::A;
    int consecutive_count_ = 0;
    const int max_consecutive_ = 5;
    std::mutex mutex_;
    std::condition_variable cv_;
    int waiting_a_ = 0;
    int waiting_b_ = 0;

public:
    void carArrived(int carId, Road road,
                    std::function<void()> turnGreen,
                    std::function<void()> crossCar) {
        std::unique_lock<std::mutex> lock(mutex_);
        
        if (road == Road::A) ++waiting_a_;
        else ++waiting_b_;
        
        // Wait for green or forced switch
        cv_.wait(lock, [&]() {
            if (current_green_ == road) return true;
            
            // Force switch for fairness
            Road other = (road == Road::A) ? Road::B : Road::A;
            int other_waiting = (road == Road::A) ? waiting_b_ : waiting_a_;
            
            if (consecutive_count_ >= max_consecutive_ && other_waiting == 0) {
                current_green_ = road;
                consecutive_count_ = 0;
                turnGreen();
                return true;
            }
            return false;
        });
        
        if (road == Road::A) --waiting_a_;
        else --waiting_b_;
        
        ++consecutive_count_;
        crossCar();
        
        cv_.notify_all();
    }
};

int main() {
    TrafficLight light;
    std::mutex cout_mutex;
    
    auto car = [&](int carId, Road road) {
        std::this_thread::sleep_for(std::chrono::milliseconds(rand() % 100));
        
        auto turnGreen = [&]() {
            std::lock_guard<std::mutex> lock(cout_mutex);
            std::cout << "Light changed to Road " 
                      << (road == Road::A ? "A" : "B") << std::endl;
        };
        
        auto crossCar = [&]() {
            std::lock_guard<std::mutex> lock(cout_mutex);
            std::cout << "Car " << carId << " from Road " 
                      << (road == Road::A ? "A" : "B") << " crossed" << std::endl;
        };
        
        light.carArrived(carId, road, turnGreen, crossCar);
    };
    
    std::vector<std::thread> threads;
    
    // Cars from Road A
    for (int i = 0; i < 5; ++i) {
        threads.emplace_back(car, i, Road::A);
    }
    
    // Cars from Road B
    for (int i = 5; i < 10; ++i) {
        threads.emplace_back(car, i, Road::B);
    }
    
    for (auto& t : threads) t.join();
    
    std::cout << "All cars passed!" << std::endl;
    return 0;
}

