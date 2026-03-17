# Design a Logging Framework
**Difficulty:** Medium-Hard | **Companies:** All Tier-1 (Google, Amazon, Meta, Microsoft)

---

## Problem Statement

Design a high-performance, extensible logging framework with support for multiple log levels, async logging, multiple appenders, and structured logging.

---

## Requirements

### Functional Requirements
1. Multiple log levels (TRACE, DEBUG, INFO, WARN, ERROR, FATAL)
2. Hierarchical loggers with inheritance
3. Multiple appenders (Console, File, Network)
4. Async logging with bounded queue
5. Log formatting with patterns
6. MDC (Mapped Diagnostic Context) support
7. Log rotation and compression

### Non-Functional Requirements
1. Minimal performance overhead
2. Thread-safe
3. Non-blocking async logging
4. Extensible appender and formatter architecture

---

## Class Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                         Logger                                  │
├─────────────────────────────────────────────────────────────────┤
│ - name: String                                                  │
│ - level: LogLevel                                               │
│ - appenders: List<Appender>                                     │
│ - parent: Logger                                                │
│ - additive: boolean                                             │
├─────────────────────────────────────────────────────────────────┤
│ + trace(msg: String, args: Object...): void                     │
│ + debug(msg: String, args: Object...): void                     │
│ + info(msg: String, args: Object...): void                      │
│ + warn(msg: String, args: Object...): void                      │
│ + error(msg: String, args: Object...): void                     │
│ + error(msg: String, throwable: Throwable): void                │
│ + isEnabled(level: LogLevel): boolean                           │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                        LogEvent                                 │
├─────────────────────────────────────────────────────────────────┤
│ - timestamp: Instant                                            │
│ - level: LogLevel                                               │
│ - loggerName: String                                            │
│ - message: String                                               │
│ - arguments: Object[]                                           │
│ - throwable: Throwable                                          │
│ - threadName: String                                            │
│ - threadId: long                                                │
│ - mdc: Map<String, String>                                      │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                  <<interface>> Appender                         │
├─────────────────────────────────────────────────────────────────┤
│ + append(event: LogEvent): void                                 │
│ + start(): void                                                 │
│ + stop(): void                                                  │
│ + isStarted(): boolean                                          │
└─────────────────────────────────────────────────────────────────┘
         △
         │
   ┌─────┴──────┬──────────────┬────────────────┐
   │            │              │                │
┌──┴────┐  ┌────┴────┐   ┌─────┴─────┐   ┌──────┴──────┐
│Console│  │  File   │   │  Async    │   │  Network    │
│Appender│  │Appender │   │ Appender  │   │  Appender   │
└───────┘  └─────────┘   └───────────┘   └─────────────┘
```

---

## Class Implementations

### 1. LogLevel Enum
```java
public enum LogLevel {
    TRACE(0),
    DEBUG(1),
    INFO(2),
    WARN(3),
    ERROR(4),
    FATAL(5),
    OFF(Integer.MAX_VALUE);
    
    private final int severity;
    
    LogLevel(int severity) {
        this.severity = severity;
    }
    
    public boolean isEnabledFor(LogLevel threshold) {
        return this.severity >= threshold.severity;
    }
}
```

### 2. MDC (Mapped Diagnostic Context)
```java
public class MDC {
    private static final ThreadLocal<Map<String, String>> contextMap = 
        ThreadLocal.withInitial(HashMap::new);
    
    public static void put(String key, String value) {
        contextMap.get().put(key, value);
    }
    
    public static String get(String key) {
        return contextMap.get().get(key);
    }
    
    public static void remove(String key) {
        contextMap.get().remove(key);
    }
    
    public static void clear() {
        contextMap.get().clear();
    }
    
    public static Map<String, String> getCopyOfContextMap() {
        return new HashMap<>(contextMap.get());
    }
    
    public static void setContextMap(Map<String, String> map) {
        contextMap.set(new HashMap<>(map));
    }
}
```

### 3. Logger Implementation
```java
public class Logger {
    private static final LoggerFactory factory = LoggerFactory.getInstance();
    
    private final String name;
    private volatile LogLevel level;
    private final List<Appender> appenders;
    private Logger parent;
    private boolean additive = true;
    
    Logger(String name) {
        this.name = name;
        this.appenders = new CopyOnWriteArrayList<>();
    }
    
    public void info(String message, Object... args) {
        log(LogLevel.INFO, message, args, null);
    }
    
    public void error(String message, Throwable throwable) {
        log(LogLevel.ERROR, message, null, throwable);
    }
    
    private void log(LogLevel level, String message, Object[] args, Throwable t) {
        if (!isEnabled(level)) return;
        
        LogEvent event = LogEvent.builder()
            .timestamp(Instant.now())
            .level(level)
            .loggerName(name)
            .message(message)
            .arguments(args)
            .throwable(t)
            .threadName(Thread.currentThread().getName())
            .threadId(Thread.currentThread().getId())
            .mdc(MDC.getCopyOfContextMap())
            .build();
        
        callAppenders(event);
    }
    
    private void callAppenders(LogEvent event) {
        for (Appender appender : appenders) {
            appender.append(event);
        }
        if (additive && parent != null) {
            parent.callAppenders(event);
        }
    }
    
    public boolean isEnabled(LogLevel level) {
        LogLevel effectiveLevel = getEffectiveLevel();
        return level.isEnabledFor(effectiveLevel);
    }
    
    private LogLevel getEffectiveLevel() {
        if (level != null) return level;
        if (parent != null) return parent.getEffectiveLevel();
        return LogLevel.INFO;
    }
    
    public void addAppender(Appender appender) {
        appenders.add(appender);
    }
}
```

### 4. Async Appender (Decorator Pattern)
```java
public class AsyncAppender implements Appender {
    private final Appender delegate;
    private final BlockingQueue<LogEvent> queue;
    private final Thread dispatcherThread;
    private volatile boolean running;
    private final int discardThreshold;
    
    public AsyncAppender(Appender delegate, int queueSize) {
        this.delegate = delegate;
        this.queue = new ArrayBlockingQueue<>(queueSize);
        this.discardThreshold = (int) (queueSize * 0.8);
        this.dispatcherThread = new Thread(this::dispatch, "AsyncAppender");
    }
    
    @Override
    public void append(LogEvent event) {
        if (!running) return;
        
        // Discard low priority logs when queue is filling up
        if (queue.size() > discardThreshold) {
            if (event.getLevel().ordinal() < LogLevel.WARN.ordinal()) {
                return;  // Discard TRACE, DEBUG, INFO when overloaded
            }
        }
        
        if (!queue.offer(event)) {
            // Queue full - handle overflow
            handleOverflow(event);
        }
    }
    
    private void dispatch() {
        while (running || !queue.isEmpty()) {
            try {
                LogEvent event = queue.poll(100, TimeUnit.MILLISECONDS);
                if (event != null) {
                    delegate.append(event);
                }
            } catch (InterruptedException e) {
                Thread.currentThread().interrupt();
                break;
            }
        }
    }
    
    @Override
    public void start() {
        running = true;
        delegate.start();
        dispatcherThread.start();
    }
    
    @Override
    public void stop() {
        running = false;
        try {
            dispatcherThread.join(5000);
        } catch (InterruptedException e) {
            Thread.currentThread().interrupt();
        }
        delegate.stop();
    }
}
```

### 5. File Appender with Rotation
```java
public class RollingFileAppender implements Appender {
    private final String filePattern;
    private final long maxFileSize;
    private final int maxHistory;
    private final LogFormatter formatter;
    private BufferedWriter writer;
    private Path currentFile;
    private long currentSize;
    
    @Override
    public synchronized void append(LogEvent event) {
        try {
            String formatted = formatter.format(event);
            writer.write(formatted);
            writer.newLine();
            currentSize += formatted.length();
            
            if (currentSize >= maxFileSize) {
                rollover();
            }
        } catch (IOException e) {
            // Handle error
        }
    }
    
    private void rollover() throws IOException {
        writer.close();
        Path archived = Paths.get(filePattern + "." + Instant.now().toEpochMilli());
        Files.move(currentFile, archived);
        compressAsync(archived);
        cleanOldFiles();
        openNewFile();
    }
}
```

