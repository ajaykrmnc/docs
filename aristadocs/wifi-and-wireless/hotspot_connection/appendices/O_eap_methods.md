## Appendix O: EAP Method Deep Dive

### O.1 EAP-TLS (Transport Layer Security)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    EAP-TLS AUTHENTICATION FLOW                               │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  Client                    AP                      RADIUS Server             │
│     │                      │                            │                    │
│     │◄─────────────────────│ EAP-Request/Identity       │                    │
│     │                      │                            │                    │
│     │ EAP-Response/Identity ─────────────────────────►│                    │
│     │ (username@realm)     │                            │                    │
│     │                      │                            │                    │
│     │◄─────────────────────│ EAP-Request/EAP-TLS       │                    │
│     │                      │ (TLS Start)                │                    │
│     │                      │                            │                    │
│     │ EAP-Response/EAP-TLS ─────────────────────────►│                    │
│     │ (TLS ClientHello)    │                            │                    │
│     │                      │                            │                    │
│     │◄─────────────────────│ EAP-Request/EAP-TLS       │                    │
│     │                      │ (TLS ServerHello,          │                    │
│     │                      │  Certificate,              │                    │
│     │                      │  CertificateRequest,       │                    │
│     │                      │  ServerHelloDone)          │                    │
│     │                      │                            │                    │
│     │ EAP-Response/EAP-TLS ─────────────────────────►│                    │
│     │ (Certificate,        │                            │                    │
│     │  ClientKeyExchange,  │                            │                    │
│     │  CertificateVerify,  │                            │                    │
│     │  ChangeCipherSpec,   │                            │                    │
│     │  Finished)           │                            │                    │
│     │                      │                            │                    │
│     │◄─────────────────────│ EAP-Request/EAP-TLS       │                    │
│     │                      │ (ChangeCipherSpec,         │                    │
│     │                      │  Finished)                 │                    │
│     │                      │                            │                    │
│     │ EAP-Response/EAP-TLS ─────────────────────────►│                    │
│     │ (empty)              │                            │                    │
│     │                      │                            │                    │
│     │◄─────────────────────│ EAP-Success               │                    │
│     │                      │ + MPPE Keys                │                    │
│     │                      │                            │                    │
│                                                                              │
│  Key Derivation:                                                             │
│  • TLS PRF generates Master Secret                                           │
│  • MSK = TLS-PRF(Master Secret, "client EAP encryption", 64 bytes)          │
│  • EMSK = TLS-PRF(Master Secret, "client EAP encryption", 64 bytes, offset) │
│  • PMK = First 32 bytes of MSK                                               │
│                                                                              │
│  Certificate Requirements:                                                   │
│  • Client certificate with Extended Key Usage: Client Authentication        │
│  • Server certificate with Extended Key Usage: Server Authentication        │
│  • Both signed by trusted CA                                                 │
│  • CRL or OCSP for revocation checking                                       │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### O.2 EAP-TTLS (Tunneled TLS)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    EAP-TTLS AUTHENTICATION FLOW                              │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  Phase 1: TLS Tunnel Establishment                                           │
│  ─────────────────────────────────────                                       │
│  Client                    AP                      RADIUS Server             │
│     │                      │                            │                    │
│     │◄─────────────────────│ EAP-Request/Identity       │                    │
│     │                      │                            │                    │
│     │ EAP-Response/Identity ─────────────────────────►│                    │
│     │ (anonymous@realm)    │                            │                    │
│     │                      │                            │                    │
│     │◄─────────────────────│ EAP-Request/EAP-TTLS      │                    │
│     │                      │ (TLS Start)                │                    │
│     │                      │                            │                    │
│     │ EAP-Response/EAP-TTLS ────────────────────────►│                    │
│     │ (TLS ClientHello)    │                            │                    │
│     │                      │                            │                    │
│     │◄─────────────────────│ EAP-Request/EAP-TTLS      │                    │
│     │                      │ (TLS ServerHello,          │                    │
│     │                      │  Certificate,              │                    │
│     │                      │  ServerHelloDone)          │                    │
│     │                      │                            │                    │
│     │ EAP-Response/EAP-TTLS ────────────────────────►│                    │
│     │ (ClientKeyExchange,  │                            │                    │
│     │  ChangeCipherSpec,   │                            │                    │
│     │  Finished)           │                            │                    │
│     │                      │                            │                    │
│     │◄─────────────────────│ EAP-Request/EAP-TTLS      │                    │
│     │                      │ (ChangeCipherSpec,         │                    │
│     │                      │  Finished)                 │                    │
│     │                      │                            │                    │
│  ═══════════════════════════════════════════════════════════════════════    │
│                    TLS TUNNEL ESTABLISHED                                    │
│  ═══════════════════════════════════════════════════════════════════════    │
│                                                                              │
│  Phase 2: Inner Authentication (inside TLS tunnel)                           │
│  ─────────────────────────────────────────────────                           │
│     │                      │                            │                    │
│     │ EAP-Response/EAP-TTLS ────────────────────────►│                    │
│     │ (AVP: User-Name,     │                            │                    │
│     │  AVP: User-Password) │                            │                    │
│     │                      │                            │                    │
│     │◄─────────────────────│ EAP-Success               │                    │
│     │                      │ + MPPE Keys                │                    │
│     │                      │                            │                    │
│                                                                              │
│  Inner Methods Supported:                                                    │
│  • PAP (Password Authentication Protocol)                                    │
│  • CHAP (Challenge Handshake Authentication Protocol)                        │
│  • MS-CHAPv2 (Microsoft CHAP version 2)                                      │
│  • EAP-MD5                                                                   │
│  • EAP-MSCHAPv2                                                              │
│  • EAP-GTC (Generic Token Card)                                              │
│                                                                              │
│  Advantages:                                                                 │
│  • Server certificate only (no client certificate needed)                    │
│  • Identity protection (real username sent inside tunnel)                    │
│  • Supports legacy authentication methods                                    │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### O.3 EAP-PEAP (Protected EAP)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    EAP-PEAP AUTHENTICATION FLOW                              │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  Phase 1: TLS Tunnel (same as EAP-TTLS)                                      │
│  ─────────────────────────────────────                                       │
│  • TLS handshake with server certificate                                     │
│  • Client validates server certificate                                       │
│  • TLS tunnel established                                                    │
│                                                                              │
│  Phase 2: Inner EAP (inside TLS tunnel)                                      │
│  ─────────────────────────────────────                                       │
│  Client                    AP                      RADIUS Server             │
│     │                      │                            │                    │
│     │◄─────────────────────│ EAP-Request/Identity       │                    │
│     │                      │ (inside tunnel)            │                    │
│     │                      │                            │                    │
│     │ EAP-Response/Identity ─────────────────────────►│                    │
│     │ (real username)      │                            │                    │
│     │                      │                            │                    │
│     │◄─────────────────────│ EAP-Request/EAP-MSCHAPv2  │                    │
│     │                      │ (Challenge)                │                    │
│     │                      │                            │                    │
│     │ EAP-Response/EAP-MSCHAPv2 ─────────────────────►│                    │
│     │ (Response)           │                            │                    │
│     │                      │                            │                    │
│     │◄─────────────────────│ EAP-Request/EAP-MSCHAPv2  │                    │
│     │                      │ (Success + Authenticator)  │                    │
│     │                      │                            │                    │
│     │ EAP-Response/EAP-MSCHAPv2 ─────────────────────►│                    │
│     │ (empty)              │                            │                    │
│     │                      │                            │                    │
│     │◄─────────────────────│ EAP-Success               │                    │
│     │                      │ + MPPE Keys                │                    │
│     │                      │                            │                    │
│                                                                              │
│  PEAP Versions:                                                              │
│  • PEAPv0 (Microsoft): Inner method is EAP-MSCHAPv2                         │
│  • PEAPv1 (Cisco): Inner method is EAP-GTC                                  │
│                                                                              │
│  Cryptobinding:                                                              │
│  • Binds inner and outer authentication                                      │
│  • Prevents man-in-the-middle attacks                                        │
│  • Uses Compound MAC (CMAC)                                                  │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### O.4 EAP-SIM/AKA/AKA' (Cellular Authentication)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    EAP-SIM AUTHENTICATION FLOW                               │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  Client (with SIM)         AP                      RADIUS + HLR/HSS         │
│     │                      │                            │                    │
│     │◄─────────────────────│ EAP-Request/Identity       │                    │
│     │                      │                            │                    │
│     │ EAP-Response/Identity ─────────────────────────►│                    │
│     │ (1<IMSI>@realm)      │                            │                    │
│     │                      │                            │                    │
│     │◄─────────────────────│ EAP-Request/SIM-Start     │                    │
│     │                      │ (AT_VERSION_LIST,          │                    │
│     │                      │  AT_PERMANENT_ID_REQ)      │                    │
│     │                      │                            │                    │
│     │ EAP-Response/SIM-Start ────────────────────────►│                    │
│     │ (AT_NONCE_MT,        │                            │                    │
│     │  AT_SELECTED_VERSION,│                            │                    │
│     │  AT_IDENTITY)        │                            │                    │
│     │                      │                            │                    │
│     │                      │                            │ ──► HLR/HSS       │
│     │                      │                            │ Get triplets       │
│     │                      │                            │ (RAND, SRES, Kc)   │
│     │                      │                            │ ◄──                │
│     │                      │                            │                    │
│     │◄─────────────────────│ EAP-Request/SIM-Challenge │                    │
│     │                      │ (AT_RAND x 2-3,            │                    │
│     │                      │  AT_MAC)                   │                    │
│     │                      │                            │                    │
│     │ ──► SIM Card         │                            │                    │
│     │ Run A3/A8 algorithm  │                            │                    │
│     │ Get SRES, Kc         │                            │                    │
│     │ ◄──                  │                            │                    │
│     │                      │                            │                    │
│     │ EAP-Response/SIM-Challenge ────────────────────►│                    │
│     │ (AT_MAC)             │                            │                    │
│     │                      │                            │                    │
│     │◄─────────────────────│ EAP-Success               │                    │
│     │                      │ + MPPE Keys                │                    │
│     │                      │                            │                    │
│                                                                              │
│  Key Derivation:                                                             │
│  • MK = SHA1(Identity | Kc values | NONCE_MT | Version List | Selected Ver) │
│  • MSK = PRF(MK)[0:64]                                                       │
│  • EMSK = PRF(MK)[64:128]                                                    │
│  • PMK = MSK[0:32]                                                           │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│                    EAP-AKA vs EAP-AKA' COMPARISON                            │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  Feature              EAP-AKA              EAP-AKA'                          │
│  ───────              ───────              ────────                          │
│  Network              3G/4G USIM           4G/5G USIM                        │
│  Algorithm            MILENAGE             MILENAGE + SHA-256                │
│  Key Derivation       SHA-1                SHA-256                           │
│  Binding              None                 AT_KDF, AT_KDF_INPUT              │
│  Security             Good                 Better (5G ready)                 │
│  Identity             0<IMSI>@realm        6<IMSI>@realm                     │
│                                                                              │
│  EAP-AKA' Improvements:                                                      │
│  • Stronger key derivation function                                          │
│  • Network name binding (prevents roaming attacks)                           │
│  • Required for 5G networks                                                  │
│  • Backward compatible with EAP-AKA                                          │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

