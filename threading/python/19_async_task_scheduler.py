"""
QUESTION 19: Async Task Scheduler with Dependencies (Databricks/Glean)
======================================================================

Problem: Execute tasks respecting dependencies. Task B depends on A means
A must complete before B starts. Maximize parallelism.

Key Concepts: DAG scheduling, Topological sort, Dependency resolution
"""

import threading
from collections import defaultdict, deque
from typing import Dict, List, Set, Callable
from concurrent.futures import ThreadPoolExecutor, Future
import time


class Task:
    """Represents a task with dependencies."""
    
    def __init__(self, task_id: str, func: Callable):
        self.id = task_id
        self.func = func
        self.dependencies: Set[str] = set()
        self.dependents: Set[str] = set()


class DAGTaskScheduler:
    """
    DAG-based Task Scheduler.
    
    EXPLANATION:
    Algorithm (Kahn's topological sort with parallelism):
    1. Build dependency graph
    2. Find tasks with no dependencies (ready to run)
    3. Run ready tasks in parallel
    4. When task completes, update dependents
    5. Add newly ready tasks to queue
    6. Repeat until all done
    
    This naturally maximizes parallelism while respecting dependencies.
    """
    
    def __init__(self, num_workers: int = 4):
        self.tasks: Dict[str, Task] = {}
        self.num_workers = num_workers
    
    def add_task(self, task_id: str, func: Callable, 
                 dependencies: List[str] = None):
        """Add a task with optional dependencies."""
        task = Task(task_id, func)
        if dependencies:
            task.dependencies = set(dependencies)
        self.tasks[task_id] = task
        
        # Update dependency graph
        for dep_id in task.dependencies:
            if dep_id in self.tasks:
                self.tasks[dep_id].dependents.add(task_id)
    
    def execute(self) -> Dict[str, any]:
        """Execute all tasks respecting dependencies."""
        results = {}
        in_degree = {t: len(self.tasks[t].dependencies) for t in self.tasks}
        
        # Find initial ready tasks (no dependencies)
        ready = deque([t for t in self.tasks if in_degree[t] == 0])
        
        lock = threading.Lock()
        completed = threading.Event()
        remaining = len(self.tasks)
        
        def on_task_complete(task_id: str, result):
            nonlocal remaining
            
            with lock:
                results[task_id] = result
                remaining -= 1
                
                # Update dependents
                for dep_id in self.tasks[task_id].dependents:
                    in_degree[dep_id] -= 1
                    if in_degree[dep_id] == 0:
                        ready.append(dep_id)
                
                if remaining == 0:
                    completed.set()
        
        with ThreadPoolExecutor(max_workers=self.num_workers) as executor:
            futures: Dict[str, Future] = {}
            
            while remaining > 0:
                # Submit ready tasks
                while ready:
                    task_id = ready.popleft()
                    task = self.tasks[task_id]
                    
                    def run_task(tid, func):
                        result = func()
                        on_task_complete(tid, result)
                        return result
                    
                    futures[task_id] = executor.submit(run_task, task_id, task.func)
                
                # Wait a bit for tasks to complete
                if remaining > 0 and not ready:
                    completed.wait(timeout=0.1)
        
        return results


class SimpleDAGScheduler:
    """
    Simpler implementation using futures.
    
    EXPLANATION:
    Each task waits for its dependencies' futures.
    Naturally handles ordering without explicit graph management.
    """
    
    def __init__(self, num_workers: int = 4):
        self.tasks: Dict[str, Callable] = {}
        self.dependencies: Dict[str, List[str]] = defaultdict(list)
        self.num_workers = num_workers
    
    def add_task(self, task_id: str, func: Callable, deps: List[str] = None):
        self.tasks[task_id] = func
        if deps:
            self.dependencies[task_id] = deps
    
    def execute(self) -> Dict[str, any]:
        futures: Dict[str, Future] = {}
        
        with ThreadPoolExecutor(max_workers=self.num_workers) as executor:
            def submit_task(task_id: str) -> Future:
                if task_id in futures:
                    return futures[task_id]
                
                # Submit dependencies first
                dep_futures = [submit_task(d) for d in self.dependencies[task_id]]
                
                def run():
                    # Wait for dependencies
                    for f in dep_futures:
                        f.result()
                    return self.tasks[task_id]()
                
                futures[task_id] = executor.submit(run)
                return futures[task_id]
            
            # Submit all tasks
            for task_id in self.tasks:
                submit_task(task_id)
            
            # Wait and collect results
            return {tid: f.result() for tid, f in futures.items()}


def demo():
    scheduler = DAGTaskScheduler(num_workers=4)
    
    #     A
    #    / \
    #   B   C
    #    \ /
    #     D
    
    scheduler.add_task("A", lambda: (print("A"), time.sleep(0.1), "A")[2])
    scheduler.add_task("B", lambda: (print("B"), time.sleep(0.1), "B")[2], ["A"])
    scheduler.add_task("C", lambda: (print("C"), time.sleep(0.1), "C")[2], ["A"])
    scheduler.add_task("D", lambda: (print("D"), "D")[1], ["B", "C"])
    
    results = scheduler.execute()
    print(f"Results: {results}")


if __name__ == "__main__":
    demo()

