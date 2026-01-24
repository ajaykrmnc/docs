# Unix Pipes, Client-Server Architecture, and the Close System Call

## A Deep Technical Exploration in the Tradition of Maurice Bach

---

**Document Version:** 1.0
**Last Updated:** February 2026
**Scope:** Kernel Internals, System Call Implementation, Data Structures, and Algorithms

---

## Table of Contents

1. [Introduction](#1-introduction)
   - [The Unix Philosophy of Communication](#the-unix-philosophy-of-communication)
   - [Historical Context](#historical-context)
   - [Document Organization](#document-organization)

2. [Fundamental Concepts](#2-fundamental-concepts)
   - [File Descriptors and the Open File Table](#file-descriptors-and-the-open-file-table)
   - [The Inode Abstraction](#the-inode-abstraction)
   - [Reference Counting in the Kernel](#reference-counting-in-the-kernel)

3. [The Pipe Mechanism](#3-the-pipe-mechanism)
   - [Pipe System Call Implementation](#pipe-system-call-implementation)
   - [Pipe Data Structures](#pipe-data-structures)
   - [The Pipe Buffer](#the-pipe-buffer)
   - [Reading from a Pipe](#reading-from-a-pipe)
   - [Writing to a Pipe](#writing-to-a-pipe)
   - [Pipe Capacity and Blocking](#pipe-capacity-and-blocking)

4. [Named Pipes (FIFOs)](#4-named-pipes-fifos)
   - [FIFO Creation and the Filesystem](#fifo-creation-and-the-filesystem)
   - [Opening a FIFO](#opening-a-fifo)
   - [FIFO Semantics](#fifo-semantics)

5. [Client-Server Architecture with Pipes](#5-client-server-architecture-with-pipes)
   - [The Server Process Model](#the-server-process-model)
   - [Connection Establishment](#connection-establishment)
   - [Request-Response Protocol](#request-response-protocol)
   - [Multiplexing with select() and poll()](#multiplexing-with-select-and-poll)

6. [The Close System Call](#6-the-close-system-call)
   - [Close System Call Implementation](#close-system-call-implementation)
   - [Reference Count Decrement](#reference-count-decrement)
   - [Resource Cleanup](#resource-cleanup)
   - [Close and Pipes](#close-and-pipes)
   - [Close and Sockets](#close-and-sockets)

7. [Advanced Topics](#7-advanced-topics)
   - [Pipe Atomicity Guarantees](#pipe-atomicity-guarantees)
   - [Signal Generation (SIGPIPE)](#signal-generation-sigpipe)
   - [Splice and Zero-Copy I/O](#splice-and-zero-copy-io)

8. [Practical Implementation](#8-practical-implementation)
   - [Building a Pipe-Based Server](#building-a-pipe-based-server)
   - [Error Handling Patterns](#error-handling-patterns)
   - [Performance Considerations](#performance-considerations)

---

## 1. Introduction

### The Unix Philosophy of Communication

The Unix operating system, from its inception at Bell Labs in the early 1970s, embraced a fundamental principle: **everything is a file**. This abstraction, revolutionary for its time, unified the interface to diverse system resources—disk files, devices, terminals, and inter-process communication channels—under a single, elegant API: `open()`, `read()`, `write()`, and `close()`.

The pipe mechanism, introduced by Douglas McIlroy and implemented by Ken Thompson in 1973, exemplifies this philosophy. A pipe appears to processes as a pair of file descriptors, yet it exists entirely in memory, serving as a conduit for data flow between processes. This design decision—treating IPC as file I/O—has profound implications:

1. **Uniformity**: Programs need not distinguish between reading from a file and reading from a pipe
2. **Composability**: The shell can connect arbitrary programs via pipes without modification
3. **Simplicity**: The kernel maintains a single, well-understood interface

As Maurice Bach wrote in "The Design of the UNIX Operating System":

> "The elegance of the UNIX system lies in its simplicity. The file abstraction provides a uniform interface to a variety of I/O devices and inter-process communication mechanisms."

### Historical Context

The evolution of Unix IPC mechanisms reflects the growing complexity of computing:

| Era   | Mechanism           | Characteristics                           |
| ----- | ------------------- | ----------------------------------------- |
| 1973  | Anonymous Pipes     | Unidirectional, related processes only    |
| 1974  | Named Pipes (FIFOs) | Filesystem presence, unrelated processes  |
| 1983  | BSD Sockets         | Network transparency, bidirectional       |
| 1983  | System V IPC        | Message queues, semaphores, shared memory |
| 1990s | Unix Domain Sockets | Local IPC with socket semantics           |

Each mechanism addressed specific limitations while preserving the file descriptor abstraction where possible.

### Document Organization

This document follows the structure established by Maurice Bach, proceeding from fundamental data structures through system call implementation to practical application. We examine:

1. **Data Structures**: The kernel tables that support pipes and file descriptors
2. **Algorithms**: The step-by-step procedures the kernel follows
3. **Interactions**: How system calls affect kernel state
4. **Edge Cases**: Boundary conditions and error handling

---

## 2. Fundamental Concepts

Before examining pipes in detail, we must understand the kernel data structures that underpin all file operations in Unix.

### File Descriptors and the Open File Table

When a process opens a file (or creates a pipe), the kernel establishes a chain of data structures linking the process to the underlying resource.

#### The Three-Level Structure

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        KERNEL DATA STRUCTURES                                │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│   Process A                    System-Wide                   Filesystem      │
│   ─────────                    ───────────                   ──────────      │
│                                                                              │
│   ┌─────────────┐             ┌─────────────────┐          ┌─────────────┐  │
│   │ Per-Process │             │   System File   │          │   Inode     │  │
│   │ File Table  │             │     Table       │          │   Table     │  │
│   │ (u_ofile[]) │             │  (file struct)  │          │(inode/vnode)│  │
│   ├─────────────┤             ├─────────────────┤          ├─────────────┤  │
│   │ fd 0 ───────┼────────────>│ f_offset: 0     │────┐     │ i_mode      │  │
│   │ fd 1 ───────┼──────┐      │ f_count: 1      │    │     │ i_size      │  │
│   │ fd 2 ───────┼──┐   │      │ f_flag: O_RDONLY│    │     │ i_count: 2  │  │
│   │ fd 3 ───────┼┐ │   │      │ f_inode ────────┼────┼────>│ i_data[]    │  │
│   │    ...      │││   │      ├─────────────────┤    │     │    ...      │  │
│   └─────────────┘││   │      │ f_offset: 1024  │    │     ├─────────────┤  │
│                  ││   └─────>│ f_count: 1      │────┘     │ i_mode      │  │
│   Process B      ││          │ f_flag: O_WRONLY│          │ i_size      │  │
│   ─────────      ││          │ f_inode ────────┼─────────>│ i_count: 1  │  │
│                  ││          ├─────────────────┤          │ i_data[]    │  │
│   ┌─────────────┐││          │ f_offset: 512   │          │    ...      │  │
│   │ Per-Process │││          │ f_count: 2      │──┐       └─────────────┘  │
│   │ File Table  │││          │ f_flag: O_RDWR  │  │                        │
│   ├─────────────┤││          │ f_inode ────────┼──┼──>  (pipe inode)       │
│   │ fd 0 ───────┼┼┴─────────>│    ...          │  │                        │
│   │ fd 1 ───────┼┴────────────────────────────────┘                        │
│   │    ...      │                                                          │
│   └─────────────┘                                                          │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

#### The Per-Process File Descriptor Table

Each process maintains an array of pointers to system file table entries. This array, historically called
`u_ofile[]` in the user area (`struct user`), has evolved but retains its essential character:

```c
/* Simplified representation of per-process file table */
struct files_struct {
    atomic_t        count;           /* Reference count */
    struct fdtable  *fdt;            /* Pointer to file descriptor table */
    struct fdtable  fdtab;           /* Embedded fdtable for small sets */
    spinlock_t      file_lock;       /* Protects concurrent access */
    int             next_fd;         /* Next fd to allocate */
    /* ... */
};

struct fdtable {
    unsigned int    max_fds;         /* Current maximum */
    struct file     **fd;            /* Array of file pointers */
    fd_set          *close_on_exec;  /* Bitmap: close on exec() */
    fd_set          *open_fds;       /* Bitmap: which fds are open */
    /* ... */
};
```

**Key observations:**

1. **File descriptors are small integers**: They are indices into the `fd[]` array
2. **Allocation is sequential**: The kernel returns the lowest available fd
3. **Descriptors 0, 1, 2 are conventional**: stdin, stdout, stderr by convention, not enforcement
4. **The table can grow**: Modern kernels expand the table dynamically

#### The System-Wide File Table

The system file table (historically the `file` structure array) contains entries shared across processes. Each entry records:

```c
struct file {
    union {
        struct llist_node   fu_llist;
        struct rcu_head     fu_rcuhead;
    } f_u;
    struct path             f_path;       /* Path to the file */
    struct inode            *f_inode;     /* Cached inode pointer */
    const struct file_operations *f_op;   /* Operations table */

    spinlock_t              f_lock;
    atomic_long_t           f_count;      /* Reference count */
    unsigned int            f_flags;      /* O_RDONLY, O_WRONLY, etc. */
    fmode_t                 f_mode;       /* FMODE_READ, FMODE_WRITE */
    struct mutex            f_pos_lock;
    loff_t                  f_pos;        /* Current read/write position */

    /* Owner for SIGIO/SIGURG signals */
    struct fown_struct      f_owner;

    /* For pipes: */
    void                    *private_data; /* Pipe-specific data */

    /* ... */
};
```

**Critical fields explained:**

| Field     | Purpose                                  |
| --------- | ---------------------------------------- |
| `f_count` | Number of file descriptors pointing here |
| `f_pos`   | Current file offset (seek position)      |
| `f_flags` | Access mode and status flags             |
| `f_op`    | Virtual function table for operations    |
| `f_inode` | Link to the inode layer                  |

**Why this separation matters:**

Consider what happens when a process calls `fork()`:

```c
pid_t pid = fork();
```

The child process receives a **copy** of the parent's file descriptor table, but both tables point to the **same** system file table entries. Thus:

1. File descriptors are **independent** (closing fd 3 in child doesn't affect parent)
2. File offsets are **shared** (read in child advances position for parent too)
3. Reference counts increment (file table entry's `f_count` increases)

### The Inode Abstraction

The inode (index node) represents a file's **identity**, independent of any process's view of it. For disk files, the inode contains:

```c
struct inode {
    umode_t                 i_mode;       /* File type and permissions */
    unsigned short          i_opflags;
    kuid_t                  i_uid;        /* Owner user ID */
    kgid_t                  i_gid;        /* Owner group ID */
    unsigned int            i_flags;

    const struct inode_operations *i_op;  /* Inode operations */
    struct super_block      *i_sb;        /* Owning superblock */

    unsigned long           i_ino;        /* Inode number */
    atomic_t                i_count;      /* Reference count */
    unsigned int            i_nlink;      /* Hard link count */

    dev_t                   i_rdev;       /* Device ID (for device files) */
    loff_t                  i_size;       /* File size in bytes */
    struct timespec64       i_atime;      /* Last access time */
    struct timespec64       i_mtime;      /* Last modification time */
    struct timespec64       i_ctime;      /* Last status change time */

    unsigned short          i_bytes;
    blkcnt_t                i_blocks;     /* Number of blocks */

    /* For pipes: */
    struct pipe_inode_info  *i_pipe;      /* Pipe information */

    /* ... */
};
```

**For pipes specifically**, the `i_pipe` field points to a `pipe_inode_info` structure containing the pipe
buffer and synchronization primitives. We examine this in detail in Section 3.

### Reference Counting in the Kernel

Reference counting is the fundamental mechanism by which the kernel manages shared resource lifetimes. Three
distinct reference counts govern file-related resources:

```
┌──────────────────────────────────────────────────────────────────────────┐
│                    REFERENCE COUNT HIERARCHY                              │
├──────────────────────────────────────────────────────────────────────────┤
│                                                                           │
│   Level 1: File Descriptor (per-process)                                  │
│   ─────────────────────────────────────                                   │
│   • Exists in per-process table                                           │
│   • Not reference-counted per se                                          │
│   • Closing removes the entry                                             │
│                                                                           │
│            │                                                              │
│            │ points to                                                    │
│            ▼                                                              │
│                                                                           │
│   Level 2: File Table Entry (f_count)                                     │
│   ──────────────────────────────────                                      │
│   • Incremented: dup(), fork(), open() same entry                         │
│   • Decremented: close()                                                  │
│   • When reaches 0: entry freed, f_pos lost                               │
│                                                                           │
│            │                                                              │
│            │ points to                                                    │
│            ▼                                                              │
│                                                                           │
│   Level 3: Inode (i_count)                                                │
│   ────────────────────────                                                │
│   • Incremented: each file table entry referencing it                     │
│   • Decremented: when file table entry freed                              │
│   • When reaches 0 AND i_nlink == 0: file deleted                         │
│                                                                           │
│   For pipes: i_nlink is always 0 (no directory entry)                     │
│              Pipe destroyed when last reference closes                    │
│                                                                           │
└──────────────────────────────────────────────────────────────────────────┘
```

#### Algorithm: Reference Count Management

```
algorithm: increment_file_ref(file_entry)
input:     file_entry - pointer to system file table entry
output:    none
{
    atomic_inc(&file_entry->f_count);
}

algorithm: decrement_file_ref(file_entry)
input:     file_entry - pointer to system file table entry
output:    none
{
    if (atomic_dec_and_test(&file_entry->f_count)) {
        /* Last reference - cleanup */
        inode = file_entry->f_inode;

        /* Release any locks held by this file table entry */
        locks_remove_file(file_entry);

        /* Call file-type-specific cleanup */
        if (file_entry->f_op->release)
            file_entry->f_op->release(inode, file_entry);

        /* Decrement inode reference */
        iput(inode);

        /* Free the file structure */
        file_free(file_entry);
    }
}
```

This cascade of decrements explains why closing the last file descriptor to a pipe causes the pipe to be
destroyed: the `f_count` reaches zero, triggering `iput()` on the pipe inode, whose `i_count` (now zero with
`i_nlink` already zero) causes the pipe buffer to be freed.

---

## 3. The Pipe Mechanism

The pipe is perhaps the most elegant inter-process communication mechanism in Unix. It provides a
unidirectional data channel between processes, requiring no filesystem storage and existing only as long as
processes hold references to it.

### Pipe System Call Implementation

The `pipe()` system call creates a pipe and returns two file descriptors:

```c
#include <unistd.h>

int pipe(int pipefd[2]);
```

Where:

- `pipefd[0]` is the **read end** (receives data)
- `pipefd[1]` is the **write end** (sends data)

#### The pipe() Algorithm

```
algorithm: sys_pipe
input:     pipefd - pointer to user space array for two file descriptors
output:    0 on success, -1 on error (errno set)

{
    /* Step 1: Allocate pipe inode */
    inode = get_pipe_inode();
    if (inode == NULL) {
        return -ENFILE;    /* System file table full */
    }

    /* Step 2: Allocate pipe buffer */
    pipe_info = alloc_pipe_info();
    if (pipe_info == NULL) {
        iput(inode);
        return -ENOMEM;
    }
    inode->i_pipe = pipe_info;

    /* Step 3: Allocate two file table entries */
    read_file = alloc_file();
    write_file = alloc_file();
    if (read_file == NULL || write_file == NULL) {
        free_pipe_info(pipe_info);
        iput(inode);
        return -ENFILE;
    }

    /* Step 4: Initialize read end */
    read_file->f_inode = inode;
    read_file->f_op = &read_pipefifo_fops;
    read_file->f_mode = FMODE_READ;
    read_file->f_flags = O_RDONLY;
    read_file->f_count = 1;
    read_file->f_pos = 0;          /* Meaningless for pipes */

    /* Step 5: Initialize write end */
    write_file->f_inode = inode;
    write_file->f_op = &write_pipefifo_fops;
    write_file->f_mode = FMODE_WRITE;
    write_file->f_flags = O_WRONLY;
    write_file->f_count = 1;
    write_file->f_pos = 0;

    /* Step 6: Increment inode reference count (two references) */
    inode->i_count = 2;

    /* Step 7: Allocate file descriptors */
    read_fd = get_unused_fd();
    write_fd = get_unused_fd();
    if (read_fd < 0 || write_fd < 0) {
        /* Cleanup and return error */
        put_unused_fd(read_fd);
        put_unused_fd(write_fd);
        fput(read_file);
        fput(write_file);
        return -EMFILE;    /* Per-process limit exceeded */
    }

    /* Step 8: Install file descriptors */
    fd_install(read_fd, read_file);
    fd_install(write_fd, write_file);

    /* Step 9: Copy to user space */
    pipefd[0] = read_fd;
    pipefd[1] = write_fd;

    return 0;
}
```

#### Understanding "Two Files" - The Key Insight

**Your question is crucial**: Why create "two files" if they're not actual files on disk?

The answer lies in understanding what a "file" means in Unix kernel terminology:

**These are NOT disk files.** The `read_file` and `write_file` in the algorithm are **file table entries**
(`struct file`)—kernel data structures that describe *how* a process is accessing a resource. They are
"views" or "handles" to the underlying pipe, not files themselves.

Think of it this way:

```
┌───────────────────────────────────────────────────────────────────────────┐
│                     WHY TWO FILE TABLE ENTRIES?                            │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   ANALOGY: A HALLWAY WITH TWO DOORS                                        │
│   ═══════════════════════════════════                                      │
│                                                                            │
│   Imagine a pipe as a hallway. To use the hallway, you need doors:         │
│                                                                            │
│   ┌────────┐                                         ┌────────┐           │
│   │ DOOR A │     ════════════════════════════>       │ DOOR B │           │
│   │(write) │         HALLWAY (pipe buffer)           │ (read) │           │
│   │ ───>   │         Data flows one way --->         │  ───>  │           │
│   └────────┘                                         └────────┘           │
│                                                                            │
│   • The HALLWAY is the actual pipe buffer (the shared memory)              │
│   • DOOR A (write end) = one file table entry (write permissions)          │
│   • DOOR B (read end) = another file table entry (read permissions)        │
│                                                                            │
│   The "doors" aren't the hallway—they're access points WITH RULES:         │
│   • Door A only lets you PUT things IN                                     │
│   • Door B only lets you TAKE things OUT                                   │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```

**Why can't we use just ONE file table entry?**

Each file table entry stores:
1. **Access mode** (`f_mode`): READ or WRITE—but not both for a pipe end
2. **Operations table** (`f_op`): Different functions for reading vs writing
3. **Flags** (`f_flags`): O_RDONLY vs O_WRONLY

If we used one entry, we'd face problems:
- How would the kernel know if `read()` or `write()` is valid for a given fd?
- How would `close()` know if the last *reader* or last *writer* closed?
- Pipes are *unidirectional*—enforcing this requires separate modes

**The Complete Picture:**

```
┌───────────────────────────────────────────────────────────────────────────┐
│              DECOMPOSING THE PIPE SYSTEM CALL                              │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   STEP-BY-STEP BREAKDOWN:                                                  │
│                                                                            │
│   1. get_pipe_inode()                                                      │
│      └─> Creates ONE inode (identity of the pipe)                          │
│          This is the "thing" itself—the pipe's existence                   │
│                                                                            │
│   2. alloc_pipe_info()                                                     │
│      └─> Creates the actual buffer where data lives                        │
│          This is attached to the inode (inode->i_pipe)                     │
│                                                                            │
│   3. alloc_file() × 2                                                      │
│      └─> Creates TWO file table entries (not files!)                       │
│                                                                            │
│          read_file:                      write_file:                       │
│          ┌────────────────────┐         ┌────────────────────┐            │
│          │ f_mode  = READ     │         │ f_mode  = WRITE    │            │
│          │ f_flags = O_RDONLY │         │ f_flags = O_WRONLY │            │
│          │ f_op = read_ops    │──┐      │ f_op = write_ops   │──┐         │
│          │ f_inode ───────────┼──┼──────│─f_inode ───────────┼──┼──┐      │
│          └────────────────────┘  │      └────────────────────┘  │  │      │
│                                  │                              │  │      │
│          Both point to the       │                              │  │      │
│          SAME inode! ────────────┴──────────────────────────────┘  │      │
│                                                                    │      │
│                                  ┌─────────────────────────────────┘      │
│                                  ▼                                        │
│   4. The shared inode:           ┌──────────────────────┐                 │
│                                  │ PIPE INODE           │                 │
│                                  │ ──────────           │                 │
│                                  │ i_count = 2          │ ◄── Two refs!   │
│                                  │ i_pipe ──────────────┼──┐              │
│                                  └──────────────────────┘  │              │
│                                                            │              │
│   5. The buffer:                 ┌─────────────────────────┘              │
│                                  ▼                                        │
│                                  ┌──────────────────────┐                 │
│                                  │ pipe_inode_info      │                 │
│                                  │ ────────────────     │                 │
│                                  │ readers = 1          │                 │
│                                  │ writers = 1          │                 │
│                                  │ bufs[] (ring buffer) │                 │
│                                  └──────────────────────┘                 │
│                                                                            │
│   6. get_unused_fd() × 2                                                   │
│      └─> Gets two NUMBERS (small integers) from process's fd table         │
│          These are what user code sees: fd[0]=3, fd[1]=4                   │
│                                                                            │
│   7. fd_install()                                                          │
│      └─> Links: fd number ──> file table entry                             │
│          fd[0] (3) ──> read_file                                           │
│          fd[1] (4) ──> write_file                                          │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```

**Key terminology clarification:**

| Term                    | What It Actually Is                                    |
| ----------------------- | ------------------------------------------------------ |
| **File Descriptor (fd)**| A small integer (index into per-process table)         |
| **File Table Entry**    | Kernel struct describing access mode, position, etc.   |
| **Inode**               | Kernel struct representing the resource's identity     |
| **Pipe Buffer**         | The actual memory where data is stored                 |
| **"read_file"**         | A file table entry configured for reading              |
| **"write_file"**        | A file table entry configured for writing              |

**Why "file" in the naming?**

Historical Unix used `struct file` for these entries because of the "everything is a file" philosophy.
Even though pipes have no disk presence, the kernel reuses the same structure to describe access to them.
This is abstraction at work—the user-space program calls `read()` and `write()` identically whether
it's a disk file, pipe, socket, or device.

**What happens when you use the pipe:**

**First, where do fd numbers 3 and 4 come from?**

When a Unix process starts, it typically already has three file descriptors open:

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    STANDARD FILE DESCRIPTORS                             │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│   Every process inherits these from its parent (usually the shell):      │
│                                                                          │
│   fd[0] = stdin  (standard input)  ──> typically the terminal           │
│   fd[1] = stdout (standard output) ──> typically the terminal           │
│   fd[2] = stderr (standard error)  ──> typically the terminal           │
│                                                                          │
│   These are ALREADY TAKEN when your program starts!                      │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

When `pipe()` is called, the kernel allocates the **lowest available** file descriptor numbers:

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    FILE DESCRIPTOR ALLOCATION                            │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│   BEFORE pipe() call:                                                    │
│   ┌─────────────────────────────────────────────────────────────────┐   │
│   │ Index:  │  0   │  1   │  2   │  3   │  4   │  5   │ ...         │   │
│   │ Status: │ USED │ USED │ USED │ FREE │ FREE │ FREE │             │   │
│   │ Points: │stdin │stdout│stderr│  -   │  -   │  -   │             │   │
│   └─────────────────────────────────────────────────────────────────┘   │
│                                                                          │
│   pipe() calls get_unused_fd() twice:                                    │
│     - First call returns 3 (lowest free) → assigned to read end         │
│     - Second call returns 4 (next lowest free) → assigned to write end  │
│                                                                          │
│   AFTER pipe(pipefd) call:                                               │
│   ┌─────────────────────────────────────────────────────────────────┐   │
│   │ Index:  │  0   │  1   │  2   │  3   │  4   │  5   │ ...         │   │
│   │ Status: │ USED │ USED │ USED │ USED │ USED │ FREE │             │   │
│   │ Points: │stdin │stdout│stderr│read_ │write_│  -   │             │   │
│   │         │      │      │      │file  │file  │      │             │   │
│   └─────────────────────────────────────────────────────────────────┘   │
│                                                                          │
│   Result: pipefd[0] = 3 (read end)                                       │
│           pipefd[1] = 4 (write end)                                      │
│                                                                          │
│   NOTE: If fd 3 was already in use (e.g., you opened another file),     │
│         pipe() would return 4 and 5, or whatever is next available!     │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

**Now, what happens when you use the pipe:**

```
Process calls: write(pipefd[1], "Hello", 5)
               where pipefd[1] contains the value 4
                  │
                  ▼
┌─────────────────────────────────────────────────────────────────────────┐
│  1. Kernel receives: write(4, "Hello", 5)                                │
│     The "4" is just a number—an index into the fd table                 │
│                                                                          │
│  2. Kernel looks up fd_table[4] ──> finds pointer to write_file          │
│                                                                          │
│  3. Checks write_file->f_mode: is FMODE_WRITE set? YES ✓                 │
│                                                                          │
│  4. Calls write_file->f_op->write() which is pipe_write()                │
│                                                                          │
│  5. pipe_write() accesses write_file->f_inode->i_pipe (the buffer)       │
│                                                                          │
│  6. Copies "Hello" into the pipe buffer's ring                           │
│                                                                          │
│  7. Wakes up any process blocked reading from this pipe                  │
└─────────────────────────────────────────────────────────────────────────┘

Process calls: read(pipefd[0], buf, 100)
               where pipefd[0] contains the value 3
                  │
                  ▼
┌─────────────────────────────────────────────────────────────────────────┐
│  1. Kernel receives: read(3, buf, 100)                                   │
│     The "3" is just a number—an index into the fd table                 │
│                                                                          │
│  2. Kernel looks up fd_table[3] ──> finds pointer to read_file           │
│                                                                          │
│  3. Checks read_file->f_mode: is FMODE_READ set? YES ✓                   │
│                                                                          │
│  4. Calls read_file->f_op->read() which is pipe_read()                   │
│                                                                          │
│  5. pipe_read() accesses read_file->f_inode->i_pipe (SAME buffer!)       │
│                                                                          │
│  6. Copies "Hello" from the pipe buffer into user's buf                  │
│                                                                          │
│  7. Returns 5 (bytes read)                                               │
└─────────────────────────────────────────────────────────────────────────┘
```

**Summary**: The "two files" are two *access handles* (file table entries) that both point to the
*same* pipe. One handle permits only writing, the other only reading. The file descriptors (integers)
returned to user space are simply indices that lead to these handles.

#### State After pipe() Call

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        STATE AFTER pipe(fd) CALL                             │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│   Process                     System File Table             Pipe Inode       │
│   ───────                     ─────────────────             ──────────       │
│                                                                              │
│   ┌─────────────┐            ┌──────────────────┐         ┌─────────────┐   │
│   │ fd table    │            │ File Entry (read)│         │ Pipe Inode  │   │
│   ├─────────────┤            ├──────────────────┤         ├─────────────┤   │
│   │ fd[0]=3 ────┼───────────>│ f_count: 1       │────┐    │ i_count: 2  │   │
│   │ fd[1]=4 ────┼──────┐     │ f_mode: READ     │    │    │ i_nlink: 0  │   │
│   │    ...      │      │     │ f_op: read_ops   │    │    │ i_pipe: ────┼──┐│
│   └─────────────┘      │     │ f_inode: ────────┼────┼───>│    ...      │  ││
│                        │     └──────────────────┘    │    └─────────────┘  ││
│                        │                             │                      ││
│                        │     ┌──────────────────┐    │    ┌─────────────┐  ││
│                        │     │ File Entry(write)│    │    │pipe_inode_  │<─┘│
│                        └────>│ f_count: 1       │────┘    │   info      │   │
│                              │ f_mode: WRITE    │         ├─────────────┤   │
│                              │ f_op: write_ops  │         │ readers: 1  │   │
│                              │ f_inode: ────────┼────────>│ writers: 1  │   │
│                              └──────────────────┘         │ bufs: ──────┼──┐│
│                                                           │ ring_size   │  ││
│                                                           └─────────────┘  ││
│                                                                             ││
│                                                           ┌─────────────┐  ││
│                                                           │ Pipe Buffer │<─┘│
│                                                           │ (circular)  │   │
│                                                           ├─────────────┤   │
│                                                           │ [         ] │   │
│                                                           │ head: 0     │   │
│                                                           │ tail: 0     │   │
│                                                           └─────────────┘   │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Pipe Data Structures

The `pipe_inode_info` structure is the heart of pipe management:

```c
struct pipe_inode_info {
    struct mutex        mutex;          /* Serializes access */
    wait_queue_head_t   rd_wait;        /* Readers waiting for data */
    wait_queue_head_t   wr_wait;        /* Writers waiting for space */

    unsigned int        head;           /* Write position (producer) */
    unsigned int        tail;           /* Read position (consumer) */
    unsigned int        max_usage;      /* High-water mark */
    unsigned int        ring_size;      /* Number of buffer slots */
    unsigned int        nr_accounted;   /* For accounting */

    unsigned int        readers;        /* Number of read file entries */
    unsigned int        writers;        /* Number of write file entries */
    unsigned int        files;          /* Total file entries */
    unsigned int        r_counter;      /* Reader open count (FIFOs) */
    unsigned int        w_counter;      /* Writer open count (FIFOs) */

    struct page         *tmp_page;      /* Cached page for small writes */
    struct fasync_struct *fasync_readers;  /* Async notification */
    struct fasync_struct *fasync_writers;

    struct pipe_buffer  *bufs;          /* Array of buffer descriptors */
    struct user_struct  *user;          /* User for resource accounting */
};
```

#### The Pipe Buffer Array

Each slot in `bufs[]` describes a page of data:

```c
struct pipe_buffer {
    struct page     *page;      /* Page containing data */
    unsigned int    offset;     /* Start of data in page */
    unsigned int    len;        /* Length of data */
    const struct pipe_buf_operations *ops;
    unsigned int    flags;
    unsigned long   private;
};
```

```
┌───────────────────────────────────────────────────────────────────────────┐
│                     PIPE BUFFER RING STRUCTURE                             │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   pipe_inode_info                                                          │
│   ┌────────────────┐                                                       │
│   │ head: 3        │     (next write position)                             │
│   │ tail: 1        │     (next read position)                              │
│   │ ring_size: 16  │     (typically 16 pages = 64KB default)               │
│   │ bufs: ─────────┼──┐                                                    │
│   └────────────────┘  │                                                    │
│                       │                                                    │
│                       ▼                                                    │
│   ┌─────┬─────┬─────┬─────┬─────┬─────┬─────┬─────┬───────┐               │
│   │  0  │  1  │  2  │  3  │  4  │  5  │ ... │ 14  │  15   │  bufs[]       │
│   ├─────┼─────┼─────┼─────┼─────┼─────┼─────┼─────┼───────┤               │
│   │empty│DATA │DATA │empty│empty│empty│     │empty│ empty │               │
│   │     │     │     │     │     │     │     │     │       │               │
│   └─────┴──┬──┴──┬──┴─────┴─────┴─────┴─────┴─────┴───────┘               │
│            │     │                                                         │
│            │     │    ┌─────────────────────────────────┐                  │
│            │     └───>│ pipe_buffer[2]                  │                  │
│            │          │ page: 0xffff8801234   ──────┐   │                  │
│            │          │ offset: 0              │   │   │                  │
│            │          │ len: 4096              │   │   │                  │
│            │          └────────────────────────│───┘   │                  │
│            │                                   │       │                  │
│            │          ┌────────────────────────│───────┘                  │
│            │          │                        ▼                          │
│            │          │           ┌────────────────────┐                  │
│            │          │           │    Physical Page   │                  │
│            └──────────│──────┐    │    (4096 bytes)    │                  │
│                       │      │    │  "Hello, World..." │                  │
│            ┌──────────┘      │    └────────────────────┘                  │
│            ▼                 ▼                                             │
│   ┌────────────────────┐   ┌────────────────────┐                         │
│   │ pipe_buffer[1]     │   │    Physical Page   │                         │
│   │ page: 0xffff8800abc│──>│    (4096 bytes)    │                         │
│   │ offset: 512        │   │ [...data...]       │                         │
│   │ len: 2048          │   └────────────────────┘                         │
│   └────────────────────┘                                                   │
│                                                                            │
│   Data available = (head - tail) buffers = (3 - 1) = 2 buffers            │
│   Next read from: bufs[tail % ring_size] = bufs[1]                        │
│   Next write to:  bufs[head % ring_size] = bufs[3]                        │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```

### The Pipe Buffer

#### Buffer Organization

The pipe buffer in modern Linux is organized as a **ring buffer of page references**. This is a significant evolution from the original Unix design (which used a fixed 4KB buffer in the inode).

Key characteristics:

- **Default capacity**: 16 pages = 65,536 bytes (configurable via `/proc/sys/fs/pipe-max-size`)
- **Page-based**: Each buffer slot references a full page (4KB on most systems)
- **Partial pages**: The `offset` and `len` fields allow using portions of pages
- **Zero-copy capable**: Pages can be moved between pipes without copying

#### Capacity Constants

```c
#define PIPE_DEF_BUFFERS    16    /* Default number of buffer slots */
#define PIPE_BUF            4096  /* POSIX atomic write guarantee */
```

### Reading from a Pipe

Reading from a pipe involves extracting data from the circular buffer while handling synchronization with writers.

#### The pipe_read() Algorithm

```
algorithm: pipe_read
input:     file     - file table entry for read end
           buf      - user buffer to receive data
           count    - number of bytes requested
output:    number of bytes read, 0 for EOF, -1 for error

{
    pipe = file->f_inode->i_pipe;
    total_read = 0;

    /* Acquire pipe mutex */
    mutex_lock(&pipe->mutex);

    for (;;) {
        /* Check if data is available */
        if (pipe->head != pipe->tail) {
            /* Data available - extract it */

            while (total_read < count && pipe->head != pipe->tail) {
                /* Get buffer at tail position */
                buf_idx = pipe->tail & (pipe->ring_size - 1);
                buffer = &pipe->bufs[buf_idx];

                /* Calculate how much to read from this buffer */
                chars = min(buffer->len, count - total_read);

                /* Copy data to user space */
                copy_to_user(buf + total_read,
                            page_address(buffer->page) + buffer->offset,
                            chars);

                total_read += chars;
                buffer->offset += chars;
                buffer->len -= chars;

                /* If buffer exhausted, release it */
                if (buffer->len == 0) {
                    pipe_buf_release(pipe, buffer);
                    pipe->tail++;
                }
            }

            /* Wake up any waiting writers */
            wake_up_interruptible(&pipe->wr_wait);

            mutex_unlock(&pipe->mutex);
            return total_read;
        }

        /* No data available */

        /* Check for EOF: no data AND no writers */
        if (pipe->writers == 0) {
            mutex_unlock(&pipe->mutex);
            return 0;    /* EOF */
        }

        /* Check for non-blocking mode */
        if (file->f_flags & O_NONBLOCK) {
            mutex_unlock(&pipe->mutex);
            return -EAGAIN;
        }

        /* Check for pending signals */
        if (signal_pending(current)) {
            mutex_unlock(&pipe->mutex);
            return -ERESTARTSYS;
        }

        /* Block waiting for data */
        mutex_unlock(&pipe->mutex);
        wait_event_interruptible(pipe->rd_wait,
                                 pipe->head != pipe->tail ||
                                 pipe->writers == 0);
        mutex_lock(&pipe->mutex);
    }
}
```

#### Read Behavior Summary

| Condition                 | Blocking Mode              | Non-Blocking Mode       |
| ------------------------- | -------------------------- | ----------------------- |
| Data available            | Return data immediately    | Return data immediately |
| Pipe empty, writers exist | Block until data or signal | Return -EAGAIN          |
| Pipe empty, no writers    | Return 0 (EOF)             | Return 0 (EOF)          |

### Writing to a Pipe

Writing to a pipe involves placing data into the circular buffer, potentially blocking if the pipe is full.

#### The pipe_write() Algorithm

```
algorithm: pipe_write
input:     file     - file table entry for write end
           buf      - user buffer containing data
           count    - number of bytes to write
output:    number of bytes written, -1 for error

{
    pipe = file->f_inode->i_pipe;
    total_written = 0;

    /* Check for broken pipe (no readers) */
    if (pipe->readers == 0) {
        send_sig(SIGPIPE, current, 0);
        return -EPIPE;
    }

    mutex_lock(&pipe->mutex);

    for (;;) {
        /* Re-check for readers (may have closed while waiting) */
        if (pipe->readers == 0) {
            mutex_unlock(&pipe->mutex);
            send_sig(SIGPIPE, current, 0);
            return -EPIPE;
        }

        /* Calculate available space */
        used_buffers = pipe->head - pipe->tail;

        if (used_buffers < pipe->ring_size) {
            /* Space available */

            while (total_written < count &&
                   (pipe->head - pipe->tail) < pipe->ring_size) {

                /* Get buffer at head position */
                buf_idx = pipe->head & (pipe->ring_size - 1);
                buffer = &pipe->bufs[buf_idx];

                /* Try to merge with existing partial buffer */
                if (can_merge(buffer, count - total_written)) {
                    chars = do_merge(buffer, buf + total_written,
                                    count - total_written);
                    total_written += chars;
                    continue;
                }

                /* Allocate new page if needed */
                if (buffer->page == NULL) {
                    buffer->page = alloc_page(GFP_KERNEL);
                    if (buffer->page == NULL) {
                        if (total_written > 0)
                            break;
                        mutex_unlock(&pipe->mutex);
                        return -ENOMEM;
                    }
                    buffer->offset = 0;
                    buffer->len = 0;
                }

                /* Calculate how much to write to this buffer */
                chars = min(PAGE_SIZE - buffer->offset - buffer->len,
                           count - total_written);

                /* Copy from user space */
                copy_from_user(page_address(buffer->page) +
                              buffer->offset + buffer->len,
                              buf + total_written,
                              chars);

                buffer->len += chars;
                total_written += chars;

                /* Move head if buffer is full or no more data */
                if (buffer->len == PAGE_SIZE || total_written == count) {
                    pipe->head++;
                }
            }

            /* Wake up any waiting readers */
            wake_up_interruptible(&pipe->rd_wait);

            if (total_written > 0) {
                mutex_unlock(&pipe->mutex);
                return total_written;
            }
        }

        /* Pipe full */

        /* Check for non-blocking mode */
        if (file->f_flags & O_NONBLOCK) {
            mutex_unlock(&pipe->mutex);
            if (total_written > 0)
                return total_written;
            return -EAGAIN;
        }

        /* Check for pending signals */
        if (signal_pending(current)) {
            mutex_unlock(&pipe->mutex);
            if (total_written > 0)
                return total_written;
            return -ERESTARTSYS;
        }

        /* Block waiting for space */
        mutex_unlock(&pipe->mutex);
        wait_event_interruptible(pipe->wr_wait,
                                 (pipe->head - pipe->tail) < pipe->ring_size ||
                                 pipe->readers == 0);
        mutex_lock(&pipe->mutex);
    }
}
```

#### Write Behavior Summary

| Condition                | Blocking Mode                | Non-Blocking Mode            |
| ------------------------ | ---------------------------- | ---------------------------- |
| Space available          | Write data, wake readers     | Write data, wake readers     |
| Pipe full, readers exist | Block until space or signal  | Return -EAGAIN (or partial)  |
| No readers               | Return -EPIPE, raise SIGPIPE | Return -EPIPE, raise SIGPIPE |

### Pipe Capacity and Blocking

#### The Producer-Consumer Model

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    PIPE AS PRODUCER-CONSUMER BUFFER                        │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│    WRITER                    PIPE BUFFER                      READER       │
│   (Producer)                  (Queue)                       (Consumer)     │
│                                                                            │
│   ┌─────────┐           ┌─────────────────────┐           ┌─────────┐     │
│   │ Process │           │  ████████████░░░░░  │           │ Process │     │
│   │    A    │──write()─>│  ▲           ▲      │──read()──>│    B    │     │
│   │         │           │  │           │      │           │         │     │
│   └─────────┘           │ tail       head     │           └─────────┘     │
│       │                 │  (read)    (write)  │               │           │
│       │                 └─────────────────────┘               │           │
│       │                                                       │           │
│       │    ┌──────────────────────────────────────────┐      │           │
│       │    │ When pipe FULL (head - tail == capacity) │      │           │
│       └───>│   Writer BLOCKS on wr_wait queue         │      │           │
│            │   Until reader consumes data             │      │           │
│            └──────────────────────────────────────────┘      │           │
│                                                               │           │
│            ┌──────────────────────────────────────────┐      │           │
│            │ When pipe EMPTY (head == tail)           │<─────┘           │
│            │   Reader BLOCKS on rd_wait queue         │                  │
│            │   Until writer produces data             │                  │
│            └──────────────────────────────────────────┘                  │
│                                                                           │
│   BLOCKING SEMANTICS:                                                     │
│   • Writer waits for space (flow control)                                │
│   • Reader waits for data (synchronization)                              │
│   • Both can be interrupted by signals                                   │
│   • Non-blocking modes return EAGAIN instead                             │
│                                                                           │
└───────────────────────────────────────────────────────────────────────────┘
```

#### Capacity Limits

```c
/* System-wide limits (from /proc/sys/fs/) */
/proc/sys/fs/pipe-max-size        /* Maximum pipe capacity (bytes) */
/proc/sys/fs/pipe-user-pages-hard /* Hard limit on pipe pages per user */
/proc/sys/fs/pipe-user-pages-soft /* Soft limit (after which unprivileged
                                     users can't increase pipe size) */
```

#### The F_SETPIPE_SZ Operation

The `fcntl()` system call can adjust pipe capacity:

```c
int new_size = fcntl(pipefd[1], F_SETPIPE_SZ, desired_size);
int cur_size = fcntl(pipefd[1], F_GETPIPE_SZ);
```

---

## 4. Named Pipes (FIFOs)

While anonymous pipes require a parent-child relationship (the child inherits the pipe from fork()), **named pipes** (FIFOs) exist in the filesystem and can connect unrelated processes.

### Why Is It Called "FIFO"?

The name **FIFO** stands for **First In, First Out** — the fundamental data structure behavior of a pipe.

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    WHY THE NAME "FIFO"?                                    │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   FIFO = First In, First Out                                               │
│                                                                            │
│   It describes HOW DATA FLOWS through the pipe:                            │
│                                                                            │
│   ┌─────────────────────────────────────────────────────────────────┐     │
│   │                                                                  │     │
│   │   WRITE END                                          READ END    │     │
│   │      │                                                  │        │     │
│   │      ▼                                                  ▼        │     │
│   │   ═══════════════════════════════════════════════════════════    │     │
│   │   │ A │ B │ C │ D │ E │ F │ ─────────────────────────────> │    │     │
│   │   ═══════════════════════════════════════════════════════════    │     │
│   │     ▲                                                   ▲        │     │
│   │     │                                                   │        │     │
│   │   First                                               First      │     │
│   │   written                                             read       │     │
│   │                                                                  │     │
│   │   • 'A' was written FIRST → 'A' is read FIRST                    │     │
│   │   • 'F' was written LAST  → 'F' is read LAST                     │     │
│   │   • Order is PRESERVED - no random access!                       │     │
│   │                                                                  │     │
│   └─────────────────────────────────────────────────────────────────┘     │
│                                                                            │
│   CONTRAST WITH OTHER DATA STRUCTURES:                                     │
│                                                                            │
│   ┌─────────────────┬─────────────────────────────────────────────┐       │
│   │ Structure       │ Behavior                                    │       │
│   ├─────────────────┼─────────────────────────────────────────────┤       │
│   │ FIFO (Queue)    │ First In, First Out - like a pipe/line      │       │
│   │ LIFO (Stack)    │ Last In, First Out - like a stack of plates │       │
│   │ Random Access   │ Access any position - like an array/file    │       │
│   └─────────────────┴─────────────────────────────────────────────┘       │
│                                                                            │
│   A pipe is essentially a QUEUE in kernel memory:                          │
│   • You can only APPEND to one end (write)                                 │
│   • You can only REMOVE from the other end (read)                          │
│   • You CANNOT seek, rewind, or access the middle                          │
│   • Data is CONSUMED when read (not copied - it's gone!)                   │
│                                                                            │
│   THE TWO NAMES:                                                           │
│   ┌─────────────────────────────────────────────────────────────────┐     │
│   │                                                                  │     │
│   │   "Named Pipe"  = Emphasizes it has a FILESYSTEM NAME/PATH       │     │
│   │                   (unlike anonymous pipes which have no name)    │     │
│   │                                                                  │     │
│   │   "FIFO"        = Emphasizes the DATA STRUCTURE behavior         │     │
│   │                   (First In, First Out queue semantics)          │     │
│   │                                                                  │     │
│   │   Both terms refer to the SAME thing!                            │     │
│   │                                                                  │     │
│   └─────────────────────────────────────────────────────────────────┘     │
│                                                                            │
│   HISTORICAL NOTE:                                                         │
│   The term "FIFO" was chosen because Unix already had "pipes" (anonymous   │
│   pipes), and the new filesystem-visible version needed a distinct name.   │
│   Since the key characteristic is the queue-like FIFO behavior, that       │
│   became the name. The 'p' in `ls -l` output stands for "pipe":            │
│                                                                            │
│   $ ls -l /tmp/myfifo                                                      │
│   prw-r--r-- 1 user user 0 Feb 12 10:00 /tmp/myfifo                        │
│   │                                                                        │
│   └── 'p' = pipe (FIFO)                                                    │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```

**Key insight**: Both anonymous pipes and named pipes (FIFOs) have FIFO behavior — data comes out in the same order it went in. The difference is that a "named pipe" has a path in the filesystem, while an anonymous pipe does not.

### Why Do We Need Named Pipes? The Parent-Child Problem Explained

**The fundamental problem with anonymous pipes:**

An anonymous pipe created by `pipe()` exists ONLY in kernel memory—it has no name, no filesystem
presence, nothing that another process can use to find it. The ONLY way to get access to a pipe's
file descriptors is to **inherit them**.

```
┌───────────────────────────────────────────────────────────────────────────┐
│           THE PROBLEM: HOW DO PROCESSES SHARE A PIPE?                      │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   SCENARIO 1: Parent creates pipe, then forks (WORKS!)                     │
│   ═══════════════════════════════════════════════════                      │
│                                                                            │
│   TIME ──────────────────────────────────────────────────────────────>     │
│                                                                            │
│   Step 1: Parent calls pipe()                                              │
│   ┌─────────────────────────────────────────────────────────────────┐     │
│   │  Parent Process (PID 100)                                        │     │
│   │  ┌──────────────┐                                                │     │
│   │  │ fd table:    │         Kernel Memory                          │     │
│   │  │ 0: stdin     │         ┌─────────────────┐                    │     │
│   │  │ 1: stdout    │         │   PIPE BUFFER   │                    │     │
│   │  │ 2: stderr    │         │   (no name!)    │                    │     │
│   │  │ 3: read_end ─┼────────>│                 │                    │     │
│   │  │ 4: write_end─┼────────>│                 │                    │     │
│   │  └──────────────┘         └─────────────────┘                    │     │
│   └─────────────────────────────────────────────────────────────────┘     │
│                                                                            │
│   Step 2: Parent calls fork() - child INHERITS fd table                    │
│   ┌─────────────────────────────────────────────────────────────────┐     │
│   │  Parent (PID 100)              Child (PID 101)                   │     │
│   │  ┌──────────────┐              ┌──────────────┐                  │     │
│   │  │ fd table:    │              │ fd table:    │  ◄── COPY!       │     │
│   │  │ 0: stdin     │              │ 0: stdin     │                  │     │
│   │  │ 1: stdout    │              │ 1: stdout    │                  │     │
│   │  │ 2: stderr    │              │ 2: stderr    │                  │     │
│   │  │ 3: read_end ─┼──┐       ┌──>│ 3: read_end ─┼──┐               │     │
│   │  │ 4: write_end─┼──┼───┐   │   │ 4: write_end─┼──┼──┐            │     │
│   │  └──────────────┘  │   │   │   └──────────────┘  │  │            │     │
│   │                    │   │   │                     │  │            │     │
│   │                    │   │   │   Kernel Memory     │  │            │     │
│   │                    │   │   │   ┌─────────────┐   │  │            │     │
│   │                    │   │   │   │ PIPE BUFFER │   │  │            │     │
│   │                    └───┼───┼──>│             │<──┘  │            │     │
│   │                        └───┼──>│             │<─────┘            │     │
│   │                            │   └─────────────┘                   │     │
│   │                            │                                     │     │
│   │   Both processes can now   │                                     │     │
│   │   access the SAME pipe!    │                                     │     │
│   └────────────────────────────┴─────────────────────────────────────┘     │
│                                                                            │
│   ✓ This works because fork() copies the file descriptor table            │
│   ✓ Child inherits pointers to the same kernel pipe structure             │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```

**But what if the processes are NOT related?**

```
┌───────────────────────────────────────────────────────────────────────────┐
│   SCENARIO 2: Two unrelated processes want to communicate (FAILS!)         │
│   ════════════════════════════════════════════════════════════════         │
│                                                                            │
│   Process A (PID 100)              Process B (PID 200)                     │
│   Started by: ./server             Started by: ./client                    │
│   Started at: 10:00 AM             Started at: 10:05 AM                    │
│                                                                            │
│   ┌──────────────────┐             ┌──────────────────┐                   │
│   │ Process A        │             │ Process B        │                   │
│   │                  │             │                  │                   │
│   │ pipe(fd);        │             │ // How do I get  │                   │
│   │ // Creates pipe  │             │ // access to A's │                   │
│   │ // fd[0], fd[1]  │             │ // pipe???       │                   │
│   │                  │             │                  │                   │
│   │ // The pipe has  │             │ // I can't!      │                   │
│   │ // NO NAME!      │             │ // There's no    │                   │
│   │ // It's just in  │             │ // way to find   │                   │
│   │ // kernel memory │             │ // it!           │                   │
│   └──────────────────┘             └──────────────────┘                   │
│           │                                 │                              │
│           │                                 │                              │
│           ▼                                 ▼                              │
│   ┌─────────────────┐              ┌─────────────────┐                    │
│   │   PIPE BUFFER   │              │   ??? WHERE ??? │                    │
│   │   (in kernel)   │              │                 │                    │
│   │   No path!      │              │   Process B has │                    │
│   │   No name!      │              │   NO WAY to get │                    │
│   │   No inode #!   │              │   a reference   │                    │
│   └─────────────────┘              └─────────────────┘                    │
│                                                                            │
│   ✗ Process B was NOT forked from Process A                               │
│   ✗ Process B did NOT inherit A's file descriptors                        │
│   ✗ There is NO filesystem path to open()                                 │
│   ✗ IMPOSSIBLE to connect!                                                │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```

**The solution: Give the pipe a NAME in the filesystem!**

```
┌───────────────────────────────────────────────────────────────────────────┐
│   SCENARIO 3: Named Pipe (FIFO) - Unrelated processes CAN communicate!    │
│   ═════════════════════════════════════════════════════════════════════    │
│                                                                            │
│   Step 1: Someone creates a FIFO with a filesystem path                    │
│                                                                            │
│   $ mkfifo /tmp/myfifo                                                     │
│   $ ls -l /tmp/myfifo                                                      │
│   prw-r--r-- 1 user user 0 Feb 12 10:00 /tmp/myfifo                        │
│   ^                                                                        │
│   └── 'p' means it's a pipe (FIFO)                                         │
│                                                                            │
│   Now in the filesystem:                                                   │
│   ┌─────────────────────────────────────────────────────────────────┐     │
│   │  /tmp/                                                           │     │
│   │    └── myfifo  ──────> FIFO inode (i_mode = S_IFIFO)             │     │
│   │                        This inode has a NAME and PATH!           │     │
│   └─────────────────────────────────────────────────────────────────┘     │
│                                                                            │
│   Step 2: ANY process can now open() it by path!                           │
│                                                                            │
│   Process A (PID 100)              Process B (PID 200)                     │
│   ┌──────────────────┐             ┌──────────────────┐                   │
│   │                  │             │                  │                   │
│   │ fd = open(       │             │ fd = open(       │                   │
│   │   "/tmp/myfifo", │             │   "/tmp/myfifo", │                   │
│   │   O_WRONLY);     │             │   O_RDONLY);     │                   │
│   │                  │             │                  │                   │
│   │ write(fd, data); │             │ read(fd, buf);   │                   │
│   │                  │             │                  │                   │
│   └────────┬─────────┘             └────────┬─────────┘                   │
│            │                                │                              │
│            │      ┌─────────────────┐       │                              │
│            │      │   FILESYSTEM    │       │                              │
│            │      │  /tmp/myfifo    │       │                              │
│            │      │       │         │       │                              │
│            │      │       ▼         │       │                              │
│            │      │  ┌─────────┐    │       │                              │
│            └──────┼─>│  FIFO   │<───┼───────┘                              │
│                   │  │  inode  │    │                                      │
│                   │  │    │    │    │                                      │
│                   │  │    ▼    │    │                                      │
│                   │  │ ┌─────┐ │    │                                      │
│                   │  │ │PIPE │ │    │                                      │
│                   │  │ │BUF  │ │    │                                      │
│                   │  │ └─────┘ │    │                                      │
│                   │  └─────────┘    │                                      │
│                   └─────────────────┘                                      │
│                                                                            │
│   ✓ Both processes use the SAME PATH: "/tmp/myfifo"                       │
│   ✓ The filesystem provides the "meeting point"                           │
│   ✓ No inheritance needed - just know the path!                           │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```

**Real-world examples where named pipes are essential:**

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    REAL-WORLD USE CASES FOR FIFOs                          │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   1. CLIENT-SERVER ARCHITECTURE                                            │
│   ─────────────────────────────                                            │
│   Server starts first, creates /var/run/myserver.fifo                      │
│   Clients start later, connect by opening the same path                    │
│                                                                            │
│   $ ./server &                    # Creates FIFO, waits for clients        │
│   $ ./client request1             # Opens FIFO, sends request              │
│   $ ./client request2             # Different client, same FIFO            │
│                                                                            │
│   2. LOGGING DAEMON                                                        │
│   ─────────────────                                                        │
│   $ mkfifo /var/log/app.pipe                                               │
│   $ ./log_processor < /var/log/app.pipe &   # Reads from FIFO              │
│   $ ./app1 > /var/log/app.pipe              # Writes to FIFO               │
│   $ ./app2 > /var/log/app.pipe              # Another writer               │
│                                                                            │
│   3. SHELL PIPELINES WITH PERSISTENCE                                      │
│   ────────────────────────────────────                                     │
│   $ mkfifo /tmp/data_pipe                                                  │
│   $ tail -f /var/log/syslog > /tmp/data_pipe &   # Producer                │
│   $ grep "error" < /tmp/data_pipe                 # Consumer               │
│                                                                            │
│   4. INTER-APPLICATION COMMUNICATION                                       │
│   ──────────────────────────────────                                       │
│   A Python script and a C program need to communicate:                     │
│   - Neither is parent/child of the other                                   │
│   - They agree on a path: /tmp/py_to_c.fifo                                │
│   - Python writes, C reads (or vice versa)                                 │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```

**Summary: Anonymous Pipe vs Named Pipe**

| Aspect                  | Anonymous Pipe (`pipe()`)        | Named Pipe (FIFO)                |
| ----------------------- | -------------------------------- | -------------------------------- |
| **Has filesystem path** | NO                               | YES (`/tmp/myfifo`)              |
| **How to access**       | Inherit fd via `fork()`          | `open("/path/to/fifo")`          |
| **Who can use it**      | Parent + children only           | ANY process with permissions     |
| **Lifetime**            | Until all fds closed             | Until `unlink()` (persists!)     |
| **Typical use**         | Shell pipelines (`ls \| grep`)   | Client-server, daemons           |
| **Created by**          | `pipe()` system call             | `mkfifo()` or `mknod()`          |

### FIFO Creation and the Filesystem

A FIFO is created using `mkfifo()` or `mknod()`:

```c
#include <sys/types.h>
#include <sys/stat.h>

int mkfifo(const char *pathname, mode_t mode);
int mknod(const char *pathname, mode_t mode | S_IFIFO, 0);
```

#### The mkfifo() Algorithm

```
algorithm: sys_mkfifo
input:     pathname - path where FIFO will appear in filesystem
           mode     - permission bits (umask applied)
output:    0 on success, -1 on error

{
    /* Step 1: Lookup parent directory */
    dir_inode = namei(dirname(pathname));
    if (dir_inode == NULL) {
        return -ENOENT;
    }

    /* Step 2: Check permissions in parent directory */
    if (!may_create(dir_inode, current->cred)) {
        iput(dir_inode);
        return -EACCES;
    }

    /* Step 3: Check if name already exists */
    existing = lookup(dir_inode, basename(pathname));
    if (existing != NULL) {
        iput(dir_inode);
        iput(existing);
        return -EEXIST;
    }

    /* Step 4: Allocate new inode */
    fifo_inode = new_inode(dir_inode->i_sb);
    if (fifo_inode == NULL) {
        iput(dir_inode);
        return -ENOSPC;
    }

    /* Step 5: Initialize FIFO inode */
    fifo_inode->i_mode = S_IFIFO | (mode & ~current->umask);
    fifo_inode->i_uid = current->uid;
    fifo_inode->i_gid = current->gid;
    fifo_inode->i_size = 0;
    fifo_inode->i_op = &fifo_inode_operations;
    fifo_inode->i_fop = &pipefifo_fops;
    fifo_inode->i_nlink = 1;    /* Note: FIFOs have directory entry */
    fifo_inode->i_pipe = NULL;  /* Created on first open */

    /* Step 6: Create directory entry */
    error = dir_inode->i_op->mknod(dir_inode, dentry, fifo_inode);

    iput(dir_inode);
    return error;
}
```

#### FIFO vs Anonymous Pipe: Key Differences

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    ANONYMOUS PIPE vs NAMED PIPE (FIFO)                     │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   ANONYMOUS PIPE                      NAMED PIPE (FIFO)                    │
│   ══════════════                      ═════════════════                    │
│                                                                            │
│   Created by: pipe()                  Created by: mkfifo(), mknod()        │
│                                                                            │
│   Lifetime: until last                Lifetime: until unlink()             │
│             fd closed                           (persists in filesystem)   │
│                                                                            │
│   i_nlink: 0                          i_nlink: 1 (has directory entry)     │
│   (no filesystem presence)            (visible via ls, stat, etc.)         │
│                                                                            │
│   Access: inherited via               Access: via open() with pathname     │
│           fork()                                                           │
│                                                                            │
│   Processes: must be                  Processes: any with path and         │
│              related                             permissions               │
│                                                                            │
│   ┌─────────┐     ┌─────────┐        ┌─────────┐  /tmp/   ┌─────────┐     │
│   │ Parent  │────>│ Child   │        │ ProcA   │  myfifo  │ ProcB   │     │
│   │ pipe[1] │     │ pipe[0] │        │ open()  │<────────>│ open()  │     │
│   └─────────┘     └─────────┘        └─────────┘          └─────────┘     │
│        │               │                  │                    │          │
│        └───────┬───────┘                  │                    │          │
│                ▼                          ▼                    ▼          │
│   ┌───────────────────────┐      ┌─────────────────────────────────┐     │
│   │   Pipe Inode          │      │   FIFO Inode                    │     │
│   │   (kernel only)       │      │   (in filesystem + kernel)      │     │
│   │   i_nlink = 0         │      │   i_nlink = 1                   │     │
│   │   i_pipe: buffer      │      │   i_pipe: buffer (when open)    │     │
│   └───────────────────────┘      └─────────────────────────────────┘     │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```

### Opening a FIFO

Opening a FIFO has unique semantics that differ from regular files.

#### The FIFO open() Algorithm

```
algorithm: fifo_open
input:     inode    - FIFO inode
           file     - file table entry being initialized
           flags    - O_RDONLY, O_WRONLY, O_RDWR, O_NONBLOCK
output:    0 on success, -1 on error

{
    pipe = inode->i_pipe;

    /* Step 1: Create pipe_inode_info if first open */
    if (pipe == NULL) {
        pipe = alloc_pipe_info();
        if (pipe == NULL)
            return -ENOMEM;
        inode->i_pipe = pipe;
    }

    /* Step 2: Handle according to access mode */

    if (flags & O_RDONLY) {
        /* Opening for reading */
        pipe->r_counter++;
        pipe->readers++;

        if (!(flags & O_NONBLOCK)) {
            /* Block until a writer opens */
            while (pipe->w_counter == 0) {
                if (signal_pending(current)) {
                    pipe->r_counter--;
                    pipe->readers--;
                    return -ERESTARTSYS;
                }
                /* Wait for writer */
                wait_event_interruptible(pipe->rd_wait,
                                        pipe->w_counter > 0);
            }
        }

        /* Wake any blocked writers */
        wake_up_interruptible(&pipe->wr_wait);
    }

    else if (flags & O_WRONLY) {
        /* Opening for writing */

        if (!(flags & O_NONBLOCK) && pipe->r_counter == 0) {
            /* No readers and blocking mode */
            return -ENXIO;    /* POSIX requirement */
        }

        pipe->w_counter++;
        pipe->writers++;

        if (!(flags & O_NONBLOCK)) {
            /* Block until a reader opens */
            while (pipe->r_counter == 0) {
                if (signal_pending(current)) {
                    pipe->w_counter--;
                    pipe->writers--;
                    return -ERESTARTSYS;
                }
                wait_event_interruptible(pipe->wr_wait,
                                        pipe->r_counter > 0);
            }
        }

        /* Wake any blocked readers */
        wake_up_interruptible(&pipe->rd_wait);
    }

    else if (flags & O_RDWR) {
        /* Opening for both - doesn't block */
        pipe->r_counter++;
        pipe->w_counter++;
        pipe->readers++;
        pipe->writers++;

        /* Wake anyone waiting */
        wake_up_interruptible(&pipe->rd_wait);
        wake_up_interruptible(&pipe->wr_wait);
    }

    /* Step 3: Set up file table entry */
    file->private_data = pipe;

    return 0;
}
```

### FIFO Semantics

#### Opening Behavior Matrix

| Open Mode                | No Other End Open            | Other End Open     |
| ------------------------ | ---------------------------- | ------------------ |
| `O_RDONLY`               | **Block** until writer opens | Return immediately |
| `O_RDONLY \| O_NONBLOCK` | Return immediately           | Return immediately |
| `O_WRONLY`               | **Block** until reader opens | Return immediately |
| `O_WRONLY \| O_NONBLOCK` | Return **ENXIO** error       | Return immediately |
| `O_RDWR`                 | Return immediately           | Return immediately |

#### FIFO Lifecycle

```
┌───────────────────────────────────────────────────────────────────────────┐
│                         FIFO LIFECYCLE                                     │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   1. CREATION (mkfifo)                                                     │
│   ┌────────────────────────────────────────────────────────────────┐      │
│   │  $ mkfifo /tmp/myfifo                                          │      │
│   │                                                                 │      │
│   │  Filesystem:  /tmp/myfifo (inode with S_IFIFO mode)            │      │
│   │  Kernel:      No pipe_inode_info yet (i_pipe = NULL)           │      │
│   └────────────────────────────────────────────────────────────────┘      │
│                                                                            │
│   2. FIRST OPEN (either end)                                               │
│   ┌────────────────────────────────────────────────────────────────┐      │
│   │  Reader: $ cat < /tmp/myfifo &    (blocks waiting for writer)  │      │
│   │                                                                 │      │
│   │  Kernel: allocate pipe_inode_info                              │      │
│   │          readers = 1, writers = 0                              │      │
│   │          Process sleeping on rd_wait                           │      │
│   └────────────────────────────────────────────────────────────────┘      │
│                                                                            │
│   3. SECOND OPEN (other end)                                               │
│   ┌────────────────────────────────────────────────────────────────┐      │
│   │  Writer: $ echo "hello" > /tmp/myfifo                          │      │
│   │                                                                 │      │
│   │  Kernel: readers = 1, writers = 1                              │      │
│   │          Wake reader from rd_wait                              │      │
│   │          Both processes continue                               │      │
│   └────────────────────────────────────────────────────────────────┘      │
│                                                                            │
│   4. DATA TRANSFER                                                         │
│   ┌────────────────────────────────────────────────────────────────┐      │
│   │  Writer writes "hello\n" -> pipe buffer                        │      │
│   │  Reader reads "hello\n" <- pipe buffer                         │      │
│   │  (Same semantics as anonymous pipe)                            │      │
│   └────────────────────────────────────────────────────────────────┘      │
│                                                                            │
│   5. CLOSE (one end)                                                       │
│   ┌────────────────────────────────────────────────────────────────┐      │
│   │  Writer closes: writers = 0                                    │      │
│   │  Reader gets EOF (read returns 0)                              │      │
│   │                                                                 │      │
│   │  Kernel: pipe buffer freed when last reference closes          │      │
│   │          FIFO inode remains (i_pipe = NULL again)              │      │
│   └────────────────────────────────────────────────────────────────┘      │
│                                                                            │
│   6. REUSE                                                                 │
│   ┌────────────────────────────────────────────────────────────────┐      │
│   │  FIFO can be opened again - new pipe buffer allocated          │      │
│   │  Previous data is gone (pipe buffer was freed)                 │      │
│   └────────────────────────────────────────────────────────────────┘      │
│                                                                            │
│   7. DELETION (unlink)                                                     │
│   ┌────────────────────────────────────────────────────────────────┐      │
│   │  $ rm /tmp/myfifo                                              │      │
│   │                                                                 │      │
│   │  Directory entry removed                                       │      │
│   │  Inode freed when i_count reaches 0                            │      │
│   │  (Same as regular file deletion)                               │      │
│   └────────────────────────────────────────────────────────────────┘      │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```

---

## 5. Client-Server Architecture with Pipes

The client-server model is a fundamental pattern in systems programming. Pipes, despite their simplicity, can implement sophisticated client-server architectures.

### The Stevens Two-Pipe Pattern: Bidirectional Communication

One of the most important patterns from W. Richard Stevens' "Unix Network Programming" is the
**two-pipe pattern** for bidirectional parent-child communication. Let's analyze it in detail.

#### The Problem: Pipes Are Unidirectional

A single pipe only flows in ONE direction:

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    THE UNIDIRECTIONAL PROBLEM                              │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   With ONE pipe, you can only go ONE way:                                  │
│                                                                            │
│   ┌────────┐         ┌─────────────────┐         ┌────────┐               │
│   │ Parent │ ──────> │   PIPE BUFFER   │ ──────> │ Child  │               │
│   │ writes │         │   (one-way!)    │         │ reads  │               │
│   └────────┘         └─────────────────┘         └────────┘               │
│                                                                            │
│   But what if the child needs to RESPOND?                                  │
│                                                                            │
│   Parent: "What is 2 + 2?"  ────────────────────>  Child receives         │
│   Parent: waiting...                               Child: "4"             │
│   Parent: still waiting...                         Child: How do I send   │
│   Parent: ???                                             it back???      │
│                                                                            │
│   ✗ The child CANNOT write back through the same pipe!                    │
│   ✗ Pipes are NOT bidirectional!                                          │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```

#### "But Wait—Can't the Child Write to the Same Pipe?"

A common question: After `fork()`, the child inherits BOTH `fd[3]` (read end) AND `fd[4]`
(write end). So technically, couldn't the child just write to `fd[4]`?

**Yes, it CAN. But the problem isn't capability—it's DATA INTEGRITY.**

```
┌───────────────────────────────────────────────────────────────────────────┐
│   WHAT HAPPENS IF CHILD WRITES TO THE SAME PIPE IT READS FROM?             │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   After fork(), with ONE pipe:                                             │
│                                                                            │
│   Parent                              Child                                │
│   ┌──────────────┐                    ┌──────────────┐                    │
│   │ fd[3] = READ │                    │ fd[3] = READ │                    │
│   │ fd[4] = WRITE│                    │ fd[4] = WRITE│                    │
│   └──────┬───────┘                    └──────┬───────┘                    │
│          │                                   │                             │
│          │         ┌─────────────┐           │                             │
│          └────────>│ PIPE BUFFER │<──────────┘                             │
│                    │   (shared!) │                                         │
│                    └─────────────┘                                         │
│                                                                            │
│   PROBLEM: Both processes share the SAME buffer!                           │
│                                                                            │
│   Scenario:                                                                │
│   1. Parent writes "What is 2+2?" to fd[4]                                 │
│   2. Child reads from fd[3], gets "What is 2+2?"  ✓                        │
│   3. Child writes "4" to fd[4]                                             │
│   4. Parent reads from fd[3]... but WAIT!                                  │
│                                                                            │
│   WHO GETS THE DATA???                                                     │
│                                                                            │
│               ┌───────────────────────────────────────────────┐           │
│               │              PIPE BUFFER                      │           │
│               │              ┌───────┐                        │           │
│               │              │  "4"  │                        │           │
│               │              └───┬───┘                        │           │
│               │                  │                            │           │
│               │      ┌───────────┴───────────┐                │           │
│               │      ▼                       ▼                │           │
│               │ ┌────────┐              ┌────────┐            │           │
│               │ │ Parent │              │ Child  │            │           │
│               │ │ read() │              │ read() │            │           │
│               │ └────────┘              └────────┘            │           │
│               │                                               │           │
│               │   RACE CONDITION! Either one might get it!    │           │
│               └───────────────────────────────────────────────┘           │
│                                                                            │
│   • Parent might accidentally read its OWN question back                   │
│   • Child might accidentally read its OWN answer back                      │
│   • Data from both processes gets INTERLEAVED and MIXED!                   │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```

**The Core Issue: A Pipe is Just ONE Queue**

```
┌───────────────────────────────────────────────────────────────────────────┐
│   A PIPE IS A SINGLE FIFO BUFFER - NOT TWO SEPARATE CHANNELS               │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   Think of a pipe like a TUBE:                                             │
│                                                                            │
│   ════════════════════════════════════════════════════════                 │
│   IN ──────> [data][data][data][data] ──────> OUT                          │
│   ════════════════════════════════════════════════════════                 │
│                                                                            │
│   • There's ONE entrance (write end)                                       │
│   • There's ONE exit (read end)                                            │
│   • Data comes out in the ORDER it went in (FIFO)                          │
│   • ANYONE with the read end can read                                      │
│   • ANYONE with the write end can write                                    │
│                                                                            │
│   If both parent and child write AND read from the same pipe:              │
│                                                                            │
│   Time 1: Parent writes "REQUEST"                                          │
│   Time 2: Child writes "RESPONSE"                                          │
│                                                                            │
│   Buffer: [R][E][Q][U][E][S][T][R][E][S][P][O][N][S][E]                    │
│                                                                            │
│   When parent calls read()... it might get:                                │
│   • "REQUEST" (its own data!) - WRONG                                      │
│   • "RESPONSE" (the reply) - CORRECT (if lucky)                            │
│   • "UESTRES" (partial mix) - CORRUPTION                                   │
│                                                                            │
│   There's NO WAY to separate "this byte is from parent" vs                 │
│                              "this byte is from child"                     │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```

**Summary: Why One Pipe Doesn't Work for Bidirectional Communication**

| Approach | Result |
|----------|--------|
| One pipe, both processes read & write | **BROKEN**: Data gets mixed. Race condition on reads. No message boundaries. Parent might read its own data. |
| Two pipes, dedicated directions | **CORRECT**: Clean separation. Pipe1 = requests only. Pipe2 = responses only. No mixing possible! |

The child *can* write to the pipe—the issue is that with one pipe, **you can't tell
whose data is whose**. Two pipes solve this by providing dedicated, one-way channels.

#### The Solution: Use TWO Pipes

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    THE TWO-PIPE SOLUTION                                   │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   pipe1: Parent ──────────────────────────────────────────> Child          │
│          (parent writes requests, child reads requests)                    │
│                                                                            │
│   pipe2: Parent <────────────────────────────────────────── Child          │
│          (child writes responses, parent reads responses)                  │
│                                                                            │
│   ┌────────────┐                                      ┌────────────┐      │
│   │            │ ════════ pipe1 (request) ═════════> │            │      │
│   │   PARENT   │                                      │   CHILD    │      │
│   │  (client)  │ <═══════ pipe2 (response) ════════  │  (server)  │      │
│   │            │                                      │            │      │
│   └────────────┘                                      └────────────┘      │
│                                                                            │
│   Now bidirectional communication is possible!                             │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```

#### The Stevens Code Explained Step-by-Step

Here's the code from Stevens' book with detailed annotations:

```c
int main(int argc, char **argv)
{
    int   pipe1[2], pipe2[2];   /* Two pipes: 4 file descriptors total */
    pid_t childpid;

    Pipe(pipe1);    /* Create first pipe:  pipe1[0]=read, pipe1[1]=write */
    Pipe(pipe2);    /* Create second pipe: pipe2[0]=read, pipe2[1]=write */

    if ((childpid = Fork()) == 0) {
        /* ══════════════════════════════════════════════════════════════ */
        /* CHILD PROCESS                                                   */
        /* ══════════════════════════════════════════════════════════════ */
        Close(pipe1[1]);    /* Child closes pipe1 WRITE end */
        Close(pipe2[0]);    /* Child closes pipe2 READ end */

        server(pipe1[0], pipe2[1]);  /* Child: reads from pipe1, writes to pipe2 */
        exit(0);
    }

    /* ══════════════════════════════════════════════════════════════════ */
    /* PARENT PROCESS                                                      */
    /* ══════════════════════════════════════════════════════════════════ */
    Close(pipe1[0]);    /* Parent closes pipe1 READ end */
    Close(pipe2[1]);    /* Parent closes pipe2 WRITE end */

    client(pipe2[0], pipe1[1]);  /* Parent: reads from pipe2, writes to pipe1 */

    /* ... */
}
```

#### Visual Walkthrough: Before and After fork()

```
┌───────────────────────────────────────────────────────────────────────────┐
│   STEP 1: BEFORE fork() - Parent creates both pipes                        │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   After Pipe(pipe1) and Pipe(pipe2), parent has:                           │
│                                                                            │
│   Parent Process                                                           │
│   ┌─────────────────────────────────────────────────────────────────┐     │
│   │  File Descriptor Table:                                          │     │
│   │  ┌─────┬─────┬─────┬─────┬─────┬─────┬─────┐                    │     │
│   │  │  0  │  1  │  2  │  3  │  4  │  5  │  6  │                    │     │
│   │  │stdin│stdout│stderr│     │     │     │     │                    │     │
│   │  │     │     │     │pipe1│pipe1│pipe2│pipe2│                    │     │
│   │  │     │     │     │[0]  │[1]  │[0]  │[1]  │                    │     │
│   │  │     │     │     │READ │WRITE│READ │WRITE│                    │     │
│   │  └─────┴─────┴─────┴──┬──┴──┬──┴──┬──┴──┬──┘                    │     │
│   └───────────────────────┼─────┼─────┼─────┼───────────────────────┘     │
│                           │     │     │     │                              │
│                           ▼     ▼     ▼     ▼                              │
│                      ┌─────────────┐  ┌─────────────┐                      │
│                      │   PIPE 1    │  │   PIPE 2    │                      │
│                      │   BUFFER    │  │   BUFFER    │                      │
│                      └─────────────┘  └─────────────┘                      │
│                                                                            │
│   At this point, parent has ALL FOUR ends of both pipes!                   │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘

┌───────────────────────────────────────────────────────────────────────────┐
│   STEP 2: AFTER fork() - Child inherits ALL file descriptors              │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   Parent Process                         Child Process                     │
│   ┌───────────────────────┐              ┌───────────────────────┐        │
│   │  fd 3: pipe1[0] READ  │              │  fd 3: pipe1[0] READ  │        │
│   │  fd 4: pipe1[1] WRITE │              │  fd 4: pipe1[1] WRITE │        │
│   │  fd 5: pipe2[0] READ  │              │  fd 5: pipe2[0] READ  │        │
│   │  fd 6: pipe2[1] WRITE │              │  fd 6: pipe2[1] WRITE │        │
│   └───────────┬───────────┘              └───────────┬───────────┘        │
│               │                                      │                     │
│               │      ┌─────────────┐                 │                     │
│               ├─────>│   PIPE 1    │<────────────────┤                     │
│               │      │   BUFFER    │                 │                     │
│               │      └─────────────┘                 │                     │
│               │                                      │                     │
│               │      ┌─────────────┐                 │                     │
│               └─────>│   PIPE 2    │<────────────────┘                     │
│                      │   BUFFER    │                                       │
│                      └─────────────┘                                       │
│                                                                            │
│   PROBLEM: Both processes have ALL ends of BOTH pipes!                     │
│   This is a MESS - we need to clean it up!                                 │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘

┌───────────────────────────────────────────────────────────────────────────┐
│   STEP 3: Close unused ends - THE CRITICAL STEP!                           │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   CHILD executes:                        PARENT executes:                  │
│   Close(pipe1[1]);  /* don't write */    Close(pipe1[0]);  /* don't read */│
│   Close(pipe2[0]);  /* don't read  */    Close(pipe2[1]);  /* don't write*/│
│                                                                            │
│   Parent Process                         Child Process                     │
│   ┌───────────────────────┐              ┌───────────────────────┐        │
│   │  fd 3: CLOSED ✗       │              │  fd 3: pipe1[0] READ ✓│        │
│   │  fd 4: pipe1[1] WRITE✓│              │  fd 4: CLOSED ✗       │        │
│   │  fd 5: pipe2[0] READ ✓│              │  fd 5: CLOSED ✗       │        │
│   │  fd 6: CLOSED ✗       │              │  fd 6: pipe2[1] WRITE✓│        │
│   └───────────┬───────────┘              └───────────┬───────────┘        │
│               │                                      │                     │
│               │                                      │                     │
│   WRITE only  │      ┌─────────────┐                 │  READ only          │
│   (fd 4) ─────┼─────>│   PIPE 1    │─────────────────┼──> (fd 3)           │
│               │      │  (request)  │                 │                     │
│               │      └─────────────┘                 │                     │
│               │                                      │                     │
│   READ only   │      ┌─────────────┐                 │  WRITE only         │
│   (fd 5) <────┼──────│   PIPE 2    │<────────────────┼─── (fd 6)           │
│               │      │  (response) │                 │                     │
│               │      └─────────────┘                 │                     │
│               │                                      │                     │
└───────────────────────────────────────────────────────────────────────────┘

┌───────────────────────────────────────────────────────────────────────────┐
│   FINAL STATE: Clean bidirectional communication                           │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   ┌────────────────┐                           ┌────────────────┐         │
│   │     PARENT     │                           │     CHILD      │         │
│   │    (client)    │                           │    (server)    │         │
│   │                │                           │                │         │
│   │  pipe1[1]=4 ───┼── PIPE 1 (requests) ─────>┼─── pipe1[0]=3  │         │
│   │  (write end)   │                           │   (read end)   │         │
│   │                │                           │                │         │
│   │  pipe2[0]=5 <──┼── PIPE 2 (responses) <────┼─── pipe2[1]=6  │         │
│   │  (read end)    │                           │   (write end)  │         │
│   │                │                           │                │         │
│   └────────────────┘                           └────────────────┘         │
│                                                                            │
│   Communication flow:                                                      │
│   1. Parent writes request to pipe1[1]                                     │
│   2. Child reads request from pipe1[0]                                     │
│   3. Child processes request                                               │
│   4. Child writes response to pipe2[1]                                     │
│   5. Parent reads response from pipe2[0]                                   │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```

#### Why Must We Close the Unused Ends?

This is **critical** and often confuses beginners. There are THREE reasons:

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    WHY CLOSE UNUSED PIPE ENDS?                             │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   REASON 1: EOF DETECTION                                                  │
│   ═══════════════════════                                                  │
│                                                                            │
│   Remember: read() returns 0 (EOF) only when ALL write ends are closed!   │
│                                                                            │
│   If child doesn't close pipe1[1]:                                         │
│   ┌─────────────────────────────────────────────────────────────────┐     │
│   │  Child calls: read(pipe1[0], buf, size)                          │     │
│   │                                                                   │     │
│   │  Parent closes pipe1[1] and exits                                 │     │
│   │                                                                   │     │
│   │  Child's read() BLOCKS FOREVER!                                   │     │
│   │  Why? Because child still has pipe1[1] open!                      │     │
│   │  Kernel thinks: "There's still a writer, wait for data..."        │     │
│   │                                                                   │     │
│   │  The child is waiting for ITSELF to write! DEADLOCK!              │     │
│   └─────────────────────────────────────────────────────────────────┘     │
│                                                                            │
│   REASON 2: SIGPIPE / EPIPE DETECTION                                      │
│   ════════════════════════════════════                                     │
│                                                                            │
│   Remember: write() to a pipe with no readers generates SIGPIPE!          │
│                                                                            │
│   If parent doesn't close pipe2[1]:                                        │
│   ┌─────────────────────────────────────────────────────────────────┐     │
│   │  Child exits unexpectedly                                         │     │
│   │                                                                   │     │
│   │  Parent calls: write(pipe1[1], data, size)                        │     │
│   │                                                                   │     │
│   │  No SIGPIPE! Because parent still has pipe2[1] open!              │     │
│   │  Kernel thinks: "There's still a reader (parent itself)..."       │     │
│   │                                                                   │     │
│   │  Parent doesn't know child is dead!                               │     │
│   └─────────────────────────────────────────────────────────────────┘     │
│                                                                            │
│   REASON 3: RESOURCE MANAGEMENT                                            │
│   ═════════════════════════════                                            │
│                                                                            │
│   File descriptors are limited (typically 1024 per process).              │
│   Keeping unused fds wastes resources.                                    │
│                                                                            │
│   Also: The pipe buffer memory isn't freed until ALL references close!    │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```

#### The Pattern Summarized

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    THE STEVENS TWO-PIPE PATTERN                            │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   SETUP:                                                                   │
│   ──────                                                                   │
│   1. Create pipe1 (for requests:  parent → child)                          │
│   2. Create pipe2 (for responses: child → parent)                          │
│   3. Fork                                                                  │
│                                                                            │
│   IN CHILD:                                                                │
│   ─────────                                                                │
│   4. Close pipe1[1]  (child doesn't write requests)                        │
│   5. Close pipe2[0]  (child doesn't read responses)                        │
│   6. Use pipe1[0] to READ requests                                         │
│   7. Use pipe2[1] to WRITE responses                                       │
│                                                                            │
│   IN PARENT:                                                               │
│   ──────────                                                               │
│   8. Close pipe1[0]  (parent doesn't read requests)                        │
│   9. Close pipe2[1]  (parent doesn't write responses)                      │
│   10. Use pipe1[1] to WRITE requests                                       │
│   11. Use pipe2[0] to READ responses                                       │
│                                                                            │
│   MEMORY AID:                                                              │
│   ───────────                                                              │
│   • pipe1 = "parent TO child"   → parent keeps [1], child keeps [0]        │
│   • pipe2 = "child TO parent"   → child keeps [1], parent keeps [0]        │
│   • [0] is always READ, [1] is always WRITE                                │
│   • Close the ends you DON'T use!                                          │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```

### The Server Process Model

A pipe-based server must address several design considerations:

1. **How do clients find the server?** (Named pipe with known path)
2. **How are multiple clients handled?** (Fork per client or multiplexing)
3. **How are responses sent?** (Separate response channel or bidirectional protocol)

#### Server Architecture Patterns

```
┌───────────────────────────────────────────────────────────────────────────┐
│              CLIENT-SERVER PATTERNS WITH PIPES                             │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   PATTERN 1: Fork-per-Client Server                                        │
│   ══════════════════════════════════                                       │
│                                                                            │
│   ┌─────────┐                                                              │
│   │ Client1 │──────┐                                                       │
│   └─────────┘      │     ┌──────────────┐    ┌──────────────┐             │
│                    ├────>│ Server FIFO  │───>│ Server Main  │             │
│   ┌─────────┐      │     │  (well-known │    │   Process    │             │
│   │ Client2 │──────┤     │    path)     │    │  (listener)  │             │
│   └─────────┘      │     └──────────────┘    └──────┬───────┘             │
│                    │                                 │                     │
│   ┌─────────┐      │                          fork() │                     │
│   │ Client3 │──────┘                                 ▼                     │
│   └─────────┘                          ┌─────────────────────────┐        │
│                                        │  Child processes        │        │
│                                        │  (one per connection)   │        │
│                                        │  ┌───┐ ┌───┐ ┌───┐     │        │
│                                        │  │W1 │ │W2 │ │W3 │     │        │
│                                        │  └───┘ └───┘ └───┘     │        │
│                                        └─────────────────────────┘        │
│                                                                            │
│   PATTERN 2: Multiplexing Server (select/poll)                             │
│   ═════════════════════════════════════════════                            │
│                                                                            │
│   ┌─────────┐                                                              │
│   │ Client1 │─────FIFO1────┐                                               │
│   └─────────┘              │                                               │
│                            │    ┌────────────────────────────┐            │
│   ┌─────────┐              ├───>│  Single Server Process     │            │
│   │ Client2 │─────FIFO2────┤    │                            │            │
│   └─────────┘              │    │  select()/poll() on all    │            │
│                            │    │  file descriptors          │            │
│   ┌─────────┐              │    │                            │            │
│   │ Client3 │─────FIFO3────┘    │  Event-driven handling     │            │
│   └─────────┘                   └────────────────────────────┘            │
│                                                                            │
│   PATTERN 3: Bidirectional with Client FIFOs                               │
│   ═══════════════════════════════════════════                              │
│                                                                            │
│   ┌─────────┐    /tmp/server.fifo    ┌──────────┐                         │
│   │ Client  │────────────────────────>│  Server  │                         │
│   │  (PID   │<────────────────────────│          │                         │
│   │  1234)  │    /tmp/client.1234     └──────────┘                         │
│   └─────────┘                                                              │
│                                                                            │
│   Client creates /tmp/client.<PID> for responses                           │
│   Request includes client PID for server to find response FIFO            │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```

### Connection Establishment

In a pipe-based server, "connection establishment" differs from socket-based servers. There's no explicit accept() call; instead, the server reads requests and implicitly serves whoever wrote them.

#### Establishing a Bidirectional Channel

```
algorithm: establish_bidirectional_connection
client_side:
{
    /* Step 1: Create client-specific response FIFO */
    sprintf(client_fifo_path, "/tmp/client.%d", getpid());
    mkfifo(client_fifo_path, 0600);

    /* Step 2: Format request with return address */
    sprintf(request, "%d:%s", getpid(), command);

    /* Step 3: Open server FIFO and send request */
    server_fd = open("/tmp/server.fifo", O_WRONLY);
    write(server_fd, request, strlen(request));
    close(server_fd);

    /* Step 4: Open client FIFO to receive response */
    response_fd = open(client_fifo_path, O_RDONLY);
    read(response_fd, response, sizeof(response));
    close(response_fd);

    /* Step 5: Cleanup */
    unlink(client_fifo_path);
}

server_side:
{
    /* Step 1: Create well-known server FIFO */
    mkfifo("/tmp/server.fifo", 0666);

    for (;;) {
        /* Step 2: Open server FIFO (blocks until writer) */
        request_fd = open("/tmp/server.fifo", O_RDONLY);

        /* Step 3: Read request */
        n = read(request_fd, buffer, sizeof(buffer));
        close(request_fd);

        /* Step 4: Parse client PID from request */
        sscanf(buffer, "%d:%s", &client_pid, command);

        /* Step 5: Process request */
        result = process_command(command);

        /* Step 6: Open client FIFO and send response */
        sprintf(client_fifo_path, "/tmp/client.%d", client_pid);
        response_fd = open(client_fifo_path, O_WRONLY);
        write(response_fd, result, strlen(result));
        close(response_fd);
    }
}
```

### Request-Response Protocol

A robust protocol must handle message framing since pipes are byte streams, not message-oriented.

#### Message Framing Strategies

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    MESSAGE FRAMING STRATEGIES                              │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   STRATEGY 1: Delimiter-Based (e.g., newline)                              │
│   ─────────────────────────────────────────────                            │
│                                                                            │
│   │ G │ E │ T │   │ / │ f │ o │ o │ \n │ G │ E │ T │   │ / │ b │ a │ r │   │
│   └───┴───┴───┴───┴───┴───┴───┴───┴────┴───┴───┴───┴───┴───┴───┴───┴───┘   │
│   ├─────────── message 1 ───────────┤├────────── message 2 ──────────▶    │
│                                                                            │
│   Pros: Simple parsing, human-readable                                     │
│   Cons: Cannot include delimiter in payload, need escaping                 │
│                                                                            │
│                                                                            │
│   STRATEGY 2: Length-Prefixed                                              │
│   ───────────────────────────                                              │
│                                                                            │
│   │ 0x00 │ 0x08 │ G │ E │ T │   │ / │ f │ o │ o │ 0x00 │ 0x07 │ ...│       │
│   └──────┴──────┴───┴───┴───┴───┴───┴───┴───┴───┴──────┴──────┴────┘       │
│   ├─ length ──┤├────────── data ────────────────┤├─ next ─────────▶       │
│    (2 bytes)         (8 bytes)                      message                │
│                                                                            │
│   Pros: Binary-safe, efficient parsing, no escaping                        │
│   Cons: More complex, requires careful byte-order handling                 │
│                                                                            │
│                                                                            │
│   STRATEGY 3: Fixed-Size Records                                           │
│   ──────────────────────────────                                           │
│                                                                            │
│   │ CMD │ ARG1 │ ARG2 │ PAD │ CMD │ ARG1 │ ARG2 │ PAD │                    │
│   └─────┴──────┴──────┴─────┴─────┴──────┴──────┴─────┘                    │
│   ├────── 64 bytes ─────────┤├────── 64 bytes ─────────┤                   │
│                                                                            │
│   Pros: Simplest parsing, predictable memory usage                         │
│   Cons: Wastes space, limits message size                                  │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```

#### Protocol Structure Example

```c
/* Fixed-size request structure */
struct request {
    uint32_t    magic;          /* 0xDEADBEEF */
    uint32_t    version;        /* Protocol version */
    pid_t       client_pid;     /* For response routing */
    uint32_t    seq_num;        /* Sequence number */
    uint32_t    cmd;            /* Command code */
    uint32_t    payload_len;    /* Length of following data */
    /* Variable payload follows */
};

/* Fixed-size response structure */
struct response {
    uint32_t    magic;          /* 0xBEEFDEAD */
    uint32_t    version;
    uint32_t    seq_num;        /* Echoed from request */
    int32_t     status;         /* 0 = success, negative = error */
    uint32_t    payload_len;
    /* Variable payload follows */
};
```

### Multiplexing with select() and poll()

For handling multiple pipes (or any file descriptors) without creating multiple processes, Unix provides the `select()` and `poll()` system calls.

#### The select() System Call

```c
#include <sys/select.h>

int select(int nfds,
           fd_set *readfds,
           fd_set *writefds,
           fd_set *exceptfds,
           struct timeval *timeout);
```

#### select() Algorithm

```
algorithm: sys_select
input:     nfds      - highest fd + 1
           readfds   - fds to check for readability
           writefds  - fds to check for writability
           exceptfds - fds to check for exceptions
           timeout   - maximum wait time
output:    number of ready fds, 0 for timeout, -1 for error

{
    /* Step 1: Copy fd_sets from user space */
    copy_from_user(&in_readfds, readfds, ...);
    copy_from_user(&in_writefds, writefds, ...);
    copy_from_user(&in_exceptfds, exceptfds, ...);

    /* Step 2: Calculate deadline */
    if (timeout != NULL)
        deadline = current_time + timeout;
    else
        deadline = INFINITE;

    for (;;) {
        ready_count = 0;

        /* Step 3: Check each fd for readiness */
        for (fd = 0; fd < nfds; fd++) {
            file = current->files->fd[fd];

            if (FD_ISSET(fd, &in_readfds)) {
                /* Check if data available */
                if (file->f_op->poll(file, NULL) & POLLIN) {
                    FD_SET(fd, &out_readfds);
                    ready_count++;
                }
            }

            if (FD_ISSET(fd, &in_writefds)) {
                /* Check if space available for writing */
                if (file->f_op->poll(file, NULL) & POLLOUT) {
                    FD_SET(fd, &out_writefds);
                    ready_count++;
                }
            }

            /* Similar for exceptfds... */
        }

        /* Step 4: If any ready, return */
        if (ready_count > 0) {
            copy_to_user(readfds, &out_readfds, ...);
            copy_to_user(writefds, &out_writefds, ...);
            return ready_count;
        }

        /* Step 5: Check timeout */
        if (current_time >= deadline)
            return 0;

        /* Step 6: Sleep until event or timeout */
        schedule_timeout(deadline - current_time);

        /* Step 7: Check for signals */
        if (signal_pending(current))
            return -EINTR;
    }
}
```

#### poll() Alternative

```c
#include <poll.h>

struct pollfd {
    int   fd;         /* File descriptor */
    short events;     /* Requested events */
    short revents;    /* Returned events */
};

int poll(struct pollfd *fds, nfds_t nfds, int timeout);
```

`poll()` is generally preferred over `select()` because:

- No artificial FD_SETSIZE limit
- More efficient for sparse fd sets
- Cleaner interface

#### Multiplexing Server Pattern

```c
/* Server handling multiple client FIFOs with poll() */
void multiplex_server(void) {
    struct pollfd fds[MAX_CLIENTS + 1];
    int nfds = 1;

    /* fds[0] is always the server's incoming request FIFO */
    int server_fd = open("/tmp/server.fifo", O_RDONLY | O_NONBLOCK);
    fds[0].fd = server_fd;
    fds[0].events = POLLIN;

    for (;;) {
        int ready = poll(fds, nfds, -1);  /* Block indefinitely */

        if (ready < 0) {
            if (errno == EINTR)
                continue;
            perror("poll");
            exit(1);
        }

        /* Check each fd */
        for (int i = 0; i < nfds; i++) {
            if (fds[i].revents & POLLIN) {
                /* Data available on fds[i].fd */
                handle_input(fds[i].fd);
            }

            if (fds[i].revents & POLLHUP) {
                /* Other end closed */
                close(fds[i].fd);
                /* Remove from array (shift others down) */
                memmove(&fds[i], &fds[i+1], (nfds-i-1) * sizeof(fds[0]));
                nfds--;
                i--;
            }
        }
    }
}
```

---

## 6. The Close System Call

The `close()` system call is deceptively simple in its interface but involves complex interactions between multiple kernel data structures. Understanding `close()` is essential for understanding resource management in Unix.

### Close System Call Implementation

```c
#include <unistd.h>

int close(int fd);
```

The function appears trivial, but the kernel performs numerous operations to properly release resources.

### The close() Algorithm

```
algorithm: sys_close
input:     fd - file descriptor to close
output:    0 on success, -1 on error (errno set)

{
    /* Step 1: Validate file descriptor */
    files = current->files;

    spin_lock(&files->file_lock);

    if (fd < 0 || fd >= files->max_fds) {
        spin_unlock(&files->file_lock);
        return -EBADF;    /* Bad file descriptor */
    }

    file = files->fd[fd];
    if (file == NULL) {
        spin_unlock(&files->file_lock);
        return -EBADF;
    }

    /* Step 2: Remove file descriptor from per-process table */
    files->fd[fd] = NULL;
    FD_CLR(fd, files->close_on_exec);
    FD_CLR(fd, files->open_fds);

    spin_unlock(&files->file_lock);

    /* Step 3: Decrement file table entry reference count */
    /* This is where most of the work happens */
    return filp_close(file, files);
}

algorithm: filp_close
input:     file  - pointer to file table entry
           files - per-process file table (for owner checking)
output:    0 on success, error code otherwise

{
    /* Step 1: Call file-type-specific flush */
    if (file->f_op->flush) {
        error = file->f_op->flush(file, files);
        /* Note: flush errors are returned but don't prevent close */
    }

    /* Step 2: Remove POSIX locks owned by this files_struct */
    if (file->f_mode & FMODE_WRITE) {
        locks_remove_posix(file, files);
    }

    /* Step 3: Decrement reference count */
    fput(file);

    return error;
}

algorithm: fput
input:     file - pointer to file table entry
output:    none

{
    /* Step 1: Atomically decrement reference count */
    if (atomic_long_dec_and_test(&file->f_count)) {
        /* Reference count reached zero - this is the last close */

        /* Step 2: Schedule actual release (may sleep) */
        /* Using delayed work to avoid holding locks */
        call_rcu(&file->f_u.fu_rcuhead, delayed_fput);
    }
}

algorithm: __fput (delayed execution)
input:     file - pointer to file table entry
output:    none

{
    inode = file->f_inode;

    /* Step 1: Remove file from inode's file list */
    /* (Used for lease/lock tracking) */

    /* Step 2: Disable async notifications */
    if (file->f_op->fasync) {
        file->f_op->fasync(-1, file, 0);
    }

    /* Step 3: Remove all file locks */
    locks_remove_file(file);

    /* Step 4: Security module cleanup */
    security_file_free(file);

    /* Step 5: Call file-type-specific release */
    if (file->f_op->release) {
        file->f_op->release(inode, file);
    }

    /* Step 6: Release path reference */
    path_put(&file->f_path);

    /* Step 7: Decrement inode reference count */
    iput(inode);

    /* Step 8: Free the file structure */
    put_empty_filp(file);
}
```

### Reference Count Decrement

The core of close() is the reference counting logic. Let's trace what happens in various scenarios:

```
┌───────────────────────────────────────────────────────────────────────────┐
│                 REFERENCE COUNTING SCENARIOS IN CLOSE()                    │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   SCENARIO 1: Simple close (one fd, one process)                           │
│   ══════════════════════════════════════════════                           │
│                                                                            │
│   Before close():                      After close():                      │
│                                                                            │
│   Process P                            Process P                           │
│   ┌──────────────┐                     ┌──────────────┐                   │
│   │ fd[3] ───────┼──┐                  │ fd[3] = NULL │                   │
│   └──────────────┘  │                  └──────────────┘                   │
│                     │                                                      │
│                     ▼                                                      │
│   ┌──────────────────────┐             ┌──────────────────────┐           │
│   │ File Entry           │             │ (freed)              │           │
│   │ f_count: 1 ──────────┼─▶ FREED     │                      │           │
│   │ f_inode: ───────────▶│             │                      │           │
│   └──────────────────────┘             └──────────────────────┘           │
│                     │                                                      │
│                     ▼                                                      │
│   ┌──────────────────────┐             ┌──────────────────────┐           │
│   │ Inode                │             │ (freed if i_nlink=0) │           │
│   │ i_count: 1 ─ ─ ─ ─ ─▶│             │                      │           │
│   └──────────────────────┘             └──────────────────────┘           │
│                                                                            │
│                                                                            │
│   SCENARIO 2: After dup() (two fds, same file entry)                       │
│   ══════════════════════════════════════════════════                       │
│                                                                            │
│   Before close(3):                     After close(3):                     │
│                                                                            │
│   Process P                            Process P                           │
│   ┌──────────────┐                     ┌──────────────┐                   │
│   │ fd[3] ───────┼──┐                  │ fd[3] = NULL │                   │
│   │ fd[4] ───────┼──┤                  │ fd[4] ────────┼──┐               │
│   └──────────────┘  │                  └──────────────┘  │               │
│                     │                                    │               │
│                     ▼                                    ▼               │
│   ┌──────────────────────┐             ┌──────────────────────┐          │
│   │ File Entry           │             │ File Entry           │          │
│   │ f_count: 2           │             │ f_count: 1           │          │
│   │ (NOT freed)          │             │ (still valid)        │          │
│   └──────────────────────┘             └──────────────────────┘          │
│                                                                            │
│                                                                            │
│   SCENARIO 3: After fork() (two processes, two fds, same file entry)      │
│   ═══════════════════════════════════════════════════════════════════      │
│                                                                            │
│   Before child close(3):               After child close(3):               │
│                                                                            │
│   Parent P         Child C             Parent P         Child C            │
│   ┌─────────┐     ┌─────────┐         ┌─────────┐     ┌─────────┐         │
│   │ fd[3]───┼─┐ ┌─┼───fd[3] │         │ fd[3]───┼──┐  │fd[3]=NULL│         │
│   └─────────┘ │ │ └─────────┘         └─────────┘  │  └─────────┘         │
│               │ │                                  │                       │
│               ▼ ▼                                  ▼                       │
│   ┌──────────────────────┐             ┌──────────────────────┐           │
│   │ File Entry           │             │ File Entry           │           │
│   │ f_count: 2           │             │ f_count: 1           │           │
│   │ (NOT freed)          │             │ (still valid)        │           │
│   └──────────────────────┘             └──────────────────────┘           │
│                                                                            │
│   Note: Parent still has valid fd[3] pointing to the file entry           │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```

### Resource Cleanup

When `f_count` reaches zero, the kernel performs extensive cleanup:

#### File-Type-Specific Cleanup

Each file type has a `release` function:

```c
const struct file_operations pipe_fops = {
    .open       = pipe_open,
    .release    = pipe_release,    /* Called on last close */
    .read       = pipe_read,
    .write      = pipe_write,
    .poll       = pipe_poll,
    /* ... */
};
```

#### The pipe_release() Function

```
algorithm: pipe_release
input:     inode - pipe inode
           file  - file table entry being closed
output:    0

{
    pipe = inode->i_pipe;

    mutex_lock(&pipe->mutex);

    /* Determine which end is being closed */
    if (file->f_mode & FMODE_READ) {
        /* Closing read end */
        pipe->readers--;

        if (pipe->readers == 0) {
            /* No more readers - wake any blocked writers */
            wake_up_interruptible(&pipe->wr_wait);

            /* Mark for SIGPIPE generation on subsequent writes */
        }
    }

    if (file->f_mode & FMODE_WRITE) {
        /* Closing write end */
        pipe->writers--;

        if (pipe->writers == 0) {
            /* No more writers - wake any blocked readers */
            wake_up_interruptible(&pipe->rd_wait);

            /* Readers will now see EOF */
        }
    }

    pipe->files--;

    /* Check if pipe should be destroyed */
    if (pipe->files == 0) {
        /* Last reference - free pipe buffer */
        mutex_unlock(&pipe->mutex);
        free_pipe_info(pipe);
        return 0;
    }

    mutex_unlock(&pipe->mutex);
    return 0;
}
```

### Close and Pipes

Closing a pipe end has specific effects depending on which end is closed:

#### Closing the Read End

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    CLOSING THE READ END OF A PIPE                          │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   Before: Reader and Writer both active                                    │
│                                                                            │
│   ┌──────────┐           ┌────────────────┐           ┌──────────┐        │
│   │  Writer  │──write()─>│  Pipe Buffer   │──read()──>│  Reader  │        │
│   └──────────┘           │  [  data...  ] │           └──────────┘        │
│                          └────────────────┘                                │
│                                                                            │
│   After: Reader closes its end                                             │
│                                                                            │
│   ┌──────────┐           ┌────────────────┐           ┌──────────┐        │
│   │  Writer  │──write()─>│  Pipe Buffer   │     X     │ (closed) │        │
│   │          │           │  pipe->readers │           └──────────┘        │
│   │          │           │      = 0       │                                │
│   └──────────┘           └────────────────┘                                │
│        │                                                                   │
│        │  Next write() call:                                               │
│        │                                                                   │
│        ├─▶ 1. Kernel checks: pipe->readers == 0?  YES                     │
│        │                                                                   │
│        ├─▶ 2. Kernel sends SIGPIPE to writer process                      │
│        │      • Default action: terminate process                          │
│        │      • Can be caught or ignored                                   │
│        │                                                                   │
│        └─▶ 3. write() returns -1 with errno = EPIPE                       │
│                                                                            │
│   This is the "broken pipe" error                                          │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```

#### Closing the Write End

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    CLOSING THE WRITE END OF A PIPE                         │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   Before: Writer writes data, Reader reads                                 │
│                                                                            │
│   ┌──────────┐           ┌────────────────┐           ┌──────────┐        │
│   │  Writer  │──write()─>│  Pipe Buffer   │──read()──>│  Reader  │        │
│   └──────────┘           │  [  data...  ] │           └──────────┘        │
│                          └────────────────┘                                │
│                                                                            │
│   After: Writer closes its end                                             │
│                                                                            │
│   ┌──────────┐           ┌────────────────┐           ┌──────────┐        │
│   │ (closed) │     X     │  Pipe Buffer   │──read()──>│  Reader  │        │
│   └──────────┘           │  [remaining]   │           │          │        │
│                          │  pipe->writers │           └──────────┘        │
│                          │      = 0       │                │               │
│                          └────────────────┘                │               │
│                                                            │               │
│   Reader's next read() calls:                              │               │
│                                                            │               │
│   1. If data remains in buffer:                            │               │
│      └─▶ read() returns data normally                      │               │
│                                                            │               │
│   2. When buffer becomes empty:                            │               │
│      └─▶ read() returns 0 (EOF)                            │               │
│          • This is how reader knows writer is done         │               │
│          • No signal sent (unlike write to broken pipe)    │               │
│          • Reader should close its end and exit loop       │               │
│                                                                            │
│   This is the standard "end of file" condition for pipes                   │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```

### Close and Sockets

While this document focuses on pipes, understanding how `close()` differs for sockets is instructive:

#### Socket Close vs Shutdown

```c
close(sockfd);                 /* Release fd AND possibly close connection */
shutdown(sockfd, SHUT_RD);     /* Half-close: disable reading */
shutdown(sockfd, SHUT_WR);     /* Half-close: disable writing (send FIN) */
shutdown(sockfd, SHUT_RDWR);   /* Full close but fd still valid */
```

#### Differences

| Aspect            | Pipe close()                         | Socket close()            |
| ----------------- | ------------------------------------ | ------------------------- |
| Effect on fd      | Fd becomes invalid                   | Fd becomes invalid        |
| Peer notification | Writers get SIGPIPE, readers get EOF | TCP FIN sent to peer      |
| Data in buffer    | Discarded                            | Kernel tries to deliver   |
| Half-close        | Not possible (pipes unidirectional)  | Via shutdown()            |
| TIME_WAIT         | Not applicable                       | Socket may linger         |
| SO_LINGER         | Not applicable                       | Can affect close behavior |

---

## 7. Advanced Topics

This section explores advanced aspects of pipe behavior that are crucial for building robust systems.

### Pipe Atomicity and PIPE_BUF

One of the most important guarantees Unix provides for pipes is **atomic writes** up to a certain size.

#### The PIPE_BUF Constant

```c
#include <limits.h>

/* POSIX minimum: 512 bytes, typical Linux: 4096 bytes */
#ifndef PIPE_BUF
#define PIPE_BUF 4096  /* On most systems */
#endif
```

#### Atomicity Guarantees

```
┌───────────────────────────────────────────────────────────────────────────┐
│                        PIPE ATOMICITY GUARANTEES                           │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   RULE 1: Writes ≤ PIPE_BUF are ATOMIC                                    │
│   ═══════════════════════════════════════                                  │
│                                                                            │
│   Writer A: write(fd, "AAAA", 4)     Writer B: write(fd, "BBBB", 4)       │
│                    │                              │                        │
│                    └──────────────┬───────────────┘                        │
│                                   ▼                                        │
│                    ┌──────────────────────────────┐                        │
│                    │ Pipe Buffer                  │                        │
│                    │                              │                        │
│                    │ Either: │A│A│A│A│B│B│B│B│    │                        │
│                    │     or: │B│B│B│B│A│A│A│A│    │                        │
│                    │                              │                        │
│                    │ NEVER:  │A│A│B│B│A│A│B│B│    │  ✗ Interleaving       │
│                    │                              │                        │
│                    └──────────────────────────────┘                        │
│                                                                            │
│   The entire 4-byte message is written as one unit                        │
│                                                                            │
│                                                                            │
│   RULE 2: Writes > PIPE_BUF may be INTERLEAVED                            │
│   ════════════════════════════════════════════════                         │
│                                                                            │
│   Writer A: write(fd, big_buffer_A, 8192)                                 │
│   Writer B: write(fd, big_buffer_B, 8192)                                 │
│                                                                            │
│   Possible result in pipe:                                                 │
│   │A₁│A₂│B₁│A₃│B₂│B₃│A₄│...│                                              │
│                                                                            │
│   Chunks from A and B may interleave                                      │
│                                                                            │
│                                                                            │
│   RULE 3: Blocking behavior                                                │
│   ════════════════════════════                                             │
│                                                                            │
│   For write size n:                                                        │
│                                                                            │
│   If n ≤ PIPE_BUF:                                                        │
│     • Blocking: write blocks until n bytes of space available             │
│     • Non-blocking: returns EAGAIN if < n bytes available                 │
│                                                                            │
│   If n > PIPE_BUF:                                                        │
│     • Blocking: may write partial chunks, blocks between chunks           │
│     • Non-blocking: writes as much as possible, may return < n            │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```

#### Kernel Implementation of Atomicity

```
algorithm: pipe_write_atomic
input:     pipe   - pipe_inode_info structure
           buffer - user data to write
           len    - length of write
output:    bytes written, or -1 on error

{
    if (len <= PIPE_BUF) {
        /* ATOMIC write path */

        mutex_lock(&pipe->mutex);

        /* Must wait for enough space for entire write */
        while (pipe_space(pipe) < len) {
            if (O_NONBLOCK) {
                mutex_unlock(&pipe->mutex);
                return -EAGAIN;
            }

            /* Sleep until space available */
            mutex_unlock(&pipe->mutex);
            wait_event_interruptible(pipe->wr_wait,
                                     pipe_space(pipe) >= len);
            mutex_lock(&pipe->mutex);

            /* Check if pipe still valid after waking */
            if (pipe->readers == 0) {
                mutex_unlock(&pipe->mutex);
                send_sig(SIGPIPE, current, 0);
                return -EPIPE;
            }
        }

        /* Copy entire buffer atomically (while holding mutex) */
        copy_from_user_to_pipe(pipe, buffer, len);

        mutex_unlock(&pipe->mutex);
        wake_up_interruptible(&pipe->rd_wait);

        return len;
    }
    else {
        /* NON-ATOMIC write path */

        total_written = 0;

        while (total_written < len) {
            mutex_lock(&pipe->mutex);

            /* Write as much as possible */
            chunk = min(len - total_written, pipe_space(pipe));

            if (chunk > 0) {
                copy_from_user_to_pipe(pipe, buffer + total_written, chunk);
                total_written += chunk;
            }

            mutex_unlock(&pipe->mutex);
            wake_up_interruptible(&pipe->rd_wait);

            if (total_written < len) {
                if (O_NONBLOCK)
                    return total_written > 0 ? total_written : -EAGAIN;

                /* Wait for more space */
                wait_event_interruptible(pipe->wr_wait,
                                         pipe_space(pipe) > 0);
            }
        }

        return total_written;
    }
}
```

#### Practical Implications

```c
/* Safe: atomic write, messages won't interleave */
struct message {
    uint32_t type;
    uint32_t len;
    char data[PIPE_BUF - 8];  /* Keep total ≤ PIPE_BUF */
};

void send_message(int fd, struct message *msg) {
    ssize_t n = write(fd, msg, sizeof(*msg));
    /* Either entire message written, or error */
}

/* Unsafe: large writes may interleave */
void send_large_data(int fd, char *data, size_t len) {
    /* If multiple writers, data may interleave! */
    write(fd, data, len);  /* len > PIPE_BUF */
}

/* Safe alternative for large data: use locking */
pthread_mutex_t pipe_mutex = PTHREAD_MUTEX_INITIALIZER;

void send_large_data_safe(int fd, char *data, size_t len) {
    pthread_mutex_lock(&pipe_mutex);
    write(fd, data, len);
    pthread_mutex_unlock(&pipe_mutex);
}
```

### The SIGPIPE Signal

SIGPIPE is one of the most important signals in Unix IPC, yet is often mishandled.

#### When SIGPIPE is Generated

```
┌───────────────────────────────────────────────────────────────────────────┐
│                        SIGPIPE SIGNAL GENERATION                           │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   Condition: write() to a pipe/FIFO with no readers                       │
│                                                                            │
│                                                                            │
│   Step 1: Process calls write()                                           │
│   ──────────────────────────────                                           │
│                                                                            │
│   Process ───write(pipefd[1], data, len)──▶  Kernel                       │
│                                                                            │
│                                                                            │
│   Step 2: Kernel checks pipe state                                        │
│   ─────────────────────────────────                                        │
│                                                                            │
│   Kernel:                                                                  │
│     pipe = inode->i_pipe;                                                 │
│     if (pipe->readers == 0) {                                             │
│         /* No process has read end open */                                │
│         goto broken_pipe;                                                 │
│     }                                                                      │
│                                                                            │
│                                                                            │
│   Step 3: Signal and error                                                │
│   ─────────────────────────                                                │
│                                                                            │
│   broken_pipe:                                                             │
│     send_sig(SIGPIPE, current, 0);   /* Send signal */                    │
│     return -EPIPE;                    /* Return error */                  │
│                                                                            │
│                                                                            │
│   Step 4: Process receives signal                                         │
│   ──────────────────────────────                                           │
│                                                                            │
│   ┌─────────────────────────────────────────────────────────┐             │
│   │                                                          │             │
│   │   Default action: TERMINATE PROCESS                     │             │
│   │                                                          │             │
│   │   The shell command:                                     │             │
│   │     $ yes | head -1                                      │             │
│   │                                                          │             │
│   │   yes is terminated by SIGPIPE when head closes pipe     │             │
│   │                                                          │             │
│   └─────────────────────────────────────────────────────────┘             │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```

#### Handling SIGPIPE

```c
/* Method 1: Ignore SIGPIPE globally */
signal(SIGPIPE, SIG_IGN);

/* Method 2: Use sigaction for more control */
struct sigaction sa;
sa.sa_handler = SIG_IGN;
sigemptyset(&sa.sa_mask);
sa.sa_flags = 0;
sigaction(SIGPIPE, &sa, NULL);

/* Method 3: Block SIGPIPE for specific threads */
sigset_t set;
sigemptyset(&set);
sigaddset(&set, SIGPIPE);
pthread_sigmask(SIG_BLOCK, &set, NULL);

/* Method 4: Custom signal handler */
void sigpipe_handler(int sig) {
    /* Log the event, set a flag, etc. */
    fprintf(stderr, "SIGPIPE received\n");
    /* Don't exit - handle gracefully */
}
signal(SIGPIPE, sigpipe_handler);
```

#### SIGPIPE Best Practices

```
┌───────────────────────────────────────────────────────────────────────────┐
│                        SIGPIPE HANDLING STRATEGIES                         │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   STRATEGY 1: Ignore and check EPIPE                                       │
│   ═══════════════════════════════════                                      │
│                                                                            │
│   signal(SIGPIPE, SIG_IGN);                                               │
│                                                                            │
│   ssize_t n = write(fd, data, len);                                       │
│   if (n == -1) {                                                          │
│       if (errno == EPIPE) {                                               │
│           /* Reader closed - clean up */                                  │
│           close(fd);                                                      │
│           return PEER_DISCONNECTED;                                       │
│       }                                                                   │
│       /* Handle other errors */                                           │
│   }                                                                       │
│                                                                            │
│   Pros: Simple, explicit error handling                                   │
│   Cons: Global effect, may affect libraries                               │
│                                                                            │
│                                                                            │
│   STRATEGY 2: Per-call suppression (Linux)                                │
│   ═════════════════════════════════════════                                │
│                                                                            │
│   /* MSG_NOSIGNAL flag for send() on sockets */                           │
│   send(sockfd, data, len, MSG_NOSIGNAL);                                  │
│                                                                            │
│   Note: Not available for pipe write()                                    │
│                                                                            │
│                                                                            │
│   STRATEGY 3: Thread-local blocking                                        │
│   ═══════════════════════════════════                                      │
│                                                                            │
│   /* Block SIGPIPE only in I/O threads */                                 │
│   void* io_thread(void* arg) {                                            │
│       sigset_t mask;                                                      │
│       sigemptyset(&mask);                                                 │
│       sigaddset(&mask, SIGPIPE);                                          │
│       pthread_sigmask(SIG_BLOCK, &mask, NULL);                            │
│                                                                            │
│       /* Now write() returns EPIPE without signal */                      │
│       ...                                                                 │
│   }                                                                       │
│                                                                            │
│   Pros: Doesn't affect other threads                                      │
│   Cons: More complex, must do per-thread                                  │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```

### Pipe Capacity and Tuning

Modern Linux allows dynamic adjustment of pipe capacity.

#### Default Pipe Capacity

```c
/* Default capacity: 16 pages = 65536 bytes (on 4KB page systems) */
#define PIPE_DEF_BUFFERS 16

/* Check current pipe capacity */
int capacity = fcntl(pipefd[0], F_GETPIPE_SZ);
printf("Pipe capacity: %d bytes\n", capacity);
```

#### Adjusting Pipe Capacity

```c
#define _GNU_SOURCE
#include <fcntl.h>

int pipefd[2];
pipe(pipefd);

/* Increase pipe capacity */
int new_size = 1024 * 1024;  /* 1 MB */
int result = fcntl(pipefd[0], F_SETPIPE_SZ, new_size);
if (result == -1) {
    if (errno == EPERM) {
        /* Exceeds /proc/sys/fs/pipe-max-size and not privileged */
    }
}

/* Actual size may be larger (rounded to power of 2) */
int actual = fcntl(pipefd[0], F_GETPIPE_SZ);
printf("Actual capacity: %d bytes\n", actual);
```

#### System-Wide Pipe Limits

```
┌───────────────────────────────────────────────────────────────────────────┐
│                        PIPE CAPACITY SYSTEM LIMITS                         │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   /proc/sys/fs/pipe-max-size                                              │
│   ═══════════════════════════                                              │
│   Maximum size unprivileged users can set                                 │
│   Default: 1048576 (1 MB)                                                 │
│                                                                            │
│   # View                                                                  │
│   cat /proc/sys/fs/pipe-max-size                                          │
│                                                                            │
│   # Increase (as root)                                                    │
│   echo 16777216 > /proc/sys/fs/pipe-max-size  # 16 MB                     │
│                                                                            │
│                                                                            │
│   /proc/sys/fs/pipe-user-pages-hard                                       │
│   ════════════════════════════════                                         │
│   Hard limit on total pages a user can allocate to pipes                  │
│   0 = no limit (default)                                                  │
│                                                                            │
│                                                                            │
│   /proc/sys/fs/pipe-user-pages-soft                                       │
│   ════════════════════════════════                                         │
│   Soft limit - after this, only default-sized pipes allowed              │
│   Default: 16384 pages = 64 MB                                            │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```

### Zero-Copy I/O: splice(), vmsplice(), and tee()

Linux provides system calls for moving data without copying through userspace.

#### The splice() System Call

```c
#define _GNU_SOURCE
#include <fcntl.h>

ssize_t splice(int fd_in, loff_t *off_in,
               int fd_out, loff_t *off_out,
               size_t len, unsigned int flags);
```

`splice()` moves data between a pipe and another file descriptor (file, socket, another pipe) without copying through userspace.

```
┌───────────────────────────────────────────────────────────────────────────┐
│                        SPLICE ZERO-COPY TRANSFER                           │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   TRADITIONAL COPY (with userspace buffer):                                │
│   ══════════════════════════════════════════                               │
│                                                                            │
│   File ──read()──▶ [Kernel Buffer] ──copy──▶ [User Buffer]                │
│                                                                            │
│   [User Buffer] ──copy──▶ [Kernel Buffer] ──write()──▶ Socket             │
│                                                                            │
│   4 copies: file→kernel, kernel→user, user→kernel, kernel→socket         │
│                                                                            │
│                                                                            │
│   WITH SPLICE (zero-copy via pipe):                                        │
│   ════════════════════════════════                                         │
│                                                                            │
│   Step 1: splice from file to pipe (zero-copy, just page references)     │
│   ┌──────┐                    ┌──────────────┐                            │
│   │ File │───splice()────────▶│     Pipe     │                            │
│   └──────┘                    │  [page refs] │                            │
│                               └──────────────┘                            │
│                                                                            │
│   Step 2: splice from pipe to socket (zero-copy)                          │
│   ┌──────────────┐                    ┌────────┐                          │
│   │     Pipe     │───splice()────────▶│ Socket │                          │
│   │  [page refs] │                    └────────┘                          │
│   └──────────────┘                                                        │
│                                                                            │
│   0 copies through userspace! Pages are shared, not copied.               │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```

#### splice() Example: File to Socket Transfer

```c
#define _GNU_SOURCE
#include <fcntl.h>
#include <unistd.h>
#include <sys/socket.h>

/* Zero-copy file transfer to socket */
ssize_t sendfile_via_splice(int sockfd, int filefd, size_t count) {
    int pipefd[2];
    ssize_t total = 0;

    if (pipe(pipefd) == -1)
        return -1;

    while (count > 0) {
        ssize_t n;

        /* Splice from file to pipe */
        n = splice(filefd, NULL, pipefd[1], NULL,
                   count, SPLICE_F_MOVE | SPLICE_F_MORE);
        if (n <= 0) {
            if (n == 0) break;  /* EOF */
            goto error;
        }

        /* Splice from pipe to socket */
        ssize_t sent = 0;
        while (sent < n) {
            ssize_t s = splice(pipefd[0], NULL, sockfd, NULL,
                               n - sent, SPLICE_F_MOVE | SPLICE_F_MORE);
            if (s <= 0) goto error;
            sent += s;
        }

        total += n;
        count -= n;
    }

    close(pipefd[0]);
    close(pipefd[1]);
    return total;

error:
    close(pipefd[0]);
    close(pipefd[1]);
    return -1;
}
```

#### The vmsplice() System Call

`vmsplice()` transfers user memory into a pipe (or from a pipe to user memory) without copying.

```c
#define _GNU_SOURCE
#include <fcntl.h>
#include <sys/uio.h>

ssize_t vmsplice(int fd, const struct iovec *iov,
                 unsigned long nr_segs, unsigned int flags);
```

```c
/* Example: Efficiently write user buffer to pipe */
char user_buffer[65536];
/* ... fill buffer ... */

struct iovec iov = {
    .iov_base = user_buffer,
    .iov_len = sizeof(user_buffer)
};

/* Pages are "gifted" to pipe - don't modify user_buffer until consumed! */
ssize_t n = vmsplice(pipefd[1], &iov, 1, SPLICE_F_GIFT);
```

#### The tee() System Call

`tee()` duplicates data between two pipes without consuming it.

```c
#define _GNU_SOURCE
#include <fcntl.h>

ssize_t tee(int fd_in, int fd_out, size_t len, unsigned int flags);
```

```
┌───────────────────────────────────────────────────────────────────────────┐
│                          TEE OPERATION                                     │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│                        ┌─────────────┐                                    │
│                   ┌───▶│   Pipe B    │───▶ Consumer B                     │
│                   │    │  (copy)     │                                    │
│   ┌─────────────┐ │    └─────────────┘                                    │
│   │   Pipe A    │─┤                                                       │
│   │ (original)  │ │    tee(A, B, len, flags)                              │
│   └─────────────┘ │                                                       │
│        │          └───▶ Data remains in Pipe A                            │
│        │                for original consumer                              │
│        ▼                                                                   │
│   Consumer A                                                               │
│                                                                            │
│   Use case: "T" in a pipeline (like Unix tee command)                     │
│                                                                            │
│   $ producer | tee /dev/stderr | consumer                                 │
│                                                                            │
│   Implementation: tee() + splice() from each pipe                         │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```

### Pipe Internals: The Kernel Data Path

Understanding the kernel's data path helps diagnose performance issues.

#### Pipe Buffer Pages

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    PIPE BUFFER INTERNAL STRUCTURE                          │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   struct pipe_inode_info {                                                │
│       unsigned int head;        /* Index of first filled buffer */       │
│       unsigned int tail;        /* Index of last filled buffer */        │
│       unsigned int ring_size;   /* Number of buffers (power of 2) */     │
│       struct pipe_buffer *bufs; /* Array of buffer descriptors */        │
│       ...                                                                 │
│   };                                                                      │
│                                                                            │
│   struct pipe_buffer {                                                    │
│       struct page *page;        /* Physical page */                       │
│       unsigned int offset;      /* Start of data in page */              │
│       unsigned int len;         /* Length of data */                     │
│       const struct pipe_buf_operations *ops;                              │
│       unsigned int flags;                                                 │
│       unsigned long private;                                              │
│   };                                                                      │
│                                                                            │
│                                                                            │
│   Ring Buffer Layout (default 16 buffers):                                │
│   ═══════════════════════════════════════                                  │
│                                                                            │
│   bufs[]:  [0][1][2][3][4][5][6][7][8][9][10][11][12][13][14][15]         │
│               ▲              ▲                                            │
│               │              │                                            │
│             tail           head                                            │
│           (consumer)     (producer)                                        │
│                                                                            │
│   Each buffer points to a 4KB page:                                       │
│                                                                            │
│   bufs[1]: page=0xffff8800123   offset=0    len=4096  (full page)        │
│   bufs[2]: page=0xffff8800456   offset=0    len=2048  (partial)          │
│   bufs[3]: page=0xffff8800789   offset=512  len=1024  (mid-page)         │
│   bufs[4]: (empty - not yet allocated)                                   │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```

---

## 8. Practical Implementation

This section provides complete, production-ready code examples that synthesize the concepts discussed throughout this document.

### A Complete Client-Server Example

The following example implements a simple key-value store server using named pipes, demonstrating proper error handling, signal management, and protocol design.

#### Server Implementation

```c
/*
 * kvserver.c - A simple key-value server using FIFOs
 *
 * Build: gcc -o kvserver kvserver.c -Wall -Wextra
 * Usage: ./kvserver
 *
 * Protocol:
 *   Request:  "client_pid:command:key[:value]\n"
 *   Response: "status:message\n"
 */

#define _GNU_SOURCE
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <fcntl.h>
#include <sys/stat.h>
#include <signal.h>
#include <errno.h>

#define SERVER_FIFO "/tmp/kvserver.fifo"
#define MAX_CLIENTS 100
#define MAX_MSG_LEN 4096
#define MAX_KEY_LEN 256
#define MAX_VAL_LEN 2048
#define MAX_ENTRIES 1000

/* Key-value store (simple array for demonstration) */
struct kv_entry {
    char key[MAX_KEY_LEN];
    char value[MAX_VAL_LEN];
    int in_use;
};

static struct kv_entry store[MAX_ENTRIES];
static volatile sig_atomic_t running = 1;

/* Signal handler for graceful shutdown */
void handle_signal(int sig) {
    (void)sig;
    running = 0;
}

/* Find entry by key */
struct kv_entry *find_entry(const char *key) {
    for (int i = 0; i < MAX_ENTRIES; i++) {
        if (store[i].in_use && strcmp(store[i].key, key) == 0)
            return &store[i];
    }
    return NULL;
}

/* Find free entry */
struct kv_entry *find_free_entry(void) {
    for (int i = 0; i < MAX_ENTRIES; i++) {
        if (!store[i].in_use)
            return &store[i];
    }
    return NULL;
}

/* Send response to client */
void send_response(pid_t client_pid, int status, const char *message) {
    char client_fifo[64];
    char response[MAX_MSG_LEN];
    int fd;

    snprintf(client_fifo, sizeof(client_fifo), "/tmp/kvclient.%d", client_pid);
    snprintf(response, sizeof(response), "%d:%s\n", status, message);

    /* Open client FIFO (non-blocking to avoid deadlock) */
    fd = open(client_fifo, O_WRONLY | O_NONBLOCK);
    if (fd == -1) {
        if (errno != ENXIO)  /* ENXIO = no reader */
            perror("open client fifo");
        return;
    }

    /* Write response (atomic if < PIPE_BUF) */
    if (write(fd, response, strlen(response)) == -1)
        perror("write response");

    close(fd);
}

/* Process a single request */
void process_request(const char *request) {
    pid_t client_pid;
    char command[16], key[MAX_KEY_LEN], value[MAX_VAL_LEN];
    struct kv_entry *entry;

    /* Parse request: "pid:command:key[:value]" */
    int n = sscanf(request, "%d:%15[^:]:%255[^:]:%2047[^\n]",
                   &client_pid, command, key, value);

    if (n < 3) {
        if (n >= 1)
            send_response(client_pid, -1, "invalid request format");
        return;
    }

    /* Handle GET command */
    if (strcmp(command, "GET") == 0) {
        entry = find_entry(key);
        if (entry)
            send_response(client_pid, 0, entry->value);
        else
            send_response(client_pid, -1, "key not found");
    }
    /* Handle SET command */
    else if (strcmp(command, "SET") == 0) {
        if (n < 4) {
            send_response(client_pid, -1, "SET requires value");
            return;
        }
        entry = find_entry(key);
        if (!entry) {
            entry = find_free_entry();
            if (!entry) {
                send_response(client_pid, -1, "store full");
                return;
            }
            strncpy(entry->key, key, MAX_KEY_LEN - 1);
            entry->in_use = 1;
        }
        strncpy(entry->value, value, MAX_VAL_LEN - 1);
        send_response(client_pid, 0, "OK");
    }
    /* Handle DEL command */
    else if (strcmp(command, "DEL") == 0) {
        entry = find_entry(key);
        if (entry) {
            entry->in_use = 0;
            send_response(client_pid, 0, "OK");
        } else {
            send_response(client_pid, -1, "key not found");
        }
    }
    else {
        send_response(client_pid, -1, "unknown command");
    }
}

int main(void) {
    int server_fd;
    char buffer[MAX_MSG_LEN];
    ssize_t n;

    /* Set up signal handlers */
    struct sigaction sa = {
        .sa_handler = handle_signal,
        .sa_flags = 0
    };
    sigemptyset(&sa.sa_mask);
    sigaction(SIGINT, &sa, NULL);
    sigaction(SIGTERM, &sa, NULL);
    signal(SIGPIPE, SIG_IGN);  /* Ignore SIGPIPE */

    /* Remove old FIFO if exists */
    unlink(SERVER_FIFO);

    /* Create server FIFO */
    if (mkfifo(SERVER_FIFO, 0666) == -1) {
        perror("mkfifo");
        exit(1);
    }

    printf("KV Server started. Listening on %s\n", SERVER_FIFO);
    printf("Press Ctrl+C to stop.\n");

    while (running) {
        /*
         * Open server FIFO for reading.
         * We also open for writing to prevent EOF when last client closes.
         */
        server_fd = open(SERVER_FIFO, O_RDONLY);
        if (server_fd == -1) {
            if (errno == EINTR) continue;
            perror("open server fifo");
            break;
        }

        /* Also open write end to keep FIFO alive */
        int dummy_fd = open(SERVER_FIFO, O_WRONLY);

        /* Read requests */
        while (running && (n = read(server_fd, buffer, sizeof(buffer) - 1)) > 0) {
            buffer[n] = '\0';

            /* Process each line (request) */
            char *line = strtok(buffer, "\n");
            while (line) {
                process_request(line);
                line = strtok(NULL, "\n");
            }
        }

        close(server_fd);
        if (dummy_fd != -1) close(dummy_fd);
    }

    /* Cleanup */
    unlink(SERVER_FIFO);
    printf("\nServer stopped.\n");
    return 0;
}
```

#### Client Implementation

```c
/*
 * kvclient.c - Client for the key-value server
 *
 * Build: gcc -o kvclient kvclient.c -Wall -Wextra
 * Usage: ./kvclient GET mykey
 *        ./kvclient SET mykey myvalue
 *        ./kvclient DEL mykey
 */

#define _GNU_SOURCE
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <fcntl.h>
#include <sys/stat.h>
#include <errno.h>

#define SERVER_FIFO "/tmp/kvserver.fifo"
#define MAX_MSG_LEN 4096
#define TIMEOUT_SECS 5

int main(int argc, char *argv[]) {
    char client_fifo[64];
    char request[MAX_MSG_LEN];
    char response[MAX_MSG_LEN];
    int server_fd, client_fd;
    pid_t my_pid = getpid();
    ssize_t n;

    if (argc < 3) {
        fprintf(stderr, "Usage: %s <GET|SET|DEL> key [value]\n", argv[0]);
        exit(1);
    }

    /* Create client-specific FIFO for response */
    snprintf(client_fifo, sizeof(client_fifo), "/tmp/kvclient.%d", my_pid);
    unlink(client_fifo);  /* Remove if exists */

    if (mkfifo(client_fifo, 0600) == -1) {
        perror("mkfifo client");
        exit(1);
    }

    /* Build request */
    if (argc >= 4) {
        snprintf(request, sizeof(request), "%d:%s:%s:%s\n",
                 my_pid, argv[1], argv[2], argv[3]);
    } else {
        snprintf(request, sizeof(request), "%d:%s:%s\n",
                 my_pid, argv[1], argv[2]);
    }

    /* Open server FIFO */
    server_fd = open(SERVER_FIFO, O_WRONLY);
    if (server_fd == -1) {
        perror("Cannot connect to server");
        unlink(client_fifo);
        exit(1);
    }

    /* Send request (atomic write) */
    if (write(server_fd, request, strlen(request)) == -1) {
        perror("write request");
        close(server_fd);
        unlink(client_fifo);
        exit(1);
    }
    close(server_fd);

    /*
     * Open client FIFO for reading response.
     * Use alarm() for timeout.
     */
    alarm(TIMEOUT_SECS);

    client_fd = open(client_fifo, O_RDONLY);
    if (client_fd == -1) {
        perror("open client fifo");
        unlink(client_fifo);
        exit(1);
    }

    alarm(0);  /* Cancel alarm */

    /* Read response */
    n = read(client_fd, response, sizeof(response) - 1);
    if (n > 0) {
        response[n] = '\0';
        /* Parse and display response */
        int status;
        char message[MAX_MSG_LEN];
        if (sscanf(response, "%d:%[^\n]", &status, message) == 2) {
            if (status == 0) {
                printf("%s\n", message);
            } else {
                fprintf(stderr, "Error: %s\n", message);
            }
        }
    } else if (n == 0) {
        fprintf(stderr, "Server closed connection\n");
    } else {
        perror("read response");
    }

    close(client_fd);
    unlink(client_fifo);
    return 0;
}
```

### Error Handling Patterns

Robust pipe-based programs must handle numerous error conditions.

#### Comprehensive Error Handling

```c
/*
 * Robust I/O functions for pipe communication
 */

#include <errno.h>
#include <unistd.h>

/*
 * Write exactly n bytes to a file descriptor.
 * Handles partial writes and interruptions.
 *
 * Returns:  n on success
 *          -1 on error (check errno)
 *          -2 on EPIPE (peer closed)
 */
ssize_t write_all(int fd, const void *buf, size_t n) {
    const char *p = buf;
    size_t remaining = n;

    while (remaining > 0) {
        ssize_t written = write(fd, p, remaining);

        if (written == -1) {
            if (errno == EINTR) {
                /* Interrupted by signal, retry */
                continue;
            }
            if (errno == EAGAIN || errno == EWOULDBLOCK) {
                /* Non-blocking fd, would block */
                /* In real code: use select/poll and retry */
                continue;
            }
            if (errno == EPIPE) {
                /* Peer closed - return special value */
                return -2;
            }
            /* Other error */
            return -1;
        }

        p += written;
        remaining -= written;
    }

    return n;
}

/*
 * Read exactly n bytes from a file descriptor.
 * Handles partial reads and interruptions.
 *
 * Returns:  n on success (all bytes read)
 *          0 < ret < n if EOF before n bytes
 *          0 on immediate EOF
 *         -1 on error
 */
ssize_t read_all(int fd, void *buf, size_t n) {
    char *p = buf;
    size_t remaining = n;

    while (remaining > 0) {
        ssize_t nread = read(fd, p, remaining);

        if (nread == -1) {
            if (errno == EINTR) {
                /* Interrupted by signal, retry */
                continue;
            }
            if (errno == EAGAIN || errno == EWOULDBLOCK) {
                /* Non-blocking fd, no data available */
                if (remaining < n) {
                    /* Partial read, return what we have */
                    return n - remaining;
                }
                continue;
            }
            /* Other error */
            return -1;
        }

        if (nread == 0) {
            /* EOF */
            break;
        }

        p += nread;
        remaining -= nread;
    }

    return n - remaining;
}

/*
 * Read a newline-terminated line from fd.
 *
 * Returns: length of line (including \n)
 *          0 on EOF
 *         -1 on error
 */
ssize_t read_line(int fd, char *buf, size_t maxlen) {
    size_t i = 0;

    while (i < maxlen - 1) {
        char c;
        ssize_t n = read(fd, &c, 1);

        if (n == -1) {
            if (errno == EINTR)
                continue;
            return -1;
        }

        if (n == 0) {
            /* EOF */
            break;
        }

        buf[i++] = c;
        if (c == '\n')
            break;
    }

    buf[i] = '\0';
    return i;
}
```

#### Error Codes Summary

```
┌───────────────────────────────────────────────────────────────────────────┐
│                        PIPE-RELATED ERROR CODES                            │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   errno         │ Meaning                    │ Common Cause               │
│   ══════════════╪════════════════════════════╪════════════════════════════│
│   EBADF         │ Bad file descriptor        │ fd not open, already closed│
│   EINTR         │ Interrupted by signal      │ Signal delivered during I/O│
│   EAGAIN        │ Would block (non-blocking) │ Pipe full/empty, O_NONBLOCK│
│   EWOULDBLOCK   │ Same as EAGAIN             │ (synonym on most systems)  │
│   EPIPE         │ Broken pipe                │ No readers, write attempted│
│   ENXIO         │ No such device             │ Open FIFO O_WRONLY|NONBLOCK│
│   ENOENT        │ No such file/directory     │ FIFO path doesn't exist    │
│   EACCES        │ Permission denied          │ Insufficient permissions   │
│   EEXIST        │ File exists                │ mkfifo on existing path    │
│   EMFILE        │ Too many open files        │ Per-process limit exceeded │
│   ENFILE        │ File table overflow        │ System-wide limit exceeded │
│   EFBIG         │ File too large             │ Exceeds pipe capacity limit│
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```

### Performance Considerations

#### Optimizing Pipe Throughput

```
┌───────────────────────────────────────────────────────────────────────────┐
│                     PIPE PERFORMANCE OPTIMIZATION                          │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   1. BUFFER SIZE SELECTION                                                 │
│   ═════════════════════════                                                │
│                                                                            │
│   Small writes (< 512 bytes):                                             │
│   • High overhead per byte (system call overhead dominates)               │
│   • Accumulate in userspace buffer, write in chunks                       │
│                                                                            │
│   Optimal write size:                                                      │
│   • 4096-8192 bytes typically best                                        │
│   • Matches page size, minimizes copies                                   │
│   • Stays within atomic guarantees for PIPE_BUF writes                    │
│                                                                            │
│                                                                            │
│   2. PIPE CAPACITY TUNING                                                  │
│   ════════════════════════                                                 │
│                                                                            │
│   Default 65KB may be insufficient for bursty workloads:                  │
│                                                                            │
│   /* Increase pipe capacity */                                            │
│   fcntl(pipefd[1], F_SETPIPE_SZ, 1024 * 1024);  /* 1 MB */               │
│                                                                            │
│   Benefits:                                                                │
│   • Smooths out producer/consumer rate differences                        │
│   • Reduces context switches                                              │
│   • May waste memory if not utilized                                      │
│                                                                            │
│                                                                            │
│   3. AVOID SMALL READS                                                     │
│   ════════════════════                                                     │
│                                                                            │
│   /* BAD: Reading byte-by-byte */                                         │
│   while (read(fd, &c, 1) == 1) { ... }                                    │
│                                                                            │
│   /* GOOD: Bulk reading with buffering */                                 │
│   char buf[8192];                                                         │
│   ssize_t n;                                                              │
│   while ((n = read(fd, buf, sizeof(buf))) > 0) {                          │
│       process_buffer(buf, n);                                             │
│   }                                                                       │
│                                                                            │
│                                                                            │
│   4. USE SPLICE FOR ZERO-COPY                                             │
│   ═══════════════════════════                                              │
│                                                                            │
│   When moving data between file/socket and pipe:                          │
│   • splice() avoids user-space copies                                     │
│   • Significant speedup for large transfers                               │
│   • Requires both ends to support splice                                  │
│                                                                            │
│                                                                            │
│   5. NON-BLOCKING I/O WITH POLL                                           │
│   ═════════════════════════════                                            │
│                                                                            │
│   For multiplexing multiple pipes:                                        │
│   • Use poll() or epoll() instead of blocking I/O                        │
│   • Avoids creating thread per pipe                                       │
│   • Better CPU utilization                                                │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```

#### Benchmarking Pipe Performance

```c
/*
 * Simple pipe throughput benchmark
 */
#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
#include <time.h>
#include <sys/wait.h>

#define DATA_SIZE (1024 * 1024 * 100)  /* 100 MB */

int main(void) {
    int pipefd[2];
    char *buffer;
    size_t buf_size = 65536;  /* Try different sizes */

    pipe(pipefd);
    buffer = malloc(buf_size);

    clock_t start = clock();

    if (fork() == 0) {
        /* Child: write data */
        close(pipefd[0]);

        size_t written = 0;
        while (written < DATA_SIZE) {
            size_t chunk = (DATA_SIZE - written < buf_size) ?
                           DATA_SIZE - written : buf_size;
            write(pipefd[1], buffer, chunk);
            written += chunk;
        }
        close(pipefd[1]);
        exit(0);
    }

    /* Parent: read data */
    close(pipefd[1]);

    size_t total_read = 0;
    ssize_t n;
    while ((n = read(pipefd[0], buffer, buf_size)) > 0) {
        total_read += n;
    }
    close(pipefd[0]);
    wait(NULL);

    clock_t end = clock();
    double seconds = (double)(end - start) / CLOCKS_PER_SEC;
    double mbps = (DATA_SIZE / (1024.0 * 1024.0)) / seconds;

    printf("Transferred: %zu bytes\n", total_read);
    printf("Time: %.3f seconds\n", seconds);
    printf("Throughput: %.2f MB/s\n", mbps);

    free(buffer);
    return 0;
}
```

### Common Pitfalls and Debugging

```
┌───────────────────────────────────────────────────────────────────────────┐
│                        COMMON PIPE PITFALLS                                │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   PITFALL 1: Forgetting to close unused pipe ends                         │
│   ══════════════════════════════════════════════                          │
│                                                                            │
│   /* WRONG: Child never sees EOF */                                       │
│   pipe(pipefd);                                                           │
│   if (fork() == 0) {                                                      │
│       /* Child reads, but parent's write end still open! */              │
│       while (read(pipefd[0], buf, n) > 0) ...                             │
│   }                                                                       │
│                                                                            │
│   /* RIGHT: Close unused ends */                                          │
│   pipe(pipefd);                                                           │
│   if (fork() == 0) {                                                      │
│       close(pipefd[1]);  /* Close write end in child */                   │
│       while (read(pipefd[0], buf, n) > 0) ...                             │
│   } else {                                                                │
│       close(pipefd[0]);  /* Close read end in parent */                   │
│       write(pipefd[1], data, len);                                        │
│       close(pipefd[1]);  /* Signal EOF to child */                        │
│   }                                                                       │
│                                                                            │
│                                                                            │
│   PITFALL 2: Deadlock from blocking opens on FIFOs                        │
│   ════════════════════════════════════════════════                         │
│                                                                            │
│   /* DEADLOCK: Both processes wait for the other */                       │
│   Process A: open("/tmp/fifo1", O_RDONLY);  /* Blocks */                  │
│   Process B: open("/tmp/fifo2", O_RDONLY);  /* Blocks */                  │
│                                                                            │
│   /* SOLUTION: Use O_RDWR or coordinate open order */                     │
│   Process A: open("/tmp/fifo1", O_RDWR);    /* Doesn't block */           │
│                                                                            │
│                                                                            │
│   PITFALL 3: Not handling SIGPIPE                                         │
│   ════════════════════════════════                                         │
│                                                                            │
│   Default: Process terminates silently on SIGPIPE                         │
│                                                                            │
│   /* SOLUTION: Ignore SIGPIPE, handle EPIPE */                            │
│   signal(SIGPIPE, SIG_IGN);                                               │
│   if (write(fd, data, len) == -1 && errno == EPIPE) {                    │
│       /* Handle gracefully */                                             │
│   }                                                                       │
│                                                                            │
│                                                                            │
│   PITFALL 4: Assuming atomic writes for large data                        │
│   ══════════════════════════════════════════════                           │
│                                                                            │
│   Writes > PIPE_BUF may interleave with other writers!                    │
│                                                                            │
│   /* SOLUTION: Use mutex or ensure single writer */                       │
│   pthread_mutex_lock(&pipe_mutex);                                        │
│   write(fd, large_data, large_len);                                       │
│   pthread_mutex_unlock(&pipe_mutex);                                      │
│                                                                            │
│                                                                            │
│   PITFALL 5: FIFO left behind after crash                                 │
│   ═══════════════════════════════════════                                  │
│                                                                            │
│   /* SOLUTION: Always unlink on startup and use atexit */                 │
│   unlink(FIFO_PATH);                                                      │
│   mkfifo(FIFO_PATH, 0666);                                                │
│   atexit(cleanup_fifo);                                                   │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```

---

## 9. Conclusion

### Summary of Key Concepts

This document has explored Unix pipes and the close system call in depth, following the style of Maurice J. Bach's classic treatment of the UNIX operating system. Let us recapitulate the essential concepts:

**The Unix Philosophy of Simplicity**: Pipes embody the Unix philosophy—do one thing well and combine simple tools. A pipe is simply a buffer with a read end and a write end, yet this simple abstraction enables powerful compositions.

**The Three-Level Data Structure Hierarchy**: Understanding pipes requires understanding the kernel's file abstraction:

- **Per-process file descriptor table**: Mapping integers (file descriptors) to file entries
- **System-wide file table**: Tracking open instances with reference counts and positions
- **Inode table**: Representing the underlying file object with pipe-specific data

**Reference Counting as Resource Management**: The kernel uses reference counting throughout. When `f_count` reaches zero, resources are released. When `pipe->readers` or `pipe->writers` reaches zero, specific actions occur (SIGPIPE or EOF).

**The close() System Call**: Though simple in interface, `close()` triggers a cascade:

1. Remove fd from per-process table
2. Decrement file entry reference count
3. If count reaches zero, perform file-type-specific cleanup
4. For pipes: update reader/writer counts, wake blocked processes, possibly destroy pipe

**Atomicity Guarantees**: POSIX mandates that writes ≤ PIPE_BUF (typically 4096 bytes) are atomic. Larger writes may interleave, requiring application-level synchronization.

**Named Pipes (FIFOs)**: Extend anonymous pipes to unrelated processes via filesystem presence, with special blocking semantics on open().

### The Enduring Relevance of Pipes

Despite being over 50 years old, pipes remain fundamental to Unix systems:

- **Shell pipelines** power daily command-line work
- **Process supervision** systems use pipes for communication
- **Language Server Protocol (LSP)** implementations often use pipes
- **Container orchestration** relies on pipes for I/O handling
- **Zero-copy optimizations** like splice() build on the pipe abstraction

### Further Study

For those wishing to deepen their understanding:

1. **Read the kernel source**: Linux's `fs/pipe.c` is well-commented and educational
2. **POSIX specifications**: The formal requirements for pipe behavior
3. **Historical papers**: McIlroy's original pipe paper from 1964
4. **Bach's book**: "The Design of the UNIX Operating System" remains invaluable

---

## Appendix A: Quick Reference

### System Calls Summary

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                      PIPE-RELATED SYSTEM CALLS                               │
├─────────────────┬───────────────────────────────────────────────────────────┤
│ System Call     │ Description                                               │
├─────────────────┼───────────────────────────────────────────────────────────┤
│ pipe(fd[2])     │ Create anonymous pipe; fd[0]=read, fd[1]=write           │
│ pipe2(fd[2],fl) │ Create pipe with flags (O_CLOEXEC, O_NONBLOCK)           │
│ mkfifo(path,m)  │ Create named pipe (FIFO) at path with mode m             │
│ mknod(p,m,dev)  │ Create special file (including FIFO with S_IFIFO)        │
│ open(path,fl)   │ Open file/FIFO; blocks for FIFO unless O_NONBLOCK        │
│ read(fd,b,n)    │ Read up to n bytes; returns 0 on EOF (no writers)        │
│ write(fd,b,n)   │ Write n bytes; SIGPIPE/EPIPE if no readers               │
│ close(fd)       │ Close file descriptor, decrement reference counts        │
│ dup(fd)         │ Duplicate fd, returns new fd sharing file entry          │
│ dup2(old,new)   │ Duplicate old to new, closing new if open                │
│ fcntl(fd,cmd)   │ File control: get/set pipe size, flags, etc.             │
│ select(...)     │ Wait for readiness on multiple fds                        │
│ poll(fds,n,to)  │ Wait for events on multiple fds                           │
│ splice(...)     │ Zero-copy data transfer between pipe and fd               │
│ vmsplice(...)   │ Zero-copy from user memory to pipe                        │
│ tee(in,out,l,f) │ Duplicate data between pipes without consuming           │
└─────────────────┴───────────────────────────────────────────────────────────┘
```

### Important Constants

```
┌──────────────────────────┬────────────────────────────────────────────────┐
│ Constant                  │ Typical Value / Meaning                        │
├──────────────────────────┼────────────────────────────────────────────────┤
│ PIPE_BUF                 │ 4096 (Linux), 512 (POSIX minimum)              │
│ Default pipe capacity    │ 65536 bytes (16 x 4KB pages)                   │
│ pipe-max-size            │ 1048576 (1MB, adjustable via /proc)            │
│ SIGPIPE                  │ Signal 13, sent on write to broken pipe        │
│ EPIPE                    │ errno 32, returned on write to broken pipe     │
│ O_NONBLOCK               │ Non-blocking I/O flag                          │
│ O_CLOEXEC                │ Close on exec flag                             │
└──────────────────────────┴────────────────────────────────────────────────┘
```

---

## Appendix B: References

### Primary Sources

1. **Bach, Maurice J.** "The Design of the UNIX Operating System." Prentice Hall, 1986.
   - The definitive reference for classical Unix kernel internals

2. **Kernighan, Brian W., and Rob Pike.** "The Unix Programming Environment." Prentice Hall, 1984.
   - Excellent practical coverage of pipes and shell programming

3. **Stevens, W. Richard, and Stephen A. Rago.** "Advanced Programming in the UNIX Environment." Third Edition, Addison-Wesley, 2013.
   - Comprehensive modern treatment of Unix system programming

4. **Kerrisk, Michael.** "The Linux Programming Interface." No Starch Press, 2010.
   - Authoritative Linux-specific system programming reference

### Historical Papers

5. **McIlroy, M. Douglas.** "A Research UNIX Reader: Annotated Excerpts from the Programmer's Manual, 1971-1986." Bell Labs Technical Report, 1987.
   - Historical context for pipe development

6. **Thompson, Ken, and Dennis Ritchie.** "The UNIX Time-Sharing System." Communications of the ACM, 1974.
   - The original Unix paper

### Linux Kernel Documentation

7. **Linux kernel source: fs/pipe.c**
   - Current pipe implementation

8. **Linux man-pages project**
   - https://man7.org/linux/man-pages/

---

_Document Version: 1.0_
_Last Updated: 2026-02-12_
_Style: Maurice Bach / Unix Internals_
