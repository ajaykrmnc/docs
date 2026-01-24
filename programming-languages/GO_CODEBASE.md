# Go Codebase (`ap/src/go/`)

This document describes the Go codebase location, structure, and how it fits within the overall AP repository hierarchy.

## Location in Repository Hierarchy

```
ap/                                 # Repository root
├── docs/                           # Documentation
├── ap/                             # Main AP source tree
│   ├── src/                        # All source code
│   │   ├── go/                     # ◄── GO CODEBASE
│   │   │   ├── arista-ap/          # Main Go module
│   │   │   ├── blobs/              # External dependencies
│   │   │   └── pkg/                # Go package cache
│   │   ├── wlan-drivers/           # Kernel drivers (C)
│   │   ├── common/                 # Common C libraries
│   │   ├── hostapd-2.10/           # hostapd (C)
│   │   ├── wl_evt_handler/         # Event handler (C)
│   │   ├── cli/                    # CLI (C)
│   │   └── ...                     # Other C components
│   ├── rootfs/                     # Root filesystem overlay
│   └── platform/                   # Platform-specific configs
└── vendors/                        # Third-party vendor code
```

## Go vs C Components

The AP software stack is split between C and Go:

| Component | Language | Location | Purpose |
|-----------|----------|----------|---------|
| WLAN Drivers | C | `ap/src/wlan-drivers/` | Kernel-space driver, DP/CP |
| hostapd | C | `ap/src/hostapd-2.10/` | 802.1X, WPA, RADIUS |
| Event Handler | C | `ap/src/wl_evt_handler/` | Driver event processing |
| Common Libraries | C | `ap/src/common/` | Shared C utilities |
| **Management Agents** | **Go** | `ap/src/go/arista-ap/` | User-space management |
| **OpenConfig Agent** | **Go** | `ap/src/go/arista-ap/ocagent/` | gNMI/gNOI server |
| **Config Agent** | **Go** | `ap/src/go/arista-ap/configagent/` | Configuration application |
| **RRM Agent** | **Go** | `ap/src/go/arista-ap/rrmagent/` | Radio Resource Management |

## Go Module Structure (`ap/src/go/arista-ap/`)

### Executables (`cmd/`)

Entry points for Go binaries:

| Binary | Location | Description |
|--------|----------|-------------|
| `ocagent` | `cmd/ocagent/` | OpenConfig gNMI/gNOI agent |
| `configagent` | `cmd/configagent/` | Configuration application agent |
| `rrmagent` | `cmd/rrmagent/` | Radio Resource Management agent |
| `gobin` | `cmd/gobin/` | Multi-purpose binary (trigger manager, health monitor) |
| `cloudagent` | `cmd/cloudagent/` | Cloud connectivity agent |
| `arqwrap` | `cmd/arqwrap/` | QCA QWRAP helper |
| `client_datapath` | `cmd/client_datapath/` | Client datapath debugging tool |
| `aeroscout` | `cmd/aeroscout/` | AeroScout RTLS integration |
| `mldaddrtool` | `cmd/mldaddrtool/` | MLD address tool |

### Core Packages

#### Agent Packages

| Package | Purpose |
|---------|---------|
| `ocagent/` | OpenConfig agent - gNMI Get/Set/Subscribe, gNOI operations |
| `configagent/` | Applies configuration to radios, SSIDs, security |
| `rrmagent/` | RRM - channel selection, TPC, DFS |
| `cloudagent/` | Cloud connectivity and registration |
| `gobin/` | Trigger/timer handlers, health monitoring |

#### Configuration & State

| Package | Purpose |
|---------|---------|
| `config/` | Device configuration parsing (SSID, radio, security) |
| `ardsconfwriter/` | ARDS (Arista Realtime Data Store) configuration writers |
| `devconfstate/` | Device configuration state management |
| `flatapconf/` | Flat AP configuration format |

#### Network & Wireless

| Package | Purpose |
|---------|---------|
| `wlanioctl/` | WLAN ioctl interface to kernel driver |
| `netlink/` | Netlink interface for driver communication |
| `katunnel/` | L2/IPsec tunnel management |
| `vlan/` | VLAN configuration and management |
| `wiredconf/` | Wired interface configuration |
| `wiredfeatures/` | Wired network features |
| `nwutils/` | Network utilities |
| `iptables/` | iptables rule management |

#### Radio & Wireless Features

| Package | Purpose |
|---------|---------|
| `radioutils/` | Radio utility functions |
| `tpc/` | Transmit Power Control |
| `ppstate/` | Preamble Puncture state |
| `afc/` | Automatic Frequency Coordination (6 GHz) |
| `gps/` | GPS location services |
| `wifiutil/` | WiFi utility functions |
| `scheduledssid/` | Scheduled SSID enable/disable |

#### Infrastructure

| Package | Purpose |
|---------|---------|
| `aputils/` | Common AP utilities |
| `utils/` | General utilities |
| `constants/` | Shared constants |
| `path/` | File path definitions |
| `logwriter/` | Log file management |
| `procinfo/` | Process information |
| `procd/` | procd service management |
| `reboot/` | Reboot handling |
| `profiler/` | Performance profiling |

#### Security & Certificates

| Package | Purpose |
|---------|---------|
| `certutils/` | Certificate utilities |
| `certrevocation/` | Certificate revocation checking |
| `tpmutils/` | TPM utilities |
| `rpm/` | RADIUS proxy manager |

#### gNMI/gNOI

| Package | Purpose |
|---------|---------|
| `gnmi/` | gNMI server implementation |
| `gnoi/` | gNOI (gRPC Network Operations Interface) |
| `rshell/` | Remote shell server |
| `packet_capture/` | Packet capture service |

#### Monitoring & Debugging

| Package | Purpose |
|---------|---------|
| `aphm/` | AP Health Monitor |
| `apremedy/` | AP remediation actions |
| `debugbundle/` | Debug bundle generation |
| `techsupport/` | Tech support collection |
| `perfstat/` | Performance statistics |
| `sensord/` | Sensor daemon interface |
| `client_datapath/` | Client datapath debugging |

#### Generated Code (`gen/`)

Auto-generated Go code from protobuf/YANG:

| Package | Source |
|---------|--------|
| `gen/ocstruct/` | OpenConfig YANG models |
| `gen/wificonfig/` | WiFi configuration protobufs |
| `gen/wldrvstate/` | WLAN driver state protobufs |
| `gen/radiomgrstate/` | Radio manager state |
| `gen/deviceconfig/` | Device configuration |
| `gen/adminops/` | Admin operations |
| `gen/tunnelInfo/` | Tunnel information |

### Vendor-Specific Code (`qca/`)

QCA SPF version-specific implementations:

```
qca/
├── spf11dot1/           # SPF 11.1
├── spf11dot4csu1/       # SPF 11.4 CSU1
├── spf12dot2csu2/       # SPF 12.2 CSU2
└── spf12dot5cs/         # SPF 12.5 CS
```

## Build System

### Makefile Integration

```makefile
# From go.mk
go_mod = go
go_src = $(AP_SRC_DIR)/go/arista-ap/
go_bld = $(BLD_DIR_TC)
go_dep = s4common wificonfig testmodel radiomgrstate commproto rrm ...
```

### Build Outputs

Binaries are built to `$(BLD_DIR)/`:

| Target | Binary |
|--------|--------|
| `TGTGOBIN` | `gobin` |
| `TGTOCAGENT` | `ocagent` |
| `TGT_RRM_AGENT` | `rrmagent` |
| `TGT_CONFIG_AGENT` | `configagent` |
| `TGT_CLOUD_AGENT` | `cloudagent` |
| `TGT_ARQWRAP_AGENT` | `arqwrap` |

## Runtime Architecture

### Process Hierarchy

```
┌─────────────────────────────────────────────────────────────────────┐
│                          AP Runtime                                  │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │                      KERNEL SPACE                             │  │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐   │  │
│  │  │ arwlandrv   │  │   gwmac     │  │  Other kernel mods   │   │  │
│  │  │ (ar_dp.c)   │  │             │  │                      │   │  │
│  │  └─────────────┘  └─────────────┘  └─────────────────────┘   │  │
│  └──────────────────────────────────────────────────────────────┘  │
│                              │                                       │
│                         ioctl/netlink                                │
│                              │                                       │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │                      USER SPACE                               │  │
│  │                                                                │  │
│  │  ┌─────────────────────────────────────────────────────────┐ │  │
│  │  │                   GO AGENTS                              │ │  │
│  │  │  ┌───────────┐ ┌──────────────┐ ┌───────────────────┐   │ │  │
│  │  │  │ ocagent   │ │ configagent  │ │    rrmagent       │   │ │  │
│  │  │  │ (gNMI)    │ │ (config)     │ │    (RRM)          │   │ │  │
│  │  │  └───────────┘ └──────────────┘ └───────────────────┘   │ │  │
│  │  │  ┌───────────┐ ┌──────────────┐ ┌───────────────────┐   │ │  │
│  │  │  │  gobin    │ │ cloudagent   │ │     arqwrap       │   │ │  │
│  │  │  │ (triggers)│ │ (cloud)      │ │    (QWRAP)        │   │ │  │
│  │  │  └───────────┘ └──────────────┘ └───────────────────┘   │ │  │
│  │  └─────────────────────────────────────────────────────────┘ │  │
│  │                                                                │  │
│  │  ┌─────────────────────────────────────────────────────────┐ │  │
│  │  │                    C DAEMONS                             │ │  │
│  │  │  ┌───────────┐ ┌──────────────┐ ┌───────────────────┐   │ │  │
│  │  │  │ hostapd   │ │  wlevtd      │ │    portald        │   │ │  │
│  │  │  │ (802.1X)  │ │ (events)     │ │   (captive)       │   │ │  │
│  │  │  └───────────┘ └──────────────┘ └───────────────────┘   │ │  │
│  │  └─────────────────────────────────────────────────────────┘ │  │
│  └──────────────────────────────────────────────────────────────┘  │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

### Inter-Process Communication

| Mechanism | Usage |
|-----------|-------|
| ARDS (SysDB) | Primary config/state store between agents |
| Netlink | Go agents ↔ kernel driver |
| ioctl | Go agents ↔ kernel driver (wlanioctl) |
| Unix Socket | Inter-agent communication |
| gRPC | External ↔ ocagent (gNMI/gNOI) |

## Key Interfaces

### To Kernel Driver

```go
// wlanioctl/wlan_ioctl.go - ioctl interface
// netlink/netlink.go - netlink interface
```

### To ARDS (State Store)

```go
// ardsconfwriter/ - Write configuration to ARDS
// Uses: code.arista.io/eos/octa/agent/ards
// Uses: code.arista.io/eos/octa/sysdb/mount
```

### To External Controllers (gNMI)

```go
// ocagent/agent.go - gNMI server
// gnmi/server.go - gNMI implementation
// gnoi/server.go - gNOI implementation
```

## Development

### Dependencies

Go module path: `arista.io/ap`

External dependencies:
- `code.arista.io/eos/octa/` - Arista OCTA libraries
- `github.com/openconfig/gnmi/` - gNMI protocol
- `github.com/aristanetworks/glog` - Logging

### Testing

Run tests from `ap/src/go/arista-ap/`:
```bash
go test ./...
```

### Building

```bash
# From ap/ root
make go
```

## Related Documentation

- [DATAPATH_CONTROLPATH.md](DATAPATH_CONTROLPATH.md) - DP/CP architecture (kernel driver)
- [QCA_ARISTA_INTEGRATION.md](QCA_ARISTA_INTEGRATION.md) - QCA driver integration
- [ap/src/wlan-drivers/ar/docs/codebase_structure.md](../ap/src/wlan-drivers/ar/docs/codebase_structure.md) - Driver structure

