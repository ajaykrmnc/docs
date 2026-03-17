# Design an Order Management System
**Difficulty:** Hard | **Companies:** Amazon, Uber, DoorDash, Shopify

---

## Problem Statement

Design an e-commerce order management system with state machine, inventory reservation, payment processing, and event sourcing.

---

## Requirements

### Functional Requirements
1. Order lifecycle management (state machine)
2. Inventory reservation with rollback
3. Payment processing with retry logic
4. Split shipments and partial fulfillment
5. Order modification and cancellation
6. Event sourcing for complete audit trail
7. Real-time order tracking

### Non-Functional Requirements
1. Strong consistency for inventory
2. Idempotent operations
3. High availability
4. Eventual consistency for analytics

---

## Class Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                    OrderService                                 │
├─────────────────────────────────────────────────────────────────┤
│ - orderRepository: OrderRepository                              │
│ - inventoryService: InventoryService                            │
│ - paymentService: PaymentService                                │
│ - eventStore: EventStore                                        │
│ - stateMachine: OrderStateMachine                               │
├─────────────────────────────────────────────────────────────────┤
│ + createOrder(request: CreateOrderRequest): Order               │
│ + processPayment(orderId: String): PaymentResult                │
│ + cancelOrder(orderId: String, reason: String): void            │
│ + updateOrder(orderId: String, updates: OrderUpdate): Order     │
│ + getOrderHistory(orderId: String): List<OrderEvent>            │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                         Order                                   │
├─────────────────────────────────────────────────────────────────┤
│ - orderId: String                                               │
│ - customerId: String                                            │
│ - items: List<OrderItem>                                        │
│ - status: OrderStatus                                           │
│ - shippingAddress: Address                                      │
│ - payment: PaymentInfo                                          │
│ - subtotal: Money                                               │
│ - tax: Money                                                    │
│ - total: Money                                                  │
│ - createdAt: Instant                                            │
│ - version: long                                                 │
├─────────────────────────────────────────────────────────────────┤
│ + addItem(item: OrderItem): void                                │
│ + removeItem(itemId: String): void                              │
│ + transitionTo(status: OrderStatus): void                       │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                    OrderStateMachine                            │
├─────────────────────────────────────────────────────────────────┤
│ - transitions: Map<OrderStatus, Set<OrderStatus>>               │
│ - handlers: Map<Transition, TransitionHandler>                  │
├─────────────────────────────────────────────────────────────────┤
│ + canTransition(from: OrderStatus, to: OrderStatus): boolean    │
│ + transition(order: Order, to: OrderStatus): Order              │
│ + getValidTransitions(status: OrderStatus): Set<OrderStatus>    │
└─────────────────────────────────────────────────────────────────┘
```

---

## Class Implementations

### 1. Order Status and State Machine
```java
public enum OrderStatus {
    CREATED,
    PENDING_PAYMENT,
    PAYMENT_CONFIRMED,
    INVENTORY_RESERVED,
    PROCESSING,
    SHIPPED,
    DELIVERED,
    CANCELLED,
    REFUNDED,
    FAILED
}

public class OrderStateMachine {
    private final Map<OrderStatus, Set<OrderStatus>> transitions;
    private final Map<Transition, TransitionHandler> handlers;
    
    public OrderStateMachine() {
        this.transitions = new EnumMap<>(OrderStatus.class);
        this.handlers = new HashMap<>();
        initializeTransitions();
    }
    
    private void initializeTransitions() {
        transitions.put(OrderStatus.CREATED, 
            Set.of(OrderStatus.PENDING_PAYMENT, OrderStatus.CANCELLED));
        transitions.put(OrderStatus.PENDING_PAYMENT,
            Set.of(OrderStatus.PAYMENT_CONFIRMED, OrderStatus.FAILED, OrderStatus.CANCELLED));
        transitions.put(OrderStatus.PAYMENT_CONFIRMED,
            Set.of(OrderStatus.INVENTORY_RESERVED, OrderStatus.FAILED));
        transitions.put(OrderStatus.INVENTORY_RESERVED,
            Set.of(OrderStatus.PROCESSING, OrderStatus.CANCELLED));
        transitions.put(OrderStatus.PROCESSING,
            Set.of(OrderStatus.SHIPPED, OrderStatus.CANCELLED));
        transitions.put(OrderStatus.SHIPPED,
            Set.of(OrderStatus.DELIVERED));
        transitions.put(OrderStatus.DELIVERED,
            Set.of(OrderStatus.REFUNDED));
        transitions.put(OrderStatus.CANCELLED,
            Set.of(OrderStatus.REFUNDED));
    }
    
    public boolean canTransition(OrderStatus from, OrderStatus to) {
        Set<OrderStatus> validTransitions = transitions.get(from);
        return validTransitions != null && validTransitions.contains(to);
    }
    
    public Order transition(Order order, OrderStatus toStatus) {
        if (!canTransition(order.getStatus(), toStatus)) {
            throw new InvalidTransitionException(
                "Cannot transition from " + order.getStatus() + " to " + toStatus);
        }
        
        Transition transition = new Transition(order.getStatus(), toStatus);
        TransitionHandler handler = handlers.get(transition);
        
        if (handler != null) {
            handler.handle(order);
        }
        
        order.setStatus(toStatus);
        return order;
    }
}
```

### 2. Order and OrderItem
```java
public class Order {
    private final String orderId;
    private final String customerId;
    private List<OrderItem> items;
    private OrderStatus status;
    private Address shippingAddress;
    private PaymentInfo payment;
    private Money subtotal;
    private Money tax;
    private Money total;
    private Instant createdAt;
    private Instant updatedAt;
    private long version;  // Optimistic locking
    
    public void addItem(OrderItem item) {
        if (status != OrderStatus.CREATED) {
            throw new OrderModificationException("Cannot modify order in status: " + status);
        }
        items.add(item);
        recalculateTotals();
    }
    
    public void removeItem(String itemId) {
        if (status != OrderStatus.CREATED) {
            throw new OrderModificationException("Cannot modify order in status: " + status);
        }
        items.removeIf(item -> item.getItemId().equals(itemId));
        recalculateTotals();
    }
    
    private void recalculateTotals() {
        this.subtotal = items.stream()
            .map(OrderItem::getLineTotal)
            .reduce(Money.ZERO, Money::add);
        this.tax = subtotal.multiply(0.1);  // 10% tax
        this.total = subtotal.add(tax);
    }
}

public class OrderItem {
    private final String itemId;
    private final String productId;
    private final String productName;
    private int quantity;
    private Money unitPrice;
    private ItemStatus status;
    private String shipmentId;
    
    public Money getLineTotal() {
        return unitPrice.multiply(quantity);
    }
}
```

### 3. Event Sourcing
```java
public abstract class OrderEvent {
    private final String eventId;
    private final String orderId;
    private final Instant timestamp;
    private final String triggeredBy;
    
    public abstract void apply(Order order);
}

public class OrderCreatedEvent extends OrderEvent {
    private final String customerId;
    private final List<OrderItem> items;
    private final Address shippingAddress;
    
    @Override
    public void apply(Order order) {
        order.setCustomerId(customerId);
        order.setItems(new ArrayList<>(items));
        order.setShippingAddress(shippingAddress);
        order.setStatus(OrderStatus.CREATED);
    }
}

public class PaymentConfirmedEvent extends OrderEvent {
    private final String paymentId;
    private final Money amount;
    private final PaymentMethod method;
    
    @Override
    public void apply(Order order) {
        order.setPayment(new PaymentInfo(paymentId, amount, method));
        order.setStatus(OrderStatus.PAYMENT_CONFIRMED);
    }
}

public class EventStore {
    private final Map<String, List<OrderEvent>> events;
    private final List<EventHandler> subscribers;
    
    public void append(OrderEvent event) {
        events.computeIfAbsent(event.getOrderId(), k -> new ArrayList<>())
            .add(event);
        notifySubscribers(event);
    }
    
    public Order reconstruct(String orderId) {
        List<OrderEvent> orderEvents = events.get(orderId);
        if (orderEvents == null) return null;
        
        Order order = new Order(orderId);
        for (OrderEvent event : orderEvents) {
            event.apply(order);
        }
        return order;
    }
}
```

### 4. Inventory Service with Saga
```java
public class InventoryService {
    private final InventoryRepository repository;
    
    public ReservationResult reserve(String orderId, List<OrderItem> items) {
        List<InventoryReservation> reservations = new ArrayList<>();
        
        try {
            for (OrderItem item : items) {
                InventoryReservation reservation = reserveItem(
                    orderId, item.getProductId(), item.getQuantity());
                reservations.add(reservation);
            }
            return ReservationResult.success(reservations);
        } catch (InsufficientInventoryException e) {
            // Rollback all reservations
            rollbackReservations(reservations);
            return ReservationResult.failed(e.getProductId(), e.getAvailable());
        }
    }
    
    private InventoryReservation reserveItem(String orderId, String productId, int qty) {
        return repository.executeInTransaction(() -> {
            Inventory inv = repository.findByProductId(productId);
            
            if (inv.getAvailable() < qty) {
                throw new InsufficientInventoryException(productId, inv.getAvailable());
            }
            
            inv.reserve(qty);
            repository.save(inv);
            
            return new InventoryReservation(orderId, productId, qty);
        });
    }
    
    public void confirmReservation(String orderId) {
        List<InventoryReservation> reservations = getReservations(orderId);
        for (InventoryReservation res : reservations) {
            Inventory inv = repository.findByProductId(res.getProductId());
            inv.confirmReservation(res.getQuantity());
            repository.save(inv);
        }
    }
    
    public void releaseReservation(String orderId) {
        List<InventoryReservation> reservations = getReservations(orderId);
        rollbackReservations(reservations);
    }
}
```

### 5. Order Service Orchestration
```java
public class OrderService {
    private final OrderRepository orderRepo;
    private final InventoryService inventoryService;
    private final PaymentService paymentService;
    private final EventStore eventStore;
    private final OrderStateMachine stateMachine;
    
    @Transactional
    public Order createOrder(CreateOrderRequest request) {
        String orderId = generateOrderId();
        
        // Create order
        Order order = new Order(orderId, request.getCustomerId());
        request.getItems().forEach(order::addItem);
        order.setShippingAddress(request.getShippingAddress());
        
        // Publish event
        eventStore.append(new OrderCreatedEvent(order));
        
        orderRepo.save(order);
        return order;
    }
    
    public Order processOrder(String orderId) {
        Order order = orderRepo.findById(orderId)
            .orElseThrow(() -> new OrderNotFoundException(orderId));
        
        // Reserve inventory
        ReservationResult reservation = inventoryService.reserve(orderId, order.getItems());
        if (!reservation.isSuccess()) {
            stateMachine.transition(order, OrderStatus.FAILED);
            throw new InsufficientInventoryException(reservation.getFailedProduct());
        }
        
        try {
            // Process payment
            PaymentResult payment = paymentService.charge(order.getTotal(), order.getPayment());
            if (!payment.isSuccess()) {
                inventoryService.releaseReservation(orderId);
                stateMachine.transition(order, OrderStatus.FAILED);
                throw new PaymentFailedException(payment.getError());
            }
            
            eventStore.append(new PaymentConfirmedEvent(order, payment));
            stateMachine.transition(order, OrderStatus.PAYMENT_CONFIRMED);
            stateMachine.transition(order, OrderStatus.INVENTORY_RESERVED);
            
        } catch (Exception e) {
            inventoryService.releaseReservation(orderId);
            throw e;
        }
        
        return orderRepo.save(order);
    }
}
```

