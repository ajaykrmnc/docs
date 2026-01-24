# NFS-Based Remote Development Architecture

## Complete Guide for Local UI with Remote Filesystem and LSP

**Document Version:** 1.0  
**Last Updated:** January 2026  
**Target Audience:** Developers, System Administrators, DevOps Engineers

---

## Table of Contents

1. [Introduction](#1-introduction)
2. [NFS Architecture](#2-nfs-architecture)
3. [Server Setup (Linux)](#3-server-setup-linux)
4. [Client Setup (macOS)](#4-client-setup-macos)
5. [NFSv4 Specific Configuration](#5-nfsv4-specific-configuration)
6. [LSP Integration with NFS](#6-lsp-integration-with-nfs)
7. [Performance Optimization](#7-performance-optimization)
8. [Security Considerations](#8-security-considerations)
9. [High Availability and Redundancy](#9-high-availability-and-redundancy)
10. [Monitoring and Troubleshooting](#10-monitoring-and-troubleshooting)
11. [Docker and Container Integration](#11-docker-and-container-integration)
12. [Practical Workflows](#12-practical-workflows)
13. [Limitations and Alternatives](#13-limitations-and-alternatives)
14. [Quick Reference](#14-quick-reference)

---

## 1. Introduction

### 1.1 Overview of NFS-Based Remote Development

Network File System (NFS) provides a powerful foundation for remote development workflows
where developers want the responsiveness of local tools while accessing code stored on
remote servers. This architecture enables:

- **Local UI Performance**: Native applications like iTerm, Neovim, and VS Code run
  locally with full GPU acceleration and zero UI latency
- **Remote Filesystem Access**: Code and project files reside on a remote Linux server,
  accessible via NFS mount points
- **Remote LSP Processing**: Language servers execute on the remote machine where the
  code lives, with communication tunneled to local editors
- **Unified Development Experience**: The combination feels like local development
  while leveraging remote compute resources

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    NFS-Based Remote Development Architecture             │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│   ┌──────────────────────┐              ┌──────────────────────────┐    │
│   │   LOCAL MACHINE      │              │    REMOTE SERVER         │    │
│   │   (macOS/Linux)      │              │    (Linux)               │    │
│   │                      │              │                          │    │
│   │  ┌────────────────┐  │              │  ┌────────────────────┐  │    │
│   │  │  iTerm/Terminal│  │              │  │   NFS Server       │  │    │
│   │  └───────┬────────┘  │              │  │   (nfs-kernel-     │  │    │
│   │          │           │              │  │    server)         │  │    │
│   │  ┌───────▼────────┐  │   NFS/TCP    │  └─────────┬──────────┘  │    │
│   │  │    Neovim      │  │◄────────────►│            │             │    │
│   │  │   (Local UI)   │  │   Port 2049  │  ┌─────────▼──────────┐  │    │
│   │  └───────┬────────┘  │              │  │  /home/dev/code    │  │    │
│   │          │           │              │  │  (Exported Dir)    │  │    │
│   │  ┌───────▼────────┐  │              │  └────────────────────┘  │    │
│   │  │  LSP Client    │  │   SSH Tunnel │                          │    │
│   │  │  (nvim-lsp)    │◄─┼──────────────┼─►┌────────────────────┐  │    │
│   │  └────────────────┘  │   Port 9999  │  │   LSP Servers      │  │    │
│   │                      │              │  │   - gopls          │  │    │
│   │  ┌────────────────┐  │              │  │   - rust-analyzer  │  │    │
│   │  │  NFS Mount     │  │              │  │   - pyright        │  │    │
│   │  │ /mnt/remote    │  │              │  └────────────────────┘  │    │
│   │  └────────────────┘  │              │                          │    │
│   └──────────────────────┘              └──────────────────────────┘    │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

### 1.2 History and Versions of NFS

NFS was developed by Sun Microsystems in 1984 and has evolved significantly over four
decades. Understanding the version history helps in choosing the right configuration.

#### NFSv2 (1989) - RFC 1094

- Original widely-deployed version
- 32-bit file sizes (max 4GB files)
- UDP transport only
- Stateless protocol design
- Synchronous writes only
- **Status**: Obsolete, not recommended

#### NFSv3 (1995) - RFC 1813

- 64-bit file sizes (large file support)
- Asynchronous writes for better performance
- TCP transport support (in addition to UDP)
- READDIRPLUS for faster directory operations
- Weak cache consistency (WCC) data
- ACCESS procedure for permission checking
- **Status**: Still widely used, but NFSv4 preferred

```
NFSv3 Protocol Stack:
┌─────────────────────────┐
│     NFS Protocol        │
├─────────────────────────┤
│         RPC             │
├─────────────────────────┤
│      TCP or UDP         │
├─────────────────────────┤
│         IP              │
├─────────────────────────┤
│      Ethernet           │
└─────────────────────────┘
```

#### NFSv4 (2003) - RFC 3530

Major redesign with significant improvements:

- **Stateful Protocol**: Server maintains client state for better consistency
- **Compound Operations**: Multiple operations in single RPC call
- **Mandatory Strong Security**: Kerberos integration (RPCSEC_GSS)
- **Single Port**: Uses only TCP port 2049 (simplified firewall config)
- **Integrated Locking**: No separate lock manager (NLM) needed
- **ACL Support**: Access Control Lists for fine-grained permissions
- **Delegation**: Server can delegate file operations to clients for caching
- **Pseudo Filesystem**: Virtual root for all exports
- **UTF-8 Filenames**: Internationalization support

#### NFSv4.1 (2010) - RFC 5661

- **Sessions**: Improved connection management and exactly-once semantics
- **pNFS (Parallel NFS)**: Distributed data across multiple servers
- **Directory Delegations**: Cache directory contents locally
- **Improved Trunking**: Multiple network paths for redundancy

#### NFSv4.2 (2016) - RFC 7862

- **Server-Side Copy**: Copy files without transferring through client
- **Sparse Files**: Efficient handling of files with holes
- **Space Reservations**: Pre-allocate disk space
- **Application I/O Hints**: Optimize for specific access patterns
- **Labeled NFS**: SELinux security label support

```
NFS Version Comparison:
┌────────────────┬─────────┬─────────┬─────────┬─────────┬─────────┐
│ Feature        │ NFSv2   │ NFSv3   │ NFSv4   │ NFSv4.1 │ NFSv4.2 │
├────────────────┼─────────┼─────────┼─────────┼─────────┼─────────┤
│ Max File Size  │ 4GB     │ 16EB    │ 16EB    │ 16EB    │ 16EB    │
│ Transport      │ UDP     │ UDP/TCP │ TCP     │ TCP     │ TCP     │
│ State          │ None    │ Partial │ Full    │ Full    │ Full    │
│ Security       │ AUTH_SYS│ AUTH_SYS│ Kerberos│ Kerberos│ Kerberos│
│ Ports Required │ Many    │ Many    │ 2049    │ 2049    │ 2049    │
│ Locking        │ NLM     │ NLM     │ Built-in│ Built-in│ Built-in│
│ Delegations    │ No      │ No      │ Yes     │ Yes     │ Yes     │
│ pNFS           │ No      │ No      │ No      │ Yes     │ Yes     │
│ Server Copy    │ No      │ No      │ No      │ No      │ Yes     │
└────────────────┴─────────┴─────────┴─────────┴─────────┴─────────┘
```

### 1.3 Why NFS for Remote Development

NFS offers several advantages for remote development scenarios:

#### Performance Benefits

1. **Kernel-Level Integration**: NFS is implemented in the kernel, providing
   native filesystem semantics without FUSE overhead
2. **Efficient Caching**: Aggressive client-side caching reduces network round trips
3. **Large Transfer Sizes**: Configurable read/write sizes up to 1MB for efficiency
4. **Connection Persistence**: Long-lived TCP connections avoid setup overhead

#### Development Workflow Benefits

1. **Transparent Access**: Files appear as local; tools work without modification
2. **No Sync Required**: Changes are immediately visible (no manual push/pull)
3. **Full POSIX Semantics**: File permissions, symlinks, and special files work correctly
4. **Concurrent Access**: Multiple developers can access shared codebases

#### Operational Benefits

1. **Mature Technology**: Decades of production use and optimization
2. **Universal Support**: Built into Linux, macOS, BSD, and most Unix systems
3. **Standard Protocol**: Well-documented, interoperable implementations
4. **Centralized Storage**: Simplified backup and management

### 1.4 Comparison with Other Solutions

#### NFS vs SSHFS

```
┌─────────────────────────┬──────────────────────┬──────────────────────┐
│ Aspect                  │ NFS                  │ SSHFS                │
├─────────────────────────┼──────────────────────┼──────────────────────┤
│ Performance             │ High (kernel-level)  │ Lower (FUSE-based)   │
│ Setup Complexity        │ Medium               │ Low                  │
│ Security (default)      │ Low (AUTH_SYS)       │ High (SSH)           │
│ Security (with Kerberos)│ High                 │ N/A                  │
│ Firewall Friendly       │ Yes (NFSv4)          │ Yes (SSH port)       │
│ Caching                 │ Excellent            │ Basic                │
│ Large File Handling     │ Excellent            │ Good                 │
│ Concurrent Users        │ Native support       │ Limited              │
│ macOS Support           │ Native               │ Requires macFUSE     │
│ Latency Sensitivity     │ Lower                │ Higher               │
│ CPU Overhead            │ Low                  │ High (encryption)    │
└─────────────────────────┴──────────────────────┴──────────────────────┘
```

**When to choose NFS:**
- High-performance requirements
- Large codebases with many files
- Multiple concurrent users
- Native macOS integration preferred
- Low-latency file operations needed

**When to choose SSHFS:**
- Quick ad-hoc access needed
- Security is paramount and Kerberos is not available
- Traversing untrusted networks
- Simple setup preferred over performance

#### NFS vs Samba/CIFS

```
┌─────────────────────────┬──────────────────────┬──────────────────────┐
│ Aspect                  │ NFS                  │ Samba/CIFS           │
├─────────────────────────┼──────────────────────┼──────────────────────┤
│ Primary Platform        │ Unix/Linux/macOS     │ Windows              │
│ POSIX Semantics         │ Full                 │ Partial              │
│ Symlink Support         │ Native               │ Limited              │
│ Permission Model        │ Unix                 │ Windows ACLs         │
│ Performance (Unix)      │ Excellent            │ Good                 │
│ Case Sensitivity        │ Preserved            │ Configurable         │
│ File Locking            │ POSIX                │ Windows-style        │
│ Character Encoding      │ UTF-8                │ Various              │
└─────────────────────────┴──────────────────────┴──────────────────────┘
```

**When to choose NFS:**
- Unix/Linux/macOS environments
- Full POSIX compliance needed
- Symlinks and Unix permissions required
- Development workflows with Unix tools

**When to choose Samba:**
- Windows clients in the mix
- Active Directory integration
- Windows-style permissions needed

#### NFS vs Custom Solutions (rsync, Mutagen, etc.)

```
┌─────────────────────────┬──────────────────────┬──────────────────────┐
│ Aspect                  │ NFS                  │ Sync-based Solutions │
├─────────────────────────┼──────────────────────┼──────────────────────┤
│ Real-time Updates       │ Yes                  │ Near-real-time       │
│ Conflict Handling       │ Server authoritative │ Manual/merge needed  │
│ Offline Access          │ No                   │ Yes                  │
│ Network Dependency      │ Always online        │ Periodic sync        │
│ Storage Duplication     │ No                   │ Yes (both locations) │
│ Initial Setup Time      │ Fast                 │ Depends on size      │
│ Large Repos             │ Scales well          │ Slow initial sync    │
│ Multiple Developers     │ Natural              │ Complex              │
└─────────────────────────┴──────────────────────┴──────────────────────┘
```

**When to choose NFS:**
- Always-connected environment
- Single source of truth preferred
- No local storage duplication wanted
- Team collaboration on same codebase

**When to choose Sync Solutions:**
- Offline work capability needed
- Unreliable network connectivity
- Independent local copies preferred
- Complex merge workflows acceptable

---

## 2. NFS Architecture

### 2.1 How NFS Works

NFS uses a client-server architecture built on Remote Procedure Calls (RPC).
Understanding the underlying mechanisms helps in troubleshooting and optimization.

#### Remote Procedure Call (RPC)

NFS operations are implemented as RPCs, allowing clients to execute procedures
on the server as if they were local function calls.

```
RPC Call Flow:
┌──────────────────┐                          ┌──────────────────┐
│    NFS Client    │                          │    NFS Server    │
│                  │                          │                  │
│  ┌────────────┐  │    1. RPC Request        │  ┌────────────┐  │
│  │ open()     │──┼─────────────────────────►│  │ NFS Daemon │  │
│  │ read()     │  │                          │  │  (nfsd)    │  │
│  │ write()    │  │    2. Process Request    │  └─────┬──────┘  │
│  │ close()    │  │                          │        │         │
│  └────────────┘  │                          │        ▼         │
│        ▲         │    3. Access Local FS    │  ┌────────────┐  │
│        │         │                          │  │ Filesystem │  │
│        │         │    4. RPC Response       │  │ (ext4/xfs) │  │
│        └─────────┼◄─────────────────────────┼──┴────────────┘  │
│                  │                          │                  │
└──────────────────┘                          └──────────────────┘
```

#### External Data Representation (XDR)

XDR is a standard for describing and encoding data, ensuring interoperability
between different architectures (endianness, word size, etc.).

```
XDR Encoding Example:
┌─────────────────────────────────────────────────────────────────┐
│ Data Type        │ XDR Encoding                                │
├─────────────────────────────────────────────────────────────────┤
│ Integer (32-bit) │ 4 bytes, big-endian                         │
│ Hyper (64-bit)   │ 8 bytes, big-endian                         │
│ String           │ 4-byte length + data + padding to 4-byte    │
│ Opaque (fixed)   │ n bytes + padding to 4-byte boundary        │
│ Opaque (variable)│ 4-byte length + data + padding              │
│ Array            │ 4-byte count + elements                     │
└─────────────────────────────────────────────────────────────────┘
```

#### Stateless vs Stateful Design

**NFSv3 - Stateless Design:**
- Server maintains no information about clients
- Each request contains all necessary information
- Client responsible for recovery after server restart
- Simple server implementation but limited functionality

```
NFSv3 Stateless Operation:
┌────────────┐                              ┌────────────┐
│   Client   │                              │   Server   │
└─────┬──────┘                              └─────┬──────┘
      │                                           │
      │───── READ(filehandle, offset, count) ────►│
      │                                           │
      │◄──── DATA(bytes) ─────────────────────────│
      │                                           │
      │  (Server crash and restart)               │
      │                                           │
      │───── READ(filehandle, offset, count) ────►│
      │                                           │
      │◄──── DATA(bytes) ─────────────────────────│
      │                                           │
      │  (Client retries work automatically)      │
      ▼                                           ▼
```

**NFSv4 - Stateful Design:**
- Server maintains client state (open files, locks, delegations)
- Improved semantics (mandatory locking, share reservations)
- Lease-based state management with expiration
- Client must reclaim state after server restart

```
NFSv4 Stateful Operation:
┌────────────┐                              ┌────────────┐
│   Client   │                              │   Server   │
└─────┬──────┘                              └─────┬──────┘
      │                                           │
      │───── OPEN(filename) ─────────────────────►│
      │                                           │
      │◄──── stateid, filehandle ─────────────────│
      │                                           │
      │───── READ(stateid, offset, count) ───────►│
      │                                           │
      │◄──── DATA(bytes) ─────────────────────────│
      │                                           │
      │───── CLOSE(stateid) ─────────────────────►│
      │                                           │
      │◄──── OK ──────────────────────────────────│
      │                                           │
      │  (Server tracks open files and locks)     │
      ▼                                           ▼
```

### 2.2 NFSv4 Improvements Over NFSv3

NFSv4 represents a major evolution with numerous improvements:

#### Single Port Operation

```
NFSv3 Port Requirements:            NFSv4 Port Requirements:
┌─────────────────────────────┐     ┌─────────────────────────────┐
│ Service        │ Port       │     │ Service        │ Port       │
├─────────────────────────────┤     ├─────────────────────────────┤
│ portmapper     │ 111        │     │ NFS            │ 2049       │
│ nfsd           │ 2049       │     │ (All services) │ (Only)     │
│ mountd         │ Dynamic    │     └─────────────────────────────┘
│ statd          │ Dynamic    │
│ lockd          │ Dynamic    │      Much simpler firewall config!
└─────────────────────────────┘
```

#### Compound Operations

NFSv4 allows multiple operations in a single RPC call, reducing round trips:

```
NFSv3 Multiple Operations:          NFSv4 Compound Operation:
┌────────┐      ┌────────┐          ┌────────┐      ┌────────┐
│ Client │      │ Server │          │ Client │      │ Server │
└───┬────┘      └───┬────┘          └───┬────┘      └───┬────┘
    │               │                   │               │
    │─── LOOKUP ───►│                   │─── COMPOUND ─►│
    │◄─────────────│                   │    LOOKUP     │
    │               │                   │    GETATTR    │
    │─── GETATTR ──►│                   │    READ       │
    │◄─────────────│                   │◄──────────────│
    │               │                   │               │
    │─── READ ─────►│               (All in one round trip!)
    │◄─────────────│
    │               │
(3 round trips)                     (1 round trip)
```

#### Pseudo Filesystem

NFSv4 presents a unified view of all exports:

```
NFSv3 Separate Exports:              NFSv4 Pseudo Filesystem:

Export: /home                        /  (pseudo root)
Export: /data                        ├── home (real export)
Export: /projects                    ├── data (real export)
                                     └── projects (real export)

Client must mount each               Client mounts / and navigates
export separately                    to any export transparently
```

#### Delegation

Server can delegate file operations to trusted clients:

```
Delegation Flow:
┌────────────────────────────────────────────────────────────────────────┐
│                                                                        │
│   ┌────────────┐                              ┌────────────┐           │
│   │  Client A  │                              │   Server   │           │
│   └─────┬──────┘                              └─────┬──────┘           │
│         │                                           │                  │
│         │───── OPEN file.txt ─────────────────────►│                  │
│         │                                           │                  │
│         │◄──── OK + READ DELEGATION ────────────────│                  │
│         │                                           │                  │
│         │  (Client can now cache reads locally)     │                  │
│         │  (No need to check with server)           │                  │
│         │                                           │                  │
│   ┌─────▼──────┐                              ┌─────▼──────┐           │
│   │  Client B  │                              │   Server   │           │
│   └─────┬──────┘                              └─────┬──────┘           │
│         │                                           │                  │
│         │───── OPEN file.txt (for write) ─────────►│                  │
│         │                                           │                  │
│         │                  ┌────────────┐           │                  │
│         │                  │  Client A  │◄── CB_RECALL delegation     │
│         │                  └─────┬──────┘           │                  │
│         │                        │                  │                  │
│         │               Returns delegation ────────►│                  │
│         │                                           │                  │
│         │◄──── OK (can now write) ──────────────────│                  │
│         │                                           │                  │
│                                                                        │
└────────────────────────────────────────────────────────────────────────┘
```

### 2.3 Client-Server Model

The NFS architecture consists of several components working together:

```
Complete NFS Architecture:
┌─────────────────────────────────────────────────────────────────────────────┐
│                              CLIENT SIDE                                     │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│   User Application (vim, gcc, ls, cat, etc.)                                │
│         │                                                                    │
│         ▼                                                                    │
│   ┌─────────────────────────────────────────────────────────────────┐       │
│   │                    VFS (Virtual File System)                     │       │
│   │              Provides unified interface to all filesystems       │       │
│   └─────────────────────────────────────────────────────────────────┘       │
│         │                                                                    │
│         ▼                                                                    │
│   ┌─────────────────────────────────────────────────────────────────┐       │
│   │                      NFS Client                                  │       │
│   │  ┌─────────────┐  ┌──────────────┐  ┌────────────────────────┐  │       │
│   │  │ Attribute   │  │ Data Cache   │  │ Request Scheduler      │  │       │
│   │  │ Cache       │  │ (Page Cache) │  │ (Read-ahead/Write-back)│  │       │
│   │  └─────────────┘  └──────────────┘  └────────────────────────┘  │       │
│   └─────────────────────────────────────────────────────────────────┘       │
│         │                                                                    │
│         ▼                                                                    │
│   ┌─────────────────────────────────────────────────────────────────┐       │
│   │              RPC Client / SUNRPC                                 │       │
│   │        Handles connection management and retransmission          │       │
│   └─────────────────────────────────────────────────────────────────┘       │
│         │                                                                    │
│         ▼                                                                    │
│   ┌─────────────────────────────────────────────────────────────────┐       │
│   │                    TCP/IP Stack                                  │       │
│   └─────────────────────────────────────────────────────────────────┘       │
│                                    │                                         │
└────────────────────────────────────┼─────────────────────────────────────────┘
                                     │ Network
                                     │
┌────────────────────────────────────┼─────────────────────────────────────────┐
│                                    │                                         │
│   ┌─────────────────────────────────────────────────────────────────┐       │
│   │                    TCP/IP Stack                                  │       │
│   └─────────────────────────────────────────────────────────────────┘       │
│         │                                                                    │
│         ▼                                                                    │
│   ┌─────────────────────────────────────────────────────────────────┐       │
│   │              RPC Server / SUNRPC                                 │       │
│   └─────────────────────────────────────────────────────────────────┘       │
│         │                                                                    │
│         ▼                                                                    │
│   ┌─────────────────────────────────────────────────────────────────┐       │
│   │                      NFS Server (nfsd)                           │       │
│   │  ┌─────────────┐  ┌──────────────┐  ┌────────────────────────┐  │       │
│   │  │ Export      │  │ File Handle  │  │ Lock Manager           │  │       │
│   │  │ Table       │  │ Cache        │  │ (NFSv4 built-in)       │  │       │
│   │  └─────────────┘  └──────────────┘  └────────────────────────┘  │       │
│   └─────────────────────────────────────────────────────────────────┘       │
│         │                                                                    │
│         ▼                                                                    │
│   ┌─────────────────────────────────────────────────────────────────┐       │
│   │                    VFS (Virtual File System)                     │       │
│   └─────────────────────────────────────────────────────────────────┘       │
│         │                                                                    │
│         ▼                                                                    │
│   ┌─────────────────────────────────────────────────────────────────┐       │
│   │              Local Filesystem (ext4, xfs, btrfs)                 │       │
│   └─────────────────────────────────────────────────────────────────┘       │
│         │                                                                    │
│         ▼                                                                    │
│   ┌─────────────────────────────────────────────────────────────────┐       │
│   │                    Block Device / Storage                        │       │
│   └─────────────────────────────────────────────────────────────────┘       │
│                                                                              │
├─────────────────────────────────────────────────────────────────────────────┤
│                              SERVER SIDE                                     │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 2.4 NFS Operations Overview

NFS defines a set of standard operations for file system access:

#### File Operations

| Operation    | Description                                     |
|-------------|------------------------------------------------|
| OPEN        | Open a file, obtain stateid                     |
| CLOSE       | Close a file, release stateid                   |
| READ        | Read data from a file                           |
| WRITE       | Write data to a file                            |
| COMMIT      | Commit written data to stable storage           |
| LOCK        | Acquire a byte-range lock                       |
| LOCKU       | Release a byte-range lock                       |
| LOCKT       | Test for lock                                   |

#### Directory Operations

| Operation    | Description                                     |
|-------------|------------------------------------------------|
| LOOKUP      | Look up a filename in a directory               |
| CREATE      | Create a non-regular file                       |
| MKDIR       | Create a directory                              |
| REMOVE      | Remove a file                                   |
| RMDIR       | Remove a directory                              |
| RENAME      | Rename a file or directory                      |
| LINK        | Create a hard link                              |
| SYMLINK     | Create a symbolic link                          |
| READDIR     | Read directory contents                         |
| READLINK    | Read symbolic link target                       |

#### Attribute Operations

| Operation    | Description                                     |
|-------------|------------------------------------------------|
| GETATTR     | Get file attributes                             |
| SETATTR     | Set file attributes                             |
| ACCESS      | Check access permissions                        |
| GETFH       | Get current filehandle                          |
| PUTFH       | Set current filehandle                          |
| SAVEFH      | Save current filehandle                         |
| RESTOREFH  | Restore saved filehandle                        |

---

## 3. Server Setup (Linux)

### 3.1 Installing NFS Server Packages

#### Debian/Ubuntu Systems

```bash
# Update package lists
sudo apt update

# Install NFS kernel server
sudo apt install nfs-kernel-server

# Verify installation
dpkg -l | grep nfs-kernel-server

# Check NFS server version
cat /proc/fs/nfsd/versions
```

#### RHEL/CentOS/Fedora Systems

```bash
# Install NFS utilities
sudo dnf install nfs-utils

# For older CentOS/RHEL 7:
sudo yum install nfs-utils

# Verify installation
rpm -qa | grep nfs-utils
```

#### Arch Linux

```bash
# Install NFS utilities
sudo pacman -S nfs-utils
```

### 3.2 Configuring /etc/exports

The `/etc/exports` file defines which directories are shared and access permissions.

#### Basic Syntax

```
/path/to/export    client(options) [client2(options2)] ...
```

#### Example Configuration

```bash
# /etc/exports - NFS export configuration for development

# Export home directories for development team
# Allow read-write access from specific subnet
/home/developers    192.168.1.0/24(rw,sync,no_subtree_check,no_root_squash)

# Export project directories
# Multiple client specifications
/data/projects      192.168.1.0/24(rw,sync,no_subtree_check) \
                    10.0.0.0/8(ro,sync,no_subtree_check)

# Export with hostname patterns
/var/shared         *.dev.example.com(rw,sync,no_subtree_check)

# Export to specific host
/home/ajay          devmac.local(rw,sync,no_subtree_check,all_squash,anonuid=1000,anongid=1000)

# Read-only export for build artifacts
/data/artifacts     *(ro,sync,no_subtree_check)

# NFSv4-only export with Kerberos
/secure/data        gss/krb5p(rw,sync,no_subtree_check,sec=krb5p)
```

### 3.3 Export Options Explained

#### Access Options

| Option | Description |
|--------|-------------|
| `rw` | Read-write access (default is `ro`) |
| `ro` | Read-only access |
| `async` | Respond before data is written to disk (faster, less safe) |
| `sync` | Respond only after data is written to disk (slower, safer) |

#### Subtree Checking

| Option | Description |
|--------|-------------|
| `subtree_check` | Verify file is in exported tree (default, can cause issues) |
| `no_subtree_check` | Disable subtree checking (recommended) |

```
Subtree Check Issue Illustrated:

/data
├── projects (exported)
│   ├── app1
│   │   └── moved_file.txt  ← File moved here
│   └── app2
└── archive (not exported)
    └── moved_file.txt  ← Originally here

With subtree_check enabled, if a file is renamed while
a client has it open, NFS might lose track of it.
no_subtree_check is almost always the better choice.
```

#### Root Squashing Options

| Option | Description |
|--------|-------------|
| `root_squash` | Map root (UID 0) to anonymous user (default) |
| `no_root_squash` | Allow root access (needed for some admin tasks) |
| `all_squash` | Map all users to anonymous |
| `anonuid=UID` | Set anonymous user's UID |
| `anongid=GID` | Set anonymous user's GID |

```
Root Squashing Visualization:

Client                              Server
┌─────────────────┐                 ┌─────────────────┐
│ root (UID 0)    │ ──root_squash──►│ nobody (65534)  │
│ user1 (UID 1000)│ ────────────────►│ user1 (UID 1000)│
└─────────────────┘                 └─────────────────┘

With no_root_squash:
┌─────────────────┐                 ┌─────────────────┐
│ root (UID 0)    │ ────────────────►│ root (UID 0)    │
│ user1 (UID 1000)│ ────────────────►│ user1 (UID 1000)│
└─────────────────┘                 └─────────────────┘

With all_squash + anonuid=1000:
┌─────────────────┐                 ┌─────────────────┐
│ root (UID 0)    │ ────────────────►│ devuser (1000)  │
│ user1 (UID 1000)│ ────────────────►│ devuser (1000)  │
│ user2 (UID 1001)│ ────────────────►│ devuser (1000)  │
└─────────────────┘                 └─────────────────┘
```

#### Security Options

| Option | Description |
|--------|-------------|
| `sec=mode` | Security flavor (sys, krb5, krb5i, krb5p) |
| `secure` | Require requests from ports < 1024 (default) |
| `insecure` | Allow requests from any port |

### 3.4 Starting and Enabling NFS Services

#### Systemd-Based Systems (Modern Linux)

```bash
# Enable NFS server to start at boot
sudo systemctl enable nfs-server

# Start NFS server
sudo systemctl start nfs-server

# Check status
sudo systemctl status nfs-server

# Reload exports without restart (after editing /etc/exports)
sudo exportfs -ra

# View currently exported filesystems
sudo exportfs -v

# Show connected clients
sudo showmount -a
```

#### Managing Individual Components

```bash
# Enable RPC bind (required)
sudo systemctl enable rpcbind
sudo systemctl start rpcbind

# For NFSv3, also need these:
sudo systemctl enable nfs-mountd
sudo systemctl start nfs-mountd

sudo systemctl enable nfs-idmapd  # For NFSv4 ID mapping
sudo systemctl start nfs-idmapd

# Check which NFS services are running
systemctl list-units --type=service | grep nfs
```

#### Verifying Server Status

```bash
# Check RPC services
rpcinfo -p localhost

# Expected output for NFSv4:
# program vers proto   port  service
# 100000    4   tcp    111  portmapper
# 100000    4   udp    111  portmapper
# 100003    4   tcp   2049  nfs
# 100005    3   tcp  20048  mountd
# ...

# Check NFS version support
cat /proc/fs/nfsd/versions
# Output: -2 +3 +4 +4.1 +4.2

# Check number of NFS threads
cat /proc/fs/nfsd/threads
```

### 3.5 Firewall Configuration

#### Using firewalld (RHEL/CentOS/Fedora)

```bash
# Add NFS service
sudo firewall-cmd --permanent --add-service=nfs

# For NFSv3, also add:
sudo firewall-cmd --permanent --add-service=rpc-bind
sudo firewall-cmd --permanent --add-service=mountd

# Reload firewall
sudo firewall-cmd --reload

# Verify
sudo firewall-cmd --list-services
```

#### Using UFW (Ubuntu)

```bash
# Allow NFS
sudo ufw allow from 192.168.1.0/24 to any port nfs

# For NFSv4 only (simplest)
sudo ufw allow 2049/tcp

# For NFSv3 (need to fix ports first - see below)
sudo ufw allow 111/tcp
sudo ufw allow 111/udp
sudo ufw allow 2049/tcp
sudo ufw allow 2049/udp
sudo ufw allow 32765:32768/tcp
sudo ufw allow 32765:32768/udp

# Check status
sudo ufw status
```

#### Fixing NFSv3 Ports for Firewall

NFSv3 uses dynamic ports by default. To make it firewall-friendly:

```bash
# /etc/nfs.conf (modern systems)
[lockd]
port = 32765

[mountd]
port = 32767

[statd]
port = 32766

# Or for older systems, edit /etc/sysconfig/nfs:
LOCKD_TCPPORT=32765
LOCKD_UDPPORT=32765
MOUNTD_PORT=32767
STATD_PORT=32766
```

#### Using iptables Directly

```bash
# NFSv4 only (recommended)
sudo iptables -A INPUT -p tcp --dport 2049 -j ACCEPT
sudo iptables -A INPUT -p tcp --dport 2049 -s 192.168.1.0/24 -j ACCEPT

# NFSv3 with fixed ports
sudo iptables -A INPUT -p tcp --dport 111 -j ACCEPT
sudo iptables -A INPUT -p udp --dport 111 -j ACCEPT
sudo iptables -A INPUT -p tcp --dport 2049 -j ACCEPT
sudo iptables -A INPUT -p udp --dport 2049 -j ACCEPT
sudo iptables -A INPUT -p tcp --dport 32765:32768 -j ACCEPT
sudo iptables -A INPUT -p udp --dport 32765:32768 -j ACCEPT

# Save iptables rules
sudo iptables-save > /etc/iptables/rules.v4
```

### 3.6 Performance Tuning

#### NFS Server Thread Count

```bash
# Check current thread count
cat /proc/fs/nfsd/threads

# Set thread count (8-16 per CPU core is common)
echo 32 | sudo tee /proc/fs/nfsd/threads

# Make permanent in /etc/nfs.conf:
[nfsd]
threads = 32
```

#### Tuning sysctl Parameters

```bash
# /etc/sysctl.d/99-nfs-tuning.conf

# Increase network buffer sizes
net.core.rmem_max = 16777216
net.core.wmem_max = 16777216
net.core.rmem_default = 1048576
net.core.wmem_default = 1048576

# TCP buffer tuning
net.ipv4.tcp_rmem = 4096 1048576 16777216
net.ipv4.tcp_wmem = 4096 1048576 16777216

# NFS-specific tuning
sunrpc.tcp_slot_table_entries = 128
sunrpc.udp_slot_table_entries = 128

# Apply changes
sudo sysctl -p /etc/sysctl.d/99-nfs-tuning.conf
```

#### Filesystem Tuning on Server

```bash
# For ext4: Enable writeback mode for better write performance
# In /etc/fstab:
/dev/sda1 /data ext4 defaults,data=writeback,noatime 0 2

# For XFS: Increase log size
mkfs.xfs -l size=128m /dev/sdb1

# Mount with optimal options
mount -o noatime,nodiratime,logbufs=8 /dev/sdb1 /data

# Consider using SSD or NVMe for hot data
# Use RAID10 for balance of performance and redundancy
```

---

## 4. Client Setup (macOS)

### 4.1 macOS NFS Client Capabilities

macOS includes a robust NFS client built into the kernel with support for:

- NFSv2, NFSv3, and NFSv4
- Kerberos authentication
- Finder integration
- Automounting
- Read-ahead caching
- Write-behind buffering

```bash
# Check macOS NFS client version
nfsstat -m  # Shows mounted NFS filesystems with options

# View NFS client statistics
nfsstat -c  # Client-side statistics

# Check available NFS-related commands
ls /sbin/mount_nfs /usr/bin/nfs*
```

### 4.2 Mounting NFS Shares Manually

#### Basic Mount Command

```bash
# Create mount point
sudo mkdir -p /Volumes/remote-dev

# Basic NFSv4 mount
sudo mount -t nfs -o vers=4 server.example.com:/home/dev /Volumes/remote-dev

# NFSv3 mount
sudo mount -t nfs -o vers=3 server.example.com:/home/dev /Volumes/remote-dev

# Mount with specific options
sudo mount -t nfs -o vers=4,tcp,rsize=1048576,wsize=1048576,resvport \
    server.example.com:/home/dev /Volumes/remote-dev
```

#### Mount Options for macOS

```bash
# Recommended mount options for development workloads:
sudo mount -t nfs \
    -o vers=4,tcp \
    -o rsize=1048576,wsize=1048576 \
    -o resvport \
    -o noatime \
    -o soft,timeo=30,retrans=2 \
    -o actimeo=2 \
    -o nfc \
    server.example.com:/home/dev /Volumes/remote-dev
```

### 4.3 Mount Options Explained

#### Version and Protocol

| Option | Description |
|--------|-------------|
| `vers=3` or `vers=4` | NFS protocol version |
| `tcp` | Use TCP transport (recommended) |
| `udp` | Use UDP transport (not recommended for WAN) |

#### Transfer Size Options

| Option | Description |
|--------|-------------|
| `rsize=N` | Read buffer size in bytes (max 1048576) |
| `wsize=N` | Write buffer size in bytes (max 1048576) |

```
Performance Impact of rsize/wsize:

┌─────────────────────────────────────────────────────────────────┐
│ Buffer Size │ Small Files │ Large Files │ Network Overhead     │
├─────────────────────────────────────────────────────────────────┤
│ 8192        │ Good        │ Slow        │ High (many packets)  │
│ 32768       │ Good        │ Moderate    │ Moderate             │
│ 131072      │ Okay        │ Good        │ Lower                │
│ 1048576     │ Okay        │ Excellent   │ Minimal              │
└─────────────────────────────────────────────────────────────────┘

For development with many small files: 32768-131072
For large file transfers: 1048576
```

#### Timeout and Retry Options

| Option | Description |
|--------|-------------|
| `soft` | Return error on timeout (vs `hard` which retries indefinitely) |
| `hard` | Retry indefinitely on timeout (can cause hangs) |
| `timeo=N` | Timeout in tenths of a second before retry |
| `retrans=N` | Number of retries before giving up (with soft) |
| `intr` | Allow interrupt of hung NFS operations |

```
Soft vs Hard Mount Behavior:

Hard Mount (default):
┌────────────┐                              ┌────────────┐
│   Client   │                              │   Server   │
└─────┬──────┘                              └─────┬──────┘
      │                                           │
      │───── READ request ───────────────────────►│ (Server down)
      │                                           X
      │◄──── (no response) ───────────────────────│
      │                                           │
      │───── Retry READ ─────────────────────────►│
      │                                           X
      │◄──── (no response) ───────────────────────│
      │                                           │
      │  (Continues forever until server returns) │
      │  (Process hangs, cannot be killed easily) │

Soft Mount:
┌────────────┐                              ┌────────────┐
│   Client   │                              │   Server   │
└─────┬──────┘                              └─────┬──────┘
      │                                           │
      │───── READ request ───────────────────────►│ (Server down)
      │                                           X
      │◄──── (no response, timeout) ──────────────│
      │                                           │
      │───── Retry (retrans times) ──────────────►│
      │                                           X
      │                                           │
      │  Return EIO error to application          │
      │  (Application can handle gracefully)      │
```

#### Caching Options

| Option | Description |
|--------|-------------|
| `actimeo=N` | Set all cache timeouts to N seconds |
| `acregmin=N` | Min seconds to cache regular file attributes |
| `acregmax=N` | Max seconds to cache regular file attributes |
| `acdirmin=N` | Min seconds to cache directory attributes |
| `acdirmax=N` | Max seconds to cache directory attributes |
| `noac` | Disable attribute caching (reduces performance) |

#### macOS-Specific Options

| Option | Description |
|--------|-------------|
| `resvport` | Use privileged port (required by most servers) |
| `nfc` | Enable Unicode NFC normalization for filenames |
| `locallocks` | Use local locking instead of NFS locking |
| `nobrowse` | Don't show in Finder sidebar |
| `rdirplus` | Enable READDIRPLUS for NFSv3 |

### 4.4 Auto-Mounting with /etc/auto_master

macOS uses the automounter (`autofs`) for automatic mounting of NFS shares.

#### Configuring /etc/auto_master

```bash
# /etc/auto_master - Main automounter configuration
#
# Automounter master map
# Format: mount_point  map_name  options
#
+auto_master
/home                   auto_home       -nobrowse,nosuid
/Network/Servers        -fstab
/-                      -static
/Volumes/nfs            auto_nfs        -nobrowse
```

#### Creating /etc/auto_nfs

```bash
# /etc/auto_nfs - NFS automount map
#
# Format: key  [options]  location
#
# Mount server.example.com:/home/dev at /Volumes/nfs/dev
dev         -fstype=nfs,vers=4,rsize=1048576,wsize=1048576,resvport \
            server.example.com:/home/dev

# Mount projects directory
projects    -fstype=nfs,vers=4,soft,timeo=30,resvport \
            server.example.com:/data/projects

# Mount with different server
builds      -fstype=nfs,vers=4,ro,resvport \
            buildserver.example.com:/artifacts
```

#### Activating Automount Configuration

```bash
# Restart automountd to pick up changes
sudo automount -vc

# Verify automount is running
sudo launchctl list | grep autofsd

# Test by accessing the mount point
ls /Volumes/nfs/dev

# Check what's mounted
mount | grep nfs
```

#### Automount Debugging

```bash
# Enable verbose automount logging
sudo sysctl -w debug.automount=1

# Check system log for automount messages
log show --predicate 'subsystem == "com.apple.autofs"' --last 10m

# Manually trigger automount
sudo automount -vc -d

# View automount status
sudo automount -m
```

### 4.5 Finder Integration

#### Making NFS Mounts Visible in Finder

```bash
# By default, mounts with 'nobrowse' don't show in Finder
# To show in Finder, mount without nobrowse:
sudo mount -t nfs -o vers=4,resvport server.example.com:/home/dev /Volumes/dev

# Or use open command to reveal in Finder:
open /Volumes/nfs/dev
```

#### Connect to Server via Finder

1. Press `Cmd + K` in Finder (or Go → Connect to Server)
2. Enter: `nfs://server.example.com/home/dev`
3. Click Connect
4. Mounted at `/Volumes/home/dev`

#### Creating Desktop Alias

```bash
# Create symbolic link on Desktop
ln -s /Volumes/nfs/dev ~/Desktop/Remote-Dev

# Or create Finder alias
osascript -e 'tell application "Finder" to make alias file to POSIX file "/Volumes/nfs/dev" at desktop'
```

### 4.6 Troubleshooting Common macOS Issues

#### Issue: Mount Fails with "Permission Denied"

```bash
# Check if server requires privileged port
# macOS default uses unprivileged ports
sudo mount -t nfs -o resvport server:/export /mnt

# Verify server allows your IP
ssh server "showmount -e"

# Check firewall on server
ssh server "sudo iptables -L -n | grep 2049"
```

#### Issue: Slow Performance

```bash
# Check mount options
nfsstat -m

# Ensure using TCP and large buffer sizes
sudo umount /Volumes/remote
sudo mount -t nfs -o vers=4,tcp,rsize=1048576,wsize=1048576 server:/export /Volumes/remote

# Disable attribute caching for debugging (not for production!)
sudo mount -t nfs -o noac server:/export /Volumes/remote
```

#### Issue: Stale File Handle

```bash
# Usually happens when server export changes
sudo umount -f /Volumes/remote

# If umount hangs
sudo umount -f -l /Volumes/remote  # Lazy unmount

# Remount
sudo mount -t nfs server:/export /Volumes/remote
```

#### Issue: Operation Not Permitted

```bash
# Often UID/GID mapping issue
# Check your local UID
id

# Check expected UID on server
ssh server "id youruser"

# If using all_squash on server, ensure anonuid matches
# Server /etc/exports:
# /export client(rw,all_squash,anonuid=1000,anongid=1000)
```

#### Issue: Lock Errors

```bash
# NFSv4 includes locking, but can have issues
# Try mounting with local locking
sudo mount -t nfs -o locallocks server:/export /Volumes/remote

# Or disable locking entirely (not recommended for shared access)
sudo mount -t nfs -o nolocks server:/export /Volumes/remote
```

---

## 5. NFSv4 Specific Configuration

### 5.1 ID Mapping (idmapd)

NFSv4 uses string-based user/group names instead of numeric UIDs/GIDs.
The `idmapd` daemon translates between the two.

#### How ID Mapping Works

```
NFSv4 ID Mapping Flow:

Client Side                                    Server Side
┌─────────────────────────────────────────────────────────────────────┐
│                                                                      │
│  Local User                                    Remote File           │
│  (ajay, UID 501)                              (owner: ajay)          │
│       │                                              ▲               │
│       ▼                                              │               │
│  ┌─────────────┐                              ┌─────────────┐        │
│  │ NFS Client  │                              │ NFS Server  │        │
│  │ idmapd      │                              │ idmapd      │        │
│  └──────┬──────┘                              └──────┬──────┘        │
│         │                                            │               │
│         ▼                                            ▼               │
│  ajay@example.com  ◄─────── Network ──────►  ajay@example.com       │
│  (String form)                                (String form)          │
│                                                      │               │
│                                                      ▼               │
│                                              Local User              │
│                                              (ajay, UID 1000)        │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

#### Server-Side Configuration

```bash
# /etc/idmapd.conf
[General]
# Domain must match on client and server
Domain = example.com

[Mapping]
Nobody-User = nobody
Nobody-Group = nogroup

[Translation]
Method = nsswitch
# Or use static mapping:
# Method = static
# Static-File = /etc/idmapd.map

# Restart idmapd
sudo systemctl restart nfs-idmapd

# Clear ID mapping cache
sudo nfsidmap -c
```

#### Client-Side Configuration (Linux)

```bash
# Same /etc/idmapd.conf structure
[General]
Domain = example.com

[Translation]
Method = nsswitch
```

#### macOS ID Mapping

macOS handles ID mapping differently. Configure in `/etc/nfs.conf`:

```bash
# /etc/nfs.conf (macOS)
nfs.client.default_nfs4domain = example.com

# Restart NFS client
sudo nfsd restart
```

### 5.2 Kerberos Authentication Setup

Kerberos provides strong authentication for NFSv4, replacing the weak AUTH_SYS.

#### Prerequisites

```
Kerberos Infrastructure Needed:
┌─────────────────────────────────────────────────────────────────────┐
│                                                                      │
│   ┌─────────────┐      ┌─────────────┐      ┌─────────────┐         │
│   │   KDC       │      │ NFS Server  │      │ NFS Client  │         │
│   │ (Kerberos)  │      │             │      │             │         │
│   └──────┬──────┘      └──────┬──────┘      └──────┬──────┘         │
│          │                    │                    │                │
│   Contains:                Has keytab:         Has keytab:          │
│   - krbtgt/REALM          nfs/server.realm    - Client principal    │
│   - nfs/server.realm      - Host principal    - Or user's TGT       │
│   - user principals                                                  │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

#### Server Kerberos Setup

```bash
# 1. Install Kerberos packages
sudo apt install krb5-user krb5-config  # Debian/Ubuntu
sudo dnf install krb5-workstation       # RHEL/Fedora

# 2. Configure /etc/krb5.conf
[libdefaults]
    default_realm = EXAMPLE.COM
    dns_lookup_realm = false
    dns_lookup_kdc = true

[realms]
    EXAMPLE.COM = {
        kdc = kdc.example.com
        admin_server = kdc.example.com
    }

[domain_realm]
    .example.com = EXAMPLE.COM
    example.com = EXAMPLE.COM

# 3. Create service principal on KDC
kadmin.local -q "addprinc -randkey nfs/nfsserver.example.com"

# 4. Export keytab to NFS server
kadmin.local -q "ktadd -k /etc/krb5.keytab nfs/nfsserver.example.com"

# 5. Start GSSD (handles Kerberos for NFS)
sudo systemctl enable nfs-server rpc-gssd
sudo systemctl start rpc-gssd

# 6. Configure export with Kerberos
# /etc/exports
/secure gss/krb5(rw,sync,no_subtree_check,sec=krb5p)
```

#### Client Kerberos Setup

```bash
# 1. Install Kerberos client
sudo apt install krb5-user  # Debian/Ubuntu

# 2. Same /etc/krb5.conf as server (or copy from KDC)

# 3. Get Kerberos ticket
kinit username@EXAMPLE.COM

# 4. Verify ticket
klist

# 5. Mount with Kerberos
sudo mount -t nfs -o sec=krb5p server:/secure /mnt/secure
```

### 5.3 NFSv4 ACLs

NFSv4 supports rich ACLs beyond traditional Unix permissions.

#### ACL Structure

```
NFSv4 ACL Entry Format:

TYPE:FLAGS:PRINCIPAL:PERMISSIONS

TYPE:        ALLOW or DENY
FLAGS:       Inheritance flags (for directories)
PRINCIPAL:   User or group (user@domain or group@domain)
PERMISSIONS: rwadDxnNtTcCoy (much more granular than rwx)
```

#### Permission Mapping

| NFSv4 | Description | Unix Equivalent |
|-------|-------------|-----------------|
| r | Read data | r |
| w | Write data | w |
| x | Execute | x |
| a | Append data | (part of w) |
| d | Delete file | (directory w) |
| D | Delete child (dir) | (directory w) |
| t | Read attributes | (implicit) |
| T | Write attributes | (implicit) |
| n | Read named attrs | - |
| N | Write named attrs | - |
| c | Read ACL | - |
| C | Write ACL | (owner only) |
| o | Change owner | (root only) |

#### Setting NFSv4 ACLs

```bash
# View ACL
nfs4_getfacl /path/to/file

# Set ACL allowing user read/write
nfs4_setfacl -a A::user@example.com:rwatTnNcCy /path/to/file

# Deny group access
nfs4_setfacl -a D::group@example.com:rwadDxnNtTcCo /path/to/file

# Set default ACL for new files in directory
nfs4_setfacl -a A:fd:user@example.com:rwatTnNcCy /path/to/directory
```

### 5.4 Delegation and Caching

NFSv4 delegations allow clients to cache aggressively by delegating authority.

#### Delegation Types

| Type | Description |
|------|-------------|
| READ | Client can cache reads without checking server |
| WRITE | Client can cache writes without syncing to server |

#### Delegation Flow

```
Open Delegation Sequence:
┌────────────────────────────────────────────────────────────────────────────┐
│                                                                             │
│  Client A                           Server                     Client B    │
│  ────────                           ──────                     ────────    │
│      │                                 │                          │        │
│      │──── OPEN file.txt ─────────────►│                          │        │
│      │                                 │                          │        │
│      │◄─── OK + READ DELEGATION ───────│                          │        │
│      │                                 │                          │        │
│      │  (Client A can now cache and    │                          │        │
│      │   read without server contact)  │                          │        │
│      │                                 │                          │        │
│      │     ... many local reads ...    │                          │        │
│      │     (no network traffic)        │                          │        │
│      │                                 │                          │        │
│      │                                 │◄── OPEN file.txt (write) ─│        │
│      │                                 │                          │        │
│      │◄─── CB_RECALL (give back) ──────│                          │        │
│      │                                 │                          │        │
│      │──── DELEGRETURN ───────────────►│                          │        │
│      │                                 │                          │        │
│      │                                 │──── OK (can now write) ──►│        │
│      │                                 │                          │        │
└────────────────────────────────────────────────────────────────────────────┘
```

#### Configuring Delegation

```bash
# Server side - Enable delegations (usually on by default)
echo "Y" | sudo tee /proc/fs/nfsd/nfsv4_delegations

# Check delegation status
cat /proc/fs/nfsd/nfsv4_delegations

# Client side - View delegation statistics
cat /proc/fs/nfsfs/delegation

# Per-export delegation control (/etc/exports)
/data client(rw,no_subtree_check,delegation)
```

### 5.5 pNFS (Parallel NFS)

pNFS, introduced in NFSv4.1, enables parallel data access across multiple servers.

#### pNFS Architecture

```
pNFS Layout Types:
┌─────────────────────────────────────────────────────────────────────────┐
│                                                                          │
│   ┌──────────────┐                                                      │
│   │   Metadata   │◄─── Layout requests                                  │
│   │    Server    │                                                      │
│   │   (MDS)      │                                                      │
│   └──────────────┘                                                      │
│          │                                                               │
│          │ Returns layout map                                           │
│          ▼                                                               │
│   ┌──────────────────────────────────────────────────────────┐          │
│   │                     pNFS Client                           │          │
│   └─────┬────────────────────┬───────────────────────┬───────┘          │
│         │                    │                       │                   │
│         ▼                    ▼                       ▼                   │
│   ┌──────────┐        ┌──────────┐           ┌──────────┐               │
│   │  Data    │        │  Data    │           │  Data    │               │
│   │ Server 1 │        │ Server 2 │           │ Server 3 │               │
│   │  (DS)    │        │  (DS)    │           │  (DS)    │               │
│   └──────────┘        └──────────┘           └──────────┘               │
│                                                                          │
│   Data is striped across multiple servers for parallel I/O              │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

#### pNFS Layout Types

| Layout | Description | Backend |
|--------|-------------|---------|
| Files | Data striped across NFS servers | Multiple NFS servers |
| Blocks | Block-level access | SAN (FC, iSCSI) |
| Objects | Object storage | Object Storage Devices |
| FlexFiles | Enhanced files layout | NFSv3/4 data servers |

```bash
# Check pNFS support
cat /proc/fs/nfsd/supported_layouts
# Output: files

# Mount with pNFS enabled
sudo mount -t nfs -o vers=4.1 server:/export /mnt

# Verify pNFS is working
cat /proc/fs/nfsfs/pnfs_files/*
```

---

## 6. LSP Integration with NFS

### 6.1 Running LSP Servers on the NFS Server

When using NFS for remote development, running LSP servers on the machine
where files are stored provides optimal performance.

#### Why Remote LSP?

```
Remote LSP Benefits:
┌─────────────────────────────────────────────────────────────────────────┐
│                                                                          │
│  Without Remote LSP (LSP runs locally over NFS):                        │
│  ┌─────────────────────────────────────────────────────────────────┐    │
│  │ Local Machine                                                    │    │
│  │  ┌─────────┐      ┌─────────┐                                   │    │
│  │  │ Neovim  │◄────►│ gopls   │──┐                                │    │
│  │  └─────────┘      └─────────┘  │ Many small file reads          │    │
│  │       ▲                        ▼ over NFS (slow!)               │    │
│  │       │              ┌──────────────────┐                       │    │
│  │       └──────────────│ NFS Mount        │◄─── Network ───┐      │    │
│  │                      │ /Volumes/remote  │                │      │    │
│  │                      └──────────────────┘                │      │    │
│  └──────────────────────────────────────────────────────────│──────┘    │
│                                                              │           │
│  ┌──────────────────────────────────────────────────────────│──────┐    │
│  │ Remote Server                                             │      │    │
│  │                                                           ▼      │    │
│  │                      ┌──────────────────┐                       │    │
│  │                      │ /home/dev/code   │ Actual files          │    │
│  │                      └──────────────────┘                       │    │
│  └─────────────────────────────────────────────────────────────────┘    │
│                                                                          │
│  Problem: LSP reads hundreds of files, each incurring network latency   │
│                                                                          │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  With Remote LSP (LSP runs on server, tunneled to client):              │
│  ┌─────────────────────────────────────────────────────────────────┐    │
│  │ Local Machine                                                    │    │
│  │  ┌─────────┐      ┌─────────────┐                               │    │
│  │  │ Neovim  │◄────►│ LSP Proxy   │                               │    │
│  │  └─────────┘      └──────┬──────┘                               │    │
│  │       ▲                  │ JSON-RPC over SSH tunnel             │    │
│  │       │                  │ (small messages, low latency)        │    │
│  │       │                  ▼                                       │    │
│  │  NFS Mount        SSH Tunnel to server:9999                     │    │
│  │  (for editing)                                                   │    │
│  └──────────────────────────────────────────────────────────────────┘    │
│                                                                          │
│  ┌──────────────────────────────────────────────────────────────────┐   │
│  │ Remote Server                                                     │   │
│  │  ┌─────────┐      ┌──────────────────┐                           │   │
│  │  │ gopls   │◄────►│ /home/dev/code   │ Local disk access (fast!) │   │
│  │  └────┬────┘      └──────────────────┘                           │   │
│  │       │                                                           │   │
│  │  Listening on port 9999                                          │   │
│  └──────────────────────────────────────────────────────────────────┘   │
│                                                                          │
│  Result: LSP has local disk speed, only LSP messages cross network      │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

