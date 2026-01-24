## Phase 7: Captive Portal (Optional)

If the hotspot has a captive portal enabled, the client must authenticate before accessing the internet.

### 7.1 Captive Portal Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                       CAPTIVE PORTAL ARCHITECTURE                            │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌──────────────────────────────────────────────────────────────────────┐   │
│  │                         Access Point                                  │   │
│  │  ┌────────────────────────────────────────────────────────────────┐  │   │
│  │  │                                                                 │  │   │
│  │  │  ┌─────────────┐    ┌─────────────┐    ┌─────────────────────┐ │  │   │
│  │  │  │   hostapd   │    │   portald   │    │     iptables        │ │  │   │
│  │  │  │ (WiFi Auth) │    │  (Portal    │    │   (Firewall)        │ │  │   │
│  │  │  │             │    │   Daemon)   │    │                     │ │  │   │
│  │  │  └──────┬──────┘    └──────┬──────┘    └──────────┬──────────┘ │  │   │
│  │  │         │                  │                      │            │  │   │
│  │  │         │                  │                      │            │  │   │
│  │  │         ▼                  ▼                      ▼            │  │   │
│  │  │  ┌─────────────────────────────────────────────────────────┐  │  │   │
│  │  │  │                    Client States                         │  │  │   │
│  │  │  │                                                          │  │  │   │
│  │  │  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐   │  │  │   │
│  │  │  │  │ CLIENT_NOTYET│─►│CLIENT_GATE1  │─►│CLIENT_ACCEPT │   │  │  │   │
│  │  │  │  │ (Pre-auth)   │  │  (Portal)    │  │ (Authorized) │   │  │  │   │
│  │  │  │  └──────────────┘  └──────────────┘  └──────────────┘   │  │  │   │
│  │  │  │         │                                    │           │  │  │   │
│  │  │  │         ▼                                    ▼           │  │  │   │
│  │  │  │  ┌──────────────┐                   ┌──────────────┐    │  │  │   │
│  │  │  │  │ CLIENT_DENY  │                   │CLIENT_BLACKOUT│   │  │  │   │
│  │  │  │  │ (Blocked)    │                   │ (Timed out)   │   │  │  │   │
│  │  │  │  └──────────────┘                   └──────────────┘    │  │  │   │
│  │  │  │                                                          │  │  │   │
│  │  │  └─────────────────────────────────────────────────────────┘  │  │   │
│  │  │                                                                 │  │   │
│  │  └────────────────────────────────────────────────────────────────┘  │   │
│  │                                                                       │   │
│  └──────────────────────────────────────────────────────────────────────┘   │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 7.2 HTTP Redirect Flow

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         CAPTIVE PORTAL REDIRECT FLOW                         │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  Client                        AP (portald)              Portal Server      │
│    │                              │                           │             │
│    │  HTTP Request                │                           │             │
│    │  GET http://example.com/     │                           │             │
│    │ ─────────────────────────────►                           │             │
│    │                              │                           │             │
│    │  ┌───────────────────────────┤                           │             │
│    │  │ Check client state        │                           │             │
│    │  │ State = CLIENT_NOTYET     │                           │             │
│    │  │ Intercept HTTP request    │                           │             │
│    │  └───────────────────────────┤                           │             │
│    │                              │                           │             │
│    │  HTTP 302 Redirect           │                           │             │
│    │  Location: http://192.0.2.254/portal?url=example.com     │             │
│    │ ◄─────────────────────────────                           │             │
│    │                              │                           │             │
│    │  HTTP Request to Portal      │                           │             │
│    │  GET http://192.0.2.254/portal?url=example.com           │             │
│    │ ─────────────────────────────►                           │             │
│    │                              │                           │             │
│    │  Portal Login Page           │                           │             │
│    │  ┌───────────────────────────────────────────────────┐   │             │
│    │  │ <html>                                            │   │             │
│    │  │   <form action="/login" method="POST">            │   │             │
│    │  │     <input name="username" />                     │   │             │
│    │  │     <input name="password" type="password" />     │   │             │
│    │  │     <button type="submit">Login</button>          │   │             │
│    │  │   </form>                                         │   │             │
│    │  │ </html>                                           │   │             │
│    │  └───────────────────────────────────────────────────┘   │             │
│    │ ◄─────────────────────────────                           │             │
│    │                              │                           │             │
│    │  POST /login                 │                           │             │
│    │  username=guest&password=... │                           │             │
│    │ ─────────────────────────────►                           │             │
│    │                              │                           │             │
│    │  ┌───────────────────────────┤                           │             │
│    │  │ Validate credentials      │                           │             │
│    │  │ (Local DB or RADIUS)      │                           │             │
│    │  │ Update client state       │                           │             │
│    │  │ State = CLIENT_ACCEPT     │                           │             │
│    │  │ Update iptables rules     │                           │             │
│    │  └───────────────────────────┤                           │             │
│    │                              │                           │             │
│    │  HTTP 302 Redirect           │                           │             │
│    │  Location: http://example.com/                           │             │
│    │ ◄─────────────────────────────                           │             │
│    │                              │                           │             │
│    │  ════════════════════════════════════════════════════    │             │
│    │           CLIENT NOW HAS INTERNET ACCESS                  │             │
│    │  ════════════════════════════════════════════════════    │             │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 7.3 Portal Daemon (portald) Implementation

```c
// portal.c - Main portal daemon
int main(int argc, char *argv[])
{
    // Initialize portal daemon
    portal_init();

    // Start HTTP listener on port 80
    start_http_listener(80);

    // Start HTTPS listener on port 443
    start_https_listener(443);

    // Main event loop
    while (running) {
        // Handle incoming HTTP requests
        // Check client authentication status
        // Redirect unauthenticated clients to portal
        // Allow authenticated clients through
    }
}

// redirector.c - HTTP redirect handling
void capture_client(struct client_info *client, struct http_request *req)
{
    char redirect_url[MAX_URL_LEN];

    // Build redirect URL with original destination
    snprintf(redirect_url, sizeof(redirect_url),
             "http://%s/portal?url=%s&mac=%s",
             PORTAL_IP,           // 192.0.2.254
             req->original_url,   // Original destination
             client->mac_addr);   // Client MAC for tracking

    // Send HTTP 302 redirect
    send_http_redirect(client->socket, redirect_url);
}
```

### 7.4 Firewall Rules (iptables)

```bash
# firewall.c - iptables rule management

# Pre-authentication rules (CLIENT_NOTYET)
# Allow DHCP
iptables -A FORWARD -i $IFACE -p udp --dport 67:68 -j ACCEPT
# Allow DNS (for captive portal detection)
iptables -A FORWARD -i $IFACE -p udp --dport 53 -j ACCEPT
# Redirect HTTP to portal
iptables -t nat -A PREROUTING -i $IFACE -p tcp --dport 80 \

    -j DNAT --to-destination 192.0.2.254:80
# Block all other traffic
iptables -A FORWARD -i $IFACE -j DROP

# Post-authentication rules (CLIENT_ACCEPT)
# Allow all traffic from authenticated client
iptables -I FORWARD -m mac --mac-source $CLIENT_MAC -j ACCEPT
# Remove redirect rule
iptables -t nat -D PREROUTING -m mac --mac-source $CLIENT_MAC \
    -p tcp --dport 80 -j DNAT --to-destination 192.0.2.254:80
```

### 7.5 Walled Garden

The walled garden allows access to specific sites before authentication:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           WALLED GARDEN                                      │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  Allowed before authentication:                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │ • Portal server (192.0.2.254)                                       │    │
│  │ • DNS servers                                                        │    │
│  │ • DHCP servers                                                       │    │
│  │ • Configured whitelist domains:                                      │    │
│  │   - captive.apple.com (iOS detection)                               │    │
│  │   - connectivitycheck.gstatic.com (Android detection)               │    │
│  │   - www.msftconnecttest.com (Windows detection)                     │    │
│  │   - Payment gateways (for paid hotspots)                            │    │
│  │   - Terms of service pages                                          │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  Blocked before authentication:                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │ • All other HTTP/HTTPS traffic                                      │    │
│  │ • Email (SMTP, IMAP, POP3)                                          │    │
│  │ • VPN connections                                                    │    │
│  │ • SSH, Telnet                                                        │    │
│  │ • All other protocols                                                │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 7.6 Captive Portal Detection (CNA)

Modern devices automatically detect captive portals:

| OS | Detection URL | Expected Response |
|----|---------------|-------------------|
| iOS/macOS | captive.apple.com/hotspot-detect.html | "Success" |
| Android | connectivitycheck.gstatic.com/generate_204 | HTTP 204 |
| Windows | www.msftconnecttest.com/connecttest.txt | "Microsoft Connect Test" |
| Chrome OS | clients3.google.com/generate_204 | HTTP 204 |

### 7.7 Portal Authentication Methods

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    PORTAL AUTHENTICATION METHODS                             │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  1. Click-Through (Terms Acceptance)                                        │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │ • User clicks "Accept" button                                       │    │
│  │ • No credentials required                                           │    │
│  │ • Used for free public WiFi                                         │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  2. Username/Password (Local or RADIUS)                                     │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │ • User enters credentials                                           │    │
│  │ • Validated against local database or RADIUS server                 │    │
│  │ • Used for guest networks, hotels, enterprises                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  3. Voucher/Access Code                                                     │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │ • User enters pre-generated code                                    │    │
│  │ • Time-limited or data-limited access                               │    │
│  │ • Used for paid hotspots, events                                    │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  4. Social Login (OAuth)                                                    │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │ • User logs in with Facebook, Google, etc.                          │    │
│  │ • Collects user data for marketing                                  │    │
│  │ • Used for retail, hospitality                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  5. SMS Verification                                                        │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │ • User enters phone number                                          │    │
│  │ • Receives SMS with verification code                               │    │
│  │ • Used for identity verification                                    │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  6. Payment Gateway                                                         │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │ • User pays for access (credit card, PayPal)                        │    │
│  │ • Time-based or data-based plans                                    │    │
│  │ • Used for airports, hotels, paid hotspots                          │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

