"""
QUESTION 16: Parallel Merge Sort (Databricks)
=============================================

Problem: Implement merge sort using multiple threads for parallel sorting.

Key Concepts: Divide and conquer with threads, Thread overhead, Optimal parallelism
"""

import threading
from typing import List
import random
import time
from concurrent.futures import ThreadPoolExecutor


def merge(left: List[int], right: List[int]) -> List[int]:
    """Merge two sorted lists."""
    result = []
    i = j = 0
    
    while i < len(left) and j < len(right):
        if left[i] <= right[j]:
            result.append(left[i])
            i += 1
        else:
            result.append(right[j])
            j += 1
    
    result.extend(left[i:])
    result.extend(right[j:])
    return result


def sequential_merge_sort(arr: List[int]) -> List[int]:
    """Standard sequential merge sort."""
    if len(arr) <= 1:
        return arr
    
    mid = len(arr) // 2
    left = sequential_merge_sort(arr[:mid])
    right = sequential_merge_sort(arr[mid:])
    return merge(left, right)


class ParallelMergeSort:
    """
    Parallel Merge Sort using threads.
    
    EXPLANATION:
    - Split array into halves
    - Sort each half in separate thread
    - Merge results
    
    IMPORTANT: Don't create too many threads!
    - Thread creation overhead can exceed benefit
    - Use depth limit to control parallelism
    - Fall back to sequential below threshold
    """
    
    def __init__(self, max_depth: int = 3):
        self.max_depth = max_depth
    
    def sort(self, arr: List[int]) -> List[int]:
        return self._parallel_sort(arr, 0)
    
    def _parallel_sort(self, arr: List[int], depth: int) -> List[int]:
        if len(arr) <= 1:
            return arr
        
        mid = len(arr) // 2
        
        # Use threads only up to max_depth
        if depth < self.max_depth:
            left_result = [None]
            right_result = [None]
            
            def sort_left():
                left_result[0] = self._parallel_sort(arr[:mid], depth + 1)
            
            def sort_right():
                right_result[0] = self._parallel_sort(arr[mid:], depth + 1)
            
            left_thread = threading.Thread(target=sort_left)
            right_thread = threading.Thread(target=sort_right)
            
            left_thread.start()
            right_thread.start()
            
            left_thread.join()
            right_thread.join()
            
            return merge(left_result[0], right_result[0])
        else:
            # Fall back to sequential
            left = sequential_merge_sort(arr[:mid])
            right = sequential_merge_sort(arr[mid:])
            return merge(left, right)


class ParallelMergeSortPool:
    """
    Using ThreadPoolExecutor (Better approach).
    
    EXPLANATION:
    Thread pool avoids thread creation overhead.
    Fixed number of workers process tasks.
    """
    
    def __init__(self, num_workers: int = 4):
        self.num_workers = num_workers
    
    def sort(self, arr: List[int]) -> List[int]:
        if len(arr) <= 1000:  # Threshold for parallelism
            return sequential_merge_sort(arr)
        
        with ThreadPoolExecutor(max_workers=self.num_workers) as executor:
            # Split into chunks
            chunk_size = len(arr) // self.num_workers
            chunks = [arr[i:i+chunk_size] for i in range(0, len(arr), chunk_size)]
            
            # Sort chunks in parallel
            futures = [executor.submit(sequential_merge_sort, chunk) for chunk in chunks]
            sorted_chunks = [f.result() for f in futures]
            
            # Merge all chunks
            while len(sorted_chunks) > 1:
                merged = []
                for i in range(0, len(sorted_chunks), 2):
                    if i + 1 < len(sorted_chunks):
                        merged.append(merge(sorted_chunks[i], sorted_chunks[i+1]))
                    else:
                        merged.append(sorted_chunks[i])
                sorted_chunks = merged
            
            return sorted_chunks[0]


def benchmark():
    sizes = [10000, 50000, 100000]
    
    for size in sizes:
        arr = [random.randint(0, 1000000) for _ in range(size)]
        
        # Sequential
        start = time.time()
        result1 = sequential_merge_sort(arr.copy())
        seq_time = time.time() - start
        
        # Parallel
        sorter = ParallelMergeSort(max_depth=3)
        start = time.time()
        result2 = sorter.sort(arr.copy())
        par_time = time.time() - start
        
        assert result1 == result2, "Results don't match!"
        print(f"Size {size}: Sequential={seq_time:.3f}s, Parallel={par_time:.3f}s, "
              f"Speedup={seq_time/par_time:.2f}x")


if __name__ == "__main__":
    benchmark()

