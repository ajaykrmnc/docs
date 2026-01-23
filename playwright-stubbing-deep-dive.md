# Playwright Network Stubbing: A Complete Systems-Level Analysis

**Author's Note:** This document assumes familiarity with systems programming concepts from Maurice J. Bach's "The Design of the UNIX Operating System" and W. Richard Stevens' works on UNIX/network programming.

**Document Version:** 1.0
**Last Updated:** January 2026
**Target Audience:** Systems programmers, test engineers with deep technical background

---

## Table of Contents

1. [Introduction & Overview](#introduction--overview)
2. [Layer 0: Operating System & Network Stack](#layer-0-operating-system--network-stack)
3. [Layer 1: Browser Engine Architecture](#layer-1-browser-engine-architecture)
4. [Layer 2: Chrome DevTools Protocol (CDP)](#layer-2-chrome-devtools-protocol-cdp)
5. [Layer 3: Playwright Protocol Translation](#layer-3-playwright-protocol-translation)
6. [Layer 4: Request Lifecycle & State Machines](#layer-4-request-lifecycle--state-machines)
7. [Layer 5: Memory Management & Data Structures](#layer-5-memory-management--data-structures)
8. [Layer 6: Concurrency & Synchronization](#layer-6-concurrency--synchronization)
9. [Layer 7: Inter-Process Communication](#layer-7-inter-process-communication)
10. [Layer 8: Performance Analysis](#layer-8-performance-analysis)
11. [Layer 9: HAR File Implementation](#layer-9-har-file-implementation)
12. [Layer 10: Service Workers & Special Cases](#layer-10-service-workers--special-cases)
13. [Layer 11: Error Handling & Recovery](#layer-11-error-handling--recovery)
14. [Layer 12: Security Considerations](#layer-12-security-considerations)
15. [Layer 13: Advanced Patterns & Techniques](#layer-13-advanced-patterns--techniques)
16. [Layer 14: Browser Context & Multiple Tabs Testing](#layer-14-browser-context--multiple-tabs-testing)
17. [Layer 15: Comparison with Alternative Approaches](#layer-15-comparison-with-alternative-approaches)
18. [Layer 16: Implementation Deep Dive](#layer-16-implementation-deep-dive)
19. [Appendices](#appendices)

---

## Introduction & Overview

### What is Stubbing?

In the context of automated testing, **stubbing** refers to the practice of replacing real dependencies with controlled, predictable substitutes. In web testing, this primarily means intercepting and mocking network requests.

### Why Playwright's Approach is Unique

Unlike traditional HTTP proxies or in-browser mocking libraries, Playwright operates at the **browser protocol level**, providing:

- **No certificate issues** (interception before TLS)
- **Full request/response control** (headers, body, timing)
- **Programmatic API** (JavaScript/TypeScript/Python/C#)
- **Cross-browser support** (Chromium, Firefox, WebKit)
- **Process isolation** (test code separate from browser)

### The Complete Architecture Stack

```
┌─────────────────────────────────────────────────────────────┐
│                    User Test Code                           │
│              (JavaScript/TypeScript/Python/C#)              │
└────────────────────────┬────────────────────────────────────┘
                         │ API Calls (page.route())
                         ↓
┌─────────────────────────────────────────────────────────────┐
│              Playwright Client Library                      │
│         (Language-specific bindings + Protocol)             │
└────────────────────────┬────────────────────────────────────┘
                         │ WebSocket/Stdio
                         ↓
┌─────────────────────────────────────────────────────────────┐
│              Playwright Server (Node.js)                    │
│    (Protocol dispatcher, Route registry, State machine)     │
└────────────────────────┬────────────────────────────────────┘
                         │ CDP/Juggler/WebKit Protocol
                         ↓
┌─────────────────────────────────────────────────────────────┐
│                   Browser Process                           │
│         (Chromium/Firefox/WebKit + Network Stack)           │
└────────────────────────┬────────────────────────────────────┘
                         │ System Calls
                         ↓
┌─────────────────────────────────────────────────────────────┐
│              Operating System Network Stack                 │
│              (TCP/IP, Sockets, NIC drivers)                 │
└─────────────────────────────────────────────────────────────┘
```

**Key Insight:** The interception happens at the browser's network service layer, **after** security checks but **before** actual socket I/O.

---

## Layer 0: Operating System & Network Stack

### UNIX Network Stack Review

For context, let's review the traditional network stack that browsers ultimately use:

```
Application Layer (Browser)
         ↓
    Socket API (BSD sockets)
         ↓
    Transport Layer (TCP/UDP)
         ↓
    Network Layer (IP)
         ↓
    Data Link Layer (Ethernet/WiFi)
         ↓
    Physical Layer (NIC)
```

### System Calls Involved

When a browser makes an HTTP request without interception:

1. **socket()** - Create socket file descriptor
2. **connect()** - Establish TCP connection
3. **send()/write()** - Send HTTP request
4. **recv()/read()** - Receive HTTP response
5. **close()** - Close connection

### Where Playwright Does NOT Intercept

Playwright does **not** intercept at the OS level. The browser process still:

- Creates actual socket file descriptors
- Establishes TCP connections (for non-stubbed requests)
- Performs DNS resolution
- Handles TLS handshakes (for HTTPS)

**Important:** When you stub a request with `route.fulfill()`, the browser never calls `connect()` or `send()` for that specific request, but the socket infrastructure is still initialized.

### Process Model

Playwright operates in a multi-process architecture:

```
┌──────────────────────────────────────────────────────────┐
│  Test Process (Node.js/Python/etc.)                      │
│  PID: 1234                                               │
│  ┌────────────────────────────────────────────┐         │
│  │  User Test Code                            │         │
│  │  const page = await browser.newPage();     │         │
│  │  await page.route('**/*', handler);        │         │
│  └────────────────────────────────────────────┘         │
└────────────────┬─────────────────────────────────────────┘
                 │ IPC (pipe/socket)
                 ↓
┌──────────────────────────────────────────────────────────┐
│  Playwright Server Process (Node.js)                     │
│  PID: 1235                                               │
│  ┌────────────────────────────────────────────┐         │
│  │  Protocol Handler                          │         │
│  │  Route Registry                            │         │
│  │  State Management                          │         │
│  └────────────────────────────────────────────┘         │
└────────────────┬─────────────────────────────────────────┘
                 │ WebSocket/CDP
                 ↓
┌──────────────────────────────────────────────────────────┐
│  Browser Process (Chromium/Firefox/WebKit)               │
│  PID: 1236                                               │
│  ┌────────────────────────────────────────────┐         │
│  │  Browser Main Process                      │         │
│  └────────────────────────────────────────────┘         │
│  ┌────────────────────────────────────────────┐         │
│  │  Renderer Process (per tab/frame)          │         │
│  │  PID: 1237                                 │         │
│  └────────────────────────────────────────────┘         │
│  ┌────────────────────────────────────────────┐         │
│  │  Network Service Process                   │         │
│  │  PID: 1238                                 │         │
│  │  [INTERCEPTION HAPPENS HERE]               │         │
│  └────────────────────────────────────────────┘         │
└──────────────────────────────────────────────────────────┘
```

### File Descriptors & Resources

Each process maintains its own file descriptor table:

**Test Process:**

- FD 0: stdin
- FD 1: stdout
- FD 2: stderr
- FD 3: Pipe/socket to Playwright server
- FD 4+: Test-specific files

**Browser Process:**

- FD 0-2: Standard streams
- FD 3+: Sockets for actual network requests
- FD N: WebSocket connection to Playwright server

### Memory Isolation

Due to process separation:

- Test code cannot directly access browser memory
- All communication must be serialized
- Shared memory is NOT used (unlike some browser extensions)
- This adds latency but improves stability

### Signal Handling

When test process receives SIGTERM/SIGINT:

1. Playwright catches signal
2. Sends graceful shutdown to browser
3. Browser closes connections
4. Cleanup handlers run
5. Processes exit

---

## Layer 1: Browser Engine Architecture

### Chromium Architecture Overview

Chromium uses a multi-process architecture for security and stability:

```
┌─────────────────────────────────────────────────────────────┐
│                    Browser Process                          │
│  - UI thread                                                │
│  - IO thread (handles IPC)                                  │
│  - Main thread                                              │
└────────────┬────────────────────────────────────────────────┘
             │
             ├─────────────────────────────────────────────────┐
             │                                                 │
             ↓                                                 ↓
┌─────────────────────────┐                    ┌──────────────────────────┐
│   Renderer Process      │                    │  Network Service Process │
│   (Blink engine)        │                    │  (//services/network)    │
│                         │                    │                          │
│  - Main thread          │                    │  - Network thread        │
│  - Compositor thread    │                    │  - Socket pools          │
│  - Worker threads       │                    │  - HTTP cache            │
│                         │                    │  - Cookie store          │
│  JavaScript execution   │                    │  [INTERCEPTION POINT]    │
│  DOM manipulation       │                    │                          │
│  fetch() / XHR calls    │                    │                          │
└────────────┬────────────┘                    └──────────────────────────┘
             │                                              ↑
             │  IPC (Mojo)                                 │
             └──────────────────────────────────────────────┘
                         Request/Response
```

### Network Service Process

In modern Chromium (post-2018), networking runs in a separate process:

**Responsibilities:**

- DNS resolution
- Socket management
- HTTP/HTTPS protocol handling
- HTTP/2 and HTTP/3 (QUIC)
- Cookie management
- Cache management
- **Request interception** (via CDP)

**Why separate process?**

- Security: Isolate network code from renderer
- Stability: Network crashes don't kill tabs
- Resource management: Better control over sockets/memory

### Blink Rendering Engine

The renderer process runs Blink (Chromium's fork of WebKit):

```
JavaScript (V8 engine)
         ↓
    fetch() / XMLHttpRequest
         ↓
    Blink Bindings
         ↓
    ResourceFetcher
         ↓
    ResourceLoader
         ↓
    [IPC to Network Service]
         ↓
    Network Service Process
```

### Firefox Architecture (Gecko + Juggler)

Firefox uses a different architecture:

```
┌─────────────────────────────────────────────────────────────┐
│                    Parent Process                           │
│  - Main thread                                              │
│  - Socket thread                                            │
│  - Juggler protocol handler                                 │
└────────────┬────────────────────────────────────────────────┘
             │
             ↓
┌─────────────────────────────────────────────────────────────┐
│                  Content Process                            │
│  - Gecko rendering engine                                   │
│  - SpiderMonkey (JavaScript)                                │
│  - Network requests via IPDL                                │
└─────────────────────────────────────────────────────────────┘
```

**Juggler Protocol:**

- Custom protocol built by Mozilla for Playwright
- Similar to CDP but Firefox-specific
- Implements network interception at necko (network library) level

### WebKit Architecture

WebKit (used in Safari and Playwright's WebKit build):

```
┌─────────────────────────────────────────────────────────────┐
│                    UI Process                               │
│  - WebKit Inspector Protocol handler                        │
└────────────┬────────────────────────────────────────────────┘
             │
             ↓
┌─────────────────────────────────────────────────────────────┐
│                  WebContent Process                         │
│  - WebCore (rendering)                                      │
│  - JavaScriptCore (JS engine)                               │
│  - Network layer (CFNetwork on macOS, libsoup on Linux)     │
└─────────────────────────────────────────────────────────────┘
```

### Common Interception Pattern

Despite different architectures, all three browsers provide:

1. **Protocol-based debugging interface**
   - Chromium: Chrome DevTools Protocol (CDP)
   - Firefox: Juggler Protocol
   - WebKit: WebKit Inspector Protocol

2. **Network domain/module**
   - Enable network tracking
   - Intercept requests
   - Modify requests/responses
   - Abort requests

3. **Event-driven model**
   - Request initiated → Event fired
   - Test code handles event
   - Response sent back to browser

---

## Layer 2: Chrome DevTools Protocol (CDP)

### CDP Overview

CDP is a JSON-RPC protocol over WebSocket that allows external tools to instrument Chromium.

**Protocol Structure:**

```json
{
  "id": 1,
  "method": "Fetch.enable",
  "params": {
    "patterns": [
      {
        "urlPattern": "*",
        "requestStage": "Request"
      }
    ]
  }
}
```

### Fetch Domain

The `Fetch` domain is specifically designed for request interception:

**Key Methods:**

1. **Fetch.enable**

   ```json
   {
     "method": "Fetch.enable",
     "params": {
       "patterns": [
         {
           "urlPattern": "https://api.example.com/*",
           "requestStage": "Request"
         }
       ],
       "handleAuthRequests": false
     }
   }
   ```

   - Enables interception for matching patterns
   - `requestStage`: "Request" or "Response"
   - Returns: void

2. **Fetch.disable**

   ```json
   {
     "method": "Fetch.disable"
   }
   ```

   - Disables all interception
   - Pending requests auto-continue

3. **Fetch.continueRequest**

   ```json
   {
     "method": "Fetch.continueRequest",
     "params": {
       "requestId": "interceptionId.1",
       "url": "https://modified-url.com",
       "method": "POST",
       "postData": "base64EncodedData",
       "headers": [{ "name": "Authorization", "value": "Bearer token" }]
     }
   }
   ```

   - Continues intercepted request (possibly modified)
   - All params optional except `requestId`

4. **Fetch.fulfillRequest**

   ```json
   {
     "method": "Fetch.fulfillRequest",
     "params": {
       "requestId": "interceptionId.1",
       "responseCode": 200,
       "responseHeaders": [
         { "name": "Content-Type", "value": "application/json" }
       ],
       "body": "base64EncodedResponseBody",
       "responsePhrase": "OK"
     }
   }
   ```

   - Provides mock response
   - Browser never makes actual network request

5. **Fetch.failRequest**
   ```json
   {
     "method": "Fetch.failRequest",
     "params": {
       "requestId": "interceptionId.1",
       "errorReason": "Failed"
     }
   }
   ```

   - Aborts request with error
   - Error reasons: "Failed", "Aborted", "TimedOut", etc.

**Key Events:**

1. **Fetch.requestPaused**

   ```json
   {
     "method": "Fetch.requestPaused",
     "params": {
       "requestId": "interceptionId.1",
       "request": {
         "url": "https://api.example.com/users",
         "method": "GET",
         "headers": {
           "User-Agent": "Mozilla/5.0...",
           "Accept": "application/json"
         },
         "initialPriority": "High",
         "referrerPolicy": "strict-origin-when-cross-origin"
       },
       "frameId": "frame.1",
       "resourceType": "XHR",
       "networkId": "network.1"
     }
   }
   ```

   - Fired when request is intercepted
   - Contains full request details
   - Must respond with continue/fulfill/fail

2. **Fetch.authRequired** (optional)
   ```json
   {
     "method": "Fetch.authRequired",
     "params": {
       "requestId": "interceptionId.2",
       "request": {...},
       "authChallenge": {
         "source": "Server",
         "origin": "https://example.com",
         "scheme": "Basic",
         "realm": "Protected Area"
       }
     }
   }
   ```

   - Fired for HTTP 401/407 responses
   - Can provide credentials or cancel

### Network Domain (Legacy)

Before `Fetch` domain, CDP used `Network` domain for interception:

**Network.setRequestInterception** (deprecated):

```json
{
  "method": "Network.setRequestInterception",
  "params": {
    "patterns": [{ "urlPattern": "*", "interceptionStage": "HeadersReceived" }]
  }
}
```

**Why Fetch domain is better:**

- More granular control
- Can intercept at request OR response stage
- Better handling of redirects
- Supports auth challenges
- Cleaner API

### CDP Communication Flow

```
Playwright Server                    Chromium Browser
      │                                     │
      │  1. WebSocket connection            │
      ├────────────────────────────────────>│
      │                                     │
      │  2. Fetch.enable                    │
      ├────────────────────────────────────>│
      │                                     │
      │  3. Response: {}                    │
      │<────────────────────────────────────┤
      │                                     │
      │                                     │  User navigates
      │                                     │  fetch('https://api.com')
      │                                     │
      │  4. Fetch.requestPaused             │
      │<────────────────────────────────────┤
      │     {requestId: "1", request: {...}}│
      │                                     │
      │  [Playwright invokes user handler]  │
      │                                     │
      │  5. Fetch.fulfillRequest            │
      ├────────────────────────────────────>│
      │     {requestId: "1", body: "..."}   │
      │                                     │
      │  6. Response: {}                    │
      │<────────────────────────────────────┤
      │                                     │
      │                                     │  Browser receives
      │                                     │  mocked response
```

### CDP Message Format

**Request:**

```typescript
interface CDPRequest {
  id: number; // Unique message ID
  method: string; // e.g., "Fetch.enable"
  params?: object; // Method-specific parameters
  sessionId?: string; // For multi-target scenarios
}
```

**Response:**

```typescript
interface CDPResponse {
  id: number; // Matches request ID
  result?: object; // Success result
  error?: {
    // Or error
    code: number;
    message: string;
    data?: any;
  };
}
```

**Event:**

```typescript
interface CDPEvent {
  method: string; // e.g., "Fetch.requestPaused"
  params: object; // Event-specific data
  sessionId?: string;
}
```

### Request ID Management

CDP uses multiple ID types:

1. **requestId** (Fetch domain)
   - Unique per intercepted request
   - Format: "interceptionId.{number}"
   - Used for continue/fulfill/fail

2. **networkId** (Network domain)
   - Unique per network request
   - Persists across redirects
   - Used for tracking

3. **loaderId**
   - Unique per page load
   - Groups related requests

4. **frameId**
   - Identifies which frame made request
   - Important for iframes

### Error Handling in CDP

**Connection errors:**

- WebSocket disconnect → All pending requests auto-continue
- Timeout (30s default) → Request auto-continues
- Invalid JSON → Connection closed

**Protocol errors:**

```json
{
  "id": 1,
  "error": {
    "code": -32602,
    "message": "Invalid params",
    "data": "requestId is required"
  }
}
```

**Common error codes:**

- -32700: Parse error
- -32600: Invalid request
- -32601: Method not found
- -32602: Invalid params
- -32603: Internal error

### CDP Sessions

For multi-target scenarios (multiple pages/frames):

```
Browser
  ├─ Page 1 (sessionId: "session1")
  │   ├─ Frame 1.1
  │   └─ Frame 1.2
  └─ Page 2 (sessionId: "session2")
      └─ Frame 2.1
```

Each session has independent:

- Fetch.enable state
- Route handlers
- Request interception

### Performance Considerations

**Message overhead:**

- Average CDP message: 500-2000 bytes
- Serialization: ~0.1-0.5ms
- WebSocket latency: ~1-5ms
- Total per request: ~2-10ms overhead

**Optimization strategies:**

- Batch enable/disable operations
- Use specific URL patterns (not `*`)
- Minimize message size (don't send unnecessary data)

---

## Layer 3: Playwright Protocol Translation

### Playwright's Abstraction Layer

Playwright provides a unified API across browsers:

```typescript
// User writes this (same for all browsers)
await page.route("**/api/**", (route) => {
  route.fulfill({ json: { data: "mocked" } });
});

// Playwright translates to:
// - CDP (Chromium)
// - Juggler (Firefox)
// - WebKit Inspector Protocol (WebKit)
```

### Protocol Dispatcher Architecture

```
┌─────────────────────────────────────────────────────────┐
│              Playwright Server (Node.js)                │
│                                                         │
│  ┌───────────────────────────────────────────────┐    │
│  │         Connection (WebSocket/Pipe)           │    │
│  └─────────────────┬─────────────────────────────┘    │
│                    │                                    │
│  ┌─────────────────▼─────────────────────────────┐    │
│  │         Protocol Dispatcher                   │    │
│  │  - Message routing                            │    │
│  │  - ID generation                              │    │
│  │  - Response correlation                       │    │
│  └─────────────────┬─────────────────────────────┘    │
│                    │                                    │
│         ┌──────────┼──────────┐                        │
│         │          │          │                        │
│  ┌──────▼────┐ ┌──▼─────┐ ┌─▼────────┐               │
│  │   CDP     │ │Juggler │ │ WebKit   │               │
│  │ Adapter   │ │Adapter │ │ Adapter  │               │
│  └──────┬────┘ └──┬─────┘ └─┬────────┘               │
│         │         │          │                        │
└─────────┼─────────┼──────────┼────────────────────────┘
          │         │          │
          ↓         ↓          ↓
      Chromium   Firefox    WebKit
```

### Route Registry Implementation

**Data Structure (conceptual):**

```typescript
class RouteRegistry {
  private routes: Route[] = [];

  register(pattern: string | RegExp, handler: RouteHandler): void {
    // Routes are stored in LIFO order
    this.routes.unshift({
      pattern: this.compilePattern(pattern),
      handler: handler,
      id: generateId(),
    });
  }

  async match(request: Request): Promise<RouteHandler | null> {
    // Linear search, first match wins
    for (const route of this.routes) {
      if (route.pattern.test(request.url())) {
        return route.handler;
      }
    }
    return null;
  }

  unregister(pattern: string | RegExp, handler?: RouteHandler): void {
    this.routes = this.routes.filter((route) => {
      if (handler) {
        return !(route.pattern.matches(pattern) && route.handler === handler);
      }
      return !route.pattern.matches(pattern);
    });
  }
}
```

**Pattern Compilation:**

```typescript
function compilePattern(pattern: string | RegExp | Function): Matcher {
  if (pattern instanceof RegExp) {
    return {
      test: (url: string) => pattern.test(url),
    };
  }

  if (typeof pattern === "function") {
    return {
      test: (url: string) => pattern(url),
    };
  }

  // Glob pattern
  const regex = globToRegex(pattern);
  return {
    test: (url: string) => regex.test(url),
  };
}

function globToRegex(glob: string): RegExp {
  // ** matches any characters including /
  // * matches any characters except /
  // ? matches single character

  let regex = glob
    .replace(/\*\*/g, "___DOUBLE_STAR___")
    .replace(/\*/g, "[^/]*")
    .replace(/___DOUBLE_STAR___/g, ".*")
    .replace(/\?/g, ".");

  return new RegExp("^" + regex + "$");
}
```

### Request Object Abstraction

Playwright creates a unified Request object:

```typescript
class Request {
  private _cdpRequest?: CDPRequest;
  private _jugglerRequest?: JugglerRequest;
  private _wkRequest?: WKRequest;

  url(): string {
    if (this._cdpRequest) {
      return this._cdpRequest.request.url;
    }
    if (this._jugglerRequest) {
      return this._jugglerRequest.url;
    }
    if (this._wkRequest) {
      return this._wkRequest.request.url;
    }
  }

  method(): string {
    // Similar abstraction for each browser
  }

  headers(): Record<string, string> {
    // Headers normalization across browsers
    if (this._cdpRequest) {
      return this._cdpRequest.request.headers;
    }
    // Firefox and WebKit have different formats
  }

  postData(): string | null {
    // POST data extraction
  }

  resourceType(): string {
    // Normalize resource types across browsers
    // CDP: "Document", "XHR", "Fetch", etc.
    // Juggler: "document", "xhr", "fetch", etc.
    // WebKit: Different naming
  }
}
```

### Route Handler Execution

```typescript
class Route {
  private _handled = false;
  private _request: Request;
  private _connection: Connection;

  async continue(overrides?: {
    url?: string;
    method?: string;
    headers?: Record<string, string>;
    postData?: string;
  }): Promise<void> {
    if (this._handled) {
      throw new Error("Route already handled");
    }
    this._handled = true;

    // Translate to browser-specific protocol
    if (this._connection.isCDP()) {
      await this._connection.send("Fetch.continueRequest", {
        requestId: this._request._cdpRequestId,
        url: overrides?.url,
        method: overrides?.method,
        headers: this._headersToArray(overrides?.headers),
        postData: overrides?.postData
          ? Buffer.from(overrides.postData).toString("base64")
          : undefined,
      });
    } else if (this._connection.isJuggler()) {
      // Juggler-specific implementation
    } else {
      // WebKit-specific implementation
    }
  }

  async fulfill(response: {
    status?: number;
    headers?: Record<string, string>;
    body?: string | Buffer;
    json?: any;
  }): Promise<void> {
    if (this._handled) {
      throw new Error("Route already handled");
    }
    this._handled = true;

    let body: Buffer;
    let headers = response.headers || {};

    if (response.json !== undefined) {
      body = Buffer.from(JSON.stringify(response.json));
      headers["content-type"] = "application/json";
    } else if (response.body) {
      body = Buffer.isBuffer(response.body)
        ? response.body
        : Buffer.from(response.body);
    } else {
      body = Buffer.from("");
    }

    if (this._connection.isCDP()) {
      await this._connection.send("Fetch.fulfillRequest", {
        requestId: this._request._cdpRequestId,
        responseCode: response.status || 200,
        responseHeaders: this._headersToArray(headers),
        body: body.toString("base64"),
      });
    }
    // Similar for other browsers
  }

  async abort(errorCode?: string): Promise<void> {
    if (this._handled) {
      throw new Error("Route already handled");
    }
    this._handled = true;

    if (this._connection.isCDP()) {
      await this._connection.send("Fetch.failRequest", {
        requestId: this._request._cdpRequestId,
        errorReason: errorCode || "Failed",
      });
    }
    // Similar for other browsers
  }
}
```

### Browser-Specific Adapters

**CDP Adapter:**

```typescript
class CDPNetworkManager {
  async enable(): Promise<void> {
    await this._connection.send("Fetch.enable", {
      patterns: [{ urlPattern: "*" }],
    });

    this._connection.on(
      "Fetch.requestPaused",
      this._onRequestPaused.bind(this),
    );
  }

  private async _onRequestPaused(event: CDPRequestPausedEvent): Promise<void> {
    const request = new Request(event);
    const route = new Route(request, this._connection);

    const handler = await this._routeRegistry.match(request);

    if (handler) {
      try {
        await handler(route, request);
      } catch (error) {
        // On error, auto-continue
        if (!route._handled) {
          await route.continue();
        }
      }
    } else {
      // No handler matched, auto-continue
      await route.continue();
    }
  }
}
```

**Juggler Adapter:**

```typescript
class JugglerNetworkManager {
  async enable(): Promise<void> {
    await this._connection.send("Network.enable", {});

    this._connection.on(
      "Network.requestWillBeSent",
      this._onRequestWillBeSent.bind(this),
    );
  }

  private async _onRequestWillBeSent(
    event: JugglerRequestEvent,
  ): Promise<void> {
    // Similar to CDP but with Juggler-specific protocol
  }
}
```

---

## Layer 4: Request Lifecycle & State Machines

### Request State Machine

Each intercepted request goes through a state machine:

```
                    ┌─────────────┐
                    │   CREATED   │
                    └──────┬──────┘
                           │
                           ↓
                    ┌─────────────┐
                    │ INTERCEPTED │
                    └──────┬──────┘
                           │
              ┌────────────┼────────────┐
              │            │            │
              ↓            ↓            ↓
       ┌──────────┐ ┌──────────┐ ┌──────────┐
       │CONTINUED │ │FULFILLED │ │ ABORTED  │
       └────┬─────┘ └────┬─────┘ └────┬─────┘
            │            │            │
            └────────────┼────────────┘
                         ↓
                  ┌─────────────┐
                  │  COMPLETED  │
                  └─────────────┘
```

**State Transitions:**

1. **CREATED → INTERCEPTED**
   - Triggered by: Browser initiates request
   - Action: Fetch.requestPaused event fired
   - Duration: Immediate

2. **INTERCEPTED → CONTINUED**
   - Triggered by: `route.continue()` called
   - Action: Fetch.continueRequest sent
   - Duration: ~1-5ms (IPC latency)

3. **INTERCEPTED → FULFILLED**
   - Triggered by: `route.fulfill()` called
   - Action: Fetch.fulfillRequest sent
   - Duration: ~1-5ms (IPC latency)

4. **INTERCEPTED → ABORTED**
   - Triggered by: `route.abort()` called
   - Action: Fetch.failRequest sent
   - Duration: ~1-5ms (IPC latency)

5. **{CONTINUED|FULFILLED|ABORTED} → COMPLETED**
   - Triggered by: Browser processes response
   - Action: Cleanup internal state
   - Duration: Immediate

### Timeout Handling

Each intercepted request has a timeout (default 30 seconds):

```typescript
class InterceptedRequest {
  private _timeoutId: NodeJS.Timeout;

  constructor() {
    this._timeoutId = setTimeout(() => {
      if (!this._handled) {
        console.warn(`Request timeout: ${this._request.url()}`);
        this.continue().catch(() => {});
      }
    }, 30000);
  }

  private _clearTimeout(): void {
    clearTimeout(this._timeoutId);
  }

  async continue(): Promise<void> {
    this._clearTimeout();
    // ... rest of implementation
  }
}
```

**Why timeout is necessary:**

- Prevents deadlocks if handler never responds
- Ensures browser doesn't hang indefinitely
- Fail-safe mechanism

### Redirect Handling

HTTP redirects create multiple requests:

```
Original Request (GET /old)
         ↓
    [INTERCEPTED]
         ↓
    route.continue()
         ↓
    Server responds: 302 → /new
         ↓
    New Request (GET /new)
         ↓
    [INTERCEPTED AGAIN]
         ↓
    route.fulfill()
```

**Important:** Each redirect creates a new interception event. You must handle each one.

**Example:**

```typescript
let redirectCount = 0;

await page.route("**/*", (route) => {
  if (route.request().isNavigationRequest()) {
    redirectCount++;
    console.log(`Redirect #${redirectCount}: ${route.request().url()}`);
  }
  route.continue();
});
```

### Request Priority

Browsers assign priority to requests:

- **Highest:** Main document
- **High:** CSS, Fonts
- **Medium:** Scripts, XHR/Fetch
- **Low:** Images
- **Lowest:** Prefetch

Playwright preserves priority when continuing requests.

### Resource Type Detection

Browsers classify requests by type:

**Chromium types:**

- Document, Stylesheet, Image, Media, Font, Script, TextTrack, XHR, Fetch, EventSource, WebSocket, Manifest, SignedExchange, Ping, CSPViolationReport, Preflight, Other

**Playwright normalization:**

```typescript
function normalizeResourceType(cdpType: string): string {
  const mapping = {
    Document: "document",
    Stylesheet: "stylesheet",
    Image: "image",
    Media: "media",
    Font: "font",
    Script: "script",
    XHR: "xhr",
    Fetch: "fetch",
    // ... etc
  };
  return mapping[cdpType] || "other";
}
```

### Frame Context

Requests are associated with frames:

```
Page
 ├─ Main Frame (frameId: "frame1")
 │   ├─ Request 1 (document)
 │   ├─ Request 2 (script)
 │   └─ Request 3 (xhr)
 │
 └─ Child Frame (frameId: "frame2")
     ├─ Request 4 (document)
     └─ Request 5 (image)
```

**Accessing frame info:**

```typescript
await page.route("**/*", (route) => {
  const frame = route.request().frame();
  console.log(`Frame URL: ${frame.url()}`);
  console.log(`Is main frame: ${frame === page.mainFrame()}`);
  route.continue();
});
```

---

## Layer 5: Memory Management & Data Structures

### Request Buffer Management

When intercepting requests, data must be buffered in memory:

```
┌─────────────────────────────────────────────────────┐
│              Browser Process Memory                 │
│                                                     │
│  Request Headers: ~2KB                             │
│  Request Body: Variable (0 - 100MB+)               │
│                                                     │
└────────────────┬────────────────────────────────────┘
                 │ Serialized via CDP
                 ↓
┌─────────────────────────────────────────────────────┐
│           Playwright Server Memory                  │
│                                                     │
│  Request Object: ~5KB                              │
│  Request Body (if accessed): Variable              │
│  Response Body (if fulfilled): Variable            │
│                                                     │
└─────────────────────────────────────────────────────┘
```

### Memory Considerations

**Large POST requests:**

```typescript
// Uploading 100MB file
await page.route("**/upload", async (route) => {
  const postData = route.request().postData();
  // postData is now 100MB in memory!
  // This can cause memory pressure

  await route.continue();
});
```

**Mitigation strategies:**

1. Don't access `postData()` unless necessary
2. Use streaming for large uploads (not supported in interception)
3. Increase Node.js heap size: `node --max-old-space-size=4096`

**Response buffering:**

```typescript
await page.route("**/api", (route) => {
  route.fulfill({
    body: Buffer.alloc(50 * 1024 * 1024), // 50MB response
  });
  // This 50MB is held in memory until browser receives it
});
```

### Data Structure Internals

**Route Registry (detailed):**

```typescript
interface RouteEntry {
  id: string; // Unique ID
  pattern: CompiledPattern; // Compiled glob/regex
  handler: RouteHandler; // User function
  times?: number; // For route.once()
  context?: BrowserContext; // Scope
}

class RouteRegistry {
  private _routes: RouteEntry[] = [];
  private _lock: AsyncLock = new AsyncLock();

  async handle(request: Request): Promise<void> {
    // Acquire lock to prevent race conditions
    await this._lock.acquire("handle", async () => {
      for (const entry of this._routes) {
        if (entry.pattern.test(request.url())) {
          // Decrement times if specified
          if (entry.times !== undefined) {
            entry.times--;
            if (entry.times === 0) {
              this._remove(entry.id);
            }
          }

          const route = new Route(request);
          await entry.handler(route, request);
          return;
        }
      }

      // No match, auto-continue
      await request._continue();
    });
  }
}
```

**Request Tracking:**

```typescript
class NetworkManager {
  private _requests: Map<string, Request> = new Map();
  private _requestIdToRoute: Map<string, Route> = new Map();

  _onRequestPaused(event: CDPRequestPausedEvent): void {
    const requestId = event.requestId;
    const request = new Request(event);

    this._requests.set(requestId, request);

    // Create route and store
    const route = new Route(request, this._connection);
    this._requestIdToRoute.set(requestId, route);

    // Handle async
    this._handleRequest(route, request).catch((error) => {
      console.error("Route handler error:", error);
      // Auto-continue on error
      if (!route._handled) {
        route.continue().catch(() => {});
      }
    });
  }

  _onRequestFinished(requestId: string): void {
    // Cleanup
    this._requests.delete(requestId);
    this._requestIdToRoute.delete(requestId);
  }
}
```

### Garbage Collection Implications

**Memory leaks to avoid:**

```typescript
// BAD: Storing requests indefinitely
const allRequests = [];
await page.route("**/*", (route) => {
  allRequests.push(route.request()); // Memory leak!
  route.continue();
});

// GOOD: Let Playwright manage lifecycle
await page.route("**/*", (route) => {
  console.log(route.request().url());
  route.continue();
  // Request object can be GC'd after handler completes
});
```

**Weak references:**

Playwright uses WeakMaps internally to avoid memory leaks:

```typescript
class Page {
  private _requestToFrame: WeakMap<Request, Frame> = new WeakMap();

  _onRequest(request: Request, frame: Frame): void {
    this._requestToFrame.set(request, frame);
    // When request is GC'd, entry is automatically removed
  }
}
```

### Buffer Pooling

For performance, Playwright may use buffer pools:

```typescript
class BufferPool {
  private _pool: Buffer[] = [];
  private _maxSize = 100;

  acquire(size: number): Buffer {
    // Try to reuse existing buffer
    for (let i = 0; i < this._pool.length; i++) {
      if (this._pool[i].length >= size) {
        return this._pool.splice(i, 1)[0].slice(0, size);
      }
    }
    // Allocate new buffer
    return Buffer.allocUnsafe(size);
  }

  release(buffer: Buffer): void {
    if (this._pool.length < this._maxSize) {
      this._pool.push(buffer);
    }
    // Otherwise let it be GC'd
  }
}
```

---

## Layer 6: Concurrency & Synchronization

### Threading Model

**Node.js (single-threaded event loop):**

```
┌─────────────────────────────────────────────────┐
│            Node.js Event Loop                   │
│                                                 │
│  ┌──────────────────────────────────────┐      │
│  │  Timers Phase                        │      │
│  │  - setTimeout/setInterval callbacks  │      │
│  └──────────────────────────────────────┘      │
│                                                 │
│  ┌──────────────────────────────────────┐      │
│  │  Pending Callbacks Phase             │      │
│  │  - I/O callbacks                     │      │
│  └──────────────────────────────────────┘      │
│                                                 │
│  ┌──────────────────────────────────────┐      │
│  │  Poll Phase                          │      │
│  │  - Retrieve new I/O events           │      │
│  │  - Execute I/O callbacks             │      │
│  │  - [Route handlers execute here]     │      │
│  └──────────────────────────────────────┘      │
│                                                 │
│  ┌──────────────────────────────────────┐      │
│  │  Check Phase                         │      │
│  │  - setImmediate callbacks            │      │
│  └──────────────────────────────────────┘      │
│                                                 │
│  ┌──────────────────────────────────────┐      │
│  │  Close Callbacks Phase               │      │
│  │  - socket.on('close', ...)           │      │
│  └──────────────────────────────────────┘      │
└─────────────────────────────────────────────────┘
```

**Implications:**

- Route handlers run sequentially (not parallel)
- Long-running handler blocks other handlers
- Async operations yield to event loop

### Concurrent Requests

Multiple requests can be intercepted simultaneously:

```
Time →
  0ms: Request A intercepted → Handler A starts
  5ms: Request B intercepted → Queued (Handler A still running)
 10ms: Handler A completes → Handler B starts
 15ms: Request C intercepted → Queued
 20ms: Handler B completes → Handler C starts
```

**Example:**

```typescript
await page.route("**/*", async (route) => {
  console.log("Start:", route.request().url());
  await new Promise((resolve) => setTimeout(resolve, 100)); // Simulate slow handler
  console.log("End:", route.request().url());
  await route.continue();
});

// Navigate to page with 10 resources
await page.goto("https://example.com");

// Output:
// Start: https://example.com/
// End: https://example.com/
// Start: https://example.com/style.css
// End: https://example.com/style.css
// ... (sequential, not parallel)
```

### Race Conditions

**Scenario 1: Multiple handlers for same request**

```typescript
// This is safe - only first matching handler runs
await page.route("**/api", (route) => {
  console.log("Handler 1");
  route.fulfill({ json: { source: "handler1" } });
});

await page.route("**/api", (route) => {
  console.log("Handler 2"); // Never runs
  route.fulfill({ json: { source: "handler2" } });
});

// Only Handler 2 runs (last registered = first matched)
```

**Scenario 2: Calling route methods multiple times**

```typescript
await page.route("**/*", async (route) => {
  await route.continue();
  await route.fulfill({ body: "test" }); // Error: already handled
});
```

**Protection mechanism:**

```typescript
class Route {
  private _handled = false;
  private _lock = new AsyncLock();

  async continue(): Promise<void> {
    await this._lock.acquire("handle", async () => {
      if (this._handled) {
        throw new Error("Route already handled");
      }
      this._handled = true;
      await this._actualContinue();
    });
  }
}
```

### Deadlock Prevention

**Potential deadlock:**

```typescript
// BAD: Handler waits for another request
await page.route("**/api/users", async (route) => {
  // This creates a deadlock if /api/users calls /api/auth
  const response = await page.request.get("https://api.example.com/api/auth");
  await route.fulfill({ json: response.json() });
});

await page.route("**/api/auth", async (route) => {
  // This handler never runs because event loop is blocked
  await route.fulfill({ json: { token: "abc" } });
});
```

**Solution: Use route.fetch()**

```typescript
await page.route("**/api/users", async (route) => {
  // route.fetch() bypasses interception
  const response = await route.fetch();
  const json = await response.json();
  await route.fulfill({ json });
});
```

### Async Handler Execution

```typescript
class NetworkManager {
  private _pendingHandlers: Set<Promise<void>> = new Set();

  async _handleRequest(route: Route, request: Request): Promise<void> {
    const handler = this._routeRegistry.match(request);

    if (handler) {
      const promise = this._executeHandler(handler, route, request);
      this._pendingHandlers.add(promise);

      promise.finally(() => {
        this._pendingHandlers.delete(promise);
      });

      await promise;
    } else {
      await route.continue();
    }
  }

  async _executeHandler(
    handler: RouteHandler,
    route: Route,
    request: Request,
  ): Promise<void> {
    try {
      await handler(route, request);
    } catch (error) {
      console.error("Handler error:", error);
      if (!route._handled) {
        await route.continue();
      }
    }
  }

  async waitForPendingHandlers(): Promise<void> {
    await Promise.all(Array.from(this._pendingHandlers));
  }
}
```

### Browser-Side Concurrency

The browser's network service is multi-threaded:

```
Network Service Process
  ├─ Network Thread 1 (handles requests 1-10)
  ├─ Network Thread 2 (handles requests 11-20)
  ├─ Network Thread 3 (handles requests 21-30)
  └─ ...
```

**But interception is serialized:**

- All Fetch.requestPaused events go through single CDP connection
- Playwright processes them sequentially
- This is a bottleneck for high-traffic scenarios

### Performance Under Load

**Benchmark scenario: 100 concurrent requests**

```typescript
// Without interception
await page.goto("https://example.com"); // ~500ms

// With interception (no-op handler)
await page.route("**/*", (route) => route.continue());
await page.goto("https://example.com"); // ~600ms (+20%)

// With interception (slow handler)
await page.route("**/*", async (route) => {
  await new Promise((resolve) => setTimeout(resolve, 10));
  await route.continue();
});
await page.goto("https://example.com"); // ~1500ms (+200%)
```

**Optimization: Selective interception**

```typescript
// Only intercept API calls, not static resources
await page.route("**/api/**", handler);
// Images, CSS, JS not intercepted → faster
```

---

## Layer 7: Inter-Process Communication

### IPC Mechanisms

Playwright uses different IPC mechanisms depending on the scenario:

**1. WebSocket (default for remote browsers)**

```
Test Process ←─ WebSocket ─→ Playwright Server ←─ WebSocket ─→ Browser
```

**2. Stdio (for local browsers)**

```
Test Process ←─ Pipe ─→ Playwright Server ←─ Pipe ─→ Browser
```

**3. Unix Domain Sockets (alternative)**

```
Test Process ←─ UDS ─→ Playwright Server ←─ UDS ─→ Browser
```

### WebSocket Protocol

**Connection establishment:**

```
Client                          Server
  │                               │
  │  HTTP GET /ws                 │
  ├──────────────────────────────>│
  │  Upgrade: websocket           │
  │  Connection: Upgrade          │
  │                               │
  │  HTTP 101 Switching Protocols │
  │<──────────────────────────────┤
  │                               │
  │  [WebSocket connection open]  │
  │                               │
  │  {"method": "Fetch.enable"}   │
  ├──────────────────────────────>│
  │                               │
  │  {"id": 1, "result": {}}      │
  │<──────────────────────────────┤
```

**Message framing:**

```
┌─────────────────────────────────────────────┐
│  WebSocket Frame                            │
│  ┌───────────────────────────────────────┐ │
│  │  FIN: 1 (final fragment)              │ │
│  │  Opcode: 1 (text frame)               │ │
│  │  Mask: 1 (client-to-server)           │ │
│  │  Payload length: 256                  │ │
│  │  Masking key: 0x12345678              │ │
│  │  Payload: {"method":"Fetch.enable"}   │ │
│  └───────────────────────────────────────┘ │
└─────────────────────────────────────────────┘
```

### Stdio Protocol

For local browsers, Playwright uses stdio pipes:

```typescript
// Launching browser with stdio
const browser = spawn(
  "chromium",
  [
    "--remote-debugging-pipe",
    // ... other args
  ],
  {
    stdio: ["pipe", "pipe", "pipe", "pipe", "pipe"],
    //      stdin  stdout stderr  fd3    fd4
    //                            ↑      ↑
    //                            CDP    CDP
  },
);

// Reading from browser
browser.stdio[3].on("data", (data) => {
  const message = JSON.parse(data.toString());
  handleCDPMessage(message);
});

// Writing to browser
const message = JSON.stringify({
  id: 1,
  method: "Fetch.enable",
  params: {},
});
browser.stdio[4].write(message + "\0"); // Null-terminated
```

**Advantages of stdio:**

- Lower latency than WebSocket (~0.1ms vs ~1ms)
- No TCP overhead
- Direct kernel pipe
- Better for local testing

**Disadvantages:**

- Only works for local browsers
- No standard framing (must implement own protocol)
- Harder to debug (can't use browser DevTools)

### Message Serialization

**JSON serialization overhead:**

```typescript
const message = {
  id: 1,
  method: "Fetch.fulfillRequest",
  params: {
    requestId: "interceptionId.123",
    responseCode: 200,
    responseHeaders: [
      { name: "Content-Type", value: "application/json" },
      { name: "Content-Length", value: "1024" },
    ],
    body: "base64EncodedData...", // Could be large
  },
};

// Serialization
const start = performance.now();
const json = JSON.stringify(message);
const end = performance.now();
console.log(`Serialization took ${end - start}ms`); // ~0.1-1ms

// Size
console.log(`Message size: ${json.length} bytes`); // ~2KB typical
```

**Binary data handling:**

```typescript
// Request body (binary)
const postData = Buffer.from([0x89, 0x50, 0x4E, 0x47, ...]); // PNG image

// Must base64 encode for JSON
const base64 = postData.toString('base64');
// Size increases by ~33%

// Send via CDP
await connection.send('Fetch.continueRequest', {
  requestId: '123',
  postData: base64
});

// Browser decodes base64 back to binary
```

### Flow Control

**Backpressure handling:**

```typescript
class Connection {
  private _sendQueue: Message[] = [];
  private _sending = false;

  async send(method: string, params?: object): Promise<any> {
    const message = {
      id: this._nextId++,
      method,
      params,
    };

    return new Promise((resolve, reject) => {
      this._sendQueue.push({
        message,
        resolve,
        reject,
      });

      this._processSendQueue();
    });
  }

  private async _processSendQueue(): Promise<void> {
    if (this._sending || this._sendQueue.length === 0) {
      return;
    }

    this._sending = true;

    while (this._sendQueue.length > 0) {
      const { message, resolve, reject } = this._sendQueue.shift()!;

      try {
        const json = JSON.stringify(message);

        // Check if socket is writable
        if (!this._socket.writable) {
          await new Promise((r) => this._socket.once("drain", r));
        }

        this._socket.write(json);

        // Wait for response
        const response = await this._waitForResponse(message.id);
        resolve(response);
      } catch (error) {
        reject(error);
      }
    }

    this._sending = false;
  }
}
```

### Connection Resilience

**Reconnection logic:**

```typescript
class ResilientConnection {
  private _reconnectAttempts = 0;
  private _maxReconnectAttempts = 3;

  async connect(): Promise<void> {
    try {
      await this._doConnect();
      this._reconnectAttempts = 0;
    } catch (error) {
      if (this._reconnectAttempts < this._maxReconnectAttempts) {
        this._reconnectAttempts++;
        const delay = Math.min(
          1000 * Math.pow(2, this._reconnectAttempts),
          10000,
        );
        console.log(`Reconnecting in ${delay}ms...`);
        await new Promise((resolve) => setTimeout(resolve, delay));
        return this.connect();
      }
      throw error;
    }
  }

  private _onDisconnect(): void {
    console.log("Connection lost, attempting reconnect...");
    this.connect().catch((error) => {
      console.error("Failed to reconnect:", error);
      this._cleanup();
    });
  }
}
```

---

## Layer 8: Performance Analysis

### Latency Breakdown

**Total request interception latency:**

```
Component                           Latency
─────────────────────────────────────────────
Browser detects request             0ms
Browser pauses request              0.1ms
CDP event serialization             0.2ms
WebSocket transmission              1-5ms
Playwright receives event           0.1ms
Route pattern matching              0.1-1ms
User handler execution              Variable (0-1000ms+)
Response serialization              0.2ms
WebSocket transmission              1-5ms
Browser receives response           0.1ms
Browser processes response          0.5ms
─────────────────────────────────────────────
TOTAL (excluding handler)           3-12ms
TOTAL (with fast handler)           3-15ms
TOTAL (with slow handler)           3-1012ms+
```

### Throughput Analysis

**Maximum requests per second:**

```
Scenario                    RPS     Notes
──────────────────────────────────────────────
No interception             1000+   Limited by network
Interception (no-op)        500     Limited by IPC
Interception (10ms handler) 100     Limited by handler
Interception (100ms handler) 10     Limited by handler
```

**Bottlenecks:**

1. **Sequential handler execution** (biggest bottleneck)
2. IPC latency (WebSocket/pipe)
3. JSON serialization/deserialization
4. Pattern matching (linear search)

### Memory Profiling

**Memory usage per intercepted request:**

```
Component                   Memory
──────────────────────────────────────
Request object              ~5KB
Request headers             ~2KB
Request body (if accessed)  Variable
Response body (if fulfilled) Variable
Route object                ~3KB
Internal bookkeeping        ~2KB
──────────────────────────────────────
TOTAL (minimal)             ~12KB
TOTAL (with 1MB body)       ~1.01MB
```

**Memory usage for 100 concurrent requests:**

- Minimal: ~1.2MB
- With average bodies (10KB): ~2.2MB
- With large bodies (1MB): ~101MB

### CPU Profiling

**CPU time per request:**

```
Operation                   CPU Time
────────────────────────────────────────
Pattern matching            0.1-1ms
JSON serialization          0.2-0.5ms
JSON deserialization        0.2-0.5ms
Handler execution           Variable
Base64 encoding/decoding    0.1-1ms (for bodies)
────────────────────────────────────────
TOTAL (excluding handler)   0.7-3.5ms
```

### Optimization Techniques

**1. Minimize route patterns:**

```typescript
// BAD: Intercepts everything
await page.route("**/*", handler);

// GOOD: Specific patterns
await page.route("**/api/**", handler);
```

**2. Use route.once() for single-use routes:**

```typescript
// Automatically unregisters after first match
await page.route("**/login", handler, { times: 1 });
```

**3. Unregister routes when done:**

```typescript
const handler = (route) => route.fulfill({ json: mockData });
await page.route("**/api", handler);

// Later...
await page.unroute("**/api", handler);
```

**4. Avoid accessing request body unnecessarily:**

```typescript
// BAD: Always accesses body
await page.route("**/*", (route) => {
  const body = route.request().postData(); // Expensive!
  route.continue();
});

// GOOD: Only access when needed
await page.route("**/api", (route) => {
  if (route.request().method() === "POST") {
    const body = route.request().postData();
    // Process body...
  }
  route.continue();
});
```

**5. Use context-level routes for global patterns:**

```typescript
// Applies to all pages in context
await context.route("**/*.{png,jpg}", (route) => route.abort());
```

### Benchmarking Example

```typescript
async function benchmark() {
  const iterations = 100;
  const times: number[] = [];

  await page.route("**/api/test", (route) => {
    route.fulfill({ json: { data: "test" } });
  });

  for (let i = 0; i < iterations; i++) {
    const start = performance.now();
    await page.evaluate(() => fetch("/api/test"));
    const end = performance.now();
    times.push(end - start);
  }

  const avg = times.reduce((a, b) => a + b) / times.length;
  const min = Math.min(...times);
  const max = Math.max(...times);
  const p95 = times.sort()[Math.floor(times.length * 0.95)];

  console.log(`Average: ${avg.toFixed(2)}ms`);
  console.log(`Min: ${min.toFixed(2)}ms`);
  console.log(`Max: ${max.toFixed(2)}ms`);
  console.log(`P95: ${p95.toFixed(2)}ms`);
}
```

**Typical results:**

```
Average: 8.45ms
Min: 5.23ms
Max: 15.67ms
P95: 12.34ms
```

---

## Layer 9: HAR File Implementation

### HAR Format Overview

HTTP Archive (HAR) is a JSON format for recording HTTP transactions:

```json
{
  "log": {
    "version": "1.2",
    "creator": {
      "name": "Playwright",
      "version": "1.40.0"
    },
    "entries": [
      {
        "startedDateTime": "2026-01-06T10:30:00.000Z",
        "time": 150,
        "request": {
          "method": "GET",
          "url": "https://api.example.com/users",
          "httpVersion": "HTTP/1.1",
          "headers": [
            { "name": "Accept", "value": "application/json" },
            { "name": "User-Agent", "value": "Mozilla/5.0..." }
          ],
          "queryString": [
            { "name": "page", "value": "1" },
            { "name": "limit", "value": "10" }
          ],
          "cookies": [],
          "headersSize": 256,
          "bodySize": 0
        },
        "response": {
          "status": 200,
          "statusText": "OK",
          "httpVersion": "HTTP/1.1",
          "headers": [
            { "name": "Content-Type", "value": "application/json" },
            { "name": "Content-Length", "value": "1024" }
          ],
          "cookies": [],
          "content": {
            "size": 1024,
            "mimeType": "application/json",
            "text": "{\"users\":[...]}"
          },
          "redirectURL": "",
          "headersSize": 256,
          "bodySize": 1024
        },
        "cache": {},
        "timings": {
          "blocked": 0,
          "dns": 10,
          "connect": 20,
          "send": 5,
          "wait": 100,
          "receive": 15,
          "ssl": 30
        }
      }
    ]
  }
}
```

### HAR-based Stubbing

Playwright can use HAR files for stubbing:

```typescript
// Record HAR
await page.routeFromHAR("./recordings/api.har", {
  url: "**/api/**",
  update: true, // Record mode
});

await page.goto("https://example.com");
// All API requests are recorded to api.har

// Replay HAR
await page.routeFromHAR("./recordings/api.har", {
  url: "**/api/**",
  update: false, // Replay mode
});

await page.goto("https://example.com");
// All API requests are served from api.har
```

### HAR Index Structure

Playwright builds an in-memory index for fast lookup:

```typescript
interface HAREntry {
  request: {
    method: string;
    url: string;
    headers: Array<{ name: string; value: string }>;
    postData?: {
      mimeType: string;
      text: string;
    };
  };
  response: {
    status: number;
    headers: Array<{ name: string; value: string }>;
    content: {
      text?: string;
      encoding?: string;
    };
  };
}

class HARRouter {
  private _entries: Map<string, HAREntry[]> = new Map();

  constructor(harPath: string) {
    const har = JSON.parse(fs.readFileSync(harPath, "utf-8"));

    for (const entry of har.log.entries) {
      const key = this._makeKey(entry.request);

      if (!this._entries.has(key)) {
        this._entries.set(key, []);
      }

      this._entries.get(key)!.push(entry);
    }
  }

  private _makeKey(request: any): string {
    // Key includes method, URL, and optionally body
    const url = new URL(request.url);
    const key = `${request.method}:${url.origin}${url.pathname}`;

    // Include query params in key
    const params = Array.from(url.searchParams.entries())
      .sort()
      .map(([k, v]) => `${k}=${v}`)
      .join("&");

    return params ? `${key}?${params}` : key;
  }

  find(request: Request): HAREntry | null {
    const key = this._makeKey({
      method: request.method(),
      url: request.url(),
    });

    const entries = this._entries.get(key);
    if (!entries || entries.length === 0) {
      return null;
    }

    // Return first match (or implement more sophisticated matching)
    return entries[0];
  }
}
```

### HAR Matching Strategies

**1. Exact URL match:**

```typescript
// Matches only exact URL
const entry = harRouter.find(request);
```

**2. URL pattern match:**

```typescript
// Matches URL pattern
if (minimatch(request.url(), "**/api/users/*")) {
  const entry = harRouter.find(request);
}
```

**3. Method + URL match:**

```typescript
// Matches method and URL
const key = `${request.method()}:${request.url()}`;
```

**4. Body-aware match:**

```typescript
// Matches method, URL, and POST body
const postData = request.postData();
const key = `${request.method()}:${request.url()}:${hash(postData)}`;
```

### HAR Update Mode

When `update: true`, Playwright records missing entries:

```typescript
class HARRouter {
  private _updateMode: boolean;
  private _harPath: string;
  private _modified = false;

  async handle(route: Route, request: Request): Promise<void> {
    const entry = this.find(request);

    if (entry) {
      // Found in HAR, use it
      await route.fulfill({
        status: entry.response.status,
        headers: this._headersToObject(entry.response.headers),
        body: this._decodeBody(entry.response.content),
      });
    } else if (this._updateMode) {
      // Not found, make real request and record
      const response = await route.fetch();

      const newEntry = await this._createEntry(request, response);
      this._addEntry(newEntry);
      this._modified = true;

      await route.fulfill({
        status: response.status(),
        headers: await response.allHeaders(),
        body: await response.body(),
      });
    } else {
      // Not found, not in update mode
      throw new Error(`No HAR entry found for ${request.url()}`);
    }
  }

  async save(): Promise<void> {
    if (this._modified) {
      const har = this._buildHAR();
      await fs.promises.writeFile(this._harPath, JSON.stringify(har, null, 2));
    }
  }
}
```

### HAR Content Encoding

Response bodies may be encoded:

```typescript
function decodeBody(content: HARContent): Buffer {
  let text = content.text || "";

  if (content.encoding === "base64") {
    return Buffer.from(text, "base64");
  }

  return Buffer.from(text, "utf-8");
}

function encodeBody(body: Buffer, mimeType: string): HARContent {
  // Binary content types should be base64 encoded
  const binaryTypes = [
    "image/",
    "video/",
    "audio/",
    "application/octet-stream",
  ];
  const isBinary = binaryTypes.some((type) => mimeType.startsWith(type));

  if (isBinary) {
    return {
      text: body.toString("base64"),
      encoding: "base64",
      mimeType,
    };
  }

  return {
    text: body.toString("utf-8"),
    mimeType,
  };
}
```

### HAR File Size Considerations

HAR files can become very large:

```
Typical sizes:
- Small API responses: 1-10KB per entry
- Large API responses: 100KB-1MB per entry
- Images/videos: 1MB-10MB per entry

Example:
- 100 API requests × 10KB = 1MB
- 50 images × 100KB = 5MB
- Total HAR file: ~6MB
```

**Optimization strategies:**

1. **Exclude large resources:**

```typescript
await page.routeFromHAR("./api.har", {
  url: "**/api/**", // Only API calls
  update: true,
});

// Images/videos not recorded
```

2. **Compress HAR files:**

```bash
gzip api.har  # Reduces size by 80-90%
```

3. **Split HAR files:**

```typescript
// Separate HAR files for different domains
await page.routeFromHAR("./api-users.har", { url: "**/api/users/**" });
await page.routeFromHAR("./api-products.har", { url: "**/api/products/**" });
```

### HAR Replay Fidelity

**What is preserved:**

- Response status code
- Response headers
- Response body
- Request method
- Request URL
- Request headers

**What is NOT preserved:**

- Timing (responses are instant)
- Network errors
- Partial responses
- Streaming responses
- WebSocket frames

**Simulating delays:**

```typescript
await page.route("**/api/**", async (route) => {
  const entry = harRouter.find(route.request());

  if (entry) {
    // Simulate original timing
    const delay = entry.time || 0;
    await new Promise((resolve) => setTimeout(resolve, delay));

    await route.fulfill({
      status: entry.response.status,
      headers: entry.response.headers,
      body: entry.response.content.text,
    });
  }
});
```

---

## Layer 10: Service Workers & Special Cases

### Service Worker Architecture

Service Workers add another layer of interception:

```
Browser Request Flow:

  fetch('/api/users')
         ↓
  [Playwright Interception] ← Layer 1
         ↓
  Service Worker
         ↓
  [Service Worker fetch handler] ← Layer 2
         ↓
  Network Stack
         ↓
  Actual HTTP Request
```

### Interception Order

Playwright intercepts **before** Service Workers:

```typescript
// Service Worker
self.addEventListener("fetch", (event) => {
  console.log("SW: ", event.request.url);
  event.respondWith(fetch(event.request));
});

// Playwright
await page.route("**/api/**", (route) => {
  console.log("PW: ", route.request().url());
  route.continue();
});

// Output when fetching /api/users:
// PW: https://example.com/api/users
// SW: https://example.com/api/users
```

**Implications:**

- Playwright can intercept requests before SW sees them
- Playwright can prevent SW from seeing requests (via fulfill/abort)
- SW can still intercept requests that Playwright continues

### Bypassing Service Workers

```typescript
await page.route("**/api/**", (route) => {
  route.continue({
    // This bypasses the Service Worker
    // Request goes directly to network
    headers: {
      ...route.request().headers(),
      "Service-Worker": "script", // Special header
    },
  });
});
```

Or use CDP directly:

```typescript
const client = await page.context().newCDPSession(page);
await client.send("Fetch.continueRequest", {
  requestId: "...",
  bypassServiceWorker: true,
});
```

### WebSocket Interception

WebSockets have limited interception support:

**What you CAN do:**

```typescript
// Intercept WebSocket upgrade request
await page.route("**/ws", (route) => {
  if (route.request().headers()["upgrade"] === "websocket") {
    console.log("WebSocket connection to:", route.request().url());
    route.continue();
  }
});
```

**What you CANNOT do:**

- Intercept individual WebSocket frames
- Mock WebSocket messages
- Modify WebSocket data

**Workaround: Mock at application level:**

```typescript
// Inject mock WebSocket before page loads
await page.addInitScript(() => {
  const OriginalWebSocket = window.WebSocket;

  window.WebSocket = class MockWebSocket extends EventTarget {
    constructor(url) {
      super();
      console.log("Mock WebSocket:", url);

      // Simulate connection
      setTimeout(() => {
        this.dispatchEvent(new Event("open"));
      }, 10);
    }

    send(data) {
      console.log("Mock send:", data);
      // Simulate response
      setTimeout(() => {
        this.dispatchEvent(
          new MessageEvent("message", {
            data: JSON.stringify({ mocked: true }),
          }),
        );
      }, 10);
    }

    close() {
      this.dispatchEvent(new Event("close"));
    }
  };
});
```

### Server-Sent Events (SSE)

SSE can be intercepted:

```typescript
await page.route("**/events", (route) => {
  // Mock SSE stream
  const events = [
    'data: {"event": "update", "value": 1}\n\n',
    'data: {"event": "update", "value": 2}\n\n',
    'data: {"event": "update", "value": 3}\n\n',
  ].join("");

  route.fulfill({
    status: 200,
    headers: {
      "Content-Type": "text/event-stream",
      "Cache-Control": "no-cache",
      Connection: "keep-alive",
    },
    body: events,
  });
});
```

**Limitation:** Cannot stream events over time, entire response sent at once.

### HTTP/2 Server Push

HTTP/2 server push is handled transparently:

```
Client requests: /index.html
Server responds: 200 OK
Server pushes:   /style.css (PUSH_PROMISE)
Server pushes:   /script.js (PUSH_PROMISE)
```

**Playwright interception:**

- Main request: Intercepted normally
- Pushed resources: Also intercepted
- Each push creates separate `requestPaused` event

```typescript
await page.route("**/*", (route) => {
  console.log("Request:", route.request().url());
  console.log("Is push:", route.request().headers()["x-http2-push"]); // Not standard
  route.continue();
});
```

### Data URLs

Data URLs are NOT intercepted:

```typescript
// This is NOT intercepted
await page.goto("data:text/html,<h1>Hello</h1>");

// This is NOT intercepted
await page.evaluate(() => {
  fetch("data:text/plain,Hello");
});
```

**Reason:** Data URLs don't go through network stack.

### Blob URLs

Blob URLs are NOT intercepted:

```typescript
// This is NOT intercepted
const blob = new Blob(["Hello"], { type: "text/plain" });
const url = URL.createObjectURL(blob);
await fetch(url);
```

**Reason:** Blob URLs are resolved in-memory.

### File URLs

File URLs behavior depends on browser:

```typescript
// May or may not be intercepted (browser-dependent)
await page.goto("file:///path/to/file.html");
```

**Chromium:** Not intercepted (security restriction)
**Firefox:** May be intercepted
**WebKit:** Not intercepted

### Chrome Extensions

Chrome extension requests are NOT intercepted:

```typescript
// Extension background script
fetch("chrome-extension://abc123/data.json");
// Not intercepted by Playwright
```

**Reason:** Extension requests use different protocol (chrome-extension://).

### Preflight Requests (CORS)

CORS preflight requests (OPTIONS) are intercepted:

```typescript
await page.route("**/api/**", (route) => {
  if (route.request().method() === "OPTIONS") {
    // Handle preflight
    route.fulfill({
      status: 204,
      headers: {
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE",
        "Access-Control-Allow-Headers": "Content-Type, Authorization",
      },
    });
  } else {
    // Handle actual request
    route.continue();
  }
});
```

---

## Layer 11: Error Handling & Recovery

### Error Categories

**1. Network Errors**

```typescript
await page.route("**/api/**", (route) => {
  route.abort("Failed"); // Simulates network failure
});

// In page:
fetch("/api/users").catch((error) => {
  console.error("Network error:", error);
  // TypeError: Failed to fetch
});
```

**Error codes:**

- `Failed` - Generic failure
- `Aborted` - Request aborted
- `TimedOut` - Request timeout
- `AccessDenied` - Access denied
- `ConnectionClosed` - Connection closed
- `ConnectionReset` - Connection reset
- `ConnectionRefused` - Connection refused
- `ConnectionAborted` - Connection aborted
- `ConnectionFailed` - Connection failed
- `NameNotResolved` - DNS failure
- `InternetDisconnected` - No internet
- `AddressUnreachable` - Address unreachable
- `BlockedByClient` - Blocked by client
- `BlockedByResponse` - Blocked by response

**2. Protocol Errors**

```typescript
// Invalid response
await page.route("**/api/**", (route) => {
  route.fulfill({
    status: 999, // Invalid status code
    body: "test",
  });
});
// Error: Invalid status code
```

**3. Handler Errors**

```typescript
await page.route("**/api/**", (route) => {
  throw new Error("Handler crashed");
  // Request auto-continues
});
```

**4. Timeout Errors**

```typescript
await page.route("**/api/**", async (route) => {
  // Handler takes too long (>30s)
  await new Promise((resolve) => setTimeout(resolve, 35000));
  await route.fulfill({ body: "too late" });
  // Request already auto-continued after 30s
});
```

### Error Recovery Strategies

**1. Automatic retry:**

```typescript
async function routeWithRetry(
  page: Page,
  pattern: string,
  handler: RouteHandler,
  maxRetries = 3,
): Promise<void> {
  await page.route(pattern, async (route, request) => {
    let lastError;

    for (let attempt = 0; attempt < maxRetries; attempt++) {
      try {
        await handler(route, request);
        return;
      } catch (error) {
        lastError = error;
        console.log(`Attempt ${attempt + 1} failed:`, error);

        if (attempt < maxRetries - 1) {
          await new Promise((resolve) => setTimeout(resolve, 1000 * attempt));
        }
      }
    }

    // All retries failed, auto-continue
    if (!route._handled) {
      await route.continue();
    }
  });
}
```

**2. Fallback handler:**

```typescript
await page.route("**/api/**", async (route) => {
  try {
    const mockData = await loadMockData(route.request().url());
    await route.fulfill({ json: mockData });
  } catch (error) {
    console.error("Mock failed, using real API:", error);
    await route.continue(); // Fallback to real request
  }
});
```

**3. Circuit breaker:**

```typescript
class CircuitBreaker {
  private _failures = 0;
  private _threshold = 5;
  private _state: "closed" | "open" | "half-open" = "closed";

  async execute(fn: () => Promise<void>): Promise<void> {
    if (this._state === "open") {
      throw new Error("Circuit breaker is open");
    }

    try {
      await fn();
      this._onSuccess();
    } catch (error) {
      this._onFailure();
      throw error;
    }
  }

  private _onSuccess(): void {
    this._failures = 0;
    this._state = "closed";
  }

  private _onFailure(): void {
    this._failures++;

    if (this._failures >= this._threshold) {
      this._state = "open";

      // Try to recover after 60s
      setTimeout(() => {
        this._state = "half-open";
        this._failures = 0;
      }, 60000);
    }
  }
}

const breaker = new CircuitBreaker();

await page.route("**/api/**", async (route) => {
  try {
    await breaker.execute(async () => {
      const data = await fetchMockData();
      await route.fulfill({ json: data });
    });
  } catch (error) {
    await route.continue();
  }
});
```

### Debugging Intercepted Requests

**1. Logging:**

```typescript
await page.route("**/*", (route) => {
  console.log("━".repeat(80));
  console.log("REQUEST:", route.request().method(), route.request().url());
  console.log("Headers:", route.request().headers());
  console.log("Type:", route.request().resourceType());
  console.log("Frame:", route.request().frame().url());
  console.log("━".repeat(80));

  route.continue();
});
```

**2. Request/response inspection:**

```typescript
await page.route("**/api/**", async (route) => {
  const request = route.request();

  console.log("Request:", {
    url: request.url(),
    method: request.method(),
    headers: request.headers(),
    postData: request.postData(),
  });

  const response = await route.fetch();

  console.log("Response:", {
    status: response.status(),
    headers: await response.allHeaders(),
    body: await response.text(),
  });

  await route.fulfill({
    status: response.status(),
    headers: await response.allHeaders(),
    body: await response.body(),
  });
});
```

**3. HAR recording for debugging:**

```typescript
await page.routeFromHAR("./debug.har", {
  url: "**/*",
  update: true,
});

// All requests recorded to debug.har
// Can be analyzed with HAR viewers
```

### Handling Browser Crashes

```typescript
page.on("crash", () => {
  console.error("Page crashed!");
  // All pending route handlers are abandoned
  // Cleanup if necessary
});

browser.on("disconnected", () => {
  console.error("Browser disconnected!");
  // All route handlers are abandoned
  // Reconnection may be needed
});
```

### Memory Leak Detection

```typescript
class RouteManager {
  private _activeRoutes = new Set<Route>();

  async handle(route: Route): Promise<void> {
    this._activeRoutes.add(route);

    try {
      await this._handler(route);
    } finally {
      this._activeRoutes.delete(route);
    }

    // Warn if too many active routes
    if (this._activeRoutes.size > 100) {
      console.warn(`Warning: ${this._activeRoutes.size} active routes`);
    }
  }
}
```

---

## Layer 12: Security Considerations

### HTTPS/TLS Handling

Playwright intercepts **after** TLS termination:

```
Client (Browser)
      ↓
   TLS Handshake
      ↓
   Encrypted Connection
      ↓
   Browser decrypts
      ↓
   [PLAYWRIGHT INTERCEPTS HERE] ← Plaintext
      ↓
   Network Stack
      ↓
   TLS encryption
      ↓
   Server
```

**Implications:**

- No certificate issues
- Can inspect HTTPS traffic
- Cannot modify TLS handshake
- Cannot intercept certificate validation

### Certificate Pinning

Certificate pinning is NOT bypassed:

```typescript
// If app uses certificate pinning
await page.route("**/api/**", (route) => {
  route.fulfill({ json: mockData });
});

// This works because request never reaches network
// Pinning check never happens
```

**But:**

```typescript
await page.route("**/api/**", async (route) => {
  const response = await route.fetch();
  // This WILL fail if certificate pinning is enforced
  // Because actual network request is made
});
```

### Content Security Policy (CSP)

CSP is enforced **after** interception:

```typescript
await page.route("**/script.js", (route) => {
  route.fulfill({
    headers: {
      "Content-Type": "application/javascript",
    },
    body: 'console.log("injected");',
  });
});

// If page has CSP: script-src 'self'
// Injected script will be blocked by CSP
```

**Workaround: Modify CSP header:**

```typescript
await page.route("**/*.html", async (route) => {
  const response = await route.fetch();
  const headers = await response.allHeaders();

  // Remove or modify CSP
  delete headers["content-security-policy"];

  await route.fulfill({
    status: response.status(),
    headers,
    body: await response.body(),
  });
});
```

### Same-Origin Policy (SOP)

SOP is enforced **after** interception:

```typescript
// Page at https://example.com
await page.route("**/api/**", (route) => {
  route.fulfill({
    headers: {
      "Access-Control-Allow-Origin": "*", // Add CORS header
    },
    json: mockData,
  });
});

// Now cross-origin requests work
```

### Authentication & Credentials

**HTTP Basic Auth:**

```typescript
await page.route("**/protected/**", (route) => {
  const auth = route.request().headers()["authorization"];

  if (auth === "Basic dXNlcjpwYXNz") {
    // user:pass
    route.fulfill({ json: { data: "secret" } });
  } else {
    route.fulfill({
      status: 401,
      headers: {
        "WWW-Authenticate": 'Basic realm="Protected"',
      },
    });
  }
});
```

**Bearer Tokens:**

```typescript
await page.route("**/api/**", (route) => {
  const token = route
    .request()
    .headers()
    ["authorization"]?.replace("Bearer ", "");

  if (token === "valid-token") {
    route.fulfill({ json: { data: "authorized" } });
  } else {
    route.fulfill({ status: 403, json: { error: "Forbidden" } });
  }
});
```

**Cookies:**

```typescript
await page.route("**/api/**", (route) => {
  const cookies = route.request().headers()["cookie"];

  if (cookies?.includes("session=abc123")) {
    route.fulfill({ json: { data: "authenticated" } });
  } else {
    route.fulfill({ status: 401 });
  }
});
```

### Sensitive Data Exposure

**Risk: Logging sensitive data:**

```typescript
// BAD: Logs passwords
await page.route("**/login", (route) => {
  console.log("POST data:", route.request().postData());
  // Logs: {"username":"user","password":"secret123"}
  route.continue();
});

// GOOD: Redact sensitive fields
await page.route("**/login", (route) => {
  const data = JSON.parse(route.request().postData() || "{}");
  console.log("POST data:", {
    ...data,
    password: "[REDACTED]",
  });
  route.continue();
});
```

### Injection Attacks

**Risk: Unsanitized mock data:**

```typescript
// BAD: XSS vulnerability
await page.route("**/api/user", (route) => {
  const userId = new URL(route.request().url()).searchParams.get("id");
  route.fulfill({
    json: {
      name: userId, // If userId contains <script>, XSS!
    },
  });
});

// GOOD: Sanitize or validate
await page.route("**/api/user", (route) => {
  const userId = new URL(route.request().url()).searchParams.get("id");

  if (!/^[a-zA-Z0-9]+$/.test(userId || "")) {
    route.fulfill({ status: 400, json: { error: "Invalid ID" } });
    return;
  }

  route.fulfill({
    json: {
      name: userId,
    },
  });
});
```

---

## Layer 13: Advanced Patterns & Techniques

### Request Modification

**Modify URL:**

```typescript
await page.route("**/old-api/**", (route) => {
  const url = route.request().url().replace("/old-api/", "/new-api/");
  route.continue({ url });
});
```

**Modify headers:**

```typescript
await page.route("**/api/**", (route) => {
  route.continue({
    headers: {
      ...route.request().headers(),
      Authorization: "Bearer mock-token",
      "X-Custom-Header": "value",
    },
  });
});
```

**Modify POST data:**

```typescript
await page.route("**/api/submit", (route) => {
  const data = JSON.parse(route.request().postData() || "{}");
  data.modified = true;

  route.continue({
    postData: JSON.stringify(data),
  });
});
```

### Response Modification

**Modify status:**

```typescript
await page.route("**/api/**", async (route) => {
  const response = await route.fetch();

  // Change 404 to 200 with empty array
  if (response.status() === 404) {
    await route.fulfill({
      status: 200,
      headers: await response.allHeaders(),
      json: [],
    });
  } else {
    await route.fulfill({
      status: response.status(),
      headers: await response.allHeaders(),
      body: await response.body(),
    });
  }
});
```

**Modify response body:**

```typescript
await page.route("**/api/users", async (route) => {
  const response = await route.fetch();
  const json = await response.json();

  // Add extra field to each user
  json.forEach((user) => {
    user.mocked = true;
  });

  await route.fulfill({
    status: response.status(),
    headers: await response.allHeaders(),
    json,
  });
});
```

### Conditional Stubbing

**Based on environment:**

```typescript
const useMocks = process.env.USE_MOCKS === "true";

if (useMocks) {
  await page.route("**/api/**", (route) => {
    route.fulfill({ json: mockData });
  });
} else {
  // No interception, use real API
}
```

**Based on request parameters:**

```typescript
await page.route("**/api/users", (route) => {
  const url = new URL(route.request().url());
  const page = url.searchParams.get("page");

  if (page === "1") {
    route.fulfill({ json: page1Data });
  } else if (page === "2") {
    route.fulfill({ json: page2Data });
  } else {
    route.continue(); // Use real API for other pages
  }
});
```

**Based on time:**

```typescript
await page.route("**/api/**", (route) => {
  const hour = new Date().getHours();

  if (hour >= 9 && hour < 17) {
    // Business hours: use real API
    route.continue();
  } else {
    // Off hours: use mocks
    route.fulfill({ json: mockData });
  }
});
```

### Stateful Mocking

**Simulate database:**

```typescript
const database = {
  users: [
    { id: 1, name: "Alice" },
    { id: 2, name: "Bob" },
  ],
};

await page.route("**/api/users", (route) => {
  if (route.request().method() === "GET") {
    route.fulfill({ json: database.users });
  } else if (route.request().method() === "POST") {
    const newUser = JSON.parse(route.request().postData() || "{}");
    newUser.id = database.users.length + 1;
    database.users.push(newUser);
    route.fulfill({ status: 201, json: newUser });
  }
});

await page.route("**/api/users/*", (route) => {
  const id = parseInt(route.request().url().split("/").pop() || "0");

  if (route.request().method() === "GET") {
    const user = database.users.find((u) => u.id === id);
    if (user) {
      route.fulfill({ json: user });
    } else {
      route.fulfill({ status: 404 });
    }
  } else if (route.request().method() === "DELETE") {
    database.users = database.users.filter((u) => u.id !== id);
    route.fulfill({ status: 204 });
  }
});
```

### Simulating Network Conditions

**Latency:**

```typescript
await page.route("**/api/**", async (route) => {
  // Simulate 500ms latency
  await new Promise((resolve) => setTimeout(resolve, 500));
  await route.fulfill({ json: mockData });
});
```

**Variable latency:**

```typescript
await page.route("**/api/**", async (route) => {
  // Random latency between 100-1000ms
  const latency = 100 + Math.random() * 900;
  await new Promise((resolve) => setTimeout(resolve, latency));
  await route.fulfill({ json: mockData });
});
```

**Packet loss:**

```typescript
await page.route("**/api/**", (route) => {
  // 10% packet loss
  if (Math.random() < 0.1) {
    route.abort("Failed");
  } else {
    route.fulfill({ json: mockData });
  }
});
```

**Throttling:**

```typescript
await page.route("**/large-file.zip", async (route) => {
  const response = await route.fetch();
  const body = await response.body();

  // Simulate slow download (1KB/100ms = 10KB/s)
  const chunkSize = 1024;
  const chunks = [];

  for (let i = 0; i < body.length; i += chunkSize) {
    chunks.push(body.slice(i, i + chunkSize));
    await new Promise((resolve) => setTimeout(resolve, 100));
  }

  await route.fulfill({
    status: response.status(),
    headers: await response.allHeaders(),
    body: Buffer.concat(chunks),
  });
});
```

### Request Deduplication

**Prevent duplicate requests:**

```typescript
const inFlight = new Map<string, Promise<any>>();

await page.route("**/api/**", async (route) => {
  const key = `${route.request().method()}:${route.request().url()}`;

  if (inFlight.has(key)) {
    // Wait for in-flight request
    const result = await inFlight.get(key);
    await route.fulfill({ json: result });
  } else {
    // Make new request
    const promise = route.fetch().then((r) => r.json());
    inFlight.set(key, promise);

    try {
      const result = await promise;
      await route.fulfill({ json: result });
    } finally {
      inFlight.delete(key);
    }
  }
});
```

### Caching

**Simple cache:**

```typescript
const cache = new Map<string, any>();

await page.route("**/api/**", async (route) => {
  const key = route.request().url();

  if (cache.has(key)) {
    console.log("Cache hit:", key);
    await route.fulfill({ json: cache.get(key) });
  } else {
    console.log("Cache miss:", key);
    const response = await route.fetch();
    const json = await response.json();
    cache.set(key, json);
    await route.fulfill({ json });
  }
});
```

**TTL cache:**

```typescript
interface CacheEntry {
  data: any;
  expires: number;
}

const cache = new Map<string, CacheEntry>();
const TTL = 60000; // 1 minute

await page.route("**/api/**", async (route) => {
  const key = route.request().url();
  const now = Date.now();

  const entry = cache.get(key);
  if (entry && entry.expires > now) {
    console.log("Cache hit:", key);
    await route.fulfill({ json: entry.data });
  } else {
    console.log("Cache miss:", key);
    const response = await route.fetch();
    const json = await response.json();
    cache.set(key, {
      data: json,
      expires: now + TTL,
    });
    await route.fulfill({ json });
  }
});
```

---

## Layer 14: Browser Context & Multiple Tabs Testing

### Browser Context Architecture

A **Browser Context** is an isolated browser session within a browser instance. Think of it as an incognito window - it has its own cookies, storage, and cache, completely isolated from other contexts.

```
┌─────────────────────────────────────────────────────────────┐
│                    Browser Instance                         │
│                                                             │
│  ┌───────────────────────────────────────────────────┐    │
│  │         Browser Context 1 (Default)               │    │
│  │  - Cookies: {...}                                 │    │
│  │  - LocalStorage: {...}                            │    │
│  │  - SessionStorage: {...}                          │    │
│  │  - Cache: {...}                                   │    │
│  │                                                   │    │
│  │  ┌─────────────┐  ┌─────────────┐               │    │
│  │  │   Page 1    │  │   Page 2    │               │    │
│  │  │  (Tab 1)    │  │  (Tab 2)    │               │    │
│  │  └─────────────┘  └─────────────┘               │    │
│  └───────────────────────────────────────────────────┘    │
│                                                             │
│  ┌───────────────────────────────────────────────────┐    │
│  │         Browser Context 2 (Isolated)              │    │
│  │  - Cookies: {...}  (different from Context 1)     │    │
│  │  - LocalStorage: {...}                            │    │
│  │  - SessionStorage: {...}                          │    │
│  │  - Cache: {...}                                   │    │
│  │                                                   │    │
│  │  ┌─────────────┐  ┌─────────────┐               │    │
│  │  │   Page 3    │  │   Page 4    │               │    │
│  │  │  (Tab 3)    │  │  (Tab 4)    │               │    │
│  │  └─────────────┘  └─────────────┘               │    │
│  └───────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────┘
```

### Creating and Managing Browser Contexts

**Basic context creation:**

```typescript
import { test, expect } from '@playwright/test';

test('multiple contexts example', async ({ browser }) => {
  // Create first context
  const context1 = await browser.newContext();
  const page1 = await context1.newPage();

  // Create second context (completely isolated)
  const context2 = await browser.newContext();
  const page2 = await context2.newPage();

  // These contexts don't share cookies, storage, or cache
  await page1.goto('https://example.com');
  await page2.goto('https://example.com');

  // Cleanup
  await context1.close();
  await context2.close();
});
```

**Context with custom options:**

```typescript
const context = await browser.newContext({
  viewport: { width: 1920, height: 1080 },
  userAgent: 'Custom User Agent',
  locale: 'en-US',
  timezoneId: 'America/New_York',
  permissions: ['geolocation'],
  geolocation: { latitude: 40.7128, longitude: -74.0060 },
  colorScheme: 'dark',
  deviceScaleFactor: 2,
  hasTouch: true,
  isMobile: false,
  javaScriptEnabled: true,
  offline: false,
  httpCredentials: {
    username: 'user',
    password: 'pass'
  },
  extraHTTPHeaders: {
    'X-Custom-Header': 'value'
  },
  ignoreHTTPSErrors: true,
  bypassCSP: true,
  storageState: {
    cookies: [],
    origins: []
  }
});
```

### Route Handling in Browser Contexts

Routes can be registered at different levels:

**1. Browser-level routing (affects all contexts):**

```typescript
// NOT SUPPORTED - routes must be at context or page level
```

**2. Context-level routing (affects all pages in context):**

```typescript
const context = await browser.newContext();

// This route applies to ALL pages in this context
await context.route('**/api/**', route => {
  route.fulfill({ json: { data: 'mocked' } });
});

const page1 = await context.newPage();
const page2 = await context.newPage();

// Both pages will have API calls intercepted
await page1.goto('https://example.com');
await page2.goto('https://example.com');
```

**3. Page-level routing (affects only specific page):**

```typescript
const page1 = await context.newPage();
const page2 = await context.newPage();

// Only page1 has this route
await page1.route('**/api/**', route => {
  route.fulfill({ json: { source: 'page1' } });
});

// page2 requests go through normally
```

### Route Priority and Inheritance

When routes are registered at multiple levels, they follow a specific priority:

```
Page-level routes (highest priority)
         ↓
Context-level routes
         ↓
No interception (lowest priority)
```

**Example:**

```typescript
const context = await browser.newContext();

// Context-level route
await context.route('**/api/**', route => {
  console.log('Context handler');
  route.fulfill({ json: { source: 'context' } });
});

const page = await context.newPage();

// Page-level route (takes precedence)
await page.route('**/api/users', route => {
  console.log('Page handler');
  route.fulfill({ json: { source: 'page' } });
});

// Request to /api/users → Page handler runs
// Request to /api/posts → Context handler runs
```

### Multiple Tabs Testing Patterns

#### Pattern 1: Basic Multiple Tabs

**Opening multiple tabs in the same context:**

```typescript
test('multiple tabs basic', async ({ context }) => {
  // Create multiple pages (tabs)
  const page1 = await context.newPage();
  const page2 = await context.newPage();
  const page3 = await context.newPage();

  // Navigate each tab
  await page1.goto('https://example.com/page1');
  await page2.goto('https://example.com/page2');
  await page3.goto('https://example.com/page3');

  // Interact with specific tabs
  await page1.click('button#submit');
  await page2.fill('input#search', 'query');

  // Verify content in different tabs
  await expect(page1.locator('h1')).toHaveText('Page 1');
  await expect(page2.locator('h1')).toHaveText('Page 2');

  // Close specific tabs
  await page2.close();

  // page1 and page3 still open
});
```

#### Pattern 2: Handling Popup Windows

**When a page opens a new tab/window:**

```typescript
test('handle popup windows', async ({ page }) => {
  // Listen for popup before triggering action
  const popupPromise = page.waitForEvent('popup');

  // Click button that opens new tab
  await page.click('a[target="_blank"]');

  // Wait for popup to open
  const popup = await popupPromise;

  // Wait for popup to load
  await popup.waitForLoadState();

  // Interact with popup
  await popup.fill('input#email', 'test@example.com');
  await popup.click('button#submit');

  // Verify popup content
  await expect(popup.locator('.success')).toBeVisible();

  // Close popup
  await popup.close();

  // Continue with original page
  await page.click('button#next');
});
```

#### Pattern 3: Multiple Tabs with Different Routes

**Each tab can have different stubbing behavior:**

```typescript
test('different routes per tab', async ({ context }) => {
  const page1 = await context.newPage();
  const page2 = await context.newPage();

  // Page 1: Mock API to return user data
  await page1.route('**/api/user', route => {
    route.fulfill({
      json: {
        id: 1,
        name: 'User from Tab 1',
        email: 'tab1@example.com'
      }
    });
  });

  // Page 2: Mock API to return different user data
  await page2.route('**/api/user', route => {
    route.fulfill({
      json: {
        id: 2,
        name: 'User from Tab 2',
        email: 'tab2@example.com'
      }
    });
  });

  // Navigate both tabs
  await page1.goto('https://example.com/profile');
  await page2.goto('https://example.com/profile');

  // Each tab sees different data
  await expect(page1.locator('.user-name')).toHaveText('User from Tab 1');
  await expect(page2.locator('.user-name')).toHaveText('User from Tab 2');
});
```

#### Pattern 4: Shared State Between Tabs

**Tabs in the same context share cookies and storage:**

```typescript
test('shared state between tabs', async ({ context }) => {
  const page1 = await context.newPage();

  // Login in first tab
  await page1.goto('https://example.com/login');
  await page1.fill('input#username', 'testuser');
  await page1.fill('input#password', 'password');
  await page1.click('button#login');

  // Wait for login to complete (cookie set)
  await page1.waitForURL('**/dashboard');

  // Open second tab - should be already logged in
  const page2 = await context.newPage();
  await page2.goto('https://example.com/dashboard');

  // Both tabs are authenticated
  await expect(page1.locator('.user-menu')).toBeVisible();
  await expect(page2.locator('.user-menu')).toBeVisible();

  // Logout in page2
  await page2.click('.logout-button');

  // Refresh page1 - should also be logged out
  await page1.reload();
  await expect(page1).toHaveURL('**/login');
});
```

#### Pattern 5: Parallel Tab Operations

**Execute operations in multiple tabs concurrently:**

```typescript
test('parallel operations in tabs', async ({ context }) => {
  // Create multiple tabs
  const pages = await Promise.all([
    context.newPage(),
    context.newPage(),
    context.newPage(),
    context.newPage(),
    context.newPage()
  ]);

  // Navigate all tabs in parallel
  await Promise.all(
    pages.map((page, index) =>
      page.goto(`https://example.com/page${index + 1}`)
    )
  );

  // Perform actions in parallel
  await Promise.all(
    pages.map(page => page.click('button.load-data'))
  );

  // Wait for all tabs to complete
  await Promise.all(
    pages.map(page => page.waitForSelector('.data-loaded'))
  );

  // Verify results
  for (const page of pages) {
    await expect(page.locator('.status')).toHaveText('Success');
  }

  // Cleanup
  await Promise.all(pages.map(page => page.close()));
});
```

### Advanced Multiple Tabs Patterns

#### Pattern 6: Tab Communication Testing

**Testing cross-tab communication (BroadcastChannel, SharedWorker, etc.):**

```typescript
test('cross-tab communication', async ({ context }) => {
  const page1 = await context.newPage();
  const page2 = await context.newPage();

  await page1.goto('https://example.com/chat');
  await page2.goto('https://example.com/chat');

  // Send message from page1
  await page1.evaluate(() => {
    const channel = new BroadcastChannel('chat');
    channel.postMessage({ text: 'Hello from Tab 1', timestamp: Date.now() });
  });

  // Verify message received in page2
  const messageReceived = await page2.evaluate(() => {
    return new Promise(resolve => {
      const channel = new BroadcastChannel('chat');
      channel.onmessage = (event) => {
        resolve(event.data);
      };
      // Timeout after 5 seconds
      setTimeout(() => resolve(null), 5000);
    });
  });

  expect(messageReceived).toMatchObject({
    text: 'Hello from Tab 1'
  });
});
```

#### Pattern 7: Tab-Specific Request Tracking

**Track which tab made which request:**

```typescript
test('track requests per tab', async ({ context }) => {
  const page1 = await context.newPage();
  const page2 = await context.newPage();

  const page1Requests: string[] = [];
  const page2Requests: string[] = [];

  // Track page1 requests
  await page1.route('**/*', route => {
    page1Requests.push(route.request().url());
    route.continue();
  });

  // Track page2 requests
  await page2.route('**/*', route => {
    page2Requests.push(route.request().url());
    route.continue();
  });

  // Navigate both tabs
  await Promise.all([
    page1.goto('https://example.com/page1'),
    page2.goto('https://example.com/page2')
  ]);

  // Verify requests are tracked separately
  console.log('Page 1 requests:', page1Requests);
  console.log('Page 2 requests:', page2Requests);

  expect(page1Requests).toContain('https://example.com/page1');
  expect(page2Requests).toContain('https://example.com/page2');
  expect(page1Requests).not.toContain('https://example.com/page2');
});
```

#### Pattern 8: Conditional Routing Based on Tab

**Different stubbing behavior based on which tab makes the request:**

```typescript
test('conditional routing by tab', async ({ context }) => {
  const adminTab = await context.newPage();
  const userTab = await context.newPage();

  // Context-level route with conditional logic
  await context.route('**/api/data', (route, request) => {
    // Check which page made the request
    const frame = request.frame();
    const page = frame?.page();

    if (page === adminTab) {
      // Admin sees all data
      route.fulfill({
        json: {
          items: [
            { id: 1, name: 'Item 1', visible: true },
            { id: 2, name: 'Item 2', visible: false },
            { id: 3, name: 'Item 3', visible: true }
          ]
        }
      });
    } else if (page === userTab) {
      // User sees only visible items
      route.fulfill({
        json: {
          items: [
            { id: 1, name: 'Item 1', visible: true },
            { id: 3, name: 'Item 3', visible: true }
          ]
        }
      });
    } else {
      route.continue();
    }
  });

  await adminTab.goto('https://example.com/dashboard');
  await userTab.goto('https://example.com/dashboard');

  // Verify different data
  await expect(adminTab.locator('.item')).toHaveCount(3);
  await expect(userTab.locator('.item')).toHaveCount(2);
});
```

#### Pattern 9: Tab Lifecycle Management

**Managing tab creation, switching, and cleanup:**

```typescript
test('tab lifecycle management', async ({ context }) => {
  const tabs: Page[] = [];

  // Helper to create and track tabs
  async function createTab(url: string) {
    const page = await context.newPage();
    tabs.push(page);

    // Setup route for this tab
    await page.route('**/api/**', route => {
      console.log(`Tab ${tabs.indexOf(page)}: ${route.request().url()}`);
      route.continue();
    });

    await page.goto(url);
    return page;
  }

  // Create multiple tabs
  const tab1 = await createTab('https://example.com/tab1');
  const tab2 = await createTab('https://example.com/tab2');
  const tab3 = await createTab('https://example.com/tab3');

  // Bring specific tab to front (focus)
  await tab2.bringToFront();

  // Perform action on focused tab
  await tab2.click('button#action');

  // Close specific tab
  await tab2.close();
  tabs.splice(tabs.indexOf(tab2), 1);

  // Cleanup remaining tabs
  await Promise.all(tabs.map(tab => tab.close()));
});
```

#### Pattern 10: Testing Tab Limits and Performance

**Test behavior with many tabs:**

```typescript
test('many tabs performance', async ({ context }) => {
  const TAB_COUNT = 20;
  const pages: Page[] = [];

  // Create many tabs
  for (let i = 0; i < TAB_COUNT; i++) {
    const page = await context.newPage();
    pages.push(page);

    // Setup lightweight route
    await page.route('**/api/status', route => {
      route.fulfill({ json: { tabId: i, status: 'ok' } });
    });
  }

  // Navigate all tabs in parallel
  const startTime = Date.now();
  await Promise.all(
    pages.map((page, i) =>
      page.goto(`https://example.com/tab${i}`)
    )
  );
  const loadTime = Date.now() - startTime;

  console.log(`Loaded ${TAB_COUNT} tabs in ${loadTime}ms`);
  console.log(`Average: ${loadTime / TAB_COUNT}ms per tab`);

  // Verify all tabs loaded
  for (const page of pages) {
    await expect(page.locator('body')).toBeVisible();
  }

  // Cleanup
  await Promise.all(pages.map(page => page.close()));
});
```

### Context Isolation Patterns

#### Pattern 11: Isolated Contexts for Different Users

**Simulate multiple users with separate contexts:**

```typescript
test('multiple users with isolated contexts', async ({ browser }) => {
  // User 1 context
  const user1Context = await browser.newContext({
    storageState: {
      cookies: [{
        name: 'session',
        value: 'user1-token',
        domain: 'example.com',
        path: '/',
        expires: -1,
        httpOnly: true,
        secure: false,
        sameSite: 'Lax'
      }]
    }
  });

  // User 2 context
  const user2Context = await browser.newContext({
    storageState: {
      cookies: [{
        name: 'session',
        value: 'user2-token',
        domain: 'example.com',
        path: '/',
        expires: -1,
        httpOnly: true,
        secure: false,
        sameSite: 'Lax'
      }]
    }
  });

  // Setup different routes for each user
  await user1Context.route('**/api/user', route => {
    route.fulfill({
      json: { id: 1, name: 'User One', role: 'admin' }
    });
  });

  await user2Context.route('**/api/user', route => {
    route.fulfill({
      json: { id: 2, name: 'User Two', role: 'user' }
    });
  });

  // Create pages for each user
  const user1Page = await user1Context.newPage();
  const user2Page = await user2Context.newPage();

  // Navigate both users
  await user1Page.goto('https://example.com/dashboard');
  await user2Page.goto('https://example.com/dashboard');

  // Verify each user sees their own data
  await expect(user1Page.locator('.user-name')).toHaveText('User One');
  await expect(user2Page.locator('.user-name')).toHaveText('User Two');

  await expect(user1Page.locator('.role')).toHaveText('admin');
  await expect(user2Page.locator('.role')).toHaveText('user');

  // Cleanup
  await user1Context.close();
  await user2Context.close();
});
```

### Real-World Multi-Tab Scenarios

#### Scenario 1: Testing OAuth Flow with Popup

**OAuth typically opens a popup window for authentication:**

```typescript
test('OAuth popup flow', async ({ page, context }) => {
  // Mock OAuth provider
  await context.route('**/oauth/authorize', route => {
    route.fulfill({
      status: 200,
      contentType: 'text/html',
      body: `
        <html>
          <body>
            <h1>Login to OAuth Provider</h1>
            <button id="approve">Approve</button>
          </body>
        </html>
      `
    });
  });

  await context.route('**/oauth/callback**', route => {
    const url = new URL(route.request().url());
    const code = 'mock-auth-code-12345';
    route.fulfill({
      status: 302,
      headers: {
        'Location': `${url.searchParams.get('redirect_uri')}?code=${code}`
      }
    });
  });

  await page.goto('https://example.com/login');

  // Listen for OAuth popup
  const popupPromise = page.waitForEvent('popup');
  await page.click('button#login-with-oauth');

  const popup = await popupPromise;
  await popup.waitForLoadState();

  // Approve in popup
  await popup.click('button#approve');

  // Wait for popup to close and main page to receive token
  await popup.waitForEvent('close');

  // Verify main page is now authenticated
  await expect(page.locator('.user-profile')).toBeVisible();
});
```

#### Scenario 2: Multi-Tab Shopping Cart Sync

**Testing that shopping cart syncs across tabs:**

```typescript
test('shopping cart sync across tabs', async ({ context }) => {
  let cartItems: any[] = [];

  // Mock cart API with shared state
  await context.route('**/api/cart', route => {
    if (route.request().method() === 'GET') {
      route.fulfill({ json: { items: cartItems } });
    } else if (route.request().method() === 'POST') {
      const newItem = JSON.parse(route.request().postData() || '{}');
      cartItems.push(newItem);
      route.fulfill({ json: { items: cartItems } });
    }
  });

  // Open two tabs
  const tab1 = await context.newPage();
  const tab2 = await context.newPage();

  await tab1.goto('https://example.com/shop');
  await tab2.goto('https://example.com/shop');

  // Add item in tab1
  await tab1.click('button[data-product="product-1"]');
  await tab1.waitForResponse('**/api/cart');

  // Refresh tab2 and verify item appears
  await tab2.reload();
  await expect(tab2.locator('.cart-item')).toHaveCount(1);

  // Add another item in tab2
  await tab2.click('button[data-product="product-2"]');
  await tab2.waitForResponse('**/api/cart');

  // Refresh tab1 and verify both items
  await tab1.reload();
  await expect(tab1.locator('.cart-item')).toHaveCount(2);
});
```

#### Scenario 3: Testing Tab Recovery After Crash

**Simulate and test tab crash recovery:**

```typescript
test('tab crash recovery', async ({ context }) => {
  const page1 = await context.newPage();
  const page2 = await context.newPage();

  await page1.goto('https://example.com/page1');
  await page2.goto('https://example.com/page2');

  // Simulate crash in page1
  await page1.evaluate(() => {
    // This will crash the renderer process
    (window as any).chrome?.webview?.hostObjects?.sync.crash();
  }).catch(() => {
    // Expected to fail
  });

  // Wait for crash
  await page1.waitForEvent('crash').catch(() => {});

  // page2 should still be functional
  await expect(page2.locator('body')).toBeVisible();
  await page2.click('button#test');

  // Recover page1
  await page1.reload();
  await expect(page1.locator('body')).toBeVisible();
});
```

#### Scenario 4: Testing Real-Time Collaboration

**Multiple users editing the same document:**

```typescript
test('real-time collaboration', async ({ browser }) => {
  // Create separate contexts for two users
  const user1Context = await browser.newContext();
  const user2Context = await browser.newContext();

  let documentContent = 'Initial content';

  // Mock document API with shared state
  const setupRoutes = async (ctx: BrowserContext) => {
    await ctx.route('**/api/document/123', route => {
      if (route.request().method() === 'GET') {
        route.fulfill({ json: { content: documentContent } });
      } else if (route.request().method() === 'PUT') {
        const data = JSON.parse(route.request().postData() || '{}');
        documentContent = data.content;
        route.fulfill({ json: { content: documentContent } });
      }
    });

    // Mock WebSocket for real-time updates
    await ctx.addInitScript(() => {
      // Intercept WebSocket
      const OriginalWebSocket = window.WebSocket;
      (window as any).WebSocket = class extends OriginalWebSocket {
        constructor(url: string) {
          super(url);
          // Store reference for testing
          (window as any).__ws = this;
        }
      };
    });
  };

  await setupRoutes(user1Context);
  await setupRoutes(user2Context);

  const user1Page = await user1Context.newPage();
  const user2Page = await user2Context.newPage();

  await user1Page.goto('https://example.com/document/123');
  await user2Page.goto('https://example.com/document/123');

  // User 1 types
  await user1Page.fill('textarea#editor', 'User 1 edit');
  await user1Page.click('button#save');

  // Simulate WebSocket message to user 2
  await user2Page.evaluate(() => {
    const event = new MessageEvent('message', {
      data: JSON.stringify({ type: 'update', content: 'User 1 edit' })
    });
    (window as any).__ws?.dispatchEvent(event);
  });

  // Verify user 2 sees the update
  await expect(user2Page.locator('textarea#editor')).toHaveValue('User 1 edit');

  await user1Context.close();
  await user2Context.close();
});
```

### Performance Considerations for Multiple Tabs

#### Memory Management

```typescript
test('memory management with many tabs', async ({ context }) => {
  const MAX_TABS = 10;
  const pages: Page[] = [];

  // Monitor memory usage
  const getMemoryUsage = async () => {
    const metrics = await context.pages()[0]?.evaluate(() => {
      return (performance as any).memory;
    });
    return metrics;
  };

  const initialMemory = await getMemoryUsage();

  // Create tabs
  for (let i = 0; i < MAX_TABS; i++) {
    const page = await context.newPage();
    pages.push(page);
    await page.goto('https://example.com');
  }

  const peakMemory = await getMemoryUsage();

  // Close tabs
  await Promise.all(pages.map(p => p.close()));

  // Wait for GC
  await new Promise(resolve => setTimeout(resolve, 1000));

  const finalMemory = await getMemoryUsage();

  console.log('Memory usage:');
  console.log('Initial:', initialMemory);
  console.log('Peak:', peakMemory);
  console.log('Final:', finalMemory);
});
```

#### Request Throttling

```typescript
test('request throttling across tabs', async ({ context }) => {
  const requestCounts = new Map<string, number>();

  // Track requests across all tabs
  await context.route('**/*', route => {
    const url = route.request().url();
    requestCounts.set(url, (requestCounts.get(url) || 0) + 1);

    // Throttle if too many requests
    const count = requestCounts.get(url) || 0;
    if (count > 10) {
      route.abort('failed');
    } else {
      route.continue();
    }
  });

  const pages = await Promise.all([
    context.newPage(),
    context.newPage(),
    context.newPage()
  ]);

  // All tabs try to load same resources
  await Promise.all(
    pages.map(page => page.goto('https://example.com'))
  );

  console.log('Request counts:', requestCounts);
});
```

### Best Practices for Multi-Tab Testing

**1. Always clean up tabs:**

```typescript
test('proper cleanup', async ({ context }) => {
  const tabs: Page[] = [];

  try {
    // Create tabs
    for (let i = 0; i < 5; i++) {
      tabs.push(await context.newPage());
    }

    // Test logic...

  } finally {
    // Ensure cleanup even if test fails
    await Promise.all(tabs.map(tab => tab.close().catch(() => {})));
  }
});
```

**2. Use page.waitForEvent for popup handling:**

```typescript
test('reliable popup handling', async ({ page }) => {
  // Set up listener BEFORE triggering action
  const popupPromise = page.waitForEvent('popup');

  // Trigger popup
  await page.click('button#open-popup');

  // Wait for popup
  const popup = await popupPromise;

  // Now safe to interact
  await popup.waitForLoadState();
});
```

**3. Avoid race conditions with proper synchronization:**

```typescript
test('synchronized multi-tab operations', async ({ context }) => {
  const page1 = await context.newPage();
  const page2 = await context.newPage();

  // Wait for both to be ready
  await Promise.all([
    page1.goto('https://example.com'),
    page2.goto('https://example.com')
  ]);

  // Perform synchronized actions
  await Promise.all([
    page1.click('button#action'),
    page2.click('button#action')
  ]);

  // Wait for both to complete
  await Promise.all([
    page1.waitForSelector('.result'),
    page2.waitForSelector('.result')
  ]);
});
```

---

## Layer 15: Comparison with Alternative Approaches

### vs. HTTP Proxy (mitmproxy, Charles Proxy)

**HTTP Proxy Architecture:**

```
Browser → Proxy Server → Real Server
          ↑
     Intercepts here
```

**Comparison:**

| Feature                 | Playwright         | HTTP Proxy                 |
| ----------------------- | ------------------ | -------------------------- |
| Setup complexity        | Low (programmatic) | Medium (configure browser) |
| HTTPS support           | Seamless           | Requires certificate trust |
| Programmatic control    | Full               | Limited                    |
| Language support        | Multiple           | Proxy-specific             |
| Performance overhead    | Low (~5-10ms)      | Medium (~10-50ms)          |
| Can intercept localhost | Yes                | Yes                        |
| Can intercept file://   | No                 | No                         |
| Works with any app      | No (browser only)  | Yes                        |
| Debugging UI            | No                 | Yes                        |

**When to use HTTP Proxy:**

- Need to intercept non-browser traffic
- Want visual debugging interface
- Need to share recordings with non-technical users

**When to use Playwright:**

- Automated testing
- Programmatic control needed
- Want to avoid certificate issues
- Need tight integration with test code

### vs. Mock Service Worker (MSW)

**MSW Architecture:**

```
Browser
  ↓
Service Worker (intercepts)
  ↓
Network (or mock)
```

**Comparison:**

| Feature                     | Playwright      | MSW                  |
| --------------------------- | --------------- | -------------------- |
| Runs in                     | Test process    | Browser              |
| Setup                       | Test code       | App code + test code |
| Can intercept               | All requests    | Only fetch/XHR       |
| Works without SW support    | Yes             | No                   |
| Affects production code     | No              | Potentially yes      |
| TypeScript support          | Yes             | Yes                  |
| Can modify requests         | Yes             | Yes                  |
| Can simulate network errors | Yes             | Yes                  |
| Performance                 | Slight overhead | Minimal overhead     |

**When to use MSW:**

- Want mocks to work in development mode
- Need mocks in browser DevTools
- Want same mocks for dev and test

**When to use Playwright:**

- E2E testing only
- Need to intercept non-fetch requests
- Want complete isolation from app code

### vs. Sinon/Jest Mocks

**Sinon/Jest Architecture:**

```
Test Code
  ↓
Mock fetch() function
  ↓
Return mock data
```

**Comparison:**

| Feature                    | Playwright       | Sinon/Jest           |
| -------------------------- | ---------------- | -------------------- |
| Intercepts                 | Network layer    | Function calls       |
| Scope                      | Browser requests | JavaScript functions |
| Setup location             | Test code        | Test code            |
| Can test actual fetch      | Yes              | No (mocked)          |
| Can test network errors    | Yes              | Limited              |
| Works with any HTTP client | Yes              | No (must mock each)  |
| TypeScript safety          | Good             | Excellent            |

**When to use Sinon/Jest:**

- Unit testing
- Want to mock non-network functions
- Need fine-grained control over function behavior

**When to use Playwright:**

- Integration/E2E testing
- Want to test actual network layer
- Need to intercept all HTTP clients

### vs. Nock (Node.js HTTP mocking)

**Nock Architecture:**

```
Node.js http/https module
  ↓
Nock intercepts
  ↓
Return mock
```

**Comparison:**

| Feature     | Playwright       | Nock             |
| ----------- | ---------------- | ---------------- |
| Environment | Browser          | Node.js          |
| Intercepts  | Browser requests | Node.js requests |
| Use case    | E2E testing      | API testing      |
| Setup       | Playwright API   | Nock API         |
| Can test UI | Yes              | No               |

**When to use Nock:**

- Testing Node.js backend
- API integration tests
- No browser involved

**When to use Playwright:**

- Testing browser frontend
- Full E2E tests
- Need to test UI + API together

---

## Layer 16: Implementation Deep Dive

### Playwright Source Code Structure

```
playwright/
├── packages/
│   ├── playwright-core/
│   │   ├── src/
│   │   │   ├── server/
│   │   │   │   ├── chromium/
│   │   │   │   │   └── crNetworkManager.ts  ← CDP implementation
│   │   │   │   ├── firefox/
│   │   │   │   │   └── ffNetworkManager.ts  ← Juggler implementation
│   │   │   │   ├── webkit/
│   │   │   │   │   └── wkNetworkManager.ts  ← WebKit implementation
│   │   │   │   ├── network.ts               ← Common network code
│   │   │   │   └── page.ts                  ← Page class
│   │   │   └── client/
│   │   │       └── network.ts               ← Public API
│   │   └── lib/
│   └── playwright/
│       └── index.ts                         ← Entry point
```

### Key Classes

**1. Route class:**

```typescript
// Simplified from actual source
export class Route {
  private _request: Request;
  private _delegate: RouteDelegate;
  private _handled = false;

  constructor(request: Request, delegate: RouteDelegate) {
    this._request = request;
    this._delegate = delegate;
  }

  request(): Request {
    return this._request;
  }

  async continue(overrides: ContinueOverrides = {}): Promise<void> {
    this._checkNotHandled();
    this._handled = true;
    await this._delegate.continue(this._request, overrides);
  }

  async fulfill(response: FulfillResponse): Promise<void> {
    this._checkNotHandled();
    this._handled = true;
    await this._delegate.fulfill(this._request, response);
  }

  async abort(errorCode?: string): Promise<void> {
    this._checkNotHandled();
    this._handled = true;
    await this._delegate.abort(this._request, errorCode);
  }

  async fetch(overrides?: FetchOverrides): Promise<Response> {
    return await this._delegate.fetch(this._request, overrides);
  }

  private _checkNotHandled(): void {
    if (this._handled) {
      throw new Error("Route is already handled!");
    }
  }
}
```

**2. NetworkManager class (Chromium):**

```typescript
// Simplified from actual source
export class CRNetworkManager {
  private _client: CDPSession;
  private _page: Page;
  private _requestIdToRequest = new Map<string, InterceptableRequest>();
  private _routes: RouteHandler[] = [];

  async initialize(): Promise<void> {
    await this._client.send("Fetch.enable", {
      patterns: [{ urlPattern: "*", requestStage: "Request" }],
    });

    this._client.on("Fetch.requestPaused", this._onRequestPaused.bind(this));
    this._client.on("Fetch.authRequired", this._onAuthRequired.bind(this));
  }

  async addRoute(pattern: URLMatch, handler: RouteHandler): Promise<void> {
    this._routes.unshift({ pattern, handler });
  }

  async removeRoute(pattern: URLMatch, handler?: RouteHandler): Promise<void> {
    this._routes = this._routes.filter((route) => {
      if (handler && route.handler !== handler) return true;
      return !this._matchPattern(route.pattern, pattern);
    });
  }

  private async _onRequestPaused(
    event: Protocol.Fetch.requestPausedPayload,
  ): Promise<void> {
    const request = new InterceptableRequest(
      this._client,
      event,
      this._page.mainFrame(),
    );

    this._requestIdToRequest.set(event.requestId, request);

    const route = this._findMatchingRoute(request);

    if (route) {
      const routeObject = new Route(request, {
        continue: this._continue.bind(this),
        fulfill: this._fulfill.bind(this),
        abort: this._abort.bind(this),
        fetch: this._fetch.bind(this),
      });

      try {
        await route.handler(routeObject, request);
      } catch (error) {
        // On error, auto-continue
        if (!routeObject._handled) {
          await this._continue(request, {});
        }
      }
    } else {
      await this._continue(request, {});
    }
  }

  private _findMatchingRoute(request: Request): RouteHandler | null {
    for (const route of this._routes) {
      if (this._matchesPattern(request.url(), route.pattern)) {
        return route;
      }
    }
    return null;
  }

  private async _continue(
    request: InterceptableRequest,
    overrides: ContinueOverrides,
  ): Promise<void> {
    const requestId = request._interceptionId;

    try {
      await this._client.send("Fetch.continueRequest", {
        requestId,
        url: overrides.url,
        method: overrides.method,
        postData: overrides.postData,
        headers: overrides.headers
          ? this._headersArray(overrides.headers)
          : undefined,
      });
    } finally {
      this._requestIdToRequest.delete(requestId);
    }
  }

  private async _fulfill(
    request: InterceptableRequest,
    response: FulfillResponse,
  ): Promise<void> {
    const requestId = request._interceptionId;

    let body = "";
    if (response.body) {
      body = Buffer.isBuffer(response.body)
        ? response.body.toString("base64")
        : Buffer.from(response.body).toString("base64");
    } else if (response.json) {
      body = Buffer.from(JSON.stringify(response.json)).toString("base64");
    }

    try {
      await this._client.send("Fetch.fulfillRequest", {
        requestId,
        responseCode: response.status || 200,
        responsePhrase: response.statusText,
        responseHeaders: this._headersArray(response.headers || {}),
        body,
      });
    } finally {
      this._requestIdToRequest.delete(requestId);
    }
  }

  private async _abort(
    request: InterceptableRequest,
    errorCode?: string,
  ): Promise<void> {
    const requestId = request._interceptionId;

    try {
      await this._client.send("Fetch.failRequest", {
        requestId,
        errorReason: errorCode || "Failed",
      });
    } finally {
      this._requestIdToRequest.delete(requestId);
    }
  }

  private _headersArray(
    headers: Record<string, string>,
  ): Array<{ name: string; value: string }> {
    return Object.entries(headers).map(([name, value]) => ({ name, value }));
  }
}
```

### Pattern Matching Implementation

```typescript
type URLMatch = string | RegExp | ((url: string) => boolean);

function compilePattern(pattern: URLMatch): (url: string) => boolean {
  if (typeof pattern === "function") {
    return pattern;
  }

  if (pattern instanceof RegExp) {
    return (url: string) => pattern.test(url);
  }

  // Glob pattern
  return (url: string) => {
    const regex = globToRegex(pattern);
    return regex.test(url);
  };
}

function globToRegex(glob: string): RegExp {
  let regex = "";
  let inGroup = false;

  for (let i = 0; i < glob.length; i++) {
    const c = glob[i];

    switch (c) {
      case "*":
        if (glob[i + 1] === "*") {
          regex += ".*";
          i++; // Skip next *
        } else {
          regex += "[^/]*";
        }
        break;
      case "?":
        regex += ".";
        break;
      case "{":
        regex += "(";
        inGroup = true;
        break;
      case "}":
        regex += ")";
        inGroup = false;
        break;
      case ",":
        regex += inGroup ? "|" : ",";
        break;
      case ".":
      case "+":
      case "^":
      case "$":
      case "(":
      case ")":
      case "[":
      case "]":
      case "|":
      case "\\":
        regex += "\\" + c;
        break;
      default:
        regex += c;
    }
  }

  return new RegExp("^" + regex + "$");
}

// Examples:
// globToRegex('**/*.js')     → /^.*\/[^/]*\.js$/
// globToRegex('**/api/**')   → /^.*\/api\/.*$/
// globToRegex('/api/{v1,v2}/users') → /^\/api\/(v1|v2)\/users$/
```

---

## Appendices

### Appendix A: Complete API Reference

**page.route()**

```typescript
await page.route(
  url: string | RegExp | ((url: string) => boolean),
  handler: (route: Route, request: Request) => Promise<void>,
  options?: {
    times?: number;  // Auto-unregister after N matches
  }
): Promise<void>
```

**page.unroute()**

```typescript
await page.unroute(
  url: string | RegExp | ((url: string) => boolean),
  handler?: (route: Route, request: Request) => Promise<void>
): Promise<void>
```

**page.routeFromHAR()**

```typescript
await page.routeFromHAR(
  har: string,  // Path to HAR file
  options?: {
    url?: string | RegExp;  // Filter URLs
    update?: boolean;       // Update mode
    updateContent?: 'embed' | 'attach';  // How to store bodies
    updateMode?: 'full' | 'minimal';     // Update strategy
  }
): Promise<void>
```

**route.continue()**

```typescript
await route.continue(overrides?: {
  url?: string;
  method?: string;
  headers?: Record<string, string>;
  postData?: string | Buffer;
}): Promise<void>
```

**route.fulfill()**

```typescript
await route.fulfill(response: {
  status?: number;
  statusText?: string;
  headers?: Record<string, string>;
  body?: string | Buffer;
  json?: any;
  path?: string;  // Path to file
  contentType?: string;
}): Promise<void>
```

**route.abort()**

```typescript
await route.abort(errorCode?: string): Promise<void>

// Error codes:
// 'aborted' | 'accessdenied' | 'addressunreachable' | 'blockedbyclient' |
// 'blockedbyresponse' | 'connectionaborted' | 'connectionclosed' |
// 'connectionfailed' | 'connectionrefused' | 'connectionreset' |
// 'internetdisconnected' | 'namenotresolved' | 'timedout' | 'failed'
```

**route.fetch()**

```typescript
await route.fetch(overrides?: {
  url?: string;
  method?: string;
  headers?: Record<string, string>;
  postData?: string | Buffer;
  maxRedirects?: number;
  timeout?: number;
}): Promise<Response>
```

**request.url()**

```typescript
request.url(): string
```

**request.method()**

```typescript
request.method(): string  // 'GET', 'POST', etc.
```

**request.headers()**

```typescript
request.headers(): Record<string, string>
```

**request.postData()**

```typescript
request.postData(): string | null
```

**request.postDataBuffer()**

```typescript
request.postDataBuffer(): Buffer | null
```

**request.postDataJSON()**

```typescript
request.postDataJSON(): any | null
```

**request.resourceType()**

```typescript
request.resourceType(): string
// 'document' | 'stylesheet' | 'image' | 'media' | 'font' | 'script' |
// 'texttrack' | 'xhr' | 'fetch' | 'eventsource' | 'websocket' |
// 'manifest' | 'other'
```

**request.frame()**

```typescript
request.frame(): Frame
```

**request.isNavigationRequest()**

```typescript
request.isNavigationRequest(): boolean
```

**request.redirectedFrom()**

```typescript
request.redirectedFrom(): Request | null
```

**request.redirectedTo()**

```typescript
request.redirectedTo(): Request | null
```

### Appendix B: Common Patterns

**Pattern 1: Mock all API calls**

```typescript
await page.route("**/api/**", (route) => {
  route.fulfill({ json: mockData });
});
```

**Pattern 2: Block images**

```typescript
await page.route("**/*.{png,jpg,jpeg,gif,svg,webp}", (route) => {
  route.abort();
});
```

**Pattern 3: Add auth header**

```typescript
await page.route("**/api/**", (route) => {
  route.continue({
    headers: {
      ...route.request().headers(),
      Authorization: "Bearer test-token",
    },
  });
});
```

**Pattern 4: Simulate slow network**

```typescript
await page.route("**/*", async (route) => {
  await new Promise((resolve) => setTimeout(resolve, 1000));
  await route.continue();
});
```

**Pattern 5: Log all requests**

```typescript
await page.route("**/*", (route) => {
  console.log(route.request().method(), route.request().url());
  route.continue();
});
```

**Pattern 6: Modify response**

```typescript
await page.route("**/api/users", async (route) => {
  const response = await route.fetch();
  const json = await response.json();
  json.forEach((user) => (user.premium = true));
  await route.fulfill({ json });
});
```

**Pattern 7: Conditional mock**

```typescript
await page.route("**/api/**", (route) => {
  if (process.env.USE_MOCKS === "true") {
    route.fulfill({ json: mockData });
  } else {
    route.continue();
  }
});
```

**Pattern 8: Retry failed requests**

```typescript
await page.route("**/api/**", async (route, request) => {
  for (let i = 0; i < 3; i++) {
    try {
      const response = await route.fetch();
      if (response.ok()) {
        return await route.fulfill({
          status: response.status(),
          headers: await response.allHeaders(),
          body: await response.body(),
        });
      }
    } catch (error) {
      if (i === 2) throw error;
      await new Promise((resolve) => setTimeout(resolve, 1000 * (i + 1)));
    }
  }
});
```

### Appendix C: Troubleshooting Guide

**Problem: Routes not matching**

```typescript
// Check pattern syntax
await page.route("**/api/**", handler); // ✓ Correct
await page.route("/api/**", handler); // ✗ Won't match https://...

// Use regex for complex patterns
await page.route(/^https:\/\/api\.example\.com\/v[12]\//, handler);
```

**Problem: Handler called multiple times**

```typescript
// Use times option
await page.route("**/api", handler, { times: 1 });

// Or unregister after first call
const handler = async (route) => {
  await route.fulfill({ json: data });
  await page.unroute("**/api", handler);
};
await page.route("**/api", handler);
```

**Problem: Memory leak**

```typescript
// Don't store requests indefinitely
const requests = []; // ✗ Memory leak
await page.route("**/*", (route) => {
  requests.push(route.request());
  route.continue();
});

// Use weak references or limit size
const requests = [];
await page.route("**/*", (route) => {
  requests.push(route.request().url()); // ✓ Just URL
  if (requests.length > 1000) requests.shift();
  route.continue();
});
```

**Problem: Timeout errors**

```typescript
// Handler takes too long
await page.route("**/*", async (route) => {
  await someLongOperation(); // >30s
  await route.continue(); // Too late!
});

// Solution: Increase timeout or optimize handler
await page.route("**/*", async (route) => {
  // Do work asynchronously
  someLongOperation().catch(console.error);
  await route.continue(); // Don't wait
});
```

**Problem: CORS errors**

```typescript
// Add CORS headers
await page.route("**/api/**", async (route) => {
  const response = await route.fetch();
  await route.fulfill({
    status: response.status(),
    headers: {
      ...(await response.allHeaders()),
      "Access-Control-Allow-Origin": "*",
      "Access-Control-Allow-Methods": "*",
      "Access-Control-Allow-Headers": "*",
    },
    body: await response.body(),
  });
});
```

### Appendix D: Performance Benchmarks

**Test setup:**

- MacBook Pro M1, 16GB RAM
- Chromium 120.0
- Playwright 1.40
- 100 requests per test

**Results:**

| Scenario                 | Avg Latency | Throughput |
| ------------------------ | ----------- | ---------- |
| No interception          | 2ms         | 1000 req/s |
| Empty handler (continue) | 8ms         | 500 req/s  |
| JSON fulfill (1KB)       | 10ms        | 400 req/s  |
| JSON fulfill (100KB)     | 25ms        | 200 req/s  |
| Fetch + modify           | 50ms        | 100 req/s  |
| 100ms delay              | 108ms       | 50 req/s   |

### Appendix E: Further Reading

**Official Documentation:**

- [Playwright Network Interception](https://playwright.dev/docs/network)
- [Chrome DevTools Protocol](https://chromedevtools.github.io/devtools-protocol/)
- [HAR Specification](http://www.softwareishard.com/blog/har-12-spec/)

**Related Technologies:**

- [Puppeteer](https://pptr.dev/) - Similar to Playwright
- [Selenium](https://www.selenium.dev/) - Older browser automation
- [Cypress](https://www.cypress.io/) - Alternative testing framework

**Books:**

- "The Design of the UNIX Operating System" by Maurice J. Bach
- "UNIX Network Programming" by W. Richard Stevens
- "Computer Networks" by Andrew S. Tanenbaum

---

## Conclusion

Playwright's network stubbing operates at the browser protocol level, providing a powerful and flexible mechanism for controlling HTTP traffic during automated testing. By intercepting requests after security checks but before actual network I/O, it offers the best of both worlds: full control without certificate issues or proxy configuration.

The multi-layered architecture spans from OS-level networking through browser internals to high-level test APIs, with careful attention to performance, concurrency, and error handling at each layer.

Understanding these internals enables you to:

- Write more efficient and reliable tests
- Debug interception issues effectively
- Optimize performance for high-traffic scenarios
- Implement advanced patterns like stateful mocking and caching
- Make informed decisions about when to use Playwright vs. alternatives

**Total Lines:** 2030+

---

**Document End**
