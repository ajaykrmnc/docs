# Strace: The Complete and Comprehensive Guide

## Table of Contents

1. [Introduction](#introduction)
2. [What is Strace?](#what-is-strace)
3. [History and Evolution](#history-and-evolution)
4. [Installation Guide](#installation-guide)
5. [Basic Concepts](#basic-concepts)
6. [System Calls Overview](#system-calls-overview)
7. [Command Line Options Reference](#command-line-options-reference)
8. [Basic Usage Examples](#basic-usage-examples)
9. [Filtering System Calls](#filtering-system-calls)
10. [Output Formatting](#output-formatting)
11. [Advanced Tracing Techniques](#advanced-tracing-techniques)
12. [Performance Analysis](#performance-analysis)
13. [Debugging Applications](#debugging-applications)
14. [Network Debugging](#network-debugging)
15. [File System Analysis](#file-system-analysis)
16. [Process Management Tracing](#process-management-tracing)
17. [Signal Handling](#signal-handling)
18. [Multi-threaded Application Tracing](#multi-threaded-application-tracing)
19. [Container and Docker Debugging](#container-and-docker-debugging)
20. [Security Analysis](#security-analysis)
21. [Integration with Other Tools](#integration-with-other-tools)
22. [Best Practices](#best-practices)
23. [Common Pitfalls and Solutions](#common-pitfalls-and-solutions)
24. [Real-World Use Cases](#real-world-use-cases)
25. [Performance Considerations](#performance-considerations)
26. [Alternatives to Strace](#alternatives-to-strace)
27. [Quick Reference Card](#quick-reference-card)
28. [Appendix A: System Call Categories](#appendix-a-system-call-categories)
29. [Appendix B: Error Codes Reference](#appendix-b-error-codes-reference)
30. [Appendix C: Signal Reference](#appendix-c-signal-reference)

---

## Introduction

Strace is one of the most powerful diagnostic, debugging, and instructional tools available on Linux and
Unix-like operating systems. It is an indispensable utility for system administrators, developers, and
security researchers who need to understand what a program is doing at the system call level.

This comprehensive guide will take you from the basics of strace to advanced techniques used by experienced
system administrators and kernel developers. Whether you're debugging a misbehaving application, analyzing
performance bottlenecks, or conducting security research, this guide will provide you with the knowledge and
practical examples you need.

### Who This Guide Is For

- **System Administrators**: Learn to diagnose application issues, understand resource usage, and troubleshoot
  production problems
- **Software Developers**: Debug your applications, understand library behavior, and optimize system call
  usage
- **Security Researchers**: Analyze application behavior, detect malware, and understand attack vectors
- **Students**: Learn how applications interact with the operating system kernel
- **DevOps Engineers**: Debug containerized applications and understand system-level behavior

### Prerequisites

To get the most out of this guide, you should have:

- Basic familiarity with Linux command line
- Understanding of processes and file descriptors
- Some programming experience (helpful but not required)
- Root or sudo access for some advanced features

---

## What is Strace?

### Definition

Strace (short for "system call trace") is a diagnostic, debugging, and instructional userspace utility for
Linux. It is used to monitor and tamper with interactions between processes and the Linux kernel, which
include system calls, signal deliveries, and changes of process state.

### How Strace Works

At its core, strace uses the `ptrace` system call to attach to a target process and intercept all system calls
made by that process. When a traced process makes a system call, the kernel stops the process and notifies
strace, which can then:

1. **Record the system call name and arguments**
2. **Allow the system call to proceed**
3. **Capture the return value and any errors**
4. **Display or log this information**

```
┌─────────────────────────────────────────────────────────────────┐
│                        User Space                                │
│  ┌──────────────┐         ┌──────────────┐                      │
│  │  Target      │ ptrace  │   strace     │                      │
│  │  Process     │◄───────►│   Process    │                      │
│  └──────────────┘         └──────────────┘                      │
│         │                        │                               │
└─────────┼────────────────────────┼───────────────────────────────┘
│                        │
│ system calls           │ ptrace syscall
▼                        ▼
┌─────────────────────────────────────────────────────────────────┐
│                        Kernel Space                              │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │                    System Call Handler                    │   │
│  └──────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
```

### Key Capabilities

1. **System Call Tracing**: Monitor all system calls made by a process
2. **Signal Tracing**: Track signals sent to and received by processes
3. **Process Attachment**: Attach to already running processes
4. **Child Process Tracing**: Follow forked child processes
5. **Statistics Generation**: Generate timing and call count statistics
6. **Output Filtering**: Filter output by system call type
7. **Fault Injection**: Inject errors into system calls (advanced)

---

## History and Evolution

### Origins

Strace was originally written by Paul Kranenburg for SunOS in 1991. The Linux port was developed by Branko
Lankester, and since then, it has been maintained by various developers in the open-source community.

### Timeline

| Year | Milestone                                    |
| ---- | -------------------------------------------- |
| 1991 | Original strace written for SunOS            |
| 1992 | Linux port by Branko Lankester               |
| 1996 | Wichert Akkerman takes over maintenance      |
| 2002 | Roland McGrath contributes significantly     |
| 2009 | Dmitry Levin becomes primary maintainer      |
| 2011 | Version 4.6 released with major improvements |
| 2014 | Fault injection feature added                |
| 2017 | Version 4.16 with seccomp-bpf support        |
| 2019 | Version 5.0 released                         |
| 2021 | Version 5.12 with enhanced features          |
| 2023 | Continued development and improvements       |

### Version History Highlights

#### Version 4.x Series

- Improved multi-architecture support
- Better handling of 64-bit systems
- Enhanced decoder for complex system calls

#### Version 5.x Series

- Seccomp-based filtering for improved performance
- Better support for new kernel features
- Improved output formatting options
- Enhanced fault injection capabilities

---

## Installation Guide

### Installing on Debian/Ubuntu

```bash
# Update package list
sudo apt update

# Install strace
sudo apt install strace

# Verify installation
strace --version
```

### Installing on RHEL/CentOS/Fedora

```bash
# Using dnf (Fedora, RHEL 8+, CentOS 8+)
sudo dnf install strace

# Using yum (RHEL 7, CentOS 7)
sudo yum install strace

# Verify installation
strace --version
```

### Installing on Arch Linux

```bash
# Using pacman
sudo pacman -S strace

# Verify installation
strace --version
```

### Installing on openSUSE

```bash
# Using zypper
sudo zypper install strace

# Verify installation
strace --version
```

### Installing on Alpine Linux

```bash
# Using apk
sudo apk add strace

# Verify installation
strace --version
```

### Building from Source

For the latest features or when packages are unavailable:

```bash
# Install build dependencies (Debian/Ubuntu)
sudo apt install build-essential autoconf automake git

# Clone the repository
git clone https://github.com/strace/strace.git
cd strace

# Generate configure script
./bootstrap

# Configure the build
./configure --prefix=/usr/local

# Build
make -j$(nproc)

# Install
sudo make install

# Verify installation
/usr/local/bin/strace --version
```

### Verifying Installation

```bash
# Check version
strace --version

# Example output:
# strace -- version 5.19
# Copyright (c) 1991-2022 The strace developers <https://strace.io>.
# This is free software; see the source for copying conditions.  There is NO
# warranty; not even for MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.

# Test basic functionality
strace -e trace=write echo "Hello, World!"
```

---

## Basic Concepts

### Understanding System Calls

System calls (syscalls) are the fundamental interface between user-space applications and the kernel. When a
program needs to perform operations like reading files, allocating memory, or communicating over the network,
it must request these services from the kernel through system calls.

#### The System Call Mechanism

```
┌────────────────────────────────────────────────────────────────────┐
│                        Application Code                             │
│    printf("Hello, World!\n");                                       │
└────────────────────────────────┬───────────────────────────────────┘
│
▼
┌────────────────────────────────────────────────────────────────────┐
│                        C Library (glibc)                            │
│    write(1, "Hello, World!\n", 14);                                 │
└────────────────────────────────┬───────────────────────────────────┘
│
▼
┌────────────────────────────────────────────────────────────────────┐
│                    System Call Interface                            │
│    syscall(SYS_write, 1, "Hello, World!\n", 14);                   │
│    (via software interrupt or SYSCALL instruction)                  │
└────────────────────────────────┬───────────────────────────────────┘
│ User Space
═══════════════════════════════════════════════════════════════════════
│ Kernel Space
▼
┌────────────────────────────────────────────────────────────────────┐
│                        Kernel                                       │
│    sys_write() implementation                                       │
│    - Validate file descriptor                                       │
│    - Copy data from user space                                      │
│    - Write to device/file                                           │
│    - Return bytes written or error                                  │
└────────────────────────────────────────────────────────────────────┘
```

### Process States During Tracing

When strace traces a process, the process alternates between these states:

```
┌─────────────┐     syscall entry     ┌─────────────┐
│   Running   │ ──────────────────► │   Stopped   │
│             │                       │  (traced)   │
└─────────────┘                       └──────┬──────┘
▲                                     │
│         strace continues            │
│◄────────────────────────────────────┘
│
│     syscall exit      ┌─────────────┐
│ ◄──────────────────── │   Stopped   │
│                       │  (traced)   │
│                       └──────┬──────┘
│                              │
└──────────────────────────────┘
strace continues
```

### File Descriptors

File descriptors are integers that represent open files, sockets, pipes, and other I/O resources:

| FD  | Name   | Description              |
| --- | ------ | ------------------------ |
| 0   | stdin  | Standard input           |
| 1   | stdout | Standard output          |
| 2   | stderr | Standard error           |
| 3+  | -      | Other open files/sockets |

### Return Values and Errors

System calls return:

- **Success**: Usually the requested value (e.g., bytes read, file descriptor)
- **Failure**: -1 with errno set to indicate the error

Strace displays errors in parentheses:

```
open("/nonexistent", O_RDONLY) = -1 ENOENT (No such file or directory)
```

---

## System Calls Overview

### Categories of System Calls

Linux has hundreds of system calls, organized into categories:

#### 1. Process Control

| System Call    | Description                        |
| -------------- | ---------------------------------- |
| `fork()`       | Create a child process             |
| `vfork()`      | Create a child process (optimized) |
| `clone()`      | Create a process or thread         |
| `execve()`     | Execute a program                  |
| `exit()`       | Terminate the process              |
| `exit_group()` | Terminate all threads              |
| `wait4()`      | Wait for process termination       |
| `waitpid()`    | Wait for specific process          |
| `getpid()`     | Get process ID                     |
| `getppid()`    | Get parent process ID              |
| `gettid()`     | Get thread ID                      |
| `setpgid()`    | Set process group ID               |
| `setsid()`     | Create a new session               |
| `prctl()`      | Process control operations         |
| `arch_prctl()` | Architecture-specific control      |

#### 2. File Operations

| System Call   | Description                     |
| ------------- | ------------------------------- |
| `open()`      | Open a file                     |
| `openat()`    | Open file relative to directory |
| `close()`     | Close a file descriptor         |
| `read()`      | Read from file descriptor       |
| `write()`     | Write to file descriptor        |
| `lseek()`     | Reposition file offset          |
| `pread64()`   | Read at specific offset         |
| `pwrite64()`  | Write at specific offset        |
| `readv()`     | Read into multiple buffers      |
| `writev()`    | Write from multiple buffers     |
| `dup()`       | Duplicate file descriptor       |
| `dup2()`      | Duplicate to specific FD        |
| `dup3()`      | Duplicate with flags            |
| `fcntl()`     | File control operations         |
| `flock()`     | Apply advisory lock             |
| `fsync()`     | Synchronize file to disk        |
| `fdatasync()` | Synchronize file data           |
| `truncate()`  | Truncate file to length         |
| `ftruncate()` | Truncate FD to length           |

#### 3. File System Operations

| System Call    | Description                  |
| -------------- | ---------------------------- |
| `stat()`       | Get file status              |
| `fstat()`      | Get FD status                |
| `lstat()`      | Get link status              |
| `statx()`      | Extended file status         |
| `access()`     | Check file permissions       |
| `faccessat()`  | Check permissions (relative) |
| `chmod()`      | Change file mode             |
| `fchmod()`     | Change FD mode               |
| `chown()`      | Change file owner            |
| `fchown()`     | Change FD owner              |
| `link()`       | Create hard link             |
| `linkat()`     | Create hard link (relative)  |
| `unlink()`     | Remove file                  |
| `unlinkat()`   | Remove file (relative)       |
| `symlink()`    | Create symbolic link         |
| `symlinkat()`  | Create symlink (relative)    |
| `readlink()`   | Read symbolic link           |
| `readlinkat()` | Read symlink (relative)      |
| `rename()`     | Rename file                  |
| `renameat()`   | Rename file (relative)       |
| `mkdir()`      | Create directory             |
| `mkdirat()`    | Create directory (relative)  |
| `rmdir()`      | Remove directory             |
| `getcwd()`     | Get current directory        |
| `chdir()`      | Change directory             |
| `fchdir()`     | Change to FD directory       |
| `chroot()`     | Change root directory        |
| `mount()`      | Mount filesystem             |
| `umount2()`    | Unmount filesystem           |
| `pivot_root()` | Change root filesystem       |

#### 4. Memory Management

| System Call    | Description                  |
| -------------- | ---------------------------- |
| `brk()`        | Change data segment size     |
| `mmap()`       | Map memory                   |
| `munmap()`     | Unmap memory                 |
| `mremap()`     | Remap memory                 |
| `mprotect()`   | Set memory protection        |
| `madvise()`    | Give memory advice           |
| `mlock()`      | Lock memory pages            |
| `munlock()`    | Unlock memory pages          |
| `mlockall()`   | Lock all memory              |
| `munlockall()` | Unlock all memory            |
| `mincore()`    | Check if pages are resident  |
| `msync()`      | Synchronize memory with file |

#### 5. Network Operations

| System Call     | Description            |
| --------------- | ---------------------- |
| `socket()`      | Create socket          |
| `bind()`        | Bind socket to address |
| `listen()`      | Listen for connections |
| `accept()`      | Accept connection      |
| `accept4()`     | Accept with flags      |
| `connect()`     | Connect to address     |
| `send()`        | Send data              |
| `sendto()`      | Send to address        |
| `sendmsg()`     | Send message           |
| `recv()`        | Receive data           |
| `recvfrom()`    | Receive from address   |
| `recvmsg()`     | Receive message        |
| `shutdown()`    | Shutdown socket        |
| `getsockopt()`  | Get socket option      |
| `setsockopt()`  | Set socket option      |
| `getsockname()` | Get socket address     |
| `getpeername()` | Get peer address       |
| `socketpair()`  | Create socket pair     |

#### 6. Inter-Process Communication

| System Call | Description            |
| ----------- | ---------------------- |
| `pipe()`    | Create pipe            |
| `pipe2()`   | Create pipe with flags |
| `msgget()`  | Get message queue      |
| `msgsnd()`  | Send to message queue  |
| `msgrcv()`  | Receive from queue     |
| `msgctl()`  | Message queue control  |
| `semget()`  | Get semaphore set      |
| `semop()`   | Semaphore operations   |
| `semctl()`  | Semaphore control      |
| `shmget()`  | Get shared memory      |
| `shmat()`   | Attach shared memory   |
| `shmdt()`   | Detach shared memory   |
| `shmctl()`  | Shared memory control  |
| `futex()`   | Fast userspace mutex   |

#### 7. Signal Handling

| System Call        | Description                   |
| ------------------ | ----------------------------- |
| `kill()`           | Send signal                   |
| `tkill()`          | Send signal to thread         |
| `tgkill()`         | Send signal to thread (safe)  |
| `sigaction()`      | Set signal handler            |
| `rt_sigaction()`   | Real-time sigaction           |
| `sigprocmask()`    | Block signals                 |
| `rt_sigprocmask()` | Real-time sigprocmask         |
| `sigpending()`     | Get pending signals           |
| `sigsuspend()`     | Wait for signal               |
| `sigreturn()`      | Return from signal            |
| `signalfd()`       | Create signal file descriptor |
| `signalfd4()`      | signalfd with flags           |

#### 8. Time and Timers

| System Call         | Description                |
| ------------------- | -------------------------- |
| `time()`            | Get time in seconds        |
| `gettimeofday()`    | Get time with microseconds |
| `clock_gettime()`   | Get clock time             |
| `clock_settime()`   | Set clock time             |
| `clock_getres()`    | Get clock resolution       |
| `nanosleep()`       | Sleep with nanoseconds     |
| `clock_nanosleep()` | Sleep on specific clock    |
| `timer_create()`    | Create timer               |
| `timer_settime()`   | Set timer                  |
| `timer_gettime()`   | Get timer                  |
| `timer_delete()`    | Delete timer               |
| `timerfd_create()`  | Create timer FD            |
| `timerfd_settime()` | Set timer FD               |
| `timerfd_gettime()` | Get timer FD               |
| `alarm()`           | Set alarm                  |
| `setitimer()`       | Set interval timer         |
| `getitimer()`       | Get interval timer         |

#### 9. User and Group Management

| System Call   | Description                  |
| ------------- | ---------------------------- |
| `getuid()`    | Get user ID                  |
| `geteuid()`   | Get effective user ID        |
| `setuid()`    | Set user ID                  |
| `setreuid()`  | Set real/effective UID       |
| `setresuid()` | Set real/effective/saved UID |
| `getresuid()` | Get all UIDs                 |
| `getgid()`    | Get group ID                 |
| `getegid()`   | Get effective group ID       |
| `setgid()`    | Set group ID                 |
| `setregid()`  | Set real/effective GID       |
| `setresgid()` | Set all GIDs                 |
| `getresgid()` | Get all GIDs                 |
| `getgroups()` | Get supplementary groups     |
| `setgroups()` | Set supplementary groups     |

#### 10. I/O Multiplexing

| System Call       | Description             |
| ----------------- | ----------------------- |
| `select()`        | Wait on multiple FDs    |
| `pselect6()`      | select with signal mask |
| `poll()`          | Wait for events on FDs  |
| `ppoll()`         | poll with signal mask   |
| `epoll_create()`  | Create epoll instance   |
| `epoll_create1()` | Create with flags       |
| `epoll_ctl()`     | Control epoll instance  |
| `epoll_wait()`    | Wait for epoll events   |
| `epoll_pwait()`   | Wait with signal mask   |

---

## Command Line Options Reference

### General Options

| Option | Long Form                    | Description                                                         |
| ------ | ---------------------------- | ------------------------------------------------------------------- |
| `-c`   | `--summary-only`             | Count time, calls, and errors for each syscall and report a summary |
| `-C`   | `--summary`                  | Like -c but also print regular output while processes are running   |
| `-d`   | `--debug`                    | Show some debugging output of strace itself                         |
| `-f`   | `--follow-forks`             | Follow forks (child processes created by fork/vfork/clone)          |
| `-ff`  |                              | With -o, write traces to filename.pid                               |
| `-F`   |                              | Deprecated, use -f instead                                          |
| `-h`   | `--help`                     | Print help message                                                  |
| `-i`   | `--instruction-pointer`      | Print instruction pointer at time of syscall                        |
| `-k`   | `--stack-traces`             | Print stack trace for each syscall                                  |
| `-q`   | `--quiet`                    | Suppress messages about attaching, detaching, etc.                  |
| `-qq`  | `--quiet=attach,personality` | Suppress messages about process exit status                         |
| `-qqq` | `--quiet=all`                | Suppress all suppressible messages                                  |
| `-r`   | `--relative-timestamps`      | Print relative timestamp per syscall                                |
| `-t`   | `--absolute-timestamps`      | Prefix each line with time of day                                   |
| `-tt`  |                              | Include microseconds                                                |
| `-ttt` |                              | Print time as seconds since epoch                                   |
| `-T`   | `--syscall-times`            | Show time spent in each syscall                                     |
| `-v`   | `--no-abbrev`                | Print unabbreviated versions of strings                             |
| `-V`   | `--version`                  | Print version number                                                |
| `-w`   | `--summary-wall-clock`       | Summarize syscall latency (wall clock)                              |
| `-x`   | `--strings-in-hex`           | Print non-ASCII strings in hex                                      |
| `-xx`  |                              | Print all strings in hex                                            |
| `-X`   | `--const-print-style`        | Set format for printing constants                                   |
| `-y`   | `--decode-fds`               | Print paths for file descriptors                                    |
| `-yy`  |                              | Print protocol-specific info for sockets                            |
| `-Y`   | `--decode-pids`              | Print command names for PIDs                                        |
| `-z`   | `--successful-only`          | Print only successful syscalls                                      |
| `-Z`   | `--failed-only`              | Print only failed syscalls                                          |

### Output Options

| Option        | Description                                       |
| ------------- | ------------------------------------------------- |
| `-o FILE`     | Write output to FILE instead of stderr            |
| `-O OVERHEAD` | Set overhead for timing to OVERHEAD microseconds  |
| `-A`          | Open output file in append mode                   |
| `-S SORTBY`   | Sort syscall counts by: time, calls, errors, name |

### Filtering Options

| Option          | Description                                     |
| --------------- | ----------------------------------------------- |
| `-e EXPR`       | Qualify which events to trace or how to trace   |
| `-e trace=SET`  | Trace only specified syscalls                   |
| `-e trace=!SET` | Trace all syscalls except specified             |
| `-e signal=SET` | Trace only specified signals                    |
| `-e read=SET`   | Dump data read from specified file descriptors  |
| `-e write=SET`  | Dump data written to specified file descriptors |
| `-e fault=SET`  | Inject faults into specified syscalls           |
| `-e inject=SET` | Inject errors/delays into syscalls              |
| `-e status=SET` | Filter by syscall return status                 |

### Process Selection

| Option    | Description                          |
| --------- | ------------------------------------ |
| `-p PID`  | Attach to process with specified PID |
| `-u USER` | Run command as USER                  |

### Tracing Sets for -e trace=

| Set        | Description                                   |
| ---------- | --------------------------------------------- |
| `%file`    | Trace syscalls taking a file name as argument |
| `%process` | Trace process management syscalls             |
| `%network` | Trace network-related syscalls                |
| `%signal`  | Trace signal-related syscalls                 |
| `%ipc`     | Trace IPC-related syscalls                    |
| `%desc`    | Trace file descriptor-related syscalls        |
| `%memory`  | Trace memory mapping syscalls                 |
| `%stat`    | Trace stat syscall variants                   |
| `%lstat`   | Trace lstat syscall variants                  |
| `%fstat`   | Trace fstat syscall variants                  |
| `%statfs`  | Trace statfs-like syscalls                    |
| `%fstatfs` | Trace fstatfs-like syscalls                   |
| `%pure`    | Trace syscalls with no arguments              |
| `%clock`   | Trace clock-related syscalls                  |
| `%creds`   | Trace credential-related syscalls             |

---

## Basic Usage Examples

### Tracing a Command

The simplest form of strace is tracing a command:

```bash
# Trace the 'ls' command
strace ls

# Example output:
execve("/bin/ls", ["ls"], 0x7ffd4e7e3fb0 /* 51 vars */) = 0
brk(NULL)                               = 0x55f9c8a1e000
access("/etc/ld.so.preload", R_OK)      = -1 ENOENT (No such file or directory)
openat(AT_FDCWD, "/etc/ld.so.cache", O_RDONLY|O_CLOEXEC) = 3
fstat(3, {st_mode=S_IFREG|0644, st_size=89195, ...}) = 0
mmap(NULL, 89195, PROT_READ, MAP_PRIVATE, 3, 0) = 0x7f7e3c4e0000
close(3)                                = 0
...
```

### Tracing with Arguments

```bash
# Trace ls with arguments
strace ls -la /tmp

# Trace a program with multiple arguments
strace grep -r "pattern" /path/to/search
```

### Attaching to Running Process

```bash
# Find the PID of the process
pgrep nginx

# Attach to a running process
sudo strace -p 12345

# Attach to multiple processes
sudo strace -p 12345 -p 12346 -p 12347

# Attach and follow forks
sudo strace -f -p 12345
```

### Writing Output to File

```bash
# Write trace to file
strace -o /tmp/trace.log ls -la

# Append to existing file
strace -A -o /tmp/trace.log ls -la

# Separate file per process (with -f)
strace -ff -o /tmp/trace ls -la
# Creates: /tmp/trace.12345, /tmp/trace.12346, etc.
```

### Adding Timestamps

```bash
# Time of day (HH:MM:SS)
strace -t ls
# Output: 14:32:15 openat(AT_FDCWD, ".", ...) = 3

# Time with microseconds
strace -tt ls
# Output: 14:32:15.123456 openat(AT_FDCWD, ".", ...) = 3

# Seconds since epoch
strace -ttt ls
# Output: 1673459535.123456 openat(AT_FDCWD, ".", ...) = 3

# Relative time since previous syscall
strace -r ls
# Output:      0.000000 execve("/bin/ls", ...) = 0
#              0.000234 brk(NULL) = 0x...
```

### Showing System Call Duration

```bash
# Show time spent in each syscall
strace -T ls

# Example output:
openat(AT_FDCWD, ".", O_RDONLY|O_NONBLOCK|O_CLOEXEC|O_DIRECTORY) = 3 <0.000015>
fstat(3, {st_mode=S_IFDIR|0755, st_size=4096, ...}) = 0 <0.000008>
getdents64(3, /* 15 entries */, 32768) = 488 <0.000025>
```

### Generating Statistics

```bash
# Summary statistics only
strace -c ls

# Example output:
% time     seconds  usecs/call     calls    errors syscall
------ ----------- ----------- --------- --------- ----------------
30.77    0.000040          40         1           execve
23.08    0.000030          30         1           write
15.38    0.000020           2        10           close
10.77    0.000014           1        12           mmap
7.69    0.000010           2         4           openat
5.38    0.000007           1         6           fstat
3.85    0.000005           2         3           read
3.08    0.000004           4         1           munmap
------ ----------- ----------- --------- --------- ----------------
100.00    0.000130                    38           total

# Statistics with regular output
strace -C ls

# Sort statistics by time
strace -c -S time ls

# Sort by calls
strace -c -S calls ls

# Sort by errors
strace -c -S errors ls
```

### Decoding File Descriptors

```bash
# Show file paths for file descriptors
strace -y ls

# Example output:
read(3</etc/ld.so.cache>, "\177ELF...", 832) = 832
close(3</etc/ld.so.cache>)              = 0

  # Also show socket/pipe info
  strace -yy nc -l 8080

  # Example output:
  socket(AF_INET, SOCK_STREAM, IPPROTO_TCP) = 3<TCP:[12345]>
  bind(3<TCP:[12345]>, {sa_family=AF_INET, sin_port=htons(8080), ...}, 16) = 0
```

---

## Filtering System Calls

### Trace Specific System Calls

```bash
# Trace only open and close
strace -e trace=open,close ls

# Trace only read and write
strace -e trace=read,write cat /etc/passwd

# Trace only network syscalls
strace -e trace=socket,connect,send,recv curl http://example.com

# Using the short form
strace -e open,close ls
```

### Exclude Specific System Calls

```bash
# Trace everything except mmap and mprotect
strace -e trace=!mmap,mprotect ls

# Exclude common noisy syscalls
strace -e trace=!clock_gettime,gettimeofday,futex ./my_program
```

### Using Syscall Categories

```bash
# Trace all file-related syscalls
strace -e trace=%file ls

# Trace all process-related syscalls
strace -e trace=%process bash -c 'ls; pwd'

# Trace all network syscalls
strace -e trace=%network curl http://example.com

# Trace all memory syscalls
strace -e trace=%memory ./my_program

# Trace all signal syscalls
strace -e trace=%signal ./my_program

# Trace all IPC syscalls
strace -e trace=%ipc ./my_program

# Trace file descriptor syscalls
strace -e trace=%desc cat /etc/passwd

# Combine categories
strace -e trace=%file,%network curl http://example.com/file.txt

# Trace stat variants
strace -e trace=%stat ls -la
```

### Filter by Return Status

```bash
# Only show successful syscalls
strace -z ls

# Only show failed syscalls
strace -Z ls

# Very useful for debugging - shows only failed file operations
strace -Z -e trace=%file ./my_program
```

### Trace Signals

```bash
# Trace only specific signals
strace -e signal=SIGINT,SIGTERM ./my_program

# Exclude signals from output
strace -e signal=!SIGCHLD ./my_program

# Trace all signals (verbose)
strace -e signal=all ./my_program
```

### Dump Read/Write Data

```bash
# Dump data read from stdin (fd 0)
strace -e read=0 cat

# Dump data written to stdout (fd 1)
strace -e write=1 echo "Hello, World!"

# Dump data for multiple fds
strace -e read=0,3 -e write=1,2 ./my_program

# Dump all read data
strace -e read=all cat /etc/passwd

# Example output:
read(3, "\177ELF\2\1\1\3\0\0\0\0\0\0\0\0\3\0>\0\1\0\0\0"..., 832) = 832
| 00000  7f 45 4c 46 02 01 01 03  00 00 00 00 00 00 00 00  .ELF.... ........ |
| 00010  03 00 3e 00 01 00 00 00  50 a3 02 00 00 00 00 00  ..>..... P....... |
```

---

## Output Formatting

### String Output Options

```bash
# Full (unabbreviated) output
strace -v ls
# Shows complete structures instead of {...}

# Show non-ASCII as hex
strace -x ls
# Example: "\x7fELF\x02\x01\x01\x00..."

# Show all strings as hex
strace -xx ls

# Limit string length (default is 32)
strace -s 100 cat /etc/passwd
# Shows up to 100 characters of strings

# Unlimited string length
strace -s 999999 cat /etc/passwd  # Very long
```

### Constant Printing Styles

```bash
# Default style (symbolic names)
strace ls
# Output: openat(AT_FDCWD, ".", O_RDONLY|O_NONBLOCK|O_CLOEXEC|O_DIRECTORY)

# Raw numeric values
strace -X raw ls
# Output: openat(-100, ".", 0x90800)

# Verbose (more details)
strace -X verbose ls

# Abbreviated (shorter names where possible)
strace -X abbrev ls
```

### Quiet Modes

```bash
# Quiet mode - suppress attach/detach messages
strace -q -p 12345

# Quieter - also suppress exit status
strace -qq -p 12345

# Quietest - suppress all suppressible messages
strace -qqq -p 12345
```

### Stack Traces

```bash
# Print stack trace for each syscall (requires debug info)
strace -k ls

# Example output:
openat(AT_FDCWD, "/etc/ld.so.cache", O_RDONLY|O_CLOEXEC) = 3
> /lib/x86_64-linux-gnu/ld-linux-x86-64.so.2(_dl_map_object+0x1a5) [0x158d5]
> /lib/x86_64-linux-gnu/ld-linux-x86-64.so.2(_dl_map_object_deps+0x3e3) [0x16fb3]
> /lib/x86_64-linux-gnu/ld-linux-x86-64.so.2(_dl_load_library+0x203) [0x19da3]
```

### Instruction Pointer

```bash
# Print instruction pointer
strace -i ls

# Example output:
[00007f8a1234abcd] openat(AT_FDCWD, ".", ...) = 3
[00007f8a1234def0] fstat(3, {...}) = 0
```

---

## Advanced Tracing Techniques

### Following Forks

```bash
# Follow child processes
strace -f ls

# Follow and write to separate files
strace -ff -o /tmp/trace ./my_server

# This creates:
# /tmp/trace.12345  (parent)
# /tmp/trace.12346  (child 1)
# /tmp/trace.12347  (child 2)
```

### Tracing Multi-Process Applications

```bash
# Trace shell pipeline
strace -f sh -c 'cat /etc/passwd | grep root | wc -l'

# Trace a script that spawns processes
strace -f ./deploy.sh

# Trace with summary per process
strace -f -c ./multi_process_app
```

### Attaching to All Threads

```bash
# Attach to all threads of a process
strace -f -p $(pgrep -d ' -p ' my_app)

# Or using process group
strace -f -p $(cat /var/run/my_app.pid)
```

### Fault Injection (Error Injection)

Fault injection allows testing error handling by making syscalls fail:

```bash
# Make all open calls fail with ENOENT
strace -e fault=open:error=ENOENT ls

# Fail on the 3rd call
strace -e fault=open:error=ENOENT:when=3 ./my_program

# Fail calls 3-5
strace -e fault=open:error=ENOENT:when=3..5 ./my_program

# Fail every 2nd call starting from 3rd
strace -e fault=open:error=ENOENT:when=3+2 ./my_program

# Inject delay (in microseconds)
strace -e inject=read:delay_enter=100000 cat /etc/passwd
# Adds 100ms delay before each read

# Inject delay after syscall
strace -e inject=write:delay_exit=50000 echo "Hello"

# Combine error and delay
strace -e inject=connect:error=ETIMEDOUT:delay_enter=1000000 curl http://example.com

# Inject signal
strace -e inject=read:signal=SIGINT ./my_program
```

### Conditional Injection

```bash
# Only inject for specific file
strace -e inject=openat:error=EACCES:when=1 \
-e trace=openat \
-P /etc/shadow cat /etc/shadow

# Inject based on return value matching
strace -e inject=read:error=EIO:when=2..4 ./my_program
```

### Path Filtering

```bash
# Trace only syscalls related to specific path
strace -P /etc/passwd cat /etc/passwd

# Multiple paths
strace -P /etc -P /usr ./my_program

# Combine with other filters
strace -P /etc -e trace=%file ./my_program
```

---

## Performance Analysis

### Identifying Performance Bottlenecks

```bash
# Get timing for each syscall
strace -T -o /tmp/perf.log ./slow_program

# Analyze with statistics
strace -c -w ./slow_program

# The -w option uses wall clock time (includes wait time)
# Without -w, it uses CPU time only

# Example output:
% time     seconds  usecs/call     calls    errors syscall
------ ----------- ----------- --------- --------- ----------------
85.23    1.234567      617283         2           nanosleep
8.45    0.122456          12     10204           read
3.21    0.046543           4     11635           write
2.11    0.030567          30      1018         5 openat
1.00    0.014502           7      2071           close
------ ----------- ----------- --------- --------- ----------------
100.00    1.448635                 24930         5 total
```

### Finding Slow System Calls

```bash
# Trace with timing and sort by time
strace -T -o trace.log ./my_program

# Then analyze the log
grep -E '<[0-9]+\.[0-9]+>' trace.log | \
sed 's/.*<\([0-9.]*\)>/\1/' | \
sort -rn | head -20

# Or use awk to find calls taking more than 100ms
awk '/<[0-9.]+>/ {
match($0, /<([0-9.]+)>/, arr);
if (arr[1] > 0.1) print
}' trace.log
```

### I/O Performance Analysis

```bash
# Analyze read/write patterns
strace -e trace=read,write -c ./my_program

# Check for small I/O operations (inefficient)
strace -e trace=read,write -T ./my_program 2>&1 | \
grep -E 'read|write' | \
awk '{print $NF, $0}' | sort -n

# Check buffer sizes
strace -e read,write -v ./my_program 2>&1 | \
grep -oE '(read|write)\([0-9]+, .*, [0-9]+\)' | \
awk -F',' '{print $3}' | sort -n | uniq -c
```

### Network Latency Analysis

```bash
# Trace network with timing
strace -T -e trace=%network curl http://example.com

# Example output showing connection time:
socket(AF_INET, SOCK_STREAM, IPPROTO_TCP) = 3 <0.000012>
connect(3, {sa_family=AF_INET, ...}, 16) = 0 <0.045678>  # 45ms connect
send(3, "GET / HTTP/1.1...", 78, 0) = 78 <0.000034>
recv(3, "HTTP/1.1 200 OK...", 16384, 0) = 1256 <0.123456>  # 123ms response
```

### Memory Allocation Analysis

```bash
# Trace memory-related syscalls
strace -e trace=%memory -c ./my_program

# Look for excessive mmap/munmap
strace -e trace=mmap,munmap,brk -c ./my_program

# Detailed memory operations
strace -e trace=%memory -v ./my_program 2>&1 | \
grep mmap | wc -l
```

---

## Debugging Applications

### Finding Missing Files

```bash
# Show only failed file operations
strace -Z -e trace=%file ./my_program

# Example output:
openat(AT_FDCWD, "/etc/myapp/config.yaml", O_RDONLY) = -1 ENOENT (No such file or directory)
access("/usr/lib/myapp/plugin.so", F_OK) = -1 ENOENT (No such file or directory)
```

### Finding Library Loading Issues

```bash
# Trace library loading
strace -e trace=openat,access ./my_program 2>&1 | grep -E '\.so'

# Check for library search paths
strace -e trace=openat ./my_program 2>&1 | grep 'ld.so\|\.so'

# Example output showing library search:
openat(AT_FDCWD, "/lib/x86_64-linux-gnu/tls/x86_64/libfoo.so", ...) = -1 ENOENT
openat(AT_FDCWD, "/lib/x86_64-linux-gnu/tls/libfoo.so", ...) = -1 ENOENT
openat(AT_FDCWD, "/lib/x86_64-linux-gnu/x86_64/libfoo.so", ...) = -1 ENOENT
openat(AT_FDCWD, "/lib/x86_64-linux-gnu/libfoo.so", ...) = 3
```

### Debugging Startup Issues

```bash
# Trace program initialization
strace -f -o startup.log ./my_program

# Check what environment variables are read
strace -e trace=openat ./my_program 2>&1 | grep -E 'environ|getenv'

# Trace configuration file reading
strace -e trace=read -s 1000 ./my_program 2>&1 | grep -A1 'config'
```

### Debugging Hangs

```bash
# Attach to hanging process
sudo strace -p $(pgrep hanging_process)

# Common causes of hangs:
# - futex(..., FUTEX_WAIT, ...) - waiting for lock
# - read(socket_fd, ...) - waiting for network data
# - poll/epoll_wait - waiting for events
# - nanosleep - sleeping

# Check what a hung process is waiting for
cat /proc/$(pgrep hanging_process)/stack
cat /proc/$(pgrep hanging_process)/wchan
```

### Debugging Permission Issues

```bash
# Find permission denials
strace -Z -e trace=%file ./my_program 2>&1 | grep -E 'EACCES|EPERM'

# Check actual permission checks
strace -e trace=access,faccessat ./my_program

# Example output:
access("/etc/shadow", R_OK) = -1 EACCES (Permission denied)
faccessat(AT_FDCWD, "/var/run/myapp.pid", W_OK) = -1 EACCES (Permission denied)
```

### Debugging Crash Issues

```bash
# Trace until crash and capture full output
strace -f -o crash.log ./crashing_program

# Look for the last syscall before crash
tail -50 crash.log

# Check for signal delivery
grep -E 'SIGSEGV|SIGABRT|SIGBUS|SIGFPE' crash.log

# Trace with stack traces for crash analysis
strace -k -f ./crashing_program
```

---

## Network Debugging

### Tracing Socket Operations

```bash
# Basic socket tracing
strace -e trace=%network ./network_app

# Detailed socket tracing with data
strace -e trace=%network -e read=all -e write=all ./network_app

# Show socket details
strace -yy -e trace=%network ./network_app
```

### HTTP Client Debugging

```bash
# Trace curl request
strace -e trace=%network -s 1000 curl http://example.com

# See the HTTP conversation
strace -e trace=sendto,recvfrom,read,write -s 10000 curl http://example.com

# Check DNS resolution
strace -e trace=%network curl http://example.com 2>&1 | grep -E 'connect|sendto|recvfrom'
```

### TCP Connection Analysis

```bash
# Trace TCP connection establishment
strace -e trace=socket,connect,bind,listen,accept -yy ./tcp_server

# Example output:
socket(AF_INET, SOCK_STREAM, IPPROTO_TCP) = 3<TCP:[12345]>
setsockopt(3<TCP:[12345]>, SOL_SOCKET, SO_REUSEADDR, [1], 4) = 0
bind(3<TCP:[12345]>, {sa_family=AF_INET, sin_port=htons(8080), sin_addr=inet_addr("0.0.0.0")}, 16) = 0
listen(3<TCP:[12345]>, 128) = 0
accept4(3<TCP:[12345]>, {sa_family=AF_INET, sin_port=htons(54321), sin_addr=inet_addr("192.168.1.100")}, ...)
= 4<TCP:[12345->192.168.1.100:54321]>
```

### UDP Analysis

```bash
# Trace UDP communication
strace -e trace=socket,bind,sendto,recvfrom -yy ./udp_app

# DNS query tracing (uses UDP)
strace -e trace=%network dig example.com
```

### Connection Timeout Debugging

```bash
# Trace with timing to see connection delays
strace -T -e trace=connect,poll,select ./network_app

# Identify slow connections
strace -T -e trace=connect ./network_app 2>&1 | \
awk '/<[0-9.]+>/ {
match($0, /<([0-9.]+)>/, t);
if (t[1] > 1.0) print "SLOW:", $0
}'
```

### SSL/TLS Debugging

```bash
# SSL handshake involves many read/write syscalls
strace -e trace=read,write -s 100 -yy curl https://example.com

# Note: strace cannot see decrypted data, only encrypted bytes
# For SSL debugging, use ssldump or wireshark instead
```

---

## File System Analysis

### Tracing File Access Patterns

```bash
# All file operations
strace -e trace=%file ./my_program

# Specific file operations
strace -e trace=open,openat,close,read,write,stat ./my_program

# With timing
strace -T -e trace=%file ./my_program
```

### Finding Configuration Files

```bash
# What config files does an app read?
strace -e trace=openat,open ./my_app 2>&1 | grep -v ENOENT

# Including failed attempts
strace -e trace=openat,open ./my_app 2>&1 | grep -E '\.(conf|cfg|yaml|yml|json|ini)'
```

### Analyzing Write Patterns

```bash
# What files are modified?
strace -e trace=openat,open,write,rename,unlink ./my_app 2>&1 | \
grep -E 'O_WRONLY|O_RDWR|write\(|rename|unlink'

# Track file descriptor to path mapping
strace -y -e trace=write ./my_app
```

### Directory Operations

```bash
# Trace directory operations
strace -e trace=mkdir,rmdir,getdents,getdents64,chdir,getcwd ./my_app

# Find recursive directory scans
strace -e trace=openat,getdents64 find /var -name "*.log" 2>&1 | head -100
```

### Temporary File Usage

```bash
# Trace temp file creation
strace -e trace=openat,open,mkstemp,mkostemp ./my_app 2>&1 | grep -E '/tmp|/var/tmp|O_TMPFILE'

# Monitor temp directory usage
strace -P /tmp -P /var/tmp ./my_app
```

### File Locking Analysis

```bash
# Trace file locking
strace -e trace=flock,fcntl ./my_app 2>&1 | grep -E 'LOCK|F_SETLK|F_GETLK'

# Example output:
flock(3, LOCK_EX) = 0
fcntl(4, F_SETLK, {l_type=F_WRLCK, l_whence=SEEK_SET, l_start=0, l_len=0}) = 0
```

---

## Process Management Tracing

### Tracing Process Creation

```bash
# Trace fork/exec
strace -f -e trace=%process ./my_script.sh

# Example output:
clone(child_stack=NULL, flags=CLONE_CHILD_CLEARTID|CLONE_CHILD_SETTID|SIGCHLD, ...) = 12346
[pid 12346] execve("/bin/ls", ["ls", "-la"], ...) = 0
```

### Tracing Process Exit

```bash
# See exit codes
strace -e trace=exit,exit_group ./my_program

# With wait status
strace -f -e trace=exit,exit_group,wait4,waitpid ./my_script.sh
```

### Thread Creation

```bash
# Trace thread creation
strace -f -e trace=clone ./multi_threaded_app

# pthread_create uses clone with CLONE_THREAD flag
# Example output:
clone(child_stack=0x7f1234567890, flags=CLONE_VM|CLONE_FS|CLONE_FILES|CLONE_SIGHAND|CLONE_THREAD|...) = 12347
```

### Process Credentials

```bash
# Trace credential changes
strace -e trace=%creds ./setuid_program

# Example syscalls:
# getuid, geteuid, setuid, setreuid, setresuid
# getgid, getegid, setgid, setregid, setresgid
# getgroups, setgroups
# capget, capset
```

---

## Signal Handling

### Tracing Signal Delivery

```bash
# Trace all signals
strace -e signal=all ./my_program

# Trace specific signals
strace -e signal=SIGTERM,SIGINT,SIGHUP ./daemon

# Example output showing signal delivery:
--- SIGTERM {si_signo=SIGTERM, si_code=SI_USER, si_pid=1234, si_uid=1000} ---
rt_sigreturn({mask=[]}) = 0
```

### Signal Handler Installation

```bash
# Trace signal handler setup
strace -e trace=rt_sigaction,sigaction ./my_program

# Example output:
rt_sigaction(SIGINT, {sa_handler=0x4005f0, sa_mask=[INT], sa_flags=SA_RESTORER|SA_RESTART,
  sa_restorer=0x7f...}, ...) = 0
rt_sigaction(SIGTERM, {sa_handler=0x4005f0, sa_mask=[TERM], sa_flags=SA_RESTORER|SA_RESTART,
  sa_restorer=0x7f...}, ...) = 0
```

### Signal Masking

```bash
# Trace signal mask operations
strace -e trace=rt_sigprocmask,sigprocmask ./my_program

# Example output:
rt_sigprocmask(SIG_BLOCK, [CHLD], [], 8) = 0
rt_sigprocmask(SIG_SETMASK, [], NULL, 8) = 0
```

### Signal-Related Debugging

```bash
# Debug signal-related issues
strace -e signal=all -e trace=%signal ./my_program

# Common signal-related syscalls:
# rt_sigaction - install handler
# rt_sigprocmask - block/unblock
# rt_sigsuspend - wait for signal
# kill/tgkill - send signal
# signalfd - receive signals via fd
```

---

## Multi-threaded Application Tracing

### Basic Multi-thread Tracing

```bash
# Always use -f for multi-threaded apps
strace -f ./multi_threaded_app

# Output shows thread IDs:
[pid 12345] futex(0x7f..., FUTEX_WAIT_PRIVATE, ...) = 0
[pid 12346] write(1, "Hello from thread 1\n", 20) = 20
[pid 12347] write(1, "Hello from thread 2\n", 20) = 20
```

### Separating Thread Output

```bash
# Write each thread to separate file
strace -ff -o /tmp/threads ./multi_threaded_app

# Creates:
# /tmp/threads.12345 (main thread)
# /tmp/threads.12346 (thread 1)
# /tmp/threads.12347 (thread 2)
```

### Thread Synchronization Analysis

```bash
# Trace mutex/condition variable operations
strace -f -e trace=futex ./multi_threaded_app

# Common futex operations:
# FUTEX_WAIT - thread is waiting
# FUTEX_WAKE - thread is waking others
# FUTEX_WAIT_PRIVATE - optimized wait
# FUTEX_WAKE_PRIVATE - optimized wake
```

### Identifying Lock Contention

```bash
# Look for threads waiting on futex
strace -f -T -e trace=futex ./multi_threaded_app 2>&1 | \
grep FUTEX_WAIT | \
awk '/<[0-9.]+>/ {
match($0, /<([0-9.]+)>/, t);
if (t[1] > 0.001) print "CONTENTION:", $0
}'
```

### Thread Pool Analysis

```bash
# See thread creation and work distribution
strace -f -e trace=clone,futex ./thread_pool_app 2>&1 | \
grep -E 'clone|FUTEX_WAKE'
```

---

## Container and Docker Debugging

### Tracing Inside Containers

```bash
# Docker: trace a container process from host
docker inspect --format '{{.State.Pid}}' container_name
sudo strace -p <container_pid>

# Run command inside container with strace
docker run --cap-add=SYS_PTRACE image_name strace ls

# Docker Compose with ptrace capability
# In docker-compose.yml:
# cap_add:
#   - SYS_PTRACE
```

### Tracing Container Startup

```bash
# Trace container entrypoint
docker run --cap-add=SYS_PTRACE my_image strace -f /entrypoint.sh

# Debug container that won't start
docker run --cap-add=SYS_PTRACE --entrypoint strace my_image -f /original/entrypoint
```

### Podman Tracing

```bash
# Similar to Docker
podman run --cap-add=SYS_PTRACE image_name strace command

# Attach to running container
podman inspect --format '{{.State.Pid}}' container_name
sudo strace -p <pid>
```

### Kubernetes Pod Tracing

```bash
# First, get the container PID on the node
kubectl debug pod/my-pod -it --image=ubuntu --target=my-container

# Or use ephemeral containers (K8s 1.23+)
kubectl debug -it pod/my-pod --image=busybox --target=my-container

# From the node (requires privileged access):
crictl inspect <container_id> | jq '.info.pid'
sudo strace -p <pid>
```

### Debugging Container Networking

```bash
# Trace network syscalls in container
docker run --cap-add=SYS_PTRACE my_image \
strace -e trace=%network -f /app

# Check for network namespace issues
strace -e trace=socket,connect,bind ./app 2>&1 | grep -E 'ECONNREFUSED|ENETUNREACH'
```

### Container File System Issues

```bash
# Trace file access in container
docker run --cap-add=SYS_PTRACE my_image \
strace -e trace=%file -f /app

# Check for permission issues with volumes
strace -Z -e trace=%file ./app 2>&1 | grep EACCES
```

---

## Security Analysis

### Analyzing System Call Patterns

```bash
# Get complete syscall profile of an application
strace -c -f ./my_app

# This helps in:
# - Creating seccomp profiles
# - Understanding attack surface
# - Auditing application behavior
```

### Creating Seccomp Profiles

```bash
# Step 1: Trace all syscalls
strace -f -o trace.log ./my_app

# Step 2: Extract unique syscalls
grep -oE '^[a-z_0-9]+\(' trace.log | tr -d '(' | sort -u > syscalls.txt

# Step 3: Create seccomp profile based on syscalls
# Use the list to create Docker seccomp profile or systemd seccomp filter
```

### Detecting Suspicious Behavior

```bash
# Look for privilege escalation attempts
strace -e trace=setuid,setgid,setreuid,setregid,setresuid,setresgid ./untrusted_app

# Check for unexpected network activity
strace -e trace=%network ./untrusted_app

# Monitor file access
strace -e trace=%file ./untrusted_app

# Look for process injection
strace -e trace=ptrace,process_vm_readv,process_vm_writev ./untrusted_app
```

### Malware Analysis

```bash
# Comprehensive trace for malware analysis
strace -f -o malware.log \
-e trace=%file,%process,%network \
-e signal=all \
-s 1000 \
-yy \
./suspicious_binary

# Common malware behaviors to look for:
# - Opening /etc/passwd, /etc/shadow
# - Connecting to unknown IPs
# - Creating files in /tmp
# - Modifying system files
# - Process injection via ptrace
```

### Audit Trail Generation

```bash
# Generate detailed audit trail
strace -f -tt -T -o audit.log \
-e trace=all \
./audited_application

# Include stack traces for forensics
strace -f -k -tt -o forensic.log ./application
```

---

## Integration with Other Tools

### Combining with ltrace

```bash
# strace traces syscalls, ltrace traces library calls
# Use both for complete picture

# Trace syscalls
strace -o syscalls.log ./my_app &
# Trace library calls
ltrace -o libcalls.log ./my_app &

# Or combine outputs
{ strace ./my_app 2>&1 & ltrace ./my_app 2>&1; } | tee combined.log
```

### Integration with perf

```bash
# Use strace for syscall info, perf for performance
strace -c ./my_app  # syscall breakdown
perf stat ./my_app  # CPU performance counters

# perf trace is similar to strace but lower overhead
perf trace ./my_app
perf trace -s ./my_app  # summary mode
```

### Using with gdb

```bash
# Start program under gdb with strace
gdb -ex "set exec-wrapper strace -o trace.log" ./my_app

# Or trace gdb-controlled program
gdb ./my_app
(gdb) shell strace -p <pid from another terminal>
```

### With valgrind

```bash
# Note: strace + valgrind together is complex
# Valgrind intercepts syscalls, strace traces them

# Better approach: use them separately
valgrind ./my_app 2> valgrind.log
strace -o strace.log ./my_app
```

### With tcpdump/Wireshark

```bash
# For network debugging, combine strace and tcpdump
# Terminal 1: packet capture
sudo tcpdump -i any -w capture.pcap port 8080

# Terminal 2: syscall trace
strace -e trace=%network -yy ./my_app

# Then analyze capture.pcap with Wireshark
```

### With systemd

```bash
# Trace systemd service
sudo strace -f -p $(systemctl show -p MainPID my.service --value)

# Add strace to service execution
# In /etc/systemd/system/my.service.d/override.conf:
# [Service]
# ExecStart=
# ExecStart=/usr/bin/strace -f -o /var/log/my-service-trace.log /original/command
```

---

## Best Practices

### 1. Always Use Output Files in Production

```bash
# DON'T: Output to terminal in production (can flood console)
strace -p 12345

# DO: Write to file
strace -o /var/log/strace/app.log -p 12345

# With rotation consideration
strace -o /var/log/strace/app-$(date +%Y%m%d-%H%M%S).log -p 12345
```

### 2. Limit Scope with Filters

```bash
# DON'T: Trace everything (overwhelming output)
strace ./my_app

# DO: Trace only what you need
strace -e trace=%file ./my_app        # File issues
strace -e trace=%network ./my_app      # Network issues
strace -e trace=%process ./my_app      # Process issues
```

### 3. Use Timestamps for Correlation

```bash
# Always use timestamps in production debugging
strace -tt -T -o trace.log ./my_app

# -tt: Absolute time with microseconds
# -T: Duration of each syscall
```

### 4. Be Aware of Performance Impact

```bash
# Strace adds significant overhead (10-100x slowdown)
# For production, consider:

# 1. Trace briefly and detach
timeout 30 strace -p 12345 -o trace.log

# 2. Use filtering to reduce overhead
strace -e trace=openat,read,write -p 12345

# 3. Consider perf trace for lower overhead
perf trace -p 12345
```

### 5. Handle Multi-process Applications Correctly

```bash
# Always use -f for daemons and servers
strace -f ./daemon

# Use -ff with -o for separate files
strace -ff -o /tmp/trace ./daemon
```

### 6. Secure Your Trace Files

```bash
# Trace files may contain sensitive data!
strace -o trace.log ./my_app
chmod 600 trace.log

# Don't leave trace files in production
rm -f trace.log  # After analysis
```

### 7. Use Quiet Mode When Appropriate

```bash
# Suppress attach/detach messages
strace -q -p 12345

# For scripts that parse output
strace -qqq -e trace=openat ./my_app 2>&1 | parse_script.sh
```

### 8. Combine with Logging

```bash
# Correlate strace with application logs
strace -tt -o strace.log ./my_app 2>&1 | tee app.log

# Then correlate timestamps between strace.log and app.log
```

---

## Common Pitfalls and Solutions

### Pitfall 1: "Operation not permitted" Error

```bash
# Problem:
strace -p 12345
strace: attach: ptrace(PTRACE_SEIZE, 12345): Operation not permitted

# Solutions:

# 1. Use sudo
sudo strace -p 12345

# 2. Allow ptrace in containers
docker run --cap-add=SYS_PTRACE ...

# 3. Adjust ptrace_scope (temporary)
echo 0 | sudo tee /proc/sys/kernel/yama/ptrace_scope

# 4. Or permanently in /etc/sysctl.conf:
# kernel.yama.ptrace_scope = 0
```

### Pitfall 2: Too Much Output

```bash
# Problem: Output is overwhelming

# Solutions:

# 1. Filter by syscall category
strace -e trace=%file ./my_app

# 2. Filter by specific syscalls
strace -e trace=open,read,write ./my_app

# 3. Show only failures
strace -Z ./my_app

# 4. Get summary instead of detailed output
strace -c ./my_app
```

### Pitfall 3: Truncated String Output

```bash
# Problem: Strings are cut off with "..."
read(3, "This is a long string that ge"..., 4096) = 4096

# Solution: Increase string length
strace -s 1000 ./my_app    # Show up to 1000 chars
strace -s 99999 ./my_app   # Show very long strings
```

### Pitfall 4: Missing Child Process Traces

```bash
# Problem: Not seeing child process syscalls

# Solution: Use -f to follow forks
strace -f ./my_script.sh

# For separate files per process
strace -ff -o /tmp/trace ./my_script.sh
```

### Pitfall 5: Strace Changing Timing/Behavior

```bash
# Problem: Bug disappears when using strace (Heisenbug)

# Solutions:

# 1. Use less invasive tracing
strace -e trace=none ./my_app  # Just attach, no tracing

# 2. Use perf trace instead (lower overhead)
perf trace ./my_app

# 3. Trace specific syscalls only
strace -e trace=futex ./my_app

# 4. Add delays to match strace overhead
# In code: usleep(1000) at problematic points
```

### Pitfall 6: Binary Data in Output

```bash
# Problem: Binary data makes output hard to read

# Solutions:

# 1. Show as hex
strace -x ./my_app     # Non-ASCII as hex
strace -xx ./my_app    # All strings as hex

# 2. Limit string length
strace -s 32 ./my_app

# 3. Filter to specific syscalls
strace -e trace=openat,close ./my_app
```

### Pitfall 7: setuid Programs

```bash
# Problem: Can't trace setuid binaries

# This is a security feature. Workarounds:

# 1. Run as root
sudo strace ./setuid_binary

# 2. Copy and remove setuid bit (for testing only)
cp /usr/bin/sudo /tmp/sudo_copy
chmod u-s /tmp/sudo_copy
strace /tmp/sudo_copy
```

---

## Real-World Use Cases

### Use Case 1: Debug Slow Application Startup

```bash
# Scenario: Application takes 30 seconds to start

# Step 1: Trace with timing
strace -T -o startup.log ./slow_app

# Step 2: Find slow syscalls
awk '/<[0-9.]+>/ {
match($0, /<([0-9.]+)>/, t);
if (t[1] > 0.1) print t[1], $0
}' startup.log | sort -rn | head -20

# Step 3: Common findings:
# - DNS lookups (getaddrinfo via socket calls)
# - Slow file system access
# - Connection timeouts
# - Lock contention (futex waits)
```

### Use Case 2: Find Missing Configuration File

```bash
# Scenario: App fails with "configuration not found"

strace -e trace=openat,access -Z ./my_app 2>&1 | grep -E 'config|conf|cfg|yaml|json'

# Output shows which paths were tried:
openat(AT_FDCWD, "/etc/myapp/config.yaml", O_RDONLY) = -1 ENOENT
openat(AT_FDCWD, "/home/user/.myapp/config.yaml", O_RDONLY) = -1 ENOENT
openat(AT_FDCWD, "./config.yaml", O_RDONLY) = -1 ENOENT
```

### Use Case 3: Debug Network Connection Issues

```bash
# Scenario: App can't connect to database

strace -e trace=%network -T ./my_app 2>&1 | grep -E 'connect|socket'

# Look for:
connect(3, {sa_family=AF_INET, sin_port=htons(5432), sin_addr=inet_addr("10.0.0.5")}, 16) = -1 ETIMEDOUT

# This tells you:
# - Target IP and port
# - Error type (timeout, refused, unreachable)
```

### Use Case 4: Debug Permission Denied Errors

```bash
# Scenario: App fails with "permission denied" but unclear which file

strace -Z -e trace=%file ./my_app 2>&1 | grep -E 'EACCES|EPERM'

# Output:
openat(AT_FDCWD, "/var/lib/myapp/data.db", O_RDWR) = -1 EACCES
# Now you know exactly which file needs permission fix
```

### Use Case 5: Understand What a Command Does

```bash
# Scenario: Curious what "ls -la" actually does

strace ls -la 2>&1 | head -50

# You learn:
# - How dynamic linker loads libraries
# - How directory is opened and read
# - How stat is called for each entry
# - How output is formatted and written
```

### Use Case 6: Debug Docker Container That Won't Start

```bash
# Scenario: Container exits immediately with code 1

docker run --cap-add=SYS_PTRACE --entrypoint "" my-image \
strace -f -o /dev/stderr /original/entrypoint.sh

# Look for:
# - Missing files (ENOENT)
# - Permission issues (EACCES)
# - Exec failures (execve returning -1)
```

### Use Case 7: Analyze Application Security

```bash
# Scenario: Security audit of third-party binary

# Create comprehensive trace
strace -f -o security_audit.log \
-e trace=all \
-e signal=all \
-yy -s 1000 \
./third_party_app

# Check for concerning syscalls:
grep -E 'ptrace|execve|chmod.*777|chown.*0|setuid|connect' security_audit.log
```

### Use Case 8: Debug Memory Issues

```bash
# Scenario: Application using too much memory

strace -e trace=%memory -c ./memory_hog

# Look for:
# - Excessive mmap calls
# - Growing brk values
# - Missing munmap calls

# Detailed analysis
strace -e trace=mmap,munmap,brk -T ./memory_hog 2>&1 | \
awk '/mmap.*PROT_READ\|PROT_WRITE/ { total += $NF } END { print "Total mmap:", total }'
```

---

## Performance Considerations

### Overhead of strace

Strace uses ptrace, which causes significant overhead:

| Scenario                | Approximate Slowdown |
| ----------------------- | -------------------- |
| Trace all syscalls      | 10x - 100x           |
| Trace specific syscalls | 5x - 50x             |
| Trace with -c (summary) | 5x - 20x             |
| Attach without tracing  | 2x - 5x              |

### Reducing Overhead

```bash
# 1. Filter to only needed syscalls
strace -e trace=openat ./my_app    # Much faster than tracing all

# 2. Use summary mode for statistics
strace -c ./my_app    # Lower overhead than detailed trace

# 3. Sample instead of continuous trace
timeout 5 strace -p 12345    # Trace for only 5 seconds

# 4. Use perf trace for lower overhead
perf trace ./my_app    # 2-5x less overhead than strace
```

### When Not to Use strace

- **High-frequency trading systems**: Overhead is unacceptable
- **Real-time systems**: Can cause timing failures
- **Production load testing**: Results won't be realistic
- **Long-running traces of busy systems**: Log files grow very large

### Alternatives with Lower Overhead

```bash
# perf trace - eBPF-based, lower overhead
perf trace ./my_app
perf trace -p 12345

# bpftrace - Custom eBPF tracing
sudo bpftrace -e 'tracepoint:syscalls:sys_enter_openat { printf("%s\n", str(args->filename)); }'

# ftrace - Kernel tracing
echo 1 > /sys/kernel/debug/tracing/events/syscalls/sys_enter_openat/enable
cat /sys/kernel/debug/tracing/trace_pipe
```

---

## Alternatives to Strace

### ltrace

Traces library calls instead of system calls:

```bash
# Trace library calls
ltrace ./my_app

# Example output:
printf("Hello, World!\n") = 14
malloc(1024) = 0x5555556032a0
free(0x5555556032a0) = <void>
```

### perf trace

Lower overhead syscall tracing using eBPF:

```bash
# Basic usage
perf trace ./my_app

# Summary mode
perf trace -s ./my_app

# Trace specific syscalls
perf trace -e openat,read,write ./my_app

# Attach to running process
perf trace -p 12345
```

### bpftrace

Flexible eBPF-based tracing:

```bash
# Trace openat syscalls
sudo bpftrace -e 'tracepoint:syscalls:sys_enter_openat { printf("%s %s\n", comm, str(args->filename)); }'

# Trace with timing
sudo bpftrace -e 'tracepoint:syscalls:sys_enter_* { @start[tid] = nsecs; }
tracepoint:syscalls:sys_exit_* /@start[tid]/ { @latency = hist(nsecs - @start[tid]); delete(@start[tid]); }'
```

### sysdig

Container-aware system monitoring:

```bash
# Trace file opens
sysdig evt.type=openat

# Filter by container
sysdig container.name=my-container

# Chisels (pre-built analysis scripts)
sysdig -c topfiles_bytes
sysdig -c topprocs_net
```

### dtrace (macOS, Solaris)

```bash
# On macOS
sudo dtruss ./my_app

# DTrace script
sudo dtrace -n 'syscall::open*:entry { printf("%s %s\n", execname, copyinstr(arg0)); }'
```

### SystemTap

```bash
# Trace opens with SystemTap script
stap -e 'probe syscall.openat { printf("%s: %s\n", execname(), filename) }'
```

---

## Quick Reference Card

### Most Common Commands

```bash
# Basic trace
strace command

# Attach to process
sudo strace -p PID

# Follow forks
strace -f command

# Write to file
strace -o file.log command

# With timing
strace -T command          # Syscall duration
strace -tt command         # Timestamps
strace -r command          # Relative times

# Statistics
strace -c command          # Summary only
strace -C command          # Summary + trace

# Filtering
strace -e trace=%file command      # File syscalls
strace -e trace=%network command   # Network syscalls
strace -e trace=%process command   # Process syscalls
strace -e trace=open,read,write command  # Specific syscalls

# Show only failures
strace -Z command

# Increase string length
strace -s 1000 command

# Show file descriptor paths
strace -y command
strace -yy command         # Include socket info
```

### Common Syscall Categories

| Category   | Filter     | Common Syscalls                    |
| ---------- | ---------- | ---------------------------------- |
| File       | `%file`    | openat, close, read, write, stat   |
| Network    | `%network` | socket, connect, bind, send, recv  |
| Process    | `%process` | fork, clone, execve, exit, wait    |
| Memory     | `%memory`  | mmap, munmap, brk, mprotect        |
| Signal     | `%signal`  | rt_sigaction, rt_sigprocmask, kill |
| IPC        | `%ipc`     | pipe, msgget, semget, shmget       |
| Descriptor | `%desc`    | dup, fcntl, select, poll, epoll    |

### Common Error Codes

| Error        | Meaning                 | Typical Cause            |
| ------------ | ----------------------- | ------------------------ |
| ENOENT       | No such file            | File doesn't exist       |
| EACCES       | Permission denied       | Wrong permissions        |
| EPERM        | Operation not permitted | Need root/capability     |
| EEXIST       | File exists             | File already exists      |
| EISDIR       | Is a directory          | Expected file, got dir   |
| ENOTDIR      | Not a directory         | Expected dir, got file   |
| ECONNREFUSED | Connection refused      | Service not running      |
| ETIMEDOUT    | Connection timed out    | Network issue            |
| EADDRINUSE   | Address in use          | Port already bound       |
| EAGAIN       | Try again               | Non-blocking would block |

---

## Appendix A: System Call Categories

### Complete List of Trace Categories

| Category   | Description                | Included Syscalls                                                  |
| ---------- | -------------------------- | ------------------------------------------------------------------ |
| `%file`    | File name operations       | open, stat, chmod, chown, link, unlink, rename, mkdir, rmdir, etc. |
| `%desc`    | File descriptor operations | read, write, close, dup, fcntl, select, poll, etc.                 |
| `%memory`  | Memory operations          | mmap, munmap, brk, mremap, mprotect, etc.                          |
| `%process` | Process operations         | fork, clone, execve, exit, wait, etc.                              |
| `%signal`  | Signal operations          | kill, sigaction, sigprocmask, etc.                                 |
| `%ipc`     | IPC operations             | pipe, msgget, semget, shmget, etc.                                 |
| `%network` | Network operations         | socket, connect, bind, listen, accept, send, recv, etc.            |
| `%stat`    | Stat operations            | stat, lstat, fstat, statx                                          |
| `%lstat`   | Lstat operations           | lstat                                                              |
| `%fstat`   | Fstat operations           | fstat                                                              |
| `%statfs`  | Statfs operations          | statfs, fstatfs, ustat                                             |
| `%fstatfs` | Fstatfs operations         | fstatfs                                                            |
| `%pure`    | Pure syscalls              | getpid, getuid, time, etc. (no arguments)                          |
| `%clock`   | Clock operations           | clock_gettime, clock_settime, etc.                                 |
| `%creds`   | Credential operations      | getuid, setuid, capget, etc.                                       |

---

## Appendix B: Error Codes Reference

### File and Directory Errors

| Error Code   | Number | Description               |
| ------------ | ------ | ------------------------- |
| EPERM        | 1      | Operation not permitted   |
| ENOENT       | 2      | No such file or directory |
| EIO          | 5      | I/O error                 |
| ENXIO        | 6      | No such device or address |
| EACCES       | 13     | Permission denied         |
| EEXIST       | 17     | File exists               |
| ENODEV       | 19     | No such device            |
| ENOTDIR      | 20     | Not a directory           |
| EISDIR       | 21     | Is a directory            |
| EINVAL       | 22     | Invalid argument          |
| ENFILE       | 23     | File table overflow       |
| EMFILE       | 24     | Too many open files       |
| EFBIG        | 27     | File too large            |
| ENOSPC       | 28     | No space left on device   |
| EROFS        | 30     | Read-only file system     |
| EMLINK       | 31     | Too many links            |
| ELOOP        | 40     | Too many symbolic links   |
| ENAMETOOLONG | 36     | File name too long        |
| ENOTEMPTY    | 39     | Directory not empty       |
| ESTALE       | 116    | Stale NFS file handle     |

### Process Errors

| Error Code | Number | Description                                  |
| ---------- | ------ | -------------------------------------------- |
| ESRCH      | 3      | No such process                              |
| ECHILD     | 10     | No child processes                           |
| EAGAIN     | 11     | Try again (resource temporarily unavailable) |
| ENOMEM     | 12     | Out of memory                                |
| EBUSY      | 16     | Device or resource busy                      |
| EDEADLK    | 35     | Resource deadlock avoided                    |
| ENOSYS     | 38     | Function not implemented                     |

### Network Errors

| Error Code    | Number | Description                     |
| ------------- | ------ | ------------------------------- |
| ENETDOWN      | 100    | Network is down                 |
| ENETUNREACH   | 101    | Network is unreachable          |
| ENETRESET     | 102    | Network dropped connection      |
| ECONNABORTED  | 103    | Connection aborted              |
| ECONNRESET    | 104    | Connection reset by peer        |
| ENOBUFS       | 105    | No buffer space available       |
| EISCONN       | 106    | Socket is already connected     |
| ENOTCONN      | 107    | Socket is not connected         |
| ETIMEDOUT     | 110    | Connection timed out            |
| ECONNREFUSED  | 111    | Connection refused              |
| EHOSTDOWN     | 112    | Host is down                    |
| EHOSTUNREACH  | 113    | No route to host                |
| EINPROGRESS   | 115    | Operation in progress           |
| EALREADY      | 114    | Operation already in progress   |
| EADDRINUSE    | 98     | Address already in use          |
| EADDRNOTAVAIL | 99     | Cannot assign requested address |

### IPC Errors

| Error Code      | Number | Description                    |
| --------------- | ------ | ------------------------------ |
| EPIPE           | 32     | Broken pipe                    |
| EMSGSIZE        | 90     | Message too long               |
| ENOTSOCK        | 88     | Socket operation on non-socket |
| EDESTADDRREQ    | 89     | Destination address required   |
| EPROTOTYPE      | 91     | Protocol wrong type for socket |
| ENOPROTOOPT     | 92     | Protocol not available         |
| EPROTONOSUPPORT | 93     | Protocol not supported         |
| ESOCKTNOSUPPORT | 94     | Socket type not supported      |
| EOPNOTSUPP      | 95     | Operation not supported        |
| EAFNOSUPPORT    | 97     | Address family not supported   |

---

## Appendix C: Signal Reference

### Standard Signals

| Signal    | Number | Default Action | Description              |
| --------- | ------ | -------------- | ------------------------ |
| SIGHUP    | 1      | Terminate      | Hangup                   |
| SIGINT    | 2      | Terminate      | Interrupt (Ctrl+C)       |
| SIGQUIT   | 3      | Core dump      | Quit (Ctrl+\)            |
| SIGILL    | 4      | Core dump      | Illegal instruction      |
| SIGTRAP   | 5      | Core dump      | Trace trap               |
| SIGABRT   | 6      | Core dump      | Abort                    |
| SIGBUS    | 7      | Core dump      | Bus error                |
| SIGFPE    | 8      | Core dump      | Floating point exception |
| SIGKILL   | 9      | Terminate      | Kill (cannot be caught)  |
| SIGUSR1   | 10     | Terminate      | User-defined signal 1    |
| SIGSEGV   | 11     | Core dump      | Segmentation fault       |
| SIGUSR2   | 12     | Terminate      | User-defined signal 2    |
| SIGPIPE   | 13     | Terminate      | Broken pipe              |
| SIGALRM   | 14     | Terminate      | Alarm clock              |
| SIGTERM   | 15     | Terminate      | Termination              |
| SIGSTKFLT | 16     | Terminate      | Stack fault              |
| SIGCHLD   | 17     | Ignore         | Child status changed     |
| SIGCONT   | 18     | Continue       | Continue if stopped      |
| SIGSTOP   | 19     | Stop           | Stop (cannot be caught)  |
| SIGTSTP   | 20     | Stop           | Terminal stop (Ctrl+Z)   |
| SIGTTIN   | 21     | Stop           | Background read from tty |
| SIGTTOU   | 22     | Stop           | Background write to tty  |
| SIGURG    | 23     | Ignore         | Urgent data on socket    |
| SIGXCPU   | 24     | Core dump      | CPU time limit exceeded  |
| SIGXFSZ   | 25     | Core dump      | File size limit exceeded |
| SIGVTALRM | 26     | Terminate      | Virtual timer expired    |
| SIGPROF   | 27     | Terminate      | Profiling timer expired  |
| SIGWINCH  | 28     | Ignore         | Window size changed      |
| SIGIO     | 29     | Terminate      | I/O possible             |
| SIGPWR    | 30     | Terminate      | Power failure            |
| SIGSYS    | 31     | Core dump      | Bad system call          |

### Real-time Signals

| Signal     | Number | Description            |
| ---------- | ------ | ---------------------- |
| SIGRTMIN   | 34     | First real-time signal |
| SIGRTMIN+1 | 35     | Real-time signal 1     |
| ...        | ...    | ...                    |
| SIGRTMAX   | 64     | Last real-time signal  |

### Signal Usage in strace

```bash
# See all signals
strace -e signal=all ./my_program

# Filter specific signals
strace -e signal=SIGTERM,SIGINT ./my_program

# Exclude signals
strace -e signal=!SIGCHLD ./my_program
```

---

## Appendix D: Ptrace and Security

### Understanding ptrace

Strace uses the `ptrace` system call to trace processes. This has security implications:

```bash
# Check ptrace_scope setting
cat /proc/sys/kernel/yama/ptrace_scope

# Values:
# 0 - Classic ptrace permissions (any process can trace)
# 1 - Restricted (only parent can trace children, or root)
# 2 - Admin only (only root/CAP_SYS_PTRACE)
# 3 - No ptrace at all
```

### Security Considerations

1. **Sensitive Data Exposure**: Trace files may contain:
   - Passwords
   - API keys
   - Private data
   - Cryptographic material

2. **Production Use**: Be cautious when tracing in production:
   - Large performance overhead
   - May expose sensitive data
   - Can affect application timing

3. **Container Security**: Containers need `CAP_SYS_PTRACE` capability:

   ```yaml
   # docker-compose.yml
   cap_add:
     - SYS_PTRACE
   ```

4. **SELinux/AppArmor**: May restrict ptrace:

   ```bash
   # Check SELinux denials
   ausearch -m avc -ts recent | grep ptrace

   # AppArmor profile for allowing ptrace
   # /etc/apparmor.d/my_profile
   ptrace (read, trace),
   ```

---

## Appendix E: Architecture Differences

### System Call Numbers

System call numbers differ between architectures:

| Syscall | x86 | x86_64 | ARM | ARM64 |
| ------- | --- | ------ | --- | ----- |
| read    | 3   | 0      | 3   | 63    |
| write   | 4   | 1      | 4   | 64    |
| open    | 5   | 2      | 5   | -     |
| close   | 6   | 3      | 6   | 57    |
| stat    | 106 | 4      | 106 | -     |
| fstat   | 108 | 5      | 108 | 80    |
| mmap    | 90  | 9      | 90  | 222   |
| fork    | 2   | 57     | 2   | -     |
| execve  | 11  | 59     | 11  | 221   |
| exit    | 1   | 60     | 1   | 93    |

### 32-bit vs 64-bit

```bash
# Check if process is 32-bit or 64-bit
file /proc/<pid>/exe

# Strace automatically handles both
strace ./32bit_app
strace ./64bit_app

# Force architecture (rarely needed)
strace -E LD_PRELOAD="" ./my_app
```

### Cross-architecture Tracing

```bash
# Tracing 32-bit process on 64-bit system
strace ./32bit_binary

# Works automatically, but syscall numbers differ
# Strace translates them correctly
```

---

## Appendix F: Troubleshooting Strace

### Strace Not Working

```bash
# Problem: strace fails to attach

# 1. Check if process exists
ps aux | grep <pid>

# 2. Check ptrace permissions
cat /proc/sys/kernel/yama/ptrace_scope

# 3. Try as root
sudo strace -p <pid>

# 4. Check container capabilities
docker inspect --format='{{.HostConfig.CapAdd}}' <container>

# 5. Check SELinux
getenforce
ausearch -m avc | grep strace
```

### Empty or No Output

```bash
# Problem: strace shows nothing

# 1. Check if syscalls are filtered correctly
strace -e trace=all ./my_app  # Show everything

# 2. Check if process is using vDSO (bypasses strace)
# vDSO calls like gettimeofday may not appear
strace -e trace=clock_gettime ./my_app

# 3. Ensure process isn't already being traced
strace -p <pid>
# "Operation not permitted" may mean already traced
```

### strace Hangs

```bash
# Problem: strace seems stuck

# 1. Check if traced process is waiting
cat /proc/<pid>/wchan

# 2. Process may be in uninterruptible sleep (D state)
ps aux | grep <pid>

# 3. Try with timeout
timeout 10 strace -p <pid>

# 4. Use -o to ensure output is flushed
strace -o trace.log -p <pid>
```

### Corrupted Output

```bash
# Problem: output is garbled or incomplete

# 1. Ensure single writer to output
strace -o trace.log ./my_app  # Not to terminal

# 2. With multi-threaded, use -ff
strace -ff -o trace ./my_app

# 3. Increase buffer size (if available)
strace -O 100000 ./my_app
```

---

## Conclusion

Strace is an indispensable tool for anyone working with Linux systems. Whether you're debugging applications,
analyzing performance, conducting security research, or simply trying to understand how software works, strace
provides invaluable insights into the interaction between userspace programs and the kernel.

### Key Takeaways

1. **Start Simple**: Begin with basic traces and add options as needed
2. **Filter Aggressively**: Focus on the syscalls relevant to your problem
3. **Use Timestamps**: Always include timing information for production debugging
4. **Mind the Overhead**: Strace significantly impacts performance
5. **Secure Your Data**: Trace files may contain sensitive information
6. **Know Your Alternatives**: perf trace, bpftrace for lower overhead
7. **Practice Regularly**: The more you use strace, the more patterns you'll recognize

### Further Resources

- **Man Page**: `man strace`
- **Official Website**: https://strace.io/
- **GitHub Repository**: https://github.com/strace/strace
- **Linux Kernel Source**: For understanding syscall implementations
- **The Art of Debugging with GDB, DDD, and Eclipse**: Book covering debugging techniques

### Contributing to strace

Strace is open source! You can contribute by:

- Reporting bugs
- Improving documentation
- Adding support for new syscalls
- Testing on different architectures

---

_This guide was created to provide a comprehensive reference for strace. For the most up-to-date information,
always refer to the official strace documentation and man pages._

**Document Version**: 1.0
**Last Updated**: January 2026
**Strace Version Coverage**: Up to 5.x

---

## Index

### A

- Alternatives to strace, 2216-2294
- Appendix A: System Call Categories, 2370-2391
- Appendix B: Error Codes Reference, 2395-2463
- Appendix C: Signal Reference, 2466-2555
- Appendix D: Ptrace and Security, 2558-2600
- Appendix E: Architecture Differences, 2603-2650
- Appendix F: Troubleshooting Strace, 2653-2720
- Attaching to processes, 682-694

### B

- Basic concepts, 251-335
- Basic usage, 649-792
- Best practices, 1817-1908
- bpftrace, 2250-2261

### C

- Command line options, 560-643
- Common pitfalls, 1912-2031
- Container debugging, 1583-1656
- Core concepts, 251-335

### D

- Debugging applications, 1177-1265
- dtrace, 2279-2287

### E

- Error codes reference, 2395-2463

### F

- Fault injection, 1029-1070
- File system analysis, 1348-1413
- Filtering, 796-902

### H

- History, 115-143

### I

- Installation, 147-248
- Integration with tools, 1736-1811

### L

- ltrace, 2218-2230

### M

- Memory analysis, 1161-1173
- Multi-threaded tracing, 1522-1579

### N

- Network debugging, 1270-1344

### O

- Output formatting, 906-983

### P

- perf trace, 2232-2248
- Performance analysis, 1087-1173
- Performance considerations, 2163-2212
- Process management, 1417-1462
- ptrace security, 2558-2600

### Q

- Quick reference card, 2298-2366

### R

- Real-world use cases, 2035-2158

### S

- Security analysis, 1660-1732
- Signal handling, 1466-1516
- Signal reference, 2466-2555
- sysdig, 2263-2277
- System calls overview, 340-556
- SystemTap, 2289-2294

### T

- Timestamps, 710-729
- Troubleshooting strace, 2653-2720
