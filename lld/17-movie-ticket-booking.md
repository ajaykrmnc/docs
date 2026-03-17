# Design a Movie Ticket Booking System
**Difficulty:** Medium-Hard | **Companies:** Amazon, Google, BookMyShow

---

## Problem Statement

Design a movie ticket booking system with seat selection, concurrent booking handling, temporary seat holds, and payment processing.

---

## Requirements

### Functional Requirements
1. Browse movies, theaters, and show timings
2. View seat map with real-time availability
3. Select and temporarily hold seats
4. Concurrent booking prevention
5. Payment processing with timeout
6. Booking confirmation with e-tickets
7. Cancellation and refund processing

### Non-Functional Requirements
1. Handle concurrent seat bookings (no double booking)
2. Low latency seat availability checks
3. Scalable to multiple cities/theaters

---

## Class Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                     BookingService                              │
├─────────────────────────────────────────────────────────────────┤
│ - showRepository: ShowRepository                                │
│ - seatLockManager: SeatLockManager                              │
│ - paymentGateway: PaymentGateway                                │
│ - bookingRepository: BookingRepository                          │
│ - notificationService: NotificationService                      │
├─────────────────────────────────────────────────────────────────┤
│ + getAvailableSeats(showId: String): List<Seat>                 │
│ + holdSeats(showId: String, seatIds: List, userId: String): Hold│
│ + confirmBooking(holdId: String, payment: PaymentInfo): Booking │
│ + cancelBooking(bookingId: String): RefundResult                │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                          Show                                   │
├─────────────────────────────────────────────────────────────────┤
│ - showId: String                                                │
│ - movie: Movie                                                  │
│ - theater: Theater                                              │
│ - screen: Screen                                                │
│ - startTime: LocalDateTime                                      │
│ - endTime: LocalDateTime                                        │
│ - seats: Map<String, ShowSeat>                                  │
│ - pricing: Map<SeatType, Money>                                 │
├─────────────────────────────────────────────────────────────────┤
│ + getAvailableSeats(): List<ShowSeat>                           │
│ + getSeat(seatId: String): ShowSeat                             │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                        ShowSeat                                 │
├─────────────────────────────────────────────────────────────────┤
│ - seatId: String                                                │
│ - row: String                                                   │
│ - number: int                                                   │
│ - type: SeatType                                                │
│ - status: SeatStatus                                            │
│ - price: Money                                                  │
├─────────────────────────────────────────────────────────────────┤
│ + isAvailable(): boolean                                        │
│ + hold(userId: String): boolean                                 │
│ + book(): void                                                  │
│ + release(): void                                               │
└─────────────────────────────────────────────────────────────────┘
```

---

## Class Implementations

### 1. Core Entities
```java
public class Movie {
    private final String movieId;
    private String title;
    private String description;
    private Duration duration;
    private String language;
    private Genre genre;
    private Rating rating;
    private LocalDate releaseDate;
    private List<String> cast;
}

public class Theater {
    private final String theaterId;
    private String name;
    private Address address;
    private List<Screen> screens;
    private List<Amenity> amenities;
}

public class Screen {
    private final String screenId;
    private String name;
    private int totalSeats;
    private List<Seat> seats;
    private ScreenType type;  // IMAX, 3D, STANDARD
}

public class Seat {
    private final String seatId;
    private final String row;
    private final int number;
    private final SeatType type;
    
    public enum SeatType {
        REGULAR(1.0), PREMIUM(1.5), VIP(2.0), RECLINER(2.5);
        private final double priceMultiplier;
    }
}
```

### 2. ShowSeat with Status Management
```java
public class ShowSeat {
    private final String showSeatId;
    private final Seat seat;
    private final Show show;
    private volatile SeatStatus status;
    private Money price;
    private String holderId;
    private Instant holdExpiresAt;
    private final ReentrantLock lock;
    
    public ShowSeat(Seat seat, Show show, Money basePrice) {
        this.showSeatId = show.getShowId() + "-" + seat.getSeatId();
        this.seat = seat;
        this.show = show;
        this.status = SeatStatus.AVAILABLE;
        this.price = basePrice.multiply(seat.getType().getPriceMultiplier());
        this.lock = new ReentrantLock();
    }
    
    public boolean tryHold(String userId, Duration holdDuration) {
        lock.lock();
        try {
            // Check if previous hold has expired
            if (status == SeatStatus.HELD && Instant.now().isAfter(holdExpiresAt)) {
                release();
            }
            
            if (status != SeatStatus.AVAILABLE) {
                return false;
            }
            
            this.status = SeatStatus.HELD;
            this.holderId = userId;
            this.holdExpiresAt = Instant.now().plus(holdDuration);
            return true;
        } finally {
            lock.unlock();
        }
    }
    
    public boolean book(String userId) {
        lock.lock();
        try {
            if (status != SeatStatus.HELD || !holderId.equals(userId)) {
                return false;
            }
            if (Instant.now().isAfter(holdExpiresAt)) {
                release();
                return false;
            }
            
            this.status = SeatStatus.BOOKED;
            return true;
        } finally {
            lock.unlock();
        }
    }
    
    public void release() {
        lock.lock();
        try {
            this.status = SeatStatus.AVAILABLE;
            this.holderId = null;
            this.holdExpiresAt = null;
        } finally {
            lock.unlock();
        }
    }
}

public enum SeatStatus {
    AVAILABLE, HELD, BOOKED, BLOCKED
}
```

### 3. SeatLockManager with Distributed Locking
```java
public class SeatLockManager {
    private final RedisClient redis;
    private final Duration defaultHoldDuration;
    
    public SeatLockManager(RedisClient redis, Duration holdDuration) {
        this.redis = redis;
        this.defaultHoldDuration = holdDuration;
    }
    
    public SeatHold tryHoldSeats(String showId, List<String> seatIds, String userId) {
        String holdId = generateHoldId();
        List<String> heldSeats = new ArrayList<>();
        
        try {
            for (String seatId : seatIds) {
                String lockKey = buildLockKey(showId, seatId);
                boolean acquired = redis.setNx(lockKey, userId, defaultHoldDuration);
                
                if (!acquired) {
                    // Check if held by same user
                    String holder = redis.get(lockKey);
                    if (!userId.equals(holder)) {
                        throw new SeatNotAvailableException(seatId);
                    }
                }
                heldSeats.add(seatId);
            }
            
            return new SeatHold(holdId, showId, heldSeats, userId, 
                               Instant.now().plus(defaultHoldDuration));
        } catch (SeatNotAvailableException e) {
            // Rollback held seats
            releaseSeats(showId, heldSeats);
            throw e;
        }
    }
    
    public void releaseSeats(String showId, List<String> seatIds) {
        for (String seatId : seatIds) {
            String lockKey = buildLockKey(showId, seatId);
            redis.delete(lockKey);
        }
    }
    
    public boolean extendHold(String showId, List<String> seatIds, String userId) {
        for (String seatId : seatIds) {
            String lockKey = buildLockKey(showId, seatId);
            String holder = redis.get(lockKey);
            
            if (!userId.equals(holder)) {
                return false;
            }
            redis.expire(lockKey, defaultHoldDuration);
        }
        return true;
    }
    
    private String buildLockKey(String showId, String seatId) {
        return "seat:lock:" + showId + ":" + seatId;
    }
}
```

### 4. Booking Service
```java
public class BookingService {
    private final ShowRepository showRepo;
    private final SeatLockManager lockManager;
    private final PaymentGateway paymentGateway;
    private final BookingRepository bookingRepo;
    private final NotificationService notificationService;
    
    public SeatHold holdSeats(String showId, List<String> seatIds, String userId) {
        Show show = showRepo.findById(showId)
            .orElseThrow(() -> new ShowNotFoundException(showId));
        
        // Validate seats exist
        for (String seatId : seatIds) {
            ShowSeat seat = show.getSeat(seatId);
            if (seat == null || !seat.isAvailable()) {
                throw new SeatNotAvailableException(seatId);
            }
        }
        
        return lockManager.tryHoldSeats(showId, seatIds, userId);
    }
    
    @Transactional
    public Booking confirmBooking(String holdId, PaymentInfo paymentInfo) {
        SeatHold hold = getAndValidateHold(holdId);
        Show show = showRepo.findById(hold.getShowId()).get();
        
        // Calculate total
        Money total = hold.getSeatIds().stream()
            .map(id -> show.getSeat(id).getPrice())
            .reduce(Money.ZERO, Money::add);
        
        // Process payment
        PaymentResult payment = paymentGateway.charge(total, paymentInfo);
        if (!payment.isSuccess()) {
            throw new PaymentFailedException(payment.getError());
        }
        
        try {
            // Mark seats as booked
            for (String seatId : hold.getSeatIds()) {
                ShowSeat seat = show.getSeat(seatId);
                if (!seat.book(hold.getUserId())) {
                    throw new BookingFailedException("Seat no longer available: " + seatId);
                }
            }
            
            // Create booking
            Booking booking = Booking.builder()
                .bookingId(generateBookingId())
                .showId(hold.getShowId())
                .userId(hold.getUserId())
                .seatIds(hold.getSeatIds())
                .totalAmount(total)
                .paymentId(payment.getPaymentId())
                .status(BookingStatus.CONFIRMED)
                .build();
            
            bookingRepo.save(booking);
            notificationService.sendBookingConfirmation(booking);
            
            return booking;
        } catch (Exception e) {
            // Refund on failure
            paymentGateway.refund(payment.getPaymentId());
            throw e;
        }
    }
}
```

