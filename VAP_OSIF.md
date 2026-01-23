# VAP (Virtual Access Point) and OSIF (OS Interface) Architecture

This document describes the VAP and OSIF layers in the Arista AP WLAN driver stack.

## Overview

The WLAN driver stack uses a layered architecture to manage virtual wireless interfaces:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           User Space                                        │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐         │
│  │  hostapd    │  │  ocagent    │  │ configagent │  │   iwpriv    │         │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘         │
│         │                │                │                │                │
│         └────────────────┴────────────────┴────────────────┘                │
│                                   │                                         │
│                          cfg80211 / ioctl                                   │
├───────────────────────────────────┼─────────────────────────────────────────┤
│                           Kernel Space                                      │
│                                   │                                         │
│  ┌────────────────────────────────▼────────────────────────────────────────┐│
│  │                    OSIF Layer (osif_umac.c)                             ││
│  │  ┌──────────────────────────────────────────────────────────────────┐   ││
│  │  │  osif_dev (per-VAP)                                              │   ││
│  │  │  - struct net_device *netdev  (athX)                             │   ││
│  │  │  - wlan_if_t os_if            (ieee80211vap pointer)             │   ││
│  │  │  - enum ieee80211_opmode os_opmode                               │   ││
│  │  │  - struct net_device_ops (osif_vap_open, osif_vap_stop, ...)     │   ││
│  │  └──────────────────────────────────────────────────────────────────┘   ││
│  └─────────────────────────────────┬───────────────────────────────────────┘│
│                                    │                                        │
│  ┌─────────────────────────────────▼───────────────────────────────────────┐│
│  │                    UMAC Layer (ieee80211_vap.c)                         ││
│  │  ┌──────────────────────────────────────────────────────────────────┐   ││
│  │  │  ieee80211vap (per-VAP)                                          │   ││
│  │  │  - enum ieee80211_opmode iv_opmode                               │   ││
│  │  │  - struct ieee80211com *iv_ic  (back ptr to radio)               │   ││
│  │  │  - u_int8_t iv_myaddr[6]       (BSSID)                           │   ││
│  │  │  - struct wlan_objmgr_vdev *vdev_obj                             │   ││
│  │  └──────────────────────────────────────────────────────────────────┘   ││
│  └─────────────────────────────────┬───────────────────────────────────────┘│
│                                    │                                        │
│  ┌─────────────────────────────────▼───────────────────────────────────────┐│
│  │                    Arista Layer (ar_main.c)                             ││
│  │  ┌──────────────────────────────────────────────────────────────────┐   ││
│  │  │  ar_vdev_s (per-VAP)                                             │   ││
│  │  │  - vdrv_if_vdev_t vdrv_vdev   (QCA vdev handle)                  │   ││
│  │  │  - struct ar_pdev_s *ar_pdev  (parent radio)                     │   ││
│  │  │  - uint8_t mac[6]             (BSSID)                            │   ││
│  │  │  - VDRV_IF_VDEV_MODE vapmode                                     │   ││
│  │  └──────────────────────────────────────────────────────────────────┘   ││
│  └─────────────────────────────────┬───────────────────────────────────────┘│
│                                    │                                        │
│  ┌─────────────────────────────────▼───────────────────────────────────────┐│
│  │                    QCA Driver (LMAC/Target)                             ││
│  │  ┌──────────────────────────────────────────────────────────────────┐   ││
│  │  │  wlan_objmgr_vdev (Object Manager VDEV)                          │   ││
│  │  └──────────────────────────────────────────────────────────────────┘   ││
│  └─────────────────────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────────────────────┘
```

## Object Hierarchy

The driver uses a hierarchical object model (WLAN Object Manager - `wlan_objmgr`):

```
PSOC (SoC)                              wlan_objmgr_psoc
  │
  ├── Reference: psoc->soc_objmgr
  ├── Component objects attached via wlan_objmgr_psoc_component_obj_attach()
  │
  └── PDEV (Physical Device / Radio)    wlan_objmgr_pdev
        │
        ├── ieee80211com (ic)           ← Legacy UMAC radio state
        ├── ar_pdev_s                   ← Arista radio extensions (WLAN_UMAC_COMP_AR)
        ├── ol_ath_softc_net80211       ← Offload radio context
        │
        └── VDEV (Virtual Device / VAP) wlan_objmgr_vdev
              │
              ├── ieee80211vap          ← Legacy UMAC VAP state (vdev_mlme->ext_vdev_ptr)
              ├── osif_dev              ← OS interface (vdev->vdev_nif.osdev->legacy_osif_priv)
              ├── ar_vdev_s             ← Arista extensions (WLAN_UMAC_COMP_AR)
              │
              └── PEER (Client)         wlan_objmgr_peer
                    │
                    ├── ieee80211_node  ← Legacy node state
                    └── ar_peer_s       ← Arista client extensions
```

### Object Manager Component Attachment

Each layer attaches its private object to the object manager:

```c
/* Component IDs (wlan_umac_comp_id) */
enum {
    WLAN_UMAC_COMP_MLME,      /* MLME component */
    WLAN_UMAC_COMP_AR,        /* Arista component */
    WLAN_UMAC_COMP_DP,        /* Datapath component */
    // ...
    WLAN_UMAC_MAX_COMPONENTS
};

/* Attaching Arista vdev to object manager */
QDF_STATUS vdrv_cp_if_vdev_create_handler(struct wlan_objmgr_vdev *vdev, void *arg) {
    struct ar_vdev_s *ar_vdev = ar_vdev_init(...);

    /* Attach ar_vdev as component object */
    wlan_objmgr_vdev_component_obj_attach(
        vdev,
        WLAN_UMAC_COMP_AR,      /* Component ID */
        ar_vdev,                /* Private object */
        QDF_STATUS_SUCCESS
    );
}

/* Retrieving Arista vdev from object manager */
struct ar_vdev_s *ar_vdev = wlan_objmgr_vdev_get_comp_private_obj(
    vdev,
    WLAN_UMAC_COMP_AR
);
```

### Object Lifecycle Notifications

The Object Manager dispatches create/destroy notifications:

```c
/* Registration at module init */
wlan_objmgr_register_vdev_create_handler(
    WLAN_UMAC_COMP_AR,
    vdrv_cp_if_vdev_create_handler,    /* Called when VDEV created */
    NULL
);

wlan_objmgr_register_vdev_destroy_handler(
    WLAN_UMAC_COMP_AR,
    vdrv_cp_if_vdev_delete_handler,    /* Called when VDEV deleted */
    NULL
);

/* Sequence:
   1. Core creates wlan_objmgr_vdev
   2. Object Manager calls all registered create handlers
   3. Each component attaches its private object
   4. On delete: destroy handlers called in reverse order
*/
```

## VAP Operation Modes

| Mode | Value | Description |
|------|-------|-------------|
| `IEEE80211_M_IBSS` | 0 | Ad-hoc (IBSS) station |
| `IEEE80211_M_STA` | 1 | Infrastructure station (client) |
| `IEEE80211_M_WDS` | 2 | WDS (4-address) link |
| `IEEE80211_M_AHDEMO` | 3 | Legacy ad-hoc demo mode |
| `IEEE80211_M_HOSTAP` | 6 | Access Point (AP) mode |
| `IEEE80211_M_MONITOR` | 8 | Monitor mode (packet capture) |
| `IEEE80211_M_BTAMP` | 9 | Bluetooth AMP |
| `IEEE80211_M_P2P_GO` | 33 | Wi-Fi Direct Group Owner |
| `IEEE80211_M_P2P_CLIENT` | 34 | Wi-Fi Direct Client |
| `IEEE80211_M_P2P_DEVICE` | 35 | Wi-Fi Direct Device |

## Key Structures

### ieee80211vap (UMAC VAP)

The core VAP structure in the UMAC layer:

```c
typedef struct ieee80211vap {
    TAILQ_ENTRY(ieee80211vap)  iv_next;      /* list of vap instances */
    struct ieee80211_wme_state iv_wmestate;  /* WME params */
    u_int32_t                  iv_debug;     /* debug msg flags */
    enum ieee80211_opmode      iv_opmode;    /* operation mode */
    struct ieee80211com       *iv_ic;        /* back ptr to radio */
    void                      *iv_priv;      /* private extension data */
    os_if_t                    iv_ifp;       /* opaque OS interface handle */
    char                      *iv_netdev_name;
    u_int8_t                   iv_myaddr[6]; /* current MAC address */
    u_int32_t                  iv_flags;     /* state flags */
    struct wlan_objmgr_vdev   *vdev_obj;     /* Object Manager VDEV */
    struct vdev_mlme_obj      *vdev_mlme;    /* MLME VDEV object */
    // ... many more fields
} *wlan_if_t;
```

### osif_dev (OS Interface Device)

The OS-specific wrapper around the VAP:

```c
typedef struct _osif_dev {
    uint8_t                    dev_type;      /* OSIF_NETDEV_TYPE_VAP, etc. */
    osdev_t                    os_handle;     /* OS device handle */
    struct net_device         *netdev;        /* Linux net_device (athX) */
    struct wlan_objmgr_vdev   *ctrl_vdev;     /* UMAC vdev object pointer */
    wlan_if_t                  os_if;         /* ieee80211vap pointer */
    wlan_dev_t                 os_devhandle;  /* radio handle (ieee80211com) */
    struct net_device         *os_comdev;     /* parent radio net_device */
    enum ieee80211_opmode      os_opmode;     /* cached operation mode */
    u_int8_t                   os_unit;       /* unit number */
    
    /* State flags */
    u_int32_t is_deleted:1,
              is_delete_in_progress:1,
              is_bss_started:1,
              // ...
    
    /* VLAN support */
    struct vlan_group         *vlgrp;
    unsigned short             vlanID;
    
    /* Statistics */
    struct rtnl_link_stats64   os_devstats;
    struct iw_statistics       os_iwstats;
    // ...
} osif_dev;
```

### ar_vdev_s (Arista VAP Extensions)

Arista-specific VAP state and configuration:

```c
struct ar_vdev_s {
    vdrv_if_vdev_t vdrv_vdev;      /* Handle to vendor driver vap object */
    struct ar_pdev_s *ar_pdev;     /* Handle to parent radio object */
    uint32_t flags;                /* VAP config flags */
    uint8_t mac[6];                /* VAP mac address = BSSID */
    uint8_t vdev_id;               /* vdev id */
    VDRV_IF_VDEV_MODE vapmode;     /* Operation mode */
    char netdev_name[16];          /* Net device name */

    /* Smart Steering */
    int32_t ss_rc;
    int8_t ss_rssi;

    /* 802.11v BSS Transition */
    uint16_t disassoc_imminent;
    uint16_t disassoc_timer;

    /* Statistics */
    struct ar_vdev_stats ar_vdev_stats;
    struct ar_vdev_perf ar_vdev_perf;
    // ...
};
```

## VAP Lifecycle

### VAP Creation Flow

```
User Space (iwpriv/cfg80211)
         │
         ▼
osif_ioctl_create_vap()
         │
         ▼
osif_create_vap_check()          ← Validate parameters
         │
         ▼
osif_create_vap_netdev_alloc()   ← Allocate net_device + osif_dev
         │
         ▼
osifp_create_wlan_vap()
         │
         ├──► wlan_vap_create()  ← Create ieee80211vap (UMAC)
         │           │
         │           ▼
         │    ieee80211_vap_setup()
         │           │
         │           ▼
         │    ic->ic_vap_create_pre_init()  ← Vendor-specific init
         │
         ├──► ar_vdev_init()     ← Create ar_vdev_s (Arista)
         │           │
         │           ▼
         │    wlan_objmgr_vdev_component_obj_attach()
         │
         ▼
osif_create_vap_complete()
         │
         ├──► osif_attach()      ← Setup net_device_ops
         │
         ▼
osif_create_vap_netdev_register()
         │
         ▼
register_netdevice()             ← Register athX with kernel
```

### VAP Open/Stop (Interface Up/Down)

```c
/* net_device_ops for VAP interfaces */
static struct net_device_ops osif_dev_ops = {
    .ndo_get_stats64  = osif_getstats,
    .ndo_open         = osif_vap_open,      /* ifconfig athX up */
    .ndo_stop         = osif_vap_stop,      /* ifconfig athX down */
    .ndo_start_xmit   = vap_hardstart,      /* TX path */
    .ndo_do_ioctl     = ieee80211_ioctl,    /* iwpriv commands */
    .ndo_change_mtu   = osif_change_mtu,
    .ndo_set_mac_address = osif_change_mac_addr,
};
```

**osif_vap_open()** flow:
1. `osif_vap_open_preprocess()` - Sanity checks, platform init
2. Open parent radio device if needed
3. `osif_vap_open_main()` → `osif_vap_init()` → `wlan_vap_init()`

**osif_vap_stop()** flow:
1. `osif_vap_pre_stop()` - Pre-stop processing
2. Mode-specific stop:
   - AP/Monitor: `osif_vap_stop_ap()`
   - STA: `osif_vap_stop_sta()`

### VDEV State Machine

The VDEV MLME (Media Access Control Layer Management Entity) state machine:

```
                         ┌─────────────────────────────────────┐
                         │                                     │
                         ▼                                     │
    ┌──────────┐    ┌─────────┐    ┌────────┐    ┌────────┐   │
    │  INIT    │───►│  START  │───►│   UP   │───►│  STOP  │───┘
    └──────────┘    └─────────┘    └────────┘    └────────┘
         │                              │             │
         │                              │             │
         ▼                              ▼             ▼
    ┌──────────────────────────────────────────────────────┐
    │                        DOWN                          │
    └──────────────────────────────────────────────────────┘
```

**State transitions (AP Mode):**

| Current State | Event | Next State | Action |
|---------------|-------|------------|--------|
| INIT | vdev_start_req | START_PROGRESS | Send WMI_VDEV_START_CMD |
| START_PROGRESS | vdev_start_resp | UP | Start beaconing |
| UP | vdev_stop_req | STOP_PROGRESS | Send WMI_VDEV_STOP_CMD |
| STOP_PROGRESS | vdev_stop_resp | INIT | Cleanup |

```c
/* State machine events */
enum wlan_vdev_sm_evt {
    WLAN_VDEV_SM_EV_START,           /* Start VDEV */
    WLAN_VDEV_SM_EV_START_REQ,       /* Start request sent to FW */
    WLAN_VDEV_SM_EV_START_RESP,      /* FW responded to start */
    WLAN_VDEV_SM_EV_UP_HOST_RESTART, /* Restart from host */
    WLAN_VDEV_SM_EV_STOP,            /* Stop VDEV */
    WLAN_VDEV_SM_EV_STOP_RESP,       /* FW responded to stop */
    WLAN_VDEV_SM_EV_DOWN,            /* Bring down VDEV */
    // ...
};

/* Dispatch event to state machine */
wlan_vdev_mlme_sm_deliver_evt(vdev, WLAN_VDEV_SM_EV_START, 0, NULL);
```

### VAP Deletion Flow

```
osif_ioctl_delete_vap()
         │
         ▼
osif_delete_vap()
         │
         ├──► wlan_vap_delete()           ← Delete ieee80211vap
         │           │
         │           ▼
         │    ieee80211_vap_delete()
         │
         ├──► ar_vdev_deinit()            ← Delete ar_vdev_s
         │
         ▼
osif_delete_vap_wait_and_free()
         │
         ▼
unregister_netdevice()                    ← Unregister athX
```

## OSIF Layer Functions

### Key OSIF Functions

| Function | Purpose |
|----------|---------|
| `osif_create_vap()` | Create VAP and net_device |
| `osif_delete_vap()` | Delete VAP |
| `osif_vap_open()` | Bring VAP interface up |
| `osif_vap_stop()` | Bring VAP interface down |
| `osif_vap_init()` | Initialize VAP for operation |
| `osif_attach()` | Attach OSIF to VAP, setup net_device_ops |
| `osif_detach()` | Detach OSIF from VAP |
| `osif_getstats()` | Get interface statistics |

### Data Path Integration

```
TX Path (User Space → Wireless):
  Application → Socket → net_device (athX)
                              │
                              ▼
                    osif_dev_ops.ndo_start_xmit (vap_hardstart)
                              │
                              ▼
                    osif_dev → ieee80211vap → ar_vdev_s
                              │
                              ▼
                    QCA Driver TX → Firmware → Radio

RX Path (Wireless → User Space):
  Radio → Firmware → QCA Driver RX
                              │
                              ▼
                    ar_vdev_s → ieee80211vap → osif_dev
                              │
                              ▼
                    netif_rx(skb) → net_device (athX)
                              │
                              ▼
                    Socket → Application
```

## Key Source Files

| File | Layer | Description |
|------|-------|-------------|
| `QCA/.../os/linux/src/osif_umac.c` | OSIF | Main OSIF implementation |
| `QCA/.../os/linux/src/osif_private.h` | OSIF | osif_dev structure definition |
| `QCA/.../umac/base/ieee80211_vap.c` | UMAC | VAP creation/deletion |
| `QCA/.../umac/include/ieee80211_var.h` | UMAC | ieee80211vap structure |
| `QCA/.../include/_ieee80211.h` | UMAC | ieee80211_opmode enum |
| `ar/core/src/ar_main.c` | Arista | ar_vdev_init/deinit |
| `ar/core/src/ar_types.h` | Arista | ar_vdev_s structure |
| `ar/vdrv_if/qca/common/vdrv_cp_if.c` | Arista | VDEV create/delete handlers |

## Kernel Internals

### net_device Registration

The VAP's `net_device` integrates with Linux networking via `register_netdevice()`. The key callbacks:

```c
struct net_device_ops osif_dev_ops = {
    .ndo_open         = osif_vap_open,       /* Called from dev_open() */
    .ndo_stop         = osif_vap_stop,       /* Called from dev_close() */
    .ndo_start_xmit   = vap_hardstart,       /* dev_queue_xmit() → hard_start_xmit */
    .ndo_do_ioctl     = ieee80211_ioctl,     /* ioctl(fd, SIOCDEVPRIVATE, ...) */
    .ndo_get_stats64  = osif_getstats,       /* /proc/net/dev, ifconfig */
    .ndo_set_rx_mode  = osif_set_multicast_list,  /* Multicast filter */
    .ndo_set_mac_address = osif_change_mac_addr,
    .ndo_change_mtu   = osif_change_mtu,
    .ndo_select_queue = osif_select_queue,   /* Multi-queue TX selection */
};
```

### ioctl Path (User → Kernel)

```
User Space:
  ioctl(sockfd, SIOCDEVPRIVATE + N, &iwreq)
         │
         ▼
Kernel (net/core/dev_ioctl.c):
  sock_ioctl() → dev_ioctl() → dev_ifsioc()
         │
         ▼
  ndo_do_ioctl(dev, ifr, cmd)
         │
         ▼
Driver (osif_umac.c):
  ieee80211_ioctl(dev, ifr, cmd)
         │
         ├── SIOCG80211STATS     → ieee80211_ioctl_getstats()
         ├── IEEE80211_IOCTL_GETPARAM → ieee80211_ioctl_getparam()
         ├── IEEE80211_IOCTL_SETPARAM → ieee80211_ioctl_setparam()
         ├── SIOC80211IFCREATE   → osif_ioctl_create_vap()
         ├── SIOC80211IFDESTROY  → osif_ioctl_delete_vap()
         └── Wireless Extensions → ieee80211_ioctl_iwpriv()
                                        │
                                        ▼
                              iw_handler_def → iw_priv_handlers[]
```

### sk_buff Flow (TX Path)

```
Application:
  send()/write() → socket layer → sk_buff allocation
         │
         ▼
Network Stack:
  dev_queue_xmit(skb)
         │
         ├── Qdisc processing (if configured)
         │
         ▼
  __dev_xmit_skb() → sch_direct_xmit()
         │
         ▼
  dev_hard_start_xmit()
         │
         ▼
Driver (osif_umac.c):
  vap_hardstart(skb, dev)
         │
         ├── osifp = netdev_priv(dev)        /* Get osif_dev */
         ├── vap = osifp->os_if              /* Get ieee80211vap */
         │
         ▼
  osif_vap_hardstart_generic(skb, dev)
         │
         ├── ieee80211_classify()            /* WMM/TID classification */
         ├── skb->priority = tid             /* Set TID in skb */
         │
         ▼
  ol_tx_ll_fast() / dp_tx()                  /* Offload TX path */
         │
         ├── Encapsulation (802.3 → 802.11)
         ├── Encryption (if needed)
         ├── DMA descriptor setup
         │
         ▼
  CE (Copy Engine) / HIF layer → Firmware → Radio
```

### sk_buff Flow (RX Path)

```
Hardware:
  Radio → Firmware decryption → DMA to host memory
         │
         ▼
Driver (Interrupt Context - NAPI):
  dp_rx_process() / htt_rx_amsdu_pop()
         │
         ├── skb = dev_alloc_skb(len)        /* Allocate sk_buff */
         ├── skb_put(skb, len)               /* Set data length */
         ├── Decapsulation (802.11 → 802.3)
         │
         ▼
  dp_rx_deliver_to_stack() / osif_deliver_data()
         │
         ├── skb->dev = osifp->netdev        /* Set athX as source */
         ├── skb->protocol = eth_type_trans(skb, dev)
         │
         ▼
  netif_rx(skb) or netif_receive_skb(skb)    /* Process context or NAPI */
         │
         ▼
Network Stack:
  __netif_receive_skb() → deliver_skb() → packet handlers
         │
         ▼
  ip_rcv() → tcp_rcv() → sk_receive_queue
         │
         ▼
Application:
  recv()/read()
```

### Synchronization Primitives

The driver uses multiple locking mechanisms:

```c
/* Per-VAP locks */
struct ieee80211vap {
    qdf_spinlock_t     iv_lock;              /* General VAP lock */
    qdf_mutex_t        iv_mlme_lock;         /* MLME operations */
    // ...
};

/* Arista layer uses */
struct ar_vdev_s {
    atomic_t bcn_ie_update_ongoing;          /* Atomic flag */
    // ...
};

struct ar_pdev_s {
    spinlock_t node_ht_lock;                 /* Hash table lock */
    // ...
};

/* OSIF layer */
struct _osif_dev {
    spinlock_t list_lock;                    /* pending_rx_frames list */
    spinlock_t nbuf_arr_lock;                /* fastpath buffer array */
    // ...
};
```

**Context considerations:**
- `spin_lock_bh()` - Bottom-half disabled, used when called from process context but shared with softirq
- `spin_lock_irqsave()` - IRQ disabled, used when shared with hardirq handler
- `rcu_read_lock()` - Read-side critical section for RCU-protected data (peer lookups)

### Reference Counting

Objects use reference counting for safe deletion:

```c
/* Object Manager reference counting */
wlan_objmgr_vdev_get_ref(vdev, WLAN_MLME_OBJ_REF);    /* Increment */
wlan_objmgr_vdev_release_ref(vdev, WLAN_MLME_OBJ_REF); /* Decrement */

/* Arista DP layer */
static inline void ar_dp_vdev_get_ref(struct ar_dp_vdev_s *vdev) {
    ar_obj_get_ref(&vdev->obj);   /* Atomic increment */
}

static inline void ar_dp_vdev_release_ref(struct ar_dp_vdev_s *vdev) {
    if (ar_obj_release_ref(&vdev->obj))  /* Returns true if zero */
        ar_os_free(vdev);
}

/* Typical pattern for safe access */
vdev = ar_dp_soc->dp_vdev_map[vdev_id];
if (vdev && ar_dp_vdev_get_ref(vdev)) {
    /* Use vdev safely */
    ar_dp_vdev_release_ref(vdev);
}
```

### Memory Allocation

```c
/* Kernel allocations */
ar_os_malloc(size)      → kmalloc(size, GFP_ATOMIC)   /* Can't sleep */
ar_os_zalloc(size)      → kzalloc(size, GFP_ATOMIC)   /* Zero-initialized */
ar_os_free(ptr)         → kfree(ptr)

/* DMA-coherent for descriptor rings */
dma_alloc_coherent(dev, size, &dma_handle, GFP_KERNEL)

/* sk_buff allocation */
dev_alloc_skb(len)      /* For RX, reserves headroom */
alloc_skb(len, GFP_ATOMIC)  /* In interrupt context */
```

### procfs / sysfs Interfaces

```
/proc/net/dev                           ← Interface statistics
/sys/class/net/athX/                    ← net_device sysfs
/sys/class/net/athX/address             ← MAC address
/sys/class/net/athX/operstate           ← up/down state
/proc/<pid>/fd/                         ← Open file descriptors
/proc/net/wireless                      ← Wireless stats (iwconfig)

/* Driver-specific proc entries */
/proc/sys/dev/wifi/                     ← QCA driver params
```

### NAPI (New API) Polling

RX uses NAPI to avoid interrupt storms:

```c
/* NAPI registration */
netif_napi_add(netdev, &dp_soc->napi, dp_rx_napi_poll, budget);
napi_enable(&dp_soc->napi);

/* Interrupt handler */
irqreturn_t dp_rx_interrupt(int irq, void *dev_id) {
    napi_schedule(&dp_soc->napi);      /* Schedule poll */
    return IRQ_HANDLED;
}

/* Poll function - runs in softirq context */
int dp_rx_napi_poll(struct napi_struct *napi, int budget) {
    int work_done = 0;
    while (work_done < budget && rx_ring_has_data()) {
        skb = dp_rx_process_one();
        netif_receive_skb(skb);
        work_done++;
    }
    if (work_done < budget) {
        napi_complete(napi);           /* Re-enable interrupts */
    }
    return work_done;
}
```

### Workqueue Deferred Processing

```c
/* Arista uses workqueues for deferred operations */
struct ar_dp_pdev_s {
    struct {
        struct workqueue_struct *workqueue;
        struct work_struct work;
    } defer;
};

/* Initialization */
pdev->defer.workqueue = create_singlethread_workqueue("ar_dp_defer");
INIT_WORK(&pdev->defer.work, ar_dp_defer_work_handler);

/* Schedule deferred work */
queue_work(pdev->defer.workqueue, &pdev->defer.work);

/* Cleanup */
flush_workqueue(pdev->defer.workqueue);
destroy_workqueue(pdev->defer.workqueue);
```

## Related Documentation

- [GO_CODEBASE.md](GO_CODEBASE.md) - Go agent architecture
- [KERNEL_USERSPACE.md](KERNEL_USERSPACE.md) - Kernel vs user space components
- [NETLINK_IOCTL.md](NETLINK_IOCTL.md) - Netlink and ioctl interfaces
- [DATAPATH_CONTROLPATH.md](DATAPATH_CONTROLPATH.md) - Data path and control path

