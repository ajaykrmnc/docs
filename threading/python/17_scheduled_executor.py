"""
QUESTION 17: Scheduled Executor Service (Rubrik/Glean)
======================================================

Problem: Implement a scheduler that executes tasks at specified times or intervals.

Key Concepts: Priority queues, Timer threads, Periodic execution
"""

import threading
import heapq
import time
from typing import Callable, Optional
from dataclasses import dataclass, field


@dataclass(order=True)
class ScheduledTask:
    """Task with scheduled execution time."""
    execute_time: float
    task_id: int = field(compare=False)
    func: Callable = field(compare=False)
    interval: Optional[float] = field(default=None, compare=False)
    cancelled: bool = field(default=False, compare=False)


class ScheduledExecutor:
    """
    Scheduled Executor Service.
    
    EXPLANATION:
    Architecture:
    1. Min-heap priority queue (ordered by execute_time)
    2. Worker thread waits until next task is due
    3. Supports one-time and periodic tasks
    
    Key Design:
    - Use Condition to wait with timeout
    - Wake up when new task added (might be earlier)
    - Periodic tasks re-add themselves after execution
    """
    
    def __init__(self, num_workers: int = 1):
        self._task_queue = []  # min-heap
        self._lock = threading.Lock()
        self._condition = threading.Condition(self._lock)
        self._shutdown = False
        self._task_id = 0
        
        self._workers = [
            threading.Thread(target=self._worker_loop, daemon=True)
            for _ in range(num_workers)
        ]
        for w in self._workers:
            w.start()
    
    def _next_task_id(self):
        self._task_id += 1
        return self._task_id
    
    def schedule(self, func: Callable, delay: float) -> int:
        """Schedule one-time task after delay seconds."""
        task = ScheduledTask(
            execute_time=time.time() + delay,
            task_id=self._next_task_id(),
            func=func
        )
        
        with self._condition:
            heapq.heappush(self._task_queue, task)
            self._condition.notify()  # Wake worker
        
        return task.task_id
    
    def schedule_periodic(self, func: Callable, delay: float, interval: float) -> int:
        """Schedule periodic task."""
        task = ScheduledTask(
            execute_time=time.time() + delay,
            task_id=self._next_task_id(),
            func=func,
            interval=interval
        )
        
        with self._condition:
            heapq.heappush(self._task_queue, task)
            self._condition.notify()
        
        return task.task_id
    
    def cancel(self, task_id: int) -> bool:
        """Cancel a scheduled task."""
        with self._lock:
            for task in self._task_queue:
                if task.task_id == task_id:
                    task.cancelled = True
                    return True
        return False
    
    def _worker_loop(self):
        while True:
            with self._condition:
                while not self._shutdown and not self._task_queue:
                    self._condition.wait()
                
                if self._shutdown:
                    return
                
                # Wait until next task is due
                task = self._task_queue[0]
                wait_time = task.execute_time - time.time()
                
                if wait_time > 0:
                    # Wait, but wake if new task added
                    self._condition.wait(timeout=wait_time)
                    continue
                
                # Remove task from queue
                heapq.heappop(self._task_queue)
            
            # Execute task (outside lock!)
            if not task.cancelled:
                try:
                    task.func()
                except Exception as e:
                    print(f"Task error: {e}")
                
                # Re-schedule if periodic
                if task.interval and not task.cancelled:
                    task.execute_time = time.time() + task.interval
                    with self._condition:
                        heapq.heappush(self._task_queue, task)
                        self._condition.notify()
    
    def shutdown(self, wait: bool = True):
        with self._condition:
            self._shutdown = True
            self._condition.notify_all()
        
        if wait:
            for w in self._workers:
                w.join(timeout=1)


def demo():
    executor = ScheduledExecutor()
    
    executor.schedule(lambda: print(f"One-time task at {time.time():.2f}"), delay=0.5)
    
    task_id = executor.schedule_periodic(
        lambda: print(f"Periodic task at {time.time():.2f}"),
        delay=0.2, interval=0.3
    )
    
    time.sleep(1.5)
    executor.cancel(task_id)
    print("Periodic task cancelled")
    
    time.sleep(0.5)
    executor.shutdown()
    print("Executor shut down")


if __name__ == "__main__":
    demo()

