# UID, GID, and Process Credentials

## Table of Contents

1. Introduction - Why Numeric IDs?
2. The Basics - UID, GID, and User Database
3. Process Credentials - Real, Effective, Saved, and Filesystem IDs
4. How Permission Checking Works
5. Setuid and Setgid Programs
6. Supplementary Groups
7. Why Grouping Matters - File Sharing
8. NFS and Network File Sharing
9. Centralized Identity Management
10. Kernel Data Structures
11. System Calls for Credentials
12. Security Considerations
13. Summary and Quick Reference

---

## 1. Introduction - Why Numeric IDs?

### The Problem Unix Solves

```
┌───────────────────────────────────────────────────────────────────────┐
│                     WHY NUMERIC IDs?                                   │
├───────────────────────────────────────────────────────────────────────┤
│                                                                       │
│   The kernel doesn't understand names. It works with numbers.         │
│                                                                       │
│   When you type:    ls -l project.txt                                 │
│   Kernel stores:    owner_uid=1000, owner_gid=2000                    │
│   Shell displays:   owner=alice, group=developers                     │
│                                                                       │
│   The translation happens in userspace (via NSS - Name Service Switch)│
│                                                                       │
│   ┌──────────────────┐     ┌──────────────────┐                      │
│   │   KERNEL SPACE   │     │   USER SPACE     │                      │
│   │                  │     │                  │                      │
│   │  inode.uid=1000  │────►│  "alice"         │                      │
│   │  inode.gid=2000  │────►│  "developers"    │                      │
│   │                  │     │                  │                      │
│   │  Numbers only!   │     │  Names for humans│                      │
│   └──────────────────┘     └──────────────────┘                      │
│                                                                       │
└───────────────────────────────────────────────────────────────────────┘
```

### Historical Context

```
┌───────────────────────────────────────────────────────────────────────┐
│                     EVOLUTION OF UNIX IDs                              │
├───────────────────────────────────────────────────────────────────────┤
│                                                                       │
│   Early Unix (1970s):                                                 │
│   • 16-bit UIDs (0-65535)                                            │
│   • Sufficient for single machines                                   │
│                                                                       │
│   System V / BSD (1980s):                                             │
│   • Still 16-bit, but groups became important                        │
│   • Supplementary groups introduced (BSD)                            │
│                                                                       │
│   Modern Linux:                                                       │
│   • 32-bit UIDs (0-4,294,967,295)                                    │
│   • Needed for enterprise environments                               │
│   • User namespaces add another layer                                │
│                                                                       │
│   Special UIDs:                                                       │
│   • UID 0        = root (superuser, all permissions)                 │
│   • UID 65534    = nobody (used for untrusted operations)            │
│   • UID 1-999    = system accounts (daemons, services)               │
│   • UID 1000+    = regular users                                     │
│                                                                       │
└───────────────────────────────────────────────────────────────────────┘
```

---

## 2. The Basics - UID, GID, and User Database

### The User Database (/etc/passwd)

```
┌───────────────────────────────────────────────────────────────────────┐
│                      /etc/passwd FORMAT                                │
├───────────────────────────────────────────────────────────────────────┤
│                                                                       │
│   alice:x:1000:1000:Alice Smith:/home/alice:/bin/bash                 │
│   ─┬──  ┬ ─┬── ─┬── ─────┬───── ─────┬───── ────┬────                │
│    │    │  │    │        │           │          │                     │
│    │    │  │    │        │           │          └─► Login shell       │
│    │    │  │    │        │           └──────────► Home directory      │
│    │    │  │    │        └──────────────────────► GECOS (full name)   │
│    │    │  │    └───────────────────────────────► Primary GID         │
│    │    │  └────────────────────────────────────► UID                 │
│    │    └───────────────────────────────────────► Password (x=shadow) │
│    └────────────────────────────────────────────► Username            │
│                                                                       │
│   Example entries:                                                    │
│   root:x:0:0:root:/root:/bin/bash                                     │
│   nobody:x:65534:65534:nobody:/nonexistent:/usr/sbin/nologin          │
│   alice:x:1000:1000:Alice:/home/alice:/bin/bash                       │
│   bob:x:1001:1001:Bob:/home/bob:/bin/bash                             │
│   www-data:x:33:33:www-data:/var/www:/usr/sbin/nologin                │
│                                                                       │
└───────────────────────────────────────────────────────────────────────┘
```

### The Group Database (/etc/group)

```
┌───────────────────────────────────────────────────────────────────────┐
│                       /etc/group FORMAT                                │
├───────────────────────────────────────────────────────────────────────┤
│                                                                       │
│   developers:x:2000:alice,bob,charlie                                 │
│   ────┬─────  ┬ ─┬── ───────┬────────                                │
│       │       │  │          │                                         │
│       │       │  │          └──────────► Member list                  │
│       │       │  └─────────────────────► GID                          │
│       │       └────────────────────────► Password (rarely used)       │
│       └────────────────────────────────► Group name                   │
│                                                                       │
│   Example entries:                                                    │
│   root:x:0:                                                           │
│   sudo:x:27:alice                                                     │
│   www-data:x:33:                                                      │
│   alice:x:1000:                          # alice's private group      │
│   developers:x:2000:alice,bob            # shared project group       │
│   docker:x:999:alice,bob                 # access to docker           │
│                                                                       │
└───────────────────────────────────────────────────────────────────────┘
```

### Primary Group vs Supplementary Groups

```
┌───────────────────────────────────────────────────────────────────────┐
│              PRIMARY GROUP vs SUPPLEMENTARY GROUPS                     │
├───────────────────────────────────────────────────────────────────────┤
│                                                                       │
│                         alice (UID 1000)                              │
│                               │                                       │
│            ┌──────────────────┼──────────────────┐                    │
│            │                  │                  │                    │
│            ▼                  ▼                  ▼                    │
│   ┌─────────────────┐ ┌─────────────┐ ┌─────────────────────┐        │
│   │  PRIMARY GROUP  │ │ SUPP GROUP  │ │    SUPP GROUP       │        │
│   │                 │ │             │ │                     │        │
│   │  alice (1000)   │ │ sudo (27)   │ │ developers (2000)   │        │
│   │                 │ │             │ │                     │        │
│   │ From /etc/passwd│ │     From /etc/group members list    │        │
│   └─────────────────┘ └─────────────┘ └─────────────────────┘        │
│                                                                       │
│   • Primary group: Assigned to new files created by user             │
│   • Supplementary groups: Additional access permissions              │
│                                                                       │
│   $ id alice                                                          │
│   uid=1000(alice) gid=1000(alice) groups=1000(alice),27(sudo),2000(developers)
│                   ─────┬─────           ──────────────┬──────────────│
│                   Primary GID              Supplementary groups       │
│                                                                       │
└───────────────────────────────────────────────────────────────────────┘
```

---

## 3. Process Credentials - Real, Effective, Saved, and Filesystem IDs

Every process carries a complete set of credentials:

```
┌───────────────────────────────────────────────────────────────────────┐
│                     PROCESS CREDENTIALS                                │
├───────────────────────────────────────────────────────────────────────┤
│                                                                       │
│   ┌─────────────────────────────────────────────────────────────────┐ │
│   │                        USER IDs                                 │ │
│   ├─────────────────────────────────────────────────────────────────┤ │
│   │                                                                 │ │
│   │   RUID (Real UID)                                              │ │
│   │   • Who actually logged in and started the process             │ │
│   │   • Set at login, inherited by child processes                 │ │
│   │   • Used to determine who to send signals to                   │ │
│   │                                                                 │ │
│   │   EUID (Effective UID)                                         │ │
│   │   • Used for ALL permission checks                             │ │
│   │   • Can differ from RUID for setuid programs                   │ │
│   │   • If EUID=0, process has root privileges                     │ │
│   │                                                                 │ │
│   │   SUID (Saved UID)                                             │ │
│   │   • Saved copy of EUID when exec() runs setuid program         │ │
│   │   • Allows dropping and regaining privileges                   │ │
│   │                                                                 │ │
│   │   FSUID (Filesystem UID) - Linux specific                      │ │
│   │   • Used only for filesystem permission checks                 │ │
│   │   • Usually equals EUID (legacy, rarely used directly)         │ │
│   │                                                                 │ │
│   └─────────────────────────────────────────────────────────────────┘ │
│                                                                       │
│   ┌─────────────────────────────────────────────────────────────────┐ │
│   │                        GROUP IDs                                │ │
│   ├─────────────────────────────────────────────────────────────────┤ │
│   │                                                                 │ │
│   │   RGID (Real GID)       - User's actual primary group          │ │
│   │   EGID (Effective GID)  - Used for permission checks           │ │
│   │   SGID (Saved GID)      - Saved for privilege switching        │ │
│   │   FSGID (Filesystem GID)- For filesystem checks (Linux)        │ │
│   │                                                                 │ │
│   │   Supplementary Groups  - Additional groups (up to 65536)      │ │
│   │                                                                 │ │
│   └─────────────────────────────────────────────────────────────────┘ │
│                                                                       │
└───────────────────────────────────────────────────────────────────────┘
```

### Visualizing Real vs Effective

```
┌───────────────────────────────────────────────────────────────────────┐
│                  REAL vs EFFECTIVE UIDs                                │
├───────────────────────────────────────────────────────────────────────┤
│                                                                       │
│   SCENARIO 1: Normal Program (e.g., /bin/ls)                          │
│   ────────────────────────────────────────────                        │
│                                                                       │
│   alice (UID 1000) runs: $ ls /home                                   │
│                                                                       │
│   ┌─────────────────────────────────────┐                             │
│   │         ls process                   │                             │
│   │                                      │                             │
│   │   RUID = 1000 (alice)               │                             │
│   │   EUID = 1000 (alice)  ◄── same     │                             │
│   │   SUID = 1000 (alice)               │                             │
│   │                                      │                             │
│   └─────────────────────────────────────┘                             │
│                                                                       │
│   Permission check uses EUID=1000                                     │
│                                                                       │
│                                                                       │
│   SCENARIO 2: Setuid Program (e.g., /usr/bin/passwd)                  │
│   ──────────────────────────────────────────────────                  │
│                                                                       │
│   $ ls -l /usr/bin/passwd                                             │
│   -rwsr-xr-x 1 root root 68208 ... /usr/bin/passwd                   │
│      ↑                                                                │
│      s = setuid bit (execute + setuid)                                │
│                                                                       │
│   alice (UID 1000) runs: $ passwd                                     │
│                                                                       │
│   ┌─────────────────────────────────────┐                             │
│   │       passwd process                 │                             │
│   │                                      │                             │
│   │   RUID = 1000 (alice) ◄── who ran it│                             │
│   │   EUID = 0    (root)  ◄── from file │                             │
│   │   SUID = 0    (root)     owner      │                             │
│   │                                      │                             │
│   └─────────────────────────────────────┘                             │
│                                                                       │
│   • EUID=0 allows writing to /etc/shadow                              │
│   • RUID=1000 tells passwd which user's password to change           │
│                                                                       │
└───────────────────────────────────────────────────────────────────────┘
```

### The Saved UID - Privilege Switching

```
┌───────────────────────────────────────────────────────────────────────┐
│                    SAVED UID - DROP AND REGAIN                         │
├───────────────────────────────────────────────────────────────────────┤
│                                                                       │
│   A setuid program needs to:                                          │
│   1. Drop privileges for normal operations (security)                 │
│   2. Regain privileges when needed (functionality)                    │
│                                                                       │
│   Example: Network server that needs to bind to port 80               │
│                                                                       │
│   ┌──────────────────────────────────────────────────────────────┐   │
│   │   Step 1: Program starts (setuid root)                       │   │
│   │   RUID=1000, EUID=0, SUID=0                                  │   │
│   │                                                              │   │
│   │   Step 2: Bind to port 80 (needs root)                       │   │
│   │   bind(sockfd, port 80) ← succeeds because EUID=0            │   │
│   │                                                              │   │
│   │   Step 3: Drop privileges                                    │   │
│   │   seteuid(1000)  →  RUID=1000, EUID=1000, SUID=0            │   │
│   │                                     ↑                        │   │
│   │                            Now running as alice              │   │
│   │                                                              │   │
│   │   Step 4: Handle requests safely with limited privileges     │   │
│   │                                                              │   │
│   │   Step 5: Need root again? Use SUID                          │   │
│   │   seteuid(0)  →  RUID=1000, EUID=0, SUID=0                  │   │
│   │               ↑                                              │   │
│   │   Can regain root because SUID=0 allows it                   │   │
│   └──────────────────────────────────────────────────────────────┘   │
│                                                                       │
│   Security: Call setuid(1000) to permanently drop root               │
│   This sets RUID=EUID=SUID=1000 - cannot regain root                 │
│                                                                       │
└───────────────────────────────────────────────────────────────────────┘
```

---

## 4. How Permission Checking Works

### The Permission Check Algorithm

```
┌───────────────────────────────────────────────────────────────────────┐
│                  UNIX PERMISSION CHECK ALGORITHM                       │
├───────────────────────────────────────────────────────────────────────┤
│                                                                       │
│   When process accesses a file:                                       │
│                                                                       │
│   ┌─────────────────────────────────────────────────────────────────┐ │
│   │                                                                 │ │
│   │   if (process.EUID == 0) {                                      │ │
│   │       return ALLOW;    // Root bypasses most checks             │ │
│   │   }                                                             │ │
│   │                                                                 │ │
│   │   if (process.EUID == file.owner_uid) {                        │ │
│   │       check OWNER permission bits (rwx------)                   │ │
│   │       return result;                                            │ │
│   │   }                                                             │ │
│   │                                                                 │ │
│   │   if (process.EGID == file.group_gid ||                        │ │
│   │       file.group_gid IN process.supplementary_groups) {        │ │
│   │       check GROUP permission bits (---rwx---)                   │ │
│   │       return result;                                            │ │
│   │   }                                                             │ │
│   │                                                                 │ │
│   │   check OTHER permission bits (------rwx)                       │ │
│   │   return result;                                                │ │
│   │                                                                 │ │
│   └─────────────────────────────────────────────────────────────────┘ │
│                                                                       │
│   KEY: Only ONE category is checked, in order:                        │
│        1. Owner  2. Group  3. Other                                   │
│                                                                       │
└───────────────────────────────────────────────────────────────────────┘
```

### Permission Check Examples

```
┌───────────────────────────────────────────────────────────────────────┐
│                    PERMISSION CHECK EXAMPLES                           │
├───────────────────────────────────────────────────────────────────────┤
│                                                                       │
│   File: project.txt                                                   │
│   Owner: alice (UID 1000)                                             │
│   Group: developers (GID 2000)                                        │
│   Mode: rw-r-----  (640)                                              │
│                                                                       │
│   ┌─────────────────────────────────────────────────────────────────┐ │
│   │ Process     EUID   EGID   Supp Groups   Category   Access       │ │
│   ├─────────────────────────────────────────────────────────────────┤ │
│   │ alice's     1000   1000   [2000]        OWNER      rw- ✓        │ │
│   │ bob's       1001   1001   [2000]        GROUP      r-- ✓ read   │ │
│   │ charlie's   1002   1002   []            OTHER      --- ✗        │ │
│   │ root's      0      0      []            (root)     rw- ✓        │ │
│   └─────────────────────────────────────────────────────────────────┘ │
│                                                                       │
│                                                                       │
│   GOTCHA: Owner permissions can be MORE restrictive than group!       │
│                                                                       │
│   File: weird.txt                                                     │
│   Owner: alice (UID 1000)                                             │
│   Group: developers (GID 2000)                                        │
│   Mode: ---rw----  (060)   ← Owner has NO permissions!                │
│                                                                       │
│   • alice (owner) CANNOT read the file                               │
│   • bob (in group developers) CAN read and write                     │
│   • This is valid but unusual                                        │
│                                                                       │
└───────────────────────────────────────────────────────────────────────┘
```

---

## 5. Setuid and Setgid Programs

### How Setuid Works

```
┌───────────────────────────────────────────────────────────────────────┐
│                     SETUID BIT EXPLAINED                               │
├───────────────────────────────────────────────────────────────────────┤
│                                                                       │
│   File permissions have special bits:                                 │
│                                                                       │
│   ┌─────────────────────────────────────────────────────────────────┐ │
│   │                                                                 │ │
│   │   rwsr-xr-x    setuid bit (s in owner execute position)        │ │
│   │   rwxr-sr-x    setgid bit (s in group execute position)        │ │
│   │   rwxr-xr-t    sticky bit (t in other execute position)        │ │
│   │                                                                 │ │
│   │   Numeric: chmod 4755 file  (setuid)                           │ │
│   │           chmod 2755 file  (setgid)                            │ │
│   │           chmod 1755 file  (sticky)                            │ │
│   │                                                                 │ │
│   └─────────────────────────────────────────────────────────────────┘ │
│                                                                       │
│   When exec() runs a setuid program:                                  │
│                                                                       │
│   ┌────────────────────┐         ┌────────────────────┐              │
│   │   Before exec()    │         │   After exec()     │              │
│   │                    │         │                    │              │
│   │   RUID = 1000     │  ────►  │   RUID = 1000      │              │
│   │   EUID = 1000     │         │   EUID = 0  ◄─┐    │              │
│   │   SUID = 1000     │         │   SUID = 0    │    │              │
│   │                    │         │         from file │              │
│   └────────────────────┘         └──────── owner ────┘              │
│                                                                       │
└───────────────────────────────────────────────────────────────────────┘
```

### Common Setuid Programs

```
┌───────────────────────────────────────────────────────────────────────┐
│                   COMMON SETUID PROGRAMS                               │
├───────────────────────────────────────────────────────────────────────┤
│                                                                       │
│   $ find /usr/bin -perm -4000 -ls 2>/dev/null                        │
│                                                                       │
│   Program          Owner   Why Setuid?                                │
│   ─────────────────────────────────────────────────────────────────  │
│   /usr/bin/passwd   root   Write to /etc/shadow                      │
│   /usr/bin/su       root   Change user identity                      │
│   /usr/bin/sudo     root   Execute commands as another user          │
│   /usr/bin/chsh     root   Change user's shell in /etc/passwd        │
│   /usr/bin/newgrp   root   Change effective group                    │
│   /bin/ping         root   Create raw network sockets (older systems)│
│   /bin/mount        root   Mount filesystems                         │
│   /bin/umount       root   Unmount filesystems                       │
│                                                                       │
│   Note: Modern Linux uses CAPABILITIES instead of setuid for         │
│   programs like ping (CAP_NET_RAW capability)                        │
│                                                                       │
└───────────────────────────────────────────────────────────────────────┘
```

### Setgid on Directories

```
┌───────────────────────────────────────────────────────────────────────┐
│                   SETGID ON DIRECTORIES                                │
├───────────────────────────────────────────────────────────────────────┤
│                                                                       │
│   When setgid is set on a DIRECTORY, files created inside inherit    │
│   the directory's group (not the creator's primary group).           │
│                                                                       │
│   This is crucial for shared project directories!                     │
│                                                                       │
│   $ mkdir /shared/project                                             │
│   $ chgrp developers /shared/project                                  │
│   $ chmod 2775 /shared/project                                        │
│          ↑                                                            │
│          setgid bit                                                   │
│                                                                       │
│   Without setgid:                 With setgid:                        │
│   ┌─────────────────────┐        ┌─────────────────────┐              │
│   │ alice creates file  │        │ alice creates file  │              │
│   │                     │        │                     │              │
│   │ file.txt            │        │ file.txt            │              │
│   │ owner: alice        │        │ owner: alice        │              │
│   │ group: alice   ←────│────    │ group: developers ←─│── inherited  │
│   │ (alice's primary)   │        │ (from directory)    │              │
│   └─────────────────────┘        └─────────────────────┘              │
│                                                                       │
│   With setgid, ALL files in /shared/project get group=developers     │
│                                                                       │
└───────────────────────────────────────────────────────────────────────┘
```

---

## 6. Supplementary Groups

### What Are Supplementary Groups?

```
┌───────────────────────────────────────────────────────────────────────┐
│                    SUPPLEMENTARY GROUPS                                │
├───────────────────────────────────────────────────────────────────────┤
│                                                                       │
│   Each process has:                                                   │
│   • ONE primary/effective GID (from /etc/passwd)                     │
│   • MANY supplementary groups (from /etc/group membership)           │
│                                                                       │
│   ┌─────────────────────────────────────────────────────────────────┐ │
│   │                                                                 │ │
│   │   /etc/passwd:                                                  │ │
│   │   alice:x:1000:1000:...     ← primary GID is 1000               │ │
│   │                                                                 │ │
│   │   /etc/group:                                                   │ │
│   │   alice:x:1000:             ← alice's private group             │ │
│   │   sudo:x:27:alice           ← alice is a member                 │ │
│   │   developers:x:2000:alice,bob                                   │ │
│   │   docker:x:999:alice        ← alice is a member                 │ │
│   │   www-data:x:33:alice                                           │ │
│   │                                                                 │ │
│   │   When alice logs in, her process gets:                         │ │
│   │   EGID = 1000                                                   │ │
│   │   Supplementary = [27, 33, 999, 2000]                          │ │
│   │                                                                 │ │
│   └─────────────────────────────────────────────────────────────────┘ │
│                                                                       │
│   Limits:                                                             │
│   • Traditional Unix: 16 supplementary groups                        │
│   • Linux: 65536 supplementary groups (NGROUPS_MAX)                  │
│                                                                       │
└───────────────────────────────────────────────────────────────────────┘
```

### How Supplementary Groups Are Loaded

```
┌───────────────────────────────────────────────────────────────────────┐
│                 SUPPLEMENTARY GROUPS LOADING                           │
├───────────────────────────────────────────────────────────────────────┤
│                                                                       │
│   When user logs in (via login, sshd, etc.):                         │
│                                                                       │
│   1. Login program runs as root                                       │
│   2. Calls initgroups("alice", 1000)                                  │
│      • Scans /etc/group for alice's memberships                      │
│      • Calls setgroups() to set supplementary groups                 │
│   3. Calls setgid(1000) and setuid(1000)                             │
│   4. exec() user's shell                                              │
│                                                                       │
│   ┌────────────────────────────────────────────────────────────────┐ │
│   │                                                                │ │
│   │   /* Simplified login code */                                  │ │
│   │                                                                │ │
│   │   /* Must be root to do this */                                │ │
│   │   initgroups(username, primary_gid);  /* Load supp groups */  │ │
│   │                                                                │ │
│   │   setgid(gid);   /* Set real and effective GID */              │ │
│   │   setuid(uid);   /* Set real and effective UID */              │ │
│   │                  /* Now we are the user, cannot go back */     │ │
│   │                                                                │ │
│   │   exec(shell);   /* Run user's shell */                        │ │
│   │                                                                │ │
│   └────────────────────────────────────────────────────────────────┘ │
│                                                                       │
│   Child processes inherit supplementary groups from parent!          │
│                                                                       │
└───────────────────────────────────────────────────────────────────────┘
```

### Viewing and Changing Groups

```bash
# See your groups
$ id
uid=1000(alice) gid=1000(alice) groups=1000(alice),27(sudo),999(docker),2000(developers)

# See groups only
$ groups
alice sudo docker developers

# See another user's groups
$ id bob
uid=1001(bob) gid=1001(bob) groups=1001(bob),2000(developers)

# Temporarily change effective group (rarely used)
$ newgrp developers
$ id
uid=1000(alice) gid=2000(developers) groups=1000(alice),27(sudo),999(docker),2000(developers)
                    ↑
            EGID changed to developers
```

---

## 7. Why Grouping Matters - File Sharing

```
Without groups:
┌──────────────┐     ┌──────────────┐
│    Alice     │     │     Bob      │
│  UID: 1000   │     │  UID: 1001   │
└──────────────┘     └──────────────┘
        │                   │
        ▼                   ▼
   project.txt         Can't access!
   owner: alice        (different UID)
   mode: rw-------
```

```
With groups:
┌──────────────┐     ┌──────────────┐
│    Alice     │     │     Bob      │
│  UID: 1000   │     │  UID: 1001   │
│  GID: 2000   │     │  GID: 2000   │
│ (developers) │     │ (developers) │
└──────────────┘     └──────────────┘
        │                   │
        └─────────┬─────────┘
                  ▼
             project.txt
             owner: alice
             group: developers
             mode: rw-rw----
                   ↑
              Both can access via group!
```

### Setting Up a Shared Project Directory

```bash
# As root, create the shared directory
mkdir /projects/webapp

# Create the group and add users
groupadd -g 2000 webapp-team
usermod -aG webapp-team alice
usermod -aG webapp-team bob
usermod -aG webapp-team charlie

# Set ownership and permissions
chown root:webapp-team /projects/webapp
chmod 2775 /projects/webapp
#     ↑
#     setgid bit - new files inherit group

# Verify
$ ls -ld /projects/webapp
drwxrwsr-x 2 root webapp-team 4096 Feb 15 10:00 /projects/webapp
      ↑
      setgid (s instead of x)
```

### The Complete Shared Directory Setup

```
┌───────────────────────────────────────────────────────────────────────┐
│               SHARED DIRECTORY BEST PRACTICES                         │
├───────────────────────────────────────────────────────────────────────┤
│                                                                       │
│   Directory: /projects/webapp                                         │
│   Owner: root (so users can't delete the directory itself)           │
│   Group: webapp-team                                                  │
│   Mode: 2775 (rwxrwsr-x)                                             │
│                                                                       │
│   Breakdown:                                                          │
│   ┌───────────────────────────────────────────────────────────────┐  │
│   │  2    │  7    │  7    │  5                                    │  │
│   │ setgid│ owner │ group │ other                                 │  │
│   │       │ rwx   │ rwx   │ r-x                                   │  │
│   └───────────────────────────────────────────────────────────────┘  │
│                                                                       │
│   What this achieves:                                                 │
│   • Users in webapp-team can create/modify files                     │
│   • New files automatically get group=webapp-team (setgid)           │
│   • Others can read but not modify                                   │
│                                                                       │
│   For files, also set umask:                                          │
│   $ umask 002   ← files created as rw-rw-r-- (664)                  │
│                   directories as rwxrwxr-x (775)                     │
│                                                                       │
│   Or use ACLs for finer control:                                      │
│   $ setfacl -d -m g:webapp-team:rwx /projects/webapp                 │
│                                                                       │
└───────────────────────────────────────────────────────────────────────┘
```

---

## 8. NFS and Network File Sharing

### How NFS Works with UIDs

NFS trusts UIDs and GIDs directly - there is **no username translation** by default.

```
┌───────────────────────────────────────────────────────────────────────┐
│                         NFS FILE SHARING                               │
├───────────────────────────────────────────────────────────────────────┤
│                                                                       │
│   Server (fileserver)              Client (workstation)               │
│   ┌─────────────────┐              ┌─────────────────┐               │
│   │ alice UID=1000  │              │ alice UID=1000  │  ✓ Match!     │
│   │ bob   UID=1001  │              │ bob   UID=1001  │  ✓ Match!     │
│   └─────────────────┘              └─────────────────┘               │
│           │                                │                          │
│           └────────────NFS─────────────────┘                          │
│                                                                       │
│   File on server: project.txt                                         │
│   Owner UID: 1000, GID: 2000                                         │
│   Mode: rw-rw----                                                     │
│                                                                       │
│   ┌─────────────────────────────────────────────────────────────────┐│
│   │                    NFS Protocol Flow                            ││
│   │                                                                 ││
│   │   Client                              Server                    ││
│   │   ┌──────────────┐                   ┌──────────────┐          ││
│   │   │ alice runs:  │                   │              │          ││
│   │   │ cat project.t│  ──────────────►  │ Receives:    │          ││
│   │   │              │  NFS READ request │ UID=1000     │          ││
│   │   │ Send:        │  with UID=1000   │ GID=1000     │          ││
│   │   │ UID=1000     │  GID=1000        │ Groups=[2000]│          ││
│   │   │ GID=1000     │  Groups=[2000]   │              │          ││
│   │   │ Groups=[2000]│                   │ Checks:      │          ││
│   │   │              │  ◄──────────────  │ 1000==1000?  │          ││
│   │   │ Receives data│  File contents   │ YES, allow   │          ││
│   │   └──────────────┘                   └──────────────┘          ││
│   │                                                                 ││
│   └─────────────────────────────────────────────────────────────────┘│
│                                                                       │
│   KEY: Server trusts whatever UID/GID the client sends!              │
│                                                                       │
└───────────────────────────────────────────────────────────────────────┘
```

### The UID Mismatch Problem

```
┌───────────────────────────────────────────────────────────────────────┐
│                     UID MISMATCH DISASTER                              │
├───────────────────────────────────────────────────────────────────────┤
│                                                                       │
│   Server                              Client                          │
│   ┌──────────────────┐               ┌──────────────────┐            │
│   │ alice   UID=1000 │               │ charlie UID=1000 │ ← PROBLEM! │
│   │ bob     UID=1001 │               │ alice   UID=1002 │            │
│   │ charlie UID=1002 │               │ bob     UID=1001 │ ✓ OK       │
│   └──────────────────┘               └──────────────────┘            │
│                                                                       │
│   What happens:                                                       │
│   ┌─────────────────────────────────────────────────────────────────┐│
│   │                                                                 ││
│   │   charlie on client runs:  cat /nfs/home/alice/secrets.txt     ││
│   │                                                                 ││
│   │   NFS sends: UID=1000 (charlie's UID on client)                ││
│   │                                                                 ││
│   │   Server sees: UID=1000 requesting alice's file                ││
│   │   Server checks: file owner UID=1000, request UID=1000         ││
│   │   Server decides: SAME! Allow access.                          ││
│   │                                                                 ││
│   │   RESULT: charlie can read ALL of alice's files!               ││
│   │                                                                 ││
│   └─────────────────────────────────────────────────────────────────┘│
│                                                                       │
│   Meanwhile, alice on client (UID=1002) CANNOT access her files!     │
│                                                                       │
└───────────────────────────────────────────────────────────────────────┘
```

### Root Squashing

```
┌───────────────────────────────────────────────────────────────────────┐
│                        ROOT SQUASHING                                  │
├───────────────────────────────────────────────────────────────────────┤
│                                                                       │
│   Problem: If NFS trusts UIDs blindly, root on client = root on server│
│   Anyone with root on a client machine can access EVERYTHING!        │
│                                                                       │
│   Solution: ROOT SQUASHING (enabled by default)                       │
│                                                                       │
│   ┌─────────────────────────────────────────────────────────────────┐ │
│   │                                                                 │ │
│   │   Client sends:  UID=0 (root)                                  │ │
│   │                                                                 │ │
│   │   Server maps:   UID=0  →  UID=65534 (nobody)                  │ │
│   │                  GID=0  →  GID=65534 (nogroup)                 │ │
│   │                                                                 │ │
│   │   Effect: root on client becomes "nobody" on server            │ │
│   │           Cannot access files owned by root on server          │ │
│   │                                                                 │ │
│   └─────────────────────────────────────────────────────────────────┘ │
│                                                                       │
│   NFS export configuration (/etc/exports):                            │
│                                                                       │
│   # Default - root is squashed to nobody                              │
│   /exports/shared  192.168.1.0/24(rw,root_squash)                    │
│                                                                       │
│   # Dangerous - trust root on these clients                           │
│   /exports/trusted 192.168.1.10(rw,no_root_squash)                   │
│                                                                       │
│   # Squash ALL users to nobody (very restrictive)                     │
│   /exports/public  *(ro,all_squash)                                  │
│                                                                       │
│   # Map all users to specific UID/GID                                 │
│   /exports/anon    *(rw,all_squash,anonuid=1000,anongid=2000)        │
│                                                                       │
└───────────────────────────────────────────────────────────────────────┘
```

### NFSv4 ID Mapping

```
┌───────────────────────────────────────────────────────────────────────┐
│                      NFSv4 ID MAPPING                                  │
├───────────────────────────────────────────────────────────────────────┤
│                                                                       │
│   NFSv4 can use string identities instead of numeric UIDs!           │
│                                                                       │
│   ┌─────────────────────────────────────────────────────────────────┐ │
│   │                                                                 │ │
│   │   NFSv3: Sends UID 1000                                        │ │
│   │   NFSv4: Sends "alice@example.com"                             │ │
│   │                                                                 │ │
│   │   Server maps "alice@example.com" to local UID                 │ │
│   │   This allows different UIDs on different machines!            │ │
│   │                                                                 │ │
│   └─────────────────────────────────────────────────────────────────┘ │
│                                                                       │
│   Configuration (/etc/idmapd.conf):                                   │
│                                                                       │
│   [General]                                                           │
│   Domain = example.com                                                │
│                                                                       │
│   [Mapping]                                                           │
│   Nobody-User = nobody                                                │
│   Nobody-Group = nogroup                                              │
│                                                                       │
│   Both client and server must have matching domain configuration!    │
│                                                                       │
└───────────────────────────────────────────────────────────────────────┘
```

---

## 9. Centralized Identity Management

### The Problem with Local Users

```
┌───────────────────────────────────────────────────────────────────────┐
│               THE PROBLEM: UID CONSISTENCY                             │
├───────────────────────────────────────────────────────────────────────┤
│                                                                       │
│   With local /etc/passwd on each machine:                             │
│                                                                       │
│   ┌────────────────┐ ┌────────────────┐ ┌────────────────┐           │
│   │   Server 1     │ │   Server 2     │ │   Server 3     │           │
│   │                │ │                │ │                │           │
│   │ alice UID=1000 │ │ alice UID=1001 │ │ alice UID=1000 │           │
│   │ bob   UID=1001 │ │ bob   UID=1000 │ │ bob   UID=1002 │           │
│   └────────────────┘ └────────────────┘ └────────────────┘           │
│          ↑                   ↑                   ↑                    │
│          │                   │                   │                    │
│          └───────────────────┼───────────────────┘                    │
│                              │                                        │
│                    NFS shared storage                                 │
│                              │                                        │
│                        ┌─────▼─────┐                                  │
│                        │  File     │                                  │
│                        │ UID=1000  │                                  │
│                        └───────────┘                                  │
│                                                                       │
│   Who owns this file?                                                 │
│   • On Server 1: alice                                               │
│   • On Server 2: bob (!)                                             │
│   • On Server 3: alice                                               │
│                                                                       │
│   CHAOS!                                                              │
│                                                                       │
└───────────────────────────────────────────────────────────────────────┘
```

### Solutions: Centralized Directory Services

```
┌───────────────────────────────────────────────────────────────────────┐
│             CENTRALIZED IDENTITY SOLUTIONS                             │
├───────────────────────────────────────────────────────────────────────┤
│                                                                       │
│   ┌───────────────────────────────────────────────────────────────┐  │
│   │                    LDAP / Active Directory                     │  │
│   │                                                                │  │
│   │   All user accounts stored centrally:                         │  │
│   │   • alice: UID=10001, GID=10001                               │  │
│   │   • bob:   UID=10002, GID=10002                               │  │
│   │   • developers group: GID=20000                               │  │
│   │                                                                │  │
│   │   All servers query the same source                           │  │
│   │   UIDs are GUARANTEED to be consistent                        │  │
│   │                                                                │  │
│   └───────────────────────────────────────────────────────────────┘  │
│                              │                                        │
│              ┌───────────────┼───────────────┐                        │
│              │               │               │                        │
│              ▼               ▼               ▼                        │
│   ┌────────────────┐ ┌────────────────┐ ┌────────────────┐           │
│   │   Server 1     │ │   Server 2     │ │   Server 3     │           │
│   │                │ │                │ │                │           │
│   │ alice UID=10001│ │ alice UID=10001│ │ alice UID=10001│           │
│   │ bob   UID=10002│ │ bob   UID=10002│ │ bob   UID=10002│           │
│   └────────────────┘ └────────────────┘ └────────────────┘           │
│                                                                       │
│   Common solutions:                                                   │
│   • OpenLDAP + NSS LDAP module                                       │
│   • Microsoft Active Directory + SSSD                                │
│   • FreeIPA (LDAP + Kerberos + DNS)                                  │
│   • NIS/NIS+ (legacy, insecure - avoid)                             │
│                                                                       │
└───────────────────────────────────────────────────────────────────────┘
```

### NSS - Name Service Switch

```
┌───────────────────────────────────────────────────────────────────────┐
│                    NAME SERVICE SWITCH (NSS)                           │
├───────────────────────────────────────────────────────────────────────┤
│                                                                       │
│   /etc/nsswitch.conf controls where the system looks up users:       │
│                                                                       │
│   ┌─────────────────────────────────────────────────────────────────┐ │
│   │   # /etc/nsswitch.conf                                         │ │
│   │                                                                 │ │
│   │   passwd:  files ldap                                          │ │
│   │   group:   files ldap                                          │ │
│   │   shadow:  files ldap                                          │ │
│   │            ─┬──  ─┬──                                          │ │
│   │             │     └── Then check LDAP                          │ │
│   │             └──────── First check /etc/passwd                  │ │
│   │                                                                 │ │
│   └─────────────────────────────────────────────────────────────────┘ │
│                                                                       │
│   How a lookup works:                                                 │
│                                                                       │
│   ┌─────────────────────────────────────────────────────────────────┐ │
│   │                                                                 │ │
│   │   Program calls: getpwnam("alice")                             │ │
│   │         │                                                       │ │
│   │         ▼                                                       │ │
│   │   NSS checks /etc/passwd first                                 │ │
│   │         │                                                       │ │
│   │         │ Not found?                                           │ │
│   │         ▼                                                       │ │
│   │   NSS queries LDAP                                             │ │
│   │         │                                                       │ │
│   │         ▼                                                       │ │
│   │   Returns UID=10001, GID=10001, etc.                          │ │
│   │                                                                 │ │
│   └─────────────────────────────────────────────────────────────────┘ │
│                                                                       │
└───────────────────────────────────────────────────────────────────────┘
```

---

## 10. Kernel Data Structures

### struct cred - Process Credentials in Linux

```
┌───────────────────────────────────────────────────────────────────────┐
│                 KERNEL CREDENTIALS STRUCTURE                           │
├───────────────────────────────────────────────────────────────────────┤
│                                                                       │
│   /* From include/linux/cred.h */                                    │
│                                                                       │
│   struct cred {                                                       │
│       atomic_t    usage;                                              │
│                                                                       │
│       kuid_t      uid;        /* Real UID */                         │
│       kgid_t      gid;        /* Real GID */                         │
│       kuid_t      suid;       /* Saved UID */                        │
│       kgid_t      sgid;       /* Saved GID */                        │
│       kuid_t      euid;       /* Effective UID */                    │
│       kgid_t      egid;       /* Effective GID */                    │
│       kuid_t      fsuid;      /* UID for filesystem access */        │
│       kgid_t      fsgid;      /* GID for filesystem access */        │
│                                                                       │
│       unsigned    securebits;                                         │
│       kernel_cap_t cap_inheritable;  /* Capability sets */           │
│       kernel_cap_t cap_permitted;                                     │
│       kernel_cap_t cap_effective;                                     │
│       kernel_cap_t cap_bset;                                          │
│       kernel_cap_t cap_ambient;                                       │
│                                                                       │
│       struct group_info *group_info;  /* Supplementary groups */     │
│       ...                                                             │
│   };                                                                  │
│                                                                       │
│   ┌─────────────────────────────────────────────────────────────────┐ │
│   │   struct group_info {                                          │ │
│   │       atomic_t   usage;                                        │ │
│   │       int        ngroups;    /* Number of groups */            │ │
│   │       kgid_t     gid[0];     /* Array of group IDs */          │ │
│   │   };                                                            │ │
│   └─────────────────────────────────────────────────────────────────┘ │
│                                                                       │
└───────────────────────────────────────────────────────────────────────┘
```

### Process Credentials Visualization

```
┌───────────────────────────────────────────────────────────────────────┐
│                  PROCESS CREDENTIALS IN MEMORY                         │
├───────────────────────────────────────────────────────────────────────┤
│                                                                       │
│   ┌─────────────────────────────────────────────────────────────────┐ │
│   │                     task_struct                                 │ │
│   │                    (process PCB)                                │ │
│   │                                                                 │ │
│   │   pid:        1234                                              │ │
│   │   comm:       "myprogram"                                       │ │
│   │   state:      RUNNING                                           │ │
│   │   ...                                                           │ │
│   │                         ┌───────────────────────────────────┐   │ │
│   │   cred: ────────────────►  struct cred                      │   │ │
│   │                         │                                   │   │ │
│   │                         │  uid  = 1000                      │   │ │
│   │                         │  gid  = 1000                      │   │ │
│   │                         │  euid = 0     (setuid program)   │   │ │
│   │                         │  egid = 1000                      │   │ │
│   │                         │  suid = 0                         │   │ │
│   │                         │  sgid = 1000                      │   │ │
│   │                         │  fsuid= 0                         │   │ │
│   │                         │  fsgid= 1000                      │   │ │
│   │                         │                                   │   │ │
│   │                         │  group_info ─┐                    │   │ │
│   │                         └──────────────┼────────────────────┘   │ │
│   │                                        │                        │ │
│   │                                        ▼                        │ │
│   │                         ┌───────────────────────────────────┐   │ │
│   │                         │  struct group_info                │   │ │
│   │                         │                                   │   │ │
│   │                         │  ngroups = 3                      │   │ │
│   │                         │  gid[0] = 27   (sudo)            │   │ │
│   │                         │  gid[1] = 999  (docker)          │   │ │
│   │                         │  gid[2] = 2000 (developers)      │   │ │
│   │                         └───────────────────────────────────┘   │ │
│   │                                                                 │ │
│   └─────────────────────────────────────────────────────────────────┘ │
│                                                                       │
└───────────────────────────────────────────────────────────────────────┘
```

---

## 11. System Calls for Credentials

### UID/GID System Calls

```
┌───────────────────────────────────────────────────────────────────────┐
│                   CREDENTIAL SYSTEM CALLS                              │
├───────────────────────────────────────────────────────────────────────┤
│                                                                       │
│   GETTING IDs                                                         │
│   ─────────────────────────────────────────────────────────────────  │
│   getuid()       - Returns real UID                                  │
│   getgid()       - Returns real GID                                  │
│   geteuid()      - Returns effective UID                             │
│   getegid()      - Returns effective GID                             │
│   getresuid()    - Returns real, effective, and saved UID            │
│   getresgid()    - Returns real, effective, and saved GID            │
│   getgroups()    - Returns supplementary group list                   │
│                                                                       │
│   SETTING IDs (requires privilege)                                    │
│   ─────────────────────────────────────────────────────────────────  │
│   setuid(uid)    - Set real, effective, and saved UID                │
│   setgid(gid)    - Set real, effective, and saved GID                │
│   seteuid(euid)  - Set only effective UID                            │
│   setegid(egid)  - Set only effective GID                            │
│   setreuid()     - Set real and effective UID                        │
│   setregid()     - Set real and effective GID                        │
│   setresuid()    - Set real, effective, and saved UID                │
│   setresgid()    - Set real, effective, and saved GID                │
│   setgroups()    - Set supplementary group list (root only)          │
│   initgroups()   - Initialize groups from /etc/group                  │
│                                                                       │
│   setfsuid()     - Set filesystem UID (Linux-specific)               │
│   setfsgid()     - Set filesystem GID (Linux-specific)               │
│                                                                       │
└───────────────────────────────────────────────────────────────────────┘
```

### Example: Dropping Privileges

```c
/* Example: Setuid program that drops privileges */

#include <unistd.h>
#include <sys/types.h>
#include <stdio.h>

int main() {
    /* Started as setuid root */
    printf("Initial: RUID=%d, EUID=%d\n", getuid(), geteuid());
    /* Output: Initial: RUID=1000, EUID=0 */

    /* Do privileged work here (bind to port 80, etc.) */

    /* Temporarily drop privileges */
    if (seteuid(getuid()) < 0) {
        perror("seteuid");
        return 1;
    }
    printf("After seteuid: RUID=%d, EUID=%d\n", getuid(), geteuid());
    /* Output: After seteuid: RUID=1000, EUID=1000 */

    /* Do unprivileged work safely */

    /* Regain privileges if needed */
    if (seteuid(0) < 0) {
        perror("seteuid");
        return 1;
    }
    printf("Regained: RUID=%d, EUID=%d\n", getuid(), geteuid());
    /* Output: Regained: RUID=1000, EUID=0 */

    /* Permanently drop privileges (cannot regain) */
    if (setuid(getuid()) < 0) {
        perror("setuid");
        return 1;
    }
    printf("Permanent: RUID=%d, EUID=%d\n", getuid(), geteuid());
    /* Output: Permanent: RUID=1000, EUID=1000 */

    /* Now SUID is also 1000, cannot become root again */

    return 0;
}
```

---

## 12. Security Considerations

### Setuid Program Pitfalls

```
┌───────────────────────────────────────────────────────────────────────┐
│                 SETUID SECURITY CHECKLIST                              │
├───────────────────────────────────────────────────────────────────────┤
│                                                                       │
│   1. DROP PRIVILEGES EARLY                                            │
│      • Get root work done immediately                                 │
│      • Drop to unprivileged user ASAP                                │
│      • Minimal time running with elevated privileges                 │
│                                                                       │
│   2. DROP ALL PRIVILEGES                                              │
│      • setuid() not just seteuid()                                   │
│      • Clear supplementary groups if needed                          │
│      • Reset environment variables                                   │
│                                                                       │
│   3. VALIDATE INPUTS                                                  │
│      • Never trust user input                                        │
│      • Sanitize paths, filenames                                     │
│      • Avoid system(), popen(), execlp() with user data             │
│                                                                       │
│   4. ENVIRONMENT DANGERS                                              │
│      • Clear LD_PRELOAD, LD_LIBRARY_PATH                             │
│      • Be careful with PATH                                          │
│      • IFS attacks (legacy)                                          │
│                                                                       │
│   5. FILE DESCRIPTOR LEAKS                                            │
│      • Close sensitive FDs before exec()                             │
│      • Use O_CLOEXEC                                                 │
│                                                                       │
└───────────────────────────────────────────────────────────────────────┘
```

### Common Attacks

```
┌───────────────────────────────────────────────────────────────────────┐
│                    COMMON UID/GID ATTACKS                              │
├───────────────────────────────────────────────────────────────────────┤
│                                                                       │
│   1. PRIVILEGE ESCALATION VIA SETUID                                  │
│      • Buffer overflow in setuid program → run as root               │
│      • Race conditions (TOCTOU)                                      │
│      • Symlink attacks                                               │
│                                                                       │
│   2. NFS UID SPOOFING                                                 │
│      • Create user with desired UID on client                        │
│      • Access files on NFS share as that UID                         │
│      • Mitigated by root_squash, Kerberos, NFSv4 sec=krb5           │
│                                                                       │
│   3. CONTAINER BREAKOUT                                               │
│      • User namespaces: root in container = unprivileged outside    │
│      • Misconfigured volumes: host files accessible                  │
│                                                                       │
│   4. GROUP MEMBERSHIP ABUSE                                           │
│      • docker group = effectively root                               │
│      • adm group = read system logs                                  │
│      • Unnecessary group membership = unnecessary access             │
│                                                                       │
└───────────────────────────────────────────────────────────────────────┘
```

---

## 13. Quick Reference: Checking Your IDs

### Command-Line Tools

```bash
# See your IDs (most common command)
$ id
uid=1000(alice) gid=1000(alice) groups=1000(alice),2000(developers),27(sudo)

# See another user's IDs
$ id bob
uid=1001(bob) gid=1001(bob) groups=1001(bob),2000(developers)

# Just the UID
$ id -u
1000

# Just the username
$ id -un
alice

# Just the groups (names)
$ id -Gn
alice developers sudo

# Just the groups (numbers)
$ id -G
1000 2000 27
```

### Checking Process Credentials

```bash
# See process credentials in detail
$ cat /proc/self/status | grep -E '^(Uid|Gid|Groups)'
Uid:    1000    1000    1000    1000   # Real, Effective, Saved, FS
Gid:    1000    1000    1000    1000
Groups: 27 1000 2000

# For a specific process (PID 1234)
$ cat /proc/1234/status | grep -E '^(Uid|Gid|Groups)'

# Using ps to see RUID and EUID
$ ps -o pid,ruid,euid,cmd -p $$
  PID  RUID  EUID CMD
 5678  1000  1000 -bash
```

### File Ownership Commands

```bash
# File ownership (numeric)
$ ls -ln project.txt
-rw-rw---- 1 1000 2000 1024 Feb 15 10:00 project.txt
              ↑    ↑
             UID  GID

# File ownership (names)
$ ls -l project.txt
-rw-rw---- 1 alice developers 1024 Feb 15 10:00 project.txt

# Using stat for detailed info
$ stat project.txt
  File: project.txt
  Size: 1024            Blocks: 8          IO Block: 4096   regular file
Access: (0660/-rw-rw----)  Uid: ( 1000/   alice)   Gid: ( 2000/developers)
...

# Change owner (requires root or ownership)
$ chown alice:developers project.txt

# Change only group
$ chgrp developers project.txt
```

### User and Group Database

```bash
# Look up a user
$ getent passwd alice
alice:x:1000:1000:Alice Smith:/home/alice:/bin/bash

# Look up a group
$ getent group developers
developers:x:2000:alice,bob,charlie

# Look up UID from name
$ id -u alice
1000

# Look up name from UID
$ getent passwd 1000 | cut -d: -f1
alice
```

---

## 14. Summary Tables

### ID Types Quick Reference

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         UID/GID TYPES SUMMARY                           │
├────────────┬────────────────────────────────────────────────────────────┤
│ Type       │ Description                                               │
├────────────┼────────────────────────────────────────────────────────────┤
│ RUID       │ Real UID - who logged in, parent process UID              │
│ EUID       │ Effective UID - used for permission checks                │
│ SUID       │ Saved UID - copy of EUID at exec, for privilege switch    │
│ FSUID      │ Filesystem UID - for file access (Linux only)             │
├────────────┼────────────────────────────────────────────────────────────┤
│ RGID       │ Real GID - primary group at login                         │
│ EGID       │ Effective GID - used for group permission checks          │
│ SGID       │ Saved GID - copy of EGID at exec                          │
│ FSGID      │ Filesystem GID - for file access (Linux only)             │
├────────────┼────────────────────────────────────────────────────────────┤
│ Primary    │ From /etc/passwd - assigned to new files                  │
│ Suppl.     │ From /etc/group - additional access rights                │
└────────────┴────────────────────────────────────────────────────────────┘
```

### Special UIDs and GIDs

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         SPECIAL IDS                                     │
├─────────┬─────────┬─────────────────────────────────────────────────────┤
│ Name    │ UID/GID │ Purpose                                             │
├─────────┼─────────┼─────────────────────────────────────────────────────┤
│ root    │ 0       │ Superuser, bypasses most permission checks          │
│ nobody  │ 65534   │ Unprivileged user, NFS root squash target          │
│ daemon  │ 1       │ System daemons                                      │
│ bin     │ 2       │ Binary file ownership                               │
│ sys     │ 3       │ System files                                        │
├─────────┼─────────┼─────────────────────────────────────────────────────┤
│         │ < 1000  │ Typically reserved for system accounts (varies)    │
│         │ ≥ 1000  │ Normal user accounts                                │
│         │ 65534   │ nobody/nogroup (overflow/NFS squash)               │
└─────────┴─────────┴─────────────────────────────────────────────────────┘
```

### File Permission Bits

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    FILE PERMISSION BITS                                 │
├────────────────┬────────────────────────────────────────────────────────┤
│ Bit            │ Effect                                                 │
├────────────────┼────────────────────────────────────────────────────────┤
│ r (4)          │ Read file / list directory                            │
│ w (2)          │ Write file / create/delete in directory               │
│ x (1)          │ Execute file / traverse directory                     │
├────────────────┼────────────────────────────────────────────────────────┤
│ setuid (4000)  │ Execute with file owner's EUID                        │
│ setgid (2000)  │ Execute with file group's EGID                        │
│                │ On directory: new files inherit directory's GID       │
│ sticky (1000)  │ On directory: only owner can delete files             │
└────────────────┴────────────────────────────────────────────────────────┘

Example:
-rwsr-xr-x  setuid executable (s in user execute position)
-rwxr-sr-x  setgid executable (s in group execute position)
drwxrwsr-x  setgid directory (new files get directory's group)
drwxrwxrwt  sticky directory (only owner can delete own files)
```

### NFS Security Options

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         NFS SECURITY OPTIONS                            │
├──────────────────┬──────────────────────────────────────────────────────┤
│ Option           │ Description                                          │
├──────────────────┼──────────────────────────────────────────────────────┤
│ root_squash      │ Map UID 0 → nobody (default, recommended)           │
│ no_root_squash   │ Allow root access (dangerous!)                       │
│ all_squash       │ Map ALL users → nobody                              │
│ anonuid=N        │ UID to use for squashed users                        │
│ anongid=N        │ GID to use for squashed users                        │
├──────────────────┼──────────────────────────────────────────────────────┤
│ sec=sys          │ Use UID/GID from client (NFSv3 default)             │
│ sec=krb5         │ Kerberos authentication only                         │
│ sec=krb5i        │ Kerberos + integrity checking                        │
│ sec=krb5p        │ Kerberos + privacy (encryption)                      │
└──────────────────┴──────────────────────────────────────────────────────┘
```

---

## 15. The Big Picture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    UID/GID - THE COMPLETE FLOW                          │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│   ┌──────────────────┐                                                  │
│   │   User Logs In   │                                                  │
│   │   (alice)        │                                                  │
│   └────────┬─────────┘                                                  │
│            │                                                            │
│            ▼                                                            │
│   ┌──────────────────┐        ┌──────────────────┐                      │
│   │  /etc/passwd     │        │  /etc/group      │                      │
│   │  alice:x:1000:   │        │  developers:x:   │                      │
│   │  1000:...        │        │  2000:alice,bob  │                      │
│   └────────┬─────────┘        └────────┬─────────┘                      │
│            │                           │                                │
│            └─────────────┬─────────────┘                                │
│                          │                                              │
│                          ▼                                              │
│            ┌──────────────────────────────┐                             │
│            │       Login Process          │                             │
│            │   Sets RUID=1000, RGID=1000  │                             │
│            │   Loads groups: 1000, 2000   │                             │
│            └──────────────┬───────────────┘                             │
│                           │                                             │
│                           ▼                                             │
│            ┌──────────────────────────────┐                             │
│            │     Shell Process (bash)     │                             │
│            │                              │                             │
│            │   RUID=1000   EUID=1000      │                             │
│            │   RGID=1000   EGID=1000      │                             │
│            │   Groups: 1000, 2000         │                             │
│            └──────────────┬───────────────┘                             │
│                           │                                             │
│            ┌──────────────┴───────────────┐                             │
│            │                              │                             │
│            ▼                              ▼                             │
│   ┌─────────────────────┐      ┌─────────────────────┐                  │
│   │  Normal Program     │      │  Setuid Program     │                  │
│   │                     │      │  (e.g., passwd)     │                  │
│   │  RUID=1000          │      │                     │                  │
│   │  EUID=1000          │      │  RUID=1000          │                  │
│   │  (inherits all)     │      │  EUID=0 (from file) │                  │
│   └─────────────────────┘      │  SUID=0             │                  │
│                                └──────────┬──────────┘                  │
│                                           │                             │
│                                           ▼                             │
│                                ┌─────────────────────┐                  │
│                                │  Kernel Permission  │                  │
│                                │      Check          │                  │
│                                │                     │                  │
│                                │  Uses EUID to       │                  │
│                                │  determine access   │                  │
│                                └─────────────────────┘                  │
│                                                                         │
│   ON NFS:                                                               │
│   ┌─────────────────────────────────────────────────────────────────┐   │
│   │                                                                 │   │
│   │   Client                    Server                              │   │
│   │   ┌──────┐    NFS RPC       ┌──────┐                           │   │
│   │   │UID   │  ─────────────▶  │UID   │  Check against           │   │
│   │   │ 1000 │  "open file"     │ 1000 │  file ownership          │   │
│   │   └──────┘  (carries UID)   └──────┘                           │   │
│   │                                                                 │   │
│   │   ⚠ UID must mean the same person on both systems!             │   │
│   │                                                                 │   │
│   └─────────────────────────────────────────────────────────────────┘   │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 16. Key Takeaways

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         KEY INSIGHTS                                    │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│   1. NUMBERS, NOT NAMES                                                 │
│      The kernel works with UID/GID numbers, not usernames.             │
│      Names are a user-space convenience for humans.                     │
│                                                                         │
│   2. REAL vs EFFECTIVE                                                  │
│      RUID = who you really are (for auditing)                          │
│      EUID = what permissions you have (for access control)             │
│                                                                         │
│   3. GROUPS FOR SHARING                                                 │
│      Without groups, you'd have to make files world-readable.          │
│      Groups allow controlled sharing between specific users.            │
│                                                                         │
│   4. SETUID = CONTROLLED PRIVILEGE                                      │
│      Allows normal users to perform specific privileged operations     │
│      (change password, bind to port 80, etc.)                          │
│                                                                         │
│   5. NFS TRUSTS THE CLIENT                                              │
│      NFS (especially v3) trusts whatever UID the client sends.         │
│      UID consistency across systems is CRITICAL.                       │
│                                                                         │
│   6. CENTRALIZE FOR SCALE                                               │
│      Use LDAP/AD for consistent UIDs across multiple systems.          │
│      Manual UID management doesn't scale.                               │
│                                                                         │
│   7. PRINCIPLE OF LEAST PRIVILEGE                                       │
│      Drop privileges as soon as possible.                               │
│      Only grant group membership when necessary.                        │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 17. References

### Books

- Bach, Maurice J. "The Design of the UNIX Operating System." Prentice Hall, 1986.
- Stevens, W. Richard. "Advanced Programming in the UNIX Environment."
  Addison-Wesley, 3rd Edition, 2013.
- Love, Robert. "Linux System Programming." O'Reilly, 2nd Edition, 2013.
- Kerrisk, Michael. "The Linux Programming Interface." No Starch Press, 2010.

### Man Pages

```bash
man 2 getuid      # getuid, geteuid
man 2 setuid      # setuid, seteuid, setreuid, setresuid
man 2 getgroups   # getgroups, setgroups
man 5 passwd      # /etc/passwd format
man 5 group       # /etc/group format
man 7 credentials # Process credentials overview
man 8 exports     # NFS exports configuration
```

### Kernel Source Files (Linux)

```
include/linux/cred.h         # struct cred definition
kernel/cred.c                # Credential management
kernel/sys.c                 # setuid, setgid system calls
fs/nfsd/auth.c               # NFS server authentication
```

### Online Resources

- POSIX.1-2017 specification for credential handling
- Linux kernel documentation: Documentation/security/credentials.rst
- NFS RFC 7530 (NFSv4), RFC 1813 (NFSv3)
- Linux Security Modules (LSM) documentation

---

*Part of the Unix Kernel Internals series - following the style of
Maurice J. Bach's "The Design of the UNIX Operating System"*

