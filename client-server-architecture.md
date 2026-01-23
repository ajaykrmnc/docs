# Client-Server Architecture

## Overview

Client-server architecture is a distributed computing model where **clients** request services and **servers** provide them. This separation of concerns enables scalability, centralized data management, and specialized resource allocation.

```
┌──────────┐         Request          ┌──────────┐
│          │ ──────────────────────►  │          │
│  CLIENT  │                          │  SERVER  │
│          │ ◄──────────────────────  │          │
└──────────┘         Response         └──────────┘
```

## Core Components

### Client
- **Initiates** communication
- Sends requests for resources or services
- Renders UI and handles user interaction
- Examples: Web browsers, mobile apps, desktop applications

### Server
- **Listens** for incoming connections
- Processes requests and returns responses
- Manages shared resources (databases, files, computation)
- Examples: Web servers (Nginx, Apache), API servers, database servers

## Communication Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                        REQUEST/RESPONSE CYCLE                    │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  1. Client establishes connection (TCP handshake)                │
│                    │                                             │
│                    ▼                                             │
│  2. Client sends HTTP request                                    │
│     ┌─────────────────────────────────────┐                     │
│     │ GET /api/users HTTP/1.1             │                     │
│     │ Host: api.example.com               │                     │
│     │ Authorization: Bearer token123      │                     │
│     └─────────────────────────────────────┘                     │
│                    │                                             │
│                    ▼                                             │
│  3. Server processes request                                     │
│     - Authentication/Authorization                               │
│     - Business logic execution                                   │
│     - Database queries                                           │
│                    │                                             │
│                    ▼                                             │
│  4. Server sends HTTP response                                   │
│     ┌─────────────────────────────────────┐                     │
│     │ HTTP/1.1 200 OK                     │                     │
│     │ Content-Type: application/json      │                     │
│     │                                     │                     │
│     │ {"users": [...]}                    │                     │
│     └─────────────────────────────────────┘                     │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

## Architecture Patterns

### 1. Two-Tier Architecture
```
┌────────┐         ┌────────────────────┐
│ Client │ ◄─────► │ Server + Database  │
└────────┘         └────────────────────┘
```
- Direct client-to-database communication
- Simple but limited scalability

### 2. Three-Tier Architecture
```
┌────────┐      ┌─────────────┐      ┌──────────┐
│ Client │ ◄──► │ Application │ ◄──► │ Database │
│ (UI)   │      │   Server    │      │  Server  │
└────────┘      └─────────────┘      └──────────┘
```
- Separation of presentation, logic, and data
- Better scalability and maintainability

### 3. N-Tier / Microservices
```
┌────────┐      ┌─────────┐      ┌─────────────────────────────┐
│ Client │ ◄──► │ Gateway │ ◄──► │ Service A  Service B  ...   │
└────────┘      └─────────┘      │     │          │            │
                                 │     ▼          ▼            │
                                 │   DB A      DB B            │
                                 └─────────────────────────────┘
```

## Protocol Stack

| Layer | Protocol | Purpose |
|-------|----------|---------|
| Application | HTTP/HTTPS, gRPC, GraphQL | Request/Response semantics |
| Security | TLS/SSL | Encryption, authentication |
| Transport | TCP, UDP | Reliable/unreliable delivery |
| Network | IP | Routing and addressing |

## HTTP Methods (REST)

| Method | Purpose | Idempotent |
|--------|---------|------------|
| GET | Retrieve resource | ✅ Yes |
| POST | Create resource | ❌ No |
| PUT | Replace resource | ✅ Yes |
| PATCH | Partial update | ❌ No |
| DELETE | Remove resource | ✅ Yes |

## Connection Management

### Keep-Alive (HTTP/1.1+)
```
Connection: keep-alive
```
- Reuses TCP connections for multiple requests
- Reduces latency from repeated handshakes

### Connection Pooling
- Clients maintain a pool of reusable connections
- Prevents connection exhaustion under load

## Scaling Strategies

### Horizontal Scaling
```
                    ┌──────────┐
              ┌───► │ Server 1 │
┌────────┐    │     └──────────┘
│  Load  │────┤     ┌──────────┐
│Balancer│────┼───► │ Server 2 │
└────────┘    │     └──────────┘
              │     ┌──────────┐
              └───► │ Server 3 │
                    └──────────┘
```

### Caching Layers
```
Client ──► CDN ──► Reverse Proxy ──► Application ──► Cache ──► Database
                   (with cache)        Server       (Redis)
```

## Security Considerations

| Concern | Solution |
|---------|----------|
| Data in transit | TLS/HTTPS encryption |
| Authentication | JWT, OAuth 2.0, API keys |
| Authorization | RBAC, ABAC, scopes |
| Rate limiting | Token bucket, sliding window |
| Input validation | Server-side validation, sanitization |

## Advantages

- **Centralized data management**: Single source of truth
- **Scalability**: Scale servers independently
- **Security**: Centralized access control
- **Maintenance**: Update server without changing clients

## Disadvantages

- **Single point of failure**: Server downtime affects all clients
- **Network dependency**: Requires connectivity
- **Latency**: Network round-trips add delay
- **Cost**: Server infrastructure and maintenance

