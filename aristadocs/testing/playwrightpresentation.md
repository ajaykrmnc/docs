# Playwright Internals: How does Playwright works

### What is Stubbing?

In the context of automated testing, **stubbing** refers to the practice of replacing real dependencies with controlled,
predictable substitutes. In web testing, this primarily means intercepting and
mocking network requests.

### Why Playwright's Approach is Unique

Unlike traditional HTTP proxies or in-browser mocking libraries, Playwright operates at the **browser protocol level**, providing:

- **No certificate issues** (interception before TLS)
- **Full request/response control** (headers, body, timing)
- **Programmatic API** (JavaScript/TypeScript/Python/C#)
- **Cross-browser support** (Chromium, Firefox, WebKit)
- **Process isolation** (test code separate from browser)

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

## Layer 2: Chrome DevTools Protocol

### CDP Overview

CDP is a JSON-RPC protocol over WebSocket that allows external tools to instrument Chromium.

**Protocol Structure:**

to intercept network connection

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

### CDP Communication Flow

```

┌─────────────────────────────────────────────────────┐
│ Step 1: Route Registration                          │
│ - Playwright stores route pattern in memory         │
│ - Pattern: '**/api/users'                           │
│ - Handler: fulfill function                         │
└─────────────────────────────────────────────────────┘
                    │
                    ▼
┌─────────────────────────────────────────────────────┐
│ Step 2: Enable Network Interception via CDP         │
│ - Send: Fetch.enable (CDP command)                  │
│ - Send: Network.setRequestInterception({            │
│     patterns: [{ urlPattern: '*' }]                 │
│   })                                                │
└─────────────────────────────────────────────────────┘
                    │
                    ▼
┌─────────────────────────────────────────────────────┐
│ Step 3: Browser Enables Interception                │
│ - Network service pauses requests                   │
│ - Emits: Network.requestWillBeSent                  │
│ - Emits: Fetch.requestPaused                        │
└─────────────────────────────────────────────────────┘
```

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
      │     {requestId: "1", request: {...&#125;&#125;│
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

### Phase 3: Request Lifecycle with Interception

```
┌─────────────────────────────────────────────────────────────┐
│ 1. JavaScript Execution (Renderer Process)                  │
│    fetch('https://api.example.com/api/users')               │
│    - V8 engine executes                                     │
│    - Blink creates ResourceRequest                          │
└─────────────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│ 2. IPC to Browser Process                                   │
│    Mojo IPC: network.mojom.URLLoaderFactory.CreateLoader    │
│    - Serialized request data                                │
│    - Sent over IPC channel (fd 8)                           │
└─────────────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│ 3. Network Service (Browser Process)                        │
│    - Checks: Fetch.enable active? YES                       │
│    - Action: Pause request                                  │
│    - State: Request in PAUSED queue                         │
└─────────────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│ 4. CDP Event Emission                                       │
│    Event: Fetch.requestPaused                               │
│    Payload: {                                               │
│      requestId: "interception-job-1.0",                     │
│      request: {                                             │
│        url: "https://api.example.com/api/users",            │
│        method: "GET",                                       │
│        headers: {                                           │
│          "User-Agent": "Mozilla/5.0...",                    │
│          "Accept": "application/json"                       │
│        },                                                   │
│        postData: undefined                                  │
│      },                                                     │
│      frameId: "frame-1",                                    │
│      resourceType: "Fetch"                                  │
│    }                                                        │
└─────────────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│ 5. WebSocket Transmission (fd 6 → fd 7)                     │
│    Frame Type: Text                                         │
│    Payload: JSON-serialized CDP event                       │
│    Size: ~500 bytes                                         │
│    Latency: <1ms (localhost)                                │
└─────────────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│ 6. Playwright Client Processing                             │
│    - Deserialize JSON                                       │
│    - Match route patterns (RegExp test)                     │
│    - Pattern '**/api/**' matches                            │
│    - Create Route object                                    │
│    - Call user handler                                      │
└─────────────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│ 7. User Handler Execution                                   │
│    route.fulfill({                                          │
│      status: 200,                                           │
│      headers: { 'Content-Type': 'application/json' },       │
│      body: '{"data": "mocked"}'                             │
│    })                                                       │
└─────────────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│ 8. CDP Command: Fetch.fulfillRequest                        │
│    Command: {                                               │
│      requestId: "interception-job-1.0",                     │
│      responseCode: 200,                                     │
│      responseHeaders: [                                     │
│        { name: "Content-Type", value: "application/json" }  │
│      ],                                                     │
│      body: "eyJkYXRhIjogIm1vY2tlZCJ9" (base64)             │
│    }                                                        │
└─────────────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│ 9. WebSocket Transmission (fd 6 → fd 7)                     │
│    Frame Type: Text                                         │
│    Payload: JSON-serialized CDP command                     │
└─────────────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│ 10. Browser Network Service                                 │
│     - Locate paused request by ID                           │
│     - Create synthetic URLLoaderClient response             │
│     - Populate headers and body                             │
│     - Mark as complete                                      │
└─────────────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│ 11. IPC to Renderer Process                                 │
│     Mojo IPC: network.mojom.URLLoaderClient.OnReceiveResponse│
│     - Response headers                                      │
│     - Status code: 200                                      │
│     Mojo IPC: network.mojom.URLLoaderClient.OnStartLoadingResponseBody│
│     - Response body data pipe                               │
│     Mojo IPC: network.mojom.URLLoaderClient.OnComplete      │
└─────────────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│ 12. Renderer Process (V8)                                   │
│     - fetch() Promise resolves                              │
│     - Response object created                               │
│     - await response.json() → {"data": "mocked"}            │
└─────────────────────────────────────────────────────────────┘
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
-
- [Mermaid_chart](https://www.mermaidchart.com/play?utm_source=mermaid_live_editor&utm_medium=share#pako:eNqFktFu2jAUhl_Fyq6JxLTd9KISBFISCEPAqkqmF65zEtwaO3OcpWjau9fYaD2onfBVPv-2z5dj_4m4LiG6iWrDmj3ZjneKuNF2T2FiF22htWTBjmB2UQhPY0T9_IYb0VgSN31s28f3eEyT--TndNQ0UnBmhVYkFa-2M3BeBKoMHx_qrSQ79kbU-0-qJnRsdN-CSbSy8GpRxQldsRrIkAxIwYRCyTQkX12yhJ5s2RMKU8rDUbHRnQWyZ6qUYNqrmmcRsu6UFQfAlne0F6rUfXzQ_GUNvzrXqTW0jVYtOPFK1J3xPUEeMyo1Z3JjtXGyKMjow0zrF5I5S8OhcQuuuhWuLtmA-S34hVhOTbApmOV7MKjMnB5Y0whVx8_4Hhe0ZJatjObQtmmn-En7enMmbtPH2yuoF8s3P5buNUjAhZZ0DUyS0Srz4vCfnxyRweCWnB_p2EMSIPEwwTDFkOI9Mwx3ASYesgBTDCmGzEMeIPcwx7AIMMd1Fh4KvGx50Tl7lOA8KyHlzRcYVt-rCifpOakqGMIQJ9m_pPp2meTvp1WnJPr7BhBNH-k)

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
  geolocation: { latitude: 40.7128, longitude: -74.006 },
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

**Key Takeaway:** Playwright's stubbing operates at the browser's network
service layer via CDP, intercepting requests before socket creation, resulting
in deterministic, fast, and resource-efficient tests.

