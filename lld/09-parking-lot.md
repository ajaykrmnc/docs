# Design a Parking Lot System
**Difficulty:** Medium | **Companies:** Amazon, Google, Microsoft, Uber

---

## Problem Statement

Design a parking lot system with multiple floors, different vehicle types, real-time spot tracking, and payment processing.

---

## Requirements

### Functional Requirements
1. Support multiple vehicle types (Motorcycle, Car, Bus)
2. Multiple floors with different spot sizes
3. Automated spot assignment based on vehicle type
4. Real-time availability tracking
5. Ticket-based entry and exit
6. Payment processing with hourly rates
7. Reservation system for future parking

### Non-Functional Requirements
1. High concurrency support
2. Quick spot finding algorithm
3. Fair pricing

---

## Class Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                       ParkingLot                                │
├─────────────────────────────────────────────────────────────────┤
│ - name: String                                                  │
│ - floors: List<ParkingFloor>                                    │
│ - entryPanels: List<EntryPanel>                                 │
│ - exitPanels: List<ExitPanel>                                   │
│ - displayBoards: List<DisplayBoard>                             │
│ - activeTickets: Map<String, Ticket>                            │
├─────────────────────────────────────────────────────────────────┤
│ + getAvailableSpot(vehicleType: VehicleType): ParkingSpot       │
│ + parkVehicle(vehicle: Vehicle): Ticket                         │
│ + unparkVehicle(ticket: Ticket): Payment                        │
│ + getAvailability(): Map<VehicleType, Integer>                  │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                      ParkingFloor                               │
├─────────────────────────────────────────────────────────────────┤
│ - floorNumber: int                                              │
│ - spots: Map<SpotType, List<ParkingSpot>>                       │
│ - displayBoard: DisplayBoard                                    │
├─────────────────────────────────────────────────────────────────┤
│ + getAvailableSpot(type: VehicleType): ParkingSpot              │
│ + getAvailableCount(type: SpotType): int                        │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                      ParkingSpot                                │
├─────────────────────────────────────────────────────────────────┤
│ - spotId: String                                                │
│ - floorNumber: int                                              │
│ - spotType: SpotType                                            │
│ - vehicle: Vehicle                                              │
│ - isAvailable: boolean                                          │
├─────────────────────────────────────────────────────────────────┤
│ + park(vehicle: Vehicle): boolean                               │
│ + unpark(): Vehicle                                             │
│ + canFit(vehicleType: VehicleType): boolean                     │
└─────────────────────────────────────────────────────────────────┘
```

---

## Class Implementations

### 1. Enums and Vehicle Classes
```java
public enum VehicleType {
    MOTORCYCLE, CAR, BUS
}

public enum SpotType {
    COMPACT(VehicleType.MOTORCYCLE),
    REGULAR(VehicleType.CAR),
    LARGE(VehicleType.BUS);
    
    private final VehicleType defaultVehicle;
    
    public boolean canFit(VehicleType vehicle) {
        return this.ordinal() >= vehicle.ordinal();
    }
}

public abstract class Vehicle {
    private final String licensePlate;
    private final VehicleType type;
    
    protected Vehicle(String licensePlate, VehicleType type) {
        this.licensePlate = licensePlate;
        this.type = type;
    }
    
    public String getLicensePlate() { return licensePlate; }
    public VehicleType getType() { return type; }
}

public class Car extends Vehicle {
    public Car(String licensePlate) {
        super(licensePlate, VehicleType.CAR);
    }
}

public class Motorcycle extends Vehicle {
    public Motorcycle(String licensePlate) {
        super(licensePlate, VehicleType.MOTORCYCLE);
    }
}

public class Bus extends Vehicle {
    public Bus(String licensePlate) {
        super(licensePlate, VehicleType.BUS);
    }
}
```

### 2. ParkingSpot Implementation
```java
public class ParkingSpot {
    private final String spotId;
    private final int floorNumber;
    private final SpotType spotType;
    private Vehicle vehicle;
    private final ReentrantLock lock;
    
    public ParkingSpot(String spotId, int floorNumber, SpotType spotType) {
        this.spotId = spotId;
        this.floorNumber = floorNumber;
        this.spotType = spotType;
        this.lock = new ReentrantLock();
    }
    
    public boolean park(Vehicle vehicle) {
        lock.lock();
        try {
            if (!isAvailable() || !canFit(vehicle.getType())) {
                return false;
            }
            this.vehicle = vehicle;
            return true;
        } finally {
            lock.unlock();
        }
    }
    
    public Vehicle unpark() {
        lock.lock();
        try {
            Vehicle parked = this.vehicle;
            this.vehicle = null;
            return parked;
        } finally {
            lock.unlock();
        }
    }
    
    public boolean isAvailable() {
        return vehicle == null;
    }
    
    public boolean canFit(VehicleType vehicleType) {
        return spotType.canFit(vehicleType);
    }
}
```

### 3. Ticket and Payment
```java
public class Ticket {
    private final String ticketId;
    private final Vehicle vehicle;
    private final ParkingSpot spot;
    private final Instant entryTime;
    private Instant exitTime;
    private TicketStatus status;
    
    public Ticket(Vehicle vehicle, ParkingSpot spot) {
        this.ticketId = generateTicketId();
        this.vehicle = vehicle;
        this.spot = spot;
        this.entryTime = Instant.now();
        this.status = TicketStatus.ACTIVE;
    }
    
    private String generateTicketId() {
        return "TKT-" + System.currentTimeMillis() + "-" + 
               ThreadLocalRandom.current().nextInt(1000);
    }
    
    public Duration getParkingDuration() {
        Instant end = exitTime != null ? exitTime : Instant.now();
        return Duration.between(entryTime, end);
    }
    
    public void markExit() {
        this.exitTime = Instant.now();
        this.status = TicketStatus.PAID;
    }
}

public class PricingStrategy {
    private final Map<VehicleType, Double> hourlyRates;
    
    public PricingStrategy() {
        hourlyRates = new HashMap<>();
        hourlyRates.put(VehicleType.MOTORCYCLE, 1.0);
        hourlyRates.put(VehicleType.CAR, 2.0);
        hourlyRates.put(VehicleType.BUS, 5.0);
    }
    
    public double calculateFee(Ticket ticket) {
        Duration duration = ticket.getParkingDuration();
        long hours = duration.toHours();
        if (duration.toMinutesPart() > 0) hours++;  // Round up
        
        double rate = hourlyRates.get(ticket.getVehicle().getType());
        return hours * rate;
    }
}
```

### 4. ParkingLot Main Class
```java
public class ParkingLot {
    private static ParkingLot instance;
    private final String name;
    private final List<ParkingFloor> floors;
    private final Map<String, Ticket> activeTickets;
    private final PricingStrategy pricingStrategy;
    private final ParkingStrategy parkingStrategy;
    
    private ParkingLot(String name, int numFloors, int spotsPerFloor) {
        this.name = name;
        this.floors = new ArrayList<>();
        this.activeTickets = new ConcurrentHashMap<>();
        this.pricingStrategy = new PricingStrategy();
        this.parkingStrategy = new NearestSpotStrategy();
        
        for (int i = 0; i < numFloors; i++) {
            floors.add(new ParkingFloor(i, spotsPerFloor));
        }
    }
    
    public static synchronized ParkingLot getInstance(String name, int floors, int spots) {
        if (instance == null) {
            instance = new ParkingLot(name, floors, spots);
        }
        return instance;
    }
    
    public Ticket parkVehicle(Vehicle vehicle) {
        ParkingSpot spot = parkingStrategy.findSpot(floors, vehicle.getType());
        
        if (spot == null) {
            throw new ParkingFullException("No available spot for " + vehicle.getType());
        }
        
        if (!spot.park(vehicle)) {
            throw new ParkingException("Failed to park vehicle");
        }
        
        Ticket ticket = new Ticket(vehicle, spot);
        activeTickets.put(ticket.getTicketId(), ticket);
        return ticket;
    }
    
    public Payment processExit(String ticketId, PaymentMethod method) {
        Ticket ticket = activeTickets.get(ticketId);
        if (ticket == null) {
            throw new InvalidTicketException("Invalid ticket: " + ticketId);
        }
        
        double amount = pricingStrategy.calculateFee(ticket);
        Payment payment = method.process(amount);
        
        if (payment.isSuccessful()) {
            ticket.getSpot().unpark();
            ticket.markExit();
            activeTickets.remove(ticketId);
        }
        
        return payment;
    }
    
    public Map<VehicleType, Integer> getAvailability() {
        Map<VehicleType, Integer> availability = new EnumMap<>(VehicleType.class);
        for (VehicleType type : VehicleType.values()) {
            int count = floors.stream()
                .mapToInt(f -> f.getAvailableCount(type))
                .sum();
            availability.put(type, count);
        }
        return availability;
    }
}
```

