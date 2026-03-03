"""
QUESTION 5: Implement a Thread Pool (Databricks/Glean Favorite)
===============================================================

Problem Statement:
------------------
Implement a thread pool that:
1. Maintains a fixed number of worker threads
2. Accepts tasks via a submit method
3. Returns Future objects for task results
4. Supports graceful shutdown

Companies: Databricks (Spark uses thread pools), Glean (parallel indexing)

Key Concepts:
- Thread pool pattern
- Task queuing
- Future/Promise pattern
- Graceful shutdown
"""

import threading
import queue
import time
from typing import Callable, Any, Optional
from dataclasses import dataclass
import traceback


@dataclass
class Task:
    """Represents a task to be executed"""
    func: Callable
    args: tuple
    kwargs: dict
    future: 'Future'


class Future:
    """
    Represents a future result of an async computation.
    
    EXPLANATION:
    ------------
    A Future is a placeholder for a result that will be available later.
    - get() blocks until result is ready
    - Uses Condition variable to signal completion
    - Stores exception if task fails
    """
    
    def __init__(self):
        self._result = None
        self._exception = None
        self._done = False
        self._condition = threading.Condition()
    
    def set_result(self, result: Any):
        """Set the result and wake up waiting threads"""
        with self._condition:
            self._result = result
            self._done = True
            self._condition.notify_all()
    
    def set_exception(self, exc: Exception):
        """Set exception if task failed"""
        with self._condition:
            self._exception = exc
            self._done = True
            self._condition.notify_all()
    
    def get(self, timeout: Optional[float] = None) -> Any:
        """
        Get the result, blocking until available.
        
        CRITICAL: This is how caller waits for async result!
        """
        with self._condition:
            while not self._done:
                if not self._condition.wait(timeout):
                    raise TimeoutError("Future timed out")
            
            if self._exception:
                raise self._exception
            return self._result
    
    def is_done(self) -> bool:
        return self._done


class ThreadPool:
    """
    Fixed-size thread pool implementation.
    
    EXPLANATION:
    ------------
    Architecture:
    1. Task Queue: Holds pending tasks (thread-safe queue)
    2. Worker Threads: Pull tasks from queue and execute them
    3. Shutdown flag: Signals workers to stop
    
    Why Thread Pools?
    - Avoid thread creation overhead
    - Control resource usage
    - Reuse threads for multiple tasks
    """
    
    def __init__(self, num_workers: int):
        self.num_workers = num_workers
        self.task_queue = queue.Queue()
        self.workers = []
        self.shutdown_flag = False
        self._lock = threading.Lock()
        
        # Start worker threads
        for i in range(num_workers):
            worker = threading.Thread(target=self._worker_loop, name=f"Worker-{i}")
            worker.daemon = True  # Daemon threads exit when main thread exits
            worker.start()
            self.workers.append(worker)
    
    def _worker_loop(self):
        """
        Worker thread main loop.
        
        Continuously pulls tasks from queue and executes them.
        Uses None as poison pill for shutdown.
        """
        while True:
            try:
                task = self.task_queue.get(timeout=0.1)
                
                # Check for poison pill
                if task is None:
                    break
                
                # Execute task
                try:
                    result = task.func(*task.args, **task.kwargs)
                    task.future.set_result(result)
                except Exception as e:
                    task.future.set_exception(e)
                finally:
                    self.task_queue.task_done()
                    
            except queue.Empty:
                if self.shutdown_flag:
                    break
    
    def submit(self, func: Callable, *args, **kwargs) -> Future:
        """
        Submit a task for execution.
        
        Returns a Future that will contain the result.
        """
        if self.shutdown_flag:
            raise RuntimeError("ThreadPool is shut down")
        
        future = Future()
        task = Task(func=func, args=args, kwargs=kwargs, future=future)
        self.task_queue.put(task)
        return future
    
    def shutdown(self, wait: bool = True):
        """
        Shutdown the thread pool.
        
        If wait=True, waits for all tasks to complete.
        """
        self.shutdown_flag = True
        
        if wait:
            self.task_queue.join()  # Wait for all tasks
        
        # Send poison pills to stop workers
        for _ in self.workers:
            self.task_queue.put(None)
        
        # Wait for workers to finish
        for worker in self.workers:
            worker.join(timeout=1)


def example_task(n: int) -> int:
    """Example task that squares a number"""
    time.sleep(0.1)  # Simulate work
    return n * n


def main():
    pool = ThreadPool(num_workers=4)
    
    # Submit 10 tasks
    futures = [pool.submit(example_task, i) for i in range(10)]
    
    # Get results
    results = [f.get() for f in futures]
    print(f"Results: {results}")
    
    # Shutdown
    pool.shutdown()
    print("Pool shutdown complete")


if __name__ == "__main__":
    main()

