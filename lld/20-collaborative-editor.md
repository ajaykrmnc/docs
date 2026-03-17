# Design a Real-Time Collaborative Editor
**Difficulty:** Very Hard | **Companies:** Google (Docs), Microsoft, Notion, Figma

---

## Problem Statement

Design a collaborative document editing system supporting real-time editing by multiple users, conflict resolution, version history, and offline editing.

---

## Requirements

### Functional Requirements
1. Real-time collaborative editing
2. Conflict resolution (OT or CRDT)
3. Cursor and selection sync across users
4. Version history with branching
5. Offline editing with sync on reconnect
6. Access control (view, comment, edit)
7. Comments and suggestions

### Non-Functional Requirements
1. Low latency updates (< 100ms)
2. Consistency (all users see same document)
3. Offline-first capability
4. Scale to 100+ concurrent editors

---

## Class Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                       Document                                  │
├─────────────────────────────────────────────────────────────────┤
│ - documentId: String                                            │
│ - content: String                                               │
│ - version: long                                                 │
│ - operations: List<Operation>                                   │
│ - collaborators: Map<String, Collaborator>                      │
│ - accessControl: AccessControl                                  │
├─────────────────────────────────────────────────────────────────┤
│ + apply(operation: Operation): void                             │
│ + getContent(): String                                          │
│ + getVersion(): long                                            │
│ + addCollaborator(user: User, permission: Permission): void     │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                        Operation                                │
├─────────────────────────────────────────────────────────────────┤
│ - operationId: String                                           │
│ - type: OperationType                                           │
│ - position: int                                                 │
│ - content: String                                               │
│ - length: int                                                   │
│ - userId: String                                                │
│ - timestamp: long                                               │
│ - baseVersion: long                                             │
├─────────────────────────────────────────────────────────────────┤
│ + transform(other: Operation): Operation                        │
│ + apply(document: String): String                               │
│ + inverse(): Operation                                          │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                  OperationalTransformer                         │
├─────────────────────────────────────────────────────────────────┤
│ + transform(op1: Operation, op2: Operation): TransformResult    │
│ + compose(ops: List<Operation>): Operation                      │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                      CollaborationServer                        │
├─────────────────────────────────────────────────────────────────┤
│ - documents: Map<String, Document>                              │
│ - sessions: Map<String, List<Session>>                          │
│ - transformer: OperationalTransformer                           │
│ - syncManager: SyncManager                                      │
├─────────────────────────────────────────────────────────────────┤
│ + handleOperation(docId: String, op: Operation): void           │
│ + handleCursorUpdate(docId: String, cursor: Cursor): void       │
│ + broadcast(docId: String, message: Message): void              │
└─────────────────────────────────────────────────────────────────┘
```

---

## Class Implementations

### 1. Operation Types
```java
public enum OperationType {
    INSERT, DELETE, RETAIN
}

public class Operation {
    private final String operationId;
    private final OperationType type;
    private final int position;
    private final String content;    // For INSERT
    private final int length;        // For DELETE/RETAIN
    private final String userId;
    private final long timestamp;
    private final long baseVersion;

    // Insert operation
    public static Operation insert(int position, String content, String userId, long version) {
        return new Operation(UUID.randomUUID().toString(), OperationType.INSERT,
            position, content, content.length(), userId, System.currentTimeMillis(), version);
    }

    // Delete operation
    public static Operation delete(int position, int length, String userId, long version) {
        return new Operation(UUID.randomUUID().toString(), OperationType.DELETE,
            position, null, length, userId, System.currentTimeMillis(), version);
    }

    public String apply(String document) {
        switch (type) {
            case INSERT:
                return document.substring(0, position) + content +
                       document.substring(position);
            case DELETE:
                return document.substring(0, position) +
                       document.substring(position + length);
            default:
                return document;
        }
    }

    public Operation inverse(String document) {
        switch (type) {
            case INSERT:
                return Operation.delete(position, content.length(), userId, baseVersion);
            case DELETE:
                String deleted = document.substring(position, position + length);
                return Operation.insert(position, deleted, userId, baseVersion);
            default:
                return this;
        }
    }
}
```

### 2. Operational Transformation
```java
public class OperationalTransformer {

    /**
     * Transform op1 against op2, assuming op2 was applied first.
     * Returns transformed op1 that can be applied after op2.
     */
    public TransformResult transform(Operation op1, Operation op2) {
        if (op1.getType() == OperationType.INSERT && op2.getType() == OperationType.INSERT) {
            return transformInsertInsert(op1, op2);
        }
        if (op1.getType() == OperationType.INSERT && op2.getType() == OperationType.DELETE) {
            return transformInsertDelete(op1, op2);
        }
        if (op1.getType() == OperationType.DELETE && op2.getType() == OperationType.INSERT) {
            return transformDeleteInsert(op1, op2);
        }
        if (op1.getType() == OperationType.DELETE && op2.getType() == OperationType.DELETE) {
            return transformDeleteDelete(op1, op2);
        }
        return new TransformResult(op1, op2);
    }

    private TransformResult transformInsertInsert(Operation op1, Operation op2) {
        int pos1 = op1.getPosition();
        int pos2 = op2.getPosition();

        if (pos1 < pos2 || (pos1 == pos2 && op1.getUserId().compareTo(op2.getUserId()) < 0)) {
            // op1 position unchanged
            return new TransformResult(op1, op2.withPosition(pos2 + op1.getLength()));
        } else {
            // op1 shifts right
            return new TransformResult(op1.withPosition(pos1 + op2.getLength()), op2);
        }
    }

    private TransformResult transformInsertDelete(Operation insert, Operation delete) {
        int insertPos = insert.getPosition();
        int deletePos = delete.getPosition();
        int deleteLen = delete.getLength();

        if (insertPos <= deletePos) {
            // Insert before delete region
            return new TransformResult(insert, delete.withPosition(deletePos + insert.getLength()));
        } else if (insertPos >= deletePos + deleteLen) {
            // Insert after delete region
            return new TransformResult(insert.withPosition(insertPos - deleteLen), delete);
        } else {
            // Insert within delete region - insert at delete position
            return new TransformResult(insert.withPosition(deletePos),
                delete.withLength(deleteLen + insert.getLength()));
        }
    }

    private TransformResult transformDeleteDelete(Operation op1, Operation op2) {
        int pos1 = op1.getPosition(), len1 = op1.getLength();
        int pos2 = op2.getPosition(), len2 = op2.getLength();

        // No overlap
        if (pos1 + len1 <= pos2) {
            return new TransformResult(op1, op2.withPosition(pos2 - len1));
        }
        if (pos2 + len2 <= pos1) {
            return new TransformResult(op1.withPosition(pos1 - len2), op2);
        }

        // Overlapping deletes - handle carefully
        int start = Math.min(pos1, pos2);
        int end1 = pos1 + len1, end2 = pos2 + len2;

        if (pos1 <= pos2 && end1 >= end2) {
            // op1 contains op2
            return new TransformResult(op1.withLength(len1 - len2), Operation.noop());
        }
        // ... more cases

        return new TransformResult(op1, op2);
    }
}

public class TransformResult {
    private final Operation transformedOp1;
    private final Operation transformedOp2;
}
```

### 3. Document with Version Control
```java
public class Document {
    private final String documentId;
    private StringBuilder content;
    private long version;
    private final List<Operation> history;
    private final Map<String, Collaborator> collaborators;
    private final ReentrantReadWriteLock lock;

    public Document(String documentId) {
        this.documentId = documentId;
        this.content = new StringBuilder();
        this.version = 0;
        this.history = new ArrayList<>();
        this.collaborators = new ConcurrentHashMap<>();
        this.lock = new ReentrantReadWriteLock();
    }

    public synchronized OperationResult apply(Operation operation) {
        lock.writeLock().lock();
        try {
            // Transform if operation is based on old version
            Operation transformed = operation;
            if (operation.getBaseVersion() < version) {
                transformed = transformAgainstHistory(operation);
            }

            // Apply operation
            String newContent = transformed.apply(content.toString());
            content = new StringBuilder(newContent);
            version++;

            // Store in history
            history.add(transformed);

            return new OperationResult(transformed, version);
        } finally {
            lock.writeLock().unlock();
        }
    }

    private Operation transformAgainstHistory(Operation op) {
        Operation transformed = op;
        for (int i = (int) op.getBaseVersion(); i < history.size(); i++) {
            Operation concurrent = history.get(i);
            TransformResult result = transformer.transform(transformed, concurrent);
            transformed = result.getTransformedOp1();
        }
        return transformed;
    }

    public String getContentAtVersion(long targetVersion) {
        StringBuilder result = new StringBuilder();
        for (int i = 0; i < targetVersion && i < history.size(); i++) {
            result = new StringBuilder(history.get(i).apply(result.toString()));
        }
        return result.toString();
    }
}
```

### 4. Collaboration Server
```java
public class CollaborationServer {
    private final Map<String, Document> documents;
    private final Map<String, List<Session>> sessions;
    private final OperationalTransformer transformer;
    private final ExecutorService broadcaster;

    public void handleOperation(String docId, String sessionId, Operation operation) {
        Document doc = documents.get(docId);
        Session session = getSession(docId, sessionId);

        // Apply operation
        OperationResult result = doc.apply(operation);

        // Acknowledge to sender
        session.send(new AckMessage(operation.getOperationId(), result.getVersion()));

        // Broadcast to other collaborators
        broadcastToOthers(docId, sessionId, new OperationMessage(result.getOperation()));
    }

    public void handleCursorUpdate(String docId, String sessionId, Cursor cursor) {
        // Broadcast cursor position to all other users
        broadcastToOthers(docId, sessionId, new CursorMessage(sessionId, cursor));
    }

    private void broadcastToOthers(String docId, String excludeSession, Message message) {
        List<Session> docSessions = sessions.get(docId);
        if (docSessions == null) return;

        for (Session session : docSessions) {
            if (!session.getId().equals(excludeSession)) {
                broadcaster.submit(() -> session.send(message));
            }
        }
    }

    public void handleReconnect(String docId, String sessionId, long lastVersion) {
        Document doc = documents.get(docId);
        Session session = getSession(docId, sessionId);

        // Send missed operations
        List<Operation> missed = doc.getOperationsSince(lastVersion);
        session.send(new SyncMessage(missed, doc.getVersion()));
    }
}

public class Cursor {
    private final String sessionId;
    private final String userName;
    private final String color;
    private final int position;
    private final int selectionStart;
    private final int selectionEnd;
}
```

