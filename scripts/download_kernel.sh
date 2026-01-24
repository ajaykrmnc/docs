#!/usr/bin/env bash
# Copyright (c) 2025 Arista Networks, Inc.  All rights reserved.
# Arista Networks, Inc. Confidential and Proprietary.
#
# Script to download Linux kernel source and optionally set up a patch management repository.
#
# Usage:
#   ./scripts/download_kernel.sh [OPTIONS]
#
# Options:
#   -s, --spf VERSION    SPF version (12.2 or 12.5). Default: 12.2
#   -o, --output DIR     Output directory. Default: current directory
#   -p, --apply-patches  Apply existing patches after extraction
#   -g, --git-init       Initialize git repo for patch management
#   -h, --help           Show this help message

set -euo pipefail

# Default values
SPF_VERSION="12.2"
OUTPUT_DIR="."
APPLY_PATCHES=false
GIT_INIT=false

TOPDIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DIST_WIFI_BASE="http://distwifi.pune.aristanetworks.com/storage/bin"
BLOBS_YAML="$TOPDIR/blobs.yaml"

# Kernel blob info from blobs.yaml
declare -A KERNEL_BLOBS=(
    ["12.2"]="linux-5.4.tar.gz.e6d261562a5b330a2bc6353752b92b8b11b4db9254efe97a5eaa2f7ce5ab858d"
    ["12.5"]="linux-5.4.tar.gz.ef3fa4f249c40feb79ac77e7c8a7d59f0ba04146634d5794abcce2376155b8f9"
)

declare -A KERNEL_SHASUMS=(
    ["12.2"]="e6d261562a5b330a2bc6353752b92b8b11b4db9254efe97a5eaa2f7ce5ab858d"
    ["12.5"]="ef3fa4f249c40feb79ac77e7c8a7d59f0ba04146634d5794abcce2376155b8f9"
)

usage() {
    head -20 "$0" | tail -15
    exit 0
}

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*"
}

error() {
    echo "[ERROR] $*" >&2
    exit 1
}

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -s|--spf)
            SPF_VERSION="$2"
            shift 2
            ;;
        -o|--output)
            OUTPUT_DIR="$2"
            shift 2
            ;;
        -p|--apply-patches)
            APPLY_PATCHES=true
            shift
            ;;
        -g|--git-init)
            GIT_INIT=true
            shift
            ;;
        -h|--help)
            usage
            ;;
        *)
            error "Unknown option: $1"
            ;;
    esac
done

# Validate SPF version
if [[ ! -v "KERNEL_BLOBS[$SPF_VERSION]" ]]; then
    error "Invalid SPF version: $SPF_VERSION. Supported: ${!KERNEL_BLOBS[*]}"
fi

KERNEL_BLOB="${KERNEL_BLOBS[$SPF_VERSION]}"
KERNEL_SHASUM="${KERNEL_SHASUMS[$SPF_VERSION]}"
KERNEL_VERSION="5.4"
KERNEL_TARBALL="linux-${KERNEL_VERSION}.tar.gz"
KERNEL_DIR="linux-${KERNEL_VERSION}"

# Create output directory
mkdir -p "$OUTPUT_DIR"
cd "$OUTPUT_DIR"

log "Downloading Linux $KERNEL_VERSION kernel for SPF $SPF_VERSION..."

# Download kernel
if [[ -f "$KERNEL_TARBALL" ]]; then
    log "Kernel tarball already exists, verifying checksum..."
    if echo "$KERNEL_SHASUM  $KERNEL_TARBALL" | sha256sum -c --quiet 2>/dev/null; then
        log "Checksum verified, skipping download."
    else
        log "Checksum mismatch, re-downloading..."
        rm -f "$KERNEL_TARBALL"
        curl -L -o "$KERNEL_TARBALL" "${DIST_WIFI_BASE}/${KERNEL_BLOB}" || \
            error "Failed to download kernel. Are you on the internal network?"
    fi
else
    curl -L -o "$KERNEL_TARBALL" "${DIST_WIFI_BASE}/${KERNEL_BLOB}" || \
        error "Failed to download kernel. Are you on the internal network?"
fi

# Verify checksum
log "Verifying checksum..."
echo "$KERNEL_SHASUM  $KERNEL_TARBALL" | sha256sum -c || \
    error "Checksum verification failed!"

# Extract kernel
log "Extracting kernel to $KERNEL_DIR..."
rm -rf "$KERNEL_DIR"
mkdir -p "$KERNEL_DIR"
tar -xzf "$KERNEL_TARBALL" -C "$KERNEL_DIR" --strip-components=1

# Initialize git repo if requested
if $GIT_INIT; then
    log "Initializing git repository..."
    cd "$KERNEL_DIR"
    git init
    git add -A
    git commit -m "Initial import: Linux $KERNEL_VERSION from SPF $SPF_VERSION"
    git tag "vanilla-${KERNEL_VERSION}-spf${SPF_VERSION}"
    cd ..
fi

# Apply patches if requested
if $APPLY_PATCHES; then
    log "Applying patches..."
    PLATFORM_BASE="$TOPDIR/ap/platform"
    COMMON_PATCHLIST="$TOPDIR/ap/platform/cvendors/QCA/kernel/$KERNEL_VERSION/patchlists/kernel_patchlist"
    COMMON_PATCH_DIR="$PLATFORM_BASE/patches/kernel/$KERNEL_VERSION/common"
    
    if [[ -f "$COMMON_PATCHLIST" ]]; then
        cd "$KERNEL_DIR"
        while read -r patch_name; do
            [[ -z "$patch_name" || "$patch_name" =~ ^# ]] && continue
            PATCH_FILE="$COMMON_PATCH_DIR/$patch_name"
            if [[ -f "$PATCH_FILE" ]]; then
                log "Applying: $patch_name"
                git am "$PATCH_FILE" || {
                    log "Warning: Failed to apply $patch_name, trying with 3-way merge..."
                    git am --abort 2>/dev/null || true
                    git am --3way "$PATCH_FILE" || error "Failed to apply $patch_name"
                }
            else
                log "Warning: Patch file not found: $PATCH_FILE"
            fi
        done < "$COMMON_PATCHLIST"
        cd ..
    else
        log "Warning: Patchlist not found: $COMMON_PATCHLIST"
    fi
fi

log "Done! Kernel source is available at: $(pwd)/$KERNEL_DIR"

