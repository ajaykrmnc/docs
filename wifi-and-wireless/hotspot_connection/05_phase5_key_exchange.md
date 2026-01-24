## Phase 5: Security Key Exchange (4-Way Handshake)

After association, the 4-Way Handshake establishes encryption keys.

### 5.1 Key Hierarchy

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           WPA/WPA2/WPA3 KEY HIERARCHY                        │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                    Master Key Sources                                │    │
│  ├─────────────────────────────────────────────────────────────────────┤    │
│  │                                                                      │    │
│  │  WPA-Personal:                    WPA-Enterprise:                    │    │
│  │  ┌──────────────────┐            ┌──────────────────┐               │    │
│  │  │   Passphrase     │            │   EAP Method     │               │    │
│  │  │  (8-63 chars)    │            │ (TLS/TTLS/PEAP)  │               │    │
│  │  └────────┬─────────┘            └────────┬─────────┘               │    │
│  │           │                               │                          │    │
│  │           ▼                               ▼                          │    │
│  │  ┌──────────────────┐            ┌──────────────────┐               │    │
│  │  │ PBKDF2(pass,SSID)│            │       MSK        │               │    │
│  │  │   4096 rounds    │            │ (Master Session  │               │    │
│  │  └────────┬─────────┘            │      Key)        │               │    │
│  │           │                      └────────┬─────────┘               │    │
│  │           │                               │                          │    │
│  │           └───────────────┬───────────────┘                          │    │
│  │                           ▼                                          │    │
│  │                  ┌──────────────────┐                                │    │
│  │                  │       PMK        │                                │    │
│  │                  │ (Pairwise Master │                                │    │
│  │                  │      Key)        │                                │    │
│  │                  │   256 bits       │                                │    │
│  │                  └────────┬─────────┘                                │    │
│  │                           │                                          │    │
│  └───────────────────────────┼──────────────────────────────────────────┘    │
│                              │                                               │
│                              ▼                                               │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                    4-Way Handshake                                   │    │
│  │                                                                      │    │
│  │  PTK = PRF(PMK + ANonce + SNonce + AA + SPA)                        │    │
│  │                                                                      │    │
│  │  Where:                                                              │    │
│  │    PMK    = Pairwise Master Key                                     │    │
│  │    ANonce = Authenticator Nonce (random from AP)                    │    │
│  │    SNonce = Supplicant Nonce (random from client)                   │    │
│  │    AA     = Authenticator Address (AP MAC)                          │    │
│  │    SPA    = Supplicant Address (Client MAC)                         │    │
│  │                                                                      │    │
│  └────────────────────────────┬────────────────────────────────────────┘    │
│                               │                                              │
│                               ▼                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                    PTK (Pairwise Transient Key)                      │    │
│  ├─────────────────────────────────────────────────────────────────────┤    │
│  │                                                                      │    │
│  │  ┌─────────────┬─────────────┬─────────────────────────────────┐    │    │
│  │  │     KCK     │     KEK     │              TK                 │    │    │
│  │  │  (128 bits) │  (128 bits) │          (128/256 bits)         │    │    │
│  │  ├─────────────┼─────────────┼─────────────────────────────────┤    │    │
│  │  │ Key         │ Key         │ Temporal Key                    │    │    │
│  │  │ Confirmation│ Encryption  │ (Data encryption)               │    │    │
│  │  │ Key         │ Key         │                                 │    │    │
│  │  │ (MIC calc)  │ (Key wrap)  │                                 │    │    │
│  │  └─────────────┴─────────────┴─────────────────────────────────┘    │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                    GTK (Group Temporal Key)                          │    │
│  ├─────────────────────────────────────────────────────────────────────┤    │
│  │                                                                      │    │
│  │  GMK (Group Master Key) ──► GTK (128/256 bits)                      │    │
│  │                                                                      │    │
│  │  Used for broadcast/multicast traffic encryption                    │    │
│  │  Shared among all clients on the same BSS                           │    │
│  │  Delivered encrypted with KEK during 4-Way Handshake                │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 5.2 4-Way Handshake Sequence

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           4-WAY HANDSHAKE                                    │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  Client (Supplicant)                                    AP (Authenticator)  │
│    │                                                              │         │
│    │                                                              │         │
│    │  ┌─────────────────────────────────────────────────────────┐│         │
│    │  │ Both parties have PMK (from password or RADIUS)         ││         │
│    │  └─────────────────────────────────────────────────────────┘│         │
│    │                                                              │         │
│    │  ════════════════════════════════════════════════════════   │         │
│    │                    MESSAGE 1 (M1)                            │         │
│    │  ════════════════════════════════════════════════════════   │         │
│    │                                                              │         │
│    │  EAPOL-Key (ANonce, Replay Counter)                         │         │
│    │  ┌─────────────────────────────────────────────────────┐    │         │
│    │  │ Key Info: Pairwise, ACK                              │    │         │
│    │  │ Key Length: 16 (CCMP) or 32 (GCMP-256)              │    │         │
│    │  │ Replay Counter: 1                                    │    │         │
│    │  │ Key Nonce: ANonce (32 bytes random)                  │    │         │
│    │  │ Key MIC: 0 (not yet computed)                        │    │         │
│    │  │ Key Data: Empty                                      │    │         │
│    │  └─────────────────────────────────────────────────────┘    │         │
│    │ ◄────────────────────────────────────────────────────────────│         │
│    │                                                              │         │
│    │  ┌─────────────────────────────────────────────────────┐    │         │
│    │  │ Client generates SNonce                              │    │         │
│    │  │ Client computes PTK = PRF(PMK, ANonce, SNonce, ...)  │    │         │
│    │  │ Client derives KCK, KEK, TK from PTK                 │    │         │
│    │  └─────────────────────────────────────────────────────┘    │         │
│    │                                                              │         │
│    │  ════════════════════════════════════════════════════════   │         │
│    │                    MESSAGE 2 (M2)                            │         │
│    │  ════════════════════════════════════════════════════════   │         │
│    │                                                              │         │
│    │  EAPOL-Key (SNonce, MIC, RSN IE)                            │         │
│    │  ┌─────────────────────────────────────────────────────┐    │         │
│    │  │ Key Info: Pairwise, MIC                              │    │         │
│    │  │ Replay Counter: 1 (same as M1)                       │    │         │
│    │  │ Key Nonce: SNonce (32 bytes random)                  │    │         │
│    │  │ Key MIC: HMAC-SHA1(KCK, EAPOL-Key frame)            │    │         │
│    │  │ Key Data: RSN IE (client's security capabilities)   │    │         │
│    │  └─────────────────────────────────────────────────────┘    │         │
│    │ ────────────────────────────────────────────────────────────►│         │
│    │                                                              │         │
│    │                         ┌────────────────────────────────────┤         │
│    │                         │ AP computes PTK using SNonce       │         │
│    │                         │ AP verifies MIC using KCK          │         │
│    │                         │ AP validates RSN IE                │         │
│    │                         └────────────────────────────────────┤         │
│    │                                                              │         │
│    │  ════════════════════════════════════════════════════════   │         │
│    │                    MESSAGE 3 (M3)                            │         │
│    │  ════════════════════════════════════════════════════════   │         │
│    │                                                              │         │
│    │  EAPOL-Key (ANonce, MIC, Install, Encrypted GTK)            │         │
│    │  ┌─────────────────────────────────────────────────────┐    │         │
│    │  │ Key Info: Pairwise, Install, ACK, MIC, Secure       │    │         │
│    │  │ Replay Counter: 2                                    │    │         │
│    │  │ Key Nonce: ANonce (same as M1)                       │    │         │
│    │  │ Key MIC: HMAC-SHA1(KCK, EAPOL-Key frame)            │    │         │
│    │  │ Key Data (encrypted with KEK):                       │    │         │
│    │  │   • RSN IE (AP's security capabilities)             │    │         │
│    │  │   • GTK KDE (Group Temporal Key)                    │    │         │
│    │  │   • IGTK KDE (Integrity GTK, if MFP enabled)        │    │         │
│    │  └─────────────────────────────────────────────────────┘    │         │
│    │ ◄────────────────────────────────────────────────────────────│         │
│    │                                                              │         │
│    │  ┌─────────────────────────────────────────────────────┐    │         │
│    │  │ Client verifies MIC                                  │    │         │
│    │  │ Client decrypts GTK using KEK                        │    │         │
│    │  │ Client installs PTK and GTK                          │    │         │
│    │  └─────────────────────────────────────────────────────┘    │         │
│    │                                                              │         │
│    │  ════════════════════════════════════════════════════════   │         │
│    │                    MESSAGE 4 (M4)                            │         │
│    │  ════════════════════════════════════════════════════════   │         │
│    │                                                              │         │
│    │  EAPOL-Key (MIC, Acknowledgment)                            │         │
│    │  ┌─────────────────────────────────────────────────────┐    │         │
│    │  │ Key Info: Pairwise, MIC, Secure                      │    │         │
│    │  │ Replay Counter: 2 (same as M3)                       │    │         │
│    │  │ Key Nonce: 0                                         │    │         │
│    │  │ Key MIC: HMAC-SHA1(KCK, EAPOL-Key frame)            │    │         │
│    │  │ Key Data: Empty                                      │    │         │
│    │  └─────────────────────────────────────────────────────┘    │         │
│    │ ────────────────────────────────────────────────────────────►│         │
│    │                                                              │         │
│    │                         ┌────────────────────────────────────┤         │
│    │                         │ AP verifies MIC                    │         │
│    │                         │ AP installs PTK                    │         │
│    │                         │ AP opens controlled port           │         │
│    │                         └────────────────────────────────────┤         │
│    │                                                              │         │
│    │  ════════════════════════════════════════════════════════   │         │
│    │           ENCRYPTED DATA COMMUNICATION BEGINS                │         │
│    │  ════════════════════════════════════════════════════════   │         │
│    │                                                              │         │
│    │  ◄═══════════════ Encrypted with TK ═══════════════════════►│         │
│    │                                                              │         │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 5.3 WPA State Machine (hostapd)

```c
// wpa_auth.c - WPA PTK state machine
SM_STATE(WPA_PTK, INITIALIZE)
{
    SM_ENTRY_MA(WPA_PTK, INITIALIZE, wpa_ptk);
    sm->keycount = 0;
    sm->PTKRequest = FALSE;
    sm->TimeoutEvt = FALSE;
    sm->TimeoutCtr = 0;
    sm->PInitAKeys = FALSE;
    sm->Pair = TRUE;
}

SM_STATE(WPA_PTK, PTKSTART)
{
    SM_ENTRY_MA(WPA_PTK, PTKSTART, wpa_ptk);
    sm->PTKRequest = FALSE;
    sm->TimeoutEvt = FALSE;
    sm->TimeoutCtr++;

    // Generate ANonce
    if (random_get_bytes(sm->ANonce, WPA_NONCE_LEN)) {
        wpa_printf(MSG_ERROR, "WPA: Failed to get random data for ANonce");
        sm->Disconnect = TRUE;
        return;
    }

    // Send Message 1
    wpa_send_eapol(sm->wpa_auth, sm, WPA_KEY_INFO_ACK | WPA_KEY_INFO_KEY_TYPE,
                   NULL, sm->ANonce, NULL, 0, 0, 0);
}

SM_STATE(WPA_PTK, PTKCALCNEGOTIATING)
{
    SM_ENTRY_MA(WPA_PTK, PTKCALCNEGOTIATING, wpa_ptk);

    // Derive PTK from PMK, ANonce, SNonce, AA, SPA
    wpa_derive_ptk(sm, sm->SNonce, sm->PMK, sm->pmk_len, &PTK);

    // Verify MIC in Message 2
    if (wpa_verify_key_mic(sm->wpa_key_mgmt, sm->pmk_len, &PTK.kck,
                           sm->last_rx_eapol_key, sm->last_rx_eapol_key_len)) {
        wpa_printf(MSG_DEBUG, "WPA: Invalid MIC in msg 2/4");
        return;
    }
}

SM_STATE(WPA_PTK, PTKINITNEGOTIATING)
{
    SM_ENTRY_MA(WPA_PTK, PTKINITNEGOTIATING, wpa_ptk);

    // Send Message 3 with GTK
    wpa_send_eapol(sm->wpa_auth, sm,
                   WPA_KEY_INFO_ACK | WPA_KEY_INFO_INSTALL |
                   WPA_KEY_INFO_KEY_TYPE | WPA_KEY_INFO_MIC |
                   WPA_KEY_INFO_SECURE | WPA_KEY_INFO_ENCR_KEY_DATA,
                   kde, kde_len, sm->ANonce, keyidx, encr);
}

SM_STATE(WPA_PTK, PTKINITDONE)
{
    SM_ENTRY_MA(WPA_PTK, PTKINITDONE, wpa_ptk);

    // Install PTK to driver
    wpa_auth_set_key(sm->wpa_auth, 0, alg, sm->addr, 0, sm->PTK.tk, tk_len);

    // Mark port as authorized
    sm->pairwise_set = TRUE;
    wpa_auth_set_eapol(sm->wpa_auth, sm->addr, WPA_EAPOL_authorized, 1);
}
```

### 5.4 EAPOL-Key Frame Format

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         EAPOL-KEY FRAME FORMAT                               │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  Offset  Size   Field                Description                            │
│  ──────  ────   ─────                ───────────                            │
│  0       1      Protocol Version     0x02 (802.1X-2004)                     │
│  1       1      Packet Type          0x03 (EAPOL-Key)                       │
│  2       2      Packet Body Length   Length of key descriptor               │
│  4       1      Descriptor Type      0x02 (RSN Key)                         │
│  5       2      Key Information      Flags (see below)                      │
│  7       2      Key Length           16 (CCMP) or 32 (GCMP-256)            │
│  9       8      Replay Counter       Monotonically increasing               │
│  17      32     Key Nonce            ANonce or SNonce                       │
│  49      16     EAPOL-Key IV         Initialization vector (legacy)         │
│  65      8      Key RSC              Receive Sequence Counter               │
│  73      8      Reserved             Must be zero                           │
│  81      16     Key MIC              Message Integrity Code                 │
│  97      2      Key Data Length      Length of Key Data field               │
│  99      var    Key Data             RSN IE, GTK, etc. (may be encrypted)  │
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                    Key Information Bits                              │    │
│  ├─────────────────────────────────────────────────────────────────────┤    │
│  │  Bit 0-2:   Key Descriptor Version (1=HMAC-MD5/RC4, 2=HMAC-SHA1/AES)│    │
│  │  Bit 3:     Key Type (0=Group, 1=Pairwise)                          │    │
│  │  Bit 4-5:   Reserved                                                 │    │
│  │  Bit 6:     Install (set in M3)                                     │    │
│  │  Bit 7:     Key ACK (set by AP in M1, M3)                           │    │
│  │  Bit 8:     Key MIC (set when MIC is present)                       │    │
│  │  Bit 9:     Secure (set after PTK installed)                        │    │
│  │  Bit 10:    Error (set on MIC failure)                              │    │
│  │  Bit 11:    Request (set by STA to request new key)                 │    │
│  │  Bit 12:    Encrypted Key Data (set when Key Data is encrypted)     │    │
│  │  Bit 13:    SMK Message (for PeerKey)                               │    │
│  │  Bit 14-15: Reserved                                                 │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

