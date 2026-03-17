# Design an Elevator System
**Difficulty:** Medium-Hard | **Companies:** Google, Amazon, Microsoft, Uber

---

## Problem Statement

Design an elevator control system for a building with multiple elevators, supporting multiple scheduling algorithms, VIP/emergency modes, and real-time status display.

---

## Requirements

### Functional Requirements
1. Multiple elevators serving multiple floors
2. Handle up/down requests from floors
3. Handle floor selection from inside elevator
4. Multiple scheduling algorithms (SCAN, LOOK, FCFS)
5. VIP and emergency override modes
6. Weight limit enforcement
7. Display current status on each floor

### Non-Functional Requirements
1. Minimize average wait time
2. Fair distribution of load across elevators
3. Handle concurrent requests safely
4. Real-time status updates

---

## Class Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                   ElevatorController                            │
├─────────────────────────────────────────────────────────────────┤
│ - elevators: List<Elevator>                                     │
│ - floors: List<Floor>                                           │
│ - scheduler: ElevatorScheduler                                  │
│ - pendingRequests: Queue<Request>                               │
├─────────────────────────────────────────────────────────────────┤
│ + requestElevator(floor: int, direction: Direction): void       │
│ + selectFloor(elevatorId: int, floor: int): void                │
│ + setEmergencyMode(elevatorId: int): void                       │
│ + getStatus(): List<ElevatorStatus>                             │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                        Elevator                                 │
├─────────────────────────────────────────────────────────────────┤
│ - id: int                                                       │
│ - currentFloor: int                                             │
│ - direction: Direction                                          │
│ - state: ElevatorState                                          │
│ - destinationFloors: TreeSet<Integer>                           │
│ - currentWeight: double                                         │
│ - maxWeight: double                                             │
│ - door: Door                                                    │
├─────────────────────────────────────────────────────────────────┤
│ + addDestination(floor: int): boolean                           │
│ + move(): void                                                  │
│ + openDoor(): void                                              │
│ + closeDoor(): void                                             │
│ + isOverweight(): boolean                                       │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                 <<interface>> ElevatorScheduler                 │
├─────────────────────────────────────────────────────────────────┤
│ + schedule(request: Request, elevators: List<Elevator>): Elevator│
│ + optimizeRoute(elevator: Elevator): List<Integer>              │
└─────────────────────────────────────────────────────────────────┘
         △
         │
    ┌────┴────┬────────────┬─────────────┐
    │         │            │             │
┌───┴──┐  ┌───┴───┐  ┌─────┴────┐  ┌─────┴─────┐
│ FCFS │  │ SCAN  │  │  LOOK    │  │ Shortest  │
│      │  │       │  │          │  │  Seek     │
└──────┘  └───────┘  └──────────┘  └───────────┘
```

---

## Class Implementations

### 1. Direction and State Enums
```java
public enum Direction {
    UP, DOWN, IDLE;
    
    public Direction opposite() {
        return this == UP ? DOWN : (this == DOWN ? UP : IDLE);
    }
}

public enum ElevatorState {
    MOVING, STOPPED, DOOR_OPEN, MAINTENANCE, EMERGENCY
}
```

### 2. Request Class
```java
public class Request implements Comparable<Request> {
    private final int sourceFloor;
    private final int destinationFloor;
    private final Direction direction;
    private final Instant timestamp;
    private final RequestType type;  // EXTERNAL (from floor), INTERNAL (from cabin)
    private final Priority priority;
    
    public Request(int sourceFloor, Direction direction) {
        this.sourceFloor = sourceFloor;
        this.direction = direction;
        this.destinationFloor = -1;  // Unknown for external requests
        this.timestamp = Instant.now();
        this.type = RequestType.EXTERNAL;
        this.priority = Priority.NORMAL;
    }
    
    public Request(int sourceFloor, int destinationFloor, Priority priority) {
        this.sourceFloor = sourceFloor;
        this.destinationFloor = destinationFloor;
        this.direction = destinationFloor > sourceFloor ? Direction.UP : Direction.DOWN;
        this.timestamp = Instant.now();
        this.type = RequestType.INTERNAL;
        this.priority = priority;
    }
    
    @Override
    public int compareTo(Request other) {
        int priorityCompare = this.priority.compareTo(other.priority);
        if (priorityCompare != 0) return priorityCompare;
        return this.timestamp.compareTo(other.timestamp);
    }
}

public enum Priority {
    EMERGENCY(0), VIP(1), NORMAL(2);
    private final int value;
}
```

### 3. Elevator Implementation
```java
public class Elevator {
    private final int id;
    private int currentFloor;
    private Direction direction;
    private ElevatorState state;
    private final TreeSet<Integer> upStops;
    private final TreeSet<Integer> downStops;
    private double currentWeight;
    private final double maxWeight;
    private final Door door;
    private final int minFloor;
    private final int maxFloor;
    private final List<ElevatorObserver> observers;
    
    public Elevator(int id, int minFloor, int maxFloor, double maxWeight) {
        this.id = id;
        this.minFloor = minFloor;
        this.maxFloor = maxFloor;
        this.maxWeight = maxWeight;
        this.currentFloor = minFloor;
        this.direction = Direction.IDLE;
        this.state = ElevatorState.STOPPED;
        this.upStops = new TreeSet<>();
        this.downStops = new TreeSet<>(Collections.reverseOrder());
        this.door = new Door();
        this.observers = new ArrayList<>();
    }
    
    public synchronized boolean addDestination(int floor, Direction requestDir) {
        if (floor < minFloor || floor > maxFloor) return false;
        if (isOverweight()) return false;
        
        if (requestDir == Direction.UP || 
            (direction == Direction.UP && floor >= currentFloor)) {
            upStops.add(floor);
        } else {
            downStops.add(floor);
        }
        
        if (direction == Direction.IDLE) {
            direction = floor > currentFloor ? Direction.UP : Direction.DOWN;
        }
        
        notifyObservers();
        return true;
    }
    
    public synchronized void step() {
        if (state == ElevatorState.MAINTENANCE || state == ElevatorState.EMERGENCY) {
            return;
        }
        
        if (shouldStopAtCurrentFloor()) {
            stop();
            return;
        }
        
        move();
    }
    
    private void move() {
        if (direction == Direction.UP && currentFloor < maxFloor) {
            currentFloor++;
            state = ElevatorState.MOVING;
        } else if (direction == Direction.DOWN && currentFloor > minFloor) {
            currentFloor--;
            state = ElevatorState.MOVING;
        } else {
            // Switch direction if needed
            switchDirection();
        }
        notifyObservers();
    }
    
    private boolean shouldStopAtCurrentFloor() {
        TreeSet<Integer> currentStops = direction == Direction.UP ? upStops : downStops;
        return currentStops.contains(currentFloor);
    }
    
    private void stop() {
        state = ElevatorState.STOPPED;
        TreeSet<Integer> currentStops = direction == Direction.UP ? upStops : downStops;
        currentStops.remove(currentFloor);
        
        openDoor();
        // Simulate passenger exchange
        closeDoor();
        
        if (currentStops.isEmpty()) {
            switchDirection();
        }
    }
    
    private void switchDirection() {
        if (direction == Direction.UP && !downStops.isEmpty()) {
            direction = Direction.DOWN;
        } else if (direction == Direction.DOWN && !upStops.isEmpty()) {
            direction = Direction.UP;
        } else {
            direction = Direction.IDLE;
            state = ElevatorState.STOPPED;
        }
    }
    
    public int getDistanceTo(int floor, Direction dir) {
        if (direction == Direction.IDLE) {
            return Math.abs(currentFloor - floor);
        }
        
        if (direction == dir) {
            if ((direction == Direction.UP && floor >= currentFloor) ||
                (direction == Direction.DOWN && floor <= currentFloor)) {
                return Math.abs(currentFloor - floor);
            }
        }
        
        // Need to complete current direction first
        int boundary = direction == Direction.UP ? maxFloor : minFloor;
        return Math.abs(currentFloor - boundary) + Math.abs(boundary - floor);
    }
}
```

### 4. LOOK Scheduling Algorithm
```java
public class LOOKScheduler implements ElevatorScheduler {
    
    @Override
    public Elevator schedule(Request request, List<Elevator> elevators) {
        Elevator best = null;
        int minDistance = Integer.MAX_VALUE;
        
        for (Elevator elevator : elevators) {
            if (elevator.getState() == ElevatorState.MAINTENANCE) continue;
            if (elevator.isOverweight()) continue;
            
            int distance = elevator.getDistanceTo(request.getSourceFloor(), 
                                                   request.getDirection());
            
            // Prefer elevators already moving in the same direction
            if (elevator.getDirection() == request.getDirection()) {
                distance -= 1000;  // Bonus for same direction
            }
            
            if (distance < minDistance) {
                minDistance = distance;
                best = elevator;
            }
        }
        
        return best;
    }
}
```

