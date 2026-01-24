# Object-Oriented Programming and Design Patterns

## Table of Contents
1. [OOP Principles Deep Dive](#oop-principles)
2. [SOLID Principles](#solid-principles)
3. [Creational Patterns](#creational-patterns)
4. [Structural Patterns](#structural-patterns)
5. [Behavioral Patterns](#behavioral-patterns)
6. [Java-Specific OOP Features](#java-specific-features)
7. [Interview Questions](#interview-questions)

---

## OOP Principles Deep Dive

### 1. Encapsulation - Information Hiding

```java
// BAD: Exposing internal state
public class BankAccountBad {
    public double balance;  // Direct access - dangerous!
}

// GOOD: Encapsulated with validation
public class BankAccount {
    private double balance;
    private final String accountNumber;
    private List<Transaction> transactions = new ArrayList<>();
    
    public BankAccount(String accountNumber, double initialDeposit) {
        if (initialDeposit < 0) {
            throw new IllegalArgumentException("Initial deposit cannot be negative");
        }
        this.accountNumber = accountNumber;
        this.balance = initialDeposit;
    }
    
    public void deposit(double amount) {
        if (amount <= 0) {
            throw new IllegalArgumentException("Deposit amount must be positive");
        }
        balance += amount;
        transactions.add(new Transaction(TransactionType.DEPOSIT, amount));
    }
    
    public void withdraw(double amount) {
        if (amount <= 0) {
            throw new IllegalArgumentException("Withdrawal amount must be positive");
        }
        if (amount > balance) {
            throw new InsufficientFundsException("Insufficient balance");
        }
        balance -= amount;
        transactions.add(new Transaction(TransactionType.WITHDRAWAL, amount));
    }
    
    public double getBalance() {
        return balance;
    }
    
    // Return defensive copy to prevent external modification
    public List<Transaction> getTransactions() {
        return Collections.unmodifiableList(transactions);
    }
}
```

### 2. Inheritance - Type Hierarchy

```java
// Template Method Pattern using inheritance
public abstract class DataProcessor {
    // Template method - defines algorithm skeleton
    public final void process() {
        readData();
        processData();
        writeData();
        if (needsCleanup()) {
            cleanup();
        }
    }
    
    protected abstract void readData();
    protected abstract void processData();
    protected abstract void writeData();
    
    // Hook method - optional override
    protected boolean needsCleanup() {
        return false;
    }
    
    protected void cleanup() {
        // Default implementation
    }
}

public class CSVProcessor extends DataProcessor {
    private List<String[]> data;
    
    @Override
    protected void readData() {
        // Read CSV file
    }
    
    @Override
    protected void processData() {
        // Process CSV data
    }
    
    @Override
    protected void writeData() {
        // Write processed data
    }
    
    @Override
    protected boolean needsCleanup() {
        return true;  // Override hook
    }
}
```

### 3. Polymorphism - Multiple Forms

```java
// Compile-time polymorphism (Method Overloading)
public class Calculator {
    public int add(int a, int b) {
        return a + b;
    }
    
    public double add(double a, double b) {
        return a + b;
    }
    
    public int add(int... numbers) {
        return Arrays.stream(numbers).sum();
    }
}

// Runtime polymorphism (Method Overriding)
interface Shape {
    double area();
    double perimeter();
}

class Circle implements Shape {
    private double radius;
    
    public Circle(double radius) {
        this.radius = radius;
    }
    
    @Override
    public double area() {
        return Math.PI * radius * radius;
    }
    
    @Override
    public double perimeter() {
        return 2 * Math.PI * radius;
    }
}

class Rectangle implements Shape {
    private double width, height;
    
    public Rectangle(double width, double height) {
        this.width = width;
        this.height = height;
    }
    
    @Override
    public double area() {
        return width * height;
    }
    
    @Override
    public double perimeter() {
        return 2 * (width + height);
    }
}

// Polymorphic usage
public class ShapeCalculator {
    public double totalArea(List<Shape> shapes) {
        return shapes.stream()
                     .mapToDouble(Shape::area)
                     .sum();
    }
}
```

### 4. Abstraction - Essential Features

```java
// Interface: Pure abstraction
public interface PaymentGateway {
    PaymentResult processPayment(PaymentRequest request);
    RefundResult refund(String transactionId, double amount);
    PaymentStatus getStatus(String transactionId);
}

// Abstract class: Partial abstraction with shared code
public abstract class AbstractPaymentGateway implements PaymentGateway {
    protected final Logger logger = LoggerFactory.getLogger(getClass());
    protected final PaymentValidator validator;
    
    protected AbstractPaymentGateway(PaymentValidator validator) {
        this.validator = validator;
    }
    
    @Override
    public final PaymentResult processPayment(PaymentRequest request) {
        // Template method with shared validation logic
        validator.validate(request);
        logger.info("Processing payment: {}", request.getId());
        
        PaymentResult result = doProcessPayment(request);
        
        logger.info("Payment result: {}", result.getStatus());
        return result;
    }
    
    protected abstract PaymentResult doProcessPayment(PaymentRequest request);
}
```

---

## SOLID Principles

### 1. Single Responsibility Principle (SRP)

```java
// BAD: One class doing too much
public class UserServiceBad {
    public void createUser(User user) { /* ... */ }
    public void sendEmail(String to, String subject) { /* ... */ }
    public String generateReport(List<User> users) { /* ... */ }
    public void validateEmail(String email) { /* ... */ }
}

// GOOD: Each class has one responsibility
public class UserService {
    private final UserRepository repository;
    private final UserValidator validator;
    private final EmailService emailService;

    public User createUser(CreateUserRequest request) {
        validator.validate(request);
        User user = repository.save(new User(request));
        emailService.sendWelcomeEmail(user);
        return user;
    }
}

public class EmailService {
    public void sendWelcomeEmail(User user) { /* ... */ }
    public void sendPasswordReset(User user, String token) { /* ... */ }
}

public class UserReportGenerator {
    public String generateReport(List<User> users) { /* ... */ }
}
```

### 2. Open/Closed Principle (OCP)

```java
// BAD: Adding new shapes requires modifying existing code
public class AreaCalculatorBad {
    public double calculateArea(Object shape) {
        if (shape instanceof Rectangle r) {
            return r.width * r.height;
        } else if (shape instanceof Circle c) {
            return Math.PI * c.radius * c.radius;
        }
        // Adding Triangle requires modifying this class!
        throw new IllegalArgumentException("Unknown shape");
    }
}

// GOOD: Open for extension, closed for modification
public interface Shape {
    double calculateArea();
}

public class Rectangle implements Shape {
    private final double width, height;

    @Override
    public double calculateArea() {
        return width * height;
    }
}

public class Circle implements Shape {
    private final double radius;

    @Override
    public double calculateArea() {
        return Math.PI * radius * radius;
    }
}

// New shapes can be added without modifying existing code
public class Triangle implements Shape {
    private final double base, height;

    @Override
    public double calculateArea() {
        return 0.5 * base * height;
    }
}

public class AreaCalculator {
    public double calculateTotalArea(List<Shape> shapes) {
        return shapes.stream()
            .mapToDouble(Shape::calculateArea)
            .sum();
    }
}
```

### 3. Liskov Substitution Principle (LSP)

```java
// BAD: Square breaks Rectangle's contract
public class RectangleBad {
    protected int width, height;

    public void setWidth(int width) { this.width = width; }
    public void setHeight(int height) { this.height = height; }
    public int getArea() { return width * height; }
}

public class SquareBad extends RectangleBad {
    @Override
    public void setWidth(int width) {
        this.width = width;
        this.height = width;  // Violates LSP!
    }

    @Override
    public void setHeight(int height) {
        this.width = height;
        this.height = height;  // Violates LSP!
    }
}

// Test that fails with Square:
void testRectangle(RectangleBad r) {
    r.setWidth(5);
    r.setHeight(4);
    assert r.getArea() == 20;  // Fails for Square!
}

// GOOD: Use composition or separate hierarchies
public interface Shape {
    int getArea();
}

public final class Rectangle implements Shape {
    private final int width, height;

    public Rectangle(int width, int height) {
        this.width = width;
        this.height = height;
    }

    @Override
    public int getArea() { return width * height; }
}

public final class Square implements Shape {
    private final int side;

    public Square(int side) { this.side = side; }

    @Override
    public int getArea() { return side * side; }
}
```

### 4. Interface Segregation Principle (ISP)

```java
// BAD: Fat interface forces unnecessary implementations
public interface WorkerBad {
    void work();
    void eat();
    void sleep();
}

public class RobotBad implements WorkerBad {
    public void work() { /* working */ }
    public void eat() { /* Robots don't eat! */ }  // Forced to implement
    public void sleep() { /* Robots don't sleep! */ }  // Forced to implement
}

// GOOD: Segregated interfaces
public interface Workable {
    void work();
}

public interface Eatable {
    void eat();
}

public interface Sleepable {
    void sleep();
}

public class Human implements Workable, Eatable, Sleepable {
    public void work() { /* working */ }
    public void eat() { /* eating */ }
    public void sleep() { /* sleeping */ }
}

public class Robot implements Workable {
    public void work() { /* working */ }
    // No need to implement eat() or sleep()
}
```

### 5. Dependency Inversion Principle (DIP)

```java
// BAD: High-level module depends on low-level module
public class OrderServiceBad {
    private MySQLDatabase database = new MySQLDatabase();  // Concrete dependency
    private SmtpEmailSender emailSender = new SmtpEmailSender();

    public void createOrder(Order order) {
        database.save(order);  // Coupled to MySQL
        emailSender.send(order.getCustomerEmail(), "Order confirmed");
    }
}

// GOOD: Both depend on abstractions
public interface OrderRepository {
    void save(Order order);
    Optional<Order> findById(String id);
}

public interface NotificationService {
    void notifyOrderCreated(Order order);
}

public class OrderService {
    private final OrderRepository repository;
    private final NotificationService notifications;

    // Dependencies injected
    public OrderService(OrderRepository repository, NotificationService notifications) {
        this.repository = repository;
        this.notifications = notifications;
    }

    public void createOrder(Order order) {
        repository.save(order);
        notifications.notifyOrderCreated(order);
    }
}

// Implementations can be swapped easily
public class MySQLOrderRepository implements OrderRepository { /* ... */ }
public class MongoOrderRepository implements OrderRepository { /* ... */ }
public class EmailNotificationService implements NotificationService { /* ... */ }
public class SmsNotificationService implements NotificationService { /* ... */ }
```

---

## Creational Patterns

### Singleton Pattern

```java
// Thread-safe Singleton implementations

// 1. Eager initialization (simplest)
public class EagerSingleton {
    private static final EagerSingleton INSTANCE = new EagerSingleton();
    private EagerSingleton() {}
    public static EagerSingleton getInstance() { return INSTANCE; }
}

// 2. Double-checked locking (lazy, thread-safe)
public class LazyThreadSafeSingleton {
    private static volatile LazyThreadSafeSingleton instance;
    private LazyThreadSafeSingleton() {}

    public static LazyThreadSafeSingleton getInstance() {
        if (instance == null) {
            synchronized (LazyThreadSafeSingleton.class) {
                if (instance == null) {
                    instance = new LazyThreadSafeSingleton();
                }
            }
        }
        return instance;
    }
}

// 3. Bill Pugh Singleton (recommended)
public class BillPughSingleton {
    private BillPughSingleton() {}

    private static class SingletonHelper {
        private static final BillPughSingleton INSTANCE = new BillPughSingleton();
    }

    public static BillPughSingleton getInstance() {
        return SingletonHelper.INSTANCE;  // Loaded only when accessed
    }
}

// 4. Enum Singleton (best - prevents reflection attacks)
public enum EnumSingleton {
    INSTANCE;

    public void doSomething() { /* ... */ }
}
```

### Factory Pattern

```java
// Simple Factory
public class PaymentProcessorFactory {
    public static PaymentProcessor create(PaymentMethod method) {
        return switch (method) {
            case CREDIT_CARD -> new CreditCardProcessor();
            case PAYPAL -> new PayPalProcessor();
            case BANK_TRANSFER -> new BankTransferProcessor();
        };
    }
}

// Abstract Factory
public interface UIFactory {
    Button createButton();
    TextField createTextField();
    Checkbox createCheckbox();
}

public class WindowsUIFactory implements UIFactory {
    public Button createButton() { return new WindowsButton(); }
    public TextField createTextField() { return new WindowsTextField(); }
    public Checkbox createCheckbox() { return new WindowsCheckbox(); }
}

public class MacUIFactory implements UIFactory {
    public Button createButton() { return new MacButton(); }
    public TextField createTextField() { return new MacTextField(); }
    public Checkbox createCheckbox() { return new MacCheckbox(); }
}

// Usage
public class Application {
    private UIFactory uiFactory;

    public Application(UIFactory factory) {
        this.uiFactory = factory;
    }

    public void createUI() {
        Button btn = uiFactory.createButton();
        TextField tf = uiFactory.createTextField();
        // All components are from same family
    }
}
```

### Builder Pattern

```java
public class HttpRequest {
    private final String url;
    private final String method;
    private final Map<String, String> headers;
    private final String body;
    private final Duration timeout;

    private HttpRequest(Builder builder) {
        this.url = builder.url;
        this.method = builder.method;
        this.headers = Map.copyOf(builder.headers);
        this.body = builder.body;
        this.timeout = builder.timeout;
    }

    public static class Builder {
        private final String url;  // Required
        private String method = "GET";
        private Map<String, String> headers = new HashMap<>();
        private String body;
        private Duration timeout = Duration.ofSeconds(30);

        public Builder(String url) {
            this.url = Objects.requireNonNull(url);
        }

        public Builder method(String method) {
            this.method = method;
            return this;
        }

        public Builder header(String name, String value) {
            headers.put(name, value);
            return this;
        }

        public Builder body(String body) {
            this.body = body;
            return this;
        }

        public Builder timeout(Duration timeout) {
            this.timeout = timeout;
            return this;
        }

        public HttpRequest build() {
            // Validation
            if (body != null && "GET".equals(method)) {
                throw new IllegalStateException("GET requests cannot have body");
            }
            return new HttpRequest(this);
        }
    }
}

// Usage
HttpRequest request = new HttpRequest.Builder("https://api.example.com")
    .method("POST")
    .header("Content-Type", "application/json")
    .header("Authorization", "Bearer token")
    .body("{\"key\": \"value\"}")
    .timeout(Duration.ofSeconds(10))
    .build();
```

---

## Structural Patterns

### Adapter Pattern

```java
// Target interface
public interface MediaPlayer {
    void play(String filename);
}

// Adaptee (incompatible interface)
public class VLCPlayer {
    public void playVLC(String filename) { /* VLC specific */ }
}

public class MP4Player {
    public void playMP4(String filename) { /* MP4 specific */ }
}

// Adapter
public class MediaAdapter implements MediaPlayer {
    private VLCPlayer vlcPlayer;
    private MP4Player mp4Player;

    @Override
    public void play(String filename) {
        if (filename.endsWith(".vlc")) {
            if (vlcPlayer == null) vlcPlayer = new VLCPlayer();
            vlcPlayer.playVLC(filename);
        } else if (filename.endsWith(".mp4")) {
            if (mp4Player == null) mp4Player = new MP4Player();
            mp4Player.playMP4(filename);
        }
    }
}
```

### Decorator Pattern

```java
// Component interface
public interface Coffee {
    double getCost();
    String getDescription();
}

// Concrete component
public class SimpleCoffee implements Coffee {
    public double getCost() { return 2.0; }
    public String getDescription() { return "Coffee"; }
}

// Base decorator
public abstract class CoffeeDecorator implements Coffee {
    protected final Coffee decoratedCoffee;

    public CoffeeDecorator(Coffee coffee) {
        this.decoratedCoffee = coffee;
    }

    public double getCost() { return decoratedCoffee.getCost(); }
    public String getDescription() { return decoratedCoffee.getDescription(); }
}

// Concrete decorators
public class MilkDecorator extends CoffeeDecorator {
    public MilkDecorator(Coffee coffee) { super(coffee); }

    @Override
    public double getCost() { return super.getCost() + 0.5; }

    @Override
    public String getDescription() { return super.getDescription() + ", Milk"; }
}

public class SugarDecorator extends CoffeeDecorator {
    public SugarDecorator(Coffee coffee) { super(coffee); }

    @Override
    public double getCost() { return super.getCost() + 0.2; }

    @Override
    public String getDescription() { return super.getDescription() + ", Sugar"; }
}

// Usage
Coffee coffee = new SugarDecorator(new MilkDecorator(new SimpleCoffee()));
System.out.println(coffee.getDescription()); // Coffee, Milk, Sugar
System.out.println(coffee.getCost());        // 2.7
```

### Proxy Pattern

```java
// Subject interface
public interface Image {
    void display();
}

// Real subject (expensive to create)
public class RealImage implements Image {
    private final String filename;

    public RealImage(String filename) {
        this.filename = filename;
        loadFromDisk();  // Expensive operation
    }

    private void loadFromDisk() {
        System.out.println("Loading " + filename);
    }

    @Override
    public void display() {
        System.out.println("Displaying " + filename);
    }
}

// Proxy (lazy loading)
public class ProxyImage implements Image {
    private final String filename;
    private RealImage realImage;

    public ProxyImage(String filename) {
        this.filename = filename;
    }

    @Override
    public void display() {
        if (realImage == null) {
            realImage = new RealImage(filename);  // Load only when needed
        }
        realImage.display();
    }
}
```

---

## Behavioral Patterns

### Strategy Pattern

```java
// Strategy interface
@FunctionalInterface
public interface CompressionStrategy {
    byte[] compress(byte[] data);
}

// Concrete strategies
public class ZipCompression implements CompressionStrategy {
    @Override
    public byte[] compress(byte[] data) {
        // ZIP compression logic
        return compressedData;
    }
}

public class GzipCompression implements CompressionStrategy {
    @Override
    public byte[] compress(byte[] data) {
        // GZIP compression logic
        return compressedData;
    }
}

// Context
public class FileCompressor {
    private CompressionStrategy strategy;

    public void setStrategy(CompressionStrategy strategy) {
        this.strategy = strategy;
    }

    public byte[] compressFile(byte[] fileData) {
        return strategy.compress(fileData);
    }
}

// Usage
FileCompressor compressor = new FileCompressor();
compressor.setStrategy(new ZipCompression());
byte[] compressed = compressor.compressFile(data);

// With lambda (functional interface)
compressor.setStrategy(data -> customCompress(data));
```

### Observer Pattern

```java
// Subject
public class EventManager {
    private Map<String, List<EventListener>> listeners = new HashMap<>();

    public void subscribe(String eventType, EventListener listener) {
        listeners.computeIfAbsent(eventType, k -> new ArrayList<>()).add(listener);
    }

    public void unsubscribe(String eventType, EventListener listener) {
        listeners.getOrDefault(eventType, Collections.emptyList()).remove(listener);
    }

    public void notify(String eventType, Object data) {
        listeners.getOrDefault(eventType, Collections.emptyList())
            .forEach(listener -> listener.update(eventType, data));
    }
}

// Observer interface
@FunctionalInterface
public interface EventListener {
    void update(String eventType, Object data);
}

// Usage
EventManager events = new EventManager();
events.subscribe("order.created", (type, data) -> sendEmail((Order) data));
events.subscribe("order.created", (type, data) -> updateInventory((Order) data));
events.notify("order.created", newOrder);
```

### Template Method Pattern

```java
public abstract class DataProcessor {

    // Template method (final to prevent override)
    public final void process() {
        readData();
        processData();
        writeData();
        if (shouldNotify()) {
            notifyComplete();
        }
    }

    // Abstract methods (must be implemented)
    protected abstract void readData();
    protected abstract void processData();
    protected abstract void writeData();

    // Hook methods (optional override)
    protected boolean shouldNotify() {
        return true;
    }

    protected void notifyComplete() {
        System.out.println("Processing complete");
    }
}

public class CSVProcessor extends DataProcessor {
    @Override
    protected void readData() {
        System.out.println("Reading CSV file");
    }

    @Override
    protected void processData() {
        System.out.println("Processing CSV data");
    }

    @Override
    protected void writeData() {
        System.out.println("Writing processed data");
    }
}
```

---

## Interview Questions

### Q1: Difference between Abstract Class and Interface?

| Abstract Class | Interface |
|----------------|-----------|
| Can have state (fields) | Only constants (static final) |
| Can have constructor | No constructor |
| Single inheritance | Multiple inheritance |
| Can have any access modifier | Public by default |
| Use for IS-A + shared code | Use for CAN-DO capability |

### Q2: When to use Composition vs Inheritance?

```java
// Prefer COMPOSITION when:
// - "HAS-A" relationship
// - Need flexibility to change behavior at runtime
// - Avoiding fragile base class problem

public class Car {
    private Engine engine;  // HAS-A
    private Transmission transmission;

    public void drive() {
        engine.start();
        transmission.shift(1);
    }
}

// Use INHERITANCE when:
// - True "IS-A" relationship
// - Need to override behavior
// - Liskov Substitution holds

public class ElectricCar extends Car {
    @Override
    public void start() {
        // Electric specific startup
    }
}
```

### Q3: Explain Method Overloading vs Overriding

```java
// OVERLOADING: Same method name, different parameters (compile-time)
public class Calculator {
    public int add(int a, int b) { return a + b; }
    public double add(double a, double b) { return a + b; }
    public int add(int a, int b, int c) { return a + b + c; }
}

// OVERRIDING: Same signature, different implementation (runtime)
public class Animal {
    public void speak() { System.out.println("Some sound"); }
}

public class Dog extends Animal {
    @Override
    public void speak() { System.out.println("Bark"); }
}
```
