## Appendix B: Key Derivation Functions

### B.1 PMK Derivation (PSK)

```
PMK = PBKDF2(HMAC-SHA1, passphrase, SSID, 4096, 256)

Where:
  - passphrase: 8-63 ASCII characters
  - SSID: Network name (up to 32 bytes)
  - 4096: Iteration count
  - 256: Output length in bits
```

### B.2 PTK Derivation

```
PTK = PRF-X(PMK, "Pairwise key expansion",
            Min(AA, SPA) || Max(AA, SPA) ||
            Min(ANonce, SNonce) || Max(ANonce, SNonce))

Where:
  - PMK: Pairwise Master Key (256 bits)
  - AA: Authenticator Address (AP MAC)
  - SPA: Supplicant Address (Client MAC)
  - ANonce: Authenticator Nonce (256 bits)
  - SNonce: Supplicant Nonce (256 bits)
  - X: 384 for CCMP, 512 for CCMP-256/GCMP-256

PRF-X uses HMAC-SHA1 for WPA2, HMAC-SHA256/384 for WPA3
```

### B.3 GTK Derivation

```
GTK = PRF-X(GMK, "Group key expansion",
            AA || GNonce)

Where:
  - GMK: Group Master Key (256 bits)
  - AA: Authenticator Address (AP MAC)
  - GNonce: Group Nonce (256 bits)
  - X: 128 for CCMP, 256 for CCMP-256/GCMP-256
```

### B.4 SAE Key Derivation

```
1. Generate random scalar: rand
2. Compute element: PWE = H2E(password, SSID) or H2C(password, MAC1, MAC2)
3. Compute scalar: scalar = (rand + mask) mod r
4. Compute element: element = inverse(mask * PWE)
5. Exchange commit messages
6. Compute shared secret: K = (peer_scalar * PWE + peer_element) * rand
7. Derive PMK: PMK = KDF(K, "SAE KCK and PMK", ...)
```

---

