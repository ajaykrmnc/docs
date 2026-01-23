# Drivers Used in the Repository

This document provides an overview of all drivers used in this project, including WLAN drivers, platform drivers, and network subsystem components.

## Driver Categories

### 1. WLAN Drivers

#### Arista WLAN Driver (`ar/`)

The main Arista WLAN driver code located at `src/wlan-drivers/ar/`:

| Component | Path | Description |
|-----------|------|-------------|
| Core | `ar/core/src/` | Core business logic |
| Data Path | `ar/core/src/ar_dp.c` | TX/RX packet handling |
| QoS | `ar/core/src/ar_qos.c` | TID/AC mapping |
| APC | `ar/core/src/ar_apc.c` | Access Point Controller |
| ACL | `ar/core/src/ar_acl.c` | Access Control Lists |
| ARP | `ar/core/src/ar_arp.c` | ARP handling |
| Config | `ar/core/src/ar_cfg.c` | Configuration management |
| Control Path | `ar/core/src/ar_cp.c` | Management frame handling |
| Events | `ar/core/src/ar_evt.c` | Driver events, notifications |
| Main | `ar/core/src/ar_main.c` | Module initialization |
| Proc | `ar/core/src/ar_proc.c` | Procfs interface |
| Proxy ARP | `ar/core/src/ar_proxyarp.c` | DHCP/ARP proxying |
| Radiotap | `ar/core/src/ar_radiotap.c` | Monitor mode |
| Background Mon | `ar/core/src/ar_bgmon.c` | Channel/radio monitoring |
| Scanning | `ar/core/src/ar_cs_scan.c` | Off-channel scanning |
| AP Management | `ar/core/src/ar_mgmt_ap.c` | BSS management |
| RF Neighbor | `ar/core/src/ar_rf_nbr.c` | Neighbor AP detection |
| IE Handling | `ar/core/src/ar_ie.c` | 802.11 IE parsing/building |

#### Null AP Driver Module

- **Location**: `src/wlan-drivers/null_apdrv_mod/`
- **Purpose**: Stub/null driver for testing

### 2. hostapd/wpa_supplicant Drivers

Located at `src/hostapd-2.10/src/drivers/` and `src/wpa_supplicant-2.9/src/drivers/`:

| Driver | Config Flag | Description |
|--------|-------------|-------------|
| NL80211 | `CONFIG_DRIVER_NL80211` | Primary Linux wireless driver |
| NL80211 QCA | `CONFIG_DRIVER_NL80211_QCA` | Qualcomm vendor extensions |
| NL80211 BRCM | `CONFIG_DRIVER_NL80211_BRCM` | Broadcom vendor extensions |
| WEXT | `CONFIG_DRIVER_WEXT` | Wireless Extensions (legacy) |
| HostAP | `CONFIG_DRIVER_HOSTAP` | HostAP driver |
| BSD | `CONFIG_DRIVER_BSD` | BSD network driver |
| OpenBSD | `CONFIG_DRIVER_OPENBSD` | OpenBSD driver |
| NDIS | `CONFIG_DRIVER_NDIS` | Windows NDIS driver |
| Wired | `CONFIG_DRIVER_WIRED` | Wired 802.1X driver |
| MACsec Linux | `CONFIG_DRIVER_MACSEC_LINUX` | Linux MACsec driver |
| MACsec QCA | `CONFIG_DRIVER_MACSEC_QCA` | Qualcomm MACsec driver |
| Atheros | `CONFIG_DRIVER_ATHR` | Atheros driver |
| Roboswitch | `CONFIG_DRIVER_ROBOSWITCH` | Roboswitch driver |

### 3. Platform/Reset Drivers

#### GPIO Button Hotplug Driver

- **Location**: `platform/common/src/reset_driver/`
- **Module**: `gpio-button-hotplug`
- **File**: `gpio-button-hotplug.c`
- **Purpose**: Handles reset button events via GPIO
- **Features**:
  - Platform driver for `gpio-keys` and `gpio-keys-polled`
  - Creates `/proc/sensor_reset` for reset button status
  - Sends netlink events for button press/release

### 4. Network Subsystem (NSS) Drivers

Qualcomm NSS drivers for hardware-accelerated networking:

| Module | Description | Platform |
|--------|-------------|----------|
| `nssdp` | NSS Data Plane | All QCA platforms |
| `nssdrv` (`qca-nss-drv`) | Main NSS driver | HAWKEYE |
| `nsscrypto` | NSS crypto acceleration | HAWKEYE |
| `nsscfi` | NSS CFI interface | HAWKEYE |
| `nsscl` | NSS Client interface | HAWKEYE |
| `nssppe` | NSS Packet Processing Engine | BELLS/MIAMI |
| `nsseip` | NSS EIP security | BELLS/MIAMI |

### 5. Ethernet/Switch Drivers

| Module | Description |
|--------|-------------|
| `ssdk` | Switch SDK |
| `ssdksh` | SSDK Shell interface |
| `edma` | Enhanced DMA driver (HAWKEYE) |
| `nat46` | NAT46 translation |
| `realtek-phy` | Realtek PHY driver (BELLS, conditional) |

### 6. BLE (Bluetooth Low Energy) Drivers

- **Platforms**: HAWKEYE, BELLS, MIAMI
- **Condition**: `BLE_SUPPORT = TRUE`
- **Components**:
  - HCI attach scripts
  - BLE configuration functions
  - Platform-specific BLE setup (`ble_functions`)

### 7. GPS Drivers

| Module | Condition | Description |
|--------|-----------|-------------|
| `gps` | `GPS_CAPABLE = 1` | GPS support module |
| `gpsd` | `GPS_CAPABLE = 1` | GPS daemon |
| `upgrade_gps` | `UART_GPS_CAPABLE = 1` | UART GPS upgrade |
| `qtlgpsi2cupd` | `QTL_GPS_CAPABLE = 1` | Quectel GPS I2C updater |
| `anld` | `DNI_GPS_CAPABLE = 1` | DNI GPS module |

### 8. Kernel Modules (Internal)

| Module | Description |
|--------|-------------|
| `ipwcmask` | IP wildcard mask |
| `bpipe` | Buffered pipe |
| `bcmcopt` | Broadcast/multicast options |
| `pktmngl` | Packet mangling |
| `arutils` | Arista utilities |
| `ca` | Content analytics |
| `ipthrole` | IPtables role |
| `ipthfw` | IPtables firewall |
| `ipthappfw` | IPtables app firewall |
| `testdev` | Test device |
| `ar_match` | Arista match module |
| `upskiso` | UPSK isolation |
| `gwmac` | Gateway MAC |
| `qca_mcs` | QCA multicast (conditional) |
| `tcpmss` | TCP MSS module (conditional) |
| `arpkttrace` | AR packet trace |
| `l2proxy` | L2 proxy |
| `arkerneltoggle` | Kernel toggle |

### 9. Wireless Driver Modules

| Module | Condition | Description |
|--------|-----------|-------------|
| `arwlandrv` | Always | Main Arista WLAN driver |
| `apdrv` | Always | AP driver module |
| `sendrv` | `CMN_AP_SEN_DRV != 1` | Sensor driver |
| `3raddrv` | `PLATFORM_TYPE = 11ax_3Radio` | 3-radio driver |
| `cnss2` | `CNSS2_MODULE_SUPPORT = TRUE` | CNSS2 platform driver |

### 10. Security/Crypto Drivers

| Module | Condition | Description |
|--------|-----------|-------------|
| `tpm_fw_upg` | `TPM2_UPGRADE_SUPPORT = TRUE` | TPM firmware upgrade |

### 11. Spectral Analysis

| Module | Condition | Description |
|--------|-----------|-------------|
| `athssd` | `SPECTRAL_ANALYSIS_SUPPORT = TRUE` | Atheros spectral scan daemon |

## Driver Dependencies

```
kernel
├── nssdp
│   ├── ssdk
│   ├── nssdrv (depends on nssdp, ssdk on some platforms)
│   └── nssppe
├── rstdrv (reset driver)
├── arwlandrv
│   └── QCA licensed drivers
└── nl (libnl)
    └── qcanl (QCA NL80211 lib)
```

## Platform-Specific Module Lists

### HAWKEYE Platform
```
ENET_MODULES: nssdp edma ssdk ssdksh nssdrv nsscrypto nsscfi nsscl
PLAT_MODULES: kernel $(ENET_MODULES) bootldr sdk-rootfs rstdrv ble
```

### BELLS Platform
```
ENET_MODULES: nssdp ssdk nssppe nat46 ssdksh [realtek-phy]
PLAT_MODULES: $(ENET_MODULES) kernel bootldr rstdrv part nsseip ble gps sdk-rootfs cnss2
```

### MIAMI Platform
```
ENET_MODULES: nssdp ssdk nssppe nat46 ssdksh
PLAT_MODULES: nsseip $(ENET_MODULES) kernel bootldr rstdrv part ble gps sdk-rootfs tpm_fw_upg
```

