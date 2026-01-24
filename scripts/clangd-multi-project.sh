#!/bin/bash
# Multi-project clangd wrapper for remote TCP connections
# This script can be used to start clangd with the correct compile_commands.json
# based on the project directory

# Configuration: Add your projects here
# Format: PROJECT_NAME:PROJECT_PATH:COMPILE_COMMANDS_PATH
declare -A PROJECTS=(
    ["ap"]="/garage/workspace/ap:/garage/workspace/ap/compile_commands.json"
    ["linux-kernel"]="/Users/ajay.kumar/linux-5.4:/Users/ajay.kumar/linux-5.4/compile_commands.json"
)

# Default clangd binary
CLANGD_BIN="${CLANGD_BIN:-clangd}"

# Parse command line for --compile-commands-dir or detect from working directory
PROJECT_DIR=""
COMPILE_COMMANDS=""

# Check if a project path is specified or detect from current directory
if [[ -n "$1" && -d "$1" ]]; then
    PROJECT_DIR="$1"
    shift
else
    PROJECT_DIR="$(pwd)"
fi

# Find matching project
for name in "${!PROJECTS[@]}"; do
    IFS=':' read -r proj_path cc_path <<< "${PROJECTS[$name]}"
    if [[ "$PROJECT_DIR" == "$proj_path"* ]]; then
        echo "Detected project: $name" >&2
        COMPILE_COMMANDS="$cc_path"
        break
    fi
done

if [[ -z "$COMPILE_COMMANDS" ]]; then
    echo "Warning: No project matched for $PROJECT_DIR, using default clangd behavior" >&2
fi

# Start clangd
exec "$CLANGD_BIN" \
    --background-index \
    --clang-tidy=false \
    --header-insertion=never \
    --log=error \
    ${COMPILE_COMMANDS:+--compile-commands-dir="$(dirname "$COMPILE_COMMANDS")"} \
    "$@"

