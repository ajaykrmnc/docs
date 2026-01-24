# Cross-Compilation Guide for WiFi AP Repository

This document provides a comprehensive explanation of how cross-compilation works in the wifi-ap repository,
covering how x86_64 build hosts produce aarch64 (ARM64) binaries for Access Points.

---

## Table of Contents

1. [Overview](#overview)
2. [Key Concepts](#key-concepts)
3. [Build Environment Architecture](#build-environment-architecture)
4. [Toolchain Installation and Configuration](#toolchain-installation-and-configuration)
5. [Cross-Compilation Variables](#cross-compilation-variables)
6. [Platform-Specific Configuration](#platform-specific-configuration)
7. [Kernel Cross-Compilation](#kernel-cross-compilation)
8. [Driver and Module Building](#driver-and-module-building)
9. [Userspace Component Cross-Compilation](#userspace-component-cross-compilation)
10. [Go Cross-Compilation](#go-cross-compilation)
11. [Build Caching with ccache](#build-caching-with-ccache)
12. [Image Generation](#image-generation)
13. [Build Directory Structure](#build-directory-structure)
14. [Complete Build Flow](#complete-build-flow)
15. [Native Builds for Unit Testing](#native-builds-for-unit-testing)
16. [Debugging and Troubleshooting](#debugging-and-troubleshooting)
17. [Quick Reference](#quick-reference)
18. [Manual Toolchain Installation and Troubleshooting](#manual-toolchain-installation-and-troubleshooting)
    - [Understanding MUSL vs glibc Toolchains](#understanding-musl-vs-glibc-toolchains)
    - [Verifying Access to Distribution Servers](#verifying-access-to-distribution-servers)
    - [Manual Toolchain Installation](#manual-toolchain-installation)
    - [Complete Installation Script](#complete-installation-script)
    - [Secrets and Permissions Required](#secrets-and-permissions-required)
    - [Verifying Toolchain Installation](#verifying-toolchain-installation)
    - [Troubleshooting Missing /export Content](#troubleshooting-missing-export-content)

---

## Overview

Cross-compilation is the process of building executable code for a platform different from the one on which
the compiler is running. In this repository:

| Aspect | Value |
|--------|-------|
| **Host Architecture** | x86_64 (Intel/AMD 64-bit) |
| **Target Architecture** | aarch64 (ARM 64-bit) |
| **Host OS** | AlmaLinux 9 (in container) |
| **Target OS** | Embedded Linux (musl or glibc) |
| **Build System** | GNU Make with Barney containers |

The Docker/Barney container doesn't inherently "know" it needs to build for ARM - this is configured through
Makefiles and toolchain selection.

### Why Cross-Compilation?

1. **Performance**: Building on x86_64 servers is significantly faster than on ARM devices
2. **Resources**: Build servers have more RAM, CPU, and storage than embedded devices
3. **Consistency**: Same build environment for all developers and CI
4. **Parallelization**: Can run many parallel builds on powerful CI infrastructure

---

## Key Concepts

### Terminology

| Term | Definition |
|------|------------|
| **Host** | The machine where compilation runs (x86_64 build server) |
| **Target** | The machine where compiled code will execute (ARM64 AP) |
| **Cross-Compiler** | A compiler that runs on host but produces target binaries |
| **Toolchain** | Complete set of tools: compiler, linker, assembler, libraries |
| **Sysroot** | Target system's root filesystem used during compilation |
| **CROSS_COMPILE** | Prefix added to all tool invocations (e.g., `aarch64-linux-gnu-`) |

### C Library Variants

The repository uses two C library implementations:

| Library | Description | Use Case |
|---------|-------------|----------|
| **glibc** | GNU C Library, full-featured | General userspace applications |
| **musl** | Lightweight, static-friendly | Kernel/driver builds, embedded components |

---

## Build Environment Architecture

### Container Hierarchy

The build environment is defined in `barney.yaml` using a layered image approach:

```
┌─────────────────────────────────────────────────────────────────────────┐
│  internal/almalinux-bootstrap                                           │
│  └── Base AlmaLinux 9.6 minimal image                                   │
└─────────────────────────────────────────────────────────────────────────┘
│
▼
┌─────────────────────────────────────────────────────────────────────────┐
│  wifi-almalinux                                                          │
│  └── Build tools: gcc, make, cmake, meson, git, flex, bison, dtc, etc.  │
└─────────────────────────────────────────────────────────────────────────┘
│
▼
┌─────────────────────────────────────────────────────────────────────────┐
│  wifi-ap-build-floor                                                     │
│  ├── wifi-almalinux (base OS)                                           │
│  ├── wifi-blob-build-rpms (blob utilities)                              │
│  ├── internal/keys (signing keys)                                        │
│  ├── toolchains (ALL cross-compilation toolchains)                       │
│  │   ├── toolchains/gnu-11-3 (glibc-based ARM64)                        │
│  │   ├── toolchains/musl (musl-based for various SPF versions)          │
│  │   ├── toolchains/ap-build-tools (QCA SDK tools)                      │
│  │   ├── toolchains/microsoft-fips-go (FIPS-compliant Go)               │
│  │   ├── toolchains/buf (Protocol buffers)                              │
│  │   └── toolchains/shellcheck (Shell linting)                          │
│  ├── internal/protobuf (protobuf-c compiler)                            │
│  └── wifi-pip-deps (Python packages: jinja2, pylint, etc.)              │
└─────────────────────────────────────────────────────────────────────────┘
│
▼
┌─────────────────────────────────────────────────────────────────────────┐
│  wifi-ap-build-env                                                       │
│  └── Environment variables:                                              │
│      ├── DIST_CACHE_DIR=/tmp/.wifi_build/blobs                          │
│      ├── DIST_WIFI_BASE=http://wifi-build.sjc.aristanetworks.com/...    │
│      ├── DIST_BASE=http://dist.aristanetworks.com/storage/wifi          │
│      ├── CCACHE_REMOTE_STORAGE=redis://wifi-ccache-redis...             │
│      └── HOME=/home                                                      │
└─────────────────────────────────────────────────────────────────────────┘
│
▼
┌─────────────────────────────────────────────────────────────────────────┐
│  build-ap/<model>  (e.g., build-ap/c460, build-ap/o435)                 │
│  └── Specific AP build with: make ap AP=<MODEL> -j8 NOLOGFILE=1         │
└─────────────────────────────────────────────────────────────────────────┘
```

### Key Container Configuration (barney.yaml)

```yaml
wifi-ap-build-floor:
  units:
    - image: .%wifi-almalinux           # Base OS with native build tools
    - image: .%wifi-blob-build-rpms     # Blob download/extraction utilities
    - image: .%internal/keys            # Code signing keys
    - image: .%toolchains               # ALL cross-compilation toolchains
    - image: .%internal/protobuf        # Protocol buffers compiler
    - image: .%wifi-pip-deps            # Python dependencies

wifi-ap-build-env:
  entry:
    env:
      DIST_CACHE_DIR: /tmp/.wifi_build/blobs
      DIST_WIFI_BASE: http://wifi-build.sjc.aristanetworks.com/storage/bin
      DIST_BASE: http://dist.aristanetworks.com/storage/wifi
      CCACHE_REMOTE_STORAGE: redis://wifi-ccache-redis.infra.corp.arista.io:65531
      CCACHE_REMOTE_ONLY: "true"
  units:
    - image: .%wifi-ap-build-floor
```

---

## Toolchain Installation and Configuration

### Where Toolchains Are Installed

All toolchains are installed to the `/export` directory inside the container:

```
/export/
├── arm-gnu-toolchain-11.3.rel1-x86_64-aarch64-none-linux-gnu/   # glibc toolchain
│   ├── bin/
│   │   ├── aarch64-none-linux-gnu-gcc
│   │   ├── aarch64-none-linux-gnu-g++
│   │   ├── aarch64-none-linux-gnu-ld
│   │   ├── aarch64-none-linux-gnu-ar
│   │   ├── aarch64-none-linux-gnu-strip
│   │   ├── aarch64-none-linux-gnu-objcopy
│   │   └── ...
│   ├── lib/
│   ├── include/
│   └── aarch64-none-linux-gnu/
│       └── libc/          # Target sysroot
│
├── toolchain-aarch64_cortex-a73_gcc-7.5.0_musl-1.1.24-spf12.2/  # SPF 12.2 musl
│   └── bin/
│       ├── aarch64-openwrt-linux-musl-gcc
│       └── ...
│
├── toolchain-aarch64_cortex-a53_gcc-12.3.0_musl-1.2.4-spf12.5/  # SPF 12.5 musl
│   └── bin/
│       ├── aarch64-openwrt-linux-musl-gcc
│       └── ...
│
└── ap-build-tools/        # QCA SDK tools (mkits.sh, pack.py, etc.)
```

### How Toolchains Are Downloaded

Toolchains are downloaded during container image build from dist servers:

**GNU Toolchain (glibc-based)** - `toolchains/gnu-11-3`:
```yaml
toolchains/gnu-11-3:
  units:
    - floor: .%internal/toolchain-floor
  build: |
    export DIST_BASE=http://dist.aristanetworks.com/storage/wifi
    mkdir -p /dest/export
    wget -nv $DIST_BASE/toolchains/arm-gnu-toolchain-11.3.alma_rel1-x86_64-aarch64-none-linux-gnu.tar.xz \
    -O /tmp/toolchain-11.3.rel1-x86_64-aarch64-gnu.tar.xz
    echo "5c281156f064abec19be13183c675010e0906031cf31d6e019e08b138e7c639e /tmp/..." | sha256sum --check -
    tar -Jxf /tmp/toolchain-11.3.rel1-x86_64-aarch64-gnu.tar.xz -C /dest/export
```

**MUSL Toolchains** - `toolchains/musl`:
```yaml
toolchains/musl:
  units:
    - floor: .%internal/toolchain-floor
  build: |
    export DIST_BASE=http://dist.aristanetworks.com/storage/wifi
    mkdir -p /dest/export

    # SPF 10 toolchain
    wget -nv $DIST_BASE/toolchains/toolchain-aarch64_cortex-a53_gcc-5.2.0_musl-1.1.16-spf10cs.tar.xz
    tar -Jxf /tmp/toolchain-5.2.0-musl.tar.xz -C /dest/export

    # SPF 12.2 toolchain (BELLS - C-460, O-435)
    wget -nv $DIST_BASE/toolchains/toolchain-aarch64_cortex-a73_gcc-7.5.0_musl-1.1.24-spf12.2_cs.tar.xz
    tar -Jxf ... -C /dest/export

    # SPF 12.5 toolchain (MIAMI - C-400, O-405)
    wget -nv $DIST_BASE/toolchains/toolchain-aarch64_cortex-a53_gcc-12.3.0_musl-1.2.4-spf12.5ed.tar.xz
    tar -Jxf ... -C /dest/export
```

### Toolchain Naming Convention

#### GNU Toolchain Format
```
arm-gnu-toolchain-11.3.rel1-x86_64-aarch64-none-linux-gnu
│                  │         │      │      │     │
│                  │         │      │      │     └── Target OS (GNU libc)
│                  │         │      │      └── Target vendor (none = bare-metal style)
│                  │         │      └── Target architecture (ARM 64-bit)
│                  │         └── Host architecture (Intel 64-bit)
│                  └── GCC version (11.3 release 1)
└── Toolchain provider (ARM)
```

#### MUSL Toolchain Format
```
toolchain-aarch64_cortex-a73_gcc-7.5.0_musl-1.1.24-spf12.2
│         │          │         │          │
│         │          │         │          └── SPF (Software Platform Framework) version
│         │          │         └── C library and version (musl 1.1.24)
│         │          └── GCC version (7.5.0)
│         └── Target CPU core (Cortex-A73)
└── Target architecture (aarch64)
```

---

## Cross-Compilation Variables

### Core Variables in tools_vars.mk

The file `ap/scripts/tools_vars.mk` defines all cross-compilation variables:

```makefile
# Default toolchain (glibc-based)
TOOLS_NAME := arm-gnu-toolchain-11.3.rel1-x86_64-aarch64-none-linux-gnu
TOOLS_ABBR_NAME := arm64_gcc-11.3-gnu

# Architecture settings
ARCH := aarch64
HOST := $(ARCH)-none-linux-gnu           # aarch64-none-linux-gnu
CROSS_TOOL := $(HOST)

# Toolchain paths
TOOLS_DIR := /export
TOOLS_BASE_DIR := $(TOOLS_DIR)/$(TOOLS_NAME)
TOOLS_BIN_DIR := $(TOOLS_BASE_DIR)/bin
TOOLS_INC_DIR := $(TOOLS_BASE_DIR)/include

# Kernel toolchain (may differ from userspace)
K_TOOLS_NAME := toolchain-aarch64_cortex-a73_gcc-7.5.0_musl-1.1.24-spf12.2
K_TOOLS_BASE_DIR := $(TOOLS_DIR)/$(K_TOOLS_NAME)
K_TOOLS_BIN_DIR := $(K_TOOLS_BASE_DIR)/bin

# CROSS_COMPILE prefix (with optional ccache)
CACHE_TOOL ?= ccache
CROSS := $(strip $(CACHE_TOOL) $(HOST)-)        # "ccache aarch64-none-linux-gnu-"
K_CROSS := $(strip $(CACHE_TOOL) $(K_HOST)-)    # Kernel cross-compile prefix

# Tool definitions
TOOLPREFIX_NO_CCH := $(strip $(filter-out $(CACHE_TOOL),$(CROSS)))
CC := $(strip $(CACHE_TOOL) $(TOOLPREFIX_NO_CCH)gcc)      # ccache aarch64-none-linux-gnu-gcc
CXX := $(strip $(CACHE_TOOL) $(TOOLPREFIX_NO_CCH)g++)     # ccache aarch64-none-linux-gnu-g++
AR := $(TOOLPREFIX_NO_CCH)ar                               # aarch64-none-linux-gnu-ar
LD := $(TOOLPREFIX_NO_CCH)ld                               # aarch64-none-linux-gnu-ld
NM := $(TOOLPREFIX_NO_CCH)nm
STRIP := $(TOOLPREFIX_NO_CCH)strip
OBJCOPY := $(TOOLPREFIX_NO_CCH)objcopy
```

### Compiler Tools Mapping

| Variable | Resolves To | Purpose |
|----------|-------------|---------|
| `$(CC)` | `ccache aarch64-none-linux-gnu-gcc` | C compiler |
| `$(CXX)` | `ccache aarch64-none-linux-gnu-g++` | C++ compiler |
| `$(AR)` | `aarch64-none-linux-gnu-ar` | Static library archiver |
| `$(LD)` | `aarch64-none-linux-gnu-ld` | Linker |
| `$(STRIP)` | `aarch64-none-linux-gnu-strip` | Strip debug symbols |
| `$(OBJCOPY)` | `aarch64-none-linux-gnu-objcopy` | Binary manipulation |
| `$(NM)` | `aarch64-none-linux-gnu-nm` | Symbol listing |

### PATH Configuration

The build system prepends toolchain directories to PATH:

```makefile
PLAT_PATH := $(TOOLS_BIN_DIR):$(SDK_TOOLS):$(GEN_TOOLS):$(K_TOOLS_BIN_DIR)
PATH := $(PLAT_PATH):$(PATH)
```

This ensures cross-compilation tools are found before native tools.

---

## Platform-Specific Configuration

### Configuration File Hierarchy

Each AP model has configuration at multiple levels:

```
ap/platform/cvendors/QCA/
├── SOC/
│   ├── BELLS/common/config/
│   │   └── config.platform         # BELLS chipset configuration
│   ├── MIAMI/common/config/
│   │   └── config.platform         # MIAMI chipset configuration
│   └── HAWKEYE/common/config/
│       └── config.platform         # HAWKEYE chipset configuration
│
└── boards/
├── C_460/
│   └── common/config/
│       └── config.ap           # C-460 specific settings
├── O_435/
│   └── common/config/
│       └── config.ap           # O-435 specific settings
└── C_400/
└── common/config/
└── config.ap           # C-400 specific settings
```

### BELLS Platform (C-460, O-435, C-430)

`ap/platform/cvendors/QCA/SOC/BELLS/common/config/config.platform`:

```makefile
##########  ARCH, TOOLCHAIN ######################
TOOLS_NAME := toolchain-aarch64_cortex-a73_gcc-7.5.0_musl-1.1.24-spf12.2
K_TOOLS_NAME := toolchain-aarch64_cortex-a73_gcc-7.5.0_musl-1.1.24-spf12.2
TOOLS_ABBR_NAME := arm64_gcc-7.5.0-musl-1.1.24
GCC_VER := 7.5.0

ARCH := aarch64
HOST := $(ARCH)-openwrt-linux
K_HOST := $(ARCH)-openwrt-linux
CROSS_TOOL := $(HOST)-musl
K_CROSS_TOOL := $(K_HOST)-musl

CHIPSET := BELLS
TARGET := arm64-elf
KERNELARCH := arm64

############ KERNEL ###############################
KERNEL_VERSION := 5.4
KERNEL_MINOR_VERSION := 213

############ ARCHITECTURE #########################
ARCH_LITTLE_ENDIAN := TRUE
ARCH_ARGS := -march=armv8-a -mtune=cortex-a73

############ IMAGE ################################
IMG_PREFIX := ipq9574
fstype := squashfs
KERNEL_IMAGE := $(IMG_PREFIX)-$(IMG_SUB_PLATFORM_PREFIX)-fit-uImage.itb
```

### MIAMI Platform (C-400, O-405)

`ap/platform/cvendors/QCA/SOC/MIAMI/common/config/config.platform`:

```makefile
############ KERNEL ###############################
KERNEL_VERSION := 5.4
KERNEL_MINOR_VERSION := 213

fstype := squashfs

IMG_PREFIX := ipq5332
KERNEL_IMAGE := $(IMG_PREFIX)-$(IMG_SUB_PLATFORM_PREFIX)-fit-uImage.itb

############ PLATFORM FOR SDK ##############################
PLATFORM_11BE := TRUE
ARCH_LITTLE_ENDIAN := TRUE

IPROUTE2_VER := iproute2-4.0.0

# Toolchain defined in board-specific config.ap
# Uses: toolchain-aarch64_cortex-a53_gcc-12.3.0_musl-1.2.4-spf12.5
```

### Platform-Toolchain Mapping

| Platform | SPF Version | Kernel | Toolchain | Target CPU |
|----------|-------------|--------|-----------|------------|
| HAWKEYE | 11.1/11.4 | 4.4 | gcc-5.2.0-musl-spf11.x | Cortex-A53 |
| BELLS | 12.2 | 5.4 | gcc-7.5.0-musl-spf12.2 | Cortex-A73 |
| MIAMI | 12.5 | 5.4 | gcc-12.3.0-musl-spf12.5 | Cortex-A53 |

---

## Kernel Cross-Compilation

### Kernel Source Acquisition

The Linux kernel source is downloaded as a "blob" managed by `blobs.yaml`:

```yaml
# blobs.yaml entries for kernel sources
- dest: ap/platform/cvendors/QCA/SPF/12.2/src_blobs/linux-5.4.tar.gz
  shasum: <sha256-hash>
  source: linux-5.4.tar.gz.<sha256-hash>

- dest: ap/platform/cvendors/QCA/SPF/12.5/src_blobs/linux-5.4.tar.gz
  shasum: <sha256-hash>
  source: linux-5.4.tar.gz.<sha256-hash>
```

### Kernel Build Process

The kernel build is orchestrated by `ap/platform/cvendors/QCA/SPF/<version>/src/kernel/Makefile.sdk`:

#### Step 1: Source Extraction
```makefile
KERNEL_SRC_DIR := $(NEW_QCA_SPF_PATH)/$(SPF)/src_blobs
KERNEL_SRC_FILE := $(KERNEL_SRC_DIR)/linux-$(KERNEL_VERSION).tar.gz

$(BLD_DIR)/.common_prep: $(blob_bld_deps)
tar -xf $(KERNEL_SRC_FILE) --strip-components 1 -C $(BLD_DIR)
git init
git add -A
git commit -m "Initial kernel source"
```

#### Step 2: Patch Application
```makefile
# Patches are organized by platform and SPF version
KERNEL_PATCHLIST := patchlists/kernel_patchlist
PLATFORM_PATCH_FILE := $(NEW_PLATFORM_AP_PATH)/SPF/$(SPF)/$(KERNEL_PATCHLIST)
COMMON_PATCH_FILE := $(NEW_QCA_PATH)/kernel/$(KERNEL_VERSION)/$(KERNEL_PATCHLIST)
SPF_PATCH_FILE := $(NEW_QCA_SPF_PATH)/$(SPF)/$(KERNEL_PATCHLIST)

# Apply patches using git am
PATCHES_GIT_AM := 1
$(foreach patch,$(PATCHES_LIST),git am $(patch);)
```

#### Step 3: Configuration
```makefile
# Kernel defconfig location
KERNEL_DEF_CFG_FILE := $(K_CONFIG_DIR)/$(SPF)/$(PLATFORM_AP_MODEL)/kernel_defconfig

# Configure kernel with cross-compiler
$(MAKE) ARCH=$(ARCH) CROSS_COMPILE="$(K_CROSS)" -C $(kernel_path) $(KERNEL_CONFIG)_defconfig
$(MAKE) ARCH=$(ARCH) CROSS_COMPILE="$(K_CROSS)" -C $(kernel_path) olddefconfig
$(MAKE) ARCH=$(ARCH) CROSS_COMPILE="$(K_CROSS)" -C $(kernel_path) prepare
$(MAKE) ARCH=$(ARCH) CROSS_COMPILE="$(K_CROSS)" -C $(kernel_path) modules_prepare
```

#### Step 4: Build
```makefile
MAKE_ARGS := CROSS_COMPILE="$(K_CROSS)" ARCH=$(KERNELARCH)

# Build kernel image, modules, and device trees
$(MAKE) $(MAKE_ARGS) -C $(kernel_path) Image
$(MAKE) $(MAKE_ARGS) -C $(kernel_path) modules
$(MAKE) $(MAKE_ARGS) -C $(kernel_path) dtbs
```

#### Step 5: FIT Image Generation
```makefile
$(KERNEL_IMAGE): | $(KERNEL_IMG_DIR)
@gzip -9 -c $(KERNEL_BOOT_DIR)/Image > $(KERNEL_IMG_DIR)/Image.gz
@mkits.sh \
-D $(IMG_PREFIX)-$(IMG_SUB_PLATFORM_PREFIX) \
-o $(KERNEL_IMG_DIR)/$(KERNEL_ITS_FILE) \
-k $(KERNEL_IMG_DIR)/Image.gz \
$(if $(KERNEL_DTB),-d $(KERNEL_DTB)) \
-C gzip \
-a $(KERNEL_LOAD_ADDR) \
-e $(KERNEL_ENTRY_ADDR) \
-A $(ARCH) \
-v $(KERNEL_VERSION).$(KERNEL_MINOR_VERSION)
@mkimage -f $(KERNEL_IMG_DIR)/$(KERNEL_ITS_FILE) $(KERNEL_IMG_DIR)/$(KERNEL_IMAGE)
```

### Kernel defconfig Files

Platform-specific kernel configurations:

```
ap/platform/patches/kernel/5.4/
├── 12.2/
│   ├── C_460/kernel_defconfig
│   ├── O_435/kernel_defconfig
│   └── C_430/kernel_defconfig
└── 12.5/
├── C_400/kernel_defconfig
└── O_405/kernel_defconfig
```

Example defconfig header:
```
# Automatically generated file; DO NOT EDIT.
# Linux/arm64 5.4.213 Kernel Configuration
#
# Compiler: aarch64-openwrt-linux-musl-gcc (OpenWrt GCC 7.5.0) 7.5.0
#
CONFIG_CC_IS_GCC=y
CONFIG_GCC_VERSION=70500
```

---

## Driver and Module Building

### Out-of-Tree Kernel Module Pattern

External drivers are built against the kernel using `scripts/rules_common.mk`:

```makefile
# Driver build rule
define driver_build =
@echo "===================================================================="
@$(MAKE) -C $(kernel_path) M=$(BLD_DIR) modules \
$1 CROSS_COMPILE="$(K_CROSS)"
endef

# Driver preparation (symlinks)
define driver_prep =
@for d in $1; do \
mkdir -p $3/$$d; \
for i in $2/$$d/{*.c,Kbuild}; do \
if test -f $$i; then \
ln -sf $$i $3/$$d/`basename $$i`; \
fi; \
done; \
done;
endef
```

### Example Driver Makefile (Makefile.sdk)

```makefile
# ap/src/bpipe/Makefile.sdk
include $(MOD_COMMON_MK)

TGT := $(BLD_DIR)/$(MODULE).ko
SRCDIR := $(shell pwd)
SUBDIRS := .

# IMPORTANT: Use KERNELARCH not ARCH for kernel module builds
ARCH := $(KERNELARCH)

include $(RULES_INT_MK)

MAKE_ARGS = EXTRA_CFLAGS="$(CFLAGS)"

custom_prep:
+$(call driver_prep,$(SUBDIRS),$(SRCDIR),$(BLD_DIR))

build_module:
+$(call driver_build,$(MAKE_ARGS))

install: install_lib_bin

install_lib_bin:
$(call install_stripped,$(TGT),$(KMOD_INSTALL_PATH))
```

### WLAN Driver Cross-Compilation

WLAN drivers have extensive cross-compilation configuration:

```makefile
# ap/src/wlan-drivers/QCA/licensed/spf12_2_csu2/Makefile.sdk

# Set TOOLPREFIX for vendor SDK
ifeq ($(MOD), wlantools)
WLAN_MAKEOPTS+= TOOLPREFIX="$(CROSS_TOOL)-"
else
WLAN_MAKEOPTS+= TOOLPREFIX="$(K_CROSS_TOOL)-"
endif

WLAN_MAKEOPTS+= \
NO_SIMPLE_CONFIG=1 \
USE_PLATFORM_FRAMEWORK=1 \
TARGET=$(TARGET) \
BIG_ENDIAN_HOST=$(BIG_ENDIAN_HOST) \
ARCH=$(KERNELARCH) \
KERNELARCH=$(KERNELARCH) \
KERNELVER=$(KERNEL_VERSION) \
KBUILDPATH=$(kernel_path) \
KERNELPATH=$(kernel_path)
```

---

## Userspace Component Cross-Compilation

### Standard Makefile Pattern

Most userspace components follow this pattern in their `Makefile.sdk`:

```makefile
include $(MOD_COMMON_MK)

TGT := $(BLD_DIR)/$(MODULE)
SRCS := main.c utils.c

include $(RULES_INT_MK)

# Include paths
INC += -I$(TOOLS_INC_DIR) -I$(apcomm_inc)

# Library paths
LIBS += -L$(s4_bins)/usr/lib -lssl -lcrypto
LIBS += -Wl,-rpath-link,$(s4_lib)

# Compiler flags
CFLAGS += -Wall -Werror

build_module: $(TGT)

install: install_lib_bin

install_lib_bin:
$(call install_stripped,$(TGT),$(INSTALL_ROOT_DIR)/bin)
```

### Meson Cross-Compilation

For Meson-based builds (e.g., libpam), a cross-compilation file is used:

`ap/scripts/meson-aarch64-cross-compilation.txt`:
```ini
# Cross compilation file required for meson

[host_machine]
system = 'linux'
cpu_family = 'aarch64'
cpu = 'aarch64'
endian = 'little'
```

Usage in Makefile:
```makefile
# ap/lib/libpam/Makefile.sdk
CFG_CMD := meson setup $(BUILD_DIR) $(BLD_DIR) \
--cross-file $(AP_SCRIPTS_DIR)/meson-aarch64-cross-compilation.txt \
-Dpamlocking=true \
-Dselinux=disabled \
-Ddocs=disabled
```

### CMake Cross-Compilation

For CMake-based builds:

```makefile
# ap/lib/esl_scd/Makefile.sdk
CFG_CMD = cmake \
-DCMAKE_CXX_FLAGS="-I $(s4_inc) -DARISTA_EXTN" \
-DCMAKE_LIBRARY_PATH="$(s4_bins)/usr/lib" \
-DCMAKE_BUILD_TYPE="RelWithDebInfo" \
-DCMAKE_SYSTEM_PROCESSOR=$(ARCH) \
-DCMAKE_EXE_LINKER_FLAGS="-L$(s4_bins)/usr/lib -Wl,-rpath-link,$(s4_lib)" \
. && cmake --build .
```

---

## Go Cross-Compilation

### Go Environment Setup

Go binaries are cross-compiled for ARM64 in `ap/src/go/arista-ap/Makefile.sdk`:

```makefile
# Go cross-compilation environment
GOFLAGS := -ldflags="-s -w"

# For pure Go (no CGO)
export GOOS=linux
export GOARCH=arm64

# For CGO-enabled builds
export CGO_ENABLED=1
export CGO_CFLAGS="$(CFLAGS)"
export CGO_LDFLAGS="-L$(pmac_lib) -lpmac"
export CC=$(CC)

# Build targets
$(GO) build $(GOFLAGS) -o $(TGTGOBIN) ./cmd/gobin
$(GO) build $(GOFLAGS) -o $(TGTOCAGENT) ./cmd/ocagent
```

### FIPS-Compliant Go

For FIPS 140-2/140-3 compliance, a Microsoft FIPS Go toolchain is used:

```yaml
# barney.yaml
toolchains/microsoft-fips-go:
  units:
    - floor: .%internal/toolchain-floor
  build: |
    mkdir -p /dest/opt
    wget -nv "https://artifactory.../golang-fips/go1.25.3/go1.25.3-1.linux-amd64.tar.gz"
    tar -zxf /tmp/golang.tar.gz -C /dest/opt
    ln -sf /opt/go/bin/go /dest/usr/bin/go
```

---

## Build Caching with ccache

### ccache Integration

The build system uses ccache for compilation caching:

```makefile
# scripts/vars.mk
CACHE_TOOL ?= ccache

# ap/scripts/tools_vars.mk
CROSS := $(strip $(CACHE_TOOL) $(HOST)-)
CC := $(strip $(CACHE_TOOL) $(TOOLPREFIX_NO_CCH)gcc)
```

### Remote ccache Configuration

CI builds use remote ccache storage:

```yaml
# barney.yaml - wifi-ap-build-env
entry:
  env:
    # Ccache version 4.7+
    CCACHE_REMOTE_STORAGE: redis://wifi-ccache-redis.infra.corp.arista.io:65531
    # Ccache version 4.5-4.6
    CCACHE_SECONDARY_STORAGE: redis://wifi-ccache-redis.infra.corp.arista.io:65531
    CCACHE_REMOTE_ONLY: "true"
```

### Disabling ccache

To disable ccache for debugging:
```bash
make ap AP=C_460 CACHE_TOOL=
```

---

## Image Generation

### Rootfs Creation (SquashFS)

Platform-specific image generation in `src/image/Makefile.sdk`:

```makefile
# Compression settings
SQUASHFS_BLOCKSIZE := 256k
SQUASHFSOPT := -b $(SQUASHFS_BLOCKSIZE)
SQUASHFSOPT += -p '/dev d 755 0 0' -p '/dev/console c 600 0 0 5 1'
LZMA_XZ_OPTIONS := -Xpreset 9 -Xe -Xlc 0 -Xlp 2 -Xpb 2 -Xbcj arm -b 256k
SQUASHFSCOMP := -comp xz $(LZMA_XZ_OPTIONS)

rootfs_image:
@mksquashfs4 \
$(INSTALL_ROOT_DIR) \
$(INSTALL_DIR)/root.squashfs \
$(SQUASHFS_COMMON_OPT) \
$(SQUASHFSCOMP) \
$(SQUASHFSOPT)
```

### FIT Image Structure

Kernel FIT (Flattened Image Tree) format:
```
kernel.itb
├── Image (compressed kernel)
├── Device Tree Blob(s)
└── Configuration
```

### Manufacturing Image Generation

`ap/platform/mp_image/mp_image_gen.sh` creates final images:

```bash
# Image naming format
MP_IMG="MP_IMG_${MWM_VER}_${SDK_VER}_${VENDOR_BLD_VER}_${VENDOR_ID}_${PLATFORM_ID}_${VARIANT}_${FLASH_TYPE}.bin"

# NOR flash image (for newer platforms)
gen_nor_img() {
  # Align and pack partitions
  for file in ubootenv kernel rootfs; do
    ${PACK_FILE} "${file}" "${file}.align" "${size}"
    cat "${file}.align" >> "${MP_IMG_FILE}"
  done
}
```

---

## Build Directory Structure

### Directory Layout

```
build/
└── ap/
├── arm64_gcc-7.5.0-musl-1.1.24_BELLS_C_460/   # Toolchain_Chipset_Model
│   ├── linux-5.4/                              # Kernel build directory
│   │   ├── arch/arm64/
│   │   ├── drivers/
│   │   ├── .config
│   │   └── vmlinux
│   ├── bpipe/                                  # Module build dirs
│   ├── sensord/
│   ├── apcomm/
│   └── install/
│       ├── rootfs/                             # Staged root filesystem
│       │   ├── bin/
│       │   ├── lib/
│       │   ├── opt/
│       │   └── ...
│       └── images/
│           ├── kernel.itb
│           └── root.squashfs
│
├── pkg/
│   └── C_460/                                  # Final packages
│       ├── AP_Upgrade/
│       └── MP_IMG/
│
└── symtab/                                     # Debug symbols
└── C_460/
```

### Key Path Variables

Defined in `scripts/vars.mk`:

```makefile
BUILD_BASE := $(if $(DESTDIR),$(DESTDIR),$(TOPDIR)/build)
BUILD_BASE_AP := $(TOPDIR)/build/ap
PKG_BASE_AP := $(BUILD_BASE)/ap

# Per-module build directory
BLD_DIR = $(BLD)/$(MODULE)
BLD_DIR_TC = $(BUILD_BASE_AP)/$(TOOLS_ABBR_NAME)_$(CHIPSET)_$(AP)
```

---

## Complete Build Flow

### Makefile Include Chain

```
make ap AP=C_460
│
▼
ap/scripts/Makefile
│
├──► ap/scripts/vendors.mk (selects vendor: QCA)
│
├──► scripts/vars.mk (paths, directories, version)
│
├──► config.ap (AP-specific: PLATFORM_ID, VENDOR_ID)
│        Located: ap/platform/cvendors/QCA/boards/C_460/common/config/
│
├──► config.platform (chipset: TOOLS_NAME, KERNEL_VERSION)
│        Located: ap/platform/cvendors/QCA/SOC/BELLS/common/config/
│
└──► ap/scripts/tools_vars.mk (CROSS, CC, toolchain paths)
```

### Build Execution Steps

```bash
# Inside container
make ap AP=C_460 -j8

# Step-by-step execution:
# 1. Parse Makefile hierarchy, determine toolchain
# 2. Download blobs (kernel source, SDK rootfs, etc.)
# 3. Extract kernel to build/ap/<toolchain>_<chipset>_C_460/linux-5.4/
# 4. Apply kernel patches from patchlists
# 5. Configure kernel with defconfig
# 6. Cross-compile kernel: CROSS_COMPILE="ccache aarch64-openwrt-linux-musl-"
# 7. Build kernel modules
# 8. Build external drivers (wlan, ethernet, etc.)
# 9. Build userspace components (sensord, hostapd, etc.)
# 10. Build Go binaries (ocagent, gobin, etc.)
# 11. Stage rootfs with all binaries
# 12. Create squashfs image
# 13. Create FIT kernel image
# 14. Generate manufacturing package
```

### CI Build Command (barney.yaml)

```yaml
build-ap/c460:
  units:
    - floor: .%wifi-ap-build-env
      entry:
        mutables: [/root, /common, /home, /usr]
      build: |
        mkdir -p /tmp/.wifi_build/cache
        export PATH=$PATH:/usr/local/bin

        cd $SRCDIR
        git init
        git config --global --add safe.directory /src/code.arista.io/mgmt/wifi-ap
        git config --global user.email "barney-dev@arista.com"
        git config --global user.name "barney-dev"

        make ap AP=C_460 -j8 NOLOGFILE=1

        mkdir -p /dest/artifacts /dest/symtab
        cp -r /dest/ap/pkg/C_460 /dest/artifacts
        cp -r /dest/ap/symtab /dest/symtab/C_460
```

---

## Native Builds for Unit Testing

### Switching to Native Compilation

For unit tests, the build system switches to native x86_64 compilation:

```makefile
# ap/scripts/tools_vars.mk
ifeq ($(UTESTS), TRUE)
BLD_NATIVE := 1
endif

ifeq ($(BLD_NATIVE), 1)
ARCH := $(shell arch)                    # x86_64
TOOLS_ABBR_NAME := ut-$(ARCH)-gcc        # ut-x86_64-gcc
HOST :=                                   # Empty - use native tools
CROSS :=                                  # Empty - no cross prefix
endif
```

### Running Unit Tests

```bash
# Build and run unit tests (native x86_64)
make ap AP=C_460 UTESTS=TRUE

# This sets:
# - ARCH=x86_64
# - CC=gcc (native)
# - CROSS= (empty)
# - BLD_NATIVE=1
```

---

## Debugging and Troubleshooting

### Common Cross-Compilation Issues

#### 1. Wrong Architecture Binary
```bash
# Check binary architecture
file build/ap/.../sensord/sensord
# Expected: ELF 64-bit LSB executable, ARM aarch64
# Wrong: ELF 64-bit LSB executable, x86-64
```

**Fix**: Ensure `CROSS_COMPILE` is set correctly in the build.

#### 2. Missing Libraries
```
/path/to/aarch64-linux-gnu-ld: cannot find -lssl
```

**Fix**: Add library path to `LDFLAGS`:
```makefile
LIBS += -L$(s4_bins)/usr/lib -Wl,-rpath-link,$(s4_lib)
```

#### 3. Header Not Found
```
fatal error: openssl/ssl.h: No such file or directory
```

**Fix**: Add include path:
```makefile
INC += -I$(s4_inc)
```

### Viewing Cross-Compile Settings

```bash
# Inside container, after sourcing environment
echo "CC: $CC"
echo "CROSS: $CROSS"
echo "ARCH: $ARCH"
echo "TOOLS_DIR: $TOOLS_DIR"

# Verify cross-compiler
$CC --version
# aarch64-none-linux-gnu-gcc (GNU Toolchain...) 11.3.1
```

### Build Verbosity

```bash
# Enable verbose output
make ap AP=C_460 V=1

# Show actual compiler commands with all flags
```

---

## Quick Reference

### Environment Variables

| Variable | Description | Example Value |
|----------|-------------|---------------|
| `ARCH` | Target architecture | `aarch64` |
| `KERNELARCH` | Kernel architecture | `arm64` |
| `CROSS_COMPILE` | Cross-compile prefix | `aarch64-none-linux-gnu-` |
| `K_CROSS` | Kernel cross-compile | `ccache aarch64-openwrt-linux-musl-` |
| `CC` | C compiler | `ccache aarch64-none-linux-gnu-gcc` |
| `TOOLS_DIR` | Toolchain base | `/export` |
| `TOOLS_NAME` | Toolchain directory | `arm-gnu-toolchain-11.3...` |

### AP Model to Toolchain Mapping

| AP Model | Chipset | SPF | Toolchain |
|----------|---------|-----|-----------|
| C-460 | BELLS | 12.2 | gcc-7.5.0-musl-1.1.24-spf12.2 |
| O-435 | BELLS | 12.2/12.5 | gcc-7.5.0-musl-1.1.24-spf12.2 |
| C-430 | MIAMI | 12.2/12.5 | gcc-7.5.0-musl-1.1.24-spf12.2 |
| C-400 | MIAMI | 12.5 | gcc-12.3.0-musl-1.2.4-spf12.5 |
| O-405 | MIAMI | 12.5 | gcc-12.3.0-musl-1.2.4-spf12.5 |
| C-360 | HAWKEYE | 11.4 | gcc-5.2.0-musl-spf11.4 |
| C-330 | HAWKEYE | 11.4 | gcc-5.2.0-musl-spf11.4 |
| W-318 | HAWKEYE | 11.4 | gcc-5.2.0-musl-spf11.4 |

### Key Files

| File | Purpose |
|------|---------|
| `barney.yaml` | Container/image definitions |
| `blobs.yaml` | External dependency management |
| `ap/scripts/tools_vars.mk` | Cross-compiler variables |
| `ap/scripts/vendors.mk` | Vendor selection |
| `scripts/vars.mk` | Global path variables |
| `scripts/rules_common.mk` | Build rule definitions |
| `config.platform` | Chipset-level configuration |
| `config.ap` | AP-model configuration |

### Build Commands

```bash
# Full AP build
make ap AP=C_460 -j8

# Clean build
make clean_ap AP=C_460
make ap AP=C_460 -j8

# Build specific module
make ap AP=C_460 MOD=sensord

# Unit test build (native)
make ap AP=C_460 UTESTS=TRUE

# Verbose build
make ap AP=C_460 V=1

# Without ccache
make ap AP=C_460 CACHE_TOOL=
```

---

## Manual Toolchain Installation and Troubleshooting

This section covers how to manually install toolchains when the `/export` directory is missing content, how to 
verify access to the distribution servers, and what secrets/permissions are required.

### Understanding MUSL vs glibc Toolchains

The repository uses two types of C library implementations in its cross-compilation toolchains:

#### GNU glibc Toolchain
- **Use Case**: General userspace applications
- **Toolchain**: `arm-gnu-toolchain-11.3.rel1-x86_64-aarch64-none-linux-gnu`
- **Compiler Prefix**: `aarch64-none-linux-gnu-`
- **Features**: Full POSIX compliance, dynamic linking, larger runtime

#### MUSL Toolchains (Embedded/Kernel)
- **Use Case**: Kernel builds, drivers, lightweight embedded components
- **Examples**:
  - SPF 10: `toolchain-aarch64_cortex-a53_gcc-5.2.0_musl-1.1.16-spf10cs`
  - SPF 11.1: `toolchain-aarch64_cortex-a53_gcc-5.2.0_musl-1.1.16-spf11.1`
  - SPF 12.2: `toolchain-aarch64_cortex-a73_gcc-7.5.0_musl-1.1.24-spf12.2`
  - SPF 12.5: `toolchain-aarch64_cortex-a53_gcc-12.3.0_musl-1.2.4-spf12.5`
- **Compiler Prefix**: `aarch64-openwrt-linux-musl-`
- **Features**: Small footprint, static linking friendly, faster startup

### Verifying Access to Distribution Servers

Before manually installing toolchains, verify you can access the Arista distribution servers.

#### Distribution Server URLs

| Server | URL | Purpose |
|--------|-----|---------|
| Primary Dist | `http://dist.aristanetworks.com/storage/wifi` | Main toolchain/blob storage |
| WiFi Build | `http://wifi-build.sjc.aristanetworks.com/storage/bin` | WiFi-specific builds |
| Pune Mirror | `http://distwifi.pune.aristanetworks.com` | Regional mirror |

#### Connectivity Test Commands

```bash
# Test basic connectivity to dist server
curl -I http://dist.aristanetworks.com/storage/wifi/

# Test access to toolchains directory
curl -I http://dist.aristanetworks.com/storage/wifi/toolchains/

# List available toolchains (if directory listing is enabled)
curl http://dist.aristanetworks.com/storage/wifi/toolchains/

# Test specific toolchain file
wget --spider 
http://dist.aristanetworks.com/storage/wifi/toolchains/arm-gnu-toolchain-11.3.alma_rel1-x86_64-aarch64-none-linux-gnu.tar.xz
```

#### Network Requirements

1. **VPN/Network Access**: Must be on Arista corporate network or VPN
2. **DNS Resolution**: Ensure `dist.aristanetworks.com` resolves correctly
3. **Firewall**: Port 80 (HTTP) must be open to the distribution servers
4. **Proxy**: If behind a proxy, configure `http_proxy` environment variable

```bash
# If behind proxy
export http_proxy=http://proxy.aristanetworks.com:8080
export https_proxy=http://proxy.aristanetworks.com:8080

# Test with proxy
wget --spider http://dist.aristanetworks.com/storage/wifi/toolchains/
```

### Manual Toolchain Installation

If the `/export` directory is missing toolchains (removed from container, corrupted, or building outside 
container), you can install them manually.

#### Where to Run Commands

| Environment | Installation Path | Notes |
|-------------|------------------|-------|
| Inside Barney container | `/export/` | Standard location |
| Local development | `/export/` or custom path | Update `TOOLS_DIR` in Makefile |
| CI runner | `/export/` | Containers should have toolchains pre-installed |

#### Installing GNU glibc Toolchain (GCC 11.3)

```bash
# Set distribution base URL
export DIST_BASE=http://dist.aristanetworks.com/storage/wifi

# Create installation directory
sudo mkdir -p /export

# Download GNU toolchain
wget -nv $DIST_BASE/toolchains/arm-gnu-toolchain-11.3.alma_rel1-x86_64-aarch64-none-linux-gnu.tar.xz \
-O /tmp/toolchain-11.3.rel1-x86_64-aarch64-gnu.tar.xz

# Verify checksum (CRITICAL for security!)
echo "5c281156f064abec19be13183c675010e0906031cf31d6e019e08b138e7c639e 
/tmp/toolchain-11.3.rel1-x86_64-aarch64-gnu.tar.xz" \
| sha256sum --strict --check -

# Extract to /export
sudo tar -Jxf /tmp/toolchain-11.3.rel1-x86_64-aarch64-gnu.tar.xz -C /export

# Verify installation
ls /export/arm-gnu-toolchain-11.3.rel1-x86_64-aarch64-none-linux-gnu/bin/
/export/arm-gnu-toolchain-11.3.rel1-x86_64-aarch64-none-linux-gnu/bin/aarch64-none-linux-gnu-gcc --version

# Cleanup
rm /tmp/toolchain-11.3.rel1-x86_64-aarch64-gnu.tar.xz
```

#### Installing MUSL Toolchains

```bash
export DIST_BASE=http://dist.aristanetworks.com/storage/wifi
sudo mkdir -p /export

# SPF 10 Toolchain (HAWKEYE platform - older APs)
wget -nv $DIST_BASE/toolchains/toolchain-aarch64_cortex-a53_gcc-5.2.0_musl-1.1.16-spf10cs.tar.xz \
-O /tmp/toolchain-5.2.0-musl.tar.xz
echo "2e5b2d7dc690ae84d18f193aad4d6c71f0ff3a264db5df54172c7a6b6586f0f9  /tmp/toolchain-5.2.0-musl.tar.xz" \
| sha256sum --strict --check -
sudo tar -Jxf /tmp/toolchain-5.2.0-musl.tar.xz -C /export

# SPF 11.1 Toolchain (HAWKEYE - C-360, C-330, W-318)
wget -nv $DIST_BASE/toolchains/toolchain-aarch64_cortex-a53_gcc-5.2.0_musl-1.1.16-spf11.1.tar.xz \
-O /tmp/toolchain-5.2.0-musl-spf11.1.tar.xz
echo "eeb0e1e1a9b6e1f1be836ccd439ebb1e5d169ec15846e43ffc659186479fe7aa 
/tmp/toolchain-5.2.0-musl-spf11.1.tar.xz" \
| sha256sum --strict --check -
sudo tar -Jxf /tmp/toolchain-5.2.0-musl-spf11.1.tar.xz -C /export

# SPF 12.2 Toolchain (BELLS - C-460, O-435, C-430)
wget -nv $DIST_BASE/toolchains/toolchain-aarch64_cortex-a73_gcc-7.5.0_musl-1.1.24-spf12.2_cs.tar.xz \
-O /tmp/toolchain-7.5.0-musl-spf12.2.tar.xz
echo "49012fa7874df9e39641f919de571dea2298319d6303c915e017858fedc61f50  
/tmp/toolchain-7.5.0-musl-spf12.2.tar.xz" \
| sha256sum --strict --check -
sudo tar -Jxf /tmp/toolchain-7.5.0-musl-spf12.2.tar.xz -C /export

# SPF 12.5 Toolchain (MIAMI - C-400, O-405)
wget -nv $DIST_BASE/toolchains/toolchain-aarch64_cortex-a53_gcc-12.3.0_musl-1.2.4-spf12.5ed.tar.xz \
-O /tmp/toolchain-12.3.0-musl-spf12.5.tar.xz
echo "5845e0b02d5b934ec6960605074c0cec9a5ecfc9864e2c01b5db1bfd96fb8aad  
/tmp/toolchain-12.3.0-musl-spf12.5.tar.xz" \
| sha256sum --strict --check -
sudo tar -Jxf /tmp/toolchain-12.3.0-musl-spf12.5.tar.xz --no-same-owner -C /export

# Cleanup
rm /tmp/*.tar.xz
```

#### Installing AP Build Tools

```bash
export DIST_BASE=http://dist.aristanetworks.com/storage/wifi

wget -nv $DIST_BASE/build-slaves/tools/ap-build-tools-2.0.12.tar.xz \
-O /tmp/ap-build-tools.tar.xz
echo "551896e2091109a3e69207f2df9517697e3f0b72f2b6fd05354e8523404da252 /tmp/ap-build-tools.tar.xz" \
| sha256sum --strict --check -
sudo tar -Jxf /tmp/ap-build-tools.tar.xz -C /export

# Verify
ls /export/ap-build-tools/
```

### Complete Installation Script

Create a script to install all toolchains at once:

```bash
#!/bin/bash
# install_toolchains.sh - Install all cross-compilation toolchains

set -e  # Exit on error

DIST_BASE="http://dist.aristanetworks.com/storage/wifi"
EXPORT_DIR="${EXPORT_DIR:-/export}"

echo "Installing toolchains to $EXPORT_DIR..."
sudo mkdir -p "$EXPORT_DIR"

# Function to download, verify, and extract
install_toolchain() {
  local url="$1"
  local checksum="$2"
  local filename=$(basename "$url")
  local tmpfile="/tmp/$filename"

  echo "Downloading $filename..."
  wget -nv "$url" -O "$tmpfile"

  echo "Verifying checksum..."
  echo "$checksum  $tmpfile" | sha256sum --strict --check -

  echo "Extracting to $EXPORT_DIR..."
  sudo tar -Jxf "$tmpfile" --no-same-owner -C "$EXPORT_DIR"

  rm -f "$tmpfile"
  echo "Done: $filename"
  echo
}

# GNU glibc Toolchain
install_toolchain \
"$DIST_BASE/toolchains/arm-gnu-toolchain-11.3.alma_rel1-x86_64-aarch64-none-linux-gnu.tar.xz" \
"5c281156f064abec19be13183c675010e0906031cf31d6e019e08b138e7c639e"

# MUSL Toolchains
install_toolchain \
"$DIST_BASE/toolchains/toolchain-aarch64_cortex-a53_gcc-5.2.0_musl-1.1.16-spf10cs.tar.xz" \
"2e5b2d7dc690ae84d18f193aad4d6c71f0ff3a264db5df54172c7a6b6586f0f9"

install_toolchain \
"$DIST_BASE/toolchains/toolchain-aarch64_cortex-a53_gcc-5.2.0_musl-1.1.16-spf11.1.tar.xz" \
"eeb0e1e1a9b6e1f1be836ccd439ebb1e5d169ec15846e43ffc659186479fe7aa"

install_toolchain \
"$DIST_BASE/toolchains/toolchain-aarch64_cortex-a73_gcc-7.5.0_musl-1.1.24-spf12.2_cs.tar.xz" \
"49012fa7874df9e39641f919de571dea2298319d6303c915e017858fedc61f50"

install_toolchain \
"$DIST_BASE/toolchains/toolchain-aarch64_cortex-a53_gcc-12.3.0_musl-1.2.4-spf12.5ed.tar.xz" \
"5845e0b02d5b934ec6960605074c0cec9a5ecfc9864e2c01b5db1bfd96fb8aad"

# AP Build Tools
install_toolchain \
"$DIST_BASE/build-slaves/tools/ap-build-tools-2.0.12.tar.xz" \
"551896e2091109a3e69207f2df9517697e3f0b72f2b6fd05354e8523404da252"

echo "All toolchains installed successfully!"
echo
echo "Installed toolchains:"
ls -la "$EXPORT_DIR"
```

### Secrets and Permissions Required

#### No Secrets Needed for Toolchain Download

Toolchain downloads from `dist.aristanetworks.com` **do not require authentication** - they only require 
network access to Arista's internal network.

#### Secrets Required for Other Build Operations

| Secret | Environment Variable | Purpose | Where Defined |
|--------|---------------------|---------|---------------|
| Vault Secret ID | `VAULT_SECRET_ID` | Image signing via Vault | `barney.yaml` → 
`${secrets.wifi_licensing_server_token}` |
| ccache URL | `CCACHE_REMOTE_STORAGE` | Remote build cache | `barney.yaml` → 
`${secrets.wifi_ccache_remote_storage_url}` |

#### CI/CD Secrets (Barney)

In `barney.yaml`, secrets are referenced as `${secrets.<name>}`:

```yaml
wifi-ap-build-env:
  entry:
    env:
      VAULT_SECRET_ID: "${secrets.wifi_licensing_server_token}"
      CCACHE_REMOTE_STORAGE: 
      "${secrets.wifi_ccache_remote_storage_url:-redis://wifi-ccache-redis.infra.corp.arista.io:65531}"
```

These secrets are managed by Barney infrastructure and are automatically injected during CI builds. For local 
builds without these secrets:

```bash
# Build without remote ccache (slower but works)
export CCACHE_REMOTE_ONLY=false

# Skip image signing (for development only)
# Note: Signed images are required for production
```

### Verifying Toolchain Installation

After installation, verify the toolchains are correctly installed:

```bash
# Check all expected directories exist
echo "=== Checking /export directory ==="
ls -la /export/

# Expected output:
# drwxr-xr-x  arm-gnu-toolchain-11.3.rel1-x86_64-aarch64-none-linux-gnu
# drwxr-xr-x  toolchain-aarch64_cortex-a53_gcc-5.2.0_musl-1.1.16-spf10cs
# drwxr-xr-x  toolchain-aarch64_cortex-a53_gcc-5.2.0_musl-1.1.16-spf11.1
# drwxr-xr-x  toolchain-aarch64_cortex-a73_gcc-7.5.0_musl-1.1.24-spf12.2
# drwxr-xr-x  toolchain-aarch64_cortex-a53_gcc-12.3.0_musl-1.2.4-spf12.5
# drwxr-xr-x  ap-build-tools

# Verify GNU compiler
echo "=== GNU glibc Compiler ==="
/export/arm-gnu-toolchain-11.3.rel1-x86_64-aarch64-none-linux-gnu/bin/aarch64-none-linux-gnu-gcc --version
# Expected: aarch64-none-linux-gnu-gcc (GNU Toolchain for the A-profile Architecture 11.3.rel1...) 11.3.1

# Verify MUSL compilers
echo "=== MUSL SPF 12.2 Compiler (BELLS) ==="
/export/toolchain-aarch64_cortex-a73_gcc-7.5.0_musl-1.1.24-spf12.2/bin/aarch64-openwrt-linux-musl-gcc 
--version
# Expected: aarch64-openwrt-linux-musl-gcc (OpenWrt GCC 7.5.0) 7.5.0

echo "=== MUSL SPF 12.5 Compiler (MIAMI) ==="
/export/toolchain-aarch64_cortex-a53_gcc-12.3.0_musl-1.2.4-spf12.5/bin/aarch64-openwrt-linux-musl-gcc 
--version
# Expected: aarch64-openwrt-linux-musl-gcc (OpenWrt GCC 12.3.0) 12.3.0

# Verify cross-compilation works
echo "=== Test Cross-Compilation ==="
echo 'int main() { return 0; }' > /tmp/test.c
/export/arm-gnu-toolchain-11.3.rel1-x86_64-aarch64-none-linux-gnu/bin/aarch64-none-linux-gnu-gcc \
-o /tmp/test_arm64 /tmp/test.c
file /tmp/test_arm64
# Expected: ELF 64-bit LSB executable, ARM aarch64, version 1 (SYSV)...
rm /tmp/test.c /tmp/test_arm64
```

### Troubleshooting Missing /export Content

#### Issue: "/export directory does not exist" Error

```
ap/scripts/tools_vars.mk:80: *** /export/arm-gnu-toolchain-11.3... directory does not exist!
```

**Solutions**:

1. **Inside Container**: Ensure you're using the correct Barney image:
   ```bash
   barney run .%wifi-ap-build-env -- /bin/bash
   ls /export/   # Should show toolchains
   ```

2. **Wrong Container Image**: Use `wifi-ap-build-env`, not just `wifi-almalinux`:
   ```bash
   # Wrong (no toolchains)
   barney run .%wifi-almalinux -- /bin/bash

   # Correct (has toolchains)
   barney run .%wifi-ap-build-env -- /bin/bash
   ```

3. **Manual Install**: Follow the installation steps above

#### Issue: "Connection refused" or "Host not found"

```
wget: unable to resolve host address 'dist.aristanetworks.com'
```

**Solutions**:

1. Check VPN connection
2. Verify DNS resolution: `nslookup dist.aristanetworks.com`
3. Try alternate server: `http://wifi-build.sjc.aristanetworks.com/storage/bin`
4. Check proxy settings

#### Issue: "Checksum mismatch"

```
sha256sum: WARNING: 1 computed checksum did NOT match
```

**Solutions**:

1. **Corrupted download**: Re-download the file
2. **Outdated checksum**: Check `barney.yaml` for the latest checksums
3. **Wrong file**: Verify you're downloading the correct toolchain version

#### Issue: "Permission denied" when extracting

```
tar: Cannot open: Permission denied
```

**Solutions**:

1. Use `sudo` when extracting to `/export`
2. Use `--no-same-owner` flag: `tar -Jxf file.tar.xz --no-same-owner -C /export`
3. Create directory with correct permissions first: `sudo mkdir -p /export && sudo chmod 755 /export`

### Using a Custom Toolchain Path

If you cannot install to `/export`, you can use a custom path:

```bash
# Install to custom location
mkdir -p ~/toolchains
export EXPORT_DIR=~/toolchains
# Run installation script with custom EXPORT_DIR

# Override in build
make ap AP=C_460 TOOLS_DIR=~/toolchains
```

Or modify `ap/scripts/tools_vars.mk` temporarily:
```makefile
# Change this:
TOOLS_BASE_DIR := $(TOOLS_DIR)/$(TOOLS_NAME)
# To:
TOOLS_BASE_DIR := /home/$(USER)/toolchains/$(TOOLS_NAME)
```

---

## Summary

Cross-compilation in this repository is achieved through:

1. **Container Environment**: Barney containers provide a consistent x86_64 AlmaLinux build environment with
all necessary tools and toolchains pre-installed

2. **Multiple Toolchains**: Pre-built cross-compilers for different targets (glibc, musl variants) installed
in `/export`

3. **Makefile Configuration**: Platform-specific config files (`config.platform`, `config.ap`) set
`CROSS_COMPILE`, `ARCH`, and toolchain paths

4. **Blob System**: External dependencies (kernel source, SDK rootfs, vendor SDKs) are downloaded, verified,
and extracted via `blobs.yaml`

5. **Build Orchestration**: Hierarchical Makefiles coordinate kernel, driver, userspace, and image builds

6. **Build Caching**: ccache with remote Redis storage accelerates rebuilds

7. **Multi-Language Support**: C/C++ (GCC), Go (with CGO), Meson, CMake all support cross-compilation

The container itself is architecture-agnostic - it's the toolchains and Makefile variables that enable
building ARM64 binaries on an x86_64 host.
