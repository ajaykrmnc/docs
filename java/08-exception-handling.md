# Exception Handling and Error Management - Deep Dive

## Table of Contents
1. [Exception Hierarchy](#exception-hierarchy)
2. [Checked vs Unchecked Exceptions](#checked-vs-unchecked)
3. [Exception Handling Internals](#exception-internals)
4. [Best Practices](#best-practices)
5. [Custom Exceptions](#custom-exceptions)
6. [Exception Handling Patterns](#exception-patterns)
7. [Try-with-Resources](#try-with-resources)
8. [Interview Questions](#interview-questions)

---

## Exception Hierarchy

### Complete Exception Class Hierarchy

```
java.lang.Object
    └── java.lang.Throwable
            │
            ├── java.lang.Error (Unchecked - Don't catch!)
            │       ├── OutOfMemoryError
            │       ├── StackOverflowError
            │       ├── VirtualMachineError
            │       ├── NoClassDefFoundError
            │       ├── LinkageError
            │       ├── AssertionError
            │       └── ExceptionInInitializerError
            │
            └── java.lang.Exception
                    │
                    ├── RuntimeException (Unchecked)
                    │       ├── NullPointerException
                    │       ├── IllegalArgumentException
                    │       │       └── NumberFormatException
                    │       ├── IllegalStateException
                    │       ├── IndexOutOfBoundsException
                    │       │       ├── ArrayIndexOutOfBoundsException
                    │       │       └── StringIndexOutOfBoundsException
                    │       ├── ClassCastException
                    │       ├── ArithmeticException
                    │       ├── UnsupportedOperationException
                    │       ├── ConcurrentModificationException
                    │       └── NoSuchElementException
                    │
                    └── Checked Exceptions (Must be handled)
                            ├── IOException
                            │       ├── FileNotFoundException
                            │       ├── EOFException
                            │       └── SocketException
                            ├── SQLException
                            ├── ClassNotFoundException
                            ├── InterruptedException
                            ├── ReflectiveOperationException
                            └── ParseException
```

### Memory Layout of Exception

```
Exception Object:
┌────────────────────────────────────────────────────────────────┐
│ Object Header                                                   │
├────────────────────────────────────────────────────────────────┤
│ detailMessage: String                                          │ ← Error message
├────────────────────────────────────────────────────────────────┤
│ cause: Throwable                                               │ ← Chained exception
├────────────────────────────────────────────────────────────────┤
│ stackTrace: StackTraceElement[]                                │ ← Call stack
├────────────────────────────────────────────────────────────────┤
│ suppressedExceptions: List<Throwable>                          │ ← try-with-resources
└────────────────────────────────────────────────────────────────┘

StackTraceElement:
┌────────────────────────────────────────────────────────────────┐
│ declaringClass: String    │ e.g., "java.lang.String"          │
│ methodName: String        │ e.g., "substring"                 │
│ fileName: String          │ e.g., "String.java"               │
│ lineNumber: int           │ e.g., 1967                        │
└────────────────────────────────────────────────────────────────┘
```

---

## Checked vs Unchecked Exceptions

### Decision Framework

```
                    ┌─────────────────────────────────────┐
                    │     Can caller reasonably recover?   │
                    └─────────────────────┬───────────────┘
                                          │
                    ┌─────────────────────┴───────────────┐
                    │                                     │
                   YES                                   NO
                    │                                     │
                    ▼                                     ▼
        ┌───────────────────────┐          ┌───────────────────────────┐
        │   Checked Exception   │          │   Is it a programming     │
        │                       │          │          error?           │
        │  - IOException        │          └─────────────┬─────────────┘
        │  - SQLException       │                        │
        │  - Custom checked     │          ┌─────────────┴─────────────┐
        └───────────────────────┘          │                           │
                                          YES                          NO
                                           │                           │
                                           ▼                           ▼
                               ┌───────────────────────┐  ┌────────────────────────┐
                               │ RuntimeException      │  │ Error (serious)        │
                               │                       │  │ OR                     │
                               │ - NullPointerException│  │ RuntimeException       │
                               │ - IllegalArgument     │  │ (unrecoverable logic)  │
                               └───────────────────────┘  └────────────────────────┘
```

### Examples with Rationale

```java
public class ExceptionDesignDemo {
    
    // CHECKED: Caller can and should handle
    // - File might not exist, but caller can provide alternative
    public String readConfig(String path) throws IOException {
        return Files.readString(Path.of(path));
    }
    
    // UNCHECKED: Programming error - null should never be passed
    public void process(Object data) {
        if (data == null) {
            throw new IllegalArgumentException("data cannot be null");
        }
        // Process data
    }
    
    // UNCHECKED: Programming error - invalid state
    public void withdraw(double amount) {
        if (!isAccountActive) {
            throw new IllegalStateException("Account is not active");
        }
        if (amount > balance) {
            // Could be checked if recovery is expected
            throw new InsufficientBalanceException("Insufficient funds");
        }
    }
    
    // Custom checked exception for business logic recovery
    public class InsufficientBalanceException extends Exception {
        private final double available;
        private final double requested;
        
        public InsufficientBalanceException(String message, double available, double requested) {
            super(message);
            this.available = available;
            this.requested = requested;
        }
        
        public double getShortfall() {
            return requested - available;
        }
    }
}
```

---

## Exception Handling Internals

### Exception Table in Bytecode

When you write a try-catch block, the compiler generates an exception table:

```java
// Source code
public void method() {
    try {
        mayThrow();
    } catch (IOException e) {
        handle(e);
    } finally {
        cleanup();
    }
}

// Bytecode exception table (simplified)
Exception table:
   from    to  target type
     0     4     8   Class java/io/IOException  // try block → catch
     0     4    16   any                        // try block → finally
     8    12    16   any                        // catch block → finally
```

### Stack Unwinding Process

```
Stack During Exception Propagation:
                                                                
┌──────────────────┐                                           
│    method3()     │ ← Exception thrown here                    
│    line 45       │   throw new IOException()                  
├──────────────────┤                                           
│    method2()     │ ← No handler, unwind                       
│    line 23       │                                           
├──────────────────┤                                           
│    method1()     │ ← Has catch(IOException), handle here      
│    line 12       │                                           
├──────────────────┤                                           
│    main()        │                                           
└──────────────────┘                                           

Process:
1. Exception created (expensive - captures stack trace)
2. JVM searches current method's exception table
3. If no handler found, unwind to caller
4. Repeat until handler found or thread terminates
5. Execute finally blocks during unwinding
```

---

## Best Practices

### 1. Exception Handling Patterns

```java
// 1. Don't catch Exception or Throwable
// BAD
try {
    doSomething();
} catch (Exception e) {  // Catches everything!
    e.printStackTrace();
}

// GOOD - Catch specific exceptions
try {
    doSomething();
} catch (IOException e) {
    handleIOError(e);
} catch (SQLException e) {
    handleDBError(e);
}

// 2. Don't swallow exceptions
// BAD
try {
    doSomething();
} catch (IOException e) {
    // Empty catch - exception lost!
}

// GOOD - At minimum, log it
try {
    doSomething();
} catch (IOException e) {
    logger.error("Operation failed", e);
    throw new ServiceException("Operation failed", e);
}

// 3. Use exception chaining
// GOOD - Preserve original cause
try {
    readFile();
} catch (IOException e) {
    throw new ConfigurationException("Failed to load config", e);
}
```

### 2. Resource Management

```java
// BAD - Manual resource management (error-prone)
FileInputStream fis = null;
try {
    fis = new FileInputStream("file.txt");
    // use fis
} catch (IOException e) {
    // handle
} finally {
    if (fis != null) {
        try {
            fis.close();  // Can also throw!
        } catch (IOException e) {
            // Suppress or log
        }
    }
}

// GOOD - Try-with-resources (Java 7+)
try (FileInputStream fis = new FileInputStream("file.txt");
     BufferedInputStream bis = new BufferedInputStream(fis)) {
    // use streams
} catch (IOException e) {
    // handle
}
// Both streams automatically closed in reverse order
```

### 3. Exception Translation

```java
public class UserService {
    private final UserRepository repository;

    // Translate low-level exceptions to domain exceptions
    public User findUser(int id) throws UserNotFoundException {
        try {
            return repository.findById(id)
                .orElseThrow(() -> new UserNotFoundException("User not found: " + id));
        } catch (SQLException e) {
            throw new DataAccessException("Database error while finding user", e);
        }
    }
}
```

---

## Custom Exceptions

### Designing Custom Exceptions

```java
// Base domain exception
public class DomainException extends RuntimeException {
    private final ErrorCode errorCode;

    public DomainException(ErrorCode errorCode, String message) {
        super(message);
        this.errorCode = errorCode;
    }

    public DomainException(ErrorCode errorCode, String message, Throwable cause) {
        super(message, cause);
        this.errorCode = errorCode;
    }

    public ErrorCode getErrorCode() {
        return errorCode;
    }
}

public enum ErrorCode {
    USER_NOT_FOUND("USR001"),
    INVALID_CREDENTIALS("USR002"),
    INSUFFICIENT_BALANCE("PAY001"),
    PAYMENT_FAILED("PAY002");

    private final String code;

    ErrorCode(String code) { this.code = code; }
    public String getCode() { return code; }
}

// Specific exceptions
public class UserNotFoundException extends DomainException {
    public UserNotFoundException(String userId) {
        super(ErrorCode.USER_NOT_FOUND, "User not found: " + userId);
    }
}

public class InsufficientBalanceException extends DomainException {
    private final BigDecimal available;
    private final BigDecimal required;

    public InsufficientBalanceException(BigDecimal available, BigDecimal required) {
        super(ErrorCode.INSUFFICIENT_BALANCE,
            String.format("Insufficient balance. Available: %s, Required: %s", available, required));
        this.available = available;
        this.required = required;
    }

    public BigDecimal getShortfall() {
        return required.subtract(available);
    }
}
```

---

## Try-with-Resources Deep Dive

### AutoCloseable Interface

```java
public interface AutoCloseable {
    void close() throws Exception;
}

// Custom resource
public class DatabaseConnection implements AutoCloseable {
    private Connection connection;

    public DatabaseConnection(String url) throws SQLException {
        this.connection = DriverManager.getConnection(url);
    }

    @Override
    public void close() throws SQLException {
        if (connection != null && !connection.isClosed()) {
            connection.close();
        }
    }
}

// Usage
try (DatabaseConnection db = new DatabaseConnection(url)) {
    // use db
}  // Automatically closed
```

### Suppressed Exceptions

```java
public class SuppressedExceptionDemo {

    public void demonstrateSuppression() {
        try (ProblematicResource resource = new ProblematicResource()) {
            resource.doWork();  // Throws WorkException
        } catch (Exception e) {
            System.out.println("Primary: " + e.getMessage());

            // Access suppressed exceptions
            for (Throwable suppressed : e.getSuppressed()) {
                System.out.println("Suppressed: " + suppressed.getMessage());
            }
        }
    }
}

class ProblematicResource implements AutoCloseable {
    public void doWork() throws WorkException {
        throw new WorkException("Work failed");
    }

    @Override
    public void close() throws CloseException {
        throw new CloseException("Close failed");  // This is suppressed
    }
}
```

### Effectively Final in Try-with-Resources (Java 9+)

```java
// Java 7/8 - Variable must be declared in try
try (BufferedReader br = new BufferedReader(new FileReader(path))) {
    // use br
}

// Java 9+ - Effectively final variables work
BufferedReader br = new BufferedReader(new FileReader(path));
try (br) {  // br is effectively final
    // use br
}
```

---

## Exception Performance

### Cost of Exceptions

```java
public class ExceptionPerformance {

    // Exceptions are expensive due to:
    // 1. Stack trace capture (fillInStackTrace)
    // 2. Stack unwinding
    // 3. Object creation

    // If stack trace not needed, can skip it
    public class FastException extends RuntimeException {
        public FastException(String message) {
            super(message, null, true, false);  // Don't capture stack trace
        }
    }

    // Pre-created exception (for very hot paths)
    private static final IndexOutOfBoundsException INDEX_EXCEPTION =
        new IndexOutOfBoundsException();

    // Don't use exceptions for flow control!
    // BAD
    public int findIndexBad(int[] arr, int value) {
        try {
            for (int i = 0; ; i++) {
                if (arr[i] == value) return i;
            }
        } catch (ArrayIndexOutOfBoundsException e) {
            return -1;
        }
    }

    // GOOD
    public int findIndexGood(int[] arr, int value) {
        for (int i = 0; i < arr.length; i++) {
            if (arr[i] == value) return i;
        }
        return -1;
    }
}
```

---

## Interview Questions

### Q1: What happens if both try and finally throw exceptions?

```java
try {
    throw new RuntimeException("Try exception");
} finally {
    throw new RuntimeException("Finally exception");
}
// Result: "Finally exception" is thrown, "Try exception" is lost!
// Use try-with-resources to avoid this (try exception suppresses close exception)
```

### Q2: Can you return from finally block?

```java
// Yes, but DON'T DO IT!
public int badMethod() {
    try {
        return 1;
    } finally {
        return 2;  // This overwrites the try return!
    }
}
// Returns 2, not 1!
```

### Q3: What is the difference between throw and throws?

```java
// throw - Actually throws an exception
public void validate(String input) {
    if (input == null) {
        throw new IllegalArgumentException("Input cannot be null");
    }
}

// throws - Declares that method might throw exception
public void readFile(String path) throws IOException {
    Files.readString(Path.of(path));
}
```

### Q4: When does finally NOT execute?

```java
// 1. System.exit() called
try {
    System.exit(0);
} finally {
    System.out.println("Never printed");
}

// 2. JVM crashes
// 3. Infinite loop or thread killed before finally
// 4. Power outage (obviously)
```
