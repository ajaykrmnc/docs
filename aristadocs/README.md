# Arista Proprietary Documentation

⚠️ **CONFIDENTIAL - ARISTA NETWORKS INTERNAL USE ONLY**

This directory contains proprietary documentation related to Arista Networks WiFi Access Point development, including QCA driver integration, kernel patches, and internal build systems.

---

## 📁 Directory Structure

### `wlan-drivers/`
Documentation for Qualcomm (QCA) WiFi driver integration with Arista code:
- QCA binary driver integration architecture
- WLAN driver terminology and concepts
- Data path and control path documentation
- QoS configuration and testing
- TID investigation reports
- VAP and OSIF documentation
- ar_meta_cache implementation

### `wifi-and-wireless/`
WiFi and wireless networking documentation:
- Hotspot connection pathway (complete 8-phase guide)
- AP data generation
- DHCP and beacon handling
- HOSTAPD configuration
- Inter-AP communication
- RADIUS authentication
- WPA/WPA2 security
- WiFi standards compliance
- Ethernet vs WiFi comparison

### `networking/`
Arista AP-specific networking documentation:
- TOS (Type of Service) implementation
- DSCP documentation
- QoS downstream traffic management
- Bridges and tunnels
- VXLAN and tunnel interfaces
- Network interface documentation
- Upstream/downstream traffic
- Proxy configuration
- DHCP documentation

### `kernel-and-system/`
Kernel patches and system-level documentation:
- AR meta cache debug guide
- ar_meta field in sk_buff
- sk_buff modification guides
- Kernel-userspace communication
- Kernel build lifecycle
- Linux 5.4 patch workflow
- Netlink and IOCTL
- Kernel patch management

### `build-and-tooling/`
Build system and tooling documentation:
- ARM vs x86 architecture guide
- Cross-compilation guide
- Makefile commands
- Repository analysis and rebuild estimation

### `programming-languages/`
Language-specific documentation:
- Go codebase structure (Arista AP)

### `remove-dev/`
Remote development setup:
- SSH connectivity issues (IPv6 corporate network)

### `testing/`
Testing documentation:
- Playwright presentation

---

## 🔒 Confidentiality Notice

This documentation contains:
- Proprietary Arista Networks implementation details
- QCA (Qualcomm) driver integration specifics
- Internal build system configurations
- Corporate network infrastructure details
- Custom kernel patches and modifications

**Do not share outside of Arista Networks.**

---

## 📚 Key Topics Covered

- **WiFi Driver Development**: QCA binary integration, vendor interfaces, data/control paths
- **Kernel Development**: Custom sk_buff modifications, ar_meta cache, patch management
- **Network Engineering**: QoS, TOS/DSCP, VXLAN, tunneling, bridge configuration
- **Build Systems**: Cross-compilation, ARM/x86 architecture, ccache, distributed builds
- **Testing**: QoS testing, AP functionality testing, Playwright automation

---

## 🔗 Related Resources

- Internal GitLab: `https://gitlab.aristanetworks.com/ajay.kumar/docs`
- WiFi Build System: `http://wifi-build.sjc.aristanetworks.com/`
- Distribution Server: `http://dist.aristanetworks.com/storage/wifi`

---

**Last Updated:** March 2026
**Maintained by:** Ajay Kumar (@ajay.kumar@arista.com)
