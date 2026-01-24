# Blocking vs Non-Blocking I/O - Deep Dive

## Table of Contents
1. [I/O Models Overview](#io-models)
2. [Blocking I/O (BIO)](#blocking-io)
3. [Non-Blocking I/O (NIO)](#nonblocking-io)
4. [Asynchronous I/O (AIO)](#async-io)
5. [Multiplexing with Selectors](#selectors)
6. [Reactor Pattern](#reactor-pattern)
7. [Proactor Pattern](#proactor-pattern)
8. [Performance Comparison](#performance)
9. [Interview Questions](#interview-questions)

---

## I/O Models Overview

### The Five I/O Models (Unix/Linux)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         I/O OPERATION PHASES                                │
├─────────────────────────────────────────────────────────────────────────────┤
│  Phase 1: Wait for data to be ready (network → kernel buffer)               │
│  Phase 2: Copy data from kernel to user space (kernel → application)        │
└─────────────────────────────────────────────────────────────────────────────┘

Model Comparison:
┌──────────────────────┬─────────────────┬─────────────────┬─────────────────┐
│ Model                │ Phase 1         │ Phase 2         │ Thread Behavior │
├──────────────────────┼─────────────────┼─────────────────┼─────────────────┤
│ Blocking I/O         │ BLOCKS          │ BLOCKS          │ Waits entirely  │
│ Non-blocking I/O     │ Returns EAGAIN  │ BLOCKS          │ Polls repeatedly│
│ I/O Multiplexing     │ BLOCKS on select│ BLOCKS          │ Monitors many   │
│ Signal-driven I/O    │ Returns (signal)│ BLOCKS          │ Notified async  │
│ Asynchronous I/O     │ Returns         │ Returns         │ Fully async     │
└──────────────────────┴─────────────────┴─────────────────┴─────────────────┘
```

### Java I/O Evolution

```
Java I/O History:
┌─────────────────────────────────────────────────────────────────────────────┐
│ Java 1.0  │ java.io          │ Blocking, stream-oriented                   │
│ Java 1.4  │ java.nio         │ Non-blocking, buffer-oriented, selectors    │
│ Java 7    │ java.nio.file    │ NIO.2, async file I/O, Path API             │
│ Java 7    │ AsynchronousChannel │ True async I/O with callbacks/Future     │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Blocking I/O (BIO)

### How Blocking I/O Works

```
Blocking I/O Thread Model:
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│  Client 1   │     │  Client 2   │     │  Client 3   │
└──────┬──────┘     └──────┬──────┘     └──────┬──────┘
       │                   │                   │
       ▼                   ▼                   ▼
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│  Thread 1   │     │  Thread 2   │     │  Thread 3   │
│  (BLOCKED)  │     │  (BLOCKED)  │     │  (BLOCKED)  │
└──────┬──────┘     └──────┬──────┘     └──────┬──────┘
       │                   │                   │
       └───────────────────┼───────────────────┘
                           ▼
                    ┌─────────────┐
                    │   Kernel    │
                    │   Buffer    │
                    └─────────────┘

Problem: One thread per connection = 10,000 connections = 10,000 threads!
```

### Blocking I/O Example

```java
public class BlockingIOServer {
    
    public static void main(String[] args) throws IOException {
        ServerSocket serverSocket = new ServerSocket(8080);
        System.out.println("Server started on port 8080");
        
        while (true) {
            // BLOCKS until client connects
            Socket clientSocket = serverSocket.accept();
            
            // One thread per client (traditional approach)
            new Thread(() -> handleClient(clientSocket)).start();
        }
    }
    
    private static void handleClient(Socket socket) {
        try (BufferedReader reader = new BufferedReader(
                new InputStreamReader(socket.getInputStream()));
             PrintWriter writer = new PrintWriter(
                socket.getOutputStream(), true)) {
            
            String line;
            // BLOCKS until data available or connection closed
            while ((line = reader.readLine()) != null) {
                writer.println("Echo: " + line);
            }
        } catch (IOException e) {
            e.printStackTrace();
        }
    }
}
```

### Thread Pool Improvement

```java
public class ThreadPoolBlockingServer {
    private static final ExecutorService pool = 
        Executors.newFixedThreadPool(200);  // Limited threads
    
    public static void main(String[] args) throws IOException {
        ServerSocket serverSocket = new ServerSocket(8080);
        
        while (true) {
            Socket clientSocket = serverSocket.accept();
            pool.submit(() -> handleClient(clientSocket));
        }
    }
    
    // Still blocking, but with bounded threads
    // Problem: 200 threads = max 200 concurrent connections
}
```

### Blocking I/O Internals

```
System Call Flow (read):
┌─────────────────────────────────────────────────────────────────────────────┐
│ 1. Application calls read()                                                 │
│ 2. Thread transitions to KERNEL MODE                                        │
│ 3. Kernel checks if data available in socket buffer                         │
│    - If NO data: Thread put in WAIT QUEUE, context switch                   │
│    - If data available: Copy to user buffer                                 │
│ 4. When data arrives (interrupt), thread moved to READY QUEUE               │
│ 5. Scheduler eventually runs thread, returns to USER MODE                   │
│ 6. read() returns with data                                                 │
└─────────────────────────────────────────────────────────────────────────────┘

Thread States During Blocking I/O:
RUNNABLE → read() → BLOCKED (waiting for I/O) → RUNNABLE (data ready)
```

---

## Non-Blocking I/O (NIO)

### How Non-Blocking I/O Works

```
Non-Blocking I/O Model:
┌─────────────────────────────────────────────────────────────────────────────┐
│                                                                             │
│  Application          Kernel                                                │
│  ┌─────────┐         ┌─────────────────────────────────────┐               │
│  │         │ read()  │                                     │               │
│  │         │────────►│  No data? Return EAGAIN immediately │               │
│  │         │◄────────│                                     │               │
│  │         │         │                                     │               │
│  │  Poll   │ read()  │                                     │               │
│  │  Loop   │────────►│  No data? Return EAGAIN immediately │               │
│  │         │◄────────│                                     │               │
│  │         │         │                                     │               │
│  │         │ read()  │  Data ready!                        │               │
│  │         │────────►│  ┌─────────────────────────────┐   │               │
│  │         │         │  │ Copy data to user buffer    │   │               │
│  │         │◄────────│  └─────────────────────────────┘   │               │
│  └─────────┘         └─────────────────────────────────────┘               │
│                                                                             │
│  Problem: Busy-waiting wastes CPU cycles!                                   │
│  Solution: Use I/O Multiplexing (select/poll/epoll)                         │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Java NIO Core Components

```
NIO Architecture:
┌─────────────────────────────────────────────────────────────────────────────┐
│                                                                             │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐                     │
│  │   Buffers   │    │  Channels   │    │  Selectors  │                     │
│  │             │    │             │    │             │                     │
│  │ ByteBuffer  │◄──►│SocketChannel│───►│  Selector   │                     │
│  │ CharBuffer  │    │FileChannel  │    │             │                     │
│  │ IntBuffer   │    │DatagramChan │    │ SelectionKey│                     │
│  └─────────────┘    └─────────────┘    └─────────────┘                     │
│                                                                             │
│  Buffer: Container for data (read from/write to channels)                   │
│  Channel: Bidirectional connection (like streams but non-blocking)          │
│  Selector: Monitors multiple channels for events                            │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Buffer Internals

```java
public class BufferInternals {

    public static void main(String[] args) {
        // Buffer has 4 key properties:
        // capacity: Maximum elements it can hold (fixed)
        // limit: First element that should not be read/written
        // position: Next element to be read/written
        // mark: Remembered position (optional)

        // Invariant: 0 <= mark <= position <= limit <= capacity

        ByteBuffer buffer = ByteBuffer.allocate(10);
        // State: position=0, limit=10, capacity=10

        buffer.put((byte) 'H');
        buffer.put((byte) 'i');
        // State: position=2, limit=10, capacity=10

        buffer.flip();  // Prepare for reading
        // State: position=0, limit=2, capacity=10

        byte b = buffer.get();  // Returns 'H'
        // State: position=1, limit=2, capacity=10

        buffer.clear();  // Prepare for writing (doesn't erase data)
        // State: position=0, limit=10, capacity=10

        buffer.compact();  // Keep unread data, prepare for writing
        // Moves unread data to beginning
    }
}
```

```
Buffer State Transitions:
┌─────────────────────────────────────────────────────────────────────────────┐
│                                                                             │
│  WRITE MODE                          READ MODE                              │
│  ┌─────────────────────────┐        ┌─────────────────────────┐            │
│  │ H │ i │   │   │   │     │        │ H │ i │   │   │   │     │            │
│  └─────────────────────────┘        └─────────────────────────┘            │
│    ▲       ▲               ▲          ▲       ▲               ▲            │
│    │       │               │          │       │               │            │
│    0      pos=2          limit=       pos=0  limit=2        cap=10         │
│                          cap=10                                             │
│                                                                             │
│                    flip()                                                   │
│           ─────────────────────►                                            │
│                                                                             │
│                    clear() or compact()                                     │
│           ◄─────────────────────                                            │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Direct vs Heap Buffers

```java
public class DirectVsHeapBuffer {

    public static void compare() {
        // Heap Buffer: Allocated in JVM heap
        ByteBuffer heapBuffer = ByteBuffer.allocate(1024);
        // - Subject to GC
        // - May require extra copy for I/O (JVM heap → native memory)
        // - Faster allocation

        // Direct Buffer: Allocated in native memory
        ByteBuffer directBuffer = ByteBuffer.allocateDirect(1024);
        // - Not subject to GC (but wrapper object is)
        // - Zero-copy I/O possible
        // - Slower allocation
        // - Use for long-lived, I/O-heavy buffers
    }
}
```

```
Memory Layout:
┌─────────────────────────────────────────────────────────────────────────────┐
│                                                                             │
│  HEAP BUFFER I/O:                                                           │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐                  │
│  │  JVM Heap    │───►│ Native Temp  │───►│   Kernel     │                  │
│  │  Buffer      │    │   Buffer     │    │   Buffer     │                  │
│  └──────────────┘    └──────────────┘    └──────────────┘                  │
│        (extra copy required)                                                │
│                                                                             │
│  DIRECT BUFFER I/O:                                                         │
│  ┌──────────────┐                        ┌──────────────┐                  │
│  │   Native     │───────────────────────►│   Kernel     │                  │
│  │   Buffer     │                        │   Buffer     │                  │
│  └──────────────┘                        └──────────────┘                  │
│        (zero-copy possible)                                                 │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Channel Operations

```java
public class ChannelExample {

    public static void nonBlockingChannel() throws IOException {
        // Create non-blocking socket channel
        SocketChannel channel = SocketChannel.open();
        channel.configureBlocking(false);  // KEY: Non-blocking mode

        channel.connect(new InetSocketAddress("localhost", 8080));

        // Non-blocking connect - may not complete immediately
        while (!channel.finishConnect()) {
            // Do other work while connecting
            System.out.println("Still connecting...");
        }

        ByteBuffer buffer = ByteBuffer.allocate(1024);

        // Non-blocking read - returns immediately
        int bytesRead = channel.read(buffer);
        // bytesRead = -1: End of stream
        // bytesRead = 0: No data available (non-blocking)
        // bytesRead > 0: Data read

        if (bytesRead == 0) {
            // No data available, do something else
        }
    }
}
```

---

## Multiplexing with Selectors

### Selector Architecture

```
Selector Model (I/O Multiplexing):
┌─────────────────────────────────────────────────────────────────────────────┐
│                                                                             │
│  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐          │
│  │Channel 1│  │Channel 2│  │Channel 3│  │Channel 4│  │Channel N│          │
│  └────┬────┘  └────┬────┘  └────┬────┘  └────┬────┘  └────┬────┘          │
│       │            │            │            │            │                 │
│       │  register  │  register  │  register  │  register  │                 │
│       └────────────┴────────────┼────────────┴────────────┘                 │
│                                 ▼                                           │
│                    ┌────────────────────────┐                               │
│                    │       SELECTOR         │                               │
│                    │                        │                               │
│                    │  select() - BLOCKS     │                               │
│                    │  until events ready    │                               │
│                    │                        │                               │
│                    │  Returns: Set of       │                               │
│                    │  ready SelectionKeys   │                               │
│                    └────────────────────────┘                               │
│                                 │                                           │
│                                 ▼                                           │
│                    ┌────────────────────────┐                               │
│                    │    SINGLE THREAD       │                               │
│                    │  processes all ready   │                               │
│                    │       channels         │                               │
│                    └────────────────────────┘                               │
│                                                                             │
│  Advantage: One thread handles thousands of connections!                    │
└─────────────────────────────────────────────────────────────────────────────┘
```

### SelectionKey Operations

```java
public class SelectionKeyOperations {

    // Interest operations (what we want to monitor)
    public static final int OP_READ = SelectionKey.OP_READ;      // 1
    public static final int OP_WRITE = SelectionKey.OP_WRITE;    // 4
    public static final int OP_CONNECT = SelectionKey.OP_CONNECT; // 8
    public static final int OP_ACCEPT = SelectionKey.OP_ACCEPT;  // 16

    public void registerChannel(Selector selector,
                                 SocketChannel channel) throws IOException {
        channel.configureBlocking(false);

        // Register channel with selector for READ events
        SelectionKey key = channel.register(selector, OP_READ);

        // Attach custom object to key
        key.attach(new ConnectionContext());

        // Change interest ops later
        key.interestOps(OP_READ | OP_WRITE);

        // Check ready operations
        if (key.isReadable()) { /* handle read */ }
        if (key.isWritable()) { /* handle write */ }
        if (key.isConnectable()) { /* finish connect */ }
        if (key.isAcceptable()) { /* accept connection */ }
    }
}
```

### Complete NIO Server Example

```java
public class NIOServer {
    private Selector selector;
    private ServerSocketChannel serverChannel;
    private ByteBuffer buffer = ByteBuffer.allocate(1024);

    public void start(int port) throws IOException {
        // Open selector
        selector = Selector.open();

        // Open server channel
        serverChannel = ServerSocketChannel.open();
        serverChannel.bind(new InetSocketAddress(port));
        serverChannel.configureBlocking(false);

        // Register for ACCEPT events
        serverChannel.register(selector, SelectionKey.OP_ACCEPT);

        System.out.println("NIO Server started on port " + port);

        // Event loop
        while (true) {
            // Block until at least one channel is ready
            int readyChannels = selector.select();

            if (readyChannels == 0) continue;

            // Get ready keys
            Set<SelectionKey> selectedKeys = selector.selectedKeys();
            Iterator<SelectionKey> keyIterator = selectedKeys.iterator();

            while (keyIterator.hasNext()) {
                SelectionKey key = keyIterator.next();

                if (key.isAcceptable()) {
                    handleAccept(key);
                } else if (key.isReadable()) {
                    handleRead(key);
                } else if (key.isWritable()) {
                    handleWrite(key);
                }

                // IMPORTANT: Remove processed key
                keyIterator.remove();
            }
        }
    }

    private void handleAccept(SelectionKey key) throws IOException {
        ServerSocketChannel server = (ServerSocketChannel) key.channel();
        SocketChannel client = server.accept();
        client.configureBlocking(false);

        // Register new client for READ events
        client.register(selector, SelectionKey.OP_READ);
        System.out.println("Client connected: " + client.getRemoteAddress());
    }

    private void handleRead(SelectionKey key) throws IOException {
        SocketChannel client = (SocketChannel) key.channel();
        buffer.clear();

        int bytesRead = client.read(buffer);

        if (bytesRead == -1) {
            // Client disconnected
            client.close();
            key.cancel();
            return;
        }

        buffer.flip();
        byte[] data = new byte[buffer.remaining()];
        buffer.get(data);
        String message = new String(data);
        System.out.println("Received: " + message);

        // Echo back - register for WRITE
        key.attach(message);
        key.interestOps(SelectionKey.OP_WRITE);
    }

    private void handleWrite(SelectionKey key) throws IOException {
        SocketChannel client = (SocketChannel) key.channel();
        String message = (String) key.attachment();

        buffer.clear();
        buffer.put(("Echo: " + message).getBytes());
        buffer.flip();

        client.write(buffer);

        // Switch back to READ mode
        key.interestOps(SelectionKey.OP_READ);
    }
}
```

### OS-Level Multiplexing

```
Linux I/O Multiplexing Evolution:
┌─────────────────────────────────────────────────────────────────────────────┐
│                                                                             │
│  select() - Original (1983)                                                 │
│  ├── Limited to 1024 file descriptors (FD_SETSIZE)                         │
│  ├── O(n) scanning of all FDs                                              │
│  └── Copies FD sets between user/kernel space each call                    │
│                                                                             │
│  poll() - Improvement                                                       │
│  ├── No FD limit                                                           │
│  ├── Still O(n) scanning                                                   │
│  └── Still copies data each call                                           │
│                                                                             │
│  epoll() - Linux 2.6+ (Best)                                               │
│  ├── O(1) for ready events                                                 │
│  ├── No FD limit                                                           │
│  ├── Edge-triggered and level-triggered modes                              │
│  └── Kernel maintains interest list (no copy each call)                    │
│                                                                             │
│  kqueue - BSD/macOS equivalent of epoll                                    │
│  IOCP - Windows I/O Completion Ports                                       │
│                                                                             │
│  Java NIO uses the best available:                                          │
│  - Linux: epoll                                                             │
│  - macOS: kqueue                                                            │
│  - Windows: select (or IOCP for AIO)                                        │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Asynchronous I/O (AIO)

### True Asynchronous I/O

```
Async I/O Model:
┌─────────────────────────────────────────────────────────────────────────────┐
│                                                                             │
│  Application                    Kernel                                      │
│  ┌─────────┐                   ┌─────────────────────────────────────┐     │
│  │         │ aio_read()        │                                     │     │
│  │         │──────────────────►│  Returns immediately                │     │
│  │         │◄──────────────────│  (operation in progress)            │     │
│  │         │                   │                                     │     │
│  │  Do     │                   │  ┌─────────────────────────────┐   │     │
│  │  other  │                   │  │ Kernel handles I/O          │   │     │
│  │  work   │                   │  │ in background               │   │     │
│  │         │                   │  └─────────────────────────────┘   │     │
│  │         │                   │                                     │     │
│  │         │  Callback/Signal  │  Data ready + copied to user buffer│     │
│  │         │◄──────────────────│                                     │     │
│  └─────────┘                   └─────────────────────────────────────┘     │
│                                                                             │
│  Key difference from NIO:                                                   │
│  - NIO: Kernel notifies when data READY, app still does the copy           │
│  - AIO: Kernel does EVERYTHING, notifies when COMPLETE                     │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Java AIO (NIO.2) Example

```java
public class AsyncIOExample {

    // Method 1: Using Future
    public void readWithFuture() throws Exception {
        AsynchronousFileChannel channel = AsynchronousFileChannel.open(
            Paths.get("data.txt"), StandardOpenOption.READ);

        ByteBuffer buffer = ByteBuffer.allocate(1024);

        // Returns immediately with Future
        Future<Integer> future = channel.read(buffer, 0);

        // Do other work while I/O in progress
        doOtherWork();

        // Block until complete (or check isDone())
        Integer bytesRead = future.get();

        buffer.flip();
        System.out.println("Read " + bytesRead + " bytes");
    }

    // Method 2: Using CompletionHandler (callback)
    public void readWithCallback() throws Exception {
        AsynchronousFileChannel channel = AsynchronousFileChannel.open(
            Paths.get("data.txt"), StandardOpenOption.READ);

        ByteBuffer buffer = ByteBuffer.allocate(1024);

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
                System.err.println("Read failed: " + exc.getMessage());
            }
        });

        // Method returns immediately, callback invoked when complete
        System.out.println("Read initiated, doing other work...");
    }
}
```

### Async Socket Server

```java
public class AsyncSocketServer {

    public void start(int port) throws Exception {
        AsynchronousServerSocketChannel server =
            AsynchronousServerSocketChannel.open();
        server.bind(new InetSocketAddress(port));

        System.out.println("Async server started on port " + port);

        // Accept connections asynchronously
        server.accept(null, new CompletionHandler<AsynchronousSocketChannel, Void>() {
            @Override
            public void completed(AsynchronousSocketChannel client, Void attachment) {
                // Accept next connection
                server.accept(null, this);

                // Handle this client
                handleClient(client);
            }

            @Override
            public void failed(Throwable exc, Void attachment) {
                System.err.println("Accept failed: " + exc.getMessage());
            }
        });

        // Keep main thread alive
        Thread.currentThread().join();
    }

    private void handleClient(AsynchronousSocketChannel client) {
        ByteBuffer buffer = ByteBuffer.allocate(1024);

        client.read(buffer, buffer, new CompletionHandler<Integer, ByteBuffer>() {
            @Override
            public void completed(Integer bytesRead, ByteBuffer buf) {
                if (bytesRead == -1) {
                    try { client.close(); } catch (IOException e) {}
                    return;
                }

                buf.flip();
                // Echo back
                client.write(buf, buf, new CompletionHandler<Integer, ByteBuffer>() {
                    @Override
                    public void completed(Integer bytesWritten, ByteBuffer buf) {
                        buf.clear();
                        // Read next message
                        client.read(buf, buf,
                            AsyncSocketServer.this.createReadHandler(client));
                    }

                    @Override
                    public void failed(Throwable exc, ByteBuffer buf) {
                        try { client.close(); } catch (IOException e) {}
                    }
                });
            }

            @Override
            public void failed(Throwable exc, ByteBuffer buf) {
                try { client.close(); } catch (IOException e) {}
            }
        });
    }

    private CompletionHandler<Integer, ByteBuffer> createReadHandler(
            AsynchronousSocketChannel client) {
        // Return handler for recursive reads
        return new CompletionHandler<>() {
            @Override
            public void completed(Integer result, ByteBuffer buf) {
                // Handle read...
            }
            @Override
            public void failed(Throwable exc, ByteBuffer buf) {}
        };
    }
}
```

---

## Reactor Pattern

### Single-Threaded Reactor

```
Single-Threaded Reactor:
┌─────────────────────────────────────────────────────────────────────────────┐
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                           REACTOR                                    │   │
│  │  ┌─────────────┐    ┌─────────────┐    ┌─────────────────────────┐  │   │
│  │  │  Selector   │───►│ Dispatcher  │───►│      Event Handlers     │  │   │
│  │  │  (demux)    │    │             │    │  ┌─────┐ ┌─────┐ ┌─────┐│  │   │
│  │  └─────────────┘    └─────────────┘    │  │Read │ │Write│ │Accept│  │   │
│  │        ▲                               │  └─────┘ └─────┘ └─────┘│  │   │
│  │        │                               └─────────────────────────┘  │   │
│  └────────┼────────────────────────────────────────────────────────────┘   │
│           │                                                                 │
│  ┌────────┴────────┐                                                       │
│  │ Channel 1       │                                                       │
│  │ Channel 2       │  All on single thread                                 │
│  │ Channel N       │                                                       │
│  └─────────────────┘                                                       │
│                                                                             │
│  Pros: Simple, no synchronization needed                                    │
│  Cons: One slow handler blocks everything                                   │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Multi-Threaded Reactor

```
Multi-Threaded Reactor (Netty-style):
┌─────────────────────────────────────────────────────────────────────────────┐
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                        BOSS GROUP (Acceptor)                         │   │
│  │  ┌─────────────┐                                                     │   │
│  │  │  Selector   │  Single thread accepts connections                  │   │
│  │  │  (ACCEPT)   │                                                     │   │
│  │  └──────┬──────┘                                                     │   │
│  └─────────┼───────────────────────────────────────────────────────────┘   │
│            │ dispatch new connections                                       │
│            ▼                                                                │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                       WORKER GROUP (I/O)                             │   │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐                  │   │
│  │  │  Selector 1 │  │  Selector 2 │  │  Selector N │                  │   │
│  │  │  (READ/     │  │  (READ/     │  │  (READ/     │                  │   │
│  │  │   WRITE)    │  │   WRITE)    │  │   WRITE)    │                  │   │
│  │  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘                  │   │
│  │         │                │                │                          │   │
│  │    Channels 1-K    Channels K+1-2K   Channels 2K+1-3K               │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  Each worker thread handles subset of connections                           │
│  Typically: workers = CPU cores                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Reactor Implementation

```java
public class MultiReactor {

    private final Selector bossSelector;
    private final Selector[] workerSelectors;
    private final int workerCount;
    private int nextWorker = 0;

    public MultiReactor(int workers) throws IOException {
        this.workerCount = workers;
        this.bossSelector = Selector.open();
        this.workerSelectors = new Selector[workers];

        for (int i = 0; i < workers; i++) {
            workerSelectors[i] = Selector.open();
        }
    }

    public void start(int port) throws IOException {
        // Start worker threads
        for (int i = 0; i < workerCount; i++) {
            final int workerId = i;
            new Thread(() -> runWorker(workerId), "worker-" + i).start();
        }

        // Setup server channel
        ServerSocketChannel serverChannel = ServerSocketChannel.open();
        serverChannel.bind(new InetSocketAddress(port));
        serverChannel.configureBlocking(false);
        serverChannel.register(bossSelector, SelectionKey.OP_ACCEPT);

        // Boss loop - accept connections
        while (true) {
            bossSelector.select();

            Iterator<SelectionKey> keys = bossSelector.selectedKeys().iterator();
            while (keys.hasNext()) {
                SelectionKey key = keys.next();
                keys.remove();

                if (key.isAcceptable()) {
                    acceptConnection((ServerSocketChannel) key.channel());
                }
            }
        }
    }

    private void acceptConnection(ServerSocketChannel server) throws IOException {
        SocketChannel client = server.accept();
        client.configureBlocking(false);

        // Round-robin to workers
        Selector workerSelector = workerSelectors[nextWorker];
        nextWorker = (nextWorker + 1) % workerCount;

        // Wake up worker and register channel
        workerSelector.wakeup();
        client.register(workerSelector, SelectionKey.OP_READ);
    }

    private void runWorker(int workerId) {
        Selector selector = workerSelectors[workerId];

        while (true) {
            try {
                selector.select();

                Iterator<SelectionKey> keys = selector.selectedKeys().iterator();
                while (keys.hasNext()) {
                    SelectionKey key = keys.next();
                    keys.remove();

                    if (key.isReadable()) {
                        handleRead(key);
                    } else if (key.isWritable()) {
                        handleWrite(key);
                    }
                }
            } catch (IOException e) {
                e.printStackTrace();
            }
        }
    }

    private void handleRead(SelectionKey key) throws IOException {
        // Read and process data
    }

    private void handleWrite(SelectionKey key) throws IOException {
        // Write response
    }
}
```

---

## Proactor Pattern

### Proactor vs Reactor

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                     REACTOR vs PROACTOR                                     │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  REACTOR (Synchronous Event Demultiplexing):                               │
│  1. Wait for events (select/poll/epoll)                                    │
│  2. Dispatch to handler                                                    │
│  3. Handler performs I/O operation (read/write)                            │
│  4. Handler processes data                                                 │
│                                                                             │
│  Application does the I/O!                                                  │
│                                                                             │
│  ─────────────────────────────────────────────────────────────────────────  │
│                                                                             │
│  PROACTOR (Asynchronous Event Demultiplexing):                             │
│  1. Initiate async I/O operation                                           │
│  2. OS/kernel performs I/O in background                                   │
│  3. Completion event delivered                                             │
│  4. Handler processes already-read data                                    │
│                                                                             │
│  OS does the I/O!                                                           │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘

When to use which:
- Reactor: Linux (epoll is very efficient), most Java servers
- Proactor: Windows (IOCP), when true async needed, Java AIO
```

---

## Performance Comparison

### Benchmarks

```
Connection Scalability (C10K Problem):
┌─────────────────────────────────────────────────────────────────────────────┐
│                                                                             │
│  Connections    BIO (threads)    NIO (selector)    AIO                     │
│  ──────────────────────────────────────────────────────────────────────    │
│      100            100              1-4             1-4                    │
│    1,000          1,000              1-4             1-4                    │
│   10,000         10,000*             1-8             1-8                    │
│  100,000        IMPOSSIBLE          8-16            8-16                    │
│                                                                             │
│  * Thread creation/context switching becomes bottleneck                     │
│                                                                             │
│  Memory Usage (per connection):                                             │
│  - BIO: ~1MB (thread stack) + buffers                                      │
│  - NIO: ~few KB (SelectionKey + buffers)                                   │
│  - AIO: ~few KB (similar to NIO)                                           │
│                                                                             │
│  Latency (single connection):                                               │
│  - BIO: Lowest (dedicated thread, no multiplexing overhead)                │
│  - NIO: Slightly higher (selector overhead)                                │
│  - AIO: Slightly higher (async overhead)                                   │
└─────────────────────────────────────────────────────────────────────────────┘
```

### When to Use What

```
Decision Matrix:
┌─────────────────────────────────────────────────────────────────────────────┐
│                                                                             │
│  Use BLOCKING I/O when:                                                     │
│  ✓ Few concurrent connections (< 100)                                      │
│  ✓ Simple request-response pattern                                         │
│  ✓ Long-running operations per request                                     │
│  ✓ Simplicity is priority                                                  │
│                                                                             │
│  Use NIO (Non-blocking) when:                                              │
│  ✓ Many concurrent connections (1000+)                                     │
│  ✓ Short-lived connections                                                 │
│  ✓ Need to handle C10K+ problem                                            │
│  ✓ Building servers, proxies, gateways                                     │
│                                                                             │
│  Use AIO (Async) when:                                                     │
│  ✓ File I/O with large files                                               │
│  ✓ Windows platform (IOCP)                                                 │
│  ✓ True async semantics needed                                             │
│  ✓ Callback-based programming preferred                                    │
│                                                                             │
│  In Practice:                                                               │
│  - Most Java servers use NIO (Netty, Tomcat NIO connector)                 │
│  - AIO adoption is limited (Linux AIO not as mature as epoll)              │
│  - Frameworks abstract the complexity (use Netty!)                         │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Interview Questions

### Q1: Explain the difference between Blocking and Non-Blocking I/O

```
Answer:

BLOCKING I/O:
- Thread waits (blocks) until I/O operation completes
- Simple programming model
- One thread per connection
- Doesn't scale well (thread overhead)

NON-BLOCKING I/O:
- I/O operations return immediately
- Returns EAGAIN/EWOULDBLOCK if not ready
- Single thread can handle multiple connections
- Requires polling or event notification (select/epoll)
- More complex but scales to thousands of connections

Key insight: The difference is in WHEN the thread waits:
- Blocking: Waits during the I/O operation
- Non-blocking: Waits at the selector (for any channel to be ready)
```

### Q2: What is the C10K problem?

```
Answer:

The C10K problem refers to handling 10,000+ concurrent connections.

With blocking I/O:
- 10,000 connections = 10,000 threads
- Each thread: ~1MB stack = 10GB RAM just for stacks
- Context switching overhead becomes prohibitive
- Thread scheduling becomes bottleneck

Solution: Non-blocking I/O with event multiplexing
- Single thread monitors all connections
- Only active connections consume CPU
- Memory usage: O(connections) not O(threads)

Modern servers handle C100K or C1M using:
- epoll (Linux) / kqueue (BSD) / IOCP (Windows)
- Event-driven architecture (Reactor pattern)
- Frameworks like Netty, Node.js
```

### Q3: Explain Selector in Java NIO

```java
// Selector allows single thread to monitor multiple channels

// Key concepts:
// 1. Register channels with selector for specific events
// 2. Call select() to block until events ready
// 3. Process ready channels
// 4. Repeat

Selector selector = Selector.open();

// Register channels
channel1.register(selector, SelectionKey.OP_READ);
channel2.register(selector, SelectionKey.OP_READ);

while (true) {
    // Blocks until at least one channel ready
    int ready = selector.select();

    // Process ready channels
    Set<SelectionKey> keys = selector.selectedKeys();
    for (SelectionKey key : keys) {
        if (key.isReadable()) {
            // Handle read
        }
    }
    keys.clear();  // Must clear!
}

// Under the hood:
// - Linux: Uses epoll
// - macOS: Uses kqueue
// - Windows: Uses select (less efficient)
```

### Q4: What is zero-copy and how does Java support it?

```java
// Zero-copy: Transfer data without copying through user space

// Traditional copy (4 copies):
// Disk → Kernel Buffer → User Buffer → Socket Buffer → NIC

// Zero-copy (2 copies with sendfile):
// Disk → Kernel Buffer → NIC (via DMA)

// Java zero-copy with FileChannel.transferTo()
public void zeroCopyTransfer(String file, SocketChannel socket)
        throws IOException {
    FileChannel fileChannel = FileChannel.open(Paths.get(file));

    // Directly transfers from file to socket
    // Uses sendfile() system call on Linux
    long transferred = fileChannel.transferTo(
        0, fileChannel.size(), socket);
}

// Also: MappedByteBuffer for memory-mapped files
FileChannel channel = FileChannel.open(path, READ);
MappedByteBuffer buffer = channel.map(
    FileChannel.MapMode.READ_ONLY, 0, channel.size());
// Buffer directly maps to file, no copying
```

### Q5: Compare Netty's threading model

```
Netty Threading Model:
┌─────────────────────────────────────────────────────────────────────────────┐
│                                                                             │
│  BossGroup (1-2 threads)                                                   │
│  └── Accepts connections                                                   │
│      └── Registers with WorkerGroup                                        │
│                                                                             │
│  WorkerGroup (CPU cores threads)                                           │
│  └── Each thread has own Selector                                          │
│      └── Handles READ/WRITE for assigned channels                          │
│          └── Executes ChannelHandler pipeline                              │
│                                                                             │
│  Key principles:                                                            │
│  1. One channel always handled by same thread (no sync needed)             │
│  2. Handlers should be non-blocking (offload to separate pool)             │
│  3. EventLoop = Thread + Selector + Task Queue                             │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘

// Netty example
EventLoopGroup bossGroup = new NioEventLoopGroup(1);
EventLoopGroup workerGroup = new NioEventLoopGroup();  // Default: CPU cores

ServerBootstrap b = new ServerBootstrap();
b.group(bossGroup, workerGroup)
 .channel(NioServerSocketChannel.class)
 .childHandler(new ChannelInitializer<SocketChannel>() {
     @Override
     protected void initChannel(SocketChannel ch) {
         ch.pipeline().addLast(new MyHandler());
     }
 });
```

### Q6: What happens when you call read() on a blocking socket?

```
System call flow:

1. Application calls read(socket, buffer, size)
2. Transition to kernel mode (syscall)
3. Kernel checks socket receive buffer:

   If buffer EMPTY:
   ├── Add thread to socket's wait queue
   ├── Set thread state to INTERRUPTIBLE
   ├── Context switch to another thread
   ├── ... (thread sleeping) ...
   ├── Data arrives (network interrupt)
   ├── Kernel copies data to socket buffer
   ├── Wake up waiting thread
   └── Thread scheduled to run

   If buffer has DATA:
   └── Copy data to user buffer immediately

4. Return to user mode with bytes read

Time breakdown (typical):
- Syscall overhead: ~100ns
- Context switch: ~1-10μs
- Network wait: 1ms - 100ms (depends on network)
- Data copy: ~1μs per KB
```


