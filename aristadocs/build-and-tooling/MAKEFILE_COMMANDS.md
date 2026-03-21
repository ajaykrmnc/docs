# Makefile Commands Reference Guide

This document provides comprehensive documentation for all available Make commands in the `scripts/` directory 
and the root Makefile.

---

## Table of Contents

1. [Getting Help](#getting-help)
2. [Server Targets](#server-targets)
3. [AP (Access Point) Targets](#ap-access-point-targets)
4. [API Targets](#api-targets)
5. [Adapter Targets](#adapter-targets)
6. [Vendor Targets](#vendor-targets)
7. [Blob Management](#blob-management)
8. [VM Image Targets](#vm-image-targets)
9. [DI (Device Interaction) Targets](#di-device-interaction-targets)
10. [Go Targets](#go-targets)
11. [Linter Targets](#linter-targets)
12. [Common Command Line Arguments](#common-command-line-arguments)
13. [Build System Files Overview](#build-system-files-overview)

---

## Getting Help

| Command | Description |
|---------|-------------|
| `make help` | Display main help menu with all available help options |
| `make help_adapters` | Show adapter-related targets and options |
| `make help_api` | Show API-related targets and options |
| `make help_server` | Show server-related targets and options |
| `make help_vendors` | Show vendor-related targets and options |
| `make help_ap` | Show AP-related targets and options |
| `make help_blobs` | Show blob management targets and options |
| `make help_vm_image` | Show VM image-related targets and options |
| `make help_di` | Show DI (Device Interaction) targets |
| `make help_all` | Display all help sections at once |

---

## Server Targets

### Build Targets

| Command | Description | Use Case |
|---------|-------------|----------|
| `make server` | Build serverd binaries and install artifacts | Full server build including evtgw and 
tools |
| `make server_bin` | Build serverd binary only | Quick rebuild of server binary |
| `make evtgw` | Build Event Gateway binary | Build the event gateway component |
| `make server_tools` | Build `ext`, `cacheinfo` modules | Build auxiliary server tools |

### Test Targets

| Command | Description | Use Case |
|---------|-------------|----------|
| `make server_ut` | Run serverd unit tests | Verify server functionality |
| `make evtgw_ut` | Run Event Gateway unit tests | Test event gateway component |
| `make check_server` | Build server RPM and run unit tests | CI/CD validation pipeline |

### Clean Targets

| Command | Description | Use Case |
|---------|-------------|----------|
| `make clean_server` | Clean server build artifacts | Reset server build state |
| `make evtgw.clean` | Clean Event Gateway build artifacts | Reset evtgw build (add `UTESTS=TRUE` for UT 
artifacts) |

### Packaging Targets

| Command | Description | Use Case |
|---------|-------------|----------|
| `make rpm_server` | Create server core RPM | Generate RPM package (requires server, api, vendors built) |
| `make pkg_rpm_server` | Package server for Server RPM | Prepare server for RPM packaging |
| `make pkg_server` | Create final server upgrade bundle | Complete server upgrade package |
| `make clean_pkg_server` | Clean server and AP related packaging | Reset packaging artifacts |
| `make oss_wm` | Generate WM OSS Software bundle | Create open-source software bundle |

**Common Arguments:**
```bash
make server MEMCHECK=TRUE           # Run unit tests under valgrind
make server CACHE_TOOL=ccache       # Use ccache for faster builds
make server V=1                     # Verbose build output
make rpm_server VENDOR_LIST="vendor1 vendor2"  # Specify vendors
make rpm_server OS_LIST="os1 os2"   # Specify operating systems
```

---

## AP (Access Point) Targets

### Top-Level Targets

| Command | Description | Use Case |
|---------|-------------|----------|
| `make ap` | Build, install, create dbg symbols for APs | Full AP build pipeline |
| `make pkg_ap` | Package all APs for given vendors | Create AP packages |
| `make oss_ap` | Create OSS SW tar bundle for vendors | Generate open-source bundles |
| `make check_ap` | Build and execute AP unit tests | Validate AP functionality |
| `make clean_ap` | Clean AP build artifacts | Reset AP build state |
| `make clean_workspace` | Comprehensive workspace cleanup | Deep clean including git, blobs, ccache |

**Top-Level Arguments:**
```bash
make ap AP="AP1 AP2 AP3"            # Build specific APs
make ap AP_TYPES="type1 type2"      # Build specific AP types
make ap VENDOR_LIST="vendor1"       # Build for specific vendors
make ap CACHE_TOOL=ccache           # Use ccache
make ap V=1                         # Verbose output
make ap BLD_NATIVE=1                # Native compilation

# Clean workspace example (comprehensive cleanup)
make clean_workspace commondir=/path/to/common blobsdir=/path/to/blobs cachedir=/path/to/cache pull_latest=1
```

### Module-Level Targets

| Command | Description | Use Case |
|---------|-------------|----------|
| `make modhelp` | List supported modules for an AP | Discover available modules |
| `make prep` | Prep module for build (download blob build deps) | Prepare build dependencies |
| `make all` | Build AP image | Compile the AP |
| `make all UT=1` | Build and execute AP Unit Tests | Run module tests |
| `make prep_install` | Prep module for install (download blob install deps) | Prepare install dependencies |
| `make install` | Create AP Upgrade bundle | Package for deployment |
| `make mpimg` | Create AP MP Image(s) after `make install` | Generate manufacturing images |
| `make kmods` | Build AP kernel modules | Compile kernel components |
| `make kmods.install` | Install AP kernel modules | Deploy kernel modules |
| `make umods` | Build AP userspace modules | Compile userspace components |
| `make umods.install` | Install AP userspace modules | Deploy userspace modules |

### Per-Module Targets

For any module `[module]`, the following targets are available:

| Command | Description | Use Case |
|---------|-------------|----------|
| `make [module]` | Build module with dependencies | Compile specific module |
| `make [module] UT=1` | Build module and execute UT | Test specific module |
| `make [module].clean` | Clean module artifacts | Reset module build |
| `make [module].clean UT=1` | Clean module UT artifacts | Reset module test build |
| `make [module].localclean` | Clean only build artifacts | Light cleanup (not all modules) |
| `make [module].cleanstate` | Clean build state to force rebuild | Force next rebuild |
| `make [module].install` | Install module | Deploy module artifacts |
| `make [module].full` | Build and install module | Complete module deployment |
| `make [module].prep` | Prep module | Download dependencies |
| `make [module].dep` | List module dependencies | View dependency graph |

### Debug Targets

| Command | Description | Use Case |
|---------|-------------|----------|
| `make chkbld` | List build status of all AP modules | Debug build progress |
| `make vardump` | List ALL compile and runtime AP vars | Inspect build configuration |
| `make vardump MODVARS=1` | List only Module Variables | Debug module config |
| `make vardump BLDVARS=1` | List only Build Variables | Debug build settings |
| `make vardump PATHVARS=1` | List only Path Variables | Debug path configuration |
| `make env` | Create and display env file for an AP | View environment setup |

---

## API Targets

| Command | Description | Use Case |
|---------|-------------|----------|
| `make common_api` | Build common API components | Build shared API libs |
| `make vendor_api` | Build vendor API components | Build vendor-specific APIs |
| `make check_api` | Build and run API unit tests | Validate API functionality |
| `make clean_api` | Clean API build artifacts | Reset API build |
| `make pkg_rpm_api` | Package API for Server RPM | Prepare for RPM packaging |

**Arguments:**
```bash
make common_api API="api1 api2"      # Build specific APIs
make vendor_api VENDOR_LIST="vendor1"  # Build for specific vendor
```

---

## Adapter Targets

| Command | Description | Use Case |
|---------|-------------|----------|
| `make adapters` | Build adapters | Compile adapter components |
| `make check_adapters` | Build and run adapter unit tests | Validate adapters |
| `make clean_adapters` | Clean adapter build artifacts | Reset adapter build |

**Arguments:**
```bash
make adapters ADAPTERS="adapter1 adapter2"  # Build specific adapters
```

---

## Vendor Targets

| Command | Description | Use Case |
|---------|-------------|----------|
| `make vendors` | Build vendor-specific RPMs | Create vendor packages |
| `make check_vendors` | Build sanity for vendors | Validate vendor builds |
| `make clean_vendors` | Clean vendor artifacts | Reset vendor build |

**Arguments:**
```bash
make vendors VENDOR_LIST="vendor1 vendor2"  # Build specific vendors
```

---

## Blob Management

Blobs are managed through stdin commands. Use `make help_blobs` for full details.

### Usage Patterns

```bash
# Single command
echo "ls ./" | make blobs

# Multiple commands
echo -e "cmd1\ncmd2\ncmd3" | make blobs

# From file
cat cmdFile | make blobs

# Interactive (enter commands, then Ctrl-D)
make blobs
```

### Available Actions

| Action | Syntax | Description |
|--------|--------|-------------|
| `rm` | `rm &lt;src&gt;` | Remove blob entry/entries in YAML file |
| `mv` | `mv &lt;src&gt; &lt;dest&gt;` | Move blob entry/entries in YAML file |
| `cp` | `cp &lt;src&gt; &lt;dest&gt;` | Copy blob entry/entries in YAML file |
| `add` | `add &lt;src&gt;` | Add blob entry/entries in YAML file |
| `up` | `up &lt;src&gt;` | Upload blob(s) |
| `val` | `val &lt;src&gt;` | Validate blob(s) in local cache |
| `cln` | `cln &lt;src&gt;` | Clean blob(s) (rm -f) |
| `hgrm` | `hgrm &lt;src&gt;` | Remove blob(s) (hg remove) |
| `cch` | `cch &lt;src&gt;` | Copy blob(s) from Repo to local cache dir |
| `ls` | `ls &lt;src&gt;` | List blob entry/entries in YAML file |
| `srt` | `srt` | Sort blob YAML file |

**Notes:**
- `src` and `dest` can be exact blob paths or directories ending in `/`
- Repo top dir can be specified as `./`

---

## VM Image Targets

| Command | Description | Use Case |
|---------|-------------|----------|
| `make vm_image` | Build VM image for given configuration | Create virtual machine image |
| `make clean_vm_image` | Clean VM image build artifacts | Reset VM image build |

**Arguments:**
```bash
make vm_image BUILD_NO="<WM build no>"
make vm_image BUILD_URL="<URL of WM build>"
make vm_image VENDOR="airtight"
make vm_image DEPLOYMENT_LIST="gcp vmware kvm dut"
make vm_image IMAGE_TYPE="prod"      # or "inhouse" for test password
```

---

## DI (Device Interaction) Targets

| Command | Description | Use Case |
|---------|-------------|----------|
| `make di` | Build DI libraries | Compile device interaction code |
| `make di_ut` | Build and run DI unit tests | Validate DI functionality |
| `make clean_di` | Clean DI build artifacts | Reset DI build |
| `make clean_di_ut` | Clean DI unit test artifacts | Reset DI test build |

---

## Go Targets

| Command | Description | Use Case |
|---------|-------------|----------|
| `make check_go` | Run Go checks | Validate Go code |
| `make build_cloud_cgo` | Build Cloud CGO components | Compile CGO bindings |
| `make build_cloud_go` | Build Cloud Go components | Compile Go services |
| `make clean_go` | Clean Go build artifacts | Reset Go build |
| `make get_arista_aeris_repo` | Fetch Arista Aeris repository | Download dependencies |
| `make get_arista_apsim_repo` | Fetch Arista APSim repository | Download AP simulator |
| `make cloud_test` | Run cloud tests | Validate cloud components |
| `make gen_wifi_state_data_model` | Generate WiFi state data model | Create data model code |
| `make upgrade_bin` | Build upgrade binary | Create upgrade tool |
| `make apsim` | Build AP Simulator | Create testing simulator |
| `make clean_apsim` | Clean AP Simulator artifacts | Reset APSim build |

---

## Linter Targets

| Command | Description | Use Case |
|---------|-------------|----------|
| `make check_linters COMMIT_FILES_LIST="files"` | Run all linters on specified files | Code review validation 
|

### Supported Linters

The linter system checks the following file types:

| File Type | Linter | Description |
|-----------|--------|-------------|
| `.proto` | `buf format`, `buf lint` | Protocol buffer files |
| `.c`, `.h` | `clang-format` | C/C++ source files |
| Shell scripts | `shfmt`, `shellcheck` | Shell script formatting and checking |
| `.json` | `jsonlint` | JSON validation |
| `.go` | `gofmt` | Go code formatting |
| `.yaml` | `yamale` | YAML validation with schema |
| `.py` | `pylint` | Python code analysis |
| `.tac` | `tacfmt` | TAC file formatting |

### Ignore Files

Linters use ignore files in `scripts/`:
- `.buf-ignore` - Proto files to ignore
- `.WMformat-ignore` - Clang format ignores
- `.shfmt-ignore` - Shell format ignores
- `.shellcheck-ignore` - Shell check ignores
- `.pylint-ignore` - Pylint ignores

---

## Common Command Line Arguments

### Global Arguments

| Argument | Description | Example |
|----------|-------------|---------|
| `V=1` | Verbose output | `make ap V=1` |
| `CACHE_TOOL=ccache` | Use ccache for compilation | `make server CACHE_TOOL=ccache` |
| `DESTDIR=&lt;path&gt;` | Specify build artifacts directory | `make server DESTDIR=/custom/path` |
| `NOLOGFILE=1` | Skip creating log files | `make ap NOLOGFILE=1` |
| `UTESTS=TRUE` | Enable unit testing mode | `make server_ut UTESTS=TRUE` |
| `MEMCHECK=TRUE` | Run tests under valgrind | `make server_ut MEMCHECK=TRUE` |
| `BLD_NATIVE=1` | Use native compilation | `make ap BLD_NATIVE=1` |
| `SYM=1` | Generate debug symbols | `make ap SYM=1` |
| `UT=1` | Unit test mode (AP specific) | `make all UT=1` |

### Filtering Arguments

| Argument | Description | Example |
|----------|-------------|---------|
| `AP="AP1 AP2"` | Specify APs to build | `make ap AP="C_460 C_360"` |
| `VENDOR_LIST="v1 v2"` | Specify vendors | `make vendors VENDOR_LIST="airtight"` |
| `OS_LIST="os1 os2"` | Specify operating systems | `make rpm_server OS_LIST="centos"` |
| `AP_TYPES="t1 t2"` | Specify AP types | `make ap AP_TYPES="indoor outdoor"` |

---

## Build System Files Overview

### Core Makefile Includes

| File | Purpose |
|------|---------|
| `scripts/vars.mk` | Global variable definitions (paths, versions, etc.) |
| `scripts/common.mk` | Common utility rules (profiling, variable dumping) |
| `scripts/help.mk` | Help target definitions |
| `scripts/linter.mk` | Linter rules and configurations |

### Build Rules

| File | Purpose |
|------|---------|
| `scripts/rules_common.mk` | Shared build rules (make_rule, clean_rule, driver_build) |
| `scripts/rules_ext.mk` | External module build rules (blob handling, patching) |
| `scripts/rules_int.mk` | Internal module build rules (compilation, linking) |
| `scripts/mod_common.mk` | Module common variables and UT support |
| `scripts/s4_common.mk` | S4 model compilation rules (TAC files, ARDS models) |

### Security Tools

| File | Purpose |
|------|---------|
| `scripts/run_sectools.mk` | Secure boot image signing and verification |

---

## Build Flow Overview

### Standard Build Dependency Graph

```
[all] → post_build → build_module → pre_build → [prep] → custom_prep → common_prep
↓
(blob download)
```

### AP Build Flow

```
make ap → prep → all → chkbld → install → symtab
↓
kmods + umods
↓
[module].install
```

### Server Build Flow

```
make check_server → server_ut → cloud_test → server → mock_api → mock_vendors
↓              ↓
rpm_server → adapters → pkg_server
```

---

## Examples

### Building a Single AP
```bash
make ap AP="C_460"
```

### Building with Verbose Output and ccache
```bash
make server V=1 CACHE_TOOL=ccache
```

### Running Unit Tests with Memory Checking
```bash
make server_ut MEMCHECK=TRUE
```

### Comprehensive Workspace Cleanup
```bash
make clean_workspace commondir=/path/to/common blobsdir=/path/to/blobs cachedir=/path/to/ccache pull_latest=1
```

### Checking Code Before Commit
```bash
make check_linters COMMIT_FILES_LIST="path/to/file1.c path/to/file2.py"
```

### Building Vendor-Specific Components
```bash
make vendors VENDOR_LIST="airtight"
make pkg_server VENDOR_LIST="airtight" OS_LIST="centos"
```

### Creating OSS Bundles
```bash
make oss_ap VENDOR_LIST="airtight"
make oss_wm VENDOR_LIST="airtight" OS_LIST="centos"
```

---

## Troubleshooting

### Common Issues

1. **Make version error**: Ensure you have Make 4.2.1 or 4.3
   ```bash
   make --version
   ```

2. **Build logs**: Check `build/&lt;component&gt;/log/` for detailed logs

3. **Profile timing**: Check `build/profile/` for build timing information

4. **Verbose debugging**: Use `V=1` for detailed build output

5. **Module status**: Use `make chkbld AP="&lt;AP&gt;"` to check build status

---

*Generated for the WiFi AP build system. For additional help, run `make help` or `make help_all`.*

