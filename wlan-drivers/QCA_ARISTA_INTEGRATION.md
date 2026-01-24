# Qualcomm Binary and Arista Code Integration

This document describes how Qualcomm (QCA) binary drivers are integrated with Arista code, the linking mechanisms, and the architectural patterns used to combine proprietary and custom components.

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        OWNERSHIP & MODIFIABILITY                            │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  ARISTA CODE (Full Control)                                         │   │
│  │  ar/                                                                 │   │
│  │  ✅ Can modify freely                                               │   │
│  │  ✅ Can add new features                                            │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                               │                                             │
│                               │ Uses APIs from                              │
│                               ▼                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  QCA HEADER FILES (Compiled into Arista binary)                     │   │
│  │  QCA/licensed/.../include/, os/linux/include/                       │   │
│  │  ⚠️ Inline functions compiled into our code                        │   │
│  │  ⚠️ Structure definitions (ieee80211_cb, etc.)                      │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                               │                                             │
│                               │ Calls into                                  │
│                               ▼                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  QCA BINARY DRIVER (Pre-compiled, closed source)                    │   │
│  │  dp_tx.o, dp_rx.o, hal_srng.o, etc.                                 │   │
│  │  ❌ Cannot modify                                                   │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                               │                                             │
│                               │ Programs                                    │
│                               ▼                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  WIFI HARDWARE (Qualcomm chipset)                                   │   │
│  │  IPQ8074, IPQ6018, IPQ5332, etc.                                    │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Integration Layers

### 1. Vendor Driver Interface (`ar/vdrv_if/`)

The primary abstraction layer between Arista code and QCA-specific implementations:

```
vdrv_if/
├── inc/                    # Vendor-agnostic headers
│   ├── vdrv_dp_if.h        # Data path interface (TX/RX, TID, DHCP, EAPOL)
│   ├── vdrv_cp_if.h        # Control path interface
│   └── vdrv_cp_if_*.h      # Other control path interfaces
└── qca/                    # QCA-specific implementations
    ├── common/             # Common QCA implementation
    │   ├── vdrv_dp_if.c    # Wraps QCA wbuf functions
    │   └── vdrv_cp_if.c    # Control path wrappers
    ├── spf11_4/            # SPF 11.4 specific
    ├── spf12_2_csu2/       # SPF 12.2 CSU2 specific
    └── spf12_5_cs/         # SPF 12.5 CS specific
```

**Key Functions in `vdrv_cp_if.c`**:
- Registers Arista components with QCA Object Manager
- Attaches Arista objects (psoc, pdev, vdev, peer) to QCA objects
- Uses `wlan_objmgr_*_component_obj_attach()` for object association

### 2. Arista Interface Layer (`ar/ar_if/`)

Glue code between Arista core and QCA:

```
ar_if/
├── inc/                    # Interface headers
│   ├── ar_dp_if.h          # Data path interface
│   └── ar_cp_if.h          # Control path interface
└── qca/                    # QCA-specific implementation
    └── common/
        └── ar_dp_if.c      # Data path callbacks for QCA
```

### 3. Airtight Extension (`umac/airtight_extn/`)

Custom Arista code compiled into QCA UMAC layer:

| File | Purpose |
|------|---------|
| `atn_umac.c` | UMAC integration, register access |
| `atn_subr.c` | Background scanning, initialization |
| `atn_counters.c` | Radio/client statistics collection |
| `atn_wireless.h` | Airtight extension header definitions |

## Build and Linking Process

### Build Order

```
1. Kernel builds first
2. QCA driver modules compile (provides .ko files and headers)
3. Arista ar/ code compiles using QCA headers
4. Final kernel modules link together
```

### Module Dependencies

From `apdrv.mk`:
```makefile
apdrv_dep = kernel arkerneltoggle arwlandrv.prep wlevt.prep
            commproto.prep commutils.prep apcomm.prep cnss2 gwmac
```

### QCA Kernel Modules Built

| Module | Path | Description |
|--------|------|-------------|
| `qdf.ko` | `cmn_dev/qdf/` | Qualcomm Driver Framework |
| `asf.ko` | `asf/` | Atheros Service Framework |
| `mem_manager.ko` | `os/linux/mem/` | Memory management |
| `umac.ko` | `umac/` | Upper MAC (includes airtight_extn) |
| `qca_spectral.ko` | `cmn_dev/spectral/` | Spectral analysis |
| `qca_ol.ko` | `qca_ol/` | QCA Offload module |
| `wifi_3_0.ko` | `qca_ol/wifi3.0/` | WiFi 3.0 (11ax) |
| `wifi_2_0.ko` | `qca_ol/wifi2.0/` | WiFi 2.0 legacy |
| `ath_pktlog.ko` | `lmac/ath_pktlog/` | Packet logging |
| `smart_antenna.ko` | `smartantenna/` | Smart antenna |

### Module Loading Order

From `wlan_modules_ap`:
```bash
insmod broadcast_multicast_opt.ko
insmod mem_manager.ko
insmod qdf.ko
insmod asf.ko
insmod umac.ko $UMAC_ARGS
insmod qca_spectral.ko
insmod qca_ol.ko
insmod wifi_3_0.ko
insmod wifi_2_0.ko
insmod ath_pktlog.ko
insmod smart_antenna.ko
```

## Callback Registration and Hooks

### Object Manager Integration

Arista registers components with QCA's Object Manager framework:

```c
// From vdrv_cp_if.c
wlan_objmgr_psoc_component_obj_attach(psoc, WLAN_UMAC_COMP_AR, ar_psoc, ...);
wlan_objmgr_pdev_component_obj_attach(pdev, WLAN_UMAC_COMP_AR, ar_pdev, ...);
wlan_objmgr_vdev_component_obj_attach(vdev, WLAN_UMAC_COMP_AR, ar_vdev, ...);
wlan_objmgr_peer_component_obj_attach(peer, WLAN_UMAC_COMP_AR, ar_peer, ...);
```

### Data Path Callbacks

QCA driver calls Arista functions during TX/RX:

```
TX Flow:
  Linux netif_rx()
    → osif_vap_hardstart()        [QCA]
    → ar_dp_if_tx_handle()        [Arista ar_if]
    → ar_dp_tx_handle()           [Arista core]
    → vdrv_dp_if_tx_send()        [Arista vdrv_if]
    → dp_tx_send()                [QCA Binary]

RX Flow:
  WiFi Hardware
    → dp_rx_process()             [QCA Binary]
    → ar_dp_if_rx_handle()        [Arista ar_if]
    → ar_dp_rx_handle()           [Arista core]
    → netif_rx()                  [Linux]
```

### Management Frame Callbacks

```c
// Register for management frame RX callbacks
cb_info[0].frm_type = MGMT_PROBE_RESP;
cb_info[0].mgmt_rx_cb = vdrv_cp_if_rx_mgmt_parser;
cb_info[1].frm_type = MGMT_BEACON;
cb_info[1].mgmt_rx_cb = vdrv_cp_if_rx_mgmt_parser;
wlan_mgmt_txrx_register_rx_cb(psoc, WLAN_UMAC_COMP_SCAN, cb_info, 2);
```

## Kbuild Integration

### QCA Kbuild Files

The QCA driver uses Kbuild files to compile kernel modules:

**umac/Kbuild** - Compiles UMAC with Arista extensions:
```makefile
# Third-party/vendor extensions
ifeq ($(QCA_THIRDPARTY), 1)
PLTFRM_OBJS = $(DEPTH)/thirdparty/$(THIRDPARTY_VENDOR)/ath_carr_pltfrm.o
endif

# Airtight extension objects are compiled into umac.ko
OSDEP_OBJS += airtight_extn/atn_umac.o
OSDEP_OBJS += airtight_extn/atn_subr.o
OSDEP_OBJS += airtight_extn/atn_counters.o
```

**qca_ol/Kbuild** - Compiles offload module:
```makefile
qca_ol-objs += if_ath_pci.o    # PCIe bus
qca_ol-objs += if_ath_ahb.o    # AHB bus
```

### Arista Makefile Integration

**arwlandrv.mk**:
```makefile
arwlandrv_mod = arwlandrv
arwlandrv_src = $(AP_SRC_DIR)/wlan-drivers/ar
arwlandrv_bld = $(K_BLD_DIR_TC_PLAT)
arwlandrv_dep = arkerneltoggle
```

## Symbol Export and Linking

### Exported Symbols

QCA modules export symbols that Arista code uses:

```c
// From ar_dp_if.c
EXPORT_SYMBOL(ar_dp_if_vdev_create);
EXPORT_SYMBOL(ar_dp_if_peer_create);
```

### Include Paths

```makefile
# QCA headers used by Arista
INCS += -I$(QCA_PATH)/cmn_dev/qdf/inc
INCS += -I$(QCA_PATH)/os/linux/include
INCS += -I$(QCA_PATH)/umac/include
INCS += -I$(QCA_PATH)/cmn_dev/dp/inc
```

## Binary Blob Integration

### Pre-compiled Blobs

Some QCA components are delivered as pre-compiled tarballs:

```makefile
# From Makefile.sdk
BLOB_BLD_DEPS := \
    $(addprefix $(CURDIR)/,\
        spf12_5_cs_ol_include.tgz spf12_5_cs_fw_hdr.tgz)
```

### Firmware Loading

Firmware blobs are loaded at runtime:
- Path: `/lib/firmware/` or `/ini/`
- Loaded via: `request_firmware()` kernel API
- Platforms: HAWKEYE, PINE, WAIKIKI

## SPF Version-Specific Implementations

Different SPF versions may have API differences:

| SPF Version | Location | Notes |
|-------------|----------|-------|
| SPF 11.4 | `vdrv_if/qca/spf11_4/` | Older API compatibility |
| SPF 12.2 CSU2 | `vdrv_if/qca/spf12_2_csu2/` | WiFi 6E support |
| SPF 12.5 CS | `vdrv_if/qca/spf12_5_cs/` | Latest APIs |

## Key Data Structures

### Object Hierarchy

```
struct wlan_objmgr_psoc    ← QCA Platform SoC
    └── ar_psoc            ← Arista extension (attached via component)

struct wlan_objmgr_pdev    ← QCA Physical Device (radio)
    └── ar_pdev            ← Arista extension

struct wlan_objmgr_vdev    ← QCA Virtual Device (VAP)
    └── ar_vdev            ← Arista extension

struct wlan_objmgr_peer    ← QCA Peer (client)
    └── ar_peer            ← Arista extension
```

### Accessor Macros

```c
// Get Arista objects from QCA objects
#define VDRV_GET_AR_PDEV(_pdev) \
  wlan_objmgr_pdev_get_comp_private_obj(_pdev, WLAN_UMAC_COMP_AR)

#define VDRV_GET_AR_VDEV(_vdev) \
  wlan_objmgr_vdev_get_comp_private_obj(_vdev, WLAN_UMAC_COMP_AR)

#define VDRV_GET_AR_PEER(_peer) \
  wlan_objmgr_peer_get_comp_private_obj(_peer, WLAN_UMAC_COMP_AR)
```

## What Can/Cannot Be Modified

### ✅ Modifiable (Arista Code)

| Component | Location |
|-----------|----------|
| Core business logic | `ar/core/src/*.c` |
| Vendor interface wrappers | `ar/vdrv_if/qca/**/*.c` |
| Arista interface layer | `ar/ar_if/**/*.c` |
| Airtight extensions | `QCA/licensed/*/umac/airtight_extn/` |

### ⚠️ Use But Don't Modify (QCA Headers)

| Component | Location |
|-----------|----------|
| wbuf inline functions | `os/linux/include/wbuf_adf_private.h` |
| CB structure definitions | `os/linux/include/osdep_adf.h` |
| QDF wrappers | `cmn_dev/qdf/inc/qdf_nbuf.h` |

### ❌ Cannot Modify (QCA Binary)

| Component | Files |
|-----------|-------|
| TX datapath | `dp_tx.c` → `dp_tx.o` |
| RX datapath | `dp_rx.c` → `dp_rx.o` |
| HAL layer | `hal_srng.c` → `.o` |
| Ring management | All HAL files |

## References

- [QUALCOMM_CONTRIBUTION.md](QUALCOMM_CONTRIBUTION.md) - QCA contributions overview
- [DRIVERS.md](DRIVERS.md) - All drivers in the repository
- `ar/docs/codebase_structure.md` - Detailed codebase structure
- `ar/docs/skb_tid_metadata_flow.md` - SKB metadata flow documentation

