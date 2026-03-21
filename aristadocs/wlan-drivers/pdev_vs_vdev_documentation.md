# PDEV vs VDEV: Comprehensive Documentation

## Overview

In the WLAN Object Manager architecture, **PDEV (Physical Device)** and **VDEV (Virtual Device)** are two
fundamental object types that represent different layers of the wireless stack hierarchy. Understanding their
differences is critical for proper driver development and interface design.

## Object Hierarchy

```
PSOC (Physical SoC)
└── PDEV (Physical Device / Radio)
└── VDEV (Virtual Device / Interface)
└── PEER (Connected Station/Client)
```

---

## PDEV (Physical Device)

### Definition

PDEV represents a **physical radio interface** in the system. It corresponds to actual hardware - typically a
radio chip or band (e.g., 2.4GHz, 5GHz, 6GHz radios).

### Key Characteristics

| Attribute       | Description                                    |
| --------------- | ---------------------------------------------- |
| **Scope**       | Hardware-level, represents physical radio      |
| **Quantity**    | Limited by hardware (typically 1-3 per device) |
| **Identity**    | Has unique `pdev_id` assigned by PSOC          |
| **MAC Address** | Hardware MAC address of the radio              |
| **Lifetime**    | Tied to hardware availability                  |

### Core Structure (`wlan_objmgr_pdev`)

```c
struct wlan_objmgr_pdev {
  struct wlan_chan_list *current_chan_list;     // Active channel list
  struct wlan_objmgr_pdev_nif  pdev_nif;        // Network interface info
  struct wlan_objmgr_pdev_objmgr pdev_objmgr;   // Object manager info
  struct wlan_objmgr_pdev_mlme   pdev_mlme;     // MLME operations
  void *pdev_comp_priv_obj[WLAN_UMAC_MAX_COMPONENTS];
  QDF_STATUS obj_status[WLAN_UMAC_MAX_COMPONENTS];
  WLAN_OBJ_STATE obj_state;
  target_pdev_info_t *tgt_if_handle;            // Target interface
  qdf_spinlock_t pdev_lock;
  bool standby_active;
};
```

### PDEV Flags (Hardware/Radio Capabilities)

| Flag                                 | Purpose                    |
| ------------------------------------ | -------------------------- |
| `WLAN_PDEV_F_SCAN`                   | Radio is scanning          |
| `WLAN_PDEV_F_SHSLOT`                 | Short slot time enabled    |
| `WLAN_PDEV_F_DFS_CHANSWITCH_PENDING` | DFS channel switch pending |
| `WLAN_PDEV_F_TXPOW_FIXED`            | TX power fixed rate        |
| `WLAN_PDEV_F_AMPDU`                  | A-MPDU supported           |
| `WLAN_PDEV_F_AMSDU`                  | A-MSDU supported           |
| `WLAN_PDEV_F_DOT11D`                 | 11D in use                 |
| `WLAN_PDEV_F_RADAR`                  | Radar detected             |
| `WLAN_PDEV_F_MULTIVDEV_RESTART`      | Multi-VDEV restart enabled |
| `WLAN_PDEV_F_BEACON_PROTECTION`      | Beacon protection enabled  |

### PDEV Interface APIs

```c
// Creation/Deletion
struct wlan_objmgr_pdev *wlan_objmgr_pdev_obj_create(
  struct wlan_objmgr_psoc *psoc,
  struct pdev_osif_priv *osdev_priv);

QDF_STATUS wlan_objmgr_pdev_obj_delete(struct wlan_objmgr_pdev *pdev);

// Getters/Setters
uint8_t *wlan_pdev_get_hw_macaddr(struct wlan_objmgr_pdev *pdev);
void wlan_pdev_set_hw_macaddr(struct wlan_objmgr_pdev *pdev, uint8_t *macaddr);
struct pdev_osif_priv *wlan_pdev_get_ospriv(struct wlan_objmgr_pdev *pdev);
struct wlan_objmgr_psoc *wlan_pdev_get_psoc(struct wlan_objmgr_pdev *pdev);

// Iteration
QDF_STATUS wlan_objmgr_pdev_iterate_obj_list(
  struct wlan_objmgr_pdev *pdev,
  enum wlan_objmgr_obj_type obj_type,
  wlan_objmgr_pdev_op_handler handler,
  void *arg, uint8_t lock_free_op,
  wlan_objmgr_ref_dbgid dbg_id);

// VDEV Management on PDEV
QDF_STATUS wlan_objmgr_pdev_vdev_attach(struct wlan_objmgr_pdev *pdev,
                                        struct wlan_objmgr_vdev *vdev);
QDF_STATUS wlan_objmgr_pdev_vdev_detach(struct wlan_objmgr_pdev *pdev,
                                        struct wlan_objmgr_vdev *vdev);
```

---

## VDEV (Virtual Device)

### Definition

VDEV represents a **virtual network interface** that operates on top of a PDEV. Multiple VDEVs can share the
same physical radio, each serving a different purpose (e.g., AP, STA, Monitor).

### Key Characteristics

| Attribute          | Description                                     |
| ------------------ | ----------------------------------------------- |
| **Scope**          | Software-level, represents logical interface    |
| **Quantity**       | Multiple per PDEV (limited by `max_vdev_count`) |
| **Identity**       | Has unique `vdev_id` within PSOC                |
| **MAC Address**    | Can have distinct MAC from PDEV                 |
| **Lifetime**       | Created/destroyed dynamically                   |
| **Operation Mode** | Has specific opmode (STA, AP, etc.)             |

### Core Structure (`wlan_objmgr_vdev`)

```c
struct wlan_objmgr_vdev {
  qdf_list_node_t vdev_node;                    // List node in PDEV
  struct wlan_objmgr_vdev_mlme vdev_mlme;       // MLME info (opmode, state, channels)
  struct wlan_objmgr_vdev_objmgr vdev_objmgr;   // Object manager (peers, pdev ref)
  struct wlan_objmgr_vdev_nif vdev_nif;         // OS interface
  void *vdev_comp_priv_obj[WLAN_UMAC_MAX_COMPONENTS];
  QDF_STATUS obj_status[WLAN_UMAC_MAX_COMPONENTS];
  WLAN_OBJ_STATE obj_state;
  qdf_spinlock_t vdev_lock;
  struct wlan_mlo_dev_context *mlo_dev_ctx;     // MLO context (11be)
};
```

### VDEV MLME Sub-structure

```c
struct wlan_objmgr_vdev_mlme {
  enum QDF_OPMODE vdev_opmode;      // Operating mode
  enum wlan_vdev_state mlme_state;  // Current state
  enum wlan_vdev_state mlme_substate;
  struct wlan_channel *bss_chan;    // BSS channel
  struct wlan_channel *des_chan;    // Desired channel
  uint32_t vdev_caps;               // Capabilities
  uint32_t vdev_feat_caps;          // Feature caps
  uint32_t vdev_feat_ext_caps;      // Extended feature caps
  uint32_t vdev_op_flags;           // Operation flags
  uint8_t  mataddr[QDF_MAC_ADDR_SIZE];
  uint8_t  macaddr[QDF_MAC_ADDR_SIZE];
  uint8_t  mldaddr[QDF_MAC_ADDR_SIZE];  // MLD address (11be)
  uint8_t  mlo_link_id;             // MLO link ID
};
```

### VDEV Operation Modes (QDF_OPMODE)

| Mode                  | Description                  |
| --------------------- | ---------------------------- |
| `QDF_STA_MODE`        | Station/Client mode          |
| `QDF_SAP_MODE`        | SoftAP mode                  |
| `QDF_P2P_CLIENT_MODE` | P2P Client                   |
| `QDF_P2P_GO_MODE`     | P2P Group Owner              |
| `QDF_IBSS_MODE`       | Ad-hoc mode                  |
| `QDF_MONITOR_MODE`    | Monitor/sniffer mode         |
| `QDF_P2P_DEVICE_MODE` | P2P Device                   |
| `QDF_OCB_MODE`        | Outside Context of BSS (V2X) |
| `QDF_NDI_MODE`        | NAN Data Interface           |
| `QDF_WDS_MODE`        | Wireless Distribution System |
| `QDF_FTM_MODE`        | Factory Test Mode            |
| `QDF_NAN_DISC_MODE`   | NAN Discovery                |
| `QDF_TDLS_MODE`       | Tunneled Direct Link Setup   |

### VDEV Feature Flags

| Flag                   | Purpose                    |
| ---------------------- | -------------------------- |
| `WLAN_VDEV_F_PRIVACY`  | Privacy/encryption enabled |
| `WLAN_VDEV_F_WPA`      | WPA/WPA2 enabled           |
| `WLAN_VDEV_F_HIDESSID` | Hide SSID in beacon        |
| `WLAN_VDEV_F_AMPDU`    | A-MPDU supported           |
| `WLAN_VDEV_F_UAPSD`    | U-APSD enabled             |
| `WLAN_VDEV_F_PURE11N`  | Pure 11n mode              |
| `WLAN_VDEV_F_PURE11AC` | Pure 11ac mode             |
| `WLAN_VDEV_F_SON`      | Wi-Fi SON mode             |
| `WLAN_VDEV_FEXT2_MLO`  | MLO enabled (11be)         |

### VDEV Interface APIs

```c
// Creation/Deletion
struct wlan_objmgr_vdev *wlan_objmgr_vdev_obj_create(
  struct wlan_objmgr_pdev *pdev,
  struct wlan_vdev_create_params *params);

QDF_STATUS wlan_objmgr_vdev_obj_delete(struct wlan_objmgr_vdev *vdev);

// Getters/Setters
enum QDF_OPMODE wlan_vdev_mlme_get_opmode(struct wlan_objmgr_vdev *vdev);
void wlan_vdev_mlme_set_opmode(struct wlan_objmgr_vdev *vdev, enum QDF_OPMODE mode);
void wlan_vdev_mlme_set_macaddr(struct wlan_objmgr_vdev *vdev, uint8_t *macaddr);
uint8_t *wlan_vdev_mlme_get_macaddr(struct wlan_objmgr_vdev *vdev);
struct wlan_objmgr_pdev *wlan_vdev_get_pdev(struct wlan_objmgr_vdev *vdev);
struct wlan_objmgr_psoc *wlan_vdev_get_psoc(struct wlan_objmgr_vdev *vdev);
uint8_t wlan_vdev_get_id(struct wlan_objmgr_vdev *vdev);

// Peer Management
QDF_STATUS wlan_objmgr_iterate_peerobj_list(
  struct wlan_objmgr_vdev *vdev,
  wlan_objmgr_vdev_op_handler handler,
  void *arg, wlan_objmgr_ref_dbgid dbg_id);

// WMI Commands (Target Interface)
QDF_STATUS send_vdev_create_cmd(wmi_unified_t wmi, uint8_t macaddr[],
                                struct vdev_create_params *param);
QDF_STATUS send_vdev_delete_cmd(wmi_unified_t wmi, uint8_t if_id);
QDF_STATUS send_vdev_start_cmd(wmi_unified_t wmi, struct vdev_start_params *req);
QDF_STATUS send_vdev_stop_cmd(wmi_unified_t wmi, uint8_t vdev_id);
QDF_STATUS send_vdev_down_cmd(wmi_unified_t wmi, uint8_t vdev_id);
```

---

## Key Differences Summary

| Aspect                  | PDEV                       | VDEV                             |
| ----------------------- | -------------------------- | -------------------------------- |
| **Abstraction Level**   | Physical hardware          | Virtual/logical interface        |
| **Represents**          | Radio chip/band            | Network interface (wlan0, wlan1) |
| **Quantity per device** | Fixed (hardware-dependent) | Dynamic (software-configurable)  |
| **Parent Object**       | PSOC                       | PDEV                             |
| **Child Objects**       | VDEVs                      | PEERs                            |
| **MAC Address**         | Hardware MAC               | Can be different from PDEV       |
| **Channel**             | Channel list capability    | Active BSS/desired channel       |
| **Operating Mode**      | N/A (hardware)             | STA, AP, Monitor, P2P, etc.      |
| **Creation Trigger**    | Driver initialization      | User/application request         |
| **Key Identifier**      | `pdev_id` (0-2 typically)  | `vdev_id` (0-255)                |
| **State Machine**       | No dedicated SM            | Full MLME state machine          |
| **Peer Handling**       | Indirect (via VDEVs)       | Direct (maintains peer list)     |

---

## Interface Design Differences

### 1. Creation Parameters

**PDEV Creation:**

```c
struct wlan_objmgr_pdev *wlan_objmgr_pdev_obj_create(
  struct wlan_objmgr_psoc *psoc,      // Parent PSOC
  struct pdev_osif_priv *osdev_priv   // OS interface private data
);
```

**VDEV Creation:**

```c
struct wlan_vdev_create_params {
  enum QDF_OPMODE opmode;             // Operation mode (required)
  uint32_t flags;                     // Creation flags
  size_t size_vdev_priv;              // Private data size
  void *legacy_osif;                  // OS interface
  uint8_t macaddr[QDF_MAC_ADDR_SIZE]; // MAC address
  uint8_t mataddr[QDF_MAC_ADDR_SIZE]; // MAT address
  uint8_t mldaddr[QDF_MAC_ADDR_SIZE]; // MLD address (11be)
  bool mlo_sap_sync_disable;          // MLO SAP sync flag
};
```

### 2. Object Manager Structure

**PDEV Object Manager:**

```c
struct wlan_objmgr_pdev_objmgr {
  uint8_t wlan_pdev_id;               // PDEV identifier
  uint8_t wlan_vdev_count;            // Current VDEV count
  uint8_t max_vdev_count;             // Maximum VDEVs allowed
  qdf_list_t wlan_vdev_list;          // List of VDEVs
  uint16_t wlan_peer_count;           // Total peer count
  uint16_t max_peer_count;            // Max peers
  struct wlan_objmgr_psoc *wlan_psoc; // Parent PSOC reference
  qdf_atomic_t ref_cnt;
};
```

**VDEV Object Manager:**

```c
struct wlan_objmgr_vdev_objmgr {
  uint8_t vdev_id;                    // VDEV identifier
  struct wlan_objmgr_peer *self_peer; // Self PEER reference
  struct wlan_objmgr_peer *bss_peer;  // BSS PEER reference
  qdf_list_t wlan_peer_list;          // List of PEERs
  struct wlan_objmgr_pdev *wlan_pdev; // Parent PDEV reference
  uint16_t wlan_peer_count;           // Current peer count
  uint16_t max_peer_count;            // Max peers for this VDEV
  uint32_t c_flags;                   // Creation flags
  qdf_atomic_t ref_cnt;
};
```

### 3. Operations Callbacks

**PDEV Operations:**

```c
struct mlme_external_tx_ops {
  QDF_STATUS (*pdev_ops)(
    struct wlan_objmgr_pdev *pdev,
    enum wlan_mlme_pdev_param type,
    void *data, void *ret);
};
```

**VDEV Operations:**

```c
struct vdev_mlme_ops {
  QDF_STATUS (*mlme_vdev_validate_basic_params)(struct vdev_mlme_obj *vdev_mlme);
  QDF_STATUS (*mlme_vdev_start_send)(struct vdev_mlme_obj *vdev_mlme, ...);
  QDF_STATUS (*mlme_vdev_restart_send)(struct vdev_mlme_obj *vdev_mlme, ...);
  QDF_STATUS (*mlme_vdev_stop_send)(struct vdev_mlme_obj *vdev_mlme, ...);
  QDF_STATUS (*mlme_vdev_start_continue)(struct vdev_mlme_obj *vdev_mlme, ...);
  QDF_STATUS (*mlme_vdev_up_send)(struct vdev_mlme_obj *vdev_mlme);
  QDF_STATUS (*mlme_vdev_down_send)(struct vdev_mlme_obj *vdev_mlme);
  // ... many more VDEV-specific operations
};
```

---

## Channel Management Differences

### PDEV Channel Management

- Maintains **channel list** of all supported channels
- Defines hardware capabilities per band
- DFS/radar detection at PDEV level
- Channel switch affects all VDEVs on the radio

### VDEV Channel Management

- Has **bss_chan**: Currently operating channel
- Has **des_chan**: Desired/target channel
- Channel width per VDEV can vary
- Puncture patterns (11be) per VDEV

```c
struct wlan_channel {
  uint16_t ch_freq;           // Frequency in MHz
  uint8_t  ch_ieee;           // IEEE channel number
  uint8_t  ch_freq_seg1;      // Center freq for VHT80/160
  uint8_t  ch_freq_seg2;      // Second center freq (80+80)
  int8_t   ch_maxpower;       // Max TX power
  enum phy_ch_width ch_width; // Channel width
  enum wlan_phymode ch_phymode;
  uint16_t puncture_bitmap;   // Puncture pattern (11be)
};
```

---

## Reference Count Management

Both PDEV and VDEV use reference counting to manage object lifecycle:

```c
// PDEV reference management
void wlan_objmgr_pdev_get_ref(struct wlan_objmgr_pdev *pdev,
                              wlan_objmgr_ref_dbgid id);
void wlan_objmgr_pdev_release_ref(struct wlan_objmgr_pdev *pdev,
                                  wlan_objmgr_ref_dbgid id);

// VDEV reference management
void wlan_objmgr_vdev_get_ref(struct wlan_objmgr_vdev *vdev,
                              wlan_objmgr_ref_dbgid id);
void wlan_objmgr_vdev_release_ref(struct wlan_objmgr_vdev *vdev,
                                  wlan_objmgr_ref_dbgid id);
```

---

## MLO (Multi-Link Operation) Considerations (Wi-Fi 7 / 802.11be)

### PDEV in MLO

- Each PDEV represents a single radio/link
- Multiple PDEVs may participate in MLO

### VDEV in MLO

- VDEVs can be MLO-enabled: `WLAN_VDEV_FEXT2_MLO`
- Has `mlo_dev_ctx` for MLO device context
- Maintains `mlo_link_id` for link identification
- Supports MLD (Multi-Link Device) addressing via `mldaddr`
- MLO flags: `WLAN_VDEV_FEXT2_MLO_STA_LINK`, `WLAN_VDEV_FEXT2_MLO_MCAST`

---

## Use Case Examples

### Example 1: Concurrent AP + STA

```
PDEV (5GHz Radio)
├── VDEV0 (AP Mode)     - Broadcasts SSID, accepts clients
└── VDEV1 (STA Mode)    - Connected to upstream AP
```

### Example 2: Dual-Band AP

```
PDEV0 (2.4GHz)
└── VDEV0 (AP Mode)     - 2.4GHz AP interface

PDEV1 (5GHz)
└── VDEV1 (AP Mode)     - 5GHz AP interface
```

### Example 3: Monitor + AP

```
PDEV (5GHz)
├── VDEV0 (AP Mode)     - Normal AP operation
└── VDEV1 (Monitor)     - Packet capture
```

---

## Best Practices

1. **Always check for NULL** when getting PDEV/VDEV references
2. **Use proper reference counting** to prevent use-after-free
3. **Lock objects** before modifying shared state
4. **VDEV opmode is immutable** after creation
5. **PDEV operations affect all child VDEVs**
6. **Channel changes at PDEV level** require coordinating with all VDEVs
