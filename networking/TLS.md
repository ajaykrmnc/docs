# TLS Implementation Documentation

This document provides a comprehensive overview of the TLS (Transport Layer Security) implementation in the AP codebase, from the high-level architecture down to implementation details.

## Table of Contents

1. [Overview](#overview)
2. [Architecture](#architecture)
3. [TLS Library Backends](#tls-library-backends)
4. [Core Data Structures](#core-data-structures)
5. [TLS Connection Lifecycle](#tls-connection-lifecycle)
6. [Certificate Management](#certificate-management)
7. [TLS Connection Flags](#tls-connection-flags)
8. [Cipher Suites](#cipher-suites)
9. [EAP-TLS Integration](#eap-tls-integration)
10. [OCSP Support](#ocsp-support)

---

## Overview

The TLS implementation in this codebase provides secure communication for:
- **EAP-TLS**: Certificate-based authentication
- **EAP-PEAP**: Protected EAP with TLS tunnel
- **EAP-TTLS**: Tunneled TLS
- **EAP-FAST**: Flexible Authentication via Secure Tunneling
- **RADIUS communication**: Secure RADIUS server connections

The implementation supports multiple TLS library backends and provides a unified abstraction layer.

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                        EAP Methods Layer                            │
│    (eap_tls.c, eap_peap.c, eap_ttls.c, eap_fast.c)                 │
└───────────────────────────┬─────────────────────────────────────────┘
                            │
┌───────────────────────────▼─────────────────────────────────────────┐
│                     TLS Abstraction Layer                           │
│                         (tls.h)                                     │
│   - tls_init()             - tls_connection_handshake()            │
│   - tls_connection_init()  - tls_connection_encrypt()              │
│   - tls_connection_deinit()- tls_connection_decrypt()              │
│   - tls_connection_set_params()                                     │
└───────────────────────────┬─────────────────────────────────────────┘
                            │
        ┌───────────────────┼───────────────────┬─────────────────────┐
        │                   │                   │                     │
┌───────▼───────┐   ┌───────▼───────┐   ┌───────▼───────┐   ┌─────────▼─────────┐
│  tls_openssl.c │   │ tls_wolfssl.c │   │ tls_gnutls.c  │   │  tls_internal.c   │
│   (OpenSSL)    │   │  (wolfSSL)    │   │   (GnuTLS)    │   │ (Internal TLS)    │
└───────┬────────┘   └───────┬───────┘   └───────┬───────┘   └─────────┬─────────┘
        │                    │                   │                     │
┌───────▼────────────────────▼───────────────────▼─────────────────────▼─────────┐
│                        Native TLS Libraries                                     │
└─────────────────────────────────────────────────────────────────────────────────┘
```

### Source File Locations

| Component | Path |
|-----------|------|
| TLS Header | `src/hostapd-2.10/src/crypto/tls.h` |
| OpenSSL Backend | `src/hostapd-2.10/src/crypto/tls_openssl.c` |
| wolfSSL Backend | `src/hostapd-2.10/src/crypto/tls_wolfssl.c` |
| GnuTLS Backend | `src/hostapd-2.10/src/crypto/tls_gnutls.c` |
| Internal TLS | `src/hostapd-2.10/src/tls/tlsv1_*.c` |
| OCSP Support | `src/hostapd-2.10/src/crypto/tls_openssl_ocsp.c` |

---

## TLS Library Backends

The codebase supports multiple TLS library implementations:

### 1. OpenSSL (`tls_openssl.c`)
- **Most feature-complete** implementation
- Supports all TLS versions (1.0, 1.1, 1.2, 1.3)
- Full OCSP stapling support
- Engine support for hardware tokens (PKCS#11, TPM)
- Suite B cryptography support

### 2. wolfSSL (`tls_wolfssl.c`)
- Lightweight alternative to OpenSSL
- Good for embedded systems
- Supports TLS 1.0-1.3

### 3. GnuTLS (`tls_gnutls.c`)
- GPL-compatible alternative
- OCSP support (version 3.1.3+)
- Limited engine support compared to OpenSSL

### 4. Internal TLS (`tls_internal.c`)
- Standalone implementation (no external dependencies)
- Uses internal crypto (libtommath)
- Suitable for minimal deployments

### 5. No TLS (`tls_none.c`)
- Stub implementation for builds without TLS support
- All functions return failure or no-op

---

## Core Data Structures

### `struct tls_config`
Global TLS library configuration:

```c
struct tls_config {
    const char *opensc_engine_path;    // OpenSC engine path
    const char *pkcs11_engine_path;    // PKCS#11 engine path
    const char *pkcs11_module_path;    // PKCS#11 module path
    int fips_mode;                     // Enable FIPS mode
    int cert_in_cb;                    // Include cert in callback
    const char *openssl_ciphers;       // Cipher suite configuration
    unsigned int tls_session_lifetime; // Session cache lifetime
    unsigned int crl_reload_interval;  // CRL reload interval
    unsigned int tls_flags;            // Global TLS flags
    void (*event_cb)(...);             // Event callback function
    void *cb_ctx;                      // Callback context
};
```

### `struct tls_connection_params`
Per-connection TLS parameters:

```c
struct tls_connection_params {
    // CA Certificate
    const char *ca_cert;           // CA cert file path
    const u8 *ca_cert_blob;        // CA cert as blob
    size_t ca_cert_blob_len;       // Blob length
    const char *ca_path;           // CA certificates directory

    // Certificate Matching
    const char *subject_match;     // Subject DN match string
    const char *altsubject_match;  // Alt subject match
    const char *suffix_match;      // DNS suffix match
    const char *domain_match;      // Domain name match

    // Client Certificate
    const char *client_cert;       // Client cert file
    const u8 *client_cert_blob;    // Client cert blob

    // Private Key
    const char *private_key;       // Private key file
    const u8 *private_key_blob;    // Private key blob
    const char *private_key_passwd;// Key password

    // DH Parameters
    const char *dh_file;           // DH parameters file

    // Engine/Hardware Token (OpenSSL-specific)
    int engine;                    // Use engine for private key
    const char *engine_id;         // Engine identifier
    const char *pin;               // Token PIN
    const char *key_id;            // Key ID in engine

    // Cipher Configuration
    const char *openssl_ciphers;   // Cipher suite string
    const char *openssl_ecdh_curves; // ECDH curves

    // Flags and OCSP
    unsigned int flags;            // TLS_CONN_* flags
    const char *ocsp_stapling_response;  // OCSP response file
};
```

### `struct tls_connection`
Opaque connection handle (implementation-specific)

---

## TLS Connection Lifecycle

### 1. Initialization

```c
// Initialize TLS library (once per application)
void *tls_ctx = tls_init(&tls_config);

// Create a new connection
struct tls_connection *conn = tls_connection_init(tls_ctx);

// Configure connection parameters
tls_connection_set_params(tls_ctx, conn, &params);
```

### 2. Handshake

```c
// Client-side handshake
struct wpabuf *out_data;
struct wpabuf *appl_data = NULL;

// First call with NULL to generate ClientHello
out_data = tls_connection_handshake(tls_ctx, conn, NULL, &appl_data);

// Subsequent calls with server response
while (!tls_connection_established(tls_ctx, conn)) {
    // Send out_data to server, receive response
    struct wpabuf *in_data = /* receive from server */;
    out_data = tls_connection_handshake(tls_ctx, conn, in_data, &appl_data);
}

// Server-side handshake
out_data = tls_connection_server_handshake(tls_ctx, conn, in_data, &appl_data);
```

### 3. Data Transfer

```c
// Encrypt data for transmission
struct wpabuf *encrypted = tls_connection_encrypt(tls_ctx, conn, plaintext);

// Decrypt received data
struct wpabuf *decrypted = tls_connection_decrypt(tls_ctx, conn, ciphertext);
```

### 4. Cleanup

```c
// Close connection
tls_connection_deinit(tls_ctx, conn);

// Cleanup TLS library
tls_deinit(tls_ctx);
```

---

## Certificate Management

### Certificate Verification Callback

The TLS implementation uses `tls_verify_cb()` for certificate chain validation:

```c
static int tls_verify_cb(int preverify_ok, X509_STORE_CTX *x509_ctx) {
    // Get certificate at current depth
    X509 *cert = X509_STORE_CTX_get_current_cert(x509_ctx);
    int depth = X509_STORE_CTX_get_error_depth(x509_ctx);

    // Perform custom validation:
    // - Subject matching
    // - Alt subject matching
    // - Domain suffix matching
    // - Certificate subject DN checking

    return preverify_ok;
}
```

### Certificate Validation Options

| Option | Description |
|--------|-------------|
| `subject_match` | Exact subject DN match |
| `altsubject_match` | Alternative subject match |
| `suffix_match` | Domain suffix matching (supports wildcards) |
| `domain_match` | Exact domain matching |
| `check_cert_subject` | Custom subject field checking |

### TLS Failure Reasons

```c
enum tls_fail_reason {
    TLS_FAIL_UNSPECIFIED = 0,
    TLS_FAIL_UNTRUSTED = 1,        // Untrusted CA
    TLS_FAIL_REVOKED = 2,          // Certificate revoked
    TLS_FAIL_NOT_YET_VALID = 3,    // Certificate not yet valid
    TLS_FAIL_EXPIRED = 4,          // Certificate expired
    TLS_FAIL_SUBJECT_MISMATCH = 5, // Subject mismatch
    TLS_FAIL_ALTSUBJECT_MISMATCH = 6,
    TLS_FAIL_BAD_CERTIFICATE = 7,
    TLS_FAIL_SERVER_CHAIN_PROBE = 8,
    TLS_FAIL_DOMAIN_SUFFIX_MISMATCH = 9,
    TLS_FAIL_DOMAIN_MISMATCH = 10,
    TLS_FAIL_INSUFFICIENT_KEY_LEN = 11,
    TLS_FAIL_DN_MISMATCH = 12,
};
```

---

## TLS Connection Flags

Connection behavior is controlled via `TLS_CONN_*` flags:

### Version Control Flags

| Flag | Bit | Description |
|------|-----|-------------|
| `TLS_CONN_DISABLE_TLSv1_0` | 8 | Disable TLS 1.0 |
| `TLS_CONN_DISABLE_TLSv1_1` | 5 | Disable TLS 1.1 |
| `TLS_CONN_DISABLE_TLSv1_2` | 6 | Disable TLS 1.2 |
| `TLS_CONN_DISABLE_TLSv1_3` | 13 | Disable TLS 1.3 |
| `TLS_CONN_ENABLE_TLSv1_0` | 14 | Explicitly enable TLS 1.0 |
| `TLS_CONN_ENABLE_TLSv1_1` | 15 | Explicitly enable TLS 1.1 |
| `TLS_CONN_ENABLE_TLSv1_2` | 16 | Explicitly enable TLS 1.2 |

### Security Flags

| Flag | Bit | Description |
|------|-----|-------------|
| `TLS_CONN_ALLOW_SIGN_RSA_MD5` | 0 | Allow RSA-MD5 signatures |
| `TLS_CONN_DISABLE_TIME_CHECKS` | 1 | Skip certificate time validation |
| `TLS_CONN_DISABLE_SESSION_TICKET` | 2 | Disable TLS session tickets |
| `TLS_CONN_ALLOW_UNSAFE_RENEGOTIATION` | 18 | Allow unsafe renegotiation |

### OCSP Flags

| Flag | Bit | Description |
|------|-----|-------------|
| `TLS_CONN_REQUEST_OCSP` | 3 | Request OCSP stapling |
| `TLS_CONN_REQUIRE_OCSP` | 4 | Require valid OCSP response |
| `TLS_CONN_REQUIRE_OCSP_ALL` | 10 | Require OCSP for all certs |

### Suite B / EAP Flags

| Flag | Bit | Description |
|------|-----|-------------|
| `TLS_CONN_EAP_FAST` | 7 | EAP-FAST specific handling |
| `TLS_CONN_EXT_CERT_CHECK` | 9 | External certificate check |
| `TLS_CONN_SUITEB` | 11 | Suite B 192-bit security |
| `TLS_CONN_SUITEB_NO_ECDH` | 12 | Suite B without ECDH |
| `TLS_CONN_TEAP_ANON_DH` | 17 | TEAP anonymous DH |

### Usage Example

```c
struct tls_connection_params params;
params.flags = TLS_CONN_DISABLE_TLSv1_0 |
               TLS_CONN_DISABLE_TLSv1_1 |
               TLS_CONN_REQUIRE_OCSP;
```

---

## Cipher Suites

### Built-in Cipher Identifiers

```c
enum {
    TLS_CIPHER_NONE,
    TLS_CIPHER_RC4_SHA,              // 0x0005
    TLS_CIPHER_AES128_SHA,           // 0x002f
    TLS_CIPHER_RSA_DHE_AES128_SHA,   // 0x0031
    TLS_CIPHER_ANON_DH_AES128_SHA,   // 0x0034
    TLS_CIPHER_RSA_DHE_AES256_SHA,   // 0x0039
    TLS_CIPHER_AES256_SHA,           // 0x0035
};
```

### Suite B Configuration

Suite B (NSA Suite B cryptography) uses specific cipher suites:

```c
// Suite B with ECDH
const char *ciphers = "ECDHE-RSA-AES256-GCM-SHA384:DHE-RSA-AES256-GCM-SHA384";

// Suite B without ECDH
const char *ciphers = "DHE-RSA-AES256-GCM-SHA384";
```

### Custom Cipher Configuration

```c
// Via connection params
params.openssl_ciphers = "HIGH:!aNULL:!MD5";

// Via global config
tls_config.openssl_ciphers = "ECDHE+AESGCM:DHE+AESGCM";
```

---

## EAP-TLS Integration

### EAP-TLS Flow

```
Client                                    Server
   │                                         │
   │◄──────── EAP-Request/Identity ─────────│
   │                                         │
   │────────── EAP-Response/Identity ───────►│
   │                                         │
   │◄──────── EAP-Request/EAP-TLS ──────────│ (TLS Start)
   │                                         │
   │────────── EAP-Response/EAP-TLS ────────►│ (ClientHello)
   │                                         │
   │◄──────── EAP-Request/EAP-TLS ──────────│ (ServerHello, Certificate,
   │                                         │  ServerKeyExchange,
   │                                         │  CertificateRequest,
   │                                         │  ServerHelloDone)
   │                                         │
   │────────── EAP-Response/EAP-TLS ────────►│ (Certificate, ClientKeyExchange,
   │                                         │  CertificateVerify,
   │                                         │  ChangeCipherSpec, Finished)
   │                                         │
   │◄──────── EAP-Request/EAP-TLS ──────────│ (ChangeCipherSpec, Finished)
   │                                         │
   │────────── EAP-Response/EAP-TLS ────────►│ (Empty)
   │                                         │
   │◄──────── EAP-Success ──────────────────│
   │                                         │
```

### EAP-TLS Initialization

```c
// In eap_tls.c
static void *eap_tls_init(struct eap_sm *sm)
{
    struct eap_tls_data *data = os_zalloc(sizeof(*data));

    // Initialize TLS for EAP-TLS
    if (eap_peer_tls_ssl_init(sm, &data->ssl, config, EAP_TYPE_TLS)) {
        wpa_printf(MSG_INFO, "EAP-TLS: Failed to initialize SSL.");
        return NULL;
    }

    data->eap_type = EAP_TYPE_TLS;
    return data;
}
```

### PEAP (Protected EAP)

PEAP creates a TLS tunnel for inner EAP method:

```c
// In eap_peap.c
static void *eap_peap_init(struct eap_sm *sm)
{
    struct eap_peap_data *data = os_zalloc(sizeof(*data));

    data->peap_version = EAP_PEAP_VERSION;
    data->crypto_binding = OPTIONAL_BINDING;

    // Initialize TLS tunnel
    if (eap_peer_tls_ssl_init(sm, &data->ssl, config, EAP_TYPE_PEAP)) {
        return NULL;
    }

    // Select phase 2 methods
    eap_peer_select_phase2_methods(config, "auth=",
                                   &data->phase2_types,
                                   &data->num_phase2_types, 0);
    return data;
}
```

---

## OCSP Support

### OCSP (Online Certificate Status Protocol)

OCSP provides real-time certificate revocation checking.

### OCSP Stapling

```c
// Request OCSP stapling from server
params.flags |= TLS_CONN_REQUEST_OCSP;

// Require valid OCSP response
params.flags |= TLS_CONN_REQUIRE_OCSP;

// Require OCSP for entire certificate chain
params.flags |= TLS_CONN_REQUIRE_OCSP_ALL;
```

### OCSP Response Validation

```c
// In tls_openssl_ocsp.c
enum ocsp_result check_ocsp_resp(SSL_CTX *ssl_ctx, SSL *ssl,
                                  X509 *cert, X509 *issuer,
                                  X509 *issuer_issuer)
{
    // Parse OCSP response
    // Verify signature
    // Check response validity time
    // Match certificate serial number

    return OCSP_GOOD;  // or OCSP_REVOKED, OCSP_NO_RESPONSE, OCSP_INVALID
}
```

### OCSP Results

| Result | Description |
|--------|-------------|
| `OCSP_GOOD` | Certificate is valid |
| `OCSP_REVOKED` | Certificate has been revoked |
| `OCSP_NO_RESPONSE` | No OCSP response received |
| `OCSP_INVALID` | OCSP response is invalid |

---

## TLS Events

### Event Types

```c
enum tls_event {
    TLS_CERT_CHAIN_SUCCESS,         // Certificate chain validated
    TLS_CERT_CHAIN_FAILURE,         // Certificate chain validation failed
    TLS_PEER_CERTIFICATE,           // Peer certificate received
    TLS_ALERT,                      // TLS alert received
    TLS_UNSAFE_RENEGOTIATION_DISABLED,  // Unsafe renegotiation blocked
};
```

### Event Callback

```c
void tls_event_handler(void *ctx, enum tls_event ev,
                       union tls_event_data *data)
{
    switch (ev) {
    case TLS_CERT_CHAIN_FAILURE:
        wpa_printf(MSG_WARNING, "TLS: Certificate validation failed: %s",
                   data->cert_fail.reason_txt);
        break;
    case TLS_PEER_CERTIFICATE:
        wpa_printf(MSG_DEBUG, "TLS: Peer cert subject: %s",
                   data->peer_cert.subject);
        break;
    case TLS_ALERT:
        wpa_printf(MSG_WARNING, "TLS: Alert %s: %s",
                   data->alert.type, data->alert.description);
        break;
    }
}
```

---

## Key Export and Session Resumption

### Key Material Export (RFC 5705)

```c
// Export keying material for EAP methods
int tls_connection_export_key(void *tls_ctx, struct tls_connection *conn,
                              const char *label,
                              const u8 *context, size_t context_len,
                              u8 *out, size_t out_len);
```

### Session Resumption

```c
// Check if session was resumed
int resumed = tls_connection_resumed(tls_ctx, conn);

// Configure session caching
tls_config.tls_session_lifetime = 86400;  // 24 hours

// Remove session to prevent resumption
tls_connection_remove_session(conn);
```

---

## Engine Support (Hardware Tokens)

### TPM/PKCS#11 Integration

```c
struct tls_connection_params params;

// Enable engine
params.engine = 1;
params.engine_id = "pkcs11";
params.pin = "1234";
params.key_id = "pkcs11:token=MyToken;object=MyKey";
params.cert_id = "pkcs11:token=MyToken;object=MyCert";
```

### Engine Initialization (OpenSSL)

```c
// Load PKCS#11 engine
if (conf->pkcs11_engine_path || conf->pkcs11_module_path) {
    tls_engine_load_dynamic_pkcs11(conf->pkcs11_engine_path,
                                   conf->pkcs11_module_path);
}
```

---

## Internal TLS Implementation

For deployments without external TLS libraries, an internal implementation exists:

### Components

| File | Purpose |
|------|---------|
| `tlsv1_client.c` | TLS client state machine |
| `tlsv1_server.c` | TLS server state machine |
| `tlsv1_common.c` | Shared TLS utilities |
| `tlsv1_record.c` | TLS record layer |
| `tlsv1_cred.c` | Credential management |
| `x509v3.c` | X.509 certificate parsing |
| `rsa.c` | RSA operations |
| `pkcs1.c` / `pkcs5.c` / `pkcs8.c` | PKCS standards support |

---

## Debugging

### Debug Logging

```c
// Enable wolfSSL debugging
#ifdef DEBUG_WOLFSSL
wolfSSL_Debugging_ON();
#endif

// GnuTLS debug level
if (wpa_debug_show_keys)
    gnutls_global_set_log_level(11);
```

### Getting TLS Version and Cipher

```c
char version[32], cipher[64];

tls_get_version(tls_ctx, conn, version, sizeof(version));
tls_get_cipher(tls_ctx, conn, cipher, sizeof(cipher));

wpa_printf(MSG_DEBUG, "TLS: Using %s with %s", version, cipher);
```

