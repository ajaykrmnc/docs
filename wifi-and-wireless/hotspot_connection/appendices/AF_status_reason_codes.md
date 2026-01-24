## Appendix AF: Status and Reason Codes

### AF.1 Status Codes

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    802.11 STATUS CODES                                       │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  Common Status Codes (used in Association/Authentication Response):          │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │  Code   Name                                                        │    │
│  │  ────   ────                                                        │    │
│  │    0    SUCCESSFUL                                                  │    │
│  │    1    UNSPECIFIED_FAILURE                                         │    │
│  │    2    TDLS_WAKEUP_ALTERNATE                                       │    │
│  │    3    TDLS_WAKEUP_REJECT                                          │    │
│  │   10    CAPS_UNSUPPORTED                                            │    │
│  │   11    REASSOC_NO_ASSOC                                            │    │
│  │   12    ASSOC_DENIED_UNSPEC                                         │    │
│  │   13    NOT_SUPPORTED_AUTH_ALG                                      │    │
│  │   14    UNKNOWN_AUTH_TRANSACTION                                    │    │
│  │   15    CHALLENGE_FAIL                                              │    │
│  │   16    AUTH_TIMEOUT                                                │    │
│  │   17    AP_UNABLE_TO_HANDLE_NEW_STA                                 │    │
│  │   18    ASSOC_DENIED_RATES                                          │    │
│  │   19    ASSOC_DENIED_NOSHORT                                        │    │
│  │   22    ASSOC_DENIED_NOPBCC                                         │    │
│  │   23    ASSOC_DENIED_NOAGILITY                                      │    │
│  │   25    ASSOC_DENIED_NOSPECTRUM                                     │    │
│  │   26    ASSOC_REJECTED_BAD_POWER                                    │    │
│  │   27    ASSOC_REJECTED_BAD_SUPP_CHAN                                │    │
│  │   28    ASSOC_DENIED_NOSHORT_SLOT                                   │    │
│  │   30    ASSOC_DENIED_NO_HT                                          │    │
│  │   31    R0KH_UNREACHABLE                                            │    │
│  │   32    ASSOC_DENIED_NO_PCO                                         │    │
│  │   34    REFUSED_TEMPORARILY                                         │    │
│  │   35    ROBUST_MGMT_FRAME_POLICY_VIOLATION                          │    │
│  │   37    REQUESTED_TCLAS_NOT_SUPPORTED                               │    │
│  │   38    TCLAS_RESOURCES_EXHAUSTED                                   │    │
│  │   39    REJECTED_WITH_SUGGESTED_BSS_TRANSITION                      │    │
│  │   40    REJECT_WITH_SCHEDULE                                        │    │
│  │   41    REJECT_NO_WAKEUP_SPECIFIED                                  │    │
│  │   42    SUCCESS_POWER_SAVE_MODE                                     │    │
│  │   43    PENDING_ADMITTING_FST_SESSION                               │    │
│  │   44    PERFORMING_FST_NOW                                          │    │
│  │   45    PENDING_GAP_IN_BA_WINDOW                                    │    │
│  │   46    REJECT_U_PID_SETTING                                        │    │
│  │   53    REFUSED_EXTERNAL_REASON                                     │    │
│  │   54    REFUSED_AP_OUT_OF_MEMORY                                    │    │
│  │   55    REJECTED_EMERGENCY_SERVICE_NOT_SUPPORTED                    │    │
│  │   59    QUERY_RESP_OUTSTANDING                                      │    │
│  │   60    REQUEST_DECLINED                                            │    │
│  │   61    INVALID_PARAMETERS                                          │    │
│  │   67    REJECTED_WITH_SUGGESTED_BAND_AND_CHANNEL                    │    │
│  │   68    ASSOC_DENIED_NO_VHT                                         │    │
│  │   71    ENABLEMENT_DENIED                                           │    │
│  │   72    RESTRICTION_FROM_AUTHORIZED_GDB                             │    │
│  │   73    AUTHORIZATION_DEENABLED                                     │    │
│  │   76    FILS_AUTHENTICATION_FAILURE                                 │    │
│  │   77    UNKNOWN_AUTHENTICATION_SERVER                               │    │
│  │   78    SAE_HASH_TO_ELEMENT                                         │    │
│  │   79    SAE_PK                                                      │    │
│  │   82    DENIED_HE_NOT_SUPPORTED                                     │    │
│  │  112    ASSOC_DENIED_NO_EHT                                         │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### AF.2 Reason Codes

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    802.11 REASON CODES                                       │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  Reason Codes (used in Deauthentication/Disassociation):                     │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │  Code   Name                                                        │    │
│  │  ────   ────                                                        │    │
│  │    0    Reserved                                                    │    │
│  │    1    UNSPECIFIED                                                 │    │
│  │    2    PREV_AUTH_NOT_VALID                                         │    │
│  │    3    DEAUTH_LEAVING                                              │    │
│  │    4    DISASSOC_DUE_TO_INACTIVITY                                  │    │
│  │    5    DISASSOC_AP_BUSY                                            │    │
│  │    6    CLASS2_FRAME_FROM_NONAUTH_STA                               │    │
│  │    7    CLASS3_FRAME_FROM_NONASSOC_STA                              │    │
│  │    8    DISASSOC_STA_HAS_LEFT                                       │    │
│  │    9    STA_REQ_ASSOC_WITHOUT_AUTH                                  │    │
│  │   10    PWR_CAPABILITY_NOT_VALID                                    │    │
│  │   11    SUPPORTED_CHANNEL_NOT_VALID                                 │    │
│  │   12    BSS_TRANSITION_DISASSOC                                     │    │
│  │   13    INVALID_IE                                                  │    │
│  │   14    MICHAEL_MIC_FAILURE                                         │    │
│  │   15    4WAY_HANDSHAKE_TIMEOUT                                      │    │
│  │   16    GROUP_KEY_UPDATE_TIMEOUT                                    │    │
│  │   17    IE_IN_4WAY_DIFFERS                                          │    │
│  │   18    GROUP_CIPHER_NOT_VALID                                      │    │
│  │   19    PAIRWISE_CIPHER_NOT_VALID                                   │    │
│  │   20    AKMP_NOT_VALID                                              │    │
│  │   21    UNSUPPORTED_RSN_IE_VERSION                                  │    │
│  │   22    INVALID_RSN_IE_CAPAB                                        │    │
│  │   23    IEEE_802_1X_AUTH_FAILED                                     │    │
│  │   24    CIPHER_SUITE_REJECTED                                       │    │
│  │   25    TDLS_TEARDOWN_UNREACHABLE                                   │    │
│  │   26    TDLS_TEARDOWN_UNSPECIFIED                                   │    │
│  │   27    SSP_REQUESTED_DISASSOC                                      │    │
│  │   28    NO_SSP_ROAMING_AGREEMENT                                    │    │
│  │   29    BAD_CIPHER_OR_AKM                                           │    │
│  │   30    NOT_AUTHORIZED_THIS_LOCATION                                │    │
│  │   31    SERVICE_CHANGE_PRECLUDES_TS                                 │    │
│  │   32    UNSPECIFIED_QOS_REASON                                      │    │
│  │   33    NOT_ENOUGH_BANDWIDTH                                        │    │
│  │   34    DISASSOC_LOW_ACK                                            │    │
│  │   35    EXCEEDED_TXOP                                               │    │
│  │   36    STA_LEAVING                                                 │    │
│  │   37    END_TS_BA_DLS                                               │    │
│  │   38    UNKNOWN_TS_BA                                               │    │
│  │   39    TIMEOUT                                                     │    │
│  │   45    PEERKEY_MISMATCH                                            │    │
│  │   46    AUTHORIZED_ACCESS_LIMIT_REACHED                             │    │
│  │   47    EXTERNAL_SERVICE_REQUIREMENTS                               │    │
│  │   48    INVALID_FT_ACTION_FRAME_COUNT                               │    │
│  │   49    INVALID_PMKID                                               │    │
│  │   50    INVALID_MDE                                                 │    │
│  │   51    INVALID_FTE                                                 │    │
│  │   52    MESH_PEERING_CANCELLED                                      │    │
│  │   53    MESH_MAX_PEERS                                              │    │
│  │   54    MESH_CONFIG_POLICY_VIOLATION                                │    │
│  │   55    MESH_CLOSE_RCVD                                             │    │
│  │   56    MESH_MAX_RETRIES                                            │    │
│  │   57    MESH_CONFIRM_TIMEOUT                                        │    │
│  │   58    MESH_INVALID_GTK                                            │    │
│  │   59    MESH_INCONSISTENT_PARAMS                                    │    │
│  │   60    MESH_INVALID_SECURITY_CAP                                   │    │
│  │   61    MESH_PATH_ERROR_NO_PROXY_INFO                               │    │
│  │   62    MESH_PATH_ERROR_NO_FORWARDING_INFO                          │    │
│  │   63    MESH_PATH_ERROR_DEST_UNREACHABLE                            │    │
│  │   64    MAC_ADDRESS_ALREADY_EXISTS_IN_MBSS                          │    │
│  │   65    MESH_CHANNEL_SWITCH_REGULATORY_REQ                          │    │
│  │   66    MESH_CHANNEL_SWITCH_UNSPECIFIED                             │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

