# Complete Guide: Remote Clangd TCP Setup for Neovim with LazyVim

**Document Version:** 1.0
**Last Updated:** January 2026
**Author:** Development Team

---

## Table of Contents

1. [Introduction](#1-introduction)
2. [Problem Statement](#2-problem-statement)
3. [Architecture Overview](#3-architecture-overview)
4. [Prerequisites](#4-prerequisites)
5. [Infrastructure Setup](#5-infrastructure-setup)
6. [Script Development](#6-script-development)
7. [Neovim Configuration Journey](#7-neovim-configuration-journey)
8. [Troubleshooting Chronicle](#8-troubleshooting-chronicle)
9. [Final Working Configuration](#9-final-working-configuration)
10. [Testing and Verification](#10-testing-and-verification)
11. [Maintenance and Operations](#11-maintenance-and-operations)
12. [Advanced Topics](#12-advanced-topics)
13. [Frequently Asked Questions](#13-frequently-asked-questions)
14. [Appendix](#14-appendix)

---

## 1. Introduction

### 1.1 What is This Document?

This document provides a comprehensive guide to setting up a remote clangd language server
that can be used with Neovim (specifically LazyVim distribution) on a local macOS machine.
The clangd server runs on a remote Linux server and communicates with the local editor
via TCP over an SSH tunnel.

### 1.2 Why Remote Clangd?

There are several scenarios where running clangd on a remote server is beneficial:

1. **Cross-compilation environments**: When developing for embedded systems or different
   architectures, the build toolchain and headers exist only on the remote server.

2. **Large codebases**: Clangd requires significant CPU and memory resources. Running it
   on a powerful remote server offloads this from your local machine.

3. **Consistent development environment**: Team members can share the same clangd setup
   regardless of their local machine configuration.

4. **Access to compile_commands.json**: The compilation database is generated on the
   build server and may reference paths that only exist there.

### 1.3 Technology Stack

- **Local Machine**: macOS with Neovim 0.11.4 and LazyVim
- **Remote Server**: Linux (referred to as `ap-remote`)
- **Language Server**: clangd 17.0.6
- **File Synchronization**: Mutagen (bidirectional sync)
- **Network Communication**: SSH tunnel + socat for TCP relay
- **Editor Integration**: nvim-lspconfig with custom configuration

---

## 2. Problem Statement

### 2.1 The Challenge

The goal was to configure Neovim with LazyVim to use a remote clangd server instead of
a locally installed one. This seems straightforward but presented multiple challenges:

1. **LSP Protocol over Network**: The Language Server Protocol (LSP) uses JSON-RPC over
   stdin/stdout. We needed to relay this over TCP.

2. **LazyVim's Plugin Architecture**: LazyVim has its own way of configuring LSP servers
   that differs from vanilla Neovim.

3. **Mason Integration**: LazyVim uses Mason to manage LSP servers, which kept overriding
   our custom clangd configuration.

4. **File Path Synchronization**: Both local and remote machines need access to the same
   files at the same paths for clangd to work correctly.

### 2.2 Requirements

1. Clangd must run on the remote server (`ap-remote`)
2. Neovim on local macOS must connect to remote clangd
3. All clangd features must work (go-to-definition, hover, completion, etc.)
4. The setup should be persistent and easy to restart
5. Local Mason-installed clangd must not interfere

---

## 3. Architecture Overview

### 3.1 High-Level Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              LOCAL MACHINE (macOS)                          │
│                                                                             │
│  ┌─────────────────┐                                                        │
│  │                 │                                                        │
│  │     NEOVIM      │                                                        │
│  │   (LazyVim)     │                                                        │
│  │                 │                                                        │
│  │  ┌───────────┐  │                                                        │
│  │  │ LSP Client│  │    stdio (stdin/stdout)                                │
│  │  └─────┬─────┘  │           │                                            │
│  │        │        │           │                                            │
│  └────────┼────────┘           │                                            │
│           │                    ▼                                            │
│           │         ┌─────────────────────┐                                 │
│           │         │                     │                                 │
│           └────────►│ clangd-tcp-client.sh│                                 │
│                     │                     │                                 │
│                     │  - Checks tunnel    │                                 │
│                     │  - Starts if needed │                                 │
│                     │  - Runs socat       │                                 │
│                     │                     │                                 │
│                     └──────────┬──────────┘                                 │
│                                │                                            │
│                                │ socat - TCP:localhost:9999                 │
│                                ▼                                            │
│                     ┌─────────────────────┐                                 │
│                     │                     │                                 │
│                     │   SSH TUNNEL        │                                 │
│                     │   (Port Forward)    │                                 │
│                     │                     │                                 │
│                     │ localhost:9999 ─────┼──────────────────────┐          │
│                     │                     │                      │          │
│                     └─────────────────────┘                      │          │
│                                                                  │          │
└──────────────────────────────────────────────────────────────────┼──────────┘
                                                                   │
                                            SSH Encrypted Tunnel   │
                                                                   │
┌──────────────────────────────────────────────────────────────────┼──────────┐
│                                                                  │          │
│                          REMOTE SERVER (ap-remote / Linux)       │          │
│                                                                  │          │
│                     ┌─────────────────────┐                      │          │
│                     │                     │◄─────────────────────┘          │
│                     │   socat             │                                 │
│                     │   TCP-LISTEN:9999   │                                 │
│                     │                     │                                 │
│                     └──────────┬──────────┘                                 │
│                                │                                            │
│                                │ fork + EXEC for each connection            │

---

## 4. Prerequisites

### 4.1 Local Machine Requirements

#### 4.1.1 Neovim Installation

Neovim 0.11+ is required for the new `vim.lsp.config()` and `vim.lsp.enable()` APIs.

```bash
# Check Neovim version
nvim --version

# Expected output (minimum):
# NVIM v0.11.0
# Build type: Release
# LuaJIT 2.1.0-beta3
```

If you need to install or upgrade:

```bash
# macOS with Homebrew
brew install neovim

# Or upgrade existing
brew upgrade neovim
```

#### 4.1.2 LazyVim Installation

This guide assumes you're using LazyVim. If not installed:

```bash
# Backup existing config
mv ~/.config/nvim ~/.config/nvim.bak
mv ~/.local/share/nvim ~/.local/share/nvim.bak

# Clone LazyVim starter
git clone https://github.com/LazyVim/starter ~/.config/nvim

# Remove .git so you can add your own repo
rm -rf ~/.config/nvim/.git
```

#### 4.1.3 Required Tools

```bash
# Install socat (for TCP relay)
brew install socat

# Install netcat (for connection testing)
brew install netcat

# Verify installations
which socat    # Should return path
which nc       # Should return path
```

#### 4.1.4 SSH Configuration

Ensure you have SSH access to the remote server:

```bash
# Test SSH connection
ssh ap-remote "echo 'Connection successful'"

# Recommended: Set up SSH config for easier access
cat >> ~/.ssh/config << 'EOF'
Host ap-remote
    HostName your-remote-server.com
    User your-username
    IdentityFile ~/.ssh/id_rsa
    ServerAliveInterval 60
    ServerAliveCountMax 3
EOF
```

### 4.2 Remote Server Requirements

#### 4.2.1 Clangd Installation

```bash
# SSH to remote server
ssh ap-remote

# Check if clangd is installed
which clangd
clangd --version

# If not installed (Ubuntu/Debian):
sudo apt update
sudo apt install clangd

# Or install specific version:
sudo apt install clangd-17
```

#### 4.2.2 Socat Installation

```bash
# On remote server
sudo apt install socat

# Verify
which socat
socat -V
```

#### 4.2.3 Workspace Directory

The workspace directory must exist and contain the source code:

```bash
# On remote server
ls -la /garage/workspace/ap

# Should contain your C/C++ source files and compile_commands.json
ls /garage/workspace/ap/compile_commands.json
```

### 4.3 File Synchronization (Mutagen)

Mutagen keeps files synchronized between local and remote machines.

#### 4.3.1 Install Mutagen

```bash
# macOS
brew install mutagen-io/mutagen/mutagen

# Verify
mutagen version
```

#### 4.3.2 Create Sync Session

```bash
# Create bidirectional sync
mutagen sync create \
    ~/garage/workspace/ap \
    ap-remote:/garage/workspace/ap \
    --name=ap-workspace \
    --sync-mode=two-way-resolved \
    --ignore-vcs \
    --ignore=".git" \
    --ignore="build/**" \
    --ignore="*.o" \
    --ignore="*.a"

# Check sync status
mutagen sync list
mutagen sync monitor ap-workspace
```

#### 4.3.3 Important Mutagen Considerations

- **Pause During Config Changes**: Mutagen can interfere with Neovim config changes
  ```bash
  mutagen sync pause ap-workspace
  # Make changes to ~/.config/nvim
  mutagen sync resume ap-workspace
  ```

- **Conflict Resolution**: Two-way-resolved mode automatically resolves conflicts
  by preferring the most recent change

- **Sync Latency**: There's a small delay between local changes and remote sync.
  For LSP to see new files, wait a few seconds after creating them.

---

## 5. Infrastructure Setup

### 5.1 Directory Structure

Create the necessary directory structure:

```bash
# Local machine
mkdir -p ~/garage/workspace/ap/scripts
mkdir -p ~/.cache/clangd-client
mkdir -p ~/.cache/clangd-tunnel

# Remote server
ssh ap-remote "mkdir -p /garage/workspace/ap/scripts"
ssh ap-remote "mkdir -p ~/.cache/clangd-server"
```

### 5.2 Script Locations

All scripts are stored in the `scripts/` directory of the workspace:

```
/garage/workspace/ap/
├── scripts/
│   ├── clangd-tcp-server.sh      # Runs on remote server
│   ├── clangd-tcp-client.sh      # Runs on local machine
│   ├── clangd-tunnel-setup.sh    # Manages SSH tunnel
│   └── CLANGD_TCP_SETUP_GUIDE.md # This documentation
├── ap/
│   └── src/                      # Source code
├── compile_commands.json         # Compilation database
└── ...
```


│                                ▼                                            │
│                     ┌─────────────────────┐                                 │
│                     │                     │                                 │
│                     │      CLANGD         │                                 │
│                     │                     │                                 │
│                     │  - Parses C/C++     │                                 │
│                     │  - Background index │                                 │
│                     │  - Completions      │                                 │
│                     │  - Diagnostics      │                                 │
│                     │                     │                                 │
│                     └─────────────────────┘                                 │
│                                │                                            │
│                                │ Reads files from                           │
│                                ▼                                            │
│                     ┌─────────────────────┐                                 │
│                     │                     │                                 │
│                     │  /garage/workspace  │◄────── Mutagen Sync             │
│                     │       /ap           │                                 │
│                     │                     │                                 │
│                     └─────────────────────┘                                 │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 3.2 Data Flow

1. **User Action**: User opens a C file in Neovim or requests go-to-definition
2. **LSP Request**: Neovim's LSP client generates a JSON-RPC request
3. **Client Script**: The request is sent to `clangd-tcp-client.sh` via stdin
4. **Socat Relay**: Local socat sends the request to `localhost:9999`
5. **SSH Tunnel**: The tunnel forwards the request to `ap-remote:9999`
6. **Remote Socat**: Remote socat receives the request and spawns/forwards to clangd
7. **Clangd Processing**: Clangd processes the request using the remote filesystem
8. **Response Path**: The response travels back through the same path in reverse

### 3.3 Component Responsibilities

| Component | Location | Responsibility |
|-----------|----------|----------------|
| Neovim LSP Client | Local | Generates LSP requests, displays results |
| clangd-tcp-client.sh | Local | Wrapper script, tunnel management, socat relay |
| clangd-tunnel-setup.sh | Local | SSH tunnel lifecycle management |
| SSH Tunnel | Network | Encrypted port forwarding |
| clangd-tcp-server.sh | Remote | TCP server, spawns clangd instances |
| clangd | Remote | Language server, code intelligence |
| Mutagen | Both | Bidirectional file synchronization |


