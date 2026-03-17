# Design a Notification System
**Difficulty:** Hard | **Companies:** Meta, Google, Apple, Amazon, Netflix

---

## Problem Statement

Design a multi-channel notification system with priority-based delivery, user preferences, templates, and delivery tracking.

---

## Requirements

### Functional Requirements
1. Multiple channels: Push, SMS, Email, In-App
2. Priority-based delivery with rate limiting
3. User preference management
4. Template engine with personalization
5. Delivery tracking and analytics
6. Batching and digest notifications
7. Retry with exponential backoff

### Non-Functional Requirements
1. High throughput (millions of notifications/day)
2. Low latency for urgent notifications
3. At-least-once delivery guarantee
4. Fault tolerance

---

## Class Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                   NotificationService                           │
├─────────────────────────────────────────────────────────────────┤
│ - channelRegistry: Map<ChannelType, Channel>                    │
│ - templateEngine: TemplateEngine                                │
│ - preferenceStore: UserPreferenceStore                          │
│ - rateLimiter: NotificationRateLimiter                          │
│ - deliveryTracker: DeliveryTracker                              │
│ - priorityQueues: Map<Priority, BlockingQueue<Notification>>    │
├─────────────────────────────────────────────────────────────────┤
│ + send(notification: Notification): NotificationResult          │
│ + sendBulk(notifications: List<Notification>): BatchResult      │
│ + schedule(notification: Notification, time: Instant): void     │
│ + getDeliveryStatus(notificationId: String): DeliveryStatus     │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                      Notification                               │
├─────────────────────────────────────────────────────────────────┤
│ - notificationId: String                                        │
│ - userId: String                                                │
│ - type: NotificationType                                        │
│ - channels: List<ChannelType>                                   │
│ - priority: Priority                                            │
│ - template: String                                              │
│ - data: Map<String, Object>                                     │
│ - scheduledTime: Instant                                        │
│ - expiresAt: Instant                                            │
├─────────────────────────────────────────────────────────────────┤
│ + render(engine: TemplateEngine): RenderedContent               │
│ + isExpired(): boolean                                          │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                  <<interface>> Channel                          │
├─────────────────────────────────────────────────────────────────┤
│ + send(content: RenderedContent, recipient: Recipient): Result  │
│ + getType(): ChannelType                                        │
│ + isAvailable(): boolean                                        │
└─────────────────────────────────────────────────────────────────┘
         △
    ┌────┴────┬──────────┬────────────┐
    │         │          │            │
  Push     Email       SMS        InApp
 Channel   Channel    Channel    Channel
```

---

## Class Implementations

### 1. Notification and Priority
```java
public class Notification {
    private final String notificationId;
    private final String userId;
    private final NotificationType type;
    private final List<ChannelType> channels;
    private final Priority priority;
    private final String templateId;
    private final Map<String, Object> data;
    private final Instant scheduledTime;
    private final Instant expiresAt;
    private int attemptCount;
    
    private Notification(Builder builder) {
        this.notificationId = UUID.randomUUID().toString();
        this.userId = builder.userId;
        this.type = builder.type;
        this.channels = builder.channels;
        this.priority = builder.priority;
        this.templateId = builder.templateId;
        this.data = Map.copyOf(builder.data);
        this.scheduledTime = builder.scheduledTime;
        this.expiresAt = builder.expiresAt;
        this.attemptCount = 0;
    }
    
    public boolean isExpired() {
        return expiresAt != null && Instant.now().isAfter(expiresAt);
    }
    
    public void incrementAttempt() {
        this.attemptCount++;
    }
    
    public static class Builder {
        private String userId;
        private NotificationType type;
        private List<ChannelType> channels = new ArrayList<>();
        private Priority priority = Priority.NORMAL;
        private String templateId;
        private Map<String, Object> data = new HashMap<>();
        private Instant scheduledTime;
        private Instant expiresAt;
        
        public Builder userId(String userId) { this.userId = userId; return this; }
        public Builder type(NotificationType type) { this.type = type; return this; }
        public Builder channel(ChannelType channel) { this.channels.add(channel); return this; }
        public Builder priority(Priority p) { this.priority = p; return this; }
        public Builder template(String id) { this.templateId = id; return this; }
        public Builder data(String key, Object value) { this.data.put(key, value); return this; }
        public Notification build() { return new Notification(this); }
    }
}

public enum Priority {
    CRITICAL(0, Duration.ZERO),
    HIGH(1, Duration.ofSeconds(5)),
    NORMAL(2, Duration.ofSeconds(30)),
    LOW(3, Duration.ofMinutes(5));
    
    private final int level;
    private final Duration maxDelay;
}
```

### 2. Channel Implementations
```java
public interface Channel {
    DeliveryResult send(RenderedContent content, Recipient recipient);
    ChannelType getType();
    boolean isAvailable();
}

public class PushChannel implements Channel {
    private final PushProvider provider;
    private final CircuitBreaker circuitBreaker;
    
    @Override
    public DeliveryResult send(RenderedContent content, Recipient recipient) {
        if (!circuitBreaker.allowRequest()) {
            return DeliveryResult.failed("Circuit breaker open");
        }
        
        try {
            PushMessage message = PushMessage.builder()
                .title(content.getTitle())
                .body(content.getBody())
                .data(content.getPayload())
                .token(recipient.getPushToken())
                .build();
            
            provider.send(message);
            circuitBreaker.recordSuccess();
            return DeliveryResult.success();
        } catch (Exception e) {
            circuitBreaker.recordFailure();
            return DeliveryResult.failed(e.getMessage());
        }
    }
}

public class EmailChannel implements Channel {
    private final EmailProvider emailProvider;
    private final TemplateEngine templateEngine;
    
    @Override
    public DeliveryResult send(RenderedContent content, Recipient recipient) {
        Email email = Email.builder()
            .to(recipient.getEmail())
            .subject(content.getTitle())
            .htmlBody(content.getHtmlBody())
            .textBody(content.getBody())
            .build();
        
        return emailProvider.send(email);
    }
}
```

### 3. User Preferences
```java
public class UserPreference {
    private final String userId;
    private Map<NotificationType, ChannelPreference> preferences;
    private boolean doNotDisturb;
    private TimeRange quietHours;
    private Set<ChannelType> globallyDisabled;
    private DigestPreference digestPreference;
    
    public List<ChannelType> getEnabledChannels(NotificationType type) {
        if (doNotDisturb || isQuietHours()) {
            return List.of();  // Or only allow CRITICAL
        }
        
        ChannelPreference pref = preferences.get(type);
        if (pref == null) {
            return getDefaultChannels(type);
        }
        
        return pref.getEnabledChannels().stream()
            .filter(c -> !globallyDisabled.contains(c))
            .collect(Collectors.toList());
    }
    
    private boolean isQuietHours() {
        if (quietHours == null) return false;
        LocalTime now = LocalTime.now();
        return quietHours.contains(now);
    }
}

public class DigestPreference {
    private boolean enabled;
    private Duration interval;  // e.g., every 4 hours
    private Set<NotificationType> digestTypes;
    private Instant lastDigestSent;
}
```

### 4. NotificationService with Priority Queues
```java
public class NotificationService {
    private final Map<Priority, BlockingQueue<Notification>> queues;
    private final Map<ChannelType, Channel> channels;
    private final UserPreferenceStore preferenceStore;
    private final TemplateEngine templateEngine;
    private final DeliveryTracker tracker;
    private final ExecutorService[] workers;
    
    public NotificationService() {
        this.queues = new EnumMap<>(Priority.class);
        for (Priority p : Priority.values()) {
            queues.put(p, new LinkedBlockingQueue<>());
        }
        // More workers for higher priority
        this.workers = new ExecutorService[4];
        startWorkers();
    }
    
    public CompletableFuture<NotificationResult> send(Notification notification) {
        UserPreference prefs = preferenceStore.get(notification.getUserId());
        List<ChannelType> enabledChannels = prefs.getEnabledChannels(notification.getType());
        
        if (enabledChannels.isEmpty()) {
            return CompletableFuture.completedFuture(
                NotificationResult.skipped("User disabled notifications")
            );
        }
        
        queues.get(notification.getPriority()).offer(notification);
        return tracker.trackAsync(notification.getNotificationId());
    }
    
    private void processNotification(Notification notification) {
        if (notification.isExpired()) {
            tracker.markExpired(notification.getNotificationId());
            return;
        }
        
        RenderedContent content = templateEngine.render(
            notification.getTemplateId(), 
            notification.getData()
        );
        
        for (ChannelType channelType : notification.getChannels()) {
            Channel channel = channels.get(channelType);
            DeliveryResult result = channel.send(content, getRecipient(notification));
            tracker.recordDelivery(notification.getNotificationId(), channelType, result);
            
            if (!result.isSuccess()) {
                scheduleRetry(notification, channelType);
            }
        }
    }
}
```

