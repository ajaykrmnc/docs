# Design a Distributed Task Scheduler
**Difficulty:** Hard | **Companies:** Google, Airbnb, Uber, Netflix

---

## Problem Statement

Design a distributed task scheduler that supports cron-based recurring tasks, one-time tasks, task dependencies (DAG execution), and distributed execution across worker nodes.

---

## Requirements

### Functional Requirements
1. Schedule one-time tasks for future execution
2. Schedule recurring tasks using cron expressions
3. Support task dependencies (DAG-based execution)
4. Retry failed tasks with configurable backoff
5. Prioritize tasks based on urgency
6. Cancel or pause scheduled tasks
7. Track task execution history and status

### Non-Functional Requirements
1. Distributed execution across multiple workers
2. Exactly-once execution guarantee
3. Fault-tolerant (handle worker failures)
4. Scalable to millions of tasks
5. Low latency task dispatch

---

## Class Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                      TaskScheduler                              │
├─────────────────────────────────────────────────────────────────┤
│ - taskQueue: PriorityBlockingQueue<ScheduledTask>               │
│ - taskRegistry: Map<String, Task>                               │
│ - workerPool: WorkerPool                                        │
│ - dagExecutor: DAGExecutor                                      │
│ - persistenceStore: TaskStore                                   │
├─────────────────────────────────────────────────────────────────┤
│ + schedule(task: Task, triggerTime: Instant): TaskId            │
│ + scheduleCron(task: Task, cron: String): TaskId                │
│ + scheduleDAG(dag: TaskDAG): DAGExecutionId                     │
│ + cancel(taskId: TaskId): boolean                               │
│ + pause(taskId: TaskId): void                                   │
│ + resume(taskId: TaskId): void                                  │
│ + getStatus(taskId: TaskId): TaskStatus                         │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                          Task                                   │
├─────────────────────────────────────────────────────────────────┤
│ - taskId: String                                                │
│ - name: String                                                  │
│ - payload: Map<String, Object>                                  │
│ - handler: TaskHandler                                          │
│ - priority: Priority                                            │
│ - retryPolicy: RetryPolicy                                      │
│ - timeout: Duration                                             │
│ - resourceRequirements: ResourceSpec                            │
├─────────────────────────────────────────────────────────────────┤
│ + execute(context: ExecutionContext): TaskResult                │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                      CronExpression                             │
├─────────────────────────────────────────────────────────────────┤
│ - seconds: String                                               │
│ - minutes: String                                               │
│ - hours: String                                                 │
│ - dayOfMonth: String                                            │
│ - month: String                                                 │
│ - dayOfWeek: String                                             │
├─────────────────────────────────────────────────────────────────┤
│ + parse(expression: String): CronExpression                     │
│ + getNextExecutionTime(from: Instant): Instant                  │
│ + matches(instant: Instant): boolean                            │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                       WorkerNode                                │
├─────────────────────────────────────────────────────────────────┤
│ - nodeId: String                                                │
│ - capacity: ResourceSpec                                        │
│ - currentLoad: AtomicReference<ResourceSpec>                    │
│ - status: WorkerStatus                                          │
│ - runningTasks: Map<TaskId, TaskExecution>                      │
├─────────────────────────────────────────────────────────────────┤
│ + execute(task: ScheduledTask): CompletableFuture<TaskResult>   │
│ + heartbeat(): WorkerHealth                                     │
│ + getAvailableCapacity(): ResourceSpec                          │
└─────────────────────────────────────────────────────────────────┘
```

---

## Class Implementations

### 1. Task and ScheduledTask
```java
public class Task {
    private final String taskId;
    private final String name;
    private final Map<String, Object> payload;
    private final String handlerClass;
    private final Priority priority;
    private final RetryPolicy retryPolicy;
    private final Duration timeout;
    
    public TaskResult execute(ExecutionContext context) {
        TaskHandler handler = loadHandler(handlerClass);
        return handler.handle(payload, context);
    }
}

public class ScheduledTask implements Comparable<ScheduledTask> {
    private final Task task;
    private final Instant scheduledTime;
    private final CronExpression cronExpression;  // null for one-time
    private final int attemptNumber;
    private TaskStatus status;
    
    @Override
    public int compareTo(ScheduledTask other) {
        int timeCompare = this.scheduledTime.compareTo(other.scheduledTime);
        if (timeCompare != 0) return timeCompare;
        return other.task.getPriority().compareTo(this.task.getPriority());
    }
    
    public ScheduledTask nextOccurrence() {
        if (cronExpression == null) return null;
        Instant nextTime = cronExpression.getNextExecutionTime(Instant.now());
        return new ScheduledTask(task, nextTime, cronExpression, 0);
    }
}

public enum Priority {
    CRITICAL(0), HIGH(1), MEDIUM(2), LOW(3);
    private final int value;
}
```

### 2. Retry Policy
```java
public class RetryPolicy {
    private final int maxRetries;
    private final Duration initialDelay;
    private final double multiplier;
    private final Duration maxDelay;
    private final Set<Class<? extends Exception>> retryableExceptions;
    
    public Duration getDelayForAttempt(int attempt) {
        if (attempt <= 0) return Duration.ZERO;
        
        double delay = initialDelay.toMillis() * Math.pow(multiplier, attempt - 1);
        delay = Math.min(delay, maxDelay.toMillis());
        
        // Add jitter to prevent thundering herd
        delay = delay * (0.5 + Math.random());
        
        return Duration.ofMillis((long) delay);
    }
    
    public boolean shouldRetry(int attempt, Exception exception) {
        if (attempt >= maxRetries) return false;
        return retryableExceptions.isEmpty() || 
               retryableExceptions.stream()
                   .anyMatch(e -> e.isInstance(exception));
    }
    
    public static RetryPolicy exponentialBackoff(int maxRetries) {
        return new RetryPolicy(maxRetries, Duration.ofSeconds(1), 2.0, 
                               Duration.ofMinutes(5), Set.of());
    }
}
```

### 3. DAG Executor
```java
public class DAGExecutor {
    private final TaskScheduler scheduler;
    private final Map<String, DAGExecution> executions;
    
    public DAGExecutionId execute(TaskDAG dag) {
        DAGExecution execution = new DAGExecution(dag);
        executions.put(execution.getId(), execution);
        
        // Start with tasks that have no dependencies
        List<Task> readyTasks = dag.getTasksWithNoDependencies();
        for (Task task : readyTasks) {
            scheduleDAGTask(execution, task);
        }
        
        return execution.getId();
    }
    
    private void scheduleDAGTask(DAGExecution execution, Task task) {
        scheduler.schedule(task, Instant.now())
            .thenAccept(result -> onTaskComplete(execution, task, result));
    }
    
    private void onTaskComplete(DAGExecution execution, Task task, TaskResult result) {
        execution.markComplete(task.getTaskId(), result);
        
        if (result.isSuccess()) {
            List<Task> unlockedTasks = execution.getUnlockedTasks(task.getTaskId());
            for (Task next : unlockedTasks) {
                scheduleDAGTask(execution, next);
            }
        } else {
            execution.handleFailure(task.getTaskId(), result);
        }
    }
}

public class TaskDAG {
    private final Map<String, Task> tasks;
    private final Map<String, Set<String>> dependencies;  // task -> dependencies
    private final Map<String, Set<String>> dependents;    // task -> dependents
    
    public List<Task> getTasksWithNoDependencies() {
        return tasks.values().stream()
            .filter(t -> dependencies.getOrDefault(t.getTaskId(), Set.of()).isEmpty())
            .collect(Collectors.toList());
    }
    
    public void addDependency(String taskId, String dependsOn) {
        dependencies.computeIfAbsent(taskId, k -> new HashSet<>()).add(dependsOn);
        dependents.computeIfAbsent(dependsOn, k -> new HashSet<>()).add(taskId);
    }
}
```

