# Linux 5.4 Kernel Patch Workflow: Apply, Remove & Reapply

## Executive Summary

This document provides an extensive guide for managing kernel patches applied to `~/linux-5.4`. It covers the complete lifecycle of patch management including application, removal, reapplication, conflict resolution, and best practices specific to the Arista AP build system.

---

## Verified Kernel Analysis (February 2025)

### Current State of ~/linux-5.4

Based on analysis of the actual kernel tree and comparison with fresh blob downloads:

| Property | Value |
|----------|-------|
| **Base Branch** | `NHSS.QSDK.12.5` (Qualcomm SDK) |
| **Base Commit** | `cedcc90e01ee` ("platform: ipq: Update TME_AUTH_EN mask as 0x80") |
| **Current HEAD** | `6eeb8e7cfa67` ("Added custom Flag KMEMLEAK_IGNORE_FALSE_POSITIVES") |
| **Total Patches Applied** | **149 commits** on top of QSDK 12.5 base |
| **Vanilla Tag** | ❌ Does not exist (must be created manually) |

### Patch Breakdown by Source (149 patches)

| Source | Count | Description |
|--------|-------|-------------|
| **Arista (@arista.com)** | **75** | Custom features, CVE fixes, debugging tools |
| **Delta ODM (@deltaww.com)** | **33** | C-430 hardware support, GPIO, LEDs, PHY drivers |
| **Other Upstream Fixes** | **40** | Security backports, Bluetooth, netfilter fixes |
| **Qualcomm (quicinc.com)** | **1** | Minor platform fix |

### Arista Patches Categories

**Custom Features:**
- `bridge_pkt_trace`, `ar_pkt_trace` - Packet tracing
- `l2tif_feature`, `bridge_gatewaymac` - L2 features
- `ar_fips_mode`, `ar_fips_simulate_selftest_error` - FIPS support
- VxLAN L2Proxy, force-fragmentation

**CVE Fixes (14 patches):**
- CVE-2023-4194, CVE-2023-4128, CVE-2023-3611, CVE-2023-35001
- Multiple netfilter, Bluetooth, and scheduler fixes

**Debugging Tools:**
- KMEMLEAK enhancements, KASAN stack support
- Panic logging, skb_corruption detection
- slub/skb debug logging

### Delta ODM Patches (C-430 specific)

- Realtek RTL8251B PHY driver support
- GPS/BT pin configuration on gpio-expander
- TPM chip changes for FIPS 140-3 certification
- LED configuration, RTC driver (rtc-pcf85363)
- SPI NOR and UART settings

### Kernel Blob Comparison (Verified February 2025)

| Property | SPF 12.2 Blob | SPF 12.5 Blob |
|----------|---------------|---------------|
| **SHA256** | `e6d261562a5b330a2bc6353752b92b8b11b4db9254efe97a5eaa2f7ce5ab858d` | `ef3fa4f249c40feb79ac77e7c8a7d59f0ba04146634d5794abcce2376155b8f9` |
| **Size** | 1,930,257,560 bytes (1.8 GB) | 1,956,290,042 bytes (1.8 GB) |
| **Branch** | `NHSS.QSDK.12.2.r6` | `NHSS.QSDK.12.5` |
| **HEAD Commit** | `64bf4136cdf6` | `cedcc90e01ee` |
| **Extracts To** | `linux-5.4/` | `linux-ipq-5.4/` |
| **Total Commits** | 898,696 | 899,342 |
| **Common Ancestor** | `f07d42312bd8` | `f07d42312bd8` |

### ✅ Verified: SPF 12.5 Tarball Matches ~/linux-5.4 Base

**Verification performed on February 5, 2025:**

```
Fresh SPF 12.5 tarball HEAD: cedcc90e01ee429b50bd4bc72f1e6a67269ae12b
~/linux-5.4 NHSS.QSDK.12.5:  cedcc90e01ee429b50bd4bc72f1e6a67269ae12b

✅ MATCH! The fresh SPF 12.5 tarball is IDENTICAL to ~/linux-5.4 base
```

**File comparison:**
- Fresh tarball files: 69,457
- ~/linux-5.4 files: 83,624 (includes build artifacts and patch modifications)
- Kernel version: 5.4.213 (both)

**Conclusion:** The `~/linux-5.4` directory was correctly initialized from the SPF 12.5 kernel blob, and 149 patches have been applied on top of it.

### Creating the Vanilla Tag

Since `vanilla-5.4` tag doesn't exist, create it at the QSDK 12.5 base:

```bash
cd ~/linux-5.4

# Create vanilla tag at the SPF 12.5 base commit
git tag vanilla-5.4 cedcc90e01ee

# Verify - should show 149 patches
git log --oneline vanilla-5.4..HEAD | wc -l

# Alternative: Create descriptive tag
git tag vanilla-5.4-spf12.5 cedcc90e01ee
```

---

## Table of Contents

1. [Verified Kernel Analysis](#verified-kernel-analysis-february-2025)
2. [Overview of the Patch System](#overview-of-the-patch-system)
3. [Patch Hierarchy and Sources](#patch-hierarchy-and-sources)
4. [Initial Setup of ~/linux-5.4](#initial-setup-of-linux-54)
5. [Applying Patches - The Complete Flow](#applying-patches---the-complete-flow)
6. [Removing Patches - Methods and Challenges](#removing-patches---methods-and-challenges)
7. [Reapplying Patches - Rebuilding the Patch Stack](#reapplying-patches---rebuilding-the-patch-stack)
8. [Challenges and Edge Cases](#challenges-and-edge-cases)
9. [Ideal Workflow for Development](#ideal-workflow-for-development)
10. [Automation Scripts](#automation-scripts)
11. [Troubleshooting Guide](#troubleshooting-guide)

---

## Overview of the Patch System

### How Patches Flow in the Build System

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        BUILD SYSTEM PATCH FLOW                          │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  make ap AP=C_460                                                        │
│         │                                                                │
│         ▼                                                                │
│  ┌──────────────────┐                                                    │
│  │ Load config.ap   │ → Sets KERNEL_VERSION=5.4, SPF=12.2               │
│  └────────┬─────────┘                                                    │
│           │                                                              │
│           ▼                                                              │
│  ┌──────────────────────────────────────────────────────────────┐       │
│  │              BLOB DOWNLOAD (generate.mk)                      │       │
│  │  • Read blobs.yaml                                            │       │
│  │  • Download linux-5.4.tar.gz from distwifi server             │       │
│  │  • Verify SHA256: e6d261562a5b330...                          │       │
│  │  • Extract to BLD_DIR                                         │       │
│  └────────┬─────────────────────────────────────────────────────┘       │
│           │                                                              │
│           ▼                                                              │
│  ┌──────────────────────────────────────────────────────────────┐       │
│  │              PATCH APPLICATION (rules_ext.mk)                 │       │
│  │                                                               │       │
│  │  for patch in PATCHES_LIST; do                                │       │
│  │      git am $patch    # For kernel 5.4+ (PATCHES_GIT_AM=1)   │       │
│  │  done                                                         │       │
│  │                                                               │       │
│  │  PATCHES_LIST is assembled from 3 sources (in order):        │       │
│  │  1. Platform patches  → C_460 specific                        │       │
│  │  2. Common patches    → All kernel 5.4 platforms             │       │
│  │  3. SPF patches       → 12.2 specific                        │       │
│  └──────────────────────────────────────────────────────────────┘       │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

### Key Files in the Patch System

| File/Directory | Purpose |
|---------------|---------|
| `blobs.yaml` | Defines kernel source blob locations and SHA256 checksums |
| `src-patches.sh` | Script for applying patches to create patched kernel trees |
| `scripts/rules_ext.mk` | Build system rules for extraction and patch application |
| `scripts/download_kernel.sh` | Helper script to download kernel and optionally apply patches |
| `ap/platform/cvendors/QCA/SPF/12.2/src/kernel/Makefile.sdk` | Kernel build configuration including patch list assembly |

---

## Patch Hierarchy and Sources

The patch system uses a **3-tier hierarchy** to organize patches by scope:

```
ap/platform/
├── patches/kernel/5.4/
│   ├── common/                         # TIER 1: All 5.4 platforms
│   │   ├── CVE-*.patch                 # Security patches
│   │   ├── bridge_gwmac.patch          # Feature patches
│   │   ├── vxlan_*.patch               # VXLAN improvements
│   │   └── ... (107 patches)
│   │
│   ├── 12.2/                           # TIER 2: SPF 12.2 specific
│   │   ├── common/                     # All boards on SPF 12.2
│   │   │   ├── l2tif_feature_12_2.patch
│   │   │   ├── hairpin_mode_12_2.patch
│   │   │   └── ... (10 patches)
│   │   ├── C_460/                      # TIER 3: C_460 specific
│   │   │   ├── C460_DELTA_*.patch      # Board-specific DTS patches
│   │   │   └── ... (18 patches)
│   │   └── O_435/                      # TIER 3: O_435 specific
│   │
│   └── 12.5/                           # TIER 2: SPF 12.5 specific
│       ├── common/
│       ├── C_400/
│       └── C_430/
│
└── cvendors/QCA/
    ├── kernel/5.4/patchlists/
    │   └── kernel_patchlist            # Lists patches from common/
    │
    ├── SPF/12.2/patchlists/
    │   └── kernel_patchlist            # Lists patches from 12.2/common/
    │
    └── boards/C_460/SPF/12.2/patchlists/
        └── kernel_patchlist            # Lists patches from 12.2/C_460/
```

### Patchlist Format

Patchlists are simple text files, one patch filename per line:

```text
# ap/platform/cvendors/QCA/kernel/5.4/patchlists/kernel_patchlist
max_akm_suite_update.patch
increase_custom_event_size.patch
content_analytic_support.patch
CVE-2023-1206_bug835295.patch
...
```

### Patch File Format (git format-patch)

All patches for kernel 5.4+ MUST be in git format-patch format:

```diff
From abc123def456789 Mon Sep 17 00:00:00 2001
From: Developer Name <dev@example.com>
Date: Tue, 5 Dec 2023 10:30:00 -0800
Subject: [PATCH] net: bridge: Fix gateway MAC assignment

Description of the change and why it's needed.
Reference: BUG-123456
Upstream: https://git.kernel.org/...

---
 net/bridge/br_input.c | 15 +++++++++------
 1 file changed, 9 insertions(+), 6 deletions(-)

diff --git a/net/bridge/br_input.c b/net/bridge/br_input.c
...
```

---

## Initial Setup of ~/linux-5.4

### Method 1: Using the Download Script (Recommended)

```bash
# Download kernel and initialize git repo
./scripts/download_kernel.sh --spf 12.2 --output ~/ --git-init

# Result: ~/linux-5.4 with git initialized, tagged vanilla-5.4-spf12.2
```

### Method 2: Manual Setup

```bash
# Step 1: Download the kernel blob
DIST_WIFI_BASE="http://distwifi.pune.aristanetworks.com/storage/bin"
KERNEL_BLOB="linux-5.4.tar.gz.e6d261562a5b330a2bc6353752b92b8b11b4db9254efe97a5eaa2f7ce5ab858d"

mkdir -p ~/linux-5.4
curl -L "${DIST_WIFI_BASE}/${KERNEL_BLOB}" | tar -xzf - -C ~/linux-5.4 --strip-components=1

# Step 2: Verify extraction
ls ~/linux-5.4/Makefile  # Should exist

# Step 3: Initialize git repository (CRITICAL for patch management)
cd ~/linux-5.4
git init
git add -A
git commit -m "Initial import: Linux 5.4 from SPF 12.2"
git tag vanilla-5.4

# Step 4: Create development branch
git checkout -b arista-patches
```

### Method 3: Using src-patches.sh (For OpenGrok/CI)

```bash
# Creates patched trees for all APs in ap/src/kernels/
./src-patches.sh /path/to/ap-repo
# Result: ap/src/kernels/C_460_linux_5.4/, etc.
```

**⚠️ CRITICAL: Always initialize a git repository before applying patches!**

Without git:
- Cannot use `git am` for patch application
- Cannot track which patches are applied
- Cannot easily remove or reorder patches
- Lose all git history and bisection capability

---

## Applying Patches - The Complete Flow

### Patch Application Order

Patches are applied in a specific order defined by the patchlists. For C_460:

```
TOTAL PATCHES ≈ 135 patches applied in this order:

1. Platform patches (C_460 specific)      → 18 patches
2. Common patches (all 5.4)               → 107 patches
3. SPF patches (12.2 common)              → 10 patches
```

### Step-by-Step Application Process

```bash
#!/bin/bash
# apply_all_patches.sh - Apply all patches for a specific AP

AP_MODEL="${1:-C_460}"
SPF="${2:-12.2}"
KERNEL_VERSION="5.4"
LINUX_PATH="$HOME/linux-5.4"
REPO_ROOT="/path/to/ap-repo"

# Ensure we're on clean branch
cd "$LINUX_PATH"
git checkout arista-patches 2>/dev/null || git checkout -b arista-patches

# Define patch directories and lists
PLATFORM_BASE="$REPO_ROOT/ap/platform"
PATCH_BASE="$PLATFORM_BASE/patches/kernel/$KERNEL_VERSION"

# Source patchlists
COMMON_PATCHLIST="$PLATFORM_BASE/cvendors/QCA/kernel/$KERNEL_VERSION/patchlists/kernel_patchlist"
SPF_PATCHLIST="$PLATFORM_BASE/cvendors/QCA/SPF/$SPF/patchlists/kernel_patchlist"
PLATFORM_PATCHLIST="$PLATFORM_BASE/cvendors/QCA/boards/$AP_MODEL/SPF/$SPF/patchlists/kernel_patchlist"

# Apply in order: Platform → Common → SPF
apply_patches() {
    local patchlist="$1"
    local patchdir="$2"

    while read -r patch_name; do
        [[ -z "$patch_name" || "$patch_name" =~ ^# ]] && continue

        PATCH_FILE="$patchdir/$patch_name"
        if [[ -f "$PATCH_FILE" ]]; then
            echo "Applying: $patch_name"
            git am "$PATCH_FILE" || {
                echo "FAILED: $patch_name - attempting 3-way merge..."
                git am --abort 2>/dev/null
                git am --3way "$PATCH_FILE" || {
                    echo "ERROR: Cannot apply $patch_name"
                    return 1
                }
            }
        else
            echo "WARNING: Patch not found: $PATCH_FILE"
        fi
    done < "$patchlist"
}

# Apply patches in correct order
echo "=== Applying Platform Patches ($AP_MODEL) ==="
apply_patches "$PLATFORM_PATCHLIST" "$PATCH_BASE/$SPF/$AP_MODEL"

echo "=== Applying Common Patches ==="
apply_patches "$COMMON_PATCHLIST" "$PATCH_BASE/common"

echo "=== Applying SPF Patches ($SPF) ==="
apply_patches "$SPF_PATCHLIST" "$PATCH_BASE/$SPF/common"

echo "=== Done! $(git rev-list vanilla-5.4..HEAD --count) patches applied ==="
```

### Using the Build System (Automatic)

The build system handles this automatically when you run:

```bash
make ap AP=C_460
```

Key makefile variables:
- `PATCHES_GIT_AM=1` - Use git am instead of patch command
- `PATCHES_DEPTH=1` - Strip 1 directory component (-p1)
- `PATCHES_LIST` - Combined list of all patch files

---

## Removing Patches - Methods and Challenges

### Removing ALL Pre-Applied Patches (Complete Reset)

When you need to start fresh and remove all patches that have been applied to your kernel tree.

#### First: Check if vanilla-5.4 Tag Exists

```bash
cd ~/linux-5.4

# Check for vanilla tag
git tag -l "vanilla*"

# If empty, the tag doesn't exist - see "Creating a Vanilla Tag" below
```

#### Creating a Vanilla Tag (If Missing)

If your kernel tree was extracted without creating a vanilla tag, you have several options:

**Option 1: Find the Base Commit (Recommended)**

```bash
cd ~/linux-5.4

# Look for the initial import or first commit
git log --oneline --reverse | head -5

# Or find where Arista patches start
git log --oneline --grep="Arista" | tail -1
git log --oneline --grep="CVE-" | tail -1
git log --oneline --grep="ar_" | tail -1

# The commit BEFORE the first Arista patch is your vanilla base
# Example: If first Arista patch is abc1234, find its parent:
git log --oneline abc1234^..abc1234
git rev-parse abc1234^  # Get parent commit

# Create the vanilla tag at that commit
git tag vanilla-5.4 <parent-commit-hash>
```

**Option 2: Use Qualcomm SDK Branch as Base**

If your kernel came from Qualcomm SPF (like NHSS.QSDK.12.5):

```bash
cd ~/linux-5.4

# Check for SDK branch
git branch -a | grep -i qsdk

# If NHSS.QSDK.12.5 exists, find where it diverges from HEAD
git merge-base HEAD NHSS.QSDK.12.5

# Create vanilla tag at that point
git tag vanilla-5.4 $(git merge-base HEAD NHSS.QSDK.12.5)
```

**Option 3: Re-extract Fresh Kernel (Most Reliable)**

```bash
# Remove existing and start fresh
rm -rf ~/linux-5.4

# Use download script with --git-init to create proper vanilla tag
./scripts/download_kernel.sh --spf 12.2 --output ~/ --git-init

# This creates vanilla-5.4-spf12.2 tag automatically
```

**Option 4: Count Patches and Reset by Number**

If you know how many patches were applied:

```bash
cd ~/linux-5.4

# Count Arista-related commits
git log --oneline --grep="CVE-\|Arista\|ar_\|bridge_\|vxlan_" | wc -l

# Reset back N commits (replace N with count)
git tag vanilla-5.4 HEAD~N
```

---

#### Method A: Git Reset to Vanilla Tag (Fastest)

**Prerequisites:** `vanilla-5.4` tag must exist (see above)

```bash
cd ~/linux-5.4

# Check current state
git log --oneline vanilla-5.4..HEAD | head -5
# Shows: 135 patches applied

# Hard reset to vanilla (DESTROYS all local changes)
git reset --hard vanilla-5.4

# Verify clean state
git log --oneline -1
# Output: abc1234 Initial import: Linux 5.4 from SPF 12.2

# Recreate development branch
git checkout -b arista-patches-clean
```

**⚠️ WARNING:** This permanently discards ALL uncommitted changes and ALL patches.

#### Method B: Create New Branch from Vanilla (Preserves Old Branch)

```bash
cd ~/linux-5.4

# Keep the old patched branch for reference
git branch arista-patches-backup

# Create fresh branch from vanilla
git checkout vanilla-5.4
git checkout -b arista-patches-fresh

# Old patches still available in backup branch
git log --oneline arista-patches-backup | head -5
```

#### Method C: Interactive Rebase to Remove All (Selective)

```bash
cd ~/linux-5.4

# Start interactive rebase from vanilla
git rebase -i vanilla-5.4

# In the editor, delete ALL lines (or change 'pick' to 'd' for delete)
# Save and exit

# Result: Empty branch at vanilla-5.4 level
```

#### Method D: Complete Re-extraction (Nuclear Option)

When git state is corrupted or you want a guaranteed clean slate:

```bash
# Remove existing directory
rm -rf ~/linux-5.4

# Re-download and extract
./scripts/download_kernel.sh --spf 12.2 --output ~/ --git-init

# Result: Fresh ~/linux-5.4 with only vanilla-5.4 tag, no patches
```

#### Method E: Using the Build System (For Build Directory)

The build system extracts fresh kernel for each clean build:

```bash
cd /path/to/ap-repo

# Clean the kernel build directory
make clean AP=C_460

# Or specifically clean kernel module
make -C ap/scripts kernel_clean AP=C_460

# Next build will extract fresh kernel and reapply patches
make ap AP=C_460
```

#### Complete Reset Script

```bash
#!/bin/bash
# reset_kernel_patches.sh - Remove all patches and optionally reapply

LINUX_PATH="${1:-$HOME/linux-5.4}"
REAPPLY="${2:-no}"  # Pass "yes" to reapply after reset

cd "$LINUX_PATH" || { echo "ERROR: $LINUX_PATH not found"; exit 1; }

# Verify we're in a git repo with vanilla tag
if ! git rev-parse vanilla-5.4 >/dev/null 2>&1; then
    echo "ERROR: vanilla-5.4 tag not found. Is this a properly initialized kernel tree?"
    exit 1
fi

# Count current patches
PATCH_COUNT=$(git rev-list vanilla-5.4..HEAD --count 2>/dev/null || echo "0")
echo "Current state: $PATCH_COUNT patches applied"

# Backup current branch name
CURRENT_BRANCH=$(git rev-parse --abbrev-ref HEAD)

# Check for uncommitted changes
if ! git diff-index --quiet HEAD --; then
    echo "WARNING: Uncommitted changes detected!"
    read -p "Discard all changes? (yes/no): " CONFIRM
    [[ "$CONFIRM" != "yes" ]] && exit 1
fi

# Perform reset
echo "Resetting to vanilla-5.4..."
git reset --hard vanilla-5.4

echo "All $PATCH_COUNT patches removed."
echo ""

# Optionally reapply
if [[ "$REAPPLY" == "yes" ]]; then
    echo "Reapplying patches..."
    # Source your apply script here
    # ./apply_all_patches.sh C_460 12.2
    echo "Reapply requested - run your patch application script"
fi

echo "Done! Kernel is now at vanilla state."
git log --oneline -1
```

#### Verification After Reset

```bash
cd ~/linux-5.4

# Verify no patches applied
git rev-list vanilla-5.4..HEAD --count
# Output: 0

# Verify at correct commit
git describe --tags
# Output: vanilla-5.4

# Verify working tree is clean
git status
# Output: nothing to commit, working tree clean

# Verify key files are vanilla (no Arista modifications)
grep -q "ARISTA" drivers/net/ethernet/qualcomm/Makefile && \
    echo "WARNING: Still has Arista changes" || \
    echo "OK: Vanilla state confirmed"
```

#### Flow Diagram: Complete Patch Removal

```
┌─────────────────────────────────────────────────────────────────┐
│                    REMOVE ALL PATCHES FLOW                       │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Current State: 135 patches applied on arista-patches branch    │
│                                                                  │
│  Step 1: Backup (Optional)                                       │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │ git branch arista-patches-backup                         │    │
│  └─────────────────────────────────────────────────────────┘    │
│                          │                                       │
│                          ▼                                       │
│  Step 2: Reset to Vanilla                                        │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │ git reset --hard vanilla-5.4                             │    │
│  │                                                          │    │
│  │ OR (preserving branch):                                  │    │
│  │ git checkout vanilla-5.4                                 │    │
│  │ git checkout -b arista-patches-clean                     │    │
│  └─────────────────────────────────────────────────────────┘    │
│                          │                                       │
│                          ▼                                       │
│  Step 3: Verify Clean State                                      │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │ git rev-list vanilla-5.4..HEAD --count                   │    │
│  │ # Output: 0                                              │    │
│  └─────────────────────────────────────────────────────────┘    │
│                          │                                       │
│                          ▼                                       │
│  Step 4: Ready for Fresh Patch Application                       │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │ ./apply_all_patches.sh C_460 12.2                        │    │
│  │ # Applies 135 patches fresh                              │    │
│  └─────────────────────────────────────────────────────────┘    │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

### Method 1: Remove Single Patch with git revert (Safe)

```bash
cd ~/linux-5.4

# Find the commit for the patch you want to remove
git log --oneline --grep="CVE-2023-1206"
# Output: abc1234 CVE-2023-1206_bug835295

# Revert it (creates a new commit)
git revert abc1234

# Note: This keeps history intact but adds a revert commit
```

**Pros:** Safe, preserves history, easy to undo
**Cons:** Creates additional commits, patch is still in history

### Method 2: Interactive Rebase to Remove Patch (Clean but Risky)

```bash
cd ~/linux-5.4

# Find vanilla tag (base)
git log --oneline vanilla-5.4..HEAD | wc -l  # Shows N patches

# Interactive rebase from vanilla
git rebase -i vanilla-5.4

# In editor, delete or comment the line for the patch to remove:
# pick abc1234 CVE-2023-1206_bug835295  <- DELETE THIS LINE

# Save and exit - git will replay remaining patches
```

**Pros:** Clean history, patch completely removed
**Cons:** Rewrites history, may cause conflicts, breaks shared branches

### Method 3: Reset and Reapply (Nuclear Option)

```bash
cd ~/linux-5.4

# Go back to vanilla
git checkout vanilla-5.4
git checkout -B arista-patches  # Reset branch

# Modify patchlist to exclude the patch
# Then reapply all patches (see apply script above)
```

**Pros:** Guaranteed clean state
**Cons:** Time-consuming, loses any local modifications

### Removing from the Build System

To permanently remove a patch from the build:

```bash
# Step 1: Remove from patchlist
vim ap/platform/cvendors/QCA/kernel/5.4/patchlists/kernel_patchlist
# Delete the line containing the patch name

# Step 2: (Optional) Delete the patch file
rm ap/platform/patches/kernel/5.4/common/CVE-2023-1206_bug835295.patch

# Step 3: Clean and rebuild
make clean AP=C_460
make ap AP=C_460
```

---

## Reapplying Patches - Rebuilding the Patch Stack

### Scenario 1: Fresh Reapplication After Modification

```bash
cd ~/linux-5.4

# Reset to vanilla
git reset --hard vanilla-5.4

# Create fresh branch
git checkout -b arista-patches-v2

# Reapply all patches with the modified patchlist
./apply_all_patches.sh C_460 12.2
```

### Scenario 2: Reapply After Conflict Resolution

When a patch fails to apply:

```bash
# Attempt to apply
git am /path/to/problem-patch.patch

# If it fails:
# error: patch failed: drivers/net/some_file.c:123
# Patch failed at 0001 description

# Option A: 3-way merge
git am --3way /path/to/problem-patch.patch

# Option B: Manual resolution
git am --reject /path/to/problem-patch.patch
# Edit files to apply changes from .rej files
git add .
git am --continue

# Option C: Skip this patch
git am --skip
```

### Scenario 3: Regenerating Patches After Modifications

If you've made changes to the kernel and need to update patches:

```bash
cd ~/linux-5.4

# Ensure all changes are committed
git add .
git commit -m "Fix issue in bridge_gwmac"

# Regenerate all patches from vanilla
git format-patch vanilla-5.4..HEAD -o /tmp/new-patches/

# Replace old patches (be careful!)
cp /tmp/new-patches/*.patch /path/to/ap/platform/patches/kernel/5.4/common/

# Update patchlist with new filenames (git format-patch adds number prefixes)
ls /tmp/new-patches/*.patch | xargs -n1 basename > /path/to/patchlist
```

### Scenario 4: Rebasing Patches on New Kernel Base

When the SPF provides a new kernel tarball:

```bash
# Download and extract new kernel
./scripts/download_kernel.sh --spf 12.2 --output ~/linux-5.4-new --git-init

cd ~/linux-5.4-new

# Create patches branch
git checkout -b arista-patches

# Try to apply existing patches
for patch in $(cat /path/to/kernel_patchlist); do
    git am /path/to/patches/common/$patch || {
        echo "Conflict in: $patch"
        # Resolve manually or skip
        git am --3way || git am --skip
    }
done

# After resolving all conflicts, regenerate patches
git format-patch vanilla-5.4..HEAD -o /path/to/patches/common/
```

---

## Challenges and Edge Cases

### Challenge 1: Patch Order Dependencies

**Problem:** Patch B depends on changes made by Patch A. Removing A breaks B.

```
Patch A: Adds function foo_helper()
Patch B: Calls foo_helper()
Removing A → Patch B fails: undefined reference to foo_helper
```

**Solution:**
1. Identify dependencies using git log:
   ```bash
   git log --oneline --all --source -- path/to/file.c
   ```
2. Remove dependent patches in reverse order
3. Or merge dependent patches into one

### Challenge 2: Context Drift

**Problem:** Patches fail because surrounding code has changed.

```
Patch expects:          Actual code:
---                     ---
int old_function() {    int old_function() {
    do_something();         do_something();
    // line to change       new_line();        <- NEW
    return 0;               // line to change
}                           return 0;
                        }
```

**Solutions:**
- Use `git am --3way` for intelligent merging
- Use `--ignore-whitespace` for whitespace issues
- Regenerate patch with updated context

### Challenge 3: Conflicting Patches

**Problem:** Two patches modify the same lines differently.

**Solution:**
```bash
# Apply first patch
git am patch_a.patch

# Apply second patch - will conflict
git am patch_b.patch  # FAILS

# Resolve conflict
git am --3way patch_b.patch  # Try 3-way
# If still fails:
git am --reject patch_b.patch
# Manually merge changes from .rej files
vim path/to/file.c
git add path/to/file.c
git am --continue
```

### Challenge 4: Platform-Specific vs Common Patches

**Problem:** A fix is needed for one platform but breaks another.

**Best Practice:**
1. If fix is universal → Add to common patches
2. If fix is SPF-specific → Add to SPF patches
3. If fix is board-specific → Add to platform patches

```
Board-specific:  ap/platform/patches/kernel/5.4/12.2/C_460/my-fix.patch
SPF-specific:    ap/platform/patches/kernel/5.4/12.2/common/my-fix.patch
Universal:       ap/platform/patches/kernel/5.4/common/my-fix.patch
```

### Challenge 5: Binary Blobs in Patches

**Problem:** Kernel includes some binary files that can't be patched.

**Solution:** These are typically handled by the SPF tarball, not patches.

### Challenge 6: Maintaining Upstream References

**Problem:** Tracking which patches come from upstream Linux.

**Best Practice:** Include upstream commit info in patch header:
```
Subject: [PATCH] net: fix NULL pointer dereference

Backported from upstream:
commit abc123def456 in torvalds/linux
Link: https://git.kernel.org/pub/scm/linux/kernel/git/torvalds/linux.git/commit/?id=abc123
CVE: CVE-2023-XXXX
BUG: 123456
```

---

## Ideal Workflow for Development

### Recommended Git Branch Structure

```
                         vanilla-5.4 (tag)
                              │
                              ▼
           ┌──────────────────┴───────────────────┐
           │                                      │
           ▼                                      ▼
    arista-patches                          feature-branch
    (all patches applied)                   (for development)
           │                                      │
           │                                      ▼
           │                              ┌───────────────┐
           │                              │ Make changes  │
           │                              │ Test locally  │
           │                              │ Commit        │
           │                              └───────┬───────┘
           │                                      │
           │◄─────────────────────────────────────┘
           │         (cherry-pick or merge)
           ▼
    Generate new patch
    with git format-patch
```

### Ideal Development Workflow

```bash
# === SETUP PHASE ===

# 1. Clone the AP repository
git clone <ap-repo-url>
cd ap

# 2. Download and prepare kernel
./scripts/download_kernel.sh --spf 12.2 --output ~/ --git-init

# 3. Apply all existing patches
cd ~/linux-5.4
./apply_all_patches.sh C_460 12.2

# 4. Create feature branch for development
git checkout -b feature/my-fix

# === DEVELOPMENT PHASE ===

# 5. Make your changes
vim drivers/net/bridge/br_input.c

# 6. Test build (link to AP build system)
export KERNEL_SRC=~/linux-5.4
make -C /path/to/ap ap AP=C_460

# 7. Commit changes with proper message
git add drivers/net/bridge/br_input.c
git commit -m "net: bridge: Fix gateway MAC race condition

The bridge driver had a race condition when assigning gateway MAC
addresses. This fix adds proper locking around the assignment.

BUG: 123456
Tested: C_460, O_435
"

# === EXPORT PHASE ===

# 8. Generate patch
git format-patch -1 HEAD -o /tmp/patches/
# Output: /tmp/patches/0001-net-bridge-Fix-gateway-MAC-race-condition.patch

# 9. Rename to follow naming convention
mv /tmp/patches/0001-*.patch /path/to/ap/platform/patches/kernel/5.4/common/bridge_gwmac_race_fix.patch

# 10. Add to patchlist
echo "bridge_gwmac_race_fix.patch" >> /path/to/ap/platform/cvendors/QCA/kernel/5.4/patchlists/kernel_patchlist

# 11. Test full build
cd /path/to/ap
make clean AP=C_460
make ap AP=C_460

# === COMMIT PHASE ===

# 12. Commit to AP repo
git add ap/platform/patches/kernel/5.4/common/bridge_gwmac_race_fix.patch
git add ap/platform/cvendors/QCA/kernel/5.4/patchlists/kernel_patchlist
git commit -m "kernel: Add bridge gateway MAC race fix"
```

### Quick Reference: Common Operations

| Task | Command |
|------|---------|
| Check applied patches count | `git rev-list vanilla-5.4..HEAD --count` |
| List applied patches | `git log --oneline vanilla-5.4..HEAD` |
| Find patch for a file | `git log --oneline -- path/to/file.c` |
| Check if patch applies | `git am --dry-run /path/to/patch.patch` |
| Apply with 3-way merge | `git am --3way /path/to/patch.patch` |
| Abort failed apply | `git am --abort` |
| Skip problematic patch | `git am --skip` |
| Generate patch from commit | `git format-patch -1 HEAD` |
| Find conflicts | `git diff --check` |
| Reset to vanilla | `git reset --hard vanilla-5.4` |

---

## Automation Scripts

### Script: Validate All Patches Apply Cleanly

```bash
#!/bin/bash
# validate_patches.sh - Ensure all patches apply without conflicts

set -e

REPO_ROOT="${1:-.}"
SPF="${2:-12.2}"
KERNEL_VERSION="5.4"

PATCH_BASE="$REPO_ROOT/ap/platform/patches/kernel/$KERNEL_VERSION"
PATCHLIST_BASE="$REPO_ROOT/ap/platform/cvendors/QCA"

# Create temp directory
TEMP_DIR=$(mktemp -d)
trap "rm -rf $TEMP_DIR" EXIT

echo "Downloading kernel..."
$REPO_ROOT/scripts/download_kernel.sh --spf $SPF --output $TEMP_DIR --git-init

cd "$TEMP_DIR/linux-$KERNEL_VERSION"

echo "Testing patch application..."
FAILED=0

# Test common patches
while read -r patch; do
    [[ -z "$patch" || "$patch" =~ ^# ]] && continue
    PATCH_FILE="$PATCH_BASE/common/$patch"

    if ! git am --dry-run "$PATCH_FILE" 2>/dev/null; then
        echo "FAIL: $patch"
        ((FAILED++))
    else
        echo "OK: $patch"
    fi
done < "$PATCHLIST_BASE/kernel/$KERNEL_VERSION/patchlists/kernel_patchlist"

echo ""
echo "=== Results: $FAILED patches failed ==="
exit $FAILED
```

### Script: Generate Patch Summary Report

```bash
#!/bin/bash
# patch_report.sh - Generate summary of all kernel patches

REPO_ROOT="${1:-.}"
KERNEL_VERSION="5.4"
PATCH_BASE="$REPO_ROOT/ap/platform/patches/kernel/$KERNEL_VERSION"

echo "# Kernel $KERNEL_VERSION Patch Summary"
echo "Generated: $(date)"
echo ""

for dir in "$PATCH_BASE"/common "$PATCH_BASE"/*/common "$PATCH_BASE"/*/*; do
    [[ -d "$dir" ]] || continue

    CVE_COUNT=$(ls "$dir"/CVE-*.patch 2>/dev/null | wc -l)
    FEATURE_COUNT=$(ls "$dir"/*.patch 2>/dev/null | wc -l)
    FEATURE_COUNT=$((FEATURE_COUNT - CVE_COUNT))

    echo "## ${dir#$PATCH_BASE/}"
    echo "- CVE patches: $CVE_COUNT"
    echo "- Feature patches: $FEATURE_COUNT"
    echo ""
done
```

### Script: Sync Kernel Dev Tree with AP Repo

```bash
#!/bin/bash
# sync_patches.sh - Export patches from dev tree to AP repo

LINUX_PATH="$HOME/linux-5.4"
REPO_ROOT="${1:-.}"
SPF="${2:-12.2}"
KERNEL_VERSION="5.4"

cd "$LINUX_PATH"

# Determine patch destination based on current context
# This is a simplified version - in practice you might want more logic
PATCH_DIR="$REPO_ROOT/ap/platform/patches/kernel/$KERNEL_VERSION/common"

echo "Regenerating patches from $LINUX_PATH"
echo "Destination: $PATCH_DIR"

# Backup existing patches
BACKUP_DIR="$PATCH_DIR.backup.$(date +%Y%m%d%H%M%S)"
cp -r "$PATCH_DIR" "$BACKUP_DIR"

# Generate fresh patches
rm -f "$PATCH_DIR"/*.patch
git format-patch vanilla-5.4..HEAD -o "$PATCH_DIR" --no-numbered

# Generate new patchlist
ls "$PATCH_DIR"/*.patch | xargs -n1 basename | sort > \
    "$REPO_ROOT/ap/platform/cvendors/QCA/kernel/$KERNEL_VERSION/patchlists/kernel_patchlist"

echo "Done! Backup saved to: $BACKUP_DIR"
```

---

## Troubleshooting Guide

### Error: "Patch does not apply"

```
error: patch failed: drivers/net/file.c:123
error: drivers/net/file.c: patch does not apply
Patch failed at 0001 Subject line here
```

**Solutions:**
1. Try 3-way merge: `git am --3way patch.patch`
2. Check for whitespace issues: `git am --ignore-whitespace patch.patch`
3. Manual application:
   ```bash
   git am --reject patch.patch
   # Edit files based on .rej files
   git add .
   git am --continue
   ```

### Error: "Previous rebase directory exists"

```
error: .git/rebase-apply already exists
```

**Solution:**
```bash
git am --abort
# or
rm -rf .git/rebase-apply
```

### Error: "Not a git repository"

```
fatal: not a git repository
```

**Solution:**
```bash
cd ~/linux-5.4
git init
git add -A
git commit -m "Initial import"
git tag vanilla-5.4
```

### Error: "Patch format detection failed"

```
Patch format detection failed.
```

**Solution:** The patch is not in git format-patch format. Convert it:
```bash
# If it's a unified diff, you can apply with patch command
patch -p1 < legacy.patch

# Then create proper git patch
git add -A
git commit -m "Applied legacy patch"
git format-patch -1 HEAD -o /tmp/
```

### Error: "Binary files differ"

```
error: cannot apply binary patch to 'path/to/file.bin'
```

**Solution:** Binary files cannot be patched. Options:
1. Exclude from patch
2. Use git-lfs for binary handling
3. Distribute binary separately

### Checking Patch Application Status

```bash
# See what patches have been applied
git log --oneline vanilla-5.4..HEAD

# Compare expected vs actual
EXPECTED=$(wc -l < /path/to/kernel_patchlist)
ACTUAL=$(git rev-list vanilla-5.4..HEAD --count)
echo "Expected: $EXPECTED, Applied: $ACTUAL"

# Find specific patch
git log --oneline --grep="CVE-2023"
```

---

## Best Practices Summary

1. **Always work in a git repository** - Initialize with `git init` before any patches
2. **Tag the vanilla kernel** - Use `vanilla-5.4` as base reference
3. **Use feature branches** - Develop on branches, merge to arista-patches
4. **Follow naming conventions:**
   - CVE fixes: `CVE-YYYY-NNNNN_bugNNNNNN.patch`
   - Features: `descriptive_name.patch`
   - Platform-specific: `PLATFORM_description.patch`
5. **Include metadata in patches:**
   - BUG reference
   - CVE ID if applicable
   - Upstream commit link if backporting
   - Test platforms
6. **Test before committing:**
   - `git am --dry-run` to verify patch applies
   - Full build test
   - Runtime test on target hardware
7. **Keep patches small and focused** - One logical change per patch
8. **Document dependencies** - Note when patch B requires patch A
9. **Regenerate after modifications** - Use `git format-patch` to update

---

## Appendix: Patch Application Matrix

| AP Model | Kernel | SPF | Common Patches | SPF Patches | Platform Patches |
|----------|--------|-----|----------------|-------------|------------------|
| C_460 | 5.4 | 12.2 | 107 | 10 | 18 |
| O_435 | 5.4 | 12.2 | 107 | 10 | ~15 |
| C_400 | 5.4 | 12.5 | 107 | ~12 | ~20 |
| C_430 | 5.4 | 12.5 | 107 | ~12 | ~18 |
| C_330 | 4.4 | 11.4 | ~60 | N/A | N/A |
| C_360 | 4.4 | 11.4 | ~60 | N/A | N/A |

**Note:** Kernel 4.4 platforms use `patch -p1` instead of `git am`, and have a flat patch structure.

---

## Related Documentation

- [docs/kernel-patch-management.md](kernel-patch-management.md) - Build system integration details
- [scripts/download_kernel.sh](../scripts/download_kernel.sh) - Kernel download helper
- [src-patches.sh](../src-patches.sh) - OpenGrok patch application script

