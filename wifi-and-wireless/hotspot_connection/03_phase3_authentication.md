## Phase 3: Authentication

After selecting a network, the client initiates the authentication process.

### 3.1 Open System Authentication

For Open networks and WPA/WPA2/WPA3-Personal, Open System Authentication is used:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                       OPEN SYSTEM AUTHENTICATION                             │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  Client                                                          AP         │
│    │                                                              │         │
│    │  Authentication Request                                      │         │
│    │  ┌─────────────────────────────────────────────────────┐    │         │
│    │  │ Algorithm: Open System (0)                           │    │         │
│    │  │ Sequence Number: 1                                   │    │         │
│    │  │ Status Code: 0 (Reserved)                            │    │         │
│    │  └─────────────────────────────────────────────────────┘    │         │
│    │ ────────────────────────────────────────────────────────────►│         │
│    │                                                              │         │
│    │  Authentication Response                                     │         │
│    │  ┌─────────────────────────────────────────────────────┐    │         │
│    │  │ Algorithm: Open System (0)                           │    │         │
│    │  │ Sequence Number: 2                                   │    │         │
│    │  │ Status Code: 0 (Success)                             │    │         │
│    │  └─────────────────────────────────────────────────────┘    │         │
│    │ ◄────────────────────────────────────────────────────────────│         │
│    │                                                              │         │
│    │         ══════ Authentication Complete ══════                │         │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 3.2 SAE (Simultaneous Authentication of Equals) - WPA3

For WPA3-Personal, SAE provides stronger authentication:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    SAE AUTHENTICATION (WPA3-Personal)                        │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  Client                                                          AP         │
│    │                                                              │         │
│    │  SAE Commit                                                  │         │
│    │  ┌─────────────────────────────────────────────────────┐    │         │
│    │  │ Algorithm: SAE (3)                                   │    │         │
│    │  │ Sequence: 1 (Commit)                                 │    │         │
│    │  │ Finite Cyclic Group: 19 (256-bit ECC)               │    │         │
│    │  │ Scalar: Random value derived from password          │    │         │
│    │  │ Element: ECC point                                   │    │         │
│    │  └─────────────────────────────────────────────────────┘    │         │
│    │ ────────────────────────────────────────────────────────────►│         │
│    │                                                              │         │
│    │  SAE Commit                                                  │         │
│    │  ┌─────────────────────────────────────────────────────┐    │         │
│    │  │ Algorithm: SAE (3)                                   │    │         │
│    │  │ Sequence: 1 (Commit)                                 │    │         │
│    │  │ Scalar: AP's random value                           │    │         │
│    │  │ Element: AP's ECC point                             │    │         │
│    │  └─────────────────────────────────────────────────────┘    │         │
│    │ ◄────────────────────────────────────────────────────────────│         │
│    │                                                              │         │
│    │  SAE Confirm                                                 │         │
│    │  ┌─────────────────────────────────────────────────────┐    │         │
│    │  │ Algorithm: SAE (3)                                   │    │         │
│    │  │ Sequence: 2 (Confirm)                                │    │         │
│    │  │ Send-Confirm: Counter                                │    │         │
│    │  │ Confirm: HMAC of shared secret                       │    │         │
│    │  └─────────────────────────────────────────────────────┘    │         │
│    │ ────────────────────────────────────────────────────────────►│         │
│    │                                                              │         │
│    │  SAE Confirm                                                 │         │
│    │ ◄────────────────────────────────────────────────────────────│         │
│    │                                                              │         │
│    │    ══════ PMK Derived, Authentication Complete ══════       │         │
│                                                                              │
│  Benefits:                                                                   │
│  • Resistant to offline dictionary attacks                                  │
│  • Forward secrecy (past sessions protected even if password compromised)  │
│  • Mutual authentication (both parties prove password knowledge)           │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 3.3 Authentication State Machine (hostapd)

```c
// ieee802_11.c - Authentication handling
static void handle_auth(struct hostapd_data *hapd,
                        const struct ieee80211_mgmt *mgmt, size_t len,
                        int rssi, int from_queue)
{
    u16 auth_alg = le_to_host16(mgmt->u.auth.auth_alg);
    u16 auth_transaction = le_to_host16(mgmt->u.auth.auth_transaction);

    switch (auth_alg) {
    case WLAN_AUTH_OPEN:
        // Simple open system authentication
        // Send success response
        break;
    case WLAN_AUTH_SHARED_KEY:
        // WEP shared key (deprecated)
        break;
    case WLAN_AUTH_FT:
        // 802.11r Fast Transition
        handle_auth_ft_finish(ctx, dst, bssid, auth_transaction, status, ies, ies_len);
        break;
    case WLAN_AUTH_SAE:
        // WPA3 SAE authentication
        handle_auth_sae(hapd, sta, mgmt, len, auth_transaction, status_code);
        break;
    case WLAN_AUTH_FILS_SK:
    case WLAN_AUTH_FILS_SK_PFS:
        // Fast Initial Link Setup
        handle_auth_fils(hapd, sta, ...);
        break;
    }
}
```

---

