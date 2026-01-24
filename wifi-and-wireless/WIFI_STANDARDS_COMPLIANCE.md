# WiFi Standards Compliance and Testing

This document describes how the AP repository follows WiFi standards (IEEE 802.11) and the tests used to validate compliance.

## Supported WiFi Standards

### IEEE 802.11 Protocol Generations

| Standard | Description | Max Protocol ID | Supported |
|----------|-------------|-----------------|-----------|
| 802.11a | Legacy 5GHz OFDM | 1 | ✓ |
| 802.11b/g | Legacy 2.4GHz | 1 | ✓ |
| 802.11n (WiFi 4) | High Throughput (HT) | 2 | ✓ |
| 802.11ac (WiFi 5) | Very High Throughput (VHT) | 3 | ✓ |
| 802.11ax (WiFi 6/6E) | High Efficiency (HE) | 4 | ✓ |
| 802.11be (WiFi 7) | Extremely High Throughput (EHT) | 5 | ✓ |

### Frequency Bands

- **2.4 GHz Band**: Channels 1-14 (20/40 MHz)
- **5 GHz Band**: Channels 36-165 (20/40/80/160/80+80 MHz)
- **6 GHz Band**: Channels 1-233 (20/40/80/160/320 MHz)

### Channel Widths

| Width | Protocol Support |
|-------|------------------|
| 20 MHz | 802.11a/b/g/n/ac/ax/be |
| 40 MHz | 802.11n/ac/ax/be |
| 80 MHz | 802.11ac/ax/be |
| 160 MHz | 802.11ac/ax/be |
| 80+80 MHz | 802.11ac/ax/be |
| 320 MHz | 802.11be only |

## Security Standards

### WPA/WPA2/WPA3 Support

| Security Mode | Key Management | Tests |
|---------------|----------------|-------|
| Open | None | ClientConnectivityTest |
| WPA-PSK | Pre-Shared Key | ClientConnectivityTest, ApRoleRedirection |
| WPA2-PSK | Pre-Shared Key | ClientConnectivityTest |
| WPA3-SAE | Simultaneous Authentication of Equals | ApFipsSSIDTest, ClientConnectivityTest |
| WPA2-WPA3 Mixed | Transition Mode | ClientConnectivityTest, ApRoleRedirection |
| WPA-DOT1X | 802.1X/EAP | ClientConnectivityTest, WiredClientTest |
| WPA3-DOT1X | 802.1X Enterprise | ApOpenConfigTest |
| WPA3-DOT1X-192 | Suite B 192-bit | ApOpenConfigTest |
| OWE | Opportunistic Wireless Encryption | ApAfcConnectivityTest |
| UPSK | User Pre-Shared Key | ClientConnectivityTest, UpskIsoTest |

### 802.1X Authentication

- EAP-TLS support with certificate provisioning
- RADIUS server integration
- COA (Change of Authorization) support
- MAC authentication
- RADIUS accounting

## Advanced WiFi Features

### 802.11r - Fast BSS Transition (FT)

- Mobility Domain support
- PMK-R0/R1 key caching
- Fast transition roaming between APs
- **Tests**: ClientRoamingTest, PMKCacheSyncTest

### 802.11k - Radio Resource Management (RRM)

- Neighbor reports
- Link measurement
- Beacon reports
- **Tests**: NeighborReportTest, BeaconReportTest

### 802.11v - Wireless Network Management (WNM)

- BSS Transition Management
- BSS Termination notices
- **Tests**: ClientRoamingTest

### DFS (Dynamic Frequency Selection)

- Radar detection and channel switching
- CAC (Channel Availability Check)
- NOL (Non-Occupancy List) management
- **Tests**: ApDfsTest, ApAcsDfsTest, ApDfsInfoSharingTest

### 6 GHz / AFC (Automated Frequency Coordination)

- Standard Power AP support
- AFC server communication
- Grace period handling
- **Tests**: ApAfcConnectivityTest, AfcIndoorLocationTest

### WiFi 7 (802.11be) Features

- Multi-Link Operation (MLO)
- 320 MHz channel width support
- Preamble Puncturing
- MRU (Multiple Resource Units)
- **Tests**: MloMbssTest, MwmApInterfaceListTest

### 802.11ax (WiFi 6) Features

- OFDMA (Downlink/Uplink)
- MU-MIMO (Downlink/Uplink)
- BSS Coloring
- Spatial Reuse
- Target Wake Time (TWT)

## Test Categories

### Basic Sanity Tests (BasicSanity Suite)

| Test | Description |
|------|-------------|
| ClientConnectivityTest | Client connection with various security modes |
| ClientConnectivityTestMwm | Client connectivity via management platform |
| ApIpChangeTest | AP IP address change handling |
| ApNeighborhoodTest | AP neighbor discovery |
| ClientRoamingTest | Client roaming between APs |

### Advanced Tests (Advanced Suite)

| Test | Description |
|------|-------------|
| ApAfcConnectivityTest | AFC functionality for 6GHz |
| ApDfsInfoSharingTest | DFS radar info sharing |
| ApPacketCaptureTest | 802.11 frame capture and validation |
| ApMeshTest | Mesh network formation |
| ValidateBeaconTest | Beacon frame validation |
| ValidateCapabilityTest | Client capability validation |
| CertProvisioningTest | Certificate provisioning |
| AuthSurvivabilityModeTest | RADIUS failover handling |

### Protocol Validation Tests

| Test | What It Validates |
|------|-------------------|
| ApPacketCaptureTest | 802.11 Auth/Assoc, EAPOL handshake, SAE commit/confirm |
| ValidateBeaconTest | Beacon contents, supported rates, QBSS Load IE |
| ValidateCapabilityTest | Client capabilities in association request |
| ApDfsTest | Radar detection, CAC, channel switching |

## Running Tests

Tests are organized using the `ptest-suite` framework:

```bash
# Run BasicSanity suite
./WifiClusterTest/ptest-suite --suite BasicSanity

# Run specific test
./WifiClusterTest/ctest/ClientConnectivityTest.py --security=wpa3-sae

# Run with specific variant
./WifiClusterTest/ctest/ApMeshTest.py --radioBand=6G --wifi7
```

## Platform Capabilities

AP capabilities are defined in `ap_capability.conf` files per platform:

```
# Protocol capability bits: a(0), an(1), bg(2), bgn(3), ac(4), ax(5), be(6)
WIFI_MAX_PROTOCOL=5        # 11be
WIFI_MAX_CHAN_WIDTH=6      # 320MHz
DFS_CAPABILITY=1           # DFS supported
```

