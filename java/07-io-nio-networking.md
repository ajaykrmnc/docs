# Java I/O, NIO, and Networking - Deep Dive

## Table of Contents
1. [I/O Stream Fundamentals](#io-fundamentals)
2. [Classic I/O vs NIO](#classic-vs-nio)
3. [NIO Channels and Buffers](#nio-channels-buffers)
4. [NIO.2 File API](#nio2-file-api)
5. [Networking Fundamentals](#networking-fundamentals)
6. [Non-Blocking I/O with Selectors](#selectors)
7. [Async I/O (NIO.2)](#async-io)
8. [Interview Questions](#interview-questions)

---

## I/O Stream Fundamentals

### Stream Hierarchy

```
                        ┌─────────────────────────────────────────────────┐
                        │              BYTE STREAMS                       │
                        │         (Binary Data - 8-bit bytes)             │
                        └─────────────────────────────────────────────────┘
                                          │
              ┌───────────────────────────┴───────────────────────────┐
              │                                                       │
        InputStream                                            OutputStream
              │                                                       │
    ┌─────────┼─────────────┬─────────────┐             ┌────────────┼──────────────┐
    │         │             │             │             │            │              │
FileInput  ByteArray   Buffered     Object        FileOutput   ByteArray    Buffered
Stream     InputStream InputStream  InputStream    Stream      OutputStream OutputStream
    │                       │                           │                         │
    └───────────────────────┼───────────────────────────┼─────────────────────────┘
                            │                           │
                     DataInputStream             DataOutputStream
                     (primitives)                (primitives)


                        ┌─────────────────────────────────────────────────┐
                        │            CHARACTER STREAMS                    │
                        │        (Text Data - 16-bit Unicode)             │
                        └─────────────────────────────────────────────────┘
                                          │
              ┌───────────────────────────┴───────────────────────────┐
              │                                                       │
           Reader                                                  Writer
              │                                                       │
    ┌─────────┼─────────────┬─────────────┐             ┌────────────┼──────────────┐
    │         │             │             │             │            │              │
FileReader InputStreamReader BufferedReader       FileWriter  OutputStreamWriter BufferedWriter
              │              (+ readLine())                    │
              │                                                │
        StringReader                                    StringWriter
              │                                                │
        CharArrayReader                                 CharArrayWriter
```

### Decorator Pattern in I/O

```java
// Classic I/O uses Decorator pattern for flexibility
public class IODecoratorDemo {
    
    // Reading with multiple decorators
    public static void readFile(String path) throws IOException {
        // Layer 1: FileInputStream - reads raw bytes from file
        // Layer 2: BufferedInputStream - adds buffering for performance
        // Layer 3: DataInputStream - adds methods to read primitives
        
        try (DataInputStream dis = new DataInputStream(
                new BufferedInputStream(
                    new FileInputStream(path)))) {
            
            int intValue = dis.readInt();
            double doubleValue = dis.readDouble();
            String utfString = dis.readUTF();
        }
    }
    
    // Writing with decorators
    public static void writeFile(String path) throws IOException {
        try (DataOutputStream dos = new DataOutputStream(
                new BufferedOutputStream(
                    new FileOutputStream(path)))) {
            
            dos.writeInt(42);
            dos.writeDouble(3.14159);
            dos.writeUTF("Hello, World!");
        }
    }
    
    // Text file with character streams
    public static List<String> readTextFile(String path) throws IOException {
        List<String> lines = new ArrayList<>();
        
        try (BufferedReader reader = new BufferedReader(
                new InputStreamReader(
                    new FileInputStream(path), StandardCharsets.UTF_8))) {
            
            String line;
            while ((line = reader.readLine()) != null) {
                lines.add(line);
            }
        }
        return lines;
    }
}
```

---

## Classic I/O vs NIO

### Comparison Table

```
┌─────────────────────┬───────────────────────┬───────────────────────────┐
│ Feature             │ Classic I/O           │ NIO                       │
├─────────────────────┼───────────────────────┼───────────────────────────┤
│ Data Unit           │ Streams (bytes/chars) │ Buffers + Channels        │
│ I/O Mode            │ Blocking              │ Non-blocking + Blocking   │
│ Scalability         │ Thread per connection │ One thread, many channels │
│ Data Direction      │ One-directional       │ Bi-directional (channels) │
│ Memory              │ JVM heap only         │ Direct buffers (off-heap) │
│ File Operations     │ Basic                 │ Memory-mapped files       │
│ Complexity          │ Simple                │ More complex              │
│ Best For            │ Simple I/O, text      │ High-concurrency servers  │
└─────────────────────┴───────────────────────┴───────────────────────────┘
```

### When to Use What

```java
// Use Classic I/O when:
// - Simple file reading/writing
// - Text processing with BufferedReader
// - Object serialization
// - Low concurrency requirements

// Classic I/O example - simple and readable
public static String readFileClassic(String path) throws IOException {
    StringBuilder sb = new StringBuilder();
    try (BufferedReader reader = new BufferedReader(new FileReader(path))) {
        String line;
        while ((line = reader.readLine()) != null) {
            sb.append(line).append("\n");
        }
    }
    return sb.toString();
}

// Use NIO when:
// - High-performance file operations
// - Non-blocking network I/O
// - Memory-mapped file access
// - Scatter/Gather I/O
// - Multiplexed I/O (one thread, multiple connections)

// NIO example - more control
public static String readFileNIO(Path path) throws IOException {
    ByteBuffer buffer = ByteBuffer.allocate(1024);
    StringBuilder sb = new StringBuilder();
    
    try (FileChannel channel = FileChannel.open(path, StandardOpenOption.READ)) {
        while (channel.read(buffer) > 0) {
            buffer.flip();  // Switch to read mode
            sb.append(StandardCharsets.UTF_8.decode(buffer));
            buffer.clear(); // Switch to write mode
        }
    }
    return sb.toString();
}

// NIO.2 (Java 7+) - Best of both worlds
public static String readFileNIO2(Path path) throws IOException {
    return Files.readString(path);  // Simple AND efficient
}
```

---

## NIO Channels and Buffers

### Buffer Internals

```
Buffer State Variables:
┌───────────────────────────────────────────────────────────────────────────┐
│                                                                           │
│   0 <= mark <= position <= limit <= capacity                              │
│                                                                           │
│   ┌─────┬─────┬─────┬─────┬─────┬─────┬─────┬─────┬─────┬─────┐          │
│   │  H  │  e  │  l  │  l  │  o  │     │     │     │     │     │          │
│   └─────┴─────┴─────┴─────┴─────┴─────┴─────┴─────┴─────┴─────┘          │
│   0     1     2     3     4     5     6     7     8     9    10          │
│                           ▲                 ▲                 ▲           │
│                        position           limit           capacity        │
│                                                                           │
│   After writing "Hello":                                                  │
│   - position = 5 (next write position)                                    │
│   - limit = 10 (max writable)                                             │
│   - capacity = 10 (fixed size)                                            │
│                                                                           │
│   After flip() for reading:                                               │
│   - position = 0 (next read position)                                     │
│   - limit = 5 (was position, max readable)                                │
│   - capacity = 10 (unchanged)                                             │
│                                                                           │
└───────────────────────────────────────────────────────────────────────────┘
```

### Buffer Operations

```java
public class BufferOperations {

    public void demonstrateBuffer() {
        // Allocate buffer
        ByteBuffer buffer = ByteBuffer.allocate(1024);

        // Writing to buffer
        buffer.put("Hello".getBytes());
        System.out.println("After write - position: " + buffer.position()); // 5

        // Prepare for reading
        buffer.flip();
        System.out.println("After flip - position: " + buffer.position()); // 0
        System.out.println("After flip - limit: " + buffer.limit());       // 5

        // Reading from buffer
        byte[] data = new byte[buffer.remaining()];
        buffer.get(data);

        // Prepare for more writing
        buffer.clear();  // position = 0, limit = capacity
        // OR
        buffer.compact(); // Copies unread data to beginning

        // Direct buffer (off-heap, faster for I/O)
        ByteBuffer directBuffer = ByteBuffer.allocateDirect(1024);
    }
}
```

### Channel Operations

```java
public class ChannelOperations {

    // Copy file using channels (faster than streams for large files)
    public void copyFile(Path source, Path dest) throws IOException {
        try (FileChannel sourceChannel = FileChannel.open(source, StandardOpenOption.READ);
             FileChannel destChannel = FileChannel.open(dest,
                 StandardOpenOption.CREATE, StandardOpenOption.WRITE)) {

            // transferTo/transferFrom use OS-level optimizations
            sourceChannel.transferTo(0, sourceChannel.size(), destChannel);
        }
    }

    // Memory-mapped file (extremely fast for large files)
    public void memoryMappedFile(Path path) throws IOException {
        try (FileChannel channel = FileChannel.open(path,
                StandardOpenOption.READ, StandardOpenOption.WRITE)) {

            MappedByteBuffer buffer = channel.map(
                FileChannel.MapMode.READ_WRITE, 0, channel.size());

            // Direct memory access
            byte firstByte = buffer.get(0);
            buffer.put(0, (byte) 'X');  // Writes directly to file!
        }
    }
}
```

---

## NIO.2 File API (Java 7+)

### Path and Files

```java
public class NIO2Demo {

    public void pathOperations() {
        // Creating paths
        Path path = Path.of("/home/user/file.txt");
        Path path2 = Paths.get("/home", "user", "file.txt");

        // Path components
        System.out.println("Filename: " + path.getFileName());
        System.out.println("Parent: " + path.getParent());
        System.out.println("Root: " + path.getRoot());
        System.out.println("Absolute: " + path.toAbsolutePath());

        // Resolving paths
        Path base = Path.of("/home/user");
        Path resolved = base.resolve("documents/file.txt"); // /home/user/documents/file.txt
        Path sibling = path.resolveSibling("other.txt");    // /home/user/other.txt

        // Relativizing
        Path relative = Path.of("/home").relativize(Path.of("/home/user/file.txt")); // user/file.txt
    }

    public void fileOperations() throws IOException {
        Path path = Path.of("test.txt");

        // Read/write entire file
        String content = Files.readString(path);
        Files.writeString(path, "Hello, World!");

        // Read all lines
        List<String> lines = Files.readAllLines(path);

        // Stream lines (lazy, good for large files)
        try (Stream<String> stream = Files.lines(path)) {
            stream.filter(line -> line.contains("error"))
                  .forEach(System.out::println);
        }

        // File attributes
        BasicFileAttributes attrs = Files.readAttributes(path, BasicFileAttributes.class);
        System.out.println("Size: " + attrs.size());
        System.out.println("Created: " + attrs.creationTime());
        System.out.println("Modified: " + attrs.lastModifiedTime());

        // File operations
        Files.copy(path, Path.of("backup.txt"), StandardCopyOption.REPLACE_EXISTING);
        Files.move(path, Path.of("renamed.txt"), StandardCopyOption.ATOMIC_MOVE);
        Files.delete(path);
    }
}
```

### Walking Directory Trees

```java
public class DirectoryWalking {

    // Find all Java files
    public List<Path> findJavaFiles(Path root) throws IOException {
        try (Stream<Path> stream = Files.walk(root)) {
            return stream
                .filter(p -> p.toString().endsWith(".java"))
                .collect(Collectors.toList());
        }
    }

    // Using FileVisitor for more control
    public void walkWithVisitor(Path root) throws IOException {
        Files.walkFileTree(root, new SimpleFileVisitor<Path>() {
            @Override
            public FileVisitResult visitFile(Path file, BasicFileAttributes attrs) {
                System.out.println("File: " + file);
                return FileVisitResult.CONTINUE;
            }

            @Override
            public FileVisitResult preVisitDirectory(Path dir, BasicFileAttributes attrs) {
                System.out.println("Directory: " + dir);
                return FileVisitResult.CONTINUE;
            }

            @Override
            public FileVisitResult visitFileFailed(Path file, IOException exc) {
                System.err.println("Failed: " + file);
                return FileVisitResult.CONTINUE;
            }
        });
    }

    // Watch for file changes
    public void watchDirectory(Path dir) throws IOException, InterruptedException {
        WatchService watcher = FileSystems.getDefault().newWatchService();
        dir.register(watcher,
            StandardWatchEventKinds.ENTRY_CREATE,
            StandardWatchEventKinds.ENTRY_DELETE,
            StandardWatchEventKinds.ENTRY_MODIFY);

        while (true) {
            WatchKey key = watcher.take();  // Blocks until event

            for (WatchEvent<?> event : key.pollEvents()) {
                Path changed = (Path) event.context();
                System.out.println(event.kind() + ": " + changed);
            }

            if (!key.reset()) break;
        }
    }
}
```

---

## Networking

### Socket Programming

```java
// Simple TCP Server
public class TcpServer {
    public void start(int port) throws IOException {
        try (ServerSocket serverSocket = new ServerSocket(port)) {
            System.out.println("Server listening on port " + port);

            while (true) {
                Socket client = serverSocket.accept();
                // Handle in new thread
                new Thread(() -> handleClient(client)).start();
            }
        }
    }

    private void handleClient(Socket client) {
        try (BufferedReader in = new BufferedReader(
                new InputStreamReader(client.getInputStream()));
             PrintWriter out = new PrintWriter(
                client.getOutputStream(), true)) {

            String message;
            while ((message = in.readLine()) != null) {
                System.out.println("Received: " + message);
                out.println("Echo: " + message);
            }
        } catch (IOException e) {
            e.printStackTrace();
        }
    }
}

// Simple TCP Client
public class TcpClient {
    public void connect(String host, int port) throws IOException {
        try (Socket socket = new Socket(host, port);
             BufferedReader in = new BufferedReader(
                new InputStreamReader(socket.getInputStream()));
             PrintWriter out = new PrintWriter(
                socket.getOutputStream(), true);
             BufferedReader console = new BufferedReader(
                new InputStreamReader(System.in))) {

            String userInput;
            while ((userInput = console.readLine()) != null) {
                out.println(userInput);
                System.out.println("Server: " + in.readLine());
            }
        }
    }
}
```

### Non-Blocking I/O with Selectors

```java
public class NioServer {

    public void start(int port) throws IOException {
        Selector selector = Selector.open();
        ServerSocketChannel serverChannel = ServerSocketChannel.open();
        serverChannel.bind(new InetSocketAddress(port));
        serverChannel.configureBlocking(false);
        serverChannel.register(selector, SelectionKey.OP_ACCEPT);

        ByteBuffer buffer = ByteBuffer.allocate(1024);

        while (true) {
            selector.select();  // Blocks until events

            Iterator<SelectionKey> keys = selector.selectedKeys().iterator();
            while (keys.hasNext()) {
                SelectionKey key = keys.next();
                keys.remove();

                if (key.isAcceptable()) {
                    // New connection
                    SocketChannel client = serverChannel.accept();
                    client.configureBlocking(false);
                    client.register(selector, SelectionKey.OP_READ);

                } else if (key.isReadable()) {
                    // Data available to read
                    SocketChannel client = (SocketChannel) key.channel();
                    buffer.clear();
                    int bytesRead = client.read(buffer);

                    if (bytesRead == -1) {
                        client.close();
                    } else {
                        buffer.flip();
                        client.write(buffer);  // Echo back
                    }
                }
            }
        }
    }
}
```

### Async I/O (NIO.2)

```java
public class AsyncIODemo {

    public void asyncFileRead(Path path) throws IOException {
        AsynchronousFileChannel channel = AsynchronousFileChannel.open(path, StandardOpenOption.READ);
        ByteBuffer buffer = ByteBuffer.allocate(1024);

        // Callback-based
        channel.read(buffer, 0, buffer, new CompletionHandler<Integer, ByteBuffer>() {
            @Override
            public void completed(Integer bytesRead, ByteBuffer attachment) {
                attachment.flip();
                byte[] data = new byte[attachment.remaining()];
                attachment.get(data);
                System.out.println("Read: " + new String(data));
            }

            @Override
            public void failed(Throwable exc, ByteBuffer attachment) {
                exc.printStackTrace();
            }
        });
    }

    public void asyncSocketClient(String host, int port) throws Exception {
        AsynchronousSocketChannel channel = AsynchronousSocketChannel.open();

        // Connect asynchronously
        Future<Void> future = channel.connect(new InetSocketAddress(host, port));
        future.get();  // Wait for connection

        // Write asynchronously
        ByteBuffer buffer = ByteBuffer.wrap("Hello".getBytes());
        Future<Integer> writeFuture = channel.write(buffer);
        writeFuture.get();

        // Read asynchronously
        buffer.clear();
        Future<Integer> readFuture = channel.read(buffer);
        readFuture.get();

        channel.close();
    }
}
```

---

## Interview Questions

### Q1: Difference between InputStream and Reader?

| InputStream | Reader |
|-------------|--------|
| Byte-oriented (8-bit) | Character-oriented (16-bit Unicode) |
| For binary data | For text data |
| read() returns int (0-255) | read() returns int (0-65535) |
| FileInputStream | FileReader |

### Q2: What is the Decorator Pattern in Java I/O?

```java
// Base stream
InputStream is = new FileInputStream("file.txt");

// Decorated with buffering
is = new BufferedInputStream(is);

// Decorated with data type reading
DataInputStream dis = new DataInputStream(is);

// Each decorator adds functionality without changing the interface
int value = dis.readInt();
```

### Q3: When to use NIO vs Classic I/O?

- **Classic I/O**: Simple file operations, text processing
- **NIO Channels/Buffers**: Large file transfers, need for memory-mapped files
- **NIO Selectors**: Multiple connections (servers), non-blocking required
- **NIO.2 Async**: High-concurrency servers, callback-based processing
