# Problem 18: Traffic Light Controlled Intersection (LeetCode 1279)

## 🎯 Problem Statement
Cars from two roads approach intersection. Control traffic light to ensure cars from only one road pass at a time. Minimize light changes.

## 🏢 Companies
**Databricks, Rubrik** - Tests state machine and mutual exclusion

## 🔑 Core Principles

### 1. The Intersection

```
           ROAD A
             │
        ↓    │    ↑
       ─────────────
ROAD B →     │     ← ROAD B
       ─────────────
        ↑    │    ↓
             │
           ROAD A

Only ONE road can have green at a time!
```

### 2. State Machine

```
┌─────────────────┐          ┌─────────────────┐
│  ROAD A GREEN   │  ──────► │  ROAD B GREEN   │
│  (Road B Red)   │  Car     │  (Road A Red)   │
│                 │  from B  │                 │
└─────────────────┘          └─────────────────┘
         ▲                            │
         │                            │
         │      Car from A arrives    │
         └────────────────────────────┘
```

### 3. Basic Implementation

```python
class TrafficLight:
    def __init__(self):
        self.current_green = Road.A  # Initial state
        self.lock = Lock()
    
    def car_arrived(self, car_id, road, turn_green, cross):
        with self.lock:  # Mutual exclusion
            if self.current_green != road:
                # Need to change light
                turn_green()
                self.current_green = road
            
            cross()  # Car crosses safely
```

### 4. Minimizing Light Changes

```
SCENARIO: Cars arrive in order A, A, A, B, A, A

NAIVE (change for each car):
  A→Cross, A→Cross, A→Cross, [CHANGE], B→Cross, [CHANGE], A→Cross...
  Changes: 2

OPTIMAL (batch same road):
  [GREEN A] A→Cross, A→Cross, A→Cross, [CHANGE], 
  [GREEN B] B→Cross, [CHANGE],
  [GREEN A] A→Cross, A→Cross
  Changes: 2 (same, but we only change when necessary)

Key insight: Don't change light if already green for this road!
```

### 5. Preventing Starvation

```
PROBLEM: Road A cars keep arriving, Road B waits forever

SOLUTION: Fair scheduling with max consecutive cars

class TrafficLightFair:
    def __init__(self, max_consecutive=5):
        self.current_green = Road.A
        self.consecutive = 0
        self.max_consecutive = max_consecutive
        self.waiting = {Road.A: 0, Road.B: 0}
        self.condition = Condition()
    
    def car_arrived(self, road, turn_green, cross):
        with self.condition:
            self.waiting[road] += 1
            
            # Wait if not our turn
            while self.current_green != road:
                # Check if should force switch
                other = Road.B if road == Road.A else Road.A
                if (self.consecutive >= self.max_consecutive and
                    self.waiting[road] > 0):
                    # Force switch for fairness
                    turn_green()
                    self.current_green = road
                    self.consecutive = 0
                    break
                
                self.condition.wait()
            
            # Cross
            self.waiting[road] -= 1
            self.consecutive += 1
            cross()
            
            # Maybe switch after crossing
            other = Road.B if road == Road.A else Road.A
            if (self.consecutive >= self.max_consecutive and
                self.waiting[other] > 0):
                self.current_green = other
                self.consecutive = 0
                self.condition.notify_all()
```

## 📊 Approaches Comparison

| Approach | Starvation-Free | Min Changes | Complexity |
|----------|-----------------|-------------|------------|
| Basic mutex | ❌ | ✅ | Simple |
| **With fairness** | ✅ | ✅ | Medium |
| Round-robin | ✅ | ❌ (many changes) | Simple |

## 🧠 Key Insights

### Why Lock is Sufficient?
```
Basic problem only needs MUTUAL EXCLUSION:
- Only one car in intersection at a time
- Light state is shared resource

No waiting/signaling needed for basic version!
```

### When to Use Condition Variable?
```
NEEDED WHEN:
- Cars must WAIT for their turn
- Fair scheduling requires queuing
- Want to implement priority

NOT NEEDED WHEN:
- Simple mutual exclusion sufficient
- No waiting/queuing logic
```

## 💻 C++ Solution

```cpp
class TrafficLight {
    Road current_green_ = Road::A;
    mutex mutex_;
    
public:
    void carArrived(int carId, Road road,
                    function<void()> turnGreen,
                    function<void()> cross) {
        lock_guard<mutex> lock(mutex_);
        
        if (current_green_ != road) {
            turnGreen();
            current_green_ = road;
        }
        
        cross();
    }
};
```

## ⚠️ Common Mistakes

| Mistake | Problem | Fix |
|---------|---------|-----|
| No mutual exclusion | Collision! | Use mutex |
| Always changing light | Inefficient | Check current state |
| No starvation prevention | Unfair | Add max consecutive |
| Complex when simple works | Over-engineering | Start with mutex |

## 🔗 Real-World Considerations
- **Sensor integration**: Detect waiting cars
- **Emergency priority**: Ambulance preemption
- **Time-based**: Rush hour scheduling
- **Pedestrians**: Additional states

