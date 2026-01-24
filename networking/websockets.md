# WebSockets

## Overview

WebSocket is a **full-duplex, bidirectional** communication protocol that provides persistent connections
between client and server over a single TCP connection. Unlike HTTP's request-response model, WebSocket
enables real-time, two-way data flow.

```
Traditional HTTP:                    WebSocket:

Client ──req──► Server               Client ◄────────► Server
Client ◄──res── Server                  │   persistent   │
Client ──req──► Server                  │   connection   │
Client ◄──res── Server                  │                │
(half-duplex, stateless)             (full-duplex, stateful)
```

## WebSocket vs HTTP

| Feature    | HTTP                           | WebSocket                    |
| ---------- | ------------------------------ | ---------------------------- |
| Connection | Short-lived (per request)      | Persistent                   |
| Direction  | Half-duplex (request-response) | Full-duplex (bidirectional)  |
| Overhead   | Headers on every request       | Minimal frame overhead       |
| Initiation | Client only                    | Either client or server      |
| Use case   | REST APIs, page loads          | Real-time apps, live updates |

## The WebSocket Handshake

WebSocket connections start as HTTP and **upgrade** to the WebSocket protocol:

```
┌─────────────────────────────────────────────────────────────────┐
│                    WEBSOCKET HANDSHAKE                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  1. Client sends HTTP Upgrade request                            │
│     ┌───────────────────────────────────────────┐               │
│     │ GET /chat HTTP/1.1                        │               │
│     │ Host: server.example.com                  │               │
│     │ Upgrade: websocket                        │               │
│     │ Connection: Upgrade                       │               │
│     │ Sec-WebSocket-Key: dGhlIHNhbXBsZSBub25jZQ==│               │
│     │ Sec-WebSocket-Version: 13                 │               │
│     └───────────────────────────────────────────┘               │
│                         │                                        │
│                         ▼                                        │
│  2. Server accepts upgrade                                       │
│     ┌───────────────────────────────────────────┐               │
│     │ HTTP/1.1 101 Switching Protocols          │               │
│     │ Upgrade: websocket                        │               │
│     │ Connection: Upgrade                       │               │
│     │ Sec-WebSocket-Accept: s3pPLMBiTxaQ9kYGzz...│               │
│     └───────────────────────────────────────────┘               │
│                         │                                        │
│                         ▼                                        │
│  3. WebSocket connection established                             │
│     ◄═══════════════════════════════════════════►               │
│           Bidirectional binary frames                            │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

## Protocol Details

### URL Schemes

- `ws://` - Unencrypted WebSocket (port 80)
- `wss://` - Encrypted WebSocket over TLS (port 443)

### Frame Structure

```
0                   1                   2                   3
0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1
+-+-+-+-+-------+-+-------------+-------------------------------+
|F|R|R|R| opcode|M| Payload len |    Extended payload length    |
|I|S|S|S|  (4)  |A|     (7)     |             (16/64)           |
|N|V|V|V|       |S|             |   (if payload len==126/127)   |
| |1|2|3|       |K|             |                               |
+-+-+-+-+-------+-+-------------+-------------------------------+
|     Extended payload length (if payload len == 127)           |
+-------------------------------+-------------------------------+
|                     Masking-key (if MASK set)                 |
+-------------------------------+-------------------------------+
|                          Payload Data                         |
+---------------------------------------------------------------+
```

### Opcodes

| Opcode | Meaning            |
| ------ | ------------------ |
| 0x0    | Continuation frame |
| 0x1    | Text frame (UTF-8) |
| 0x2    | Binary frame       |
| 0x8    | Connection close   |
| 0x9    | Ping               |
| 0xA    | Pong               |

## Client-Side Implementation

```javascript
// Establish connection
const socket = new WebSocket("wss://api.example.com/ws");

// Connection opened
socket.addEventListener("open", (event) => {
  console.log("Connected to server");
  socket.send(JSON.stringify({ type: "subscribe", channel: "updates" }));
});

// Receive messages
socket.addEventListener("message", (event) => {
  const data = JSON.parse(event.data);
  console.log("Received:", data);
});

// Handle errors
socket.addEventListener("error", (error) => {
  console.error("WebSocket error:", error);
});

// Connection closed
socket.addEventListener("close", (event) => {
  console.log(`Closed: code=${event.code}, reason=${event.reason}`);
});

// Send message
socket.send(JSON.stringify({ type: "message", content: "Hello!" }));

// Close connection
socket.close(1000, "Normal closure");
```

## Server-Side Implementation (Node.js)

```javascript
const WebSocket = require("ws");
const server = new WebSocket.Server({ port: 8080 });

server.on("connection", (socket, request) => {
  console.log("Client connected");

  socket.on("message", (message) => {
    const data = JSON.parse(message);

    // Broadcast to all clients
    server.clients.forEach((client) => {
      if (client.readyState === WebSocket.OPEN) {
        client.send(JSON.stringify({ type: "broadcast", data }));
      }
    });
  });

  socket.on("close", () => console.log("Client disconnected"));
});
```

## Connection Lifecycle

```
┌───────────┐     ┌───────────┐     ┌───────────┐     ┌───────────┐
│ CONNECTING│────►│   OPEN    │────►│  CLOSING  │────►│  CLOSED   │
│  (0)      │     │   (1)     │     │   (2)     │     │   (3)     │
└───────────┘     └───────────┘     └───────────┘     └───────────┘
Handshake         Active           Close sent        Terminated
in progress       connection       or received
```

## Heartbeat / Keep-Alive

```
Client                          Server
│                               │
│◄────────── Ping ──────────────│
│─────────── Pong ─────────────►│
│                               │
│  (If no Pong received,        │
│   assume connection dead)     │
```

## Common Use Cases

| Use Case                | Example                    |
| ----------------------- | -------------------------- |
| Chat applications       | Slack, Discord             |
| Live notifications      | Social media feeds         |
| Real-time collaboration | Google Docs, Figma         |
| Gaming                  | Multiplayer games          |
| Financial data          | Stock tickers, trading     |
| IoT                     | Device monitoring, control |

## Scaling WebSockets

```
┌──────────────────┐
│   Redis Pub/Sub  │
│   (Message Bus)  │
└────────┬─────────┘
│
┌───────────────────┼───────────────────┐
│                   │                   │
┌─────▼─────┐       ┌─────▼─────┐       ┌─────▼─────┐
│  Server 1 │       │  Server 2 │       │  Server 3 │
│ (clients) │       │ (clients) │       │ (clients) │
└───────────┘       └───────────┘       └───────────┘
```

## Security Considerations

| Concern            | Mitigation                            |
| ------------------ | ------------------------------------- |
| Authentication     | Validate during handshake, use tokens |
| Authorization      | Check permissions per message/channel |
| Origin validation  | Verify `Origin` header                |
| Rate limiting      | Limit messages per connection         |
| Message validation | Validate/sanitize all incoming data   |
| Use TLS            | Always use `wss://` in production     |
