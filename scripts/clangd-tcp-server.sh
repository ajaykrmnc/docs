#!/bin/bash
# Remote clangd TCP server script
# This script runs on the remote server (ap-remote) and starts clangd listening on a TCP port

set -euo pipefail

# Configuration
WORKSPACE_DIR="/garage/workspace/ap"
CLANGD_PORT="${CLANGD_PORT:-9999}"
CLANGD_BIN="${CLANGD_BIN:-/usr/bin/clangd}"
LOG_DIR="${HOME}/.cache/clangd-server"
LOG_FILE="${LOG_DIR}/clangd-server.log"

# Create log directory
mkdir -p "${LOG_DIR}"

# Function to log messages
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*" | tee -a "${LOG_FILE}"
}

# Function to cleanup on exit
cleanup() {
    log "Shutting down clangd TCP server on port ${CLANGD_PORT}"
    # Kill any socat processes we started
    pkill -P $$ socat 2>/dev/null || true
}

trap cleanup EXIT INT TERM

# Check if clangd exists
if [[ ! -x "${CLANGD_BIN}" ]]; then
    log "ERROR: clangd not found at ${CLANGD_BIN}"
    exit 1
fi

# Check if workspace directory exists
if [[ ! -d "${WORKSPACE_DIR}" ]]; then
    log "ERROR: Workspace directory not found: ${WORKSPACE_DIR}"
    exit 1
fi

# Check if port is already in use
if lsof -Pi :${CLANGD_PORT} -sTCP:LISTEN -t >/dev/null 2>&1; then
    log "WARNING: Port ${CLANGD_PORT} is already in use"
    log "Killing existing process..."
    lsof -ti:${CLANGD_PORT} | xargs kill -9 2>/dev/null || true
    sleep 1
fi

log "Starting clangd TCP server"
log "Workspace: ${WORKSPACE_DIR}"
log "Port: ${CLANGD_PORT}"
log "Clangd binary: ${CLANGD_BIN}"

# Change to workspace directory
cd "${WORKSPACE_DIR}"

# Start TCP server that directly spawns clangd for each connection
# The 'fork' option allows multiple simultaneous connections
log "Launching TCP server on port ${CLANGD_PORT}..."
exec socat \
    TCP-LISTEN:${CLANGD_PORT},reuseaddr,fork \
    EXEC:"${CLANGD_BIN} --background-index"

