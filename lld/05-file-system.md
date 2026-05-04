# Design an In-Memory File System
**Difficulty:** Hard | **Companies:** Google, Dropbox, Apple, Microsoft

---

## Problem Statement

Design an in-memory file system that supports Unix-like operations including files, directories, symbolic 
links, permissions, and file watching.

---

## Requirements

### Functional Requirements
1. Support files, directories, and symbolic links
2. Unix-like operations: ls, cd, mkdir, rm, mv, cp, chmod, touch
3. Permission system (read/write/execute) for user/group/other
4. Hard links with reference counting
5. File content read/write operations
6. Watch for file changes (inotify-like functionality)

### Non-Functional Requirements
1. Thread-safe operations
2. Efficient path resolution
3. Memory-efficient storage

---

## Class Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                       FileSystem                                │
├─────────────────────────────────────────────────────────────────┤
│ - root: Directory                                               │
│ - inodeTable: Map<Long, INode>                                  │
│ - currentDir: Directory                                         │
│ - watchers: Map<String, List<FileWatcher>>                      │
├─────────────────────────────────────────────────────────────────┤
│ + mkdir(path: String): void                                     │
│ + touch(path: String): void                                     │
│ + ls(path: String): List<String>                                │
│ + cd(path: String): void                                        │
│ + rm(path: String, recursive: boolean): void                    │
│ + mv(src: String, dest: String): void                           │
│ + cp(src: String, dest: String): void                           │
│ + chmod(path: String, permissions: int): void                   │
│ + read(path: String): byte[]                                    │
│ + write(path: String, content: byte[]): void                    │
│ + link(target: String, linkPath: String): void                  │
│ + symlink(target: String, linkPath: String): void               │
│ + watch(path: String, watcher: FileWatcher): void               │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                    <<abstract>> INode                           │
├─────────────────────────────────────────────────────────────────┤
│ - inodeNumber: long                                             │
│ - permissions: Permission                                       │
│ - owner: String                                                 │
│ - group: String                                                 │
│ - createdAt: Instant                                            │
│ - modifiedAt: Instant                                           │
│ - accessedAt: Instant                                           │
│ - linkCount: AtomicInteger                                      │
├─────────────────────────────────────────────────────────────────┤
│ + getType(): FileType                                           │
│ + hasPermission(user: String, perm: PermType): boolean          │
└─────────────────────────────────────────────────────────────────┘
              △
              │
    ┌─────────┼─────────┐
    │         │         │
┌───┴───┐ ┌───┴───┐ ┌───┴────┐
│ File  │ │  Dir  │ │SymLink │
└───────┘ └───────┘ └────────┘
```

---

## Class Implementations

### 1. Permission System
```java
public class Permission {
    private int mode;  // Unix-style: e.g., 0755
    
    public static final int READ = 4;
    public static final int WRITE = 2;
    public static final int EXECUTE = 1;
    
    public Permission(int mode) {
        this.mode = mode;
    }
    
    public boolean canRead(PermissionContext ctx) {
        return hasPermission(ctx, READ);
    }
    
    public boolean canWrite(PermissionContext ctx) {
        return hasPermission(ctx, WRITE);
    }
    
    public boolean canExecute(PermissionContext ctx) {
        return hasPermission(ctx, EXECUTE);
    }
    
    private boolean hasPermission(PermissionContext ctx, int perm) {
        int shift;
        if (ctx.isOwner()) shift = 6;       // Owner bits
        else if (ctx.isGroup()) shift = 3;  // Group bits
        else shift = 0;                      // Other bits
        
        return ((mode >> shift) & perm) == perm;
    }
    
    public void setMode(int mode) {
        this.mode = mode;
    }
    
    public String toString() {
        return toSymbolicString();
    }
    
    private String toSymbolicString() {
        StringBuilder sb = new StringBuilder();
        for (int i = 2; i >= 0; i--) {
            int bits = (mode >> (i * 3)) & 7;
            sb.append((bits & READ) != 0 ? "r" : "-");
            sb.append((bits & WRITE) != 0 ? "w" : "-");
            sb.append((bits & EXECUTE) != 0 ? "x" : "-");
        }
        return sb.toString();
    }
}
```

### 2. INode and File Classes
```java
public abstract class INode {
    private static final AtomicLong INODE_COUNTER = new AtomicLong(1);
    
    protected final long inodeNumber;
    protected Permission permissions;
    protected String owner;
    protected String group;
    protected Instant createdAt;
    protected Instant modifiedAt;
    protected Instant accessedAt;
    protected final AtomicInteger linkCount;
    
    protected INode(String owner, int mode) {
        this.inodeNumber = INODE_COUNTER.getAndIncrement();
        this.owner = owner;
        this.group = owner;
        this.permissions = new Permission(mode);
        this.createdAt = Instant.now();
        this.modifiedAt = this.createdAt;
        this.accessedAt = this.createdAt;
        this.linkCount = new AtomicInteger(1);
    }
    
    public abstract FileType getType();
    
    public void incrementLinkCount() { linkCount.incrementAndGet(); }
    public int decrementLinkCount() { return linkCount.decrementAndGet(); }
}

public class File extends INode {
    private byte[] content;
    private final ReentrantReadWriteLock lock;
    
    public File(String owner) {
        super(owner, 0644);
        this.content = new byte[0];
        this.lock = new ReentrantReadWriteLock();
    }
    
    public byte[] read() {
        lock.readLock().lock();
        try {
            accessedAt = Instant.now();
            return Arrays.copyOf(content, content.length);
        } finally {
            lock.readLock().unlock();
        }
    }
    
    public void write(byte[] data) {
        lock.writeLock().lock();
        try {
            this.content = Arrays.copyOf(data, data.length);
            this.modifiedAt = Instant.now();
        } finally {
            lock.writeLock().unlock();
        }
    }
    
    public void append(byte[] data) {
        lock.writeLock().lock();
        try {
            byte[] newContent = new byte[content.length + data.length];
            System.arraycopy(content, 0, newContent, 0, content.length);
            System.arraycopy(data, 0, newContent, content.length, data.length);
            this.content = newContent;
            this.modifiedAt = Instant.now();
        } finally {
            lock.writeLock().unlock();
        }
    }
    
    @Override
    public FileType getType() { return FileType.REGULAR_FILE; }
    
    public long getSize() { return content.length; }
}
```

### 3. Directory
```java
public class Directory extends INode {
    private final Map<String, INode> children;
    private Directory parent;
    
    public Directory(String owner, Directory parent) {
        super(owner, 0755);
        this.children = new ConcurrentHashMap<>();
        this.parent = parent;
    }
    
    public void addChild(String name, INode node) {
        if (name.contains("/")) {
            throw new IllegalArgumentException("Name cannot contain /");
        }
        children.put(name, node);
        modifiedAt = Instant.now();
    }
    
    public INode getChild(String name) {
        if (name.equals(".")) return this;
        if (name.equals("..")) return parent != null ? parent : this;
        return children.get(name);
    }
    
    public INode removeChild(String name) {
        INode removed = children.remove(name);
        if (removed != null) modifiedAt = Instant.now();
        return removed;
    }
    
    public List<String> list() {
        return new ArrayList<>(children.keySet());
    }
    
    @Override
    public FileType getType() { return FileType.DIRECTORY; }
}
```

