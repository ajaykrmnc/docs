# Hostapd - WiFi Access Point Daemon

This document describes the hostapd implementation in this repository, covering authentication, security modes, configuration, and integration with Arista AP infrastructure.

## Overview

Hostapd is the IEEE 802.11 access point management daemon that handles:
- Client authentication and association
- WPA/WPA2/WPA3 key management
- IEEE 802.1X/EAP authentication
- RADIUS integration
- Fast BSS Transition (802.11r)
- Radio Resource Management (802.11k)
- Wireless Network Management (802.11v)

## Security Modes

### Personal (PSK-based)

| Mode | Key Management | Description |
|------|---------------|-------------|
| **WPA-PSK** | WPA-PSK | Legacy WPA with TKIP/CCMP |
| **WPA2-PSK** | WPA-PSK | WPA2 with CCMP (AES) |
| **WPA3-SAE** | SAE | Simultaneous Authentication of Equals |
| **WPA3-SAE-Transition** | SAE + WPA-PSK | Mixed mode for compatibility |

### Enterprise (802.1X)

| Mode | Key Management | Description |
|------|---------------|-------------|
| **WPA-Enterprise** | WPA-EAP | WPA with RADIUS authentication |
| **WPA2-Enterprise** | WPA-EAP | WPA2 with RADIUS authentication |
| **WPA3-Enterprise** | WPA-EAP-SHA256 | WPA3 with enhanced security |
| **WPA3-Enterprise-192** | WPA-EAP-SUITE-B-192 | Suite B 192-bit security |

### Enhanced Open

| Mode | Key Management | Description |
|------|---------------|-------------|
| **OWE** | OWE | Opportunistic Wireless Encryption |
| **OWE-Transition** | OWE + OPEN | Mixed mode with hidden OWE network |

## EAP Methods

The integrated EAP server supports:

| Method | Config Flag | Description |
|--------|-------------|-------------|
| EAP-TLS | `CONFIG_EAP_TLS` | Certificate-based authentication |
| EAP-TTLS | `CONFIG_EAP_TTLS` | Tunneled TLS |
| EAP-PEAP | `CONFIG_EAP_PEAP` | Protected EAP |
| EAP-MSCHAPv2 | `CONFIG_EAP_MSCHAPV2` | Microsoft Challenge Handshake |
| EAP-GTC | `CONFIG_EAP_GTC` | Generic Token Card |
| EAP-SIM | `CONFIG_EAP_SIM` | SIM card authentication |
| EAP-AKA | `CONFIG_EAP_AKA` | USIM authentication |
| EAP-AKA' | `CONFIG_EAP_AKA_PRIME` | Improved AKA |
| EAP-MD5 | `CONFIG_EAP_MD5` | MD5-Challenge |

## Advanced Features

### Unique PSK (UPSK)

Per-client unique PSK obtained from RADIUS server:
- RADIUS returns PSK in `Tunnel-Password` attribute
- Enables individual client credentials without 802.1X complexity
- Supports UPSK Isolation for client separation

```
wpa_psk_radius=2  # Required - reject if no Tunnel-Password
upsk_enabled=1
```

### Group PSK (GPSK)

Role-based PSK assignment:
- Different PSKs mapped to different client roles
- RADIUS returns role information
- Supports VLAN assignment per role

### Fast Transition (802.11r)

```
ieee80211r=1
mobility_domain=<MDID>
r0_key_holder=<R0KH-ID>
r1_key_holder=<R1KH-ID>
r0kh=<neighbor AP R0KH config>
r1kh=<neighbor AP R1KH config>
ft_over_ds=1
pmk_r1_push=1
```

### OKC (Opportunistic Key Caching)

```
okc=1
```

## Build Configuration

Key compile-time options in `.config`:

```makefile
# Core Features
CONFIG_ATN=y                # Arista AP integration
CONFIG_IEEE80211W=y         # Management Frame Protection
CONFIG_IEEE80211R=y         # Fast BSS Transition
CONFIG_IEEE80211N=y         # 802.11n HT
CONFIG_IEEE80211AC=1        # 802.11ac VHT
CONFIG_IEEE80211AX=1        # 802.11ax HE (WiFi 6)
CONFIG_IEEE80211BE=y        # 802.11be EHT (WiFi 7)

# Security Features
CONFIG_SAE=y                # WPA3-Personal
CONFIG_SAE_PK=y             # SAE Public Key
CONFIG_OWE=y                # Opportunistic Wireless Encryption
CONFIG_FILS=y               # Fast Initial Link Setup
CONFIG_DPP=y                # Device Provisioning Protocol
CONFIG_DPP2=y               # DPP 2.0
CONFIG_DPP3=y               # DPP 3.0
CONFIG_SUITEB=y             # Suite B cryptography
CONFIG_SUITEB192=y          # Suite B 192-bit

# Advanced Features
CONFIG_WNM=y                # Wireless Network Management
CONFIG_MBO=y                # Multi-Band Operation
CONFIG_HS20=y               # Hotspot 2.0 / Passpoint
CONFIG_WPS=y                # Wi-Fi Protected Setup
CONFIG_ACS=y                # Automatic Channel Selection
CONFIG_FST=y                # Fast Session Transfer
CONFIG_MLO=y                # Multi-Link Operation (WiFi 7)
CONFIG_PASN=y               # Pre-Association Security Negotiation
```

## RADIUS Configuration

### Authentication Server

```
auth_server_addr=<IP>
auth_server_port=1812
auth_server_shared_secret=<secret>
radius_client_intf=<interface>
```

### Accounting

```
acct_server_addr=<IP>
acct_server_port=1813
acct_server_shared_secret=<secret>
radius_acct_interim_interval=600
```

### Change of Authorization (CoA/DM)

```
radius_das_enable=1
radius_coa_enable=1
radius_das_port=3799
```

## Arista-Specific Extensions

### Source Files

| File | Purpose |
|------|---------|
| `ar_main.c` | Arista main entry point and initialization |
| `ar_config_file.c` | Extended configuration parsing |
| `ar_wpa_auth.c` | WPA authentication extensions |
| `ar_wpa_auth_ft.c` | Fast Transition extensions |
| `ar_upsk.c` | Unique PSK implementation |
| `ar_upsk_iso.c` | UPSK isolation |
| `ar_sec_auth_cache.c` | Security authentication cache |
| `ar_accounting.c` | RADIUS accounting extensions |
| `ar_gauth.c` | Guest authentication |
| `ar_vlan_mapping.c` | Dynamic VLAN assignment |
| `ar_ieee802_1x.c` | 802.1X extensions |

### Inter-AP Communication

Hostapd integrates with synch_agent for:
- OKC cache synchronization
- FT key distribution (PMK-R0/R1)
- Security authentication cache sync
- Client roaming coordination

### ArDS Integration

```c
// ArDS client initialization for hostapd
rc = MarcoCCreate("hostapd");
rc = MarcoCDoInit(argc, argv);
```

## Configuration Files

| File | Description |
|------|-------------|
| `/opt/ap/hostapd.conf` | Main hostapd configuration |
| `/tmp/profile&lt;N&gt;/sec_profile` | Per-SSID security profile |
| `/opt/ap/sensor/auth.conf` | Authentication key file |

## Runtime Management

### Control Interface

```bash
# Add VAP
hostapd_cli -p /var/run/hostapd ADD <interface>

# Remove VAP
hostapd_cli -p /var/run/hostapd REMOVE <interface>

# Status
hostapd_cli -p /var/run/hostapd status
```

### Init Script

```bash
/opt/ap/etc/init.d/hostapd.init start
/opt/ap/etc/init.d/hostapd.init stop
/opt/ap/etc/init.d/hostapd.init restart
```

