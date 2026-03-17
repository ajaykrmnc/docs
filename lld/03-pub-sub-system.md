# Design a Pub-Sub Messaging System
**Difficulty:** Hard | **Companies:** Google (Pub/Sub), AWS (SNS/SQS), Meta, LinkedIn

---

## Problem Statement

Design a publisher-subscriber messaging system that enables asynchronous communication between services with guaranteed delivery and multiple subscription models.

---

## Requirements

### Functional Requirements
1. Publishers can publish messages to topics
2. Subscribers can subscribe to topics (push or pull model)
3. Support topic-based and content-based filtering
4. At-least-once and exactly-once delivery semantics
5. Message ordering guarantees within partitions
6. Dead letter queue for failed messages
7. Message acknowledgment and retry mechanism

### Non-Functional Requirements
1. High throughput (millions of messages per second)
2. Low latency message delivery
3. Horizontal scalability
4. Fault tolerance and message durability

---

## Class Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                       MessageBroker                             │
├─────────────────────────────────────────────────────────────────┤
│ - topics: Map<String, Topic>                                    │
│ - subscriptions: Map<String, List<Subscription>>                │
│ - messageStore: MessageStore                                    │
│ - deliveryService: DeliveryService                              │
├─────────────────────────────────────────────────────────────────┤
│ + createTopic(name: String): Topic                              │
│ + deleteTopic(name: String): void                               │
│ + publish(topicName: String, message: Message): MessageId       │
│ + subscribe(topicName: String, sub: Subscription): void         │
│ + unsubscribe(subscriptionId: String): void                     │
│ + acknowledge(subscriptionId: String, messageId: String): void  │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                          Topic                                  │
├─────────────────────────────────────────────────────────────────┤
│ - topicId: String                                               │
│ - name: String                                                  │
│ - partitions: List<Partition>                                   │
│ - retentionPeriod: Duration                                     │
│ - subscriptions: List<Subscription>                             │
├─────────────────────────────────────────────────────────────────┤
│ + addPartition(): void                                          │
│ + getPartition(key: String): Partition                          │
│ + publish(message: Message): void                               │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                        Subscription                             │
├─────────────────────────────────────────────────────────────────┤
│ - subscriptionId: String                                        │
│ - topicId: String                                               │
│ - subscriber: Subscriber                                        │
│ - deliveryType: DeliveryType (PUSH/PULL)                        │
│ - filter: MessageFilter                                         │
│ - ackDeadline: Duration                                         │
│ - maxRetries: int                                               │
│ - deadLetterTopic: Topic                                        │
├─────────────────────────────────────────────────────────────────┤
│ + matches(message: Message): boolean                            │
│ + deliver(message: Message): DeliveryResult                     │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                         Message                                 │
├─────────────────────────────────────────────────────────────────┤
│ - messageId: String                                             │
│ - payload: byte[]                                               │
│ - attributes: Map<String, String>                               │
│ - publishTime: Instant                                          │
│ - orderingKey: String                                           │
│ - deduplicationId: String                                       │
└─────────────────────────────────────────────────────────────────┘
```

---

## Class Implementations

### 1. Message
```java
public class Message {
    private final String messageId;
    private final byte[] payload;
    private final Map<String, String> attributes;
    private final Instant publishTime;
    private final String orderingKey;      // For ordered delivery
    private final String deduplicationId;  // For exactly-once
    
    private Message(Builder builder) {
        this.messageId = UUID.randomUUID().toString();
        this.payload = builder.payload;
        this.attributes = Map.copyOf(builder.attributes);
        this.publishTime = Instant.now();
        this.orderingKey = builder.orderingKey;
        this.deduplicationId = builder.deduplicationId;
    }
    
    public static class Builder {
        private byte[] payload;
        private Map<String, String> attributes = new HashMap<>();
        private String orderingKey;
        private String deduplicationId;
        
        public Builder payload(byte[] payload) {
            this.payload = payload;
            return this;
        }
        
        public Builder attribute(String key, String value) {
            this.attributes.put(key, value);
            return this;
        }
        
        public Builder orderingKey(String key) {
            this.orderingKey = key;
            return this;
        }
        
        public Message build() {
            return new Message(this);
        }
    }
}
```

### 2. Topic with Partitioning
```java
public class Topic {
    private final String topicId;
    private final String name;
    private final List<Partition> partitions;
    private final CopyOnWriteArrayList<Subscription> subscriptions;
    private final Duration retentionPeriod;
    private final PartitionStrategy partitionStrategy;
    
    public Topic(String name, int numPartitions, Duration retention) {
        this.topicId = UUID.randomUUID().toString();
        this.name = name;
        this.partitions = new ArrayList<>();
        this.subscriptions = new CopyOnWriteArrayList<>();
        this.retentionPeriod = retention;
        this.partitionStrategy = new HashPartitionStrategy();
        
        for (int i = 0; i < numPartitions; i++) {
            partitions.add(new Partition(i));
        }
    }
    
    public void publish(Message message) {
        Partition partition = partitionStrategy.selectPartition(
            message.getOrderingKey(), 
            partitions
        );
        partition.append(message);
        notifySubscribers(message);
    }
    
    private void notifySubscribers(Message message) {
        for (Subscription sub : subscriptions) {
            if (sub.matches(message)) {
                sub.deliver(message);
            }
        }
    }
}

class Partition {
    private final int partitionId;
    private final List<Message> messages;
    private final AtomicLong offset;
    private final ReentrantReadWriteLock lock;
    
    public void append(Message message) {
        lock.writeLock().lock();
        try {
            messages.add(message);
            offset.incrementAndGet();
        } finally {
            lock.writeLock().unlock();
        }
    }
    
    public List<Message> read(long fromOffset, int maxMessages) {
        lock.readLock().lock();
        try {
            int start = (int) fromOffset;
            int end = Math.min(start + maxMessages, messages.size());
            return new ArrayList<>(messages.subList(start, end));
        } finally {
            lock.readLock().unlock();
        }
    }
}
```

### 3. Subscription with Filtering
```java
public class Subscription {
    private final String subscriptionId;
    private final String topicId;
    private final Subscriber subscriber;
    private final DeliveryType deliveryType;
    private final MessageFilter filter;
    private final Duration ackDeadline;
    private final int maxRetries;
    private final Topic deadLetterTopic;
    private final Map<String, PendingMessage> pendingAcks;
    
    public boolean matches(Message message) {
        return filter == null || filter.matches(message);
    }
    
    public void deliver(Message message) {
        if (deliveryType == DeliveryType.PUSH) {
            pushMessage(message);
        } else {
            // PULL: Store for later retrieval
            pendingAcks.put(message.getMessageId(), 
                new PendingMessage(message, Instant.now()));
        }
    }
    
    private void pushMessage(Message message) {
        CompletableFuture.runAsync(() -> {
            int attempts = 0;
            while (attempts < maxRetries) {
                try {
                    subscriber.onMessage(message);
                    return;
                } catch (Exception e) {
                    attempts++;
                    exponentialBackoff(attempts);
                }
            }
            // Move to dead letter queue
            if (deadLetterTopic != null) {
                deadLetterTopic.publish(message);
            }
        });
    }
}
```

