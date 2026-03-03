"""
QUESTION 18: Traffic Light Controlled Intersection (LeetCode 1279)
==================================================================

Problem: Cars from two roads approach intersection. Control traffic light
to ensure cars from only one road pass at a time.

Key Concepts: Mutual exclusion, State machines, Thread coordination
"""

import threading
import time
import random
from enum import Enum


class Direction(Enum):
    ROAD_A = 1  # North-South
    ROAD_B = 2  # East-West


class TrafficLight:
    """
    Traffic Light Controller.
    
    EXPLANATION:
    Only one road has green light at a time.
    Cars must wait if their road has red light.
    Change light only when car from other road arrives.
    
    Key Design:
    - Track current green road
    - Lock ensures atomic light checks/changes
    - Don't change light unnecessarily (reduce context switches)
    """
    
    def __init__(self):
        self.current_green = Direction.ROAD_A
        self._lock = threading.Lock()
    
    def car_arrived(self, car_id: int, road: Direction, direction: str,
                    turn_green: Callable, cross: Callable):
        """
        Called when car arrives at intersection.
        
        Args:
            car_id: Unique car identifier
            road: Which road the car is on (A or B)
            direction: Where car is going (for printing)
            turn_green: Call to turn light green
            cross: Call when car crosses
        """
        with self._lock:
            if self.current_green != road:
                # Need to change light
                turn_green()
                self.current_green = road
            
            # Now safe to cross
            cross()


class TrafficLightFair:
    """
    Fair Traffic Light (Prevents Starvation).
    
    EXPLANATION:
    Track waiting cars on each road.
    After N cars pass, check if other road has waiting cars.
    If so, switch light to prevent starvation.
    """
    
    def __init__(self, max_consecutive: int = 5):
        self.current_green = Direction.ROAD_A
        self.consecutive_count = 0
        self.max_consecutive = max_consecutive
        self.waiting = {Direction.ROAD_A: 0, Direction.ROAD_B: 0}
        self._lock = threading.Lock()
        self._condition = threading.Condition(self._lock)
    
    def car_arrived(self, car_id: int, road: Direction,
                    turn_green: Callable, cross: Callable):
        with self._condition:
            self.waiting[road] += 1
            
            # Wait for our turn
            while self.current_green != road:
                # Check if we should switch
                other = Direction.ROAD_B if road == Direction.ROAD_A else Direction.ROAD_A
                if (self.consecutive_count >= self.max_consecutive and 
                    self.waiting[road] > 0):
                    # Force switch
                    turn_green()
                    self.current_green = road
                    self.consecutive_count = 0
                    break
                
                self._condition.wait()
            
            # Cross
            self.waiting[road] -= 1
            self.consecutive_count += 1
            cross()
            
            # Check if should switch for fairness
            other = Direction.ROAD_B if road == Direction.ROAD_A else Direction.ROAD_A
            if (self.consecutive_count >= self.max_consecutive and 
                self.waiting[other] > 0 and self.waiting[road] == 0):
                self.current_green = other
                self.consecutive_count = 0
                self._condition.notify_all()


def simulate():
    light = TrafficLight()
    
    def car(car_id: int, road: Direction, direction: str):
        time.sleep(random.uniform(0, 0.5))  # Random arrival
        
        def turn_green():
            print(f"Light changed to {road.name}")
        
        def cross():
            print(f"Car {car_id} from {road.name} going {direction}")
        
        light.car_arrived(car_id, road, direction, turn_green, cross)
    
    threads = []
    
    # Cars from Road A
    for i in range(5):
        t = threading.Thread(target=car, args=(i, Direction.ROAD_A, "North"))
        threads.append(t)
    
    # Cars from Road B
    for i in range(5, 10):
        t = threading.Thread(target=car, args=(i, Direction.ROAD_B, "East"))
        threads.append(t)
    
    random.shuffle(threads)
    
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    
    print("All cars passed!")


if __name__ == "__main__":
    simulate()

