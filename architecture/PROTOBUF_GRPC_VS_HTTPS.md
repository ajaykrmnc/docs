# Protocol Buffers and gRPC vs HTTPS/REST - Complete Technical Reference

This document provides a comprehensive comparison of Protocol Buffers (Protobuf) and gRPC versus traditional HTTPS/REST with JSON, explaining why certain protocols are chosen for specific use cases like AP telemetry.


## Overview

### Protocol Comparison at a Glance

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        DATA TRANSFER PROTOCOLS                               │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────────────────────┐    ┌─────────────────────────────────┐    │
│  │     REST/HTTPS (JSON)       │    │       gRPC (Protobuf)           │    │
│  ├─────────────────────────────┤    ├─────────────────────────────────┤    │
│  │  • Text-based (JSON/XML)    │    │  • Binary format                │    │
│  │  • Human readable           │    │  • Machine optimized            │    │
│  │  • HTTP/1.1 typically       │    │  • HTTP/2 always                │    │
│  │  • Request/Response only    │    │  • Bidirectional streaming      │    │
│  │  • Schema optional          │    │  • Schema required (.proto)     │    │
│  │  • Larger payload size      │    │  • Smaller payload size         │    │
│  │  • Universal browser support│    │  • Requires grpc-web for browser│    │
│  │  • Easy debugging           │    │  • Harder debugging (binary)    │    │
│  └─────────────────────────────┘    └─────────────────────────────────┘    │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Quick Comparison

| Aspect | REST/HTTPS + JSON | gRPC + Protobuf |
|--------|-------------------|-----------------|
| **Primary Use** | Public APIs, Web | Internal services, IoT |
| **Data Format** | Text (JSON) | Binary |
| **Performance** | Good | Excellent |
| **Ease of Use** | Easy | Moderate |
| **Browser Support** | Native | Limited (grpc-web) |

---

## What is Protobuf?

### Definition

**Protocol Buffers (Protobuf)** is Google's language-neutral, platform-neutral, extensible mechanism for serializing structured data. It's like JSON or XML, but smaller, faster, and simpler.

### How Protobuf Works

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         PROTOBUF WORKFLOW                                    │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  1. Define Schema (.proto file)                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  message Client {                                                    │   │
│  │    bytes mac = 1;                                                    │   │
│  │    int32 rssi = 2;                                                   │   │
│  │    string ssid = 3;                                                  │   │
│  │  }                                                                   │   │
│  └──────────────────────────────┬──────────────────────────────────────┘   │
│                                 │                                           │
│  2. Generate Code (protoc)      ▼                                           │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  $ protoc --go_out=. --c_out=. client.proto                         │   │
│  └──────────────────────────────┬──────────────────────────────────────┘   │
│                                 │                                           │
│  3. Generated Code              ▼                                           │
│  ┌───────────────────┐    ┌───────────────────┐    ┌───────────────────┐   │
│  │  client.pb.go     │    │  client.pb.c      │    │  client_pb2.py    │   │
│  │  (Go bindings)    │    │  (C bindings)     │    │  (Python bindings)│   │
│  └───────────────────┘    └───────────────────┘    └───────────────────┘   │
│                                                                             │
│  4. Use in Application                                                      │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  client := &Client{Mac: mac, Rssi: -64, Ssid: "MyNetwork"}          │   │
│  │  data, _ := proto.Marshal(client)    // Serialize to binary         │   │
│  │  proto.Unmarshal(data, &client)      // Deserialize from binary     │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Protobuf Schema Example

```protobuf
syntax = "proto3";

package telemetry;

// Client telemetry message
message ClientTelemetry {
  bytes mac = 1;              // Field number 1: MAC address (6 bytes)
  int32 rssi = 2;             // Field number 2: Signal strength
  uint32 channel = 3;         // Field number 3: WiFi channel
  uint64 tx_bytes = 4;        // Field number 4: Bytes transmitted
  uint64 rx_bytes = 5;        // Field number 5: Bytes received
  uint32 tx_packets = 6;      // Field number 6: Packets transmitted
  uint32 rx_packets = 7;      // Field number 7: Packets received
  float snr = 8;              // Field number 8: Signal-to-noise ratio
  repeated string ipv6 = 9;   // Field number 9: IPv6 addresses (array)
}

// Device telemetry message
message DeviceTelemetry {
  repeated float cpu_util = 1;    // Per-CPU utilization
  float mem_used = 2;             // Memory used percentage
  float mem_available = 3;        // Memory available percentage
}
```

### Key Protobuf Features

| Feature | Description |
|---------|-------------|
| **Field Numbers** | Unique identifiers (not names) for each field |
| **Wire Types** | Varint, 64-bit, length-delimited, 32-bit |
| **Optional Fields** | Fields can be omitted (zero value default) |
| **Repeated Fields** | Arrays/lists of values |
| **Nested Messages** | Messages within messages |
| **Enums** | Enumerated types |
| **Oneof** | Mutually exclusive fields |

---

## What is gRPC?

### Definition

**gRPC** (gRPC Remote Procedure Call) is a high-performance, open-source RPC framework developed by Google. It uses HTTP/2 for transport, Protobuf for serialization, and provides features like authentication, load balancing, and bidirectional streaming.

### gRPC Architecture Stack

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              gRPC STACK                                      │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                     APPLICATION LAYER                                │   │
│  │              (Your Service Methods & Business Logic)                 │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                    │                                        │
│  ┌─────────────────────────────────▼───────────────────────────────────┐   │
│  │                       gRPC FRAMEWORK                                 │   │
│  │         (Stubs, Channels, Interceptors, Load Balancing)              │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                    │                                        │
│  ┌─────────────────────────────────▼───────────────────────────────────┐   │
│  │                   PROTOBUF SERIALIZATION                             │   │
│  │              (Binary encoding/decoding of messages)                  │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                    │                                        │
│  ┌─────────────────────────────────▼───────────────────────────────────┐   │
│  │                       HTTP/2 TRANSPORT                               │   │
│  │       (Multiplexing, Streaming, Header Compression, Flow Control)    │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                    │                                        │
│  ┌─────────────────────────────────▼───────────────────────────────────┐   │
│  │                        TLS ENCRYPTION                                │   │
│  │                    (Optional but recommended)                        │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                    │                                        │
│  ┌─────────────────────────────────▼───────────────────────────────────┐   │
│  │                          TCP/IP                                      │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### gRPC Service Definition

```protobuf
syntax = "proto3";

package anmi;

import "gnmi/gnmi.proto";

// aNMI Service - Arista Network Management Interface
service aNMI {
  // Device capabilities exchange
  rpc Capabilities(DeviceCapability) returns (CapabilityResponse);

  // Pull - Server streams data to client (AP pulls config)
  rpc Pull(stream PullRequest) returns (stream PullResponse);

  // Publish - Client streams data to server (AP publishes telemetry)
  rpc Publish(stream PublishRequest) returns (stream PublishResponse);
}

message DeviceIdentity {
  string id = 1;  // Typically the MAC of the device
}

message PublishRequest {
  oneof pub {
    PublishStart pubstart = 1;
    gnmi.Notification update = 2;
  }
}

message PublishResponse {
  oneof resp {
    PublishIntervals intervals = 1;
    Error err = 2;
  }
}
```

### Key gRPC Features

| Feature | Description |
|---------|-------------|
| **HTTP/2 Based** | Multiplexing, header compression, flow control |
| **Streaming** | Client, server, and bidirectional streaming |
| **Deadlines/Timeouts** | Built-in timeout handling |
| **Cancellation** | Propagated across the call chain |
| **Authentication** | TLS, token-based, custom auth |
| **Load Balancing** | Client-side and proxy-based |
| **Interceptors** | Middleware for logging, auth, etc. |

---

## What is REST/HTTPS?

### Definition

**REST** (Representational State Transfer) is an architectural style for designing networked applications. Combined with HTTPS (HTTP Secure), it provides a secure, stateless way to transfer data using standard HTTP methods.

### REST Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                            REST/HTTPS STACK                                  │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                     APPLICATION LAYER                                │   │
│  │                (API Endpoints, Business Logic)                       │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                    │                                        │
│  ┌─────────────────────────────────▼───────────────────────────────────┐   │
│  │                      JSON SERIALIZATION                              │   │
│  │              (Text-based encoding/decoding)                          │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                    │                                        │
│  ┌─────────────────────────────────▼───────────────────────────────────┐   │
│  │                       HTTP/1.1 (or HTTP/2)                           │   │
│  │              (Request/Response, Headers, Methods)                    │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                    │                                        │
│  ┌─────────────────────────────────▼───────────────────────────────────┐   │
│  │                        TLS ENCRYPTION                                │   │
│  │                       (HTTPS = HTTP + TLS)                           │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                    │                                        │
│  ┌─────────────────────────────────▼───────────────────────────────────┐   │
│  │                          TCP/IP                                      │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### REST HTTP Methods

| Method | Purpose | Example |
|--------|---------|---------|
| **GET** | Retrieve resource | `GET /api/clients/E4:D1:24:A0:47:60` |
| **POST** | Create resource | `POST /api/clients` |
| **PUT** | Update resource (full) | `PUT /api/clients/E4:D1:24:A0:47:60` |
| **PATCH** | Update resource (partial) | `PATCH /api/clients/E4:D1:24:A0:47:60` |
| **DELETE** | Delete resource | `DELETE /api/clients/E4:D1:24:A0:47:60` |

### REST/JSON Example

```json
// Request
POST /api/telemetry HTTP/1.1
Host: cloud.example.com
Content-Type: application/json
Authorization: Bearer eyJhbGciOiJIUzI1NiIs...

{
  "mac": "E4:D1:24:A0:47:60",
  "rssi": -64,
  "channel": 36,
  "txBytes": 1234567890,
  "rxBytes": 9876543210,
  "ssid": "Corporate-WiFi"
}

// Response
HTTP/1.1 200 OK
Content-Type: application/json

{
  "status": "success",
  "message": "Telemetry received"
}
```

---

## Key Differences

### Comprehensive Comparison Table

| Feature | REST/HTTPS + JSON | gRPC + Protobuf |
|---------|-------------------|-----------------|
| **Data Format** | Text (JSON/XML) | Binary |
| **Schema** | Optional (OpenAPI) | Required (.proto) |
| **HTTP Version** | HTTP/1.1 (usually) | HTTP/2 (always) |
| **Streaming** | Limited | Native (4 types) |
| **Browser Support** | Native | Requires grpc-web |
| **Code Generation** | Optional | Automatic |
| **Debugging** | Easy (readable) | Hard (binary) |
| **Payload Size** | Larger | 3-10x smaller |
| **Serialization Speed** | Slower | 10x faster |
| **Type Safety** | Runtime validation | Compile-time |
| **Learning Curve** | Easy | Moderate |
| **Tooling** | Extensive | Growing |
| **Error Handling** | HTTP status codes | Rich error model |
| **Versioning** | URL/Header based | Schema evolution |

---

## Serialization Comparison

### Same Data, Different Formats

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                     SERIALIZATION SIZE COMPARISON                            │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  Data: Client with MAC, RSSI, Channel, TX Bytes                             │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  JSON (Text) - 95 bytes:                                             │   │
│  │  {                                                                   │   │
│  │    "mac": "E4:D1:24:A0:47:60",                                      │   │
u oiu ou │  │    "rssi": -64,                                                     
│   │
│  │    "channel": 36,                                                   │   │
│  │    "txBytes": 1234567890                                            │   │
│  │  }                                                                   │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  XML (Text) - 156 bytes:                                             │   │
│  │  <?xml version="1.0"?>                                               │   │
│  │  <client>                                                            │   │
│  │    <mac>E4:D1:24:A0:47:60</mac>                                     │   │
│  │    <rssi>-64</rssi>                                                 │   │
│  │    <channel>36</channel>                                            │   │
│  │    <txBytes>1234567890</txBytes>                                    │   │
│  │  </client>                                                           │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  Protobuf (Binary) - 22 bytes:                                       │   │
│  │  0A 06 E4 D1 24 A0 47 60 10 40 18 24 20 D2 85 D8 CC 04              │   │
│  │                                                                      │   │
│  │  Breakdown:                                                          │   │
│  │  0A 06 [6 bytes MAC]     - Field 1, length 6                        │   │
│  │  10 40                   - Field 2, varint -64                      │   │
│  │  18 24                   - Field 3, varint 36                       │   │
│  │  20 [5 bytes varint]     - Field 4, varint 1234567890              │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  Size Comparison:                                                           │
│  ┌──────────────┬──────────┬────────────────┐                              │
│  │ Format       │ Size     │ vs Protobuf    │                              │
│  ├──────────────┼──────────┼────────────────┤                              │
│  │ Protobuf     │ 22 bytes │ baseline       │                              │
│  │ JSON         │ 95 bytes │ 4.3x larger    │                              │
│  │ XML          │ 156 bytes│ 7.1x larger    │                              │
│  └──────────────┴──────────┴────────────────┘                              │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Protobuf Wire Format

| Wire Type | Value | Used For |
|-----------|-------|----------|
| 0 | Varint | int32, int64, uint32, uint64, bool, enum |
| 1 | 64-bit | fixed64, sfixed64, double |
| 2 | Length-delimited | string, bytes, embedded messages, repeated |
| 5 | 32-bit | fixed32, sfixed32, float |

### Varint Encoding

Protobuf uses variable-length encoding for integers:

```
Value: 300

Binary: 00000001 00101100 (2 bytes in standard int16)

Varint: 10101100 00000010 (2 bytes, MSB indicates continuation)
        └─ 0101100 = 44    └─ 0000010 = 2

Result: (2 << 7) | 44 = 256 + 44 = 300
```

---

## Transport Protocol Comparison

### HTTP/1.1 vs HTTP/2

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                       HTTP/1.1 vs HTTP/2                                     │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  HTTP/1.1 (REST typically):                                                 │
│  ┌─────────┐     ┌─────────┐                                               │
│  │ Client  │     │ Server  │                                               │
│  └────┬────┘     └────┬────┘                                               │
│       │               │                                                     │
│       │──Request 1───▶│  ─┐                                                │
│       │◀──Response 1──│   │ Sequential                                     │
│       │               │   │ (Head-of-line blocking)                        │
│       │──Request 2───▶│   │                                                │
│       │◀──Response 2──│  ─┘                                                │
│       │               │                                                     │
│                                                                             │
│  HTTP/2 (gRPC):                                                             │
│  ┌─────────┐     ┌─────────┐                                               │
│  │ Client  │     │ Server  │                                               │
│  └────┬────┘     └────┬────┘                                               │
│       │               │                                                     │
│       │══Stream 1════▶│  ─┐                                                │
│       │══Stream 2════▶│   │ Multiplexed                                    │
│       │◀═════Stream 1═│   │ (Parallel on single connection)                │
│       │══Stream 3════▶│   │                                                │
│       │◀═════Stream 2═│  ─┘                                                │
│       │◀═════Stream 3═│                                                     │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### HTTP/2 Features Used by gRPC

| Feature | Benefit |
|---------|---------|
| **Multiplexing** | Multiple requests on single connection |
| **Header Compression (HPACK)** | Reduced overhead |
| **Binary Framing** | Efficient parsing |
| **Server Push** | Proactive data sending |
| **Stream Prioritization** | Important data first |
| **Flow Control** | Prevents overwhelming receivers |

---

## Communication Patterns

### REST vs gRPC Patterns

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        COMMUNICATION PATTERNS                                │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  REST: Request/Response Only                                         │   │
│  │                                                                      │   │
│  │  Client ─────── Request ─────────▶ Server                           │   │
│  │  Client ◀────── Response ───────── Server                           │   │
│  │                                                                      │   │
│  │  (For streaming: WebSocket or Server-Sent Events as workaround)     │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  gRPC: Four Native Patterns                                          │   │
│  │                                                                      │   │
│  │  1. Unary RPC (like REST):                                          │   │
│  │     rpc GetClient(ClientRequest) returns (ClientResponse);          │   │
│  │     Client ──────▶ Server                                           │   │
│  │     Client ◀────── Server                                           │   │
│  │                                                                      │   │
│  │  2. Server Streaming RPC:                                           │   │
│  │     rpc ListClients(Filter) returns (stream Client);                │   │
│  │     Client ──────▶ Server                                           │   │
│  │     Client ◀────── Server (message 1)                               │   │
│  │     Client ◀────── Server (message 2)                               │   │
│  │     Client ◀────── Server (message N)                               │   │
│  │                                                                      │   │
│  │  3. Client Streaming RPC:                                           │   │
│  │     rpc UploadTelemetry(stream Telemetry) returns (Summary);        │   │
│  │     Client ──────▶ Server (message 1)                               │   │
│  │     Client ──────▶ Server (message 2)                               │   │
│  │     Client ──────▶ Server (message N)                               │   │
│  │     Client ◀────── Server (single response)                         │   │
│  │                                                                      │   │
│  │  4. Bidirectional Streaming RPC:                                    │   │
u
│  │     rpc Publish(stream Request) returns (stream Response);          │   │
│  │     Client ◀─────▶ Server (both stream simultaneously)              │   │
│  │                                                                      │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Streaming Example (from AP codebase)

```protobuf
// AP publishes telemetry as a stream
service aNMI {
  // Bidirectional streaming - AP publishes data, server sends control messages
  rpc Publish(stream PublishRequest) returns (stream PublishResponse);
}

message PublishRequest {
  oneof pub {
    PublishStart pubstart = 1;      // Initial handshake
    gnmi.Notification update = 2;    // Telemetry update
  }
}

message PublishResponse {
  oneof resp {
    PublishIntervals intervals = 1;  // Server adjusts publish rate
    Error err = 2;                   // Error from server
  }
}
```

---

## Performance Comparison

### Benchmark Results (Typical)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                     PERFORMANCE BENCHMARKS                                   │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  Test: 10,000 client telemetry records                                      │
│                                                                             │
│  ┌─────────────────────┬───────────────┬─────────────────┬──────────────┐  │
│  │ Metric              │ REST/JSON     │ gRPC/Protobuf   │ Improvement  │  │
│  ├─────────────────────┼───────────────┼─────────────────┼──────────────┤  │
│  │ Payload Size        │ 950 KB        │ 220 KB          │ 77% smaller  │  │
│  │ Serialization Time  │ 45 ms         │ 5 ms            │ 9x faster    │  │
│  │ Deserialization     │ 52 ms         │ 4 ms            │ 13x faster   │  │
│  │ Network Transfer    │ 120 ms        │ 35 ms           │ 3.4x faster  │  │
│  │ Total Latency       │ 217 ms        │ 44 ms           │ 4.9x faster  │  │
│  │ Throughput          │ 46 req/sec    │ 227 req/sec     │ 4.9x higher  │  │
│  │ CPU Usage           │ 78%           │ 25%             │ 3.1x less    │  │
│  │ Memory (peak)       │ 128 MB        │ 42 MB           │ 3x less      │  │
│  └─────────────────────┴───────────────┴─────────────────┴──────────────┘  │
│                                                                             │
│  Visualization:                                                             │
│                                                                             │
│  Payload Size:                                                              │
│  REST/JSON  ████████████████████████████████████████████████ 950 KB        │
│  gRPC/Proto ███████████ 220 KB                                              │
│                                                                             │
│  Latency:                                                                   │
│  REST/JSON  ████████████████████████████████████████████████ 217 ms        │
│  gRPC/Proto █████████ 44 ms                                                 │
│                                                                             │
│  Throughput:                                                                │
│  REST/JSON  █████████ 46 req/sec                                            │
│  gRPC/Proto ████████████████████████████████████████████████ 227 req/sec   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Bandwidth Impact for AP Telemetry

```
Scenario: 1000 clients × telemetry every 30 seconds

┌─────────────────────────────────────────────────────────────────────────────┐
│                      BANDWIDTH CALCULATION                                   │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  JSON Format:                                                               │
│  • Per-client record: ~500 bytes                                            │
│  • 1000 clients × 500 bytes = 500 KB per interval                          │
│  • 500 KB ÷ 30 seconds = 16.7 KB/sec = 133 Kbps                            │
│                                                                             │
│  Protobuf Format:                                                           │
│  • Per-client record: ~100 bytes                                            │
│  • 1000 clients × 100 bytes = 100 KB per interval                          │
│  • 100 KB ÷ 30 seconds = 3.3 KB/sec = 27 Kbps                              │
│                                                                             │
│  ┌───────────────────────────────────────────────────────────────────┐     │
│  │                    Bandwidth Savings: 80%                         │     │
│  │         (Crucial for APs with limited uplink bandwidth)           │     │
│  └───────────────────────────────────────────────────────────────────┘     │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Why AP Uses Protobuf/gRPC

### 1. Bandwidth Constraints

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                      AP BANDWIDTH CONSTRAINTS                                │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌───────────────┐                    ┌───────────────┐                    │
│  │     AP        │                    │    Cloud      │                    │
│  │               │                    │               │                    │
│  │ • 200+ clients│  ──── Uplink ────▶ │  • Analytics  │                    │
│  │ • Telemetry   │    (Limited BW)    │  • Management │                    │
│  │ • Analytics   │                    │  • Dashboards │                    │
│  └───────────────┘                    └───────────────┘                    │
│                                                                             │
│  Uplink constraints:                                                        │
│  • Shared with client traffic                                               │
│  • May be congested                                                         │
│  • WAN link limitations                                                     │
│                                                                             │
│  Protobuf benefits:                                                         │
│  • 70-80% smaller payloads                                                  │
│  • More data per available bandwidth                                        │
│  • Less competition with user traffic                                       │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 2. CPU/Memory Constraints

```c
// JSON parsing (slow, memory intensive)
json_object *obj = json_tokener_parse(json_string);  // Full parse into memory
const char *mac = json_object_get_string(
    json_object_object_get(obj, "mac")               // String lookup
);
int rssi = json_object_get_int(
    json_object_object_get(obj, "rssi")              // Another string lookup
);
json_object_put(obj);                                // Manual cleanup

// Protobuf parsing (fast, efficient)
ClientTelemetry msg = CLIENT_TELEMETRY__INIT;
client_telemetry__unpack(NULL, len, buffer, &msg);   // Direct binary decode
// msg.mac, msg.rssi available immediately           // Direct field access
// No manual cleanup for stack-allocated messages
```

### 3. Streaming Requirements

APs need to continuously stream telemetry data:

```go
// From AP codebase - continuous telemetry publishing
func (client *AnmiClient) PublishTelemetry(ctx context.Context) error {
    stream, err := client.Publish(ctx)
    if err != nil {
        return err
    }

    // Send initial handshake
    stream.Send(&PublishRequest{
        Pub: &PublishRequest_Pubstart{
            Pubstart: &PublishStart{
                Clientid: &DeviceIdentity{Id: apMac},
            },
        },
    })

    // Continuously stream telemetry
    for {
        select {
        case telemetry := <-telemetryChannel:
            stream.Send(&PublishRequest{
                Pub: &PublishRequest_Update{
                    Update: telemetry,
                },
            })
        case resp := <-responseChannel:
            // Handle server responses (rate adjustments, etc.)
            handleResponse(resp)
        }
    }
}
```

### 4. Strong Typing and Schema Evolution

```protobuf
// Version 1 - Original schema
message ClientTelemetry {
  bytes mac = 1;
  int32 rssi = 2;
}

// Version 2 - Added new fields (backward compatible!)
message ClientTelemetry {
  bytes mac = 1;
  int32 rssi = 2;
  uint32 mcs_rate = 3;      // New field - old receivers ignore
  float snr = 4;            // New field - old receivers ignore
}

// Version 3 - Deprecated field (still backward compatible)
message ClientTelemetry {
  bytes mac = 1;
  int32 rssi = 2 [deprecated = true];  // Marked deprecated
  uint32 mcs_rate = 3;
  float snr = 4;
  int32 rssi_dbm = 5;       // Replacement field
}
```

---

## When to Use Each Protocol

### Decision Matrix

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        PROTOCOL SELECTION GUIDE                              │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  Use REST/HTTPS + JSON when:                                                │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  ✓ Building public APIs                                              │   │
│  │  ✓ Browser clients (web applications)                                │   │
│  │  ✓ Third-party integrations                                          │   │
│  │  ✓ Human-readable debugging is important                             │   │
│  │  ✓ Caching is needed (HTTP caching)                                  │   │
│  │  ✓ Simple request/response patterns                                  │   │
│  │  ✓ Wide ecosystem/library support needed                             │   │
│  │  ✓ Team is more familiar with REST                                   │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  Use gRPC + Protobuf when:                                                  │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  ✓ High-performance internal services                                │   │
│  │  ✓ Microservice-to-microservice communication                        │   │
│  │  ✓ IoT/embedded devices with limited resources                       │   │
│  │  ✓ Real-time streaming requirements                                  │   │
│  │  ✓ Bandwidth-constrained networks                                    │   │
│  │  ✓ Strong typing and schema enforcement needed                       │   │
│  │  ✓ Polyglot environments (multi-language)                            │   │
│  │  ✓ Bidirectional communication needed                                │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Use Case Examples

| Use Case | Recommended | Reason |
|----------|-------------|--------|
| **Public REST API** | REST/JSON | Universal compatibility, easy testing |
| **Web Dashboard** | REST/JSON | Native browser support |
| **Mobile App Backend** | gRPC | Efficient, smaller battery drain |
| **Microservices** | gRPC | High performance, strong contracts |
| **AP Telemetry** | gRPC/Protobuf | Streaming, bandwidth, CPU efficiency |
| **IoT Sensors** | Protobuf | Minimal overhead |
| **Third-Party Analytics** | REST/JSON | External compatibility |
| **Config Management** | gNMI (gRPC) | Industry standard for network devices |
| **Real-time Monitoring** | gRPC | Bidirectional streaming |
| **Batch Data Export** | Either | Depends on consumer |

---

## Implementation Examples

### REST/JSON Client (Go)

```go
// REST client for third-party analytics
func postWifiRssiData() error {
    // Prepare JSON payload
    data := RssiData{
        LanMac:    ap.DeviceMac.String(),
        Timestamp: time.Now().Unix(),
        Clients:   collectClientRssi(),
    }

    jsonData, err := json.Marshal(data)
    if err != nil {
        return err
    }

    // HTTP POST request
    resp, err := http.Post(
        serverURL,
        "application/json",
        bytes.NewBuffer(jsonData),
    )
    if err != nil {
        return err
    }
    defer resp.Body.Close()

    if resp.StatusCode != http.StatusOK {
        return fmt.Errorf("server returned %d", resp.StatusCode)
    }

    return nil
}
```

### gRPC/Protobuf Client (Go)

```go
// gRPC client for telemetry streaming
func publishTelemetry(client anmi.ANMIClient) error {
    // Create bidirectional stream
    stream, err := client.Publish(context.Background())
    if err != nil {
        return err
    }

    // Send initial handshake
    err = stream.Send(&anmi.PublishRequest{
        Pub: &anmi.PublishRequest_Pubstart{
            Pubstart: &anmi.PublishStart{
                Clientid: &anmi.DeviceIdentity{Id: apMac},
            },
        },
    })
    if err != nil {
        return err
    }

    // Continuous telemetry loop
    ticker := time.NewTicker(30 * time.Second)
    for range ticker.C {
        telemetry := collectTelemetry()

        err = stream.Send(&anmi.PublishRequest{
            Pub: &anmi.PublishRequest_Update{
                Update: telemetry,
            },
        })
        if err != nil {
            return err
        }
    }

    return nil
}
```

### Protobuf Serialization (C)

```c
// From AP codebase - sending device telemetry
int SendDeviceTelemetryRec(const C_APRuntime_SystemPerf* PerfRec) {
    ApDeviceTelemetryRec perfData = AP_DEVICE_TELEMETRY_REC__INIT;

    // Populate protobuf message
    perfData.n_cpu_util = APRuntime_SystemPerf_cpuUtilization_SIZE;
    perfData.cpu_util = allocate_cpu_util_array(perfData.n_cpu_util);

    for (int core = 0; core < perfData.n_cpu_util; core++) {
        perfData.cpu_util[core] = create_cpu_util_entry(PerfRec, core);
    }

    // Serialize to binary
    size_t len = ap_device_telemetry_rec__get_packed_size(&perfData);
    void* buffer = malloc(SNDREC_BASICSIZE + len);

    // Set header
    SREC_SETHDR(buffer, AP_DEVICE_TELEMETRY_REC, NULL, sensor_macaddress, len);

    // Pack protobuf data
    ap_device_telemetry_rec__pack(&perfData, buffer + SNDREC_BASICSIZE);

    // Send
    int ret = Send_Protobuf_Record(buffer, SNDREC_BASICSIZE + len, RELIABLE);

    free(buffer);
    return ret;
}
```

---

## Schema Evolution

### Backward and Forward Compatibility

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        SCHEMA EVOLUTION                                      │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  Protobuf Compatibility Rules:                                              │
│                                                                             │
│  ✓ SAFE Changes:                                                            │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  • Add new fields (with new field numbers)                          │   │
│  │  • Remove optional fields                                            │   │
│  │  • Rename fields (wire format uses numbers, not names)              │   │
│  │  • Change int32 ↔ int64, uint32 ↔ uint64                            │   │
│  │  • Add values to enums                                               │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  ✗ UNSAFE Changes:                                                          │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  • Change field numbers                                              │   │
│  │  • Change field types incompatibly (string ↔ int)                   │   │
│  │  • Remove required fields                                            │   │
│  │  • Reuse deleted field numbers                                       │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  Example Evolution:                                                         │
│                                                                             │
│  v1.0                  v1.1                   v2.0                         │
│  ┌──────────────┐     ┌──────────────┐      ┌──────────────┐              │
│  │ mac = 1      │     │ mac = 1      │      │ mac = 1      │              │
│  │ rssi = 2     │ ──▶ │ rssi = 2     │ ──▶  │ rssi = 2     │              │
│  │              │     │ channel = 3  │      │ channel = 3  │              │
│  │              │     │              │      │ mcs_rate = 4 │              │
│  └──────────────┘     └──────────────┘      │ snr = 5      │              │
│                                              └──────────────┘              │
│                                                                             │
│  • Old clients can read new messages (ignore unknown fields)               │
│  • New clients can read old messages (missing fields get defaults)         │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### JSON Schema Evolution Challenges

```json
// v1.0 - Original
{"mac": "E4:D1:24:A0:47:60", "rssi": -64}

// v1.1 - Added field (breaking if required!)
{"mac": "E4:D1:24:A0:47:60", "rssi": -64, "channel": 36}

// v2.0 - Changed type (BREAKING!)
{"mac": "E4:D1:24:A0:47:60", "rssi": "-64 dBm", "channel": 36}
//                                   ^^^^^^^^ Now a string!

// Problems:
// • No built-in schema versioning
// • Type changes break clients silently
// • No compile-time checking
// • Must handle missing fields manually
```

---

## Debugging and Tooling

### REST/JSON Tools

| Tool | Purpose |
|------|---------|
| **curl** | Command-line HTTP client |
| **Postman** | GUI API testing |
| **Browser DevTools** | Inspect network requests |
| **jq** | JSON processing |
| **Swagger/OpenAPI** | API documentation |

### gRPC/Protobuf Tools

| Tool | Purpose |
|------|---------|
| **grpcurl** | Command-line gRPC client |
| **BloomRPC** | GUI gRPC testing |
| **grpc-web-devtools** | Browser extension |
| **protoc** | Protobuf compiler |
| **buf** | Modern protobuf tooling |

### Debugging Protobuf Messages

```bash
# Decode protobuf message (requires .proto file)
protoc --decode=ClientTelemetry client.proto < binary_message.bin

# Using grpcurl to call gRPC service
grpcurl -plaintext \
    -d '{"id": "E4:D1:24:A0:47:60"}' \
    localhost:50051 \
    anmi.ANMI/GetClient

# Inspect protobuf binary (raw)
xxd binary_message.bin
```

---

## Summary

### Quick Reference

| Aspect | REST/HTTPS + JSON | gRPC + Protobuf |
|--------|-------------------|-----------------|
| **Best For** | Public APIs, Web | Internal services, IoT |
| **Payload Size** | Larger (text) | Smaller (binary) |
| **Performance** | Good | Excellent |
| **Streaming** | Limited | Native |
| **Browser Support** | Native | grpc-web required |
| **Debugging** | Easy | Harder |
| **Schema** | Optional | Required |
| **Learning Curve** | Easy | Moderate |

### AP Codebase Usage

| Component | Protocol | Reason |
|-----------|----------|--------|
| Telemetry to Cloud | Protobuf/gRPC | Streaming, efficiency |
| aNMI Management | gRPC | Bidirectional, gNMI standard |
| Third-Party Analytics | REST/JSON | External compatibility |
| Internal IPC | Protobuf | Speed, type safety |

---

## References

### Internal Code References

- **aNMI Protocol**: `ap/src/go/arista-ap/anet/anmi/proto/anmi.proto`
- **Device Telemetry**: `ap/src/sensord/src/ards/device_telemetry_handlers.c`
- **Protobuf Records**: `ap/src/sensord/src/spectradata/granular_tel_rec.c`
- **Third-Party Analytics**: `ap/src/go/arista-ap/gobin/third_party_analytics.go`
- **Protobuf Headers**: `ap/src/sensord/include/protobuf/protobuf_device.h`

### External References

- [Protocol Buffers Documentation](https://developers.google.com/protocol-buffers)
- [gRPC Documentation](https://grpc.io/docs/)
- [HTTP/2 RFC 7540](https://tools.ietf.org/html/rfc7540)
- [gNMI Specification](https://github.com/openconfig/gnmi)
- [REST Architectural Style](https://restfulapi.net/)

---

*Document Version: 1.0*
*Last Updated: 2026-01-10*

