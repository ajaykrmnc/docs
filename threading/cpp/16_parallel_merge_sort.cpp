/*
 * QUESTION 16: Parallel Merge Sort (Databricks)
 * =============================================
 * 
 * Problem: Implement merge sort using multiple threads.
 * 
 * Key Concepts: Divide and conquer, thread overhead, std::async
 * 
 * Compile: g++ -std=c++17 -pthread 16_parallel_merge_sort.cpp -o parallel_sort
 */

#include <iostream>
#include <vector>
#include <thread>
#include <future>
#include <algorithm>
#include <random>
#include <chrono>

void merge(std::vector<int>& arr, int left, int mid, int right) {
    std::vector<int> temp(right - left + 1);
    int i = left, j = mid + 1, k = 0;
    
    while (i <= mid && j <= right) {
        temp[k++] = (arr[i] <= arr[j]) ? arr[i++] : arr[j++];
    }
    while (i <= mid) temp[k++] = arr[i++];
    while (j <= right) temp[k++] = arr[j++];
    
    std::copy(temp.begin(), temp.end(), arr.begin() + left);
}

void sequentialMergeSort(std::vector<int>& arr, int left, int right) {
    if (left >= right) return;
    int mid = left + (right - left) / 2;
    sequentialMergeSort(arr, left, mid);
    sequentialMergeSort(arr, mid + 1, right);
    merge(arr, left, mid, right);
}

class ParallelMergeSort {
    /*
     * EXPLANATION:
     * - Split array and sort halves in parallel
     * - Use depth limit to avoid too many threads
     * - Fall back to sequential below threshold
     * 
     * IMPORTANT: Thread creation overhead can exceed benefit!
     */
private:
    int max_depth_;
    
    void parallelSort(std::vector<int>& arr, int left, int right, int depth) {
        if (left >= right) return;
        
        int mid = left + (right - left) / 2;
        
        if (depth < max_depth_) {
            // Use std::async for parallel execution
            auto left_future = std::async(std::launch::async,
                [this, &arr, left, mid, depth]() {
                    parallelSort(arr, left, mid, depth + 1);
                });
            
            parallelSort(arr, mid + 1, right, depth + 1);
            left_future.get();
        } else {
            sequentialMergeSort(arr, left, mid);
            sequentialMergeSort(arr, mid + 1, right);
        }
        
        merge(arr, left, mid, right);
    }

public:
    ParallelMergeSort(int max_depth = 3) : max_depth_(max_depth) {}
    
    void sort(std::vector<int>& arr) {
        if (arr.empty()) return;
        parallelSort(arr, 0, arr.size() - 1, 0);
    }
};

// Using std::thread directly
void parallelMergeSortThread(std::vector<int>& arr, int left, int right, int depth) {
    if (left >= right) return;
    
    int mid = left + (right - left) / 2;
    
    if (depth < 3) {
        std::thread left_thread(parallelMergeSortThread, 
                                std::ref(arr), left, mid, depth + 1);
        parallelMergeSortThread(arr, mid + 1, right, depth + 1);
        left_thread.join();
    } else {
        sequentialMergeSort(arr, left, mid);
        sequentialMergeSort(arr, mid + 1, right);
    }
    
    merge(arr, left, mid, right);
}

void benchmark() {
    std::vector<int> sizes = {10000, 50000, 100000};
    std::random_device rd;
    std::mt19937 gen(rd());
    
    for (int size : sizes) {
        std::vector<int> arr(size);
        std::generate(arr.begin(), arr.end(), [&]() { return gen() % 1000000; });
        
        auto arr_copy = arr;
        
        // Sequential
        auto start = std::chrono::high_resolution_clock::now();
        sequentialMergeSort(arr, 0, arr.size() - 1);
        auto seq_time = std::chrono::high_resolution_clock::now() - start;
        
        // Parallel
        start = std::chrono::high_resolution_clock::now();
        ParallelMergeSort sorter(3);
        sorter.sort(arr_copy);
        auto par_time = std::chrono::high_resolution_clock::now() - start;
        
        auto seq_ms = std::chrono::duration_cast<std::chrono::milliseconds>(seq_time).count();
        auto par_ms = std::chrono::duration_cast<std::chrono::milliseconds>(par_time).count();
        
        std::cout << "Size " << size << ": Sequential=" << seq_ms << "ms, Parallel=" 
                  << par_ms << "ms, Speedup=" << (double)seq_ms/par_ms << "x" << std::endl;
    }
}

int main() {
    benchmark();
    return 0;
}

