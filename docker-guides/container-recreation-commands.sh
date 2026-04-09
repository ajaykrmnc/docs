#!/bin/bash
#
# Container Recreation Commands
# Generated: March 23, 2026
# 
# This script contains the exact commands to recreate your containers in Colima
# if they ever need to be rebuilt from scratch.
#
# Usage:
#   1. Make sure Colima is running: colima start
#   2. Make sure images are loaded (see image import section)
#   3. Run individual commands or source this file
#

set -e  # Exit on error

echo "=== Container Recreation Script ==="
echo "This script will recreate your Docker containers in Colima"
echo ""

# ============================================================================
# PREREQUISITES
# ============================================================================

echo "Checking prerequisites..."

# Check if Colima is running
if ! docker info &> /dev/null; then
    echo "❌ Error: Docker is not running. Please start Colima first:"
    echo "   colima start"
    exit 1
fi

# Check if using Colima context
CURRENT_CONTEXT=$(docker context show)
if [ "$CURRENT_CONTEXT" != "colima" ]; then
    echo "⚠️  Warning: Not using Colima context. Switching..."
    docker context use colima
fi

# Check if images exist
echo "Checking for required images..."
if ! docker images | grep -q "barney-docker"; then
    echo "❌ Error: barney-docker:latest image not found"
    echo "   Please import the image first (see IMAGE IMPORT section below)"
    exit 1
fi

if ! docker images | grep -q "artools-base"; then
    echo "❌ Error: artools-base:latest image not found"
    echo "   Please import the image first (see IMAGE IMPORT section below)"
    exit 1
fi

echo "✅ Prerequisites check passed"
echo ""

# ============================================================================
# VOLUME CREATION
# ============================================================================

echo "=== Creating Volumes ==="

# Create artools-base workspace volume
if docker volume ls | grep -q "artools-docker_artools-base-workspace"; then
    echo "⚠️  Volume artools-docker_artools-base-workspace already exists"
else
    echo "Creating volume: artools-docker_artools-base-workspace"
    docker volume create artools-docker_artools-base-workspace
    echo "✅ Volume created"
fi

echo ""

# ============================================================================
# CONTAINER CREATION
# ============================================================================

echo "=== Creating Containers ==="

# ----------------------------------------------------------------------------
# wifiap Container
# ----------------------------------------------------------------------------

echo "Creating wifiap container..."

# Remove existing container if it exists
if docker ps -a | grep -q "wifiap"; then
    echo "⚠️  Removing existing wifiap container..."
    docker rm -f wifiap
fi

# Create wifiap container
docker run -dit \
  --name wifiap \
  --network host \
  --user barney \
  --hostname ajay.kumar \
  --workdir /workspace \
  --dns 10.14.0.1 \
  --dns 10.128.1.1 \
  --dns 10.128.1.2 \
  --dns 8.8.8.8 \
  --dns-search sjc.aristanetworks.com \
  --dns-search aristanetworks.com \
  --dns-search arista.io \
  -v /Users/ajay.kumar/.ssh:/root/.ssh:ro \
  -v /Volumes/linux-dev/garage/:/garage:rw \
  -v /Volumes/linux-dev/linux/:/linux:rw \
  -v /Users/ajay.kumar/.zshrc:/root/.zshrc:ro \
  -v /Users/ajay.kumar/.config:/root/.config:rw \
  -e TERM=xterm-256color \
  -e LANG=en_US.UTF-8 \
  -e LC_ALL=en_US.UTF-8 \
  -e CGO_ENABLED=1 \
  barney-docker:latest

echo "✅ wifiap container created"
echo ""

# ----------------------------------------------------------------------------
# artools-base Container
# ----------------------------------------------------------------------------

echo "Creating artools-base container..."

# Remove existing container if it exists
if docker ps -a | grep -q "artools-base"; then
    echo "⚠️  Removing existing artools-base container..."
    docker rm -f artools-base
fi

# Create artools-base container
docker run -dit \
  --name artools-base \
  --network host \
  --hostname artools-base \
  --workdir /workspace \
  --dns 10.14.0.1 \
  --dns 10.128.1.1 \
  --dns 10.128.1.2 \
  --dns 8.8.8.8 \
  --dns-search sjc.aristanetworks.com \
  --dns-search aristanetworks.com \
  --dns-search arista.io \
  -v /Users/ajay.kumar:/home/user:rw \
  -v /Users/ajay.kumar/.gitconfig:/root/.gitconfig:ro \
  -v /Users/ajay.kumar/.ssh:/root/.ssh:ro \
  -v artools-docker_artools-base-workspace:/workspace:rw \
  -e LANG=en_US.UTF-8 \
  -e LC_ALL=en_US.UTF-8 \
  -e A4_CHROOT=/ \
  -e TERM=xterm-256color \
  artools-base:latest

echo "✅ artools-base container created"
echo ""

# ============================================================================
# VERIFICATION
# ============================================================================

echo "=== Verification ==="

echo "Listing containers..."
docker ps -a

echo ""
echo "Testing container connectivity..."

if docker exec wifiap echo "wifiap is responsive" &> /dev/null; then
    echo "✅ wifiap container is working"
else
    echo "❌ wifiap container is not responding"
fi

if docker exec artools-base echo "artools-base is responsive" &> /dev/null; then
    echo "✅ artools-base container is working"
else
    echo "❌ artools-base container is not responding"
fi

echo ""
echo "=== Container Recreation Complete ==="

# ============================================================================
# IMAGE IMPORT SECTION (for reference)
# ============================================================================
#
# If you need to import images from tar files, use these commands:
#
# docker load -i /path/to/barney-docker.tar
# docker load -i /path/to/artools-base.tar
#
# Or if you need to export images:
#
# docker save barney-docker:latest -o barney-docker.tar
# docker save artools-base:latest -o artools-base.tar
#
# ============================================================================

# ============================================================================
# INDIVIDUAL CONTAINER COMMANDS (for copy-paste)
# ============================================================================
#
# If you want to recreate containers individually, use these commands:
#
# --- wifiap Container ---
# docker rm -f wifiap  # Remove existing if needed
# docker run -dit --name wifiap --network host --user barney --hostname ajay.kumar --workdir /workspace --dns 10.14.0.1 --dns 10.128.1.1 --dns 10.128.1.2 --dns 8.8.8.8 --dns-search sjc.aristanetworks.com --dns-search aristanetworks.com --dns-search arista.io -v /Users/ajay.kumar/.ssh:/root/.ssh:ro -v /Volumes/linux-dev/garage/:/garage:rw -v /Volumes/linux-dev/linux/:/linux:rw -v /Users/ajay.kumar/.zshrc:/root/.zshrc:ro -v /Users/ajay.kumar/.config:/root/.config:rw -e TERM=xterm-256color -e LANG=en_US.UTF-8 -e LC_ALL=en_US.UTF-8 -e CGO_ENABLED=1 barney-docker:latest
#
# --- artools-base Container ---
# docker rm -f artools-base  # Remove existing if needed
# docker run -dit --name artools-base --network host --hostname artools-base --workdir /workspace --dns 10.14.0.1 --dns 10.128.1.1 --dns 10.128.1.2 --dns 8.8.8.8 --dns-search sjc.aristanetworks.com --dns-search aristanetworks.com --dns-search arista.io -v /Users/ajay.kumar:/home/user:rw -v /Users/ajay.kumar/.gitconfig:/root/.gitconfig:ro -v /Users/ajay.kumar/.ssh:/root/.ssh:ro -v artools-docker_artools-base-workspace:/workspace:rw -e LANG=en_US.UTF-8 -e LC_ALL=en_US.UTF-8 -e A4_CHROOT=/ -e TERM=xterm-256color artools-base:latest
#
# ============================================================================

