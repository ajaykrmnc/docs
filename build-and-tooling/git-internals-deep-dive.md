# Git Internals: A Deep Dive into the Data Structures and Architecture

## Preface

This document explores the internal architecture of Git, the distributed version control
system created by Linus Torvalds in 2005. Much like Maurice J. Bach's seminal work
"The Design of the UNIX Operating System" explained the internals of UNIX, this document
aims to provide an equally thorough understanding of Git's internal mechanisms.

Git is fundamentally a content-addressable filesystem with a version control system
built on top. Understanding this distinction is crucial to grasping how Git operates
at its core. While most users interact with Git through its porcelain commands, this
document focuses exclusively on the plumbing—the underlying data structures, algorithms,
and mechanisms that make Git work.

---

## Table of Contents

1. The Philosophy of Content-Addressable Storage
2. The Git Object Model
   - 2.1 Blob Objects
   - 2.2 Tree Objects
   - 2.3 Commit Objects
   - 2.4 Tag Objects
3. The Object Database
   - 3.1 Loose Objects
   - 3.2 Object Storage Format
   - 3.3 Object Naming and SHA-1
4. Pack Files
   - 4.1 Pack File Structure
   - 4.2 Delta Compression
   - 4.3 Pack Indexes
   - 4.4 Multi-Pack Indexes
5. The .git Directory Anatomy
6. References and the Ref Database
   - 6.1 Branches
   - 6.2 Tags
   - 6.3 Remote-Tracking References
   - 6.4 Symbolic References
   - 6.5 The Reflog
7. The Index (Staging Area)
   - 7.1 Index File Format
   - 7.2 Cache Entries
   - 7.3 Extensions
   - 7.4 Split Index
8. Merge Algorithms
   - 8.1 Three-Way Merge
   - 8.2 Recursive Merge Strategy
   - 8.3 Octopus Merge
   - 8.4 Conflict Resolution
9. Diff Algorithms
   - 9.1 Myers Diff Algorithm
   - 9.2 Patience Diff
   - 9.3 Histogram Diff
10. The DAG: Directed Acyclic Graph
11. Garbage Collection
12. Transfer Protocols
13. Hooks Architecture
14. Worktrees and Submodules
15. Cryptographic Integrity

---

## Chapter 1: The Philosophy of Content-Addressable Storage

At its core, Git is a content-addressable filesystem. This means that the "address"
(or name) of any piece of content is derived directly from the content itself using
a cryptographic hash function. This architectural decision has profound implications
for how Git stores, retrieves, and verifies data.

### 1.1 What is Content-Addressable Storage?

In traditional filesystems, data is stored at locations determined by the filesystem's
allocation algorithms. The name of a file and its location on disk are arbitrary—
you can rename a file without changing its contents, and you can move it without
altering its identity.

Content-addressable storage (CAS) inverts this relationship. The identifier of any
piece of data is computed as a cryptographic hash of the data itself. This creates
a deterministic relationship between content and identity:

```
Identity = Hash(Content)
```

This design provides several crucial properties:

**Integrity Verification**: Because the name is derived from the content, any
corruption or tampering is immediately detectable. If even a single bit changes,
the hash changes completely (the avalanche effect), and the content no longer
matches its identifier.

**Deduplication**: Identical content always produces the same hash. If you store
the same file contents twice, Git automatically deduplicates them because they
would have the same object name.

**Immutability**: Objects in Git are immutable. You cannot change an object's
content without changing its identity. This makes Git's history tamper-evident.

### 1.2 The Choice of SHA-1

Git originally chose SHA-1 (Secure Hash Algorithm 1) as its hash function. SHA-1
produces a 160-bit (20-byte) hash value, typically represented as a 40-character
hexadecimal string:

```
e83c5163316f89bfbde7d9ab23ca2e25604af290
```

The choice of SHA-1 was based on several factors when Git was created in 2005:

1. **Speed**: SHA-1 is relatively fast to compute, which is important given
   the frequency of hash calculations in Git operations.

2. **Collision Resistance**: At the time, SHA-1 was considered cryptographically
   secure against collision attacks (finding two different inputs that produce
   the same hash).

3. **Wide Adoption**: SHA-1 was a well-understood, standardized algorithm with
   implementations available on all platforms.

### 1.3 The SHA-1 to SHA-256 Transition

Since Git's creation, cryptographic attacks against SHA-1 have advanced. In 2017,
researchers demonstrated the first practical SHA-1 collision (the "SHAttered" attack).
While Git includes mitigations against known collision attacks, the project has been
working on transitioning to SHA-256.

The SHA-256 transition involves:

- A new hash function producing 256-bit (32-byte) hashes
- Backward compatibility mechanisms for interoperability
- Repository format version 1 to indicate SHA-256 usage

The transition preserves Git's fundamental architecture while strengthening its
cryptographic foundation.

### 1.4 The Object Model Overview

Git's content-addressable storage is organized around four types of objects:

1. **Blob**: Stores file contents (no filename, no metadata—just content)
2. **Tree**: Stores directory structure (names, modes, and references to blobs/trees)
3. **Commit**: Stores a snapshot reference with metadata (author, message, parent commits)
4. **Tag**: Stores a reference to another object with annotation metadata

Each object type serves a specific purpose in representing a version-controlled
project's state and history. Together, they form a directed acyclic graph (DAG)
that represents the complete history of a repository.

---

## Chapter 2: The Git Object Model

The Git object model is the foundation upon which all of Git's functionality is
built. Understanding these four object types and their relationships is essential
to understanding how Git tracks changes, manages history, and enables collaboration.

### 2.1 Blob Objects

A blob (binary large object) is the simplest Git object type. It stores the contents
of a single file—nothing more. No filename, no permissions, no timestamps. Just
raw content.

#### 2.1.1 Blob Structure

A blob object consists of:

```
blob <content-length>\0<content>
```

Where:
- `blob` is the literal string identifying the object type
- `<content-length>` is the decimal representation of the content size in bytes
- `\0` is a null byte separator
- `<content>` is the raw file content

For example, if we have a file containing "Hello, World!\n" (14 bytes), the
blob object would be:

```
blob 14\0Hello, World!\n
```

This entire structure is then compressed using zlib and stored in the object
database with a filename derived from its SHA-1 hash.

#### 2.1.2 The Separation of Content and Metadata

Git's decision to separate file content from file metadata (name, path, permissions)
is a deliberate architectural choice with significant implications:

**Rename Detection**: Since a blob only contains content, Git can detect renames
by comparing blob hashes. If two files in different commits have the same blob
hash, they contain identical content regardless of their names.

**Space Efficiency**: If you have 100 files with identical content, Git stores
only one blob. The tree objects reference the same blob with different names.

**Simplicity**: Each object type has a single responsibility. Blobs store content;
trees handle structure.

#### 2.1.3 Binary vs Text Content

Git treats all file content as binary data. There is no fundamental distinction
between "text files" and "binary files" at the blob level. The blob simply stores
whatever bytes comprise the file.

However, Git does apply heuristics to determine if content is text-like for the
purposes of diff generation and merge operations:

1. Git scans the first 8000 bytes of content
2. If a null byte (\0) is found, the content is considered binary
3. Text content receives line-based diff treatment
4. Binary content is treated as an atomic unit for diffs

This heuristic can be overridden using gitattributes, allowing users to specify
that certain files should be treated as text or binary regardless of their content.

#### 2.1.4 Large File Considerations

Blobs store complete file contents, which presents challenges for large files:

- Each version of a large file creates a new blob
- Pack file delta compression helps but has limits
- Binary files often don't delta-compress well

This limitation led to the development of Git LFS (Large File Storage), which
replaces large file blobs with small pointer files while storing the actual
content in a separate storage system.

### 2.2 Tree Objects

While blobs store file contents, tree objects store directory structure. A tree
is essentially a directory listing that maps names to blobs (files) or other
trees (subdirectories).

#### 2.2.1 Tree Structure

A tree object has the following format:

```
tree <content-length>\0<entries>
```

Where each entry has the format:

```
<mode> <name>\0<20-byte-sha1>
```

Multiple entries are concatenated without separators. The entries are sorted
by name using a specific algorithm (described below).

#### 2.2.2 File Modes

The mode field is an octal number representing the file type and permissions.
Git uses a simplified subset of Unix file modes:

| Mode    | Description                                    |
|---------|------------------------------------------------|
| 100644  | Regular file (not executable)                  |
| 100755  | Regular file (executable)                      |
| 120000  | Symbolic link                                  |
| 040000  | Directory (subdirectory tree)                  |
| 160000  | Gitlink (submodule reference)                  |

Note that Git only preserves the executable bit for regular files. Other Unix
permissions (read, write, group, other) are not preserved. This is a deliberate
simplification—Git focuses on content versioning, not full filesystem metadata.

#### 2.2.3 Tree Entry Sorting

Tree entries must be sorted in a specific order for consistent hashing. The
sorting algorithm is not simple lexicographic ordering:

1. Entries are sorted by name bytes
2. For sorting purposes, tree entries (directories) have "/" appended to their name
3. This ensures proper ordering for comparison operations

For example, given entries:
- `foo` (blob)
- `foo.c` (blob)
- `foo` (tree, representing `foo/`)

The sort order would be: `foo` (blob), `foo` (tree), `foo.c` (blob)

This sorting is crucial because changing the order would change the tree's hash.

#### 2.2.4 Tree Hierarchy and Path Resolution

Git does not store paths directly. Instead, paths are constructed by traversing
the tree hierarchy from the root:

```
Root Tree
├── src/ (tree object A)
│   ├── main.c (blob X)
│   └── utils/ (tree object B)
│       └── helper.c (blob Y)
└── README (blob Z)
```

To resolve the path `src/utils/helper.c`:

1. Start at the root tree
2. Find entry "src" → tree object A
3. In tree A, find entry "utils" → tree object B
4. In tree B, find entry "helper.c" → blob Y

This hierarchical structure means:
- Moving a file changes only the trees in its path to the root
- Unchanged directories reference the same tree objects
- Structural sharing minimizes storage requirements

#### 2.2.5 Sparse Trees and Empty Directories

Git has a fundamental limitation: it cannot track empty directories. This is
because Git tracks content, and an empty directory contains no content:

- Trees must contain at least one entry
- A tree with no entries would have no content-derived identity
- The convention is to place a `.gitkeep` file in directories that must exist

This limitation is inherent to Git's content-addressable design.

### 2.3 Commit Objects

Commit objects are the heart of Git's version control capabilities. A commit
represents a snapshot of the project at a point in time, along with metadata
about that snapshot and its relationship to previous snapshots.

#### 2.3.1 Commit Structure

A commit object has the following format:

```
commit <content-length>\0<commit-content>
```

The commit content consists of:

```
tree <tree-sha1>
parent <parent-sha1>
[parent <parent-sha1>]...
author <name> <email> <timestamp> <timezone>
committer <name> <email> <timestamp> <timezone>
[gpgsig <signature>]

<commit-message>
```

Let's examine each field:

**tree**: The SHA-1 of the root tree object representing the project state.
Every commit points to exactly one tree—the complete snapshot of the project
at that moment.

**parent**: The SHA-1 of a parent commit. A commit may have:
- Zero parents (initial commit)
- One parent (regular commit)
- Multiple parents (merge commit)

**author**: The person who originally wrote the changes. Includes name, email,
Unix timestamp, and timezone offset (e.g., `+0530` or `-0800`).

**committer**: The person who applied the commit to the repository. Often the
same as the author, but different when patches are applied by someone else.

**gpgsig** (optional): A GPG signature for commit verification.

**commit-message**: The message describing the changes, preceded by a blank line.

#### 2.3.2 The Distinction Between Author and Committer

The author/committer distinction enables Git's distributed workflow:

**Author**: Created the original change
- Set when the commit is first created
- Preserved when commits are cherry-picked or rebased
- Represents intellectual ownership

**Committer**: Applied the change to the repository
- Updated when commits are modified (rebase, amend)
- Represents who introduced the commit to this history
- Includes the committer's timestamp (when the commit was applied)

For example, when you cherry-pick a commit:
- Author remains the original creator
- Committer becomes you, with the current timestamp

When you rebase:
- Author remains unchanged
- Committer and committer date are updated

#### 2.3.3 Timestamp Format

Git stores timestamps in a specific format:

```
<unix-timestamp> <timezone-offset>
```

For example:
```
1609459200 +0000
```

This represents January 1, 2021 00:00:00 UTC.

The Unix timestamp is the number of seconds since the Unix epoch (January 1, 1970
00:00:00 UTC). The timezone offset indicates the author's/committer's local time
zone at the time of the commit.

Git preserves the original timezone rather than converting to UTC. This maintains
information about when the commit was made in the committer's local context.

#### 2.3.4 Commit Identity and the Immutability Principle

Because a commit's SHA-1 is derived from all of its content, including:
- The tree reference
- All parent references
- Author information (including timestamp)
- Committer information (including timestamp)
- The commit message

Any change to any of these fields creates a completely different commit. This
immutability principle has important implications:

1. **Amending creates new commits**: When you amend a commit, you create a new
   commit object with a new SHA-1. The old commit still exists (until garbage
   collected).

2. **Rebasing rewrites history**: Rebase creates new commit objects because
   parent references change. Even if the tree and message are identical, the
   parent SHA-1 differs.

3. **Cherry-picking creates new commits**: The parent and committer information
   change, resulting in a new commit SHA-1.

4. **History is tamper-evident**: Any modification to historical commits
   creates a divergent history that's immediately detectable.

#### 2.3.5 Merge Commits

When a commit has multiple parents, it represents a merge. The commit structure
simply includes multiple `parent` lines:

```
tree abc123...
parent def456...
parent 789abc...
author Alice <alice@example.com> 1609459200 +0000
committer Alice <alice@example.com> 1609459300 +0000

Merge branch 'feature' into main
```

The order of parents matters:
- The first parent is traditionally the branch being merged into
- Subsequent parents are the branches being merged
- This convention affects tools like `git log --first-parent`

Merge commits themselves don't store the merge algorithm or conflict resolutions.
They simply record the result (tree) and the parents. The merge process is
ephemeral—only its result is persisted.

### 2.4 Tag Objects

Tag objects provide a way to give a meaningful name to a specific point in
history, along with optional metadata. Tags come in two forms: lightweight
and annotated.

#### 2.4.1 Lightweight vs Annotated Tags

**Lightweight tags** are not objects at all. They are simply references
(discussed in Chapter 6) pointing directly to a commit. A lightweight tag
is just a file in `.git/refs/tags/` containing a commit SHA-1.

**Annotated tags** are full Git objects with their own SHA-1, stored in the
object database. They contain metadata and point to another object.

#### 2.4.2 Tag Object Structure

An annotated tag has the following format:

```
tag <content-length>\0<tag-content>
```

The tag content consists of:

```
object <target-sha1>
type <target-type>
tag <tag-name>
tagger <name> <email> <timestamp> <timezone>
[gpgsig <signature>]

<tag-message>
```

**object**: The SHA-1 of the object being tagged. While typically a commit,
tags can point to any object type (blob, tree, or even another tag).

**type**: The type of the target object (`commit`, `tree`, `blob`, or `tag`).

**tag**: The tag name (e.g., `v1.0.0`).

**tagger**: The person who created the tag, with timestamp.

**gpgsig** (optional): A GPG signature for tag verification.

**tag-message**: A message describing the tag, preceded by a blank line.

#### 2.4.3 Tag-to-Tag References (Recursive Tags)

Git allows tags to point to other tags, creating a chain:

```
Tag A → Tag B → Tag C → Commit
```

This is unusual but valid. Git provides "tag peeling" to resolve such chains
and find the ultimate target object.

#### 2.4.4 Why Use Annotated Tags?

Annotated tags offer advantages over lightweight tags:

1. **Metadata**: Include tagger identity and timestamp
2. **Message**: Can describe the release or milestone
3. **Signatures**: Can be GPG-signed for verification
4. **Persistence**: Are full objects, ensuring they survive certain operations

For release versioning, annotated tags are the standard practice because they
provide a verifiable record of who created the tag and when.

---

## Chapter 3: The Object Database

Git's object database is the persistent storage layer for all objects. It's
located in the `.git/objects` directory and uses a specific organization
scheme for efficient storage and retrieval.

### 3.1 Loose Objects

When Git first creates an object, it's stored as a "loose" object—a single
compressed file in the object database.

#### 3.1.1 Loose Object Storage Path

Loose objects are stored using their SHA-1 hash as the path:

```
.git/objects/<first-2-chars>/<remaining-38-chars>
```

For example, an object with SHA-1 `e83c5163316f89bfbde7d9ab23ca2e25604af290`
is stored at:

```
.git/objects/e8/3c5163316f89bfbde7d9ab23ca2e25604af290
```

The two-character prefix serves as a directory to prevent having too many
files in a single directory, which could impact filesystem performance.

#### 3.1.2 Compression Format

Loose objects are compressed using zlib's deflate algorithm:

```
zlib_deflate(type + " " + size + "\0" + content)
```

The compression typically achieves significant space savings for text content,
while binary content may see less benefit.

#### 3.1.3 Reading a Loose Object

To read a loose object:

1. Compute the expected path from the SHA-1
2. Read the file contents
3. Decompress using zlib inflate
4. Parse the header to get type and size
5. Verify the content size matches
6. Optionally verify the SHA-1 matches

This verification ensures object integrity. A corrupted object will fail
either decompression or hash verification.

### 3.2 Object Storage Format

Let's examine the complete format of stored objects.

#### 3.2.1 The Object Header

Every Git object begins with a header:

```
<type> <size>\0
```

Where:
- `<type>` is one of: `blob`, `tree`, `commit`, `tag`
- `<size>` is the decimal content size in bytes
- `\0` is a null byte separator

This header is part of the content that's hashed to produce the object's SHA-1.

#### 3.2.2 Hash Computation

The SHA-1 is computed over the complete object (header + content):

```python
sha1(type + " " + str(len(content)) + "\0" + content)
```

This ensures the object type and size are cryptographically bound to the content.
An attacker cannot change an object's type without changing its hash.

#### 3.2.3 Object Verification

Git verifies objects in several situations:

1. **On read**: Optional, controlled by `core.fsync*` settings
2. **During fsck**: Explicit verification of all objects
3. **During transfer**: Received objects are verified before storage
4. **During gc**: Objects are verified during repacking

Verification catches:
- Disk corruption
- Memory errors during storage
- Transmission errors
- Intentional tampering

### 3.3 Object Naming and SHA-1

The SHA-1 hash serves as both the object's name and its integrity check.

#### 3.3.1 Collision Probability

With a 160-bit hash, the probability of accidental collision is astronomically
low. The birthday paradox suggests we'd need about 2^80 objects before having
a 50% chance of collision. For perspective:

- 2^80 ≈ 1.2 × 10^24 objects
- If a repository averaged 1 million commits per second
- It would take about 38 billion years to reach a 50% collision probability

For practical purposes, accidental collisions are not a concern.

#### 3.3.2 Intentional Collision Attacks

Intentional collisions are a different matter. The SHAttered attack demonstrated
that SHA-1 collisions could be generated with significant computational resources
(about 6,500 years of single-CPU time, or much less with distributed computing).

Git has implemented mitigations:

1. **Collision detection**: Git checks for known collision patterns
2. **SHA-256 transition**: New repositories can use SHA-256
3. **Transfer validation**: Additional checks during fetch/push

For most repositories, the practical risk remains low because an attacker
would need write access to introduce a collision.

#### 3.3.3 Object Abbreviation

Git allows SHA-1 abbreviation for human convenience:

- Full: `e83c5163316f89bfbde7d9ab23ca2e25604af290`
- Abbreviated: `e83c516` (or even `e83c5` if unique)

Git automatically determines the minimum unique abbreviation length. The
`core.abbrev` setting controls the default abbreviation length.

In large repositories, longer abbreviations are needed to maintain uniqueness.
Git will always expand to the full SHA-1 internally.

---

## Chapter 4: Pack Files

While loose objects are simple and efficient for individual operations, they
become inefficient for storage and transfer as a repository grows. Pack files
solve this by combining multiple objects into a single file with sophisticated
delta compression.

### 4.1 Pack File Structure

A pack file consists of three main components:

1. **Header**: Magic number, version, and object count
2. **Object entries**: Compressed objects and deltas
3. **Trailer**: SHA-1 checksum of the pack contents

#### 4.1.1 Pack Header

The 12-byte pack header contains:

```
Bytes 0-3:   "PACK" (magic signature)
Bytes 4-7:   Version number (network byte order, currently 2 or 3)
Bytes 8-11:  Number of objects (network byte order)
```

Version 2 is the most common. Version 3 was introduced for SHA-256 support.

#### 4.1.2 Object Entries

Each object entry begins with a variable-length header encoding:
- Object type (3 bits)
- Uncompressed size (variable-length encoding)

The type values are:

| Value | Type            | Description                    |
|-------|-----------------|--------------------------------|
| 1     | OBJ_COMMIT      | Commit object                  |
| 2     | OBJ_TREE        | Tree object                    |
| 3     | OBJ_BLOB        | Blob object                    |
| 4     | OBJ_TAG         | Tag object                     |
| 6     | OBJ_OFS_DELTA   | Delta with offset reference    |
| 7     | OBJ_REF_DELTA   | Delta with SHA-1 reference     |

Types 5 is reserved. Types 6 and 7 are for delta-compressed objects.

#### 4.1.3 Variable-Length Integer Encoding

Pack files use a variable-length integer encoding for sizes:

```
Bit 7: Continuation flag (1 = more bytes follow)
Bits 0-6: Size data (7 bits per byte)
```

For object headers, the first byte encodes:
```
Bit 7:    Continuation flag
Bits 4-6: Object type
Bits 0-3: Size (least significant 4 bits)
```

Subsequent bytes provide additional size bits (7 bits each).

#### 4.1.4 Pack Trailer

The 20-byte trailer is the SHA-1 of all preceding pack content (header and
entries). This enables verification of pack integrity.

### 4.2 Delta Compression

Delta compression is the key to pack file efficiency. Instead of storing
complete object content, Git stores the differences between similar objects.

#### 4.2.1 The Delta Philosophy

Git's delta compression is based on several observations:

1. **Similar content is common**: Different versions of a file often share
   significant content.

2. **Non-adjacent objects may be similar**: A file at revision 1 might be
   most similar to a file at revision 100, not revision 2.

3. **Base choice matters**: Choosing the right base object for delta
   compression dramatically affects compression ratio.

#### 4.2.2 Delta Instruction Format

A delta is a sequence of instructions to reconstruct the target from a base:

**Copy instruction**: Copy bytes from the base object
```
Bit 7: 1 (indicates copy)
Bits 0-6: Presence flags for offset and size bytes
```

Following bytes specify offset (up to 4 bytes) and size (up to 3 bytes).

**Insert instruction**: Insert literal bytes
```
Bit 7: 0 (indicates insert)
Bits 0-6: Number of bytes to insert (1-127)
```

Following bytes are the literal data to insert.

#### 4.2.3 Delta Chain Length

Deltas can reference other deltas, forming a chain:

```
Base Object ← Delta 1 ← Delta 2 ← Delta 3
```

To reconstruct Delta 3's target:
1. Read the base object
2. Apply Delta 1 to get intermediate 1
3. Apply Delta 2 to get intermediate 2
4. Apply Delta 3 to get the final object

Long chains provide better compression but slower reconstruction. Git limits
chain depth (default 50) via `pack.depth`.

#### 4.2.4 Delta Base Selection

Git uses sophisticated heuristics to choose delta bases:

1. **Type matching**: Only delta against the same object type
2. **Size similarity**: Prefer bases of similar size
3. **Path similarity**: Prefer objects from the same path (for blobs)
4. **Recency**: Recent objects make good bases

The algorithm (implemented in `diff-delta.c`) uses a sliding window approach
to find the best base among candidate objects.

#### 4.2.5 OFS_DELTA vs REF_DELTA

Two delta encoding schemes exist:

**OFS_DELTA (type 6)**: References base by offset within the pack file
- More compact (offset vs. 20-byte SHA-1)
- Requires pack file integrity
- Used within single pack files

**REF_DELTA (type 7)**: References base by SHA-1
- Self-describing (no pack context needed)
- Used during network transfer
- Allows referencing objects in other packs

During transfer, REF_DELTA is common because the receiver's pack organization
is unknown. After receiving, Git repacks using OFS_DELTA for efficiency.

### 4.3 Pack Indexes

Pack files are optimized for sequential writing, not random access. Pack
indexes provide efficient object lookup.

#### 4.3.1 Index File Structure (Version 2)

The `.idx` file accompanying each `.pack` file contains:

**Header (8 bytes)**:
```
Bytes 0-3: Magic number (0xff744f63)
Bytes 4-7: Version (2)
```

**Fan-out Table (256 × 4 bytes = 1024 bytes)**:
Entry N contains the cumulative count of objects whose first SHA-1 byte is ≤ N.
This enables binary search by first byte.

**SHA-1 Table**:
Sorted list of all object SHA-1s (20 bytes each).

**CRC32 Table**:
CRC32 of each object's pack data (4 bytes each).

**Offset Table**:
Pack offset for each object (4 bytes each). High bit indicates large offset.

**Large Offset Table** (if needed):
8-byte offsets for packs larger than 2GB.

**Trailers**:
- SHA-1 of the pack file
- SHA-1 of the index file itself

#### 4.3.2 Object Lookup Algorithm

To find an object in a pack:

1. Extract the first byte of the SHA-1 (e.g., 0xe8)
2. Use the fan-out table to find the range of objects starting with that byte
3. Binary search within that range in the SHA-1 table
4. If found, use the same index position in the offset table
5. Seek to that offset in the pack file

This provides O(log n) lookup with good cache behavior due to the sorted SHA-1
table structure.

#### 4.3.3 Reverse Index

Sometimes Git needs to find which object is at a given pack offset (e.g., when
processing delta bases). The reverse index maps offsets back to objects.

Originally computed on-demand in memory, Git now supports on-disk reverse
indexes (`.rev` files) for improved performance on large packs.

### 4.4 Multi-Pack Indexes

As repositories grow, they may accumulate many pack files. Multi-pack indexes
(MIDX) provide unified indexing across multiple packs.

#### 4.4.1 The Multi-Pack Problem

Without MIDX, looking up an object requires:
1. Checking loose objects directory
2. Checking each pack file's index

With hundreds of pack files, this becomes slow even with binary search.

#### 4.4.2 MIDX Structure

The multi-pack index contains:

1. **Pack name table**: List of pack file names
2. **Object ID table**: Sorted SHA-1s from all packs
3. **Object offset table**: Pack index + offset pairs
4. **Optional extensions**: Bitmaps, commit graphs, etc.

MIDX provides single-lookup access to objects across all indexed packs.

#### 4.4.3 MIDX Bitmaps

Commit reachability is a common operation (e.g., "which objects are reachable
from commit X?"). Reachability bitmaps pre-compute this information:

- One bitmap per "important" commit
- Each bit represents one object in the MIDX
- Bit is set if object is reachable from that commit

Bitmap operations (AND, OR, XOR) enable fast set operations:
- "Objects reachable from A but not B" = bitmap(A) AND NOT bitmap(B)

This dramatically accelerates clone, fetch, and push operations.

---

## Chapter 5: The .git Directory Anatomy

The `.git` directory is the repository's database. Understanding its structure
reveals how Git organizes and persists all repository data.

### 5.1 Directory Overview

A typical `.git` directory contains:

```
.git/
├── HEAD                  # Current branch reference
├── config                # Repository configuration
├── description           # Description (for gitweb)
├── hooks/                # Hook scripts
├── index                 # Staging area
├── info/                 # Additional info (exclude, refs)
├── logs/                 # Reflog data
├── objects/              # Object database
│   ├── info/             # Object database info
│   ├── pack/             # Pack files
│   └── [0-9a-f][0-9a-f]/ # Loose objects
└── refs/                 # Reference database
    ├── heads/            # Branch references
    ├── tags/             # Tag references
    └── remotes/          # Remote-tracking references
```

### 5.2 The HEAD File

HEAD indicates the current checkout state. It's either:

**A symbolic reference** (most common):
```
ref: refs/heads/main
```
This means "HEAD points to the branch 'main'."

**A direct SHA-1** (detached HEAD):
```
e83c5163316f89bfbde7d9ab23ca2e25604af290
```
This means HEAD points directly to a commit, not a branch.

The HEAD file is critical—it tells Git where new commits should be recorded
and which branch to update.

### 5.3 The config File

Repository-local configuration in INI format:

```ini
[core]
    repositoryformatversion = 0
    filemode = true
    bare = false
    logallrefupdates = true
[remote "origin"]
    url = git@github.com:user/repo.git
    fetch = +refs/heads/*:refs/remotes/origin/*
[branch "main"]
    remote = origin
    merge = refs/heads/main
```

Configuration is read from multiple sources (in order of precedence):
1. `.git/config` (repository)
2. `~/.gitconfig` (user)
3. `/etc/gitconfig` (system)

Later entries override earlier ones.

### 5.4 The info Directory

Contains repository metadata:

**info/exclude**: Additional ignore patterns not in `.gitignore`
**info/refs**: Packed references (older format)
**info/attributes**: Repository-level attributes

The `info/exclude` file is useful for user-specific ignores that shouldn't
be committed to `.gitignore`.

### 5.5 The logs Directory

Contains reflogs (reference logs) tracking reference changes:

```
.git/logs/
├── HEAD                  # HEAD reflog
└── refs/
    ├── heads/
    │   └── main          # Branch reflogs
    └── remotes/
        └── origin/
            └── main      # Remote-tracking reflogs
```

Each line in a reflog records:
```
<old-sha1> <new-sha1> <author> <timestamp> <message>
```

Reflogs enable recovering from mistakes—even deleted branches can often
be restored from reflog entries.

### 5.6 The objects Directory

The object database, as discussed in Chapter 3:

```
objects/
├── info/                 # Object database metadata
│   ├── alternates        # Links to alternate object stores
│   └── packs             # List of pack files (optional)
├── pack/                 # Pack files
│   ├── pack-<hash>.pack  # Pack data
│   ├── pack-<hash>.idx   # Pack index
│   └── pack-<hash>.rev   # Reverse index (optional)
└── [0-9a-f][0-9a-f]/     # Loose object directories
```

### 5.7 The refs Directory

Contains references (discussed in detail in Chapter 6):

```
refs/
├── heads/               # Local branches
│   ├── main
│   └── feature
├── tags/                # Tags
│   └── v1.0.0
├── remotes/             # Remote-tracking branches
│   └── origin/
│       ├── main
│       └── HEAD
└── stash                # Stash reference
```

### 5.8 Special Files

**ORIG_HEAD**: Previous HEAD value before dangerous operations
**MERGE_HEAD**: Commit(s) being merged (during merge)
**CHERRY_PICK_HEAD**: Commit being cherry-picked
**REVERT_HEAD**: Commit being reverted
**BISECT_LOG**: Bisect session log
**FETCH_HEAD**: Results of last fetch operation

These files coordinate multi-step operations and recovery.

---

## Chapter 6: References and the Ref Database

References (refs) are human-readable names for commit SHA-1s. They transform
Git from a content-addressed storage system into a usable version control tool.

### 6.1 Reference Types and Storage

#### 6.1.1 Loose References

The simplest reference is a file containing a 40-character SHA-1:

```
$ cat .git/refs/heads/main
e83c5163316f89bfbde7d9ab23ca2e25604af290
```

The file path determines the reference type:
- `refs/heads/*`: Local branches
- `refs/tags/*`: Tags
- `refs/remotes/*`: Remote-tracking references

#### 6.1.2 Packed References

When repositories have many references, Git packs them into a single file:

```
$ cat .git/packed-refs
# pack-refs with: peeled fully-peeled sorted
e83c5163316f89bfbde7d9ab23ca2e25604af290 refs/heads/main
f5a1234567890abcdef1234567890abcdef12345 refs/tags/v1.0.0
^abc0987654321fedcba0987654321fedcba0987
```

The `^` prefix indicates a "peeled" value—the commit that an annotated tag
ultimately points to.

#### 6.1.3 Reference Lookup Order

When resolving a reference, Git checks:
1. Loose reference file (`.git/refs/...`)
2. Packed references file (`.git/packed-refs`)

Loose references take precedence, enabling updates without rewriting packed-refs.

### 6.2 Branches

Branches are references in `refs/heads/`. They represent lines of development.

#### 6.2.1 Branch as a Moving Pointer

A branch is nothing more than a pointer to a commit. When you commit, Git:
1. Creates the commit object
2. Updates the branch file to contain the new commit's SHA-1

The simplicity is profound—branches are cheap because they're just 41-byte files
(40 hex characters + newline).

#### 6.2.2 Branch Update Mechanics

When updating a branch reference, Git:
1. Writes the new SHA-1 to a lock file (`refs/heads/branch.lock`)
2. Verifies the expected old value (for atomic updates)
3. Renames the lock file to the actual ref file
4. Updates the reflog

The lock file prevents concurrent updates from corrupting the reference.

#### 6.2.3 The Current Branch

The current branch is indicated by HEAD. When HEAD contains:
```
ref: refs/heads/main
```

And you make a commit:
1. Git reads HEAD to find `refs/heads/main`
2. Git reads `refs/heads/main` to find the parent commit
3. Git creates the new commit with that parent
4. Git updates `refs/heads/main` to point to the new commit

### 6.3 Tags

Tags are references in `refs/tags/`. They provide stable names for commits.

#### 6.3.1 Lightweight Tag Implementation

A lightweight tag is simply a reference file:

```
$ cat .git/refs/tags/v1.0.0
e83c5163316f89bfbde7d9ab23ca2e25604af290
```

#### 6.3.2 Annotated Tag References

An annotated tag reference points to a tag object, not directly to a commit:

```
$ cat .git/refs/tags/v1.0.0
f5a1234567890abcdef1234567890abcdef12345  # Tag object SHA-1
```

The tag object then points to the commit (or other object).

#### 6.3.3 Tag Peeling

"Peeling" a tag means following the reference chain to find the ultimate target:

```
refs/tags/v1.0.0 → tag object → commit object
```

The packed-refs file caches peeled values with the `^` prefix to avoid repeated
object lookups.

### 6.4 Remote-Tracking References

Remote-tracking refs in `refs/remotes/` record the state of branches on remotes.

#### 6.4.1 Remote Namespace

Each remote has its own namespace:

```
refs/remotes/origin/main
refs/remotes/origin/feature
refs/remotes/upstream/main
```

#### 6.4.2 Refspec and Updates

The refspec (in `.git/config`) defines how remote refs map to local refs:

```
fetch = +refs/heads/*:refs/remotes/origin/*
```

This means:
- Fetch all branches from `refs/heads/*` on the remote
- Store them in `refs/remotes/origin/*` locally
- The `+` allows non-fast-forward updates

#### 6.4.3 Remote HEAD

`refs/remotes/origin/HEAD` is a symbolic reference indicating the remote's
default branch. It's updated during clone and can be updated manually.

### 6.5 Symbolic References

Symbolic references point to other references, not directly to commits.

#### 6.5.1 HEAD as Symbolic Reference

HEAD is the primary example:

```
ref: refs/heads/main
```

This indirection means:
- Commits update the target branch, not HEAD
- Switching branches only changes HEAD
- Tools know which branch is "current"

#### 6.5.2 Other Symbolic References

Git supports symbolic refs elsewhere:
- `refs/remotes/origin/HEAD` → default remote branch
- Custom symbolic refs are possible but rare

#### 6.5.3 Symbolic Reference Resolution

Resolution follows the reference chain:

```
HEAD → refs/heads/main → e83c5163...
```

The final SHA-1 is the "fully resolved" value.

### 6.6 The Reflog

The reflog (reference log) tracks all reference changes over time.

#### 6.6.1 Reflog Entry Format

Each reflog entry contains:

```
<old-sha1> <new-sha1> <name> <email> <timestamp> <message>
```

Example entry:
```
abc123 def456 Alice <alice@example.com> 1609459200 +0000	commit: Add feature
```

#### 6.6.2 Reflog Storage

Reflogs are stored in `.git/logs/`:

```
.git/logs/HEAD                 # All HEAD changes
.git/logs/refs/heads/main      # Changes to refs/heads/main
```

Each file contains one entry per line, with newest entries last.

#### 6.6.3 Reflog Expiration

Reflogs aren't eternal—they expire based on:

- `gc.reflogExpire`: Entries older than this are removed (default 90 days)
- `gc.reflogExpireUnreachable`: Unreachable entries expire faster (default 30 days)

Expiration happens during garbage collection.

#### 6.6.4 Reflog Syntax

Git provides special syntax for reflog access:

- `HEAD@{1}`: HEAD's previous value
- `main@{yesterday}`: main's value yesterday
- `main@{2.weeks.ago}`: main's value two weeks ago

The `@{n}` syntax counts reflog entries; time-based syntax searches by timestamp.

---

## Chapter 7: The Index (Staging Area)

The index is Git's staging area—a binary file that tracks which changes will
be included in the next commit. It's the bridge between the working tree and
the repository.

### 7.1 The Role of the Index

The index serves multiple purposes:

1. **Staging area**: Tracks changes to be committed
2. **Merge buffer**: Holds multiple versions during merge conflicts
3. **Cache**: Stores file metadata for fast status checks

Understanding the index is crucial for understanding Git's three-tree architecture:

```
Working Directory ←→ Index ←→ HEAD (Repository)
```

### 7.2 Index File Format

The index file (`.git/index`) has a binary format optimized for performance.

#### 7.2.1 Index Header

The 12-byte header contains:

```
Bytes 0-3:   Signature ("DIRC" = DirCache)
Bytes 4-7:   Version number (2, 3, or 4)
Bytes 8-11:  Number of index entries
```

Version 2 is most common. Version 3 added extended flags. Version 4 added
path prefix compression.

#### 7.2.2 Index Entries

Each entry represents a tracked file:

**Core fields (62 bytes minimum)**:
- `ctime`: File metadata change time (8 bytes)
- `mtime`: File content modification time (8 bytes)
- `dev`: Device ID (4 bytes)
- `ino`: Inode number (4 bytes)
- `mode`: File mode (4 bytes)
- `uid`: User ID (4 bytes)
- `gid`: Group ID (4 bytes)
- `size`: File size (4 bytes)
- `sha1`: Object SHA-1 (20 bytes)
- `flags`: Flag bits (2 bytes)
- `path`: Null-terminated path (variable length)

**Padding**: Entries are padded to 8-byte boundaries.

#### 7.2.3 The stat Cache

The `ctime`, `mtime`, `dev`, `ino`, `size` fields form a "stat cache." Git
uses these to quickly detect unchanged files:

1. Run `stat()` on the working tree file
2. Compare against cached values
3. If all match, file is unchanged (no SHA-1 computation needed)
4. If any differ, recompute SHA-1 to confirm change

This optimization makes `git status` fast even in large repositories.

#### 7.2.4 Flag Bits

The 2-byte flags field encodes:

```
Bits 15-14:  Extended flag (for version 3+)
Bit 13:      Assume valid (skip worktree update check)
Bit 12:      Extended (another 2-byte extended flags follows)
Bits 11-0:   Path length (if < 4096, else 0xFFF)
```

Extended flags (when bit 12 is set):
```
Bit 15:      Reserved
Bit 14:      Skip-worktree (file exists in index but not working tree)
Bit 13:      Intent-to-add (placeholder for file to be added)
```

### 7.3 Index Extensions

Following the entries, the index may contain extensions:

#### 7.3.1 Tree Cache Extension (TREE)

Caches tree objects to accelerate commits:

```
Signature: "TREE"
Size: 4 bytes (extension data size)
Data: Cached tree entries
```

Each cached entry contains:
- Path component
- Entry count and subtree count
- SHA-1 of the tree object

When you commit, Git can reuse cached tree objects for unchanged directories
rather than recomputing them.

#### 7.3.2 Resolve Undo Extension (REUC)

Stores information for undoing conflict resolution:

```
Signature: "REUC"
Data: Entries for each resolved path
```

This allows `git checkout -m <path>` to restore conflict state.

#### 7.3.3 Untracked Cache Extension (UNTR)

Caches untracked file information to accelerate status:

```
Signature: "UNTR"
Data: Directory validity info and untracked entries
```

The untracked cache records which directories were fully scanned and which
untracked files were found, avoiding re-scanning unchanged directories.

#### 7.3.4 File System Monitor Extension (FSMN)

Integrates with filesystem monitoring (fsmonitor):

```
Signature: "FSMN"
Data: Token and file list from fs monitor
```

With fsmonitor (e.g., Watchman), Git learns about changed files from the OS
rather than scanning the entire working tree.

### 7.4 Conflict Entries

During a merge conflict, the index stores multiple versions of conflicted files.

#### 7.4.1 Stage Numbers

Each index entry has a stage number (encoded in the flags):

| Stage | Meaning                              |
|-------|--------------------------------------|
| 0     | Normal (merged) entry                |
| 1     | Base version (common ancestor)       |
| 2     | "Ours" version (current branch)      |
| 3     | "Theirs" version (merged branch)     |

A conflicted file has entries at stages 1, 2, and 3, but not stage 0.

#### 7.4.2 Conflict Resolution

Resolving a conflict:
1. User edits the file to resolve differences
2. User stages the file
3. Git removes stage 1, 2, 3 entries
4. Git adds a stage 0 entry with the resolved content's SHA-1

The REUC extension records the removed entries for potential un-resolution.

### 7.5 Split Index

Large repositories may have thousands of files. Rewriting the entire index
for small changes is inefficient.

#### 7.5.1 How Split Index Works

Split index separates the index into:

1. **Shared index**: Contains most entries (`.git/sharedindex.*`)
2. **Split index**: Contains changes since the shared index (`.git/index`)

The split index references the shared index and records:
- Deleted entries (by marking them)
- New/modified entries (stored directly)

#### 7.5.2 Benefits and Tradeoffs

Benefits:
- Faster index writes for incremental changes
- Reduced I/O for partial updates

Tradeoffs:
- More complex index reading
- Periodic shared index refreshes needed
- Some operations may be slower

### 7.6 Index Lock

Concurrent index access is prevented by locking:

1. Operations acquire `.git/index.lock`
2. Write new index content
3. Rename lock file to `.git/index`

If a lock file exists from a crashed operation, users see:

```
fatal: Unable to create '.git/index.lock': File exists.
```

The lock file must be manually removed after confirming no Git processes
are running.

---

## Chapter 8: Merge Algorithms

Merging is one of Git's most sophisticated operations. Git implements several
merge strategies, each with its own algorithm and use cases.

### 8.1 The Three-Way Merge Foundation

All Git merge strategies build upon the three-way merge concept.

#### 8.1.1 The Problem with Two-Way Merge

Consider merging two versions of a file:

```
Version A:            Version B:
line 1                line 1
line 2 (modified)     line 2
line 3                line 3 (modified)
```

With only A and B, we cannot determine:
- Who changed line 2?
- Who changed line 3?
- Should both changes be kept?

#### 8.1.2 Introducing the Common Ancestor

Three-way merge adds the common ancestor (Base):

```
Base:                 Version A:          Version B:
line 1                line 1              line 1
line 2                line 2 (modified)   line 2
line 3                line 3              line 3 (modified)
```

Now we can reason:
- A changed line 2 (differs from Base), B didn't (matches Base) → use A
- A didn't change line 3, B changed line 3 → use B
- Both changed the same line → CONFLICT

#### 8.1.3 Three-Way Merge Algorithm

For each section of content:

1. **Compare each version to base**:
   - A matches base, B differs → B changed → use B
   - A differs, B matches base → A changed → use A
   - A and B both match base → no change → use base
   - A and B both differ from base:
     - A equals B → same change → use A (or B)
     - A differs from B → CONFLICT

This applies at different granularities (lines, hunks, or files).

### 8.2 Finding the Merge Base

Before merging, Git must find the common ancestor.

#### 8.2.1 Single Merge Base

In simple cases, there's one obvious common ancestor:

```
       o---o---o---o  (branch A)
      /
o---o (base)
      \
       o---o---o  (branch B)
```

The "base" commit is the merge base.

#### 8.2.2 Multiple Merge Bases (Criss-Cross)

Some histories have multiple possible merge bases:

```
       o---M1--o---o  (branch A)
      /   /
o---o---o
      \   \
       o---M2--o---o  (branch B)
```

Where M1 merged B into A, and M2 merged A into B. Both commits before M1 and
M2 are potential merge bases.

Git's merge base algorithm finds all merge bases and may merge them recursively
(see section 8.3).

#### 8.2.3 Virtual Merge Base

When there are multiple merge bases, Git can create a "virtual" merge base by
merging the multiple bases together. This merged result becomes the base for
the final three-way merge.

### 8.3 Merge Strategies

Git supports multiple merge strategies, each optimized for different scenarios.

#### 8.3.1 The Resolve Strategy

The simplest strategy:

1. Find a single merge base
2. Perform three-way merge
3. If conflicts, mark them

Limitations:
- Only handles two branches at a time
- May choose wrong base with criss-cross merges

#### 8.3.2 The Recursive Strategy

The default strategy for two-branch merges:

1. Find all merge bases
2. If multiple bases exist:
   a. Recursively merge the bases
   b. Use the result as a virtual merge base
3. Perform three-way merge with the (virtual) base

Advantages:
- Handles criss-cross histories correctly
- Produces more sensible results for complex histories

The recursion limit is 200 by default (configurable).

#### 8.3.3 The Ort Strategy

"Ostensibly Recursive's Twin" (ORT) is a rewritten recursive strategy:

- Faster implementation
- Better handling of renames
- More predictable conflict resolution
- Gradually becoming the new default

ORT addresses performance issues in the original recursive implementation.

#### 8.3.4 The Octopus Strategy

Merges more than two branches simultaneously:

```
o---o---o---o---M  (result)
           /   /
o---o---o---o /
         \ /
o---o---o--
```

Constraints:
- No conflicts allowed (aborts if conflicts occur)
- Designed for integrating independent feature branches
- Commonly used for topic branch integration

#### 8.3.5 The Ours Strategy

Takes the current branch content, ignoring other branches:

- Creates a merge commit with multiple parents
- Uses only "ours" content (ignores "theirs")
- Useful for declaring merge without changes

Not to be confused with `-X ours` which is an option to the recursive strategy.

#### 8.3.6 The Subtree Strategy

Merges a subtree of one project into another:

- Shifts paths during merge
- Allows embedding one repository in a subdirectory of another
- Forms the basis for subtree workflows

### 8.4 File-Level Merge Operations

At the file level, Git must handle various scenarios.

#### 8.4.1 Simple Cases (No Conflict)

| Base    | Ours    | Theirs  | Result         |
|---------|---------|---------|----------------|
| Present | Same    | Same    | Use base       |
| Present | Changed | Same    | Use ours       |
| Present | Same    | Changed | Use theirs     |
| Present | Changed | Changed | Same way → OK  |
| Absent  | Present | Absent  | Use ours (add) |
| Absent  | Absent  | Present | Use theirs (add)|
| Present | Absent  | Same    | Delete         |
| Present | Same    | Absent  | Delete         |

#### 8.4.2 Conflict Cases

| Base    | Ours      | Theirs    | Result               |
|---------|-----------|-----------|----------------------|
| Present | Changed   | Changed   | Different → CONFLICT |
| Absent  | Present   | Present   | Different → CONFLICT |
| Present | Absent    | Changed   | Modify/delete conflict|
| Present | Changed   | Absent    | Modify/delete conflict|

#### 8.4.3 Content Merge

When both sides modify the same file differently, Git performs content-level
(line-by-line) merge:

1. Split files into lines
2. Run diff algorithms to find changes
3. Apply three-way merge logic to each region
4. Mark unresolvable regions as conflicts

### 8.5 Rename Detection in Merges

Handling renamed files during merge is crucial for correctness.

#### 8.5.1 The Rename Detection Problem

Consider:
- In base: file named `old.c`
- In ours: file renamed to `new.c`, content unchanged
- In theirs: content of `old.c` modified

Without rename detection:
- Git sees `old.c` deleted in ours, modified in theirs (conflict!)
- Git sees `new.c` added in ours (no merge needed)
- Result: we lose theirs' changes

With rename detection:
- Git recognizes `old.c` → `new.c` rename
- Git applies theirs' changes to `new.c`
- Result: correctly merged

#### 8.5.2 Rename Detection Algorithm

Git detects renames by content similarity:

1. Find files that exist in base but not in ours/theirs
2. Find files that exist in ours/theirs but not in base
3. Compare content similarity between missing and added files
4. If similarity exceeds threshold (default 50%), consider it a rename

The similarity is computed using a delta compression algorithm variant.

#### 8.5.3 Rename/Rename Conflicts

Both sides may rename differently:

- Base: `file.c`
- Ours: renamed to `ours.c`
- Theirs: renamed to `theirs.c`

Git cannot automatically choose the correct name—this is a rename/rename conflict.

### 8.6 Conflict Representation

When Git cannot automatically merge, it records the conflict.

#### 8.6.1 Working Tree Conflict Markers

Git inserts conflict markers in the working tree:

```
<<<<<<< HEAD
content from ours
=======
content from theirs
>>>>>>> branch
```

With `merge.conflictStyle = diff3`:

```
<<<<<<< HEAD
content from ours
||||||| merged common ancestor
content from base
=======
content from theirs
>>>>>>> branch
```

#### 8.6.2 Index Conflict State

As described in Chapter 7, the index stores stages:

- Stage 1: base version
- Stage 2: ours version
- Stage 3: theirs version

The lack of stage 0 indicates an unresolved conflict.

#### 8.6.3 MERGE_HEAD and MERGE_MSG

During a merge:
- `.git/MERGE_HEAD` contains the SHA-1 being merged
- `.git/MERGE_MSG` contains the prepared commit message

These files indicate an in-progress merge and are used when committing.

---

## Chapter 9: Diff Algorithms

Diff algorithms determine how Git identifies changes between versions.
Different algorithms have different strengths.

### 9.1 The Diff Problem

Given two sequences (usually lines of text), find the minimal edit script
that transforms one into the other.

```
Version A:           Version B:
line 1               line 1
line 2               line 2
line 3               line 3 (modified)
line 4               line 4
                     line 5 (added)
```

A diff represents:
- Line 3: changed
- Line 5: added

### 9.2 The Myers Diff Algorithm

The default Git diff algorithm, developed by Eugene Myers in 1986.

#### 9.2.1 Core Concept

Myers models diff as a graph search problem:

- X-axis: positions in sequence A (original)
- Y-axis: positions in sequence B (new)
- Goal: find shortest path from (0,0) to (len(A), len(B))

Move types:
- Horizontal (→): Delete from A
- Vertical (↓): Insert from B
- Diagonal (↘): Match (no change)

#### 9.2.2 Algorithm Overview

1. Search outward from (0,0) by number of edits (k = 0, 1, 2, ...)
2. For each k, find all reachable endpoints
3. Extend along diagonals greedily (diagonals are "free")
4. Stop when reaching (len(A), len(B))

The algorithm is O((N+M)D) where D is the edit distance.

#### 9.2.3 Myers Strengths and Weaknesses

Strengths:
- Guaranteed minimal edit script
- Efficient for small changes in large files
- Well-understood behavior

Weaknesses:
- May produce unintuitive results with certain patterns
- Doesn't consider semantic meaning of lines

### 9.3 The Patience Diff Algorithm

Patience diff produces more human-readable diffs for certain cases.

#### 9.3.1 Motivation

Consider two versions of code:

```
Version A:              Version B:
func_a() {              func_a() {
    ...                     ... (modified)
}                       }

func_b() {              func_c() {
    ...                     ...
}                       }

                        func_b() {
                            ...
                        }
```

Myers might match the `}` of `func_a()` with the `}` of `func_c()`, producing
a confusing diff.

#### 9.3.2 Algorithm Overview

Patience diff works differently:

1. Find unique lines common to both versions
2. Use longest increasing subsequence (LIS) of these unique lines as anchors
3. Recursively apply the algorithm to sections between anchors
4. Use Myers for sections without unique common lines

#### 9.3.3 Key Insight

Unique lines often mark structural boundaries (function definitions, class
declarations). By anchoring on these, patience diff tends to align structural
elements correctly.

### 9.4 The Histogram Diff Algorithm

An optimization of patience diff.

#### 9.4.1 Improvements Over Patience

Histogram diff:
- Uses line occurrence counting (histogram)
- Considers low-frequency lines, not just unique lines
- Faster implementation for large files

#### 9.4.2 Performance Characteristics

Histogram diff is generally:
- Faster than patience diff
- Produces similar (often identical) results
- Default for some Git operations in certain contexts

### 9.5 Diff Output Formats

Git can produce diffs in various formats.

#### 9.5.1 Unified Diff

The standard format:

```
diff --git a/file.c b/file.c
index abc123..def456 100644
--- a/file.c
+++ b/file.c
@@ -10,7 +10,8 @@
 context line
 context line
-removed line
+added line
+another added line
 context line
```

Components:
- Header identifying files and modes
- Hunk headers (`@@ ... @@`) with line numbers
- Context lines (space prefix)
- Removed lines (`-` prefix)
- Added lines (`+` prefix)

#### 9.5.2 Raw Format

For script processing:

```
:100644 100644 abc123 def456 M	file.c
```

Fields: old mode, new mode, old SHA-1, new SHA-1, status, filename

#### 9.5.3 Stat Format

Summary of changes:

```
 file.c | 42 ++++++++++++++++++++++++------------------
 1 file changed, 24 insertions(+), 18 deletions(-)
```

### 9.6 Binary Diff

Git can compute binary diffs for storage efficiency, though not for display.

#### 9.6.1 Binary Detection

Git uses heuristics to detect binary content:
- Check first 8000 bytes for null (\0) characters
- If found, treat as binary

This can be overridden with `.gitattributes`.

#### 9.6.2 Binary Diff Representation

In textual diffs, binary changes are noted:

```
Binary files a/image.png and b/image.png differ
```

For storage, Git's delta compression (in pack files) handles binary diffs.

---

## Chapter 10: The DAG: Directed Acyclic Graph

Git's history is organized as a Directed Acyclic Graph (DAG). Understanding
this structure is key to understanding Git's behavior.

### 10.1 DAG Fundamentals

#### 10.1.1 Definition

A DAG is a graph where:
- **Directed**: Edges have direction (from child to parent)
- **Acyclic**: No cycles exist (you cannot reach a commit from itself by following edges)

In Git:
- Nodes are commits
- Edges point from commits to their parents

#### 10.1.2 Parent Relationships

Every commit (except the initial commit) has one or more parents:

- Single parent: Regular commit
- Multiple parents: Merge commit
- Zero parents: Root/initial commit

The direction is child → parent (toward the past).

### 10.2 Reachability

Reachability is a fundamental concept in Git.

#### 10.2.1 Definition

Commit A is reachable from commit B if there exists a path from B to A
following parent links.

```
A ← B ← C ← D ← E
```

A is reachable from E (follow the chain). E is not reachable from A (wrong
direction).

#### 10.2.2 Reachability and Operations

Many Git operations use reachability:

- **Fetch/Push**: Transfer objects reachable from refs
- **Garbage Collection**: Remove unreachable objects
- **Merge Base**: Find common reachable ancestors
- **Log**: Show commits reachable from a starting point

#### 10.2.3 Ancestry Queries

Git provides operators for ancestry:

- `A^`: First parent of A
- `A^2`: Second parent of A (for merges)
- `A~n`: The nth ancestor (following first parents)
- `A..B`: Commits reachable from B but not A
- `A...B`: Symmetric difference (reachable from A or B but not both)

### 10.3 Graph Traversal

Git traverses the DAG for many operations.

#### 10.3.1 Topological Sort

For operations like `git log`, Git performs topological sorting:

- Parents appear after children
- Commits with multiple paths appear once

```
    o---o---o (branch A)
   /         \
  o---o---o---M (merge)
   \         /
    o---o---o (branch B)
```

A topological sort ensures the merge M appears before all its ancestors.

#### 10.3.2 Commit Date vs Topological Order

By default, `git log` orders by commit date. With `--topo-order`, it uses
true topological ordering:

- Date order: May interleave commits from different branches
- Topo order: Groups related commits together

#### 10.3.3 Graph Traversal Optimization

For large repositories, full traversal is expensive. Git uses:

1. **Commit graph file**: Pre-computed commit metadata cache
2. **Generation numbers**: Enables pruning during traversal
3. **Bitmaps**: Fast reachability computation
4. **Bloom filters**: Fast path-based filtering

### 10.4 The Commit Graph File

The commit graph is a binary file caching commit metadata for faster traversal.

#### 10.4.1 Motivation

Reading commit objects from pack files requires:
- Finding the object in the pack index
- Decompressing the object
- Parsing the commit format

The commit graph caches parsed data for O(1) access.

#### 10.4.2 Commit Graph Structure

Located at `.git/objects/info/commit-graph`:

**Header**:
- Magic signature (CGPH)
- Version number
- Hash algorithm ID
- Number of chunks
- Number of base commit graphs

**OID Fanout**: Cumulative count by first byte (like pack index)

**OID Lookup**: Sorted list of commit SHA-1s

**Commit Data**: Fixed-size entries per commit:
- Tree SHA-1 (or index)
- First parent (index in OID lookup, or special value)
- Second parent (index, or extra edges offset)
- Generation number (topological generation)
- Commit timestamp

**Extra Edge List**: For commits with >2 parents

#### 10.4.3 Generation Numbers

Generation numbers enable pruning:

- Generation 0: Used only if not computed
- Generation N: 1 + max(parent generations)

Property: If gen(A) ≤ gen(B), then A is not an ancestor of B.

This allows skipping branches during reachability queries.

#### 10.4.4 Corrected Commit Dates

Git 2.36+ introduced "corrected commit dates":

- Monotonically increasing along parent chains
- Corrects for clock skew in actual commit dates
- Enables more accurate generation-based pruning

### 10.5 Topological Levels and Generations

Understanding generations helps with graph algorithms.

#### 10.5.1 Topological Level

The topological level of a commit:
- Root commits: level 0
- Other commits: 1 + max(parent levels)

This equals the longest path to any root commit.

#### 10.5.2 Applications

Generation numbers enable:
- Faster merge-base computation
- More efficient reachability queries
- Better pruning during graph traversal

---

## Chapter 11: Garbage Collection

Git's garbage collector reclaims storage by removing unreachable objects
and repacking data.

### 11.1 Object Lifecycle

Objects in Git go through several states:

1. **Created**: Written as loose objects
2. **Packed**: Combined into pack files
3. **Unreachable**: No references point to them
4. **Pruned**: Removed from the repository

### 11.2 What Makes Objects Unreachable

Objects become unreachable when:

- Branches are deleted
- Commits are amended or rebased
- Force pushes replace history
- Stashes are dropped

Unreachable objects are not immediately deleted—they may be needed for recovery.

### 11.3 The GC Process

Garbage collection involves several steps:

#### 11.3.1 Pack Loose Objects

Loose objects are combined into pack files:

- Reduces file count (filesystem overhead)
- Enables delta compression
- More efficient for large repositories

#### 11.3.2 Prune Unreachable Objects

Objects not reachable from any reference are candidates for removal:

1. Mark all reachable objects (from refs, reflog, worktrees)
2. Identify unmarked objects
3. Check object age (grace period)
4. Remove objects older than the grace period

The default grace period is 2 weeks (`gc.pruneExpire`).

#### 11.3.3 Expire Reflogs

Reflog entries are removed based on age:

- `gc.reflogExpire`: Reachable entries (default 90 days)
- `gc.reflogExpireUnreachable`: Unreachable entries (default 30 days)

#### 11.3.4 Pack References

Loose references are packed into `.git/packed-refs`:

- Reduces file count
- Atomic updates become faster
- May be split for performance

#### 11.3.5 Repack

Existing pack files may be reorganized:

- Combine multiple packs into one
- Improve delta compression (better base selection)
- Remove redundant objects

### 11.4 Auto GC

Git triggers garbage collection automatically:

#### 11.4.1 Triggers

Auto-GC runs when thresholds are exceeded:

- `gc.auto` (default 6700): Loose object count threshold
- `gc.autoPackLimit` (default 50): Pack file count threshold

#### 11.4.2 Background GC

Recent Git versions can run GC in the background:

- `gc.autoDetach`: Run GC as background process
- `maintenance`: Scheduled maintenance tasks

### 11.5 GC Safety Mechanisms

GC has safeguards to prevent data loss:

#### 11.5.1 Grace Period

Objects are not removed immediately:

```
gc.pruneExpire = 2.weeks.ago
```

This gives time for recovery if something was deleted accidentally.

#### 11.5.2 Reflog Protection

Reflogs keep deleted commits reachable:

- Even after deleting a branch, reflog entries exist
- Objects remain reachable through reflog
- Reflog must expire before objects are pruned

#### 11.5.3 Lock Files

GC uses lock files to prevent concurrent operations:

- `gc.pid`: Records GC process ID
- Prevents multiple GC processes
- Prevents interference with other operations

### 11.6 Manual GC Control

Users can control GC behavior:

#### 11.6.1 Aggressive GC

```
git gc --aggressive
```

- Uses more time for better compression
- Recomputes delta bases thoroughly
- Useful for repositories with imported history

#### 11.6.2 Prune Now

```
git gc --prune=now
```

- Removes unreachable objects immediately
- No grace period
- Use with caution (no recovery)

#### 11.6.3 Keep Unreachable

Some operations create `.keep` files to protect packs from GC.

---

## Chapter 12: Transfer Protocols

Git uses various protocols for data transfer between repositories.

### 12.1 Protocol Overview

Git supports several transport mechanisms:

| Protocol | URL Scheme | Characteristics |
|----------|------------|-----------------|
| Local    | file://    | Direct filesystem access |
| SSH      | ssh://     | Encrypted, authenticated |
| Git      | git://     | Unauthenticated, read-only |
| HTTP(S)  | http://    | Web-based, widely accessible |

### 12.2 The Dumb Protocol (HTTP)

The original HTTP protocol is "dumb"—the server is a static file server.

#### 12.2.1 Discovery

Client requests:
1. `GET /info/refs` - List of references
2. `GET /objects/info/packs` - List of pack files

#### 12.2.2 Object Retrieval

Client fetches objects individually:
- Loose objects: `GET /objects/ab/cdef...`
- Pack files: `GET /objects/pack/pack-<hash>.pack`
- Pack indexes: `GET /objects/pack/pack-<hash>.idx`

#### 12.2.3 Limitations

The dumb protocol:
- Requires many HTTP requests
- No delta compression during transfer
- Inefficient for large repositories

### 12.3 The Smart Protocol (SSH/Git/Smart HTTP)

The smart protocol uses a bidirectional connection.

#### 12.3.1 Reference Advertisement

Server sends list of references with capabilities:

```
<sha1> <refname>\0<capabilities>
<sha1> <refname>
...
0000
```

The `0000` is a "flush packet" marking the end.

#### 12.3.2 Want/Have Negotiation

Client sends "want" and "have" lines:

```
want <sha1> <capabilities>
want <sha1>
...
have <sha1>
have <sha1>
...
done
```

- **want**: Objects the client needs
- **have**: Objects the client already has
- **done**: End of negotiation

The server uses "have" information to compute the minimal pack.

#### 12.3.3 Pack Data Transfer

Server sends a pack file containing:
- All objects reachable from "want" refs
- Not reachable from "have" refs
- Delta-compressed where possible

### 12.4 Capability Negotiation

Protocol capabilities enable feature detection.

#### 12.4.1 Common Capabilities

| Capability | Purpose |
|------------|---------|
| `multi_ack` | Optimized negotiation |
| `thin-pack` | Delta against known objects |
| `side-band` | Progress messages |
| `ofs-delta` | Offset-based deltas |
| `shallow` | Shallow clone support |
| `filter` | Partial clone filtering |

#### 12.4.2 Protocol Version 2

Version 2 (introduced in Git 2.18) improves efficiency:

- Stateless protocol
- Server-side ref filtering
- Better packfile negotiation
- Reduced round trips

### 12.5 Push Protocol

Push uses a similar but different flow.

#### 12.5.1 Reference Update Requests

Client sends desired ref updates:

```
<old-sha1> <new-sha1> <refname>
...
0000
<pack data>
```

Each line specifies:
- Current value (what client expects)
- New value (what client wants)
- Reference name

#### 12.5.2 Atomic Push

The `atomic` capability ensures all-or-nothing updates:
- Either all refs update successfully
- Or none do (if any fails)

#### 12.5.3 Push Options

Push options allow metadata transmission:
- Used by hosting services
- Example: GitLab merge request creation

### 12.6 Shallow Clones

Shallow clones limit history depth.

#### 12.6.1 Shallow Boundary

A shallow clone has a "shallow boundary"—commits marked as having no parents
for clone purposes:

- `.git/shallow` lists boundary commits
- Parent links exist but are not followed

#### 12.6.2 Deepening and Unshallowing

Shallow clones can be:
- **Deepened**: Fetch more history
- **Unshallowed**: Fetch complete history

The boundary moves as history is fetched.

### 12.7 Partial Clones

Partial clones (Git 2.19+) allow blob-less or tree-less clones.

#### 12.7.1 Filter Specifications

```
--filter=blob:none      # No blobs
--filter=blob:limit=1m  # Blobs under 1MB only
--filter=tree:0         # No trees (extreme)
```

#### 12.7.2 On-Demand Fetching

Missing objects are fetched when accessed:
- Checkout fetches needed blobs
- Log might trigger tree fetching

This is called "promisor" behavior—the remote promises to provide objects.

---

## Chapter 13: Hooks Architecture

Git hooks are scripts that execute at specific points in Git's workflow.
They enable customization and automation.

### 13.1 Hook Categories

Hooks fall into several categories:

1. **Client-side hooks**: Run on developer machines
2. **Server-side hooks**: Run on Git servers
3. **Commit workflow hooks**: Related to commits
4. **Email workflow hooks**: Related to patches
5. **Other hooks**: Miscellaneous operations

### 13.2 Hook Location and Execution

#### 13.2.1 Default Location

Hooks are stored in `.git/hooks/`:

```
.git/hooks/
├── pre-commit
├── prepare-commit-msg
├── commit-msg
├── post-commit
├── pre-rebase
├── post-checkout
├── post-merge
├── pre-push
├── pre-receive
├── update
└── post-receive
```

Sample hooks (with `.sample` extension) are installed by default.

#### 13.2.2 Custom Hook Location

The `core.hooksPath` configuration allows specifying an alternative location:
- Enables shared hooks across repositories
- Allows version-controlled hooks

#### 13.2.3 Execution Environment

Hooks receive:
- Standard input (for some hooks)
- Command-line arguments (hook-specific)
- Environment variables (GIT_DIR, GIT_WORK_TREE, etc.)

Exit codes:
- 0: Success (allow operation to proceed)
- Non-zero: Failure (abort operation)

### 13.3 Client-Side Commit Hooks

#### 13.3.1 pre-commit

Runs before the commit message editor:

- Inspect the snapshot being committed
- Run linters, tests, style checks
- Exit non-zero to abort the commit

The index contains the staged changes; working tree may differ.

#### 13.3.2 prepare-commit-msg

Runs after default message generation, before editor:

- Arguments: message file path, message source, commit SHA (for amend)
- Modify the commit message template
- Insert ticket numbers, branch info, etc.

#### 13.3.3 commit-msg

Runs after message entry, before commit creation:

- Argument: file containing the commit message
- Validate message format
- Abort if message doesn't meet requirements

#### 13.3.4 post-commit

Runs after commit creation:

- No arguments
- Notification purposes (display, alerts)
- Cannot affect the commit

### 13.4 Server-Side Hooks

#### 13.4.1 pre-receive

Runs once before any refs are updated:

- Standard input: `<old-sha1> <new-sha1> <refname>` lines
- Validate entire push as a unit
- Exit non-zero to reject the entire push

#### 13.4.2 update

Runs once per ref being updated:

- Arguments: refname, old-sha1, new-sha1
- Validate individual ref updates
- Exit non-zero to reject that ref (others may proceed)

#### 13.4.3 post-receive

Runs after all refs are updated:

- Standard input: same format as pre-receive
- Trigger deployments, notifications
- Cannot affect the push

#### 13.4.4 post-update

Runs after refs are updated:

- Arguments: list of updated refnames
- Legacy hook (prefer post-receive)
- Commonly used for `git update-server-info`

### 13.5 Other Important Hooks

#### 13.5.1 pre-rebase

Runs before rebase operation:

- Arguments: upstream branch, branch being rebased
- Prevent rebasing certain branches
- Useful for shared branch protection

#### 13.5.2 post-checkout

Runs after checkout operations:

- Arguments: previous HEAD, new HEAD, branch flag
- Set up working directory (submodules, generated files)
- Update local databases

#### 13.5.3 pre-push

Runs before push to remote:

- Arguments: remote name, remote URL
- Standard input: `<local ref> <local sha1> <remote ref> <remote sha1>`
- Run tests before push
- Verify all commits are properly formatted

#### 13.5.4 fsmonitor-watchman

Integrates with filesystem monitoring:

- Called to get list of changed files
- Enables faster status/add operations
- Uses Watchman or similar tools

### 13.6 Hook Security Considerations

#### 13.6.1 Executable Permissions

Hooks must be executable:
- POSIX: chmod +x required
- Windows: uses extension-based execution

#### 13.6.2 Trusted Hooks

Hooks can execute arbitrary code:
- Don't clone untrusted repositories without inspection
- `core.hooksPath` can enforce verified hooks
- Consider hook signing for critical environments

---

## Chapter 14: Worktrees and Submodules

Git supports working with multiple working directories and nested repositories.

### 14.1 Multiple Worktrees

Worktrees allow multiple working directories sharing one repository.

#### 14.1.1 Worktree Structure

Main repository:
```
project/
├── .git/                  # Repository
└── (working files)        # Main worktree
```

Additional worktree:
```
../project-feature/
├── .git                   # File linking to main repository
└── (working files)        # Feature worktree
```

The worktree's `.git` is a file:
```
gitdir: /path/to/project/.git/worktrees/project-feature
```

#### 14.1.2 Worktree Database

Main repository tracks worktrees:
```
.git/worktrees/
└── project-feature/
    ├── HEAD              # Worktree's HEAD
    ├── index             # Worktree's index
    ├── gitdir            # Path to worktree's .git file
    └── logs/             # Worktree's reflogs
```

#### 14.1.3 Worktree Constraints

Constraints prevent confusion:
- Same branch cannot be checked out in multiple worktrees
- Worktrees share object database and refs
- Each worktree has its own index and HEAD

#### 14.1.4 Worktree Use Cases

Common scenarios:
- Build one branch while editing another
- Test on multiple branches simultaneously
- Long-running operations on separate worktrees

### 14.2 Submodules

Submodules embed one repository inside another.

#### 14.2.1 Submodule Configuration

The `.gitmodules` file tracks submodules:

```
[submodule "lib"]
    path = lib
    url = https://github.com/example/lib.git
    branch = main
```

This file is version-controlled—everyone sees the same submodule configuration.

#### 14.2.2 Gitlink Entries

In the tree object, submodules appear as "gitlink" entries:

- Mode: 160000
- Type: commit
- Value: submodule commit SHA-1

The superproject records which commit of the submodule should be used.

#### 14.2.3 Submodule Repository Location

Submodule repositories are stored in:
```
.git/modules/<submodule-name>/
```

The submodule working directory contains:
```
lib/.git     # File: "gitdir: ../.git/modules/lib"
```

This indirection allows:
- Submodule checkout/removal without losing history
- Shared storage for submodule objects

#### 14.2.4 Submodule States

A submodule can be in various states:

| State | Description |
|-------|-------------|
| Registered | Listed in .gitmodules |
| Initialized | .git/config has submodule entry |
| Populated | Working tree is checked out |
| Updated | At commit specified by superproject |

Operations move submodules between states.

#### 14.2.5 Submodule Update Modes

Different update strategies:

| Mode | Behavior |
|------|----------|
| checkout | Checkout specified commit (detached HEAD) |
| rebase | Rebase local changes onto specified commit |
| merge | Merge specified commit into local branch |
| none | Don't update automatically |

#### 14.2.6 Superproject/Submodule Synchronization

The relationship between superproject and submodule:

1. Superproject tree records submodule commit SHA-1
2. Submodule is a full repository at that commit
3. Changes in submodule require:
   - Commit in submodule
   - Update gitlink in superproject
   - Commit in superproject

This explicit tracking is both a strength and a complexity.

#### 14.2.7 Recursive Operations

Many Git operations support recursive submodule handling:

- `--recurse-submodules`: Include submodules in operation
- `submodule.recurse`: Default recursive behavior

---

## Chapter 15: Cryptographic Integrity

Git uses cryptographic hashing for data integrity and supports signing
for authentication.

### 15.1 Hash-Based Integrity

#### 15.1.1 The Trust Chain

Every object's identity is its hash:

```
Commit (hash includes):
├── Tree SHA-1 → Tree Object (hash includes)
│   ├── Blob SHA-1 → Blob Object (content hash)
│   └── Tree SHA-1 → Subtree Object
├── Parent SHA-1 → Parent Commit
└── Metadata (author, message, etc.)
```

Verifying a commit hash transitively verifies:
- All ancestor commits
- All trees and blobs in the snapshot
- All metadata

#### 15.1.2 Tamper Evidence

Any modification changes hashes:

1. Change a blob → blob hash changes
2. Tree containing that blob → tree hash changes
3. Commit containing that tree → commit hash changes
4. All descendant commits → their hashes change

History rewriting is detectable by hash comparison.

### 15.2 Object Verification

#### 15.2.1 On-Read Verification

Git can verify objects when reading:

```
transfer.fsckObjects = true
```

This catches:
- Hash mismatches (corruption)
- Malformed objects
- Known collision patterns (SHAttered)

#### 15.2.2 Fsck Verification

Full verification with `git fsck`:

- Checks all objects in database
- Verifies object format
- Checks referential integrity
- Reports dangling objects

### 15.3 Commit Signing

GPG/SSH signatures authenticate commits.

#### 15.3.1 Signature Storage

Signed commits include a `gpgsig` header:

```
tree abc123...
parent def456...
author Alice <alice@example.com> 1609459200 +0000
committer Alice <alice@example.com> 1609459200 +0000
gpgsig -----BEGIN PGP SIGNATURE-----

 iQEzBAABCAAdFiEE...
 ...
 -----END PGP SIGNATURE-----

Commit message here
```

The signature covers the commit content (minus the signature itself).

#### 15.3.2 Signature Verification

Verification checks:
1. Signature is valid for the commit content
2. Signing key is trusted
3. Key was valid at commit time (optionally)

#### 15.3.3 SSH Signing

Git 2.34+ supports SSH keys for signing:

- Uses existing SSH keys (no GPG required)
- Simpler key management for some workflows
- `gpg.format = ssh` to enable

### 15.4 Tag Signing

#### 15.4.1 Annotated Tag Signatures

Signed tags include a signature in the tag object:

```
object abc123...
type commit
tag v1.0.0
tagger Alice <alice@example.com> 1609459200 +0000
-----BEGIN PGP SIGNATURE-----
...
-----END PGP SIGNATURE-----

Release version 1.0.0
```

#### 15.4.2 Verification

Tag signature verification confirms:
- The tag points to the claimed object
- The tagger created the signature
- The key is trusted

### 15.5 Push Certificate

Push operations can be signed.

#### 15.5.1 Certificate Content

A push certificate includes:
- Pusher identity
- Nonce (prevents replay)
- List of ref updates
- Signature over the above

#### 15.5.2 Server Verification

Servers receiving signed pushes can:
- Verify pusher identity
- Log authenticated push history
- Enforce signing requirements

### 15.6 SHA-256 Transition

The transition from SHA-1 to SHA-256 strengthens cryptographic guarantees.

#### 15.6.1 SHA-256 Repository Format

SHA-256 repositories use:
- 64-character hexadecimal hashes
- Repository format version 1
- `extensions.objectFormat = sha256`

#### 15.6.2 Interoperability

The transition includes:
- Hash conversion between formats
- Signature over both hash algorithms (for transition)
- Gradual adoption path

---

## Chapter 16: Advanced Data Structures

Git employs additional data structures for performance optimization.

### 16.1 Bloom Filters

Bloom filters enable fast negative lookups for path-based queries.

#### 16.1.1 Purpose

When querying "did commit X change path P?", Git normally:
1. Load commit X's tree
2. Load parent's tree
3. Recursively compare trees along path P

With Bloom filters:
1. Check if P is in X's Bloom filter
2. If not in filter, definitely no change (fast path)
3. If in filter, may have changed (do full check)

#### 16.1.2 Changed-Path Bloom Filters

Stored in commit-graph files:
- One filter per commit
- Encodes which paths changed in that commit
- False positives possible, false negatives not

#### 16.1.3 Filter Parameters

Key parameters:
- Hash count: Number of hash functions (7 in Git)
- Bits per entry: Filter size relative to entry count
- Hash algorithm: murmur3 variants

### 16.2 Bitmap Indexes

Bitmaps accelerate reachability queries.

#### 16.2.1 Bitmap Structure

Each bitmap:
- Has one bit per object in the pack
- Bit is set if object is reachable from the bitmap's commit
- Supports fast set operations (AND, OR, NOT)

#### 16.2.2 Bitmap Coverage

Not every commit has a bitmap:
- Selected commits (usually branch tips, tags)
- Commits reachable from selected commits use bitmap operations

#### 16.2.3 Pack Reuse with Bitmaps

When serving a clone/fetch:
1. Compute reachability using bitmaps
2. Send pack bytes directly (no re-deltification)
3. Dramatic speedup for large repositories

### 16.3 The Commit Graph

Detailed in Chapter 10, but additional aspects:

#### 16.3.1 Incremental Commit Graphs

Large repositories use incremental graphs:
- Base graph(s) for historical commits
- Incremental graphs for recent commits
- Merged periodically during GC

#### 16.3.2 Graph Chains

Chain file lists base graphs:
```
.git/objects/info/commit-graphs/commit-graph-chain
```

Each graph can build on predecessors.

### 16.4 Midx and Bitmaps Interaction

Multi-pack indexes integrate with bitmaps:

#### 16.4.1 Unified Object Numbering

MIDX provides global object numbering:
- Objects across all packs get sequential numbers
- Bitmaps reference objects by this numbering

#### 16.4.2 Reachability Bitmaps with MIDX

The `.bitmap` file alongside MIDX:
- Provides reachability info across all packs
- Single bitmap covers entire repository
- Faster than per-pack bitmaps

---

## Chapter 17: Performance Considerations

Git's performance characteristics affect repository design and usage.

### 17.1 Filesystem Interactions

#### 17.1.1 Directory Entry Overhead

Many small files impact performance:
- Directory scanning takes time
- Inode allocation has overhead
- Pack files reduce file count

#### 17.1.2 Index Loading

The index is read frequently:
- Kept in memory during operations
- Large indexes consume memory
- Split index helps for very large repos

#### 17.1.3 Filesystem Case Sensitivity

Case sensitivity issues:
- Git is case-sensitive internally
- Case-insensitive filesystems cause problems
- `core.ignoreCase` provides workarounds

### 17.2 Network Efficiency

#### 17.2.1 Negotiation Optimization

Fetch negotiation can be slow:
- Many round-trips for large differences
- `multi_ack` and `multi_ack_detailed` help
- Protocol v2 reduces round-trips

#### 17.2.2 Pack Transfer Optimization

Pack transfer efficiency:
- Thin packs reduce transfer size
- Delta base reuse reduces CPU
- Bitmaps enable pack reuse

### 17.3 Large Repository Strategies

#### 17.3.1 Monorepo Challenges

Large monorepos face:
- Slow status (many files)
- Large index (memory)
- Slow clone (history depth)

#### 17.3.2 Partial Clone

Reduces initial clone:
- Omit blobs (blobless clone)
- Fetch on demand
- Tradeoff: network for initial storage

#### 17.3.3 Sparse Checkout

Work with subset of files:
- Index contains all files
- Working tree has subset
- Reduces I/O, memory for operations

#### 17.3.4 FSMonitor Integration

Filesystem monitoring:
- OS notifies of changes
- Skip full directory scans
- Dramatically faster status

### 17.4 Object Database Optimization

#### 17.4.1 Pack File Size

Pack file size tradeoffs:
- Large packs: fewer files, better delta opportunities
- Small packs: faster updates, less rewrite

#### 17.4.2 Delta Chain Length

Longer chains:
- Better compression
- Slower object reconstruction
- `pack.depth` configures maximum

#### 17.4.3 Window Size

Delta window:
- More candidates: better deltas
- More memory: `pack.window` configures
- More CPU: slower packing

---

## Chapter 18: Conclusion

### 18.1 The Elegance of Git's Design

Git's architecture demonstrates elegant simplicity:

1. **Content-addressable storage**: A simple concept with profound implications
2. **Immutable objects**: Enable integrity, sharing, and caching
3. **The DAG**: Natural representation for version history
4. **Separation of concerns**: Blobs hold content, trees hold structure

### 18.2 The Layered Architecture

Git operates in layers:

1. **Plumbing**: Low-level operations on objects and refs
2. **Porcelain**: High-level user-facing commands
3. **Protocols**: Network transfer mechanisms
4. **Hosting**: Remote repository services (beyond Git itself)

Understanding the lower layers illuminates the higher ones.

### 18.3 Evolution and Future

Git continues evolving:

- **SHA-256**: Stronger cryptographic foundation
- **Partial clone**: Better support for large repositories
- **Commit graphs**: Faster history operations
- **ORT merge**: Improved merge performance
- **Reftable**: More efficient reference storage (in development)

The core architecture remains stable while implementations improve.

### 18.4 Final Thoughts

Git's power comes from its fundamental data model. The content-addressable
object database, the directed acyclic graph of commits, and the simple
reference model combine to create a system that is:

- **Reliable**: Cryptographic integrity at every level
- **Efficient**: Sophisticated compression and caching
- **Distributed**: No privileged central server required
- **Flexible**: Supports diverse workflows

By understanding these internals—the blobs and trees, the pack files and
indexes, the merge algorithms and transfer protocols—developers gain
insight into not just how Git works, but why it works the way it does.

This knowledge transforms Git from a mysterious tool into a transparent
system, enabling more effective use and troubleshooting. The journey
through Git's internals reveals a carefully designed system where each
piece serves a purpose in the greater whole.

---

## Appendix A: Object Format Specifications

### A.1 Blob Format

```
blob SP <size> NUL <content>
```

- `SP`: Space character (0x20)
- `NUL`: Null byte (0x00)
- `<size>`: Decimal ASCII representation of content length
- `<content>`: Raw file content (may be binary)

### A.2 Tree Format

```
tree SP <size> NUL <entries>
```

Each entry:
```
<mode> SP <name> NUL <20-byte SHA-1>
```

- `<mode>`: Octal file mode (ASCII digits)
- `<name>`: Filename (no slash, null, or leading dot-dot)
- `<20-byte SHA-1>`: Binary SHA-1 (not hex)

Entries must be sorted (see section 2.2.3).

### A.3 Commit Format

```
commit SP <size> NUL <header> LF LF <message>
```

Header lines:
```
tree SP <40-hex-sha1> LF
parent SP <40-hex-sha1> LF
[additional parent lines]
author SP <identity> LF
committer SP <identity> LF
[gpgsig SP <signature> LF]
[other headers]
```

Identity format:
```
<name> SP LT <email> GT SP <unix-timestamp> SP <tz-offset>
```

### A.4 Tag Format

```
tag SP <size> NUL <content>
```

Content:
```
object SP <40-hex-sha1> LF
type SP <object-type> LF
tag SP <tag-name> LF
tagger SP <identity> LF
[gpgsig SP <signature> LF]
LF
<message>
```

---

## Appendix B: Pack Format Specification

### B.1 Pack File Header

```
Bytes 0-3:   PACK (magic: 0x5041434b)
Bytes 4-7:   Version (network byte order, 2 or 3)
Bytes 8-11:  Object count (network byte order)
```

### B.2 Pack Object Header

Variable-length encoding:
```
Byte 1:
  Bit 7:     MSB (more size bytes follow)
  Bits 4-6:  Object type (1-4 for regular, 6-7 for delta)
  Bits 0-3:  Size (least significant 4 bits)

Additional bytes (if bit 7 set):
  Bit 7:     MSB (more bytes follow)
  Bits 0-6:  Size (7 bits per byte)
```

### B.3 Delta Format

```
<base-object-size> (variable-length)
<target-object-size> (variable-length)
<instructions>
```

Instructions:
- Copy: Bit 7 = 1, followed by offset/size bytes
- Insert: Bit 7 = 0, bits 0-6 = length, followed by data

### B.4 Pack Trailer

```
20 bytes: SHA-1 of pack contents (excluding trailer)
```

---

## Appendix C: Index Format Specification

### C.1 Index Header

```
Bytes 0-3:   DIRC (magic: 0x44495243)
Bytes 4-7:   Version (2, 3, or 4)
Bytes 8-11:  Entry count
```

### C.2 Index Entry (Version 2)

```
Bytes 0-3:   ctime seconds
Bytes 4-7:   ctime nanoseconds
Bytes 8-11:  mtime seconds
Bytes 12-15: mtime nanoseconds
Bytes 16-19: dev
Bytes 20-23: ino
Bytes 24-27: mode
Bytes 28-31: uid
Bytes 32-35: gid
Bytes 36-39: file size
Bytes 40-59: SHA-1
Bytes 60-61: flags
Bytes 62+:   path (null-terminated)
Padding:     To 8-byte boundary
```

### C.3 Index Extensions

```
4 bytes: Extension signature
4 bytes: Extension size
N bytes: Extension data
```

Known extensions:
- TREE: Cached tree objects
- REUC: Resolve undo information
- UNTR: Untracked cache
- FSMN: FSMonitor data
- EOIE: End of index entry
- IEOT: Index entry offset table

### C.4 Index Trailer

```
20 bytes: SHA-1 of index contents (excluding trailer)
```

---

## Appendix D: Reference Format Specifications

### D.1 Loose Reference

Plain text file containing:
```
<40-hex-sha1> LF
```

### D.2 Symbolic Reference

```
ref: <target-ref-path> LF
```

Example:
```
ref: refs/heads/main
```

### D.3 Packed References

```
# pack-refs with: <options>
<40-hex-sha1> SP <refname> LF
[^<40-hex-sha1> LF]
```

The `^` prefix indicates peeled value for annotated tags.

---

## Appendix E: Protocol Specifications

### E.1 Pkt-Line Format

Length-prefixed lines:
```
<4-hex-length><data>
```

Special values:
- `0000`: Flush packet (end of message)
- `0001`: Delimiter packet (protocol v2)

### E.2 Reference Advertisement (v1)

```
<40-hex-sha1> SP <refname> NUL <capabilities> LF
<40-hex-sha1> SP <refname> LF
...
0000
```

### E.3 Want/Have Negotiation

```
want SP <40-hex-sha1> SP <capabilities> LF
want SP <40-hex-sha1> LF
...
have SP <40-hex-sha1> LF
...
done LF
```

Server responses:
- `NAK`: No common ancestor
- `ACK <sha1>`: Common ancestor found

---

## Glossary

**Blob**: Git object storing file content without metadata.

**Branch**: A movable pointer to a commit, stored in refs/heads/.

**Commit**: Git object representing a snapshot with metadata and history links.

**DAG**: Directed Acyclic Graph—the structure of Git's commit history.

**Delta**: The difference between two objects, used for compression.

**Detached HEAD**: State where HEAD points directly to a commit, not a branch.

**Fast-forward**: Merge where the target is an ancestor of the source.

**Gitlink**: Tree entry mode (160000) representing a submodule.

**HEAD**: Reference indicating the current branch or commit.

**Index**: Staging area; binary file tracking proposed next commit.

**Loose object**: Individually stored, zlib-compressed object.

**Merge base**: Common ancestor commit(s) of branches being merged.

**OID**: Object Identifier—the SHA hash naming an object.

**Pack file**: Collection of objects with delta compression.

**Peeling**: Resolving a reference chain to its ultimate target.

**Plumbing**: Low-level Git commands and internals.

**Porcelain**: High-level, user-facing Git commands.

**Reachability**: Whether one commit can be reached from another via parent links.

**Ref**: Reference—a named pointer to a commit (branch, tag, etc.).

**Reflog**: Log of reference value changes over time.

**Refspec**: Mapping between remote and local references.

**SHA-1**: Secure Hash Algorithm 1—Git's original hash function.

**Symbolic ref**: Reference pointing to another reference.

**Tag**: Named reference to a specific commit; may be annotated.

**Tree**: Git object representing directory structure.

**Worktree**: A working directory associated with a repository.

---

*This document provides a comprehensive exploration of Git's internal
architecture. Like the systems described in Bach's operating systems
text, Git's elegance lies in the careful composition of simple,
well-defined components into a powerful whole.*


