# Comprehensive Guide to Unix/Linux File Modes and Process GID

## Table of Contents

1. [Introduction](#introduction)
2. [Understanding File Modes](#understanding-file-modes)
   - [Basic Permission Types](#basic-permission-types)
   - [Permission Categories](#permission-categories)
   - [Numeric (Octal) Notation](#numeric-octal-notation)
   - [Symbolic Notation](#symbolic-notation)
3. [Special Permission Bits](#special-permission-bits)
   - [SUID (Set User ID)](#suid-set-user-id)
   - [SGID (Set Group ID)](#sgid-set-group-id)
   - [Sticky Bit](#sticky-bit)
4. [Group ID (GID) Fundamentals](#group-id-gid-fundamentals)
   - [What is a GID?](#what-is-a-gid)
   - [Primary vs Supplementary Groups](#primary-vs-supplementary-groups)
   - [Group Database Structure](#group-database-structure)
5. [Process GID Concepts](#process-gid-concepts)
   - [Real GID (RGID)](#real-gid-rgid)
   - [Effective GID (EGID)](#effective-gid-egid)
   - [Saved Set-Group-ID (SSGID)](#saved-set-group-id-ssgid)
   - [File System GID (FSGID)](#file-system-gid-fsgid)
6. [Permission Checking Mechanisms](#permission-checking-mechanisms)
7. [Practical Examples and Use Cases](#practical-examples-and-use-cases)
8. [Security Implications](#security-implications)
9. [System Calls and APIs](#system-calls-and-apis)
10. [Best Practices](#best-practices)
11. [Troubleshooting](#troubleshooting)
12. [Advanced Topics](#advanced-topics)
13. [References](#references)

---

## Introduction

Unix and Linux operating systems employ a sophisticated permission system that controls access to files,
directories, and system resources. This permission model is fundamental to system security and multi-user
environments. Understanding file modes and Group IDs (GIDs) is essential for system administrators,
developers, and security professionals.

This comprehensive guide explores every aspect of file modes and GID management, from basic concepts to
advanced implementations. Whether you're managing a production server, developing system-level applications,
or simply trying to understand how Unix permissions work, this guide provides the depth of knowledge you need.

### Historical Context

The Unix permission system was developed in the early 1970s at Bell Labs as part of the original Unix
operating system. Ken Thompson and Dennis Ritchie designed a simple yet powerful model that has stood the test
of time. The original design goals were:

- **Simplicity**: Easy to understand and implement
- **Efficiency**: Minimal overhead for permission checks
- **Flexibility**: Support for multi-user environments
- **Security**: Protection of user data and system resources

The permission model has evolved over the decades, with additions like Access Control Lists (ACLs),
capabilities, and security modules (SELinux, AppArmor), but the core file mode and GID concepts remain central
to Unix/Linux security.

### Why This Matters

Understanding file modes and GIDs is crucial because:

1. **Security**: Misconfigured permissions are a leading cause of security vulnerabilities
2. **Functionality**: Many applications depend on correct permission settings
3. **Compliance**: Regulatory requirements often mandate specific permission configurations
4. **Troubleshooting**: Permission issues are common sources of system problems
5. **Development**: System programming requires deep understanding of these concepts

---

## Understanding File Modes

File modes in Unix/Linux systems define who can access a file and what operations they can perform. Every file
and directory has an associated mode that controls these access permissions.

### The Inode and File Metadata

Before diving into permissions, it's important to understand where this information is stored. In Unix
filesystems, each file is represented by an inode (index node) that contains metadata about the file:

```
+------------------+
|     Inode        |
+------------------+
| File Type        |
| Permissions      |
| Owner UID        |
| Group GID        |
| Link Count       |
| File Size        |
| Timestamps       |
| Block Pointers   |
+------------------+
```

The permissions are stored as a 16-bit field within the inode:

```
Bits:  15 14 13 12 | 11 10 9 | 8 7 6 | 5 4 3 | 2 1 0
File Type   | Special | Owner | Group | Other
|  Bits   |  rwx  |  rwx  |  rwx
```

### Basic Permission Types

Unix systems define three fundamental permission types that control file access:

#### Read Permission (r)

Read permission grants the ability to view the contents of a file or list the contents of a directory.

**For Regular Files:**

- View file contents using commands like `cat`, `less`, `more`
- Copy the file
- Open the file for reading in applications

**For Directories:**

- List directory contents using `ls`
- View file names within the directory
- Use tab completion for files in the directory

**Binary Representation:** `100` (4 in octal)

```bash
# Example: File with read permission
$ ls -l readable_file.txt
-r--r--r-- 1 user group 1024 Jan 15 10:00 readable_file.txt

# Can read the file
$ cat readable_file.txt
This is the content of the file.

# Cannot write to the file
$ echo "new content" > readable_file.txt
bash: readable_file.txt: Permission denied
```

#### Write Permission (w)

Write permission grants the ability to modify file contents or alter directory contents (create, delete,
rename files).

**For Regular Files:**

- Modify file contents
- Truncate the file
- Append to the file
- Delete file contents

**For Directories:**

- Create new files within the directory
- Delete files within the directory (with some caveats)
- Rename files within the directory
- Create subdirectories

**Binary Representation:** `010` (2 in octal)

```bash
# Example: File with write permission
$ ls -l writable_file.txt
--w--w--w- 1 user group 1024 Jan 15 10:00 writable_file.txt

# Can write to the file
$ echo "new content" > writable_file.txt

# Cannot read the file (no read permission)
$ cat writable_file.txt
cat: writable_file.txt: Permission denied
```

**Important Note on Directory Write Permission:**

Having write permission on a directory allows you to create and delete files in that directory, even if you
don't own those files. This is why the sticky bit (discussed later) is important for shared directories like
`/tmp`.

```bash
# Directory with write permission
$ ls -ld /shared_directory
drwxrwxrwx 2 root root 4096 Jan 15 10:00 /shared_directory

# Any user can create files here
$ touch /shared_directory/my_file.txt

# Any user can delete files here (without sticky bit)
$ rm /shared_directory/other_users_file.txt
```

#### Execute Permission (x)

Execute permission grants the ability to run a file as a program or enter a directory.

**For Regular Files:**

- Run the file as an executable program
- Required for scripts and binary executables
- Works in conjunction with the shebang (#!) for scripts

**For Directories:**

- Enter the directory using `cd`
- Access files within the directory (with appropriate file permissions)
- Required to traverse the directory in path resolution

**Binary Representation:** `001` (1 in octal)

```bash
# Example: Executable file
$ ls -l script.sh
-rwxr-xr-x 1 user group 256 Jan 15 10:00 script.sh

# Can execute the script
$ ./script.sh
Hello, World!

# File without execute permission
$ chmod -x script.sh
$ ./script.sh
bash: ./script.sh: Permission denied
```

**The Directory Execute Permission Explained:**

The execute permission on directories is often misunderstood. Here's a detailed breakdown:

```bash
# Directory with only read permission (no execute)
$ chmod 444 test_dir
$ ls test_dir
file1.txt  file2.txt  file3.txt

# Cannot access files within
$ cat test_dir/file1.txt
cat: test_dir/file1.txt: Permission denied

# Cannot enter the directory
$ cd test_dir
bash: cd: test_dir: Permission denied

# Directory with only execute permission (no read)
$ chmod 111 test_dir

# Cannot list contents
$ ls test_dir
ls: cannot open directory 'test_dir': Permission denied

# But can access files if you know their names
$ cat test_dir/file1.txt
Contents of file1
```

### Permission Categories

Permissions are assigned to three categories of users:

#### Owner (User)

The owner is typically the user who created the file. The owner has special privileges:

- Can always change the file's permissions (chmod)
- Can change the file's group (if member of the new group)
- First permission set checked during access control

```bash
# Viewing the owner
$ ls -l myfile.txt
-rw-r--r-- 1 alice developers 1024 Jan 15 10:00 myfile.txt
^^^^^
Owner is 'alice'

# Changing ownership (requires root or file owner)
$ chown bob myfile.txt
```

#### Group

The group represents a collection of users who share common access needs:

- Second permission set checked (after owner, if user is not owner)
- Users can belong to multiple groups
- Primary group is used for new file creation

```bash
# Viewing the group
$ ls -l myfile.txt
-rw-r--r-- 1 alice developers 1024 Jan 15 10:00 myfile.txt
^^^^^^^^^^
Group is 'developers'

# Changing group ownership
$ chgrp testers myfile.txt

# Or using chown
$ chown :testers myfile.txt
```

#### Others (World)

The "others" category applies to all users who are neither the owner nor members of the file's group:

- Third and final permission set checked
- Represents the default access for all other system users
- Should typically be the most restrictive

```bash
# The last three permission bits apply to 'others'
-rw-r--r-- 1 alice developers 1024 Jan 15 10:00 myfile.txt
^^^
Others have read-only access
```

### Permission Checking Algorithm

When a process attempts to access a file, the kernel follows this algorithm:

```
1. Is the process running as root (UID 0)?
YES → Grant access (with some exceptions)
NO  → Continue

2. Is the process's effective UID equal to the file's owner UID?
YES → Use OWNER permissions, STOP
NO  → Continue

3. Is the process's effective GID or any supplementary GID equal
to the file's group GID?
YES → Use GROUP permissions, STOP
NO  → Continue

4. Use OTHER permissions
```

```c
/* Simplified permission check pseudocode */
int check_permission(process *p, file *f, int access_mode) {
  /* Root bypass (simplified) */
  if (p->euid == 0) {
    if (access_mode == EXECUTE && !any_execute_bit(f))
      return -EACCES;
    return 0;
  }

  /* Owner check */
  if (p->euid == f->uid) {
    if ((f->mode >> 6) & access_mode)
      return 0;
    return -EACCES;
  }

  /* Group check */
  if (in_group(p, f->gid)) {
    if ((f->mode >> 3) & access_mode)
      return 0;
    return -EACCES;
  }

  /* Others check */
  if (f->mode & access_mode)
    return 0;
  return -EACCES;
}
```

### Numeric (Octal) Notation

The most compact way to represent permissions is using octal (base-8) notation. Each permission category
(owner, group, others) is represented by a single octal digit.

#### Understanding Octal Calculation

Each permission type has a value:

- Read (r) = 4
- Write (w) = 2
- Execute (x) = 1

Add these values together for each category:

```
Permission  Binary  Octal
---------   ------  -----
---         000     0
--x         001     1
-w-         010     2
-wx         011     3
r--         100     4
r-x         101     5
rw-         110     6
rwx         111     7
```

#### Common Permission Modes

```bash
# 755 - Standard for executables and directories
-rwxr-xr-x  (Owner: full, Group: read+execute, Others: read+execute)

# 644 - Standard for regular files
-rw-r--r--  (Owner: read+write, Group: read, Others: read)

# 600 - Private files
-rw-------  (Owner: read+write, Group: none, Others: none)

# 700 - Private directories/executables
-rwx------  (Owner: full, Group: none, Others: none)

# 777 - Full access (generally not recommended)
-rwxrwxrwx  (Everyone: full access)

# 666 - Read/write for everyone (not recommended)
-rw-rw-rw-  (Everyone: read+write)

# 444 - Read-only for everyone
-r--r--r--  (Everyone: read only)

# 000 - No access (except root)
----------  (No one can access)
```

#### Four-Digit Octal Notation

When special permission bits (SUID, SGID, sticky bit) are included, a fourth digit is prepended:

```bash
# 4755 - SUID executable
-rwsr-xr-x

# 2755 - SGID executable
-rwxr-sr-x

# 1777 - Sticky bit (common for /tmp)
drwxrwxrwt

# 6755 - Both SUID and SGID
-rwsr-sr-x

# 7777 - All special bits and all permissions
-rwsrwsrwt
```

#### Octal Calculation Examples

```bash
# Example 1: rw-r--r-- (644)
Owner:  rw- = 4 + 2 + 0 = 6
Group:  r-- = 4 + 0 + 0 = 4
Others: r-- = 4 + 0 + 0 = 4
Result: 644

# Example 2: rwxr-xr-x (755)
Owner:  rwx = 4 + 2 + 1 = 7
Group:  r-x = 4 + 0 + 1 = 5
Others: r-x = 4 + 0 + 1 = 5
Result: 755

# Example 3: rw------- (600)
Owner:  rw- = 4 + 2 + 0 = 6
Group:  --- = 0 + 0 + 0 = 0
Others: --- = 0 + 0 + 0 = 0
Result: 600

# Example 4: rwsr-xr-x (4755) with SUID
Special: SUID = 4
Owner:   rwx = 7 (displayed as rws because of SUID)
Group:   r-x = 5
Others:  r-x = 5
Result:  4755
```

### Symbolic Notation

Symbolic notation provides a more human-readable way to view and modify permissions.

#### Permission Display Format

```
-rwxr-xr-x
│└┬┘└┬┘└┬┘
│ │  │  └── Others permissions (r-x)
│ │  └───── Group permissions (r-x)
│ └──────── Owner permissions (rwx)
└────────── File type indicator
```

#### File Type Indicators

```
-  Regular file
d  Directory
l  Symbolic link
c  Character device
b  Block device
p  Named pipe (FIFO)
s  Socket
```

#### Using chmod with Symbolic Notation

The symbolic notation uses the following format:

```
chmod [who][operator][permission] file
```

**Who:**

- `u` - User (owner)
- `g` - Group
- `o` - Others
- `a` - All (u, g, and o)

**Operator:**

- `+` - Add permission
- `-` - Remove permission
- `=` - Set exact permission

**Permission:**

- `r` - Read
- `w` - Write
- `x` - Execute
- `X` - Execute only if directory or already executable
- `s` - SUID/SGID
- `t` - Sticky bit

```bash
# Add execute permission for owner
$ chmod u+x script.sh

# Remove write permission for group and others
$ chmod go-w file.txt

# Set read-only for everyone
$ chmod a=r file.txt

# Add SUID
$ chmod u+s program

# Add SGID to directory
$ chmod g+s shared_dir

# Add sticky bit
$ chmod +t /tmp

# Complex example: owner can do everything,
# group can read and execute, others can only read
$ chmod u=rwx,g=rx,o=r file.txt

# Copy permissions from another file
$ chmod --reference=source_file target_file

# Recursive permission change
$ chmod -R 755 directory/
```

#### Symbolic Permission Examples

```bash
# Make a script executable by the owner
$ chmod u+x myscript.sh
Before: -rw-r--r--
After:  -rwxr--r--

# Allow group to write
$ chmod g+w document.txt
Before: -rw-r--r--
After:  -rw-rw-r--

# Remove all permissions for others
$ chmod o= sensitive_file.txt
Before: -rw-r--r--
After:  -rw-r-----

# Make a directory and its contents accessible
$ chmod u=rwx,g=rx,o= private_dir
Before: drwxr-xr-x
After:  drwxr-x---

# Set exact permissions
$ chmod u=rw,g=r,o= config.conf
Result: -rw-r-----
```

---

## Special Permission Bits

Beyond the standard read, write, and execute permissions, Unix/Linux systems support three special permission
bits that modify how programs execute or how directory contents are managed.

### SUID (Set User ID)

The SUID bit is one of the most powerful and potentially dangerous permission settings in Unix systems. When
set on an executable file, it causes the program to run with the privileges of the file's owner, regardless of
who executes it.

#### How SUID Works

```
Normal execution:
User alice runs program owned by root
→ Program runs as alice (alice's UID)

With SUID:
User alice runs SUID program owned by root
→ Program runs as root (root's UID)
```

#### Setting and Identifying SUID

```bash
# Set SUID using symbolic notation
$ chmod u+s program

# Set SUID using octal notation
$ chmod 4755 program

# Identifying SUID files
$ ls -l /usr/bin/passwd
-rwsr-xr-x 1 root root 68208 Jan 15 10:00 /usr/bin/passwd
^
's' in owner execute position indicates SUID

# If there's no execute permission, 'S' (capital) is shown
$ ls -l broken_suid
-rwSr-xr-x 1 root root 1024 Jan 15 10:00 broken_suid
^
'S' means SUID is set but owner lacks execute permission
```

#### Common SUID Programs

Many system utilities require SUID to function properly:

```bash
# passwd - Allows users to change their passwords
$ ls -l /usr/bin/passwd
-rwsr-xr-x 1 root root 68208 /usr/bin/passwd

# su - Switch user
$ ls -l /usr/bin/su
-rwsr-xr-x 1 root root 67816 /usr/bin/su

# sudo - Execute commands as another user
$ ls -l /usr/bin/sudo
-rwsr-xr-x 1 root root 166056 /usr/bin/sudo

# ping - Send ICMP packets (requires raw socket access)
$ ls -l /usr/bin/ping
-rwsr-xr-x 1 root root 44168 /usr/bin/ping

# mount/umount - Mount/unmount filesystems
$ ls -l /usr/bin/mount
-rwsr-xr-x 1 root root 55528 /usr/bin/mount
```

#### SUID Security Considerations

SUID programs are frequent targets for privilege escalation attacks:

```bash
# Find all SUID files on the system
$ find / -perm -4000 -type f 2>/dev/null

# Find SUID files owned by root
$ find / -perm -4000 -user root -type f 2>/dev/null

# Audit SUID files regularly
$ find / -perm -4000 -type f -exec ls -la {} \; 2>/dev/null > suid_audit.txt
```

**Best Practices for SUID:**

1. **Minimize SUID usage** - Only use when absolutely necessary
2. **Audit regularly** - Maintain an inventory of SUID files
3. **Drop privileges** - Programs should drop SUID privileges as soon as possible
4. **Avoid SUID scripts** - Many systems ignore SUID on scripts for security
5. **Use alternatives** - Consider capabilities or sudo instead

#### SUID on Directories

SUID on directories is generally ignored on Linux systems. However, on some older Unix systems, it had special
meaning for directory creation.

### SGID (Set Group ID)

The SGID bit has different effects depending on whether it's applied to an executable file or a directory.

#### SGID on Executable Files

When set on an executable, the program runs with the privileges of the file's group:

```bash
# Set SGID using symbolic notation
$ chmod g+s program

# Set SGID using octal notation
$ chmod 2755 program

# Identifying SGID executables
$ ls -l /usr/bin/wall
-rwxr-sr-x 1 root tty 30800 Jan 15 10:00 /usr/bin/wall
^
's' in group execute position indicates SGID
```

**Common SGID Programs:**

```bash
# wall - Write to all users (needs tty group)
$ ls -l /usr/bin/wall
-rwxr-sr-x 1 root tty 30800 /usr/bin/wall

# write - Write to another user's terminal
$ ls -l /usr/bin/write
-rwxr-sr-x 1 root tty 30800 /usr/bin/write

# crontab - Manage cron jobs
$ ls -l /usr/bin/crontab
-rwxr-sr-x 1 root crontab 43568 /usr/bin/crontab
```

#### SGID on Directories

SGID on directories has a practical use: it causes new files and subdirectories created within to inherit the
directory's group, rather than the creator's primary group.

```bash
# Create a shared directory
$ mkdir /shared
$ chgrp developers /shared
$ chmod 2775 /shared

$ ls -ld /shared
drwxrwsr-x 2 root developers 4096 Jan 15 10:00 /shared
^
's' indicates SGID on directory

# When user alice (primary group: users) creates a file:
$ touch /shared/new_file.txt
$ ls -l /shared/new_file.txt
-rw-r--r-- 1 alice developers 0 Jan 15 10:00 new_file.txt
^^^^^^^^^^
Group is 'developers', not 'users'
```

**Practical Use Case: Collaborative Directories**

```bash
# Create a project directory for team collaboration
$ mkdir /projects/webapp
$ chgrp webdev /projects/webapp
$ chmod 2775 /projects/webapp

# All files created will have 'webdev' group
# All team members in 'webdev' group can collaborate

# For stricter security (no others access):
$ chmod 2770 /projects/webapp
```

### Sticky Bit

The sticky bit has a specific purpose when applied to directories: it restricts file deletion so that only the
file's owner, the directory's owner, or root can delete or rename files within the directory.

#### Understanding the Sticky Bit

```bash
# Set sticky bit using symbolic notation
$ chmod +t directory

# Set sticky bit using octal notation
$ chmod 1777 directory

# Identifying sticky bit
$ ls -ld /tmp
drwxrwxrwt 18 root root 4096 Jan 15 10:00 /tmp
^
't' in others execute position indicates sticky bit

# If there's no execute permission for others, 'T' is shown
$ ls -ld weird_dir
drwxrwxrwT 2 root root 4096 Jan 15 10:00 weird_dir
^
'T' means sticky bit set but others lack execute permission
```

#### Why Sticky Bit Matters

Without the sticky bit, anyone with write permission on a directory could delete any file within it,
regardless of file ownership:

```bash
# Without sticky bit on /tmp:
# User bob could delete alice's files!

# With sticky bit:
# Users can only delete their own files
```

**Common Sticky Bit Directories:**

```bash
# /tmp - Temporary files
$ ls -ld /tmp
drwxrwxrwt 18 root root 4096 Jan 15 10:00 /tmp

# /var/tmp - Persistent temporary files
$ ls -ld /var/tmp
drwxrwxrwt 6 root root 4096 Jan 15 10:00 /var/tmp

# Shared upload directories
$ ls -ld /uploads
drwxrwxrwt 10 www-data www-data 4096 Jan 15 10:00 /uploads
```

#### Sticky Bit on Files (Historical)

Historically, the sticky bit on executable files told the system to keep the program's code segment in swap
space after execution for faster subsequent loading. This is ignored on modern systems.

### Combining Special Bits

Special bits can be combined using octal notation:

```
Special Bit    Octal Value
-----------    -----------
SUID           4
SGID           2
Sticky         1
```

```bash
# SUID + SGID (4 + 2 = 6)
$ chmod 6755 program
-rwsr-sr-x

# SUID + Sticky (4 + 1 = 5)
$ chmod 5755 program
-rwsr-xr-t

# SGID + Sticky (2 + 1 = 3)
$ chmod 3755 program
-rwxr-sr-t

# All three (4 + 2 + 1 = 7)
$ chmod 7755 program
-rwsr-sr-t
```

### Special Bits Permission Table

```
+--------+----------+-----------+----------------------------------+
| Octal  | Files    | Dirs      | Description                      |
+--------+----------+-----------+----------------------------------+
| 0      | ---      | ---       | No special bits                  |
| 1      | ---      | Sticky    | Restrict deletion in directory   |
| 2      | SGID     | SGID      | Run as group / inherit group     |
| 3      | SGID     | SGID+Stky | Both SGID and sticky             |
| 4      | SUID     | (ignored) | Run as owner                     |
| 5      | SUID     | Sticky    | SUID file, sticky directory      |
| 6      | SUID+GID | SGID      | Both SUID and SGID               |
| 7      | All      | SGID+Stky | All special bits                 |
+--------+----------+-----------+----------------------------------+
```

---

## Group ID (GID) Fundamentals

Groups are a fundamental mechanism for organizing users and managing access to resources. Every user belongs
to at least one group, and every file is associated with exactly one group.

### What is a GID?

A GID (Group ID) is a numeric identifier assigned to a group. The system uses this number internally to track
group memberships and permissions:

```
Group Name      GID
----------      ---
root            0
wheel           10
audio           29
video           44
users           100
docker          999
developers      1001
```

**GID Ranges (Linux conventions):**

```
GID Range        Purpose
---------        -------
0                root group
1-99             System groups (distribution-specific)
100-499          System groups for installed packages
500-999          System groups (some distributions)
1000+            Regular user groups (Debian/Ubuntu)
500+             Regular user groups (RHEL/CentOS)
65534            nobody/nogroup (overflow group)
```

### Primary vs Supplementary Groups

Each user has a primary group and zero or more supplementary groups:

#### Primary Group

- Set in `/etc/passwd`
- Used as the default group for new files created by the user
- A user has exactly one primary group

```bash
# View user's primary group
$ id -g alice
1001

$ id -gn alice
developers

# The primary group is the fourth field in /etc/passwd
$ grep alice /etc/passwd
alice:x:1001:1001:Alice Smith:/home/alice:/bin/bash
^^^^
Primary GID
```

#### Supplementary Groups

- Defined in `/etc/group`
- Provide additional group memberships
- A user can belong to many supplementary groups

```bash
# View all groups a user belongs to
$ id alice
uid=1001(alice) gid=1001(developers) groups=1001(developers),27(sudo),44(video),1002(webdev)

# Just the group names
$ groups alice
alice : developers sudo video webdev

# View supplementary groups (GIDs)
$ id -G alice
1001 27 44 1002
```

### Group Database Structure

Group information is stored in several system files:

#### /etc/group

The primary group database file:

```bash
$ cat /etc/group
root:x:0:
daemon:x:1:
bin:x:2:
sys:x:3:
adm:x:4:syslog,alice
tty:x:5:
disk:x:6:
...
developers:x:1001:alice,bob,charlie
webdev:x:1002:alice,david
```

**Format:** `group_name:password:GID:user_list`

```
Field         Description
-----         -----------
group_name    The name of the group
password      Usually 'x' (password in /etc/gshadow) or empty
GID           The numeric group ID
user_list     Comma-separated list of supplementary members
```

#### /etc/gshadow

Contains encrypted group passwords and group administrators:

```bash
$ sudo cat /etc/gshadow
root:::
developers:!::alice,bob,charlie
webdev:$6$hash...::alice,david
```

**Format:** `group_name:password:administrators:members`

```
Field           Description
-----           -----------
group_name      The name of the group
password        Encrypted password (! or * means no password)
administrators  Users who can manage group membership
members         Group members (mirrors /etc/group)
```

### Managing Groups

#### Creating Groups

```bash
# Create a new group
$ sudo groupadd developers

# Create group with specific GID
$ sudo groupadd -g 2000 contractors

# Create system group (lower GID)
$ sudo groupadd -r docker
```

#### Modifying Groups

```bash
# Add user to supplementary group
$ sudo usermod -aG developers alice

# Change group name
$ sudo groupmod -n newname oldname

# Change group GID
$ sudo groupmod -g 2001 developers
```

#### Deleting Groups

```bash
# Delete a group
$ sudo groupdel contractors

# Note: Cannot delete a user's primary group
$ sudo groupdel alices_primary
groupdel: cannot remove the primary group of user 'alice'
```

### Group Membership Commands

```bash
# View current user's groups
$ groups
alice developers sudo docker

# View another user's groups
$ groups bob
bob : bob developers webdev

# Detailed group information
$ id
uid=1001(alice) gid=1001(alice) groups=1001(alice),27(sudo),999(docker),1002(developers)

# View group members
$ getent group developers
developers:x:1001:alice,bob,charlie
```

### newgrp - Changing the Active Group

The `newgrp` command starts a new shell with a different primary group:

```bash
# Check current primary group
$ id -gn
alice

# Switch to different group
$ newgrp developers

# New files will now use 'developers' as group
$ touch test_file.txt
$ ls -l test_file.txt
-rw-r--r-- 1 alice developers 0 Jan 15 10:00 test_file.txt

# Exit the newgrp shell to return to original group
$ exit
```

### sg - Run Command with Different Group

The `sg` command runs a single command with a different group:

```bash
# Run command with different group
$ sg developers -c "touch /shared/project_file.txt"

# The file will have 'developers' as its group
```

---

## Process GID Concepts

Every process running on a Unix/Linux system has associated group identifiers that determine its access
rights. Understanding these GIDs is crucial for security and proper program behavior.

### The Four Process GIDs

A process in Linux has four distinct GID attributes:

```
+------------------+
|    Process       |
+------------------+
| Real GID (RGID)  |  Who started the process
| Effective GID    |  Used for permission checks
|   (EGID)         |
| Saved Set-GID    |  Preserved EGID for later use
|   (SSGID)        |
| File System GID  |  Used for file access (Linux-specific)
|   (FSGID)        |
+------------------+
```

### Real GID (RGID)

The Real GID identifies the actual group of the user who started the process. It doesn't change during process
execution (except by superuser).

#### Characteristics

- Set at login time to the user's primary group
- Inherited from parent process during fork()
- Used to determine who really owns the process
- Can only be changed by root

```c
/* Getting the Real GID */
#include <unistd.h>
#include <sys/types.h>

gid_t real_gid = getgid();
printf("Real GID: %d\n", real_gid);
```

```bash
# View from shell
$ id -gr
developers

$ id -g
1001
```

#### Real GID in Process Table

```bash
# View process GIDs with ps
$ ps -o pid,rgid,gid,sgid,cmd
PID  RGID   GID  SGID CMD
1234  1001  1001  1001 bash
1235  1001  1002  1002 sgid_program  # Note: GID differs from RGID
```

### Effective GID (EGID)

The Effective GID is the primary identifier used by the kernel when making permission decisions for group
access.

#### Role in Permission Checking

```
When process attempts to access a file:

1. Compare process EUID with file UID
2. If not owner, compare process EGID with file GID
3. If no match, check supplementary groups
4. If still no match, use "other" permissions
```

#### How EGID Changes

The EGID can differ from the RGID in several scenarios:

```bash
# 1. Running an SGID program
$ ls -l /usr/bin/write
-rwxr-sr-x 1 root tty 30800 /usr/bin/write
^
SGID bit set

# When alice (GID 1001) runs this:
# RGID = 1001 (alice's primary group)
# EGID = 5 (tty - the program's group)
```

```c
/* Setting EGID programmatically */
#include <unistd.h>

// Set effective GID (requires appropriate privileges)
if (setegid(1002) == -1) {
  perror("setegid failed");
}

// Get effective GID
gid_t egid = getegid();
```

#### EGID Use Cases

1. **SGID Programs**: Programs that need group-level access to shared resources
2. **Privilege Management**: Temporarily assuming group privileges
3. **Daemon Processes**: Services that need to run with specific group access

### Saved Set-Group-ID (SSGID)

The Saved Set-Group-ID preserves the EGID at the moment of exec(), allowing a program to toggle between
privileges.

#### Purpose and Functionality

```
At exec() of SGID program:
1. RGID stays the same (user's real group)
2. EGID becomes the program's group
3. SSGID copies the EGID value

This allows the program to:
- Drop privileges: Set EGID = RGID
- Restore privileges: Set EGID = SSGID
```

#### Privilege Manipulation Pattern

```c
#include <unistd.h>
#include <stdio.h>

int main() {
  gid_t rgid = getgid();    // Real GID
  gid_t egid = getegid();   // Effective GID (from SGID)

  printf("Initial: RGID=%d, EGID=%d\n", rgid, egid);

  // Do privileged operation with elevated EGID
  do_privileged_file_access();

  // Drop privileges temporarily
  if (setegid(rgid) == -1) {
    perror("Cannot drop privileges");
  }
  printf("Dropped: RGID=%d, EGID=%d\n", getgid(), getegid());

  // Do unprivileged work
  process_user_input();

  // Restore privileges (SGID was saved)
  if (setegid(egid) == -1) {
    perror("Cannot restore privileges");
  }
  printf("Restored: RGID=%d, EGID=%d\n", getgid(), getegid());

  // Do another privileged operation
  do_more_privileged_work();

  return 0;
}
```

### File System GID (FSGID)

The FSGID is a Linux-specific identifier used specifically for file system access checks. It's primarily used
by the NFS server.

#### Why FSGID Exists

The FSGID allows file system access to use a different GID than other permission checks:

```c
/*
 * Example: NFS server handling requests
 *
 * The NFS server might need to:
 * 1. Keep its EGID for signal handling (root)
 * 2. Access files as the client's group (FSGID)
 */

#include <sys/fsuid.h>

// Set FSGID for file operations
int old_fsgid = setfsgid(client_gid);

// File operations now use client_gid
write_file_for_client();

// Restore original FSGID
setfsgid(old_fsgid);
```

#### FSGID Behavior

- Usually tracks the EGID automatically
- Only changes independently when explicitly set
- Used only for file system permission checks
- Other operations still use EGID

```c
#include <sys/fsuid.h>
#include <stdio.h>

int main() {
  // FSGID typically equals EGID
  printf("EGID: %d\n", getegid());

  // Set different FSGID
  int old_fsgid = setfsgid(1002);
  printf("Old FSGID was: %d\n", old_fsgid);

  // Now file operations use GID 1002
  // But EGID is still the original value

  // Getting current FSGID (call setfsgid with -1)
  int current_fsgid = setfsgid(-1);
  printf("Current FSGID: %d\n", current_fsgid);

  return 0;
}
```

### Supplementary Group IDs

In addition to the four main GIDs, a process maintains a list of supplementary group IDs:

```c
#include <unistd.h>
#include <sys/types.h>
#include <grp.h>
#include <stdio.h>

int main() {
  gid_t groups[100];
  int ngroups;

  // Get number of supplementary groups
  ngroups = getgroups(100, groups);

  printf("Process has %d supplementary groups:\n", ngroups);
  for (int i = 0; i < ngroups; i++) {
    struct group *grp = getgrgid(groups[i]);
    printf("  GID %d (%s)\n", groups[i], grp ? grp->gr_name : "unknown");
  }

  return 0;
}
```

```bash
# View from command line
$ id
uid=1001(alice) gid=1001(developers) groups=1001(developers),27(sudo),44(video),999(docker)

# The 'groups' part shows supplementary groups
```

### GID System Calls Reference

Here's a comprehensive reference of GID-related system calls:

```c
#include <unistd.h>
#include <sys/types.h>

/* Getting GIDs */
gid_t getgid(void);           // Get real GID
gid_t getegid(void);          // Get effective GID

/* Setting GIDs - varying privilege requirements */
int setgid(gid_t gid);        // Set real and effective GID
int setegid(gid_t gid);       // Set effective GID only
int setregid(gid_t rgid, gid_t egid);  // Set real and effective
int setresgid(gid_t rgid, gid_t egid, gid_t sgid);  // Set all three

/* Getting all three */
int getresgid(gid_t *rgid, gid_t *egid, gid_t *sgid);

/* Supplementary groups */
int getgroups(int size, gid_t list[]);
int setgroups(size_t size, const gid_t *list);  // Requires CAP_SETGID

/* Linux-specific - File system GID */
#include <sys/fsuid.h>
int setfsgid(gid_t fsgid);    // Returns previous FSGID
```

### Permission Behavior Table

| Action                 | GID Used              | Notes                         |
| ---------------------- | --------------------- | ----------------------------- |
| File permission check  | EGID + supplementary  | Standard access control       |
| New file creation      | EGID (or parent SGID) | Depends on directory settings |
| Sending signals        | RGID for permission   | Kill, SIGTERM, etc.           |
| File system operations | FSGID (Linux)         | Usually equals EGID           |
| Dumpable attribute     | RGID/EGID mismatch    | Core dumps may be disabled    |

### Process GID Inheritance

Understanding how GIDs are inherited during fork() and exec():

```
fork():
- All GIDs (RGID, EGID, SSGID, FSGID) copied exactly
- Supplementary groups copied exactly
- Child is an exact copy of parent

exec() (non-SGID binary):
- RGID unchanged
- EGID unchanged
- SSGID set to EGID
- FSGID unchanged
- Supplementary groups unchanged

exec() (SGID binary):
- RGID unchanged
- EGID set to file's group
- SSGID set to file's group
- FSGID set to match EGID
- Supplementary groups unchanged
```

```c
/* Demonstrating inheritance */
#include <unistd.h>
#include <stdio.h>
#include <sys/wait.h>

void print_gids(const char *msg) {
  gid_t rgid, egid, sgid;
  getresgid(&rgid, &egid, &sgid);
  printf("%s: RGID=%d, EGID=%d, SSGID=%d\n", msg, rgid, egid, sgid);
}

int main() {
  print_gids("Parent before fork");

  pid_t pid = fork();
  if (pid == 0) {
    // Child process
    print_gids("Child after fork");

    // Execute a program
    execl("/path/to/program", "program", NULL);
    perror("exec failed");
    _exit(1);
  } else {
    wait(NULL);
    print_gids("Parent after child exits");
  }

  return 0;
}
```

---

## Permission Checking Mechanisms

The Linux kernel employs a sophisticated algorithm to determine whether a process can access a file.
Understanding this mechanism is essential for debugging access issues and designing secure systems.

### The Access Control Decision Flow

```
+-------------------+
| Process requests  |
| file access       |
+-------------------+
|
v
+-------------------+
| Is process root?  |----YES----> Special handling
| (EUID == 0)       |             (see below)
+-------------------+
| NO
v
+-------------------+
| Check owner match |
| EUID == file UID? |----YES----> Use OWNER permissions
+-------------------+              Check r/w/x against request
| NO                      Grant or deny
v
+-------------------+
| Check group match |
| EGID == file GID? |----YES----> Use GROUP permissions
| or supplementary  |             Check r/w/x against request
| group matches?    |             Grant or deny
+-------------------+
| NO
v
+-------------------+
| Use OTHER         |
| permissions       |
| Check r/w/x       |
+-------------------+
|
v
Grant or Deny
```

### Root (Superuser) Access

When a process has EUID 0 (root), special rules apply:

```
For READ and WRITE:
- Always permitted for all files

For EXECUTE:
- Permitted only if at least one execute bit is set
- This prevents accidentally running non-executable files as root

For directories:
- Always permitted (read, write, execute)
```

```bash
# Root can read any file
$ sudo cat /etc/shadow
root:$6$xyz...

# Root can write to any file
$ sudo sh -c 'echo "test" >> /root/protected_file'

# But root cannot execute a file with no execute bits
$ sudo /path/to/data_file
bash: /path/to/data_file: Permission denied

# Unless at least one execute bit is set
$ sudo chmod u+x /path/to/script
$ sudo /path/to/script
Script executed successfully
```

### The access() System Call

The `access()` system call checks permissions using the REAL UID/GID rather than effective:

```c
#include <unistd.h>
#include <stdio.h>

int main() {
  const char *file = "/some/file";

  // Check read access
  if (access(file, R_OK) == 0) {
    printf("File is readable\n");
  } else {
    perror("Read access denied");
  }

  // Check write access
  if (access(file, W_OK) == 0) {
    printf("File is writable\n");
  }

  // Check execute access
  if (access(file, X_OK) == 0) {
    printf("File is executable\n");
  }

  // Check if file exists
  if (access(file, F_OK) == 0) {
    printf("File exists\n");
  }

  // Check multiple permissions
  if (access(file, R_OK | W_OK) == 0) {
    printf("File is readable and writable\n");
  }

  return 0;
}
```

**Access Modes:**

| Mode | Value | Description              |
| ---- | ----- | ------------------------ |
| F_OK | 0     | Check file existence     |
| X_OK | 1     | Check execute permission |
| W_OK | 2     | Check write permission   |
| R_OK | 4     | Check read permission    |

### The faccessat() System Call

Extended version of access() with additional flags:

```c
#include <fcntl.h>
#include <unistd.h>

int result = faccessat(dirfd, pathname, mode, flags);

/* Flags:
 * AT_EACCESS - Use effective UID/GID instead of real
 * AT_SYMLINK_NOFOLLOW - Don't dereference symlinks
 */

// Example: Check using effective IDs
if (faccessat(AT_FDCWD, "/path/to/file", R_OK, AT_EACCESS) == 0) {
  printf("Effective user can read this file\n");
}
```

### Capability-Based Access Control

Modern Linux uses capabilities to provide fine-grained privilege control:

```bash
# View file capabilities
$ getcap /usr/bin/ping
/usr/bin/ping = cap_net_raw+ep

# Instead of SUID, ping uses CAP_NET_RAW capability
# This is more secure than full root privileges
```

**Relevant Capabilities for GID/Permissions:**

| Capability          | Description                                               |
| ------------------- | --------------------------------------------------------- |
| CAP_SETGID          | Allows manipulating process GIDs and supplementary groups |
| CAP_CHOWN           | Allows changing file owner and group                      |
| CAP_DAC_OVERRIDE    | Bypass read, write, execute permission checks             |
| CAP_DAC_READ_SEARCH | Bypass read and search permission checks                  |
| CAP_FOWNER          | Bypass permission checks for file owner operations        |

```c
/* Checking and using capabilities */
#include <sys/capability.h>

cap_t caps = cap_get_proc();
cap_flag_value_t value;

// Check if we have CAP_SETGID
cap_get_flag(caps, CAP_SETGID, CAP_EFFECTIVE, &value);
if (value == CAP_SET) {
  printf("Process has CAP_SETGID\n");
}

cap_free(caps);
```

---

## Practical Examples and Use Cases

This section provides real-world examples of file modes and GID management in various scenarios.

### Setting Up a Shared Project Directory

Create a directory where team members can collaborate:

```bash
#!/bin/bash
# setup_shared_project.sh

PROJECT_NAME="webapp"
TEAM_GROUP="developers"
BASE_DIR="/projects"

# Create the project directory
sudo mkdir -p "${BASE_DIR}/${PROJECT_NAME}"

# Set ownership
sudo chown root:${TEAM_GROUP} "${BASE_DIR}/${PROJECT_NAME}"

# Set permissions:
# - Owner (root): full access
# - Group (developers): read, write, execute
# - Others: no access
# - SGID: new files inherit group
sudo chmod 2770 "${BASE_DIR}/${PROJECT_NAME}"

# Create subdirectories with same permissions
for subdir in src docs tests config; do
  sudo mkdir "${BASE_DIR}/${PROJECT_NAME}/${subdir}"
  sudo chmod 2770 "${BASE_DIR}/${PROJECT_NAME}/${subdir}"
done

# Verify setup
ls -la "${BASE_DIR}/${PROJECT_NAME}"

echo "Project directory setup complete!"
echo "Add users to the '${TEAM_GROUP}' group with:"
echo "  sudo usermod -aG ${TEAM_GROUP} username"
```

### Creating a Secure Upload Directory

Set up a directory for file uploads with appropriate restrictions:

```bash
#!/bin/bash
# setup_upload_dir.sh

UPLOAD_DIR="/var/uploads"
WEB_USER="www-data"
WEB_GROUP="www-data"

# Create upload directory
sudo mkdir -p "${UPLOAD_DIR}"

# Set ownership to web server user
sudo chown ${WEB_USER}:${WEB_GROUP} "${UPLOAD_DIR}"

# Permissions:
# - Owner (www-data): full access
# - Group (www-data): read and execute
# - Others: no access
# - Sticky bit: prevent users from deleting others' files
sudo chmod 1750 "${UPLOAD_DIR}"

# Create temporary processing directory
sudo mkdir -p "${UPLOAD_DIR}/processing"
sudo chown ${WEB_USER}:${WEB_GROUP} "${UPLOAD_DIR}/processing"
sudo chmod 1770 "${UPLOAD_DIR}/processing"

echo "Upload directory setup complete!"
```

### Setting Up SSH Key Permissions

SSH requires strict permissions for security:

```bash
#!/bin/bash
# fix_ssh_permissions.sh

SSH_DIR="${HOME}/.ssh"

# Create .ssh directory if it doesn't exist
mkdir -p "${SSH_DIR}"

# Set directory permissions (owner only)
chmod 700 "${SSH_DIR}"

# Set permissions for various key files
if [ -f "${SSH_DIR}/id_rsa" ]; then
  chmod 600 "${SSH_DIR}/id_rsa"
fi

if [ -f "${SSH_DIR}/id_rsa.pub" ]; then
  chmod 644 "${SSH_DIR}/id_rsa.pub"
fi

if [ -f "${SSH_DIR}/id_ed25519" ]; then
  chmod 600 "${SSH_DIR}/id_ed25519"
fi

if [ -f "${SSH_DIR}/id_ed25519.pub" ]; then
  chmod 644 "${SSH_DIR}/id_ed25519.pub"
fi

if [ -f "${SSH_DIR}/authorized_keys" ]; then
  chmod 600 "${SSH_DIR}/authorized_keys"
fi

if [ -f "${SSH_DIR}/known_hosts" ]; then
  chmod 644 "${SSH_DIR}/known_hosts"
fi

if [ -f "${SSH_DIR}/config" ]; then
  chmod 600 "${SSH_DIR}/config"
fi

echo "SSH permissions configured correctly"
ls -la "${SSH_DIR}"
```

### Database Directory Security

Secure database directories for MySQL/PostgreSQL:

```bash
#!/bin/bash
# secure_database_dir.sh

# MySQL example
MYSQL_DATA="/var/lib/mysql"
MYSQL_USER="mysql"
MYSQL_GROUP="mysql"

sudo chown -R ${MYSQL_USER}:${MYSQL_GROUP} "${MYSQL_DATA}"
sudo chmod 750 "${MYSQL_DATA}"
sudo find "${MYSQL_DATA}" -type d -exec chmod 750 {} \;
sudo find "${MYSQL_DATA}" -type f -exec chmod 640 {} \;

# PostgreSQL example
PG_DATA="/var/lib/postgresql/14/main"
PG_USER="postgres"
PG_GROUP="postgres"

sudo chown -R ${PG_USER}:${PG_GROUP} "${PG_DATA}"
sudo chmod 700 "${PG_DATA}"
sudo find "${PG_DATA}" -type d -exec chmod 700 {} \;
sudo find "${PG_DATA}" -type f -exec chmod 600 {} \;

echo "Database directories secured"
```

### Web Application File Permissions

Comprehensive example for a web application:

```bash
#!/bin/bash
# secure_webapp.sh

WEB_ROOT="/var/www/myapp"
WEB_USER="www-data"
WEB_GROUP="www-data"
DEPLOY_GROUP="deployers"

# Set ownership: root owns, webdev group for deployment
sudo chown -R root:${DEPLOY_GROUP} "${WEB_ROOT}"

# Set directory permissions
sudo find "${WEB_ROOT}" -type d -exec chmod 2775 {} \;

# Set file permissions
sudo find "${WEB_ROOT}" -type f -exec chmod 664 {} \;

# Make scripts executable
sudo find "${WEB_ROOT}/bin" -type f -name "*.sh" -exec chmod 775 {} \;

# Special directories that web server needs to write to
for write_dir in cache logs uploads sessions; do
  if [ -d "${WEB_ROOT}/${write_dir}" ]; then
    sudo chown -R ${WEB_USER}:${WEB_GROUP} "${WEB_ROOT}/${write_dir}"
    sudo chmod 2770 "${WEB_ROOT}/${write_dir}"
  fi
done

# Protect configuration files
sudo chmod 640 "${WEB_ROOT}/config/"*.php
sudo chmod 640 "${WEB_ROOT}/.env"

# Protect sensitive directories
sudo chmod 750 "${WEB_ROOT}/config"
sudo chmod 700 "${WEB_ROOT}/private"

echo "Web application permissions configured"
```

### Log File Management

Setting up log file permissions:

```bash
#!/bin/bash
# setup_log_rotation.sh

LOG_DIR="/var/log/myapp"
APP_USER="myapp"
LOG_GROUP="adm"

# Create log directory
sudo mkdir -p "${LOG_DIR}"

# Set ownership (app can write, adm group can read)
sudo chown ${APP_USER}:${LOG_GROUP} "${LOG_DIR}"

# Directory permissions
sudo chmod 2750 "${LOG_DIR}"

# Create initial log files with correct permissions
for logfile in application.log error.log access.log; do
  sudo touch "${LOG_DIR}/${logfile}"
  sudo chown ${APP_USER}:${LOG_GROUP} "${LOG_DIR}/${logfile}"
  sudo chmod 640 "${LOG_DIR}/${logfile}"
done

# Logrotate configuration
cat << 'EOF' | sudo tee /etc/logrotate.d/myapp
/var/log/myapp/*.log {
daily
rotate 14
compress
delaycompress
missingok
notifempty
create 640 myapp adm
sharedscripts
postrotate
systemctl reload myapp 2>/dev/null || true
endscript
}
EOF

echo "Log configuration complete"
```

### SUID/SGID Program Example

Creating a program that uses elevated group privileges:

```c
/* group_accessor.c
 * A program that accesses files as a specific group
 * Compile: gcc -o group_accessor group_accessor.c
 * Install: sudo chgrp shared group_accessor && sudo chmod 2755 group_accessor
 */

#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
#include <sys/types.h>
#include <fcntl.h>
#include <string.h>
#include <errno.h>

#define SHARED_DIR "/shared/group_files"

void print_ids(const char *label) {
  printf("%s - UID: %d, GID: %d, EUID: %d, EGID: %d\n",
         label, getuid(), getgid(), geteuid(), getegid());
}

int main(int argc, char *argv[]) {
  gid_t real_gid = getgid();
  gid_t effective_gid = getegid();

  print_ids("Initial state");

  if (argc < 2) {
    fprintf(stderr, "Usage: %s <filename>\n", argv[0]);
    return 1;
  }

  // Build path to shared file
  char filepath[512];
  snprintf(filepath, sizeof(filepath), "%s/%s", SHARED_DIR, argv[1]);

  // Access file with elevated group privileges
  printf("Accessing: %s\n", filepath);

  int fd = open(filepath, O_RDONLY);
  if (fd == -1) {
    perror("Cannot open file");
    return 1;
  }

  // Read and display file contents
  char buffer[1024];
  ssize_t bytes_read;

  printf("--- File Contents ---\n");
  while ((bytes_read = read(fd, buffer, sizeof(buffer) - 1)) > 0) {
    buffer[bytes_read] = '\0';
    printf("%s", buffer);
  }
  printf("\n--- End of File ---\n");

  close(fd);

  // Drop privileges before doing anything else
  if (setegid(real_gid) == -1) {
    perror("Failed to drop privileges");
    return 1;
  }

  print_ids("After dropping privileges");

  return 0;
}
```

### Finding Files with Specific Permissions

Useful commands for auditing file permissions:

```bash
#!/bin/bash
# audit_permissions.sh

echo "=== SUID Files ==="
find / -perm -4000 -type f 2>/dev/null

echo ""
echo "=== SGID Files ==="
find / -perm -2000 -type f 2>/dev/null

echo ""
echo "=== World-Writable Files ==="
find / -perm -0002 -type f 2>/dev/null | head -50

echo ""
echo "=== World-Writable Directories without Sticky Bit ==="
find / -perm -0002 -type d ! -perm -1000 2>/dev/null

echo ""
echo "=== Files Not Owned by Any User ==="
find / -nouser 2>/dev/null

echo ""
echo "=== Files Not Owned by Any Group ==="
find / -nogroup 2>/dev/null

echo ""
echo "=== Files with Full Permissions (777) ==="
find / -perm 777 -type f 2>/dev/null | head -20

echo ""
echo "=== Recently Modified SUID/SGID Files (last 7 days) ==="
find / -type f \( -perm -4000 -o -perm -2000 \) -mtime -7 2>/dev/null
```

### Changing Group Ownership Recursively with Preservation

```bash
#!/bin/bash
# change_group_preserve.sh

TARGET_DIR="$1"
NEW_GROUP="$2"

if [ -z "$TARGET_DIR" ] || [ -z "$NEW_GROUP" ]; then
  echo "Usage: $0 <directory> <new_group>"
  exit 1
fi

# Verify directory exists
if [ ! -d "$TARGET_DIR" ]; then
  echo "Error: Directory does not exist"
  exit 1
fi

# Verify group exists
if ! getent group "$NEW_GROUP" > /dev/null; then
  echo "Error: Group does not exist"
  exit 1
fi

echo "Changing group ownership of ${TARGET_DIR} to ${NEW_GROUP}"

# Change group ownership
sudo chgrp -R "${NEW_GROUP}" "${TARGET_DIR}"

# Preserve SGID on directories
sudo find "${TARGET_DIR}" -type d -exec chmod g+s {} \;

# Report results
echo ""
echo "Group ownership changed. Directory structure:"
ls -laR "${TARGET_DIR}" | head -50

echo ""
echo "SGID directories:"
find "${TARGET_DIR}" -type d -perm -2000 -exec ls -ld {} \;
```

---

## Security Implications

Understanding the security implications of file modes and GIDs is crucial for system hardening and
vulnerability prevention.

### Common Permission Vulnerabilities

#### World-Writable Files and Directories

```bash
# Dangerous: World-writable configuration file
$ ls -l /etc/myapp/config.ini
-rw-rw-rw- 1 root root 1024 /etc/myapp/config.ini

# An attacker could modify this file:
$ echo "admin_password=hacked" >> /etc/myapp/config.ini

# Fix: Restrict permissions
$ sudo chmod 644 /etc/myapp/config.ini
# Or even more restrictive:
$ sudo chmod 640 /etc/myapp/config.ini
```

#### SUID/SGID Vulnerabilities

Poorly written SUID/SGID programs are prime targets for privilege escalation:

```bash
# Find SUID programs that might be exploitable
$ find / -perm -4000 -type f 2>/dev/null | xargs ls -la

# Common attack vectors:
# 1. Buffer overflows in SUID programs
# 2. PATH manipulation
# 3. Library injection (LD_PRELOAD - usually blocked for SUID)
# 4. Race conditions
# 5. Symbolic link attacks
```

#### Insecure Directory Permissions

```bash
# Problem: /tmp without sticky bit
$ ls -ld /tmp
drwxrwxrwx 10 root root 4096 /tmp  # Missing 't' at end!

# Any user can delete any file in /tmp
# This enables symlink attacks and file manipulation

# Fix:
$ sudo chmod +t /tmp
$ ls -ld /tmp
drwxrwxrwt 10 root root 4096 /tmp  # Sticky bit now set
```

### Privilege Escalation Prevention

#### Secure Program Design

```c
/* secure_program.c - Demonstrates secure privilege handling */

#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
#include <sys/types.h>
#include <string.h>
#include <errno.h>

/* Global variables for saved IDs */
static uid_t saved_uid;
static gid_t saved_gid;

void save_privileges(void) {
  saved_uid = geteuid();
  saved_gid = getegid();
}

int drop_privileges_permanently(void) {
  gid_t real_gid = getgid();
  uid_t real_uid = getuid();

  /* Drop supplementary groups first */
  if (setgroups(1, &real_gid) == -1) {
    perror("setgroups");
    return -1;
  }

  /* Drop GID */
  if (setresgid(real_gid, real_gid, real_gid) == -1) {
    perror("setresgid");
    return -1;
  }

  /* Drop UID */
  if (setresuid(real_uid, real_uid, real_uid) == -1) {
    perror("setresuid");
    return -1;
  }

  /* Verify privileges were dropped */
  if (geteuid() != real_uid || getegid() != real_gid) {
    fprintf(stderr, "Failed to drop privileges\n");
    return -1;
  }

  return 0;
}

int drop_privileges_temporarily(void) {
  gid_t real_gid = getgid();
  uid_t real_uid = getuid();

  /* Drop effective IDs only, keep saved IDs */
  if (setegid(real_gid) == -1) {
    perror("setegid");
    return -1;
  }

  if (seteuid(real_uid) == -1) {
    perror("seteuid");
    return -1;
  }

  return 0;
}

int restore_privileges(void) {
  if (seteuid(saved_uid) == -1) {
    perror("seteuid");
    return -1;
  }

  if (setegid(saved_gid) == -1) {
    perror("setegid");
    return -1;
  }

  return 0;
}

int main(int argc, char *argv[]) {
  /* Save original privileges immediately */
  save_privileges();

  printf("Starting with EUID=%d, EGID=%d\n", geteuid(), getegid());

  /* Do privileged operation (e.g., open a protected file) */
  FILE *fp = fopen("/etc/shadow", "r");
  if (fp) {
    printf("Opened protected file successfully\n");
    fclose(fp);
  }

  /* Drop privileges for user interaction */
  if (drop_privileges_temporarily() == -1) {
    exit(EXIT_FAILURE);
  }

  printf("After drop: EUID=%d, EGID=%d\n", geteuid(), getegid());

  /* Handle user input safely with dropped privileges */
  char input[256];
  printf("Enter command: ");
  if (fgets(input, sizeof(input), stdin) != NULL) {
    printf("You entered: %s", input);
  }

  /* Drop privileges permanently before exiting */
  if (drop_privileges_permanently() == -1) {
    exit(EXIT_FAILURE);
  }

  printf("Final state: EUID=%d, EGID=%d\n", geteuid(), getegid());

  return 0;
}
```

### Security Hardening Checklist

```bash
#!/bin/bash
# security_audit.sh - Comprehensive permission security audit

echo "========================================"
echo "Permission Security Audit"
echo "========================================"
echo ""

# Check 1: World-writable files
echo "[CHECK 1] World-writable files in sensitive directories:"
find /etc /usr /bin /sbin -perm -0002 -type f 2>/dev/null
echo ""

# Check 2: SUID binaries
echo "[CHECK 2] SUID binaries (review for necessity):"
find / -perm -4000 -type f 2>/dev/null | wc -l
echo "SUID files found. Full list:"
find / -perm -4000 -type f 2>/dev/null
echo ""

# Check 3: SGID binaries
echo "[CHECK 3] SGID binaries:"
find / -perm -2000 -type f 2>/dev/null | wc -l
echo ""

# Check 4: Orphaned files
echo "[CHECK 4] Files without valid owner/group:"
find / -nouser -o -nogroup 2>/dev/null | head -20
echo ""

# Check 5: Critical file permissions
echo "[CHECK 5] Critical file permission check:"

check_perms() {
  file=$1
  expected=$2
  actual=$(stat -c %a "$file" 2>/dev/null)
  if [ "$actual" != "$expected" ]; then
    echo "  WARNING: $file has $actual, expected $expected"
  else
    echo "  OK: $file = $actual"
  fi
}

check_perms /etc/passwd 644
check_perms /etc/shadow 640
check_perms /etc/group 644
check_perms /etc/gshadow 640
check_perms /etc/sudoers 440
echo ""

# Check 6: Home directory permissions
echo "[CHECK 6] Home directory permissions:"
for home in /home/*; do
  if [ -d "$home" ]; then
    perms=$(stat -c %a "$home")
    if [ "$perms" != "700" ] && [ "$perms" != "750" ]; then
      echo "  WARNING: $home has permissions $perms"
    fi
  fi
done
echo ""

# Check 7: SSH key permissions
echo "[CHECK 7] SSH key file permissions:"
for keyfile in /home/*/.ssh/id_rsa /home/*/.ssh/id_ed25519 /root/.ssh/id_rsa; do
  if [ -f "$keyfile" ]; then
    perms=$(stat -c %a "$keyfile")
    if [ "$perms" != "600" ]; then
      echo "  WARNING: $keyfile has $perms, should be 600"
    fi
  fi
done
echo ""

# Check 8: Sticky bit on shared directories
echo "[CHECK 8] World-writable directories without sticky bit:"
find / -type d -perm -0002 ! -perm -1000 2>/dev/null | grep -v "^/proc\|^/sys"
echo ""

echo "========================================"
echo "Audit Complete"
echo "========================================"
```

### Umask Configuration

The umask determines default permissions for new files:

```bash
# View current umask
$ umask
0022

# Octal value interpretation:
# Files: 666 - 022 = 644 (rw-r--r--)
# Directories: 777 - 022 = 755 (rwxr-xr-x)

# More restrictive umask
$ umask 077
# Files: 666 - 077 = 600 (rw-------)
# Directories: 777 - 077 = 700 (rwx------)

# Set umask in shell profile
echo "umask 027" >> ~/.bashrc
# Files: 666 - 027 = 640 (rw-r-----)
# Directories: 777 - 027 = 750 (rwxr-x---)
```

**System-wide umask configuration:**

```bash
# /etc/login.defs
UMASK 027

# /etc/profile or /etc/profile.d/umask.sh
umask 027

# PAM configuration (/etc/pam.d/common-session)
session optional pam_umask.so umask=027
```

---

## System Calls and APIs

This section provides a comprehensive reference for the system calls and library functions related to file
modes and GID management.

### File Permission System Calls

#### chmod() and fchmod()

```c
#include <sys/stat.h>

/* Change permissions of a file by path */
int chmod(const char *pathname, mode_t mode);

/* Change permissions of an open file */
int fchmod(int fd, mode_t mode);

/* Change permissions relative to directory fd */
int fchmodat(int dirfd, const char *pathname, mode_t mode, int flags);
```

**Example Usage:**

```c
#include <sys/stat.h>
#include <stdio.h>
#include <fcntl.h>

int main() {
  /* Set file to rw-r----- */
  if (chmod("/path/to/file", S_IRUSR | S_IWUSR | S_IRGRP) == -1) {
    perror("chmod failed");
    return 1;
  }

  /* Or using octal notation */
  if (chmod("/path/to/file", 0640) == -1) {
    perror("chmod failed");
    return 1;
  }

  /* Using fchmod on open file */
  int fd = open("/path/to/file", O_RDONLY);
  if (fd != -1) {
    fchmod(fd, 0644);
    close(fd);
  }

  /* Using fchmodat with AT_SYMLINK_NOFOLLOW */
  fchmodat(AT_FDCWD, "/path/to/symlink", 0644, AT_SYMLINK_NOFOLLOW);

  return 0;
}
```

#### Mode Constants

```c
/* Permission bits */
S_ISUID     04000   /* Set-user-ID bit */
S_ISGID     02000   /* Set-group-ID bit */
S_ISVTX     01000   /* Sticky bit */

S_IRWXU     00700   /* Owner: read, write, execute */
S_IRUSR     00400   /* Owner: read */
S_IWUSR     00200   /* Owner: write */
S_IXUSR     00100   /* Owner: execute */

S_IRWXG     00070   /* Group: read, write, execute */
S_IRGRP     00040   /* Group: read */
S_IWGRP     00020   /* Group: write */
S_IXGRP     00010   /* Group: execute */

S_IRWXO     00007   /* Others: read, write, execute */
S_IROTH     00004   /* Others: read */
S_IWOTH     00002   /* Others: write */
S_IXOTH     00001   /* Others: execute */
```

#### chown(), fchown(), lchown()

```c
#include <unistd.h>

/* Change owner and group of a file */
int chown(const char *pathname, uid_t owner, gid_t group);

/* Change owner and group of an open file */
int fchown(int fd, uid_t owner, gid_t group);

/* Change owner and group of a symbolic link */
int lchown(const char *pathname, uid_t owner, gid_t group);

/* Change owner and group relative to directory fd */
int fchownat(int dirfd, const char *pathname, uid_t owner, gid_t group, int flags);
```

**Example Usage:**

```c
#include <unistd.h>
#include <sys/types.h>
#include <stdio.h>
#include <fcntl.h>
#include <grp.h>
#include <pwd.h>

int main() {
  /* Change to specific UID and GID */
  if (chown("/path/to/file", 1000, 1000) == -1) {
    perror("chown failed");
    return 1;
  }

  /* Change only the group (-1 leaves owner unchanged) */
  if (chown("/path/to/file", -1, 1001) == -1) {
    perror("chown (group only) failed");
    return 1;
  }

  /* Look up UID/GID by name */
  struct passwd *pw = getpwnam("alice");
  struct group *gr = getgrnam("developers");

  if (pw && gr) {
    chown("/path/to/file", pw->pw_uid, gr->gr_gid);
  }

  /* fchown on open file */
  int fd = open("/path/to/file", O_RDONLY);
  if (fd != -1) {
    fchown(fd, 1000, 1000);
    close(fd);
  }

  /* lchown for symbolic links (doesn't follow link) */
  lchown("/path/to/symlink", 1000, 1000);

  return 0;
}
```

### GID System Calls

#### Getting GIDs

```c
#include <unistd.h>
#include <sys/types.h>

/* Get real group ID */
gid_t getgid(void);

/* Get effective group ID */
gid_t getegid(void);

/* Get real, effective, and saved set-group-ID */
int getresgid(gid_t *rgid, gid_t *egid, gid_t *sgid);

/* Get list of supplementary group IDs */
int getgroups(int size, gid_t list[]);
```

**Example:**

```c
#include <unistd.h>
#include <sys/types.h>
#include <stdio.h>
#include <grp.h>
#include <stdlib.h>

void print_all_gids(void) {
  gid_t rgid, egid, sgid;

  /* Get the three main GIDs */
  if (getresgid(&rgid, &egid, &sgid) == 0) {
    printf("Real GID:    %d\n", rgid);
    printf("Effective GID: %d\n", egid);
    printf("Saved GID:   %d\n", sgid);
  }

  /* Get supplementary groups */
  int ngroups = getgroups(0, NULL);  /* Get count first */
  if (ngroups > 0) {
    gid_t *groups = malloc(ngroups * sizeof(gid_t));
    if (groups) {
      getgroups(ngroups, groups);
      printf("Supplementary groups:\n");
      for (int i = 0; i < ngroups; i++) {
        struct group *grp = getgrgid(groups[i]);
        printf("  %d (%s)\n", groups[i],
               grp ? grp->gr_name : "unknown");
      }
      free(groups);
    }
  }
}

int main() {
  print_all_gids();
  return 0;
}
```

#### Setting GIDs

```c
#include <unistd.h>
#include <sys/types.h>

/* Set effective group ID */
int setgid(gid_t gid);

/* Set effective group ID */
int setegid(gid_t egid);

/* Set real and effective group IDs */
int setregid(gid_t rgid, gid_t egid);

/* Set real, effective, and saved group IDs */
int setresgid(gid_t rgid, gid_t egid, gid_t sgid);

/* Set supplementary group IDs (requires CAP_SETGID) */
int setgroups(size_t size, const gid_t *list);

/* Initialize supplementary groups for user */
int initgroups(const char *user, gid_t group);
```

**Example:**

```c
#include <unistd.h>
#include <sys/types.h>
#include <grp.h>
#include <stdio.h>
#include <stdlib.h>
#include <errno.h>

int switch_to_user_group(const char *username, gid_t gid) {
  /* Initialize supplementary groups for the user */
  if (initgroups(username, gid) == -1) {
    perror("initgroups failed");
    return -1;
  }

  /* Set the GID */
  if (setgid(gid) == -1) {
    perror("setgid failed");
    return -1;
  }

  return 0;
}

int drop_group_privileges(void) {
  gid_t real_gid = getgid();

  /* Set all GIDs to the real GID */
  if (setresgid(real_gid, real_gid, real_gid) == -1) {
    perror("setresgid failed");
    return -1;
  }

  /* Clear supplementary groups */
  if (setgroups(1, &real_gid) == -1) {
    perror("setgroups failed");
    return -1;
  }

  return 0;
}

int main() {
  printf("Before: EGID = %d\n", getegid());

  /* Example: temporarily change to another group */
  if (setegid(1002) == 0) {
    printf("Changed EGID to 1002\n");
  }

  /* Drop all group privileges */
  if (drop_group_privileges() == 0) {
    printf("Dropped group privileges\n");
  }

  printf("After: EGID = %d\n", getegid());

  return 0;
}
```

### File System GID (Linux-Specific)

```c
#include <sys/fsuid.h>

/* Set file system group ID */
int setfsgid(gid_t fsgid);

/* Returns the previous FSGID on success */
```

**Example:**

```c
#include <sys/fsuid.h>
#include <stdio.h>
#include <unistd.h>
#include <fcntl.h>

int access_file_as_group(const char *path, gid_t gid) {
  /* Save current FSGID */
  gid_t old_fsgid = setfsgid(gid);

  printf("Changed FSGID from %d to %d\n", old_fsgid, gid);

  /* Now file operations will use the new GID */
  int fd = open(path, O_RDONLY);
  if (fd == -1) {
    perror("open failed");
  } else {
    printf("File opened successfully\n");
    close(fd);
  }

  /* Restore original FSGID */
  setfsgid(old_fsgid);

  return 0;
}
```

### stat() and File Information

```c
#include <sys/stat.h>
#include <unistd.h>

/* Get file status */
int stat(const char *pathname, struct stat *statbuf);
int fstat(int fd, struct stat *statbuf);
int lstat(const char *pathname, struct stat *statbuf);
int fstatat(int dirfd, const char *pathname, struct stat *statbuf, int flags);

/* The stat structure */
struct stat {
  dev_t     st_dev;      /* Device ID */
  ino_t     st_ino;      /* Inode number */
  mode_t    st_mode;     /* File mode (permissions + type) */
  nlink_t   st_nlink;    /* Number of hard links */
  uid_t     st_uid;      /* User ID of owner */
  gid_t     st_gid;      /* Group ID of owner */
  dev_t     st_rdev;     /* Device ID (if special file) */
  off_t     st_size;     /* Total size in bytes */
  blksize_t st_blksize;  /* Block size for filesystem I/O */
  blkcnt_t  st_blocks;   /* Number of 512B blocks allocated */
  time_t    st_atime;    /* Time of last access */
  time_t    st_mtime;    /* Time of last modification */
  time_t    st_ctime;    /* Time of last status change */
};
```

**Example:**

```c
#include <sys/stat.h>
#include <stdio.h>
#include <pwd.h>
#include <grp.h>
#include <time.h>

void print_file_info(const char *path) {
  struct stat sb;

  if (stat(path, &sb) == -1) {
    perror("stat");
    return;
  }

  /* File type */
  printf("File type: ");
  switch (sb.st_mode & S_IFMT) {
    case S_IFREG:  printf("regular file\n"); break;
    case S_IFDIR:  printf("directory\n"); break;
    case S_IFLNK:  printf("symbolic link\n"); break;
    case S_IFBLK:  printf("block device\n"); break;
    case S_IFCHR:  printf("character device\n"); break;
    case S_IFIFO:  printf("FIFO/pipe\n"); break;
    case S_IFSOCK: printf("socket\n"); break;
    default:       printf("unknown\n"); break;
  }

  /* Permissions */
  printf("Permissions: %o\n", sb.st_mode & 07777);

  /* Owner and group */
  struct passwd *pw = getpwuid(sb.st_uid);
  struct group *gr = getgrgid(sb.st_gid);
  printf("Owner: %s (UID %d)\n", pw ? pw->pw_name : "unknown", sb.st_uid);
  printf("Group: %s (GID %d)\n", gr ? gr->gr_name : "unknown", sb.st_gid);

  /* Size */
  printf("Size: %ld bytes\n", (long)sb.st_size);

  /* Timestamps */
  printf("Last access: %s", ctime(&sb.st_atime));
  printf("Last modify: %s", ctime(&sb.st_mtime));
  printf("Last change: %s", ctime(&sb.st_ctime));

  /* Special bits */
  if (sb.st_mode & S_ISUID) printf("SUID bit set\n");
  if (sb.st_mode & S_ISGID) printf("SGID bit set\n");
  if (sb.st_mode & S_ISVTX) printf("Sticky bit set\n");
}

int main(int argc, char *argv[]) {
  if (argc < 2) {
    printf("Usage: %s <file>\n", argv[0]);
    return 1;
  }

  print_file_info(argv[1]);
  return 0;
}
```

### Permission Macros

```c
#include <sys/stat.h>

/* File type test macros */
S_ISREG(m)   /* Is it a regular file? */
S_ISDIR(m)   /* Is it a directory? */
S_ISCHR(m)   /* Is it a character device? */
S_ISBLK(m)   /* Is it a block device? */
S_ISFIFO(m)  /* Is it a FIFO (named pipe)? */
S_ISLNK(m)   /* Is it a symbolic link? */
S_ISSOCK(m)  /* Is it a socket? */

/* Example usage */
struct stat sb;
stat("/path/to/file", &sb);

if (S_ISREG(sb.st_mode)) {
  printf("Regular file\n");
}

if (S_ISDIR(sb.st_mode)) {
  printf("Directory\n");
}

/* Check specific permissions */
if (sb.st_mode & S_IRUSR) {
  printf("Owner can read\n");
}

if (sb.st_mode & S_IWGRP) {
  printf("Group can write\n");
}

if (sb.st_mode & S_IXOTH) {
  printf("Others can execute\n");
}
```

### Group Database Functions

```c
#include <grp.h>

/* Get group entry by name */
struct group *getgrnam(const char *name);

/* Get group entry by GID */
struct group *getgrgid(gid_t gid);

/* The group structure */
struct group {
  char   *gr_name;    /* Group name */
  char   *gr_passwd;  /* Group password */
  gid_t   gr_gid;     /* Group ID */
  char  **gr_mem;     /* NULL-terminated array of member names */
};

/* Thread-safe versions */
int getgrnam_r(const char *name, struct group *grp,
               char *buf, size_t buflen, struct group **result);
int getgrgid_r(gid_t gid, struct group *grp,
               char *buf, size_t buflen, struct group **result);

/* Iterate through group database */
struct group *getgrent(void);
void setgrent(void);
void endgrent(void);
```

**Example:**

```c
#include <grp.h>
#include <stdio.h>
#include <string.h>
#include <stdlib.h>

void print_group_info(const char *name) {
  struct group *grp = getgrnam(name);

  if (!grp) {
    printf("Group '%s' not found\n", name);
    return;
  }

  printf("Group name: %s\n", grp->gr_name);
  printf("GID: %d\n", grp->gr_gid);
  printf("Members:\n");

  for (char **member = grp->gr_mem; *member != NULL; member++) {
    printf("  - %s\n", *member);
  }
}

void print_all_groups(void) {
  struct group *grp;

  setgrent();  /* Rewind to beginning */

  while ((grp = getgrent()) != NULL) {
    printf("%s:%d\n", grp->gr_name, grp->gr_gid);
  }

  endgrent();  /* Close the database */
}

/* Thread-safe version */
int get_group_gid_safe(const char *name, gid_t *gid) {
  struct group grp;
  struct group *result;
  char buf[4096];

  if (getgrnam_r(name, &grp, buf, sizeof(buf), &result) != 0 || !result) {
    return -1;
  }

  *gid = result->gr_gid;
  return 0;
}

int main() {
  print_group_info("developers");
  printf("\nAll groups:\n");
  print_all_groups();
  return 0;
}
```

---

## Best Practices

This section outlines recommended practices for managing file modes and GIDs in production environments.

### Principle of Least Privilege

Always assign the minimum permissions necessary:

```bash
# Bad: Overly permissive
chmod 777 /var/www/html

# Good: Minimal permissions
chmod 755 /var/www/html        # Directories
chmod 644 /var/www/html/*.html # Static files
chmod 640 /var/www/html/*.php  # PHP files (no world read)

# Application configuration files
chmod 600 /etc/myapp/secrets.conf  # Only owner
chmod 640 /etc/myapp/config.conf   # Owner + group
```

### Group Organization Strategy

```bash
# Create functional groups
sudo groupadd webdev      # Web development team
sudo groupadd dbadmin     # Database administrators
sudo groupadd operations  # Operations/DevOps team
sudo groupadd security    # Security team

# Create resource-based groups
sudo groupadd www-data    # Web server processes
sudo groupadd mysql       # Database processes
sudo groupadd docker      # Docker access

# Add users to appropriate groups
sudo usermod -aG webdev,docker alice    # Developer with Docker access
sudo usermod -aG dbadmin,security bob   # DBA with security access
```

### Directory Structure Permissions

```bash
#!/bin/bash
# Standard permission template for projects

PROJECT="/opt/myproject"

# Root directory - restrictive
chown root:projectteam "$PROJECT"
chmod 2750 "$PROJECT"

# Source code - team can read/write
chown -R root:projectteam "$PROJECT/src"
find "$PROJECT/src" -type d -exec chmod 2775 {} \;
find "$PROJECT/src" -type f -exec chmod 664 {} \;

# Configuration - restricted
chown -R root:projectteam "$PROJECT/config"
find "$PROJECT/config" -type d -exec chmod 2750 {} \;
find "$PROJECT/config" -type f -exec chmod 640 {} \;

# Secrets - highly restricted
chown -R root:projectteam "$PROJECT/secrets"
chmod 2700 "$PROJECT/secrets"
find "$PROJECT/secrets" -type f -exec chmod 600 {} \;

# Logs - app can write, group can read
chown -R appuser:projectteam "$PROJECT/logs"
find "$PROJECT/logs" -type d -exec chmod 2750 {} \;
find "$PROJECT/logs" -type f -exec chmod 640 {} \;

# Temporary files - restricted
chown appuser:appuser "$PROJECT/tmp"
chmod 1700 "$PROJECT/tmp"
```

### Automation and Configuration Management

Use configuration management tools to enforce permissions:

```yaml
# Ansible example
- name: Set application directory permissions
  file:
    path: /opt/myapp
    state: directory
    owner: root
    group: appgroup
    mode: "2755"

- name: Set configuration file permissions
  file:
    path: /etc/myapp/config.yml
    owner: root
    group: appgroup
    mode: "0640"

- name: Recursively set source permissions
  file:
    path: /opt/myapp/src
    state: directory
    recurse: yes
    owner: root
    group: devgroup
    mode: u=rwX,g=rwX,o=
```

```ruby
# Chef example
directory '/opt/myapp' do
owner 'root'
group 'appgroup'
mode '2755'
action :create
end

file '/etc/myapp/config.yml' do
owner 'root'
group 'appgroup'
mode '0640'
action :create
end
```

### Regular Auditing

```bash
#!/bin/bash
# weekly_permission_audit.sh

AUDIT_LOG="/var/log/permission_audit.log"
ALERT_EMAIL="security@company.com"

echo "Permission Audit - $(date)" >> "$AUDIT_LOG"

# Check for new SUID/SGID files
echo "=== New SUID/SGID Files ===" >> "$AUDIT_LOG"
find / -perm /6000 -type f -mtime -7 2>/dev/null >> "$AUDIT_LOG"

# Check for world-writable files in sensitive locations
echo "=== World-Writable Files ===" >> "$AUDIT_LOG"
find /etc /usr /bin /sbin -perm -0002 -type f 2>/dev/null >> "$AUDIT_LOG"

# Check home directory permissions
echo "=== Insecure Home Directories ===" >> "$AUDIT_LOG"
find /home -maxdepth 1 -type d -perm /g+w,o+w 2>/dev/null >> "$AUDIT_LOG"

# Check for permission changes on critical files
echo "=== Critical File Permission Changes ===" >> "$AUDIT_LOG"
for file in /etc/passwd /etc/shadow /etc/sudoers; do
  current=$(stat -c %a "$file")
  echo "$file: $current" >> "$AUDIT_LOG"
done

# Send alert if issues found
if grep -q "ALERT" "$AUDIT_LOG"; then
  mail -s "Permission Audit Alert" "$ALERT_EMAIL" < "$AUDIT_LOG"
fi
```

---

## Troubleshooting

This section covers common permission-related problems and their solutions.

### Common Error Messages

#### "Permission denied"

```bash
# Scenario 1: No execute permission on parent directory
$ cat /opt/restricted/file.txt
cat: /opt/restricted/file.txt: Permission denied

# Diagnosis
$ ls -ld /opt/restricted
drw-r--r-- 2 root root 4096 Jan 15 10:00 /opt/restricted
# Missing 'x' for directory traversal

# Fix
$ sudo chmod +x /opt/restricted

# Scenario 2: No read permission on file
$ cat /etc/shadow
cat: /etc/shadow: Permission denied

$ ls -l /etc/shadow
-rw-r----- 1 root shadow 1234 Jan 15 10:00 /etc/shadow
# Need to be in 'shadow' group or be root

# Scenario 3: SELinux/AppArmor blocking access
$ cat /var/www/html/index.html
cat: /var/www/html/index.html: Permission denied

# Check for security denials
$ sudo ausearch -m AVC -ts recent
# or
$ sudo dmesg | grep -i denied
```

#### "Operation not permitted"

```bash
# Often indicates capability or immutable attribute issue
$ chown user /some/file
chown: changing ownership of '/some/file': Operation not permitted

# Check immutable attribute
$ lsattr /some/file
----i----------- /some/file

# Remove immutable attribute (requires root)
$ sudo chattr -i /some/file
$ chown user /some/file  # Now works
```

### Debugging Permission Issues

```bash
#!/bin/bash
# debug_permissions.sh

FILE="$1"
USER="${2:-$(whoami)}"

if [ -z "$FILE" ]; then
  echo "Usage: $0 <file> [user]"
  exit 1
fi

echo "=== Debugging permissions for: $FILE ==="
echo "Checking access for user: $USER"
echo ""

# Check if file exists
if [ ! -e "$FILE" ]; then
  echo "ERROR: File does not exist"
  exit 1
fi

# File information
echo "--- File Information ---"
ls -la "$FILE"
stat "$FILE"
echo ""

# Check each directory in path
echo "--- Path Components ---"
path="$FILE"
while [ "$path" != "/" ]; do
  path=$(dirname "$path")
  echo -n "$path: "
  ls -ld "$path" 2>&1
done
echo ""

# Check user information
echo "--- User Information ---"
id "$USER"
echo ""

# Check effective access
echo "--- Access Check ---"
if sudo -u "$USER" test -r "$FILE" 2>/dev/null; then
  echo "Read: YES"
else
  echo "Read: NO"
fi

if sudo -u "$USER" test -w "$FILE" 2>/dev/null; then
  echo "Write: YES"
else
  echo "Write: NO"
fi

if sudo -u "$USER" test -x "$FILE" 2>/dev/null; then
  echo "Execute: YES"
else
  echo "Execute: NO"
fi
echo ""

# Check for ACLs
echo "--- Access Control Lists ---"
getfacl "$FILE" 2>/dev/null || echo "ACLs not available"
echo ""

# Check for SELinux context
echo "--- SELinux Context ---"
ls -Z "$FILE" 2>/dev/null || echo "SELinux not available"
echo ""

# Check for file attributes
echo "--- Extended Attributes ---"
lsattr "$FILE" 2>/dev/null || echo "Extended attributes not available"
```

### Fixing Common Issues

#### SSH Key Permission Issues

```bash
# SSH complains about permissions
$ ssh user@host
@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
@         WARNING: UNPROTECTED PRIVATE KEY FILE!          @
@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
Permissions 0644 for '/home/user/.ssh/id_rsa' are too open.

# Fix all SSH permissions
chmod 700 ~/.ssh
chmod 600 ~/.ssh/id_rsa
chmod 600 ~/.ssh/id_ed25519
chmod 644 ~/.ssh/id_rsa.pub
chmod 644 ~/.ssh/id_ed25519.pub
chmod 600 ~/.ssh/authorized_keys
chmod 600 ~/.ssh/config
chmod 644 ~/.ssh/known_hosts
```

#### Web Server Permission Issues

```bash
# Apache/Nginx cannot read files
# Check web server user
$ ps aux | grep -E '(apache|nginx|httpd)'
www-data  1234  0.0  0.5  ...  nginx: worker process

# Fix web content permissions
sudo chown -R root:www-data /var/www/html
sudo find /var/www/html -type d -exec chmod 755 {} \;
sudo find /var/www/html -type f -exec chmod 644 {} \;

# For upload directories
sudo chown www-data:www-data /var/www/html/uploads
sudo chmod 755 /var/www/html/uploads
```

#### Database Permission Issues

```bash
# MySQL cannot read data directory
# Check MySQL user
$ ps aux | grep mysql
mysql     1234  0.5  5.0  ...  /usr/sbin/mysqld

# Fix data directory
sudo chown -R mysql:mysql /var/lib/mysql
sudo chmod 750 /var/lib/mysql
sudo find /var/lib/mysql -type d -exec chmod 750 {} \;
sudo find /var/lib/mysql -type f -exec chmod 640 {} \;
```

### Using strace to Debug Permissions

```bash
# Trace system calls to find permission issues
$ strace -f -e trace=open,openat,access cat /path/to/file 2>&1

# Example output
openat(AT_FDCWD, "/path/to/file", O_RDONLY) = -1 EACCES (Permission denied)
# Shows exactly which call failed

# For more detailed output
$ strace -f -e trace=file cat /path/to/file 2>&1
```

### Process Credential Debugging

```bash
#!/bin/bash
# show_process_creds.sh - Show credentials for a process

PID="$1"

if [ -z "$PID" ]; then
  echo "Usage: $0 <pid>"
  exit 1
fi

if [ ! -d "/proc/$PID" ]; then
  echo "Process $PID not found"
  exit 1
fi

echo "=== Process $PID Credentials ==="

# Get UIDs
echo "UIDs (Real, Effective, Saved, FS):"
cat /proc/$PID/status | grep -E '^Uid:'

# Get GIDs
echo "GIDs (Real, Effective, Saved, FS):"
cat /proc/$PID/status | grep -E '^Gid:'

# Get supplementary groups
echo "Supplementary Groups:"
cat /proc/$PID/status | grep -E '^Groups:'

# Get capabilities
echo "Capabilities:"
cat /proc/$PID/status | grep -E '^Cap'

# Get command
echo "Command:"
cat /proc/$PID/cmdline | tr '\0' ' '
echo ""
```

---

## Advanced Topics

### Access Control Lists (ACLs)

ACLs extend the traditional permission model to allow fine-grained access control:

```bash
# View ACLs
$ getfacl /path/to/file
# file: path/to/file
# owner: alice
# group: developers
user::rw-
user:bob:r--
group::r--
group:qa:rw-
mask::rw-
other::---

# Set ACLs
# Give specific user read access
$ setfacl -m u:bob:r /path/to/file

# Give specific group read-write access
$ setfacl -m g:qa:rw /path/to/file

# Remove specific ACL
$ setfacl -x u:bob /path/to/file

# Remove all ACLs
$ setfacl -b /path/to/file

# Set default ACLs for directories (inherited by new files)
$ setfacl -d -m g:developers:rw /path/to/directory

# Copy ACLs from one file to another
$ getfacl file1 | setfacl --set-file=- file2

# Recursive ACL setting
$ setfacl -R -m g:developers:rw /path/to/directory
```

**ACL Mask:**

The mask entry limits the maximum permissions for named users, named groups, and the owning group:

```bash
# View effective permissions with mask
$ getfacl /path/to/file
user:bob:rwx          #effective:r--
group:developers:rwx  #effective:r--
mask::r--             # Mask limits effective permissions

# Modify mask
$ setfacl -m m::rwx /path/to/file
```

### Linux Capabilities

Capabilities provide a way to divide root privileges into distinct units:

```bash
# View file capabilities
$ getcap /usr/bin/ping
/usr/bin/ping = cap_net_raw+ep

# Set capabilities
$ sudo setcap cap_net_bind_service=+ep /path/to/program

# Remove capabilities
$ sudo setcap -r /path/to/program

# View process capabilities
$ cat /proc/self/status | grep Cap
CapInh: 0000000000000000
CapPrm: 0000003fffffffff
CapEff: 0000003fffffffff
CapBnd: 0000003fffffffff
CapAmb: 0000000000000000

# Decode capability values
$ capsh --decode=0000003fffffffff
```

**Common Capabilities:**

| Capability           | Description                                                     |
| -------------------- | --------------------------------------------------------------- |
| CAP_SETUID           | Make arbitrary manipulations of process UIDs                    |
| CAP_SETGID           | Make arbitrary manipulations of process GIDs                    |
| CAP_CHOWN            | Make arbitrary changes to file UIDs and GIDs                    |
| CAP_DAC_OVERRIDE     | Bypass file read, write, and execute permission checks          |
| CAP_DAC_READ_SEARCH  | Bypass file read and directory search permission checks         |
| CAP_FOWNER           | Bypass permission checks for operations that require file owner |
| CAP_NET_BIND_SERVICE | Bind to privileged ports (< 1024)                               |
| CAP_NET_RAW          | Use RAW and PACKET sockets                                      |
| CAP_SYS_ADMIN        | Perform various system administration operations                |

### Security Modules (SELinux/AppArmor)

These Mandatory Access Control (MAC) systems add another layer on top of DAC:

#### SELinux

```bash
# Check if SELinux is enabled
$ getenforce
Enforcing

# View file security context
$ ls -Z /var/www/html/index.html
-rw-r--r--. root root system_u:object_r:httpd_sys_content_t:s0 index.html

# Change file context
$ sudo chcon -t httpd_sys_content_t /path/to/file

# Restore default context
$ sudo restorecon -v /path/to/file

# View process context
$ ps -eZ | grep httpd
system_u:system_r:httpd_t:s0    1234 ?    00:00:00 httpd

# Troubleshoot SELinux denials
$ sudo ausearch -m AVC -ts recent
$ sudo sealert -a /var/log/audit/audit.log
```

#### AppArmor

```bash
# Check AppArmor status
$ sudo aa-status

# View profile for a program
$ cat /etc/apparmor.d/usr.sbin.apache2

# Put profile in complain mode (log but don't block)
$ sudo aa-complain /etc/apparmor.d/usr.sbin.apache2

# Put profile in enforce mode
$ sudo aa-enforce /etc/apparmor.d/usr.sbin.apache2

# Generate profile for a program
$ sudo aa-genprof /path/to/program
```

### Namespace and Container Permissions

Containers use Linux namespaces to isolate permissions:

```bash
# View namespace information for a process
$ ls -l /proc/<pid>/ns/
lrwxrwxrwx 1 root root 0 user -> 'user:[4026531837]'
lrwxrwxrwx 1 root root 0 mnt -> 'mnt:[4026532198]'
lrwxrwxrwx 1 root root 0 net -> 'net:[4026532201]'

# User namespace remapping
# Container UID 0 maps to host UID 100000
$ cat /proc/<pid>/uid_map
0     100000      65536

# Similarly for GIDs
$ cat /proc/<pid>/gid_map
0     100000      65536
```

**Docker Example:**

```bash
# Run container with specific user
$ docker run --user 1000:1000 myimage

# Run with read-only root filesystem
$ docker run --read-only myimage

# Mount with specific permissions
$ docker run -v /host/path:/container/path:ro myimage
```

### Extended Attributes

Extended attributes store additional metadata beyond traditional Unix permissions:

```bash
# List extended attributes
$ getfattr -d /path/to/file
# file: path/to/file
user.comment="Important file"

# Set extended attribute
$ setfattr -n user.description -v "Project configuration" /path/to/file

# Remove extended attribute
$ setfattr -x user.description /path/to/file

# Security-related attributes
$ getfattr -n security.selinux /path/to/file
```

### File Immutability

Make files immutable (cannot be modified or deleted):

```bash
# Set immutable attribute
$ sudo chattr +i /important/file

# View attributes
$ lsattr /important/file
----i----------- /important/file

# Remove immutable attribute
$ sudo chattr -i /important/file

# Append-only attribute (can only append, not modify)
$ sudo chattr +a /var/log/audit.log

# Common attributes:
# i - Immutable
# a - Append only
# s - Secure deletion
# S - Synchronous updates
# d - No dump
# e - Extent format (ext4)
```

---

## References

### Man Pages

| Page                 | Description                 |
| -------------------- | --------------------------- |
| `man 2 chmod`        | chmod system call           |
| `man 2 chown`        | chown system call           |
| `man 2 stat`         | stat system call            |
| `man 2 access`       | access system call          |
| `man 2 getuid`       | Get user/group IDs          |
| `man 2 setuid`       | Set user/group IDs          |
| `man 5 passwd`       | Password file format        |
| `man 5 group`        | Group file format           |
| `man 5 shadow`       | Shadow password file format |
| `man 7 capabilities` | Linux capabilities overview |
| `man 7 credentials`  | Process credentials         |
| `man 8 setcap`       | Set file capabilities       |
| `man 1 chmod`        | chmod command               |
| `man 1 chown`        | chown command               |
| `man 1 chgrp`        | chgrp command               |

### Books and Documentation

1. **"The Linux Programming Interface"** by Michael Kerrisk
   - Comprehensive coverage of Unix/Linux system programming
   - Detailed chapters on permissions and credentials

2. **"Unix and Linux System Administration Handbook"** by Evi Nemeth et al.
   - Practical system administration guidance
   - Security and permissions best practices

3. **"Understanding the Linux Kernel"** by Daniel P. Bovet and Marco Cesati
   - Deep dive into kernel internals
   - Permission checking implementation details

4. **Linux Kernel Documentation**
   - `/usr/src/linux/Documentation/filesystems/`
   - `/usr/src/linux/Documentation/security/`

5. **GNU Coreutils Manual**
   - https://www.gnu.org/software/coreutils/manual/

### Online Resources

- **Linux man pages online:** https://man7.org/linux/man-pages/
- **The Linux Documentation Project:** https://tldp.org/
- **Red Hat Security Guide:** https://access.redhat.com/documentation/
- **Ubuntu Security Guide:** https://ubuntu.com/security
- **CIS Benchmarks:** https://www.cisecurity.org/cis-benchmarks/

### Standards

- **POSIX.1-2017** - IEEE Std 1003.1-2017
  - Defines standard Unix permission behavior

- **Linux Standard Base (LSB)**
  - File system hierarchy and permissions standards

- **Filesystem Hierarchy Standard (FHS)**
  - Standard directory layout and permissions

---

## Appendix A: Quick Reference Tables

### Permission Octal Values

| Permission | Symbolic       | Octal |
| ---------- | -------------- | ----- |
| Read       | r              | 4     |
| Write      | w              | 2     |
| Execute    | x              | 1     |
| SUID       | s (on owner x) | 4000  |
| SGID       | s (on group x) | 2000  |
| Sticky     | t (on other x) | 1000  |

### Common Permission Modes

| Mode | Symbolic  | Typical Use                      |
| ---- | --------- | -------------------------------- |
| 0755 | rwxr-xr-x | Directories, executables         |
| 0644 | rw-r--r-- | Regular files                    |
| 0600 | rw------- | Private files                    |
| 0700 | rwx------ | Private directories              |
| 0750 | rwxr-x--- | Restricted directories           |
| 0640 | rw-r----- | Configuration files              |
| 0440 | r--r----- | Read-only config (e.g., sudoers) |
| 2775 | rwxrwsr-x | Shared directory with SGID       |
| 1777 | rwxrwxrwt | Shared writable (e.g., /tmp)     |
| 4755 | rwsr-xr-x | SUID executable                  |

### System Call Summary

| Function      | Description                        |
| ------------- | ---------------------------------- |
| `getuid()`    | Get real UID                       |
| `geteuid()`   | Get effective UID                  |
| `getgid()`    | Get real GID                       |
| `getegid()`   | Get effective GID                  |
| `setuid()`    | Set real and effective UID         |
| `setgid()`    | Set real and effective GID         |
| `seteuid()`   | Set effective UID                  |
| `setegid()`   | Set effective GID                  |
| `setreuid()`  | Set real and effective UID         |
| `setregid()`  | Set real and effective GID         |
| `setresuid()` | Set real, effective, and saved UID |
| `setresgid()` | Set real, effective, and saved GID |
| `getgroups()` | Get supplementary group IDs        |
| `setgroups()` | Set supplementary group IDs        |
| `chmod()`     | Change file permissions            |
| `chown()`     | Change file owner and group        |
| `stat()`      | Get file status                    |
| `access()`    | Check file accessibility           |

---

## Appendix B: Troubleshooting Flowchart

```
User reports "Permission denied"
│
▼
┌───────────────┐
│ Does file     │ NO ──► Check file exists in expected location
│ exist?        │        Check parent directory permissions
└───────┬───────┘
│ YES
▼
┌───────────────┐
│ Can user      │ NO ──► Check execute permission on all parent
│ traverse path?│        directories in the path
└───────┬───────┘
│ YES
▼
┌───────────────┐
│ Check file    │
│ permissions   │
│               │ NO ──► Fix with chmod/chown
│ User = Owner? ├──────► Check owner permissions (first 3 bits)
│               │
│ User in Group?├──────► Check group permissions (second 3 bits)
│               │
│ Otherwise     ├──────► Check other permissions (last 3 bits)
└───────┬───────┘
│ Permissions look OK
▼
┌───────────────┐
│ Check ACLs    │ NO ──► Check `getfacl` output
│ Allow access? │        Verify mask doesn't restrict
└───────┬───────┘
│ YES or no ACLs
▼
┌───────────────┐
│ Check SELinux │ NO ──► Review audit logs
│ /AppArmor     │        Fix context or update policy
└───────┬───────┘
│ YES or not enabled
▼
┌───────────────┐
│ Check file    │ YES ─► Use chattr to remove
│ attributes    │        immutable/append-only flags
│ (immutable)?  │
└───────┬───────┘
│ NO
▼
┌───────────────┐
│ Check mount   │ YES ─► Remount with appropriate
│ options       │        options (rw, exec, etc.)
│ (ro, noexec)? │
└───────┬───────┘
│ NO
▼
┌───────────────┐
│ Use strace to │
│ identify exact│
│ failing call  │
└───────────────┘
```

---

## Appendix C: Security Audit Checklist

```
[ ] No world-writable files in system directories
[ ] No SUID/SGID files in user-writable locations
[ ] All SUID/SGID binaries are necessary and from trusted sources
[ ] /tmp and /var/tmp have sticky bit set
[ ] Home directories are not world-readable
[ ] SSH key files have correct permissions (600 for private, 644 for public)
[ ] /etc/shadow and /etc/gshadow are not world-readable
[ ] No files or directories without valid owner/group
[ ] Critical configuration files are not world-writable
[ ] Umask is set appropriately system-wide
[ ] Sensitive directories are not accessible by unauthorized users
[ ] Application log files are properly secured
[ ] Database files are accessible only by database user
[ ] Web content is readable but not writable by web server
[ ] Cron directories have appropriate permissions
[ ] Boot-related files are protected
```

---

_Document Version: 1.0_
_Last Updated: January 2026_
_Author: System Administration Documentation Team_
