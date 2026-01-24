# Linux Kernel Patch Management Workflow

This document explains how to download, manage, and apply patches to the Linux kernel (specifically linux-5.4) used in this project.

## Overview

The kernel patch management system uses a hierarchical structure with three levels of patches:
1. **Common patches** - Apply to all platforms using a specific kernel version
2. **SPF patches** - Apply to platforms using a specific Software Platform (SPF) version
3. **Platform-specific patches** - Apply only to a specific AP model

---

## Build Pipeline: How `make ap AP=C_460` Downloads the Kernel

When you run `make ap AP=C_460`, the following pipeline is triggered:

### Step 1: Top-Level Makefile Invocation

```
Makefile (root)
    └── ap target
        └── calls make_ap function
            └── $(MAKE) -C $(AP_SCRIPTS_DIR) ... all
```

The `make_ap` function in the root `Makefile` (lines 196-261) determines:
- Whether to use new or old platform infrastructure
- Sets `PLATFORM_AP_MODEL`, `PLATFORM_CHIPSET`, `PLATFORM_CHIPSET_VENDOR`

### Step 2: AP Scripts Makefile Processing

`ap/scripts/Makefile` is invoked and:

1. **Loads AP Configuration**:
   ```makefile
   include $(NEW_PLATFORM_AP_PATH)/common/config/config.ap
   include $(NEW_PLATFORM_AP_PATH)/SPF/$(SPF)/config/config_spf.ap
   ```

2. **Sets Key Variables** (from `config_spf.ap`):
   ```makefile
   KERNEL_VERSION := 5.4
   SPF := 12.2
   SEC_SDK_VERSION := 12.2
   ```

3. **Includes Module Definitions**:
   ```makefile
   include $(PLAT_MODULES_DIR)/config.modules
   ```

### Step 3: Kernel Module Build Triggered

When the `kernel` module is built:

```
ap/platform/cvendors/QCA/SPF/12.2/src/kernel/
    ├── kernel.mk      # Module definition
    └── Makefile.sdk   # Build rules
```

**kernel.mk** defines:
```makefile
kernel_mod = linux-$(KERNEL_VERSION)
kernel_src = $(NEW_QCA_SPF_PATH)/$(SPF)/src/kernel
kernel_bld = $(K_BLD_DIR_TC_PLAT)
kernel_path = $(kernel_bld)/$(kernel_mod)
```

**Makefile.sdk** defines the source tarball:
```makefile
KERNEL_SRC_DIR := $(NEW_QCA_SPF_PATH)/$(SPF)/src_blobs
KERNEL_SRC_FILE := $(KERNEL_SRC_DIR)/linux-$(KERNEL_VERSION).tar.gz
SRC := $(KERNEL_SRC_FILE)
```

### Step 4: Blob Download via `generate.mk`

The magic happens in `scripts/rules_ext.mk`:

```makefile
# Convert $(SRC) to absolute PATH
BLOB_BLD_DEPS ?= $(if $(filter $(TOPDIR)%,$(SRC)),$(SRC),$(CURDIR)/$(SRC))

# Include blob-utils rules
include $(BLOBS_RULES_MAK)  # /usr/share/blob-utils/generate.mk
```

The `generate.mk` (from `blob-utils` package) does the following:

1. **Reads `blobs.yaml`** to find the source file mapping:
   ```yaml
   - dest: ap/platform/cvendors/QCA/SPF/12.2/src_blobs/linux-5.4.tar.gz
     shasum: e6d261562a5b330a2bc6353752b92b8b11b4db9254efe97a5eaa2f7ce5ab858d
     size: 1930257560
     source: linux-5.4.tar.gz.e6d261562a5b330a2bc6353752b92b8b11b4db9254efe97a5eaa2f7ce5ab858d
   ```

2. **Downloads from Distribution Server**:
   ```
   DIST_WIFI_BASE = http://distwifi.pune.aristanetworks.com/storage/bin
   ```

   The blob is downloaded to a cache directory (`DIST_CACHE_DIR`) and then symlinked/copied to the destination.

3. **Verifies SHA256 checksum** against `blobs.yaml`

### Step 5: Source Extraction and Patch Application

In `scripts/rules_ext.mk`, the `.common_prep` target:

```makefile
$(BLD_DIR)/.common_prep: $(if $(BLOB_BLD_DEPS),$(blob_bld_deps), | $(BLD_DIR))
    # Extract tarball
    for src in $(SRC); do
        tar -xf $$src --strip-components 1 -C $(BLD_DIR);
    done;

    # Apply patches using git am (for kernel 5.4+)
    cd $(BLD_DIR);
    for i in $(PATCHES_LIST); do
        echo "Applying patchfile (using git am) $$i";
        git am $$i;
    done;
```

### Step 6: Patch List Assembly

**Makefile.sdk** assembles patches from three sources:

```makefile
KERNEL_PATCHLIST := patchlists/kernel_patchlist

# Platform-specific patches
PLATFORM_PATCH_FILE := $(NEW_PLATFORM_AP_PATH)/SPF/$(SPF)/$(KERNEL_PATCHLIST)
PLATFORM_PATCH_DIR := $(PLATFORM_BASE)/patches/kernel/$(KERNEL_VERSION)/$(SPF)/$(PLATFORM_AP_MODEL)

# Common patches (all platforms)
COMMON_PATCH_FILE := $(NEW_QCA_PATH)/kernel/$(KERNEL_VERSION)/$(KERNEL_PATCHLIST)
COMMON_PATCH_DIR := $(PLATFORM_BASE)/patches/kernel/$(KERNEL_VERSION)/common

# SPF-specific patches
SPF_PATCH_FILE := $(NEW_QCA_SPF_PATH)/$(SPF)/$(KERNEL_PATCHLIST)
SPF_PATCH_DIR := $(PLATFORM_BASE)/patches/kernel/$(KERNEL_VERSION)/$(SPF)/common

# Combine all patches
PATCHES_LIST += $(addprefix $(PLATFORM_PATCH_DIR)/,$(file < $(PLATFORM_PATCH_FILE)))
PATCHES_LIST += $(addprefix $(COMMON_PATCH_DIR)/,$(file < $(COMMON_PATCH_FILE)))
PATCHES_LIST += $(addprefix $(SPF_PATCH_DIR)/,$(file < $(SPF_PATCH_FILE)))
```

### Complete Flow Diagram

```
make ap AP=C_460
    │
    ├── Load config.ap (C_460 specific)
    │   └── Sets: KERNEL_VERSION=5.4, SPF=12.2
    │
    ├── Build kernel module
    │   │
    │   ├── BLOB_BLD_DEPS = linux-5.4.tar.gz
    │   │
    │   ├── generate.mk (blob-utils)
    │   │   ├── Read blobs.yaml
    │   │   ├── Download from DIST_WIFI_BASE
    │   │   │   └── http://distwifi.pune.aristanetworks.com/storage/bin/
    │   │   │       linux-5.4.tar.gz.<sha256>
    │   │   ├── Verify SHA256
    │   │   └── Place at: ap/platform/cvendors/QCA/SPF/12.2/src_blobs/linux-5.4.tar.gz
    │   │
    │   ├── Extract tarball to BLD_DIR
    │   │
    │   └── Apply patches (git am)
    │       ├── Common patches (ap/platform/patches/kernel/5.4/common/)
    │       ├── SPF patches (ap/platform/patches/kernel/5.4/12.2/common/)
    │       └── Platform patches (ap/platform/patches/kernel/5.4/12.2/C_460/)
    │
    └── Continue with kernel build...
```

---

## Downloading the Linux Kernel

### Method 1: Using the Build System (Recommended)

When you run `make ap AP=C_460`, the build system automatically downloads the kernel via the `blob-utils` package. This requires access to the internal distribution server.

```bash
# This automatically downloads all required blobs including the kernel
make ap AP=C_460
```

### Method 2: Manual Download from Internal Server

If you need to download the kernel manually (e.g., for a separate patch management repo):

```bash
# For SPF 12.2 (C_460, O_435)
DIST_WIFI_BASE="http://distwifi.pune.aristanetworks.com/storage/bin"
KERNEL_BLOB="linux-5.4.tar.gz.e6d261562a5b330a2bc6353752b92b8b11b4db9254efe97a5eaa2f7ce5ab858d"

mkdir -p ap/platform/cvendors/QCA/SPF/12.2/src_blobs
curl -L -o ap/platform/cvendors/QCA/SPF/12.2/src_blobs/linux-5.4.tar.gz \
    "${DIST_WIFI_BASE}/${KERNEL_BLOB}"

# Verify checksum
echo "e6d261562a5b330a2bc6353752b92b8b11b4db9254efe97a5eaa2f7ce5ab858d  ap/platform/cvendors/QCA/SPF/12.2/src_blobs/linux-5.4.tar.gz" | sha256sum -c

# For SPF 12.5 (C_400, C_430)
KERNEL_BLOB_12_5="linux-5.4.tar.gz.ef3fa4f249c40feb79ac77e7c8a7d59f0ba04146634d5794abcce2376155b8f9"

mkdir -p ap/platform/cvendors/QCA/SPF/12.5/src_blobs
curl -L -o ap/platform/cvendors/QCA/SPF/12.5/src_blobs/linux-5.4.tar.gz \
    "${DIST_WIFI_BASE}/${KERNEL_BLOB_12_5}"
```

### Method 3: Using `blobs` Make Target

```bash
# Download all blobs defined in blobs.yaml
make blobs
```

This runs `blobs_process.py` which reads `blobs.yaml` and downloads all required files.

### Method 4: Download Vanilla Kernel from kernel.org (For External Development)

If you don't have access to the internal server, you can download the vanilla kernel:

```bash
# Download vanilla Linux 5.4 from kernel.org
wget https://cdn.kernel.org/pub/linux/kernel/v5.x/linux-5.4.tar.xz

# Extract
tar -xf linux-5.4.tar.xz

# Initialize git repo for patch management
cd linux-5.4
git init
git add -A
git commit -m "Initial import: Linux 5.4 vanilla from kernel.org"
git tag vanilla-5.4
```

**Note:** The internal kernel tarball may contain vendor-specific modifications from Qualcomm (QCA). The vanilla kernel from kernel.org is the upstream version without these modifications.

### Kernel Blob Reference (from blobs.yaml)

| SPF Version | Destination Path | SHA256 | Size |
|-------------|------------------|--------|------|
| 12.2 | `ap/platform/cvendors/QCA/SPF/12.2/src_blobs/linux-5.4.tar.gz` | `e6d261...` | ~1.9 GB |
| 12.5 | `ap/platform/cvendors/QCA/SPF/12.5/src_blobs/linux-5.4.tar.gz` | `ef3fa4...` | ~1.9 GB |

---

## Directory Structure

```
ap/platform/
├── patches/
│   └── kernel/
│       ├── 4.4/                          # Kernel 4.4 patches
│       └── 5.4/                          # Kernel 5.4 patches
│           ├── common/                   # Common patches for all 5.4 platforms
│           │   ├── CVE-*.patch
│           │   └── feature_*.patch
│           ├── 12.2/                     # SPF 12.2 specific
│           │   ├── common/               # Common to all 12.2 boards
│           │   ├── C_460/                # Platform-specific patches
│           │   └── O_435/
│           └── 12.5/                     # SPF 12.5 specific
│               ├── common/
│               ├── C_400/
│               └── C_430/
├── cvendors/QCA/
│   ├── kernel/
│   │   └── 5.4/patchlists/
│   │       └── kernel_patchlist          # Common patchlist for kernel 5.4
│   ├── SPF/
│   │   ├── 12.2/
│   │   │   ├── patchlists/
│   │   │   │   └── kernel_patchlist      # SPF-level patchlist
│   │   │   └── src_blobs/
│   │   │       └── linux-5.4.tar.gz      # Kernel source tarball
│   │   └── 12.5/
│   │       └── ...
│   └── boards/
│       └── <AP_MODEL>/SPF/<SPF_VERSION>/
│           └── patchlists/
│               └── kernel_patchlist      # Platform-specific patchlist
```

## How to Fetch the Linux Kernel

### 1. From Internal Distribution Server

The kernel source blobs are stored on the internal distribution server and managed via `blobs.yaml`:

```bash
# Blobs are downloaded from:
DIST_WIFI_BASE="http://distwifi.pune.aristanetworks.com/storage/bin"

# To download manually:
curl -O $DIST_WIFI_BASE/<blob_source_name>
```

### 2. Extracting the Kernel

```bash
# Extract to a working directory
KERNEL_VERSION="5.4"
LINUX_PATH="/path/to/working/linux-${KERNEL_VERSION}"
mkdir -p "$LINUX_PATH"
tar -xzf linux-${KERNEL_VERSION}.tar.gz -C "$LINUX_PATH" --strip-components=1
```

### 3. Using the Automated Script

The `src-patches.sh` script automates downloading and extracting kernels for all supported APs:

```bash
./src-patches.sh /path/to/repo
```

This will create patched kernel trees at `ap/src/kernels/<AP>_linux_<VERSION>/`.

## Patchlist Format

Patchlists are simple text files listing patch filenames (one per line):

```
# ap/platform/cvendors/QCA/kernel/5.4/patchlists/kernel_patchlist
max_akm_suite_update.patch
increase_custom_event_size.patch
content_analytic_support.patch
CVE-2023-1206_bug835295.patch
CVE-2023-0590_bug793340.patch
...
```

## Patch Format

Patches should be in git-format (created with `git format-patch`):

```
From <commit-sha> Mon Sep 17 00:00:00 2001
From: Author Name <email@example.com>
Date: Tue, 5 Dec 2023 22:33:29 -0800
Subject: [PATCH] Brief description of the change

Detailed description and patch links for reference:
https://git.kernel.org/pub/scm/linux/kernel/git/stable/linux.git/commit/...

---
 path/to/file.c | 25 ++++++++++++++-----------
 1 file changed, 14 insertions(+), 11 deletions(-)

diff --git a/path/to/file.c b/path/to/file.c
index 96c3e9c..4ddaf69 100644
--- a/path/to/file.c
+++ b/path/to/file.c
...
```

## Applying Patches

### Method 1: Using git am (Recommended for kernel 5.4+)

```bash
cd /path/to/linux-5.4
git init  # if not already a git repo

# Apply patches from patchlist
PATCHES_DIR="ap/platform/patches/kernel/5.4/common"
while read patch_name; do
    git am "${PATCHES_DIR}/${patch_name}"
done < /path/to/kernel_patchlist
```

### Method 2: Using patch command (Legacy, for kernel 4.4)

```bash
cd /path/to/linux-4.4

# Apply individual patch
patch -p1 < /path/to/patch-file.patch

# Apply multiple patches
for patch in /path/to/patches/*.patch; do
    patch -p1 < "$patch"
done
```

### Method 3: Using the Build System

The build system automatically applies patches during the kernel build:

```bash
# Makefile.sdk handles patch application
# Patches are applied via PATCHES_LIST variable
make kernel
```

---

## Adding a New Patch

### Step 1: Create the Patch File

```bash
# In your working kernel directory with the fix
git add <modified-files>
git commit -m "Brief description of the change"

# Generate the patch
git format-patch -1 HEAD --stdout > my-patch-name.patch

# Or for multiple commits
git format-patch HEAD~3..HEAD
```

### Step 2: Place the Patch in the Correct Directory

| Scope | Directory |
|-------|-----------|
| All platforms (5.4) | `ap/platform/patches/kernel/5.4/common/` |
| SPF-specific | `ap/platform/patches/kernel/5.4/<SPF>/common/` |
| Platform-specific | `ap/platform/patches/kernel/5.4/<SPF>/<AP_MODEL>/` |

### Step 3: Add Patch to Patchlist

Edit the appropriate patchlist file:

```bash
# For common patches
echo "my-patch-name.patch" >> ap/platform/cvendors/QCA/kernel/5.4/patchlists/kernel_patchlist

# For SPF-specific patches
echo "my-patch-name.patch" >> ap/platform/cvendors/QCA/SPF/12.5/patchlists/kernel_patchlist

# For platform-specific patches
echo "my-patch-name.patch" >> ap/platform/cvendors/QCA/boards/<AP_MODEL>/SPF/<SPF>/patchlists/kernel_patchlist
```

### Step 4: Verify the Patch

```bash
# Test apply (dry run)
cd /path/to/kernel
git apply --check /path/to/my-patch-name.patch

# Or for git am
git am --dry-run /path/to/my-patch-name.patch
```

---

## Removing a Patch

### Step 1: Remove from Patchlist

Edit the appropriate patchlist file and remove the patch filename.

### Step 2: (Optional) Delete the Patch File

```bash
rm ap/platform/patches/kernel/5.4/common/my-patch-name.patch
```

### Step 3: Verify Build

Rebuild the kernel to ensure no dependencies on the removed patch.

---

## Setting Up a Separate Kernel Repository for Patch Management

To create a dedicated repository for managing kernel patches more efficiently:

### 1. Initialize the Kernel Repository

```bash
# Create a new directory for your kernel repo
mkdir linux-5.4-patches
cd linux-5.4-patches

# Download and extract vanilla kernel
wget https://cdn.kernel.org/pub/linux/kernel/v5.x/linux-5.4.tar.xz
tar -xf linux-5.4.tar.xz
cd linux-5.4

# Initialize git
git init
git add -A
git commit -m "Initial import: Linux 5.4 vanilla"
git tag vanilla-5.4
```

### 2. Create a Branch for Your Patches

```bash
# Create development branch
git checkout -b arista-patches

# Apply existing patches in order
PATCH_DIR="/path/to/ap/platform/patches/kernel/5.4/common"
while read patch_name; do
    git am "${PATCH_DIR}/${patch_name}"
done < /path/to/kernel_patchlist
```

### 3. Workflow for Adding New Patches

```bash
# Make your changes
vim drivers/net/some_file.c

# Commit with proper message format
git add drivers/net/some_file.c
git commit -m "net: fix issue in some_file

Detailed description of the fix.
Reference: BUG-123456"

# Export the patch
git format-patch HEAD~1 -o /path/to/ap/platform/patches/kernel/5.4/common/

# Add to patchlist
echo "0001-net-fix-issue-in-some_file.patch" >> /path/to/kernel_patchlist
```

### 4. Workflow for Removing Patches

```bash
# Interactive rebase to remove a patch
git rebase -i vanilla-5.4

# In the editor, delete or comment out the line for the patch to remove
# Save and exit

# Regenerate all patches
rm /path/to/ap/platform/patches/kernel/5.4/common/*.patch
git format-patch vanilla-5.4..HEAD -o /path/to/ap/platform/patches/kernel/5.4/common/

# Update patchlist
ls /path/to/ap/platform/patches/kernel/5.4/common/*.patch | \
    xargs -n1 basename > /path/to/kernel_patchlist
```

### 5. Updating to a New Kernel Version

```bash
# Fetch new kernel
wget https://cdn.kernel.org/pub/linux/kernel/v5.x/linux-5.4.NEW.tar.xz

# Create new branch from vanilla
git checkout vanilla-5.4
git checkout -b update-5.4.NEW

# Extract and update
tar -xf linux-5.4.NEW.tar.xz --strip-components=1
git add -A
git commit -m "Update to Linux 5.4.NEW"
git tag vanilla-5.4.NEW

# Rebase patches
git checkout arista-patches
git rebase vanilla-5.4.NEW

# Resolve any conflicts and continue
# git rebase --continue
```

---

## Current Included Patches (Kernel 5.4)

The kernel 5.4 common patches include security fixes (CVEs) and feature enhancements:

### Security Patches (CVEs)
| Patch | Description |
|-------|-------------|
| CVE-2023-0590 | Race condition fix in qdisc_graft() |
| CVE-2023-1206 | Bug 835295 fix |
| CVE-2023-2248 | Bug 809258 fix |
| CVE-2023-32233 | Bug 813345 fix |
| CVE-2023-35001 | Bug 835298 fix |
| CVE-2023-3609 | Bug 842604 fix |
| CVE-2023-3611 | Bug 842606 fix |
| CVE-2024-1086 | Bug 943600 fix |
| ... | (See full list in patchlist) |

### Feature Patches
| Patch | Description |
|-------|-------------|
| max_akm_suite_update | AKM suite updates |
| increase_custom_event_size | Increase nl80211 custom event buffer |
| content_analytic_support | Content analytics support |
| gre_copy_tos_v6 | GRE ToS copy for IPv6 |
| bridge_gwmac | Gateway MAC support for bridge |
| vxlan_perf | VXLAN performance improvements |
| vxlan_fragment | VXLAN fragmentation support |
| vxlan_l2proxy | VXLAN L2 proxy support |

---

## Best Practices

1. **Naming Convention**: Use descriptive names like `CVE-YYYY-NNNN_bugNNNNN.patch` for security fixes
2. **Commit Messages**: Include reference links to upstream patches when backporting
3. **Testing**: Always test patches on a clean kernel tree before committing
4. **Order Matters**: Patches are applied in the order listed in the patchlist
5. **Documentation**: Add comments in patch headers explaining the purpose
6. **Version Control**: Keep the patch repository in sync with the main AP repository

---

## Troubleshooting

### Patch Fails to Apply

```bash
# Check for conflicts
git am --3way /path/to/patch.patch

# Or manual resolution
patch -p1 --dry-run < /path/to/patch.patch  # Check what would happen
patch -p1 < /path/to/patch.patch            # Apply
# Fix any rejects manually
```

### Finding Which Patch Introduced a Change

```bash
# In the patch repository
git log --oneline -- path/to/file.c
git blame path/to/file.c
```

### Verifying Patch Application

```bash
# Check if all patches applied successfully
git log --oneline vanilla-5.4..HEAD | wc -l  # Should match patchlist count
```

