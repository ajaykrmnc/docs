## Appendix D: Source Code References

### D.1 hostapd Source Files

| File | Description |
|------|-------------|
| `src/ap/hostapd.c` | Main AP daemon |
| `src/ap/beacon.c` | Beacon frame generation |
| `src/ap/ieee802_11.c` | 802.11 frame handling |
| `src/ap/sta_info.c` | Station management |
| `src/ap/wpa_auth.c` | WPA state machine |
| `src/ap/wpa_auth_ie.c` | RSN IE handling |
| `src/ap/ieee802_1x.c` | 802.1X authenticator |
| `src/ap/drv_callbacks.c` | Driver event callbacks |
| `src/ap/ap_drv_ops.c` | Driver operations |
| `src/ap/hs20.c` | Hotspot 2.0 |
| `src/ap/gas_serv.c` | GAS/ANQP server |
| `src/ap/wnm_ap.c` | 802.11v WNM |
| `src/ap/rrm.c` | 802.11k RRM |

### D.2 wpa_supplicant Source Files

| File | Description |
|------|-------------|
| `src/rsn_supp/wpa.c` | WPA supplicant state machine |
| `src/rsn_supp/wpa_ie.c` | RSN IE handling |
| `src/eap_peer/*.c` | EAP methods |
| `src/common/sae.c` | SAE implementation |
| `src/common/wpa_common.c` | Common WPA functions |

### D.3 Key Functions

```c
// Authentication handling
void handle_auth(struct hostapd_data *hapd,
                 const struct ieee80211_mgmt *mgmt,
                 size_t len, int rssi, int from_queue);

// Association handling
void handle_assoc(struct hostapd_data *hapd,
                  const struct ieee80211_mgmt *mgmt,
                  size_t len, int reassoc, int rssi);

// WPA state machine
void wpa_receive(struct wpa_authenticator *wpa_auth,
                 struct wpa_state_machine *sm,
                 u8 *data, size_t data_len);

// EAPOL transmission
void wpa_send_eapol(struct wpa_authenticator *wpa_auth,
                    struct wpa_state_machine *sm,
                    int key_info, const u8 *key_rsc,
                    const u8 *nonce, const u8 *kde,
                    size_t kde_len, int keyidx, int encr);

// PTK derivation
int wpa_derive_ptk(struct wpa_state_machine *sm,
                   const u8 *snonce, const u8 *pmk,
                   unsigned int pmk_len,
                   struct wpa_ptk *ptk,
                   int akmp, int cipher,
                   const u8 *z, size_t z_len,
                   size_t kdk_len);
```

---

